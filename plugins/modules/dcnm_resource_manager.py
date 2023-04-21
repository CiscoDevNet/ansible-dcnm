#!/usr/bin/python
#
# Copyright (c) 2022-2023 Cisco and/or its affiliates.
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
__author__ = "Mallik Mudigonda"

DOCUMENTATION = """
---
module: dcnm_resource_manager
short_description: DCNM ansible module for managing resources.
version_added: "2.1.0"
description:
    - DCNM ansible module for creating, deleting and querying resources
author: Mallik Mudigonda (@mmudigon)
options:
  fabric:
    description:
      - 'Name of the target fabric for resource manager operations'
    type: str
    required: true
  state:
    description:
      - The required state of the configuration after module completion.
    type: str
    required: false
    choices:
      - merged
      - deleted
      - query
    default: merged
  config:
    description:
      - A list of dictionaries containing resources and switch information
    type: list
    elements: dict
    suboptions:
      entity_name:
        description:
          - A unique name which identifies the entity to which the resourcce is allocated to.
          - The format of this parameter depends on the scope_type. The details are provided in
          - the EXAMPLES section
        type: str
        required: true
      pool_type:
        description:
          - Type of resource pool
        type: str
        required: true
        choices:
          - ID
          - IP
          - SUBNET
      pool_name:
        description:
          - Name of the resource pool from which the resource is allocated
        type: str
        required: true
      scope_type:
        description:
          - Socpe of resource allocation
        type: str
        required: true
        choices:
          - fabric
          - device
          - device_interface
          - device_pair
          - link
      resource:
        description:
          - Value of the resource being allocated
          - The value will be
          -     an integer if pool_type is ID
          -     an IPV4/IPV6 address if pool_type is IP
          -     an IPV4 address/net_mask or IPV6 address/net_maskif pool_type is SUBNET
        type: str
        required: true
      switch:
        description:
        - IP address or DNS name of the management interface of the switch to which the allocated resource is assigned to.
        type: list
        elements: str
        required: false
"""

