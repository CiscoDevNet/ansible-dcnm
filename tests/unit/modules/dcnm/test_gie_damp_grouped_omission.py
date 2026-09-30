"""Dampening: the SEVEN withdrawn as one group, through the real `main()`.

EXPERIMENTAL / CONTROLLER-ONLY. The seven resets these cases rely on are CANDIDATES from a
local experimental generation, registered so the omission path can be executed and observed at
a controller. They are NOT accepted device resets, they are NOT part of the 157 integration,
and nothing was deployed in the campaign that produced them -- so no device acceptance exists
for any of the seven. See investigations/pr725-dampening-all/EXPERIMENTAL_LEDGER.md.

WHY THIS FILE EXISTS RATHER THAN SEVEN PER-ROW FIXTURES

The parent declares five conditional rules over this family, and rule 2 (`all_or_none`) makes
`dampeningReuse`, `dampeningSuppress` and `dampeningMaxSuppress` withdrawable only TOGETHER: a
per-row omission of any one of them describes a controller state that cannot exist -- two of
the three present, one absent. A per-row fixture for those would be green in the mock and
impossible on a controller, which is the failure mode the pilot matrix exists to avoid. They
are named in `GROUPED_ONLY_NO_PER_ROW_FIXTURE` in the harness and covered here instead.

The other four DO have per-row fixtures in the matrix; they are re-exercised here as part of
the group, because "each one works alone" and "all seven work together in one request" are
different statements.

WHAT IS ASSERTED

The captured REQUEST and the PUBLIC DIFF, never `changed` alone. Deploy flags are asserted
FALSE on every case: this campaign's whole contract is that nothing reaches a device.

Offline. No controller and no device.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    resolve_binding,
)

from .gie_withdrawal_harness import (
    GROUPED_ONLY_NO_PER_ROW_FIXTURE,
    IF_A,
    ROUTED,
    base_for,
    build_have,
    cfg,
    diff_nvpairs,
    request_nvpairs,
    run_configs,
    split_calls,
)

# The valid seven-field positive: it satisfies all five conditional rules and every declared
# range. Written out rather than derived, so a change to the rules shows up as a failure here
# instead of being silently followed.
POSITIVE = {
    "enable_dampening": True,          # rule 1: any explicit value needs the gate
    "dampening_half_life": 5,          # 1..30      -- rule 3: reuse needs it
    "dampening_reuse": 750,            # 1..20000   -- rule 2: with suppress + max
    "dampening_suppress": 2000,        # 1..20000
    "dampening_max_suppress": 60,      # 1..255
    "dampening_restart": True,         # rule 4: needs half_life+reuse+suppress+max
    "dampening_restart_penalty": 1000,  # 1..20000  -- rule 5: needs restart true
}

# nvPair spelling, and the reset each identity is entitled to. Hand-written, independent of the
# table: an expectation read back from the subject under test cannot fail.
EXPECTED_RESET = {
    "dampening": "false",
    "dampeningRestart": "false",
    "dampeningHalfLife": "",
    "dampeningReuse": "",
    "dampeningSuppress": "",
    "dampeningMaxSuppress": "",
    "dampeningRestartPenalty": "",
}

# What the controller holds once the positive is applied, per identity.
EXPECTED_APPLIED = {
    "dampening": "true",
    "dampeningRestart": "true",
    "dampeningHalfLife": "5",
    "dampeningReuse": "750",
    "dampeningSuppress": "2000",
    "dampeningMaxSuppress": "60",
    "dampeningRestartPenalty": "1000",
}


def _have():
    return build_have(ROUTED, **POSITIVE)


def _run(profile, state, **kw):
    """Drive `main()` with `deploy: False`, which is what the live campaign used in EVERY
    stage. The harness default is `deploy=True`; leaving it would assert against a model this
    campaign never sent, and the deploy-flag assertions below would be meaningless."""
    return run_configs([cfg(IF_A, profile, deploy=False)], state, deploy=False, **kw)


def test_the_seven_are_registered_before_anything_below_is_meaningful():
    """Guard the guard. Without the experimental metadata the module REFUSES these omissions,
    and a refusal is not a withdrawal -- every case below would pass for the wrong reason."""
    for nvpair, reset in sorted(EXPECTED_RESET.items()):
        key = [k for k in POSITIVE
               if resolve_binding(ROUTED, k)["parent_nvpair"] == nvpair][0]
        b = resolve_binding(ROUTED, key)
        assert b.get("reset_wire") == reset, (
            "%s::%s reset is %r, declared %r" % (ROUTED, nvpair, b.get("reset_wire"), reset))
        assert isinstance(b["reset_wire"], str), (
            "%s::%s reset_wire is %s; the controller returns this nvPair as a string"
            % (ROUTED, nvpair, type(b["reset_wire"]).__name__))


def test_the_three_all_or_none_members_are_the_declared_grouped_only_set():
    """The harness's declaration and this file's reason must not drift apart. If a per-row
    fixture is ever added for one of the three, this fails and points at the rule that made it
    impossible."""
    assert set(GROUPED_ONLY_NO_PER_ROW_FIXTURE) == {
        (ROUTED, "dampeningReuse"),
        (ROUTED, "dampeningSuppress"),
        (ROUTED, "dampeningMaxSuppress"),
    }, sorted(GROUPED_ONLY_NO_PER_ROW_FIXTURE)


def test_the_omission_model_carries_none_of_the_seven():
    """The absence must be EFFECTIVE, not a `false`/`''` the fixture slipped in. A model that
    re-declared the targets would make every case below an ordinary apply."""
    want = base_for(ROUTED)
    present = [k for k in POSITIVE if k in want]
    assert not present, "the omission model still declares: %s" % present


def test_merged_preserves_all_seven():
    """CONTROL: the resets below belong to the WITHDRAWAL path, not to the shape of the model.
    Under `merged` the same omission preserves every one of the seven."""
    result, calls = _run(base_for(ROUTED, description="damp-merged"), "merged", have=_have())
    assert not result.get("failed"), result.get("msg")
    nv = request_nvpairs(calls)
    assert nv, "the description change produced no request"
    for nvpair, applied in sorted(EXPECTED_APPLIED.items()):
        assert nv[0].get(nvpair) == applied, (
            "merged did not preserve %s: %r, expected %r"
            % (nvpair, nv[0].get(nvpair), applied))
    assert split_calls(calls)["deploys"] == [], "merged sent a deploy request"


def test_check_mode_plans_all_seven_and_transmits_nothing():
    """A plan is not a write. "It did not write" alone would also describe a check mode that
    planned nothing at all, so both halves are asserted."""
    result, calls = _run(base_for(ROUTED), "replaced", have=_have(), check_mode=True)
    dnv = diff_nvpairs(result)
    assert dnv, "check mode planned nothing at all"
    for nvpair, reset in sorted(EXPECTED_RESET.items()):
        assert dnv[0].get(nvpair) == reset, (
            "check mode did not plan %s: %r, expected %r"
            % (nvpair, dnv[0].get(nvpair), reset))
    buckets = split_calls(calls)
    assert buckets["updates"] == [], "check mode sent a configuration request"
    assert buckets["deploys"] == [], "check mode sent a deploy request"


def test_replaced_withdraws_all_seven_in_one_request():
    """The grouped property: one payload carries all seven resets.

    EXACTLY one update. "All seven appear somewhere" would also be true of a run that split
    them across requests, and the all_or_none rule means a split is precisely the shape the
    controller would refuse.
    """
    result, calls = _run(base_for(ROUTED), "replaced", have=_have())
    assert not result.get("failed"), result.get("msg")
    updates = split_calls(calls)["updates"]
    assert len(updates) == 1, "expected exactly one request, got %d" % len(updates)
    assert split_calls(calls)["deploys"] == [], (
        "the withdrawal sent a deploy request; this campaign is deploy:false throughout")
    nv = request_nvpairs(calls)
    for nvpair, reset in sorted(EXPECTED_RESET.items()):
        assert nv[0].get(nvpair) == reset, (
            "%s travelled as %r, expected the reset %r" % (nvpair, nv[0].get(nvpair), reset))
    # And the public diff owns all seven too, independently of the request body.
    dnv = diff_nvpairs(result)
    assert dnv, "nothing was reported in the public diff"
    for nvpair, reset in sorted(EXPECTED_RESET.items()):
        assert dnv[0].get(nvpair) == reset, (
            "%s was reset in the request but is %r in the diff" % (nvpair, dnv[0].get(nvpair)))


@pytest.mark.parametrize("nvpair", sorted(EXPECTED_RESET))
def test_the_five_numbers_are_cleared_per_identity_not_by_the_gate_alone(nvpair):
    """Per-identity, so turning the gate off cannot masquerade as clearing the numbers.

    This is the whole reason the assertions are per-nvPair rather than "the rendered line is
    gone": on a controller the gate empties the RENDER while the five value nvPairs keep their
    contents, so a line-level check would score a partial clear as complete.
    """
    _result, calls = _run(base_for(ROUTED), "replaced", have=_have())
    nv = request_nvpairs(calls)[0]
    assert nv.get(nvpair) == EXPECTED_RESET[nvpair], (
        "%s is %r, expected %r" % (nvpair, nv.get(nvpair), EXPECTED_RESET[nvpair]))


def test_unrelated_fields_survive_the_grouped_withdrawal():
    """A reset that spilled onto a field nobody withdrew would be invisible in a count."""
    have = _have()
    before = dict(have[0]["interfaces"][0]["nvPairs"])
    _result, calls = _run(base_for(ROUTED), "replaced", have=have)
    nv = request_nvpairs(calls)[0]
    spilled = {
        k: (before[k], nv.get(k))
        for k in before
        if not k.startswith("dampening") and k in nv and nv[k] != before[k]
    }
    assert not spilled, "the withdrawal changed fields nobody omitted: %s" % spilled
