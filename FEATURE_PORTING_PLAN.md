# Feature Porting Plan: dcnm_vrf.py → dcnm_vrf_v2.py

This document tracks features to be ported from `dcnm_vrf.py` (develop branch) into the new Pydantic-based `dcnm_vrf_v2.py` module.

## Status Legend

- ⬜ Not Started
- 🟡 In Progress
- ✅ Completed
- ❌ Not Applicable / Won't Implement

---

## High Priority Features

### 1. L3VNI Without VLAN Support ✅

**Issue:** #337, #435, #481, #508
**Commits:** 1ee37630, 050b1222, 9070a444
**Status:** COMPLETED (2025-11-12)
**Commit:** 954ce991

**Description:** Support for L3VNI without requiring a VLAN configuration.

**Changes Required in dcnm_vrf_v2.py:**

- [x] Add `l3vni_wo_vlan` parameter to module arguments
  - Type: bool
  - Default: Inherited from fabric level settings
  - Documentation: "Enable L3 VNI without VLAN"

- [x] Add fabric-level detection in `__init__()`:
  ```python
  self.fabric_nvpairs = self.fabric_data.get("nvPairs")
  self.fabric_l3vni_wo_vlan = False
  if self.fabric_nvpairs and self.fabric_nvpairs.get("ENABLE_L3VNI_NO_VLAN") == "true":
      self.fabric_l3vni_wo_vlan = True
  ```

- [x] Update documentation notes for:
  - `vrf_vlan_name`: "Not applicable to L3VNI w/o VLAN config"
  - `vrf_intf_desc`: "Not applicable to L3VNI w/o VLAN config"
  - `vrf_int_mtu`: "Not applicable to L3VNI w/o VLAN config"
  - `ipv6_linklocal_enable`: "Not applicable to L3VNI w/o VLAN config"

- [x] Update template config in `update_create_params()`:
  - Handled automatically via Pydantic model
  - Added `l3vni_wo_vlan` field to `VrfTemplateConfigV12` with alias `enableL3VniNoVlan`

- [x] Update `get_want_attach()` logic for vlan_id handling:
  ```python
  # Handle vlan_id based on l3vni_wo_vlan setting
  if validated_playbook_config_model.l3vni_wo_vlan:
      vlan_id: int = 0
  else:
      vlan_id: int = validated_playbook_config_model.vlan_id or 0
  ```

- [x] Pydantic models updated:
  - Added `l3vni_wo_vlan` to `PlaybookVrfModelV12`
  - Added `l3vni_wo_vlan` to `VrfTemplateConfigV12` with alias `enableL3VniNoVlan`

**Note:** The Pydantic-based implementation in dcnm_vrf_v2 handles template config automatically through models, so manual updates to `diff_for_create()`, `push_diff_create_update()`, and `get_have()` are not required. The models handle serialization/deserialization.

**Reference Code:** `plugins/modules/dcnm_vrf.py:147, 703-706, 1495, 1847-1852, 2246, 2556, 2856-2871`

---

### 2. Deploy Flag Handling Fix ✅

**Issue:** #491
**Commit:** 4aa56027
**Status:** COMPLETED (2025-11-12)
**Commit:** 5cf8e407

**Description:** VRFs should never deploy when the `deploy` flag is explicitly set to False.

**Changes Required in dcnm_vrf_v2.py:**

- [x] Update `get_diff_replace()` to filter VRFs with `deploy=False`:
  ```python
  modified_all_vrfs = copy.deepcopy(all_vrfs)
  for vrf in all_vrfs:
      want_vrf_data = find_dict_in_list_by_key_value(
          search=self.config, key="vrf_name", value=vrf
      )
      if want_vrf_data.get('deploy', True) is False:
          modified_all_vrfs.remove(vrf)

  if modified_all_vrfs:
      if not diff_deploy:
          diff_deploy.update({"vrfNames": ",".join(modified_all_vrfs)})
      else:
          vrfs = self.diff_deploy["vrfNames"] + "," + ",".join(modified_all_vrfs)
          diff_deploy.update({"vrfNames": vrfs})
  ```

