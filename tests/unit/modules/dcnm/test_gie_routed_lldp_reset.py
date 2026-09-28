"""``int_routed_host`` LLDP: the two resets, measured live and now registered.

Until this lot, ``disable_lldp_transmit`` and ``disable_lldp_receive`` were registered on
``int_routed_host`` with no ``reset_wire``, so omitting either one under ``replaced`` refused the
whole invocation. They are withdrawable, and the wire value is the string ``"false"``.

WHY THE MEASUREMENT NEEDED A COMPANION HELD AT TRUE
``int_routed_host`` does not emit the LLDP CLI itself. Read from the template installed on the
controller (NDFC 12.6.0.267), the parent instantiates a child and gates it on an OR::

    lldpTransmit = normalize(scope.get("lldpTransmit", "false")).lower()
    lldpReceive  = normalize(scope.get("lldpReceive",  "false")).lower()
    if lldpTransmit == "true" or lldpReceive == "true":
        "interface_lldp_disable",
        "DISABLE_LLDP_TRANSMIT": lldpTransmit,
        "DISABLE_LLDP_RECEIVE":  lldpReceive

and the child emits one line per direction::

    if ($$DISABLE_LLDP_TRANSMIT$$ == "true") { no lldp transmit }
    if ($$DISABLE_LLDP_RECEIVE$$  == "true") { no lldp receive  }

So driving both to ``"false"`` destroys the child and both lines disappear together -- which proves
nothing about either field on its own. The live measurement therefore held the companion explicitly
at ``"true"`` so the child stayed alive, and only the target's line went away. Evidence:

    stage M1 both true          -> both lines present        (positive control)
    stage M2 transmit -> false  -> only `no lldp transmit` gone, receive survived
    stage M3 both true again    -> both lines present again  (positive control for the mirror)
    stage M4 receive  -> false  -> only `no lldp receive` gone, transmit survived

on Ethernet1/64 of Leaf-103 in fabric SMU90, 2026-09-28. The polarity was read from the child's
body, not inferred from the positive nvPair name: ``"true"`` means *disable*.

WHAT THESE CASES CANNOT PROVE
That the child template exists on the controller, or that the device drops the line. A missing child
would transport the nvPair, return success and produce no CLI -- exercised, never validated. The live
stages above are what closed that; these cases hold the contract in place afterwards.

Offline: no controller and no device.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    resolve_binding,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    GIE_WITHDRAW_NONE,
    GIE_WITHDRAW_RESET,
    gie_withdrawal_action,
)

from .gie_withdrawal_harness import (  # noqa: F401  (fixtures come with the harness)
    ACCESS,
    ROUTED,
    SUPPORTED,
    base_for,
    build_have,
    diff_nvpairs,
    request_nvpairs,
    run,
    split_calls,
)

TX = "disable_lldp_transmit"
RX = "disable_lldp_receive"
W_TX = "lldpTransmit"
W_RX = "lldpReceive"
RESET = "false"

# (target public key, target nvPair, companion public key, companion nvPair)
DIRECTIONS = [
    pytest.param(TX, W_TX, RX, W_RX, id="transmit"),
    pytest.param(RX, W_RX, TX, W_TX, id="receive"),
]


def _both_true_have():
    """HAVE with both directions disabled, taken from the module's own outbound payload.

    Built through ``build_have`` rather than hand-written: a fixture invented by the test can
    assert a shape the module never produces, and this contract is about what the module does with
    a HAVE the controller actually returns.
    """
    return build_have(ROUTED, key=TX, value=True, **{RX: True})


def _profile_holding(companion):
    """The withdrawal profile: the target OMITTED, the companion declared ``True``.

    Omission is the whole point -- an explicit ``False`` would be an ordinary apply, not a
    withdrawal, and would prove nothing about ``replaced``.
    """
    return base_for(ROUTED, **{companion: True})


# --------------------------------------------------------------- the registration itself

@pytest.mark.parametrize("key,nvpair,_c,_cw", DIRECTIONS)
def test_the_reset_is_registered_as_the_string_false(key, nvpair, _c, _cw):
    """Guard the guard.

    Every case below is meaningless if the row stopped declaring the reset, and they would all pass
    for the wrong reason. The type matters as much as the value: the controller returns this nvPair
    as a string, so the reset must be the string ``"false"``. A native bool is not interchangeable
    with it in either direction -- ``False == "false"`` is False, so the comparison against the HAVE
    would never match, and in a boolean test the two are OPPOSITE: the non-empty string ``"false"``
    is truthy while native ``False`` is falsy.
    """
    binding = resolve_binding(ROUTED, key)
    assert binding is not None, "{0}::{1} is not registered".format(ROUTED, key)
    assert binding["parent_nvpair"] == nvpair
    assert binding.get("reset_wire") == RESET
    assert isinstance(binding.get("reset_wire"), str)
    assert binding.get("default_template") is False


@pytest.mark.parametrize("key,_nv,_c,_cw", DIRECTIONS)
def test_the_engine_resets_a_configured_value_and_leaves_a_default_alone(key, _nv, _c, _cw):
    """``have == declared default`` is nothing to withdraw; anything else is the reset."""
    assert gie_withdrawal_action(ROUTED, key, "true", SUPPORTED) == (GIE_WITHDRAW_RESET, RESET)
    assert gie_withdrawal_action(ROUTED, key, RESET, SUPPORTED) == (GIE_WITHDRAW_NONE, None)


# --------------------------------------------------------------- independence, both directions

@pytest.mark.parametrize("key,nvpair,companion,comp_nv", DIRECTIONS)
def test_replaced_withdraws_only_the_omitted_direction(key, nvpair, companion, comp_nv):
    """The reset for the target travels; the companion keeps the value it was given.

    This is the case the live stages M2 and M4 measured. Both directions are exercised because they
    are two separate identities in the table: N proofs of one field are not N fields proved.
    """
    result, calls = run(_profile_holding(companion), "replaced", have=_both_true_have())
    assert not result.get("failed"), result.get("msg")

    sent = request_nvpairs(calls)
    assert sent, "the module sent no nvPairs at all, so nothing was withdrawn"
    target = [m[nvpair] for m in sent if nvpair in m]
    held = [m[comp_nv] for m in sent if comp_nv in m]
    assert target == [RESET] * len(target) and target, (
        "expected {0} to travel as {1!r}, got {2!r}".format(nvpair, RESET, target))
    assert held == ["true"] * len(held) and held, (
        "the companion {0} must survive at 'true', got {1!r}".format(comp_nv, held))


@pytest.mark.parametrize("key,nvpair,companion,comp_nv", DIRECTIONS)
def test_merged_does_not_withdraw_the_omitted_direction(key, nvpair, companion, comp_nv):
    """Under ``merged`` an omission preserves. Only ``replaced`` withdraws.

    Without this the reset cases above would not establish that the withdrawal belongs to
    ``replaced``: an omission that cleared the field under every state would be a different, much
    worse behaviour that the same assertions would happily accept.
    """
    result, calls = run(_profile_holding(companion), "merged", have=_both_true_have())
    assert not result.get("failed"), result.get("msg")
    sent = request_nvpairs(calls)
    assert RESET not in [m[nvpair] for m in sent if nvpair in m], (
        "{0} was reset under `merged`; an omission there must preserve".format(nvpair))


@pytest.mark.parametrize("key,nvpair,companion,comp_nv", DIRECTIONS)
def test_check_mode_plans_the_reset_and_writes_nothing(key, nvpair, companion, comp_nv):
    """The plan is visible and the controller is untouched.

    ``updates`` and ``deploys`` are asserted separately: a single "writes" bucket cannot show a run
    that configured nothing yet still deployed.
    """
    result, calls = run(_profile_holding(companion), "replaced",
                        have=_both_true_have(), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    # `split_calls` returns a DICT, not a tuple. Unpacking it bound the four KEYS as strings, so
    # `len(updates)` was `len("updates")` == 7 and the message read like a real request count. An
    # assertion phrased `>= 1` would have passed for an entirely wrong reason.
    buckets = split_calls(calls)
    assert buckets["updates"] == [], (
        "check mode sent {0} configuration request(s)".format(len(buckets["updates"])))
    assert buckets["deploys"] == [], (
        "check mode sent {0} deploy request(s)".format(len(buckets["deploys"])))
    # The name of this case promises the reset is PLANNED, so it has to assert that too. Asserting
    # only "nothing was written" would pass for a run that also planned nothing -- which is the
    # difference between a working check mode and a check mode that quietly does no work.
    planned = [m[nvpair] for m in diff_nvpairs(result) if nvpair in m]
    assert planned == [RESET], (
        "check mode did not plan the reset for {0}: {1!r}".format(nvpair, planned))


@pytest.mark.parametrize("key,nvpair,companion,comp_nv", DIRECTIONS)
def test_rerun_over_the_reset_converges(key, nvpair, companion, comp_nv):
    """``have == reset_wire`` is nothing to withdraw, so the second run must not write.

    Idempotency here is the absence of a configuration request, not a ``changed`` flag.
    """
    have = build_have(ROUTED, key=key, value=False, **{companion: True})
    result, calls = run(_profile_holding(companion), "replaced", have=have)
    assert not result.get("failed"), result.get("msg")
    buckets = split_calls(calls)
    assert buckets["updates"] == [], (
        "a rerun over the established reset sent {0} configuration request(s)"
        .format(len(buckets["updates"])))


# --------------------------------------------------------------- scope of the registration

SISTERS_WITHOUT_RESET = ["enable_ospf", "ospf_area_id", "ospf_tag", "disable_bfd_echo"]


@pytest.mark.parametrize("key", SISTERS_WITHOUT_RESET)
def test_a_sister_binding_on_the_same_parent_still_refuses(key):
    """Registering these two must not relax fail-closed for the rest of the parent.

    ``int_routed_host`` carries many registered fields with no measured reset. If this lot had
    widened the behaviour instead of registering two rows, these would have started returning a
    reset for a value nobody measured -- which is the failure mode the whole campaign exists to
    prevent.
    """
    binding = resolve_binding(ROUTED, key)
    assert binding is not None, "{0}::{1} is not registered".format(ROUTED, key)
    assert binding.get("reset_wire") is None, (
        "{0}::{1} gained a reset this lot never measured".format(ROUTED, key))
    action, wire = gie_withdrawal_action(ROUTED, key, "true", SUPPORTED)
    assert action not in (GIE_WITHDRAW_RESET, GIE_WITHDRAW_NONE), (
        "{0}::{1} now answers {2!r} for a configured value with no registered reset"
        .format(ROUTED, key, action))
    assert wire is None


# The two vPC parents declare the same public keys and were NOT measured: SMU90 has one leaf and one
# spine, no `feature vpc`, so no vPC pair exists to test them on. Registering them from this parent's
# result is exactly the "copy it to the other parents" move the mandate forbids, and this case is what
# would catch it.
VPC_PARENTS = ["int_vpc_access_host", "int_vpc_trunk_host"]


@pytest.mark.parametrize("parent", VPC_PARENTS)
@pytest.mark.parametrize("key", [TX, RX])
def test_the_unmeasured_vpc_parents_did_not_inherit_the_reset(parent, key):
    """Same public key, different parent, no measurement: still no reset."""
    binding = resolve_binding(parent, key)
    assert binding is not None, "{0}::{1} is not registered".format(parent, key)
    assert binding.get("reset_wire") is None, (
        "{0}::{1} gained a reset from the routed measurement; support is per parent and this one "
        "was never measured".format(parent, key))


# --------------------------------------------------------------- fixtures other suites depend on

# Registering a reset has consequences the suite's own guards enforce, and it bit three times.
#
# `test_dcnm_intf_withdrawal.py` and `test_gie_withdrawal_classifier.py` each pick a concrete
# (parent, key) as the fixture for a property. When a row's registration status changes under them,
# those cases stop testing what their names say -- and several keep PASSING, which is worse than
# failing because nobody looks.
#
# History of this exact fixture:
#   * it was ``int_access_host::disable_lldp_receive``; the access batch measured its reset, so the
#     C7 cases were rehomed to ``int_routed_host::disable_lldp_receive``;
#   * this lot measured that one, so they were rehomed again, to ``int_routed_host::disable_bfd_echo``;
#   * in doing so I over-replaced and put ``bfdEcho`` into two ACCESS cases where it is NOT
#     registered at all, making them pass while exercising nothing. The peer review caught it.
#
# So the guard is no longer about one row. It is a table of every fixture those suites rely on, with
# the property each one needs, checked by that property rather than by name. `reset` means the row
# must carry a measured reset; `no_reset` means it must not, and must declare a default so a
# configured value classifies as UNSUPPORTED rather than UNCLASSIFIED.
FIXTURE_CONTRACTS = [
    # (parent, key, requirement, which cases depend on it)
    pytest.param(ROUTED, "disable_bfd_echo", "no_reset",
                 "the C7 unsupported row: test_c7_*, test_check_mode_also_refuses_*, "
                 "test_valid_first_interface_unsupported_second_*, "
                 "test_merged_is_never_blocked_by_an_unsupported_row, and the classifier's "
                 "differs_no_reset row",
                 id="routed-bfd_echo-no_reset"),
    pytest.param(ACCESS, "disable_lldp_receive", "reset",
                 "test_equivalent_have_encodings_classify_identically (needs a REGISTERED row so "
                 "the HAVE validator processes both encodings) and "
                 "test_deleted_state_does_not_enter_the_withdrawal_path (needs a row `replaced` "
                 "would actually withdraw, so `deleted` skipping it means something)",
                 id="access-lldp_receive-reset"),
]


@pytest.mark.parametrize("parent,key,requirement,dependents", FIXTURE_CONTRACTS)
def test_the_fixtures_other_suites_rely_on_still_have_the_property_they_need(
        parent, key, requirement, dependents):
    """Every fixture must be REGISTERED on its own parent, and hold the property it was picked for.

    The first half is what the review caught: an unregistered key resolves to no binding, the engine
    answers NONE, and the dependent cases pass having exercised nothing. Registration is checked per
    parent because support is per parent -- the same public key can be registered on one and absent
    on another, which is exactly how the mistake happened.

    When this fails, do NOT relax the dependent cases. Pick another row that has the required
    property, rehome them, and update this table. If none is left, that is the real news and belongs
    in a report rather than in a test edit.
    """
    binding = resolve_binding(parent, key)
    assert binding is not None, (
        "{0}::{1} is not registered on that parent, so a HAVE carrying it is ignored by the engine "
        "and these cases pass while exercising nothing: {2}".format(parent, key, dependents))
    reset = binding.get("reset_wire")
    if requirement == "reset":
        assert reset is not None, (
            "{0}::{1} lost its reset, so the cases that need a withdrawable row no longer have "
            "one: {2}".format(parent, key, dependents))
    elif requirement == "no_reset":
        assert reset is None, (
            "{0}::{1} gained a reset, so it is no longer an unsupported row and these cases are no "
            "longer testing a refusal: {2}".format(parent, key, dependents))
        assert binding.get("default_template") is not None, (
            "{0}::{1} declares no default_template, so a configured value classifies as "
            "UNCLASSIFIED rather than UNSUPPORTED and the message those cases assert would "
            "differ".format(parent, key))
    else:
        raise AssertionError("unknown requirement %r" % requirement)


# The earlier guard, `test_the_rehomed_c7_row_is_genuinely_unsupported`, covered ONLY the ROUTED
# row and is subsumed by FIXTURE_CONTRACTS above. It was REMOVED rather than left alongside: two
# sources of the same truth drift apart, and this campaign already paid for that once (the
# `resumen` of vo_ospf_process kept its own copy of the inverted default after the guard was
# corrected).
