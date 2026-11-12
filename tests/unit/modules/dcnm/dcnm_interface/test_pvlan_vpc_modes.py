"""vPC PVLAN modes and ingress QoS of int_vpc_pvlan_host."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_ENABLED_PATCH_VERSIONS

from .helpers.vpc_controller import IP1
from .helpers.vpc_controller import IP2
from .helpers.vpc_controller import M1
from .helpers.vpc_controller import M2
from .helpers.vpc_controller import PAIR
from .helpers.vpc_controller import SN1
from .helpers.vpc_controller import SN2
from .helpers.ethernet_controller import TRUNK
from .helpers.vpc_controller import VPC
from .helpers.vpc_controller import VpcController
from .helpers.ethernet_controller import preview
from .helpers.vpc_controller import release_only
from .helpers.vpc_controller import run_vpc
from .helpers.vpc_controller import vpc_del_item
from .helpers.vpc_modes import ASSOC_TS
from .helpers.vpc_modes import KEYWORD
from .helpers.vpc_modes import MAP_P
from .helpers.vpc_modes import MODES
from .helpers.vpc_modes import PAIRS
from .helpers.vpc_modes import P_
from .helpers.vpc_modes import TP
from .helpers.vpc_modes import TS
from .helpers.vpc_modes import baseline_ctrl
from .helpers.vpc_modes import converged_preview
from .helpers.vpc_modes import converged_previews
from .helpers.vpc_modes import create_previews
from .helpers.vpc_modes import gate
from .helpers.vpc_modes import item
from .helpers.vpc_modes import member_after
from .helpers.vpc_modes import per_peer
from .helpers.vpc_modes import po_stanza
from .helpers.vpc_modes import pvlan_lines
from .helpers.vpc_modes import routed_ctrl
from .helpers.vpc_modes import seeded_ctrl
from .helpers.vpc_modes import sent_parent
from .helpers import binding_harness as G
from .helpers import vpc_controller as V


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_vpc_modes_e1.py
# Promiscuous, trunk promiscuous and trunk secondary for a vPC in mode 'pvlan' (int_vpc_pvlan_host).
#
# NOT LIVE TESTED. Real main() through the EXISTING vPC harness (VpcController: two peers, per-serial previews). Labels:
#   [SRC] the installed templates (VPC-TEMPLATE-READ): the parent's per-submode lists and per-peer PVLAN native/allowed (HOST 192-229,
#         604-680), the child Po body (POVPC 217-252) = the regular Po body + `vpc N`;
#   [MEASURED elsewhere] the prepared access member of the regular-Po EXP-1 (fixtures/pvlan_po_delete_saved.json#pvlan_po_ts_exp1_measured, branch A), and the
#         regular-Po pending shapes (force join, parent-only update, `mapping trunk P remove S`);
#   SYNTHETIC: every vPC preview below (written by hand from those templates; no vPC of these submodes was ever observed).
# Gate records are checked per SITE with the exact peer + serial + target + decision (the host L2 lesson: an update records two `prior`
# `converged` decisions plus two `deploy` decisions; never assert a peer list over the whole gate list or call every record `deploy`).
# ====================================================================================================
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
    }  # PCIDs are always required
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
    [("ACCESS_VLAN", "10", "does not model"), ("ADMIN_STATE", "", "administrative state is unknown"), ("CONF", "lldp transmit", "freeform CONF")],
)
def test_trunk_secondary_refuses_a_prepared_member_outside_the_contract_on_either_peer(key, value, needle):
    ctrl = baseline_ctrl(TS)
    ctrl.nodes[SN1][M1]["nvPairs"][key] = value
    create_previews(ctrl, TS)
    status, result = run_vpc(ctrl, [item(TS)])
    assert status == "fail" and needle in result["msg"] and ctrl.writes() == [], result.get("msg")


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


# ================================================================== N06: one primary per secondary in the vPC's (shared) list
N06 = "is associated with more than one primary VLAN"
N06_BAD = {
    TP: {"pvlan_mapping": [{"primary_vlan": 2210, "secondary_vlans": "2211-2212"}, {"primary_vlan": 2410, "secondary_vlans": "2212"}]},
    TS: {"pvlan_association": [{"primary_vlan": 2210, "secondary_vlan": 2212}, {"primary_vlan": 2410, "secondary_vlan": 2212}]},
}


@pytest.mark.parametrize("mode", [TP, TS])
def test_n06_creation_request_alone_is_refused_before_any_read_or_write(mode):
    ctrl = baseline_ctrl(mode)
    status, result = run_vpc(ctrl, [item(mode, **N06_BAD[mode])])
    assert status == "fail" and N06 in result["msg"] and "secondary VLAN 2212" in result["msg"] and "(2210, 2410)" in result["msg"], result.get("msg")
    assert ctrl.writes() == [] and ctrl.previews_asked() == []


@pytest.mark.parametrize(
    "mode, add, secondary",
    [
        (TP, {"pvlan_mapping": [{"primary_vlan": 2410, "secondary_vlans": "2211"}]}, 2211),
        (TS, {"pvlan_association": [{"primary_vlan": 2410, "secondary_vlan": 2212}]}, 2212),
    ],
)
def test_n06_merged_union_with_the_current_list_is_refused_before_any_write(mode, add, secondary):
    ctrl = with_networks_2410(seeded_ctrl(mode))
    converged_previews(ctrl, mode)  # the update's read-only preflight of each peer
    upd = item(mode, **add)
    for k in ("pvlan_mapping", "pvlan_association"):
        if k not in add:
            upd["profile"].pop(k, None)
    status, result = run_vpc(ctrl, [upd], state="merged")
    assert status == "fail" and N06 in result["msg"] and "secondary VLAN %d" % secondary in result["msg"], result.get("msg")
    assert "(2210, 2410)" in result["msg"]
    assert ctrl.writes() == []  # read-only preflight previews are allowed; no create, modify, markdelete or deploy


def test_n06_distinct_primaries_reach_both_peers_with_the_same_pairs_and_are_not_a_conflict():
    pairs = [(2210, 2211), (2210, 2212), (2410, 2412)]
    ctrl = baseline_ctrl(TP)
    create_previews(ctrl, TP, pairs)
    mapping = [{"primary_vlan": 2210, "secondary_vlans": "2211-2212"}, {"primary_vlan": 2410, "secondary_vlans": "2412"}]
    status, result = run_vpc(ctrl, [item(TP, pvlan_mapping=mapping)])
    assert status == "exit" and N06 not in result.get("msg", ""), result.get("msg")
    lists = [P.pairs_from_wire(ctrl.nodes[s]["port-channel10"]["nvPairs"]["MAPPING_LIST"], "MAPPING_LIST") for s in (SN1, SN2)]
    assert lists == [pairs, pairs]  # the repeated pair on two peers is the same association, not a conflict


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_vpc_ingress_qos.py
# Ingress QoS (ENABLE_QOS, QOS_POLICY, qosStatsSuppressed) of the vPC PVLAN parent int_vpc_pvlan_host.
#
# NOT LIVE TESTED. Real main() through the EXISTING vPC harness; previews are SYNTHETIC, written by hand from the CORRECTED templates
# (the parent's QoS block with qosPolicy/queuingPolicy locals as in the reference int_vpc_trunk_host and every Engineering set; the
# child's `service-policy type qos input <p>[ no-stats]` as in the regular templates). The INSTALLED revision on the test ND drops the
# values parent -> children (MEASURED for QUEUING_POLICY, live S1) and its child renders a `type ENABLE_QOS` literal: the harness
# reproduces that loss with `defective_qos_template`, and those cases must fail WITHOUT a deploy.
#
# The REFERENCE section drives the regular vPC parents (trunk, dot1q) through the same main() and reads the request the module sends.
# ====================================================================================================
SMU = sorted(GIE_ENABLED_PATCH_VERSIONS)[0]
QOS_KEYS = ("ENABLE_QOS", "QOS_POLICY", "qosStatsSuppressed")


def _norm(nv):
    return {k: str(nv.get(k)).lower() if k != "QOS_POLICY" else (nv.get(k) or "") for k in QOS_KEYS if k in nv}


# ====================================================================================== reference: the module's regular vPC rule
def _base_without_qos(parent):
    # the harness base profiles carry enable_qos/qos_policy; an omission case must not send them
    return {k: v for k, v in G.base_for(parent).items() if k not in ("enable_qos", "qos_policy")}


def _regular(parent, state, have_extra, want_extra):
    have = G.build_have(parent, **have_extra) if have_extra is not None else None
    want = dict(_base_without_qos(parent), **want_extra)
    for key in [k for k, v in want.items() if v is None]:
        want.pop(key)
    result, calls = G.run(want, state, have=have, parent=parent)
    assert not result.get("failed"), result.get("msg")
    found = []
    G._collect_policies([c["payload"] for c in G.writes(calls)], found)
    return bool(G.split_calls(calls)["updates"]), (found[0]["interfaces"][0]["nvPairs"] if found else None)


@pytest.mark.parametrize("parent", [G.VPC_TRUNK, G.VPC_DOT1Q])
def test_reference_regular_vpc_ingress_qos_rule(parent):
    """The regular rule IQ1 reuses (the request the module itself sends)."""
    on = dict(enable_qos=True, qos_policy="Q1", disable_qos_stats=True)
    written, nv = _regular(parent, "merged", None, on)
    assert written and _norm(nv) == {"ENABLE_QOS": "true", "QOS_POLICY": "Q1", "qosStatsSuppressed": "true"}
    written, _nv = _regular(parent, "merged", on, {})                       # merged, omitted: nothing
    assert not written
    written, nv = _regular(parent, "merged", on, dict(enable_qos=True, qos_policy="Q2"))     # policy change, QoS restated
    assert written and nv["QOS_POLICY"] == "Q2"
    # DOCUMENTED DIVERGENCE: a merged policy change that does not restate enable_qos sends QOS_POLICY '' on the regular parent (the
    # payload builder reads the spec default enable_qos=False), i.e. the policy is dropped silently. The PVLAN rule keeps ENABLE_QOS
    # from HAVE and applies the new policy (test_vpc_pvlan_rule_matches_the_regular_one, third row).
    written, nv = _regular(parent, "merged", on, dict(qos_policy="Q2"))
    assert written and nv["QOS_POLICY"] == ""
    written, nv = _regular(parent, "merged", on, dict(enable_qos=False, qos_policy=None))   # merged disable: an omitted policy is kept
    assert written and _norm(nv)["ENABLE_QOS"] == "false" and nv["QOS_POLICY"] == "Q1"
    result, calls = G.run(_base_without_qos(parent), "replaced", have=G.build_have(parent, **on), parent=parent)  # replaced, omitted: reset
    found = []
    G._collect_policies([c["payload"] for c in G.writes(calls)], found)
    nv = found[0]["interfaces"][0]["nvPairs"]
    assert _norm(nv) == {"ENABLE_QOS": "false", "QOS_POLICY": "", "qosStatsSuppressed": "false"}


# ====================================================================================== PVLAN rule (helper)
def _raw(**extra):
    raw = {"pvlan_mode": "host", "peer1_members": [V.M1], "peer2_members": [V.M2], "peer1_pcid": 10, "peer2_pcid": 10,
           "pvlan_association": [{"primary_vlan": V.PRIMARY, "secondary_vlan": V.SECONDARY}]}
    raw.update(extra)
    return raw


def _legs(raw):
    return P.vpc_pair_view(raw, V.PAIR, [V.SN1, V.SN2])


def _have(**extra):
    raw = _raw(**extra)
    nv = P.vpc_host_nvpairs(raw, "vPC10", _legs(raw))
    nv.update(P.registry_companions("replaced", P.VPC_HOST_POLICY, raw, None, "12.6.0.267", SMU)[0])
    return nv


def _reconcile(state, have, patch=SMU, **want):
    raw = _raw(**want)
    return P.reconcile_vpc(state, raw, "vPC10", _legs(raw), P.VPC_HOST_POLICY, have, "12.6.0.267", patch)


ON = dict(enable_qos=True, qos_policy="Q1", disable_qos_stats=True)


@pytest.mark.parametrize(
    "state, have, want, written, expected",
    [
        ("merged", {}, ON, True, {"ENABLE_QOS": "true", "QOS_POLICY": "Q1", "qosStatsSuppressed": "true"}),
        ("merged", ON, {}, False, {"ENABLE_QOS": "true", "QOS_POLICY": "Q1", "qosStatsSuppressed": "true"}),
        ("merged", ON, dict(qos_policy="Q2"), True, {"ENABLE_QOS": "true", "QOS_POLICY": "Q2", "qosStatsSuppressed": "true"}),
        ("merged", dict(enable_qos=True, qos_policy="Q1"), dict(enable_qos=False), True,
         {"ENABLE_QOS": "false", "QOS_POLICY": "Q1", "qosStatsSuppressed": "false"}),   # residual kept, as the regular merged
        ("replaced", dict(enable_qos=True, qos_policy="Q1"), dict(enable_qos=False), True,
         {"ENABLE_QOS": "false", "QOS_POLICY": "", "qosStatsSuppressed": "false"}),    # full payload clears it, as the regular
        ("replaced", ON, {}, True, {"ENABLE_QOS": "false", "QOS_POLICY": "", "qosStatsSuppressed": "false"}),
        ("replaced", ON, ON, False, {"ENABLE_QOS": "true", "QOS_POLICY": "Q1", "qosStatsSuppressed": "true"}),
        ("merged", dict(enable_qos=True, qos_policy="Q1"), dict(disable_qos_stats=False), False,
         {"ENABLE_QOS": "true", "QOS_POLICY": "Q1", "qosStatsSuppressed": "false"}),
    ],
)
def test_vpc_pvlan_rule_matches_the_regular_one(state, have, want, written, expected):
    out = _reconcile(state, _have(**have), **want)
    assert out["blocked"] == [], out["blocked"]
    assert out["update"] is written
    assert _norm(out["nv"]) == expected
    if written:
        assert set(out["changed"]) <= set(QOS_KEYS) and out["ask_legs"] == [0, 1]


def test_an_untouched_merged_keeps_a_residual_policy_of_a_disabled_qos_and_the_children_never_see_it():
    have = _have()
    have["QOS_POLICY"] = "RESIDUAL"  # ENABLE_QOS false, a policy left by another tool
    out = _reconcile("merged", have, peer1_description="d1", peer2_description="d2")
    assert out["blocked"] == [] and out["nv"]["QOS_POLICY"] == "RESIDUAL" and "QOS_POLICY" not in out["changed"]
    for index in (0, 1):
        child = P.vpc_leg_po_nv(out["nv"], index, "vPC10")
        assert child["QOS_POLICY"] == "" and not any("service-policy type qos" in x for x in P.render(P.VPC_PO_POLICY, child).scalars)


@pytest.mark.parametrize(
    "have, want, needle",
    [
        ({}, dict(enable_qos=True), "needs a qos_policy"),
        ({}, dict(enable_qos=False, qos_policy="Q1"), "qos_policy requires enable_qos true"),
        ({}, dict(qos_policy="Q1"), "qos_policy requires enable_qos true"),
        ({}, dict(disable_qos_stats=True), "disable_qos_stats true only takes effect"),
        (dict(enable_qos=True, qos_policy="Q1"), dict(enable_qos=False, disable_qos_stats=True), "disable_qos_stats true only takes effect"),
    ],
)
def test_combinations_the_template_cannot_honour_are_refused_before_any_write(have, want, needle):
    out = _reconcile("merged", _have(**have), **want)
    assert out["update"] is False and any(needle in b for b in out["blocked"]), out["blocked"]


def test_raw_values_follow_the_template_types():
    assert P.vpc_not_implemented(dict(_raw(), enable_qos="yes"), "vPC10") == ["enable_qos must be a boolean"]
    assert "qos_policy must be one policy-map name" in P.vpc_not_implemented(dict(_raw(), qos_policy="a b"), "vPC10")[0]
    out = _reconcile("merged", _have(), patch=None, **ON)
    assert out["update"] is False and any("requires caller-supplied patch_version" in b for b in out["blocked"]), out["blocked"]


# ====================================================================================== child expectation (corrected templates)
@pytest.mark.parametrize("stats, line", [(False, "service-policy type qos input Q1"), (True, "service-policy type qos input Q1 no-stats")])
def test_both_children_carry_the_qos_line_of_the_corrected_child(stats, line):
    nv = _have(enable_qos=True, qos_policy="Q1", disable_qos_stats=stats)
    for index in (0, 1):
        child = P.vpc_leg_po_nv(nv, index, "vPC10")
        assert (child["ENABLE_QOS"], child["QOS_POLICY"], child["qosStatsSuppressed"]) == ("true", "Q1", "true" if stats else "false")
        scalars = P.render(P.VPC_PO_POLICY, child).scalars
        assert line in scalars and not any("ENABLE_QOS" in x for x in scalars)


def test_a_child_that_lost_the_qos_values_differs_from_its_parent():
    nv = _have(enable_qos=True, qos_policy="Q1")
    expected = P.vpc_leg_po_nv(nv, 0, "vPC10")
    lost = dict(expected, ENABLE_QOS="false", QOS_POLICY="")   # the MEASURED shape of the installed revision
    assert set(P.vpc_child_differences(lost, expected)) == {"ENABLE_QOS", "QOS_POLICY"}
    assert P.vpc_child_differences(dict(expected, QOS_POLICY="q1"), expected) == ["QOS_POLICY"]  # exact name


# ====================================================================================== main(): positive, corrected templates
def _child_with_qos(line):
    return V.po_stanza() + ["  " + line] if line else V.po_stanza()


def _preview(serial, port, run_line, exp_line, pend):
    return V.preview(pend, serial=serial, running=_child_with_qos(run_line) + V.member_after(port),
                     expected=_child_with_qos(exp_line) + V.member_after(port))


def _queue(ctrl, run_line, exp_line, pend, preflight_line=None):
    for serial, port in ((V.SN1, V.M1), (V.SN2, V.M2)):
        ctrl.vpc_previews[serial] = [_preview(serial, port, preflight_line, preflight_line, []), _preview(serial, port, run_line, exp_line, pend)]


LINE = "service-policy type qos input Q1 no-stats"
ADD = ["interface port-channel10", "  " + LINE]


def _seeded(**qos):
    ctrl = V.created_ctrl()
    parent = ctrl.parents[V.VPC]["nvPairs"]
    parent.update(qos)
    ctrl._expand_children(parent)
    return ctrl


def test_enabling_qos_with_an_explicit_policy_reaches_both_children_and_the_repeat_writes_nothing():
    ctrl = V.created_ctrl()
    _queue(ctrl, None, LINE, ADD)
    status, res = V.run_vpc(ctrl, [V.vpc_item(**ON)], state="merged", patch_version=SMU)
    assert status == "exit" and res["changed"] is True, res.get("msg")
    sent = json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]
    assert _norm(sent) == {"ENABLE_QOS": "true", "QOS_POLICY": "Q1", "qosStatsSuppressed": "true"}
    assert len(ctrl.deploys()) == 1
    for serial in (V.SN1, V.SN2):
        child = ctrl.nodes[serial]["port-channel10"]["nvPairs"]
        assert (child["ENABLE_QOS"], child["QOS_POLICY"], child["qosStatsSuppressed"]) == ("true", "Q1", "true")
    ctrl.next_invocation()
    before = len(ctrl.writes())
    for serial, port in ((V.SN1, V.M1), (V.SN2, V.M2)):
        ctrl.vpc_previews[serial] = [_preview(serial, port, LINE, LINE, [])]
    status, res = V.run_vpc(ctrl, [V.vpc_item(**ON)], state="merged", patch_version=SMU)
    assert status == "exit" and res["changed"] is False, res
    assert len(ctrl.writes()) == before


def test_merged_omission_keeps_qos_and_replaced_withdraws_it_on_both_peers():
    ctrl = _seeded(ENABLE_QOS="true", QOS_POLICY="Q1", qosStatsSuppressed="true")
    pend = ["interface port-channel10", "  description d1"]
    for serial, port, desc in ((V.SN1, V.M1, "d1"), (V.SN2, V.M2, "d2")):
        run_cfg = _child_with_qos(LINE) + V.member_after(port)
        exp = _child_with_qos(LINE) + ["  description %s" % desc] + V.member_after(port)
        ctrl.vpc_previews[serial] = [V.preview([], serial=serial, running=run_cfg, expected=run_cfg),
                                     V.preview(["interface port-channel10", "  description %s" % desc], serial=serial, running=run_cfg, expected=exp)]
    status, res = V.run_vpc(ctrl, [V.vpc_item(peer1_description="d1", peer2_description="d2")], state="merged", patch_version=SMU)
    assert status == "exit" and res["changed"] is True, res.get("msg")
    sent = json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]
    assert _norm(sent) == {"ENABLE_QOS": "true", "QOS_POLICY": "Q1", "qosStatsSuppressed": "true"}
    # replaced without the QoS keys: reset, and the pending must withdraw the line on both peers
    ctrl = _seeded(ENABLE_QOS="true", QOS_POLICY="Q1", qosStatsSuppressed="true")
    _queue(ctrl, LINE, None, ["interface port-channel10", "  no " + LINE], preflight_line=LINE)
    status, res = V.run_vpc(ctrl, [V.vpc_item()], state="replaced", patch_version=SMU)
    assert status == "exit" and res["changed"] is True, res.get("msg")
    sent = json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]
    assert _norm(sent) == {"ENABLE_QOS": "false", "QOS_POLICY": "", "qosStatsSuppressed": "false"} and len(ctrl.deploys()) == 1
    del pend


def test_a_policy_change_withdraws_the_old_line_and_adds_the_new_one():
    ctrl = _seeded(ENABLE_QOS="true", QOS_POLICY="Q1", qosStatsSuppressed="true")
    new = "service-policy type qos input Q2 no-stats"
    _queue(ctrl, LINE, new, ["interface port-channel10", "  no " + LINE, "  " + new], preflight_line=LINE)
    status, res = V.run_vpc(ctrl, [V.vpc_item(qos_policy="Q2")], state="merged", patch_version=SMU)
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]["QOS_POLICY"] == "Q2"


# ====================================================================================== main(): negatives
def test_the_installed_revision_that_drops_the_values_is_refused_before_any_deploy():
    """The MEASURED parent -> children loss: the parent stores the QoS values, both children keep ENABLE_QOS false / QOS_POLICY '', the
    controller's expected child configuration has no qos line, and the preview is In-Sync. Refused, never deployed."""
    ctrl = V.created_ctrl()
    ctrl.defective_qos_template = True
    _queue(ctrl, None, None, [])
    status, res = V.run_vpc(ctrl, [V.vpc_item(**ON)], state="merged", patch_version=SMU)
    assert status == "fail" and ctrl.deploys() == [], res
    assert "service-policy type qos input Q1 no-stats" in res["msg"] and "disagrees with the intended state" in res["msg"]
    for serial in (V.SN1, V.SN2):
        child = ctrl.nodes[serial]["port-channel10"]["nvPairs"]
        assert (child["ENABLE_QOS"], child["QOS_POLICY"], child["qosStatsSuppressed"]) == ("false", "", "true")
    # the next invocation sees the partial state and refuses before any write
    ctrl.next_invocation()
    writes = len(ctrl.writes())
    status, res = V.run_vpc(ctrl, [V.vpc_item(**ON)], state="merged", patch_version=SMU)
    assert status == "fail" and "does not follow the parent's intent" in res["msg"] and "ENABLE_QOS" in res["msg"], res
    assert len(ctrl.writes()) == writes and ctrl.deploys() == []