EXAMPLES = """
# Entity name format
# ==================
#
# The format of the entity name depends on the scope_type of the resource being allocated.

# Scope Type                Entity Name
# =====================================
# Fabric                    Eg: My_Network_30000
# Device                    Eg: loopback0
# Device Pair               Eg: FDO21331S8T~FDO21332E6X~vPC1
# Device Interface          Eg: FDO21332E6X~Ethernet1/13
# Link                      Eg: FDO21332E6X~Ethernet1/3~FDO21331S8T~Ethernet1/3

# where FDO21331S8T and FDO21331S8T are switch serial numbers

# This module supports the following states:

# Merged:
#   Resources defined in the playbook will be merged into the target fabric.
#     - If the Resources does not exist it will be added.
#     - If the Resources exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - Resources that are not specified in the playbook will be untouched.
#
# Deleted:
#   Resources defined in the playbook will be deleted.
#
# Query:
#   Returns the current DCNM state for the Resources listed in the playbook.

# CREATING RESOURCES
# ==================
- name: Create Resources
  cisco.dcnm.dcnm_resource_manager:
    state: merged                               # choose form [merged, deleted, query]
    fabric: test_fabric
    config:
      - entity_name: "l3_vni_fabric"            # A unique name to identify the resource
        pool_type: "ID"                         # choose from ['ID', 'IP, 'SUBNET']
        pool_name: "L3_VNI"                     # Based on the 'poolType', select appropriate name
        scope_type: "fabric"                    # choose from ['fabric', 'device', device_interface', 'device_pair', 'link']
        resource: "101"                         # The value of the resource being created

      - entity_name: "9M99N34RDED~9NXHSNTEO6C"  # A unique name to identify the resource
        pool_type: "ID"                         # choose from ['ID', 'IP, 'SUBNET']
        pool_name: "VPC_ID"                     # Based on the 'poolType', select appropriate name
        scope_type: "device_pair"               # choose from ['fabric', 'device', device_interface', 'device_pair', 'link']
        switch:                                 # provide the switch information to which the given resource is to be attached
          - 192.175.1.1
          - 192.175.1.2
        resource: "500"                         # The value of the resource being created

      - entity_name: "mmudigon-2"               # A unique name to identify the resource
        pool_type: "IP"                         # choose from ['ID', 'IP, 'SUBNET']
        pool_name: "LOOPBACK0_IP_POOL"          # Based on the 'poolType', select appropriate name
        scope_type: "fabric"                    # choose from ['fabric', 'device', device_interface', 'device_pair', 'link']
        resource: "110.1.1.1"                   # The value of the resource being created

      - entity_name: "9M99N34RDED~Ethernet1/10" # A unique name to identify the resource
        pool_type: "IP"                         # choose from ['ID', 'IP, 'SUBNET']
        pool_name: "LOOPBACK1_IP_POOL"          # Based on the 'poolType', select appropriate name
        scope_type: "device_interface"          # choose from ['fabric', 'device', device_interface', 'device_pair', 'link']
        switch:                                 # provide the switch information to which the given resource is to be attached
          - 192.175.1.1
        resource: "fe:80::04"                   # The value of the resource being created

      - entity_name: "9M99N34RDED~Ethernet1/3~9NXHSNTEO6C~Ethernet1/3"  # A unique name to identify the resource
        pool_type: "SUBNET"                     # choose from ['ID', 'IP, 'SUBNET']
        pool_name: "SUBNET"                     # Based on the 'poolType', select appropriate name
        scope_type: "link"                      # choose from ['fabric', 'device', device_interface', 'device_pair', 'link']
        switch:                                 # provide the switch information to which the given resource is to be attached
          - 192.175.1.1
        resource: "fe:80:05::05/64"

# DELETING RESOURCES
# ==================

- name: Delete Resources
  cisco.dcnm.dcnm_resource_manager:
    state: deleted                              # choose form [merged, deleted, query]
    fabric: test_fabric
    config:
      - entity_name: "l3_vni_fabric"            # A unique name to identify the resource
        pool_type: "ID"                         # choose from ['ID', 'IP, 'SUBNET']
        pool_name: "L3_VNI"                     # Based on the 'poolType', select appropriate name
        scope_type: "fabric"                    # choose from ['fabric', 'device', device_interface', 'device_pair', 'link']

      - entity_name: "9M99N34RDED~9NXHSNTEO6C"  # A unique name to identify the resource
        pool_type: "ID"                         # choose from ['ID', 'IP, 'SUBNET']
        pool_name: "VPC_ID"                     # Based on the 'poolType', select appropriate name
        scope_type: "device_pair"               # choose from ['fabric', 'device', device_interface', 'device_pair', 'link']
        switch:                                 # provide the switch information to which the given resource is attached
          - 192.175.1.1
          - 192.175.1.2

      - entity_name: "mmudigon-2"               # A unique name to identify the resource
        pool_type: "IP"                         # choose from ['ID', 'IP, 'SUBNET']
        pool_name: "LOOPBACK0_IP_POOL"          # Based on the 'poolType', select appropriate name
        scope_type: "fabric"                    # choose from ['fabric', 'device', device_interface', 'device_pair', 'link']

      - entity_name: "9M99N34RDED~Ethernet1/10" # A unique name to identify the resource
        pool_type: "IP"                         # choose from ['ID', 'IP, 'SUBNET']
        pool_name: "LOOPBACK1_IP_POOL"          # Based on the 'poolType', select appropriate name
        scope_type: "device_interface"          # choose from ['fabric', 'device', device_interface', 'device_pair', 'link']
        switch:                                 # provide the switch information to which the given resource is attached
          - 192.175.1.1

      - entity_name: "9M99N34RDED~Ethernet1/3~9NXHSNTEO6C~Ethernet1/3" # A unique name to identify the resource
        pool_type: "SUBNET"                     # choose from ['ID', 'IP, 'SUBNET']
        pool_name: "SUBNET"                     # Based on the 'poolType', select appropriate name
        scope_type: "link"                      # choose from ['fabric', 'device', device_interface', 'device_pair', 'link']
        switch:                                 # provide the switch information to which the given resource is attached
          - 192.175.1.1

# QUERY SERVICE POLICIES
# ======================

- name: Query all Resources - no filters
  cisco.dcnm.dcnm_resource_manager:
    state: query                               # choose form [merged, deleted, query]
    fabric: test_fabric

- name: Query Resources - filter by entity name
  cisco.dcnm.dcnm_resource_manager:
    state: query                                # choose form [merged, deleted, query]
    fabric: test_fabric
    config:
      - entity_name: "l3_vni_fabric"            # A unique name to identify the resource
      - entity_name: "loopback_dev"             # A unique name to identify the resource
      - entity_name: "9M99N34RDED~9NXHSNTEO6C"  # A unique name to identify the resource
      - entity_name: "9M99N34RDED~Ethernet1/10" # A unique name to identify the resource
      - entity_name: "9M99N34RDED~Ethernet1/2~~9NXHSNTEO6CEthernet1/2" # A unique name to identify the resource

- name: Query Resources - filter by switch
  cisco.dcnm.dcnm_resource_manager:
    state: query                                # choose form [merged, deleted, query]
    fabric: test_fabric
    config:
      - switch:                                 # provide the switch information to which the given resource is attached
          - 192.175.1.1

- name: Query Resources - filter by fabric and pool name
  cisco.dcnm.dcnm_resource_manager:
    state: query                                # choose form [merged, deleted, query]
    fabric: test_fabric
    config:
      - pool_name: "L3_VNI"                     # Based on the 'poolType', select appropriate name
      - pool_name: "VPC_ID"                     # Based on the 'poolType', select appropriate name
      - pool_name: "SUBNET"                     # Based on the 'poolType', select appropriate name

- name: Query Resources - filter by switch and pool name
  cisco.dcnm.dcnm_resource_manager:
    state: query                                # choose form [merged, deleted, query]
    fabric: "{{ ansible_it_fabric }}"
    config:
      - pool_name: "L3_VNI"                     # Based on the 'poolType', select appropriate name
        switch:                                 # provide the switch information to which the given resource is attached
          - 192.175.1.1
      - pool_name: "LOOPBACK_ID"                # Based on the 'poolType', select appropriate name
        switch:                                 # provide the switch information to which the given resource is attached
          - 192.175.1.1
      - pool_name: "VPC_ID"                     # Based on the 'poolType', select appropriate name
        switch:                                 # provide the switch information to which the given resource is attached
          - 192.175.1.2

- name: Query Resources - mixed query
  cisco.dcnm.dcnm_resource_manager:
    state: query                                # choose form [merged, deleted, query]
    fabric: test_fabric
    config:
      - entity_name: "l2_vni_fabric"            # A unique name to identify the resource
      - switch:                                 # provide the switch information to which the given resource is attached
          - 192.175.1.1
      - pool_name: "LOOPBACK_ID"                # Based on the 'poolType', select appropriate name
      - pool_name: "VPC_ID"                     # Based on the 'poolType', select appropriate name
        switch:                                 # provide the switch information to which the given resource is attached
          - 192.175.1.1

"""

