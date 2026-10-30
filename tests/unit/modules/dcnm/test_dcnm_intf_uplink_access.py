# Copyright (c) 2026 Cisco and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Mode 'uplink_access': updates of an existing ToR-uplink vPC parent on the leaf pair (int_vpc_uplink_access).

The ToR pairing creates the parent on the pair serial, its port-channel child and member on each leaf, and owns
everything except twelve keys. These tests drive the real main() and assert what the module sends: one
interface/modify for the parent on the pair serial, the requested keys, every other stored nvPair byte-equal, nothing
for the children or the ToR, and no request at all for a refused item.

The controller double follows the shape of a saved read of a paired ToR: the intent and detail reads answer for a
leaf serial and return the parent under the pair serial, the same reads by pair serial fail, and the detail read of
either leaf returns the rows of both. Every serial, name and ID is synthetic. The tests make no claim about the
template or the device.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
from urllib.parse import parse_qs, urlsplit

from unittest.mock import patch

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import gie_withdrawal_harness as h

UL = "int_vpc_uplink_access"
UL_PO = "int_vpc_uplink_access_po"
UL_MEMBER = "int_vpc_uplink_access_po_member"
VPC = "vPC2"
PAIR = h.VPC_PAIR_SERIAL
LEAVES = (h.SERIAL, h.PEER_SERIAL)
TOR_SERIAL = "SAL1819SANT"
TOR_PO = "port-channel501"
PO = "port-channel2"
MEMBER = "Ethernet1/5"
DESC = "vPC-leaf-connected-to-tor:tor-1-port-channel501"

# The 24 stored nvPairs of the parent, in the shape of the saved read (values synthetic). None of the 12 keys.
STORED = {
    "ADMIN_STATE": "true",
    "BPDUGUARD_ENABLED": "false",
    "ENABLE_MIRROR_CONFIG": "false",
    "INTF_NAME": VPC,
    "MTU": "jumbo",
    "NBR_INTF_NAME": TOR_PO,
    "NBR_SERIAL_NUMBER": TOR_SERIAL,
    "PC_MODE": "active",
    "PEER1_ALLOWED_VLANS": "none",
    "PEER1_MEMBER_INTERFACES": MEMBER,
    "PEER1_PCID": "2",
    "PEER1_PO_CONF": "",
    "PEER1_PO_DESC": DESC,
    "PEER2_ALLOWED_VLANS": "none",
    "PEER2_MEMBER_INTERFACES": MEMBER,
    "PEER2_PCID": "2",
    "PEER2_PO_CONF": "",
    "PEER2_PO_DESC": DESC,
    "POLICY_DESC": "",
    "POLICY_ID": "POLICY-2001",
    "PRIORITY": "250",
    "PTP_VLAN": "",
    "SPEED": "Auto",
    "SWITCH_ROLE": "leaf",
}
# Sent back unchanged in every write; POLICY_ID and POLICY_DESC are controller metadata the module never sends.
PRESERVED = sorted(k for k in STORED if k not in ("POLICY_ID", "POLICY_DESC"))

# (public key, nvPair, reset) of the 12 parent bindings.
ROWS = [
    ("enable_qos", "ENABLE_QOS", "false"),
    ("qos_policy", "QOS_POLICY", ""),
    ("disable_qos_stats", "qosStatsSuppressed", "false"),
    ("spanning_tree_port_type", "spanningTreePortType", "no"),
    ("enable_storm_control", "ENABLE_STORM_CONTROL", "false"),
    ("storm_control_action", "STORM_CONTROL_ACTION", "no"),
    ("storm_control_broadcast_level_percent", "STORM_CONTROL_BCAST_LEVEL_PERCENT", ""),
    ("storm_control_multicast_level_percent", "STORM_CONTROL_MCAST_LEVEL_PERCENT", ""),
    ("storm_control_unicast_level_percent", "STORM_CONTROL_UCAST_LEVEL_PERCENT", ""),
    ("storm_control_broadcast_level_pps", "STORM_CONTROL_BCAST_LEVEL_PPS", ""),
    ("storm_control_multicast_level_pps", "STORM_CONTROL_MCAST_LEVEL_PPS", ""),
    ("storm_control_unicast_level_pps", "STORM_CONTROL_UCAST_LEVEL_PPS", ""),
]
# Each leaf child holds the 12 values at their defaults (the parent forwards them on rebuild).
CHILD_DEFAULTS = dict((nv, reset) for _k, nv, reset in ROWS)


def _parent(policy=UL, **stored):
    return {"policy": policy, "interfaces": [{
        "serialNumber": PAIR, "ifName": VPC, "interfaceType": "INTERFACE_VPC", "fabricName": h.FABRIC,
        "nvPairs": dict(STORED, **stored)}]}


def _child(serial):
    nv = dict(CHILD_DEFAULTS, ADMIN_STATE="true", ALLOWED_VLANS="none", BPDUGUARD_ENABLED="false", CONF="",
              DESC=DESC, MTU="jumbo", NATIVE_VLAN="", POLICY_DESC="", POLICY_ID="POLICY-22" + serial[-1],
              PO_ID=PO, PRIMARY_INTF=VPC, PRIORITY="400", SPEED="Auto", SWITCH_ROLE="leaf")
    return {"policy": UL_PO, "interfaces": [{"serialNumber": serial, "ifName": PO, "nvPairs": nv}]}


