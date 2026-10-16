"""A1: the description of ONE vPC peer may change alone (existing vPC, int_vpc_pvlan_host). Real main() through the EXISTING vPC harness
(VpcController: two peers, per-serial previews). Fixtures are SYNTHETIC (template-shaped); NOT LIVE TESTED.

What is asserted (not only changed=true): the OUTBOUND parent request (the exact nvPairs of the one interface/modify), the per-peer gate
records (site + peer + serial + decision, never a count over the whole list), the order of the calls, the untouched peer's intended value
and its convergence. Gate records of an update: two `prior` records (converged) and two `deploy` records; the touched peer `deploy`, the
untouched one `converged`.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .test_dcnm_intf_pvlan_harness import preview
from .test_dcnm_intf_pvlan_vpc_harness import (
    IP1,
    IP2,
    M1,
    M2,
    PAIR,
    SN1,
    SN2,
    VPC,
    VPC_HOST,
    converged_preview,
    created_ctrl,
    description_preview,
    member_after,
    po_stanza,
    run_vpc,
    vpc_item,
)

SERIAL = {1: SN1, 2: SN2}
PORT = {SN1: M1, SN2: M2}


def gate(result, site, serial):
    recs = [g for g in result["pvlan_gate"] if g["site"] == site and g["serial"] == serial]
    assert len(recs) == 1, (site, serial, result["pvlan_gate"])
    return recs[0]


def queue(ctrl, touched, old, new, other_desc=None):
    """Previews: the touched serial converged then pending `description`; the untouched serial converged twice (nothing to deploy)."""
    other = SN2 if touched == SN1 else SN1
    ctrl.vpc_previews[touched] = [converged_preview(touched, PORT[touched], desc=old), description_preview(touched, PORT[touched], old, new)]
    ctrl.vpc_previews[other] = [converged_preview(other, PORT[other], desc=other_desc), converged_preview(other, PORT[other], desc=other_desc)]
    return other


def removal_preview(serial, port, old):
    pending = ["interface port-channel10", "  no description %s" % old]
    return preview(pending, serial=serial, running=po_stanza(desc=old) + member_after(port), expected=po_stanza() + member_after(port))


def outbound(ctrl):
    assert len(ctrl.modifies()) == 1, ctrl.modifies()
    body = json.loads(ctrl.modifies()[0][2])
    assert len(body) == 1 and body[0]["policy"] == VPC_HOST and body[0]["interfaces"][0]["serialNumber"] == PAIR
    return body[0]["interfaces"][0]["nvPairs"]


def assert_one_peer_update(ctrl, result, touched):
    other = SN2 if touched == SN1 else SN1
    assert result["changed"] is True
    assert gate(result, "prior", SN1)["targets"] == {VPC: "converged"} and gate(result, "prior", SN2)["targets"] == {VPC: "converged"}
    assert gate(result, "deploy", touched)["targets"] == {VPC: "deploy"}
    assert gate(result, "deploy", other)["targets"] == {VPC: "converged"}, "the untouched peer is judged and must converge"
    assert gate(result, "deploy", SN1)["peer"] == 1 and gate(result, "deploy", SN2)["peer"] == 2
    assert ctrl.order() == ["PREVIEW", "PREVIEW", "MODIFY", "PREVIEW", "PREVIEW", "DEPLOY"]
    assert len(ctrl.deploys()) == 1 and ctrl.creates() == []


@pytest.mark.parametrize("peer", [1, 2])
def test_merged_description_of_one_peer_alone_sends_one_parent_modify_and_gates_each_peer(peer):
    ctrl = created_ctrl()
    touched = SERIAL[peer]
    queue(ctrl, touched, None, "site-%d" % peer)
    status, result = run_vpc(ctrl, [vpc_item(**{"peer%d_description" % peer: "site-%d" % peer})], state="merged")
    assert status == "exit", result.get("msg")
    assert_one_peer_update(ctrl, result, touched)
    sent = outbound(ctrl)
    assert sent["PEER%d_PO_DESC" % peer] == "site-%d" % peer
    assert sent["PEER%d_PO_DESC" % (3 - peer)] == "", "the other peer keeps what the controller holds"
    assert sent["COPY_DESC"] == "false" and sent["ADMIN_STATE"] == "false" and sent["PEER1_PCID"] == "10" and sent["PEER2_PCID"] == "10"
    assert P.pairs_from_wire(sent["ASSOCIATION_LIST"], "ASSOCIATION_LIST") == [(2210, 2212)] and len(sent) >= 39, "the FULL nvPair set is sent"
    assert ctrl.parents[VPC]["nvPairs"]["PEER%d_PO_DESC" % peer] == "site-%d" % peer


def test_switch_list_inversion_maps_peer1_description_to_the_controllers_second_serial():
    ctrl = created_ctrl()
    queue(ctrl, SN2, None, "inv")  # peer1_* belong to switch[0] = IP2 = the controller's SECOND serial
    item = vpc_item(peer1_description="inv", switches=[IP2, IP1], peer1_members=[M2], peer2_members=[M1])
    status, result = run_vpc(ctrl, [item], state="merged")
    assert status == "exit", result.get("msg")
    assert_one_peer_update(ctrl, result, SN2)
    sent = outbound(ctrl)
    assert sent["PEER2_PO_DESC"] == "inv" and sent["PEER1_PO_DESC"] == "", "the value lands on the serial that owns it, in controller order"


def test_merged_omission_preserves_the_other_peers_description():
    ctrl = created_ctrl(descs=("keep-a", "keep-b"))
    queue(ctrl, SN1, "keep-a", "new-a", other_desc="keep-b")
    status, result = run_vpc(ctrl, [vpc_item(peer1_description="new-a")], state="merged")
    assert status == "exit", result.get("msg")
    assert_one_peer_update(ctrl, result, SN1)
    sent = outbound(ctrl)
    assert sent["PEER1_PO_DESC"] == "new-a" and sent["PEER2_PO_DESC"] == "keep-b"


def test_replaced_keeps_its_reset_semantics_and_computes_the_final_intent():
    # the omitted peer 2 returns to the template default "": here it already is "", so only peer 1 changes (a one-peer update)
    ctrl = created_ctrl(descs=("old-a", ""))
    queue(ctrl, SN1, "old-a", "new-a")
    status, result = run_vpc(ctrl, [vpc_item(peer1_description="new-a")], state="replaced")
    assert status == "exit", result.get("msg")
    assert_one_peer_update(ctrl, result, SN1)
    sent = outbound(ctrl)
    assert sent["PEER1_PO_DESC"] == "new-a" and sent["PEER2_PO_DESC"] == ""
    # an omitted peer 2 that currently HOLDS a description is reset by replaced: that is a two-peer update (already supported), not A1
    ctrl = created_ctrl(descs=("old-a", "old-b"))
    ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1, desc="old-a"), description_preview(SN1, M1, "old-a", "new-a")]
    ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2, desc="old-b"), removal_preview(SN2, M2, "old-b")]
    status, result = run_vpc(ctrl, [vpc_item(peer1_description="new-a")], state="replaced")
    assert status == "exit", result.get("msg")
    sent = outbound(ctrl)
    assert sent["PEER1_PO_DESC"] == "new-a" and sent["PEER2_PO_DESC"] == "", "replaced resets the omitted description of the other peer"
    assert gate(result, "deploy", SN1)["targets"] == {VPC: "deploy"} and gate(result, "deploy", SN2)["targets"] == {VPC: "deploy"}


def test_the_same_request_again_is_a_zero_write_noop():
    ctrl = created_ctrl(descs=("site-1", ""))
    ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1, desc="site-1")]
    ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2)]
    status, result = run_vpc(ctrl, [vpc_item(peer1_description="site-1")], state="merged")
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.writes() == [] and ctrl.deploys() == [] and result.get("response") == []
    assert gate(result, "prior", SN1)["targets"] == {VPC: "converged"} and gate(result, "prior", SN2)["targets"] == {VPC: "converged"}
    assert [g["site"] for g in result["pvlan_gate"]] == ["prior", "prior"]


def test_an_unexpected_pending_on_the_untouched_peer_prevents_the_deploy():
    ctrl = created_ctrl()
    ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1), description_preview(SN1, M1, None, "a")]
    ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2), description_preview(SN2, M2, None, "zz")]  # a pending nobody asked for
    status, result = run_vpc(ctrl, [vpc_item(peer1_description="a")], state="merged")
    assert status == "fail", result
    assert gate(result, "deploy", SN1)["targets"] == {VPC: "deploy"} and gate(result, "deploy", SN2)["targets"] == {VPC: "refuse"}
    assert "peer 2" in result["msg"] and "description zz" in result["msg"]
    assert ctrl.deploys() == [], "nothing is deployed: the intent was written (known pre-deploy limit) but the deploy is blocked"


def test_copy_description_true_makes_a_new_unilateral_description_refuse_before_any_write():
    ctrl = created_ctrl()
    ctrl.parents[VPC]["nvPairs"]["COPY_DESC"] = "true"
    ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1)]
    ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2)]
    status, result = run_vpc(ctrl, [vpc_item(peer1_description="a", copy_description=True)], state="merged")
    assert status == "fail" and "copy_description is true" in result["msg"] and "peer 1" in result["msg"], result.get("msg")
    assert ctrl.writes() == [] and ctrl.modifies() == [] and ctrl.deploys() == []
    # same through the controller's stored value (the request does not state copy_description)
    ctrl = created_ctrl()
    ctrl.parents[VPC]["nvPairs"]["COPY_DESC"] = "true"
    status, result = run_vpc(ctrl, [vpc_item(peer2_description="b")], state="merged")
    assert status == "fail" and "copy_description is true" in result["msg"] and "peer 2" in result["msg"], result.get("msg")
    assert ctrl.writes() == []


@pytest.mark.parametrize(
    "delta",
    [{"peer1_cmds": ["logging event port link-status"]}, {"peer2_cmds": ["logging event port link-status"]}],
    ids=["peer1-freeform", "peer2-freeform"],
)
def test_a_unilateral_freeform_stays_refused_before_any_write(delta):
    ctrl = created_ctrl()
    ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1)]
    ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2)]
    status, result = run_vpc(ctrl, [vpc_item(**delta)], state="merged")
    assert status == "fail" and "changes only peer" in result["msg"] and ctrl.writes() == [], result.get("msg")


# ---- helper level: native/allowed of ONE peer stay refused (trunk modes); both peers, shared fields and membership unchanged
def trunk_have(mode, native="100", allowed="2210-2212"):
    ctrl = created_ctrl()
    h = copy.deepcopy(ctrl.parents[VPC]["nvPairs"])
    h.update(
        PVLAN_MODE=mode, PEER1_PVLAN_NATIVE_VLAN=native, PEER2_PVLAN_NATIVE_VLAN=native, PEER1_PVLAN_ALLOWED_VLANS=allowed, PEER2_PVLAN_ALLOWED_VLANS=allowed
    )
    h["ASSOCIATION_LIST"] = h["ASSOCIATION_LIST"] if mode == "trunk secondary" else ""
    h["MAPPING_LIST"] = "" if mode == "trunk secondary" else json.dumps({"MAPPING_LIST": [{"P_VLAN": "2210", "S_VLAN": "2212"}]}, separators=(",", ":"))
    return h


def reconcile(raw_delta, have, state="merged"):
    raw = {
        "pvlan_mode": "host",
        "peer1_members": [M1],
        "peer2_members": [M2],
        "peer1_pcid": 10,
        "peer2_pcid": 10,
        "admin_state": False,
        "pvlan_association": [{"primary_vlan": 2210, "secondary_vlan": 2212}],
    }
    raw.update(raw_delta)
    legs = P.vpc_pair_view(raw, PAIR, [SN1, SN2])
    return P.reconcile_vpc(state, raw, VPC, legs, VPC_HOST, copy.deepcopy(have))


@pytest.mark.parametrize("field", ["peer1_native_vlan", "peer1_allowed_vlans"])
def test_unilateral_native_or_allowed_stays_refused_in_trunk_secondary(field):
    value = 200 if "native" in field else "2210-2211"
    out = reconcile({"pvlan_mode": "trunk secondary", field: value}, trunk_have("trunk secondary"))
    assert out["update"] is False and any("changes only peer 1" in b for b in out["blocked"]), out["blocked"]


def test_helper_admits_the_two_peer_and_shared_cases_unchanged():
    have = trunk_have("trunk secondary")
    both = reconcile({"pvlan_mode": "trunk secondary", "peer1_native_vlan": 200, "peer2_native_vlan": 200}, have)
    assert both["update"] is True and both["ask_legs"] == [0, 1] and not both["blocked"]
    out = reconcile({"peer1_description": "a", "peer2_description": "b"}, created_ctrl().parents[VPC]["nvPairs"])
    assert out["update"] is True and out["ask_legs"] == [0, 1] and not out["blocked"]
    out = reconcile({"admin_state": True}, created_ctrl().parents[VPC]["nvPairs"])
    assert out["update"] is True and out["ask_legs"] == [0, 1] and not out["blocked"]


def test_helper_unilateral_description_decision_and_copy_description_guard():
    have = created_ctrl().parents[VPC]["nvPairs"]
    ok = reconcile({"peer2_description": "b"}, have)
    assert ok["update"] is True and ok["ask_legs"] == [1] and sorted(ok["changed"]) == ["PEER2_PO_DESC"] and not ok["blocked"]
    have_copy = dict(have, COPY_DESC="true")
    bad = reconcile({"peer2_description": "b"}, have_copy)
    assert bad["update"] is False and any("copy_description is true" in b for b in bad["blocked"]), bad["blocked"]
    both = reconcile({"peer1_description": "a", "peer2_description": "b"}, have_copy)
    assert both["update"] is True and both["ask_legs"] == [0, 1] and not both["blocked"], "COPY_DESC=true with BOTH peers is unchanged"
    # a request that flips copy_description changes a SHARED key: it reaches both peers, so A1 does not apply
    flip = reconcile({"peer1_description": "a", "copy_description": True}, have)
    assert flip["ask_legs"] == [0, 1]


def test_description_plus_members_of_one_peer_stays_refused_as_a_documented_limit():
    """A1 limit: the combination was composed offline in a throwaway copy with a hand-built fixture (probes/probe_combo.py) but no real pending
    shape exists for a join next to a description change, so it keeps the existing refusal. Membership-only and description-only stay admitted."""
    have = created_ctrl().parents[VPC]["nvPairs"]
    both = reconcile({"peer1_members": [M1, "Ethernet1/9"], "peer1_description": "a"}, have)
    assert both["update"] is False and any(
        "changes only peer 1" in b and "PEER1_MEMBER_INTERFACES" in b and "PEER1_PO_DESC" in b for b in both["blocked"]
    ), both["blocked"]
    members = reconcile({"peer1_members": [M1, "Ethernet1/9"]}, have)
    assert members["update"] is True and members["ask_legs"] == [0] and not members["blocked"], "the existing membership-only exception is untouched"
    desc = reconcile({"peer1_description": "a"}, have)
    assert desc["update"] is True and desc["ask_legs"] == [0] and not desc["blocked"]
    # description on one peer + members on the OTHER peer reaches both peers: supported before and after
    cross = reconcile({"peer1_description": "a", "peer2_members": [M2, "Ethernet1/9"]}, have)
    assert cross["update"] is True and cross["ask_legs"] == [0, 1] and not cross["blocked"]
