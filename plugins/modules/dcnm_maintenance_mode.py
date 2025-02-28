#!/usr/bin/python
#
# Copyright (c) 2020-2024 Cisco and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import absolute_import, division, print_function

__metaclass__ = type
__author__ = "Allen Robel"

DOCUMENTATION = """
---
module: dcnm_maintenance_mode
short_description: Manage Maintenance Mode Configuration of NX-OS Switches.
version_added: "3.6.0"
author: Allen Robel (@quantumonion)
description:
- Enable Maintenance or Normal Mode.
options:
    state:
        choices:
        - merged
        - query
        default: merged
        description:
        - The state of the feature or object after module completion
        type: str
    config:
        description:
        - A dictionary containing the maintenance mode configuration.
        type: dict
        required: true
        suboptions:
            deploy:
                default: false
                description:
                - Whether to deploy the switch configurations.
                required: false
                type: bool
            wait_for_mode_change:
                default: false
                description:
                - If deploy is enabled, whether to wait for NDFC to push the change to the switch.  Ignored if deploy is not enabled.
                required: false
                type: bool
            mode:
                choices:
                - maintenance
                - normal
                default: normal
                description:
                - Enable maintenance or normal mode on all switches.
                required: false
                type: bool
            switches:
                description:
                - A list of target switches.
                - Per-switch options override the global options.
                required: true
                type: list
                elements: dict
                suboptions:
                    ip_address:
                        description:
                        - The IP address of the switch.
                        required: true
                        type: str
                    mode:
                        choices:
                        - maintenance
                        - normal
                        default: normal
                        description:
                        - Enable maintenance or normal mode for the switch.
                        required: false
                        type: str
                    deploy:
                        default: false
                        description:
                        - Whether to deploy the switch configuration.
                        required: false
                        type: bool
                    wait_for_mode_change:
                        default: false
                        description:
                        - If deploy is enabled, whether to wait for NDFC to push the change to the switch. Ignored if deploy is not enabled.
                        required: false
                        type: bool
"""

EXAMPLES = """

# Enable maintenance mode on all switches.
# Do not deploy the configuration on any switch.

- name: Configure switch mode
  cisco.dcnm.dcnm_maintenance_mode:
    state: merged
    config:
        deploy: true
        wait_for_mode_change: true
        mode: maintenance
        switches:
            -   ip_address: 192.168.1.2
            -   ip_address: 192.160.1.3
            -   ip_address: 192.160.1.4
  register: result
- debug:
    var: result

# Enable maintenance mode on two switches.
# Enable normal mode on one switch.
# Deploy the configuration on one switch.

- name: Configure switch mode
  cisco.dcnm.dcnm_maintenance_mode:
    state: merged
    config:
        deploy: false
        mode: maintenance
        switches:
            -   ip_address: 192.168.1.2
                mode: normal
            -   ip_address: 192.160.1.3
                deploy: true
                wait_for_mode_change: true
            -   ip_address: 192.160.1.4
  register: result
- debug:
    var: result


"""
# pylint: disable=wrong-import-position
import copy
import inspect
import json
import logging

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.common.log_v2 import Log
from ..module_utils.common.maintenance_mode import MaintenanceMode
from ..module_utils.common.maintenance_mode_info import MaintenanceModeInfo
from ..module_utils.common.merge_dicts_v2 import MergeDicts
from ..module_utils.common.params_merge_defaults_v2 import ParamsMergeDefaults
from ..module_utils.common.params_validate_v2 import ParamsValidate
from ..module_utils.common.properties import Properties
from ..module_utils.common.response_handler import ResponseHandler
from ..module_utils.common.rest_send_v2 import RestSend
from ..module_utils.common.results import Results
from ..module_utils.common.sender_dcnm import Sender


def json_pretty(msg):
    """
    Return a pretty-printed JSON string for logging messages
    """
    return json.dumps(msg, indent=4, sort_keys=True)


