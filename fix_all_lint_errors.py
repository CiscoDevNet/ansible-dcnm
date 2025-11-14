#!/usr/bin/env python3
"""
Comprehensive script to fix ansible-lint errors in bulk.
Handles:
1. load-failure errors (incorrect indentation breaking YAML parsing)
2. yaml[indentation] errors (wrong indentation levels)
3. yaml[line-length] errors (lines exceeding 160 chars)
4. yaml[key-duplicates] (duplicate 'that' keys in assertions)
5. yaml[brackets] (spacing in brackets)
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def run_ansible_lint(file_path: str) -> List[str]:
    """Run ansible-lint on a file and return error lines."""
    try:
        result = subprocess.run(
            ['ansible-lint', '--profile=production', file_path],
            capture_output=True,
            text=True,
            cwd='/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm'
        )
        # Parse output for errors
        errors = []
        for line in result.stdout.split('\n'):
            if 'yaml[' in line or 'load-failure' in line:
                errors.append(line)
        return errors
    except Exception as e:
        print(f"Error running ansible-lint: {e}")
        return []


def fix_indentation_pattern_1(lines: List[str]) -> Tuple[List[str], bool]:
    """Fix pattern: expect 10 spaces but found 8 (after 'that:')."""
    new_lines = []
    modified = False
    
    for i, line in enumerate(lines):
        if i > 0 and lines[i-1].strip() == 'that:':
            # Lines after 'that:' should be indented 2 more spaces
            if re.match(r'^        - ', line):  # 8 spaces
                new_lines.append('  ' + line)
                modified = True
                continue
        new_lines.append(line)
    
    return new_lines, modified


def fix_indentation_pattern_2(lines: List[str]) -> Tuple[List[str], bool]:
    """Fix pattern: 10 spaces when 8 expected (task properties)."""
    new_lines = []
    modified = False
    
    for i, line in enumerate(lines):
        # Check for 10-space indentation that should be 8
        if re.match(r'^          - ', line):  # 10 spaces before dash
            # Look back to find context
            j = i - 1
            while j >= 0 and (lines[j].strip() == '' or lines[j].strip().startswith('#')):
                j -= 1
            
            if j >= 0:
                # If previous non-empty line is at 6 spaces or starts with 6, reduce to 8
                if re.match(r'^      [a-zA-Z]', lines[j]) or re.match(r'^      - ', lines[j]):
                    new_lines.append(line[2:])  # Remove 2 spaces
                    modified = True
                    continue
        
        new_lines.append(line)
    
    return new_lines, modified


def fix_indentation_pattern_3(lines: List[str]) -> Tuple[List[str], bool]:
    """Fix pattern: 8 spaces when 10 expected (nested items under lists)."""
    new_lines = []
    modified = False
    
    for i, line in enumerate(lines):
        # Check for properties that should be more indented
        if re.match(r'^        [a-zA-Z_][a-zA-Z_0-9]*:', line) and i > 0:
            # Look for previous list item at 8 spaces
            j = i - 1
            while j >= 0 and lines[j].strip() == '':
                j -= 1
            
            if j >= 0 and re.match(r'^        - ', lines[j]):
                # This property should be at 10 spaces (under the list item)
                new_lines.append('  ' + line)
                modified = True
                continue
        
        new_lines.append(line)
    
    return new_lines, modified


def fix_duplicate_that_keys(lines: List[str]) -> Tuple[List[str], bool]:
    """Fix duplicate 'that:' keys in assertions by removing duplicates."""
    new_lines = []
    modified = False
    in_assert_block = False
    seen_that = False
    
    for i, line in enumerate(lines):
        # Check if we're entering an assert block
        if 'ansible.builtin.assert:' in line or 'assert:' in line:
            in_assert_block = True
            seen_that = False
            new_lines.append(line)
            continue
        
        # Check if we're leaving the assert block
        if in_assert_block and line.strip() and not line.strip().startswith('#'):
            if not line.startswith(' '):
                in_assert_block = False
                seen_that = False
        
        # If in assert block and we see 'that:', track it
        if in_assert_block and line.strip() == 'that:':
            if seen_that:
                # Skip this duplicate 'that:' line
                modified = True
                continue
            seen_that = True
        
        new_lines.append(line)
    
    return new_lines, modified


def fix_config_indentation(lines: List[str]) -> Tuple[List[str], bool]:
    """Fix deeply nested config blocks with wrong indentation."""
    new_lines = []
    modified = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Look for pattern: config: followed by wrongly indented keys
        if 'config:' in line and i + 1 < len(lines):
            next_line = lines[i + 1]
            # If next line has more than 2 extra spaces, it's wrong
            current_indent = len(line) - len(line.lstrip())
            next_indent = len(next_line) - len(next_line.lstrip())
            
            if next_line.strip() and not next_line.strip().startswith('#'):
                expected_indent = current_indent + 2
                if next_indent > expected_indent + 2:
                    # Fix the indentation
                    spaces_to_remove = next_indent - expected_indent
                    new_lines.append(line)
                    i += 1
                    
                    # Fix subsequent lines at wrong indent level
                    while i < len(lines):
                        curr_line = lines[i]
                        if curr_line.strip() and not curr_line.strip().startswith('#'):
                            curr_line_indent = len(curr_line) - len(curr_line.lstrip())
                            if curr_line_indent >= next_indent:
                                # Remove excess spaces
                                new_lines.append(' ' * (curr_line_indent - spaces_to_remove) + curr_line.lstrip())
                                modified = True
                            else:
                                new_lines.append(curr_line)
                                break
                        else:
                            new_lines.append(curr_line)
                        i += 1
                    continue
        
        new_lines.append(line)
        i += 1
    
    return new_lines, modified


def fix_list_indicator_missing(lines: List[str]) -> Tuple[List[str], bool]:
    """Fix 'did not find expected '-' indicator' errors."""
    new_lines = []
    modified = False
    
    for i, line in enumerate(lines):
        # Look for lines that should be list items but aren't
        # Pattern: a line with dict-like content that should be a list item
        if i > 0 and ':' in line and '-' not in line:
            prev_line = lines[i-1].strip()
            # Check if previous line suggests this should be a list
            if prev_line.endswith(':') or (i > 1 and '- ' in lines[i-2]):
                indent = len(line) - len(line.lstrip())
                # Check if this looks like it should be a list item
                if re.match(r'^\s+[a-zA-Z_][a-zA-Z_0-9]*:\s*$', line):
                    # Convert to list item
                    new_lines.append(' ' * indent + '- ' + line.lstrip())
                    modified = True
                    continue
        
        new_lines.append(line)
    
    return new_lines, modified


def fix_mapping_values_not_allowed(lines: List[str]) -> Tuple[List[str], bool]:
    """Fix 'mapping values are not allowed in this context' errors."""
    new_lines = []
    modified = False
    
    for i, line in enumerate(lines):
        # This error often occurs with inline dictionaries that need proper formatting
        # Pattern: key: value: nested_value (double colon)
        if line.count(':') > 1 and '-' not in line:
            # Check for inline dict that needs to be split
            parts = line.split(':', 2)
            if len(parts) >= 3:
                indent = len(line) - len(line.lstrip())
                # Split into proper YAML
                new_lines.append(parts[0] + ':')
                new_lines.append(' ' * (indent + 2) + parts[1].strip() + ': ' + parts[2].strip())
                modified = True
                continue
        
        new_lines.append(line)
    
    return new_lines, modified


def fix_file(file_path: Path) -> bool:
    """Apply all fixes to a file."""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False
    
    original_content = ''.join(lines)
    modified = False
    
    # Apply fixes in sequence
    fixes = [
        fix_duplicate_that_keys,
        fix_config_indentation,
        fix_indentation_pattern_1,
        fix_indentation_pattern_2,
        fix_indentation_pattern_3,
        fix_list_indicator_missing,
        fix_mapping_values_not_allowed,
    ]
    
    for fix_func in fixes:
        lines, was_modified = fix_func(lines)
        if was_modified:
            modified = True
    
    if modified:
        try:
            with open(file_path, 'w') as f:
                f.writelines(lines)
            return True
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
            # Restore original
            with open(file_path, 'w') as f:
                f.write(original_content)
            return False
    
    return False


def main():
    """Main function."""
    base_path = Path("/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm")
    
    # Get all YAML files in tests directory
    test_files = list(base_path.glob("tests/**/*.yaml"))
    test_files.extend(list(base_path.glob("tests/**/*.yml")))
    
    print(f"Found {len(test_files)} YAML files to process")
    
    fixed_count = 0
    for file_path in test_files:
        rel_path = file_path.relative_to(base_path)
        print(f"Processing {rel_path}...", end=' ')
        
        if fix_file(file_path):
            fixed_count += 1
            print("✓ Fixed")
        else:
            print("- No changes")
    
    print(f"\nFixed {fixed_count} files")
    print("\nRun 'ansible-lint --profile=production' to verify fixes")


if __name__ == "__main__":
    main()
