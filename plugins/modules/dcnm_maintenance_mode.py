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
version_added: "3.5.0"
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
                description:
                - Whether to deploy the switch configurations.
                default: False
                required: false
                type: bool
            mode:
                default: maintenance
                description:
                - Enable maintenance or normal mode on all switches.
                required: false
                type: bool
            switches:
                description:
                - A list of target switches.
                - Per-switch options override the global options.
                required: false
                type: list
                elements: dict
                suboptions:
                    ip_address:
                        description:
                        - The IP address of the switch.
                        required: true
                        type: str
                    mode:
                        description:
                        - Enable maintenance or normal mode for the switch.
                        required: true
                        type: str
                    deploy:
                        default: False
                        description:
                        - Whether to deploy the switch configuration.
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
        deploy: false
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
from os import environ
from typing import Any, Dict

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.common.exceptions import \
    ControllerResponseError
from ansible_collections.cisco.dcnm.plugins.module_utils.common.log import Log
from ansible_collections.cisco.dcnm.plugins.module_utils.common.maintenance_mode import \
    MaintenanceMode
from ansible_collections.cisco.dcnm.plugins.module_utils.common.merge_dicts_v2 import \
    MergeDicts
from ansible_collections.cisco.dcnm.plugins.module_utils.common.params_merge_defaults_v2 import \
    ParamsMergeDefaults
from ansible_collections.cisco.dcnm.plugins.module_utils.common.params_validate_v2 import \
    ParamsValidate
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.common.switch_details import \
    SwitchDetails
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details import \
    FabricDetailsByName


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

        self._properties = {}
        self._properties["params"] = None
        self._params_spec: Dict[str, Any] = {}

        self.valid_states = ["merged", "query"]

    def commit(self):
        """
        Build the parameter specification based on the state

        ## Raises
        -   ValueError if params.state is not a valid state for
            the dcnm_maintenance_mode module
        """
        method_name = inspect.stack()[0][3]

        if self.params["state"] not in self.valid_states:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Invalid state {self.params['state']}. "
            msg += f"Expected one of {', '.join(self.valid_states)}."
            raise ValueError(msg)

        if self.params["state"] == "merged":
            self._build_params_spec_for_merged_state()
        if self.params["state"] == "query":
            self._build_params_spec_for_query_state()

    def _build_params_spec_for_merged_state(self) -> Dict[str, Any]:
        """
        Build the parameter specifications for ``merged`` state.
        """
        self._params_spec: Dict[str, Any] = {}
        self._params_spec["ip_address"] = {}
        self._params_spec["ip_address"]["required"] = True
        self._params_spec["ip_address"]["type"] = "ipv4"

        self._params_spec["mode"] = {}
        self._params_spec["mode"]["required"] = False
        self._params_spec["mode"]["type"] = "str"

        self._params_spec["deploy"] = {}
        self._params_spec["deploy"]["required"] = False
        self._params_spec["deploy"]["type"] = "bool"
        self._params_spec["deploy"]["default"] = False

    def _build_params_spec_for_query_state(self) -> Dict[str, Any]:
        """
        Build the parameter specifications for ``query`` state.
        """
        self._params_spec: Dict[str, Any] = {}
        self._params_spec["ip_address"] = {}
        self._params_spec["ip_address"]["required"] = True
        self._params_spec["ip_address"]["type"] = "ipv4"

    @property
    def params_spec(self) -> Dict[str, Any]:
        """
        return the parameter specification
        """
        return self._params_spec

    @property
    def params(self) -> Dict[str, Any]:
        """
        Expects value to be the return value of
        ``AnsibleModule.params`` property.

        -   getter: return the params
        -   setter: set the params
        -   setter: raise ``ValueError`` if value is not a dict
        """
        return self._properties["params"]

    @params.setter
    def params(self, value: Dict[str, Any]) -> None:
        """
        -   setter: set the params
        """
        if not isinstance(value, dict):
            msg = f"{self.class_name}.params.setter: "
            msg += "expected dict type for value. "
            msg += f"got {type(value).__name__}."
            raise ValueError(msg)
        self._properties["params"] = value


