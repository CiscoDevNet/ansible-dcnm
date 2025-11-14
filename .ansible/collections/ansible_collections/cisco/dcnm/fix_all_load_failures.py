#!/usr/bin/env python3
"""
Fix all YAML load-failure errors reported by ansible-lint.
This script reads the ansible-lint output and fixes the specific errors.
"""
import subprocess
import re
from pathlib import Path

def run_ansible_lint():
    """Run ansible-lint and return list of files with errors."""
    result = subprocess.run(
        ['ansible-lint', '--profile=production', '--tags', 'load-failure', '--parseable'],
        capture_output=True,
        text=True,
        cwd='/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm'
    )
    
    errors = {}
    for line in result.stdout.splitlines() + result.stderr.splitlines():
        match = re.match(r'([^:]+):(\d+):(\d+):', line)
        if match:
            file_path = match.group(1)
            line_num = int(match.group(2))
            if file_path not in errors:
                errors[file_path] = []
            errors[file_path].append(line_num)
    
    return errors

def fix_assert_indentation(file_path, error_lines):
    """Fix assert block indentation issues."""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    modified = False
    for line_num in error_lines:
        if line_num <= len(lines):
            idx = line_num - 1
            line = lines[idx]
            
            # Check if it's an assert line that needs fixing
            if line.startswith('    - '):
                # Look back to find if we're in a 'that:' block
                for i in range(idx - 1, max(0, idx - 10), -1):
                    if 'that:' in lines[i]:
                        # Fix: change from 4-space to 6-space indent
                        lines[idx] = '      ' + line[4:]
                        modified = True
                        break
    
    if modified:
        with open(file_path, 'w') as f:
            f.writelines(lines)
        return True
    return False

def main():
    print("Running ansible-lint to find errors...")
    errors = run_ansible_lint()
    
    print(f"\nFound {len(errors)} files with errors")
    
    fixed_count = 0
    for file_path, error_lines in errors.items():
        full_path = Path('/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm') / file_path
        if full_path.exists():
            if fix_assert_indentation(full_path, error_lines):
                print(f"Fixed: {file_path}")
                fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")
    
    # Run ansible-lint again to see remaining errors
    print("\nRunning ansible-lint again...")
    subprocess.run(['ansible-lint', '--profile=production', '--tags', 'load-failure'],
                   cwd='/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm')

if __name__ == '__main__':
    main()
