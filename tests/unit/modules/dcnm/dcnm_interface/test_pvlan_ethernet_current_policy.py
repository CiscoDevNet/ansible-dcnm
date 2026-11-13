"""Native Ethernet PVLAN: current-policy resolution from the summary, the detail and a new read."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import ast
import contextlib
import copy
import functools
import inspect
import json
import pytest

from unittest.mock import patch
from ansible.module_utils import basic
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import AnsibleExitJson
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import AnsibleFailJson
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import exit_json
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import fail_json
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm import dcnm as utility
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module
from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from ..dcnm_module import set_module_args
from .helpers.ethernet_controller import DEPLOY
from .helpers.ethernet_controller import FABRIC
from .helpers.ethernet_controller import FIXTURE
from .helpers.ethernet_controller import IF7
from .helpers.ethernet_controller import IF8
from .helpers.ethernet_controller import INVENTORY
from .helpers.ethernet_controller import MODIFY
from .helpers.ethernet_controller import NDFC
from .helpers.ethernet_controller import PREVIEW_MARK
from .helpers.ethernet_controller import PVLAN
from .helpers.ethernet_controller import SERIAL
from .helpers.ethernet_controller import SWITCH_IP
from .helpers.ethernet_controller import TRANSITIONS
from .helpers.ethernet_controller import TRUNK
from .helpers.ethernet_controller import FakeController
from .helpers.ethernet_controller import authority
from .helpers.ethernet_controller import measured_preview
from .helpers.ethernet_controller import pending
from .helpers.ethernet_controller import preview
from .helpers.ethernet_controller import pvlan_item
from .helpers.ethernet_controller import pvlan_nv
from .helpers.ethernet_controller import reset_preview
from .helpers.ethernet_controller import run
from .helpers.ethernet_controller import trunk_item
from .helpers.ethernet_controller import DEVICE
from .helpers.ethernet_controller import OVERLAY_PROFILE
from .helpers.ethernet_controller import DELETE
from .helpers.ethernet_controller import ok
from .helpers.ethernet_controller import trunk_host_nv
from .helpers.fixture_cases import load_case


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_e3.py
# Native Ethernet PVLAN: corrected behavior for the second review's findings.
#
# Every case drives the real main() through helpers/ethernet_controller; only external I/O is mocked. Response labels:
# MEASURED (discovery capture), SYNTHETIC (robustness counterexample built on a measured capture, NOT a claim that NDFC emits
# it), TEMPLATE-PREDICTED (rendered from the pinned installed template, not measured).
#
# The transport cases use transport_run(): the harness boundary WITHOUT its boolean capability mock and without the
# module-level dcnm_send mock. Every request of the module and of the shared helpers (dcnm_send, dcnm_get_bulk_api_support)
# reaches the fake controller through a patched ansible.module_utils.connection.Connection, the lowest transport the
# collection calls.
# ====================================================================================================
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
ACL = "ip access-group KEEP-IN in"  # SYNTHETIC: a review probe command
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
    negation to the target's pendingConfig block (the review probe construction)."""
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


# The real communication helpers, taken when this module is imported, before any test can patch them.
TRANSPORT_HELPERS = ("dcnm_send", "dcnm_get_bulk_api_support")
REAL_HELPERS = dict((name, getattr(utility, name)) for name in TRANSPORT_HELPERS)


def assert_real_helpers(owner):
    """Fail unless owner binds the helpers defined in module_utils/network/dcnm/dcnm.py."""
    for name, helper in REAL_HELPERS.items():
        code = getattr(helper, "__code__", None)
        assert code is not None and code.co_filename == utility.__file__ and code.co_name == name, (
            "%s taken at import is not the helper defined in %s" % (name, utility.__name__))
        assert getattr(owner, name) is helper, "%s.%s is not the real helper from %s" % (
            owner.__name__.rsplit(".", 1)[-1], name, utility.__name__)


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
        # The shared helpers call utility.dcnm_send. Pin the real functions, so a patch that another test module
        # never undid cannot replace the transport these cases exercise.
        patch.object(utility, "dcnm_send", REAL_HELPERS["dcnm_send"]),
        patch.object(utility, "dcnm_get_bulk_api_support", REAL_HELPERS["dcnm_get_bulk_api_support"]),
    ]
    assert_real_helpers(module)
    for p in patches:
        p.start()
    try:
        assert_real_helpers(utility)  # the pins above took effect
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
    """Probe UNOWNED-device-acl-removal-accepted: ADD_2212 on a MEASURED preview with the
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

    @pytest.mark.parametrize("line", ("switchport access vlan 10", "spanning-tree cost 4"))
    def test_unowned_command_in_an_owned_field_blocks_proof(self, line):
        # The device state of a field the operation owns cannot be interpreted: neither a deploy
        # nor convergence is declared, even with the measured, otherwise valid pending.
        c = ctrl()
        c.previews = [with_device_line(measured_preview("G6-M0b"), line, negate=False)]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "cannot be proven safe or converged" in res["msg"] and deploys(c) == []

    def test_a_device_speed_line_is_owned_and_its_withdrawal_must_be_in_the_pending(self):
        # RC1: `speed <n>` is a line int_pvlan_host renders, so the operation owns it. On a device whose intent is Auto, the measured
        # pending that does not withdraw it is still refused before any deploy, now with the precise reason.
        c = ctrl()
        c.previews = [with_device_line(measured_preview("G6-M0b"), "speed 1000", negate=False)]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "withdrawal of 'speed 1000' is absent from the pending" in res["msg"] and deploys(c) == []


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


# ===================================================================================== E3-09
# Everything transport_run() patches; none of it may stay changed after a run or a refusal.
TRANSPORT_RUN_TARGETS = (
    (basic.AnsibleModule, "exit_json"), (basic.AnsibleModule, "fail_json"), (module, "get_fabric_inventory_details"),
    (module, "get_ip_sn_dict"), (module, "dcnm_get_ip_addr_info"), (module, "dcnm_version_supported"),
    (utility, "Connection"), (module, "get_fabric_details"), (module.time, "sleep"),
    (utility, "dcnm_send"), (utility, "dcnm_get_bulk_api_support"),
)


def transport_run_state():
    return [getattr(owner, name) for owner, name in TRANSPORT_RUN_TARGETS]


def same_objects(left, right):
    return len(left) == len(right) and all(a is b for a, b in zip(left, right))


class TestE309RealHelperGuard:
    """transport_run() refuses a substitute in the module's own helper binding before main() or Connection runs."""

    @staticmethod
    def stand_in(name):
        # Delegates to the real helper and copies its name and module, so only the guard can tell it apart.
        real = REAL_HELPERS[name]

        @functools.wraps(real)
        def substitute(*args, **kwargs):
            return real(*args, **kwargs)
        return substitute

    @pytest.mark.parametrize("utility_too", [False, True], ids=["module_binding", "module_and_utility_bindings"])
    @pytest.mark.parametrize("name", TRANSPORT_HELPERS)
    def test_substituted_helper_is_refused_before_main(self, name, utility_too):
        c = tctrl()
        c.previews = [measured_preview("G6-M0b")]
        substitute = self.stand_in(name)
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(module, name, substitute))
            if utility_too:
                stack.enter_context(patch.object(utility, name, substitute))
            main = stack.enter_context(patch.object(module, "main"))
            before = transport_run_state()
            with pytest.raises(AssertionError, match=r"dcnm_interface\.%s is not the real helper from " % name):
                transport_run(c, [pvlan_item(**ADD_2212)])
            assert main.call_count == 0 and c.calls == []
            assert same_objects(transport_run_state(), before)

    def test_real_helpers_reach_the_controller_through_connection(self):
        c = tctrl()
        c.previews = [measured_preview("G6-M0b")]
        before = transport_run_state()
        status, res = transport_run(c, [pvlan_item(**ADD_2212)])
        assert status == "exit", res
        assert len(c.requests(mark=BULK_PROBE)) == 1 and len(c.requests("POST", MODIFY)) == 1 and len(deploys(c)) == 1
        assert same_objects(transport_run_state(), before)


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_e3_units.py
# Helper-level and static checks (they do not replace the real-main cases in test_pvlan_ethernet_current_policy.py).
#
# Helper: the owned vocabulary, the observed/owned/foreign split, and a sweep over EVERY measured discovery preview with device
# authority: each keeps its earlier decision under the transition's vocabulary; adding a SYNTHETIC negation of an unowned device
# command turns every one into a refusal; adding the unowned command untouched never changes the decision (no obligation).
# Static: the gate passes the transition vocabulary, and the check-mode branch of the PVLAN preflight is decided before the
# capability probe can be evaluated.
#
# On a helper without the vocabulary API assess() falls back to the older signature, so the sweep compares behavior rather than
# failing at import.
# ====================================================================================================
VOCAB = getattr(P, "transition_vocabulary", None)
UNOWNED = (ACL, "ip dhcp snooping trust")


