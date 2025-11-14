#!/usr/bin/env python3
"""Fix lines with one extra leading space causing indentation errors."""

import re
from pathlib import Path


def fix_extra_space_indentation(filepath):
    """Fix lines that have exactly one extra space in indentation."""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        fixed = False
        
        for i in range(len(lines)):
            line = lines[i]
            if not line.strip():
                continue
            
            # Get current indentation
            curr_indent = len(line) - len(line.lstrip())
            
            # Check if this line looks like a key: value pair or list item
            stripped = line.lstrip()
            if not (stripped.startswith('-') or ':' in stripped):
                continue
            
            # Find previous non-empty line
            prev_idx = i - 1
            while prev_idx >= 0 and not lines[prev_idx].strip():
                prev_idx -= 1
            
            if prev_idx < 0:
                continue
            
            prev_line = lines[prev_idx]
            prev_indent = len(prev_line) - len(prev_line.lstrip())
            prev_stripped = prev_line.lstrip()
            
            # If previous line is a key and current line should be indented by 2
            # but is indented by 3 (odd number that's not a multiple of 2)
            if ':' in prev_stripped:
                expected_indent = prev_indent + 2
                # If current indentation is exactly 1 more than expected
                if curr_indent == expected_indent + 1:
                    # Remove one space
                    lines[i] = ' ' * expected_indent + line.lstrip()
                    fixed = True
            
            # If previous line is same level (sibling key) but current has 1 extra space
            elif curr_indent == prev_indent + 1 and curr_indent % 2 == 1:
                # Should be at same level
                lines[i] = ' ' * prev_indent + line.lstrip()
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
    for yaml_file in base.glob('**/*.yaml'):
        if any(part.startswith('.') for part in yaml_file.parts):
            continue
        
        if fix_extra_space_indentation(yaml_file):
            count += 1
            rel_path = yaml_file.relative_to(base)
            print(f"✓ Fixed {rel_path}")
    
    print(f"\nFixed {count} files")


if __name__ == '__main__':
    main()
