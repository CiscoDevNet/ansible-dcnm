"""Conventional and PVLAN aggregates created, modified and deleted in one invocation."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import pytest

from .helpers import ethernet_controller as HH
from .helpers import membership as MU
from .helpers import vpc_controller as V
from .helpers.ethernet_controller import SWITCH_IP
from .helpers.ethernet_controller import run
from .helpers.mixed_controller import released_block
from .helpers import port_channel_controller as PH
from .helpers.ethernet_controller import IF7
from .helpers.ethernet_controller import IF8
from .helpers.ethernet_controller import SERIAL
from .helpers.ethernet_controller import TRUNK
from .helpers.ethernet_controller import preview
from .helpers.ethernet_controller import trunk_host_nv
from .helpers.vpc_controller import _remap_answer
from .helpers import port_channel_release as G4
from .helpers import port_channel_controller as G5
from .helpers import vpc_controller as R
from .helpers.ethernet_controller import ok
from .helpers.mixed_controller import vpc_conv_pending
from .helpers.mixed_controller import C14 as MIXED_DELETE_C14
from .helpers.mixed_controller import T6_GLOBAL
from .helpers.mixed_controller import V5 as MIXED_DELETE_V5
from .helpers.mixed_controller import V6 as MIXED_DELETE_V6
from .helpers.mixed_controller import add_conv_po
from .helpers.mixed_controller import po_preview
from .helpers.mixed_controller import vpc_mixed_ctrl
from .helpers.mixed_controller import CONV_RUNNING
from .helpers.mixed_controller import SavedConvController
from .helpers.mixed_controller import deploy_bodies
from .helpers.mixed_controller import later_writes
from .helpers.mixed_controller import queue_vpc
from .helpers.mixed_controller import retry
from .helpers.mixed_controller import saved_po_ctrl
from .helpers.mixed_controller import saved_preview
from .helpers.mixed_controller import saved_vpc_ctrl
from .helpers.mixed_controller import stage
from .helpers.mixed_controller import vpc_owned as mixed_retry_vpc_owned
from .helpers.mixed_controller import vpc_retry


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_mixed_batch.py
# Conventional and PVLAN member removals in ONE dcnm_interface call.
#
# A single `state: replaced` call, each item deploy false, can release a member of a CONVENTIONAL port-channel / vPC and a member
# of a PVLAN one on the same switch. The PVLAN saved-update gate (`update_saved`) must not refuse the conventional released member
# as "outside this deploy batch".
#
# Rule: a pending interface outside the PVLAN batch is accepted ONLY when this invocation's CONFIRMED update (per-item SUCCESS) of a
# conventional aggregate released it on THAT physical serial (pre-state member list read by this run minus the member list sent) AND
# its pending block withdraws that aggregate's channel-group. Everything else stays refused.
#
# Shapes: measured module arguments and forced-preview pending lines, sanitized. Real main() through the existing Po and vPC
# harnesses; only the controller boundary is faked.
# ====================================================================================================
CONV_PO, CONV_PO_ITEM = "Port-channel301", "port-channel301"
C14, C15 = "Ethernet1/14", "Ethernet1/15"
CONV_PO_POLICY, CONV_MEMBER_POLICY = "int_port_channel_trunk_host", "int_port_channel_trunk_member_11_1"
CONV_VPC, CONV_VPC_ITEM = "vPC305", "vpc305"
V5, V6 = "Ethernet1/5", "Ethernet1/6"
CONV_VPC_POLICY = "int_vpc_trunk_host"
PATCH = "4.3.1.0175006017"  # the measured invocation's patch_version (required by its disable_lldp_* fields)

# Measured module arguments of the conventional items (profile and members as measured).
CONV_PO_PROFILE = {
    "admin_state": True, "allowed_vlans": "none", "bpdu_guard": True, "cmds": "", "copy_description": False, "description": "INTEG-PO-CONV-V2",
    "disable_lacp_suspend_individual": False, "disable_lldp_receive": False, "disable_lldp_transmit": False, "duplex": "auto", "enable_cdp": True,
    "enable_monitor": False, "enable_qos": False, "enable_storm_control": False, "guard_mode": "no", "lacp_port_priority": 32768,
    "lacp_rate": "normal", "members": [C14], "mode": "trunk", "mtu": "jumbo", "native_vlan": "", "pc_mode": "active", "port_type_fast": True,
    "spanning_tree_port_type": "no", "speed": "auto",
}
CONV_VPC_PROFILE = {
    "admin_state": True, "bpdu_guard": True, "copy_description": False, "disable_lacp_suspend_individual": False, "disable_lldp_receive": False,
    "disable_lldp_transmit": False, "enable_cdp": True, "enable_lacp_vpc_convergence": False, "enable_qos": False, "enable_storm_control": False,
    "guard_mode": "no", "lacp_port_priority": 32768, "lacp_rate": "normal", "mode": "trunk", "mtu": "jumbo", "pc_mode": "active",
    "peer1_allowed_vlans": "none", "peer1_cmds": "", "peer1_description": "INTEG-VPC-CONV-V2", "peer1_members": [V5], "peer1_native_vlan": "",
    "peer1_pcid": 305, "peer2_allowed_vlans": "none", "peer2_cmds": "", "peer2_description": "INTEG-VPC-CONV-V2", "peer2_members": [V5],
    "peer2_native_vlan": "", "peer2_pcid": 305, "port_type_fast": True, "spanning_tree_port_type": "no", "speed": "auto",
}


def with_pending(resp, extra):
    entry = resp["DATA"][0]
    entry["pendingConfig"] = list(entry.get("pendingConfig") or []) + list(extra)
    entry["status"] = "Out-of-Sync"
    return resp


# ================================================================== regular port-channels
def po_ctrl(conv_members=(C14, C15)):
    """The PVLAN Po of the membership harness plus a conventional trunk Po301 with its own members on the same switch."""
    ctrl = MU.seeded()
    nv = {"MEMBER_INTERFACES": ",".join(conv_members), "PO_ID": CONV_PO, "PC_MODE": "active", "DESC": "INTEG-PO-CONV-V2", "ADMIN_STATE": "true",
          "ALLOWED_VLANS": "none", "MTU": "jumbo", "SPEED": "Auto", "BPDUGUARD_ENABLED": "true", "PORTTYPE_FAST_ENABLED": "true",
          "CONF": ""}
    ctrl.detail[CONV_PO] = {"policy": CONV_PO_POLICY, "nvPairs": nv}
    ctrl.po_names.add(CONV_PO)
    for port in conv_members:
        ctrl.detail[port] = {"policy": CONV_MEMBER_POLICY, "nvPairs": {"PO_ID": CONV_PO, "ADMIN_STATE": "true", "INTF_NAME": port}}
    return ctrl


def conv_po_item(members=(C14,), deploy=False, **profile):
    prof = dict(CONV_PO_PROFILE, members=list(members))
    prof.update(profile)
    return {"name": CONV_PO_ITEM, "type": "pc", "switch": [SWITCH_IP], "deploy": deploy, "profile": prof}


def t5_po_call(ctrl, extra_pending, conv=None, pvlan_deploy=False):
    """The measured shape on one switch: conventional Po301 releases Eth1/15, PVLAN Po releases E9, both items deploy false, one call."""
    ctrl.previews = [with_pending(MU.fragments(kept=(MU.E7,), removed_trunk=(MU.E9,)), extra_pending)]
    return run(ctrl, [conv or conv_po_item(), MU.item([MU.E7], deploy=pvlan_deploy)], "replaced", patch_version=PATCH)


def test_t5_po_conventional_release_in_the_same_call_is_part_of_the_saved_pvlan_update():
    ctrl = po_ctrl()
    status, result = t5_po_call(ctrl, released_block(C15))
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.deploys() == [], "deploy false: nothing deployed"
    assert result["pvlan_gate_invocation_releases"] == [{"site": "update_saved", "serial": MU.H.SERIAL, "interfaces": ["ethernet1/15"]}]
    assert [s for s in result["pvlan_saved"] if s["operation"] == "remove member"]
    bodies = [b for b in ctrl.modify_bodies() if any(p.get("policy") == CONV_PO_POLICY for p in b)]
    assert len(bodies) == 1, "conventional and PVLAN updates travel in the one bulk modify"


def test_unrelated_physical_pending_is_still_refused_with_no_deploy():
    ctrl = po_ctrl()
    status, result = t5_po_call(ctrl, released_block(C15) + ["interface ethernet1/30", "  description stray"])
    assert status == "fail" and "outside this deploy batch: ethernet1/30" in result["msg"], result.get("msg")
    assert "ethernet1/15" not in result["msg"].split("outside this deploy batch:")[1].split("\n")[0]
    assert ctrl.deploys() == []


def test_unrelated_global_pending_is_still_refused():
    ctrl = po_ctrl()
    status, result = t5_po_call(ctrl, released_block(C15) + ["router bgp 65000"])
    assert status == "fail" and "outside interface scope" in result["msg"] and ctrl.deploys() == [], result.get("msg")


@pytest.mark.parametrize("block, why", [
    (released_block(C15, withdrawal=False), "no channel-group withdrawal in its pending"),
    (released_block(C15, pcid=999), "withdrawal of another port-channel id"),
])
def test_a_released_name_whose_pending_does_not_withdraw_that_channel_group_stays_foreign(block, why):
    ctrl = po_ctrl()
    status, result = t5_po_call(ctrl, block)
    assert status == "fail" and "outside this deploy batch: ethernet1/15" in result["msg"], (why, result.get("msg"))


def test_a_requested_conventional_item_that_releases_nothing_grants_no_ownership():
    """Po301 is in the call but keeps BOTH members (only its description changes): Eth1/15 pending is not this operation's."""
    ctrl = po_ctrl()
    status, result = t5_po_call(ctrl, released_block(C15), conv=conv_po_item(members=(C14, C15), description="INTEG-PO-CONV-V3"))
    assert status == "fail" and "outside this deploy batch: ethernet1/15" in result["msg"], result.get("msg")


