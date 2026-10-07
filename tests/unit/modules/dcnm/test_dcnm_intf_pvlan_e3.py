"""Native Ethernet PVLAN E3: the corrected behavior for architect review R2 findings R2-01/R2-02.

Every case drives the real main() through test_dcnm_intf_pvlan_harness; only external I/O is
mocked. Case IDs E3-0x follow the E3 mandate; R2 probe cases are in review/R2/probe_e2.py, which
asserted the E2 DEFECTS. Response labels: MEASURED (G5/G6 discovery capture), SYNTHETIC
(robustness counterexample built on a measured capture, NOT a claim that NDFC emits it),
TEMPLATE-PREDICTED (rendered from the pinned installed template, not measured).

R2-02 cases use transport_run(): the harness boundary WITHOUT its boolean capability mock and
without the module-level dcnm_send mock. Every request of the module and of the shared helpers
(dcnm_send, dcnm_get_bulk_api_support) reaches the fake controller through a patched
ansible.module_utils.connection.Connection, the lowest transport the collection calls.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json

from unittest.mock import patch

import pytest

from ansible.module_utils import basic
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import (
    AnsibleExitJson,
    AnsibleFailJson,
    exit_json,
    fail_json,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm import dcnm as utility

from .dcnm_module import set_module_args
from .test_dcnm_intf_pvlan_harness import (
    DEPLOY,
    FABRIC,
    FIXTURE,
    IF7,
    IF8,
    INVENTORY,
    MODIFY,
    NDFC,
    PREVIEW_MARK,
    PVLAN,
    SERIAL,
    SWITCH_IP,
    TRANSITIONS,
    TRUNK,
    FakeController,
    authority,
    measured_preview,
    module,
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
BULK_PROBE = "/top-down/v2/bulk-update/networks"
WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")
ACL = "ip access-group KEEP-IN in"  # SYNTHETIC: the architect's R2 probe command
# SYNTHETIC unowned commands for a PVLAN -> PVLAN transition. The second is a command only the
# int_trunk_host template renders (aclFilter), so it is foreign unless that policy is involved.
OTHER_UNOWNED = ("ip dhcp snooping trust", "ip port access-group FOO-IN in", "storm-control broadcast level 5.00")
NOT_OWNED = "does not own"
NOT_ROLLED_BACK = "ALREADY changed on the controller and is not rolled back"


def ctrl(nv=TPROM_A11, policy=PVLAN, ifname=IF7):
    c = FakeController()
    c.detail[ifname] = {"policy": policy, "nvPairs": copy.deepcopy(nv)}
    return c


def deploys(c):
    return c.requests("POST", DEPLOY)


def writes(c):
    return [x for x in c.calls if x[0] in WRITE_METHODS]


def with_device_line(resp, line, negate=True, ifname=IF7):
    """SYNTHETIC: add `line` to the target's runningConfig stanza and, when `negate`, its
    negation to the target's pendingConfig block (the R2 probe construction)."""
    resp = copy.deepcopy(resp)
    entry = resp["DATA"][0]

    def insert(lines, text):
        index = next(i for i, x in enumerate(lines) if x.strip().lower() == "interface " + ifname.lower())
        lines.insert(index + 1, "  " + text)

    insert(entry["runningConfig"], line)
    if negate:
        if not any(x.strip().lower() == "interface " + ifname.lower() for x in entry["pendingConfig"]):
            entry["pendingConfig"][:0] = ["interface " + ifname.lower()]
        insert(entry["pendingConfig"], "no " + line)
        entry["status"] = "Out-of-Sync"
    return resp


# ------------------------------------------------------------------ transport-boundary runner
class TransportController(FakeController):
    """The fake controller plus an answer for the bulk capability probe. bulk_probe_code=None
    answers it like any other unknown request (HTTP 200); 404 is the helper's 'absent'."""

    def __init__(self):
        super(TransportController, self).__init__()
        self.bulk_probe_code = None

    def __call__(self, mod, method, path, data=None):
        if path.endswith(BULK_PROBE) and self.bulk_probe_code is not None:
            self.calls.append((method, path, data))
            return {"RETURN_CODE": self.bulk_probe_code, "MESSAGE": "probe", "DATA": {}}
        return super(TransportController, self).__call__(mod, method, path, data)


