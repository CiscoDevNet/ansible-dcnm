# Interface binding registry: sources and regeneration

`plugins/module_utils/gie_binding_table.py` is a **generated** file ("DO NOT EDIT"). Its canonical source is the set of
registry slices in `tools/registry/slices/` (`registry_slice_*.yaml`). The generator is
`tools/gie_generate_binding_table.py`. Everything needed to regenerate the table is in this repository.

## What is what

| Path | Role | Used at runtime by the module? |
|------|------|--------------------------------|
| `plugins/module_utils/gie_binding_table.py` | Compiled, versioned table (`BINDING_TABLE`, `PROVENANCE_SHA256`) | Yes. This is the only artifact the module imports. |
| `tools/registry/slices/*.yaml` | Canonical registry sources (one slice per lot of bindings) | No. Development tooling. |
| `tools/gie_generate_binding_table.py` | Deterministic generator and `--check` | No. Development tooling. |
| `tests/unit/modules/dcnm/test_gie_registry_sources.py` | Regeneration, determinism, divergence and hygiene tests | Tests only. |

The module never reads YAML or NDFC templates. `tools/` is part of the collection tree (and of the built tarball, as
`tools/gie_generate_binding_table.py` already was), so the source tests run both from a checkout and from the installed
collection that CI tests. No YAML is added to the module runtime path.

## Requirements

Python 3 and PyYAML. PyYAML is already installed with `ansible-core`; no other package or service is needed. Sources are read as
UTF-8, so the result does not depend on the locale.

## Commands (run from the repository root, or from anywhere: paths are relative to the script)

```bash
# Verify: regenerate in memory from the sources and compare byte for byte with the versioned table.
# Exit code 0 = identical. Exit code 1 = divergence (first differing lines are printed). Nothing is written.
python3 tools/gie_generate_binding_table.py --check

# Regenerate the versioned table from the sources.
python3 tools/gie_generate_binding_table.py --regenerate

# Both accept --slices DIR and --table FILE to work on a copy.
python3 tools/gie_generate_binding_table.py --check --slices /path/to/copy_of_slices
```

The explicit form `python3 tools/gie_generate_binding_table.py <slice.yaml> [...] <output.py>` is unchanged.

Slices are enumerated by file name, byte-wise, so the order does not depend on the shell or the locale. The compiled rows are
sorted by `(parent_template, parent_nvpair)`, and `PROVENANCE_SHA256` is the SHA-256 of the compiled rows (not of the YAML
bytes). Editing a comment in a slice therefore does not change the table, and any change to a compiled field does.

## Adding or editing a binding

1. Edit (or add) the row in the appropriate `tools/registry/slices/registry_slice_*.yaml`. A new binding must also be listed in
   `COMMITTED_BINDINGS` in the generator: only committed bindings are compiled, and a row that reuses a committed public
   `profile_key` on another parent is rejected on purpose. Every string row must declare `string_compare`.
2. Run `python3 tools/gie_generate_binding_table.py --regenerate`.
3. Review the diff of **both** the slice and `plugins/module_utils/gie_binding_table.py`. The table diff must contain exactly the
   change you meant (one key per line, so a changed field is one changed line).
4. Run `python3 tools/gie_generate_binding_table.py --check` and the unit tests (`tests/unit/modules/dcnm/test_gie_*.py`).
   `test_gie_patch_version_gate.py` pins the provenance hash on purpose: update it in the same commit, and say why.
5. Commit the slice and the regenerated table together. CI fails if they disagree.

## Compiled metadata and registry-only metadata

The compiled fields are the ones in `FIELDS` in the generator (`reset_wire`, `default_template`, `valid_values`, `mechanism`, ...).
Other keys in a slice (for example `removal_semantics`, and the comments) are **documentation of the contract and its provenance**
and are not compiled. In particular, how an omitted binding is withdrawn under `replaced` / `overridden` is decided by the engine
from the compiled `reset_wire` and `default_template` (`gie_withdrawal_action`), not by `removal_semantics`.

## Sanitization policy for the sources

Slices are published. They must not contain absolute or personal paths, references to private evidence files, lab serial numbers,
switch names or management addresses. Measurements are kept as provenance (what was measured, on which NDFC version, the outcome)
but the lab objects are replaced by neutral placeholders (`leaf-A`, `<lab-serial>`, `<lab-ip>`).
`test_gie_registry_sources.py` enforces this.
