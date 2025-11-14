#!/usr/bin/env python3
"""
Script to fix "mapping values are not allowed in this context" errors.
These occur when 'that:' is on the same line as 'assert:'.

Pattern to fix:
  - ansible.builtin.assert: that:
      - condition

Should be:
  - ansible.builtin.assert:
      that:
        - condition
"""

import re
from pathlib import Path


def fix_assert_inline_that(file_path: Path) -> bool:
    """Fix inline 'that:' after 'assert:'."""
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
        
        # Check for pattern: assert: that:
        if re.search(r'assert:\s+that:', line):
            # Get the indentation of the assert line
            indent_match = re.match(r'^(\s*)[-\s]*', line)
            if indent_match:
                base_indent = indent_match.group(1)
                
                # If line starts with dash, preserve it
                if '-' in line[:len(base_indent) + 3]:
                    # Split the line
                    # From: "    - ansible.builtin.assert: that:"
                    # To:   "    - ansible.builtin.assert:"
                    #       "        that:"
                    assert_part = re.sub(r':\s+that:\s*$', ':', line)
                    new_lines.append(assert_part)
                    
                    # Calculate indentation for 'that:'
                    # It should be base_indent + 2 (for dash) + 2 (for property indent) = base_indent + 4
                    # But if there's already a dash, it's base_indent + 2 + 2 = base_indent + 4
                    # For "    - assert:", 'that:' should be at "        that:" (base + 4)
                    list_item_indent = len(base_indent) + 2
                    that_indent = ' ' * (list_item_indent + 2)
                    new_lines.append(that_indent + 'that:\n')
                    
                    modified = True
                    i += 1
                    
                    # Now fix the indentation of following assert conditions
                    # They should be at that_indent + 2
                    condition_indent = that_indent + '  '
                    while i < len(lines):
                        next_line = lines[i]
                        if not next_line.strip():
                            new_lines.append(next_line)
                            i += 1
                            continue
                        
                        # Check if this line is part of the assert block
                        next_stripped = next_line.lstrip()
                        next_indent_len = len(next_line) - len(next_stripped)
                        
                        # If indentation is less than or equal to the assert line, we're done
                        if next_indent_len <= len(base_indent):
                            break
                        
                        # If this is a dash (condition), fix its indentation
                        if next_stripped.startswith('-'):
                            new_lines.append(condition_indent + next_stripped)
                            modified = True
                            i += 1
                        else:
                            # Not a condition, stop processing
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
        if fix_assert_inline_that(file_path):
            fixed_count += 1
            print(f"✓ Fixed: {rel_path}")
    
    print(f"\n{fixed_count} files modified")


if __name__ == "__main__":
    main()
