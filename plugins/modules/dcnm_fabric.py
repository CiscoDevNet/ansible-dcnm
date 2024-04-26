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
author: Allen Robel (@quantumonion)
options:
  state:
    description:
    - The state of DCNM after module completion.
    - I(merged) and I(query) are the only states supported.
    type: str
    choices:
      - deleted
      - merged
      - query
    default: merged
  config:
    description:
    - A dictionary of fabric configurations
    type: list
    elements: dict
    suboptions:
      AAA_REMOTE_IP_ENABLED:
        description:
        - Enable (True) or disable (False) AAA remote IP
        - NDFC GUI label, Enable AAA IP Authorization
        - NDFC GUI tab, Advanced
        type: bool
        required: false
        default: False
      ADVERTISE_PIP_BGP:
        description:
        - Enable (True) or disable (False) usage of Primary VTEP IP Advertisement As Next-Hop Of Prefix Routes
        - NDFC GUI label, vPC advertise-pip
        - NDFC GUI tab, VPC
        type: bool
        required: false
        default: False
      ANYCAST_BGW_ADVERTISE_PIP:
        description:
        - Enable (True) or disable (False) advertising Anycast Border Gateway PIP as VTEP.
        - Effective after Recalculate Config on parent MSD fabric.
        - NDFC GUI label, Anycast Border Gateway advertise-pip
        - NDFC GUI tab, Advanced
        type: bool
        required: false
        default: False
      ANYCAST_GW_MAC:
        description:
        - Shared MAC address for all leafs (xx:xx:xx:xx:xx:xx, xxxx.xxxx.xxxx, etc)
        - NDFC GUI label, Anycast Gateway MAC
        - NDFC GUI tab, General Parameters
        type: str
        required: false
        default: "2020.0000.00aa"
      ANYCAST_LB_ID:
        description:
        - Underlay Anycast Loopback Id
        - NDFC GUI label, Underlay Anycast Loopback Id
        - NDFC GUI tab, Protocols
        type: int
        required: false
        default: 10
      ANYCAST_RP_IP_RANGE:
        description:
        - Anycast or Phantom RP IP Address Range
        - NDFC GUI label, Underlay RP Loopback IP Range
        - NDFC GUI tab, Resources
        type: str
        required: false
        default: 10.254.254.0/24
      AUTO_SYMMETRIC_DEFAULT_VRF:
        description:
        - Enable (True) or disable (False) auto generation of Default VRF interface and BGP peering configuration on managed neighbor devices.
        - If True, auto created VRF Lite IFC links will have 'Auto Deploy Default VRF for Peer' enabled.
        - vrf_lite_autoconfig must be set to 1
        - AUTO_SYMMETRIC_VRF_LITE must be set to True
        - AUTO_VRFLITE_IFC_DEFAULT_VRF must be set to True
        - NDFC GUI label, Auto Deploy Default VRF for Peer
        - NDFC GUI tab, Resources
        type: bool
        required: false
        default: False
      AUTO_SYMMETRIC_VRF_LITE:
        description:
        - Enable (True) or disable (False) auto generation of VRF LITE sub-interface and BGP peering configuration on managed neighbor devices.
        - If True, auto created VRF Lite IFC links will have 'Auto Deploy for Peer' enabled.
        - NDFC GUI label, Auto Deploy for Peer
        - NDFC GUI tab, Resources
        - VRF_LITE_AUTOCONFIG must be set to 1
        type: bool
        required: false
        default: False
      AUTO_VRFLITE_IFC_DEFAULT_VRF:
        description:
        - Enable (True) or disable (False) auto generation of Default VRF interface and BGP peering configuration on VRF LITE IFC auto deployment.
        - If True, auto created VRF Lite IFC links will have 'Auto Deploy Default VRF' enabled.
        - NDFC GUI label, Auto Deploy Default VRF
        - NDFC GUI tab, Resources
        - VRF_LITE_AUTOCONFIG must be set to 1
        type: bool
        required: false
        default: False
      BGP_AS:
        description:
        - The fabric BGP Autonomous System number
        - NDFC GUI label, BGP ASN
        - NDFC GUI tab, General Parameters
        type: str
        required: true
      DEFAULT_VRF_REDIS_BGP_RMAP:
        description:
        - Route Map used to redistribute BGP routes to IGP in default vrf in auto created VRF Lite IFC links
        - NDFC GUI label, Redistribute BGP Route-map Name
        - NDFC GUI tab, Resources
        type: str
        required: false
      FABRIC_NAME:
        description:
        - The name of the fabric
        type: str
        required: true
      FABRIC_TYPE:
        description:
        - The type of fabric
        type: str
        required: true
        choices:
        - "VXLAN_EVPN"
      PM_ENABLE:
        description:
        - Enable (True) or disable (False) fabric performance monitoring
        - NDFC GUI label, Enable Performance Monitoring
        - NDFC GUI tab, General Parameters
        type: bool
        required: false
        default: False
      REPLICATION_MODE:
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
      VRF_LITE_AUTOCONFIG:
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
# pylint: disable=wrong-import-position
import copy
import inspect
import json
import logging

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.common.exceptions import \
    ControllerResponseError