def test_an_unconfirmed_conventional_update_grants_no_ownership():
    """A per-item ERROR for Po301 in the bulk modify fails the run (existing batch-error rule) before any gate: nothing is accepted."""
    ctrl = po_ctrl()
    ctrl.modify_responses = [{"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [
        {"reportItemType": "ERROR", "message": "refused", "entity": "%s~%s" % (MU.H.SERIAL, CONV_PO_ITEM)},
        {"reportItemType": "SUCCESS", "message": "Interface updated successfully", "entity": "%s~%s" % (MU.H.SERIAL, MU.H.PO)}]}]
    status, result = t5_po_call(ctrl, released_block(C15))
    assert status == "fail" and "pvlan_gate_invocation_releases" not in result and ctrl.deploys() == [], result.get("msg")


def test_saved_retry_does_not_take_ownership_from_desired_membership_alone(monkeypatch):
    """The measured call saves both removals (fixed). A LATER invocation repeats the same items -- Po301 already holds one member, so nothing is
    updated now -- with deploy true to complete the saved PVLAN removal: the conventional released pending is NOT an operation of this
    invocation (its update ended in the previous process) and still refuses the deploy; desired membership alone grants nothing."""
    ctrl = po_ctrl()
    status, result = t5_po_call(ctrl, released_block(C15))
    assert status == "exit", result.get("msg")
    ctrl.next_invocation()
    monkeypatch.setitem(HH.INVENTORY, SWITCH_IP, dict(HH.INVENTORY[SWITCH_IP], ccStatus="Out-of-Sync"))
    saved = with_pending(MU.fragments(kept=(MU.E7,), removed_trunk=(MU.E9,)), released_block(C15))
    ctrl.previews = [copy.deepcopy(saved) for _i in range(3)]
    status, result = run(ctrl, [conv_po_item(), MU.item([MU.E7], deploy=True)], "replaced", patch_version=PATCH)
    assert status == "fail" and "outside this deploy batch: ethernet1/15" in result["msg"] and ctrl.deploys() == [], result.get("msg")
    assert "pvlan_gate_invocation_releases" not in result


def test_pure_pvlan_saved_removal_is_unchanged():
    ctrl = MU.seeded()
    ctrl.previews = [MU.fragments(kept=(MU.E7,), removed_trunk=(MU.E9,))]
    status, result = run(ctrl, [MU.item([MU.E7], deploy=False)], "replaced", patch_version=PATCH)
    assert status == "exit" and ctrl.deploys() == [] and "pvlan_gate_invocation_releases" not in result, result.get("msg")


def test_conventional_only_member_removal_makes_no_pvlan_reads():
    ctrl = po_ctrl()
    status, result = run(ctrl, [conv_po_item()], "replaced", patch_version=PATCH)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.previews == [] and not [c for c in ctrl.calls if "config-preview" in c[1]] and "pvlan_gate" not in result


# ================================================================== vPC
def vpc_ctrl():
    """The PVLAN vPC10 membership harness (peer1 M1 + E9P removed, peer2 M2) plus a conventional trunk vPC305 with Eth1/5-6 on BOTH peers."""
    ctrl = MU.vpc_seeded({V.SN1: [V.M1, MU.E9P], V.SN2: [V.M2]})
    ctrl.parents[CONV_VPC] = {"policy": CONV_VPC_POLICY, "nvPairs": {
        "PEER1_MEMBER_INTERFACES": "%s,%s" % (V5, V6), "PEER2_MEMBER_INTERFACES": "%s,%s" % (V5, V6), "PEER1_PCID": "305", "PEER2_PCID": "305",
        "PC_MODE": "active", "ADMIN_STATE": "true", "PEER1_PO_DESC": "INTEG-VPC-CONV-V2", "PEER2_PO_DESC": "INTEG-VPC-CONV-V2",
        "PEER1_PO_CONF": "", "PEER2_PO_CONF": ""}}
    return ctrl


def conv_vpc_item(peer1=(V5,), peer2=(V5,), deploy=False):
    return {"name": CONV_VPC_ITEM, "type": "vpc", "switch": [V.IP1, V.IP2], "deploy": deploy,
            "profile": dict(CONV_VPC_PROFILE, peer1_members=list(peer1), peer2_members=list(peer2))}


def t5_vpc_call(ctrl, extra=None, conv=None):
    """PVLAN vPC10 releases E9P on peer 1 only; conventional vPC305 releases Eth1/6 on both peers; one call, items deploy false."""
    extra = extra if extra is not None else {V.SN1: released_block(V6, 305), V.SN2: released_block(V6, 305)}
    MU.queue_peer(ctrl, V.SN1, kept=(V.M1,), removed_trunk=(MU.E9P,))
    MU.queue_peer(ctrl, V.SN2, kept=(V.M2,))
    for serial in (V.SN1, V.SN2):
        ctrl.vpc_previews[serial] = [with_pending(p, extra.get(serial, [])) if extra.get(serial) else p for p in ctrl.vpc_previews[serial][1:]]
    item = V.vpc_item(peer1_members=[V.M1], peer2_members=[V.M2])
    return V.run_vpc(ctrl, [conv or conv_vpc_item(), dict(item, deploy=False)], state="replaced", patch_version=PATCH)