def tctrl(nv=TPROM_A11, policy=PVLAN, ifname=IF7):
    c = TransportController()
    c.detail[ifname] = {"policy": policy, "nvPairs": copy.deepcopy(nv)}
    return c


def transport_run(ctrl_, config, state="merged", check_mode=False, check_deploy=False):
    """Real main(); the only transport mock is Connection (no capability or dcnm_send mock)."""

    class FakeConnection(object):
        def __init__(self, socket_path):
            pass

        def send_request(self, method, path, data=None):
            return ctrl_(None, method, path, data)

        send_txt_request = send_request
        send_urlencoded_request = send_request

    args = {"state": state, "fabric": FABRIC, "config": config, "check_deploy": check_deploy}
    if check_mode:
        args["_ansible_check_mode"] = True
    patches = [
        patch.object(basic.AnsibleModule, "exit_json", exit_json),
        patch.object(basic.AnsibleModule, "fail_json", fail_json),
        patch.object(module, "get_fabric_inventory_details", return_value=copy.deepcopy(INVENTORY)),
        patch.object(module, "get_ip_sn_dict", return_value=({SWITCH_IP: SERIAL}, {})),
        patch.object(module, "dcnm_get_ip_addr_info", side_effect=lambda m, sw, a, b: sw),
        patch.object(module, "dcnm_version_supported", return_value=(12, NDFC)),
        patch.object(utility, "Connection", FakeConnection),
        patch.object(module, "get_fabric_details", return_value={"nvPairs": {"HOST_INTF_ADMIN_STATE": "false"}}),
        patch.object(module.time, "sleep", return_value=None),
    ]
    assert module.dcnm_get_bulk_api_support is utility.dcnm_get_bulk_api_support
    assert module.dcnm_send is utility.dcnm_send
    for p in patches:
        p.start()
    try:
        set_module_args(args)
        try:
            module.main()
        except AnsibleExitJson as exc:
            return "exit", exc.args[0]
        except AnsibleFailJson as exc:
            return "fail", exc.args[0]
        raise AssertionError("main() returned without exit_json/fail_json")
    finally:
        for p in reversed(patches):
            p.stop()


# ===================================================================================== E3-01
class TestE301ProbeAclRemovalIsRefused:
    """R2 probe UNOWNED-device-acl-removal-accepted: ADD_2212 on MEASURED G6-M0b with the
    SYNTHETIC ACL in runningConfig and its negation in pendingConfig only."""

    @pytest.mark.parametrize("check_deploy", [False, True])
    def test_acl_removal_is_refused_with_zero_deploys(self, check_deploy):
        c = ctrl()
        c.previews = [with_device_line(measured_preview("G6-M0b"), ACL)]
        status, res = run(c, [pvlan_item(**ADD_2212)], check_deploy=check_deploy)
        assert status == "fail", res
        assert "pre-deploy gate (deploy) refused" in res["msg"]
        assert NOT_OWNED in res["msg"] and "no " + ACL in res["msg"]
        assert NOT_ROLLED_BACK in res["msg"] and IF7 + " on " + SERIAL in res["msg"]
        assert "No deployment request was sent for this batch" in res["msg"]
        assert len(c.requests("POST", MODIFY)) == 1 and deploys(c) == []

    def test_probe_controls_are_unchanged(self):
        c = ctrl()
        c.previews = [measured_preview("G6-M0b")]  # MEASURED, no synthetic line
        assert run(c, [pvlan_item(**ADD_2212)])[0] == "exit"
        assert len(deploys(c)) == 1


