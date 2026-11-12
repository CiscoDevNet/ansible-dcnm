"""Per-peer description updates and clears of an existing PVLAN vPC."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .helpers.ethernet_controller import preview
from .helpers.vpc_controller import IP1
from .helpers.vpc_controller import IP2
from .helpers.vpc_controller import M1
from .helpers.vpc_controller import M2
from .helpers.vpc_controller import PAIR
from .helpers.vpc_controller import SN1
from .helpers.vpc_controller import SN2
from .helpers.vpc_controller import VPC
from .helpers.vpc_controller import VPC_HOST
from .helpers.vpc_controller import converged_preview
from .helpers.vpc_controller import created_ctrl
from .helpers.vpc_controller import description_preview
from .helpers.vpc_controller import member_after
from .helpers.vpc_controller import po_stanza
from .helpers.vpc_controller import run_vpc
from .helpers.vpc_controller import vpc_item
from .helpers import membership as MM
from .helpers import vpc_controller as V


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_vpc_a1_description.py
# A1: the description of ONE vPC peer may change alone (existing vPC, int_vpc_pvlan_host). Real main() through the EXISTING vPC harness
# (VpcController: two peers, per-serial previews). Fixtures are SYNTHETIC (template-shaped); NOT LIVE TESTED.
#
# What is asserted (not only changed=true): the OUTBOUND parent request (the exact nvPairs of the one interface/modify), the per-peer gate
# records (site + peer + serial + decision, never a count over the whole list), the order of the calls, the untouched peer's intended value
# and its convergence. Gate records of an update: two `prior` records (converged) and two `deploy` records; the touched peer `deploy`, the
# untouched one `converged`.
# ====================================================================================================
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
    """A1 limit: the combination was composed offline in a throwaway copy with a hand-built fixture (an out-of-tree probe) but no real pending
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


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_vpc_a1_description_clear.py
# A1-CLEAR: an explicit empty peerN_description clears the description of THAT vPC peer (merged), through the real input validator and the
# real main(), on the EXISTING vPC harness (VpcController: two peers, per-serial previews). Fixtures are SYNTHETIC (template-shaped): the
# removal pending `no description <old>` is the harness' own removal_preview, NOT measured live. NOT LIVE TESTED.
#
# Contract under test:
#   * peerN_description: ""      -> clears that peer's PEERn_PO_DESC; the other peer, every member list and every other nvPair are carried;
#   * peerN_description omitted  -> kept (merged); a repeat of an already-empty clear is a zero-write no-op;
#   * copy_description true      -> a one-peer description change (a clear included) is still refused before any write;
#   * any other value            -> still a single-line string of at most 254 characters: LF and CR refused, longer refused, non-str refused.
# Asserted on the outbound parent request, the per-peer gate records, the call order and the request log (writes), not only changed.
# ====================================================================================================
VPC_DESC_CLEAR_SERIAL = {1: SN1, 2: SN2}
VPC_DESC_CLEAR_PORT = {SN1: M1, SN2: M2}


def clear_queue(ctrl, touched, old, other_desc):
    other = SN2 if touched == SN1 else SN1
    ctrl.vpc_previews[touched] = [converged_preview(touched, VPC_DESC_CLEAR_PORT[touched], desc=old),
                                  removal_preview(touched, VPC_DESC_CLEAR_PORT[touched], old)]
    ctrl.vpc_previews[other] = [converged_preview(other, VPC_DESC_CLEAR_PORT[other], desc=other_desc),
                                converged_preview(other, VPC_DESC_CLEAR_PORT[other], desc=other_desc)]
    return other


