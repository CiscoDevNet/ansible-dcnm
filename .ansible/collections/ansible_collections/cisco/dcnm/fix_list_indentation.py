#!/usr/bin/env python3
"""
Fix list indentation issues in YAML files.
Ensures all list items at the same level have consistent indentation.
"""
import re
from pathlib import Path

def fix_list_indentation(file_path):
    """Fix inconsistent list item indentation in a YAML file."""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        modified = False
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            
            # Check for list items
            if stripped.startswith('- '):
                current_indent = len(line) - len(stripped)
                
                # Look ahead to find other list items that should be at same level
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    next_stripped = next_line.lstrip()
                    
                    if next_stripped.startswith('- '):
                        next_indent = len(next_line) - len(next_stripped)
                        
                        # If this list item has different indentation, fix it
                        # Check if it's the next sibling (not a nested list)
                        if abs(next_indent - current_indent) == 2:
                            # Fix the indentation
                            lines[j] = ' ' * current_indent + next_stripped
                            modified = True
                    elif next_stripped and not next_stripped.startswith('#'):
                        # Non-list line with content, check if we should stop
                        next_indent = len(next_line) - len(next_stripped)
                        if next_indent <= current_indent:
                            break
                    
                    j += 1
            
            i += 1
        
        if modified:
            with open(file_path, 'w') as f:
                f.writelines(lines)
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    test_dirs = [
        "tests/integration/targets/dcnm_image_upgrade/tests",
        "tests/integration/targets/dcnm_interface/tests/dcnm",
        "tests/integration/targets/dcnm_inventory/tests/dcnm",
        "tests/integration/targets/dcnm_links/tests/dcnm",
    ]
    
    fixed_count = 0
    for test_dir in test_dirs:
        test_path = Path(test_dir)
        if test_path.exists():
            for yaml_file in test_path.glob("*.yaml"):
                if fix_list_indentation(yaml_file):
                    print(f"Fixed: {yaml_file}")
                    fixed_count += 1
    
    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == "__main__":
    main()
