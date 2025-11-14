#!/usr/bin/env python3
import re

# Files and line numbers that need fixing
violations = {
    'tests/integration/targets/dcnm_bootflash/tests/dcnm_bootflash_deleted_specific.yaml': [176],
    'tests/integration/targets/dcnm_bootflash/tests/dcnm_bootflash_deleted_wildcard.yaml': [176],
    'tests/integration/targets/dcnm_bootflash/tests/dcnm_bootflash_query_specific.yaml': [157, 196],
    'tests/integration/targets/dcnm_bootflash/tests/dcnm_bootflash_query_wildcard.yaml': [157, 196],
    'tests/integration/targets/dcnm_fabric/tests/dcnm_fabric_merged_save_deploy.yaml': [394, 404],
    'tests/integration/targets/dcnm_fabric/tests/dcnm_fabric_replaced_save_deploy.yaml': [362, 552],
    'tests/integration/targets/dcnm_image_upgrade/tests/deleted.yaml': [164, 251],
    'tests/integration/targets/dcnm_image_upgrade/tests/deleted_1x_switch.yaml': [150],
    'tests/integration/targets/dcnm_image_upgrade/tests/query.yaml': [204, 395],
    'tests/integration/targets/dcnm_inventory/tests/dcnm/rma.yaml': [39, 40],
    'tests/integration/targets/dcnm_policy/tests/dcnm/dcnm_policy_merge.yaml': [479, 480],
    'tests/integration/targets/dcnm_resource_manager/tests/dcnm/dcnm_res_manager_query.yaml': [237],
    'tests/integration/targets/dcnm_vrf/tests/dcnm/self-contained-tests/scale.yaml': [61],
    'tests/integration/targets/prepare_dcnm_intf/tasks/main.yaml': [213, 215, 223, 225],
}

for filepath, lines in violations.items():
    try:
        with open(filepath, 'r') as f:
            content = f.readlines()
        
        modified = False
        for line_num in sorted(lines, reverse=True):  # Process from bottom to top
            idx = line_num - 1
            if idx < len(content):
                line = content[idx]
                # Check if line is too long and contains a comment or string
                if len(line.rstrip()) > 160:
                    # Try to break at a logical point
                    # For lines with "that:" assertions, break after "that:"
                    if 'that:' in line and len(line) > 160:
                        indent = len(line) - len(line.lstrip())
                        # Keep the line as is for now - ansible handles multi-line asserts
                        # We can use YAML folded scalars (>-) if needed
                        pass
                    # For lines with long strings, we can use YAML line continuation
                    # For now, just flag them
                    print(f"Line {line_num} in {filepath} is {len(line.rstrip())} chars (needs manual review)")
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

print("\nNote: Line-length violations often require manual review.")
print("Most are assertion messages or config strings that are intentionally long.")
