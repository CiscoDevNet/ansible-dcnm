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

"""

EXAMPLES = """

# Query vrfs in fabric f1.
- name: Query vrfs in fabric f1
  cisco.dcnm.dcnm_fabrics_vrfs:
    state: query
    config:
        fabric_name: f1
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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.endpoint_parsers.ep_v1_lanfabric_rest_topdown_fabrics_vrfs import \
    FabricsVrfsByName, FabricsVrfsByKeyValue
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

        self.fabrics_vrfs_info = FabricsVrfsByName()
        self.fabrics_vrfs_info_nv = FabricsVrfsByKeyValue()

        msg = "ENTERED Query(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def get_have_nv(self):
        """
        ### Summary
        Build self.have, a dict containing the VRF info.

        ### Raises
        -   ``ValueError`` if FabricsVrfsByKeyValue() raises ``ValueError``
        ```
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        try:
            self.fabrics_vrfs_info_nv.rest_send = self.rest_send
            self.fabrics_vrfs_info_nv.results = self.results
            self.fabrics_vrfs_info_nv.fabric_name = self.config["fabric_name"]
            self.fabrics_vrfs_info_nv.vrf_name = self.config["vrf_name"]
            self.fabrics_vrfs_info_nv.filter_key = "vrfId"
            self.fabrics_vrfs_info_nv.filter_value = 63031
            self.fabrics_vrfs_info_nv.refresh()
            self.log.debug(f"default_sg_tag: {self.fabrics_vrfs_info_nv.default_sg_tag}")
            self.log.debug(f"enforce: {self.fabrics_vrfs_info_nv.enforce}")
            self.log.debug(f"fabric: {self.fabrics_vrfs_info_nv.fabric}")
            self.log.debug(f"hierarchical_key: {self.fabrics_vrfs_info_nv.hierarchical_key}")
            self.log.debug(f"item_id: {self.fabrics_vrfs_info_nv.item_id}")
            self.log.debug(f"service_vrf_template: {self.fabrics_vrfs_info_nv.service_vrf_template}")
            self.log.debug(f"source: {self.fabrics_vrfs_info_nv.source}")
            self.log.debug(f"tenant_name: {self.fabrics_vrfs_info_nv.tenant_name}")
            self.log.debug(f"vrf_id: {self.fabrics_vrfs_info_nv.vrf_id}")
            self.log.debug(f"vrf_name: {self.fabrics_vrfs_info_nv.vrf_name}")
            self.log.debug(f"vrf_status: {self.fabrics_vrfs_info_nv.vrf_status}")
            self.log.debug(f"vrf_extension_template: {self.fabrics_vrfs_info_nv.vrf_extension_template}")
            self.log.debug(f"vrf_template_config: {self.fabrics_vrfs_info_nv.vrf_template_config}")
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error while retrieving VRF info. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error
        self.have = self.fabrics_vrfs_info_nv.filtered_data

    def get_have(self):
        """
        ### Summary
        Build self.have, a dict containing the current mode of all switches.

        ### Raises
        -   ``ValueError`` if FabricsVrfsInfo() raises ``ValueError``
        ```
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        try:
            self.fabrics_vrfs_info.rest_send = self.rest_send
            self.fabrics_vrfs_info.results = self.results
            self.fabrics_vrfs_info.fabric_name = self.config["fabric_name"]
            self.fabrics_vrfs_info.refresh()
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error while retrieving switch info. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error
        self.have = self.fabrics_vrfs_info.all_data

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
            self.get_have_nv()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error while retrieving switch information "
            msg += "from the controller. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        # If we got this far, the requests were successful.
        self.results.action = "fabrics_vrfs_info"
        self.results.changed = False
        self.results.diff_current = self.have
        self.results.failed = False
        self.results.response_current = {"MESSAGE": "FabricsVrfInfo OK."}
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
    sender.ansible_module = ansible_module
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
