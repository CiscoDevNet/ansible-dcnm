"""vPC dot1q-tunnel (``type: vpc``, ``profile.mode: dot1q``) through the real ``main()``.

The parent is ``int_vpc_dot1q_tunnel``. Its six generic bindings (acl_filter,
spanning_tree_port_type, disable_qos_stats, disable_queuing_stats, disable_lldp_transmit,
disable_lldp_receive) carry, in candidate c2, the reset of their explicit neutral: '' for the
ACL, 'no' for the port type, 'false' for the four booleans. c2 is used only after those neutrals
were measured on this parent on both peers. An omission under ``replaced`` therefore withdraws
exactly the omitted field and nothing else; under ``merged`` it still preserves.

The harness pair answers with the controller order REVERSED from the playbook order
(``VPC_PAIR_SERIAL = PEER~SERIAL`` while the playbook lists ``[SWITCH, PEER]``), and every
per-peer value differs between the peers, so a wrong peer mapping cannot pass by coincidence.

Offline: no controller and no device.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    BINDING_TABLE,
)

from .gie_withdrawal_harness import (
    PEER_IP,
    SWITCH_IP,
    VPC_ACCESS,
    VPC_DOT1Q,
    VPC_PAIR_SERIAL,
    _collect_policies,
    base_for,
    build_have,
    cfg_for,
    diff_nvpairs,
    run_configs,
    split_calls,
    writes,
)

RESETS = {
    "acl_filter": "",
    "spanning_tree_port_type": "no",
    "disable_qos_stats": "false",
    "disable_queuing_stats": "false",
    "disable_lldp_transmit": "false",
    "disable_lldp_receive": "false",
}
GENERIC = {
    "acl_filter": ("aclFilter", "PILOT-ACL"),
    "spanning_tree_port_type": ("spanningTreePortType", "normal"),
    "disable_qos_stats": ("qosStatsSuppressed", True),
    "disable_queuing_stats": ("queuingStats", True),
    "disable_lldp_transmit": ("lldpTransmit", True),
    "disable_lldp_receive": ("lldpReceive", True),
}
POSITIVE = {k: v for k, (_n, v) in GENERIC.items()}


def dot1q(**extra):
    return base_for(VPC_DOT1Q, **extra)


def conf(profile, switches=None):
    c = cfg_for(VPC_DOT1Q, profile)
    if switches is not None:
        c["switch"] = switches
    return c


def run(profile, state, have=None, check=False, switches=None, configs=None):
    return run_configs(configs or [conf(profile, switches)], state, have=have, check_mode=check)


def policies(calls):
    found = []
    _collect_policies([c["payload"] for c in writes(calls)], found)
    return found


def only_request(calls):
    ups = split_calls(calls)["updates"]
    assert len(ups) == 1, ups
    found = policies(calls)
    assert len(found) == 1, found
    return found[0]


def no_writes(calls):
    b = split_calls(calls)
    return b["updates"] == [] and b["deploys"] == [] and b["other"] == []


def have(**extra):
    return build_have(VPC_DOT1Q, **extra)


# ------------------------------------------------------------------ selection and pair mapping
def test_merged_create_selects_the_dot1q_tunnel_parent_with_the_supplied_values():
    result, calls = run(dot1q(**POSITIVE), "merged")
    assert not result.get("failed"), result.get("msg")
    pol = only_request(calls)
    assert pol["policy"] == "int_vpc_dot1q_tunnel"
    iface = pol["interfaces"][0]
    assert iface["serialNumber"] == VPC_PAIR_SERIAL and iface["interfaceType"] == "INTERFACE_VPC"
    assert iface["ifName"] == "vPC13"
    nv = iface["nvPairs"]
    for key, (nvpair, value) in GENERIC.items():
        expected = str(value).lower() if isinstance(value, bool) else value
        assert nv[nvpair] == expected, (key, nv.get(nvpair))
    assert nv["PC_MODE"] == "active" and nv["MTU"] == "jumbo"
    assert nv["PORTTYPE_FAST_ENABLED"] == "false" and nv["BPDUGUARD_ENABLED"] == "no"


def test_reversed_playbook_order_maps_every_per_peer_value_to_the_controller_peer():
    """Playbook [SWITCH, PEER]; controller pair PEER~SERIAL: controller PEER1 is the playbook's
    second switch, so it must receive every peer2 value."""
    result, calls = run(dot1q(), "merged", switches=[SWITCH_IP, PEER_IP])
    assert not result.get("failed"), result.get("msg")
    nv = only_request(calls)["interfaces"][0]["nvPairs"]
    assert (nv["PEER1_PCID"], nv["PEER2_PCID"]) == ("14", "13")
    assert (nv["PEER1_MEMBER_INTERFACES"], nv["PEER2_MEMBER_INTERFACES"]) == ("Ethernet1/54", "Ethernet1/53")
    assert (nv["PEER1_ACCESS_VLAN"], nv["PEER2_ACCESS_VLAN"]) == ("3802", "3801")
    assert (nv["PEER1_PO_DESC"], nv["PEER2_PO_DESC"]) == ("dot1q peer2", "dot1q peer1")


def test_playbook_order_matching_the_controller_order_is_not_swapped():
    result, calls = run(dot1q(), "merged", switches=[PEER_IP, SWITCH_IP])
    assert not result.get("failed"), result.get("msg")
    nv = only_request(calls)["interfaces"][0]["nvPairs"]
    assert (nv["PEER1_PCID"], nv["PEER2_PCID"]) == ("13", "14")
    assert (nv["PEER1_MEMBER_INTERFACES"], nv["PEER2_MEMBER_INTERFACES"]) == ("Ethernet1/53", "Ethernet1/54")
    assert (nv["PEER1_ACCESS_VLAN"], nv["PEER2_ACCESS_VLAN"]) == ("3801", "3802")


def test_a_switch_list_that_is_not_the_pair_is_refused_before_any_request():
    result, calls = run(dot1q(), "merged", switches=[SWITCH_IP, SWITCH_IP])
    assert result.get("failed") and "vPC pair" in result.get("msg", "")
    assert no_writes(calls)


# ------------------------------------------------------------------ merged
def test_merged_rerun_converges():
    prof = dot1q(**POSITIVE)
    result, calls = run(prof, "merged", have=have(**POSITIVE))
    assert not result.get("failed"), result.get("msg")
    assert split_calls(calls)["updates"] == [] and result["changed"] is False


def test_merged_update_preserves_omitted_generic_fields():
    """A native change under merged; the six generic fields are omitted and travel as HAVE."""
    result, calls = run(dot1q(peer1_description="changed p1"), "merged", have=have(**POSITIVE))
    assert not result.get("failed"), result.get("msg")
    nv = only_request(calls)["interfaces"][0]["nvPairs"]
    assert nv["aclFilter"] == "PILOT-ACL" and nv["spanningTreePortType"] == "normal"
    for nvpair in ("qosStatsSuppressed", "queuingStats", "lldpTransmit", "lldpReceive"):
        assert nv[nvpair] == "true", nvpair
    assert "changed p1" in (nv["PEER1_PO_DESC"], nv["PEER2_PO_DESC"])


def test_merged_member_change_touches_only_the_intended_peer():
    """Members are a merged UNION (native, shared with access/trunk): the playbook's peer1 --
    controller PEER2 -- gains Ethernet1/55 next to Ethernet1/53; the other peer is untouched."""
    prof = dot1q(peer1_members=["Ethernet1/55"])        # playbook peer1 = controller PEER2
    result, calls = run(prof, "merged", have=have())
    assert not result.get("failed"), result.get("msg")
    nv = only_request(calls)["interfaces"][0]["nvPairs"]
    assert sorted(nv["PEER2_MEMBER_INTERFACES"].split(",")) == ["Ethernet1/53", "Ethernet1/55"]
    assert nv["PEER1_MEMBER_INTERFACES"] == "Ethernet1/54"


def test_replaced_member_change_is_exact_and_confined_to_one_peer():
    prof = dot1q(peer1_members=["Ethernet1/55"])
    result, calls = run(prof, "replaced", have=have())
    assert not result.get("failed"), result.get("msg")
    nv = only_request(calls)["interfaces"][0]["nvPairs"]
    assert nv["PEER2_MEMBER_INTERFACES"] == "Ethernet1/55"
    assert nv["PEER1_MEMBER_INTERFACES"] == "Ethernet1/54"


# ------------------------------------------------------------------ replaced: measured resets
@pytest.mark.parametrize("key", sorted(GENERIC))
def test_replaced_omission_withdraws_only_the_omitted_field(key):
    result, calls = run(dot1q(**{k: v for k, v in POSITIVE.items() if k != key}), "replaced",
                        have=have(**POSITIVE))
    assert not result.get("failed"), result.get("msg")
    nv = only_request(calls)["interfaces"][0]["nvPairs"]
    for k, (nvpair, _v) in GENERIC.items():
        if k == key:
            assert nv[nvpair] == RESETS[k], (k, nv[nvpair])
        else:
            assert nv[nvpair] != RESETS[k], "%s was withdrawn with %s" % (k, key)


@pytest.mark.parametrize("key", sorted(GENERIC))
def test_check_mode_plans_the_same_withdrawal_and_sends_nothing(key):
    result, calls = run(dot1q(**{k: v for k, v in POSITIVE.items() if k != key}), "replaced",
                        have=have(**POSITIVE), check=True)
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is True
    planned = diff_nvpairs(result)
    assert planned and all(p[GENERIC[key][0]] == RESETS[key] for p in planned), planned
    assert no_writes(calls)


def test_replaced_omission_at_the_declared_default_needs_nothing():
    """HAVE at the template defaults: the omission has nothing to withdraw and is accepted."""
    result, calls = run(dot1q(), "replaced", have=have())
    assert not result.get("failed"), result.get("msg")
    assert split_calls(calls)["updates"] == []


def test_replaced_resets_native_fields_but_keeps_generic_values_it_was_given():
    """Native defaults and generic values are separate: a replaced run that gives all six
    generic fields and omits a native description writes the native default and the six as given."""
    prof = dot1q(**POSITIVE)
    prof.pop("peer2_description")
    result, calls = run(prof, "replaced", have=have(**POSITIVE))
    assert not result.get("failed"), result.get("msg")
    nv = only_request(calls)["interfaces"][0]["nvPairs"]
    assert "" in (nv["PEER1_PO_DESC"], nv["PEER2_PO_DESC"])
    assert nv["aclFilter"] == "PILOT-ACL" and nv["lldpTransmit"] == "true"


def test_check_mode_plans_a_native_change_and_sends_nothing():
    result, calls = run(dot1q(**dict(POSITIVE, peer1_description="plan")), "replaced",
                        have=have(**POSITIVE), check=True)
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is True and diff_nvpairs(result)
    assert no_writes(calls)


def test_the_six_resets_are_this_parents_own_rows():
    rows = {r["profile_key"]: r for r in BINDING_TABLE if r["parent_template"] == VPC_DOT1Q}
    assert {k: r.get("reset_wire") for k, r in rows.items()} == RESETS
    assert all(isinstance(r["reset_wire"], str) for r in rows.values())


def test_the_sibling_vpc_access_parent_is_not_touched_by_a_dot1q_withdrawal():
    """The same omission on each parent writes that parent's own template, never the other."""
    acc = base_for(VPC_ACCESS)
    r_acc, c_acc = run_configs([cfg_for(VPC_ACCESS, acc)], "replaced",
                               have=build_have(VPC_ACCESS, disable_lldp_transmit=True))
    r_dq, c_dq = run(dot1q(), "replaced", have=have(disable_lldp_transmit=True))
    assert not r_acc.get("failed") and not r_dq.get("failed"), (r_acc.get("msg"), r_dq.get("msg"))
    assert only_request(c_acc)["policy"] == VPC_ACCESS
    dq = only_request(c_dq)
    assert dq["policy"] == VPC_DOT1Q and dq["interfaces"][0]["nvPairs"]["lldpTransmit"] == "false"


