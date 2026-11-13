"""Controllers and queued previews for invocations that mix conventional and PVLAN aggregates."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
from . import ethernet_controller as HH
from . import port_channel_controller as G5
from . import vpc_controller as R
from . import vpc_controller as V
from .ethernet_controller import SERIAL, SWITCH_IP, TRUNK, run, trunk_host_nv


def vpc_conv_pending(member, pcid=305):
    return ["no interface port-channel%d" % pcid] + released_block(member, pcid)


CONV_RUNNING = ["interface ethernet1/14", "  channel-group 301 mode active", "  mtu 9216", "  switchport mode trunk",
                "interface port-channel301", "  description INTEG-PO-CONV-V2", "  mtu 9216", "  switchport mode trunk",
                "  switchport trunk allowed vlan none"]


class SavedConvController(G5.DeployedReleaseController):
    """The measured deletion harness + the conventional Po's saved deletion as the controller keeps it (MEASURED live,
 Port-channel301): after its mark-delete the Po stays listed, markDeleted, with ONE `interface_delete` policy whose source is
    the Po itself, until a deploy that names it. The member is released (int_trunk_host)."""

    conv_marked = None

    def __call__(self, mod, method, path, data=None):
        resp = super(SavedConvController, self).__call__(mod, method, path, data)
        lowered = str(data).lower()
        if method == "DELETE" and path.endswith("/rest/interface/markdelete") and "port-channel301" in lowered:
            entry = copy.deepcopy(self.marked_template)
            entry.update({"ifName": "Port-channel301", "entityId": "%s~port-channel301" % SERIAL, "alias": "INTEG-PO-CONV-V2"})
            entry["underlayPolicies"] = [dict(entry["underlayPolicies"][0], entityName="port-channel301", source="port-channel301")]
            self.conv_marked = entry
            nv = trunk_host_nv(C14)
            nv["ADMIN_STATE"] = "true"  # MEASURED live: the released conventional member is int_trunk_host, administratively up
            self.detail[C14] = {"policy": TRUNK, "nvPairs": nv}
        if method == "POST" and path.endswith("/rest/globalInterface/deploy") and "port-channel301" in lowered:
            self.conv_marked = None
        return resp

    def _summary_list(self):
        return super(SavedConvController, self)._summary_list() + ([copy.deepcopy(self.conv_marked)] if self.conv_marked else [])

    def _policies(self):
        extra = []
        if self.conv_marked:
            extra = [{"entityName": "port-channel301", "entityType": "INTERFACE", "templateName": "interface_delete", "source": "port-channel301",
                      "deleted": True, "policyId": "POLICY-CONV-DEL", "serialNumber": SERIAL}]
        return super(SavedConvController, self)._policies() + extra


def saved_po_ctrl():
    ctrl = G5.hr_ctrl([])
    ctrl.__class__ = SavedConvController  # before measured_po wraps the summary, so the marked conventional entry is listed
    return add_conv_po(R.measured_po(ctrl))


def saved_preview(extra_global=None, extra_blocks=None, running=None):
    """The fresh forced preview of the saved state: pending = the PVLAN Po's + the conventional sibling's (live shape); running = the
    device still holding both port-channels with their members joined."""
    resp = po_preview(T6_GLOBAL if extra_global is None else extra_global,
                      released_block(C14, 301) if extra_blocks is None else extra_blocks)
    entry = resp["DATA"][0]
    entry["runningConfig"] = list(entry.get("runningConfig") or []) + list(CONV_RUNNING if running is None else running)
    return resp


def stage(ctrl):
    """Invocation 1: the measured call (both items deploy false). Returns its result."""
    ctrl.previews = [saved_preview()]
    status, result = run(ctrl, [{"name": "port-channel301", "switch": [SWITCH_IP], "deploy": False},
                                {"name": "po502", "switch": [SWITCH_IP], "deploy": False}], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert "globalInterface/deploy" not in R.writes(ctrl), "invocation 1 deploys nothing"
    assert ctrl.conv_marked is not None and ctrl.marked is not None
    ctrl.next_invocation()
    return result


def retry(ctrl, items=None, previews=4, deploy=True, preview=None):
    """Invocation 2: a NEW module run, global deploy AND item deploy as requested; only the fake's persisted state is shared."""
    ctrl.previews = [copy.deepcopy(preview or saved_preview()) for _i in range(previews)]
    start = len(ctrl.calls)
    items = items or [{"name": "port-channel301", "switch": [SWITCH_IP], "deploy": deploy},
                      {"name": "po502", "switch": [SWITCH_IP], "deploy": deploy}]
    status, result = R.with_args(HH, run, ctrl, items, {"deploy": deploy}, state="deleted")
    return status, result, start


def later_writes(ctrl, start):
    return R.writes(type("C", (), {"calls": ctrl.calls[start:]}))


def deploy_bodies(ctrl, start):
    return [json.loads(c[2]) for c in ctrl.calls[start:] if c[0] == "POST" and c[1].endswith("/rest/globalInterface/deploy")]


# ================================================================== vPC
class SavedConvVpc(R.MeasuredVpc):
    """The vPC deletion harness with each mark-delete's child `interface_delete` owned by THAT vPC (`vpc305` for the conventional one)."""

    def __call__(self, mod, method, path, data=None):
        if method == "DELETE" and path.endswith(V.MARKDELETE):
            self.marked_source = json.loads(data)[0]["ifName"].lower()
            try:
                return super(SavedConvVpc, self).__call__(mod, method, path, data)
            finally:
                self.marked_source = None
        return super(SavedConvVpc, self).__call__(mod, method, path, data)


