"""Membership controllers and previews for existing PVLAN port-channels and vPCs."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P
from . import port_channel_controller as H
from . import vpc_controller as V
from . import port_channel_release as RR
from .port_channel_controller import PoLifecycleController
from .fixture_cases import load_case


PAIR = (V.PRIMARY, V.SECONDARY)
ROUTED = "int_routed_host"
E7, E9, E10 = "Ethernet1/7", "Ethernet1/9", "Ethernet1/10"


def member_nv(port):
    return {"PO_ID": H.PO, "PC_MODE": "active", "PVLAN_MODE": "host", "CDP_ENABLE": "true", "lldpTransmit": "false", "lldpReceive": "false",
            "LACP_PORT_PRIO": "32768", "LACP_RATE": "normal", "DESC": "", "CONF": "", "ADMIN_STATE": "false", "INTF_NAME": port}


class MembershipPo(PoLifecycleController):
    """PoLifecycleController + the SIMULATED effect of a membership modify of the port-channel. `released_policy` / `released_nv(port)`
    give the release of a removed port (default: the measured-shape int_trunk_host, ADMIN_STATE "true"); `keep_claim` leaves the removed
    port as a member (the controller did not release it); routed releases get their measured own children (no_shut -> shut on a down
    modify, DERIVED)."""

    released_policy = V.TRUNK
    keep_claim = False

    def released_nv(self, port):
        if self.released_policy == ROUTED:
            nv = copy.deepcopy(RR.RELEASED_ROUTED)
            nv["INTF_NAME"] = port
            return nv
        nv = V.trunk_host_nv(port)
        nv["ADMIN_STATE"] = "true"
        return nv

    def __call__(self, mod, method, path, data=None):
        before = None
        body = json.loads(data) if (method == "POST" and path.endswith(V.MODIFY)) else None
        po_update = body and any(p.get("policy") == H.PO_HOST for p in body)
        if po_update:
            before = set(P.normalize_member_list(self.detail[H.PO]["nvPairs"].get("MEMBER_INTERFACES"))[0])
        resp = super(MembershipPo, self).__call__(mod, method, path, data)
        if po_update and str((resp.get("DATA") or [{}])[0].get("reportItemType", "")).upper() == "SUCCESS":
            after = set(P.normalize_member_list(self.detail[H.PO]["nvPairs"].get("MEMBER_INTERFACES"))[0])
            for port in sorted(after - before):
                name = "Ethernet" + port[len("ethernet"):]
                self.detail[name] = {"policy": H.PO_MEMBER, "nvPairs": member_nv(name)}
            for port in sorted(before - after):
                name = "Ethernet" + port[len("ethernet"):]
                if self.keep_claim:
                    continue
                self.detail[name] = {"policy": self.released_policy, "nvPairs": self.released_nv(name)}
                if self.released_policy == ROUTED:
                    self.policies_extra = self.policies_extra + RR.child_policies(name, RR.CHILDREN_UP)
        if body and not po_update:  # a released routed member set down: its own up child becomes the down child (DERIVED)
            for payload in body:
                for intf in payload["interfaces"]:
                    if payload["policy"] == ROUTED and intf["nvPairs"].get("ADMIN_STATE") == "false":
                        for p in self.policies_extra:
                            if p["entityName"] == intf["ifName"] and p["templateName"] == "no_shut_interface":
                                p["templateName"], p["priority"] = "shut_interface", 458
        return resp

    def po_modifies(self):
        return [b for b in self.modify_bodies() if any(p.get("policy") == H.PO_HOST for p in b)]

    def member_modifies(self):
        return [b for b in self.modify_bodies() if not any(p.get("policy") == H.PO_HOST for p in b)]


def seeded(members=(E7, E9), spare=(E10,), **knobs):
    ctrl = PoLifecycleController()
    ctrl.__class__ = MembershipPo
    nv = P.po_host_nvpairs(H.po_item(members=list(members))["profile"], H.PO)
    ctrl.detail[H.PO] = {"policy": H.PO_HOST, "nvPairs": nv}
    ctrl.po_names.add(H.PO)
    for port in members:
        ctrl.detail[port] = {"policy": H.PO_MEMBER, "nvPairs": member_nv(port)}
    for port in spare:
        tnv = V.trunk_host_nv(port)
        tnv["ADMIN_STATE"] = "false"
        ctrl.detail[port] = {"policy": V.TRUNK, "nvPairs": tnv}
    for k, v in knobs.items():
        setattr(ctrl, k, v)
    return ctrl


def strip_vpc(lines):
    return [line for line in lines if line.strip() != "vpc 10"]


def fragments(kept=(), added=(), removed_trunk=(), removed_routed=()):
    """One switch preview from per-port fragments (see the module docstring for what is simulated)."""
    pend, run, exp = [], strip_vpc(V.po_stanza(PAIR)), strip_vpc(V.po_stanza(PAIR))
    for port in kept:
        run += V.member_after(port, PAIR)
        exp += V.member_after(port, PAIR)
    for port in added:
        pend += V.create_pending(port, PAIR)[len(V.po_stanza(PAIR)):]
        run += V.member_running_baseline(port)
        exp += V.member_after(port, PAIR)
    for port in removed_trunk:
        d = P.preview_entry(V.delete_preview(V.SN1, port, PAIR), V.SN1)
        pend += d["pendingConfig"][1:]
        run += V.member_after(port, PAIR)
        exp += d["expectedConfig"]
    for port in removed_routed:
        p_, _r, e_ = RR.routed_release_preview(port=port, po_number="10", pair=PAIR)
        pend += p_[1:]
        run += V.member_after(port, PAIR)
        exp += e_
    return H.preview(pend, running=run, expected=exp)


def item(members, **kw):
    return H.po_item(members=members, **kw)


def run(ctrl, cfg, state):
    return H.run(ctrl, [cfg], state=state)


# ================================================================== vPC: membership per peer (one peer or both)
E9P = "Ethernet1/9"


class MembershipVpc(V.VpcController):
    """VpcController + the SIMULATED release of the ports a parent modify removes (the harness already turns added ports into members):
    int_trunk_host ADMIN_STATE "true", or the measured routed form with its own children (`routed_ports`)."""

    routed_ports = frozenset()
    unsafe_ports = frozenset()

    def __call__(self, mod, method, path, data=None):
        before = {}
        body = json.loads(data) if (method == "POST" and path.endswith(V.MODIFY)) else None
        vpc_update = body and any(p.get("policy") == V.VPC_HOST for p in body)
        if vpc_update and V.VPC in self.parents:
            nv = self.parents[V.VPC]["nvPairs"]
            before = dict((s, set(P.normalize_member_list(nv["PEER%d_MEMBER_INTERFACES" % n])[0])) for n, s in ((1, V.SN1), (2, V.SN2)))
        resp = super(MembershipVpc, self).__call__(mod, method, path, data)
        if vpc_update and before and V.VPC in self.parents:
            nv = self.parents[V.VPC]["nvPairs"]
            for n, serial in ((1, V.SN1), (2, V.SN2)):
                after = set(P.normalize_member_list(nv["PEER%d_MEMBER_INTERFACES" % n])[0])
                for port in sorted(before[serial] - after):
                    name = "Ethernet" + port[len("ethernet"):]
                    if (serial, name) in self.routed_ports:
                        rnv = copy.deepcopy(RR.RELEASED_ROUTED)
                        rnv["INTF_NAME"] = name
                        self.nodes[serial][name] = {"policy": ROUTED, "nvPairs": rnv}
                        self.policies_extra[serial] += RR.child_policies(name, RR.CHILDREN_UP, serial)
                    else:
                        tnv = V.trunk_host_nv(name)
                        tnv["ADMIN_STATE"] = "true"
                        if (serial, name) in self.unsafe_ports:
                            tnv["ALLOWED_VLANS"] = "all"
                        self.nodes[serial][name] = {"policy": V.TRUNK, "nvPairs": tnv}
        if body and not vpc_update:
            for payload in body:
                for intf in payload["interfaces"]:
                    if payload["policy"] == ROUTED and intf["nvPairs"].get("ADMIN_STATE") == "false":
                        for p in self.policies_extra[intf["serialNumber"]]:
                            if p["entityName"] == intf["ifName"] and p["templateName"] == "no_shut_interface":
                                p["templateName"], p["priority"] = "shut_interface", 458
        return resp

    def parent_modifies(self):
        return [json.loads(c[2]) for c in self.modifies() if any(p.get("policy") == V.VPC_HOST for p in json.loads(c[2]))]

    def member_modifies(self):
        return [json.loads(c[2]) for c in self.modifies() if not any(p.get("policy") == V.VPC_HOST for p in json.loads(c[2]))]


def vpc_seeded(ports, spare=None):
    ctrl = V.VpcController()
    for serial, plist in ports.items():
        for port in plist:
            nv = V.trunk_host_nv(port)
            nv["ADMIN_STATE"] = "false"
            ctrl.nodes[serial][port] = {"policy": V.TRUNK, "nvPairs": nv}
    ctrl = ctrl.seed_vpc()
    nv = ctrl.parents[V.VPC]["nvPairs"]
    for n, serial in ((1, V.SN1), (2, V.SN2)):
        nv["PEER%d_MEMBER_INTERFACES" % n] = ",".join(ports[serial])
    ctrl._expand_children(nv)
    for serial, plist in (spare or {}).items():
        for port in plist:
            tnv = V.trunk_host_nv(port)
            tnv["ADMIN_STATE"] = "false"
            ctrl.nodes[serial][port] = {"policy": V.TRUNK, "nvPairs": tnv}
    ctrl.next_invocation()
    ctrl.__class__ = MembershipVpc
    return ctrl


def peer_preview(serial, kept=(), added=(), removed_trunk=(), removed_routed=(), prior=False):
    """One peer's preview from fragments: `prior` = the current state before the modify (added ports still standalone, removed still members)."""
    pend, run, exp = [], list(V.po_stanza(PAIR)), list(V.po_stanza(PAIR))
    for port in list(kept) + (list(removed_trunk) + list(removed_routed) if prior else []):
        run += V.member_after(port, PAIR)
        exp += V.member_after(port, PAIR)
    for port in added:
        run += V.member_running_baseline(port)
        if prior:
            exp += V.member_running_baseline(port)
        else:
            pend += V.create_pending(port, PAIR)[len(V.po_stanza(PAIR)):]
            exp += V.member_after(port, PAIR)
    if not prior:
        for port in removed_trunk:
            d = P.preview_entry(V.delete_preview(serial, port, PAIR), serial)
            pend += d["pendingConfig"][1:]
            run += V.member_after(port, PAIR)
            exp += d["expectedConfig"]
        for port in removed_routed:
            p_, _r, e_ = RR.routed_release_preview(port=port, po_number="10", pair=PAIR)
            pend += p_[1:]
            run += V.member_after(port, PAIR)
            exp += e_
    return V.preview(pend, serial=serial, running=run, expected=exp)


