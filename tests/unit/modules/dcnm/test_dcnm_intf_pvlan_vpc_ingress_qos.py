"""Ingress QoS (ENABLE_QOS, QOS_POLICY, qosStatsSuppressed) of the vPC PVLAN parent int_vpc_pvlan_host.

NOT LIVE TESTED. Real main() through the EXISTING vPC harness; previews are SYNTHETIC, written by hand from the CORRECTED templates
(the parent's QoS block with qosPolicy/queuingPolicy locals as in the reference int_vpc_trunk_host and every Engineering set; the
child's `service-policy type qos input <p>[ no-stats]` as in the regular templates). The INSTALLED revision on the test ND drops the
values parent -> children (MEASURED for QUEUING_POLICY, live S1) and its child renders a `type ENABLE_QOS` literal: the harness
reproduces that loss with `defective_qos_template`, and those cases must fail WITHOUT a deploy.

The REFERENCE section drives the regular vPC parents (trunk, dot1q) through the same main() and reads the request the module sends.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_ENABLED_PATCH_VERSIONS

from . import gie_withdrawal_harness as G
from . import test_dcnm_intf_pvlan_vpc_harness as V

SMU = sorted(GIE_ENABLED_PATCH_VERSIONS)[0]
QOS_KEYS = ("ENABLE_QOS", "QOS_POLICY", "qosStatsSuppressed")


def _norm(nv):
    return {k: str(nv.get(k)).lower() if k != "QOS_POLICY" else (nv.get(k) or "") for k in QOS_KEYS if k in nv}


# ====================================================================================== reference: the module's regular vPC rule
def _base_without_qos(parent):
    # the harness base profiles carry enable_qos/qos_policy; an omission case must not send them
    return {k: v for k, v in G.base_for(parent).items() if k not in ("enable_qos", "qos_policy")}


def _regular(parent, state, have_extra, want_extra):
    have = G.build_have(parent, **have_extra) if have_extra is not None else None
    want = dict(_base_without_qos(parent), **want_extra)
    for key in [k for k, v in want.items() if v is None]:
        want.pop(key)
    result, calls = G.run(want, state, have=have, parent=parent)
    assert not result.get("failed"), result.get("msg")
    found = []
    G._collect_policies([c["payload"] for c in G.writes(calls)], found)
    return bool(G.split_calls(calls)["updates"]), (found[0]["interfaces"][0]["nvPairs"] if found else None)


@pytest.mark.parametrize("parent", [G.VPC_TRUNK, G.VPC_DOT1Q])
def test_reference_regular_vpc_ingress_qos_rule(parent):
    """The regular rule IQ1 reuses (the request the module itself sends)."""
    on = dict(enable_qos=True, qos_policy="Q1", disable_qos_stats=True)
    written, nv = _regular(parent, "merged", None, on)
    assert written and _norm(nv) == {"ENABLE_QOS": "true", "QOS_POLICY": "Q1", "qosStatsSuppressed": "true"}
    written, _nv = _regular(parent, "merged", on, {})                       # merged, omitted: nothing
    assert not written
    written, nv = _regular(parent, "merged", on, dict(enable_qos=True, qos_policy="Q2"))     # policy change, QoS restated
    assert written and nv["QOS_POLICY"] == "Q2"
    # DOCUMENTED DIVERGENCE: a merged policy change that does not restate enable_qos sends QOS_POLICY '' on the regular parent (the
    # payload builder reads the spec default enable_qos=False), i.e. the policy is dropped silently. The PVLAN rule keeps ENABLE_QOS
    # from HAVE and applies the new policy (test_vpc_pvlan_rule_matches_the_regular_one, third row).
    written, nv = _regular(parent, "merged", on, dict(qos_policy="Q2"))
    assert written and nv["QOS_POLICY"] == ""
    written, nv = _regular(parent, "merged", on, dict(enable_qos=False, qos_policy=None))   # merged disable: an omitted policy is kept
    assert written and _norm(nv)["ENABLE_QOS"] == "false" and nv["QOS_POLICY"] == "Q1"
    result, calls = G.run(_base_without_qos(parent), "replaced", have=G.build_have(parent, **on), parent=parent)  # replaced, omitted: reset
    found = []
    G._collect_policies([c["payload"] for c in G.writes(calls)], found)
    nv = found[0]["interfaces"][0]["nvPairs"]
    assert _norm(nv) == {"ENABLE_QOS": "false", "QOS_POLICY": "", "qosStatsSuppressed": "false"}


# ====================================================================================== PVLAN rule (helper)
def _raw(**extra):
    raw = {"pvlan_mode": "host", "peer1_members": [V.M1], "peer2_members": [V.M2], "peer1_pcid": 10, "peer2_pcid": 10,
           "pvlan_association": [{"primary_vlan": V.PRIMARY, "secondary_vlan": V.SECONDARY}]}
    raw.update(extra)
    return raw


def _legs(raw):
    return P.vpc_pair_view(raw, V.PAIR, [V.SN1, V.SN2])


def _have(**extra):
    raw = _raw(**extra)
    nv = P.vpc_host_nvpairs(raw, "vPC10", _legs(raw))
    nv.update(P.registry_companions("replaced", P.VPC_HOST_POLICY, raw, None, "12.6.0.267", SMU)[0])
    return nv


def _reconcile(state, have, patch=SMU, **want):
    raw = _raw(**want)
    return P.reconcile_vpc(state, raw, "vPC10", _legs(raw), P.VPC_HOST_POLICY, have, "12.6.0.267", patch)


ON = dict(enable_qos=True, qos_policy="Q1", disable_qos_stats=True)


@pytest.mark.parametrize(
    "state, have, want, written, expected",
    [
        ("merged", {}, ON, True, {"ENABLE_QOS": "true", "QOS_POLICY": "Q1", "qosStatsSuppressed": "true"}),
        ("merged", ON, {}, False, {"ENABLE_QOS": "true", "QOS_POLICY": "Q1", "qosStatsSuppressed": "true"}),
        ("merged", ON, dict(qos_policy="Q2"), True, {"ENABLE_QOS": "true", "QOS_POLICY": "Q2", "qosStatsSuppressed": "true"}),
        ("merged", dict(enable_qos=True, qos_policy="Q1"), dict(enable_qos=False), True,
         {"ENABLE_QOS": "false", "QOS_POLICY": "Q1", "qosStatsSuppressed": "false"}),   # residual kept, as the regular merged
        ("replaced", dict(enable_qos=True, qos_policy="Q1"), dict(enable_qos=False), True,
         {"ENABLE_QOS": "false", "QOS_POLICY": "", "qosStatsSuppressed": "false"}),    # full payload clears it, as the regular
        ("replaced", ON, {}, True, {"ENABLE_QOS": "false", "QOS_POLICY": "", "qosStatsSuppressed": "false"}),
        ("replaced", ON, ON, False, {"ENABLE_QOS": "true", "QOS_POLICY": "Q1", "qosStatsSuppressed": "true"}),
        ("merged", dict(enable_qos=True, qos_policy="Q1"), dict(disable_qos_stats=False), False,
         {"ENABLE_QOS": "true", "QOS_POLICY": "Q1", "qosStatsSuppressed": "false"}),
    ],
)
def test_vpc_pvlan_rule_matches_the_regular_one(state, have, want, written, expected):
    out = _reconcile(state, _have(**have), **want)
    assert out["blocked"] == [], out["blocked"]
    assert out["update"] is written
    assert _norm(out["nv"]) == expected
    if written:
        assert set(out["changed"]) <= set(QOS_KEYS) and out["ask_legs"] == [0, 1]


def test_an_untouched_merged_keeps_a_residual_policy_of_a_disabled_qos_and_the_children_never_see_it():
    have = _have()
    have["QOS_POLICY"] = "RESIDUAL"  # ENABLE_QOS false, a policy left by another tool
    out = _reconcile("merged", have, peer1_description="d1", peer2_description="d2")
    assert out["blocked"] == [] and out["nv"]["QOS_POLICY"] == "RESIDUAL" and "QOS_POLICY" not in out["changed"]
    for index in (0, 1):
        child = P.vpc_leg_po_nv(out["nv"], index, "vPC10")
        assert child["QOS_POLICY"] == "" and not any("service-policy type qos" in x for x in P.render(P.VPC_PO_POLICY, child).scalars)


@pytest.mark.parametrize(
    "have, want, needle",
    [
        ({}, dict(enable_qos=True), "needs a qos_policy"),
        ({}, dict(enable_qos=False, qos_policy="Q1"), "qos_policy requires enable_qos true"),
        ({}, dict(qos_policy="Q1"), "qos_policy requires enable_qos true"),
        ({}, dict(disable_qos_stats=True), "disable_qos_stats true only takes effect"),
        (dict(enable_qos=True, qos_policy="Q1"), dict(enable_qos=False, disable_qos_stats=True), "disable_qos_stats true only takes effect"),
    ],
)
def test_combinations_the_template_cannot_honour_are_refused_before_any_write(have, want, needle):
    out = _reconcile("merged", _have(**have), **want)
    assert out["update"] is False and any(needle in b for b in out["blocked"]), out["blocked"]


def test_raw_values_follow_the_template_types():
    assert P.vpc_not_implemented(dict(_raw(), enable_qos="yes"), "vPC10") == ["enable_qos must be a boolean"]
    assert "qos_policy must be one policy-map name" in P.vpc_not_implemented(dict(_raw(), qos_policy="a b"), "vPC10")[0]
    out = _reconcile("merged", _have(), patch=None, **ON)
    assert out["update"] is False and any("requires caller-supplied patch_version" in b for b in out["blocked"]), out["blocked"]


# ====================================================================================== child expectation (corrected templates)
@pytest.mark.parametrize("stats, line", [(False, "service-policy type qos input Q1"), (True, "service-policy type qos input Q1 no-stats")])
def test_both_children_carry_the_qos_line_of_the_corrected_child(stats, line):
    nv = _have(enable_qos=True, qos_policy="Q1", disable_qos_stats=stats)
    for index in (0, 1):
        child = P.vpc_leg_po_nv(nv, index, "vPC10")
        assert (child["ENABLE_QOS"], child["QOS_POLICY"], child["qosStatsSuppressed"]) == ("true", "Q1", "true" if stats else "false")
        scalars = P.render(P.VPC_PO_POLICY, child).scalars
        assert line in scalars and not any("ENABLE_QOS" in x for x in scalars)


def test_a_child_that_lost_the_qos_values_differs_from_its_parent():
    nv = _have(enable_qos=True, qos_policy="Q1")
    expected = P.vpc_leg_po_nv(nv, 0, "vPC10")
    lost = dict(expected, ENABLE_QOS="false", QOS_POLICY="")   # the MEASURED shape of the installed revision
    assert set(P.vpc_child_differences(lost, expected)) == {"ENABLE_QOS", "QOS_POLICY"}
    assert P.vpc_child_differences(dict(expected, QOS_POLICY="q1"), expected) == ["QOS_POLICY"]  # exact name


# ====================================================================================== main(): positive, corrected templates
def _child_with_qos(line):
    return V.po_stanza() + ["  " + line] if line else V.po_stanza()


def _preview(serial, port, run_line, exp_line, pend):
    return V.preview(pend, serial=serial, running=_child_with_qos(run_line) + V.member_after(port),
                     expected=_child_with_qos(exp_line) + V.member_after(port))


def _queue(ctrl, run_line, exp_line, pend, preflight_line=None):
    for serial, port in ((V.SN1, V.M1), (V.SN2, V.M2)):
        ctrl.vpc_previews[serial] = [_preview(serial, port, preflight_line, preflight_line, []), _preview(serial, port, run_line, exp_line, pend)]


LINE = "service-policy type qos input Q1 no-stats"
ADD = ["interface port-channel10", "  " + LINE]


def _seeded(**qos):
    ctrl = V.created_ctrl()
    parent = ctrl.parents[V.VPC]["nvPairs"]
    parent.update(qos)
    ctrl._expand_children(parent)
    return ctrl


def test_enabling_qos_with_an_explicit_policy_reaches_both_children_and_the_repeat_writes_nothing():
    ctrl = V.created_ctrl()
    _queue(ctrl, None, LINE, ADD)
    status, res = V.run_vpc(ctrl, [V.vpc_item(**ON)], state="merged", patch_version=SMU)
    assert status == "exit" and res["changed"] is True, res.get("msg")
    sent = json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]
    assert _norm(sent) == {"ENABLE_QOS": "true", "QOS_POLICY": "Q1", "qosStatsSuppressed": "true"}
    assert len(ctrl.deploys()) == 1
    for serial in (V.SN1, V.SN2):
        child = ctrl.nodes[serial]["port-channel10"]["nvPairs"]
        assert (child["ENABLE_QOS"], child["QOS_POLICY"], child["qosStatsSuppressed"]) == ("true", "Q1", "true")
    ctrl.next_invocation()
    before = len(ctrl.writes())
    for serial, port in ((V.SN1, V.M1), (V.SN2, V.M2)):
        ctrl.vpc_previews[serial] = [_preview(serial, port, LINE, LINE, [])]
    status, res = V.run_vpc(ctrl, [V.vpc_item(**ON)], state="merged", patch_version=SMU)
    assert status == "exit" and res["changed"] is False, res
    assert len(ctrl.writes()) == before


def test_merged_omission_keeps_qos_and_replaced_withdraws_it_on_both_peers():
    ctrl = _seeded(ENABLE_QOS="true", QOS_POLICY="Q1", qosStatsSuppressed="true")
    pend = ["interface port-channel10", "  description d1"]
    for serial, port, desc in ((V.SN1, V.M1, "d1"), (V.SN2, V.M2, "d2")):
        run_cfg = _child_with_qos(LINE) + V.member_after(port)
        exp = _child_with_qos(LINE) + ["  description %s" % desc] + V.member_after(port)
        ctrl.vpc_previews[serial] = [V.preview([], serial=serial, running=run_cfg, expected=run_cfg),
                                     V.preview(["interface port-channel10", "  description %s" % desc], serial=serial, running=run_cfg, expected=exp)]
    status, res = V.run_vpc(ctrl, [V.vpc_item(peer1_description="d1", peer2_description="d2")], state="merged", patch_version=SMU)
    assert status == "exit" and res["changed"] is True, res.get("msg")
    sent = json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]
    assert _norm(sent) == {"ENABLE_QOS": "true", "QOS_POLICY": "Q1", "qosStatsSuppressed": "true"}
    # replaced without the QoS keys: reset, and the pending must withdraw the line on both peers
    ctrl = _seeded(ENABLE_QOS="true", QOS_POLICY="Q1", qosStatsSuppressed="true")
    _queue(ctrl, LINE, None, ["interface port-channel10", "  no " + LINE], preflight_line=LINE)
    status, res = V.run_vpc(ctrl, [V.vpc_item()], state="replaced", patch_version=SMU)
    assert status == "exit" and res["changed"] is True, res.get("msg")
    sent = json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]
    assert _norm(sent) == {"ENABLE_QOS": "false", "QOS_POLICY": "", "qosStatsSuppressed": "false"} and len(ctrl.deploys()) == 1
    del pend


def test_a_policy_change_withdraws_the_old_line_and_adds_the_new_one():
    ctrl = _seeded(ENABLE_QOS="true", QOS_POLICY="Q1", qosStatsSuppressed="true")
    new = "service-policy type qos input Q2 no-stats"
    _queue(ctrl, LINE, new, ["interface port-channel10", "  no " + LINE, "  " + new], preflight_line=LINE)
    status, res = V.run_vpc(ctrl, [V.vpc_item(qos_policy="Q2")], state="merged", patch_version=SMU)
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]["QOS_POLICY"] == "Q2"


# ====================================================================================== main(): negatives
def test_the_installed_revision_that_drops_the_values_is_refused_before_any_deploy():
    """The MEASURED parent -> children loss: the parent stores the QoS values, both children keep ENABLE_QOS false / QOS_POLICY '', the
    controller's expected child configuration has no qos line, and the preview is In-Sync. Refused, never deployed."""
    ctrl = V.created_ctrl()
    ctrl.defective_qos_template = True
    _queue(ctrl, None, None, [])
    status, res = V.run_vpc(ctrl, [V.vpc_item(**ON)], state="merged", patch_version=SMU)
    assert status == "fail" and ctrl.deploys() == [], res
    assert "service-policy type qos input Q1 no-stats" in res["msg"] and "disagrees with the intended state" in res["msg"]
    for serial in (V.SN1, V.SN2):
        child = ctrl.nodes[serial]["port-channel10"]["nvPairs"]
        assert (child["ENABLE_QOS"], child["QOS_POLICY"], child["qosStatsSuppressed"]) == ("false", "", "true")
    # the next invocation sees the partial state and refuses before any write
    ctrl.next_invocation()
    writes = len(ctrl.writes())
    status, res = V.run_vpc(ctrl, [V.vpc_item(**ON)], state="merged", patch_version=SMU)
    assert status == "fail" and "does not follow the parent's intent" in res["msg"] and "ENABLE_QOS" in res["msg"], res
    assert len(ctrl.writes()) == writes and ctrl.deploys() == []


