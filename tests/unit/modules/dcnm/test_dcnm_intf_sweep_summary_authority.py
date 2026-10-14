"""`overridden` / `deleted` WITHOUT config: the interface summary of every switch is the scope of the sweep.

A switch whose summary could not be read authoritatively (HTTP error, an entry the reader rejects, a transport failure on
every attempt) used to contribute no interface, so the run ended as a successful no-op -- or swept only the readable
switches -- over state it never saw. It must now refuse during planning, naming the switch, before any configuration or
deployment request. A VALID empty summary is still a successful no-op, and a vPC peer covered by the pair's answer is not
refused. Drives the real main() through a recording transport (no network, no .env); the faults are synthetic.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
from unittest.mock import patch

import pytest
from ansible.module_utils.connection import ConnectionError as AnsibleConnectionError
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from .dcnm_module import set_module_args

FABRIC = "SWEEPFAB"
SWITCHES = {"A": ("192.0.2.11", "SNSWEEP0011", "leaf-a"), "B": ("192.0.2.12", "SNSWEEP0012", "leaf-b")}
STATES = ["overridden", "deleted"]
FAULTS = ["http500", "http500_empty", "invalid", "transport"]
TRUNK_NV = {
    "ADMIN_STATE": "false", "ALLOWED_VLANS": "10", "BPDUGUARD_ENABLED": "no", "CONF": "", "DESC": "", "ENABLE_MIRROR_CONFIG": "false",
    "ENABLE_NETFLOW": "false", "FEC": "auto", "GF": "", "INTF_NAME": "Ethernet1/9", "MTU": "jumbo", "NATIVE_VLAN": "", "NETFLOW_MONITOR": "",
    "POLICY_DESC": "", "POLICY_ID": "POLICY-1", "PORTTYPE_FAST_ENABLED": "true", "PRIORITY": "500", "PTP": "false", "SPEED": "Auto",
    "FABRIC_NAME": FABRIC, "MARK_DELETED": "false", "DUPLEX": "auto", "ENABLE_CDP": "true", "QUEUING_POLICY": "", "ENABLE_PFC": "false",
    "ENABLE_QOS": "false", "QOS_POLICY": "",
}


def _entry(name, sn, if_type="INTERFACE_ETHERNET", physical="true", drop=()):
    item = {"ifName": name, "serialNo": sn, "fabricName": FABRIC, "ifType": if_type, "isPhysical": physical, "markDeleted": False,
            "alias": "", "deleteReason": None, "complianceStatus": "In-Sync", "underlayPolicies": [], "deletable": True,
            "mgmtIpAddress": "", "interfaceDbId": 1}
    for key in drop:
        item.pop(key)
    return item


def _summary(mode, sn, extra=()):
    if mode == "valid":
        return {"RETURN_CODE": 200, "MESSAGE": "OK",
                "DATA": [_entry("Ethernet1/9", sn), _entry("mgmt0", sn, "INTERFACE_MGMT", "false")] + list(extra)}
    if mode == "valid_empty":
        return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": []}
    if mode == "http500":
        return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {"error": "synthetic fault"}}
    if mode == "http500_empty":
        return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}
    if mode == "invalid":
        return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [_entry("Ethernet1/9", sn, drop=("ifType",))]}
    if mode == "transport":
        raise AnsibleConnectionError("synthetic transport failure")
    raise ValueError(mode)


def _have(sn):
    return [{"policy": "int_trunk_host", "interfaces": [{"ifName": "Ethernet1/9", "serialNumber": sn, "interfaceType": "INTERFACE_ETHERNET",
                                                         "fabricName": FABRIC, "nvPairs": dict(TRUNK_NV)}]}]


class _Case(ModuleTestCase):
    def runTest(self):
        pass


def _run(state, modes, managable=None, pair_extra=None):
    """modes {"A": mode, "B": mode}; pair_extra: entries of B appended to A's VALID answer (a vPC pair answer)."""
    managable = managable or {}
    inventory = {SWITCHES[k][0]: {"logicalName": SWITCHES[k][2], "serialNumber": SWITCHES[k][1], "isVpcConfigured": "False",
                                  "vpcDomain": 0, "switchRole": "leaf", "managable": managable.get(k, "True")} for k in modes}
    ip_sn = {SWITCHES[k][0]: SWITCHES[k][1] for k in modes}
    hn_sn = {SWITCHES[k][2]: SWITCHES[k][1] for k in modes}
    by_sn = {SWITCHES[k][1]: mode for k, mode in modes.items()}
    calls = []

    def send(mod, method, path, payload=None):
        calls.append({"method": method, "path": path, "payload": json.loads(payload) if isinstance(payload, str) and payload else payload})
        if method != "GET":
            return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": []}
        if "accessmode" in path.lower():
            return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {"readonly": False}}
        sn = path.split("serialNumber=")[-1].split("&")[0] if "serialNumber=" in path else None
        if "/interface/detail" in path:
            extra = pair_extra if (pair_extra and sn == SWITCHES["A"][1]) else ()
            return _summary(by_sn.get(sn, "valid_empty"), sn, extra)
        if "/interface?" in path:
            return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": _have(sn) if sn in by_sn else []}
        return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": []}

    case = _Case(methodName="runTest")
    case.setUp()
    set_module_args({"state": state, "fabric": FABRIC, "config": []})
    result = None
    try:
        with patch.object(module, "get_fabric_inventory_details", return_value=inventory), \
                patch.object(module, "get_ip_sn_dict", return_value=(ip_sn, hn_sn)), \
                patch.object(module, "dcnm_version_supported", return_value=(12, "12.6.0.267")), \
                patch.object(module, "dcnm_get_bulk_api_support", return_value=False), \
                patch.object(module, "dcnm_send", side_effect=send), \
                patch.object(module.time, "sleep"):
            try:
                module.main()
            except (AnsibleExitJson, AnsibleFailJson) as exc:
                result = exc.args[0]
            else:
                raise AssertionError("module did not exit through Ansible")
    finally:
        case.tearDown()
    return result, calls


