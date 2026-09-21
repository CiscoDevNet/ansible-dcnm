"""Deterministic generator for the interface binding table.

Compiles the approved bindings from the registry YAML into a static Python artifact under
plugins/module_utils/. Runtime imports that artifact only; it never reads YAML or NDFC
template files.

Only the bindings listed in COMMITTED_BINDINGS are compiled. A registry row outside that set
is skipped -- except when it reuses a committed public profile_key on a different parent,
which is rejected: the same public name exists under other mechanisms (for example
int_vpc_trunk_host::GUARD_MODE is child_pti), and skipping it silently would make a
non-passthrough binding look merely unselected.

The curated `profile_key` in the registry is authoritative. It is never derived by
lower-casing an nvPair name; a row whose profile_key does not match the committed value is
rejected rather than rewritten.

Usage: python3 gie_generate_binding_table.py <registry_yaml> [<more_yaml> ...] <output_py>
Deterministic: same input -> byte-identical output (sorted keys, fixed formatting, provenance
sha256 over the compiled rows).
"""
import hashlib
import json
import sys

import yaml

COMMITTED_BINDINGS = {
    # WITHDRAWN: the three fabric-loopback OSPF-auth bindings.
    #
    # OSPF authentication on a fabric loopback is UNDERLAY authentication and the fabric owns
    # it. The template gates the whole block on `linkStateRouting == "ospf"` and reads
    # OSPF_AUTH_ENABLE, OSPF_AUTH_KEY_ID and OSPF_AUTH_KEY from fabricSettings, treating any
    # interface value as a mere override -- which a keychain fabric setting then deletes.
    # Configuring it per loopback is not part of the product.
    #
    # They were the only child_pti bindings in this table, and the two global validators that
    # served them (dcnm_intf_validate_ospf_auth_key_input and ..._message_digest_input) rejected
    # ospf_auth_key on ANY interface whose type was not "lo" -- which blocked registering
    # legitimate OSPF auth on int_routed_host, int_subif and int_vlan, where it is a
    # self-contained interface feature with no fabric involvement.
    #
    # Withdrawing them is not the same as deleting configuration: see
    # test_gie_loopback_auth_is_fabric_owned.py, which pins that an unrelated loopback update
    # still preserves everything the fabric manages.

    # Host ethernet and port-channel parents, passthrough.
    ("int_access_host", "FLOWCONTROL_RECEIVE"): "flowcontrol_receive",
    ("int_trunk_host", "FLOWCONTROL_RECEIVE"): "flowcontrol_receive",
    ("int_access_host", "FLOWCONTROL_SEND"): "flowcontrol_send",
    ("int_trunk_host", "FLOWCONTROL_SEND"): "flowcontrol_send",

    ("int_trunk_host", "GUARD_MODE"): "guard_mode",
    ("int_port_channel_trunk_host", "GUARD_MODE"): "guard_mode",


    ("int_access_host", "ACL_FILTER"): "acl_filter",
    ("int_trunk_host", "ACL_FILTER"): "acl_filter",
    ("int_port_channel_access_host", "ACL_FILTER"): "acl_filter",
    ("int_port_channel_trunk_host", "ACL_FILTER"): "acl_filter",
    ("int_port_channel_dot1q_tunnel_host", "ACL_FILTER"): "acl_filter",

    ("int_access_host", "SPANNING_TREE_PORT_TYPE"): "spanning_tree_port_type",
    ("int_trunk_host", "SPANNING_TREE_PORT_TYPE"): "spanning_tree_port_type",

    ("int_access_host", "DISABLE_QOS_STATS"): "disable_qos_stats",
    ("int_trunk_host", "DISABLE_QOS_STATS"): "disable_qos_stats",
    ("int_access_host", "DISABLE_QUEUING_STATS"): "disable_queuing_stats",
    ("int_trunk_host", "DISABLE_QUEUING_STATS"): "disable_queuing_stats",

    # The same four fields on the port-channel host parents. DISABLE_LLDP differs from the
    # other three: the parent delegates it to the member policy instead of emitting the CLI
    # itself, so whether it takes effect is measured rather than assumed. See the slice. Each was originally registered
    # only on the parents under test at the time; sweeping all 98 templates showed the
    # port-channel parents declare them too. An unregistered binding does not fail -- the
    # module answers "not supported on this interface", which is false: the template declares
    # it, the registry did not.
    ("int_port_channel_access_host", "SPANNING_TREE_PORT_TYPE"): "spanning_tree_port_type",
    ("int_port_channel_trunk_host", "SPANNING_TREE_PORT_TYPE"): "spanning_tree_port_type",
    ("int_port_channel_dot1q_tunnel_host", "SPANNING_TREE_PORT_TYPE"): "spanning_tree_port_type",


    ("int_port_channel_access_host", "DISABLE_QOS_STATS"): "disable_qos_stats",
    ("int_port_channel_trunk_host", "DISABLE_QOS_STATS"): "disable_qos_stats",
    ("int_port_channel_dot1q_tunnel_host", "DISABLE_QOS_STATS"): "disable_qos_stats",

    ("int_port_channel_access_host", "DISABLE_QUEUING_STATS"): "disable_queuing_stats",
    ("int_port_channel_trunk_host", "DISABLE_QUEUING_STATS"): "disable_queuing_stats",
    ("int_port_channel_dot1q_tunnel_host", "DISABLE_QUEUING_STATS"): "disable_queuing_stats",

    # The two vPC host parents, passthrough. These are the only vPC parents a playbook can
    # reach: the module builds its policy key as <type>_<mode> and pol_types carries just
    # "vpc_trunk" and "vpc_access". The intermediate _po_11_1 and the _po_member_11_1 levels
    # are created by the host template itself and are not registered.
    #
    # The docstring above names int_vpc_trunk_host::GUARD_MODE as child_pti. That referred to
    # the TEMPLATE delegating the value to a child, which it does -- but `mechanism` here means
    # who owns validation, the invalid-parent guard, the generic prof_spec, carry-forward and
    # wire-form conversion. vPC has no dedicated machinery for any of those, and
    # int_port_channel_trunk_host::DISABLE_LLDP already sets the precedent: it delegates to a
    # member template and is registered passthrough. Delegation does not decide the mechanism.
    #
    # Measured, not inferred: writing GUARD_MODE=root into the vpc55 parent's nvPairs produced
    # `spanning-tree guard root` on both peers. See registry_slice_0b_15.yaml.
    ("int_vpc_trunk_host", "SPANNING_TREE_PORT_TYPE"): "spanning_tree_port_type",
    ("int_vpc_access_host", "SPANNING_TREE_PORT_TYPE"): "spanning_tree_port_type",


    ("int_vpc_trunk_host", "ACL_FILTER"): "acl_filter",
    ("int_vpc_access_host", "ACL_FILTER"): "acl_filter",

    # trunk only: int_vpc_access_host does not declare GUARD_MODE.
    ("int_vpc_trunk_host", "GUARD_MODE"): "guard_mode",

    ("int_vpc_trunk_host", "DISABLE_QOS_STATS"): "disable_qos_stats",
    ("int_vpc_access_host", "DISABLE_QOS_STATS"): "disable_qos_stats",

    ("int_vpc_trunk_host", "DISABLE_QUEUING_STATS"): "disable_queuing_stats",
    ("int_vpc_access_host", "DISABLE_QUEUING_STATS"): "disable_queuing_stats",

    # int_routed_host -- the first non-switchport parent after the fabric loopback.
    #
    # Four of these six delegate to a child template (interface_lldp_disable,
    # bfd_no_echo_interface, interface_ip_arp_timeout_11_1,
    # interface_ip_access_group_in_11_1), all verified present on 12.6.0.267. Per the
    # precedent recorded above for int_port_channel_trunk_host::DISABLE_LLDP, delegation does
    # not decide the mechanism: the module writes one parent nvPair, so these stay passthrough.
    ("int_routed_host", "DISABLE_BFD_ECHO"): "disable_bfd_echo",

    # IsShow="ENABLE_QOS==true" / QUEUING_POLICY!='' -- these only append `no-stats` to the
    # service-policy line the QoS scaffold emits. Unlike the dot1q port-channel, the scaffold
    # is native to eth_prof_spec_routed_host, so they are reachable from the data model.
    ("int_routed_host", "DISABLE_QOS_STATS"): "disable_qos_stats",
    ("int_routed_host", "DISABLE_QUEUING_STATS"): "disable_queuing_stats",

    # ARP_TIMEOUT is deliberately NOT committed yet. int_subif and int_vlan declare it too and
    # both are reachable (pol_types "sub_int_subint" and "svi_vlan"), so committing it on the
    # routed parent alone would make the module answer "not supported on this interface" for
    # the other two -- which is false, and is exactly the failure this table exists to prevent.
    # It goes in as one lot across the three parents, with its own prof_spec work and its own
    # live run. The generator enforces this: it rejects a row that claims a committed public
    # profile_key from an uncommitted parent rather than skipping it silently.
    ("int_routed_host", "IPV4_ACL_IN"): "ipv4_acl_in",
    # DISABLE_LLDP was retired: the 2026-09-14 release removes it from all eight parents
    # and splits it into two independent fields. This is not a rename: the old field disabled
    # both directions together; these can disable either direction. See registry_slice_0b_17.
    #
    # Keeping the old binding would be worse than removing it: a PTI accepts nvPairs its
    # template does not declare. DISABLE_LLDP would still travel through the API and appear
    # valid, but would never produce CLI.
    ("int_access_host", "DISABLE_LLDP_TRANSMIT"): "disable_lldp_transmit",
    ("int_trunk_host", "DISABLE_LLDP_TRANSMIT"): "disable_lldp_transmit",
    ("int_routed_host", "DISABLE_LLDP_TRANSMIT"): "disable_lldp_transmit",
    ("int_port_channel_access_host", "DISABLE_LLDP_TRANSMIT"): "disable_lldp_transmit",
    ("int_port_channel_trunk_host", "DISABLE_LLDP_TRANSMIT"): "disable_lldp_transmit",
    ("int_port_channel_dot1q_tunnel_host", "DISABLE_LLDP_TRANSMIT"): "disable_lldp_transmit",
    ("int_vpc_access_host", "DISABLE_LLDP_TRANSMIT"): "disable_lldp_transmit",
    ("int_vpc_trunk_host", "DISABLE_LLDP_TRANSMIT"): "disable_lldp_transmit",

    ("int_access_host", "DISABLE_LLDP_RECEIVE"): "disable_lldp_receive",
    ("int_trunk_host", "DISABLE_LLDP_RECEIVE"): "disable_lldp_receive",
    ("int_routed_host", "DISABLE_LLDP_RECEIVE"): "disable_lldp_receive",
    ("int_port_channel_access_host", "DISABLE_LLDP_RECEIVE"): "disable_lldp_receive",
    ("int_port_channel_trunk_host", "DISABLE_LLDP_RECEIVE"): "disable_lldp_receive",
    ("int_port_channel_dot1q_tunnel_host", "DISABLE_LLDP_RECEIVE"): "disable_lldp_receive",
    ("int_vpc_access_host", "DISABLE_LLDP_RECEIVE"): "disable_lldp_receive",
    ("int_vpc_trunk_host", "DISABLE_LLDP_RECEIVE"): "disable_lldp_receive",

    # OSPF on the routed host parent, child_pti. FOUR ONLY, on purpose: this is the first
    # time child_pti is exercised on a routed parent rather than the fabric loopback, and
    # every OSPF field is gated IsShow="ENABLE_OSPF==true" so none can be tested alone.
    # The gate plus the two the template marks IsMandatory feed one shared base child;
    # OSPF_COST is the value field under test, with unambiguous CLI and no secret.
    # The remaining OSPF fields stay out until this slice is measured on hardware.
    ("int_routed_host", "ENABLE_OSPF"): "enable_ospf",
    ("int_routed_host", "OSPF_TAG"): "ospf_tag",
    ("int_routed_host", "ENABLE_OSPF_AUTH"): "enable_ospf_auth",
    ("int_routed_host", "OSPF_AUTH_KEY_ID"): "ospf_auth_key_id",
    ("int_routed_host", "OSPF_AUTH_KEY"): "ospf_auth_key",
    ("int_routed_host", "OSPF_AUTHENTICATION_KEY_TYPE"): "ospf_authentication_key_type",
    ("int_routed_host", "OSPF_AUTHENTICATION_KEY"): "ospf_authentication_key",
    ("int_routed_host", "OSPF_AREA_ID"): "ospf_area_id",
    ("int_routed_host", "OSPF_COST"): "ospf_cost",

    # Lot 2: the nine non-authentication OSPF fields on the same parent. All gated by
    # ENABLE_OSPF, all IsMandatory=false, each with its own child template -- so they are
    # independent value fields behind one gate, not a composite.
    #
    # The three enums default to "no_change", NDFC's sentinel for "leave the device alone".
    # That is the controller's semantics; the engine validates enum membership and transports
    # the string, exactly as it already does for GUARD_MODE ("no") and SPANNING_TREE_PORT_TYPE.
    #
    # The five authentication fields are deliberately NOT here: they carry or gate secrets, and
    # three already exist as child_pti on int_fabric_loopback_11_1. Registering the same nvPair
    # on a second parent is a per-(parent, nvpair) mechanism decision, not a copy.
    ("int_routed_host", "OSPF_MTU_IGNORE"): "ospf_mtu_ignore",
    ("int_routed_host", "OSPF_SHUTDOWN"): "ospf_shutdown",
    ("int_routed_host", "OSPF_HELLO_INTERVAL"): "ospf_hello_interval",
    ("int_routed_host", "OSPF_DEAD_INTERVAL"): "ospf_dead_interval",
    ("int_routed_host", "OSPF_TRANSMIT_DELAY"): "ospf_transmit_delay",
    ("int_routed_host", "OSPF_PRIORITY"): "ospf_priority",
    ("int_routed_host", "OSPF_PASSIVE_MODE"): "ospf_passive_mode",
    ("int_routed_host", "OSPF_NETWORK_TYPE"): "ospf_network_type",
    ("int_routed_host", "OSPF_BFD_MODE"): "ospf_bfd_mode",

    # int_subif and int_vlan -- the first bindings ever registered for these two parents. Both
    # needed the engine hooked into their validator and builder first; neither had it.
    #
    # Extracted per parent, never copied: the three OSPF parents model the same concepts with
    # different nvPairs and even different TYPES.
    #
    #     concept      int_routed_host       int_subif                 int_vlan
    #     passive      OSPF_PASSIVE_MODE     OSPF_PASSIVE_INTERFACE    OSPF_PASSIVE_MODE
    #                  enum                  boolean                   enum
    #     bfd          OSPF_BFD_MODE         OSPF_BFD                  OSPF_BFD_MODE
    #                  enum                  boolean                   enum
    #     retransmit   absent                OSPF_RETRANSMIT_INTERVAL  OSPF_RETRANSMIT_INTERVAL
    #
    # This is why the table is keyed by (parent_template, parent_nvpair). A slice copied from
    # the routed parent would have registered nvPairs that do not exist on the other two.
    ("int_subif", "ENABLE_OSPF"): "enable_ospf",
    ("int_subif", "OSPF_AREA_ID"): "ospf_area_id",
    ("int_subif", "OSPF_BFD"): "ospf_bfd",
    ("int_subif", "OSPF_COST"): "ospf_cost",
    ("int_subif", "OSPF_DEAD_INTERVAL"): "ospf_dead_interval",
    ("int_subif", "OSPF_HELLO_INTERVAL"): "ospf_hello_interval",
    ("int_subif", "OSPF_MTU_IGNORE"): "ospf_mtu_ignore",
    ("int_subif", "OSPF_NETWORK_TYPE"): "ospf_network_type",
    ("int_subif", "OSPF_PASSIVE_INTERFACE"): "ospf_passive_interface",
    ("int_subif", "OSPF_PRIORITY"): "ospf_priority",
    ("int_subif", "OSPF_RETRANSMIT_INTERVAL"): "ospf_retransmit_interval",
    ("int_subif", "OSPF_SHUTDOWN"): "ospf_shutdown",
    ("int_subif", "OSPF_TAG"): "ospf_tag",
    ("int_subif", "ENABLE_OSPF_AUTH"): "enable_ospf_auth",
    ("int_subif", "OSPF_AUTH_KEY_ID"): "ospf_auth_key_id",
    ("int_subif", "OSPF_AUTH_KEY"): "ospf_auth_key",
    ("int_subif", "OSPF_AUTHENTICATION_KEY_TYPE"): "ospf_authentication_key_type",
    ("int_subif", "OSPF_AUTHENTICATION_KEY"): "ospf_authentication_key",
    ("int_subif", "OSPF_TRANSMIT_DELAY"): "ospf_transmit_delay",
    ("int_vlan", "ENABLE_OSPF"): "enable_ospf",
    ("int_vlan", "OSPF_AREA_ID"): "ospf_area_id",
    ("int_vlan", "OSPF_BFD_MODE"): "ospf_bfd_mode",
    ("int_vlan", "OSPF_COST"): "ospf_cost",
    ("int_vlan", "OSPF_DEAD_INTERVAL"): "ospf_dead_interval",
    ("int_vlan", "OSPF_HELLO_INTERVAL"): "ospf_hello_interval",
    ("int_vlan", "OSPF_MTU_IGNORE"): "ospf_mtu_ignore",
    ("int_vlan", "OSPF_NETWORK_TYPE"): "ospf_network_type",
    ("int_vlan", "OSPF_PASSIVE_MODE"): "ospf_passive_mode",
    ("int_vlan", "OSPF_PRIORITY"): "ospf_priority",
    ("int_vlan", "OSPF_RETRANSMIT_INTERVAL"): "ospf_retransmit_interval",
    ("int_vlan", "OSPF_SHUTDOWN"): "ospf_shutdown",
    ("int_vlan", "OSPF_TAG"): "ospf_tag",
    ("int_vlan", "ENABLE_OSPF_AUTH"): "enable_ospf_auth",
    ("int_vlan", "OSPF_AUTH_KEY_ID"): "ospf_auth_key_id",
    ("int_vlan", "OSPF_AUTH_KEY"): "ospf_auth_key",
    ("int_vlan", "OSPF_AUTHENTICATION_KEY_TYPE"): "ospf_authentication_key_type",
    ("int_vlan", "OSPF_AUTHENTICATION_KEY"): "ospf_authentication_key",
    ("int_vlan", "OSPF_TRANSMIT_DELAY"): "ospf_transmit_delay",

    # --- EIGRP on int_routed_host (slice 0b_22) ---
    ("int_routed_host", "EIGRP_PROCESS_TAG"): "eigrp_process_tag",
    ("int_routed_host", "ENABLE_EIGRP_ROUTING"): "enable_eigrp_routing",
    ("int_routed_host", "ENABLE_EIGRP_IPV6_ROUTING"): "enable_eigrp_ipv6_routing",
    ("int_routed_host", "EIGRP_IPV4_PASSIVE"): "eigrp_ipv4_passive",
    ("int_routed_host", "EIGRP_NO_IPV4_PASSIVE"): "eigrp_no_ipv4_passive",
    ("int_routed_host", "EIGRP_NO_IPV6_PASSIVE"): "eigrp_no_ipv6_passive",
    ("int_routed_host", "ENABLE_EIGRP_SHUTDOWN"): "enable_eigrp_shutdown",
    ("int_routed_host", "ENABLE_EIGRP_BFD"): "enable_eigrp_bfd",
    ("int_routed_host", "DISABLE_EIGRP_BFD"): "disable_eigrp_bfd",
    ("int_routed_host", "EIGRP_IPV4_DISTRIBUTE_LIST_PREFIX_LIST"): "eigrp_ipv4_distribute_list_prefix_list",
    ("int_routed_host", "EIGRP_IPV4_DISTRIBUTE_LIST_DIRECTION"): "eigrp_ipv4_distribute_list_direction",
    ("int_routed_host", "EIGRP_IPV6_DISTRIBUTE_LIST_PREFIX_LIST"): "eigrp_ipv6_distribute_list_prefix_list",
    ("int_routed_host", "EIGRP_IPV6_DISTRIBUTE_LIST_DIRECTION"): "eigrp_ipv6_distribute_list_direction",
    # --- EIGRP on int_subif (slice 0b_22) ---
    ("int_subif", "EIGRP_PROCESS_TAG"): "eigrp_process_tag",
    ("int_subif", "ENABLE_EIGRP_ROUTING"): "enable_eigrp_routing",
    ("int_subif", "ENABLE_EIGRP_IPV6_ROUTING"): "enable_eigrp_ipv6_routing",
    ("int_subif", "EIGRP_IPV4_PASSIVE"): "eigrp_ipv4_passive",
    ("int_subif", "EIGRP_NO_IPV4_PASSIVE"): "eigrp_no_ipv4_passive",
    ("int_subif", "EIGRP_NO_IPV6_PASSIVE"): "eigrp_no_ipv6_passive",
    ("int_subif", "ENABLE_EIGRP_SHUTDOWN"): "enable_eigrp_shutdown",
    ("int_subif", "ENABLE_EIGRP_BFD"): "enable_eigrp_bfd",
    ("int_subif", "DISABLE_EIGRP_BFD"): "disable_eigrp_bfd",
    ("int_subif", "EIGRP_IPV4_DISTRIBUTE_LIST_PREFIX_LIST"): "eigrp_ipv4_distribute_list_prefix_list",
    ("int_subif", "EIGRP_IPV4_DISTRIBUTE_LIST_DIRECTION"): "eigrp_ipv4_distribute_list_direction",
    ("int_subif", "EIGRP_IPV6_DISTRIBUTE_LIST_PREFIX_LIST"): "eigrp_ipv6_distribute_list_prefix_list",
    ("int_subif", "EIGRP_IPV6_DISTRIBUTE_LIST_DIRECTION"): "eigrp_ipv6_distribute_list_direction",
    # --- EIGRP on int_vlan (slice 0b_22) ---
    ("int_vlan", "EIGRP_PROCESS_TAG"): "eigrp_process_tag",
    ("int_vlan", "ENABLE_EIGRP_ROUTING"): "enable_eigrp_routing",
    ("int_vlan", "ENABLE_EIGRP_IPV6_ROUTING"): "enable_eigrp_ipv6_routing",
    ("int_vlan", "EIGRP_IPV4_PASSIVE"): "eigrp_ipv4_passive",
    ("int_vlan", "EIGRP_NO_IPV4_PASSIVE"): "eigrp_no_ipv4_passive",
    ("int_vlan", "EIGRP_NO_IPV6_PASSIVE"): "eigrp_no_ipv6_passive",
    ("int_vlan", "ENABLE_EIGRP_SHUTDOWN"): "enable_eigrp_shutdown",
    ("int_vlan", "ENABLE_EIGRP_BFD"): "enable_eigrp_bfd",
    ("int_vlan", "DISABLE_EIGRP_BFD"): "disable_eigrp_bfd",
    ("int_vlan", "EIGRP_IPV4_DISTRIBUTE_LIST_PREFIX_LIST"): "eigrp_ipv4_distribute_list_prefix_list",
    ("int_vlan", "EIGRP_IPV4_DISTRIBUTE_LIST_DIRECTION"): "eigrp_ipv4_distribute_list_direction",
    ("int_vlan", "EIGRP_IPV6_DISTRIBUTE_LIST_PREFIX_LIST"): "eigrp_ipv6_distribute_list_prefix_list",
    ("int_vlan", "EIGRP_IPV6_DISTRIBUTE_LIST_DIRECTION"): "eigrp_ipv6_distribute_list_direction",
    # --- OSPF on int_loopback (slice 0b_23) ---
    ("int_loopback", "ENABLE_OSPF"): "enable_ospf",
    ("int_loopback", "OSPF_TAG"): "ospf_tag",
    ("int_loopback", "OSPF_AREA_ID"): "ospf_area_id",
    ("int_loopback", "OSPF_ADVERTISE_SUBNET"): "ospf_advertise_subnet",
    ("int_loopback", "OSPF_COST"): "ospf_cost",
    ("int_loopback", "OSPF_HELLO_INTERVAL"): "ospf_hello_interval",
    ("int_loopback", "OSPF_DEAD_INTERVAL"): "ospf_dead_interval",
    ("int_loopback", "OSPF_RETRANSMIT_INTERVAL"): "ospf_retransmit_interval",
    ("int_loopback", "OSPF_TRANSMIT_DELAY"): "ospf_transmit_delay",
    ("int_loopback", "OSPF_PRIORITY"): "ospf_priority",
    ("int_loopback", "OSPF_MTU_IGNORE"): "ospf_mtu_ignore",
    ("int_loopback", "OSPF_SHUTDOWN"): "ospf_shutdown",
    ("int_loopback", "OSPF_NETWORK_TYPE"): "ospf_network_type",
    ("int_loopback", "OSPF_BFD"): "ospf_bfd",
    ("int_loopback", "ENABLE_OSPF_AUTH"): "enable_ospf_auth",
    ("int_loopback", "OSPF_AUTH_KEY_ID"): "ospf_auth_key_id",
    ("int_loopback", "OSPF_AUTH_KEY"): "ospf_auth_key",
    ("int_loopback", "OSPF_AUTHENTICATION_KEY_TYPE"): "ospf_authentication_key_type",
    ("int_loopback", "OSPF_AUTHENTICATION_KEY"): "ospf_authentication_key",
    # --- BFD on int_subif and int_vlan (slice 0b_24) ---
    ("int_subif", "ENABLE_BFD_INTERVAL"): "enable_bfd_interval",
    ("int_subif", "BFD_TX_INTERVAL"): "bfd_tx_interval",
    ("int_subif", "BFD_MIN_RX_INTERVAL"): "bfd_min_rx_interval",
    ("int_subif", "BFD_MULTIPLIER"): "bfd_multiplier",
    ("int_vlan", "ENABLE_BFD_INTERVAL"): "enable_bfd_interval",
    ("int_vlan", "BFD_TX_INTERVAL"): "bfd_tx_interval",
    ("int_vlan", "BFD_MIN_RX_INTERVAL"): "bfd_min_rx_interval",
    ("int_vlan", "BFD_MULTIPLIER"): "bfd_multiplier",
    ("int_vlan", "DISABLE_BFD_ECHO"): "disable_bfd_echo",
    # --- EIGRP on int_loopback (slice 0b_25) ---
    #
    # EIGHT, not the family's thirteen. The INSTALLED parent -- int_loopback.template@27cd9ce7e671b5f3,
    # measured against the controller -- does not declare ENABLE_EIGRP_IPV6_ROUTING nor any of the
    # four distribute-list fields. Registering a field the parent does not declare is the
    # silent-drop failure this table exists to prevent: NDFC discards the unknown nvPair, the
    # module reports success, and the device gets nothing. Slice 0b_22's uniformity across the
    # three overlay parents is not evidence about this one.
    #
    # Every one of the seven CLI commands these eight produce was measured as ACCEPTED on FAB4
    # (nxos64-cs.10.6.2.F.bin) through NDFC before this entry was added, including the two that
    # needed `feature bfd` and the two `no ...` forms. See the phase34 FAB4 EIGRP evidence.
    ("int_loopback", "EIGRP_PROCESS_TAG"): "eigrp_process_tag",
    ("int_loopback", "ENABLE_EIGRP_ROUTING"): "enable_eigrp_routing",
    ("int_loopback", "EIGRP_IPV4_PASSIVE"): "eigrp_ipv4_passive",
    ("int_loopback", "EIGRP_NO_IPV4_PASSIVE"): "eigrp_no_ipv4_passive",
    ("int_loopback", "EIGRP_NO_IPV6_PASSIVE"): "eigrp_no_ipv6_passive",
    ("int_loopback", "ENABLE_EIGRP_SHUTDOWN"): "enable_eigrp_shutdown",
    ("int_loopback", "ENABLE_EIGRP_BFD"): "enable_eigrp_bfd",
    ("int_loopback", "DISABLE_EIGRP_BFD"): "disable_eigrp_bfd",
    # --- HSRP on int_vlan (slice 0b_26) ---
    #
    # The first three rows that sit on top of MODULE-NATIVE fields. enable_hsrp, hsrp_vip,
    # hsrp_group, preempt and hsrp_priority are already in the native SVI arg spec; the engine
    # contributes only these three, which it does not carry. So they cannot be exercised alone --
    # a round has to build a working HSRP group with the native fields first.
    #
    # int_vlan is the only parent of the four that declares HSRP. The template enforces the whole
    # dependency chain itself (six rules around :782-:830), including `lower cannot be greater
    # than upper` -- a relationship BETWEEN two fields that no per-field min/max can express and
    # the registry cannot declare. Not duplicated here; NDFC fails loudly on it.
    ("int_vlan", "HSRP_PRIORITY_FORWARDING_THRESHOLD_LOWER"): "hsrp_priority_forwarding_threshold_lower",
    ("int_vlan", "HSRP_PRIORITY_FORWARDING_THRESHOLD_UPPER"): "hsrp_priority_forwarding_threshold_upper",
    ("int_vlan", "HSRP_PREEMPT_DELAY_MINIMUM"): "hsrp_preempt_delay_minimum",
    # --- HSRP IPv6 on int_vlan (slice 0b_27) ---
    #
    # Four rows for what was asked as one. HSRP_GROUPv6 cannot produce a line on its own: the
    # DSL's whole IPv6 block sits behind `if ipv6_vip:` (HSRP_VIPv6), and before that a bare
    # `except` clears ipv6_vip when PREFIXv6 is missing -- so without the prefix the block is
    # skipped SILENTLY. The chain is IPv6 + PREFIXv6 + HSRP_VIPv6, and only then does
    # HSRP_GROUPv6 have anything to change.
    #
    # IPv6 and PREFIXv6 are interface addressing, not HSRP, and they are here rather than in
    # svi_prof_spec because int_vlan names its prefix PREFIXv6 while int_subif and
    # int_routed_host name theirs IPv6_PREFIX. The native builder writes IPv6_PREFIX; making it
    # branch per parent is exactly what resolving by (parent, nvpair) avoids.
    #
    # The two address fields are ipV6Address in the template and go in as `string` -- the FIRST
    # two rows of the table that correspond to an address field. The module stops validating the
    # format; NDFC still does, with its own rules (`host address part cannot be all 0s`). That is
    # delegation, not fail-open -- but it is a precedent, and it does NOT resolve
    # DHCP_RELAY_SRC_INTF (type `interface`) or HSRP_SECONDARY_VIPS (struct list of 16).
    #
    # No collision: dcnm_intf_get_svi_payload writes ENABLE_HSRP, HSRP_GROUP, HSRP_PRIORITY,
    # HSRP_VERSION and HSRP_VIP by hand, none of these four.
    # IPv6 / PREFIXv6 WITHDRAWN from this slice -- measured defect, not a preference.
    #
    # Registering ("int_vlan", "IPv6") -> "ipv6_addr" made the engine's guard claim that public
    # key GLOBALLY, and it then rejected ipv6_addr on int_subif, where the NATIVE arg spec
    # supports it:
    #
    #     'ipv6_addr' is not supported on this interface (type 'sub_int', mode 'subint').
    #     No template metadata was queried and no change was sent.
    #
    # Two of test_dcnm_intf.py's subinterface tests caught it. A profile_key the native spec
    # already serves on OTHER parents cannot be registered for one parent: the guard is not
    # per-parent for the rejection path even though the binding is.
    #
    # test_gie_legacy_and_engine_never_collide did NOT catch this -- it checks whether the
    # REGISTERED parent's builder writes the nvPair by hand, and the SVI builder does not write
    # IPv6. The blind spot is the other parents' builders. Recorded in phase37.
    #
    # SVI IPv6 addressing belongs in svi_prof_spec, where it already lives for int_subif and
    # int_loopback -- with the caveat that int_vlan names its prefix PREFIXv6 while the others
    # use IPv6_PREFIX, so the native path needs that mapping.
    ("int_vlan", "HSRP_VIPv6"): "hsrp_vipv6",
    ("int_vlan", "HSRP_GROUPv6"): "hsrp_groupv6",
    # --- split redirects + ND suppress-RA (slice 0b_28) ---
    #
    # Three fields on three parents. int_loopback declares none of them.
    #
    # DISABLE_IP_REDIRECTS is excluded deliberately: it is native (disable_ip_redirects has six
    # uses in the module). Registering it would repeat the ipv6_addr failure: gie_guarded_keys()
    # contains profile keys without parents, so it would claim the name globally. Check public
    # names in dcnm_interface.py before registering them. The three below have no native uses.
    #
    # The native field gates both split fields through IsShow="DISABLE_IP_REDIRECTS!=true"
    # and combines with them using OR. Its default differs: false on routed/subif, true on
    # int_vlan. That default caused the SVI blocker: on that parent, the split fields remain
    # hidden unless the run sends disable_ip_redirects: false.
    #
    # Unlike BFD and HSRP, each field has its own CLI line. The
    # routed_interface_redirects_disable child tests each value independently.
    ("int_routed_host", "DISABLE_IPV4_REDIRECTS"): "disable_ipv4_redirects",
    ("int_routed_host", "DISABLE_IPV6_REDIRECTS"): "disable_ipv6_redirects",
    ("int_routed_host", "IPV6_ND_SUPPRESS_RA"): "ipv6_nd_suppress_ra",
    ("int_subif", "DISABLE_IPV4_REDIRECTS"): "disable_ipv4_redirects",
    ("int_subif", "DISABLE_IPV6_REDIRECTS"): "disable_ipv6_redirects",
    ("int_subif", "IPV6_ND_SUPPRESS_RA"): "ipv6_nd_suppress_ra",
    ("int_vlan", "DISABLE_IPV4_REDIRECTS"): "disable_ipv4_redirects",
    ("int_vlan", "DISABLE_IPV6_REDIRECTS"): "disable_ipv6_redirects",
    ("int_vlan", "IPV6_ND_SUPPRESS_RA"): "ipv6_nd_suppress_ra",
    # --- Dampening on int_routed_host (slice 0b_6) ---
    #
    # Seven, on this parent only: int_subif, int_vlan and int_loopback declare none.
    #
    # These rows already existed in 0b_6 with `mechanism: child_pti`, but never reached the
    # table because they were absent from this allowlist; the generator silently skips
    # unselected rows. Their mechanism was corrected to passthrough in the existing slice.
    # An initial duplicate 0b_29 slice failed with "duplicate committed binding", as with
    # the eight BFD rows.
    #
    # This family cannot be validated on the device: C9300v NX-OS lacks `dampening`.
    # NDFC probes on FAB1 (lite 10.5.5) and FAB4 (full 10.6.2) both returned
    # "CLI command is invalid". Phase33 attributed this to the lite image, but the full
    # FAB4 image also rejects it despite supporting EIGRP. The limitation is not "lite".
    #
    # Controller validation remains possible: POST evaluates the template before deployment,
    # exercising all four dependency rules and allowing read-back. Device validation is
    # excluded because of the platform limitation, not because the run was omitted.
    #
    # This is the registry's deepest chain, with four levels and four template rules.
    # One rule links three registered fields ("reuse, suppress and max suppress must
    # be configured together"), unlike earlier batches. None of those rules is duplicated here.
    ("int_routed_host", "ENABLE_DAMPENING"): "enable_dampening",
    ("int_routed_host", "DAMPENING_HALF_LIFE"): "dampening_half_life",
    ("int_routed_host", "DAMPENING_REUSE"): "dampening_reuse",
    ("int_routed_host", "DAMPENING_SUPPRESS"): "dampening_suppress",
    ("int_routed_host", "DAMPENING_MAX_SUPPRESS"): "dampening_max_suppress",
    ("int_routed_host", "DAMPENING_RESTART"): "dampening_restart",
    ("int_routed_host", "DAMPENING_RESTART_PENALTY"): "dampening_restart_penalty",
    # --- ARP_TIMEOUT on the three overlay parents (slice 0b_30) ---
    #
    # The simplest registry case: one field, one child, one CLI line
    # (`interface_ip_arp_timeout_11_1` -> `ip arp timeout $$ARP_TIMEOUT$$`), without a boolean
    # gate, cross-field dependencies or IsShow. int_loopback does not declare it.
    #
    # `integer ARP_TIMEOUT { min=60; max=28800; }` is identical on all three, with no defaultValue.
    # The missing default caused the redirects batch to abort, but needs no engine change
    # here: exemption (3) in gie_validate_binding_value already accepts "" for an integer read
    # from HAVE, through the OSPF_COST path. This was checked in the code before registration.
    #
    # The device supports it: the phase33 probe sent `ip arp timeout 300` and the line
    # appeared, unlike dampening above, whose CLI is unavailable on this platform.
    #
    # OPEN: none of the three template bodies calls deleteChildTemplate for this child, and
    # emission is gated by `if arpTimeout != ""`. Sending "" does not request removal of an
    # existing child. This matches the residue left on a physical port during EIGRP testing,
    # so the three rows retain removal_semantics: unresolved until measured live.
    ("int_routed_host", "ARP_TIMEOUT"): "arp_timeout",
    ("int_subif", "ARP_TIMEOUT"): "arp_timeout",
    ("int_vlan", "ARP_TIMEOUT"): "arp_timeout",
    # --- PIM, across all four parents (slice 0b_31) ---
    #
    # Eight rows with an uneven distribution; the distribution is the assertion:
    #     ENABLE_PIM_SPARSE        4   all four parents
    #     PIM_DR_PRIORITY          3   no int_loopback: a loopback does not elect a DR
    #     ENABLE_PIM_BFD_INSTANCE  1   declared only by int_routed_host
    #
    # One CLI line per field (pim_interface, interface_pim_dr_priority,
    # pim_bfd_instance_interface); all three children were installed and inspected.
    # Their output is not combined, unlike BFD, HSRP and dampening.
    #
    # All three are independent: no IsShow or addErrorReport connects them, and each has its
    # own `if`. Negative tests therefore target registry bounds rather than template rules,
    # as with ARP_TIMEOUT. The DSL does not require sparse-mode before dr-priority, so the
    # template can emit dr-priority alone. The device response remains a live-test question.
    #
    # Important boundary case: `if pimDrPriority != "" and pimDrPriority != "1"`.
    # Value 1 emits no line, and `min = 1` makes that value the lower bound.
    # No CLI at the lower bound is expected behavior, not a defect.
    #
    # PIM_DR_PRIORITY is `long` in the template and registered as `integer`:
    # _TYPE_TO_VALIDATOR does not recognize `long`; Python integers support 4294967295.
    # This is the first registry field whose template type is absent from that map.
    ("int_loopback", "ENABLE_PIM_SPARSE"): "enable_pim_sparse",
    ("int_routed_host", "ENABLE_PIM_SPARSE"): "enable_pim_sparse",
    ("int_subif", "ENABLE_PIM_SPARSE"): "enable_pim_sparse",
    ("int_vlan", "ENABLE_PIM_SPARSE"): "enable_pim_sparse",
    ("int_routed_host", "PIM_DR_PRIORITY"): "pim_dr_priority",
    ("int_subif", "PIM_DR_PRIORITY"): "pim_dr_priority",
    ("int_vlan", "PIM_DR_PRIORITY"): "pim_dr_priority",
    ("int_routed_host", "ENABLE_PIM_BFD_INSTANCE"): "enable_pim_bfd_instance",
    # --- IPv6 link-local on the three overlay parents (slice 0b_32) ---
    #
    # Three rows: int_loopback does not declare it. The installed child is
    # interface_ipv6_link_local_address_11_1 -> `ipv6 link-local $$IPV6_LINK_LOCAL$$`.
    #
    # The key is `IPv6_LINK_LOCAL`, with a lowercase v. The parent declares this spelling
    # and translates it when calling the child, which expects uppercase:
    #     ipv6LinkLocal = normalize(IPv6_LINK_LOCAL)   ->   {"IPV6_LINK_LOCAL": ipv6LinkLocal}
    # The module writes parent nvPairs, so it must use the parent's spelling. Copying the
    # child's spelling would make NDFC store an unread key: success reported, CLI absent.
    # This is the same distinction as PREFIXv6 versus IPv6_PREFIX.
    #
    # The template declares `ipV6Address`; register `string` with max_length 45, as for
    # HSRP_VIPv6. _TYPE_TO_VALIDATOR does not recognize `ipV6Address`, so registering that
    # type would make the binding unreachable through fail-closed validation, as `long`
    # would for PIM_DR_PRIORITY.
    #
    # Do not register ipv6_addr or ipv6_mask_len: they are native SVI arg-spec fields
    # (24 and 13 uses). Registering them would break int_subif and int_routed_host through
    # the global guard, as happened with ipv6_addr on 2026-09-20.
    ("int_routed_host", "IPv6_LINK_LOCAL"): "ipv6_link_local",
    ("int_subif", "IPv6_LINK_LOCAL"): "ipv6_link_local",
    ("int_vlan", "IPv6_LINK_LOCAL"): "ipv6_link_local",
    # --- MACSEC on int_routed_host (slice 0b_33) ---
    #
    # Four rows, only on this parent: it is the only one that declares them. IsShow gates
    # the three strings on the boolean, as with HSRP. Two strings are also IsMandatory when
    # enabled, providing the template rule for a negative test:
    # "MACsec keychain and policy are required when MACsec interface policy is enabled."
    #
    # These fields contain an enable flag and object names, not secrets: the strings refer to
    # a keychain and policy on the switch. Keep `no_log: false`; masking names would scrub
    # matching strings throughout Ansible output without protecting key material.
    # The material belongs to the keychain, which this module does not create.
    #
    # Parent and child names differ (MACSEC_KEY_CHAIN_NAME -> KEY_CHAIN_NAME, etc.).
    # The parent translates them; these rows use parent names, as with IPv6_LINK_LOCAL.
    #
    # The macsec_fallback_interface child has two branches, with and without fallback.
    # A single live run exercises only one.
    #
    # Measured live (FAB4, L1-F4, nxos64-cs.10.6.2.F): `feature macsec` was already enabled,
    # the CLI was supported and applied, and `system-default-macsec-policy` already existed.
    #
    # Validation is asymmetric: an unknown policy causes a 500 with "Failed to find policy",
    # but an unknown keychain is accepted and applied, leaving a dangling reference without
    # a warning. See phase44.
    ("int_routed_host", "ENABLE_MACSEC_INTERFACE_POLICY"): "enable_macsec_interface_policy",
    ("int_routed_host", "MACSEC_KEY_CHAIN_NAME"): "macsec_key_chain_name",
    ("int_routed_host", "MACSEC_POLICY_NAME"): "macsec_policy_name",
    ("int_routed_host", "MACSEC_FALLBACK_KEY_CHAIN_NAME"): "macsec_fallback_key_chain_name",
    # --- Batch 2: three unrelated fields on two parents (slice 0b_34) ---
    #
    # IPV4_ACL_IN on int_vlan reuses the public key already present on int_routed_host.
    # This is why bindings are keyed by (parent, nvpair), not by name alone.
    # Parent and child spellings differ again: the parent declares IPV4_ACL_IN and passes
    # {"IPV4_ACL": ipv4AclIn} to the child (int_vlan:1641). Use the parent's spelling.
    # Verification also needs care: NDFC lowercases the ACL name, while NX-OS `include`
    # is case-sensitive. Searching for the original spelling may return nothing.
    ("int_vlan", "IPV4_ACL_IN"): "ipv4_acl_in",
    # PRIVATE_VLAN_MAPPING is `integerRange` in the template, another type absent from
    # _TYPE_TO_VALIDATOR after PIM's `long` and link-local's `ipV6Address`. Register `string`,
    # without copying numeric bounds: the value is a list or range ("3194,3196" / "3194-3196",
    # according to Description). NDFC applies 1..4094 to each VLAN ID. Adding min/max here
    # would compare a string against an integer.
    ("int_vlan", "PRIVATE_VLAN_MAPPING"): "private_vlan_mapping",
    # ENABLE_VPC_PEER_LINK emits two lines: `vpc peer-link` and
    # `spanning-tree port type network`. It takes precedence over the BPDU guard branch
    # (:653-655). This parent also declares the registered SPANNING_TREE_PORT_TYPE field,
    # but an explicit `pass` (:670) ignores that field when peer-link is true.
    # The omission is silent: changed=True, `network` on the device, and no mention of the
    # requested `edge`. This resembles PIM_DR_PRIORITY's silent value 1, except that here
    # the ignored value was explicitly requested.
    #
    # Two template rules (:450, :457) provide negative test cases.
    #
    # Validated live on the Leaf-105/106 vPC pair (domain 105), using a disposable Po510 on
    # Eth1/7-1/8. An earlier comment incorrectly excluded device validation based on
    # observations from Leaf-103, which is not a vPC peer. Testing the actual pair showed:
    #
    #   NX-OS rejects a second peer-link in the domain; NDFC does not check this:
    #       ERROR: Operation failed: [vPC Peer-link has already been configured on po500]
    #   The error identifies each switch and deployment returns 500. The device enforces
    #   consistency, not the controller, complementing the keychain/ACL/link-local cases
    #   where NDFC accepted nonexistent or out-of-range objects.
    #
    #   Application is partial, which is what made the binding measurable on the device:
    #   `spanning-tree port type network` (:654) reaches it, but `vpc peer-link` (:686) does
    #   not. Rejection occurs at command #12, leaving earlier commands applied.
    #
    #   Two settings are silently ignored, as demonstrated by a control:
    #       peer-link false -> `spanning-tree port type normal` + `... bpduguard enable`
    #       peer-link true  -> neither; `... port type network` appears instead
    #   Without the control, missing CLI could also mean the field has no effect at all.
    #   Code inspection shows the same behavior for BPDUFILTER_ENABLED (:660).
    #
    #   The discard is not detectable from any layer. NDFC stores the requested
    #   SPANNING_TREE_PORT_TYPE: "normal", while its own pendingConfig emits `network`
    #   (observed with forceShowRun=true) -- the same template generates both. So on a pair
    #   without an existing peer-link, controller and device would agree and the interface
    #   would read In-Sync with the requested value stored and never applied.
    #
    #   Reapplying returns `replaced: []`: intent converges, but the device rejects deployment.
    #   Omitting the key preserves the stored "true". After restoration, both peers matched
    #   their original configuration line for line and were In-Sync with empty pendingConfig.
    #
    #   Successful `vpc peer-link` deployment was not measured: the lab has one pair and its
    #   domain already has a peer-link. This is a topology limit, not missing binding coverage.
    ("int_port_channel_trunk_host", "ENABLE_VPC_PEER_LINK"): "enable_vpc_peer_link",
}