from ansible_collections.cisco.dcnm.plugins.module_utils.common.log import Log
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
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
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_summary import \
    FabricSummary
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_types import \
    FabricTypes
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.query import \
    FabricQuery
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.template_get import \
    TemplateGet
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.update import \
    FabricUpdateBulk
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.verify_playbook_params import \
    VerifyPlaybookParams


def json_pretty(msg):
    """
    Return a pretty-printed JSON string for logging messages
    """
    return json.dumps(msg, indent=4, sort_keys=True)


class Common(FabricCommon):
    """
    Common methods, properties, and resources for all states.
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        super().__init__(params)
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.results = Results()
        self.results.state = self.state
        self.results.check_mode = self.check_mode

        msg = "ENTERED Common(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.endpoints = ApiEndpoints()

        self._implemented_states = set()

        self._verify_playbook_params = VerifyPlaybookParams()

        # populated in self.validate_input()
        self.payloads = {}

        self.config = params.get("config")
        if not isinstance(self.config, list):
            msg = "expected list type for self.config. "
            msg += f"got {type(self.config).__name__}"
            raise ValueError(msg)

        self.validated = []
        self.have = {}
        self.want = []
        self.query = []

        self._build_properties()

    def _build_properties(self):
        self._properties["ansible_module"] = None

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
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self.have = FabricDetailsByName(self.params)
        self.have.rest_send = RestSend(self.ansible_module)
        self.have.refresh()

    def get_want(self) -> None:
        """
        Caller: main()

        1. Validate the playbook configs
        2. Update self.want with the playbook configs
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        merged_configs = []
        for config in self.config:
            try:
                self._verify_payload(config)
            except ValueError as error:
                self.ansible_module.fail_json(f"{error}", **self.results.failed_result)
            merged_configs.append(copy.deepcopy(config))

        self.want = []
        for config in merged_configs:
            self.want.append(copy.deepcopy(config))

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


