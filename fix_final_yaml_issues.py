#!/usr/bin/env python3
"""Fix remaining common YAML issues."""

import re
from pathlib import Path


def fix_yaml_issues(filepath):
    """Fix multiple YAML issues in a file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original = content
        
        # Fix 1: Comment spacing - add space after #
        lines = content.split('\n')
        fixed_lines = []
        for line in lines:
            # Find comments without space after #
            if '#' in line:
                # Don't touch shebangs or lines that are just ###
                if not line.strip().startswith('#!/') and not re.match(r'^\s*#+\s*$', line):
                    # Fix #comment to # comment
                    line = re.sub(r'#([^\s#])', r'# \1', line)
            fixed_lines.append(line)
        content = '\n'.join(fixed_lines)
        
        # Fix 2: Remove excessive empty lines (more than 2 consecutive)
        while '\n\n\n\n' in content:
            content = content.replace('\n\n\n\n', '\n\n\n')
        
        # Fix 3: Remove trailing whitespace
        lines = content.split('\n')
        content = '\n'.join(line.rstrip() for line in lines)
        
        # Write if changed
        if content != original:
            with open(filepath, 'w') as f:
                f.write(content)
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
        
        if fix_yaml_issues(yaml_file):
            count += 1
            rel_path = yaml_file.relative_to(base)
            if count <= 50:  # Only print first 50
                print(f"✓ {rel_path}")
    
    print(f"\nFixed {count} files")


if __name__ == '__main__':
    main()
