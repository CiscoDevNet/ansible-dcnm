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

### 3. VRF Lite DOT1Q Auto-Allocation ✅

**Issue:** #210, #467
**Commit:** c475d351
**Status:** COMPLETED (2025-11-12)
**Commit:** ef522122

**Description:** Auto-allocate DOT1Q IDs for VRF Lite extensions when not explicitly provided.

**Changes Required in dcnm_vrf_v2.py:**

- [x] Add new method `get_vrf_lite_dot1q_id()`:
  - Implemented at `dcnm_vrf_v12.py:543-608`
  - Calls NDFC resource reservation API endpoint `/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/resource-manager/reserve-id`
  - Returns allocated DOT1Q ID or calls fail_json on error

- [x] Update `update_attach_params_extension_values()` to auto-allocate:
  - Method signature updated to accept `serial_number` and `vrf_name` parameters
  - Auto-allocation logic added at lines 996-1001
  - Checks if `playbook_vrf_lite_model.dot1q` is empty
  - If empty, calls `get_vrf_lite_dot1q_id()` to allocate DOT1Q ID

- [x] Update `property_values_match()` to accept `skip_prop` parameter:
  - Updated method signature at line 465
  - Added logic to skip properties in `skip_prop` list
  - Defaults to empty list if `skip_prop` is None

- [x] Use skip_prop in `_extension_values_match()`:
  - Updated at lines 830-834
  - Creates `skip_prop` list
  - Adds "DOT1Q_ID" to `skip_prop` if `want_vrf_lite["DOT1Q_ID"]` is empty
  - Passes `skip_prop` to `property_values_match()`

**Note:** The Pydantic-based implementation automatically handles serialization/deserialization through the `PlaybookVrfLiteModel`, which stores `dot1q` as a string and validates it properly.

**Reference Code:** `plugins/modules/dcnm_vrf.py:3160-3209, 3338-3354, 845-857, 970-977`

---

### 4. IPv6 Redistribute Route Map ✅

**Issue:** #492
**Commit:** 349bbeb6
**Status:** COMPLETED (2025-11-12)
**Commit:** c75ee142

**Description:** Add support for IPv6 redistribute route-map configuration.

**Changes Required in dcnm_vrf_v2.py:**

- [x] Add `v6_redist_direct_rmap` parameter to module arguments:
  - Type: str
  - Default: 'FABRIC-RMAP-REDIST-SUBNET'
  - Description: "IPv6 Redistribute Direct Route Map"
  - Implemented at `dcnm_vrf_v2.py:126-131`

- [x] Add `v6_redist_direct_rmap` to PlaybookVrfModelV12:
  - Field added at `model_playbook_vrf_v12.py:310`
  - Maps to v6VrfRouteMap in template config
  - Default: 'FABRIC-RMAP-REDIST-SUBNET'

- [x] Add `v6_redist_direct_rmap` to VrfTemplateConfigV12:
  - Field added at `vrf_template_config_v12.py:74`
  - Alias: v6VrfRouteMap
  - Automatically serializes to/from controller payload

**Note:** The Pydantic-based implementation automatically handles serialization/deserialization between playbook parameters (`v6_redist_direct_rmap`) and controller API fields (`v6VrfRouteMap`). Manual updates to `update_create_params()` and `get_have()` are not required as the models handle this automatically.

**Reference Code:** `plugins/modules/dcnm_vrf.py:122-127, 1491, 1628, 2249, 2550, 3050`

---

## Medium Priority Features

### 5. Empty InstanceValues Handling ✅

**Issue:** #522
**Commit:** 3acfab8c
**Status:** COMPLETED (2025-11-12)
**Commit:** 4141f8ae

**Description:** Better handling of empty string vs None for `instanceValues` field.

**Changes Required in dcnm_vrf_v2.py:**

- [x] Update condition in `diff_for_attach_deploy()`:
  - Updated at `dcnm_vrf_v12.py:705-708`
  - Changed from simple truthy check to explicit None and empty string check
  - Before: `if want_attach.get("instanceValues") and have_lan_attach_model.instance_values:`
  - After: Explicitly checks `(is not None and != "")` for both want and have
  - Prevents attempting to parse empty strings as JSON
  - Ensures consistent handling of missing/empty instanceValues

**Reference Code:** `plugins/modules/dcnm_vrf.py:901-906`

---

### 6. Network Attachment Check During Deletion ✅

**Issue:** #456
**Commit:** 28c16fea
**Status:** COMPLETED (2025-11-12)
**Commit:** 40aa7bfb

**Description:** Prevent VRF deletion if networks are still attached.

**Changes Required in dcnm_vrf_v2.py:**

