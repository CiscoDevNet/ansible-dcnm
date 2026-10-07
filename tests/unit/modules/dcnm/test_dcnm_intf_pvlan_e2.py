"""Native Ethernet PVLAN E2: the corrected behavior for architect review R1 findings F1-F5.

Every case drives the real main() through test_dcnm_intf_pvlan_harness; only external I/O is
mocked. Case IDs R1-xx refer to review/R1/probe_candidate.py, which asserted the E1 DEFECTS; the
cases here assert the corrected result. Response labels: MEASURED (G5/G6 discovery capture),
DOCUMENTED (module source), SYNTHETIC (robustness counterexample, not a claim the controller
emits it), TEMPLATE-PREDICTED (rendered from the pinned installed template, not measured).
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json

import pytest

from .test_dcnm_intf_pvlan_harness import (
    DELETE,
    DEPLOY,
    FIXTURE,
    IF7,
    IF8,
    MODIFY,
    PREVIEW_MARK,
    PVLAN,
    SERIAL,
    TRANSITIONS,
    TRUNK,
    FakeController,
    authority,
    measured_preview,
    ok,
    pending,
    preview,
    pvlan_item,
    pvlan_nv,
    reset_preview,
    run,
    trunk_item,
)

TPROM_A11 = pvlan_nv("G6-M0a")
TPROM_BOTH = pvlan_nv("G6-M0b")
ADD_2212 = dict(pvlan_mode="trunk promiscuous", pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2212"}])
KEEP_2211 = [
    pvlan_item(
        pvlan_mode="trunk promiscuous",
        admin_state=False,
        pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2211"}],
        native_vlan="2301",
        allowed_vlans="2301",
    )
]
TSEC_2212 = [
    pvlan_item(
        pvlan_mode="trunk secondary",
        admin_state=False,
        pvlan_association=[{"primary_vlan": 2210, "secondary_vlan": 2212}],
        native_vlan="2301",
        allowed_vlans="2301",
    )
]
MEASURED_SUCCESS = ok(copy.deepcopy(FIXTURE["deploy_success"]))  # MEASURED (names Ethernet1/7)


def ctrl(nv=TPROM_A11, policy=PVLAN, ifname=IF7):
    c = FakeController()
    c.detail[ifname] = {"policy": policy, "nvPairs": copy.deepcopy(nv)}
    return c


def deploys(c):
    return c.requests("POST", DEPLOY)


def assert_no_writes(c):
    assert c.mutating() == [], c.mutating()
    assert c.requests(mark=PREVIEW_MARK) == []


# ===================================================================================== F1
FAILED_BODIES = {
    "measured_500": {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": FIXTURE["deploy_500"]["data"]},  # MEASURED (G5 PU3)
    "http500_dict": {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {"error": "synthetic"}},  # SYNTHETIC (R1-02/03)
    "dict_error": ok({"reportItemType": "ERROR", "message": "synthetic failure"}),  # SYNTHETIC (R1-04)
    "list_error": ok([{"reportItemType": "ERROR", "message": "CLI command failed", "entity": SERIAL + "~" + IF7}]),  # SYNTHETIC
    "empty_dict": ok({}),  # SYNTHETIC
    "unknown_key": ok({"message": "Interface deployed successfully", "value": [{"serialNumber": SERIAL, "IfName": IF7}], "x": 1}),
    "not_named": ok({"message": "Interface deployed successfully", "value": []}),  # SYNTHETIC
    "mixed_list": ok([{"reportItemType": "WARNING", "message": "No Commands to execute"}, {"reportItemType": "ERROR", "message": "x"}]),
}


class TestF1EveryDeployAttemptIsJudged:
    """A failed or indeterminate attempt fails the run even when every later read says In-Sync."""

    @pytest.mark.parametrize("kind", sorted(FAILED_BODIES))
    def test_primary_attempt(self, kind):
        c = ctrl()
        c.previews = [measured_preview("G6-M0b"), measured_preview("G6-M0b", "post")]
        c.deploy_responses = [copy.deepcopy(FAILED_BODIES[kind])]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "attempt (deploy) failed or is indeterminate" in res["msg"]
        assert len(deploys(c)) == 1
        assert FAILED_BODIES[kind] in res["response"]  # the ORIGINAL response is retained
        assert res["pvlan_attempts"][-1]["site"] == "deploy"

    @pytest.mark.parametrize("kind", sorted(FAILED_BODIES))
    def test_check_deploy_resend_attempt_r1_02(self, kind):
        c = ctrl()
        c.previews = [measured_preview("G6-M0b"), measured_preview("G6-M0b"), measured_preview("G6-M0b", "post")]
        c.deploy_responses = [copy.deepcopy(MEASURED_SUCCESS), copy.deepcopy(FAILED_BODIES[kind])]
        status, res = run(c, [pvlan_item(**ADD_2212)], check_deploy=True)
        assert status == "fail" and "attempt (check_deploy_resend) failed" in res["msg"]
        assert len(deploys(c)) == 2  # nothing after the failed resend
        assert "deploy Ethernet1/7@" + SERIAL + ": accepted" in res["msg"]  # partial progress is reported
        assert FAILED_BODIES[kind] in res["response"]

    @pytest.mark.parametrize("kind", sorted(FAILED_BODIES))
    def test_deployment_status_retry_attempt_r1_03(self, kind):
        c = ctrl()
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("G6-M0b")] * 3 + [measured_preview("G6-M0b", "post")]
        c.compliance = ["Out-of-Sync"] * 9 + ["In-Sync"] * 20
        c.deploy_responses = [copy.deepcopy(MEASURED_SUCCESS)] * 2 + [copy.deepcopy(FAILED_BODIES[kind])]
        status, res = run(c, [pvlan_item(**ADD_2212)], check_deploy=True)
        assert status == "fail" and "attempt (deployment_status_retry) failed" in res["msg"]
        assert len(deploys(c)) == 3
        assert FAILED_BODIES[kind] in res["response"]

    def test_measured_success_at_every_attempt_passes(self):
        c = ctrl()
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("G6-M0b")] * 3 + [measured_preview("G6-M0b", "post")] * 3
        c.compliance = ["Out-of-Sync"] * 9 + ["In-Sync"] * 20
        status, res = run(c, [pvlan_item(**ADD_2212)], check_deploy=True)
        assert status == "exit", res
        assert [a["outcome"] for a in res.get("pvlan_attempts", [])] in ([], ["accepted"] * 3)

    def test_documented_benign_notice_with_matching_readback_passes(self):
        c = ctrl()
        c.previews = [measured_preview("G6-M0b")]
        c.deploy_responses = [ok([{"reportItemType": "WARNING", "message": "No Commands to execute. In-Sync"}])]  # DOCUMENTED
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "exit", res


# ===================================================================================== F2
SUMMARY_DEFECTS = {
    "null": {"underlayPolicies": None},  # R1-07-null
    "absent": {"underlayPolicies": DELETE},
    "missing_source": {"underlayPolicies": [{"templateName": PVLAN}]},  # R1-07-missing-source
    "dict_container": {"underlayPolicies": {"source": ""}},
    "non_dict_entry": {"underlayPolicies": [""]},
    "multiple_direct": {"underlayPolicies": [{"source": "", "templateName": PVLAN}, {"source": "", "templateName": "second-policy"}]},
    "overlay_source": {"underlayPolicies": [{"source": "OVERLAY", "templateName": PVLAN}]},
    "template_mismatch": {"underlayPolicies": [{"source": "", "templateName": "int_access_host"}]},
    "summary_policy_mismatch": {"policy": "int_access_host"},
}
OVERLAY_PROFILE = {  # MEASURED shape of the attachment-owned Eth1/3 entry (discovery g6-s0 policies)
    "autoGenerated": False,
    "deleted": False,
    "entityName": IF7,
    "entityType": "Interface",
    "id": 0,
    "policyId": "PROFILE-NETWORK-82",
    "priority": 1525,
    "secondaryEntityName": "PV_COMMUNITY",
    "secondaryEntityType": "Config_Profile",
    "serialNumber": SERIAL,
    "source": "OVERLAY",
    "templateName": "NA",
}
POLICY_DEFECTS = {
    "overlay_profile": ("extra", [OVERLAY_PROFILE]),
    "second_direct": ("extra", [{"entityName": IF7, "entityType": "INTERFACE", "templateName": TRUNK, "source": "", "deleted": False}]),
    "template_mismatch": ("override", ok([{"entityName": IF7, "entityType": "INTERFACE", "templateName": "int_access_host", "source": "", "deleted": False}])),
    "source_non_empty": ("override", ok([{"entityName": IF7, "entityType": "INTERFACE", "templateName": PVLAN, "source": "OVERLAY", "deleted": False}])),
    "malformed_entry": ("override", ok([{"entityName": IF7}])),
    "not_a_list": ("override", ok({"entityName": IF7})),
    "read_failure": ("override", {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}),
}


def apply_policy_defect(c, kind):
    how, value = POLICY_DEFECTS[kind]
    if how == "extra":
        c.policies_extra = copy.deepcopy(value)
    else:
        c.policies_override = copy.deepcopy(value)


class TestF2OwnershipAuthority:

    @pytest.mark.parametrize("kind", sorted(SUMMARY_DEFECTS))
    @pytest.mark.parametrize("check_mode,deploy", [(False, True), (False, False), (True, True)])
    def test_incomplete_or_conflicting_summary_refuses_before_any_write(self, kind, check_mode, deploy):
        c = ctrl()
        c.summary[IF7] = copy.deepcopy(SUMMARY_DEFECTS[kind])
        status, res = run(c, [pvlan_item(deploy=deploy, **ADD_2212)], check_mode=check_mode)
        assert status == "fail" and "No configuration or deployment request was sent" in res["msg"], res
        assert_no_writes(c)

    @pytest.mark.parametrize("kind", sorted(POLICY_DEFECTS))
    @pytest.mark.parametrize("check_mode", [False, True])
    def test_policy_list_must_show_one_direct_policy(self, kind, check_mode):
        c = ctrl()
        apply_policy_defect(c, kind)
        status, res = run(c, [pvlan_item(**ADD_2212)], check_mode=check_mode)
        assert status == "fail" and "No configuration or deployment request was sent" in res["msg"], res
        assert_no_writes(c)

    def test_deleted_policy_entries_are_ignored_and_the_direct_port_is_accepted(self):
        c = ctrl()
        c.policies_extra = [dict(OVERLAY_PROFILE, deleted=True)]
        c.previews = [measured_preview("G6-M0b")]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "exit", res

    def test_measured_direct_port_control(self):
        c = ctrl()
        c.previews = [measured_preview("G6-M0b")]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "exit", res
        # The policy list is also read by the pre-existing breakout path, so its presence proves
        # nothing alone; the policy-list authority is proven by the read_failure/overlay cases.

    @pytest.mark.parametrize("kind", ["null", "missing_source", "multiple_direct"])
    def test_deleted_state_refuses_an_ambiguous_pvlan_port(self, kind):
        c = ctrl()
        c.summary[IF7] = copy.deepcopy(SUMMARY_DEFECTS[kind])
        status, res = run(c, [{"name": IF7, "switch": ["10.0.0.1"]}], state="deleted")
        assert status == "fail"
        assert_no_writes(c)

    def test_overridden_refuses_an_ambiguous_unlisted_pvlan_port(self):
        c = ctrl()
        c.detail[IF8] = {"policy": PVLAN, "nvPairs": pvlan_nv("G6-M0a", ifname=IF8)}
        c.summary[IF8] = copy.deepcopy(SUMMARY_DEFECTS["missing_source"])
        status, res = run(c, KEEP_2211, state="overridden")
        assert status == "fail"
        assert_no_writes(c)

    def test_ambiguous_second_target_stops_a_valid_first(self):
        c = ctrl()
        c.detail[IF8] = {"policy": PVLAN, "nvPairs": pvlan_nv("G6-M0a", ifname=IF8)}
        c.summary[IF7] = copy.deepcopy(SUMMARY_DEFECTS["null"])
        status, res = run(c, [pvlan_item(IF8, **ADD_2212), pvlan_item(IF7, **ADD_2212)])
        assert status == "fail"
        assert_no_writes(c)


# ===================================================================================== F3
class TestF3RemainingWorkAndConvergence:

    def test_r1_01_converged_before_resend_skips_the_redundant_deploy(self):
        c = ctrl()
        c.previews = [measured_preview("G6-M0b"), measured_preview("G6-M0b", "post")]
        status, res = run(c, [pvlan_item(**ADD_2212)], check_deploy=True)
        assert status == "exit", res
        assert c.order() == ["MODIFY", "PREVIEW", "DEPLOY", "PREVIEW"]
        assert res["pvlan_gate"][-1]["targets"] == {IF7: "converged"}

    def test_r1_05_valid_removal_after_a_blocked_first_attempt(self):
        c = ctrl(TPROM_BOTH)
        c.previews = [preview([])]  # carries no device authority: refused after the intent write
        status, res = run(c, KEEP_2211, state="replaced")
        assert status == "fail" and "ALREADY changed" in res["msg"] and deploys(c) == []
        c.next_invocation()
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("G6-M1")]  # MEASURED: device still has 2212, intent has 2211 only
        before = len(c.calls)
        status, res = run(c, KEEP_2211, state="replaced")
        assert status == "exit", res
        later = list(c.calls[before:])
        assert not [x for x in later if x[1].endswith(MODIFY)] and len([x for x in later if x[1].endswith(DEPLOY)]) == 1

    def test_failed_gate_rerun_for_a_submode_change(self):
        c = ctrl(TRANSITIONS["TS1"]["pre_nv"])
        c.previews = [preview([])]
        assert run(c, TSEC_2212, state="replaced")[0] == "fail"
        c.next_invocation()
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("TS1")]
        status, res = run(c, TSEC_2212, state="replaced")
        assert status == "exit", res
        assert len(deploys(c)) == 1

    def test_deploy_false_then_deploy_true(self):
        c = ctrl()
        assert run(c, [pvlan_item(deploy=False, **ADD_2212)])[0] == "exit"
        assert c.order() == ["MODIFY"]
        c.next_invocation()
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("G6-M0b")]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "exit", res
        assert c.order() == ["MODIFY", "PREVIEW", "DEPLOY"]

    def test_complete_convergence_sends_no_deploy(self):
        c = ctrl(TPROM_BOTH)
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}  # stale summary; device already converged
        c.previews = [measured_preview("G6-M0b", "post")]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "exit", res
        assert deploys(c) == [] and c.requests("POST", MODIFY) == []

    def test_partial_convergence_deploys_only_the_remaining_target(self):
        c = ctrl(TPROM_BOTH)
        c.detail[IF8] = {"policy": PVLAN, "nvPairs": pvlan_nv("G6-M0a", ifname=IF8)}
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        run7, exp7 = authority("G6-M0b", "post", IF7)
        run8, exp8 = authority("G6-M0b", "pre", IF8)
        lines = [l.replace("ethernet1/7", "ethernet1/8") for l in pending("G6-M0b")]
        c.previews = [preview(lines, running=run7 + run8, expected=exp7 + exp8)]
        status, res = run(c, [pvlan_item(IF7, **ADD_2212), pvlan_item(IF8, **ADD_2212)])
        assert status == "exit", res
        sent = [json.loads(x[2]) for x in deploys(c)]
        assert sent == [[{"serialNumber": SERIAL, "ifName": IF8, "fabricName": "test_fabric"}]]

    def test_partial_convergence_keeps_non_pvlan_batch_members(self):
        c = ctrl(TPROM_BOTH)
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.detail[IF8] = {"policy": TRUNK, "nvPairs": copy.deepcopy(FIXTURE["trunk_host_baseline"]["nvPairs"])}
        run7, exp7 = authority("G6-M0b", "post", IF7)
        c.previews = [preview(["interface ethernet1/8", "  description sibling", "configure terminal"], running=run7, expected=exp7)]
        status, res = run(c, [pvlan_item(IF7, **ADD_2212), trunk_item(IF8, description="sibling")])
        assert status == "exit", res
        sent = [json.loads(x[2]) for x in deploys(c)]
        assert sent == [[{"serialNumber": SERIAL, "ifName": IF8, "fabricName": "test_fabric"}]]

    # ---- negative controls
    def test_unexpectedly_empty_initial_preview_is_refused(self):
        running, expected = authority("G6-M0b")
        c = ctrl()
        c.previews = [preview([], status="In-Sync", running=running, expected=expected)]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "is empty but the device differs" in res["msg"] and deploys(c) == []

    def test_wrong_withdrawal_is_refused(self):
        running, expected = authority("G6-M1")
        lines = [l.replace("2210 remove 2212", "2210 remove 2211") for l in pending("G6-M1")]
        c = ctrl(TPROM_BOTH)
        c.previews = [preview(lines, running=running, expected=expected)]
        status, res = run(c, KEEP_2211, state="replaced")
        assert status == "fail" and "unexpected partial removal" in res["msg"] and deploys(c) == []

    def test_stale_controller_expectation_is_refused(self):
        running = authority("G6-M0b")[0]
        stale_expected = authority("G6-M0a")[1]  # the controller still expects the old mapping
        c = ctrl()
        c.previews = [preview(pending("G6-M0b"), running=running, expected=stale_expected)]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "disagrees with the intended state" in res["msg"] and deploys(c) == []

    def test_ambiguous_device_authority_is_refused(self):
        running, expected = authority("G6-M0b")
        c = ctrl()
        c.previews = [preview(pending("G6-M0b"), running=running + running, expected=expected)]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "2 running" in res["msg"] and deploys(c) == []

    def test_missing_device_authority_is_refused(self):
        expected = authority("G6-M0b")[1]
        c = ctrl()
        c.previews = [preview(pending("G6-M0b"), expected=expected)]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "carries no runningConfig" in res["msg"] and deploys(c) == []

    def test_foreign_pending_is_refused(self):
        running, expected = authority("G6-M0b")
        c = ctrl()
        c.previews = [preview(pending("G6-M0b") + ["interface ethernet1/9", "  shutdown"], running=running, expected=expected)]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "outside this deploy batch" in res["msg"] and deploys(c) == []

    def test_malformed_non_trunk_promiscuous_removal_is_refused_on_redeploy(self):
        # Intent already holds the reduced promiscuous mapping (as left by G5 PU3); the device
        # still holds both secondaries. MEASURED PU3 pending carries '22102210 remove 2211'.
        c = ctrl(TRANSITIONS["PU3"]["post_nv"])
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("PU3")]
        status, res = run(
            c, [pvlan_item(pvlan_mode="promiscuous", admin_state=False, pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2212"}])], state="replaced"
        )
        assert status == "fail" and "malformed VLAN number" in res["msg"] and deploys(c) == []

    def test_defect_guard_still_blocks_the_intent_write(self):
        c = ctrl(pvlan_nv("PU2"))
        status, res = run(c, [pvlan_item(pvlan_mode="promiscuous", pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2212"}])], state="replaced")
        assert status == "fail" and "keeps other secondaries is blocked" in res["msg"]
        assert_no_writes(c)


# ===================================================================================== F4
class TestF4BulkCapabilityInCommonPreflight:

    @pytest.mark.parametrize("check_mode", [False, True])
    def test_missing_bulk_api_is_diagnosed_in_both_modes_r1_06(self, check_mode):
        c = ctrl()
        status, res = run(c, [pvlan_item(**ADD_2212)], check_mode=check_mode, bulk=False)
        assert status == "fail" and "bulk interface update API" in res["msg"]
        assert "No configuration or deployment request was sent" in res["msg"]
        assert_no_writes(c)

    def test_invalid_second_object_is_still_reported_first(self):
        c = ctrl()
        bad = pvlan_item(IF8, pvlan_mode="trunk promiscuous", pvlan_mapping=[{"primary_vlan": True, "secondary_vlans": "2"}])
        status, res = run(c, [pvlan_item(**ADD_2212), bad], check_mode=True, bulk=False)
        assert status == "fail" and "integer VLAN ID" in res["msg"]
        assert_no_writes(c)

    def test_no_pvlan_write_needs_no_capability(self):
        c = ctrl(TPROM_BOTH)
        status, res = run(c, [pvlan_item(**ADD_2212)], check_mode=True, bulk=False)  # in sync: no write planned
        assert status == "exit" and res["changed"] is False


# ===================================================================================== F5
class TestF5ActualResetPayload:

    def test_module_reset_payload_and_its_template_predicted_transition(self):
        c = ctrl()
        c.previews = [reset_preview()]  # TEMPLATE-PREDICTED
        status, res = run(c, [{"name": IF7, "switch": ["10.0.0.1"]}], state="deleted")
        assert status == "exit", res
        policy, nv = c.sent_nv()
        assert policy == TRUNK
        assert (nv["BPDUGUARD_ENABLED"], nv["PORTTYPE_FAST_ENABLED"], nv["MTU"], nv["ALLOWED_VLANS"], nv["NATIVE_VLAN"]) == (False, True, "jumbo", "none", "")
        assert (nv["ENABLE_STORM_CONTROL"], nv["STORM_CONTROL_ACTION"]) == (False, "no")

    def test_exact_restoration_fixture_is_not_the_module_reset(self):
        c = ctrl()
        c.previews = [measured_preview("G6-MR")]  # MEASURED exact restoration (BPDUGUARD 'no')
        status, res = run(c, [{"name": IF7, "switch": ["10.0.0.1"]}], state="deleted")
        assert status == "fail" and "disagrees with the intended state" in res["msg"]
        assert "spanning-tree bpduguard disable" in res["msg"] and deploys(c) == []

    def test_blocked_reset_is_not_reported_as_a_deletion(self):
        running, expected = authority("G6-MR")
        lines = pending("G6-MR")[:-1] + ["  ptp", "configure terminal"]
        c = ctrl()
        c.previews = [preview(lines, running=running, expected=expected + ["  spanning-tree bpduguard disable"])]
        status, res = run(c, [{"name": IF7, "switch": ["10.0.0.1"]}], state="deleted")
        assert status == "fail" and "ALREADY changed" in res["msg"] and deploys(c) == []

    @pytest.mark.parametrize("check_mode", [False, True])
    def test_unmodeled_destination_is_refused_before_the_write(self, check_mode):
        c = ctrl()
        status, res = run(c, [trunk_item(IF7, admin_state=False, speed="10Gb")], state="replaced", check_mode=check_mode)
        assert status == "fail" and "not covered by the CLI model" in res["msg"]
        assert_no_writes(c)