class LoseAfterDeploy(V.VpcController):
    """SYNTHETIC: the child of peer 2 loses the QoS values after the deploy (a later regeneration by the installed revision)."""

    def __call__(self, mod, method, path, data=None):
        resp = super(LoseAfterDeploy, self).__call__(mod, method, path, data)
        if method == "POST" and path.endswith(V.DEPLOY) and "port-channel10" in self.nodes[V.SN2]:
            self.nodes[V.SN2]["port-channel10"]["nvPairs"].update({"ENABLE_QOS": "false", "QOS_POLICY": ""})
        return resp


def test_a_child_that_loses_the_values_after_the_deploy_is_reported_without_rewrite():
    ctrl = V.created_ctrl()
    ctrl.__class__ = LoseAfterDeploy
    _queue(ctrl, None, LINE, ADD)
    status, res = V.run_vpc(ctrl, [V.vpc_item(**ON)], state="merged", patch_version=SMU)
    assert status == "fail" and "post-deploy intent readback differs" in res["msg"] and "QOS_POLICY" in res["msg"], res
    assert len(ctrl.modifies()) == 1 and len(ctrl.deploys()) == 1
    at = max(i for i, c in enumerate(ctrl.calls) if c[0] == "POST" and c[1].endswith(V.DEPLOY))
    assert [c for c in ctrl.calls[at + 1:] if c[0] in ("POST", "PUT", "DELETE") and "config-preview" not in c[1]] == []


