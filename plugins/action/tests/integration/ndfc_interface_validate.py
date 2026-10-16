from __future__ import absolute_import, division, print_function


__metaclass__ = type

from pprint import pprint
import json
from ansible.utils.display import Display
from ansible.plugins.action import ActionBase
from ansible.module_utils.common.text.converters import to_native
import re
from ..plugin_utils.tools import load_yaml_file, process_deepdiff
from ..plugin_utils.pydantic_schemas.dcnm_interface.schemas import DcnmInterfaceQuerySchema, R2_REDACTED, r2_is_sensitive, r2_redact

try:
    from deepdiff import DeepDiff
    HAS_DEEPDIFF = True
    DEEPDIFF_IMPORT_ERROR = None
except ImportError as imp_exc:
    HAS_DEEPDIFF = False
    DEEPDIFF_IMPORT_ERROR = str(imp_exc)

display = Display()


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        results = super(ActionModule, self).run(tmp, task_vars)
        results['failed'] = False

        # Check if deepdiff is available at runtime
        if not HAS_DEEPDIFF:
            results['failed'] = True
            results['msg'] = f"DeepDiff must be installed to use this plugin. Use pip or install test-requirements. Import error: {DEEPDIFF_IMPORT_ERROR}"
            return results

        ndfc_data = self._task.args.get('ndfc_data', None)
        test_data = self._task.args.get('test_data', None)
        config_path = self._task.args.get('config_path', None)
        check_deleted = self._task.args.get('check_deleted', False)
        ignore_fields = list(self._task.args.get('ignore_fields', []))

        for input_item in [ndfc_data, test_data, config_path]:
            if input_item is None:
                results['failed'] = True
                results['msg'] = f"Required input parameter not found: '{input_item}'"
                return results

        # Get switch mapping from test_data.sw_sn
        switch_ip_sn_mapping = test_data.get('sw_sn', {})

        # removes ansible embeddings and converts to native python types
        native_ndfc_data = json.loads(json.dumps(ndfc_data, default=to_native))

        test_fabric = test_data['fabric']

        expected_data_parsed = None
        diagnostics = []
        if config_path != "":
            # only parse if config file exists
            expected_config_data = load_yaml_file(config_path)
            expected_data = DcnmInterfaceQuerySchema.yaml_config_to_dict(
                expected_config_data, test_fabric, switch_ip_sn_mapping, diagnostics=diagnostics)
            expected_data_parsed = DcnmInterfaceQuerySchema.model_validate(expected_data).model_dump(exclude_none=True)

        # Parse NDFC data through schema to normalize it (case conversion, tuple handling, etc.). R2: the schema keeps
        # every nvPair (extra="allow"), so a requested nvPair can no longer vanish from either side before the comparison.
        ndfc_data_parsed = DcnmInterfaceQuerySchema.model_validate(native_ndfc_data).model_dump(exclude_none=True)

        if deleted_results := self.verify_deleted(results, check_deleted, expected_data_parsed, ndfc_data_parsed, config_path):
            return deleted_results

        if diagnostics:
            # A requested field the checker cannot represent is a FAILURE, never a silent PASS (keys only, no values).
            results['failed'] = True
            results['msg'] = 'Data is not valid: requested fields cannot be validated:\n' + "\n".join(diagnostics)
            return results

        differences = self.compare_interfaces(expected_data_parsed, ndfc_data_parsed, ignore_fields)
        if not differences:
            results['failed'] = False
            results['msg'] = 'Data is valid. \n\n Expected data: \n\n{0}\n\nActual data: \n\n{1}'.format(
                r2_redact(expected_data_parsed), r2_redact(ndfc_data_parsed))
        else:
            results['failed'] = True
            print("\n\nExpected: ")
            pprint(r2_redact(expected_data_parsed))
            print("\n\nActual: ")
            pprint(r2_redact(ndfc_data_parsed))
            print("\n\nDifferences: ")
            pprint(differences)
            results['msg'] = 'Data is not valid.\n\nDifferences: \n\n{0}'.format(differences)

        return results

    @staticmethod
    def _interface_key(interface):
        return (tuple(interface.get("serialNumber") or ()), str(interface.get("ifName", "")).lower())

    def compare_interfaces(self, expected_data, ndfc_data, ignore_fields):
        """R2: compare per interface IDENTITY (serial number tuple + ifName), never across interfaces.

        For each expected interface: absent from the readback -> difference; each expected nvPair absent from the
        readback -> 'missing'; a different normalized value -> 'different'. nvPairs the test did not request, and other
        controller metadata, are ignored (DeepDiff's dictionary_item_added is dropped by process_deepdiff). Fields in
        `ignore_fields` are left out of both sides. Sensitive values are never reported, only their key names.
        When the readback holds several entries for one identity, EVERY entry must hold the requested values: the verdict
        never depends on which entry comes first. Identical entries, or entries that differ only in nvPairs the test did
        not request, still pass.
        Returns {} when everything requested matches.
        """
        differences = {}
        if expected_data is None:
            # No config_path and no check_deleted: nothing to compare with (the base comparison of None also failed).
            return {"expected": "no expected data (empty config_path without check_deleted)"}
        if ndfc_data.get("failed"):
            differences["readback"] = "the query result is marked failed"
        actual = {}
        for policy in ndfc_data.get("response") or []:
            for interface in policy.get("interfaces") or []:
                actual.setdefault(self._interface_key(interface), []).append(interface.get("nvPairs") or {})
        for policy in expected_data.get("response") or []:
            for interface in policy.get("interfaces") or []:
                key = self._interface_key(interface)
                label = "{0} on {1}".format(key[1], "~".join(key[0]))
                if key not in actual:
                    differences[label] = "interface not found in the readback"
                    continue
                want = dict((k, v) for k, v in (interface.get("nvPairs") or {}).items() if k not in ignore_fields)
                found = [self._entry_differences(want, nvpairs, ignore_fields) for nvpairs in actual[key]]
                if len(found) == 1:
                    if found[0]:
                        differences[label] = found[0]
                elif any(found):
                    differences[label] = {
                        "ambiguous_readback": "{0} readback entries for this interface; each must hold the requested values".format(len(found)),
                        "entries": dict(("#{0}".format(index + 1), entry or "matches") for index, entry in enumerate(found)),
                    }
        return differences

    def _entry_differences(self, want, nvpairs, ignore_fields):
        """Differences between the requested nvPairs and ONE readback entry ({} when every requested value matches)."""
        have = dict((k, v) for k, v in nvpairs.items() if k not in ignore_fields)
        # The expectation is a few requested nvPairs; the readback is the full template. DeepDiff >= 8 would report the two
        # dicts as one change at 'root' when they share few keys (threshold_to_diff_deeper, default 0.33); 0 keeps it per key.
        diff = process_deepdiff(DeepDiff(want, have, threshold_to_diff_deeper=0), keys_to_ignore=ignore_fields, ignore_extra_fields=True)
        entry = {}
        if not diff:
            return entry
        for path in diff.get("dictionary_item_removed", []):
            entry.setdefault("missing", []).append(self._path_key(path))
        for change in ("values_changed", "type_changes"):
            for path, values in (diff.get(change) or {}).items():
                nvpair = self._path_key(path)
                if r2_is_sensitive(nvpair):
                    entry.setdefault("different", {})[nvpair] = {"expected": R2_REDACTED, "actual": R2_REDACTED}
                else:
                    entry.setdefault("different", {})[nvpair] = {"expected": values.get("old_value"), "actual": values.get("new_value")}
        for other in set(diff) - set(("dictionary_item_removed", "values_changed", "type_changes")):
            entry.setdefault("other", []).append(other)
        return entry

    @staticmethod
    def _path_key(path):
        m = re.match(r"^root\[['\"](.+)['\"]\]$", str(path))
        return m.group(1) if m else str(path)

    def _normalize_interface_id_fields(self, expected_data, ndfc_data):
        """
        Normalize PO_ID and INTF_NAME fields in expected data based on interface type and what's present in NDFC data.
        For port-channel interfaces, use PO_ID. For other interfaces, use INTF_NAME.
        Also handle special cases like V6IP vs IPv6 for loopback interfaces.
        Remove the incorrect field from expected data if it's not present in the actual NDFC data.
        """
        for expected_policy in expected_data.get("response", []):
            for expected_interface in expected_policy.get("interfaces", []):
                expected_nvpairs = expected_interface.get("nvPairs", {})

                # Find corresponding interface in NDFC data
                ndfc_interface = self._find_matching_interface(expected_interface, ndfc_data)
                if not ndfc_interface:
                    continue

                ndfc_nvpairs = ndfc_interface.get("nvPairs", {})

                # Determine if this is a port-channel or loopback interface
                ifname = expected_interface.get("ifName", "").lower()
                is_port_channel = ifname.startswith("port-channel")
                is_loopback = ifname.startswith("loopback")

                if is_port_channel:
                    # For port-channel interfaces, use PO_ID
                    if "PO_ID" not in ndfc_nvpairs and "PO_ID" in expected_nvpairs:
                        del expected_nvpairs["PO_ID"]
                        display.vvv(f"Removed PO_ID from expected data for port-channel interface {ifname}")

                    # Remove INTF_NAME if present (shouldn't be used for port-channel)
                    if "INTF_NAME" in expected_nvpairs:
                        del expected_nvpairs["INTF_NAME"]
                        display.vvv(f"Removed INTF_NAME from expected data for port-channel interface {ifname}")
                else:
                    # For other interfaces, use INTF_NAME
                    if "INTF_NAME" not in ndfc_nvpairs and "INTF_NAME" in expected_nvpairs:
                        del expected_nvpairs["INTF_NAME"]
                        display.vvv(f"Removed INTF_NAME from expected data for interface {ifname}")

                    # Remove PO_ID if present (shouldn't be used for non-port-channel)
                    if "PO_ID" in expected_nvpairs:
                        del expected_nvpairs["PO_ID"]
                        display.vvv(f"Removed PO_ID from expected data for non-port-channel interface {ifname}")

                # Handle special IPv6 field mapping for loopback interfaces
                if is_loopback:
                    # For loopback interfaces, NDFC uses V6IP instead of IPv6
                    if "IPv6" in expected_nvpairs and "V6IP" in ndfc_nvpairs:
                        # Move IPv6 value to V6IP in expected data
                        expected_nvpairs["V6IP"] = expected_nvpairs["IPv6"]
                        del expected_nvpairs["IPv6"]
                        display.vvv(f"Moved IPv6 to V6IP for loopback interface {ifname}")
                    elif "IPv6" in expected_nvpairs and "V6IP" not in ndfc_nvpairs:
                        # Remove IPv6 if NDFC doesn't have V6IP
                        del expected_nvpairs["IPv6"]
                        display.vvv(f"Removed IPv6 from expected data for loopback interface {ifname}")

                    # For loopback interfaces, NDFC uses ROUTE_MAP_TAG instead of ROUTING_TAG
                    if "ROUTING_TAG" in expected_nvpairs and "ROUTE_MAP_TAG" in ndfc_nvpairs:
                        # Move ROUTING_TAG value to ROUTE_MAP_TAG in expected data
                        expected_nvpairs["ROUTE_MAP_TAG"] = expected_nvpairs["ROUTING_TAG"]
                        del expected_nvpairs["ROUTING_TAG"]
                        display.vvv(f"Moved ROUTING_TAG to ROUTE_MAP_TAG for loopback interface {ifname}")
                    elif "ROUTING_TAG" in expected_nvpairs and "ROUTE_MAP_TAG" not in ndfc_nvpairs:
                        # Remove ROUTING_TAG if NDFC doesn't have ROUTE_MAP_TAG
                        del expected_nvpairs["ROUTING_TAG"]
                        display.vvv(f"Removed ROUTING_TAG from expected data for loopback interface {ifname}")
                else:
                    # For non-loopback interfaces, remove V6IP if present
                    if "V6IP" in expected_nvpairs:
                        del expected_nvpairs["V6IP"]
                        display.vvv(f"Removed V6IP from expected data for non-loopback interface {ifname}")

                    # For non-loopback interfaces, remove ROUTE_MAP_TAG if present
                    if "ROUTE_MAP_TAG" in expected_nvpairs:
                        del expected_nvpairs["ROUTE_MAP_TAG"]
                        display.vvv(f"Removed ROUTE_MAP_TAG from expected data for non-loopback interface {ifname}")

    def _find_matching_interface(self, expected_interface, ndfc_data):
        """
        Find the matching interface in NDFC data based on ifName and serialNumber.
        """
        expected_ifname = expected_interface.get("ifName", "").lower()
        expected_serial = expected_interface.get("serialNumber", "")

        for ndfc_policy in ndfc_data.get("response", []):
            for ndfc_interface in ndfc_policy.get("interfaces", []):
                ndfc_ifname = ndfc_interface.get("ifName", "").lower()
                ndfc_serial = ndfc_interface.get("serialNumber", "")

                if expected_ifname == ndfc_ifname and expected_serial == ndfc_serial:
                    return ndfc_interface

        return None

    def verify_deleted(self, results, check_deleted, expected_data, ndfc_data, config_path):
        if not check_deleted:
            return None

        existing_interfaces = set()
        for policy in ndfc_data["response"]:
            for interface in policy["interfaces"]:
                existing_interfaces.add((interface["serialNumber"], interface["ifName"]))

        if config_path == "":
            # check for full delete
            if not ndfc_data["failed"] and len(existing_interfaces) == 0:
                results['msg'] = 'All interfaces are deleted'
            else:
                print("Interfaces still existing: ")
                print(existing_interfaces)
                results['failed'] = True
                results['msg'] = 'Error: Expected full delete as config_path is empty but interfaces still exist.'
                if ndfc_data["failed"]:
                    results['msg'] += '\n\nError: ' + ndfc_data["error"]
                return results
            return results

        # checks for a partial delete
        deleted_interfaces = set()
        for policy in expected_data["response"]:
            for interface in policy["interfaces"]:
                deleted_interfaces.add((interface["serialNumber"], interface["ifName"]))

        remaining_interfaces = existing_interfaces.intersection(deleted_interfaces)
        if len(remaining_interfaces) > 0:
            results['failed'] = True
            print("Expected interfaces to be deleted: ")
            print(deleted_interfaces)
            print("\nInterfaces present in NDFC: ")
            print(existing_interfaces)
            print("\nInterfaces still not deleted: ")
            print(remaining_interfaces)
            results['msg'] = 'All interfaces are not deleted'
            return results

        print("Expected interfaces to be deleted: ")
        print(deleted_interfaces)
        print("\n\nInterfaces present in NDFC: ")
        print(existing_interfaces)
        print("Interfaces still not deleted: ")
        print(remaining_interfaces)
        results['failed'] = False
        results['msg'] = 'Provided interfaces are deleted'
        return results