- [x] Verified `diff_merge_attach()` already has correct logic:
  - Already checks `want_config_deploy is True` before adding VRFs to deploy list (lines 2548, 2551)
  - No changes needed - existing implementation is correct

**Reference Code:** `plugins/modules/dcnm_vrf.py:2098-2113, 2411-2426`

**Test Cases:**
- VRF with `deploy: false` should be created but not deployed
- VRF with `deploy: false` should not appear in deploy API call
- VRF without deploy flag should default to `deploy: true`

---

### 3. VRF Lite DOT1Q Auto-Allocation ⬜

**Issue:** #210, #467
**Commit:** c475d351

**Description:** Auto-allocate DOT1Q IDs for VRF Lite extensions when not explicitly provided.

**Changes Required in dcnm_vrf_v2.py:**

- [ ] Add new method `get_vrf_lite_dot1q_id()`:
  ```python
  def get_vrf_lite_dot1q_id(self, serial_number: str, vrf_name: str, interface: str) -> int:
      """
      # Summary

      Given a switch serial, vrf name and ifname, return the dot1q ID
      reserved for the vrf_lite extension on that switch.

      ## Raises

      Calls fail_json if DCNM fails to reserve the dot1q ID.
      """
      path = "/appcenter/cisco/ndfc/api/v1/lan-fabric"
      path += "/rest/resource-manager/reserve-id"
      verb = "POST"
      payload = {
          "scopeType": "DeviceInterface",
          "usageType": "TOP_DOWN_L3_DOT1Q",
          "serialNumber": serial_number,
          "ifName": interface,
          "allocatedTo": vrf_name
      }

      resp = dcnm_send(self.module, verb, path, json.dumps(payload))
      if resp.get("RETURN_CODE") != 200:
          # fail_json with error
      return resp.get("DATA")
  ```

- [ ] Update `update_vrf_attach_vrf_lite_extensions()` to auto-allocate:
  ```python
  if item["user"]["dot1q"]:
      nbr_dict["DOT1Q_ID"] = str(item["user"]["dot1q"])
  else:
      dot1q_vlan = self.get_vrf_lite_dot1q_id(
          serial_number,
          vrf_attach.get("vrfName"),
          nbr_dict["IF_NAME"]
      )
      if dot1q_vlan is not None:
          nbr_dict["DOT1Q_ID"] = str(dot1q_vlan)
      else:
          self.module.fail_json(msg="Failed to get dot1q ID...")
  ```

- [ ] Update `compare_properties()` to accept `skip_prop` parameter:
  ```python
  @staticmethod
  def compare_properties(dict1, dict2, property_list, skip_prop=None):
      for prop in property_list:
          if skip_prop and prop in skip_prop:
              continue
          if dict1.get(prop) != dict2.get(prop):
              return False
      return True
  ```

- [ ] Use skip_prop in `diff_for_attach_deploy()`:
  ```python
  skip_prop = []
  if not wlite["DOT1Q_ID"]:
      skip_prop.append("DOT1Q_ID")
  if not self.compare_properties(
      wlite, hlite, self.vrf_lite_properties, skip_prop
  ):
      found = False
  ```

**Reference Code:** `plugins/modules/dcnm_vrf.py:3160-3209, 3338-3354, 845-857, 970-977`

---

### 4. IPv6 Redistribute Route Map ⬜

**Issue:** #492
**Commit:** 349bbeb6

**Description:** Add support for IPv6 redistribute route-map configuration.

**Changes Required in dcnm_vrf_v2.py:**

- [ ] Add `v6_redist_direct_rmap` parameter to module arguments:
  - Type: str
  - Default: 'FABRIC-RMAP-REDIST-SUBNET'
  - Description: "IPv6 Redistribute Direct Route Map"

- [ ] Add to template config in `update_create_params()`:
  ```python
  template_conf.update(v6VrfRouteMap=vrf.get("v6_redist_direct_rmap", ""))
  ```

- [ ] Update `get_have()` template config:
  ```python
  t_conf.update(v6VrfRouteMap=json_to_dict.get("v6VrfRouteMap", ""))
  ```

- [ ] Update query/state methods to include `v6VrfRouteMap`

