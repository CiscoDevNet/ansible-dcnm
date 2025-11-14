#!/usr/bin/env python3
"""
Comprehensive YAML syntax error fixer for ansible-lint violations.
Fixes:
- "mapping values are not allowed in this context" (colon in wrong place)
- "did not find expected key" (indentation issues)
- "did not find expected '-' indicator" (list item indentation)
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple


def parse_lint_output(lint_file: str) -> Dict[str, List[Tuple[int, str]]]:
    """Parse lint output to extract file-specific errors."""
    errors = {}
    
    with open(lint_file, 'r') as f:
        content = f.read()
    
    # Match patterns like: filepath.yaml:line:col error_message
    pattern = r'\[35m([^\[]+?\.ya?ml)\[0m:(\d+):\d+ \[2m(.+?)\[0m'
    
    for match in re.finditer(pattern, content):
        filepath = match.group(1)
        line_num = int(match.group(2))
        error_msg = match.group(3)
        
        if filepath not in errors:
            errors[filepath] = []
        errors[filepath].append((line_num, error_msg))
    
    return errors


def fix_mapping_values_error(lines: List[str], line_num: int) -> bool:
    """
    Fix 'mapping values are not allowed in this context' error.
    Usually caused by unquoted strings with colons.
    """
    if line_num <= 0 or line_num > len(lines):
        return False
    
    idx = line_num - 1
    line = lines[idx]
    
    # Common pattern: variable: {{ some_var }}: extra text
    # Should be quoted
    if '{{' in line and '}}' in line and line.count(':') > 1:
        # Find the key part
        match = re.match(r'^(\s+)(\w+):\s*(.+)$', line)
        if match:
            indent, key, value = match.groups()
            # If value has unquoted colon after Jinja
            if '}}:' in value and not value.strip().startswith('"'):
                # Quote the value
                lines[idx] = f'{indent}{key}: "{value}"'
                return True
    
    return False


def fix_expected_key_error(lines: List[str], line_num: int) -> bool:
    """
    Fix 'did not find expected key' error.
    Usually caused by incorrect indentation.
    """
    if line_num <= 0 or line_num > len(lines):
        return False
    
    idx = line_num - 1
    line = lines[idx]
    
    # Check if this line is overly indented compared to context
    if idx > 0:
        prev_line = lines[idx - 1]
        
        curr_indent = len(line) - len(line.lstrip())
        prev_indent = len(prev_line) - len(prev_line.lstrip())
        
        # If current line is indented way more than previous
        if curr_indent > prev_indent + 4:
            # Reduce indentation
            diff = curr_indent - (prev_indent + 2)
            if diff > 0:
                lines[idx] = line[diff:]
                return True
    
    return False


def fix_expected_dash_error(lines: List[str], line_num: int) -> bool:
    """
    Fix 'did not find expected '-' indicator' error.
    Usually caused by missing or misplaced list item indicator.
    """
    if line_num <= 0 or line_num > len(lines):
        return False
    
    idx = line_num - 1
    line = lines[idx]
    
    # Check if this should be a list item but missing dash
    if idx > 0:
        prev_line = lines[idx - 1]
        
        # If previous line has a dash and current doesn't
        if re.match(r'^\s+-\s+', prev_line) and not re.match(r'^\s+-\s+', line):
            # Check if it's at wrong indentation
            curr_indent = len(line) - len(line.lstrip())
            prev_match = re.match(r'^(\s+)-\s+', prev_line)
            if prev_match:
                expected_indent = len(prev_match.group(1))
                if curr_indent != expected_indent:
                    # Fix indentation
                    diff = curr_indent - expected_indent
                    if diff > 0:
                        lines[idx] = line[diff:]
                        return True
                    elif diff < 0:
                        lines[idx] = ' ' * (-diff) + line
                        return True
    
    return False


def fix_file(filepath: Path, errors: List[Tuple[int, str]]) -> int:
    """Fix all errors in a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixes_applied = 0
        
        # Sort errors by line number (descending) to avoid offset issues
        for line_num, error_msg in sorted(errors, key=lambda x: x[0], reverse=True):
            fixed = False
            
            if 'mapping values are not allowed' in error_msg:
                fixed = fix_mapping_values_error(lines, line_num)
            elif 'did not find expected key' in error_msg:
                fixed = fix_expected_key_error(lines, line_num)
            elif "did not find expected '-' indicator" in error_msg:
                fixed = fix_expected_dash_error(lines, line_num)
            
            if fixed:
                fixes_applied += 1
        
        if fixes_applied > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        
        return fixes_applied
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return 0


def main():
    """Main function."""
    base_dir = Path('/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm')
    lint_output = base_dir / 'current-lint-output.txt'
    
    if not lint_output.exists():
        print(f"Lint output not found: {lint_output}")
        return 1
    
    print("Parsing lint output...")
    errors = parse_lint_output(str(lint_output))
    print(f"Found errors in {len(errors)} files")
    
    total_fixed = 0
    files_fixed = 0
    
    for filepath_str, file_errors in sorted(errors.items()):
        filepath = base_dir / filepath_str
        if not filepath.exists():
            continue
        
        fixes = fix_file(filepath, file_errors)
        if fixes > 0:
            files_fixed += 1
            total_fixed += fixes
            rel_path = filepath.relative_to(base_dir)
            print(f"✓ Fixed {rel_path} ({fixes} errors)")
    
    print(f"\nSummary: Fixed {total_fixed} errors in {files_fixed} files")
    return 0


if __name__ == '__main__':
    exit(main())