import json
import copy
import ipaddress

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
    validate_list_of_dicts,
    dcnm_version_supported,
    get_ip_sn_dict,
    get_fabric_inventory_details,
    dcnm_get_ip_addr_info,
)

from datetime import datetime


# Resource Class object which includes all the required methods and data to configure and maintain resources
class DcnmResManager:
    dcnm_rm_paths = {
        11: {
            "RM_GET_RESOURCES_BY_FABRIC": "/rest/resource-manager/fabrics/{}",
            "RM_GET_RESOURCES_BY_SNO_AND_POOLNAME": "/rest/resource-manager/switch/{}/pools/{}",
            "RM_GET_RESOURCES_BY_FABRIC_AND_POOLNAME": "/rest/resource-manager/fabric/{}/pools/{}",
            "RM_CREATE_RESOURCE": "/rest/resource-manager/fabrics/{}/resources",
            "RM_DELETE_RESOURCE": "/rest/resource-manager/resources?id=",
        },
        12: {
            "RM_GET_RESOURCES_BY_FABRIC": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/resource-manager/fabrics/{}",
            "RM_GET_RESOURCES_BY_SNO_AND_POOLNAME": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/resource-manager/switch/{}/pools/{}",
            "RM_GET_RESOURCES_BY_FABRIC_AND_POOLNAME": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/resource-manager/fabric/{}/pools/{}",
            "RM_CREATE_RESOURCE": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/resource-manager/fabrics/{}/resources",
            "RM_DELETE_RESOURCE": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/resource-manager/resources?id=",
        },
    }

    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.fabric = module.params["fabric"]
        self.config = copy.deepcopy(module.params.get("config"))
        self.rm_info = []
        self.want = []
        self.have = []
        self.diff_create = []
        self.diff_delete = []
        self.fd = None
        self.res_pools = {}
        self.changed_dict = [
            {"merged": [], "deleted": [], "query": [], "debugs": []}
        ]

        self.dcnm_version = dcnm_version_supported(self.module)

        self.inventory_data = get_fabric_inventory_details(
            self.module, self.fabric
        )
        self.ip_sn, self.hn_sn = get_ip_sn_dict(self.inventory_data)

        self.paths = self.dcnm_rm_paths[self.dcnm_version]
        self.result = dict(changed=False, diff=[], response=[])

    def log_msg(self, msg):

        if self.fd is None:
            self.fd = open("res_mgr.log", "w+")
        if self.fd is not None:
            self.fd.write(msg)
            self.fd.write("\n")
            self.fd.flush()

    def dcnm_rm_validate_and_build_rm_info(self, cfg, rm_spec):

        """
        Routine to validate the playbook input and fill up default values for objects not included.
        In this case we validate the playbook against rm_spec which inlcudes required information
        This routine updates self.rm_info with validated playbook information by defaulting values
        not included

        Parameters:
            cfg (dict): The config from playbook
            rm_spec (dict): Resource Manager spec

        Returns:
            None
        """

        rm_info, invalid_params = validate_list_of_dicts(cfg, rm_spec)
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(
                "while processing Resource -  "
                + cfg[0]["entity_name"]
                + ", "
                + "\n".join(invalid_params)
            )
            self.module.fail_json(msg=mesg)

        self.rm_info.extend(rm_info)

    def dcnm_rm_check_resource_params(self, res):

        """
        Routine to validate the poolname and scope type combinations. Since all such combinations are
        not valid, this routine checks for valid combinations

        Parameters:
            res (dict): Resource information

        Returns:
            True - if the resource has a valid poolname-scopetype combination
            False - Otherwise
        """

        poolname_to_scope_type = {
            "L3_VNI": ["fabric"],
            "L2_VNI": ["fabric"],
            "VPC_ID": ["device_pair"],
            "FEX_ID": ["device"],
            "BGP_ASN_ID": ["fabric"],
            "LOOPBACK_ID": ["device"],
            "PORT_CHANNEL_ID": ["device"],
            "VPC_DOMAIN_ID": ["fabric"],
            "VPC_PEER_LINK_VLAN": ["device_pair"],
            "TOP_DOWN_L3_DOT1Q": ["device_interface"],
            "TUNNEL_ID_IOS_XE": ["device"],
            "OBJECT_TRACKING_NUMBER_POOL": ["device"],
            "INSTANCE_ID": ["device"],
            "PORT_CHANNEL_ID_IOS_XE": ["device"],
            "ROUTE_MAP_SEQUENCE_NUMBER_POOL": ["device"],
            "SERVICE_NETWORK_VLAN": ["device"],
            "TOP_DOWN_VRF_VLAN": ["device"],
            "TOP_DOWN_NETWORK_VLAN": ["device"],
            "IP_POOL": ["fabric", "device_interface"],
            "SUBNET": ["link"],
        }
        # RESOURCE = {'entity_name': 'l3_vni_fabric', 'pool_type': 'ID', 'pool_name': 'L3_VNI', 'scope_type': 'fabric', 'resource': '101'}

        # Configuration in query state may not include all parameters. So don;t try to validate
        if self.module.params["state"] == "query":
            return True, ""

        if res["pool_type"] == "ID":
            pool_name = res["pool_name"]
        elif res["pool_type"] == "IP":
            pool_name = "IP_POOL"
        elif res["pool_type"] == "SUBNET":
            pool_name = "SUBNET"
        else:
            return (
                False,
                "Given pool type = '" + res["pool_type"] + "' is invalid,"
                " Allowed pool types = ['ID', 'IP', 'SUBNET']",
            )

        if poolname_to_scope_type.get(pool_name, None) is None:
            return (
                False,
                "Given pool name '" + res["pool_name"] + "' is not valid",
            )
        if res["scope_type"] not in poolname_to_scope_type[pool_name]:
            return (
                False,
                "Given scope type '"
                + res["scope_type"]
                + "' is not valid for pool name = '"
                + res["pool_name"]
                + "', Allowed scope_types = "
                + str(poolname_to_scope_type[pool_name]),
            )
        return True, ""

    def dcnm_rm_validate_input(self):

        """
        Routine to validate playbook input based on the state. Since each state has a different
        config structure, this routine handles the validation based on the given state

        Parameters:
            None

        Returns:
            None
        """

        if None is self.config:
            return

        cfg = []
        for item in self.config:

            if self.module.params["state"] != "query":
                if item.get("scope_type", None) is None:
                    self.module.fail_json(
                        msg="Mandatory parameter 'scope_type' missing"
                    )

                if item.get("pool_type", None) is None:
                    self.module.fail_json(
                        msg="Mandatory parameter 'pool_type' missing"
                    )

                if item.get("pool_name", None) is None:
                    self.module.fail_json(
                        msg="Mandatory parameter 'pool_name' missing"
                    )

                if item.get("entity_name", None) is None:
                    self.module.fail_json(
                        msg="Mandatory parameter 'entity_name' missing"
                    )

            rc, mesg = self.dcnm_rm_check_resource_params(item)
            if not rc:
                self.module.fail_json(msg=mesg)

            citem = copy.deepcopy(item)

            cfg.append(citem)

            if self.module.params["state"] == "query":
                # config for query state is different. So validate query state differently
                self.dcnm_rm_validate_query_state_input(cfg)
            else:
                self.dcnm_rm_validate_rm_input(cfg)
            cfg.remove(citem)

    def dcnm_rm_validate_rm_input(self, cfg):

        """
        Routine to validate the playbook input. This routine updates self.rm_info
        with validated playbook information by defaulting values not included

        Parameters:
            cfg (dict): The config from playbook

        Returns:
            None
        """

        rm_spec = dict(
            entity_name=dict(required=True, type="str"),
            pool_type=dict(required=True, type="str"),
            pool_name=dict(required=True, type="str"),
            scope_type=dict(required=True, type="str"),
        )

        if cfg[0]["scope_type"] != "fabric":
            rm_spec["switch"] = dict(required=True, type="list")

        if self.module.params["state"] == "merged":
            if cfg[0]["pool_type"] == "ID":
                rm_spec["resource"] = dict(required=True, type="int")
            if cfg[0]["pool_type"] == "IP":
                if isinstance(
                    ipaddress.ip_address(cfg[0]["resource"]),
                    ipaddress.IPv4Address,
                ):
                    rm_spec["resource"] = dict(required=True, type="ipv4")
                if isinstance(
                    ipaddress.ip_address(cfg[0]["resource"]),
                    ipaddress.IPv6Address,
                ):
                    rm_spec["resource"] = dict(required=True, type="ipv6")
            if cfg[0]["pool_type"] == "SUBNET":
                ip_addr = cfg[0]["resource"].split("/")[0]
                if isinstance(
                    ipaddress.ip_address(ip_addr), ipaddress.IPv4Address
                ):
                    rm_spec["resource"] = dict(
                        required=True, type="ipv4_subnet"
                    )
                if isinstance(
                    ipaddress.ip_address(ip_addr), ipaddress.IPv6Address
                ):
                    rm_spec["resource"] = dict(
                        required=True, type="ipv6_subnet"
                    )

        self.dcnm_rm_validate_and_build_rm_info(cfg, rm_spec)

    def dcnm_rm_validate_query_state_input(self, cfg):

        """
        Playbook input will be different for differnt states. This routine validates the query state
        input. This routine updates self.rm_info with validated playbook information related to query
        state.

        Parameters:
            cfg (dict): The config from playbook

        Returns:
           None
        """

        rm_spec = dict(
            entity_name=dict(type="str"),
            pool_name=dict(type="str"),
            switch=dict(type="list", elements="str"),
        )

        rm_info, invalid_params = validate_list_of_dicts(cfg, rm_spec)
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

        if rm_info:
            self.rm_info.extend(rm_info)

    def dcnm_rm_get_rm_payload(self, rm, sw):

        """
        This routine builds the complete Resource Manager payload based on the information in self.want

        Parameters:
            rm (dict): Resource information

        Returns:
            rm_payload (dict): Resource payload information populated with appropriate data from playbook config
        """

        scope_type_xlate = {
            "fabric": "Fabric",
            "device": "Device",
            "device_interface": "DeviceInterface",
            "device_pair": "DevicePair",
            "link": "Link",
        }

        rm_payload = {}

        # Populate the common information

        rm_payload["poolName"] = rm["pool_name"]

        # Scope type values from playbook must be converted to payload format.

        rm_payload["scopeType"] = scope_type_xlate[rm["scope_type"]]
        rm_payload["entityName"] = rm["entity_name"]
        rm_payload["resource"] = rm.get("resource", None)

        rm_payload["scopeValue"] = (
            self.fabric if rm["scope_type"] == "fabric" else self.ip_sn[sw]
        )

        return rm_payload

    def dcnm_rm_get_want(self):

        """
        This routine updates self.want with the payload information based on the playbook configuration.

        Parameters:
            None

        Returns:
            None
        """

        if None is self.config:
            return

        if not self.rm_info:
            return

        # self.rm_info is a list of directories each having config related to a particular resource
        for rm_elem in self.rm_info:
            if rm_elem.get("switch", None):
                for sw in rm_elem["switch"]:
                    rm_payload = self.dcnm_rm_get_rm_payload(rm_elem, sw)
                    if rm_payload not in self.want:
                        self.want.append(rm_payload)
            else:
                rm_payload = self.dcnm_rm_get_rm_payload(rm_elem, None)
                if rm_payload not in self.want:
                    self.want.append(rm_payload)

    def dcnm_rm_compare_entity_names(self, e1, e2):

        # Eventhough entity names are strings, the same ca be a combination of two serial numbers in
        # certain cases. The order of these serial numbers may be different on the DCNM server than
        # what is given in the playbook. So we split the entity name, sort the same and then compare
        # the resulting contents
        return sorted(e1.split("~")) == sorted(e2.split("~"))

    def dcnm_rm_get_rm_info_from_dcnm(self, res, res_type):

        """
        Routine to get existing Resource information from DCNM which matches the given Resource.

        Parameters:
            res  (dict): Resource information
            res_type (string): String indicating whether the 'res' passed is in 'PLAYBOOK' format
                            or 'PAYLOAD' format
        Returns:
            resp["DATA"] (dict): Resource informatikon obtained from the DCNM server if it exists
            [] otherwise
        """

        key = res["scopeValue"] + "_" + res["poolName"]

        if self.res_pools.get(key, None) is None:
            if res["scopeType"] == "Fabric":
                path_str = "RM_GET_RESOURCES_BY_FABRIC_AND_POOLNAME"
            else:
                path_str = "RM_GET_RESOURCES_BY_SNO_AND_POOLNAME"

            if res_type == "PAYLOAD":
                path = self.paths[path_str].format(
                    res["scopeValue"], res["poolName"]
                )
            else:
                path = ""

            resp = dcnm_send(self.module, "GET", path)

            if resp and (resp["RETURN_CODE"] == 200) and resp["DATA"]:
                self.res_pools[key] = resp["DATA"]
            else:
                return []

        for relem in self.res_pools[key]:
            # For switch and serial number combination, poolName will not be filled with proper value
            # Since we know which pool is used in this run, fill it up here
            relem["resourcePool"]["poolName"] = res["poolName"]
            if self.dcnm_rm_match_resources(
                relem, res, res["scopeType"].lower()
            ):
                return relem
            else:
                if self.dcnm_rm_compare_entity_names(
                    relem["entityName"], res["entityName"]
                ):
                    mismatch_values = self.dcnm_rm_get_mismatched_values(
                        relem, res, res["scopeType"].lower()
                    )
                    self.changed_dict[0]["debugs"].append(
                        {
                            "Entity Name": res["entityName"],
                            "MISMATCHED_VALUES": mismatch_values,
                        }
                    )
        return []

    def dcnm_rm_get_have(self):

        """
        Routine to get exisitng resource information from DCNM that matches information in self.want.
        This routine updates self.have with all the resources that match the given playbook configuration

        Parameters:
            None

        Returns:
            None
        """

        if self.want == []:
            return

        for res in self.want:
            have = self.dcnm_rm_get_rm_info_from_dcnm(res, "PAYLOAD")
            if (have != []) and (have not in self.have):
                self.have.append(have)

    def dcnm_rm_compare_resource_values(self, r1, r2):

        """
        Routine to compare the resource values. Resource values will be different for ID, IP and SUBNET
        pools. For IP and SUBNET the addresses can be included with subnet masks. This routine compares
        these values appropriately

        Parameters:
            r1 : First Resource value
            r2 : Second Resource value

        Returns:
            True - if both resource values same
            False - otherwise
        """

        rv1 = []
        rv2 = []
        r1_ip4 = False
        r2_ip4 = False
        r1_ip6 = False
        r2_ip6 = False

        if "." in r1:
            r1_ip4 = True
        if "." in r2:
            r2_ip4 = True

        if ":" in r1:
            r1_ip6 = True
        if ":" in r2:
            r2_ip6 = True

        if "/" in r1:
            rv1 = r1.split("/")
        if "/" in r1:
            rv2 = r2.split("/")

        if r1_ip4 and r2_ip4:
            if rv1 and not rv2:
                return False
            if rv2 and not rv1:
                return False
            if rv1 and rv2:
                return (
                    ipaddress.IPv4Address(rv1[0]).exploded
                    == ipaddress.IPv4Address(rv2[0]).exploded
                ) and (rv1[1] == rv2[1])
            else:
                return (
                    ipaddress.IPv4Address(r1).exploded
                    == ipaddress.IPv4Address(r2).exploded
                )

        if r1_ip6 and r2_ip6:
            if rv1 and not rv2:
                return False
            if rv2 and not rv1:
                return False
            if rv1 and rv2:
                return (
                    ipaddress.IPv6Address(rv1[0]).exploded
                    == ipaddress.IPv6Address(rv2[0]).exploded
                ) and (rv1[1] == rv2[1])
            else:
                return (
                    ipaddress.IPv6Address(r1).exploded
                    == ipaddress.IPv6Address(r2).exploded
                )

        return r1 == r2

    def dcnm_rm_compare_resources(self, res):

        """
        This routine finds a resource in self.have that matches the given resource. If the given
        resource already exist then the resource is not added to the resource list to be created on
        DCNM server in the current run. The given resource is added to the list of resources to be
        created otherwise

        Parameters:
            res : Resource to be matched from self.have

        Returns:
            DCNM_RES_ADD - if given resource is not found
            DCNM_RES_DONT_ADD - otherwise
        """

        # Comparing resources is different for resources of scopeType Fabric and others

        match_res = []
        match_res = [
            relem
            for relem in self.have
            if (
                self.dcnm_rm_match_resources(
                    relem, res, res["scopeType"].lower()
                )
            )
        ]

        if match_res != []:
            # Found a matching resource. Check the resource values here. If they are same then the given resource
            # is identical to the existing resource. Otherwise we should add it.
            if self.dcnm_rm_compare_resource_values(
                str(match_res[0]["allocatedIp"]), str(res["resource"])
            ):
                return "DCNM_RES_DONT_ADD"
            else:
                return "DCNM_RES_ADD"
        else:

            return "DCNM_RES_ADD"

    def dcnm_rm_get_diff_merge(self):

        """
        Routine to populate a list of payload information in self.diff_create to create new resources.

        Parameters:
            None

        Returns:
            None
        """

        if not self.want:
            return

        for res in self.want:

            rc = self.dcnm_rm_compare_resources(res)

            if rc == "DCNM_RES_ADD":
                # Resource does not exists, create a new one.
                if res not in self.diff_create:
                    self.changed_dict[0]["merged"].append(res)
                    self.diff_create.append(res)

    def dcnm_rm_get_mismatched_values(self, res1, res2, scope):

        """
        Routine to find the resource parameters that are not matching. Routine compares the two resources
        given and populates mismatch_values with parameters that don't match

        Parameters:
            res1 - First resource
            res2 - Second resource
            scope - scope of the resources

        Returns:
            mismatch_values - a list of dicts containing mismatched values
        """

        mismatch_values = []

        if res1["entityType"] != res2["scopeType"]:
            mismatch_values.append(
                {
                    "have_entity_type": res1["entityType"],
                    "want_scope_type": res2["scopeType"],
                }
            )
        if res1["resourcePool"]["poolName"] != res2["poolName"]:
            mismatch_values.append(
                {
                    "have_pool_name": res1["resourcePool"]["poolName"],
                    "want_pool_nme": res2["poolName"],
                }
            )

        if scope == "fabric":
            if res1["resourcePool"]["fabricName"] != self.fabric:
                mismatch_values.append(
                    {
                        "have_fabric_name": res1["resourcePool"]["fabricName"],
                        "want_fabric_name": self.fabric,
                    }
                )
        else:
            if res1["allocatedScopeValue"] != res2["scopeValue"]:
                mismatch_values.append(
                    {
                        "have_scope_value": res1["allocatedScopeValue"],
                        "want_scope_value": res2["scopeValue"],
                    }
                )
        return mismatch_values

    def dcnm_rm_match_resources(self, res1, res2, scope):

        """
        Routine compares two resources based on the given scope

        Parameters:
            res1 - First resource
            res2 - Second resource
            scope - scope of the resources

        Returns:
            True - if resources match
            False - otherwise
        """

        if not self.dcnm_rm_compare_entity_names(
            res1["entityName"], res2["entityName"]
        ):
            return False
        if res1["entityType"] != res2["scopeType"]:
            return False
        if res1["resourcePool"]["poolName"] != res2["poolName"]:
            return False

        if scope == "fabric":
            if res1["resourcePool"]["fabricName"] != self.fabric:
                return False
        else:
            # For scope values of "device_pair", "link" and "device_interface", the scope value will be set
            # to the first part of the entity name by DCNM even though a specific scope value is included
            # in the create payload. So for such scope values we wil check the first part of the entity name
            # also
            if (
                res1["allocatedScopeValue"] != res2["scopeValue"]
                and res1["allocatedScopeValue"]
                != res1["entityName"].split("~")[0]
            ):
                return False
        return True

    def dcnm_rm_get_diff_deleted(self):

        """
        Routine to get a list of payload information that will be used to delete resources.
        This routine updates self.diff_delete	with payloads that are used to delete resources
        from the server.

        Parameters:
            None

        Returns:
            None
        """

        for res in self.have:
            self.diff_delete.append(str(res["id"]))
        if self.diff_delete:
            self.changed_dict[0]["deleted"].extend(self.diff_delete)

    def dcnm_rm_get_diff_query(self):

        """
        Routine to get resource information based on the playbook configuration.
        This routine updates self.result with resources requested for in the playbook if they exist on
        the DCNM server.

        Parameters:
            None

        Returns:
            None
        """

        if self.rm_info == []:
            # No config is included in input. Get all pools by Fabric
            path = self.paths["RM_GET_RESOURCES_BY_FABRIC"].format(self.fabric)

            resp = dcnm_send(self.module, "GET", path)

            if resp and resp["RETURN_CODE"] == 200 and resp["DATA"]:
                self.result["response"].extend(resp["DATA"])
        else:
            res_pools = {}
            for res in self.rm_info:

                filter_by_entity_name = False
                filter_by_switch = False
                path_list = []

                # Check if entity name is included. If so filter the output by entity name
                if res.get("entity_name", None) is not None:
                    filter_by_entity_name = True
                if res.get("pool_name", None) is not None:
                    # Check if switch is included.
                    if res.get("switch", None) is not None:
                        for sw in res["switch"]:
                            path_list.append(
                                self.paths[
                                    "RM_GET_RESOURCES_BY_SNO_AND_POOLNAME"
                                ].format(self.ip_sn[sw], res["pool_name"])
                            )
                            filter_by_switch = True
                    else:
                        path_list.append(
                            self.paths[
                                "RM_GET_RESOURCES_BY_FABRIC_AND_POOLNAME"
                            ].format(self.fabric, res["pool_name"])
                        )
                else:
                    path_list.append(
                        self.paths["RM_GET_RESOURCES_BY_FABRIC"].format(
                            self.fabric
                        )
                    )
                    # Check if switch is included.
                    if res.get("switch", None) is not None:
                        filter_by_switch = True

                for path in path_list:
                    if res_pools.get(path, None) is None:
                        resp = dcnm_send(self.module, "GET", path)
                    else:
                        resp = res_pools[path]

                    if resp and resp["RETURN_CODE"] == 200 and resp["DATA"]:

                        if res_pools.get(path, None) is None:
                            # Note down the resources fetched against the "path". This was we need not fetch the resources again
                            # if required from the same path
                            res_pools[path] = resp

                        if (
                            filter_by_entity_name is False
                            and filter_by_switch is False
                        ):
                            self.result["response"].extend(resp["DATA"])
                            continue

                        rlist = resp["DATA"]

                        # Check if filters are set. If so filter the content based on the filter values
                        if filter_by_entity_name and filter_by_switch:
                            match_res = [
                                relem
                                for relem in rlist
                                if (
                                    self.dcnm_rm_compare_entity_names(
                                        relem["entityName"], res["entity_name"]
                                    )
                                    and self.dcnm_rm_match_switch(
                                        relem["allocatedScopeValue"],
                                        res["switch"],
                                    )
                                )
                            ]
                        elif filter_by_entity_name:
                            match_res = [
                                relem
                                for relem in rlist
                                if self.dcnm_rm_compare_entity_names(
                                    relem["entityName"], res["entity_name"]
                                )
                            ]
                        elif filter_by_switch:
                            match_res = [
                                relem
                                for relem in rlist
                                if self.dcnm_rm_match_switch(
                                    relem["allocatedScopeValue"], res["switch"]
                                )
                            ]

                        if match_res:
                            self.result["response"].extend(match_res)

    def dcnm_rm_match_switch(self, sw, sw_list):

        """
        Routine to compare switch information. This is used to filter out resource information during query.

        Parameters:
            sw - switch information included in the resource on DCNM server
            sw_list - list of switches included in the resource from playbook config

        Returns:
            True - if the switch information is present in the resource from DCNM
            False - otherwise
        """

        for sw_elem in sw_list:
            if sw == self.ip_sn[sw_elem]:
                return True
        return False

    def dcnm_rm_send_message_to_dcnm(self):

        """
        Routine to push payloads to DCNM server. This routine implements reqquired error checks and retry mechanisms to handle
        transient errors. This routine checks self.diff_create, self.diff_delete lists and push appropriate requests to DCNM.

        Parameters:
            None

        Returns:
            None
        """

        resp = None
        create_flag = False
        delete_flag = False

        path = self.paths["RM_CREATE_RESOURCE"].format(self.fabric)

        for res in self.diff_create:

            json_payload = json.dumps(res)
            resp = dcnm_send(self.module, "POST", path, json_payload)

            create_flag = True

            self.result["response"].append(resp)
            if resp and resp.get("RETURN_CODE") != 200:
                resp["CHANGED"] = self.changed_dict[0]
                self.module.fail_json(msg=resp)

        if self.diff_delete:
            path = self.paths["RM_DELETE_RESOURCE"].format(self.fabric)

            del_path = path + ",".join(self.diff_delete)

            resp = dcnm_send(self.module, "DELETE", del_path)

            delete_flag = True

            self.result["response"].append(resp)
            if resp and resp.get("RETURN_CODE") != 200:
                resp["CHANGED"] = self.changed_dict[0]
                self.module.fail_json(msg=resp)

        self.result["changed"] = create_flag or delete_flag

    def dcnm_rm_translate_switch_info(self, config, ip_sn, hn_sn):

        """
        Routine to translate parameters in playbook if required. This routine converts the hostname information included in
        playbook to actual addresses.

        Parameters:
            config - The resource which needs tranlation
            ip_sn - IP address to serial number mappings
            hn_sn - hostname to serial number mappings

        Returns:
            None
        """

        if None is config:
            return

        for cfg in config:

            index = 0

            if None is cfg.get("switch", None):
                continue
            for sw_elem in cfg["switch"]:
                addr_info = dcnm_get_ip_addr_info(
                    self.module, sw_elem, ip_sn, hn_sn
                )
                cfg["switch"][index] = addr_info
                index = index + 1


