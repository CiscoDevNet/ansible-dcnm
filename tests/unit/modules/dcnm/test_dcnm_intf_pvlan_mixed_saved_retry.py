"""A saved mixed conventional/PVLAN aggregate deletion completed by a LATER dcnm_interface invocation with deployment.

Invocation 1: `state: deleted`, a conventional port-channel + a PVLAN Po (and the vPC analogue), every item deploy false. Both
mark-deletes are confirmed, the members are released in intent, nothing is deployed; the module process ends.
Invocation 2: a NEW module instance (fresh main()) requests the deletion of the same aggregates with the global AND per-item deploy
true. Nothing of invocation 1 survives except the controller state the fake keeps: the conventional port-channel listed in the
MEASURED "marked for deletion" form (markDeleted, one `interface_delete` policy whose source is itself -- for a vPC child, its
parent vPC), its released members, and a device running configuration that still holds the aggregate with those members joined
(fresh forced preview).

Rule under test: the conventional saved deletion is completed together with the PVLAN one only when THIS request names it with
deployment and the controller state above proves it on every physical serial; ambiguous, unrelated or unverifiable state refuses
with nothing deployed.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

import pytest

from .dcnm_interface.helpers import ethernet_controller as HH
from .dcnm_interface.helpers import port_channel_controller as G5
from .dcnm_interface.helpers import vpc_controller as R
from .dcnm_interface.helpers import vpc_controller as V
from .dcnm_interface.helpers.ethernet_controller import SERIAL, SWITCH_IP, run
from .test_dcnm_intf_pvlan_mixed_batch import released_block
from .test_dcnm_intf_pvlan_mixed_delete import C14, T6_GLOBAL, vpc_conv_pending
from .dcnm_interface.helpers.mixed_controller import (
    CONV_RUNNING,
    SavedConvController,
    deploy_bodies,
    later_writes,
    queue_vpc,
    retry,
    saved_po_ctrl,
    saved_preview,
    saved_vpc_ctrl,
    stage,
    vpc_owned,
    vpc_retry,
)


# ================================================================== regular port-channels
def test_fresh_deploy_true_invocation_completes_the_saved_mixed_po_deletion_from_controller_state():
    ctrl = saved_po_ctrl()
    stage(ctrl)
    status, result, start = retry(ctrl)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    writes = later_writes(ctrl, start)
    assert "interface/markdelete" not in writes, "no second mark-delete: the saved deletion is continued, not redone"
    assert writes.count("globalInterface/deploy") == 1
    sent = sorted((i["serialNumber"], i["ifName"].lower()) for b in deploy_bodies(ctrl, start) for i in b)
    assert sent == [(SERIAL, "port-channel301"), (SERIAL, "port-channel502")], "only the two saved deletions are deployed"
    assert ctrl.conv_marked is None and ctrl.marked is None, "both port-channels are gone after the deploy"
    rel = [r for r in result["pvlan_gate_invocation_releases"] if r["site"] == "delete_deploy"]
    assert rel == [{"site": "delete_deploy", "serial": SERIAL, "interfaces": ["ethernet1/14"], "withdrawn": ["no interface port-channel301"]}]
    assert any(r.get("state") == "completing the saved deletion" and r.get("kind") == "conventional" for r in result["pvlan_saved"])


def test_a_further_repeat_after_the_completed_deletion_writes_and_deploys_nothing():
    ctrl = saved_po_ctrl()
    stage(ctrl)
    status, result, _start = retry(ctrl)
    assert status == "exit", result.get("msg")
    ctrl.next_invocation()
    status, result, start = retry(ctrl, preview=G5.corrected_hr_preview(), previews=2)
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert later_writes(ctrl, start) == [] and "pvlan_gate_invocation_releases" not in result


@pytest.mark.parametrize("global_deploy, item_deploy", [(False, False), (True, False)], ids=["all-false", "nac-shape-item-false"])
def test_a_retry_whose_effective_item_deploy_is_false_still_only_saves(global_deploy, item_deploy):
    ctrl = saved_po_ctrl()
    stage(ctrl)
    ctrl.previews = [saved_preview() for _i in range(3)]
    start = len(ctrl.calls)
    status, result = R.with_args(HH, run, ctrl, [{"name": "port-channel301", "switch": [SWITCH_IP], "deploy": item_deploy},
                                                 {"name": "po502", "switch": [SWITCH_IP], "deploy": item_deploy}],
                                 {"deploy": global_deploy}, state="deleted")
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert later_writes(ctrl, start) == [] and ctrl.conv_marked is not None and ctrl.marked is not None
    assert not [r for r in result.get("pvlan_saved") or [] if r.get("kind") == "conventional"]


def test_a_conventional_item_kept_at_deploy_false_is_not_deployed_by_the_pvlan_continuation():
    """Per-item deploy decides: Po301 named with deploy false beside Po502 with deploy true -- Po301 is not taken into the deployment, so
    its saved pending stays unowned and the PVLAN deploy is refused with nothing sent (existing precedence preserved)."""
    ctrl = saved_po_ctrl()
    stage(ctrl)
    status, result, start = retry(ctrl, items=[{"name": "port-channel301", "switch": [SWITCH_IP], "deploy": False},
                                               {"name": "po502", "switch": [SWITCH_IP], "deploy": True}])
    assert status == "fail" and "outside interface scope" in result["msg"], result.get("msg")
    assert "globalInterface/deploy" not in later_writes(ctrl, start)


def test_a_request_that_does_not_name_the_conventional_saved_deletion_does_not_own_it():
    ctrl = saved_po_ctrl()
    stage(ctrl)
    status, result, start = retry(ctrl, items=[{"name": "po502", "switch": [SWITCH_IP], "deploy": True}])
    assert status == "fail" and "outside interface scope" in result["msg"] and "ethernet1/14" in result["msg"], result.get("msg")
    assert "globalInterface/deploy" not in later_writes(ctrl, start)


@pytest.mark.parametrize("extra_global, blocks, needle", [
    (T6_GLOBAL + ["no interface port-channel399"], None, "outside interface scope"),
    (T6_GLOBAL + ["router bgp 65000"], None, "outside interface scope"),
    (["no interface port-channel302"], None, "outside interface scope"),
    (None, released_block(C14, 301) + ["interface ethernet1/30", "  description stray"], "outside this deploy batch: ethernet1/30"),
    (None, released_block(C14, 399), "outside this deploy batch: ethernet1/14"),
], ids=["foreign-aggregate", "foreign-global", "wrong-pcid", "foreign-physical", "member-withdraws-another-id"])
def test_unrelated_or_mismatched_pending_still_refuses_the_continuation(extra_global, blocks, needle):
    ctrl = saved_po_ctrl()
    stage(ctrl)
    status, result, start = retry(ctrl, preview=saved_preview(extra_global, blocks))
    assert status == "fail" and needle in result["msg"], result.get("msg")
    assert "globalInterface/deploy" not in later_writes(ctrl, start)


@pytest.mark.parametrize("running, needle", [
    ([], "does not hold port-channel301 exactly once"),
    (CONV_RUNNING + ["interface ethernet1/15", "  channel-group 301 mode active"], "member Ethernet1/15"),
], ids=["device-no-longer-holds-it", "joined-member-not-released"])
def test_saved_state_the_controller_and_device_do_not_prove_is_refused_before_any_write(running, needle):
    ctrl = saved_po_ctrl()
    stage(ctrl)
    ctrl.detail["Ethernet1/15"] = {"policy": "int_port_channel_trunk_member_11_1", "nvPairs": {"PO_ID": "Port-channel301", "ADMIN_STATE": "true"}}
    status, result, start = retry(ctrl, preview=saved_preview(running=running))
    assert status == "fail" and "saved conventional deletion cannot be completed" in result["msg"] and needle in result["msg"], result.get("msg")
    assert later_writes(ctrl, start) == []


def test_a_po_the_device_holds_in_a_pvlan_mode_is_not_taken_as_a_conventional_sibling():
    """The existing PVLAN continuation claims it (it is a PVLAN Po on the device) and its own gate refuses: nothing is deployed."""
    ctrl = saved_po_ctrl()
    stage(ctrl)
    running = ["interface port-channel301", "  switchport mode private-vlan host", "interface ethernet1/14", "  channel-group 301 mode active"]
    status, result, start = retry(ctrl, preview=saved_preview(running=running))
    assert status == "fail" and not [r for r in result.get("pvlan_saved") or [] if r.get("kind") == "conventional"], result.get("msg")
    assert "globalInterface/deploy" not in later_writes(ctrl, start)


def test_a_marked_listing_owned_by_another_source_is_not_recognised():
    ctrl = saved_po_ctrl()
    stage(ctrl)
    ctrl.conv_marked["underlayPolicies"][0]["source"] = "port-channel399"
    status, result, start = retry(ctrl)
    assert status == "fail" and "outside interface scope" in result["msg"], result.get("msg")
    assert "globalInterface/deploy" not in later_writes(ctrl, start)


def test_an_unreadable_preview_refuses_the_retry_with_nothing_sent():
    ctrl = saved_po_ctrl()
    stage(ctrl)
    ctrl.previews = [{"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}} for _i in range(3)]
    start = len(ctrl.calls)
    status, result = R.with_args(HH, run, ctrl, [{"name": "port-channel301", "switch": [SWITCH_IP], "deploy": True},
                                                 {"name": "po502", "switch": [SWITCH_IP], "deploy": True}], {"deploy": True}, state="deleted")
    assert status == "fail" and later_writes(ctrl, start) == [], result.get("msg")


def test_partial_state_with_only_the_pvlan_deletion_left_is_completed_alone():
    """The conventional deletion is already applied (gone, no pending): only the PVLAN continuation remains and is completed."""
    ctrl = saved_po_ctrl()
    stage(ctrl)
    ctrl.conv_marked = None
    status, result, start = retry(ctrl, preview=saved_preview(extra_global=[], extra_blocks=[], running=[]))
    assert status == "exit" and result["changed"] is True, result.get("msg")
    sent = sorted(i["ifName"].lower() for b in deploy_bodies(ctrl, start) for i in b)
    assert sent == ["port-channel502"] and not [r for r in result["pvlan_saved"] if r.get("kind") == "conventional"]


def test_partial_state_with_only_the_conventional_deletion_left_keeps_the_legacy_generic_path():
    """The PVLAN deletion is already applied: no PVLAN continuation exists on the serial, so nothing here engages; the generic path stays as
    it was (a marked, not In-Sync conventional Po is not deployed by it) and the saved conventional deletion remains for the fabric deploy.
    Documented limitation, unchanged legacy behavior."""
    ctrl = saved_po_ctrl()
    stage(ctrl)
    ctrl.marked = None
    ctrl.policies_extra = []
    status, result, start = retry(ctrl, preview=saved_preview(extra_global=T6_GLOBAL[:1]))
    assert status == "exit" and later_writes(ctrl, start) == [] and ctrl.conv_marked is not None, result.get("msg")
    assert not [r for r in result.get("pvlan_saved") or [] if r.get("kind") == "conventional"]


def test_the_saved_deletion_message_names_only_the_supported_continuations():
    """The user-facing continuation of a saved deletion promises only what the module does (tested above) and names the cases it does
    not complete."""
    ctrl = saved_po_ctrl()
    result = stage(ctrl)
    text = [r for r in result["pvlan_saved"] if r.get("operation") == "delete"][0]["continuation"]
    assert "deploy true naming the same aggregates" in text and "a saved conventional port-channel or vPC deleted with it" in text
    for limit in ("left out of that request", "PVLAN sibling is already deployed", "child port-channel id differs from its vPC id"):
        assert limit in text, limit


class StillListedAfterDeploy(SavedConvController):
    """The controller keeps listing the conventional Po after its deploy (not converged)."""

    def __call__(self, mod, method, path, data=None):
        kept = self.conv_marked
        resp = super(StillListedAfterDeploy, self).__call__(mod, method, path, data)
        if method == "POST" and path.endswith("/rest/globalInterface/deploy"):
            self.conv_marked = kept
        return resp


def test_a_deployed_conventional_deletion_that_does_not_read_back_fails_with_the_observed_state():
    ctrl = saved_po_ctrl()
    stage(ctrl)
    ctrl.__class__ = StillListedAfterDeploy
    status, result, start = retry(ctrl)
    assert status == "fail" and "could not be verified" in result["msg"] and "still listed" in result["msg"], result.get("msg")
    assert later_writes(ctrl, start).count("globalInterface/deploy") == 1, "deployed once; nothing else sent"


def test_fresh_deploy_true_invocation_completes_the_saved_mixed_vpc_deletion_on_both_peers():
    ctrl = saved_vpc_ctrl()
    status, result, start = vpc_retry(ctrl)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.deploys()) == 1 and "interface/markdelete" not in later_writes(ctrl, start)
    sent = sorted((i["serialNumber"], i["ifName"].lower()) for i in json.loads(ctrl.deploys()[0][2]))
    assert sent == [(V.PAIR, "vpc10"), (V.PAIR, "vpc305")]
    assert vpc_owned(result) == [(V.SN1, ("ethernet1/5",), ("no interface port-channel305",)),
                                 (V.SN2, ("ethernet1/6",), ("no interface port-channel305",))]
    assert not [e for s in (V.SN1, V.SN2) for e in ctrl.summary_extra[s] if str(e.get("markDeleted")) == "True"], "both peers clean"
    assert ctrl.nodes[V.SN1]["Ethernet1/5"]["policy"] == V.TRUNK and ctrl.nodes[V.SN2]["Ethernet1/6"]["policy"] == V.TRUNK
    ctrl.next_invocation()
    status, result, start = vpc_retry(ctrl, n=2)
    assert status == "exit" and result["changed"] is False and later_writes(ctrl, start) == [], result.get("msg")


def test_a_peer_whose_device_does_not_hold_the_conventional_child_refuses_with_the_peer_named():
    ctrl = saved_vpc_ctrl()
    status, result, start = vpc_retry(ctrl, running={V.SN2: []})
    assert status == "fail" and "conventional port-channel on peer(s) %s only" % V.SN1 in result["msg"], result.get("msg")
    assert later_writes(ctrl, start) == []


def test_a_failed_peer_read_refuses_with_nothing_sent():
    ctrl = saved_vpc_ctrl()
    queue_vpc(ctrl, 4)
    ctrl.vpc_previews[V.SN2] = [{"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}} for _i in range(4)]
    start = len(ctrl.calls)
    status, result = R.with_args(V, V.run_vpc, ctrl, [{"name": "vpc305", "type": "vpc", "switch": [V.IP1, V.IP2], "deploy": True},
                                                      V.vpc_del_item(deploy=True)], {"deploy": True}, state="deleted")
    assert status == "fail" and later_writes(ctrl, start) == [], result.get("msg")


def test_the_other_peers_member_is_not_owned_on_this_peer():
    ctrl = saved_vpc_ctrl()
    status, result, start = vpc_retry(ctrl, extra={V.SN1: vpc_conv_pending("Ethernet1/6")})
    assert status == "fail" and "peer 1 (%s): pending exists for interfaces outside this deploy batch: ethernet1/6" % V.SN1 in result["msg"], \
        result.get("msg")
    assert "globalInterface/deploy" not in later_writes(ctrl, start)


def test_a_conventional_vpc_marked_on_one_peer_only_is_refused():
    ctrl = saved_vpc_ctrl()
    ctrl.summary_extra[V.SN2] = [e for e in ctrl.summary_extra[V.SN2] if e.get("ifName") != "port-channel305"]
    status, result, start = vpc_retry(ctrl)
    assert status == "fail" and later_writes(ctrl, start) == [], result.get("msg")