def test_t5_vpc_conventional_release_on_both_peers_is_part_of_the_saved_pvlan_update():
    ctrl = vpc_ctrl()
    status, result = t5_vpc_call(ctrl)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert "DEPLOY" not in ctrl.order()
    owned = sorted(set((r["serial"], tuple(r["interfaces"])) for r in result["pvlan_gate_invocation_releases"]))
    assert owned == [(V.SN1, ("ethernet1/6",)), (V.SN2, ("ethernet1/6",))], "each peer's own Eth1/6, judged per physical serial"


def test_vpc_names_are_not_interchangeable_across_peer_serials():
    """vPC305 releases Eth1/6 on peer 2 only; an Eth1/6 pending on peer 1 is NOT that release and stays foreign."""
    ctrl = vpc_ctrl()
    status, result = t5_vpc_call(ctrl, conv=conv_vpc_item(peer1=(V5, V6), peer2=(V5,)))
    assert status == "fail" and "peer 1 (%s): pending exists for interfaces outside this deploy batch: ethernet1/6" % V.SN1 in result["msg"], result.get("msg")
    assert "DEPLOY" not in ctrl.order()


def test_vpc_unrelated_pending_on_a_peer_is_still_refused():
    ctrl = vpc_ctrl()
    stray = ["interface ethernet1/30", "  description stray"]
    status, result = t5_vpc_call(ctrl, extra={V.SN1: released_block(V6, 305), V.SN2: released_block(V6, 305) + stray})
    assert status == "fail" and "outside this deploy batch: ethernet1/30" in result["msg"] and "DEPLOY" not in ctrl.order(), result.get("msg")


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_mixed_create.py
# A conventional and a PVLAN aggregate CREATED in ONE dcnm_interface call with deploy true.
#
# The conventional member's JOIN (`channel-group <id> force mode active`) appears in the pending that the PVLAN pre-deploy gate
# (`deploy`) reads, and must not be refused as "outside this deploy batch".
#
# Rule (same family as the release and deletion rules): a pending interface outside the PVLAN batch is accepted ONLY when THIS
# invocation's confirmed write of a CONVENTIONAL aggregate joined it on THAT physical serial (members sent minus the pre-state
# members read by this run; all of them for a creation) AND its pending block joins that aggregate's channel-group
# (`channel-group <id>[ force][ mode M]`). For a conventional vPC this invocation created, the child `port-channel<id>` of each
# peer is that creation's own pending too.
#
# Shapes: the Po case uses a measured pending; the vPC case is SIMULATED with the same member form. Real main() through the
# existing harnesses; only the controller boundary is faked.
# ====================================================================================================
IF9 = "Ethernet1/9"
MIXED_CREATE_PATCH = PATCH


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
def mixed_create_po_ctrl(conv_members=(IF8,)):
    ctrl = PH.baseline_ctrl()
    for port in conv_members:
        ctrl.detail[port] = {"policy": TRUNK, "nvPairs": trunk_host_nv(port)}
    return ctrl


def mixed_create_conv_po_item(members=(IF8,), deploy=True):
    return conv_po_item(members=members, deploy=deploy)


def f1_po_call(ctrl, extra_pending, members=(IF8,), conv=None, pvlan_deploy=True, previews=1):
    """F-1: create conventional Po301 + PVLAN po10 in ONE merged call, global and item deploy true."""
    pending = PH.PENDING_NEW + conv_po_stanza() + list(extra_pending)
    ctrl.previews = [preview(pending, running=PH.RUNNING_MEMBER, expected=PH.PO_STANZA + PH.MEMBER_AFTER) for _i in range(previews)]
    return run(ctrl, [conv or mixed_create_conv_po_item(members=members), PH.po_item(deploy=pvlan_deploy)], "merged", patch_version=MIXED_CREATE_PATCH)


def deployed_names(ctrl):
    return [sorted(i["ifName"] for i in json.loads(c[2])) for c in ctrl.deploys()]


def test_f1_po_mixed_creation_with_deploy_true_is_deployed_once_and_owns_the_conventional_join():
    ctrl = mixed_create_po_ctrl()
    status, result = f1_po_call(ctrl, join_block(IF8))
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.creates()) == 2, "both aggregates created"
    assert deployed_names(ctrl) == [sorted([CONV_PO, PH.PO])], "one deploy of exactly the two created aggregates"
    assert result["pvlan_gate_invocation_releases"] == [{"site": "deploy", "serial": SERIAL, "interfaces": ["ethernet1/8"]}]


def test_f1_po_with_several_conventional_members_owns_each_join():
    ctrl = mixed_create_po_ctrl(conv_members=(IF8, IF9))
    status, result = f1_po_call(ctrl, join_block(IF8) + join_block(IF9), members=(IF8, IF9))
    assert status == "exit", result.get("msg")
    assert result["pvlan_gate_invocation_releases"][0]["interfaces"] == ["ethernet1/8", "ethernet1/9"]
    assert len(ctrl.deploys()) == 1


def test_unrelated_physical_pending_is_still_refused_with_no_deploy_mixed_create():
    ctrl = mixed_create_po_ctrl()
    status, result = f1_po_call(ctrl, join_block(IF8) + ["interface ethernet1/30", "  description stray"])
    assert status == "fail" and "outside this deploy batch: ethernet1/30" in result["msg"], result.get("msg")
    assert "ethernet1/8" not in result["msg"].split("outside this deploy batch:")[1].split("\n")[0]
    assert ctrl.deploys() == []


def test_unrelated_global_pending_is_still_refused_with_no_deploy():
    ctrl = mixed_create_po_ctrl()
    status, result = f1_po_call(ctrl, join_block(IF8) + ["router bgp 65000"])
    assert status == "fail" and "outside interface scope" in result["msg"] and ctrl.deploys() == [], result.get("msg")


def test_a_join_of_another_port_channel_id_or_without_a_join_stays_foreign():
    for block, why in ((join_block(IF8, pcid=999), "joins another id"), (join_block(IF8, join=False), "no channel-group join")):
        ctrl = mixed_create_po_ctrl()
        status, result = f1_po_call(ctrl, block)
        assert status == "fail" and "outside this deploy batch: ethernet1/8" in result["msg"], (why, result.get("msg"))
        assert ctrl.deploys() == [], why


def test_a_member_the_conventional_creation_did_not_send_stays_foreign():
    """Po301 is created with Eth1/8 only; a join block for Eth1/9 (even with the same id) is not this invocation's operation."""
    ctrl = mixed_create_po_ctrl(conv_members=(IF8, IF9))
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
    ctrl = mixed_create_po_ctrl()
    status, result = f1_po_call(ctrl, join_block(IF8), conv=mixed_create_conv_po_item(deploy=False), pvlan_deploy=False)
    assert status == "exit" and ctrl.deploys() == [], result.get("msg")
    assert "pvlan_gate_invocation_releases" not in result


def test_conventional_member_added_by_an_update_in_the_same_call_is_owned():
    """The update analogue (an open limit of the live run): Po301 [Eth1/14] -> [Eth1/14, Eth1/15] next to a saved PVLAN member removal."""
    ctrl = po_ctrl(conv_members=(C14,))
    status, result = t5_po_call(ctrl, join_block(C15), conv=conv_po_item(members=(C14, C15)))
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert result["pvlan_gate_invocation_releases"] == [{"site": "update_saved", "serial": HH.SERIAL, "interfaces": ["ethernet1/15"]}]


MIXED_CREATE_V5 = "Ethernet1/5"


def mixed_create_vpc_ctrl():
    ctrl = V.baseline_ctrl()
    for serial in (V.SN1, V.SN2):
        ctrl.nodes[serial][MIXED_CREATE_V5] = {"policy": TRUNK, "nvPairs": trunk_host_nv(MIXED_CREATE_V5)}
    return ctrl


