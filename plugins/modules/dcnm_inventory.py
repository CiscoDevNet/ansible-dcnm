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
__author__ = "Karthik Babu Harichandra Babu, Praveen Ramoorthy"

DOCUMENTATION = """
---
module: dcnm_inventory
short_description: Add and remove Switches from a DCNM managed VXLAN fabric.
version_added: "0.9.0"
description:
    - "Add and remove Switches from a DCNM managed VXLAN fabric."
author: Karthik Babu Harichandra Babu(@kharicha), Praveen Ramoorthy(@praveenramoorthy)
options:
  fabric:
    description:
    - Name of the target fabric for Inventory operations
    type: str
    required: yes
  state:
    description:
    - The state of DCNM after module completion.
    - I(merged) and I(query) are the only states supported for POAP.
    - I(merged) is the only state supported for RMA.
    type: str
    choices:
      - merged
      - overridden
      - deleted
      - query
    default: merged
  save:
    description:
    - Save/Recalculate the configuration of the fabric after the inventory is updated
    type: bool
    required: false
    default: true
  deploy:
    description:
    - Deploy the pending configuration of the fabric after inventory is updated
    type: bool
    required: false
    default: true
  config:
    description:
    - List of switches being managed. Not required for state deleted
    type: list
    elements: dict
    suboptions:
      seed_ip:
        description:
        - Seed Name(support both IP address and dns_name) of the switch
          which needs to be added to the DCNM Fabric
        type: str
        required: true
      auth_proto:
        description:
        - Name of the authentication protocol to be used.
        - For POAP and RMA configurations authentication protocol should be I(MD5).
        choices: ['MD5', 'SHA', 'MD5_DES', 'MD5_AES', 'SHA_DES', 'SHA_AES']
        type: str
        required: false
        default: 'MD5'
      user_name:
        description:
        - Login username to the switch.
        - For POAP and RMA configurations username should be I(admin)
        type: str
        required: true
      password:
        description:
        - Login password to the switch
        type: str
        required: true
      max_hops:
        description:
        - Maximum Hops to reach the switch.
        - This parameter is deprecated(as on 2024-03-06)
        - Defaults to 0 irrespective of configured value.
        type: int
        required: false
        default: 0
      role:
        description:
        - Role which needs to be assigned to the switch
        choices: ['leaf', 'spine', 'border', 'border_spine', 'border_gateway', 'border_gateway_spine',
                 'super_spine', 'border_super_spine', 'border_gateway_super_spine', 'access', 'aggregation',
                 'edge_router', 'core_router', 'tor']
        type: str
        required: false
        default: leaf
      preserve_config:
        description:
        - Set this to false for greenfield deployment and true for brownfield deployment
        type: bool
        required: false
        default: false
      poap:
        description:
        - Configurations of switch to Bootstrap/Pre-provision.
        - Please note that POAP and DHCP configurations needs to enabled in fabric configuration
          before adding/preprovisioning switches through POAP.
        - Idempotence checks against inventory is only for B(IP Address) for Preprovision configs.
        - Idempotence checks against inventory is only for B(IP Address) and B(Serial Number) for Bootstrap configs.
        type: list
        elements: dict
        suboptions:
          discovery_username:
            description:
            - Username for device discovery during POAP and RMA discovery
            type: str
            required: false
          discovery_password:
            description:
            - Password for device discovery during POAP and RMA discovery
            type: str
            required: false
          serial_number:
            description:
            - Serial number of switch to Bootstrap.
            - When C(preprovision_serial) is provided along with C(serial_number),
              then the Preprovisioned switch(with serial number as in C(preprovision_serial)) will be swapped
              with a actual switch(with serial number in C(serial_number)) through bootstrap.
            - Swap feature is supported only on NDFC and is not supported on DCNM 11.x versions.
            type: str
            required: false
          preprovision_serial:
            description:
            - Serial number of switch to Pre-provision.
            - When C(preprovision_serial) is provided along with C(serial_number),
              then the Preprovisioned switch(with serial number as in C(preprovision_serial)) will be swapped
              with a actual switch(with serial number in C(serial_number)) through bootstrap.
            - Swap feature is supported only on NDFC and is not supported on DCNM 11.x versions.
            type: str
            required: false
          model:
            description:
            - Model of switch to Bootstrap/Pre-provision.
            type: str
            required: false
          version:
            description:
            - Software version of switch to Bootstrap/Pre-provision.
            type: str
            required: false
          hostname:
            description:
            - Hostname of switch to Bootstrap/Pre-provision.
            type: str
            required: false
          image_policy:
            description:
            - Name of the image policy to be applied on switch during Bootstrap/Pre-provision.
            type: str
            required: false
          config_data:
            description:
            - Basic config data of switch to Bootstrap/Pre-provision.
            - C(modulesModel) and C(gateway) are mandatory.
            - C(modulesModel) is list of model of modules in switch to Bootstrap/Pre-provision.
            - C(gateway) is the gateway IP with mask for the switch to Bootstrap/Pre-provision.
            - For other supported config data please refer to NDFC/DCNM configuration guide.
            type: dict
            required: false
      rma:
        description:
        - RMA an existing switch with a new one
        - Please note that the existing switch should be configured and deployed in maintenance mode
        - Please note that the existing switch being replaced should be shutdown state or out of network
        type: list
        elements: dict
        suboptions:
          discovery_username:
            description:
            - Username for device discovery during POAP and RMA discovery
            type: str
            required: false
          discovery_password:
            description:
            - Password for device discovery during POAP and RMA discovery
            type: str
            required: false
          serial_number:
            description:
            - Serial number of switch to Bootstrap for RMA.
            type: str
            required: true
          old_serial:
            description:
            - Serial number of switch to be replaced by RMA.
            type: str
            required: true
          model:
            description:
            - Model of switch to Bootstrap for RMA.
            type: str
            required: true
          version:
            description:
            - Software version of switch to Bootstrap for RMA.
            type: str
            required: true
          image_policy:
            description:
            - Name of the image policy to be applied on switch during Bootstrap for RMA.
            type: str
            required: false
          config_data:
            description:
            - Basic config data of switch to Bootstrap for RMA.
            - C(modulesModel) and C(gateway) are mandatory.
            - C(modulesModel) is list of model of modules in switch to Bootstrap for RMA.
            - C(gateway) is the gateway IP with mask for the switch to Bootstrap for RMA.
            - For other supported config data please refer to NDFC/DCNM configuration guide.
            type: dict
            required: true
  query_poap:
    description:
    - Query for Bootstrap(POAP) capable switches available.
    type: bool
    required: false
    default: false
"""

