"""Paired vPC withdrawal through the real dcnm_interface.main() path.

The VPC_SNO response shape and reversed pair order mirror ALPHA's m4-m7 GET
captures. All addresses, serials, members and policy names here are synthetic.
Controller and device behavior remains outside this offline test.
"""
from __future__ import absolute_import, division, print_function

import copy

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import BINDING_TABLE

from .gie_withdrawal_harness import (
    PEER_SERIAL, SERIAL, VPC_PAIR_SERIAL, VPC_ACCESS, VPC_TRUNK, ROUTED,
    base_for, cfg_for, diff_nvpairs, request_nvpairs, run_configs, split_calls, writes,
    _collect_policies,
)

TARGETS = {
    VPC_ACCESS: {"aclFilter": "", "lldpReceive": "false", "lldpTransmit": "false",
                 "qosStatsSuppressed": "false", "queuingStats": "false",
                 "spanningTreePortType": "no"},
    VPC_TRUNK: {"aclFilter": "", "lldpReceive": "false", "lldpTransmit": "false",
                "qosStatsSuppressed": "false", "queuingStats": "false",
                "spanningTreePortType": "no", "GUARD_MODE": "no"},
}
PUBLIC_KEYS = ("acl_filter", "disable_lldp_receive", "disable_lldp_transmit",
               "disable_qos_stats", "disable_queuing_stats", "spanning_tree_port_type",
               "guard_mode")


def _configs(positive):
    configs = []
    for parent in (VPC_ACCESS, VPC_TRUNK):
        profile = base_for(parent)
        if positive:
            profile.update(acl_filter="PILOT-ACL", disable_lldp_receive=True,
                           disable_lldp_transmit=True, disable_qos_stats=True,
                           disable_queuing_stats=True,
                           spanning_tree_port_type=("normal" if parent == VPC_ACCESS
                                                    else "network"))
            if parent == VPC_TRUNK:
                profile["guard_mode"] = "root"
        else:
            assert not set(PUBLIC_KEYS) & set(profile)
        configs.append(cfg_for(parent, profile))
    return configs


def _policies(calls):
    found = []
    _collect_policies([call["payload"] for call in writes(calls)], found)
    return {p["policy"]: p for p in found}


def _wire(policy):
    return policy["interfaces"][0]["nvPairs"]


def _assert_pair(policy, parent):
    iface = policy["interfaces"][0]
    assert policy["policy"] == parent
    assert iface["serialNumber"] == VPC_PAIR_SERIAL
    assert iface["interfaceType"] == "INTERFACE_VPC"
    assert iface["ifName"] == ("vPC11" if parent == VPC_ACCESS else "vPC12")
    nv = iface["nvPairs"]
    assert nv["PEER1_MEMBER_INTERFACES"] == nv["PEER2_MEMBER_INTERFACES"] == "Ethernet1/51"
    # The pair response orders peer 2 before peer 1. The module must remap
    # descriptions with that order rather than silently treating it as input order.
    assert nv["PEER1_PO_DESC"] == "pilot peer2"
    assert nv["PEER2_PO_DESC"] == "pilot peer1"
    assert nv["PORTTYPE_FAST_ENABLED"] == "false"
    assert nv["QOS_POLICY"] == "pilot_qos" and nv["QUEUING_POLICY"] == "pilot_queue"


