"""Direct tests of the withdrawal DECISION FUNCTION.

Labelled HELPER tests throughout. They are not a substitute for the real-module coverage
in `test_dcnm_intf_withdrawal.py`; they exist because `gie_withdrawal_action` is also the
function an external caller invokes on its own -- a compatibility probe, or a live
batch's classification preflight. Such a caller never goes through `main()`, so the gate
must live inside the function itself, and that copy needs its own proof.

NOT LIVE TESTED IN THIS GENERATION.

The unsupported routed fixture is now ``eigrp_ipv4_passive`` because PIM/BFD
gained a measured reset. ``FIXTURE_CONTRACTS`` checks its registration and
no-reset property per parent. ACCESS positive cases keep their own measured rows.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from .gie_withdrawal_harness import an_unclassifiable_key

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    gie_withdrawal_action,
    gie_binding_applicable,
    GIE_WITHDRAW_NONE,
    GIE_WITHDRAW_RESET,
    GIE_WITHDRAW_UNSUPPORTED,
    GIE_WITHDRAW_UNCLASSIFIED,
    GIE_WITHDRAW_INAPPLICABLE,
)

ACCESS = "int_access_host"
ROUTED = "int_routed_host"
SUBIF = "int_subif"
SVI = "int_vlan"
OK = "12.6.0.267"


# ------------------------------------------------------------------ version boundary
@pytest.mark.parametrize("version", ["12.6.0.266", "12.4.1", "not-a-version", "", None],
                         ids=["one_below", "far_below", "malformed", "empty", "none"])
def test_classifier_refuses_an_inapplicable_binding(version):
    """The gate mutation 3b targets. Below min_ndfc_version, or on a version we cannot
    parse, the answer is INAPPLICABLE -- never a reset, never a refusal."""
    action, wire = gie_withdrawal_action(ACCESS, "acl_filter", "ACL-PILOT", version)
    assert action == GIE_WITHDRAW_INAPPLICABLE, (
        "a binding the controller cannot carry was classified %r; emitting a reset here "
        "transports what an explicit key is refused, and refusing here rejects a run over "
        "a field this controller never had" % action)
    assert wire is None


@pytest.mark.parametrize("version", [OK, "12.6.0.268", "12.7.0.1", "13.0.0.0"],
                         ids=["equal", "patch_above", "minor_above", "major_above"])
def test_classifier_reconciles_once_the_version_supports_it(version):
    action, wire = gie_withdrawal_action(ACCESS, "acl_filter", "ACL-PILOT", version)
    assert (action, wire) == (GIE_WITHDRAW_RESET, "")


def test_applicability_helper_agrees_with_the_classifier():
    """Two entry points, one boundary. A caller that selects with the helper and then
    classifies must never see the two disagree."""
    for version in ("12.6.0.266", OK, "nonsense", None):
        applicable = gie_binding_applicable(ACCESS, "acl_filter", version)
        action, _ = gie_withdrawal_action(ACCESS, "acl_filter", "ACL-PILOT", version)
        assert applicable == (action != GIE_WITHDRAW_INAPPLICABLE), version


# ------------------------------------------------------------------ HAVE encodings
@pytest.mark.parametrize("have", ["false", False], ids=["wire_string", "native_bool"])
def test_both_accepted_encodings_of_the_declared_default_mean_the_same_state(have):
    action, _ = gie_withdrawal_action(ACCESS, "disable_lldp_receive", have, OK)
    assert action == GIE_WITHDRAW_NONE, (
        "encoding %r of the declared default classified as %r; the HAVE validator accepts "
        "both spellings and they describe one controller state" % (have, action))


@pytest.mark.parametrize("have", ["true", True], ids=["wire_string", "native_bool"])
def test_both_encodings_of_a_non_default_also_agree(have):
    """The opposite direction, so the normalisation is not just collapsing everything to
    'no change'.

    REHOMED: this used int_access_host::disable_lldp_receive, which had no reset when the
    test was written. That row is now supported, so the C7 half of the assertion would
    have been silently lost. int_routed_host::disable_lldp_receive is a genuine
    unsupported-but-applicable row -- a declared default, no established reset -- so the
    guarantee moves rather than weakening.
    """
    action, _ = gie_withdrawal_action(ROUTED, "eigrp_ipv4_passive", have, OK)
    assert action == GIE_WITHDRAW_UNSUPPORTED


@pytest.mark.parametrize("have", ["true", True], ids=["wire_string", "native_bool"])
def test_both_encodings_reach_the_same_reset(have):
    action, wire = gie_withdrawal_action(ACCESS, "disable_lldp_transmit", have, OK)
    assert (action, wire) == (GIE_WITHDRAW_RESET, "false")


def test_normalisation_does_not_turn_an_empty_string_into_a_false():
    """`""` is NDFC's 'no value', not the boolean false, and the two must not merge.

    A blanket coercion would make an unset field look like a configured default -- and on
    a binding whose declared default is False that silently reclassifies C-nothing as
    already-withdrawn for the wrong reason.
    """
    # REHOMED to int_routed_host for the same reason as above: the access row now has a
    # reset, and this case needs one that does not.
    empty, _ = gie_withdrawal_action(ROUTED, "eigrp_ipv4_passive", "", OK)
    false_wire, _ = gie_withdrawal_action(ROUTED, "eigrp_ipv4_passive", "false", OK)
    assert false_wire == GIE_WITHDRAW_NONE
    assert empty != GIE_WITHDRAW_RESET, (
        "an empty HAVE produced a reset; absence is not a configured value")


def test_an_integer_zero_is_not_an_empty_value():
    """The other half of the same rule: no empty-to-zero conversion in either direction.

    The key is DERIVED, not named: this used `ospf_cost` until G37 measured its reset, which is
    the second time a registration invalidated a hardcoded example here.
    """
    # REHOMED to `int_vlan`, for the same reason as the decision-table row below and one step
    # further: the dampening generation consumed `int_routed_host`'s last unclassifiable integers,
    # BETA moved this to `int_subif`, and this union registers the three BFD timers there too.
    # `int_vlan` still carries four (the HSRP integers). The harness asserts loudly when a parent
    # runs out, which is how this was caught.
    key = an_unclassifiable_key(SVI, "integer")
    zero, _ = gie_withdrawal_action(SVI, key, 0, OK)
    empty, _ = gie_withdrawal_action(SVI, key, "", OK)
    assert zero == GIE_WITHDRAW_UNCLASSIFIED, (
        "a real integer value was treated as absence (%s)" % key)
    assert empty == GIE_WITHDRAW_UNCLASSIFIED
    # They classify the same here only because this row has neither metadata; the point is
    # that "0" and "" took different routes to get there, not that they are interchangeable.
    assert gie_withdrawal_action(SVI, key, "0", OK)[0] == zero


# ------------------------------------------------------------------ the decision table
@pytest.mark.parametrize("parent,key,have,expected", [
    (ACCESS, "acl_filter", "", GIE_WITHDRAW_NONE),             # already at its reset
    (ACCESS, "acl_filter", "ACL-X", GIE_WITHDRAW_RESET),       # reset known
    (ACCESS, "flowcontrol_receive", "off", GIE_WITHDRAW_NONE),  # reset == default
    (ACCESS, "flowcontrol_receive", "on", GIE_WITHDRAW_RESET),
    (ACCESS, "disable_lldp_receive", "false", GIE_WITHDRAW_NONE),   # at declared default
    # REHOMED: access disable_lldp_receive now carries a reset, so the
    # differs-without-a-reset row moves to a parent where that is still true.
    # BFD echo and PIM/BFD gained measured resets in separate campaigns. The
    # withheld EIGRP passive row remains a registered no-reset example.
    (ROUTED, "eigrp_ipv4_passive", "true", GIE_WITHDRAW_UNSUPPORTED),
    # DERIVED, and REHOMED THREE TIMES NOW. `ospf_cost` held this slot until G37 measured its
    # reset; the five dampening integers held it next, which is why BETA moved it to `int_subif`;
    # and THIS union registers the three BFD timers on `int_subif` as well, so that parent has run
    # out too. Measured on the integrated table: int_routed_host 0 candidates, int_subif 0,
    # int_vlan 4 (the HSRP integers). So it moves to `int_vlan`.
    #
    # The harness refuses to let this pass vacuously -- `an_unclassifiable_key` asserts loudly
    # when a parent has no candidate left -- which is exactly how this was caught rather than
    # discovered by a green suite. Deriving the key keeps the row honest the next time a
    # generation consumes the last candidate on a parent.
    (SVI, an_unclassifiable_key(SVI, "integer"), "100", GIE_WITHDRAW_UNCLASSIFIED),
    (ACCESS, an_unclassifiable_key(SVI, "integer"), "100", GIE_WITHDRAW_NONE),
], ids=["reset_already_applied", "reset_needed", "default_is_the_reset",
        "enum_needs_reset", "at_declared_default", "differs_no_reset",
        "no_metadata", "not_on_this_parent"])
def test_the_decision_table_row_by_row(parent, key, have, expected):
    action, wire = gie_withdrawal_action(parent, key, have, OK)
    assert action == expected, "%s::%s with HAVE %r" % (parent, key, have)
    assert (wire is not None) == (action == GIE_WITHDRAW_RESET)