def queue_peer(ctrl, serial, **kw):
    ctrl.vpc_previews[serial] = [peer_preview(serial, prior=True, **kw), peer_preview(serial, **kw)]


PORTS = {V.SN1: [V.M1, "Ethernet1/9", "Ethernet1/10"], V.SN2: [V.M2, "Ethernet1/11"]}


def vpc_baseline():
    ctrl = V.VpcController()
    for serial, ports in PORTS.items():
        for port in ports:
            nv = V.trunk_host_nv(port)
            nv["ADMIN_STATE"] = "false"
            ctrl.nodes[serial][port] = {"policy": V.TRUNK, "nvPairs": nv}
    return ctrl


def vpc_item(**kw):
    return V.vpc_item(peer1_members=PORTS[V.SN1], peer2_members=PORTS[V.SN2], **kw)


def combine_previews(serial, ports, factory, *args):
    """One switch preview, assembled from existing explicit per-port fixtures."""
    entries = [P.preview_entry(factory(serial, port, *args), serial) for port in ports]
    fields = {}
    for key in ("pendingConfig", "runningConfig", "expectedConfig"):
        lines = []
        for i, entry in enumerate(entries):
            current = None
            for line in entry[key]:
                if line.lower().strip().startswith("interface "):
                    current = line.lower().strip()[10:]
                if i and (current == "port-channel10" or line.lower().strip() == "no interface port-channel10"):
                    continue
                lines.append(line)
        fields[key] = lines
    return V.preview(fields["pendingConfig"], serial=serial, running=fields["runningConfig"], expected=fields["expectedConfig"])


