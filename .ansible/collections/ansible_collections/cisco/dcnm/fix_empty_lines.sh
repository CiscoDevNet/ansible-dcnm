#!/bin/bash
# Fix empty lines in Python modules - remove excess blank lines in YAML examples

files=(
  "plugins/modules/dcnm_bootflash.py:185"
  "plugins/modules/dcnm_fabric.py:3715"
  "plugins/modules/dcnm_image_upgrade.py:400"
  "plugins/modules/dcnm_interface.py:1808"
  "plugins/modules/dcnm_links.py:603"
  "plugins/modules/dcnm_log.py:75"
  "plugins/modules/dcnm_maintenance_mode.py:142"
  "plugins/modules/dcnm_resource_manager.py:278"
  "plugins/modules/dcnm_rest.py:90"
  "plugins/modules/dcnm_service_policy.py:438"
  "plugins/modules/dcnm_service_route_peering.py:1158"
)

for item in "${files[@]}"; do
  file="${item%%:*}"
  line="${item##*:}"
  # Delete the blank line at the specified line number
  sed -i '' "${line}d" "$file"
  echo "Fixed: $file line $line"
done
