#!/usr/bin/env python3
import re

def fix_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    modified = False
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check for unnamed assert/debug/meta
        match = re.match(r'^(\s+)- (ansible\.builtin\.)?(assert|debug|meta):', line)
        if match:
            indent = match.group(1)
            module = match.group(3)
            name_map = {'assert': 'Assert', 'debug': 'Debug', 'meta': 'Meta'}
            lines.insert(i, f'{indent}- name: {name_map[module]}\n')
            modified = True
            i += 1
        i += 1
    
    if modified:
        with open(filepath, 'w') as f:
            f.writelines(lines)
        print(f"Fixed: {filepath}")

files = [
    'tests/integration/targets/module_integration/tasks/fabric_setup.yaml',
    'tests/integration/targets/prepare_dcnm_policy/tasks/main.yaml',
    'tests/integration/targets/prepare_dcnm_service_route_peering/tasks/main.yaml',
    'tests/integration/targets/prepare_dcnm_template/tasks/main.yaml'
]

for f in files:
    try:
        fix_file(f)
    except Exception as e:
        print(f"Error: {e}")