def conv_vpc_create_item(deploy=True):
    return {"name": CONV_VPC_ITEM, "type": "vpc", "switch": [V.IP1, V.IP2], "deploy": deploy,
            "profile": dict(CONV_VPC_PROFILE, peer1_members=[MIXED_CREATE_V5], peer2_members=[MIXED_CREATE_V5])}


def conv_child(pcid=305):
    return ["interface port-channel%d" % pcid, "  switchport", "  switchport mode trunk", "  switchport trunk allowed vlan none",
            "  mtu 9216", "  vpc %d" % pcid, "  description INTEG-VPC-CONV-V2", "  no shutdown"]


def f1_vpc_call(ctrl, extra=None):
    extra = extra if extra is not None else {s: conv_child() + join_block(MIXED_CREATE_V5, 305) for s in (V.SN1, V.SN2)}
    for serial, port in ((V.SN1, V.M1), (V.SN2, V.M2)):
        pv = V.create_preview(serial, port)
        entry = pv["DATA"][0]
        entry["pendingConfig"] = list(entry["pendingConfig"]) + list(extra.get(serial, []))
        ctrl.vpc_previews[serial] = [pv, copy.deepcopy(V.converged_preview(serial, port))]
    return V.run_vpc(ctrl, [conv_vpc_create_item(), V.vpc_item()], state="merged", patch_version=MIXED_CREATE_PATCH)


def vpc_owned(result):
    return sorted((r["serial"], tuple(r["interfaces"])) for r in result.get("pvlan_gate_invocation_releases") or [])


def test_f1_vpc_mixed_creation_owns_each_peers_child_and_join():
    ctrl = mixed_create_vpc_ctrl()
    status, result = f1_vpc_call(ctrl)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert vpc_owned(result) == [(V.SN1, ("ethernet1/5", "port-channel305")), (V.SN2, ("ethernet1/5", "port-channel305"))]
    deploys = [c for c in ctrl.calls if c[0] == "POST" and c[1].endswith(V.DEPLOY)]
    assert len(deploys) == 1 and sorted(i["ifName"] for i in json.loads(deploys[0][2])) == sorted([CONV_VPC, V.VPC])


def test_f1_vpc_child_of_another_id_on_a_peer_stays_foreign():
    ctrl = mixed_create_vpc_ctrl()
    extra = {V.SN1: conv_child() + join_block(MIXED_CREATE_V5, 305), V.SN2: conv_child(306) + join_block(MIXED_CREATE_V5, 305)}
    status, result = f1_vpc_call(ctrl, extra)
    assert status == "fail" and "outside this deploy batch: port-channel306" in result["msg"], result.get("msg")
    assert not [c for c in ctrl.calls if c[0] == "POST" and c[1].endswith(V.DEPLOY)]


def test_f1_vpc_child_names_are_scoped_per_peer_serial():
    """peer1 child port-channel305, peer2 child port-channel306: a port-channel306 block on PEER 1 is not the creation's (it belongs to
    peer 2's serial only)."""
    ctrl = mixed_create_vpc_ctrl()
    item = conv_vpc_create_item()
    item["profile"] = dict(item["profile"], peer2_pcid=306)
    extra = {V.SN1: conv_child(305) + conv_child(306) + join_block(MIXED_CREATE_V5, 305), V.SN2: conv_child(306) + join_block(MIXED_CREATE_V5, 306)}
    for serial, port in ((V.SN1, V.M1), (V.SN2, V.M2)):
        pv = V.create_preview(serial, port)
        entry = pv["DATA"][0]
        entry["pendingConfig"] = list(entry["pendingConfig"]) + list(extra[serial])
        ctrl.vpc_previews[serial] = [pv, copy.deepcopy(V.converged_preview(serial, port))]
    status, result = V.run_vpc(ctrl, [item, V.vpc_item()], state="merged", patch_version=MIXED_CREATE_PATCH)
    assert status == "fail" and "peer 1" in result["msg"] and "outside this deploy batch: port-channel306" in result["msg"], result.get("msg")
    assert not [c for c in ctrl.calls if c[0] == "POST" and c[1].endswith(V.DEPLOY)]


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_mixed_create_child_ids.py
# Interaction of two independent changes (mixed creation x vPC child ids): a conventional vPC and a PVLAN vPC whose peers use port-channel
# numbers different from the vPC id, created in ONE call with deploy true. The PVLAN part is judged with each peer's own Po (11 / 12); the conventional
# child ownership still comes from the conventional vPC's own PEERn_PCID. NOT LIVE TESTED.
# ====================================================================================================
def _call(extra):
    ctrl = mixed_create_vpc_ctrl()
    for serial, port, pcid in ((V.SN1, V.M1, "11"), (V.SN2, V.M2, "12")):
        pv = _remap_answer(V.create_preview(serial, port), pcid)
        entry = pv["DATA"][0]
        entry["pendingConfig"] = list(entry["pendingConfig"]) + list(extra.get(serial, []))
        ctrl.vpc_previews[serial] = [pv, copy.deepcopy(_remap_answer(V.converged_preview(serial, port), pcid))]
    return ctrl, V.run_vpc(ctrl, [conv_vpc_create_item(), V.vpc_item(peer1_pcid=11, peer2_pcid=12)], state="merged", patch_version=MIXED_CREATE_PATCH)


def test_mixed_vpc_creation_with_a_pvlan_vpc_of_other_port_channel_numbers_is_deployed_once_and_owns_only_the_conventional_pieces():
    extra = {s: conv_child() + join_block(MIXED_CREATE_V5, 305) for s in (V.SN1, V.SN2)}
    ctrl, (status, result) = _call(extra)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert vpc_owned(result) == [(V.SN1, ("ethernet1/5", "port-channel305")), (V.SN2, ("ethernet1/5", "port-channel305"))]
    deploys = [c for c in ctrl.calls if c[0] == "POST" and c[1].endswith(V.DEPLOY)]
    assert len(deploys) == 1 and sorted(i["ifName"] for i in json.loads(deploys[0][2])) == sorted(["vPC305", V.VPC])
    assert "port-channel11" in ctrl.nodes[V.SN1] and "port-channel12" in ctrl.nodes[V.SN2] and "port-channel10" not in ctrl.nodes[V.SN1]


def test_a_pending_child_of_the_pvlan_vpcs_number_on_the_wrong_peer_is_not_granted_by_the_conventional_creation():
    # the conventional creation owns port-channel305 only; a stray port-channel12 block on peer 1 is nobody's pending in this batch
    extra = {V.SN1: conv_child() + join_block(MIXED_CREATE_V5, 305) + conv_child(12), V.SN2: conv_child() + join_block(MIXED_CREATE_V5, 305)}
    ctrl, (status, result) = _call(extra)
    assert status == "fail" and "outside this deploy batch" in result["msg"], result.get("msg")
    assert not [c for c in ctrl.calls if c[0] == "POST" and c[1].endswith(V.DEPLOY)]


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_mixed_delete.py
# Conventional and PVLAN aggregate DELETIONS in ONE dcnm_interface call.
#
# A single `state: deleted` call, each item deploy false, can delete a conventional port-channel and a PVLAN one. The PVLAN
# saved-deletion gate (`delete_saved`) then reads a pending that also holds the conventional `no interface port-channel<id>` and
# its released member, and must not refuse them.
#
# Rule: a conventional port-channel / vPC whose generic mark-delete THIS invocation sent, and whose ORIGINAL answer is the
# measured success naming exactly the requested items, leaves on each physical serial (vPC: both child port-channels, PEERn ->
# n-th serial) exactly (a) the global line `no interface port-channel<its id>` and (b) its pre-state members, each judged by the
# existing rule (the block must withdraw that channel-group). Any other global line, interface, id or serial stays refused; an
# unconfirmed answer grants nothing; nothing survives the invocation.
#
# Shapes: a measured forced-preview pending on the measured deletion harness; the vPC on the existing vPC deletion harness. Real
# main(); only the controller boundary is faked.
# ====================================================================================================
def hr_mixed_ctrl(cls=None):
    ctrl = add_conv_po(R.measured_po(G5.hr_ctrl([])))
    if cls is not None:
        ctrl.__class__ = cls
    return ctrl


