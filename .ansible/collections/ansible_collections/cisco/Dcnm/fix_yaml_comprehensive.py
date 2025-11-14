#!/usr/bin/env python3
"""Fix YAML syntax errors from ansible-lint."""

import re
import subprocess
from pathlib import Path
from collections import defaultdict


def get_lint_errors():
    """Run ansible-lint and extract errors."""
    result = subprocess.run(
        ['ansible-lint', '--profile=production'],
        capture_output=True,
        text=True,
        cwd='/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm'
    )
    
    # Strip ANSI codes
    output = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout + result.stderr)
    
    errors = defaultdict(list)
    
    # Parse errors: filepath.yaml:line:col error message
    for line in output.split('\n'):
        match = re.match(r'([^:]+\.ya?ml):(\d+):(\d+)\s+(.+)$', line)
        if match:
            filepath, line_num, col, error_msg = match.groups()
            errors[filepath].append((int(line_num), int(col), error_msg))
    
    return errors


def fix_file(filepath, file_errors):
    """Fix errors in a single file."""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        original = ''.join(lines)
        changes = 0
        
        # Sort by line number descending to avoid offset issues
        for line_num, col, error in sorted(file_errors, key=lambda x: x[0], reverse=True):
            idx = line_num - 1
            if idx < 0 or idx >= len(lines):
                continue
            
            line = lines[idx]
            
            # Fix: mapping values are not allowed in this context
            if 'mapping values are not allowed' in error:
                # Usually unquoted string with colon
                # Pattern: key: {{ var }}: text or key: value: text
                if '{{' in line and '}}' in line:
                    # Quote the entire value after the key
                    match = re.match(r'^(\s+)(\w+):\s*(.+)$', line)
                    if match:
                        indent, key, value = match.groups()
                        value = value.rstrip()
                        if not (value.startswith('"') or value.startswith("'")):
                            lines[idx] = f'{indent}{key}: "{value}"\n'
                            changes += 1
            
            # Fix: did not find expected key
            elif 'did not find expected key' in error:
                # Usually over-indented line
                if idx > 0:
                    curr_indent = len(line) - len(line.lstrip())
                    # Find previous non-empty line
                    prev_idx = idx - 1
                    while prev_idx >= 0 and not lines[prev_idx].strip():
                        prev_idx -= 1
                    if prev_idx >= 0:
                        prev_line = lines[prev_idx]
                        prev_indent = len(prev_line) - len(prev_line.lstrip())
                        
                        # If over-indented by more than 2 spaces
                        if curr_indent > prev_indent + 4:
                            # Reduce to prev + 2
                            correct_indent = prev_indent + 2
                            lines[idx] = ' ' * correct_indent + line.lstrip()
                            changes += 1
            
            # Fix: did not find expected '-' indicator  
            elif "did not find expected '-' indicator" in error:
                # Usually list item at wrong indentation
                if idx > 0:
                    # Find previous list item
                    prev_idx = idx - 1
                    while prev_idx >= 0:
                        if re.match(r'^\s+-\s+', lines[prev_idx]):
                            prev_match = re.match(r'^(\s+)-', lines[prev_idx])
                            expected_indent = len(prev_match.group(1))
                            
                            curr_indent = len(line) - len(line.lstrip())
                            if curr_indent != expected_indent:
                                lines[idx] = ' ' * expected_indent + line.lstrip()
                                changes += 1
                            break
                        prev_idx -= 1
        
        if changes > 0:
            with open(filepath, 'w') as f:
                f.writelines(lines)
            return changes
        
        return 0
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return 0


def main():
    base = Path('/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm')
    
    print("Getting lint errors...")
    errors = get_lint_errors()
    print(f"Found errors in {len(errors)} files")
    
    total_changes = 0
    files_fixed = 0
    
    for filepath_str, file_errors in sorted(errors.items()):
        filepath = base / filepath_str
        if not filepath.exists():
            continue
        
        changes = fix_file(filepath, file_errors)
        if changes > 0:
            files_fixed += 1
            total_changes += changes
            rel_path = filepath.relative_to(base)
            print(f"✓ Fixed {rel_path} ({changes} changes)")
    
    print(f"\nFixed {total_changes} errors in {files_fixed} files")


if __name__ == '__main__':
    main()
