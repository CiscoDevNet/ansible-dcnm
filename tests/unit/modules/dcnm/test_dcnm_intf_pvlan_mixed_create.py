"""A conventional and a PVLAN aggregate CREATED in ONE dcnm_interface call with deploy true.

The conventional member's JOIN (`channel-group <id> force mode active`) appears in the pending that the PVLAN pre-deploy gate
(`deploy`) reads, and must not be refused as "outside this deploy batch".

Rule (same family as the release and deletion rules): a pending interface outside the PVLAN batch is accepted ONLY when THIS
invocation's confirmed write of a CONVENTIONAL aggregate joined it on THAT physical serial (members sent minus the pre-state
members read by this run; all of them for a creation) AND its pending block joins that aggregate's channel-group
(`channel-group <id>[ force][ mode M]`). For a conventional vPC this invocation created, the child `port-channel<id>` of each
peer is that creation's own pending too.

Shapes: the Po case uses a measured pending; the vPC case is SIMULATED with the same member form. Real main() through the
existing harnesses; only the controller boundary is faked.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json

from . import test_dcnm_intf_pvlan_mixed_batch as MB
from . import test_dcnm_intf_pvlan_po_host as PH
from . import test_dcnm_intf_pvlan_vpc_harness as V
from .test_dcnm_intf_pvlan_harness import IF7, IF8, SERIAL, TRUNK, preview, run, trunk_host_nv

CONV_PO, CONV_PO_ITEM = "Port-channel301", "port-channel301"
IF9 = "Ethernet1/9"
PATCH = MB.PATCH


def join_block(member, pcid=301, join=True):
    """The MEASURED pending of a conventional member joined by its new port-channel."""
    lines = ["interface %s" % member.lower(), "  no spanning-tree bpduguard disable", "  no spanning-tree port type edge trunk"]
    if join:
        lines.append("  channel-group %d force mode active" % pcid)
    return lines + ["  no shutdown"]


def conv_po_stanza(pcid=301):
    return ["interface port-channel%d" % pcid, "  switchport", "  switchport mode trunk", "  switchport trunk allowed vlan none", "  mtu 9216",
            "  spanning-tree bpduguard enable", "  spanning-tree port type edge trunk", "  description INTEG-PO-CONV-V2", "  no shutdown"]


# ================================================================== regular port-channels
def po_ctrl(conv_members=(IF8,)):
    ctrl = PH.baseline_ctrl()
    for port in conv_members:
        ctrl.detail[port] = {"policy": TRUNK, "nvPairs": trunk_host_nv(port)}
    return ctrl


def conv_po_item(members=(IF8,), deploy=True):
    return MB.conv_po_item(members=members, deploy=deploy)


def f1_po_call(ctrl, extra_pending, members=(IF8,), conv=None, pvlan_deploy=True, previews=1):
    """F-1: create conventional Po301 + PVLAN po10 in ONE merged call, global and item deploy true."""
    pending = PH.PENDING_NEW + conv_po_stanza() + list(extra_pending)
    ctrl.previews = [preview(pending, running=PH.RUNNING_MEMBER, expected=PH.PO_STANZA + PH.MEMBER_AFTER) for _i in range(previews)]
    return run(ctrl, [conv or conv_po_item(members=members), PH.po_item(deploy=pvlan_deploy)], "merged", patch_version=PATCH)


def deployed_names(ctrl):
    return [sorted(i["ifName"] for i in json.loads(c[2])) for c in ctrl.deploys()]


def test_f1_po_mixed_creation_with_deploy_true_is_deployed_once_and_owns_the_conventional_join():
    ctrl = po_ctrl()
    status, result = f1_po_call(ctrl, join_block(IF8))
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.creates()) == 2, "both aggregates created"
    assert deployed_names(ctrl) == [sorted([CONV_PO, PH.PO])], "one deploy of exactly the two created aggregates"
    assert result["pvlan_gate_invocation_releases"] == [{"site": "deploy", "serial": SERIAL, "interfaces": ["ethernet1/8"]}]


def test_f1_po_with_several_conventional_members_owns_each_join():
    ctrl = po_ctrl(conv_members=(IF8, IF9))
    status, result = f1_po_call(ctrl, join_block(IF8) + join_block(IF9), members=(IF8, IF9))
    assert status == "exit", result.get("msg")
    assert result["pvlan_gate_invocation_releases"][0]["interfaces"] == ["ethernet1/8", "ethernet1/9"]
    assert len(ctrl.deploys()) == 1


def test_unrelated_physical_pending_is_still_refused_with_no_deploy():
    ctrl = po_ctrl()
    status, result = f1_po_call(ctrl, join_block(IF8) + ["interface ethernet1/30", "  description stray"])
    assert status == "fail" and "outside this deploy batch: ethernet1/30" in result["msg"], result.get("msg")
    assert "ethernet1/8" not in result["msg"].split("outside this deploy batch:")[1].split("\n")[0]
    assert ctrl.deploys() == []


def test_unrelated_global_pending_is_still_refused_with_no_deploy():
    ctrl = po_ctrl()
    status, result = f1_po_call(ctrl, join_block(IF8) + ["router bgp 65000"])
    assert status == "fail" and "outside interface scope" in result["msg"] and ctrl.deploys() == [], result.get("msg")


def test_a_join_of_another_port_channel_id_or_without_a_join_stays_foreign():
    for block, why in ((join_block(IF8, pcid=999), "joins another id"), (join_block(IF8, join=False), "no channel-group join")):
        ctrl = po_ctrl()
        status, result = f1_po_call(ctrl, block)
        assert status == "fail" and "outside this deploy batch: ethernet1/8" in result["msg"], (why, result.get("msg"))
        assert ctrl.deploys() == [], why


def test_a_member_the_conventional_creation_did_not_send_stays_foreign():
    """Po301 is created with Eth1/8 only; a join block for Eth1/9 (even with the same id) is not this invocation's operation."""
    ctrl = po_ctrl(conv_members=(IF8, IF9))
    status, result = f1_po_call(ctrl, join_block(IF8) + join_block(IF9))
    assert status == "fail" and "outside this deploy batch: ethernet1/9" in result["msg"], result.get("msg")
    assert ctrl.deploys() == []


