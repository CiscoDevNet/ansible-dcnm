"""Retirement scope: resetting a physical Ethernet to its role default with registered fields configured.

int_routed_host realizes all its configuration in interface-scoped child policies and removes them in delete(); the
generator marks every one of its bindings dropped_on_policy_change. A leaf reset (int_routed_host -> int_trunk_host)
therefore proceeds for every consistent field group, with the same single write as a neutral routed port, and never
sends a source-only field or its key material. What stays refused: the border same-parent cases (EIGRP passive without
a verified reset; OSPF on with a tag) and the border transitions from the inline-rendered int_trunk_host and
int_access_host, whose cleanup is not established. Real main() through gie_withdrawal_harness; values are synthetic.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

import pytest

from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import gie_withdrawal_harness as h
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.test_dcnm_intf_default_reset_registered_f2 import (
    STATES,
    nvpairs_of_reset,
    reset_policies,
    reset_wire,
    run,
)

KEY = "SYNTHETIC-KEY-MATERIAL"
ROUTED_GROUPS = {
    "arp_bfd": {"arpTimeout": "1200", "bfdEcho": "true"},
    "dampening": {"dampening": "true", "dampeningHalfLife": "20", "dampeningReuse": "800", "dampeningSuppress": "2500",
                  "dampeningMaxSuppress": "80"},
    "pim": {"ENABLE_PIM_SPARSE": "true", "PIM_DR_PRIORITY": "10", "pimBfdInstance": "true"},
    "eigrp_routing": {"eigrpRouting": "true", "eigrpProcessTag": "SYN-EIGRP", "eigrpShutdown": "true", "eigrpBfd": "true"},
    "eigrp_passive": {"eigrpRouting": "true", "eigrpProcessTag": "SYN-EIGRP", "eigrpIpv4Passive": "true"},
    "eigrp_v6_dist": {"eigrpRouting": "true", "eigrpProcessTag": "SYN-EIGRP", "eigrpIpv6Routing": "true",
                      "eigrpIpv4DistributeListPrefixList": "SYN-PL", "eigrpIpv4DistributeListDirection": "in"},
    "ospf_base": {"ospf": "true", "OSPF_AREA_ID": "0.0.0.0"},
    "ospf_active": {"ospf": "true", "ospfTag": "SYN-OSPF", "OSPF_AREA_ID": "0.0.0.1", "ospfCost": "20",
                    "ospfNetworkType": "point_to_point"},
    "ospf_auth_md5": {"ospf": "true", "ospfTag": "SYN-OSPF", "ospfAuthentication": "true",
                      "ospfAuthenticationKey": "md5", "OSPF_AUTH_KEY_ID": "7", "OSPF_AUTH_KEY": KEY},
    "macsec": {"macsecInterfacePolicy": "true", "macsecKeyChainName": "SYN-KC", "macsecPolicyName": "SYN-MP"},
    "rt1_five": {"ipv4Redirects": "true", "ipv6Redirects": "true", "ipv4AclIn": "SYN-ACL", "ipv6LinkLocal": "fe80::1",
                 "ipv6NdSuppressRa": "true"},
}


def eth_have(parent, nv):
    have = copy.deepcopy(h.build_have(parent))
    base = have[0]["interfaces"][0]["nvPairs"]
    if parent == h.ROUTED and "ospf" not in nv:
        base["ospf"] = "false"          # the harness's routed base enables OSPF; other groups start from it off
    base.update(nv)
    return have


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("group", sorted(ROUTED_GROUPS))
def test_leaf_reset_of_a_routed_port_drops_every_group_with_one_write(state, group):
    _r0, calls0 = run(state, eth_have(h.ROUTED, {}), "leaf")
    result, calls = run(state, eth_have(h.ROUTED, ROUTED_GROUPS[group]), "leaf")
    assert not result.get("failed"), result.get("msg")
    assert reset_policies(calls)[0]["policy"] == h.TRUNK
    assert nvpairs_of_reset(calls) == nvpairs_of_reset(calls0)      # nothing of the group reaches int_trunk_host
    assert [(c["method"], c["path"]) for c in calls] == [(c["method"], c["path"]) for c in calls0]
    assert KEY not in str(calls) and KEY not in str(result)


@pytest.mark.parametrize("state", STATES)
def test_leaf_reset_keeps_the_destination_reset_for_fields_both_parents_register(state):
    result, calls = run(state, eth_have(h.ROUTED, {"lldpReceive": "true", "queuingStats": "true"}), "leaf")
    assert not result.get("failed"), result.get("msg")
    sent = nvpairs_of_reset(calls)
    assert sent["lldpReceive"] == reset_wire(h.TRUNK, "lldpReceive")
    assert sent["queuingStats"] == reset_wire(h.TRUNK, "queuingStats")


@pytest.mark.parametrize("state", STATES)
def test_second_leaf_run_over_the_reset_is_a_noop(state):
    _r1, calls1 = run(state, eth_have(h.ROUTED, ROUTED_GROUPS["ospf_auth_md5"]), "leaf")
    have = copy.deepcopy(reset_policies(calls1))
    have[0]["interfaces"][0].update(interfaceType="INTERFACE_ETHERNET", fabricName=h.FABRIC)
    result, calls = run(state, have, "leaf")
    assert not result.get("failed") and result["changed"] is False and h.writes(calls) == [], result.get("msg")


# ------------------------------------------------------------------ still refused (same parent, inline parents)
@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("group, text", [
    ("eigrp_passive", "eigrp_ipv4_passive (eigrpIpv4Passive) on %s [%s], parent int_routed_host"),
])
def test_border_same_parent_refusals_are_unchanged(state, group, text):
    result, calls = run(state, eth_have(h.ROUTED, ROUTED_GROUPS[group]), "border")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    assert (text % (h.IF_A, h.SERIAL) if "%s" in text else text) in result["msg"]
    assert KEY not in result["msg"]


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("parent, nv, field", [
    (h.TRUNK, {"aclFilter": "SYN-ACL"}, "acl_filter (aclFilter)"),
    (h.TRUNK, {"flowcontrolReceive": "on"}, "flowcontrol_receive (flowcontrolReceive)"),
    (h.TRUNK, {"spanningTreePortType": "network", "GUARD_MODE": "root"}, "guard_mode (GUARD_MODE)"),
    (h.ACCESS, {"aclFilter": "SYN-ACL"}, "acl_filter (aclFilter)"),
    (h.ACCESS, {"spanningTreePortType": "network"}, "spanning_tree_port_type (spanningTreePortType)"),
])
def test_border_transition_from_an_inline_parent_sends_the_routed_default(state, parent, nv, field):
    """P2: the controller negates the inline lines for this transition (cleared_on_change_to); the reset is the ordinary
    routed default and carries none of the source-only keys. test_gie_border_l2_retirement.py has the full matrix."""
    result, calls = run(state, eth_have(parent, nv), "border")
    assert not result.get("failed"), result.get("msg")
    assert reset_policies(calls)[0]["policy"] == h.ROUTED
    assert not any(k in nvpairs_of_reset(calls) for k in nv), field


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("group", ["arp_bfd", "dampening", "pim", "eigrp_routing", "macsec", "rt1_five", "ospf_base",
                                   "ospf_active"])
def test_border_same_parent_resets_with_verified_wires(state, group):
    result, calls = run(state, eth_have(h.ROUTED, ROUTED_GROUPS[group]), "border")
    assert not result.get("failed"), result.get("msg")
    sent = nvpairs_of_reset(calls)
    assert reset_policies(calls)[0]["policy"] == h.ROUTED
    for nvpair in ROUTED_GROUPS[group]:
        if nvpair == "ospfTag":
            assert nvpair not in sent        # D-3: inert under the final gate, kept stored, never sent
            continue
        if ROUTED_GROUPS[group][nvpair] == reset_wire(h.ROUTED, nvpair):
            continue                    # already the neutral value (e.g. area 0.0.0.0): nothing to withdraw
        assert sent.get(nvpair) == reset_wire(h.ROUTED, nvpair), nvpair
