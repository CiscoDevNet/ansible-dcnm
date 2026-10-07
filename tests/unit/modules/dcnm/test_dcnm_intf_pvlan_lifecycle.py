"""Native Ethernet PVLAN: lifecycle, response outcomes, pre-deploy gate and coexistence.

Real main() through test_dcnm_intf_pvlan_harness. Case IDs E09-E14 refer to the design matrix.
Assertions are made at the sender boundary: the ordered request log of the fake controller.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import ast
import copy
import os

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_ENABLED_PATCH_VERSIONS

from .test_dcnm_intf_pvlan_harness import (
    DEPLOY,
    FIXTURE,
    IF7,
    IF8,
    MODIFY,
    PREVIEW_MARK,
    PVLAN,
    RECOMPUTE_FLAGS,
    SERIAL,
    TRUNK,
    FakeController,
    ok,
    authority,
    measured_preview,
    pending,
    preview,
    recreate_preview,
    reset_preview,
    pvlan_item,
    pvlan_nv,
    run,
    trunk_host_nv,
    trunk_item,
)

IF9 = "Ethernet1/9"
APPROVED_PATCH = sorted(GIE_ENABLED_PATCH_VERSIONS)[0]
TPROM_A11 = pvlan_nv("G6-M0a")
TPROM_BOTH = pvlan_nv("G6-M0b")
ADD_2212 = dict(pvlan_mode="trunk promiscuous", pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2212"}])


def ctrl(nv=TPROM_A11, policy=PVLAN, ifname=IF7):
    c = FakeController()
    c.detail[ifname] = {"policy": policy, "nvPairs": copy.deepcopy(nv)}
    return c


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
        # E3 (architect R2-02): the bulk capability cannot be verified without its POST probe,
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
def test_e13_registry_rows_and_resets_are_unchanged_and_carry_no_pvlan_binding():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "plugins", "module_utils", "gie_binding_table.py")
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
    assert (rows, resets, pvlan) == (234, 207, 0)


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
