"""Regression for the S2 neutral-enum omission defect, on all eight rows.

THE DEFECT

`gie_declared_default_wire()` serialized `default_template` -- which is recorded in the PUBLIC
vocabulary -- without the wire-value mapping, while `gie_withdrawal_action()` compares a HAVE
that came FROM the controller against it. So a field already sitting at its SMU declared
neutral read as `no_change` on one side and `noChange` on the other, classified as an
unclassifiable value, and refused the whole invocation. `merged` was unaffected, which is why
it is the positive control below.

The fix translates at the declared-default boundary, so both sides of that comparison are in
the wire representation. No reset was registered for these rows, the public vocabulary did not
move, and the general withdrawal contract is untouched.

WHY THESE EXPECTATIONS ARE INDEPENDENT

The neutral spellings are transcribed by hand from the captured declarations (capture-S2,
byte-identical to capture-R2 at 12.6.0.267), not obtained from the mapper under test:

    ospfNetworkType   validValues=noChange,broadcast,pointToPoint   defaultValue=noChange
    ospfBfdMode       validValues=noChange,enable,disable           defaultValue=noChange
    ospfPassiveMode   validValues=noChange,passive,noPassive        defaultValue=noChange

NOT LIVE TESTED ON SMU. Offline only.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table as table
from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine as engine

from .gie_withdrawal_harness import SUPPORTED, base_for, build_have, run, split_calls

# Hand-transcribed neutral value per enum wire key.
REVIEWED_NEUTRAL = {
    "ospfNetworkType": "noChange",
    "ospfBfdMode": "noChange",
    "ospfPassiveMode": "noChange",
}


def _rows():
    t = table.BINDING_TABLE
    return list(t.values()) if isinstance(t, dict) else list(t)


NEUTRAL_ROWS = sorted((b["parent_template"], b["profile_key"], b["parent_nvpair"]) for b in _rows() if b["parent_nvpair"] in REVIEWED_NEUTRAL)
NEUTRAL_IDS = ["%s::%s" % (p.replace("int_", ""), k) for p, k, _nv in NEUTRAL_ROWS]


def test_the_derived_set_covers_all_eight_neutral_enum_rows():
    """Guard the guard: eight rows over three fields and five parents."""
    assert len(NEUTRAL_ROWS) == 8, NEUTRAL_ROWS
    assert {nv for _p, _k, nv in NEUTRAL_ROWS} == set(REVIEWED_NEUTRAL)


@pytest.mark.parametrize("parent,profile_key,nvpair", NEUTRAL_ROWS, ids=NEUTRAL_IDS)
def test_the_declared_default_is_serialized_in_the_wire_vocabulary(parent, profile_key, nvpair):
    """The exact boundary that was wrong: the default must be the controller's spelling."""
    binding = engine.resolve_binding(parent, profile_key)
    assert engine.gie_declared_default_wire(binding) == REVIEWED_NEUTRAL[nvpair]


@pytest.mark.parametrize("parent,profile_key,nvpair", NEUTRAL_ROWS, ids=NEUTRAL_IDS)
def test_a_have_at_the_declared_neutral_is_already_withdrawn(parent, profile_key, nvpair):
    """No reset exists for these rows, so a HAVE already neutral must be a no-op -- not an
    unclassifiable value, and not an invented reset."""
    action, wire = engine.gie_withdrawal_action(parent, profile_key, REVIEWED_NEUTRAL[nvpair], SUPPORTED)
    assert action == engine.GIE_WITHDRAW_NONE, (action, wire)


@pytest.mark.parametrize("parent,profile_key,nvpair", NEUTRAL_ROWS, ids=NEUTRAL_IDS)
def test_the_pre_smu_spelling_is_not_silently_accepted_as_neutral(parent, profile_key, nvpair):
    """This build is SMU-only, so there is exactly ONE neutral representation.

    Before the fix the comparison held the PUBLIC spelling, so `no_change` in a HAVE read as
    neutral and the controller's own `noChange` did not. The fix moves the comparison to the
    wire representation; the mirror image must NOT be introduced as a second accepted
    spelling, because dual-schema support is explicitly out of scope. A controller on this
    build never returns `no_change`, so seeing it is an unrecognised value and is refused --
    not quietly treated as already-withdrawn.
    """
    action, _wire = engine.gie_withdrawal_action(parent, profile_key, "no_change", SUPPORTED)
    # THE GUARANTEE, invariant and the whole reason this case exists: the pre-SMU spelling is
    # NEVER read as already-withdrawn.
    assert action != engine.GIE_WITHDRAW_NONE, (
        "the pre-SMU spelling was read as already-withdrawn: %r" % action)
    # The CONCRETE outcome depends on whether the row carries a registered reset, and both
    # branches are declared rather than letting a future registration invalidate the case:
    #
    #   no reset   -> UNSUPPORTED: there is no known way to withdraw it, so it fails closed.
    #   with reset -> RESET: it differs from the neutral, so it is NORMALISED by sending it.
    #
    # B3 registered two of these eight rows, which is what stopped the second branch from
    # being hypothetical. The first version of this case covered only the first branch.
    binding = engine.resolve_binding(parent, profile_key)
    if binding.get("reset_wire") is None:
        assert action == engine.GIE_WITHDRAW_UNSUPPORTED, action
    else:
        assert action == engine.GIE_WITHDRAW_RESET, action