def _member(serial):
    nv = {"ADMIN_STATE": "true", "ALLOWED_VLANS": "none", "CONF": "", "DESC": "", "INTF_NAME": MEMBER,
          "PC_MODE": "active", "POLICY_DESC": "", "POLICY_ID": "POLICY-23" + serial[-1], "PO_ID": PO,
          "PRIMARY_INTF": VPC, "PRIORITY": "450", "PTP": "false", "PTP_VLAN": ""}
    return {"policy": UL_MEMBER, "interfaces": [{"serialNumber": serial, "ifName": MEMBER, "nvPairs": nv}]}


def _have(policy=UL, parent=True, **stored):
    """Intent records. The parent is returned by the read of either leaf."""
    have = [_member(s) for s in LEAVES] + [_child(s) for s in LEAVES]
    return have + ([_parent(policy, **stored)] if parent else [])


def _row(serial, if_name, if_type, template, source, **extra):
    row = {
        "ifName": if_name, "serialNo": serial, "fabricName": h.FABRIC, "ifType": if_type, "isPhysical": "false",
        "markDeleted": False, "deletable": False, "editAllowed": True, "alias": "", "deleteReason": None,
        "complianceStatus": "In-Sync", "vpcId": 0,
        "underlayPolicies": [{"templateName": template, "entityName": if_name, "source": source,
                              "serialNumber": serial, "autoGenerated": True}],
    }
    row.update(extra)
    return row


def _detail(parent_template=UL, parent_source="", parent_type="INTERFACE_VPC", **parent_extra):
    """The paired detail answer of either leaf: the parent row on the pair serial and both leaves' children."""
    rows = [_row(PAIR, VPC, parent_type, parent_template, parent_source, deletable=True, alias=None,
                 **parent_extra)]
    for s in LEAVES:
        rows.append(_row(s, "Port-channel2", "INTERFACE_PORT_CHANNEL", UL_PO, VPC, vpcId=2,
                         alias="vPC-leaf-connected-to-tor:tor-1-port-channel501",
                         deleteReason="Interface has policy attached from vPC2"))
        rows.append(_row(s, MEMBER, "INTERFACE_ETHERNET", UL_MEMBER, VPC, vpcId=2, isPhysical="true"))
    return rows


def _transport(detail=None, failing=()):
    """Controller double: reads by leaf serial answer, reads by pair serial fail as measured."""
    def factory(calls, have):
        def send(mod, method, path, payload=None):
            parsed = json.loads(payload) if isinstance(payload, str) else copy.deepcopy(payload)
            calls.append({"method": method, "path": path, "payload": parsed})
            if method != "GET":
                return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": []}
            query = parse_qs(urlsplit(path).query)
            serial = (query.get("serialNumber") or [None])[0]
            if "vpcpair_serial_number" in path:
                return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {"vpc_pair_sn": PAIR}}
            if "readonly" in path or "accessmode" in path.lower():
                return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {"readonly": False}}
            if serial is not None and ("~" in serial or serial in failing):
                return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error",
                        "DATA": [{"message": "Serial number is not valid", "reportItemType": "ERROR"}]}
            if "/interface/detail" in path:
                rows = detail if detail is not None else _detail()
                return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": copy.deepcopy(rows)}
            if "/interface?" in path:
                return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [
                    copy.deepcopy(p) for p in have
                    if serial is None or p["interfaces"][0]["serialNumber"] in (serial, PAIR)]}
            return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": []}
        return send
    return factory


def _cfg(switch=None, deploy=True, name="vpc2", **profile):
    return {"name": name, "type": "vpc", "switch": list(switch or (h.SWITCH_IP, h.PEER_IP)), "deploy": deploy,
            "profile": dict({"mode": "uplink_access"}, **profile)}


def _run(configs, state, have, detail=None, failing=(), **kw):
    return h.run_configs(configs if isinstance(configs, list) else [configs], state, have,
                         transport=_transport(detail, failing), **kw)


def _modify(calls):
    """nvPairs of the one parent modify; asserts it is the only interface written and it is the parent."""
    entries = []
    for c in h.writes(calls):
        if "interface/modify" not in c["path"]:
            continue
        for pol in c["payload"] if isinstance(c["payload"], list) else [c["payload"]]:
            assert pol["policy"] == UL, pol["policy"]
            entries.extend(pol["interfaces"])
    assert len(entries) == 1, entries
    assert entries[0]["serialNumber"] == PAIR and entries[0]["ifName"] == VPC, entries[0]
    return entries[0]["nvPairs"]


def _paths(calls):
    return [c["method"] + " " + c["path"].split("/rest/")[-1].split("?")[0] for c in h.writes(calls)]


def _state_reads(calls):
    """Interface intent and detail reads (the vPC pair lookup of the inventory is not one)."""
    return [c["path"] for c in calls if c["method"] == "GET"
            and ("/interface?" in c["path"] or "/interface/detail" in c["path"])]


def _assert_refused(result, calls, *words):
    assert result.get("failed"), "the item was not refused"
    assert h.writes(calls) == [], [c["method"] + " " + c["path"] for c in h.writes(calls)]
    for w in words:
        assert w in result["msg"], result["msg"]
    assert "no change was sent" in result["msg"].lower(), result["msg"]


