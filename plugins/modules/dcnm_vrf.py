#!/usr/bin/python
#
# Copyright (c) 2020-2023 Cisco and/or its affiliates.
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
__author__ = "Shrishail Kariyappanavar, Karthik Babu Harichandra Babu, Praveen Ramoorthy, Allen Robel"

DOCUMENTATION = """
---
module: dcnm_vrf
short_description: Add and remove VRFs from a DCNM managed VXLAN fabric.
version_added: "0.9.0"
description:
    - "Add and remove VRFs and VRF Lite Extension from a DCNM managed VXLAN fabric."
    - "In Multisite fabrics, VRFs can be created only on Multisite fabric"
    - "In Multisite fabrics, VRFs cannot be created on member fabric"
author: Shrishail Kariyappanavar(@nkshrishail), Karthik Babu Harichandra Babu (@kharicha), Praveen Ramoorthy(@praveenramoorthy)
options:
  fabric:
    description:
    - Name of the target fabric for vrf operations
    type: str
    required: yes
  state:
    description:
    - The state of DCNM after module completion.
    type: str
    choices:
      - merged
      - replaced
      - overridden
      - deleted
      - query
    default: merged
  config:
    description:
    - List of details of vrfs being managed. Not required for state deleted
    type: list
    elements: dict
    suboptions:
      vrf_name:
        description:
        - Name of the vrf being managed
        type: str
        required: true
      vrf_id:
        description:
        - ID of the vrf being managed
        type: int
        required: false
      vlan_id:
        description:
        - vlan ID for the vrf attachment
        - If not specified in the playbook, DCNM will auto-select an available vlan_id
        type: int
        required: false
      vrf_template:
        description:
        - Name of the config template to be used
        type: str
        default: 'Default_VRF_Universal'
      vrf_extension_template:
        description:
        - Name of the extension config template to be used
        type: str
        default: 'Default_VRF_Extension_Universal'
      service_vrf_template:
        description:
        - Service vrf template
        type: str
        default: None
      vrf_vlan_name:
        description:
        - VRF Vlan Name
        - if > 32 chars enable - system vlan long-name
        - Not applicable to L3VNI w/o VLAN config
        type: str
        required: false
      vrf_intf_desc:
        description:
        - VRF Intf Description
        - Not applicable to L3VNI w/o VLAN config
        type: str
        required: false
      vrf_description:
        description:
        - VRF Description
        type: str
        required: false
      vrf_int_mtu:
        description:
        - VRF interface MTU
        - Not applicable to L3VNI w/o VLAN config
        type: int
        required: false
        default: 9216
      loopback_route_tag:
        description:
        - Loopback Routing Tag
        type: int
        required: false
        default: 12345
      redist_direct_rmap:
        description:
        - Redistribute Direct Route Map
        type: str
        required: false
        default: 'FABRIC-RMAP-REDIST-SUBNET'
      v6_redist_direct_rmap:
        description:
        - IPv6 Redistribute Direct Route Map
        type: str
        required: false
        default: 'FABRIC-RMAP-REDIST-SUBNET'
      max_bgp_paths:
        description:
        - Max BGP Paths
        type: int
        required: false
        default: 1
      max_ibgp_paths:
        description:
        - Max iBGP Paths
        type: int
        required: false
        default: 2
      ipv6_linklocal_enable:
        description:
        - Enable IPv6 link-local Option
        - Not applicable to L3VNI w/o VLAN config
        type: bool
        required: false
        default: true
      l3vni_wo_vlan:
        description:
        - Enable L3 VNI without VLAN
        type: bool
        required: false
        default: Inherited from fabric level settings
      trm_enable:
        description:
        - Enable Tenant Routed Multicast
        type: bool
        required: false
        default: false
      no_rp:
        description:
        - No RP, only SSM is used
        - supported on NDFC only
        type: bool
        required: false
        default: false
      rp_external:
        description:
        - Specifies if RP is external to the fabric
        - Can be configured only when TRM is enabled
        type: bool
        required: false
        default: false
      rp_address:
        description:
        - IPv4 Address of RP
        - Can be configured only when TRM is enabled
        type: str
        required: false
      rp_loopback_id:
        description:
        - loopback ID of RP
        - Can be configured only when TRM is enabled
        type: int
        required: false
      underlay_mcast_ip:
        description:
        - Underlay IPv4 Multicast Address
        - Can be configured only when TRM is enabled
        type: str
        required: false
      overlay_mcast_group:
        description:
        - Underlay IPv4 Multicast group (224.0.0.0/4 to 239.255.255.255/4)
        - Can be configured only when TRM is enabled
        type: str
        required: false
      trm_bgw_msite:
        description:
        - Enable TRM on Border Gateway Multisite
        - Can be configured only when TRM is enabled
        type: bool
        required: false
        default: false
      adv_host_routes:
        description:
        - Flag to Control Advertisement of /32 and /128 Routes to Edge Routers
        type: bool
        required: false
        default: false
      adv_default_routes:
        description:
        - Flag to Control Advertisement of Default Route Internally
        type: bool
        required: false
        default: true
      static_default_route:
        description:
        - Flag to Control Static Default Route Configuration
        type: bool
        required: false
        default: true
      bgp_password:
        description:
        - VRF Lite BGP neighbor password
        - Password should be in Hex string format
        type: str
        required: false
      bgp_passwd_encrypt:
        description:
        - VRF Lite BGP Key Encryption Type
        - Allowed values are 3 (3DES) and 7 (Cisco)
        type: int
        choices:
          - 3
          - 7
        required: false
        default: 3
      netflow_enable:
        description:
        - Enable netflow on VRF-LITE Sub-interface
        - Netflow is supported only if it is enabled on fabric
        - Netflow configs are supported on NDFC only
        type: bool
        required: false
        default: false
      nf_monitor:
        description:
        - Netflow Monitor
        - Netflow configs are supported on NDFC only
        type: str
        required: false
      disable_rt_auto:
        description:
        - Disable RT Auto-Generate
        - supported on NDFC only
        type: bool
        required: false
        default: false
      import_vpn_rt:
        description:
        - VPN routes to import
        - supported on NDFC only
        - Use ',' to separate multiple route-targets
        type: str
        required: false
      export_vpn_rt:
        description:
        - VPN routes to export
        - supported on NDFC only
        - Use ',' to separate multiple route-targets
        type: str
        required: false
      import_evpn_rt:
        description:
        - EVPN routes to import
        - supported on NDFC only
        - Use ',' to separate multiple route-targets
        type: str
        required: false
      export_evpn_rt:
        description:
        - EVPN routes to export
        - supported on NDFC only
        - Use ',' to separate multiple route-targets
        type: str
        required: false
      import_mvpn_rt:
        description:
        - MVPN routes to import
        - supported on NDFC only
        - Can be configured only when TRM is enabled
        - Use ',' to separate multiple route-targets
        type: str
        required: false
      export_mvpn_rt:
        description:
        - MVPN routes to export
        - supported on NDFC only
        - Can be configured only when TRM is enabled
        - Use ',' to separate multiple route-targets
        type: str
        required: false
      attach:
        description:
        - List of vrf attachment details
        type: list
        elements: dict
        suboptions:
          ip_address:
            description:
            - IP address of the switch where vrf will be attached or detached
            type: str
            required: true
            suboptions:
              vrf_lite:
                type: list
                description:
                - VRF Lite Extensions options
                elements: dict
                required: false
                suboptions:
                  peer_vrf:
                    description:
                    - VRF Name to which this extension is attached
                    type: str
                    required: false
                  interface:
                    description:
                    - Interface of the switch which is connected to the edge router
                    type: str
                    required: true
                  ipv4_addr:
                    description:
                    - IP address of the interface which is connected to the edge router
                    type: str
                    required: false
                  neighbor_ipv4:
                    description:
                    - Neighbor IP address of the edge router
                    type: str
                    required: false
                  ipv6_addr:
                    description:
                    - IPv6 address of the interface which is connected to the edge router
                    type: str
                    required: false
                  neighbor_ipv6:
                    description:
                    - Neighbor IPv6 address of the edge router
                    type: str
                    required: false
                  dot1q:
                    description:
                    - DOT1Q Id
                    type: str
                    required: false
          import_evpn_rt:
            description:
            - import evpn route-target
            - supported on NDFC only
            - Use ',' to separate multiple route-targets
            type: str
            required: false
          export_evpn_rt:
            description:
            - export evpn route-target
            - supported on NDFC only
            - Use ',' to separate multiple route-targets
            type: str
            required: false
          deploy:
            description:
            - Per switch knob to control whether to deploy the attachment
            - This knob has been deprecated from Ansible NDFC Collection Version 2.1.0 onwards.
              There will not be any functional impact if specified in playbook.
            type: bool
            default: true
      deploy:
        description:
        - Global knob to control whether to deploy the attachment
        - Ansible NDFC Collection Behavior for Version 2.0.1 and earlier
        - This knob will create and deploy the attachment in DCNM only when set to "True" in playbook
        - Ansible NDFC Collection Behavior for Version 2.1.0 and later
        - Attachments specified in the playbook will always be created in DCNM.
          This knob, when set to "True",  will deploy the attachment in DCNM, by pushing the configs to switch.
          If set to "False", the attachments will be created in DCNM, but will not be deployed
        type: bool
        default: true
"""

EXAMPLES = """
# This module supports the following states:
#
# Merged:
#   VRFs defined in the playbook will be merged into the target fabric.
#     - If the VRF does not exist it will be added.
#     - If the VRF exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - VRFs that are not specified in the playbook will be untouched.
#
# Replaced:
#   VRFs defined in the playbook will be replaced in the target fabric.
#     - If the VRF does not exist it will be added.
#     - If the VRF exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - Properties that can be managed by the module but are  not specified
#       in the playbook will be deleted or defaulted if possible.
#     - VRFs that are not specified in the playbook will be untouched.
#
# Overridden:
#   VRFs defined in the playbook will be overridden in the target fabric.
#     - If the VRF does not exist it will be added.
#     - If the VRF exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - Properties that can be managed by the module but are not specified
#       in the playbook will be deleted or defaulted if possible.
#     - VRFs that are not specified in the playbook will be deleted.
#
# Deleted:
#   VRFs defined in the playbook will be deleted.
#   If no VRFs are provided in the playbook, all VRFs present on that DCNM fabric will be deleted.
#
# Query:
#   Returns the current DCNM state for the VRFs listed in the playbook.
#
# rollback functionality:
# This module supports task level rollback functionality. If any task runs into failures, as part of failure
# handling, the module tries to bring the state of the DCNM back to the state captured in have structure at the
# beginning of the task execution. Following few lines provide a logical description of how this works,
# if (failure)
#     want data = have data
#     have data = get state of DCNM
#     Run the module in override state with above set of data to produce the required set of diffs
#     and push the diff payloads to DCNM.
# If rollback fails, the module does not attempt to rollback again, it just quits with appropriate error messages.

# The two VRFs below will be merged into the target fabric.
- name: Merge vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: merged
    config:
    - vrf_name: ansible-vrf-r1
      vrf_id: 9008011
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      vlan_id: 2000
      service_vrf_template: null
      attach:
      - ip_address: 192.168.1.224
      - ip_address: 192.168.1.225
    - vrf_name: ansible-vrf-r2
      vrf_id: 9008012
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      service_vrf_template: null
      attach:
      - ip_address: 192.168.1.224
      - ip_address: 192.168.1.225

# VRF LITE Extension attached
- name: Merge vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: merged
    config:
    - vrf_name: ansible-vrf-r1
      vrf_id: 9008011
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      vlan_id: 2000
      service_vrf_template: null
      attach:
      - ip_address: 192.168.1.224
      - ip_address: 192.168.1.225
        vrf_lite:
          - peer_vrf: test_vrf_1 # optional
            interface: Ethernet1/16 # mandatory
            ipv4_addr: 10.33.0.2/30 # optional
            neighbor_ipv4: 10.33.0.1 # optional
            ipv6_addr: 2010::10:34:0:7/64 # optional
            neighbor_ipv6: 2010::10:34:0:3 # optional
            dot1q: 2 # dot1q can be got from dcnm/optional
          - peer_vrf: test_vrf_2 # optional
            interface: Ethernet1/17 # mandatory
            ipv4_addr: 20.33.0.2/30 # optional
            neighbor_ipv4: 20.33.0.1 # optional
            ipv6_addr: 3010::10:34:0:7/64 # optional
            neighbor_ipv6: 3010::10:34:0:3 # optional
            dot1q: 3 # dot1q can be got from dcnm/optional

# The two VRFs below will be replaced in the target fabric.
- name: Replace vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: replaced
    config:
    - vrf_name: ansible-vrf-r1
      vrf_id: 9008011
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      vlan_id: 2000
      service_vrf_template: null
      attach:
      - ip_address: 192.168.1.224
      # Delete this attachment
      # - ip_address: 192.168.1.225
      # Create the following attachment
      - ip_address: 192.168.1.226
    # Dont touch this if its present on DCNM
    # - vrf_name: ansible-vrf-r2
    #   vrf_id: 9008012
    #   vrf_template: Default_VRF_Universal
    #   vrf_extension_template: Default_VRF_Extension_Universal
    #   attach:
    #   - ip_address: 192.168.1.224
    #   - ip_address: 192.168.1.225

# The two VRFs below will be overridden in the target fabric.
- name: Override vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: overridden
    config:
    - vrf_name: ansible-vrf-r1
      vrf_id: 9008011
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      vlan_id: 2000
      service_vrf_template: null
      attach:
      - ip_address: 192.168.1.224
      # Delete this attachment
      # - ip_address: 192.168.1.225
      # Create the following attachment
      - ip_address: 192.168.1.226
    # Delete this vrf
    # - vrf_name: ansible-vrf-r2
    #   vrf_id: 9008012
    #   vrf_template: Default_VRF_Universal
    #   vrf_extension_template: Default_VRF_Extension_Universal
    #   vlan_id: 2000
    #   service_vrf_template: null
    #   attach:
    #   - ip_address: 192.168.1.224
    #   - ip_address: 192.168.1.225

- name: Delete selected vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: deleted
    config:
    - vrf_name: ansible-vrf-r1
      vrf_id: 9008011
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      vlan_id: 2000
      service_vrf_template: null
    - vrf_name: ansible-vrf-r2
      vrf_id: 9008012
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      vlan_id: 2000
      service_vrf_template: null

- name: Delete all the vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: deleted

- name: Query vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: query
    config:
    - vrf_name: ansible-vrf-r1
    - vrf_name: ansible-vrf-r2
"""
import ast
import copy
import inspect
import json
import logging
import re
import time

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_get_ip_addr_info, dcnm_get_url, dcnm_send, dcnm_version_supported,
    get_fabric_details, get_fabric_inventory_details, get_ip_sn_dict,
    get_sn_fabric_dict, validate_list_of_dicts, search_nested_json,
    find_dict_in_list_by_key_value)

from ..module_utils.common.log_v2 import Log

dcnm_vrf_paths = {
    11: {
        "GET_VRF": "/rest/top-down/fabrics/{}/vrfs",
        "GET_VRF_ATTACH": "/rest/top-down/fabrics/{}/vrfs/attachments?vrf-names={}",
        "GET_VRF_SWITCH": "/rest/top-down/fabrics/{}/vrfs/switches?vrf-names={}&serial-numbers={}",
        "GET_VRF_ID": "/rest/managed-pool/fabrics/{}/partitions/ids",
        "GET_VLAN": "/rest/resource-manager/vlan/{}?vlanUsageType=TOP_DOWN_VRF_VLAN",
        "GET_NET_VRF": "/rest/resource-manager/fabrics/{}/networks?vrf-name={}"
    },
    12: {
        "GET_VRF": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/vrfs",
        "GET_VRF_ATTACH": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/vrfs/attachments?vrf-names={}",
        "GET_VRF_SWITCH": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/vrfs/switches?vrf-names={}&serial-numbers={}",
        "GET_VRF_ID": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/vrfinfo",
        "GET_VLAN": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/resource-manager/vlan/{}?vlanUsageType=TOP_DOWN_VRF_VLAN",
        "GET_NET_VRF": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/networks?vrf-name={}",
    },
}


