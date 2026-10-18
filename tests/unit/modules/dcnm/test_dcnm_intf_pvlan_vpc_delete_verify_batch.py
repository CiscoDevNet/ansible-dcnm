"""PR725 DF-2: the post-deploy verification of a PVLAN vPC DELETION is planned per vPC pair and round, like the one of a creation.

Same controller double and entry point as test_dcnm_intf_pvlan_vpc_batch (MultiVpc, the REAL main()). The judgement of each vPC is unchanged
(dcnm_intf_pvlan_vpc_deleted_judge); what changes is who shares the reads: every round reads the parents of a pair once and each peer serial
once for the legs of ALL the vPCs the pair deletes. Values are SYNTHETIC. NOT LIVE TESTED by this file."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from . import test_dcnm_intf_pvlan_vpc_batch as B
from . import test_dcnm_intf_pvlan_vpc_harness as V

module = B.module
PA, PB = B.PA, B.PB


def deleted_setup(n, npairs=1, members=1):
    """N vPCs created and deployed, then the controller double moved to a new invocation with recording reset."""
    ctrl, config = B.created(n, npairs, members)
    assert B.run(ctrl, config)[0] == "exit"
    ctrl.next_invocation()
    ctrl.calls = []
    ctrl.sleep_log[:] = []
    return ctrl, config


def delete_all(ctrl, config):
    items = []
    for c in config:
        index = next(i for i, pair in enumerate(B.PAIRS) if B.IPS[pair[0]] in c["switch"])
        items.append(ctrl.del_item(int(c["name"][3:]), index))
    return B.run(ctrl, items, state="deleted")


@pytest.mark.parametrize("members", [1, 2])
@pytest.mark.parametrize("n", [1, 2, 5, 10])
def test_deletion_reads_do_not_grow_with_the_number_of_vpcs(n, members):
    ctrl, config = deleted_setup(n, members=members)
    status, result = delete_all(ctrl, config)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    # one round: parents (1 bulk of the pair) + per peer serial summary + forced bulk + policy list = 7, whatever N and members per peer
    assert B.post_kinds(ctrl) == {"summary": 2, "bulk": 3, "policies": 2}
    assert B.post_gets(ctrl) == 7 and ctrl.sleep_log == []
    assert sorted(result["pvlan_verification"]) == sorted(c["name"].replace("vpc", "vPC") for c in config)
    assert all(v["state"] == "verified" and v["parent"] == "absent" and set(v["peers"].values()) == {"verified"}
               for v in result["pvlan_verification"].values())


def test_two_pairs_cost_one_round_each_not_one_per_vpc():
    ctrl, config = deleted_setup(6, npairs=2)
    status, result = delete_all(ctrl, config)
    assert status == "exit", result.get("msg")
    assert B.post_kinds(ctrl) == {"summary": 4, "bulk": 6, "policies": 4}


def test_a_vpc_whose_member_is_not_in_sync_fails_alone_and_the_others_are_still_reported():
    ctrl, config = deleted_setup(3)
    ctrl.ready_round[(V.SN2, "Ethernet2/11")] = None
    status, result = delete_all(ctrl, config)
    assert status == "fail", "a member that never reaches In-Sync cannot be reported as released"
    assert result["msg"].startswith("vPC vPC11 was deleted but its release could not be verified on every peer")
    assert "peer 2 (%s)" % V.SN2 in result["msg"] and "Ethernet2/11 is not In-Sync" in result["msg"]
    assert "vPC10" not in result["msg"] and "vPC12" not in result["msg"]
    states = dict((k, v["state"]) for k, v in result["pvlan_verification"].items())
    assert states == {"vPC10": "verified", "vPC11": "failed", "vPC12": "verified"}
    # the pair is read every round (7 GETs) until the budget of 6 rounds with 5 waits is spent: per pair, not per vPC
    assert (B.post_gets(ctrl), len(ctrl.sleep_log)) == (6 * 7, 5)


def test_two_failing_vpcs_are_both_named():
    ctrl, config = deleted_setup(3)
    ctrl.ready_round[(V.SN2, "Ethernet2/10")] = None
    ctrl.ready_round[(V.SN1, "Ethernet1/12")] = None
    status, result = delete_all(ctrl, config)
    assert status == "fail"
    assert "vPC vPC10 was deleted" in result["msg"] and "vPC vPC12 was deleted" in result["msg"] and "vPC vPC11 was deleted" not in result["msg"]
    assert dict((k, v["state"]) for k, v in result["pvlan_verification"].items()) == {"vPC10": "failed", "vPC11": "verified", "vPC12": "failed"}


def test_a_late_convergence_costs_a_round_per_pair_not_per_vpc():
    ctrl, config = deleted_setup(10)
    for k in range(10, 20):
        ctrl.ready_round[(V.SN1, "Ethernet1/%d" % k)] = 1
    status, result = delete_all(ctrl, config)
    assert status == "exit", result.get("msg")
    assert (B.post_gets(ctrl), len(ctrl.sleep_log)) == (2 * 7, 1)


@pytest.mark.parametrize("kind, serial, needle", [
    ("summary", V.SN2, "the interface summary of %s could not be read authoritatively" % V.SN2),
    ("bulk", V.SN1, "could not be read authoritatively"),
    ("policies", V.SN2, "the switch policy list of %s could not be read authoritatively" % V.SN2),
])
def test_an_unreadable_peer_fails_every_vpc_of_the_pair_and_is_never_taken_for_absence(kind, serial, needle):
    ctrl, config = deleted_setup(3)
    ctrl.post_fail[(kind, serial)] = 10 ** 6
    status, result = delete_all(ctrl, config)
    assert status == "fail" and needle in result["msg"], result.get("msg")
    assert all(v["state"] == "failed" for v in result["pvlan_verification"].values())


@pytest.mark.parametrize("label, inject, needle", [
    ("child still listed", lambda c, s: c.post_extra.setdefault(s, []).append(c._summary_entry(s, "port-channel11", {"policy": V.VPC_PO}, "In-Sync")),
     "the interface summary still lists port-channel11"),
    ("member missing from the summary", lambda c, s: c.post_drop.setdefault(s, set()).add("Ethernet2/11" if s == V.SN2 else "Ethernet1/11"),
     "is not In-Sync in the interface summary"),
    ("member duplicated in the summary", lambda c, s: c.post_dup.setdefault(s, set()).add("Ethernet2/11" if s == V.SN2 else "Ethernet1/11"),
     "is not In-Sync in the interface summary"),
    ("member not released (admin up)", lambda c, s: c.post_mutate.__setitem__((s, "Ethernet2/11" if s == V.SN2 else "Ethernet1/11"), {"ADMIN_STATE": "true"}),
     "member Ethernet"),
])
def test_a_partial_release_of_one_peer_fails_that_vpc_only(label, inject, needle):
    ctrl, config = deleted_setup(3)
    inject(ctrl, V.SN2)
    status, result = delete_all(ctrl, config)
    assert status == "fail", label
    assert result["msg"].startswith("vPC vPC11 was deleted but its release could not be verified on every peer"), (label, result["msg"][:200])
    assert needle in result["msg"] and "vPC10" not in result["msg"] and "vPC12" not in result["msg"], label
    assert result["pvlan_verification"]["vPC10"]["state"] == "verified" and result["pvlan_verification"]["vPC12"]["state"] == "verified"
    assert "peer 2 (%s)" % V.SN2 in result["msg"] and "peer 1" not in result["msg"], "the clean peer is not blamed"


def test_the_parent_that_remains_fails_that_vpc_and_names_it():
    ctrl, config = deleted_setup(2)
    real = module.DcnmIntf.dcnm_intf_get_intf_info

    def parent_back(self, name, sno, kind, *a, **k):
        if ctrl.deployed and kind == "INTERFACE_VPC" and name == "vPC11":
            return {"policy": V.VPC_HOST}
        return real(self, name, sno, kind, *a, **k)

    from unittest.mock import patch
    with patch.object(module.DcnmIntf, "dcnm_intf_get_intf_info", parent_back):
        status, result = delete_all(ctrl, config)
    assert status == "fail" and "the vPC vPC11 is still present in the controller's intent" in result["msg"]
    assert result["pvlan_verification"]["vPC11"]["parent"] == "still present" and result["pvlan_verification"]["vPC10"]["state"] == "verified"


def test_the_same_vpc_name_on_two_pairs_is_judged_per_pair():
    ctrl, config = B.same_name_on_two_pairs()
    assert B.run(ctrl, config)[0] == "exit"
    ctrl.next_invocation()
    ctrl.calls = []
    ctrl.sleep_log[:] = []
    ctrl.ready_round[(B.PAIRS[1][1], "Ethernet2/10")] = None  # pair B, peer 2 only
    status, result = B.run(ctrl, [ctrl.del_item(10, 0), ctrl.del_item(10, 1)], state="deleted")
    assert status == "fail"
    assert "peer 2 (%s)" % B.PAIRS[1][1] in result["msg"]
    assert not any(s in result["msg"] for s in B.PAIRS[0]), "pair A's serials never appear in pair B's failure"


def test_a_reversed_switch_order_keeps_the_controller_peer_identity():
    ctrl, config = deleted_setup(2)
    items = [ctrl.del_item(10), ctrl.del_item(11)]
    items[1]["switch"] = list(reversed(items[1]["switch"]))
    status, result = B.run(ctrl, items, state="deleted")
    assert status == "exit", result.get("msg")
    assert B.post_gets(ctrl) == 7 and all(v["state"] == "verified" for v in result["pvlan_verification"].values())


# ============================================================== Alpha review F-1 / F-3: each remaining check has a discriminating test
class _PostDeploy(B.MultiVpc):
    """MultiVpc + post-deploy detail changes the harness does not offer: an extra intent entry per serial (`post_detail_extra`), a policy
    replaced on a member (`post_policy`) and nvPairs applied from a given verification round on (`late_mutate`: (serial, ifName) ->
    (rounds waited, nvPairs))."""

    def __init__(self, *a, **k):
        super(_PostDeploy, self).__init__(*a, **k)
        self.post_detail_extra, self.post_policy, self.late_mutate = {}, {}, {}

    def _peer_details(self, serial):
        out = super(_PostDeploy, self)._peer_details(serial)
        if not self.deployed or "~" in serial:
            return out
        for d in out:
            intf = d["interfaces"][0]
            if (serial, intf["ifName"]) in self.post_policy:
                d["policy"] = self.post_policy[(serial, intf["ifName"])]
            late = self.late_mutate.get((serial, intf["ifName"]))
            if late and len(self.sleep_log) >= late[0]:
                intf["nvPairs"].update(late[1])
        return out + [dict(e) for e in self.post_detail_extra.get(serial, [])]


def post_deploy_setup(n):
    ctrl, config = deleted_setup(n)
    ctrl.__class__ = _PostDeploy
    ctrl.post_detail_extra, ctrl.post_policy, ctrl.late_mutate = {}, {}, {}
    return ctrl, config


def marked_parent(pair_serial, name):
    """The MEASURED V-7a listing (NDFC 12.6.0.267) of a mark-deleted vPC parent in a peer's summary: markDeleted, Out-of-Sync, no underlay
    policy, while its intent (bulk detail) is already gone. Adopted from Alpha's control C-A (alpha-df2-review/controls)."""
    return {"ifName": name, "serialNo": pair_serial, "fabricName": "test_fabric", "ifType": "INTERFACE_VPC", "isPhysical": "False",
            "deletable": "True", "editAllowed": "True", "markDeleted": "True", "alias": "", "deleteReason": None,
            "complianceStatus": "Out-of-Sync", "underlayPolicies": [], "interfaces": [{"nvPairs": {}}]}