**Reference Code:** `plugins/modules/dcnm_vrf.py:122-127, 1491, 1628, 2249, 2550, 3050`

---

## Medium Priority Features

### 5. Empty InstanceValues Handling ⬜

**Issue:** #522
**Commit:** 3acfab8c

**Description:** Better handling of empty string vs None for `instanceValues` field.

**Changes Required in dcnm_vrf_v2.py:**

- [ ] Update condition in `diff_for_attach_deploy()`:
  ```python
  if (
      (want["instanceValues"] is not None and want["instanceValues"] != "")
      and
      (have["instanceValues"] is not None and have["instanceValues"] != "")
  ):
      # Process instanceValues
  ```

**Reference Code:** `plugins/modules/dcnm_vrf.py:901-906`

---

### 6. Network Attachment Check During Deletion ⬜

**Issue:** #456
**Commit:** 28c16fea

**Description:** Prevent VRF deletion if networks are still attached.

**Changes Required in dcnm_vrf_v2.py:**

- [ ] Add `GET_NET_VRF` path to `dcnm_vrf_paths`:
  ```python
  11: {
      "GET_NET_VRF": "/rest/resource-manager/fabrics/{}/networks?vrf-name={}"
  },
  12: {
      "GET_NET_VRF": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/networks?vrf-name={}"
  }
  ```

- [ ] Add network check in deletion flow:
  ```python
  path = self.paths["GET_NET_VRF"].format(self.fabric, vrf_name)
  resp = dcnm_send(self.module, "GET", path)

  network_list = search_nested_json(resp.get("DATA"), ["networkName"])
  if network_list:
      msg = f"VRF {vrf_name} has attached networks: {network_list}"
      self.module.fail_json(msg=msg)
  ```

- [ ] Import `search_nested_json` from `dcnm` module utils

**Reference Code:** `plugins/modules/dcnm_vrf.py:603, 611, 3926-3943`

**Note:** Requires `search_nested_json` utility function.

---

### 7. Orphaned Resources Cleanup Enhancement ⬜

**Issue:** Various cleanup issues
**Commit:** Multiple

**Description:** Improved cleanup of orphaned VRF resources across multiple pool types.

**Changes Required in dcnm_vrf_v2.py:**

- [ ] Update `release_orphaned_resources()` signature:
  ```python
  def release_orphaned_resources(self, vrf_del_list, is_rollback=False):
  ```

- [ ] Support multiple resource pools:
  ```python
  resource_pool = ["TOP_DOWN_VRF_VLAN", "TOP_DOWN_L3_DOT1Q"]
  for pool in resource_pool:
      req_path = path + f"pools/{pool}"
      resp = dcnm_send(self.module, "GET", req_path)
      # Process resources in pool
  ```

- [ ] Update filtering logic to use `vrf_del_list`:
  ```python
  for item in resp["DATA"]:
      if "entityName" not in item:
          continue
      if item["entityName"] not in vrf_del_list:
          continue
      # ... rest of logic
  ```

**Reference Code:** `plugins/modules/dcnm_vrf.py:3826-3885`

---

### 8. Attach State Logic Refinement ⬜

**Issue:** #522 (partial)
**Commit:** 3acfab8c (partial)

**Description:** Improved attach state determination logic.

**Changes Required in dcnm_vrf_v2.py:**

- [ ] Update attach state logic in `get_have()`:
  ```python
  # Old logic:
  # attach_state = not attach["lanAttachState"] == "NA"

  # New logic:
  attach_state = bool(attach.get("isLanAttached", False))
  deploy = attach_state
  ```

**Reference Code:** `plugins/modules/dcnm_vrf.py:1689-1690`

---

### 9. VRF Deletion Failure Fix ⬜

**Issue:** #451
**Commit:** faeae9b0

**Description:** Better error handling during VRF deletion failures.

**Changes Required in dcnm_vrf_v2.py:**

- [ ] Review and port error handling improvements from deletion flow
- [ ] Ensure proper response handling for "Fail" messages in NDFC responses

**Reference Code:** `plugins/modules/dcnm_vrf.py` - deletion methods

---

### 10. Response Data "Fail" Message Handling ⬜

