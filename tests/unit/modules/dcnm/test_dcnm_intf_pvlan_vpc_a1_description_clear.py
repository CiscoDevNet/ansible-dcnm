"""A1-CLEAR: an explicit empty peerN_description clears the description of THAT vPC peer (merged), through the real input validator and the
real main(), on the EXISTING vPC harness (VpcController: two peers, per-serial previews). Fixtures are SYNTHETIC (template-shaped): the
removal pending `no description <old>` is the harness' own removal_preview, NOT measured live. NOT LIVE TESTED.

Contract under test:
  * peerN_description: ""      -> clears that peer's PEERn_PO_DESC; the other peer, every member list and every other nvPair are carried;
  * peerN_description omitted  -> kept (merged); a repeat of an already-empty clear is a zero-write no-op;
  * copy_description true      -> a one-peer description change (a clear included) is still refused before any write;
  * any other value            -> still a single-line string of at most 254 characters: LF and CR refused, longer refused, non-str refused.
Asserted on the outbound parent request, the per-peer gate records, the call order and the request log (writes), not only changed."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .test_dcnm_intf_pvlan_harness import preview
from .test_dcnm_intf_pvlan_vpc_harness import (
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


def removal_preview(serial, port, old):
    pending = ["interface port-channel10", "  no description %s" % old]
    return preview(pending, serial=serial, running=po_stanza(desc=old) + member_after(port), expected=po_stanza() + member_after(port))


def clear_queue(ctrl, touched, old, other_desc):
    other = SN2 if touched == SN1 else SN1
    ctrl.vpc_previews[touched] = [converged_preview(touched, PORT[touched], desc=old), removal_preview(touched, PORT[touched], old)]
    ctrl.vpc_previews[other] = [converged_preview(other, PORT[other], desc=other_desc), converged_preview(other, PORT[other], desc=other_desc)]
    return other


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
    assert ctrl.order() == ["PREVIEW", "PREVIEW", "MODIFY", "PREVIEW", "PREVIEW", "DEPLOY"]
    assert len(ctrl.modifies()) == 1 and len(ctrl.deploys()) == 1 and ctrl.creates() == []


@pytest.mark.parametrize("peer", [1, 2])
def test_a1_clear_explicit_empty_clears_only_that_peer(peer):
    ctrl = created_ctrl(descs=("old-a", "old-b"))
    before = dict(ctrl.parents[VPC]["nvPairs"])
    touched = SERIAL[peer]
    clear_queue(ctrl, touched, "old-a" if peer == 1 else "old-b", "old-b" if peer == 1 else "old-a")
    status, result = run_vpc(ctrl, [vpc_item(**{"peer%d_description" % peer: ""})], state="merged")
    assert status == "exit", result.get("msg")
    assert_one_peer_update(ctrl, result, touched)
    sent = outbound(ctrl)
    assert sent["PEER%d_PO_DESC" % peer] == ""
    assert sent["PEER%d_PO_DESC" % (3 - peer)] == ("old-b" if peer == 1 else "old-a"), "the other peer keeps its description"
    for key in ("PEER1_MEMBER_INTERFACES", "PEER2_MEMBER_INTERFACES", "PEER1_PCID", "PEER2_PCID", "COPY_DESC", "ADMIN_STATE", "ASSOCIATION_LIST"):
        assert sent[key] == before[key], key
    changed_keys = sorted(k for k in sent if before.get(k, "") != sent[k] and k not in ("POLICY_ID",))
    assert changed_keys == ["PEER%d_PO_DESC" % peer], changed_keys
    assert ctrl.parents[VPC]["nvPairs"]["PEER%d_PO_DESC" % peer] == ""


@pytest.mark.parametrize("peer", [1, 2])
def test_a1_clear_set_then_clear_the_same_peer_in_two_invocations(peer):
    ctrl = created_ctrl(descs=("", "keep-b") if peer == 1 else ("keep-a", ""))
    touched, other_desc = SERIAL[peer], ("keep-b" if peer == 1 else "keep-a")
    other = SN2 if touched == SN1 else SN1
    ctrl.vpc_previews[touched] = [converged_preview(touched, PORT[touched]), description_preview(touched, PORT[touched], None, "a1-peer%d" % peer)]
    ctrl.vpc_previews[other] = [converged_preview(other, PORT[other], desc=other_desc)] * 2
    status, result = run_vpc(ctrl, [vpc_item(**{"peer%d_description" % peer: "a1-peer%d" % peer})], state="merged")
    assert status == "exit", result.get("msg")
    assert ctrl.parents[VPC]["nvPairs"]["PEER%d_PO_DESC" % peer] == "a1-peer%d" % peer
    ctrl.next_invocation()
    ctrl.calls = []
    clear_queue(ctrl, touched, "a1-peer%d" % peer, other_desc)
    status, result = run_vpc(ctrl, [vpc_item(**{"peer%d_description" % peer: ""})], state="merged")
    assert status == "exit", result.get("msg")
    assert_one_peer_update(ctrl, result, touched)
    sent = outbound(ctrl)
    assert sent["PEER%d_PO_DESC" % peer] == "" and sent["PEER%d_PO_DESC" % (3 - peer)] == other_desc


def test_a1_clear_repeat_of_an_already_empty_description_is_a_zero_write_noop():
    ctrl = created_ctrl(descs=("", "keep-b"))
    ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1)]
    ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2, desc="keep-b")]
    status, result = run_vpc(ctrl, [vpc_item(peer1_description="")], state="merged")
    assert status == "exit", result.get("msg")
    assert result["changed"] is False and ctrl.writes() == [] and ctrl.modifies() == [] and ctrl.deploys() == []


def test_a1_clear_omission_still_preserves_both_descriptions():
    ctrl = created_ctrl(descs=("keep-a", "keep-b"))
    ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1, desc="keep-a")]
    ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2, desc="keep-b")]
    status, result = run_vpc(ctrl, [vpc_item()], state="merged")
    assert status == "exit", result.get("msg")
    assert result["changed"] is False and ctrl.writes() == []
    assert ctrl.parents[VPC]["nvPairs"]["PEER1_PO_DESC"] == "keep-a" and ctrl.parents[VPC]["nvPairs"]["PEER2_PO_DESC"] == "keep-b"


def test_a1_clear_with_copy_description_true_is_refused_before_any_write():
    ctrl = created_ctrl(descs=("old-a", ""))
    ctrl.parents[VPC]["nvPairs"]["COPY_DESC"] = "true"
    ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1, desc="old-a")]
    ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2)]
    status, result = run_vpc(ctrl, [vpc_item(peer1_description="")], state="merged")
    assert status == "fail" and "copy_description is true" in result["msg"] and "peer 1" in result["msg"], result.get("msg")
    assert ctrl.writes() == [] and ctrl.modifies() == [] and ctrl.deploys() == []


@pytest.mark.parametrize(
    "value, needle",
    [("a\nb", "peer1_description must be a single-line"), ("a\rb", "peer1_description must be a single-line"),
     ("x" * 255, "peer1_description must be a single-line"), (["a"], "peer1_description")],
    ids=["LF", "CR", "255-chars", "list"],
)
def test_a1_clear_other_values_keep_the_single_line_length_and_type_rules(value, needle):
    ctrl = created_ctrl(descs=("old-a", ""))
    status, result = run_vpc(ctrl, [vpc_item(peer1_description=value)], state="merged")
    assert status == "fail" and needle in result["msg"], result.get("msg")
    assert ctrl.writes() == [] and ctrl.modifies() == [] and ctrl.deploys() == []


@pytest.mark.parametrize("value", ["", "x", "x" * 254, " site 1 "], ids=["empty", "one", "254-chars", "spaces"])
def test_a1_clear_validator_accepts_empty_and_single_line_values_up_to_254(value):
    raw = {"mode": "pvlan", "pvlan_mode": "host", "pvlan_association": [{"primary_vlan": 2210, "secondary_vlan": 2212}],
           "peer1_members": [M1], "peer2_members": [M2], "peer1_pcid": 10, "peer2_pcid": 10, "peer1_description": value}
    assert not [r for r in P.vpc_not_implemented(raw, VPC) if "description" in r]
