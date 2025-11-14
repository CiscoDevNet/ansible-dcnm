#!/usr/bin/env python3
"""
Script to fix the most common load-failure pattern:
Properties not properly indented under list items in YAML files.

Pattern:
  - key1: value
  key2: value  # WRONG - should be indented 2 more spaces
  
Should be:
  - key1: value
    key2: value  # CORRECT
"""

import re
import sys
from pathlib import Path


def fix_list_item_indentation(file_path: Path) -> bool:
    """Fix properties that should be indented under list items."""
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
        
        # Check if this is a list item (starts with dash after spaces)
        list_match = re.match(r'^(\s+)- ', line)
        if list_match:
            list_indent = len(list_match.group(1))
            property_indent = list_indent + 2  # Properties should be +2 from dash
            
            new_lines.append(line)
            i += 1
            
            # Process following lines that should be properties of this list item
            while i < len(lines):
                next_line = lines[i]
                
                # Skip empty lines and comments
                if not next_line.strip() or next_line.strip().startswith('#'):
                    new_lines.append(next_line)
                    i += 1
                    continue
                
                # Check indentation of next line
                next_stripped = next_line.lstrip()
                next_indent = len(next_line) - len(next_stripped)
                
                # If next line starts with dash at same or less indent, it's a new list item or different block
                if next_stripped.startswith('-'):
                    if next_indent <= list_indent:
                        break
                    # It's a nested list, continue
                    new_lines.append(next_line)
                    i += 1
                    continue
                
                # If next line has less indent than list_indent, it's a new block
                if next_indent < list_indent:
                    break
                
                # If next line is a property at wrong indent (same as list_indent), fix it
                if next_indent == list_indent and ':' in next_line:
                    # This property should be indented under the list item
                    fixed_line = ' ' * property_indent + next_stripped
                    new_lines.append(fixed_line)
                    modified = True
                    i += 1
                    continue
                
                # If indent is between list and property level, also fix
                if list_indent < next_indent < property_indent and ':' in next_line:
                    fixed_line = ' ' * property_indent + next_stripped
                    new_lines.append(fixed_line)
                    modified = True
                    i += 1
                    continue
                
                # Line is at correct indent or part of a nested structure
                new_lines.append(next_line)
                i += 1
        else:
            new_lines.append(line)
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
        if fix_list_item_indentation(file_path):
            fixed_count += 1
            print(f"✓ Fixed: {rel_path}")
    
    print(f"\n{fixed_count} files modified")
    print("\nRun 'ansible-lint --profile=production' to verify fixes")


if __name__ == "__main__":
    main()