EXAMPLES = """
# This module supports the following states:
#
# Merged:
#   Switches defined in the playbook will be merged into the target fabric.
#     - If the switch does not exist it will be added.
#     - Switches that are not specified in the playbook will be untouched.
#
# Overridden:
#   The playbook will serve as source of truth for the target fabric.
#     - If the switch does not exist it will be added.
#     - If the switch is not defined in the playbook but exists in DCNM it will be removed.
#     - If the switch exists, properties that need to be modified and can be modified will be modified.
#
# Deleted:
#   Deletes the list of switches specified in the playbook.
#   If no switches are provided in the playbook, all the switches present on that DCNM fabric will be deleted.
#
# Query:
#   Returns the current DCNM state for the switches listed in the playbook.


# The following two switches will be merged into the existing fabric
- name: Merge switch into fabric
  cisco.dcnm.dcnm_inventory:
    fabric: vxlan-fabric
    state: merged # merged / deleted / overridden / query
    config:
    - seed_ip: 192.168.0.1
      auth_proto: MD5 # choose from [MD5, SHA, MD5_DES, MD5_AES, SHA_DES, SHA_AES]
      user_name: switch_username
      password: switch_password
      max_hops: 0
      role: spine
      preserve_config: False # boolean, default is  true
    - seed_ip: 192.168.0.2
      auth_proto: MD5 # choose from [MD5, SHA, MD5_DES, MD5_AES, SHA_DES, SHA_AES]
      user_name: switch_username
      password: switch_password
      max_hops: 0
      role: leaf
      preserve_config: False # boolean, default is true

# The following two switches will be added or updated in the existing fabric and all other
# switches will be removed from the fabric
- name: Override Switch
  cisco.dcnm.dcnm_inventory:
    fabric: vxlan-fabric
    state: overridden # merged / deleted / overridden / query
    config:
    - seed_ip: 192.168.0.1
      auth_proto: MD5 # choose from [MD5, SHA, MD5_DES, MD5_AES, SHA_DES, SHA_AES]
      user_name: switch_username
      password: switch_password
      max_hops: 0
      role: spine
      preserve_config: False # boolean, default is  true
    - seed_ip: 192.168.0.2
      auth_proto: MD5 # choose from [MD5, SHA, MD5_DES, MD5_AES, SHA_DES, SHA_AES]
      user_name: switch_username
      password: switch_password
      max_hops: 0
      role: leaf
      preserve_config: False # boolean, default is true

# The following two switches will be deleted in the existing fabric
- name: Delete selected switches
  cisco.dcnm.dcnm_inventory:
    fabric: vxlan-fabric
    state: deleted # merged / deleted / overridden / query
    config:
    - seed_ip: 192.168.0.1
    - seed_ip: 192.168.0.2

# All the switches will be deleted in the existing fabric
- name: Delete all the switches
  cisco.dcnm.dcnm_inventory:
    fabric: vxlan-fabric
    state: deleted # merged / deleted / overridden / query

# The following two switches information will be queried in the existing fabric
- name: Query switch into fabric
  cisco.dcnm.dcnm_inventory:
    fabric: vxlan-fabric
    state: query # merged / deleted / overridden / query
    config:
    - seed_ip: 192.168.0.1
      role: spine
    - seed_ip: 192.168.0.2
      role: leaf

# All the existing switches will be queried in the existing fabric
- name: Query all the switches in the fabric
  cisco.dcnm.dcnm_inventory:
    fabric: vxlan-fabric
    state: query # merged / deleted / overridden / query

# The following task will enable Bootstrap and DHCP on an existing fabric.
# Please note that only bootstrap and DHCP configs are present in the below example.
# You have to add other existing fabric configs to the task.
- name: Bootstrap and DHCP Configuration
  cisco.dcnm.dcnm_rest:
    method: PUT
    path: /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/vxlan-fabric
    json_data: '{"fabricId": "FABRIC-7","fabricName": "vxlan-fabric","id": 7,"nvPairs":{...,"BOOTSTRAP_ENABLE": true,"DHCP_ENABLE": true,"DHCP_IPV6_ENABLE": "DHCPv4","DHCP_START": "192.168.1.10", "DHCP_END": "192.168.1.20","MGMT_GW": "192.168.123.1","MGMT_PREFIX": "24",...},"templateName": "Easy_Fabric"}' # noqa

# The following switch will be Bootstrapped and merged into the existing fabric
- name: Poap switch Configuration
  cisco.dcnm.dcnm_inventory:
    fabric: vxlan-fabric
    state: merged # Only 2 options supported merged/query for poap config
    config:
    # All the values below are mandatory if poap configuration is being done - state is merged
    - seed_ip: 192.168.0.5
      user_name: switch_username
      password: switch_password
      role: border_gateway
      poap:
        - serial_number: 2A3BCDEFJKL
          model: 'N9K-C9300v'
          version: '9.3(7)'
          hostname: 'POAP_SWITCH'
          image_policy: "poap_image_policy"
          config_data:
            modulesModel: [N9K-X9364v, N9K-vSUP]
            gateway: 192.168.0.1/24

# The following switch will be Pre-provisioned and merged into the existing fabric
- name: Pre-provision switch Configuration
  cisco.dcnm.dcnm_inventory:
    fabric: vxlan-fabric
    state: merged # Only 2 options supported merged/query for poap config
    config:
    # All the values below are mandatory if poap configuration is being done - state is merged
    - seed_ip: 192.168.0.4
      user_name: switch_username
      password: switch_password
      role: border
      poap:
        - preprovision_serial: 1A2BCDEFGHI
          model: 'N9K-C9300v'
          version: '9.3(7)'
          hostname: 'PREPRO_SWITCH'
          image_policy: "prepro_image_policy"
          config_data:
            modulesModel: [N9K-X9364v, N9K-vSUP]
            gateway: 192.168.0.1/24

- name: Poap, Pre-provision and existing switch Configuration
  cisco.dcnm.dcnm_inventory:
    fabric: vxlan-fabric
    state: merged # Only 2 options supported merged/query for poap config
    config:
    - seed_ip: 192.168.0.2
      user_name: switch_username
      password: switch_password
      role: border_gateway
      poap:
        - serial_number: 2A3BCDEFGHI
          model: 'N9K-C9300v'
          version: '9.3(7)'
          hostname: 'POAP_SWITCH'
          image_policy: "poap_image_policy"
          config_data:
            modulesModel: [N9K-X9364v, N9K-vSUP]
            gateway: 192.168.0.1/24
    - seed_ip: 192.168.0.3
      user_name: switch_username
      password: switch_password
      auth_proto: MD5
      max_hops: 0
      preserve_config: False
      role: spine
    - seed_ip: 192.168.0.4
      user_name: switch_username
      password: switch_password
      role: border
      poap:
        - preprovision_serial: 1A2BCDEFGHI
          model: 'N9K-C9300v'
          version: '9.3(7)'
          hostname: 'PREPRO_SWITCH'
          image_policy: "prepro_image_policy"
          config_data:
            modulesModel: [N9K-X9364v, N9K-vSUP]
            gateway: 192.168.0.1/24

# The following pre-provisioned switch will be swapped with actual switch in the existing fabric
# No Need to provide any other parameters for swap operation as bootstrap will inherit the preprovision configs
# If other parameters are provided it will be overidden with preprovision switch configs
# This swap feature is supported only in NDFC and not on DCNM 11.x versions
- name: Pre-provision switch Configuration
  cisco.dcnm.dcnm_inventory:
    fabric: vxlan-fabric
    state: merged # Only 2 options supported merged/query for poap config
    config:
    # All the values below are mandatory if poap configuration is being done - state is merged
    - seed_ip: 192.168.0.4
      user_name: switch_username
      password: switch_password
      role: border
      poap:
        - preprovision_serial: 1A2BCDEFGHI
          serial_number: 2A3BCDEFGHI

# All the existing switches along with available Bootstrap(POAP)
# will be queried in the existing fabric
- name: Query all the switches in the fabric
  cisco.dcnm.dcnm_inventory:
    fabric: vxlan-fabric
    state: query # merged / query
    query_poap: True

# The following switch which is part of fabric will be replaced with a new switch
# with same configurations through RMA.
# Please note that the existing switch should be configured in maintenance mode and in shutdown state
- name: RMA switch Configuration
  cisco.dcnm.dcnm_inventory:
    fabric: vxlan-fabric
    state: merged # Only merged is supported for rma config
    config:
    - seed_ip: 192.168.0.4
      user_name: switch_username
      password: switch_password
      rma:
        - serial_number: 2A3BCDEFJKL
          old_serial: 2A3BCDEFGHI
          model: 'N9K-C9300v'
          version: '9.3(7)'
          image_policy: "rma_image_policy"
          config_data:
            modulesModel: [N9K-X9364v, N9K-vSUP]
            gateway: 192.168.0.1/24
"""

