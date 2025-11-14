#!/usr/bin/env python3
import re
import sys

def fix_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    modified = False
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check for unnamed assert/debug/meta/set_fact
        if re.match(r'^(\s+)- (ansible\.builtin\.)?(assert|debug|meta|set_fact):', line):
            indent = re.match(r'^(\s+)', line).group(1)
            module = re.search(r'(assert|debug|meta|set_fact)', line).group(1)
            # Add name before the task
            name_map = {
                'assert': 'Assert',
                'debug': 'Debug',
                'meta': 'Meta',
                'set_fact': 'Set fact'
            }
            lines.insert(i, f'{indent}- name: {name_map[module]}\n')
            modified = True
            i += 1  # Skip the newly inserted line
        i += 1
    
    if modified:
        with open(filepath, 'w') as f:
            f.writelines(lines)
        print(f"Fixed: {filepath}")
        return True
    return False

if __name__ == '__main__':
    import subprocess
    # Get files with name[missing] violations
    result = subprocess.run(
        ['ansible-lint', '--parseable', '--nocolor'],
        capture_output=True, text=True, cwd='.'
    )
    
    files_to_fix = set()
    for line in result.stdout.split('\n'):
        if 'name[missing]' in line:
            filepath = line.split(':')[0]
            if filepath:
                files_to_fix.add(filepath)
    
    for filepath in sorted(files_to_fix):
        try:
            fix_file(filepath)
        except Exception as e:
            print(f"Error fixing {filepath}: {e}")
