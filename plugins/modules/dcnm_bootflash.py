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

        self.have consists of the controller's understanding of the current
        state of files on the switches.
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

        self.bootflash_files = BootflashFiles()
        self.bootflash_info = BootflashInfo()
        self.partition = None
        self.filepath = None
        self.filename = None
        self.ip_address = None
        self.supervisor = None

        msg = f"ENTERED {self.class_name}().{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def parse_target(self, target) -> None:
        """
        ### Summary
        Parse the target.filepath parameter into its consituent API parameters.

        ### Raises
        -   ``ValueError`` if:
            -   ``filepath`` is not set in the target dict.
            -   ``supervisor`` is not set in the target dict.

        ### Target Structure
        {
            filepath: bootflash:/myDir/foo.txt
            supervisor: active
        }

        Set the following API parameters from the above structure:

        - self.partition: bootflash:
        - self.filepath: bootflash:/myDir/
        - self.filename: foo.txt
        - self.supervisor: active

        ### Notes
        -   While this method is written to support files in directories, the
            NDFC API does not support listing files within a directory.
            Hence, we currently support only files in the root directory of
            the partition.
        -   If the file is located in the root directory of the of the
            partition, the filepath MUST NOT have a trailing slash.
            i.e. filepath == "bootflash:/" will NOT match.  It MUST
            be "bootflash:".
        -   If the file is located in a directory, the filepath MUST
            have a trailing slash.  i.e. filepath == "bootflash:/myDir"
            will NOT match since NDFC is not smart enough to add the
            slash between the filepath and filename and, using the example
            in Target Structure above, it will reconstruct the path as
            bootflash:/myDirfoo.txt which, of course, will not match
            (or worse yet, match and delete the wrong file).
        """
        method_name = inspect.stack()[0][3]

        def raise_error(msg):
            raise ValueError(f"{self.class_name}.{method_name}: {msg}")

        if target.get("filepath", None) is None:
            msg = "Expected filepath in target dict. "
            msg += f"Got {target}"
            raise_error(msg)
        if target.get("supervisor", None) is None:
            msg = "Expected supervisor in target dict. "
            msg += f"Got {target}"
            raise_error(msg)

        parts = target.get("filepath").split("/")
        self.partition = parts[0]
        # If len(parts) == 2, the file is located in the root directory of the
        # partition. In this case we DO NOT want to add a trailing slash to
        # the filepath.  i.e. filepath == "bootflash:/" will NOT match.
        self.filepath = "/".join(parts[0:-1])
        # If there's one or more directory levels in the path we DO need to
        # add a trailing slash to filepath.
        if len(parts) > 2:
            # Input: bootflash:/myDir/foo.txt
            # parts: ['bootflash:', 'myDir', 'foo.txt']
            # Result: self.filepath == bootflash:/myDir/
            self.filepath = "/".join(parts[0:-1]) + "/"
        self.filename = parts[-1]
        self.supervisor = target.get("supervisor")

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

        self.bootflash_info.filter_filename = self.filename
        self.bootflash_info.filter_filepath = self.filepath
        self.bootflash_info.filter_partition = self.partition
        self.bootflash_info.filter_supervisor = self.supervisor
        self.bootflash_info.filter_switch = self.ip_address

        msg = f"{self.class_name}.{method_name}: "
        msg += f"filename: {self.filename}, "
        msg += f"filepath: {self.filepath}, "
        msg += f"ip_address: {self.ip_address}, "
        msg += f"partition: {self.partition}, "
        msg += f"supervisor: {self.supervisor} "

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
                self.parse_target(target)
                if not self.file_exists():
                    continue
                self.bootflash_files.file_name = self.filename
                self.bootflash_files.file_path = self.filepath
                self.bootflash_files.ip_address = switch["ip_address"]
                self.bootflash_files.partition = self.partition
                self.bootflash_files.supervisor = self.supervisor
                self.bootflash_files.add_file()

        self.bootflash_files.commit()


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
