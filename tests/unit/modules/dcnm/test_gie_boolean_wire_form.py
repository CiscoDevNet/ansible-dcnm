"""nvPairs is a STRING-valued map. A boolean binding must be transported as its wire form.

Measured on a live controller (NDFC 12.6.0.267, Leaf-101, DISABLE_LLDP on both host eth
parents). Stage p1 set the field and NDFC stored it. Stage p2 re-sent the IDENTICAL intent and
the module reported changed=True with 2 API calls again -- the field never converges:

    want (engine)  DISABLE_LLDP = True     <- native Python bool
    have (NDFC)    DISABLE_LLDP = "true"   <- what the controller stores and returns
    compare        "true" != True          -> diff on every single run

The module's existing convention normalizes booleans at COMPARISON time, per key, through a
hardcoded allowlist in dcnm_intf_compare_elements:

    boolean_keys = ["ENABLE_ORPHAN_PORT", "DISABLE_LACP_SUSPEND", "ENABLE_LACP_VPC_CONV",
                    "ENABLE_PFC", "ENABLE_MONITOR", "CDP_ENABLE", "ENABLE_QOS",
                    "COPY_DESC", "ENABLE_STORM_CONTROL"]

Adding DISABLE_LLDP to that list would fix the symptom and defeat the point: a generic engine
whose every new boolean requires editing a per-nvPair allowlist is not generic. It is also not
reachable from there -- dcnm_intf_compare_elements receives the nvPair name but NOT the parent
template, so it cannot resolve a parent-scoped binding at all.

The engine emits the wire form instead. Then both sides are strings and the pre-existing generic
branch in dcnm_intf_compare_elements (isinstance(e, str) -> e.lower()) compares them correctly,
with no change to that function and no allowlist to maintain.

SCOPE: passthrough only.
    passthrough -> written straight into nvPairs; transport is the whole job. 15 bindings today:
                   13 string/enum (serialization is a no-op) and 2 boolean (the fix).
    child_pti   -> the OSPF-MD domain on int_fabric_loopback_11_1. It has a dedicated normalizer
                   (dcnm_intf_normalize_ospf_auth_message_digest) and its call site already
                   stringifies explicitly. Left native so the golden payload snapshots that pin
                   the pre-migration OSPF emission stay byte-identical.

Run:
    pytest tests/unit/modules/dcnm/test_gie_boolean_wire_form.py
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest import mock

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    BINDING_TABLE,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    gie_contribute_nvpairs,
    gie_validate_binding_value,
)
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

TRUNK = "int_trunk_host"
ACCESS = "int_access_host"
LOOPBACK = "int_fabric_loopback_11_1"
VERSION = "12.6.0.267"

_OMITTED = object()

# Derived from the table, NOT hand-listed. A boolean binding registered later is covered by
# these tests the day it lands, which is the point of a generic engine: the contract belongs to
# the mechanism, not to any one field. Hand-listing would silently leave the next one untested.
BOOL_PASSTHROUGH = sorted(
    (b["parent_template"], b["profile_key"], b["parent_nvpair"])
    for b in BINDING_TABLE
    if b["type"] == "boolean" and b["mechanism"] == "passthrough"
)
BOOL_IDS = ["%s::%s" % (p.replace("int_", ""), k) for p, k, nvpair in BOOL_PASSTHROUGH]


def test_the_derived_set_is_not_empty_and_covers_the_known_fields():
    """Guard the guard: an empty parametrize list turns every test below into a no-op.

    Also pins the fields known to be boolean passthrough today, so a binding silently changing
    type or mechanism shows up here instead of quietly leaving this file with nothing to run.
    """
    assert BOOL_PASSTHROUGH, "no boolean passthrough bindings -- the tests below run on nothing"
    assert {k for parent, k, nvpair in BOOL_PASSTHROUGH} == {
        "disable_lldp_transmit", "disable_lldp_receive", "disable_qos_stats", "disable_queuing_stats", "disable_bfd_echo",
        # The boolean OSPF names, once. enable_ospf reaches this set from both lots; listing it
        # twice made the literal look like it pinned more than it does.
        "enable_ospf", "ospf_mtu_ignore", "ospf_shutdown",
        "ospf_bfd", "ospf_passive_interface",
        "enable_ospf_auth",
        # Redirects partidos + ND suppress-RA, slice 0b_28. Los tres en los tres padres overlay.
        # El cuarto del grupo, disable_ip_redirects, es NATIVO y no aparece aqui -- si apareciera
        # significaria que el registry le quito el nombre al arg spec.
        "disable_ipv4_redirects", "disable_ipv6_redirects", "ipv6_nd_suppress_ra",
        # Dampening, slice 0b_6: solo DOS de sus siete son boolean. Los otros cinco son
        # integer y viven en la lista de representacion HAVE, no aqui.
        "enable_dampening", "dampening_restart",
        # PIM, slice 0b_31: DOS de sus tres claves son boolean. pim_dr_priority es integer y
        # vive en la lista de representacion HAVE, no aqui.
        "enable_pim_sparse", "enable_pim_bfd_instance",
        # MACSEC, slice 0b_33: solo el habilitador es boolean. Los otros tres son NOMBRES
        # (string) y no aparecen aqui.
        "enable_macsec_interface_policy",
        # EIGRP, slice 0b_22 -- eight distinct keys, each on all three overlay parents.
        "enable_eigrp_routing", "enable_eigrp_ipv6_routing", "enable_eigrp_shutdown",
        "enable_eigrp_bfd", "disable_eigrp_bfd",
        "eigrp_ipv4_passive", "eigrp_no_ipv4_passive", "eigrp_no_ipv6_passive",
        # int_loopback, slice 0b_23. Five of its six booleans are names already here; the sixth,
        # ospf_advertise_subnet, exists on no other parent -- advertising a loopback's subnet is
        # a loopback concept.
        "ospf_advertise_subnet",
        # BFD: enable_bfd_interval is the gate. disable_bfd_echo gains a second parent
        # (int_vlan) for a key int_routed_host already carried, so int_vlan goes 12 -> 13.
        "enable_bfd_interval",
        # There is no eigrp_ipv6_passive: IPv4 declares both the passive and the no-passive
        # field, IPv6 only the no-passive one. The children match -- an ipv6-passive child
        # does not exist either. The asymmetry is the template's.
    }
    # 80 = the per-parent counts below, which are what the table actually holds. Measured
    # against BINDING_TABLE when slice 0b_22 landed, not carried forward by arithmetic:
    #
    #     int_access_host                     4      int_routed_host    17
    #     int_trunk_host                      4      int_subif          14
    #     int_port_channel_access_host        4      int_vlan           12
    #     int_port_channel_trunk_host         4
    #     int_port_channel_dot1q_tunnel_host  4      int_vpc_access_host  4
    #                                                int_vpc_trunk_host   4
    #                                                int_loopback         6
    #
    # The three overlay parents grew by 8 each: the eleven EIGRP booleans are eight distinct
    # keys plus the three that repeat per parent. int_routed_host 9 -> 17, int_subif 6 -> 14,
    # int_vlan 4 -> 12.
    #
    # This used to be a derivation -- "3 x 8 = 24, plus disable_bfd_echo, plus enable_ospf..."
    # -- and the derivation had silently drifted to 28 while the assertion said 44. Nobody
    # noticed, because only the number is executed and only the prose was wrong. A breakdown
    # that can be checked against the table beats a chain of arithmetic that cannot.
    #
    # int_routed_host emits no CLI of its own for any of them -- every value is handed to a
    # child template. Same reasoning as the vPC parents below: that does not exempt it from the
    # wire form, because the value lands in the routed parent's own nvPairs first.
    #
    # The vPC parents emit no CLI of their own -- they hand the value to a child template. They
    # are still passthrough and therefore still need the wire form: the value lands in the vPC
    # parent's own nvPairs first, and nvPairs is a string-valued map. A native bool left there
    # would reproduce exactly the non-convergence this file exists to prevent.
    # 96 = 87 + the NINE of slice 0b_28, all boolean: three fields on each of the three
    # overlay parents. Slice 0b_27 added none here -- hsrp_groupv6 is an integer and
    # hsrp_vipv6 a string.
    # 98 = 96 + los DOS boolean de dampening. Sus otros cinco campos son integer.
    # 103 = 98 + los CINCO boolean de PIM: enable_pim_sparse en los cuatro padres y
    # enable_pim_bfd_instance en int_routed_host. pim_dr_priority es integer y no cuenta aqui.
    # 104 = 103 + enable_macsec_interface_policy, el UNICO boolean de MACSEC: sus otros tres
    # campos son nombres (string).
    assert len(BOOL_PASSTHROUGH) == 104


# ------------------------------------------------------- what the engine emits --

@pytest.mark.parametrize("parent,profile_key,nvpair", BOOL_PASSTHROUGH, ids=BOOL_IDS)
@pytest.mark.parametrize(
    "value,wire", [(True, "true"), (False, "false")], ids=["true", "false"]
)
def test_boolean_passthrough_is_emitted_as_its_wire_form(
    parent, profile_key, nvpair, value, wire
):
    """The exact defect: a native bool in nvPairs never matches the controller's string."""
    add, err = gie_contribute_nvpairs(parent, {profile_key: value}, VERSION)
    assert err is None
    assert add[nvpair] == wire
    assert isinstance(add[nvpair], str)
    # Not the Python repr: NDFC's template DSL tests `== "true"`, lowercase.
    assert add[nvpair] != str(value)


