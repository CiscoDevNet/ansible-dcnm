#!/usr/bin/env python3
"""
Fix YAML indentation violations reported by ansible-lint.
Parses lint output and fixes specific indentation issues.
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple


def parse_lint_output(lint_file: str) -> List[Dict]:
    """Parse ansible-lint output to extract indentation violations."""
    violations = []

    with open(lint_file, 'r') as f:
        content = f.read()

    # Match indentation violations
    # Format: yaml[indentation]: Wrong indentation: expected X but found Y
    # path/to/file.yaml:line_number
    pattern = r'yaml\[indentation\]: Wrong indentation: expected (\d+) but found (\d+)\n([^\n]+):(\d+)'

    for match in re.finditer(pattern, content):
        expected = int(match.group(1))
        found = int(match.group(2))
        filepath = match.group(3)
        line_num = int(match.group(4))

        violations.append({
            'file': filepath,
            'line': line_num,
            'expected': expected,
            'found': found
        })

    return violations


def fix_indentation_in_file(filepath: Path, fixes: List[Dict]) -> int:
    """Apply indentation fixes to a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        fixed_count = 0

        # Sort fixes by line number (descending) to avoid offset issues
        fixes_sorted = sorted(fixes, key=lambda x: x['line'], reverse=True)

        for fix in fixes_sorted:
            line_idx = fix['line'] - 1  # Convert to 0-indexed

            if line_idx < 0 or line_idx >= len(lines):
                continue

            line = lines[line_idx]

            # Calculate current indentation
            current_indent = len(line) - len(line.lstrip())

            # Only fix if current indentation matches what lint reported
            if current_indent == fix['found']:
                diff = fix['expected'] - fix['found']

                if diff > 0:
                    # Add spaces
                    lines[line_idx] = ' ' * diff + line
                    fixed_count += 1
                elif diff < 0:
                    # Remove spaces
                    spaces_to_remove = -diff
                    if line[:spaces_to_remove].strip() == '':  # Only remove if they're spaces
                        lines[line_idx] = line[spaces_to_remove:]
                        fixed_count += 1

        if fixed_count > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)

        return fixed_count

    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return 0


def main():
    """Main function."""
    base_dir = Path('/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm')
    lint_file = Path('/Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/last lint failures')

    if not lint_file.exists():
        print(f"Lint file not found: {lint_file}")
        return 1

    print("Parsing lint output...")
    violations = parse_lint_output(str(lint_file))
    print(f"Found {len(violations)} indentation violations")

    # Group violations by file
    files_to_fix = {}
    for v in violations:
        filepath = base_dir / v['file']
        if filepath not in files_to_fix:
            files_to_fix[filepath] = []
        files_to_fix[filepath].append(v)

    print(f"Fixing {len(files_to_fix)} files...")

    total_fixed = 0
    for filepath, fixes in sorted(files_to_fix.items()):
        if not filepath.exists():
            continue

        fixed_count = fix_indentation_in_file(filepath, fixes)
        if fixed_count > 0:
            total_fixed += fixed_count
            rel_path = filepath.relative_to(base_dir)
            print(f"✓ Fixed {rel_path} ({fixed_count} indentation issues)")

    print()
    print(f"Summary: Fixed {total_fixed} indentation violations across {len(files_to_fix)} files")
    return 0


if __name__ == '__main__':
    sys.exit(main())
