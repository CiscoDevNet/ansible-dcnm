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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.log import Log
from ansible_collections.cisco.dcnm.plugins.module_utils.common.maintenance_mode import \
    MaintenanceMode
from ansible_collections.cisco.dcnm.plugins.module_utils.common.merge_dicts import \
    MergeDicts
from ansible_collections.cisco.dcnm.plugins.module_utils.common.params_merge_defaults import \
    ParamsMergeDefaults
from ansible_collections.cisco.dcnm.plugins.module_utils.common.params_validate import \
    ParamsValidate
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.common.switch_details import \
    SwitchDetails


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
    params_spec.params = ansible_module.params
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
        self._properties["params"] = value


class Common:
    """
    Common methods, properties, and resources for all states.
    """

    def __init__(self, params):
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

        self.params_spec = ParamsSpec()
        self.params_spec.params = self.params
        try:
            self.params_spec.commit()
        except ValueError as error:
            self.ansible_module.fail_json(error, **self.results.failed_result)

        msg = f"ENTERED Common().{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.switch_details = SwitchDetails()
        self.switch_details.results = self.results

        # populated in self.validate_input()
        self.payloads = {}

        # populated in self.get_want()
        self.validated_configs = []

        self.config = self.params.get("config")
        if not isinstance(self.config, dict):
            msg = "expected dict type for self.config. "
            msg += f"got {type(self.config).__name__}"
            raise ValueError(msg)

        self.validator = ParamsValidate(self.ansible_module)

        self.validated = []
        self.have = {}
        self.want = []
        self.query = []
        self._implemented_states = set()
        # populated in self._merge_global_and_switch_configs()
        self.switch_configs = []

    def _init_properties(self):
        self._properties = {}
        self._properties["ansible_module"] = None

    def get_have(self):
        """
        Caller: main()

        Build self.have, a dict containing the current mode of all switches.

        Have is a dict, keyed on switch_ip, where each element is a dict
        with the following structure:

        ```json
        {
            "192.169.1.2": {
                fabric_name: "MyFabric",
                maintenance_mode: "Maintenance",
                serial_number: "FCI1234567"
            },
            "192.169.1.3": {
                fabric_name: "YourFabric",
                maintenance_mode: "Normal",
                serial_number: "FCH2345678"
            }
        }
        ```
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self.switch_details.rest_send = RestSend(self.ansible_module)
        self.switch_details.refresh()
        self.have = {}
        # self.config has already been validated
        for switch in self.config.get("switches"):
            ip_address = switch.get("ip_address")
            self.switch_details.filter = ip_address
            serial_number = self.switch_details.serial_number
            if serial_number is None:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Switch with ip_address {ip_address} "
                msg += "does not exist on the controller."
                self.ansible_module.fail_json(msg, **self.results.failed_result)
            mode = self.switch_details.maintenance_mode
            fabric_name = self.switch_details.fabric_name
            self.have[ip_address] = {}
            self.have[ip_address].update({"maintenance_mode": mode})
            self.have[ip_address].update({"serial_number": serial_number})
            self.have[ip_address].update({"fabric_name": fabric_name})

    def get_want(self) -> None:
        """
        Caller: main()

        1. Merge the global config into each switch config
        2. Validate the merged configs
        3. Populate self.want with the validated configs

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
                "mode": "maintenance",
                "deploy": false
            }
        ]
        ```
        """
        msg = "ENTERED"
        self.log.debug(msg)
        # Generate the params_spec used to validate the configs
        params_spec = ParamsSpec()
        params_spec.params = self.params
        params_spec.commit()

        # Builds self.switch_configs
        self._merge_global_and_switch_configs(self.config)

        # If a parameter is missing from the config, and the parameter
        # has a default value, merge the default value for the parameter
        # into the config.
        merged_configs = []
        merge_defaults = ParamsMergeDefaults(self.ansible_module)
        merge_defaults.params_spec = params_spec.params_spec
        for config in self.switch_configs:
            merge_defaults.parameters = config
            merge_defaults.commit()
            merged_configs.append(merge_defaults.merged_parameters)

        # validate the merged configs
        self.validated_configs = []
        self.validator.params_spec = params_spec.params_spec
        for config in merged_configs:
            self.validator.parameters = config
            self.validator.commit()
            self.want.append(copy.deepcopy(config))

        # Exit if there's nothing to do
        if len(self.want) == 0:
            self.ansible_module.exit_json(**self.results.ok_result)

    def _merge_global_and_switch_configs(self, config) -> None:
        """
        Merge the global config with each switch config and
        populate list of merged configs self.switch_configs.

        Merge rules:
        1.  switch_config takes precedence over global_config.
        2.  If switch_config is missing a parameter, use parameter
            from global_config.
        3.  If switch_config has a parameter, use it.
        """
        method_name = inspect.stack()[0][3]

        if not config.get("switches"):
            msg = f"{self.class_name}.{method_name}: "
            msg += "playbook is missing list of switches"
            self.ansible_module.fail_json(msg)

        self.switch_configs = []
        merged_configs = []
        for switch in config["switches"]:
            # we need to rebuild global_config in this loop
            # because merge_dicts modifies it in place
            global_config = copy.deepcopy(config)
            global_config.pop("switches", None)
            msg = (
                f"global_config: {json.dumps(global_config, indent=4, sort_keys=True)}"
            )
            self.log.debug(msg)

            msg = f"switch PRE_MERGE : {json.dumps(switch, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            merge_dicts = MergeDicts(self.ansible_module)
            merge_dicts.dict1 = global_config
            merge_dicts.dict2 = switch
            merge_dicts.commit()
            switch_config = merge_dicts.dict_merged

            msg = f"switch POST_MERGE: {json.dumps(switch_config, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            merged_configs.append(switch_config)
        self.switch_configs = copy.copy(merged_configs)

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
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        super().__init__(params)
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = f"ENTERED Merged.{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.need = []

        self._implemented_states.add("merged")

    def get_need(self):
        """
        Build self.need for merged state.

        ### Caller
        commit()

        ### self.need structure
        ```json
        {
            "172.22.150.2": {
                "deploy": false
                "fabric_name": "MyFabric",
                "maintenance_mode": "maintenance",
                "serial_number": "FCI1234567"
            },
            "172.22.150.3": {
                "deploy": true
                "fabric_name": "YourFabric",
                "maintenance_mode": "normal",
                "serial_number": "HMD2345678"
            }
        }
        """
        self.need = {}
        for want in self.want:
            want_ip = want.get("ip_address", None)
            if want_ip not in self.have:
                continue
            serial_number = self.have[want_ip]["serial_number"]
            fabric_name = self.have[want_ip]["fabric_name"]
            if want.get("mode") != self.have[want_ip]["maintenance_mode"]:
                self.need[want_ip] = want
                self.need[want_ip].update({"deploy": want.get("deploy")})
                self.need[want_ip].update({"fabric_name": fabric_name})
                self.need[want_ip].update({"serial_number": serial_number})
                self.need[want_ip].update({"maintenance_mode": want.get("mode")})

    def commit(self):
        """
        Commit the merged state request
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        msg = f"{self.class_name}.{method_name}: entered"
        self.log.debug(msg)

        self.rest_send = RestSend(self.ansible_module)

        self.get_want()
        self.get_have()
        self.get_need()
        self.send_need()

    def send_need(self) -> None:
        """
        Caller: commit()

        Build and send the payload to modify maintenance mode.
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
        instance.rest_send = RestSend(self.ansible_module)
        instance.results = self.results
        for ip_address, switch in self.need.items():
            mode = switch.get("maintenance_mode", None)
            serial_number = switch.get("serial_number", None)
            fabric_name = switch.get("fabric_name", None)
            deploy = switch.get("deploy", False)
            try:
                instance.deploy = deploy
                instance.fabric_name = fabric_name
                instance.ip_address = ip_address
                instance.mode = mode
                instance.serial_number = serial_number
                instance.commit()
            except ValueError as error:
                self.results.build_final_result()
                self.ansible_module.fail_json(f"{error}", **self.results.final_result)


class Query(Common):
    """
    Handle query state
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        super().__init__(ansible_module)
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED Query(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self._implemented_states.add("query")

    def commit(self) -> None:
        """
        1.  query the switches in self.want that exist on the controller
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.get_want()

        self.switch_details.rest_send = RestSend(self.ansible_module)
        self.switch_details.refresh()
        # self.config has already been validated
        for item in self.want:
            ip_address = item.get("ip_address")
            self.switch_details.filter = ip_address
            serial_number = self.switch_details.serial_number
            if serial_number is None:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Switch with ip_address {ip_address} "
                msg += "does not exist on the controller."
                self.ansible_module.fail_json(msg, **self.results.failed_result)
            mode = self.switch_details.mode
            fabric_name = self.switch_details.fabric_name
            self.results.diff_current = {
                "fabric_name": fabric_name,
                "ip_address": ip_address,
                "mode": mode,
                "serial_number": serial_number,
            }
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
    # argument_spec["deploy"] = {
    #     "default": True,
    #     "required": False,
    #     "type": "bool",
    # }
    # argument_spec["mode"] = {
    #     "choices": ["Maintenance", "Normal"],
    #     "default": "Maintenance",
    #     "required": False,
    #     "type": "str"
    # }
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
        task = Merged(ansible_module.params)
        task.ansible_module = ansible_module
        task.commit()
    elif ansible_module.params["state"] == "query":
        task = Query(ansible_module.params)
        task.ansible_module = ansible_module
        task.commit()
    else:
        # We should never get here since the state parameter has
        # already been validated.
        msg = f"Unknown state {task.ansible_module.params['state']}"
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
