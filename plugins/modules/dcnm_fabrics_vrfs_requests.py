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
module: dcnm_fabrics_vrfs
short_description: Query Fabrics VRFs of NX-OS Switches.
version_added: "3.5.0"
author: Allen Robel (@quantumonion)
description:
- Query VRFs within a fabric.
options:
    state:
        choices:
        - query
        default: query
        description:
        - The state of the feature or object after module completion
        type: str
    config:
        description:
        - A dictionary containing the query parameters.
        type: dict
        required: true
        suboptions:
            fabric_name:
                description:
                - The name of the fabric to query.
                required: true
                type: str
            vrf_name:
                description:
                - The the vrf to query.
                required: false
                default: null
                type: str

"""

EXAMPLES = """

# Query all vrfs in fabric_name f1.
- name: Query vrfs in fabric f1
  cisco.dcnm.dcnm_fabrics_vrfs:
    state: query
    config:
        fabric_name: f1
  register: result
- debug:
    var: result

# Query vrf v1 in fabric f1.
- name: Query vrf_name v1 in fabric_name f1
  cisco.dcnm.dcnm_fabrics_vrfs:
    state: query
    config:
        fabric_name: f1
        vrf_name: v1
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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.log_v2 import \
    Log
from ansible_collections.cisco.dcnm.plugins.module_utils.common.epp.v1.lan_fabric.rest.top_down.fabrics.epp_vrfs import \
    EppFabricsVrfsByName
from ansible_collections.cisco.dcnm.plugins.module_utils.common.properties import \
    Properties
from ansible_collections.cisco.dcnm.plugins.module_utils.common.response_handler import \
    ResponseHandler
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_requests import \
    Sender


def json_pretty(msg):
    """
    Return a pretty-printed JSON string for logging messages
    """
    return json.dumps(msg, indent=4, sort_keys=True)


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
        self.want = self.config


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

        msg = "ENTERED Query(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def get_have(self):
        """
        ### Summary
        Build self.have, a dict containing the current mode of all switches.

        ### Raises
        -   ``ValueError`` if EppFabricsVrfsByName() raises ``ValueError``
        ```
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.get_vrf_info = EppFabricsVrfsByName()
        try:
            self.get_vrf_info.rest_send = self.rest_send
            self.get_vrf_info.results = self.results
            self.get_vrf_info.fabric_name = self.config["fabric_name"]
            vrf_name = self.config.get("vrf_name")
            if vrf_name is not None:
                self.get_vrf_info.filter = self.config.get("vrf_name")
            self.get_vrf_info.refresh()
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error while retrieving switch info. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error
        if vrf_name is not None:
            self.have = self.get_vrf_info.filtered_data
        else:
            self.have = self.get_vrf_info.all_data

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
            msg += "Error while retrieving fabric vrf information "
            msg += "from the controller. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        # If we got this far, the request was successful, or the
        # fabric does not exist.
        # If the fabric does not exist, self.have will be empty.
        # If the user has set vrf_name, and vrf_name does not exist,
        # self.have will be None.
        self.results.action = "fabrics_vrfs_info"
        self.results.changed = False
        if self.have is None:
            self.results.diff_current = {}
        else:
            self.results.diff_current = self.have
        self.results.failed = False
        self.results.response_current = self.get_vrf_info.rest_send.response_current
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
        "choices": ["query"],
        "default": "query",
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
    sender.login()
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    if params["state"] == "query":
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
