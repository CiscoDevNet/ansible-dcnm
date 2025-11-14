#!/usr/bin/env python3
"""
Comprehensive ansible-lint fixer for DCNM collection.
Fixes: truthy, indentation, empty-lines, trailing-spaces, colons, deprecated includes, etc.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


def fix_truthy_values(content: str) -> str:
    """Fix yaml[truthy] violations - convert True/False to true/false."""
    # Match True/False as values (not in strings)
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        # Don't modify if it's in a comment or string
        if '#' in line:
            comment_idx = line.index('#')
            before_comment = line[:comment_idx]
            comment = line[comment_idx:]
            # Fix only before comment
            before_comment = re.sub(r':\s+(True|False)\s*$', lambda m: f': {m.group(1).lower()}', before_comment)
            before_comment = re.sub(r':\s+(True|False)(\s*[,\]}])', lambda m: f': {m.group(1).lower()}{m.group(2)}', before_comment)
            line = before_comment + comment
        else:
            line = re.sub(r':\s+(True|False)\s*$', lambda m: f': {m.group(1).lower()}', line)
            line = re.sub(r':\s+(True|False)(\s*[,\]}])', lambda m: f': {m.group(1).lower()}{m.group(2)}', line)

        fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def fix_trailing_spaces(content: str) -> str:
    """Fix yaml[trailing-spaces] violations."""
    lines = content.split('\n')
    return '\n'.join(line.rstrip() for line in lines)


def fix_empty_lines(content: str) -> str:
    """Fix yaml[empty-lines] violations - max 2 consecutive empty lines."""
    # Replace 3+ consecutive newlines with 2
    while '\n\n\n\n' in content:
        content = content.replace('\n\n\n\n', '\n\n\n')

    return content


def fix_colon_spacing(content: str) -> str:
    """Fix yaml[colons] violations - exactly one space after colon."""
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        # Find colons not in strings
        if ':' in line and not line.strip().startswith('#'):
            # Replace multiple spaces after colon with single space
            # But preserve indentation before the key
            parts = line.split(':', 1)
            if len(parts) == 2:
                key_part = parts[0]
                value_part = parts[1]
                # Remove leading spaces from value part and add exactly one
                value_part = ' ' + value_part.lstrip() if value_part.strip() else value_part
                line = key_part + ':' + value_part

        fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def fix_deprecated_include(content: str) -> str:
    """Fix deprecated 'include' module - replace with 'include_tasks'."""
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        # Replace include: with include_tasks:
        if re.match(r'^(\s*)include:\s*', line):
            line = re.sub(r'^(\s*)include:\s*', r'\1ansible.builtin.include_tasks: ', line)
        # Handle old-style include directive
        elif re.match(r'^(\s*)-\s+include:\s*', line):
            line = re.sub(r'^(\s*)-\s+include:\s*', r'\1- ansible.builtin.include_tasks: ', line)

        fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def fix_fqcn_builtins(content: str) -> str:
    """Fix fqcn[action-core] violations - add ansible.builtin prefix."""
    # Common builtin modules that need FQCN
    builtins = ['include_tasks', 'import_tasks', 'set_fact', 'debug', 'assert',
                'pause', 'fail', 'command', 'shell', 'copy', 'template', 'file']

    for builtin in builtins:
        # Replace module: with ansible.builtin.module:
        pattern = rf'^(\s*){builtin}:\s*'
        replacement = rf'\1ansible.builtin.{builtin}: '
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

        # Handle task format
        pattern = rf'^(\s*-\s+){builtin}:\s*'
        replacement = rf'\1ansible.builtin.{builtin}: '
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    return content


def fix_brackets_spacing(content: str) -> str:
    """Fix yaml[brackets] violations - remove extra spaces in brackets."""
    # Fix [ item ] -> [item]
    content = re.sub(r'\[\s+', '[', content)
    content = re.sub(r'\s+\]', ']', content)

    return content


def fix_line_length_simple(content: str, max_length: int = 160) -> str:
    """
    Fix yaml[line-length] violations for simple cases (long strings).
    This is conservative and only breaks obvious long strings.
    """
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        if len(line) <= max_length:
            fixed_lines.append(line)
            continue

        # Only try to fix if it's a simple key: value line
        if ':' in line and not line.strip().startswith('-'):
            match = re.match(r'^(\s*)(\w+):\s*(.+)$', line)
            if match:
                indent, key, value = match.groups()
                if len(value) > max_length - len(indent) - len(key) - 2:
                    # Skip for now - manual intervention needed
                    pass

        fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def fix_indentation_pattern(content: str, expected: int, found: int, line_num: int) -> str:
    """Fix specific indentation issue at a given line."""
    lines = content.split('\n')

    if 0 < line_num <= len(lines):
        idx = line_num - 1
        line = lines[idx]

        # Calculate current indentation
        current_indent = len(line) - len(line.lstrip())

        if current_indent == found:
            # Replace the indentation
            diff = expected - found
            if diff > 0:
                # Add spaces
                lines[idx] = ' ' * diff + line
            elif diff < 0:
                # Remove spaces
                lines[idx] = line[-diff:]

    return '\n'.join(lines)


def process_file(filepath: Path, fixes_to_apply: List[str]) -> Tuple[bool, int]:
    """Process a single file and apply requested fixes."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        fix_count = 0

        # Apply fixes in order
        if 'truthy' in fixes_to_apply:
            new_content = fix_truthy_values(content)
            if new_content != content:
                fix_count += content.count('True') + content.count('False')
                content = new_content

        if 'trailing-spaces' in fixes_to_apply:
            new_content = fix_trailing_spaces(content)
            if new_content != content:
                fix_count += 1
                content = new_content

        if 'empty-lines' in fixes_to_apply:
            new_content = fix_empty_lines(content)
            if new_content != content:
                fix_count += 1
                content = new_content

        if 'colons' in fixes_to_apply:
            new_content = fix_colon_spacing(content)
            if new_content != content:
                fix_count += 1
                content = new_content

        if 'deprecated-include' in fixes_to_apply:
            new_content = fix_deprecated_include(content)
            if new_content != content:
                fix_count += 1
                content = new_content

        if 'fqcn' in fixes_to_apply:
            new_content = fix_fqcn_builtins(content)
            if new_content != content:
                fix_count += 1
                content = new_content

        if 'brackets' in fixes_to_apply:
            new_content = fix_brackets_spacing(content)
            if new_content != content:
                fix_count += 1
                content = new_content

        # Write back if changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, fix_count

        return False, 0

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False, 0


def main():
    """Main function to process all YAML files."""
    base_dir = Path('/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm')

    # Fixes to apply
    fixes = [
        'truthy',
        'trailing-spaces',
        'empty-lines',
        'colons',
        'deprecated-include',
        'fqcn',
        'brackets'
    ]

    # Find all YAML files
    yaml_files = []
    for pattern in ['**/*.yaml', '**/*.yml']:
        yaml_files.extend(base_dir.glob(pattern))

    print(f"Found {len(yaml_files)} YAML files to process")
    print(f"Applying fixes: {', '.join(fixes)}")
    print()

    total_fixed = 0
    total_changes = 0

    for yaml_file in sorted(yaml_files):
        # Skip hidden directories
        if any(part.startswith('.') for part in yaml_file.parts):
            continue

        changed, fix_count = process_file(yaml_file, fixes)
        if changed:
            total_fixed += 1
            total_changes += fix_count
            rel_path = yaml_file.relative_to(base_dir)
            print(f"✓ Fixed {rel_path} ({fix_count} changes)")

    print()
    print(f"Summary: Fixed {total_fixed} files with {total_changes} total changes")


if __name__ == '__main__':
    main()