def assess(body, entry, desired, pre, post):
    if VOCAB is None:
        return P.assess_target(body, entry, "Ethernet1/7", desired)
    return P.assess_target(body, entry, "Ethernet1/7", desired, VOCAB(pre, post))


def entry(phase, extra_running=None):
    running = list(phase["running_stanza"])
    if extra_running:
        running.insert(1, "  " + extra_running)
    return {"runningConfig": running, "expectedConfig": phase["expected_stanza"]}


def body(phase):
    return P.split_blocks(phase["pendingConfig"])[0].get("ethernet1/7", [])


def sides(t):
    return (t["pre_policy"], t["pre_nv"]), (t["post_policy"], t["post_nv"])


PRE_CASES = sorted(c for c in TRANSITIONS if c in DEVICE)
POST_CASES = sorted(c for c in TRANSITIONS if c in DEVICE and "post" in DEVICE[c] and c != "PU3")


# ------------------------------------------------------------------ measured sweep
@pytest.mark.parametrize("case", PRE_CASES)
def test_measured_pre_deploy_decision_is_kept(case):
    t = TRANSITIONS[case]
    pre, post = sides(t)
    decision, problems = assess(body(DEVICE[case]["pre"]), entry(DEVICE[case]["pre"]), P.render(*post), pre, post)
    assert decision == ("refuse" if t["expect"] == "reject" else "deploy"), problems


@pytest.mark.parametrize("line", UNOWNED)
@pytest.mark.parametrize("case", [c for c in PRE_CASES if TRANSITIONS[c]["expect"] != "reject"])
def test_unowned_negation_turns_every_measured_transition_into_a_refusal(case, line):
    t = TRANSITIONS[case]
    pre, post = sides(t)
    decision, problems = assess(body(DEVICE[case]["pre"]) + ["no " + line], entry(DEVICE[case]["pre"], line), P.render(*post), pre, post)
    assert decision == "refuse" and any("does not own" in p for p in problems), problems


@pytest.mark.parametrize("line", UNOWNED)
@pytest.mark.parametrize("case", [c for c in PRE_CASES if TRANSITIONS[c]["expect"] != "reject"])
def test_untouched_unowned_command_keeps_the_measured_decision(case, line):
    t = TRANSITIONS[case]
    pre, post = sides(t)
    decision, problems = assess(body(DEVICE[case]["pre"]), entry(DEVICE[case]["pre"], line), P.render(*post), pre, post)
    assert decision == "deploy", problems


@pytest.mark.parametrize("line", UNOWNED)
@pytest.mark.parametrize("case", POST_CASES)
def test_measured_convergence_survives_an_untouched_unowned_command(case, line):
    t = TRANSITIONS[case]
    pre, post = sides(t)
    assert assess([], entry(DEVICE[case]["post"], line), P.render(*post), pre, post) == ("converged", [])


# ------------------------------------------------------------------ vocabulary and model
def test_vocabulary_owns_only_the_transition_policies():
    pvlan = P.transition_vocabulary((P.PVLAN_POLICY, {}), (P.PVLAN_POLICY, {}))
    reset = P.transition_vocabulary((P.PVLAN_POLICY, {}), (P.TRUNK_HOST_POLICY, {}))
    for line in ("switchport private-vlan mapping trunk 2210 2211", "switchport mode private-vlan host", "mtu 9216", "shutdown"):
        assert pvlan.owns(line) and reset.owns(line)
    for line in ("switchport mode trunk", "switchport trunk allowed vlan none", "ip port access-group FOO in"):
        assert not pvlan.owns(line) and reset.owns(line)
    for line in (ACL, "ip dhcp snooping trust", "no ip access-group KEEP-IN in"):
        assert not pvlan.owns(line) and not reset.owns(line)


def test_unmodeled_policy_contributes_nothing():
    v = P.transition_vocabulary(("int_access_host", {"CONF": ACL}), (P.PVLAN_POLICY, {}))
    assert not v.owns("switchport mode access") and not v.owns(ACL) and v.interferes("switchport access vlan 10")


def test_freeform_lines_are_owned_only_from_either_side_conf():
    v = P.transition_vocabulary((P.PVLAN_POLICY, {"CONF": ACL + "\n ip dhcp snooping trust "}), (P.PVLAN_POLICY, {"CONF": ""}))
    assert v.owns(ACL) and v.owns("ip dhcp snooping trust") and not v.owns("ip verify unicast source reachable-via rx")


def test_interference_is_namespace_based():
    v = P.transition_vocabulary((P.PVLAN_POLICY, {}), (P.PVLAN_POLICY, {}))
    for line in ("speed 1000", "switchport access vlan 10", "spanning-tree cost 4", "no lldp transmit-tlv", "service-policy input X"):
        assert v.interferes(line)
    for line in (ACL, "ip dhcp snooping trust", "storm-control broadcast level 5.00", "ip port access-group FOO in", "switchportx"):
        assert not v.interferes(line)


def test_cli_model_separates_observed_owned_and_foreign():
    v = P.transition_vocabulary((P.PVLAN_POLICY, {}), (P.PVLAN_POLICY, {}))
    m = P.cli_model(["mtu 9216", ACL, "switchport mode private-vlan trunk promiscuous", "switchport private-vlan mapping trunk 2210 2211"], v)
    assert m.foreign == {ACL} and ACL not in m.scalars
    assert m.pairs == {(2210, 2211)} and {"mtu 9216", "switchport", "no shutdown"} <= m.scalars


def test_foreign_pre_line_is_never_removable_and_never_required():
    v = P.transition_vocabulary((P.PVLAN_POLICY, {}), (P.PVLAN_POLICY, {}))
    pre = P.cli_model(["switchport mode private-vlan host", "switchport private-vlan host-association 2210 2211", ACL], v)
    post = P.cli_model(["switchport mode private-vlan host", "switchport private-vlan host-association 2210 2211", "description x"], v)
    assert P.validate_transition(["description x"], pre, post) == []  # the ACL is not an obligation
    problems = P.validate_transition(["no " + ACL], pre, post)
    assert problems and "does not own" in problems[0]


