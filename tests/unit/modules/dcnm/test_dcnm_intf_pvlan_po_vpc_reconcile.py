"""RECONCILE: PVLAN regular port-channel / vPC under `overridden` (A) and the NaC deployment contract (B).

A -- `overridden` reuses the existing paths: a PVLAN aggregate the request keeps goes through its own PVLAN compare (replace semantics),
and every PVLAN aggregate of the sweep's scope that the request no longer wants is registered by the SAME deletion preflight as a named
`deleted` (ownership, admin-down members, fabric host default, bulk API), released by G4/E5 and verified. The generic default reset the
sweep queues for the member of a deleted aggregate is withdrawn (the PVLAN release corrects that member itself).

MEASURED inputs: the existing fixtures of the harnesses (H1/G4R1 for the regular Po, L1/E4 for the vPC) and, for the vPC summary,
`deletable` False on the child port-channel and on the physical members, True on the parent (alpha2-vpc-combined-live C0, NDFC
12.6.0.267, sum104.json) -- the vPC harness reports True everywhere, so MeasuredVpc restores the measured value. Real main(); only the
controller boundary is intercepted.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

import pytest
from unittest.mock import patch

from . import test_dcnm_intf_pvlan_harness as HH
from . import test_dcnm_intf_pvlan_member_updates as MU
from . import test_dcnm_intf_pvlan_po_g4_release as G4
from . import test_dcnm_intf_pvlan_vpc_harness as V
from .test_dcnm_intf_pvlan_harness import SWITCH_IP, TRUNK, run

PO_PROFILE = {"mode": "pvlan", "pvlan_mode": "host", "members": [G4.MEM], "pc_mode": "active", "admin_state": False,
              "pvlan_association": [{"primary_vlan": 2210, "secondary_vlan": 2212}]}
RETAINED_PO = {"name": "po502", "type": "pc", "switch": [SWITCH_IP], "deploy": True, "profile": PO_PROFILE}


def lo(ip, deploy=True):
    """A desired non-PVLAN interface, so the overridden request is not empty (the sweep keeps its normal scope)."""
    return {"name": "lo100", "type": "lo", "switch": [ip], "deploy": deploy,
            "profile": {"mode": "lo", "int_vrf": "", "ipv4_addr": "10.9.9.9", "admin_state": True}}


def with_args(harness, runner, ctrl, config, extra, **kw):
    """The harness runner with extra module arguments (global deploy, override_intf_types): the harness's own set_module_args is
    wrapped, nothing else changes."""
    original = harness.set_module_args
    with patch.object(harness, "set_module_args", side_effect=lambda a: original(dict(a, **extra))):
        return runner(ctrl, config, **kw)


def writes(ctrl):
    out = []
    for m, p, _d in ctrl.calls:
        if m in ("POST", "PUT", "DELETE") and "/config-preview" not in p and "networkAttachments" not in p:
            out.append(p.rsplit("/rest/", 1)[-1])
    return out


def modify_payloads(ctrl):
    return [p for m, path, d in ctrl.calls if m == "POST" and path.endswith("/rest/interface/modify") for p in json.loads(d)]


class MeasuredVpc(V.VpcController):
    """The vPC harness with the MEASURED summary `deletable` (child Po and physical members False, parent True)."""

    def _summary_entry(self, serial, name, d, status):
        entry = super(MeasuredVpc, self)._summary_entry(serial, name, d, status)
        if d["policy"] in (V.VPC_PO, V.PO_MEMBER, TRUNK, "int_access_host", "int_routed_host"):
            entry["deletable"] = "False"
        return entry


def measured_po(ctrl):
    """The Po harnesses report `deletable` True and no policy source on physical ports; the controller reports `deletable` False on a
    PVLAN member and on a standalone int_trunk_host, and the member's policy source is its port-channel in lower case (MEASURED: G4R1
    HR-pre summary `port-channel502`, C0 sum104, Leaf-103/104 Ethernet1/15 of PR725-ADMIN-UP-JOIN). The sweep then defers those ports to
    their source instead of resetting them directly, which is the path the controller really takes."""
    original = ctrl._summary_list

    def summary():
        out = original()
        for entry in out:
            if str(entry.get("isPhysical")).lower() == "true":
                entry["deletable"] = "False"
                d = ctrl.detail.get(entry["ifName"]) or {}
                if d.get("policy") == G4.PO_MEMBER:
                    for pol in entry.get("underlayPolicies") or []:
                        pol["source"] = str((d.get("nvPairs") or {}).get("PO_ID", "")).lower()
        return out

    ctrl._summary_list = summary
    return ctrl


def vpc_ctrl(cls=None):
    ctrl = (cls or MeasuredVpc)().seed_baseline().seed_vpc()
    ctrl.next_invocation()
    return ctrl


# ================================================================== A: regular port-channel
def test_po_retained_by_overridden_is_its_own_pvlan_repetition_without_writes():
    ctrl = measured_po(G4.owned_ctrl())
    status, result = run(ctrl, [RETAINED_PO], state="overridden")
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert writes(ctrl) == []


def test_po_dropped_by_overridden_is_deleted_through_the_pvlan_path_and_its_member_released_once():
    ctrl = measured_po(G4.owned_ctrl())
    status, result = run(ctrl, [lo(SWITCH_IP)], state="overridden")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert writes(ctrl) == ["interface/markdelete", "interface/modify", "globalInterface/deploy", "globalInterface", "globalInterface/deploy"]
    payloads = modify_payloads(ctrl)
    assert len(payloads) == 1 and payloads[0]["policy"] == TRUNK, "ONE member write: the G4 correction, never the generic reset"
    nv = payloads[0]["interfaces"][0]["nvPairs"]
    assert nv["ADMIN_STATE"] == "false" and len(nv) == 50
    assert result["diff"][0]["replaced"] == [] and G4.MEM not in json.dumps(result["diff"][0]["deploy"])
    assert G4.PO not in ctrl.detail and ctrl.detail[G4.MEM]["nvPairs"]["ADMIN_STATE"] == "false"


def test_the_last_pvlan_port_channel_goes_with_an_empty_desired_set():
    ctrl = measured_po(G4.owned_ctrl())
    status, result = run(ctrl, [], state="overridden")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert writes(ctrl) == ["interface/markdelete", "interface/modify", "globalInterface/deploy"]


def test_override_intf_types_that_exclude_port_channels_leave_the_pvlan_port_channel_alone():
    ctrl = measured_po(G4.owned_ctrl())
    status, result = with_args(HH, run, ctrl, [lo(SWITCH_IP)], {"override_intf_types": ["lo"]}, state="overridden")
    assert status == "exit", result.get("msg")
    assert writes(ctrl) == ["globalInterface", "globalInterface/deploy"] and G4.PO in ctrl.detail


def test_a_dropped_port_channel_whose_member_is_up_keeps_the_release_contract_and_writes_nothing():
    ctrl = measured_po(G4.owned_ctrl())
    ctrl.detail[G4.MEM]["nvPairs"]["ADMIN_STATE"] = "true"
    status, result = run(ctrl, [lo(SWITCH_IP)], state="overridden")
    assert status == "fail" and "not administratively down; releasing it is not implemented" in result["msg"], result.get("msg")
    assert writes(ctrl) == []


def test_an_unreadable_summary_refuses_the_sweep_before_any_write():
    ctrl = measured_po(G4.owned_ctrl())
    ctrl.read_failures = {"/rest/interface/detail?serialNumber="}
    status, result = run(ctrl, [lo(SWITCH_IP)], state="overridden")
    assert status == "fail" and writes(ctrl) == [], result.get("msg")


def test_check_mode_keeps_a_retained_port_channel_and_refuses_an_undemonstrable_deletion():
    ctrl = measured_po(G4.owned_ctrl())
    status, result = run(ctrl, [RETAINED_PO], state="overridden", check_mode=True)
    assert status == "exit" and writes(ctrl) == [], result.get("msg")
    ctrl = measured_po(G4.owned_ctrl())
    status, result = run(ctrl, [lo(SWITCH_IP)], state="overridden", check_mode=True)
    assert status == "fail" and "refused in check mode" in result["msg"] and writes(ctrl) == [], result.get("msg")


def test_overridden_with_fewer_members_releases_the_dropped_member_through_the_membership_path():
    ctrl = measured_po(MU.seeded())
    ctrl.previews = [MU.fragments(kept=(MU.E7,), removed_trunk=(MU.E9,))]
    status, result = run(ctrl, [MU.item([MU.E7])], state="overridden")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.po_modifies()) == 1 and len(ctrl.member_modifies()) == 1 and len(ctrl.deploys()) == 1
    assert ctrl.detail[MU.E9]["policy"] == TRUNK and ctrl.detail[MU.E9]["nvPairs"]["ADMIN_STATE"] == "false"


# ================================================================== A: vPC
def test_vpc_retained_by_overridden_is_its_own_pvlan_repetition_without_writes():
    ctrl = vpc_ctrl()
    V.converged_previews(ctrl)
    status, result = V.run_vpc(ctrl, [V.vpc_item()], state="overridden")
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert writes(ctrl) == []


@pytest.mark.parametrize("switches", [[V.IP1], [V.IP1, V.IP2]], ids=["one-peer-in-request", "both-peers-in-request"])
def test_vpc_dropped_by_overridden_is_deleted_once_released_on_both_peers_and_verified(switches):
    ctrl = vpc_ctrl()
    V.delete_previews(ctrl)
    status, result = V.run_vpc(ctrl, [lo(ip) for ip in switches], state="overridden")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert writes(ctrl)[:4] == ["interface/markdelete", "interface/modify", "interface/modify", "globalInterface/deploy"]
    assert len(ctrl.markdeletes()) == 1, "one identity (pair + name), deleted once even when both peers are swept"
    assert sorted(p["interfaces"][0]["serialNumber"] for p in modify_payloads(ctrl) if p["policy"] == TRUNK) == [V.SN1, V.SN2]
    assert V.VPC not in ctrl.parents


class OtherPair(MeasuredVpc):
    """The controller places the first peer in ANOTHER pair than the summary's vPC identity."""

    def __call__(self, mod, method, path, data=None):
        if "vpcpair_serial_number" in path:
            self.calls.append((method, path, data))
            return HH.ok({"vpc_pair_sn": "FDO00000001~FDO00000009"})
        return super(OtherPair, self).__call__(mod, method, path, data)


def test_vpc_whose_pair_the_controller_does_not_confirm_is_refused_before_any_write():
    ctrl = vpc_ctrl(OtherPair)
    V.delete_previews(ctrl)
    status, result = V.run_vpc(ctrl, [lo(V.IP1)], state="overridden")
    assert status == "fail" and "vPC pair" in result["msg"] and writes(ctrl) == [], result.get("msg")


def test_vpc_dropped_with_an_up_member_on_one_peer_keeps_the_release_contract():
    ctrl = vpc_ctrl()
    ctrl.nodes[V.SN2][V.M2]["nvPairs"]["ADMIN_STATE"] = "true"
    V.delete_previews(ctrl)
    status, result = V.run_vpc(ctrl, [lo(V.IP1)], state="overridden")
    assert status == "fail" and "not administratively down" in result["msg"] and writes(ctrl) == [], result.get("msg")
