"""A never-deployed vPC parent is read without a compliance value; it is never In-Sync.

MEASURED (live, NDFC 12.6.0.267, `interface/detail`): a conventional vPC created with ``deploy: false`` shows its LOGICAL parent
(ifType INTERFACE_VPC, composite serial) with ``complianceStatus`` present and null, while its child port-channels report
``Out-of-Sync``. The strict summary reader used to reject the whole switch for that one entry, so the next invocation (deploy, query,
sweep) was refused as "could not be read authoritatively".

The reader now accepts null ONLY for that shape. Absent key, empty string, a non-string, and null on any other entry or on a single
serial are still rejected. The null is stored untouched and every consumer keeps comparing against "In-Sync", so convergence is still
required and an unknown compliance never authorises a deploy by itself.

The vPC parent null in the main() cases is a REPLAY of the measured shape (harness entry with its compliance replaced by null); the
reader cases are labelled SYNTHETIC where they alter a measured entry to probe a format the capture does not show.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import types
from unittest import mock

import pytest

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

from . import gie_withdrawal_harness as H

DcnmIntf = dcnm_interface.DcnmIntf
PAIR = "SN1~SN2"


# ------------------------------------------------------------------ reader
def _entry(name="vPC12", if_type="INTERFACE_VPC", serial=PAIR, compliance=None, **kw):
    item = {
        "ifName": name, "serialNo": serial, "fabricName": "F", "ifType": if_type, "isPhysical": None, "markDeleted": False,
        "alias": None, "deleteReason": None, "complianceStatus": compliance, "underlayPolicies": [],
    }
    item.update(kw)
    return item


def _stub():
    s = types.SimpleNamespace()
    s.have_all = []
    s.have_all_cached_snos = set()
    s.have_all_failed_snos = set()
    s.paths = {"IF_DETAIL_WITH_SNO": "/detail?serialNumber={0}"}
    s.ip_sn = {"192.0.2.1": "SN1", "192.0.2.2": "SN2"}
    s.vpc_ip_sn = {}
    s.module = mock.Mock()
    s._dcnm_intf_authority_key = DcnmIntf._dcnm_intf_authority_key
    s._dcnm_intf_query_serial = DcnmIntf._dcnm_intf_query_serial
    s._dcnm_intf_serial_parts = DcnmIntf._dcnm_intf_serial_parts
    s._dcnm_intf_summary_authorities = lambda sno: set()
    s._dcnm_intf_get_with_retries = mock.Mock()
    return s


def _read(items, sno="SN1", stub=None):
    s = stub or _stub()
    s._dcnm_intf_get_with_retries.return_value = {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": items}
    with mock.patch.object(dcnm_interface, "read_reason_note") as note, mock.patch.object(dcnm_interface, "read_reason_clear"):
        ok = DcnmIntf.dcnm_intf_get_have_all_with_sno(s, sno)
    return s, ok, note


def test_measured_undeployed_vpc_parent_is_read_and_stored_untouched():
    child = _entry("Port-channel12", "INTERFACE_PORT_CHANNEL", "SN1", "Out-of-Sync")
    s, ok, note = _read([child, _entry()])
    assert ok is True and note.call_count == 0
    assert s.have_all_failed_snos == set() and s.have_all_cached_snos
    parent = [e for e in s.have_all if e["ifType"] == "INTERFACE_VPC"][0]
    assert parent["complianceStatus"] is None, "no In-Sync (or any other value) may be invented"


def test_in_sync_vpc_parent_control_is_unchanged():
    s, ok, _n = _read([_entry(compliance="In-Sync")])
    assert ok is True and s.have_all[0]["complianceStatus"] == "In-Sync"


@pytest.mark.parametrize("entry,label", [
    (_entry("Port-channel12", "INTERFACE_PORT_CHANNEL", "SN1", None), "null on a port-channel child"),
    (_entry("Ethernet1/5", "INTERFACE_ETHERNET", "SN1", None), "null on a physical member"),
    (_entry(serial="SN1"), "null on an INTERFACE_VPC with a single serial"),
    (_entry(compliance=""), "empty string on the vPC parent"),
    (_entry(compliance=5), "non-string on the vPC parent"),
], ids=lambda v: v if isinstance(v, str) else "")
def test_null_is_not_accepted_outside_the_measured_shape_SYNTHETIC(entry, label):
    s, ok, note = _read([entry])
    assert ok is False, label
    assert s.have_all == [] and s.have_all_failed_snos == {"SN1"}
    assert note.call_args[0][3] == "entry 0: field complianceStatus missing or empty"


def test_absent_compliance_key_on_the_vpc_parent_is_still_rejected_SYNTHETIC():
    entry = _entry()
    del entry["complianceStatus"]
    s, ok, note = _read([entry])
    assert ok is False and s.have_all_failed_snos == {"SN1"}
    assert note.call_args[0][3] == "entry 0: field complianceStatus missing or empty"


def test_a_valid_null_parent_does_not_hide_a_malformed_record_next_to_it():
    bad = _entry("Port-channel12", "INTERFACE_PORT_CHANNEL", "SN1", "In-Sync")
    del bad["alias"]
    s, ok, note = _read([_entry(), bad])
    assert ok is False and s.have_all == [] and s.have_all_failed_snos == {"SN1"}
    assert note.call_args[0][3] == "entry 1: field alias missing"


def test_one_unreadable_switch_stays_failed_while_the_other_is_read():
    s = _stub()
    s, ok_a, _n = _read([_entry()], "SN1", s)
    s._dcnm_intf_get_with_retries.return_value = {"RETURN_CODE": 500, "MESSAGE": "boom", "DATA": None}
    with mock.patch.object(dcnm_interface, "read_reason_note"), mock.patch.object(dcnm_interface, "read_reason_clear"):
        ok_b = DcnmIntf.dcnm_intf_get_have_all_with_sno(s, "SN2")
    assert ok_a is True and ok_b is False
    assert "SN2" in s.have_all_failed_snos or any("SN2" in x for x in s.have_all_failed_snos)
    with pytest.raises(Exception):
        s.module.fail_json.side_effect = RuntimeError("fail_json")
        DcnmIntf.dcnm_intf_require_summary_authority(types.SimpleNamespace(
            module=s.module, have_all_failed_snos=s.have_all_failed_snos, have_all_cached_snos=s.have_all_cached_snos,
            have_breakout_failed_snos=set(), have_breakout_cached_snos=set(),
            _dcnm_intf_authority_key=DcnmIntf._dcnm_intf_authority_key), "SN2")


# ------------------------------------------------------------------ real main()
VPC_HAVE = None


def _have():
    global VPC_HAVE
    if VPC_HAVE is None:
        VPC_HAVE = H.build_have(H.VPC_TRUNK)
    return copy.deepcopy(VPC_HAVE)


def _conf(deploy=True):
    return H.cfg_for(H.VPC_TRUNK, H.base_for(H.VPC_TRUNK), deploy=deploy)


def _drive(configs, state, converge_after_deploy=False, detail_override=None, check_deploy=False, null_parent=True):
    """Real main() with the harness transport; the vPC parent entry of `interface/detail` is the measured never-deployed shape."""
    calls = []
    have = _have()
    base = H._transport(calls, have)
    deployed = {"done": False}

    def send(mod, method, path, payload=None):
        response = base(mod, method, path, payload)
        if method == "POST" and path.endswith("/rest/globalInterface/deploy"):
            deployed["done"] = True
        if method == "GET" and "/interface/detail" in path:
            if detail_override is not None:
                return detail_override(response)
            if null_parent and not (converge_after_deploy and deployed["done"]):
                for entry in response["DATA"]:
                    if entry["ifType"] == "INTERFACE_VPC":
                        entry["complianceStatus"] = None
        return response

    original = H.set_module_args

    def with_args(args):
        args = dict(args)
        if check_deploy:
            args["check_deploy"] = True
        return original(args)

    with mock.patch.object(H, "_transport", lambda _c, _h: send), mock.patch.object(H, "set_module_args", with_args):
        result, _unused = H.run_configs(configs, state, have=have)
    return result, calls


def _writes(calls):
    return [c for c in calls if c["method"] != "GET"]


def _deploys(calls):
    return [c for c in _writes(calls) if c["path"].endswith("/rest/globalInterface/deploy")]


def test_next_invocation_with_deploy_reads_the_parent_and_deploys_it():
    result, calls = _drive([_conf(True)], "merged")
    assert not result.get("failed"), result.get("msg")
    assert len(_deploys(calls)) == 1 and len(_writes(calls)) == 1, "only the deploy; no intent is rewritten"
    assert [i["ifName"] for i in _deploys(calls)[0]["payload"]] == ["vPC12"]


def test_next_invocation_without_deploy_reads_and_writes_nothing():
    result, calls = _drive([_conf(False)], "merged")
    assert not result.get("failed"), result.get("msg")
    assert _writes(calls) == []


def test_query_reads_the_undeployed_parent():
    result, calls = _drive([_conf(True)], "query")
    assert not result.get("failed"), result.get("msg")
    assert _writes(calls) == []


def test_convergence_is_still_required_when_the_parent_stays_unknown():
    result, calls = _drive([_conf(True)], "merged", check_deploy=True)
    assert result["failed"] is True
    assert "did not reach 'In-Sync'" in str(result["msg"])
    assert len(_deploys(calls)) >= 1


def test_convergence_check_passes_once_the_controller_reports_in_sync():
    result, calls = _drive([_conf(True)], "merged", converge_after_deploy=True, check_deploy=True)
    assert not result.get("failed"), result.get("msg")
    assert len(_deploys(calls)) >= 1


def test_malformed_neighbour_entry_still_refuses_the_whole_request_before_any_write():
    def broken(response):
        for entry in response["DATA"]:
            if entry["ifType"] == "INTERFACE_VPC":
                entry["complianceStatus"] = None
        response["DATA"].append({"ifName": "Ethernet1/40"})
        return response

    result, calls = _drive([_conf(True)], "merged", detail_override=broken)
    assert result["failed"] is True and "could not be read authoritatively" in result["msg"]
    assert _writes(calls) == []


def test_sweep_without_config_still_refuses_when_the_summary_is_unreadable():
    def http_500(_response):
        return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": None}

    for state in ("overridden", "deleted"):
        result, calls = _drive([], state, detail_override=http_500)
        assert result.get("failed") is True, (state, result)
        assert _writes(calls) == []


def test_named_delete_of_the_undeployed_vpc_is_unchanged_by_the_reader_fix():
    """Control: this path never depended on the changed check; base and candidate send the same two writes."""
    conf = {"name": "vpc12", "type": "vpc", "switch": ["10.0.0.1", "10.0.0.2"], "deploy": True}
    result, calls = _drive([conf], "deleted")
    assert not result.get("failed"), result.get("msg")
    assert [(c["method"], c["path"].rsplit("/rest/", 1)[-1]) for c in _writes(calls)] == [
        ("DELETE", "interface/markdelete"), ("POST", "globalInterface/deploy")]
