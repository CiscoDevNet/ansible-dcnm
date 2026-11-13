# dcnm_interface unit tests

Tests for `plugins/modules/dcnm_interface.py`, the generic interface engine (`plugins/module_utils/gie_*.py`) and the
PVLAN helpers (`plugins/module_utils/interface_pvlan.py`). The original suite in `../test_dcnm_intf.py` stays where it is.

## Layout

| Path | Content |
|---|---|
| `test_binding_*.py` | Registered nvPair bindings: values, versions, withdrawal, resets, OSPF, SMU 017 fields, registry sources |
| `test_pvlan_*.py` | PVLAN on Ethernet, port-channels and vPCs: input, lifecycle, members, verification, mixed batches |
| `test_mode_*.py`, `test_svi_*.py` | Interface modes (peer link, uplink access, dot1q) and int_vlan SVI fields |
| `test_read_*.py`, `test_delete_*.py`, `test_no_log_and_redaction.py` | HAVE reads, read budget, deletion and redaction contracts |
| `test_helper_contracts.py` | Contracts of the helpers below |
| `helpers/` | Shared controllers, runners and builders; nothing in it is collected |
| `fixtures/` | Measured and synthetic captures, read through `helpers/fixture_cases.py` |

A merged suite keeps each former module as a section that starts with `# Formerly <module>.py` and that module's
description. A name that two former modules defined differently carries a short tag of its section, for example
`_l3po_ospf_have`.

## Execution boundaries

- Real `main()` with the controller doubled at `dcnm_send`: `helpers/binding_harness.py` (`run_configs`, `run`,
  `emit_real_result`) for bindings, `helpers/ethernet_controller.py` (`run`) and `helpers/vpc_controller.py` (`run_vpc`)
  for PVLAN. `helpers/module_runner.py` holds the `TestCase` base that patches only the external boundary. Each test
  builds a fresh controller; patches are owned by the case that starts them and are stopped by it.
- Real `main()` and real communication helpers (`dcnm_send`, `dcnm_get_bulk_api_support`) with the controller doubled
  at `Connection`, beneath those helpers: `transport_run()` in `test_pvlan_ethernet_current_policy.py`.
- Engine and helper functions without the module, for example `test_binding_engine.py` and `test_pvlan_vpc_units.py`.
- The HTTPAPI connection layer is tested in `tests/unit/plugins/httpapi/`, not here.

## Fixtures

Read a capture by its original name, never by path:

```python
from .helpers.fixture_cases import load_case, load_text

FX = load_case("pvlan_po_m1_measured")       # JSON capture, a fresh copy on every call
text = load_text("int_vlan_0efb09af_dhcp_excerpt")  # verbatim text
```

`helpers/fixture_cases.py` maps each capture to its bundle and documents the bundle format, including the
`$baseline` / `$set` / `$unset` form used for repeated snapshots. Comments refer to a capture as
`fixtures/<bundle>#<capture>`. Keep the `MEASURED`, `SIMULATED`, `SYNTHETIC` and `NOT LIVE TESTED` labels of a capture
next to its data, and keep expected values independent of the code under test.

## Running

```bash
pytest tests/unit/modules/dcnm/dcnm_interface
```

Run it from an `ansible_collections/cisco/dcnm` checkout, as the rest of the unit suite.
