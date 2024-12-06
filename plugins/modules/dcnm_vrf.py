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
        type: str
        required: false
      vrf_intf_desc:
        description:
        - VRF Intf Description
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
        type: bool
        required: false
        default: true
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
    get_ip_sn_fabric_dict, validate_list_of_dicts)

# from ..module_utils.common.controller_version import ControllerVersion
from ..module_utils.common.log_v2 import Log

# from ..module_utils.common.response_handler import ResponseHandler
# from ..module_utils.common.rest_send_v2 import RestSend
# from ..module_utils.common.results import Results
# from ..module_utils.common.sender_dcnm import Sender
# from ..module_utils.fabric.fabric_details_v2 import FabricDetailsByName


class DcnmVrf:

    dcnm_vrf_paths = {
        11: {
            "GET_VRF": "/rest/top-down/fabrics/{}/vrfs",
            "GET_VRF_ATTACH": "/rest/top-down/fabrics/{}/vrfs/attachments?vrf-names={}",
            "GET_VRF_SWITCH": "/rest/top-down/fabrics/{}/vrfs/switches?vrf-names={}&serial-numbers={}",
            "GET_VRF_ID": "/rest/managed-pool/fabrics/{}/partitions/ids",
            "GET_VLAN": "/rest/resource-manager/vlan/{}?vlanUsageType=TOP_DOWN_VRF_VLAN",
        },
        12: {
            "GET_VRF": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/vrfs",
            "GET_VRF_ATTACH": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/vrfs/attachments?vrf-names={}",
            "GET_VRF_SWITCH": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/vrfs/switches?vrf-names={}&serial-numbers={}",
            "GET_VRF_ID": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/vrfinfo",
            "GET_VLAN": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/resource-manager/vlan/{}?vlanUsageType=TOP_DOWN_VRF_VLAN",
        },
    }

    def __init__(self, module):
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.module = module
        self.params = module.params
        self.fabric = module.params["fabric"]
        self.config = copy.deepcopy(module.params.get("config"))
        self.check_mode = False
        self.have_create = []
        self.want_create = []
        self.diff_create = []
        self.diff_create_update = []
        # This variable is created specifically to hold all the create payloads which are missing a
        # vrfId. These payloads are sent to DCNM out of band (basically in the get_diff_merge())
        # We lose diffs for these without this variable. The content stored here will be helpful for
        # cases like "check_mode" and to print diffs[] in the output of each task.
        self.diff_create_quick = []
        self.have_attach = []
        self.want_attach = []
        self.diff_attach = []
        self.validated = []
        # diff_detach is to list all attachments of a vrf being deleted, especially for state: OVERRIDDEN
        # The diff_detach and delete operations have to happen before create+attach+deploy for vrfs being created.
        # This is specifically to address cases where VLAN from a vrf which is being deleted is used for another
        # vrf. Without this additional logic, the create+attach+deploy go out first and complain the VLAN is already
        # in use.
        self.diff_detach = []
        self.have_deploy = {}
        self.want_deploy = {}
        self.diff_deploy = {}
        self.diff_undeploy = {}
        self.diff_delete = {}
        self.diff_input_format = []
        self.query = []
        self.dcnm_version = dcnm_version_supported(self.module)
        self.inventory_data = get_fabric_inventory_details(self.module, self.fabric)
        self.ip_sn, self.hn_sn = get_ip_sn_dict(self.inventory_data)
        self.fabric_data = get_fabric_details(self.module, self.fabric)
        self.fabric_type = self.fabric_data.get("fabricType")
        self.ip_fab, self.sn_fab = get_ip_sn_fabric_dict(self.inventory_data)
        if self.dcnm_version > 12:
            self.paths = self.dcnm_vrf_paths[12]
        else:
            self.paths = self.dcnm_vrf_paths[self.dcnm_version]

        self.result = {"changed": False, "diff": [], "response": []}

        self.failed_to_rollback = False
        self.WAIT_TIME_FOR_DELETE_LOOP = 5  # in seconds

        msg = f"{self.class_name}.__init__(): DONE"
        self.log.debug(msg)

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
        value = dict_with_key.get(key)
        if value in ["false", "False", False]:
            return False
        if value in ["true", "True", True]:
            return True

        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"caller: {caller}: "
        msg = f"{str(value)} with type {type(value)} "
        msg += "is not convertable to boolean"
        self.module.fail_json(msg=msg)

    @staticmethod
    def compare_properties(dict1, dict2, property_list):
        """
        Given two dictionaries and a list of keys:

        - Return True if all property values match.
        - Return False otherwise
        """
        for prop in property_list:
            if dict1.get(prop) != dict2.get(prop):
                return False
        return True

    def diff_for_attach_deploy(self, want_a, have_a, replace=False):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
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
                            {"freeformConfig": have["freeformConfig"]}
                        )  # copy freeformConfig from have as module is not managing it
                        want_inst_values = {}
                        have_inst_values = {}
                        if (
                            want["instanceValues"] is not None
                            and have["instanceValues"] is not None
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

                            vrf_lite_properties = [
                                "DOT1Q_ID",
                                "IP_MASK",
                                "IPV6_MASK",
                                "IPV6_NEIGHBOR",
                                "NEIGHBOR_IP",
                                "PEER_VRF_NAME",
                            ]
                            for wlite in want_e["VRF_LITE_CONN"]:
                                for hlite in have_e["VRF_LITE_CONN"]:
                                    found = False
                                    interface_match = False
                                    if wlite["IF_NAME"] != hlite["IF_NAME"]:
                                        continue
                                    found = True
                                    interface_match = True
                                    if not self.compare_properties(
                                        wlite, hlite, vrf_lite_properties
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
                            want_is_deploy = self.to_bool("is_deploy", want)
                            have_is_deploy = self.to_bool("is_deploy", have)

                            want_is_attached = self.to_bool("isAttached", want)
                            have_is_attached = self.to_bool("isAttached", have)

                            if have_is_attached != want_is_attached:

                                if "isAttached" in want:
                                    del want["isAttached"]

                                want["deployment"] = True
                                attach_list.append(want)
                                if want_is_deploy is True:
                                    deploy_vrf = True
                                continue

                            want_deployment = self.to_bool("deployment", want)
                            have_deployment = self.to_bool("deployment", have)

                            if (want_deployment != have_deployment) or (
                                want_is_deploy != have_is_deploy
                            ):
                                if want_is_deploy is True:
                                    deploy_vrf = True

                        if self.dict_values_differ(want_inst_values, have_inst_values):
                            found = False

                        if found:
                            break

                    if interface_match and not found:
                        break

            if not found:
                if self.to_bool("isAttached", want):
                    del want["isAttached"]
                    want["deployment"] = True
                    attach_list.append(want)
                    if self.to_bool("is_deploy", want):
                        deploy_vrf = True

        msg = f"{self.class_name}.{method_name}: "
        msg += f"deploy_vrf: {deploy_vrf}, "
        msg += f"attach_list: {json.dumps(attach_list, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        return attach_list, deploy_vrf

    def update_attach_params(self, attach, vrf_name, deploy, vlanId):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
        self.log.debug(msg)

        vrf_ext = False

        if not attach:
            return {}

        serial = ""
        attach["ip_address"] = dcnm_get_ip_addr_info(
            self.module, attach["ip_address"], None, None
        )
        for ip, ser in self.ip_sn.items():
            if ip == attach["ip_address"]:
                serial = ser

        if not serial:
            msg = f"Fabric {self.fabric} does not contain switch "
            msg += f"{attach['ip_address']}"
            self.module.fail_json(msg=msg)

        role = self.inventory_data[attach["ip_address"]].get("switchRole")

        if role.lower() in ("spine", "super spine"):
            msg = f"VRFs cannot be attached to switch {attach['ip_address']} "
            msg += f"with role {role}"
            self.module.fail_json(msg=msg)

        ext_values = {}
        ext_values["VRF_LITE_CONN"] = []
        ms_con = {}
        ms_con["MULTISITE_CONN"] = []
        ext_values["MULTISITE_CONN"] = json.dumps(ms_con)

        if attach["vrf_lite"]:
            # Before applying the vrf_lite config, verify that the switch role
            # begins with border
            if not re.search(r"\bborder\b", role.lower()):
                msg = f"VRF LITE cannot be attached to switch {attach['ip_address']} "
                msg += f"with role {role}"
                self.module.fail_json(msg=msg)

            for item in attach["vrf_lite"]:
                if (
                    item["interface"]
                    or item["dot1q"]
                    or item["ipv4_addr"]
                    or item["neighbor_ipv4"]
                    or item["ipv6_addr"]
                    or item["neighbor_ipv6"]
                    or item["peer_vrf"]
                ):

                    # If the playbook contains vrf lite elements add the
                    # extension values
                    nbr_dict = {}
                    if item["interface"]:
                        nbr_dict["IF_NAME"] = item["interface"]
                    else:
                        nbr_dict["IF_NAME"] = ""

                    if item["dot1q"]:
                        nbr_dict["DOT1Q_ID"] = str(item["dot1q"])
                    else:
                        nbr_dict["DOT1Q_ID"] = ""

                    if item["ipv4_addr"]:
                        nbr_dict["IP_MASK"] = item["ipv4_addr"]
                    else:
                        nbr_dict["IP_MASK"] = ""

                    if item["neighbor_ipv4"]:
                        nbr_dict["NEIGHBOR_IP"] = item["neighbor_ipv4"]
                    else:
                        nbr_dict["NEIGHBOR_IP"] = ""

                    if item["ipv6_addr"]:
                        nbr_dict["IPV6_MASK"] = item["ipv6_addr"]
                    else:
                        nbr_dict["IPV6_MASK"] = ""

                    if item["neighbor_ipv6"]:
                        nbr_dict["IPV6_NEIGHBOR"] = item["neighbor_ipv6"]
                    else:
                        nbr_dict["IPV6_NEIGHBOR"] = ""

                    if item["peer_vrf"]:
                        nbr_dict["PEER_VRF_NAME"] = item["peer_vrf"]
                    else:
                        nbr_dict["PEER_VRF_NAME"] = ""

                    nbr_dict["VRF_LITE_JYTHON_TEMPLATE"] = "Ext_VRF_Lite_Jython"

                    msg = f"{self.class_name}.update_attach_params: "
                    msg += f"nbr_dict: {json.dumps(nbr_dict, indent=4, sort_keys=True)}"
                    self.log.debug(msg)

                    vrflite_con = {}
                    vrflite_con["VRF_LITE_CONN"] = []
                    vrflite_con["VRF_LITE_CONN"].append(copy.deepcopy(nbr_dict))

                    if ext_values["VRF_LITE_CONN"]:
                        ext_values["VRF_LITE_CONN"]["VRF_LITE_CONN"].extend(
                            vrflite_con["VRF_LITE_CONN"]
                        )
                    else:
                        ext_values["VRF_LITE_CONN"] = vrflite_con

            ext_values["VRF_LITE_CONN"] = json.dumps(ext_values["VRF_LITE_CONN"])

            vrf_ext = True

        attach.update({"fabric": self.fabric})
        attach.update({"vrfName": vrf_name})
        attach.update({"vlan": vlanId})
        # This flag is not to be confused for deploy of attachment.
        # "deployment" should be set True for attaching an attachment
        # and set to False for detaching an attachment
        attach.update({"deployment": True})
        attach.update({"isAttached": True})
        attach.update({"serialNumber": serial})
        attach.update({"is_deploy": deploy})
        if vrf_ext:
            attach.update({"extensionValues": json.dumps(ext_values).replace(" ", "")})
        else:
            attach.update({"extensionValues": ""})
        # freeformConfig, loopbackId, loopbackIpAddress, and loopbackIpV6Address
        # will be copied from have
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

        msg = f"{self.class_name}.{method_name}: "
        msg += f"attach: {json.dumps(attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        return attach

    def dict_values_differ(self, dict1, dict2, skip_keys=None) -> bool:
        """
        # Summary

        Given a two dictionaries and, optionally, a list of keys to skip:

        -   Return True if the values for any (non-skipped) keys differs.
        -   Return False otherwise
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
        self.log.debug(msg)

        if skip_keys is None:
            skip_keys = []

        for key in dict1.keys():
            if key in skip_keys:
                continue
            dict1_value = str(dict1[key]).lower()
            dict2_value = str(dict2[key]).lower()
            if dict1_value != dict2_value:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Values differ: key {key} "
                msg += f"dict1_value {dict1_value} != dict2_value {dict2_value}. "
                msg += "returning True"
                self.log.debug(msg)
                return True
        return False

    def diff_for_create(self, want, have):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
        self.log.debug(msg)

        conf_changed = False
        if not have:
            return {}

        create = {}

        json_to_dict_want = json.loads(want["vrfTemplateConfig"])
        json_to_dict_have = json.loads(have["vrfTemplateConfig"])

        vlanId_want = str(json_to_dict_want.get("vrfVlanId", ""))

        if vlanId_want != "0":

            templates_differ = self.dict_values_differ(
                json_to_dict_want, json_to_dict_have
            )

            msg = f"{self.class_name}.{method_name}: "
            msg += f"templates_differ: {templates_differ}, vlanId_want: {vlanId_want}"
            self.log.debug(msg)

            if want["vrfId"] is not None and have["vrfId"] != want["vrfId"]:
                msg = f"{self.class_name}.diff_for_create: "
                msg += f"vrf_id for vrf {want['vrfName']} cannot be updated to "
                msg += "a different value"
                self.module.fail_json(msg)

            elif templates_differ:
                conf_changed = True
                if want["vrfId"] is None:
                    # The vrf updates with missing vrfId will have to use existing
                    # vrfId from the instance of the same vrf on DCNM.
                    want["vrfId"] = have["vrfId"]
                create = want

            else:
                pass

        else:

            # skip vrfVlanId when comparing
            templates_differ = self.dict_values_differ(
                json_to_dict_want, json_to_dict_have, skip_keys=["vrfVlanId"]
            )

            if want["vrfId"] is not None and have["vrfId"] != want["vrfId"]:
                msg = f"{self.class_name}.diff_for_create: "
                msg += f"vrf_id for vrf {want['vrfName']} cannot be updated to "
                msg += "a different value"
                self.module.fail_json(msg=msg)

            elif templates_differ:
                conf_changed = True
                if want["vrfId"] is None:
                    # The vrf updates with missing vrfId will have to use existing
                    # vrfId from the instance of the same vrf on DCNM.
                    want["vrfId"] = have["vrfId"]
                create = want

            else:
                pass

        msg = f"{self.class_name}.{method_name}: "
        msg += f"returning conf_changed: {conf_changed}, "
        msg += f"create: {create}"
        self.log.debug(msg)

        return create, conf_changed

    def update_create_params(self, vrf, vlanId=""):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
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
            "vrfVlanId": vlanId,
            "vrfVlanName": vrf.get("vrf_vlan_name", ""),
            "vrfIntfDescription": vrf.get("vrf_intf_desc", ""),
            "vrfDescription": vrf.get("vrf_description", ""),
            "mtu": vrf.get("vrf_int_mtu", ""),
            "tag": vrf.get("loopback_route_tag", ""),
            "vrfRouteMap": vrf.get("redist_direct_rmap", ""),
            "maxBgpPaths": vrf.get("max_bgp_paths", ""),
            "maxIbgpPaths": vrf.get("max_ibgp_paths", ""),
            "ipv6LinkLocalFlag": vrf.get("ipv6_linklocal_enable", True),
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
        method = "GET"
        path = self.paths["GET_VRF"].format(self.fabric)

        vrf_objects = dcnm_send(self.module, method, path)

        missing_fabric, not_ok = self.handle_response(vrf_objects, "query_dcnm")

        if missing_fabric or not_ok:
            msg1 = f"Fabric {self.fabric} not present on the controller"
            msg2 = f"Unable to find vrfs under fabric: {self.fabric}"
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
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
        self.log.debug(msg)

        method = "GET"
        path = self.paths["GET_VRF_SWITCH"].format(
            attach["fabric"], attach["vrfName"], attach["serialNumber"]
        )
        lite_objects = dcnm_send(self.module, method, path)

        return copy.deepcopy(lite_objects)

    def get_have(self):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
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
                "maxBgpPaths": json_to_dict.get("maxBgpPaths", 1),
                "maxIbgpPaths": json_to_dict.get("maxIbgpPaths", 2),
                "ipv6LinkLocalFlag": json_to_dict.get("ipv6LinkLocalFlag", True),
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
                "bgpPasswordKeyType": json_to_dict.get("bgpPasswordKeyType", ""),
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
                attach_state = False if attach["lanAttachState"] == "NA" else True
                deploy = attach["isLanAttached"]
                deployed = False
                if deploy and (
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
                msg = f"{self.class_name}.{method_name}: "
                if not lite_objects.get("DATA"):
                    return

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

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.have_create: {json.dumps(self.have_create, indent=4)}"
        self.log.debug(msg)

        # json.dumps() here breaks unit tests since self.have_attach is
        # a MagicMock and not JSON serializable.
        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.have_attach: {self.have_attach}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.have_deploy: {json.dumps(self.have_deploy, indent=4)}"
        self.log.debug(msg)

    def get_want(self):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
        self.log.debug(msg)

        want_create = []
        want_attach = []
        want_deploy = {}

        all_vrfs = ""

        if not self.config:
            return

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.config {json.dumps(self.config, indent=4)}"
        self.log.debug(msg)

        for vrf in self.validated:
            vrf_attach = {}
            vrfs = []

            vrf_deploy = vrf.get("deploy", True)
            if vrf.get("vlan_id"):
                vlanId = vrf.get("vlan_id")
            else:
                vlanId = 0

            want_create.append(self.update_create_params(vrf, vlanId))

            if not vrf.get("attach"):
                continue
            for attach in vrf["attach"]:
                deploy = vrf_deploy
                vrfs.append(
                    self.update_attach_params(attach, vrf["vrf_name"], deploy, vlanId)
                )

            if vrfs:
                vrf_attach.update({"vrfName": vrf["vrf_name"]})
                vrf_attach.update({"lanAttachList": vrfs})
                want_attach.append(vrf_attach)

            all_vrfs += vrf["vrf_name"] + ","

        if all_vrfs:
            want_deploy.update({"vrfNames": all_vrfs[:-1]})

        self.want_create = want_create
        self.want_attach = want_attach
        self.want_deploy = want_deploy

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.want_create: {json.dumps(self.want_create, indent=4)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.want_attach: {json.dumps(self.want_attach, indent=4)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.want_deploy: {json.dumps(self.want_deploy, indent=4)}"
        self.log.debug(msg)

    def get_diff_delete(self):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
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

        all_vrfs = ""

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
                    all_vrfs += have_a["vrfName"] + ","
            if all_vrfs:
                diff_undeploy.update({"vrfNames": all_vrfs[:-1]})

        else:

            for have_a in self.have_attach:
                detach_items = get_items_to_detach(have_a["lanAttachList"])
                if detach_items:
                    have_a.update({"lanAttachList": detach_items})
                    diff_detach.append(have_a)
                    all_vrfs += have_a["vrfName"] + ","

                diff_delete.update({have_a["vrfName"]: "DEPLOYED"})
            if all_vrfs:
                diff_undeploy.update({"vrfNames": all_vrfs[:-1]})

        self.diff_detach = diff_detach
        self.diff_undeploy = diff_undeploy
        self.diff_delete = diff_delete

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.diff_detach: {json.dumps(self.diff_detach, indent=4)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.diff_undeploy: {json.dumps(self.diff_undeploy, indent=4)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.diff_delete: {json.dumps(self.diff_delete, indent=4)}"
        self.log.debug(msg)

    def get_diff_override(self):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
        self.log.debug(msg)

        all_vrfs = ""
        diff_delete = {}

        self.get_diff_replace()

        diff_create = self.diff_create
        diff_attach = self.diff_attach
        diff_detach = self.diff_detach
        diff_deploy = self.diff_deploy
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
                    all_vrfs += have_a["vrfName"] + ","

                diff_delete.update({have_a["vrfName"]: "DEPLOYED"})

        if all_vrfs:
            diff_undeploy.update({"vrfNames": all_vrfs[:-1]})

        self.diff_create = diff_create
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy
        self.diff_detach = diff_detach
        self.diff_undeploy = diff_undeploy
        self.diff_delete = diff_delete

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.diff_create: {json.dumps(self.diff_create, indent=4)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.diff_attach: {json.dumps(self.diff_attach, indent=4)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.diff_deploy: {json.dumps(self.diff_deploy, indent=4)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.diff_detach: {json.dumps(self.diff_detach, indent=4)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.diff_undeploy: {json.dumps(self.diff_undeploy, indent=4)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.diff_delete: {json.dumps(self.diff_delete, indent=4)}"
        self.log.debug(msg)

    def get_diff_replace(self):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
        self.log.debug(msg)

        all_vrfs = ""

        self.get_diff_merge(replace=True)
        diff_create = self.diff_create
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
                    all_vrfs += have_a["vrfName"] + ","

        if not all_vrfs:
            self.diff_create = diff_create
            self.diff_attach = diff_attach
            self.diff_deploy = diff_deploy
            return

        if not self.diff_deploy:
            diff_deploy.update({"vrfNames": all_vrfs[:-1]})
        else:
            vrfs = self.diff_deploy["vrfNames"] + "," + all_vrfs[:-1]
            diff_deploy.update({"vrfNames": vrfs})

        self.diff_create = diff_create
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.diff_create: {json.dumps(self.diff_create, indent=4)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.diff_attach: {json.dumps(self.diff_attach, indent=4)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.diff_deploy: {json.dumps(self.diff_deploy, indent=4)}"
        self.log.debug(msg)

    def get_diff_merge(self, replace=False):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
        self.log.debug(msg)

        # Special cases:
        # 1. Auto generate vrfId if its not mentioned by user:
        #    In this case, we need to query the DCNM to get a usable ID and use it in the payload.
        #    And also, any such vrf create requests need to be pushed individually(not bulk op).

        diff_create = []
        diff_create_update = []
        diff_create_quick = []
        diff_attach = []
        diff_deploy = {}
        prev_vrf_id_fetched = None
        conf_changed = {}

        all_vrfs = ""

        attach_found = False
        vrf_found = False
        for want_c in self.want_create:
            vrf_found = False
            for have_c in self.have_create:
                if want_c["vrfName"] == have_c["vrfName"]:
                    vrf_found = True
                    diff, conf_chg = self.diff_for_create(want_c, have_c)
                    conf_changed.update({want_c["vrfName"]: conf_chg})
                    if diff:
                        diff_create_update.append(diff)
                    break
            if not vrf_found:
                vrf_id = want_c.get("vrfId", None)
                if vrf_id is None:
                    # vrfId is not provided by user.
                    # Need to query DCNM to fetch next available vrfId and use it here.
                    method = "POST"

                    attempt = 0
                    while attempt < 10:
                        attempt += 1
                        path = self.paths["GET_VRF_ID"].format(self.fabric)
                        if self.dcnm_version > 11:
                            vrf_id_obj = dcnm_send(self.module, "GET", path)
                        else:
                            vrf_id_obj = dcnm_send(self.module, method, path)

                        missing_fabric, not_ok = self.handle_response(
                            vrf_id_obj, "query_dcnm"
                        )

                        if missing_fabric or not_ok:
                            # arobel: TODO: Not covered by UT
                            msg0 = f"{self.class_name}.{method_name}: "
                            msg1 = f"{msg0} Fabric {self.fabric} not present on the controller"
                            msg2 = f"{msg0} Unable to generate vrfId for vrf "
                            msg2 += f"{want_c['vrfName']} under fabric {self.fabric}"
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
                            msg += (
                                f"Unsupported controller version: {self.dcnm_version}"
                            )
                            self.module.fail_json(msg)

                        if vrf_id != prev_vrf_id_fetched:
                            want_c.update({"vrfId": vrf_id})
                            json_to_dict = json.loads(want_c["vrfTemplateConfig"])
                            template_conf = {
                                "vrfSegmentId": vrf_id,
                                "vrfName": want_c["vrfName"],
                                "vrfVlanId": json_to_dict.get("vrfVlanId"),
                                "vrfVlanName": json_to_dict.get("vrfVlanName"),
                                "vrfIntfDescription": json_to_dict.get(
                                    "vrfIntfDescription"
                                ),
                                "vrfDescription": json_to_dict.get("vrfDescription"),
                                "mtu": json_to_dict.get("mtu"),
                                "tag": json_to_dict.get("tag"),
                                "vrfRouteMap": json_to_dict.get("vrfRouteMap"),
                                "maxBgpPaths": json_to_dict.get("maxBgpPaths"),
                                "maxIbgpPaths": json_to_dict.get("maxIbgpPaths"),
                                "ipv6LinkLocalFlag": json_to_dict.get(
                                    "ipv6LinkLocalFlag"
                                ),
                                "trmEnabled": json_to_dict.get("trmEnabled"),
                                "isRPExternal": json_to_dict.get("isRPExternal"),
                                "rpAddress": json_to_dict.get("rpAddress"),
                                "loopbackNumber": json_to_dict.get("loopbackNumber"),
                                "L3VniMcastGroup": json_to_dict.get("L3VniMcastGroup"),
                                "multicastGroup": json_to_dict.get("multicastGroup"),
                                "trmBGWMSiteEnabled": json_to_dict.get(
                                    "trmBGWMSiteEnabled"
                                ),
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
                                "bgpPasswordKeyType": json_to_dict.get(
                                    "bgpPasswordKeyType"
                                ),
                            }

                            if self.dcnm_version > 11:
                                template_conf.update(
                                    isRPAbsent=json_to_dict.get("isRPAbsent")
                                )
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
                                    routeTargetImport=json_to_dict.get(
                                        "routeTargetImport"
                                    )
                                )
                                template_conf.update(
                                    routeTargetExport=json_to_dict.get(
                                        "routeTargetExport"
                                    )
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

                            want_c.update(
                                {"vrfTemplateConfig": json.dumps(template_conf)}
                            )
                            prev_vrf_id_fetched = vrf_id
                            break

                    if not vrf_id:
                        # arobel: TODO: Not covered by UT
                        msg = f"{self.class_name}.{method_name}: "
                        msg += f"Unable to generate vrfId for vrf: {want_c['vrfName']} "
                        msg += f"under fabric: {self.fabric}"
                        self.module.fail_json(msg=msg)

                    create_path = self.paths["GET_VRF"].format(self.fabric)

                    diff_create_quick.append(want_c)

                    if self.module.check_mode:
                        continue

                    # arobel: TODO: The below is not covered by UT
                    resp = dcnm_send(
                        self.module, method, create_path, json.dumps(want_c)
                    )
                    self.result["response"].append(resp)
                    fail, self.result["changed"] = self.handle_response(resp, "create")
                    if fail:
                        self.failure(resp)

                else:
                    diff_create.append(want_c)

        for want_a in self.want_attach:
            deploy_vrf = ""
            attach_found = False
            for have_a in self.have_attach:
                if want_a["vrfName"] == have_a["vrfName"]:
                    attach_found = True
                    diff, vrf = self.diff_for_attach_deploy(
                        want_a["lanAttachList"], have_a["lanAttachList"], replace
                    )
                    if diff:
                        base = want_a.copy()
                        del base["lanAttachList"]
                        base.update({"lanAttachList": diff})

                        diff_attach.append(base)
                        if vrf:
                            deploy_vrf = want_a["vrfName"]
                    else:
                        if vrf or conf_changed.get(want_a["vrfName"], False):
                            deploy_vrf = want_a["vrfName"]

            if not attach_found and want_a.get("lanAttachList"):
                atch_list = []
                for attach in want_a["lanAttachList"]:
                    if attach.get("isAttached"):
                        del attach["isAttached"]
                    atch_list.append(attach)
                if atch_list:
                    base = want_a.copy()
                    del base["lanAttachList"]
                    base.update({"lanAttachList": atch_list})
                    diff_attach.append(base)
                    if attach["is_deploy"]:
                        deploy_vrf = want_a["vrfName"]

                for atch in atch_list:
                    atch["deployment"] = True

            if deploy_vrf:
                all_vrfs += deploy_vrf + ","

        if all_vrfs:
            diff_deploy.update({"vrfNames": all_vrfs[:-1]})

        self.diff_create = diff_create
        self.diff_create_update = diff_create_update
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy
        self.diff_create_quick = diff_create_quick

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.diff_create: {json.dumps(self.diff_create, indent=4)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += (
            f"self.diff_create_update: {json.dumps(self.diff_create_update, indent=4)}"
        )
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.diff_attach: {json.dumps(self.diff_attach, indent=4)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.diff_deploy: {json.dumps(self.diff_deploy, indent=4)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.diff_create_quick: {json.dumps(self.diff_create_quick, indent=4)}"
        self.log.debug(msg)

    def format_diff(self):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
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

        diff_create.extend(diff_create_quick)
        diff_create.extend(diff_create_update)
        diff_attach.extend(diff_detach)
        diff_deploy.extend(diff_undeploy)

        for want_d in diff_create:

            found_a = self.find_dict_in_list_by_key_value(
                search=diff_attach, key="vrfName", value=want_d["vrfName"]
            )

            found_c = want_d

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
            found_c.update({"max_bgp_paths": json_to_dict.get("maxBgpPaths", "")})
            found_c.update({"max_ibgp_paths": json_to_dict.get("maxIbgpPaths", "")})
            found_c.update(
                {"ipv6_linklocal_enable": json_to_dict.get("ipv6LinkLocalFlag", True)}
            )
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

            if diff_deploy and found_c["vrf_name"] in diff_deploy:
                diff_deploy.remove(found_c["vrf_name"])
            if not found_a:
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

        self.diff_input_format = diff

        msg = f"{self.class_name}.{method_name}: "
        msg += "self.diff_input_format: "
        msg += f"{json.dumps(self.diff_input_format, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def get_diff_query(self):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
        self.log.debug(msg)

        method = "GET"
        path = self.paths["GET_VRF"].format(self.fabric)
        vrf_objects = dcnm_send(self.module, method, path)
        missing_fabric, not_ok = self.handle_response(vrf_objects, "query_dcnm")

        if (
            vrf_objects.get("ERROR") == "Not Found"
            and vrf_objects.get("RETURN_CODE") == 404
        ):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Fabric {self.fabric} does not exist on the controller"
            self.module.fail_json(msg=msg)
            return

        if missing_fabric or not_ok:
            # arobel: TODO: Not covered by UT
            msg0 = f"{self.class_name}.{method_name}:"
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
                        method = "GET"
                        path = self.paths["GET_VRF_ATTACH"].format(
                            self.fabric, vrf["vrfName"]
                        )

                        vrf_attach_objects = dcnm_send(self.module, method, path)

                        missing_fabric, not_ok = self.handle_response(
                            vrf_attach_objects, "query_dcnm"
                        )

                        if missing_fabric or not_ok:
                            # arobel: TODO: Not covered by UT
                            msg0 = f"{self.class_name}.{method_name}:"
                            msg1 = f"{msg0} Fabric {self.fabric} not present on the controller"
                            msg2 = f"{msg0} Unable to find attachments for "
                            msg2 += (
                                f"vrfs: {vrf['vrfName']} under fabric: {self.fabric}"
                            )
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
                method = "GET"
                path = self.paths["GET_VRF_ATTACH"].format(self.fabric, vrf["vrfName"])

                vrf_attach_objects = dcnm_send(self.module, method, path)

                missing_fabric, not_ok = self.handle_response(vrf_objects, "query_dcnm")

                if missing_fabric or not_ok:
                    msg1 = f"Fabric {self.fabric} not present on DCNM"
                    msg2 = "Unable to find attachments for "
                    msg2 += f"vrfs: {vrf['vrfName']} under fabric: {self.fabric}"

                    self.module.fail_json(msg=msg1 if missing_fabric else msg2)
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

    def push_to_remote(self, is_rollback=False):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
        self.log.debug(msg)

        path = self.paths["GET_VRF"].format(self.fabric)

        method = "PUT"
        if self.diff_create_update:
            for vrf in self.diff_create_update:
                update_path = f"{path}/{vrf['vrfName']}"
                resp = dcnm_send(self.module, method, update_path, json.dumps(vrf))
                self.result["response"].append(resp)
                fail, self.result["changed"] = self.handle_response(resp, "create")
                if fail:
                    if is_rollback:
                        self.failed_to_rollback = True
                        return
                    self.failure(resp)

        #
        # The detach and un-deploy operations are executed before the create,attach and deploy to particularly
        # address cases where a VLAN for vrf attachment being deleted is re-used on a new vrf attachment being
        # created. This is needed specially for state: overridden
        #

        method = "POST"
        if self.diff_detach:
            detach_path = path + "/attachments"

            # Update the fabric name to specific fabric to which the switches belong for multisite fabric.
            if self.fabric_type == "MFD":
                for elem in self.diff_detach:
                    for node in elem["lanAttachList"]:
                        node["fabric"] = self.sn_fab[node["serialNumber"]]

            for d_a in self.diff_detach:
                for v_a in d_a["lanAttachList"]:
                    if "is_deploy" in v_a.keys():
                        del v_a["is_deploy"]

            resp = dcnm_send(
                self.module, method, detach_path, json.dumps(self.diff_detach)
            )
            self.result["response"].append(resp)
            fail, self.result["changed"] = self.handle_response(resp, "attach")
            if fail:
                if is_rollback:
                    self.failed_to_rollback = True
                    return
                self.failure(resp)

        method = "POST"
        if self.diff_undeploy:
            deploy_path = path + "/deployments"
            resp = dcnm_send(
                self.module, method, deploy_path, json.dumps(self.diff_undeploy)
            )
            self.result["response"].append(resp)
            fail, self.result["changed"] = self.handle_response(resp, "deploy")
            if fail:
                if is_rollback:
                    self.failed_to_rollback = True
                    return
                self.failure(resp)

        del_failure = ""

        if self.diff_delete and self.wait_for_vrf_del_ready():
            method = "DELETE"
            for vrf, state in self.diff_delete.items():
                if state == "OUT-OF-SYNC":
                    del_failure += vrf + ","
                    continue
                delete_path = path + "/" + vrf
                resp = dcnm_send(self.module, method, delete_path)
                self.result["response"].append(resp)
                fail, self.result["changed"] = self.handle_response(resp, "delete")
                if fail:
                    if is_rollback:
                        self.failed_to_rollback = True
                        return
                    self.failure(resp)

        if del_failure:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Deletion of vrfs {del_failure[:-1]} has failed"
            self.result["response"].append(msg)
            self.module.fail_json(msg=self.result)

        method = "POST"
        if self.diff_create:

            for vrf in self.diff_create:
                json_to_dict = json.loads(vrf["vrfTemplateConfig"])
                vlanId = json_to_dict.get("vrfVlanId", "0")

                if vlanId == 0:
                    vlan_path = self.paths["GET_VLAN"].format(self.fabric)
                    vlan_data = dcnm_send(self.module, "GET", vlan_path)

                    if vlan_data["RETURN_CODE"] != 200:
                        msg = f"{self.class_name}.{method_name}: "
                        msg += f"Failure getting autogenerated vlan_id {vlan_data}"
                        self.module.fail_json(msg=msg)

                    vlanId = vlan_data["DATA"]

                t_conf = {
                    "vrfSegmentId": vrf["vrfId"],
                    "vrfName": json_to_dict.get("vrfName", ""),
                    "vrfVlanId": vlanId,
                    "vrfVlanName": json_to_dict.get("vrfVlanName"),
                    "vrfIntfDescription": json_to_dict.get("vrfIntfDescription"),
                    "vrfDescription": json_to_dict.get("vrfDescription"),
                    "mtu": json_to_dict.get("mtu"),
                    "tag": json_to_dict.get("tag"),
                    "vrfRouteMap": json_to_dict.get("vrfRouteMap"),
                    "maxBgpPaths": json_to_dict.get("maxBgpPaths"),
                    "maxIbgpPaths": json_to_dict.get("maxIbgpPaths"),
                    "ipv6LinkLocalFlag": json_to_dict.get("ipv6LinkLocalFlag"),
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
                    t_conf.update(isRPAbsent=json_to_dict.get("isRPAbsent"))
                    t_conf.update(ENABLE_NETFLOW=json_to_dict.get("ENABLE_NETFLOW"))
                    t_conf.update(NETFLOW_MONITOR=json_to_dict.get("NETFLOW_MONITOR"))
                    t_conf.update(disableRtAuto=json_to_dict.get("disableRtAuto"))
                    t_conf.update(
                        routeTargetImport=json_to_dict.get("routeTargetImport")
                    )
                    t_conf.update(
                        routeTargetExport=json_to_dict.get("routeTargetExport")
                    )
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

                resp = dcnm_send(self.module, method, path, json.dumps(vrf))
                self.result["response"].append(resp)
                fail, self.result["changed"] = self.handle_response(resp, "create")
                if fail:
                    if is_rollback:
                        self.failed_to_rollback = True
                        return
                    self.failure(resp)

        if self.diff_attach:
            for d_a in self.diff_attach:
                for v_a in d_a["lanAttachList"]:
                    v_a.update(vlan=0)
                    if "is_deploy" in v_a.keys():
                        del v_a["is_deploy"]
                    if v_a.get("vrf_lite"):
                        for ip, ser in self.ip_sn.items():
                            if ser == v_a["serialNumber"]:
                                """Before apply the vrf_lite config, need double check if the switch role is started wth Border"""
                                role = self.inventory_data[ip].get("switchRole")
                                r = re.search(r"\bborder\b", role.lower())
                                if not r:
                                    msg = f"{self.class_name}.{method_name}: "
                                    msg += "VRF LITE cannot be attached to "
                                    msg += f"switch {ip} with role {role}"
                                    self.module.fail_json(msg=msg)

                        lite_objects = self.get_vrf_lite_objects(v_a)
                        if not lite_objects.get("DATA"):
                            return

                        lite = lite_objects["DATA"][0]["switchDetailsList"][0][
                            "extensionPrototypeValues"
                        ]
                        ext_values = None
                        extension_values = {}
                        extension_values["VRF_LITE_CONN"] = []
                        extension_values["MULTISITE_CONN"] = []

                        for ext_l in lite:
                            if str(ext_l.get("extensionType")) != "VRF_LITE":
                                continue
                            ext_values = ext_l["extensionValues"]
                            ext_values = ast.literal_eval(ext_values)
                            for ad_l in v_a.get("vrf_lite"):
                                if ad_l["interface"] == ext_values["IF_NAME"]:
                                    nbr_dict = {}
                                    nbr_dict["IF_NAME"] = ad_l["interface"]

                                    if ad_l["dot1q"]:
                                        nbr_dict["DOT1Q_ID"] = str(ad_l["dot1q"])
                                    else:
                                        nbr_dict["DOT1Q_ID"] = str(
                                            ext_values["DOT1Q_ID"]
                                        )

                                    if ad_l["ipv4_addr"]:
                                        nbr_dict["IP_MASK"] = ad_l["ipv4_addr"]
                                    else:
                                        nbr_dict["IP_MASK"] = ext_values["IP_MASK"]

                                    if ad_l["neighbor_ipv4"]:
                                        nbr_dict["NEIGHBOR_IP"] = ad_l["neighbor_ipv4"]
                                    else:
                                        nbr_dict["NEIGHBOR_IP"] = ext_values[
                                            "NEIGHBOR_IP"
                                        ]

                                    nbr_dict["NEIGHBOR_ASN"] = ext_values[
                                        "NEIGHBOR_ASN"
                                    ]

                                    if ad_l["ipv6_addr"]:
                                        nbr_dict["IPV6_MASK"] = ad_l["ipv6_addr"]
                                    else:
                                        nbr_dict["IPV6_MASK"] = ext_values["IPV6_MASK"]

                                    if ad_l["neighbor_ipv6"]:
                                        nbr_dict["IPV6_NEIGHBOR"] = ad_l[
                                            "neighbor_ipv6"
                                        ]
                                    else:
                                        nbr_dict["IPV6_NEIGHBOR"] = ext_values[
                                            "IPV6_NEIGHBOR"
                                        ]

                                    nbr_dict["AUTO_VRF_LITE_FLAG"] = ext_values[
                                        "AUTO_VRF_LITE_FLAG"
                                    ]

                                    if ad_l["peer_vrf"]:
                                        nbr_dict["PEER_VRF_NAME"] = ad_l["peer_vrf"]
                                    else:
                                        nbr_dict["PEER_VRF_NAME"] = ext_values[
                                            "PEER_VRF_NAME"
                                        ]

                                    nbr_dict["VRF_LITE_JYTHON_TEMPLATE"] = (
                                        "Ext_VRF_Lite_Jython"
                                    )
                                    vrflite_con = {}
                                    vrflite_con["VRF_LITE_CONN"] = []
                                    vrflite_con["VRF_LITE_CONN"].append(
                                        copy.deepcopy(nbr_dict)
                                    )
                                    if extension_values["VRF_LITE_CONN"]:
                                        extension_values["VRF_LITE_CONN"][
                                            "VRF_LITE_CONN"
                                        ].extend(vrflite_con["VRF_LITE_CONN"])
                                    else:
                                        extension_values["VRF_LITE_CONN"] = vrflite_con

                                    ms_con = {}
                                    ms_con["MULTISITE_CONN"] = []
                                    extension_values["MULTISITE_CONN"] = json.dumps(
                                        ms_con
                                    )

                                    del ad_l

                        if ext_values is None:
                            for ip, ser in self.ip_sn.items():
                                # arobel TODO: Not covered by UT
                                if ser == v_a["serialNumber"]:
                                    msg = f"{self.class_name}.{method_name}: "
                                    msg += "No VRF LITE capable interfaces found "
                                    msg += f"on this switch {ip}"
                            self.module.fail_json(msg=msg)
                        else:
                            extension_values["VRF_LITE_CONN"] = json.dumps(
                                extension_values["VRF_LITE_CONN"]
                            )
                            v_a["extensionValues"] = json.dumps(
                                extension_values
                            ).replace(" ", "")
                            if v_a.get("vrf_lite", None) is not None:
                                del v_a["vrf_lite"]

                    else:
                        if "vrf_lite" in v_a.keys():
                            del v_a["vrf_lite"]

            path = self.paths["GET_VRF"].format(self.fabric)
            method = "POST"
            attach_path = path + "/attachments"

            # Update the fabric name to specific fabric to which the switches belong for multisite fabric.
            if self.fabric_type == "MFD":
                for elem in self.diff_attach:
                    for node in elem["lanAttachList"]:
                        node["fabric"] = self.sn_fab[node["serialNumber"]]
            resp = dcnm_send(
                self.module, method, attach_path, json.dumps(self.diff_attach)
            )
            self.result["response"].append(resp)
            fail, self.result["changed"] = self.handle_response(resp, "attach")
            if fail:
                if is_rollback:
                    self.failed_to_rollback = True
                    return
                self.failure(resp)

        method = "POST"
        if self.diff_deploy:
            deploy_path = path + "/deployments"
            resp = dcnm_send(
                self.module, method, deploy_path, json.dumps(self.diff_deploy)
            )
            self.result["response"].append(resp)
            fail, self.result["changed"] = self.handle_response(resp, "deploy")
            if fail:
                if is_rollback:
                    self.failed_to_rollback = True
                    return
                self.failure(resp)

    def wait_for_vrf_del_ready(self):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
        self.log.debug(msg)

        method = "GET"
        if self.diff_delete:
            for vrf in self.diff_delete:
                state = False
                path = self.paths["GET_VRF_ATTACH"].format(self.fabric, vrf)
                while not state:
                    resp = dcnm_send(self.module, method, path)
                    state = True
                    if resp.get("DATA") is not None:
                        attach_list = resp["DATA"][0]["lanAttachList"]
                        msg = f"{self.class_name}.{method_name}: "
                        msg += f"attach_list: {json.dumps(attach_list, indent=4)}"
                        self.log.debug(msg)

                        for atch in attach_list:
                            if (
                                atch["lanAttachState"] == "OUT-OF-SYNC"
                                or atch["lanAttachState"] == "FAILED"
                            ):
                                self.diff_delete.update({vrf: "OUT-OF-SYNC"})
                                break
                            if (
                                atch["lanAttachState"] == "DEPLOYED"
                                and atch["isLanAttached"] is True
                            ):
                                vrf_name = atch.get("vrfName", "unknown")
                                fabric_name = atch.get("fabricName", "unknown")
                                switch_ip = atch.get("ipAddress", "unknown")
                                switch_name = atch.get("switchName", "unknown")
                                vlan_id = atch.get("vlanId", "unknown")
                                msg = f"{self.class_name}.{method_name}: "
                                msg += f"Network attachments associated with vrf {vrf_name} "
                                msg += "must be removed (e.g. using the dcnm_network module) "
                                msg += "prior to deleting the vrf. "
                                msg += f"Details: fabric_name: {fabric_name}, "
                                msg += f"vrf_name: {vrf_name}. "
                                msg += "Network attachments found on "
                                msg += f"switch_ip: {switch_ip}, "
                                msg += f"switch_name: {switch_name}, "
                                msg += f"vlan_id: {vlan_id}"
                                self.module.fail_json(msg=msg)
                            if atch["lanAttachState"] != "NA":
                                time.sleep(self.WAIT_TIME_FOR_DELETE_LOOP)
                                self.diff_delete.update({vrf: "DEPLOYED"})
                                state = False
                                break
                            self.diff_delete.update({vrf: "NA"})

            return True

    def validate_input(self):
        """Parse the playbook values, validate to param specs."""
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
        self.log.debug(msg)

        state = self.params["state"]

        if state in ("merged", "overridden", "replaced"):

            vrf_spec = dict(
                vrf_name=dict(required=True, type="str", length_max=32),
                vrf_id=dict(type="int", range_max=16777214),
                vrf_template=dict(type="str", default="Default_VRF_Universal"),
                vrf_extension_template=dict(
                    type="str", default="Default_VRF_Extension_Universal"
                ),
                vlan_id=dict(type="int", range_max=4094),
                source=dict(type="str", default=None),
                service_vrf_template=dict(type="str", default=None),
                attach=dict(type="list"),
                deploy=dict(type="bool", default=True),
                vrf_vlan_name=dict(type="str", default=""),
                vrf_intf_desc=dict(type="str", default=""),
                vrf_description=dict(type="str", default=""),
                vrf_int_mtu=dict(
                    type="int", range_min=68, range_max=9216, default=9216
                ),
                loopback_route_tag=dict(
                    type="int", default=12345, range_max=4294967295
                ),
                redist_direct_rmap=dict(
                    type="str", default="FABRIC-RMAP-REDIST-SUBNET"
                ),
                max_bgp_paths=dict(type="int", range_min=1, range_max=64, default=1),
                max_ibgp_paths=dict(type="int", range_min=1, range_max=64, default=2),
                ipv6_linklocal_enable=dict(type="bool", default=True),
                trm_enable=dict(type="bool", default=False),
                no_rp=dict(type="bool", default=False),
                rp_external=dict(type="bool", default=False),
                rp_address=dict(type="str", default=""),
                rp_loopback_id=dict(type="int", range_max=1023, default=""),
                underlay_mcast_ip=dict(type="str", default=""),
                overlay_mcast_group=dict(type="str", default=""),
                trm_bgw_msite=dict(type="bool", default=False),
                adv_host_routes=dict(type="bool", default=False),
                adv_default_routes=dict(type="bool", default=True),
                static_default_route=dict(type="bool", default=True),
                bgp_password=dict(type="str", default=""),
                bgp_passwd_encrypt=dict(type="int", default=3, choices=[3, 7]),
                netflow_enable=dict(type="bool", default=False),
                nf_monitor=dict(type="str", default=""),
                disable_rt_auto=dict(type="bool", default=False),
                import_vpn_rt=dict(type="str", default=""),
                export_vpn_rt=dict(type="str", default=""),
                import_evpn_rt=dict(type="str", default=""),
                export_evpn_rt=dict(type="str", default=""),
                import_mvpn_rt=dict(type="str", default=""),
                export_mvpn_rt=dict(type="str", default=""),
            )
            att_spec = dict(
                ip_address=dict(required=True, type="str"),
                deploy=dict(type="bool", default=True),
                vrf_lite=dict(type="list"),
                import_evpn_rt=dict(type="str", default=""),
                export_evpn_rt=dict(type="str", default=""),
            )
            lite_spec = dict(
                interface=dict(required=True, type="str"),
                peer_vrf=dict(type="str"),
                ipv4_addr=dict(type="ipv4_subnet"),
                neighbor_ipv4=dict(type="ipv4"),
                ipv6_addr=dict(type="ipv6"),
                neighbor_ipv6=dict(type="ipv6"),
                dot1q=dict(type="int"),
            )

            msg = None
            if self.config:
                for vrf in self.config:
                    # A few user provided vrf parameters need special handling
                    # Ignore user input for src and hard code it to None
                    vrf["source"] = None
                    if not vrf.get("service_vrf_template"):
                        vrf["service_vrf_template"] = None

                    if "vrf_name" not in vrf:
                        msg = "vrf_name is mandatory under vrf parameters"

                    if "attach" in vrf and vrf["attach"]:
                        for attach in vrf["attach"]:
                            # if 'ip_address' not in attach or 'vlan_id' not in attach:
                            #     msg = "ip_address and vlan_id are mandatory under attach parameters"
                            if "ip_address" not in attach:
                                msg = "ip_address is mandatory under attach parameters"
            else:
                if state in ("merged", "replaced"):
                    msg = f"{self.class_name}.{method_name}: "
                    msg += f"config element is mandatory for {state} state"

            if msg:
                self.module.fail_json(msg=msg)

            if self.config:
                valid_vrf, invalid_params = validate_list_of_dicts(
                    self.config, vrf_spec
                )
                for vrf in valid_vrf:
                    if vrf.get("attach"):
                        for entry in vrf.get("attach"):
                            entry["deploy"] = vrf["deploy"]
                        valid_att, invalid_att = validate_list_of_dicts(
                            vrf["attach"], att_spec
                        )
                        vrf["attach"] = valid_att

                        invalid_params.extend(invalid_att)
                        for lite in vrf.get("attach"):
                            if lite.get("vrf_lite"):
                                valid_lite, invalid_lite = validate_list_of_dicts(
                                    lite["vrf_lite"], lite_spec
                                )
                                lite["vrf_lite"] = valid_lite
                                invalid_params.extend(invalid_lite)
                    self.validated.append(vrf)

                if invalid_params:
                    msg = "Invalid parameters in playbook: {0}".format(
                        "\n".join(invalid_params)
                    )
                    self.module.fail_json(msg=msg)

        else:

            vrf_spec = dict(
                vrf_name=dict(required=True, type="str", length_max=32),
                vrf_id=dict(type="int", range_max=16777214),
                vrf_template=dict(type="str", default="Default_VRF_Universal"),
                vrf_extension_template=dict(
                    type="str", default="Default_VRF_Extension_Universal"
                ),
                vlan_id=dict(type="int", range_max=4094),
                source=dict(type="str", default=None),
                service_vrf_template=dict(type="str", default=None),
                attach=dict(type="list"),
                deploy=dict(type="bool"),
                vrf_vlan_name=dict(type="str", default=""),
                vrf_intf_desc=dict(type="str", default=""),
                vrf_description=dict(type="str", default=""),
                vrf_int_mtu=dict(
                    type="int", range_min=68, range_max=9216, default=9216
                ),
                loopback_route_tag=dict(
                    type="int", default=12345, range_max=4294967295
                ),
                redist_direct_rmap=dict(
                    type="str", default="FABRIC-RMAP-REDIST-SUBNET"
                ),
                max_bgp_paths=dict(type="int", range_min=1, range_max=64, default=1),
                max_ibgp_paths=dict(type="int", range_min=1, range_max=64, default=2),
                ipv6_linklocal_enable=dict(type="bool", default=True),
                trm_enable=dict(type="bool", default=False),
                no_rp=dict(type="bool", default=False),
                rp_external=dict(type="bool", default=False),
                rp_address=dict(type="str", default=""),
                rp_loopback_id=dict(type="int", range_max=1023, default=""),
                underlay_mcast_ip=dict(type="str", default=""),
                overlay_mcast_group=dict(type="str", default=""),
                trm_bgw_msite=dict(type="bool", default=False),
                adv_host_routes=dict(type="bool", default=False),
                adv_default_routes=dict(type="bool", default=True),
                static_default_route=dict(type="bool", default=True),
                bgp_password=dict(type="str", default=""),
                bgp_passwd_encrypt=dict(type="int", default=3, choices=[3, 7]),
                netflow_enable=dict(type="bool", default=False),
                nf_monitor=dict(type="str", default=""),
                disable_rt_auto=dict(type="bool", default=False),
                import_vpn_rt=dict(type="str", default=""),
                export_vpn_rt=dict(type="str", default=""),
                import_evpn_rt=dict(type="str", default=""),
                export_evpn_rt=dict(type="str", default=""),
                import_mvpn_rt=dict(type="str", default=""),
                export_mvpn_rt=dict(type="str", default=""),
            )
            att_spec = dict(
                ip_address=dict(required=True, type="str"),
                deploy=dict(type="bool", default=True),
                vrf_lite=dict(type="list", default=[]),
                import_evpn_rt=dict(type="str", default=""),
                export_evpn_rt=dict(type="str", default=""),
            )
            lite_spec = dict(
                interface=dict(type="str"),
                peer_vrf=dict(type="str"),
                ipv4_addr=dict(type="ipv4_subnet"),
                neighbor_ipv4=dict(type="ipv4"),
                ipv6_addr=dict(type="ipv6"),
                neighbor_ipv6=dict(type="ipv6"),
                dot1q=dict(type="int"),
            )

            if self.config:
                valid_vrf, invalid_params = validate_list_of_dicts(
                    self.config, vrf_spec
                )
                for vrf in valid_vrf:
                    if vrf.get("attach"):
                        valid_att, invalid_att = validate_list_of_dicts(
                            vrf["attach"], att_spec
                        )
                        vrf["attach"] = valid_att
                        invalid_params.extend(invalid_att)
                        for lite in vrf.get("attach"):
                            if lite.get("vrf_lite"):
                                valid_lite, invalid_lite = validate_list_of_dicts(
                                    lite["vrf_lite"], lite_spec
                                )
                                lite["vrf_lite"] = valid_lite
                                invalid_params.extend(invalid_lite)
                    self.validated.append(vrf)

                if invalid_params:
                    msg = "Invalid parameters in playbook: {0}".format(
                        "\n".join(invalid_params)
                    )
                    self.module.fail_json(msg=msg)

    def handle_response(self, res, op):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
        self.log.debug(msg)

        fail = False
        changed = True

        if op == "query_dcnm":
            # This if blocks handles responses to the query APIs against DCNM.
            # Basically all GET operations.
            #
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

        # Implementing a per task rollback logic here so that we rollback DCNM to the have state
        # whenever there is a failure in any of the APIs.
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
            msg1 = "FAILED - Attempted rollback of the task has failed, may need manual intervention"
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

        if self.module._verbosity >= 5:
            self.module.fail_json(msg=res)

        self.module.fail_json(msg=res)


def main():
    """main entry point for module execution"""

    # Logging setup
    try:
        log = Log()
        log.commit()
    except (TypeError, ValueError) as error:
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
        module.exit_json(**dcnm_vrf.result)

    dcnm_vrf.push_to_remote()

    module.exit_json(**dcnm_vrf.result)


if __name__ == "__main__":
    main()
