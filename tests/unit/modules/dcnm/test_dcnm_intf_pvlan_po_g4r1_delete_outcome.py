"""PO G4-R1 (Alpha): the mark-delete of a registered PVLAN port-channel deletion must be CONFIRMED before anything else.

Reproduces the architect probe review/PO_G4_R1/probe_uncertain_markdelete.py through real main() and the existing G4
ReleaseController: the mark-delete APPLIES the measured release (the member becomes the HR-post int_trunk_host,
ADMIN_STATE "true") but its ANSWER is not the measured success. G4 retried that DELETE 20 times, the generic parser turned
the HTTP 500 into a synthetic 200/OK (changed=False), the member release was skipped and, with a down-looking preview,
one deploy was sent. G4-R1: one attempt, measured answer only; any other answer stops the run before any member modify or
deploy, whatever a later preview would look like.

The error answers below are SYNTHETIC (none was observed live); the success answer is the MEASURED one (markdelete_ok).
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from ansible.module_utils.connection import ConnectionError as AnsibleConnectionError

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .test_dcnm_intf_pvlan_harness import SWITCH_IP, TRUNK, run
from .test_dcnm_intf_pvlan_po_g1 import PoLifecycleController, markdelete_ok
from .test_dcnm_intf_pvlan_po_g4_release import MARKDELETE, MEM, PO, ReleaseController, delete, entry, owned_ctrl

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
            "DATA": {"message": "Request accepted", "value": [{"interfaceType": "INTERFACE_PORT_CHANNEL", "serialNumber": SERIAL, "IfName": PO}]},
        },
    ),
    (
        "multi_status_error_item",
        {"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [{"reportItemType": "ERROR", "message": "synthetic", "entity": "%s~%s" % (SERIAL, PO)}]},
    ),
    (
        "not_ok_message",
        {
            "RETURN_CODE": 200,
            "MESSAGE": "Accepted",
            "DATA": {"message": "Interface deleted successfully", "value": [{"interfaceType": "INTERFACE_PORT_CHANNEL", "serialNumber": SERIAL, "IfName": PO}]},
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
        assert P.po_markdelete_outcome_problems(answer, SERIAL, PO), _label
    assert P.po_markdelete_outcome_problems(None, SERIAL, PO)


def test_two_registered_pvlan_deletions_are_sent_one_request_each():
    ctrl = owned_ctrl()
    ctrl.detail["Port-channel503"] = dict(ctrl.detail[PO], nvPairs=dict(ctrl.detail[PO]["nvPairs"], PO_ID="Port-channel503", MEMBER_INTERFACES="Ethernet1/11"))
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