# Fields carried into the runtime table (curated + generated), in a fixed order.
# min_length/max_length carry the registry string constraints (ACL_FILTER).
FIELDS = ["parent_template", "parent_nvpair", "profile_key", "applicable_interface_type",
          "applicable_mode", "type", "valid_values", "default_template", "mechanism",
          "min_ndfc_version", "min_length", "max_length", "min_value", "max_value",
          "no_log"]

# The registry spells the numeric bounds `min` and `max`; the runtime table spells them
# `min_value` and `max_value`. The rename is deliberate: a substring test for "min" -- the
# obvious way to look for these -- also matches `min_ndfc_version` and `min_length`, which is
# exactly the confusion that let 15 declared bounds sit unenforced without anyone noticing.
REGISTRY_FIELD_ALIASES = {"min_value": "min", "max_value": "max"}

# Mechanisms gie_engine can interpret. Anything else is rejected at compile time rather than
# shipped into the runtime table -- see the fail-open note in compile_rows().
KNOWN_MECHANISMS = {"passthrough", "child_pti"}

# Public profile keys owned by the committed set; see the module docstring for why a row
# outside the set that reuses one of them is rejected instead of skipped.
COMMITTED_PROFILE_KEYS = set(COMMITTED_BINDINGS.values())


# Per-row registry schema, enforced HERE rather than by a separate checker script.
#
# WHY HERE. There were two standalone validators under
# evidence/generic-interface-engine/ -- registry-schema/registry_schema_check.py (42 lines) and
# registry/registry_schema_check.py (454 lines) -- and BOTH had been dead for four lots without
# anyone noticing, for different reasons: the first still expected a flat list and every slice is
# now a mapping with a `bindings:` key, the second required a `sensitive` field that only one
# surviving slice declares. Nothing broke loudly because nothing ran them. A validator you have
# to remember to invoke is a validator that goes stale; this function runs on every regeneration,
# which is the only moment the rows are read at all.
#
# SCOPE. Exactly what the dead checkers enforced per row, no more -- recovering a lost net, not
# widening it. Deliberately NOT re-implemented here because compile_rows already does it above:
# the COMMITTED_BINDINGS allowlist, duplicate keys, profile_key mismatch, unknown mechanism, and
# the complete-set check. Deliberately NOT required: `sensitive` (gone from every slice but
# 0b_21) and `evidence_ref` (0b_15's eleven rows have never carried one; adding it is a separate
# decision about data, not about this gate).
SCHEMA_REQUIRED_FIELDS = (
    "parent_template",
    "parent_nvpair",
    "profile_key",
    "applicable_interface_type",
    "applicable_mode",
    "type",
    "presence_model",
    "emit_when",
    "mechanism",
    "min_ndfc_version",
    # One value in the whole registry: 212 occurrences, all `desired_parent`. The 454-line
    # checker asserted the literal, and a negative test rejected `type_builder`.
    "parent_resolution",
)

