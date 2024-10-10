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
__author__ = (
    "Shrishail Kariyappanavar, Karthik Babu Harichandra Babu, Praveen Ramoorthy"
)

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

import json
import time
import copy
import ast
import re
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    get_fabric_inventory_details,
    dcnm_send,
    validate_list_of_dicts,
    dcnm_get_ip_addr_info,
    get_ip_sn_dict,
    get_fabric_details,
    get_ip_sn_fabric_dict,
    dcnm_version_supported,
    dcnm_get_url,
)
from ansible.module_utils.basic import AnsibleModule


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

        self.result = dict(changed=False, diff=[], response=[])

        self.failed_to_rollback = False
        self.WAIT_TIME_FOR_DELETE_LOOP = 5  # in seconds

    def diff_for_attach_deploy(self, want_a, have_a, replace=False):

        attach_list = []

        if not want_a:
            return attach_list

        dep_vrf = False
        for want in want_a:
            found = False
            interface_match = False
            if have_a:
                for have in have_a:
                    if want["serialNumber"] == have["serialNumber"]:
                        # handle instanceValues first
                        want.update({"freeformConfig": have["freeformConfig"]})  # copy freeformConfig from have as module is not managing it
                        want_inst_values = {}
                        have_inst_values = {}
                        if (
                            want["instanceValues"] is not None
                            and have["instanceValues"] is not None
                        ):
                            want_inst_values = ast.literal_eval(want["instanceValues"])
                            have_inst_values = ast.literal_eval(have["instanceValues"])

                            # update unsupported paramters using using have
                            # Only need ipv4 or ipv6. Don't require both, but both can be supplied (as per the GUI)
                            want_inst_values.update({"loopbackId": have_inst_values["loopbackId"]})
                            if "loopbackIpAddress" in have_inst_values:
                                want_inst_values.update({"loopbackIpAddress": have_inst_values["loopbackIpAddress"]})
                            if "loopbackIpV6Address" in have_inst_values:
                                want_inst_values.update({"loopbackIpV6Address": have_inst_values["loopbackIpV6Address"]})

                            want.update({"instanceValues": json.dumps(want_inst_values)})
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

                            if replace and (len(want_e["VRF_LITE_CONN"]) != len(have_e["VRF_LITE_CONN"])):
                                # In case of replace/override if the length of want and have lite attach of a switch
                                # is not same then we have to push the want to NDFC. No further check is required for
                                # this switch
                                break

                            for wlite in want_e["VRF_LITE_CONN"]:
                                for hlite in have_e["VRF_LITE_CONN"]:
                                    found = False
                                    interface_match = False
                                    if wlite["IF_NAME"] == hlite["IF_NAME"]:
                                        found = True
                                        interface_match = True
                                        if wlite["DOT1Q_ID"]:
                                            if (
                                                wlite["DOT1Q_ID"]
                                                != hlite["DOT1Q_ID"]
                                            ):
                                                found = False
                                                break

                                        if wlite["IP_MASK"]:
                                            if (
                                                wlite["IP_MASK"]
                                                != hlite["IP_MASK"]
                                            ):
                                                found = False
                                                break

                                        if wlite["NEIGHBOR_IP"]:
                                            if (
                                                wlite["NEIGHBOR_IP"]
                                                != hlite["NEIGHBOR_IP"]
                                            ):
                                                found = False
                                                break

                                        if wlite["IPV6_MASK"]:
                                            if (
                                                wlite["IPV6_MASK"]
                                                != hlite["IPV6_MASK"]
                                            ):
                                                found = False
                                                break

                                        if wlite["IPV6_NEIGHBOR"]:
                                            if (
                                                wlite["IPV6_NEIGHBOR"]
                                                != hlite["IPV6_NEIGHBOR"]
                                            ):
                                                found = False
                                                break

                                        if wlite["PEER_VRF_NAME"]:
                                            if (
                                                wlite["PEER_VRF_NAME"]
                                                != hlite["PEER_VRF_NAME"]
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

                            if want.get("isAttached") is not None:
                                if bool(have["isAttached"]) is not bool(
                                    want["isAttached"]
                                ):
                                    del want["isAttached"]
                                    want["deployment"] = True
                                    attach_list.append(want)
                                    if bool(want["is_deploy"]):
                                        dep_vrf = True
                                    continue

                            if ((bool(want["deployment"]) is not bool(have["deployment"])) or
                               (bool(want["is_deploy"]) is not bool(have["is_deploy"]))):
                                if bool(want["is_deploy"]):
                                    dep_vrf = True

                        for k, v in want_inst_values.items():
                            if v != have_inst_values.get(k, ""):
                                found = False

                        if found:
                            break

                    if interface_match and not found:
                        break

            if not found:
                if bool(want["isAttached"]):
                    del want["isAttached"]
                    want["deployment"] = True
                    attach_list.append(want)
                    if bool(want["is_deploy"]):
                        dep_vrf = True

        return attach_list, dep_vrf

    def update_attach_params(self, attach, vrf_name, deploy, vlanId):

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
            self.module.fail_json(
                msg="Fabric: {0} does not have the switch: {1}".format(
                    self.fabric, attach["ip_address"]
                )
            )

        role = self.inventory_data[attach["ip_address"]].get("switchRole")

        if role.lower() == "spine" or role.lower() == "super spine":
            msg = "VRFs cannot be attached to switch {0} with role {1}".format(
                attach["ip_address"], role
            )
            self.module.fail_json(msg=msg)

        ext_values = {}
        ext_values["VRF_LITE_CONN"] = []
        ms_con = {}
        ms_con["MULTISITE_CONN"] = []
        ext_values["MULTISITE_CONN"] = json.dumps(ms_con)

        if attach["vrf_lite"]:
            """Before apply the vrf_lite config, need double check if the swtich role is started wth Border"""
            r = re.search(r"\bborder\b", role.lower())
            if not r:
                msg = "VRF LITE cannot be attached to switch {0} with role {1}".format(
                    attach["ip_address"], role
                )
                self.module.fail_json(msg=msg)

            at_lite = attach["vrf_lite"]
            for a_l in at_lite:
                if (
                    a_l["interface"]
                    or a_l["dot1q"]
                    or a_l["ipv4_addr"]
                    or a_l["neighbor_ipv4"]
                    or a_l["ipv6_addr"]
                    or a_l["neighbor_ipv6"]
                    or a_l["peer_vrf"]
                ):

                    """if vrf lite elements are provided by the user in the playbook fill the extension values"""
                    vrflite_con = {}
                    vrflite_con["VRF_LITE_CONN"] = []
                    vrflite_con["VRF_LITE_CONN"].append({})

                    if a_l["interface"]:
                        vrflite_con["VRF_LITE_CONN"][0]["IF_NAME"] = a_l["interface"]
                    else:
                        vrflite_con["VRF_LITE_CONN"][0]["IF_NAME"] = ""

                    if a_l["dot1q"]:
                        vrflite_con["VRF_LITE_CONN"][0]["DOT1Q_ID"] = str(a_l["dot1q"])
                    else:
                        vrflite_con["VRF_LITE_CONN"][0]["DOT1Q_ID"] = ""

                    if a_l["ipv4_addr"]:
                        vrflite_con["VRF_LITE_CONN"][0]["IP_MASK"] = a_l["ipv4_addr"]
                    else:
                        vrflite_con["VRF_LITE_CONN"][0]["IP_MASK"] = ""

                    if a_l["neighbor_ipv4"]:
                        vrflite_con["VRF_LITE_CONN"][0]["NEIGHBOR_IP"] = a_l[
                            "neighbor_ipv4"
                        ]
                    else:
                        vrflite_con["VRF_LITE_CONN"][0]["NEIGHBOR_IP"] = ""

                    if a_l["ipv6_addr"]:
                        vrflite_con["VRF_LITE_CONN"][0]["IPV6_MASK"] = a_l["ipv6_addr"]
                    else:
                        vrflite_con["VRF_LITE_CONN"][0]["IPV6_MASK"] = ""

                    if a_l["neighbor_ipv6"]:
                        vrflite_con["VRF_LITE_CONN"][0]["IPV6_NEIGHBOR"] = a_l[
                            "neighbor_ipv6"
                        ]
                    else:
                        vrflite_con["VRF_LITE_CONN"][0]["IPV6_NEIGHBOR"] = ""

                    if a_l["peer_vrf"]:
                        vrflite_con["VRF_LITE_CONN"][0]["PEER_VRF_NAME"] = a_l["peer_vrf"]
                    else:
                        vrflite_con["VRF_LITE_CONN"][0]["PEER_VRF_NAME"] = ""

                    vrflite_con["VRF_LITE_CONN"][0][
                        "VRF_LITE_JYTHON_TEMPLATE"
                    ] = "Ext_VRF_Lite_Jython"
                    if (ext_values["VRF_LITE_CONN"]):
                        ext_values["VRF_LITE_CONN"]["VRF_LITE_CONN"].extend(vrflite_con["VRF_LITE_CONN"])
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
        # freeformConfig, loopbackId. loopbackIpAddress, and loopbackIpV6Address will be copied from have
        attach.update({"freeformConfig": ""})
        inst_values = {
            "loopbackId": "",
            "loopbackIpAddress": "",
            "loopbackIpV6Address": "",
        }
        if self.dcnm_version > 11:
            inst_values.update({
                "switchRouteTargetImportEvpn": attach["import_evpn_rt"],
                "switchRouteTargetExportEvpn": attach["export_evpn_rt"],
            })
        attach.update({"instanceValues": json.dumps(inst_values).replace(" ", "")})
        if "deploy" in attach:
            del attach["deploy"]
        del attach["ip_address"]

        return attach

    def diff_for_create(self, want, have):

        conf_changed = False
        if not have:
            return {}

        create = {}

        json_to_dict_want = json.loads(want["vrfTemplateConfig"])
        json_to_dict_have = json.loads(have["vrfTemplateConfig"])

        vlanId_want = str(json_to_dict_want.get("vrfVlanId", ""))
        vlanId_have = json_to_dict_have.get("vrfVlanId", "")
        vlanName_want = json_to_dict_want.get("vrfVlanName", "")
        vlanName_have = json_to_dict_have.get("vrfVlanName", "")
        vlanIntf_want = json_to_dict_want.get("vrfIntfDescription", "")
        vlanIntf_have = json_to_dict_have.get("vrfIntfDescription", "")
        vrfDesc_want = json_to_dict_want.get("vrfDescription", "")
        vrfDesc_have = json_to_dict_have.get("vrfDescription", "")
        vrfMtu_want = str(json_to_dict_want.get("mtu", ""))
        vrfMtu_have = json_to_dict_have.get("mtu", "")
        vrfTag_want = str(json_to_dict_want.get("tag", ""))
        vrfTag_have = json_to_dict_have.get("tag", "")
        redRmap_want = json_to_dict_want.get("vrfRouteMap", "")
        redRmap_have = json_to_dict_have.get("vrfRouteMap", "")
        maxBgp_want = str(json_to_dict_want.get("maxBgpPaths", ""))
        maxBgp_have = json_to_dict_have.get("maxBgpPaths", "")
        maxiBgp_want = str(json_to_dict_want.get("maxIbgpPaths", ""))
        maxiBgp_have = json_to_dict_have.get("maxIbgpPaths", "")
        ipv6ll_want = str(json_to_dict_want.get("ipv6LinkLocalFlag", "")).lower()
        ipv6ll_have = json_to_dict_have.get("ipv6LinkLocalFlag", "")
        trmen_want = str(json_to_dict_want.get("trmEnabled", "")).lower()
        trmen_have = json_to_dict_have.get("trmEnabled", "")
        norp_want = str(json_to_dict_want.get("isRPAbsent", "")).lower()
        norp_have = json_to_dict_have.get("isRPAbsent", "")
        rpext_want = str(json_to_dict_want.get("isRPExternal", "")).lower()
        rpext_have = json_to_dict_have.get("isRPExternal", "")
        rpadd_want = json_to_dict_want.get("rpAddress", "")
        rpadd_have = json_to_dict_have.get("rpAddress", "")
        rploid_want = str(json_to_dict_want.get("loopbackNumber", ""))
        rploid_have = json_to_dict_have.get("loopbackNumber", "")
        mcastadd_want = json_to_dict_want.get("L3VniMcastGroup", "")
        mcastadd_have = json_to_dict_have.get("L3VniMcastGroup", "")
        mcastgrp_want = json_to_dict_want.get("multicastGroup", "")
        mcastgrp_have = json_to_dict_have.get("multicastGroup", "")
        trmBgwms_want = str(json_to_dict_want.get("trmBGWMSiteEnabled", "")).lower()
        trmBgwms_have = json_to_dict_have.get("trmBGWMSiteEnabled", "")
        advhrt_want = str(json_to_dict_want.get("advertiseHostRouteFlag", "")).lower()
        advhrt_have = json_to_dict_have.get("advertiseHostRouteFlag", "")
        advdrt_want = str(json_to_dict_want.get("advertiseDefaultRouteFlag", "")).lower()
        advdrt_have = json_to_dict_have.get("advertiseDefaultRouteFlag", "")
        constd_want = str(json_to_dict_want.get("configureStaticDefaultRouteFlag", "")).lower()
        constd_have = json_to_dict_have.get("configureStaticDefaultRouteFlag", "")
        bgppass_want = json_to_dict_want.get("bgpPassword", "")
        bgppass_have = json_to_dict_have.get("bgpPassword", "")
        bgppasskey_want = str(json_to_dict_want.get("bgpPasswordKeyType", ""))
        bgppasskey_have = json_to_dict_have.get("bgpPasswordKeyType", "")
        nfen_want = str(json_to_dict_want.get("ENABLE_NETFLOW", "")).lower()
        nfen_have = json_to_dict_have.get("ENABLE_NETFLOW", "")
        nfmon_want = json_to_dict_want.get("NETFLOW_MONITOR", "")
        nfmon_have = json_to_dict_have.get("NETFLOW_MONITOR", "")
        disrtauto_want = str(json_to_dict_want.get("disableRtAuto", "")).lower()
        disrtauto_have = json_to_dict_have.get("disableRtAuto", "")
        rtvpnImp_want = json_to_dict_want.get("routeTargetImport", "")
        rtvpnImp_have = json_to_dict_have.get("routeTargetImport", "")
        rtvpnExp_want = json_to_dict_want.get("routeTargetExport", "")
        rtvpnExp_have = json_to_dict_have.get("routeTargetExport", "")
        rtevpnImp_want = json_to_dict_want.get("routeTargetImportEvpn", "")
        rtevpnImp_have = json_to_dict_have.get("routeTargetImportEvpn", "")
        rtevpnExp_want = json_to_dict_want.get("routeTargetExportEvpn", "")
        rtevpnExp_have = json_to_dict_have.get("routeTargetExportEvpn", "")
        rtmvpnImp_want = json_to_dict_want.get("routeTargetImportMvpn", "")
        rtmvpnImp_have = json_to_dict_have.get("routeTargetImportMvpn", "")
        rtmvpnExp_want = json_to_dict_want.get("routeTargetExportMvpn", "")
        rtmvpnExp_have = json_to_dict_have.get("routeTargetExportMvpn", "")

        if vlanId_want != "0":

            if want["vrfId"] is not None and have["vrfId"] != want["vrfId"]:
                self.module.fail_json(
                    msg="vrf_id for vrf:{0} cant be updated to a different value".format(
                        want["vrfName"]
                    )
                )
            elif (
                have["serviceVrfTemplate"] != want["serviceVrfTemplate"]
                or have["vrfTemplate"] != want["vrfTemplate"]
                or have["vrfExtensionTemplate"] != want["vrfExtensionTemplate"]
                or vlanId_have != vlanId_want
                or vlanName_have != vlanName_want
                or vlanIntf_have != vlanIntf_want
                or vrfDesc_have != vrfDesc_want
                or vrfMtu_have != vrfMtu_want
                or vrfTag_have != vrfTag_want
                or redRmap_have != redRmap_want
                or maxBgp_have != maxBgp_want
                or maxiBgp_have != maxiBgp_want
                or ipv6ll_have != ipv6ll_want
                or trmen_have != trmen_want
                or norp_have != norp_want
                or rpext_have != rpext_want
                or rpadd_have != rpadd_want
                or rploid_have != rploid_want
                or mcastadd_have != mcastadd_want
                or mcastgrp_have != mcastgrp_want
                or trmBgwms_have != trmBgwms_want
                or advhrt_have != advhrt_want
                or advdrt_have != advdrt_want
                or constd_have != constd_want
                or bgppass_have != bgppass_want
                or bgppasskey_have != bgppasskey_want
                or nfen_have != nfen_want
                or nfmon_have != nfmon_want
                or disrtauto_have != disrtauto_want
                or rtvpnImp_have != rtvpnImp_want
                or rtvpnExp_have != rtvpnExp_want
                or rtevpnImp_have != rtevpnImp_want
                or rtevpnExp_have != rtevpnExp_want
                or rtmvpnImp_have != rtmvpnImp_want
                or rtmvpnExp_have != rtmvpnExp_want
            ):

                conf_changed = True
                if want["vrfId"] is None:
                    # The vrf updates with missing vrfId will have to use existing
                    # vrfId from the instance of the same vrf on DCNM.
                    want["vrfId"] = have["vrfId"]
                create = want
            else:
                pass

        else:

            if want["vrfId"] is not None and have["vrfId"] != want["vrfId"]:
                self.module.fail_json(
                    msg="vrf_id for vrf:{0} cant be updated to a different value".format(
                        want["vrfName"]
                    )
                )
            elif (
                have["serviceVrfTemplate"] != want["serviceVrfTemplate"]
                or have["vrfTemplate"] != want["vrfTemplate"]
                or have["vrfExtensionTemplate"] != want["vrfExtensionTemplate"]
                or vlanName_have != vlanName_want
                or vlanIntf_have != vlanIntf_want
                or vrfDesc_have != vrfDesc_want
                or vrfMtu_have != vrfMtu_want
                or vrfTag_have != vrfTag_want
                or redRmap_have != redRmap_want
                or maxBgp_have != maxBgp_want
                or maxiBgp_have != maxiBgp_want
                or ipv6ll_have != ipv6ll_want
                or trmen_have != trmen_want
                or norp_have != norp_want
                or rpext_have != rpext_want
                or rpadd_have != rpadd_want
                or rploid_have != rploid_want
                or mcastadd_have != mcastadd_want
                or mcastgrp_have != mcastgrp_want
                or trmBgwms_have != trmBgwms_want
                or advhrt_have != advhrt_want
                or advdrt_have != advdrt_want
                or constd_have != constd_want
                or bgppass_have != bgppass_want
                or bgppasskey_have != bgppasskey_want
                or nfen_have != nfen_want
                or nfmon_have != nfmon_want
                or disrtauto_have != disrtauto_want
                or rtvpnImp_have != rtvpnImp_want
                or rtvpnExp_have != rtvpnExp_want
                or rtevpnImp_have != rtevpnImp_want
                or rtevpnExp_have != rtevpnExp_want
                or rtmvpnImp_have != rtmvpnImp_want
                or rtmvpnExp_have != rtmvpnExp_want
            ):

                conf_changed = True
                if want["vrfId"] is None:
                    # The vrf updates with missing vrfId will have to use existing
                    # vrfId from the instance of the same vrf on DCNM.
                    want["vrfId"] = have["vrfId"]
                create = want
            else:
                pass

        return create, conf_changed

    def update_create_params(self, vrf, vlanId=""):

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

    def get_have(self):

        have_create = []
        have_deploy = {}

        curr_vrfs = ""

        method = "GET"
        path = self.paths["GET_VRF"].format(self.fabric)

        vrf_objects = dcnm_send(self.module, method, path)

        missing_fabric, not_ok = self.handle_response(vrf_objects, "query_dcnm")

        if missing_fabric or not_ok:
            msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find vrfs under fabric: {0}".format(self.fabric)

            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

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
                "advertiseHostRouteFlag": json_to_dict.get("advertiseHostRouteFlag", False),
                "advertiseDefaultRouteFlag": json_to_dict.get("advertiseDefaultRouteFlag", True),
                "configureStaticDefaultRouteFlag": json_to_dict.get("configureStaticDefaultRouteFlag", True),
                "bgpPassword": json_to_dict.get("bgpPassword", ""),
                "bgpPasswordKeyType": json_to_dict.get("bgpPasswordKeyType", ""),
            }

            if self.dcnm_version > 11:
                t_conf.update(isRPAbsent=json_to_dict.get("isRPAbsent", False))
                t_conf.update(ENABLE_NETFLOW=json_to_dict.get("ENABLE_NETFLOW", False))
                t_conf.update(NETFLOW_MONITOR=json_to_dict.get("NETFLOW_MONITOR", ""))
                t_conf.update(disableRtAuto=json_to_dict.get("disableRtAuto", False))
                t_conf.update(routeTargetImport=json_to_dict.get("routeTargetImport", ""))
                t_conf.update(routeTargetExport=json_to_dict.get("routeTargetExport", ""))
                t_conf.update(routeTargetImportEvpn=json_to_dict.get("routeTargetImportEvpn", ""))
                t_conf.update(routeTargetExportEvpn=json_to_dict.get("routeTargetExportEvpn", ""))
                t_conf.update(routeTargetImportMvpn=json_to_dict.get("routeTargetImportMvpn", ""))
                t_conf.update(routeTargetExportMvpn=json_to_dict.get("routeTargetExportMvpn", ""))

            vrf.update({"vrfTemplateConfig": json.dumps(t_conf)})
            del vrf["vrfStatus"]
            have_create.append(vrf)

        upd_vrfs = ""

        for vrf_attach in vrf_attach_objects["DATA"]:
            if not vrf_attach.get("lanAttachList"):
                continue
            attach_list = vrf_attach["lanAttachList"]
            dep_vrf = ""
            for attach in attach_list:
                attach_state = False if attach["lanAttachState"] == "NA" else True
                deploy = attach["isLanAttached"]
                deployed = False
                if bool(deploy) and (
                    attach["lanAttachState"] == "OUT-OF-SYNC"
                    or attach["lanAttachState"] == "PENDING"
                ):
                    deployed = False
                else:
                    deployed = True

                if bool(deployed):
                    dep_vrf = attach["vrfName"]

                sn = attach["switchSerialNo"]
                vlan = attach["vlanId"]
                inst_values = attach.get("instanceValues", None)

                # The deletes and updates below are done to update the incoming dictionary format to
                # match to what the outgoing payload requirements mandate.
                # Ex: 'vlanId' in the attach section of incoming payload needs to be changed to 'vlan'
                # on the attach section of outgoing payload.

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

                """ Get the VRF LITE extension template and update it to the attach['extensionvalues']"""

                """Get the IP/Interface that is connected to edge router can be get from below query"""
                method = "GET"
                path = self.paths["GET_VRF_SWITCH"].format(
                    self.fabric, attach["vrfName"], sn
                )

                lite_objects = dcnm_send(self.module, method, path)

                if not lite_objects.get("DATA"):
                    return

                for sdl in lite_objects["DATA"]:
                    for epv in sdl["switchDetailsList"]:
                        if epv.get("extensionValues"):
                            ext_values = epv["extensionValues"]
                            ext_values = ast.literal_eval(ext_values)
                            if ext_values.get("VRF_LITE_CONN") is not None:
                                ext_values = ast.literal_eval(
                                    ext_values["VRF_LITE_CONN"]
                                )
                                extension_values = {}
                                extension_values["VRF_LITE_CONN"] = []

                                for ev in ext_values.get("VRF_LITE_CONN"):
                                    vrflite_con = {}

                                    vrflite_con["VRF_LITE_CONN"] = []
                                    vrflite_con["VRF_LITE_CONN"].append({})
                                    vrflite_con["VRF_LITE_CONN"][0]["IF_NAME"] = ev[
                                        "IF_NAME"
                                    ]
                                    vrflite_con["VRF_LITE_CONN"][0]["DOT1Q_ID"] = str(
                                        ev["DOT1Q_ID"]
                                    )
                                    vrflite_con["VRF_LITE_CONN"][0]["IP_MASK"] = ev[
                                        "IP_MASK"
                                    ]
                                    vrflite_con["VRF_LITE_CONN"][0]["NEIGHBOR_IP"] = ev[
                                        "NEIGHBOR_IP"
                                    ]
                                    vrflite_con["VRF_LITE_CONN"][0]["IPV6_MASK"] = ev[
                                        "IPV6_MASK"
                                    ]
                                    vrflite_con["VRF_LITE_CONN"][0][
                                        "IPV6_NEIGHBOR"
                                    ] = ev["IPV6_NEIGHBOR"]

                                    vrflite_con["VRF_LITE_CONN"][0][
                                        "AUTO_VRF_LITE_FLAG"
                                    ] = "false"
                                    vrflite_con["VRF_LITE_CONN"][0][
                                        "PEER_VRF_NAME"
                                    ] = ev["PEER_VRF_NAME"]
                                    vrflite_con["VRF_LITE_CONN"][0][
                                        "VRF_LITE_JYTHON_TEMPLATE"
                                    ] = "Ext_VRF_Lite_Jython"

                                    if (extension_values["VRF_LITE_CONN"]):
                                        extension_values["VRF_LITE_CONN"]["VRF_LITE_CONN"].extend(vrflite_con["VRF_LITE_CONN"])
                                    else:
                                        extension_values["VRF_LITE_CONN"] = vrflite_con

                                extension_values["VRF_LITE_CONN"] = json.dumps(
                                    extension_values["VRF_LITE_CONN"]
                                )

                                ms_con = {}
                                ms_con["MULTISITE_CONN"] = []
                                extension_values["MULTISITE_CONN"] = json.dumps(
                                    ms_con
                                )
                                e_values = json.dumps(extension_values).replace(
                                    " ", ""
                                )

                                attach.update({"extensionValues": e_values})

                        ff_config = epv.get("freeformConfig", "")
                        attach.update({"freeformConfig": ff_config})

            if dep_vrf:
                upd_vrfs += dep_vrf + ","

        have_attach = vrf_attach_objects["DATA"]

        if upd_vrfs:
            have_deploy.update({"vrfNames": upd_vrfs[:-1]})

        self.have_create = have_create
        self.have_attach = have_attach
        self.have_deploy = have_deploy

    def get_want(self):

        want_create = []
        want_attach = []
        want_deploy = {}

        all_vrfs = ""

        if not self.config:
            return

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

    def get_diff_delete(self):

        diff_detach = []
        diff_undeploy = {}
        diff_delete = {}

        all_vrfs = ""

        if self.config:

            for want_c in self.want_create:
                if not next(
                    (
                        have_c
                        for have_c in self.have_create
                        if have_c["vrfName"] == want_c["vrfName"]
                    ),
                    None,
                ):
                    continue
                diff_delete.update({want_c["vrfName"]: "DEPLOYED"})

                have_a = next(
                    (
                        attach
                        for attach in self.have_attach
                        if attach["vrfName"] == want_c["vrfName"]
                    ),
                    None,
                )

                if not have_a:
                    continue

                to_del = []
                atch_h = have_a["lanAttachList"]
                for a_h in atch_h:
                    if a_h["isAttached"]:
                        del a_h["isAttached"]
                        a_h.update({"deployment": False})
                        to_del.append(a_h)
                if to_del:
                    have_a.update({"lanAttachList": to_del})
                    diff_detach.append(have_a)
                    all_vrfs += have_a["vrfName"] + ","
            if all_vrfs:
                diff_undeploy.update({"vrfNames": all_vrfs[:-1]})

        else:
            for have_a in self.have_attach:
                to_del = []
                atch_h = have_a["lanAttachList"]
                for a_h in atch_h:
                    if a_h["isAttached"]:
                        del a_h["isAttached"]
                        a_h.update({"deployment": False})
                        to_del.append(a_h)
                if to_del:
                    have_a.update({"lanAttachList": to_del})
                    diff_detach.append(have_a)
                    all_vrfs += have_a["vrfName"] + ","

                diff_delete.update({have_a["vrfName"]: "DEPLOYED"})
            if all_vrfs:
                diff_undeploy.update({"vrfNames": all_vrfs[:-1]})

        self.diff_detach = diff_detach
        self.diff_undeploy = diff_undeploy
        self.diff_delete = diff_delete

    def get_diff_override(self):

        all_vrfs = ""
        diff_delete = {}

        self.get_diff_replace()

        diff_create = self.diff_create
        diff_attach = self.diff_attach
        diff_detach = self.diff_detach
        diff_deploy = self.diff_deploy
        diff_undeploy = self.diff_undeploy

        for have_a in self.have_attach:
            found = next(
                (
                    vrf
                    for vrf in self.want_create
                    if vrf["vrfName"] == have_a["vrfName"]
                ),
                None,
            )
            to_del = []
            if not found:
                atch_h = have_a["lanAttachList"]
                for a_h in atch_h:
                    if a_h["isAttached"]:
                        del a_h["isAttached"]
                        a_h.update({"deployment": False})
                        to_del.append(a_h)

                if to_del:
                    have_a.update({"lanAttachList": to_del})
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

    def get_diff_replace(self):

        all_vrfs = ""

        self.get_diff_merge(replace=True)
        diff_create = self.diff_create
        diff_attach = self.diff_attach
        diff_deploy = self.diff_deploy

        for have_a in self.have_attach:
            r_vrf_list = []
            h_in_w = False
            for want_a in self.want_attach:
                if have_a["vrfName"] == want_a["vrfName"]:
                    h_in_w = True
                    atch_h = have_a["lanAttachList"]
                    atch_w = want_a.get("lanAttachList")

                    for a_h in atch_h:
                        if not a_h["isAttached"]:
                            continue
                        a_match = False

                        if atch_w:
                            for a_w in atch_w:
                                if a_h["serialNumber"] == a_w["serialNumber"]:
                                    # Have is already in diff, no need to continue looking for it.
                                    a_match = True
                                    break
                        if not a_match:
                            del a_h["isAttached"]
                            a_h.update({"deployment": False})
                            r_vrf_list.append(a_h)
                    break

            if not h_in_w:
                found = next(
                    (
                        vrf
                        for vrf in self.want_create
                        if vrf["vrfName"] == have_a["vrfName"]
                    ),
                    None,
                )
                if found:
                    atch_h = have_a["lanAttachList"]
                    for a_h in atch_h:
                        if not bool(a_h["isAttached"]):
                            continue
                        del a_h["isAttached"]
                        a_h.update({"deployment": False})
                        r_vrf_list.append(a_h)

            if r_vrf_list:
                in_diff = False
                for d_attach in self.diff_attach:
                    if have_a["vrfName"] == d_attach["vrfName"]:
                        in_diff = True
                        d_attach["lanAttachList"].extend(r_vrf_list)
                        break

                if not in_diff:
                    r_vrf_dict = {
                        "vrfName": have_a["vrfName"],
                        "lanAttachList": r_vrf_list,
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

    def get_diff_merge(self, replace=False):

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
                            msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
                            msg2 = (
                                "Unable to generate vrfId for vrf: {0} "
                                "under fabric: {1}".format(
                                    want_c["vrfName"], self.fabric
                                )
                            )

                            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

                        if not vrf_id_obj["DATA"]:
                            continue

                        if self.dcnm_version == 11:
                            vrf_id = vrf_id_obj["DATA"].get("partitionSegmentId")
                        elif self.dcnm_version >= 12:
                            vrf_id = vrf_id_obj["DATA"].get("l3vni")
                        else:
                            msg = "Unsupported DCNM version: version {0}".format(
                                self.dcnm_version
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
                                "advertiseHostRouteFlag": json_to_dict.get("advertiseHostRouteFlag"),
                                "advertiseDefaultRouteFlag": json_to_dict.get("advertiseDefaultRouteFlag"),
                                "configureStaticDefaultRouteFlag": json_to_dict.get("configureStaticDefaultRouteFlag"),
                                "bgpPassword": json_to_dict.get("bgpPassword"),
                                "bgpPasswordKeyType": json_to_dict.get("bgpPasswordKeyType"),
                            }

                            if self.dcnm_version > 11:
                                template_conf.update(isRPAbsent=json_to_dict.get("isRPAbsent"))
                                template_conf.update(ENABLE_NETFLOW=json_to_dict.get("ENABLE_NETFLOW"))
                                template_conf.update(NETFLOW_MONITOR=json_to_dict.get("NETFLOW_MONITOR"))
                                template_conf.update(disableRtAuto=json_to_dict.get("disableRtAuto"))
                                template_conf.update(routeTargetImport=json_to_dict.get("routeTargetImport"))
                                template_conf.update(routeTargetExport=json_to_dict.get("routeTargetExport"))
                                template_conf.update(routeTargetImportEvpn=json_to_dict.get("routeTargetImportEvpn"))
                                template_conf.update(routeTargetExportEvpn=json_to_dict.get("routeTargetExportEvpn"))
                                template_conf.update(routeTargetImportMvpn=json_to_dict.get("routeTargetImportMvpn"))
                                template_conf.update(routeTargetExportMvpn=json_to_dict.get("routeTargetExportMvpn"))

                            want_c.update(
                                {"vrfTemplateConfig": json.dumps(template_conf)}
                            )
                            prev_vrf_id_fetched = vrf_id
                            break

                    if not vrf_id:
                        self.module.fail_json(
                            msg="Unable to generate vrfId for vrf: {0} "
                            "under fabric: {1}".format(want_c["vrfName"], self.fabric)
                        )

                    create_path = self.paths["GET_VRF"].format(self.fabric)

                    diff_create_quick.append(want_c)

                    if self.module.check_mode:
                        continue

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
            dep_vrf = ""
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
                            dep_vrf = want_a["vrfName"]
                    else:
                        if vrf or conf_changed.get(want_a["vrfName"], False):
                            dep_vrf = want_a["vrfName"]

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
                    if bool(attach["is_deploy"]):
                        dep_vrf = want_a["vrfName"]

                for atch in atch_list:
                    atch["deployment"] = True

            if dep_vrf:
                all_vrfs += dep_vrf + ","

        if all_vrfs:
            diff_deploy.update({"vrfNames": all_vrfs[:-1]})

        self.diff_create = diff_create
        self.diff_create_update = diff_create_update
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy
        self.diff_create_quick = diff_create_quick

    def format_diff(self):

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

            found_a = next(
                (vrf for vrf in diff_attach if vrf["vrfName"] == want_d["vrfName"]),
                None,
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
            found_c.update({"vrf_intf_desc": json_to_dict.get("vrfIntfDescription", "")})
            found_c.update({"vrf_description": json_to_dict.get("vrfDescription", "")})
            found_c.update({"vrf_int_mtu": json_to_dict.get("mtu", "")})
            found_c.update({"loopback_route_tag": json_to_dict.get("tag", "")})
            found_c.update({"redist_direct_rmap": json_to_dict.get("vrfRouteMap", "")})
            found_c.update({"max_bgp_paths": json_to_dict.get("maxBgpPaths", "")})
            found_c.update({"max_ibgp_paths": json_to_dict.get("maxIbgpPaths", "")})
            found_c.update({"ipv6_linklocal_enable": json_to_dict.get("ipv6LinkLocalFlag", True)})
            found_c.update({"trm_enable": json_to_dict.get("trmEnabled", False)})
            found_c.update({"rp_external": json_to_dict.get("isRPExternal", False)})
            found_c.update({"rp_address": json_to_dict.get("rpAddress", "")})
            found_c.update({"rp_loopback_id": json_to_dict.get("loopbackNumber", "")})
            found_c.update({"underlay_mcast_ip": json_to_dict.get("L3VniMcastGroup", "")})
            found_c.update({"overlay_mcast_group": json_to_dict.get("multicastGroup", "")})
            found_c.update({"trm_bgw_msite": json_to_dict.get("trmBGWMSiteEnabled", False)})
            found_c.update({"adv_host_routes": json_to_dict.get("advertiseHostRouteFlag", False)})
            found_c.update({"adv_default_routes": json_to_dict.get("advertiseDefaultRouteFlag", True)})
            found_c.update({"static_default_route": json_to_dict.get("configureStaticDefaultRouteFlag", True)})
            found_c.update({"bgp_password": json_to_dict.get("bgpPassword", "")})
            found_c.update({"bgp_passwd_encrypt": json_to_dict.get("bgpPasswordKeyType", "")})
            if self.dcnm_version > 11:
                found_c.update({"no_rp": json_to_dict.get("isRPAbsent", False)})
                found_c.update({"netflow_enable": json_to_dict.get("ENABLE_NETFLOW", True)})
                found_c.update({"nf_monitor": json_to_dict.get("NETFLOW_MONITOR", "")})
                found_c.update({"disable_rt_auto": json_to_dict.get("disableRtAuto", False)})
                found_c.update({"import_vpn_rt": json_to_dict.get("routeTargetImport", "")})
                found_c.update({"export_vpn_rt": json_to_dict.get("routeTargetExport", "")})
                found_c.update({"import_evpn_rt": json_to_dict.get("routeTargetImportEvpn", "")})
                found_c.update({"export_evpn_rt": json_to_dict.get("routeTargetExportEvpn", "")})
                found_c.update({"import_mvpn_rt": json_to_dict.get("routeTargetImportMvpn", "")})
                found_c.update({"export_mvpn_rt": json_to_dict.get("routeTargetExportMvpn", "")})

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

    def get_diff_query(self):

        method = "GET"
        path = self.paths["GET_VRF"].format(self.fabric)
        vrf_objects = dcnm_send(self.module, method, path)
        missing_fabric, not_ok = self.handle_response(vrf_objects, "query_dcnm")

        if (
            vrf_objects.get("ERROR") == "Not Found"
            and vrf_objects.get("RETURN_CODE") == 404
        ):
            self.module.fail_json(
                msg="Fabric {0} not present on DCNM".format(self.fabric)
            )
            return

        if missing_fabric or not_ok:
            msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find VRFs under fabric: {0}".format(self.fabric)
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
                            msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
                            msg2 = (
                                "Unable to find attachments for "
                                "vrfs: {0} under fabric: {1}".format(
                                    vrf["vrfName"], self.fabric
                                )
                            )

                            self.module.fail_json(msg=msg1 if missing_fabric else msg2)
                            return

                        if not vrf_attach_objects["DATA"]:
                            return

                        for vrf_attach in vrf_attach_objects["DATA"]:
                            if want_c["vrfName"] == vrf_attach["vrfName"]:
                                if not vrf_attach.get("lanAttachList"):
                                    continue
                                attach_list = vrf_attach["lanAttachList"]

                                for attach in attach_list:
                                    path = self.paths["GET_VRF_SWITCH"].format(
                                        self.fabric,
                                        attach["vrfName"],
                                        attach["switchSerialNo"],
                                    )
                                    lite_objects = dcnm_send(self.module, method, path)
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
                    msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
                    msg2 = (
                        "Unable to find attachments for "
                        "vrfs: {0} under fabric: {1}".format(
                            vrf["vrfName"], self.fabric
                        )
                    )

                    self.module.fail_json(msg=msg1 if missing_fabric else msg2)
                    return

                if not vrf_attach_objects["DATA"]:
                    return

                for vrf_attach in vrf_attach_objects["DATA"]:
                    if not vrf_attach.get("lanAttachList"):
                        continue
                    attach_list = vrf_attach["lanAttachList"]

                    for attach in attach_list:
                        path = self.paths["GET_VRF_SWITCH"].format(
                            self.fabric, attach["vrfName"], attach["switchSerialNo"]
                        )

                        lite_objects = dcnm_send(self.module, method, path)
                        if not lite_objects.get("DATA"):
                            return
                        item["attach"].append(lite_objects.get("DATA")[0])
                    query.append(item)

        self.query = query

    def push_to_remote(self, is_rollback=False):

        path = self.paths["GET_VRF"].format(self.fabric)

        method = "PUT"
        if self.diff_create_update:
            for vrf in self.diff_create_update:
                update_path = path + "/{0}".format(vrf["vrfName"])
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
            self.result["response"].append(
                "Deletion of vrfs {0} has failed".format(del_failure[:-1])
            )
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
                        self.module.fail_json(
                            msg="Failure getting autogenerated vlan_id {0}".format(
                                vlan_data
                            )
                        )
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
                    "advertiseHostRouteFlag": json_to_dict.get("advertiseHostRouteFlag"),
                    "advertiseDefaultRouteFlag": json_to_dict.get("advertiseDefaultRouteFlag"),
                    "configureStaticDefaultRouteFlag": json_to_dict.get("configureStaticDefaultRouteFlag"),
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
                    t_conf.update(routeTargetImportEvpn=json_to_dict.get("routeTargetImportEvpn"))
                    t_conf.update(routeTargetExportEvpn=json_to_dict.get("routeTargetExportEvpn"))
                    t_conf.update(routeTargetImportMvpn=json_to_dict.get("routeTargetImportMvpn"))
                    t_conf.update(routeTargetExportMvpn=json_to_dict.get("routeTargetExportMvpn"))

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
                                    msg = "VRF LITE cannot be attached to switch {0} with role {1}".format(
                                        ip, role
                                    )
                                    self.module.fail_json(msg=msg)

                        """Get the IP/Interface that is connected to edge router can be get from below query"""
                        method = "GET"
                        path = self.paths["GET_VRF_SWITCH"].format(
                            self.fabric, v_a["vrfName"], v_a["serialNumber"]
                        )

                        lite_objects = dcnm_send(self.module, method, path)

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
                            if str(ext_l.get("extensionType")) == "VRF_LITE":
                                ext_values = ext_l["extensionValues"]
                                ext_values = ast.literal_eval(ext_values)
                                for ad_l in v_a.get("vrf_lite"):
                                    if ad_l["interface"] == ext_values["IF_NAME"]:
                                        vrflite_con = {}
                                        vrflite_con["VRF_LITE_CONN"] = []
                                        vrflite_con["VRF_LITE_CONN"].append({})
                                        vrflite_con["VRF_LITE_CONN"][0][
                                            "IF_NAME"
                                        ] = ad_l["interface"]

                                        if ad_l["dot1q"]:
                                            vrflite_con["VRF_LITE_CONN"][0][
                                                "DOT1Q_ID"
                                            ] = str(ad_l["dot1q"])
                                        else:
                                            vrflite_con["VRF_LITE_CONN"][0][
                                                "DOT1Q_ID"
                                            ] = str(ext_values["DOT1Q_ID"])

                                        if ad_l["ipv4_addr"]:
                                            vrflite_con["VRF_LITE_CONN"][0][
                                                "IP_MASK"
                                            ] = ad_l["ipv4_addr"]
                                        else:
                                            vrflite_con["VRF_LITE_CONN"][0][
                                                "IP_MASK"
                                            ] = ext_values["IP_MASK"]

                                        if ad_l["neighbor_ipv4"]:
                                            vrflite_con["VRF_LITE_CONN"][0][
                                                "NEIGHBOR_IP"
                                            ] = ad_l["neighbor_ipv4"]
                                        else:
                                            vrflite_con["VRF_LITE_CONN"][0][
                                                "NEIGHBOR_IP"
                                            ] = ext_values["NEIGHBOR_IP"]

                                        vrflite_con["VRF_LITE_CONN"][0][
                                            "NEIGHBOR_ASN"
                                        ] = ext_values["NEIGHBOR_ASN"]

                                        if ad_l["ipv6_addr"]:
                                            vrflite_con["VRF_LITE_CONN"][0][
                                                "IPV6_MASK"
                                            ] = ad_l["ipv6_addr"]
                                        else:
                                            vrflite_con["VRF_LITE_CONN"][0][
                                                "IPV6_MASK"
                                            ] = ext_values["IPV6_MASK"]

                                        if ad_l["neighbor_ipv6"]:
                                            vrflite_con["VRF_LITE_CONN"][0][
                                                "IPV6_NEIGHBOR"
                                            ] = ad_l["neighbor_ipv6"]
                                        else:
                                            vrflite_con["VRF_LITE_CONN"][0][
                                                "IPV6_NEIGHBOR"
                                            ] = ext_values["IPV6_NEIGHBOR"]

                                        vrflite_con["VRF_LITE_CONN"][0][
                                            "AUTO_VRF_LITE_FLAG"
                                        ] = ext_values["AUTO_VRF_LITE_FLAG"]

                                        if ad_l["peer_vrf"]:
                                            vrflite_con["VRF_LITE_CONN"][0][
                                                "PEER_VRF_NAME"
                                            ] = ad_l["peer_vrf"]
                                        else:
                                            vrflite_con["VRF_LITE_CONN"][0][
                                                "PEER_VRF_NAME"
                                            ] = ext_values["PEER_VRF_NAME"]

                                        vrflite_con["VRF_LITE_CONN"][0][
                                            "VRF_LITE_JYTHON_TEMPLATE"
                                        ] = "Ext_VRF_Lite_Jython"
                                        if (extension_values["VRF_LITE_CONN"]):
                                            extension_values["VRF_LITE_CONN"]["VRF_LITE_CONN"].extend(vrflite_con["VRF_LITE_CONN"])
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
                                if ser == v_a["serialNumber"]:
                                    msg = "There is no VRF LITE capable interface on this switch {0}".format(
                                        ip
                                    )
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
                        for atch in attach_list:
                            if (
                                atch["lanAttachState"] == "OUT-OF-SYNC"
                                or atch["lanAttachState"] == "FAILED"
                            ):
                                self.diff_delete.update({vrf: "OUT-OF-SYNC"})
                                break
                            if atch["lanAttachState"] != "NA":
                                self.diff_delete.update({vrf: "DEPLOYED"})
                                state = False
                                time.sleep(self.WAIT_TIME_FOR_DELETE_LOOP)
                                break
                            self.diff_delete.update({vrf: "NA"})

            return True

    def validate_input(self):
        """Parse the playbook values, validate to param specs."""

        state = self.params["state"]

        if state == "merged" or state == "overridden" or state == "replaced":

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
                vrf_int_mtu=dict(type="int", range_min=68, range_max=9216, default=9216),
                loopback_route_tag=dict(type="int", default=12345, range_max=4294967295),
                redist_direct_rmap=dict(type="str", default="FABRIC-RMAP-REDIST-SUBNET"),
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
                if state == "merged" or state == "replaced":
                    msg = "config: element is mandatory for this state {0}".format(
                        state
                    )

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
                vrf_int_mtu=dict(type="int", range_min=68, range_max=9216, default=9216),
                loopback_route_tag=dict(type="int", default=12345, range_max=4294967295),
                redist_direct_rmap=dict(type="str", default="FABRIC-RMAP-REDIST-SUBNET"),
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

        # Donot Rollback for Multi-site fabrics
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
        module.fail_json(
            msg="Fabric {0} missing on DCNM or does not have any switches".format(
                dcnm_vrf.fabric
            )
        )

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
