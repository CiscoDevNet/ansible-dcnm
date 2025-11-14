#!/usr/bin/env python3
"""
Fix ansible-lint name violations:
- name[play]: Add names to plays
- name[casing]: Capitalize task/handler names
- name[missing]: Add names to tasks
"""

import re
import sys
from pathlib import Path
from typing import List


def capitalize_name(content: str) -> str:
    """Fix name[casing] - capitalize task names."""
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        # Match "name: some text" where text starts with lowercase
        match = re.match(r'^(\s*)name:\s+([a-z].*)', line)
        if match:
            indent = match.group(1)
            name_text = match.group(2)
            # Capitalize first letter
            capitalized = name_text[0].upper() + name_text[1:]
            line = f"{indent}name: {capitalized}"

        fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def add_play_names(content: str) -> str:
    """Fix name[play] - add names to plays."""
    lines = content.split('\n')
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Detect play start: "---" or "- hosts:"
        if line.strip() == '---' and i + 1 < len(lines):
            fixed_lines.append(line)
            i += 1
            next_line = lines[i]

            # Check if next line is "- hosts:" without a name
            if re.match(r'^\s*-\s+hosts:', next_line):
                # Check if there's a name in the following lines
                has_name = False
                for j in range(i+1, min(i+5, len(lines))):
                    if re.match(r'^\s+name:', lines[j]):
                        has_name = True
                        break
                    if re.match(r'^\s*-\s+', lines[j]):  # New task/play
                        break

                if not has_name:
                    # Extract hosts value for a descriptive name
                    hosts_match = re.search(r'hosts:\s+(.+)', next_line)
                    hosts_val = hosts_match.group(1).strip() if hosts_match else "all"
                    indent = re.match(r'^(\s*)', next_line).group(1)
                    name_line = f"{indent}  name: Play for {hosts_val}"
                    fixed_lines.append(name_line)

            continue

        # Also handle plays without --- prefix
        if re.match(r'^\s*-\s+hosts:', line):
            # Check if there's a name
            has_name = False
            for j in range(i+1, min(i+5, len(lines))):
                if re.match(r'^\s+name:', lines[j]):
                    has_name = True
                    break
                if re.match(r'^\s*-\s+', lines[j]):  # New task/play
                    break

            if not has_name:
                hosts_match = re.search(r'hosts:\s+(.+)', line)
                hosts_val = hosts_match.group(1).strip() if hosts_match else "all"
                indent = re.match(r'^(\s*)', line).group(1)
                fixed_lines.append(line)
                name_line = f"{indent}  name: Play for {hosts_val}"
                fixed_lines.append(name_line)
                i += 1
                continue

        fixed_lines.append(line)
        i += 1

    return '\n'.join(fixed_lines)


def add_task_names(content: str) -> str:
    """Fix name[missing] - add names to tasks."""
    lines = content.split('\n')
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Detect task without name: "- module:"
        if re.match(r'^\s*-\s+\w+:\s*', line) and 'name:' not in line:
            # Check if next line is 'name:'
            has_name = False
            if i + 1 < len(lines):
                next_line = lines[i+1]
                if re.match(r'^\s+name:', next_line):
                    has_name = True

            if not has_name:
                # Extract module name
                module_match = re.search(r'-\s+(\w+):', line)
                if module_match:
                    module_name = module_match.group(1)
                    # Common modules to name
                    if module_match and module_name in ['include_tasks', 'import_tasks', 'ansible.builtin.include_tasks', 'ansible.builtin.import_tasks']:
                        # Try to extract filename
                        file_match = re.search(r':\s+(.+\.ya?ml)', line)
                        if file_match:
                            filename = file_match.group(1).strip()
                            indent = re.match(r'^(\s*)-', line).group(1)
                            name_line = f"{indent}  name: Include {filename}"
                            fixed_lines.append(line)
                            fixed_lines.append(name_line)
                            i += 1
                            continue

        fixed_lines.append(line)
        i += 1

    return '\n'.join(fixed_lines)


def process_file(filepath: Path) -> tuple:
    """Process a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Apply fixes
        content = capitalize_name(content)
        content = add_play_names(content)
        content = add_task_names(content)

        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            # Count number of changes
            changes = sum(1 for a, b in zip(original_content.split('\n'), content.split('\n')) if a != b)
            return True, changes

        return False, 0

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False, 0


def main():
    """Main function."""
    base_dir = Path('/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm')

    # Find all YAML files
    yaml_files = []
    for pattern in ['**/*.yaml', '**/*.yml']:
        yaml_files.extend(base_dir.glob(pattern))

    print(f"Processing {len(yaml_files)} YAML files for naming fixes...")

    total_fixed = 0
    total_changes = 0

    for yaml_file in sorted(yaml_files):
        # Skip hidden directories
        if any(part.startswith('.') for part in yaml_file.parts):
            continue

        changed, change_count = process_file(yaml_file)
        if changed:
            total_fixed += 1
            total_changes += change_count
            rel_path = yaml_file.relative_to(base_dir)
            print(f"✓ Fixed {rel_path} ({change_count} changes)")

    print()
    print(f"Summary: Fixed {total_fixed} files with {total_changes} naming changes")
    return 0


if __name__ == '__main__':
    sys.exit(main())
