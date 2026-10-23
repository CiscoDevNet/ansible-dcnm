"""The post-deploy verification of a PVLAN vPC DELETION reads ONE summary per peer serial and round (2 GETs per pair and
round), whatever the number of vPCs or members, and judges every vPC of the pair on those answers.

The intent, the release contract and the policy residue are proven FRESH BEFORE the deploy (the release proof and phase C of
dcnm_intf_pvlan_vpc_release_members); after the deploy the module reads only what the deploy changed: the listings and the In-Sync
status of each peer. The checks that used to run after the deploy are exercised here at the phase that now owns them (injected when
the controller releases the members), and the contract change -- what is no longer re-read after the deploy -- is asserted
explicitly. Same controller double and entry point as test_dcnm_intf_pvlan_vpc_batch (MultiVpc, the REAL main()). Values are
SYNTHETIC. NOT LIVE TESTED by this file.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

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
    # one round: ONE summary per peer serial = 2, whatever N and members per peer (previously 7: pair bulk, peer bulks and policy lists)
    assert B.post_kinds(ctrl) == {"summary": 2}
    assert B.post_gets(ctrl) == 2 and ctrl.sleep_log == []
    assert sorted(result["pvlan_verification"]) == sorted(c["name"].replace("vpc", "vPC") for c in config)
    assert all(v["state"] == "verified" and v["parent"] == "not listed" and set(v["peers"].values()) == {"verified"}
               for v in result["pvlan_verification"].values())


def test_two_pairs_cost_one_round_each_not_one_per_vpc():
    ctrl, config = deleted_setup(6, npairs=2)
    status, result = delete_all(ctrl, config)
    assert status == "exit", result.get("msg")
    assert B.post_kinds(ctrl) == {"summary": 4}


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
    # the pair is read every round (2 GETs) until the budget of 6 rounds with 5 waits is spent: per pair, not per vPC
    assert (B.post_gets(ctrl), len(ctrl.sleep_log)) == (6 * 2, 5)


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
    assert (B.post_gets(ctrl), len(ctrl.sleep_log)) == (2 * 2, 1)


@pytest.mark.parametrize("serial", [V.SN1, V.SN2])
def test_an_unreadable_peer_fails_every_vpc_of_the_pair_and_is_never_taken_for_absence(serial):
    ctrl, config = deleted_setup(3)
    ctrl.post_fail[("summary", serial)] = 10 ** 6
    status, result = delete_all(ctrl, config)
    assert status == "fail" and "the interface summary of %s could not be read authoritatively" % serial in result["msg"], result.get("msg")
    assert all(v["state"] == "failed" and v["parent"] == "unreadable" for v in result["pvlan_verification"].values())


@pytest.mark.parametrize("kind", ["bulk", "policies"])
def test_the_intent_and_policy_reads_are_not_repeated_after_the_deploy(kind):
    """Contract change: these were read after the deploy (fail-closed re-confirmations); a failure there can no longer fail the deletion."""
    ctrl, config = deleted_setup(3)
    for serial in B.PAIRS[0]:
        ctrl.post_fail[(kind, serial)] = 10 ** 6
    status, result = delete_all(ctrl, config)
    assert status == "exit" and all(v["state"] == "verified" for v in result["pvlan_verification"].values()), result.get("msg")
    assert B.post_kinds(ctrl) == {"summary": 2}


def test_one_transient_summary_failure_is_a_transport_retry_not_a_new_round():
    ctrl, config = deleted_setup(2)
    ctrl.post_fail[("summary", V.SN2)] = 1
    status, result = delete_all(ctrl, config)
    assert status == "exit", result.get("msg")
    # the reader's own bounded transport retry (3 attempts, 1 s apart): +1 GET and +1 wait, still one verification round
    assert (B.post_gets(ctrl), len(ctrl.sleep_log)) == (3, 1) and ctrl.sleep_log == [1]


@pytest.mark.parametrize("label, inject, needle", [
    ("child still listed", lambda c, s: c.post_extra.setdefault(s, []).append(c._summary_entry(s, "port-channel11", {"policy": V.VPC_PO}, "In-Sync")),
     "the interface summary still lists port-channel11"),
    ("member missing from the summary", lambda c, s: c.post_drop.setdefault(s, set()).add("Ethernet2/11" if s == V.SN2 else "Ethernet1/11"),
     "is not In-Sync in the interface summary"),
    ("member duplicated in the summary", lambda c, s: c.post_dup.setdefault(s, set()).add("Ethernet2/11" if s == V.SN2 else "Ethernet1/11"),
     "is not In-Sync in the interface summary"),
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


def test_a_parent_back_in_the_intent_after_the_deploy_is_not_read_again():
    """Contract change: the parent's intent is not read after the deploy (the pair bulk used to re-confirm it). The deletion of the parent is
    proven by the confirmed mark-delete (or, for a saved deletion, the controller's marked-for-deletion listing); after the deploy the
    summaries prove it is no longer listed. A re-creation by another party after the deploy is outside the module's verification."""
    ctrl, config = deleted_setup(2)
    real = module.DcnmIntf.dcnm_intf_get_intf_info

    def parent_back(self, name, sno, kind, *a, **k):
        if ctrl.deployed and kind == "INTERFACE_VPC" and name == "vPC11":
            return {"policy": V.VPC_HOST}
        return real(self, name, sno, kind, *a, **k)

    from unittest.mock import patch
    with patch.object(module.DcnmIntf, "dcnm_intf_get_intf_info", parent_back):
        status, result = delete_all(ctrl, config)
    assert status == "exit", result.get("msg")
    assert result["pvlan_verification"]["vPC11"]["parent"] == "not listed" and B.post_kinds(ctrl) == {"summary": 2}


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
    assert B.post_gets(ctrl) == 2 and all(v["state"] == "verified" for v in result["pvlan_verification"].values())


# ============================================================== review F-1 / F-3: each remaining check has a discriminating test
class _PostDeploy(B.MultiVpc):
    """MultiVpc + post-deploy SUMMARY changes the harness does not offer: the member's listed policy (`post_policy`, (serial, ifName) ->
    template) and a compliance status from a given verification round on (`late_status`, (serial, ifName) -> (rounds waited, status));
    and a live policy added when the controller marks a vPC deleted (`marked_policy`, vPC name -> (serial, policy entry))."""

    def __init__(self, *a, **k):
        super(_PostDeploy, self).__init__(*a, **k)
        self.post_policy, self.late_status, self.marked_policy = {}, {}, {}

    def _peer_summary(self, serial):
        out = super(_PostDeploy, self)._peer_summary(serial)
        if not self.deployed:
            return out
        for e in out:
            key = (serial, e.get("ifName"))
            if key in self.post_policy and e.get("underlayPolicies"):
                e["underlayPolicies"][0]["templateName"] = self.post_policy[key]
            late = self.late_status.get(key)
            if late and len(self.sleep_log) >= late[0]:
                e["complianceStatus"] = late[1]
        return out

    def __call__(self, mod, method, path, data=None):
        if method == "DELETE" and path.endswith(V.MARKDELETE):
            name = json.loads(data)[0]["ifName"]
            if name in self.marked_policy:
                serial, policy = self.marked_policy[name]
                self.policies_extra[serial].append(policy)
        return super(_PostDeploy, self).__call__(mod, method, path, data)


def post_deploy_setup(n):
    ctrl, config = deleted_setup(n)
    ctrl.__class__ = _PostDeploy
    ctrl.post_policy, ctrl.late_status, ctrl.marked_policy = {}, {}, {}
    return ctrl, config


def marked_parent(pair_serial, name):
    """The MEASURED listing (NDFC 12.6.0.267) of a mark-deleted vPC parent in a peer's summary: markDeleted, Out-of-Sync, no underlay
    policy, while its intent (bulk detail) is already gone."""
    return {"ifName": name, "serialNo": pair_serial, "fabricName": "test_fabric", "ifType": "INTERFACE_VPC", "isPhysical": "False",
            "deletable": "True", "editAllowed": "True", "markDeleted": "True", "alias": "", "deleteReason": None,
            "complianceStatus": "Out-of-Sync", "underlayPolicies": [], "interfaces": [{"nvPairs": {}}]}


def test_a_parent_still_listed_after_the_deploy_fails_on_the_summary():
    """F-1: the partial-deploy detection belongs to the SUMMARY listing (the parent's intent is already empty after its mark-delete)."""
    ctrl, _config = deleted_setup(2)
    pair = B.PAIRS[0]
    for serial in pair:
        ctrl.post_extra[serial] = [marked_parent(pair[0] + "~" + pair[1], "vPC11")]
    status, result = B.run(ctrl, [ctrl.del_item(10), ctrl.del_item(11)], state="deleted")
    assert status == "fail" and "the interface summary still lists vPC11" in result["msg"], result.get("msg")
    assert result["pvlan_verification"]["vPC11"]["parent"] == "still listed"
    assert result["pvlan_verification"]["vPC11"]["state"] == "failed" and result["pvlan_verification"]["vPC10"]["state"] == "verified"
    assert result["pvlan_verification"]["vPC10"]["parent"] == "not listed"


def test_a_child_still_claimed_on_one_peer_is_refused_before_the_deploy():
    """F-3, moved: a child port-channel still live in one peer's intent carries its live policy; the fresh release proof refuses it
    before any deploy (it used to be found after the deploy with the peer's bulk read)."""
    ctrl, config = post_deploy_setup(3)
    ctrl.marked_policy["vPC11"] = (V.SN2, {"entityName": "port-channel11", "entityType": "INTERFACE", "templateName": V.VPC_PO, "source": "vPC11",
                                           "deleted": False, "policyId": "CHILD-LEFT", "serialNumber": V.SN2})
    status, result = delete_all(ctrl, config)
    assert status == "fail" and "PVLAN vPC vPC11" in result["msg"] and "(peer 2)" in result["msg"], result.get("msg")
    assert "live policies still reference the vPC or its child port-channel" in result["msg"] and "port-channel11" in result["msg"]
    assert ctrl.deploys() == [] and "pvlan_verification" not in result


def test_a_member_listed_with_another_policy_after_the_deploy_fails_that_vpc_only():
    """F-3: the summary entry of the released member reports a readable policy that is not the released one."""
    ctrl, config = post_deploy_setup(3)
    ctrl.post_policy[(V.SN1, "Ethernet1/11")] = "int_access_host"
    status, result = delete_all(ctrl, config)
    assert status == "fail" and result["msg"].startswith("vPC vPC11 was deleted but its release could not be verified"), result.get("msg")
    assert "lists the member Ethernet1/11 with int_access_host, not the released int_trunk_host" in result["msg"]
    assert "peer 1 (%s)" % V.SN1 in result["msg"] and "vPC10" not in result["msg"]


@pytest.mark.parametrize("value", [None, [], [{"templateName": "int_trunk_host"}, {"templateName": "int_access_host"}]])
def test_a_member_entry_without_a_readable_policy_is_not_judged_on_its_policy(value):
    """The summary reader requires the `underlayPolicies` key; its CONTENT is optional in the existing contract (pvlan_summary_policy:
    null or empty = no policy reported, several objects = unknown). Neither is a failure of the post-deploy proof, and no other read is made
    to recover the policy."""
    ctrl, config = deleted_setup(2)
    real = B.MultiVpc._peer_summary

    def no_policy(self, serial):
        out = real(self, serial)
        if self.deployed:
            for e in out:
                if e.get("ifName") == "Ethernet1/10":
                    e["underlayPolicies"] = value
        return out

    from unittest.mock import patch
    with patch.object(B.MultiVpc, "_peer_summary", no_policy):
        status, result = delete_all(ctrl, config)
    assert status == "exit" and result["pvlan_verification"]["vPC10"]["state"] == "verified", result.get("msg")
    assert B.post_kinds(ctrl) == {"summary": 2}


def test_a_member_changed_after_the_deploy_is_not_re_read():
    """Contract change: the member's intent (the peer bulk) is not read after the deploy; an administrative change made by another
    party after the pre-deploy proof is outside the module's verification (the external harness checks it)."""
    ctrl, config = deleted_setup(3)
    ctrl.post_mutate[(V.SN2, "Ethernet2/11")] = {"ADMIN_STATE": "true"}
    status, result = delete_all(ctrl, config)
    assert status == "exit" and all(v["state"] == "verified" for v in result["pvlan_verification"].values()), result.get("msg")


def test_a_vpc_verified_in_an_earlier_round_is_judged_again_until_its_pair_closes():
    """F-3: vPC10 is clean in round 1 while vPC11 is still converging; in round 2 vPC10's member is Out-of-Sync again. The pair is
    closed only when EVERY vPC is clean in the same round, so vPC10 is judged again and fails (a stale `verified` is never kept)."""
    ctrl, config = post_deploy_setup(2)
    ctrl.ready_round[(V.SN1, "Ethernet1/11")] = 1
    ctrl.late_status[(V.SN2, "Ethernet2/10")] = (1, "Out-of-Sync")
    status, result = delete_all(ctrl, config)
    assert status == "fail", "a vPC that regressed after an earlier clean round must not stay verified"
    assert "vPC vPC10 was deleted but its release could not be verified" in result["msg"], result["msg"][:300]
    assert result["pvlan_verification"]["vPC10"]["state"] == "failed" and result["pvlan_verification"]["vPC11"]["state"] == "verified"
