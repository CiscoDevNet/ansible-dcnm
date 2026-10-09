"""PO G4 (Alpha, PR725-PVLAN-PO-PLAN-001): deletion of an owned PVLAN host port-channel without enabling its member.

Architect decision B (review/PO_G3_R1): after the accepted mark-delete and BEFORE any deploy, the released standalone
member's ADMIN_STATE is set to "false" with its complete writable nvPairs (legacy interface/modify), then the normal
gate, deploy and G2 verification run.

MEASURED inputs (fixtures/pvlan_po_h1_measured.json, Alpha4's live G2/R2 run): the parent/member intents before the
deletion (H1-post), the member AS RELEASED by the controller after the mark-delete (HR-post: int_trunk_host, 55 nvPairs,
ADMIN_STATE "true", pending `no shutdown`), and the state after the operator's correction (H1-verify: ADMIN_STATE "false",
In-Sync, 0 pending, member expected/running trunk + shutdown).

SIMULATED, NOT LIVE-MEASURED: the controller's answer to the legacy interface/modify of the released member (the harness
answers 207 with one SUCCESS item and stores the sent nvPairs; the measured fix was a GUI save, not this API), and the
preview after that modify (the measured H1-verify preview is used: same member state, Po never deployed, as in the HR
incident). Real main(); only the controller boundary is intercepted (existing harness). The serial is the harness one.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import os

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .test_dcnm_intf_pvlan_harness import SWITCH_IP, TRUNK, preview, run
from .test_dcnm_intf_pvlan_po_g1 import PoLifecycleController, markdelete_ok

FIXTURE = json.load(open(os.path.join(os.path.dirname(__file__), "fixtures", "pvlan_po_h1_measured.json")))
PO_NAME, MEM = "port-channel502", "Ethernet1/10"
PO = "Port-channel502"
PO_MEMBER = "int_port_channel_pvlan_member"
MARKDELETE = "/rest/interface/markdelete"
MODIFY = "/rest/interface/modify"
DEPLOY = "/rest/globalInterface/deploy"
SUMMARY = "/rest/interface/detail?serialNumber="
POLICIES = "/control/policies/switches/"
DETAIL = "/rest/interface?serialNumber="
ERROR = {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}


def stage(name):
    return copy.deepcopy(FIXTURE["stages"][name])


def harness_nv(nv):
    """Measured nvPairs for the harness: only POLICY_ID dropped (the harness numbers its own policies)."""
    return dict((k, v) for k, v in nv.items() if k != "POLICY_ID")


def entry(name):
    pf = stage(name)["preview_forced"]
    return {
        "RETURN_CODE": 200,
        "MESSAGE": "OK",
        "DATA": [preview(pf["pendingConfig"], running=pf["runningConfig_stanzas"], expected=pf["expectedConfig_stanzas"])["DATA"][0]],
    }


RELEASED = harness_nv(stage("HR-post")["intent"][MEM]["nvPairs"])  # MEASURED: int_trunk_host, ADMIN_STATE "true"


class ReleaseController(PoLifecycleController):
    """The existing Po harness + the MEASURED release: the mark-delete removes the parent and its member policies and
    leaves the member as `released_nv` (default: the measured HR-post int_trunk_host, ADMIN_STATE "true").

    Knobs, all after the mark-delete: `fail_after_delete` = path markers answered 500; `extra_after_delete` = live
    policies that appear; `released_policy` = the member's template; `keep_parent`; `modify_mode` in
    {"store" (default harness: 207 SUCCESS, store the sent nvPairs), "lossy" (store but lose/alter a field),
    "keep_up" (answer SUCCESS but leave ADMIN_STATE "true")}; `modify_responses` (harness) for ERROR/incomplete answers."""

    def __init__(self):
        super(ReleaseController, self).__init__()
        self.release_member = False
        self.after_delete = False
        self.released_nv = copy.deepcopy(RELEASED)
        self.released_policy = TRUNK
        self.fail_after_delete = set()
        self.extra_after_delete = []
        self.keep_parent = False
        self.modify_mode = "store"
        self.lossy_change = ("DEBOUNCE_TIMER", None)

    def __call__(self, mod, method, path, data=None):
        if self.after_delete and method == "GET" and any(m in path for m in self.fail_after_delete):
            self.calls.append((method, path, data))
            return dict(ERROR)
        if method == "DELETE" and path.endswith(MARKDELETE):
            self.calls.append((method, path, data))
            self.after_delete = True
            if not self.keep_parent:
                self.detail.pop(PO, None)
                self.po_names.discard(PO)
            self.detail[MEM] = {"policy": self.released_policy, "nvPairs": copy.deepcopy(self.released_nv)}
            self.policies_extra = list(self.extra_after_delete)
            return markdelete_ok(data)
        resp = super(ReleaseController, self).__call__(mod, method, path, data)
        if method == "POST" and path.endswith(MODIFY) and MEM in self.detail:
            nv = self.detail[MEM]["nvPairs"]
            if self.modify_mode == "lossy":
                key, value = self.lossy_change
                if value is None:
                    nv.pop(key, None)
                else:
                    nv[key] = value
            elif self.modify_mode == "keep_up":
                nv["ADMIN_STATE"] = "true"
        return resp

    def writes(self):
        return [c for c in self.calls if c[0] in ("POST", "PUT", "DELETE") and "/config-preview" not in c[1]]

    def write_kinds(self):
        out = []
        for c in self.writes():
            out.append("markdelete" if c[1].endswith(MARKDELETE) else "modify" if c[1].endswith(MODIFY) else "deploy" if c[1].endswith(DEPLOY) else c[1])
        return out

    def modify_bodies(self):
        return [json.loads(c[2]) for c in self.calls if c[0] == "POST" and c[1].endswith(MODIFY)]

    def phase_order(self):
        """The ordered phases of the deletion invocation: writes, the fresh reads between them and the preview."""
        out = []
        for m, p, _d in self.calls:
            if m == "DELETE" and p.endswith(MARKDELETE):
                out.append("markdelete")
            elif m == "POST" and p.endswith(MODIFY):
                out.append("modify")
            elif m == "POST" and p.endswith(DEPLOY):
                out.append("deploy")
            elif "/config-preview/" in p:
                out.append("preview")
            elif m == "GET" and (SUMMARY in p or POLICIES in p or DETAIL in p):
                out.append("read")
        compact = []
        for x in out:
            if not (compact and compact[-1] == x == "read"):
                compact.append(x)
        return compact


def owned_ctrl(**knobs):
    """The MEASURED H1-post parent and member, ready for `deleted` (parent/member intents + the policy shape)."""
    ctrl = ReleaseController()
    ctrl.detail[PO] = {"policy": P.PO_HOST_POLICY, "nvPairs": harness_nv(stage("H1-post")["intent"][PO_NAME]["nvPairs"])}
    ctrl.po_names.add(PO)
    ctrl.detail[MEM] = {"policy": PO_MEMBER, "nvPairs": harness_nv(stage("H1-post")["intent"][MEM]["nvPairs"])}
    for k, v in knobs.items():
        setattr(ctrl, k, v)
    if "previews" not in knobs:
        ctrl.previews = [entry("H1-verify")]
    return ctrl


def delete(ctrl):
    return run(ctrl, [{"name": "po502", "switch": [SWITCH_IP], "deploy": True}], state="deleted")


# ------------------------------------------------------------------ the measured lifecycle, corrected
def test_g4_corrects_the_measured_admin_up_release_before_the_deploy_in_order():
    ctrl = owned_ctrl()
    status, result = delete(ctrl)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.write_kinds() == ["markdelete", "modify", "deploy"]
    assert ctrl.phase_order() == ["read", "markdelete", "read", "modify", "read", "preview", "deploy", "read"], ctrl.phase_order()
    assert PO not in ctrl.detail and ctrl.detail[MEM]["policy"] == TRUNK and ctrl.detail[MEM]["nvPairs"]["ADMIN_STATE"] == "false"
    record = [r for r in result["pvlan_po_release"] if r.get("member") == MEM][0]
    assert record["released_admin_state"] == "true" and "ADMIN_STATE true -> false" in record["member_modify"]


def test_the_member_modify_carries_every_measured_writable_nvpair_and_changes_only_admin_state():
    ctrl = owned_ctrl()
    assert delete(ctrl)[0] == "exit"
    bodies = ctrl.modify_bodies()
    assert len(bodies) == 1 and len(bodies[0]) == 1, "ONE legacy modify, ONE interface"
    payload = bodies[0][0]
    intf = payload["interfaces"][0]
    assert payload["policy"] == TRUNK and intf["ifName"] == MEM and intf["interfaceType"] == "INTERFACE_ETHERNET"
    measured = stage("HR-post")["intent"][MEM]["nvPairs"]
    writable = dict((k, v) for k, v in measured.items() if k not in P.PO_RELEASE_METADATA)
    expected = dict(writable, ADMIN_STATE="false")
    assert intf["nvPairs"] == expected, "the complete writable set (50 measured keys), only ADMIN_STATE changed"
    assert len(expected) == 50 and not set(intf["nvPairs"]) & P.PO_RELEASE_METADATA
    assert "MARK_DELETED" not in intf["nvPairs"], "the GUI-added MARK_DELETED is metadata, never guessed"


def test_a_release_already_down_is_not_modified():
    ctrl = owned_ctrl(released_nv=dict(RELEASED, ADMIN_STATE="false"))
    status, result = delete(ctrl)
    assert status == "exit", result.get("msg")
    assert ctrl.write_kinds() == ["markdelete", "deploy"]
    assert [r for r in result["pvlan_po_release"] if r.get("member") == MEM][0]["member_modify"].startswith("not needed")


def test_a_stale_admin_up_preview_after_the_modify_stops_before_the_deploy():
    """The measured HR-post preview (expected member WITHOUT shutdown, pending `no shutdown`) after the correction: the
    gate refuses, the modify stays done, nothing is deployed."""
    ctrl = owned_ctrl(previews=[entry("HR-post")])
    status, result = delete(ctrl)
    assert status == "fail" and "'no shutdown'" in result["msg"] and "No deployment request was sent" in result["msg"]
    assert ctrl.write_kinds() == ["markdelete", "modify"]


# ------------------------------------------------------------------ ownership / claims / reads after the mark-delete
@pytest.mark.parametrize(
    "knobs, needle",
    [
        ({"released_policy": "int_access_host"}, "not a readable int_trunk_host"),
        (
            {
                "extra_after_delete": [
                    {
                        "entityName": MEM,
                        "entityType": "INTERFACE",
                        "templateName": "Config_Profile",
                        "source": "OVERLAY",
                        "deleted": False,
                        "policyId": "POLICY-990009",
                        "priority": 500,
                        "serialNumber": "x",
                    }
                ]
            },
            "not a sole direct int_trunk_host",
        ),
        (
            {
                "extra_after_delete": [
                    {
                        "entityName": MEM,
                        "entityType": "INTERFACE",
                        "templateName": "int_trunk_host",
                        "source": "",
                        "deleted": False,
                        "policyId": "POLICY-990010",
                        "priority": 500,
                        "serialNumber": "x",
                    }
                ]
            },
            "not a sole direct int_trunk_host",
        ),
        (
            {
                "extra_after_delete": [
                    {
                        "entityName": MEM,
                        "entityType": "INTERFACE",
                        "templateName": "int_eth",
                        "source": PO_NAME,
                        "deleted": False,
                        "policyId": "POLICY-990011",
                        "priority": 512,
                        "serialNumber": "x",
                    }
                ]
            },
            "live policies still reference the port-channel",
        ),
        ({"keep_parent": True}, "the port-channel is still listed"),
        ({"fail_after_delete": {SUMMARY}}, "the interface summary could not be read authoritatively"),
        ({"fail_after_delete": {POLICIES}}, "the switch policy list could not be read authoritatively"),
        ({"fail_after_delete": {DETAIL}}, "could not be read authoritatively"),
    ],
)
def test_an_unprovable_release_stops_after_the_markdelete_with_no_member_modify_or_deploy(knobs, needle):
    ctrl = owned_ctrl(**knobs)
    status, result = delete(ctrl)
    assert status == "fail" and needle in result["msg"], result.get("msg")
    assert "member release failed while proving the released member before any member write" in result["msg"]
    # G4-R1: the report separates CONFIRMED writes from writes with an UNVERIFIED outcome.
    assert "Confirmed writes: mark-delete of Port-channel502 (confirmed by its measured outcome)" in result["msg"]
    assert "Writes with an UNVERIFIED outcome: none" in result["msg"]
    assert ctrl.write_kinds() == ["markdelete"]


# ------------------------------------------------------------------ the modify outcome and the readback
@pytest.mark.parametrize(
    "response, needle",
    [
        (
            {
                "RETURN_CODE": 207,
                "MESSAGE": "Multi-Status",
                "DATA": [{"reportItemType": "ERROR", "message": "synthetic refusal", "entity": "SAL1819SAN8~Ethernet1/10"}],
            },
            "ERROR item",
        ),
        ({"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": []}, "no outcome item"),
        ({"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": {}}, "no per-item outcome list"),
        ({"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}, "the modify answered 500"),
    ],
)
def test_an_unverified_modify_outcome_stops_before_the_deploy(response, needle):
    ctrl = owned_ctrl(modify_responses=[response])
    status, result = delete(ctrl)
    assert status == "fail" and needle in result["msg"] and "at the member modify" in result["msg"], result.get("msg")
    assert ctrl.write_kinds() == ["markdelete", "modify"]


@pytest.mark.parametrize(
    "mode, change, needle",
    [
        ("lossy", ("DEBOUNCE_TIMER", None), "writable nvPair DEBOUNCE_TIMER was lost"),
        ("lossy", ("MTU", "default"), "writable nvPair MTU changed"),
        ("lossy", ("NEW_FIELD", "x"), "writable nvPair NEW_FIELD appeared"),
        ("keep_up", None, "ADMIN_STATE reads back 'true'"),
    ],
)
def test_a_mismatched_readback_stops_before_the_deploy(mode, change, needle):
    ctrl = owned_ctrl(modify_mode=mode)
    if change:
        ctrl.lossy_change = change
    status, result = delete(ctrl)
    assert status == "fail" and needle in result["msg"] and "at the member readback" in result["msg"], result.get("msg")
    assert ctrl.write_kinds() == ["markdelete", "modify"]


def test_classified_metadata_differences_are_tolerated_on_readback():
    before = stage("HR-post")["intent"][MEM]["nvPairs"]
    after = dict(stage("H1-verify")["intent"][MEM]["nvPairs"])  # MEASURED after the GUI fix: + MARK_DELETED, ADMIN false
    assert P.po_released_member_readback_problems(before, after) == []
    after["PRIORITY"], after["POLICY_ID"] = "450", "POLICY-1"
    assert P.po_released_member_readback_problems(before, after) == []


# ------------------------------------------------------------------ final verification
def test_an_exhausted_final_verification_after_a_corrected_release_fails_without_another_write():
    ctrl = owned_ctrl()
    original = ReleaseController.__call__

    def after_deploy_summary_fails(mod, method, path, data=None):
        if ctrl.deploys() and method == "GET" and SUMMARY in path:
            ctrl.calls.append((method, path, data))
            return dict(ERROR)
        return original(ctrl, mod, method, path, data)

    status, result = run(after_deploy_summary_fails, [{"name": "po502", "switch": [SWITCH_IP], "deploy": True}], state="deleted")
    assert status == "fail" and "could not be verified after 6 readback attempts" in result["msg"]
    assert ctrl.write_kinds() == ["markdelete", "modify", "deploy"], "no second cleanup after the deploy"


# ------------------------------------------------------------------ unsupported scope refused before any write
def test_a_member_holding_a_foreign_policy_is_refused_before_the_markdelete():
    ctrl = owned_ctrl()
    ctrl.policies_extra = [
        {
            "entityName": MEM,
            "entityType": "INTERFACE",
            "templateName": "Config_Profile",
            "source": "OVERLAY",
            "deleted": False,
            "policyId": "POLICY-990012",
            "priority": 500,
            "serialNumber": "x",
        }
    ]
    status, result = delete(ctrl)
    assert status == "fail" and "live policies are not exactly those of" in result["msg"] and ctrl.writes() == []


def test_a_member_whose_pvlan_policy_names_another_parent_is_refused_before_the_markdelete():
    ctrl = owned_ctrl()
    ctrl.detail[MEM]["nvPairs"]["PO_ID"] = "Port-channel503"
    status, result = delete(ctrl)
    assert status == "fail" and "is not the member of this port-channel" in result["msg"] and ctrl.writes() == []


def test_no_bulk_update_api_is_refused_before_the_markdelete():
    ctrl = owned_ctrl()
    status, result = run(ctrl, [{"name": "po502", "switch": [SWITCH_IP], "deploy": True}], state="deleted", bulk=False)
    assert status == "fail" and "bulk interface update API is not available" in result["msg"] and ctrl.writes() == []


def test_a_member_that_is_administratively_up_before_the_deletion_is_refused_before_the_markdelete():
    ctrl = owned_ctrl()
    ctrl.detail[MEM]["nvPairs"]["ADMIN_STATE"] = "true"
    status, result = delete(ctrl)
    assert status == "fail" and "not administratively down" in result["msg"] and ctrl.writes() == []
