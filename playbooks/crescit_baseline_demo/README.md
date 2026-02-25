# Crescit Baseline Demo (Existing Network State)

This folder defines the **existing configuration baseline** for `cisco_test_fabric1`.
Use it to seed NDFC + switches before evaluating PR scenario playbooks from:

- `playbooks/test_scenarios/`

## Why this exists

Crescit evaluates proposed playbook changes against current fabric state.
To demonstrate realistic impact analysis, this baseline creates an initial production-like state.

## Baseline objects created

- VRFs:
  - `PROD_VRF_Core`
  - `PROD_VRF_Shared`
- Networks:
  - `PROD_NET_CoreServices`
  - `PROD_NET_Operations`
  - `PROD_NET_SharedServices`
- VLANs:
  - `120` (`PROD_Core_VLAN120`)
  - `3901` (`MGMT_OOB_VLAN3901`)
  - `999` (`PROD_OldApp_VLAN999`)  <-- used by remove scenario tests

## Inventory

Edit `inventory.yaml` with your NDFC credentials and controller IP if needed.

## Apply baseline

```bash
cd /Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm
ansible-playbook -i playbooks/crescit_baseline_demo/inventory.yaml \
  playbooks/crescit_baseline_demo/00_apply_existing_baseline.yaml
```

## Verify baseline

```bash
ansible-playbook -i playbooks/crescit_baseline_demo/inventory.yaml \
  playbooks/crescit_baseline_demo/01_verify_baseline_state.yaml
```

## Notes

- `deploy_changes` defaults to `true` in `00_apply_existing_baseline.yaml`.
- Set `deploy_changes: false` if you only want staged changes in NDFC.
