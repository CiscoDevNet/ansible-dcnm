#!/usr/bin/env python3
"""Fix assert statement formatting."""

import re
from pathlib import Path


def fix_assert_format(filepath):
    """Fix 'ansible.builtin.assert: that:' to proper format."""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        fixed = False
        
        for i in range(len(lines)):
            line = lines[i]
            
            # Match: '- ansible.builtin.assert: that:' or 'ansible.builtin.assert: that:'
            match = re.match(r'^(\s*)(-\s+)?ansible\.builtin\.assert:\s*that:\s*$', line)
            if match:
                indent = match.group(1)
                dash = match.group(2) or ''
                # Reformat to two lines
                lines[i] = f'{indent}{dash}ansible.builtin.assert:\n'
                lines.insert(i+1, f'{indent}  that:\n')
                fixed = True
            
            # Also fix 'assert: that:' without FQCN
            match = re.match(r'^(\s*)(-\s+)?assert:\s*that:\s*$', line)
            if match:
                indent = match.group(1)
                dash = match.group(2) or ''
                lines[i] = f'{indent}{dash}ansible.builtin.assert:\n'
                lines.insert(i+1, f'{indent}  that:\n')
                fixed = True
        
        if fixed:
            with open(filepath, 'w') as f:
                f.writelines(lines)
            return True
        
        return False
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False


def main():
    base = Path('/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm')
    
    count = 0
    for yaml_file in sorted(base.glob('**/*.yaml')):
        if any(part.startswith('.') for part in yaml_file.parts):
            continue
        
        if fix_assert_format(yaml_file):
            count += 1
            rel_path = yaml_file.relative_to(base)
            print(f"✓ {rel_path}")
    
    print(f"\nFixed {count} files")


if __name__ == '__main__':
    main()