def vpc_desc_clear_assert_one_peer_update(ctrl, result, touched):
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
    touched = VPC_DESC_CLEAR_SERIAL[peer]
    clear_queue(ctrl, touched, "old-a" if peer == 1 else "old-b", "old-b" if peer == 1 else "old-a")
    status, result = run_vpc(ctrl, [vpc_item(**{"peer%d_description" % peer: ""})], state="merged")
    assert status == "exit", result.get("msg")
    vpc_desc_clear_assert_one_peer_update(ctrl, result, touched)
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
    touched, other_desc = VPC_DESC_CLEAR_SERIAL[peer], ("keep-b" if peer == 1 else "keep-a")
    other = SN2 if touched == SN1 else SN1
    ctrl.vpc_previews[touched] = [converged_preview(touched, VPC_DESC_CLEAR_PORT[touched]),
                                  description_preview(touched, VPC_DESC_CLEAR_PORT[touched], None, "a1-peer%d" % peer)]
    ctrl.vpc_previews[other] = [converged_preview(other, VPC_DESC_CLEAR_PORT[other], desc=other_desc)] * 2
    status, result = run_vpc(ctrl, [vpc_item(**{"peer%d_description" % peer: "a1-peer%d" % peer})], state="merged")
    assert status == "exit", result.get("msg")
    assert ctrl.parents[VPC]["nvPairs"]["PEER%d_PO_DESC" % peer] == "a1-peer%d" % peer
    ctrl.next_invocation()
    ctrl.calls = []
    clear_queue(ctrl, touched, "a1-peer%d" % peer, other_desc)
    status, result = run_vpc(ctrl, [vpc_item(**{"peer%d_description" % peer: ""})], state="merged")
    assert status == "exit", result.get("msg")
    vpc_desc_clear_assert_one_peer_update(ctrl, result, touched)
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


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_vpc_postr2_a1_compat.py
# A1 (the description of ONE vPC peer changes alone) next to what was published after it: speed/duplex, multi-member and input parity.
#
# A1 was written on N06. The published base now also carries the duplex rule and the early refusal of a combined speed + duplex change (R1), the
# multi-member vPC support, the bpdu_guard/speed input parity, and the registry work. These cases prove that they coexist: a description-only change of
# one peer still reaches exactly that peer while the shared values already stored (speed, duplex, bpdu_guard, every member) are carried unchanged, and a
# real shared change next to it is judged by the rule that owns it. They reuse the A1, vPC and multi-member harnesses; nothing here is a new framework.
#
# Synthetic fixtures, controller mocked at its boundary. NOT LIVE TESTED.
# ====================================================================================================
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
    out = reconcile({"peer%d_description" % peer: "x"}, have)
    assert out["update"] is True and out["ask_legs"] == [peer - 1] and not out["blocked"], out["blocked"]
    assert sorted(out["changed"]) == ["PEER%d_PO_DESC" % peer]
    assert out["nv"]["SPEED"] == "1Gb" and out["nv"]["PORT_DUPLEX_MODE"] == "full"


def test_postr2a1_restating_the_stored_speed_and_duplex_is_not_a_second_change():
    have = _have(SPEED="1Gb", PORT_DUPLEX_MODE="full")
    out = reconcile({"peer1_description": "x", "speed": "1gb", "duplex": "full"}, have)
    assert out["update"] is True and out["ask_legs"] == [0] and not out["blocked"], out["blocked"]
    assert sorted(out["changed"]) == ["PEER1_PO_DESC"]


def test_postr2a1_a_combined_speed_and_duplex_change_next_to_a_description_is_refused_by_its_own_rule():
    have = _have()  # Auto / auto
    out = reconcile({"peer1_description": "x", "speed": "1Gb", "duplex": "full"}, have)
    assert out["update"] is False and any(COMBINED in b for b in out["blocked"]), out["blocked"]


def test_postr2a1_a_duplex_change_alone_next_to_a_description_reaches_both_peers_not_just_one():
    have = _have(SPEED="1Gb")
    out = reconcile({"peer1_description": "x", "duplex": "full"}, have)
    assert out["update"] is True and out["ask_legs"] == [0, 1] and not out["blocked"], "a shared field reaches both peers: A1 does not apply"


def test_postr2a1_description_alone_does_not_hide_the_duplex_needs_a_fixed_speed_rule():
    out = reconcile({"peer1_description": "x", "duplex": "full"}, _have())  # speed stays Auto
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
    out = reconcile({"peer1_members": respelled, "peer2_members": MM.PORTS[V.SN2], "peer1_description": "x"}, have)
    assert out["update"] is True and out["ask_legs"] == [0] and not out["blocked"], out["blocked"]
    assert sorted(out["changed"]) == ["PEER1_PO_DESC"], "the same ports in another spelling and order are not a membership change"


def test_postr2a1_helper_description_with_a_member_change_of_the_same_peer_stays_refused_with_two_members():
    have = _have(PEER1_MEMBER_INTERFACES=",".join(MM.PORTS[V.SN1]), PEER2_MEMBER_INTERFACES=",".join(MM.PORTS[V.SN2]))
    joined = MM.PORTS[V.SN1] + ["Ethernet1/20"]
    out = reconcile({"peer1_members": joined, "peer2_members": MM.PORTS[V.SN2], "peer1_description": "x"}, have)
    assert out["update"] is False and any("changes only peer 1" in b for b in out["blocked"]), out["blocked"]
    # replaced states the complete membership: dropping a member next to the description is the same refused combination
    dropped = reconcile({"peer1_members": MM.PORTS[V.SN1][:1], "peer2_members": MM.PORTS[V.SN2], "peer1_description": "x"}, have, state="replaced")
    assert dropped["update"] is False and any("changes only peer 1" in b for b in dropped["blocked"]), dropped["blocked"]


def test_postr2a1_helper_merged_never_drops_a_member_so_a_subset_next_to_a_description_is_description_only():
    have = _have(PEER1_MEMBER_INTERFACES=",".join(MM.PORTS[V.SN1]), PEER2_MEMBER_INTERFACES=",".join(MM.PORTS[V.SN2]))
    out = reconcile({"peer1_members": MM.PORTS[V.SN1][:1], "peer2_members": MM.PORTS[V.SN2], "peer1_description": "x"}, have)
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
