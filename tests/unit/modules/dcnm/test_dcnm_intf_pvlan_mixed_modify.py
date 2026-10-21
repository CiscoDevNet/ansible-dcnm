"""Conventional interfaces MODIFIED in the same dcnm_interface call as a saved PVLAN membership removal.

A single `replaced` call, every item deploy false, can remove members of a PVLAN and of a conventional aggregate AND change
other interfaces on the same switches. The PVLAN `update_saved` gate must not refuse those changes as "outside this deploy
batch".

Rule: a pending interface outside the PVLAN batch is accepted when THIS invocation's confirmed bulk update (the payload actually
sent and a per-item SUCCESS naming it) modified it on THAT physical serial: the interface itself (Ethernet, loopback,
port-channel, SVI ...) or, for a conventional vPC, each peer's child `port-channel<PEERn_PCID>` on that peer. Anything only
desired, not sent, not confirmed, on another serial or another port-channel id, and every global line, stays refused.

Real main() through the existing mixed-batch Po and vPC harnesses; only the controller boundary is faked.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

from . import test_dcnm_intf_pvlan_harness as HH
from . import test_dcnm_intf_pvlan_member_updates as MU
from . import test_dcnm_intf_pvlan_mixed_batch as MB
from . import test_dcnm_intf_pvlan_vpc_harness as V
from .test_dcnm_intf_pvlan_harness import SWITCH_IP, run

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
    ctrl = MB.po_ctrl()
    ctrl.detail[MB.CONV_PO]["nvPairs"]["DESC"] = "INTEG-PO-CONV-V1"
    return ctrl


def owned(result):
    return sorted(set((r["serial"], n) for r in result.get("pvlan_gate_invocation_releases") or [] for n in r["interfaces"]))


# ================================================================== regular port-channel
def test_conventional_po_modified_and_releasing_a_member_in_the_same_call_is_part_of_the_saved_update():
    """Fail-before on 5d28167e: refused as 'outside this deploy batch: port-channel301'."""
    ctrl = po_desc_ctrl()
    status, result = MB.t5_po_call(ctrl, MB.released_block(MB.C15) + PO_BLOCK)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.deploys() == [], "deploy false: nothing deployed"
    assert owned(result) == [(MU.H.SERIAL, "ethernet1/15"), (MU.H.SERIAL, "port-channel301")]
    bodies = [b for b in ctrl.modify_bodies() if any(p.get("policy") == MB.CONV_PO_POLICY for p in b)]
    assert len(bodies) == 1 and any(i["ifName"] == MU.H.PO for p in bodies[0] for i in p["interfaces"]), \
        "the conventional Po and the PVLAN Po travel in the one bulk modify (the released member's own write follows, as before)"


def test_loopback_modified_beside_the_aggregates_is_part_of_the_saved_update():
    ctrl = po_desc_ctrl()
    seed_lo(ctrl)
    ctrl.previews = [MB.with_pending(MU.fragments(kept=(MU.E7,), removed_trunk=(MU.E9,)), MB.released_block(MB.C15) + PO_BLOCK + LO_BLOCK)]
    status, result = run(ctrl, [MB.conv_po_item(), lo_item(), MU.item([MU.E7], deploy=False)], "replaced", patch_version=MB.PATCH)
    assert status == "exit", result.get("msg")
    assert owned(result) == [(MU.H.SERIAL, "ethernet1/15"), (MU.H.SERIAL, "loopback391"), (MU.H.SERIAL, "port-channel301")]
    assert ctrl.deploys() == []


def test_member_release_alone_is_still_accepted():
    """Positive control."""
    status, result = MB.t5_po_call(MB.po_ctrl(), MB.released_block(MB.C15))
    assert status == "exit" and owned(result) == [(MU.H.SERIAL, "ethernet1/15")], result.get("msg")


def test_an_interface_in_the_call_that_was_not_modified_grants_nothing():
    """loopback391 is requested exactly as stored (no update sent) but has a pending block: not this invocation's write."""
    ctrl = po_desc_ctrl()
    seed_lo(ctrl)
    first, result = run(ctrl, [lo_item()], "replaced", patch_version=MB.PATCH)  # an earlier invocation stores the V2 loopback
    assert first == "exit", result.get("msg")
    ctrl.next_invocation()
    ctrl.calls = []
    ctrl.previews = [MB.with_pending(MU.fragments(kept=(MU.E7,), removed_trunk=(MU.E9,)), MB.released_block(MB.C15) + PO_BLOCK + LO_BLOCK)]
    status, result = run(ctrl, [MB.conv_po_item(), lo_item(), MU.item([MU.E7], deploy=False)], "replaced", patch_version=MB.PATCH)
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
    ctrl.previews = [MB.with_pending(MU.fragments(kept=(MU.E7,), removed_trunk=(MU.E9,)), PO_BLOCK + LO_BLOCK)]
    status, result = run(ctrl, [MB.conv_po_item(), lo_item(), MU.item([MU.E7], deploy=False)], "replaced", patch_version=MB.PATCH)
    assert status == "fail" and "outside this deploy batch: port-channel301" in result["msg"], result.get("msg")
    assert "loopback391" not in result["msg"].split("outside this deploy batch:")[1].split("\n")[0]
    assert ctrl.deploys() == []


