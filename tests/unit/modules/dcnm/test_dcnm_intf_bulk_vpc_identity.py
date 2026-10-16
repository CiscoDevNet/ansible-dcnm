"""A vPC record in a bulk interface response must not mark its switch unreadable.

The bulk endpoint (``/rest/interface?serialNumber=X``) does NOT return ``interfaceType``.
Measured against NDFC 12.6.0.267: a vPC record carries exactly ``ifName``, ``nvPairs`` and a
combined ``serialNumber``, and the item enclosing it carries exactly ``policy`` and
``interfaces``. ``_dcnm_intf_bulk_response_identity`` decided the vPC branch on the type alone,
so every vPC record fell through to the single-serial branch, which rejects a combined serial.

One rejected record marks the WHOLE switch unreadable, and from then on any interface on it
that reaches the authority gate fails with "could not be read authoritatively".

Interfaces still named in the playbook never noticed: they are in ``want``, so the sweep skips
the gate for them. The damage only surfaced on a delete-everything run -- ``config: []`` with
``state: overridden``, which is what a NAC remove step sends -- where nothing is wanted and the
gate runs over every interface. It then failed on whichever interface came first, naming an
interface that was not itself at fault.

Corroborating the pair against ``vpc_ip_sn`` is NOT a usable check here and these tests pin
that too: that map is only ever populated from switches named in the playbook, so on the very
run where this breaks it is empty. The check that does the work is that the serial we queried
is one of the two halves of the returned pair.

Companion to test_dcnm_intf_override_authority_scope.py, which covers where the gate runs.
This file covers what makes it fire.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

DcnmIntf = dcnm_interface.DcnmIntf

QUERY = "9P21OHXOL9L"
PEER = "912N7KTAC63"
PAIR = "{0}~{1}".format(QUERY, PEER)
FOREIGN_PAIR = "AAAAAAAAAAA~BBBBBBBBBBB"


def _obj(vpc_ip_sn=None):
    """The helper under test needs no constructed module, only its own state."""
    obj = DcnmIntf.__new__(DcnmIntf)
    obj.vpc_ip_sn = vpc_ip_sn if vpc_ip_sn is not None else {}
    return obj


# The exact shape NDFC returns. interfaceType is absent at BOTH levels -- that absence
# is the whole point, so it is spelled out rather than implied.
REAL_VPC_ITEM = {
    "policy": "int_vpc_trunk_host",
    "interfaces": [
        {
            "ifName": "vpc55",
            "serialNumber": PAIR,
            "nvPairs": {"MEMBER_INTERFACES": "e1/5"},
        }
    ],
}


def test_the_bulk_item_really_has_no_interface_type():
    """Pin the premise: if NDFC ever starts sending it, this test says so first."""
    assert "interfaceType" not in REAL_VPC_ITEM
    assert "interfaceType" not in REAL_VPC_ITEM["interfaces"][0]


def test_a_vpc_record_without_interface_type_resolves():
    """The regression. Before the fix this returned None and poisoned the switch."""
    intf = REAL_VPC_ITEM["interfaces"][0]
    identity = _obj()._dcnm_intf_bulk_response_identity(
        intf["serialNumber"],
        intf.get("interfaceType", REAL_VPC_ITEM.get("interfaceType")),
        QUERY,
        QUERY,
    )
    assert identity == PAIR


def test_resolution_does_not_depend_on_vpc_ip_sn():
    """An empty pair map is the normal state on a delete-everything run.

    If this ever needs vpc_ip_sn populated, the bug is back by another route.
    """
    empty = _obj({})._dcnm_intf_bulk_response_identity(PAIR, None, QUERY, QUERY)
    populated = _obj({"192.0.2.10": PAIR})._dcnm_intf_bulk_response_identity(
        PAIR, None, QUERY, QUERY
    )
    assert empty == populated == PAIR


def test_the_explicit_type_still_resolves():
    """Callers that DO declare the type keep their existing path, unchanged.

    That path corroborates the pair against ``vpc_ip_sn``, so this populates it --
    which is exactly what the pre-existing bulk tests do. The declared path was not
    touched: only the absent-type case changed.
    """
    for declared in ("INTERFACE_VPC", "AA_FEX"):
        obj = _obj({"192.0.2.10": PAIR})
        assert obj._dcnm_intf_bulk_response_identity(PAIR, declared, QUERY, QUERY) == PAIR


def test_a_physical_type_with_a_combined_serial_is_still_malformed():
    """Shape only decides when the type is absent.

    A record that says INTERFACE_ETHERNET and carries a pair serial is malformed --
    a physical port belongs to one switch. Widening the shape rule to cover declared
    types would have silently accepted it; this pins that it does not.
    """
    assert (
        _obj({"192.0.2.10": PAIR})._dcnm_intf_bulk_response_identity(
            PAIR, "INTERFACE_ETHERNET", QUERY, QUERY
        )
        is None
    )


@pytest.mark.parametrize(
    "response_serial,query_serial,expected_serial,why",
    [
        ("ZZZZZZZZZZZ", QUERY, QUERY, "a different switch's serial"),
        (FOREIGN_PAIR, QUERY, QUERY, "a pair that does not contain the queried serial"),
        (PAIR, QUERY, FOREIGN_PAIR, "an explicit pair was asked for, a different one came back"),
        (PAIR, None, QUERY, "no queried serial to check the halves against"),
        (None, QUERY, QUERY, "no serial at all"),
        ("", QUERY, QUERY, "an empty serial"),
        ("A~B~C", QUERY, QUERY, "a malformed three-part serial"),
    ],
)
def test_a_foreign_or_malformed_record_is_still_rejected(
    response_serial, query_serial, expected_serial, why
):
    """The fix must not become a way in. Each of these must still fail closed."""
    assert (
        _obj()._dcnm_intf_bulk_response_identity(
            response_serial, None, query_serial, expected_serial
        )
        is None
    ), why


def test_a_plain_single_serial_record_still_resolves():
    """Non-vPC interfaces are the common case and must be untouched."""
    assert _obj()._dcnm_intf_bulk_response_identity(QUERY, None, QUERY, QUERY) == QUERY


def test_a_single_serial_from_another_switch_is_rejected():
    assert (
        _obj()._dcnm_intf_bulk_response_identity("ZZZZZZZZZZZ", None, QUERY, QUERY)
        is None
    )