def _assert_preserved(nv):
    for k in PRESERVED:
        assert nv[k] == STORED[k], k
    assert "POLICY_ID" not in nv and "POLICY_DESC" not in nv


# ------------------------------------------------------------------ rows
@pytest.mark.parametrize("key,nvpair,reset", ROWS)
def test_the_twelve_rows_are_registered_on_the_uplink_parent(key, nvpair, reset):
    b = resolve_binding(UL, key)
    assert b is not None and b["parent_nvpair"] == nvpair and b["mechanism"] == "passthrough"
    assert b["applicable_interface_type"] == "vpc" and b["applicable_mode"] == "uplink_access"
    assert b.get("reset_wire") == reset


def test_no_row_is_registered_on_the_generated_children():
    for key, _nv, _reset in ROWS:
        assert resolve_binding(UL_PO, key) is None and resolve_binding(UL_MEMBER, key) is None


# ------------------------------------------------------------------ reads and identity
def test_reads_use_a_leaf_serial_and_the_write_targets_the_pair_serial():
    result, calls = _run(_cfg(spanning_tree_port_type="network"), "merged", _have())
    assert not result.get("failed"), result.get("msg")
    reads = [parse_qs(urlsplit(c["path"]).query).get("serialNumber", [None])[0]
             for c in calls if c["method"] == "GET" and "/interface" in c["path"]]
    assert reads and all(s in LEAVES for s in reads if s is not None), reads
    assert _modify(calls)["spanningTreePortType"] == "network"


def test_a_duplicated_paired_detail_row_is_accepted():
    detail = _detail() + [_row(PAIR, VPC, "INTERFACE_VPC", UL, "", deletable=True, alias=None)]
    result, calls = _run(_cfg(spanning_tree_port_type="network"), "merged", _have(), detail=detail)
    assert not result.get("failed"), result.get("msg")
    assert _modify(calls)["spanningTreePortType"] == "network"


def test_a_failed_read_is_not_an_absent_parent():
    result, calls = _run(_cfg(spanning_tree_port_type="network"), "merged", _have(), failing=LEAVES)
    assert result.get("failed"), "a failed read was accepted"
    assert h.writes(calls) == []


@pytest.mark.parametrize("have,words", [
    (_have(parent=False), "no uplink vPC exists"),
    (_have(policy="int_vpc_trunk_host"), "holds policy int_vpc_trunk_host"),
])
def test_a_missing_or_foreign_parent_is_refused(have, words):
    result, calls = _run(_cfg(spanning_tree_port_type="network"), "merged", have)
    _assert_refused(result, calls, words)


@pytest.mark.parametrize("detail", [
    [r for r in _detail() if r["ifName"] != VPC],
    _detail(parent_type="INTERFACE_PORT_CHANNEL"),
    _detail(parent_source="port-channel2"),
    _detail(parent_template="int_vpc_trunk_host"),
    _detail(markDeleted=True),
    _detail() + [_row(PAIR, VPC, "INTERFACE_VPC", UL, "", markDeleted=True)],
], ids=["absent", "not-a-vpc", "with-source", "other-template", "marked-deleted", "conflicting-duplicate"])
def test_a_detail_that_does_not_show_the_parent_is_refused(detail):
    result, calls = _run(_cfg(spanning_tree_port_type="network"), "merged", _have(), detail=detail)
    _assert_refused(result, calls)


# ------------------------------------------------------------------ merged
def test_merged_sends_one_parent_modify_and_preserves_every_other_nvpair():
    result, calls = _run(_cfg(spanning_tree_port_type="network"), "merged", _have())
    assert not result.get("failed"), result.get("msg")
    nv = _modify(calls)
    _assert_preserved(nv)
    assert sorted(nv) == sorted(PRESERVED + ["spanningTreePortType"])


def test_merged_writes_neither_the_children_nor_the_tor():
    result, calls = _run(_cfg(spanning_tree_port_type="network"), "merged", _have())
    assert not result.get("failed"), result.get("msg")
    assert _paths(calls) == ["POST interface/modify", "POST globalInterface/deploy"]
    deployed = [d for c in h.writes(calls) if c["path"].endswith("deploy") for d in c["payload"]]
    assert [(d["serialNumber"], d["ifName"]) for d in deployed] == [(PAIR, VPC)]
    sent = json.dumps([c["payload"] for c in h.writes(calls)])
    assert TOR_SERIAL + '"' not in sent.replace(STORED["NBR_SERIAL_NUMBER"] + '"', "", 1)
    assert UL_PO not in sent and UL_MEMBER not in sent


def test_merged_deploy_false_saves_without_deploying():
    result, calls = _run(_cfg(deploy=False, spanning_tree_port_type="network"), "merged", _have())
    assert not result.get("failed"), result.get("msg")
    assert _paths(calls) == ["POST interface/modify"]


ORDINARY_VPC_DEFAULTS = ("PORTTYPE_FAST_ENABLED", "CDP_ENABLE", "COPY_DESC", "LACP_PORT_PRIO", "LACP_RATE",
                         "DISABLE_LACP_SUSPEND", "ENABLE_LACP_VPC_CONV", "QUEUING_POLICY", "PEER1_NATIVE_VLAN",
                         "PEER2_NATIVE_VLAN", "PEER1_ACCESS_VLAN", "PEER2_ACCESS_VLAN")


