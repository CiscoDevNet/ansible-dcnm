#!/usr/bin/env python3
"""Fix remaining ansible-lint violations."""

import re
from pathlib import Path


def fix_file(filepath):
    """Fix various issues in a file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Fix no-free-form for set_fact
    # Convert "ansible.builtin.set_fact: var=value" to proper YAML
    content = re.sub(
        r'^(\s*)ansible\.builtin\.set_fact:\s+(\w+)=',
        r'\1ansible.builtin.set_fact:\n\1  \2: ',
        content,
        flags=re.MULTILINE
    )
    
    # Fix var-naming - convert IT_CONTEXT to it_context
    content = content.replace('IT_CONTEXT', 'it_context')
    
    # Fix jinja spacing - remove spaces around filter pipes
    content = re.sub(r'\|\s+combine\s+\(', '| combine(', content)
    content = re.sub(r'\|\s+join\s+\(', '| join(', content)
    
    # Fix empty-lines in modules (max 2 blank lines)
    lines = content.split('\n')
    fixed_lines = []
    blank_count = 0
    
    for line in lines:
        if line.strip() == '':
            blank_count += 1
            if blank_count <= 2:
                fixed_lines.append(line)
        else:
            blank_count = 0
            fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # Fix trailing spaces
    lines = content.split('\n')
    content = '\n'.join(line.rstrip() for line in lines)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


base = Path('/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm')

# Fix Python module docstrings
modules = [
    'plugins/modules/dcnm_image_policy.py',
    'plugins/modules/dcnm_image_upgrade.py',
    'plugins/modules/dcnm_interface.py',
    'plugins/modules/dcnm_inventory.py',
    'plugins/modules/dcnm_links.py',
    'plugins/modules/dcnm_log.py',
    'plugins/modules/dcnm_maintenance_mode.py',
    'plugins/modules/dcnm_network.py',
    'plugins/modules/dcnm_rest.py',
    'plugins/modules/dcnm_service_node.py',
    'plugins/modules/dcnm_service_policy.py',
    'plugins/modules/dcnm_service_route_peering.py',
    'plugins/modules/dcnm_vrf.py',
]

fixed_count = 0
for module in modules:
    module_path = base / module
    if module_path.exists():
        if fix_file(module_path):
            fixed_count += 1
            print(f"✓ Fixed {module}")

# Fix all YAML files for remaining issues
for yaml_file in base.glob('**/*.yaml'):
    if any(part.startswith('.') for part in yaml_file.parts):
        continue
    if fix_file(yaml_file):
        fixed_count += 1

print(f"\nFixed {fixed_count} files")
