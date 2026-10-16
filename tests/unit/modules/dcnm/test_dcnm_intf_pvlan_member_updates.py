"""MM-B: membership of an EXISTING PVLAN port-channel / vPC: add and remove members under the regular rule.

Regular port-channel rule (dcnm_intf_compare_elements / dcnm_intf_merge_want_and_have): `merged` is the union of HAVE and the requested
members (an omitted `members` keeps HAVE); `replaced` states the exact membership. PVLAN keeps one deliberate difference, documented: an
omitted or empty list in `replaced` (which the regular module sends as an empty MEMBER_INTERFACES) is refused, because an empty member
list is not implemented.

SIMULATED, NOT MEASURED: the controller effect of a membership modify (an added port becomes int_port_channel_pvlan_member of the
port-channel; a removed port is released as int_trunk_host -- or int_routed_host, the Q56 MEASURED form -- with ADMIN_STATE "true", like a
deleted port-channel's member) and the per-member preview fragments (added: the H1 MEASURED creation form `channel-group N force`; removed:
the deletion form `no channel-group N force` with the release; existing: converged). Real main(); only the controller boundary is
intercepted (existing Po/vPC harnesses, subclassed here).
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from . import test_dcnm_intf_pvlan_po_host as H
from . import test_dcnm_intf_pvlan_vpc_harness as V
from . import test_dcnm_intf_pvlan_release_routed as RR
from .test_dcnm_intf_pvlan_po_g1 import PoLifecycleController

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


# ------------------------------------------------------------------ adding members (merged and replaced)
@pytest.mark.parametrize("state, requested, final", [
    ("merged", [E10], {E7, E9, E10}),
    ("merged", [E7, E10], {E7, E9, E10}),
    ("replaced", [E7, E9, E10], {E7, E9, E10}),
])
def test_adding_a_member_joins_it_through_the_force_form_and_keeps_the_others(state, requested, final):
    ctrl = seeded()
    ctrl.previews = [fragments(kept=(E7, E9), added=(E10,))]
    status, result = run(ctrl, item(requested), state)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.po_modifies()) == 1 and ctrl.member_modifies() == [] and len(ctrl.deploys()) == 1
    sent = ctrl.po_modifies()[0][0]["interfaces"][0]["nvPairs"]["MEMBER_INTERFACES"]
    assert P.normalize_member_list(sent)[0] == set(p.lower() for p in final)
    assert ctrl.detail[E10]["policy"] == H.PO_MEMBER


def test_one_to_three_members():
    ctrl = seeded(members=(E7,), spare=(E9, E10))
    ctrl.previews = [fragments(kept=(E7,), added=(E9, E10))]
    status, result = run(ctrl, item([E9, E10]), "merged")
    assert status == "exit", result.get("msg")
    assert P.normalize_member_list(ctrl.detail[H.PO]["nvPairs"]["MEMBER_INTERFACES"])[0] == {"ethernet1/7", "ethernet1/9", "ethernet1/10"}


@pytest.mark.parametrize("state, requested", [("merged", ["e1/9", "Ethernet1/7"]), ("replaced", ["e1/9", "eth1/7"]), ("merged", [E7])])
def test_reorder_alias_and_subset_in_merged_are_no_ops(state, requested):
    ctrl = seeded()
    ctrl.previews = [fragments(kept=(E7, E9))]
    status, result = run(ctrl, item(requested), state)
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.writes() == []


def test_merged_with_members_omitted_keeps_every_member():
    ctrl = seeded()
    run_ = strip_vpc(V.po_stanza(PAIR)) + V.member_after(E7, PAIR) + V.member_after(E9, PAIR)
    exp_ = strip_vpc(V.po_stanza(PAIR, desc="x")) + V.member_after(E7, PAIR) + V.member_after(E9, PAIR)
    ctrl.previews = [H.preview(["interface port-channel10", "  description x"], running=run_, expected=exp_)]
    cfg = item([E7], description="x")
    del cfg["profile"]["members"]
    status, result = run(ctrl, cfg, "merged")
    assert status == "exit", result.get("msg")
    assert P.normalize_member_list(ctrl.detail[H.PO]["nvPairs"]["MEMBER_INTERFACES"])[0] == {"ethernet1/7", "ethernet1/9"}


# ------------------------------------------------------------------ removing members (replaced): release before the deploy
def test_replaced_removes_a_member_and_releases_it_down_before_the_deploy():
    ctrl = seeded()
    ctrl.previews = [fragments(kept=(E7,), removed_trunk=(E9,))]
    status, result = run(ctrl, item([E7]), "replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.order().index("DEPLOY") > max(i for i, x in enumerate(ctrl.order()) if x == "MODIFY")
    assert len(ctrl.po_modifies()) == 1 and len(ctrl.member_modifies()) == 1 and len(ctrl.deploys()) == 1
    payload = ctrl.member_modifies()[0][0]
    assert payload["policy"] == V.TRUNK and payload["interfaces"][0]["ifName"] == E9 and payload["interfaces"][0]["nvPairs"]["ADMIN_STATE"] == "false"
    assert ctrl.detail[E9]["policy"] == V.TRUNK and ctrl.detail[E9]["nvPairs"]["ADMIN_STATE"] == "false"
    record = [r for r in result["pvlan_po_release"] if r["member"] == E9][0]
    assert record["release_context"] == "update" and record["released_policy"] == V.TRUNK


def test_replaced_removal_with_the_q56_routed_release_keeps_the_routed_policy():
    ctrl = seeded(released_policy=ROUTED)
    ctrl.previews = [fragments(kept=(E7,), removed_routed=(E9,))]
    status, result = run(ctrl, item([E7]), "replaced")
    assert status == "exit", result.get("msg")
    payload = ctrl.member_modifies()[0][0]
    assert payload["policy"] == ROUTED and payload["interfaces"][0]["nvPairs"]["ADMIN_STATE"] == "false"
    assert ctrl.detail[E9]["policy"] == ROUTED


def test_replaced_swap_adds_one_member_and_removes_another():
    ctrl = seeded()
    ctrl.previews = [fragments(kept=(E7,), added=(E10,), removed_trunk=(E9,))]
    status, result = run(ctrl, item([E7, E10]), "replaced")
    assert status == "exit", result.get("msg")
    assert ctrl.detail[E10]["policy"] == H.PO_MEMBER and ctrl.detail[E9]["policy"] == V.TRUNK
    assert [b[0]["interfaces"][0]["ifName"] for b in ctrl.member_modifies()] == [E9]


def test_a_second_replaced_run_after_the_removal_writes_nothing():
    ctrl = seeded()
    ctrl.previews = [fragments(kept=(E7,), removed_trunk=(E9,))]
    assert run(ctrl, item([E7]), "replaced")[0] == "exit"
    ctrl.next_invocation()
    ctrl.calls = []
    ctrl.previews = [fragments(kept=(E7,))]
    status, result = run(ctrl, item([E7]), "replaced")
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.writes() == []


# ------------------------------------------------------------------ refused before any write
@pytest.mark.parametrize("members, needle", [(None, "states the exact member list"), ([], "")])
def test_replaced_without_an_explicit_member_list_is_refused_before_any_write(members, needle):
    ctrl = seeded()
    cfg = item([E7])
    if members is None:
        del cfg["profile"]["members"]
    else:
        cfg["profile"]["members"] = members
    status, result = run(ctrl, cfg, "replaced")
    assert status == "fail" and needle in result["msg"] and ctrl.writes() == [], result.get("msg")


@pytest.mark.parametrize("change, needle", [
    # RELEASE-ADMIN: an up member is released to the fabric default; an unknown administrative state stays refused
    (lambda c: c.detail[E9]["nvPairs"].update(ADMIN_STATE="maybe"), "unknown administrative state"),
    (lambda c: setattr(c, "policies_extra", [{"entityName": E9, "entityType": "INTERFACE", "templateName": "Config_Profile", "source": "OVERLAY",
                                              "deleted": False, "policyId": "POLICY-990100", "priority": 500, "serialNumber": "x"}]),
     "live policies are not exactly those of"),
])
def test_an_unsafe_member_to_remove_is_refused_before_any_write(change, needle):
    ctrl = seeded()
    change(ctrl)
    status, result = run(ctrl, item([E7]), "replaced")
    assert status == "fail" and needle in result["msg"] and ctrl.writes() == [], result.get("msg")


def test_removal_without_deploy_is_saved_released_and_never_deployed():
    # LIFECYCLE-B (was: refused): deploy false SAVES the removal -- the parent's modify, the removed member released administratively
    # down, the pending validated by the pre-deploy gate -- and sends no deployment request.
    ctrl = seeded()
    ctrl.previews = [fragments(kept=(E7,), removed_trunk=(E9,))]
    status, result = run(ctrl, item([E7], deploy=False), "replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.po_modifies()) == 1 and len(ctrl.member_modifies()) == 1 and ctrl.deploys() == []
    assert ctrl.detail[E9]["nvPairs"]["ADMIN_STATE"] == "false"
    assert [r["operation"] for r in result["pvlan_saved"]] == ["remove member"]


@pytest.mark.parametrize("policy, needle", [(H.PO_MEMBER, "already a port-channel member"), ("int_access_host", "is not covered")])
def test_an_unsuitable_member_to_add_is_refused_before_any_write(policy, needle):
    ctrl = seeded()
    ctrl.detail[E10] = {"policy": policy, "nvPairs": dict(member_nv(E10), PO_ID="Port-channel99") if policy == H.PO_MEMBER else
                        {"ADMIN_STATE": "false", "INTF_NAME": E10}}
    status, result = run(ctrl, item([E10]), "merged")
    assert status == "fail" and needle in result["msg"] and ctrl.writes() == [], result.get("msg")


# ------------------------------------------------------------------ failures after the parent's modify: never a deploy
def test_an_unsafe_release_of_the_removed_member_stops_before_any_member_write():
    class Unsafe(MembershipPo):
        def released_nv(self, port):
            nv = super(Unsafe, self).released_nv(port)
            nv["ALLOWED_VLANS"] = "all"
            return nv
    ctrl = seeded()
    ctrl.__class__ = Unsafe
    status, result = run(ctrl, item([E7]), "replaced")
    assert status == "fail" and "ALLOWED_VLANS" in result["msg"], result.get("msg")
    assert "pending membership update" in result["msg"] and "membership update of Port-channel10 (per-item SUCCESS)" in result["msg"]
    assert len(ctrl.po_modifies()) == 1 and ctrl.member_modifies() == [] and ctrl.deploys() == []


def test_a_207_error_on_the_removed_member_modify_stops_before_the_deploy():
    ctrl = seeded()
    ctrl.modify_responses = [None, {"RETURN_CODE": 207, "MESSAGE": "Multi-Status",
                                    "DATA": [{"reportItemType": "ERROR", "message": "synthetic", "entity": H.SERIAL + "~" + E9}]}]
    status, result = run(ctrl, item([E7]), "replaced")
    assert status == "fail" and "ERROR item" in result["msg"] and "at the member modify" in result["msg"], result.get("msg")
    assert ctrl.deploys() == []


def test_a_removed_member_still_claimed_after_the_modify_stops_before_any_member_write():
    ctrl = seeded(keep_claim=True)
    status, result = run(ctrl, item([E7]), "replaced")
    assert status == "fail" and "still claimed by the port-channel" in result["msg"], result.get("msg")
    assert ctrl.member_modifies() == [] and ctrl.deploys() == []


def test_a_stale_preview_for_the_removed_member_refuses_the_deploy():
    ctrl = seeded()
    ctrl.previews = [fragments(kept=(E7, E9))]  # the removed member's withdrawal is absent from the pending
    status, result = run(ctrl, item([E7]), "replaced")
    assert status == "fail" and "No deployment request was sent" in result["msg"], result.get("msg")
    assert len(ctrl.member_modifies()) == 1 and ctrl.deploys() == []


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


def test_vpc_adding_a_member_on_one_peer_only_keeps_the_other_peer():
    ctrl = vpc_seeded({V.SN1: [V.M1], V.SN2: [V.M2]}, spare={V.SN1: [E9P]})
    queue_peer(ctrl, V.SN1, kept=(V.M1,), added=(E9P,))
    queue_peer(ctrl, V.SN2, kept=(V.M2,))
    item = V.vpc_item(peer1_members=[V.M1, E9P])
    status, result = V.run_vpc(ctrl, [item])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.parent_modifies()) == 1 and ctrl.member_modifies() == [] and len(ctrl.deploys()) == 1
    nv = ctrl.parents[V.VPC]["nvPairs"]
    assert P.normalize_member_list(nv["PEER1_MEMBER_INTERFACES"])[0] == {"ethernet1/7", "ethernet1/9"}
    assert P.normalize_member_list(nv["PEER2_MEMBER_INTERFACES"])[0] == {V.M2.lower()}
    assert ctrl.nodes[V.SN1][E9P]["policy"] == V.PO_MEMBER


def test_vpc_adding_members_on_both_peers():
    ctrl = vpc_seeded({V.SN1: [V.M1], V.SN2: [V.M2]}, spare={V.SN1: [E9P], V.SN2: [E9P]})
    queue_peer(ctrl, V.SN1, kept=(V.M1,), added=(E9P,))
    queue_peer(ctrl, V.SN2, kept=(V.M2,), added=(E9P,))
    status, result = V.run_vpc(ctrl, [V.vpc_item(peer1_members=[E9P], peer2_members=[E9P])])
    assert status == "exit", result.get("msg")
    assert ctrl.nodes[V.SN1][E9P]["policy"] == V.PO_MEMBER and ctrl.nodes[V.SN2][E9P]["policy"] == V.PO_MEMBER


def test_vpc_reordered_aliases_are_a_no_op():
    ctrl = vpc_seeded({V.SN1: [V.M1, E9P], V.SN2: [V.M2]})
    queue_peer(ctrl, V.SN1, kept=(V.M1, E9P))
    queue_peer(ctrl, V.SN2, kept=(V.M2,))
    status, result = V.run_vpc(ctrl, [V.vpc_item(peer1_members=["e1/9", "eth1/7"])], state="replaced")
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.writes() == []


@pytest.mark.parametrize("routed", [False, True])
def test_vpc_replaced_removes_a_member_of_one_peer_and_releases_it_down_before_the_deploy(routed):
    ctrl = vpc_seeded({V.SN1: [V.M1, E9P], V.SN2: [V.M2]})
    if routed:
        ctrl.routed_ports = frozenset([(V.SN1, E9P)])
        queue_peer(ctrl, V.SN1, kept=(V.M1,), removed_routed=(E9P,))
    else:
        queue_peer(ctrl, V.SN1, kept=(V.M1,), removed_trunk=(E9P,))
    queue_peer(ctrl, V.SN2, kept=(V.M2,))
    status, result = V.run_vpc(ctrl, [V.vpc_item(peer1_members=[V.M1], peer2_members=[V.M2])], state="replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    mods = ctrl.member_modifies()
    assert len(mods) == 1 and mods[0][0]["interfaces"][0]["ifName"] == E9P and mods[0][0]["interfaces"][0]["serialNumber"] == V.SN1
    assert mods[0][0]["policy"] == (ROUTED if routed else V.TRUNK) and mods[0][0]["interfaces"][0]["nvPairs"]["ADMIN_STATE"] == "false"
    order = ctrl.order()
    assert max(i for i, x in enumerate(order) if x == "MODIFY") < order.index("DEPLOY")
    record = [r for r in result["pvlan_vpc_release"] if r.get("member") == E9P][0]
    assert record["release_context"] == "update" and record["released_policy"] == (ROUTED if routed else V.TRUNK)


def test_vpc_replaced_without_a_peer_member_list_is_refused_before_any_write():
    ctrl = vpc_seeded({V.SN1: [V.M1], V.SN2: [V.M2]})
    item = V.vpc_item()
    del item["profile"]["peer2_members"]
    status, result = V.run_vpc(ctrl, [item], state="replaced")
    assert status == "fail" and "states the exact member list of each peer" in result["msg"] and ctrl.writes() == [], result.get("msg")


def test_a_unilateral_change_that_is_not_membership_stays_refused():
    ctrl = vpc_seeded({V.SN1: [V.M1], V.SN2: [V.M2]})
    # A1: a one-peer description is supported now; the freeform of one peer is the still-refused example
    status, result = V.run_vpc(ctrl, [V.vpc_item(peer1_cmds=["logging event port link-status"])])
    assert status == "fail" and "changes only peer 1" in result["msg"] and ctrl.writes() == [], result.get("msg")


def test_vpc_removing_a_member_whose_admin_state_is_unknown_is_refused_before_any_write():
    # RELEASE-ADMIN: an up member is released to the fabric default (test_dcnm_intf_pvlan_release_admin.py); unknown stays refused
    ctrl = vpc_seeded({V.SN1: [V.M1, E9P], V.SN2: [V.M2]})
    ctrl.nodes[V.SN1][E9P]["nvPairs"]["ADMIN_STATE"] = "maybe"
    status, result = V.run_vpc(ctrl, [V.vpc_item(peer1_members=[V.M1], peer2_members=[V.M2])], state="replaced")
    assert status == "fail" and "administrative state is unknown" in result["msg"] and ctrl.writes() == [], result.get("msg")


def test_vpc_unsafe_release_of_a_removed_member_stops_before_any_member_write_and_deploy():
    ctrl = vpc_seeded({V.SN1: [V.M1, E9P], V.SN2: [V.M2]})
    ctrl.unsafe_ports = frozenset([(V.SN1, E9P)])
    queue_peer(ctrl, V.SN1, kept=(V.M1,), removed_trunk=(E9P,))
    queue_peer(ctrl, V.SN2, kept=(V.M2,))
    status, result = V.run_vpc(ctrl, [V.vpc_item(peer1_members=[V.M1], peer2_members=[V.M2])], state="replaced")
    assert status == "fail" and "ALLOWED_VLANS" in result["msg"] and "membership update of the vPC" in result["msg"], result.get("msg")
    assert len(ctrl.parent_modifies()) == 1 and ctrl.member_modifies() == [] and ctrl.deploys() == []


def test_po_removed_routed_member_with_an_up_child_after_the_deploy_fails_verification_without_another_write():
    class Reappears(MembershipPo):
        def __call__(self, mod, method, path, data=None):
            resp = super(Reappears, self).__call__(mod, method, path, data)
            if method == "POST" and path.endswith(V.DEPLOY):
                self.policies_extra = self.policies_extra + [RR.own(E9, "no_shut_interface", prio=452)]
            return resp
    ctrl = seeded(released_policy=ROUTED)
    ctrl.__class__ = Reappears
    ctrl.previews = [fragments(kept=(E7,), removed_routed=(E9,))]
    status, result = run(ctrl, item([E7]), "replaced")
    assert status == "fail" and "could not be verified as released after 6 readback attempts" in result["msg"], result.get("msg")
    assert len(ctrl.deploys()) == 1 and len(ctrl.member_modifies()) == 1
