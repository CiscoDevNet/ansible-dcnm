#!/usr/bin/env python3
"""
Script to fix common YAML indentation issues reported by ansible-lint.
Handles patterns like:
- Wrong indentation: expected X but found Y
- Fixes assert blocks, list items, and nested structures
"""

import re
import sys
from pathlib import Path


def fix_indentation_issues(file_path):
    """Fix indentation issues in a YAML file."""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False
    
    modified = False
    new_lines = []
    
    for i, line in enumerate(lines):
        new_line = line
        
        # Fix pattern: 8 spaces when 10 expected (assert blocks after "that:")
        if i > 0 and lines[i-1].strip().startswith('that:'):
            # Check if current line has 8 spaces (should be 10)
            if re.match(r'^        [^ ]', line):
                new_line = '  ' + line
                modified = True
        
        # Fix pattern: 10 spaces when 8 expected (list items under tasks)
        # This is for lines that have 10 spaces but should have 8
        elif re.match(r'^          - ', line):
            # Check context - if parent is at 6 spaces, this should be 8
            if i > 0:
                prev_line = lines[i-1].strip()
                # If previous line is a key at appropriate level, adjust
                if prev_line.endswith(':') or prev_line == '':
                    # Find the actual context
                    j = i - 1
                    while j >= 0 and (lines[j].strip() == '' or lines[j].strip().startswith('#')):
                        j -= 1
                    if j >= 0 and re.match(r'^      [^ ]', lines[j]):
                        new_line = line[2:]  # Remove 2 spaces
                        modified = True
        
        # Fix pattern: 4 spaces when 6 expected (assert under "that:")
        elif i > 0 and lines[i-1].strip() == 'that:':
            if re.match(r'^    [^ ]', line):
                new_line = '  ' + line
                modified = True
        
        # Fix pattern: 6 spaces when 4 expected (misaligned list items)
        elif re.match(r'^      - ', line):
            # Check if this should be at 4 spaces instead
            if i > 0:
                j = i - 1
                while j >= 0 and lines[j].strip() == '':
                    j -= 1
                if j >= 0 and re.match(r'^  [^ ]', lines[j]):
                    new_line = line[2:]  # Remove 2 spaces
                    modified = True
        
        # Fix pattern: 6 spaces when 8 expected (nested properties)
        elif re.match(r'^      [a-zA-Z_]', line) and ':' in line:
            if i > 0:
                j = i - 1
                while j >= 0 and lines[j].strip() == '':
                    j -= 1
                if j >= 0 and re.match(r'^        - ', lines[j]):
                    new_line = '  ' + line
                    modified = True
        
        new_lines.append(new_line)
    
    if modified:
        try:
            with open(file_path, 'w') as f:
                f.writelines(new_lines)
            return True
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
            return False
    
    return False


def main():
    """Main function to process files."""
    # List of files with indentation issues from ansible-lint output
    files_to_fix = [
        # dcnm_bootflash files
        "tests/integration/targets/dcnm_bootflash/tests/dcnm_bootflash_deleted_specific.yaml",
        "tests/integration/targets/dcnm_bootflash/tests/dcnm_bootflash_deleted_wildcard.yaml",
        "tests/integration/targets/dcnm_bootflash/tests/dcnm_bootflash_query_specific.yaml",
        "tests/integration/targets/dcnm_bootflash/tests/dcnm_bootflash_query_wildcard.yaml",
        
        # dcnm_image_policy files
        "tests/integration/targets/dcnm_image_policy/tests/dcnm_image_policy_deleted.yaml",
        "tests/integration/targets/dcnm_image_policy/tests/dcnm_image_policy_deleted_all_policies.yaml",
        "tests/integration/targets/dcnm_image_policy/tests/dcnm_image_policy_merged.yaml",
        "tests/integration/targets/dcnm_image_policy/tests/dcnm_image_policy_overridden.yaml",
        "tests/integration/targets/dcnm_image_policy/tests/dcnm_image_policy_query.yaml",
        "tests/integration/targets/dcnm_image_policy/tests/dcnm_image_policy_replaced.yaml",
        
        # dcnm_image_upgrade files
        "tests/integration/targets/dcnm_image_upgrade/tests/deleted_1x_switch.yaml",
        
        # dcnm_image_upload files
        "tests/integration/targets/dcnm_image_upload/tests/dcnm/dcnm_image_upload_delete.yaml",
        "tests/integration/targets/dcnm_image_upload/tests/dcnm/dcnm_image_upload_merge.yaml",
        "tests/integration/targets/dcnm_image_upload/tests/dcnm/dcnm_image_upload_override.yaml",
        "tests/integration/targets/dcnm_image_upload/tests/dcnm/dcnm_image_upload_query.yaml",
        
        # dcnm_interface files (many files with indentation issues)
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_aa_fex_delete.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_aa_fex_merge.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_aa_fex_override.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_aa_fex_replace.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_delete_deploy.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_eth_delete.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_intf_sanity.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_lo_delete.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_lo_fabric.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_lo_mpls.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_lo_override.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_pc_delete.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_pc_merge.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_pc_override.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_pc_replace.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_st_fex_delete.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_st_fex_merge.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_st_fex_override.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_st_fex_replace.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_sub_delete.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_sub_merge.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_sub_override.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_sub_replace.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_svi_delete.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_svi_merge.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_svi_override.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_svi_query.yaml",
        "tests/integration/targets/dcnm_interface/tests/dcnm/dcnm_svi_replace.yaml",
        
        # dcnm_inventory files
        "tests/integration/targets/dcnm_inventory/tests/dcnm/rma.yaml",
        
        # dcnm_policy files
        "tests/integration/targets/dcnm_policy/tests/dcnm/dcnm_policy_merge_same_template.yaml",
        
        # dcnm_service_route_peering files
        "tests/integration/targets/dcnm_service_route_peering/tests/dcnm/dcnm_service_route_peering_merge.yaml",
        "tests/integration/targets/dcnm_service_route_peering/tests/dcnm/dcnm_service_route_peering_no_opt_elems.yaml",
        "tests/integration/targets/dcnm_service_route_peering/tests/dcnm/dcnm_service_route_peering_no_state.yaml",
        "tests/integration/targets/dcnm_service_route_peering/tests/dcnm/dcnm_service_route_peering_sanity.yaml",
        
        # dcnm_template files
        "tests/integration/targets/dcnm_template/tests/dcnm/dcnm_template_delete.yaml",
        "tests/integration/targets/dcnm_template/tests/dcnm/dcnm_template_query.yaml",
        "tests/integration/targets/dcnm_template/tests/dcnm/dcnm_template_validation_fail.yaml",
        "tests/integration/targets/dcnm_template/tests/dcnm/dcnm_template_wrong_state.yaml",
    ]
    
    base_path = Path("/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm")
    
    fixed_count = 0
    for file_rel in files_to_fix:
        file_path = base_path / file_rel
        if file_path.exists():
            print(f"Processing {file_rel}...")
            if fix_indentation_issues(file_path):
                fixed_count += 1
                print(f"  ✓ Fixed")
            else:
                print(f"  - No changes needed")
        else:
            print(f"  ✗ File not found: {file_path}")
    
    print(f"\nFixed {fixed_count} files")


if __name__ == "__main__":
    main()
