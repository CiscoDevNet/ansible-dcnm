#!/usr/bin/env python3
"""Deterministic generator for the thin-engine binding table (Phase 1).

Compiles the COMMITTED bindings from the APPROVED Phase-0B registry into a static Python
artifact under plugins/module_utils/. Runtime imports the artifact only; it never reads the
investigation evidence dir or NDFC template files.

Committed bindings (and ONLY these):

  A1.5 slice — unchanged, frozen observable contract:
    - int_fabric_loopback_11_1 :: ENABLE_OSPF_AUTH_MESSAGE_DIGEST  (boolean, child_pti)
    - int_access_host          :: FLOWCONTROL_RECEIVE              (enum on/off, passthrough)
    - int_trunk_host           :: FLOWCONTROL_RECEIVE              (enum on/off, passthrough)

  A1.6 slice — simple passthrough, from reviewed registry slices 0b_7/0b_8/0b_9:
    - int_trunk_host                    :: GUARD_MODE    (enum, passthrough)
    - int_port_channel_trunk_host       :: GUARD_MODE    (enum, passthrough)
    - int_access_host                   :: DISABLE_LLDP  (boolean, passthrough)
    - int_trunk_host                    :: DISABLE_LLDP  (boolean, passthrough)
    - int_access_host                   :: ACL_FILTER    (string, passthrough)
    - int_trunk_host                    :: ACL_FILTER    (string, passthrough)
    - int_port_channel_access_host      :: ACL_FILTER    (string, passthrough)
    - int_port_channel_trunk_host       :: ACL_FILTER    (string, passthrough)
    - int_port_channel_dot1q_tunnel_host:: ACL_FILTER    (string, passthrough)

  FLOWCONTROL slice — companion of the A1.5 receive binding, from registry slice 0b_11:
    - int_trunk_host  :: FLOWCONTROL_SEND  (enum on/off, passthrough)
    - int_access_host :: FLOWCONTROL_SEND  (enum on/off, passthrough)
  Sweeping all 90+ templates confirms ONLY these two parents carry FLOWCONTROL, so together
  with the A1.5 receive rows these four entries close the field's universe.

  A1.9 slice — OSPF legacy-key pair, from reviewed registry slice 0b_10:
    - int_fabric_loopback_11_1 :: OSPF_AUTH_KEY_ID  (integer, child_pti)
    - int_fabric_loopback_11_1 :: OSPF_AUTH_KEY     (string,  child_pti)
  Ambos alimentan el MISMO hijo (ospf_interface_auth) y por eso comparten mecanismo y
  effect_rules. La atomicidad del par, el rango [0,255] y la exclusion de keychain NO se
  registran: permanecen en el validador dedicado del modulo, igual que ocurrio con el
  validador del booleano en la migracion A1.5.

The curated `profile_key` in the registry is authoritative. It is never derived by
lower-casing an nvPair name: a row whose profile_key does not match the committed value is
rejected rather than accepted or rewritten.

Usage: python3 gie_generate_binding_table.py <approved_slice_yaml> [<more_slices> ...] <output_py>
Deterministic: same input -> byte-identical output (sorted keys, fixed formatting, provenance
sha256 over the compiled rows).
"""
import sys, yaml, json, hashlib

MONDAY = {
    # --- A1.5 (frozen) ---
    ("int_fabric_loopback_11_1", "ENABLE_OSPF_AUTH_MESSAGE_DIGEST"):
        "enable_ospf_auth_message_digest",
    ("int_access_host", "FLOWCONTROL_RECEIVE"): "flowcontrol_receive",
    ("int_trunk_host", "FLOWCONTROL_RECEIVE"): "flowcontrol_receive",
    # --- A1.6: GUARD_MODE (registry slice 0b_7) ---
    ("int_trunk_host", "GUARD_MODE"): "guard_mode",
    ("int_port_channel_trunk_host", "GUARD_MODE"): "guard_mode",
    # --- A1.6: DISABLE_LLDP (registry slice 0b_8) ---
    ("int_access_host", "DISABLE_LLDP"): "disable_lldp",
    ("int_trunk_host", "DISABLE_LLDP"): "disable_lldp",
    # --- A1.6: ACL_FILTER (registry slice 0b_9) ---
    ("int_access_host", "ACL_FILTER"): "acl_filter",
    ("int_trunk_host", "ACL_FILTER"): "acl_filter",
    ("int_port_channel_access_host", "ACL_FILTER"): "acl_filter",
    ("int_port_channel_trunk_host", "ACL_FILTER"): "acl_filter",
    ("int_port_channel_dot1q_tunnel_host", "ACL_FILTER"): "acl_filter",
    # --- FLOWCONTROL_SEND (registry slice 0b_11) ---
    ("int_trunk_host", "FLOWCONTROL_SEND"): "flowcontrol_send",
    ("int_access_host", "FLOWCONTROL_SEND"): "flowcontrol_send",
    # --- A1.9: par de clave OSPF legacy (registry slice 0b_10) ---
    ("int_fabric_loopback_11_1", "OSPF_AUTH_KEY_ID"): "ospf_auth_key_id",
    ("int_fabric_loopback_11_1", "OSPF_AUTH_KEY"): "ospf_auth_key",
}

# Fields carried into the runtime table (curated + generated), in a fixed order.
# min_length/max_length carry the reviewed string constraints (ACL_FILTER).
FIELDS = ["parent_template", "parent_nvpair", "profile_key", "applicable_interface_type",
          "applicable_mode", "type", "valid_values", "default_template", "mechanism",
          "min_ndfc_version", "min_length", "max_length"]

# Public profile keys owned by the committed set. A row that reuses one of these keys on a
# parent/nvPair that is NOT committed is an UNEXPECTED binding: the same public name exists in
# the ledger under other mechanisms (e.g. int_vpc_trunk_host::GUARD_MODE is child_pti), and
# skipping it silently would let a non-passthrough binding look merely "not selected".
COMMITTED_PROFILE_KEYS = set(MONDAY.values())


def compile_rows(slice_rows):
    out = []
    seen = set()
    for r in slice_rows:
        key = (r.get("parent_template"), r.get("parent_nvpair"))
        if key not in MONDAY:
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
        if r.get("profile_key") != MONDAY[key]:
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
    if seen != set(MONDAY):
        missing = sorted(set(MONDAY) - seen)
        raise ValueError("missing committed bindings {0!r}".format(missing))
    out.sort(key=lambda x: (x["parent_template"], x["parent_nvpair"]))
    return out


def render(rows):
    prov = hashlib.sha256(json.dumps(rows, sort_keys=True, default=list).encode()).hexdigest()
    lines = [
        "# GENERATED — DO NOT EDIT. Static thin-engine binding table (Phase 1).",
        "# Source: approved Phase-0B registry. Generator: tools/gie_generate_binding_table.py.",
        "# Runtime imports this module only; it does not read the evidence dir or templates.",
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
    assert len(rows) == len(MONDAY), \
        f"expected {len(MONDAY)} committed bindings, compiled {len(rows)}"
    open(out_path, "w").write(render(rows))
    print(f"compiled {len(rows)} bindings -> {out_path}")
    for r in rows:
        print("  ", r["parent_template"], "::", r["parent_nvpair"], "->", r["mechanism"])


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