def test_no_ordinary_vpc_default_reaches_the_payload():
    result, calls = _run(_cfg(enable_storm_control=True, storm_control_broadcast_level_percent="50"),
                         "merged", _have())
    assert not result.get("failed"), result.get("msg")
    nv = _modify(calls)
    for k in ORDINARY_VPC_DEFAULTS:
        assert k not in nv, k
    # Only the two explicit storm keys: no default action, no other level.
    assert sorted(k for k in nv if k.startswith(("STORM", "ENABLE_STORM"))) == [
        "ENABLE_STORM_CONTROL", "STORM_CONTROL_BCAST_LEVEL_PERCENT"]


@pytest.mark.parametrize("profile", [{}, {"spanning_tree_port_type": "network"}])
def test_merged_repeat_and_omission_write_nothing(profile):
    result, calls = _run(_cfg(deploy=False, **profile), "merged", _have(spanningTreePortType="network"))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and result["changed"] is False


def test_an_explicit_default_over_an_absent_value_is_stored_once():
    result, calls = _run(_cfg(deploy=False, spanning_tree_port_type="no"), "merged", _have())
    assert not result.get("failed"), result.get("msg")
    assert _modify(calls)["spanningTreePortType"] == "no"
    result, calls = _run(_cfg(deploy=False, spanning_tree_port_type="no"), "merged",
                         _have(spanningTreePortType="no"))
    assert h.writes(calls) == []


