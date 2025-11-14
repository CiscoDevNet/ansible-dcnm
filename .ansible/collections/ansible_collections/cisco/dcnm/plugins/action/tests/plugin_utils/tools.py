from __future__ import absolute_import, division, print_function

import yaml
import os


def load_yaml_file(file_path):
    """
    Load a YAML file from the given path and return its content as a Python object.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")

    with open(file_path, 'r', encoding='utf-8') as yaml_file:
        try:
            return yaml.safe_load(yaml_file)
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file '{file_path}': {e}") from e


def process_deepdiff(deepdiff_output, keys_to_ignore, ignore_extra_fields=False):
    """
    Process deepdiff output to extract paths ignoring indices and find differences.
    Returns a dictionary with the same structure as deepdiff output but with
    processed iterable items for easier comparison.
    Stores values in a "path" -> List["value"] mapping to find differences.
    Args:
        deepdiff_output: The output from DeepDiff
        ignore_extra_fields: When True, ignores dictionary_item_added changes (default: False)
    """
    def normalize_path(path):
        """Remove indexes from paths to make them comparable."""
        parts = []
        for part in path.replace("root", "").replace("'", "").replace('"', '').strip("[]").split("]["):
            # We want to ignore numeric indexes to make it order agnostic
            if not part.isdigit():
                parts.append(part)
        return "[" + "][".join(parts) + "]"

    def extract_values(data, current_path="", values=None):
        """Extract all values with their normalized paths."""
        if values is None:
            values = {}

        if isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{current_path}['{key}']" if current_path else f"['{key}']"
                extract_values(value, new_path, values)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                # We include index in the internal path but will normalize later
                new_path = f"{current_path}[{i}]"
                extract_values(item, new_path, values)
        else:
            # Store the path with its value
            norm_path = normalize_path(current_path)
            if norm_path not in values:
                values[norm_path] = []
            values[norm_path].append(str(data))
        return values

    processed_diff = {}

    # Copy all items except iterable_item_added and iterable_item_removed
    # If ignore_extra_fields is True, also exclude dictionary_item_added
    for diff_type, diff_data in deepdiff_output.items():
        if diff_type not in ['iterable_item_added', 'iterable_item_removed']:
            if ignore_extra_fields and diff_type == 'dictionary_item_added':
                continue
            processed_diff[diff_type] = diff_data

    added_values = {}
    removed_values = {}

    # Extract added items
    if 'iterable_item_added' in deepdiff_output:
        for root_path, data in deepdiff_output['iterable_item_added'].items():
            values = extract_values(data, root_path)
            for path, vals in values.items():
                if path not in added_values:
                    added_values[path] = []
                added_values[path].extend(vals)

    # Extract removed items
    if 'iterable_item_removed' in deepdiff_output:
        for root_path, data in deepdiff_output['iterable_item_removed'].items():
            values = extract_values(data, root_path)
            for path, vals in values.items():
                if path not in removed_values:
                    removed_values[path] = []
                removed_values[path].extend(vals)

    # Process and add the paths with differences
    diff_paths = {}

    # Compare added and removed values
    all_paths = set(list(added_values.keys()) + list(removed_values.keys()))

    for path in all_paths:
        removed = removed_values.get(path, [])
        added = added_values.get(path, [])

        remaining_removed = removed.copy()
        remaining_added = added.copy()

        # Find matching values by checking them as key in the remaining_added dict
        for val in removed[:]:
            if val in remaining_added:
                remaining_added.remove(val)
                remaining_removed.remove(val)

        # Add differences to diff_paths
        for val in remaining_removed:
            if 'removed_values' not in diff_paths:
                diff_paths['removed_values'] = {}
            if path not in diff_paths['removed_values']:
                diff_paths['removed_values'][path] = []
            diff_paths['removed_values'][path].append(val)

        for val in remaining_added:
            if 'added_values' not in diff_paths:
                diff_paths['added_values'] = {}
            if path not in diff_paths['added_values']:
                diff_paths['added_values'][path] = []
            diff_paths['added_values'][path].append(val)

    # Filter out added paths that don't have a corresponding path in removed_values
    # This is because these paths do not need to be checked as expected data does not have them
    if 'added_values' in diff_paths:
        paths_to_remove = []
        for path in diff_paths['added_values']:
            if 'removed_values' not in diff_paths or path not in diff_paths['removed_values']:
                paths_to_remove.append(path)

        for path in paths_to_remove:
            del diff_paths['added_values'][path]

        diff_paths_keys = list(diff_paths['added_values'].keys())
        for path in diff_paths_keys:
            for field in keys_to_ignore:
                if field in path:
                    del diff_paths['added_values'][path]

        # Remove added_values if it becomes empty after filtering
        if not diff_paths['added_values']:
            del diff_paths['added_values']

    if diff_paths:
        if 'added_values' in diff_paths:
            processed_diff['iterable_item_added'] = diff_paths['added_values']
        if 'removed_values' in diff_paths:
            processed_diff['iterable_item_removed'] = diff_paths['removed_values']

    return processed_diff