# ===================================================================================== E3-02
class TestE302OtherUnownedCommands:

    @pytest.mark.parametrize("line", OTHER_UNOWNED)
    def test_primary_attempt(self, line):
        c = ctrl()
        c.previews = [with_device_line(measured_preview("G6-M0b"), line)]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and NOT_OWNED in res["msg"] and "no " + line in res["msg"]
        assert NOT_ROLLED_BACK in res["msg"] and deploys(c) == []

    @pytest.mark.parametrize("line", (ACL,) + OTHER_UNOWNED)
    def test_check_deploy_resend_attempt(self, line):
        c = ctrl()
        c.previews = [measured_preview("G6-M0b"), with_device_line(measured_preview("G6-M0b"), line)]
        status, res = run(c, [pvlan_item(**ADD_2212)], check_deploy=True)
        assert status == "fail" and "gate (check_deploy_resend) refused" in res["msg"]
        assert NOT_OWNED in res["msg"] and len(deploys(c)) == 1

    @pytest.mark.parametrize("line", (ACL,) + OTHER_UNOWNED)
    def test_deployment_status_retry_attempt(self, line):
        c = ctrl()
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("G6-M0b")] * 2 + [with_device_line(measured_preview("G6-M0b"), line)]
        c.compliance = ["Out-of-Sync"] * 9 + ["In-Sync"] * 20
        status, res = run(c, [pvlan_item(**ADD_2212)], check_deploy=True)
        assert status == "fail" and "gate (deployment_status_retry) refused" in res["msg"]
        assert NOT_OWNED in res["msg"] and len(deploys(c)) == 2

    @pytest.mark.parametrize("line", (ACL,) + OTHER_UNOWNED)
    def test_untouched_unowned_device_command_creates_no_obligation(self, line):
        c = ctrl()
        c.previews = [with_device_line(measured_preview("G6-M0b"), line, negate=False)]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "exit", res
        assert len(deploys(c)) == 1

    @pytest.mark.parametrize("line", ("speed 1000", "switchport access vlan 10", "spanning-tree cost 4"))
    def test_unowned_command_in_an_owned_field_blocks_proof(self, line):
        # The device state of a field the operation owns cannot be interpreted: neither a deploy
        # nor convergence is declared, even with the measured, otherwise valid pending.
        c = ctrl()
        c.previews = [with_device_line(measured_preview("G6-M0b"), line, negate=False)]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "cannot be proven safe or converged" in res["msg"] and deploys(c) == []


# ===================================================================================== E3-03
class TestE303OwnedRemovalsStillDeploy:

    def test_measured_g6_m1_trunk_promiscuous_partial_removal(self):
        c = ctrl(TPROM_BOTH)
        c.previews = [measured_preview("G6-M1")]  # MEASURED 'mapping trunk 2210 remove 2212'
        status, res = run(c, KEEP_2211, state="replaced")
        assert status == "exit", res
        assert len(deploys(c)) == 1

    def test_measured_submode_change_withdraws_the_old_list(self):
        c = ctrl(TRANSITIONS["TS1"]["pre_nv"])
        c.previews = [measured_preview("TS1")]  # MEASURED trunk promiscuous -> trunk secondary
        status, res = run(c, TSEC_2212, state="replaced")
        assert status == "exit", res
        assert len(deploys(c)) == 1

    def test_withdrawal_of_the_policys_own_freeform_command(self):
        # The SAME synthetic ACL is owned when it is the current policy's CONF (cmds) value and
        # the request withdraws it: field ownership authorizes the negation, not device presence.
        have = copy.deepcopy(TPROM_BOTH)
        have["CONF"] = ACL
        c = ctrl(have)
        c.previews = [with_device_line(measured_preview("G6-M1"), ACL)]
        status, res = run(c, KEEP_2211, state="replaced")
        assert status == "exit", res
        assert c.sent_nv()[1]["CONF"] == "" and len(deploys(c)) == 1

    def test_unowned_removal_next_to_an_owned_partial_removal(self):
        c = ctrl(TPROM_BOTH)
        c.previews = [with_device_line(measured_preview("G6-M1"), ACL)]
        status, res = run(c, KEEP_2211, state="replaced")
        assert status == "fail" and NOT_OWNED in res["msg"] and deploys(c) == []