# ------------------------------------------------------------------ the campaign masks, offline
# The live stages use these exact profiles; each plan is proven here first.
MASK_B_POS = {"spanning_tree_port_type": "network", "disable_queuing_stats": True,
              "disable_lldp_receive": True}
CAMPAIGN_POS = dict(POSITIVE, spanning_tree_port_type="network")
WIRE_MASK_A = {"aclFilter": "", "spanningTreePortType": "network", "qosStatsSuppressed": "false",
               "queuingStats": "true", "lldpTransmit": "false", "lldpReceive": "true"}


def test_r3_merged_omission_of_mask_a_preserves_everything():
    result, calls = run(dot1q(**MASK_B_POS), "merged", have=have(**CAMPAIGN_POS))
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is False and no_writes(calls)


def test_r4_r5_replaced_omission_of_mask_a_withdraws_exactly_mask_a():
    result, calls = run(dot1q(**MASK_B_POS), "replaced", have=have(**CAMPAIGN_POS))
    assert not result.get("failed"), result.get("msg")
    nv = only_request(calls)["interfaces"][0]["nvPairs"]
    assert {k: nv[k] for k in WIRE_MASK_A} == WIRE_MASK_A


def test_r6_replaced_rerun_at_mask_a_converges():
    mask_a_have = dict(MASK_B_POS, acl_filter="", disable_qos_stats=False,
                       disable_lldp_transmit=False)
    result, calls = run(dot1q(**MASK_B_POS), "replaced", have=have(**mask_a_have))
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is False and no_writes(calls)


