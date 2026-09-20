# Binding engine unit tests.
#
# Covers intent survival (profile key -> parent nvPair), explicit-only emission, omission
# semantics, value types, and version fail-closed for a registered key. The OSPF-MD
# unsupported-version path stays with the module's compatibility hook and is covered by
# test_dcnm_intf_ospfmd_have_fetch and test_dcnm_ospfmd_parent_child_contract.
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import hashlib
import importlib.util
import json
from pathlib import Path
import pytest
import yaml
from unittest import mock
from ansible_collections.cisco.dcnm.plugins.module_utils import (
    gie_binding_table,
    gie_engine,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    BINDING_TABLE, PROVENANCE_SHA256, registered_profile_keys, resolve_binding,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    gie_version_supported, gie_extend_prof_spec, gie_contribute_nvpairs,
    gie_validator_type, gie_all_registered_keys, gie_guarded_keys,
    gie_invalid_parent_key, gie_nvpair_keymap, gie_carry_forward_bindings,
    gie_validate_binding_value,
    GieBindingError,
)

TRUNK = "int_trunk_host"
ACCESS = "int_access_host"
LOOPBACK = "int_fabric_loopback_11_1"
PC_TRUNK = "int_port_channel_trunk_host"
PC_ACCESS = "int_port_channel_access_host"
PC_DOT1Q = "int_port_channel_dot1q_tunnel_host"
ROUTED = "int_routed_host"
VPC_TRUNK = "int_vpc_trunk_host"
VPC_ACCESS = "int_vpc_access_host"

# Baseline rows. These three and their behaviour must not change.
BASELINE_ROWS = {
    (ACCESS, "FLOWCONTROL_RECEIVE", "flowcontrol_receive"),
    (TRUNK, "FLOWCONTROL_RECEIVE", "flowcontrol_receive"),
}
# Simple passthrough rows.
PASSTHROUGH_ROWS = {
    (TRUNK, "GUARD_MODE", "guard_mode"),
    (PC_TRUNK, "GUARD_MODE", "guard_mode"),
    (ACCESS, "DISABLE_LLDP_TRANSMIT", "disable_lldp_transmit"),
    (ACCESS, "DISABLE_LLDP_RECEIVE", "disable_lldp_receive"),
    (TRUNK, "DISABLE_LLDP_TRANSMIT", "disable_lldp_transmit"),
    (TRUNK, "DISABLE_LLDP_RECEIVE", "disable_lldp_receive"),
    (ACCESS, "ACL_FILTER", "acl_filter"),
    (TRUNK, "ACL_FILTER", "acl_filter"),
    (PC_ACCESS, "ACL_FILTER", "acl_filter"),
    (PC_TRUNK, "ACL_FILTER", "acl_filter"),
    (PC_DOT1Q, "ACL_FILTER", "acl_filter"),
}
# The OSPF legacy-key pair. Both rows feed the SAME child (ospf_interface_auth), so both
# are child_pti on the loopback parent.
# FLOWCONTROL_SEND, companion of the receive rows. Only these two parents carry FLOWCONTROL,
# so these two rows plus the receive pair close the field's universe.
FC_SEND_ROWS = {
    (TRUNK, "FLOWCONTROL_SEND", "flowcontrol_send"),
    (ACCESS, "FLOWCONTROL_SEND", "flowcontrol_send"),
}
# SPANNING_TREE_PORT_TYPE is NOT independent: the template rejects a non-"no" value while
# PORTTYPE_FAST_ENABLED is true, and true is the default on both sides. That relation is
# deliberately not registered -- the precondition lives in a field the registry does not own.
STP_ROWS = {
    (TRUNK, "SPANNING_TREE_PORT_TYPE", "spanning_tree_port_type"),
    (ACCESS, "SPANNING_TREE_PORT_TYPE", "spanning_tree_port_type"),
}
# QoS statistics. Neither field emits a CLI line of its own: each is the " no-stats" suffix of
# the service-policy line its dependency produces, so with the dependency unmet the value is
# stored on the controller and is a silent no-op on the device.
QOS_STATS_ROWS = {
    (TRUNK, "DISABLE_QOS_STATS", "disable_qos_stats"),
    (ACCESS, "DISABLE_QOS_STATS", "disable_qos_stats"),
    (TRUNK, "DISABLE_QUEUING_STATS", "disable_queuing_stats"),
    (ACCESS, "DISABLE_QUEUING_STATS", "disable_queuing_stats"),
}
# The same four fields on the port-channel host parents. Each was originally registered only on
# the parents under test at the time; the port-channel templates declare them too, and an
# unregistered binding does not fail -- the module answers "not supported on this interface",
# which is false.
#
# DISABLE_LLDP is included to MEASURE it, not because it is known to work: on these parents the
# template delegates the value to the member policy instead of emitting the CLI itself. Whether
# it reaches the member is an empirical question, answered by the lab, not by preference.
PC_ROWS = {
    (PC_ACCESS, "DISABLE_LLDP_TRANSMIT", "disable_lldp_transmit"),
    (PC_ACCESS, "DISABLE_LLDP_RECEIVE", "disable_lldp_receive"),
    (PC_TRUNK, "DISABLE_LLDP_TRANSMIT", "disable_lldp_transmit"),
    (PC_TRUNK, "DISABLE_LLDP_RECEIVE", "disable_lldp_receive"),
    (PC_DOT1Q, "DISABLE_LLDP_TRANSMIT", "disable_lldp_transmit"),
    (PC_DOT1Q, "DISABLE_LLDP_RECEIVE", "disable_lldp_receive"),
    (PC_ACCESS, "SPANNING_TREE_PORT_TYPE", "spanning_tree_port_type"),
    (PC_TRUNK, "SPANNING_TREE_PORT_TYPE", "spanning_tree_port_type"),
    (PC_DOT1Q, "SPANNING_TREE_PORT_TYPE", "spanning_tree_port_type"),
    (PC_ACCESS, "DISABLE_QOS_STATS", "disable_qos_stats"),
    (PC_TRUNK, "DISABLE_QOS_STATS", "disable_qos_stats"),
    (PC_DOT1Q, "DISABLE_QOS_STATS", "disable_qos_stats"),
    (PC_ACCESS, "DISABLE_QUEUING_STATS", "disable_queuing_stats"),
    (PC_TRUNK, "DISABLE_QUEUING_STATS", "disable_queuing_stats"),
    (PC_DOT1Q, "DISABLE_QUEUING_STATS", "disable_queuing_stats"),
}

# The two vPC host parents. These are the only vPC parents the module can reach: it builds its
# policy key as <type>_<mode> and pol_types carries just "vpc_trunk" and "vpc_access".
#
# Every one of these delegates -- the vPC parent emits no CLI of its own, it hands the value to
# an intermediate _po_11_1 child and, for DISABLE_LLDP, down to a _po_member_11_1. They are still
# `passthrough`, because that word describes who owns validation, the invalid-parent guard, the
# generic prof_spec, carry-forward and wire-form conversion -- not what the template does next.
# int_port_channel_trunk_host::DISABLE_LLDP set the precedent: it delegates too and is
# passthrough.
#
# Measured before registering: GUARD_MODE=root written into the vpc55 parent's nvPairs produced
# `spanning-tree guard root` on both peers of the pair.
#
# GUARD_MODE appears on trunk only -- int_vpc_access_host does not declare it.
VPC_ROWS = {
    (VPC_TRUNK, "SPANNING_TREE_PORT_TYPE", "spanning_tree_port_type"),
    (VPC_ACCESS, "SPANNING_TREE_PORT_TYPE", "spanning_tree_port_type"),
    (VPC_TRUNK, "DISABLE_LLDP_TRANSMIT", "disable_lldp_transmit"),
    (VPC_TRUNK, "DISABLE_LLDP_RECEIVE", "disable_lldp_receive"),
    (VPC_ACCESS, "DISABLE_LLDP_TRANSMIT", "disable_lldp_transmit"),
    (VPC_ACCESS, "DISABLE_LLDP_RECEIVE", "disable_lldp_receive"),
    (VPC_TRUNK, "ACL_FILTER", "acl_filter"),
    (VPC_ACCESS, "ACL_FILTER", "acl_filter"),
    (VPC_TRUNK, "GUARD_MODE", "guard_mode"),
    (VPC_TRUNK, "DISABLE_QOS_STATS", "disable_qos_stats"),
    (VPC_ACCESS, "DISABLE_QOS_STATS", "disable_qos_stats"),
    (VPC_TRUNK, "DISABLE_QUEUING_STATS", "disable_queuing_stats"),
    (VPC_ACCESS, "DISABLE_QUEUING_STATS", "disable_queuing_stats"),
}

# int_routed_host -- the first non-switchport parent. Reachable as pol_types "eth_routed".
#
# Every one of these ends in a child template; none of them emits CLI from the parent itself:
# interface_lldp_disable, bfd_no_echo_interface, interface_ip_access_group_in_11_1 and, for the
# stats pair, interface_qos_service_policy / interface_queuing_service_policy, where the boolean
# rides as the child's DISABLE_STATS parameter rather than gating its creation. All five were
# confirmed present on the controller before registering -- a missing child returns success and
# silently emits nothing.
#
# ARP_TIMEOUT is declared by this template too and is deliberately absent: int_subif and
# int_vlan declare it as well and all three are reachable, so it goes in as one lot across the
# three parents. The generator enforces that, not a reviewer.
ROUTED_ROWS = {
    (ROUTED, "DISABLE_LLDP_TRANSMIT", "disable_lldp_transmit"),
    (ROUTED, "DISABLE_LLDP_RECEIVE", "disable_lldp_receive"),
    (ROUTED, "DISABLE_BFD_ECHO", "disable_bfd_echo"),
    (ROUTED, "IPV4_ACL_IN", "ipv4_acl_in"),
    (ROUTED, "DISABLE_QOS_STATS", "disable_qos_stats"),
    (ROUTED, "DISABLE_QUEUING_STATS", "disable_queuing_stats"),
}

