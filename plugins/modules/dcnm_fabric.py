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
module: dcnm_fabric
short_description: Create Fabrics.
version_added: "0.9.0"
description:
    - "Create Fabrics."
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
      fabric_type:
        description:
        - The type of fabric
        type: str
        required: true
        default: "VXLAN_EVPN"
        choices:
        - "VXLAN_EVPN"
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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_fabric import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.common import \
    FabricCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.create import \
    FabricCreateBulk
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.delete import \
    FabricDelete
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details import \
    FabricDetailsByName
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_task_result import \
    FabricTaskResult
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.query import \
    FabricQuery
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.update import \
    FabricUpdateBulk
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.vxlan.verify_fabric_params import \
    VerifyFabricParams

# from ansible_collections.cisco.dcnm.plugins.module_utils.common.merge_dicts import \
#     MergeDicts
# from ansible_collections.cisco.dcnm.plugins.module_utils.common.params_merge_defaults import \
#     ParamsMergeDefaults
# from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.vxlan.params_spec import \
#     ParamsSpec
# from ansible_collections.cisco.dcnm.plugins.module_utils.common.params_validate import \
#     ParamsValidate


def json_pretty(msg):
    """
    Return a pretty-printed JSON string for logging messages
    """
    return json.dumps(msg, indent=4, sort_keys=True)


class TaskCommon(FabricCommon):
    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        super().__init__(ansible_module)
        method_name = inspect.stack()[0][3]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED TaskCommon(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.endpoints = ApiEndpoints()

        self._implemented_states = set()

        self.params = ansible_module.params
        self._verify_fabric_params = VerifyFabricParams()
        self.rest_send = RestSend(self.ansible_module)
        # populated in self.validate_input()
        self.payloads = {}

        self.config = ansible_module.params.get("config")
        if not isinstance(self.config, list):
            msg = "expected list type for self.config. "
            msg = f"got {type(self.config).__name__}"
            self.ansible_module.fail_json(msg, **self.failed_result)

        self.validated = []
        self.have = {}
        self.want = []
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
        self.have = FabricDetailsByName(self.ansible_module)
        self.have.refresh()

    def get_want(self) -> None:
        """
        Caller: main()

        1. Validate the playbook configs
        2. Update self.want with the playbook configs
        """
        method_name = inspect.stack()[0][3]
        merged_configs = []
        for config in self.config:
            merged_configs.append(copy.deepcopy(config))

        self.want = []
        for config in merged_configs:
            self.want.append(copy.deepcopy(config))

        # Exit if there's nothing to do
        if len(self.want) == 0:
            self.ansible_module.exit_json(**self.task_result.module_result)

    def update_diff_and_response(self, obj) -> None:
        """
        Update the appropriate self.task_result diff and response,
        based on the current ansible state, with the diff and
        response from obj.
        """
        for diff in obj.diff:
            if self.state == "deleted":
                self.task_result.diff_deleted = copy.deepcopy(diff)
            if self.state == "merged":
                self.task_result.diff_merged = copy.deepcopy(diff)
            if self.state == "query":
                self.task_result.diff_query = copy.deepcopy(diff)

        for response in obj.response:
            if self.state == "deleted":
                self.task_result.response_deleted = copy.deepcopy(response)
            if self.state == "merged":
                self.task_result.response_merged = copy.deepcopy(response)
            if self.state == "query":
                self.task_result.response_query = copy.deepcopy(response)


class QueryTask(TaskCommon):
    """
    Query state for FabricVxlanTask
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        super().__init__(ansible_module)
        method_name = inspect.stack()[0][3]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED QueryTask(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self._implemented_states.add("query")

    def commit(self) -> None:
        """
        1.  query the fabrics in self.want that exist on the controller
        """
        self.get_want()
        method_name = inspect.stack()[0][3]
        instance = FabricQuery(self.ansible_module)
        fabric_names_to_query = []
        for want in self.want:
            fabric_names_to_query.append(want["fabric_name"])
        instance.fabric_names = copy.copy(fabric_names_to_query)
        instance.commit()
        self.update_diff_and_response(instance)


class DeletedTask(TaskCommon):
    """
    deleted state for FabricVxlanTask
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        super().__init__(ansible_module)
        method_name = inspect.stack()[0][3]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED DeletedTask(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self._implemented_states.add("deleted")

    def commit(self) -> None:
        """
        delete the fabrics in self.want that exist on the controller
        """
        self.get_want()
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += "entered"
        self.log.debug(msg)
        instance = FabricDelete(self.ansible_module)
        fabric_names_to_delete = []
        for want in self.want:
            fabric_names_to_delete.append(want["fabric_name"])
        instance.fabric_names = fabric_names_to_delete
        instance.commit()
        self.update_diff_and_response(instance)


class MergedTask(TaskCommon):
    """
    Ansible support for Data Center VXLAN EVPN
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        super().__init__(ansible_module)
        method_name = inspect.stack()[0][3]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED MergedTask(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.need_create = []
        self.need_update = []

        self._implemented_states.add("merged")

    def get_need(self):
        """
        Caller: commit()

        Build self.need for merged state
        """
        method_name = inspect.stack()[0][3]
        self.payloads = {}
        for want in self.want:
            if want["FABRIC_NAME"] not in self.have.all_data:
                self.need_create.append(want)
            else:
                self.need_update.append(want)

    def commit(self):
        """
        Caller: main()

        Commit the merged state request
        """
        method_name = inspect.stack()[0][3]
        self.log.debug(f"{self.class_name}.{method_name}: entered")

        self.get_want()
        self.get_have()
        self.get_need()
        self.send_need_create()
        self.send_need_update()

    def send_need_create(self) -> None:
        """
        Caller: commit()

        Build and send the payload to create fabrics specified in the playbook.
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: entered. "
        msg += f"self.need_create: {json_pretty(self.need_create)}"
        self.log.debug(msg)

        if len(self.need_create) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "No fabrics to create."
            self.log.debug(msg)
            return

        self.fabric_create = FabricCreateBulk(self.ansible_module)
        self.fabric_create.payloads = self.need_create
        self.fabric_create.commit()
        self.update_diff_and_response(self.fabric_create)

    def send_need_update(self) -> None:
        """
        Caller: commit()

        Build and send the payload to create fabrics specified in the playbook.
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: entered. "
        msg += f"self.need_update: {json_pretty(self.need_update)}"
        self.log.debug(msg)

        if len(self.need_update) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "No fabrics to update."
            self.log.debug(msg)
            return

        self.fabric_update = FabricUpdateBulk(self.ansible_module)
        self.fabric_update.payloads = self.need_update
        self.fabric_update.commit()
        self.update_diff_and_response(self.fabric_update)


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

    if ansible_module.params["state"] == "merged":
        task = MergedTask(ansible_module)
        task.commit()
    elif ansible_module.params["state"] == "deleted":
        task = DeletedTask(ansible_module)
        task.commit()
    elif ansible_module.params["state"] == "query":
        task = QueryTask(ansible_module)
        task.commit()
    else:
        # We should never get here since the state parameter has
        # already been validated.
        msg = f"Unknown state {task.ansible_module.params['state']}"
        task.ansible_module.fail_json(msg)

    ansible_module.exit_json(**task.task_result.module_result)


if __name__ == "__main__":
    main()