def main():

    """ main entry point for module execution
    """
    element_spec = dict(
        fabric=dict(required=True, type="str"),
        config=dict(required=False, type="list", elements="dict"),
        state=dict(
            type="str",
            default="merged",
            choices=["merged", "deleted", "query"],
        ),
    )

    module = AnsibleModule(
        argument_spec=element_spec, supports_check_mode=True
    )

    dcnm_rm = DcnmResManager(module)

    dcnm_rm.result["StartTime"] = datetime.now().strftime("%H:%M:%S")

    state = module.params["state"]

    if not dcnm_rm.config:
        if state == "merged" or state == "deleted":
            module.fail_json(
                msg="'config' element is mandatory for state '{0}', given = '{1}'".format(
                    state, dcnm_rm.config
                )
            )

    dcnm_rm.dcnm_rm_translate_switch_info(
        dcnm_rm.config, dcnm_rm.ip_sn, dcnm_rm.hn_sn
    )

    dcnm_rm.dcnm_rm_validate_input()

    if module.params["state"] != "query":
        dcnm_rm.dcnm_rm_get_want()
        dcnm_rm.dcnm_rm_get_have()

    if module.params["state"] == "merged":
        dcnm_rm.dcnm_rm_get_diff_merge()

    if module.params["state"] == "deleted":
        dcnm_rm.dcnm_rm_get_diff_deleted()

    if module.params["state"] == "query":
        dcnm_rm.dcnm_rm_get_diff_query()

    dcnm_rm.result["diff"] = dcnm_rm.changed_dict

    if dcnm_rm.diff_create or dcnm_rm.diff_delete:
        dcnm_rm.result["changed"] = True

    if module.check_mode:
        dcnm_rm.result["changed"] = False
        dcnm_rm.result["EndTime"] = datetime.now().strftime("%H:%M:%S")
        module.exit_json(**dcnm_rm.result)

    dcnm_rm.dcnm_rm_send_message_to_dcnm()

    module.exit_json(**dcnm_rm.result)


if __name__ == "__main__":
    main()
