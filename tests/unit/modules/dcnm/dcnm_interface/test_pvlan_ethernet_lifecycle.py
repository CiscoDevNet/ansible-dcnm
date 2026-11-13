"""Native Ethernet PVLAN: lifecycle, ingress QoS state, patch_version coexistence and read reuse."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import ast
import copy
import json
import os
import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_ENABLED_PATCH_VERSIONS
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import registered_profile_keys
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface
from unittest.mock import patch
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from .helpers.ethernet_controller import DEPLOY
from .helpers.ethernet_controller import FIXTURE
from .helpers.ethernet_controller import IF7
from .helpers.ethernet_controller import IF8
from .helpers.ethernet_controller import MODIFY
from .helpers.ethernet_controller import PREVIEW_MARK
from .helpers.ethernet_controller import PVLAN
from .helpers.ethernet_controller import RECOMPUTE_FLAGS
from .helpers.ethernet_controller import SERIAL
from .helpers.ethernet_controller import TRUNK
from .helpers.ethernet_controller import ok
from .helpers.ethernet_controller import authority
from .helpers.ethernet_controller import measured_preview
from .helpers.ethernet_controller import pending
from .helpers.ethernet_controller import preview
from .helpers.ethernet_controller import recreate_preview
from .helpers.ethernet_controller import reset_preview
from .helpers.ethernet_controller import pvlan_item
from .helpers.ethernet_controller import pvlan_nv
from .helpers.ethernet_controller import run
from .helpers.ethernet_controller import trunk_host_nv
from .helpers.ethernet_controller import trunk_item
from .helpers.ethernet_lifecycle import ctrl
from .helpers.ethernet_controller import SMU
from .helpers.ethernet_controller import eth_item
from .helpers.ethernet_controller import full_model
from .helpers.ethernet_controller import have_nv
from .helpers import mixed_controller as SR
from .helpers import vpc_controller as V
from .helpers import vpc_controller as CI
from .helpers import vpc_controller as RD


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_lifecycle.py
# Native Ethernet PVLAN: lifecycle, response outcomes, pre-deploy gate and coexistence.
#
# Real main() through helpers/ethernet_controller. Case IDs E09-E14 refer to the design matrix.
# Assertions are made at the sender boundary: the ordered request log of the fake controller.
# ====================================================================================================
IF9 = "Ethernet1/9"
APPROVED_PATCH = sorted(GIE_ENABLED_PATCH_VERSIONS)[0]
TPROM_BOTH = pvlan_nv("G6-M0b")
ADD_2212 = dict(pvlan_mode="trunk promiscuous", pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2212"}])


def deploys(c):
    return c.requests("POST", DEPLOY)


def each_deploy_follows_a_preview(c):
    kinds = []
    for _method, p, _body in c.calls:
        if PREVIEW_MARK in p:
            kinds.append("P")
        elif p.endswith(DEPLOY):
            kinds.append("D")
    return all(i > 0 and kinds[i - 1] == "P" for i, k in enumerate(kinds) if k == "D")


# ===================================================================================== E09
class TestE09Lifecycle:

    def test_query_is_read_only(self):
        c = ctrl()
        status, res = run(c, [{"name": IF7, "switch": ["10.0.0.1"]}], state="query")
        assert status == "exit"
        assert c.mutating() == [] and c.requests(mark=PREVIEW_MARK) == []

    def test_deleted_resets_to_the_ethernet_default_through_the_gate(self):
        # Fixture: TEMPLATE-PREDICTED module reset (measured G6-MR + the int_trunk_host bpduguard line).
        c = ctrl()
        c.previews = [reset_preview()]
        status, res = run(c, [{"name": IF7, "switch": ["10.0.0.1"]}], state="deleted")
        assert status == "exit", res
        policy, nv = c.sent_nv()
        assert policy == TRUNK and "PVLAN_MODE" not in nv
        assert nv["BPDUGUARD_ENABLED"] is False and nv["ALLOWED_VLANS"] == "none"  # the real default payload
        assert c.order() == ["MODIFY", "PREVIEW", "DEPLOY"]

    def test_recreate_after_delete(self):
        c = ctrl()
        c.previews = [reset_preview()]
        assert run(c, [{"name": IF7, "switch": ["10.0.0.1"]}], state="deleted")[0] == "exit"
        c.previews = [recreate_preview()]
        status, res = run(
            c,
            [
                pvlan_item(
                    pvlan_mode="trunk promiscuous",
                    admin_state=False,
                    native_vlan="2301",
                    allowed_vlans="2301",
                    pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2211"}],
                )
            ],
        )
        assert status == "exit", res
        assert c.detail[IF7]["policy"] == PVLAN

    def test_overridden_resets_an_unlisted_pvlan_port_and_keeps_the_listed_one(self):
        c = ctrl()
        c.detail[IF8] = {"policy": PVLAN, "nvPairs": pvlan_nv("G6-M0a", ifname=IF8)}
        c.previews = [reset_preview(IF8)]
        status, res = run(
            c,
            [
                pvlan_item(
                    pvlan_mode="trunk promiscuous",
                    admin_state=False,
                    native_vlan="2301",
                    allowed_vlans="2301",
                    pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2211"}],
                )
            ],
            state="overridden",
        )
        assert status == "exit", res
        assert c.sent_nv(IF8)[0] == TRUNK
        assert c.sent_nv(IF7) is None  # retained and unchanged
        assert each_deploy_follows_a_preview(c)

    def test_overridden_never_writes_an_attachment_owned_pvlan_port(self):
        c = ctrl()
        c.detail[IF8] = {"policy": PVLAN, "nvPairs": pvlan_nv("G6-M0a", ifname=IF8)}
        c.summary[IF8] = {"underlayPolicies": [{"source": "OVERLAY", "templateName": PVLAN}]}
        status, res = run(
            c,
            [
                pvlan_item(
                    pvlan_mode="trunk promiscuous",
                    admin_state=False,
                    native_vlan="2301",
                    allowed_vlans="2301",
                    pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2211"}],
                )
            ],
            state="overridden",
        )
        assert c.sent_nv(IF8) is None
        assert deploys(c) == [] or status == "exit"

    def test_failed_gate_after_intent_change_is_reported_and_a_rerun_reads_fresh_state(self):
        c = ctrl()
        c.previews = [preview([])]  # stale: In-Sync while a change is expected
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail"
        assert "ALREADY changed on the controller" in res["msg"] and "No deployment request was sent" in res["msg"]
        assert deploys(c) == []
        # The controller now holds the new intent; the device has not received it.
        c.next_invocation()
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("G6-M0b")]
        before = len(c.calls)
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "exit", res
        later = c.calls[before:]
        assert not [x for x in later if x[1].endswith(MODIFY)]  # no second intent write
        assert len([x for x in later if x[1].endswith(DEPLOY)]) == 1


# ===================================================================================== E10
def err(entity, message="rejected"):
    return {"reportItemType": "ERROR", "message": message, "entity": entity}


def succ(entity):
    return {"reportItemType": "SUCCESS", "message": "Interface updated successfully", "entity": entity}


class TestE10Outcomes:

    @pytest.mark.parametrize(
        "resp,fragment",
        [
            ({"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [err(SERIAL + "~" + IF7)]}, "rejected 1 item"),
            ({"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [err(SERIAL + "~" + IF7)]}, "rejected 1 item"),
            (
                {"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [{"reportItemType": "WARNING", "message": "?", "entity": SERIAL + "~" + IF7}]},
                "indeterminate",
            ),
            ({"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": {"unexpected": True}}, "indeterminate"),
            ({"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": []}, "indeterminate"),
            ({"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [succ(SERIAL + "~Ethernet1/99")]}, "indeterminate"),
        ],
    )
    def test_uncertain_or_failed_modify_never_reaches_deploy(self, resp, fragment):
        c = ctrl()
        c.modify_responses = [resp]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and fragment in res["msg"]
        assert deploys(c) == [] and c.requests(mark=PREVIEW_MARK) == []

    def test_mixed_batch_names_what_was_applied(self):
        c = ctrl()
        c.detail[IF8] = {"policy": PVLAN, "nvPairs": pvlan_nv("G6-M0a", ifname=IF8)}
        c.modify_responses = [{"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [succ(SERIAL + "~" + IF7), err(SERIAL + "~" + IF8)]}]
        status, res = run(c, [pvlan_item(**ADD_2212), pvlan_item(IF8, **ADD_2212)])
        assert status == "fail" and "Applied before the rejection" in res["msg"]
        assert deploys(c) == []

    @pytest.mark.parametrize(
        "resp",
        [
            {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}},
            ok([{"switchId": SERIAL, "status": "Out-of-Sync", "pendingConfig": None}]),
            ok({"error": "boom"}),
            ok([{"switchId": SERIAL, "status": "Weird", "pendingConfig": ["interface ethernet1/7"]}]),
        ],
    )
    def test_preview_failure_or_malformed_answer_refuses_deploy(self, resp):
        c = ctrl()
        c.previews = [resp]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "pre-deploy gate" in res["msg"]
        assert deploys(c) == []

    def test_measured_deploy_500_fails_visibly_without_retry(self):
        c = ctrl()
        c.previews = [measured_preview("G6-M0b")]
        c.deploy_responses = [{"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": FIXTURE["deploy_500"]["data"]}]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "failed or is indeterminate" in res["msg"]
        assert len(deploys(c)) == 1

    def test_deploy_200_with_error_item_is_not_success(self):
        c = ctrl()
        c.previews = [measured_preview("G6-M0b")]
        c.deploy_responses = [ok([err(SERIAL + "~" + IF7, "CLI command failed")])]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "failed or is indeterminate" in res["msg"]

    def test_benign_no_command_warning_still_needs_matching_readback(self):
        c = ctrl()
        c.previews = [measured_preview("G6-M0b")]
        c.deploy_responses = [ok([{"reportItemType": "WARNING", "message": "No Commands to execute. In-Sync"}])]
        c.compliance = ["Out-of-Sync"] * 10
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "did not reach In-Sync" in res["msg"]


# ===================================================================================== E11
class TestE11FreshPendingGate:

    def test_exact_legacy_recompute_flags_and_zero_manage_calls(self):
        c = ctrl()
        c.previews = [measured_preview("G6-M0b")]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "exit", res
        previews = c.requests("GET", PREVIEW_MARK)
        assert len(previews) == 1
        assert previews[0][1] == ("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/test_fabric/config-preview/" + SERIAL + "?" + RECOMPUTE_FLAGS)
        assert c.manage() == []
        idx = [i for i, x in enumerate(c.calls) if x[1].endswith(DEPLOY)][0]
        assert PREVIEW_MARK in c.calls[idx - 1][1]  # fresh read immediately before deploy

    @pytest.mark.parametrize(
        "lines,fragment",
        [
            ([], "is empty but the device differs"),
            (pending("G6-M0b") + ["interface ethernet1/9", "  shutdown"], "outside this deploy batch"),
            (["feature private-vlan"] + pending("G6-M0b"), "outside interface scope"),
            ([l.replace("mapping trunk 2210 2211-2212", "mapping trunk 22102210 2211-2212") for l in pending("G6-M0b")], "malformed VLAN"),
            ([l.replace("2211-2212", "2211-2213") for l in pending("G6-M0b")], "not part of the intended state"),
            (pending("G6-M0b")[:-1] + ["  no switchport private-vlan trunk native vlan 2301", "configure terminal"], "unexpected removal"),
            (pending("G6-M0b")[:-1] + ["  ptp", "configure terminal"], "unmodeled command"),
        ],
    )
    def test_stale_foreign_malformed_or_wrong_pending_stops_deploy(self, lines, fragment):
        running, expected = authority("G6-M0b")  # measured device and controller authority
        c = ctrl()
        c.previews = [preview(lines, status="Out-of-Sync" if lines else "In-Sync", running=running, expected=expected)]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and fragment in res["msg"], res["msg"]
        assert deploys(c) == []

    def test_preview_for_another_serial_is_refused(self):
        c = ctrl()
        c.previews = [measured_preview("G6-M0b", serial="OTHER0000")]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "0 entries" in res["msg"]
        assert deploys(c) == []

    def test_check_deploy_resend_and_status_retry_are_each_gated(self):
        # check_deployment_status (pre-existing) decides from the summary read BEFORE the deploy;
        # the port therefore starts Out-of-Sync so the loop reaches its retry at 10.
        c = ctrl()
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("G6-M0b")] + [measured_preview("G6-M0b")] * 3
        c.compliance = ["Out-of-Sync"] * 9 + ["In-Sync"] * 10
        status, res = run(c, [pvlan_item(**ADD_2212)], check_deploy=True)
        assert status == "exit", res
        assert len(deploys(c)) >= 3  # main, resend, retry at 10
        assert each_deploy_follows_a_preview(c)

    def test_refused_resend_gate_sends_no_second_deploy(self):
        c = ctrl()
        running, expected = authority("G6-M0b")
        c.previews = [measured_preview("G6-M0b"), preview(["interface ethernet1/9", "  shutdown"], running=running, expected=expected)]
        status, res = run(c, [pvlan_item(**ADD_2212)], check_deploy=True)
        assert status == "fail" and "check_deploy_resend" in res["msg"]
        assert len(deploys(c)) == 1

    def test_refused_status_retry_gate_sends_no_retry(self):
        c = ctrl()
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("G6-M0b"), measured_preview("G6-M0b"), {"RETURN_CODE": 500, "DATA": {}}]
        c.compliance = ["Out-of-Sync"] * 30
        status, res = run(c, [pvlan_item(**ADD_2212)], check_deploy=True)
        assert status == "fail" and "deployment_status_retry" in res["msg"]
        assert len(deploys(c)) == 2


# ===================================================================================== E12
class TestE12CheckModeDeployFalseAndConvergence:

    def test_check_mode_sends_no_write_and_no_refreshing_preview(self):
        c = ctrl()
        status, res = run(c, [pvlan_item(**ADD_2212)], check_mode=True)
        # The bulk capability cannot be verified without its POST probe,
        # so a planned PVLAN write in check mode ends in an explicit refusal, not a success.
        assert status == "fail" and "could not be verified in check mode" in res["msg"]
        assert c.mutating() == [] and c.requests(mark=PREVIEW_MARK) == []

    def test_deploy_false_saves_intent_only(self):
        c = ctrl()
        status, res = run(c, [pvlan_item(deploy=False, **ADD_2212)])
        assert status == "exit"
        assert c.order() == ["MODIFY"]

    def test_already_out_of_sync_intent_is_redeployed_through_the_gate(self):
        c = ctrl(TPROM_BOTH)
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("G6-M0b")]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "exit", res
        assert c.order() == ["PREVIEW", "DEPLOY"]

    def test_convergence_failure_after_deploy_is_visible(self):
        c = ctrl()
        c.previews = [measured_preview("G6-M0b")]
        c.compliance = ["Out-of-Sync"] * 10
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "did not reach In-Sync" in res["msg"]
        assert len(deploys(c)) == 1


# ===================================================================================== E13
def test_e13_registry_rows_and_resets_are_unchanged_except_the_c1_pvlan_companions():
    """The 11 PVLAN companion bindings (REGISTRY_BINDING rows) are added, each with a reset_wire inferred from
    its sibling parents; nothing else in the table changed (234 -> 245 rows, 207 -> 218 resets)."""
    path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "plugins", "module_utils", "gie_binding_table.py")
    tree = ast.parse(open(path).read())
    rows = resets = pvlan = 0
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "BINDING_TABLE" for t in node.targets):
            for elt in node.value.elts:
                keys = dict((k.value, v) for k, v in zip(elt.keys, elt.values) if isinstance(k, ast.Constant))
                rows += 1
                resets += "reset_wire" in keys
                parent = keys.get("parent_template")
                pvlan += isinstance(parent, ast.Constant) and "pvlan" in parent.value
    # The vPC PVLAN qosStatsSuppressed row (inferred reset): one more row, reset and PVLAN row.
    # + 5 rows and 5 resets: SMU 017 first increment, slice 0b_37 (no PVLAN parent).
    # + 5 rows and 5 resets: SMU 017 loopback EIGRP, slice 0b_38; + 1 row and 1 reset: routed port-channel PIM BFD,
    # slice 0b_39; + 19 rows and 16 resets: the routed port-channel OSPF family, slice 0b_40; + 1 row and 1 reset: the
    # trunk port-channel reset-skip default, slice rs1 (no PVLAN parent); + 4 rows and 2 resets: the peer-link parent,
    # slice pl1 (no PVLAN parent); + 12 rows and 12 resets: the ToR-uplink parent, slice ul1 (no PVLAN parent); + 2 rows
    # and 2 resets: routed port-channel PIM sparse mode and DR priority, slice 0b_41 (no PVLAN parent).
    assert (rows, resets, pvlan) == (234 + 11 + 1 + 5 + 5 + 1 + 19 + 1 + 4 + 12 + 2,
                                     207 + 11 + 1 + 5 + 5 + 1 + 16 + 1 + 2 + 12 + 2, 11 + 1)


# ===================================================================================== E14
class TestE14Coexistence:

    def batch(self, invalid_second=False):
        items = [
            pvlan_item(**ADD_2212),
            trunk_item(IF8, deploy=True, disable_lldp_transmit=True, description="scalar sibling"),
            {
                "name": IF9,
                "type": "eth",
                "switch": ["10.0.0.1"],
                "deploy": True,
                "profile": {"mode": "dot1q", "access_vlan": "300", "description": "dot1q sibling"},
            },
        ]
        if invalid_second:
            items[1] = pvlan_item(IF8, pvlan_mode="trunk promiscuous", pvlan_mapping=[{"primary_vlan": True, "secondary_vlans": "2"}])
        return items

    def fresh(self):
        c = ctrl()
        c.detail[IF8] = {"policy": TRUNK, "nvPairs": trunk_host_nv(IF8)}
        c.detail[IF9] = {"policy": TRUNK, "nvPairs": trunk_host_nv(IF9)}
        return c

    def test_pvlan_scalar_and_dot1q_siblings_in_one_real_batch(self):
        # The IF8 sibling sets a REGISTERED scalar (disable_lldp_transmit), so PR725's
        # patch_version contract applies to this batch: the caller declares the approved
        # patch. PVLAN itself needs none (see the negative case below and the PVLAN suites,
        # which run with the argument absent).
        alone = self.fresh()
        assert run(alone, self.batch()[1:2] + self.batch()[2:], patch_version=APPROVED_PATCH)[0] == "exit"
        c = self.fresh()
        sibling_lines = ["interface ethernet1/8", "  no lldp transmit", "interface ethernet1/9", "  switchport mode dot1q-tunnel"]
        running, expected = authority("G6-M0b")
        c.previews = [preview(pending("G6-M0b")[:-1] + sibling_lines + ["configure terminal"], running=running, expected=expected)]
        status, res = run(c, self.batch(), patch_version=APPROVED_PATCH)
        assert status == "exit", res
        assert c.sent_nv(IF8) == alone.sent_nv(IF8)  # no PVLAN handling of siblings
        assert c.sent_nv(IF9) == alone.sent_nv(IF9)
        assert str(c.sent_nv(IF8)[1].get("lldpTransmit")).lower() == "true"  # registered scalar still emitted
        assert c.sent_nv(IF9)[0] == "int_dot1q_tunnel_host"
        assert c.sent_nv(IF7)[0] == PVLAN
        assert alone.requests(mark=PREVIEW_MARK) == []  # siblings alone never gate

    def test_registered_scalar_sibling_without_patch_stops_the_whole_batch(self):
        # Same batch, no patch_version: the registered scalar is refused before ANY write,
        # including the PVLAN item that on its own would need no patch context.
        c = self.fresh()
        status, res = run(c, self.batch())
        assert status == "fail"
        assert "disable_lldp_transmit" in res["msg"] and "patch_version" in res["msg"]
        assert c.mutating() == [] and c.requests(mark=PREVIEW_MARK) == []

    def test_unsupported_second_object_stops_the_whole_batch(self):
        c = self.fresh()
        status, res = run(c, self.batch(invalid_second=True))
        assert status == "fail"
        assert c.mutating() == [] and c.requests(mark=PREVIEW_MARK) == []


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_eth_qos_state.py
# Ingress QoS of the Ethernet PVLAN parent int_pvlan_host, judged on the RESULTING state.
#
# NOT LIVE TESTED. Real main() through the existing Ethernet PVLAN harness, deploy false. A requested non-empty qos_policy needs
# ENABLE_QOS true after an omitted enable_qos resolves (merged keeps HAVE; replaced, overridden and a policy change take the
# template default false). A name kept from HAVE while QoS is disabled stays allowed. Policy names are synthetic.
# ====================================================================================================
REFUSAL = "qos_policy requires enable_qos true"
ENABLED = dict(ENABLE_QOS="true", QOS_POLICY="QOS-OLD")
DISABLED_EMPTY = dict(ENABLE_QOS="false", QOS_POLICY="")
DISABLED_NAMED = dict(ENABLE_QOS="false", QOS_POLICY="QOS-OLD")


def _item(state, **profile):
    return eth_item(deploy=False, **profile) if state == "merged" else full_model(**profile)


def _sent_qos(c, ifname=IF7):
    nv = c.sent_nv(ifname)[1]
    return nv["ENABLE_QOS"], nv["QOS_POLICY"]


def _assert_refused(status, res, c):
    assert status == "fail" and REFUSAL in res["msg"], res.get("msg")
    assert c.mutating() == []


@pytest.mark.parametrize("state, stored", [
    ("merged", DISABLED_EMPTY),
    ("merged", DISABLED_NAMED),
    ("replaced", ENABLED),
    ("replaced", DISABLED_EMPTY),
    ("overridden", ENABLED),
    ("overridden", DISABLED_NAMED),
])
def test_a_requested_name_that_resolves_to_disabled_qos_is_refused_before_any_write(state, stored):
    c = ctrl(nv=have_nv(**stored))
    status, res = run(c, [_item(state, qos_policy="QOS-NEW")], state=state, patch_version=SMU)
    _assert_refused(status, res, c)


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_a_requested_name_on_a_policy_change_takes_the_disabled_default_and_is_refused(state):
    c = ctrl(nv=trunk_host_nv(IF7), policy=TRUNK)
    status, res = run(c, [full_model(qos_policy="QOS-NEW")], state=state, patch_version=SMU)
    _assert_refused(status, res, c)


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_a_valid_item_before_the_refused_one_is_not_written(state):
    c = ctrl(nv=have_nv(**DISABLED_EMPTY))
    c.detail[IF8] = {"policy": PVLAN, "nvPairs": dict(pvlan_nv("G6-M0a", ifname=IF8), **DISABLED_EMPTY)}
    valid = _item(state, enable_qos=True, qos_policy="QOS-OK")
    invalid = dict(copy.deepcopy(_item(state, qos_policy="QOS-NEW")), name=IF8)
    status, res = run(c, [valid, invalid], state=state, patch_version=SMU)
    _assert_refused(status, res, c)
    assert IF8 in res["msg"] and IF7 + " on" not in res["msg"]


def test_an_explicit_false_with_a_name_is_still_refused_at_input():
    c = ctrl(nv=have_nv(**ENABLED))
    status, res = run(c, [eth_item(deploy=False, enable_qos=False, qos_policy="QOS-NEW")], patch_version=SMU)
    assert status == "fail" and "Invalid parameters in playbook" in res["msg"] and REFUSAL in res["msg"], res.get("msg")
    assert c.mutating() == []


@pytest.mark.parametrize("state, stored, profile, sent", [
    # merged name-only over enabled QoS: the policy change the module honors
    ("merged", ENABLED, dict(qos_policy="QOS-NEW"), ("true", "QOS-NEW")),
    ("merged", DISABLED_EMPTY, dict(enable_qos=True, qos_policy="QOS-NEW"), ("true", "QOS-NEW")),
    ("replaced", DISABLED_NAMED, dict(enable_qos=True, qos_policy="QOS-NEW"), ("true", "QOS-NEW")),
    ("overridden", ENABLED, dict(enable_qos=True, qos_policy="QOS-NEW"), ("true", "QOS-NEW")),
    # disabling keeps an omitted stored name; re-enabling reuses it
    ("merged", ENABLED, dict(enable_qos=False), ("false", "QOS-OLD")),
    ("merged", DISABLED_NAMED, dict(enable_qos=True), ("true", "QOS-OLD")),
    # an empty name clears
    ("merged", DISABLED_NAMED, dict(qos_policy=""), ("false", "")),
    ("merged", ENABLED, dict(enable_qos=False, qos_policy=""), ("false", "")),
    ("replaced", ENABLED, dict(qos_policy=""), ("false", "")),
    # neither key
    ("merged", DISABLED_NAMED, dict(description="qos untouched"), ("false", "QOS-OLD")),
    ("merged", ENABLED, dict(description="qos untouched"), ("true", "QOS-OLD")),
    ("replaced", ENABLED, dict(), ("false", "")),
])
def test_supported_qos_requests_are_unchanged(state, stored, profile, sent):
    c = ctrl(nv=have_nv(**stored))
    status, res = run(c, [_item(state, **profile)], state=state, patch_version=SMU)
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert _sent_qos(c) == sent


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_patch_version_coexistence.py
# Coexistence of native Ethernet PVLAN (int_pvlan_host) with the caller-supplied patch_version gate.
#
# Native PVLAN owns its fields directly (no registry binding exists for int_pvlan_host), so the
# patch_version contract must neither be required for PVLAN nor change what PVLAN sends. Registered
# scalars keep their own contract. Real main() through the PVLAN harness; assertions are made on the
# ordered request log of the fake controller (method, path, body), not on exit status alone.
#
# NOT LIVE TESTED. No controller or switch is contacted.
# ====================================================================================================
APPROVED = sorted(GIE_ENABLED_PATCH_VERSIONS)[0]
PATCH_VALUES = [
    pytest.param(None, id="omitted"),
    pytest.param(APPROVED, id="approved"),
    pytest.param("4.4.1", id="nd_release"),
    pytest.param("4.3.1.0175006010", id="unapproved"),
]


def _request_log(c):
    return [(m, p, json.loads(b) if isinstance(b, str) else b) for m, p, b in c.calls]


def test_int_pvlan_host_registers_only_the_two_c1_lldp_companions():
    """Precondition for everything below: the PVLAN core fields stay native. Only the two LLDP companions
    of int_pvlan_host are registered (REGISTRY_BINDING rows); every native PVLAN field below still owes nothing to the patch gate."""
    assert registered_profile_keys(PVLAN) == {"disable_lldp_transmit", "disable_lldp_receive"}


def test_every_engine_contribution_call_receives_the_callers_patch_version():
    """All gie_contribute_nvpairs call sites, including the PVLAN builder added after the patch
    gate was designed, forward the module's own patch_version. A site passing only the NDFC
    version would silently evaluate the gate with no caller context."""
    with open(dcnm_interface.__file__) as handle:
        tree = ast.parse(handle.read())
    calls = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "gie_contribute_nvpairs"
    ]
    # + the port-channel and vPC PVLAN builders (7 -> 9), + the peer-link builder (10), + the uplink builder (11).
    assert len(calls) == 11, len(calls)
    for call in calls:
        assert len(call.args) == 4, ast.get_source_segment(open(dcnm_interface.__file__).read(), call)
        fourth = call.args[3]
        assert isinstance(fourth, ast.Call) and getattr(fourth.func, "id", None) == "getattr"
        assert [a.value for a in fourth.args[1:]] == ["patch_version", None]


@pytest.mark.parametrize("patch_version", PATCH_VALUES)
def test_native_pvlan_merged_is_byte_identical_for_any_patch_value(patch_version):
    reference = ctrl()
    reference.previews = [measured_preview("G6-M0b")]
    assert run(reference, [pvlan_item(**ADD_2212)])[0] == "exit"

    c = ctrl()
    c.previews = [measured_preview("G6-M0b")]
    status, res = run(c, [pvlan_item(**ADD_2212)], patch_version=patch_version)
    assert status == "exit", res
    assert c.sent_nv(IF7)[0] == PVLAN
    assert _request_log(c) == _request_log(reference)
    assert "PATCH_VERSION" not in json.dumps(_request_log(c)).upper()


@pytest.mark.parametrize("patch_version", PATCH_VALUES)
def test_native_pvlan_deleted_reset_is_unchanged_by_patch_value(patch_version):
    c = ctrl()
    c.previews = [reset_preview()]
    status, res = run(c, [{"name": IF7, "switch": ["10.0.0.1"]}], state="deleted",
                      patch_version=patch_version)
    assert status == "exit", res
    policy, nv = c.sent_nv()
    assert policy == TRUNK and "PVLAN_MODE" not in nv
    assert c.order() == ["MODIFY", "PREVIEW", "DEPLOY"]


@pytest.mark.parametrize("patch_version", PATCH_VALUES)
def test_native_pvlan_query_is_read_only_for_any_patch_value(patch_version):
    c = ctrl()
    status, _res = run(c, [{"name": IF7, "switch": ["10.0.0.1"]}], state="query",
                       patch_version=patch_version)
    assert status == "exit"
    assert c.mutating() == [] and c.requests(mark=PREVIEW_MARK) == []


@pytest.mark.parametrize("patch_version", PATCH_VALUES)
def test_trunk_to_pvlan_transition_never_carries_registered_trunk_values(patch_version):
    """The registry carry-forward is same-parent only: registered values the controller holds on
    int_trunk_host (GUARD_MODE, aclFilter) must not be copied into the new int_pvlan_host payload,
    whatever the patch context. (lldpTransmit/lldpReceive are a separate, PVLAN-native
    preservation owned by interface_pvlan.PRESERVE_ALWAYS and are not asserted here.)"""
    have = dict(trunk_host_nv(IF7), GUARD_MODE="root", aclFilter="PILOT-ACL")
    c = ctrl(nv=have, policy=TRUNK)
    c.previews = [recreate_preview()]
    item = pvlan_item(
        pvlan_mode="trunk promiscuous", admin_state=False, native_vlan="2301", allowed_vlans="2301",
        pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2211"}],
    )
    status, res = run(c, [item], patch_version=patch_version)
    assert status == "exit", res
    policy, nv = c.sent_nv(IF7)
    assert policy == PVLAN
    assert "GUARD_MODE" not in nv and "aclFilter" not in nv
    assert c.order() == ["MODIFY", "PREVIEW", "DEPLOY"]


@pytest.mark.parametrize("patch_version", [p for p in PATCH_VALUES if p.id in ("omitted", "unapproved")])
def test_registered_key_on_a_pvlan_profile_needs_an_approved_patch(patch_version):
    """Disable_lldp_transmit is a registered int_pvlan_host companion now. Without an approved patch_version the
    explicit field is refused with the engine's patch message before any write or preview (the native siblings of the same
    item included). The approved/ND 4.4.1 side is covered by test_pvlan_companions.py."""
    c = ctrl()
    c.previews = [measured_preview("G6-M0b")]
    item = pvlan_item(disable_lldp_transmit=True, **copy.deepcopy(ADD_2212))
    status, res = run(c, [item], patch_version=patch_version)
    assert status == "fail"
    assert "'disable_lldp_transmit' requires caller-supplied patch_version" in res["msg"]
    assert c.mutating() == [] and c.requests(mark=PREVIEW_MARK) == []


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_api_reuse.py
# API-REUSE: two read reuses, local to ONE invocation and to the phase BEFORE its first write.
#
# 1. PLANNING-REUSE: the saved-state recognition reads ONE forced preview per queried serial and every candidate on that switch judges it;
#    the gates keep their own fresh preview. Measured before (d76094b0): a saved mixed Po retry recomputed the same switch 3 times
#    before its gate (4 previews in all).
# 2. PREWRITE-REUSE: see the second section.
#
# Real main() through the existing harnesses; only the controller boundary is faked. Results, deploy payloads and saved-state records are
# asserted to stay those of the base, not only the counters.
# ====================================================================================================
PREVIEW = "/config-preview/"


def previews_by_serial(calls):
    out = {}
    for c in calls:
        if c[0] == "GET" and PREVIEW in c[1]:
            serial = c[1].split(PREVIEW)[1].split("?")[0]
            out[serial] = out.get(serial, 0) + 1
    return out


# ================================================================== 1. PLANNING-REUSE, end to end
def test_saved_mixed_po_retry_reads_one_planning_preview_and_one_gate_preview_with_the_same_outcome():
    ctrl = SR.saved_po_ctrl()
    SR.stage(ctrl)
    status, result, start = SR.retry(ctrl)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    # before: 4 (Po301 candidate, po502 candidate, conventional sibling, gate); now 1 planning + 1 gate
    assert previews_by_serial(ctrl.calls[start:]) == {SERIAL: 2}
    # the outcome is the base one: one deploy of exactly the two saved aggregates, no mark-delete, both completions reported
    bodies = SR.deploy_bodies(ctrl, start)
    assert len(bodies) == 1 and sorted(i["ifName"].lower() for i in bodies[0]) == ["port-channel301", "port-channel502"]
    assert "interface/markdelete" not in SR.later_writes(ctrl, start)
    assert ctrl.conv_marked is None and ctrl.marked is None, "both port-channels are gone after the deploy"
    rel = [r for r in result["pvlan_gate_invocation_releases"] if r["site"] == "delete_deploy"]
    assert rel == [{"site": "delete_deploy", "serial": SERIAL, "interfaces": ["ethernet1/14"], "withdrawn": ["no interface port-channel301"]}]
    # the base records (d76094b0): the PVLAN Po continuation and the conventional sibling, both completing the saved deletion
    assert [(r.get("kind"), r.get("name"), r.get("operation"), r.get("state")) for r in result["pvlan_saved"]] == [
        (None, None, "delete", "completing the saved deletion"),
        ("conventional", "Port-channel301", "delete", "completing the saved deletion")], result["pvlan_saved"]


def test_saved_mixed_vpc_retry_reads_each_peers_own_planning_preview_once():
    ctrl = SR.saved_vpc_ctrl()
    status, result, start = SR.vpc_retry(ctrl)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    counts = previews_by_serial(ctrl.calls[start:])
    assert set(counts) == {V.SN1, V.SN2}, counts
    assert counts[V.SN1] == counts[V.SN2] == 2, counts  # 1 planning + 1 gate per peer (before: 3 per peer)
    sent = sorted((i["serialNumber"], i["ifName"].lower()) for i in json.loads(ctrl.deploys()[0][2]))
    assert sent == [(V.PAIR, "vpc10"), (V.PAIR, "vpc305")]
    assert SR.vpc_owned(result) == [(V.SN1, ("ethernet1/5",), ("no interface port-channel305",)),
                                    (V.SN2, ("ethernet1/6",), ("no interface port-channel305",))]


def test_a_new_process_reads_its_own_planning_preview_nothing_is_carried_over():
    ctrl = SR.saved_po_ctrl()
    SR.stage(ctrl)
    staged = len(ctrl.calls)
    _status, _result, start = SR.retry(ctrl)
    assert start == staged and previews_by_serial(ctrl.calls[start:]) == {SERIAL: 2}


# ================================================================== 1. PLANNING-REUSE, the helper's contract
class _Obj(object):
    """The smallest object the helper needs; the method under test is the module's own."""

    def __init__(self):
        self.module = object()
        self.fabric = "f"
        self.paths = {"PVLAN_CONFIG_PREVIEW": "/control/fabrics/{}/config-preview/{}?forceShowRun=true"}

    def planning(self, query_serial):
        return module.DcnmIntf.dcnm_intf_pvlan_planning_preview(self, query_serial)


