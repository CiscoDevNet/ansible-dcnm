# Interface binding registry: sources and regeneration

`plugins/module_utils/gie_binding_table.py` is a **generated** file ("DO NOT EDIT"). Its canonical source is the set of
registry sources in `tools/registry/slices/` (`registry_slice_*.yaml`), one file per feature family. The generator is
`tools/gie_generate_binding_table.py`. Everything needed to regenerate the table is in this repository.

## What is what

| Path | Role | Used at runtime by the module? |
|------|------|--------------------------------|
| `plugins/module_utils/gie_binding_table.py` | Compiled, versioned table (`BINDING_TABLE`, `PROVENANCE_SHA256`) | Yes. This is the only artifact the module imports. |
| `tools/registry/slices/*.yaml` | Canonical registry sources (eight family files) | No. Development tooling. |
| `tools/gie_generate_binding_table.py` | Deterministic generator and `--check` | No. Development tooling. |
| `tests/unit/modules/dcnm/dcnm_interface/test_binding_registry_sources.py` | Regeneration, determinism, divergence and hygiene tests | Tests only. |

The module never reads YAML or NDFC templates. `tools/` is part of the collection tree (and of the built tarball, as
`tools/gie_generate_binding_table.py` already was), so the source tests run both from a checkout and from the installed
collection that CI tests. No YAML is added to the module runtime path.

## Requirements

Python 3 and PyYAML. PyYAML is already installed with `ansible-core`; no other package or service is needed. Sources are read as
UTF-8, so the result does not depend on the locale.

## Source layout

The sources are grouped by feature family. A file holds every binding of its family, whatever parent template it is declared
on. Within a file, the rows keep the order of the original lots, and each lot's header comment is kept as a section comment.

| File | Family | Rows |
|------|--------|-----:|
| `registry_slice_eigrp.yaml` | EIGRP on the routed, subinterface, SVI and loopback parents | 52 |
| `registry_slice_hsrp_ipv6_nd.yaml` | HSRP, IPv6 and neighbor-discovery/redirect fields on the overlay parents | 17 |
| `registry_slice_interface_common.yaml` | Fields shared by Ethernet, routed, loopback and SVI parents: LLDP, QoS, ACL, flow control, dampening, ARP and related options | 40 |
| `registry_slice_macsec.yaml` | MACsec on the routed parent | 4 |
| `registry_slice_multicast_bfd.yaml` | PIM and BFD parents | 22 |
| `registry_slice_ospf.yaml` | OSPF parents, including the routed port-channel | 96 |
| `registry_slice_port_channel_vpc.yaml` | Port-channel, vPC, peer-link and uplink parents | 61 |
| `registry_slice_pvlan.yaml` | Private VLAN companion fields | 12 |

The registry used to be split into 42 files, one per development lot (`registry_slice_0b_22_eigrp.yaml` and so on). Comments in
the sources, in the generator and in the tests still cite those lot names, such as "slice 0b_22". Each lot is now a section of
a family file, introduced by a `# ==== Source lot ... ====` comment, so a lot name can be found with a text search. A lot whose
rows belong to several families keeps its header in the family that holds most of its rows. The other families point to it.

