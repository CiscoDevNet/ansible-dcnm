"""PVLAN vPC whose port-channel numbers (peer1_pcid / peer2_pcid) differ from the vPC id and from each other -- the regular vPC contract.

NOT LIVE TESTED. Same harness as test_dcnm_intf_pvlan_vpc.py. The simulated controller already builds each child from the parent's own
PEERn_PCID; the device stanzas of the harness are written for Po 10 and are remapped here per peer (`port-channel10` / `channel-group 10`
become that peer's number; `vpc 10` stays: it is the vPC id). Every `run_vpc` is a NEW process image: nothing is remembered from the call that
created the vPC.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .test_dcnm_intf_pvlan_harness import TRUNK

from .test_dcnm_intf_pvlan_vpc_harness import (
    IP1,
    IP2,
    M1,
    M2,
    PAIR,
    SN1,
    SN2,
    VPC,
    PO_MEMBER,
    VPC_HOST,
    VPC_PO,
    VpcController,
    baseline_ctrl,
    converged_preview,
    converged_previews,
    create_previews,
    created_ctrl,
    delete_previews,
    description_preview,
    pc_mode_preview,
    release_only,
    run_vpc,
    update_preview,
    vpc_del_item,
    vpc_item,
)

# (peer1 = SN1, peer2 = SN2). All differ from the vPC id 10; the second is asymmetric; the third swaps them.
PCIDS = [("11", "11"), ("11", "12"), ("12", "11"), ("4096", "1")]
BASE_VID = "10"


def _remap_line(line, pcid):
    return line.replace("port-channel10", "port-channel" + pcid).replace("channel-group 10", "channel-group " + pcid)


def _remap_answer(answer, pcid):
    if callable(answer):
        return lambda path, _a=answer: _remap_answer(_a(path), pcid)
    out = copy.deepcopy(answer)
    for entry in out.get("DATA") or []:
        for key in ("pendingConfig", "runningConfig", "expectedConfig"):
            if isinstance(entry.get(key), list):
                entry[key] = [_remap_line(x, pcid) for x in entry[key]]
    return out


def remap(ctrl, pcids):
    """Rewrite the queued previews of both peers for their own port-channel numbers."""
    for serial, pcid in ((SN1, pcids[0]), (SN2, pcids[1])):
        ctrl.vpc_previews[serial] = [_remap_answer(a, pcid) for a in ctrl.vpc_previews.get(serial, [])]
    return ctrl


def seeded(pcids, **kw):
    return created_ctrl(pcids=pcids, **kw)


def po(serial_index, pcids):
    return "port-channel" + pcids[serial_index]


def sent_nv(ctrl):
    body = json.loads(ctrl.creates()[0][2])
    body = body[0] if isinstance(body, list) else body
    return body["interfaces"][0]["nvPairs"]


# ================================================================== the contract (pure function, raw input)
def _profile(**kw):
    prof = {"pvlan_mode": "host", "mode": "pvlan", "peer1_members": [M1], "peer2_members": [M2],
            "pvlan_association": [{"primary_vlan": 2210, "secondary_vlan": 2212}]}
    prof.update(kw)
    return prof


@pytest.mark.parametrize("kw", [
    {}, {"peer1_pcid": 11}, {"peer2_pcid": 12}, {"peer1_pcid": 11, "peer2_pcid": 12}, {"peer1_pcid": 10, "peer2_pcid": 10},
    {"peer1_pcid": 1, "peer2_pcid": 4096},
])
def test_valid_pcid_inputs_are_accepted_whether_or_not_they_equal_the_vpc_id(kw):
    assert P.vpc_not_implemented(_profile(**kw), "vPC10") == []


@pytest.mark.parametrize("value", [0, 4097, -1, True, 11.5, "11", [11]])
@pytest.mark.parametrize("key", ["peer1_pcid", "peer2_pcid"])
def test_an_invalid_pcid_is_refused_before_any_read(key, value):
    reasons = P.vpc_not_implemented(_profile(**{key: value}), "vPC10")
    assert reasons and any(key in r and "1 to 4096" in r for r in reasons), reasons


def test_the_pair_view_binds_each_pcid_to_the_serial_that_owns_it_and_defaults_to_the_vpc_id():
    raw = _profile(peer1_pcid=11, peer2_pcid=12, peer1_members=["Ethernet1/7"], peer2_members=["Ethernet1/8"])
    legs = P.vpc_pair_view(raw, PAIR, [SN2, SN1], "vPC10")  # playbook switches reversed: peer1_* belong to SN2
    by_serial = dict((leg["serial"], (leg["pcid"], leg["pcid_given"])) for leg in legs)
    assert by_serial == {SN2: (11, True), SN1: (12, True)}
    legs = P.vpc_pair_view(_profile(), PAIR, [SN1, SN2], "vPC10")
    assert [(leg["pcid"], leg["pcid_given"]) for leg in legs] == [("10", False), ("10", False)]


# ================================================================== creation
@pytest.mark.parametrize("pcids", PCIDS)
def test_creation_sends_each_peers_own_port_channel_number_and_both_children_are_judged_by_it(pcids):
    ctrl = baseline_ctrl()
    create_previews(ctrl)
    remap(ctrl, pcids)
    status, result = run_vpc(ctrl, [vpc_item(peer1_pcid=int(pcids[0]), peer2_pcid=int(pcids[1]))])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    nv = sent_nv(ctrl)
    assert (nv["PEER1_PCID"], nv["PEER2_PCID"]) == pcids
    assert po(0, pcids) in ctrl.nodes[SN1] and po(1, pcids) in ctrl.nodes[SN2]
    if BASE_VID not in pcids:
        assert "port-channel10" not in ctrl.nodes[SN1] and "port-channel10" not in ctrl.nodes[SN2]
    assert [g["peer"] for g in result["pvlan_gate"]] == [1, 2] and all(g["targets"][VPC] == "deploy" for g in result["pvlan_gate"])
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1


def test_creation_with_the_playbook_switches_swapped_keeps_each_number_with_its_serial():
    ctrl = baseline_ctrl()
    create_previews(ctrl)
    remap(ctrl, ("11", "12"))
    # peer1_* of the playbook belong to its FIRST switch (SN2 here): SN2 owns 12 and SN1 owns 11
    status, result = run_vpc(ctrl, [vpc_item(switches=[IP2, IP1], peer1_members=[M2], peer2_members=[M1], peer1_pcid=12, peer2_pcid=11)])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    nv = sent_nv(ctrl)
    assert (nv["PEER1_PCID"], nv["PEER2_PCID"]) == ("11", "12") and nv["PEER1_MEMBER_INTERFACES"] == M1
    assert "port-channel11" in ctrl.nodes[SN1] and "port-channel12" in ctrl.nodes[SN2]


def test_omitted_pcids_default_to_the_vpc_id_on_a_creation_exactly_as_before():
    ctrl = baseline_ctrl()
    create_previews(ctrl)
    item = vpc_item()
    item["profile"].pop("peer1_pcid"), item["profile"].pop("peer2_pcid")
    status, result = run_vpc(ctrl, [item])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert (sent_nv(ctrl)["PEER1_PCID"], sent_nv(ctrl)["PEER2_PCID"]) == ("10", "10")


def test_only_one_pcid_given_the_other_defaults_to_the_vpc_id():
    ctrl = baseline_ctrl()
    create_previews(ctrl)
    remap(ctrl, ("11", "10"))
    item = vpc_item(peer1_pcid=11)
    item["profile"].pop("peer2_pcid")
    status, result = run_vpc(ctrl, [item])
    assert status == "exit", result.get("msg")
    assert (sent_nv(ctrl)["PEER1_PCID"], sent_nv(ctrl)["PEER2_PCID"]) == ("11", "10")


@pytest.mark.parametrize("side", [0, 1])
def test_a_child_port_channel_that_already_exists_on_either_peer_refuses_the_creation_with_no_write(side):
    pcids = ("11", "12")
    ctrl = baseline_ctrl()
    serial = (SN1, SN2)[side]
    ctrl.nodes[serial]["port-channel" + pcids[side]] = {"policy": "int_port_channel_trunk_host", "nvPairs": {"PO_ID": "po"}}
    create_previews(ctrl)
    remap(ctrl, pcids)
    status, result = run_vpc(ctrl, [vpc_item(peer1_pcid=11, peer2_pcid=12)])
    assert status == "fail" and ctrl.writes() == [] and "port-channel" + pcids[side] in result["msg"], result.get("msg")


def test_two_vpcs_of_one_request_cannot_claim_the_same_port_channel_number_on_a_peer():
    ctrl = baseline_ctrl()
    create_previews(ctrl)
    first = vpc_item(name="vpc10", peer1_pcid=11, peer2_pcid=11)
    second = vpc_item(name="vpc20", peer1_pcid=11, peer2_pcid=12, peer1_members=["Ethernet1/9"], peer2_members=["Ethernet1/10"])
    status, result = run_vpc(ctrl, [first, second])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")
    assert "port-channel number" in result["msg"] or "also uses" in result["msg"], result["msg"]


# ================================================================== repetition and update (a NEW process each time)
@pytest.mark.parametrize("pcids", PCIDS)
@pytest.mark.parametrize("explicit", [True, False])
def test_identical_repetition_is_a_noop_with_explicit_or_omitted_pcids(pcids, explicit):
    ctrl = seeded(pcids)
    converged_previews(ctrl)
    remap(ctrl, pcids)
    item = vpc_item(peer1_pcid=int(pcids[0]), peer2_pcid=int(pcids[1]))
    if not explicit:
        item["profile"].pop("peer1_pcid"), item["profile"].pop("peer2_pcid")
    status, result = run_vpc(ctrl, [item])
    assert status == "exit" and result["changed"] is False and ctrl.writes() == [], result.get("msg")


@pytest.mark.parametrize("explicit", [True, False])
def test_a_replaced_update_keeps_the_stored_port_channel_numbers_and_creates_no_other_port_channel(explicit):
    pcids = ("11", "12")
    new = (2210, 2213)
    ctrl = seeded(pcids)
    ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1), update_preview(SN1, M1, (2210, 2212), new)]
    ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2), update_preview(SN2, M2, (2210, 2212), new)]
    remap(ctrl, pcids)
    item = vpc_item(peer1_pcid=11, peer2_pcid=12, pvlan_association=[{"primary_vlan": new[0], "secondary_vlan": new[1]}])
    if not explicit:
        item["profile"].pop("peer1_pcid"), item["profile"].pop("peer2_pcid")
    status, result = run_vpc(ctrl, [item], state="replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.modifies()) == 1 and ctrl.creates() == [] and len(ctrl.deploys()) == 1
    nv = json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]
    assert (nv["PEER1_PCID"], nv["PEER2_PCID"]) == pcids, "an update never changes or defaults the stored numbers"
    assert sorted(k for k in ctrl.nodes[SN1] if k.startswith("port-channel")) == ["port-channel11"]
    assert sorted(k for k in ctrl.nodes[SN2] if k.startswith("port-channel")) == ["port-channel12"]


@pytest.mark.parametrize("explicit", [True, False])
def test_a_merged_update_keeps_the_stored_port_channel_numbers(explicit):
    pcids = ("11", "12")
    ctrl = seeded(pcids, descs=("keep-a", "keep-b"))
    ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1, desc="keep-a"), pc_mode_preview(SN1, M1, "keep-a")]
    ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2, desc="keep-b"), pc_mode_preview(SN2, M2, "keep-b")]
    remap(ctrl, pcids)
    item = vpc_item(peer1_pcid=11, peer2_pcid=12, pc_mode="passive")
    if not explicit:
        item["profile"].pop("peer1_pcid"), item["profile"].pop("peer2_pcid")
    status, result = run_vpc(ctrl, [item], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    sent = json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]
    assert sent["PC_MODE"] == "passive" and (sent["PEER1_PCID"], sent["PEER2_PCID"]) == pcids
    assert sent["PEER1_PO_DESC"] == "keep-a" and sent["PEER2_PO_DESC"] == "keep-b" and len(ctrl.deploys()) == 1


@pytest.mark.parametrize("state", ["replaced", "merged"])
def test_a_description_update_of_both_peers_reaches_payload_and_children_and_keeps_identity_and_association(state):
    """The live driver's update step: ONLY the descriptions change; vPC id, Po numbers, members and association stay (the driver never invents a network)."""
    pcids = ("11", "12")
    ctrl = seeded(pcids, descs=("base-a", "base-b"))
    ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1, desc="base-a"), description_preview(SN1, M1, "base-a", "new-a")]
    ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2, desc="base-b"), description_preview(SN2, M2, "base-b", "new-b")]
    remap(ctrl, pcids)
    status, result = run_vpc(ctrl, [vpc_item(peer1_pcid=11, peer2_pcid=12, peer1_description="new-a", peer2_description="new-b")], state=state)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    nv = json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]
    assert (nv["PEER1_PO_DESC"], nv["PEER2_PO_DESC"]) == ("new-a", "new-b")
    assert (nv["PEER1_PCID"], nv["PEER2_PCID"]) == pcids and (nv["PEER1_MEMBER_INTERFACES"], nv["PEER2_MEMBER_INTERFACES"]) == (M1, M2)
    assert P.pairs_from_wire(nv["ASSOCIATION_LIST"], "ASSOCIATION_LIST") == [(2210, 2212)]
    assert ctrl.nodes[SN1]["port-channel11"]["nvPairs"]["DESC"] == "new-a" and ctrl.nodes[SN2]["port-channel12"]["nvPairs"]["DESC"] == "new-b"
    # the next step of the sequence, still carrying the UPDATED content, is a no-op: nothing reverts it
    ctrl.next_invocation()
    ctrl.calls = []
    ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1, desc="new-a")]
    ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2, desc="new-b")]
    remap(ctrl, pcids)
    status, result = run_vpc(ctrl, [vpc_item(peer1_pcid=11, peer2_pcid=12, peer1_description="new-a", peer2_description="new-b")], state="replaced")
    assert status == "exit" and result["changed"] is False and ctrl.writes() == [], result.get("msg")