@pytest.mark.parametrize("parent", [TRUNK, ACCESS])
@pytest.mark.parametrize(
    "key,value",
    [
        ("flowcontrol_receive", "on"),
        ("flowcontrol_send", "off"),
        ("spanning_tree_port_type", "network"),
        ("acl_filter", "MY-FILTER"),
    ],
)
def test_string_and_enum_passthrough_are_untouched(parent, key, value):
    """The other 13 passthrough bindings must come through byte-identical.

    Serializing a str is a no-op, but that has to be proven rather than assumed -- a change
    that silently lowercased ACL_FILTER would corrupt a case-sensitive ACL name.
    """
    add, err = gie_contribute_nvpairs(parent, {key: value}, VERSION)
    assert err is None
    assert list(add.values()) == [value]
    assert add[list(add)[0]] is value or add[list(add)[0]] == value


def test_acl_filter_case_is_preserved_exactly():
    """Named explicitly because lowercasing is the plausible way to get this wrong."""
    add, err = gie_contribute_nvpairs(TRUNK, {"acl_filter": "MiXeD-Case_ACL"}, VERSION)
    assert err is None
    assert add["ACL_FILTER"] == "MiXeD-Case_ACL"


def test_omitted_boolean_still_contributes_nothing():
    """Serialization must not resurrect the explicit-only contract."""
    add, err = gie_contribute_nvpairs(TRUNK, {"description": "x"}, VERSION)
    assert err is None
    assert "DISABLE_LLDP_TRANSMIT" not in add


