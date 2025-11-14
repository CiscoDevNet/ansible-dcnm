#!/usr/bin/env python3
import re

files_to_fix = [
    ('tests/integration/targets/dcnm_fabric/tasks/dcnm.yaml', 14),
    ('tests/integration/targets/dcnm_image_policy/tasks/dcnm.yaml', 14),
    ('tests/integration/targets/dcnm_image_upgrade/tasks/dcnm.yaml', 14),
    ('tests/integration/targets/dcnm_image_upload/tasks/dcnm.yaml', 14),
    ('tests/integration/targets/dcnm_interface/tasks/main.yaml', 16),
    ('tests/integration/targets/dcnm_links/tasks/dcnm.yaml', 16),
    ('tests/integration/targets/dcnm_log/tasks/dcnm.yaml', 16),
    ('tests/integration/targets/dcnm_maintenance_mode/tasks/dcnm.yaml', 14),
    ('tests/integration/targets/dcnm_network/tasks/main.yaml', 65),
    ('tests/integration/targets/dcnm_policy/tasks/dcnm.yaml', 16),
    ('tests/integration/targets/dcnm_resource_manager/tasks/dcnm.yaml', 16),
    ('tests/integration/targets/dcnm_service_node/tasks/dcnm.yaml', 16),
    ('tests/integration/targets/dcnm_service_policy/tasks/dcnm.yaml', 14),
    ('tests/integration/targets/dcnm_service_route_peering/tasks/dcnm.yaml', 16),
    ('tests/integration/targets/dcnm_template/tasks/dcnm.yaml', 16),
    ('tests/integration/targets/dcnm_vpc_pair/tasks/main.yaml', 42),
    ('tests/integration/targets/dcnm_vrf/tasks/dcnm.yaml', 16),
    ('tests/integration/targets/module_integration/tasks/dcnm.yaml', 14),
]

for filepath, line_num in files_to_fix:
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        idx = line_num - 1
        line = lines[idx]
        
        # Match pattern: ansible.builtin.set_fact: var="value"
        match = re.match(r'^(\s+)ansible\.builtin\.set_fact:\s+(\w+)=(.+)$', line)
        if match:
            indent = match.group(1)
            var_name = match.group(2)
            value = match.group(3)
            
            # Replace with dictionary format
            new_line = f'{indent}ansible.builtin.set_fact:\n{indent}  {var_name}: {value}\n'
            lines[idx] = new_line
            
            with open(filepath, 'w') as f:
                f.writelines(lines)
            
            print(f"Fixed: {filepath}:{line_num}")
    except Exception as e:
        print(f"Error in {filepath}:{line_num} - {e}")

print("\nDone!")
