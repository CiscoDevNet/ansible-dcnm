#!/usr/bin/env python3
"""Fix 'did not find expected key' errors by correcting indentation."""

import subprocess
import re
from pathlib import Path

def get_errors_by_file():
    """Get all 'did not find expected key' errors."""
    result = subprocess.run(
        ['ansible-lint', '--profile=production'],
        capture_output=True,
        text=True,
        cwd='/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm'
    )
    
    output = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout + result.stderr)
    
    errors = {}
    for line in output.split('\n'):
        if 'did not find expected key' in line or "did not find expected '-' indicator" in line:
            match = re.match(r'([^:]+\.ya?ml):(\d+)', line)
            if match:
                filepath, line_num = match.groups()
                if filepath not in errors:
                    errors[filepath] = []
                errors[filepath].append(int(line_num))
    
    return errors

def fix_file(filepath, error_lines):
    """Fix indentation errors in a file."""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        fixed_count = 0
        
        # Sort in reverse to avoid line number shifts
        for line_num in sorted(error_lines, reverse=True):
            idx = line_num - 1
            if idx < 0 or idx >= len(lines):
                continue
            
            line = lines[idx]
            if not line.strip():
                continue
            
            # Get current indentation
            curr_indent = len(line) - len(line.lstrip())
            
            # Find previous non-empty line
            prev_idx = idx - 1
            while prev_idx >= 0 and not lines[prev_idx].strip():
                prev_idx -= 1
            
            if prev_idx < 0:
                continue
            
            prev_line = lines[prev_idx]
            prev_indent = len(prev_line) - len(prev_line.lstrip())
            
            # If current line starts with dash but has wrong indent
            if line.lstrip().startswith('-'):
                # Check if previous line also has dash (sibling list item)
                if prev_line.lstrip().startswith('-'):
                    if curr_indent != prev_indent:
                        lines[idx] = ' ' * prev_indent + line.lstrip()
                        fixed_count += 1
            # If previous line ends with colon, current should be +2
            elif prev_line.rstrip().endswith(':'):
                expected = prev_indent + 2
                if curr_indent != expected:
                    lines[idx] = ' ' * expected + line.lstrip()
                    fixed_count += 1
            # Check if over-indented
            elif curr_indent > prev_indent + 4:
                expected = prev_indent + 2
                lines[idx] = ' ' * expected + line.lstrip()
                fixed_count += 1
        
        if fixed_count > 0:
            with open(filepath, 'w') as f:
                f.writelines(lines)
            return fixed_count
        
        return 0
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return 0

base = Path('/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm')

print("Getting errors...")
errors = get_errors_by_file()
print(f"Found errors in {len(errors)} files")

total_fixed = 0
files_fixed = 0

for filepath_str, error_lines in sorted(errors.items()):
    filepath = base / filepath_str
    if not filepath.exists():
        continue
    
    fixed = fix_file(filepath, error_lines)
    if fixed > 0:
        files_fixed += 1
        total_fixed += fixed
        rel_path = filepath.relative_to(base)
        if files_fixed <= 20:
            print(f"✓ {rel_path} ({fixed} fixes)")

if files_fixed > 20:
    print(f"... and {files_fixed - 20} more files")

print(f"\nFixed {total_fixed} errors in {files_fixed} files")
