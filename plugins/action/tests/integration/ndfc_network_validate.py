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
from ..plugin_utils.pydantic_schemas.dcnm_network.schemas import DcnmNetworkQuerySchema

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

    def run(self, tmp=None, task_vars=None):
        results = super(ActionModule, self).run(tmp, task_vars)
        results['failed'] = False

        if 'ndfc_data' not in self._task.args:
            results['failed'] = True
            results['msg'] = 'No data found in ndfc_data'
            return results

        ndfc_data = self._task.args['ndfc_data']
        # removes ansible embeddings and converts to native python types
        native_ndfc_data = json.loads(json.dumps(ndfc_data, default=to_native))

        if "test_data" not in self._task.args:
            results['failed'] = True
            results['msg'] = 'No test data is found in test_data'
            return results

        test_data = self._task.args['test_data']

        if "config_path" not in self._task.args:
            results['failed'] = True
            results['msg'] = 'No path is loaded into config_path'
            return results

        config_path = self._task.args['config_path']

        if 'check_deleted' in self._task.args:
            check_deleted = self._task.args['check_deleted']

        check_deleted = False

        test_fabric = test_data['test_fabric']
        if config_path != "":
            # only parse if config file exists
            expected_config_data = load_yaml_file(config_path)
            expected_data = DcnmNetworkQuerySchema.yaml_config_to_dict(expected_config_data, test_fabric)

            expected_data_parsed = DcnmNetworkQuerySchema.parse_obj(expected_data).dict(exclude_none=True)

        ndfc_data_parsed = DcnmNetworkQuerySchema.parse_obj(native_ndfc_data).dict(exclude_none=True)

        if check_deleted:
            results['failed'] = False
            results['msg'] = ""
            existing_networks = set()
            for network in ndfc_data_parsed["response"]:
                existing_networks.add(network["parent"]["networkName"])

            if config_path == "":
                # check for full delete
                if not ndfc_data_parsed["failed"] and len(existing_networks) == 0:
                    results['msg'] = 'All networks are deleted'
                else:
                    print("Networks still existing: ")
                    print(existing_networks)
                    results['failed'] = True
                    results['msg'] = 'Error: Expected full delete as config_path is empty but networks still exist.'
                    if ndfc_data_parsed["failed"]:
                        results['msg'] += '\n\nError: ' + ndfc_data_parsed["error"]
                    return results
                return results

            # checks for a partial delete
            deleted_networks = set()
            for network in expected_data_parsed["response"]:
                deleted_networks.add(network["parent"]["networkName"])

            remaining_networks = existing_networks.intersection(deleted_networks)
            if len(remaining_networks) > 0:
                results['failed'] = True
                print("Expected networks to be deleted: ")
                print(deleted_networks)
                print("\nNetworks present in NDFC: ")
                print(existing_networks)
                print("\nNetworks still not deleted: ")
                print(remaining_networks)
                results['msg'] = 'All networks are not deleted'
                return results

            print("Expected networks to be deleted: ")
            print(deleted_networks)
            print("\n\nNetworks present in NDFC: ")
            print(existing_networks)
            print("Networks still not deleted: ")
            print(remaining_networks)
            results['failed'] = False
            results['msg'] = 'Provided networks are deleted'
            return results

        # non deleted checking
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
        # This is useful when the the actual data has more fields than the expected data
        processed_validity = process_deepdiff(validity, ignore_extra_fields=True)
        if processed_validity == {}:
            results['failed'] = False
            results['msg'] = f'Data is valid. \n\n Expected data: \n\n{expected_data}\n\nActual data: \n\n{ndfc_data_parsed}'.format(
                expected_data_parsed,
                ndfc_data_parsed
            )
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
