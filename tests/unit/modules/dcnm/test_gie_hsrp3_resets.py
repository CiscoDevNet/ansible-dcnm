"""``int_vlan`` HSRP: the preempt delay and the forwarding-threshold pair, measured live.

Until this lot the three identities carried no ``reset_wire``, so omitting any of them under
``replaced`` refused the whole invocation. All three are now withdrawable.

WHERE THE VALUES COME FROM
Measured in the HSRP IPv4 source campaign on an SVI, with HSRP version 2, group 79,
documentation-range VIP 192.0.2.254, priority 120 and preempt enabled::

    positive   preempt delay minimum 45
               priority 120 forwarding-threshold lower 90 upper 110
    clear      the three nvPairs to "" through a raw preserving update (they are INTEGERS and the
               public empty string stays refused), then an interface-scoped deploy
    device     `preempt` and `priority 120` SURVIVED without their suffixes; the VIP, the version
               and the interface address were untouched

THE WITHDRAWAL DEGRADES, IT DOES NOT DELETE
The parent emits no CLI of its own. With PREEMPT true it emits either the delay child
(``preempt delay minimum <v>``) or the plain ``interface_hsrp_preempt`` child; with a priority other
than 100 it emits either the threshold child or the plain ``interface_hsrp_priority`` child. So the
reset leaves the host line in place and removes only the clause. Every case below therefore holds
``preempt`` and ``hsrp_priority`` explicit: turning either off would remove the line itself, which is
destroying the prerequisite, not withdrawing the field.

THE THRESHOLDS ARE A COORDINATED PAIR
One child emits both, and the installed body rejects either alone ("Both HSRP lower and upper
forwarding thresholds are required"). They were measured together and are covered together here;
per-row fixtures for them would describe a request the controller refuses, which is why the shared
harness lists them as grouped-only.

OUT OF THIS LOT
``hsrp_vipv6`` and ``hsrp_groupv6`` are NOT registered. On the measured controller the installed
``int_vlan`` body emitted no IPv6 line at all for this subject, so neither has an observable positive
or a measurable clear. They stay unregistered and a case below pins that.

Offline: no controller and no device.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    BINDING_TABLE,
    resolve_binding,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    GIE_WITHDRAW_NONE,
    GIE_WITHDRAW_RESET,
    gie_withdrawal_action,
)

from .gie_withdrawal_harness import (
    GROUPED_ONLY_NO_PER_ROW_FIXTURE,
    HSRP_CTX,
    SVI,
    SUPPORTED_PATCH,
    base_for,
    build_have,
    cfg_for,
    diff_nvpairs,
    request_nvpairs,
    run_configs,
    split_calls,
)

SUPPORTED = "12.6.0.267"

# (profile_key, parent_nvpair, reset_wire, the value the live positive really sent)
ROWS = [
    ("hsrp_preempt_delay_minimum", "hsrpPreemptDelayMinimum", "", 45),
    ("hsrp_priority_forwarding_threshold_lower", "hsrpPriorityForwardingThresholdLower", "", 90),
    ("hsrp_priority_forwarding_threshold_upper", "hsrpPriorityForwardingThresholdUpper", "", 110),
]
IDS = [r[0] for r in ROWS]
PAIR = {"hsrp_priority_forwarding_threshold_lower": 90,
        "hsrp_priority_forwarding_threshold_upper": 110}
POSITIVE = dict(HSRP_CTX, hsrp_preempt_delay_minimum=45, **PAIR)


def _have(**extra):
    return build_have(SVI, **dict(POSITIVE, **extra))


def _run(profile, state, have, check_mode=False):
    return run_configs([cfg_for(SVI, profile)], state, have=have, check_mode=check_mode)


@pytest.mark.parametrize("key,nvpair,reset,_applied", ROWS, ids=IDS)
def test_the_row_declares_the_measured_reset_as_a_string(key, nvpair, reset, _applied):
    """The registration, including the Python type. The controller returns these nvPairs as
    strings, so the reset is the empty STRING, not ``None`` and not ``0``."""
    b = resolve_binding(SVI, key)
    assert b is not None, "%s::%s is not registered" % (SVI, key)
    assert b["parent_nvpair"] == nvpair
    assert b["type"] == "integer"
    assert b.get("reset_wire") == reset and isinstance(b.get("reset_wire"), str), (
        "%s::%s reset is %r" % (SVI, key, b.get("reset_wire")))


@pytest.mark.parametrize("key,_nv,reset,applied", ROWS, ids=IDS)
def test_the_engine_withdraws_the_applied_value(key, _nv, reset, applied):
    assert gie_withdrawal_action(SVI, key, str(applied), SUPPORTED, SUPPORTED_PATCH) == (
        GIE_WITHDRAW_RESET, reset)


@pytest.mark.parametrize("key,_nv,reset,_applied", ROWS, ids=IDS)
def test_nothing_is_withdrawn_when_the_value_already_is_the_reset(key, _nv, reset, _applied):
    """NEGATIVE CONTROL: without it an engine that always emitted the reset would pass the case
    above and turn every converged rerun into a write."""
    assert gie_withdrawal_action(SVI, key, reset, SUPPORTED, SUPPORTED_PATCH) == (
        GIE_WITHDRAW_NONE, None)


@pytest.mark.parametrize("key,_nv,reset,applied", ROWS, ids=IDS)
def test_the_reset_is_refused_below_the_minimum_version(key, _nv, reset, applied):
    assert resolve_binding(SVI, key)["min_ndfc_version"] == SUPPORTED
    assert gie_withdrawal_action(SVI, key, str(applied), "12.6.0.266", SUPPORTED_PATCH) != (
        GIE_WITHDRAW_RESET, reset)


def test_the_threshold_pair_is_declared_grouped_only_and_the_delay_is_not():
    assert (SVI, "hsrpPriorityForwardingThresholdLower") in GROUPED_ONLY_NO_PER_ROW_FIXTURE
    assert (SVI, "hsrpPriorityForwardingThresholdUpper") in GROUPED_ONLY_NO_PER_ROW_FIXTURE
    assert (SVI, "hsrpPreemptDelayMinimum") not in GROUPED_ONLY_NO_PER_ROW_FIXTURE


@pytest.mark.parametrize("key", IDS)
def test_the_public_empty_string_stays_refused(key):
    """The reset is emitted by the engine on withdrawal only. An operator cannot type it."""
    result, calls = _run(dict(POSITIVE, **{key: ""}), "merged", have=_have())
    assert result.get("failed"), "the public empty string was accepted for %s" % key
    assert split_calls(calls)["updates"] == [] and split_calls(calls)["deploys"] == []


def test_merged_preserves_all_three():
    """CONTROL: the omission itself withdraws nothing under merged."""
    want = base_for(SVI, **dict(HSRP_CTX, description="hsrp3-merged"))
    result, calls = _run(want, "merged", have=_have())
    assert not result.get("failed"), result.get("msg")
    nv = request_nvpairs(calls)
    assert nv, "the description change produced no request"
    for key, nvpair, _r, applied in ROWS:
        assert nv[0].get(nvpair) == str(applied), (nvpair, nv[0].get(nvpair))


def test_check_mode_plans_the_three_and_transmits_nothing():
    result, calls = _run(base_for(SVI, **HSRP_CTX), "replaced", have=_have(), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    dnv = diff_nvpairs(result)
    assert dnv, "check mode planned nothing"
    for _k, nvpair, reset, _a in ROWS:
        assert dnv[0].get(nvpair) == reset, (nvpair, dnv[0].get(nvpair))
    assert split_calls(calls)["updates"] == [] and split_calls(calls)["deploys"] == []


def test_replaced_withdraws_the_three_in_one_request_and_keeps_the_hosts():
    """The pair travels in the SAME request -- a split is the shape the controller refuses -- and
    the host lines' prerequisites (PREEMPT, HSRP_PRIORITY, the VIP, the group) travel unchanged."""
    result, calls = _run(base_for(SVI, **HSRP_CTX), "replaced", have=_have())
    assert not result.get("failed"), result.get("msg")
    updates = split_calls(calls)["updates"]
    assert len(updates) == 1, "expected exactly one request, got %d" % len(updates)
    nv = request_nvpairs(calls)[0]
    for _k, nvpair, reset, _a in ROWS:
        assert nv.get(nvpair) == reset, (nvpair, nv.get(nvpair))
    assert nv.get("PREEMPT") == "true"
    assert nv.get("HSRP_PRIORITY") == "120"
    assert nv.get("HSRP_VIP") == "192.0.2.254" and nv.get("HSRP_GROUP") == "79"
    assert nv.get("ENABLE_HSRP") == "true"