def _writes(calls):
    return [c for c in calls if c["method"] != "GET"]


def _serials_written(calls):
    out = set()
    for call in _writes(calls):
        body = call["payload"] if isinstance(call["payload"], list) else [call["payload"]]
        for elem in body:
            for intf in (elem.get("interfaces") or [elem]) if isinstance(elem, dict) else []:
                if isinstance(intf, dict) and intf.get("serialNumber"):
                    out.add(intf["serialNumber"])
    return out


@pytest.mark.parametrize("state", STATES)
def test_valid_summary_with_drift_still_resets_and_deploys(state):
    result, calls = _run(state, {"A": "valid"})
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is True
    assert [c["method"] for c in _writes(calls)] == ["PUT", "POST"]
    assert _serials_written(calls) == {SWITCHES["A"][1]}


@pytest.mark.parametrize("state", STATES)
def test_valid_empty_summary_is_still_a_successful_noop(state):
    result, calls = _run(state, {"A": "valid_empty"})
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is False and _writes(calls) == []


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("fault", FAULTS)
def test_unreadable_summary_refuses_by_switch_before_any_write_SYNTHETIC(state, fault):
    result, calls = _run(state, {"A": fault})
    assert result.get("failed") is True, "an unreadable summary must not end as a successful no-op"
    assert SWITCHES["A"][1] in result["msg"] and "summary" in result["msg"] and "could not be read authoritatively" in result["msg"]
    assert _writes(calls) == [], "the refusal must precede every configuration or deployment request"


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("fault", FAULTS)
def test_one_unreadable_switch_blocks_the_whole_sweep_before_any_write_SYNTHETIC(state, fault):
    # Switch A is readable and has real work; B is not readable. Nothing may be sent -- not even A's reset.
    result, calls = _run(state, {"A": "valid", "B": fault})
    assert result.get("failed") is True
    assert SWITCHES["B"][1] in result["msg"] and SWITCHES["A"][1] not in result["msg"]
    assert _writes(calls) == []


@pytest.mark.parametrize("state", STATES)
def test_unmanageable_switch_is_part_of_the_sweep_so_its_unreadable_summary_also_refuses_SYNTHETIC(state):
    # The sweep resets interfaces of every switch of the fabric (an unmanageable one included, see the control below),
    # so an unreadable unmanageable switch is not out of scope.
    result, calls = _run(state, {"A": "valid", "B": "http500"}, managable={"B": "False"})
    assert result.get("failed") is True and SWITCHES["B"][1] in result["msg"]
    assert _writes(calls) == []


@pytest.mark.parametrize("state", STATES)
def test_control_unmanageable_switch_with_drift_is_swept(state):
    result, calls = _run(state, {"A": "valid", "B": "valid"}, managable={"B": "False"})
    assert not result.get("failed"), result.get("msg")
    assert _serials_written(calls) == {SWITCHES["A"][1], SWITCHES["B"][1]}


@pytest.mark.parametrize("state", STATES)
def test_vpc_peer_covered_by_the_pair_answer_is_not_refused(state):
    # A's answer also carries B's interfaces (a paired answer): B is read authoritatively through it, so the sweep must not
    # refuse it. B's own summary would fail if it were requested.
    peer = SWITCHES["B"][1]
    pair = [_entry("Ethernet1/9", peer), _entry("mgmt0", peer, "INTERFACE_MGMT", "false")]
    result, calls = _run(state, {"A": "valid", "B": "http500"}, pair_extra=pair)
    assert not result.get("failed"), result.get("msg")
    assert not any("/interface/detail" in c["path"] and peer in c["path"] for c in calls), "the peer was covered by A's answer"
    assert _serials_written(calls) == {SWITCHES["A"][1], peer}
