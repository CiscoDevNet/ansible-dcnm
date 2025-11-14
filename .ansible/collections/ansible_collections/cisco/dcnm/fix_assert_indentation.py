#!/usr/bin/env python3
"""
Fix assert indentation issues in YAML files.
Converts lines with 4-space indentation under 'that:' to 6-space indentation.
"""
import re
import sys
from pathlib import Path

def fix_assert_indentation(file_path):
    """Fix assert block indentation in a YAML file."""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        modified = False
        in_assert_block = False
        that_indent_level = 0
        
        for i, line in enumerate(lines):
            # Check if we're entering an assert block with 'that:'
            if 'that:' in line and ('assert:' in lines[i-1] if i > 0 else False):
                in_assert_block = True
                # Determine the indentation level of 'that:'
                that_indent_level = len(line) - len(line.lstrip())
                continue
            
            if in_assert_block:
                current_indent = len(line) - len(line.lstrip())
                
                # Check if line is a list item under 'that:'
                stripped = line.lstrip()
                if stripped.startswith('- '):
                    expected_indent = that_indent_level + 2
                    if current_indent == that_indent_level - 2:  # 4 spaces instead of 6
                        # Fix the indentation
                        lines[i] = ' ' * expected_indent + stripped
                        modified = True
                elif stripped and not stripped.startswith('#'):
                    # Non-list item, check if we should exit assert block
                    if current_indent <= that_indent_level:
                        in_assert_block = False
        
        if modified:
            with open(file_path, 'w') as f:
                f.writelines(lines)
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    # Get all YAML files with load-failure errors
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
                if fix_assert_indentation(yaml_file):
                    print(f"Fixed: {yaml_file}")
                    fixed_count += 1
    
    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == "__main__":
    main()
