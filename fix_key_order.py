#!/usr/bin/env python3
"""Fix key-order violations by putting 'name' before 'hosts'."""

import re
from pathlib import Path

def fix_key_order(filepath):
    """Reorder play keys to have 'name' before 'hosts'."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original = content
        
        # Pattern: '- hosts: X\n  name: Y' -> '- name: Y\n  hosts: X'
        # This is a multi-line pattern
        pattern = r'^(- )hosts:(\s+\S+)\n(\s+)name:(\s+.+)$'
        replacement = r'\1name:\4\n\3hosts:\2'
        
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        if content != original:
            with open(filepath, 'w') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

base = Path('/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm')

files = [
    'playbooks/roles/dcnm_fabric/dcnm_tests.yaml',
    'playbooks/roles/dcnm_image_policy/dcnm_tests.yaml',
    'playbooks/roles/dcnm_image_upgrade/dcnm_tests.yaml',
    'playbooks/roles/dcnm_interface/dcnm_tests.yaml',
    'playbooks/roles/dcnm_maintenance_mode/dcnm_tests.yaml',
    'playbooks/roles/dcnm_network/dcnm_tests.yaml',
    'playbooks/roles/dcnm_policy/dcnm_tests.yaml',
    'playbooks/roles/dcnm_vpc_pair/dcnm_tests.yaml',
    'playbooks/roles/dcnm_vrf/dcnm_tests.yaml',
    'playbooks/roles/ndfc_interface/ndfc_tests.yaml',
]

fixed = 0
for file in files:
    fpath = base / file
    if fpath.exists() and fix_key_order(fpath):
        fixed += 1
        print(f"✓ {file}")

print(f"\nFixed {fixed} files")