def test_owned_withdrawals_are_still_required_and_allowed():
    v = P.transition_vocabulary((P.PVLAN_POLICY, {"DESC": "old"}), (P.PVLAN_POLICY, {}))
    pre = P.cli_model(["switchport mode private-vlan host", "description old"], v)
    post = P.cli_model(["switchport mode private-vlan host"], v)
    assert P.validate_transition(["no description old"], pre, post) == []
    assert P.validate_transition(["shutdown"], pre, post) != []  # the owned withdrawal is missing


def test_model_default_has_no_foreign_lines():
    assert P.render(P.PVLAN_POLICY, TRANSITIONS["G6-M1"]["post_nv"]).foreign == set()


# ------------------------------------------------------------------ static checks
def _source(func):
    return inspect.getsource(func)


def test_static_gate_passes_the_transition_vocabulary():
    tree = ast.parse(inspect.cleandoc("\n" + _source(module.DcnmIntf.dcnm_intf_pvlan_deploy_gate)))
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "pvlan_assess_target"]
    assert len(calls) == 1 and len(calls[0].args) == 5
    vocab = calls[0].args[4]
    assert isinstance(vocab, ast.Call) and vocab.func.id == "pvlan_transition_vocabulary"


def test_static_check_mode_is_decided_before_the_capability_probe():
    src = _source(module.DcnmIntf.dcnm_intf_pvlan_preflight)
    assert src.count("self.has_bulk_api") == 1
    assert src.index("if self.module.check_mode:") < src.index("self.has_bulk_api")
    assert src.index("elif not self.has_bulk_api") > src.index("could not be verified in check mode")


