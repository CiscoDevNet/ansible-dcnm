"""OFFLINE coexistence of the SVI-list, mapping-reset and vPC-dot1q deliveries."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

from .gie_withdrawal_harness import (
    SVI,
    VPC_DOT1Q,
    VPC_PAIR_SERIAL,
    _collect_policies,
    base_for,
    build_have,
    cfg_for,
    diff_nvpairs,
    run_configs,
    split_calls,
)

MAPPING = "3214,3216"
SECONDARY_GWS = [
    {"gateway_ip_address": "198.51.100.254/24"},
    {"gateway_ip_address": "203.0.113.254/24"},
]
SECONDARY_VIPS = [
    {"hsrp_secondary_vip": "192.0.2.123"},
    {"hsrp_secondary_vip": "192.0.2.133"},
]
GWS_WIRE = '{"secondaryGws":[{"gatewayIpAddress":"198.51.100.254/24"},{"gatewayIpAddress":"203.0.113.254/24"}]}'
VIPS_WIRE = '{"hsrpSecondaryVips":[{"hsrpSecondaryVip":"192.0.2.123"},{"hsrpSecondaryVip":"192.0.2.133"}]}'
PRIMARY = {
    "ipv4_addr": "192.0.2.1",
    "ipv4_mask_len": 24,
    "enable_hsrp": True,
    "hsrp_vip": "192.0.2.253",
    "hsrp_group": 1,
    "hsrp_version": 1,
}
DOT1Q_POSITIVE = {
    "acl_filter": "PILOT-ACL",
    "spanning_tree_port_type": "normal",
    "disable_qos_stats": True,
    "disable_queuing_stats": True,
    "disable_lldp_transmit": True,
    "disable_lldp_receive": True,
}
DOT1Q_RESETS = {
    "aclFilter": "",
    "spanningTreePortType": "no",
    "qosStatsSuppressed": "false",
    "queuingStats": "false",
    "lldpTransmit": "false",
    "lldpReceive": "false",
}


def configs():
    svi = base_for(SVI, **dict(PRIMARY, secondary_gws=copy.deepcopy(SECONDARY_GWS), hsrp_secondary_vips=copy.deepcopy(SECONDARY_VIPS)))
    # The mapping is intentionally omitted. Both lists are explicit and nonempty.
    return [cfg_for(SVI, svi), cfg_for(VPC_DOT1Q, base_for(VPC_DOT1Q))]


def configured_have():
    svi = build_have(SVI, "private_vlan_mapping", MAPPING, **PRIMARY)
    svi_nv = svi[0]["interfaces"][0]["nvPairs"]
    svi_nv["secondaryGws"] = GWS_WIRE
    svi_nv["hsrpSecondaryVips"] = VIPS_WIRE
    svi[0]["interfaces"][0]["interfaceType"] = "INTERFACE_VLAN"
    return svi + build_have(VPC_DOT1Q, **DOT1Q_POSITIVE)


def request_policies(calls):
    found = []
    _collect_policies([c["payload"] for c in split_calls(calls)["updates"]], found)
    return {policy["policy"]: policy for policy in found}


def assert_exact_resets_and_preservation(policies):
    assert set(policies) == {SVI, VPC_DOT1Q}

    svi = policies[SVI]["interfaces"][0]
    svi_nv = svi["nvPairs"]
    assert svi["interfaceType"] == "INTERFACE_VLAN"
    assert svi_nv["privateVlanMapping"] == ""
    assert svi_nv["secondaryGws"] == GWS_WIRE
    assert svi_nv["hsrpSecondaryVips"] == VIPS_WIRE
    assert svi_nv["IP"] == "192.0.2.1" and svi_nv["PREFIX"] == "24"
    assert svi_nv["ENABLE_HSRP"] == "true" and svi_nv["HSRP_VIP"] == "192.0.2.253"

    dot1q = policies[VPC_DOT1Q]["interfaces"][0]
    dot1q_nv = dot1q["nvPairs"]
    assert dot1q["interfaceType"] == "INTERFACE_VPC"
    assert dot1q["serialNumber"] == VPC_PAIR_SERIAL
    assert {key: dot1q_nv[key] for key in DOT1Q_RESETS} == DOT1Q_RESETS
    # The pair is controller-ordered in the request; every peer-specific identity differs.
    assert (dot1q_nv["PEER1_PCID"], dot1q_nv["PEER2_PCID"]) == ("14", "13")
    assert (dot1q_nv["PEER1_MEMBER_INTERFACES"], dot1q_nv["PEER2_MEMBER_INTERFACES"]) == (
        "Ethernet1/54",
        "Ethernet1/53",
    )
    assert (dot1q_nv["PEER1_ACCESS_VLAN"], dot1q_nv["PEER2_ACCESS_VLAN"]) == (
        "3802",
        "3801",
    )


def synthetic_post_apply_have(policies):
    have = []
    for policy in (policies[SVI], policies[VPC_DOT1Q]):
        item = copy.deepcopy(policy)
        item["interfaces"][0]["fabricName"] = "test_fabric"
        have.append(item)
    return have


def test_offline_union_resets_both_objects_and_preserves_explicit_lists_in_one_main_call():
    result, calls = run_configs(configs(), "replaced", have=configured_have())
    assert not result.get("failed"), result.get("msg")
    policies = request_policies(calls)
    assert_exact_resets_and_preservation(policies)


def test_offline_union_check_mode_plans_without_mutating_stub_calls():
    result, calls = run_configs(configs(), "replaced", have=configured_have(), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert result.get("changed") is True
    buckets = split_calls(calls)
    assert buckets["updates"] == [] and buckets["deploys"] == [] and buckets["other"] == []
    planned = diff_nvpairs(result)
    svi = next(nv for nv in planned if "privateVlanMapping" in nv)
    dot1q = next(nv for nv in planned if "aclFilter" in nv)
    assert svi["privateVlanMapping"] == ""
    assert "secondaryGws" not in svi and "hsrpSecondaryVips" not in svi
    assert {key: dot1q[key] for key in DOT1Q_RESETS} == DOT1Q_RESETS


def test_offline_union_synthetic_post_apply_have_converges():
    applied, calls = run_configs(configs(), "replaced", have=configured_have())
    assert not applied.get("failed"), applied.get("msg")
    post_apply = synthetic_post_apply_have(request_policies(calls))

    result, rerun_calls = run_configs(configs(), "replaced", have=post_apply)
    assert not result.get("failed"), result.get("msg")
    assert result.get("changed") is False
    buckets = split_calls(rerun_calls)
    assert buckets["updates"] == [] and buckets["deploys"] == [] and buckets["other"] == []