def test_the_rerun_converges():
    have = _have()
    for _k, nvpair, reset, _a in ROWS:
        have[0]["interfaces"][0]["nvPairs"][nvpair] = reset
    result, calls = _run(base_for(SVI, **HSRP_CTX), "replaced", have=have)
    assert not result.get("failed"), result.get("msg")
    assert split_calls(calls)["updates"] == [], "a converged rerun wrote"
    assert result.get("changed") is False


def test_the_deferred_ipv6_rows_stay_unregistered():
    """``hsrp_vipv6`` / ``hsrp_groupv6`` had no observable positive on the measured controller.
    Registering them here would claim a withdrawal nobody observed."""
    for key in ("hsrp_vipv6", "hsrp_groupv6"):
        b = resolve_binding(SVI, key)
        assert b is not None and b.get("reset_wire") is None, (key, b and b.get("reset_wire"))


def test_the_arithmetic_is_197_plus_three():
    """234 identities, 207 resets, and these three are the only int_vlan HSRP rows with one."""
    con_reset = [r for r in BINDING_TABLE if r.get("reset_wire") is not None]
    assert len(BINDING_TABLE) == 234   # 228 + six int_vpc_dot1q_tunnel rows
    # 200 + six dot1q resets + int_vlan::privateVlanMapping = 207.
    assert len(con_reset) == 197 + 3 + 6 + 1, (
        "the table carries %d resets, expected 207" % len(con_reset))
    hsrp = {r["profile_key"] for r in con_reset
            if r["parent_template"] == SVI and r["profile_key"].startswith("hsrp")}
    assert hsrp == set(IDS), sorted(hsrp)


def test_the_omission_want_really_omits():
    """The absence must be effective: the base SVI profile plus the HSRP context carries none of
    the three, so the cases above measure an omission and not an ordinary apply."""
    want = base_for(SVI, **HSRP_CTX)
    assert not [k for k in IDS if k in want]
