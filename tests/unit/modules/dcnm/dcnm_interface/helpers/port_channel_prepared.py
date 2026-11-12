"""Port-channel PVLAN controllers for members prepared as access or routed before a trunk-secondary join."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
from .ethernet_controller import SWITCH_IP, preview, run
from .port_channel_controller import PoLifecycleController
from .fixture_cases import load_case


FX = load_case("pvlan_po_ts_exp1_measured")
MEM, PO_DEV, PO = "Ethernet1/8", "port-channel504", "Port-channel504"
TS = "trunk secondary"
TS1_PROFILE = {  # live model TS1 (replaced, 2210/2212)
    "mode": "pvlan",
    "pvlan_mode": TS,
    "members": [MEM],
    "pc_mode": "active",
    "admin_state": False,
    "pvlan_association": [{"primary_vlan": 2210, "secondary_vlan": 2212}],
    "native_vlan": "2301",
    "allowed_vlans": "2301",
}


def branch(b):
    return copy.deepcopy(FX["branches"][b])


def member_nv(b):
    return dict((k, v) for k, v in branch(b)["member_before"]["intent"][MEM]["nvPairs"].items() if k != "POLICY_ID")


def member_policy(b):
    return branch(b)["member_before"]["intent"][MEM]["policy"]


def measured_preview(b, pending=None, running=None, expected=None):
    cp = branch(b)["create_preview"]
    return preview(
        pending if pending is not None else cp["pendingConfig"],
        running=running if running is not None else cp["runningConfig_stanzas"],
        expected=expected if expected is not None else cp["expectedConfig_stanzas"],
    )


def self_children(b):
    """The measured live child policies of the prepared member (routed: routed_interface/interface_mtu/shut_interface, source =
    the member itself)."""
    out = []
    for p in branch(b)["member_before"]["policies"]:
        if p.get("source") and p["source"].lower() == MEM.lower():
            out.append(dict(p, entityType="INTERFACE", serialNumber="x"))
    return out


def ctrl_for(b, nv=None):
    ctrl = PoLifecycleController()
    ctrl.detail[MEM] = {"policy": member_policy(b), "nvPairs": nv if nv is not None else member_nv(b)}
    ctrl.policies_extra = self_children(b)
    return ctrl


def create(ctrl, pv=None, **profile):
    if pv is not None:
        ctrl.previews = [pv]
    prof = dict(TS1_PROFILE, **profile)
    return run(ctrl, [{"name": "po504", "type": "pc", "switch": [SWITCH_IP], "deploy": True, "profile": prof}], state="replaced")