def test_static_shared_bulk_helper_is_the_post_probe():
    src = inspect.getsource(module.dcnm_get_bulk_api_support)
    assert 'method = "POST"' in src and "bulk-update/networks" in src


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_e4.py
# Current-policy interpretation of the MEASURED interface summary for native Ethernet PVLAN.
#
# MEASURED (NDFC 12.6.0.267): interface/detail carries no top-level `policy`; the policy identity is the single nested
# `underlayPolicies` object. Reading the top-level key refused every valid PVLAN merge on that shape and silently skipped the
# PVLAN gate for a `deleted` reset. These tests drive the real main() (harness default = measured shape) and the real
# pre-state method against verbatim entries.
# ====================================================================================================
MEASURED = load_case("dcnm_intf_pvlan_summary_measured")["entries"]
IF3 = "Ethernet1/3"
ETH_SUMMARY_ADD_2212 = dict(pvlan_mode="trunk promiscuous", pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2212"}])
NO_WRITE = "No configuration or deployment request was sent"
DEFECT_FRAGMENT = {
    "top_contradiction": "contradicts the underlay policy",
    "policy_id": "switch policy id",
    "entity": "targets Ethernet1/8",
    "serial": "on OTHER",
    "entity_type": "attached to a SWITCH",
    "null": "lists no underlay policy",
    "two": "lists 2 underlay policies",
    "missing_id": "lacks policyId",
    "source_overlay": "owned by another resource (source OVERLAY)",
}


def eth_summary_ctrl(nv=None, policy=PVLAN, ifname=IF7):
    c = FakeController()
    c.detail[ifname] = {"policy": policy, "nvPairs": copy.deepcopy(nv if nv is not None else pvlan_nv("G6-M0a", ifname=ifname))}
    return c


def each_deploy_follows_a_preview(c):
    kinds = ["P" if PREVIEW_MARK in p else "D" if p.endswith(DEPLOY) else "" for _m, p, _b in c.calls]
    kinds = [k for k in kinds if k]
    return all(i > 0 and kinds[i - 1] == "P" for i, k in enumerate(kinds) if k == "D")


def under(c, ifname=IF7, **changes):
    """The harness's measured-shape underlay object for `ifname`, with `changes` (DELETE removes a key)."""
    index = sorted(c.detail).index(ifname)
    u = {
        "source": "",
        "templateName": c.detail[ifname]["policy"],
        "policyId": c._policy_id(index),
        "entityName": ifname,
        "entityType": "INTERFACE",
        "serialNumber": SERIAL,
    }
    for key, value in changes.items():
        if value is DELETE:
            u.pop(key)
        else:
            u[key] = value
    return u


# ===================================================================================== helper units
class TestSummaryPolicyOnMeasuredEntries:

    def test_verbatim_entries(self):
        state, value = P.summary_policy(MEASURED[IF7], IF7)
        assert state == P.SUMMARY_KNOWN and value["templateName"] == TRUNK and value["policyId"] == "POLICY-174760" and value["source"] == ""
        state, value = P.summary_policy(MEASURED[IF3], IF3)
        assert state == P.SUMMARY_KNOWN and value["templateName"] == PVLAN and value["policyId"] == "POLICY-175820"
        assert P.summary_policy(MEASURED["Vlan1"], "Vlan1") == (P.SUMMARY_ABSENT, None)
        assert all("policy" not in e for e in MEASURED.values())  # the measured shape itself

    @pytest.mark.parametrize(
        "mutate,fragment",
        [
            (lambda e: e.pop("underlayPolicies"), "no underlay policy list (absent)"),
            (lambda e: e.__setitem__("underlayPolicies", e["underlayPolicies"][0]), "no underlay policy list (dict)"),
            (lambda e: e.__setitem__("underlayPolicies", e["underlayPolicies"] * 2), "lists 2 underlay policies"),
            (lambda e: e.__setitem__("underlayPolicies", [""]), "lists 1 underlay policies"),
            (lambda e: e["underlayPolicies"][0].pop("policyId"), "lacks policyId"),
            (lambda e: e["underlayPolicies"][0].__setitem__("policyId", ""), "lacks policyId"),
            (lambda e: e["underlayPolicies"][0].__setitem__("templateName", None), "lacks templateName"),
            (lambda e: e["underlayPolicies"][0].pop("source"), "no source string"),
            (lambda e: e["underlayPolicies"][0].__setitem__("entityName", IF8), "targets Ethernet1/8"),
            (lambda e: e["underlayPolicies"][0].__setitem__("serialNumber", "OTHER"), "targets Ethernet1/3 on OTHER"),
            (lambda e: e["underlayPolicies"][0].__setitem__("entityType", "SWITCH"), "attached to a SWITCH"),
            (lambda e: e.__setitem__("policy", TRUNK), "contradicts the underlay policy"),
        ],
    )
    def test_unknown_is_never_a_policy(self, mutate, fragment):
        entry = copy.deepcopy(MEASURED[IF3])
        mutate(entry)
        state, reason = P.summary_policy(entry, IF3)
        assert state == P.SUMMARY_UNKNOWN and fragment in reason, reason

    def test_consistent_top_level_policy_is_accepted(self):
        entry = dict(copy.deepcopy(MEASURED[IF3]), policy=PVLAN)
        assert P.summary_policy(entry, IF3)[0] == P.SUMMARY_KNOWN

    def test_top_level_policy_without_underlay_is_a_contradiction(self):
        entry = dict(copy.deepcopy(MEASURED["Vlan1"]), policy="int_vlan")
        assert P.summary_policy(entry, "Vlan1")[0] == P.SUMMARY_UNKNOWN

    def test_foreign_source_is_reported(self):
        entry = copy.deepcopy(MEASURED[IF3])
        entry["underlayPolicies"][0]["source"] = "OVERLAY"
        assert P.summary_policy(entry, IF3)[1]["source"] == "OVERLAY"
        entry["underlayPolicies"][0].pop("policyId")
        assert P.summary_policy(entry, IF3) == (P.SUMMARY_UNKNOWN, "its policy is owned by another resource (source OVERLAY)")

    def test_mentions_policy_reads_every_field(self):
        assert P.summary_mentions_policy(MEASURED[IF3], PVLAN) and not P.summary_mentions_policy(MEASURED[IF7], PVLAN)
        assert P.summary_mentions_policy({"underlayPolicies": {"templateName": PVLAN}}, PVLAN)
        assert P.summary_mentions_policy({"policy": PVLAN, "underlayPolicies": None}, PVLAN)
        assert not P.summary_mentions_policy(None, PVLAN)


# ===================================================================================== pre-state units (real method)
class PreStateDouble(object):
    """Only the state the real dcnm_intf_pvlan_pre_state reads; every read it makes is recorded."""

    _dcnm_intf_authority_key = module.DcnmIntf._dcnm_intf_authority_key
    PVLAN_PHYSICAL_ETHERNET_NAME = getattr(module.DcnmIntf, "PVLAN_PHYSICAL_ETHERNET_NAME", None)  # absent on older code; lets that replay import

    def __init__(self, entry, detail="absent", summary_ok=True):
        self.have = []
        self.have_all = [entry] if entry is not None else []
        self.have_all_cached_snos = {SERIAL} if summary_ok else set()
        self.have_all_failed_snos = set() if summary_ok else {SERIAL}
        self.detail = detail  # "absent", "failed" or (policy, nvPairs)
        self.reads = []
        self.intf_detail_cache = {}  # nothing read yet in this invocation unless a test says so
        self.intf_detail_authoritative_absent_keys = set()
        self.intf_detail_cached_snos = set()

    def dcnm_intf_get_have_all_with_sno(self, sno):
        self.reads.append("summary")
        return False

    def dcnm_intf_bulk_fetch_intf_info(self, sno):
        self.reads.append("detail")

    def dcnm_intf_detail_unavailable(self, name, sno):
        return self.detail == "failed"

    def dcnm_intf_get_intf_info(self, name, sno, if_type):
        if self.detail == "absent":
            return []
        return {"policy": self.detail[0], "interfaces": [{"ifName": name, "serialNumber": sno, "nvPairs": copy.deepcopy(self.detail[1])}]}

    def pre(self, name):
        return module.DcnmIntf.dcnm_intf_pvlan_pre_state(self, name, SERIAL)


def entry_for(name, template=None, base=IF3, **changes):
    e = copy.deepcopy(MEASURED[base])
    e["ifName"] = name
    e["underlayPolicies"][0]["entityName"] = name
    if template:
        e["underlayPolicies"][0]["templateName"] = template
    e.update(changes)
    return e


class TestPreStateResolution:

    def test_known_pvlan_needs_the_detail_and_returns_its_nvpairs(self):
        d = PreStateDouble(entry_for(IF7), detail=(PVLAN, {"PVLAN_MODE": "host"}))
        assert d.pre(IF7) == ("known", PVLAN, {"PVLAN_MODE": "host"}) and d.reads == ["detail"]

    def test_known_non_pvlan_is_preserved_even_without_the_detail(self):
        for detail in ("absent", "failed", (TRUNK, {})):
            d = PreStateDouble(entry_for(IF7, TRUNK), detail=detail)
            assert d.pre(IF7) == ("known", TRUNK, None)

    def test_known_trunk_summary_with_pvlan_detail_is_a_pvlan_target(self):
        # The caller's ownership check then refuses the disagreement; it is never skipped.
        d = PreStateDouble(entry_for(IF7, TRUNK), detail=(PVLAN, {"PVLAN_MODE": "host"}))
        assert d.pre(IF7)[:2] == ("known", PVLAN)

    def test_policy_less_svi_is_not_a_target_without_any_read(self):
        d = PreStateDouble(copy.deepcopy(MEASURED["Vlan1"]))
        assert d.pre("Vlan1") == ("known", None, None) and d.reads == []

    @pytest.mark.parametrize(
        "name,sno", [("port-channel300", SERIAL), ("Loopback200", SERIAL), ("Ethernet1/3.2", SERIAL), ("vlan2001", SERIAL), ("vPC150", "FOX1821H035~" + SERIAL)]
    )
    def test_non_physical_ethernet_identities_are_never_targets(self, name, sno):
        d = PreStateDouble(None, summary_ok=False)
        assert module.DcnmIntf.dcnm_intf_pvlan_pre_state(d, name, sno) == ("known", None, None) and d.reads == []

    @pytest.mark.parametrize(
        "entry", [entry_for(IF7, ifType="INTERFACE_PORT_CHANNEL"), entry_for(IF7, isPhysical="false")], ids=["port-channel-type", "not-physical"]
    )
    def test_type_fields_exclude_pvlan_when_no_field_names_it(self, entry):
        entry["underlayPolicies"] = [{"source": ""}]  # unreadable identity, but never int_pvlan_host
        d = PreStateDouble(entry)
        # the type exclusion is judged after the detail is resolved (one bulk read per
        # switch), so that a known PVLAN detail can never be hidden; the earlier expectation was reads == [].
        assert d.pre(IF7) == ("known", None, None) and d.reads == ["detail"]

    def test_type_fields_do_not_hide_a_named_pvlan_policy(self):
        d = PreStateDouble(entry_for(IF7, isPhysical="false"), detail=(PVLAN, {"PVLAN_MODE": "host"}))
        # a PVLAN detail against a non-physical summary is a type/policy contradiction,
        # "unknown" (refused before any write). The earlier expectation was ("known", PVLAN), refused later by
        # the ownership check; both send nothing, and it is now refused at registration for every detail origin.
        state, reason, _nv = d.pre(IF7)
        assert state == "unknown" and "not a physical Ethernet" in reason

    @pytest.mark.parametrize("detail,expected", [("absent", ("absent", None, None)), ((TRUNK, {}), ("known", TRUNK, None))])
    def test_physical_port_without_underlay_is_resolved_by_the_detail(self, detail, expected):
        d = PreStateDouble(entry_for(IF7, underlayPolicies=None), detail=detail)
        assert d.pre(IF7) == expected and d.reads == ["detail"]

    @pytest.mark.parametrize(
        "entry,detail",
        [
            (entry_for(IF7, underlayPolicies=[{"source": "", "templateName": PVLAN}]), (TRUNK, {})),  # names PVLAN, detail disagrees
            (entry_for(IF7, underlayPolicies=[{"source": "", "templateName": PVLAN}]), "failed"),
            (entry_for(IF7, underlayPolicies="garbage"), "failed"),
            (entry_for(IF7, underlayPolicies="garbage"), "absent"),
            (entry_for(IF7, underlayPolicies=None), "failed"),
            (entry_for(IF7, policy=PVLAN, underlayPolicies=None), (TRUNK, {})),
        ],
        ids=[
            "pvlan-named-detail-trunk",
            "pvlan-named-detail-failed",
            "garbage-detail-failed",
            "garbage-detail-absent",
            "absent-detail-failed",
            "top-pvlan-detail-trunk",
        ],
    )
    def test_unresolved_or_contradictory_state_is_unknown(self, entry, detail):
        d = PreStateDouble(entry, detail=detail)
        state, reason, nv = d.pre(IF7)
        assert state == "unknown" and isinstance(reason, str) and nv is None, (state, reason)

    def test_garbage_summary_with_a_positive_non_pvlan_detail_is_that_policy(self):
        d = PreStateDouble(entry_for(IF7, underlayPolicies="garbage"), detail=(TRUNK, {}))
        assert d.pre(IF7) == ("known", TRUNK, None)

    def test_detail_already_read_in_this_invocation_is_authoritative(self):
        d = PreStateDouble(None, summary_ok=False)
        d.intf_detail_cache[(SERIAL, IF7.lower())] = {"policy": PVLAN, "interfaces": [{"nvPairs": {"PVLAN_MODE": "host"}}]}
        assert d.pre(IF7) == ("known", PVLAN, {"PVLAN_MODE": "host"}) and d.reads == []
        d.intf_detail_cache[(SERIAL, IF7.lower())] = {"policy": TRUNK, "interfaces": [{"nvPairs": {}}]}
        assert d.pre(IF7) == ("known", TRUNK, None)

    def test_authoritative_detail_absence_is_a_creation_not_a_reset(self):
        d = PreStateDouble(None, summary_ok=False)
        d.intf_detail_authoritative_absent_keys.add((SERIAL, IF7.lower()))
        assert d.pre(IF7) == ("absent", None, None) and d.reads == []

    def test_unreadable_summary_is_unknown_and_not_absent(self):
        # The detail is now always resolved, and an already failed summary is not
        # re-read per interface. Both authorities unreadable stays "unknown"; an
        # authoritative detail absence with an unreadable summary is covered in test_pvlan_ethernet_current_policy.
        d = PreStateDouble(None, summary_ok=False, detail="failed")
        assert d.pre(IF7)[0] == "unknown" and d.reads == []  # neither authority is re-read

    def test_interface_missing_from_an_authoritative_summary_is_absent(self):
        assert PreStateDouble(None).pre(IF7) == ("absent", None, None)

    def test_two_summary_entries_are_unknown(self):
        d = PreStateDouble(entry_for(IF7))
        d.have_all.append(entry_for(IF7))
        assert d.pre(IF7)[0] == "unknown"


# ===================================================================================== real main(), measured shape
class TestMergedOnTheMeasuredShape:

    def test_verbatim_summary_entry_valid_merge_passes_its_gate(self):
        c = eth_summary_ctrl(ifname=IF3)
        c.summary[IF3] = copy.deepcopy(MEASURED[IF3])  # verbatim (sanitized) measured entry
        c.policies_override = ok(
            [
                {
                    "entityName": IF3,
                    "entityType": "INTERFACE",
                    "templateName": PVLAN,
                    "source": "",
                    "deleted": False,
                    "policyId": "POLICY-175820",
                    "priority": 500,
                    "serialNumber": SERIAL,
                }
            ]
        )
        c.previews = [measured_preview("G6-M0b", ifname=IF3)]
        status, res = run(c, [pvlan_item(IF3, **ETH_SUMMARY_ADD_2212)])
        assert status == "exit", res
        assert c.order() == ["MODIFY", "PREVIEW", "DEPLOY"] and each_deploy_follows_a_preview(c)

    def test_harness_default_is_the_measured_shape(self):
        c = eth_summary_ctrl()
        c.previews = [measured_preview("G6-M0b")]
        status, res = run(c, [pvlan_item(**ETH_SUMMARY_ADD_2212)])
        assert status == "exit", res
        summary = [r for r in c.calls if "/rest/interface/detail?serialNumber=" in r[1]]
        assert summary and "policy" not in c._summary_list()[0]

    def test_consistent_top_level_policy_control(self):
        c = eth_summary_ctrl()
        c.summary_top_policy = True
        c.previews = [measured_preview("G6-M0b")]
        assert run(c, [pvlan_item(**ETH_SUMMARY_ADD_2212)])[0] == "exit"

    @pytest.mark.parametrize("deploy", [True, False])
    def test_check_mode_reaches_the_e3_check_mode_gate_not_ownership(self, deploy):
        c = eth_summary_ctrl()
        status, res = run(c, [pvlan_item(deploy=deploy, **ETH_SUMMARY_ADD_2212)], check_mode=True)
        assert status == "fail" and "could not be verified in check mode" in res["msg"] and "summary policy" not in res["msg"], res
        assert c.mutating() == []

    @pytest.mark.parametrize("kind", sorted(DEFECT_FRAGMENT))
    @pytest.mark.parametrize("check_mode", [False, True])
    def test_ownership_defects_refuse_before_any_write(self, kind, check_mode):
        c = eth_summary_ctrl()
        c.summary[IF7] = {
            "top_contradiction": {"policy": TRUNK},
            "policy_id": {"underlayPolicies": [under(c, policyId="POLICY-999")]},
            "entity": {"underlayPolicies": [under(c, entityName=IF8)]},
            "serial": {"underlayPolicies": [under(c, serialNumber="OTHER")]},
            "entity_type": {"underlayPolicies": [under(c, entityType="SWITCH")]},
            "null": {"underlayPolicies": None},
            "two": {"underlayPolicies": [under(c), under(c)]},
            "missing_id": {"underlayPolicies": [under(c, policyId=DELETE)]},
            "source_overlay": {"underlayPolicies": [under(c, source="OVERLAY")]},
        }[kind]
        status, res = run(c, [pvlan_item(**ETH_SUMMARY_ADD_2212)], check_mode=check_mode)
        assert status == "fail" and NO_WRITE in res["msg"] and DEFECT_FRAGMENT[kind] in res["msg"], res
        assert c.mutating() == [] and c.requests(mark=PREVIEW_MARK) == []

    def test_detail_policy_id_must_match_the_summary(self):
        nv = dict(pvlan_nv("G6-M0a"), POLICY_ID="POLICY-555")
        c = eth_summary_ctrl(nv)
        status, res = run(c, [pvlan_item(**ETH_SUMMARY_ADD_2212)])
        assert status == "fail" and "POLICY_ID" in res["msg"] and c.mutating() == []

    def test_attachment_second_live_policy_is_refused(self):
        c = eth_summary_ctrl()
        c.policies_extra = [copy.deepcopy(OVERLAY_PROFILE)]
        status, res = run(c, [pvlan_item(**ETH_SUMMARY_ADD_2212)])
        assert status == "fail" and "2 live policies" in res["msg"] and c.mutating() == []

    def test_port_channel_member_is_refused_on_the_measured_shape(self):
        member = "int_port_channel_trunk_member_11_1"
        c = eth_summary_ctrl({"PO_ID": "Port-channel5", "INTF_NAME": IF7, "DESC": "", "ADMIN_STATE": "true", "CONF": ""}, member)
        status, res = run(c, [pvlan_item(**ETH_SUMMARY_ADD_2212)])
        assert status == "fail" and "port-channel or vPC member" in res["msg"] and c.mutating() == []


class TestResetAndOtherPreStatePaths:

    def test_deleted_reset_of_a_pvlan_port_is_registered_and_gated(self):
        c = eth_summary_ctrl()
        c.previews = [reset_preview()]
        status, res = run(c, [{"name": IF7, "switch": [SWITCH_IP]}], state="deleted")
        assert status == "exit", res
        assert c.sent_nv()[0] == TRUNK and c.order() == ["MODIFY", "PREVIEW", "DEPLOY"]

    def test_invalid_reset_preview_sends_no_deploy_and_reports_the_pending_intent(self):
        c = eth_summary_ctrl()
        c.previews = [with_device_line(reset_preview(), "ip access-group KEEP-IN in")]
        status, res = run(c, [{"name": IF7, "switch": [SWITCH_IP]}], state="deleted")
        assert status == "fail" and NOT_OWNED in res["msg"] and NOT_ROLLED_BACK in res["msg"]
        assert deploys(c) == [] and len(c.requests("POST", MODIFY)) == 1

    @pytest.mark.parametrize("kind", ["overlay_policy", "policy_id", "missing_id", "top_contradiction"])
    def test_deleted_reset_ownership_error_sends_nothing(self, kind):
        c = eth_summary_ctrl()
        if kind == "overlay_policy":
            c.policies_extra = [copy.deepcopy(OVERLAY_PROFILE)]
        else:
            c.summary[IF7] = {
                "policy_id": {"underlayPolicies": [under(c, policyId="POLICY-999")]},
                "missing_id": {"underlayPolicies": [under(c, policyId=DELETE)]},
                "top_contradiction": {"policy": TRUNK},
            }[kind]
        c.previews = [reset_preview()]
        status, res = run(c, [{"name": IF7, "switch": [SWITCH_IP]}], state="deleted")
        assert status == "fail" and c.mutating() == [] and c.requests(mark=PREVIEW_MARK) == [], res
        fragment = {"overlay_policy": "2 live policies", "policy_id": "switch policy id", "missing_id": "lacks policyId", "top_contradiction": "contradicts"}[
            kind
        ]
        assert fragment in res["msg"], res

    def test_deleted_reset_when_summary_says_trunk_but_detail_is_pvlan(self):
        c = eth_summary_ctrl()
        c.summary[IF7] = {"underlayPolicies": [under(c, templateName=TRUNK)]}
        c.previews = [reset_preview()]
        status, res = run(c, [{"name": IF7, "switch": [SWITCH_IP]}], state="deleted")
        assert status == "fail" and "disagrees" in res["msg"] and c.mutating() == []

    def test_overridden_resets_an_unlisted_pvlan_port_through_the_gate(self):
        c = eth_summary_ctrl()
        c.detail[IF8] = {"policy": PVLAN, "nvPairs": pvlan_nv("G6-M0a", ifname=IF8)}
        c.previews = [reset_preview(IF8)]
        keep = pvlan_item(
            pvlan_mode="trunk promiscuous",
            admin_state=False,
            native_vlan="2301",
            allowed_vlans="2301",
            pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2211"}],
        )
        status, res = run(c, [keep], state="overridden")
        assert status == "exit", res
        assert c.sent_nv(IF8)[0] == TRUNK and c.sent_nv(IF7) is None and each_deploy_follows_a_preview(c)
        assert len(c.requests(mark=PREVIEW_MARK)) >= 1

    def test_overridden_with_an_unknown_unlisted_pvlan_port_sends_nothing(self):
        c = eth_summary_ctrl()
        c.detail[IF8] = {"policy": PVLAN, "nvPairs": pvlan_nv("G6-M0a", ifname=IF8)}
        c.summary[IF8] = {"underlayPolicies": [under(c, IF8, policyId=DELETE)]}
        keep = pvlan_item(
            pvlan_mode="trunk promiscuous",
            admin_state=False,
            native_vlan="2301",
            allowed_vlans="2301",
            pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2211"}],
        )
        status, res = run(c, [keep], state="overridden")
        assert status == "fail" and c.mutating() == [], res

    def test_conversion_of_a_pvlan_port_to_trunk_reaches_the_gate(self):
        c = eth_summary_ctrl()
        c.previews = [reset_preview()]
        status, res = run(c, [trunk_item(IF7)], state="replaced")
        # This shape used to be refused at ownership before any request; now the conversion reaches the
        # PVLAN pre-deploy gate, whose verdict on this preview is the existing behavior.
        assert c.requests(mark=PREVIEW_MARK) or status == "fail", res
        assert "summary policy None" not in res.get("msg", "")
        assert each_deploy_follows_a_preview(c)

    def test_out_of_sync_redeploy_goes_through_the_gate(self):
        c = eth_summary_ctrl(pvlan_nv("G6-M0b"))
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("G6-M0b")]
        status, res = run(c, [pvlan_item(**ETH_SUMMARY_ADD_2212)])
        assert status == "exit", res
        assert c.order() == ["PREVIEW", "DEPLOY"]


