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
    ("int_vlan", "OSPF_TRANSMIT_DELAY"): "ospf_transmit_delay",
}

# Fields carried into the runtime table (curated + generated), in a fixed order.
# min_length/max_length carry the registry string constraints (ACL_FILTER).
FIELDS = ["parent_template", "parent_nvpair", "profile_key", "applicable_interface_type",
          "applicable_mode", "type", "valid_values", "default_template", "mechanism",
          "min_ndfc_version", "min_length", "max_length", "min_value", "max_value"]

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
