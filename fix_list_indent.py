#!/usr/bin/env python3
"""Fix list items that have incorrect indentation."""
import re
from pathlib import Path

def fix_list_indentation(filepath):
    """Fix list items with extra leading space."""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        fixed = False
        for i in range(len(lines)):
            # Find lines that start with space(s) then "- "
            match = re.match(r'^(\s+)- ', lines[i])
            if match and i > 0:
                # Check if previous line is also a list item or a key
                prev_line = lines[i-1]
                prev_match = re.match(r'^(\s+)- ', prev_line)
                key_match = re.match(r'^(\s+)\w+:', prev_line)
                
                if prev_match:
                    # Should be at same indentation as previous list item
                    prev_indent = len(prev_match.group(1))
                    curr_indent = len(match.group(1))
                    
                    if curr_indent != prev_indent:
                        # Fix the indentation
                        diff = curr_indent - prev_indent
                        if diff > 0:
                            # Remove extra spaces
                            lines[i] = lines[i][diff:]
                            fixed = True
                elif key_match:
                    # First list item after a key, ensure proper indentation
                    key_indent = len(key_match.group(1))
                    curr_indent = len(match.group(1))
                    expected = key_indent + 2
                    
                    if curr_indent != expected:
                        diff = curr_indent - expected
                        if diff > 0:
                            lines[i] = lines[i][diff:]
                            fixed = True
                        elif diff < 0:
                            lines[i] = ' ' * (-diff) + lines[i]
                            fixed = True
        
        if fixed:
            with open(filepath, 'w') as f:
                f.writelines(lines)
            return True
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
    return False

base = Path('/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm')
count = 0

# Fix all the files that had load-failure errors
problem_files = [
    'tests/integration/targets/dcnm_vrf/tests/dcnm/merged.yaml',
    'tests/integration/targets/dcnm_vrf/tests/dcnm/overridden.yaml',
    'tests/integration/targets/dcnm_vrf/tests/dcnm/query.yaml',
    'tests/integration/targets/dcnm_vrf/tests/dcnm/replaced.yaml',
    'tests/integration/targets/dcnm_vrf/tests/dcnm/sanity.yaml',
    'tests/integration/targets/dcnm_vrf/tests/dcnm/self-contained-tests/deleted_vrf_all.yaml',
    'tests/integration/targets/dcnm_vrf/tests/dcnm/self-contained-tests/merged_vrf_all.yaml',
    'tests/integration/targets/dcnm_vrf/tests/dcnm/self-contained-tests/overridden_vrf_all.yaml',
    'tests/integration/targets/dcnm_vrf/tests/dcnm/self-contained-tests/replaced_vrf_all.yaml',
    'tests/integration/targets/dcnm_vrf/tests/dcnm/self-contained-tests/vrf_lite.yaml',
    'tests/integration/targets/module_integration/tasks/fabric_setup.yaml',
    'tests/integration/targets/module_integration/tests/spine_leaf_basic.yaml',
    'tests/integration/targets/module_integration/tests/spine_leaf_merged.yaml',
    'tests/integration/targets/module_integration/tests/spine_leaf_overridden.yaml',
    'tests/integration/targets/module_integration/tests/spine_leaf_replaced.yaml',
    'tests/integration/targets/module_integration/tests/spine_leaf_replaced_2.yaml',
    'tests/integration/targets/prepare_dcnm_service_route_peering/tasks/main.yaml',
]

for pfile in problem_files:
    fpath = base / pfile
    if fpath.exists():
        if fix_list_indentation(fpath):
            count += 1
            print(f"✓ Fixed {pfile}")

print(f"\nFixed {count} files")
