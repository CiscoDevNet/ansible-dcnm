"""PVLAN vPC identity: child port-channel numbers and saved deletions per switch pair."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P
from unittest.mock import patch

from .helpers.ethernet_controller import TRUNK
from .helpers.vpc_controller import IP1
from .helpers.vpc_controller import IP2
from .helpers.vpc_controller import M1
from .helpers.vpc_controller import M2
from .helpers.vpc_controller import PAIR
from .helpers.vpc_controller import SN1
from .helpers.vpc_controller import SN2
from .helpers.vpc_controller import VPC
from .helpers.vpc_controller import PO_MEMBER
from .helpers.vpc_controller import VPC_HOST
from .helpers.vpc_controller import VPC_PO
from .helpers.vpc_controller import VpcController
from .helpers.vpc_controller import baseline_ctrl
from .helpers.vpc_controller import converged_preview
from .helpers.vpc_controller import converged_previews
from .helpers.vpc_controller import create_previews
from .helpers.vpc_controller import delete_previews
from .helpers.vpc_controller import description_preview
from .helpers.vpc_controller import pc_mode_preview
from .helpers.vpc_controller import release_only
from .helpers.vpc_controller import run_vpc
from .helpers.vpc_controller import update_preview
from .helpers.vpc_controller import vpc_del_item
from .helpers.vpc_controller import vpc_item
from .helpers.vpc_controller import remap
from .helpers.vpc_controller import seeded
from .helpers.vpc_controller import sent_nv
from .helpers import port_channel_release as R
from .helpers import vpc_controller as B
from .helpers import vpc_controller as V
from .helpers.vpc_controller import lo
from .helpers.mixed_controller import vpc_conv_pending
from .helpers.mixed_controller import conv_vpc_running


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_vpc_child_ids.py
# PVLAN vPC whose port-channel numbers (peer1_pcid / peer2_pcid) differ from the vPC id and from each other -- the regular vPC contract.
#
# NOT LIVE TESTED. Same harness as test_pvlan_vpc_lifecycle.py. The simulated controller already builds each child from the parent's own
# PEERn_PCID; the device stanzas of the harness are written for Po 10 and are remapped here per peer (`port-channel10` / `channel-group 10`
# become that peer's number; `vpc 10` stays: it is the vPC id). Every `run_vpc` is a NEW process image: nothing is remembered from the call that
# created the vPC.
# ====================================================================================================
# (peer1 = SN1, peer2 = SN2). All differ from the vPC id 10; the second is asymmetric; the third swaps them.
PCIDS = [("11", "11"), ("11", "12"), ("12", "11"), ("4096", "1")]
BASE_VID = "10"


def po(serial_index, pcids):
    return "port-channel" + pcids[serial_index]


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
    """The vPC harness with the MEASURED summary `deletable` (child Po and physical members False, parent True), as in test_pvlan_po_vpc_common."""

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


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_vpc_saved_pairs.py
# A saved PVLAN vPC deletion is continued per switch pair: two independent pairs may use the same vPC name.
#
# NOT LIVE TESTED. Real main(); only the controller boundary is intercepted, through MultiVpc (test_pvlan_vpc_batch) with two
# pairs. Each pair keeps its own marked-for-deletion listings, previews and deployment state: the deploy of one pair never clears the
# other pair's pending deletion. Every run is a NEW module instance; only the controller state carries over. Values are SYNTHETIC.
#
# Two discovery routes reach the continuation. The vPC named by a `deleted` request (`named`) carries a deploy choice per pair. The
# marked children found by an `overridden` sweep (`marked`) carry the one global deploy choice, so a mixed choice is reachable only
# through the named route.
# ====================================================================================================
PA, PB = B.PA, B.PB
SN3, SN4 = B.PAIRS[1]
ALL = (V.SN1, V.SN2, SN3, SN4)
SAVED = "completing the saved deletion"
AWAITING = "saved, awaiting deployment (nothing written by this run)"
NO_PCIDS = ((None, None), (None, None))
ROUTES = ["named", "marked"]


class PairCtrl(B.MultiVpc):
    """MultiVpc plus one injection: a config-preview answered with HTTP 500 for the listed serials."""

    def __init__(self, npairs=2):
        super(PairCtrl, self).__init__(npairs)
        self.preview_500 = set()

    def __call__(self, mod, method, path, data=None):
        if V.PREVIEW_MARK in path and path.split("config-preview/")[1].split("?")[0] in self.preview_500:
            self.calls.append((method, path, data))
            return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}
        return super(PairCtrl, self).__call__(mod, method, path, data)


class RoutedPairCtrl(PairCtrl):
    """PairCtrl whose mark-delete releases the listed members as the MEASURED routed form of the installed template (86 nvPairs, with
    their own children), the way the border ports of a pair do. A SUCCESS modify that sets a routed member down turns its own
    no_shut_interface into shut_interface (measured). `routed_nv` is the released body."""

    def __init__(self, routed, npairs=2, routed_nv=None):
        super(RoutedPairCtrl, self).__init__(npairs)
        self.routed = frozenset(routed)
        self.routed_nv = R.RELEASED_ROUTED_CDP if routed_nv is None else routed_nv
        self.roles = dict((serial, "border") for serial, _port in self.routed)  # a border port releases routed; an overridden sweep keeps it

    def _released(self, serial, port, k, pcid):
        if (serial, port) not in self.routed:
            return super(RoutedPairCtrl, self)._released(serial, port, k, pcid)
        pending, _running, expected = R.routed_release_preview(port=port, po_number=str(pcid), pair=(V.PRIMARY, V.SECONDARY))
        return pending[1:], expected

    def __call__(self, mod, method, path, data=None):
        resp = super(RoutedPairCtrl, self).__call__(mod, method, path, data)
        if method == "DELETE" and path.endswith(V.MARKDELETE):
            item = json.loads(data)[0]
            _k, pair, first, second = self.plan[self.key(item["serialNumber"], item["ifName"])]
            for serial, ports in zip(pair, (first, second)):
                for port in ports:
                    if (serial, port) in self.routed:
                        nv = copy.deepcopy(self.routed_nv)
                        nv["INTF_NAME"] = port
                        self.nodes[serial][port] = {"policy": R.ROUTED, "nvPairs": nv}
                        self.policies_extra[serial] += R.child_policies(port, R.CHILDREN_UP, serial)
        if method == "POST" and path.endswith(V.MODIFY):
            for payload in json.loads(data):
                for intf in payload["interfaces"]:
                    if payload["policy"] == R.ROUTED and intf["nvPairs"].get("ADMIN_STATE") == "false":
                        for p_ in self.policies_extra[intf["serialNumber"]]:
                            if p_["entityName"] == intf["ifName"] and p_["templateName"] == "no_shut_interface":
                                p_["templateName"], p_["priority"] = "shut_interface", 458
        return resp


# Pair A releases trunk members; the two border peers of pair B release routed ones (vPC id 10: Ethernet1/10 and Ethernet2/10).
BORDER_B = ((SN3, "Ethernet1/10"), (SN4, "Ethernet2/10"))


def border_pair(**kwargs):
    return RoutedPairCtrl(BORDER_B, **kwargs)


def vpc_kwargs(pcids):
    return dict((key, value) for key, value in (("peer1_pcid", pcids[0]), ("peer2_pcid", pcids[1])) if value is not None)


def saved_pairs(ks=(10, 10), pcids=NO_PCIDS, npairs=2, ctrl=None):
    """vPC k0 on pair A and vPC k1 on pair B created and deployed, then BOTH deletions saved with deploy false (invocation 2).
    The controller keeps the children marked for deletion, with the vPC as source, until a deploy names that vPC. `ctrl.saved_calls` keeps
    the requests of the saving run."""
    ctrl = ctrl or PairCtrl(npairs)
    config = [ctrl.add_vpc(ks[i], i, **vpc_kwargs(pcids[i])) for i in range(npairs)]
    assert B.run(ctrl, config)[0] == "exit"
    ctrl.next_invocation()
    ctrl.calls = []
    ctrl.children_marked_deleted = True
    items = [dict(ctrl.del_item(ks[i], i), deploy=False) for i in range(npairs)]
    status, result = B.run(ctrl, items, state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.markdeletes()) == npairs and ctrl.deploys() == []
    for i in range(npairs):
        assert marked(ctrl)[B.PAIRS[i][0]] and marked(ctrl)[B.PAIRS[i][1]], "the saved deletion is pending on both peers"
    ctrl.saved_calls = list(ctrl.calls)
    ctrl.saved_result = result
    ctrl.next_invocation()
    ctrl.calls = []
    return ctrl


def marked(ctrl):
    """{serial: sorted child port-channels the summary lists as marked for deletion}."""
    return dict((s, sorted(e["ifName"] for e in ctrl.summary_extra[s] if str(e.get("markDeleted")) == "True")) for s in sorted(ctrl.nodes))


def policies_marked(ctrl):
    return dict((s, sorted(p["entityName"] for p in ctrl.policies_extra[s] if p.get("templateName") == "interface_delete")) for s in sorted(ctrl.nodes))


def resume(ctrl, route, deploys, ks=(10, 10), order=None, names=None):
    """The next process asks for the saved deletions again. named: `deleted` naming each vPC with its own deploy; marked: an
    `overridden` sweep whose scope is the four switches (one global deploy)."""
    npairs = len(ctrl.pairs)
    if route == "named":
        names = names or [None] * npairs
        items = []
        for i in (order or range(npairs)):
            item = dict(ctrl.del_item(ks[i], i), deploy=deploys[i])
            if names[i]:
                item["name"] = names[i]
            items.append(item)
        return B.run(ctrl, items, state="deleted")
    assert len(set(deploys)) == 1, "the sweep carries one global deploy choice"
    config = [lo(B.IPS[s], deploy=deploys[0]) for s in sorted(ctrl.nodes)]
    original = B.set_module_args
    with patch.object(B, "set_module_args", side_effect=lambda args: original(dict(args, deploy=deploys[0]))):
        return B.run(ctrl, config, state="overridden")


def vpc_writes(ctrl):
    """The non-GET requests of the run that concern an aggregate: (method, endpoint, body) with the loopback requests of the sweep left out."""
    out = []
    for method, path, data in ctrl.calls:
        if method == "GET" or "config-preview" in path or "networkAttachments" in path:
            continue
        body = json.loads(data) if data else None
        if isinstance(body, dict) and body.get("policy") == "int_loopback":
            continue
        if path.endswith(V.DEPLOY):
            body = [d for d in body if "~" in d["serialNumber"]]
            if not body:
                continue
        out.append((method, path.rsplit("/rest/", 1)[-1], body))
    return out


def deployed(ctrl):
    """Every aggregate deploy item of the run, as sent."""
    items = [d for m, p, body in vpc_writes(ctrl) if p == "globalInterface/deploy" for d in body]
    assert all(sorted(d) == ["fabricName", "ifName", "serialNumber"] for d in items), items
    return sorted((d["serialNumber"], d["ifName"], d["fabricName"]) for d in items)


def sent(pair, name="vPC10"):
    return (pair, name, V.FABRIC)


def reports(result):
    return sorted((r["serial"], r["vpc"], r["state"], tuple(r["members"])) for r in result.get("pvlan_saved", []))


def members(pair_index, k=10):
    serials = B.PAIRS[pair_index]
    return ("Ethernet1/%d on %s" % (k, serials[0]), "Ethernet2/%d on %s" % (k, serials[1]))


def judged(result, done, names=("vPC10", "vPC10")):
    """The result keys that describe the deployed pairs: the gate judged both peers of each pair, and the post-deploy verification
    reported each pair under its own identity (the vPC name alone when it is unique in the run, else name@pair)."""
    pairs = (PA, PB)
    composite = len(done) > 1 and len(set(names[i] for i in done)) == 1  # a repeated name is the only one qualified by its pair
    gate = sorted(("delete_deploy", serial, names[i], ((names[i], "deploy"),)) for i in done for serial in B.PAIRS[i])
    assert sorted((g["site"], g["serial"], g["vpc"], tuple(sorted(g["targets"].items()))) for g in result.get("pvlan_gate", [])) == gate
    expected = dict(("%s@%s" % (names[i], pairs[i]) if composite else names[i],
                     ("verified", pairs[i] if composite else None, tuple((serial, "verified") for serial in B.PAIRS[i]))) for i in done)
    got = dict((key, (v["state"], v.get("pair"), tuple(sorted(v["peers"].items())))) for key, v in result.get("pvlan_verification", {}).items())
    assert got == expected, got


def nothing_written(ctrl):
    assert vpc_writes(ctrl) == [], vpc_writes(ctrl)


PCID_CASES = [
    pytest.param(NO_PCIDS, id="po-id-is-vpc-id"),
    pytest.param(((11, 12), (21, 22)), id="po-ids-differ-from-vpc-id-and-between-pairs"),
    pytest.param(((11, 12), (12, 11)), id="po-ids-swapped-between-pairs"),
]


# ============================================================ the same vPC name on two pairs, both deployed
@pytest.mark.parametrize("pcids", PCID_CASES)
@pytest.mark.parametrize("route", ROUTES)
def test_both_pairs_with_the_same_vpc_name_are_completed_and_each_is_deployed_once(route, pcids):
    ctrl = saved_pairs(pcids=pcids)
    status, result = resume(ctrl, route, (True, True))
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert deployed(ctrl) == [sent(PA), sent(PB)]
    assert [w for w in vpc_writes(ctrl) if w[1] != "globalInterface/deploy"] == [], "a saved deletion is not marked or modified again"
    assert reports(result) == [(PA, "vPC10", SAVED, members(0)), (PB, "vPC10", SAVED, members(1))]
    assert ctrl.deployed_vpcs == {(PA, "vPC10"), (PB, "vPC10")}
    judged(result, (0, 1))
    assert marked(ctrl) == dict((s, []) for s in ALL) and policies_marked(ctrl) == dict((s, []) for s in ALL)
    # the next process finds nothing to continue
    ctrl.next_invocation()
    ctrl.calls = []
    status, result = resume(ctrl, route, (True, True))
    assert status == "exit", result.get("msg")
    if route == "named":  # the sweep of the marked route also re-sends its own loopback, which this double does not store
        assert result["changed"] is False
    nothing_written(ctrl)
    assert not result.get("pvlan_saved")


@pytest.mark.parametrize("route", ROUTES)
def test_the_request_order_does_not_select_the_pair(route):
    ctrl = saved_pairs()
    status, result = resume(ctrl, route, (True, True), order=(1, 0))
    assert status == "exit", result.get("msg")
    assert deployed(ctrl) == [sent(PA), sent(PB)]
    assert ctrl.deployed_vpcs == {(PA, "vPC10"), (PB, "vPC10")}
    assert reports(result) == [(PA, "vPC10", SAVED, members(0)), (PB, "vPC10", SAVED, members(1))]
    judged(result, (0, 1))


def test_the_vpc_name_is_normalised_per_request_not_per_spelling():
    ctrl = saved_pairs()
    status, result = resume(ctrl, "named", (True, True), names=("vpc10", "VPC10"))
    assert status == "exit", result.get("msg")
    assert deployed(ctrl) == [sent(PA), sent(PB)]
    assert marked(ctrl) == dict((s, []) for s in ALL)


# ============================================================ the deploy choice and the report belong to the pair
@pytest.mark.parametrize("route", ROUTES)
def test_both_pairs_with_deploy_false_stay_saved_and_both_are_reported_pending(route):
    ctrl = saved_pairs()
    before = (marked(ctrl), policies_marked(ctrl))
    status, result = resume(ctrl, route, (False, False))
    assert status == "exit", result.get("msg")
    nothing_written(ctrl)
    assert reports(result) == [(PA, "vPC10", AWAITING, members(0)), (PB, "vPC10", AWAITING, members(1))]
    assert (marked(ctrl), policies_marked(ctrl)) == before and ctrl.deployed_vpcs == set()


@pytest.mark.parametrize("deploys, order", [((True, False), None), ((False, True), None), ((True, False), (1, 0)), ((False, True), (1, 0))])
def test_each_pair_keeps_its_own_deploy_choice_and_report(deploys, order):
    ctrl = saved_pairs()
    status, result = resume(ctrl, "named", deploys, order=order)
    assert status == "exit", result.get("msg")
    done, kept = (0, 1) if deploys[0] else (1, 0)
    pairs = (PA, PB)
    assert deployed(ctrl) == [sent(pairs[done])]
    judged(result, (done,))
    assert [w for w in vpc_writes(ctrl) if w[1] != "globalInterface/deploy"] == []
    assert reports(result) == sorted([(pairs[done], "vPC10", SAVED, members(done)), (pairs[kept], "vPC10", AWAITING, members(kept))])
    # the deploy of one pair neither completes nor clears the other pair's pending deletion
    assert ctrl.deployed_vpcs == {(pairs[done], "vPC10")}
    for serial in B.PAIRS[done]:
        assert marked(ctrl)[serial] == [] and policies_marked(ctrl)[serial] == []
    for serial in B.PAIRS[kept]:
        assert len(marked(ctrl)[serial]) == 1 and len(policies_marked(ctrl)[serial]) == 1


def test_the_pair_left_saved_is_completed_by_a_later_repeat_and_the_finished_pair_is_not_touched_again():
    ctrl = saved_pairs()
    assert resume(ctrl, "named", (True, False))[0] == "exit"
    ctrl.next_invocation()
    ctrl.calls = []
    status, result = resume(ctrl, "named", (True, True))
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert deployed(ctrl) == [sent(PB)], "pair A was completed by the first run"
    assert reports(result) == [(PB, "vPC10", SAVED, members(1))]
    judged(result, (1,))
    assert ctrl.deployed_vpcs == {(PA, "vPC10"), (PB, "vPC10")} and marked(ctrl) == dict((s, []) for s in ALL)


# ============================================================ controls: unaffected shapes
@pytest.mark.parametrize("route", ROUTES)
def test_control_one_pair_is_completed(route):
    ctrl = saved_pairs(npairs=1)
    status, result = resume(ctrl, route, (True,))
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert deployed(ctrl) == [sent(PA)]
    assert reports(result) == [(PA, "vPC10", SAVED, members(0))]
    judged(result, (0,))
    assert marked(ctrl) == dict((s, []) for s in ALL[:2])


@pytest.mark.parametrize("route", ROUTES)
def test_control_different_vpc_names_on_two_pairs_are_completed(route):
    ctrl = saved_pairs(ks=(10, 11))
    status, result = resume(ctrl, route, (True, True), ks=(10, 11))
    assert status == "exit", result.get("msg")
    assert deployed(ctrl) == [sent(PA), sent(PB, "vPC11")]
    assert reports(result) == [(PA, "vPC10", SAVED, members(0)), (PB, "vPC11", SAVED, members(1, 11))]
    judged(result, (0, 1), names=("vPC10", "vPC11"))
    assert marked(ctrl) == dict((s, []) for s in ALL)


# ============================================================ refusals stay whole-invocation and pair-scoped
@pytest.mark.parametrize("route", ROUTES)
def test_a_peer_listing_two_marked_children_is_refused_naming_that_peer_and_nothing_is_sent(route):
    ctrl = saved_pairs()
    ctrl.summary_extra[SN3].append(ctrl._marked_deleted_entry(SN3, "port-channel13"))
    status, result = resume(ctrl, route, (True, True))
    assert status == "fail", result.get("msg")
    # named: the peer's two children are reported as ambiguous; marked: the sweep names both children and the device holds only one as a PVLAN port-channel
    needle = ("peer %s lists port-channel10, port-channel13 marked for deletion with the vPC as source" if route == "named"
              else "peer 1 (%s): the device does not hold port-channel13 in a PVLAN mode") % SN3
    assert needle in result["msg"], result["msg"]
    assert PA not in result["msg"] and V.SN1 not in result["msg"] and V.SN2 not in result["msg"], "pair A is not blamed"
    nothing_written(ctrl)


@pytest.mark.parametrize("route", ROUTES)
def test_a_saved_deletion_marked_on_one_peer_only_is_refused_naming_that_pair_and_nothing_is_sent(route):
    ctrl = saved_pairs()
    ctrl.summary_extra[SN4] = []
    status, result = resume(ctrl, route, (True, True))
    assert status == "fail", result.get("msg")
    assert "vPC10 on %s: the saved deletion is marked on peer(s) %s only; peer(s) %s list no marked child" % (PB, SN3, SN4) in result["msg"], result["msg"]
    assert PA not in result["msg"]
    nothing_written(ctrl)


@pytest.mark.parametrize("route", ROUTES)
def test_an_unreadable_preview_of_one_peer_refuses_both_pairs_and_nothing_is_sent(route):
    ctrl = saved_pairs()
    ctrl.preview_500.add(SN4)
    status, result = resume(ctrl, route, (True, True))
    assert status == "fail", result.get("msg")
    assert SN4 in result["msg"] and PA not in result["msg"], result["msg"]
    nothing_written(ctrl)


@pytest.mark.parametrize("route", ROUTES)
def test_pending_outside_the_saved_deletion_of_one_pair_is_refused_and_nothing_is_sent(route):
    ctrl = saved_pairs()
    ctrl.extra_pending[SN3] = ["interface Ethernet1/99", "  description unrelated"]
    status, result = resume(ctrl, route, (True, True))
    assert status == "fail", result.get("msg")
    assert "pending exists for interfaces outside this deploy batch: ethernet1/99" in result["msg"] and SN3 in result["msg"], result["msg"]
    nothing_written(ctrl)


@pytest.mark.parametrize("route", ROUTES)
def test_an_unreadable_summary_of_one_peer_is_refused_and_nothing_is_sent(route):
    ctrl = saved_pairs()
    ctrl.read_failures.add("/rest/interface/detail?serialNumber=%s" % SN4)
    status, result = resume(ctrl, route, (True, True))
    assert status == "fail", result.get("msg")
    assert SN4 in result["msg"], result["msg"]
    nothing_written(ctrl)


def test_a_marked_listing_owned_by_another_source_on_one_pair_is_not_completed_and_the_other_pair_is():
    ctrl = saved_pairs()
    for serial in (SN3, SN4):
        for entry in ctrl.summary_extra[serial]:
            entry["underlayPolicies"][0]["source"] = "foreign-owner"
        for policy in ctrl.policies_extra[serial]:
            policy["source"] = "foreign-owner"
    status, result = resume(ctrl, "named", (True, True))
    assert status == "exit", result.get("msg")
    assert deployed(ctrl) == [sent(PA)]
    assert reports(result) == [(PA, "vPC10", SAVED, members(0))]
    assert ctrl.deployed_vpcs == {(PA, "vPC10")}
    assert len(marked(ctrl)[SN3]) == 1 and len(marked(ctrl)[SN4]) == 1, "the foreign listing is left alone"


# ============================================================ discovery is limited to the pair of the request
def summary_reads(ctrl, serial):
    return sum(1 for method, path, _data in ctrl.calls if method == "GET" and "/rest/interface/detail?serialNumber=%s" % serial in path)


def test_a_pair_without_a_saved_deletion_is_not_read_as_a_continuation_because_another_pair_has_one():
    ctrl = saved_pairs()
    assert resume(ctrl, "named", (False, True))[0] == "exit"  # pair B is completed first
    ctrl.next_invocation()
    ctrl.calls = []
    status, result = resume(ctrl, "named", (True, True))
    assert status == "exit", result.get("msg")
    assert deployed(ctrl) == [sent(PA)] and reports(result) == [(PA, "vPC10", SAVED, members(0))]
    assert summary_reads(ctrl, SN4) == 0, "pair B lists no marked child, so its second peer is not read for the saved deletion of pair A"


def test_the_pair_identity_ignores_the_order_of_the_peers_and_keeps_pairs_apart():
    identity = module_class()._dcnm_intf_vpc_pair_identity
    assert identity(PA) == identity(V.SN2 + "~" + V.SN1) == identity(PA.lower())
    assert identity(PA) != identity(PB)
    assert identity(None, V.SN1) == (V.SN1.casefold(),) == identity(V.SN1), "not a pair: stands for itself and is refused later"


def module_class():
    return B.module.DcnmIntf


# ============================================================ contradicting requests are refused, not resolved by order
@pytest.mark.parametrize("vpc_deploy, child_deploy", [(False, True), (True, False)])
def test_a_vpc_and_its_child_requested_with_different_deploy_choices_are_refused_for_that_pair_only(vpc_deploy, child_deploy):
    ctrl = saved_pairs()
    items = [dict(ctrl.del_item(10, 0), deploy=vpc_deploy)] + [
        {"name": "port-channel10", "type": "pc", "switch": [B.IPS[s]], "deploy": child_deploy} for s in B.PAIRS[0]]
    items.append(dict(ctrl.del_item(10, 1), deploy=True))
    status, result = B.run(ctrl, items, state="deleted")
    assert status == "fail", result.get("msg")
    assert "vPC10 on %s: the saved vPC deletion is requested both with and without deployment" % PA in result["msg"], result["msg"]
    assert PB not in result["msg"]
    nothing_written(ctrl)


# ============================================================ the shared discovery also classifies a conventional vPC per pair
class ConvPairCtrl(PairCtrl):
    """PairCtrl plus a CONVENTIONAL trunk vPC `vpc305` saved for deletion on every pair, seeded by hand in the measured form of the
    existing mixed saved-retry doubles: the child port-channel is listed marked with the vPC as source, the member was released
    administratively up, and the forced preview still holds the child with its member joined and its withdrawal pending."""

    CONV = "vpc305"
    MEMBERS = ("Ethernet1/5", "Ethernet1/6")

    def __init__(self, npairs=2):
        super(ConvPairCtrl, self).__init__(npairs)
        self.conv_seeded, self.conv_done = False, set()

    def seed_conventional(self):
        self.conv_seeded = True
        self.marked_source = self.CONV
        try:
            for pair in self.pairs:
                for serial, member in zip(pair, self.MEMBERS):
                    nv = V.trunk_host_nv(member)
                    nv["ADMIN_STATE"] = "true"
                    self.nodes[serial][member] = {"policy": V.TRUNK, "nvPairs": nv}
                    self.summary_extra[serial].append(self._marked_deleted_entry(serial, "port-channel305"))
                    self.policies_extra[serial].append({
                        "entityName": "port-channel305", "entityType": "INTERFACE", "templateName": "interface_delete", "source": self.CONV,
                        "deleted": True, "policyId": V.pid(serial, "port-channel305") + "-del", "serialNumber": serial})
        finally:
            self.marked_source = None

    def _preview_for(self, serial):
        resp = super(ConvPairCtrl, self)._preview_for(serial)
        pair = self.psn(self.pair_of(serial))
        if self.conv_seeded and (pair, self.CONV) not in self.conv_done:
            member = self.MEMBERS[self.pair_of(serial).index(serial)]
            entry = resp["DATA"][0]
            entry["pendingConfig"] = list(entry["pendingConfig"]) + vpc_conv_pending(member)
            entry["runningConfig"] = list(entry["runningConfig"]) + conv_vpc_running(member)
            entry["status"] = "Out-of-Sync"
        return resp

    def _deploy_completed(self, data):
        super(ConvPairCtrl, self)._deploy_completed(data)
        for item in json.loads(data):
            if str(item["ifName"]).lower() == self.CONV:
                self.conv_done.add((item["serialNumber"], self.CONV))


def conv_items(ctrl, deploys):
    return [{"name": ConvPairCtrl.CONV, "type": "vpc", "switch": [B.IPS[s] for s in B.PAIRS[i]], "deploy": deploys[i]} for i in range(2)]


def saved_conventional_pairs():
    ctrl = ConvPairCtrl(2)
    config = [ctrl.add_vpc(10, i) for i in range(2)]
    assert B.run(ctrl, config)[0] == "exit"
    ctrl.next_invocation()
    ctrl.calls = []
    ctrl.children_marked_deleted = True
    status, result = B.run(ctrl, [dict(ctrl.del_item(10, i), deploy=False) for i in range(2)], state="deleted")
    assert status == "exit" and ctrl.deploys() == [], result.get("msg")
    ctrl.seed_conventional()
    ctrl.next_invocation()
    ctrl.calls = []
    return ctrl


def test_a_saved_conventional_vpc_of_the_same_name_on_two_pairs_is_completed_with_each_pairs_pvlan_vpc():
    ctrl = saved_conventional_pairs()
    items = [dict(ctrl.del_item(10, i), deploy=True) for i in range(2)] + conv_items(ctrl, (True, True))
    status, result = B.run(ctrl, items, state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert deployed(ctrl) == sorted([sent(PA), sent(PB), sent(PA, "vPC305"), sent(PB, "vPC305")])
    saved = sorted((r.get("kind", "vpc"), r["serial"], r.get("name") or r["vpc"], r["state"]) for r in result["pvlan_saved"])
    assert saved == sorted([("vpc", PA, "vPC10", SAVED), ("vpc", PB, "vPC10", SAVED), ("conventional", PA, "vPC305", SAVED),
                            ("conventional", PB, "vPC305", SAVED)]), saved
    assert marked(ctrl) == dict((s, []) for s in ALL) and policies_marked(ctrl) == dict((s, []) for s in ALL)
    assert ctrl.conv_done == {(PA, "vpc305"), (PB, "vpc305")}


def test_a_pair_whose_saved_conventional_vpc_is_not_requested_with_deployment_keeps_the_pvlan_deploy_of_that_pair_refused():
    ctrl = saved_conventional_pairs()
    items = [dict(ctrl.del_item(10, i), deploy=True) for i in range(2)] + conv_items(ctrl, (True, False))
    status, result = B.run(ctrl, items, state="deleted")
    assert status == "fail", result.get("msg")
    assert "vPC10 on %s: peer 1 (%s): pending exists for interfaces outside this deploy batch: ethernet1/5" % (PB, SN3) in result["msg"], result["msg"]
    assert "vPC10 on %s: peer" % PA not in result["msg"], "pair A's conventional vPC is owned by this request"
    assert deployed(ctrl) == [] and ctrl.deployed_vpcs == set() and ctrl.conv_done == set()
    assert len(marked(ctrl)[V.SN1]) == 2 and len(marked(ctrl)[SN3]) == 2, "nothing was completed on either pair"


# ============================================================ the released routed member of a border pair (installed template)
# Pair A releases int_trunk_host; both peers of pair B release int_routed_host with CDP_ENABLE "true" (MEASURED). The first measured routed
# body had no CDP key and is covered with the Po and vPC tests of test_pvlan_member_release_routed.
def member_modifies(ctrl, calls):
    """{(serial, ifName): (policy, nvPairs)} of the released-member modifies in `calls` (the vPC parent modify is left out)."""
    out = {}
    for method, path, data in calls:
        if method == "POST" and path.endswith(V.MODIFY):
            for payload in json.loads(data):
                for intf in payload["interfaces"]:
                    if intf["serialNumber"] in ctrl.nodes:
                        out[(intf["serialNumber"], intf["ifName"])] = (payload["policy"], intf["nvPairs"])
    return out


def test_a_border_pair_saved_deletion_releases_routed_members_corrected_and_pending():
    """FAIL-BEFORE: the module refuses pair B after both mark-deletes with CDP_ENABLE='true' is outside the released routed form."""
    ctrl = saved_pairs(ctrl=border_pair())
    written = member_modifies(ctrl, ctrl.saved_calls)
    assert sorted(written) == [(V.SN1, "Ethernet1/10"), (V.SN2, "Ethernet2/10"), (SN3, "Ethernet1/10"), (SN4, "Ethernet2/10")]
    for key, (policy, nv) in written.items():
        assert nv["ADMIN_STATE"] == "false"
        if key in BORDER_B:
            assert policy == R.ROUTED and nv["CDP_ENABLE"] == "true", "the controller value is carried"
            assert ctrl.nodes[key[0]][key[1]]["policy"] == R.ROUTED
        else:
            assert policy == V.TRUNK
    released = dict(((r["serial"], r["member"]), r["released_policy"]) for r in ctrl.saved_result["pvlan_vpc_release"])
    assert released == dict((key, written[key][0]) for key in written), "each member keeps ITS released policy"
    assert ctrl.deploys() == [] and ctrl.saved_result["changed"] is True
    assert sorted((r["serial"], r["state"].split(":")[0]) for r in ctrl.saved_result["pvlan_saved"]) == [(PA, "saved"), (PB, "saved")]


@pytest.mark.parametrize("route", ROUTES)
def test_a_border_pair_is_continued_with_the_trunk_pair_and_both_are_deployed_once(route):
    ctrl = saved_pairs(ctrl=border_pair())
    status, result = resume(ctrl, route, (True, True))
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert deployed(ctrl) == [sent(PA), sent(PB)]
    assert [w for w in vpc_writes(ctrl) if w[1] != "globalInterface/deploy"] == [], "no member is written again"
    assert reports(result) == [(PA, "vPC10", SAVED, members(0)), (PB, "vPC10", SAVED, members(1))]
    judged(result, (0, 1))
    assert ctrl.deployed_vpcs == {(PA, "vPC10"), (PB, "vPC10")} and marked(ctrl) == dict((s, []) for s in ALL)
    for serial, port in BORDER_B:
        assert ctrl.nodes[serial][port]["policy"] == R.ROUTED and ctrl.nodes[serial][port]["nvPairs"]["CDP_ENABLE"] == "true"
    ctrl.next_invocation()
    ctrl.calls = []
    status, result = resume(ctrl, route, (True, True))
    assert status == "exit", result.get("msg")
    if route == "named":
        assert result["changed"] is False
    nothing_written(ctrl)


@pytest.mark.parametrize("deploys", [(True, False), (False, True)])
def test_a_border_pair_keeps_its_own_deploy_choice(deploys):
    ctrl = saved_pairs(ctrl=border_pair())
    status, result = resume(ctrl, "named", deploys)
    assert status == "exit", result.get("msg")
    done, kept = (0, 1) if deploys[0] else (1, 0)
    pairs = (PA, PB)
    assert deployed(ctrl) == [sent(pairs[done])]
    assert reports(result) == sorted([(pairs[done], "vPC10", SAVED, members(done)), (pairs[kept], "vPC10", AWAITING, members(kept))])
    for serial in B.PAIRS[kept]:
        assert len(marked(ctrl)[serial]) == 1 and len(policies_marked(ctrl)[serial]) == 1


def test_a_border_pair_with_both_deploy_false_stays_saved_and_is_reported_for_both_pairs():
    ctrl = saved_pairs(ctrl=border_pair())
    status, result = resume(ctrl, "named", (False, False))
    assert status == "exit", result.get("msg")
    nothing_written(ctrl)
    assert reports(result) == [(PA, "vPC10", AWAITING, members(0)), (PB, "vPC10", AWAITING, members(1))]


def test_a_border_pair_saved_with_deploy_true_is_deployed_in_one_run():
    """The deployed deletion (no saved stage) of the same two pairs."""
    ctrl = border_pair()
    config = [ctrl.add_vpc(10, i) for i in range(2)]
    assert B.run(ctrl, config)[0] == "exit"
    ctrl.next_invocation()
    ctrl.calls = []
    status, result = B.run(ctrl, [ctrl.del_item(10, 0), ctrl.del_item(10, 1)], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert sorted((d["serialNumber"], d["ifName"]) for call in ctrl.deploys() for d in json.loads(call[2])) == [(PA, "vPC10"), (PB, "vPC10")]
    judged(result, (0, 1))
    written = member_modifies(ctrl, ctrl.calls)
    assert all(written[key][0] == R.ROUTED and written[key][1]["CDP_ENABLE"] == "true" for key in BORDER_B)


@pytest.mark.parametrize("value", ["false", ""])
def test_a_non_default_cdp_on_the_border_pair_is_refused_naming_that_pair_and_writing_no_member_there(value):
    ctrl = border_pair(routed_nv=dict(R.RELEASED_ROUTED_CDP, CDP_ENABLE=value))
    config = [ctrl.add_vpc(10, i) for i in range(2)]
    assert B.run(ctrl, config)[0] == "exit"
    ctrl.next_invocation()
    ctrl.calls = []
    items = [dict(ctrl.del_item(10, i), deploy=False) for i in range(2)]
    status, result = B.run(ctrl, items, state="deleted")
    assert status == "fail" and PB in result["msg"] and "CDP_ENABLE=" in result["msg"], result.get("msg")
    assert ctrl.deploys() == []
    assert not [key for key in member_modifies(ctrl, ctrl.calls) if key in BORDER_B], "no member write on the refused pair"
