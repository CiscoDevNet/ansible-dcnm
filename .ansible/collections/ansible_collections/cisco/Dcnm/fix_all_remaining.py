#!/usr/bin/env python3
"""Fix all remaining ansible-lint errors."""

import re
import subprocess
from pathlib import Path
from collections import defaultdict

def get_all_errors():
    """Run ansible-lint and extract all errors."""
    result = subprocess.run(
        ['ansible-lint', '--profile=production'],
        capture_output=True,
        text=True,
        cwd='/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm'
    )
    
    # Strip ANSI codes
    output = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout + result.stderr)
    
    errors = defaultdict(list)
    
    for line in output.split('\n'):
        match = re.match(r'([^:]+\.ya?ml):(\d+)(?::(\d+))?\s+(.+)$', line)
        if match:
            filepath, line_num, col, error_msg = match.groups()
            errors[filepath].append((int(line_num), int(col) if col else 0, error_msg))
    
    return errors

def fix_mapping_values_error(lines, line_num):
    """Fix 'mapping values are not allowed' - usually unquoted string with colons."""
    idx = line_num - 1
    if idx < 0 or idx >= len(lines):
        return False
    
    line = lines[idx]
    
    # Check if this is an assert statement that needs restructuring
    if 'that:' in line and ('{{' in line or ':' in line.split('that:')[1] if 'that:' in line else False):
        # This is malformed, likely "that: value" should be on separate line
        return False
    
    # Quote unquoted strings with colons
    if '{{' in line and '}}' in line and not line.strip().startswith('#'):
        match = re.match(r'^(\s+)(\w+):\s*(.+)$', line)
        if match:
            indent, key, value = match.groups()
            value = value.strip()
            if not (value.startswith('"') or value.startswith("'")):
                lines[idx] = f'{indent}{key}: "{value}"\n'
                return True
    
    return False

def fix_expected_key_error(lines, line_num):
    """Fix 'did not find expected key' - indentation issue."""
    idx = line_num - 1
    if idx < 0 or idx >= len(lines):
        return False
    
    line = lines[idx]
    if not line.strip():
        return False
    
    curr_indent = len(line) - len(line.lstrip())
    
    # Find previous non-empty line
    prev_idx = idx - 1
    while prev_idx >= 0 and not lines[prev_idx].strip():
        prev_idx -= 1
    
    if prev_idx < 0:
        return False
    
    prev_line = lines[prev_idx]
    prev_indent = len(prev_line) - len(prev_line.lstrip())
    
    # If previous line ends with colon, current should be indented +2
    if prev_line.rstrip().endswith(':'):
        expected = prev_indent + 2
        if curr_indent != expected:
            lines[idx] = ' ' * expected + line.lstrip()
            return True
    # If over-indented
    elif curr_indent > prev_indent + 4:
        expected = prev_indent + 2
        lines[idx] = ' ' * expected + line.lstrip()
        return True
    
    return False

def fix_file(filepath, file_errors):
    """Fix all errors in a single file."""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        fixed_count = 0
        
        # Sort by line number descending to avoid offset issues
        for line_num, col, error_msg in sorted(file_errors, key=lambda x: x[0], reverse=True):
            if 'mapping values are not allowed' in error_msg:
                if fix_mapping_values_error(lines, line_num):
                    fixed_count += 1
            elif 'did not find expected key' in error_msg:
                if fix_expected_key_error(lines, line_num):
                    fixed_count += 1
        
        if fixed_count > 0:
            with open(filepath, 'w') as f:
                f.writelines(lines)
            return fixed_count
        
        return 0
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return 0

def main():
    base = Path('/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm')
    
    print("Getting all lint errors...")
    all_errors = get_all_errors()
    print(f"Found errors in {len(all_errors)} files")
    
    total_fixed = 0
    files_fixed = 0
    
    for filepath_str, file_errors in sorted(all_errors.items()):
        filepath = base / filepath_str
        if not filepath.exists():
            continue
        
        fixed = fix_file(filepath, file_errors)
        if fixed > 0:
            files_fixed += 1
            total_fixed += fixed
            rel_path = filepath.relative_to(base)
            if files_fixed <= 30:  # Print first 30
                print(f"✓ {rel_path} ({fixed} fixes)")
    
    if files_fixed > 30:
        print(f"... and {files_fixed - 30} more files")
    
    print(f"\nFixed {total_fixed} errors in {files_fixed} files")

if __name__ == '__main__':
    main()
