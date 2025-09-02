from __future__ import absolute_import, division, print_function


__metaclass__ = type

from pprint import pprint
import json
from ansible.utils.display import Display
from ansible.plugins.action import ActionBase
from ansible.module_utils.six import raise_from
from ansible.errors import AnsibleError
from ansible.module_utils.common.text.converters import to_native
from ..plugin_utils.tools import load_yaml_file, process_deepdiff
from ..plugin_utils.pydantic_schemas.dcnm_vpc_pair.schemas import DcnmVpcPairQuerySchema

try:
    from deepdiff import DeepDiff
except ImportError as imp_exc:
    DEEPDIFF_IMPORT_ERROR = imp_exc
else:
    DEEPDIFF_IMPORT_ERROR = None

if DEEPDIFF_IMPORT_ERROR:
    raise_from(
        AnsibleError('DeepDiff must be installed to use this plugin. Use pip or install test-requirements.'),
        DEEPDIFF_IMPORT_ERROR)

display = Display()


class ActionModule(ActionBase):

    def filter_actual_config_fields(self, expected_data, actual_data, fabric_type=""):
        """
        Filter specific configuration fields in actual data to only include items 
        that exist in expected data
        """
        if not expected_data or not actual_data:
            return actual_data
            
        def normalize_multiline_configs(config_value):
            """Normalize multiline configuration strings"""
            if not config_value:
                return []
            
            if isinstance(config_value, str):
                lines = [line.strip() for line in config_value.split('\n') if line.strip()]
                return sorted(lines)
            return config_value

        def filter_nvpairs(expected_nvpairs, actual_nvpairs):
            """Filter nvPairs based on expected configuration"""
            # If actual nvpairs is empty dict, return empty dict
            if actual_nvpairs == {}:
                return {}
                
            if not expected_nvpairs or not actual_nvpairs:
                return actual_nvpairs
                
            filtered_nvpairs = actual_nvpairs.copy()
            multiline_fields = [
                'PEER1_DOMAIN_CONF', 'PEER2_DOMAIN_CONF', 
                'PEER1_PO_CONF', 'PEER2_PO_CONF',
                'PEER1_MEMBER_INTERFACES', 'PEER2_MEMBER_INTERFACES'
            ]
            
            for field in multiline_fields:
                if field in expected_nvpairs and field in actual_nvpairs:
                    if field.endswith('_MEMBER_INTERFACES'):
                        # Handle interface lists (comma-separated)
                        expected_interfaces = set()
                        if expected_nvpairs[field]:
                            expected_interfaces = set([iface.strip() for iface in expected_nvpairs[field].split(',')])
                        
                        actual_interfaces = set()
                        if actual_nvpairs[field]:
                            actual_interfaces = set([iface.strip() for iface in actual_nvpairs[field].split(',')])
                        
                        # Keep only interfaces that exist in expected
                        filtered_interfaces = expected_interfaces.intersection(actual_interfaces)
                        filtered_nvpairs[field] = ','.join(sorted(filtered_interfaces)) if filtered_interfaces else ""
                    
                    else:
                        # Handle multiline configuration strings
                        expected_lines = normalize_multiline_configs(expected_nvpairs[field])
                        actual_lines = normalize_multiline_configs(actual_nvpairs[field])
                        
                        # Keep only lines that exist in expected
                        filtered_lines = [line for line in actual_lines if line in expected_lines]
                        filtered_nvpairs[field] = '\n'.join(filtered_lines) if filtered_lines else ""
            
            return filtered_nvpairs
        
        # Apply filtering to actual data
        filtered_actual = actual_data.copy()
        if "response" in expected_data and "response" in actual_data:
            for i, expected_vpc_pair in enumerate(expected_data["response"]):
                if i < len(actual_data["response"]):
                    actual_vpc_pair = actual_data["response"][i]
                    if "nvPairs" in expected_vpc_pair and "nvPairs" in actual_vpc_pair:
                        # If actual nvPairs is empty dict, apply conditional logic based on fabric_type
                        if actual_vpc_pair["nvPairs"] == {}:
                            filtered_actual["response"][i]["nvPairs"] = {}
                            # Only modify expected data if fabric_type contains "vxlan" (case insensitive)
                            if "vxlan" in fabric_type.lower():
                                display.v(f"VXLAN fabric detected ({fabric_type}), setting expected nvPairs to {{}} and templateName to ''")
                                expected_data["response"][i]["nvPairs"] = {}
                                # Also set templateName to empty string for VXLAN fabrics
                                if "templateName" in expected_data["response"][i]:
                                    expected_data["response"][i]["templateName"] = ""
                            else:
                                display.v(f"Non-VXLAN fabric detected ({fabric_type}), keeping expected nvPairs unchanged")
                        else:
                            filtered_nvpairs = filter_nvpairs(
                                expected_vpc_pair["nvPairs"], 
                                actual_vpc_pair["nvPairs"]
                            )
                            filtered_actual["response"][i]["nvPairs"] = filtered_nvpairs
        
        return filtered_actual

    def convert_ip_to_sn(self, data, ip_to_sn_mapping):
        """
        Convert IP addresses to serial numbers in the data structure using the provided mapping
        """
        if not ip_to_sn_mapping:
            return data
            
        def convert_recursive(obj):
            if isinstance(obj, dict):
                converted = {}
                for key, value in obj.items():
                    if key in ['peerOneId', 'peerTwoId'] and isinstance(value, str):
                        # Check if the value is an IP address that exists in our mapping
                        if value in ip_to_sn_mapping:
                            converted[key] = ip_to_sn_mapping[value]
                        else:
                            converted[key] = value
                    else:
                        converted[key] = convert_recursive(value)
                return converted
            elif isinstance(obj, list):
                return [convert_recursive(item) for item in obj]
            else:
                return obj
        
        return convert_recursive(data)

    def verify_deleted(self, results, check_deleted, expected_data, ndfc_data, config_path):
        if not check_deleted:
            return None
        
        existing_vpc_pairs = set()
        for vpc_pair in ndfc_data["response"]:
            # Create a unique identifier for each VPC pair using peer IDs
            vpc_pair_id = f"{vpc_pair.get('peerOneId', '')}_{vpc_pair.get('peerTwoId', '')}"
            existing_vpc_pairs.add(vpc_pair_id)

        if config_path == "":
            # check for full delete
            if not ndfc_data["failed"] and len(existing_vpc_pairs) == 0:
                results['msg'] = 'All VPC pairs are deleted'
            else:
                print("VPC pairs still existing: ")
                print(existing_vpc_pairs)
                results['failed'] = True
                results['msg'] = 'Error: Expected full delete as config_path is empty but VPC pairs still exist.'
                if ndfc_data["failed"]:
                    results['msg'] += '\n\nError: ' + ndfc_data["error"]
                return results
            return results
        
        # checks for a partial delete
        deleted_vpc_pairs = set()
        for vpc_pair in expected_data["response"]:
            vpc_pair_id = f"{vpc_pair.get('peerOneId', '')}_{vpc_pair.get('peerTwoId', '')}"
            deleted_vpc_pairs.add(vpc_pair_id)

        remaining_vpc_pairs = existing_vpc_pairs.intersection(deleted_vpc_pairs)
        if len(remaining_vpc_pairs) > 0:
            results['failed'] = True
            print("Expected VPC pairs to be deleted: ")
            print(deleted_vpc_pairs)
            print("\nVPC pairs present in NDFC: ")
            print(existing_vpc_pairs)
            print("\nVPC pairs still not deleted: ")
            print(remaining_vpc_pairs)
            results['msg'] = 'All VPC pairs are not deleted'
            return results

        print("Expected VPC pairs to be deleted: ")
        print(deleted_vpc_pairs)
        print("\n\nVPC pairs present in NDFC: ")
        print(existing_vpc_pairs)
        print("VPC pairs still not deleted: ")
        print(remaining_vpc_pairs)
        results['failed'] = False
        results['msg'] = 'Provided VPC pairs are deleted'
        return results

    def run(self, tmp=None, task_vars=None):
        results = super(ActionModule, self).run(tmp, task_vars)
        results['failed'] = False

        ndfc_data = self._task.args.get('ndfc_data', None)
        test_data = self._task.args.get('test_data', None)
        config_path = self._task.args.get('config_path', None)
        check_deleted = self._task.args.get('check_deleted', False)
        ignore_fields = list(self._task.args.get('ignore_fields', []))
        
        # Extract fabric_type and ip_to_sn_mapping from test_data if available
        fabric_type = test_data.get('fabric_type', '') if test_data else ''
        ip_to_sn_mapping = test_data.get('ip_to_sn_mapping', {}) if test_data else {}
        display.v(f"Fabric type extracted from test_data: {fabric_type}")
        display.v(f"IP to SN mapping extracted from test_data: {len(ip_to_sn_mapping)} entries")
        
        for input_item in [ndfc_data, test_data, config_path]:
            if input_item is None:
                results['failed'] = True
                results['msg'] = f"Required input parameter not found: '{input_item}'"
                return results

        # removes ansible embeddings and converts to native python types
        native_ndfc_data = json.loads(json.dumps(ndfc_data, default=to_native))

        test_fabric = test_data['fabric']

        expected_data_parsed = None
        if config_path != "":
            # only parse if config file exists
            expected_config_data = load_yaml_file(config_path)
            expected_data = DcnmVpcPairQuerySchema.yaml_config_to_dict(expected_config_data, test_fabric)
            
            # Convert IP addresses to serial numbers in expected data if mapping is provided
            if ip_to_sn_mapping:
                expected_data = self.convert_ip_to_sn(expected_data, ip_to_sn_mapping)

            expected_data_parsed = DcnmVpcPairQuerySchema.model_validate(expected_data).model_dump(exclude_none=True)

        ndfc_data_parsed = DcnmVpcPairQuerySchema.model_validate(native_ndfc_data).model_dump(exclude_none=True)

        # Apply configuration filtering if we have expected data
        if expected_data_parsed:
            native_ndfc_data = self.filter_actual_config_fields(expected_data_parsed, native_ndfc_data, fabric_type)
            ndfc_data_parsed = DcnmVpcPairQuerySchema.model_validate(native_ndfc_data).model_dump(exclude_none=True)

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
            results['msg'] = f'Data is valid. \n\n Expected data: \n\n{expected_data}\n\nActual data: \n\n{ndfc_data_parsed}'
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