def test_pair_main_path_positive_merged_check_replaced_and_rerun():
    positive, pos_calls = run_configs(_configs(True), "merged", [])
    assert not positive.get("failed") and positive["changed"]
    lookups = [c for c in pos_calls if c["method"] == "GET"
               and "vpcpair_serial_number" in c["path"]]
    assert len(lookups) == 2
    assert {c["path"].split("serial_number=")[1] for c in lookups} == {SERIAL, PEER_SERIAL}
    have_by_parent = _policies(pos_calls)
    assert set(have_by_parent) == set(TARGETS)
    for parent, policy in have_by_parent.items():
        _assert_pair(policy, parent)
        assert all(_wire(policy)[name] != reset for name, reset in TARGETS[parent].items())

    have = list(copy.deepcopy(have_by_parent).values())
    omitted = _configs(False)
    merged, merged_calls = run_configs(omitted, "merged", have)
    assert not merged.get("failed") and not merged["changed"]
    assert not request_nvpairs(merged_calls) and not split_calls(merged_calls)["updates"]

    checked, check_calls = run_configs(omitted, "replaced", have, check_mode=True)
    assert not checked.get("failed") and checked["changed"]
    assert not writes(check_calls)
    check_diff = {p["interfaces"][0]["ifName"]: _wire(p)
                  for p in checked["diff"][0]["replaced"]}
    assert set(check_diff) == {"vPC11", "vPC12"}
    for parent, name in ((VPC_ACCESS, "vPC11"), (VPC_TRUNK, "vPC12")):
        assert {k: check_diff[name][k] for k in TARGETS[parent]} == TARGETS[parent]

    replaced, replace_calls = run_configs(omitted, "replaced", have)
    assert not replaced.get("failed") and replaced["changed"]
    requests = _policies(replace_calls)
    assert set(requests) == set(TARGETS)
    assert len(split_calls(replace_calls)["updates"]) == 1
    assert len(split_calls(replace_calls)["deploys"]) == 1
    assert len(diff_nvpairs(replaced)) == 2
    for parent, policy in requests.items():
        _assert_pair(policy, parent)
        assert {k: _wire(policy)[k] for k in TARGETS[parent]} == TARGETS[parent]

    converged = copy.deepcopy(have)
    for item in converged:
        parent = item["policy"]
        _wire(item).update({k: _wire(requests[parent])[k] for k in TARGETS[parent]})
    rerun, rerun_calls = run_configs(omitted, "replaced", converged)
    assert not rerun.get("failed") and not rerun["changed"]
    assert not diff_nvpairs(rerun) and not writes(rerun_calls)


def test_pim_vpc_and_prior_routed_reset_coexist_as_separate_valid_interfaces():
    """One invocation carries a routed PIM profile and a distinct vPC profile."""
    routed = dict(base_for(ROUTED), enable_pim_sparse=True,
                  pim_dr_priority=77, disable_lldp_receive=True)
    vpc = dict(base_for(VPC_ACCESS), acl_filter="PILOT-ACL",
               disable_lldp_receive=True)
    positive = [cfg_for(ROUTED, routed), cfg_for(VPC_ACCESS, vpc)]
    applied, calls = run_configs(positive, "merged", [])
    assert not applied.get("failed") and applied["changed"]
    have = list(copy.deepcopy(_policies(calls)).values())
    assert {p["policy"] for p in have} == {ROUTED, VPC_ACCESS}

    routed.pop("pim_dr_priority")
    routed.pop("disable_lldp_receive")
    vpc.pop("acl_filter")
    vpc.pop("disable_lldp_receive")
    omitted = [cfg_for(ROUTED, routed), cfg_for(VPC_ACCESS, vpc)]
    result, replacement_calls = run_configs(omitted, "replaced", have)
    assert not result.get("failed") and result["changed"]
    sent = _policies(replacement_calls)
    assert set(sent) == {ROUTED, VPC_ACCESS}
    assert _wire(sent[ROUTED])["PIM_DR_PRIORITY"] == "1"
    assert _wire(sent[ROUTED])["ENABLE_PIM_SPARSE"] == "true"
    assert _wire(sent[ROUTED])["lldpReceive"] == "false"
    assert _wire(sent[VPC_ACCESS])["aclFilter"] == ""
    assert _wire(sent[VPC_ACCESS])["lldpReceive"] == "false"
    _assert_pair(sent[VPC_ACCESS], VPC_ACCESS)


@pytest.mark.parametrize("family", ("PIM/ACL", "vPC"))
def test_combined_case_fails_when_one_source_family_is_removed_in_memory(monkeypatch, family):
    """A green combined case must depend on both source families' registrations."""
    if family == "PIM/ACL":
        rows = [row for row in BINDING_TABLE
                if row["profile_key"] in ("enable_pim_sparse", "pim_dr_priority",
                                          "ipv4_acl_in", "enable_pim_bfd_instance")
                and row["parent_template"] in
                ("int_loopback", ROUTED, "int_subif", "int_vlan")]
        assert len(rows) == 10
    else:
        rows = [row for row in BINDING_TABLE
                if row["parent_template"] in (VPC_ACCESS, VPC_TRUNK)]
        assert len(rows) == 13
    with monkeypatch.context() as patcher:
        for row in rows:
            patcher.delitem(row, "reset_wire")
        with pytest.raises(AssertionError):
            test_pim_vpc_and_prior_routed_reset_coexist_as_separate_valid_interfaces()
