#!/usr/bin/env python3
"""Fix malformed assert statements in prepare_dcnm_policy."""

filepath = '/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm/tests/integration/targets/prepare_dcnm_policy/tasks/main.yaml'

with open(filepath, 'r') as f:
    lines = f.readlines()

i = 0
fixed_count = 0

while i < len(lines):
    line = lines[i]
    
    # Check for "    - name: Assert" followed by "    - ansible.builtin.assert:"
    if line.strip() == '- name: Assert' and i + 1 < len(lines):
        next_line = lines[i + 1]
        if '    - ansible.builtin.assert:' in next_line:
            # This is the malformed pattern
            # Replace the next line to remove the dash and fix indentation
            lines[i + 1] = next_line.replace('    - ansible.builtin.assert:', '      ansible.builtin.assert:')
            fixed_count += 1
            print(f"Fixed line {i + 2}")
    
    i += 1

with open(filepath, 'w') as f:
    f.writelines(lines)

print(f"\nFixed {fixed_count} assert statements")
