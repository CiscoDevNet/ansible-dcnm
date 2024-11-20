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
__author__ = "Mallik Mudigonda"

DOCUMENTATION = """
---
module: dcnm_interface
short_description: DCNM Ansible Module for managing interfaces.
version_added: "0.9.0"
description:
    - "DCNM Ansible Module for the following interface service operations"
    - "Create, Delete, Modify PortChannel, VPC, Loopback and Sub-Interfaces"
    - "Modify Ethernet Interfaces"
author: Mallik Mudigonda(@mmudigon)
options:
  check_deploy:
    description:
    - Deploy operations may take considerable time in certain cases based on the configuration included
      in the playbook. A success response from DCNM server does not guarantee the completion of deploy
      operation. This flag if set indicates that the module should verify if the configured state is in
      sync with what is requested in playbook. If not set the module will return without verifying the
      state.
    type: bool
    required: false
    default: false
  fabric:
    description:
    - Name of the target fabric for interface operations
    type: str
    required: true
  state:
    description:
    - The required state of the configuration after module completion.
    type: str
    choices: ['merged', 'replaced', 'overridden', 'deleted', 'query']
    default: merged
  deploy:
    description:
    - Flag indicating if the configuration must be pushed to the switch. This flag is used to decide the deploy behavior in
      'deleted' and 'overridden' states as mentioned below
    - In 'overridden' state this flag will be used to deploy deleted interfaces.
    - In 'deleted' state this flag will be used to deploy deleted interfaces when a specific 'config' block is not
      included.
    - The 'deploy' flags included with individual interface configuration elements under the 'config' block will take precedence
       over this global flag.
    type: bool
    default: true
  override_intf_types:
    description:
    - A list of interface types which will be deleted/defaulted in overridden/deleted state. If this list is empty, then during
      overridden/deleted state, all interface types will be defaulted/deleted. If this list includes specific interface types,
      then only those interface types that are included in the list will be deleted/defaulted.
    type: list
    required: false
    elements: str
    choices: ["pc", "vpc", "sub_int", "lo", "eth", "svi", "st_fex", "aa_fex"]
    default: []
  config:
    description:
    - A dictionary of interface operations
    type: list
    elements: dict
    default: []
    suboptions:
      name:
        description:
        - Name of the interface. Example, po55, eth2/1, lo100, vpc25, eth1/1.1.
        type: str
        required: true
      switch:
        description:
        - IP address or DNS name of the management interface. All switches mentioned in this list
          will be deployed with the included configuration. For vPC interfaces
          this list object will contain elements each of which is a list of
          pair of switches
        type: list
        elements: str
        required: true
      type:
        description:
        - Interface type. Example, pc, vpc, sub_int, lo, eth, svi
        type: str
        required: true
        choices: ['pc', 'vpc', 'sub_int', 'lo', 'eth', 'svi', 'st-fex', 'aa-fex']
      deploy:
        description:
        - Flag indicating if the configuration must be pushed to the switch. If not included
          it is considered true by default
        type: bool
        default: true
      profile_pc:
        description:
        - Though the key shown here is 'profile_pc' the actual key to be used in playbook
          is 'profile'. The key 'profile_pc' is used here to logically segregate the interface objects applicable for this profile
        - Object profile which must be included for port channel interface configurations.
        suboptions:
          mode:
            description:
            - Interface mode
            choices: ['trunk', 'access', 'l3', 'monitor']
            type: str
            required: true
          members:
            description:
            - Member interfaces that are part of this port channel
            type: list
            elements: str
            required: true
          access_vlan:
            description:
            - Vlan for the interface. This option is applicable only for interfaces whose 'mode' is 'access'
            type: str
            default: ""
          int_vrf:
            description:
            - Interface VRF name. This object is applicable only if the 'mode' is 'l3'
            type: str
            default: default
          ipv4_addr:
            description:
            - IPV4 address of the interface. This object is applicable only if the 'mode' is 'l3'
            type: str
            default: ""
          ipv4_mask_len:
            description:
            - IPV4 address mask length. This object is applicable only if the 'mode' is 'l3'
            - Minimum Value (1), Maximum Value (31)
            type: int
            default: 8
          route_tag:
            description:
            - Route tag associated with the interface IP. This object is applicable only if the 'mode' is 'l3'
            type: str
            default: ""
          cmds:
            description:
            - Commands to be included in the configuration under this interface
            type: list
            elements: str
            default: []
          description:
            description:
            - Description of the interface
            type: str
            default: ""
          admin_state:
            description:
            - Administrative state of the interface
            type: bool
            default: true
      profile_vpc:
        description:
        - Though the key shown here is 'profile_vpc' the actual key to be used in playbook
          is 'profile'. The key 'profile_vpc' is used here to logically segregate the interface
          objects applicable for this profile
        - Object profile which must be included for virtual port channel inetrface configurations.
        suboptions:
          mode:
            description:
            -  Interface mode
            choices: ['trunk', 'access']
            type: str
            required: true
          peer1_pcid:
            description:
            - Port channel identifier of first peer. If this object is not included, then the value defaults to the
              vPC identifier. This value cannot be changed once vPC is created
            - Minimum Value (1), Maximum Value (4096)
            - Default value if not specified is the vPC port identifier
            type: int
          peer2_pcid:
            description:
            - Port channel identifier of second peer. If this object is not included, then the value defaults to the
              vPC identifier. This value cannot be changed once vPC is created
            - Minimum Value (1), Maximum Value (4096)
            - Default value if not specified is the vPC port identifier
            type: int
          peer1_members:
            description:
            - Member interfaces that are part of this port channel on first peer
            type: list
            elements: str
            required: true
          peer2_members:
            description:
            - Member interfaces that are part of this port channel on second peer
            type: list
            elements: str
            required: true
          pc_mode:
            description:
            - Port channel mode
            type: str
            choices: ['active', 'passive', 'on']
            default: active
          bpdu_guard:
            description:
            - Spanning-tree bpduguard
            type: str
            choices: ['true', 'false', 'no']
            default: 'true'
          port_type_fast:
            description:
            - Spanning-tree edge port behavior
            type: bool
            choices: [true, false]
            default: true
          mtu:
            description:
            - Interface MTU
            type: str
            choices: ['default', 'jumbo']
            default: jumbo
          peer1_allowed_vlans:
            description:
            - Vlans that are allowed on this interface of first peer.
              This option is applicable only for interfaces whose 'mode' is 'trunk'
            type: str
            choices: ['none', 'all', 'vlan-range(e.g., 1-2, 3-40)']
            default: none
          peer2_allowed_vlans:
            description:
            - Vlans that are allowed on this interface of second peer.
              This option is applicable only for interfaces whose 'mode' is 'trunk'
            type: str
            choices: ['none', 'all', 'vlan-range(e.g., 1-2, 3-40)']
            default: none
          peer1_access_vlan:
            description:
            - Vlan for the interface of first peer.
              This option is applicable only for interfaces whose 'mode' is 'access'
            type: str
            default: ''
          peer2_access_vlan:
            description:
            - Vlan for the interface of second peer.
              This option is applicable only for interfaces whose 'mode' is 'access'
            type: str
            default: ''
          peer1_cmds:
            description:
            - Commands to be included in the configuration under this interface of first peer
            type: list
            elements: str
            default: []
          peer2_cmds:
            description:
            - Commands to be included in the configuration under this interface of second peer
            type: list
            elements: str
            default: []
          peer1_description:
            description:
            - Description of the interface of first peer
            type: str
            default: ""
          peer2_description:
            description:
            - Description of the interface of second peer
            type: str
            default: ""
          admin_state:
            description:
            - Administrative state of the interface
            type: bool
            default: true
      profile_subint:
        description:
        - Though the key shown here is 'profile_subint' the actual key to be used in playbook
          is 'profile'. The key 'profile_subint' is used here to logically segregate the interface
          objects applicable for this profile
        - Object profile which must be included for sub-interface configurations.
        suboptions:
          mode:
            description:
            - Interface mode
            choices: ['subint']
            type: str
            required: true
          int_vrf:
            description:
            - Interface VRF name.
            type: str
            default: default
          ipv4_addr:
            description:
            - IPV4 address of the interface.
            type: str
            default: ""
          ipv4_mask_len:
            description:
            - IPV4 address mask length.
            - Minimum Value (8), Maximum Value (31)
            type: int
            default: 8
          ipv6_addr:
            description:
            - IPV6 address of the interface.
            type: str
            default: ""
          ipv6_mask_len:
            description:
            - IPV6 address mask length.
            - Minimum Value (1), Maximum Value (31)
            type: int
            default: 8
          mtu:
            description:
            - Interface MTU
            - Minimum Value (567), Maximum Value (9216)
            type: int
            default: 9216
          vlan:
            description:
            - DOT1Q vlan id for this interface
            - Minimum Value (2), Maximum Value (3967)
            type: int
            default: 0
          cmds:
            description:
            - Commands to be included in the configuration under this interface
            type: list
            elements: str
            default: []
          description:
            description:
            - Description of the interface
            type: str
            default: ""
          admin_state:
            description:
            - Administrative state of the interface
            type: bool
            default: true
      profile_lo:
        description:
        - Though the key shown here is 'profile_lo' the actual key to be used in playbook
          is 'profile'. The key 'profile_lo' is used here to logically segregate the interface
          objects applicable for this profile
        - Object profile which must be included for loopback interface configurations.
        suboptions:
          mode:
            choices: ['lo', 'fabric', 'mpls']
            description:
            - There are several modes for loopback interfaces.
            - Mode 'lo' is used to create, modify and delete non fabric loopback
              interfaces using policy 'int_loopback'.
            - Mode 'fabric' is used to modify loopbacks created when the fabric is first
              created using policy 'int_fabric_loopback_11_1'
            - Mode 'mpls' is used to modify loopbacks created when the fabric is first
              created using policy 'int_mpls_loopback'
            - Mode 'fabric' and 'mpls' interfaces can be modified but not created or deleted.
            type: str
            required: true
          int_vrf:
            description:
            - Interface VRF name.
            type: str
            default: default
          ipv4_addr:
            description:
            - IPv4 address of the interface.
            type: str
            default: ""
          secondary_ipv4_addr:
            description:
            - Secondary IP address of the nve interface loopback
            type: str
            default: ""
          ipv6_addr:
            description:
            - IPv6 address of the interface.
            type: str
            default: ""
          route_tag:
            description:
            - Route tag associated with the interface IP.
            type: str
            default: ""
          cmds:
            description:
            - Commands to be included in the configuration under this interface
            type: list
            elements: str
            default: []
          description:
            description:
            - Description of the interface
            type: str
            default: ""
          admin_state:
            description:
            - Administrative state of the interface
            type: bool
            default: true
      profile_eth:
        description:
        - Though the key shown here is 'profile_eth' the actual key to be used in playbook
          is 'profile'. The key 'profile_eth' is used here to logically segregate the interface
          objects applicable for this profile
        - Object profile which must be included for ethernet interface configurations.
        suboptions:
          mode:
            description:
            - Interface mode
            choices: ['trunk', 'access', 'routed', 'monitor', 'epl_routed']
            type: str
            required: true
          bpdu_guard:
            description:
            - Spanning-tree bpduguard
            type: str
            choices: ['true', 'false', 'no']
            default: 'true'
          port_type_fast:
            description:
            - Spanning-tree edge port behavior
            type: bool
            choices: [true, false]
            default: true
          mtu:
            description:
            - Interface MTU.
            - Can be specified either "default" or "jumbo" for access and
              trunk interface types. If not specified, it defaults to "jumbo"
            - Can be specified with any value within 576 and 9216 for routed interface
              types. If not specified, it defaults to 9216
            type: str
          allowed_vlans:
            description:
            - Vlans that are allowed on this interface.
              This option is applicable only for interfaces whose 'mode' is 'trunk'
            type: str
            choices: ['none', 'all', 'vlan-range(e.g., 1-2, 3-40)']
            default: none
          access_vlan:
            description:
            - Vlan for the interface. This option is applicable only for interfaces whose 'mode' is 'access'
            type: str
            default: ""
          speed:
            description:
            - Speed of the interface.
            type: str
            default: Auto
          int_vrf:
            description:
            - Interface VRF name. This object is applicable only if the 'mode' is 'routed'
            type: str
            default: default
          ipv4_addr:
            description:
            - IPV4 address of the interface. This object is applicable only if the 'mode' is
              'routed' or 'epl_routed'
            type: str
            default: ""
          ipv4_mask_len:
            description:
            - IPV4 address mask length. This object is applicable only if the 'mode' is 'routed' or
              'epl_routed'
            - Minimum Value (1), Maximum Value (31)
            type: int
            default: 8
          ipv6_addr:
            description:
            - IPV6 address of the interface. This object is applicable only if the 'mode' is 'epl_routed'
            type: str
            default: ""
          ipv6_mask_len:
            description:
            - IPV6 address mask length. This object is applicable only if the 'mode' is 'epl_routed'
            - Minimum Value (1), Maximum Value (31)
            type: int
            default: 8
          route_tag:
            description:
            - Route tag associated with the interface IP. This object is applicable only if the 'mode' is
              'routed' or 'epl_routed'
            type: str
            default: ""
          cmds:
            description:
            - Commands to be included in the configuration under this interface
            type: list
            elements: str
            default: []
          description:
            description:
            - Description of the interface
            type: str
            default: ""
          admin_state:
            description:
            - Administrative state of the interface
            type: bool
            default: true
      profile_svi:
        description:
        - Though the key shown here is 'profile_svi' the actual key to be used in playbook
          is 'profile'. The key 'profile_svi' is used here to logically segregate the interface
          objects applicable for this profile
        - Object profile which must be included for SVI interface configurations.
        suboptions:
          mode:
            description:
            - Interface mode.
            choices: ['vlan']
            type: str
            required: true
          int_vrf:
            description:
            - Interface VRF name.
            type: str
            default: "default"
          ipv4_addr:
            description:
            - IPV4 address of the interface.
            type: str
            default: ""
          ipv4_mask_len:
            description:
            - IPV4 address mask length. This parameter is required if 'ipv4_addr' is included.
            - Minimum Value (1), Maximum Value (31)
            type: int
          cmds:
            description:
            - Commands to be included in the configuration under this interface.
            type: list
            elements: str
            default: []
          description:
            description:
            - Description of the interface.
            type: str
            default: ""
          admin_state:
            description:
            - Administrative state of the interface.
            type: bool
            required: true
          route_tag:
            description:
            - Route tag associated with the interface IP.
            type: str
            default: ""
          mtu:
            description:
            - Interface MTU.
            type: int
            default: 9216
          disable_ip_redirects:
            description:
            - Flag to enable/disable IP redirects.
            type: bool
            default: false
          enable_hsrp:
            description:
            - Flag to enable/disable HSRP on the interface.
            type: bool
            default: false
          hsrp_vip:
            description:
            - Virtual IP address for HSRP. This parameter is required if "enable_hsrp" is True.
            type: str
            default: ""
          hsrp_group:
            description:
            - HSRP group. This parameter is required if "enable_hsrp" is True.
            type: str
            default: ""
          hsrp_priority:
            description:
            - HSRP priority.
            type: str
            default: ""
          hsrp_vmac:
            description:
            - HSRP virtual MAC.
            type: str
            default: ""
          dhcp_server_addr1:
            description:
            - DHCP relay server address.
            type: str
            default: ""
          vrf_dhcp1:
            description:
            - VRF to reach DHCP server. This parameter is required if "dhcp_server_addr1" is included.
            type: str
            default: ""
          dhcp_server_addr2:
            description:
            - DHCP relay server address.
            type: str
            default: ""
          vrf_dhcp2:
            description:
            - VRF to reach DHCP server. This parameter is required if "dhcp_server_addr2" is included.
            type: str
            default: ""
          dhcp_server_addr3:
            description:
            - DHCP relay server address.
            type: str
            default: ""
          vrf_dhcp3:
            description:
            - VRF to reach DHCP server. This parameter is required if "dhcp_server_addr3" is included.
            type: str
            default: ""
          adv_subnet_in_underlay:
            description:
            - Flag to enable/disable advertisements of subnets into underlay.
            type: bool
            default: false
          enable_netflow:
            description:
            - Flag to enable netflow.
            type: bool
            default: false
          netflow_monitor:
            description:
            - Name of netflow monitor. This parameter is required if "enable_netflow" is True.
            type: str
            default: ""
          hsrp_version:
            description:
            - HSRP protocol version.
            type: int
            default: 1
            choices: [1,2]
          preempt:
            description:
            - Flag to enable/disable overthrow of low priority active routers. This parameter is valid only if "enable_hsrp" is True.
            type: bool
            default: false
      profile_st_fex:
        description:
        - Though the key shown here is 'profile_st_fex' the actual key to be used in playbook
          is 'profile'. The key 'profile_st_fex' is used here to logically segregate the interface objects applicable for this profile
        - Object profile which must be included for straigth-through FEX interface configurations.
        suboptions:
          mode:
            description:
            - Interface mode
            choices: ['port_channel_st']
            type: str
            required: true
          mtu:
            description:
            - Interface MTU.
            type: str
            choices: ['default', 'jumbo']
            default: 'jumbo'
          members:
            description:
            - Member interfaces that are part of this FEX
            type: list
            elements: str
            required: true
          cmds:
            description:
            - Commands to be included in the configuration under this interface
            type: list
            elements: str
            default: []
          description:
            description:
            - Description of the FEX interface
            type: str
            default: ""
          po_description:
            description:
            - Description of the port-channel which is part of the FEX interface
            type: str
            default: ""
          admin_state:
            description:
            - Administrative state of the interface
            type: bool
            default: true
          enable_netflow:
            description:
            - Flag to enable netflow.
            type: bool
            default: false
          netflow_monitor:
            description:
            - Name of netflow monitor. This parameter is required if "enable_netflow" is True.
            type: str
            default: ""
      profile_aa_fex:
        description:
        - Though the key shown here is 'profile_aa_fex' the actual key to be used in playbook
          is 'profile'. The key 'profile_aa_fex' is used here to logically segregate the interface
          objects applicable for this profile
        - Object profile which must be included for active-active FEX inetrface configurations.
        suboptions:
          description:
            description:
            - Description of the FEX interface
            type: str
            default: ""
          mode:
            description:
            -  Interface mode
            choices: ['port_channel_aa']
            type: str
            required: true
          peer1_members:
            description:
            - Member interfaces that are part of this port channel on first peer
            type: list
            elements: str
            required: true
          peer2_members:
            description:
            - Member interfaces that are part of this port channel on second peer
            type: list
            elements: str
            required: true
          mtu:
            description:
            - Interface MTU
            type: str
            choices: ['default', 'jumbo']
            default: 'jumbo'
          peer1_cmds:
            description:
            - Commands to be included in the configuration under this interface of first peer
            type: list
            elements: str
            default: []
          peer2_cmds:
            description:
            - Commands to be included in the configuration under this interface of second peer
            type: list
            elements: str
            default: []
          peer1_po_description:
            description:
            - Description of the port-channel interface of first peer
            type: str
            default: ""
          peer2_po_description:
            description:
            - Description of the port-channel interface of second peer
            type: str
            default: ""
          admin_state:
            description:
            - Administrative state of the interface
            type: bool
            default: true
          enable_netflow:
            description:
            - Flag to enable netflow.
            type: bool
            default: false
          netflow_monitor:
            description:
            - Name of netflow monitor. This parameter is required if "enable_netflow" is True.
            type: str
            default: ""

"""

