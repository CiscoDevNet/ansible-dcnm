"""vPC PVLAN mode controllers (promiscuous, trunk promiscuous, trunk secondary)."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P
from .vpc_controller import IP1, IP2, M1, M2, SN1, SN2, VPC, VpcController, member_running_baseline, preview
from .fixture_cases import load_case


EXP1 = load_case("pvlan_po_ts_exp1_measured")
P_, TP, TS = "promiscuous", "trunk promiscuous", "trunk secondary"
KEYWORD = {P_: "mapping", TP: "mapping trunk", TS: "association trunk"}


# ---------------------------------------------------------------- SYNTHETIC stanzas (templates [SRC]), per submode
def pvlan_lines(mode, pairs, native="", allowed=""):
    out = ["switchport private-vlan trunk native vlan %s" % native] if native and native != "1" else []
    out += ["switchport private-vlan trunk allowed vlan %s" % allowed] if allowed else []
    return out + ["switchport private-vlan %s %d %d" % ((KEYWORD[mode],) + p) for p in pairs]


def po_stanza(mode, pairs, native="", allowed="", desc=None):
    lines = ["interface port-channel10", "  switchport", "  switchport mode private-vlan %s" % mode]
    lines += ["  " + x for x in pvlan_lines(mode, pairs, native, allowed)]
    lines += ["  mtu 9216", "  vpc 10", "  spanning-tree bpduguard enable", "  spanning-tree port type edge trunk"]
    return lines + (["  description %s" % desc] if desc else []) + ["  shutdown"]


def member_after(port, mode, pairs, native="", allowed=""):
    return (
        ["interface %s" % port, "  switchport", "  switchport mode private-vlan %s" % mode]
        + ["  " + x for x in pvlan_lines(mode, pairs, native, allowed)]
        + ["  mtu 9216", "  channel-group 10 mode active", "  shutdown"]
    )


ACCESS_RUNNING = ["shutdown", "spanning-tree port type edge", "mtu 9216"]  # MEASURED (regular Po)


def create_preview(serial, port, mode, pairs, native="", allowed="", baseline="trunk"):
    """The creation pending of ONE peer: the child Po's full stanza and the member join with the force COMMAND (MEASURED shape of a regular Po:
    trunk member -> `no ... edge trunk`; access member -> `no ... edge`)."""
    lowered = port.lower()
    edge = "  no spanning-tree port type edge trunk" if baseline == "trunk" else "  no spanning-tree port type edge"
    running = member_running_baseline(port) if baseline == "trunk" else ["interface %s" % port] + ["  " + x for x in ACCESS_RUNNING]
    pend = po_stanza(mode, pairs, native, allowed) + [
        "interface %s" % lowered,
        edge,
        "configure terminal",
        "interface %s" % lowered,
        "  channel-group 10 force mode active",
        "  shutdown",
        "configure terminal",
    ]
    return preview(pend, serial=serial, running=running, expected=po_stanza(mode, pairs, native, allowed) + member_after(port, mode, pairs, native, allowed))


def converged_preview(serial, port, mode, pairs, native="", allowed=""):
    state = po_stanza(mode, pairs, native, allowed) + member_after(port, mode, pairs, native, allowed)
    return preview([], serial=serial, running=state, expected=state)


# ---------------------------------------------------------------- items and seeded states
MAP_P = [{"primary_vlan": 2210, "secondary_vlans": "2212"}]
MAP_TP = [{"primary_vlan": 2210, "secondary_vlans": "2211-2212"}]
ASSOC_TS = [{"primary_vlan": 2210, "secondary_vlan": 2212}]
PAIRS = {P_: [(2210, 2212)], TP: [(2210, 2211), (2210, 2212)], TS: [(2210, 2212)]}
# Per-peer trunk fields, DIFFERENT per peer so a crossed binding is visible: playbook peer1 -> switch[0].
TRUNK_FIELDS = {"peer1_native_vlan": "2301", "peer1_allowed_vlans": "2301", "peer2_native_vlan": "2302", "peer2_allowed_vlans": "2302"}


def item(mode, switches=None, deploy=True, **extra):
    prof = {"mode": "pvlan", "pvlan_mode": mode, "peer1_members": [M1], "peer2_members": [M2], "peer1_pcid": 10, "peer2_pcid": 10, "admin_state": False}
    if mode in (P_, TP):
        prof["pvlan_mapping"] = MAP_P if mode == P_ else MAP_TP
    else:
        prof["pvlan_association"] = ASSOC_TS
    if mode in (TP, TS):
        prof.update(TRUNK_FIELDS)
    prof.update(extra)
    prof = dict((k, v) for k, v in prof.items() if v is not None)
    return {"name": "vpc10", "type": "vpc", "switch": list(switches or [IP1, IP2]), "deploy": deploy, "profile": prof}


def per_peer(mode, index):
    """(native, allowed) of the controller's n-th peer for the seeded/created vPC."""
    if mode not in (TP, TS):
        return "", ""
    return ("2301", "2301") if index == 0 else ("2302", "2302")


def prepared_access_nv(port):
    nv = dict((k, v) for k, v in EXP1["branches"]["A"]["member_before"]["intent"]["Ethernet1/8"]["nvPairs"].items() if k != "POLICY_ID")
    nv["INTF_NAME"] = port
    return nv


