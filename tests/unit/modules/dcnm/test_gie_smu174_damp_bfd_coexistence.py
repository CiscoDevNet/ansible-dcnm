"""Do the seven dampening resets and the routed BFD echo reset coexist in ONE real request?

WHY THIS FILE EXISTS

`test_gie_damp_grouped_omission.py` drives the seven dampening identities as a group, and the
pilot matrix in `test_dcnm_intf_withdrawal.py` drives `int_routed_host::disable_bfd_echo` on its
own. Neither asks whether a single `replaced` request can carry BOTH withdrawals: the dampening
suite omits only dampening keys, and the BFD row is exercised with an empty prerequisite context.
Checked before writing this file -- no fixture in the harness mixes the two families, and no
existing test drives them through one module invocation.

WHY THIS COMBINATION IS A VALID ONE TO BUILD

Both identities live on `int_routed_host`, and neither gates the other: dampening is an interface
dampening feature with its own gate and numeric group, while `bfdEcho` is a BFD interface option.
The dampening group is supplied in full -- gate, half-life, reuse, suppress, max-suppress and
restart -- because the parent refuses a partial group, and `disable_bfd_echo` needs no
prerequisite of its own. So this is a configuration that stands on its own rather than a pile of
fields assembled to inflate a payload.

Deploy travels FALSE, which is what the dampening campaign used in every stage. The harness
default is `deploy=True`; leaving it would assert against a model that campaign never sent.

EVIDENCE STATUS, KEPT APART DELIBERATELY

The BFD reset retains its source-campaign live acceptance. The seven dampening resets are
CONTROLLER_OMISSION_VERIFIED / DEVICE_NOT_VALIDATED: their omission was observed at the
controller with deploy false, NX-OS withdrawal was never validated, and the lab platform does not
support that CLI. Putting them in one offline request proves they coexist in the module's
withdrawal path. It does not upgrade the dampening evidence, and nothing here should be read as
device validation of anything.

Offline. Real `main()`, real argument spec, real validation, real serialisation; mocks only at
inventory/transport. Assertions are against the CAPTURED REQUEST and the PUBLIC DIFF, never
against `changed`. NOT LIVE TESTED.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    resolve_binding,
)

from .gie_withdrawal_harness import (
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

# The full dampening group the parent requires, plus the BFD echo option. Written by hand: an
# expectation read back from the subject under test cannot fail.
POSITIVE = {
    "enable_dampening": True,
    "dampening_half_life": 5,
    "dampening_reuse": 750,
    "dampening_suppress": 2000,
    "dampening_max_suppress": 60,
    "dampening_restart": True,
    "dampening_restart_penalty": 1000,
    "disable_bfd_echo": True,
}

# nvPair spelling -> the reset each identity is entitled to. Eight rows: seven dampening and
# the BFD echo. Two of the dampening rows and the BFD row reset with the wire STRING 'false';
# the five dampening numbers reset with the EMPTY STRING. Those are different values and the
# distinction is the point -- a copy-paste of one onto the other must fail here.
EXPECTED_RESET = {
    "dampening": "false",
    "dampeningRestart": "false",
    "dampeningHalfLife": "",
    "dampeningReuse": "",
    "dampeningSuppress": "",
    "dampeningMaxSuppress": "",
    "dampeningRestartPenalty": "",
    "bfdEcho": "false",
}
DAMP_NVPAIRS = [nv for nv in EXPECTED_RESET if nv != "bfdEcho"]

# What the controller holds once the positive is applied.
EXPECTED_APPLIED = {
    "dampening": "true",
    "dampeningRestart": "true",
    "dampeningHalfLife": "5",
    "dampeningReuse": "750",
    "dampeningSuppress": "2000",
    "dampeningMaxSuppress": "60",
    "dampeningRestartPenalty": "1000",
    "bfdEcho": "true",
}


def _have():
    return build_have(ROUTED, **POSITIVE)


def _run(profile, state, **kw):
    return run_configs([cfg(IF_A, profile, deploy=False)], state, deploy=False, **kw)


def _omitting_everything():
    """The withdrawal model: the base routed profile with NONE of the eight keys present.

    `base_for` is not enough on its own for a key that the base profile itself declares, so each
    target is popped explicitly and the result asserted empty of all eight. A model that still
    carried one of them would make this an ordinary apply for that row.
    """
    w = dict(base_for(ROUTED))
    for key in POSITIVE:
        w.pop(key, None)
    return w


# ===================================================== the registration, guarded
def test_all_eight_are_registered_before_anything_below_is_meaningful():
    """Guard the guard. If any of the eight lost its reset the module would REFUSE, and a
    refusal is not a withdrawal -- every case below would pass for the wrong reason."""
    pairs = [(nv, EXPECTED_RESET[nv]) for nv in EXPECTED_RESET]
    for nvpair, reset in pairs:
        rows = [r for r in [resolve_binding(ROUTED, k) for k in POSITIVE] if r]
        row = [r for r in rows if r["parent_nvpair"] == nvpair]
        assert row, "%s::%s is not in the table at all" % (ROUTED, nvpair)
        got = row[0].get("reset_wire")
        assert got == reset, "%s::%s reset is %r, expected %r" % (ROUTED, nvpair, got, reset)
        assert isinstance(got, str), (
            "%s::%s reset_wire is %s; the controller returns this nvPair as a string"
            % (ROUTED, nvpair, type(got).__name__))


def test_the_withdrawal_model_carries_none_of_the_eight():
    """The omission has to be real. If a target survived in the model this would be an apply."""
    w = _omitting_everything()
    present = sorted(k for k in POSITIVE if k in w)
    assert not present, "the withdrawal model still declares %r" % (present,)


# ============================================ one request, both families withdrawn
def test_one_replaced_request_carries_all_seven_dampening_resets_and_the_bfd_echo_reset():
    """The union property neither family's own suite states: eight resets, one payload.

    Each of the eight is checked SEPARATELY, by nvPair and by exact value. A count would pass
    while one row carried the wrong neutral.
    """
    result, calls = _run(_omitting_everything(), "replaced", have=_have())
    assert not result.get("failed"), result.get("msg")
    nv = request_nvpairs(calls)
    assert nv, ("no request was sent, so neither family's omission was detected. changed=%s"
                % result.get("changed"))
    assert len(split_calls(calls)["updates"]) == 1, (
        "expected exactly one configuration request, got %d"
        % len(split_calls(calls)["updates"]))
    for nvpair, reset in EXPECTED_RESET.items():
        assert nv[0].get(nvpair) == reset, (
            "%s travelled as %r, expected %r" % (nvpair, nv[0].get(nvpair), reset))
    # The public diff must own all eight too, independently of the request body.
    dnv = diff_nvpairs(result)
    assert dnv, "the run reported no public diff at all"
    for nvpair, reset in EXPECTED_RESET.items():
        assert dnv[0].get(nvpair) == reset, (
            "%s is absent from or wrong in the public diff: %r" % (nvpair, dnv[0].get(nvpair)))


# Explicit wire values from the routed base profile and its stable defaults. These are not
# derived from a second module request: that request can be a no-op and compare nothing.
EXPECTED_RETAINED_WIRE = {
    "DESC": "pilot",
    "FEC": "auto",
    "IP": "192.0.2.1",
    "PREFIX": "30",
    "INTF_VRF": "default",
    "OSPF_AREA_ID": "0.0.0.0",
    "ospf": "true",
    "MTU": "9216",
}


def _assert_untargeted_wire(nv):
    assert EXPECTED_RETAINED_WIRE, "no retained wire fields were specified"
    assert not set(EXPECTED_RETAINED_WIRE) & set(EXPECTED_RESET), (
        "a withdrawal target was included among retained fields")
    for field, value in EXPECTED_RETAINED_WIRE.items():
        assert field in nv, "untargeted %s is absent from the withdrawal request" % field
        assert nv[field] == value, (
            "untargeted %s changed during the combined withdrawal: %r, expected %r"
            % (field, nv[field], value))


def test_the_untargeted_prerequisites_survive_the_combined_withdrawal():
    """A reset that spilled onto a field nobody withdrew would be invisible in a count.

    `base_for(ROUTED)` supplies description, FEC, IP/prefix and OSPF; the module supplies the
    stable MTU and VRF defaults. None is a withdrawal target here; each must arrive unchanged.
    """
    result, calls = _run(_omitting_everything(), "replaced", have=_have())
    assert not result.get("failed"), result.get("msg")
    nv = request_nvpairs(calls)
    assert len(nv) == 1, "expected one actual withdrawal request, got %d" % len(nv)
    _assert_untargeted_wire(nv[0])


@pytest.mark.parametrize("corruption", ("missing_desc", "changed_fec"))
def test_the_retained_context_guard_rejects_a_missing_or_changed_field(corruption):
    result, calls = _run(_omitting_everything(), "replaced", have=_have())
    assert not result.get("failed"), result.get("msg")
    requests = request_nvpairs(calls)
    assert len(requests) == 1, "the negative control has no withdrawal payload"
    nv = dict(requests[0])
    _assert_untargeted_wire(nv)  # the untouched candidate must pass the same guard
    if corruption == "missing_desc":
        del nv["DESC"]
        field = "DESC"
    else:
        nv["FEC"] = "unexpected"
        field = "FEC"
    with pytest.raises(AssertionError, match="untargeted %s" % field):
        _assert_untargeted_wire(nv)


# =================================================================== controls
def test_merged_withdraws_nothing_from_either_family():
    """CONTROL: the eight resets above belong to the WITHDRAWAL path, not to the model's shape.
    Under `merged` the same omission preserves every one of them."""
    result, calls = _run(dict(_omitting_everything(), description="damp-bfd-merged"),
                         "merged", have=_have())
    assert not result.get("failed"), result.get("msg")
    nv = request_nvpairs(calls)
    assert nv, "the description change produced no request"
    for nvpair, applied in EXPECTED_APPLIED.items():
        assert nv[0].get(nvpair) == applied, (
            "merged changed %s to %r; an omission there must preserve %r"
            % (nvpair, nv[0].get(nvpair), applied))


def test_check_mode_plans_all_eight_and_transmits_nothing():
    """CONTROL: a plan is not a write. "It did not write" alone would also describe a check
    mode that planned nothing at all, so both halves are asserted."""
    result, calls = _run(_omitting_everything(), "replaced", have=_have(), check_mode=True)
    dnv = diff_nvpairs(result)
    assert dnv, "check mode planned nothing at all"
    for nvpair, reset in EXPECTED_RESET.items():
        assert dnv[0].get(nvpair) == reset, (
            "check mode did not plan %s as %r: %r" % (nvpair, reset, dnv[0].get(nvpair)))
    buckets = split_calls(calls)
    assert buckets["updates"] == [], "check mode sent a configuration request"
    assert buckets["deploys"] == [], "check mode sent a deploy request"


def test_rerun_from_the_withdrawn_state_converges():
    """CONTROL: with all eight already at their reset, the same model must configure nothing.
    `changed` alone is not the evidence -- the request buckets are."""
    withdrawn = build_have(ROUTED)
    for nvpair, reset in EXPECTED_RESET.items():
        withdrawn[0]["interfaces"][0]["nvPairs"][nvpair] = reset
    result, calls = _run(_omitting_everything(), "replaced", have=withdrawn)
    buckets = split_calls(calls)
    assert buckets["updates"] == [], (
        "a converged rerun sent a configuration request: %s"
        % [c["path"] for c in buckets["updates"]])
    assert buckets["deploys"] == [], "a converged rerun sent a deploy request"
    assert not result.get("failed"), result.get("msg")


def test_the_two_families_neutrals_are_not_interchangeable():
    """CONTROL: the assertions above have teeth because the neutrals differ. Three booleans
    reset to the STRING 'false' and five numbers to the EMPTY string; neither is the native
    `False`, which would never match a controller HAVE and is falsy where `'false'` is truthy."""
    booleans = {"dampening", "dampeningRestart", "bfdEcho"}
    for nvpair, reset in EXPECTED_RESET.items():
        if nvpair in booleans:
            assert reset == "false", "%s should reset to the string 'false'" % nvpair
        else:
            assert reset == "", "%s should reset to the empty string" % nvpair
        assert reset is not False and not isinstance(reset, bool), (
            "%s reset is a native bool: %r" % (nvpair, reset))
    assert len({EXPECTED_RESET[n] for n in EXPECTED_RESET}) == 2, (
        "the two neutral shapes collapsed into one, so a copy-paste between a boolean and a "
        "number would no longer be detectable here")


def test_the_dampening_evidence_status_is_not_upgraded_by_this_coexistence():
    """The seven dampening rows are registered and their omission was observed at the
    CONTROLLER with deploy false. NX-OS withdrawal was never validated and the lab platform
    does not support that CLI.

    This case asserts the only part of that a table can carry: the rows are registered, and the
    BFD row they travel beside is registered too. It deliberately asserts NOTHING about device
    behaviour, and its presence must not be read as device validation of dampening. The
    evidence split lives in the campaign reviews and in the task's support-limitation note.
    """
    for key in ("enable_dampening", "dampening_restart", "dampening_half_life",
                "dampening_reuse", "dampening_suppress", "dampening_max_suppress",
                "dampening_restart_penalty"):
        b = resolve_binding(ROUTED, key)
        assert b is not None and isinstance(b.get("reset_wire"), str), (
            "%s::%s is not registered with a string reset" % (ROUTED, key))
    echo = resolve_binding(ROUTED, "disable_bfd_echo")
    assert echo is not None and echo.get("reset_wire") == "false"