def test_r7_replaced_omission_of_mask_b_on_top_withdraws_the_rest():
    mask_a_have = dict(MASK_B_POS, acl_filter="", disable_qos_stats=False,
                       disable_lldp_transmit=False)
    result, calls = run(dot1q(), "replaced", have=have(**mask_a_have))
    assert not result.get("failed"), result.get("msg")
    nv = only_request(calls)["interfaces"][0]["nvPairs"]
    assert {GENERIC[k][0]: nv[GENERIC[k][0]] for k in GENERIC} == {
        GENERIC[k][0]: v for k, v in RESETS.items()}


# ------------------------------------------------------------------ input boundaries
def test_a_field_registered_only_on_another_parent_is_refused():
    result, calls = run(dot1q(guard_mode="root"), "merged")
    assert result.get("failed") and "guard_mode" in result.get("msg", "")
    assert no_writes(calls)


@pytest.mark.parametrize("mode", ["monitor", "routed", "trunk_typo"])
def test_an_unsupported_vpc_mode_is_refused_before_any_request(mode):
    result, calls = run(dot1q(mode=mode), "merged")
    assert result.get("failed") and "vPC mode" in result.get("msg", "")
    assert no_writes(calls)


def test_dot1q_is_refused_on_a_controller_without_the_template():
    """DCNM 11 has no int_vpc_dot1q_tunnel in pol_types: refused, not a KeyError."""
    from unittest.mock import patch
    from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module
    result, calls = run_configs([conf(dot1q())], "merged",
                                extra_patch=patch.object(module, "dcnm_version_supported",
                                                         return_value=11))
    assert result.get("failed") and "vPC mode" in result.get("msg", ""), result.get("msg")
    assert "dot1q" in result.get("msg", "") and no_writes(calls)


