#!/usr/bin/env python3
"""
Fix common YAML indentation issues found by ansible-lint load-failure errors.
"""
import re
import sys
from pathlib import Path

def fix_list_indentation(content):
    """Fix list items that have incorrect indentation (missing dash or wrong indent)."""
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Pattern: spaces followed by "- " then key: value
        # If next line doesn't start with proper dash but should be list item
        if i < len(lines) - 1:
            current_match = re.match(r'^(\s+)(- \w+:)', line)
            next_line = lines[i + 1]
            next_match = re.match(r'^(\s+)(\w+:)', next_line)
            
            if current_match and next_match:
                current_indent = len(current_match.group(1))
                next_indent = len(next_match.group(1))
                
                # If next line has same indent as current (after dash), it should have a dash
                if next_indent == current_indent + 2:
                    # Check if it's a continuation of dict or should be new list item
                    # by looking at previous patterns
                    pass  # Keep as is, it's dict continuation
                elif next_indent == current_indent:
                    # Should be a list item
                    fixed_lines.append(line)
                    i += 1
                    continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_assert_indentation(content):
    """Fix assert 'that' blocks where list items lose their dash."""
    lines = content.split('\n')
    fixed_lines = []
    in_assert_that = False
    that_indent = 0
    
    for i, line in enumerate(lines):
        # Detect 'that:' in assert block
        if re.match(r'^(\s+)that:\s*$', line):
            in_assert_that = True
            that_indent = len(re.match(r'^(\s+)', line).group(1))
            fixed_lines.append(line)
            continue
        
        if in_assert_that:
            # Check if we've left the that block
            if line.strip() and not line.strip().startswith('#'):
                match = re.match(r'^(\s+)', line)
                if match:
                    line_indent = len(match.group(1))
                    if line_indent <= that_indent:
                        in_assert_that = False
                        fixed_lines.append(line)
                        continue
                    
                    # Expected indent for list items under 'that:'
                    expected_indent = that_indent + 2
                    
                    # If line doesn't start with dash but should
                    if line_indent == expected_indent and not line.strip().startswith('-'):
                        # Add the dash
                        fixed_line = ' ' * expected_indent + '- ' + line.strip()
                        fixed_lines.append(fixed_line)
                        continue
            elif not line.strip():
                # Empty line might end the block
                in_assert_that = False
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_config_indentation(content):
    """Fix config block indentation issues."""
    lines = content.split('\n')
    fixed_lines = []
    in_config = False
    config_indent = 0
    
    for i, line in enumerate(lines):
        # Detect 'config:' line
        if re.match(r'^(\s+)config:\s*$', line):
            in_config = True
            config_indent = len(re.match(r'^(\s+)', line).group(1))
            fixed_lines.append(line)
            continue
        
        if in_config:
            # Check if we've left the config block
            if line.strip() and not line.strip().startswith('#'):
                match = re.match(r'^(\s+)', line)
                if match:
                    line_indent = len(match.group(1))
                    if line_indent <= config_indent:
                        in_config = False
                        fixed_lines.append(line)
                        continue
                    
                    # List items under config should be at config_indent + 2
                    list_indent = config_indent + 2
                    dict_indent = config_indent + 4
                    
                    if line.strip().startswith('- '):
                        # It's a list item, check indent
                        if line_indent != list_indent:
                            fixed_line = ' ' * list_indent + line.strip()
                            fixed_lines.append(fixed_line)
                            continue
                    elif line_indent < list_indent:
                        # Might be missing dash
                        if ':' in line:
                            fixed_line = ' ' * list_indent + '- ' + line.strip()
                            fixed_lines.append(fixed_line)
                            continue
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_set_fact_indentation(content):
    """Fix set_fact blocks with inconsistent indentation."""
    lines = content.split('\n')
    fixed_lines = []
    in_set_fact = False
    set_fact_indent = 0
    
    for i, line in enumerate(lines):
        # Detect 'ansible.builtin.set_fact:' or 'set_fact:'
        if re.match(r'^(\s+)(?:ansible\.builtin\.)?set_fact:\s*$', line):
            in_set_fact = True
            set_fact_indent = len(re.match(r'^(\s+)', line).group(1))
            fixed_lines.append(line)
            continue
        
        if in_set_fact:
            # Check if we've left the set_fact block
            if line.strip() and not line.strip().startswith('#'):
                match = re.match(r'^(\s+)', line)
                if match:
                    line_indent = len(match.group(1))
                    if line_indent <= set_fact_indent:
                        in_set_fact = False
                        fixed_lines.append(line)
                        continue
                    
                    # All variables should be at set_fact_indent + 2
                    expected_indent = set_fact_indent + 2
                    
                    if ':' in line and line_indent != expected_indent:
                        # Fix the indentation
                        fixed_line = ' ' * expected_indent + line.strip()
                        fixed_lines.append(fixed_line)
                        continue
            elif not line.strip():
                # Empty line ends the block
                in_set_fact = False
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def main():
    if len(sys.argv) < 2:
        print("Usage: fix_yaml_indentation.py <file_or_directory>")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    
    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = list(path.rglob('*.yaml')) + list(path.rglob('*.yml'))
    else:
        print(f"Error: {path} not found")
        sys.exit(1)
    
    for file_path in files:
        try:
            content = file_path.read_text()
            original = content
            
            # Apply fixes in sequence
            content = fix_set_fact_indentation(content)
            content = fix_assert_indentation(content)
            content = fix_config_indentation(content)
            content = fix_list_indentation(content)
            
            if content != original:
                file_path.write_text(content)
                print(f"Fixed: {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

if __name__ == '__main__':
    main()
