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
    # DISABLE_LLDP se retiro: la entrega del 14sep2026 lo elimina de los ocho parents y lo
    # parte en dos campos independientes. No es un rename -- el viejo apagaba las dos
    # direcciones juntas, estos permiten apagar solo una. Ver registry_slice_0b_17.
    #
    # Dejar el binding viejo registrado seria peor que no tenerlo: un PTI acepta nvPairs que su
    # template no declara, asi que DISABLE_LLDP seguiria viajando y viendose bien por API, sin
    # producir CLI nunca.
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
    # needed `feature bfd` and the two `no ...` forms. See phase34-fab4-eigrp-soporte.
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
    # Tres campos x tres padres. int_loopback no declara ninguno.
    #
    # DISABLE_IP_REDIRECTS queda FUERA a proposito: es nativo (disable_ip_redirects, 6 usos en
    # el modulo), y registrarlo repetiria el fallo de ipv6_addr -- gie_guarded_keys() es un set
    # de profile_key SIN padre, asi que reclamaria el nombre globalmente. La regla barata que
    # ese fallo dejo: grepear el nombre publico en dcnm_interface.py antes de registrar. Los
    # tres de abajo dan 0.
    #
    # El nativo GATEA a los dos split via IsShow="DISABLE_IP_REDIRECTS!=true" y se combina con
    # ellos por OR, y su default NO es uniforme: false en routed y subif, true en int_vlan --
    # el mismo default que causo el blocker del SVI. En ese padre los split estan ocultos salvo
    # que la ronda mande disable_ip_redirects: false.
    #
    # A diferencia de BFD y HSRP, cada campo tiene su PROPIA linea: el hijo
    # routed_interface_redirects_disable es condicional por dentro, uno por cada valor.
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
    # Siete, y SOLO en este padre: int_subif, int_vlan e int_loopback declaran 0 de 7.
    #
    # Las filas NO son nuevas: llevaban escritas en 0b_6 desde hace tiempo con
    # `mechanism: child_pti` y nunca llegaron a la tabla, porque no estaban en esta lista -- el
    # generador salta en silencio una fila que no este aqui. Corregidas a passthrough en el slice
    # existente; un primer intento creo un 0b_29 duplicado y el generador lo rechazo con
    # "duplicate committed binding". Misma historia que las ocho de BFD.
    #
    # LA UNICA FAMILIA QUE NO LLEGA AL EQUIPO. `dampening` no existe en el NX-OS de C9300v:
    # sondeado por NDFC en FAB1 (lite 10.5.5) y en FAB4 (completa 10.6.2), las dos rechazan con
    # "CLI command is invalid". La fase 33 lo habia atribuido a la imagen lite; FAB4 corre la
    # completa -- la que si soporta EIGRP -- y tambien lo rechaza, asi que la causa no es "lite".
    #
    # Se registran igual porque la capa de CONTROLADOR si es validable: el POST evalua el template
    # antes del deploy, asi que las cuatro reglas de dependencia se ejercitan y el read-back se
    # lee. La capa de dispositivo queda fuera de alcance por hardware, no por falta de ronda.
    #
    # Cadena de cuatro niveles, la mas profunda del registro, y cuatro reglas del template --
    # una de ellas liga TRES campos registrados entre si ("reuse, suppress and max suppress must
    # be configured together"), algo que ningun lote anterior tenia. Ninguna se duplica aqui.
    ("int_routed_host", "ENABLE_DAMPENING"): "enable_dampening",
    ("int_routed_host", "DAMPENING_HALF_LIFE"): "dampening_half_life",
    ("int_routed_host", "DAMPENING_REUSE"): "dampening_reuse",
    ("int_routed_host", "DAMPENING_SUPPRESS"): "dampening_suppress",
    ("int_routed_host", "DAMPENING_MAX_SUPPRESS"): "dampening_max_suppress",
    ("int_routed_host", "DAMPENING_RESTART"): "dampening_restart",
    ("int_routed_host", "DAMPENING_RESTART_PENALTY"): "dampening_restart_penalty",
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