# ------------------------------------------- what the operator actually observes --
#
# The tests above pin the engine in isolation, so they would all still pass if the comparison
# path disagreed. These drive dcnm_intf_compare_want_and_have -- the code that decides
# changed=True -- with the exact want/have pair measured on the lab.
#
# CRITICAL: the WANT side is built BY THE ENGINE, from the playbook-level value, exactly as
# dcnm_intf_get_eth_payload does. Hand-writing the wire string into want instead would make
# these pass both before and after the fix -- a test that cannot fail. The want must carry
# whatever the engine currently produces, so the engine's behaviour is what is under test.


def _engine_nvpairs(parent, profile_key, value):
    """The nvPairs the module would build for this profile, via the real engine call."""
    add, err = gie_contribute_nvpairs(parent, {profile_key: value}, VERSION)
    assert err is None, err
    return add


def _payload(parent, profile_key, nvpair, value=_OMITTED, description="same",
             engine_built=False):
    nvpairs = {"DESC": description}
    if value is not _OMITTED:
        if engine_built:
            nvpairs.update(_engine_nvpairs(parent, profile_key, value))
        else:
            nvpairs[nvpair] = value
    return {
        "deploy": False,
        "policy": parent,
        "interfaceType": "INTERFACE_ETHERNET",
        "interfaces": [{
            "serialNumber": "SN1",
            "interfaceType": "INTERFACE_ETHERNET",
            "ifName": "Ethernet1/4",
            "fabricName": "FAB1",
            "nvPairs": nvpairs,
        }],
    }


def _compare_obj(state, parent, profile_key, nvpair, want=_OMITTED, have=_OMITTED,
                 want_description="same", have_description="same"):
    """`want` is the PLAYBOOK value (a native bool); the engine turns it into nvPairs.
    `have` is the raw string the controller returns.
    """
    module = mock.Mock()
    module.params = {"fabric": "FAB1", "config": [], "state": state}
    module.check_mode = False
    with mock.patch.object(
        dcnm_interface, "dcnm_version_supported", return_value=(12, "12.6.0.267")
    ):
        obj = dcnm_interface.DcnmIntf(module)
    obj.want = [_payload(parent, profile_key, nvpair, want, want_description,
                         engine_built=True)]
    have_payload = _payload(parent, profile_key, nvpair, have, have_description)
    have_payload.pop("deploy")
    obj.have = [have_payload]
    pb = {
        "ifname": "Ethernet1/4",
        "sno": "SN1",
        "fabric": "FAB1",
        "policy": parent,
        "description": want_description,
    }
    if want is not _OMITTED:
        pb[profile_key] = want
    obj.pb_input = [pb]
    return obj