class Want:
    """
    ### Summary
    Build self.want, a list of validated playbook configurations.

    ### Raises
    -   ``ValueError`` if ParamsSpec() raises ``ValueError``
    -   ``ValueError`` _merge_global_and_switch_configs()
        raises ``ValueError``

    ### Details
    1. Merge the playbook global config into each switch config.
    2. Validate the merged configs from step 1 against the param spec.
    3. Populate self.want with the validated configs.

    ### Usage
    ```python
    instance = Want()
    instance.params = ansible_module.params
    instance.params_spec = ParamsSpec()
    instance.results = Results()
    instance.items_key = "switches"
    instance.validator = ParamsValidate()
    instance.commit()
    want = instance.want
    ```
    ### self.want structure

    ```json
    [
        {
            "ip_address": "192.168.1.2",
            "mode": "maintenance",
            "deploy": false
        },
        {
            "ip_address": "192.168.1.3",
            "mode": "normal",
            "deploy": true
        }
    ]
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED Want()")

        self._properties = {}
        self._properties["config"] = None
        self._properties["items_key"] = None
        self._properties["params"] = None
        self._properties["params_spec"] = None
        self._properties["results"] = None
        self._properties["validator"] = None
        self._properties["want"] = []

        self.merged_configs = []
        self.item_configs = []
        self.validator = None

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
            msg += "self.params is required"
            raise ValueError(msg)
        if self.params_spec is None:
            msg = f"{self.class_name}.generate_params_spec(): "
            msg += "self.params_spec is required"
            raise ValueError(msg)

        try:
            self.params_spec.params = self.params
        except ValueError as error:
            raise ValueError(error) from error

        try:
            self.params_spec.commit()
        except ValueError as error:
            raise ValueError(error) from error

    def validate_configs(self) -> None:
        """
        ### Summary
        Validate the merged configs against the param spec
        and populate self.want with the validated configs.

        ### Raises
        -   ``ValueError`` if self.validator is not set

        """
        if self.validator is None:
            msg = f"{self.class_name}.validate_configs(): "
            msg += "self.validator is required"
            raise ValueError(msg)

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
        -   ``ValueError`` if self.params is not set
        -   ``ValueError`` if self.params_spec is not set
        -   ``ValueError`` if self.validator is not set
        -   ``ValueError`` if self.params_spec raises ``ValueError``
        -   ``ValueError`` if _merge_global_and_switch_configs()
            raises ``ValueError``

        ### Details
        See class docstring.

        ### self.want structure
        See class docstring.
        """
        method_name = inspect.stack()[0][3]

        if self.validator is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"self.validator must be set before calling {method_name}"
            raise ValueError(msg)

        try:
            self.generate_params_spec()
        except ValueError as error:
            raise ValueError(error) from error

        try:
            self._merge_global_and_item_configs()
        except ValueError as error:
            raise ValueError(error) from error

        self.build_merged_configs()

        try:
            self.validate_configs()
        except ValueError as error:
            raise ValueError(error) from error

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
            msg += "self.config is required"
            raise ValueError(msg)
        if self.items_key is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "self.items_key is required"
            raise ValueError(msg)
        if not self.config.get(self.items_key):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"playbook is missing list of {self.items_key}"
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

            merge_dicts = MergeDicts()
            try:
                merge_dicts.dict1 = global_config
                merge_dicts.dict2 = item
                merge_dicts.commit()
                item_config = merge_dicts.dict_merged
            except (TypeError, ValueError) as error:
                raise ValueError(error) from error

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
        return self._properties["config"]

    @config.setter
    def config(self, value) -> None:
        if not isinstance(value, dict):
            msg = f"{self.class_name}.config.setter: "
            msg += "expected dict for value. "
            msg += f"got {type(value).__name__}."
            raise ValueError(msg)
        self._properties["config"] = value

    @property
    def items_key(self) -> str:
        """
        Expects value to be the key for the list of items in the
        playbook config.

        -   getter: return the items_key
        -   setter: set the items_key
        -   setter: raise ``ValueError`` if value is not a string
        """
        return self._properties["items_key"]

    @items_key.setter
    def items_key(self, value: str) -> None:
        """
        -   setter: set the items_key
        """
        if not isinstance(value, str):
            msg = f"{self.class_name}.items_key.setter: "
            msg += "expected string type for value. "
            msg += f"got {type(value).__name__}."
            raise ValueError(msg)
        self._properties["items_key"] = value

    @property
    def want(self) -> Dict[str, Any]:
        """
        return the want list
        """
        return self._properties["want"]

    @property
    def params(self) -> Dict[str, Any]:
        """
        Expects value to be the return value of
        ``AnsibleModule.params`` property.

        -   getter: return the params
        -   setter: set the params
        -   setter: raise ``ValueError`` if value is not a dict
        """
        return self._properties["params"]

    @params.setter
    def params(self, value: Dict[str, Any]) -> None:
        """
        -   setter: set the params
        """
        if not isinstance(value, dict):
            msg = f"{self.class_name}.params.setter: "
            msg += "expected dict type for value. "
            msg += f"got {type(value).__name__}."
            raise ValueError(msg)
        self._properties["params"] = value

    @property
    def params_spec(self):
        """
        ### Summary
        Expects value to be an instance of ParamsSpec().

        ``params_spec`` is passed to ``validator`` to validate the
        playbook config.

        -   getter: return the params_spec instance
        -   setter: set the params_spec instance
        -   setter: raise ``ValueError`` if value is not an instance
            of ParamsSpec()
        """
        return self._properties["params_spec"]

    @params_spec.setter
    def params_spec(self, value) -> None:
        """
        -   setter: set the params_spec instance
        """
        if not isinstance(value, ParamsSpec):
            msg = f"{self.class_name}.params_spec.setter: "
            msg += "expected ParamsSpec() instance for value. "
            msg += f"got {type(value).__name__}."
            raise ValueError(msg)
        self._properties["params_spec"] = value

    @property
    def validator(self) -> Any:
        """
        getter: return the validator
        setter: set the validator
        """
        return self._properties["validator"]

    @validator.setter
    def validator(self, value: Any) -> None:
        """
        setter: set the validator
        """
        self._properties["validator"] = value


