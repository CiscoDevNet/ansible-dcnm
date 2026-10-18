"""PR725 RESULT-IDENTITY: `pvlan_verification` keeps one entry per vPC even when the SAME vPC name is deleted on two pairs.

Before: the result was keyed by the vPC name alone, so vPC10 of pair A and vPC10 of pair B overwrote each other (the judgement inside the
module already tells them apart; only the presentation lost one). Now a name that is unique in the invocation keeps its plain key and entry
format; a repeated name is keyed `<name>@<pair>` (pair = both peer serials, alphabetical) with `vpc` and `pair` inside the entry.
Same controller double and entry point as test_dcnm_intf_pvlan_vpc_batch (the REAL main()). Values are SYNTHETIC. NOT LIVE TESTED."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from . import test_dcnm_intf_pvlan_vpc_batch as B

A_PAIR = "~".join(sorted(B.PAIRS[0]))
B_PAIR = "~".join(sorted(B.PAIRS[1]))
KEY_A, KEY_B = "vPC10@" + A_PAIR, "vPC10@" + B_PAIR


def deleted_same_name(reverse_b=False, fail=None):
    ctrl, config = B.same_name_on_two_pairs()
    assert B.run(ctrl, config)[0] == "exit"
    ctrl.next_invocation()
    ctrl.calls = []
    ctrl.sleep_log[:] = []
    if fail:
        fail(ctrl)
    items = [ctrl.del_item(10, 0), ctrl.del_item(10, 1)]
    if reverse_b:
        items[1]["switch"] = list(reversed(items[1]["switch"]))
    status, result = B.run(ctrl, items, state="deleted")
    return ctrl, status, result


def test_the_same_vpc_name_on_two_pairs_keeps_both_results():
    ctrl, status, result = deleted_same_name()
    assert status == "exit", result.get("msg")
    ver = result["pvlan_verification"]
    assert sorted(ver) == sorted([KEY_A, KEY_B]), "one entry per pair, no plain vPC10 entry that could read as both"
    for key, pair, vpc_pair in ((KEY_A, A_PAIR, B.PAIRS[0]), (KEY_B, B_PAIR, B.PAIRS[1])):
        entry = ver[key]
        assert entry["vpc"] == "vPC10" and entry["pair"] == pair and entry["state"] == "verified" and entry["parent"] == "not listed"
        assert sorted(entry["peers"]) == sorted(vpc_pair), "every peer of THIS pair, none of the other"
        assert set(entry["peers"].values()) == {"verified"}


def test_one_good_pair_and_one_failed_pair_are_both_reported_and_the_run_still_fails():
    def member_stuck(ctrl):
        ctrl.ready_round[(B.PAIRS[1][1], "Ethernet2/10")] = None
    ctrl, status, result = deleted_same_name(fail=member_stuck)
    assert status == "fail" and "vPC vPC10 was deleted but its release could not be verified" in result["msg"]
    assert B.PAIRS[1][1] in result["msg"] and not any(s in result["msg"] for s in B.PAIRS[0])
    ver = result["pvlan_verification"]
    assert sorted(ver) == sorted([KEY_A, KEY_B])
    assert ver[KEY_A]["state"] == "verified" and set(ver[KEY_A]["peers"].values()) == {"verified"}
    assert ver[KEY_B]["state"] == "failed"
    assert ver[KEY_B]["peers"][B.PAIRS[1][0]] == "verified" and ver[KEY_B]["peers"][B.PAIRS[1][1]] != "verified"


def test_an_unreadable_peer_fails_both_entries_and_keeps_both():
    ctrl, status, result = deleted_same_name(fail=lambda c: c.post_fail.__setitem__(("summary", B.PAIRS[1][1]), 10 ** 6))
    assert status == "fail"
    ver = result["pvlan_verification"]
    assert sorted(ver) == sorted([KEY_A, KEY_B]) and ver[KEY_A]["state"] == "verified" and ver[KEY_B]["state"] == "failed"


def test_the_identity_does_not_depend_on_the_order_of_the_peers():
    _c1, _s1, plain = deleted_same_name()
    _c2, _s2, reversed_ = deleted_same_name(reverse_b=True)
    assert sorted(reversed_["pvlan_verification"]) == sorted(plain["pvlan_verification"]) == sorted([KEY_A, KEY_B])
    assert reversed_["pvlan_verification"][KEY_B]["pair"] == B_PAIR
    assert sorted(reversed_["pvlan_verification"][KEY_B]["peers"]) == sorted(B.PAIRS[1])


def test_the_unique_name_keeps_its_plain_key_and_format():
    ctrl, config = B.created(3)
    assert B.run(ctrl, config)[0] == "exit"
    ctrl.next_invocation()
    status, result = B.run(ctrl, [ctrl.del_item(k) for k in (10, 11, 12)], state="deleted")
    assert status == "exit", result.get("msg")
    ver = result["pvlan_verification"]
    assert sorted(ver) == ["vPC10", "vPC11", "vPC12"]
    assert all(sorted(e) == ["parent", "peers", "state"] for e in ver.values()), "no new field when the name is unique"


def test_two_different_names_on_two_pairs_keep_plain_keys():
    ctrl = B.MultiVpc(2)
    config = [ctrl.add_vpc(10, 0), ctrl.add_vpc(11, 1)]
    assert B.run(ctrl, config)[0] == "exit"
    ctrl.next_invocation()
    status, result = B.run(ctrl, [ctrl.del_item(10, 0), ctrl.del_item(11, 1)], state="deleted")
    assert status == "exit", result.get("msg")
    assert sorted(result["pvlan_verification"]) == ["vPC10", "vPC11"]


def test_only_the_repeated_name_is_composite_when_others_are_unique():
    ctrl = B.MultiVpc(2)
    config = [ctrl.add_vpc(10, 0), ctrl.add_vpc(10, 1), ctrl.add_vpc(11, 0)]
    assert B.run(ctrl, config)[0] == "exit"
    ctrl.next_invocation()
    status, result = B.run(ctrl, [ctrl.del_item(10, 0), ctrl.del_item(10, 1), ctrl.del_item(11, 0)], state="deleted")
    assert status == "exit", result.get("msg")
    assert sorted(result["pvlan_verification"]) == sorted([KEY_A, KEY_B, "vPC11"])
    assert "vpc" not in result["pvlan_verification"]["vPC11"]


def test_the_reads_the_writes_and_the_deploy_do_not_change():
    ctrl, status, result = deleted_same_name()
    assert status == "exit"
    # one round per pair, the summary of each peer only (no parent/peer bulk, no policy list after the deploy); one mark-delete per vPC;
    # the release modifies come before the single deploy. The composite keys add no request.
    assert B.post_kinds(ctrl) == {"summary": 4}
    assert len(ctrl.markdeletes()) == 2 and len(ctrl.deploys()) == 1 and ctrl.sleep_log == []
    assert ctrl.order() == ["MODIFY"] * 4 + ["PREVIEW"] * 4 + ["DEPLOY"]
