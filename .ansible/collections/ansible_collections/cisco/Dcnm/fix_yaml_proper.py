#!/usr/bin/env python3
"""
Properly fix YAML lint violations without merging or destroying YAML structure.

This script fixes violations by only modifying the specific issues on each line:
- yaml[hyphens]: Fix spacing after hyphen (should be exactly 1 space)
- yaml[indentation]: Fix indentation level
- yaml[truthy]: Change True/False to true/false
- yaml[colons]: Fix spacing around colons
- yaml[comments]: Add space after #
- yaml[octal-values]: Quote octal-like values
"""

import re
import subprocess
from collections import defaultdict


def get_violations():
    """Get yaml violations with detailed information."""
    result = subprocess.run(
        ["ansible-lint", "--nocolor", "--parseable", "plugins/modules/"],
        capture_output=True,
        text=True
    )

    violations = defaultdict(list)

    for line in result.stdout.splitlines() + result.stderr.splitlines():
        # Match format: filepath:lineno: yaml[type][/]: message
        match = re.match(r'^([^:]+):(\d+):\s+yaml\[(\w+)\]\[\S*\]:\s+(.+)$', line)
        if match:
            filepath, lineno, vtype, message = match.groups()
            violations[filepath].append({
                'line': int(lineno),
                'type': vtype,
                'message': message
            })

    return violations


def fix_file_violations(filepath, file_violations):
    """Fix all violations in a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    modified = False

    # Group violations by line number
    by_line = defaultdict(list)
    for v in file_violations:
        by_line[v['line']].append(v)

    for lineno in sorted(by_line.keys()):
        idx = lineno - 1
        if idx < 0 or idx >= len(lines):
            continue

        original = lines[idx]
        fixed = original

        for v in by_line[lineno]:
            vtype = v['type']
            message = v['message']

            if vtype == 'hyphens' and 'Too many spaces after hyphen' in message:
                # Fix: "    -   key:" -> "    - key:" (exactly 1 space after hyphen)
                # Only fix lines that start with whitespace, hyphen, and multiple spaces
                match = re.match(r'^(\s*)-\s{2,}', fixed)
                if match:
                    indent = match.group(1)
                    # Replace the hyphen and multiple spaces with hyphen and single space
                    fixed = re.sub(r'^(\s*)-\s{2,}', r'\1- ', fixed)

            elif vtype == 'indentation' and 'Wrong indentation' in message:
                # Extract expected and found values
                match = re.search(r'expected (\d+) but found (\d+)', message)
                if match:
                    expected = int(match.group(1))
                    found = int(match.group(2))

                    # Only fix if the line starts with exactly 'found' spaces
                    if fixed.startswith(' ' * found) and not fixed.startswith(' ' * (found + 1)):
                        content = fixed.lstrip()
                        fixed = ' ' * expected + content

            elif vtype == 'truthy':
                # Fix True/False/Yes/No/yes/no/ON/OFF/on/off -> true/false
                # Only fix YAML values, not in comments or strings
                patterns = [
                    (r':\s+True\s*$', ': true\n'),
                    (r':\s+True\s+(#.*)$', r': true \1'),
                    (r':\s+False\s*$', ': false\n'),
                    (r':\s+False\s+(#.*)$', r': false \1'),
                    (r':\s+Yes\s*$', ': true\n'),
                    (r':\s+Yes\s+(#.*)$', r': true \1'),
                    (r':\s+No\s*$', ': false\n'),
                    (r':\s+No\s+(#.*)$', r': false \1'),
                ]
                for pattern, repl in patterns:
                    if re.search(pattern, fixed):
                        fixed = re.sub(pattern, repl, fixed)
                        break

            elif vtype == 'colons' and 'Too many spaces after colon' in message:
                # Fix "key:  value" -> "key: value" (exactly 1 space after colon)
                fixed = re.sub(r':(\s{2,})(\S)', r': \2', fixed)

            elif vtype == 'comments' and 'Missing starting space' in message:
                # Fix "#comment" -> "# comment"
                fixed = re.sub(r'#([^\s#])', r'# \1', fixed)

            elif vtype == 'octal-values':
                # Quote octal-like numeric strings
                match = re.search(r'(\w+):\s+(0\d{5,})(\s*(?:#|$))', fixed)
                if match:
                    key, value, rest = match.groups()
                    if not (f'"{value}"' in fixed or f"'{value}'" in fixed):
                        fixed = fixed.replace(f'{key}: {value}', f'{key}: "{value}"')

        if fixed != original:
            lines[idx] = fixed
            modified = True

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return True
    return False


def main():
    """Main function."""
    print("=" * 70)
    print("Fixing YAML Violations in Module Files")
    print("=" * 70)

    # Run multiple passes to handle cascading fixes
    max_passes = 5
    for pass_num in range(1, max_passes + 1):
        print(f"\nPass {pass_num}:")
        violations = get_violations()

        if not violations:
            print("  No violations found!")
            break

        total_violations = sum(len(v) for v in violations.values())
        print(f"  Found {total_violations} violations in {len(violations)} files")

        fixed_files = 0
        for filepath, file_violations in violations.items():
            if fix_file_violations(filepath, file_violations):
                fixed_files += 1

        print(f"  Fixed {fixed_files} files")

        if fixed_files == 0:
            print("  No more automatic fixes possible")
            break

    # Final verification
    print("\n" + "=" * 70)
    print("Final Verification")
    print("=" * 70)
    final_violations = get_violations()
    if not final_violations:
        print("✓ All violations fixed!")
        return 0
    else:
        total = sum(len(v) for v in final_violations.values())
        print(f"⚠ {total} violations remaining (may require manual review)")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
