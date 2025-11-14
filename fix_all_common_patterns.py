#!/usr/bin/env python3
"""Fix all common YAML patterns causing ansible-lint failures."""

import re
from pathlib import Path


def fix_yaml_file(filepath):
    """Apply all common YAML fixes to a file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original = content
        
        # Fix 1: mapping values are not allowed - quote Jinja expressions with colons
        # Pattern: key: {{ variable }}: extra or key: text: extra
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # If line has unquoted Jinja with trailing colon
            if '{{' in line and '}}:' in line:
                match = re.match(r'^(\s+)(\w+):\s*(.+)$', line)
                if match:
                    indent, key, value = match.groups()
                    value = value.strip()
                    # If not already quoted
                    if not (value.startswith('"') or value.startswith("'")):
                        line = f'{indent}{key}: "{value}"'
            
            # Fix unquoted values with embedded colons
            elif ':' in line:
                match = re.match(r'^(\s+)(\w+):\s*([^"\'#\n]+:.+)$', line)
                if match:
                    indent, key, value = match.groups()
                    value = value.strip()
                    # If contains colon but not quoted and not a dict
                    if not value.startswith('{') and '{{' not in value:
                        line = f'{indent}{key}: "{value}"'
            
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # Fix 2: Name casing - capitalize first letter of task names
        content = re.sub(
            r'^(\s+name:\s+)([a-z])',
            lambda m: m.group(1) + m.group(2).upper(),
            content,
            flags=re.MULTILINE
        )
        
        # Fix 3: Remove FQCN issues - ensure ansible.builtin for core modules
        for module in ['include_tasks', 'set_fact', 'debug', 'assert', 'pause']:
            # Add FQCN if missing
            content = re.sub(
                rf'^(\s+){module}:',
                rf'\1ansible.builtin.{module}:',
                content,
                flags=re.MULTILINE
            )
            # Also fix task-level
            content = re.sub(
                rf'^(\s+)-\s+{module}:',
                rf'\1- ansible.builtin.{module}:',
                content,
                flags=re.MULTILINE
            )
        
        # Fix 4: key-order issues - move 'name' before other keys in tasks
        # This is complex, so we'll skip for now
        
        # Fix 5: Ensure consistent indentation (multiples of 2)
        lines = content.split('\n')
        fixed_lines = []
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                # If odd indentation (not multiple of 2)
                if indent % 2 == 1:
                    # Round down to nearest even
                    new_indent = (indent // 2) * 2
                    line = ' ' * new_indent + line.lstrip()
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # Write back if changed
        if content != original:
            with open(filepath, 'w') as f:
                f.write(content)
            return True
        
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False


def main():
    base = Path('/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm')
    
    fixed_count = 0
    
    # Process all YAML files
    for yaml_file in sorted(base.glob('**/*.yaml')):
        if any(part.startswith('.') for part in yaml_file.parts):
            continue
        
        if fix_yaml_file(yaml_file):
            fixed_count += 1
            rel_path = yaml_file.relative_to(base)
            print(f"✓ {rel_path}")
    
    print(f"\nFixed {fixed_count} files")


if __name__ == '__main__':
    main()
