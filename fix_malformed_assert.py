#!/usr/bin/env python3
"""
Script to fix malformed assert blocks where:
1. 'that:' is not properly indented under 'assert:'
2. Conditions are missing dashes or have wrong indentation
3. Next task starts at wrong indent level

Pattern to fix:
    - ansible.builtin.assert:
    that:
        'condition'

      - name: Next task

Should be:
    - ansible.builtin.assert:
        that:
          - 'condition'

    - name: Next task
"""

import re
from pathlib import Path


def fix_malformed_assert(file_path: Path) -> bool:
    """Fix malformed assert blocks."""
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
        
        # Check for assert: at end of line
        if 'assert:' in line and line.strip().endswith('assert:'):
            # Get the indentation
            assert_match = re.match(r'^(\s*)[-\s]*', line)
            if not assert_match:
                new_lines.append(line)
                i += 1
                continue
            
            base_indent = assert_match.group(1)
            has_dash = '-' in line[:len(base_indent) + 3]
            
            new_lines.append(line)
            i += 1
            
            # Check next non-empty line
            while i < len(lines) and not lines[i].strip():
                new_lines.append(lines[i])
                i += 1
            
            if i >= len(lines):
                break
            
            next_line = lines[i]
            next_stripped = next_line.lstrip()
            next_indent_len = len(next_line) - len(next_stripped)
            
            # Check if next line is 'that:' at wrong indent
            if next_stripped.startswith('that:'):
                # Calculate correct indentation for 'that:'
                if has_dash:
                    correct_that_indent = len(base_indent) + 2 + 2  # base + dash + property
                else:
                    correct_that_indent = len(base_indent) + 2  # base + property
                
                # If 'that:' is at wrong indent (same as base or less), fix it
                if next_indent_len <= len(base_indent):
                    new_lines.append(' ' * correct_that_indent + 'that:\n')
                    modified = True
                    i += 1
                    
                    # Now handle the conditions
                    condition_indent = ' ' * (correct_that_indent + 2)
                    
                    while i < len(lines):
                        cond_line = lines[i]
                        if not cond_line.strip():
                            new_lines.append(cond_line)
                            i += 1
                            continue
                        
                        cond_stripped = cond_line.lstrip()
                        cond_indent_len = len(cond_line) - len(cond_stripped)
                        
                        # If line starts at or before base indent, we're done with assert block
                        if cond_indent_len <= len(base_indent):
                            # Check if this should actually be indented correctly as next task
                            if cond_stripped.startswith('- '):
                                # This is the next task, fix its indentation if needed
                                if cond_indent_len != len(base_indent):
                                    new_lines.append(base_indent + cond_stripped)
                                    modified = True
                                    i += 1
                                break
                            else:
                                break
                        
                        # This is a condition line
                        if cond_stripped.startswith('-'):
                            # Already has dash, just fix indent
                            new_lines.append(condition_indent + cond_stripped)
                            modified = True
                            i += 1
                        elif cond_stripped.startswith("'") or cond_stripped.startswith('"'):
                            # Condition without dash, add it
                            new_lines.append(condition_indent + '- ' + cond_stripped)
                            modified = True
                            i += 1
                        else:
                            # Not a condition, done with assert block
                            break
                    
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
        if fix_malformed_assert(file_path):
            fixed_count += 1
            print(f"✓ Fixed: {rel_path}")
    
    print(f"\n{fixed_count} files modified")


if __name__ == "__main__":
    main()
