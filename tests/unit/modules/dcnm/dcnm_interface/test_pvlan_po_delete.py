"""Deletion of an owned PVLAN port-channel: readback verification, release and confirmed mark-delete."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P
from ansible.module_utils.connection import ConnectionError as AnsibleConnectionError

from .helpers.ethernet_controller import IF7
from .helpers.ethernet_controller import TRUNK
from .helpers.ethernet_controller import run
from .helpers.ethernet_controller import trunk_host_nv
from .helpers.port_channel_controller import PoLifecycleController
from .helpers.port_channel_controller import create_preview
from .helpers.port_channel_controller import del_item
from .helpers.port_channel_controller import delete_preview
from .helpers.port_channel_controller import item
from .helpers.port_channel_controller import markdelete_ok
from .helpers.port_channel_controller import PO
from .helpers.port_channel_controller import PO_MEMBER
from .helpers.ethernet_controller import SWITCH_IP
from .helpers.port_channel_release import DETAIL
from .helpers.port_channel_release import ERROR as PO_RELEASE_ERROR
from .helpers.port_channel_release import MEM
from .helpers.port_channel_release import PO as PO_RELEASE_PO
from .helpers.port_channel_release import POLICIES as PO_RELEASE_POLICIES
from .helpers.port_channel_release import PO_NAME
from .helpers.port_channel_release import RELEASED
from .helpers.port_channel_release import ReleaseController
from .helpers.port_channel_release import SUMMARY as PO_RELEASE_SUMMARY
from .helpers.port_channel_release import delete
from .helpers.port_channel_release import entry
from .helpers.port_channel_release import owned_ctrl
from .helpers.port_channel_release import stage
from .helpers.port_channel_release import MARKDELETE
from .helpers.port_channel_release import PO as PO_DELETE_OUTCOME_PO


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_po_g2_delete_verify.py
# The post-deletion readback of a PVLAN port-channel must distinguish "release verified" from "release could not be
# verified".
#
# NOT LIVE TESTED. Real main() in state `deleted`; only the controller boundary is intercepted, through the EXISTING harness
# (FakeController -> PoController -> PoLifecycleController). After the mark-delete, this controller can answer the
# interface-summary and/or policy-list reads with HTTP 500 for a given number of HTTP calls. The module's bounded GET retries each
# summary read 3 times (_dcnm_intf_get_with_retries), so one failed verifier attempt = 3 failed HTTP calls. Every scenario also
# asserts that no write other than the one mark-delete and the one deploy was sent (no rewrite of the member, no second deploy, no
# recovery write). Previews are SYNTHETIC (same as the deletion tests).
#
# The fail-before is the earlier module, which passed the all-summary-reads-fail scenario as a SUCCESS.
# ====================================================================================================
SUMMARY = "/rest/interface/detail?serialNumber="
POLICIES = "/control/policies/switches/"
# Host, the mode whose creation is measured; the creation of the other modes is refused before any write.
MODE = "host"
LINES = ["switchport private-vlan host-association 2210 2212"]
ASSOC = [{"primary_vlan": 2210, "secondary_vlan": 2212}]
ERROR = {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}


class ReadbackController(PoLifecycleController):
    """After the delete DEPLOY (so that the post-deploy verifier, not the pre-deploy member release, is what meets
    them): the next `fail_summary` summary GETs and `fail_policies` policy-list GETs answer 500. `keep_parent` leaves the
    port-channel listed after the mark-delete (the controller did not remove it)."""

    def __init__(self):
        super(ReadbackController, self).__init__()
        self.after_delete = False
        self.after_deploy = False
        self.fail_summary = 0
        self.fail_policies = 0
        self.keep_parent = False
        self.summary_reads_after_delete = 0
        self.policy_reads_after_delete = 0

    def __call__(self, mod, method, path, data=None):
        if method == "POST" and path.endswith("/rest/globalInterface/deploy"):
            self.after_deploy = True
        if self.after_deploy and method == "GET" and SUMMARY in path:
            self.summary_reads_after_delete += 1
            if self.fail_summary:
                self.fail_summary -= 1
                self.calls.append((method, path, data))
                return dict(ERROR)
        if self.after_deploy and method == "GET" and POLICIES in path:
            self.policy_reads_after_delete += 1
            if self.fail_policies:
                self.fail_policies -= 1
                self.calls.append((method, path, data))
                return dict(ERROR)
        if method == "DELETE" and path.endswith("/rest/interface/markdelete"):
            self.after_delete = True
            if self.keep_parent:
                self.calls.append((method, path, data))
                return markdelete_ok(data)
        return super(ReadbackController, self).__call__(mod, method, path, data)


def deleted_ctrl(**knobs):
    """A host port-channel created through main() (same steps as the `created` helper, on this controller),
    then a fresh invocation ready for `deleted`."""
    ctrl = ReadbackController()
    ctrl.detail[IF7] = {"policy": TRUNK, "nvPairs": trunk_host_nv(IF7)}
    ctrl.previews = [create_preview(MODE, LINES)]
    status, result = run(ctrl, [item(MODE, pvlan_association=ASSOC)], state="replaced")
    assert status == "exit" and result["changed"] is True, result
    ctrl.detail[IF7] = {
        "policy": PO_MEMBER,
        "nvPairs": {
            "PO_ID": PO,
            "PC_MODE": "active",
            "PVLAN_MODE": MODE,
            "CDP_ENABLE": "true",
            "lldpTransmit": "false",
            "lldpReceive": "false",
            "LACP_PORT_PRIO": "32768",
            "LACP_RATE": "normal",
            "DESC": "",
            "CONF": "",
            "ADMIN_STATE": "false",
            "INTF_NAME": IF7,
        },
    }
    ctrl.next_invocation()
    ctrl.calls = []
    ctrl.after_deploy = False  # the creation above deployed; only the deletion's deploy arms the read failures
    for k, v in knobs.items():
        setattr(ctrl, k, v)
    ctrl.previews = [delete_preview(MODE, LINES)]
    return ctrl


def only_the_deletion_was_written(ctrl):
    writes = [c for c in ctrl.calls if c[0] in ("POST", "PUT", "DELETE") and "/config-preview" not in c[1]]
    kinds = sorted(("markdelete" if c[1].endswith("/rest/interface/markdelete") else "deploy" if "deploy" in c[1] else c[1]) for c in writes)
    return kinds == ["deploy", "markdelete"]


def only_the_markdelete_was_written(ctrl):
    """A problem found by the pre-deploy member release stops the run after the mark-delete: no modify, no deploy."""
    writes = [c for c in ctrl.calls if c[0] in ("POST", "PUT", "DELETE") and "/config-preview" not in c[1]]
    return [c[1].rsplit("/", 2)[-2] + "/" + c[1].rsplit("/", 1)[-1] for c in writes] == ["interface/markdelete"]


def test_all_summary_reads_fail_is_an_error_never_a_verified_deletion():
    ctrl = deleted_ctrl(fail_summary=10**6)
    status, result = run(ctrl, [del_item()], state="deleted")
    assert status == "fail", "six failed summary reads must not end as a successful deletion"
    assert "release could not be verified after 6 readback attempts" in result["msg"]
    assert "the interface summary could not be read authoritatively" in result["msg"]
    # The reads are counted after the delete deploy; one summary read before the verifier is not one of its attempts.
    assert ctrl.summary_reads_after_delete >= 6 * 3, "6 verifier attempts x 3 bounded GET retries"
    assert only_the_deletion_was_written(ctrl), "no rewrite, no second deploy, no recovery write"
    assert PO not in ctrl.detail and ctrl.detail[IF7]["policy"] == TRUNK, "the controller state is left as it is"


def test_transient_summary_failures_then_a_verified_release_succeed():
    ctrl = deleted_ctrl(fail_summary=2 * 3)  # the first two verifier attempts fail, the third reads authoritatively
    status, result = run(ctrl, [del_item()], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.summary_reads_after_delete >= 2 * 3 + 1
    assert only_the_deletion_was_written(ctrl)


def test_a_port_channel_that_stays_listed_is_an_error():
    # Found by the member release BEFORE any deploy (it proves the parent absent first), not by the post-deploy verifier.
    ctrl = deleted_ctrl(keep_parent=True)
    status, result = run(ctrl, [del_item()], state="deleted")
    assert status == "fail" and "the port-channel is still listed" in result["msg"] and "No deployment request was sent" in result["msg"]
    assert only_the_markdelete_was_written(ctrl)


def test_a_policy_list_that_cannot_be_read_is_an_error():
    ctrl = deleted_ctrl(fail_policies=10**6)
    status, result = run(ctrl, [del_item()], state="deleted")
    assert status == "fail" and "the switch policy list could not be read authoritatively" in result["msg"]
    assert ctrl.policy_reads_after_delete == 6, "one fresh policy-list read per verifier attempt"
    assert only_the_deletion_was_written(ctrl)


def test_a_persistent_child_policy_residue_is_an_error():
    ctrl = deleted_ctrl()
    ctrl.policies_extra = [
        {
            "entityName": IF7,
            "entityType": "INTERFACE",
            "templateName": "int_eth",
            "source": PO,
            "deleted": False,
            "policyId": "POLICY-990001",
            "priority": 512,
            "serialNumber": "x",
        }
    ]
    status, result = run(ctrl, [del_item()], state="deleted")
    # The surviving child claim is found by the member release BEFORE any deploy.
    assert status == "fail" and "live policies still reference the port-channel" in result["msg"]
    assert only_the_markdelete_was_written(ctrl)


def test_the_normal_deletion_still_succeeds_with_no_extra_write():
    ctrl = deleted_ctrl()
    status, result = run(ctrl, [del_item()], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.summary_reads_after_delete >= 1 and ctrl.policy_reads_after_delete == 1
    assert only_the_deletion_was_written(ctrl)
    assert PO not in ctrl.detail and ctrl.detail[IF7]["policy"] == TRUNK


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_po_g4_release.py
# Deletion of an owned PVLAN host port-channel without enabling its member.
#
# After the accepted mark-delete and BEFORE any deploy, the released standalone member's ADMIN_STATE is set to "false" with its
# complete writable nvPairs (legacy interface/modify), then the normal gate, deploy and deletion verification run.
#
# MEASURED inputs (fixtures/pvlan_po_create_update.json#pvlan_po_h1_measured): the parent/member intents before the deletion, the member AS RELEASED by the
# controller after the mark-delete (int_trunk_host, 55 nvPairs, ADMIN_STATE "true", pending `no shutdown`), and the state after a
# manual correction (ADMIN_STATE "false", In-Sync, 0 pending, member expected/running trunk + shutdown).
#
# SIMULATED, NOT LIVE-MEASURED: the controller's answer to the legacy interface/modify of the released member (the harness answers
# 207 with one SUCCESS item and stores the sent nvPairs; the measured fix was a GUI save, not this API), and the preview after that
# modify (the measured corrected preview is used: same member state, Po never deployed). Real main(); only the controller boundary is
# intercepted (existing harness). The serial is the harness one.
# ====================================================================================================
# ------------------------------------------------------------------ the measured lifecycle, corrected
def test_g4_corrects_the_measured_admin_up_release_before_the_deploy_in_order():
    ctrl = owned_ctrl()
    status, result = delete(ctrl)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.write_kinds() == ["markdelete", "modify", "deploy"]
    assert ctrl.phase_order() == ["read", "markdelete", "read", "modify", "read", "preview", "deploy", "read"], ctrl.phase_order()
    assert PO_RELEASE_PO not in ctrl.detail and ctrl.detail[MEM]["policy"] == TRUNK and ctrl.detail[MEM]["nvPairs"]["ADMIN_STATE"] == "false"
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
        ({"fail_after_delete": {PO_RELEASE_SUMMARY}}, "the interface summary could not be read authoritatively"),
        ({"fail_after_delete": {PO_RELEASE_POLICIES}}, "the switch policy list could not be read authoritatively"),
        ({"fail_after_delete": {DETAIL}}, "could not be read authoritatively"),
    ],
)
def test_an_unprovable_release_stops_after_the_markdelete_with_no_member_modify_or_deploy(knobs, needle):
    ctrl = owned_ctrl(**knobs)
    status, result = delete(ctrl)
    assert status == "fail" and needle in result["msg"], result.get("msg")
    assert "member release failed while proving the released member before any member write" in result["msg"]
    # The report separates CONFIRMED writes from writes with an UNVERIFIED outcome.
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
        if ctrl.deploys() and method == "GET" and PO_RELEASE_SUMMARY in path:
            ctrl.calls.append((method, path, data))
            return dict(PO_RELEASE_ERROR)
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


def test_a_member_whose_admin_state_is_unknown_before_the_deletion_is_refused_before_the_markdelete():
    # An up member is released to the fabric default (test_pvlan_member_admin.py); unknown stays refused
    ctrl = owned_ctrl()
    ctrl.detail[MEM]["nvPairs"]["ADMIN_STATE"] = "maybe"
    status, result = delete(ctrl)
    assert status == "fail" and "unknown administrative state" in result["msg"] and ctrl.writes() == []


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_po_g4r1_delete_outcome.py
# The mark-delete of a registered PVLAN port-channel deletion must be CONFIRMED before anything else.
#
# Reproduces an uncertain mark-delete through real main() and the existing ReleaseController: the mark-delete APPLIES the measured
# release (the member becomes an int_trunk_host with ADMIN_STATE "true") but its ANSWER is not the measured success. The earlier code
# retried that DELETE 20 times, the generic parser turned the HTTP 500 into a synthetic 200/OK (changed=False), the member release
# was skipped and, with a down-looking preview, one deploy was sent. Now: one attempt, measured answer only; any other answer stops the
# run before any member modify or deploy, whatever a later preview would look like.
#
# The error answers below are SYNTHETIC (none was observed live); the success answer is the MEASURED one (markdelete_ok).
# ====================================================================================================
SERIAL = "SAL1819SAN8"
UNVERIFIED = [
    ("http500_empty_list", {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": []}),
    ("ok_without_value", {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {"message": "Interface deleted successfully"}}),
    ("ok_list_data", {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": []}),
    (
        "ok_foreign_item",
        {
            "RETURN_CODE": 200,
            "MESSAGE": "OK",
            "DATA": {
                "message": "Interface deleted successfully",
                "value": [{"interfaceType": "INTERFACE_PORT_CHANNEL", "serialNumber": SERIAL, "IfName": "Port-channel503"}],
            },
        },
    ),
    (
        "ok_other_message",
        {
            "RETURN_CODE": 200,
            "MESSAGE": "OK",
            "DATA": {"message": "Request accepted",
                     "value": [{"interfaceType": "INTERFACE_PORT_CHANNEL", "serialNumber": SERIAL, "IfName": PO_DELETE_OUTCOME_PO}]},
        },
    ),
    (
        "multi_status_error_item",
        {"RETURN_CODE": 207, "MESSAGE": "Multi-Status",
         "DATA": [{"reportItemType": "ERROR", "message": "synthetic", "entity": "%s~%s" % (SERIAL, PO_DELETE_OUTCOME_PO)}]},
    ),
    (
        "not_ok_message",
        {
            "RETURN_CODE": 200,
            "MESSAGE": "Accepted",
            "DATA": {"message": "Interface deleted successfully",
                     "value": [{"interfaceType": "INTERFACE_PORT_CHANNEL", "serialNumber": SERIAL, "IfName": PO_DELETE_OUTCOME_PO}]},
        },
    ),
]


def transport_answering(ctrl, answer):
    """The probe's transport: the mark-delete IS applied (measured release) but answers `answer`; an exception class
    is raised instead when `answer` is one."""

    def transport(mod, method, path, data=None):
        if method == "DELETE" and path.endswith(MARKDELETE):
            ReleaseController.__call__(ctrl, mod, method, path, data)
            if isinstance(answer, type) and issubclass(answer, Exception):
                raise answer("synthetic transport failure")
            return dict(answer)
        return ReleaseController.__call__(ctrl, mod, method, path, data)

    return transport


def run_with(ctrl, answer):
    return run(transport_answering(ctrl, answer), [{"name": "po502", "switch": [SWITCH_IP], "deploy": True}], state="deleted")


@pytest.mark.parametrize("preview_fixture", ["HR-post", "H1-verify"])
@pytest.mark.parametrize("label, answer", UNVERIFIED + [("transport_exception", AnsibleConnectionError)])
def test_an_unverified_markdelete_outcome_stops_with_one_delete_and_nothing_else(label, answer, preview_fixture):
    ctrl = owned_ctrl(previews=[entry(preview_fixture)])
    status, result = run_with(ctrl, answer)
    assert status == "fail", label
    assert "at the mark-delete (outcome UNVERIFIED; not retried)" in result["msg"], result.get("msg")
    assert "Confirmed writes: none" in result["msg"] and "mark-delete of Port-channel502 (it may or may not have been applied" in result["msg"]
    assert ctrl.write_kinds() == ["markdelete"], "ONE delete, no member modify, no deploy (%s)" % ctrl.write_kinds()
    assert not any("/config-preview/" in p for _m, p, _d in ctrl.calls), "nothing after an unverified mark-delete, not even the gate"
    record = result["pvlan_po_release"][-1]
    assert record["confirmed_writes"] == [] and len(record["uncertain_writes"]) == 1
    assert ctrl.detail[MEM]["nvPairs"]["ADMIN_STATE"] == "true", "the (applied) release is left as is for the scoped recovery"


def test_the_measured_markdelete_answer_is_confirmed_and_enters_the_release_before_the_deploy():
    ctrl = owned_ctrl()
    status, result = delete(ctrl)
    assert status == "exit", result.get("msg")
    assert ctrl.write_kinds() == ["markdelete", "modify", "deploy"]
    assert ctrl.phase_order() == ["read", "markdelete", "read", "modify", "read", "preview", "deploy", "read"]


def test_the_outcome_check_accepts_only_the_measured_success_shape():
    measured = {
        "RETURN_CODE": 200,
        "MESSAGE": "OK",
        "DATA": {
            "message": "Interface deleted successfully",
            "value": [{"interfaceType": "INTERFACE_PORT_CHANNEL", "serialNumber": "SAL0000PO01", "IfName": "Port-channel502"}],
        },
    }
    assert P.po_markdelete_outcome_problems(measured, "SAL0000PO01", "Port-channel502") == []
    assert P.po_markdelete_outcome_problems(measured, "SAL0000PO01", "port-channel502") == []
    for _label, answer in UNVERIFIED:
        assert P.po_markdelete_outcome_problems(answer, SERIAL, PO_DELETE_OUTCOME_PO), _label
    assert P.po_markdelete_outcome_problems(None, SERIAL, PO_DELETE_OUTCOME_PO)


def test_two_registered_pvlan_deletions_are_sent_one_request_each():
    ctrl = owned_ctrl()
    ctrl.detail["Port-channel503"] = dict(
        ctrl.detail[PO_DELETE_OUTCOME_PO],
        nvPairs=dict(ctrl.detail[PO_DELETE_OUTCOME_PO]["nvPairs"], PO_ID="Port-channel503", MEMBER_INTERFACES="Ethernet1/11"))
    ctrl.po_names.add("Port-channel503")
    ctrl.detail["Ethernet1/11"] = dict(ctrl.detail[MEM], nvPairs=dict(ctrl.detail[MEM]["nvPairs"], PO_ID="Port-channel503", INTF_NAME="Ethernet1/11"))
    status, result = run(
        ctrl, [{"name": "po502", "switch": [SWITCH_IP], "deploy": True}, {"name": "po503", "switch": [SWITCH_IP], "deploy": True}], state="deleted"
    )
    deletes = [c for c in ctrl.calls if c[0] == "DELETE" and c[1].endswith(MARKDELETE)]
    assert len(deletes) == 2 and all(len(__import__("json").loads(c[2])) == 1 for c in deletes), "one port-channel per request"


def test_a_non_pvlan_port_channel_deletion_keeps_the_generic_path():
    ctrl = PoLifecycleController()
    ctrl.detail["Port-channel10"] = {"policy": "int_port_channel_trunk_host", "nvPairs": {"MEMBER_INTERFACES": "Ethernet1/8", "PO_ID": "Port-channel10"}}
    ctrl.po_names.add("Port-channel10")
    status, result = run(ctrl, [{"name": "po10", "switch": [SWITCH_IP], "deploy": True}], state="deleted")
    assert status == "exit" and "pvlan_po_release" not in result and "pvlan_gate" not in result
    assert len([c for c in ctrl.calls if c[0] == "DELETE"]) == 1


def test_markdelete_ok_helper_is_the_measured_shape():
    answer = markdelete_ok('[{"ifName": "Port-channel502", "serialNumber": "SAL0000PO01"}]')
    assert answer["DATA"]["value"] == [{"interfaceType": "INTERFACE_PORT_CHANNEL", "serialNumber": "SAL0000PO01", "IfName": "Port-channel502"}]
    assert TRUNK == "int_trunk_host"
