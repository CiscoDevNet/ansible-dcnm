#!/usr/bin/env python3
"""
Script to fix tasks wrongly indented under assert blocks.

Pattern to fix:
    - ansible.builtin.assert:
        that:
          - condition
            
        - name: Next Task  # WRONG - should be at base level

Should be:
    - ansible.builtin.assert:
        that:
          - condition
    
    - name: Next Task  # CORRECT
"""

import re
from pathlib import Path


def fix_tasks_under_assert(file_path: Path) -> bool:
    """Fix tasks that are wrongly nested under assert blocks."""
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
        
        # Check for assert: with that: block
        if 'assert:' in line and line.strip().endswith('assert:'):
            assert_match = re.match(r'^(\s*)[-\s]*', line)
            if not assert_match:
                continue
            
            base_indent = assert_match.group(1)
            
            # Skip lines until we find potential misindented task
            in_assert_block = True
            while i < len(lines) and in_assert_block:
                curr_line = lines[i]
                
                if not curr_line.strip():
                    new_lines.append(curr_line)
                    i += 1
                    continue
                
                curr_stripped = curr_line.lstrip()
                curr_indent_len = len(curr_line) - len(curr_stripped)
                
                # If we find a line that starts with "- name:" but is indented more than base
                if curr_stripped.startswith('- name:') and curr_indent_len > len(base_indent):
                    # This task should be at base level
                    fixed_line = base_indent + curr_stripped
                    new_lines.append(fixed_line)
                    modified = True
                    i += 1
                    in_assert_block = False
                # If we find any task-like keyword wrongly indented
                elif curr_indent_len > len(base_indent) + 2:
                    # Check if this looks like a task (has name:, register:, when:, etc.)
                    if any(keyword in curr_stripped for keyword in ['- name:', '- ansible.', '- cisco.']):
                        if curr_stripped.startswith('-'):
                            # It's a task, move to correct indent
                            fixed_line = base_indent + curr_stripped
                            new_lines.append(fixed_line)
                            modified = True
                            i += 1
                            in_assert_block = False
                        else:
                            new_lines.append(curr_line)
                            i += 1
                    else:
                        new_lines.append(curr_line)
                        i += 1
                # If indent is at or less than base, we're out of assert block
                elif curr_indent_len <= len(base_indent):
                    in_assert_block = False
                else:
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
        if fix_tasks_under_assert(file_path):
            fixed_count += 1
            print(f"✓ Fixed: {rel_path}")
    
    print(f"\n{fixed_count} files modified")


if __name__ == "__main__":
    main()
