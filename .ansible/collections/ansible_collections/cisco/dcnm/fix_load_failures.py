#!/usr/bin/env python3
"""
Fix YAML load-failure errors by correcting common indentation patterns.
This script specifically targets the patterns found by ansible-lint.
"""
import sys
import re
from pathlib import Path

def fix_file(file_path):
    """Fix YAML indentation issues in a single file."""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        fixed_lines = []
        i = 0
        modified = False
        
        while i < len(lines):
            line = lines[i]
            
            # Pattern 1: Lines starting with "    - " (4 spaces + dash) after "that:"
            # These should be "      - " (6 spaces + dash)
            if i > 0 and lines[i-1].strip() == 'that:':
                if line.startswith('    - '):
                    # This is correct indentation
                    fixed_lines.append(line)
                    i += 1
                    continue
            
            # Pattern 2: Lines starting with "    - " in assert blocks (wrong indent)
            # Should be "      - " when inside a that: block
            # Look back to find if we're in a that: block
            in_that_block = False
            for j in range(i-1, max(0, i-20), -1):
                if 'that:' in lines[j]:
                    in_that_block = True
                    break
                if lines[j].strip() and not lines[j].strip().startswith('-') and not lines[j].strip().startswith('#'):
                    # Check if this line is less indented (means we left the block)
                    if len(lines[j]) - len(lines[j].lstrip()) < len(lines[i]) - len(lines[i].lstrip()) - 2:
                        break
            
            if in_that_block and re.match(r'^    - ', line):
                # Change to 6-space indent
                fixed_lines.append('      ' + line[4:])
                modified = True
                i += 1
                continue
            
            # Pattern 3: Missing dash in list (line has key: value but should be - key: value)
            # This happens after seeing a list item, next line at same indent should also have dash
            if i > 0:
                prev_match = re.match(r'^(\s+)- (\w+):', lines[i-1])
                curr_match = re.match(r'^(\s+)(\w+):', line)
                if prev_match and curr_match:
                    prev_indent = len(prev_match.group(1))
                    curr_indent = len(curr_match.group(1))
                    # If current line has same indent as previous list item (after dash)
                    if curr_indent == prev_indent + 2:
                        # This should be a list item
                        fixed_lines.append(' ' * prev_indent + '- ' + line.lstrip())
                        modified = True
                        i += 1
                        continue
            
            # Pattern 4: Line has extra indent (starts with more spaces than expected)
            # Check for set_fact blocks with inconsistent indentation
            if 'set_fact:' in ''.join(lines[max(0, i-5):i]):
                # Look for variables with wrong indent
                match = re.match(r'^(\s+)(\w+):', line)
                if match and i > 0:
                    # Find the set_fact line
                    for j in range(i-1, max(0, i-10), -1):
                        if 'set_fact:' in lines[j]:
                            set_fact_indent = len(lines[j]) - len(lines[j].lstrip())
                            expected_indent = set_fact_indent + 2
                            current_indent = len(match.group(1))
                            if current_indent != expected_indent and current_indent > expected_indent:
                                # Fix the indent
                                fixed_lines.append(' ' * expected_indent + line.lstrip())
                                modified = True
                                i += 1
                                continue
                            break
            
            fixed_lines.append(line)
            i += 1
        
        if modified:
            with open(file_path, 'w') as f:
                f.writelines(fixed_lines)
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: fix_load_failures.py <file1> [file2] ...")
        sys.exit(1)
    
    fixed_count = 0
    for arg in sys.argv[1:]:
        path = Path(arg)
        if path.is_file():
            if fix_file(path):
                print(f"Fixed: {path}")
                fixed_count += 1
        elif path.is_dir():
            for yaml_file in path.rglob('*.yaml'):
                if fix_file(yaml_file):
                    print(f"Fixed: {yaml_file}")
                    fixed_count += 1
    
    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == '__main__':
    main()