def conv_vpc_running(member):
    return ["interface port-channel305", "  switchport mode trunk", "  vpc 305", "interface %s" % member, "  channel-group 305 mode active"]


def vpc_preview(serial, port, conv_member, extra=None, running=None):
    p = V.delete_preview(serial, port)
    entry = p["DATA"][0]
    entry["pendingConfig"] = list(entry["pendingConfig"]) + list(vpc_conv_pending(conv_member) if extra is None else extra)
    entry["runningConfig"] = list(entry.get("runningConfig") or []) + list(conv_vpc_running(conv_member) if running is None else running)
    return p


def queue_vpc(ctrl, n, extra=None, running=None):
    for serial, port, conv in ((V.SN1, V.M1, "Ethernet1/5"), (V.SN2, V.M2, "Ethernet1/6")):
        ctrl.vpc_previews[serial] = [vpc_preview(serial, port, conv, (extra or {}).get(serial), (running or {}).get(serial)) for _i in range(n)]


def saved_vpc_ctrl():
    ctrl = vpc_mixed_ctrl()
    ctrl.__class__ = SavedConvVpc
    queue_vpc(ctrl, 1)
    status, result = V.run_vpc(ctrl, [{"name": "vpc305", "type": "vpc", "switch": [V.IP1, V.IP2], "deploy": False}, V.vpc_del_item(deploy=False)],
                               state="deleted")
    assert status == "exit" and ctrl.deploys() == [], result.get("msg")
    ctrl.next_invocation()
    return ctrl


def vpc_retry(ctrl, items=None, n=4, extra=None, running=None):
    queue_vpc(ctrl, n, extra, running)
    start = len(ctrl.calls)
    items = items or [{"name": "vpc305", "type": "vpc", "switch": [V.IP1, V.IP2], "deploy": True}, V.vpc_del_item(deploy=True)]
    status, result = R.with_args(V, V.run_vpc, ctrl, items, {"deploy": True}, state="deleted")
    return status, result, start


def vpc_owned(result):
    return sorted(set((r["serial"], tuple(r["interfaces"]), tuple(r.get("withdrawn") or ()))
                      for r in result.get("pvlan_gate_invocation_releases") or [] if r["site"] == "delete_deploy"))


def released_block(member, pcid=301, withdrawal=True):
    """The measured forced-preview pending of a conventional member released by its port-channel (live diagnosis)."""
    lines = ["interface %s" % member.lower()]
    if withdrawal:
        lines.append("  no channel-group %d force mode active" % pcid)
    return lines + ["  switchport", "  switchport mode trunk", "  switchport trunk allowed vlan none", "  mtu 9216",
                    "  spanning-tree port type edge trunk", "  no shutdown"]


CONV_PO, C14 = "Port-channel301", "Ethernet1/14"
CONV_PO_POLICY, CONV_MEMBER_POLICY = "int_port_channel_trunk_host", "int_port_channel_trunk_member_11_1"
CONV_VPC, V5, V6 = "vPC305", "Ethernet1/5", "Ethernet1/6"


def add_conv_po(ctrl, name=CONV_PO, members=(C14,)):
    """A conventional trunk port-channel ( Po301 shape) with its members, next to the harness's PVLAN Po."""
    nv = {"MEMBER_INTERFACES": ",".join(members), "PO_ID": name, "PC_MODE": "active", "DESC": "INTEG-PO-CONV-V2", "ADMIN_STATE": "true",
          "ALLOWED_VLANS": "none", "MTU": "jumbo", "SPEED": "Auto", "BPDUGUARD_ENABLED": "true", "PORTTYPE_FAST_ENABLED": "true", "CONF": ""}
    ctrl.detail[name] = {"policy": CONV_PO_POLICY, "nvPairs": nv}
    ctrl.po_names.add(name)
    for port in members:
        ctrl.detail[port] = {"policy": CONV_MEMBER_POLICY, "nvPairs": {"PO_ID": name, "ADMIN_STATE": "true", "INTF_NAME": port}}
    return ctrl


def po_preview(extra_global, extra_blocks, base=None):
    """The measured deletion pending of the PVLAN Po (its own `no interface` + released member) plus the conventional sibling's."""
    resp = base or G5.corrected_hr_preview()
    entry = resp["DATA"][0]
    entry["pendingConfig"] = list(extra_global) + list(entry["pendingConfig"]) + list(extra_blocks)
    entry["status"] = "Out-of-Sync"
    return resp


T6_GLOBAL = ["no interface port-channel301"]


# ================================================================== vPC
def vpc_mixed_ctrl(peer_members=(V5, V6), pcids=("305", "305")):
    """The PVLAN vPC10 deletion harness plus a conventional trunk vPC305 whose members DIFFER per peer (peer1 Eth1/5, peer2 Eth1/6), so a
    crossed assignment is visible."""
    ctrl = R.vpc_ctrl()
    ctrl.children_marked_deleted = True
    ctrl.parents[CONV_VPC] = {"policy": "int_vpc_trunk_host", "nvPairs": {
        "PEER1_MEMBER_INTERFACES": peer_members[0], "PEER2_MEMBER_INTERFACES": peer_members[1], "PEER1_PCID": pcids[0], "PEER2_PCID": pcids[1],
        "PC_MODE": "active", "ADMIN_STATE": "true", "PEER1_PO_DESC": "INTEG-VPC-CONV-V2", "PEER2_PO_DESC": "INTEG-VPC-CONV-V2",
        "PEER1_PO_CONF": "", "PEER2_PO_CONF": ""}}
    return ctrl
