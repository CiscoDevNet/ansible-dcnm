from __future__ import absolute_import, division, print_function


__metaclass__ = type

from ansible.utils.display import Display
from ansible.plugins.action import ActionBase
import json
from deepdiff import DeepDiff
from ansible.module_utils.common.text.converters import to_native
from pprint import pprint
from ..plugin_utils.pydantic_schemas.dcnm_network.schemas import DcnmNetworkQuerySchema
from ..plugin_utils.tools import load_yaml_file, process_deepdiff

display = Display()

class ActionModule(ActionBase):
    
    def run(self, tmp=None, task_vars=None):
        results = super(ActionModule, self).run(tmp, task_vars)
        results['failed'] = False

        ndfc_data = self._task.args['ndfc_data']
        if ndfc_data is None:
            results['failed'] = True
            results['msg'] = 'No data found in ndfc_data'
            return results

        # removes ansible embeddings and converts to native python types
        native_ndfc_data = json.loads(json.dumps(ndfc_data, default=to_native))

        config_path = self._task.args['config_path']
        if config_path is None:
            results['failed'] = True
            results['msg'] = 'No path is loaded into config_path'
            return results
        
        test_data = self._task.args['test_data']
        if test_data is None:
            results['failed'] = True
            results['msg'] = 'No test data is found in test_data'
            return results
        
        expected_config_data = load_yaml_file(config_path)
        
        test_fabric = test_data['test_fabric']
        # Convert the config yaml file to a dictionary
        
        expected_data = DcnmNetworkQuerySchema.yaml_config_to_dict(expected_config_data, test_fabric, deploy=test_data.get('deploy', False))
        expected_data_parsed = DcnmNetworkQuerySchema.parse_obj(expected_data).dict(exclude_none=True)
        ndfc_data_parsed = DcnmNetworkQuerySchema.parse_obj(native_ndfc_data).dict(exclude_none=True)
        
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
            results['msg'] = 'Data is valid. \n\n Expected data: \n\n{}\n\nActual data: \n\n{}'.format(
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
    