# The OSPF vertical slice on the same parent. Separate set because it is the first feature
# registered here that is gated (IsShow="ENABLE_OSPF==true"), and because OSPF_COST is the
# first integer binding to reach the generic carry-forward -- see
# test_gie_routed_ospf_have_representation.py.
ROUTED_OSPF_ROWS = {
    (ROUTED, "ENABLE_OSPF", "enable_ospf"),
    (ROUTED, "OSPF_TAG", "ospf_tag"),
    (ROUTED, "OSPF_AREA_ID", "ospf_area_id"),
    (ROUTED, "OSPF_COST", "ospf_cost"),
    (ROUTED, "OSPF_MTU_IGNORE", "ospf_mtu_ignore"),
    (ROUTED, "OSPF_SHUTDOWN", "ospf_shutdown"),
    (ROUTED, "OSPF_HELLO_INTERVAL", "ospf_hello_interval"),
    (ROUTED, "OSPF_DEAD_INTERVAL", "ospf_dead_interval"),
    (ROUTED, "OSPF_TRANSMIT_DELAY", "ospf_transmit_delay"),
    (ROUTED, "OSPF_PRIORITY", "ospf_priority"),
    (ROUTED, "OSPF_PASSIVE_MODE", "ospf_passive_mode"),
    (ROUTED, "OSPF_NETWORK_TYPE", "ospf_network_type"),
    (ROUTED, "OSPF_BFD_MODE", "ospf_bfd_mode"),
}


# The two parents registered for the OSPF work. Listed separately from ROUTED_OSPF_ROWS because
# they are NOT the same set: int_subif models passive and bfd as booleans where the other two use
# enums, and both carry OSPF_RETRANSMIT_INTERVAL, which int_routed_host does not declare at all.
SUBIF_OSPF_ROWS = {
    ("int_subif", "ENABLE_OSPF", "enable_ospf"),
    ("int_subif", "OSPF_AREA_ID", "ospf_area_id"),
    ("int_subif", "OSPF_BFD", "ospf_bfd"),
    ("int_subif", "OSPF_COST", "ospf_cost"),
    ("int_subif", "OSPF_DEAD_INTERVAL", "ospf_dead_interval"),
    ("int_subif", "OSPF_HELLO_INTERVAL", "ospf_hello_interval"),
    ("int_subif", "OSPF_MTU_IGNORE", "ospf_mtu_ignore"),
    ("int_subif", "OSPF_NETWORK_TYPE", "ospf_network_type"),
    ("int_subif", "OSPF_PASSIVE_INTERFACE", "ospf_passive_interface"),
    ("int_subif", "OSPF_PRIORITY", "ospf_priority"),
    ("int_subif", "OSPF_RETRANSMIT_INTERVAL", "ospf_retransmit_interval"),
    ("int_subif", "OSPF_SHUTDOWN", "ospf_shutdown"),
    ("int_subif", "OSPF_TAG", "ospf_tag"),
    ("int_subif", "OSPF_TRANSMIT_DELAY", "ospf_transmit_delay"),
}

VLAN_OSPF_ROWS = {
    ("int_vlan", "ENABLE_OSPF", "enable_ospf"),
    ("int_vlan", "OSPF_AREA_ID", "ospf_area_id"),
    ("int_vlan", "OSPF_BFD_MODE", "ospf_bfd_mode"),
    ("int_vlan", "OSPF_COST", "ospf_cost"),
    ("int_vlan", "OSPF_DEAD_INTERVAL", "ospf_dead_interval"),
    ("int_vlan", "OSPF_HELLO_INTERVAL", "ospf_hello_interval"),
    ("int_vlan", "OSPF_MTU_IGNORE", "ospf_mtu_ignore"),
    ("int_vlan", "OSPF_NETWORK_TYPE", "ospf_network_type"),
    ("int_vlan", "OSPF_PASSIVE_MODE", "ospf_passive_mode"),
    ("int_vlan", "OSPF_PRIORITY", "ospf_priority"),
    ("int_vlan", "OSPF_RETRANSMIT_INTERVAL", "ospf_retransmit_interval"),
    ("int_vlan", "OSPF_SHUTDOWN", "ospf_shutdown"),
    ("int_vlan", "OSPF_TAG", "ospf_tag"),
    ("int_vlan", "OSPF_TRANSMIT_DELAY", "ospf_transmit_delay"),
}


# The authentication lot is one set for three parents, not three sets, because the slice that
# registers it is one slice for three parents. The other OSPF families each get their own set
# above, mirroring their own per-parent slices -- this one is shaped like what it describes.
AUTH_OSPF_ROWS = {
    (parent, nvpair, key)
    for parent in ("int_routed_host", "int_subif", "int_vlan")
    for nvpair, key in (
        ("ENABLE_OSPF_AUTH", "enable_ospf_auth"),
        ("OSPF_AUTH_KEY_ID", "ospf_auth_key_id"),
        ("OSPF_AUTH_KEY", "ospf_auth_key"),
        ("OSPF_AUTHENTICATION_KEY_TYPE", "ospf_authentication_key_type"),
        ("OSPF_AUTHENTICATION_KEY", "ospf_authentication_key"),
    )
}

# EIGRP, slice 0b_22. The same comprehension shape as AUTH_OSPF_ROWS, and for the same reason:
# all thirteen fields are identical on the three overlay parents -- type, default, bounds and
# valid values -- which was measured against the controller's own bodies rather than assumed.
# The OSPF scalars needed one set per parent because those templates genuinely diverge.
EIGRP_ROWS = {
    (parent, nvpair, key)
    for parent in ("int_routed_host", "int_subif", "int_vlan")
    for nvpair, key in (
        ("EIGRP_PROCESS_TAG", "eigrp_process_tag"),
        ("ENABLE_EIGRP_ROUTING", "enable_eigrp_routing"),
        ("ENABLE_EIGRP_IPV6_ROUTING", "enable_eigrp_ipv6_routing"),
        ("EIGRP_IPV4_PASSIVE", "eigrp_ipv4_passive"),
        ("EIGRP_NO_IPV4_PASSIVE", "eigrp_no_ipv4_passive"),
        ("EIGRP_NO_IPV6_PASSIVE", "eigrp_no_ipv6_passive"),
        ("ENABLE_EIGRP_SHUTDOWN", "enable_eigrp_shutdown"),
        ("ENABLE_EIGRP_BFD", "enable_eigrp_bfd"),
        ("DISABLE_EIGRP_BFD", "disable_eigrp_bfd"),
        ("EIGRP_IPV4_DISTRIBUTE_LIST_PREFIX_LIST", "eigrp_ipv4_distribute_list_prefix_list"),
        ("EIGRP_IPV4_DISTRIBUTE_LIST_DIRECTION", "eigrp_ipv4_distribute_list_direction"),
        ("EIGRP_IPV6_DISTRIBUTE_LIST_PREFIX_LIST", "eigrp_ipv6_distribute_list_prefix_list"),
        ("EIGRP_IPV6_DISTRIBUTE_LIST_DIRECTION", "eigrp_ipv6_distribute_list_direction"),
    )
}

# int_loopback, slice 0b_23 -- the USER loopback (mode 'lo'), not int_fabric_loopback_11_1.
# Its own set, not a comprehension shared with another parent, because this template diverges
# from all three overlay parents: OSPF_ADVERTISE_SUBNET exists nowhere else, OSPF_BFD is a
# boolean here as on int_subif while routed and vlan use the enum OSPF_BFD_MODE, and
# OSPF_PASSIVE_MODE is absent entirely.
LOOPBACK_OSPF_ROWS = {
    ("int_loopback", nvpair, key)
    for nvpair, key in (
        ("ENABLE_OSPF", "enable_ospf"),
        ("OSPF_TAG", "ospf_tag"),
        ("OSPF_AREA_ID", "ospf_area_id"),
        ("OSPF_ADVERTISE_SUBNET", "ospf_advertise_subnet"),
        ("OSPF_COST", "ospf_cost"),
        ("OSPF_HELLO_INTERVAL", "ospf_hello_interval"),
        ("OSPF_DEAD_INTERVAL", "ospf_dead_interval"),
        ("OSPF_RETRANSMIT_INTERVAL", "ospf_retransmit_interval"),
        ("OSPF_TRANSMIT_DELAY", "ospf_transmit_delay"),
        ("OSPF_PRIORITY", "ospf_priority"),
        ("OSPF_MTU_IGNORE", "ospf_mtu_ignore"),
        ("OSPF_SHUTDOWN", "ospf_shutdown"),
        ("OSPF_NETWORK_TYPE", "ospf_network_type"),
        ("OSPF_BFD", "ospf_bfd"),
        # The five the architect ruled in scope here while they stay retired on the fabric
        # parent: the retirement was about ownership, and a user loopback is not underlay.
        ("ENABLE_OSPF_AUTH", "enable_ospf_auth"),
        ("OSPF_AUTH_KEY_ID", "ospf_auth_key_id"),
        ("OSPF_AUTH_KEY", "ospf_auth_key"),
        ("OSPF_AUTHENTICATION_KEY_TYPE", "ospf_authentication_key_type"),
        ("OSPF_AUTHENTICATION_KEY", "ospf_authentication_key"),
    )
}

# BFD, committed 2026-09-19 from slices 0b_4 and 0b_5 with their mechanism corrected to
# passthrough, plus the one new row of 0b_24. int_routed_host declares DISABLE_BFD_ECHO and no
# interval field; int_loopback has no interface BFD at all.
BFD_ROWS = {
    (parent, nvpair, key)
    for parent in ("int_subif", "int_vlan")
    for nvpair, key in (
        ("ENABLE_BFD_INTERVAL", "enable_bfd_interval"),
        ("BFD_TX_INTERVAL", "bfd_tx_interval"),
        ("BFD_MIN_RX_INTERVAL", "bfd_min_rx_interval"),
        ("BFD_MULTIPLIER", "bfd_multiplier"),
    )
} | {("int_vlan", "DISABLE_BFD_ECHO", "disable_bfd_echo")}