SCHEMA_TYPES = frozenset({"boolean", "integer", "string", "enum"})


def _check_registry_schema(r, key):
    """Reject a row the registry schema does not describe, naming the row and the reason.

    raise, not assert: `python -O` strips assertions, and the comment on the mechanism gate
    above records that as the explicit reason for the convention in this file.
    """
    missing = [f for f in SCHEMA_REQUIRED_FIELDS if f not in r]
    if missing:
        raise ValueError(
            "binding {0!r} is missing required registry field(s) {1}".format(
                key, sorted(missing)
            )
        )
    if r["presence_model"] != "two_axis":
        raise ValueError(
            "binding {0!r} declares presence_model {1!r}; the registry models every "
            "binding as 'two_axis'".format(key, r["presence_model"])
        )
    if r["emit_when"] != "explicit_only":
        raise ValueError(
            "binding {0!r} declares emit_when {1!r}; the registry emits every binding "
            "'explicit_only', which is what makes omission preserve".format(
                key, r["emit_when"]
            )
        )
    if r["type"] not in SCHEMA_TYPES:
        raise ValueError(
            "binding {0!r} declares type {1!r}; known values are {2}".format(
                key, r["type"], sorted(SCHEMA_TYPES)
            )
        )


def compile_rows(slice_rows):
    out = []
    seen = set()
    for r in slice_rows:
        key = (r.get("parent_template"), r.get("parent_nvpair"))
        if key not in COMMITTED_BINDINGS:
            # Not committed. Reject rather than skip when it claims a committed public key.
            if r.get("profile_key") in COMMITTED_PROFILE_KEYS:
                raise ValueError(
                    "unexpected binding {0!r} claims committed profile_key {1!r}".format(
                        key, r.get("profile_key")
                    )
                )
            continue
        if key in seen:
            raise ValueError("duplicate committed binding {0!r}".format(key))
        if r.get("profile_key") != COMMITTED_BINDINGS[key]:
            raise ValueError(
                "unexpected profile_key for committed binding {0!r}".format(key)
            )
        seen.add(key)
        # A mechanism the engine does not know is FAIL-OPEN, not inert: gie_engine compares
        # `== GIE_MECH_PASSTHROUGH` at four sites (generic arg spec, invalid-parent guard,
        # nvPair wire serialization, carry-forward), so an unknown or missing value silently
        # behaves exactly like child_pti and drops the binding out of the generic route. A typo
        # would ship a key that is transported but unguarded and never wire-serialized.
        #
        # raise, not assert: `python -O` strips assertions, and this is a correctness gate.
        #
        # This only rejects labels the engine cannot interpret. It does NOT catch a VALID
        # `child_pti` placed on a binding that owns no dedicated implementation -- which is the
        # error this table actually hit. That needs a test asserting every child_pti binding has
        # one; see test_gie_routed_bindings.py.
        mech = r.get("mechanism")
        if mech not in KNOWN_MECHANISMS:
            raise ValueError(
                "binding {0!r} declares mechanism {1!r}; known values are {2}".format(
                    key, mech, sorted(KNOWN_MECHANISMS)
                )
            )
        _check_registry_schema(r, key)
        row = {}
        for f in FIELDS:
            src = REGISTRY_FIELD_ALIASES.get(f, f)
            if src in r:
                v = r[src]
                if isinstance(v, list):
                    v = tuple(v)
                row[f] = v
        out.append(row)
    if seen != set(COMMITTED_BINDINGS):
        missing = sorted(set(COMMITTED_BINDINGS) - seen)
        raise ValueError("missing committed bindings {0!r}".format(missing))
    out.sort(key=lambda x: (x["parent_template"], x["parent_nvpair"]))
    return out