def test_merged_change_keeps_the_other_stored_keys():
    have = _have(spanningTreePortType="network", ENABLE_STORM_CONTROL="true", STORM_CONTROL_ACTION="trap")
    result, calls = _run(_cfg(spanning_tree_port_type="normal"), "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _modify(calls)
    assert nv["spanningTreePortType"] == "normal"
    assert nv["ENABLE_STORM_CONTROL"] == "true" and nv["STORM_CONTROL_ACTION"] == "trap"
    assert [sorted(c["interfaces"][0]["nvPairs"]) for c in result["diff"][0]["merged"]] == [
        ["spanningTreePortType"]]


# ------------------------------------------------------------------ replaced / overridden
# Every key set. The storm levels mix units, which the module refuses to write; a reset, disabling, or an unchanged
# request is still accepted over them.
STORED_SET = {
    "ENABLE_QOS": "true", "QOS_POLICY": "UL-QOS", "qosStatsSuppressed": "true", "spanningTreePortType": "network",
    "ENABLE_STORM_CONTROL": "true", "STORM_CONTROL_ACTION": "shutdown",
    "STORM_CONTROL_BCAST_LEVEL_PERCENT": "50", "STORM_CONTROL_MCAST_LEVEL_PERCENT": "",
    "STORM_CONTROL_UCAST_LEVEL_PERCENT": "", "STORM_CONTROL_BCAST_LEVEL_PPS": "",
    "STORM_CONTROL_MCAST_LEVEL_PPS": "1000", "STORM_CONTROL_UCAST_LEVEL_PPS": "",
}


@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_omission_resets_every_stored_key(state):
    result, calls = _run(_cfg(), state, _have(**STORED_SET))
    assert not result.get("failed"), result.get("msg")
    nv = _modify(calls)
    _assert_preserved(nv)
    for _k, nvpair, reset in ROWS:
        assert nv[nvpair] == reset, nvpair


@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_omission_with_nothing_stored_writes_nothing(state):
    result, calls = _run(_cfg(deploy=False), state, _have())
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_omission_resets_only_what_differs(state):
    result, calls = _run(_cfg(enable_qos=True, qos_policy="UL-QOS"), state, _have(**STORED_SET))
    assert not result.get("failed"), result.get("msg")
    nv = _modify(calls)
    assert nv["ENABLE_QOS"] == "true" and nv["QOS_POLICY"] == "UL-QOS"
    assert nv["qosStatsSuppressed"] == "false" and nv["ENABLE_STORM_CONTROL"] == "false"
    assert nv["STORM_CONTROL_MCAST_LEVEL_PPS"] == ""
    changed = sorted(result["diff"][0][state][0]["interfaces"][0]["nvPairs"])
    assert "ENABLE_QOS" not in changed and "QOS_POLICY" not in changed


def test_overridden_leaves_the_uplink_family_in_place():
    result, calls = _run(_cfg(), "overridden", _have(**STORED_SET))
    assert not result.get("failed"), result.get("msg")
    # Only the parent reset; the children and members of both leaves are neither deleted nor reset.
    assert _paths(calls) == ["POST interface/modify", "POST globalInterface/deploy"]
    assert result["diff"][0]["deleted"] == []
    _modify(calls)
    skipped = [s["Name"] for s in result["diff"][0]["skipped"] if "TOR uplink" in s.get("Reason", "")]
    assert sorted(skipped) == sorted([VPC, MEMBER, MEMBER]), skipped


# One row per registered reset of the parent. test_dcnm_intf_withdrawal.py requires this set to equal the registry.
UPLINK_ROUTE_RESET_ROWS = (
    (UL, "ENABLE_QOS", "enable_qos", "true", "false"),
    (UL, "QOS_POLICY", "qos_policy", "UL-QOS", ""),
    (UL, "qosStatsSuppressed", "disable_qos_stats", "true", "false"),
    (UL, "spanningTreePortType", "spanning_tree_port_type", "network", "no"),
    (UL, "ENABLE_STORM_CONTROL", "enable_storm_control", "true", "false"),
    (UL, "STORM_CONTROL_ACTION", "storm_control_action", "trap", "no"),
    (UL, "STORM_CONTROL_BCAST_LEVEL_PERCENT", "storm_control_broadcast_level_percent", "50", ""),
    (UL, "STORM_CONTROL_MCAST_LEVEL_PERCENT", "storm_control_multicast_level_percent", "50", ""),
    (UL, "STORM_CONTROL_UCAST_LEVEL_PERCENT", "storm_control_unicast_level_percent", "50", ""),
    (UL, "STORM_CONTROL_BCAST_LEVEL_PPS", "storm_control_broadcast_level_pps", "1000", ""),
    (UL, "STORM_CONTROL_MCAST_LEVEL_PPS", "storm_control_multicast_level_pps", "1000", ""),
    (UL, "STORM_CONTROL_UCAST_LEVEL_PPS", "storm_control_unicast_level_pps", "1000", ""),
)
UPLINK_ROUTE_RESET_IDENTITIES = frozenset((p, n) for p, n, _k, _h, _r in UPLINK_ROUTE_RESET_ROWS)


@pytest.mark.parametrize("policy,nvp,key,have_value,reset", UPLINK_ROUTE_RESET_ROWS,
                         ids=[n for _p, n, _k, _h, _r in UPLINK_ROUTE_RESET_ROWS])
@pytest.mark.parametrize("state,expect", [("merged", None), ("replaced", "reset"), ("overridden", "reset")])
def test_each_registered_reset_follows_the_omission_contract(policy, nvp, key, have_value, reset, state, expect):
    result, calls = _run(_cfg(deploy=False), state, _have(**{nvp: have_value}))
    assert not result.get("failed"), result.get("msg")
    if expect is None:
        assert h.writes(calls) == [], "merged changed an omitted key"
    else:
        nv = _modify(calls)
        assert nv[nvp] == reset
        assert sorted(result["diff"][0][state][0]["interfaces"][0]["nvPairs"]) == [nvp]


@pytest.mark.parametrize("nvp,key,stored", [
    (nvp, key, stored) for key, nvp in (("enable_qos", "ENABLE_QOS"), ("disable_qos_stats", "qosStatsSuppressed"),
                                        ("enable_storm_control", "ENABLE_STORM_CONTROL"))
    for stored in ("true", "false")
])
def test_repeating_a_stored_boolean_writes_nothing(nvp, key, stored):
    have = _have(**{nvp: stored, "QOS_POLICY": "UL-QOS"})
    result, calls = _run(_cfg(deploy=False, **{key: stored == "true"}), "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_a_stored_qos_without_a_name_is_not_judged_when_the_request_leaves_qos_alone():
    # For example QoS enabled outside the module with no policy name. The module sends it back unchanged.
    result, calls = _run(_cfg(spanning_tree_port_type="network"), "merged", _have(ENABLE_QOS="true", QOS_POLICY=""))
    assert not result.get("failed"), result.get("msg")
    nv = _modify(calls)
    assert nv["ENABLE_QOS"] == "true" and nv["QOS_POLICY"] == ""


def test_deleted_with_the_mode_is_refused():
    result, calls = _run(_cfg(), "deleted", _have(**STORED_SET))
    _assert_refused(result, calls, "does not support state 'deleted'")


# ------------------------------------------------------------------ QoS with an explicit name
def test_enable_without_a_stored_or_requested_name_is_refused():
    result, calls = _run(_cfg(enable_qos=True), "merged", _have())
    _assert_refused(result, calls, "non-empty 'qos_policy'", "does not choose")


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_enable_with_an_empty_name_is_refused(state):
    result, calls = _run(_cfg(enable_qos=True, qos_policy=""), state, _have(QOS_POLICY="UL-QOS"))
    _assert_refused(result, calls, "non-empty 'qos_policy'")


def test_replaced_enable_without_a_name_is_refused_even_with_one_stored():
    result, calls = _run(_cfg(enable_qos=True), "replaced", _have(ENABLE_QOS="true", QOS_POLICY="UL-QOS"))
    _assert_refused(result, calls, "non-empty 'qos_policy'")


def test_enable_with_an_explicit_name():
    result, calls = _run(_cfg(enable_qos=True, qos_policy="UL-QOS"), "merged", _have())
    assert not result.get("failed"), result.get("msg")
    nv = _modify(calls)
    assert nv["ENABLE_QOS"] == "true" and nv["QOS_POLICY"] == "UL-QOS"
    assert "qosStatsSuppressed" not in nv


def test_merged_enable_keeps_a_stored_name():
    result, calls = _run(_cfg(enable_qos=True), "merged", _have(ENABLE_QOS="false", QOS_POLICY="UL-QOS"))
    assert not result.get("failed"), result.get("msg")
    nv = _modify(calls)
    assert nv["ENABLE_QOS"] == "true" and nv["QOS_POLICY"] == "UL-QOS"


def test_no_fabric_policy_is_supplied():
    for profile in ({"enable_qos": True, "qos_policy": "UL-QOS"}, {"spanning_tree_port_type": "network"}):
        result, calls = _run(_cfg(**profile), "merged", _have())
        assert not result.get("failed"), result.get("msg")
        assert "QOS_CLASSIFICATION" not in json.dumps([c["payload"] for c in h.writes(calls)])


def test_policy_change_while_enabled():
    result, calls = _run(_cfg(qos_policy="UL-QOS-2"), "merged", _have(ENABLE_QOS="true", QOS_POLICY="UL-QOS"))
    assert not result.get("failed"), result.get("msg")
    nv = _modify(calls)
    assert nv["QOS_POLICY"] == "UL-QOS-2" and nv["ENABLE_QOS"] == "true"


def test_merged_disable_sends_false_and_keeps_the_name():
    result, calls = _run(_cfg(enable_qos=False), "merged", _have(ENABLE_QOS="true", QOS_POLICY="UL-QOS"))
    assert not result.get("failed"), result.get("msg")
    nv = _modify(calls)
    assert nv["ENABLE_QOS"] == "false" and nv["QOS_POLICY"] == "UL-QOS"


def test_merged_disable_and_clear_withdraw_both():
    have = _have(ENABLE_QOS="true", QOS_POLICY="UL-QOS")
    result, calls = _run(_cfg(enable_qos=False, qos_policy=""), "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _modify(calls)
    assert nv["ENABLE_QOS"] == "false" and nv["QOS_POLICY"] == ""


def test_an_empty_name_while_disabled_clears_the_stored_name():
    result, calls = _run(_cfg(qos_policy=""), "merged", _have(ENABLE_QOS="false", QOS_POLICY="UL-QOS"))
    assert not result.get("failed"), result.get("msg")
    assert _modify(calls)["QOS_POLICY"] == ""


@pytest.mark.parametrize("stored,profile,expected", [
    ({"ENABLE_QOS": "true", "QOS_POLICY": "UL-QOS"}, {"disable_qos_stats": True}, {"qosStatsSuppressed": "true"}),
    ({"ENABLE_QOS": "true", "QOS_POLICY": "UL-QOS", "qosStatsSuppressed": "true"}, {"disable_qos_stats": False},
     {"qosStatsSuppressed": "false"}),
    ({}, {"disable_qos_stats": True}, {"qosStatsSuppressed": "true"}),
    ({"spanningTreePortType": "network"}, {"spanning_tree_port_type": "normal"}, {"spanningTreePortType": "normal"}),
    ({"spanningTreePortType": "network"}, {"spanning_tree_port_type": "no"}, {"spanningTreePortType": "no"}),
], ids=["stats-on", "stats-off", "stats-while-qos-off", "stp-change", "stp-to-no"])
def test_statistics_and_stp_transitions(stored, profile, expected):
    result, calls = _run(_cfg(**profile), "merged", _have(**stored))
    assert not result.get("failed"), result.get("msg")
    nv = _modify(calls)
    for k, v in expected.items():
        assert nv[k] == v, k


@pytest.mark.parametrize("name", ["UL QOS", "UL\tQOS"])
def test_a_policy_name_with_whitespace_is_refused(name):
    result, calls = _run(_cfg(enable_qos=True, qos_policy=name), "merged", _have())
    _assert_refused(result, calls, "whitespace")
    assert _state_reads(calls) == []


def test_a_policy_name_longer_than_40_characters_is_refused():
    result, calls = _run(_cfg(enable_qos=True, qos_policy="P" * 41), "merged", _have())
    _assert_refused(result, calls, "qos_policy")


# ------------------------------------------------------------------ storm control
def test_storm_enable_action_and_levels():
    profile = {"enable_storm_control": True, "storm_control_action": "trap",
               "storm_control_broadcast_level_percent": "50.5", "storm_control_multicast_level_percent": "30",
               "storm_control_unicast_level_percent": "0"}
    result, calls = _run(_cfg(**profile), "merged", _have())
    assert not result.get("failed"), result.get("msg")
    nv = _modify(calls)
    assert nv["ENABLE_STORM_CONTROL"] == "true" and nv["STORM_CONTROL_ACTION"] == "trap"
    assert nv["STORM_CONTROL_BCAST_LEVEL_PERCENT"] == "50.5"
    assert nv["STORM_CONTROL_MCAST_LEVEL_PERCENT"] == "30"
    assert nv["STORM_CONTROL_UCAST_LEVEL_PERCENT"] == "0"


def test_the_default_action_is_sent_in_the_template_spelling():
    have = _have(ENABLE_STORM_CONTROL="true", STORM_CONTROL_ACTION="trap")
    result, calls = _run(_cfg(storm_control_action="default"), "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert _modify(calls)["STORM_CONTROL_ACTION"] == "no"


def test_a_zero_pps_level_is_a_value():
    result, calls = _run(_cfg(enable_storm_control=True, storm_control_broadcast_level_pps=0), "merged", _have())
    assert not result.get("failed"), result.get("msg")
    assert _modify(calls)["STORM_CONTROL_BCAST_LEVEL_PPS"] == "0"


@pytest.mark.parametrize("stored", [{}, {"ENABLE_STORM_CONTROL": "false"}])
@pytest.mark.parametrize("profile,word", [
    ({"storm_control_action": "shutdown"}, "storm_control_action"),
    ({"storm_control_unicast_level_percent": "10"}, "storm_control_unicast_level_percent"),
    ({"storm_control_unicast_level_pps": 10}, "storm_control_unicast_level_pps"),
    ({"enable_storm_control": False, "storm_control_action": "trap"}, "storm_control_action"),
])
def test_action_and_levels_need_storm_control_enabled(stored, profile, word):
    result, calls = _run(_cfg(**profile), "merged", _have(**stored))
    _assert_refused(result, calls, word, "'enable_storm_control' true")


def test_a_level_is_accepted_while_storm_control_is_stored_on():
    result, calls = _run(_cfg(storm_control_unicast_level_percent="10"), "merged",
                         _have(ENABLE_STORM_CONTROL="true"))
    assert not result.get("failed"), result.get("msg")
    assert _modify(calls)["STORM_CONTROL_UCAST_LEVEL_PERCENT"] == "10"


def test_replaced_levels_without_the_enable_are_refused():
    result, calls = _run(_cfg(storm_control_unicast_level_percent="10"), "replaced",
                         _have(ENABLE_STORM_CONTROL="true"))
    _assert_refused(result, calls, "'enable_storm_control' true")


def test_disable_keeps_the_stored_levels_under_merged():
    have = _have(ENABLE_STORM_CONTROL="true", STORM_CONTROL_BCAST_LEVEL_PERCENT="50")
    result, calls = _run(_cfg(enable_storm_control=False), "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _modify(calls)
    assert nv["ENABLE_STORM_CONTROL"] == "false" and nv["STORM_CONTROL_BCAST_LEVEL_PERCENT"] == "50"


def test_both_units_for_one_traffic_type_are_refused():
    profile = {"enable_storm_control": True, "storm_control_broadcast_level_percent": "50",
               "storm_control_broadcast_level_pps": 100}
    result, calls = _run(_cfg(**profile), "merged", _have())
    _assert_refused(result, calls, "mutually exclusive")


@pytest.mark.parametrize("profile,stored,cleared", [
    ({"storm_control_broadcast_level_percent": "40"}, {"STORM_CONTROL_BCAST_LEVEL_PPS": "1000"},
     "STORM_CONTROL_BCAST_LEVEL_PPS"),
    ({"storm_control_multicast_level_pps": 500}, {"STORM_CONTROL_MCAST_LEVEL_PERCENT": "30"},
     "STORM_CONTROL_MCAST_LEVEL_PERCENT"),
])
def test_merged_level_in_one_unit_clears_the_stored_other_unit_of_that_type(profile, stored, cleared):
    have = _have(ENABLE_STORM_CONTROL="true", **stored)
    result, calls = _run(_cfg(**profile), "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _modify(calls)
    assert nv[cleared] == ""


def test_another_traffic_type_keeps_its_stored_level():
    # A level in the other unit would mix units; test_dcnm_intf_uplink_storm_units.py covers that refusal.
    have = _have(ENABLE_STORM_CONTROL="true", STORM_CONTROL_MCAST_LEVEL_PPS="1000")
    result, calls = _run(_cfg(storm_control_broadcast_level_pps=500), "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _modify(calls)
    assert nv["STORM_CONTROL_MCAST_LEVEL_PPS"] == "1000" and "STORM_CONTROL_BCAST_LEVEL_PERCENT" not in nv


def test_replaced_switches_unit_by_resetting_the_omitted_one():
    have = _have(ENABLE_STORM_CONTROL="true", STORM_CONTROL_BCAST_LEVEL_PPS="1000")
    result, calls = _run(_cfg(enable_storm_control=True, storm_control_broadcast_level_percent="40"), "replaced",
                         have)
    assert not result.get("failed"), result.get("msg")
    nv = _modify(calls)
    assert nv["STORM_CONTROL_BCAST_LEVEL_PERCENT"] == "40" and nv["STORM_CONTROL_BCAST_LEVEL_PPS"] == ""


def test_an_empty_percent_clears_it():
    have = _have(ENABLE_STORM_CONTROL="true", STORM_CONTROL_BCAST_LEVEL_PERCENT="50")
    result, calls = _run(_cfg(storm_control_broadcast_level_percent=""), "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert _modify(calls)["STORM_CONTROL_BCAST_LEVEL_PERCENT"] == ""


@pytest.mark.parametrize("value", ["101", "100.001", "abc", "-1", "50.123"])
def test_an_invalid_percent_is_refused(value):
    result, calls = _run(_cfg(enable_storm_control=True, storm_control_broadcast_level_percent=value), "merged",
                         _have())
    _assert_refused(result, calls, "storm_control_broadcast_level_percent")


@pytest.mark.parametrize("value", [-1, 200000001])
def test_a_pps_level_out_of_range_is_refused(value):
    result, calls = _run(_cfg(enable_storm_control=True, storm_control_broadcast_level_pps=value), "merged",
                         _have())
    _assert_refused(result, calls, "storm_control_broadcast_level_pps")


def test_an_empty_pps_level_is_refused():
    result, calls = _run(_cfg(enable_storm_control=True, storm_control_broadcast_level_pps=""), "merged",
                         _have(ENABLE_STORM_CONTROL="true", STORM_CONTROL_BCAST_LEVEL_PPS="1000"))
    _assert_refused(result, calls, "storm_control_broadcast_level_pps", "must be a native integer")


def test_an_unknown_action_is_refused():
    result, calls = _run(_cfg(enable_storm_control=True, storm_control_action="no"), "merged", _have())
    _assert_refused(result, calls, "storm_control_action")


# ------------------------------------------------------------------ keys, pair, version, batch
@pytest.mark.parametrize("extra", [
    {"peer1_members": ["Ethernet1/5"]}, {"peer1_pcid": 2}, {"peer1_description": "x"}, {"peer1_cmds": ["x"]},
    {"admin_state": False}, {"queuing_policy": "q"}, {"bpdu_guard": "true"}, {"mtu": "default"},
    {"peer1_allowed_vlans": "10"}, {"speed": "10Gb"},
])
def test_keys_owned_by_the_tor_pairing_are_refused(extra):
    result, calls = _run(_cfg(**extra), "merged", _have())
    _assert_refused(result, calls, "accepts only", sorted(extra)[0])
    assert _state_reads(calls) == []


def test_a_registered_key_of_another_parent_is_refused():
    result, calls = _run(_cfg(disable_lldp_transmit=True), "merged", _have())
    _assert_refused(result, calls, "disable_lldp_transmit")


@pytest.mark.parametrize("switch", [[h.SWITCH_IP], [h.SWITCH_IP, h.SWITCH_IP]])
def test_the_item_must_name_both_leaves(switch):
    result, calls = _run(_cfg(switch=switch, spanning_tree_port_type="network"), "merged", _have())
    _assert_refused(result, calls, "two switches of the leaf vPC pair")


def test_two_items_for_one_uplink_are_refused():
    configs = [_cfg(spanning_tree_port_type="network"),
               _cfg(switch=[h.PEER_IP, h.SWITCH_IP], spanning_tree_port_type="normal")]
    result, calls = _run(configs, "merged", _have())
    _assert_refused(result, calls, "more than one item")


@pytest.mark.parametrize("patch_version", [None, h.UNSUPPORTED_PATCH, h.PATCH_KEY_OMITTED])
def test_the_mode_needs_an_approved_patch_version(patch_version):
    result, calls = _run(_cfg(), "merged", _have(), patch_version=patch_version)
    _assert_refused(result, calls, "patch_version")


def test_an_older_ndfc_is_refused():
    result, calls = _run(_cfg(), "merged", _have(), ndfc_version=h.BELOW)
    _assert_refused(result, calls, "12.6.0.267")


@pytest.mark.parametrize("state", ["merged", "replaced", "overridden"])
def test_a_dcnm_11_controller_is_refused_before_any_request(state):
    result, calls = _run(_cfg(spanning_tree_port_type="network"), state, _have(),
                         extra_patch=patch.object(dcnm_interface, "dcnm_version_supported",
                                                  return_value=(11, "11.5.3")))
    assert result.get("failed") and "not a supported vPC mode" in result["msg"], result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("state", ["merged", "replaced", "overridden"])
def test_a_refused_later_item_stops_the_valid_first_item(state):
    configs = [_cfg(spanning_tree_port_type="network"), _cfg(name="vpc3", spanning_tree_port_type="network")]
    result, calls = _run(configs, state, _have())
    _assert_refused(result, calls, "vPC3", "no uplink vPC exists")


def test_query_returns_the_stored_parent_and_writes_nothing():
    result, calls = _run(_cfg(spanning_tree_port_type="network"), "query", _have(spanningTreePortType="network"))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []
    parents = [e for e in result["response"] if e.get("policy") == UL]
    assert parents and parents[0]["interfaces"][0]["nvPairs"] == dict(STORED, spanningTreePortType="network")


def test_numeric_nd_441_is_admitted():
    result, calls = _run(_cfg(spanning_tree_port_type="network"), "merged", _have(), patch_version="4.4.1")
    assert not result.get("failed"), result.get("msg")
    assert _modify(calls)["spanningTreePortType"] == "network"


# ------------------------------------------------------------------ ordinary paths untouched
def _created(calls):
    out = []
    for c in h.writes(calls):
        if c["path"].endswith("globalInterface"):
            out.extend(c["payload"] if isinstance(c["payload"], list) else [c["payload"]])
    return out


def test_an_ordinary_vpc_is_still_not_routed_to_the_uplink_path():
    result, calls = h.run_configs([h.cfg_for(h.VPC_TRUNK, h.BASE_VPC_TRUNK)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    assert _paths(calls) == ["POST globalInterface", "POST globalInterface/deploy"]
    assert {pol["policy"] for pol in _created(calls)} == {h.VPC_TRUNK}


def test_ordinary_vpc_storm_control_keeps_its_native_rules():
    profile = dict(h.BASE_VPC_TRUNK, enable_storm_control=True, storm_control_broadcast_level_percent="50")
    result, calls = h.run_configs([h.cfg_for(h.VPC_TRUNK, profile)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _created(calls)[0]["interfaces"][0]["nvPairs"]
    # The native builder still fills the action and the other levels.
    assert nv["STORM_CONTROL_ACTION"] == "no" and nv["STORM_CONTROL_BCAST_LEVEL_PERCENT"] == "50"
    assert nv["STORM_CONTROL_MCAST_LEVEL_PPS"] == ""
