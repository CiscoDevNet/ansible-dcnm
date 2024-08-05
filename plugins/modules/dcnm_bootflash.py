#!/usr/bin/python
#
# Copyright (c) 2024 Cisco and/or its affiliates.
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
# pylint: disable=wrong-import-position
from __future__ import absolute_import, division, print_function

__metaclass__ = type
__author__ = "Allen Robel"

DOCUMENTATION = """
---
module: dcnm_bootflash
short_description: Bootflash management for Nexus switches.
version_added: "3.5.0"
description:
    - Delete, query bootflash files.
author: Allen Robel (@quantumonion)
options:
    state:
        description:
            - The state of the feature or object after module completion
        type: str
        choices:
            - deleted
            - query
        default: query
    config:
        description:
            - Configuration parameters for the module.
        type: dict
        required: true
        suboptions:
            targets:
                description:
                    - List of dictionaries containing options for files to be deleted or queried.
                type: list
                elements: dict
                default: []
                required: false
                suboptions:
                    filepath:
                        description:
                            - The path to the file to be deleted or queried.
                        type: str
                        required: true
                    supervisor:
                        description:
                            - Either active or standby. The supervisor containing the filepath.
                        type: str
                        required: false
                        choices:
                            - active
                            - standby
                        default: active
            switches:
                description:
                    - List of dictionaries containing switches on which query or delete operations are executed.
                type: list
                elements: dict
                suboptions:
                    ip_address:
                        description:
                            - The ip address of a switch.
                        type: str
                        required: true
                    targets:
                        description:
                            - List of dictionaries containing options for files to be deleted or queried.
                        type: list
                        elements: dict
                        default: []
                        required: false
                        suboptions:
                            filepath:
                                description:
                                    - The path to the file to be deleted or queried.  Only files in the root directory of the partition are currently supported.
                                type: str
                                required: true
                            supervisor:
                                description:
                                    - Either active or standby. The supervisor containing the filepath.
                                type: str
                                required: false
                                choices:
                                    - active
                                    - standby
                                default: active

"""

EXAMPLES = """
# This module supports the following states:
#
# deleted:
#   Delete files from the bootflash of one or more switches.
#
#   If an image is in use by a device, the module will fail.  Use
#   dcnm_image_upgrade module, state deleted, to detach image policies
#   containing images to be deleted.
#
# query:
#
#   Return information for one or more files.
#
# Delete two files from each of three switches.

- name: Delete two files from each of two switches
  cisco.dcnm.dcnm_bootflash:
    state: deleted
    config:
      targets:
        - filepath: bootflash:/foo.txt
          supervisor: active
        - filepath: bootflash:/bar.txt
          supervisor: standby
      switches:
        - ip_address: 192.168.1.1
        - ip_address: 192.168.1.2
        - ip_address: 192.168.1.3

# Delete two files from switch 192.168.1.1 and switch 192.168.1.2:
#   - foo.txt on the active supervisor's bootflash: device.
#   - bar.txt on the standby supervisor's bootflash: device.
# Delete one file from switch 192.168.1.3:
#   - baz.txt on the standby supervisor's bootflash: device.

- name: Delete files
  cisco.dcnm.dcnm_bootflash:
    state: deleted
    config:
      targets:
        - filepath: bootflash:/foo.txt
          supervisor: active
        - filepath: bootflash:/bar.txt
          supervisor: standby
      switches:
        - ip_address: 192.168.1.1
        - ip_address: 192.168.1.2
        - ip_address: 192.168.1.3
          targets:
            - filepath: bootflash:/baz.txt
              supervisor: standby
  register: result
- name: print result
  ansible.builtin.debug:
    var: result

# Query the controller for information about one file on three switches.
# Since the default for supervisor is "active", the module will query the
# active supervisor's bootflash: device.

- name: Query file on three switches
  cisco.dcnm.dcnm_bootflash:
    state: query
    config:
      targets:
        - filepath: bootflash:/foo.txt
    switches:
      - ip_address: 192.168.1.1
      - ip_address: 192.168.1.2
      - ip_address: 192.168.1.3
  register: result
- name: print result
  ansible.builtin.debug:
    var: result

"""