class TestNonPvlanPreserved:

    def _calls(self, top):
        c = FakeController()
        c.detail[IF8] = {"policy": TRUNK, "nvPairs": trunk_host_nv(IF8)}
        c.summary_top_policy = top
        return c

    @pytest.mark.parametrize(
        "config,state",
        [([{"name": IF8, "switch": [SWITCH_IP]}], "deleted"), ([trunk_item(IF8, allowed_vlans="10")], "merged")],
        ids=["deleted-trunk", "merged-trunk"],
    )
    def test_trunk_port_requests_do_not_depend_on_the_summary_shape(self, config, state):
        measured, legacy = self._calls(False), self._calls(True)
        a, b = run(measured, copy.deepcopy(config), state=state), run(legacy, copy.deepcopy(config), state=state)
        assert a[0] == b[0] and measured.calls == legacy.calls
        assert measured.requests(mark=PREVIEW_MARK) == []


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_e5.py
# One current-policy resolution for self.have, the detail cache and a new read.
#
# A non-PVLAN detail found in self.have or in the detail cache used to be returned BEFORE looking at the interface summary, so a
# summary whose valid nested underlay names int_pvlan_host was never contrasted and a merged change on that port was modified
# and deployed with no PVLAN gate. SYNTHETIC disagreement built on the MEASURED response shape (no `policy` is added to any raw
# answer).
# ====================================================================================================
CONFLICT = "the interface summary names int_pvlan_host but the detail holds 'int_trunk_host'"
SUMMARY_READ = "/rest/interface/detail?serialNumber="
DETAIL_BULK = "/rest/interface?serialNumber=%s" % SERIAL


