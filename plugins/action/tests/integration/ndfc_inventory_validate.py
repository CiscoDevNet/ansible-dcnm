from __future__ import absolute_import, division, print_function
from ansible.utils.display import Display
from ansible.plugins.action import ActionBase
from pydantic import BaseModel, model_validator, validator, ValidationError
from typing import List, Dict, Optional, Union
import re
import json

__metaclass__ = type

display = Display()


class ConfigData(BaseModel):
    role: Optional[str] = None
    seed_ip: Optional[str] = None


class NDFCData(BaseModel):
    ipAddress: Optional[str] = None
    switchRoleEnum: Optional[str] = None
    switchRole: Optional[str] = None


class InventoryValidate(BaseModel):
    config_data: Optional[List[ConfigData]] = None
    ndfc_data: Optional[Union[List[NDFCData], str]] = None
    ignore_fields: Optional[Dict[str, int]] = None 

    @validator('config_data', pre=True)
    def parse_config_data(cls, value):
        if isinstance(value, dict):
            return [ConfigData.parse_obj(value)]
        if isinstance(value, list):
            try:
                return [ConfigData.parse_obj(item) for item in value]
            except ValidationError as e:
                raise ValueError(f"Invalid format in Config Data: {e}")
        elif value is None:
            return None
        else:
            raise ValueError("Config Data must be a single/list of dictionary, or None.")

    @validator('ndfc_data', pre=True)
    def parse_ndfc_data(cls, value):
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            try:
                return [NDFCData.parse_obj(item) for item in value]
            except ValidationError as e:
                raise ValueError(f"Invalid format in NDFC Response: {e}")
        else:
            raise ValueError("NDFC Response must be a list of dictionaries or an error string")

    @model_validator(mode='after')
    def validate_lists_equality(cls, values):
        config_data = values.config_data
        ndfc_data = values.ndfc_data
        ignore_fields = values.ignore_fields
        response = "False"

        if isinstance(ndfc_data, str):
            if config_data is None and ndfc_data == "The queried switch is not part of the fabric configured":
                response = "True"
                return response
            else:
                print(" NDFC Query returned an Invalid Response\n")
                return response

        missing_ips = []
        role_mismatches = {}
        ndfc_data_copy = ndfc_data.copy()
        matched_indices_two = set()

        for config_data_item in config_data:
            found_match = False
            config_data_item_dict = config_data_item.dict(exclude_none=True)
            for i, ndfc_data_item in enumerate(ndfc_data_copy):
                ndfc_data_item = ndfc_data_item.dict(include=set(['ipAddress', 'switchRoleEnum', 'switchRole'] + list(config_data_item_dict.keys())))
                if i in matched_indices_two:
                    continue

                seed_ip_match = False
                role_match = False

                ip_address_two = ndfc_data_item.get('ipAddress')
                switch_role_two = ndfc_data_item.get('switchRole')
                role_one = config_data_item_dict.get('role')
                if switch_role_two is not None:
                    switch_role_two = re.sub(r'[^a-zA-Z0-9]', '', switch_role_two.lower())
                if role_one is not None:
                    role_one = re.sub(r'[^a-zA-Z0-9]', '', role_one.lower())
                seed_ip_one = config_data_item_dict.get('seed_ip')

                if ((seed_ip_one is not None and ip_address_two is not None and ip_address_two == seed_ip_one) or (ignore_fields['seed_ip'])):
                    seed_ip_match = True

                if ((role_one is not None and switch_role_two is not None and switch_role_two == role_one) or (ignore_fields['role'])) :
                    role_match = True

                if seed_ip_match and role_match:
                    matched_indices_two.add(i)
                    found_match = True
                    if ignore_fields['seed_ip']:
                        break
                elif ((seed_ip_match and role_one is not None and switch_role_two is not None and switch_role_two != role_one) or (ignore_fields['role'])):
                    role_mismatches.setdefault((seed_ip_one or ip_address_two), {"expected_role": role_one, "response_role": switch_role_two})
                    matched_indices_two.add(i)  # Consider it a partial match to avoid further matching
                    found_match = True
                    if ignore_fields['seed_ip']:
                        break

            if not found_match and config_data_item_dict is not None and config_data_item_dict.get('seed_ip') is not None:
                missing_ips.append(config_data_item_dict.get('seed_ip'))

        if not missing_ips and not role_mismatches:
            response = "True"
        else:
            print("Invalid Data:\n ")
            if not missing_ips:
                print(missing_ips)
            if not role_mismatches:
                print(json.dumps(role_mismatches, indent=2))
        return response


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        results = super(ActionModule, self).run(tmp, task_vars)
        results['failed'] = False
        ndfc_data = self._task.args['ndfc_data']
        test_data = self._task.args['test_data']

        if 'changed' in self._task.args:
            changed = self._task.args['changed']
            if not changed:
                results['failed'] = True
                results['msg'] = 'Changed is "false"'
                return results

        if len(ndfc_data['response']) == 0:
            results['failed'] = True
            results['msg'] = 'No response data found'
            return results

        ignore_fields = {"seed_ip": 0, "role": 0}

        if 'mode' in self._task.args:
            mode = self._task.args['mode'].lower()
            if mode == 'ip':
                ignore_fields['role'] = 1
            elif mode == 'role':
                ignore_fields['seed_ip'] = 1

        validation_result = InventoryValidate(config_data=test_data, ndfc_data=ndfc_data['response'], ignore_fields=ignore_fields)
        validation_output = InventoryValidate.model_validate(validation_result)

        if validation_output == "True":
            results['failed'] = False
            results['msg'] = 'Validation Successful!'
        else:
            results['failed'] = True
            results['msg'] = 'Validation Failed! Please check output above.'

        return results