import time
import copy
import json
import re
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
    validate_list_of_dicts,
    dcnm_get_ip_addr_info,
    dcnm_version_supported,
    get_fabric_details,
    get_fabric_inventory_details,
    get_ip_sn_dict,
)


class DcnmInventory:
    def __init__(self, module):
        self.switches = {}
        self.module = module
        self.params = module.params
        self.fabric = module.params["fabric"]
        self.config = module.params.get("config")
        self.check_mode = False
        self.validated = []
        self.have_create = []
        self.want_create = []
        self.want_create_poap = []
        self.want_create_rma = []
        self.diff_create = []
        self.diff_save = {}
        self.diff_delete = {}
        self.query = []
        self.node_migration = False
        self.nd_prefix = "/appcenter/cisco/ndfc/api/v1/lan-fabric"
        self.switch_snos = []

        self.result = dict(changed=False, diff=[], response=[])

        self.controller_version = dcnm_version_supported(self.module)
        self.fabric_details = get_fabric_details(self.module, self.fabric)
        self.inventory_data = get_fabric_inventory_details(
            self.module, self.fabric
        )
        self.ip_sn, self.hn_sn = get_ip_sn_dict(self.inventory_data)

        self.nd = True if self.controller_version >= 12 else False

    def discover_poap_params(self, poap_upd, poap):

        for have_c in self.have_create:
            # Idempotence - Bootstrap but already in inventory
            if poap_upd["serialNumber"]:
                if (
                    poap_upd["ipAddress"] == have_c["switches"][0]["ipaddr"]
                    and poap_upd["serialNumber"] == have_c["switches"][0]["serialNumber"]
                ):
                    return {}

            # Idempotence - Preprovision but already in inventory
            if poap_upd["preprovisionSerial"] and not poap_upd["serialNumber"]:
                if (
                    poap_upd["ipAddress"] == have_c["switches"][0]["ipaddr"]
                ):
                    return {}

        # Preprovision case
        if poap_upd["preprovisionSerial"] and not poap_upd["serialNumber"]:
            return poap_upd

        method = "GET"
        path = "/rest/control/fabrics/{0}/inventory/poap".format(
            self.fabric
        )
        if self.nd:
            path = self.nd_prefix + path
        response = dcnm_send(self.module, method, path)
        self.result["response"].append(response)
        fail, self.result["changed"] = self.handle_response(response, "query")

        if fail:
            self.module.fail_json(msg=response)

        if "DATA" in response:
            for resp in response["DATA"]:
                if (resp["serialNumber"] == poap["serial_number"]):
                    if self.nd:
                        poap_upd.update({"publicKey": resp["publicKey"]})
                        poap_upd.update({"reAdd": resp["reAdd"]})
                        poap_upd.update({"fingerprint": resp["fingerprint"]})
                        if poap["image_policy"]:
                            poap_upd.update({"imagePolicy": poap["image_policy"]})
                        else:
                            poap_upd.update({"imagePolicy": ""})
                        # poap_upd.update({"role": "leaf"})
                    return poap_upd

        msg = "Specified switch {0}".format(
            poap["serial_number"] + " is not listed in bootstrap devices or inventory. " +
            "If you are trying to pre-provision, please set " +
            "'preprovision_serial' instead of 'serial_number' in your task")

        self.module.fail_json(msg)

    def update_poap_params(self, inv, poap):

        s_ip = "None"
        if inv["seed_ip"]:
            s_ip = dcnm_get_ip_addr_info(self.module, inv["seed_ip"], None, None)

        state = self.params["state"]

        if state == "merged":
            poap_upd = {
                "ipAddress": s_ip,
                "discoveryAuthProtocol": "0",
                "password": inv["password"],
                "hostname": poap["hostname"],
                "model": poap["model"],
                "serialNumber": poap["serial_number"],
                "version": poap["version"],
                "data": json.dumps(poap["config_data"]),
                "role": inv["role"].replace(" ", "_"),
                "preprovisionSerial": poap["preprovision_serial"],
            }

            # Add discovery credentials if set in the playbook
            if poap.get("discovery_username"):
                poap_upd['discoveryUsername'] = poap["discovery_username"]
                poap_upd['discoveryPassword'] = poap["discovery_password"]

            poap_upd = self.discover_poap_params(poap_upd, poap)

            if poap_upd.get("serialNumber"):
                self.switch_snos.append(poap_upd["serialNumber"])

        return poap_upd

    def discover_rma_params(self, rma_upd, rma):

        method = "GET"
        path = "/rest/control/fabrics/{0}/inventory/poap".format(
            self.fabric
        )
        if self.nd:
            path = self.nd_prefix + path
        response = dcnm_send(self.module, method, path)
        self.result["response"].append(response)
        fail, self.result["changed"] = self.handle_response(response, "query")

        if fail:
            self.module.fail_json(msg=response)

        if "DATA" in response:
            for resp in response["DATA"]:
                if (resp["serialNumber"] == rma["serial_number"]):
                    if self.nd:
                        rma_upd.update({"publicKey": resp["publicKey"]})
                        if rma["image_policy"]:
                            rma_upd.update({"imagePolicy": rma["image_policy"]})
                        else:
                            rma_upd.update({"imagePolicy": ""})
                    rma_upd.update({"hostname": list(self.hn_sn.keys())[list(self.hn_sn.values()).index(rma_upd["oldSerialNumber"])]})
                    return rma_upd

        msg = "Specified switch {0}".format(
            rma["serial_number"] + " is not listed in bootstrap devices.")

        self.module.fail_json(msg)

    def update_rma_params(self, inv, rma):

        s_ip = "None"
        if inv["seed_ip"]:
            s_ip = dcnm_get_ip_addr_info(self.module, inv["seed_ip"], None, None)

        state = self.params["state"]

        if state == "merged":
            rma_upd = {
                "ipAddress": s_ip,
                "discoveryAuthProtocol": "0",
                "password": inv["password"],
                "model": rma["model"],
                "newSerialNumber": rma["serial_number"],
                "oldSerialNumber": rma["old_serial"],
                "version": rma["version"],
                "data": json.dumps(rma["config_data"]),
            }

            # Add discovery credentials if set in the playbook
            if rma.get("discovery_username"):
                rma_upd['discoveryUsername'] = rma["discovery_username"]
                rma_upd['discoveryPassword'] = rma["discovery_password"]

            rma_upd = self.discover_rma_params(rma_upd, rma)

            if rma_upd.get("newSerialNumber"):
                self.switch_snos.append(rma_upd["newSerialNumber"])

        return rma_upd

    def update_discover_params(self, inv):

        # with the inv parameters perform the test-reachability (discover)
        method = "POST"
        path = "/rest/control/fabrics/{0}/inventory/test-reachability".format(
            self.fabric
        )
        if self.nd:
            path = self.nd_prefix + path
        response = dcnm_send(self.module, method, path, json.dumps(inv))
        self.result["response"].append(response)
        fail, self.result["changed"] = self.handle_response(response, "create")

        if fail:
            self.module.fail_json(msg=response)

        if "DATA" in response:
            switch = []
            for sw in response["DATA"]:
                if inv["seedIP"] == sw["ipaddr"]:
                    switch.append(sw)
                    return switch
            return 0
        else:
            return 0

    def update_create_params(self, inv):

        s_ip = "None"
        if inv["seed_ip"]:
            s_ip = dcnm_get_ip_addr_info(self.module, inv["seed_ip"], None, None)

        state = self.params["state"]

        if state == "deleted":
            inv_upd = {
                "seedIP": s_ip,
            }
        elif state == "query":
            inv_upd = {"seedIP": s_ip, "role": inv["role"].replace(" ", "_")}
        else:
            if inv["auth_proto"] == "MD5":
                pro = 0
            elif inv["auth_proto"] == "SHA":
                pro = 1
            elif inv["auth_proto"] == "MD5_DES":
                pro = 2
            elif inv["auth_proto"] == "MD5_AES":
                pro = 3
            elif inv["auth_proto"] == "SHA_DES":
                pro = 4
            elif inv["auth_proto"] == "SHA_AES":
                pro = 5
            else:
                pro = 0

            inv_upd = {
                "seedIP": s_ip,
                "snmpV3AuthProtocol": pro,
                "username": inv["user_name"],
                "password": inv["password"],
                "maxHops": 0,
                "cdpSecondTimeout": "5",
                "role": inv["role"].replace(" ", "_"),
                "preserveConfig": inv["preserve_config"],
            }

            resp = self.update_discover_params(inv_upd)

            inv_upd["switches"] = resp

        return inv_upd

    def get_have(self):

        method = "GET"
        path = "/rest/control/fabrics/{0}/inventory".format(self.fabric)
        if self.nd:
            path = self.nd_prefix + path
        inv_objects = dcnm_send(self.module, method, path)

        missing_fabric, not_ok = self.handle_response(inv_objects, "query_dcnm")

        if (
            inv_objects.get("ERROR") == "Not Found"
            and inv_objects.get("RETURN_CODE") == 404
        ):
            self.module.fail_json(
                msg="Fabric {0} not present on DCNM".format(self.fabric)
            )
            return

        if missing_fabric or not_ok:
            msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find inventories under fabric: {0}".format(self.fabric)
            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

        if not inv_objects["DATA"]:
            return

        have_switch = []

        for inv in inv_objects["DATA"]:
            get_switch = {}
            get_switch.update({"sysName": inv["logicalName"]})
            get_switch.update({"serialNumber": inv["serialNumber"]})
            get_switch.update({"ipaddr": inv["ipAddress"]})
            get_switch.update({"platform": inv["nonMdsModel"]})
            get_switch.update({"version": inv["release"]})
            get_switch.update(
                {"deviceIndex": inv["logicalName"] + "(" + inv["serialNumber"] + ")"}
            )
            get_switch.update({"role": inv["switchRole"].replace(" ", "_")})
            get_switch.update({"mode": inv["mode"]})
            get_switch.update({"serialNumber": inv["serialNumber"]})
            switchdict = {}
            switchlst = []
            switchlst.append(get_switch)
            switchdict["switches"] = switchlst
            have_switch.append(switchdict)

        self.have_create = have_switch

    def get_want(self):

        want_create = []
        want_create_poap = []
        want_create_rma = []

        if not self.config:
            return

        for inv in self.validated:
            if inv.get("poap"):
                create_poap = self.update_poap_params(inv, inv["poap"][0])
                if create_poap:
                    want_create_poap.append(create_poap)
            elif inv.get("rma"):
                create_rma = self.update_rma_params(inv, inv["rma"][0])
                if create_rma:
                    want_create_rma.append(create_rma)
            else:
                want_create.append(self.update_create_params(inv))

        if not want_create and not want_create_poap and not want_create_rma:
            return

        self.want_create = want_create
        self.want_create_poap = want_create_poap
        self.want_create_rma = want_create_rma

    def get_diff_override(self):

        self.get_diff_replace()
        self.get_diff_replace_delete()

        diff_create = self.diff_create
        diff_delete = self.diff_delete

        self.diff_create = diff_create
        self.diff_delete = diff_delete

    def get_diff_replace(self):

        self.get_diff_merge()
        diff_create = self.diff_create

        self.diff_create = diff_create

    def get_diff_replace_delete(self):

        diff_delete = []

        def have_in_want(have_c):
            match_found = False
            for want_c in self.want_create:
                match = re.search(r"\S+\((\S+)\)", want_c["switches"][0]["deviceIndex"])
                if match is None:
                    continue
                want_serial_num = match.groups()[0]
                if have_c["switches"][0]["serialNumber"] == want_serial_num:
                    if (
                        have_c["switches"][0]["ipaddr"]
                        == want_c["switches"][0]["ipaddr"]
                        and have_c["switches"][0]["platform"]
                        == want_c["switches"][0]["platform"]
                        and have_c["switches"][0]["version"]
                        == want_c["switches"][0]["version"]
                        and have_c["switches"][0]["sysName"]
                        == want_c["switches"][0]["sysName"]
                        and have_c["switches"][0]["role"] == want_c["role"]
                    ):
                        match_found = True

            return match_found

        for have_c in self.have_create:
            if have_in_want(have_c):
                continue

            diff_delete.append(have_c["switches"][0]["serialNumber"])

        self.diff_delete = diff_delete

    def get_diff_delete(self):

        diff_delete = []

        if self.config:
            for want_c in self.want_create:
                for have_c in self.have_create:
                    if have_c["switches"][0]["ipaddr"] == want_c["seedIP"]:
                        diff_delete.append(have_c["switches"][0]["serialNumber"])
                        continue

        else:
            for have_c in self.have_create:
                diff_delete.append(have_c["switches"][0]["serialNumber"])

        self.diff_delete = diff_delete

    def get_diff_merge(self):

        diff_create = []

        for want_c in self.want_create:
            found = False
            match = re.search(r"\S+\((\S+)\)", want_c["switches"][0]["deviceIndex"])
            if match is None:
                msg = "Switch with IP {0} is not reachable or is not a valid IP".format(want_c["seedIP"])
                self.module.fail_json(msg=msg)
            serial_num = match.groups()[0]
            for have_c in self.have_create:
                if (
                    want_c["switches"][0]["ipaddr"] == have_c["switches"][0]["ipaddr"]
                    and serial_num == have_c["switches"][0]["serialNumber"]
                    and want_c["switches"][0]["platform"]
                    == have_c["switches"][0]["platform"]
                    and want_c["switches"][0]["version"]
                    == have_c["switches"][0]["version"]
                    and want_c["switches"][0]["sysName"]
                    == have_c["switches"][0]["sysName"]
                    and want_c["role"] == have_c["switches"][0]["role"]
                ):

                    found = True

                    if have_c["switches"][0]["mode"] == "Migration":
                        # Switch is already discovered using DCNM GUI
                        # Perform assign-role/config-save/config-deploy
                        self.switch_snos.append(serial_num)
                        self.node_migration = True
                        diff_create.append(want_c)
                        self.diff_create = diff_create

                        # Assign Role
                        self.assign_role()

                        for check in range(1, 300):
                            if not self.all_switches_ok():
                                time.sleep(5)
                            else:
                                break

                        # Config-save all switches
                        if self.params["save"]:
                            self.config_save()

                        # Config-deploy all switches
                        if self.params["deploy"]:
                            self.config_deploy()

            if not found:
                self.switch_snos.append(serial_num)
                diff_create.append(want_c)

        self.diff_create = diff_create

    def validate_input(self):
        """Parse the playbook values, validate to param specs."""

        state = self.params["state"]
        query_poap = self.params["query_poap"]

        if query_poap is True and state != "query":
            msg = "query_poap: should not be set 'True' for state {0}".format(
                state
            )
            self.module.fail_json(msg=msg)

        if state == "merged" or state == "overridden":

            inv_spec = dict(
                seed_ip=dict(required=True, type="str"),
                auth_proto=dict(
                    type="str",
                    choices=["MD5", "SHA", "MD5_DES", "MD5_AES", "SHA_DES", "SHA_AES"],
                    default="MD5",
                ),
                user_name=dict(required=True, type="str", no_log=True, length_max=32),
                password=dict(required=True, type="str", no_log=True, length_max=32),
                max_hops=dict(type="int", default=0),
                role=dict(
                    type="str",
                    choices=[
                        "leaf",
                        "spine",
                        "border",
                        "border_spine",
                        "border_gateway",
                        "border_gateway_spine",
                        "super_spine",
                        "border_super_spine",
                        "border_gateway_super_spine",
                        "access",
                        "aggregation",
                        "edge_router",
                        "core_router",
                        "tor"
                    ],
                    default="leaf",
                ),
                preserve_config=dict(type="bool", default=False),
                poap=dict(type="list"),
                rma=dict(type="list"),
            )

            poap_spec = dict(
                discovery_username=dict(type="str", no_log=True, length_max=32),
                discovery_password=dict(type="str", no_log=True, length_max=32),
                serial_number=dict(type="str", default=""),
                preprovision_serial=dict(type="str", default=""),
                model=dict(type="str", default=""),
                version=dict(type="str", default=""),
                hostname=dict(type="str", default=""),
                config_data=dict(type="dict", default={}),
                image_policy=dict(type="str", default="")
            )

            rma_spec = dict(
                discovery_username=dict(type="str", no_log=True, length_max=32),
                discovery_password=dict(type="str", no_log=True, length_max=32),
                serial_number=dict(type="str", required=True),
                old_serial=dict(type="str", required=True),
                model=dict(type="str", required=True),
                version=dict(type="str", required=True),
                config_data=dict(type="dict", required=True),
                image_policy=dict(type="str", default="")
            )

            msg = None
            if self.config:
                for inv in self.config:
                    if (
                        "seed_ip" not in inv
                        or "user_name" not in inv
                        or "password" not in inv
                    ):
                        msg = "seed ip/user name and password are mandatory under inventory parameters"
                        break
                    if "poap" in inv:
                        if state != "merged":
                            msg = "'merged' and 'query' are only supported states for POAP"
                        if inv["user_name"] != "admin":
                            msg = "user_name must be 'admin' for POAP"
                        if inv["poap"][0].get("serial_number") is None and inv["poap"][0].get("preprovision_serial") is None:
                            msg = "Please provide 'serial_number' for bootstrap or 'preprovision_serial' for preprovision"
                        if ((inv["poap"][0].get("serial_number") and inv["poap"][0].get("preprovision_serial") is None) or
                           (inv["poap"][0].get("preprovision_serial") and inv["poap"][0].get("serial_number") is None)):
                            if (inv["poap"][0].get("model") is None or inv["poap"][0].get("version") is None or
                               inv["poap"][0].get("hostname") is None or not inv["poap"][0]["config_data"]):
                                msg = "model, version, hostname and config_data must be provided for {0}".format(
                                    "Preprovisioning/Bootstraping a switch"
                                )
                        if inv["poap"][0].get("serial_number") and inv["poap"][0].get("preprovision_serial") and not self.nd:
                            msg = "Serial number swap is not supported in DCNM version 11"
                        if inv["poap"][0].get("discovery_username"):
                            if inv["poap"][0].get("discovery_password") is None:
                                msg = "discovery_password must be set when discovery_username is specified"
                        if inv["poap"][0].get("discovery_password"):
                            if inv["poap"][0].get("discovery_username") is None:
                                msg = "discovery_username must be set when discovery_password is specified"

                    if "rma" in inv:
                        if state != "merged":
                            msg = "'merged' is only supported state for RMA"
                        if inv["user_name"] != "admin":
                            msg = "user_name must be 'admin' for RMA"
                        if inv["rma"][0].get("serial_number") is None or inv["rma"][0].get("old_serial") is None:
                            msg = "Please provide 'serial_number' and 'old_serial' for RMA"
                        if inv["rma"][0].get("discovery_username"):
                            if inv["rma"][0].get("discovery_password") is None:
                                msg = "discovery_password must be set when discovery_username is specified"
                        if inv["rma"][0].get("discovery_password"):
                            if inv["rma"][0].get("discovery_username") is None:
                                msg = "discovery_username must be set when discovery_password is specified"
                    if msg:
                        self.module.fail_json(msg=msg)
            else:
                if state == "merged":
                    msg = "config: element is mandatory for this state {0}".format(
                        state
                    )

            if msg:
                self.module.fail_json(msg=msg)

            if self.config:
                valid_inv, invalid_params = validate_list_of_dicts(
                    self.config, inv_spec, self.module
                )
                for inv in valid_inv:
                    if inv.get("poap"):
                        valid_poap, invalid_poap = validate_list_of_dicts(
                            inv["poap"], poap_spec, self.module
                        )
                        invalid_params.extend(invalid_poap)
                        inv["poap"] = valid_poap

                    if inv.get("rma"):
                        valid_rma, invalid_rma = validate_list_of_dicts(
                            inv["rma"], rma_spec, self.module
                        )
                        invalid_params.extend(invalid_rma)
                        inv["rma"] = valid_rma

                    self.validated.append(inv)

                if invalid_params:
                    msg = "Invalid parameters in playbook: {0}".format(
                        "\n".join(invalid_params)
                    )
                    self.module.fail_json(msg=msg)

        elif state == "deleted":

            inv_spec = dict(seed_ip=dict(required=True, type="str"))

            msg = None
            if self.config:
                for inv in self.config:
                    if "seed_ip" not in inv:
                        msg = "seed ip is mandatory under inventory parameters for switch deletion"
                    if "poap" in inv:
                        msg = "'merged' and 'query' are only supported states for POAP"
                    if "rma" in inv:
                        msg = "'merged' is the only supported state for RMA"

            if msg:
                self.module.fail_json(msg=msg)

            if self.config:
                valid_inv, invalid_params = validate_list_of_dicts(
                    self.config, inv_spec
                )
                for inv in valid_inv:
                    self.validated.append(inv)

                if invalid_params:
                    msg = "Invalid parameters in playbook: {0}".format(
                        "\n".join(invalid_params)
                    )
                    self.module.fail_json(msg=msg)

        else:

            inv_spec = dict(
                seed_ip=dict(type="str"),
                role=dict(
                    type="str",
                    choices=[
                        "leaf",
                        "spine",
                        "border",
                        "border_spine",
                        "border_gateway",
                        "border_gateway_spine",
                        "super_spine",
                        "border_super_spine",
                        "border_gateway_super_spine",
                        "access",
                        "aggregation",
                        "edge_router",
                        "core_router",
                        "tor",
                        "None",
                    ],
                    default="None",
                ),
            )

            if self.config:
                valid_inv, invalid_params = validate_list_of_dicts(
                    self.config, inv_spec
                )
                for inv in valid_inv:
                    self.validated.append(inv)

                if invalid_params:
                    msg = "Invalid parameters in playbook: {0}".format(
                        "\n".join(invalid_params)
                    )
                    self.module.fail_json(msg=msg)

    def import_switches(self):

        method = "POST"
        path = "/rest/control/fabrics/{0}".format(self.fabric)
        if self.nd:
            path = self.nd_prefix + path
        # create_path = path + '/inventory/discover?gfBlockingCall=true'
        create_path = path + "/inventory/discover"

        if self.diff_create:
            for create in self.diff_create:
                import_response = dcnm_send(
                    self.module, method, create_path, json.dumps(create)
                )
                self.result["response"].append(import_response)
                fail, self.result["changed"] = self.handle_response(
                    import_response, "create"
                )
                if fail:
                    self.failure(import_response)

    def rediscover_switch(self, serial_num):

        method = "POST"
        path = "/rest/control/fabrics/{0}/inventory/rediscover/{1}".format(
            self.fabric, serial_num
        )
        if self.nd:
            path = self.nd_prefix + path
        response = dcnm_send(self.module, method, path)
        self.result["response"].append(response)
        fail, self.result["changed"] = self.handle_response(response, "create")
        if fail:
            self.failure(response)

    def rediscover_all_switches(self):

        # Get Fabric Inventory Details
        method = "GET"
        path = "/rest/control/fabrics/{0}/inventory".format(self.fabric)
        if self.nd:
            path = self.nd_prefix + path
        get_inv = dcnm_send(self.module, method, path)
        missing_fabric, not_ok = self.handle_response(get_inv, "query_dcnm")

        if missing_fabric or not_ok:
            msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find inventories under fabric: {0}".format(self.fabric)
            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

        if not get_inv.get("DATA"):
            return

        def ready_to_continue(inv_data):
            # This is a helper function to wait for certain events to complete
            # as part of the switch rediscovery step before moving on.

            # Check # 1
            # First check migration mode.  Switches will enter migration mode
            # even if the GRFIELD_DEBUG_FLAG is enabled so this needs to be
            # checked first.
            for switch in inv_data.get("DATA"):
                for snos in self.switch_snos:
                    if snos == switch["serialNumber"] and switch["mode"].lower() == "migration":
                        # At least one switch is still in migration mode
                        # so not ready to continue
                        return False

            # Check # 2
            # The fabric has a setting to prevent reload for greenfield
            # deployments.  If this is enabled we can skip check 3 and just return True
            if self.fabric_details["nvPairs"]["GRFIELD_DEBUG_FLAG"].lower() == "enable":
                return True

            # Check # 3
            # If we get to this check that means the GRFIELD_DEBUG_FLAG is disabled
            # and each switch will go through a realod sequence.  Unfortunately
            # the switch will show up as managable for a period of time before it
            # moves to unmanagable but we need to wait for this to allow enough time
            # for the reload to completed.
            for switch in inv_data.get("DATA"):
                for snos in self.switch_snos:
                    if snos == switch["serialNumber"] and not switch["managable"]:
                        # We found our first switch that changed state to
                        # unmanageable because it's reloading.  Now we can
                        # continue
                        return True

            # We still have not detected a switch is reloading so return False
            return False

        def switches_managable(inv_data):
            managable = True
            for switch in inv_data["DATA"]:
                for snos in self.switch_snos:
                    if snos == switch["serialNumber"] and not switch["managable"]:
                        managable = False
                        break

            return managable

        # It can take a while to rediscover switches if they are reloading
        # while importing them into the fabric.
        attempt = 1
        total_attempts = 300
        # If all switches to be added have preserve_config set to true then
        # we don't need to loop.
        all_brownfield_switches = True
        for switch in self.config:
            if not switch.get("preserve_config", True):
                all_brownfield_switches = False

        while attempt < total_attempts and not all_brownfield_switches and self.switch_snos:

            # Don't error out.  We might miss the status change so worst case
            # scenario is that we loop 300 times and then bail out.
            if attempt == 1:
                if (
                    self.fabric_details["nvPairs"]["GRFIELD_DEBUG_FLAG"].lower()
                    == "enable"
                ):
                    # It may take a few seconds for switches to enter migration mode when
                    # this flag is set.  Give it a few seconds.
                    time.sleep(20)
            get_inv = dcnm_send(self.module, method, path)
            if not ready_to_continue(get_inv):
                time.sleep(5)
                attempt += 1
                continue

            break

        attempt = 1
        total_attempts = 300

        while attempt < total_attempts:
            if attempt == total_attempts:
                msg = "Failed to rediscover switches after {0} attempts".format(
                    total_attempts
                )
                self.module.fail_json(msg=msg)
            get_inv = dcnm_send(self.module, method, path)
            if not switches_managable(get_inv):
                time.sleep(5)
                attempt += 1
                continue

            break

        for inv in get_inv["DATA"]:
            for snos in self.switch_snos:
                if snos == inv["serialNumber"]:
                    self.rediscover_switch(inv["serialNumber"])

    def all_switches_ok(self):

        all_ok = True
        # Get Fabric Inventory Details
        method = "GET"
        path = "/rest/control/fabrics/{0}/inventory".format(self.fabric)
        if self.nd:
            path = self.nd_prefix + path
        get_inv = dcnm_send(self.module, method, path)
        missing_fabric, not_ok = self.handle_response(get_inv, "query_dcnm")

        if missing_fabric or not_ok:
            msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find inventories under fabric: {0}".format(self.fabric)
            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

        for inv in get_inv["DATA"]:
            for snos in self.switch_snos:
                if snos == inv["serialNumber"] and inv["status"] != "ok":
                    all_ok = False
                    self.rediscover_switch(inv["serialNumber"])

        # If the switches added through discovery itself has issues, then there is no
        # point in checking rma switch status, so return false here.
        if not all_ok:
            return all_ok

        # This is a special handling for RMA insertion, in case of RMA the new serial number
        # will not be part of inventory data until the new switch comes up fully. So during RMA
        # check for the new serial number in the inventory data, if not present return false
        if self.want_create_rma:
            for rma in self.want_create_rma:
                if not any(inv["serialNumber"] == rma["newSerialNumber"] for inv in get_inv["DATA"]):
                    return False

        return all_ok

    def set_lancred_switch(self, set_lan):

        method = "POST"
        path = "/fm/fmrest/lanConfig/saveSwitchCredentials"
        if self.nd:
            path = self.nd_prefix + "/" + path[6:]

        response = dcnm_send(self.module, method, path, urlencode(set_lan))
        self.result["response"].append(response)
        fail, self.result["changed"] = self.handle_response(response, "create")
        if fail:
            self.failure(response)

    def lancred_all_switches(self):

        # Get Fabric Inventory Details
        method = "GET"
        path = "/fm/fmrest/lanConfig/getLanSwitchCredentials"
        if self.nd:
            path = self.nd_prefix + "/" + path[6:]
            # lan_path = '/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/lanConfig/getLanSwitchCredentials'
        get_lan = dcnm_send(self.module, method, path)
        missing_fabric, not_ok = self.handle_response(get_lan, "query_dcnm")

        if missing_fabric or not_ok:
            msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
            msg2 = "Unable to getLanSwitchCredentials under fabric: {0}".format(
                self.fabric
            )
            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

        if not get_lan.get("DATA"):
            return

        for create in self.want_create:
            for lan in get_lan["DATA"]:
                if not lan["switchDbID"]:
                    msg = "Unable to SWITCHDBID using getLanSwitchCredentials under fabric: {0}".format(
                        self.fabric
                    )
                    self.module.fail_json(msg=msg)
                if lan["ipAddress"] == create["switches"][0]["ipaddr"]:
                    set_lan = {
                        "switchIds": lan["switchDbID"],
                        "userName": create["username"],
                        "password": create["password"],
                        "v3Protocol": "0",
                    }
                    # TODO: Remove this check later.. should work on ND but does not for some reason
                    if not self.nd:
                        self.set_lancred_switch(set_lan)

    def assign_role(self):

        method = "GET"
        path = "/rest/control/fabrics/{0}/inventory".format(self.fabric)
        if self.nd:
            path = self.nd_prefix + path
        get_role = dcnm_send(self.module, method, path)
        missing_fabric, not_ok = self.handle_response(get_role, "query_dcnm")

        if missing_fabric or not_ok:
            msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find inventories under fabric: {0}".format(self.fabric)
            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

        if not get_role.get("DATA"):
            return

        for create in self.diff_create:
            for role in get_role["DATA"]:
                if not role["switchDbID"]:
                    msg = "Unable to get SWITCHDBID using getLanSwitchCredentials under fabric: {0}".format(
                        self.fabric
                    )
                    self.module.fail_json(msg=msg)
                if role["ipAddress"] == create["switches"][0]["ipaddr"]:
                    method = "PUT"
                    path = "/fm/fmrest/topology/role/{0}?newRole={1}".format(
                        role["switchDbID"], create["role"].replace("_", "%20")
                    )
                    if self.nd:
                        path = self.nd_prefix + "/" + path[6:]
                    response = dcnm_send(self.module, method, path)
                    self.result["response"].append(response)
                    fail, self.result["changed"] = self.handle_response(
                        response, "create"
                    )
                    if fail:
                        self.failure(response)

        for create in self.want_create_poap:
            for role in get_role["DATA"]:
                if not role["switchDbID"]:
                    msg = "Unable to get SWITCHDBID using getLanSwitchCredentials under fabric: {0}".format(
                        self.fabric
                    )
                    self.module.fail_json(msg=msg)
                if role["ipAddress"] == create["ipAddress"]:
                    method = "PUT"
                    path = "/fm/fmrest/topology/role/{0}?newRole={1}".format(
                        role["switchDbID"], create["role"].replace("_", "%20")
                    )
                    if self.nd:
                        path = self.nd_prefix + "/" + path[6:]
                    response = dcnm_send(self.module, method, path)
                    self.result["response"].append(response)
                    fail, self.result["changed"] = self.handle_response(
                        response, "create"
                    )
                    if fail:
                        self.failure(response)

    def config_save(self):

        success = False
        no_of_tries = 3

        # NDFC/DCNM return error when we config-save a fabric with just Pre-provisioned switches.
        if not self.want_create:
            if not self.switch_snos:
                return

        for x in range(0, no_of_tries):
            # Get Fabric ID
            method = "GET"
            path = "/rest/control/fabrics/{0}".format(self.fabric)
            if self.nd:
                path = self.nd_prefix + path
            get_fid = dcnm_send(self.module, method, path)
            missing_fabric, not_ok = self.handle_response(get_fid, "create_dcnm")

            if not get_fid.get("DATA"):
                return

            if not get_fid["DATA"]["id"]:
                msg = "Unable to find id for fabric: {0}".format(self.fabric)
                self.module.fail_json(msg=msg)

            fabric_id = get_fid["DATA"]["id"]

            # config-save
            method = "POST"
            path = "/rest/control/fabrics/{0}".format(self.fabric)
            if self.nd:
                path = self.nd_prefix + path
            save_path = path + "/config-save"
            response = dcnm_send(self.module, method, save_path)
            self.result["response"].append(response)
            fail, self.result["changed"] = self.handle_response(response, "create")
            if fail:
                self.failure(response)

            if response["RETURN_CODE"] != 200:

                # Get Fabric Errors
                method = "GET"
                path = "/rest/control/fabrics/{0}/errors".format(fabric_id)
                if self.nd:
                    path = self.nd_prefix + path
                get_fiderr = dcnm_send(self.module, method, path)
                missing_fabric, not_ok = self.handle_response(get_fiderr, "query_dcnm")

                if missing_fabric or not_ok:
                    msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
                    msg2 = "Could not get any fabric errors for fabric: {0}".format(
                        self.fabric
                    )
                    self.module.fail_json(msg=msg1 if missing_fabric else msg2)

            else:
                time.sleep(5)
                success = True
                break

            if not success and x in range(0, no_of_tries - 1):
                time.sleep(600)

    def config_deploy(self):

        # config-deploy
        method = "POST"
        path = "/rest/control/fabrics/{0}".format(self.fabric)
        if self.nd:
            path = self.nd_prefix + path
        path = path + "/config-deploy/"

        switches = ",".join(self.switch_snos)
        if switches:
            path = path + switches
            response = dcnm_send(self.module, method, path)
            self.result["response"].append(response)
            fail, self.result["changed"] = self.handle_response(response, "create")

            if fail:
                self.failure(response)

    def delete_switch(self):

        if self.diff_delete:
            method = "DELETE"
            for sn in self.diff_delete:
                path = "/rest/control/fabrics/{0}/switches/{1}".format(self.fabric, sn)
                if self.nd:
                    path = self.nd_prefix + path
                response = dcnm_send(self.module, method, path)
                self.result["response"].append(response)
                fail, self.result["changed"] = self.handle_response(response, "delete")

                if fail:
                    self.failure(response)

    def get_diff_query(self):

        query = []
        query_poap = self.params["query_poap"]

        method = "GET"
        path = "/rest/control/fabrics/{0}/inventory".format(self.fabric)
        if self.nd:
            path = self.nd_prefix + path
        inv_objects = dcnm_send(self.module, method, path)
        missing_fabric, not_ok = self.handle_response(inv_objects, "query_dcnm")

        if (
            inv_objects.get("ERROR") == "Not Found"
            and inv_objects.get("RETURN_CODE") == 404
        ):
            self.module.fail_json(
                msg="Fabric {0} not present on DCNM".format(self.fabric)
            )
            return

        if missing_fabric or not_ok:
            msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find inventories under fabric: {0}".format(self.fabric)
            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

        if not inv_objects["DATA"] and not query_poap:
            return

        if self.config and inv_objects["DATA"]:
            for want_c in self.want_create:
                for inv in inv_objects["DATA"]:
                    if want_c["role"] == "None" and want_c["seedIP"] != "None":
                        if want_c["seedIP"] == inv["ipAddress"]:
                            query.append(inv)
                            continue
                    elif want_c["role"] != "None" and want_c["seedIP"] == "None":
                        if want_c["role"] == inv["switchRole"].replace(" ", "_"):
                            query.append(inv)
                            continue
                    else:
                        if want_c["seedIP"] == inv["ipAddress"] and want_c[
                            "role"
                        ] == inv["switchRole"].replace(" ", "_"):
                            query.append(inv)
                            continue
        else:
            for inv in inv_objects["DATA"]:
                query.append(inv)

        if query_poap is True:
            method = "GET"
            path = "/rest/control/fabrics/{0}/inventory/poap".format(self.fabric)
            if self.nd:
                path = self.nd_prefix + path
            poap_objects = dcnm_send(self.module, method, path)
            missing_fabric, not_ok = self.handle_response(poap_objects, "query_dcnm")

            if (
                poap_objects.get("ERROR") == "Not Found"
                and poap_objects.get("RETURN_CODE") == 404
            ):
                self.module.fail_json(
                    msg="Fabric {0} not present on DCNM".format(self.fabric)
                )
                return

            if missing_fabric or not_ok:
                msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
                msg2 = "Unable to find inventories under fabric: {0}".format(self.fabric)
                self.module.fail_json(msg=msg1 if missing_fabric else msg2)

            if poap_objects["DATA"]:
                for poap in poap_objects["DATA"]:
                    query.append(poap)

        self.query = query

    def swap_serial(self, poap):

        method = "POST"
        swap_path = "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{0}/swapSN/{1}/{2}".format(
                    self.fabric, poap["preprovisionSerial"], poap["serialNumber"]
        )
        response = dcnm_send(self.module, method, swap_path)
        self.result["response"].append(response)
        fail, self.result["changed"] = self.handle_response(response, "create_poap")

        if fail:
            self.failure(response)

        method = "GET"
        path = "/rest/control/fabrics/{0}/inventory/poap".format(
            self.fabric
        )
        if self.nd:
            path = self.nd_prefix + path
        response = dcnm_send(self.module, method, path)
        self.result["response"].append(response)
        fail, self.result["changed"] = self.handle_response(response, "query")

        if fail:
            self.module.fail_json(msg=response)

        if "DATA" in response:
            for resp in response["DATA"]:
                if (resp["serialNumber"] == poap["serialNumber"]):
                    resp.update({"password": poap["password"]})
                    resp.update({"discoveryAuthProtocol": "0"})
                    resp.pop("seedSwitchFlag")
                    return resp

        msg = "Specified switch {0}".format(
            poap["serial_number"] + " is not listed in bootstrap devices or inventory. " +
            "If you are trying to pre-provision, please set " +
            "'preprovision_serial' instead of 'serial_number' in your task")

        self.module.fail_json(msg=response)

    def poap_config(self):

        method = "POST"
        path = "/rest/control/fabrics/{0}/inventory/poap".format(self.fabric)
        if self.nd:
            path = self.nd_prefix + path
        if self.want_create_poap:
            poap_list = copy.deepcopy(self.want_create_poap)

            for i in range(len(poap_list)):
                poap_list[i].pop("role")
                if self.nd and poap_list[i]["serialNumber"] and poap_list[i]["preprovisionSerial"]:
                    poap_list[i] = self.swap_serial(poap_list[i])
                if not poap_list[i]["serialNumber"] and poap_list[i]["preprovisionSerial"]:
                    poap_list[i]["serialNumber"] = poap_list[i]["preprovisionSerial"]
                if "preprovisionSerial" in poap_list[i]:
                    poap_list[i].pop("preprovisionSerial")

            response = dcnm_send(self.module, method, path, json.dumps(poap_list))
            self.result["response"].append(response)
            fail, self.result["changed"] = self.handle_response(response, "create_poap")

            if fail:
                self.failure(response)

    def rma_config(self):

        method = "POST"
        path = "/rest/control/fabrics/{0}/rma".format(self.fabric)
        if self.nd:
            path = self.nd_prefix + path
        if self.want_create_rma:
            for rma in self.want_create_rma:
                response = dcnm_send(self.module, method, path, json.dumps(rma))
                self.result["response"].append(response)
                fail, self.result["changed"] = self.handle_response(response, "create_rma")

                if fail:
                    self.failure(response)

    def handle_response(self, res, op):

        fail = False
        changed = True

        if op == "query_dcnm":
            # This if blocks handles responses to the query APIs against DCNM.
            # Basically all GET operations.
            if res.get("ERROR") == "Not Found" and res["RETURN_CODE"] == 404:
                return True, False
            if res["RETURN_CODE"] != 200 or res["MESSAGE"] != "OK":
                return False, True
            return False, False

        # Responses to all other operations POST and PUT are handled here.
        if res.get("MESSAGE") != "OK":
            fail = True
            changed = False
            return fail, changed
        if res.get("ERROR"):
            fail = True
            changed = False

        return fail, changed

    def failure(self, resp):

        res = copy.deepcopy(resp)

        if not resp.get("DATA"):
            data = copy.deepcopy(resp.get("DATA"))
            if data.get("stackTrace"):
                data.update(
                    {"stackTrace": "Stack trace is hidden, use '-vvvvv' to print it"}
                )
                res.update({"DATA": data})

        self.module.fail_json(msg=res)


