#!/usr/bin/env python3
"""Extract all lint errors by category."""

import re
from collections import defaultdict

with open('full-lint-output.txt', 'r') as f:
    content = f.read()

# Strip ANSI codes
content = re.sub(r'\x1b\[[0-9;]*m', '', content)

errors = defaultdict(list)

# Parse each error
lines = content.split('\n')
for i, line in enumerate(lines):
    # Match file:line patterns with error description
    match = re.match(r'^([^:]+\.ya?ml):(\d+)(?::(\d+))?\s+(.+)$', line)
    if match:
        filepath = match.group(1)
        line_num = match.group(2)
        col = match.group(3) or ''
        error_msg = match.group(4)
        
        # Categorize by error type
        if 'did not find expected' in error_msg:
            errors['yaml_syntax'].append((filepath, line_num, error_msg))
        elif 'mapping values are not allowed' in error_msg:
            errors['mapping_values'].append((filepath, line_num, error_msg))
        elif 'Wrong indentation' in error_msg:
            errors['indentation'].append((filepath, line_num, error_msg))
        elif 'name[' in line or i > 0 and 'name[' in lines[i-1]:
            errors['naming'].append((filepath, line_num, error_msg))

print("Error Categories:")
print(f"YAML Syntax Errors: {len(errors['yaml_syntax'])}")
print(f"Mapping Values Errors: {len(errors['mapping_values'])}")
print(f"Indentation Errors: {len(errors['indentation'])}")
print(f"Naming Errors: {len(errors['naming'])}")

print("\nFirst 10 YAML Syntax Errors:")
for filepath, line_num, error_msg in errors['yaml_syntax'][:10]:
    print(f"  {filepath}:{line_num} - {error_msg}")

print("\nFirst 10 Mapping Values Errors:")
for filepath, line_num, error_msg in errors['mapping_values'][:10]:
    print(f"  {filepath}:{line_num} - {error_msg}")

print("\nAll Indentation Errors:")
for filepath, line_num, error_msg in errors['indentation']:
    print(f"  {filepath}:{line_num} - {error_msg}")
