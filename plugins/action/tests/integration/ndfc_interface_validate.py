from __future__ import absolute_import, division, print_function


__metaclass__ = type

from pprint import pprint
import json
from ansible.utils.display import Display
from ansible.plugins.action import ActionBase
from ansible.module_utils.common.text.converters import to_native
from ..plugin_utils.tools import load_yaml_file, process_deepdiff
from ..plugin_utils.pydantic_schemas.dcnm_interface.schemas import DcnmInterfaceQuerySchema

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
        if config_path != "":
            # only parse if config file exists
            expected_config_data = load_yaml_file(config_path)
            expected_data = DcnmInterfaceQuerySchema.yaml_config_to_dict(expected_config_data, test_fabric, switch_ip_sn_mapping)
            expected_data_parsed = DcnmInterfaceQuerySchema.model_validate(expected_data).model_dump(exclude_none=True)

        # Parse NDFC data through schema to normalize it (case conversion, tuple handling, etc.)
        ndfc_data_parsed = DcnmInterfaceQuerySchema.model_validate(native_ndfc_data).model_dump(exclude_none=True)

        if deleted_results := self.verify_deleted(results, check_deleted, expected_data_parsed, ndfc_data_parsed, config_path):
            return deleted_results

        validity = DeepDiff(
            expected_data_parsed,
            ndfc_data_parsed,
            ignore_order=True,
            cutoff_distance_for_pairs=0,
            cutoff_intersection_for_pairs=0,
            report_repetition=True
        )

        # Process the output of deepdiff to make it easier to read
        # Effects the iterable_item_added and iterable_item_removed to remove unneeded fields
        # ignore_extra_fields=True will ignore dictionary_item_added changes
        # This is useful when the actual data has more fields than the expected data
        # keys_to_ignore is a list of fields to ignore, useful for auto provisioned fields which are not known
        processed_validity = process_deepdiff(validity, keys_to_ignore=ignore_fields, ignore_extra_fields=True)
        if processed_validity == {}:
            results['failed'] = False
            results['msg'] = f'Data is valid. \n\n Expected data: \n\n{expected_data_parsed}\n\nActual data: \n\n{ndfc_data_parsed}'
        else:
            results['failed'] = True
            print("\n\nExpected: ")
            pprint(expected_data_parsed)
            print("\n\nActual: ")
            pprint(ndfc_data_parsed)
            print("\n\nDifferences: ")
            pprint(processed_validity)
            results['msg'] = 'Data is not valid.'

        return results

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