def main():
    """main entry point for module execution"""

    element_spec = dict(
        fabric=dict(required=True, type="str"),
        config=dict(required=False, type="list", elements="dict"),
        state=dict(
            default="merged", choices=["merged", "overridden", "deleted", "query"]
        ),
        query_poap=dict(type="bool", default=False),
        save=dict(type="bool", default=True),
        deploy=dict(type="bool", default=True),
    )

    module = AnsibleModule(argument_spec=element_spec, supports_check_mode=True)

    dcnm_inv = DcnmInventory(module)
    dcnm_inv.validate_input()
    dcnm_inv.get_have()
    dcnm_inv.get_want()

    if module.params["state"] == "merged":
        dcnm_inv.get_diff_merge()

    if module.params["state"] == "overridden":
        dcnm_inv.get_diff_override()

    if module.params["state"] == "deleted":
        dcnm_inv.get_diff_delete()

    if module.params["state"] == "query":
        dcnm_inv.get_diff_query()
        dcnm_inv.result["changed"] = False
        dcnm_inv.result["response"] = dcnm_inv.query

    if not dcnm_inv.diff_delete and module.params["state"] == "deleted":
        dcnm_inv.result["changed"] = False
        dcnm_inv.result[
            "response"
        ] = "The switch provided is not part of the fabric and cannot be deleted"

    if not dcnm_inv.diff_create and module.params["state"] == "merged" and not dcnm_inv.want_create_poap and not dcnm_inv.want_create_rma:
        dcnm_inv.result["changed"] = False
        dcnm_inv.result[
            "response"
        ] = "The switch provided is already part of the fabric and cannot be created again"

    if (
        not dcnm_inv.diff_create
        and not dcnm_inv.diff_delete
        and module.params["state"] == "overridden"
    ):
        dcnm_inv.result["changed"] = False
        dcnm_inv.result[
            "response"
        ] = "The switch provided is already part of the fabric and there is no more device to delete in the fabric"

    if not dcnm_inv.query and module.params["state"] == "query":
        dcnm_inv.result["changed"] = False
        dcnm_inv.result[
            "response"
        ] = "The queried switch is not part of the fabric configured"

    if dcnm_inv.diff_create or dcnm_inv.diff_delete or dcnm_inv.want_create_poap or dcnm_inv.want_create_rma:
        dcnm_inv.result["changed"] = True
    else:
        module.exit_json(**dcnm_inv.result)

    if module.check_mode:
        dcnm_inv.result["changed"] = False
        module.exit_json(**dcnm_inv.result)

    # Delete Switch
    if dcnm_inv.diff_delete:
        # Step 1
        # Delete specific switch/all switch
        dcnm_inv.delete_switch()

    # Discover & Register Switch
    if not dcnm_inv.node_migration:
        if dcnm_inv.diff_create or dcnm_inv.want_create_poap or dcnm_inv.want_create_rma:

            # Step 1
            # Import all switches
            dcnm_inv.import_switches()

            # Import through POAP
            dcnm_inv.poap_config()

            # Import through RMA
            dcnm_inv.rma_config()

            # Step 2
            # Rediscover all switches
            dcnm_inv.rediscover_all_switches()

            # Step 3
            # Check all devices are up
            for check in range(1, 300):
                if not dcnm_inv.all_switches_ok():
                    time.sleep(5)
                    continue

                break

            # Step 4
            # Verify all devices came up finally
            if not dcnm_inv.all_switches_ok():
                msg = "Failed to import all switches into fabric: {0}".format(
                    dcnm_inv.fabric
                )
                module.fail_json(msg=msg)

            # Step 5
            # Save LAN Credentials for each switch
            dcnm_inv.lancred_all_switches()

            # Step 6
            # Assign Role
            dcnm_inv.assign_role()

            # Step 7
            # Config-save all switches
            if module.params["save"]:
                dcnm_inv.config_save()

            # Step 8
            # Config-deploy all switches
            if module.params["deploy"]:
                dcnm_inv.config_deploy()

    module.exit_json(**dcnm_inv.result)


if __name__ == "__main__":
    main()