# ===================================================================================== E3-04
class TestE304CycleAndConvergence:

    def test_complete_convergence_with_an_untouched_unowned_command(self):
        c = ctrl(TPROM_BOTH)
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [with_device_line(measured_preview("G6-M0b", "post"), ACL, negate=False)]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "exit", res
        assert deploys(c) == [] and res["pvlan_gate"][-1]["targets"] == {IF7: "converged"}

    def test_partial_convergence_does_not_hide_an_unowned_removal(self):
        c = ctrl(TPROM_BOTH)
        c.detail[IF8] = {"policy": PVLAN, "nvPairs": pvlan_nv("G6-M0a", ifname=IF8)}
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        run7, exp7 = authority("G6-M0b", "post", IF7)
        run8, exp8 = authority("G6-M0b", "pre", IF8)
        lines = [x.replace("ethernet1/7", "ethernet1/8") for x in pending("G6-M0b")]
        resp = with_device_line(preview(lines, running=run7 + run8, expected=exp7 + exp8), ACL, ifname=IF8)
        c.previews = [resp]
        status, res = run(c, [pvlan_item(IF7, **ADD_2212), pvlan_item(IF8, **ADD_2212)])
        assert status == "fail" and NOT_OWNED in res["msg"] and IF8 + " on " in res["msg"] and deploys(c) == []

    def test_partial_convergence_still_deploys_only_the_remaining_target(self):
        c = ctrl(TPROM_BOTH)
        c.detail[IF8] = {"policy": PVLAN, "nvPairs": pvlan_nv("G6-M0a", ifname=IF8)}
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        run7, exp7 = authority("G6-M0b", "post", IF7)
        run8, exp8 = authority("G6-M0b", "pre", IF8)
        lines = [x.replace("ethernet1/7", "ethernet1/8") for x in pending("G6-M0b")]
        c.previews = [with_device_line(preview(lines, running=run7 + run8, expected=exp7 + exp8), ACL, negate=False, ifname=IF7)]
        status, res = run(c, [pvlan_item(IF7, **ADD_2212), pvlan_item(IF8, **ADD_2212)])
        assert status == "exit", res
        assert [json.loads(x[2]) for x in deploys(c)] == [[{"serialNumber": SERIAL, "ifName": IF8, "fabricName": FABRIC}]]

    def test_deploy_false_then_deploy_true_is_judged_again(self):
        c = ctrl()
        assert run(c, [pvlan_item(deploy=False, **ADD_2212)])[0] == "exit"
        c.next_invocation()
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [with_device_line(measured_preview("G6-M0b"), ACL)]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and NOT_OWNED in res["msg"]
        assert c.order() == ["MODIFY", "PREVIEW"] and deploys(c) == []
        # The second invocation wrote nothing, so it does not claim to have changed intent now.
        assert NOT_ROLLED_BACK not in res["msg"]

    def test_rerun_after_a_failed_gate_keeps_refusing_the_unowned_removal(self):
        c = ctrl(TPROM_BOTH)
        c.previews = [with_device_line(measured_preview("G6-M1"), ACL)]
        assert run(c, KEEP_2211, state="replaced")[0] == "fail"
        c.next_invocation()
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [with_device_line(measured_preview("G6-M1"), ACL)]
        status, res = run(c, KEEP_2211, state="replaced")
        assert status == "fail" and NOT_OWNED in res["msg"] and deploys(c) == []

    def test_rerun_after_a_failed_gate_deploys_the_owned_removal(self):
        c = ctrl(TPROM_BOTH)
        c.previews = [preview([])]  # no device authority: refused after the intent write
        assert run(c, KEEP_2211, state="replaced")[0] == "fail"
        c.next_invocation()
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("G6-M1")]
        status, res = run(c, KEEP_2211, state="replaced")
        assert status == "exit", res
        assert len(deploys(c)) == 1

    def test_rerun_cannot_withdraw_a_freeform_command_it_no_longer_owns(self):
        # Limitation (fail closed): the first invocation wrote CONF '' and its gate failed; on the
        # rerun no side of the requested transition holds the old cmds line any more.
        have = copy.deepcopy(TPROM_BOTH)
        have["CONF"] = ACL
        c = ctrl(have)
        c.previews = [preview([])]
        assert run(c, KEEP_2211, state="replaced")[0] == "fail"
        c.next_invocation()
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [with_device_line(measured_preview("G6-M1"), ACL)]
        status, res = run(c, KEEP_2211, state="replaced")
        assert status == "fail" and NOT_OWNED in res["msg"] and deploys(c) == []

    def test_mode_change_with_an_unowned_removal_is_refused(self):
        c = ctrl(TRANSITIONS["TS1"]["pre_nv"])
        c.previews = [with_device_line(measured_preview("TS1"), ACL)]
        status, res = run(c, TSEC_2212, state="replaced")
        assert status == "fail" and NOT_OWNED in res["msg"] and NOT_ROLLED_BACK in res["msg"] and deploys(c) == []

    def test_conversion_from_an_unmodeled_policy_is_refused_before_the_write(self):
        c = ctrl(copy.deepcopy(FIXTURE["trunk_host_baseline"]["nvPairs"]), policy="int_access_host")
        status, res = run(c, [pvlan_item(**ADD_2212)], state="replaced")
        assert status == "fail" and "int_access_host is not covered by the CLI model" in res["msg"]
        assert writes(c) == [] and c.requests(mark=PREVIEW_MARK) == []


