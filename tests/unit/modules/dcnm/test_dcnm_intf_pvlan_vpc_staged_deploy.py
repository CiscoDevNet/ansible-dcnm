"""PR725-VPC-STAGED-DEPLOY-CHECKER: a PVLAN host vPC deployed in two stages, and check_deploy on a vPC creation/update.

A  (MEASURED live by Beta, S3b/S3d, NDFC 12.6.0.267): a vPC created with ``deploy: false`` (intent saved, nothing on the devices) could not be
   continued with ``deploy: true``: the pre-write gate judged the saved creation as a deployed baseline (no Po on the device, the member still
   a standalone trunk) and refused, and the code stated that completing an unapplied vPC was not implemented.
B  (MEASURED live by Beta, S3j): ``check_deploy: true`` on a vPC creation converged, then the safety re-deploy gate (check_deploy_resend)
   judged the vPC again with the creation rule "every peer must still need a deploy" and failed although the deploy had converged.

The never-deployed vPC parent is listed with ``complianceStatus`` null (MEASURED, Beta S1/S3b); the children report Out-of-Sync before the
deploy. Previews: the harness creation/converged stanzas (members down, H1 shape) and the MEASURED up-member vPC previews of
fixtures/pvlan_admin_up_join_measured.json (M3, pre/post deploy). Real main(); only the controller boundary and time are intercepted.
NOT LIVE TESTED by this file."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
from unittest.mock import patch

import pytest

from ansible.module_utils import basic
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import AnsibleExitJson, AnsibleFailJson, exit_json, fail_json
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from . import test_dcnm_intf_pvlan_vpc_harness as V
from . import test_dcnm_intf_pvlan_admin_up_join as UP
from .dcnm_module import set_module_args


class Staged(V.VpcController):
    """VpcController whose vPC parent is listed with complianceStatus null and whose children are Out-of-Sync until a deploy succeeded
    (MEASURED shape of a saved, not yet deployed vPC); `applied` survives invocations, `deployed` (harness) does not."""

    def __init__(self):
        super(Staged, self).__init__()
        self.applied = False

    def _peer_summary(self, serial):
        out = super(Staged, self)._peer_summary(serial)
        if not self.applied:
            for e in out:
                if e.get("ifType") == "INTERFACE_VPC":
                    e["complianceStatus"] = None
                elif e.get("ifName", "").lower().startswith("port-channel"):
                    e["complianceStatus"] = "Out-of-Sync"
        return out

    def __call__(self, mod, method, path, data=None):
        resp = super(Staged, self).__call__(mod, method, path, data)
        if method == "POST" and path.endswith(V.DEPLOY) and resp.get("RETURN_CODE") == 200:
            self.applied = True
        return resp


def run(ctrl, config, state="merged", check_deploy=True):
    """V.run_vpc with check_deploy chosen by the test (the harness fixes it to False)."""
    args = {"state": state, "fabric": V.FABRIC, "config": config, "check_deploy": check_deploy}
    patches = [
        patch.object(basic.AnsibleModule, "exit_json", exit_json),
        patch.object(basic.AnsibleModule, "fail_json", fail_json),
        patch.object(module, "get_fabric_inventory_details", return_value=copy.deepcopy(V.INVENTORY)),
        patch.object(module, "get_ip_sn_dict", return_value=({V.IP1: V.SN1, V.IP2: V.SN2}, {})),
        patch.object(module, "dcnm_get_ip_addr_info", side_effect=lambda m, sw, a, b: sw),
        patch.object(module, "dcnm_version_supported", return_value=(12, V.NDFC)),
        patch.object(module, "dcnm_send", side_effect=ctrl),
        patch.object(module, "dcnm_get_bulk_api_support", return_value=True),
        patch.object(module, "get_fabric_details", return_value={"nvPairs": {"HOST_INTF_ADMIN_STATE": "false"}}),
        patch.object(module.time, "sleep", return_value=None),
    ]
    for p in patches:
        p.start()
    try:
        set_module_args(args)
        try:
            module.main()
        except AnsibleExitJson as exc:
            return "exit", exc.args[0]
        except AnsibleFailJson as exc:
            return "fail", exc.args[0]
        raise AssertionError("main() returned without exit_json/fail_json")
    finally:
        for p in reversed(patches):
            p.stop()


def down_create(serial):
    return V.create_preview(serial, V.M1 if serial == V.SN1 else V.M2)


def down_converged(serial):
    return V.converged_preview(serial, V.M1 if serial == V.SN1 else V.M2)


def up_create(serial):
    return UP.vpc_preview(serial, V.M1 if serial == V.SN1 else V.M2, phase="pre_deploy", serial_fx=UP.LEAF_B if serial == V.SN1 else UP.LEAF_A)


def up_converged(serial):
    return UP.vpc_preview(serial, V.M1 if serial == V.SN1 else V.M2, phase="post_deploy", serial_fx=UP.LEAF_B if serial == V.SN1 else UP.LEAF_A)


FORMS = {"down": (down_create, down_converged), "up": (up_create, up_converged)}


def ctrl_for(form):
    ctrl = Staged().seed_baseline()
    if form == "up":
        UP.up_peers(ctrl)
    return ctrl


def queue(ctrl, *makers):
    for serial in (V.SN1, V.SN2):
        ctrl.vpc_previews[serial] = [make(serial) for make in makers]


def saved_not_applied(form, state="merged"):
    """Stage 1, through main(): the vPC is created with deploy false (one create, no deploy, no preview)."""
    ctrl = ctrl_for(form)
    status, result = run(ctrl, [V.vpc_item(deploy=False)], state=state, check_deploy=False)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.creates()) == 1 and ctrl.deploys() == [] and ctrl.previews_asked() == []
    ctrl.next_invocation()
    ctrl.calls = []
    return ctrl


# ================================================================== B: check_deploy on a creation / an update
@pytest.mark.parametrize("form", ["down", "up"])
def test_b_creation_with_check_deploy_accepts_the_converged_resend_check(form):
    ctrl = ctrl_for(form)
    create, converged = FORMS[form]
    queue(ctrl, create, converged)  # deploy gate, then the check_deploy_resend gate after the accepted deploy
    status, result = run(ctrl, [V.vpc_item()])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1, "converged at the resend check: no second deploy"
    sites = [(g["site"], g["targets"]["vPC10"]) for g in result["pvlan_gate"]]
    assert sites == [("deploy", "deploy")] * 2 + [("check_deploy_resend", "converged")] * 2


def test_b_a_straggler_peer_after_the_deploy_is_resent_once():
    ctrl = ctrl_for("down")
    ctrl.vpc_previews[V.SN1] = [down_create(V.SN1), down_converged(V.SN1)]
    ctrl.vpc_previews[V.SN2] = [down_create(V.SN2), down_create(V.SN2)]  # peer 2 not applied yet at the resend check
    status, result = run(ctrl, [V.vpc_item()])
    assert status == "exit", result.get("msg")
    assert len(ctrl.deploys()) == 2, "the safety re-deploy still covers a peer that the first deploy did not apply"


def test_b_foreign_pending_at_the_resend_check_is_still_refused():
    ctrl = ctrl_for("down")
    queue(ctrl, down_create, down_converged)
    entry = ctrl.vpc_previews[V.SN2][1]["DATA"][0]
    entry["pendingConfig"] += ["interface port-channel99", "  description foreign", "configure terminal"]
    entry["status"] = "Out-of-Sync"  # a pending makes the peer Out-of-Sync (an In-Sync status with a pending is refused on its own)
    status, result = run(ctrl, [V.vpc_item()])
    assert status == "fail" and len(ctrl.deploys()) == 1, result.get("msg")
    assert "check_deploy_resend" in result["msg"] and "outside this deploy batch: port-channel99" in result["msg"]


def test_b_an_unreadable_peer_at_the_resend_check_is_still_refused():
    ctrl = ctrl_for("down")
    queue(ctrl, down_create, down_converged)
    ctrl.vpc_previews[V.SN2][1] = {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}
    status, result = run(ctrl, [V.vpc_item()])
    assert status == "fail" and len(ctrl.deploys()) == 1, result.get("msg")
    assert "check_deploy_resend" in result["msg"]


def test_b_no_convergence_after_the_deploy_still_fails():
    ctrl = ctrl_for("down")
    queue(ctrl, down_create, down_converged)
    ctrl.compliance_by[(V.SN2, "port-channel10")] = "Out-of-Sync"
    status, result = run(ctrl, [V.vpc_item()])
    assert status == "fail" and len(ctrl.deploys()) == 1, result.get("msg")
    assert "In-Sync" in result["msg"]


def test_b_an_update_with_check_deploy_accepts_the_converged_resend_check():
    ctrl = V.created_ctrl()
    ctrl.vpc_previews[V.SN1] = [V.converged_preview(V.SN1, V.M1), V.description_preview(V.SN1, V.M1, None, "a1-peer1"),
                                V.converged_preview(V.SN1, V.M1, desc="a1-peer1")]
    ctrl.vpc_previews[V.SN2] = [V.converged_preview(V.SN2, V.M2), V.converged_preview(V.SN2, V.M2), V.converged_preview(V.SN2, V.M2)]
    status, result = run(ctrl, [V.vpc_item(peer1_description="a1-peer1")])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.modifies()) == 1 and len(ctrl.deploys()) == 1


def test_b_an_identical_repetition_with_check_deploy_writes_nothing():
    ctrl = V.created_ctrl()
    queue(ctrl, down_converged)
    status, result = run(ctrl, [V.vpc_item()])
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.writes() == []


# ================================================================== A: deploy false, then deploy true
@pytest.mark.parametrize("state", ["merged", "replaced"])
@pytest.mark.parametrize("form", ["down", "up"])
def test_a_a_saved_vpc_is_completed_by_the_next_deploy_true(form, state):
    ctrl = saved_not_applied(form, state)
    create, converged = FORMS[form]
    queue(ctrl, create, create, converged)  # pre-write check of the saved creation, deploy gate, resend check
    status, result = run(ctrl, [V.vpc_item()], state=state)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.creates() == [] and ctrl.modifies() == [] and len(ctrl.deploys()) == 1, "no intent rewrite, exactly one deploy"
    assert [d["ifName"] for d in json.loads(ctrl.deploys()[0][2])] == ["vPC10"]
    sites = [(g["site"], g["targets"]["vPC10"]) for g in result["pvlan_gate"]]
    assert sites == [("prior", "deploy")] * 2 + [("deploy", "deploy")] * 2 + [("check_deploy_resend", "converged")] * 2
    # the next identical run is a no-op on a deployed baseline
    ctrl.next_invocation()
    ctrl.calls = []
    queue(ctrl, converged)
    status, result = run(ctrl, [V.vpc_item()], state=state)
    assert status == "exit" and result["changed"] is False and ctrl.writes() == [], result.get("msg")


def test_a_without_check_deploy_the_saved_vpc_is_deployed_once():
    ctrl = saved_not_applied("down")
    queue(ctrl, down_create, down_create)
    status, result = run(ctrl, [V.vpc_item()], check_deploy=False)
    assert status == "exit" and len(ctrl.deploys()) == 1 and ctrl.creates() == [] and ctrl.modifies() == [], result.get("msg")


def test_a_a_repeated_deploy_false_writes_nothing():
    ctrl = saved_not_applied("down")
    status, result = run(ctrl, [V.vpc_item(deploy=False)], check_deploy=False)
    assert status == "exit" and result["changed"] is False and ctrl.writes() == [], result.get("msg")


def test_a_foreign_pending_on_a_peer_refuses_before_any_write():
    ctrl = saved_not_applied("down")
    queue(ctrl, down_create, down_create, down_converged)
    ctrl.vpc_previews[V.SN1][0]["DATA"][0]["pendingConfig"] += ["interface port-channel99", "  description foreign", "configure terminal"]
    status, result = run(ctrl, [V.vpc_item()])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")
    assert "outside this deploy batch: port-channel99" in result["msg"]


def test_a_one_peer_already_applied_is_a_partial_state_and_refused():
    ctrl = saved_not_applied("down")
    ctrl.vpc_previews[V.SN1] = [down_converged(V.SN1)]
    ctrl.vpc_previews[V.SN2] = [down_create(V.SN2)]
    status, result = run(ctrl, [V.vpc_item()])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")
    assert "peer 1 is already converged" in result["msg"]


def test_a_an_unreadable_peer_preview_refuses_before_any_write():
    ctrl = saved_not_applied("down")
    queue(ctrl, down_create)
    ctrl.vpc_previews[V.SN2][0] = {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}
    status, result = run(ctrl, [V.vpc_item()])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")


def test_a_a_pending_that_shuts_an_up_member_is_refused_before_any_write():
    ctrl = saved_not_applied("up")
    queue(ctrl, up_create)
    UP.shut_the_member({"pending": ctrl.vpc_previews[V.SN1][0]["DATA"][0]["pendingConfig"]})  # the same list, changed in place
    status, result = run(ctrl, [V.vpc_item()])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")


def test_a_a_changed_request_on_a_saved_vpc_stays_refused_before_any_write():
    ctrl = saved_not_applied("down")
    queue(ctrl, down_create)
    status, result = run(ctrl, [V.vpc_item(peer1_description="changed")])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")


def test_a_the_controller_parent_deployed_but_peers_not_converged_is_not_a_saved_creation():
    # the parent already reports a compliance value: the vPC was deployed once; a missing Po on the device is a drift, not a creation
    ctrl = saved_not_applied("down")
    ctrl.applied = True
    queue(ctrl, down_create)
    status, result = run(ctrl, [V.vpc_item()])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")
