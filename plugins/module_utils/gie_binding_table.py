# GENERATED — DO NOT EDIT. Static thin-engine binding table (Phase 1).
# Source: approved Phase-0B registry. Generator: tools/gie_generate_binding_table.py.
# Runtime imports this module only; it does not read the evidence dir or templates.
# provenance_sha256 = 9902134894d037825ef34d093c8223c97969b9b4620992d47140bc9ea42c0ca5

from __future__ import absolute_import, division, print_function
__metaclass__ = type

PROVENANCE_SHA256 = "9902134894d037825ef34d093c8223c97969b9b4620992d47140bc9ea42c0ca5"

BINDING_TABLE = (
    {'parent_template': 'int_access_host', 'parent_nvpair': 'ACL_FILTER', 'profile_key': 'acl_filter', 'applicable_interface_type': 'eth', 'applicable_mode': 'access', 'type': 'string', 'mechanism': 'passthrough', 'min_ndfc_version': '12.6.0.267', 'min_length': 1, 'max_length': 64},
    {'parent_template': 'int_access_host', 'parent_nvpair': 'DISABLE_LLDP', 'profile_key': 'disable_lldp', 'applicable_interface_type': 'eth', 'applicable_mode': 'access', 'type': 'boolean', 'default_template': False, 'mechanism': 'passthrough', 'min_ndfc_version': '12.6.0.267'},
    {'parent_template': 'int_access_host', 'parent_nvpair': 'FLOWCONTROL_RECEIVE', 'profile_key': 'flowcontrol_receive', 'applicable_interface_type': 'eth', 'applicable_mode': 'access', 'type': 'enum', 'valid_values': ('on', 'off'), 'default_template': 'off', 'mechanism': 'passthrough', 'min_ndfc_version': '12.6.0.267'},
    {'parent_template': 'int_access_host', 'parent_nvpair': 'FLOWCONTROL_SEND', 'profile_key': 'flowcontrol_send', 'applicable_interface_type': 'eth', 'applicable_mode': 'access', 'type': 'enum', 'valid_values': ('on', 'off'), 'default_template': 'off', 'mechanism': 'passthrough', 'min_ndfc_version': '12.6.0.267'},
    {'parent_template': 'int_access_host', 'parent_nvpair': 'SPANNING_TREE_PORT_TYPE', 'profile_key': 'spanning_tree_port_type', 'applicable_interface_type': 'eth', 'applicable_mode': 'access', 'type': 'enum', 'valid_values': ('no', 'network', 'normal'), 'default_template': 'no', 'mechanism': 'passthrough', 'min_ndfc_version': '12.6.0.267'},
    {'parent_template': 'int_fabric_loopback_11_1', 'parent_nvpair': 'ENABLE_OSPF_AUTH_MESSAGE_DIGEST', 'profile_key': 'enable_ospf_auth_message_digest', 'applicable_interface_type': 'lo', 'applicable_mode': 'fabric', 'type': 'boolean', 'default_template': False, 'mechanism': 'child_pti', 'min_ndfc_version': '12.6.0.267'},
    {'parent_template': 'int_fabric_loopback_11_1', 'parent_nvpair': 'OSPF_AUTH_KEY', 'profile_key': 'ospf_auth_key', 'applicable_interface_type': 'lo', 'applicable_mode': 'fabric', 'type': 'string', 'mechanism': 'child_pti', 'min_ndfc_version': '12.6.0.267', 'min_length': 1},
    {'parent_template': 'int_fabric_loopback_11_1', 'parent_nvpair': 'OSPF_AUTH_KEY_ID', 'profile_key': 'ospf_auth_key_id', 'applicable_interface_type': 'lo', 'applicable_mode': 'fabric', 'type': 'integer', 'mechanism': 'child_pti', 'min_ndfc_version': '12.6.0.267'},
    {'parent_template': 'int_port_channel_access_host', 'parent_nvpair': 'ACL_FILTER', 'profile_key': 'acl_filter', 'applicable_interface_type': 'pc', 'applicable_mode': 'access', 'type': 'string', 'mechanism': 'passthrough', 'min_ndfc_version': '12.6.0.267', 'min_length': 1, 'max_length': 64},
    {'parent_template': 'int_port_channel_dot1q_tunnel_host', 'parent_nvpair': 'ACL_FILTER', 'profile_key': 'acl_filter', 'applicable_interface_type': 'pc', 'applicable_mode': 'dot1q', 'type': 'string', 'mechanism': 'passthrough', 'min_ndfc_version': '12.6.0.267', 'min_length': 1, 'max_length': 64},
    {'parent_template': 'int_port_channel_trunk_host', 'parent_nvpair': 'ACL_FILTER', 'profile_key': 'acl_filter', 'applicable_interface_type': 'pc', 'applicable_mode': 'trunk', 'type': 'string', 'mechanism': 'passthrough', 'min_ndfc_version': '12.6.0.267', 'min_length': 1, 'max_length': 64},
    {'parent_template': 'int_port_channel_trunk_host', 'parent_nvpair': 'GUARD_MODE', 'profile_key': 'guard_mode', 'applicable_interface_type': 'pc', 'applicable_mode': 'trunk', 'type': 'enum', 'valid_values': ('root', 'none', 'loop', 'no'), 'default_template': 'no', 'mechanism': 'passthrough', 'min_ndfc_version': '12.6.0.267'},
    {'parent_template': 'int_trunk_host', 'parent_nvpair': 'ACL_FILTER', 'profile_key': 'acl_filter', 'applicable_interface_type': 'eth', 'applicable_mode': 'trunk', 'type': 'string', 'mechanism': 'passthrough', 'min_ndfc_version': '12.6.0.267', 'min_length': 1, 'max_length': 64},
    {'parent_template': 'int_trunk_host', 'parent_nvpair': 'DISABLE_LLDP', 'profile_key': 'disable_lldp', 'applicable_interface_type': 'eth', 'applicable_mode': 'trunk', 'type': 'boolean', 'default_template': False, 'mechanism': 'passthrough', 'min_ndfc_version': '12.6.0.267'},
    {'parent_template': 'int_trunk_host', 'parent_nvpair': 'FLOWCONTROL_RECEIVE', 'profile_key': 'flowcontrol_receive', 'applicable_interface_type': 'eth', 'applicable_mode': 'trunk', 'type': 'enum', 'valid_values': ('on', 'off'), 'default_template': 'off', 'mechanism': 'passthrough', 'min_ndfc_version': '12.6.0.267'},
    {'parent_template': 'int_trunk_host', 'parent_nvpair': 'FLOWCONTROL_SEND', 'profile_key': 'flowcontrol_send', 'applicable_interface_type': 'eth', 'applicable_mode': 'trunk', 'type': 'enum', 'valid_values': ('on', 'off'), 'default_template': 'off', 'mechanism': 'passthrough', 'min_ndfc_version': '12.6.0.267'},
    {'parent_template': 'int_trunk_host', 'parent_nvpair': 'GUARD_MODE', 'profile_key': 'guard_mode', 'applicable_interface_type': 'eth', 'applicable_mode': 'trunk', 'type': 'enum', 'valid_values': ('root', 'none', 'loop', 'no'), 'default_template': 'no', 'mechanism': 'passthrough', 'min_ndfc_version': '12.6.0.267'},
    {'parent_template': 'int_trunk_host', 'parent_nvpair': 'SPANNING_TREE_PORT_TYPE', 'profile_key': 'spanning_tree_port_type', 'applicable_interface_type': 'eth', 'applicable_mode': 'trunk', 'type': 'enum', 'valid_values': ('no', 'network', 'normal'), 'default_template': 'no', 'mechanism': 'passthrough', 'min_ndfc_version': '12.6.0.267'},
)


def registered_profile_keys(parent_template):
    """Public profile keys registered for a parent (thin: exact set, no name heuristic)."""
    return {b['profile_key'] for b in BINDING_TABLE if b['parent_template'] == parent_template}


def resolve_binding(parent_template, profile_key):
    """Exactly one binding for (parent_template, profile_key), or None."""
    hits = [b for b in BINDING_TABLE
            if b['parent_template'] == parent_template and b['profile_key'] == profile_key]
    return hits[0] if len(hits) == 1 else None


def resolve_by_nvpair(parent_template, parent_nvpair):
    hits = [b for b in BINDING_TABLE
            if b['parent_template'] == parent_template and b['parent_nvpair'] == parent_nvpair]
    return hits[0] if len(hits) == 1 else None
