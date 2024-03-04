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
"""
Classes and methods for Ansible support of NDFC Data Center VXLAN EVPN Fabric.

Ansible states "merged", "deleted", and "query" are implemented.
"""
from __future__ import absolute_import, division, print_function

import copy
import inspect
import json
import logging
from typing import Any, Dict, List

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.common.log import Log
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
    validate_list_of_dicts,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.endpoints import (
    ApiEndpoints
)
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.vxlan.verify_fabric_params import (
    VerifyFabricParams,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_task_result import (
    FabricTaskResult
)

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


class FabricVxlanTask:
    """
    Ansible support for Data Center VXLAN EVPN
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED FabricVxlanTask()")

        self.endpoints = ApiEndpoints()

        self._implemented_states = set()
        self._implemented_states.add("merged")

        self.ansible_module = ansible_module
        self.params = ansible_module.params
        self.verify = VerifyFabricParams()
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

        self.task_result = dict(changed=False, diff=[], response=[])

        self.mandatory_keys = {"fabric_name", "bgp_as"}
        # Populated in self.get_have()
        self.fabric_details = {}
        # Not currently using. Commented out in self.get_have()
        self.inventory_data = {}
        for item in self.config:
            if not self.mandatory_keys.issubset(item):
                msg = f"{self.class_name}.{method_name}: "
                msg += f"missing mandatory keys in {item}. "
                msg += f"expected {self.mandatory_keys}"
                self.ansible_module.fail_json(msg=msg)

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
        endpoint = self.endpoints.fabrics
        path = endpoint["path"]
        verb = endpoint["verb"]
        response = dcnm_send(self.ansible_module, verb, path)
        result = self._handle_get_response(response)
        if not result["success"]:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Unable to retrieve fabric information from "
            msg += "the controller."
            self.ansible_module.fail_json(msg=msg)
        self.have = {}
        for item in response["DATA"]:
            self.have[item["fabricName"]] = {}
            self.have[item["fabricName"]]["fabric_name"] = item["fabricName"]
            self.have[item["fabricName"]]["fabric_config"] = item

    def get_want(self):
        """
        Caller: main()

        Update self.want for all fabrics defined in the playbook
        """
        self.want = []
        for fabric_config in self.config:
            self.want.append(copy.deepcopy(fabric_config))

    def get_need_for_merged_state(self):
        """
        Caller: handle_merged_state()

        Build self.need for state merged
        """
        method_name = inspect.stack()[0][3]
        need: List[Dict[str, Any]] = []
        for want in self.want:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"want: {json.dumps(want, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            if want["fabric_name"] in self.have:
                continue
            need.append(want)
        self.need = copy.deepcopy(need)

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
            self.ansible_module.exit_json(**self.task_result)
        self.send_need()

    def send_need(self):
        """
        Caller: handle_merged_state()

        Build and send the payload to create the
        fabrics specified in the playbook.
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += f"need: {json.dumps(self.need, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        if len(self.need) == 0:
            self.task_result["changed"] = False
            self.task_result["success"] = True
            self.task_result["diff"] = []
            self.ansible_module.exit_json(**self.task_result)
        for item in self.need:
            fabric_name = item["fabric_name"]
            self.endpoints.fabric_name = fabric_name
            self.endpoints.template_name = "Easy_Fabric"

            try:
                endpoint = self.endpoints.fabric_create
            except ValueError as error:
                self.ansible_module.fail_json(error)

            path = endpoint["path"]
            verb = endpoint["verb"]

            payload = self.payloads[fabric_name]
            msg = f"{self.class_name}.{method_name}: "
            msg += f"verb: {verb}, path: {path}"
            self.log.debug(msg)
            msg = f"{self.class_name}.{method_name}: "
            msg += f"fabric_name: {fabric_name}, payload: {json.dumps(payload, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            response = dcnm_send(self.ansible_module, verb, path, data=json.dumps(payload))
            result = self._handle_post_put_response(response, verb)
            self.log.debug(f"response]: {json.dumps(response, indent=4, sort_keys=True)}")
            self.log.debug(f"result: {json.dumps(result, indent=4, sort_keys=True)}")
            self.task_result["changed"] = result["changed"]

            if not result["success"]:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"failed to create fabric {fabric_name}. "
                msg += f"response: {response}"
                self._failure(response)

    @staticmethod
    def _build_params_spec_for_merged_state():
        """
        Build the specs for the parameters expected when state == merged.

        Caller: _validate_input_for_merged_state()
        Return: params_spec, a dictionary containing the set of
                parameter specifications.
        """
        params_spec = {}
        params_spec.update(
            aaa_remote_ip_enabled=dict(required=False, type="bool", default=False)
        )
        # TODO:6 active_migration
        # active_migration doesn't seem to be represented in
        # the NDFC EasyFabric GUI.  Add this param if we figure out
        # what it's used for and where in the GUI it's represented
        params_spec.update(
            advertise_pip_bgp=dict(required=False, type="bool", default=False)
        )
        # TODO:6 agent_intf (add if required)
        params_spec.update(
            anycast_bgw_advertise_pip=dict(required=False, type="bool", default=False)
        )
        params_spec.update(
            anycast_gw_mac=dict(required=False, type="str", default="2020.0000.00aa")
        )
        params_spec.update(
            anycast_lb_id=dict(
                required=False, type="int", range_min=0, range_max=1023, default=""
            )
        )
        params_spec.update(
            auto_symmetric_default_vrf=dict(required=False, type="bool", default=False)
        )
        params_spec.update(
            auto_symmetric_vrf_lite=dict(required=False, type="bool", default=False)
        )
        params_spec.update(
            auto_vrflite_ifc_default_vrf=dict(
                required=False, type="bool", default=False
            )
        )
        params_spec.update(bgp_as=dict(required=True, type="str"))
        params_spec.update(
            default_vrf_redis_bgp_rmap=dict(required=False, type="str", default="")
        )
        params_spec.update(fabric_name=dict(required=True, type="str"))
        params_spec.update(pm_enable=dict(required=False, type="bool", default=False))
        params_spec.update(
            replication_mode=dict(
                required=False,
                type="str",
                default="Multicast",
                choices=["Ingress", "Multicast"],
            )
        )
        params_spec.update(
            vrf_lite_autoconfig=dict(
                required=False, type="int", default=0, choices=[0, 1]
            )
        )
        return params_spec

    def validate_input(self):
        """
        Caller: main()

        Validate the playbook parameters
        Build the payloads for each fabric
        """

        state = self.params["state"]

        # TODO:2 remove this when we implement query state
        if state not in self._implemented_states:
            msg = f"Got state {state}. "
            msg += f"Expected one of: {','.join(sorted(self._implemented_states))}"
            self.ansible_module.fail_json(msg=msg)

        if state == "merged":
            self._validate_input_for_merged_state()

        self.payloads = {}
        for fabric_config in self.config:
            verify = VerifyFabricParams()
            verify.state = state
            verify.config = fabric_config
            verify.validate_config()
            if verify.result is False:
                self.ansible_module.fail_json(msg=verify.msg)
            self.payloads[fabric_config["fabric_name"]] = verify.payload

    def _validate_input_for_merged_state(self):
        """
        Caller: self._validate_input()

        Valid self.config contains appropriate values for merged state
        """
        params_spec = self._build_params_spec_for_merged_state()
        msg = None
        if not self.config:
            msg = "config: element is mandatory for state merged"
            self.ansible_module.fail_json(msg=msg)

        valid_params, invalid_params = validate_list_of_dicts(
            self.config, params_spec, self.ansible_module
        )
        # We're not using self.validated. Keeping this to avoid
        # linter error due to non-use of valid_params
        self.validated = copy.deepcopy(valid_params)

        if invalid_params:
            msg = "Invalid parameters in playbook: "
            msg += f"{','.join(invalid_params)}"
            self.ansible_module.fail_json(msg=msg)

    def _handle_get_response(self, response):
        """
        Caller:
            - self.get_have()
        Handle NDFC responses to GET requests
        Returns: dict() with the following keys:
        - found:
            - False, if request error was "Not found" and RETURN_CODE == 404
            - True otherwise
        - success:
            - False if RETURN_CODE != 200 or MESSAGE != "OK"
            - True otherwise
        """
        # Example response
        # {
        #     'RETURN_CODE': 404,
        #     'METHOD': 'GET',
        #     'REQUEST_PATH': '...user path goes here...',
        #     'MESSAGE': 'Not Found',
        #     'DATA': {
        #         'timestamp': 1691970528998,
        #         'status': 404,
        #         'error': 'Not Found',
        #         'path': '/rest/control/fabrics/IR-Fabric'
        #     }
        # }
        result = {}
        success_return_codes = {200, 404}
        #self.log.debug(f"_handle_get_request: response {json.dumps(response, indent=4, sort_keys=True)}")
        if (
            response.get("RETURN_CODE") == 404
            and response.get("MESSAGE") == "Not Found"
        ):
            result["found"] = False
            result["success"] = True
            return result
        if (
            response.get("RETURN_CODE") not in success_return_codes
            or response.get("MESSAGE") != "OK"
        ):
            result["found"] = False
            result["success"] = False
            return result
        result["found"] = True
        result["success"] = True
        return result

    def _handle_post_put_response(self, response, verb):
        """
        Caller:
            - self.create_fabrics()

        Handle POST, PUT responses from NDFC.

        Returns: dict() with the following keys:
        - changed:
            - True if changes were made to NDFC
            - False otherwise
        - success:
            - False if RETURN_CODE != 200 or MESSAGE != "OK"
            - True otherwise

        """
        # Example response
        # {
        #     'RETURN_CODE': 200,
        #     'METHOD': 'POST',
        #     'REQUEST_PATH': '...user path goes here...',
        #     'MESSAGE': 'OK',
        #     'DATA': {...}
        valid_verbs = {"POST", "PUT"}
        if verb not in valid_verbs:
            msg = f"invalid verb {verb}. "
            msg += f"expected one of: {','.join(sorted(valid_verbs))}"
            self.ansible_module.fail_json(msg=msg)

        result = {}
        if response.get("MESSAGE") != "OK":
            result["success"] = False
            result["changed"] = False
            return result
        if response.get("ERROR"):
            result["success"] = False
            result["changed"] = False
            return result
        result["success"] = True
        result["changed"] = True
        return result

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
        state=dict(default="merged", choices=["merged", "query"]),
    )

    ansible_module = AnsibleModule(argument_spec=element_spec, supports_check_mode=True)

    # Create the base/parent logger for the dcnm collection.
    # To disable logging, comment out log.config = <file_path> below
    # log.config can be either a dictionary, or a path to a JSON file
    # Both dictionary and JSON file formats must be conformant with
    # logging.config.dictConfig and must not log to the console.
    # For an example configuration, see:
    # $ANSIBLE_COLLECTIONS_PATH/cisco/dcnm/plugins/module_utils/common/logging_config.json
    log = Log(ansible_module)
    collection_path = "/Users/arobel/repos/collections/ansible_collections/cisco/dcnm"
    config_file = f"{collection_path}/plugins/module_utils/common/logging_config.json"
    log.config = config_file
    log.commit()

    task = FabricVxlanTask(ansible_module)
    task.validate_input()
    task.get_have()
    task.get_want()

    task.log.debug(f"state: {ansible_module.params['state']}")

    if ansible_module.params["state"] == "merged":
        task.handle_merged_state()

    ansible_module.exit_json(**task.task_result)


if __name__ == "__main__":
    main()