def render(rows):
    prov = hashlib.sha256(json.dumps(rows, sort_keys=True, default=list).encode()).hexdigest()
    lines = [
        "# GENERATED - DO NOT EDIT. Static interface binding table.",
        "# Generator: tools/gie_generate_binding_table.py, from the approved registry YAML.",
        "# Runtime imports this module only; it never reads YAML or NDFC templates.",
        f"# provenance_sha256 = {prov}",
        "",
        "from __future__ import absolute_import, division, print_function",
        "__metaclass__ = type",
        "",
        f'PROVENANCE_SHA256 = "{prov}"',
        "",
        "BINDING_TABLE = (",
    ]
    # One key per line rather than one row per line. A row rendered flat reaches ~350
    # characters, well past the 160-column sanity limit, and the generated file is the one
    # place a human cannot fix it by hand -- it says DO NOT EDIT and a regeneration would undo
    # the fix. Wrapping here keeps the output both compliant and diffable: adding a field to a
    # binding shows up as one added line instead of a rewritten row.
    for row in rows:
        lines.append("    {")
        for k in FIELDS:
            if k in row:
                lines.append("        %r: %r," % (k, row[k]))
        lines.append("    },")
    lines += [
        ")",
        "",
        "",
        "def registered_profile_keys(parent_template):",
        '    """Public profile keys registered for a parent (thin: exact set, no name heuristic)."""',
        "    return {b['profile_key'] for b in BINDING_TABLE if b['parent_template'] == parent_template}",
        "",
        "",
        "def resolve_binding(parent_template, profile_key):",
        '    """Exactly one binding for (parent_template, profile_key), or None."""',
        "    hits = [b for b in BINDING_TABLE",
        "            if b['parent_template'] == parent_template and b['profile_key'] == profile_key]",
        "    return hits[0] if len(hits) == 1 else None",
        "",
        "",
        "def resolve_by_nvpair(parent_template, parent_nvpair):",
        "    hits = [b for b in BINDING_TABLE",
        "            if b['parent_template'] == parent_template and b['parent_nvpair'] == parent_nvpair]",
        "    return hits[0] if len(hits) == 1 else None",
    ]
    return "\n".join(lines) + "\n"


def main(*paths):
    if len(paths) < 2:
        raise SystemExit(__doc__)
    slice_paths, out_path = list(paths[:-1]), paths[-1]
    slice_rows = []
    for p in slice_paths:
        doc = yaml.safe_load(open(p))
        if isinstance(doc, dict):
            doc = doc.get("bindings", [])
        slice_rows.extend(doc or [])
    rows = compile_rows(slice_rows)
    assert len(rows) == len(COMMITTED_BINDINGS), \
        f"expected {len(COMMITTED_BINDINGS)} committed bindings, compiled {len(rows)}"
    open(out_path, "w").write(render(rows))
    print(f"compiled {len(rows)} bindings -> {out_path}")
    for r in rows:
        print("  ", r["parent_template"], "::", r["parent_nvpair"], "->", r["mechanism"])


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