def trunk_ctrl(names=(IF7,), pvlan_summary=()):
    c = FakeController()
    for name in names:
        c.detail[name] = {"policy": TRUNK, "nvPairs": trunk_host_nv(name)}
    for name in pvlan_summary:
        c.summary[name] = {"underlayPolicies": [under(c, name, templateName=PVLAN)]}
    return c


def eth_policy_cache_writes(c):
    return c.requests("POST", MODIFY) + c.requests("POST", DEPLOY)


# ===================================================================================== 1. the probe case
class TestProbeCaseThroughMain:

    def test_conflicting_summary_refuses_before_any_write(self):
        c = trunk_ctrl(pvlan_summary=(IF7,))
        status, res = run(c, [trunk_item(IF7, allowed_vlans="10")], state="merged")
        assert status == "fail" and CONFLICT in res["msg"] and "No configuration or deployment request was sent" in res["msg"], res
        assert eth_policy_cache_writes(c) == [] and c.requests(mark=PREVIEW_MARK) == []

    def test_consistent_trunk_control_is_unchanged(self):
        c = trunk_ctrl()
        status, res = run(c, [trunk_item(IF7, allowed_vlans="10")], state="merged")
        assert status == "exit", res
        assert c.order() == ["MODIFY", "DEPLOY"] and c.requests(mark=PREVIEW_MARK) == []