class RefusedConventionalCreate(PH.PoController):
    """The conventional creation is answered with an error: the module fails on that answer (existing rule) before any gate."""

    def __call__(self, mod, method, path, data=None):
        if method == "POST" and path.endswith(PH.GLOBAL_IF) and CONV_PO in (data or ""):
            self.calls.append((method, path, data))
            return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {"message": "refused"}}
        return super(RefusedConventionalCreate, self).__call__(mod, method, path, data)


def test_an_unconfirmed_conventional_creation_grants_nothing_and_deploys_nothing():
    ctrl = RefusedConventionalCreate()
    ctrl.detail[IF7] = {"policy": TRUNK, "nvPairs": trunk_host_nv(IF7)}
    ctrl.detail[IF8] = {"policy": TRUNK, "nvPairs": trunk_host_nv(IF8)}
    status, result = f1_po_call(ctrl, join_block(IF8))
    assert status == "fail" and ctrl.deploys() == []
    assert "pvlan_gate_invocation_releases" not in result


def test_saved_mixed_creation_deploy_false_is_unchanged():
    """NaC's shape (item deploy false): nothing previewed, nothing deployed, no ownership needed."""
    ctrl = po_ctrl()
    status, result = f1_po_call(ctrl, join_block(IF8), conv=conv_po_item(deploy=False), pvlan_deploy=False)
    assert status == "exit" and ctrl.deploys() == [], result.get("msg")
    assert "pvlan_gate_invocation_releases" not in result


def test_conventional_member_added_by_an_update_in_the_same_call_is_owned():
    """The update analogue (an open limit of the live run): Po301 [Eth1/14] -> [Eth1/14, Eth1/15] next to a saved PVLAN member removal."""
    ctrl = MB.po_ctrl(conv_members=(MB.C14,))
    status, result = MB.t5_po_call(ctrl, join_block(MB.C15), conv=MB.conv_po_item(members=(MB.C14, MB.C15)))
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert result["pvlan_gate_invocation_releases"] == [{"site": "update_saved", "serial": MB.HH.SERIAL, "interfaces": ["ethernet1/15"]}]