EXAMPLES = """

# States:
# This module supports the following states:
#
# Merged:
#   Interfaces defined in the playbook will be merged into the target fabric.
#
#   The interfaces listed in the playbook will be created if not already present on the DCNM
#   server. If the interface is already present and the configuration information included
#   in the playbook is either different or not present in DCNM, then the corresponding
#   information is added to the interface on DCNM. If an interface mentioned in playbook
#   is already present on DCNM and there is no difference in configuration, no operation
#   will be performed for such interface.
#
# Replaced:
#   Interfaces defined in the playbook will be replaced in the target fabric.
#
#   The state of the interfaces listed in the playbook will serve as source of truth for the
#   same interfaces present on the DCNM under the fabric mentioned. Additions and updations
#   will be done to bring the DCNM interfaces to the state listed in the playbook.
#   Note: Replace will only work on the interfaces mentioned in the playbook.
#
# Overridden:
#   Interfaces defined in the playbook will be overridden in the target fabric.
#
#   The state of the interfaces listed in the playbook will serve as source of truth for all
#   the interfaces under the fabric mentioned. Additions and deletions will be done to bring
#   the DCNM interfaces to the state listed in the playbook. All interfaces other than the
#   ones mentioned in the playbook will either be deleted or reset to default state.
#   Note: Override will work on the all the interfaces present in the DCNM Fabric.
#
# Deleted:
#   Interfaces defined in the playbook will be deleted in the target fabric.
#
#   Deletes the list of interfaces specified in the playbook.  If the playbook does not include
#   any switches or interface information, then all interfaces from all switches in the
#   fabric will either be deleted or put to default state. If configuuration includes information
#   pertaining to any particular switch, then interfaces belonging to that switch will either be
#   deleted or put to default. If configuration includes both interface and switch information,
#   then the specified interfaces will either be deleted or reset on all the seitches specified
#
# Query:
#   Returns the current DCNM state for the interfaces listed in the playbook.

# LOOPBACK INTERFACE

- name: Create loopback interfaces
  cisco.dcnm.dcnm_interface: &lo_merge
    fabric: mmudigon-fabric
    state: merged                         # only choose from [merged, replaced, deleted, overridden, query]
    config:
      - name: lo100                       # should be of the form lo<port-id>
        type: lo                          # choose from this list [pc, vpc, sub_int, lo, eth]
        switch:
          - "192.172.1.1"                 # provide the switch where to deploy the config
        deploy: true                      # choose from [true, false]
        profile:
          admin_state: true               # choose from [true, false]
          mode: lo                        # choose from [lo]
          int_vrf: ""                     # VRF name
          ipv4_addr: 192.169.10.1         # ipv4 address for the loopback interface
          ipv6_addr: fd01::0201           # ipV6 address for the loopback interface
          route_tag: ""                   # Routing Tag for the interface
          cmds:                           # Freeform config
            - no shutdown
          description: "loopback interface 100 configuration"

- name: Replace loopback interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: replaced                       # only choose from [merged, replaced, deleted, overridden. query]
    config:
      - name: lo100                       # should be of the form lo<port-id>
        type: lo                          # choose from this list [pc, vpc, sub_int, lo, eth]
        switch:
          - "192.172.1.1"                 # provide the switch where to deploy the config
        deploy: true                      ## choose from [true, false]
        profile:
          admin_state: false              ## choose from [true, false]
          mode: lo                        # choose from [lo]
          int_vrf: ""                     # VRF name
          ipv4_addr: 192.169.12.1         ## ipv4 address for the loopback interface
          ipv6_addr: fd01:0203            # ipV6 address for the loopback interface
          route_tag: "100"                ## Routing Tag for the interface
          cmds:                           # Freeform config
            - no shutdown
          description: "loopback interface 100 configuration - replaced"

## Loopback Interfaces Created During Fabric Creation
- name: Mange Fabric loopback interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: merged
    config:
      - name: lo1                           # This is usually lo0 or lo1 created during fabric creation
        type: lo
        switch:
          - "192.172.1.1"                   # provide the switch where to deploy the config
        deploy: true                        # choose from [true, false]
        profile:
          admin_state: false                # choose from [true, false]
          mode: fabric                      # This must be set to 'fabric' for fabric loopback interfaces
          secondary_ipv4_addr: 172.16.5.1   # secondary ipv4 address for loopback interface
          route_tag: "100"                  # Routing Tag for the interface
          cmds:                             # Freeform config
            - no shutdown
          description: "Fabric interface managed by Ansible"

# To delete or reset all interfaces on all switches in the fabric
- name: Delete loopback interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: deleted                        # only choose from [merged, replaced, deleted, overridden, query]

# To delete or reset all interfaces on a specific switch in the fabric
- name: Delete loopback interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: deleted                        # only choose from [merged, replaced, deleted, overridden, query]
    config:
      - switch:
          - "192.172.1.1"                 # provide the switch where to deploy the config

# To delete or reset a particular interface on all switches in the fabric
- name: Delete loopback interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: deleted                        # only choose from [merged, replaced, deleted, overridden, query]
    config:
      - name: lo100                       # should be of the form lo<port-id>

# To delete or reset a particular interface on a specific switch in the fabric
- name: Delete loopback interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: deleted                        # only choose from [merged, replaced, deleted, overridden, query]
    config:
      - name: lo100                       # should be of the form lo<port-id>
        switch:
          - "192.172.1.1"                 # provide the switch where to deploy the config

# To override with a particular interface configuration
- name: Override loopback interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: overridden                     # only choose from [merged, replaced, deleted, overridden, query]
    config:
      - name: lo103                       # should be of the form lo<port-id>
        type: lo                          # choose from this list [pc, vpc, sub_int, lo, eth]
        switch:
          - "192.172.1.1"                 # provide the switch where to deploy the config
        deploy: true                      # choose from [true, false]
        profile:
          admin_state: true               # choose from [true, false]
          mode: lo                        # choose from [lo]
          int_vrf: ""                     # VRF name
          ipv4_addr: 192.169.14.1         # ipv4 address for the loopback interface
          ipv6_addr: fd01::0205           # ipV6 address for the loopback interface
          route_tag: ""                   # Routing Tag for the interface
          cmds:                           # Freeform config
            - no shutdown
          description: "loopback interface 103 configuration - overridden"

# To override all interface on all switches in the fabric
- name: Override loopback interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: overridden                     # only choose from [merged, replaced, deleted, overridden, query]

# To override all interfaces on a particular switche in the fabric
- name: Override loopback interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: overridden                     # only choose from [merged, replaced, deleted, overridden, query]
    config:
      - switch:
          - "192.172.1.1"                 # provide the switch where to deploy the config

# PORTCHANNEL INTERFACE

- name: Create port channel interfaces
  cisco.dcnm.dcnm_interface: &pc_merge
    fabric: mmudigon-fabric
    state: merged                         # only choose from [merged, replaced, deleted, overridden, query]
    config:
      - name: po300                       # should be of the form po<port-id>
        type: pc                          # choose from this list [pc, vpc, sub_int, lo, eth]
        switch:
          - "192.172.1.1"                 # provide the switch information where the config is to be deployed
        deploy: true                      # choose from [true, false]
        profile:
          admin_state: true               # choose from [true, false]
          mode: trunk                     # choose from [trunk, access, l3, monitor]
          members:                        # member interfaces
            - e1/10
          pc_mode: 'on'                   # choose from ['on', 'active', 'passive']
          bpdu_guard: true                # choose from [true, false, no]
          port_type_fast: true            # choose from [true, false]
          mtu: jumbo                      # choose from [default, jumbo]
          allowed_vlans: none             # choose from [none, all, vlan range]
          cmds:                           # Freeform config
            - no shutdown
          description: "port channel acting as trunk"

      - name: po301                       # should be of the form po<port-id>
        type: pc                          # choose from this list [pc, vpc, sub_int, lo, eth]
        switch:
          - "192.172.1.1"                 # provide the switch information where the config is to be deployed
        deploy: true                      # choose from [true, false]
        profile:
          admin_state: false              # choose from [true, false]
          mode: access                    # choose from [trunk, access, l3, monitor]
          members:                        # member interfaces
            - e1/11
          pc_mode: 'on'                   # choose from ['on', 'active', 'passive']
          bpdu_guard: true                # choose from [true, false, no]
          port_type_fast: true            # choose from [true, false]
          mtu: default                    # choose from [default, jumbo]
          access_vlan: 301                #
          cmds:                           # Freeform config
            - no shutdown
          description: "port channel acting as access"

- name: Replace port channel interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: replaced                       # only choose from [merged, replaced, deleted, overridden, query]
    config:
      - name: po300                       # should be of the form po<port-id>
        type: pc                          # choose from this list [pc, vpc, sub_int, lo, eth]
        switch:
          - "192.172.1.1"                 # provide the switch information where the config is to be deployed
        deploy: true                      # choose from [true, false]
        profile:
          admin_state: false              ## choose from [true, false]
          mode: trunk                     # choose from [trunk, access, l3, monitor]
          members:                        # member interfaces
            - e1/10
          pc_mode: 'active'               ## choose from ['on', 'active', 'passive']
          bpdu_guard: false               ## choose from [true, false, no]
          port_type_fast: false           ## choose from [true, false]
          mtu: default                    ## choose from [default, jumbo]
          allowed_vlans: all              ## choose from [none, all, vlan range]
          cmds:                           # Freeform config
            - no shutdown
          description: "port channel acting as trunk - replace"

# To delete or reset a particular interface on a specific switch in the fabric
- name: Delete port channel interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: deleted                        # only choose from [merged, replaced, deleted, overridden, query]
    config:
      - name: po300                       # should be of the form po<port-id>
        switch:
          - "192.172.1.1"                 # provide the switch information where the config is to be deployed

# To delete or reset all interfaces on all switches in the fabric
- name: Delete port channel interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: deleted                        # only choose from [merged, replaced, deleted, overridden, query]

# To delete or reset a particular interface on all switches in the fabric
- name: Delete port-channel interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: deleted                        # only choose from [merged, replaced, deleted, overridden, query]
    config:
      - name: po300                       # should be of the form po<port-id>

# To delete or reset all interfaces on a specific switch in the fabric
- name: Delete port channel interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: deleted                        # only choose from [merged, replaced, deleted, overridden, query]
    config:
      - switch:
          - "192.172.1.1"                 # provide the switch information where the config is to be deployed

- name: Override port channel interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: overridden                     # only choose from [merged, replaced, deleted, overridden, query]
    config:
      - name: po320                       # should be of the form po<port-id>
        type: pc                          # choose from this list [pc, vpc, sub_int, lo, eth]
        switch:
          - "192.172.1.1"                 # provide the switch information where the config is to be deployed
        deploy: true                      # choose from [true, false]
        profile:
          admin_state: true               # choose from [true, false]
          mode: trunk                     # choose from [trunk, access, l3, monitor]
          members:                        # member interfaces
            - e1/10
          pc_mode: 'on'                   # choose from ['on', 'active', 'passive']
          bpdu_guard: true                # choose from [true, false, no]
          port_type_fast: true            # choose from [true, false]
          mtu: jumbo                      # choose from [default, jumbo]
          allowed_vlans: none             # choose from [none, all, vlan range]
          cmds:                           # Freeform config
            - no shutdown
          description: "port channel acting as trunk"

# SUB-INTERFACE

- name: Create sub-interfaces
  cisco.dcnm.dcnm_interface: &sub_merge
    fabric: mmudigon-fabric
    state: merged                         # only choose from [merged, replaced, deleted, overridden, query]
    config:
      - name: eth1/1.1                    # should be of the form eth<port-num>.<port-id>
        type: sub_int                     # choose from this list [pc, vpc, sub_int, lo, eth]
        switch:
          - "192.172.1.1"                 # provide the switch information where the config is to be deployed
        deploy: true                      # choose from [true, false]
        profile:
          admin_state: true               # choose from [true, false]
          mode: subint                    # choose from [subint]
          vlan: 100                       # vlan ID [min:2, max:3967]
          int_vrf: ""                     # VRF name
          ipv4_addr: 192.168.30.1         # ipv4 address for the sub-interface
          ipv4_mask_len: 24               # choose between [min:8, max:31]
          ipv6_addr: fd01::0401           # ipV6 address for the sub-interface
          ipv6_mask_len: 64               # choose between [min:64, max:127]
          mtu: 9216                       # choose between [min:576, max:9216]
          cmds:                           # Freeform config
            - no shutdown
          description: "sub interface eth1/1.1 configuration"

- name: Replace sub-interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: replaced                       # only choose from [merged, replaced, deleted, overridden, query]
    config:
      - name: eth1/1.1                    # should be of the form eth<port-num>.<port-id>
        type: sub_int                     # choose from this list [pc, vpc, sub_int, lo, eth]
        switch:
          - "192.172.1.1"                 # provide the switch information where the config is to be deployed
        deploy: true                      # choose from [true, false]
        profile:
          admin_state: false              ## choose from [true, false]
          mode: subint                    # choose from [subint]
          vlan: 200                       ## vlan ID [min:2, max:3967]
          int_vrf: ""                     # VRF name
          ipv4_addr: 192.168.32.1         ## ipv4 address for the sub-interface
          ipv4_mask_len: 20               # choose between [min:8, max:31]
          ipv6_addr: fd01::0403           # ipV6 address for the sub-interface
          ipv6_mask_len: 64               # choose between [min:64, max:127]
          mtu: 1500                       ## choose between [min:576, max:9216]
          cmds:                           # Freeform config
            - no shutdown
          description: "sub interface eth1/1.1 configuration - replace"

# To delete or reset all interfaces on all switches in the fabric
- name: Delete sub-interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: deleted                        # only choose from [merged, replaced, deleted, overridden, query]

# To delete or reset a particular interface on all switches in the fabric
- name: Delete port-channel interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: deleted                        # only choose from [merged, replaced, deleted, overridden, query]
    config:
      - name: eth1/1.1                    # should be of the form eth<port-num>.<port-id>

- name: Override sub-interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: overridden                     # only choose from [merged, replaced, deleted, overridden, query]
    config:
      - name: eth1/1.3                    # should be of the form eth<port-num>.<port-id>
        type: sub_int                     # choose from this list [pc, vpc, sub_int, lo, eth]
        switch:
          - "192.172.1.1"                 # provide the switch information where the config is to be deployed
        deploy: true                      # choose from [true, false]
        profile:
          admin_state: true               # choose from [true, false]
          mode: subint                    # choose from [subint]
          vlan: 103                       # vlan ID [min:2, max:3967]
          int_vrf: ""                     # VRF name
          ipv4_addr: 192.168.35.1         # ipv4 address for the sub-interface
          ipv4_mask_len: 24               # choose between [min:8, max:31]
          ipv6_addr: fd01::0405           # ipV6 address for the sub-interface
          ipv6_mask_len: 64               # choose between [min:64, max:127]
          mtu: 9216                       # choose between [min:576, max:9216]
          cmds:                           # Freeform config
            - no shutdown
          description: "sub interface eth1/1.3 configuration - override"

# VPC INTERFACE

- name: Create vPC interfaces
  cisco.dcnm.dcnm_interface: &vpc_merge
    fabric: mmudigon-fabric
    state: merged                         # only choose from [merged, replaced, deleted, overridden, query]
    config:
      - name: vpc750                      # should be of the form vpc<port-id>
        type: vpc                         # choose from this list [pc, vpc, sub_int, lo, eth]
        switch:                           # provide switches of vPC pair
          - ["192.172.1.1",
             "192.172.1.2"]
        deploy: true                      # choose from [true, false]
        profile:
          admin_state: true               # choose from [true, false]
          mode: trunk                     # choose from [trunk, access]
          peer1_pcid: 100                 # choose between [Min:1, Max:4096], if not given, will be VPC port-id
          peer2_pcid: 100                 # choose between [Min:1, Max:4096], if not given, will be VPC port-id
          peer1_members:                  # member interfaces on peer 1
            - e1/24
          peer2_members:                  # member interfaces on peer 2
            - e1/24
          pc_mode: 'active'               # choose from ['on', 'active', 'passive']
          bpdu_guard: true                # choose from [true, false, 'no']
          port_type_fast: true            # choose from [true, false]
          mtu: jumbo                      # choose from [default, jumbo]
          peer1_allowed_vlans: none       # choose from [none, all, vlan range]
          peer2_allowed_vlans: none       # choose from [none, all, vlan range]
          peer1_description: "VPC acting as trunk peer1"
          peer2_description: "VPC acting as trunk peer2"


- name: Replace vPC interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: replaced                         # only choose from [merged, replaced, deleted, overridden, query]
    config:
      - name: vpc750                      # should be of the form vpc<port-id>
        type: vpc                         # choose from this list [pc, vpc, sub_int, lo, eth]
        switch:                           # provide switches of vPC pair
          - ["192.172.1.1",
             "192.172.1.2"]
        deploy: true                      # choose from [true, false]
        profile:
          admin_state: false              ## choose from [true, false]
          mode: trunk                     # choose from [trunk, access]
          peer1_pcid: 100                 # choose between [Min:1, Max:4096], if not given, will be VPC port-id
          peer2_pcid: 100                 # choose between [Min:1, Max:4096], if not given, will be VPC port-id
          peer1_members:                  ## member interfaces on peer 1
            - e1/26
          peer2_members:                  ## member interfaces on peer 2
            - e1/26
          pc_mode: 'active'               ## choose from ['on', 'active', 'passive']
          bpdu_guard: false               ## choose from [true, false, 'no']
          port_type_fast: false           ## choose from [true, false]
          mtu: default                    ## choose from [default, jumbo]
          peer1_allowed_vlans: all        ## choose from [none, all, vlan range]
          peer2_allowed_vlans: all        ## choose from [none, all, vlan range]
          peer1_description: "VPC acting as trunk peer1 - modified"
          peer2_description: "VPC acting as trunk peer2 - modified"
          peer1_cmds:                     # Freeform config
              - no shutdown
          peer2_cmds:                     # Freeform config
              - no shutdown

# To delete or reset a particular interface on a specific switch in the fabric
- name: Delete vPC interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: deleted                         # only choose from [merged, replaced, deleted, overridden, query]
    config:
      - name: vpc750                      # should be of the form vpc<port-id>
        switch:                           # provide switches of vPC pair
          - ["192.172.1.1",
             "192.172.1.2"]

- name: Override vPC interfaces
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: overridden                         # only choose from [merged, replaced, deleted, overridden, query]
    config:
      - name: vpc752                      # should be of the form vpc<port-id>
        type: vpc                         # choose from this list [pc, vpc, sub_int, lo, eth]
        switch:                           # provide switches of vPC pair
          - ["192.172.1.1",
             "192.172.1.2"]
        deploy: true                      # choose from [true, false]
        profile:
          admin_state: true               # choose from [true, false]
          mode: trunk                     # choose from [trunk, access]
          peer1_pcid: 752                 # choose between [Min:1, Max:4096], if not given, will be VPC port-id
          #peer2_pcid: 1                  # choose between [Min:1, Max:4096], if not given, will be VPC port-id
          peer1_members:                  # member interfaces on peer 1
            - e1/26
          peer2_members:                  # member interfaces on peer 2
            - e1/27
          pc_mode: 'on'                   # choose from ['on', 'active', 'passive']
          bpdu_guard: true                # choose from [true, false, no]
          port_type_fast: true            # choose from [true, false]
          mtu: jumbo                      # choose from [default, jumbo]
          peer1_allowed_vlans: none       # choose from [none, all, vlan range]
          peer2_allowed_vlans: none       # choose from [none, all, vlan range]
          peer1_description: "VPC acting as trunk peer1"
          peer2_description: "VPC acting as trunk peer2"
          peer1_cmds:                     # Freeform config
              - no shutdown
              - no shutdown
          peer2_cmds:                     # Freeform config
              - no shutdown
              - no shutdown

# SVI INTERFACES

- name: Create SVI interfaces including optional parameters
  cisco.dcnm.dcnm_interface:
    check_deploy: true
    fabric: "{{ ansible_svi_fabric }}"
    state: merged                                   # only choose form [merged, replaced, deleted, overridden, query]
    config:
      - name: vlan1001                              # should be of the form vlan<vlan-id>
        type: svi                                   # choose from this list [pc, vpc, sub_int, lo, eth, svi]
        switch:
          - "{{ ansible_switch1 }}"                 # provide the switch information where the config is to be deployed
        deploy: true                                # choose from [true, false]
        profile:
          int_vrf: blue                             # optional, Interface VRF name, default is "default"
          ipv4_addr: 192.168.2.1                    # optional, Interfae IP, default is ""
          ipv4_mask_len: 24                         # optional, IP mask length, default is ""
          mtu: 9216                                 # optional, MTU default is ""
          route_tag: 1001                           # optional, Routing TAG, default is ""
          disable_ip_redirects: true                # optional, flag to enable/disable IP redirects, default is "false"
          cmds:                                     # Freeform config
            - no shutdown
          admin_state: true                         # Flag to enable/disable Vlan interaface
          enable_hsrp: true                         # optional, flag to enable/disable HSRP on the interface, default is "false"
          hsrp_vip: 192.168.2.100                   # optional, Virtual IP address for HSRP, default is ""
          hsrp_group: 10                            # optional, HSRP group, default is ""
          hsrp_priority: 5                          # optional, HSRP priority, default is ""
          hsrp_vmac: 0000.0101.ac0a                 # optional, HSRP virtual MAC, default is ""
          dhcp_server_addr1: 192.200.1.1            # optional, DHCP relay server address, default is ""
          vrf_dhcp1: blue                           # optional, VRF to reach DHCP server. default is ""
          dhcp_server_addr2: 192.200.1.2            # optional, DHCP relay server address, default is ""
          vrf_dhcp2: blue                           # optional, VRF to reach DHCP server. default is ""
          dhcp_server_addr3: 192.200.1.3            # optional, DHCP relay server address, default is ""
          vrf_dhcp3: blue                           # optional, VRF to reach DHCP server. default is ""
          adv_subnet_in_underlay: true              # optional, flag to enable/disable advertisements of subnets into underlay, default is "false"
          enable_netflow: false                     # optional, flag to enable netflow, default is "false"
          netflow_monitor: svi1001                  # optional, name of netflow monitor, default is ""
          hsrp_version: 1                           # optional, HSRP protocol version, default is 1
          preempt: true                             # optional, flag to enable/disable overthrow of low priority active routers, optional is "false"
          mode: vlan                                # choose from [vlan, vlan_admin_state], default is "vlan"
          description: Switched vlan interface 1001 # optional, Interface description, default is ""

- name: Replace SVI interface
  cisco.dcnm.dcnm_interface:
    check_deploy: true
    fabric: "{{ ansible_svi_fabric }}"
    state: replaced                                       # only choose form [merged, replaced, deleted, overridden, query]
    config:
      - name: vlan1001                                    # should be of the form vlan<vlan-id>
        type: svi                                         # choose from this list [pc, vpc, sub_int, lo, eth, svi]
        switch:
          - "{{ ansible_switch1 }}"                       # provide the switch information where the config is to be deployed
        deploy: true                                      # choose from [true, false]
        profile:
          int_vrf: red                                    # optional, Interface VRF name, default is "default"
          ipv4_addr: 192.169.2.1                          # optional, Interfae IP, default is ""
          ipv4_mask_len: 20                               # optional, IP mask length, default is ""
          mtu: 9210                                       # optional, MTU default is ""
          route_tag: 1002                                 # optional, Routing TAG, default is ""
          disable_ip_redirects: false                     # optional, flag to enable/disable IP redirects, default is "false"
          cmds:                                           # Freeform config
            - no shutdown
          admin_state: false                              # Flag to enable/disable Vlan interaface
          enable_hsrp: true                               # optional, flag to enable/disable HSRP on the interface, default is "false"
          hsrp_vip: 192.169.2.100                         # optional, Virtual IP address for HSRP, default is ""
          hsrp_group: 11                                  # optional, HSRP group, default is ""
          hsrp_priority: 5                                # optional, HSRP priority, default is ""
          hsrp_vmac: 0000.0102.ac0a                       # optional, HSRP virtual MAC, default is ""
          dhcp_server_addr1: 193.200.1.1                  # optional, DHCP relay server address, default is ""
          vrf_dhcp1: green                                # optional, VRF to reach DHCP server. default is ""
          dhcp_server_addr2: 193.200.1.2                  # optional, DHCP relay server address, default is ""
          vrf_dhcp2: green                                # optional, VRF to reach DHCP server. default is ""
          dhcp_server_addr3: 193.200.1.3                  # optional, DHCP relay server address, default is ""
          vrf_dhcp3: green                                # optional, VRF to reach DHCP server. default is ""
          adv_subnet_in_underlay: false                   # optional, flag to enable/disable advertisements of subnets into underlay, default is "false"
          enable_netflow: false                           # optional, flag to enable netflow, default is "false"
          netflow_monitor: svi1002                        # optional, name of netflow monitor, default is ""
          hsrp_version: 2                                 # optional, HSRP protocol version, default is 1
          preempt: false                                  # optional, flag to enable/disable overthrow of low priority active routers, optional is "false"
          mode: vlan                                      # choose from [vlan, vlan_admin_state], default is "vlan"
          description: Switched vlan interface 1001 - Rep # optional, Interface description, default is ""

- name: Delete SVI interfaces
  cisco.dcnm.dcnm_interface:
    check_deploy: True
    fabric: "{{ ansible_svi_fabric }}"
    state: deleted                        # only choose form [merged, replaced, deleted, overridden, query]
    config:
      - name: vlan1000                    # should be of the form vlan<vlan-id>
        type: svi                         # choose from this list [pc, vpc, sub_int, lo, eth, svi]
        switch:
          - "{{ ansible_switch1 }}"       # provide the switch where to deploy the config

      - name: vlan1001                    # should be of the form vlan<vlan-id>
        type: svi                         # choose from this list [pc, vpc, sub_int, lo, eth, svi]
        switch:
          - "{{ ansible_switch1 }}"       # provide the switch where to deploy the config

- name: Override SVI interface
  cisco.dcnm.dcnm_interface:
    check_deploy: true
    fabric: "{{ ansible_svi_fabric }}"
    state: overridden                                     # only choose form [merged, replaced, deleted, overridden, query]
    config:
      - name: vlan1002                                    # should be of the form vlan<vlan-id>
        type: svi                                         # choose from this list [pc, vpc, sub_int, lo, eth, svi]
        switch:
          - "{{ ansible_switch1 }}"                       # provide the switch information where the config is to be deployed
        deploy: true                                      # choose from [true, false]
        profile:
          admin_state: true                               # Flag to enable/disable Vlan interaface
          mode: vlan                                      # choose from [vlan, vlan_admin_state], default is "vlan"

# AA FEX INTERFACES

- name: Create AA FEX interfaces including optional parameters
  cisco.dcnm.dcnm_interface:
    check_deploy: True
    fabric: "{{ ansible_svi_fabric }}"
    state: merged                                   # only choose form [merged, replaced, deleted, overridden, query]
    config:
      - name: vpc151                                # should be of the form vpc<id>
        type: aa_fex                                # choose from this list [pc, vpc, sub_int, lo, eth, svi, st_fex, aa_fex]
        switch:
          - "{{ ansible_switch1 }}"                 # provide the switch information where the config is to be deployed
        deploy: true                                # choose from [true, false]
        profile:
          description: "AA FEX interface 151"       # optional, description of FEX interface, default is ""
          peer1_members:                            # optional, member interfaces, default is []
            - e1/10
          peer2_members:                            # optional, member interfaces, default is []
            - e1/10
          mtu: "jumbo"                              # optional, MTU for the interface, default is "jumbo"
          peer1_po_description: "PC 151 for AA FEX" # optional, description of PC interface, default is ""
          peer2_po_description: "PC 151 for AA FEX" # optional, description of PC interface, default is ""
          peer1_cmds:                               # optional, freeform config, default is []
            - no shutdown
          peer2_cmds:                               # optional, freeform config, default is []
            - no shutdown
          admin_state: true                         # Flag to enable/disable FEX interface.
          enable_netflow: false                     # optional, flag to enable netflow, default is false
          mode: port_channel_aa                     # choose from [port_channel_aa], default is "port_channel_aa"

- name: Replace AA FEX interface
  cisco.dcnm.dcnm_interface:
    check_deploy: true
    fabric: "{{ ansible_svi_fabric }}"
    state: replaced                                 # only choose form [merged, replaced, deleted, overridden, query]
    config:
      - name: vpc150                                # should be of the form vpc<id>
        type: aa_fex                                # choose from this list [pc, vpc, sub_int, lo, eth, svi, st_fex, aa_fex]
        switch:
          - "{{ ansible_switch1 }}"                 # provide the switch information where the config is to be deployed
        deploy: true                                # choose from [true, false]
        profile:
          peer1_members:                            # optional, member interfaces, default is []
            - e1/11
          peer2_members:                            # optional, member interfaces, default is []
            - e1/11
          mtu: "default"                            # optional, MTU for the interface, default is "jumbo"
          peer1_po_description: "PC 150 for AA FEX - REP" # optional, description of PC interface, default is ""
          peer2_po_description: "PC 150 for AA FEX - REP" # optional, description of PC interface, default is ""
          admin_state: false                        # Flag to enable/disable FEX interface.
          enable_netflow: false                     # optional, flag to enable netflow, default is false
          mode: port_channel_aa                     # choose from [port_channel_aa], default is "port_channel_aa"

          peer1_cmds:                               # optional, freeform config, default is []
            - ip arp inspection trust
          peer2_cmds:                               # optional, freeform config, default is []
            - ip arp inspection trust

- name: Delete AA FEX interfaces
  cisco.dcnm.dcnm_interface:
    check_deploy: True
    fabric: "{{ ansible_svi_fabric }}"
    state: deleted                        # only choose form [merged, replaced, deleted, overridden, query]
    config:
      - name: vpc151                      # should be of the form vpc<id>
        switch:
          - "{{ ansible_switch1 }}"       # provide the switch where to deploy the config


- name: Overide AA FEX interface with a new one
  cisco.dcnm.dcnm_interface:
    check_deploy: true
    fabric: "{{ ansible_svi_fabric }}"
    state: overridden                               # only choose form [merged, replaced, deleted, overridden, query]
    config:
      - name: vpc151                                # should be of the form vpc<id>
        type: aa_fex                                # choose from this list [pc, vpc, sub_int, lo, eth, svi, st_fex, aa_fex]
        switch:
          - "{{ ansible_switch1 }}"                 # provide the switch information where the config is to be deployed
        deploy: true                                # choose from [true, false]
        profile:
          description: "AA FEX interface 151"       # optional, description of FEX interface, default is ""
          peer1_members:                            # optional, member interfaces, default is []
            - e1/10
          peer2_members:                            # optional, member interfaces, default is []
            - e1/10
          mtu: "jumbo"                              # optional, MTU for the interface, default is "jumbo"
          peer1_po_description: "PC 151 for AA FEX" # optional, description of PC interface, default is ""
          peer2_po_description: "PC 151 for AA FEX" # optional, description of PC interface, default is ""
          peer1_cmds:                               # optional, freeform config, default is []
            - no shutdown
          peer2_cmds:                               # optional, freeform config, default is []
            - no shutdown
          admin_state: true                         # Flag to enable/disable FEX interface.
          enable_netflow: false                     # optional, flag to enable netflow, default is false
          mode: port_channel_aa                     # choose from [port_channel_aa], default is "port_channel_aa"

# STRAIGHT-THROUGH FEX INTERFACES

- name: Create ST FEX interfaces including optional parameters
  cisco.dcnm.dcnm_interface:
    check_deploy: true
    fabric: "{{ ansible_svi_fabric }}"
    state: merged                                   # only choose form [merged, replaced, deleted, overridden, query]
    config:
      - name: po151                                 # should be of the form po<po-id>
        type: st_fex                                # choose from this list [pc, vpc, sub_int, lo, eth, svi, st_fex, aa_fex]
        switch:
          - "{{ ansible_switch1 }}"                 # provide the switch information where the config is to be deployed
        deploy: true                                # choose from [true, false]
        profile:
          description: "ST FEX interface 151"       # optional, description of FEX interface, default is ""
          members:                                  # optional, member interfaces, default is []
            - e1/10
          mtu: "jumbo"                              # optional, MTU for the interface, default is "jumbo"
          po_description: "PC 151 for ST FEX"       # optional, description of PC interface, default is ""
          cmds:                                     # optional, freeform config, default is []
            - no shutdown
          admin_state: true                         # Flag to enable/disable FEX interface.
          enable_netflow: false                     # optional, flag to enable netflow, default is false
          mode: port_channel_st                     # choose from [port_channel_st], default is "port_channel_st"

- name: Replace ST FEX interface
  cisco.dcnm.dcnm_interface:
    check_deploy: true
    fabric: "{{ ansible_svi_fabric }}"
    state: replaced                                 # only choose form [merged, replaced, deleted, overridden, query]
    config:
      - name: po160                                 # should be of the form po<po-id>
        type: st_fex                                # choose from this list [pc, vpc, sub_int, lo, eth, svi, st_fex, aa_fex]
        switch:
          - "{{ ansible_switch1 }}"                 # provide the switch information where the config is to be deployed
          - "{{ ansible_switch2 }}"                 # provide the switch information where the config is to be deployed
        deploy: true                                # choose from [true, false]
        profile:
          members:                                  # optional, member interfaces, default is []
            - e1/11
          mtu: "default"                            # optional, MTU for the interface, default is "jumbo"
          po_description: "PC 160 for ST FEX - REP" # optional, description of PC interface, default is ""
          cmds:                                     # optional, freeform config, default is []
            - ip arp inspection trust
          admin_state: false                        # Flag to enable/disable FEX interface.
          enable_netflow: false                     # optional, flag to enable netflow, default is false
          mode: port_channel_st                     # choose from [port_channel_st], default is "port_channel_st"

- name: Delete ST FEX interfaces
  cisco.dcnm.dcnm_interface:
    check_deploy: True
    fabric: "{{ ansible_svi_fabric }}"
    state: deleted                        # only choose form [merged, replaced, deleted, overridden, query]
    config:
      - name: po159                       # should be of the form po<po-id>
        switch:
          - "{{ ansible_switch1 }}"       # provide the switch where to deploy the config
          - "{{ ansible_switch2 }}"       # provide the switch where to deploy the config

- name: Overide ST FEX interface with a new one
  cisco.dcnm.dcnm_interface:
    check_deploy: true
    fabric: "{{ ansible_svi_fabric }}"
    state: overridden                               # only choose form [merged, replaced, deleted, overridden, query]
    config:
      - name: po151                                 # should be of the form po<po-id>
        type: st_fex                                # choose from this list [pc, vpc, sub_int, lo, eth, svi, st_fex, aa_fex]
        switch:
          - "{{ ansible_switch1 }}"                 # provide the switch information where the config is to be deployed
        deploy: true                                # choose from [true, false]
        profile:
          description: "ST FEX interface 151"       # optional, description of FEX interface, default is ""
          members:                                  # optional, member interfaces, default is []
            - e1/10
          mtu: "jumbo"                              # optional, MTU for the interface, default is "jumbo"
          po_description: "PC 151 for ST FEX"       # optional, description of PC interface, default is ""
          cmds:                                     # optional, freeform config, default is []
            - no shutdown
          admin_state: true                         # Flag to enable/disable FEX interface.
          enable_netflow: false                     # optional, flag to enable netflow, default is false
          mode: port_channel_st                     # choose from [port_channel_st], default is "port_channel_st"

# QUERY

- name: Query interface details
  cisco.dcnm.dcnm_interface:
    fabric: mmudigon-fabric
    state: query            # only choose from [merged, replaced, deleted, overridden, query]
    config:
      - switch:
          - "192.172.1.1"
      - name: po350
        switch:
          - "192.172.1.1"
      - name: lo450
        switch:
          - "192.172.1.1"
      - name: eth1/1
        switch:
          - "192.172.1.1"
      - name: eth1/15.2
        switch:
          - "192.172.1.1"
      - name: vpc750
        switch:
          - "192.172.1.1"

"""