# EIGHT of the family's thirteen, on int_loopback alone (slice 0b_25). Listed explicitly rather
# than reusing EIGRP_ROWS' comprehension with a fourth parent, because the sets are NOT the same:
# the installed int_loopback declares no ENABLE_EIGRP_IPV6_ROUTING and none of the four
# distribute-list fields. Sharing the comprehension would assert a uniformity the controller does
# not have, and would have pinned five bindings NDFC discards in silence.
LOOPBACK_EIGRP_ROWS = {
    ("int_loopback", nvpair, key)
    for nvpair, key in (
        ("EIGRP_PROCESS_TAG", "eigrp_process_tag"),
        ("ENABLE_EIGRP_ROUTING", "enable_eigrp_routing"),
        ("EIGRP_IPV4_PASSIVE", "eigrp_ipv4_passive"),
        ("EIGRP_NO_IPV4_PASSIVE", "eigrp_no_ipv4_passive"),
        ("EIGRP_NO_IPV6_PASSIVE", "eigrp_no_ipv6_passive"),
        ("ENABLE_EIGRP_SHUTDOWN", "enable_eigrp_shutdown"),
        ("ENABLE_EIGRP_BFD", "enable_eigrp_bfd"),
        ("DISABLE_EIGRP_BFD", "disable_eigrp_bfd"),
    )
}





# HSRP on int_vlan, slice 0b_26. Three, and only on this parent: it is the only one of the four
# that declares HSRP at all. Listed explicitly because these three are the first rows that sit on
# top of MODULE-NATIVE fields -- enable_hsrp, hsrp_vip, hsrp_group, preempt and hsrp_priority are
# already in the native SVI arg spec, so the engine's contribution is exactly this set and no
# more. A fourth entry here would mean the engine had taken over a field the module already owns.
HSRP_ROWS = {
    ("int_vlan", nvpair, key)
    for nvpair, key in (
        ("HSRP_PRIORITY_FORWARDING_THRESHOLD_LOWER", "hsrp_priority_forwarding_threshold_lower"),
        ("HSRP_PRIORITY_FORWARDING_THRESHOLD_UPPER", "hsrp_priority_forwarding_threshold_upper"),
        ("HSRP_PREEMPT_DELAY_MINIMUM", "hsrp_preempt_delay_minimum"),
    )
}

# ---- binding package runtime contract ----

def test_package_provenance_and_size():
    expected_keys = (
        BASELINE_ROWS | PASSTHROUGH_ROWS | FC_SEND_ROWS | STP_ROWS
        | QOS_STATS_ROWS | PC_ROWS | VPC_ROWS | ROUTED_ROWS | ROUTED_OSPF_ROWS
        | SUBIF_OSPF_ROWS | VLAN_OSPF_ROWS | AUTH_OSPF_ROWS | EIGRP_ROWS
        | LOOPBACK_OSPF_ROWS | BFD_ROWS | LOOPBACK_EIGRP_ROWS | HSRP_ROWS
    )
    actual_keys = {
        (b["parent_template"], b["parent_nvpair"], b["profile_key"])
        for b in BINDING_TABLE
    }
    assert len(BINDING_TABLE) == len(actual_keys) == 189
    assert actual_keys == expected_keys
    # The baseline rows must survive verbatim inside the larger table.
    assert BASELINE_ROWS <= actual_keys
    assert len(PASSTHROUGH_ROWS) == 11
    assert len(FC_SEND_ROWS) == 2
    assert len(STP_ROWS) == 2
    assert len(QOS_STATS_ROWS) == 4
    assert len(PC_ROWS) == 15
    assert len(ROUTED_ROWS) == 6
    assert len(ROUTED_OSPF_ROWS) == 13
    assert len(SUBIF_OSPF_ROWS) == 14
    assert len(VLAN_OSPF_ROWS) == 14
    assert len(AUTH_OSPF_ROWS) == 15   # five fields x three parents
    # EIGHT, and the assertion is the point: the family has thirteen and the installed
    # int_loopback declares only these eight. A thirteen here would mean five bindings NDFC
    # discards in silence while the module reports success.
    assert len(LOOPBACK_EIGRP_ROWS) == 8
    # THREE, and the number is the assertion: the engine adds only what the native arg
    # spec lacks. A four here would mean it had absorbed a module-owned field.
    assert len(HSRP_ROWS) == 3
    expected_provenance = hashlib.sha256(
        json.dumps(BINDING_TABLE, sort_keys=True, default=list).encode()
    ).hexdigest()
    assert PROVENANCE_SHA256 == expected_provenance