def t6_po(ctrl, extra_global=None, extra_blocks=None, deploy=False, previews=1):
    """The measured shape on one switch: deleted, conventional Po301 and PVLAN Po502 (harness name of Po310), both deploy false, one call."""
    extra_global = T6_GLOBAL if extra_global is None else extra_global
    extra_blocks = released_block(MIXED_DELETE_C14, 301) if extra_blocks is None else extra_blocks
    ctrl.previews = [po_preview(extra_global, extra_blocks) for _i in range(previews)]
    return run(ctrl, [{"name": "port-channel301", "switch": [SWITCH_IP], "deploy": deploy},
                      {"name": "po502", "switch": [SWITCH_IP], "deploy": deploy}], state="deleted")


def writes(ctrl, start=0):
    return R.writes(type("C", (), {"calls": ctrl.calls[start:]}))


# ================================================================== regular port-channels
def test_t6_conventional_deletion_in_the_same_call_owns_its_withdrawal_and_released_member():
    ctrl = hr_mixed_ctrl()
    status, result = t6_po(ctrl)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert writes(ctrl) == ["interface/markdelete", "interface/markdelete", "interface/modify"], "PVLAN, then conventional; no deploy"
    assert result["pvlan_gate_invocation_releases"] == [
        {"site": "delete_saved", "serial": SERIAL, "interfaces": ["ethernet1/14"], "withdrawn": ["no interface port-channel301"]}]
    assert [g["site"] for g in result["pvlan_gate"]] == ["delete_saved"]
    assert "NOT deployed" in result["pvlan_saved"][0]["state"]


@pytest.mark.parametrize("extra_global, needle", [
    (T6_GLOBAL + ["no interface port-channel399"], "outside interface scope"),
    (T6_GLOBAL + ["router bgp 65000"], "outside interface scope"),
    (["no interface port-channel302"], "outside interface scope"),
], ids=["foreign-no-interface", "foreign-global", "wrong-port-channel-id"])
def test_other_global_pending_is_still_refused_with_no_deploy(extra_global, needle):
    ctrl = hr_mixed_ctrl()
    status, result = t6_po(ctrl, extra_global=extra_global)
    assert status == "fail" and needle in result["msg"] and "ALREADY changed" in result["msg"], result.get("msg")
    assert "globalInterface/deploy" not in writes(ctrl)


@pytest.mark.parametrize("blocks, foreign", [
    (released_block(MIXED_DELETE_C14, 301) + ["interface ethernet1/30", "  description stray"], "ethernet1/30"),
    (released_block(MIXED_DELETE_C14, 399), "ethernet1/14"),
    (released_block(MIXED_DELETE_C14, 301, withdrawal=False), "ethernet1/14"),
], ids=["foreign-interface", "member-withdraws-another-id", "member-without-withdrawal"])
def test_other_interface_pending_is_still_refused_with_no_deploy(blocks, foreign):
    ctrl = hr_mixed_ctrl()
    status, result = t6_po(ctrl, extra_blocks=blocks)
    assert status == "fail" and "outside this deploy batch: %s" % foreign in result["msg"], result.get("msg")
    assert "globalInterface/deploy" not in writes(ctrl)


class AmbiguousConventionalMarkdelete(G5.DeployedReleaseController):
    """The conventional Po's mark-delete answers 200/OK but its outcome does not name the requested item (UNVERIFIED)."""

    def __call__(self, mod, method, path, data=None):
        resp = super(AmbiguousConventionalMarkdelete, self).__call__(mod, method, path, data)
        if method == "DELETE" and path.endswith("/rest/interface/markdelete") and "port-channel301" in str(data).lower():
            return ok({"message": "Interface deleted successfully", "value": []})
        return resp


class FailedThenRetriedConventionalMarkdelete(G5.DeployedReleaseController):
    """The conventional Po's first mark-delete answers 500 (the generic path retries it and the retry succeeds)."""

    def __call__(self, mod, method, path, data=None):
        resp = super(FailedThenRetriedConventionalMarkdelete, self).__call__(mod, method, path, data)
        if method == "DELETE" and path.endswith("/rest/interface/markdelete") and "port-channel301" in str(data).lower():
            if not getattr(self, "failed_once", False):
                self.failed_once = True
                return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": [{"message": "transient"}]}
        return resp


@pytest.mark.parametrize("cls", [AmbiguousConventionalMarkdelete, FailedThenRetriedConventionalMarkdelete], ids=["ambiguous", "retried"])
def test_an_unverified_conventional_markdelete_grants_no_ownership(cls):
    ctrl = hr_mixed_ctrl(cls)
    status, result = t6_po(ctrl)
    assert status == "fail" and "pvlan_gate_invocation_releases" not in result, result.get("msg")
    assert "outside interface scope" in result["msg"] and "globalInterface/deploy" not in writes(ctrl)


def test_unchanged_retry_after_the_saved_deletion_writes_nothing_and_owns_nothing():
    ctrl = hr_mixed_ctrl()
    status, result = t6_po(ctrl)
    assert status == "exit", result.get("msg")
    ctrl.next_invocation()
    start = len(ctrl.calls)
    ctrl.previews = [po_preview(T6_GLOBAL, released_block(MIXED_DELETE_C14, 301))]
    status, result = run(ctrl, [{"name": "port-channel301", "switch": [SWITCH_IP], "deploy": False},
                                {"name": "po502", "switch": [SWITCH_IP], "deploy": False}], state="deleted")
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert writes(ctrl, start) == [] and "pvlan_gate_invocation_releases" not in result
    assert "awaiting deployment" in result["pvlan_saved"][0]["state"]


def test_a_later_deploy_true_continuation_does_not_inherit_the_previous_invocations_ownership():
    """A LATER process with deploy true, on a controller that does NOT list Po301 in the marked-for-deletion form (this harness drops it at
    the mark-delete) while its withdrawal and released member are still pending: nothing in the current controller state proves that
    saved deletion, so it is not this invocation's operation and the gate refuses with nothing deployed. Ownership is never inherited
    from the previous process. The positive continuation backed by the controller's marked listing is in
    test_pvlan_mixed_batches.py."""
    ctrl = hr_mixed_ctrl()
    status, result = t6_po(ctrl)
    assert status == "exit", result.get("msg")
    ctrl.next_invocation()
    start = len(ctrl.calls)
    ctrl.previews = [po_preview(T6_GLOBAL, released_block(MIXED_DELETE_C14, 301)) for _i in range(2)]
    status, result = run(ctrl, [{"name": "port-channel301", "switch": [SWITCH_IP], "deploy": True},
                                {"name": "po502", "switch": [SWITCH_IP], "deploy": True}], state="deleted")
    assert status == "fail" and "outside interface scope" in result["msg"], result.get("msg")
    assert "globalInterface/deploy" not in writes(ctrl, start) and "pvlan_gate_invocation_releases" not in result


def test_an_immediate_mixed_deletion_deploys_once_with_the_same_ownership():
    ctrl = hr_mixed_ctrl()
    status, result = t6_po(ctrl, deploy=True, previews=3)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert writes(ctrl).count("globalInterface/deploy") == 1
    assert [r["site"] for r in result["pvlan_gate_invocation_releases"]] == ["delete_deploy"]
    assert result["pvlan_gate_invocation_releases"][0]["withdrawn"] == ["no interface port-channel301"]


