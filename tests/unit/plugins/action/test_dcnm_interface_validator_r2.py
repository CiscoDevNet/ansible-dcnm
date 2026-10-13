"""PR725-R2-VALIDATOR: the dcnm_interface integration checker must detect a requested nvPair that is wrong or missing.

Review 6132068174: the checker parsed both the expected data (built from the test YAML) and the readback through a
pydantic model that silently dropped every undeclared nvPair, and its YAML -> nvPair map did not cover the registry. A
requested ``flowcontrol_send: "on"`` read back as OFF, or not read back at all, still PASSED.

Every behaviour case below runs the REAL action plugin ``ndfc_interface_validate`` (schema, expected construction, DeepDiff
and the deepdiff post-processing): only Ansible's ``ActionBase.run`` bookkeeping is replaced, because the plugin is invoked
outside a play. The YAML is written to a real file and loaded by the plugin's own loader. Serials and addresses are
synthetic (documentation ranges); secrets are synthetic placeholders and must never be printed.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import patch

import pytest
import yaml
from ansible.plugins.action import ActionBase

from ansible_collections.cisco.dcnm.plugins.action.tests.integration import ndfc_interface_validate as validator

FABRIC = "r2-fabric"
SW1, SW2 = "192.0.2.11", "192.0.2.12"
SN1, SN2 = "R2SN0000001", "R2SN0000002"
TEST_DATA = {"fabric": FABRIC, "sw_sn": {SW1: SN1, SW2: SN2}}


class _Task(object):
    def __init__(self, args):
        self.args = args


def r2_run(tmp_path, config, readback, check_deleted=False, ignore_fields=None):
    """Drive the real ActionModule.run(); returns its result dict."""
    path = tmp_path / "r2_expected.yaml"
    path.write_text(yaml.safe_dump(config))
    action = object.__new__(validator.ActionModule)
    args = {"ndfc_data": readback, "test_data": TEST_DATA, "config_path": str(path), "check_deleted": check_deleted}
    if ignore_fields is not None:
        args["ignore_fields"] = ignore_fields
    action._task = _Task(args)
    with patch.object(ActionBase, "run", return_value={}):
        return action.run(task_vars={})


def r2_readback(policy, ifname, nvpairs, serial=SN1):
    nv = {"FABRIC_NAME": FABRIC}
    nv.update(nvpairs)
    return {"changed": False, "failed": False, "response": [{"policy": policy, "interfaces": [{"ifName": ifname, "serialNumber": serial, "nvPairs": nv}]}]}


def r2_eth(mode, ifname="eth1/21", **profile):
    prof = {"mode": mode}
    prof.update(profile)
    return {"name": ifname, "type": "eth", "switch": [SW1], "profile": prof}


# ============================================================================== 1. the reported reproductions
TRUNK_FC = r2_eth("trunk", flowcontrol_receive="on", flowcontrol_send="on")


def r2_trunk_readback(**nv):
    base = {"INTF_NAME": "Ethernet1/21"}
    base.update(nv)
    return r2_readback("int_trunk_host", "Ethernet1/21", base)


def test_r2_repro_send_off_must_fail(tmp_path):
    res = r2_run(tmp_path, [TRUNK_FC], r2_trunk_readback(flowcontrolReceive="on", flowcontrolSend="off"))
    assert res["failed"] is True, res["msg"]


def test_r2_repro_send_missing_must_fail(tmp_path):
    res = r2_run(tmp_path, [TRUNK_FC], r2_trunk_readback(flowcontrolReceive="on"))
    assert res["failed"] is True, res["msg"]


def test_r2_repro_control_receive_off_fails(tmp_path):
    res = r2_run(tmp_path, [TRUNK_FC], r2_trunk_readback(flowcontrolReceive="off", flowcontrolSend="on"))
    assert res["failed"] is True, res["msg"]


def test_r2_repro_control_both_correct_passes(tmp_path):
    res = r2_run(tmp_path, [TRUNK_FC], r2_trunk_readback(flowcontrolReceive="on", flowcontrolSend="on"))
    assert res["failed"] is False, res["msg"]


def test_r2_repro_ospf_cost_wrong_must_fail(tmp_path):
    cfg = r2_eth("routed", ospf_cost=10)
    res = r2_run(tmp_path, [cfg], r2_readback("int_routed_host", "Ethernet1/21", {"INTF_NAME": "Ethernet1/21", "ospfCost": "100"}))
    assert res["failed"] is True, res["msg"]


# ============================================================================== 2. coverage of the registered names
from ansible_collections.cisco.dcnm.plugins.action.tests.plugin_utils.pydantic_schemas.dcnm_interface import schemas as S  # noqa: E402
from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table as REG  # noqa: E402

R2_KIND_OF = {"boolean": "bool", "integer": "int", "enum": "enum"}


def r2_registry_kind(row):
    if row["type"] == "string":
        return "str_exact" if row.get("string_compare") == "exact" else "str_fold"
    return R2_KIND_OF[row["type"]]


def test_r2_coverage_every_registry_identity_is_mapped_or_an_explained_exception():
    unmapped, wrong = [], []
    for row in REG.BINDING_TABLE:
        ident = (row["parent_template"], row["parent_nvpair"])
        entry = S.R2_REGISTERED_BINDINGS.get(row["profile_key"])
        if entry is None:
            unmapped.append(ident)
            continue
        nvpair, kind, parents = entry
        if nvpair != row["parent_nvpair"] or kind != r2_registry_kind(row):
            wrong.append((ident, entry[:2]))
        if row["parent_template"] not in parents and ident not in S.R2_EXCEPTIONS:
            unmapped.append(ident)
        if row["parent_template"] in parents and ident in S.R2_EXCEPTIONS:
            wrong.append((ident, "listed both as mapped and as an exception"))
    assert unmapped == [] and wrong == [], (unmapped, wrong)
    for ident, reason in S.R2_EXCEPTIONS.items():
        assert reason and any((r["parent_template"], r["parent_nvpair"]) == ident for r in REG.BINDING_TABLE), ident


def test_r2_coverage_the_checker_invents_no_identity():
    registry = set((r["profile_key"], r["parent_template"]) for r in REG.BINDING_TABLE)
    checker = set((k, p) for k, (_nv, _kind, parents) in S.R2_REGISTERED_BINDINGS.items() for p in parents)
    assert checker <= registry, sorted(checker - registry)
    assert len(S.R2_REGISTERED_BINDINGS) == len(set(r["profile_key"] for r in REG.BINDING_TABLE)) == 76


def test_r2_coverage_wire_values_sensitive_names_and_parents_match_the_registry():
    wire = dict(((r["parent_template"], r["parent_nvpair"]), dict(r["wire_values"])) for r in REG.BINDING_TABLE if r.get("wire_values"))
    assert S.R2_WIRE_VALUES == wire
    assert S.R2_SENSITIVE_NVPAIRS == frozenset(r["parent_nvpair"] for r in REG.BINDING_TABLE if r.get("no_log"))
    reachable = set(S.R2_PARENT_BY_TYPE_MODE.values())
    assert set(r["parent_template"] for r in REG.BINDING_TABLE) <= reachable


# ============================================================================== 3. behaviour by family, through the real helper
R2_PARENT_YAML = {
    "int_trunk_host": ("eth", "trunk", "eth1/21", "Ethernet1/21"),
    "int_access_host": ("eth", "access", "eth1/21", "Ethernet1/21"),
    "int_routed_host": ("eth", "routed", "eth1/21", "Ethernet1/21"),
    "int_pvlan_host": ("eth", "pvlan", "eth1/21", "Ethernet1/21"),
    "int_port_channel_trunk_host": ("pc", "trunk", "po21", "Port-channel21"),
    "int_port_channel_access_host": ("pc", "access", "po21", "Port-channel21"),
    "int_port_channel_dot1q_tunnel_host": ("pc", "dot1q", "po21", "Port-channel21"),
    "int_port_channel_pvlan_host": ("pc", "pvlan", "po21", "Port-channel21"),
    "int_vpc_trunk_host": ("vpc", "trunk", "vpc21", "vPC21"),
    "int_vpc_access_host": ("vpc", "access", "vpc21", "vPC21"),
    "int_vpc_dot1q_tunnel": ("vpc", "dot1q", "vpc21", "vPC21"),
    "int_vpc_pvlan_host": ("vpc", "pvlan", "vpc21", "vPC21"),
    "int_subif": ("sub_int", "subint", "eth1/21.10", "Ethernet1/21.10"),
    "int_loopback": ("lo", "lo", "lo21", "Loopback21"),
    "int_vlan": ("svi", "vlan", "vlan21", "vlan21"),
}


def r2_cfg(parent, **profile):
    typ, mode, name, _full = R2_PARENT_YAML[parent]
    prof = {"mode": mode}
    prof.update(profile)
    switches = [SW1, SW2] if typ == "vpc" else [SW1]
    return {"name": name, "type": typ, "switch": switches, "profile": prof}


def r2_back(parent, nvpairs, extra_interfaces=()):
    typ, _mode, _name, full = R2_PARENT_YAML[parent]
    ident = {"PO_ID": full} if typ == "pc" else {"INTF_NAME": full}
    ident.update(nvpairs)
    rb = r2_readback(parent, full, ident, serial=(SN1 + "~" + SN2) if typ == "vpc" else SN1)
    for intf in extra_interfaces:
        rb["response"][0]["interfaces"].append(intf)
    return rb


def r2_row(profile_key, parent):
    return next(r for r in REG.BINDING_TABLE if r["profile_key"] == profile_key and r["parent_template"] == parent)


def r2_values(row):
    """(requested YAML value, the correct readback wire, a wrong readback wire) for one registry row."""
    if row["type"] == "boolean":
        return True, "true", "false"
    if row["type"] == "integer":
        lo = row.get("min_value", 1)
        return lo + 1, str(lo + 1), str(lo + 2)
    if row["type"] == "enum":
        values = list(row["valid_values"])
        wv = row.get("wire_values") or {}
        pick = next((v for v in values if wv.get(v, v) != v), values[0])
        other = next(v for v in values if v != pick)
        return pick, wv.get(pick, pick), wv.get(other, other)
    return "R2-Value-A", "R2-Value-A", "R2-Value-B"


def r2_registry_parents(profile_key):
    """Parents a value can be requested on, from the REGISTRY (independent of the checker's own table)."""
    return sorted(r["parent_template"] for r in REG.BINDING_TABLE if r["profile_key"] == profile_key and not r.get("smu_unsupported"))


R2_ONE_PARENT_PER_KEY = sorted((k, r2_registry_parents(k)[0]) for k in set(r["profile_key"] for r in REG.BINDING_TABLE) if r2_registry_parents(k))


@pytest.mark.parametrize("key, parent", R2_ONE_PARENT_PER_KEY, ids=["%s@%s" % kp for kp in R2_ONE_PARENT_PER_KEY])
def test_r2_every_registered_key_correct_passes_wrong_and_missing_fail(tmp_path, key, parent):
    row = r2_row(key, parent)
    requested, good, bad = r2_values(row)
    nv = row["parent_nvpair"]
    cfg = [r2_cfg(parent, **{key: requested})]
    assert r2_run(tmp_path, cfg, r2_back(parent, {nv: good}))["failed"] is False
    assert r2_run(tmp_path, cfg, r2_back(parent, {nv: bad}))["failed"] is True
    res = r2_run(tmp_path, cfg, r2_back(parent, {}))
    assert res["failed"] is True and nv in res["msg"]


ACL_PARENTS = r2_registry_parents("acl_filter")


@pytest.mark.parametrize("parent", ACL_PARENTS)
def test_r2_eth_po_vpc_parents_acl_filter(tmp_path, parent):
    cfg = [r2_cfg(parent, acl_filter="R2-ACL-A")]
    assert r2_run(tmp_path, cfg, r2_back(parent, {"aclFilter": "R2-ACL-A"}))["failed"] is False
    assert r2_run(tmp_path, cfg, r2_back(parent, {"aclFilter": "r2-acl-a"}))["failed"] is True   # exact: case matters (F1)
    assert r2_run(tmp_path, cfg, r2_back(parent, {}))["failed"] is True


@pytest.mark.parametrize(
    "parent, key, nvpair, requested, back",
    [
        ("int_trunk_host", "disable_lldp_receive", "lldpReceive", False, "false"),
        ("int_trunk_host", "disable_lldp_transmit", "lldpTransmit", False, "false"),
        ("int_routed_host", "ospf_cost", "ospfCost", 0, "0"),
        ("int_trunk_host", "acl_filter", "aclFilter", "", ""),
        ("int_routed_host", "ipv6_link_local", "ipv6LinkLocal", "FE80::A1", "fe80::a1"),      # casefold
        ("int_vlan", "private_vlan_mapping", "privateVlanMapping", "2211-2212", "2211-2212"),
    ],
)
def test_r2_false_zero_empty_and_folded_values_are_requested_values(tmp_path, parent, key, nvpair, requested, back):
    cfg = [r2_cfg(parent, **{key: requested})]
    assert r2_run(tmp_path, cfg, r2_back(parent, {nvpair: back}))["failed"] is False
    assert r2_run(tmp_path, cfg, r2_back(parent, {}))["failed"] is True                      # not dropped by truthiness


def test_r2_native_readback_types_compare_as_nvpair_strings(tmp_path):
    cfg = [r2_cfg("int_routed_host", ospf_cost=10, disable_lldp_receive=True)]
    assert r2_run(tmp_path, cfg, r2_back("int_routed_host", {"ospfCost": 10, "lldpReceive": True}))["failed"] is False
    assert r2_run(tmp_path, cfg, r2_back("int_routed_host", {"ospfCost": 100, "lldpReceive": True}))["failed"] is True


def test_r2_null_is_an_omission_not_a_request(tmp_path):
    cfg = [r2_cfg("int_trunk_host", flowcontrol_receive="on", flowcontrol_send=None)]
    assert r2_run(tmp_path, cfg, r2_back("int_trunk_host", {"flowcontrolReceive": "on"}))["failed"] is False


def test_r2_enum_uses_the_parent_wire_spelling(tmp_path):
    cfg = [r2_cfg("int_routed_host", ospf_network_type="point_to_point")]
    assert r2_run(tmp_path, cfg, r2_back("int_routed_host", {"ospfNetworkType": "pointToPoint"}))["failed"] is False
    assert r2_run(tmp_path, cfg, r2_back("int_routed_host", {"ospfNetworkType": "broadcast"}))["failed"] is True


# ---- sensitive values: compared, never printed
R2_FAKE_VALUE = "R2-Synthetic-K1"


@pytest.mark.parametrize("key, nvpair, ctx", [
    ("ospf_auth_key", "OSPF_AUTH_KEY", {}),
    ("ospf_authentication_key", "ospfAuthenticationKey", {}),
])
def test_r2_sensitive_values_are_compared_and_never_printed(tmp_path, capsys, key, nvpair, ctx):
    cfg = [r2_cfg("int_routed_host", **dict(ctx, **{key: R2_FAKE_VALUE}))]
    ok = r2_run(tmp_path, cfg, r2_back("int_routed_host", {nvpair: R2_FAKE_VALUE}))
    bad = r2_run(tmp_path, cfg, r2_back("int_routed_host", {nvpair: R2_FAKE_VALUE + "-other"}))
    missing = r2_run(tmp_path, cfg, r2_back("int_routed_host", {}))
    out = capsys.readouterr().out
    assert ok["failed"] is False and bad["failed"] is True and missing["failed"] is True
    for text in (ok["msg"], bad["msg"], missing["msg"], out):
        assert R2_FAKE_VALUE not in text
    assert nvpair in bad["msg"] and S.R2_REDACTED in bad["msg"]


# ---- PVLAN lists, native/allowed and members of the PVLAN parents
def r2_wrap(key, rows):
    import json
    return json.dumps({key: [{"P_VLAN": str(p), "S_VLAN": str(s)} for p, s in rows]})


def test_r2_pvlan_eth_association_list_semantic(tmp_path):
    cfg = [r2_cfg("int_pvlan_host", pvlan_mode="host", pvlan_association=[{"primary_vlan": 2210, "secondary_vlan": 2212}])]
    good = {"PVLAN_MODE": "host", "ASSOCIATION_LIST": r2_wrap("ASSOCIATION_LIST", [(2210, 2212)])}
    assert r2_run(tmp_path, cfg, r2_back("int_pvlan_host", good))["failed"] is False
    bad = dict(good, ASSOCIATION_LIST=r2_wrap("ASSOCIATION_LIST", [(2210, 2211)]))
    assert r2_run(tmp_path, cfg, r2_back("int_pvlan_host", bad))["failed"] is True
    assert r2_run(tmp_path, cfg, r2_back("int_pvlan_host", {"PVLAN_MODE": "host"}))["failed"] is True
    assert r2_run(tmp_path, cfg, r2_back("int_pvlan_host", dict(good, PVLAN_MODE="promiscuous")))["failed"] is True


def test_r2_pvlan_po_mapping_range_native_allowed_and_members(tmp_path):
    cfg = [r2_cfg("int_port_channel_pvlan_host", pvlan_mode="trunk promiscuous", members=["eth1/30", "e1/31"],
                  pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2211-2212"}], native_vlan="2301", allowed_vlans="2301,2302")]
    good = {"PVLAN_MODE": "trunk promiscuous", "MAPPING_LIST": r2_wrap("MAPPING_LIST", [(2210, 2212), (2210, 2211)]),
            "PVLAN_NATIVE_VLAN": "2301", "PVLAN_ALLOWED_VLANS": "2301-2302", "MEMBER_INTERFACES": "Ethernet1/31,Ethernet1/30"}
    assert r2_run(tmp_path, cfg, r2_back("int_port_channel_pvlan_host", good))["failed"] is False
    for k, v in (("MAPPING_LIST", r2_wrap("MAPPING_LIST", [(2210, 2211)])), ("PVLAN_ALLOWED_VLANS", "2301"),
                 ("PVLAN_NATIVE_VLAN", "2302"), ("MEMBER_INTERFACES", "Ethernet1/30")):
        assert r2_run(tmp_path, cfg, r2_back("int_port_channel_pvlan_host", dict(good, **{k: v})))["failed"] is True, k
    assert "NATIVE_VLAN" not in S.DcnmInterfaceQuerySchema.yaml_config_to_dict(cfg, FABRIC)["response"][0]["interfaces"][0]["nvPairs"]


def test_r2_pvlan_vpc_per_peer_native_allowed_and_registered_companion(tmp_path):
    cfg = [r2_cfg("int_vpc_pvlan_host", pvlan_mode="trunk secondary", pvlan_association=[{"primary_vlan": 2210, "secondary_vlan": 2212}],
                  peer1_native_vlan="2301", peer2_native_vlan="2302", peer1_allowed_vlans="2301", peer2_allowed_vlans="2302",
                  disable_qos_stats=True)]
    good = {"PVLAN_MODE": "trunk secondary", "ASSOCIATION_LIST": r2_wrap("ASSOCIATION_LIST", [(2210, 2212)]),
            "PEER1_PVLAN_NATIVE_VLAN": "2301", "PEER2_PVLAN_NATIVE_VLAN": "2302", "PEER1_PVLAN_ALLOWED_VLANS": "2301",
            "PEER2_PVLAN_ALLOWED_VLANS": "2302", "qosStatsSuppressed": "true"}
    assert r2_run(tmp_path, cfg, r2_back("int_vpc_pvlan_host", good))["failed"] is False
    swapped = dict(good, PEER1_PVLAN_NATIVE_VLAN="2302", PEER2_PVLAN_NATIVE_VLAN="2301")
    assert r2_run(tmp_path, cfg, r2_back("int_vpc_pvlan_host", swapped))["failed"] is True
    assert r2_run(tmp_path, cfg, r2_back("int_vpc_pvlan_host", dict(good, qosStatsSuppressed="false")))["failed"] is True


# ============================================================================== 4. no false failures, identity, deleted, diagnostics
def test_r2_unrequested_nvpairs_and_controller_metadata_do_not_fail(tmp_path):
    cfg = [r2_cfg("int_trunk_host", flowcontrol_send="on")]
    back = r2_back("int_trunk_host", {"flowcontrolSend": "on", "flowcontrolReceive": "off", "lldpReceive": "true", "ospfCost": 1,
                                      "SOME_FUTURE_KEY": "x", "POLICY_ID": "POLICY-0", "PRIORITY": 500})
    back["response"][0]["interfaces"][0]["deleteReason"] = None
    back["extra_top_level"] = {"anything": True}
    assert r2_run(tmp_path, cfg, back)["failed"] is False


def test_r2_values_are_never_matched_across_interfaces(tmp_path):
    cfg = [r2_eth("trunk", "eth1/21", flowcontrol_send="on"), r2_eth("trunk", "eth1/22", flowcontrol_send="off")]
    swapped = {"changed": False, "failed": False, "response": [{"policy": "int_trunk_host", "interfaces": [
        {"ifName": "Ethernet1/21", "serialNumber": SN1, "nvPairs": {"FABRIC_NAME": FABRIC, "INTF_NAME": "Ethernet1/21", "flowcontrolSend": "off"}},
        {"ifName": "Ethernet1/22", "serialNumber": SN1, "nvPairs": {"FABRIC_NAME": FABRIC, "INTF_NAME": "Ethernet1/22", "flowcontrolSend": "on"}}]}]}
    res = r2_run(tmp_path, cfg, swapped)
    assert res["failed"] is True and "ethernet1/21" in res["msg"] and "ethernet1/22" in res["msg"]


def test_r2_vpc_identity_needs_both_peers_in_any_order(tmp_path):
    cfg = [r2_cfg("int_vpc_trunk_host", acl_filter="R2-ACL-A")]
    back = r2_back("int_vpc_trunk_host", {"aclFilter": "R2-ACL-A"})
    back["response"][0]["interfaces"][0]["serialNumber"] = SN2 + "~" + SN1
    assert r2_run(tmp_path, cfg, back)["failed"] is False
    back["response"][0]["interfaces"][0]["serialNumber"] = SN1
    res = r2_run(tmp_path, cfg, back)
    assert res["failed"] is True and "not found" in res["msg"]


def test_r2_requested_interface_absent_fails(tmp_path):
    res = r2_run(tmp_path, [r2_eth("trunk", "eth1/23", flowcontrol_send="on")], r2_trunk_readback(flowcontrolSend="on"))
    assert res["failed"] is True and "not found" in res["msg"]


@pytest.mark.parametrize("parent, key, value, reason", [
    ("int_routed_host", "acl_filter", "R2-ACL-A", "not a registered field of the expected parent int_routed_host"),
    ("int_port_channel_trunk_host", "enable_vpc_peer_link", True, "smu_unsupported"),
])
def test_r2_unrepresentable_requests_are_diagnosed_never_passed(tmp_path, parent, key, value, reason):
    nv = S.R2_REGISTERED_BINDINGS[key][0]
    res = r2_run(tmp_path, [r2_cfg(parent, **{key: value})], r2_back(parent, {nv: S._r2_native(value)}))
    assert res["failed"] is True and "cannot be validated" in res["msg"] and key in res["msg"] and reason in res["msg"], res["msg"]


def test_r2_unknown_parent_is_diagnosed(tmp_path):
    cfg = [r2_eth("dot1q", flowcontrol_send="on")]
    res = r2_run(tmp_path, cfg, r2_trunk_readback(flowcontrolSend="on"))
    assert res["failed"] is True and "flowcontrol_send" in res["msg"], res["msg"]


def test_r2_yaml_config_to_dict_raises_without_a_diagnostics_list():
    with pytest.raises(ValueError, match="cannot be validated"):
        S.DcnmInterfaceQuerySchema.yaml_config_to_dict([r2_cfg("int_routed_host", acl_filter="R2-ACL-A")], FABRIC)


@pytest.mark.parametrize("present, failed", [(False, False), (True, True)])
def test_r2_check_deleted_partial_is_unchanged_even_with_an_unrepresentable_field(tmp_path, present, failed):
    cfg = [r2_cfg("int_routed_host", acl_filter="R2-ACL-A")]          # unrepresentable, but deletion only checks identity
    back = r2_back("int_routed_host", {}) if present else {"changed": False, "failed": False, "response": []}
    assert r2_run(tmp_path, cfg, back, check_deleted=True)["failed"] is failed


def test_r2_check_deleted_full_delete_unchanged(tmp_path):
    action = object.__new__(validator.ActionModule)
    empty = {"changed": False, "failed": False, "response": []}
    action._task = _Task({"ndfc_data": empty, "test_data": TEST_DATA, "config_path": "", "check_deleted": True})
    with patch.object(ActionBase, "run", return_value={}):
        assert action.run(task_vars={})["failed"] is False
    action._task = _Task({"ndfc_data": r2_back("int_trunk_host", {}), "test_data": TEST_DATA, "config_path": "", "check_deleted": True})
    with patch.object(ActionBase, "run", return_value={}):
        assert action.run(task_vars={})["failed"] is True


# ---- legacy controls
def test_r2_legacy_fields_still_compared(tmp_path):
    cfg = [r2_cfg("int_vpc_access_host", description="R2 legacy", mtu="jumbo", peer1_members=["Ethernet1/40"], peer2_members=["Ethernet1/40"],
                  peer1_pcid=21, peer2_pcid=21, admin_state=False)]
    good = {"DESC": "R2 legacy", "MTU": "jumbo", "PEER1_MEMBER_INTERFACES": "Ethernet1/40", "PEER2_MEMBER_INTERFACES": "Ethernet1/40",
            "PEER1_PCID": "21", "PEER2_PCID": "21", "ADMIN_STATE": "false", "CDP_ENABLE": "true"}
    assert r2_run(tmp_path, cfg, r2_back("int_vpc_access_host", good))["failed"] is False
    assert r2_run(tmp_path, cfg, r2_back("int_vpc_access_host", dict(good, DESC="other")))["failed"] is True
    assert r2_run(tmp_path, cfg, r2_back("int_vpc_access_host", dict(good, ADMIN_STATE="true")))["failed"] is True


def test_r2_legacy_empty_config_path_without_check_deleted_still_fails(tmp_path):
    action = object.__new__(validator.ActionModule)
    action._task = _Task({"ndfc_data": r2_back("int_trunk_host", {}), "test_data": TEST_DATA, "config_path": ""})
    with patch.object(ActionBase, "run", return_value={}):
        assert action.run(task_vars={})["failed"] is True