def _run_helper(answers, calls):
    def fake(mod, method, path, data=None):
        calls.append(path)
        return answers.pop(0)
    return patch.object(module, "dcnm_send", side_effect=fake)


GOOD_A = preview(["interface ethernet1/9", "  description x"], serial="SNA")
GOOD_B = preview([], serial="SNB")
BAD = {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}


def test_an_unreadable_preview_is_returned_to_its_caller_and_never_reused_as_a_state():
    obj, calls = _Obj(), []
    with _run_helper([BAD, GOOD_A], calls):
        assert obj.planning("SNA") is BAD          # the caller judges the failure as before
        assert obj.planning("SNA") is GOOD_A       # read again: the failure was not cached
        assert obj.planning("SNA") is GOOD_A       # now reused
    assert len(calls) == 2


def test_each_queried_serial_has_its_own_answer():
    obj, calls = _Obj(), []
    with _run_helper([GOOD_A, GOOD_B], calls):
        assert obj.planning("SNA") is GOOD_A and obj.planning("SNB") is GOOD_B
        assert obj.planning("SNA") is GOOD_A and obj.planning("SNB") is GOOD_B
    assert [c.split(PREVIEW)[1].split("?")[0] for c in calls] == ["SNA", "SNB"]


def test_an_answer_of_another_serial_is_not_kept_for_the_queried_one():
    obj, calls = _Obj(), []
    with _run_helper([GOOD_B, GOOD_A], calls):
        assert obj.planning("SNA") is GOOD_B   # returned as read (its caller refuses it), not cached under SNA
        assert obj.planning("SNA") is GOOD_A
    assert len(calls) == 2