@pytest.mark.parametrize("wanted", [("12", "12"), ("11", "11"), ("10", "10")])
def test_changing_the_port_channel_number_of_an_existing_vpc_is_refused_before_any_write(wanted):
    ctrl = seeded(("11", "12"))
    converged_previews(ctrl)
    remap(ctrl, ("11", "12"))
    status, result = run_vpc(ctrl, [vpc_item(peer1_pcid=int(wanted[0]), peer2_pcid=int(wanted[1]))])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")
    assert "changing the port-channel number of an existing vPC is not implemented" in result["msg"]


# ================================================================== deletion (listed parent) in a NEW process
@pytest.mark.parametrize("pcids", PCIDS)
def test_deletion_marks_releases_and_verifies_each_peers_own_child_and_a_repetition_is_a_noop(pcids):
    ctrl = seeded(pcids)
    delete_previews(ctrl)
    remap(ctrl, pcids)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.markdeletes()) == 1 and len(ctrl.deploys()) == 1
    release_only(ctrl)
    assert not any(k.startswith("port-channel") for s in (SN1, SN2) for k in ctrl.nodes[s])
    verification = result["pvlan_verification"][VPC]
    assert verification["state"] == "verified" and verification["peers"] == {SN1: "verified", SN2: "verified"}
    ctrl.next_invocation()
    ctrl.calls = []
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and result["changed"] is False and ctrl.writes() == []