def queue(ctrl, factory, *args):
    for serial, ports in PORTS.items():
        ctrl.vpc_previews[serial].append(combine_previews(serial, ports, factory, *args))


def seeded_vpc():
    ctrl = vpc_baseline().seed_vpc()
    nv = ctrl.parents[V.VPC]["nvPairs"]
    for n, serial in enumerate((V.SN1, V.SN2), 1):
        nv["PEER%d_MEMBER_INTERFACES" % n] = ",".join(PORTS[serial])
    ctrl._expand_children(nv)
    ctrl.next_invocation()
    return ctrl


FX = load_case("pvlan_admin_up_join_measured")


LEAF_A, LEAF_B = "<SERIAL_LEAF_A>", "<SERIAL_LEAF_B>"


def transpose(lines, number, port, to_port):
    """A measured stanza list renamed to the harness: port-channel<number> -> port-channel10, its channel-group and vpc ids -> 10."""
    out = []
    for line in lines:
        line = line.replace("port-channel%s" % number, "port-channel10").replace("channel-group %s " % number, "channel-group 10 ")
        line = line.replace("vpc %s" % number, "vpc 10").replace("interface %s" % port, "interface %s" % to_port.lower())
        out.append(line)
    return out


def measured(case, phase, serial, number, port, to_port):
    m = FX[case][phase][serial]
    return dict((k, transpose(m[k], number, port, to_port)) for k in ("pending", "expected", "running"))


def vpc_preview(serial, to_port, phase="pre_deploy", serial_fx=LEAF_A, mutate=None):
    m = measured("M3", phase, serial_fx, "575", "ethernet1/16", to_port)
    if mutate:
        mutate(m)
    return V.preview(m["pending"], serial=serial, running=m["running"], expected=m["expected"])


def shut_the_member(m):
    """The pending a controller would produce if it shut the joining member (never measured): its `no shutdown` becomes `shutdown`."""
    idx = max(i for i, line in enumerate(m["pending"]) if line.strip() == "no shutdown")
    m["pending"][idx] = "  shutdown"


# ================================================================== vPC through main()
def up_peers(ctrl, peers=(V.SN1, V.SN2)):
    for serial in peers:
        port = V.M1 if serial == V.SN1 else V.M2
        ctrl.nodes[serial][port]["nvPairs"]["ADMIN_STATE"] = "true"