# ===================================================================================== 2. symmetry
class TestSameDecisionForEveryDetailOrigin:

    def _double(self, origin):
        d = PreStateDouble(entry_for(IF7, PVLAN), detail=(TRUNK, {}))
        trunk = {"policy": TRUNK, "interfaces": [{"ifName": IF7, "serialNumber": SERIAL, "nvPairs": {}}]}
        if origin == "have":
            d.have = [copy.deepcopy(trunk)]
        elif origin == "cache":
            d.intf_detail_cache[(SERIAL, IF7.lower())] = copy.deepcopy(trunk)
        return d

    @pytest.mark.parametrize("origin", ["have", "cache", "new-read"])
    def test_pre_state_conflict(self, origin):
        d = self._double(origin)
        assert d.pre(IF7) == ("unknown", CONFLICT, None)
        assert d.reads == ([] if origin != "new-read" else ["detail"])  # summary already loaded: never re-read

    @pytest.mark.parametrize(
        "state,config,unlisted",
        [
            ("merged", [trunk_item(IF7, allowed_vlans="10")], False),  # detail through self.have
            ("deleted", [{"name": IF7, "switch": [SWITCH_IP]}], False),  # reset of the listed port
            ("overridden", [trunk_item(IF7, allowed_vlans="10")], True),  # unlisted IF8 reset: detail cache
        ],
        ids=["merged-have", "deleted", "overridden-unlisted"],
    )
    def test_main_refuses_the_same_way(self, state, config, unlisted):
        target = IF8 if unlisted else IF7
        c = trunk_ctrl(names=(IF7, IF8), pvlan_summary=(target,))
        for name in (IF7, IF8):  # non-default, so deleted/overridden have a reset to send
            c.detail[name]["nvPairs"]["DESC"] = "non-default"
        status, res = run(c, copy.deepcopy(config), state=state)
        assert status == "fail" and CONFLICT in res["msg"] and target + " on " + SERIAL in res["msg"], res
        assert eth_policy_cache_writes(c) == []

    @pytest.mark.parametrize(
        "state,config",
        [
            ("merged", [trunk_item(IF7, allowed_vlans="10")]),
            ("deleted", [{"name": IF7, "switch": [SWITCH_IP]}]),
            ("overridden", [trunk_item(IF7, allowed_vlans="10")]),
        ],
        ids=["merged", "deleted", "overridden"],
    )
    def test_consistent_controls_keep_their_generic_behavior(self, state, config):
        c = trunk_ctrl(names=(IF7, IF8))
        for name in (IF7, IF8):
            c.detail[name]["nvPairs"]["DESC"] = "non-default"
        status, res = run(c, copy.deepcopy(config), state=state)
        assert status == "exit", res
        assert c.requests("POST", MODIFY) and c.requests(mark=PREVIEW_MARK) == []  # the generic write happens, ungated

    def test_reads_stay_per_switch(self):
        names = ("Ethernet1/7", "Ethernet1/8", "Ethernet1/9", "Ethernet1/10")
        c = trunk_ctrl(names=names)
        for n in names[1:]:
            c.detail[n]["nvPairs"]["DESC"] = "non-default"
        status, res = run(c, [trunk_item(IF7, allowed_vlans="10")], state="overridden")
        assert status == "exit", res
        assert len(c.requests("GET", SUMMARY_READ)) <= 2  # the generic read plus at most one PVLAN read, not per interface
        assert len([r for r in c.requests("GET") if r[1].endswith(DETAIL_BULK)]) <= 2


# ===================================================================================== 3. authoritative absence
class TestAuthoritativeAbsenceAgainstTheSummary:

    def _absent(self, entry, summary_ok=True):
        d = PreStateDouble(entry, summary_ok=summary_ok)
        d.intf_detail_authoritative_absent_keys.add((SERIAL, IF7.lower()))
        return d

    def test_absent_detail_against_a_pvlan_summary_is_unknown(self):
        d = self._absent(entry_for(IF7, PVLAN))
        state, reason, _nv = d.pre(IF7)
        assert state == "unknown" and "names int_pvlan_host but the detail holds None" in reason and d.reads == []

    def test_absent_detail_against_an_unreadable_summary_entry_is_unknown(self):
        d = self._absent(entry_for(IF7, underlayPolicies="garbage"))
        assert d.pre(IF7)[0] == "unknown"

    def test_absent_detail_with_a_failed_summary_names_nothing(self):
        d = self._absent(None, summary_ok=False)
        assert d.pre(IF7) == ("absent", None, None) and d.reads == []

    def test_absent_detail_without_any_summary_read_is_a_creation(self):
        d = self._absent(None)
        d.have_all_cached_snos = set()  # this invocation never loaded the summary
        assert d.pre(IF7) == ("absent", None, None) and d.reads == []  # no new read on a creation

    def test_absent_detail_with_a_non_pvlan_summary_stays_non_pvlan(self):
        assert self._absent(entry_for(IF7, TRUNK)).pre(IF7) == ("known", TRUNK, None)


# ===================================================================================== 4. kept refusals and gates
class TestKeptBehavior:

    def test_summary_trunk_against_detail_pvlan_is_still_refused(self):
        c = eth_summary_ctrl()
        c.summary[IF7] = {"underlayPolicies": [under(c, templateName=TRUNK)]}
        c.previews = [reset_preview()]
        status, res = run(c, [{"name": IF7, "switch": [SWITCH_IP]}], state="deleted")
        assert status == "fail" and "disagrees" in res["msg"] and eth_policy_cache_writes(c) == []

    @pytest.mark.parametrize(
        "name,sno", [("port-channel300", SERIAL), ("Loopback200", SERIAL), ("Ethernet1/3.2", SERIAL), ("vlan2001", SERIAL), ("vPC150", "FOX1821H035~" + SERIAL)]
    )
    def test_structural_exclusions_need_no_read(self, name, sno):
        d = PreStateDouble(entry_for(IF7, PVLAN), detail=(PVLAN, {}))
        assert module.DcnmIntf.dcnm_intf_pvlan_pre_state(d, name, sno) == ("known", None, None)
        assert d.reads == []

    def test_policy_less_svi_entry_is_not_a_target(self):
        d = PreStateDouble(copy.deepcopy(MEASURED["Vlan1"]))
        assert d.pre("Vlan1") == ("known", None, None) and d.reads == []

    def test_valid_pvlan_merge_still_passes_its_gate(self):
        c = eth_summary_ctrl()
        c.previews = [measured_preview("G6-M0b")]
        status, res = run(c, [pvlan_item(**ETH_SUMMARY_ADD_2212)])
        assert status == "exit" and c.order() == ["MODIFY", "PREVIEW", "DEPLOY"], res

    def test_pvlan_reset_still_goes_through_the_gate(self):
        c = eth_summary_ctrl()
        c.previews = [reset_preview()]
        status, res = run(c, [{"name": IF7, "switch": [SWITCH_IP]}], state="deleted")
        assert status == "exit" and c.order() == ["MODIFY", "PREVIEW", "DEPLOY"], res

    def test_conflict_in_check_mode_writes_nothing(self):
        c = trunk_ctrl(pvlan_summary=(IF7,))
        status, res = run(c, [trunk_item(IF7, allowed_vlans="10")], state="merged", check_mode=True)
        assert status == "fail" and CONFLICT in res["msg"] and c.mutating() == []


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_e6.py
# The summary's ifType/isPhysical can no longer hide a PVLAN policy known in the detail.
#
# A port whose summary entry said `isPhysical: false` (with a trunk underlay) used to be excluded BEFORE looking at the detail,
# so a `replaced` conversion of a port whose detail is int_pvlan_host was modified and deployed with no PVLAN gate. SYNTHETIC
# type/policy contradictions on the MEASURED response shape.
# ====================================================================================================
TYPE_CONFLICT = "the detail holds int_pvlan_host but the interface summary describes"


def eth_detail_type_writes(c):
    return c.requests("POST", MODIFY) + c.requests("POST", DEPLOY)


def nonphysical(c, template, **types):
    fields = {"isPhysical": "false"}
    fields.update(types)
    c.summary[IF7] = dict(fields, underlayPolicies=[under(c, templateName=template)])
    return c


