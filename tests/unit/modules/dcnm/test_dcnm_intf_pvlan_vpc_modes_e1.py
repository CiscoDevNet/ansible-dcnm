"""VPC-MODES-E1 (Alpha): promiscuous, trunk promiscuous and trunk secondary for a vPC in mode 'pvlan' (int_vpc_pvlan_host).

NOT LIVE TESTED. Real main() through the EXISTING vPC harness (VpcController: two peers, per-serial previews). Labels:
  [SRC] the installed templates (VPC-TEMPLATE-READ): the parent's per-submode lists and per-peer PVLAN native/allowed (HOST 192-229,
        604-680), the child Po body (POVPC 217-252) = the regular Po body + `vpc N`;
  [MEASURED elsewhere] the prepared access member of the regular-Po EXP-1 (fixtures/pvlan_po_ts_exp1_measured.json, branch A), and the
        regular-Po pending shapes (force join, parent-only update, `mapping trunk P remove S`);
  SYNTHETIC: every vPC preview below (written by hand from those templates; no vPC of these submodes was ever observed).
Gate records are checked per SITE with the exact peer + serial + target + decision (the host L2 lesson: an update records two `prior`
`converged` decisions plus two `deploy` decisions; never assert a peer list over the whole gate list or call every record `deploy`).
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import os

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .test_dcnm_intf_pvlan_vpc_harness import (
    IP1,
    IP2,
    M1,
    M2,
    PAIR,
    SN1,
    SN2,
    TRUNK,
    VPC,
    VpcController,
    member_running_baseline,
    preview,
    release_only,
    run_vpc,
    vpc_del_item,
)

EXP1 = json.load(open(os.path.join(os.path.dirname(__file__), "fixtures", "pvlan_po_ts_exp1_measured.json")))
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


ACCESS_RUNNING = ["shutdown", "spanning-tree port type edge", "mtu 9216"]  # MEASURED (EXP-1 A, regular Po)


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


def update_preview(serial, port, mode, old, new, native="", allowed="", pending=None):
    """An update of an EXISTING vPC: only the child Po block carries the change (MEASURED parent-only shape of a regular Po, H4/P2/TP2)."""
    if pending is None:
        pending = ["interface port-channel10"] + ["  switchport private-vlan %s %d %d" % ((KEYWORD[mode],) + p) for p in sorted(set(new) - set(old))]
        pending += ["  no switchport private-vlan %s %d %d" % ((KEYWORD[mode],) + p) for p in sorted(set(old) - set(new))]
    return preview(
        pending,
        serial=serial,
        running=po_stanza(mode, old, native, allowed) + member_after(port, mode, old, native, allowed),
        expected=po_stanza(mode, new, native, allowed) + member_after(port, mode, new, native, allowed),
    )


def delete_preview(serial, port, mode, pairs, native="", allowed=""):
    released = ["interface %s" % port] + [
        "  " + x
        for x in ("switchport", "switchport mode trunk", "switchport trunk allowed vlan none", "spanning-tree port type edge trunk", "mtu 9216", "shutdown")
    ]
    pend = ["no interface port-channel10", "interface %s" % port, "  no switchport mode private-vlan %s" % mode]
    pend += ["  no " + x for x in pvlan_lines(mode, pairs, native, allowed)]
    pend += [
        "  no channel-group 10 force mode active",
        "  switchport mode trunk",
        "  switchport trunk allowed vlan none",
        "  spanning-tree port type edge trunk",
    ]
    return preview(pend, serial=serial, running=po_stanza(mode, pairs, native, allowed) + member_after(port, mode, pairs, native, allowed), expected=released)


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


def with_networks_2410(ctrl):
    """SYNTHETIC networks for the second primary of the regular-Po battery: 2410 primary, 2411 community, 2412 isolated."""
    nets = ctrl.networks
    for vlan, kind, nid, prim, old in (
        (2410, "Primary", 30410, -1, "2210"),
        (2411, "Community", 30411, 30410, "2211"),
        (2412, "Isolated", 30412, 30410, "2212"),
    ):
        src = copy.deepcopy([n for n in nets if n["type"] == kind][0])
        src.update(
            networkId=nid, networkName="SYN_%d" % vlan, primaryNetworkId=prim, networkTemplateConfig=src["networkTemplateConfig"].replace(old, str(vlan))
        )
        nets.append(src)
    return ctrl


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


# ================================================================== create (each submode)
@pytest.mark.parametrize("mode", MODES)
def test_create_writes_the_submode_lists_and_per_peer_fields_and_deploys_after_both_peers_are_judged(mode):
    ctrl = baseline_ctrl(mode)
    create_previews(ctrl, mode)
    status, result = run_vpc(ctrl, [item(mode)])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1 and ctrl.modifies() == []
    nv = sent_parent(ctrl, ctrl.creates())
    key, other = P.active_list_key(mode), ("ASSOCIATION_LIST" if P.active_list_key(mode) == "MAPPING_LIST" else "MAPPING_LIST")
    assert nv["PVLAN_MODE"] == mode and P.pairs_from_wire(nv[key], key) == PAIRS[mode] and nv[other] == ""
    for n in (1, 2):
        native, allowed = per_peer(mode, n - 1)
        assert (nv["PEER%d_PVLAN_NATIVE_VLAN" % n], nv["PEER%d_PVLAN_ALLOWED_VLANS" % n]) == (native, allowed), n
    assert "createVpc" not in nv and nv["PEER1_MEMBER_INTERFACES"] == M1 and nv["PEER2_MEMBER_INTERFACES"] == M2
    assert gate(result) == {"deploy": [(1, SN1, "deploy"), (2, SN2, "deploy")]}
    for serial, n in ((SN1, 1), (SN2, 2)):
        child = ctrl.nodes[serial]["port-channel10"]["nvPairs"]
        assert child["PVLAN_MODE"] == mode and child["PVLAN_NATIVE_VLAN"] == per_peer(mode, n - 1)[0], "each child follows ITS peer"


def test_per_peer_trunk_fields_follow_the_serial_that_owns_them_when_the_switch_order_is_reversed():
    ctrl = baseline_ctrl(TP)
    create_previews(ctrl, TP)
    # playbook peer1_* belong to switch[0] = IP2 = the controller's SECOND serial
    swapped = item(
        TP,
        switches=[IP2, IP1],
        peer1_members=[M2],
        peer2_members=[M1],
        peer1_native_vlan="2302",
        peer1_allowed_vlans="2302",
        peer2_native_vlan="2301",
        peer2_allowed_vlans="2301",
    )
    status, result = run_vpc(ctrl, [swapped])
    assert status == "exit", result.get("msg")
    nv = sent_parent(ctrl, ctrl.creates())
    assert (nv["PEER1_PVLAN_NATIVE_VLAN"], nv["PEER2_PVLAN_NATIVE_VLAN"]) == ("2301", "2302") and nv["PEER1_MEMBER_INTERFACES"] == M1


# ================================================================== genuine update, exact repeat
UPDATES = {
    P_: ([{"primary_vlan": 2210, "secondary_vlans": "2211"}], [(2210, 2211), (2210, 2212)]),
    TP: ([{"primary_vlan": 2410, "secondary_vlans": "2411-2412"}], [(2210, 2211), (2210, 2212), (2410, 2411), (2410, 2412)]),
    TS: ([{"primary_vlan": 2410, "secondary_vlan": 2412}], [(2210, 2212), (2410, 2412)]),
}


@pytest.mark.parametrize("mode", MODES)
def test_merged_list_addition_keeps_every_omitted_field_and_deploys_both_peers_with_prior_then_deploy_records(mode):
    add, new = UPDATES[mode]
    ctrl = with_networks_2410(seeded_ctrl(mode))
    old = PAIRS[mode]
    for i, (serial, port) in enumerate(((SN1, M1), (SN2, M2))):
        native, allowed = per_peer(mode, i)
        ctrl.vpc_previews[serial] = [converged_preview(serial, port, mode, old, native, allowed), update_preview(serial, port, mode, old, new, native, allowed)]
    field = "pvlan_mapping" if mode in (P_, TP) else "pvlan_association"
    upd = {
        "name": "vpc10",
        "type": "vpc",
        "switch": [IP1, IP2],
        "deploy": True,
        "profile": {"mode": "pvlan", "pvlan_mode": mode, field: add, "peer1_pcid": 10, "peer2_pcid": 10},
    }  # PCIDs are always required (E5)
    status, result = run_vpc(ctrl, [upd], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.creates() == [] and len(ctrl.modifies()) == 1 and len(ctrl.deploys()) == 1
    nv = sent_parent(ctrl, ctrl.modifies())
    key = P.active_list_key(mode)
    assert P.pairs_from_wire(nv[key], key) == new and nv["PVLAN_MODE"] == mode
    for n in (1, 2):
        assert (nv["PEER%d_PVLAN_NATIVE_VLAN" % n], nv["PEER%d_PVLAN_ALLOWED_VLANS" % n]) == per_peer(mode, n - 1), "omitted per-peer fields kept"
    assert nv["PEER1_MEMBER_INTERFACES"] == M1 and nv["ADMIN_STATE"] == "false" and nv["createVpc"] == "true"
    assert result["diff"][0]["merged"][0]["interfaces"][0]["nvPairs"] == {key: nv[key]}
    assert gate(result) == {"prior": [(1, SN1, "converged"), (2, SN2, "converged")], "deploy": [(1, SN1, "deploy"), (2, SN2, "deploy")]}


@pytest.mark.parametrize("mode", MODES)
def test_exact_repeat_writes_nothing_and_judges_both_peers_converged(mode):
    ctrl = seeded_ctrl(mode)
    converged_previews(ctrl, mode)
    status, result = run_vpc(ctrl, [item(mode)], state="merged")
    assert status == "exit" and result["changed"] is False, result
    assert ctrl.writes() == [] and ctrl.deploys() == []
    assert gate(result) == {"prior": [(1, SN1, "converged"), (2, SN2, "converged")]}


# ================================================================== partial removal
def test_promiscuous_partial_removal_is_refused_before_any_intent_write():
    ctrl = seeded_ctrl(P_, pairs=[(2210, 2211), (2210, 2212)])
    converged_previews(ctrl, P_, pairs=[(2210, 2211), (2210, 2212)])
    status, result = run_vpc(ctrl, [item(P_)], state="replaced")  # keeps only 2210/2212
    assert status == "fail" and "promiscuous mapping that keeps other secondaries is blocked" in result["msg"], result.get("msg")
    assert "NOT measured" in result["msg"] and ctrl.writes() == [] and ctrl.previews_asked() == []


def test_trunk_promiscuous_partial_removal_is_not_blocked_and_deploys_with_the_measured_remove_form():
    old = [(2210, 2211), (2210, 2212), (2410, 2412)]
    new = [(2210, 2212), (2410, 2412)]
    ctrl = seeded_ctrl(TP, pairs=old)
    for i, (serial, port) in enumerate(((SN1, M1), (SN2, M2))):
        native, allowed = per_peer(TP, i)
        pend = ["interface port-channel10", "  switchport private-vlan mapping trunk 2210 remove 2211"]  # MEASURED form (regular Po TP4)
        ctrl.vpc_previews[serial] = [
            converged_preview(serial, port, TP, old, native, allowed),
            update_preview(serial, port, TP, old, new, native, allowed, pending=pend),
        ]
    req = item(TP, pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2212"}, {"primary_vlan": 2410, "secondary_vlans": "2412"}])
    status, result = run_vpc(ctrl, [req], state="replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert P.pairs_from_wire(sent_parent(ctrl, ctrl.modifies())["MAPPING_LIST"], "MAPPING_LIST") == new and len(ctrl.deploys()) == 1


def test_trunk_secondary_family_removal_deploys_with_the_withdrawal_of_the_association():
    old, new = [(2210, 2212), (2410, 2412)], [(2210, 2212)]
    ctrl = with_networks_2410(seeded_ctrl(TS, pairs=old))
    for i, (serial, port) in enumerate(((SN1, M1), (SN2, M2))):
        native, allowed = per_peer(TS, i)
        ctrl.vpc_previews[serial] = [converged_preview(serial, port, TS, old, native, allowed), update_preview(serial, port, TS, old, new, native, allowed)]
    status, result = run_vpc(ctrl, [item(TS)], state="replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert P.pairs_from_wire(sent_parent(ctrl, ctrl.modifies())["ASSOCIATION_LIST"], "ASSOCIATION_LIST") == new


# ================================================================== deletion / release (each submode)
@pytest.mark.parametrize("mode", MODES)
def test_deletion_marks_deletes_once_releases_both_members_down_before_the_single_deploy(mode):
    ctrl = seeded_ctrl(mode)
    for i, (serial, port) in enumerate(((SN1, M1), (SN2, M2))):
        native, allowed = per_peer(mode, i)
        ctrl.vpc_previews[serial] = [delete_preview(serial, port, mode, PAIRS[mode], native, allowed)]
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.markdeletes()) == 1 and len(ctrl.deploys()) == 1
    release_only(ctrl)
    for serial, port in ((SN1, M1), (SN2, M2)):
        assert ctrl.nodes[serial][port]["policy"] == TRUNK and ctrl.nodes[serial][port]["nvPairs"]["ADMIN_STATE"] == "false"
        assert "port-channel10" not in ctrl.nodes[serial]
    assert gate(result) == {"delete_deploy": [(1, SN1, "deploy"), (2, SN2, "deploy")]}


def test_trunk_secondary_release_contract_is_the_trunk_host_not_the_prepared_access_member():
    ctrl = baseline_ctrl(TS)
    create_previews(ctrl, TS)
    assert run_vpc(ctrl, [item(TS)])[0] == "exit"
    ctrl.next_invocation()
    ctrl.calls = []
    for i, (serial, port) in enumerate(((SN1, M1), (SN2, M2))):
        native, allowed = per_peer(TS, i)
        ctrl.vpc_previews[serial] = [delete_preview(serial, port, TS, PAIRS[TS], native, allowed)]
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit", result.get("msg")
    assert all(ctrl.nodes[s][p]["policy"] == TRUNK for s, p in ((SN1, M1), (SN2, M2))), "no restoration of the access preparation"


# ================================================================== invalid cross-mode fields (before any read or write)
@pytest.mark.parametrize(
    "mode, extra, needle",
    [
        (P_, {"pvlan_association": ASSOC_TS}, "pvlan_association is not valid for pvlan_mode 'promiscuous'"),
        (TS, {"pvlan_mapping": MAP_P}, "pvlan_mapping is not valid for pvlan_mode 'trunk secondary'"),
        (P_, {"peer1_native_vlan": "2301"}, "peer1_native_vlan is valid only for pvlan_mode trunk"),
        ("host", {"peer2_allowed_vlans": "2301"}, "peer2_allowed_vlans is valid only for pvlan_mode trunk"),
        (TP, {"peer1_allowed_vlans": "all"}, "'all' is refused by int_vpc_pvlan_host"),
        (TS, {"peer2_native_vlan": "5000"}, "must be '' or one VLAN ID 1-4094"),
        (P_, {"pvlan_mapping": [{"primary_vlan": 2210, "secondary_vlans": "2212"}, {"primary_vlan": 2410, "secondary_vlans": "2412"}]}, "single primary"),
        (
            TS,
            {"pvlan_association": [{"primary_vlan": 2210, "secondary_vlan": 2212}, {"primary_vlan": 2210, "secondary_vlan": 2211}]},
            "one secondary VLAN per primary",
        ),
        (TP, {"pvlan_mapping": []}, "an empty pvlan_mapping is not implemented"),
        (TP, {"native_vlan": "2301"}, "not implemented for a vPC"),
    ],
)
def test_fields_outside_the_submode_or_its_template_limits_are_refused_before_any_read(mode, extra, needle):
    ctrl = baseline_ctrl(mode if mode != "host" else P_)
    it = item(mode if mode != "host" else P_, **extra)
    if mode == "host":
        it["profile"].pop("pvlan_mapping")
        it["profile"].update(pvlan_mode="host", pvlan_association=ASSOC_TS)
    status, result = run_vpc(ctrl, [it])
    assert status == "fail" and needle in result["msg"], result.get("msg")
    assert ctrl.writes() == [] and ctrl.previews_asked() == []


def test_a_submode_change_of_an_existing_vpc_is_refused_before_any_write():
    ctrl = seeded_ctrl(TP)
    converged_previews(ctrl, TP)
    status, result = run_vpc(ctrl, [item(P_)], state="replaced")
    assert status == "fail" and "changing pvlan_mode of an existing vPC ('trunk promiscuous' -> 'promiscuous')" in result["msg"]
    assert ctrl.writes() == []


# ================================================================== trunk secondary: prepared member on BOTH peers
def test_trunk_secondary_refuses_a_trunk_member_on_one_peer_before_any_write():
    ctrl = baseline_ctrl(TS)
    nv = VpcController().seed_baseline().nodes[SN2][M2]
    ctrl.nodes[SN2][M2] = copy.deepcopy(nv)  # peer 2 keeps the measured unsafe trunk baseline
    create_previews(ctrl, TS)
    status, result = run_vpc(ctrl, [item(TS)])
    assert status == "fail" and "Known incident pending engineering" in result["msg"] and SN2 in result["msg"]
    assert ctrl.writes() == [] and ctrl.previews_asked() == []


@pytest.mark.parametrize(
    "key, value, needle",
    [("ACCESS_VLAN", "10", "does not model"), ("ADMIN_STATE", "true", "not administratively down"), ("CONF", "lldp transmit", "freeform CONF")],
)
def test_trunk_secondary_refuses_a_prepared_member_outside_the_contract_on_either_peer(key, value, needle):
    ctrl = baseline_ctrl(TS)
    ctrl.nodes[SN1][M1]["nvPairs"][key] = value
    create_previews(ctrl, TS)
    status, result = run_vpc(ctrl, [item(TS)])
    assert status == "fail" and needle in result["msg"] and ctrl.writes() == [], result.get("msg")


class RoutedVpcController(VpcController):
    """The vPC harness + the MEASURED routed behaviour (EXP-1 R, regular Po): the prepared routed member's self-sourced children disappear when
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
        if base == "routed":  # MEASURED routed shape (EXP-1 R): running `no switchport / mtu 9216`; no member line before the join
            entry = pv["DATA"][0]
            entry["runningConfig"] = ["!Command: show running-config", "hostname placeholder-sw-1", "interface %s" % port, "  no switchport", "  mtu 9216"]
            entry["pendingConfig"] = [line for line in entry["pendingConfig"] if line != "  no spanning-tree port type edge"]
        ctrl.vpc_previews[serial] = [pv]
    return ctrl