@pytest.mark.parametrize("parent,profile_key,nvpair", BOOL_PASSTHROUGH, ids=BOOL_IDS)
@pytest.mark.parametrize(
    "playbook_value,controller_value",
    [(True, "true"), (False, "false")],
    ids=["true", "false"],
)
def test_reapplying_the_same_boolean_is_idempotent(
    parent, profile_key, nvpair, playbook_value, controller_value
):
    """THE regression test. Reproduces live stage p2 exactly.

    The playbook says the field is true, the engine builds want, and the controller already
    holds "true". Before the fix the engine put a native bool in want, "true" != True compared
    unequal, and the module re-pushed on every run -- changed=True forever, with a deploy each
    time and a config-save behind it.
    """
    obj = _compare_obj("merged", parent, profile_key, nvpair,
                       playbook_value, controller_value)
    obj.dcnm_intf_compare_want_and_have("merged")
    assert obj.diff_replace == []
    assert obj.changed_dict[0]["merged"] == []


@pytest.mark.parametrize("parent,profile_key,nvpair", BOOL_PASSTHROUGH, ids=BOOL_IDS)
@pytest.mark.parametrize("state", ["merged", "replaced", "overridden"])
def test_a_real_boolean_change_is_still_detected(parent, profile_key, nvpair, state):
    """The opposite direction: the fix must not make the field unwritable.

    A test that only pins idempotency would also pass if the field were dropped entirely.
    """
    obj = _compare_obj(state, parent, profile_key, nvpair, True, "false")
    obj.dcnm_intf_compare_want_and_have(state)
    assert len(obj.diff_replace) == 1
    sent = obj.diff_replace[0]["interfaces"][0]["nvPairs"]
    assert sent[nvpair] == "true"
    reported = obj.changed_dict[0][state][0]["interfaces"][0]["nvPairs"]
    assert reported == {nvpair: "true"}


@pytest.mark.parametrize("parent,profile_key,nvpair", BOOL_PASSTHROUGH, ids=BOOL_IDS)
@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_omitted_boolean_is_carried_forward_from_have(parent, profile_key, nvpair, state):
    """Omission is not intent: an unrelated edit must not reset the controller's value.

    This matters more for the QoS-stats pair than for anything registered before it. Both are
    the " no-stats" suffix of a service-policy line, so a value silently reset to false does not
    remove a line -- it changes one in place, which is exactly the kind of drift nobody notices
    until statistics quietly come back.
    """
    obj = _compare_obj(
        state, parent, profile_key, nvpair, _OMITTED, "true",
        want_description="new", have_description="old",
    )
    obj.dcnm_intf_compare_want_and_have(state)
    sent = obj.diff_replace[0]["interfaces"][0]["nvPairs"]
    assert sent[nvpair] == "true"
    reported = obj.changed_dict[0][state][0]["interfaces"][0]["nvPairs"]
    assert reported == {"DESC": "new"}


# ---- HAVE encoding: "" for a boolean the template never defaulted --------------------
#
# Measured on NDFC 12.6.0.267 / Leaf-104 on 2026-09-20, GET of the endpoint that feeds HAVE
# on an int_routed_host interface:
#
#     DISABLE_IPV4_REDIRECTS  ""        template declares no defaultValue
#     IPV6_ND_SUPPRESS_RA     "false"   template declares defaultValue=false
#
# Both are boolean bindings on the same parent and the same interface, so the difference is
# the template's default, not the interface. Before the exemption, registering the first one
# made every operation on that parent abort while reading HAVE -- including operations that
# never mentioned redirects.
def test_have_accepts_empty_string_for_a_boolean_and_returns_it_verbatim():
    out = gie_validate_binding_value(
        "int_routed_host", "disable_ipv4_redirects", "", value_source="have"
    )
    assert out == "", "the carry-forward must round-trip the controller's own encoding"


def test_have_still_rejects_any_other_string_for_a_boolean():
    """The exemption is three values wide, not 'any string'."""
    for bogus in ("yes", "0", "False", "null"):
        with pytest.raises(Exception):
            gie_validate_binding_value(
                "int_routed_host", "disable_ipv4_redirects", bogus, value_source="have"
            )


def test_an_empty_string_is_not_accepted_as_operator_input_for_a_boolean():
    """HAVE-only. An operator writing "" is not saying anything the module can act on."""
    with pytest.raises(Exception):
        gie_validate_binding_value(
            "int_routed_host", "disable_ipv4_redirects", "", value_source="explicit"
        )