# ================================================================== saved deletion -> NEW process -> deploy -> no-op
def _saved(pcids, deploy_first=False):
    ctrl = seeded(pcids)
    ctrl.children_marked_deleted = True  # MEASURED: the children stay listed, marked, source = the vPC, until the deploy
    ctrl.parent_marked_listed = False
    delete_previews(ctrl)
    remap(ctrl, pcids)
    status, result = run_vpc(ctrl, [vpc_del_item(deploy=deploy_first)], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    return ctrl


@pytest.mark.parametrize("pcids", PCIDS)
def test_a_saved_deletion_is_completed_by_the_next_process_from_the_relation_not_from_the_vpc_id(pcids):
    ctrl = _saved(pcids)
    assert ctrl.deploys() == [] and len(ctrl.markdeletes()) == 1
    # the next process knows nothing: it must find each peer's child through the marked policy whose source is the vPC
    ctrl.next_invocation()
    ctrl.calls = []
    delete_previews(ctrl)
    delete_previews(ctrl)
    for serial in (SN1, SN2):  # the saved-deletion check and the gate each read a fresh preview
        ctrl.vpc_previews[serial] = ctrl.vpc_previews[serial] * 2
    remap(ctrl, pcids)
    status, result = run_vpc(ctrl, [vpc_del_item(deploy=True)], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.deploys()) == 1 and any(s.get("state") == "completing the saved deletion" for s in result["pvlan_saved"]), result.get("pvlan_saved")
    ctrl.next_invocation()
    ctrl.calls = []
    status, result = run_vpc(ctrl, [vpc_del_item(deploy=True)], state="deleted")
    assert status == "exit" and result["changed"] is False and ctrl.writes() == []


def test_a_saved_deletion_whose_peer_lists_two_marked_children_of_the_vpc_is_refused_not_guessed():
    pcids = ("11", "12")
    ctrl = _saved(pcids)
    extra = ctrl._marked_deleted_entry(SN1, "port-channel13")
    ctrl.summary_extra[SN1].append(extra)
    ctrl.next_invocation()
    ctrl.calls = []
    delete_previews(ctrl)
    remap(ctrl, pcids)
    status, result = run_vpc(ctrl, [vpc_del_item(deploy=True)], state="deleted")
    assert status == "fail" and ctrl.deploys() == [] and ctrl.writes() == [], result.get("msg")
    assert "marked for deletion with the vPC as source" in result["msg"]


def test_a_saved_deletion_marked_on_one_peer_only_is_refused_whatever_the_port_channel_numbers():
    pcids = ("11", "12")
    ctrl = _saved(pcids)
    ctrl.summary_extra[SN2] = [e for e in ctrl.summary_extra[SN2] if e["ifName"] != "port-channel12"]
    ctrl.next_invocation()
    ctrl.calls = []
    delete_previews(ctrl)
    remap(ctrl, pcids)
    status, result = run_vpc(ctrl, [vpc_del_item(deploy=True)], state="deleted")
    assert status == "fail" and ctrl.deploys() == [], result.get("msg")


# ================================================================== overridden keeps a requested vPC with its own numbers
class MeasuredVpc(VpcController):
    """The vPC harness with the MEASURED summary `deletable` (child Po and physical members False, parent True), as in test_dcnm_intf_pvlan_po_vpc_reconcile."""

    def _summary_entry(self, serial, name, d, status):
        entry = super(MeasuredVpc, self)._summary_entry(serial, name, d, status)
        if d["policy"] in (VPC_PO, PO_MEMBER, TRUNK, "int_access_host", "int_routed_host"):
            entry["deletable"] = "False"
        return entry


@pytest.mark.parametrize("pcids", PCIDS[:2])
def test_overridden_with_the_complete_scope_keeps_a_vpc_that_has_other_port_channel_numbers(pcids):
    ctrl = MeasuredVpc().seed_baseline().seed_vpc(pcids=pcids)
    ctrl.next_invocation()
    converged_previews(ctrl)
    remap(ctrl, pcids)
    status, result = run_vpc(ctrl, [vpc_item(peer1_pcid=int(pcids[0]), peer2_pcid=int(pcids[1]))], state="overridden")
    assert status == "exit", result.get("msg")
    assert ctrl.markdeletes() == [] and ctrl.deploys() == [], "the requested vPC and its children are retained"
    assert VPC in ctrl.parents and po(0, pcids) in ctrl.nodes[SN1] and po(1, pcids) in ctrl.nodes[SN2]
    assert ctrl.parents[VPC]["policy"] == VPC_HOST
