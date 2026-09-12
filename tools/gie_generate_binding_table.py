#!/usr/bin/env python3
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
import sys, yaml, json, hashlib

COMMITTED_BINDINGS = {
    # Fabric loopback, child_pti. The two key rows feed the same child policy
    # (ospf_interface_auth), so they share mechanism and effect rules.
    ("int_fabric_loopback_11_1", "ENABLE_OSPF_AUTH_MESSAGE_DIGEST"):
        "enable_ospf_auth_message_digest",
    ("int_fabric_loopback_11_1", "OSPF_AUTH_KEY_ID"): "ospf_auth_key_id",
    ("int_fabric_loopback_11_1", "OSPF_AUTH_KEY"): "ospf_auth_key",

    # Host ethernet and port-channel parents, passthrough.
    ("int_access_host", "FLOWCONTROL_RECEIVE"): "flowcontrol_receive",
    ("int_trunk_host", "FLOWCONTROL_RECEIVE"): "flowcontrol_receive",
    ("int_access_host", "FLOWCONTROL_SEND"): "flowcontrol_send",
    ("int_trunk_host", "FLOWCONTROL_SEND"): "flowcontrol_send",

    ("int_trunk_host", "GUARD_MODE"): "guard_mode",
    ("int_port_channel_trunk_host", "GUARD_MODE"): "guard_mode",

    ("int_access_host", "DISABLE_LLDP"): "disable_lldp",
    ("int_trunk_host", "DISABLE_LLDP"): "disable_lldp",

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

    ("int_port_channel_access_host", "DISABLE_LLDP"): "disable_lldp",
    ("int_port_channel_trunk_host", "DISABLE_LLDP"): "disable_lldp",
    ("int_port_channel_dot1q_tunnel_host", "DISABLE_LLDP"): "disable_lldp",

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

    ("int_vpc_trunk_host", "DISABLE_LLDP"): "disable_lldp",
    ("int_vpc_access_host", "DISABLE_LLDP"): "disable_lldp",

    ("int_vpc_trunk_host", "ACL_FILTER"): "acl_filter",
    ("int_vpc_access_host", "ACL_FILTER"): "acl_filter",

    # trunk only: int_vpc_access_host does not declare GUARD_MODE.
    ("int_vpc_trunk_host", "GUARD_MODE"): "guard_mode",

    ("int_vpc_trunk_host", "DISABLE_QOS_STATS"): "disable_qos_stats",
    ("int_vpc_access_host", "DISABLE_QOS_STATS"): "disable_qos_stats",

    ("int_vpc_trunk_host", "DISABLE_QUEUING_STATS"): "disable_queuing_stats",
    ("int_vpc_access_host", "DISABLE_QUEUING_STATS"): "disable_queuing_stats",
}

# Fields carried into the runtime table (curated + generated), in a fixed order.
# min_length/max_length carry the registry string constraints (ACL_FILTER).
FIELDS = ["parent_template", "parent_nvpair", "profile_key", "applicable_interface_type",
          "applicable_mode", "type", "valid_values", "default_template", "mechanism",
          "min_ndfc_version", "min_length", "max_length"]

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
        row = {}
        for f in FIELDS:
            if f in r:
                v = r[f]
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
    for row in rows:
        items = ", ".join("%r: %r" % (k, row[k]) for k in FIELDS if k in row)
        lines.append("    {" + items + "},")
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