class Common:
    """
    Common methods, properties, and resources for all states.
    """

    def __init__(self, params):
        """
        ### Raises
        -   ``ValueError`` if params does not contain ``check_mode``
        -   ``ValueError`` if params does not contain ``state``
        """
        self.class_name = self.__class__.__name__
        self.params = params
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.check_mode = self.params.get("check_mode", None)
        if self.check_mode is None:
            msg = f"{self.class_name}.__init__(): "
            msg += "check_mode is required"
            raise ValueError(msg)

        self.state = self.params.get("state", None)
        if self.state is None:
            msg = f"{self.class_name}.__init__(): "
            msg += "state is required"
            raise ValueError(msg)

        self._init_properties()

        self.results = Results()
        self.results.state = self.state
        self.results.check_mode = self.check_mode

        self.switch_details = SwitchDetails()
        self.switch_details.results = self.results

        msg = f"ENTERED Common().{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        # populated in self.validate_input()
        self.payloads = {}

        self.config = self.params.get("config")
        if not isinstance(self.config, dict):
            msg = "expected dict type for self.config. "
            msg += f"got {type(self.config).__name__}"
            raise ValueError(msg)

        self.have = {}
        self.query = []
        self.want = []

    def _init_properties(self):
        self._properties = {}
        self._properties["ansible_module"] = None

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
        except ValueError as error:
            raise ValueError(error) from error
        # Exit if there's nothing to do
        if len(self.want) == 0:
            self.ansible_module.exit_json(**self.results.ok_result)

    @property
    def ansible_module(self):
        """
        getter: return an instance of AnsibleModule
        setter: set an instance of AnsibleModule
        """
        return self._properties["ansible_module"]

    @ansible_module.setter
    def ansible_module(self, value):
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        if not isinstance(value, AnsibleModule):
            msg = f"{self.class_name}.{method_name}: "
            msg += "expected AnsibleModule instance. "
            msg += f"got {type(value).__name__}."
            raise ValueError(msg)
        self._properties["ansible_module"] = value


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
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Error: {error}"
            raise ValueError(msg) from error

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.fabric_details = FabricDetailsByName(self.params)
        self.rest_send = None

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
        -   ``ValueError`` if SwitchDetails() raises ``ControllerResponseError``
            or ``ValueError``
        -   ``ValueError`` if the switch's hosting fabric is in ``freezeMode``
        -   ``ValueError`` if the switch's maintenance mode is ``inconsistent``
        -   ``ValueError`` if the switch's maintenance mode is ``migration``

        ### self.have structure
        Have is a dict, keyed on switch_ip, where each element is a dict
        with the following structure:
        -   ``fabric_name``: The name of the switch's hosting fabric.
        -   ``mode``: The current maintenance mode of the switch.
        -   ``role``: The role of the switch in the hosting fabric.
        -   ``serial_number``: The serial number of the switch.

        ```json
        {
            "192.169.1.2": {
                fabric_name: "MyFabric",
                mode: "maintenance",
                serial_number: "FCI1234567"
            },
            "192.169.1.3": {
                fabric_name: "YourFabric",
                mode: "normal",
                serial_number: "FCH2345678"
            }
        }
        ```
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        if self.ansible_module is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"ansible_module must be set before calling {method_name}"
            raise ValueError(msg)

        self.switch_details.rest_send = RestSend(self.ansible_module)
        try:
            self.switch_details.refresh()
        except (ControllerResponseError, ValueError) as error:
            raise ValueError(error) from error

        self.fabric_details.rest_send = RestSend(self.ansible_module)
        self.fabric_details.results = self.results
        self.fabric_details.refresh()

        self.have = {}
        # self.config has already been validated
        for switch in self.config.get("switches"):
            ip_address = switch.get("ip_address")
            self.switch_details.filter = ip_address

            try:
                fabric_name = self.switch_details.fabric_name
            except ValueError as error:
                raise ValueError(error) from error

            if self.switch_details.freeze_mode is True:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Fabric {fabric_name} is in freeze mode. "
                msg += "Configuration changes are not allowed. "
                msg += "Ensure that NDFC -> Topology -> Fabric -> Actions -> "
                msg += "More -> Deployment Enable is selected."
                raise ValueError(msg)

            try:
                self.fabric_details.filter = fabric_name
            except ValueError as error:
                raise ValueError(error) from error

            if self.fabric_details.is_read_only is True:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Fabric {fabric_name} is in read-only mode. "
                msg += "Configuration changes are not allowed."
                raise ValueError(msg)

            try:
                serial_number = self.switch_details.serial_number
            except ValueError as error:
                raise ValueError(error) from error

            if serial_number is None:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Switch with ip_address {ip_address} "
                msg += "does not exist on the controller."
                raise ValueError(msg)

            mode = self.switch_details.maintenance_mode
            if mode == "inconsistent":
                msg = f"{self.class_name}.{method_name}: "
                msg += "Switch maintenance mode state differs from the "
                msg += "controller's maintenance mode state for switch "
                msg += f"with ip_address {ip_address}. This is typically "
                msg += "resolved by initiating a switch Deploy Config on "
                msg += "the controller."
                raise ValueError(msg)

            if mode == "migration":
                msg = f"{self.class_name}.{method_name}: "
                msg += "Switch maintenance mode is in migration state for the "
                msg += f"switch with ip_address {ip_address}. "
                msg += "This indicates that the switch configuration is not "
                msg += "compatible with the switch role in the hosting "
                msg += "fabric.  The issue might be resolved by initiating a "
                msg += "fabric Recalculate & Deploy on the controller. "
                msg += "Failing that, the switch configuration might need to be "
                msg += "manually modified to match the switch role in the "
                msg += "hosting fabric."
                raise ValueError(msg)

            self.have[ip_address] = {}
            self.have[ip_address].update({"fabric_name": fabric_name})
            self.have[ip_address].update({"mode": mode})
            self.have[ip_address].update({"serial_number": serial_number})

    def get_need(self):
        """
        ### Summary
        Build self.need for merged state.

        ### Raises
        None

        ### self.need structure
        ```json
        [
            {
                "deploy": false,
                "fabric_name": "MyFabric",
                "ip_address": "172.22.150.2",
                "mode": "maintenance",
                "serial_number": "FCI1234567"
            },
            {
                "deploy": true,
                "fabric_name": "YourFabric",
                "ip_address": "172.22.150.3",
                "mode": "normal",
                "serial_number": "HMD2345678"
            }
        ]
        """
        self.need = []
        for want in self.want:
            ip_address = want.get("ip_address", None)
            if ip_address not in self.have:
                continue
            serial_number = self.have[ip_address]["serial_number"]
            fabric_name = self.have[ip_address]["fabric_name"]
            if want.get("mode") != self.have[ip_address]["mode"]:
                need = want
                need.update({"deploy": want.get("deploy")})
                need.update({"fabric_name": fabric_name})
                need.update({"ip_address": ip_address})
                need.update({"mode": want.get("mode")})
                need.update({"serial_number": serial_number})
                self.need.append(copy.copy(need))

    def commit(self):
        """
        ### Summary
        Commit the merged state request

        ### Raises
        -   ``ValueError`` if get_want() raises ``ValueError``
        -   ``ValueError`` if get_have() raises ``ValueError``
        -   ``ValueError`` if send_need() raises ``ValueError``
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        msg = f"{self.class_name}.{method_name}: entered"
        self.log.debug(msg)

        self.rest_send = RestSend(self.ansible_module)

        try:
            self.get_want()
        except ValueError as error:
            raise ValueError(error) from error

        try:
            self.get_have()
        except ValueError as error:
            raise ValueError(error) from error

        self.get_need()

        try:
            self.send_need()
        except ValueError as error:
            raise ValueError(error) from error

    def send_need(self) -> None:
        """
        ### Summary
        Build and send the payload to modify maintenance mode.

        ### Raises
        -   ``ValueError`` if MaintenanceMode() raises ``ValueError``

        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        msg = f"{self.class_name}.{method_name}: entered. "
        msg += f"self.need: {json_pretty(self.need)}"
        self.log.debug(msg)

        if len(self.need) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "No switches to modify."
            self.log.debug(msg)
            return

        instance = MaintenanceMode(self.params)
        instance.rest_send = self.rest_send
        instance.results = self.results
        try:
            instance.config = self.need
        except ValueError as error:
            raise ValueError(error) from error
        try:
            instance.commit()
        except ValueError as error:
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
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Error: {error}"
            raise ValueError(msg) from error

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.fabric_details = FabricDetailsByName(self.params)

        msg = "ENTERED Query(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def get_have(self):
        """
        ### Summary
        Build self.have, a dict containing the current mode of all switches.

        ### Raises
        -   ``ValueError`` if self.ansible_module is not set
        -   ``ValueError`` if SwitchDetails() raises ``ControllerResponseError``
        -   ``ValueError`` if SwitchDetails() raises ``ValueError``

        ### self.have structure
        Have is a dict, keyed on switch_ip, where each element is a dict
        with the following structure:
        -   ``fabric_name``: The name of the switch's hosting fabric.
        -   ``freeze_mode``: The current state of the switch's hosting fabric.
            If freeze_mode is True, configuration changes cannot be made to the
            fabric or the switches within the fabric.
        -   ``mode``: The current maintenance mode of the switch.
        -   ``role``: The role of the switch in the hosting fabric.
        -   ``serial_number``: The serial number of the switch.

        ```json
        {
            "192.169.1.2": {
                deployment_disabled: true
                fabric_name: "MyFabric",
                mode: "maintenance",
                role: "spine",
                serial_number: "FCI1234567"
            },
            "192.169.1.3": {
                deployment_disabled: false
                fabric_name: "YourFabric",
                mode: "normal",
                role: "leaf",
                serial_number: "FCH2345678"
            }
        }
        ```
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        if self.ansible_module is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"ansible_module must be set before calling {method_name}"
            raise ValueError(msg)

        self.switch_details.rest_send = RestSend(self.ansible_module)
        self.fabric_details.rest_send = RestSend(self.ansible_module)

        try:
            self.switch_details.refresh()
        except (ControllerResponseError, ValueError) as error:
            raise ValueError(error) from error

        try:
            self.fabric_details.refresh()
        except (ControllerResponseError, ValueError) as error:
            raise ValueError(error) from error

        self.have = {}
        # self.config has already been validated
        for switch in self.config.get("switches"):
            ip_address = switch.get("ip_address")
            self.switch_details.filter = ip_address

            try:
                serial_number = self.switch_details.serial_number
            except ValueError as error:
                raise ValueError(error) from error

            if serial_number is None:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Switch with ip_address {ip_address} "
                msg += "does not exist on the controller."
                raise ValueError(msg)

            fabric_name = self.switch_details.fabric_name
            freeze_mode = self.switch_details.freeze_mode
            mode = self.switch_details.maintenance_mode
            role = self.switch_details.switch_role

            try:
                self.fabric_details.filter = fabric_name
            except ValueError as error:
                raise ValueError(error) from error
            fabric_read_only = self.fabric_details.is_read_only

            self.have[ip_address] = {}
            self.have[ip_address].update({"fabric_name": fabric_name})
            if freeze_mode is True or fabric_read_only is True:
                self.have[ip_address].update({"deployment_disabled": True})
            else:
                self.have[ip_address].update({"deployment_disabled": False})
            self.have[ip_address].update({"mode": mode})
            if role is not None:
                self.have[ip_address].update({"role": role})
            else:
                self.have[ip_address].update({"role": "na"})
            self.have[ip_address].update({"serial_number": serial_number})

    def commit(self) -> None:
        """
        ### Summary
        Query the switches in self.want that exist on the controller
        and update ``self.results`` with the query results.

        ### Raises
        -   ``ValueError`` if get_want() raises ``ValueError``
        -   ``ValueError`` if get_have() raises ``ValueError``
        """
        try:
            self.get_want()
        except ValueError as error:
            raise ValueError(error) from error

        try:
            self.get_have()
        except ValueError as error:
            raise ValueError(error) from error

        # If we got this far, the request was successful.
        self.results.diff_current = self.have
        self.results.changed = False
        self.results.action = "query"
        self.results.failed = False
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
    log = Log(ansible_module)

    # Create the base/parent logger for the dcnm collection.
    # Set the following environment variable to enable logging:
    #   - NDFC_LOGGING_CONFIG=<path to logging_config.json>
    # logging_config.json must be must be conformant with logging.config.dictConfig
    # and must not log to the console.
    # For an example logging_config.json configuration, see:
    # $ANSIBLE_COLLECTIONS_PATH/cisco/dcnm/plugins/module_utils/common/logging_config.json
    config_file = environ.get("NDFC_LOGGING_CONFIG", None)
    if config_file is not None:
        log.config = config_file
    try:
        log.commit()
    except json.decoder.JSONDecodeError as error:
        msg = f"Invalid logging configuration file: {log.config}. "
        msg += f"Error detail: {error}"
        ansible_module.fail_json(msg)
    except ValueError as error:
        msg = f"Invalid logging configuration file: {log.config}. "
        msg += f"Error detail: {error}"
        ansible_module.fail_json(msg)

    ansible_module.params["check_mode"] = ansible_module.check_mode
    if ansible_module.params["state"] == "merged":
        try:
            task = Merged(ansible_module.params)
            task.ansible_module = ansible_module
            task.commit()
        except ValueError as error:
            ansible_module.fail_json(f"{error}", **task.results.failed_result)

    elif ansible_module.params["state"] == "query":
        try:
            task = Query(ansible_module.params)
            task.ansible_module = ansible_module
            task.commit()
        except ValueError as error:
            ansible_module.fail_json(f"{error}", **task.results.failed_result)

    else:
        # We should never get here since the state parameter has
        # already been validated.
        msg = f"Unknown state {ansible_module.params['state']}"
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