def test_trunk_secondary_admits_a_routed_member_only_with_its_measured_self_children():
    ctrl = routed_ctrl(M2)
    status, result = run_vpc(ctrl, [item(TS)])
    assert status == "exit", result.get("msg")
    assert gate(result) == {"deploy": [(1, SN1, "deploy"), (2, SN2, "deploy")]}
    ctrl = routed_ctrl("")  # the same children, but not owned by the member itself
    status, result = run_vpc(ctrl, [item(TS)])
    assert status == "fail" and "live policies" in result["msg"] and ctrl.writes() == []


def test_routed_children_that_survive_the_creation_are_refused_by_the_post_deploy_readback():
    ctrl = routed_ctrl(M2, vanish=False)
    status, result = run_vpc(ctrl, [item(TS)])
    assert status == "fail" and "post-deploy intent readback differs" in result["msg"] and "routed_interface" in result["msg"]


def test_trunk_secondary_community_secondary_is_refused_before_any_write():
    ctrl = baseline_ctrl(TS)
    create_previews(ctrl, TS)
    status, result = run_vpc(ctrl, [item(TS, pvlan_association=[{"primary_vlan": 2210, "secondary_vlan": 2211}])])
    assert status == "fail" and "2211 is a community VLAN" in result["msg"] and ctrl.writes() == []