# ------------------------------------------------------------------ lifecycle
def test_query_returns_the_object():
    result, calls = run_configs([{"name": "vpc13", "switch": [SWITCH_IP]}], "query", have=have())
    assert not result.get("failed"), result.get("msg")
    assert no_writes(calls)
    assert "int_vpc_dot1q_tunnel" in repr(result.get("response"))


def test_deleted_names_only_this_vpc():
    other = copy.deepcopy(have()[0])
    other["interfaces"][0]["ifName"] = "vPC21"
    result, calls = run_configs([{"name": "vpc13", "type": "vpc", "switch": [SWITCH_IP, PEER_IP]}],
                                "deleted", have=have() + [other])
    assert not result.get("failed"), result.get("msg")
    sent = repr([c["payload"] for c in writes(calls)] + [c["path"] for c in writes(calls)]).lower()
    assert "vpc13" in sent and "vpc21" not in sent


def test_overridden_retained_object_follows_replaced():
    """Retained by overridden with a configured LLDP field omitted: withdrawn like replaced."""
    result, calls = run(dot1q(), "overridden", have=have(disable_lldp_receive=True))
    assert not result.get("failed"), result.get("msg")
    sent = [p for p in policies(calls) if p.get("policy") == VPC_DOT1Q]
    assert sent and sent[0]["interfaces"][0]["nvPairs"]["lldpReceive"] == "false"
