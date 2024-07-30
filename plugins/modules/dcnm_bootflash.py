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

    files:
        description:
            - List of files to be deleted or queried.
        type: list
        elements: str
        default: []
    switches:
        description:
            - List of switches containing files to be deleted or queried.
        type: list
        elements: dict
        suboptions:
            ip_address:
                description:
                    - The ip address of a switch.
                type: str
                required: true
            files:
                description:
                    - A list of files overridding the global files list.
                type: list
                elements: str
                default: []
                required: false

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
# Delete two files from two switches.

    -   name: Delete Image policies
        cisco.dcnm.dcnm_bootflash:
            state: deleted
            files:
            -   nxos64-cs.10.3.2.F.bin
            -   nxos64-cs.10.3.1.F.bin
            switches:
            -   ip_address: 192.168.1.1
            -   ip_address: 192.168.1.2
        register: result
    -   name: print result
        ansible.builtin.debug:
            var: result

# Delete two files from switch 192.168.1.1 and
# switch 192.168.1.2, and delete one file from
# switch 192.168.1.3.

    -   name: Delete Image policies
        cisco.dcnm.dcnm_bootflash:
            state: deleted
            files:
            -   nxos64-cs.10.3.2.F.bin
            -   nxos64-cs.10.3.1.F.bin
            switches:
            -   ip_address: 192.168.1.1
            -   ip_address: 192.168.1.2
            -   ip_address: 192.168.1.3
                files:
                -   nxos64-cs.10.3.1.F.bin
        register: result
    -   name: print result
        ansible.builtin.debug:
            var: result

# Query the controller for one file on switch 192.168.1.1.

    -   name: Query files
        cisco.dcnm.dcnm_bootflash:
            state: query
            files:
            -   nxos64-cs.10.3.2.F.bin
            switches:
            -   ip_address: 192.168.1.1
        register: result
    -   name: print result
        ansible.builtin.debug:
            var: result

"""

import copy
import inspect
import json
import logging

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.bootflash.bootflash_info import \
    BootflashInfo
from ansible_collections.cisco.dcnm.plugins.module_utils.bootflash.bootflash_files import \
    BootflashFiles
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

        self.check_mode = self.params.get("check_mode", None)
        if self.check_mode is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "check_mode is required."
            raise ValueError(msg)

        self._valid_states = ["deleted", "query"]
        self._states_require_config = {"deleted", "query"}

        self.state = self.params.get("state", None)
        if self.state is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "params is missing state parameter."
            raise ValueError(msg)
        if self.state not in self._valid_states:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Invalid state: {self.state}. "
            msg += f"Expected one of: {','.join(self._valid_states)}."
            raise ValueError(msg)

        self.files = self.params.get("files", None)
        if not isinstance(self.files, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "Expected list of strings for self.files. "
            msg += f"Got {type(self.files).__name__}"
            raise TypeError(msg)

        self.switches = self.params.get("switches", None)
        if not isinstance(self.switches, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "Expected list of dict for self.switches. "
            msg += f"Got {type(self.files).__name__}"
            raise TypeError(msg)

        self.results = Results()
        self.results.state = self.state
        self.results.check_mode = self.check_mode

        self._rest_send = None

        self.have = None
        self.validated = []
        self.want = []

        # files to be deleted
        self.need_delete = []
        # policies to be queried
        self.need_query = []
        self.validated_configs = []

        msg = f"ENTERED Common().{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def get_have(self) -> None:
        """
        Caller: main()

        self.have consists of the current image policies on the controller
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        self.have = BootflashInfo()
        self.have.results = self.results
        self.have.rest_send = self.rest_send  # pylint: disable=no-member
        self.have.switch_details = SwitchDetails()

    def get_want(self) -> None:
        """
        Caller: main()

        1. Validate the playbook configs
        2. Convert the validated configs to payloads
        3. Update self.want with this list of payloads
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        if self.params.get("files", None) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "params is missing files parameter."
            raise ValueError(msg)

        self.files = self.params["files"]

        if not isinstance(self.files, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "Expected list of strings for self.files. "
            msg += f"Got {type(self.files).__name__}"
            raise TypeError(msg)

        if self.params.get("switches", None) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "params is missing switches parameter."
            raise ValueError(msg)

        self.switches = self.params["switches"]

        if not isinstance(self.switches, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "Expected list of dict for self.switches. "
            msg += f"Got {type(self.files).__name__}"
            raise TypeError(msg)

        for switch in self.switches:
            if switch.get("ip_address", None) is None:
                msg = f"{self.class_name}.{method_name}: "
                msg += "Expected ip_address in switch dict. "
                msg += f"Got {switch}"
                raise ValueError(msg)

            if switch.get("files", None) is None:
                switch["files"] = self.files
            if not isinstance(switch["files"], list):
                msg = f"{self.class_name}.{method_name}: "
                msg += "Expected list of strings for switch['files']. "
                msg += f"Got {type(switch['files']).__name__}"
                raise TypeError(msg)
            self.want.append(switch)


class Deleted(Common):
    """
    Handle deleted state
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

        self.instance = BootflashFiles()

        msg = f"ENTERED {self.class_name}().{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def commit(self) -> None:
        """
        Delete the specified files from the bootflash of the specified switches.
        """
        self.get_want()

        self.results.state = self.state
        self.results.check_mode = self.check_mode
        self.instance.results = self.results
        self.instance.rest_send = self.rest_send
        self.instance.switch_details = SwitchDetails()
        self.instance.switch_details.results = Results()
        self.instance.switch_details.rest_send = self.rest_send

        for switch in self.switches:
            self.instance.ip_address = switch["ip_address"]
            for file in switch["files"]:
                self.instance.bootflash_type = "active"
                self.instance.file_name = file
                self.instance.file_path = "bootflash:"
                self.instance.partition = "bootflash:"
                self.instance.add_file()

        # self.instance.ip_address = "172.22.150.113"
        # self.instance.file_name = "oz_201.cfg"
        # self.instance.file_path = "bootflash:"
        # self.instance.partition = "bootflash:"
        self.instance.commit()

class Query(Common):
    """
    Handle query state
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
        1.  query the bootflash on switches in self.want
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.results.state = self.state
        self.results.check_mode = self.check_mode

        self.get_want()
        self.get_have()

        if len(self.switches) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "No switches to query."
            return

        switches_to_query = []
        for switch in self.switches:
            switches_to_query.append(switch["ip_address"])
        self.have.switches = switches_to_query
        self.have.refresh()

        for switch in self.switches:
            self.have.filter_switch = switch["ip_address"]
            for file in switch["files"]:
                self.have.filter_file = file
                self.have.build_matches()
                self.results.register_task_result()


def main():
    """
    main entry point for module execution
    """

    argument_spec = {
        "files": {
            "required": False,
            "type": "list",
            "elements": "str",
            "default": [],
        },
        "switches": {
            "required": False,
            "type": "list",
            "elements": "dict",
            "default": [],
        },
        "state": {
            "default": "merged",
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
    except ValueError as error:
        ansible_module.fail_json(f"{error}", **task.results.failed_result)

    task.results.build_final_result()

    if True in task.results.failed:  # pylint: disable=unsupported-membership-test
        msg = "Module failed."
        ansible_module.fail_json(msg, **task.results.final_result)
    ansible_module.exit_json(**task.results.final_result)


if __name__ == "__main__":
    main()