# ================================================================== asymmetric peers / one peer fails
def test_a_change_of_one_peer_trunk_field_only_is_refused_as_a_unilateral_update():
    ctrl = seeded_ctrl(TP)
    converged_previews(ctrl, TP)
    status, result = run_vpc(ctrl, [item(TP, peer1_native_vlan="2310")], state="merged")
    assert status == "fail" and "changes only peer 1" in result["msg"] and ctrl.writes() == []


@pytest.mark.parametrize("mode", MODES)
def test_one_peer_failing_its_gate_after_the_create_permits_no_deploy(mode):
    ctrl = baseline_ctrl(mode)
    create_previews(ctrl, mode)
    entry = ctrl.vpc_previews[SN2][0]["DATA"][0]
    entry["pendingConfig"] = entry["pendingConfig"][:-1] + ["interface ethernet1/8", "  speed 1000", "configure terminal"]  # foreign line, peer 2 only
    status, result = run_vpc(ctrl, [item(mode)])
    assert status == "fail" and ctrl.deploys() == [] and len(ctrl.creates()) == 1, result.get("msg")
    g = gate(result)["deploy"]
    assert g[0] == (1, SN1, "deploy") and g[1] == (2, SN2, "refuse"), g


def test_trunk_promiscuous_member_expected_with_the_other_peer_native_is_refused():
    ctrl = baseline_ctrl(TP)
    create_previews(ctrl, TP)
    entry = ctrl.vpc_previews[SN1][0]["DATA"][0]
    entry["expectedConfig"] = [l.replace("native vlan 2301", "native vlan 2302") for l in entry["expectedConfig"]]  # crossed peers on peer 1
    status, result = run_vpc(ctrl, [item(TP)])
    assert status == "fail" and "disagrees with the intended state" in result["msg"] and ctrl.deploys() == []