def test_a_parent_still_listed_after_the_deploy_fails_on_the_summary_not_on_the_intent_read():
    """F-1: the partial-deploy detection belongs to the SUMMARY listing; the parent intent read reports a mark-deleted parent as absent."""
    ctrl, _config = deleted_setup(2)
    pair = B.PAIRS[0]
    for serial in pair:
        ctrl.post_extra[serial] = [marked_parent(pair[0] + "~" + pair[1], "vPC11")]
    status, result = B.run(ctrl, [ctrl.del_item(10), ctrl.del_item(11)], state="deleted")
    assert status == "fail" and "the interface summary still lists vPC11" in result["msg"], result.get("msg")
    assert result["pvlan_verification"]["vPC11"]["parent"] == "absent", "the intent of a mark-deleted parent is already empty"
    assert result["pvlan_verification"]["vPC11"]["state"] == "failed" and result["pvlan_verification"]["vPC10"]["state"] == "verified"


def test_a_child_still_in_the_intent_of_one_peer_fails_that_vpc_only():
    """F-3 (M4): the child port-channel is no longer listed by the summary but is still in the peer's intent (bulk detail)."""
    ctrl, config = post_deploy_setup(3)
    child = {"serialNumber": V.SN2, "ifName": "port-channel11", "nvPairs": {"INTF_NAME": "port-channel11"}}
    ctrl.post_detail_extra[V.SN2] = [{"policy": V.VPC_PO, "interfaces": [child]}]
    status, result = delete_all(ctrl, config)
    assert status == "fail" and result["msg"].startswith("vPC vPC11 was deleted but its release could not be verified"), result.get("msg")
    assert "port-channel11" in result["msg"] and "vPC10" not in result["msg"] and "vPC12" not in result["msg"]
    assert "peer 2 (%s)" % V.SN2 in result["msg"] and "peer 1" not in result["msg"]