def test_once_sending_starts_every_read_is_fresh():
    obj, calls = _Obj(), []
    with _run_helper([GOOD_A, GOOD_A, GOOD_A], calls):
        obj.planning("SNA")
        obj._pvlan_sending = True
        obj.planning("SNA")
        obj.planning("SNA")
    assert len(calls) == 3


def test_the_sender_closes_the_planning_phase_before_any_request():
    """Static: the sending entry point marks the phase and drops the planning answers before its first request."""
    import inspect
    src = inspect.getsource(module.DcnmIntf.dcnm_intf_send_message_to_dcnm)
    first_request = min(i for i in (src.find("dcnm_send("), src.find("resp = dcnm_send")) if i >= 0)
    assert 0 <= src.find("self._pvlan_sending = True") < first_request
    assert 0 <= src.find('pop("pvlan_planning_previews", None)') < first_request


# ================================================================== 2. PREWRITE-REUSE (vPC reads before the first write)

POLICIES, DETAIL = "/control/policies/switches/", "/rest/interface?serialNumber="


def reads(calls, mark, serial, before=None):
    end = len(calls) if before is None else before
    return sum(1 for c in calls[:end] if c[0] == "GET" and (mark + serial) in c[1] and "&ifName=" not in c[1])


def first_write(calls):
    return next(i for i, c in enumerate(calls) if c[0] in ("POST", "PUT", "DELETE"))