def test_conventional_only_deletion_makes_no_pvlan_reads():
    ctrl = hr_mixed_ctrl()
    status, result = run(ctrl, [{"name": "port-channel301", "switch": [SWITCH_IP], "deploy": False}], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert not [c for c in ctrl.calls if "config-preview" in c[1]] and "pvlan_gate" not in result


def test_pure_pvlan_saved_deletion_is_unchanged():
    ctrl = R.measured_po(G5.hr_ctrl([G5.corrected_hr_preview()]))
    status, result = run(ctrl, [{"name": "po502", "switch": [SWITCH_IP], "deploy": False}], state="deleted")
    assert status == "exit" and writes(ctrl) == ["interface/markdelete", "interface/modify"], result.get("msg")
    assert "pvlan_gate_invocation_releases" not in result


# ------------------------------------------------------------------ overridden (shared deletion path)
def test_overridden_that_drops_a_conventional_and_a_pvlan_port_channel_owns_the_conventional_pending():
    """The sweep deletes both through the SAME generic / PVLAN deletion paths: the same accounting applies (no new target scope)."""
    ctrl = add_conv_po(R.measured_po(G4.owned_ctrl()))
    ctrl.previews = [po_preview(T6_GLOBAL, released_block(MIXED_DELETE_C14, 301), base=G4.entry("H1-verify"))]
    status, result = run(ctrl, [R.lo(SWITCH_IP, deploy=False)], state="overridden")
    assert status == "exit", result.get("msg")
    assert writes(ctrl).count("interface/markdelete") == 2
    assert [(r["interfaces"], r["withdrawn"]) for r in result["pvlan_gate_invocation_releases"]] == [
        (["ethernet1/14"], ["no interface port-channel301"])]


def test_overridden_without_the_conventional_deletion_still_refuses_its_pending():
    """The same pending, but this call deletes no conventional Po (none is on the switch): nothing owns it."""
    ctrl = R.measured_po(G4.owned_ctrl())
    ctrl.previews = [po_preview(T6_GLOBAL, released_block(MIXED_DELETE_C14, 301), base=G4.entry("H1-verify"))]
    status, result = run(ctrl, [R.lo(SWITCH_IP, deploy=False)], state="overridden")
    assert status == "fail" and "outside interface scope" in result["msg"], result.get("msg")


def t6_vpc(ctrl, extra=None, deploy=False):
    extra = extra if extra is not None else {V.SN1: vpc_conv_pending(MIXED_DELETE_V5), V.SN2: vpc_conv_pending(MIXED_DELETE_V6)}
    for serial, port in ((V.SN1, V.M1), (V.SN2, V.M2)):
        p = V.delete_preview(serial, port)
        p["DATA"][0]["pendingConfig"] = list(p["DATA"][0]["pendingConfig"]) + list(extra.get(serial, []))
        ctrl.vpc_previews[serial] = [p]
    return V.run_vpc(ctrl, [{"name": "vpc305", "type": "vpc", "switch": [V.IP1, V.IP2], "deploy": deploy}, V.vpc_del_item(deploy=deploy)],
                     state="deleted")


def owned(result):
    return sorted(set((r["serial"], tuple(r["interfaces"]), tuple(r.get("withdrawn") or ())) for r in result.get("pvlan_gate_invocation_releases") or []))


def test_t6_vpc_mixed_deletion_owns_each_peers_own_child_withdrawal_and_member():
    ctrl = vpc_mixed_ctrl()
    status, result = t6_vpc(ctrl)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.markdeletes()) == 2 and ctrl.deploys() == []
    assert owned(result) == [(V.SN1, ("ethernet1/5",), ("no interface port-channel305",)),
                             (V.SN2, ("ethernet1/6",), ("no interface port-channel305",))]


def test_vpc_member_names_are_not_interchangeable_across_peer_serials():
    ctrl = vpc_mixed_ctrl()
    status, result = t6_vpc(ctrl, extra={V.SN1: vpc_conv_pending(MIXED_DELETE_V6), V.SN2: vpc_conv_pending(MIXED_DELETE_V6)})
    assert status == "fail" and "peer 1 (%s): pending exists for interfaces outside this deploy batch: ethernet1/6" % V.SN1 in result["msg"], \
        result.get("msg")
    assert ctrl.deploys() == []


def test_vpc_withdrawal_of_another_child_id_is_refused():
    ctrl = vpc_mixed_ctrl()
    status, result = t6_vpc(ctrl, extra={V.SN1: vpc_conv_pending(MIXED_DELETE_V5, 306), V.SN2: vpc_conv_pending(MIXED_DELETE_V6)})
    assert status == "fail" and "peer 1 (%s): pending carries commands outside interface scope" % V.SN1 in result["msg"], result.get("msg")


def test_a_peer_whose_child_identity_is_unknown_is_not_authorised_by_the_other_peer():
    """PEER2_PCID unknown in the pre-state: peer 1 is owned, peer 2's withdrawal and member stay foreign."""
    ctrl = vpc_mixed_ctrl(pcids=("305", ""))
    status, result = t6_vpc(ctrl)
    assert status == "fail" and "peer 2 (%s)" % V.SN2 in result["msg"] and "peer 1 (%s): pending" % V.SN1 not in result["msg"], result.get("msg")
    assert ctrl.deploys() == []


class UnverifiedConventionalVpcMarkdelete(R.MeasuredVpc):
    """The conventional vPC's mark-delete answers 200/OK without naming it; the PVLAN vPC keeps the default measured answer."""

    def __call__(self, mod, method, path, data=None):
        resp = super(UnverifiedConventionalVpcMarkdelete, self).__call__(mod, method, path, data)
        if method == "DELETE" and path.endswith(V.MARKDELETE) and "vpc305" in str(data).lower():
            return ok({"message": "Interface deleted successfully", "value": []})
        return resp


def test_an_unverified_conventional_vpc_markdelete_grants_no_ownership():
    ctrl = vpc_mixed_ctrl()
    ctrl.__class__ = UnverifiedConventionalVpcMarkdelete
    status, result = t6_vpc(ctrl)
    assert len(ctrl.markdeletes()) == 2
    assert status == "fail" and "pvlan_gate_invocation_releases" not in result and ctrl.deploys() == [], result.get("msg")


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_mixed_modify.py
# Conventional interfaces MODIFIED in the same dcnm_interface call as a saved PVLAN membership removal.
#
# A single `replaced` call, every item deploy false, can remove members of a PVLAN and of a conventional aggregate AND change
# other interfaces on the same switches. The PVLAN `update_saved` gate must not refuse those changes as "outside this deploy
# batch".
#
# Rule: a pending interface outside the PVLAN batch is accepted when THIS invocation's confirmed bulk update (the payload actually
# sent and a per-item SUCCESS naming it) modified it on THAT physical serial: the interface itself (Ethernet, loopback,
# port-channel, SVI ...) or, for a conventional vPC, each peer's child `port-channel<PEERn_PCID>` on that peer. Anything only
# desired, not sent, not confirmed, on another serial or another port-channel id, and every global line, stays refused.
#
# Real main() through the existing mixed-batch Po and vPC harnesses; only the controller boundary is faked.
# ====================================================================================================
LO, LO_ITEM, LO_POLICY = "Loopback391", "loopback391", "int_loopback"
PO_BLOCK = ["interface port-channel301", "  description INTEG-PO-CONV-V2"]
LO_BLOCK = ["interface loopback391", "  description INTEG-LO-V2"]


