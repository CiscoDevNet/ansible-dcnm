"""RC2: the three LOW findings of the offline RC1 review (DELTA_SPEED_FREEFORM_REVIEW L1, L2, L3).

NOT LIVE TESTED. Real main() through the EXISTING harnesses, with the SYNTHETIC template-predicted previews of the RC1 file.
  L1 - a command repeated inside ONE freeform request is kept once, in the order of its first appearance (creation, merged, replaced,
       idempotency; port-channel and vPC);
  L2 - the port-channel post-deploy intent readback compares SPEED and CONF, with the existing normalization; a difference is reported,
       never retried or rewritten;
  L3 - the INFERRED withdrawal of an adopted `no negotiate auto` when the speed returns to Auto: deployed only when the pending carries
       it (as `negotiate auto`), refused before any deploy otherwise. This documents RC1 behaviour; it is not a behaviour change.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .test_dcnm_intf_pvlan_harness import IF7, preview, run
from .test_dcnm_intf_pvlan_po_g1 import PoLifecycleController, member_stanza, po_stanza
from .test_dcnm_intf_pvlan_po_host import DEPLOY, PO, PO_HOST
from .test_dcnm_intf_pvlan_speed_freeform import (
    ASSOC,
    FF_A,
    FF_B,
    HOST_LINES,
    _po_cfg,
    _po_have,
    _po_update_preview,
    _po_want,
    _vpc_legs,
    _vpc_raw,
    created_with,
)


# ====================================================================================== L1: repeated commands inside one request
def test_freeform_request_keeps_each_command_once_in_first_appearance_order():
    assert P.freeform_request([FF_B, FF_A, FF_B, " " + FF_A, FF_A + " "]) == [FF_B, FF_A]
    assert P.freeform_request([]) == [] and P.freeform_request(None) == []


@pytest.mark.parametrize(
    "state, have, want, conf",
    [
        ("merged", None, [FF_A, FF_B, FF_A], [FF_A, FF_B]),            # creation
        ("merged", [FF_A], [FF_B, FF_B, FF_A], [FF_A, FF_B]),          # merged appends the new command once
        ("replaced", [FF_A], [FF_B, FF_A, FF_B], [FF_B, FF_A]),        # replaced: exact list, first appearance order
        ("replaced", None, [FF_B, FF_B], [FF_B]),                      # creation through replaced
    ],
)
def test_port_channel_request_duplicates_are_stored_once(state, have, want, conf):
    have_nv = _po_have(cmds=have) if have is not None else None
    out = P.reconcile_po(state, _po_want(cmds=want), PO, PO_HOST if have_nv else None, have_nv)
    assert out["blocked"] == [], out["blocked"]
    assert P.freeform_lines(out["nv"]["CONF"]) == conf
    # idempotency: the same request against the intent it produced writes nothing
    again = P.reconcile_po(state, _po_want(cmds=want), PO, PO_HOST, out["nv"])
    assert again["blocked"] == [] and again["update"] is False


def test_vpc_request_duplicates_are_stored_once_per_peer_and_repeat_is_a_no_op():
    raw = _vpc_raw(peer1_cmds=[FF_A, FF_A], peer2_cmds=[FF_B, FF_A, FF_B])
    nv = P.vpc_host_nvpairs(raw, "vPC10", _vpc_legs(raw))
    assert (P.freeform_lines(nv["PEER1_PO_CONF"]), P.freeform_lines(nv["PEER2_PO_CONF"])) == ([FF_A], [FF_B, FF_A])
    for state in ("merged", "replaced"):
        out = P.reconcile_vpc(state, raw, "vPC10", _vpc_legs(raw), P.VPC_HOST_POLICY, nv)
        assert out["blocked"] == [] and out["update"] is False, (state, out["blocked"], out["changed"])
    have_raw = _vpc_raw(peer1_cmds=[FF_A], peer2_cmds=[FF_A])
    have = P.vpc_host_nvpairs(have_raw, "vPC10", _vpc_legs(have_raw))
    want = _vpc_raw(peer1_cmds=[FF_B, FF_B], peer2_cmds=[FF_B, FF_A, FF_B])
    out = P.reconcile_vpc("merged", want, "vPC10", _vpc_legs(want), P.VPC_HOST_POLICY, have)
    assert out["blocked"] == [] and out["update"] is True
    assert P.freeform_lines(out["nv"]["PEER1_PO_CONF"]) == [FF_A, FF_B] and P.freeform_lines(out["nv"]["PEER2_PO_CONF"]) == [FF_A, FF_B]


def test_po_merged_request_with_a_repeated_command_sends_it_once_through_main_and_the_repeat_writes_nothing():
    ctrl, _r = created_with([], [])
    old_po, old_m = po_stanza("host", HOST_LINES), member_stanza("host", HOST_LINES)
    ctrl.previews = [_po_update_preview(old_po, old_po + ["  " + FF_A], old_m, old_m, ["interface port-channel10", "  " + FF_A])]
    status, result = run(ctrl, [_po_cfg(cmds=[FF_A, FF_A])], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]["CONF"] == FF_A
    ctrl.next_invocation()
    ctrl.calls = []
    status, result = run(ctrl, [_po_cfg(cmds=[FF_A, FF_A])], state="merged")
    assert status == "exit" and result["changed"] is False, result
    assert ctrl.writes() == [] and ctrl.deploys() == []


# ====================================================================================== L2: Po post-deploy readback of SPEED / CONF
def test_po_intent_same_reuses_the_existing_normalization():
    sent = {"SPEED": "10Gb", "CONF": FF_A + "\n" + FF_B}
    assert P.po_intent_same("SPEED", {"SPEED": "10Gb"}, sent)
    assert P.po_intent_same("CONF", {"CONF": FF_B + "\n" + FF_A + "\n"}, sent)  # order and blank lines ignored, as _po_same
    assert P.po_intent_same("SPEED", {}, {"SPEED": "Auto"}) and P.po_intent_same("CONF", {}, {"CONF": ""})  # absent = template value
    assert not P.po_intent_same("SPEED", {"SPEED": "Auto"}, sent)
    assert not P.po_intent_same("CONF", {"CONF": FF_A}, sent)


class DriftAfterDeploy(PoLifecycleController):
    """SYNTHETIC: after the deploy the controller returns a port-channel intent that differs in `drift` (e.g. a value it did not keep)."""

    drift = {}

    def __call__(self, mod, method, path, data=None):
        resp = super(DriftAfterDeploy, self).__call__(mod, method, path, data)
        if method == "POST" and path.endswith(DEPLOY) and PO in self.detail:
            self.detail[PO]["nvPairs"].update(self.drift)
        return resp


@pytest.mark.parametrize("drift, key", [({"SPEED": "Auto"}, "SPEED"), ({"CONF": ""}, "CONF"), ({"SPEED": "1Gb", "CONF": FF_B}, "SPEED, CONF")])
def test_po_readback_reports_a_lost_speed_or_freeform_without_retry_or_rewrite(drift, key):
    ctrl, _r = created_with([], [])
    ctrl.__class__ = DriftAfterDeploy
    ctrl.drift = drift
    old_po, old_m = po_stanza("host", HOST_LINES), member_stanza("host", HOST_LINES)
    new_po = old_po + ["  speed 10000", "  " + FF_A]
    new_m = old_m + ["  speed 10000"]
    pend = ["interface port-channel10", "  speed 10000", "  " + FF_A, "interface ethernet1/7", "  speed 10000"]
    ctrl.previews = [_po_update_preview(old_po, new_po, old_m, new_m, pend)]
    status, result = run(ctrl, [_po_cfg(speed="10Gb", cmds=[FF_A])], state="merged")
    assert status == "fail" and "post-deploy intent readback differs in %s" % key in result["msg"], result.get("msg")
    # reported only: one intent write, one deploy, nothing written after the deploy
    assert len(ctrl.bulk_bodies()) == 1 and len(ctrl.deploys()) == 1
    deploy_at = max(i for i, c in enumerate(ctrl.calls) if c[0] == "POST" and c[1].endswith(DEPLOY))
    assert [c for c in ctrl.calls[deploy_at + 1:] if c[0] in ("POST", "PUT", "DELETE") and "/config-preview" not in c[1]] == []


def test_po_readback_with_the_kept_speed_and_freeform_passes():
    ctrl, _r = created_with([], [])
    ctrl.__class__ = DriftAfterDeploy
    ctrl.drift = {"CONF": FF_A + "\n"}  # same commands, a trailing line break: not a difference
    old_po, old_m = po_stanza("host", HOST_LINES), member_stanza("host", HOST_LINES)
    pend = ["interface port-channel10", "  speed 10000", "  " + FF_A, "interface ethernet1/7", "  speed 10000"]
    ctrl.previews = [_po_update_preview(old_po, old_po + ["  speed 10000", "  " + FF_A], old_m, old_m + ["  speed 10000"], pend)]
    status, result = run(ctrl, [_po_cfg(speed="10Gb", cmds=[FF_A])], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")


# ====================================================================================== L3: withdrawal of the adopted capability line
def _back_to_auto(pend_negotiate):
    base = dict(members=[IF7], admin_state=False)
    ctrl, _r = created_with(["speed 10000", "no negotiate auto"], ["speed 10000", "no negotiate auto"], speed="10Gb")
    run_po = po_stanza("host", HOST_LINES) + ["  speed 10000", "  no negotiate auto"]
    run_m = member_stanza("host", HOST_LINES) + ["  speed 10000", "  no negotiate auto"]
    po_pend = ["interface port-channel10", "  no speed 10000"] + (["  negotiate auto"] if pend_negotiate else [])
    m_pend = ["interface ethernet1/7", "  no speed 10000"] + (["  negotiate auto"] if pend_negotiate else [])
    ctrl.previews = [preview(po_pend + m_pend, running=run_po + run_m,
                             expected=po_stanza("host", HOST_LINES) + member_stanza("host", HOST_LINES))]
    return run(ctrl, [_po_cfg(pvlan_association=ASSOC, **base)], state="replaced"), ctrl


def test_speed_back_to_auto_deploys_when_the_pending_withdraws_the_adopted_capability_line():
    (status, result), ctrl = _back_to_auto(True)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]["SPEED"] == "Auto" and len(ctrl.deploys()) == 1


def test_speed_back_to_auto_is_refused_before_any_deploy_when_the_capability_line_is_not_withdrawn():
    (status, result), ctrl = _back_to_auto(False)
    assert status == "fail" and "withdrawal of 'no negotiate auto' is absent from the pending" in result["msg"], result.get("msg")
    assert ctrl.deploys() == []
