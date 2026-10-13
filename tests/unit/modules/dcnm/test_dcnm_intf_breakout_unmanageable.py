"""Breakout creation on an unmanageable / pre-provisioned switch (upstream #732) together with the PR725 summary-authority guard.

Order in dcnm_intf_compare_want_and_have: an unmanageable switch is skipped first (recorded in `skipped`, nothing sent); a manageable
switch still needs an authoritative breakout summary before create / no-op is decided. The deleted/overridden path keeps its own guard.
Real main() through the existing PVLAN harness (FakeController: transport only), plus the real compare method for the mixed batch and
the deletion guard. Offline doubles; not live.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
from unittest import mock

import pytest

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

from . import test_dcnm_intf_pvlan_harness as H
from .test_dcnm_intf_have_fetch_contract import _assert_zero_mutating_calls, _stub

SKIP_REASON = "Switch is in preprovision state or not manageable"
BREAKOUT = "/rest/interface/breakout"
POLICIES = "/control/policies/switches/"
ITEM = {"name": "ethernet1/100", "type": "breakout", "switch": [H.SWITCH_IP], "profile": {"map": "10g-4x"}}


def drive(managable, policies_fail=False, policies=None):
    ctrl = H.FakeController()
    if policies_fail:
        ctrl.read_failures.add(POLICIES)
    if policies is not None:
        ctrl.policies_override = H.ok(policies)
    inventory = copy.deepcopy(H.INVENTORY)
    inventory[H.SWITCH_IP]["managable"] = managable
    with mock.patch.object(H, "INVENTORY", inventory):
        status, result = H.run(ctrl, [copy.deepcopy(ITEM)])
    return status, result, ctrl


def skipped(result):
    return [s for d in result.get("diff", []) for s in d.get("skipped", [])]


# ------------------------------------------------------------------ real main()
@pytest.mark.parametrize("policies_fail", [True, False], ids=["summary_unreadable", "summary_readable"])
def test_unmanageable_switch_is_skipped_without_any_write(policies_fail):
    status, result, ctrl = drive("False", policies_fail=policies_fail)
    assert status == "exit", result.get("msg")
    assert result["changed"] is False
    assert skipped(result) == [{"Name": "Ethernet1/100", "serialNumber": H.SERIAL, "Reason": SKIP_REASON}]  # the module's spelling
    assert ctrl.mutating() == []


def test_manageable_switch_with_unreadable_breakout_summary_is_still_refused_without_writes():
    status, result, ctrl = drive("True", policies_fail=True)
    assert status == "fail"
    assert result["msg"].startswith("Current breakout summary for {0} could not be read authoritatively".format(H.SERIAL))
    assert ctrl.mutating() == []


def test_manageable_switch_with_a_valid_summary_still_creates_the_breakout():
    status, result, ctrl = drive("True")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert skipped(result) == []
    posts = ctrl.requests("POST", BREAKOUT)
    assert len(posts) == 1 and ctrl.mutating() == posts
    body = json.loads(posts[0][2])
    sent = [(i["serialNumber"], i["ifName"].lower()) for entry in (body if isinstance(body, list) else [body])
            for i in (entry if isinstance(entry, list) else entry.get("interfaces", [entry]))]
    assert sent == [(H.SERIAL, "ethernet1/100")]


def test_manageable_switch_with_the_breakout_already_present_is_a_no_op():
    existing = {"templateName": "breakout_interface", "serialNumber": H.SERIAL, "entityName": "Ethernet1/100",
                "nvPairs": {"SLOT": "1", "PORT": "100", "MAP": "10g-4x"}}
    status, result, ctrl = drive("True", policies=[existing])
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.mutating() == []


# ------------------------------------------------------------------ real compare method: mixed batch and the deletion guard
def _compare_stub(state, want_breakout):
    s = _stub()
    s.want_breakout = want_breakout
    s.want = []
    s.have = []
    s.pb_input = []
    s.diff_create_breakout = []
    s.diff_delete_breakout = []
    s.pol_pc_member_types = {12: {}}
    s.dcnm_version = 12
    s.class_name = "DcnmIntf"
    s.log = mock.Mock()
    s.changed_dict = [{"skipped": []}]
    s.module.params = {"state": state}
    s.module.fail_json.side_effect = RuntimeError("fail_json")
    return s


def _want(ifname, serial):
    return {"policy": "breakout_interface", "interfaces": [{"ifName": ifname, "serialNumber": serial}]}


def test_mixed_batch_creates_only_on_the_manageable_switch_and_skips_the_other():
    # SN1 manageable with an authoritative (empty) breakout summary; SN2 unmanageable whose read failed.
    s = _compare_stub("merged", [_want("Ethernet1/1", "SN2"), _want("Ethernet1/1", "SN1")])
    s.have_breakout = [{"SN1": []}]
    s.have_breakout_cached_snos.add("SN1")
    s.have_breakout_failed_snos.add("SN2")
    with mock.patch.object(dcnm_interface, "dcnm_send") as sender:
        dcnm_interface.DcnmIntf.dcnm_intf_compare_want_and_have(s, "merged")
    assert s.diff_create_breakout == [[{"ifName": "Ethernet1/1", "serialNumber": "SN1"}]]
    assert s.changed_dict[0]["skipped"] == [{"Name": "Ethernet1/1", "serialNumber": "SN2", "Reason": SKIP_REASON}]
    s.module.fail_json.assert_not_called()
    _assert_zero_mutating_calls(sender)


def test_the_skip_does_not_bypass_the_deletion_guard():
    # overridden: the want side only names an unmanageable switch (skipped), but a breakout summary entry whose authority is
    # not established still refuses the deletion decision.
    s = _compare_stub("overridden", [_want("Ethernet1/1", "SN2")])
    s.have_breakout = [{"SN1": ["Ethernet1/9"]}]
    s.have_breakout_failed_snos.add("SN1")
    with mock.patch.object(dcnm_interface, "dcnm_send") as sender:
        with pytest.raises(RuntimeError, match="fail_json"):
            dcnm_interface.DcnmIntf.dcnm_intf_compare_want_and_have(s, "overridden")
    assert s.diff_delete_breakout == []
    assert "Current breakout summary for SN1" in s.module.fail_json.call_args[1]["msg"]
    _assert_zero_mutating_calls(sender)
