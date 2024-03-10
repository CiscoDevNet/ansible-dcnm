#!/usr/bin/python
#
# Copyright (c) 2020-2022 Cisco and/or its affiliates.
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
module: dcnm_fabric_vxlan
short_description: Create VXLAN/EVPN Fabrics.
version_added: "0.9.0"
description:
    - "Create VXLAN/EVPN Fabrics."
author: Allen Robel
options:
  state:
    description:
    - The state of DCNM after module completion.
    - I(merged) and I(query) are the only states supported.
    type: str
    choices:
      - merged
      - query
    default: merged
  config:
    description:
    - A dictionary of fabric configurations
    type: list
    elements: dict
    suboptions:
      aaa_remote_ip_enabled:
        description:
        - Enable (True) or disable (False) AAA remote IP
        - NDFC GUI label, Enable AAA IP Authorization
        - NDFC GUI tab, Advanced
        type: bool
        required: false
        default: False
      advertise_pip_bgp:
        description:
        - Enable (True) or disable (False) usage of Primary VTEP IP Advertisement As Next-Hop Of Prefix Routes
        - NDFC GUI label, vPC advertise-pip
        - NDFC GUI tab, VPC
        type: bool
        required: false
        default: False
      anycast_bgw_advertise_pip:
        description:
        - Enable (True) or disable (False) advertising Anycast Border Gateway PIP as VTEP.
        - Effective after Recalculate Config on parent MSD fabric.
        - NDFC GUI label, Anycast Border Gateway advertise-pip
        - NDFC GUI tab, Advanced
        type: bool
        required: false
        default: False
      anycast_gw_mac:
        description:
        - Shared MAC address for all leafs (xx:xx:xx:xx:xx:xx, xxxx.xxxx.xxxx, etc)
        - NDFC GUI label, Anycast Gateway MAC
        - NDFC GUI tab, General Parameters
        type: str
        required: false
        default: "2020.0000.00aa"
      anycast_lb_id:
        description:
        - Underlay Anycast Loopback Id
        - NDFC GUI label, Underlay Anycast Loopback Id
        - NDFC GUI tab, Protocols
        type: int
        required: false
        default: ""
      anycast_rp_ip_range:
        description:
        - Anycast or Phantom RP IP Address Range
        - NDFC GUI label, Underlay RP Loopback IP Range
        - NDFC GUI tab, Resources
        type: str
        required: false
        default: 10.254.254.0/24
      auto_symmetric_default_vrf:
        description:
        - Enable (True) or disable (False) auto generation of Default VRF interface and BGP peering configuration on managed neighbor devices.
        - If True, auto created VRF Lite IFC links will have 'Auto Deploy Default VRF for Peer' enabled.
        - vrf_lite_autoconfig must be set to 1
        - auto_symmetric_vrf_lite must be set to True
        - auto_vrflite_ifc_default_vrf must be set to True
        - NDFC GUI label: Auto Deploy Default VRF for Peer
        - NDFC GUI tab: Resources
        type: bool
        required: false
        default: False
      auto_symmetric_vrf_lite:
        description:
        - Enable (True) or disable (False) auto generation of Whether to auto generate VRF LITE sub-interface and BGP peering configuration on managed neighbor devices.
        - If True, auto created VRF Lite IFC links will have 'Auto Deploy for Peer' enabled.
        - NDFC GUI label, Auto Deploy for Peer
        - NDFC GUI tab, Resources
        - vrf_lite_autoconfig must be set to 1
        type: bool
        required: false
        default: False
      auto_vrflite_ifc_default_vrf:
        description:
        - Enable (True) or disable (False) auto generation of Default VRF interface and BGP peering configuration on VRF LITE IFC auto deployment.
        - If True, auto created VRF Lite IFC links will have 'Auto Deploy Default VRF' enabled.
        - NDFC GUI label, Auto Deploy Default VRF
        - NDFC GUI tab, Resources
        - vrf_lite_autoconfig must be set to 1
        type: bool
        required: false
        default: False
      bgp_as:
        description:
        - The fabric BGP Autonomous System number
        - NDFC GUI label, BGP ASN
        - NDFC GUI tab, General Parameters
        type: str
        required: true
      default_vrf_redis_bgp_rmap:
        description:
        - Route Map used to redistribute BGP routes to IGP in default vrf in auto created VRF Lite IFC links
        - NDFC GUI label, Redistribute BGP Route-map Name
        - NDFC GUI tab, Resources
        type: str
        required: false, unless auto_vrflite_ifc_default_vrf is set to True
      fabric_name:
        description:
        - The name of the fabric
        type: str
        required: true
      pm_enable:
        description:
        - Enable (True) or disable (False) fabric performance monitoring
        - NDFC GUI label, Enable Performance Monitoring
        - NDFC GUI tab, General Parameters
        type: bool
        required: false
        default: False
      replication_mode:
        description:
        - Replication Mode for BUM Traffic
        - NDFC GUI label, Replication Mode
        - NDFC GUI tab, Replication
        type: str
        required: False
        choices:
        - Ingress
        - Multicast
        default: Multicast
      vrf_lite_autoconfig:
        description:
        - VRF Lite Inter-Fabric Connection Deployment Options.
        - If (0), VRF Lite configuration is Manual.
        - If (1), VRF Lite IFCs are auto created between border devices of two Easy Fabrics
        - If (1), VRF Lite IFCs are auto created between border devices in Easy Fabric and edge routers in External Fabric.
        - The IP address is taken from the 'VRF Lite Subnet IP Range' pool.
        - NDFC GUI label, VRF Lite Deployment
        - NDFC GUI tab, Resources
        type: int
        required: false
        default: 0
        choices:
        - 0
        - 1