import copy
import inspect
import json
import logging

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.bootflash.bootflash_files import \
    BootflashFiles
from ansible_collections.cisco.dcnm.plugins.module_utils.bootflash.bootflash_info import \
    BootflashInfo
from ansible_collections.cisco.dcnm.plugins.module_utils.bootflash.parse_target import \
    ParseTarget
from ansible_collections.cisco.dcnm.plugins.module_utils.common.log_v2 import \
    Log
from ansible_collections.cisco.dcnm.plugins.module_utils.common.properties import \
    Properties
from ansible_collections.cisco.dcnm.plugins.module_utils.common.response_handler import \
    ResponseHandler
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_dcnm import \
    Sender
from ansible_collections.cisco.dcnm.plugins.module_utils.common.switch_details import \
    SwitchDetails


def json_pretty(msg):
    """
    Return a pretty-printed JSON string for logging messages
    """
    return json.dumps(msg, indent=4, sort_keys=True)


@Properties.add_rest_send
class Common:
    """
    Common methods for all states
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.params = params

        def raise_error(msg):
            raise ValueError(f"{self.class_name}.{method_name}: {msg}")

        self.check_mode = self.params.get("check_mode", None)
        if self.check_mode is None:
            msg = "check_mode is required."
            raise_error(msg)

        self._valid_states = ["deleted", "query"]
        self._states_require_config = {"deleted", "query"}

        self.state = self.params.get("state", None)
        if self.state is None:
            msg = "params is missing state parameter."
            raise_error(msg)
        if self.state not in self._valid_states:
            msg = f"Invalid state: {self.state}. "
            msg += f"Expected one of: {','.join(self._valid_states)}."
            raise_error(msg)

        self.config = self.params.get("config", None)
        if not isinstance(self.config, dict):
            msg = "Expected dict for config. "
            msg += f"Got {type(self.config).__name__}"
            raise_error(msg)

        self.targets = self.config.get("targets", [])
        if not isinstance(self.targets, list):
            msg = "Expected list of dict for self.targets. "
            msg += f"Got {type(self.targets).__name__}"
            raise_error(msg)

        self.switches = self.config.get("switches", [])
        if not isinstance(self.switches, list):
            msg = "Expected list of dict for self.switches. "
            msg += f"Got {type(self.switches).__name__}"
            raise_error(msg)

        self._rest_send = None

        self.bootflash_info = BootflashInfo()
        self.ip_address = None
        self.parse_target = ParseTarget()
        self.results = Results()
        self.results.state = self.state
        self.results.check_mode = self.check_mode
        self.want = []

        msg = f"ENTERED Common().{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def get_want(self) -> None:
        """
        ### Summary
        1.  Validate the playbook configs
        2.  Convert the validated configs to the structure required by the
            the Delete() and Query() classes.
        3.  Update self.want with this list of payloads

        If a switch in the switches list does not have a targets key, add the
        targets key with the value of the global targets list from the
        playbook.  Else, use the switch's targets info (i.e. the switch's
        targets info overrides the global targets info).

        ### Raises
        -   ValueError if:
            -   ``ip_address`` is missing from a switch dict.
            -   ``filepath`` is missing from a target dict.
        -   TypeError if:
            -   The value of ``targets`` is not a list of dictionaries.

        ### ``want`` Structure
        -   A list of dictionaries.  Each dictionary contains the following keys:
            -   ip_address: The ip address of the switch.
            -   targets: A list of dictionaries.  Each dictionary contains the
                following keys:
                -   filepath: The path to the file to be deleted or queried.
                -   supervisor: The supervisor containing the filepath.

        ### Example ``want`` Structure
        ```json
        [
            {
                "ip_address": "192.168.1.1",
                "targets": [
                    {
                        "filepath": "bootflash:/foo.txt",
                        "supervisor": "active"
                    },
                    {
                        "filepath": "bootflash:/bar.txt",
                        "supervisor": "standby"
                    }
                ]
            }
        ]
        ```

        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        def raise_value_error(msg):
            raise ValueError(f"{self.class_name}.{method_name}: {msg}")

        def raise_type_error(msg):
            raise TypeError(f"{self.class_name}.{method_name}: {msg}")

        for switch in self.switches:
            if switch.get("ip_address", None) is None:
                msg = "Expected ip_address in switch dict. "
                msg += f"Got {switch}"
                raise_value_error(msg)

            if switch.get("targets", None) is None:
                switch["targets"] = self.targets
            if not isinstance(switch["targets"], list):
                msg = "Expected list of dictionaries for switch['targets']. "
                msg += f"Got {type(switch['targets']).__name__}"
                raise_type_error(msg)

            for target in switch["targets"]:
                if target.get("filepath", None) is None:
                    msg = "Expected filepath in target dict. "
                    msg += f"Got {target}"
                    raise_value_error(msg)
                if target.get("supervisor", None) is None:
                    target["supervisor"] = "active"
            self.want.append(switch)


