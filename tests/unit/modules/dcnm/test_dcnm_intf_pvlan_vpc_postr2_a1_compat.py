"""A1 (the description of ONE vPC peer changes alone) next to what was published after it: speed/duplex, multi-member and input parity.

A1 was written on N06. The published base now also carries the duplex rule and the early refusal of a combined speed + duplex change (R1), the
multi-member vPC support, the bpdu_guard/speed input parity, and the registry work. These cases prove that they coexist: a description-only change of
one peer still reaches exactly that peer while the shared values already stored (speed, duplex, bpdu_guard, every member) are carried unchanged, and a
real shared change next to it is judged by the rule that owns it. They reuse the A1, vPC and multi-member harnesses; nothing here is a new framework.

Synthetic fixtures, controller mocked at its boundary. NOT LIVE TESTED IN THIS GENERATION.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

import pytest

from . import test_dcnm_intf_pvlan_multimember as MM
from . import test_dcnm_intf_pvlan_vpc_a1_description as A1
from . import test_dcnm_intf_pvlan_vpc_harness as V

COMBINED = "speed and duplex cannot change in the same request"


def _have(**shared):
    """The stored parent of a coherent vPC, with some shared values already set."""
    nv = dict(V.created_ctrl().parents[V.VPC]["nvPairs"])
    nv.update(shared)
    return nv


def _ctrl(**shared):
    ctrl = V.created_ctrl()
    nv = ctrl.parents[V.VPC]["nvPairs"]
    nv.update(shared)
    ctrl._expand_children(nv)
    return ctrl


def _sent(ctrl):
    assert len(ctrl.modifies()) == 1, ctrl.modifies()
    return json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]


# ============================================================================ speed / duplex stored on the vPC
@pytest.mark.parametrize("peer", [1, 2])
def test_postr2a1_description_alone_carries_a_fixed_speed_and_duplex_unchanged(peer):
    have = _have(SPEED="1Gb", PORT_DUPLEX_MODE="full")
    out = A1.reconcile({"peer%d_description" % peer: "x"}, have)
    assert out["update"] is True and out["ask_legs"] == [peer - 1] and not out["blocked"], out["blocked"]
    assert sorted(out["changed"]) == ["PEER%d_PO_DESC" % peer]
    assert out["nv"]["SPEED"] == "1Gb" and out["nv"]["PORT_DUPLEX_MODE"] == "full"


def test_postr2a1_restating_the_stored_speed_and_duplex_is_not_a_second_change():
    have = _have(SPEED="1Gb", PORT_DUPLEX_MODE="full")
    out = A1.reconcile({"peer1_description": "x", "speed": "1gb", "duplex": "full"}, have)
    assert out["update"] is True and out["ask_legs"] == [0] and not out["blocked"], out["blocked"]
    assert sorted(out["changed"]) == ["PEER1_PO_DESC"]


def test_postr2a1_a_combined_speed_and_duplex_change_next_to_a_description_is_refused_by_its_own_rule():
    have = _have()  # Auto / auto
    out = A1.reconcile({"peer1_description": "x", "speed": "1Gb", "duplex": "full"}, have)
    assert out["update"] is False and any(COMBINED in b for b in out["blocked"]), out["blocked"]


def test_postr2a1_a_duplex_change_alone_next_to_a_description_reaches_both_peers_not_just_one():
    have = _have(SPEED="1Gb")
    out = A1.reconcile({"peer1_description": "x", "duplex": "full"}, have)
    assert out["update"] is True and out["ask_legs"] == [0, 1] and not out["blocked"], "a shared field reaches both peers: A1 does not apply"


def test_postr2a1_description_alone_does_not_hide_the_duplex_needs_a_fixed_speed_rule():
    out = A1.reconcile({"peer1_description": "x", "duplex": "full"}, _have())  # speed stays Auto
    assert out["update"] is False and any("needs a fixed speed" in b for b in out["blocked"]), out["blocked"]


def test_postr2a1_main_description_alone_keeps_speed_and_duplex_in_the_outbound_request():
    ctrl = _ctrl(SPEED="1Gb", PORT_DUPLEX_MODE="full")
    status, res = V.run_vpc(ctrl, [V.vpc_item(deploy=False, peer2_description="x")])
    assert status == "exit" and res["changed"] is True, res.get("msg")
    sent = _sent(ctrl)
    assert sent["PEER2_PO_DESC"] == "x" and sent["PEER1_PO_DESC"] == ""
    assert (sent["SPEED"], sent["PORT_DUPLEX_MODE"]) == ("1Gb", "full")


def test_postr2a1_main_combined_change_with_a_description_writes_nothing():
    ctrl = _ctrl()
    status, res = V.run_vpc(ctrl, [V.vpc_item(deploy=False, peer1_description="x", speed="1Gb", duplex="full")])
    assert status == "fail" and COMBINED in res["msg"], res.get("msg")
    assert ctrl.writes() == [] and ctrl.deploys() == []


# ============================================================================ input parity (bpdu_guard / speed spellings)
def test_postr2a1_alias_spellings_of_the_stored_values_send_the_same_request_as_the_description_alone():
    plain = _ctrl()
    st_p, res_p = V.run_vpc(plain, [V.vpc_item(deploy=False, peer1_description="x")])
    alias = _ctrl()
    st_a, res_a = V.run_vpc(alias, [V.vpc_item(deploy=False, peer1_description="x", bpdu_guard="TRUE", speed="AUTO")])
    assert st_p == st_a == "exit", (res_p.get("msg"), res_a.get("msg"))
    assert [m[2] for m in alias.modifies()] == [m[2] for m in plain.modifies()], "identical bytes: the aliases restate stored values"
    assert _sent(alias)["BPDUGUARD_ENABLED"] == "true" and _sent(alias)["SPEED"] == "Auto"


def test_postr2a1_a_real_change_of_a_shared_value_with_an_alias_reaches_both_peers():
    ctrl = _ctrl()
    status, res = V.run_vpc(ctrl, [V.vpc_item(deploy=False, peer1_description="x", bpdu_guard="NO")])
    assert status == "exit" and res["changed"] is True, res.get("msg")
    sent = _sent(ctrl)
    assert sent["BPDUGUARD_ENABLED"] == "no" and sent["PEER1_PO_DESC"] == "x" and sent["PEER2_PO_DESC"] == ""


@pytest.mark.parametrize("field,value", [("bpdu_guard", "yes"), ("speed", "1000")])
def test_postr2a1_an_invalid_spelling_next_to_a_description_fails_before_any_write(field, value):
    ctrl = _ctrl()
    status, res = V.run_vpc(ctrl, [V.vpc_item(deploy=False, peer1_description="x", **{field: value})])
    assert status == "fail" and field in res["msg"], res.get("msg")
    assert ctrl.writes() == []


# ============================================================================ multi-member vPC
def test_postr2a1_helper_description_alone_with_two_members_per_peer_and_respelled_ports():
    have = _have(PEER1_MEMBER_INTERFACES=",".join(MM.PORTS[V.SN1]), PEER2_MEMBER_INTERFACES=",".join(MM.PORTS[V.SN2]))
    respelled = [p.replace("Ethernet", "e") for p in reversed(MM.PORTS[V.SN1])]
    out = A1.reconcile({"peer1_members": respelled, "peer2_members": MM.PORTS[V.SN2], "peer1_description": "x"}, have)
    assert out["update"] is True and out["ask_legs"] == [0] and not out["blocked"], out["blocked"]
    assert sorted(out["changed"]) == ["PEER1_PO_DESC"], "the same ports in another spelling and order are not a membership change"


def test_postr2a1_helper_description_with_a_member_change_of_the_same_peer_stays_refused_with_two_members():
    have = _have(PEER1_MEMBER_INTERFACES=",".join(MM.PORTS[V.SN1]), PEER2_MEMBER_INTERFACES=",".join(MM.PORTS[V.SN2]))
    joined = MM.PORTS[V.SN1] + ["Ethernet1/20"]
    out = A1.reconcile({"peer1_members": joined, "peer2_members": MM.PORTS[V.SN2], "peer1_description": "x"}, have)
    assert out["update"] is False and any("changes only peer 1" in b for b in out["blocked"]), out["blocked"]
    # replaced states the complete membership: dropping a member next to the description is the same refused combination
    dropped = A1.reconcile({"peer1_members": MM.PORTS[V.SN1][:1], "peer2_members": MM.PORTS[V.SN2], "peer1_description": "x"}, have, state="replaced")
    assert dropped["update"] is False and any("changes only peer 1" in b for b in dropped["blocked"]), dropped["blocked"]


def test_postr2a1_helper_merged_never_drops_a_member_so_a_subset_next_to_a_description_is_description_only():
    have = _have(PEER1_MEMBER_INTERFACES=",".join(MM.PORTS[V.SN1]), PEER2_MEMBER_INTERFACES=",".join(MM.PORTS[V.SN2]))
    out = A1.reconcile({"peer1_members": MM.PORTS[V.SN1][:1], "peer2_members": MM.PORTS[V.SN2], "peer1_description": "x"}, have)
    assert out["update"] is True and out["ask_legs"] == [0] and sorted(out["changed"]) == ["PEER1_PO_DESC"], out["blocked"]
    assert out["nv"]["PEER1_MEMBER_INTERFACES"] == ",".join(MM.PORTS[V.SN1]), "merged keeps every stored member"


@pytest.mark.parametrize("peer", [1, 2])
def test_postr2a1_main_description_alone_on_a_two_members_per_peer_vpc_deploys_one_peer_and_gates_both(peer):
    ctrl = MM.seeded_vpc()
    touched, other = (V.SN1, V.SN2) if peer == 1 else (V.SN2, V.SN1)
    MM.queue(ctrl, V.converged_preview)  # prior: both peers converged
    for serial in (touched, other):
        ports = MM.PORTS[serial]
        factory = (V.description_preview, "", "multi") if serial == touched else (V.converged_preview,)
        ctrl.vpc_previews[serial].append(MM.combine_previews(serial, ports, *factory))
    item = MM.vpc_item(**{"peer%d_description" % peer: "multi"})
    status, res = V.run_vpc(ctrl, [item])
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert len(ctrl.modifies()) == 1 and len(ctrl.deploys()) == 1 and ctrl.creates() == []
    sent = _sent(ctrl)
    assert sent["PEER%d_PO_DESC" % peer] == "multi" and sent["PEER%d_PO_DESC" % (3 - peer)] == ""
    assert sent["PEER1_MEMBER_INTERFACES"] == ",".join(MM.PORTS[V.SN1]) and sent["PEER2_MEMBER_INTERFACES"] == ",".join(MM.PORTS[V.SN2])
    # with several members there is one gate record per member: every record of a serial must carry that serial's decision
    for serial, expected in ((touched, "deploy"), (other, "converged")):
        records = [g for g in res["pvlan_gate"] if g["site"] == "deploy" and g["serial"] == serial]
        assert records and all(g["targets"] == {V.VPC: expected} for g in records), (serial, expected, records)