# ================================================================== vPC (simulated)
CONV_VPC, CONV_VPC_ITEM = "vPC305", "vpc305"
V5 = "Ethernet1/5"


def vpc_ctrl():
    ctrl = V.baseline_ctrl()
    for serial in (V.SN1, V.SN2):
        ctrl.nodes[serial][V5] = {"policy": TRUNK, "nvPairs": trunk_host_nv(V5)}
    return ctrl


def conv_vpc_create_item(deploy=True):
    return {"name": CONV_VPC_ITEM, "type": "vpc", "switch": [V.IP1, V.IP2], "deploy": deploy,
            "profile": dict(MB.CONV_VPC_PROFILE, peer1_members=[V5], peer2_members=[V5])}


def conv_child(pcid=305):
    return ["interface port-channel%d" % pcid, "  switchport", "  switchport mode trunk", "  switchport trunk allowed vlan none",
            "  mtu 9216", "  vpc %d" % pcid, "  description INTEG-VPC-CONV-V2", "  no shutdown"]


def f1_vpc_call(ctrl, extra=None):
    extra = extra if extra is not None else {s: conv_child() + join_block(V5, 305) for s in (V.SN1, V.SN2)}
    for serial, port in ((V.SN1, V.M1), (V.SN2, V.M2)):
        pv = V.create_preview(serial, port)
        entry = pv["DATA"][0]
        entry["pendingConfig"] = list(entry["pendingConfig"]) + list(extra.get(serial, []))
        ctrl.vpc_previews[serial] = [pv, copy.deepcopy(V.converged_preview(serial, port))]
    return V.run_vpc(ctrl, [conv_vpc_create_item(), V.vpc_item()], state="merged", patch_version=PATCH)


def vpc_owned(result):
    return sorted((r["serial"], tuple(r["interfaces"])) for r in result.get("pvlan_gate_invocation_releases") or [])


def test_f1_vpc_mixed_creation_owns_each_peers_child_and_join():
    ctrl = vpc_ctrl()
    status, result = f1_vpc_call(ctrl)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert vpc_owned(result) == [(V.SN1, ("ethernet1/5", "port-channel305")), (V.SN2, ("ethernet1/5", "port-channel305"))]
    deploys = [c for c in ctrl.calls if c[0] == "POST" and c[1].endswith(V.DEPLOY)]
    assert len(deploys) == 1 and sorted(i["ifName"] for i in json.loads(deploys[0][2])) == sorted([CONV_VPC, V.VPC])


def test_f1_vpc_child_of_another_id_on_a_peer_stays_foreign():
    ctrl = vpc_ctrl()
    extra = {V.SN1: conv_child() + join_block(V5, 305), V.SN2: conv_child(306) + join_block(V5, 305)}
    status, result = f1_vpc_call(ctrl, extra)
    assert status == "fail" and "outside this deploy batch: port-channel306" in result["msg"], result.get("msg")
    assert not [c for c in ctrl.calls if c[0] == "POST" and c[1].endswith(V.DEPLOY)]


def test_f1_vpc_child_names_are_scoped_per_peer_serial():
    """peer1 child port-channel305, peer2 child port-channel306: a port-channel306 block on PEER 1 is not the creation's (it belongs to
    peer 2's serial only)."""
    ctrl = vpc_ctrl()
    item = conv_vpc_create_item()
    item["profile"] = dict(item["profile"], peer2_pcid=306)
    extra = {V.SN1: conv_child(305) + conv_child(306) + join_block(V5, 305), V.SN2: conv_child(306) + join_block(V5, 306)}
    for serial, port in ((V.SN1, V.M1), (V.SN2, V.M2)):
        pv = V.create_preview(serial, port)
        entry = pv["DATA"][0]
        entry["pendingConfig"] = list(entry["pendingConfig"]) + list(extra[serial])
        ctrl.vpc_previews[serial] = [pv, copy.deepcopy(V.converged_preview(serial, port))]
    status, result = V.run_vpc(ctrl, [item, V.vpc_item()], state="merged", patch_version=PATCH)
    assert status == "fail" and "peer 1" in result["msg"] and "outside this deploy batch: port-channel306" in result["msg"], result.get("msg")
    assert not [c for c in ctrl.calls if c[0] == "POST" and c[1].endswith(V.DEPLOY)]