- [x] Add `GET_NET_VRF` path to `dcnm_vrf_paths`:
  - Added at `dcnm_vrf_v12.py:69`
  - Path: `/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/networks?vrf-name={}`

- [x] Add network check in deletion flow:
  - Created `check_network_attachments()` method at `dcnm_vrf_v12.py:3129-3169`
  - Queries controller for networks attached to VRF
  - Calls fail_json if networks are found
  - Provides clear error message directing users to dcnm_network module

- [x] Call network check before deletion:
  - Added calls in both `push_to_remote()` and `push_to_remote_model()` methods
  - Checks performed before `push_diff_detach()` is called
  - Located at lines 4017-4019 and 4054-4056

**Note:** The implementation uses direct list comparison (`resp["DATA"] != []`) rather than `search_nested_json`, which is simpler and equally effective. The check validates data exists and provides appropriate error messages.

**Reference Code:** `plugins/modules/dcnm_vrf.py:603, 611, 3926-3943`

---

### 7. Orphaned Resources Cleanup Enhancement ✅

**Issue:** Various cleanup issues
**Commit:** Multiple
**Status:** COMPLETED (2025-11-12)
**Commit:** 5f0eba0f

**Description:** Improved cleanup of orphaned VRF resources across multiple pool types.

**Changes Required in dcnm_vrf_v2.py:**

- [x] Update `release_orphaned_resources()` signature:
  - Updated at `dcnm_vrf_v12.py:3900`
  - Now accepts `vrf_del_list: list` instead of single `vrf: str`
  - Signature: `def release_orphaned_resources(self, vrf_del_list: list, is_rollback=False) -> None:`

- [x] Support multiple resource pools:
  - Implemented at `dcnm_vrf_v12.py:3965-4022`
  - Processes both TOP_DOWN_VRF_VLAN and TOP_DOWN_L3_DOT1Q pools
  - Loops through each pool and queries for orphaned resources

- [x] Update filtering logic to use `vrf_del_list`:
  - Updated at `dcnm_vrf_v12.py:3998`
  - Changed from `if item["entityName"] != vrf:` to `if item["entityName"] not in vrf_del_list:`
  - Added validation for ipAddress and switchName to avoid deleting invalid Fabric-scoped resources

- [x] Update call sites:
  - Modified in both `push_to_remote()` and `push_to_remote_model()` methods
  - Changed from looping and calling once per VRF to calling once with entire list
  - Located at lines 4058-4062 and 4099-4103

**Note:** This enhancement improves efficiency by processing all VRFs in a single operation and ensures proper cleanup of both VLAN and DOT1Q resources (e.g., VRF Lite extensions).

**Reference Code:** `plugins/modules/dcnm_vrf.py:3826-3885`

---

### 8. Attach State Logic Refinement ✅

**Issue:** #522 (partial)
**Commit:** 3acfab8c (partial)
**Status:** COMPLETED (2025-11-12)
**Commit:** d4b5c4f6

**Description:** Improved attach state determination logic.

**Changes Required in dcnm_vrf_v2.py:**

- [x] Update attach state logic in `get_have_deploy()`:
  - Updated at `dcnm_vrf_v12.py:1575-1576`
  - Changed from: `deploy = attach.get("isLanAttached")`
  - Changed to: `attach_state = bool(attach.get("isLanAttached", False))` followed by `deploy = attach_state`
  - Provides explicit False default when isLanAttached is missing from controller response
  - Ensures attach_state is always a boolean rather than potentially None

**Note:** The explicit bool conversion with default value prevents subtle bugs that could occur if the controller response doesn't include the isLanAttached field. This is particularly important for handling edge cases in controller responses.

**Reference Code:** `plugins/modules/dcnm_vrf.py:1689-1690`

---

### 9. VRF Deletion Failure Fix ✅