class Deleted(Common):
    """
    ### Summary
    Handle deleted state

    ### Raises
    -   ValueError if:
        -   ``Common.__init__()`` raises TypeError or ValueError.
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]
        try:
            super().__init__(params)
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error during super().__init__(). "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        self.bootflash_files = BootflashFiles()

        msg = f"ENTERED {self.class_name}().{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def file_exists(self) -> bool:
        """
        ### Summary
        -   Return True if the file exists on the switch.
        -   Return False otherwise.

        ### Raises
        None

        ### Notes
        -   We currently support only files in the root directory of the
            partition.  This is because the NDFC API does not support
            listing files within a directory.
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        self.bootflash_info.filter_filename = self.parse_target.filename
        self.bootflash_info.filter_filepath = self.parse_target.filepath
        self.bootflash_info.filter_partition = self.parse_target.partition
        self.bootflash_info.filter_supervisor = self.parse_target.supervisor
        self.bootflash_info.filter_switch = self.ip_address

        msg = f"{self.class_name}.{method_name}: "
        msg += f"filename: {self.parse_target.filename}, "
        msg += f"filepath: {self.parse_target.filepath}, "
        msg += f"ip_address: {self.ip_address}, "
        msg += f"partition: {self.parse_target.partition}, "
        msg += f"supervisor: {self.parse_target.supervisor} "

        if self.bootflash_info.filename is None:
            msg += "not found in bootflash_info."
            self.log.debug(msg)
            return False
        msg += "found in bootflash_info."
        self.log.debug(msg)
        return True

    def commit(self) -> None:
        """
        ### Summary
        Delete the specified files if they exist.

        ### Raises
        None.  While this method does not directly raise exceptions, it
        calls other methods that may raise the following exceptions:

        -   ControllerResponseError
        -   TypeError
        -   ValueError
        """
        self.get_want()
        self.bootflash_info.results = Results()
        self.bootflash_info.rest_send = self.rest_send  # pylint: disable=no-member
        self.bootflash_info.switch_details = SwitchDetails()

        switch_list = []
        for switch in self.switches:
            switch_list.append(switch["ip_address"])
        self.bootflash_info.switches = switch_list
        self.bootflash_info.refresh()

        self.results.state = self.state
        self.results.check_mode = self.check_mode
        self.bootflash_files.results = self.results
        self.bootflash_files.rest_send = self.rest_send
        self.bootflash_files.switch_details = SwitchDetails()
        self.bootflash_files.switch_details.results = Results()

        for switch in self.switches:
            self.ip_address = switch["ip_address"]
            for target in switch["targets"]:
                self.parse_target.target = target
                self.parse_target.commit()
                if not self.file_exists():
                    continue
                self.bootflash_files.file_name = self.parse_target.filename
                self.bootflash_files.file_path = self.parse_target.filepath
                self.bootflash_files.ip_address = switch["ip_address"]
                self.bootflash_files.partition = self.parse_target.partition
                self.bootflash_files.supervisor = self.parse_target.supervisor
                self.bootflash_files.add_file()

        self.bootflash_files.commit()


