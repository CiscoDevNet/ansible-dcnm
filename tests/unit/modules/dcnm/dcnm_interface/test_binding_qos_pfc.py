"""Priority flow control, Ethernet dot1q-tunnel QoS and routed port-channel policy statistics (registry lot rp4).

ENABLE_PFC is registered on the seven parents that declare it without a native field: routed Ethernet, Ethernet
dot1q-tunnel, routed port-channel, dot1q-tunnel port-channel and the three vPC host parents. The Ethernet and
port-channel trunk and access profiles keep their native enable_pfc. The Ethernet dot1q-tunnel parent also takes the
native QoS keys of the other Ethernet modes, and the routed port-channel the routed Ethernet statistics options.
None of the twelve rows declares a reset, so under replaced and overridden an omitted value that differs from the
default is refused before any write (per route in test_binding_rp_omission.py). A merged QoS disable sends
ENABLE_QOS false and keeps the stored policy name, which the template ignores while QoS is off.

Real main() through helpers/binding_harness: only inventory, transport and sleep are mocked, and every HAVE is the
payload the module itself emits for a public profile. Values are synthetic. Nothing here is live evidence.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding

from .helpers import binding_harness as h

PFC_PARENTS = (h.ROUTED, h.ETH_DOT1Q, h.PC_L3, h.PC_DOT1Q, h.VPC_TRUNK, h.VPC_ACCESS, h.VPC_DOT1Q)
NATIVE_PFC_PARENTS = (h.ACCESS, h.TRUNK, h.PC_ACCESS, h.PC_TRUNK)
QOS_NV = ("ENABLE_QOS", "QOS_POLICY", "QUEUING_POLICY")
DOT1Q_QOS = {"enable_qos": True, "qos_policy": "pilot_qos", "queuing_policy": "pilot_queue"}
DOT1Q_QOS_WIRE = {"ENABLE_QOS": "true", "QOS_POLICY": "pilot_qos", "QUEUING_POLICY": "pilot_queue"}
DOT1Q_QOS_DISABLED = {**DOT1Q_QOS, "enable_qos": False}


def _emitted(calls):
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    return found


def _nv(calls, parent):
    found = [p for p in _emitted(calls) if p["policy"] == parent]
    assert len(found) == 1 and len(found[0]["interfaces"]) == 1, [p["policy"] for p in _emitted(calls)]
    return found[0]["interfaces"][0]["nvPairs"]


def _run(parent, profile, state="merged", have=None, **kw):
    return h.run_configs([h.cfg_for(parent, profile)], state, have or [], **kw)


def _have(parent, **extra):
    return h.build_have(parent, **extra)


def _base(parent, **extra):
    """base_for without the registered OSPF keys of the routed base, so a refusal can only come from the key under test."""
    prof = h.base_for(parent, **extra)
    if parent == h.ROUTED:
        prof.pop("enable_ospf", None)
        prof.pop("ospf_area_id", None)
    return prof


def _unrelated_change(parent):
    return {"peer1_description": "changed"} if parent in h.VPC_PARENTS else {"description": "changed"}


def _sel(nv, keys):
    return {k: nv.get(k) for k in keys if k in nv}


# ------------------------------------------------------------------ the rows
@pytest.mark.parametrize("parent", PFC_PARENTS)
def test_enable_pfc_is_one_contract_on_every_registered_parent(parent):
    b = resolve_binding(parent, "enable_pfc")
    assert b is not None, parent
    assert (b["parent_nvpair"], b["type"], b["default_template"], b["mechanism"]) == (
        "ENABLE_PFC", "boolean", False, "passthrough")
    assert "inert_when" not in b and "reset_wire" not in b


@pytest.mark.parametrize("parent", NATIVE_PFC_PARENTS)
def test_the_native_pfc_parents_have_no_row(parent):
    assert resolve_binding(parent, "enable_pfc") is None
    assert {"enable_pfc", "queuing_policy"} <= gie_engine.GIE_NATIVE_ELSEWHERE_KEYS


def test_the_dot1q_tunnel_qos_rows_use_the_native_keys():
    eq, qp, qu = (resolve_binding(h.ETH_DOT1Q, k) for k in ("enable_qos", "qos_policy", "queuing_policy"))
    assert (eq["parent_nvpair"], eq["type"], eq["default_template"]) == ("ENABLE_QOS", "boolean", False)
    assert (qp["parent_nvpair"], qp["type"]) == ("QOS_POLICY", "string")
    assert qp["string_compare"] == "unverified"
    assert qp["inert_when"] == {"nvpair": "ENABLE_QOS", "value": "false"} and "max_length" not in qp
    assert (qu["parent_nvpair"], qu["string_compare"]) == ("QUEUING_POLICY", "unverified")
    assert "inert_when" not in qu
    assert not any("reset_wire" in b for b in (eq, qp, qu))


@pytest.mark.parametrize("key", ["disable_qos_stats", "disable_queuing_stats"])
def test_the_routed_port_channel_statistics_reuse_the_routed_ethernet_contract(key):
    b, routed = resolve_binding(h.PC_L3, key), resolve_binding(h.ROUTED, key)
    for field in ("parent_nvpair", "type", "default_template", "min_ndfc_version", "no_log", "inert_when"):
        assert b.get(field) == routed.get(field), field
    # The routed reset stays the evidence for a later measurement on this parent; it is not used here.
    assert "reset_wire" not in b and routed.get("reset_wire") == "false"


# ------------------------------------------------------------------ priority flow control
@pytest.mark.parametrize("value,wire", [(True, "true"), (False, "false")], ids=["true", "false"])
@pytest.mark.parametrize("parent", PFC_PARENTS)
def test_enable_pfc_reaches_the_parent_nvpair(parent, value, wire):
    result, calls = _run(parent, _base(parent, enable_pfc=value))
    assert not result.get("failed"), result.get("msg")
    assert _nv(calls, parent)["ENABLE_PFC"] == wire


@pytest.mark.parametrize("parent", PFC_PARENTS)
def test_enable_pfc_omitted_on_create_sends_nothing(parent):
    result, calls = _run(parent, _base(parent))
    assert not result.get("failed"), result.get("msg")
    assert "ENABLE_PFC" not in _nv(calls, parent)


@pytest.mark.parametrize("parent", PFC_PARENTS)
def test_merged_omission_keeps_a_stored_pfc_and_a_repeat_writes_nothing(parent):
    have = _have(parent, enable_pfc=True)
    result, calls = _run(parent, h.base_for(parent, **_unrelated_change(parent)), "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert _nv(calls, parent)["ENABLE_PFC"] == "true"
    result, calls = _run(parent, h.base_for(parent, enable_pfc=True), "replaced", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("parent", NATIVE_PFC_PARENTS)
def test_the_native_pfc_field_is_unchanged(parent):
    """Native default false, sent on every request, as before the rows were registered."""
    for profile, expected in ((_base(parent, enable_pfc=True), True), (h.base_for(parent), False)):
        result, calls = _run(parent, profile)
        assert not result.get("failed"), result.get("msg")
        assert _nv(calls, parent)["ENABLE_PFC"] in (expected, str(expected).lower())


def test_enable_pfc_keeps_the_legacy_discard_on_a_subinterface():
    result, calls = _run(h.SUBIF, h.base_for(h.SUBIF, enable_pfc=True))
    assert not result.get("failed"), result.get("msg")
    assert "ENABLE_PFC" not in _nv(calls, h.SUBIF)


@pytest.mark.parametrize("patch_version", [None, h.UNSUPPORTED_PATCH], ids=["no_patch_version", "unsupported_patch"])
@pytest.mark.parametrize("parent", PFC_PARENTS)
def test_enable_pfc_needs_an_approved_patch_version(parent, patch_version):
    result, calls = _run(parent, _base(parent, enable_pfc=True), patch_version=patch_version)
    assert result.get("failed") and "enable_pfc" in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("parent", PFC_PARENTS)
def test_enable_pfc_must_be_a_boolean(parent):
    result, calls = _run(parent, _base(parent, enable_pfc="maybe"))
    assert result.get("failed") and "enable_pfc" in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


# ------------------------------------------------------------------ Ethernet dot1q-tunnel QoS
def test_dot1q_tunnel_create_sends_the_qos_and_queuing_policies():
    result, calls = _run(h.ETH_DOT1Q, h.base_for(h.ETH_DOT1Q, **DOT1Q_QOS))
    assert not result.get("failed"), result.get("msg")
    nv = _nv(calls, h.ETH_DOT1Q)
    assert _sel(nv, QOS_NV) == DOT1Q_QOS_WIRE
    assert (nv["BPDUGUARD_ENABLED"], nv["INTF_NAME"]) == ("true", h.IF_A), "the native dot1q nvPairs are untouched"


def test_dot1q_tunnel_qos_without_a_policy_is_transported():
    """The template falls back to QOS_CLASSIFICATION only when the fabric enables AI/ML QoS; otherwise it renders no
    QoS line. The module sends the request as the native Ethernet modes do."""
    result, calls = _run(h.ETH_DOT1Q, h.base_for(h.ETH_DOT1Q, enable_qos=True))
    assert not result.get("failed"), result.get("msg")
    assert _sel(_nv(calls, h.ETH_DOT1Q), QOS_NV) == {"ENABLE_QOS": "true"}


def test_dot1q_tunnel_merged_qos_disable_keeps_the_inert_policy():
    """No reset is established for QOS_POLICY on this parent, so the disable sends ENABLE_QOS false and the stored name
    stays: the template neither validates nor renders it while QoS is off. Whether the controller removes the
    service-policy line on deploy is not measured."""
    have = _have(h.ETH_DOT1Q, **DOT1Q_QOS)
    result, calls = _run(h.ETH_DOT1Q, h.base_for(h.ETH_DOT1Q, enable_qos=False), "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _nv(calls, h.ETH_DOT1Q)
    assert {k: v for k, v in _sel(nv, QOS_NV).items() if k != "QOS_POLICY"} == {
        "ENABLE_QOS": "false", "QUEUING_POLICY": "pilot_queue"}
    assert nv.get("QOS_POLICY", "pilot_qos") == "pilot_qos", nv.get("QOS_POLICY")
    stored = _have(h.ETH_DOT1Q, **DOT1Q_QOS_DISABLED)
    for state in ("merged", "replaced"):
        result, calls = _run(h.ETH_DOT1Q, h.base_for(h.ETH_DOT1Q, enable_qos=False, queuing_policy="pilot_queue"), state,
                             stored)
        assert not result.get("failed"), (state, result.get("msg"))
        assert h.writes(calls) == [], "the inert policy is not a withdrawal target"


def test_dot1q_tunnel_explicit_qos_clear_is_sent_as_requested():
    have = _have(h.ETH_DOT1Q, **DOT1Q_QOS)
    profile = h.base_for(h.ETH_DOT1Q, enable_qos=False, qos_policy="", queuing_policy="")
    for state in ("merged", "replaced"):
        result, calls = _run(h.ETH_DOT1Q, profile, state, have)
        assert not result.get("failed"), (state, result.get("msg"))
        assert _sel(_nv(calls, h.ETH_DOT1Q), QOS_NV) == {"ENABLE_QOS": "false", "QOS_POLICY": "", "QUEUING_POLICY": ""}


def test_dot1q_tunnel_merged_queuing_clear_differs_from_omission():
    have = _have(h.ETH_DOT1Q, **DOT1Q_QOS)
    result, calls = _run(h.ETH_DOT1Q, h.base_for(h.ETH_DOT1Q, queuing_policy=""), "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert _sel(_nv(calls, h.ETH_DOT1Q), QOS_NV) == {**DOT1Q_QOS_WIRE, "QUEUING_POLICY": ""}
    result, calls = _run(h.ETH_DOT1Q, h.base_for(h.ETH_DOT1Q), "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_dot1q_tunnel_policy_change_is_sent_and_a_repeat_writes_nothing(state):
    have = _have(h.ETH_DOT1Q, **DOT1Q_QOS)
    result, calls = _run(h.ETH_DOT1Q, h.base_for(h.ETH_DOT1Q, **{**DOT1Q_QOS, "qos_policy": "pilot_qos_b"}), state, have)
    assert not result.get("failed"), result.get("msg")
    assert _nv(calls, h.ETH_DOT1Q)["QOS_POLICY"] == "pilot_qos_b"
    result, calls = _run(h.ETH_DOT1Q, h.base_for(h.ETH_DOT1Q, **DOT1Q_QOS), state, have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_dot1q_tunnel_replaced_without_qos_is_refused_before_any_write():
    have = _have(h.ETH_DOT1Q, **DOT1Q_QOS)
    result, calls = _run(h.ETH_DOT1Q, h.base_for(h.ETH_DOT1Q), "replaced", have)
    assert result.get("failed") is True
    for key in ("enable_qos", "qos_policy", "queuing_policy"):
        assert "%s on %s" % (key, h.ETH_DOT1Q) in result["msg"], result["msg"]
    assert "pilot_q" not in result["msg"]
    assert h.writes(calls) == []


@pytest.mark.parametrize("patch_version", [None, h.UNSUPPORTED_PATCH], ids=["no_patch_version", "unsupported_patch"])
@pytest.mark.parametrize("key,value", [("enable_qos", True), ("qos_policy", "pilot_qos"), ("queuing_policy", "pilot_queue")])
def test_dot1q_tunnel_qos_needs_an_approved_patch_version(key, value, patch_version):
    result, calls = _run(h.ETH_DOT1Q, h.base_for(h.ETH_DOT1Q, **{key: value}), patch_version=patch_version)
    assert result.get("failed") and key in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


def test_dot1q_tunnel_check_mode_refuses_the_same_withdrawal():
    have = _have(h.ETH_DOT1Q, **DOT1Q_QOS)
    result, calls = _run(h.ETH_DOT1Q, h.base_for(h.ETH_DOT1Q), "replaced", have, check_mode=True)
    assert result.get("failed") is True
    assert h.writes(calls) == []


@pytest.mark.parametrize("parent", [h.ACCESS, h.TRUNK, h.PC_DOT1Q, h.VPC_DOT1Q])
def test_the_native_qos_keys_are_unchanged_elsewhere(parent):
    result, calls = _run(parent, h.base_for(parent, **DOT1Q_QOS))
    assert not result.get("failed"), result.get("msg")
    nv = _nv(calls, parent)
    assert [str(nv[k]).lower() for k in QOS_NV] == ["true", "pilot_qos", "pilot_queue"]


# ------------------------------------------------------------------ routed port-channel policy statistics
def test_routed_port_channel_statistics_append_to_their_own_policies():
    profile = h.base_for(h.PC_L3, **h.QOS, **h.QUEUE, disable_qos_stats=True, disable_queuing_stats=True)
    result, calls = _run(h.PC_L3, profile)
    assert not result.get("failed"), result.get("msg")
    nv = _nv(calls, h.PC_L3)
    assert _sel(nv, ("ENABLE_QOS", "QOS_POLICY", "QUEUING_POLICY", "qosStatsSuppressed", "queuingStats")) == {
        "ENABLE_QOS": True, "QOS_POLICY": "pilot_qos", "QUEUING_POLICY": "pilot_queue", "qosStatsSuppressed": "true",
        "queuingStats": "true"}


def test_routed_port_channel_statistics_replaced_omission_is_refused_and_the_explicit_default_is_sent():
    have = _have(h.PC_L3, **h.QOS, **h.QUEUE, disable_qos_stats=True, disable_queuing_stats=True)
    result, calls = _run(h.PC_L3, h.base_for(h.PC_L3, **h.QOS, **h.QUEUE), "replaced", have)
    assert result.get("failed") is True
    assert all("%s on %s" % (k, h.PC_L3) in result["msg"] for k in ("disable_qos_stats", "disable_queuing_stats"))
    assert h.writes(calls) == []
    profile = h.base_for(h.PC_L3, **h.QOS, **h.QUEUE, disable_qos_stats=False, disable_queuing_stats=False)
    result, calls = _run(h.PC_L3, profile, "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = _nv(calls, h.PC_L3)
    assert (nv["qosStatsSuppressed"], nv["queuingStats"], nv["QOS_POLICY"], nv["QUEUING_POLICY"]) == (
        "false", "false", "pilot_qos", "pilot_queue")


@pytest.mark.parametrize("key", ["disable_qos_stats", "disable_queuing_stats"])
def test_routed_port_channel_statistics_need_an_approved_patch_version(key):
    result, calls = _run(h.PC_L3, h.base_for(h.PC_L3, **h.QOS, **h.QUEUE, **{key: True}), patch_version=None)
    assert result.get("failed") and key in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []
