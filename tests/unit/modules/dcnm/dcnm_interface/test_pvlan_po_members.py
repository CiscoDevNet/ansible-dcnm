"""Membership of PVLAN port-channels and vPCs: updates, several members and conflicts."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from .helpers import port_channel_controller as H
from .helpers import vpc_controller as V
from .helpers import port_channel_release as RR
from .helpers.membership import E10
from .helpers.membership import E7
from .helpers.membership import E9
from .helpers.membership import E9P
from .helpers.membership import MembershipPo
from .helpers.membership import PAIR
from .helpers.membership import ROUTED
from .helpers.membership import fragments
from .helpers.membership import item
from .helpers.membership import member_nv
from .helpers.membership import queue_peer
from .helpers.membership import run
from .helpers.membership import seeded
from .helpers.membership import strip_vpc
from .helpers.membership import vpc_seeded
from .helpers.port_channel_controller import PoLifecycleController
from .helpers.membership import PORTS
from .helpers.membership import combine_previews
from .helpers.membership import queue
from .helpers.membership import seeded_vpc
from .helpers.membership import vpc_baseline
from .helpers.membership import vpc_item
from .helpers.ethernet_controller import IF7
from .helpers.ethernet_controller import IF8
from .helpers.ethernet_controller import SWITCH_IP
from .helpers.ethernet_controller import TRUNK
from .helpers.ethernet_controller import trunk_host_nv
from .helpers.ethernet_controller import run as po_conflicts_run
from .helpers.port_channel_controller import _eth
from .helpers.port_channel_controller import baseline_ctrl
from .helpers.port_channel_controller import created_ctrl
from .helpers.port_channel_controller import good_preview
from .helpers.port_channel_controller import po_item


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_member_updates.py
# Membership of an EXISTING PVLAN port-channel / vPC: add and remove members under the regular rule.
#
# Regular port-channel rule (dcnm_intf_compare_elements / dcnm_intf_merge_want_and_have): `merged` is the union of HAVE and the
# requested members (an omitted `members` keeps HAVE); `replaced` states the exact membership. PVLAN keeps one deliberate difference,
# documented: an omitted or empty list in `replaced` (which the regular module sends as an empty MEMBER_INTERFACES) is refused,
# because an empty member list is not implemented.
#
# SIMULATED, NOT MEASURED: the controller effect of a membership modify (an added port becomes int_port_channel_pvlan_member of the
# port-channel; a removed port is released as int_trunk_host -- or int_routed_host, the MEASURED form -- with ADMIN_STATE "true", like
# a deleted port-channel's member) and the per-member preview fragments (added: the MEASURED creation form `channel-group N force`;
# removed: the deletion form `no channel-group N force` with the release; existing: converged). Real main(); only the controller
# boundary is intercepted (existing Po/vPC harnesses, subclassed here).
# ====================================================================================================
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
    # An up member is released to the fabric default; an unknown administrative state stays refused
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
    # Deploy false SAVES the removal -- the parent's modify, the removed member released administratively
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
    # A one-peer description is supported now; the freeform of one peer is the still-refused example
    status, result = V.run_vpc(ctrl, [V.vpc_item(peer1_cmds=["logging event port link-status"])])
    assert status == "fail" and "changes only peer 1" in result["msg"] and ctrl.writes() == [], result.get("msg")


def test_vpc_removing_a_member_whose_admin_state_is_unknown_is_refused_before_any_write():
    # An up member is released to the fabric default (test_pvlan_member_admin.py); unknown stays refused
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


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_multimember.py
# Multiple physical PVLAN members: reuse existing transport harness and stanzas.
#
# Offline module regressions, not new live-controller measurements. Membership
# cardinality is varied; unrelated nvPair matrices deliberately are not repeated.
# ====================================================================================================
@pytest.mark.parametrize("reverse", [False, True])
def test_vpc_create_full_lists_on_correct_peers_then_repeat_with_reordered_aliases(reverse):
    ctrl = vpc_baseline()
    queue(ctrl, V.create_preview)
    item = vpc_item()
    if reverse:
        item["switch"].reverse()
        item["profile"]["peer1_members"], item["profile"]["peer2_members"] = PORTS[V.SN2], PORTS[V.SN1]
    status, result = V.run_vpc(ctrl, [item])
    assert status == "exit", result.get("msg")
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1
    parent = ctrl.parents[V.VPC]["nvPairs"]
    assert parent["PEER1_MEMBER_INTERFACES"] == ",".join(PORTS[V.SN1])
    assert parent["PEER2_MEMBER_INTERFACES"] == ",".join(PORTS[V.SN2])
    assert len(ctrl.previews_asked()) == 2, "one fresh preview per switch, not per member"
    ctrl.next_invocation()
    ctrl.calls = []
    queue(ctrl, V.converged_preview)
    item = vpc_item()
    for peer in (1, 2):
        key = "peer%d_members" % peer
        item["profile"][key] = [p.replace("Ethernet", "e") for p in reversed(item["profile"][key])]
    status, result = V.run_vpc(ctrl, [item])
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.writes() == []


def test_vpc_description_update_preserves_every_omitted_member():
    ctrl = seeded_vpc()
    queue(ctrl, V.converged_preview)
    queue(ctrl, V.description_preview, "", "multiple")
    item = vpc_item(peer1_description="multiple", peer2_description="multiple")
    del item["profile"]["peer1_members"], item["profile"]["peer2_members"]
    status, result = V.run_vpc(ctrl, [item])
    assert status == "exit", result.get("msg")
    assert len(ctrl.modifies()) == 1 and len(ctrl.deploys()) == 1
    for n, serial in enumerate((V.SN1, V.SN2), 1):
        assert ctrl.parents[V.VPC]["nvPairs"]["PEER%d_MEMBER_INTERFACES" % n] == ",".join(PORTS[serial])


@pytest.mark.parametrize("serial, port", [(V.SN1, PORTS[V.SN1][-1]), (V.SN2, PORTS[V.SN2][-1])])
def test_vpc_rejects_foreign_last_member_before_any_write(serial, port):
    ctrl = vpc_baseline()
    ctrl.nodes[serial][port]["policy"] = V.PO_MEMBER
    ctrl.nodes[serial][port]["nvPairs"]["PO_ID"] = "port-channel99"
    status, result = V.run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")
    assert port.lower() in result["msg"].lower()


def test_vpc_bad_middle_member_preview_prevents_deploy():
    ctrl = vpc_baseline()
    queue(ctrl, V.create_preview)
    entry = P.preview_entry(ctrl.vpc_previews[V.SN1][0], V.SN1)
    # Remove an entire required member from expectedConfig, retaining good last port.
    blocks = P.split_blocks(entry["expectedConfig"])[0]
    expected = []
    for name, lines in blocks.items():
        if name != PORTS[V.SN1][1].lower():
            expected += ["interface " + name] + lines
    ctrl.vpc_previews[V.SN1][0] = V.preview(entry["pendingConfig"], serial=V.SN1,
                                            running=entry["runningConfig"], expected=expected)
    status, result = V.run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and len(ctrl.creates()) == 1 and ctrl.deploys() == [], result.get("msg")


def test_vpc_readback_does_not_overwrite_a_wrong_middle_member_with_the_good_last_member():
    class WrongReadback(V.VpcController):
        def __call__(self, mod, method, path, data=None):
            result = super().__call__(mod, method, path, data)
            if method == "POST" and path.endswith(V.DEPLOY):
                self.nodes[V.SN1][PORTS[V.SN1][1]]["nvPairs"]["LACP_PORT_PRIO"] = "99"
            return result
    ctrl = vpc_baseline()
    ctrl.__class__ = WrongReadback
    queue(ctrl, V.create_preview)
    status, result = V.run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and len(ctrl.deploys()) == 1, result.get("msg")
    assert "LACP_PORT_PRIO" in result["msg"], result.get("msg")


def test_vpc_delete_releases_and_verifies_all_five_members():
    ctrl = seeded_vpc()
    queue(ctrl, V.delete_preview)
    status, result = V.run_vpc(ctrl, [V.vpc_del_item()], state="deleted")
    assert status == "exit", result.get("msg")
    assert len(ctrl.markdeletes()) == 1 and len(ctrl.modifies()) == 5 and len(ctrl.deploys()) == 1
    identities = {(i["serialNumber"], i["ifName"]) for c in ctrl.modifies() for p in json.loads(c[2]) for i in p["interfaces"]}
    assert identities == {(s, p) for s, ports in PORTS.items() for p in ports}
    for serial, port in identities:
        assert ctrl.nodes[serial][port]["nvPairs"]["ADMIN_STATE"] == "false"
    verified = result["pvlan_verification"][V.VPC]
    assert verified["state"] == "verified" and len(verified["peers"]) == 5


def test_vpc_invalid_last_release_blocks_all_member_writes():
    class InvalidRelease(V.VpcController):
        def __call__(self, mod, method, path, data=None):
            result = super().__call__(mod, method, path, data)
            if method == "DELETE" and path.endswith(V.MARKDELETE):
                nv = self.nodes[V.SN2][PORTS[V.SN2][-1]]["nvPairs"]
                nv.update(ADMIN_STATE="false", ALLOWED_VLANS="all")
            return result
    ctrl = seeded_vpc()
    ctrl.__class__ = InvalidRelease
    status, result = V.run_vpc(ctrl, [V.vpc_del_item()], state="deleted")
    assert status == "fail" and len(ctrl.markdeletes()) == 1, result.get("msg")
    assert ctrl.modifies() == [] and ctrl.deploys() == []


@pytest.mark.parametrize("members", [["Ethernet1/7", "e1/7"], ["Ethernet1/7", "Ethernet1/8-10"], ["Ethernet1/7", 9]])
def test_member_validation_refuses_alias_duplicates_ranges_and_non_strings(members):
    assert P.po_not_implemented(H.po_item(members=members)["profile"])
    assert P.vpc_not_implemented(V.vpc_item(peer1_members=members)["profile"], V.VPC)


def po_seeded():
    ctrl = PoLifecycleController()
    # Parent fixture from the existing contract; explicit members with independent descriptors.
    nv = P.po_host_nvpairs(H.po_item(members=PORTS[V.SN1])["profile"], H.PO)
    ctrl.detail[H.PO] = {"policy": H.PO_HOST, "nvPairs": nv}
    ctrl.po_names.add(H.PO)
    for port in PORTS[V.SN1]:
        ctrl.detail[port] = {"policy": H.PO_MEMBER, "nvPairs": {
            "PO_ID": H.PO, "PC_MODE": "active", "PVLAN_MODE": "host", "CDP_ENABLE": "true",
            "lldpTransmit": "false", "lldpReceive": "false", "LACP_PORT_PRIO": "32768", "LACP_RATE": "normal",
            "DESC": "", "CONF": "", "ADMIN_STATE": "false", "INTF_NAME": port}}
    return ctrl


def test_regular_po_create_sends_all_members():
    ctrl = H.PoController()
    for port in PORTS[V.SN1]:
        ctrl.detail[port] = {"policy": H.TRUNK, "nvPairs": H.trunk_host_nv(port)}
    status, result = H.run(ctrl, [H.po_item(members=PORTS[V.SN1], deploy=False)])
    assert status == "exit", result.get("msg")
    assert ctrl.detail[H.PO]["nvPairs"]["MEMBER_INTERFACES"] == ",".join(PORTS[V.SN1])
    assert len(ctrl.creates()) == 1


def test_regular_po_repeat_keeps_controller_representation_of_all_members():
    ctrl = po_seeded()
    before = copy.deepcopy(ctrl.detail[H.PO]["nvPairs"])
    status, result = H.run(ctrl, [H.po_item(members=list(reversed(PORTS[V.SN1])), deploy=False)])
    assert status == "exit" and result["changed"] is False and ctrl.writes() == [], result.get("msg")
    assert ctrl.detail[H.PO]["nvPairs"] == before


def test_regular_po_delete_restores_every_member():
    ctrl = po_seeded()
    pv = P.preview_entry(combine_previews(H.SERIAL, PORTS[V.SN1], V.delete_preview), H.SERIAL)
    pv["runningConfig"] = [line for line in pv["runningConfig"] if line.strip() != "vpc 10"]
    ctrl.previews = [H.preview(pv["pendingConfig"], running=pv["runningConfig"], expected=pv["expectedConfig"])]
    status, result = H.run(ctrl, [{"name": H.PO_ITEM_NAME, "switch": [H.SWITCH_IP], "deploy": True}], state="deleted")
    assert status == "exit", result.get("msg")
    assert len(ctrl.markdeletes()) == 1 and len(ctrl.deploys()) == 1
    assert {r["member"] for r in result["pvlan_po_release"]} == set(PORTS[V.SN1])
    assert all(ctrl.detail[p]["policy"] == H.TRUNK for p in PORTS[V.SN1])


def test_regular_po_unsafe_last_release_blocks_every_member_modify():
    class InvalidRelease(PoLifecycleController):
        def __call__(self, mod, method, path, data=None):
            result = super().__call__(mod, method, path, data)
            if method == "DELETE" and path.endswith(V.MARKDELETE):
                for port in PORTS[V.SN1]:
                    self.detail[port]["nvPairs"]["ADMIN_STATE"] = "true"
                self.detail[PORTS[V.SN1][-1]]["nvPairs"].update(ADMIN_STATE="false", ALLOWED_VLANS="all")
            return result
    ctrl = po_seeded()
    ctrl.__class__ = InvalidRelease
    status, result = H.run(ctrl, [{"name": H.PO_ITEM_NAME, "switch": [H.SWITCH_IP], "deploy": True}], state="deleted")
    assert status == "fail" and len(ctrl.markdeletes()) == 1, result.get("msg")
    assert ctrl.bulk_bodies() == [] and ctrl.deploys() == []


def test_regular_po_partial_release_reports_previous_member_write_and_stops():
    class FailedSecondWrite(PoLifecycleController):
        def __call__(self, mod, method, path, data=None):
            if method == "POST" and path.endswith(V.MODIFY):
                member = json.loads(data)[0]["interfaces"][0]["ifName"]
                if member == sorted(PORTS[V.SN1], key=str.lower)[1]:
                    self.modify_responses.append({"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [
                        {"reportItemType": "ERROR", "message": "injected second member failure", "entity": H.SERIAL + "~" + member}]})
            result = super().__call__(mod, method, path, data)
            if method == "DELETE" and path.endswith(V.MARKDELETE):
                for port in PORTS[V.SN1]:
                    self.detail[port]["nvPairs"]["ADMIN_STATE"] = "true"
            return result
    ctrl = po_seeded()
    ctrl.__class__ = FailedSecondWrite
    status, result = H.run(ctrl, [{"name": H.PO_ITEM_NAME, "switch": [H.SWITCH_IP], "deploy": True}], state="deleted")
    assert status == "fail" and ctrl.deploys() == [], result.get("msg")
    assert len(ctrl.bulk_bodies()) == 2
    first = sorted(PORTS[V.SN1], key=str.lower)[0]
    assert "modify of %s ADMIN_STATE false (per-item SUCCESS)" % first in result["msg"]
    assert ctrl.detail[first]["nvPairs"]["ADMIN_STATE"] == "false"


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_po_conflicts.py
# Membership conflicts INSIDE one invocation.
#
# NOT LIVE TESTED. Real main(); only the external boundary is mocked, through the port-channel test module (which reuses the
# existing Ethernet harness). Writes are those INTERCEPTED by the harness, not proof that NDFC accepts or rejects anything.
#
# Success of a rejection = zero configuration writes AND zero deploys. Two families, both config orders, merged and replaced:
#   A. a new PVLAN port-channel claims a member that the same invocation also manages directly as an interface;
#   B. a new PVLAN port-channel claims a member that another port-channel (non-PVLAN too) claims in the same invocation.
# ====================================================================================================
IF9 = "Ethernet1/9"
ORDERS = ("parent_first", "member_first")
STATES = ("merged", "replaced")


def ordered(order, parent, other):
    return [parent, other] if order == "parent_first" else [other, parent]


def direct_child(name=IF7, **extra):
    item = _eth(name)
    item["profile"]["description"] = "conflicting direct child"
    item["profile"].update(extra)
    return item


def trunk_po(name="po11", members=(IF7,), deploy=False):
    return {"name": name, "type": "pc", "switch": [SWITCH_IP], "deploy": deploy,
            "profile": {"mode": "trunk", "members": list(members), "allowed_vlans": "none"}}


def assert_refused(ctrl, status, result, needle):
    assert status == "fail", result
    assert needle in result["msg"], result["msg"]
    assert ctrl.writes() == [], "a refused invocation must write no configuration"
    assert ctrl.deploys() == [] and ctrl.creates() == []


# ------------------------------------------------------------------ family A: the member is also a direct entry
@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("order", ORDERS)
@pytest.mark.parametrize("deploy", [False, True])
def test_member_also_managed_directly_is_refused_in_any_order(order, state, deploy):
    ctrl = baseline_ctrl()
    ctrl.previews = [good_preview()]
    config = ordered(order, po_item(deploy=deploy), direct_child())
    status, result = po_conflicts_run(ctrl, config, state=state)
    assert_refused(ctrl, status, result, "also requested directly")


@pytest.mark.parametrize("mode", ["trunk", "access", "routed"])
def test_any_direct_profile_for_the_claimed_member_is_a_conflict(mode):
    ctrl = baseline_ctrl()
    status, result = po_conflicts_run(ctrl, [po_item(deploy=False), {"name": IF7, "type": "eth", "switch": [SWITCH_IP],
                                                                     "deploy": False, "profile": {"mode": mode}}])
    assert_refused(ctrl, status, result, "also requested directly")


@pytest.mark.parametrize("spelling", ["eth1/7", "e1/7", "ETHERNET1/7", "Ethernet 1/7"])
def test_direct_entry_spelling_is_normalised_like_the_existing_path(spelling):
    ctrl = baseline_ctrl()
    child = direct_child()
    child["name"] = spelling
    status, result = po_conflicts_run(ctrl, [po_item(deploy=False), child])
    assert_refused(ctrl, status, result, "also requested directly")


# ------------------------------------------------------------------ family B: a competing port-channel (PVLAN or not)
@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("order", ORDERS)
def test_member_claimed_by_a_non_pvlan_port_channel_is_refused_in_any_order(order, state):
    ctrl = baseline_ctrl()
    status, result = po_conflicts_run(ctrl, ordered(order, po_item(deploy=False), trunk_po()), state=state)
    assert_refused(ctrl, status, result, "also claimed by port-channel")


@pytest.mark.parametrize("members", [["eth1/7"], ["e1/7"], ["ETHERNET1/7"], [IF8, " Ethernet1/7 "], ["Ethernet1/8,Ethernet1/7"]])
def test_competing_claim_spelling_and_list_forms_are_normalised(members):
    ctrl = baseline_ctrl()
    status, result = po_conflicts_run(ctrl, [po_item(deploy=False), trunk_po(members=members)])
    assert_refused(ctrl, status, result, "also claimed by port-channel")


@pytest.mark.parametrize("order", ORDERS)
def test_two_pvlan_port_channels_still_cannot_share_a_member(order):
    ctrl = baseline_ctrl()
    status, result = po_conflicts_run(ctrl, ordered(order, po_item(deploy=False), po_item(name="po11", deploy=False)))
    assert status == "fail" and "also assigns it to port-channel" in result["msg"] and ctrl.writes() == []


@pytest.mark.parametrize("token", ["Ethernet1/5-8", "Ethernet1/7-9", "Ethernet1/x", "Port-channel3"])
def test_member_entry_that_cannot_be_resolved_is_refused_with_an_explanation(token):
    ctrl = baseline_ctrl()
    status, result = po_conflicts_run(ctrl, [po_item(deploy=False), trunk_po(members=[token])])
    assert_refused(ctrl, status, result, "cannot be resolved")


# ------------------------------------------------------------------ the existing HAVE-based controls are kept
def test_have_based_direct_child_control_is_kept():
    ctrl = created_ctrl()
    status, result = po_conflicts_run(ctrl, [_eth(IF7)], state="replaced")
    assert status == "fail" and "managed by the parent" in result["msg"] and ctrl.writes() == []


def test_have_based_member_in_another_port_channel_control_is_kept():
    ctrl = baseline_ctrl()
    ctrl.detail[IF7]["policy"] = "int_port_channel_trunk_member_11_1"
    status, result = po_conflicts_run(ctrl, [po_item()])
    assert status == "fail" and "already a port-channel member" in result["msg"] and ctrl.writes() == []


# ------------------------------------------------------------------ non-conflicting changes are preserved (positive controls)
def _other_port_ctrl():
    ctrl = baseline_ctrl()
    nv = trunk_host_nv(IF8)
    ctrl.detail[IF8] = {"policy": TRUNK, "nvPairs": nv}
    return ctrl


@pytest.mark.parametrize("order", ORDERS)
def test_pvlan_po_with_a_direct_change_on_ANOTHER_port_is_unaffected(order):
    ctrl = _other_port_ctrl()
    ctrl.previews = [good_preview()]
    other = _eth(IF8)
    other["profile"]["description"] = "independent change"
    status, result = po_conflicts_run(ctrl, ordered(order, po_item(deploy=False), other))
    assert status == "exit", result
    assert len(ctrl.creates()) == 1 and ctrl.requests("POST", "/rest/interface/modify"), "both independent writes happen"


@pytest.mark.parametrize("order", ORDERS)
def test_pvlan_po_and_a_port_channel_with_a_DIFFERENT_member_are_unaffected(order):
    ctrl = _other_port_ctrl()
    status, result = po_conflicts_run(ctrl, ordered(order, po_item(deploy=False), trunk_po(members=[IF8])))
    assert status == "exit", result
    assert len(ctrl.creates()) == 2


def test_flows_without_a_pvlan_port_channel_get_no_new_restriction():
    # ordinary Po + a direct entry for its member and a spelling the new check cannot resolve: unchanged behaviour
    ctrl = _other_port_ctrl()
    status, result = po_conflicts_run(ctrl, [trunk_po(members=["Ethernet1/5-8"]), direct_child(IF8)])
    assert status == "exit", result
    ctrl2 = _other_port_ctrl()
    status, result = po_conflicts_run(ctrl2, [trunk_po(members=[IF8]), trunk_po(name="po12", members=[IF8])])
    assert status == "exit", "two ORDINARY port-channels sharing a member are not this change's business"


def test_m1_creation_and_m2_repetition_still_work():
    ctrl = baseline_ctrl()
    ctrl.previews = [good_preview()]
    status, result = po_conflicts_run(ctrl, [po_item()])
    assert status == "exit" and result["changed"] is True and len(ctrl.creates()) == 1
    ctrl2 = created_ctrl()
    status, result = po_conflicts_run(ctrl2, [po_item()])
    assert status == "exit" and result["changed"] is False and ctrl2.writes() == []


# ------------------------------------------------------------------ pure units: normalisation and switch identity
def test_normalize_member_list_forms():
    names, bad = P.normalize_member_list("Ethernet1/7, eth1/8 ,e1/9,ETHERNET1/10/1")
    assert names == {"ethernet1/7", "ethernet1/8", "ethernet1/9", "ethernet1/10/1"} and bad == []
    names, bad = P.normalize_member_list("Ethernet1/5-8,Port-channel3,,")
    assert names == set() and bad == ["Ethernet1/5-8", "Port-channel3"]
    assert P.normalize_member_list("") == (set(), []) and P.normalize_member_list(None) == (set(), [])


class _Stub(object):
    """An object built WITHOUT __init__ (the pattern the existing unit tests use): the check reads only self.want."""
    pvlan_blocked = None

    def __init__(self, wants):
        import types
        self.want = wants
        self.pvlan_blocked = []
        self.dcnm_intf_pvlan_block = types.MethodType(module.DcnmIntf.dcnm_intf_pvlan_block, self)
        # bound lazily: the method does not exist in the earlier code, and only THESE tests may fail there
        self.dcnm_intf_pvlan_requested_conflicts = types.MethodType(module.DcnmIntf.dcnm_intf_pvlan_requested_conflicts, self)


def _want(policy, name, sno, nv):
    return {"policy": policy, "interfaces": [{"ifName": name, "serialNumber": sno, "nvPairs": nv}]}


def test_conflicts_are_scoped_by_switch_serial():
    parent = _want(P.PO_HOST_POLICY, "Port-channel10", "SER-A", {"MEMBER_INTERFACES": "Ethernet1/7"})
    same_port_other_switch = _want("int_trunk_host", "Ethernet1/7", "SER-B", {})
    same_port_same_switch = _want("int_trunk_host", "Ethernet1/7", "SER-A", {})
    stub = _Stub([parent, same_port_other_switch])
    stub.dcnm_intf_pvlan_requested_conflicts()
    assert stub.pvlan_blocked == [], "the same port name on ANOTHER switch is not a conflict"
    stub = _Stub([same_port_same_switch, parent])
    stub.dcnm_intf_pvlan_requested_conflicts()
    assert [b["interface"] for b in stub.pvlan_blocked] == ["Ethernet1/7"]


def test_vpc_peer_members_are_matched_on_their_own_peer_serial():
    parent = _want(P.PO_HOST_POLICY, "Port-channel10", "SER-A", {"MEMBER_INTERFACES": "Ethernet1/7"})
    vpc_hit = _want("int_vpc_trunk_host", "vPC20", "SER-A~SER-B", {"PEER1_MEMBER_INTERFACES": "Ethernet1/7", "PEER2_MEMBER_INTERFACES": ""})
    vpc_peer2_other_switch = _want("int_vpc_trunk_host", "vPC21", "SER-A~SER-B", {"PEER1_MEMBER_INTERFACES": "", "PEER2_MEMBER_INTERFACES": "Ethernet1/7"})
    stub = _Stub([parent, vpc_hit])
    stub.dcnm_intf_pvlan_requested_conflicts()
    assert len(stub.pvlan_blocked) == 1
    stub = _Stub([parent, vpc_peer2_other_switch])
    stub.dcnm_intf_pvlan_requested_conflicts()
    assert stub.pvlan_blocked == [], "peer-2 members belong to the SECOND serial"


def test_no_pvlan_parent_means_no_work_and_no_blocks():
    stub = _Stub([_want("int_trunk_host", "Ethernet1/7", "SER-A", {}),
                  _want("int_port_channel_trunk_host", "Port-channel11", "SER-A", {"MEMBER_INTERFACES": "Ethernet1/5-8"})])
    stub.dcnm_intf_pvlan_requested_conflicts()
    assert stub.pvlan_blocked == []
