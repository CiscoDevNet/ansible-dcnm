"""The union-level guarantee neither source campaign could state: BOTH newly accepted
reset families are present in ONE loaded table, together, with their vocabularies intact.

WHY THIS FILE EXISTS AT ALL

ALPHA measured and registered the two routed LLDP booleans; BETA measured and registered the
two routed OSPF enums. Each shipped its own 72-reset candidate and its own test file, and
neither file can see the other's rows: `test_gie_routed_lldp_reset.py` never names
`ospf_passive_mode`, and `test_gie_routed_enum_omission_b3.py` never names
`disable_lldp_transmit`.

The consequence, stated precisely: EACH family's suite passes on ITS OWN candidate and cannot
detect that the other family is missing, because it never asks about those rows. That is not
the same as both suites passing together on an incomplete table -- they do not. Run both on
either 72-reset candidate and the other family's file fails, since its rows carry no reset
there. What is missing is a case that FAILS when one family is absent while the suite that
would have noticed is the one nobody thought to run. So no single-family suite can certify the
union, and the cheapest wrong ways to produce a "74-reset" artifact -- copying one 72-row
candidate over the other, or concatenating two generated tables -- need a guarantee stated at
the union level. That is this file. Measured: it fails 4 of its 8 cases on ALPHA's candidate,
4 on BETA's, 6 on the 70-reset base, and passes 8/8 only on the union.

WHAT THIS FILE DELIBERATELY DOES NOT DUPLICATE

Two sources of the same truth drift apart, so the guards that already exist are referenced,
not reimplemented:

  * row count, identity uniqueness and the no-duplicate-row contract --
    `test_gie_passthrough_bindings.py::test_table_rows_are_unique_and_the_count_is_pinned`;
  * the table was not hand-edited after generation --
    `test_gie_passthrough_bindings.py::test_provenance_recalculates_from_packaged_rows`;
  * index freshness and a replaced table -- `test_gie_binding_indexes.py`;
  * every registered reset has real-`main()` fixture coverage --
    `test_dcnm_intf_withdrawal.py::test_the_fixture_matrix_covers_every_registered_reset`;
  * per-family withdrawal behaviour -- each family's own file.

What is left, and is only expressible once both families are present, is below.

NOT LIVE TESTED IN THIS GENERATION. No controller, Nexus or Jenkins is contacted. The four
resets carry the live acceptance of their own source campaigns; this integrated tuple does
not inherit a fresh live result from that.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    BINDING_TABLE,
    resolve_binding,
    resolve_by_nvpair,
)

ROUTED = "int_routed_host"

# The four additions this integration is the union of, and nothing else.
# (profile_key, parent_nvpair, reset_wire, declared type, family)
LLDP_FAMILY = [
    ("disable_lldp_transmit", "lldpTransmit", "false", "boolean", "lldp"),
    ("disable_lldp_receive", "lldpReceive", "false", "boolean", "lldp"),
]
ENUM_FAMILY = [
    ("ospf_passive_mode", "ospfPassiveMode", "noChange", "enum", "ospf-enum"),
    ("ospf_network_type", "ospfNetworkType", "noChange", "enum", "ospf-enum"),
]
FOUR = LLDP_FAMILY + ENUM_FAMILY
FOUR_IDS = ["%s::%s" % (ROUTED, f[1]) for f in FOUR]

PREVIOUS_RESET_TOTAL = 70
UNION_RESET_TOTAL = 74


def _rows():
    return list(BINDING_TABLE.values()) if isinstance(BINDING_TABLE, dict) else list(BINDING_TABLE)


def _registered_resets():
    return {(r["parent_template"], r["parent_nvpair"]) for r in _rows()
            if r.get("reset_wire") is not None}


@pytest.mark.parametrize("key,nvpair,reset,declared_type,_family", FOUR, ids=FOUR_IDS)
def test_each_of_the_four_resolves_from_the_actual_loaded_table(
    key, nvpair, reset, declared_type, _family
):
    """Resolved from the table the runtime really imported, by BOTH identity paths, and both
    paths must hand back the SAME row object -- a table assembled by concatenation could
    answer one path and not the other, or answer each from a different row."""
    by_key = resolve_binding(ROUTED, key)
    by_nv = resolve_by_nvpair(ROUTED, nvpair)
    assert by_key is not None, "%s::%s is absent from the loaded table" % (ROUTED, key)
    assert by_nv is not None, "%s::%s is absent from the nvPair index" % (ROUTED, nvpair)
    assert by_key is by_nv, (
        "the two identity paths for %s::%s resolved to different row objects, so the table "
        "or its indexes carry that identity twice" % (ROUTED, nvpair))
    assert by_key["parent_nvpair"] == nvpair
    assert by_key["type"] == declared_type
    assert by_key.get("reset_wire") == reset
    # The type of the reset, not only its text. The controller returns this nvPair as a
    # string, so the reset must be the string. A native bool is not interchangeable with it
    # in either direction: `False == "false"` is False, so the comparison against a HAVE
    # would never match, and in a boolean test the two are OPPOSITE -- the non-empty string
    # "false" is truthy while native False is falsy.
    assert isinstance(by_key["reset_wire"], str), (
        "%s::%s reset_wire is %s; it must be the wire STRING"
        % (ROUTED, nvpair, type(by_key["reset_wire"]).__name__))


def test_both_families_are_present_together_not_one_or_the_other():
    """The defect this file exists for. Either source candidate alone satisfies its own
    suite; only the union satisfies this."""
    registered = _registered_resets()
    lldp = [(ROUTED, nv) for _k, nv, _r, _t, _f in LLDP_FAMILY]
    enums = [(ROUTED, nv) for _k, nv, _r, _t, _f in ENUM_FAMILY]
    missing_lldp = [i for i in lldp if i not in registered]
    missing_enum = [i for i in enums if i not in registered]
    assert not missing_lldp and not missing_enum, (
        "only one family is registered, so this is a single-campaign candidate rather than "
        "the union.\n  LLDP rows missing: %s\n  OSPF enum rows missing: %s"
        % (missing_lldp, missing_enum))


def test_the_registered_reset_total_is_the_previous_seventy_plus_these_four():
    """74 = 70 + 4, and the four are accounted for by NAME, so the total cannot be reached
    by registering something else instead of one of them."""
    registered = _registered_resets()
    assert len(registered) == UNION_RESET_TOTAL, (
        "the loaded table registers %d resets, expected %d"
        % (len(registered), UNION_RESET_TOTAL))
    four = {(ROUTED, nv) for _k, nv, _r, _t, _f in FOUR}
    assert four <= registered, "not all four accepted resets are registered: %s" % (
        sorted(four - registered),)
    assert len(registered - four) == PREVIOUS_RESET_TOTAL, (
        "setting the four aside leaves %d previously accepted resets, expected %d"
        % (len(registered - four), PREVIOUS_RESET_TOTAL))


def test_merging_the_two_families_did_not_cross_contaminate_their_vocabularies():
    """The two families express "withdrawn" differently, and the merge must keep them apart.

    A boolean row's reset is the wire string of a native `False` and it declares NO SMU
    vocabulary. An enum row's reset is the neutral WIRE spelling `noChange`, it declares a
    vocabulary whose public neutral is `no_change`, and the wire spelling must NOT have been
    added to the public choices: registering a reset may not widen the public schema.
    """
    for key, nvpair, reset, _t, _f in LLDP_FAMILY:
        b = resolve_binding(ROUTED, key)
        assert b.get("wire_values") is None, (
            "%s::%s gained an SMU vocabulary it never had; the enum family's wire_values "
            "leaked onto a boolean row" % (ROUTED, nvpair))
        assert b["default_template"] is False, (
            "%s::%s declared default changed: %r" % (ROUTED, nvpair, b["default_template"]))
        assert reset == "false"

    for key, nvpair, reset, _t, _f in ENUM_FAMILY:
        b = resolve_binding(ROUTED, key)
        vocabulary = b.get("wire_values")
        assert vocabulary, "%s::%s lost its SMU vocabulary" % (ROUTED, nvpair)
        assert vocabulary["no_change"] == reset, (
            "%s::%s public neutral maps to %r, not to the registered reset %r"
            % (ROUTED, nvpair, vocabulary.get("no_change"), reset))
        assert "no_change" in b["valid_values"]
        assert reset not in b["valid_values"], (
            "%s::%s wire spelling %r leaked into the public valid_values"
            % (ROUTED, nvpair, reset))
        assert b["default_template"] == "no_change"


def test_the_four_share_one_parent_and_did_not_spread_to_its_unmeasured_siblings():
    """The union is four rows on `int_routed_host`. The parents that declare the same public
    keys without a measurement -- the two vPC parents for LLDP, `int_vlan` for the two OSPF
    enums -- must still carry no reset, or the merge widened the accepted set."""
    for _k, nvpair, _r, _t, _f in FOUR:
        b = resolve_by_nvpair(ROUTED, nvpair)
        assert b["parent_template"] == ROUTED

    unmeasured = [
        ("int_vpc_access_host", "disable_lldp_transmit"),
        ("int_vpc_access_host", "disable_lldp_receive"),
        ("int_vpc_trunk_host", "disable_lldp_transmit"),
        ("int_vpc_trunk_host", "disable_lldp_receive"),
        ("int_vlan", "ospf_passive_mode"),
        ("int_vlan", "ospf_network_type"),
    ]
    leaked = []
    for parent, key in unmeasured:
        b = resolve_binding(parent, key)
        assert b is not None, (
            "%s::%s is no longer in the table, so this guard proves nothing" % (parent, key))
        if b.get("reset_wire") is not None:
            leaked.append((parent, key, b["reset_wire"]))
    assert not leaked, (
        "the registration reached parents nobody measured: %s" % (leaked,))
