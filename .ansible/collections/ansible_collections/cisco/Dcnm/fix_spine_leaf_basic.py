#!/usr/bin/env python3
"""Fix all indentation issues in spine_leaf_basic.yaml"""

filepath = "/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm/tests/integration/targets/module_integration/tests/spine_leaf_basic.yaml"

with open(filepath, 'r') as f:
    lines = f.readlines()

# Track if we're in the block (line 25 onwards until 'always:')
in_block = False
fixed_count = 0

for i, line in enumerate(lines):
    # Check if we enter the block
    if line.strip() == '- block:':
        in_block = True
        continue
    
    # Check if we exit the block structure (before always)
    if in_block and line.strip().startswith('always:'):
        in_block = 'always_section'
    
    # Fix tasks inside block (should be 4 spaces before dash)
    if in_block == True and line.startswith('  - ') and not line.startswith('    - '):
        # Task with 2 spaces, should be 4
        lines[i] = '  ' + line  # Add 2 more spaces
        fixed_count += 1
        print(f"Line {i+1}: Fixed task indentation")
    
    # Fix module/properties inside tasks (should be 6 spaces)
    if in_block and line.startswith('    ') and not line.startswith('      '):
        # Check if this is a task property (not a task itself)
        stripped = line.strip()
        if stripped and not stripped.startswith('-') and ':' in stripped:
            # This is a property, might need fixing
            if line.startswith('    ') and not line.startswith('      '):
                # Check previous line to see if it's under a task
                if i > 0 and (lines[i-1].strip().startswith('- name:') or  
                              lines[i-1].strip().startswith('- ansible.builtin') or
                              lines[i-1].strip().startswith('- cisco')):
                    lines[i] = '  ' + line  # Add 2 more spaces
                    fixed_count += 1
                    print(f"Line {i+1}: Fixed property indentation")

# Write back
with open(filepath, 'w') as f:
    f.writelines(lines)

print(f"\nFixed {fixed_count} lines")