"""

EXAMPLES = """
# This module supports the following states:
#
# Merged:
#   Fabric defined in the playbook will be created.
#
# Query:
#   Returns the current DCNM state for the fabric.


# The following will create fabric my-fabric
- name: Create fabric
  cisco.dcnm.dcnm_fabric_vxlan:
    state: merged
    config:
    -   fabric_name: my-fabric
        bgp_as: 100

"""

import copy
import inspect
import json
import logging
from typing import Any, Dict, List

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.common.log import Log
from ansible_collections.cisco.dcnm.plugins.module_utils.common.merge_dicts import \
    MergeDicts
from ansible_collections.cisco.dcnm.plugins.module_utils.common.params_merge_defaults import \
    ParamsMergeDefaults
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.vxlan.params_spec import \
    ParamsSpec
from ansible_collections.cisco.dcnm.plugins.module_utils.common.params_validate import \
    ParamsValidate
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.common import \
    FabricCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details import \
    FabricDetailsByName
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.query import \
    FabricQuery
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_fabric import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.endpoints import (
    ApiEndpoints
)
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.vxlan.verify_fabric_params import (
    VerifyFabricParams,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.create import (
    FabricCreateBulk
)
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.delete import (
    FabricDelete
)
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_task_result import (
    FabricTaskResult
)

def json_pretty(msg):
    """
    Return a pretty-printed JSON string for logging messages
    """
    return json.dumps(msg, indent=4, sort_keys=True)

class FabricVxlanTask(FabricCommon):
    """
    Ansible support for Data Center VXLAN EVPN
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        super().__init__(ansible_module)
        method_name = inspect.stack()[0][3]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED FabricVxlanTask(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.endpoints = ApiEndpoints()

        self._implemented_states = set()
        self._implemented_states.add("merged")

        self.params = ansible_module.params
        self.verify = VerifyFabricParams()
        self.rest_send = RestSend(self.ansible_module)
        # populated in self.validate_input()
        self.payloads = {}

        self.config = ansible_module.params.get("config")
        if not isinstance(self.config, list):
            msg = "expected list type for self.config. "
            msg = f"got {type(self.config).__name__}"
            self.ansible_module.fail_json(msg=msg)

        self.check_mode = False
        self.validated = []
        self.have = {}
        self.want = []
        self.need = []
        self.query = []

        self.task_result = FabricTaskResult(self.ansible_module)


    def get_have(self):
        """
        Caller: main()

        Build self.have, which is a dict containing the current controller
        fabrics and their details.

        Have is a dict, keyed on fabric_name, where each element is a dict
        with the following structure:

        {
            "fabric_name": "fabric_name",
            "fabric_config": {
                "fabricName": "fabric_name",
                "fabricType": "VXLAN EVPN",
                etc...
            }
        }
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += "entered"
        self.log.debug(msg)
        self.have = FabricDetailsByName(self.ansible_module)
        msg = "Calling self.have.refresh (FabricDetailsByName.refresh)"
        self.log.debug(msg)
        self.have.refresh()
        msg = "Calling self.have.refresh (FabricDetailsByName.refresh) "
        msg = f"DONE. self.have: {json.dumps(self.have.all_data, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def get_want(self) -> None:
        """
        Caller: main()

        1. Validate the playbook configs
        2. Update self.want with the playbook configs
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED"
        self.log.debug(msg)

        # Generate the params_spec used to validate the configs
        params_spec = ParamsSpec(self.ansible_module)
        params_spec.commit()

        # If a parameter is missing from the config, and it has a default
        # value, add it to the config.
        merged_configs = []
        merge_defaults = ParamsMergeDefaults(self.ansible_module)
        merge_defaults.params_spec = params_spec.params_spec
        for config in self.config:
            merge_defaults.parameters = config
            merge_defaults.commit()
            merged_configs.append(merge_defaults.merged_parameters)

        # validate the merged configs
        self.want = []
        validator = ParamsValidate(self.ansible_module)
        validator.params_spec = params_spec.params_spec
        for config in merged_configs:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"config: {json.dumps(config, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            validator.parameters = config
            validator.commit()
            self.want.append(copy.deepcopy(validator.parameters))

        # Exit if there's nothing to do
        if len(self.want) == 0:
            self.ansible_module.exit_json(**self.task_result.module_result)

    def get_need_for_merged_state(self):
        """
        Caller: handle_merged_state()

        Build self.need for state merged
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += "self.have.all_data: "
        msg += f"{json.dumps(self.have.all_data, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        need: List[Dict[str, Any]] = []
        state = self.params["state"]
        self.payloads = {}
        for want in self.want:
            self.verify.state = state
            self.verify.config = want
            self.verify.validate_config()
            if self.verify.result is False:
                self.ansible_module.fail_json(msg=self.verify.msg)
            need.append(self.verify.payload)
        self.need = copy.deepcopy(need)

        msg = f"{self.class_name}.validate_input(): "
        msg += f"self.need: {json.dumps(self.need, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def handle_merged_state(self):
        """
        Caller: main()

        Handle the merged state
        """
        method_name = inspect.stack()[0][3]
        self.log.debug(f"{self.class_name}.{method_name}: entered")

        self.get_need_for_merged_state()
        if self.ansible_module.check_mode:
            self.task_result["changed"] = False
            self.task_result["success"] = True
            self.task_result["diff"] = []
            self.ansible_module.exit_json(**self.task_result.module_result)
        self.send_need()

    def handle_query_state(self) -> None:
        """
        1.  query the fabrics in self.want that exist on the controller
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += "entered"
        self.log.debug(msg)
        instance = FabricQuery(self.ansible_module)
        fabric_names_to_query = []
        for want in self.want:
            fabric_names_to_query.append(want["fabric_name"])
        instance.fabric_names = fabric_names_to_query
        msg = f"{self.class_name}.{method_name}: "
        msg += "Calling FabricQuery.commit"
        self.log.debug(msg)
        instance.commit()
        self.update_diff_and_response(instance)

    def handle_deleted_state(self) -> None:
        """
        delete the fabrics in self.want that exist on the controller
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += "entered"
        self.log.debug(msg)
        instance = FabricDelete(self.ansible_module)
        fabric_names_to_delete = []
        for want in self.want:
            fabric_names_to_delete.append(want["fabric_name"])
        instance.fabric_names = fabric_names_to_delete
        msg = f"{self.class_name}.{method_name}: "
        msg += "Calling FabricDelete.commit"
        self.log.debug(msg)
        instance.commit()
        self.update_diff_and_response(instance)

    def send_need(self):
        """
        Caller: handle_merged_state()
        """
        if self.check_mode is True:
            self.send_need_check_mode()
        else:
            self.send_need_normal_mode()

    def send_need_check_mode(self):
        """
        Caller: send_need()

        Simulate sending the payload to the controller
        to create the fabrics specified in the playbook.
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += f"need: {json.dumps(self.need, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        if len(self.need) == 0:
            self.ansible_module.exit_json(**self.task_result.module_result)
        for item in self.need:
            fabric_name = item.get("FABRIC_NAME")
            if fabric_name is None:
                msg = f"{self.class_name}.{method_name}: "
                msg += "fabric_name is required."
                self.ansible_module.fail_json(msg)
            self.endpoints.fabric_name = fabric_name
            self.endpoints.template_name = "Easy_Fabric"

            try:
                endpoint = self.endpoints.fabric_create
            except ValueError as error:
                self.ansible_module.fail_json(error)

            path = endpoint["path"]
            verb = endpoint["verb"]
            payload = item
            msg = f"{self.class_name}.{method_name}: "
            msg += f"verb: {verb}, path: {path}"
            self.log.debug(msg)

            msg = f"{self.class_name}.{method_name}: "
            msg += f"fabric_name: {fabric_name}, "
            msg += f"payload: {json.dumps(payload, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            self.rest_send.path = path
            self.rest_send.verb = verb
            self.rest_send.payload = payload
            self.rest_send.commit()

            self.result_current = self.rest_send.result_current
            self.result = self.rest_send.result_current
            self.response_current = self.rest_send.response_current
            self.response = self.rest_send.response_current

            self.task_result.response_merged = self.response_current
            if self.response_current["RETURN_CODE"] == 200:
                self.task_result.diff_merged = payload

            msg = "self.response_current: "
            msg += f"{json.dumps(self.response_current, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            msg = "self.response: "
            msg += f"{json.dumps(self.response, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            msg = "self.result_current: "
            msg += f"{json.dumps(self.result_current, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            msg = "self.result: "
            msg += f"{json.dumps(self.result, indent=4, sort_keys=True)}"
            self.log.debug(msg)

    def send_need_normal_mode(self):
        """
        Caller: send_need()

        Build and send the payload to create the
        fabrics specified in the playbook.
        """
        method_name = inspect.stack()[0][3]
        self.fabric_create = FabricCreateBulk(self.ansible_module)
        self.fabric_create.payloads = self.need
        self.fabric_create.commit()
        self.update_diff_and_response(self.fabric_create)

    def update_diff_and_response(self, obj) -> None:
        """
        Update the appropriate self.task_result diff and response,
        based on the current ansible state, with the diff and
        response from obj.
        """
        for diff in obj.diff:
            msg = f"diff: {json_pretty(diff)}"
            self.log.debug(msg)
            if self.state == "deleted":
                self.task_result.diff_deleted = diff
            if self.state == "merged":
                self.task_result.diff_merged = diff
            if self.state == "query":
                self.task_result.diff_query = diff

        msg = f"PRE_FOR: state {self.state} response: {json_pretty(obj.response)}"
        self.log.debug(msg)
        for response in obj.response:
            if "DATA" in response:
                response.pop("DATA")
            msg = f"state {self.state} response: {json_pretty(response)}"
            self.log.debug(msg)
            if self.state == "deleted":
                self.task_result.response_deleted = copy.deepcopy(response)
            if self.state == "merged":
                self.task_result.response_merged = copy.deepcopy(response)
            if self.state == "query":
                self.task_result.response_query = copy.deepcopy(response)

    def _failure(self, resp):
        """
        Caller: self.create_fabrics()

        This came from dcnm_inventory.py, but doesn't seem to be correct
        for the case where resp["DATA"] does not exist?

        If resp["DATA"] does not exist, the contents of the
        if block don't seem to actually do anything:
            - data will be None
            - Hence, data.get("stackTrace") will also be None
            - Hence, data.update() and res.update() are never executed

        So, the only two lines that will actually ever be executed are
        the happy path:

        res = copy.deepcopy(resp)
        self.ansible_module.fail_json(msg=res)
        """
        res = copy.deepcopy(resp)

        if not resp.get("DATA"):
            data = copy.deepcopy(resp.get("DATA"))
            if data.get("stackTrace"):
                data.update(
                    {"stackTrace": "Stack trace is hidden, use '-vvvvv' to print it"}
                )
                res.update({"DATA": data})

        self.log.debug("HERE")
        self.ansible_module.fail_json(msg=res)

def main():
    """main entry point for module execution"""

    element_spec = dict(
        config=dict(required=False, type="list", elements="dict"),
        state=dict(default="merged", choices=["deleted", "merged", "query"]),
    )

    ansible_module = AnsibleModule(argument_spec=element_spec, supports_check_mode=True)

    # Create the base/parent logger for the dcnm collection.
    # To enable logging, set enable_logging to True.
    # log.config can be either a dictionary, or a path to a JSON file
    # Both dictionary and JSON file formats must be conformant with
    # logging.config.dictConfig and must not log to the console.
    # For an example configuration, see:
    # $ANSIBLE_COLLECTIONS_PATH/cisco/dcnm/plugins/module_utils/common/logging_config.json
    enable_logging = False
    log = Log(ansible_module)
    if enable_logging is True:
        collection_path = (
            "/Users/arobel/repos/collections/ansible_collections/cisco/dcnm"
        )
        config_file = (
            f"{collection_path}/plugins/module_utils/common/logging_config.json"
        )
        log.config = config_file
    log.commit()

    task = FabricVxlanTask(ansible_module)
    task.log.debug(f"state: {ansible_module.params['state']}")

    if ansible_module.params["state"] == "merged":
        task.get_want()
        task.get_have()
        task.handle_merged_state()
    elif ansible_module.params["state"] == "deleted":
        task.get_want()
        task.handle_deleted_state()
    elif ansible_module.params["state"] == "query":
        task.get_want()
        task.handle_query_state()
    else:
        msg = f"Unknown state {task.ansible_module.params['state']}"
        task.ansible_module.fail_json(msg)

    msg = "task_result.module_result: "
    msg += f"{json.dumps(task.task_result.module_result, indent=4, sort_keys=True)}"
    task.log.debug(msg)
    ansible_module.exit_json(**task.task_result.module_result)


if __name__ == "__main__":
    main()