import time
import json
import re
import copy
import sys

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
    get_fabric_inventory_details,
    dcnm_get_ip_addr_info,
    validate_list_of_dicts,
    get_ip_sn_dict,
    dcnm_version_supported,
)


class DcnmIntf:

    dcnm_intf_paths = {
        11: {
            "VPC_SNO": "/rest/interface/vpcpair_serial_number?serial_number={}",
            "IF_WITH_SNO_IFNAME": "/rest/interface?serialNumber={}&ifName={}",
            "IF_DETAIL_WITH_SNO": "/rest/interface/detail?serialNumber={}",
            "GLOBAL_IF": "/rest/globalInterface",
            "GLOBAL_IF_DEPLOY": "/rest/globalInterface/deploy",
            "INTERFACE": "/rest/interface",
            "IF_MARK_DELETE": "/rest/interface/markdelete",
            "FABRIC_ACCESS_MODE": "/rest/control/fabrics/{}/accessmode",
        },
        12: {
            "VPC_SNO": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface/vpcpair_serial_number?serial_number={}",
            "IF_WITH_SNO_IFNAME": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface?serialNumber={}&ifName={}",
            "IF_DETAIL_WITH_SNO": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface/detail?serialNumber={}",
            "GLOBAL_IF": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/globalInterface",
            "GLOBAL_IF_DEPLOY": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/globalInterface/deploy",
            "INTERFACE": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface",
            "IF_MARK_DELETE": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface/markdelete",
            "FABRIC_ACCESS_MODE": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{}/accessmode",
        },
    }

    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.fabric = module.params["fabric"]
        self.config = copy.deepcopy(module.params.get("config"))
        self.pb_input = []
        self.check_mode = False
        self.intf_info = []
        self.want = []
        self.have = []
        self.have_all = []
        self.have_all_list = []
        self.diff_create = []
        self.diff_replace = []
        self.diff_delete = [[], [], [], [], [], [], [], []]
        self.diff_delete_deploy = [[], [], [], [], [], [], [], []]
        self.diff_deploy = []
        self.diff_query = []
        self.log_verbosity = 0
        self.fd = None
        self.vpc_ip_sn = {}
        self.ip_sn = {}
        self.hn_sn = {}
        self.monitoring = []

        self.changed_dict = [
            {
                "merged": [],
                "deleted": [],
                "replaced": [],
                "overridden": [],
                "deploy": [],
                "query": [],
                "debugs": [],
                "delete_deploy": [],
                "skipped": [],
                "deferred": [],
            }
        ]

        self.dcnm_version = dcnm_version_supported(self.module)

        self.inventory_data = {}

        self.paths = self.dcnm_intf_paths[self.dcnm_version]

        self.dcnm_intf_facts = {
            "fabric": module.params["fabric"],
            "config": module.params["config"],
        }

        self.result = dict(changed=False, diff=[], response=[])

        # New Interfaces
        # To map keys from self.have to keys from config
        self.keymap = {
            "DISABLE_IP_REDIRECTS": "disable_ip_redirects",
            "ENABLE_HSRP": "enable_hsrp",
            "HSRP_VIP": "hsrp_vip",
            "HSRP_GROUP": "hsrp_group",
            "PREEMPT": "preempt",
            "HSRP_VERSION": "hsrp_version",
            "HSRP_PRIORITY": "hsrp_priority",
            "MAC": "hsrp_vmac",
            "dhcpServerAddr1": "dhcp_server_addr1",
            "dhcpServerAddr2": "dhcp_server_addr2",
            "dhcpServerAddr3": "dhcp_server_addr3",
            "vrfDhcp1": "vrf_dhcp1",
            "vrfDhcp2": "vrf_dhcp2",
            "vrfDhcp3": "vrf_dhcp3",
            "advSubnetInUnderlay": "adv_subnet_in_unbderlay",
            "ENABLE_NETFLOW": "enable_netflow",
            "NETFLOW_MONITOR": "netflow_monitor",
            "policy": "policy",
            "ifName": "ifname",
            "serialNumber": "sno",
            "fabricName": "fabric",
            "IP": "ipv4_addr",
            "SECONDARY_IP": "secondary_ipv4_addr",
            "INTF_VRF": "int_vrf",
            "V6IP": "ipv6_addr",
            "IPv6": "ipv6_addr",
            "PREFIX": "ipv4_mask_len",
            "IPv6_PREFIX": "ipv6_mask_len",
            "ROUTING_TAG": "route_tag",
            "ROUTE_MAP_TAG": "route_tag",
            "CONF": "cmds",
            "DESC": "description",
            "VLAN": "vlan",
            "ADMIN_STATE": "admin_state",
            "MEMBER_INTERFACES": "members",
            "PC_MODE": "pc_mode",
            "BPDUGUARD_ENABLED": "bpdu_guard",
            "PORTTYPE_FAST_ENABLED": "port_type_fast",
            "MTU": "mtu",
            "SPEED": "speed",
            "ALLOWED_VLANS": "allowed_vlans",
            "ACCESS_VLAN": "access_vlan",
            "INTF_NAME": "ifname",
            "PO_ID": "ifname",
            "PEER1_PCID": "peer1_pcid",
            "PEER2_PCID": "peer2_pcid",
            "PEER1_MEMBER_INTERFACES": "peer1_members",
            "PEER2_MEMBER_INTERFACES": "peer2_members",
            "PEER1_ALLOWED_VLANS": "peer1_allowed_vlans",
            "PEER2_ALLOWED_VLANS": "peer2_allowed_vlans",
            "PO_DESC": "po_description",
            "PEER1_PO_DESC": "peer1_description",
            "PEER2_PO_DESC": "peer2_description",
            "PEER1_PO_CONF": "peer1_cmds",
            "PEER2_PO_CONF": "peer2_cmds",
            "PEER1_ACCESS_VLAN": "peer1_access_vlan",
            "PEER2_ACCESS_VLAN": "peer2_access_vlan",
            "DCI_ROUTING_PROTO": "dci_routing_proto",
            "DCI_ROUTING_TAG": "dci_routing_tag",
        }

        # New Interfaces
        self.pol_types = {
            11: {
                "pc_monitor": "int_monitor_port_channel_11_1",
                "pc_trunk": "int_port_channel_trunk_host_11_1",
                "pc_access": "int_port_channel_access_host_11_1",
                "pc_l3": "int_l3_port_channel",
                "sub_int_subint": "int_subif_11_1",
                "lo_lo": "int_loopback_11_1",
                "eth_trunk": "int_trunk_host_11_1",
                "eth_access": "int_access_host_11_1",
                "eth_routed": "int_routed_host_11_1",
                "eth_monitor": "int_monitor_ethernet_11_1",
                "eth_epl_routed": "epl_routed_intf",
                "vpc_trunk": "int_vpc_trunk_host_11_1",
                "vpc_access": "int_vpc_access_host_11_1",
                "svi_vlan": "int_vlan",
                "svi_vlan_admin_state": "int_vlan_admin_state",
                "st_fex_port_channel_st": "int_port_channel_fex_11_1",
                "aa_fex_port_channel_aa": "int_port_channel_aa_fex_11_1",
            },
            12: {
                "pc_monitor": "int_monitor_port_channel",
                "pc_trunk": "int_port_channel_trunk_host",
                "pc_access": "int_port_channel_access_host",
                "pc_l3": "int_l3_port_channel",
                "sub_int_subint": "int_subif",
                "lo_lo": "int_loopback",
                "lo_fabric": "int_fabric_loopback_11_1",
                "lo_mpls": "int_mpls_loopback",
                "eth_trunk": "int_trunk_host",
                "eth_access": "int_access_host",
                "eth_routed": "int_routed_host",
                "eth_monitor": "int_monitor_ethernet",
                "eth_epl_routed": "epl_routed_intf",
                "vpc_trunk": "int_vpc_trunk_host",
                "vpc_access": "int_vpc_access_host",
                "svi_vlan": "int_vlan",
                "svi_vlan_admin_state": "int_vlan_admin_state",
                "st_fex_port_channel_st": "int_port_channel_fex",
                "aa_fex_port_channel_aa": "int_port_channel_aa_fex",
            },
        }

        # New Interfaces
        self.int_types = {
            "pc": "INTERFACE_PORT_CHANNEL",
            "vpc": "INTERFACE_VPC",
            "sub_int": "SUBINTERFACE",
            "lo": "INTERFACE_LOOPBACK",
            "eth": "INTERFACE_ETHERNET",
            "svi": "INTERFACE_VLAN",
            "st_fex": "STRAIGHT_TROUGH_FEX",
            "aa_fex": "AA_FEX",
        }

        # New Interfaces
        self.int_index = {
            "INTERFACE_PORT_CHANNEL": 0,
            "INTERFACE_VPC": 1,
            "INTERFACE_ETHERNET": 2,
            "INTERFACE_LOOPBACK": 3,
            "SUBINTERFACE": 4,
            "INTERFACE_VLAN": 5,
            "STRAIGHT_TROUGH_FEX": 6,
            "AA_FEX": 7,
        }

    def log_msg(self, msg):

        if self.fd is None:
            self.fd = open("dcnm_intf.log", "a+")
        if self.fd is not None:
            self.fd.write(msg)
            self.fd.write("\n")
            self.fd.flush()

    def dcnm_intf_dump_have_all(self):

        lhave_all = []
        for have in self.have_all:
            lhave_all.append(
                {
                    "COMPLIANCE": have["complianceStatus"],
                    "FABRIC": have["fabricName"],
                    "IF_NAME": have["ifName"],
                    "IF_TYPE": have["ifType"],
                    "IP": have["ipAddress"],
                    "SNO": have["serialNo"],
                    "SYS NAME": have["sysName"],
                    "DELETABLE": have["deletable"],
                    "MARKED DELETE": have["markDeleted"],
                    "ALIAS": have["alias"],
                    "IS PHYSICAL": have["isPhysical"],
                    "UNDERLAY POLICIES": have["underlayPolicies"],
                }
            )
        self.log_msg(f"HAVE ALL = {lhave_all}")

    def dcnm_intf_xlate_speed(self, speed):

        # Controllers accept speed value in a particular format i.e. 1Gb, 100Gb etc. To make the playbook input
        # case insensitive for speed, this routine translates  the incoming speed to appropriate format.

        if speed == "":
            return ""

        if speed.lower() == "auto":
            return "auto".capitalize()
        else:
            comp = re.compile("([0-9]+)([a-zA-Z]+)")
            match = comp.match(speed)
            return str(match.group(1)) + match.group(2).capitalize()

    # New Interfaces
    def dcnm_intf_get_if_name(self, name, if_type):

        if "pc" == if_type:
            port_id = re.findall(r"\d+", name)
            return ("Port-channel" + str(port_id[0]), port_id[0])
        if "vpc" == if_type:
            port_id = re.findall(r"\d+", name)
            return ("vPC" + str(port_id[0]), port_id[0])
        if "sub_int" == if_type:
            port_id = re.findall(r"\d+\/\d+.\d+", name)
            return ("Ethernet" + str(port_id[0]), port_id[0])
        if "lo" == if_type:
            port_id = re.findall(r"\d+", name)
            return ("Loopback" + str(port_id[0]), port_id[0])
        if "eth" == if_type:
            port_id = re.findall(r"\d+\/\d+", name)
            return ("Ethernet" + str(port_id[0]), port_id[0])
        if "svi" == if_type:
            port_id = re.findall(r"\d+", name)
            return ("vlan" + str(port_id[0]), port_id[0])
        if "st_fex" == if_type:
            port_id = re.findall(r"\d+", name)
            return ("Port-channel" + str(port_id[0]), port_id[0])
        if "aa_fex" == if_type:
            port_id = re.findall(r"\d+", name)
            return ("vPC" + str(port_id[0]), port_id[0])

    def dcnm_intf_get_vpc_serial_number(self, sw):

        path = self.paths["VPC_SNO"].format(self.ip_sn[sw])
        resp = dcnm_send(self.module, "GET", path)

        if resp and resp["RETURN_CODE"] == 200:
            return resp["DATA"]["vpc_pair_sn"]
        else:
            return ""

    # Flatten the incoming config database and have the required fileds updated.
    # This modified config DB will be used while creating payloads. To avoid
    # messing up the incoming config make a copy of it.
    def dcnm_intf_copy_config(self):

        for cfg in self.config:

            if cfg.get("switch", None) is None:
                continue
            for sw in cfg["switch"]:

                c = copy.deepcopy(cfg)

                # Add type of interface
                ckeys = list(cfg.keys())
                for ck in ckeys:
                    if ck.startswith("profile"):

                        if "type" not in cfg:
                            self.module.fail_json(
                                msg="<type> element, which is mandatory is missing in config"
                            )

                        c[ck]["fabric"] = self.dcnm_intf_facts["fabric"]
                        if cfg["type"] == "vpc" or cfg["type"] == "aa_fex":
                            if self.vpc_ip_sn.get(sw, None) is None:
                                self.module.fail_json(
                                    msg="Switch '{0}' is not part of VPC pair, but given I/F '{1}' is of type VPC".format(
                                        sw, c["name"]
                                    )
                                )
                            else:
                                c[ck]["sno"] = self.vpc_ip_sn[sw]
                        else:
                            c[ck]["sno"] = self.ip_sn[sw]

                        ifname, port_id = self.dcnm_intf_get_if_name(
                            c["name"], c["type"]
                        )

                        if "mode" not in cfg["profile"]:
                            self.module.fail_json(
                                msg="Invalid parameters in playbook: while processing interface "
                                + ifname
                                + ", mode : Required parameter not found"
                            )
                        pol_ind_str = (
                            cfg["type"] + "_" + cfg["profile"]["mode"]
                        )

                        c[ck]["ifname"] = ifname
                        c[ck]["policy"] = self.pol_types[self.dcnm_version][
                            pol_ind_str
                        ]
                        self.pb_input.append(c[ck])

    def dcnm_intf_validate_interface_input(
        self, config, common_spec, prof_spec
    ):

        plist = []

        intf_info, invalid_params = validate_list_of_dicts(config, common_spec)
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(
                "while processing interface "
                + config[0]["name"]
                + "\n"
                + "\n".join(invalid_params)
            )
            self.module.fail_json(msg=mesg)

        self.intf_info.extend(intf_info)

        if prof_spec is not None:

            for item in intf_info:

                plist.append(item["profile"])
                intf_profile, invalid_params = validate_list_of_dicts(
                    plist, prof_spec
                )

                # Merge the info from the intf_profile into the intf_info to have a single dict to be used for building
                # payloads
                item["profile"].update(intf_profile[0])

                plist.remove(item["profile"])

                if invalid_params:
                    mesg = "Invalid parameters in playbook: {0}".format(
                        "while processing interface "
                        + config[0]["name"]
                        + ", "
                        + ", ".join(invalid_params)
                    )
                    self.module.fail_json(msg=mesg)

    def dcnm_intf_validate_port_channel_input(self, config):

        pc_spec = dict(
            name=dict(required=True, type="str"),
            switch=dict(required=True, type="list", elements="str"),
            type=dict(required=True, type="str"),
            deploy=dict(type="bool", default=True),
            profile=dict(required=True, type="dict"),
        )

        pc_prof_spec_trunk = dict(
            mode=dict(required=True, type="str"),
            members=dict(type="list"),
            pc_mode=dict(type="str", default="active"),
            bpdu_guard=dict(type="str", default="true"),
            port_type_fast=dict(type="bool", default=True),
            mtu=dict(type="str", default="jumbo"),
            speed=dict(type="str", default="Auto"),
            allowed_vlans=dict(type="str", default="none"),
            cmds=dict(type="list", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
        )

        pc_prof_spec_access = dict(
            mode=dict(required=True, type="str"),
            members=dict(type="list"),
            pc_mode=dict(type="str", default="active"),
            bpdu_guard=dict(type="str", default="true"),
            port_type_fast=dict(type="bool", default=True),
            mtu=dict(type="str", default="jumbo"),
            speed=dict(type="str", default="Auto"),
            access_vlan=dict(type="str", default=""),
            cmds=dict(type="list", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
        )

        pc_prof_spec_l3 = dict(
            mode=dict(required=True, type="str"),
            members=dict(type="list"),
            pc_mode=dict(type="str", default="active"),
            int_vrf=dict(type="str", default="default"),
            ipv4_addr=dict(type="ipv4", default=""),
            ipv4_mask_len=dict(type="int", default=8),
            route_tag=dict(type="str", default=""),
            mtu=dict(type="int", default=9216, range_min=576, range_max=9216),
            speed=dict(type="str", default="Auto"),
            cmds=dict(type="list", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
        )

        if "trunk" == config[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(
                config, pc_spec, pc_prof_spec_trunk
            )
        if "access" == config[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(
                config, pc_spec, pc_prof_spec_access
            )
        if "l3" == config[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(
                config, pc_spec, pc_prof_spec_l3
            )
        if "monitor" == config[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(config, pc_spec, None)

    def dcnm_intf_validate_virtual_port_channel_input(self, cfg):

        vpc_spec = dict(
            name=dict(required=True, type="str"),
            switch=dict(required=True, type="list"),
            type=dict(required=True, type="str"),
            deploy=dict(type="str", default=True),
            profile=dict(required=True, type="dict"),
        )

        vpc_prof_spec_trunk = dict(
            mode=dict(required=True, type="str"),
            peer1_pcid=dict(
                type="int", default=0, range_min=1, range_max=4096
            ),
            peer2_pcid=dict(
                type="int", default=0, range_min=1, range_max=4096
            ),
            peer1_members=dict(type="list"),
            peer2_members=dict(type="list"),
            pc_mode=dict(type="str", default="active"),
            bpdu_guard=dict(type="str", default="true"),
            port_type_fast=dict(type="bool", default=True),
            mtu=dict(type="str", default="jumbo"),
            speed=dict(type="str", default="Auto"),
            peer1_allowed_vlans=dict(type="str", default="none"),
            peer2_allowed_vlans=dict(type="str", default="none"),
            peer1_cmds=dict(type="list"),
            peer2_cmds=dict(type="list"),
            peer1_description=dict(type="str", default=""),
            peer2_description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
        )

        vpc_prof_spec_access = dict(
            mode=dict(required=True, type="str"),
            peer1_pcid=dict(
                type="int", default=0, range_min=1, range_max=4096
            ),
            peer2_pcid=dict(
                type="int", default=0, range_min=1, range_max=4096
            ),
            peer1_members=dict(type="list"),
            peer2_members=dict(type="list"),
            pc_mode=dict(type="str", default="active"),
            bpdu_guard=dict(type="str", default="true"),
            port_type_fast=dict(type="bool", default=True),
            mtu=dict(type="str", default="jumbo"),
            speed=dict(type="str", default="Auto"),
            peer1_access_vlan=dict(type="str", default=""),
            peer2_access_vlan=dict(type="str", default=""),
            peer1_cmds=dict(type="list"),
            peer2_cmds=dict(type="list"),
            peer1_description=dict(type="str", default=""),
            peer2_description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
        )

        if "trunk" == cfg[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(
                cfg, vpc_spec, vpc_prof_spec_trunk
            )
        if "access" == cfg[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(
                cfg, vpc_spec, vpc_prof_spec_access
            )

    def dcnm_intf_validate_sub_interface_input(self, cfg):

        sub_spec = dict(
            name=dict(required=True, type="str"),
            switch=dict(required=True, type="list"),
            type=dict(required=True, type="str"),
            deploy=dict(type="str", default=True),
            profile=dict(required=True, type="dict"),
        )

        sub_prof_spec = dict(
            mode=dict(required=True, type="str"),
            vlan=dict(required=True, type="int", range_min=2, range_max=3967),
            ipv4_addr=dict(required=True, type="ipv4"),
            ipv4_mask_len=dict(
                required=True, type="int", range_min=8, range_max=31
            ),
            int_vrf=dict(type="str", default="default"),
            ipv6_addr=dict(type="ipv6", default=""),
            ipv6_mask_len=dict(
                type="int", range_min=64, range_max=127, default=64
            ),
            mtu=dict(type="int", range_min=576, range_max=9216, default=9216),
            speed=dict(type="str", default="Auto"),
            cmds=dict(type="list", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
        )

        self.dcnm_intf_validate_interface_input(cfg, sub_spec, sub_prof_spec)

    def dcnm_intf_validate_loopback_interface_input(self, cfg):

        lo_spec = dict(
            name=dict(required=True, type="str"),
            switch=dict(required=True, type="list"),
            type=dict(required=True, type="str"),
            deploy=dict(type="str", default=True),
            profile=dict(required=True, type="dict"),
        )

        lo_prof_spec = dict(
            mode=dict(required=True, type="str"),
            ipv4_addr=dict(required=True, type="ipv4"),
            secondary_ipv4_addr=dict(type="ipv4", default=""),
            int_vrf=dict(type="str", default="default"),
            ipv6_addr=dict(type="ipv6", default=""),
            route_tag=dict(type="str", default=""),
            speed=dict(type="str", default="Auto"),
            cmds=dict(type="list", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
        )

        self.dcnm_intf_validate_interface_input(cfg, lo_spec, lo_prof_spec)

    def dcnm_intf_validate_ethernet_interface_input(self, cfg):

        eth_spec = dict(
            name=dict(required=True, type="str"),
            switch=dict(required=True, type="list", elements="str"),
            type=dict(required=True, type="str"),
            deploy=dict(type="str", default=True),
            profile=dict(required=True, type="dict"),
        )

        eth_prof_spec_trunk = dict(
            mode=dict(required=True, type="str"),
            bpdu_guard=dict(type="str", default="true"),
            port_type_fast=dict(type="bool", default=True),
            mtu=dict(
                type="str", default="jumbo", choices=["jumbo", "default"]
            ),
            speed=dict(type="str", default="Auto"),
            allowed_vlans=dict(type="str", default="none"),
            cmds=dict(type="list", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
        )

        eth_prof_spec_access = dict(
            mode=dict(required=True, type="str"),
            bpdu_guard=dict(type="str", default="true"),
            port_type_fast=dict(type="bool", default=True),
            mtu=dict(
                type="str", default="jumbo", choices=["jumbo", "default"]
            ),
            speed=dict(type="str", default="Auto"),
            access_vlan=dict(type="str", default=""),
            cmds=dict(type="list", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
        )

        eth_prof_spec_routed_host = dict(
            int_vrf=dict(type="str", default="default"),
            ipv4_addr=dict(type="ipv4", default=""),
            ipv4_mask_len=dict(type="int", default=8),
            route_tag=dict(type="str", default=""),
            mtu=dict(type="int", default=9216, range_min=576, range_max=9216),
            speed=dict(type="str", default="Auto"),
            cmds=dict(type="list", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
        )

        eth_prof_spec_epl_routed_host = dict(
            mode=dict(required=True, type="str"),
            ipv4_addr=dict(required=True, type="ipv4"),
            ipv4_mask_len=dict(type="int", default=8),
            ipv6_addr=dict(type="ipv6", default=""),
            ipv6_mask_len=dict(
                type="int", range_min=64, range_max=127, default=64
            ),
            route_tag=dict(type="str", default=""),
            mtu=dict(type="int", default=1500, range_max=9216),
            speed=dict(type="str", default="Auto"),
            cmds=dict(type="list", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
        )

        if "trunk" == cfg[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(
                cfg, eth_spec, eth_prof_spec_trunk
            )
        if "access" == cfg[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(
                cfg, eth_spec, eth_prof_spec_access
            )
        if "routed" == cfg[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(
                cfg, eth_spec, eth_prof_spec_routed_host
            )
        if "monitor" == cfg[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(cfg, eth_spec, None)
        if "epl_routed" == cfg[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(
                cfg, eth_spec, eth_prof_spec_epl_routed_host
            )

    def dcnm_intf_validate_vlan_interface_input(self, cfg):

        svi_spec = dict(
            name=dict(required=True, type="str"),
            switch=dict(required=True, type="list", elements="str"),
            type=dict(required=True, type="str"),
            deploy=dict(type="str", default=True),
            profile=dict(required=True, type="dict"),
        )

        svi_prof_spec = dict(
            mode=dict(required=True, type="str"),
            ipv4_addr=dict(type="ipv4", default=""),
            int_vrf=dict(type="str", default="default"),
            mtu=dict(type="int", range_min=68, range_max=9216, default=9216),
            cmds=dict(type="list", default="", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(required=True, type="bool", default=True),
            route_tag=dict(type=str, default=""),
            disable_ip_redirects=dict(type="bool", default=True),
            dhcp_server_addr1=dict(type="ipv4", default=""),
            dhcp_server_addr2=dict(type="ipv4", default=""),
            dhcp_server_addr3=dict(type="ipv4", default=""),
            adv_subnet_in_underlay=dict(type="bool", default=False),
            enable_hsrp=dict(type="bool", default=False),
            enable_netflow=dict(type="bool", default=False),
        )

        if cfg[0]["profile"].get("dhcp_server_addr1", "") != "":
            svi_prof_spec["vrf_dhcp1"] = dict(required=True, type="str")
        else:
            svi_prof_spec["vrf_dhcp1"] = dict(type="str", default="")

        if cfg[0]["profile"].get("dhcp_server_addr2", "") != "":
            svi_prof_spec["vrf_dhcp2"] = dict(required=True, type="str")
        else:
            svi_prof_spec["vrf_dhcp2"] = dict(type="str", default="")

        if cfg[0]["profile"].get("dhcp_server_addr3", "") != "":
            svi_prof_spec["vrf_dhcp3"] = dict(required=True, type="str")
        else:
            svi_prof_spec["vrf_dhcp3"] = dict(type="str", default="")

        if cfg[0]["profile"].get("ipv4_addr", False) is not False:
            svi_prof_spec["ipv4_mask_len"] = dict(
                required=True, type="int", range_min=1, range_max=31
            )
        else:
            svi_prof_spec["ipv4_mask_len"] = dict(
                type="int", range_min=1, range_max=31, default=""
            )

        if cfg[0]["profile"].get("enable_hsrp", False) is True:
            svi_prof_spec["hsrp_vip"] = dict(required=True, type="ipv4")
            svi_prof_spec["hsrp_group"] = dict(required=True, type="int")
            svi_prof_spec["preempt"] = dict(type="bool", default=False)
        else:
            svi_prof_spec["hsrp_vip"] = dict(type="ipv4", default="")
            svi_prof_spec["hsrp_group"] = dict(type="int", default="")
            if cfg[0]["profile"].get("preempt", False) is not False:
                self.module.fail_json(
                    msg="Invalid parameters in playbook: while processing interface "
                    + cfg[0]["name"]
                    + ", preempt : Not a valid parameter"
                )
        svi_prof_spec["hsrp_priority"] = dict(
            type="int", range_min=0, range_max=255, default=""
        )
        svi_prof_spec["hsrp_vmac"] = dict(type="str", default="")
        svi_prof_spec["hsrp_version"] = dict(
            type="int", range_min=1, range_max=2, default=""
        )

        if cfg[0]["profile"].get("enable_netflow", False) is True:
            svi_prof_spec["netflow_monitor"] = dict(required=True, type="str")

        self.dcnm_intf_validate_interface_input(cfg, svi_spec, svi_prof_spec)

    def dcnm_intf_validate_aa_fex_interface_input(self, cfg):

        fex_spec = dict(
            name=dict(required=True, type="str"),
            switch=dict(required=True, type="list"),
            type=dict(required=True, type="str"),
            deploy=dict(type="str", default=True),
            profile=dict(required=True, type="dict"),
        )

        fex_prof_spec = dict(
            mode=dict(required=True, type="str"),
            description=dict(type="str", default=""),
            peer1_members=dict(type="list", default=[], elements="str"),
            peer2_members=dict(type="list", default=[], elements="str"),
            mtu=dict(type="str", default="jumbo"),
            peer1_cmds=dict(type="list", default=[], elements="str"),
            peer2_cmds=dict(type="list", default=[], elements="str"),
            peer1_description=dict(type="str", default=""),
            peer2_description=dict(type="str", default=""),
            admin_state=dict(required=True, type="bool", default=True),
            enable_netflow=dict(type="bool", default=False),
        )

        if cfg[0]["profile"].get("enable_netflow", False) is True:
            fex_prof_spec["netflow_monitor"] = dict(required=True, type="str")

        self.dcnm_intf_validate_interface_input(cfg, fex_spec, fex_prof_spec)

    def dcnm_intf_validate_st_fex_interface_input(self, cfg):

        fex_spec = dict(
            name=dict(required=True, type="str"),
            switch=dict(required=True, type="list"),
            type=dict(required=True, type="str"),
            deploy=dict(type="str", default=True),
            profile=dict(required=True, type="dict"),
        )

        fex_prof_spec = dict(
            mode=dict(required=True, type="str"),
            description=dict(type="str", default=""),
            members=dict(type="list", default=[], elements="str"),
            mtu=dict(type="str", default="jumbo"),
            cmds=dict(type="list", default=[], elements="str"),
            po_description=dict(type="str", default=""),
            admin_state=dict(required=True, type="bool", default=True),
            enable_netflow=dict(type="bool", default=False),
        )

        if cfg[0]["profile"].get("enable_netflow", False) is True:
            fex_prof_spec["netflow_monitor"] = dict(required=True, type="str")

        self.dcnm_intf_validate_interface_input(cfg, fex_spec, fex_prof_spec)

    def dcnm_intf_validate_delete_state_input(self, cfg):

        del_spec = dict(
            name=dict(required=False, type="str"),
            switch=dict(required=False, type="list", elements="str"),
            deploy=dict(required=False, type="bool", default=True),
        )

        self.dcnm_intf_validate_interface_input(cfg, del_spec, None)

    def dcnm_intf_validate_query_state_input(self, cfg):

        query_spec = dict(
            name=dict(type="str", default=""),
            switch=dict(required=True, type="list", elements="str"),
        )

        self.dcnm_intf_validate_interface_input(cfg, query_spec, None)

    def dcnm_intf_validate_overridden_state_input(self, cfg):

        overridden_spec = dict(
            name=dict(required=False, type="str", default=""),
            switch=dict(required=False, type="list", elements="str"),
        )

        self.dcnm_intf_validate_interface_input(cfg, overridden_spec, None)

    # New Interfaces
    def dcnm_intf_validate_input(self):
        """Parse the playbook values, validate to param specs."""

        # Inputs will vary for each type of interface and for each state. Make specific checks
        # for each case.

        cfg = []
        for item in self.config:

            citem = copy.deepcopy(item)

            cfg.append(citem)

            if self.module.params["state"] == "deleted":
                # config for delete state is different for all interfaces. It may not have the profile
                # construct. So validate deleted state differently
                self.dcnm_intf_validate_delete_state_input(cfg)
            elif self.module.params["state"] == "query":
                # config for query state is different for all interfaces. It may not have the profile
                # construct. So validate query state differently
                self.dcnm_intf_validate_query_state_input(cfg)
            elif (self.module.params["state"] == "overridden") and not (
                any("profile" in key for key in item)
            ):
                # config for overridden state is different for all interfaces. It may not have the profile
                # construct. So validate overridden state differently
                self.dcnm_intf_validate_overridden_state_input(cfg)
            else:
                if "type" not in item:
                    mesg = "Invalid parameters in playbook: {0}".format(
                        "while processing interface " + item["name"] + "\n"
                        'mandatory object "type" missing'
                    )
                    self.module.fail_json(msg=mesg)

                if item["type"] == "pc":
                    self.dcnm_intf_validate_port_channel_input(cfg)
                if item["type"] == "vpc":
                    self.dcnm_intf_validate_virtual_port_channel_input(cfg)
                if item["type"] == "sub_int":
                    self.dcnm_intf_validate_sub_interface_input(cfg)
                if item["type"] == "lo":
                    self.dcnm_intf_validate_loopback_interface_input(cfg)
                if item["type"] == "eth":
                    self.dcnm_intf_validate_ethernet_interface_input(cfg)
                if item["type"] == "svi":
                    self.dcnm_intf_validate_vlan_interface_input(cfg)
                if item["type"] == "st_fex":
                    self.dcnm_intf_validate_st_fex_interface_input(cfg)
                if item["type"] == "aa_fex":
                    self.dcnm_intf_validate_aa_fex_interface_input(cfg)
            cfg.remove(citem)

    def dcnm_intf_get_pc_payload(self, delem, intf, profile):

        # Extract port id from the given name, which is of the form 'po300'

        ifname, port_id = self.dcnm_intf_get_if_name(
            delem["name"], delem["type"]
        )
        intf["interfaces"][0].update({"ifName": ifname})

        if delem[profile]["mode"] == "trunk":
            if delem[profile]["members"] is None:
                intf["interfaces"][0]["nvPairs"]["MEMBER_INTERFACES"] = ""
            else:
                intf["interfaces"][0]["nvPairs"][
                    "MEMBER_INTERFACES"
                ] = ",".join(delem[profile]["members"])
            intf["interfaces"][0]["nvPairs"]["PC_MODE"] = delem[profile][
                "pc_mode"
            ]
            intf["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"] = delem[
                profile
            ]["bpdu_guard"].lower()
            intf["interfaces"][0]["nvPairs"]["PORTTYPE_FAST_ENABLED"] = str(
                delem[profile]["port_type_fast"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )
            intf["interfaces"][0]["nvPairs"]["ALLOWED_VLANS"] = delem[profile][
                "allowed_vlans"
            ]
            intf["interfaces"][0]["nvPairs"]["PO_ID"] = ifname
        if delem[profile]["mode"] == "access":
            if delem[profile]["members"] is None:
                intf["interfaces"][0]["nvPairs"]["MEMBER_INTERFACES"] = ""
            else:
                intf["interfaces"][0]["nvPairs"][
                    "MEMBER_INTERFACES"
                ] = ",".join(delem[profile]["members"])
            intf["interfaces"][0]["nvPairs"]["PC_MODE"] = delem[profile][
                "pc_mode"
            ]
            intf["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"] = delem[
                profile
            ]["bpdu_guard"].lower()
            intf["interfaces"][0]["nvPairs"]["PORTTYPE_FAST_ENABLED"] = str(
                delem[profile]["port_type_fast"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )
            intf["interfaces"][0]["nvPairs"]["ACCESS_VLAN"] = delem[profile][
                "access_vlan"
            ]
            intf["interfaces"][0]["nvPairs"]["PO_ID"] = ifname
        if delem[profile]["mode"] == "l3":
            if delem[profile]["members"] is None:
                intf["interfaces"][0]["nvPairs"]["MEMBER_INTERFACES"] = ""
            else:
                intf["interfaces"][0]["nvPairs"][
                    "MEMBER_INTERFACES"
                ] = ",".join(delem[profile]["members"])
            intf["interfaces"][0]["nvPairs"]["PC_MODE"] = delem[profile][
                "pc_mode"
            ]
            intf["interfaces"][0]["nvPairs"]["INTF_VRF"] = delem[profile][
                "int_vrf"
            ]
            intf["interfaces"][0]["nvPairs"]["IP"] = str(
                delem[profile]["ipv4_addr"]
            )
            if delem[profile]["ipv4_addr"] != "":
                intf["interfaces"][0]["nvPairs"]["PREFIX"] = str(
                    delem[profile]["ipv4_mask_len"]
                )
            else:
                intf["interfaces"][0]["nvPairs"]["PREFIX"] = ""
            intf["interfaces"][0]["nvPairs"]["ROUTING_TAG"] = delem[profile][
                "route_tag"
            ]
            intf["interfaces"][0]["nvPairs"]["PO_ID"] = ifname
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )
        if delem[profile]["mode"] == "monitor":
            intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname

        if delem[profile]["mode"] != "monitor":
            intf["interfaces"][0]["nvPairs"]["DESC"] = delem[profile][
                "description"
            ]
            if delem[profile]["cmds"] is None:
                intf["interfaces"][0]["nvPairs"]["CONF"] = ""
            else:
                intf["interfaces"][0]["nvPairs"]["CONF"] = "\n".join(
                    delem[profile]["cmds"]
                )
            intf["interfaces"][0]["nvPairs"]["ADMIN_STATE"] = str(
                delem[profile]["admin_state"]
            ).lower()
            intf["interfaces"][0]["nvPairs"][
                "SPEED"
            ] = self.dcnm_intf_xlate_speed(
                str(delem[profile].get("speed", ""))
            )

    def dcnm_intf_get_vpc_payload(self, delem, intf, profile):

        # Extract port id from the given name, which is of the form 'vpc300'

        ifname, port_id = self.dcnm_intf_get_if_name(
            delem["name"], delem["type"]
        )
        intf["interfaces"][0].update({"ifName": ifname})

        if delem[profile]["mode"] == "trunk":

            if delem[profile]["peer1_members"] is None:
                intf["interfaces"][0]["nvPairs"][
                    "PEER1_MEMBER_INTERFACES"
                ] = ""
            else:
                intf["interfaces"][0]["nvPairs"][
                    "PEER1_MEMBER_INTERFACES"
                ] = ",".join(delem[profile]["peer1_members"])

            if delem[profile]["peer2_members"] is None:
                intf["interfaces"][0]["nvPairs"][
                    "PEER2_MEMBER_INTERFACES"
                ] = ""
            else:
                intf["interfaces"][0]["nvPairs"][
                    "PEER2_MEMBER_INTERFACES"
                ] = ",".join(delem[profile]["peer2_members"])

            intf["interfaces"][0]["nvPairs"]["PC_MODE"] = delem[profile][
                "pc_mode"
            ]
            intf["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"] = delem[
                profile
            ]["bpdu_guard"].lower()
            intf["interfaces"][0]["nvPairs"]["PORTTYPE_FAST_ENABLED"] = str(
                delem[profile]["port_type_fast"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )
            intf["interfaces"][0]["nvPairs"]["PEER1_ALLOWED_VLANS"] = delem[
                profile
            ]["peer1_allowed_vlans"]
            intf["interfaces"][0]["nvPairs"]["PEER2_ALLOWED_VLANS"] = delem[
                profile
            ]["peer2_allowed_vlans"]

            if delem[profile]["peer1_pcid"] == 0:
                intf["interfaces"][0]["nvPairs"]["PEER1_PCID"] = str(port_id)
            else:
                intf["interfaces"][0]["nvPairs"]["PEER1_PCID"] = str(
                    delem[profile]["peer1_pcid"]
                )

            if delem[profile]["peer2_pcid"] == 0:
                intf["interfaces"][0]["nvPairs"]["PEER2_PCID"] = str(port_id)
            else:
                intf["interfaces"][0]["nvPairs"]["PEER2_PCID"] = str(
                    delem[profile]["peer2_pcid"]
                )

        if delem[profile]["mode"] == "access":

            if delem[profile]["peer1_members"] is None:
                intf["interfaces"][0]["nvPairs"][
                    "PEER1_MEMBER_INTERFACES"
                ] = ""
            else:
                intf["interfaces"][0]["nvPairs"][
                    "PEER1_MEMBER_INTERFACES"
                ] = ",".join(delem[profile]["peer1_members"])

            if delem[profile]["peer2_members"] is None:
                intf["interfaces"][0]["nvPairs"][
                    "PEER2_MEMBER_INTERFACES"
                ] = ""
            else:
                intf["interfaces"][0]["nvPairs"][
                    "PEER2_MEMBER_INTERFACES"
                ] = ",".join(delem[profile]["peer2_members"])

            intf["interfaces"][0]["nvPairs"]["PC_MODE"] = delem[profile][
                "pc_mode"
            ]
            intf["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"] = delem[
                profile
            ]["bpdu_guard"].lower()
            intf["interfaces"][0]["nvPairs"]["PORTTYPE_FAST_ENABLED"] = str(
                delem[profile]["port_type_fast"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )
            intf["interfaces"][0]["nvPairs"]["PEER1_ACCESS_VLAN"] = delem[
                profile
            ]["peer1_access_vlan"]
            intf["interfaces"][0]["nvPairs"]["PEER2_ACCESS_VLAN"] = delem[
                profile
            ]["peer2_access_vlan"]

            if delem[profile]["peer1_pcid"] == 0:
                intf["interfaces"][0]["nvPairs"]["PEER1_PCID"] = str(port_id)
            else:
                intf["interfaces"][0]["nvPairs"]["PEER1_PCID"] = str(
                    delem[profile]["peer1_pcid"]
                )

            if delem[profile]["peer2_pcid"] == 0:
                intf["interfaces"][0]["nvPairs"]["PEER2_PCID"] = str(port_id)
            else:
                intf["interfaces"][0]["nvPairs"]["PEER2_PCID"] = str(
                    delem[profile]["peer2_pcid"]
                )

        intf["interfaces"][0]["nvPairs"]["PEER1_PO_DESC"] = delem[profile][
            "peer1_description"
        ]
        intf["interfaces"][0]["nvPairs"]["PEER2_PO_DESC"] = delem[profile][
            "peer2_description"
        ]
        if delem[profile]["peer1_cmds"] is None:
            intf["interfaces"][0]["nvPairs"]["PEER1_PO_CONF"] = ""
        else:
            intf["interfaces"][0]["nvPairs"]["PEER1_PO_CONF"] = "\n".join(
                delem[profile]["peer1_cmds"]
            )
        if delem[profile]["peer2_cmds"] is None:
            intf["interfaces"][0]["nvPairs"]["PEER2_PO_CONF"] = ""
        else:
            intf["interfaces"][0]["nvPairs"]["PEER2_PO_CONF"] = "\n".join(
                delem[profile]["peer2_cmds"]
            )
        intf["interfaces"][0]["nvPairs"]["ADMIN_STATE"] = str(
            delem[profile]["admin_state"]
        ).lower()
        intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname
        intf["interfaces"][0]["nvPairs"]["SPEED"] = self.dcnm_intf_xlate_speed(
            str(delem[profile].get("speed", ""))
        )

    def dcnm_intf_get_sub_intf_payload(self, delem, intf, profile):

        # Extract port id from the given name, which is of the form 'po300'

        ifname, port_id = self.dcnm_intf_get_if_name(
            delem["name"], delem["type"]
        )
        intf["interfaces"][0].update({"ifName": ifname})

        intf["interfaces"][0]["nvPairs"]["VLAN"] = str(delem[profile]["vlan"])
        intf["interfaces"][0]["nvPairs"]["INTF_VRF"] = delem[profile][
            "int_vrf"
        ]
        intf["interfaces"][0]["nvPairs"]["IP"] = str(
            delem[profile]["ipv4_addr"]
        )
        intf["interfaces"][0]["nvPairs"]["PREFIX"] = str(
            delem[profile]["ipv4_mask_len"]
        )
        if delem[profile]["ipv6_addr"]:
            intf["interfaces"][0]["nvPairs"]["IPv6"] = str(
                delem[profile]["ipv6_addr"]
            )
            intf["interfaces"][0]["nvPairs"]["IPv6_PREFIX"] = str(
                delem[profile]["ipv6_mask_len"]
            )
        else:
            intf["interfaces"][0]["nvPairs"]["IPv6"] = ""
            intf["interfaces"][0]["nvPairs"]["IPv6_PREFIX"] = ""
        intf["interfaces"][0]["nvPairs"]["MTU"] = str(delem[profile]["mtu"])
        intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname
        intf["interfaces"][0]["nvPairs"]["DESC"] = delem[profile][
            "description"
        ]
        if delem[profile]["cmds"] is None:
            intf["interfaces"][0]["nvPairs"]["CONF"] = ""
        else:
            intf["interfaces"][0]["nvPairs"]["CONF"] = "\n".join(
                delem[profile]["cmds"]
            )
        intf["interfaces"][0]["nvPairs"]["ADMIN_STATE"] = str(
            delem[profile]["admin_state"]
        ).lower()
        intf["interfaces"][0]["nvPairs"]["SPEED"] = self.dcnm_intf_xlate_speed(
            str(delem[profile].get("speed", ""))
        )

    def dcnm_intf_get_loopback_payload(self, delem, intf, profile):

        # Properties common for all loopback interface modes
        ifname, port_id = self.dcnm_intf_get_if_name(
            delem["name"], delem["type"]
        )
        intf["interfaces"][0].update({"ifName": ifname})

        intf["interfaces"][0]["nvPairs"]["IP"] = str(
            delem[profile]["ipv4_addr"]
        )
        intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname
        intf["interfaces"][0]["nvPairs"]["DESC"] = delem[profile][
            "description"
        ]
        if delem[profile]["cmds"] is None:
            intf["interfaces"][0]["nvPairs"]["CONF"] = ""
        else:
            intf["interfaces"][0]["nvPairs"]["CONF"] = "\n".join(
                delem[profile]["cmds"]
            )
        intf["interfaces"][0]["nvPairs"]["ADMIN_STATE"] = str(
            delem[profile]["admin_state"]
        ).lower()

        intf["interfaces"][0]["nvPairs"]["SPEED"] = self.dcnm_intf_xlate_speed(
            str(delem[profile].get("speed", ""))
        )

        # Properties for mode 'lo' Loopback Interfaces
        if delem[profile]["mode"] == "lo":

            intf["interfaces"][0]["nvPairs"]["INTF_VRF"] = delem[profile][
                "int_vrf"
            ]
            intf["interfaces"][0]["nvPairs"]["V6IP"] = str(
                delem[profile]["ipv6_addr"]
            )
            intf["interfaces"][0]["nvPairs"]["ROUTE_MAP_TAG"] = delem[profile][
                "route_tag"
            ]

        # Properties for mode 'fabric' Loopback Interfaces
        if delem[profile]["mode"] == "fabric":

            intf["interfaces"][0]["nvPairs"]["SECONDARY_IP"] = delem[profile][
                "secondary_ipv4_addr"
            ]
            intf["interfaces"][0]["nvPairs"]["V6IP"] = str(
                delem[profile]["ipv6_addr"]
            )
            intf["interfaces"][0]["nvPairs"]["ROUTE_MAP_TAG"] = delem[profile][
                "route_tag"
            ]

        # Properties for mode 'mpls' Loopback Interfaces
        if delem[profile]["mode"] == "mpls":

            # These properties are read_only properties and are not exposed as
            # properties that can be modified.  They will be updated from the
            # self.have dictionary to reflect the actual values later in the
            # code workflow that walks the want values and compares to have values.
            intf["interfaces"][0]["nvPairs"][
                "DCI_ROUTING_PROTO"
            ] = "PLACE_HOLDER"
            intf["interfaces"][0]["nvPairs"][
                "DCI_ROUTING_TAG"
            ] = "PLACE_HOLDER"

    def dcnm_intf_get_eth_payload(self, delem, intf, profile):

        # Extract port id from the given name, which is of the form 'po300'

        ifname, port_id = self.dcnm_intf_get_if_name(
            delem["name"], delem["type"]
        )
        intf["interfaces"][0].update({"ifName": ifname})

        if delem[profile]["mode"] == "trunk":
            intf["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"] = delem[
                profile
            ]["bpdu_guard"].lower()
            intf["interfaces"][0]["nvPairs"]["PORTTYPE_FAST_ENABLED"] = str(
                delem[profile]["port_type_fast"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )
            intf["interfaces"][0]["nvPairs"]["ALLOWED_VLANS"] = delem[profile][
                "allowed_vlans"
            ]
            intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname
        if delem[profile]["mode"] == "access":
            intf["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"] = delem[
                profile
            ]["bpdu_guard"].lower()
            intf["interfaces"][0]["nvPairs"]["PORTTYPE_FAST_ENABLED"] = str(
                delem[profile]["port_type_fast"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )
            intf["interfaces"][0]["nvPairs"]["ACCESS_VLAN"] = delem[profile][
                "access_vlan"
            ]
            intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname
        if delem[profile]["mode"] == "routed":
            intf["interfaces"][0]["nvPairs"]["INTF_VRF"] = delem[profile][
                "int_vrf"
            ]
            intf["interfaces"][0]["nvPairs"]["IP"] = str(
                delem[profile]["ipv4_addr"]
            )
            if delem[profile]["ipv4_addr"] != "":
                intf["interfaces"][0]["nvPairs"]["PREFIX"] = str(
                    delem[profile]["ipv4_mask_len"]
                )
            else:
                intf["interfaces"][0]["nvPairs"]["PREFIX"] = ""
            intf["interfaces"][0]["nvPairs"]["ROUTING_TAG"] = delem[profile][
                "route_tag"
            ]
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )
            intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname
        if delem[profile]["mode"] == "monitor":
            intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname
        if delem[profile]["mode"] == "epl_routed":
            intf["interfaces"][0]["nvPairs"]["IP"] = str(
                delem[profile]["ipv4_addr"]
            )
            intf["interfaces"][0]["nvPairs"]["PREFIX"] = str(
                delem[profile]["ipv4_mask_len"]
            )
            intf["interfaces"][0]["nvPairs"]["IPv6"] = str(
                delem[profile]["ipv6_addr"]
            )
            intf["interfaces"][0]["nvPairs"]["IPv6_PREFIX"] = str(
                delem[profile]["ipv6_mask_len"]
            )
            intf["interfaces"][0]["nvPairs"]["ROUTING_TAG"] = delem[profile][
                "route_tag"
            ]
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )
            intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname

        if delem[profile]["mode"] != "monitor":
            intf["interfaces"][0]["nvPairs"]["DESC"] = delem[profile][
                "description"
            ]
            if delem[profile]["cmds"] is None:
                intf["interfaces"][0]["nvPairs"]["CONF"] = ""
            else:
                intf["interfaces"][0]["nvPairs"]["CONF"] = "\n".join(
                    delem[profile]["cmds"]
                )
            intf["interfaces"][0]["nvPairs"]["ADMIN_STATE"] = str(
                delem[profile]["admin_state"]
            ).lower()
            intf["interfaces"][0]["nvPairs"][
                "SPEED"
            ] = self.dcnm_intf_xlate_speed(
                str(delem[profile].get("speed", ""))
            )

    def dcnm_intf_get_st_fex_payload(self, delem, intf, profile):

        # Extract port id from the given name, which is of the form 'po300'

        ifname, port_id = self.dcnm_intf_get_if_name(
            delem["name"], delem["type"]
        )
        intf["interfaces"][0].update({"ifName": ifname})

        if delem[profile]["members"] is None:
            intf["interfaces"][0]["nvPairs"]["MEMBER_INTERFACES"] = ""
        else:
            intf["interfaces"][0]["nvPairs"]["MEMBER_INTERFACES"] = ",".join(
                delem[profile]["members"]
            )

        intf["interfaces"][0]["nvPairs"]["MTU"] = str(delem[profile]["mtu"])
        intf["interfaces"][0]["nvPairs"]["PO_ID"] = ifname
        intf["interfaces"][0]["nvPairs"]["FEX_ID"] = port_id
        intf["interfaces"][0]["nvPairs"]["DESC"] = delem["profile"][
            "description"
        ]
        intf["interfaces"][0]["nvPairs"]["PO_DESC"] = delem["profile"][
            "po_description"
        ]
        if delem[profile]["cmds"] is None:
            intf["interfaces"][0]["nvPairs"]["CONF"] = ""
        else:
            intf["interfaces"][0]["nvPairs"]["CONF"] = "\n".join(
                delem[profile]["cmds"]
            )
        intf["interfaces"][0]["nvPairs"]["ADMIN_STATE"] = str(
            delem[profile]["admin_state"]
        ).lower()

        intf["interfaces"][0]["nvPairs"]["ENABLE_NETFLOW"] = str(
            delem[profile]["enable_netflow"]
        ).lower()

        if str(delem[profile]["enable_netflow"]).lower() == "true":
            intf["interfaces"][0]["nvPairs"]["NETFLOW_MONITOR"] = str(
                delem[profile]["netflow_monitor"]
            )

        intf["interfaces"][0]["nvPairs"]["SPEED"] = self.dcnm_intf_xlate_speed(
            str(delem[profile].get("speed", ""))
        )

    def dcnm_intf_get_aa_fex_payload(self, delem, intf, profile):

        # Extract port id from the given name, which is of the form 'vPC300'

        ifname, port_id = self.dcnm_intf_get_if_name(
            delem["name"], delem["type"]
        )
        intf["interfaces"][0].update({"ifName": ifname})

        if delem[profile]["peer1_members"] is None:
            intf["interfaces"][0]["nvPairs"]["PEER1_MEMBER_INTERFACES"] = ""
        else:
            intf["interfaces"][0]["nvPairs"][
                "PEER1_MEMBER_INTERFACES"
            ] = ",".join(delem[profile]["peer1_members"])

        if delem[profile]["peer2_members"] is None:
            intf["interfaces"][0]["nvPairs"]["PEER2_MEMBER_INTERFACES"] = ""
        else:
            intf["interfaces"][0]["nvPairs"][
                "PEER2_MEMBER_INTERFACES"
            ] = ",".join(delem[profile]["peer2_members"])

        intf["interfaces"][0]["nvPairs"]["MTU"] = str(delem[profile]["mtu"])
        intf["interfaces"][0]["nvPairs"]["PEER1_PCID"] = port_id
        intf["interfaces"][0]["nvPairs"]["PEER2_PCID"] = port_id
        intf["interfaces"][0]["nvPairs"]["FEX_ID"] = port_id
        intf["interfaces"][0]["nvPairs"]["DESC"] = delem["profile"][
            "description"
        ]
        intf["interfaces"][0]["nvPairs"]["PEER1_PO_DESC"] = delem["profile"][
            "peer1_description"
        ]
        intf["interfaces"][0]["nvPairs"]["PEER2_PO_DESC"] = delem["profile"][
            "peer2_description"
        ]

        if delem[profile]["peer1_cmds"] is None:
            intf["interfaces"][0]["nvPairs"]["PEER1_PO_CONF"] = ""
        else:
            intf["interfaces"][0]["nvPairs"]["PEER1_PO_CONF"] = "\n".join(
                delem[profile]["peer1_cmds"]
            )

        if delem[profile]["peer2_cmds"] is None:
            intf["interfaces"][0]["nvPairs"]["PEER2_PO_CONF"] = ""
        else:
            intf["interfaces"][0]["nvPairs"]["PEER2_PO_CONF"] = "\n".join(
                delem[profile]["peer2_cmds"]
            )

        intf["interfaces"][0]["nvPairs"]["ADMIN_STATE"] = str(
            delem[profile]["admin_state"]
        ).lower()

        intf["interfaces"][0]["nvPairs"]["ENABLE_NETFLOW"] = str(
            delem[profile]["enable_netflow"]
        ).lower()

        if str(delem[profile]["enable_netflow"]).lower() == "true":
            intf["interfaces"][0]["nvPairs"]["NETFLOW_MONITOR"] = str(
                delem[profile]["netflow_monitor"]
            )

        intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname

        intf["interfaces"][0]["nvPairs"]["SPEED"] = self.dcnm_intf_xlate_speed(
            str(delem[profile].get("speed", ""))
        )

    def dcnm_intf_get_svi_payload(self, delem, intf, profile):

        # Extract port id from the given name, which is of the form 'vlan300'

        ifname, port_id = self.dcnm_intf_get_if_name(
            delem["name"], delem["type"]
        )
        intf["interfaces"][0].update({"ifName": ifname})

        if delem[profile]["mode"] == "vlan":
            intf["interfaces"][0]["nvPairs"]["INTF_VRF"] = delem[profile][
                "int_vrf"
            ]
            intf["interfaces"][0]["nvPairs"]["IP"] = str(
                delem[profile]["ipv4_addr"]
            )
            intf["interfaces"][0]["nvPairs"]["PREFIX"] = str(
                delem[profile]["ipv4_mask_len"]
            )
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )
            intf["interfaces"][0]["nvPairs"]["ROUTING_TAG"] = str(
                delem[profile]["route_tag"]
            )
            intf["interfaces"][0]["nvPairs"]["DISABLE_IP_REDIRECTS"] = str(
                delem[profile]["disable_ip_redirects"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["DESC"] = delem[profile][
                "description"
            ]

            if delem[profile]["cmds"] is None:
                intf["interfaces"][0]["nvPairs"]["CONF"] = ""
            else:
                intf["interfaces"][0]["nvPairs"]["CONF"] = "\n".join(
                    delem[profile]["cmds"]
                )
            # intf["interfaces"][0]["nvPairs"]["CONF"] = str(delem[profile]["cmds"])
            intf["interfaces"][0]["nvPairs"]["ADMIN_STATE"] = str(
                delem[profile]["admin_state"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["ENABLE_HSRP"] = str(
                delem[profile]["enable_hsrp"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["HSRP_VIP"] = str(
                delem[profile]["hsrp_vip"]
            )
            intf["interfaces"][0]["nvPairs"]["HSRP_GROUP"] = str(
                delem[profile]["hsrp_group"]
            )
            if str(delem[profile]["enable_hsrp"]).lower() == "true":
                intf["interfaces"][0]["nvPairs"]["PREEMPT"] = str(
                    delem[profile]["preempt"]
                ).lower()
            else:
                intf["interfaces"][0]["nvPairs"]["PREEMPT"] = str(
                    False
                ).lower()

            intf["interfaces"][0]["nvPairs"]["HSRP_VERSION"] = str(
                delem[profile]["hsrp_version"]
            )
            intf["interfaces"][0]["nvPairs"]["HSRP_PRIORITY"] = str(
                delem[profile]["hsrp_priority"]
            )
            intf["interfaces"][0]["nvPairs"]["MAC"] = str(
                delem[profile]["hsrp_vmac"]
            )
            intf["interfaces"][0]["nvPairs"]["dhcpServerAddr1"] = str(
                delem[profile]["dhcp_server_addr1"]
            )
            intf["interfaces"][0]["nvPairs"]["vrfDhcp1"] = str(
                delem[profile]["vrf_dhcp1"]
            )
            intf["interfaces"][0]["nvPairs"]["dhcpServerAddr2"] = str(
                delem[profile]["dhcp_server_addr2"]
            )
            intf["interfaces"][0]["nvPairs"]["vrfDhcp2"] = str(
                delem[profile]["vrf_dhcp2"]
            )
            intf["interfaces"][0]["nvPairs"]["dhcpServerAddr3"] = str(
                delem[profile]["dhcp_server_addr3"]
            )
            intf["interfaces"][0]["nvPairs"]["vrfDhcp3"] = str(
                delem[profile]["vrf_dhcp3"]
            )
            intf["interfaces"][0]["nvPairs"]["advSubnetInUnderlay"] = str(
                delem[profile]["adv_subnet_in_underlay"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["ENABLE_NETFLOW"] = str(
                delem[profile]["enable_netflow"]
            ).lower()

            if str(delem[profile]["enable_netflow"]).lower() == "true":
                intf["interfaces"][0]["nvPairs"]["NETFLOW_MONITOR"] = str(
                    delem[profile]["netflow_monitor"]
                )
            else:
                intf["interfaces"][0]["nvPairs"]["NETFLOW_MONITOR"] = ""

            intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname

            intf["interfaces"][0]["nvPairs"][
                "SPEED"
            ] = self.dcnm_intf_xlate_speed(
                str(delem[profile].get("speed", ""))
            )

    # New Interfaces
    def dcnm_get_intf_payload(self, delem, sw):

        intf = {
            "deploy": False,
            "policy": "",
            "interfaceType": "",
            "interfaces": [
                {
                    "serialNumber": "",
                    "interfaceType": "",
                    "ifName": "",
                    "fabricName": "",
                    "nvPairs": {"SPEED": "Auto"},
                }
            ],
            "skipResourceCheck": str(False).lower(),
        }

        # Each interface type will have a different profile name. Set that based on the interface type and use that
        # below to extract the required parameters

        # Monitor ports are not put into diff_deploy, since they don't have any
        # commands to be executed on switch. This will affect the idempotence
        # check
        if delem["profile"]["mode"] == "monitor":
            intf.update({"deploy": False})
        else:
            intf.update({"deploy": delem["deploy"]})

        # Each type of interface and mode will have a different set of params.
        # First fill in the params common to all interface types and modes

        if "vpc" == delem["type"] or "aa_fex" == delem["type"]:
            intf["interfaces"][0].update(
                {"serialNumber": str(self.vpc_ip_sn[sw])}
            )
        else:
            intf["interfaces"][0].update({"serialNumber": str(self.ip_sn[sw])})

        intf["interfaces"][0].update(
            {"interfaceType": self.int_types[delem["type"]]}
        )
        intf["interfaces"][0].update({"fabricName": self.fabric})

        if "profile" not in delem.keys():
            # for state 'deleted', 'profile' construct is not included. So just update the ifName here
            # and return. Rest of the code is all 'profile' specific and hence not required for 'deleted'

            ifname, port_id = self.dcnm_intf_get_if_name(
                delem["name"], delem["type"]
            )
            intf["interfaces"][0].update({"ifName": ifname})
            return intf

        pol_ind_str = delem["type"] + "_" + delem["profile"]["mode"]
        intf.update({"policy": self.pol_types[self.dcnm_version][pol_ind_str]})
        intf.update({"interfaceType": self.int_types[delem["type"]]})

        # Rest of the data in the dict depends on the interface type and the template

        if "pc" == delem["type"]:
            self.dcnm_intf_get_pc_payload(delem, intf, "profile")
        if "sub_int" == delem["type"]:
            self.dcnm_intf_get_sub_intf_payload(delem, intf, "profile")
        if "lo" == delem["type"]:
            self.dcnm_intf_get_loopback_payload(delem, intf, "profile")
        if "vpc" == delem["type"]:
            self.dcnm_intf_get_vpc_payload(delem, intf, "profile")
        if "eth" == delem["type"]:
            self.dcnm_intf_get_eth_payload(delem, intf, "profile")

            # Ethernet interface payload does not have interfaceType and skipResourceCheck flags. Pop
            # them out
            intf.pop("skipResourceCheck")

        if "svi" == delem["type"]:
            self.dcnm_intf_get_svi_payload(delem, intf, "profile")

        if "st_fex" == delem["type"]:
            self.dcnm_intf_get_st_fex_payload(delem, intf, "profile")

        if "aa_fex" == delem["type"]:
            self.dcnm_intf_get_aa_fex_payload(delem, intf, "profile")

        return intf

    def dcnm_intf_merge_intf_info(self, intf_info, if_head):

        if not if_head:
            if_head.append(intf_info)
            return

        for item in if_head:

            if item["policy"] == intf_info["policy"]:
                item["interfaces"].append(intf_info["interfaces"][0])
                return
        if_head.append(intf_info)

    def dcnm_intf_get_want(self):

        if self.config == []:
            return

        if self.intf_info == []:
            return

        # self.intf_info is a list of directories each having config related to a particular interface
        for delem in self.intf_info:
            if any("profile" in key for key in delem):
                for sw in delem["switch"]:
                    intf_payload = self.dcnm_get_intf_payload(delem, sw)
                    if intf_payload not in self.want:
                        self.want.append(intf_payload)

    def dcnm_intf_get_intf_info(self, ifName, serialNumber, ifType):

        # For VPC and AA_FEX interfaces the serialNumber will be a combined one. But GET on interface cannot
        # pass this combined serial number. We will have to pass individual ones

        if ifType == "INTERFACE_VPC" or ifType == "AA_FEX":
            sno = serialNumber.split("~")[0]
        else:
            sno = serialNumber

        path = self.paths["IF_WITH_SNO_IFNAME"].format(sno, ifName)

        retry_count = 0
        while retry_count < 3:
            retry_count += 1
            resp = dcnm_send(self.module, "GET", path)

            if resp == [] or resp["RETURN_CODE"] == 200:
                break
            time.sleep(1)

        if (
            resp
            and "DATA" in resp
            and resp["DATA"]
            and resp["RETURN_CODE"] == 200
        ):
            return resp["DATA"][0]
        else:
            return []

    def dcnm_intf_get_intf_info_from_dcnm(self, intf):

        return self.dcnm_intf_get_intf_info(
            intf["ifName"], intf["serialNumber"], intf["interfaceType"]
        )

    def dcnm_intf_get_have_all_with_sno(self, sno):

        if "~" in sno:
            sno = sno.split("~")[0]
        path = self.paths["IF_DETAIL_WITH_SNO"].format(sno)
        resp = dcnm_send(self.module, "GET", path)

        if resp and "DATA" in resp and resp["DATA"]:
            self.have_all.extend(resp["DATA"])

    def dcnm_intf_get_have_all(self, sw):

        # Check if you have already got the details for this switch
        if sw in self.have_all_list:
            return

        # Check if the serial number is a combined one which will be the case for vPC interfaces.
        # If combined, then split it up and pass one of the serial numbers and not the combined one.

        if "~" in self.ip_sn[sw]:
            sno = self.ip_sn[sw].split("~")[0]
        else:
            sno = self.ip_sn[sw]

        self.have_all_list.append(sw)
        self.dcnm_intf_get_have_all_with_sno(sno)

    def dcnm_intf_get_have(self):

        if not self.want:
            return

        # We have all the requested interface config in self.want. Interfaces are grouped together based on the
        # policy string and the interface name in a single dict entry.

        for elem in self.want:
            for intf in elem["interfaces"]:
                # For each interface present here, get the information that is already available
                # in DCNM. Based on this information, we will create the required payloads to be sent
                # to the DCNM controller.

                # Fetch the information from DCNM w.r.t to the interafce that we have in self.want
                intf_payload = self.dcnm_intf_get_intf_info_from_dcnm(intf)

                if intf_payload:
                    self.have.append(intf_payload)

    def dcnm_intf_translate_elements(self, ie1, ie2):

        if sys.version_info[0] >= 3:
            # Python version 3 onwards treats unicode as strings. No special treatment is required
            e1 = ie1
            e2 = ie2
        else:
            if isinstance(
                ie1, unicode  # noqa pylint: disable=undefined-variable
            ):
                e1 = ie1.encode("utf-8")
            else:
                e1 = ie1
            if isinstance(
                ie2, unicode  # noqa pylint: disable=undefined-variable
            ):
                e2 = ie2.encode("utf-8")
            else:
                e2 = ie2

        return e1, e2

    def dcnm_intf_merge_want_and_have(self, key, wvalue, hvalue):

        comb_key = ""
        e1, e2 = self.dcnm_intf_translate_elements(wvalue, hvalue)

        if "CONF" in key:
            if e1 == "":
                comb_key = e2
            elif e2 == "":
                comb_key = e1
            else:
                comb_key = e2 + "\n" + e1
        else:
            if e1 == "":
                comb_key = e2
            elif e2 == "":
                comb_key = e1
            else:
                comb_key = e2 + "," + e1
        return comb_key

    def dcnm_intf_compare_elements(
        self, name, sno, fabric, ie1, ie2, k, state
    ):

        # unicode encoded strings must be decoded to get proper strings which is required
        # for comparison purposes

        e1, e2 = self.dcnm_intf_translate_elements(ie1, ie2)

        # The keys in key_translate represent a concatenated string. We should split
        # these strings and then compare the values
        key_translate = [
            "MEMBER_INTERFACES",
            "CONF",
            "PEER1_MEMBER_INTERFACES",
            "PEER2_MEMBER_INTERFACES",
            "PEER1_PO_CONF",
            "PEER2_PO_CONF",
        ]

        merge = False

        # Some keys have values given as a list which is encoded into a
        # string. So split that up into list and then use 'set' to process
        # the same irrespective of the order of elements
        if k in key_translate:
            # CONF, PEER1_PO_CONF and PEER2_PO_CONF has '\n' joining the commands
            # MEMBER_INTERFACES, PEER1_MEMBER_INTERFACES, and PEER2_MEMBER_INTERFACES
            # have ',' joining differnet elements. So use a multi-delimiter split
            # to split with any delim
            t_e1 = sorted(re.split(r"[\n,]", e1.strip()))
            t_e2 = sorted(re.split(r"[\n,]", e2.strip()))

            # Merging of aggregate objects (refer objects in key_translate at the top) should happen only for "merged" state.
            if state == "merged":
                merge = True
        else:
            if isinstance(e1, str):
                t_e1 = e1.lower()
            else:
                t_e1 = e1
            if isinstance(e2, str):
                t_e2 = e2.lower()
            else:
                t_e2 = e2

        if t_e1 != t_e2:

            if (state == "replaced") or (state == "overridden"):
                # Special handling is required for mode 'mpls' loopback interfaces.
                # They will contain either of the following two read_only properties.
                if k in ["DCI_ROUTING_PROTO", "DCI_ROUTING_TAG"]:
                    return "copy_and_add"

                return "add"
            elif state == "merged":
                # If the key is included in config, then use the value from want.
                # If the key is not included in config, then use the value from
                # have.

                # Match and find the corresponding PB input.

                match_pb = [
                    pb
                    for pb in self.pb_input
                    if (
                        (name.lower() == pb["ifname"].lower())
                        and (sno == pb["sno"])
                        and (fabric == pb["fabric"])
                    )
                ]

                pb_keys = list(match_pb[0].keys())
                if self.keymap[k] not in pb_keys:
                    # Copy the value from have, because for 'merged' state we
                    # should leave values that are not specified in config as is.
                    # We copy 'have' because, the validate input would have defaulted the
                    # values for non-mandatory objects.
                    return "copy_and_add"
                else:
                    if merge:
                        return "merge_and_add"
                    return "add"
        return "dont_add"

    def dcnm_intf_can_be_added(self, want):

        name = want["interfaces"][0]["ifName"]
        sno = want["interfaces"][0]["serialNumber"]
        fabric = want["interfaces"][0]["fabricName"]

        match_have = [
            have
            for have in self.have_all
            if (
                (name.lower() == have["ifName"].lower())
                and (sno == have["serialNo"])
                and (fabric == have["fabricName"])
            )
        ]
        if match_have:
            if (match_have[0]["complianceStatus"] != "In-Sync") and (
                match_have[0]["complianceStatus"] != "Pending"
            ):
                return match_have[0], True
            else:
                return match_have[0], False
        return [], True

    def dcnm_intf_compare_want_and_have(self, state):

        for want in self.want:

            delem = {}
            action = ""
            name = want["interfaces"][0]["ifName"]
            sno = want["interfaces"][0]["serialNumber"]
            fabric = want["interfaces"][0]["fabricName"]
            deploy = want["deploy"]

            intf_changed = False

            want.pop("deploy")
            match_have = [
                d
                for d in self.have
                if (
                    (name.lower() == d["interfaces"][0]["ifName"].lower())
                    and (sno == d["interfaces"][0]["serialNumber"])
                )
            ]

            if not match_have:
                changed_dict = copy.deepcopy(want)

                if (
                    (state == "merged")
                    or (state == "replaced")
                    or (state == "overridden")
                ):
                    action = "add"
            else:

                wkeys = list(want.keys())
                if "skipResourceCheck" in wkeys:
                    wkeys.remove("skipResourceCheck")
                if "interfaceType" in wkeys:
                    wkeys.remove("interfaceType")

                for d in match_have:

                    changed_dict = copy.deepcopy(want)
                    if "skipResourceCheck" in changed_dict.keys():
                        changed_dict.pop("skipResourceCheck")

                    # First check if the policies are same for want and have. If they are different, we cannot compare
                    # the profiles because each profile will have different elements. As per PRD, if policies are different
                    # we should not merge the information. For now we will assume we will overwrite the same. Don't compare
                    # rest of the structure. Overwrite with whatever is in want

                    if want["policy"] != d["policy"]:
                        action = "update"
                        continue

                    for k in wkeys:
                        if k == "interfaces":
                            if_keys = list(want[k][0].keys())
                            if_keys.remove("interfaceType")
                            changed_dict[k][0].pop("interfaceType")

                            # 'have' will not contain the fabric name object. So do not try to compare that. This
                            # is especially true for Ethernet interfaces. Since a switch can belong to only one fabric
                            # the serial number should be unique across all fabrics
                            if_keys.remove("fabricName")
                            changed_dict[k][0].pop("fabricName")
                            for ik in if_keys:
                                if ik == "nvPairs":
                                    nv_keys = list(want[k][0][ik].keys())
                                    if "SPEED" in nv_keys:
                                        # Remove 'SPEED' only if it is not included in 'have'.
                                        if (
                                            d[k][index][ik].get("SPEED", None)
                                            is None
                                        ):
                                            nv_keys.remove("SPEED")
                                    for nk in nv_keys:
                                        # HAVE may have an entry with a list # of interfaces. Check all the
                                        # interface entries for a match.  Even if one entry matches do not
                                        # add the interface
                                        for index in range(len(d[k])):
                                            res = self.dcnm_intf_compare_elements(
                                                name,
                                                sno,
                                                fabric,
                                                want[k][0][ik][nk],
                                                d[k][index][ik][nk],
                                                nk,
                                                state,
                                            )
                                            if res == "dont_add":
                                                break
                                        if res == "copy_and_add":
                                            want[k][0][ik][nk] = d[k][0][ik][
                                                nk
                                            ]
                                            continue
                                        if res == "merge_and_add":
                                            want[k][0][ik][
                                                nk
                                            ] = self.dcnm_intf_merge_want_and_have(
                                                nk,
                                                want[k][0][ik][nk],
                                                d[k][0][ik][nk],
                                            )
                                            changed_dict[k][0][ik][nk] = want[
                                                k
                                            ][0][ik][nk]
                                        if res != "dont_add":
                                            action = "update"
                                        else:
                                            # Keys and values match. Remove from changed_dict
                                            changed_dict[k][0][ik].pop(nk)
                                else:
                                    # HAVE may have an entry with a list # of interfaces. Check all the
                                    # interface entries for a match.  Even if one entry matches do not
                                    # add the interface
                                    for index in range(len(d[k])):
                                        res = self.dcnm_intf_compare_elements(
                                            name,
                                            sno,
                                            fabric,
                                            want[k][0][ik],
                                            d[k][0][ik],
                                            ik,
                                            state,
                                        )
                                        if res == "dont_add":
                                            break
                                    if res == "copy_and_add":
                                        want[k][0][ik] = d[k][0][ik]
                                        continue
                                    if res == "merge_and_add":
                                        want[k][0][
                                            ik
                                        ] = self.dcnm_intf_merge_want_and_have(
                                            ik, want[k][0][ik], d[k][0][ik]
                                        )
                                        changed_dict[k][0][ik] = want[k][0][ik]
                                    if res != "dont_add":
                                        action = "update"
                                    else:
                                        # Keys and values match. Remove from changed_dict
                                        if ik != "ifName":
                                            changed_dict[k][0].pop(ik)
                        else:
                            res = self.dcnm_intf_compare_elements(
                                name, sno, fabric, want[k], d[k], k, state
                            )

                            if res == "copy_and_add":
                                want[k] = d[k]
                                continue
                            if res == "merge_and_add":
                                want[k] = self.dcnm_intf_merge_want_and_have(
                                    k, want[k], d[k]
                                )
                                changed_dict[k] = want[k]
                            if res != "dont_add":
                                action = "update"
                            else:
                                # Keys and values match. Remove from changed_dict.
                                changed_dict.pop(k)

            if action == "add":
                self.dcnm_intf_merge_intf_info(want, self.diff_create)
                # Add the changed_dict to self.changed_dict
                self.changed_dict[0][state].append(changed_dict)
                intf_changed = True
            elif action == "update":
                # Remove the 'interfaceType' key from 'want'. It is not required for 'replace'
                if want.get("interfaceType", None) is not None:
                    want.pop("interfaceType")
                self.dcnm_intf_merge_intf_info(want, self.diff_replace)
                # Add the changed_dict to self.changed_dict
                self.changed_dict[0][state].append(changed_dict)
                intf_changed = True

            # if deploy flag is set to True, add the information so that this interface will be deployed
            if str(deploy).lower() == "true":
                # Add to diff_deploy,
                #   1. if intf_changed is True
                #   2. if intf_changed is Flase, then if 'complianceStatus is
                #      False then add to diff_deploy.
                #   3. Do not add otherwise

                if False is intf_changed:
                    match_intf, rc = self.dcnm_intf_can_be_added(want)
                else:
                    match_intf = []
                    rc = True

                if True is rc:
                    delem["serialNumber"] = sno
                    delem["ifName"] = name
                    delem["fabricName"] = self.fabric
                    self.diff_deploy.append(delem)
                    self.changed_dict[0]["deploy"].append(copy.deepcopy(delem))
                    if match_intf != []:
                        self.changed_dict[0]["debugs"].append(
                            {
                                "Name": name,
                                "SNO": sno,
                                "DeployStatus": match_intf["complianceStatus"],
                            }
                        )

    def dcnm_intf_get_diff_replaced(self):

        self.diff_create = []
        self.diff_delete = [[], [], [], [], [], [], [], []]
        self.diff_delete_deploy = [[], [], [], [], [], [], [], []]
        self.diff_deploy = []
        self.diff_replace = []

        for cfg in self.config:
            self.dcnm_intf_process_config(cfg)

        # Compare want[] and have[] and build a list of dicts containing interface information that
        # should be sent to DCNM for updation. The list can include information on interfaces which
        # are already presnt in self.have and which differ in the values for atleast one of the keys

        self.dcnm_intf_compare_want_and_have("replaced")

    def dcnm_intf_get_diff_merge(self):

        self.diff_create = []
        self.diff_delete_deploy = [[], [], [], [], [], [], [], []]
        self.diff_deploy = []
        self.diff_replace = []

        for cfg in self.config:
            self.dcnm_intf_process_config(cfg)

        # Compare want[] and have[] and build a list of dicts containing interface information that
        # should be sent to DCNM for updation. The list can include information on new interfaces or
        # information regarding interfaces which require an update i.e. if any new information is added
        # to existing information.
        # NOTE: merge_diff will be updated only if there is some new information that is not already
        #       existing. If existing information needs to be updated then use 'replace'.

        self.dcnm_intf_compare_want_and_have("merged")

    def dcnm_compare_default_payload(self, intf, have):

        if intf.get("policy") != have.get("policy"):
            return "DCNM_INTF_NOT_MATCH"

        intf_nv = intf.get("interfaces")[0].get("nvPairs")
        have_nv = have.get("interfaces")[0].get("nvPairs")

        if (
            str(intf_nv.get("SPEED")).lower()
            != str(have_nv.get("SPEED")).lower()
        ):
            return "DCNM_INTF_NOT_MATCH"
        if intf_nv.get("DESC") != have_nv.get("DESC"):
            return "DCNM_INTF_NOT_MATCH"
        if intf_nv.get("CONF") != have_nv.get("CONF"):
            return "DCNM_INTF_NOT_MATCH"
        if (
            str(intf_nv.get("ADMIN_STATE")).lower()
            != str(have_nv.get("ADMIN_STATE")).lower()
        ):
            return "DCNM_INTF_NOT_MATCH"
        if str(intf_nv.get("MTU")).lower() != str(have_nv.get("MTU")).lower():
            return "DCNM_INTF_NOT_MATCH"

        if intf.get("policy") == "int_routed_host":
            if intf_nv.get("INTF_VRF") != have_nv.get("INTF_VRF"):
                return "DCNM_INTF_NOT_MATCH"
            if (
                str(intf_nv.get("IP")).lower()
                != str(have_nv.get("IP")).lower()
            ):
                return "DCNM_INTF_NOT_MATCH"
            if (
                str(intf_nv.get("PREFIX")).lower()
                != str(have_nv.get("PREFIX")).lower()
            ):
                return "DCNM_INTF_NOT_MATCH"
            if (
                str(intf_nv.get("ROUTING_TAG")).lower()
                != str(have_nv.get("ROUTING_TAG")).lower()
            ):
                return "DCNM_INTF_NOT_MATCH"
        elif intf.get("policy") == "int_trunk_host":
            if (
                str(intf_nv.get("BPDUGUARD_ENABLED")).lower()
                != str(have_nv.get("BPDUGUARD_ENABLED")).lower()
            ):
                return "DCNM_INTF_NOT_MATCH"
            if (
                str(intf_nv.get("PORTTYPE_FAST_ENABLED")).lower()
                != str(have_nv.get("PORTTYPE_FAST_ENABLED")).lower()
            ):
                return "DCNM_INTF_NOT_MATCH"
            if (
                str(intf_nv.get("ALLOWED_VLANS")).lower()
                != str(have_nv.get("ALLOWED_VLANS")).lower()
            ):
                return "DCNM_INTF_NOT_MATCH"
        return "DCNM_INTF_MATCH"

    def dcnm_intf_get_default_eth_payload(self, ifname, sno, fabric):

        eth_payload = {
            "policy": "",
            "interfaces": [
                {
                    "interfaceType": "INTERFACE_ETHERNET",
                    "serialNumber": "",
                    "ifName": "",
                    "fabricName": "",
                    "nvPairs": {
                        "interfaceType": "INTERFACE_ETHERNET",
                        "MTU": "",
                        "SPEED": "",
                        "DESC": "",
                        "CONF": "",
                        "ADMIN_STATE": True,
                        "INTF_NAME": "",
                    },
                }
            ],
        }

        # Default payload depends on switch role. For switches with 'leaf' role the default policy must be
        # 'trunk'. For other roles it must be 'routed'.

        if self.sno_to_switch_role[sno] == "leaf":
            # default ehternet 'trunk' payload to be sent to DCNM for override case
            eth_payload["policy"] = self.pol_types[self.dcnm_version][
                "eth_trunk"
            ]
            eth_payload["interfaces"][0]["nvPairs"]["MTU"] = "jumbo"
            eth_payload["interfaces"][0]["nvPairs"]["SPEED"] = "Auto"
            eth_payload["interfaces"][0]["nvPairs"]["CONF"] = "no shutdown"
            eth_payload["interfaces"][0]["nvPairs"][
                "BPDUGUARD_ENABLED"
            ] = False
            eth_payload["interfaces"][0]["nvPairs"][
                "PORTTYPE_FAST_ENABLED"
            ] = True
            eth_payload["interfaces"][0]["nvPairs"]["ALLOWED_VLANS"] = "none"
            eth_payload["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname

            eth_payload["interfaces"][0]["ifName"] = ifname
            eth_payload["interfaces"][0]["serialNumber"] = sno
            eth_payload["interfaces"][0]["fabricName"] = fabric

        else:
            # default ehternet 'routed' payload to be sent to DCNM for override case
            eth_payload["policy"] = self.pol_types[self.dcnm_version][
                "eth_routed"
            ]
            eth_payload["interfaces"][0]["nvPairs"]["MTU"] = 9216
            eth_payload["interfaces"][0]["nvPairs"]["SPEED"] = "Auto"
            eth_payload["interfaces"][0]["nvPairs"]["CONF"] = "no shutdown"
            eth_payload["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname
            eth_payload["interfaces"][0]["nvPairs"]["INTF_VRF"] = ""
            eth_payload["interfaces"][0]["nvPairs"]["IP"] = ""
            eth_payload["interfaces"][0]["nvPairs"]["PREFIX"] = ""
            eth_payload["interfaces"][0]["nvPairs"]["ROUTING_TAG"] = ""

            eth_payload["interfaces"][0]["ifName"] = ifname
            eth_payload["interfaces"][0]["serialNumber"] = sno
            eth_payload["interfaces"][0]["fabricName"] = fabric

        return eth_payload

    def dcnm_intf_can_be_replaced(self, have):

        for item in self.pb_input:
            # For overridden state, we will not touch anything that is present in incoming config,
            # because those interfaces will anyway be modified in the current run
            if (self.module.params["state"] == "overridden") and (
                item["ifname"] == have["ifName"]
            ):
                return False, item["ifname"]
            if item.get("members"):
                if have["ifName"] in [
                    self.dcnm_intf_get_if_name(mem, "eth")[0]
                    for mem in item["members"]
                ]:
                    return False, item["ifname"]
            elif (item.get("peer1_members")) or (item.get("peer2_members")):
                if (
                    have["ifName"]
                    in [
                        self.dcnm_intf_get_if_name(mem, "eth")[0]
                        for mem in item["peer1_members"]
                    ]
                ) or (
                    have["ifName"]
                    in [
                        self.dcnm_intf_get_if_name(mem, "eth")[0]
                        for mem in item["peer2_members"]
                    ]
                ):
                    return False, item["ifname"]
        return True, None

    def dcnm_intf_process_config(self, cfg):

        processed = []

        if cfg.get("switch", None) is None:
            return
        for sw in cfg["switch"]:

            sno = self.ip_sn[sw]

            if sno not in processed:
                processed.append(sno)

                # If the switch is part of VPC pair, then a GET on any serial number will fetch details of
                # both the switches. So check before adding to have_all

                if not any(
                    d.get("serialNo", None) == self.ip_sn[sw]
                    for d in self.have_all
                ):
                    self.dcnm_intf_get_have_all(sw)

    def dcnm_intf_get_diff_overridden(self, cfg):

        deploy = False
        self.diff_create = []
        self.diff_delete = [[], [], [], [], [], [], [], []]
        self.diff_delete_deploy = [[], [], [], [], [], [], [], []]
        self.diff_deploy = []
        self.diff_replace = []

        # If no config is included, delete/default all interfaces
        if cfg == []:
            # Since there is no 'config' block, then the 'deploy' flag at top level will be
            # used to determine the deploy behaviour
            deploy = self.module.params["deploy"]
            for address in self.ip_sn.keys():
                # the given switch may be part of a VPC pair. In that case we
                # need to get interface information using one switch which returns interfaces
                # from both the switches

                if not any(
                    d.get("serialNo", None) == self.ip_sn[address]
                    for d in self.have_all
                ):
                    self.dcnm_intf_get_have_all(address)
        else:
            # compute have_all for every switch included in 'cfg'.
            # 'deploy' flag will be picked from 'cfg' in case of state 'deleted' and from
            # top level in case of state 'overridden'

            if self.module.params["state"] == "overridden":
                deploy = self.module.params["deploy"]
            if self.module.params["state"] == "deleted":
                # NOTE: in case of state 'deleted' 'cfg' will have a single entry only.
                deploy = cfg[0].get("deploy")
            for config in cfg:
                self.dcnm_intf_process_config(config)

        del_list = []
        defer_list = []

        for have in self.have_all:

            delem = {}
            name = have["ifName"]
            sno = have["serialNo"]
            fabric = have["fabricName"]

            # Check if this interface type is to be overridden.
            if self.module.params["override_intf_types"] != []:
                # Check if it is SUBINTERFACE. For sub-interfaces ifType will be retuened as INTERFACE_ETHERNET. So
                # for such interfaces, check if SUBINTERFACE is included in override list instead of have['ifType']
                if (have["ifType"] == "INTERFACE_ETHERNET") and (
                    (str(have["isPhysical"]).lower() == "none")
                    or (str(have["isPhysical"]).lower() == "false")
                ):
                    # This is a SUBINTERFACE.
                    if (
                        "SUBINTERFACE"
                        not in self.module.params["override_intf_types"]
                    ):
                        continue
                else:
                    if (
                        have["ifType"]
                        not in self.module.params["override_intf_types"]
                    ):
                        continue

            if (have["ifType"] == "INTERFACE_ETHERNET") and (
                (str(have["isPhysical"]).lower() != "none")
                and (str(have["isPhysical"]).lower() == "true")
            ):

                if have["alias"] != "" and have["deleteReason"] is not None:
                    self.changed_dict[0]["skipped"].append(
                        {
                            "Name": name,
                            "Alias": have["alias"],
                            "Delete Reason": have["deleteReason"],
                        }
                    )
                    continue

                if str(have["deletable"]).lower() == "false":
                    # Add this 'have to a deferred list. We will process this list once we have processed all the 'haves'
                    defer_list.append(have)
                    self.changed_dict[0]["deferred"].append(
                        {
                            "Name": name,
                            "Deletable": have["deletable"],
                            "Underlay Policies": have["underlayPolicies"],
                        }
                    )
                    continue

                uelem = self.dcnm_intf_get_default_eth_payload(
                    name, sno, fabric
                )
                # Before we add the interface to replace list, check if the default payload is same as
                # what is already present. If both are same, skip the interface.
                # So during idempotence, we may add the same interface again if we don't compare

                intf = self.dcnm_intf_get_intf_info(
                    have["ifName"], have["serialNo"], have["ifType"]
                )
                if intf == []:
                    # In case of LANClassic fabrics, a GET on policy details for Ethernet interfaces will return [] since
                    # these interfaces dont have any policies configured by default. In that case there is nothing to be done
                    continue

                if (
                    self.dcnm_compare_default_payload(uelem, intf)
                    == "DCNM_INTF_MATCH"
                ):
                    continue

                if uelem is not None:
                    # Before defaulting ethernet interfaces, check if they are
                    # member of any port-channel. If so, do not default that
                    rc, intf = self.dcnm_intf_can_be_replaced(have)
                    if rc is True:
                        self.dcnm_intf_merge_intf_info(
                            uelem, self.diff_replace
                        )
                        self.changed_dict[0]["replaced"].append(
                            copy.deepcopy(uelem)
                        )
                        delem["serialNumber"] = sno
                        delem["ifName"] = name
                        delem["fabricName"] = self.fabric
                        if str(deploy).lower() == "true":
                            self.diff_deploy.append(delem)
                            self.changed_dict[0]["deploy"].append(
                                copy.deepcopy(delem)
                            )
            # Sub-interafces are returned as INTERFACE_ETHERNET in have_all. So do an
            # additional check to see if it is physical. If not assume it to be sub-interface
            # for now. We will have to re-visit this check if there are additional non-physical
            # interfaces which have the same ETHERNET interafce type. For e.g., FEX ports

            if (
                (have["ifType"] == "INTERFACE_PORT_CHANNEL")
                or (have["ifType"] == "INTERFACE_LOOPBACK")
                or (have["ifType"] == "SUBINTERFACE")
                or (have["ifType"] == "INTERFACE_VPC")
                or (have["ifType"] == "INTERFACE_VLAN")
                or (have["ifType"] == "STRAIGHT_TROUGH_FEX")
                or (have["ifType"] == "AA_FEX")
                or (
                    (have["ifType"] == "INTERFACE_ETHERNET")
                    and (
                        (str(have["isPhysical"]).lower() == "none")
                        or (str(have["isPhysical"]).lower() == "false")
                    )
                )
            ):
                # Certain interfaces cannot be deleted, so check before deleting. But if the interface has been marked for delete,
                # we still go in and check if need to deploy.
                if (
                    str(have["deletable"]).lower() == "true"
                    or str(have["markDeleted"]).lower() == "true"
                ):
                    # Port-channel which are created as part of VPC peer link should not be deleted
                    if have["ifType"] == "INTERFACE_PORT_CHANNEL":
                        if (
                            have["alias"] is not None
                            and "vpc-peer-link" in have["alias"]
                        ):
                            self.changed_dict[0]["skipped"].append(
                                {
                                    "Name": name,
                                    "Alias": have["alias"],
                                    "Underlay Policies": have[
                                        "underlayPolicies"
                                    ],
                                }
                            )
                            continue
                        else:
                            self.changed_dict[0]["debugs"].append(
                                {
                                    "Name": name,
                                    "Alias": have["alias"],
                                    "Underlay Policies": have[
                                        "underlayPolicies"
                                    ],
                                }
                            )

                    # Interfaces sometimes take time to get deleted from DCNM. Such interfaces will have
                    # underlayPolicies set to "None". Such interfaces need not be deleted again

                    if have["underlayPolicies"] is None:
                        self.changed_dict[0]["skipped"].append(
                            {
                                "Name": name,
                                "Alias": have["alias"],
                                "Underlay Policies": have["underlayPolicies"],
                            }
                        )
                        continue

                    # For interfaces that are matching, leave them alone. We will overwrite the config anyway
                    # For all other interfaces, if they are PC, vPC, SUBINT, LOOPBACK, delete them.

                    # Check if this interface is present in want. If yes, ignore the interface, because all
                    # configuration from want will be added to create anyway

                    match_want = [
                        d
                        for d in self.want
                        if (
                            (
                                name.lower()
                                == d["interfaces"][0]["ifName"].lower()
                            )
                            and (sno == d["interfaces"][0]["serialNumber"])
                            and (fabric == d["interfaces"][0]["fabricName"])
                        )
                    ]
                    if not match_want:

                        delem = {}

                        delem["interfaceDbId"] = 0
                        delem["interfaceType"] = have["ifType"]
                        delem["ifName"] = name
                        delem["serialNumber"] = sno
                        delem["fabricName"] = fabric

                        # have_all will include interfaces which are marked for DELETE too. Do not delete them again.
                        if str(have["markDeleted"]).lower() == "false":
                            self.diff_delete[
                                self.int_index[have["ifType"]]
                            ].append(delem)
                            self.changed_dict[0]["deleted"].append(
                                copy.deepcopy(delem)
                            )
                            del_list.append(have)

                        if str(deploy).lower() == "true":
                            if (have["complianceStatus"] == "In-Sync") or (
                                have["complianceStatus"] == "Pending"
                            ):
                                self.diff_delete_deploy[
                                    self.int_index[have["ifType"]]
                                ].append(delem)
                                self.changed_dict[0]["delete_deploy"].append(
                                    copy.deepcopy(delem)
                                )

        for intf in defer_list:
            # Check if the 'source' for the ethernet interface is one of the interfaces that is already deleted.
            # If so you can default/reset this ethernet interface also

            delem = {}
            sno = intf["serialNo"]
            fabric = intf["fabricName"]
            name = intf["underlayPolicies"][0]["source"]

            match = [
                d
                for d in del_list
                if (
                    (name.lower() == d["ifName"].lower())
                    and (sno in d["serialNo"])
                    and (fabric == d["fabricName"])
                )
            ]
            if match:

                uelem = self.dcnm_intf_get_default_eth_payload(
                    intf["ifName"], sno, fabric
                )

                self.dcnm_intf_merge_intf_info(uelem, self.diff_replace)
                self.changed_dict[0]["replaced"].append(copy.deepcopy(uelem))
                delem["serialNumber"] = sno
                delem["ifName"] = intf["ifName"]
                delem["fabricName"] = self.fabric

                # Deploy only if requested for
                if str(deploy).lower() == "true":
                    self.diff_deploy.append(delem)
                    self.changed_dict[0]["deploy"].append(copy.deepcopy(delem))

        self.dcnm_intf_compare_want_and_have("overridden")

    def dcnm_intf_get_diff_deleted(self):

        self.diff_create = []
        self.diff_delete = [[], [], [], [], [], [], [], []]
        self.diff_delete_deploy = [[], [], [], [], [], [], [], []]
        self.diff_deploy = []
        self.diff_replace = []

        if self.config == []:
            # Now that we have all the interface information we can run override
            # and delete or reset interfaces.
            self.dcnm_intf_get_diff_overridden(self.config)
        elif self.config:
            for cfg in self.config:
                if cfg.get("name", None) is not None:
                    processed = []
                    have_all = []

                    # If interface name alone is given, then delete or reset the
                    # interface on all switches in the fabric
                    switches = cfg.get("switch", None)

                    if switches is None:
                        switches = self.ip_sn.keys()
                    else:
                        switches = cfg["switch"]

                    for sw in switches:

                        intf = {}
                        delem = {}

                        if_name, if_type = self.dcnm_extract_if_name(cfg)

                        # Check if the interface is present in DCNM
                        intf["interfaceType"] = if_type
                        if if_type == "INTERFACE_VPC":
                            intf["serialNumber"] = self.vpc_ip_sn[sw]
                        else:
                            intf["serialNumber"] = self.ip_sn[sw]
                        intf["ifName"] = if_name

                        if intf["serialNumber"] not in processed:
                            processed.append(intf["serialNumber"])
                        else:
                            continue

                        # Ethernet interfaces cannot be deleted
                        if if_type == "INTERFACE_ETHERNET":

                            if sw not in have_all:
                                have_all.append(sw)
                                self.dcnm_intf_get_have_all(sw)

                            # Get the matching interface from have_all
                            match_have = [
                                have
                                for have in self.have_all
                                if (
                                    (
                                        intf["ifName"].lower()
                                        == have["ifName"].lower()
                                    )
                                    and (
                                        intf["serialNumber"]
                                        == have["serialNo"]
                                    )
                                )
                            ][0]
                            if (
                                match_have
                                and (
                                    str(match_have["isPhysical"]).lower()
                                    != "none"
                                )
                                and (
                                    str(match_have["isPhysical"]).lower()
                                    == "true"
                                )
                            ):

                                if (
                                    str(match_have["deletable"]).lower()
                                    == "false"
                                ):
                                    continue

                                uelem = self.dcnm_intf_get_default_eth_payload(
                                    intf["ifName"],
                                    intf["serialNumber"],
                                    self.fabric,
                                )
                                intf_payload = self.dcnm_intf_get_intf_info_from_dcnm(
                                    intf
                                )

                                # Before we add the interface to replace list, check if the default payload is same as
                                # what is already present. If both are same, skip the interface. This is required specifically
                                # for ethernet interfaces because they don't actually get deleted. they will only be defaulted.
                                # So during idempotence, we may add the same interface again if we don't compare
                                if intf_payload != []:
                                    if (
                                        self.dcnm_compare_default_payload(
                                            uelem, intf_payload
                                        )
                                        == "DCNM_INTF_MATCH"
                                    ):
                                        continue

                                if uelem is not None:
                                    # Before defaulting ethernet interfaces, check if they are
                                    # member of any port-channel. If so, do not default that
                                    rc, iface = self.dcnm_intf_can_be_replaced(
                                        match_have
                                    )
                                    if rc is True:
                                        self.dcnm_intf_merge_intf_info(
                                            uelem, self.diff_replace
                                        )
                                        self.changed_dict[0][
                                            "replaced"
                                        ].append(copy.deepcopy(uelem))
                                        if (
                                            str(
                                                cfg.get("deploy", "true")
                                            ).lower()
                                            == "true"
                                        ):
                                            delem["serialNumber"] = intf[
                                                "serialNumber"
                                            ]
                                            delem["ifName"] = if_name
                                            delem["fabricName"] = self.fabric
                                            self.diff_deploy.append(delem)
                        else:
                            intf_payload = self.dcnm_intf_get_intf_info_from_dcnm(
                                intf
                            )

                            if intf_payload != []:
                                delem["ifName"] = if_name
                                delem["serialNumber"] = intf["serialNumber"]

                                self.diff_delete[
                                    self.int_index[if_type]
                                ].append(delem)
                                self.changed_dict[0]["deleted"].append(
                                    copy.deepcopy(delem)
                                )

                                if "monitor" not in intf_payload["policy"]:
                                    if (
                                        str(cfg.get("deploy", "true")).lower()
                                        == "true"
                                    ):
                                        self.diff_delete_deploy[
                                            self.int_index[if_type]
                                        ].append(delem)
                                        self.changed_dict[0][
                                            "delete_deploy"
                                        ].append(copy.deepcopy(delem))
                            else:
                                # Get Interface details which will include even interfaces that are marked for delete.
                                if sw not in have_all:
                                    have_all.append(sw)
                                    self.dcnm_intf_get_have_all(sw)

                                # Get the matching interface from have_all
                                match_have = [
                                    have
                                    for have in self.have_all
                                    if (
                                        (
                                            intf["ifName"].lower()
                                            == have["ifName"].lower()
                                        )
                                        and (
                                            intf["serialNumber"]
                                            == have["serialNo"]
                                        )
                                    )
                                ]

                                if match_have:
                                    # Matching interface found. Check 'complianceStatus' and deploy if necessary
                                    if (
                                        match_have[0]["complianceStatus"]
                                        == "In-Sync"
                                    ) or (
                                        match_have[0]["complianceStatus"]
                                        == "Pending"
                                    ):
                                        if (
                                            str(
                                                cfg.get("deploy", "true")
                                            ).lower()
                                            == "true"
                                        ):
                                            delem["ifName"] = if_name
                                            delem["serialNumber"] = intf[
                                                "serialNumber"
                                            ]
                                            self.diff_delete_deploy[
                                                self.int_index[if_type]
                                            ].append(delem)
                                            self.changed_dict[0][
                                                "delete_deploy"
                                            ].append(copy.deepcopy(delem))
                else:
                    self.dcnm_intf_get_diff_overridden([cfg])

    def dcnm_extract_if_name(self, cfg):

        if cfg["name"][0:2].lower() == "po":
            if_name, port_id = self.dcnm_intf_get_if_name(cfg["name"], "pc")
            if_type = "INTERFACE_PORT_CHANNEL"
        elif cfg["name"][0:2].lower() == "lo":
            if_name, port_id = self.dcnm_intf_get_if_name(cfg["name"], "lo")
            if_type = "INTERFACE_LOOPBACK"
        elif cfg["name"][0:3].lower() == "eth":
            if "." not in cfg["name"]:
                if_name, port_id = self.dcnm_intf_get_if_name(
                    cfg["name"], "eth"
                )
                if_type = "INTERFACE_ETHERNET"
            else:
                if_name, port_id = self.dcnm_intf_get_if_name(
                    cfg["name"], "sub_int"
                )
                if_type = "SUBINTERFACE"
        elif cfg["name"][0:3].lower() == "vpc":
            if_name, port_id = self.dcnm_intf_get_if_name(cfg["name"], "vpc")
            if_type = "INTERFACE_VPC"
        elif cfg["name"][0:4].lower() == "vlan":
            if_name, port_id = self.dcnm_intf_get_if_name(cfg["name"], "svi")
            if_type = "INTERFACE_VLAN"
        else:
            if_name = ""
            if_type = ""
        return if_name, if_type

    def dcnm_intf_get_diff_query(self):

        for info in self.intf_info:
            sno = self.ip_sn[info["switch"][0]]
            if info["name"] == "":
                # GET all interfaces
                path = self.paths["IF_DETAIL_WITH_SNO"].format(sno)
            else:
                ifname, if_type = self.dcnm_extract_if_name(info)
                # GET a specific interface
                path = self.paths["IF_WITH_SNO_IFNAME"].format(sno, ifname)

            resp = dcnm_send(self.module, "GET", path)

            if "DATA" in resp and resp["DATA"]:
                self.diff_query.extend(resp["DATA"])
        self.changed_dict[0]["query"].extend(self.diff_query)
        self.result["response"].extend(self.diff_query)

    def dcnm_parse_response(self, resp):

        failed = False

        succ_resp = {
            "DATA": {},
            "MESSAGE": "OK",
            "METHOD": "POST",
            "REQUEST_PATH": "",
            "RETURN_CODE": 200,
        }

        # Get a list of entities from the deploy. We will have to check
        # all the responses before we declare changed as True or False

        entities = self.dcnm_intf_get_entities_list(self.diff_deploy)

        ent_resp = {}
        for ent in entities:

            ent_resp[ent] = "No Error"
            if isinstance(resp["DATA"], list):
                for data in resp["DATA"]:
                    host = data.get("entity")

                    if host:
                        host = host.split(":")[0]
                        if self.hn_sn.get(host) == ent:
                            ent_resp[ent] = data.get("message")
                    else:
                        ent_resp[ent] = "No Error"
            elif isinstance(resp["DATA"], str):
                ent_resp[ent] = resp["DATA"]

        succ_resp["ORIG_MSG"] = []
        for ent in entities:
            if ent_resp[ent] == "No Error":
                continue
            elif (
                ("No Commands to execute" in ent_resp[ent])
                or (ent_resp[ent] == "Failed to fetch policies")
                or (ent_resp[ent] == "Failed to fetch switch configuration")
                or (ent_resp[ent] == "In-Sync")
            ):
                # Consider this case as success.
                succ_resp["REQUEST_PATH"] = resp["REQUEST_PATH"]
                succ_resp["MESSAGE"] = "OK"
                succ_resp["METHOD"] = resp["METHOD"]
                succ_resp["ORIG_MSG"].append(ent_resp[ent])
                succ_resp["RETURN_CODE"] = 200
            else:
                failed = True
                break

        if failed:
            return resp, False
        else:
            return succ_resp, False

    def dcnm_intf_send_message_handle_retry(self, action, path, payload, cmd):

        count = 1
        while count < 20:

            resp = dcnm_send(self.module, action, path, payload)

            # No commands to execute is normal when you try to deploy/delete an
            # interface to switch and there is no change.
            # Consider that as success and mark the change flag as 'False; to indicate
            # nothinbg actually changed

            if (resp.get("MESSAGE") == "OK") and (
                resp.get("RETURN_CODE") == 200
            ):
                return resp, True

            presp, changed = self.dcnm_parse_response(resp)
            resp = presp

            count = count + 1
            time.sleep(0.1)

        return resp, False

    def dcnm_intf_get_entities_list(self, deploy):

        sn_list = []
        usno = []

        [
            [sn_list.append(v) for k, v in d.items() if k == "serialNumber"]
            for d in deploy
        ]

        # For vPC cases, serial numbers will be a combined one. But deploy responses from the DCNM
        # controller will be based on individual switches. So we will have to split up the serial
        # numbers into individual serial numbers and add to the list

        ulist = set(sn_list)

        vpc = False
        for num in ulist:
            if "~" in num:
                vpc = True
                slist = num.split("~")
                usno.append(slist[0])
                usno.append(slist[1])

        if vpc is True:
            ulist = usno
        return ulist

    def dcnm_intf_check_deployment_status(self, deploy_list):

        # Check for deployment status of all the configured objects only if the check_deploy flag is set.
        if self.module.params["check_deploy"] is False:
            return

        path = self.paths["GLOBAL_IF_DEPLOY"]

        resp = {}

        for item in deploy_list:
            retries = 0
            while retries < 60:
                retries += 1
                name = item["ifName"]
                sno = item["serialNumber"]

                match_have = [
                    have
                    for have in self.have_all
                    if (
                        (name.lower() == have["ifName"].lower())
                        and (sno == have["serialNo"])
                        and (self.fabric == have["fabricName"])
                    )
                ]
                if match_have:

                    if match_have[0]["complianceStatus"] == "In-Sync":
                        break

                    if retries == 10 or retries == 20:
                        json_payload = json.dumps(
                            {
                                "ifName": name,
                                "serialNumber": sno,
                                "fabricName": self.fabric,
                            }
                        )
                        resp = dcnm_send(
                            self.module, "POST", path, json_payload
                        )

                    time.sleep(5)
                    self.have_all = []
                    self.dcnm_intf_get_have_all_with_sno(sno)
                else:
                    # For merge state, the interfaces would have been created just now. Fetch them again before checking
                    self.have_all = []
                    self.dcnm_intf_get_have_all_with_sno(sno)
            if (
                match_have == []
                or match_have[0]["complianceStatus"] != "In-Sync"
            ):
                self.module.fail_json(
                    msg={
                        "FAILURE REASON": "Interafce "
                        + name
                        + " did not reach 'In-Sync' State",
                        "Compliance Status": match_have[0]["complianceStatus"],
                        # "CHANGED": self.changed_dict,
                        # "RESP": resp
                        "RESULT": self.result,
                    }
                )

    def dcnm_intf_send_message_to_dcnm(self):

        resp = None
        changed = False

        delete = False
        delete_deploy = False
        create = False
        deploy = False
        replace = False

        path = self.paths["IF_MARK_DELETE"]

        # First send deletes and then try create and update. This is because during override, the overriding
        # config may conflict with existing configuration.

        for delem in self.diff_delete:

            if delem == []:
                continue

            json_payload = json.dumps(delem)

            resp = dcnm_send(self.module, "DELETE", path, json_payload)

            if resp.get("RETURN_CODE") != 200:
                if resp["DATA"]:
                    delete_failed = False
                else:
                    delete_failed = True
                for item in resp["DATA"]:
                    if "No Commands to execute" not in item["message"]:
                        delete_failed = True
                if delete_failed is False:
                    resp["RETURN_CODE"] = 200
                    resp["MESSAGE"] = "OK"

            if (resp.get("MESSAGE") != "OK") or (
                resp.get("RETURN_CODE") != 200
            ):

                # there may be cases which are not actual failures. retry the
                # action
                resp, rc = self.dcnm_intf_send_message_handle_retry(
                    "DELETE", path, json_payload, "DELETE"
                )

                # Even if one of the elements succeed, changed must be set to
                # True. Once changed becomes True, then it remains True
                if False is changed:
                    changed = rc

                if (
                    (resp.get("MESSAGE") != "OK")
                    and ("No Commands to execute" not in resp.get("MESSAGE"))
                ) or (resp.get("RETURN_CODE") != 200):
                    resp["CHANGED"] = self.changed_dict
                    self.module.fail_json(msg=resp)
            else:
                changed = True

            delete = changed
            self.result["response"].append(resp)

        resp = None

        path = self.paths["GLOBAL_IF_DEPLOY"]
        index = -1
        for delem in self.diff_delete_deploy:

            # index = index + 1
            if delem == []:
                continue

            json_payload = json.dumps(delem)

            resp = dcnm_send(self.module, "POST", path, json_payload)

            if resp.get("RETURN_CODE") != 200:
                if resp["DATA"]:
                    deploy_failed = False
                else:
                    deploy_failed = True
                for item in resp["DATA"]:
                    if (
                        "No Commands to execute" not in item["message"]
                        and "In-Sync" not in item["message"]
                    ):
                        deploy_failed = True
                if deploy_failed is False:
                    resp["RETURN_CODE"] = 200
                    resp["MESSAGE"] = "OK"
                    delete_deploy = True
            else:
                delete_deploy = True
            self.result["response"].append(resp)

        resp = None

        path = self.paths["INTERFACE"]
        for payload in self.diff_replace:

            json_payload = json.dumps(payload)
            resp = dcnm_send(self.module, "PUT", path, json_payload)

            self.result["response"].append(resp)

            if (resp.get("MESSAGE") != "OK") or (
                resp.get("RETURN_CODE") != 200
            ):
                resp["CHANGED"] = self.changed_dict
                self.module.fail_json(msg=resp)
            else:
                replace = True

        resp = None

        path = self.paths["GLOBAL_IF"]
        for payload in self.diff_create:

            json_payload = json.dumps(payload)
            resp = dcnm_send(self.module, "POST", path, json_payload)

            self.result["response"].append(resp)

            if (resp.get("MESSAGE") != "OK") or (
                resp.get("RETURN_CODE") != 200
            ):
                resp["CHANGED"] = self.changed_dict
                self.module.fail_json(msg=resp)
            else:
                create = True

        resp = None

        path = self.paths["GLOBAL_IF_DEPLOY"]
        if self.diff_deploy:

            json_payload = json.dumps(self.diff_deploy)

            resp = dcnm_send(self.module, "POST", path, json_payload)

            if (resp.get("MESSAGE") != "OK") and (
                resp.get("RETURN_CODE") != 200
            ):
                resp, rc = self.dcnm_parse_response(resp)
                changed = rc
            else:
                changed = True

            deploy = changed

            self.result["response"].append(resp)

            # Continue further only if original deploy is success. Fail otherwise
            if (resp.get("MESSAGE") != "OK") and (
                resp.get("RETURN_CODE") != 200
            ):
                resp["CHANGED"] = self.changed_dict
                self.module.fail_json(msg=resp)

        resp = None

        if self.diff_deploy:
            # Do a second deploy. Sometimes even if interfaces are created, they are
            # not being deployed. A second deploy solves the same. Don't worry about
            # the return values

            resp = dcnm_send(self.module, "POST", path, json_payload)

            resp = None

        if self.diff_deploy:
            self.dcnm_intf_check_deployment_status(self.diff_deploy)

        # In overridden and deleted states, if no delete or create is happening and we have
        # only replace, then check the return message for deploy. If it says
        # "No Commands to execute", then the interfaces we are replacing are
        # already in the required state and so consider that a no change
        if (self.module.params["state"] == "overridden") or (
            self.module.params["state"] == "deleted"
        ):
            self.result["changed"] = (
                delete or create or replace or deploy or delete_deploy
            )
        else:
            if delete or create or replace or deploy or delete_deploy:
                self.result["changed"] = True
            else:
                self.result["changed"] = False

    def dcnm_intf_get_xlated_object(self, cfg, key):

        """
        Routine to translate individual vlans like 45, 55 to 44-44 and 55-55 format

        Parameters:
            cfg (dict): Config element that includes the object idebtified by key to be translated
            key (str): key identifying the object to be translated

        Returns:
            translated object
        """

        citems = cfg["profile"][key].split(",")

        for index in range(len(citems)):
            if (
                (citems[index].lower() == "none")
                or (citems[index].lower() == "all")
                or ("-" in citems[index])
            ):
                continue

            # Playbook config includes individual vlans in allowed_vlans object. Convert the elem to
            # appropriate format i.e. vlaues in the form of 4, 7 to 4-4 and 7-7
            citems[index] = citems[index].strip() + "-" + citems[index].strip()
        return citems

    def dcnm_intf_translate_allowed_vlans(self, cfg):

        """
        Routine to translate xxx_allowed_vlans object in the config. 'xxx_allowed_vlans' object will
        allow only 'none', 'all', or 'vlan-ranges like 1-5' values. It does not allow individual
        vlans to be included. To enable user to include individual vlans in the playbook config, this
        routine tranlates the individual vlans like 3, 5 etc to 3-3 and 5-5 format.

        Parameters:
            cfg (dict): Config element that needs to be translated

        Returns:
            None
        """

        if cfg.get("profile", None) is None:
            return

        if cfg["profile"].get("allowed_vlans", None) is not None:
            xlated_obj = self.dcnm_intf_get_xlated_object(cfg, "allowed_vlans")
            cfg["profile"]["allowed_vlans"] = ",".join(xlated_obj)
        if cfg["profile"].get("peer1_allowed_vlans", None) is not None:
            xlated_obj = self.dcnm_intf_get_xlated_object(
                cfg, "peer1_allowed_vlans"
            )
            cfg["profile"]["peer1_allowed_vlans"] = ",".join(xlated_obj)
        if cfg["profile"].get("peer2_allowed_vlans", None) is not None:
            xlated_obj = self.dcnm_intf_get_xlated_object(
                cfg, "peer2_allowed_vlans"
            )
            cfg["profile"]["peer2_allowed_vlans"] = ",".join(xlated_obj)

    def dcnm_intf_update_inventory_data(self):

        """
        Routine to update inventory data for all fabrics included in the playbook. This routine
        also updates ip_sn, sn_hn and hn_sn objetcs from the updated inventory data.

        Parameters:
            None

        Returns:
            None
        """

        inv_data = get_fabric_inventory_details(self.module, self.fabric)

        self.inventory_data.update(inv_data)

        if self.module.params["state"] != "query":

            # Get all switches which are managable. Changes must be avoided to all switches which are not part of this list
            managable_ip = [
                (key, self.inventory_data[key]["serialNumber"])
                for key in self.inventory_data
                if str(self.inventory_data[key]["managable"]).lower() == "true"
            ]
            managable_hosts = [
                (
                    self.inventory_data[key]["logicalName"],
                    self.inventory_data[key]["serialNumber"],
                )
                for key in self.inventory_data
                if str(self.inventory_data[key]["managable"]).lower() == "true"
            ]

            managable = dict(managable_ip + managable_hosts)

            # Build a mapping of serial numbers to switch roles. This will be required to build default ethernet
            # payload during overridden state. for switch role leaf the default policy for ethernet interface must
            # be 'trunk' and for other roles it must be 'routed'.
            self.sno_to_switch_role = {}
            for key in self.inventory_data:
                self.sno_to_switch_role.update(
                    {
                        self.inventory_data[key][
                            "serialNumber"
                        ]: self.inventory_data[key]["switchRole"]
                    }
                )

            # Get all switches which are managable. Deploy must be avoided to all switches which are not part of this list
            ronly_sw_list = []
            for cfg in self.config:
                # Check if there are any switches which are not managable in the config.
                if cfg.get("switch", None) is not None:
                    for sw in cfg["switch"]:
                        if sw not in managable:
                            if sw not in ronly_sw_list:
                                ronly_sw_list.append(sw)

            # Deploy must be avoided to fabrics which are in monitoring mode
            path = self.paths["FABRIC_ACCESS_MODE"].format(self.fabric)
            resp = dcnm_send(self.module, "GET", path)

            if resp and resp["RETURN_CODE"] == 200:
                if str(resp["DATA"]["readonly"]).lower() == "true":
                    self.monitoring.append(self.fabric)

            # Check if source fabric is in monitoring mode. If so return an error, since fabrics in monitoring mode do not allow
            # create/modify/delete and deploy operations.
            if self.fabric in self.monitoring:
                self.module.fail_json(
                    msg="Error: Source Fabric '{0}' is in Monitoring mode, No changes are allowed on the fabric\n".format(
                        self.fabric
                    )
                )

        # Based on the updated inventory_data, update ip_sn, hn_sn and sn_hn objects
        self.ip_sn, self.hn_sn = get_ip_sn_dict(self.inventory_data)

    def dcnm_translate_playbook_info(self, config, ip_sn, hn_sn):

        # Transalte override_intf_types to proper types that can be directly used in overridden state.

        for if_type in self.module.params["override_intf_types"][:]:
            self.module.params["override_intf_types"].append(
                self.int_types[if_type]
            )
            self.module.params["override_intf_types"].remove(if_type)
        for cfg in config:
            index = 0
            if cfg.get("switch", None) is None:
                continue
            for sw_elem in cfg["switch"][:]:
                if sw_elem in self.ip_sn or sw_elem in self.hn_sn:
                    addr_info = dcnm_get_ip_addr_info(
                        self.module, sw_elem, ip_sn, hn_sn
                    )
                    cfg["switch"][index] = addr_info

                    # Check if the VPC serial number information is already present. If not fetch that
                    if self.vpc_ip_sn.get(addr_info, None) is None:
                        sno = self.dcnm_intf_get_vpc_serial_number(addr_info)
                        if "~" in sno:
                            # This switch is part of VPC pair. Populate the VPC serial number DB
                            self.vpc_ip_sn[addr_info] = sno
                else:
                    cfg["switch"].remove(sw_elem)
                index = index + 1

            # 'allowed-vlans' in the case of trunk interfaces accepts 'all', 'none' and 'vlan-ranges' which
            # will be of the form 20-30 etc. There is not way to include individual vlans which are not contiguous.
            # To include individual vlans like 3,6,20 etc. user must input them in the form 3-3, 6-6, 20-20 which is
            # not very intuitive. To handle this scenario, we allow playbooks to include individual vlans and translate
            # them here appropriately.

            if cfg.get("profile", None) is not None:
                if (
                    (
                        cfg["profile"].get("peer1_allowed_vlans", None)
                        is not None
                    )
                    or (
                        cfg["profile"].get("peer2_allowed_vlans", None)
                        is not None
                    )
                    or (cfg["profile"].get("allowed_vlans", None) is not None)
                ):
                    self.dcnm_intf_translate_allowed_vlans(cfg)


def main():

    """main entry point for module execution"""
    element_spec = dict(
        fabric=dict(required=True, type="str"),
        config=dict(required=False, type="list", elements="dict", default=[]),
        deploy=dict(required=False, type="bool", default=True),
        state=dict(
            type="str",
            default="merged",
            choices=["merged", "replaced", "overridden", "deleted", "query"],
        ),
        override_intf_types=dict(
            required=False,
            type="list",
            elements="str",
            choices=[
                "pc",
                "vpc",
                "sub_int",
                "lo",
                "eth",
                "svi",
                "st_fex",
                "aa_fex",
            ],
            default=[],
        ),
        check_deploy=dict(type="bool", default=False),
    )

    module = AnsibleModule(
        argument_spec=element_spec, supports_check_mode=True
    )

    dcnm_intf = DcnmIntf(module)

    state = module.params["state"]
    if not dcnm_intf.config:
        if state == "merged" or state == "replaced" or state == "query":
            module.fail_json(
                msg="'config' element is mandatory for state '{0}', given = '{1}'".format(
                    state, dcnm_intf.config
                )
            )

    dcnm_intf.dcnm_intf_update_inventory_data()

    if not dcnm_intf.ip_sn:
        dcnm_intf.result[
            "msg"
        ] = "Fabric {0} missing on DCNM or does not have any switches".format(
            dcnm_intf.fabric
        )
        module.fail_json(
            msg="Fabric {0} missing on DCNM or does not have any switches".format(
                dcnm_intf.fabric
            )
        )

    dcnm_intf.dcnm_translate_playbook_info(
        dcnm_intf.config, dcnm_intf.ip_sn, dcnm_intf.hn_sn
    )

    dcnm_intf.dcnm_intf_copy_config()

    dcnm_intf.dcnm_intf_validate_input()

    # state 'deleted' may not include all the information
    if (module.params["state"] != "query") and (
        module.params["state"] != "deleted"
    ):
        dcnm_intf.dcnm_intf_get_want()
        dcnm_intf.dcnm_intf_get_have()

    if module.params["state"] == "merged":
        dcnm_intf.dcnm_intf_get_diff_merge()

    if module.params["state"] == "replaced":
        dcnm_intf.dcnm_intf_get_diff_replaced()

    if module.params["state"] == "overridden":
        dcnm_intf.dcnm_intf_get_diff_overridden(dcnm_intf.config)

    if module.params["state"] == "deleted":
        dcnm_intf.dcnm_intf_get_diff_deleted()

    if module.params["state"] == "query":
        dcnm_intf.dcnm_intf_get_diff_query()

    dcnm_intf.result["diff"] = dcnm_intf.changed_dict

    if (
        dcnm_intf.diff_create
        or dcnm_intf.diff_replace
        or dcnm_intf.diff_deploy
        or dcnm_intf.diff_delete[dcnm_intf.int_index["INTERFACE_PORT_CHANNEL"]]
        or dcnm_intf.diff_delete[dcnm_intf.int_index["INTERFACE_VPC"]]
        or dcnm_intf.diff_delete[dcnm_intf.int_index["INTERFACE_ETHERNET"]]
        or dcnm_intf.diff_delete[dcnm_intf.int_index["SUBINTERFACE"]]
        or dcnm_intf.diff_delete[dcnm_intf.int_index["INTERFACE_LOOPBACK"]]
        or dcnm_intf.diff_delete[dcnm_intf.int_index["INTERFACE_VLAN"]]
        or dcnm_intf.diff_delete[dcnm_intf.int_index["STRAIGHT_TROUGH_FEX"]]
        or dcnm_intf.diff_delete[dcnm_intf.int_index["AA_FEX"]]
        or dcnm_intf.diff_delete_deploy
    ):
        dcnm_intf.result["changed"] = True
    else:
        module.exit_json(**dcnm_intf.result)

    if module.check_mode:
        dcnm_intf.result["changed"] = False
        module.exit_json(**dcnm_intf.result)

    dcnm_intf.dcnm_intf_send_message_to_dcnm()
    module.exit_json(**dcnm_intf.result)


if __name__ == "__main__":
    main()
