#!/usr/bin/env python3
"""Fix 'did not find expected key' YAML errors."""

import re
import subprocess
from pathlib import Path
from collections import defaultdict


def get_specific_errors():
    """Get specific 'did not find expected key' errors from ansible-lint."""
    result = subprocess.run(
        ['ansible-lint', '--profile=production'],
        capture_output=True,
        text=True,
        cwd='/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm'
    )
    
    # Strip ANSI codes
    output = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout + result.stderr)
    
    errors = defaultdict(list)
    
    # Find "did not find expected key" errors
    for line in output.split('\n'):
        if 'did not find expected key' in line:
            match = re.match(r'([^:]+\.ya?ml):(\d+):', line)
            if match:
                filepath, line_num = match.groups()
                errors[filepath].append(int(line_num))
    
    return errors


def fix_expected_key_error(lines, line_num):
    """Fix indentation for 'did not find expected key' error."""
    idx = line_num - 1
    if idx < 0 or idx >= len(lines):
        return False
    
    line = lines[idx]
    if not line.strip():
        return False
    
    curr_indent = len(line) - len(line.lstrip())
    
    # Find previous non-empty, non-comment line
    prev_idx = idx - 1
    while prev_idx >= 0:
        prev_line = lines[prev_idx]
        if prev_line.strip() and not prev_line.strip().startswith('#'):
            break
        prev_idx -= 1
    
    if prev_idx < 0:
        return False
    
    prev_line = lines[prev_idx]
    prev_indent = len(prev_line) - len(prev_line.lstrip())
    
    # Check if line is over-indented
    # If previous line ends with ':', current should be indented by 2
    if prev_line.rstrip().endswith(':'):
        expected = prev_indent + 2
    # If previous line has a dash, this might be same list or child
    elif '-' in prev_line:
        # Could be same list level or child dict
        if ':' in line:  # It's a dict key
            # Should be indented from the dash
            match = re.match(r'^(\s+)-', prev_line)
            if match:
                expected = len(match.group(1)) + 2
            else:
                expected = prev_indent + 2
        else:
            expected = prev_indent
    else:
        # Sibling key - same level
        expected = prev_indent
    
    if curr_indent != expected:
        lines[idx] = ' ' * expected + line.lstrip()
        return True
    
    return False


def fix_file(filepath, line_numbers):
    """Fix all expected key errors in a file."""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        fixed_count = 0
        
        # Sort in reverse to avoid line number shifts
        for line_num in sorted(line_numbers, reverse=True):
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
    
    print("Getting expected key errors...")
    errors = get_specific_errors()
    print(f"Found errors in {len(errors)} files")
    
    total_fixed = 0
    files_fixed = 0
    
    for filepath_str, line_numbers in sorted(errors.items()):
        filepath = base / filepath_str
        if not filepath.exists():
            continue
        
        fixed = fix_file(filepath, line_numbers)
        if fixed > 0:
            files_fixed += 1
            total_fixed += fixed
            rel_path = filepath.relative_to(base)
            print(f"✓ {rel_path} ({fixed} fixes)")
    
    print(f"\nFixed {total_fixed} errors in {files_fixed} files")


if __name__ == '__main__':
    main()