class LoseAfterDeploy(V.VpcController):
    """SYNTHETIC: the child of peer 2 loses the QoS values after the deploy (a later regeneration by the installed revision)."""

    def __call__(self, mod, method, path, data=None):
        resp = super(LoseAfterDeploy, self).__call__(mod, method, path, data)
        if method == "POST" and path.endswith(V.DEPLOY) and "port-channel10" in self.nodes[V.SN2]:
            self.nodes[V.SN2]["port-channel10"]["nvPairs"].update({"ENABLE_QOS": "false", "QOS_POLICY": ""})
        return resp


def test_a_child_that_loses_the_values_after_the_deploy_is_reported_without_rewrite():
    ctrl = V.created_ctrl()
    ctrl.__class__ = LoseAfterDeploy
    _queue(ctrl, None, LINE, ADD)
    status, res = V.run_vpc(ctrl, [V.vpc_item(**ON)], state="merged", patch_version=SMU)
    assert status == "fail" and "post-deploy intent readback differs" in res["msg"] and "QOS_POLICY" in res["msg"], res
    assert len(ctrl.modifies()) == 1 and len(ctrl.deploys()) == 1
    at = max(i for i, c in enumerate(ctrl.calls) if c[0] == "POST" and c[1].endswith(V.DEPLOY))
    assert [c for c in ctrl.calls[at + 1:] if c[0] in ("POST", "PUT", "DELETE") and "config-preview" not in c[1]] == []