def baseline_ctrl(mode):
    ctrl = VpcController().seed_baseline()
    if mode == TS:
        for serial, port in ((SN1, M1), (SN2, M2)):
            ctrl.nodes[serial][port] = {"policy": P.PO_ACCESS_BASELINE_POLICY, "nvPairs": prepared_access_nv(port)}
    return ctrl


def create_previews(ctrl, mode, pairs=None):
    pairs = pairs or PAIRS[mode]
    base = "access" if mode == TS else "trunk"
    for i, (serial, port) in enumerate(((SN1, M1), (SN2, M2))):
        native, allowed = per_peer(mode, i)
        ctrl.vpc_previews[serial] = [create_preview(serial, port, mode, pairs, native, allowed, base)]


def seeded_ctrl(mode, pairs=None):
    """A coherent, created and deployed vPC of `mode`, seeded BY HAND (SYNTHETIC): the host seed re-labelled to the submode."""
    pairs = pairs or PAIRS[mode]
    ctrl = VpcController().seed_baseline().seed_vpc()
    parent = ctrl.parents[VPC]["nvPairs"]
    key = P.active_list_key(mode)
    parent["PVLAN_MODE"] = mode
    parent["ASSOCIATION_LIST"] = ""
    parent["MAPPING_LIST"] = ""
    parent[key] = P.pairs_to_wire(key, pairs)
    for i in (0, 1):
        native, allowed = per_peer(mode, i)
        parent["PEER%d_PVLAN_NATIVE_VLAN" % (i + 1)] = native
        parent["PEER%d_PVLAN_ALLOWED_VLANS" % (i + 1)] = allowed
    ctrl._expand_children(parent)
    ctrl.next_invocation()
    return ctrl


def converged_previews(ctrl, mode, pairs=None, times=1):
    pairs = pairs or PAIRS[mode]
    for i, (serial, port) in enumerate(((SN1, M1), (SN2, M2))):
        native, allowed = per_peer(mode, i)
        ctrl.vpc_previews[serial] = [converged_preview(serial, port, mode, pairs, native, allowed) for _i in range(times)]


def gate(result):
    """{site: [(peer, serial, target decision)]} exactly as the module recorded it."""
    out = {}
    for rec in result.get("pvlan_gate") or []:
        out.setdefault(rec["site"], []).append((rec["peer"], rec["serial"], rec["targets"].get(VPC)))
    return dict((k, sorted(v)) for k, v in out.items())


def sent_parent(ctrl, calls):
    body = json.loads(calls[-1][2])
    body = body if isinstance(body, list) else [body]
    return body[0]["interfaces"][0]["nvPairs"]


MODES = [P_, TP, TS]


class RoutedVpcController(VpcController):
    """The vPC harness + the MEASURED routed behaviour (regular Po): the prepared routed member's self-sourced children disappear when
    the port-channel is created (`children_vanish`); with it False they stay, which the post-deploy readback must refuse."""

    children_vanish = True

    def __call__(self, mod, method, path, data=None):
        resp = super(RoutedVpcController, self).__call__(mod, method, path, data)
        if method == "POST" and path.endswith("/rest/globalInterface") and self.children_vanish:
            self.policies_extra[SN2] = [p for p in self.policies_extra[SN2] if p.get("templateName") not in P.PO_ROUTED_SELF_CHILDREN]
        return resp


def routed_ctrl(child_source, vanish=True):
    ctrl = RoutedVpcController().seed_baseline()
    ctrl.children_vanish = vanish
    ctrl.nodes[SN1][M1] = {"policy": P.PO_ACCESS_BASELINE_POLICY, "nvPairs": prepared_access_nv(M1)}
    nv = dict((k, v) for k, v in EXP1["branches"]["R"]["member_before"]["intent"]["Ethernet1/8"]["nvPairs"].items() if k != "POLICY_ID")
    nv["INTF_NAME"] = M2
    ctrl.nodes[SN2][M2] = {"policy": P.PO_ROUTED_BASELINE_POLICY, "nvPairs": nv}
    for t in sorted(P.PO_ROUTED_SELF_CHILDREN):
        ctrl.policies_extra[SN2].append(
            {
                "entityName": M2,
                "entityType": "INTERFACE",
                "templateName": t,
                "source": child_source,
                "deleted": False,
                "policyId": "POLICY-R-" + t,
                "priority": 450,
                "serialNumber": SN2,
            }
        )
    for i, (serial, port, base) in enumerate(((SN1, M1, "access"), (SN2, M2, "routed"))):
        native, allowed = per_peer(TS, i)
        pv = create_preview(serial, port, TS, PAIRS[TS], native, allowed, "access")
        if base == "routed":  # MEASURED routed shape (R): running `no switchport / mtu 9216`; no member line before the join
            entry = pv["DATA"][0]
            entry["runningConfig"] = ["!Command: show running-config", "hostname placeholder-sw-1", "interface %s" % port, "  no switchport", "  mtu 9216"]
            entry["pendingConfig"] = [line for line in entry["pendingConfig"] if line != "  no spanning-tree port type edge"]
        ctrl.vpc_previews[serial] = [pv]
    return ctrl