@pytest.mark.parametrize("state", ["replaced", "merged"])
@pytest.mark.parametrize("check_mode", [False, True])
def test_main_omitting_a_neutral_field_writes_nothing(state, check_mode):
    """Through real main(): omission of a field already at its neutral sends nothing, in
    replaced and in check mode. merged is the positive control that never regressed."""
    have = build_have("int_routed_host", "ospf_passive_mode", "no_change", enable_ospf=True)
    nv = have[0]["interfaces"][0]["nvPairs"]
    assert nv.get("ospfPassiveMode") == "noChange", sorted(nv)

    want = base_for("int_routed_host", enable_ospf=True)
    assert "ospf_passive_mode" not in want

    result, calls = run(
        want,
        state,
        have=copy.deepcopy(have),
        parent="int_routed_host",
        check_mode=check_mode,
    )
    assert not result.get("failed"), result.get("msg")
    buckets = split_calls(calls)
    assert buckets["updates"] == [], "a neutral field produced a configuration update"
    assert buckets["deploys"] == []


# ------------------------------------------------------------------- positive controls
@pytest.mark.parametrize(
    "public,wire",
    [("no_change", "noChange"), ("passive", "passive"), ("no_passive", "noPassive")],
)
def test_an_explicit_public_value_still_encodes_to_its_reviewed_wire_value(public, wire):
    add, err = engine.gie_contribute_nvpairs("int_routed_host", {"enable_ospf": True, "ospf_passive_mode": public}, SUPPORTED)
    assert err is None, err
    assert add["ospfPassiveMode"] == wire, add


def test_an_unknown_value_does_not_become_neutral():
    """The fix must not turn anything it does not recognise into the neutral default."""
    with pytest.raises(engine.GieBindingError):
        engine.gie_validate_binding_value("int_routed_host", "ospf_passive_mode", "bogus")
    action, _wire = engine.gie_withdrawal_action("int_routed_host", "ospf_passive_mode", "somethingElse", SUPPORTED)
    assert action != engine.GIE_WITHDRAW_NONE, "an unknown value was read as neutral"


def test_a_configured_enum_without_a_measured_reset_still_fails_closed_when_omitted():
    """The contract that must NOT have been weakened: a non-neutral configured value on a row
    with no measured reset still refuses, rather than being silently left or reset.

    The example is DERIVED from the table instead of hardcoded. It used to name
    `int_routed_host::ospf_passive_mode`, and B3 registered a reset for exactly that row --
    which made the case fail while the contract it guards was intact. Deriving it means a
    future registration can never invalidate this case; if the table ever ran out of
    unregistered neutral enums, the guard below says so loudly instead of the case passing
    for the wrong reason.
    """
    without_reset = [(p, k, nv) for (p, k, nv) in NEUTRAL_ROWS
                     if (engine.resolve_binding(p, k) or {}).get("reset_wire") is None]
    assert without_reset, (
        "every reviewed neutral enum now carries a reset; this case has nothing left to "
        "guard and must be rehomed deliberately, not deleted")
    for parent, profile_key, _nvpair in without_reset:
        binding = engine.resolve_binding(parent, profile_key)
        configured = next(v for pub, v in binding["wire_values"].items()
                          if pub != "no_change")
        action, _wire = engine.gie_withdrawal_action(
            parent, profile_key, configured, SUPPORTED)
        assert action == engine.GIE_WITHDRAW_UNSUPPORTED, (
            "%s::%s has no reset, so HAVE=%r must fail closed, got %r"
            % (parent, profile_key, configured, action))


def test_merged_preservation_still_works_for_a_neutral_row():
    have = build_have("int_routed_host", "ospf_passive_mode", "passive", enable_ospf=True)
    want = base_for("int_routed_host", enable_ospf=True)
    result, calls = run(want, "merged", have=copy.deepcopy(have), parent="int_routed_host")
    assert not result.get("failed"), result.get("msg")
    assert split_calls(calls)["updates"] == []


def test_unrelated_default_handling_is_untouched():
    """A boolean, a string and an integer default keep their previous wire serialization."""
    cases = [
        ("int_access_host", "disable_lldp_receive", "false"),
        ("int_access_host", "acl_filter", None),
        ("int_routed_host", "ospf_cost", None),
    ]
    for parent, key, expected in cases:
        binding = engine.resolve_binding(parent, key)
        got = engine.gie_declared_default_wire(binding)
        if expected is None:
            assert got is None or isinstance(got, str), (parent, key, got)
        else:
            assert got == expected, (parent, key, got)