def test_an_error_item_on_the_parent_modify_stops_before_any_deploy():
    ctrl = V.created_ctrl()
    _queue(ctrl, None, LINE, ADD)
    ctrl.modify_responses = [{"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [
        {"reportItemType": "ERROR", "message": "QoS policy Q1 not found", "entity": "%s~vPC10" % V.PAIR}]}]
    status, res = V.run_vpc(ctrl, [V.vpc_item(**ON)], state="merged", patch_version=SMU)
    # the QoS request reached the parent modify (one attempt), the per-item ERROR is reported, nothing is deployed or retried
    assert status == "fail" and len(ctrl.modifies()) == 1 and ctrl.deploys() == [], res
    assert "QoS policy Q1 not found" in res["msg"] and "Nothing in this batch was applied" in res["msg"]
    sent = json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]
    assert _norm(sent) == {"ENABLE_QOS": "true", "QOS_POLICY": "Q1", "qosStatsSuppressed": "true"}


@pytest.mark.parametrize(
    "profile, needle",
    [
        (dict(enable_qos=True), "needs a qos_policy"),
        (dict(enable_qos=False, qos_policy="Q1"), "qos_policy requires enable_qos true"),
        (dict(disable_qos_stats=True), "disable_qos_stats true only takes effect"),
    ],
)
def test_refusals_reach_main_before_any_write(profile, needle):
    ctrl = V.created_ctrl()
    status, res = V.run_vpc(ctrl, [V.vpc_item(**profile)], state="merged", patch_version=SMU)
    assert status == "fail" and needle in res["msg"] and ctrl.writes() == [], res
