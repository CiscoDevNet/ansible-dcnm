#!/bin/bash
# Fix all YAML load-failure errors using sed

cd /Users/sivakasi/ansible/collections/ansible_collections/cisco/dcnm_lint/dcnm

# Get list of files with load-failure errors
ansible-lint --profile=production --tags load-failure --parseable 2>/dev/null | \
  cut -d: -f1 | sort -u > /tmp/files_to_fix.txt

echo "Found $(wc -l < /tmp/files_to_fix.txt) files with errors"

# For each file, try to fix common patterns
while IFS= read -r file; do
  if [ -f "$file" ]; then
    echo "Processing: $file"
    
    # Create backup
    cp "$file" "$file.bak"
    
    # Use Python to fix the file properly
    python3 << 'PYTHON_SCRIPT' "$file"
import sys
import re

file_path = sys.argv[1]

with open(file_path, 'r') as f:
    lines = f.readlines()

fixed_lines = []
in_that_block = False
that_indent = 0

for i, line in enumerate(lines):
    # Detect that: block
    match = re.match(r'^(\s+)that:\s*$', line)
    if match:
        in_that_block = True
        that_indent = len(match.group(1))
        fixed_lines.append(line)
        continue
    
    if in_that_block:
        # Check if still in that block
        if line.strip():
            curr_indent = len(line) - len(line.lstrip())
            if curr_indent <= that_indent:
                in_that_block = False
            elif line.lstrip().startswith('- '):
                # It's a list item, ensure it has correct indent (that_indent + 2)
                expected_indent = that_indent + 2
                if curr_indent != expected_indent:
                    fixed_lines.append(' ' * expected_indent + '- ' + line.lstrip()[2:])
                    continue
        else:
            in_that_block = False
    
    fixed_lines.append(line)

with open(file_path, 'w') as f:
    f.writelines(fixed_lines)
PYTHON_SCRIPT
    
    # Check if file was fixed
    if ! ansible-lint "$file" 2>&1 | grep -q "load-failure"; then
      echo "  ✓ Fixed!"
      rm "$file.bak"
    else
      echo "  ✗ Still has errors, restoring backup"
      mv "$file.bak" "$file"
    fi
  fi
done < /tmp/files_to_fix.txt

echo "Done! Running final check..."
ansible-lint --profile=production --tags load-failure 2>&1 | grep -c "load-failure" || echo "All fixed!"