class Query(Common):
    """
    ### Summary
    Handle query state.

    ### Raises
    -   ValueError if:
        -   ``Common.__init__()`` raises TypeError or ValueError.
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]

        try:
            super().__init__(params)
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error during super().__init__(). "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        msg = f"ENTERED {self.class_name}().{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def commit(self) -> None:
        """
        ### Summary
        query the bootflash on all switches in self.switches
        and register the results.

        ### Raises
        None.  While this method does not directly raise exceptions, it
        calls other methods that may raise the following exceptions:

        -   ControllerResponseError
        -   TypeError
        -   ValueError

        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.results.state = self.state
        self.results.check_mode = self.check_mode

        self.get_want()

        if len(self.switches) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "No switches to query."
            return

        self.bootflash_info.results = self.results
        self.bootflash_info.rest_send = self.rest_send
        self.bootflash_info.switch_details = SwitchDetails()

        switches_to_query = []
        for switch in self.switches:
            switches_to_query.append(switch["ip_address"])
        self.bootflash_info.switches = switches_to_query
        self.bootflash_info.refresh()
        self.results.response_current = self.bootflash_info.response_dict
        self.results.result_current = self.bootflash_info.result_dict

        result_current = {}
        response_current = {}
        diff_current = {}
        for switch in self.switches:
            self.bootflash_info.filter_switch = switch["ip_address"]
            if switch["ip_address"] not in result_current:
                result_current[switch["ip_address"]] = []
            if switch["ip_address"] not in response_current:
                response_current[switch["ip_address"]] = []
            if switch["ip_address"] not in diff_current:
                diff_current[switch["ip_address"]] = []
            for target in switch["targets"]:
                self.parse_target.target = target
                self.parse_target.commit()
                self.bootflash_info.filter_filename = self.parse_target.filename
                self.bootflash_info.filter_filepath = self.parse_target.filepath
                self.bootflash_info.filter_partition = self.parse_target.partition
                self.bootflash_info.filter_supervisor = self.parse_target.supervisor
                self.bootflash_info.build_match()
                diff_current[switch["ip_address"]].append(self.bootflash_info.match)

            result_current[switch["ip_address"]] = self.bootflash_info.result_dict
            response_current[switch["ip_address"]] = self.bootflash_info.response_dict

        self.results.diff_current = diff_current
        self.results.register_task_result()


def main():
    """
    main entry point for module execution
    """

    argument_spec = {
        "config": {
            "required": True,
            "type": "dict",
        },
        "state": {
            "default": "query",
            "choices": ["deleted", "query"],
        },
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

    # pylint: disable=attribute-defined-outside-init
    try:
        task = None
        if params["state"] == "deleted":
            task = Deleted(params)
        if params["state"] == "query":
            task = Query(params)
        if task is None:
            ansible_module.fail_json(f"Invalid state: {params['state']}")
        task.rest_send = rest_send
        task.commit()
    except (TypeError, ValueError) as error:
        ansible_module.fail_json(f"{error}", **task.results.failed_result)

    task.results.build_final_result()

    if True in task.results.failed:  # pylint: disable=unsupported-membership-test
        msg = "Module failed."
        ansible_module.fail_json(msg, **task.results.final_result)
    ansible_module.exit_json(**task.results.final_result)


if __name__ == "__main__":
    main()
