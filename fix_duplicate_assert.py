#!/usr/bin/env python3
"""
Script to fix remaining complex YAML issues:
1. Duplicate assert lines
2. Conditions without dashes
3. Tasks with wrong indentation after assert blocks
"""

import re
from pathlib import Path


def fix_duplicate_assert_and_conditions(file_path: Path) -> bool:
    """Fix duplicate assert declarations and missing condition dashes."""
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
        
        # Check for assert: line
        if 'ansible.builtin.assert:' in line and line.strip().endswith('assert:'):
            assert_match = re.match(r'^(\s*)[-\s]*', line)
            if not assert_match:
                new_lines.append(line)
                i += 1
                continue
            
            base_indent = assert_match.group(1)
            has_dash = '-' in line[:len(base_indent) + 3]
            
            new_lines.append(line)
            i += 1
            
            # Skip empty lines
            while i < len(lines) and not lines[i].strip():
                new_lines.append(lines[i])
                i += 1
            
            if i >= len(lines):
                break
            
            # Check for duplicate assert line
            if 'ansible.builtin.assert:' in lines[i] and lines[i].strip().endswith('assert:'):
                # Skip the duplicate
                modified = True
                i += 1
                
                # Skip more empty lines
                while i < len(lines) and not lines[i].strip():
                    new_lines.append(lines[i])
                    i += 1
            
            if i >= len(lines):
                break
            
            # Calculate correct indentations
            if has_dash:
                that_indent = len(base_indent) + 4
                cond_indent = that_indent + 2
            else:
                that_indent = len(base_indent) + 2
                cond_indent = that_indent + 2
            
            # Check if next line is a condition without proper structure
            next_line = lines[i]
            next_stripped = next_line.lstrip()
            next_indent_len = len(next_line) - len(next_stripped)
            
            # If we have a condition without 'that:', add it
            if (next_stripped.startswith("'") or next_stripped.startswith('"')) and 'that:' not in next_line:
                # Add 'that:' line
                new_lines.append(' ' * that_indent + 'that:\n')
                # Add condition with dash
                new_lines.append(' ' * cond_indent + '- ' + next_stripped)
                modified = True
                i += 1
                continue
            
            # If next line is 'that:' at correct indent, process conditions
            if next_stripped == 'that:':
                new_lines.append(lines[i])
                i += 1
                
                # Process conditions
                while i < len(lines):
                    cond_line = lines[i]
                    if not cond_line.strip():
                        new_lines.append(cond_line)
                        i += 1
                        continue
                    
                    cond_stripped = cond_line.lstrip()
                    cond_indent_len = len(cond_line) - len(cond_stripped)
                    
                    # If we've left the assert block
                    if cond_indent_len <= len(base_indent):
                        break
                    
                    # If condition is missing dash and starts with quote
                    if (cond_stripped.startswith("'") or cond_stripped.startswith('"')) and not cond_stripped.startswith('-'):
                        new_lines.append(' ' * cond_indent + '- ' + cond_stripped)
                        modified = True
                        i += 1
                        continue
                    
                    # Normal condition line
                    new_lines.append(cond_line)
                    i += 1
                
                continue
        
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
        if fix_duplicate_assert_and_conditions(file_path):
            fixed_count += 1
            print(f"✓ Fixed: {rel_path}")
    
    print(f"\n{fixed_count} files modified")


if __name__ == "__main__":
    main()