| Original lot | Family files (rows) |
|--------------|---------------------|
| `0b` | `registry_slice_interface_common.yaml` (2), `registry_slice_ospf.yaml` (1) |
| `0b_11` | `registry_slice_interface_common.yaml` (2) |
| `0b_12` | `registry_slice_interface_common.yaml` (2) |
| `0b_13` | `registry_slice_interface_common.yaml` (4) |
| `0b_14` | `registry_slice_port_channel_vpc.yaml` (12) |
| `0b_15` | `registry_slice_port_channel_vpc.yaml` (11) |
| `0b_16` | `registry_slice_interface_common.yaml` (4), `registry_slice_multicast_bfd.yaml` (1) |
| `0b_17` | `registry_slice_interface_common.yaml` (6), `registry_slice_port_channel_vpc.yaml` (10) |
| `0b_18_ospf` | `registry_slice_ospf.yaml` (4) |
| `0b_19_ospf_routed_lot2` | `registry_slice_ospf.yaml` (9) |
| `0b_20_ospf_int_subif` | `registry_slice_ospf.yaml` (14) |
| `0b_20_ospf_int_vlan` | `registry_slice_ospf.yaml` (14) |
| `0b_21_ospf_auth` | `registry_slice_ospf.yaml` (15) |
| `0b_22_eigrp` | `registry_slice_eigrp.yaml` (39) |
| `0b_23_ospf_int_loopback` | `registry_slice_ospf.yaml` (19) |
| `0b_24_bfd` | `registry_slice_multicast_bfd.yaml` (1) |
| `0b_25_eigrp_int_loopback` | `registry_slice_eigrp.yaml` (8) |
| `0b_26_hsrp_int_vlan` | `registry_slice_hsrp_ipv6_nd.yaml` (3) |
| `0b_27_hsrp_ipv6_int_vlan` | `registry_slice_hsrp_ipv6_nd.yaml` (2) |
| `0b_28_redirects_nd` | `registry_slice_hsrp_ipv6_nd.yaml` (9) |
| `0b_3` | `registry_slice_interface_common.yaml` (3) |
| `0b_31_pim` | `registry_slice_multicast_bfd.yaml` (8) |
| `0b_32_ipv6_link_local` | `registry_slice_hsrp_ipv6_nd.yaml` (3) |
| `0b_33_macsec` | `registry_slice_macsec.yaml` (4) |
| `0b_34_tanda2` | `registry_slice_interface_common.yaml` (2), `registry_slice_port_channel_vpc.yaml` (1) |
| `0b_36_vpc_dot1q` | `registry_slice_port_channel_vpc.yaml` (6) |
| `0b_37_smu017_batch1` | `registry_slice_interface_common.yaml` (3), `registry_slice_ospf.yaml` (1), `registry_slice_multicast_bfd.yaml` (1) |
| `0b_38_smu017_loopback_eigrp` | `registry_slice_eigrp.yaml` (5) |
| `0b_39_smu017_l3po_pim_bfd` | `registry_slice_multicast_bfd.yaml` (1) |
| `0b_4` | `registry_slice_multicast_bfd.yaml` (4) |
| `0b_40_smu017_l3po_ospf` | `registry_slice_ospf.yaml` (19) |
| `0b_41_l3po_pim` | `registry_slice_multicast_bfd.yaml` (2) |
| `0b_5` | `registry_slice_multicast_bfd.yaml` (4) |
| `0b_6` | `registry_slice_interface_common.yaml` (7) |
| `0b_7` | `registry_slice_interface_common.yaml` (1), `registry_slice_port_channel_vpc.yaml` (1) |
| `0b_8` | `registry_slice_interface_common.yaml` (2) |
| `0b_9` | `registry_slice_interface_common.yaml` (2), `registry_slice_port_channel_vpc.yaml` (3) |
| `c1_pvlan_companions` | `registry_slice_pvlan.yaml` (11) |
| `iq1_vpc_pvlan_qos_stats` | `registry_slice_pvlan.yaml` (1) |
| `pl1_peer_link` | `registry_slice_port_channel_vpc.yaml` (4) |
| `rs1_po_link_transmit_reset_skip` | `registry_slice_port_channel_vpc.yaml` (1) |
| `ul1_uplink_access` | `registry_slice_port_channel_vpc.yaml` (12) |

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

1. Edit (or add) the row in the file of its feature family under `tools/registry/slices/`. A new binding must also be listed in
   `COMMITTED_BINDINGS` in the generator: only committed bindings are compiled, and a row that reuses a committed public
   `profile_key` on another parent is rejected on purpose. Every string row must declare `string_compare`.
2. Run `python3 tools/gie_generate_binding_table.py --regenerate`.
3. Review the diff of **both** the slice and `plugins/module_utils/gie_binding_table.py`. The table diff must contain exactly the
   change you meant (one key per line, so a changed field is one changed line).
4. Run `python3 tools/gie_generate_binding_table.py --check` and the unit tests (`tests/unit/modules/dcnm/dcnm_interface/test_binding_*.py`).
   `test_binding_versions.py` pins the provenance hash on purpose: update it in the same commit, and say why.
5. Commit the slice and the regenerated table together. CI fails if they disagree.

## Compiled metadata and registry-only metadata

The compiled fields are the ones in `FIELDS` in the generator (`reset_wire`, `default_template`, `valid_values`, `mechanism`, ...).
Other keys in a slice (for example `removal_semantics`, and the comments) are **documentation of the contract and its provenance**
and are not compiled. In particular, how an omitted binding is withdrawn under `replaced` / `overridden` is decided by the engine
from the compiled `reset_wire` and `default_template` (`gie_withdrawal_action`), not by `removal_semantics`.

## Sanitization policy for the sources

Slices are published. They must not contain absolute or personal paths, references to private evidence files, lab serial numbers,
switch names or management addresses. Measurements are kept as provenance (what was measured, on which NDFC version, the outcome)
but the lab objects are replaced by neutral placeholders (`leaf-A`, `<lab-serial>`, `<lab-ip>`, `<tag>` for routing-process tags).
`test_binding_registry_sources.py` enforces this.
