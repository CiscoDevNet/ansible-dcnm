"""VPC-HOST-E4: controls ONLY of the behaviour that E4 changes (Po G6 reconciliation). NOT LIVE TESTED.

Everything vPC-specific here is INFERRED from the MEASURED regular-Po behaviour (G3-G6) and stays pending L1: the fixtures are simulated.
Controls: persisted channel-group form (no force outside the pending), the released member kept shut (no shutdown / no write when already
shut), a repeated deletion, partial peer states, an unknown mark-delete answer, and the Po/vPC target separation.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

import pytest

from .test_dcnm_intf_pvlan_vpc_harness import (
    M1,
    SN1,
    SN2,
    create_pending,
    created_ctrl,
    delete_previews,
    release_only,
    run_vpc,
    vpc_del_item,
    member_after,
)


def test_the_persisted_member_form_has_no_force_and_the_pending_form_is_the_only_one_that_carries_it():
    persisted = member_after("Ethernet1/7")
    pending = create_pending("Ethernet1/7")
    flat = json.dumps(persisted)
    assert "channel-group 10 mode active" in flat and "force" not in flat
    assert "channel-group 10 force mode active" in json.dumps(pending)


def test_a_member_already_shut_after_the_release_is_not_written_at_all():
    ctrl = created_ctrl()
    ctrl.release_admin_up = False  # the controller already returns the members ADMIN_STATE false
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit", result.get("msg")
    assert ctrl.modifies() == [] and len(ctrl.deploys()) == 1 and len(ctrl.markdeletes()) == 1
    assert all(r.get("member_modify") in (None, "", "not needed") or "ADMIN_STATE" not in r["member_modify"] for r in result.get("pvlan_vpc_release", []))


def test_a_repeated_deletion_after_a_completed_one_writes_nothing():
    ctrl = created_ctrl()
    delete_previews(ctrl)
    assert run_vpc(ctrl, [vpc_del_item()], state="deleted")[0] == "exit"
    before = len(ctrl.writes())
    ctrl.next_invocation()
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and result["changed"] is False
    assert len(ctrl.writes()) == before, "a second invocation must not write again"


def test_a_failing_member_modify_on_the_second_peer_stops_before_the_deploy_with_peer_one_confirmed():
    ctrl = created_ctrl()
    ctrl.member_modify_fail = {SN2}
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and ctrl.deploys() == [], result.get("msg")
    assert "peer 2" in result["msg"] and "recovery is a human decision" in result["msg"]
    assert "legacy interface/modify of %s on peer 1 ADMIN_STATE false" % M1 in result["msg"]
    assert ctrl.nodes[SN1][M1]["nvPairs"]["ADMIN_STATE"] == "false"


@pytest.mark.parametrize(
    "answer",
    [
        {"RETURN_CODE": 200, "METHOD": "POST", "MESSAGE": "OK", "DATA": {}},
        {"RETURN_CODE": 200, "METHOD": "POST", "MESSAGE": "OK", "DATA": {"value": []}},
        {"RETURN_CODE": 500, "METHOD": "POST", "MESSAGE": "Internal Server Error", "DATA": "boom"},
    ],
    ids=["no-value-item", "empty-value", "http-500"],
)
def test_an_unknown_markdelete_answer_blocks_the_release_and_the_deploy_and_is_not_retried(answer):
    ctrl = created_ctrl()
    ctrl.markdelete_responses = [answer]
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and ctrl.deploys() == [] and ctrl.modifies() == []
    assert len(ctrl.markdeletes()) == 1, "one attempt: the answer is not retried"
    assert "UNVERIFIED" in result["msg"] or "UNVERIFIED".lower() in result["msg"].lower()


def test_the_child_port_channel_listed_as_marked_for_deletion_is_accepted_until_the_deploy():
    ctrl = created_ctrl()
    ctrl.children_marked_deleted = True
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit", result.get("msg")
    release_only(ctrl)
    assert len(ctrl.deploys()) == 1


def test_a_vpc_deletion_never_runs_the_regular_port_channel_steps():
    ctrl = created_ctrl()
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit"
    assert len(ctrl.markdeletes()) == 1, "exactly the vPC mark-delete; the Po G4 step does not ALSO fire on the vPC target"
    assert not result.get("pvlan_po_release") and "pvlan_vpc_release" in result
    assert {r["peer"] for r in result["pvlan_vpc_release"]} == {1, 2}