class DcnmVrf:
    """
    # Summary

    dcnm_vrf module implementation.
    """

    def __init__(self, module):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.module = module
        self.params = module.params
        self.state = self.params.get("state")

        msg = f"self.state: {self.state}, "
        msg += "self.params: "
        msg += f"{json.dumps(self.params, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        self.fabric = module.params["fabric"]
        self.config = copy.deepcopy(module.params.get("config"))

        msg = f"self.state: {self.state}, "
        msg += "self.config: "
        msg += f"{json.dumps(self.config, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        # Setting self.conf_changed to class scope since, after refactoring,
        # it is initialized and updated in one refactored method
        # (diff_merge_create) and accessed in another refactored method
        # (diff_merge_attach) which reset it to {} at the top of the method
        # (which undid the update in diff_merge_create).
        # TODO: Revisit this in Phase 2 refactoring.
        self.conf_changed = {}
        self.check_mode = False
        self.have_create = []
        self.want_create = []
        self.diff_create = []
        self.diff_create_update = []
        # self.diff_create_quick holds all the create payloads which are
        # missing a vrfId. These payloads are sent to DCNM out of band
        # (in the get_diff_merge()).  We lose diffs for these without this
        # variable. The content stored here will be helpful for cases like
        # "check_mode" and to print diffs[] in the output of each task.
        self.diff_create_quick = []
        self.have_attach = []
        self.want_attach = []
        self.diff_attach = []
        self.validated = []
        # diff_detach contains all attachments of a vrf being deleted,
        # especially for state: OVERRIDDEN
        # The diff_detach and delete operations have to happen before
        # create+attach+deploy for vrfs being created. This is to address
        # cases where VLAN from a vrf which is being deleted is used for
        # another vrf. Without this additional logic, the create+attach+deploy
        # go out first and complain the VLAN is already in use.
        self.diff_detach = []
        self.have_deploy = {}
        self.want_deploy = {}
        self.diff_deploy = {}
        self.diff_undeploy = {}
        self.diff_delete = {}
        self.diff_input_format = []
        self.query = []
        self.dcnm_version = dcnm_version_supported(self.module)

        msg = f"self.dcnm_version: {self.dcnm_version}"
        self.log.debug(msg)

        self.inventory_data = get_fabric_inventory_details(self.module, self.fabric)

        msg = "self.inventory_data: "
        msg += f"{json.dumps(self.inventory_data, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        self.ip_sn, self.hn_sn = get_ip_sn_dict(self.inventory_data)
        self.sn_ip = {value: key for (key, value) in self.ip_sn.items()}
        self.fabric_data = get_fabric_details(self.module, self.fabric)

        msg = "self.fabric_data: "
        msg += f"{json.dumps(self.fabric_data, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        self.fabric_type = self.fabric_data.get("fabricType")
        self.fabric_nvpairs = self.fabric_data.get("nvPairs")
        self.fabric_l3vni_wo_vlan = False

        if self.fabric_nvpairs and self.fabric_nvpairs.get("ENABLE_L3VNI_NO_VLAN") == "true":
            self.fabric_l3vni_wo_vlan = True

        try:
            self.sn_fab = get_sn_fabric_dict(self.inventory_data)
        except ValueError as error:
            msg += f"{self.class_name}.__init__(): {error}"
            module.fail_json(msg=msg)

        if self.dcnm_version > 12:
            self.paths = dcnm_vrf_paths[12]
        else:
            self.paths = dcnm_vrf_paths[self.dcnm_version]

        self.result = {"changed": False, "diff": [], "response": []}

        self.failed_to_rollback = False
        self.WAIT_TIME_FOR_DELETE_LOOP = 5  # in seconds

        self.vrf_lite_properties = [
            "DOT1Q_ID",
            "IF_NAME",
            "IP_MASK",
            "IPV6_MASK",
            "IPV6_NEIGHBOR",
            "NEIGHBOR_IP",
            "PEER_VRF_NAME",
        ]

        msg = "DONE"
        self.log.debug(msg)

    @staticmethod
    def get_list_of_lists(lst: list, size: int) -> list[list]:
        """
        # Summary

        Given a list of items (lst) and a chunk size (size), return a
        list of lists, where each list is size items in length.

        ## Raises

        -    ValueError if:
                -    lst is not a list.
                -    size is not an integer

        ## Example

        print(get_lists_of_lists([1,2,3,4,5,6,7], 3)

        # -> [[1, 2, 3], [4, 5, 6], [7]]
        """
        if not isinstance(lst, list):
            msg = "lst must be a list(). "
            msg += f"Got {type(lst)}."
            raise ValueError(msg)
        if not isinstance(size, int):
            msg = "size must be an integer. "
            msg += f"Got {type(size)}."
            raise ValueError(msg)
        return [lst[x : x + size] for x in range(0, len(lst), size)]

    @staticmethod
    def find_dict_in_list_by_key_value(search: list, key: str, value: str):
        """
        # Summary

        Find a dictionary in a list of dictionaries.


        ## Raises

        None

        ## Parameters

        -   search: A list of dict
        -   key: The key to lookup in each dict
        -   value: The desired matching value for key

        ## Returns

        Either the first matching dict or None

        ## Usage

        ```python
        content = [{"foo": "bar"}, {"foo": "baz"}]

        match = find_dict_in_list_by_key_value(search=content, key="foo", value="baz")
        print(f"{match}")
        # -> {"foo": "baz"}

        match = find_dict_in_list_by_key_value(search=content, key="foo", value="bingo")
        print(f"{match}")
        # -> None
        ```
        """
        match = (d for d in search if d[key] == value)
        return next(match, None)

    # pylint: disable=inconsistent-return-statements
    def to_bool(self, key, dict_with_key):
        """
        # Summary

        Given a dictionary and key, access dictionary[key] and
        try to convert the value therein to a boolean.

        -   If the value is a boolean, return a like boolean.
        -   If the value is a boolean-like string (e.g. "false"
            "True", etc), return the value converted to boolean.

        ## Raises

        -   Call fail_json() if the value is not convertable to boolean.
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        value = dict_with_key.get(key)

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        msg += f"key: {key}, "
        msg += f"value: {value}"
        self.log.debug(msg)

        if value in ["false", "False", False]:
            return False
        if value in ["true", "True", True]:
            return True

        msg = f"{self.class_name}.{method_name}: "
        msg += f"caller: {caller}: "
        msg += f"key: {key}, "
        msg += f"value ({str(value)}), "
        msg += f"with type {type(value)} "
        msg += "is not convertable to boolean"
        self.module.fail_json(msg=msg)

    # pylint: enable=inconsistent-return-statements
    @staticmethod
    def compare_properties(dict1, dict2, property_list, skip_prop=None):
        """
        Given two dictionaries, a list of keys and keys that can be
        skipped, compare the values of the keys in both dictionaries:

        - Return True if all property values match.
        - Return False otherwise
        """
        for prop in property_list:
            if skip_prop and prop in skip_prop:
                continue
            if dict1.get(prop) != dict2.get(prop):
                return False
        return True

    def diff_for_attach_deploy(self, want_a, have_a, replace=False):
        """
        # Summary

        Return attach_list, deploy_vrf

        Where:

        -   attach list is a list of attachment differences
        -   deploy_vrf is a boolean

        ## Raises

        None
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        msg += f"replace == {replace}"
        self.log.debug(msg)

        attach_list = []

        if not want_a:
            return attach_list

        deploy_vrf = False
        for want in want_a:
            found = False
            interface_match = False
            if have_a:
                for have in have_a:
                    if want["serialNumber"] == have["serialNumber"]:
                        # handle instanceValues first
                        want.update(
                            {"freeformConfig": have.get("freeformConfig", "")}
                        )  # copy freeformConfig from have as module is not managing it
                        want_inst_values = {}
                        have_inst_values = {}
                        if (
                            (want["instanceValues"] is not None and want["instanceValues"] != "")
                            and
                            (have["instanceValues"] is not None and have["instanceValues"] != "")
                        ):
                            want_inst_values = ast.literal_eval(want["instanceValues"])
                            have_inst_values = ast.literal_eval(have["instanceValues"])

                            # update unsupported parameters using have
                            # Only need ipv4 or ipv6. Don't require both, but both can be supplied (as per the GUI)
                            if "loopbackId" in have_inst_values:
                                want_inst_values.update(
                                    {"loopbackId": have_inst_values["loopbackId"]}
                                )
                            if "loopbackIpAddress" in have_inst_values:
                                want_inst_values.update(
                                    {
                                        "loopbackIpAddress": have_inst_values[
                                            "loopbackIpAddress"
                                        ]
                                    }
                                )
                            if "loopbackIpV6Address" in have_inst_values:
                                want_inst_values.update(
                                    {
                                        "loopbackIpV6Address": have_inst_values[
                                            "loopbackIpV6Address"
                                        ]
                                    }
                                )

                            want.update(
                                {"instanceValues": json.dumps(want_inst_values)}
                            )
                        if (
                            want["extensionValues"] != ""
                            and have["extensionValues"] != ""
                        ):

                            msg = "want[extensionValues] != '' and "
                            msg += "have[extensionValues] != ''"
                            self.log.debug(msg)

                            want_ext_values = want["extensionValues"]
                            want_ext_values = ast.literal_eval(want_ext_values)
                            have_ext_values = have["extensionValues"]
                            have_ext_values = ast.literal_eval(have_ext_values)

                            want_e = ast.literal_eval(want_ext_values["VRF_LITE_CONN"])
                            have_e = ast.literal_eval(have_ext_values["VRF_LITE_CONN"])

                            if replace and (
                                len(want_e["VRF_LITE_CONN"])
                                != len(have_e["VRF_LITE_CONN"])
                            ):
                                # In case of replace/override if the length of want and have lite attach of a switch
                                # is not same then we have to push the want to NDFC. No further check is required for
                                # this switch
                                break

                            for wlite in want_e["VRF_LITE_CONN"]:
                                for hlite in have_e["VRF_LITE_CONN"]:
                                    found = False
                                    interface_match = False
                                    if wlite["IF_NAME"] != hlite["IF_NAME"]:
                                        continue
                                    found = True
                                    interface_match = True
                                    skip_prop = []
                                    if not wlite["DOT1Q_ID"]:
                                        skip_prop.append("DOT1Q_ID")
                                    if not self.compare_properties(
                                        wlite, hlite, self.vrf_lite_properties, skip_prop
                                    ):
                                        found = False
                                        break

                                    if found:
                                        break

                                    if interface_match and not found:
                                        break

                                if interface_match and not found:
                                    break

                        elif (
                            want["extensionValues"] != ""
                            and have["extensionValues"] == ""
                        ):
                            found = False
                        elif (
                            want["extensionValues"] == ""
                            and have["extensionValues"] != ""
                        ):
                            if replace:
                                found = False
                            else:
                                found = True
                        else:
                            found = True
                            msg = "want_is_deploy: "
                            msg += f"{str(want.get('want_is_deploy'))}, "
                            msg += "have_is_deploy: "
                            msg += f"{str(want.get('have_is_deploy'))}"
                            self.log.debug(msg)

                            want_is_deploy = self.to_bool("is_deploy", want)
                            have_is_deploy = self.to_bool("is_deploy", have)

                            msg = "want_is_deploy: "
                            msg += f"type {type(want_is_deploy)}, "
                            msg += f"value {want_is_deploy}"
                            self.log.debug(msg)

                            msg = "have_is_deploy: "
                            msg += f"type {type(have_is_deploy)}, "
                            msg += f"value {have_is_deploy}"
                            self.log.debug(msg)

                            msg = "want_is_attached: "
                            msg += f"{str(want.get('want_is_attached'))}, "
                            msg += "want_is_attached: "
                            msg += f"{str(want.get('want_is_attached'))}"
                            self.log.debug(msg)

                            want_is_attached = self.to_bool("isAttached", want)
                            have_is_attached = self.to_bool("isAttached", have)

                            msg = "want_is_attached: "
                            msg += f"type {type(want_is_attached)}, "
                            msg += f"value {want_is_attached}"
                            self.log.debug(msg)

                            msg = "have_is_attached: "
                            msg += f"type {type(have_is_attached)}, "
                            msg += f"value {have_is_attached}"
                            self.log.debug(msg)

                            if have_is_attached != want_is_attached:

                                if "isAttached" in want:
                                    del want["isAttached"]

                                want["deployment"] = True
                                attach_list.append(want)
                                if want_is_deploy is True:
                                    if "isAttached" in want:
                                        del want["isAttached"]
                                    deploy_vrf = True
                                continue

                            msg = "want_deployment: "
                            msg += f"{str(want.get('want_deployment'))}, "
                            msg += "have_deployment: "
                            msg += f"{str(want.get('have_deployment'))}"
                            self.log.debug(msg)

                            want_deployment = self.to_bool("deployment", want)
                            have_deployment = self.to_bool("deployment", have)

                            msg = "want_deployment: "
                            msg += f"type {type(want_deployment)}, "
                            msg += f"value {want_deployment}"
                            self.log.debug(msg)

                            msg = "have_deployment: "
                            msg += f"type {type(have_deployment)}, "
                            msg += f"value {have_deployment}"
                            self.log.debug(msg)

                            if (want_deployment != have_deployment) or (
                                want_is_deploy != have_is_deploy
                            ):
                                if want_is_deploy is True:
                                    deploy_vrf = True

                        if self.dict_values_differ(want_inst_values, have_inst_values):
                            msg = "dict values differ. Set found = False"
                            self.log.debug(msg)
                            found = False

                        if found:
                            break

                    if interface_match and not found:
                        break

            if not found:
                msg = "isAttached: "
                msg += f"{str(want.get('isAttached'))}, "
                msg += "is_deploy: "
                msg += f"{str(want.get('is_deploy'))}"
                self.log.debug(msg)

                if self.to_bool("isAttached", want):
                    del want["isAttached"]
                    want["deployment"] = True
                    attach_list.append(want)
                    if self.to_bool("is_deploy", want):
                        deploy_vrf = True

        msg = "Returning "
        msg += f"deploy_vrf: {deploy_vrf}, "
        msg += "attach_list: "
        msg += f"{json.dumps(attach_list, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        return attach_list, deploy_vrf

    def update_attach_params_extension_values(self, attach) -> dict:
        """
        # Summary

        Given an attachment object (see example below):

        -   Return a populated extension_values dictionary
            if the attachment object's vrf_lite parameter is
            not null.
        -   Return an empty dictionary if the attachment object's
            vrf_lite parameter is null.

        ## Raises

        Calls fail_json() if the vrf_lite parameter is not null
        and the role of the switch in the attachment object is not
        one of the various border roles.

        ## Example attach object

        - extensionValues content removed for brevity
        - instanceValues content removed for brevity

        ```json
            {
                "deployment": true,
                "export_evpn_rt": "",
                "extensionValues": "{}",
                "fabric": "f1",
                "freeformConfig": "",
                "import_evpn_rt": "",
                "instanceValues": "{}",
                "isAttached": true,
                "is_deploy": true,
                "serialNumber": "FOX2109PGCS",
                "vlan": 500,
                "vrfName": "ansible-vrf-int1",
                "vrf_lite": [
                    {
                        "dot1q": 2,
                        "interface": "Ethernet1/2",
                        "ipv4_addr": "10.33.0.2/30",
                        "ipv6_addr": "2010::10:34:0:7/64",
                        "neighbor_ipv4": "10.33.0.1",
                        "neighbor_ipv6": "2010::10:34:0:3",
                        "peer_vrf": "ansible-vrf-int1"
                    }
                ]
            }
        ```

        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        if not attach["vrf_lite"]:
            msg = "Early return. No vrf_lite extensions to process."
            self.log.debug(msg)
            return {}

        extension_values: dict = {}
        extension_values["VRF_LITE_CONN"] = []
        ms_con: dict = {}
        ms_con["MULTISITE_CONN"] = []
        extension_values["MULTISITE_CONN"] = json.dumps(ms_con)

        # Before applying the vrf_lite config, verify that the
        # switch role begins with border

        role = self.inventory_data[attach["ip_address"]].get("switchRole")

        if not re.search(r"\bborder\b", role.lower()):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "VRF LITE attachments are appropriate only for switches "
            msg += "with Border roles e.g. Border Gateway, Border Spine, etc. "
            msg += "The playbook and/or controller settings for switch "
            msg += f"{attach['ip_address']} with role {role} need review."
            self.module.fail_json(msg=msg)

        for item in attach["vrf_lite"]:

            # If the playbook contains vrf lite parameters
            # update the extension values.
            vrf_lite_conn = {}
            for param in self.vrf_lite_properties:
                vrf_lite_conn[param] = ""

            if item["interface"]:
                vrf_lite_conn["IF_NAME"] = item["interface"]
            if item["dot1q"]:
                vrf_lite_conn["DOT1Q_ID"] = str(item["dot1q"])
            if item["ipv4_addr"]:
                vrf_lite_conn["IP_MASK"] = item["ipv4_addr"]
            if item["neighbor_ipv4"]:
                vrf_lite_conn["NEIGHBOR_IP"] = item["neighbor_ipv4"]
            if item["ipv6_addr"]:
                vrf_lite_conn["IPV6_MASK"] = item["ipv6_addr"]
            if item["neighbor_ipv6"]:
                vrf_lite_conn["IPV6_NEIGHBOR"] = item["neighbor_ipv6"]
            if item["peer_vrf"]:
                vrf_lite_conn["PEER_VRF_NAME"] = item["peer_vrf"]

            vrf_lite_conn["VRF_LITE_JYTHON_TEMPLATE"] = "Ext_VRF_Lite_Jython"

            msg = "vrf_lite_conn: "
            msg += f"{json.dumps(vrf_lite_conn, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            vrf_lite_connections: dict = {}
            vrf_lite_connections["VRF_LITE_CONN"] = []
            vrf_lite_connections["VRF_LITE_CONN"].append(copy.deepcopy(vrf_lite_conn))

            if extension_values["VRF_LITE_CONN"]:
                extension_values["VRF_LITE_CONN"]["VRF_LITE_CONN"].extend(
                    vrf_lite_connections["VRF_LITE_CONN"]
                )
            else:
                extension_values["VRF_LITE_CONN"] = copy.deepcopy(vrf_lite_connections)

            msg = "Building extension_values: "
            msg += f"{json.dumps(extension_values, indent=4, sort_keys=True)}"
            self.log.debug(msg)

        extension_values["VRF_LITE_CONN"] = json.dumps(
            extension_values["VRF_LITE_CONN"]
        )
        msg = "Returning extension_values: "
        msg += f"{json.dumps(extension_values, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        return copy.deepcopy(extension_values)

    def update_attach_params(self, attach, vrf_name, deploy, vlan_id) -> dict:
        """
        # Summary

        Turn an attachment object (attach) into a payload for the controller.

        ## Raises

        Calls fail_json() if:

        -   The switch in the attachment object is a spine
        -   If the vrf_lite object is not null, and the switch is not
            a border switch
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}."
        self.log.debug(msg)

        if not attach:
            msg = "Early return. No attachments to process."
            self.log.debug(msg)
            return {}

        # dcnm_get_ip_addr_info converts serial_numbers,
        # hostnames, etc, to ip addresses.
        attach["ip_address"] = dcnm_get_ip_addr_info(
            self.module, attach["ip_address"], None, None
        )

        serial = self.ip_to_serial_number(attach["ip_address"])

        msg = "ip_address: "
        msg += f"{attach['ip_address']}, "
        msg += "serial: "
        msg += f"{serial}, "
        msg += "attach: "
        msg += f"{json.dumps(attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if not serial:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += f"Fabric {self.fabric} does not contain switch "
            msg += f"{attach['ip_address']}"
            self.module.fail_json(msg=msg)

        role = self.inventory_data[attach["ip_address"]].get("switchRole")

        if role.lower() in ("spine", "super spine"):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "VRF attachments are not appropriate for "
            msg += "switches with Spine or Super Spine roles. "
            msg += "The playbook and/or controller settings for switch "
            msg += f"{attach['ip_address']} with role {role} need review."
            self.module.fail_json(msg=msg)

        extension_values = self.update_attach_params_extension_values(attach)
        if extension_values:
            attach.update(
                {"extensionValues": json.dumps(extension_values).replace(" ", "")}
            )
        else:
            attach.update({"extensionValues": ""})

        attach.update({"fabric": self.fabric})
        attach.update({"vrfName": vrf_name})
        attach.update({"vlan": vlan_id})
        # This flag is not to be confused for deploy of attachment.
        # "deployment" should be set True for attaching an attachment
        # and set to False for detaching an attachment
        attach.update({"deployment": True})
        attach.update({"isAttached": True})
        attach.update({"serialNumber": serial})
        attach.update({"is_deploy": deploy})

        # freeformConfig, loopbackId, loopbackIpAddress, and
        # loopbackIpV6Address will be copied from have
        attach.update({"freeformConfig": ""})
        inst_values = {
            "loopbackId": "",
            "loopbackIpAddress": "",
            "loopbackIpV6Address": "",
        }
        if self.dcnm_version > 11:
            inst_values.update(
                {
                    "switchRouteTargetImportEvpn": attach["import_evpn_rt"],
                    "switchRouteTargetExportEvpn": attach["export_evpn_rt"],
                }
            )
        attach.update({"instanceValues": json.dumps(inst_values).replace(" ", "")})

        if "deploy" in attach:
            del attach["deploy"]
        if "ip_address" in attach:
            del attach["ip_address"]

        msg = "Returning attach: "
        msg += f"{json.dumps(attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        return copy.deepcopy(attach)

    def dict_values_differ(self, dict1, dict2, skip_keys=None) -> bool:
        """
        # Summary

        Given two dictionaries and, optionally, a list of keys to skip:

        -   Return True if the values for any (non-skipped) keys differs.
        -   Return False otherwise
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        if skip_keys is None:
            skip_keys = []

        for key in dict1.keys():
            if key in skip_keys:
                continue
            dict1_value = str(dict1.get(key)).lower()
            dict2_value = str(dict2.get(key)).lower()
            # Treat None and "" as equal
            if dict1_value in (None, "none", ""):
                dict1_value = "none"
            if dict2_value in (None, "none", ""):
                dict2_value = "none"
            if dict1_value != dict2_value:
                msg = f"Values differ: key {key} "
                msg += f"dict1_value {dict1_value}, type {type(dict1_value)} != "
                msg += f"dict2_value {dict2_value}, type {type(dict2_value)}. "
                msg += "returning True"
                self.log.debug(msg)
                return True
        msg = "All dict values are equal. Returning False."
        self.log.debug(msg)
        return False

    def diff_for_create(self, want, have):
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        configuration_changed = False
        if not have:
            return {}, configuration_changed

        create = {}

        json_to_dict_want = json.loads(want["vrfTemplateConfig"])
        json_to_dict_have = json.loads(have["vrfTemplateConfig"])

        # vlan_id_want drives the conditional below, so we cannot
        # remove it here (as we did with the other params that are
        # compared in the call to self.dict_values_differ())
        vlan_id_want = str(json_to_dict_want.get("vrfVlanId", ""))
        vrfSegmentId_want = json_to_dict_want.get("vrfSegmentId")

        skip_keys = []
        if vlan_id_want == "0":
            skip_keys = ["vrfVlanId"]
        if vrfSegmentId_want is None:
            skip_keys.append("vrfSegmentId")
        templates_differ = self.dict_values_differ(
            json_to_dict_want, json_to_dict_have, skip_keys=skip_keys
        )

        msg = f"templates_differ: {templates_differ}, "
        msg += f"vlan_id_want: {vlan_id_want}"
        self.log.debug(msg)

        if want["vrfId"] is not None and have["vrfId"] != want["vrfId"]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"vrf_id for vrf {want['vrfName']} cannot be updated to "
            msg += "a different value"
            self.module.fail_json(msg=msg)

        elif templates_differ:
            configuration_changed = True
            if want["vrfId"] is None:
                # The vrf updates with missing vrfId will have to use existing
                # vrfId from the instance of the same vrf on DCNM.
                want["vrfId"] = have["vrfId"]
            create = want

        else:
            pass

        msg = f"returning configuration_changed: {configuration_changed}, "
        msg += f"create: {create}"
        self.log.debug(msg)

        return create, configuration_changed

    def update_create_params(self, vrf, vlan_id=""):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        if not vrf:
            return vrf

        v_template = vrf.get("vrf_template", "Default_VRF_Universal")
        ve_template = vrf.get(
            "vrf_extension_template", "Default_VRF_Extension_Universal"
        )
        src = None
        s_v_template = vrf.get("service_vrf_template", None)

        vrf_upd = {
            "fabric": self.fabric,
            "vrfName": vrf["vrf_name"],
            "vrfTemplate": v_template,
            "vrfExtensionTemplate": ve_template,
            "vrfId": vrf.get(
                "vrf_id", None
            ),  # vrf_id will be auto generated in get_diff_merge()
            "serviceVrfTemplate": s_v_template,
            "source": src,
        }
        template_conf = {
            "vrfSegmentId": vrf.get("vrf_id", None),
            "vrfName": vrf["vrf_name"],
            "vrfVlanId": vlan_id,
            "vrfVlanName": vrf.get("vrf_vlan_name", ""),
            "vrfIntfDescription": vrf.get("vrf_intf_desc", ""),
            "vrfDescription": vrf.get("vrf_description", ""),
            "mtu": vrf.get("vrf_int_mtu", ""),
            "tag": vrf.get("loopback_route_tag", ""),
            "vrfRouteMap": vrf.get("redist_direct_rmap", ""),
            "v6VrfRouteMap": vrf.get("v6_redist_direct_rmap", ""),
            "maxBgpPaths": vrf.get("max_bgp_paths", ""),
            "maxIbgpPaths": vrf.get("max_ibgp_paths", ""),
            "ipv6LinkLocalFlag": vrf.get("ipv6_linklocal_enable", True),
            "enableL3VniNoVlan": vrf.get("l3vni_wo_vlan", False),
            "trmEnabled": vrf.get("trm_enable", False),
            "isRPExternal": vrf.get("rp_external", False),
            "rpAddress": vrf.get("rp_address", ""),
            "loopbackNumber": vrf.get("rp_loopback_id", ""),
            "L3VniMcastGroup": vrf.get("underlay_mcast_ip", ""),
            "multicastGroup": vrf.get("overlay_mcast_group", ""),
            "trmBGWMSiteEnabled": vrf.get("trm_bgw_msite", False),
            "advertiseHostRouteFlag": vrf.get("adv_host_routes", False),
            "advertiseDefaultRouteFlag": vrf.get("adv_default_routes", True),
            "configureStaticDefaultRouteFlag": vrf.get("static_default_route", True),
            "bgpPassword": vrf.get("bgp_password", ""),
            "bgpPasswordKeyType": vrf.get("bgp_passwd_encrypt", ""),
        }
        if self.dcnm_version > 11:
            template_conf.update(isRPAbsent=vrf.get("no_rp", False))
            template_conf.update(ENABLE_NETFLOW=vrf.get("netflow_enable", False))
            template_conf.update(NETFLOW_MONITOR=vrf.get("nf_monitor", ""))
            template_conf.update(disableRtAuto=vrf.get("disable_rt_auto", False))
            template_conf.update(routeTargetImport=vrf.get("import_vpn_rt", ""))
            template_conf.update(routeTargetExport=vrf.get("export_vpn_rt", ""))
            template_conf.update(routeTargetImportEvpn=vrf.get("import_evpn_rt", ""))
            template_conf.update(routeTargetExportEvpn=vrf.get("export_evpn_rt", ""))
            template_conf.update(routeTargetImportMvpn=vrf.get("import_mvpn_rt", ""))
            template_conf.update(routeTargetExportMvpn=vrf.get("export_mvpn_rt", ""))

        vrf_upd.update({"vrfTemplateConfig": json.dumps(template_conf)})

        return vrf_upd

    def get_vrf_objects(self) -> dict:
        """
        # Summary

        Retrieve all VRF objects from the controller
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        path = self.paths["GET_VRF"].format(self.fabric)

        vrf_objects = dcnm_send(self.module, "GET", path)

        missing_fabric, not_ok = self.handle_response(vrf_objects, "query_dcnm")

        if missing_fabric or not_ok:
            msg0 = f"caller: {caller}. "
            msg1 = f"{msg0} Fabric {self.fabric} not present on the controller"
            msg2 = f"{msg0} Unable to find vrfs under fabric: {self.fabric}"
            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

        return copy.deepcopy(vrf_objects)

    def get_vrf_lite_objects(self, attach) -> dict:
        """
        # Summary

        Retrieve the IP/Interface that is connected to the switch with serial_number

        attach must contain at least the following keys:

        - fabric: The fabric to search
        - serialNumber: The serial_number of the switch
        - vrfName: The vrf to search
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}"
        self.log.debug(msg)

        msg = f"attach: {json.dumps(attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        verb = "GET"
        path = self.paths["GET_VRF_SWITCH"].format(
            attach["fabric"], attach["vrfName"], attach["serialNumber"]
        )
        msg = f"verb: {verb}, path: {path}"
        self.log.debug(msg)
        lite_objects = dcnm_send(self.module, verb, path)

        msg = f"Returning lite_objects: {json.dumps(lite_objects, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        return copy.deepcopy(lite_objects)

    def get_have(self):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        have_create = []
        have_deploy = {}

        curr_vrfs = ""

        vrf_objects = self.get_vrf_objects()

        if not vrf_objects.get("DATA"):
            return

        for vrf in vrf_objects["DATA"]:
            curr_vrfs += vrf["vrfName"] + ","

        vrf_attach_objects = dcnm_get_url(
            self.module,
            self.fabric,
            self.paths["GET_VRF_ATTACH"],
            curr_vrfs[:-1],
            "vrfs",
        )

        if not vrf_attach_objects["DATA"]:
            return

        for vrf in vrf_objects["DATA"]:
            json_to_dict = json.loads(vrf["vrfTemplateConfig"])
            t_conf = {
                "vrfSegmentId": vrf["vrfId"],
                "vrfName": vrf["vrfName"],
                "vrfVlanId": json_to_dict.get("vrfVlanId", 0),
                "vrfVlanName": json_to_dict.get("vrfVlanName", ""),
                "vrfIntfDescription": json_to_dict.get("vrfIntfDescription", ""),
                "vrfDescription": json_to_dict.get("vrfDescription", ""),
                "mtu": json_to_dict.get("mtu", 9216),
                "tag": json_to_dict.get("tag", 12345),
                "vrfRouteMap": json_to_dict.get("vrfRouteMap", ""),
                "v6VrfRouteMap": json_to_dict.get("v6VrfRouteMap", ""),
                "maxBgpPaths": json_to_dict.get("maxBgpPaths", 1),
                "maxIbgpPaths": json_to_dict.get("maxIbgpPaths", 2),
                "ipv6LinkLocalFlag": json_to_dict.get("ipv6LinkLocalFlag", True),
                "enableL3VniNoVlan": json_to_dict.get("enableL3VniNoVlan", False),
                "trmEnabled": json_to_dict.get("trmEnabled", False),
                "isRPExternal": json_to_dict.get("isRPExternal", False),
                "rpAddress": json_to_dict.get("rpAddress", ""),
                "loopbackNumber": json_to_dict.get("loopbackNumber", ""),
                "L3VniMcastGroup": json_to_dict.get("L3VniMcastGroup", ""),
                "multicastGroup": json_to_dict.get("multicastGroup", ""),
                "trmBGWMSiteEnabled": json_to_dict.get("trmBGWMSiteEnabled", False),
                "advertiseHostRouteFlag": json_to_dict.get(
                    "advertiseHostRouteFlag", False
                ),
                "advertiseDefaultRouteFlag": json_to_dict.get(
                    "advertiseDefaultRouteFlag", True
                ),
                "configureStaticDefaultRouteFlag": json_to_dict.get(
                    "configureStaticDefaultRouteFlag", True
                ),
                "bgpPassword": json_to_dict.get("bgpPassword", ""),
                "bgpPasswordKeyType": json_to_dict.get("bgpPasswordKeyType", 3),
            }

            if self.dcnm_version > 11:
                t_conf.update(isRPAbsent=json_to_dict.get("isRPAbsent", False))
                t_conf.update(ENABLE_NETFLOW=json_to_dict.get("ENABLE_NETFLOW", False))
                t_conf.update(NETFLOW_MONITOR=json_to_dict.get("NETFLOW_MONITOR", ""))
                t_conf.update(disableRtAuto=json_to_dict.get("disableRtAuto", False))
                t_conf.update(
                    routeTargetImport=json_to_dict.get("routeTargetImport", "")
                )
                t_conf.update(
                    routeTargetExport=json_to_dict.get("routeTargetExport", "")
                )
                t_conf.update(
                    routeTargetImportEvpn=json_to_dict.get("routeTargetImportEvpn", "")
                )
                t_conf.update(
                    routeTargetExportEvpn=json_to_dict.get("routeTargetExportEvpn", "")
                )
                t_conf.update(
                    routeTargetImportMvpn=json_to_dict.get("routeTargetImportMvpn", "")
                )
                t_conf.update(
                    routeTargetExportMvpn=json_to_dict.get("routeTargetExportMvpn", "")
                )

            vrf.update({"vrfTemplateConfig": json.dumps(t_conf)})
            del vrf["vrfStatus"]
            have_create.append(vrf)

        upd_vrfs = ""

        for vrf_attach in vrf_attach_objects["DATA"]:
            if not vrf_attach.get("lanAttachList"):
                continue
            attach_list = vrf_attach["lanAttachList"]
            deploy_vrf = ""
            for attach in attach_list:
                attach_state = bool(attach.get("isLanAttached", False))
                deploy = attach_state
                deployed = False
                if attach_state and (
                    attach["lanAttachState"] == "OUT-OF-SYNC"
                    or attach["lanAttachState"] == "PENDING"
                ):
                    deployed = False
                else:
                    deployed = True

                if deployed:
                    deploy_vrf = attach["vrfName"]

                sn = attach["switchSerialNo"]
                vlan = attach["vlanId"]
                inst_values = attach.get("instanceValues", None)

                # The deletes and updates below are done to update the incoming
                # dictionary format to align with the outgoing payload requirements.
                # Ex: 'vlanId' in the attach section of the incoming payload needs to
                # be changed to 'vlan' on the attach section of outgoing payload.

                del attach["vlanId"]
                del attach["switchSerialNo"]
                del attach["switchName"]
                del attach["switchRole"]
                del attach["ipAddress"]
                del attach["lanAttachState"]
                del attach["isLanAttached"]
                del attach["vrfId"]
                del attach["fabricName"]

                attach.update({"fabric": self.fabric})
                attach.update({"vlan": vlan})
                attach.update({"serialNumber": sn})
                attach.update({"deployment": deploy})
                attach.update({"extensionValues": ""})
                attach.update({"instanceValues": inst_values})
                attach.update({"isAttached": attach_state})
                attach.update({"is_deploy": deployed})

                # Get the VRF LITE extension template and update it
                # with the attach['extensionvalues']

                lite_objects = self.get_vrf_lite_objects(attach)

                if not lite_objects.get("DATA"):
                    msg = "Early return. lite_objects missing DATA"
                    self.log.debug(msg)
                    return

                msg = f"lite_objects: {json.dumps(lite_objects, indent=4, sort_keys=True)}"
                self.log.debug(msg)

                for sdl in lite_objects["DATA"]:
                    for epv in sdl["switchDetailsList"]:
                        if not epv.get("extensionValues"):
                            attach.update({"freeformConfig": ""})
                            continue
                        ext_values = ast.literal_eval(epv["extensionValues"])
                        if ext_values.get("VRF_LITE_CONN") is None:
                            continue
                        ext_values = ast.literal_eval(ext_values["VRF_LITE_CONN"])
                        extension_values = {}
                        extension_values["VRF_LITE_CONN"] = []

                        for ev in ext_values.get("VRF_LITE_CONN"):
                            ev_dict = copy.deepcopy(ev)
                            ev_dict.update({"AUTO_VRF_LITE_FLAG": "false"})
                            ev_dict.update(
                                {"VRF_LITE_JYTHON_TEMPLATE": "Ext_VRF_Lite_Jython"}
                            )

                            if extension_values["VRF_LITE_CONN"]:
                                extension_values["VRF_LITE_CONN"][
                                    "VRF_LITE_CONN"
                                ].extend([ev_dict])
                            else:
                                extension_values["VRF_LITE_CONN"] = {
                                    "VRF_LITE_CONN": [ev_dict]
                                }

                        extension_values["VRF_LITE_CONN"] = json.dumps(
                            extension_values["VRF_LITE_CONN"]
                        )

                        ms_con = {}
                        ms_con["MULTISITE_CONN"] = []
                        extension_values["MULTISITE_CONN"] = json.dumps(ms_con)
                        e_values = json.dumps(extension_values).replace(" ", "")

                        attach.update({"extensionValues": e_values})

                        ff_config = epv.get("freeformConfig", "")
                        attach.update({"freeformConfig": ff_config})

            if deploy_vrf:
                upd_vrfs += deploy_vrf + ","

        have_attach = vrf_attach_objects["DATA"]

        if upd_vrfs:
            have_deploy.update({"vrfNames": upd_vrfs[:-1]})

        self.have_create = have_create
        self.have_attach = have_attach
        self.have_deploy = have_deploy

        msg = "self.have_create: "
        msg += f"{json.dumps(self.have_create, indent=4)}"
        self.log.debug(msg)

        # json.dumps() here breaks unit tests since self.have_attach is
        # a MagicMock and not JSON serializable.
        msg = "self.have_attach: "
        msg += f"{self.have_attach}"
        self.log.debug(msg)

        msg = "self.have_deploy: "
        msg += f"{json.dumps(self.have_deploy, indent=4)}"
        self.log.debug(msg)

    def get_want(self):
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        want_create = []
        want_attach = []
        want_deploy = {}

        msg = "self.config "
        msg += f"{json.dumps(self.config, indent=4)}"
        self.log.debug(msg)

        all_vrfs = []

        msg = "self.validated: "
        msg += f"{json.dumps(self.validated, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        for vrf in self.validated:
            vrf_name = vrf.get("vrf_name")
            if not vrf_name:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"vrf missing mandatory key vrf_name: {vrf}"
                self.module.fail_json(msg=msg)

            all_vrfs.append(vrf_name)
            vrf_attach = {}
            vrfs = []

            vrf_deploy = vrf.get("deploy", True)

            if vrf.get("l3vni_wo_vlan"):
                vlan_id = ""
            else:
                if vrf.get("vlan_id"):
                    vlan_id = vrf.get("vlan_id")
                else:
                    vlan_id = 0

            want_create.append(self.update_create_params(vrf, vlan_id))

            if not vrf.get("attach"):
                msg = f"No attachments for vrf {vrf_name}. Skipping."
                self.log.debug(msg)
                continue
            for attach in vrf["attach"]:
                deploy = vrf_deploy
                vrfs.append(
                    self.update_attach_params(attach, vrf_name, deploy, vlan_id)
                )

            if vrfs:
                vrf_attach.update({"vrfName": vrf_name})
                vrf_attach.update({"lanAttachList": vrfs})
                want_attach.append(vrf_attach)

        if len(all_vrfs) != 0:
            vrf_names = ",".join(all_vrfs)
            want_deploy.update({"vrfNames": vrf_names})

        self.want_create = copy.deepcopy(want_create)
        self.want_attach = copy.deepcopy(want_attach)
        self.want_deploy = copy.deepcopy(want_deploy)

        msg = "self.want_create: "
        msg += f"{json.dumps(self.want_create, indent=4)}"
        self.log.debug(msg)

        msg = "self.want_attach: "
        msg += f"{json.dumps(self.want_attach, indent=4)}"
        self.log.debug(msg)

        msg = "self.want_deploy: "
        msg += f"{json.dumps(self.want_deploy, indent=4)}"
        self.log.debug(msg)

    def get_diff_delete(self):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        @staticmethod
        def get_items_to_detach(attach_list):
            detach_list = []
            for item in attach_list:
                if "isAttached" in item:
                    if item["isAttached"]:
                        del item["isAttached"]
                        item.update({"deployment": False})
                        detach_list.append(item)
            return detach_list

        diff_detach = []
        diff_undeploy = {}
        diff_delete = {}

        all_vrfs = []

        if self.config:

            for want_c in self.want_create:

                if not self.find_dict_in_list_by_key_value(
                    search=self.have_create, key="vrfName", value=want_c["vrfName"]
                ):
                    continue

                diff_delete.update({want_c["vrfName"]: "DEPLOYED"})

                have_a = self.find_dict_in_list_by_key_value(
                    search=self.have_attach, key="vrfName", value=want_c["vrfName"]
                )

                if not have_a:
                    continue

                detach_items = get_items_to_detach(have_a["lanAttachList"])
                if detach_items:
                    have_a.update({"lanAttachList": detach_items})
                    diff_detach.append(have_a)
                    all_vrfs.append(have_a["vrfName"])
            if len(all_vrfs) != 0:
                diff_undeploy.update({"vrfNames": ",".join(all_vrfs)})

        else:

            for have_a in self.have_attach:
                detach_items = get_items_to_detach(have_a["lanAttachList"])
                if detach_items:
                    have_a.update({"lanAttachList": detach_items})
                    diff_detach.append(have_a)
                    all_vrfs.append(have_a["vrfName"])

                diff_delete.update({have_a["vrfName"]: "DEPLOYED"})
            if len(all_vrfs) != 0:
                diff_undeploy.update({"vrfNames": ",".join(all_vrfs)})

        self.diff_detach = diff_detach
        self.diff_undeploy = diff_undeploy
        self.diff_delete = diff_delete

        msg = "self.diff_detach: "
        msg += f"{json.dumps(self.diff_detach, indent=4)}"
        self.log.debug(msg)

        msg = "self.diff_undeploy: "
        msg += f"{json.dumps(self.diff_undeploy, indent=4)}"
        self.log.debug(msg)

        msg = "self.diff_delete: "
        msg += f"{json.dumps(self.diff_delete, indent=4)}"
        self.log.debug(msg)

    def get_diff_override(self):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        all_vrfs = []
        diff_delete = {}

        self.get_diff_replace()

        diff_detach = self.diff_detach
        diff_undeploy = self.diff_undeploy

        for have_a in self.have_attach:
            found = self.find_dict_in_list_by_key_value(
                search=self.want_create, key="vrfName", value=have_a["vrfName"]
            )

            detach_list = []
            if not found:
                for item in have_a["lanAttachList"]:
                    if "isAttached" in item:
                        if item["isAttached"]:
                            del item["isAttached"]
                            item.update({"deployment": False})
                            detach_list.append(item)

                if detach_list:
                    have_a.update({"lanAttachList": detach_list})
                    diff_detach.append(have_a)
                    all_vrfs.append(have_a["vrfName"])

                diff_delete.update({have_a["vrfName"]: "DEPLOYED"})

        if len(all_vrfs) != 0:
            diff_undeploy.update({"vrfNames": ",".join(all_vrfs)})

        self.diff_delete = diff_delete
        self.diff_detach = diff_detach
        self.diff_undeploy = diff_undeploy

        msg = "self.diff_delete: "
        msg += f"{json.dumps(self.diff_delete, indent=4)}"
        self.log.debug(msg)

        msg = "self.diff_detach: "
        msg += f"{json.dumps(self.diff_detach, indent=4)}"
        self.log.debug(msg)

        msg = "self.diff_undeploy: "
        msg += f"{json.dumps(self.diff_undeploy, indent=4)}"
        self.log.debug(msg)

    def get_diff_replace(self):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        all_vrfs = []

        self.get_diff_merge(replace=True)
        diff_attach = self.diff_attach
        diff_deploy = self.diff_deploy

        for have_a in self.have_attach:
            replace_vrf_list = []
            h_in_w = False
            for want_a in self.want_attach:
                if have_a["vrfName"] == want_a["vrfName"]:
                    h_in_w = True

                    for a_h in have_a["lanAttachList"]:
                        if "isAttached" in a_h:
                            if not a_h["isAttached"]:
                                continue
                        a_match = False

                        if want_a.get("lanAttachList"):
                            for a_w in want_a.get("lanAttachList"):
                                if a_h["serialNumber"] == a_w["serialNumber"]:
                                    # Have is already in diff, no need to continue looking for it.
                                    a_match = True
                                    break
                        if not a_match:
                            if "isAttached" in a_h:
                                del a_h["isAttached"]
                            a_h.update({"deployment": False})
                            replace_vrf_list.append(a_h)
                    break

            if not h_in_w:
                found = self.find_dict_in_list_by_key_value(
                    search=self.want_create, key="vrfName", value=have_a["vrfName"]
                )

                if found:
                    atch_h = have_a["lanAttachList"]
                    for a_h in atch_h:
                        if "isAttached" in a_h:
                            if not a_h["isAttached"]:
                                continue
                            del a_h["isAttached"]
                            a_h.update({"deployment": False})
                            replace_vrf_list.append(a_h)

            if replace_vrf_list:
                in_diff = False
                for d_attach in self.diff_attach:
                    if have_a["vrfName"] == d_attach["vrfName"]:
                        in_diff = True
                        d_attach["lanAttachList"].extend(replace_vrf_list)
                        break

                if not in_diff:
                    r_vrf_dict = {
                        "vrfName": have_a["vrfName"],
                        "lanAttachList": replace_vrf_list,
                    }
                    diff_attach.append(r_vrf_dict)
                    all_vrfs.append(have_a["vrfName"])

        if len(all_vrfs) == 0:
            self.diff_attach = diff_attach
            self.diff_deploy = diff_deploy
            return

        modified_all_vrfs = copy.deepcopy(all_vrfs)
        for vrf in all_vrfs:
            # If the playbook sets the deploy key to False, then we need to remove the vrf from the deploy list.
            want_vrf_data = find_dict_in_list_by_key_value(search=self.config, key="vrf_name", value=vrf)
            if want_vrf_data.get('deploy', True) is False:
                modified_all_vrfs.remove(vrf)

        if modified_all_vrfs:
            if not diff_deploy:
                diff_deploy.update({"vrfNames": ",".join(modified_all_vrfs)})
            else:
                vrfs = self.diff_deploy["vrfNames"] + "," + ",".join(modified_all_vrfs)
                diff_deploy.update({"vrfNames": vrfs})

        self.diff_attach = copy.deepcopy(diff_attach)
        self.diff_deploy = copy.deepcopy(diff_deploy)

        msg = "self.diff_attach: "
        msg += f"{json.dumps(self.diff_attach, indent=4)}"
        self.log.debug(msg)

        msg = "self.diff_deploy: "
        msg += f"{json.dumps(self.diff_deploy, indent=4)}"
        self.log.debug(msg)

    def get_next_vrf_id(self, fabric) -> int:
        """
        # Summary

        Return the next available vrf_id for fabric.

        ## Raises

        Calls fail_json() if:
        - Controller version is unsupported
        - Unable to retrieve next available vrf_id for fabric
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        attempt = 0
        vrf_id = None
        while attempt < 10:
            attempt += 1
            path = self.paths["GET_VRF_ID"].format(fabric)
            if self.dcnm_version > 11:
                vrf_id_obj = dcnm_send(self.module, "GET", path)
            else:
                vrf_id_obj = dcnm_send(self.module, "POST", path)

            missing_fabric, not_ok = self.handle_response(vrf_id_obj, "query_dcnm")

            if missing_fabric or not_ok:
                # arobel: TODO: Not covered by UT
                msg0 = f"{self.class_name}.{method_name}: "
                msg1 = f"{msg0} Fabric {fabric} not present on the controller"
                msg2 = f"{msg0} Unable to generate vrfId under fabric {fabric}"
                self.module.fail_json(msg=msg1 if missing_fabric else msg2)

            if not vrf_id_obj["DATA"]:
                continue

            if self.dcnm_version == 11:
                vrf_id = vrf_id_obj["DATA"].get("partitionSegmentId")
            elif self.dcnm_version >= 12:
                vrf_id = vrf_id_obj["DATA"].get("l3vni")
            else:
                # arobel: TODO: Not covered by UT
                msg = f"{self.class_name}.{method_name}: "
                msg += "Unsupported controller version: "
                msg += f"{self.dcnm_version}"
                self.module.fail_json(msg)

        if vrf_id is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Unable to retrieve vrf_id "
            msg += f"for fabric {fabric}"
            self.module.fail_json(msg)
        return int(str(vrf_id))

    def diff_merge_create(self, replace=False):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        msg += f"replace == {replace}"
        self.log.debug(msg)

        self.conf_changed = {}

        diff_create = []
        diff_create_update = []
        diff_create_quick = []

        for want_c in self.want_create:
            vrf_found = False
            for have_c in self.have_create:
                if want_c["vrfName"] == have_c["vrfName"]:
                    vrf_found = True
                    msg = "Calling diff_for_create with: "
                    msg += f"want_c: {json.dumps(want_c, indent=4, sort_keys=True)}, "
                    msg += f"have_c: {json.dumps(have_c, indent=4, sort_keys=True)}"
                    self.log.debug(msg)

                    diff, conf_chg = self.diff_for_create(want_c, have_c)

                    msg = "diff_for_create() returned with: "
                    msg += f"conf_chg {conf_chg}, "
                    msg += f"diff {json.dumps(diff, indent=4, sort_keys=True)}, "
                    self.log.debug(msg)

                    msg = f"Updating self.conf_changed[{want_c['vrfName']}] "
                    msg += f"with {conf_chg}"
                    self.log.debug(msg)
                    self.conf_changed.update({want_c["vrfName"]: conf_chg})

                    if diff:
                        msg = "Appending diff_create_update with "
                        msg += f"{json.dumps(diff, indent=4, sort_keys=True)}"
                        self.log.debug(msg)
                        diff_create_update.append(diff)
                    break

            if not vrf_found:
                vrf_id = want_c.get("vrfId", None)
                if vrf_id is not None:
                    diff_create.append(want_c)
                else:
                    # vrfId is not provided by user.
                    # Fetch the next available vrfId and use it here.
                    vrf_id = self.get_next_vrf_id(self.fabric)

                    want_c.update({"vrfId": vrf_id})
                    json_to_dict = json.loads(want_c["vrfTemplateConfig"])
                    template_conf = {
                        "vrfSegmentId": vrf_id,
                        "vrfName": want_c["vrfName"],
                        "vrfVlanId": json_to_dict.get("vrfVlanId"),
                        "vrfVlanName": json_to_dict.get("vrfVlanName"),
                        "vrfIntfDescription": json_to_dict.get("vrfIntfDescription"),
                        "vrfDescription": json_to_dict.get("vrfDescription"),
                        "mtu": json_to_dict.get("mtu"),
                        "tag": json_to_dict.get("tag"),
                        "vrfRouteMap": json_to_dict.get("vrfRouteMap"),
                        "v6VrfRouteMap": json_to_dict.get("v6VrfRouteMap"),
                        "maxBgpPaths": json_to_dict.get("maxBgpPaths"),
                        "maxIbgpPaths": json_to_dict.get("maxIbgpPaths"),
                        "ipv6LinkLocalFlag": json_to_dict.get("ipv6LinkLocalFlag"),
                        "enableL3VniNoVlan": json_to_dict.get("enableL3VniNoVlan"),
                        "trmEnabled": json_to_dict.get("trmEnabled"),
                        "isRPExternal": json_to_dict.get("isRPExternal"),
                        "rpAddress": json_to_dict.get("rpAddress"),
                        "loopbackNumber": json_to_dict.get("loopbackNumber"),
                        "L3VniMcastGroup": json_to_dict.get("L3VniMcastGroup"),
                        "multicastGroup": json_to_dict.get("multicastGroup"),
                        "trmBGWMSiteEnabled": json_to_dict.get("trmBGWMSiteEnabled"),
                        "advertiseHostRouteFlag": json_to_dict.get(
                            "advertiseHostRouteFlag"
                        ),
                        "advertiseDefaultRouteFlag": json_to_dict.get(
                            "advertiseDefaultRouteFlag"
                        ),
                        "configureStaticDefaultRouteFlag": json_to_dict.get(
                            "configureStaticDefaultRouteFlag"
                        ),
                        "bgpPassword": json_to_dict.get("bgpPassword"),
                        "bgpPasswordKeyType": json_to_dict.get("bgpPasswordKeyType"),
                    }

                    if self.dcnm_version > 11:
                        template_conf.update(isRPAbsent=json_to_dict.get("isRPAbsent"))
                        template_conf.update(
                            ENABLE_NETFLOW=json_to_dict.get("ENABLE_NETFLOW")
                        )
                        template_conf.update(
                            NETFLOW_MONITOR=json_to_dict.get("NETFLOW_MONITOR")
                        )
                        template_conf.update(
                            disableRtAuto=json_to_dict.get("disableRtAuto")
                        )
                        template_conf.update(
                            routeTargetImport=json_to_dict.get("routeTargetImport")
                        )
                        template_conf.update(
                            routeTargetExport=json_to_dict.get("routeTargetExport")
                        )
                        template_conf.update(
                            routeTargetImportEvpn=json_to_dict.get(
                                "routeTargetImportEvpn"
                            )
                        )
                        template_conf.update(
                            routeTargetExportEvpn=json_to_dict.get(
                                "routeTargetExportEvpn"
                            )
                        )
                        template_conf.update(
                            routeTargetImportMvpn=json_to_dict.get(
                                "routeTargetImportMvpn"
                            )
                        )
                        template_conf.update(
                            routeTargetExportMvpn=json_to_dict.get(
                                "routeTargetExportMvpn"
                            )
                        )

                    want_c.update({"vrfTemplateConfig": json.dumps(template_conf)})

                    create_path = self.paths["GET_VRF"].format(self.fabric)

                    diff_create_quick.append(want_c)

                    if self.module.check_mode:
                        continue

                    # arobel: TODO: Not covered by UT
                    resp = dcnm_send(
                        self.module, "POST", create_path, json.dumps(want_c)
                    )
                    self.result["response"].append(resp)

                    fail, self.result["changed"] = self.handle_response(resp, "create")

                    if fail:
                        self.failure(resp)

        self.diff_create = diff_create
        self.diff_create_update = diff_create_update
        self.diff_create_quick = diff_create_quick

        msg = "self.diff_create: "
        msg += f"{json.dumps(self.diff_create, indent=4)}"
        self.log.debug(msg)

        msg = "self.diff_create_quick: "
        msg += f"{json.dumps(self.diff_create_quick, indent=4)}"
        self.log.debug(msg)

        msg = "self.diff_create_update: "
        msg += f"{json.dumps(self.diff_create_update, indent=4)}"
        self.log.debug(msg)

    def diff_merge_attach(self, replace=False):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        msg += f"replace == {replace}"
        self.log.debug(msg)

        diff_attach = []
        diff_deploy = {}

        all_vrfs = []
        for want_a in self.want_attach:
            # Check user intent for this VRF and don't add it to the deploy_vrf
            # list if the user has not requested a deploy.
            want_config = self.find_dict_in_list_by_key_value(
                search=self.config, key="vrf_name", value=want_a["vrfName"]
            )
            deploy_vrf = ""
            attach_found = False
            for have_a in self.have_attach:
                if want_a["vrfName"] == have_a["vrfName"]:
                    attach_found = True
                    diff, deploy_vrf_bool = self.diff_for_attach_deploy(
                        want_a["lanAttachList"], have_a["lanAttachList"], replace
                    )
                    if diff:
                        base = want_a.copy()
                        del base["lanAttachList"]
                        base.update({"lanAttachList": diff})

                        diff_attach.append(base)
                        if (want_config["deploy"] is True) and (
                            deploy_vrf_bool is True
                        ):
                            deploy_vrf = want_a["vrfName"]
                    else:
                        if want_config["deploy"] is True and (
                            deploy_vrf_bool
                            or self.conf_changed.get(want_a["vrfName"], False)
                        ):
                            deploy_vrf = want_a["vrfName"]

            msg = f"attach_found: {attach_found}"
            self.log.debug(msg)

            if not attach_found and want_a.get("lanAttachList"):
                attach_list = []
                for attach in want_a["lanAttachList"]:
                    if attach.get("isAttached"):
                        del attach["isAttached"]
                    if attach.get("is_deploy") is True:
                        deploy_vrf = want_a["vrfName"]
                    attach["deployment"] = True
                    attach_list.append(copy.deepcopy(attach))
                if attach_list:
                    base = want_a.copy()
                    del base["lanAttachList"]
                    base.update({"lanAttachList": attach_list})
                    diff_attach.append(base)
                # for atch in attach_list:
                #     atch["deployment"] = True

            if deploy_vrf:
                all_vrfs.append(deploy_vrf)

        modified_all_vrfs = copy.deepcopy(all_vrfs)
        for vrf in all_vrfs:
            # If the playbook sets the deploy key to False, then we need to remove the vrf from the deploy list.
            want_vrf_data = find_dict_in_list_by_key_value(search=self.config, key="vrf_name", value=vrf)
            if want_vrf_data.get("deploy", True) is False:
                modified_all_vrfs.remove(vrf)

        if modified_all_vrfs:
            if not diff_deploy:
                diff_deploy.update({"vrfNames": ",".join(modified_all_vrfs)})
            else:
                vrfs = self.diff_deploy["vrfNames"] + "," + ",".join(modified_all_vrfs)
                diff_deploy.update({"vrfNames": vrfs})

        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy

        msg = "self.diff_attach: "
        msg += f"{json.dumps(self.diff_attach, indent=4)}"
        self.log.debug(msg)

        msg = "self.diff_deploy: "
        msg += f"{json.dumps(self.diff_deploy, indent=4)}"
        self.log.debug(msg)

    def get_diff_merge(self, replace=False):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        msg += f"replace == {replace}"
        self.log.debug(msg)

        # Special cases:
        # 1. Auto generate vrfId if its not mentioned by user:
        #    - In this case, query the controller for a vrfId and
        #      use it in the payload.
        #    - Any such vrf create requests need to be pushed individually
        #      (not bulk op).

        self.diff_merge_create(replace)
        self.diff_merge_attach(replace)

    def format_diff(self):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        diff = []

        diff_create = copy.deepcopy(self.diff_create)
        diff_create_quick = copy.deepcopy(self.diff_create_quick)
        diff_create_update = copy.deepcopy(self.diff_create_update)
        diff_attach = copy.deepcopy(self.diff_attach)
        diff_detach = copy.deepcopy(self.diff_detach)
        diff_deploy = (
            self.diff_deploy["vrfNames"].split(",") if self.diff_deploy else []
        )
        diff_undeploy = (
            self.diff_undeploy["vrfNames"].split(",") if self.diff_undeploy else []
        )

        msg = "INPUT: diff_create: "
        msg += f"{json.dumps(diff_create, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = "INPUT: diff_create_quick: "
        msg += f"{json.dumps(diff_create_quick, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = "INPUT: diff_create_update: "
        msg += f"{json.dumps(diff_create_update, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = "INPUT: diff_attach: "
        msg += f"{json.dumps(diff_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = "INPUT: diff_detach: "
        msg += f"{json.dumps(diff_detach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = "INPUT: diff_deploy: "
        msg += f"{json.dumps(diff_deploy, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = "INPUT: diff_undeploy: "
        msg += f"{json.dumps(diff_undeploy, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        diff_create.extend(diff_create_quick)
        diff_create.extend(diff_create_update)
        diff_attach.extend(diff_detach)
        diff_deploy.extend(diff_undeploy)

        for want_d in diff_create:

            msg = "want_d: "
            msg += f"{json.dumps(want_d, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            found_a = self.find_dict_in_list_by_key_value(
                search=diff_attach, key="vrfName", value=want_d["vrfName"]
            )

            msg = "found_a: "
            msg += f"{json.dumps(found_a, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            found_c = copy.deepcopy(want_d)

            msg = "found_c: PRE_UPDATE: "
            msg += f"{json.dumps(found_c, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            src = found_c["source"]
            found_c.update({"vrf_name": found_c["vrfName"]})
            found_c.update({"vrf_id": found_c["vrfId"]})
            found_c.update({"vrf_template": found_c["vrfTemplate"]})
            found_c.update({"vrf_extension_template": found_c["vrfExtensionTemplate"]})
            del found_c["source"]
            found_c.update({"source": src})
            found_c.update({"service_vrf_template": found_c["serviceVrfTemplate"]})
            found_c.update({"attach": []})

            json_to_dict = json.loads(found_c["vrfTemplateConfig"])
            found_c.update({"vrf_vlan_name": json_to_dict.get("vrfVlanName", "")})
            found_c.update(
                {"vrf_intf_desc": json_to_dict.get("vrfIntfDescription", "")}
            )
            found_c.update({"vrf_description": json_to_dict.get("vrfDescription", "")})
            found_c.update({"vrf_int_mtu": json_to_dict.get("mtu", "")})
            found_c.update({"loopback_route_tag": json_to_dict.get("tag", "")})
            found_c.update({"redist_direct_rmap": json_to_dict.get("vrfRouteMap", "")})
            found_c.update({"v6_redist_direct_rmap": json_to_dict.get("v6VrfRouteMap", "")})
            found_c.update({"max_bgp_paths": json_to_dict.get("maxBgpPaths", "")})
            found_c.update({"max_ibgp_paths": json_to_dict.get("maxIbgpPaths", "")})
            found_c.update(
                {"ipv6_linklocal_enable": json_to_dict.get("ipv6LinkLocalFlag", True)}
            )
            found_c.update({"l3vni_wo_vlan": json_to_dict.get("enableL3VniNoVlan", False)})
            found_c.update({"trm_enable": json_to_dict.get("trmEnabled", False)})
            found_c.update({"rp_external": json_to_dict.get("isRPExternal", False)})
            found_c.update({"rp_address": json_to_dict.get("rpAddress", "")})
            found_c.update({"rp_loopback_id": json_to_dict.get("loopbackNumber", "")})
            found_c.update(
                {"underlay_mcast_ip": json_to_dict.get("L3VniMcastGroup", "")}
            )
            found_c.update(
                {"overlay_mcast_group": json_to_dict.get("multicastGroup", "")}
            )
            found_c.update(
                {"trm_bgw_msite": json_to_dict.get("trmBGWMSiteEnabled", False)}
            )
            found_c.update(
                {"adv_host_routes": json_to_dict.get("advertiseHostRouteFlag", False)}
            )
            found_c.update(
                {
                    "adv_default_routes": json_to_dict.get(
                        "advertiseDefaultRouteFlag", True
                    )
                }
            )
            found_c.update(
                {
                    "static_default_route": json_to_dict.get(
                        "configureStaticDefaultRouteFlag", True
                    )
                }
            )
            found_c.update({"bgp_password": json_to_dict.get("bgpPassword", "")})
            found_c.update(
                {"bgp_passwd_encrypt": json_to_dict.get("bgpPasswordKeyType", "")}
            )
            if self.dcnm_version > 11:
                found_c.update({"no_rp": json_to_dict.get("isRPAbsent", False)})
                found_c.update(
                    {"netflow_enable": json_to_dict.get("ENABLE_NETFLOW", True)}
                )
                found_c.update({"nf_monitor": json_to_dict.get("NETFLOW_MONITOR", "")})
                found_c.update(
                    {"disable_rt_auto": json_to_dict.get("disableRtAuto", False)}
                )
                found_c.update(
                    {"import_vpn_rt": json_to_dict.get("routeTargetImport", "")}
                )
                found_c.update(
                    {"export_vpn_rt": json_to_dict.get("routeTargetExport", "")}
                )
                found_c.update(
                    {"import_evpn_rt": json_to_dict.get("routeTargetImportEvpn", "")}
                )
                found_c.update(
                    {"export_evpn_rt": json_to_dict.get("routeTargetExportEvpn", "")}
                )
                found_c.update(
                    {"import_mvpn_rt": json_to_dict.get("routeTargetImportMvpn", "")}
                )
                found_c.update(
                    {"export_mvpn_rt": json_to_dict.get("routeTargetExportMvpn", "")}
                )

            del found_c["fabric"]
            del found_c["vrfName"]
            del found_c["vrfId"]
            del found_c["vrfTemplate"]
            del found_c["vrfExtensionTemplate"]
            del found_c["serviceVrfTemplate"]
            del found_c["vrfTemplateConfig"]

            msg = "found_c: POST_UPDATE: "
            msg += f"{json.dumps(found_c, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            if diff_deploy and found_c["vrf_name"] in diff_deploy:
                diff_deploy.remove(found_c["vrf_name"])
            if not found_a:
                msg = "not found_a.  Appending found_c to diff."
                self.log.debug(msg)
                diff.append(found_c)
                continue

            attach = found_a["lanAttachList"]

            for a_w in attach:
                attach_d = {}

                for k, v in self.ip_sn.items():
                    if v == a_w["serialNumber"]:
                        attach_d.update({"ip_address": k})
                        break
                attach_d.update({"vlan_id": a_w["vlan"]})
                attach_d.update({"deploy": a_w["deployment"]})
                found_c["attach"].append(attach_d)

            msg = "Appending found_c to diff."
            self.log.debug(msg)

            diff.append(found_c)

            diff_attach.remove(found_a)

        for vrf in diff_attach:
            new_attach_dict = {}
            new_attach_list = []
            attach = vrf["lanAttachList"]

            for a_w in attach:
                attach_d = {}
                for k, v in self.ip_sn.items():
                    if v == a_w["serialNumber"]:
                        attach_d.update({"ip_address": k})
                        break
                attach_d.update({"vlan_id": a_w["vlan"]})
                attach_d.update({"deploy": a_w["deployment"]})
                new_attach_list.append(attach_d)

            if new_attach_list:
                if diff_deploy and vrf["vrfName"] in diff_deploy:
                    diff_deploy.remove(vrf["vrfName"])
                new_attach_dict.update({"attach": new_attach_list})
                new_attach_dict.update({"vrf_name": vrf["vrfName"]})
                diff.append(new_attach_dict)

        for vrf in diff_deploy:
            new_deploy_dict = {"vrf_name": vrf}
            diff.append(new_deploy_dict)

        self.diff_input_format = copy.deepcopy(diff)

        msg = "self.diff_input_format: "
        msg += f"{json.dumps(self.diff_input_format, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def get_diff_query(self):
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        path = self.paths["GET_VRF"].format(self.fabric)
        vrf_objects = dcnm_send(self.module, "GET", path)

        missing_fabric, not_ok = self.handle_response(vrf_objects, "query_dcnm")

        if (
            vrf_objects.get("ERROR") == "Not Found"
            and vrf_objects.get("RETURN_CODE") == 404
        ):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += f"Fabric {self.fabric} does not exist on the controller"
            self.module.fail_json(msg=msg)

        if missing_fabric or not_ok:
            # arobel: TODO: Not covered by UT
            msg0 = f"{self.class_name}.{method_name}:"
            msg0 += f"caller: {caller}. "
            msg1 = f"{msg0} Fabric {self.fabric} not present on the controller"
            msg2 = f"{msg0} Unable to find VRFs under fabric: {self.fabric}"
            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

        if not vrf_objects["DATA"]:
            return

        if self.config:
            query = []
            for want_c in self.want_create:
                # Query the VRF
                for vrf in vrf_objects["DATA"]:

                    if want_c["vrfName"] == vrf["vrfName"]:

                        item = {"parent": {}, "attach": []}
                        item["parent"] = vrf

                        # Query the Attachment for the found VRF
                        path = self.paths["GET_VRF_ATTACH"].format(
                            self.fabric, vrf["vrfName"]
                        )

                        vrf_attach_objects = dcnm_send(self.module, "GET", path)

                        missing_fabric, not_ok = self.handle_response(
                            vrf_attach_objects, "query_dcnm"
                        )

                        if missing_fabric or not_ok:
                            # arobel: TODO: Not covered by UT
                            msg0 = f"{self.class_name}.{method_name}:"
                            msg0 += f"caller: {caller}. "
                            msg1 = f"{msg0} Fabric {self.fabric} not present on the controller"
                            msg2 = f"{msg0} Unable to find attachments for "
                            msg2 += f"vrfs: {vrf['vrfName']} under "
                            msg2 += f"fabric: {self.fabric}"
                            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

                        if not vrf_attach_objects["DATA"]:
                            return

                        for vrf_attach in vrf_attach_objects["DATA"]:
                            if want_c["vrfName"] == vrf_attach["vrfName"]:
                                if not vrf_attach.get("lanAttachList"):
                                    continue
                                attach_list = vrf_attach["lanAttachList"]

                                for attach in attach_list:
                                    # copy attach and update it with the keys that
                                    # get_vrf_lite_objects() expects.
                                    attach_copy = copy.deepcopy(attach)
                                    attach_copy.update({"fabric": self.fabric})
                                    attach_copy.update(
                                        {"serialNumber": attach["switchSerialNo"]}
                                    )
                                    lite_objects = self.get_vrf_lite_objects(
                                        attach_copy
                                    )
                                    if not lite_objects.get("DATA"):
                                        return
                                    item["attach"].append(lite_objects.get("DATA")[0])
                                query.append(item)

        else:
            query = []
            # Query the VRF
            for vrf in vrf_objects["DATA"]:
                item = {"parent": {}, "attach": []}
                item["parent"] = vrf

                # Query the Attachment for the found VRF
                path = self.paths["GET_VRF_ATTACH"].format(self.fabric, vrf["vrfName"])

                vrf_attach_objects = dcnm_send(self.module, "GET", path)

                missing_fabric, not_ok = self.handle_response(vrf_objects, "query_dcnm")

                if missing_fabric or not_ok:
                    msg0 = f"caller: {caller}. "
                    msg1 = f"{msg0} Fabric {self.fabric} not present on DCNM"
                    msg2 = f"{msg0} Unable to find attachments for "
                    msg2 += f"vrfs: {vrf['vrfName']} under fabric: {self.fabric}"

                    self.module.fail_json(msg=msg1 if missing_fabric else msg2)
                    # TODO: add a _pylint_: disable=inconsistent-return
                    # at the top and remove this return
                    return

                if not vrf_attach_objects["DATA"]:
                    return

                for vrf_attach in vrf_attach_objects["DATA"]:
                    if not vrf_attach.get("lanAttachList"):
                        continue
                    attach_list = vrf_attach["lanAttachList"]

                    for attach in attach_list:
                        # copy attach and update it with the keys that
                        # get_vrf_lite_objects() expects.
                        attach_copy = copy.deepcopy(attach)
                        attach_copy.update({"fabric": self.fabric})
                        attach_copy.update({"serialNumber": attach["switchSerialNo"]})
                        lite_objects = self.get_vrf_lite_objects(attach_copy)

                        if not lite_objects.get("DATA"):
                            return
                        item["attach"].append(lite_objects.get("DATA")[0])
                    query.append(item)

        self.query = query

    def push_diff_create_update(self, is_rollback=False):
        """
        # Summary

        Send diff_create_update to the controller
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        action = "create"
        path = self.paths["GET_VRF"].format(self.fabric)
        verb = "PUT"

        if self.diff_create_update:
            for vrf in self.diff_create_update:
                update_path = f"{path}/{vrf['vrfName']}"
                # Check for VRF VLAN ID in the template
                json_to_dict = json.loads(vrf["vrfTemplateConfig"])
                vlan_id = json_to_dict.get("vrfVlanId", "0")
                if vlan_id == 0:
                    # Get the next available VLAN ID, vlan 0 shouldn't be pushed
                    # to the controller
                    vlan_path = self.paths["GET_VLAN"].format(self.fabric)
                    vlan_data = dcnm_send(self.module, "GET", vlan_path)
                    if vlan_data["RETURN_CODE"] != 200:
                        msg = f"{self.class_name}.{method_name}: "
                        msg += f"caller: {caller}, "
                        msg += f"vrf_name: {vrf['vrfName']}. "
                        msg += f"Failure getting autogenerated vlan_id {vlan_data}"
                        self.module.fail_json(msg=msg)

                    vlan_id = vlan_data["DATA"]
                    json_to_dict.update({"vrfVlanId": vlan_id})
                    vrf.update({"vrfTemplateConfig": json.dumps(json_to_dict)})

                self.send_to_controller(
                    action,
                    verb,
                    update_path,
                    vrf,
                    log_response=True,
                    is_rollback=is_rollback,
                )

    def push_diff_detach(self, is_rollback=False):
        """
        # Summary

        Send diff_detach to the controller
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        msg += "self.diff_detach: "
        msg += f"{json.dumps(self.diff_detach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if not self.diff_detach:
            msg = "Early return. self.diff_detach is empty."
            self.log.debug(msg)
            return

        # For multisite fabric, update the fabric name to the child fabric
        # containing the switches
        if self.fabric_type == "MFD":
            for elem in self.diff_detach:
                for node in elem["lanAttachList"]:
                    node["fabric"] = self.sn_fab[node["serialNumber"]]

        for diff_attach in self.diff_detach:
            for vrf_attach in diff_attach["lanAttachList"]:
                if "is_deploy" in vrf_attach.keys():
                    del vrf_attach["is_deploy"]

        action = "attach"
        path = self.paths["GET_VRF"].format(self.fabric)
        detach_path = path + "/attachments"
        verb = "POST"

        self.send_to_controller(
            action,
            verb,
            detach_path,
            self.diff_detach,
            log_response=True,
            is_rollback=is_rollback,
        )

    def push_diff_undeploy(self, is_rollback=False):
        """
        # Summary

        Send diff_undeploy to the controller
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        msg += "self.diff_undeploy: "
        msg += f"{json.dumps(self.diff_undeploy, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if not self.diff_undeploy:
            msg = "Early return. self.diff_undeploy is empty."
            self.log.debug(msg)
            return

        action = "deploy"
        path = self.paths["GET_VRF"].format(self.fabric)
        deploy_path = path + "/deployments"
        verb = "POST"

        self.send_to_controller(
            action,
            verb,
            deploy_path,
            self.diff_undeploy,
            log_response=True,
            is_rollback=is_rollback,
        )

    def push_diff_delete(self, is_rollback=False):
        """
        # Summary

        Send diff_delete to the controller
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        msg += "self.diff_delete: "
        msg += f"{json.dumps(self.diff_delete, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if not self.diff_delete:
            msg = "Early return. self.diff_delete is None."
            self.log.debug(msg)
            return

        action = "delete"
        path = self.paths["GET_VRF"].format(self.fabric)
        verb = "DELETE"

        del_failure = ""

        self.wait_for_vrf_del_ready()
        for vrf, state in self.diff_delete.items():
            if state == "OUT-OF-SYNC":
                del_failure += vrf + ","
                continue
            delete_path = f"{path}/{vrf}"
            self.send_to_controller(
                action,
                verb,
                delete_path,
                self.diff_delete,
                log_response=True,
                is_rollback=is_rollback,
            )

        if del_failure:
            msg = f"{self.class_name}.push_diff_delete: "
            msg += f"Deletion of vrfs {del_failure[:-1]} has failed"
            self.result["response"].append(msg)
            self.module.fail_json(msg=self.result)

    def push_diff_create(self, is_rollback=False):
        """
        # Summary

        Send diff_create to the controller
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        msg += "self.diff_create: "
        msg += f"{json.dumps(self.diff_create, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if not self.diff_create:
            msg = "Early return. self.diff_create is empty."
            self.log.debug(msg)
            return

        for vrf in self.diff_create:
            json_to_dict = json.loads(vrf["vrfTemplateConfig"])
            vlan_id = json_to_dict.get("vrfVlanId", "0")
            vrf_name = json_to_dict.get("vrfName")

            if vlan_id == 0:
                vlan_path = self.paths["GET_VLAN"].format(self.fabric)
                vlan_data = dcnm_send(self.module, "GET", vlan_path)

                # TODO: arobel: Not in UT
                if vlan_data["RETURN_CODE"] != 200:
                    msg = f"{self.class_name}.{method_name}: "
                    msg += f"caller: {caller}, "
                    msg += f"vrf_name: {vrf_name}. "
                    msg += f"Failure getting autogenerated vlan_id {vlan_data}"
                    self.module.fail_json(msg=msg)

                vlan_id = vlan_data["DATA"]

            t_conf = {
                "vrfSegmentId": vrf["vrfId"],
                "vrfName": json_to_dict.get("vrfName", ""),
                "vrfVlanId": vlan_id,
                "vrfVlanName": json_to_dict.get("vrfVlanName"),
                "vrfIntfDescription": json_to_dict.get("vrfIntfDescription"),
                "vrfDescription": json_to_dict.get("vrfDescription"),
                "mtu": json_to_dict.get("mtu"),
                "tag": json_to_dict.get("tag"),
                "vrfRouteMap": json_to_dict.get("vrfRouteMap"),
                "v6VrfRouteMap": json_to_dict.get("v6VrfRouteMap"),
                "maxBgpPaths": json_to_dict.get("maxBgpPaths"),
                "maxIbgpPaths": json_to_dict.get("maxIbgpPaths"),
                "ipv6LinkLocalFlag": json_to_dict.get("ipv6LinkLocalFlag"),
                "enableL3VniNoVlan": json_to_dict.get("enableL3VniNoVlan"),
                "trmEnabled": json_to_dict.get("trmEnabled"),
                "isRPExternal": json_to_dict.get("isRPExternal"),
                "rpAddress": json_to_dict.get("rpAddress"),
                "loopbackNumber": json_to_dict.get("loopbackNumber"),
                "L3VniMcastGroup": json_to_dict.get("L3VniMcastGroup"),
                "multicastGroup": json_to_dict.get("multicastGroup"),
                "trmBGWMSiteEnabled": json_to_dict.get("trmBGWMSiteEnabled"),
                "advertiseHostRouteFlag": json_to_dict.get("advertiseHostRouteFlag"),
                "advertiseDefaultRouteFlag": json_to_dict.get(
                    "advertiseDefaultRouteFlag"
                ),
                "configureStaticDefaultRouteFlag": json_to_dict.get(
                    "configureStaticDefaultRouteFlag"
                ),
                "bgpPassword": json_to_dict.get("bgpPassword"),
                "bgpPasswordKeyType": json_to_dict.get("bgpPasswordKeyType"),
            }

            if self.dcnm_version > 11:
                t_conf.update(isRPAbsent=json_to_dict.get("isRPAbsent"))
                t_conf.update(ENABLE_NETFLOW=json_to_dict.get("ENABLE_NETFLOW"))
                t_conf.update(NETFLOW_MONITOR=json_to_dict.get("NETFLOW_MONITOR"))
                t_conf.update(disableRtAuto=json_to_dict.get("disableRtAuto"))
                t_conf.update(routeTargetImport=json_to_dict.get("routeTargetImport"))
                t_conf.update(routeTargetExport=json_to_dict.get("routeTargetExport"))
                t_conf.update(
                    routeTargetImportEvpn=json_to_dict.get("routeTargetImportEvpn")
                )
                t_conf.update(
                    routeTargetExportEvpn=json_to_dict.get("routeTargetExportEvpn")
                )
                t_conf.update(
                    routeTargetImportMvpn=json_to_dict.get("routeTargetImportMvpn")
                )
                t_conf.update(
                    routeTargetExportMvpn=json_to_dict.get("routeTargetExportMvpn")
                )

            vrf.update({"vrfTemplateConfig": json.dumps(t_conf)})

            msg = "Sending vrf create request."
            self.log.debug(msg)

            action = "create"
            verb = "POST"
            path = self.paths["GET_VRF"].format(self.fabric)
            payload = copy.deepcopy(vrf)

            self.send_to_controller(
                action, verb, path, payload, log_response=True, is_rollback=is_rollback
            )

    def is_border_switch(self, serial_number) -> bool:
        """
        # Summary

        Given a switch serial_number:

        -   Return True if the switch is a border switch
        -   Return False otherwise
        """
        is_border = False
        for ip, serial in self.ip_sn.items():
            if serial != serial_number:
                continue
            role = self.inventory_data[ip].get("switchRole")
            r = re.search(r"\bborder\b", role.lower())
            if r:
                is_border = True
        return is_border

    def get_extension_values_from_lite_objects(self, lite: list[dict]) -> list:
        """
        # Summary

        Given a list of lite objects, return:

        -   A list containing the extensionValues, if any, from these
            lite objects.
        -   An empty list, if the lite objects have no extensionValues

        ## Raises

        None
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        extension_values_list: list[dict] = []
        for item in lite:
            if str(item.get("extensionType")) != "VRF_LITE":
                continue
            extension_values = item["extensionValues"]
            extension_values = ast.literal_eval(extension_values)
            extension_values_list.append(extension_values)

        msg = "Returning extension_values_list: "
        msg += f"{json.dumps(extension_values_list, indent=4, sort_keys=True)}."
        self.log.debug(msg)

        return extension_values_list

    def get_vrf_lite_dot1q_id(self, serial_number: str, vrf_name: str, interface: str) -> int:
        """
        # Summary

        Given a switch serial, vrf name and ifname, return the dot1q ID
        reserved for the vrf_lite extension on that switch.

        ## Raises

        Calls fail_json if DNCM fails to reserve the dot1q ID.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        msg += f"serial_number: {serial_number}"
        msg += f"vrf name: {vrf_name}"
        msg += f"interface: {interface}"
        self.log.debug(msg)

        dot1q_id = None
        path = "/appcenter/cisco/ndfc/api/v1/lan-fabric"
        path += "/rest/resource-manager/reserve-id"
        verb = "POST"
        payload = {"scopeType": "DeviceInterface",
                   "usageType": "TOP_DOWN_L3_DOT1Q",
                   "serialNumber": serial_number,
                   "ifName": interface,
                   "allocatedTo": vrf_name}

        resp = dcnm_send(self.module, verb, path, json.dumps(payload))
        if resp.get("RETURN_CODE") != 200:
            msg = f"{self.class_name}.get_vrf_lite_dot1q_id: "
            msg += f"caller: {caller}. "
            msg += "Failed to get dot1q ID for vrf_lite extension on switch "
            msg += f"{serial_number} for vrf {vrf_name} and interface {interface}. "
            msg += f"Response: {resp}"
            self.module.fail_json(msg=msg)
        else:
            msg = f"{self.class_name}.get_vrf_lite_dot1q_id: "
            msg += f"caller: {caller}. "
            msg += "Successfully got dot1q ID for vrf_lite extension on switch "
            msg += f"{serial_number} for vrf {vrf_name} and interface {interface}. "
            msg += f"Response: {resp}"
            self.log.debug(msg)
            dot1q_id = resp.get("DATA")
            return dot1q_id

    def update_vrf_attach_vrf_lite_extensions(self, vrf_attach, lite) -> dict:
        """
        # Summary

        ## params
            -   vrf_attach
                A vrf_attach object containing a vrf_lite extension
                to update
            -   lite: A list of current vrf_lite extension objects from
                the switch

        ## Description

        1.  Merge the values from the vrf_attach object into a matching
            vrf_lite extension object (if any) from the switch.
        2,  Update the vrf_attach object with the merged result.
        3.  Return the updated vrf_attach object.

        If no matching vrf_lite extension object is found on the switch,
        return the unmodified vrf_attach object.

        "matching" in this case means:

        1. The extensionType of the switch's extension object is VRF_LITE
        2. The IF_NAME in the extensionValues of the extension object
           matches the interface in vrf_attach.vrf_lite.
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        msg += "vrf_attach: "
        msg += f"{json.dumps(vrf_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        serial_number = vrf_attach.get("serialNumber")

        msg = f"serial_number: {serial_number}"
        self.log.debug(msg)

        if vrf_attach.get("vrf_lite") is None:
            if "vrf_lite" in vrf_attach:
                del vrf_attach["vrf_lite"]
            vrf_attach["extensionValues"] = ""
            msg = f"serial_number: {serial_number}, "
            msg += "vrf_attach does not contain a vrf_lite configuration. "
            msg += "Returning it with empty extensionValues. "
            msg += f"{json.dumps(vrf_attach, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            return copy.deepcopy(vrf_attach)

        msg = f"serial_number: {serial_number}, "
        msg += "Received lite: "
        msg += f"{json.dumps(lite, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        ext_values = self.get_extension_values_from_lite_objects(lite)
        if ext_values is None:
            ip_address = self.serial_number_to_ip(serial_number)
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "No VRF LITE capable interfaces found on "
            msg += "this switch. "
            msg += f"ip: {ip_address}, "
            msg += f"serial_number: {serial_number}"
            self.log.debug(msg)
            self.module.fail_json(msg=msg)

        matches: dict = {}
        # user_vrf_lite_interfaces and switch_vrf_lite_interfaces
        # are used in fail_json message when no matching interfaces
        # are found on the switch
        user_vrf_lite_interfaces = []
        switch_vrf_lite_interfaces = []
        for item in vrf_attach.get("vrf_lite"):
            item_interface = item.get("interface")
            user_vrf_lite_interfaces.append(item_interface)
            for ext_value in ext_values:
                ext_value_interface = ext_value.get("IF_NAME")
                switch_vrf_lite_interfaces.append(ext_value_interface)
                msg = f"item_interface: {item_interface}, "
                msg += f"ext_value_interface: {ext_value_interface}"
                self.log.debug(msg)
                if item_interface == ext_value_interface:
                    msg = "Found item: "
                    msg += f"item[interface] {item_interface}, == "
                    msg += f"ext_values[IF_NAME] {ext_value_interface}, "
                    msg += f"{json.dumps(item)}"
                    self.log.debug(msg)
                    matches[item_interface] = {}
                    matches[item_interface]["user"] = item
                    matches[item_interface]["switch"] = ext_value
        if not matches:
            # No matches. fail_json here to avoid the following 500 error
            # "Provided interface doesn't have extensions"
            ip_address = self.serial_number_to_ip(serial_number)
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "No matching interfaces with vrf_lite extensions "
            msg += f"found on switch {ip_address} ({serial_number}). "
            msg += "playbook vrf_lite_interfaces: "
            msg += f"{','.join(sorted(user_vrf_lite_interfaces))}. "
            msg += "switch vrf_lite_interfaces: "
            msg += f"{','.join(sorted(switch_vrf_lite_interfaces))}."
            self.log.debug(msg)
            self.module.fail_json(msg)

        msg = "Matching extension object(s) found on the switch. "
        msg += "Proceeding to convert playbook vrf_lite configuration "
        msg += "to payload format. "
        msg += f"matches: {json.dumps(matches, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        extension_values: dict = {}
        extension_values["VRF_LITE_CONN"] = []
        extension_values["MULTISITE_CONN"] = []

        for interface, item in matches.items():
            msg = f"interface: {interface}: "
            msg += "item: "
            msg += f"{json.dumps(item, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            nbr_dict = {}
            nbr_dict["IF_NAME"] = item["user"]["interface"]

            if item["user"]["dot1q"]:
                nbr_dict["DOT1Q_ID"] = str(item["user"]["dot1q"])
            else:
                dot1q_vlan = self.get_vrf_lite_dot1q_id(
                    serial_number,
                    vrf_attach.get("vrfName"),
                    nbr_dict["IF_NAME"]
                )
                if dot1q_vlan is not None:
                    nbr_dict["DOT1Q_ID"] = str(dot1q_vlan)
                else:
                    msg = f"{self.class_name}.{method_name}: "
                    msg += f"caller: {caller}. "
                    msg += "Failed to get dot1q ID for vrf_lite extension "
                    msg += f"on switch {serial_number} for vrf {vrf_attach.get('vrfName')} "
                    msg += f"and interface {nbr_dict['IF_NAME']}"
                    self.module.fail_json(msg=msg)

            if item["user"]["ipv4_addr"]:
                nbr_dict["IP_MASK"] = item["user"]["ipv4_addr"]
            else:
                nbr_dict["IP_MASK"] = item["switch"]["IP_MASK"]

            if item["user"]["neighbor_ipv4"]:
                nbr_dict["NEIGHBOR_IP"] = item["user"]["neighbor_ipv4"]
            else:
                nbr_dict["NEIGHBOR_IP"] = item["switch"]["NEIGHBOR_IP"]

            nbr_dict["NEIGHBOR_ASN"] = item["switch"]["NEIGHBOR_ASN"]

            if item["user"]["ipv6_addr"]:
                nbr_dict["IPV6_MASK"] = item["user"]["ipv6_addr"]
            else:
                nbr_dict["IPV6_MASK"] = item["switch"]["IPV6_MASK"]

            if item["user"]["neighbor_ipv6"]:
                nbr_dict["IPV6_NEIGHBOR"] = item["user"]["neighbor_ipv6"]
            else:
                nbr_dict["IPV6_NEIGHBOR"] = item["switch"]["IPV6_NEIGHBOR"]

            nbr_dict["AUTO_VRF_LITE_FLAG"] = item["switch"]["AUTO_VRF_LITE_FLAG"]

            if item["user"]["peer_vrf"]:
                nbr_dict["PEER_VRF_NAME"] = item["user"]["peer_vrf"]
            else:
                nbr_dict["PEER_VRF_NAME"] = item["switch"]["PEER_VRF_NAME"]

            nbr_dict["VRF_LITE_JYTHON_TEMPLATE"] = "Ext_VRF_Lite_Jython"
            vrflite_con: dict = {}
            vrflite_con["VRF_LITE_CONN"] = []
            vrflite_con["VRF_LITE_CONN"].append(copy.deepcopy(nbr_dict))
            if extension_values["VRF_LITE_CONN"]:
                extension_values["VRF_LITE_CONN"]["VRF_LITE_CONN"].extend(
                    vrflite_con["VRF_LITE_CONN"]
                )
            else:
                extension_values["VRF_LITE_CONN"] = vrflite_con

            ms_con: dict = {}
            ms_con["MULTISITE_CONN"] = []
            extension_values["MULTISITE_CONN"] = json.dumps(ms_con)

        extension_values["VRF_LITE_CONN"] = json.dumps(
            extension_values["VRF_LITE_CONN"]
        )
        vrf_attach["extensionValues"] = json.dumps(extension_values).replace(" ", "")
        if vrf_attach.get("vrf_lite") is not None:
            del vrf_attach["vrf_lite"]

        msg = "Returning modified vrf_attach: "
        msg += f"{json.dumps(vrf_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        return copy.deepcopy(vrf_attach)

    def ip_to_serial_number(self, ip_address):
        """
        Given a switch ip_address, return the switch serial number.

        If ip_address is not found, return None.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}"
        self.log.debug(msg)

        return self.ip_sn.get(ip_address)

    def serial_number_to_ip(self, serial_number):
        """
        Given a switch serial_number, return the switch ip address.

        If serial_number is not found, return None.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}, "
        msg += f"serial_number: {serial_number}. "
        msg += f"Returning ip: {self.sn_ip.get(serial_number)}."
        self.log.debug(msg)

        return self.sn_ip.get(serial_number)

    def send_to_controller(
        self,
        action: str,
        verb: str,
        path: str,
        payload: dict,
        log_response: bool = True,
        is_rollback: bool = False,
    ):
        """
        # Summary

        Send a request to the controller.

        ## params

        -   `action`: The action to perform (create, update, delete, etc.)
        -   `verb`: The HTTP verb to use (GET, POST, PUT, DELETE)
        -   `path`: The URL path to send the request to
        -   `payload`: The payload to send with the request (None for no payload)
        -   `log_response`: If True, log the response in the result, else
            do not include the response in the result
        -   `is_rollback`: If True, attempt to rollback on failure
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}"
        self.log.debug(msg)

        msg = "TX controller: "
        msg += f"action: {action}, "
        msg += f"verb: {verb}, "
        msg += f"path: {path}, "
        msg += f"log_response: {log_response}, "
        msg += "type(payload): "
        msg += f"{type(payload)}, "
        msg += "payload: "
        msg += f"{json.dumps(payload, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if payload is not None:
            response = dcnm_send(self.module, verb, path, json.dumps(payload))
        else:
            response = dcnm_send(self.module, verb, path)

        msg = "RX controller: "
        msg += f"verb: {verb}, "
        msg += f"path: {path}, "
        msg += "response: "
        msg += f"{json.dumps(response, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = "Calling self.handle_response. "
        msg += "self.result[changed]): "
        msg += f"{self.result['changed']}"
        self.log.debug(msg)

        if log_response is True:
            self.result["response"].append(response)

        fail, self.result["changed"] = self.handle_response(response, action)

        msg = f"caller: {caller}, "
        msg += "Calling self.handle_response. DONE"
        msg += f"{self.result['changed']}"
        self.log.debug(msg)

        if fail:
            if is_rollback:
                self.failed_to_rollback = True
                return
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}, "
            msg += "Calling self.failure."
            self.log.debug(msg)
            self.failure(response)

    def update_vrf_attach_fabric_name(self, vrf_attach: dict) -> dict:
        """
        # Summary

        For multisite fabrics, replace `vrf_attach.fabric` with the name of
        the child fabric returned by `self.sn_fab[vrf_attach.serialNumber]`

        ## params

        - `vrf_attach`

        A `vrf_attach` dictionary containing the following keys:

            - `fabric` : fabric name
            - `serialNumber` : switch serial number
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        msg = "Received vrf_attach: "
        msg += f"{json.dumps(vrf_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if self.fabric_type != "MFD":
            msg = "Early return. "
            msg += f"FABRIC_TYPE {self.fabric_type} is not MFD. "
            msg += "Returning unmodified vrf_attach."
            self.log.debug(msg)
            return copy.deepcopy(vrf_attach)

        parent_fabric_name = vrf_attach.get("fabric")

        msg = f"fabric_type: {self.fabric_type}, "
        msg += "replacing parent_fabric_name "
        msg += f"({parent_fabric_name}) "
        msg += "with child fabric name."
        self.log.debug(msg)

        serial_number = vrf_attach.get("serialNumber")

        if serial_number is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "Unable to parse serial_number from vrf_attach. "
            msg += f"{json.dumps(vrf_attach, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            self.module.fail_json(msg)

        child_fabric_name = self.sn_fab[serial_number]

        if child_fabric_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "Unable to determine child fabric name for serial_number "
            msg += f"{serial_number}."
            self.log.debug(msg)
            self.module.fail_json(msg)

        msg = f"serial_number: {serial_number}, "
        msg += f"child fabric name: {child_fabric_name}. "
        self.log.debug(msg)

        vrf_attach["fabric"] = child_fabric_name

        msg += "Updated vrf_attach: "
        msg += f"{json.dumps(vrf_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        return copy.deepcopy(vrf_attach)

    def push_diff_attach(self, is_rollback=False):
        """
        # Summary

        Send diff_attach to the controller
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = f"caller {caller}, "
        msg += "ENTERED. "
        self.log.debug(msg)

        msg = "self.diff_attach PRE: "
        msg += f"{json.dumps(self.diff_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if not self.diff_attach:
            msg = "Early return. self.diff_attach is empty. "
            msg += f"{json.dumps(self.diff_attach, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            return

        new_diff_attach_list = []
        for diff_attach in self.diff_attach:
            msg = "diff_attach: "
            msg += f"{json.dumps(diff_attach, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            new_lan_attach_list = []
            for vrf_attach in diff_attach["lanAttachList"]:
                vrf_attach.update(vlan=0)

                serial_number = vrf_attach.get("serialNumber")
                ip_address = self.serial_number_to_ip(serial_number)
                msg = f"ip_address {ip_address} ({serial_number}), "
                msg += "vrf_attach: "
                msg += f"{json.dumps(vrf_attach, indent=4, sort_keys=True)}"
                self.log.debug(msg)

                vrf_attach = self.update_vrf_attach_fabric_name(vrf_attach)

                if "is_deploy" in vrf_attach:
                    del vrf_attach["is_deploy"]
                # if vrf_lite is null, delete it.
                if not vrf_attach.get("vrf_lite"):
                    if "vrf_lite" in vrf_attach:
                        del vrf_attach["vrf_lite"]
                    new_lan_attach_list.append(vrf_attach)
                    msg = f"ip_address {ip_address} ({serial_number}), "
                    msg += "deleting null vrf_lite in vrf_attach and "
                    msg += "skipping VRF Lite processing. "
                    msg += "updated vrf_attach: "
                    msg += f"{json.dumps(vrf_attach, indent=4, sort_keys=True)}"
                    self.log.debug(msg)
                    continue

                # VRF Lite processing

                msg = f"ip_address {ip_address} ({serial_number}), "
                msg += "vrf_attach.get(vrf_lite): "
                msg += f"{json.dumps(vrf_attach.get('vrf_lite'), indent=4, sort_keys=True)}"
                self.log.debug(msg)

                if not self.is_border_switch(serial_number):
                    # arobel TODO: Not covered by UT
                    msg = f"{self.class_name}.{method_name}: "
                    msg += f"caller {caller}. "
                    msg += "VRF LITE cannot be attached to "
                    msg += "non-border switch. "
                    msg += f"ip: {ip_address}, "
                    msg += f"serial number: {serial_number}"
                    self.module.fail_json(msg=msg)

                lite_objects = self.get_vrf_lite_objects(vrf_attach)

                msg = f"ip_address {ip_address} ({serial_number}), "
                msg += "lite_objects: "
                msg += f"{json.dumps(lite_objects, indent=4, sort_keys=True)}"
                self.log.debug(msg)

                if not lite_objects.get("DATA"):
                    msg = f"ip_address {ip_address} ({serial_number}), "
                    msg += "Early return, no lite objects."
                    self.log.debug(msg)
                    return

                lite = lite_objects["DATA"][0]["switchDetailsList"][0][
                    "extensionPrototypeValues"
                ]
                msg = f"ip_address {ip_address} ({serial_number}), "
                msg += "lite: "
                msg += f"{json.dumps(lite, indent=4, sort_keys=True)}"
                self.log.debug(msg)

                msg = f"ip_address {ip_address} ({serial_number}), "
                msg += "old vrf_attach: "
                msg += f"{json.dumps(vrf_attach, indent=4, sort_keys=True)}"
                self.log.debug(msg)

                vrf_attach = self.update_vrf_attach_vrf_lite_extensions(
                    vrf_attach, lite
                )
                msg = f"ip_address {ip_address} ({serial_number}), "
                msg += "new vrf_attach: "
                msg += f"{json.dumps(vrf_attach, indent=4, sort_keys=True)}"
                self.log.debug(msg)

                new_lan_attach_list.append(vrf_attach)

            msg = "Updating diff_attach[lanAttachList] with: "
            msg += f"{json.dumps(new_lan_attach_list, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            diff_attach["lanAttachList"] = copy.deepcopy(new_lan_attach_list)
            new_diff_attach_list.append(copy.deepcopy(diff_attach))

            msg = "new_diff_attach_list: "
            msg += f"{json.dumps(new_diff_attach_list, indent=4, sort_keys=True)}"
            self.log.debug(msg)

        action = "attach"
        verb = "POST"
        path = self.paths["GET_VRF"].format(self.fabric)
        attach_path = path + "/attachments"

        self.send_to_controller(
            action,
            verb,
            attach_path,
            new_diff_attach_list,
            log_response=True,
            is_rollback=is_rollback,
        )

    def push_diff_deploy(self, is_rollback=False):
        """
        # Summary

        Send diff_deploy to the controller
        """
        caller = inspect.stack()[1][3]

        msg = f"caller: {caller}. "
        msg += "ENTERED."
        self.log.debug(msg)

        if not self.diff_deploy:
            msg = "Early return. self.diff_deploy is empty."
            self.log.debug(msg)
            return

        action = "deploy"
        verb = "POST"
        path = self.paths["GET_VRF"].format(self.fabric)
        deploy_path = path + "/deployments"

        self.send_to_controller(
            action,
            verb,
            deploy_path,
            self.diff_deploy,
            log_response=True,
            is_rollback=is_rollback,
        )

    def release_resources_by_id(self, id_list=None):
        """
        # Summary

        Given a list of resource IDs, send a request to the controller
        to release them.
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = f"caller: {caller}. "
        msg += "ENTERED."
        self.log.debug(msg)

        if id_list is None:
            msg = "Early return. id_list is empty."
            self.log.debug(msg)
            return

        if not isinstance(id_list, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "id_list must be a list of resource IDs. "
            msg += f"Got: {id_list}."
            self.module.fail_json(msg)

        try:
            id_list = [int(x) for x in id_list]
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "id_list must be a list of resource IDs. "
            msg += "Where each id is convertable to integer."
            msg += f"Got: {id_list}. "
            msg += f"Error detail: {error}"
            self.module.fail_json(msg)

        # The controller can release only around 500-600 IDs per
        # request (not sure of the exact number).  We break up
        # requests into smaller lists here.  In practice, we'll
        # likely ever only have one resulting list.
        id_list_of_lists = self.get_list_of_lists([str(x) for x in id_list], 512)

        for item in id_list_of_lists:
            msg = "Releasing resource IDs: "
            msg += f"{','.join(item)}"
            self.log.debug(msg)

            action = "deploy"
            path = "/appcenter/cisco/ndfc/api/v1/lan-fabric"
            path += "/rest/resource-manager/resources"
            path += f"?id={','.join(item)}"
            verb = "DELETE"
            self.send_to_controller(action, verb, path, None, log_response=False)

    def release_orphaned_resources(self, vrf_del_list, is_rollback=False):
        """
        # Summary

        Release orphaned resources.

        ## Description

        After a VRF delete operation, resources such as the TOP_DOWN_VRF_VLAN
        resource below, can be orphaned from their VRFs.  Below, notice that
        resourcePool.vrfName is null.  This method releases resources if
        the following are true for the resources:

        - allocatedFlag is False
        - entityName == vrf
        - fabricName == self.fabric
        - switchName is not None
        - ipAddress is not None

        ```json
        [
            {
                "id": 36368,
                "resourcePool": {
                    "id": 0,
                    "poolName": "TOP_DOWN_VRF_VLAN",
                    "fabricName": "f1",
                    "vrfName": null,
                    "poolType": "ID_POOL",
                    "dynamicSubnetRange": null,
                    "targetSubnet": 0,
                    "overlapAllowed": false,
                    "hierarchicalKey": "f1"
                },
                "entityType": "Device",
                "entityName": "VRF_1",
                "allocatedIp": "201",
                "allocatedOn": 1734040978066,
                "allocatedFlag": false,
                "allocatedScopeValue": "FDO211218GC",
                "ipAddress": "172.22.150.103",
                "switchName": "cvd-1312-leaf",
                "hierarchicalKey": "0"
            }
        ]
        ```
        """
        self.log.debug("ENTERED")

        path = "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/"
        path += f"resource-manager/fabric/{self.fabric}/"
        resource_pool = ["TOP_DOWN_VRF_VLAN", "TOP_DOWN_L3_DOT1Q"]
        for pool in resource_pool:
            msg = f"Processing orphaned resources in pool:{pool}"
            self.log.debug(msg)
            req_path = path + f"pools/{pool}"
            resp = dcnm_send(self.module, "GET", req_path)
            self.result["response"].append(resp)
            fail, self.result["changed"] = self.handle_response(resp, "deploy")
            if fail:
                if is_rollback:
                    self.failed_to_rollback = True
                    return
                self.failure(resp)

            delete_ids = []
            for item in resp["DATA"]:
                if "entityName" not in item:
                    continue
                if item["entityName"] not in vrf_del_list:
                    continue
                if item.get("allocatedFlag") is not False:
                    continue
                if item.get("id") is None:
                    continue
                # Resources with no ipAddress or switchName
                # are invalid and of Fabric's scope and
                # should not be attempted to be deleted here.
                if not item.get("ipAddress"):
                    continue
                if not item.get("switchName"):
                    continue

                msg = f"item {json.dumps(item, indent=4, sort_keys=True)}"
                self.log.debug(msg)

                delete_ids.append(item["id"])

            if len(delete_ids) == 0:
                return
            msg = f"Releasing orphaned resources with IDs:{delete_ids}"
            self.log.debug(msg)
            self.release_resources_by_id(delete_ids)

    def push_to_remote(self, is_rollback=False):
        """
        # Summary

        Send all diffs to the controller
        """
        caller = inspect.stack()[1][3]
        msg = "ENTERED. "
        msg += f"caller: {caller}."
        self.log.debug(msg)

        self.push_diff_create_update(is_rollback)

        # The detach and un-deploy operations are executed before the
        # create,attach and deploy to address cases where a VLAN for vrf
        # attachment being deleted is re-used on a new vrf attachment being
        # created. This is needed specially for state: overridden

        for vrf_name in self.diff_delete:
            path = self.paths["GET_NET_VRF"].format(self.fabric, vrf_name)
            resp = dcnm_send(self.module, "GET", path)
            if resp.get("DATA") is None:
                msg = f"Invalid Response from Controller. {resp}"
                self.module.fail_json(msg=msg)
            elif resp["DATA"] != []:
                msg = f"{vrf_name} in fabric: {self.fabric} has associated network attachments. "
                self.log.debug("%s. Number of networks: %d", msg, len(resp['DATA']))
                msg += "Please remove the network attachments "
                msg += "before deleting the VRF. (maybe using dcnm_network module)"
                self.module.fail_json(msg=msg)

        self.push_diff_detach(is_rollback)
        self.push_diff_undeploy(is_rollback)

        msg = "Calling self.push_diff_delete"
        self.log.debug(msg)

        self.push_diff_delete(is_rollback)

        vrf_del_list = []
        for vrf_name in self.diff_delete:
            vrf_del_list.append(vrf_name)
        if vrf_del_list:
            msg += f"VRF(s) to be deleted: {vrf_del_list}."
            self.release_orphaned_resources(vrf_del_list, is_rollback)

        self.push_diff_create(is_rollback)
        self.push_diff_attach(is_rollback)
        self.push_diff_deploy(is_rollback)

    def wait_for_vrf_del_ready(self, vrf_name="not_supplied"):
        """
        # Summary

        Wait for VRFs to be ready for deletion.

        ## Raises

        Calls fail_json if VRF has associated network attachments.
        """
        caller = inspect.stack()[1][3]
        msg = "ENTERED. "
        msg += f"caller: {caller}, "
        msg += f"vrf_name: {vrf_name}"
        self.log.debug(msg)

        for vrf in self.diff_delete:
            ok_to_delete = False
            path = self.paths["GET_VRF_ATTACH"].format(self.fabric, vrf)
            retry_count = max(100 // self.WAIT_TIME_FOR_DELETE_LOOP, 1)
            while not ok_to_delete:
                resp = dcnm_send(self.module, "GET", path)
                ok_to_delete = True
                if resp.get("DATA") is None:
                    time.sleep(self.WAIT_TIME_FOR_DELETE_LOOP)
                    continue

                attach_list = resp["DATA"][0]["lanAttachList"]
                msg = f"ok_to_delete: {ok_to_delete}, "
                msg += f"attach_list: {json.dumps(attach_list, indent=4)}"
                self.log.debug(msg)

                for attach in attach_list:
                    if (
                        attach["lanAttachState"] == "OUT-OF-SYNC"
                        or attach["lanAttachState"] == "FAILED"
                    ):
                        self.diff_delete.update({vrf: "OUT-OF-SYNC"})
                        break
                    if attach["lanAttachState"] != "NA":
                        time.sleep(self.WAIT_TIME_FOR_DELETE_LOOP)
                        self.diff_delete.update({vrf: "DEPLOYED"})
                        ok_to_delete = False
                        break
                    self.diff_delete.update({vrf: "NA"})
                if retry_count <= 0:
                    msg = "Timeout waiting for VRF to be ready for deletion. "
                    msg += f"vrf: {vrf}, "
                    msg += f"resp: {resp}"
                    self.module.fail_json(msg=msg)
                retry_count -= 1

    def attach_spec(self):
        """
        # Summary

        Return the argument spec for network attachments
        """
        spec = {}
        spec["deploy"] = {"default": True, "type": "bool"}
        spec["ip_address"] = {"required": True, "type": "str"}
        spec["import_evpn_rt"] = {"default": "", "type": "str"}
        spec["export_evpn_rt"] = {"default": "", "type": "str"}

        if self.state in ("merged", "overridden", "replaced"):
            spec["vrf_lite"] = {"type": "list"}
        else:
            spec["vrf_lite"] = {"default": [], "type": "list"}

        return copy.deepcopy(spec)

    def lite_spec(self):
        """
        # Summary

        Return the argument spec for VRF LITE parameters
        """
        spec = {}
        spec["dot1q"] = {"type": "int"}
        spec["ipv4_addr"] = {"type": "ipv4_subnet"}
        spec["ipv6_addr"] = {"type": "ipv6"}
        spec["neighbor_ipv4"] = {"type": "ipv4"}
        spec["neighbor_ipv6"] = {"type": "ipv6"}
        spec["peer_vrf"] = {"type": "str"}

        if self.state in ("merged", "overridden", "replaced"):
            spec["interface"] = {"required": True, "type": "str"}
        else:
            spec["interface"] = {"type": "str"}

        return copy.deepcopy(spec)

    def vrf_spec(self):
        """
        # Summary

        Return the argument spec for VRF parameters
        """
        spec = {}
        spec["adv_default_routes"] = {"default": True, "type": "bool"}
        spec["adv_host_routes"] = {"default": False, "type": "bool"}

        spec["attach"] = {"type": "list"}
        spec["bgp_password"] = {"default": "", "type": "str"}
        spec["bgp_passwd_encrypt"] = {"choices": [3, 7], "default": 3, "type": "int"}
        spec["disable_rt_auto"] = {"default": False, "type": "bool"}

        spec["export_evpn_rt"] = {"default": "", "type": "str"}
        spec["export_mvpn_rt"] = {"default": "", "type": "str"}
        spec["export_vpn_rt"] = {"default": "", "type": "str"}

        spec["import_evpn_rt"] = {"default": "", "type": "str"}
        spec["import_mvpn_rt"] = {"default": "", "type": "str"}
        spec["import_vpn_rt"] = {"default": "", "type": "str"}

        spec["ipv6_linklocal_enable"] = {"default": True, "type": "bool"}

        spec["l3vni_wo_vlan"] = {"default": self.fabric_l3vni_wo_vlan, "type": "bool"}
        spec["loopback_route_tag"] = {
            "default": 12345,
            "range_max": 4294967295,
            "type": "int",
        }
        spec["max_bgp_paths"] = {
            "default": 1,
            "range_max": 64,
            "range_min": 1,
            "type": "int",
        }
        spec["max_ibgp_paths"] = {
            "default": 2,
            "range_max": 64,
            "range_min": 1,
            "type": "int",
        }
        spec["netflow_enable"] = {"default": False, "type": "bool"}
        spec["nf_monitor"] = {"default": "", "type": "str"}

        spec["no_rp"] = {"default": False, "type": "bool"}
        spec["overlay_mcast_group"] = {"default": "", "type": "str"}

        spec["redist_direct_rmap"] = {
            "default": "FABRIC-RMAP-REDIST-SUBNET",
            "type": "str",
        }
        spec["v6_redist_direct_rmap"] = {
            "default": "FABRIC-RMAP-REDIST-SUBNET",
            "type": "str",
        }
        spec["rp_address"] = {"default": "", "type": "str"}
        spec["rp_external"] = {"default": False, "type": "bool"}
        spec["rp_loopback_id"] = {"default": "", "range_max": 1023, "type": "int"}

        spec["service_vrf_template"] = {"default": None, "type": "str"}
        spec["source"] = {"default": None, "type": "str"}
        spec["static_default_route"] = {"default": True, "type": "bool"}

        spec["trm_bgw_msite"] = {"default": False, "type": "bool"}
        spec["trm_enable"] = {"default": False, "type": "bool"}

        spec["underlay_mcast_ip"] = {"default": "", "type": "str"}

        spec["vlan_id"] = {"range_max": 4094, "type": "int"}
        spec["vrf_description"] = {"default": "", "type": "str"}
        spec["vrf_id"] = {"range_max": 16777214, "type": "int"}
        spec["vrf_intf_desc"] = {"default": "", "type": "str"}
        spec["vrf_int_mtu"] = {
            "default": 9216,
            "range_max": 9216,
            "range_min": 68,
            "type": "int",
        }
        spec["vrf_name"] = {"length_max": 32, "required": True, "type": "str"}
        spec["vrf_template"] = {"default": "Default_VRF_Universal", "type": "str"}
        spec["vrf_extension_template"] = {
            "default": "Default_VRF_Extension_Universal",
            "type": "str",
        }
        spec["vrf_vlan_name"] = {"default": "", "type": "str"}

        if self.state in ("merged", "overridden", "replaced"):
            spec["deploy"] = {"default": True, "type": "bool"}
        else:
            spec["deploy"] = {"type": "bool"}

        return copy.deepcopy(spec)

    def validate_input(self):
        """Parse the playbook values, validate to param specs."""
        method_name = inspect.stack()[0][3]
        self.log.debug("ENTERED")

        attach_spec = self.attach_spec()
        lite_spec = self.lite_spec()
        vrf_spec = self.vrf_spec()

        msg = "attach_spec: "
        msg += f"{json.dumps(attach_spec, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = "lite_spec: "
        msg += f"{json.dumps(lite_spec, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = "vrf_spec: "
        msg += f"{json.dumps(vrf_spec, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if self.state in ("merged", "overridden", "replaced"):
            fail_msg_list = []
            if self.config:
                for vrf in self.config:
                    msg = f"state {self.state}: "
                    msg += "self.config[vrf]: "
                    msg += f"{json.dumps(vrf, indent=4, sort_keys=True)}"
                    self.log.debug(msg)
                    # A few user provided vrf parameters need special handling
                    # Ignore user input for src and hard code it to None
                    vrf["source"] = None
                    if not vrf.get("service_vrf_template"):
                        vrf["service_vrf_template"] = None

                    if "vrf_name" not in vrf:
                        fail_msg_list.append(
                            "vrf_name is mandatory under vrf parameters"
                        )

                    if isinstance(vrf.get("attach"), list):
                        for attach in vrf["attach"]:
                            if "ip_address" not in attach:
                                fail_msg_list.append(
                                    "ip_address is mandatory under attach parameters"
                                )
            else:
                if self.state in ("merged", "replaced"):
                    msg = f"config element is mandatory for {self.state} state"
                    fail_msg_list.append(msg)

            if fail_msg_list:
                msg = f"{self.class_name}.{method_name}: "
                msg += ",".join(fail_msg_list)
                self.module.fail_json(msg=msg)

            if self.config:
                valid_vrf, invalid_params = validate_list_of_dicts(
                    self.config, vrf_spec
                )
                for vrf in valid_vrf:

                    msg = f"state {self.state}: "
                    msg += "valid_vrf[vrf]: "
                    msg += f"{json.dumps(vrf, indent=4, sort_keys=True)}"
                    self.log.debug(msg)

                    if vrf.get("attach"):
                        for entry in vrf.get("attach"):
                            entry["deploy"] = vrf["deploy"]
                        valid_att, invalid_att = validate_list_of_dicts(
                            vrf["attach"], attach_spec
                        )
                        msg = f"state {self.state}: "
                        msg += "valid_att: "
                        msg += f"{json.dumps(valid_att, indent=4, sort_keys=True)}"
                        self.log.debug(msg)
                        vrf["attach"] = valid_att

                        invalid_params.extend(invalid_att)
                        for lite in vrf.get("attach"):
                            if lite.get("vrf_lite"):
                                valid_lite, invalid_lite = validate_list_of_dicts(
                                    lite["vrf_lite"], lite_spec
                                )
                                msg = f"state {self.state}: "
                                msg += "valid_lite: "
                                msg += f"{json.dumps(valid_lite, indent=4, sort_keys=True)}"
                                self.log.debug(msg)

                                msg = f"state {self.state}: "
                                msg += "invalid_lite: "
                                msg += f"{json.dumps(invalid_lite, indent=4, sort_keys=True)}"
                                self.log.debug(msg)

                                lite["vrf_lite"] = valid_lite
                                invalid_params.extend(invalid_lite)
                    self.validated.append(vrf)

                if invalid_params:
                    # arobel: TODO: Not in UT
                    msg = f"{self.class_name}.{method_name}: "
                    msg += "Invalid parameters in playbook: "
                    msg += f"{','.join(invalid_params)}"
                    self.module.fail_json(msg=msg)

        else:

            if self.config:
                valid_vrf, invalid_params = validate_list_of_dicts(
                    self.config, vrf_spec
                )
                for vrf in valid_vrf:
                    if vrf.get("attach"):
                        valid_att, invalid_att = validate_list_of_dicts(
                            vrf["attach"], attach_spec
                        )
                        vrf["attach"] = valid_att
                        invalid_params.extend(invalid_att)
                        for lite in vrf.get("attach"):
                            if lite.get("vrf_lite"):
                                valid_lite, invalid_lite = validate_list_of_dicts(
                                    lite["vrf_lite"], lite_spec
                                )
                                msg = f"state {self.state}: "
                                msg += "valid_lite: "
                                msg += f"{json.dumps(valid_lite, indent=4, sort_keys=True)}"
                                self.log.debug(msg)

                                msg = f"state {self.state}: "
                                msg += "invalid_lite: "
                                msg += f"{json.dumps(invalid_lite, indent=4, sort_keys=True)}"
                                self.log.debug(msg)

                                lite["vrf_lite"] = valid_lite
                                invalid_params.extend(invalid_lite)
                    self.validated.append(vrf)

                if invalid_params:
                    # arobel: TODO: Not in UT
                    msg = f"{self.class_name}.{method_name}: "
                    msg += "Invalid parameters in playbook: "
                    msg += f"{','.join(invalid_params)}"
                    self.module.fail_json(msg=msg)

    def handle_response(self, res, op):
        self.log.debug("ENTERED")

        fail = False
        changed = True

        if op == "query_dcnm":
            # These if blocks handle responses to the query APIs.
            # Basically all GET operations.
            if res.get("ERROR") == "Not Found" and res["RETURN_CODE"] == 404:
                return True, False
            if res["RETURN_CODE"] != 200 or res["MESSAGE"] != "OK":
                return False, True
            return False, False

        # Responses to all other operations POST and PUT are handled here.
        if res.get("MESSAGE") != "OK" or res["RETURN_CODE"] != 200:
            fail = True
            changed = False
            return fail, changed
        if res.get("ERROR"):
            fail = True
            changed = False
        if res.get("DATA"):
            resp_val = search_nested_json(res.get("DATA"), "fail")
            if resp_val:
                fail = True
                changed = False
        if op == "attach" and "is in use already" in str(res.values()):
            fail = True
            changed = False
        if op == "deploy" and "No switches PENDING for deployment" in str(res.values()):
            changed = False

        return fail, changed

    def failure(self, resp):
        # Do not Rollback for Multi-site fabrics
        if self.fabric_type == "MFD":
            self.failed_to_rollback = True
            self.module.fail_json(msg=resp)
            return

        # Implementing a per task rollback logic here so that we rollback
        # to the have state whenever there is a failure in any of the APIs.
        # The idea would be to run overridden state with want=have and have=dcnm_state
        self.want_create = self.have_create
        self.want_attach = self.have_attach
        self.want_deploy = self.have_deploy

        self.have_create = []
        self.have_attach = []
        self.have_deploy = {}
        self.get_have()
        self.get_diff_override()

        self.push_to_remote(True)

        if self.failed_to_rollback:
            msg1 = "FAILED - Attempted rollback of the task has failed, "
            msg1 += "may need manual intervention"
        else:
            msg1 = "SUCCESS - Attempted rollback of the task has succeeded"

        res = copy.deepcopy(resp)
        res.update({"ROLLBACK_RESULT": msg1})

        if not resp.get("DATA"):
            data = copy.deepcopy(resp.get("DATA"))
            if data.get("stackTrace"):
                data.update(
                    {"stackTrace": "Stack trace is hidden, use '-vvvvv' to print it"}
                )
                res.update({"DATA": data})

        # pylint: disable=protected-access
        if self.module._verbosity >= 5:
            self.module.fail_json(msg=res)
        # pylint: enable=protected-access

        self.module.fail_json(msg=res)


def main():
    """main entry point for module execution"""

    # Logging setup
    try:
        log = Log()
        log.commit()
    except (TypeError, ValueError):
        pass

    element_spec = dict(
        fabric=dict(required=True, type="str"),
        config=dict(required=False, type="list", elements="dict"),
        state=dict(
            default="merged",
            choices=["merged", "replaced", "deleted", "overridden", "query"],
        ),
    )

    module = AnsibleModule(argument_spec=element_spec, supports_check_mode=True)

    dcnm_vrf = DcnmVrf(module)

    if not dcnm_vrf.ip_sn:
        msg = f"Fabric {dcnm_vrf.fabric} missing on the controller or "
        msg += "does not have any switches"
        module.fail_json(msg=msg)

    dcnm_vrf.validate_input()

    dcnm_vrf.get_want()
    dcnm_vrf.get_have()

    if module.params["state"] == "merged":
        dcnm_vrf.get_diff_merge()

    if module.params["state"] == "replaced":
        dcnm_vrf.get_diff_replace()

    if module.params["state"] == "overridden":
        dcnm_vrf.get_diff_override()

    if module.params["state"] == "deleted":
        dcnm_vrf.get_diff_delete()

    if module.params["state"] == "query":
        dcnm_vrf.get_diff_query()
        dcnm_vrf.result["response"] = dcnm_vrf.query

    dcnm_vrf.format_diff()
    dcnm_vrf.result["diff"] = dcnm_vrf.diff_input_format

    if (
        dcnm_vrf.diff_create
        or dcnm_vrf.diff_attach
        or dcnm_vrf.diff_detach
        or dcnm_vrf.diff_deploy
        or dcnm_vrf.diff_undeploy
        or dcnm_vrf.diff_delete
        or dcnm_vrf.diff_create_quick
        or dcnm_vrf.diff_create_update
    ):
        dcnm_vrf.result["changed"] = True
    else:
        module.exit_json(**dcnm_vrf.result)

    if module.check_mode:
        dcnm_vrf.result["changed"] = False
        msg = f"dcnm_vrf.result: {dcnm_vrf.result}"
        dcnm_vrf.log.debug(msg)
        module.exit_json(**dcnm_vrf.result)

    dcnm_vrf.push_to_remote()

    msg = f"dcnm_vrf.result: {dcnm_vrf.result}"
    dcnm_vrf.log.debug(msg)
    module.exit_json(**dcnm_vrf.result)


if __name__ == "__main__":
    main()