**Issue:** #324, #457
**Commit:** 416fa1a9

**Description:** Proper handling of "Fail" messages in response DATA from NDFC.

**Changes Required in dcnm_vrf_v2.py:**

- [ ] Review response handling in all API interactions
- [ ] Check for "Fail" status in response DATA fields
- [ ] Raise appropriate errors with meaningful messages

**Reference Code:** `plugins/modules/dcnm_vrf.py` - response handling methods

---

## Low Priority / Nice-to-Have

### 11. Import Statement Cleanup ✅

**Status:** May already be handled in dcnm_vrf_v2.py

**Changes Required:**

- [ ] Verify imports are properly formatted
- [ ] Remove unused imports
- [ ] Use proper import from `find_dict_in_list_by_key_value` when needed

**Reference Code:** `plugins/modules/dcnm_vrf.py:589-591`

---

## Implementation Notes

### Utility Functions Needed

These utility functions should be available in module_utils or imported from dcnm:

1. ✅ `find_dict_in_list_by_key_value()` - Available in dcnm
2. ✅ `search_nested_json()` - Available in dcnm
3. ⬜ May need Pydantic equivalents for some operations

### Pydantic Model Updates

For each feature, consider whether Pydantic models need updates:

- [ ] Create/update models for L3VNI without VLAN
- [ ] Add validators for IPv6 route-map
- [ ] Add validators for DOT1Q ID handling
- [ ] Model for VRF Lite extensions

### Testing Requirements

For each ported feature:

- [ ] Unit tests mirroring dcnm_vrf tests
- [ ] Integration tests where applicable
- [ ] Update fixture files
- [ ] Test rollback scenarios

### Documentation Updates

- [ ] Update module documentation with new parameters
- [ ] Update EXAMPLES section
- [ ] Update README if needed
- [ ] Add notes about feature parity with dcnm_vrf.py

---

## Progress Tracking

Use this section to track overall progress:

- **Total Features Identified:** 11
- **Completed:** 2
- **In Progress:** 0
- **Not Started:** 9
- **Won't Implement:** 0

### Completed Features

1. ✅ L3VNI Without VLAN Support (2025-11-12) - Commit 954ce991
2. ✅ Deploy Flag Handling Fix (2025-11-12) - Commit 5cf8e407

---

## Next Steps

1. ✅ Replace dcnm_vrf.py with develop version
2. ⬜ Review dcnm_vrf_v2.py current architecture
3. ⬜ Prioritize feature porting based on user needs
4. ⬜ Start with Feature #1 (L3VNI without VLAN)
5. ⬜ Create unit tests for each ported feature
6. ⬜ Update integration tests

---

## Reference Commits in Develop Branch

| Commit | Issue | Description |
|--------|-------|-------------|
| 9070a444 | #505, #508 | Fix for L3VNI W/O VLAN_ID generation |
| 3acfab8c | #522 | Fixing handling of '' InstanceValues |
| 4aa56027 | #491 | VRFs should never deploy when deploy flag is False |
| c475d351 | #210, #467 | Fix for VRF_Lite Issue & DOT1Q_ID Auto Allocation |
| 349bbeb6 | #492 | Add support for IPv6 redistribute route-map |
| 050b1222 | #481 | DCNM_VRF: L3 VNI W/O VLAN IT Tests & Documentation |
| faeae9b0 | #451 | dcnm_vrf: VRF Deletion Failure Fix |
| 28c16fea | #456 | dcnm_vrf: raises error if networks attached during deletion |
| 416fa1a9 | #324, #457 | Handling "Fail" messages in Response Data from NDFC |
| 1ee37630 | #337, #435 | Add L3VNI w/o VLAN option support |

---

## Questions / Blockers

Add any questions or blockers encountered during porting:

1. **Q:** Does dcnm_vrf_v2.py use the same API paths structure?
   **A:** [To be determined]

2. **Q:** How are Pydantic models structured for VRF attachments?
   **A:** [To be determined]

3. **Q:** Should we maintain 100% feature parity or can we skip some legacy features?
   **A:** [To be determined based on requirements]

---

Last Updated: 2025-11-12
