"""Conventional and PVLAN member removals in ONE dcnm_interface call.

A single `state: replaced` call, each item deploy false, can release a member of a CONVENTIONAL port-channel / vPC and a member
of a PVLAN one on the same switch. The PVLAN saved-update gate (`update_saved`) must not refuse the conventional released member
as "outside this deploy batch".

Rule: a pending interface outside the PVLAN batch is accepted ONLY when this invocation's CONFIRMED update (per-item SUCCESS) of a
conventional aggregate released it on THAT physical serial (pre-state member list read by this run minus the member list sent) AND
its pending block withdraws that aggregate's channel-group. Everything else stays refused.

Shapes: measured module arguments and forced-preview pending lines, sanitized. Real main() through the existing Po and vPC
harnesses; only the controller boundary is faked.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

import pytest

from . import test_dcnm_intf_pvlan_harness as HH
from . import test_dcnm_intf_pvlan_member_updates as MU
from . import test_dcnm_intf_pvlan_vpc_harness as V
from .test_dcnm_intf_pvlan_harness import SWITCH_IP, run

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


def released_block(member, pcid=301, withdrawal=True):
    """The measured forced-preview pending of a conventional member released by its port-channel (live diagnosis)."""
    lines = ["interface %s" % member.lower()]
    if withdrawal:
        lines.append("  no channel-group %d force mode active" % pcid)
    return lines + ["  switchport", "  switchport mode trunk", "  switchport trunk allowed vlan none", "  mtu 9216",
                    "  spanning-tree port type edge trunk", "  no shutdown"]


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