def test_a_member_left_on_another_policy_after_the_deploy_fails_that_vpc_only():
    """F-3 (M8): the released member holds a policy that is not a released member policy; the release contract is not even applicable."""
    ctrl, config = post_deploy_setup(3)
    ctrl.post_policy[(V.SN1, "Ethernet1/11")] = "int_access_host"
    status, result = delete_all(ctrl, config)
    assert status == "fail" and result["msg"].startswith("vPC vPC11 was deleted but its release could not be verified"), result.get("msg")
    assert "Ethernet1/11" in result["msg"] and "peer 1 (%s)" % V.SN1 in result["msg"] and "vPC10" not in result["msg"]


def test_a_vpc_verified_in_an_earlier_round_is_judged_again_until_its_pair_closes():
    """F-3 (M9): vPC10 is clean in round 1 while vPC11 is still converging; in round 2 vPC10's member comes back administratively up. The pair
    is closed only when EVERY vPC is clean in the same round, so vPC10 is judged again and fails (a stale `verified` is never kept)."""
    ctrl, config = post_deploy_setup(2)
    ctrl.ready_round[(V.SN1, "Ethernet1/11")] = 1
    ctrl.late_mutate[(V.SN2, "Ethernet2/10")] = (1, {"ADMIN_STATE": "true"})
    status, result = delete_all(ctrl, config)
    assert status == "fail", "a vPC that regressed after an earlier clean round must not stay verified"
    assert "vPC vPC10 was deleted but its release could not be verified" in result["msg"], result["msg"][:300]
    assert result["pvlan_verification"]["vPC10"]["state"] == "failed" and result["pvlan_verification"]["vPC11"]["state"] == "verified"
