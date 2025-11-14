#!/usr/bin/env python3
"""
Script to fix assert blocks where conditions have inconsistent indentation.

Pattern to fix:
    that:
      - condition1
    - condition2  # WRONG - should be at same level as condition1
    - condition3

Should be:
    that:
      - condition1
      - condition2
      - condition3
"""

import re
from pathlib import Path


def fix_assert_condition_indent(file_path: Path) -> bool:
    """Fix inconsistent indentation in assert condition lists."""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False
    
    modified = False
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        i += 1
        
        # Check for 'that:' line
        if line.strip() == 'that:':
            that_indent = len(line) - len(line.lstrip())
            
            # Skip empty lines
            while i < len(lines) and not lines[i].strip():
                new_lines.append(lines[i])
                i += 1
            
            if i >= len(lines):
                break
            
            # Get the first condition to establish correct indent
            first_cond = lines[i]
            if not first_cond.lstrip().startswith('-'):
                continue
            
            correct_cond_indent = len(first_cond) - len(first_cond.lstrip())
            new_lines.append(first_cond)
            i += 1
            
            # Process remaining conditions
            while i < len(lines):
                curr_line = lines[i]
                
                if not curr_line.strip() or curr_line.strip().startswith('#'):
                    new_lines.append(curr_line)
                    i += 1
                    continue
                
                curr_stripped = curr_line.lstrip()
                curr_indent = len(curr_line) - len(curr_stripped)
                
                # If this looks like a condition (starts with dash and quote)
                if curr_stripped.startswith('-') and ("'" in curr_stripped or '"' in curr_stripped):
                    # Fix indent if it's wrong
                    if curr_indent != correct_cond_indent:
                        new_lines.append(' ' * correct_cond_indent + curr_stripped)
                        modified = True
                        i += 1
                        continue
                
                # If indent is less than that_indent, we're out of the assert block
                if curr_indent <= that_indent:
                    break
                
                # Regular line
                new_lines.append(curr_line)
                i += 1
    
    if modified:
        try:
            with open(file_path, 'w') as f:
                f.writelines(new_lines)
            return True
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
            return False
    
    return False


def main():
    """Main function to process files."""
    base_path = Path("/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm")
    
    # Get all test YAML files
    test_files = []
    test_files.extend(base_path.glob("tests/**/*.yaml"))
    test_files.extend(base_path.glob("tests/**/*.yml"))
    
    print(f"Found {len(test_files)} YAML test files")
    
    fixed_count = 0
    for file_path in sorted(test_files):
        rel_path = file_path.relative_to(base_path)
        if fix_assert_condition_indent(file_path):
            fixed_count += 1
            print(f"✓ Fixed: {rel_path}")
    
    print(f"\n{fixed_count} files modified")


if __name__ == "__main__":
    main()