def lo_item(description="INTEG-LO-V2", deploy=False):
    return {"name": LO_ITEM, "type": "lo", "switch": [SWITCH_IP], "deploy": deploy,
            "profile": {"mode": "lo", "int_vrf": "", "ipv4_addr": "192.0.2.91", "description": description, "admin_state": True}}


def seed_lo(ctrl, description="INTEG-LO-V1"):
    """The loopback as the controller stores it before the call: the exact nvPairs this module sends, with another description."""
    ctrl.detail[LO] = {"policy": LO_POLICY, "nvPairs": {"INTF_NAME": LO, "DESC": description, "IP": "192.0.2.91", "V6IP": "", "INTF_VRF": "",
                                                        "ROUTE_MAP_TAG": "12345", "CONF": "", "ADMIN_STATE": "true"}}


def po_desc_ctrl():
    """Po301 holds Eth1/14-15 with the OLD description: the call releases Eth1/15 AND changes the description (live shape)."""
    ctrl = po_ctrl()
    ctrl.detail[CONV_PO]["nvPairs"]["DESC"] = "INTEG-PO-CONV-V1"
    return ctrl


def mixed_modify_owned(result):
    return sorted(set((r["serial"], n) for r in result.get("pvlan_gate_invocation_releases") or [] for n in r["interfaces"]))


# ================================================================== regular port-channel
def test_conventional_po_modified_and_releasing_a_member_in_the_same_call_is_part_of_the_saved_update():
    """Fail-before on 5d28167e: refused as 'outside this deploy batch: port-channel301'."""
    ctrl = po_desc_ctrl()
    status, result = t5_po_call(ctrl, released_block(C15) + PO_BLOCK)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.deploys() == [], "deploy false: nothing deployed"
    assert mixed_modify_owned(result) == [(MU.H.SERIAL, "ethernet1/15"), (MU.H.SERIAL, "port-channel301")]
    bodies = [b for b in ctrl.modify_bodies() if any(p.get("policy") == CONV_PO_POLICY for p in b)]
    assert len(bodies) == 1 and any(i["ifName"] == MU.H.PO for p in bodies[0] for i in p["interfaces"]), \
        "the conventional Po and the PVLAN Po travel in the one bulk modify (the released member's own write follows, as before)"


def test_loopback_modified_beside_the_aggregates_is_part_of_the_saved_update():
    ctrl = po_desc_ctrl()
    seed_lo(ctrl)
    ctrl.previews = [with_pending(MU.fragments(kept=(MU.E7,), removed_trunk=(MU.E9,)), released_block(C15) + PO_BLOCK + LO_BLOCK)]
    status, result = run(ctrl, [conv_po_item(), lo_item(), MU.item([MU.E7], deploy=False)], "replaced", patch_version=PATCH)
    assert status == "exit", result.get("msg")
    assert mixed_modify_owned(result) == [(MU.H.SERIAL, "ethernet1/15"), (MU.H.SERIAL, "loopback391"), (MU.H.SERIAL, "port-channel301")]
    assert ctrl.deploys() == []


def test_member_release_alone_is_still_accepted():
    """Positive control."""
    status, result = t5_po_call(po_ctrl(), released_block(C15))
    assert status == "exit" and mixed_modify_owned(result) == [(MU.H.SERIAL, "ethernet1/15")], result.get("msg")


def test_an_interface_in_the_call_that_was_not_modified_grants_nothing():
    """loopback391 is requested exactly as stored (no update sent) but has a pending block: not this invocation's write."""
    ctrl = po_desc_ctrl()
    seed_lo(ctrl)
    first, result = run(ctrl, [lo_item()], "replaced", patch_version=PATCH)  # an earlier invocation stores the V2 loopback
    assert first == "exit", result.get("msg")
    ctrl.next_invocation()
    ctrl.calls = []
    ctrl.previews = [with_pending(MU.fragments(kept=(MU.E7,), removed_trunk=(MU.E9,)), released_block(C15) + PO_BLOCK + LO_BLOCK)]
    status, result = run(ctrl, [conv_po_item(), lo_item(), MU.item([MU.E7], deploy=False)], "replaced", patch_version=PATCH)
    assert not [p for b in ctrl.modify_bodies() for p in b if p.get("policy") == LO_POLICY], "precondition: the loopback is not sent"
    assert status == "fail" and "outside this deploy batch: loopback391" in result["msg"], result.get("msg")
    assert ctrl.deploys() == []


def test_a_modify_without_a_success_item_for_the_interface_grants_nothing():
    """207 whose DATA has no outcome item for Po301 (only the PVLAN Po and the loopback): unconfirmed, its block stays foreign."""
    ctrl = po_desc_ctrl()
    seed_lo(ctrl)
    ctrl.modify_responses = [{"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [
        {"reportItemType": "SUCCESS", "message": "Interface updated successfully", "entity": "%s~%s" % (MU.H.SERIAL, MU.H.PO)},
        {"reportItemType": "SUCCESS", "message": "Interface updated successfully", "entity": "%s~%s" % (MU.H.SERIAL, LO)}]}]
    ctrl.previews = [with_pending(MU.fragments(kept=(MU.E7,), removed_trunk=(MU.E9,)), PO_BLOCK + LO_BLOCK)]
    status, result = run(ctrl, [conv_po_item(), lo_item(), MU.item([MU.E7], deploy=False)], "replaced", patch_version=PATCH)
    assert status == "fail" and "outside this deploy batch: port-channel301" in result["msg"], result.get("msg")
    assert "loopback391" not in result["msg"].split("outside this deploy batch:")[1].split("\n")[0]
    assert ctrl.deploys() == []


def test_unrelated_interface_and_global_pending_are_still_refused():
    ctrl = po_desc_ctrl()
    status, result = t5_po_call(ctrl, released_block(C15) + PO_BLOCK + ["interface ethernet1/30", "  description stray"])
    assert status == "fail" and "outside this deploy batch: ethernet1/30" in result["msg"] and ctrl.deploys() == [], result.get("msg")
    ctrl = po_desc_ctrl()
    status, result = t5_po_call(ctrl, released_block(C15) + PO_BLOCK + ["router bgp 65000"])
    assert status == "fail" and "outside interface scope" in result["msg"] and ctrl.deploys() == [], result.get("msg")


def test_a_later_invocation_that_modifies_nothing_does_not_own_the_saved_block(monkeypatch):
    """The saved call succeeds; a LATER invocation repeats it (nothing is updated now) with deploy true to complete the saved removal:
    Po301's pending block is not that invocation's write and still refuses the deploy."""
    ctrl = po_desc_ctrl()
    status, result = t5_po_call(ctrl, released_block(C15) + PO_BLOCK)
    assert status == "exit", result.get("msg")
    ctrl.next_invocation()
    monkeypatch.setitem(HH.INVENTORY, SWITCH_IP, dict(HH.INVENTORY[SWITCH_IP], ccStatus="Out-of-Sync"))
    saved = with_pending(MU.fragments(kept=(MU.E7,), removed_trunk=(MU.E9,)), PO_BLOCK)
    ctrl.previews = [copy.deepcopy(saved) for _i in range(3)]
    status, result = run(ctrl, [conv_po_item(), MU.item([MU.E7], deploy=True)], "replaced", patch_version=PATCH)
    assert status == "fail" and "outside this deploy batch: port-channel301" in result["msg"] and ctrl.deploys() == [], result.get("msg")


# ================================================================== vPC
def vpc_desc_ctrl(pcid1="305", pcid2="305"):
    ctrl = vpc_ctrl()
    nv = ctrl.parents[CONV_VPC]["nvPairs"]
    nv.update({"PEER1_PO_DESC": "INTEG-VPC-CONV-V1", "PEER2_PO_DESC": "INTEG-VPC-CONV-V1", "PEER1_PCID": pcid1, "PEER2_PCID": pcid2})
    return ctrl