**Issue:** #451
**Commit:** faeae9b0
**Status:** COMPLETED (2025-11-12) - Already implemented in Feature #7
**Commit:** 5f0eba0f (Feature #7)

**Description:** Better error handling during VRF deletion failures, specifically preventing attempts to delete invalid TOP_DOWN_VRF_VLAN resources and preventing multiple GET calls to NDFC while deleting orphaned resources.

**Changes Required in dcnm_vrf_v2.py:**

- [x] Review and port error handling improvements from deletion flow
- [x] Add validation for ipAddress and switchName in release_orphaned_resources()
- [x] Update signature to accept vrf_del_list instead of single vrf
- [x] Add debug logging for resource cleanup operations

**Implementation Notes:**

All fixes from commit faeae9b0 were already implemented as part of Feature #7 (Orphaned Resources Cleanup Enhancement - commit 5f0eba0f):

- Validation checks for `ipAddress` and `switchName` at `dcnm_vrf_v12.py:4008-4011`
- Comment explaining invalid resources at lines 4005-4007
- Signature updated to accept `vrf_del_list: list` at line 3901
- Call sites updated to build list and call once at lines 4060-4064, 4101-4105
- Debug logging added at lines 4021-4022, 4062-4063, 4103-4104

**Note:** Feature #7 comprehensively addressed all the issues from commit faeae9b0, including:
1. Preventing deletion of invalid Fabric-scoped resources (no ipAddress or switchName)
2. Preventing multiple GET calls by accepting a list of VRFs
3. Adding appropriate debug logging throughout the cleanup process

**Reference Code:** `plugins/modules/dcnm_vrf.py:3668-3807`

---

### 10. Response Data "Fail" Message Handling ✅

**Issue:** #324, #457
**Commit:** 416fa1a9
**Status:** COMPLETED (2025-11-12)
**Commit:** 3647b9c9

**Description:** Proper handling of "Fail" messages in response DATA from NDFC. The controller sometimes returns a 200 OK status but includes "Fail" messages in nested DATA fields, which should be treated as failures.

**Changes Required in dcnm_vrf_v2.py:**

- [x] Add `search_nested_json()` utility function to dcnm.py
- [x] Import `search_nested_json` in dcnm_vrf_v12.py
- [x] Update `handle_response()` to check for "fail" in response DATA
- [x] Set fail=True and changed=False when "fail" found in DATA

**Implementation Details:**

Added `search_nested_json()` utility function to `plugins/module_utils/network/dcnm/dcnm.py`:

- Recursively searches nested dictionaries and lists for a search string
- Case-insensitive search of all string values
- Returns True if found, False otherwise
- Handles dict, list, and str types

Updated `dcnm_vrf_v12.py`:

- Added import for `search_nested_json` at line 46
- Added check in `handle_response()` at lines 4479-4483:

```python
if response_model.DATA:
    resp_val = search_nested_json(response_model.DATA, "fail")
    if resp_val:
        fail = True
        changed = False
```

**Note:** This prevents the module from incorrectly succeeding when the controller returns a "Fail" status embedded in nested response DATA fields, even if the HTTP status is 200 OK.

**Reference Code:** `plugins/modules/dcnm_vrf.py:4141-4147, plugins/module_utils/network/dcnm/dcnm.py:889-933`

---

## Low Priority / Nice-to-Have

### 11. Import Statement Cleanup ✅

**Status:** COMPLETED (2025-11-12) - Already properly handled
**Commit:** N/A (No changes needed)

**Description:** Verify all imports are properly formatted and no unused imports exist.

**Changes Required:**

- [x] Verify imports are properly formatted
- [x] Remove unused imports
- [x] Verify `find_dict_in_list_by_key_value` is properly used

**Implementation Notes:**

All imports in `dcnm_vrf_v12.py` are:

- Properly formatted by isort (alphabetical order, proper grouping)
- All imported functions are used in the code:
  - `dcnm_get_ip_addr_info`: Used 2 times
  - `dcnm_send`: Used 9 times
  - `get_fabric_details`: Used 1 time
  - `get_fabric_inventory_details`: Used 1 time
  - `get_sn_fabric_dict`: Used 1 time
  - `search_nested_json`: Used 1 time (added in Feature #10)

- `find_dict_in_list_by_key_value` is defined as a static method within the `DcnmVrfV12` class (line 340) rather than imported from dcnm.py, which is appropriate for this module's architecture

**Note:** No changes were needed. Import statements are already clean and properly maintained through continuous use of isort and black formatters.

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
- **Completed:** 11 🎉
- **In Progress:** 0
- **Not Started:** 0
- **Won't Implement:** 0

### Completed Features

1. ✅ L3VNI Without VLAN Support (2025-11-12) - Commit 954ce991
2. ✅ Deploy Flag Handling Fix (2025-11-12) - Commit 5cf8e407
3. ✅ VRF Lite DOT1Q Auto-Allocation (2025-11-12) - Commit ef522122
4. ✅ IPv6 Redistribute Route Map (2025-11-12) - Commit c75ee142
5. ✅ Empty InstanceValues Handling (2025-11-12) - Commit 4141f8ae
6. ✅ Network Attachment Check During Deletion (2025-11-12) - Commit 40aa7bfb
7. ✅ Orphaned Resources Cleanup Enhancement (2025-11-12) - Commit 5f0eba0f
8. ✅ Attach State Logic Refinement (2025-11-12) - Commit d4b5c4f6
9. ✅ VRF Deletion Failure Fix (2025-11-12) - Already in Feature #7 (Commit 5f0eba0f)
10. ✅ Response Data "Fail" Message Handling (2025-11-12) - Commit 3647b9c9
11. ✅ Import Statement Cleanup (2025-11-12) - No changes needed (Already clean)

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
