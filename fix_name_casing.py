#!/usr/bin/env python3
"""Fix name[casing] violations - capitalize task/handler names."""

import re
from pathlib import Path

def fix_task_names(filepath):
    """Capitalize task and handler names."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original = content
        
        # Fix "name: collect" -> "name: Collect"
        content = re.sub(
            r'^(\s+name:\s+)([a-z])',
            lambda m: m.group(1) + m.group(2).upper(),
            content,
            flags=re.MULTILINE
        )
        
        if content != original:
            with open(filepath, 'w') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error: {filepath}: {e}")
        return False

base = Path('/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm')

# Target specific files with name[casing] issues
files = [
    'tests/integration/targets/dcnm_bootflash/tasks/dcnm.yaml',
    'tests/integration/targets/dcnm_fabric/tasks/dcnm.yaml',
    'tests/integration/targets/dcnm_image_policy/tasks/dcnm.yaml',
    'tests/integration/targets/dcnm_image_upgrade/tasks/dcnm.yaml',
    'tests/integration/targets/dcnm_image_upload/tasks/dcnm.yaml',
    'tests/integration/targets/dcnm_interface/tasks/main.yaml',
    'tests/integration/targets/dcnm_inventory/tasks/dcnm.yaml',
    'tests/integration/targets/dcnm_links/tasks/dcnm.yaml',
    'tests/integration/targets/dcnm_log/tasks/dcnm.yaml',
    'tests/integration/targets/dcnm_maintenance_mode/tasks/dcnm.yaml',
    'tests/integration/targets/dcnm_network/tasks/dcnm.yaml',
    'tests/integration/targets/dcnm_policy/tasks/dcnm.yaml',
    'tests/integration/targets/dcnm_resource_manager/tasks/dcnm.yaml',
    'tests/integration/targets/dcnm_service_node/tasks/dcnm.yaml',
    'tests/integration/targets/dcnm_service_policy/tasks/dcnm.yaml',
    'tests/integration/targets/dcnm_service_route_peering/tasks/dcnm.yaml',
    'tests/integration/targets/dcnm_template/tasks/dcnm.yaml',
    'tests/integration/targets/dcnm_vrf/tasks/dcnm.yaml',
    'tests/integration/targets/dcnm_vpc_pair/tasks/dcnm.yaml',
    'tests/integration/targets/module_integration/tasks/dcnm.yaml',
]

fixed = 0
for file in files:
    fpath = base / file
    if fpath.exists() and fix_task_names(fpath):
        fixed += 1
        print(f"✓ {file}")

print(f"\nFixed {fixed} files")