# ===================================================================================== E3-05
class TestE305ResetAndKnownDefects:

    def test_reset_contract_is_kept(self):
        c = ctrl()
        c.previews = [reset_preview()]  # TEMPLATE-PREDICTED
        status, res = run(c, [{"name": IF7, "switch": [SWITCH_IP]}], state="deleted")
        assert status == "exit", res
        assert c.sent_nv()[0] == TRUNK and len(deploys(c)) == 1

    @pytest.mark.parametrize("line", (ACL, "ip dhcp snooping trust"))
    def test_reset_with_an_unowned_removal_is_refused_and_not_a_deletion(self, line):
        c = ctrl()
        c.previews = [with_device_line(reset_preview(), line)]
        status, res = run(c, [{"name": IF7, "switch": [SWITCH_IP]}], state="deleted")
        assert status == "fail" and NOT_OWNED in res["msg"] and NOT_ROLLED_BACK in res["msg"]
        assert deploys(c) == [] and c.sent_nv()[0] == TRUNK

    def test_measured_malformed_promiscuous_pending_is_refused(self):
        c = ctrl(TRANSITIONS["PU3"]["post_nv"])
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("PU3")]
        status, res = run(
            c, [pvlan_item(pvlan_mode="promiscuous", admin_state=False, pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2212"}])], state="replaced"
        )
        assert status == "fail" and "malformed VLAN number" in res["msg"] and deploys(c) == []

    def test_commands_outside_the_target_are_refused(self):
        running, expected = authority("G6-M0b")
        c = ctrl()
        c.previews = [preview(pending("G6-M0b") + ["interface ethernet1/9", "  shutdown"], running=running, expected=expected)]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "outside this deploy batch" in res["msg"] and deploys(c) == []

    def test_global_commands_are_refused(self):
        running, expected = authority("G6-M0b")
        c = ctrl()
        c.previews = [preview(["no ip access-list KEEP-IN"] + pending("G6-M0b"), running=running, expected=expected)]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "outside interface scope" in res["msg"] and deploys(c) == []


# ===================================================================================== E3-06
PLANNED_WRITES = {
    "add": ([pvlan_item(**ADD_2212)], "merged", TPROM_A11),
    "owned_removal": (KEEP_2211, "replaced", TPROM_BOTH),
    "mode_change": (TSEC_2212, "replaced", TRANSITIONS["TS1"]["pre_nv"]),
    "reset": ([{"name": IF7, "switch": [SWITCH_IP]}], "deleted", TPROM_A11),
}


class TestE306CheckModeTransport:

    @pytest.mark.parametrize("case", sorted(PLANNED_WRITES))
    @pytest.mark.parametrize("bulk_probe_code", [None, 404])
    def test_planned_write_is_refused_with_zero_writes(self, case, bulk_probe_code):
        config, state, nv = PLANNED_WRITES[case]
        c = tctrl(nv)
        c.bulk_probe_code = bulk_probe_code
        status, res = transport_run(c, copy.deepcopy(config), state=state, check_mode=True)
        assert status == "fail" and "could not be verified in check mode" in res["msg"], res
        assert "No configuration or deployment request was sent" in res["msg"]
        assert writes(c) == [] and c.requests(mark=BULK_PROBE) == []
        assert c.requests(mark=PREVIEW_MARK) == []  # no forced recompute

    def test_in_sync_request_needs_no_capability(self):
        c = tctrl(TPROM_BOTH)
        status, res = transport_run(c, [pvlan_item(**ADD_2212)], check_mode=True)
        assert status == "exit" and res["changed"] is False
        assert writes(c) == [] and c.requests(mark=PREVIEW_MARK) == []

    def test_deploy_only_request_succeeds_with_zero_writes_and_zero_recompute(self):
        # Intent already holds the request (no PVLAN write, so no capability is needed) but the
        # interface is Out-of-Sync: check mode reports the deploy without sending or recomputing.
        c = tctrl(TPROM_BOTH)
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        status, res = transport_run(c, [pvlan_item(**ADD_2212)], check_mode=True)
        assert status == "exit" and res["changed"] is True, res
        assert res["diff"][0]["deploy"] == [{"serialNumber": SERIAL, "ifName": IF7, "fabricName": FABRIC}]
        assert writes(c) == [] and c.requests(mark=PREVIEW_MARK) == []

    def test_invalid_second_object_is_reported_first_with_zero_writes(self):
        c = tctrl()
        bad = pvlan_item(IF8, pvlan_mode="trunk promiscuous", pvlan_mapping=[{"primary_vlan": True, "secondary_vlans": "2"}])
        status, res = transport_run(c, [pvlan_item(**ADD_2212), bad], check_mode=True)
        assert status == "fail" and "integer VLAN ID" in res["msg"]
        assert writes(c) == []

    def test_read_only_template_refusal_is_still_reported_in_check_mode(self):
        c = tctrl()
        c.read_failures = {"/configtemplate/"}
        status, res = transport_run(c, [pvlan_item(**ADD_2212)], check_mode=True)
        assert status == "fail" and "int_pvlan_host template could not be read" in res["msg"]
        assert "could not be verified in check mode" not in res["msg"] and writes(c) == []

    def test_ownership_refusal_in_check_mode_sends_nothing(self):
        c = tctrl()
        c.policies_extra = [{"entityName": IF7, "entityType": "INTERFACE", "templateName": "NA", "source": "OVERLAY", "deleted": False}]
        status, res = transport_run(c, [pvlan_item(**ADD_2212)], check_mode=True)
        assert status == "fail" and "could not be verified in check mode" not in res["msg"]
        assert writes(c) == []

    def test_non_pvlan_check_mode_is_unchanged(self):
        c = tctrl(copy.deepcopy(FIXTURE["trunk_host_baseline"]["nvPairs"]), policy=TRUNK, ifname=IF8)
        status, res = transport_run(c, [trunk_item(IF8, description="e3")], state="replaced", check_mode=True)
        assert status == "exit" and res["changed"] is True
        assert writes(c) == []


# ===================================================================================== E3-07
class TestE307NormalExecutionRegressions:

    @pytest.mark.parametrize("bulk_probe_code", [None, 405])
    def test_capability_present(self, bulk_probe_code):
        c = tctrl()
        c.bulk_probe_code = bulk_probe_code
        c.previews = [measured_preview("G6-M0b")]
        status, res = transport_run(c, [pvlan_item(**ADD_2212)])
        assert status == "exit", res
        kinds = [("PROBE" if p.endswith(BULK_PROBE) else "MODIFY" if p.endswith(MODIFY) else "DEPLOY" if p.endswith(DEPLOY) else p) for m, p, _d in writes(c)]
        assert kinds == ["PROBE", "MODIFY", "DEPLOY"]

    def test_capability_absent_is_refused_before_any_write(self):
        c = tctrl()
        c.bulk_probe_code = 404
        status, res = transport_run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "bulk interface update API, which is not available" in res["msg"]
        assert [p for _m, p, _d in writes(c)] == [x[1] for x in c.requests(mark=BULK_PROBE)]  # only the probe
        assert len(c.requests(mark=BULK_PROBE)) == 1 and c.requests(mark=PREVIEW_MARK) == []

    @pytest.mark.parametrize("bulk_probe_code", [None, 404])
    def test_non_pvlan_normal_execution_is_unchanged(self, bulk_probe_code):
        c = tctrl(copy.deepcopy(FIXTURE["trunk_host_baseline"]["nvPairs"]), policy=TRUNK, ifname=IF8)
        c.bulk_probe_code = bulk_probe_code
        status, res = transport_run(c, [trunk_item(IF8, deploy=False, description="e3")], state="replaced")
        assert status == "exit", res
        paths = [p for _m, p, _d in writes(c)]
        assert len([p for p in paths if p.endswith(BULK_PROBE)]) == 1
        assert c.requests(mark=PREVIEW_MARK) == [] and deploys(c) == []


# ===================================================================================== E3-08
class TestE308AuthorityControls:

    @pytest.mark.parametrize("check_mode", [False, True])
    def test_invalid_metadata_is_refused_before_writes(self, check_mode):
        c = tctrl()
        c.summary[IF7] = {"underlayPolicies": [{"source": "OVERLAY", "templateName": PVLAN}]}
        status, res = transport_run(c, [pvlan_item(**ADD_2212)], check_mode=check_mode)
        assert status == "fail" and "No configuration or deployment request was sent" in res["msg"]
        assert writes(c) == []

    @pytest.mark.parametrize("check_mode", [False, True])
    def test_invalid_second_object_is_refused_before_writes(self, check_mode):
        c = tctrl()
        bad = pvlan_item(IF8, pvlan_mode="trunk promiscuous", pvlan_mapping=[{"primary_vlan": True, "secondary_vlans": "2"}])
        status, res = transport_run(c, [pvlan_item(**ADD_2212), bad], check_mode=check_mode)
        assert status == "fail" and "integer VLAN ID" in res["msg"]
        assert writes(c) == []

    def test_controller_expectation_with_an_unowned_command_is_refused(self):
        # SYNTHETIC: the controller expects (and the device holds) a command outside the modeled
        # contract; the owned lines alone would agree, so this proves expectedConfig is read whole.
        c = ctrl()
        p = with_device_line(measured_preview("G6-M0b"), ACL, negate=False)
        stanza = p["DATA"][0]["expectedConfig"]
        stanza.insert(next(i for i, x in enumerate(stanza) if x.strip().lower() == "interface " + IF7.lower()) + 1, "  " + ACL)
        c.previews = [p]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "outside the modeled contract" in res["msg"] and deploys(c) == []

    @pytest.mark.parametrize(
        "defect",
        [
            ("runningConfig", [None]),
            ("runningConfig", "interface ethernet1/7"),
            ("expectedConfig", [7]),
            ("status", "Pending"),
            ("pendingConfig", None),
        ],
    )
    def test_malformed_preview_sends_no_deploy(self, defect):
        key, value = defect
        c = ctrl()
        p = measured_preview("G6-M0b")
        p["DATA"][0][key] = value
        c.previews = [p]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and NOT_ROLLED_BACK in res["msg"]
        assert len(c.requests("POST", MODIFY)) == 1 and deploys(c) == []