class ParamsSpec:
    """
    Build parameter specifications for the dcnm_maintenance_mode module.

    ### Usage
    ```python
    from ansible.module_utils.basic import AnsibleModule

    argument_spec = {}
    argument_spec["config"] = {
        "required": True,
        "type": "dict",
    }
    argument_spec["state"] = {
        "choices": ["merged", "query"],
        "default": "merged",
        "required": False,
        "type": "str"
    }

    ansible_module = AnsibleModule(
        argument_spec=argument_spec, supports_check_mode=True
    )

    params_spec = ParamsSpec()
    try:
        params_spec.params = ansible_module.params
    except ValueError as error:
        ansible_module.fail_json(error)
    params_spec.commit()
    spec = params_spec.params_spec
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED ParamsSpec()")

        self._params = None
        self._params_spec: dict = {}

        self.valid_states = ["merged", "query"]

    def commit(self):
        """
        Build the parameter specification based on the state

        ## Raises
        -   ``ValueError`` if params is not set
        """
        if self._params is None:
            msg = f"{self.class_name}.commit: "
            msg += "params must be set before calling commit()."
            raise ValueError(msg)

        if self.params["state"] == "merged":
            self._build_params_spec_for_merged_state()
        if self.params["state"] == "query":
            self._build_params_spec_for_query_state()

    def _build_params_spec_for_merged_state(self) -> None:
        """
        Build the parameter specifications for ``merged`` state.
        """
        self._params_spec: dict = {}
        self._params_spec["ip_address"] = {}
        self._params_spec["ip_address"]["required"] = True
        self._params_spec["ip_address"]["type"] = "ipv4"

        self._params_spec["mode"] = {}
        self._params_spec["mode"]["choices"] = ["normal", "maintenance"]
        self._params_spec["mode"]["default"] = "normal"
        self._params_spec["mode"]["required"] = False
        self._params_spec["mode"]["type"] = "str"

        self._params_spec["deploy"] = {}
        self._params_spec["deploy"]["default"] = False
        self._params_spec["deploy"]["required"] = False
        self._params_spec["deploy"]["type"] = "bool"

        self._params_spec["wait_for_mode_change"] = {}
        self._params_spec["wait_for_mode_change"]["default"] = False
        self._params_spec["wait_for_mode_change"]["required"] = False
        self._params_spec["wait_for_mode_change"]["type"] = "bool"

    def _build_params_spec_for_query_state(self) -> None:
        """
        Build the parameter specifications for ``query`` state.
        """
        self._params_spec: dict = {}
        self._params_spec["ip_address"] = {}
        self._params_spec["ip_address"]["required"] = True
        self._params_spec["ip_address"]["type"] = "ipv4"

    @property
    def params_spec(self) -> dict:
        """
        return the parameter specification
        """
        return self._params_spec

    @property
    def params(self) -> dict:
        """
        ### Summary
        Expects value to be a dictionary containing, at mimimum,
        the key "state" with value of either "merged" or "query".

        ### Raises
        -   setter: raise ``ValueError`` if value is not a dict
        -   setter: raise ``ValueError`` if value["state"] is missing
        -   setter: raise ``ValueError`` if value["state"] is not a valid state

        ### Details
        -   Valid params: {"state": "merged"} or {"state": "query"}
        -   getter: return the params
        -   setter: set the params
        """
        return self._params

    @params.setter
    def params(self, value: dict) -> None:
        """
        -   setter: set the params
        """
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}.setter: "
            msg += "Invalid type. Expected dict but "
            msg += f"got type {type(value).__name__}, "
            msg += f"value {value}."
            raise TypeError(msg)

        if value.get("state", None) is None:
            msg = f"{self.class_name}.{method_name}.setter: "
            msg += "params.state is required but missing."
            raise ValueError(msg)

        if value["state"] not in self.valid_states:
            msg = f"{self.class_name}.{method_name}.setter: "
            msg += f"params.state is invalid: {value['state']}. "
            msg += f"Expected one of {', '.join(self.valid_states)}."
            raise ValueError(msg)

        self._params = value


class Want:
    """
    ### Summary
    Build self.want, a list of validated playbook configurations.

    ### Raises
    -   ``ValueError`` in the following cases:
            -   ``commit()`` is issued before setting mandatory properties
            -   When passing invalid values to property setters
    -   ``TypeError`` in the following cases:
            -   When passing invalid types to property setters


    ### Details
    1. Merge the playbook global config into each switch config.
    2. Validate the merged configs from step 1 against the param spec.
    3. Populate self.want with the validated configs.

    ### Usage
    ```python
    try:
        instance = Want()
        instance.config = playbook_config
        instance.params = ansible_module.params
        instance.params_spec = ParamsSpec()
        instance.items_key = "switches"
        instance.validator = ParamsValidate()
        instance.commit()
        want = instance.want
    except (TypeError, ValueError) as error:
        handle_error(error)
    ```
    ### self.want structure

    ```json
    [
        {
            "ip_address": "192.168.1.2",
            "mode": "maintenance",
            "deploy": false
            "wait_for_mode_change": false
        },
        {
            "ip_address": "192.168.1.3",
            "mode": "normal",
            "deploy": true
            "wait_for_mode_change": true
        }
    ]
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED Want()")

        self._config = None
        self._items_key = None
        self._params = None
        self._params_spec = None
        self._validator = None
        self._want = []

        self.merge_dicts = MergeDicts()
        self.merged_configs = []
        self.item_configs = []

    def generate_params_spec(self) -> None:
        """
        ### Summary
        Generate the params_spec used to validate the configs

        ### Raises
        -   ``ValueError`` if self.params is not set
        -   ``ValueError`` if self.params_spec is not set
        """
        # Generate the params_spec used to validate the configs
        if self.params is None:
            msg = f"{self.class_name}.generate_params_spec(): "
            msg += "params is not set, and is required."
            raise ValueError(msg)
        if self.params_spec is None:
            msg = f"{self.class_name}.generate_params_spec(): "
            msg += "params_spec is not set, and is required."
            raise ValueError(msg)

        try:
            self.params_spec.params = self.params
        except ValueError as error:
            raise ValueError(error) from error

        self.params_spec.commit()

    def validate_configs(self) -> None:
        """
        ### Summary
        Validate the merged configs against the param spec
        and populate self.want with the validated configs.

        ### Raises
        None

        ### Notes
        -   validator is already verified in commit()s
        """
        self.validator.params_spec = self.params_spec.params_spec
        for config in self.merged_configs:
            self.validator.parameters = config
            self.validator.commit()
            self.want.append(copy.deepcopy(config))

    def build_merged_configs(self) -> None:
        """
        ### Summary
        If a parameter is missing from the config, and the parameter
        has a default value, merge the default value for the parameter
        into the config.

        ### Raises
        None
        """
        self.merged_configs = []
        merge_defaults = ParamsMergeDefaults()
        merge_defaults.params_spec = self.params_spec.params_spec
        for config in self.item_configs:
            merge_defaults.parameters = config
            merge_defaults.commit()
            self.merged_configs.append(merge_defaults.merged_parameters)

        msg = f"{self.class_name}.build_merged_configs(): "
        msg += f"merged_configs: {json.dumps(self.merged_configs, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def commit(self) -> None:
        """
        ### Summary
        Build self.want, a list of validated playbook configurations.

        ### Raises
        -   ``ValueError`` if:
                -   self.config is not set
                -   self.item_key is not set
                -   self.params is not set
                -   self.params_spec is not set
                -   self.validator is not set
                -   self.params_spec raises ``ValueError``
                -   _merge_global_and_switch_configs() raises ``ValueError``
                -   merge_dicts() raises `TypeError``` or ``ValueError``
                -   playbook is missing list of items

        ### Details
        See class docstring.

        ### self.want structure
        See class docstring.
        """
        method_name = inspect.stack()[0][3]

        if self.validator is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"self.validator must be set before calling {method_name}."
            raise ValueError(msg)

        try:
            self.generate_params_spec()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error generating params_spec. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        try:
            self._merge_global_and_item_configs()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error merging global and item configs. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        self.build_merged_configs()

        try:
            self.validate_configs()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error validating playbook configs against params spec. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

    def _merge_global_and_item_configs(self) -> None:
        """
        ### Summary
        Builds self.item_configs from self.config

        Merge the global playbook config with each item config and
        populate a list of merged configs (``self.item_configs``).

        ### Raises
        -   ``ValueError`` if self.config is not set
        -   ``ValueError`` if self.items_key is not set
        -   ``ValueError`` if playbook is missing list of items
        -   ``ValueError`` if merge_dicts raises ``TypeError`` or ``ValueError``

        ### Merge rules
            -   item_config takes precedence over global_config.
            -   If item_config is missing a parameter, use parameter
                from global_config.
            -   If item_config has a parameter, use it.
        """
        method_name = inspect.stack()[0][3]

        if self.config is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "config is not set, and is required."
            raise ValueError(msg)
        if self.items_key is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "items_key is not set, and is required."
            raise ValueError(msg)
        if not self.config.get(self.items_key):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"playbook is missing list of {self.items_key}."
            raise ValueError(msg)

        self.item_configs = []
        merged_configs = []
        for item in self.config[self.items_key]:
            # we need to rebuild global_config in this loop
            # because merge_dicts modifies it in place
            global_config = copy.deepcopy(self.config)
            global_config.pop(self.items_key, None)

            msg = f"{self.class_name}.{method_name}: "
            msg += "global_config: "
            msg += f"{json.dumps(global_config, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            msg = f"{self.class_name}.{method_name}: "
            msg += "switch PRE_MERGE: "
            msg += f"{json.dumps(item, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            try:
                self.merge_dicts.dict1 = global_config
                self.merge_dicts.dict2 = item
                self.merge_dicts.commit()
                item_config = self.merge_dicts.dict_merged
            except (TypeError, ValueError) as error:
                msg = f"{self.class_name}.{method_name}: "
                msg += "Error in MergeDicts(). "
                msg += f"Error detail: {error}"
                raise ValueError(msg) from error

            msg = f"{self.class_name}.{method_name}: "
            msg += "switch POST_MERGE: "
            msg += f"{json.dumps(item_config, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            merged_configs.append(item_config)
        self.item_configs = copy.copy(merged_configs)

    @property
    def config(self):
        """
        ### Summary
        The playbook configuration to be processed.

        ``config`` is processed by ``_merge_global_and_switch_configs()``
        to build ``switch_configs``.

        -   getter: return config
        -   setter: set config
        -   setter: raise ``ValueError`` if value is not a dict
        """
        return self._config

    @config.setter
    def config(self, value) -> None:
        if not isinstance(value, dict):
            msg = f"{self.class_name}.config.setter: "
            msg += "expected dict but got "
            msg += f"{type(value).__name__}, value {value}."
            raise TypeError(msg)
        self._config = value

    @property
    def items_key(self) -> str:
        """
        Expects value to be the key for the list of items in the
        playbook config.

        -   getter: return the items_key
        -   setter: set the items_key
        -   setter: raise ``ValueError`` if value is not a string
        """
        return self._items_key

    @items_key.setter
    def items_key(self, value: str) -> None:
        """
        -   setter: set the items_key
        """
        if not isinstance(value, str):
            msg = f"{self.class_name}.items_key.setter: "
            msg += "expected string but got "
            msg += f"{type(value).__name__}, value {value}."
            raise TypeError(msg)
        self._items_key = value

    @property
    def want(self) -> list:
        """
        ### Summary
        Return the want list.  See class docstring for structure details.
        """
        return self._want

    @property
    def params(self) -> dict:
        """
        ### Summary
        The return value of ``AnsibleModule.params`` property
        (or equivalent dict). This is passed to ``params_spec``
        and used in playbook config validation.

        ### Raises
        -   setter: raise ``ValueError`` if value is not a ``dict``.

        ### getter
        Return params

        ### setter
        Set params
        """
        return self._params

    @params.setter
    def params(self, value: dict) -> None:
        """
        -   setter: set the params
        """
        if not isinstance(value, dict):
            msg = f"{self.class_name}.params.setter: "
            msg += "expected dict but got "
            msg += f"{type(value).__name__}, value {value}."
            raise TypeError(msg)
        self._params = value

    @property
    def params_spec(self):
        """
        ### Summary
        The parameter specification used to validate the playbook config.
        Expects value to be an instance of ``ParamsSpec()``.

        ``params_spec`` is passed to ``validator`` to validate the
        playbook config.

        ### Raises
        -   setter: raise ``TypeError`` if value is not an instance
            of ParamsSpec()

        ### getter
        Return params_spec

        ### setter
        Set params_spec
        """
        return self._params_spec

    @params_spec.setter
    def params_spec(self, value) -> None:
        method_name = inspect.stack()[0][3]
        _class_have = None
        _class_need = "ParamsSpec"
        msg = f"{self.class_name}.{method_name}: "
        msg += f"value must be an instance of {_class_need}. "
        msg += f"Got type {type(value).__name__}, "
        msg += f"value {value}. "
        try:
            _class_have = value.class_name
        except AttributeError as error:
            msg += f"Error detail: {error}."
            raise TypeError(msg) from error
        if _class_have != _class_need:
            raise TypeError(msg)
        self._params_spec = value

    @property
    def validator(self):
        """
        ### Summary
        ``validator`` is used to validate the playbook config.
        Expects value to be an instance of ``ParamsValidate()``.

        ### Raises
        -   setter: ``TypeError`` if value is not an instance of ``ParamsValidate()``

        ### getter
        Return validator

        ### setter
        Set validator
        """
        return self._validator

    @validator.setter
    def validator(self, value) -> None:
        method_name = inspect.stack()[0][3]
        _class_have = None
        _class_need = "ParamsValidate"
        msg = f"{self.class_name}.{method_name}: "
        msg += f"value must be an instance of {_class_need}. "
        msg += f"Got type {type(value).__name__}, "
        msg += f"value {value}. "
        try:
            _class_have = value.class_name
        except AttributeError as error:
            msg += f" Error detail: {error}."
            raise TypeError(msg) from error
        if _class_have != _class_need:
            raise TypeError(msg)
        self._validator = value


@Properties.add_rest_send
class Common:
    """
    Common methods, properties, and resources for all states.
    """

    def __init__(self, params):
        """
        ### Raises
        -   ``ValueError`` if:
                -   ``params`` does not contain ``check_mode``
                -   ``params`` does not contain ``state``
                -   ``params`` does not contain ``config``
        -   ``TypeError`` if:
                -   ``config`` is not a dict
        """
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]

        self.params = params
        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.check_mode = self.params.get("check_mode", None)
        if self.check_mode is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "check_mode is required."
            raise ValueError(msg)

        self.state = self.params.get("state", None)
        if self.state is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "state is required."
            raise ValueError(msg)

        self.config = self.params.get("config", None)
        if self.config is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "config is required."
            raise ValueError(msg)
        if not isinstance(self.config, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "Expected dict type for self.config. "
            msg += f"Got {type(self.config).__name__}"
            raise TypeError(msg)

        self._rest_send = None

        self.results = Results()
        self.results.state = self.state
        self.results.check_mode = self.check_mode

        self.have = {}
        # populated in self.validate_input()
        self.payloads = {}
        self.query = []
        self.want = []

        msg = f"ENTERED Common().{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def get_want(self) -> None:
        """
        ### Summary
        Build self.want, a list of validated playbook configurations.

        ### Raises
        -   ``ValueError`` if Want() instance raises ``ValueError``
        """
        try:
            instance = Want()
            instance.config = self.config
            instance.items_key = "switches"
            instance.params = self.params
            instance.params_spec = ParamsSpec()
            instance.validator = ParamsValidate()
            instance.commit()
            self.want = instance.want
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error


class Merged(Common):
    """
    Handle merged state

    ### Raises
    -   ``ValueError`` if Common().__init__() raises ``ValueError``
    """

    def __init__(self, params):
        """
        ### Raises
        -   ``ValueError`` if Common().__init__() raises ``ValueError``
        """
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]
        try:
            super().__init__(params)
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error during super().__init__(). "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.maintenance_mode = MaintenanceMode(params)

        msg = f"ENTERED Merged.{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.need = []

    def get_have(self):
        """
        ### Summary
        Build self.have, a dict containing the current mode of all switches.

        ### Raises
        -   ``ValueError`` if self.ansible_module is not set
        -   ``ValueError`` if MaintenanceModeInfo() raises ``ValueError``

        ### self.have structure
        Have is a dict, keyed on switch_ip, where each element is a dict
        with the following structure:
        -   ``fabric_name``: The name of the switch's hosting fabric.
        -   ``fabric_freeze_mode``: The current ``freezeMode`` state of the switch's
            hosting fabric.  If ``freeze_mode`` is True, configuration changes cannot
            be made to the fabric or the switches within the fabric.
        -   ``fabric_read_only``: The current ``IS_READ_ONLY`` state of the switch's
            hosting fabric.  If ``fabric_read_only`` is True, configuration changes cannot
            be made to the fabric or the switches within the fabric.
        -   ``mode``: The current maintenance mode of the switch.
            Possible values include: , ``inconsistent``, ``maintenance``,
            ``migration``, ``normal``.
        -   ``role``: The role of the switch in the hosting fabric, e.g.
            ``spine``, ``leaf``, ``border_gateway``, etc.
        -   ``serial_number``: The serial number of the switch.

        ```json
        {
            "192.169.1.2": {
                fabric_deployment_disabled: true
                fabric_freeze_mode: true,
                fabric_name: "MyFabric",
                fabric_read_only: true
                mode: "maintenance",
                role: "spine",
                serial_number: "FCI1234567"
            },
            "192.169.1.3": {
                fabric_deployment_disabled: false
                fabric_freeze_mode: false,
                fabric_name: "YourFabric",
                fabric_read_only: false
                mode: "normal",
                role: "leaf",
                serial_number: "FCH2345678"
            }
        }
        ```
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        try:
            instance = MaintenanceModeInfo(self.params)
            instance.rest_send = self.rest_send
            instance.results = self.results
            instance.config = [
                item["ip_address"] for item in self.config.get("switches", {})
            ]
            instance.refresh()
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error while retrieving switch info. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error
        self.have = instance.info

    def fabric_deployment_disabled(self) -> None:
        """
        ### Summary
        Handle the following cases:
        -   switch migration mode is ``migration``
        -   fabric is in read-only mode (IS_READ_ONLY is True)
        -   fabric is in freeze mode (Deployment Disable)

        ### Raises
        -   ``ValueError`` if any of the above cases are true
        """
        method_name = inspect.stack()[0][3]
        for ip_address, value in self.have.items():
            fabric_name = value.get("fabric_name")
            mode = value.get("mode")
            serial_number = value.get("serial_number")
            fabric_deployment_disabled = value.get("fabric_deployment_disabled")
            fabric_freeze_mode = value.get("fabric_freeze_mode")
            fabric_read_only = value.get("fabric_read_only")

            additional_info = "Additional info: "
            additional_info += f"hosting_fabric: {fabric_name}, "
            additional_info += "fabric_deployment_disabled: "
            additional_info += f"{fabric_deployment_disabled}, "
            additional_info += "fabric_freeze_mode: "
            additional_info += f"{fabric_freeze_mode}, "
            additional_info += "fabric_read_only: "
            additional_info += f"{fabric_read_only}, "
            additional_info += f"maintenance_mode: {mode}. "

            if mode == "migration":
                msg = f"{self.class_name}.{method_name}: "
                msg += "Switch maintenance mode is in migration state for the "
                msg += "switch with "
                msg += f"ip_address {ip_address}, "
                msg += f"serial_number {serial_number}. "
                msg += "This indicates that the switch configuration is not "
                msg += "compatible with the switch role in the hosting "
                msg += "fabric.  The issue might be resolved by initiating a "
                msg += "fabric Recalculate & Deploy on the controller. "
                msg += "Failing that, the switch configuration might need to "
                msg += "be manually modified to match the switch role in the "
                msg += "hosting fabric. "
                msg += additional_info
                raise ValueError(msg)

            if fabric_read_only is True:
                msg = f"{self.class_name}.{method_name}: "
                msg += "The hosting fabric is in read-only mode for the "
                msg += f"switch with ip_address {ip_address}, "
                msg += f"serial_number {serial_number}. "
                msg += "The issue can be resolved for LAN_Classic fabrics by "
                msg += "unchecking 'Fabric Monitor Mode' in the fabric "
                msg += "settings on the controller. "
                msg += additional_info
                raise ValueError(msg)

            if fabric_freeze_mode is True:
                msg = f"{self.class_name}.{method_name}: "
                msg += "The hosting fabric is in "
                msg += "'Deployment Disable' state for the switch with "
                msg += f"ip_address {ip_address}, "
                msg += f"serial_number {serial_number}. "
                msg += "Review the 'Deployment Enable / Deployment Disable' "
                msg += "setting on the controller at: "
                msg += "Fabric Controller > Overview > "
                msg += "Topology > <fabric> > Actions > More, and change "
                msg += "the setting to 'Deployment Enable'. "
                msg += additional_info
                raise ValueError(msg)

    def get_need(self):
        """
        ### Summary
        Build self.need for merged state.

        ### Raises
        -   ``ValueError`` if the switch is not found on the controller.

        ### self.need structure
        ```json
        [
            {
                "deploy": false,
                "fabric_name": "MyFabric",
                "ip_address": "172.22.150.2",
                "mode": "maintenance",
                "serial_number": "FCI1234567"
                "wait_for_mode_change": true
            },
            {
                "deploy": true,
                "fabric_name": "YourFabric",
                "ip_address": "172.22.150.3",
                "mode": "normal",
                "serial_number": "HMD2345678"
                "wait_for_mode_change": true
            }
        ]
        """
        method_name = inspect.stack()[0][3]
        self.need = []
        for want in self.want:
            ip_address = want.get("ip_address", None)
            if ip_address not in self.have:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Switch {ip_address} not found on the controller."
                raise ValueError(msg)

            serial_number = self.have[ip_address]["serial_number"]
            fabric_name = self.have[ip_address]["fabric_name"]
            if want.get("mode") != self.have[ip_address]["mode"]:
                need = want
                need.update({"deploy": want.get("deploy")})
                need.update({"fabric_name": fabric_name})
                need.update({"ip_address": ip_address})
                need.update({"mode": want.get("mode")})
                need.update({"serial_number": serial_number})
                need.update({"wait_for_mode_change": want.get("wait_for_mode_change")})
                self.need.append(copy.copy(need))

    def commit(self):
        """
        ### Summary
        Commit the merged state request

        ### Raises
        -   ``ValueError`` if:
                -   ``rest_send`` is not set.
                -   ``get_want()`` raises ``ValueError``
                -   ``get_have()`` raises ``ValueError``
                -   ``send_need()`` raises ``ValueError``
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: entered"
        self.log.debug(msg)

        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set before calling commit."
            raise ValueError(msg)

        try:
            self.get_want()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error while retrieving playbook config. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        if len(self.want) == 0:
            return

        try:
            self.get_have()
        except ValueError as error:
            raise ValueError(error) from error

        self.fabric_deployment_disabled()

        self.get_need()

        try:
            self.send_need()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error while sending maintenance mode request. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

    def send_need(self) -> None:
        """
        ### Summary
        Build and send the payload to modify maintenance mode.

        ### Raises
        -   ``ValueError`` if MaintenanceMode() raises either
            ``TypeError`` or ``ValueError``

        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        if len(self.need) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "No switches to modify."
            self.log.debug(msg)
            return

        try:
            self.maintenance_mode.rest_send = self.rest_send
            self.maintenance_mode.results = self.results
            self.maintenance_mode.config = self.need
            self.maintenance_mode.commit()
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error


class Query(Common):
    """
    Handle query state

    ### Raises
    -   ``ValueError`` if Common().__init__() raises ``ValueError``
    -   ``ValueError`` if get_want() raises ``ValueError``
    -   ``ValueError`` if get_have() raises ``ValueError``
    """

    def __init__(self, params):
        """
        ### Raises
        -   ``ValueError`` if Common().__init__() raises ``ValueError``
        """
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]
        try:
            super().__init__(params)
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error during super().__init__(). "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.maintenance_mode_info = MaintenanceModeInfo(self.params)

        msg = "ENTERED Query(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def get_have(self):
        """
        ### Summary
        Build self.have, a dict containing the current mode of all switches.

        ### Raises
        -   ``ValueError`` if MaintenanceModeInfo() raises ``ValueError``

        ### self.have structure
        Have is a dict, keyed on switch_ip, where each element is a dict
        with the following structure:
        -   ``fabric_name``: The name of the switch's hosting fabric.
        -   ``fabric_freeze_mode``: The current ``freezeMode`` state of the switch's
            hosting fabric.  If ``freeze_mode`` is True, configuration changes cannot
            be made to the fabric or the switches within the fabric.
        -   ``fabric_read_only``: The current ``IS_READ_ONLY`` state of the switch's
            hosting fabric.  If ``fabric_read_only`` is True, configuration changes cannot
            be made to the fabric or the switches within the fabric.
        -   ``mode``: The current maintenance mode of the switch.
            Possible values include: , ``inconsistent``, ``maintenance``,
            ``migration``, ``normal``.
        -   ``role``: The role of the switch in the hosting fabric, e.g.
            ``spine``, ``leaf``, ``border_gateway``, etc.
        -   ``serial_number``: The serial number of the switch.

        ```json
        {
            "192.169.1.2": {
                fabric_deployment_disabled: true
                fabric_freeze_mode: true,
                fabric_name: "MyFabric",
                fabric_read_only: true
                mode: "maintenance",
                role: "spine",
                serial_number: "FCI1234567"
            },
            "192.169.1.3": {
                fabric_deployment_disabled: false
                fabric_freeze_mode: false,
                fabric_name: "YourFabric",
                fabric_read_only: false
                mode: "normal",
                role: "leaf",
                serial_number: "FCH2345678"
            }
        }
        ```
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        try:
            self.maintenance_mode_info.rest_send = self.rest_send
            self.maintenance_mode_info.results = self.results
            self.maintenance_mode_info.config = [
                item["ip_address"] for item in self.config.get("switches", {})
            ]
            self.maintenance_mode_info.refresh()
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error while retrieving switch info. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error
        self.have = self.maintenance_mode_info.info

    def commit(self) -> None:
        """
        ### Summary
        Query the switches in self.want that exist on the controller
        and update ``self.results`` with the query results.

        ### Raises
        -   ``ValueError`` if:
                -   ``rest_send`` is not set.
                -   ``get_want()`` raises ``ValueError``
                -   ``get_have()`` raises ``ValueError``
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: entered"
        self.log.debug(msg)

        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set before calling commit."
            raise ValueError(msg)

        try:
            self.get_want()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error while retrieving playbook config. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        if len(self.want) == 0:
            return

        try:
            self.get_have()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error while retrieving switch information "
            msg += "from the controller. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        # If we got this far, the requests were successful.
        self.results.action = "maintenance_mode_info"
        self.results.changed = False
        self.results.diff_current = self.have
        self.results.failed = False
        self.results.response_current = {"MESSAGE": "MaintenanceModeInfo OK."}
        self.results.response_current.update({"METHOD": "NA"})
        self.results.response_current.update({"REQUEST_PATH": "NA"})
        self.results.response_current.update({"RETURN_CODE": 200})
        self.results.result_current = {"changed": False, "success": True}
        self.results.register_task_result()


def main():
    """main entry point for module execution"""

    argument_spec = {}
    argument_spec["config"] = {
        "required": True,
        "type": "dict",
    }
    argument_spec["state"] = {
        "choices": ["merged", "query"],
        "default": "merged",
        "required": False,
        "type": "str",
    }

    ansible_module = AnsibleModule(
        argument_spec=argument_spec, supports_check_mode=True
    )
    params = copy.deepcopy(ansible_module.params)
    params["check_mode"] = ansible_module.check_mode

    # Logging setup
    try:
        log = Log()
        log.commit()
    except ValueError as error:
        ansible_module.fail_json(str(error))

    sender = Sender()
    sender.ansible_module = ansible_module
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    if params["state"] == "merged":
        try:
            task = Merged(params)
            task.rest_send = rest_send  # pylint: disable=attribute-defined-outside-init
            task.commit()
        except ValueError as error:
            ansible_module.fail_json(f"{error}", **task.results.failed_result)

    elif params["state"] == "query":
        try:
            task = Query(params)
            task.rest_send = rest_send  # pylint: disable=attribute-defined-outside-init
            task.commit()
        except ValueError as error:
            ansible_module.fail_json(f"{error}", **task.results.failed_result)

    else:
        # We should never get here since the state parameter has
        # already been validated.
        msg = f"Unknown state {params['state']}"
        ansible_module.fail_json(msg)

    task.results.build_final_result()

    # Results().failed is a property that returns a set()
    # of boolean values.  pylint doesn't seem to understand this so we've
    # disabled the unsupported-membership-test warning.
    if True in task.results.failed:  # pylint: disable=unsupported-membership-test
        msg = "Module failed."
        ansible_module.fail_json(msg, **task.results.final_result)
    ansible_module.exit_json(**task.results.final_result)


if __name__ == "__main__":
    main()