class Deleted(Common):
    """
    Handle deleted state
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        super().__init__(params)
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.fabric_delete = FabricDelete(self.params)

        msg = "ENTERED Deleted(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self._implemented_states.add("deleted")

    def commit(self) -> None:
        """
        delete the fabrics in self.want that exist on the controller
        """
        self.get_want()
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        msg = f"{self.class_name}.{method_name}: "
        msg += "entered"
        self.log.debug(msg)

        self.rest_send = RestSend(self.ansible_module)

        self.fabric_details = FabricDetailsByName(self.params)
        self.fabric_details.rest_send = self.rest_send

        self.fabric_summary = FabricSummary(self.params)
        self.fabric_summary.rest_send = self.rest_send

        self.fabric_delete.rest_send = self.rest_send
        self.fabric_delete.fabric_details = self.fabric_details
        self.fabric_delete.fabric_summary = self.fabric_summary
        self.fabric_delete.results = self.results

        fabric_names_to_delete = []
        for want in self.want:
            fabric_names_to_delete.append(want["fabric_name"])

        try:
            self.fabric_delete.fabric_names = fabric_names_to_delete
        except ValueError as error:
            self.ansible_module.fail_json(
                f"{error}", **self.fabric_delete.results.failed_result
            )

        try:
            self.fabric_delete.commit()
        except ValueError as error:
            self.ansible_module.fail_json(
                f"{error}", **self.fabric_delete.results.failed_result
            )


class Merged(Common):
    """
    Handle merged state
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        super().__init__(params)
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.fabric_details = FabricDetailsByName(self.params)
        self.fabric_summary = FabricSummary(self.params)
        self.fabric_create = FabricCreateBulk(self.params)
        self.fabric_types = FabricTypes()
        self.fabric_update = FabricUpdateBulk(self.params)
        self.template = TemplateGet()

        msg = f"ENTERED Merged.{method_name}: "
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
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self.payloads = {}
        for want in self.want:

            try:
                self._verify_playbook_params.config_playbook = want
            except TypeError as error:
                self.ansible_module.fail_json(f"{error}", **self.results.failed_result)

            fabric_type = want.get("FABRIC_TYPE", None)
            try:
                self.fabric_types.fabric_type = fabric_type
            except ValueError as error:
                self.ansible_module.fail_json(f"{error}", **self.results.failed_result)

            try:
                template_name = self.fabric_types.template_name
            except ValueError as error:
                self.ansible_module.fail_json(f"{error}", **self.results.failed_result)

            self.template.rest_send = self.rest_send
            self.template.template_name = template_name

            try:
                self.template.refresh()
            except ValueError as error:
                self.ansible_module.fail_json(f"{error}", **self.results.failed_result)
            except ControllerResponseError as error:
                msg = f"{self.class_name}.{method_name}: "
                msg += "Controller returned error when attempting to retrieve "
                msg += f"template: {template_name}. "
                msg += f"Error detail: {error}"
                self.ansible_module.fail_json(f"{msg}", **self.results.failed_result)

            try:
                self._verify_playbook_params.template = self.template.template
            except TypeError as error:
                self.ansible_module.fail_json(f"{error}", **self.results.failed_result)

            # Append to need_create if the fabric does not exist.
            # Otherwise, append to need_update.
            if want["FABRIC_NAME"] not in self.have.all_data:
                try:
                    self._verify_playbook_params.config_controller = None
                except TypeError as error:
                    self.ansible_module.fail_json(
                        f"{error}", **self.results.failed_result
                    )

                try:
                    self._verify_playbook_params.commit()
                except ValueError as error:
                    self.ansible_module.fail_json(
                        f"{error}", **self.results.failed_result
                    )

                self.need_create.append(want)

            else:

                nv_pairs = self.have.all_data[want["FABRIC_NAME"]]["nvPairs"]
                try:
                    self._verify_playbook_params.config_controller = nv_pairs
                except TypeError as error:
                    self.ansible_module.fail_json(
                        f"{error}", **self.results.failed_result
                    )
                try:
                    self._verify_playbook_params.commit()
                except (ValueError, KeyError) as error:
                    self.ansible_module.fail_json(
                        f"{error}", **self.results.failed_result
                    )

                self.need_update.append(want)

    def commit(self):
        """
        Commit the merged state request
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        msg = f"{self.class_name}.{method_name}: entered"
        self.log.debug(msg)

        self.rest_send = RestSend(self.ansible_module)
        self.fabric_details.rest_send = self.rest_send
        self.fabric_summary.rest_send = self.rest_send

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
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        msg = f"{self.class_name}.{method_name}: entered. "
        msg += f"self.need_create: {json_pretty(self.need_create)}"
        self.log.debug(msg)

        if len(self.need_create) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "No fabrics to create."
            self.log.debug(msg)
            return

        self.fabric_create.fabric_details = self.fabric_details
        self.fabric_create.rest_send = self.rest_send
        self.fabric_create.results = self.results

        try:
            self.fabric_create.payloads = self.need_create
        except ValueError as error:
            self.ansible_module.fail_json(
                f"{error}", **self.fabric_create.results.failed_result
            )

        try:
            self.fabric_create.commit()
        except ValueError as error:
            self.ansible_module.fail_json(
                f"{error}", **self.fabric_create.results.failed_result
            )

    def send_need_update(self) -> None:
        """
        Caller: commit()

        Build and send the payload to create fabrics specified in the playbook.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        msg = f"{self.class_name}.{method_name}: entered. "
        msg += "self.need_update: "
        msg += f"{json_pretty(self.need_update)}"
        self.log.debug(msg)

        if len(self.need_update) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "No fabrics to update."
            self.log.debug(msg)
            return

        self.fabric_update.fabric_details = self.fabric_details
        self.fabric_update.fabric_summary = self.fabric_summary
        self.fabric_update.rest_send = RestSend(self.ansible_module)
        self.fabric_update.results = self.results

        try:
            self.fabric_update.payloads = self.need_update
        except ValueError as error:
            self.ansible_module.fail_json(
                f"{error}", **self.fabric_update.results.failed_result
            )

        try:
            self.fabric_update.commit()
        except ValueError as error:
            self.ansible_module.fail_json(
                f"{error}", **self.fabric_update.results.failed_result
            )


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
        1.  query the fabrics in self.want that exist on the controller
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.fabric_details = FabricDetailsByName(self.params)
        self.fabric_details.rest_send = RestSend(self.ansible_module)

        self.get_want()

        fabric_query = FabricQuery(self.params)
        fabric_query.fabric_details = self.fabric_details

        fabric_query.results = self.results
        fabric_names_to_query = []
        for want in self.want:
            fabric_names_to_query.append(want["fabric_name"])
        try:
            fabric_query.fabric_names = copy.copy(fabric_names_to_query)
        except ValueError as error:
            self.ansible_module.fail_json(
                f"{error}", **fabric_query.results.failed_result
            )

        try:
            fabric_query.commit()
        except ValueError as error:
            self.ansible_module.fail_json(
                f"{error}", **fabric_query.results.failed_result
            )


def main():
    """main entry point for module execution"""

    argument_spec = {}
    argument_spec["config"] = {"required": False, "type": "list", "elements": "dict"}
    argument_spec["state"] = {
        "default": "merged",
        "choices": ["deleted", "merged", "query"],
    }

    ansible_module = AnsibleModule(
        argument_spec=argument_spec, supports_check_mode=True
    )

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

    ansible_module.params["check_mode"] = ansible_module.check_mode
    if ansible_module.params["state"] == "merged":
        task = Merged(ansible_module.params)
        task.ansible_module = ansible_module
        task.commit()
    elif ansible_module.params["state"] == "deleted":
        task = Deleted(ansible_module.params)
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