def test_vpc_creation_reads_each_peers_policies_once_before_writing_and_fresh_after_the_deploy():
    """Peers with DIFFERENT port-channel numbers, playbook order reversed (peer1 = SN2): each serial gets its own state."""
    pcids = ("11", "12")
    ctrl = V.baseline_ctrl()
    V.create_previews(ctrl)
    CI.remap(ctrl, pcids)
    # peer1_* of the playbook belong to its FIRST switch (SN2 here): SN2 owns 12 and SN1 owns 11
    status, result = V.run_vpc(ctrl, [V.vpc_item(switches=[V.IP2, V.IP1], peer1_members=[V.M2], peer2_members=[V.M1], peer1_pcid=12,
                                                 peer2_pcid=11)])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    w = first_write(ctrl.calls)
    for serial in (V.SN1, V.SN2):
        assert reads(ctrl.calls, POLICIES, serial, w) == 1, serial      # before: 2 (generic + vPC compare)
        assert reads(ctrl.calls[w:], POLICIES, serial) >= 1, serial     # the post-deploy verification still reads its own
    # each serial kept its own Po number and member (the base result of the swapped creation)
    nv = CI.sent_nv(ctrl)
    assert (nv["PEER1_PCID"], nv["PEER2_PCID"]) == ("11", "12") and nv["PEER1_MEMBER_INTERFACES"] == V.M1
    assert "port-channel11" in ctrl.nodes[V.SN1] and "port-channel12" in ctrl.nodes[V.SN2]


