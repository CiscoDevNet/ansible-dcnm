"""PO G2 (Alpha, PR725-PVLAN-PO-PLAN-001, review/G1_PRODUCT_R1 P1): the post-deletion readback of a PVLAN port-channel
must distinguish "release verified" from "release could not be verified".

NOT LIVE TESTED. Real main() in state `deleted`; only the controller boundary is intercepted, through the EXISTING harness
(FakeController -> E2 PoController -> G1 PoLifecycleController). After the mark-delete, this controller can answer the
interface-summary and/or policy-list reads with HTTP 500 for a given number of HTTP calls. The module's bounded GET
retries each summary read 3 times (_dcnm_intf_get_with_retries), so one failed verifier attempt = 3 failed HTTP calls.
Every scenario also asserts that no write other than the one mark-delete and the one deploy was sent (no rewrite of the
member, no second deploy, no recovery write). Previews are SYNTHETIC (same as the G1 deletion tests).

G1 (module 17029c48...) passes the all-summary-reads-fail scenario as a SUCCESS: that is the defect (fail-before).
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from .test_dcnm_intf_pvlan_harness import IF7, TRUNK, run, trunk_host_nv
from .test_dcnm_intf_pvlan_po_g1 import PoLifecycleController, create_preview, del_item, delete_preview, item, markdelete_ok
from .test_dcnm_intf_pvlan_po_host import PO, PO_MEMBER

SUMMARY = "/rest/interface/detail?serialNumber="
POLICIES = "/control/policies/switches/"
# G3: host, the mode whose creation is measured (H1); the creation of the other modes is refused before any write.
MODE = "host"
LINES = ["switchport private-vlan host-association 2210 2212"]
ASSOC = [{"primary_vlan": 2210, "secondary_vlan": 2212}]
ERROR = {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}


class ReadbackController(PoLifecycleController):
    """After the delete DEPLOY (G4: so that the post-deploy verifier, not the pre-deploy member release, is what meets
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
    """A host port-channel created through main() (same steps as the G1 `created` helper, on this controller),
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
    """G4: a problem found by the pre-deploy member release stops the run after the mark-delete: no modify, no deploy."""
    writes = [c for c in ctrl.calls if c[0] in ("POST", "PUT", "DELETE") and "/config-preview" not in c[1]]
    return [c[1].rsplit("/", 2)[-2] + "/" + c[1].rsplit("/", 1)[-1] for c in writes] == ["interface/markdelete"]


def test_all_summary_reads_fail_is_an_error_never_a_verified_deletion():
    ctrl = deleted_ctrl(fail_summary=10**6)
    status, result = run(ctrl, [del_item()], state="deleted")
    assert status == "fail", "six failed summary reads must not end as a successful deletion"
    assert "release could not be verified after 6 readback attempts" in result["msg"]
    assert "the interface summary could not be read authoritatively" in result["msg"]
    # G4: the reads are counted after the delete deploy; one summary read before the verifier is not one of its attempts.
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
    # G4: found by the member release BEFORE any deploy (it proves the parent absent first), not by the post-deploy verifier.
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
    # G4: the surviving child claim is found by the member release BEFORE any deploy.
    assert status == "fail" and "live policies still reference the port-channel" in result["msg"]
    assert only_the_markdelete_was_written(ctrl)


def test_the_normal_deletion_still_succeeds_with_no_extra_write():
    ctrl = deleted_ctrl()
    status, result = run(ctrl, [del_item()], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.summary_reads_after_delete >= 1 and ctrl.policy_reads_after_delete == 1
    assert only_the_deletion_was_written(ctrl)
    assert PO not in ctrl.detail and ctrl.detail[IF7]["policy"] == TRUNK