# ===================================================================================== the probe case
class TestProbeReplacedCase:

    def test_replaced_conversion_with_contradictory_summary_type_sends_nothing(self):
        c = nonphysical(eth_summary_ctrl(), TRUNK)
        c.previews = [reset_preview()]
        status, res = run(c, [trunk_item(IF7)], state="replaced")
        assert status == "fail" and TYPE_CONFLICT in res["msg"] and "No configuration or deployment request was sent" in res["msg"], res
        assert eth_detail_type_writes(c) == [] and c.requests(mark=PREVIEW_MARK) == []

    def test_consistent_conversion_keeps_its_gate(self):
        c = eth_summary_ctrl()
        c.previews = [reset_preview()]
        status, res = run(c, [trunk_item(IF7)], state="replaced")
        assert c.requests(mark=PREVIEW_MARK), res  # reaches the pre-deploy gate (its verdict is unchanged)
        assert len(c.requests("POST", DEPLOY)) == 0 or c.order().index("PREVIEW") < c.order().index("DEPLOY")

    def test_deleted_variant_stays_a_no_op(self):
        # Not generalized (out of scope): the probe returns no operation for deleted in this harness.
        c = nonphysical(eth_summary_ctrl(), TRUNK)
        status, res = run(c, [{"name": IF7, "switch": [SWITCH_IP]}], state="deleted")
        assert eth_detail_type_writes(c) == []


# ===================================================================================== every detail origin
class TestSameDecisionForEveryOrigin:

    @pytest.mark.parametrize("origin", ["have", "cache", "new-read"])
    @pytest.mark.parametrize("types", [{"isPhysical": "false"}, {"ifType": "INTERFACE_PORT_CHANNEL"}, {"ifType": "INTERFACE_VLAN", "isPhysical": "false"}])
    def test_pvlan_detail_against_a_non_physical_summary_is_unknown(self, origin, types):
        d = PreStateDouble(entry_for(IF7, TRUNK, **types), detail=(PVLAN, {"PVLAN_MODE": "host"}))
        detail = {"policy": PVLAN, "interfaces": [{"ifName": IF7, "serialNumber": SERIAL, "nvPairs": {"PVLAN_MODE": "host"}}]}
        if origin == "have":
            d.have = [copy.deepcopy(detail)]
        elif origin == "cache":
            d.intf_detail_cache[(SERIAL, IF7.lower())] = copy.deepcopy(detail)
        state, reason, nv = d.pre(IF7)
        assert state == "unknown" and reason.startswith(TYPE_CONFLICT) and nv is None


# ===================================================================================== both directions
class TestContradictionsInBothDirections:

    def test_pvlan_in_detail_non_physical_trunk_summary(self):
        d = PreStateDouble(entry_for(IF7, TRUNK, isPhysical="false"), detail=(PVLAN, {}))
        assert d.pre(IF7)[0] == "unknown"

    def test_pvlan_in_summary_non_physical_pvlan_detail(self):
        d = PreStateDouble(entry_for(IF7, PVLAN, isPhysical="false"), detail=(PVLAN, {}))
        assert d.pre(IF7)[0] == "unknown"

    def test_pvlan_in_summary_non_physical_trunk_detail(self):
        d = PreStateDouble(entry_for(IF7, PVLAN, isPhysical="false"), detail=(TRUNK, {}))
        state, reason, _nv = d.pre(IF7)
        assert state == "unknown" and "names int_pvlan_host" in reason

    def test_pvlan_in_summary_non_physical_absent_detail(self):
        d = PreStateDouble(entry_for(IF7, PVLAN, isPhysical="false"), detail="absent")
        assert d.pre(IF7)[0] == "unknown"

    def test_main_merged_trunk_with_a_non_physical_pvlan_summary_sends_nothing(self):
        c = FakeController()
        c.detail[IF7] = {"policy": TRUNK, "nvPairs": trunk_host_nv(IF7)}
        nonphysical(c, PVLAN)
        status, res = run(c, [trunk_item(IF7, allowed_vlans="10")], state="merged")
        assert status == "fail" and eth_detail_type_writes(c) == []

    def test_main_pvlan_merge_with_a_non_physical_summary_sends_nothing(self):
        c = nonphysical(eth_summary_ctrl(), PVLAN)
        status, res = run(c, [pvlan_item(**ETH_SUMMARY_ADD_2212)])
        assert status == "fail" and "not a standalone physical Ethernet" in res["msg"] and eth_detail_type_writes(c) == []


# ===================================================================================== kept behavior
class TestKept:

    def test_non_physical_without_any_pvlan_indication_is_still_excluded(self):
        d = PreStateDouble(entry_for(IF7, TRUNK, isPhysical="false"), detail=(TRUNK, {}))
        assert d.pre(IF7) == ("known", TRUNK, None) and d.reads == ["detail"]  # one bulk read per switch

    def test_non_physical_with_unreadable_policy_and_no_pvlan_detail_is_excluded(self):
        d = PreStateDouble(entry_for(IF7, isPhysical="false", underlayPolicies=[{"source": ""}]), detail="absent")
        assert d.pre(IF7) == ("known", None, None)

    @pytest.mark.parametrize(
        "name,sno", [("port-channel300", SERIAL), ("Loopback200", SERIAL), ("Ethernet1/3.2", SERIAL), ("vlan2001", SERIAL), ("vPC150", "FOX1821H035~" + SERIAL)]
    )
    def test_identity_exclusions_need_no_read(self, name, sno):
        d = PreStateDouble(entry_for(IF7, PVLAN), detail=(PVLAN, {}))
        assert module.DcnmIntf.dcnm_intf_pvlan_pre_state(d, name, sno) == ("known", None, None) and d.reads == []

    def test_authoritative_absence_is_still_a_creation(self):
        d = PreStateDouble(None)
        d.have_all_cached_snos = set()
        d.intf_detail_authoritative_absent_keys.add((SERIAL, IF7.lower()))
        assert d.pre(IF7) == ("absent", None, None) and d.reads == []

    def test_pvlan_reset_and_redeploy_keep_their_gates(self):
        c = eth_summary_ctrl()
        c.previews = [reset_preview()]
        assert run(c, [{"name": IF7, "switch": [SWITCH_IP]}], state="deleted")[0] == "exit" and c.order() == ["MODIFY", "PREVIEW", "DEPLOY"]
        from .helpers.ethernet_controller import pvlan_nv

        c = eth_summary_ctrl(pvlan_nv("G6-M0b"))
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("G6-M0b")]
        assert run(c, [pvlan_item(**ETH_SUMMARY_ADD_2212)])[0] == "exit" and c.order() == ["PREVIEW", "DEPLOY"]

    def test_member_port_is_still_refused(self):
        member = "int_port_channel_trunk_member_11_1"
        c = eth_summary_ctrl({"PO_ID": "Port-channel5", "INTF_NAME": IF7, "DESC": "", "ADMIN_STATE": "true", "CONF": ""}, member)
        status, res = run(c, [pvlan_item(**ETH_SUMMARY_ADD_2212)])
        assert status == "fail" and "port-channel or vPC member" in res["msg"] and eth_detail_type_writes(c) == []

    def test_consistent_trunk_control_is_unchanged(self):
        c = FakeController()
        c.detail[IF7] = {"policy": TRUNK, "nvPairs": trunk_host_nv(IF7)}
        status, res = run(c, [trunk_item(IF7, allowed_vlans="10")], state="merged")
        assert status == "exit" and c.order() == ["MODIFY", "DEPLOY"]