def test_a_failed_generic_policy_read_is_not_reused_the_vpc_reader_reads_again_and_judges_it():
    """SN2's generic policy read fails once: nothing is recorded, the vPC reader reads SN2 again (fresh) and the creation proceeds;
    SN1's complete read is still reused. A failed read is never taken as an empty policy list."""

    class OnceFailing(RD.CanaryController):
        def __call__(self, mod, method, path, data=None):
            if POLICIES + V.SN2 in path and not getattr(self, "failed_once", False):
                self.failed_once = True
                self.calls.append((method, path, data))
                return {"RETURN_CODE": 500, "MESSAGE": "x", "DATA": {}}
            return super(OnceFailing, self).__call__(mod, method, path, data)

    ctrl = OnceFailing().seed_baseline()
    V.create_previews(ctrl)
    status, result = V.run_vpc(ctrl, [V.vpc_item()])
    w = first_write(ctrl.calls) if status == "exit" else len(ctrl.calls)
    assert reads(ctrl.calls, POLICIES, V.SN2, w) >= 2, "the failed generic read was not reused as a state"
    assert reads(ctrl.calls, POLICIES, V.SN1, w) == 1


def test_a_policy_read_failing_for_the_vpc_reader_as_well_still_refuses_with_its_peer_named():
    """Both reads of SN2's policies fail: the existing refusal (peer and stage named, nothing written) is unchanged."""
    ctrl = RD.CanaryController().seed_baseline()
    ctrl.canary_failures.add(POLICIES + V.SN2)
    got = RD.refused(ctrl)
    assert any(V.SN2 in l and "switch policy list" in l for l in got), got
    assert not any(V.SN1 in l and "switch policy list" in l for l in got), got


