"""Automatic withdrawal of the five QoS and PFC booleans whose explicit "false" was measured on their own parent.

Measured live (NDFC 12.6.0.267), each as an explicit value:
  * int_l3_port_channel (body 81c9392e): qosStatsSuppressed "false" and queuingStats "false" in one request. NDFC
    negated both `service-policy ... no-stats` lines and pushed the plain lines again. ENABLE_PFC "false", sent in a
    separate request, made NDFC negate both `priority-flow-control` lines on the port-channel only; the member's
    `priority-flow-control mode on`, which no member policy carried, was gone afterwards.
  * int_dot1q_tunnel_host (body 33684a76): ENABLE_QOS "false" removed `service-policy type qos input <name>` and kept
    the queuing line; ENABLE_PFC "false" removed both `priority-flow-control` lines.
Each row now declares "false" as its reset_wire, so replaced and a retained interface of overridden send it when the
field is omitted over a stored "true". That automatic reset is new and not tested live.

The policy names keep no reset. QUEUING_POLICY omitted over a stored name is refused, and so is QOS_POLICY while
ENABLE_QOS ends true; while ENABLE_QOS ends false its inert_when gate keeps the stored name. A request that omits one
of them is refused as a whole, before any write, even when it also omits a field that now has a reset. ENABLE_PFC keeps
no reset on the other five parents.

Real main() through helpers/binding_harness: only inventory, transport and sleep are mocked, and every HAVE is the
payload the module itself emits for a public profile. Values are synthetic. Nothing here is live evidence.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import BINDING_TABLE
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_by_nvpair

from .helpers import binding_harness as h
from .helpers import role_reset

PO_QOS = dict(h.QOS, **h.QUEUE)
NAMES = {"qos_policy": "pilot_qos", "queuing_policy": "pilot_queue"}

# (parent, nvPair) -> (public key, the context stored with it and sent again on every request)
ROUTES = {
    (h.PC_L3, "qosStatsSuppressed"): ("disable_qos_stats", dict(PO_QOS)),
    (h.PC_L3, "queuingStats"): ("disable_queuing_stats", dict(PO_QOS)),
    # The measured request shape: no policy attached.
    (h.PC_L3, "ENABLE_PFC"): ("enable_pfc", {}),
    (h.ETH_DOT1Q, "ENABLE_QOS"): ("enable_qos", dict(NAMES)),
    (h.ETH_DOT1Q, "ENABLE_PFC"): ("enable_pfc", dict(NAMES, enable_qos=True)),
}
ITEMS = [(p, n, k, ctx) for (p, n), (k, ctx) in sorted(ROUTES.items())]
IDS = ["%s::%s" % (p, n) for p, n, _k, _c in ITEMS]
STATES = ["replaced", "overridden"]


def _pkw(parent):
    return {"parent": parent} if parent in h.NON_ETH_PARENTS else {}


def _have(parent, key, ctx, **nv):
    have = h.build_have(parent, **dict(ctx, **{key: True}))
    have[0]["interfaces"][0]["nvPairs"].update(nv)
    return have


def _run(parent, profile, state, have, **kw):
    if state == "overridden":
        return h.run_configs([h.cfg_for(parent, profile)], state, have, **kw)
    return h.run(profile, state, have, **dict(_pkw(parent), **kw))


def _one_update(calls):
    s = h.split_calls(calls)
    assert len(s["updates"]) == 1 and len(s["deploys"]) == 1 and s["other"] == [], (
        len(s["updates"]), len(s["deploys"]), [(c["method"], c["path"]) for c in s["other"]])
    nv = h.request_nvpairs(calls)
    assert len(nv) == 1, nv
    return nv[0]


def _reported(result):
    out = {}
    for d in h.diff_nvpairs(result):
        out.update(d)
    return out


def _refused(result, calls, *needles):
    msg = str(result.get("msg", ""))
    assert result.get("failed") is True, "the request was accepted"
    for needle in needles:
        assert needle in msg, msg
    assert "No configuration or deployment request was sent" in msg
    assert h.writes(calls) == []
    return msg


# ------------------------------------------------------------------ registry
@pytest.mark.parametrize("parent,nvpair,key,ctx", ITEMS, ids=IDS)
def test_the_row_declares_the_measured_false_as_a_string(parent, nvpair, key, ctx):
    b = resolve_by_nvpair(parent, nvpair)
    assert (b["profile_key"], b["type"], b["mechanism"]) == (key, "boolean", "passthrough")
    assert b["reset_wire"] == "false" and isinstance(b["reset_wire"], str)
    assert b["default_template"] is False, "the declared default keeps its native type"
    assert "inert_when" not in b


# Every row of these nvPairs on any parent, with its reset (None: no reset) exactly as on the parent commit 3a271ee2,
# except the five rows above. A reset measured on one parent does not move to another.
EXPECTED_RESETS = {
    ("int_dot1q_tunnel_host", "ENABLE_PFC"): "false",
    ("int_l3_port_channel", "ENABLE_PFC"): "false",
    ("int_port_channel_dot1q_tunnel_host", "ENABLE_PFC"): None,
    ("int_routed_host", "ENABLE_PFC"): None,
    ("int_vpc_access_host", "ENABLE_PFC"): None,
    ("int_vpc_dot1q_tunnel", "ENABLE_PFC"): None,
    ("int_vpc_trunk_host", "ENABLE_PFC"): None,
    ("int_dot1q_tunnel_host", "ENABLE_QOS"): "false",
    ("int_vpc_peer_link_po", "ENABLE_QOS"): None,
    ("int_vpc_uplink_access", "ENABLE_QOS"): "false",
    ("int_dot1q_tunnel_host", "QOS_POLICY"): None,
    ("int_vpc_peer_link_po", "QOS_POLICY"): None,
    ("int_vpc_uplink_access", "QOS_POLICY"): "",
    ("int_dot1q_tunnel_host", "QUEUING_POLICY"): None,
    ("int_l3_port_channel", "qosStatsSuppressed"): "false",
    ("int_l3_port_channel", "queuingStats"): "false",
}
for _p in ("int_access_host", "int_port_channel_access_host", "int_port_channel_dot1q_tunnel_host",
           "int_port_channel_trunk_host", "int_routed_host", "int_trunk_host", "int_vpc_access_host",
           "int_vpc_dot1q_tunnel", "int_vpc_pvlan_host", "int_vpc_trunk_host"):
    EXPECTED_RESETS[(_p, "qosStatsSuppressed")] = "false"
    EXPECTED_RESETS[(_p, "queuingStats")] = "false"
EXPECTED_RESETS[("int_vpc_peer_link_po", "qosStatsSuppressed")] = "false"
EXPECTED_RESETS[("int_vpc_uplink_access", "qosStatsSuppressed")] = "false"
EXPECTED_RESETS[("int_port_channel_pvlan_host", "queuingStats")] = "false"


def test_no_other_row_of_these_nvpairs_changed():
    found = {(b["parent_template"], b["parent_nvpair"]): b.get("reset_wire") for b in BINDING_TABLE
             if b["parent_nvpair"] in ("ENABLE_PFC", "ENABLE_QOS", "QOS_POLICY", "QUEUING_POLICY",
                                       "qosStatsSuppressed", "queuingStats")}
    assert len(EXPECTED_RESETS) == 39
    assert found == EXPECTED_RESETS


# ------------------------------------------------------------------ each reset alone
@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("parent,nvpair,key,ctx", ITEMS, ids=IDS)
def test_omission_sends_false_and_carries_every_other_stored_value(parent, nvpair, key, ctx, state):
    have = _have(parent, key, ctx)
    stored = have[0]["interfaces"][0]["nvPairs"]
    assert stored[nvpair] == "true", "positive control: the stored value differs from the reset"
    result, calls = _run(parent, h.want_omitting(parent, key, **ctx), state, have)
    assert not result.get("failed"), result.get("msg")
    sent = _one_update(calls)
    assert sent[nvpair] == "false"
    assert set(stored) <= set(sent), "a stored nvPair was dropped: %s" % sorted(set(stored) - set(sent))
    assert {k: v for k, v in sent.items() if k in stored and k != nvpair} == {
        k: v for k, v in stored.items() if k != nvpair}
    assert _reported(result).get(nvpair) == "false", "the reset is sent but not reported"


@pytest.mark.parametrize("parent,nvpair,key,ctx", ITEMS, ids=IDS)
def test_omission_sends_the_same_body_as_the_measured_explicit_false(parent, nvpair, key, ctx):
    have = _have(parent, key, ctx)
    _r1, omitted = h.run(h.want_omitting(parent, key, **ctx), "replaced", have, **_pkw(parent))
    _r2, explicit = h.run(h.base_for(parent, **dict(ctx, **{key: False})), "replaced", have, **_pkw(parent))
    assert _one_update(omitted) == _one_update(explicit)


@pytest.mark.parametrize("parent,nvpair,key,ctx", ITEMS, ids=IDS)
def test_check_mode_reports_the_reset_and_writes_nothing(parent, nvpair, key, ctx):
    have = _have(parent, key, ctx)
    result, calls = h.run(h.want_omitting(parent, key, **ctx), "replaced", have, check_mode=True, **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []
    assert _reported(result).get(nvpair) == "false"


@pytest.mark.parametrize("parent,nvpair,key,ctx", ITEMS, ids=IDS)
def test_the_readback_of_the_reset_converges_and_a_reapply_writes_true(parent, nvpair, key, ctx):
    have = _have(parent, key, ctx)
    _r, calls = h.run(h.want_omitting(parent, key, **ctx), "replaced", have, **_pkw(parent))
    after = copy.deepcopy(have)
    after[0]["interfaces"][0]["nvPairs"][nvpair] = _one_update(calls)[nvpair]
    for state in STATES:
        result, calls = _run(parent, h.want_omitting(parent, key, **ctx), state, after)
        assert not result.get("failed"), (state, result.get("msg"))
        assert h.writes(calls) == [] and result.get("changed") is False, state
    result, calls = h.run(h.base_for(parent, **dict(ctx, **{key: True})), "replaced", after, **_pkw(parent))
    assert _one_update(calls)[nvpair] == "true"


# ------------------------------------------------------------------ merged keeps the stored value
@pytest.mark.parametrize("parent,nvpair,key,ctx", ITEMS, ids=IDS)
def test_merged_omission_keeps_the_stored_true(parent, nvpair, key, ctx):
    have = _have(parent, key, ctx)
    result, calls = h.run(h.want_omitting(parent, key, **ctx), "merged", have, **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []
    result, calls = h.run(h.want_omitting(parent, key, description="changed", **ctx), "merged", have, **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    sent = _one_update(calls)
    assert (sent[nvpair], sent["DESC"]) == ("true", "changed")


# ------------------------------------------------------------------ readback
@pytest.mark.parametrize("stored", ["false", False, "", None], ids=["wire_false", "native_false", "empty", "absent"])
@pytest.mark.parametrize("parent,nvpair,key,ctx", ITEMS, ids=IDS)
def test_a_neutral_or_missing_readback_writes_nothing(parent, nvpair, key, ctx, stored):
    have = _have(parent, key, ctx)
    if stored is None:
        del have[0]["interfaces"][0]["nvPairs"][nvpair]
    else:
        have[0]["interfaces"][0]["nvPairs"][nvpair] = stored
    result, calls = h.run(h.want_omitting(parent, key, **ctx), "replaced", have, **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("parent,nvpair,key,ctx", ITEMS, ids=IDS)
def test_a_native_true_readback_gets_the_string_reset(parent, nvpair, key, ctx):
    have = _have(parent, key, ctx, **{nvpair: True})
    result, calls = h.run(h.want_omitting(parent, key, **ctx), "replaced", have, **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    assert _one_update(calls)[nvpair] == "false"


@pytest.mark.parametrize("bad", ["maybe", "TRUE", "True", "yes", "1", " false"])
@pytest.mark.parametrize("parent,nvpair,key,ctx", ITEMS, ids=IDS)
def test_a_malformed_readback_fails_closed_naming_the_key(parent, nvpair, key, ctx, bad):
    have = _have(parent, key, ctx, **{nvpair: bad})
    for state in ("replaced", "merged"):
        result, calls = h.run(h.want_omitting(parent, key, description="changed", **ctx), state, have,
                              **_pkw(parent))
        assert result.get("failed") is True, state
        assert "'%s'" % key in result["msg"] and parent in result["msg"], result["msg"]
        assert h.writes(calls) == [], state


# ------------------------------------------------------------------ grouped resets
@pytest.mark.parametrize("state", STATES)
def test_both_statistics_omitted_reset_together_with_the_policies_attached(state):
    """The measured request shape: both options false in one update, the policies attached."""
    have = h.build_have(h.PC_L3, disable_qos_stats=True, disable_queuing_stats=True, **PO_QOS)
    result, calls = _run(h.PC_L3, h.base_for(h.PC_L3, **PO_QOS), state, have)
    assert not result.get("failed"), result.get("msg")
    sent = _one_update(calls)
    assert {k: sent[k] for k in ("qosStatsSuppressed", "queuingStats", "QOS_POLICY", "QUEUING_POLICY")} == {
        "qosStatsSuppressed": "false", "queuingStats": "false", "QOS_POLICY": "pilot_qos",
        "QUEUING_POLICY": "pilot_queue"}
    assert sent["ENABLE_QOS"] is True, "the native field keeps its JSON boolean"
    assert "ENABLE_PFC" not in sent, "an explicit-only field that is not stored is not sent"


@pytest.mark.parametrize("state", STATES)
def test_statistics_and_pfc_omitted_reset_together_on_the_routed_port_channel(state):
    """Both statistics options and PFC stored true with the policies attached, all three omitted: one update with the
    three resets, the policy names and the native QoS boolean carried, equal to the explicit-false body."""
    have = h.build_have(h.PC_L3, enable_pfc=True, disable_qos_stats=True, disable_queuing_stats=True, **PO_QOS)
    stored = have[0]["interfaces"][0]["nvPairs"]
    result, calls = _run(h.PC_L3, h.base_for(h.PC_L3, **PO_QOS), state, have)
    assert not result.get("failed"), result.get("msg")
    sent = _one_update(calls)
    reset = ("ENABLE_PFC", "qosStatsSuppressed", "queuingStats")
    assert {k: sent[k] for k in reset} == dict.fromkeys(reset, "false")
    assert {k: v for k, v in sent.items() if k not in reset} == {k: v for k, v in stored.items() if k not in reset}
    assert sent["ENABLE_QOS"] is True and (sent["QOS_POLICY"], sent["QUEUING_POLICY"]) == ("pilot_qos", "pilot_queue")
    assert {k: _reported(result).get(k) for k in reset} == dict.fromkeys(reset, "false")
    explicit = h.base_for(h.PC_L3, enable_pfc=False, disable_qos_stats=False, disable_queuing_stats=False, **PO_QOS)
    _r, calls = h.run(explicit, "replaced", have, parent=h.PC_L3)
    assert sent == _one_update(calls)


@pytest.mark.parametrize("state", STATES)
def test_qos_and_pfc_omitted_reset_together_on_the_dot1q_tunnel_port(state):
    have = h.build_have(h.ETH_DOT1Q, enable_qos=True, enable_pfc=True, **NAMES)
    result, calls = _run(h.ETH_DOT1Q, h.base_for(h.ETH_DOT1Q, **NAMES), state, have)
    assert not result.get("failed"), result.get("msg")
    sent = _one_update(calls)
    assert {k: sent[k] for k in ("ENABLE_QOS", "ENABLE_PFC", "QOS_POLICY", "QUEUING_POLICY")} == {
        "ENABLE_QOS": "false", "ENABLE_PFC": "false", "QOS_POLICY": "pilot_qos", "QUEUING_POLICY": "pilot_queue"}


def test_one_reset_and_an_explicit_change_share_one_update():
    have = h.build_have(h.PC_L3, disable_qos_stats=True, disable_queuing_stats=True, **PO_QOS)
    profile = h.base_for(h.PC_L3, disable_queuing_stats=True, description="changed", **PO_QOS)
    result, calls = h.run(profile, "replaced", have, parent=h.PC_L3)
    assert not result.get("failed"), result.get("msg")
    sent = _one_update(calls)
    assert (sent["qosStatsSuppressed"], sent["queuingStats"], sent["DESC"]) == ("false", "true", "changed")


# ------------------------------------------------------------------ the policy names keep their contract
def test_omitted_qos_with_both_names_given_is_the_measured_disable():
    """The stored names are given again explicitly; the body is the measured merged disable."""
    have = h.build_have(h.ETH_DOT1Q, enable_qos=True, **NAMES)
    result, calls = h.run(h.base_for(h.ETH_DOT1Q, **NAMES), "replaced", have)
    assert not result.get("failed"), result.get("msg")
    _r, merged = h.run(h.base_for(h.ETH_DOT1Q, enable_qos=False), "merged", have)
    assert _one_update(calls) == _one_update(merged)


def test_omitted_qos_and_qos_policy_keep_the_stored_name_by_its_gate():
    """No reset is established for QOS_POLICY. Its gate ends false, so the stored name stays, as for an explicit
    disable that omits it; it is not cleared."""
    have = h.build_have(h.ETH_DOT1Q, enable_qos=True, **NAMES)
    result, calls = h.run(h.base_for(h.ETH_DOT1Q, queuing_policy="pilot_queue"), "replaced", have)
    assert not result.get("failed"), result.get("msg")
    sent = _one_update(calls)
    assert (sent["ENABLE_QOS"], sent["QOS_POLICY"], sent["QUEUING_POLICY"]) == ("false", "pilot_qos", "pilot_queue")
    assert "QOS_POLICY" not in _reported(result), "the kept name is reported as a change"
    _r, explicit = h.run(h.base_for(h.ETH_DOT1Q, enable_qos=False, queuing_policy="pilot_queue"), "replaced", have)
    assert sent == _one_update(explicit)


def test_omitted_qos_policy_while_qos_stays_on_is_still_refused():
    have = h.build_have(h.ETH_DOT1Q, enable_qos=True, **NAMES)
    result, calls = h.run(h.base_for(h.ETH_DOT1Q, enable_qos=True, queuing_policy="pilot_queue"), "replaced", have)
    msg = _refused(result, calls, "qos_policy on %s" % h.ETH_DOT1Q)
    assert "pilot_qos" not in msg


@pytest.mark.parametrize("omit", [("enable_qos",), ("enable_pfc",), ("enable_qos", "enable_pfc"),
                                  ("enable_qos", "qos_policy", "enable_pfc")], ids="+".join)
@pytest.mark.parametrize("state", STATES)
def test_an_omitted_queuing_policy_refuses_the_whole_request(omit, state):
    """An omitted stored name blocks the request, even when the other omitted fields have a reset. Nothing is sent."""
    have = h.build_have(h.ETH_DOT1Q, enable_qos=True, enable_pfc=True, **NAMES)
    profile = {k: v for k, v in dict(h.base_for(h.ETH_DOT1Q), enable_qos=True, enable_pfc=True,
                                     qos_policy="pilot_qos").items() if k not in omit}
    result, calls = _run(h.ETH_DOT1Q, profile, state, have)
    msg = _refused(result, calls, "queuing_policy on %s" % h.ETH_DOT1Q)
    assert "enable_qos on" not in msg and "enable_pfc on" not in msg, "a field with a reset was refused"
    assert "pilot_queue" not in msg


def test_explicit_empty_names_are_sent_as_requested():
    have = h.build_have(h.ETH_DOT1Q, enable_qos=True, **NAMES)
    for profile, expected in (
            (h.base_for(h.ETH_DOT1Q, enable_qos=True, qos_policy="pilot_qos", queuing_policy=""),
             ("true", "pilot_qos", "")),
            (h.base_for(h.ETH_DOT1Q, enable_qos=False, qos_policy="", queuing_policy="pilot_queue"),
             ("false", "", "pilot_queue"))):
        result, calls = h.run(profile, "replaced", have)
        assert not result.get("failed"), result.get("msg")
        sent = _one_update(calls)
        assert (sent["ENABLE_QOS"], sent["QOS_POLICY"], sent["QUEUING_POLICY"]) == expected


# ------------------------------------------------------------------ wire types
def test_the_registered_keys_leave_as_strings_and_the_native_qos_as_a_boolean():
    have = h.build_have(h.PC_L3, enable_pfc=True, disable_qos_stats=True, disable_queuing_stats=True, **PO_QOS)
    _r, calls = h.run(h.base_for(h.PC_L3, **PO_QOS), "replaced", have, parent=h.PC_L3)
    sent = _one_update(calls)
    assert all(isinstance(sent[k], str) for k in ("ENABLE_PFC", "qosStatsSuppressed", "queuingStats"))
    assert isinstance(sent["ENABLE_QOS"], bool)
    have = h.build_have(h.ETH_DOT1Q, enable_qos=True, enable_pfc=True, **NAMES)
    _r, calls = h.run(h.base_for(h.ETH_DOT1Q, **NAMES), "replaced", have)
    sent = _one_update(calls)
    assert isinstance(sent["ENABLE_QOS"], str) and isinstance(sent["ENABLE_PFC"], str)


# ------------------------------------------------------------------ unchanged parents and transitions
@pytest.mark.parametrize("state", STATES)
def test_routed_port_channel_pfc_omission_sends_the_measured_routing_values(state):
    """The QoS and PFC values of the measured explicit-false body: PFC as a string, the native QoS keys at their
    defaults with ENABLE_QOS a JSON boolean, the statistics options carried as the controller stores them."""
    have = _have(h.PC_L3, "enable_pfc", {}, qosStatsSuppressed="false", queuingStats="false")
    result, calls = _run(h.PC_L3, h.want_omitting(h.PC_L3, "enable_pfc"), state, have)
    assert not result.get("failed"), result.get("msg")
    sent = _one_update(calls)
    assert {k: sent[k] for k in ("ENABLE_PFC", "ENABLE_QOS", "QOS_POLICY", "QUEUING_POLICY", "qosStatsSuppressed",
                                 "queuingStats")} == {
        "ENABLE_PFC": "false", "ENABLE_QOS": False, "QOS_POLICY": "", "QUEUING_POLICY": "",
        "qosStatsSuppressed": "false", "queuingStats": "false"}


@pytest.mark.parametrize("state", STATES)
def test_routed_ethernet_pfc_omission_is_still_refused_with_the_statistics(state):
    """PFC on the routed Ethernet has no reset, so its omission blocks the request, the statistics resets of that
    parent included."""
    have = h.build_have(h.ROUTED, enable_pfc=True, disable_qos_stats=True, disable_queuing_stats=True, **PO_QOS)
    result, calls = _run(h.ROUTED, h.base_for(h.ROUTED, **PO_QOS), state, have)
    msg = _refused(result, calls, "enable_pfc on %s" % h.ROUTED)
    assert "disable_qos_stats" not in msg and "disable_queuing_stats" not in msg


@pytest.mark.parametrize("parent", [h.ROUTED, h.PC_DOT1Q, h.VPC_ACCESS, h.VPC_TRUNK, h.VPC_DOT1Q])
def test_pfc_omission_on_the_other_registered_parents_is_still_refused(parent):
    have = h.build_have(parent, enable_pfc=True)
    result, calls = h.run_configs([h.cfg_for(parent, h.want_omitting(parent, "enable_pfc"))], "replaced", have)
    _refused(result, calls, "enable_pfc on %s" % parent)


def test_deleting_a_dot1q_tunnel_port_with_qos_or_pfc_on_names_the_clear_first():
    """deleted changes the policy to the trunk role default, which has no registered row for these nvPairs, so the
    stored values block the reset. The current policy now has a verified reset, and the message says to clear the
    field there first."""
    have = h.build_have(h.ETH_DOT1Q, enable_qos=True, enable_pfc=True, **NAMES)
    result, calls = role_reset.run("deleted", have, "leaf")
    msg = str(result.get("msg", ""))
    assert result.get("failed") is True and h.writes(calls) == []
    assert "enable_qos (ENABLE_QOS)" in msg and "enable_pfc (ENABLE_PFC)" in msg, msg
    assert "Its current policy has a verified reset: clear the field on that policy first" in msg, msg


def test_deleting_a_dot1q_tunnel_port_after_the_clear_resets_it_to_the_role_default():
    have = h.build_have(h.ETH_DOT1Q, enable_qos=True, enable_pfc=True, **NAMES)
    _r, calls = h.run(h.base_for(h.ETH_DOT1Q, qos_policy="", queuing_policy=""), "replaced", have)
    have[0]["interfaces"][0]["nvPairs"].update(_one_update(calls))
    result, calls = role_reset.run("deleted", have, "leaf")
    assert not result.get("failed"), result.get("msg")
    policies = role_reset.reset_policies(calls)
    assert [p["policy"] for p in policies] == [h.TRUNK], policies