# ================================================================== host unchanged on the shared paths
def test_host_payload_is_unchanged_by_the_new_submode_fields():
    raw = {
        "mode": "pvlan",
        "pvlan_mode": "host",
        "peer1_members": [M1],
        "peer2_members": [M2],
        "peer1_pcid": 10,
        "peer2_pcid": 10,
        "admin_state": False,
        "pvlan_association": ASSOC_TS,
    }
    nv = P.vpc_host_nvpairs(raw, VPC, P.vpc_pair_view(raw, PAIR, [SN1, SN2]))
    assert nv["PVLAN_MODE"] == "host" and nv["MAPPING_LIST"] == "" and P.pairs_from_wire(nv["ASSOCIATION_LIST"], "ASSOCIATION_LIST") == [(2210, 2212)]
    assert all(nv["PEER%d_PVLAN_%s" % (n, k)] == "" for n in (1, 2) for k in ("NATIVE_VLAN", "ALLOWED_VLANS"))
    assert P.vpc_not_implemented(raw, VPC) == []


@pytest.mark.parametrize(
    "key, value, needle",
    [
        ("MAPPING_LIST", P.pairs_to_wire("MAPPING_LIST", [(2210, 2212)]), "MAPPING_LIST"),  # peer 2 child lost 2211: does not follow its parent
        ("PVLAN_NATIVE_VLAN", "2399", "PVLAN_NATIVE_VLAN"),
    ],
)
def test_a_child_that_does_not_follow_its_parent_on_one_peer_is_a_partial_state_refused_before_any_write(key, value, needle):
    ctrl = seeded_ctrl(TP)
    ctrl.nodes[SN2]["port-channel10"]["nvPairs"][key] = value
    converged_previews(ctrl, TP)
    status, result = run_vpc(ctrl, [item(TP)], state="merged")
    assert status == "fail" and "does not follow the parent's intent" in result["msg"] and needle in result["msg"], result.get("msg")
    assert ctrl.writes() == [] and SN2 in result["msg"]