def test_an_unchanged_vpc_repeat_still_reads_and_writes_nothing():
    pcids = ("11", "12")
    ctrl = CI.seeded(pcids)
    V.converged_previews(ctrl)
    CI.remap(ctrl, pcids)
    status, result = V.run_vpc(ctrl, [V.vpc_item(peer1_pcid=11, peer2_pcid=12)])
    assert status == "exit" and result["changed"] is False and ctrl.writes() == [], result.get("msg")
    for serial in (V.SN1, V.SN2):
        assert reads(ctrl.calls, POLICIES, serial) == 1, serial          # before: 2
        assert reads(ctrl.calls, "config-preview/", serial) == 1, serial  # the prior gate keeps its fresh preview


def test_a_description_update_keeps_its_modify_and_deploy_and_both_peers_new_text():
    pcids = ("11", "12")
    ctrl = CI.seeded(pcids, descs=("base-a", "base-b"))
    ctrl.vpc_previews[V.SN1] = [V.converged_preview(V.SN1, V.M1, desc="base-a"), V.description_preview(V.SN1, V.M1, "base-a", "new-a")]
    ctrl.vpc_previews[V.SN2] = [V.converged_preview(V.SN2, V.M2, desc="base-b"), V.description_preview(V.SN2, V.M2, "base-b", "new-b")]
    CI.remap(ctrl, pcids)
    status, result = V.run_vpc(ctrl, [V.vpc_item(peer1_pcid=11, peer2_pcid=12, peer1_description="new-a", peer2_description="new-b")],
                               state="replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.modifies()) == 1 and len(ctrl.deploys()) == 1
    assert ctrl.nodes[V.SN1]["port-channel11"]["nvPairs"]["DESC"] == "new-a" and ctrl.nodes[V.SN2]["port-channel12"]["nvPairs"]["DESC"] == "new-b"


class _ReuseObj(object):
    def __init__(self):
        self.have_all_cached_snos, self.have_all_failed_snos = set(), set()
        self.intf_detail_cached_snos, self.intf_detail_fetch_failed_snos = set(), set()

    @staticmethod
    def _dcnm_intf_authority_key(serial):
        return serial


def test_prewrite_records_are_per_physical_serial_dropped_on_failure_and_closed_by_sending():
    obj = _ReuseObj()
    module.pvlan_prewrite_note(obj, "policies", "SNA", True, [{"x": 1}])
    module.pvlan_prewrite_note(obj, "policies", "SNA~SNB", True, [{"x": 2}])   # a pair read is never recorded
    assert module.pvlan_prewrite_reusable(obj, "policies", "SNA") and not module.pvlan_prewrite_reusable(obj, "policies", "SNB")
    assert not module.pvlan_prewrite_reusable(obj, "policies", "SNA~SNB")
    module.pvlan_prewrite_note(obj, "policies", "SNA", False)                  # a later failed read drops the earlier one
    assert not module.pvlan_prewrite_reusable(obj, "policies", "SNA")
    module.pvlan_prewrite_note(obj, "detail", "SNA", True)
    assert not module.pvlan_prewrite_reusable(obj, "detail", "SNA"), "detail needs the serial still cached as authoritative"
    obj.intf_detail_cached_snos.add("SNA")
    assert module.pvlan_prewrite_reusable(obj, "detail", "SNA")
    obj.intf_detail_fetch_failed_snos.add("SNA")
    assert not module.pvlan_prewrite_reusable(obj, "detail", "SNA")
    obj.intf_detail_fetch_failed_snos.clear()
    obj._pvlan_sending = True
    assert not module.pvlan_prewrite_reusable(obj, "detail", "SNA")
    module.pvlan_prewrite_note(obj, "policies", "SNC", True, [])               # nothing is recorded once sending started
    obj._pvlan_sending = False
    assert not module.pvlan_prewrite_reusable(obj, "policies", "SNC")


def test_the_summary_is_always_read_again_by_the_vpc_reader():
    """Not reused on purpose: the generic summary of the OTHER peer rewrites this serial's have_all entries (pair union), so the
    pre-write summary of a serial is not provably complete when the vPC reader runs."""
    import inspect
    src = inspect.getsource(module.DcnmIntf.dcnm_intf_pvlan_vpc_read_serial)
    assert "if self.dcnm_intf_get_have_all_with_sno(serial):" in src and 'pvlan_prewrite_reusable(self, "summary"' not in src
