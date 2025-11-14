#!/usr/bin/env python3
"""Fix mapping values not allowed errors by fixing over-indentation."""

import subprocess
import re
from pathlib import Path

def get_mapping_errors():
    """Get all 'mapping values are not allowed' errors."""
    result = subprocess.run(
        ['ansible-lint', '--profile=production'],
        capture_output=True,
        text=True,
        cwd='/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm'
    )
    
    output = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout + result.stderr)
    
    errors = {}
    for line in output.split('\n'):
        if 'mapping values are not allowed' in line:
            match = re.match(r'([^:]+\.ya?ml):(\d+)', line)
            if match:
                filepath, line_num = match.groups()
                if filepath not in errors:
                    errors[filepath] = []
                errors[filepath].append(int(line_num))
    
    return errors

def fix_file_indentation(filepath, error_lines):
    """Fix over-indentation causing mapping errors."""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        fixed_count = 0
        
        # Sort in reverse
        for line_num in sorted(error_lines, reverse=True):
            idx = line_num - 1
            if idx < 0 or idx >= len(lines):
                continue
            
            line = lines[idx]
            if not line.strip() or ':' not in line:
                continue
            
            curr_indent = len(line) - len(line.lstrip())
            
            # Find previous sibling key (same level, also has colon)
            prev_idx = idx - 1
            while prev_idx >= 0:
                prev_line = lines[prev_idx]
                if prev_line.strip() and ':' in prev_line and not prev_line.strip().startswith('-'):
                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                    
                    # If current line is over-indented compared to sibling
                    if curr_indent > prev_indent:
                        lines[idx] = ' ' * prev_indent + line.lstrip()
                        fixed_count += 1
                        break
                
                prev_idx -= 1
                # Stop if we've gone too far back
                if idx - prev_idx > 10:
                    break
        
        if fixed_count > 0:
            with open(filepath, 'w') as f:
                f.writelines(lines)
            return fixed_count
        
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 0

base = Path('/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm')

print("Getting mapping value errors...")
errors = get_mapping_errors()
print(f"Found errors in {len(errors)} files")

total_fixed = 0
files_fixed = 0

for filepath_str, error_lines in sorted(errors.items()):
    filepath = base / filepath_str
    if not filepath.exists():
        continue
    
    fixed = fix_file_indentation(filepath, error_lines)
    if fixed > 0:
        files_fixed += 1
        total_fixed += fixed
        rel_path = filepath.relative_to(base)
        print(f"✓ {rel_path} ({fixed} fixes)")

print(f"\nFixed {total_fixed} errors in {files_fixed} files")