def conv_vpc(pcid1=305, pcid2=305):
    item = conv_vpc_item()
    item["profile"] = dict(item["profile"], peer1_pcid=pcid1, peer2_pcid=pcid2)
    return item


def child_block(pcid):
    return ["interface port-channel%s" % pcid, "  description INTEG-VPC-CONV-V2"]


def test_conventional_vpc_modified_owns_each_peer_child_by_its_own_pcid():
    ctrl = vpc_desc_ctrl()
    extra = {V.SN1: released_block(V6, 305) + child_block(305), V.SN2: released_block(V6, 305) + child_block(305)}
    status, result = t5_vpc_call(ctrl, extra=extra, conv=conv_vpc())
    assert status == "exit", result.get("msg")
    assert mixed_modify_owned(result) == sorted([(V.SN1, "ethernet1/6"), (V.SN1, "port-channel305"), (V.SN2, "ethernet1/6"), (V.SN2, "port-channel305")])
    assert "DEPLOY" not in ctrl.order()


def test_vpc_children_follow_the_peer_pcid_not_the_vpc_id_nor_the_other_peer():
    """PEER1_PCID 306, PEER2_PCID 307: each peer owns only its own child; port-channel307 on peer 1 and the vPC id 305 stay foreign."""
    ctrl = vpc_desc_ctrl("306", "307")
    extra = {V.SN1: released_block(V6, 306) + child_block(306), V.SN2: released_block(V6, 307) + child_block(307)}
    status, result = t5_vpc_call(ctrl, extra=extra, conv=conv_vpc(306, 307))
    assert status == "exit", result.get("msg")
    assert mixed_modify_owned(result) == sorted([(V.SN1, "ethernet1/6"), (V.SN1, "port-channel306"), (V.SN2, "ethernet1/6"), (V.SN2, "port-channel307")])
    ctrl = vpc_desc_ctrl("306", "307")
    extra = {V.SN1: released_block(V6, 306) + child_block(306) + child_block(307) + child_block(305),
             V.SN2: released_block(V6, 307) + child_block(307)}
    status, result = t5_vpc_call(ctrl, extra=extra, conv=conv_vpc(306, 307))
    assert status == "fail", result.get("msg")
    assert "peer 1 (%s): pending exists for interfaces outside this deploy batch: port-channel305, port-channel307" % V.SN1 in result["msg"], result["msg"]
    assert "DEPLOY" not in ctrl.order()


# ================================================================== the record itself (module-level function, no controller)
class _Obj(object):
    def __init__(self, targets=None, planning=None):
        self.pvlan_targets = targets or {}
        if planning is not None:
            self.pvlan_planning_previews = planning


def _payload(policy, sno, name, itype, nv=None):
    return {"policy": policy, "interfaces": [{"serialNumber": sno, "ifName": name, "interfaceType": itype, "nvPairs": nv or {}}]}


def _ok(*pairs):
    return {"RETURN_CODE": 207, "MESSAGE": "Multi-Status",
            "DATA": [{"reportItemType": t, "message": "", "entity": "%s~%s" % (s, n)} for s, n, t in pairs]}


def test_the_record_keeps_only_confirmed_sent_interfaces_per_physical_serial():
    from ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface import pvlan_record_conventional_modified as rec
    obj = _Obj(targets={("SN1", "port-channel10"): {}, ("SN1", "ethernet1/21"): {}})
    payloads = [
        _payload("int_loopback", "SN1", "Loopback391", "INTERFACE_LOOPBACK"),
        _payload("int_port_channel_trunk_host", "SN1", "Port-channel301", "INTERFACE_PORT_CHANNEL"),   # ERROR outcome
        _payload("int_trunk_host", "SN1", "Ethernet1/12", "INTERFACE_ETHERNET"),                     # no outcome item
        _payload("int_pvlan_host", "SN1", "Ethernet1/20", "INTERFACE_ETHERNET"),                     # PVLAN policy
        _payload("int_port_channel_pvlan_host", "SN1", "Port-channel10", "INTERFACE_PORT_CHANNEL"),  # PVLAN target
        _payload("int_vpc_trunk_host", "SN1~SN2", "vPC305", "INTERFACE_VPC", {"PEER1_PCID": "306", "PEER2_PCID": ""}),
        _payload("int_trunk_host", "SN1~SN2", "Ethernet1/9", "INTERFACE_ETHERNET"),                 # pair serial, not a vPC
        _payload("int_trunk_host", "SN1", "Ethernet1/21", "INTERFACE_ETHERNET"),  # a PVLAN target leaving PVLAN: the gate judges it
    ]
    resp = _ok(("SN1", "Loopback391", "SUCCESS"), ("SN1", "Port-channel301", "ERROR"), ("SN1", "Ethernet1/20", "SUCCESS"),
               ("SN1", "Port-channel10", "SUCCESS"), ("SN1~SN2", "vPC305", "SUCCESS"), ("SN1~SN2", "Ethernet1/9", "SUCCESS"),
               ("SN1", "Ethernet1/21", "SUCCESS"))
    assert rec(obj, payloads, resp) == {"SN1": {"loopback391", "port-channel306"}}, "peer 2 has no numeric PCID: nothing for SN2"
    assert obj.pvlan_invocation_modified == {"SN1": {"loopback391", "port-channel306"}}


def test_an_interface_already_pending_in_the_pre_write_planning_preview_is_not_recorded():
    from ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface import pvlan_record_conventional_modified as rec
    planning = {"SN1": {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [{"switchId": "SN1", "status": "Out-of-Sync",
                                                                       "pendingConfig": ["interface loopback391", "  description earlier"]}]}}
    obj = _Obj(planning=planning)
    payloads = [_payload("int_loopback", "SN1", "Loopback391", "INTERFACE_LOOPBACK"),
                _payload("int_loopback", "SN1", "Loopback392", "INTERFACE_LOOPBACK")]
    assert rec(obj, payloads, _ok(("SN1", "Loopback391", "SUCCESS"), ("SN1", "Loopback392", "SUCCESS"))) == {"SN1": {"loopback392"}}


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_mixed_saved_retry.py
# A saved mixed conventional/PVLAN aggregate deletion completed by a LATER dcnm_interface invocation with deployment.
#
# Invocation 1: `state: deleted`, a conventional port-channel + a PVLAN Po (and the vPC analogue), every item deploy false. Both
# mark-deletes are confirmed, the members are released in intent, nothing is deployed; the module process ends.
# Invocation 2: a NEW module instance (fresh main()) requests the deletion of the same aggregates with the global AND per-item deploy
# true. Nothing of invocation 1 survives except the controller state the fake keeps: the conventional port-channel listed in the
# MEASURED "marked for deletion" form (markDeleted, one `interface_delete` policy whose source is itself -- for a vPC child, its
# parent vPC), its released members, and a device running configuration that still holds the aggregate with those members joined
# (fresh forced preview).
#
# Rule under test: the conventional saved deletion is completed together with the PVLAN one only when THIS request names it with
# deployment and the controller state above proves it on every physical serial; ambiguous, unrelated or unverifiable state refuses
# with nothing deployed.
# ====================================================================================================
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
    (None, released_block(MIXED_DELETE_C14, 301) + ["interface ethernet1/30", "  description stray"], "outside this deploy batch: ethernet1/30"),
    (None, released_block(MIXED_DELETE_C14, 399), "outside this deploy batch: ethernet1/14"),
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
    assert mixed_retry_vpc_owned(result) == [(V.SN1, ("ethernet1/5",), ("no interface port-channel305",)),
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