def _load_generator():
    path = (
        Path(gie_binding_table.__file__).resolve().parents[2]
        / "tools"
        / "gie_generate_binding_table.py"
    )
    spec = importlib.util.spec_from_file_location("gie_table_generator_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_compiler_accepts_exact_committed_binding_set():
    generator = _load_generator()
    rows = generator.compile_rows([dict(binding) for binding in BINDING_TABLE])
    assert len(rows) == 189


def test_compiler_rejects_duplicate_or_missing_binding():
    generator = _load_generator()
    rows = [dict(binding) for binding in BINDING_TABLE]
    with pytest.raises(ValueError, match="duplicate committed binding"):
        generator.compile_rows(rows + [dict(rows[0])])
    with pytest.raises(ValueError, match="missing committed bindings"):
        generator.compile_rows(rows[:-1])


def test_compiler_renames_the_registry_numeric_bounds():
    """registry `min`/`max` -> table `min_value`/`max_value`, values intact.

    The other compiler tests feed BINDING_TABLE back in, which already carries the renamed
    fields, so none of them exercises the alias. This one starts from the REGISTRY shape.

    The rename is not cosmetic: `min` and `max` are prefixes of `min_ndfc_version` and
    `min_length`, and a substring test for "min" -- the obvious way to go looking for these --
    matches those instead. That is how 15 declared bounds stayed unenforced.
    """
    generator = _load_generator()
    rows = []
    for binding in BINDING_TABLE:
        row = dict(binding)
        if row["parent_nvpair"] == "OSPF_COST":
            row.pop("min_value", None)
            row.pop("max_value", None)
            row["min"] = 1            # registry spelling
            row["max"] = 65535
        rows.append(row)
    compiled = generator.compile_rows(rows)
    cost = next(r for r in compiled if r["parent_nvpair"] == "OSPF_COST")
    assert cost["min_value"] == 1
    assert cost["max_value"] == 65535
    assert "min" not in cost and "max" not in cost, "the registry spelling must not leak"


def test_compiler_rejects_an_unknown_mechanism():
    """Fail-open guard.

    gie_engine compares `== GIE_MECH_PASSTHROUGH` at four sites, so an unknown value behaves
    exactly like child_pti: out of the generic arg spec, out of the invalid-parent guard, left
    unserialized, out of carry-forward. A typo would ship a binding that is transported but
    never guarded. It must not compile.
    """
    generator = _load_generator()
    for bad in ("passthru", "inline_passthrough", "", None):
        rows = [dict(binding) for binding in BINDING_TABLE]
        rows[0]["mechanism"] = bad
        with pytest.raises(ValueError, match="declares mechanism"):
            generator.compile_rows(rows)


def test_compiler_rejects_profile_key_mismatch():
    generator = _load_generator()
    rows = [dict(binding) for binding in BINDING_TABLE]
    rows[0]["profile_key"] = "wrong_key"
    with pytest.raises(ValueError, match="unexpected profile_key"):
        generator.compile_rows(rows)


def test_the_loopback_parent_registers_nothing():
    """The fabric loopback has no registered bindings since the OSPF-auth retirement.

    Its three were the only ones, and they were withdrawn because OSPF authentication there is
    underlay authentication that fabricSettings owns. An empty set is the assertion, not an
    oversight: a binding reappearing on this parent should fail here.
    """
    assert registered_profile_keys(LOOPBACK) == set()


def test_registered_keys_per_parent():
    assert registered_profile_keys(TRUNK) == {
        "flowcontrol_receive", "flowcontrol_send", "spanning_tree_port_type",
        "guard_mode", "disable_lldp_transmit", "disable_lldp_receive", "acl_filter",
        "disable_qos_stats", "disable_queuing_stats",
    }
    assert registered_profile_keys(ACCESS) == {
        "flowcontrol_receive", "flowcontrol_send", "spanning_tree_port_type",
        "disable_lldp_transmit", "disable_lldp_receive", "acl_filter",
        "disable_qos_stats", "disable_queuing_stats"
    }
    assert registered_profile_keys(PC_TRUNK) == {
        "guard_mode", "acl_filter", "disable_lldp_transmit", "disable_lldp_receive",
        "spanning_tree_port_type", "disable_qos_stats", "disable_queuing_stats",
    }
    assert registered_profile_keys(PC_ACCESS) == {
        "acl_filter", "disable_lldp_transmit", "disable_lldp_receive",
        "spanning_tree_port_type", "disable_qos_stats", "disable_queuing_stats",
    }
    assert registered_profile_keys(PC_DOT1Q) == {
        "acl_filter", "disable_lldp_transmit", "disable_lldp_receive",
        "spanning_tree_port_type", "disable_qos_stats", "disable_queuing_stats",
    }
    # GUARD_MODE is NOT registered on access parents.
    assert "guard_mode" not in registered_profile_keys(ACCESS)
    assert "guard_mode" not in registered_profile_keys(PC_ACCESS)


def test_flowcontrol_binding_shape():
    b = resolve_binding(TRUNK, "flowcontrol_receive")
    assert b["parent_nvpair"] == "FLOWCONTROL_RECEIVE"
    assert b["mechanism"] == "passthrough"
    assert b["type"] == "enum" and b["valid_values"] == ("on", "off")
    assert b["min_ndfc_version"] == "12.6.0.267"


def test_flowcontrol_public_documentation_is_enum_without_default():
    documentation = yaml.safe_load(dcnm_interface.DOCUMENTATION)
    option = documentation["options"]["config"]["suboptions"]["profile_eth"][
        "suboptions"
    ]["flowcontrol_receive"]
    assert option["type"] == "str"
    assert option["choices"] == ["on", "off"]
    assert "default" not in option


def test_registry_drives_comparator_keymap_and_carry_forward():
    assert gie_nvpair_keymap()["FLOWCONTROL_RECEIVE"] == "flowcontrol_receive"
    assert gie_nvpair_keymap()["FLOWCONTROL_SEND"] == "flowcontrol_send"
    assert gie_nvpair_keymap()["SPANNING_TREE_PORT_TYPE"] == "spanning_tree_port_type"
    # FLOWCONTROL_SEND is passthrough, so it DOES join the carry-forward set -- the opposite
    # of the OSPF bindings, which are child_pti and are excluded. That difference is what
    # makes omitting the key preserve the controller's value instead of being a silent no-op.
    assert {
        (r["parent_nvpair"], r["profile_key"]) for r in gie_carry_forward_bindings(TRUNK)
    } == {
        ("FLOWCONTROL_RECEIVE", "flowcontrol_receive"),
        ("FLOWCONTROL_SEND", "flowcontrol_send"),
        ("SPANNING_TREE_PORT_TYPE", "spanning_tree_port_type"),
        ("GUARD_MODE", "guard_mode"),
        ("DISABLE_LLDP_TRANSMIT", "disable_lldp_transmit"),
        ("DISABLE_LLDP_RECEIVE", "disable_lldp_receive"),
        ("ACL_FILTER", "acl_filter"),
        ("DISABLE_QOS_STATS", "disable_qos_stats"),
        ("DISABLE_QUEUING_STATS", "disable_queuing_stats"),
    }
    assert {
        (r["parent_nvpair"], r["profile_key"]) for r in gie_carry_forward_bindings(ACCESS)
    } == {
        ("FLOWCONTROL_RECEIVE", "flowcontrol_receive"),
        ("FLOWCONTROL_SEND", "flowcontrol_send"),
        ("SPANNING_TREE_PORT_TYPE", "spanning_tree_port_type"),
        ("DISABLE_LLDP_TRANSMIT", "disable_lldp_transmit"),
        ("DISABLE_LLDP_RECEIVE", "disable_lldp_receive"),
        ("ACL_FILTER", "acl_filter"),
        ("DISABLE_QOS_STATS", "disable_qos_stats"),
        ("DISABLE_QUEUING_STATS", "disable_queuing_stats"),
    }
    assert gie_carry_forward_bindings(LOOPBACK) == []


def test_ambiguous_registry_nvpair_keymap_fails_closed(monkeypatch):
    conflicting = dict(BINDING_TABLE[0])
    conflicting["profile_key"] = "different_public_key"
    monkeypatch.setattr(
        gie_engine, "BINDING_TABLE", BINDING_TABLE + (conflicting,)
    )
    with pytest.raises(GieBindingError, match="ambiguous registered nvPair"):
        gie_nvpair_keymap()


@pytest.mark.parametrize("value", [True, "bogus", 1, None])
def test_binding_value_rejects_malformed_native_have(value):
    with pytest.raises(GieBindingError, match="authoritative controller value"):
        gie_validate_binding_value(
            TRUNK, "flowcontrol_receive", value, value_source="have"
        )


@pytest.mark.parametrize("value", ["on", "off"])
def test_binding_value_accepts_exact_native_enum(value):
    assert gie_validate_binding_value(TRUNK, "flowcontrol_receive", value) == value


# ---- FLOWCONTROL transport: intent survival + omission + native type ----

@pytest.mark.parametrize("val", ["on", "off"])
def test_flowcontrol_explicit_contributes_native_string(val):
    add, err = gie_contribute_nvpairs(TRUNK, {"mode": "trunk", "flowcontrol_receive": val}, "12.6.0.267")
    assert err is None
    assert add == {"FLOWCONTROL_RECEIVE": val}
    assert isinstance(add["FLOWCONTROL_RECEIVE"], str)


def test_flowcontrol_omitted_contributes_nothing():
    add, err = gie_contribute_nvpairs(ACCESS, {"mode": "access", "description": "x"}, "12.6.0.267")
    assert err is None and add == {}


def test_flowcontrol_present_on_both_parents():
    for p, m in [(TRUNK, "trunk"), (ACCESS, "access")]:
        add, err = gie_contribute_nvpairs(p, {"mode": m, "flowcontrol_receive": "on"}, "12.6.0.267")
        assert err is None and add == {"FLOWCONTROL_RECEIVE": "on"}


# ---- version fail-closed for a registered explicit key (FLOWCONTROL normal rule) ----

@pytest.mark.parametrize("ver", ["12.6.0.266", "12.5.9.999", None, "", "bogus", "12.x.0.1"])
def test_flowcontrol_below_or_bad_version_fails_closed(ver):
    add, err = gie_contribute_nvpairs(TRUNK, {"flowcontrol_receive": "on"}, ver)
    assert add is None and err is not None


@pytest.mark.parametrize("ver", ["12.6.0.267", "12.6.0.300", "12.7.0.1", "13.0.0.0"])
def test_flowcontrol_at_or_above_floor_ok(ver):
    add, err = gie_contribute_nvpairs(TRUNK, {"flowcontrol_receive": "off"}, ver)
    assert err is None and add == {"FLOWCONTROL_RECEIVE": "off"}


def test_version_supported_matches_semantics():
    assert gie_version_supported("12.6.0.267", "12.6.0.267") is True
    assert gie_version_supported("12.6.0.266", "12.6.0.267") is False
    assert gie_version_supported(None, "12.6.0.267") is False
    assert gie_version_supported("garbage", "12.6.0.267") is False


# ---- spec extension: explicit-only, no default ----

def test_extend_spec_adds_only_present_key_with_choices_no_default():
    spec = {"mode": {"type": "str"}}
    gie_extend_prof_spec(spec, TRUNK, {"mode": "trunk", "flowcontrol_receive": "on"})
    assert "flowcontrol_receive" in spec
    assert spec["flowcontrol_receive"]["choices"] == ["on", "off"]
    assert "default" not in spec["flowcontrol_receive"]


def test_extend_spec_skips_omitted_key():
    spec = {"mode": {"type": "str"}}
    gie_extend_prof_spec(spec, TRUNK, {"mode": "trunk"})
    assert "flowcontrol_receive" not in spec


# ---- B1: engine OWNS OSPF-MD binding resolution + supported-version transport (child_pti) ----

@pytest.mark.parametrize("val", [True, False])
@pytest.mark.parametrize("ver", ["12.6.0.266", None, "", "bogus"])
def test_ospfmd_withheld_not_failed_on_unsupported_version(val, ver):
    # child_pti: on an unsupported/unknown/malformed version the engine WITHHOLDS (no error),
    # so the module's capability gate + HAVE reconcile (compat hook) owns that path.
    add, err = gie_contribute_nvpairs(LOOPBACK, {"enable_ospf_auth_message_digest": val}, ver)
    assert err is None and add == {}


def test_ospfmd_not_in_generic_eth_spec_extension():
    # OSPF-MD (child_pti) is transported via contribute, but is NOT part of the GENERIC eth spec
    # extension (it keeps its dedicated native-boolean validate). No feature branch either way.
    spec = {}
    gie_extend_prof_spec(spec, LOOPBACK, {"enable_ospf_auth_message_digest": True})
    assert "enable_ospf_auth_message_digest" not in spec


def test_every_binding_uses_the_version_gate_with_no_exceptions():
    """Renamed from ...uses_passthrough_not_child_pti.

    It used to contrast FLOWCONTROL against the one child_pti binding, which had a withhold
    carve-out on an unsupported version. That binding is retired, so there is nothing left to
    contrast against -- and the assertion worth keeping is the stronger one: NO binding has a
    carve-out now, so an explicit value on an unsupported version fails closed, always.
    """
    assert resolve_binding(TRUNK, "flowcontrol_receive")["mechanism"] == "passthrough"
    assert all(b["mechanism"] == "passthrough" for b in BINDING_TABLE), (
        "a non-passthrough binding reappeared; the version-gate rule is no longer universal"
    )


def test_non_ospf_child_pti_does_not_inherit_ospf_withhold(monkeypatch):
    synthetic = {
        "parent_template": "synthetic_parent",
        "parent_nvpair": "ENABLE_SYNTHETIC_CHILD",
        "profile_key": "enable_synthetic_child",
        "applicable_interface_type": "svi",
        "applicable_mode": "vlan",
        "type": "boolean",
        "default_template": False,
        "mechanism": "child_pti",
        "min_ndfc_version": "12.6.0.267",
    }
    monkeypatch.setattr(
        gie_binding_table,
        "BINDING_TABLE",
        gie_binding_table.BINDING_TABLE + (synthetic,),
    )
    add, err = gie_contribute_nvpairs(
        "synthetic_parent", {"enable_synthetic_child": True}, "12.6.0.266"
    )
    assert add is None
    assert err is not None


# ---- B4: validator type comes from binding metadata; unknown fails closed ----

def test_validator_type_mapping_known():
    assert gie_validator_type("boolean") == "bool"
    assert gie_validator_type("enum") == "str"
    assert gie_validator_type("string") == "str"
    assert gie_validator_type("integer") == "int"


@pytest.mark.parametrize("bad", ["nonsense", "", None, "list", "dict"])
def test_validator_type_unknown_fails_closed(bad):
    with pytest.raises(GieBindingError):
        gie_validator_type(bad)


def test_extend_spec_flowcontrol_enum_maps_to_str():
    spec = {}
    gie_extend_prof_spec(spec, TRUNK, {"flowcontrol_receive": "on"})
    assert spec["flowcontrol_receive"]["type"] == "str"


def test_contribute_preserves_native_types_no_stringification():
    # enum -> native str; boolean -> native bool (not the "True"/"true" string)
    a1, err1 = gie_contribute_nvpairs(TRUNK, {"flowcontrol_receive": "on"}, "12.6.0.267")
    assert a1["FLOWCONTROL_RECEIVE"] == "on" and isinstance(a1["FLOWCONTROL_RECEIVE"], str)
    # The native-value case used to be the loopback child_pti binding, the only mechanism that
    # left a value unserialized. With child_pti retired every binding is passthrough, so the
    # wire form is now universal -- which is the property worth asserting.
    a2, err2 = gie_contribute_nvpairs(ROUTED, {"enable_ospf": True}, "12.6.0.267")
    assert a2["ENABLE_OSPF"] == "true" and isinstance(a2["ENABLE_OSPF"], str)


# ---- B2: registry-known key on an invalid desired parent -> fail closed (engine helper) ----

def test_all_registered_and_guarded_keys():
    assert gie_all_registered_keys() == {
        "flowcontrol_receive", "flowcontrol_send", "spanning_tree_port_type",
        "guard_mode", "disable_lldp_transmit", "disable_lldp_receive", "acl_filter",
        "disable_qos_stats", "disable_queuing_stats",
        "disable_bfd_echo", "ipv4_acl_in",
        "enable_ospf", "ospf_tag", "ospf_area_id", "ospf_cost",
        "ospf_mtu_ignore", "ospf_shutdown", "ospf_hello_interval", "ospf_dead_interval", "ospf_transmit_delay", "ospf_priority", "ospf_passive_mode", "ospf_network_type", "ospf_bfd_mode",
        "enable_ospf", "ospf_area_id", "ospf_bfd", "ospf_bfd_mode", "ospf_cost", "ospf_dead_interval", "ospf_hello_interval", "ospf_mtu_ignore", "ospf_network_type", "ospf_passive_interface", "ospf_passive_mode", "ospf_priority", "ospf_retransmit_interval", "ospf_shutdown", "ospf_tag", "ospf_transmit_delay",
        # The authentication lot, on all three OSPF parents. Passthrough like the rest, so
        # the generic guard owns it too: a key on the wrong parent is refused by the engine,
        # not by a validator written for this family.
        "enable_ospf_auth", "ospf_auth_key_id", "ospf_auth_key",
        "ospf_authentication_key_type", "ospf_authentication_key",
            # EIGRP, slice 0b_22. Thirteen fields, identical on int_routed_host, int_subif and
        # int_vlan -- measured against the bodies the controller runs, not the batch on disk.
        # EIGRP_PROCESS_TAG gates the other twelve, and the TEMPLATE refuses the tagless
        # case itself ("EIGRP process tag is required when EIGRP interface options are
        # enabled", int_routed_host:897). The engine transports and does not duplicate it.
        "eigrp_process_tag", "enable_eigrp_routing", "enable_eigrp_ipv6_routing",
        "eigrp_ipv4_passive", "eigrp_no_ipv4_passive", "eigrp_no_ipv6_passive",
        "enable_eigrp_shutdown", "enable_eigrp_bfd", "disable_eigrp_bfd",
        "eigrp_ipv4_distribute_list_prefix_list", "eigrp_ipv4_distribute_list_direction",
        "eigrp_ipv6_distribute_list_prefix_list", "eigrp_ipv6_distribute_list_direction",
        # int_loopback, slice 0b_23. Only ONE public key is new -- the other eighteen are names
        # this table already carries on other parents, which is the point of keying bindings by
        # (parent, nvpair) rather than by name.
        # HSRP on int_vlan, slice 0b_26. Three new public keys, and the only lot whose fields
        # sit on top of MODULE-NATIVE ones: enable_hsrp, hsrp_vip, hsrp_group, preempt and
        # hsrp_priority are already in the native SVI arg spec, so the engine adds only these.
        # The template enforces the whole dependency chain, including `lower cannot exceed
        # upper` -- a relationship between two fields that the registry cannot express.
        "hsrp_priority_forwarding_threshold_lower",
        "hsrp_priority_forwarding_threshold_upper",
        "hsrp_preempt_delay_minimum",
        "ospf_advertise_subnet",
        # BFD, slice 0b_24 and the eight rows of 0b_4/0b_5 committed with their mechanism
        # corrected from child_pti to passthrough. Four public keys; disable_bfd_echo was
        # already here, from int_routed_host.
        "enable_bfd_interval", "bfd_tx_interval", "bfd_min_rx_interval", "bfd_multiplier",
}
    # only passthrough keys are generically guarded; child_pti (OSPF-MD) keeps its own validate.
    # flowcontrol_send joins this set precisely BECAUSE it is passthrough -- the engine owns
    # its invalid-parent guard, unlike the OSPF bindings below.
    assert gie_guarded_keys() == {
        "flowcontrol_receive", "flowcontrol_send", "spanning_tree_port_type",
        "disable_bfd_echo", "ipv4_acl_in",
        "guard_mode", "disable_lldp_transmit", "disable_lldp_receive", "acl_filter",
        "disable_qos_stats", "disable_queuing_stats",
        # The routed OSPF slice is passthrough, so the generic guard owns it -- unlike the
        # fabric-loopback OSPF-MD trio asserted out of this set just below. Delegating to a
        # child template inside NDFC does not change which side of this line a binding sits on.
        "enable_ospf", "ospf_tag", "ospf_area_id", "ospf_cost",
        "ospf_mtu_ignore", "ospf_shutdown", "ospf_hello_interval", "ospf_dead_interval", "ospf_transmit_delay", "ospf_priority", "ospf_passive_mode", "ospf_network_type", "ospf_bfd_mode",
        "enable_ospf", "ospf_area_id", "ospf_bfd", "ospf_bfd_mode", "ospf_cost", "ospf_dead_interval", "ospf_hello_interval", "ospf_mtu_ignore", "ospf_network_type", "ospf_passive_interface", "ospf_passive_mode", "ospf_priority", "ospf_retransmit_interval", "ospf_shutdown", "ospf_tag", "ospf_transmit_delay",
        # The authentication lot, on all three OSPF parents. Passthrough like the rest, so
        # the generic guard owns it too: a key on the wrong parent is refused by the engine,
        # not by a validator written for this family.
        "enable_ospf_auth", "ospf_auth_key_id", "ospf_auth_key",
        "ospf_authentication_key_type", "ospf_authentication_key",
        # EIGRP, slice 0b_22. Passthrough like the OSPF rows, so the generic guard owns the
        # wrong-parent case for all thirteen. Nothing here enforces the EIGRP_PROCESS_TAG gate:
        # NDFC already rejects an EIGRP option with no effective tag, and a module-side rule
        # demanding the tag in every profile would break a valid partial update whose tag comes
        # from HAVE.
        "eigrp_process_tag", "enable_eigrp_routing", "enable_eigrp_ipv6_routing",
        "eigrp_ipv4_passive", "eigrp_no_ipv4_passive", "eigrp_no_ipv6_passive",
        "enable_eigrp_shutdown", "enable_eigrp_bfd", "disable_eigrp_bfd",
        "eigrp_ipv4_distribute_list_prefix_list", "eigrp_ipv4_distribute_list_direction",
        "eigrp_ipv6_distribute_list_prefix_list", "eigrp_ipv6_distribute_list_direction",
            # int_loopback, slice 0b_23. Only ONE public key is new -- the other eighteen are names
        # this table already carries on other parents, which is the point of keying bindings by
        # (parent, nvpair) rather than by name.
        # HSRP on int_vlan, slice 0b_26. Three new public keys, and the only lot whose fields
        # sit on top of MODULE-NATIVE ones: enable_hsrp, hsrp_vip, hsrp_group, preempt and
        # hsrp_priority are already in the native SVI arg spec, so the engine adds only these.
        # The template enforces the whole dependency chain, including `lower cannot exceed
        # upper` -- a relationship between two fields that the registry cannot express.
        "hsrp_priority_forwarding_threshold_lower",
        "hsrp_priority_forwarding_threshold_upper",
        "hsrp_preempt_delay_minimum",
        "ospf_advertise_subnet",
        # BFD, slice 0b_24 and the eight rows of 0b_4/0b_5 committed with their mechanism
        # corrected from child_pti to passthrough. Four public keys; disable_bfd_echo was
        # already here, from int_routed_host.
        "enable_bfd_interval", "bfd_tx_interval", "bfd_min_rx_interval", "bfd_multiplier",
}
    # The withdrawn fabric-loopback key. It is registered nowhere, so it is guarded nowhere --
    # the module rejects it by name instead, which is a different mechanism with a different
    # message.
    assert "enable_ospf_auth_message_digest" not in gie_guarded_keys()

    # INVERTED. These two used to assert the opposite, and the reason they did is gone.
    #
    # They were child_pti on int_fabric_loopback_11_1, and dcnm_intf_validate_ospf_auth_key_input
    # owned their invalid-parent check; letting the generic guard fire first would have silently
    # replaced that validator's message ("supported only on fabric loopback interfaces...").
    # Both the capability and the validator were withdrawn. Nothing owns the check now except
    # the generic guard -- so they MUST be in this set, or ospf_auth_key on a parent that does
    # not declare it would be accepted and quietly dropped.
    assert "ospf_auth_key_id" in gie_guarded_keys()
    assert "ospf_auth_key" in gie_guarded_keys()
    assert "ospf_authentication_key" in gie_guarded_keys()


def test_invalid_parent_key_flags_flowcontrol_on_wrong_parent():
    # routed/monitor/dot1q eth parents do not register flowcontrol_receive
    for parent in ("int_routed_host", "int_monitor_ethernet", "int_dot1q_tunnel_host", None):
        assert gie_invalid_parent_key(parent, ["mode", "flowcontrol_receive"]) == "flowcontrol_receive"


def test_invalid_parent_key_ok_on_valid_parents():
    assert gie_invalid_parent_key(TRUNK, ["mode", "flowcontrol_receive"]) is None
    assert gie_invalid_parent_key(ACCESS, ["mode", "flowcontrol_receive"]) is None


def test_invalid_parent_key_ignores_wholly_unknown_field():
    # a field not in the registry is left to the legacy discard path (not reported here)
    assert gie_invalid_parent_key("int_routed_host", ["mode", "some_legacy_field"]) is None


def _parent_guard_obj(profile):
    obj = object.__new__(dcnm_interface.DcnmIntf)
    obj.config = [{"name": "eth1/4", "type": "eth", "profile": profile}]
    obj.dcnm_version = 12
    obj.pol_types = {12: {
        "eth_trunk": TRUNK,
        "eth_access": ACCESS,
        "eth_routed": "int_routed_host",
    }}
    obj.module = mock.Mock()
    obj.module.fail_json.side_effect = RuntimeError("fail_json")
    return obj


def test_module_parent_guard_rejects_registered_key_before_legacy_filtering():
    obj = _parent_guard_obj({"mode": "routed", "flowcontrol_receive": "on"})
    with pytest.raises(RuntimeError, match="fail_json"):
        obj.dcnm_intf_gie_validate_parent_bindings()
    assert "flowcontrol_receive" in obj.module.fail_json.call_args.kwargs["msg"]
    assert "No template metadata was queried and no change was sent" in (
        obj.module.fail_json.call_args.kwargs["msg"]
    )


def test_module_parent_guard_accepts_both_registered_parents():
    for mode in ("trunk", "access"):
        obj = _parent_guard_obj({"mode": mode, "flowcontrol_receive": "on"})
        obj.dcnm_intf_gie_validate_parent_bindings()
        obj.module.fail_json.assert_not_called()


def test_module_parent_guard_preserves_unknown_legacy_discard_behavior():
    obj = _parent_guard_obj({"mode": "routed", "unknown_legacy_key": "x"})
    obj.dcnm_intf_gie_validate_parent_bindings()
    obj.module.fail_json.assert_not_called()


# ---- module path: intent survives profile -> validated field -> parent nvPair -> payload ----

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface  # noqa: E402


def _trunk_delem(val=None):
    prof = {"mode": "trunk", "bpdu_guard": "true", "port_type_fast": True, "mtu": "jumbo",
            "speed": "Auto", "allowed_vlans": "all", "native_vlan": "", "orphan_port": False,
            "cmds": None, "description": "test", "admin_state": True, "enable_cdp": True,
            "enable_pfc": False, "enable_monitor": False, "duplex": "auto", "enable_qos": False,
            "qos_policy": "", "queuing_policy": "", "fec": "auto"}
    if val is not None:
        prof["flowcontrol_receive"] = val
    return {"name": "eth1/4", "type": "eth", "switch": ["10.1.1.1"], "deploy": True, "profile": prof}


def _intf_trunk():
    return {"deploy": True, "policy": "int_trunk_host", "interfaceType": "INTERFACE_ETHERNET",
            "interfaces": [{"serialNumber": "", "interfaceType": "INTERFACE_ETHERNET", "ifName": "",
                            "fabricName": "test_fabric", "nvPairs": {"SPEED": "Auto"}}]}


def _intf_obj(ndfc_version):
    m = object.__new__(dcnm_interface.DcnmIntf)
    m.ndfc_version = ndfc_version
    return m


def test_module_path_flowcontrol_on_reaches_payload_nvpair():
    m, intf = _intf_obj("12.6.0.267"), _intf_trunk()
    m.dcnm_intf_get_eth_payload(_trunk_delem("on"), intf, "profile")
    assert intf["interfaces"][0]["nvPairs"]["FLOWCONTROL_RECEIVE"] == "on"


def test_module_path_flowcontrol_off_reaches_payload_nvpair():
    m, intf = _intf_obj("12.6.0.267"), _intf_trunk()
    m.dcnm_intf_get_eth_payload(_trunk_delem("off"), intf, "profile")
    assert intf["interfaces"][0]["nvPairs"]["FLOWCONTROL_RECEIVE"] == "off"


def test_module_path_flowcontrol_omitted_absent_from_payload():
    m, intf = _intf_obj("12.6.0.267"), _intf_trunk()
    m.dcnm_intf_get_eth_payload(_trunk_delem(None), intf, "profile")
    assert "FLOWCONTROL_RECEIVE" not in intf["interfaces"][0]["nvPairs"]


# ---- module compare/HAVE path: idempotency, preservation, parent transition ----

_OMITTED = object()


def _compare_payload(parent, flow=_OMITTED, description="same"):
    nvpairs = {"DESC": description}
    if flow is not _OMITTED:
        nvpairs["FLOWCONTROL_RECEIVE"] = flow
    return {
        "deploy": False,
        "policy": parent,
        "interfaceType": "INTERFACE_ETHERNET",
        "interfaces": [{
            "serialNumber": "SN1",
            "interfaceType": "INTERFACE_ETHERNET",
            "ifName": "Ethernet1/4",
            "fabricName": "FAB1",
            "nvPairs": nvpairs,
        }],
    }


def _compare_obj(state, parent, want_flow=_OMITTED, have_flow=_OMITTED,
                 want_description="same", have_description="same",
                 have_parent=None):
    module = mock.Mock()
    module.params = {"fabric": "FAB1", "config": [], "state": state}
    module.check_mode = False
    with mock.patch.object(
        dcnm_interface, "dcnm_version_supported",
        return_value=(12, "12.6.0.267"),
    ):
        obj = dcnm_interface.DcnmIntf(module)
    obj.want = [_compare_payload(parent, want_flow, want_description)]
    have = _compare_payload(
        have_parent or parent, have_flow, have_description
    )
    have.pop("deploy")
    obj.have = [have]
    pb = {
        "ifname": "Ethernet1/4",
        "sno": "SN1",
        "fabric": "FAB1",
        "policy": parent,
        "description": want_description,
    }
    if want_flow is not _OMITTED:
        pb["flowcontrol_receive"] = want_flow
    obj.pb_input = [pb]
    return obj


@pytest.mark.parametrize("parent", [TRUNK, ACCESS])
@pytest.mark.parametrize("value", ["on", "off"])
def test_flowcontrol_compare_idempotent_on_both_parents(parent, value):
    obj = _compare_obj("merged", parent, value, value)
    obj.dcnm_intf_compare_want_and_have("merged")
    assert obj.diff_replace == []
    assert obj.changed_dict[0]["merged"] == []


@pytest.mark.parametrize("parent", [TRUNK, ACCESS])
@pytest.mark.parametrize("state", ["merged", "replaced", "overridden"])
def test_flowcontrol_compare_drift_is_exact_native_delta(parent, state):
    obj = _compare_obj(state, parent, "off", "on")
    obj.dcnm_intf_compare_want_and_have(state)
    assert len(obj.diff_replace) == 1
    sent = obj.diff_replace[0]["interfaces"][0]["nvPairs"]
    assert sent["FLOWCONTROL_RECEIVE"] == "off"
    assert isinstance(sent["FLOWCONTROL_RECEIVE"], str)
    reported = obj.changed_dict[0][state][0]["interfaces"][0]["nvPairs"]
    assert reported == {"FLOWCONTROL_RECEIVE": "off"}


@pytest.mark.parametrize("parent", [TRUNK, ACCESS])
@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_omitted_flowcontrol_is_carried_from_have_on_unrelated_update(parent, state):
    obj = _compare_obj(
        state, parent, _OMITTED, "on",
        want_description="new", have_description="old",
    )
    obj.dcnm_intf_compare_want_and_have(state)
    sent = obj.diff_replace[0]["interfaces"][0]["nvPairs"]
    assert sent["FLOWCONTROL_RECEIVE"] == "on"
    reported = obj.changed_dict[0][state][0]["interfaces"][0]["nvPairs"]
    assert reported == {"DESC": "new"}


@pytest.mark.parametrize("parent", [TRUNK, ACCESS])
@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("malformed", [True, "bogus"])
def test_malformed_have_flowcontrol_fails_before_diff(
    parent, state, malformed
):
    obj = _compare_obj(
        state, parent, _OMITTED, malformed,
        want_description="new", have_description="old",
    )
    obj.module.fail_json.side_effect = RuntimeError("fail closed")
    with pytest.raises(RuntimeError, match="fail closed"):
        obj.dcnm_intf_compare_want_and_have(state)
    msg = obj.module.fail_json.call_args.kwargs["msg"]
    assert "authoritative controller value" in msg
    assert "no change was sent" in msg
    assert obj.diff_replace == []


def test_explicit_flowcontrol_survives_legacy_parent_transition():
    obj = _compare_obj(
        "replaced", TRUNK, "on", _OMITTED,
        have_parent="int_routed_host",
    )
    obj.dcnm_intf_compare_want_and_have("replaced")
    assert obj.diff_replace[0]["policy"] == TRUNK
    assert (
        obj.diff_replace[0]["interfaces"][0]["nvPairs"]["FLOWCONTROL_RECEIVE"]
        == "on"
    )


def test_missing_have_uses_existing_authority_gate_before_diff():
    obj = _compare_obj("merged", TRUNK, "on", _OMITTED)
    obj.have = []
    obj.dcnm_intf_require_detail_authority = mock.Mock(
        side_effect=RuntimeError("authoritative HAVE unavailable")
    )
    with pytest.raises(RuntimeError, match="authoritative HAVE unavailable"):
        obj.dcnm_intf_compare_want_and_have("merged")
    obj.dcnm_intf_require_detail_authority.assert_called_once_with(
        "Ethernet1/4", "SN1"
    )
    assert obj.diff_create == [] and obj.diff_replace == []


def test_check_mode_diff_keeps_native_flowcontrol_string():
    obj = _compare_obj("merged", TRUNK, "off", "on")
    obj.module.check_mode = True
    obj.dcnm_intf_compare_want_and_have("merged")
    value = obj.changed_dict[0]["merged"][0]["interfaces"][0]["nvPairs"][
        "FLOWCONTROL_RECEIVE"
    ]
    assert value == "off" and isinstance(value, str)


def test_query_keeps_controller_flowcontrol_string_without_normalization(monkeypatch):
    obj = _compare_obj("query", TRUNK)
    obj.intf_info = [{"name": "eth1/4", "switch": ["leaf-101"]}]
    obj.ip_sn = {"leaf-101": "SN1"}
    obj.dcnm_extract_if_name = lambda info: (
        "Ethernet1/4", "INTERFACE_ETHERNET"
    )
    raw = {"nvPairs": {"FLOWCONTROL_RECEIVE": "on"}}
    monkeypatch.setattr(
        dcnm_interface,
        "dcnm_send",
        lambda module, method, path: {"RETURN_CODE": 200, "DATA": [raw]},
    )
    obj.dcnm_intf_get_diff_query()
    assert obj.result["response"][0]["nvPairs"]["FLOWCONTROL_RECEIVE"] == "on"
    assert isinstance(
        obj.changed_dict[0]["query"][0]["nvPairs"]["FLOWCONTROL_RECEIVE"],
        str,
    )


# ---- exact registry contract for the OSPF legacy-key pair ----

def test_a19_pair_is_not_carried_forward():
    """child_pti bindings must stay out of the passthrough carry-forward set.

    Carry-forward preserves an authoritative HAVE value when the key is omitted. For this
    pair, omission is how the operator CLEARS the key, so carrying it forward would make
    removal impossible.
    """
    carried = {b["profile_key"] for b in gie_carry_forward_bindings(LOOPBACK)}
    assert carried.isdisjoint({"ospf_auth_key_id", "ospf_auth_key"})


# ---- native-type acceptance: str SUBCLASSES must pass (regression guard) ----
#
# Ansible never hands a module a plain `str`. A value that came from a playbook arrives as
# AnsibleUnicode, a str subclass. The engine originally checked `type(value) is native_type`,
# which is exact and rejects subclasses, so every string/enum binding was unusable end to end
# while these unit tests -- passing literal `str` -- kept passing.
#
# Every case below is therefore driven with a subclass, not a plain str. A locally defined
# subclass proves the semantics independently of the Ansible version; the AnsibleUnicode case
# proves the real one.


class _SubStr(str):
    """Stand-in for AnsibleUnicode: any str subclass must be accepted."""


def _ansible_unicode(value):
    try:
        from ansible.parsing.yaml.objects import AnsibleUnicode
    except ImportError:  # pragma: no cover - depends on the installed ansible-core
        return None
    return AnsibleUnicode(value)


@pytest.mark.parametrize("wrap", [_SubStr, _ansible_unicode], ids=["str_subclass", "AnsibleUnicode"])
def test_string_and_enum_bindings_accept_str_subclasses(wrap):
    # Deliberately not shaped like a real key. The assertion is an identity round-trip, so the
    # content is irrelevant -- but a 16-hex-character literal reads as a credential to a secret
    # scanner and invites someone to copy it into a playbook.
    key = wrap("example-ospf-key")
    if key is None:
        pytest.skip("AnsibleUnicode not importable in this ansible-core")
    # OSPF key string binding
    # Was the retired loopback ospf_auth_key. Any plain-string binding proves the same thing:
    # the check is that a str SUBCLASS is accepted, not which field carries it.
    assert gie_validate_binding_value(ROUTED, "ospf_tag", wrap("WP98")) == "WP98"
    # The enum and string bindings: the same defect made these unusable too.
    assert gie_validate_binding_value(TRUNK, "flowcontrol_receive", wrap("on")) == "on"
    assert gie_validate_binding_value(TRUNK, "acl_filter", wrap("MY_ACL")) == "MY_ACL"


def test_accepting_subclasses_does_not_make_bool_and_int_interchangeable():
    """isinstance(True, int) is True in Python, so a naive isinstance relaxation would let a
    boolean satisfy an integer binding and reach NDFC as 1 (or an int satisfy a boolean).
    """
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(ROUTED, "ospf_cost", True)
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(ROUTED, "enable_ospf", 1)
    # and the legitimate natives still pass
    assert gie_validate_binding_value(ROUTED, "ospf_cost", 17) == 17
    assert gie_validate_binding_value(ROUTED, "enable_ospf", True) is True


# ---- HAVE values: the input contract must not be applied to controller state ----
#
# These are the ACTUAL values NDFC returned for Leaf-101 Ethernet1/5 (int_trunk_host) and
# Ethernet1/4 (int_access_host) on a freshly deployed fabric, captured from
# GET /rest/interface. They are not invented: the whole point is that the registry's input
# contract does not describe what the controller stores.
#
# Applying the input contract to them made `state: overridden` abort on any explicitly
# declared host interface, which is every real deployment.

NDFC_TRUNK_HAVE = {
    "acl_filter": "",           # no ACL configured -- shorter than the registered min_length 1
    "disable_lldp_transmit": "false",    # NDFC encodes booleans as strings
    "flowcontrol_receive": "off",
    "guard_mode": "no",
}


@pytest.mark.parametrize("pk,value", sorted(NDFC_TRUNK_HAVE.items()))
def test_real_controller_values_are_carried_forward_not_rejected(pk, value):
    assert gie_validate_binding_value(TRUNK, pk, value, value_source="have") == value


def test_empty_acl_filter_from_have_is_accepted_on_both_host_parents():
    """The regression that broke `state: overridden`.

    ACL_FILTER == "" means "no ACL", which is the normal state of a host interface. It is
    only invalid as *user input*, and carrying it forward asserts "leave as-is".
    """
    for parent in (TRUNK, ACCESS):
        assert gie_validate_binding_value(parent, "acl_filter", "", value_source="have") == ""


def test_have_still_fails_closed_on_values_that_cannot_be_relayed():
    """Relaxing the input contract must not turn HAVE into an anything-goes path.

    nvPairs is a flat scalar map: a dict, a list or None signals a malformed controller
    response, not an unfamiliar encoding, and must not be relayed into a later payload.
    """
    for bad in (None, {"a": 1}, ["a"], object()):
        with pytest.raises(GieBindingError):
            gie_validate_binding_value(TRUNK, "acl_filter", bad, value_source="have")


def test_have_still_enforces_registered_choices():
    """The enum guard is deliberately KEPT on the HAVE path.

    NDFC was measured to return real enum members ('off', 'no'), so this check never fires
    on legitimate data -- and it is the one that catches genuine garbage before it is
    relayed into a later full-payload update. Only the checks that were measured to fire on
    legitimate controller state (length bounds, and the native type of booleans) were
    dropped.

    test_malformed_have_flowcontrol_fails_before_diff covers the same property end to end
    through the comparator; this pins it at the engine boundary.
    """
    for bad in ("bogus", True):
        with pytest.raises(GieBindingError):
            gie_validate_binding_value(
                TRUNK, "flowcontrol_receive", bad, value_source="have"
            )
    # ...while the members NDFC actually returns are accepted
    for good in ("on", "off"):
        assert gie_validate_binding_value(
            TRUNK, "flowcontrol_receive", good, value_source="have"
        ) == good


def test_the_input_contract_is_unchanged_for_explicit_values():
    """The boolean read-back relaxation is scoped to value_source='have'.

    This used to also assert that ``acl_filter: ""`` was rejected on explicit input. That
    claim is gone deliberately: the empty string is how a plain-string binding is CLEARED,
    and rejecting it made such a field settable and never clearable. NDFC accepts ``""``,
    stores it, and withdraws the CLI line on deploy -- measured, see
    test_gie_clear_string_binding.py. The check below keeps a length assertion in this case
    by using the UPPER bound, which has no "unset" reading and is unchanged.
    """
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(TRUNK, "acl_filter", "A" * 65)    # max_length 64
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(TRUNK, "flowcontrol_receive", "maybe")   # not a choice
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(TRUNK, "disable_lldp_transmit", "false")   # str where bool is required
    # an enum still fails closed on "": its "off" state is a named choice, never empty
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(TRUNK, "flowcontrol_receive", "")
    # and the legitimate inputs still pass
    assert gie_validate_binding_value(TRUNK, "acl_filter", "MY_ACL") == "MY_ACL"
    assert gie_validate_binding_value(TRUNK, "flowcontrol_receive", "on") == "on"
    assert gie_validate_binding_value(TRUNK, "disable_lldp_transmit", True) is True
    # the clear path: "" on a plain string is accepted and means "remove the value"
    assert gie_validate_binding_value(TRUNK, "acl_filter", "") == ""


def test_subclass_acceptance_does_not_bypass_the_other_registered_checks():
    """Relaxing the type check must not relax length or choices.

    The length probe used to be ``ospf_auth_key`` with an empty ``_SubStr``. The empty string
    now legitimately clears a plain-string binding, so it no longer proves anything about
    length. It is replaced by ``acl_filter`` over its UPPER bound, which still exercises the
    same thing the case was written for: that a str SUBCLASS -- the form every playbook value
    actually arrives in -- is still measured against the registered bounds.
    """
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(TRUNK, "acl_filter", _SubStr("A" * 65))  # max_length 64
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(TRUNK, "flowcontrol_receive", _SubStr("nope"))
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(LOOPBACK, "ospf_auth_key", 17)  # int is not a string


# ---- FLOWCONTROL_SEND: companion of the receive binding ----
#
# Driven with str SUBCLASSES, not literals. Every value that reaches a module from a playbook
# is wrapped in one (AnsibleUnicode or AnsibleUnsafeText were both observed in this codebase),
# and a test that passes a bare `str` cannot see a defect that only affects the wrapped form.
# That is exactly how these bindings stayed broken end to end while their unit tests were
# green.


@pytest.mark.parametrize("parent,mode", [(TRUNK, "trunk"), (ACCESS, "access")])
def test_flowcontrol_send_binding_shape(parent, mode):
    b = resolve_binding(parent, "flowcontrol_send")
    assert b is not None, "%s::flowcontrol_send missing" % parent
    assert b["parent_nvpair"] == "FLOWCONTROL_SEND"
    assert b["type"] == "enum"
    assert tuple(b["valid_values"]) == ("on", "off")
    assert b["default_template"] == "off"
    assert isinstance(b["default_template"], str), "YAML 1.1 'off' must stay a string"
    assert b["applicable_interface_type"] == "eth"
    assert b["applicable_mode"] == mode
    assert b["min_ndfc_version"] == "12.6.0.267"
    # passthrough, like receive: the DSL consumes the value inline and creates no child.
    assert b["mechanism"] == "passthrough"


@pytest.mark.parametrize("parent", [TRUNK, ACCESS])
@pytest.mark.parametrize("value", ["on", "off"])
def test_flowcontrol_send_transports_a_wrapped_playbook_value(parent, value):
    wrapped = _SubStr(value)
    add, err = gie_contribute_nvpairs(parent, {"flowcontrol_send": wrapped}, "12.6.0.267")
    assert err is None
    assert add == {"FLOWCONTROL_SEND": value}


@pytest.mark.parametrize("parent", [TRUNK, ACCESS])
def test_flowcontrol_send_is_explicit_only(parent):
    """Omission contributes nothing and adds no spec entry.

    Omission is NOT "set off": for a passthrough binding the carry-forward preserves the
    controller's current value instead. Registering default_template would have turned
    omission into an assertion of 'off'.
    """
    add, err = gie_contribute_nvpairs(parent, {}, "12.6.0.267")
    assert err is None and "FLOWCONTROL_SEND" not in add
    spec = {}
    gie_extend_prof_spec(spec, parent, {})
    assert "flowcontrol_send" not in spec
    gie_extend_prof_spec(spec, parent, {"flowcontrol_send": _SubStr("on")})
    assert spec["flowcontrol_send"] == {"type": "str", "choices": ["on", "off"]}


def test_flowcontrol_send_is_rejected_on_a_parent_that_does_not_register_it():
    """Being passthrough, the engine owns its invalid-parent guard."""
    assert gie_invalid_parent_key(LOOPBACK, ["flowcontrol_send"]) == "flowcontrol_send"
    assert gie_invalid_parent_key(PC_TRUNK, ["flowcontrol_send"]) == "flowcontrol_send"
    # ...and it is accepted on the two parents that do register it
    for parent in (TRUNK, ACCESS):
        assert gie_invalid_parent_key(parent, ["flowcontrol_send"]) is None


@pytest.mark.parametrize("parent", [TRUNK, ACCESS])
def test_flowcontrol_send_rejects_values_outside_the_enum(parent):
    for bad in (_SubStr("ON"), _SubStr("enabled"), _SubStr(""), True, 1):
        with pytest.raises(GieBindingError):
            gie_validate_binding_value(parent, "flowcontrol_send", bad)


def test_flowcontrol_send_public_documentation_matches_receive():
    documentation = yaml.safe_load(dcnm_interface.DOCUMENTATION)
    opts = documentation["options"]["config"]["suboptions"]["profile_eth"]["suboptions"]
    send, receive = opts["flowcontrol_send"], opts["flowcontrol_receive"]
    assert send["type"] == receive["type"] == "str"
    assert send["choices"] == receive["choices"] == ["on", "off"]
    assert "default" not in send, "explicit-only: a default would change omission semantics"


def test_flowcontrol_send_reaches_the_action_plugin_schema():
    """The action plugin keeps its OWN nvPairs mapping, unrelated to the registry.

    It is a plain dict in schemas.py, so a new profile key that is registered but not added
    there simply disappears from the pydantic model. Nothing else in the engine would catch
    that, which is why it is pinned here.
    """
    import importlib.util

    path = (
        Path(gie_binding_table.__file__).resolve().parents[2]
        / "plugins" / "action" / "tests" / "plugin_utils"
        / "pydantic_schemas" / "dcnm_interface" / "schemas.py"
    )
    source = path.read_text(encoding="utf-8")
    assert '"flowcontrol_send": "FLOWCONTROL_SEND"' in source
    assert '"flowcontrol_receive": "FLOWCONTROL_RECEIVE"' in source


# ---- SPANNING_TREE_PORT_TYPE: the first registered field that is not independent ----


@pytest.mark.parametrize("parent,mode", [(TRUNK, "trunk"), (ACCESS, "access")])
def test_spanning_tree_port_type_binding_shape(parent, mode):
    b = resolve_binding(parent, "spanning_tree_port_type")
    assert b is not None, "%s::spanning_tree_port_type missing" % parent
    assert b["parent_nvpair"] == "SPANNING_TREE_PORT_TYPE"
    assert b["type"] == "enum"
    assert tuple(b["valid_values"]) == ("no", "network", "normal")
    assert b["default_template"] == "no"
    assert b["mechanism"] == "passthrough"
    assert b["applicable_interface_type"] == "eth"
    assert b["applicable_mode"] == mode


@pytest.mark.parametrize("parent", [TRUNK, ACCESS])
def test_spanning_tree_no_stays_a_string_not_a_boolean(parent):
    """YAML 1.1 turns an unquoted `no` into False. Both the registered choice list and the
    default must survive as the string 'no', or the enum silently stops matching what the
    template declares.
    """
    b = resolve_binding(parent, "spanning_tree_port_type")
    assert "no" in b["valid_values"]
    assert False not in b["valid_values"]
    assert isinstance(b["default_template"], str)
    assert gie_validate_binding_value(parent, "spanning_tree_port_type", _SubStr("no")) == "no"
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(parent, "spanning_tree_port_type", False)


@pytest.mark.parametrize("parent", [TRUNK, ACCESS])
@pytest.mark.parametrize("value", ["no", "network", "normal"])
def test_spanning_tree_transports_a_wrapped_playbook_value(parent, value):
    add, err = gie_contribute_nvpairs(
        parent, {"spanning_tree_port_type": _SubStr(value)}, "12.6.0.267"
    )
    assert err is None
    assert add == {"SPANNING_TREE_PORT_TYPE": value}


@pytest.mark.parametrize("parent", [TRUNK, ACCESS])
def test_spanning_tree_rejects_values_outside_the_enum(parent):
    # 'edge' and 'edge trunk' are what the CLI ends up saying, but they are NOT registered
    # choices -- the template derives them from PORTTYPE_FAST_ENABLED, not from this field.
    for bad in (_SubStr("edge"), _SubStr("edge trunk"), _SubStr("NETWORK"), _SubStr(""), 1):
        with pytest.raises(GieBindingError):
            gie_validate_binding_value(parent, "spanning_tree_port_type", bad)


def test_spanning_tree_mutual_exclusion_is_not_expressed_in_the_registry():
    """Deliberate: the precondition lives in a field the registry does not own.

    The template rejects a non-"no" value while PORTTYPE_FAST_ENABLED is true
    (int_trunk_host:534, int_access_host:534), and true is the default on both sides. That
    relation is NOT registered, for two reasons:

      * it would need a new schema field for a single case -- the same `depends_on` that was
        already rejected as speculative during the OSPF migration;
      * PORTTYPE_FAST_ENABLED is handled by the module's legacy path and is absent from the
        registry, so a registry row cannot express a dependency on it.

    The engine therefore transports the value unconditionally and the template is left to
    reject it. This test pins that choice so nobody "fixes" it into the registry without
    first measuring how NDFC surfaces the rejection.
    """
    for parent in (TRUNK, ACCESS):
        b = resolve_binding(parent, "spanning_tree_port_type")
        assert "depends_on" not in b
        assert "conditional_requirement" not in b
        assert resolve_binding(parent, "port_type_fast") is None
        # transported without inspecting any other field
        add, err = gie_contribute_nvpairs(
            parent, {"spanning_tree_port_type": _SubStr("network")}, "12.6.0.267"
        )
        assert err is None and add == {"SPANNING_TREE_PORT_TYPE": "network"}


def test_spanning_tree_public_documentation_warns_about_port_type_fast():
    documentation = yaml.safe_load(dcnm_interface.DOCUMENTATION)
    opt = documentation["options"]["config"]["suboptions"]["profile_eth"]["suboptions"][
        "spanning_tree_port_type"
    ]
    assert opt["type"] == "str"
    assert opt["choices"] == ["no", "network", "normal"]
    assert "default" not in opt
    # The interaction is the single most surprising thing about this field: the default path
    # rejects it. It must be documented, or every first use fails.
    text = " ".join(opt["description"]).lower()
    assert "port_type_fast" in text


def test_spanning_tree_reaches_the_action_plugin_schema():
    path = (
        Path(gie_binding_table.__file__).resolve().parents[2]
        / "plugins" / "action" / "tests" / "plugin_utils"
        / "pydantic_schemas" / "dcnm_interface" / "schemas.py"
    )
    source = path.read_text(encoding="utf-8")
    assert '"spanning_tree_port_type": "SPANNING_TREE_PORT_TYPE"' in source


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
