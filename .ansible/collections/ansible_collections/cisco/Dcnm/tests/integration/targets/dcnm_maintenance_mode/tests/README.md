# Example dcnm_tests.yaml

## Description of integration tests in tests/integration/targets/dcnm_maintenance_mode/tests

Below is example contents for dcnm_tests.yaml to run integration tests assocated
with the ``dcnm_maintenance_mode`` module.

Replace nxos_username and nxos_password with those used in your local setup.

1. Run either of the 00_setup_fabrics_* tests first.
   - 00_setup_fabrics_1x_rw - Add leaf_1 and leaf_2 to a single fabric.
   - 00_setup_fabrics_2x_rw - Add leaf_1 to a VXLAN fabric and leaf_2 to a LAN Classic fabric.

2. Run one or more of the commented test cases.  These are numbered in pairs,
   with the odd-numbered cases assuming the switches are currently in "normal"
   mode, and the even-numbered cases assuming the switches are currently in
   "maintenance" mode.  Test case 09_merged_maintenance_mode_no_deploy is
   not paired with any other script.  It runs all "no_deploy" cases, since
   these take very little time to complete.


```yaml
---
- hosts: dcnm
  gather_facts: no
  connection: ansible.netcommon.httpapi

  vars:
    # testcase: 00_setup_fabrics_1x_rw
    # testcase: 00_setup_fabrics_2x_rw
    # testcase: 01_merged_maintenance_mode_deploy_no_wait_switch_level
    # testcase: 02_merged_normal_mode_deploy_no_wait_switch_level
    # testcase: 03_merged_maintenance_mode_deploy_no_wait_top_level
    # testcase: 04_merged_normal_mode_deploy_no_wait_top_level
    # testcase: 05_merged_maintenance_mode_deploy_wait_top_level
    # testcase: 06_merged_normal_mode_deploy_wait_top_level
    # testcase: 07_merged_maintenance_mode_deploy_wait_switch_level
    # testcase: 08_merged_normal_mode_deploy_wait_switch_level
    # testcase: 09_merged_maintenance_mode_no_deploy
    fabric_name_1: VXLAN_EVPN_Fabric
    fabric_type_1: VXLAN_EVPN
    fabric_name_2: VXLAN_EVPN_MSD_Fabric
    fabric_type_2: VXLAN_EVPN_MSD
    fabric_name_3: LAN_CLASSIC_Fabric
    fabric_type_3: LAN_CLASSIC
    fabric_name_4: IPFM_Fabric
    fabric_type_4: IPFM
    leaf_1: 192.168.1.2
    leaf_2: 192.168.1.3
    nxos_username: nxosUsername
    nxos_password: nxosPassword

  roles:
    - dcnm_maintenance_mode
```