def test_unrelated_interface_and_global_pending_are_still_refused():
    ctrl = po_desc_ctrl()
    status, result = MB.t5_po_call(ctrl, MB.released_block(MB.C15) + PO_BLOCK + ["interface ethernet1/30", "  description stray"])
    assert status == "fail" and "outside this deploy batch: ethernet1/30" in result["msg"] and ctrl.deploys() == [], result.get("msg")
    ctrl = po_desc_ctrl()
    status, result = MB.t5_po_call(ctrl, MB.released_block(MB.C15) + PO_BLOCK + ["router bgp 65000"])
    assert status == "fail" and "outside interface scope" in result["msg"] and ctrl.deploys() == [], result.get("msg")


def test_a_later_invocation_that_modifies_nothing_does_not_own_the_saved_block(monkeypatch):
    """The saved call succeeds; a LATER invocation repeats it (nothing is updated now) with deploy true to complete the saved removal:
    Po301's pending block is not that invocation's write and still refuses the deploy."""
    ctrl = po_desc_ctrl()
    status, result = MB.t5_po_call(ctrl, MB.released_block(MB.C15) + PO_BLOCK)
    assert status == "exit", result.get("msg")
    ctrl.next_invocation()
    monkeypatch.setitem(HH.INVENTORY, SWITCH_IP, dict(HH.INVENTORY[SWITCH_IP], ccStatus="Out-of-Sync"))
    saved = MB.with_pending(MU.fragments(kept=(MU.E7,), removed_trunk=(MU.E9,)), PO_BLOCK)
    ctrl.previews = [copy.deepcopy(saved) for _i in range(3)]
    status, result = run(ctrl, [MB.conv_po_item(), MU.item([MU.E7], deploy=True)], "replaced", patch_version=MB.PATCH)
    assert status == "fail" and "outside this deploy batch: port-channel301" in result["msg"] and ctrl.deploys() == [], result.get("msg")


# ================================================================== vPC
def vpc_desc_ctrl(pcid1="305", pcid2="305"):
    ctrl = MB.vpc_ctrl()
    nv = ctrl.parents[MB.CONV_VPC]["nvPairs"]
    nv.update({"PEER1_PO_DESC": "INTEG-VPC-CONV-V1", "PEER2_PO_DESC": "INTEG-VPC-CONV-V1", "PEER1_PCID": pcid1, "PEER2_PCID": pcid2})
    return ctrl


def conv_vpc(pcid1=305, pcid2=305):
    item = MB.conv_vpc_item()
    item["profile"] = dict(item["profile"], peer1_pcid=pcid1, peer2_pcid=pcid2)
    return item


def child_block(pcid):
    return ["interface port-channel%s" % pcid, "  description INTEG-VPC-CONV-V2"]


def test_conventional_vpc_modified_owns_each_peer_child_by_its_own_pcid():
    ctrl = vpc_desc_ctrl()
    extra = {V.SN1: MB.released_block(MB.V6, 305) + child_block(305), V.SN2: MB.released_block(MB.V6, 305) + child_block(305)}
    status, result = MB.t5_vpc_call(ctrl, extra=extra, conv=conv_vpc())
    assert status == "exit", result.get("msg")
    assert owned(result) == sorted([(V.SN1, "ethernet1/6"), (V.SN1, "port-channel305"), (V.SN2, "ethernet1/6"), (V.SN2, "port-channel305")])
    assert "DEPLOY" not in ctrl.order()


def test_vpc_children_follow_the_peer_pcid_not_the_vpc_id_nor_the_other_peer():
    """PEER1_PCID 306, PEER2_PCID 307: each peer owns only its own child; port-channel307 on peer 1 and the vPC id 305 stay foreign."""
    ctrl = vpc_desc_ctrl("306", "307")
    extra = {V.SN1: MB.released_block(MB.V6, 306) + child_block(306), V.SN2: MB.released_block(MB.V6, 307) + child_block(307)}
    status, result = MB.t5_vpc_call(ctrl, extra=extra, conv=conv_vpc(306, 307))
    assert status == "exit", result.get("msg")
    assert owned(result) == sorted([(V.SN1, "ethernet1/6"), (V.SN1, "port-channel306"), (V.SN2, "ethernet1/6"), (V.SN2, "port-channel307")])
    ctrl = vpc_desc_ctrl("306", "307")
    extra = {V.SN1: MB.released_block(MB.V6, 306) + child_block(306) + child_block(307) + child_block(305),
             V.SN2: MB.released_block(MB.V6, 307) + child_block(307)}
    status, result = MB.t5_vpc_call(ctrl, extra=extra, conv=conv_vpc(306, 307))
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
