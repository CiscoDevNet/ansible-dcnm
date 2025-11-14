#!/usr/bin/env python3
"""Fix excessive indentation in YAML files."""

import re
from pathlib import Path

def fix_file_indentation(filepath):
    """Fix excessive indentation in a single file."""
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
            
            # Check if indentation is odd (not multiple of 2) - always wrong
            if curr_indent % 2 == 1:
                # Round down to even number
                new_indent = (curr_indent // 2) * 2
                lines[i] = ' ' * new_indent + line.lstrip()
                fixed = True
                continue
            
            # Find previous non-empty line
            prev_idx = i - 1
            while prev_idx >= 0 and not lines[prev_idx].strip():
                prev_idx -= 1
            
            if prev_idx < 0:
                continue
            
            prev_line = lines[prev_idx]
            prev_indent = len(prev_line) - len(prev_line.lstrip())
            
            # If previous line ends with colon, current should be +2
            if prev_line.rstrip().endswith(':'):
                expected = prev_indent + 2
                if curr_indent > expected:
                    lines[i] = ' ' * expected + line.lstrip()
                    fixed = True
            # If both lines have key: value format (siblings)
            elif ':' in prev_line and ':' in line:
                # Should be at same level
                if curr_indent != prev_indent:
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
    
    # Target files with known indentation issues
    patterns = [
        'tests/integration/targets/dcnm_image_upgrade/**/*.yaml',
        'tests/integration/targets/dcnm_image_upload/**/*.yaml',
        'tests/integration/targets/dcnm_interface/**/*.yaml',
        'tests/integration/targets/dcnm_links/**/*.yaml',
        'tests/integration/targets/dcnm_bootflash/**/*.yaml',
        'tests/integration/targets/dcnm_image_policy/**/*.yaml',
    ]
    
    fixed_count = 0
    for pattern in patterns:
        for filepath in base.glob(pattern):
            if fix_file_indentation(filepath):
                fixed_count += 1
                rel_path = filepath.relative_to(base)
                if fixed_count <= 50:
                    print(f"✓ {rel_path}")
    
    if fixed_count > 50:
        print(f"... and {fixed_count - 50} more files")
    
    print(f"\nFixed {fixed_count} files")

if __name__ == '__main__':
    main()