def test_an_error_item_on_the_parent_modify_stops_before_any_deploy():
    ctrl = V.created_ctrl()
    _queue(ctrl, None, LINE, ADD)
    ctrl.modify_responses = [{"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [
        {"reportItemType": "ERROR", "message": "QoS policy Q1 not found", "entity": "%s~vPC10" % V.PAIR}]}]
    status, res = V.run_vpc(ctrl, [V.vpc_item(**ON)], state="merged", patch_version=SMU)
    # the QoS request reached the parent modify (one attempt), the per-item ERROR is reported, nothing is deployed or retried
    assert status == "fail" and len(ctrl.modifies()) == 1 and ctrl.deploys() == [], res
    assert "QoS policy Q1 not found" in res["msg"] and "Nothing in this batch was applied" in res["msg"]
    sent = json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]
    assert _norm(sent) == {"ENABLE_QOS": "true", "QOS_POLICY": "Q1", "qosStatsSuppressed": "true"}


@pytest.mark.parametrize(
    "profile, needle",
    [
        (dict(enable_qos=True), "needs a qos_policy"),
        (dict(enable_qos=False, qos_policy="Q1"), "qos_policy requires enable_qos true"),
        (dict(disable_qos_stats=True), "disable_qos_stats true only takes effect"),
    ],
)
def test_refusals_reach_main_before_any_write(profile, needle):
    ctrl = V.created_ctrl()
    status, res = V.run_vpc(ctrl, [V.vpc_item(**profile)], state="merged", patch_version=SMU)
    assert status == "fail" and needle in res["msg"] and ctrl.writes() == [], res
