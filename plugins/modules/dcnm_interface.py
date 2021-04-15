#!/usr/bin/python
#
# Copyright (c) 2020 Cisco and/or its affiliates.
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

__author__ = "Mallik Mudigonda"

DOCUMENTATION = '''
---
module: dcnm_interface
short_description: DCNM Ansible Module for managing interfaces.
version_added: "0.9.0"
description:
    - "DCNM Ansible Module for the following interface service operations"
    - "Create, Delete, Modify PortChannel, VPC, Loopback and Sub-Interfaces"
    - "Modify Ethernet Interfaces"
author: Mallik Mudigonda
options:
  fabric:
    description:
      - 'Name of the target fabric for interface operations'
    type: str
    required: true
  state:
    description:
      - The required state of the configuration after module completion.
    type: str
    choices:
      - merged
      - replaced
      - overridden
      - deleted
      - query
    default: merged
  config:
    description: A dictionary of interface operations
    type: list
    elements: dict
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
        required: true
      type:
        description:
          - Interface type. Example, pc, vpc, sub_int, lo, eth
        type: str
        required: true
        choices: ['pc', 'vpc', 'sub_int', 'lo', 'eth']
      deploy:
        description:
            - Flag indicating if the configuration must be pushed to the switch. If not included
              it is considered true by default
        type: bool
        default: true
      profile_pc:
        description:
          - NOTE: Though the key shown here is 'profile_pc' the actual key to be used in playbook 
                  is 'profile'. The key 'profile_pc' is used here to logically segregate the interface
                  objects applicable for this profile
          - Object profile which must be included for port channel interface configurations.
        suboptions:
          mode:
            description: Interface mode
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
              - Vlan for the interface. This option is applicable only for interfaces whose 'mode'
              - is 'access'
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
            type: ipv4
            default: ""
          ipv4_mask_len:
            description:
              - IPV4 address mask length. This object is applicable only if the 'mode' is 'l3'
            type: int
            choices : [Min:1, Max:31]
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
          - NOTE: Though the key shown here is 'profile_vpc' the actual key to be used in playbook 
                  is 'profile'. The key 'profile_vpc' is used here to logically segregate the interface
                  objects applicable for this profile
          - Object profile which must be included for virtual port channel inetrface configurations.
        suboptions:
          mode:
            description:
              Interface mode
            choices: ['trunk', 'access']
            type: str
            required: true
          peer1_pcid:
            description:
              - Port channel identifier of first peer. If this object is not included, then the value defaults to the
                vPC identifier. This value cannot be changed once vPC is created
            type: int
            choices: [Min:1, Max:4096]
            default: Default value is the vPC port identifier
          peer2_pcid:
            description:
              - Port channel identifier of second peer. If this object is not included, then the value defaults to the
                vPC identifier. This value cannot be changed once vPC is created
            type: int
            choices: [Min:1, Max:4096]
            default: Default value is the vPC port identifier
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
            descrption:
              - Port channel mode
            type: str
            choices: ['active', 'passive', 'on']
            default: active
          bpdu_guard:
            description:
              - Spanning-tree bpduguard
            type: str
            choices: ['true', 'false', 'no']
            default: true
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
              - Vlans that are allowed on this interface of first peer. This option is applicable only for interfaces whose 'mode' is 'trunk'
            type: str
            choices: ['none', 'all', 'vlan-range(e.g., 1-2, 3-40)']
            default: none
          peer2_allowed_vlans:
            description:
              - Vlans that are allowed on this interface of second peer. This option is applicable only for interfaces whose 'mode' is 'trunk'
            type: str
            choices: ['none', 'all', 'vlan-range(e.g., 1-2, 3-40)']
            default: none
          peer1_access_vlan:
            description:
              - Vlan for the interface of first peer. This option is applicable only for interfaces whose 'mode' is 'access'
            type: str
            default: ''
          peer2_access_vlan:
            description:
              - Vlan for the interface of second peer. This option is applicable only for interfaces whose 'mode' is 'access'
            type: str
            default: ''
          peer1_cmds:
            description:
              - Commands to be included in the configuration under this interface of first peer
            type: list
            default: []
          peer2_cmds:
            description:
              - Commands to be included in the configuration under this interface of second peer
            type: list
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
          - NOTE: Though the key shown here is 'profile_subint' the actual key to be used in playbook 
                  is 'profile'. The key 'profile_subint' is used here to logically segregate the interface
                  objects applicable for this profile
          - Object profile which must be included for sub-interface configurations.
        suboptions:
          mode:
            description: Interface mode
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
            type: ipv4
            default: ""
          ipv4_mask_len:
            description:
              - IPV4 address mask length.
            type: int
            choices : [Min:8, Max:31]
            default: 8
          ipv6_addr:
            description:
              - IPV6 address of the interface.
            type: ipv6
            default: ""
          ipv6_mask_len:
            description:
              - IPV6 address mask length.
            type: int
            choices : [Min:1, Max:31]
            default: 8
          mtu:
            description:
              - Interface MTU
            type: int
            choices: [Min: 576, Max: 9216]
            default: 9216
          vlan:
            description:
              - DOT1Q vlan id for this interface
            type: int
            choices: [Min: 2, Max: 3967]
            default: 0
          cmds:
            description:
              - Commands to be included in the configuration under this interface
            type: list
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
          - NOTE: Though the key shown here is 'profile_lo' the actual key to be used in playbook 
                  is 'profile'. The key 'profile_lo' is used here to logically segregate the interface
                  objects applicable for this profile
          - Object profile which must be included for loopback interface configurations.
        suboptions:
          mode:
            description: Interface mode
            choices: ['lo']
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
            type: ipv4
            default: ""
          ipv6_addr:
            description:
              - IPV6 address of the interface.
            type: ipv6
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
          - NOTE: Though the key shown here is 'profile_eth' the actual key to be used in playbook 
                  is 'profile'. The key 'profile_eth' is used here to logically segregate the interface
                  objects applicable for this profile
          - Object profile which must be included for ethernet interface configurations.
        suboptions:
          mode:
            description: Interface mode
            choices: ['trunk', 'access', 'routed', 'monitor', 'epl_routed']
            type: str
            required: true
          bpdu_guard:
            description:
              - Spanning-tree bpduguard
            type: str
            choices: ['true', 'false', 'no']
            default: true
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
          allowed_vlans:
            description:
              - Vlans that are allowed on this interface. This option is applicable only for interfaces whose 'mode' is 'trunk'
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
            choices: ['Auto', '100Mb', '1Gb', '10Gb', '25Gb', '40Gb', '100Gb']
            default: Auto
          int_vrf:
            description:
              - Interface VRF name. This object is applicable only if the 'mode' is 'routed'
            type: str
            default: default
          ipv4_addr:
            description:
              - IPV4 address of the interface. This object is applicable only if the 'mode' is 'routed' or 'epl_routed'
            type: ipv4
            default: ""
          ipv4_mask_len:
            description:
              - IPV4 address mask length. This object is applicable only if the 'mode' is 'routed' or
                'epl_routed'
            type: int
            choices : [Min:1, Max:31]
            default: 8
          ipv6_addr:
            description:
              - IPV6 address of the interface. This object is applicable only if the 'mode' is 'epl_routed'
            type: ipv6
            default: ""
          ipv6_mask_len:
            description:
              - IPV6 address mask length. This object is applicable only if the 'mode' is 'epl_routed'
            type: int
            choices : [Min:1, Max:31]
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
'''

EXAMPLES = '''

States:
This module supports the following states:

Merged:
  Interfaces defined in the playbook will be merged into the target fabric.

  The interfaces listed in the playbook will be created if not already present on the DCNM
  server. If the interface is already present and the configuration information included
  in the playbook is either different or not present in DCNM, then the corresponding
  information is added to the interface on DCNM. If an interface mentioned in playbook
  is already present on DCNM and there is no difference in configuration, no operation
  will be performed for such interface.

Replaced:
  Interfaces defined in the playbook will be replaced in the target fabric.

  The state of the interfaces listed in the playbook will serve as source of truth for the
  same interfaces present on the DCNM under the fabric mentioned. Additions and updations
  will be done to bring the DCNM interfaces to the state listed in the playbook.
  Note: Replace will only work on the interfaces mentioned in the playbook.

Overridden:
  Interfaces defined in the playbook will be overridden in the target fabric.

  The state of the interfaces listed in the playbook will serve as source of truth for all
  the interfaces under the fabric mentioned. Additions and deletions will be done to bring
  the DCNM interfaces to the state listed in the playbook. All interfaces other than the
  ones mentioned in the playbook will either be deleted or reset to default state.
  Note: Override will work on the all the interfaces present in the DCNM Fabric.

Deleted:
  Interfaces defined in the playbook will be deleted in the target fabric.

  Deletes the list of interfaces specified in the playbook.  If the playbook does not include
  any switches or interface information, then all interfaces from all switches in the
  fabric will either be deleted or put to default state. If configuuration includes information
  pertaining to any particular switch, then interfaces belonging to that switch will either be
  deleted or put to default. If configuration includes both interface and switch information,
  then the specified interfaces will either be deleted or reset on all the seitches specified

Query:
  Returns the current DCNM state for the interfaces listed in the playbook.

LOOPBACK INTERFACE

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

PORTCHANNEL INTERFACE

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

SUB-INTERFACE

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

VPC INTERFACE

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

QUERY

 - name: Query interface details
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: query            # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - switch:
              - "192.172.1.1"   # provide the switch information where the config is to be deployed
          - name: po350
            switch:
              - "192.172.1.1"   # provide the switch information where the config is to be deployed
          - name: lo450
            switch:
              - "192.172.1.1"   # provide the switch information where the config is to be deployed
          - name: eth1/1
            switch:
              - "192.172.1.1"   # provide the switch information where the config is to be deployed
          - name: eth1/15.2
            switch:
              - "192.172.1.1"   # provide the switch information where the config is to be deployed
          - name: vpc750
            switch:
              - "192.172.1.1"   # provide the switch information where the config is to be deployed

'''

import time
import json
import re
import copy
import sys
import socket
from textwrap import dedent

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import \
    dcnm_send, get_fabric_inventory_details, dcnm_get_ip_addr_info, validate_list_of_dicts, get_ip_sn_dict

import datetime

LOG_ERROR     = 0
LOG_DEBUG     = 4
LOG_VERBOSE   = 5

class DcnmIntf:

    def __init__(self, module):
        self.module        = module
        self.params        = module.params
        self.fabric        = module.params['fabric']
        self.config        = copy.deepcopy(module.params.get('config'))
        self.pb_input      = []
        self.check_mode    = False
        self.intf_info     = []
        self.want          = []
        self.have          = []
        self.have_all      = []
        self.have_all_list = []
        self.diff_create   = []
        self.diff_replace  = []
        self.diff_delete   = [[],[],[],[],[]]
        self.diff_deploy   = []
        self.diff_query    = []
        self.log_verbosity = 0
        self.fd            = None
        self.vpc_ip_sn     = {}
        self.changed_dict  = [{'merged' : [], 'deleted' : [], 'replaced' : [], 'overridden' : [], 'deploy' : [], 'query' : []}]

        self.inventory_data = get_fabric_inventory_details(self.module, self.fabric)
        self.ip_sn, self.hn_sn = get_ip_sn_dict(self.inventory_data)

        self.dcnm_intf_facts = {
            'fabric' : module.params['fabric'],
            'config' : module.params['config'],
        }

        self.result = dict(
            changed  = False,
            diff     = [],
            response = []
        )

        # New Interfaces
        # To map keys from self.have to keys from config
        self.keymap = {
            "policy"                  : "policy",
            "ifName"                  : "ifname",
            "serialNumber"            : "sno",
            "fabricName"              : "fabric",
            "IP"                      : "ipv4_addr",
            "INTF_VRF"                : "int_vrf",
            "V6IP"                    : "ipv6_addr",
            "IPv6"                    : "ipv6_addr",
            "IPv6_PREFIX"             : "ipv6_mask_len",
            "ROUTING_TAG"             : "route_tag",
            "ROUTE_MAP_TAG"           : "route_tag",
            "CONF"                    : "cmds",
            "DESC"                    : "description",
            "VLAN"                    : "vlan",
            "ADMIN_STATE"             : "admin_state",
            "MEMBER_INTERFACES"       : "members",
            "PC_MODE"                 : "pc_mode",
            "BPDUGUARD_ENABLED"       : "bpdu_guard",
            "PORTTYPE_FAST_ENABLED"   : "port_type_fast",
            "MTU"                     : "mtu",
            "SPEED"                   : "speed",
            "ALLOWED_VLANS"           : "allowed_vlans",
            "ACCESS_VLAN"             : "access_vlan",
            "PREFIX"                  : "ipv4_mask_len",
            "INTF_NAME"               : "ifname",
            "PO_ID"                   : "ifname",
            "PEER1_PCID"              : "peer1_pcid",
            "PEER2_PCID"              : "peer2_pcid",
            "PEER1_MEMBER_INTERFACES" : "peer1_members",
            "PEER2_MEMBER_INTERFACES" : "peer2_members",
            "PEER1_ALLOWED_VLANS"     : "peer1_allowed_vlans",
            "PEER2_ALLOWED_VLANS"     : "peer2_allowed_vlans",
            "PEER1_PO_DESC"           : "peer1_description",
            "PEER2_PO_DESC"           : "peer2_description",
            "PEER1_PO_CONF"           : "peer1_cmds",
            "PEER2_PO_CONF"           : "peer2_cmds",
            "PEER1_ACCESS_VLAN"       : "peer1_access_vlan",
            "PEER2_ACCESS_VLAN"       : "peer2_access_vlan",
        }

        # New Interfaces
        self.pol_types = {
            "pc_monitor"     : "int_monitor_port_channel_11_1",
            "pc_trunk"       : "int_port_channel_trunk_host_11_1",
            "pc_access"      : "int_port_channel_access_host_11_1",
            "pc_l3"          : "int_l3_port_channel",
            "sub_int_subint" : "int_subif_11_1",
            "lo_lo"          : "int_loopback_11_1",
            "eth_trunk"      : "int_trunk_host_11_1",
            "eth_access"     : "int_access_host_11_1",
            "eth_routed"     : "int_routed_host_11_1",
            "eth_monitor"    : "int_monitor_ethernet_11_1",
            "eth_epl_routed" : "epl_routed_intf",
            "vpc_trunk"      : "int_vpc_trunk_host_11_1",
            "vpc_access"     : "int_vpc_access_host_11_1"
        }

        # New Interfaces
        self.int_types = {
            "pc"      : "INTERFACE_PORT_CHANNEL",
            "vpc"     : "INTERFACE_VPC",
            "sub_int" : "SUBINTERFACE",
            "lo"      : "INTERFACE_LOOPBACK",
            "eth"     : "INTERFACE_ETHERNET"
        }

        # New Interfaces
        self.int_index = {
            "INTERFACE_PORT_CHANNEL" : 0,
            "INTERFACE_VPC"          : 1,
            "INTERFACE_ETHERNET"     : 2,
            "INTERFACE_LOOPBACK"     : 3,
            "SUBINTERFACE"           : 4

        }

    def log_msg (self, msg):

        if (self.fd is None):
            self.fd = open("interface.log", "w+")
        if (self.fd is not None):
            self.fd.write (msg)

    # New Interfaces
    def dcnm_intf_get_if_name (self, name, if_type):

       if ('pc' == if_type):
           port_id = re.findall(r'\d+', name)
           return ("Port-channel" + str(port_id[0]), port_id[0])
       if ('vpc' == if_type):
           port_id = re.findall(r'\d+', name)
           return ("vPC" + str(port_id[0]), port_id[0])
       if ('sub_int' == if_type):
           port_id = re.findall(r'\d+\/\d+.\d+', name)
           return ("Ethernet" + str(port_id[0]), port_id[0])
       if ('lo' == if_type):
           port_id = re.findall(r'\d+', name)
           return ("Loopback" + str(port_id[0]), port_id[0])
       if ('eth' == if_type):
           port_id = re.findall(r'\d+\/\d+', name)
           return ("Ethernet" + str(port_id[0]), port_id[0])

    def dcnm_intf_get_vpc_serial_number(self, sw):

        path = '/rest/interface/vpcpair_serial_number?serial_number=' + self.ip_sn[sw]
        resp = dcnm_send (self.module, 'GET', path)

        if (resp and resp['RETURN_CODE'] == 200):
            return resp['DATA']['vpc_pair_sn']
        else:
            return ''

    # Flatten the incoming config database and have the required fileds updated.
    # This modified config DB will be used while creating payloads. To avoid
    # messing up the incoming config make a copy of it.
    def dcnm_intf_copy_config(self):

        if (None is self.config):
            return

        for cfg in self.config:

            if(None is cfg.get('switch', None)):
                continue
            for sw in cfg['switch']:

                c = copy.deepcopy(cfg)

                # Add type of interface
                ckeys = list(cfg.keys())
                for ck in ckeys:
                    if (ck.startswith('profile')):

                        if ('type' not in cfg):
                            self.module.fail_json(msg='<type> element, which is mandatory is missing in config')

                        pol_ind_str = cfg['type'] + '_' + cfg['profile']['mode']

                        c[ck]['fabric']   = self.dcnm_intf_facts['fabric']
                        if (cfg['type'] == 'vpc'):
                            c[ck]['sno']  = self.vpc_ip_sn[sw]
                        else:
                            c[ck]['sno']  = self.ip_sn[sw]
                        ifname,port_id    = self.dcnm_intf_get_if_name (c['name'], c['type'])
                        c[ck]['ifname']   = ifname
                        c[ck]['policy']   = self.pol_types[pol_ind_str]
                        self.pb_input.append (c[ck])

    def dcnm_intf_validate_interface_input (self, config, common_spec, prof_spec):

        plist = []

        intf_info, invalid_params = validate_list_of_dicts(config, common_spec)
        if invalid_params:
            mesg = 'Invalid parameters in playbook: {}'.format("while processing interface " + config[0]['name'] + '\n'  +'\n'.join(invalid_params))
            self.module.fail_json(msg=mesg)

        self.intf_info.extend(intf_info)

        if (prof_spec is not None):

            for item in intf_info:

                plist.append(item['profile'])
                intf_profile, invalid_params = validate_list_of_dicts(plist, prof_spec)

                # Merge the info from the intf_profile into the intf_info to have a single dict to be used for building
                # payloads
                item['profile'].update(intf_profile[0])

                plist.remove(item['profile'])
                if invalid_params:
                    mesg = 'Invalid parameters in playbook: {}'.format("while processing interface " + config[0]['name'] + '\n'  +'\n'.join(invalid_params))
                    self.module.fail_json(msg=mesg)

    def dcnm_intf_validate_port_channel_input (self, config):

        pc_spec = dict(
            name           = dict(required=True, type='str'),
            switch         = dict(required=True, type='list'),
            type           = dict(required=True, type='str'),
            deploy         = dict(type='bool', default=True),
            profile        = dict(required=True, type='dict')
        )

        pc_prof_spec_trunk = dict(
            mode           = dict(required=True, type='str'),
            members        = dict(type='list'),
            pc_mode        = dict(type='str', default='active'),
            bpdu_guard     = dict(type='str', default='true'),
            port_type_fast = dict(type='bool', default=True),
            mtu            = dict(type='str', default='jumbo'),
            allowed_vlans  = dict(type='str', default='none'),
            cmds           = dict(type='list'),
            description    = dict(type='str', default=''),
            admin_state    = dict(type='bool', default=True)
        )

        pc_prof_spec_access = dict(
            mode           = dict(required=True, type='str'),
            members        = dict(type='list'),
            pc_mode        = dict(type='str', default='active'),
            bpdu_guard     = dict(type='str', default='true'),
            port_type_fast = dict(type='bool', default=True),
            mtu            = dict(type='str', default='jumbo'),
            access_vlan    = dict(type='str', default=''),
            cmds           = dict(type='list'),
            description    = dict(type='str', default=''),
            admin_state    = dict(type='bool', default=True)
        )

        pc_prof_spec_l3 = dict(
            mode           = dict(required=True, type='str'),
            members        = dict(type='list'),
            pc_mode        = dict(type='str', default='active'),
            int_vrf        = dict(type='str', default='default'),
            ipv4_addr      = dict(type='ipv4', default=''),
            ipv4_mask_len  = dict(type='int', default=8),
            route_tag      = dict(type='str', default=''),
            mtu            = dict(type='int', default=9216, range_min=576, range_max=9216),
            cmds           = dict(type='list'),
            description    = dict(type='str', default=''),
            admin_state    = dict(type='bool', default=True)
        )

        if ('trunk' == config[0]['profile']['mode']):
            self.dcnm_intf_validate_interface_input (config, pc_spec, pc_prof_spec_trunk)
        if ('access' == config[0]['profile']['mode']):
            self.dcnm_intf_validate_interface_input (config, pc_spec, pc_prof_spec_access)
        if ('l3' == config[0]['profile']['mode']):
            self.dcnm_intf_validate_interface_input (config, pc_spec, pc_prof_spec_l3)
        if ('monitor' == config[0]['profile']['mode']):
            self.dcnm_intf_validate_interface_input (config, pc_spec, None)

    def dcnm_intf_validate_virtual_port_channel_input (self, cfg):

        vpc_spec = dict(
            name           = dict(required=True, type='str'),
            switch         = dict(required=True, type='list'),
            type           = dict(required=True, type='str'),
            deploy         = dict(type='str', default=True),
            profile         = dict(required=True, type='dict')
        )

        vpc_prof_spec_trunk = dict(
            mode                 = dict(required=True, type='str'),
            peer1_pcid           = dict(type='int', default=0, range_min=1, range_max=4096),
            peer2_pcid           = dict(type='int', default=0, range_min=1, range_max=4096),
            peer1_members        = dict(type='list'),
            peer2_members        = dict(type='list'),
            pc_mode              = dict(type='str', default='active'),
            bpdu_guard           = dict(type='str', default='true'),
            port_type_fast       = dict(type='bool', default=True),
            mtu                  = dict(type='str', default='jumbo'),
            peer1_allowed_vlans  = dict(type='str', default='none'),
            peer2_allowed_vlans  = dict(type='str', default='none'),
            peer1_cmds           = dict(type='list'),
            peer2_cmds           = dict(type='list'),
            peer1_description    = dict(type='str', default=''),
            peer2_description    = dict(type='str', default=''),
            admin_state          = dict(type='bool', default=True)
        )

        vpc_prof_spec_access = dict(
            mode                 = dict(required=True, type='str'),
            peer1_pcid           = dict(type='int', default=0, range_min=1, range_max=4096),
            peer2_pcid           = dict(type='int', default=0, range_min=1, range_max=4096),
            peer1_members        = dict(type='list'),
            peer2_members        = dict(type='list'),
            pc_mode              = dict(type='str', default='active'),
            bpdu_guard           = dict(type='str', default='true'),
            port_type_fast       = dict(type='bool', default=True),
            mtu                  = dict(type='str', default='jumbo'),
            peer1_access_vlan    = dict(type='str', default=''),
            peer2_access_vlan    = dict(type='str', default=''),
            peer1_cmds           = dict(type='list'),
            peer2_cmds           = dict(type='list'),
            peer1_description    = dict(type='str', default=''),
            peer2_description    = dict(type='str', default=''),
            admin_state          = dict(type='bool', default=True)
        )

        if ('trunk' == cfg[0]['profile']['mode']):
            self.dcnm_intf_validate_interface_input (cfg, vpc_spec, vpc_prof_spec_trunk)
        if ('access' == cfg[0]['profile']['mode']):
            self.dcnm_intf_validate_interface_input (cfg, vpc_spec, vpc_prof_spec_access)

    def dcnm_intf_validate_sub_interface_input (self, cfg):

        sub_spec = dict(
            name           = dict(required=True, type='str'),
            switch         = dict(required=True, type='list'),
            type           = dict(required=True, type='str'),
            deploy         = dict(type='str', default=True),
            profile        = dict(required=True, type='dict'),
        )

        sub_prof_spec = dict(
            mode           = dict(required=True, type='str'),
            vlan           = dict(required=True, type='int', range_min=2, range_max=3967),
            ipv4_addr      = dict(required=True, type='ipv4'),
            ipv4_mask_len  = dict(required=True, type='int', range_min=8, range_max=31),
            int_vrf        = dict(type='str', default='default'),
            ipv6_addr      = dict(type='ipv6', default=''),
            ipv6_mask_len  = dict(type='int', range_min=64, range_max=127, default=64),
            mtu            = dict(type='int', range_min=576, range_max=9216, default=9216),
            cmds           = dict(type='list'),
            description    = dict(type='str', default=''),
            admin_state    = dict(type='bool', default=True)
        )

        self.dcnm_intf_validate_interface_input (cfg, sub_spec, sub_prof_spec)

    def dcnm_intf_validate_loopback_interface_input (self, cfg):

        lo_spec = dict(
            name           = dict(required=True, type='str'),
            switch         = dict(required=True, type='list'),
            type           = dict(required=True, type='str'),
            deploy         = dict(type='str', default=True),
            profile        = dict(required=True, type='dict'),
        )

        lo_prof_spec = dict(
            mode           = dict(required=True, type='str'),
            ipv4_addr      = dict(required=True, type='ipv4'),
            int_vrf        = dict(type='str', default='default'),
            ipv6_addr      = dict(type='ipv6', default=''),
            route_tag      = dict(type='str', default=''),
            cmds           = dict(type='list'),
            description    = dict(type='str', default=''),
            admin_state    = dict(type='bool', default=True)
        )

        self.dcnm_intf_validate_interface_input (cfg, lo_spec, lo_prof_spec)

    def dcnm_intf_validate_ethernet_interface_input (self, cfg):

        eth_spec = dict(
            name           = dict(required=True, type='str'),
            switch         = dict(required=True, type='list'),
            type           = dict(required=True, type='str'),
            deploy         = dict(type='str', default=True),
            profile        = dict(required=True, type='dict'),
        )

        eth_prof_spec_trunk = dict(
            mode           = dict(required=True, type='str'),
            bpdu_guard     = dict(type='str', default='true'),
            port_type_fast = dict(type='bool', default=True),
            mtu            = dict(type='str', default='jumbo'),
            speed          = dict(type='str', default="Auto"),
            allowed_vlans  = dict(type='str', default='none'),
            cmds           = dict(type='list'),
            description    = dict(type='str', default=''),
            admin_state    = dict(type='bool', default=True)
        )

        eth_prof_spec_access = dict(
            mode           = dict(required=True, type='str'),
            bpdu_guard     = dict(type='str', default='true'),
            port_type_fast = dict(type='bool', default=True),
            mtu            = dict(type='str', default='jumbo'),
            speed          = dict(type='str', default="Auto"),
            access_vlan    = dict(type='str', default=''),
            cmds           = dict(type='list'),
            description    = dict(type='str', default=''),
            admin_state    = dict(type='bool', default=True)
        )

        eth_prof_spec_routed_host= dict(
            int_vrf        = dict(type='str', default='default'),
            ipv4_addr      = dict(type='ipv4', default=''),
            ipv4_mask_len  = dict(type='int', default=8),
            route_tag      = dict(type='str', default=''),
            mtu            = dict(type='int', default=9216, range_min=576, range_max=9216),
            speed          = dict(type='str', default="Auto"),
            cmds           = dict(type='list'),
            description    = dict(type='str', default=''),
            admin_state    = dict(type='bool', default=True)
        )

        eth_prof_spec_epl_routed_host = dict(
            mode           = dict(required=True, type='str'),
            ipv4_addr      = dict(required=True, type='ipv4'),
            ipv4_mask_len  = dict(type='int', default=8),
            ipv6_addr      = dict(type='ipv6', default=''),
            ipv6_mask_len  = dict(type='int', range_min=64, range_max=127, default=64),
            route_tag      = dict(type='str', default=''),
            mtu            = dict(type='int', default=1500, range_max=9216),
            speed          = dict(type='str', default="Auto"),
            cmds           = dict(type='list'),
            description    = dict(type='str', default=''),
            admin_state    = dict(type='bool', default=True)
        )

        if ('trunk' == cfg[0]['profile']['mode']):
            self.dcnm_intf_validate_interface_input (cfg, eth_spec, eth_prof_spec_trunk)
        if ('access' == cfg[0]['profile']['mode']):
            self.dcnm_intf_validate_interface_input (cfg, eth_spec, eth_prof_spec_access)
        if ('routed' == cfg[0]['profile']['mode']):
            self.dcnm_intf_validate_interface_input (cfg, eth_spec, eth_prof_spec_routed_host)
        if ('monitor' == cfg[0]['profile']['mode']):
            self.dcnm_intf_validate_interface_input (cfg, eth_spec, None)
        if ('epl_routed' == cfg[0]['profile']['mode']):
            self.dcnm_intf_validate_interface_input (cfg, eth_spec, eth_prof_spec_epl_routed_host)

    def dcnm_intf_validate_delete_state_input(self, cfg):

        del_spec = dict(
            name           = dict(required=False, type='str'),
            switch         = dict(required=False, type='list'),
        )

        self.dcnm_intf_validate_interface_input (cfg, del_spec, None)

    def dcnm_intf_validate_query_state_input(self, cfg):

        query_spec = dict(
            name           = dict(type='str', default=''),
            switch         = dict(required=True, type='list'),
        )

        self.dcnm_intf_validate_interface_input (cfg, query_spec, None)

    def dcnm_intf_validate_overridden_state_input(self, cfg):

        overridden_spec = dict(
            name           = dict(required=False,type='str', default=''),
            switch         = dict(required=False, type='list'),
        )

        self.dcnm_intf_validate_interface_input (cfg, overridden_spec, None)

    # New Interfaces
    def dcnm_intf_validate_input(self):
        """Parse the playbook values, validate to param specs."""

        if (None is self.config):
           return

        # Inputs will vary for each type of interface and for each state. Make specific checks
        # for each case.

        cfg = []
        for item in self.config:

            citem = copy.deepcopy(item)

            cfg.append(citem)

            if (self.module.params['state'] == 'deleted'):
                # config for delete state is different for all interafces. It may not have the profile
                # construct. So validate deleted state differently
                self.dcnm_intf_validate_delete_state_input(cfg)
            elif (self.module.params['state'] == 'query'):
                # config for query state is different for all interafces. It may not have the profile
                # construct. So validate query state differently
                self.dcnm_intf_validate_query_state_input(cfg)
            elif ((self.module.params['state'] == 'overridden') and not (any('profile' in key for key in item))):
                # config for overridden state is different for all interafces. It may not have the profile
                # construct. So validate overridden state differently
                self.dcnm_intf_validate_overridden_state_input(cfg)
            else:
                if ('type' not in item):
                    mesg = 'Invalid parameters in playbook: {}'.format("while processing interface " + item['name'] + '\n'  + 'mandatory object "type" missing')
                    self.module.fail_json(msg=mesg)

                if (item['type'] == 'pc'):
                    self.dcnm_intf_validate_port_channel_input(cfg)
                if (item['type'] == 'vpc'):
                    self.dcnm_intf_validate_virtual_port_channel_input(cfg)
                if (item['type'] == 'sub_int'):
                    self.dcnm_intf_validate_sub_interface_input(cfg)
                if (item['type'] == 'lo'):
                    self.dcnm_intf_validate_loopback_interface_input(cfg)
                if (item['type'] == 'eth'):
                    self.dcnm_intf_validate_ethernet_interface_input(cfg)
            cfg.remove(citem)

    def dcnm_intf_get_pc_payload (self, delem, intf, profile):

        # Extract port id from the given name, which is of the form 'po300'

        ifname,port_id = self.dcnm_intf_get_if_name (delem['name'], delem['type'])
        intf["interfaces"][0].update ({"ifName"        : ifname})

        if (delem[profile]['mode'] == 'trunk'):
            if (delem[profile]['members'] is None):
                intf["interfaces"][0]["nvPairs"]["MEMBER_INTERFACES"]     = ""
            else:
                intf["interfaces"][0]["nvPairs"]["MEMBER_INTERFACES"]     = ",".join(delem[profile]['members'])
            intf["interfaces"][0]["nvPairs"]["PC_MODE"]                   = delem[profile]['pc_mode']
            intf["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"]         = delem[profile]['bpdu_guard'].lower()
            intf["interfaces"][0]["nvPairs"]["PORTTYPE_FAST_ENABLED"]     = str(delem[profile]['port_type_fast']).lower()
            intf["interfaces"][0]["nvPairs"]["MTU"]                       = str(delem[profile]['mtu'])
            intf["interfaces"][0]["nvPairs"]["ALLOWED_VLANS"]             = delem[profile]['allowed_vlans']
            intf["interfaces"][0]["nvPairs"]["PO_ID"]                     = ifname
        if (delem[profile]['mode'] == 'access'):
            if (delem[profile]['members'] is None):
                intf["interfaces"][0]["nvPairs"]["MEMBER_INTERFACES"]     = ""
            else:
                intf["interfaces"][0]["nvPairs"]["MEMBER_INTERFACES"]     = ",".join(delem[profile]['members'])
            intf["interfaces"][0]["nvPairs"]["PC_MODE"]                   = delem[profile]['pc_mode']
            intf["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"]         = delem[profile]['bpdu_guard'].lower()
            intf["interfaces"][0]["nvPairs"]["PORTTYPE_FAST_ENABLED"]     = str(delem[profile]['port_type_fast']).lower()
            intf["interfaces"][0]["nvPairs"]["MTU"]                       = str(delem[profile]['mtu'])
            intf["interfaces"][0]["nvPairs"]["ACCESS_VLAN"]               = delem[profile]['access_vlan']
            intf["interfaces"][0]["nvPairs"]["PO_ID"]                     = ifname
        if (delem[profile]['mode'] == 'l3'):
            if (delem[profile]['members'] is None):
                intf["interfaces"][0]["nvPairs"]["MEMBER_INTERFACES"]     = ""
            else:
                intf["interfaces"][0]["nvPairs"]["MEMBER_INTERFACES"]     = ",".join(delem[profile]['members'])
            intf["interfaces"][0]["nvPairs"]["PC_MODE"]                   = delem[profile]['pc_mode']
            intf["interfaces"][0]["nvPairs"]["INTF_VRF"]                  = delem[profile]['int_vrf']
            intf["interfaces"][0]["nvPairs"]["IP"]                        = str(delem[profile]['ipv4_addr'])
            if (delem[profile]['ipv4_addr'] != ''):
                intf["interfaces"][0]["nvPairs"]["PREFIX"]                = str(delem[profile]['ipv4_mask_len'])
            else:
                intf["interfaces"][0]["nvPairs"]["PREFIX"]                = ''
            intf["interfaces"][0]["nvPairs"]["ROUTING_TAG"]               = delem[profile]['route_tag']
            intf["interfaces"][0]["nvPairs"]["PO_ID"]                     = ifname
            intf["interfaces"][0]["nvPairs"]["MTU"]                       = str(delem[profile]['mtu'])
        if (delem[profile]['mode'] == 'monitor'):
            intf["interfaces"][0]["nvPairs"]["INTF_NAME"]                 = ifname

        if (delem[profile]['mode'] != 'monitor'):
            intf["interfaces"][0]["nvPairs"]["DESC"]                      = delem[profile]['description']
            if (delem[profile]['cmds'] is None):
                intf["interfaces"][0]["nvPairs"]["CONF"]                  = ""
            else:
                intf["interfaces"][0]["nvPairs"]["CONF"]                  = "\n".join(delem[profile]['cmds'])
            intf["interfaces"][0]["nvPairs"]["ADMIN_STATE"]               = str(delem[profile]['admin_state']).lower()

    def dcnm_intf_get_vpc_payload (self, delem, intf, profile):

        # Extract port id from the given name, which is of the form 'vpc300'

        ifname, port_id = self.dcnm_intf_get_if_name (delem['name'], delem['type'])
        intf["interfaces"][0].update ({"ifName"        : ifname})

        if (delem[profile]['mode'] == 'trunk'):

            if (delem[profile]['peer1_members'] is None):
                intf["interfaces"][0]["nvPairs"]["PEER1_MEMBER_INTERFACES"]     = ""
            else:
                intf["interfaces"][0]["nvPairs"]["PEER1_MEMBER_INTERFACES"]     = ",".join(delem[profile]['peer1_members'])

            if (delem[profile]['peer2_members'] is None):
                intf["interfaces"][0]["nvPairs"]["PEER2_MEMBER_INTERFACES"]     = ""
            else:
                intf["interfaces"][0]["nvPairs"]["PEER2_MEMBER_INTERFACES"]     = ",".join(delem[profile]['peer2_members'])

            intf["interfaces"][0]["nvPairs"]["PC_MODE"]                         = delem[profile]['pc_mode']
            intf["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"]               = delem[profile]['bpdu_guard'].lower()
            intf["interfaces"][0]["nvPairs"]["PORTTYPE_FAST_ENABLED"]           = str(delem[profile]['port_type_fast']).lower()
            intf["interfaces"][0]["nvPairs"]["MTU"]                             = str(delem[profile]['mtu'])
            intf["interfaces"][0]["nvPairs"]["PEER1_ALLOWED_VLANS"]             = delem[profile]['peer1_allowed_vlans']
            intf["interfaces"][0]["nvPairs"]["PEER2_ALLOWED_VLANS"]             = delem[profile]['peer2_allowed_vlans']

            if (delem[profile]["peer1_pcid"] == 0):
                intf["interfaces"][0]["nvPairs"]["PEER1_PCID"]                 = str(port_id)
            else:
                intf["interfaces"][0]["nvPairs"]["PEER1_PCID"]                 = str(delem[profile]["peer1_pcid"])

            if (delem[profile]["peer2_pcid"] == 0):
                intf["interfaces"][0]["nvPairs"]["PEER2_PCID"]                 =  str(port_id)
            else:
                intf["interfaces"][0]["nvPairs"]["PEER2_PCID"]                 = str(delem[profile]["peer2_pcid"])

        if (delem[profile]['mode'] == 'access'):

            if (delem[profile]['peer1_members'] is None):
                intf["interfaces"][0]["nvPairs"]["PEER1_MEMBER_INTERFACES"]     = ""
            else:
                intf["interfaces"][0]["nvPairs"]["PEER1_MEMBER_INTERFACES"]     = ",".join(delem[profile]['peer1_members'])

            if (delem[profile]['peer2_members'] is None):
                intf["interfaces"][0]["nvPairs"]["PEER2_MEMBER_INTERFACES"]     = ""
            else:
                intf["interfaces"][0]["nvPairs"]["PEER2_MEMBER_INTERFACES"]     = ",".join(delem[profile]['peer2_members'])

            intf["interfaces"][0]["nvPairs"]["PC_MODE"]                         = delem[profile]['pc_mode']
            intf["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"]               = delem[profile]['bpdu_guard'].lower()
            intf["interfaces"][0]["nvPairs"]["PORTTYPE_FAST_ENABLED"]           = str(delem[profile]['port_type_fast']).lower()
            intf["interfaces"][0]["nvPairs"]["MTU"]                             = str(delem[profile]['mtu'])
            intf["interfaces"][0]["nvPairs"]["PEER1_ACCESS_VLAN"]               = delem[profile]['peer1_access_vlan']
            intf["interfaces"][0]["nvPairs"]["PEER2_ACCESS_VLAN"]               = delem[profile]['peer2_access_vlan']

            if (delem[profile]["peer1_pcid"] == 0):
                intf["interfaces"][0]["nvPairs"]["PEER1_PCID"]                 = str(port_id)
            else:
                intf["interfaces"][0]["nvPairs"]["PEER1_PCID"]                 = str(delem[profile]["peer1_pcid"])

            if (delem[profile]["peer2_pcid"] == 0):
                intf["interfaces"][0]["nvPairs"]["PEER2_PCID"]                 = str(port_id)
            else:
                intf["interfaces"][0]["nvPairs"]["PEER2_PCID"]                 = str(delem[profile]["peer2_pcid"])

        intf["interfaces"][0]["nvPairs"]["PEER1_PO_DESC"]                       = delem[profile]['peer1_description']
        intf["interfaces"][0]["nvPairs"]["PEER2_PO_DESC"]                       = delem[profile]['peer2_description']
        if (delem[profile]['peer1_cmds'] is None):
            intf["interfaces"][0]["nvPairs"]["PEER1_PO_CONF"]                   = ""
        else:
            intf["interfaces"][0]["nvPairs"]["PEER1_PO_CONF"]                   = "\n".join(delem[profile]['peer1_cmds'])
        if (delem[profile]['peer2_cmds'] is None):
            intf["interfaces"][0]["nvPairs"]["PEER2_PO_CONF"]                   = ""
        else:
            intf["interfaces"][0]["nvPairs"]["PEER2_PO_CONF"]                   = "\n".join(delem[profile]['peer2_cmds'])
        intf["interfaces"][0]["nvPairs"]["ADMIN_STATE"]                         = str(delem[profile]['admin_state']).lower()
        intf["interfaces"][0]["nvPairs"]["INTF_NAME"]                           = ifname

    def dcnm_intf_get_sub_intf_payload (self, delem, intf, profile):

        # Extract port id from the given name, which is of the form 'po300'

        ifname, port_id = self.dcnm_intf_get_if_name (delem['name'], delem['type'])
        intf["interfaces"][0].update ({"ifName"        : ifname})

        intf["interfaces"][0]["nvPairs"]["VLAN"]               = str(delem[profile]['vlan'])
        intf["interfaces"][0]["nvPairs"]["INTF_VRF"]           = delem[profile]['int_vrf']
        intf["interfaces"][0]["nvPairs"]["IP"]                 = str(delem[profile]['ipv4_addr'])
        intf["interfaces"][0]["nvPairs"]["PREFIX"]             = str(delem[profile]['ipv4_mask_len'])
        if (delem[profile]['ipv6_addr']):
            intf["interfaces"][0]["nvPairs"]["IPv6"]           = str(delem[profile]['ipv6_addr'])
            intf["interfaces"][0]["nvPairs"]["IPv6_PREFIX"]    = str(delem[profile]['ipv6_mask_len'])
        else:
            intf["interfaces"][0]["nvPairs"]["IPv6"]           = ""
            intf["interfaces"][0]["nvPairs"]["IPv6_PREFIX"]    = ""
        intf["interfaces"][0]["nvPairs"]["MTU"]                = str(delem[profile]['mtu'])
        intf["interfaces"][0]["nvPairs"]["INTF_NAME"]          = ifname
        intf["interfaces"][0]["nvPairs"]["DESC"]               = delem[profile]['description']
        if (delem[profile]['cmds'] is None):
            intf["interfaces"][0]["nvPairs"]["CONF"]           = ""
        else:
            intf["interfaces"][0]["nvPairs"]["CONF"]           = "\n".join(delem[profile]['cmds'])
        intf["interfaces"][0]["nvPairs"]["ADMIN_STATE"]        = str(delem[profile]['admin_state']).lower()

    def dcnm_intf_get_loopback_payload (self, delem, intf, profile):

        # Extract port id from the given name, which is of the form 'po300'

        ifname, port_id = self.dcnm_intf_get_if_name (delem['name'], delem['type'])
        intf["interfaces"][0].update ({"ifName"        : ifname})

        intf["interfaces"][0]["nvPairs"]["INTF_VRF"]       = delem[profile]['int_vrf']
        intf["interfaces"][0]["nvPairs"]["IP"]             = str(delem[profile]['ipv4_addr'])
        intf["interfaces"][0]["nvPairs"]["V6IP"]           = str(delem[profile]['ipv6_addr'])
        intf["interfaces"][0]["nvPairs"]["ROUTE_MAP_TAG"]  = delem[profile]['route_tag']
        intf["interfaces"][0]["nvPairs"]["INTF_NAME"]      = ifname
        intf["interfaces"][0]["nvPairs"]["DESC"]           = delem[profile]['description']
        if (delem[profile]['cmds'] is None):
            intf["interfaces"][0]["nvPairs"]["CONF"]       = ""
        else:
            intf["interfaces"][0]["nvPairs"]["CONF"]       = "\n".join(delem[profile]['cmds'])
        intf["interfaces"][0]["nvPairs"]["ADMIN_STATE"]    = str(delem[profile]['admin_state']).lower()

    def dcnm_intf_get_eth_payload (self, delem, intf, profile):

        # Extract port id from the given name, which is of the form 'po300'

        ifname, port_id = self.dcnm_intf_get_if_name (delem['name'], delem['type'])
        intf["interfaces"][0].update ({"ifName"        : ifname})

        if (delem[profile]['mode'] == 'trunk'):
            intf["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"]         = delem[profile]['bpdu_guard'].lower()
            intf["interfaces"][0]["nvPairs"]["PORTTYPE_FAST_ENABLED"]     = str(delem[profile]['port_type_fast']).lower()
            intf["interfaces"][0]["nvPairs"]["MTU"]                       = str(delem[profile]['mtu'])
            intf["interfaces"][0]["nvPairs"]["SPEED"]                     = str(delem[profile]['speed'])
            intf["interfaces"][0]["nvPairs"]["ALLOWED_VLANS"]             = delem[profile]['allowed_vlans']
            intf["interfaces"][0]["nvPairs"]["INTF_NAME"]                 = ifname
        if (delem[profile]['mode'] == 'access'):
            intf["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"]         = delem[profile]['bpdu_guard'].lower()
            intf["interfaces"][0]["nvPairs"]["PORTTYPE_FAST_ENABLED"]     = str(delem[profile]['port_type_fast']).lower()
            intf["interfaces"][0]["nvPairs"]["MTU"]                       = str(delem[profile]['mtu'])
            intf["interfaces"][0]["nvPairs"]["SPEED"]                     = str(delem[profile]['speed'])
            intf["interfaces"][0]["nvPairs"]["ACCESS_VLAN"]               = delem[profile]['access_vlan']
            intf["interfaces"][0]["nvPairs"]["INTF_NAME"]                 = ifname
        if (delem[profile]['mode'] == 'routed'):
            intf["interfaces"][0]["nvPairs"]["INTF_VRF"]                  = delem[profile]['int_vrf']
            intf["interfaces"][0]["nvPairs"]["IP"]                        = str(delem[profile]['ipv4_addr'])
            if (delem[profile]['ipv4_addr'] != ''):
                intf["interfaces"][0]["nvPairs"]["PREFIX"]                = str(delem[profile]['ipv4_mask_len'])
            else:
                intf["interfaces"][0]["nvPairs"]["PREFIX"]                = ''
            intf["interfaces"][0]["nvPairs"]["ROUTING_TAG"]               = delem[profile]['route_tag']
            intf["interfaces"][0]["nvPairs"]["MTU"]                       = str(delem[profile]['mtu'])
            intf["interfaces"][0]["nvPairs"]["SPEED"]                     = str(delem[profile]['speed'])
            intf["interfaces"][0]["nvPairs"]["INTF_NAME"]                 = ifname
        if (delem[profile]['mode'] == 'monitor'):
            intf["interfaces"][0]["nvPairs"]["INTF_NAME"]                 = ifname
        if (delem[profile]['mode'] == 'epl_routed'):
            intf["interfaces"][0]["nvPairs"]["IP"]                        = str(delem[profile]['ipv4_addr'])
            intf["interfaces"][0]["nvPairs"]["PREFIX"]                    = str(delem[profile]['ipv4_mask_len'])
            intf["interfaces"][0]["nvPairs"]["IPv6"]                      = str(delem[profile]['ipv6_addr'])
            intf["interfaces"][0]["nvPairs"]["IPv6_PREFIX"]                = str(delem[profile]['ipv6_mask_len'])
            intf["interfaces"][0]["nvPairs"]["ROUTING_TAG"]               = delem[profile]['route_tag']
            intf["interfaces"][0]["nvPairs"]["MTU"]                       = str(delem[profile]['mtu'])
            intf["interfaces"][0]["nvPairs"]["SPEED"]                     = str(delem[profile]['speed'])
            intf["interfaces"][0]["nvPairs"]["INTF_NAME"]                 = ifname

        if (delem[profile]['mode'] != 'monitor'):
            intf["interfaces"][0]["nvPairs"]["DESC"]                      = delem[profile]['description']
            if (delem[profile]['cmds'] is None):
                intf["interfaces"][0]["nvPairs"]["CONF"]                  = ""
            else:
                intf["interfaces"][0]["nvPairs"]["CONF"]                  = "\n".join(delem[profile]['cmds'])
            intf["interfaces"][0]["nvPairs"]["ADMIN_STATE"]               = str(delem[profile]['admin_state']).lower()

    # New Interfaces
    def dcnm_get_intf_payload (self, delem, sw):

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
                    "nvPairs": {
                    }
                }
            ],
            "skipResourceCheck": str(True).lower()
        }

        # Each interface type will have a different profile name. Set that based on the interface type and use that
        # below to extract the required parameters

        # Monitor ports are not put into diff_deploy, since they don't have any
        # commands to be executed on switch. This will affect the idempotence
        # check
        if (delem['profile']['mode'] == 'monitor'):
            intf.update ({"deploy" : False})
        else:
            intf.update ({"deploy" : delem['deploy']})

        # Each type of interface and mode will have a different set of params.
        # First fill in the params common to all interface types and modes

        #intf.update ({"interfaceType"  : self.int_types[delem['type']]})

        if ('vpc' == delem['type']):
            intf["interfaces"][0].update ({"serialNumber"  : str(self.vpc_ip_sn[sw])})
        else:
            intf["interfaces"][0].update ({"serialNumber"  : str(self.ip_sn[sw])})

        intf["interfaces"][0].update ({"interfaceType" : self.int_types[delem['type']]})
        intf["interfaces"][0].update ({"fabricName"    : self.fabric})

        if ('profile' not in delem.keys()):
            # for state 'deleted', 'profile' construct is not included. So just update the ifName here
            # and return. Rest of the code is all 'profile' specific and hence not required for 'deleted'

            ifname, port_id = self.dcnm_intf_get_if_name (delem['name'], delem['type'])
            intf["interfaces"][0].update ({"ifName"        : ifname})
            return intf

        pol_ind_str = delem['type'] + '_' + delem['profile']['mode']
        #intf.update ({"policy" : self.pol_types[delem['profile']['mode']]})
        intf.update ({"policy" : self.pol_types[pol_ind_str]})
        intf.update ({"interfaceType" : self.int_types[delem['type']]})

        # Rest of the data in the dict depends on the interface type and the template

        if ('pc' == delem['type']):
            self.dcnm_intf_get_pc_payload(delem, intf, 'profile')
        if ('sub_int' == delem['type']):
            self.dcnm_intf_get_sub_intf_payload(delem, intf, 'profile')
        if ('lo' == delem['type']):
            self.dcnm_intf_get_loopback_payload (delem, intf, 'profile')
        if ('vpc' == delem['type']):
            self.dcnm_intf_get_vpc_payload(delem, intf, 'profile')
        if ('eth' == delem['type']):
            self.dcnm_intf_get_eth_payload(delem, intf, 'profile')

            # Ethernet interface payload does not have interfaceType and skipResourceCheck flags. Pop
            # them out
            intf.pop('skipResourceCheck')

        return intf

    def dcnm_intf_merge_intf_info (self, intf_info, if_head):

        if (not if_head):
            if_head.append(intf_info)
            return

        for item in if_head:

            if (item['policy'] == intf_info['policy']):
                item['interfaces'].append(intf_info['interfaces'][0])
                return
        if_head.append(intf_info)

    def dcnm_intf_get_want(self):

        if (None is self.config):
            return

        if not self.intf_info:
            return

        # self.intf_info is a list of directories each having config related to a particular interface

        for delem in self.intf_info:
            if (any('profile' in key for key in delem)):
                for sw in delem['switch']:
                    intf_payload = self.dcnm_get_intf_payload (delem, sw)
                    if (intf_payload not in self.want):
                        self.want.append(intf_payload)

    def dcnm_intf_get_intf_info(self, ifName, serialNumber, ifType):

        # For VPC interfaces the serialNumber will be a combibed one. But GET on interface cannot
        # pass this combined serial number. We will have to pass individual ones

        if (ifType == 'INTERFACE_VPC'):
            sno = serialNumber.split('~')[0]
        else:
            sno = serialNumber

        path = '/rest/interface?serialNumber=' + sno + '&ifName=' +  ifName
        resp = dcnm_send (self.module, 'GET', path)

        if ('DATA' in resp and resp['DATA']):
            return resp['DATA'][0]
        else:
            return []

    def dcnm_intf_get_intf_info_from_dcnm(self, intf):

        return self.dcnm_intf_get_intf_info (intf['ifName'], intf['serialNumber'], intf['interfaceType'])

    def dcnm_intf_get_have_all (self, sw):

        # Check if you have already got the details for this switch
        if (sw in self.have_all_list):
            return

        # Check if the serial number is a combined one which will be the case for vPC interfaces.
        # If combined, then split it up and pass one of the serial numbers and not the combined one.

        if ('~' in self.ip_sn[sw]):
            sno = self.ip_sn[sw].split('~')[0]
        else:
            sno = self.ip_sn[sw]

        # GET all interfaces
        path = '/rest/interface/detail?serialNumber=' + sno

        resp = dcnm_send(self.module, 'GET', path)

        if ('DATA' in resp and resp['DATA']):
            self.have_all.extend(resp['DATA'])
            self.have_all_list.append(sw)
        else:
            self.have_all_list.append(sw)
            return []

        # adminStatus in all_int_raw will give the deployed status. For deployed interfaces
        # adminStatus will be 1 and ifIndex will also be allocated and non zero

    def dcnm_intf_get_have(self):

        if (not self.want):
            return

        # We have all the requested interface config in self.want. Interfaces are grouped together based on the
        # policy string and the interface name in a single dict entry.

        for elem in self.want:
           for intf in elem['interfaces']:
               # For each interface present here, get the information that is already available
               # in DCNM. Based on this information, we will create the required payloads to be sent
               # to the DCNM controller based on the requested

               # Fetch the information from DCNM w.r.t to the interafce that we have in self.want
               intf_payload = self.dcnm_intf_get_intf_info_from_dcnm(intf)

               if (intf_payload):
                   self.have.append(intf_payload)

    def dcnm_intf_compare_elements (self, name, sno, fabric, ie1, ie2, k, state):

        # unicode encoded strings must be decoded to get proper strings which is required
        # for comparison purposes

        if sys.version_info[0] >= 3:
            # Python version 3 onwards trfeats unicode as strings. No special treatment is required
            e1 = ie1
            e2 = ie2
        else:
            if (isinstance(ie1, unicode)):
               e1 = ie1.encode('utf-8')
            else:
               e1 = ie1
            if (isinstance(ie2, unicode)):
               e2 = ie2.encode('utf-8')
            else:
               e2 = ie2

        # The keys in key_translate represent a concatenated string. We should split
        # these strings and then compare the values
        key_translate = ['MEMBER_INTERFACES', 'CONF', 'PEER1_MEMBER_INTERFACES', 'PEER2_MEMBER_INTERFACES', 'PEER1_PO_CONF', 'PEER2_PO_CONF']

        # Some keys have values given as a list which is encoded into a
        # string. So split that up into list and then use 'set' to process
        # the same irrespective of the order of elements
        if (k in key_translate):
            # CONF, PEER1_PO_CONF and PEER2_PO_CONF has '\n' joining the commands
            # MEMBER_INTERFACES, PEER1_MEMBER_INTERFACES, and PEER2_MEMBER_INTERFACES
            # have ',' joining differnet elements. So use a multi-delimiter split
            # to split with any delim
            t_e1 = set(re.split(r'[\n,]', e1.strip()))
            t_e2 = set(re.split(r'[\n,]', e2.strip()))
        else:
            if (isinstance(e1, str)):
                t_e1 = e1.lower()
            else:
                t_e1 = e1
            if (isinstance(e2, str)):
                t_e2 = e2.lower()
            else:
                t_e2 = e2

        if (t_e1 != t_e2):
            if ((state == 'replaced') or (state == 'overridden')):
                 return 'add'
            elif (state == 'merged'):
                # If the key is included in config, then use the value from want.
                # If the key is not included in config, then use the value from
                # have.

                # Match and find the corresponding PB input.

                match_pb = [pb for pb in self.pb_input if ((name.lower() == pb['ifname'].lower()) and
                                                       (sno == pb['sno']) and
                                                       (fabric == pb['fabric']))]

                pb_keys = list(match_pb[0].keys())
                if (self.keymap[k] not in pb_keys):
                    # Copy the value from have, because for 'merged' state we
                    # should leave values that are not specified in config as is.
                    # We copy 'have' because, the validate input would have defaulted the
                    # values for non-mandatory objects.
                    return 'copy_and_add'
                else:
                    return 'add'
        return 'dont_add'

    def dcnm_intf_can_be_added (self, want):

        name    = want['interfaces'][0]['ifName']
        sno     = want['interfaces'][0]['serialNumber']
        fabric  = want['interfaces'][0]['fabricName']

        match_have = [have for have in self.have_all if ((name.lower() == have['ifName'].lower()) and
                                               (sno == have['serialNo']) and
                                               (fabric == have['fabricName']))]
        if (match_have):
            if ((match_have[0]['complianceStatus'] != 'In-Sync') and
                (match_have[0]['complianceStatus'] != 'Pending')):
                return True
            else:
                return False
        return True

    def dcnm_intf_compare_want_and_have (self, state):

        for want in self.want:

            delem   = {}
            action  = ''
            new     = False
            add     = False
            name    = want['interfaces'][0]['ifName']
            sno     = want['interfaces'][0]['serialNumber']
            fabric  = want['interfaces'][0]['fabricName']
            deploy  = want['deploy']

            intf_changed = False

            want.pop('deploy')

            match_have = [d for d in self.have if ((name.lower() == d['interfaces'][0]['ifName'].lower()) and
                                                   (sno == d['interfaces'][0]['serialNumber']))]

            if (not match_have):
                changed_dict = copy.deepcopy(want)

                if ((state == 'merged') or (state == 'replaced') or (state == 'overridden')):
                    action = 'add'
            else:
                wkeys = list(want.keys())
                if ('skipResourceCheck' in wkeys):
                    wkeys.remove('skipResourceCheck')
                if ('interfaceType' in wkeys):
                    wkeys.remove('interfaceType')

                for d in match_have:

                    changed_dict = copy.deepcopy(want)
                    if ('skipResourceCheck' in changed_dict.keys()):
                        changed_dict.pop('skipResourceCheck')

                    # First check if the policies are same for want and have. If they are different, we cannot compare
                    # the profiles because each profile will have different elements. As per PRD, if policies are different
                    # we should not merge the information. For now we will assume we will oerwrite the same. Don't compare
                    # rest of the structure. Overwrite with waht ever is in want

                    if (want['policy'] != d['policy']):
                        action = 'update'
                        continue
                    else :
                        for k in wkeys:
                            if (k == 'interfaces'):
                                if_keys = list(want[k][0].keys())
                                if_keys.remove('interfaceType')
                                changed_dict[k][0].pop('interfaceType')

                                # 'have' will not contain the fabric name object. So do not try to compare that. This
                                # is especially true for Ethernet interfaces. Since a switch can belong to only one fabric
                                # the serial number should be unique across all fabrics
                                if_keys.remove('fabricName')
                                changed_dict[k][0].pop('fabricName')
                                for ik in if_keys:
                                    if (ik == 'nvPairs'):
                                        nv_keys = list(want[k][0][ik].keys())
                                        for nk in nv_keys:
                                            # HAVE may have an entry with a list # of interfaces. Check all the
                                            # interface entries for a match.  Even if one entry matches do not
                                            # add the interface
                                            for index in range (len(d[k])):
                                                res = self.dcnm_intf_compare_elements (name, sno, fabric,
                                                                                       want[k][0][ik][nk],
                                                                                       d[k][index][ik][nk], nk, state)
                                                if (res == 'dont_add'):
                                                  break
                                            if (res == 'copy_and_add'):
                                               want[k][0][ik][nk] = d[k][0][ik][nk]
                                               changed_dict[k][0][ik][nk] = d[k][0][ik][nk]
                                            if (res != 'dont_add'):
                                                action = 'update'
                                            else:
                                                # Keys and values match. Remove from changed_dict
                                                changed_dict[k][0][ik].pop(nk)
                                    else:
                                        # HAVE may have an entry with a list # of interfaces. Check all the
                                        # interface entries for a match.  Even if one entry matches do not
                                        # add the interface
                                        for index in range (len(d[k])):
                                            res = self.dcnm_intf_compare_elements (name, sno, fabric,
                                                                                   want[k][0][ik],
                                                                                   d[k][0][ik], ik, state)
                                            if (res == 'dont_add'):
                                              break
                                        if (res == 'copy_and_add'):
                                           want[k][0][ik] = d[k][0][ik]
                                           changed_dict[k][0][ik] = d[k][0][ik]
                                        if (res != 'dont_add'):
                                            action = 'update'
                                        else:
                                            # Keys and values match. Remove from changed_dict
                                            if (ik != 'ifName'):
                                                changed_dict[k][0].pop(ik)
                            else:
                                res = self.dcnm_intf_compare_elements (name, sno, fabric,
                                                                       want[k], d[k], k, state)

                                if (res == 'copy_and_add'):
                                   want[k] = d[k]
                                   changed_dict[k] = d[k]
                                if (res != 'dont_add'):
                                    action = 'update'
                                else:
                                    # Keys and values match. Remove from changed_dict.
                                    changed_dict.pop(k)

            if (action == 'add'):
                self.dcnm_intf_merge_intf_info(want, self.diff_create)
                # Add the changed_dict to self.changed_dict
                self.changed_dict[0][state].append(changed_dict)
                intf_changed = True
            elif (action == 'update'):
                # Remove the 'interfaceType' key from 'want'. It is not required for 'replace'
                if (want.get('interfaceType', None) != None):
                    want.pop('interfaceType')
                self.dcnm_intf_merge_intf_info(want, self.diff_replace)
                # Add the changed_dict to self.changed_dict
                self.changed_dict[0][state].append(changed_dict)
                intf_changed = True

            # if deploy flag is set to True, add the information so that this interface will be deployed
            if (str(deploy) == 'True'):
                # Add to diff_deploy,
                #   1. if intf_changed is True
                #   2. if intf_changed is Flase, then if 'complianceStatus is
                #      False then add to diff_deploy.
                #   3. Do not add otherwise

                if (False is intf_changed):
                    rc = self.dcnm_intf_can_be_added (want)
                else:
                    rc = True

                if (True is rc):
                    delem['serialNumber'] = sno
                    delem['ifName']       = name
                    self.diff_deploy.append(delem)
                    self.changed_dict[0]['deploy'].append(copy.deepcopy(delem))

    def dcnm_intf_get_diff_replaced(self):

        self.diff_create  = []
        self.diff_delete  = [[],[],[],[],[]]
        self.diff_deploy  = []
        self.diff_replace = []

        for cfg in self.config:
            self.dcnm_intf_process_config(cfg)

        # Compare want[] and have[] and build a list of dicts containing interface information that
        # should be sent to DCNM for updation. The list can include information on interfaces which
        # are already presnt in self.have and which differ in the values for atleast one of the keys

        self.dcnm_intf_compare_want_and_have ('replaced')

    def dcnm_intf_get_diff_merge(self):

        self.diff_create = []
        self.diff_delete = [[],[],[],[],[]]
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

        self.dcnm_intf_compare_want_and_have ('merged')

    def dcnm_compare_default_payload (self, intf, have):

        if(intf.get('policy') != have.get('policy')):
            return 'DCNM_INTF_NOT_MATCH' 

        intf_nv = intf.get('interfaces')[0].get('nvPairs')
        have_nv = have.get('interfaces')[0].get('nvPairs')

        if(intf_nv.get('INTF_VRF') != have_nv.get('INTF_VRF')):
            return 'DCNM_INTF_NOT_MATCH' 
        if(intf_nv.get('IP') != have_nv.get('IP')):
            return 'DCNM_INTF_NOT_MATCH' 
        if(intf_nv.get('PREFIX') != have_nv.get('PREFIX')):
            return 'DCNM_INTF_NOT_MATCH' 
        if(intf_nv.get('ROUTING_TAG') != have_nv.get('ROUTING_TAG')):
            return 'DCNM_INTF_NOT_MATCH' 
        if(intf_nv.get('MTU') != have_nv.get('MTU')):
            return 'DCNM_INTF_NOT_MATCH' 
        if(intf_nv.get('SPEED') != have_nv.get('SPEED')):
            return 'DCNM_INTF_NOT_MATCH' 
        if(intf_nv.get('DESC') != have_nv.get('DESC')):
            return 'DCNM_INTF_NOT_MATCH' 
        if(intf_nv.get('CONF') != have_nv.get('CONF')):
            return 'DCNM_INTF_NOT_MATCH' 
        if(intf_nv.get('ADMIN_STATE') != have_nv.get('ADMIN_STATE')):
            return 'DCNM_INTF_NOT_MATCH' 
        return 'DCNM_INTF_MATCH'

    def dcnm_intf_get_default_eth_payload(self, ifname, sno, fabric):

        # default payload to be sent to DCNM for override case
        eth_payload = {
            "policy": "int_routed_host_11_1",
            "interfaces": [
            {
                "interfaceType": "INTERFACE_ETHERNET",
                "serialNumber": sno,
                "ifName": "",
                "fabricName": fabric,
                "nvPairs": {
                    "interfaceType": "INTERFACE_ETHERNET",
                    "INTF_VRF": "",
                    "IP": "",
                    "PREFIX": "",
                    "ROUTING_TAG": "",
                    "MTU": "9216",
                    "SPEED": "Auto",
                    "DESC": "",
                    "CONF": "no shutdown",
                    "ADMIN_STATE": "true",
                    "INTF_NAME": ifname
                }
           }]
        }

        eth_payload ['interfaces'][0]["ifName"]       = ifname
        eth_payload ['interfaces'][0]["serialNumber"] = sno
        eth_payload ['interfaces'][0]["fabricName"]   = fabric

        return eth_payload

    def dcnm_intf_can_be_replaced(self, have):

        for item in self.pb_input:
            # For overridden state, we will not touch anything that is present in incoming config, 
            # because those interfaces will anyway be modified in the current run
            if ((self.module.params['state'] == 'overridden') and
                (item['ifname'] == have['ifName'])):
                return False, item['ifname']
            if (item.get('members')):
                if (have['ifName'] in \
                    [self.dcnm_intf_get_if_name(mem, 'eth')[0] for mem in item['members']]):
                    return False, item['ifname']
            elif ((item.get('peer1_members')) or (item.get('peer2_members'))):
                if ((have['ifName'] in \
                    [self.dcnm_intf_get_if_name(mem, 'eth')[0] for mem in item['peer1_members']]) or
                   (have['ifName'] in \
                    [self.dcnm_intf_get_if_name(mem, 'eth')[0] for mem in item['peer2_members']])):
                    return False, item['ifname']
        return True, None

    def dcnm_intf_process_config(self, cfg):

        processed = []

        if(None is cfg.get('switch', None)):
            return
        for sw in cfg['switch']:

            sno = self.ip_sn[sw]

            if (sno not in processed):
                processed.append (sno)

                # If the switch is part of VPC pair, then a GET on any serial number will fetch details of 
                # both the switches. So check before adding to have_all

                if not any(d.get('serialNo', None) == self.ip_sn[sw] for d in self.have_all):
                    self.dcnm_intf_get_have_all(sw)

    def dcnm_intf_get_diff_overridden(self, cfg):

        self.diff_create  = []
        self.diff_delete  = [[],[],[],[],[]]
        self.diff_deploy  = []
        self.diff_replace = []

        if ((cfg is not None) and (cfg != [])):
            self.dcnm_intf_process_config(cfg)
        elif ([] == cfg):
            for address in self.ip_sn.keys():
                # the given switch may be part of a VPC pair. In that case we
                # need to get interface information using one switch which returns interfaces
                # from both the switches
                if not any(d.get('serialNo', None) == self.ip_sn[address] for d in self.have_all):
                    self.dcnm_intf_get_have_all(address)
        elif (self.config):
            # compute have_all for every switch
            for config in self.config:
                self.dcnm_intf_process_config(config)

        req_objs = ['ifName', 'serialNo', 'fabricName', 'ifType', 'isPhysical', 'deletable']
        filtered_dict = [{k:v for k,v in d.items() if k in req_objs} for d in self.have_all]

        del_list   = []
        defer_list = []

        for have in self.have_all:

            delem   = {}
            name    = have['ifName']
            sno     = have['serialNo']
            fabric  = have['fabricName']

            if ((have['ifType'] == 'INTERFACE_ETHERNET') and
                ((str(have['isPhysical']).lower() != 'none') and (str(have['isPhysical']).lower() == 'true'))):

                if (str(have['deletable']).lower() == 'false'):
                    # Add this 'have to a deferred list. We will process this list once we have processed all the 'haves'
                    defer_list.append(have)
                    continue

                uelem = self.dcnm_intf_get_default_eth_payload(name, sno, fabric)
                # Before we add the interface to replace list, check if the default payload is same as 
                # what is already present. If both are same, skip the interface. 
                # So during idempotence, we may add the same interface again if we don't compare

                intf = self.dcnm_intf_get_intf_info(have['ifName'], have['serialNo'], have['ifType'])
                if (self.dcnm_compare_default_payload (uelem, intf) == 'DCNM_INTF_MATCH'):
                    continue

                if (uelem is not None):
                    # Before defaulting ethernet interfaces, check if they are
                    # member of any port-channel. If so, do not default that
                    rc, intf = self.dcnm_intf_can_be_replaced(have)
                    if (True == rc):
                        self.dcnm_intf_merge_intf_info (uelem, self.diff_replace)
                        self.changed_dict[0]['replaced'].append(copy.deepcopy(uelem))
                        delem['serialNumber'] = sno
                        delem['ifName']       = name
                        self.diff_deploy.append(delem)
                        self.changed_dict[0]['deploy'].append(copy.deepcopy(delem))

            # Sub-interafces are returned as INTERFACE_ETHERNET in have_all. So do an
            # additional check to see if it is physical. If not assume it to be sub-interface
            # for now. We will have to re-visit this check if there are additional non-physical
            # interfaces which have the same ETHERNET interafce type. For e.g., FEX ports

            if ((have['ifType']  == 'INTERFACE_PORT_CHANNEL') or
                (have['ifType']  == 'INTERFACE_LOOPBACK') or
                (have['ifType']  == 'SUBINTERFACE') or
                (have['ifType']  == 'INTERFACE_VPC') or
                ((have['ifType'] == 'INTERFACE_ETHERNET') and
                 ((str(have['isPhysical']).lower() == 'none') or (str(have['isPhysical']).lower() == "false")))):

                # Certain interfaces cannot be deleted, so check before deleting.
                if (str(have['deletable']).lower() == 'true'):

                    #Port-channel which are created as part of VPC peer link should not be deleted
                    if (have['ifType']  == 'INTERFACE_PORT_CHANNEL'):
                          if (have['alias'] == '"vpc-peer-link"'):
                              continue

                    # Interfaces sometimes take time to get deleted from DCNM. Such interfaces will have 
                    # underlayPolicies set to "None". Such interfaces need not be deleted again

                    if (have['underlayPolicies'] is None):
                        continue

                    # For interfaces that are matching, leave them alone. We will overwrite the config anyway
                    # For all other interfaces, if they are PC, vPC, SUBINT, LOOPBACK, delete them.

                    # Check if this interface is present in want. If yes, ignore the interface, because all
                    # configuration from want will be added to create anyway

                    match_want = [d for d in self.want if ((name.lower() == d['interfaces'][0]['ifName'].lower()) and
                                                           (sno == d['interfaces'][0]['serialNumber']) and
                                                           (fabric == d['interfaces'][0]['fabricName']))]

                    if (not match_want):

                        delem = {}

                        delem["interfaceDbId"] = 0
                        delem["interfaceType"] = have['ifType']
                        delem["ifName"]        = name
                        delem["serialNumber"]  = sno
                        delem["fabricName"]    = fabric

                        self.diff_delete[self.int_index[have['ifType']]].append(delem)
                        self.changed_dict[0]['deleted'].append(copy.deepcopy(delem))
                        del_list.append(have)

        for intf in defer_list:
            # Check if the 'source' for the ethernet interface is one of the interfaces that is already deleted.
            # If so you can default/reset this ethernet interface also

            delem   = {}
            sno     = intf['serialNo']
            fabric  = intf['fabricName']
            name    = intf['underlayPolicies'][0]['source']

            match = [d for d in del_list if ((name.lower() == d['ifName'].lower()) and
                                             (sno in d['serialNo']) and
                                             (fabric == d['fabricName']))]
            if (match):

                uelem = self.dcnm_intf_get_default_eth_payload(intf['ifName'], sno, fabric)

                self.dcnm_intf_merge_intf_info (uelem, self.diff_replace)
                self.changed_dict[0]['replaced'].append(copy.deepcopy(uelem))
                delem['serialNumber'] = sno
                delem['ifName']       = intf['ifName']
                self.diff_deploy.append(delem)
                self.changed_dict[0]['deploy'].append(copy.deepcopy(delem))

        self.dcnm_intf_compare_want_and_have ('overridden')

    def dcnm_intf_get_diff_deleted(self):

        self.diff_create  = []
        self.diff_delete  = [[],[],[],[],[]]
        self.diff_deploy  = []
        self.diff_replace = []

        if ((None is self.config) or (self.config is [])):
            # If no config is specified, then it means we need to delete or
            # reset all interfaces in the fabric.

            # Get the IP addresses from ip_sn. For every IP, get all interfaces
            # and delete/reset all

            for address in self.ip_sn.keys():
                # the given switch may be part of a VPC pair. In that case we
                # need to get interface information using one switch which returns interfaces
                # from both the switches
                if not any(d.get('serialNo', None) == self.ip_sn[address] for d in self.have_all):
                    self.dcnm_intf_get_have_all(address)

            # Now that we have all the interface information we can run override
            # and delete or reset interfaces.
            self.dcnm_intf_get_diff_overridden(None)
        elif (self.config):
            for cfg in self.config:
                if (cfg.get('name', None) is not None):
                    processed = []
                    have_all  = []

                    # If interface name alone is given, then delete or reset the
                    # interface on all switches in the fabric
                    switches = cfg.get('switch', None)

                    if (switches is None):
                        switches = self.ip_sn.keys()
                    else:
                        switches = cfg['switch']

                    for sw in switches:
                        intf  = {}
                        delem = {}

                        if_name, if_type = self.dcnm_extract_if_name(cfg)

                        # Check if the interface is present in DCNM
                        intf['interfaceType'] = if_type
                        if (if_type == 'INTERFACE_VPC'):
                          intf['serialNumber']  = self.vpc_ip_sn[sw]
                        else:
                          intf['serialNumber']  = self.ip_sn[sw]
                        intf['ifName']        = if_name

                        if (intf['serialNumber'] not in processed):
                            processed.append(intf['serialNumber'])
                        else:
                            continue

                        # Ethernet interfaces cannot be deleted
                        if (if_type == 'INTERFACE_ETHERNET'):

                            if (sw not in have_all):
                                have_all.append (sw)
                                self.dcnm_intf_get_have_all (sw)

                            # Get the matching interface from have_all
                            match_have = [have for have in self.have_all if ((intf['ifName'].lower() == have['ifName'].lower()) and
                                                                             (intf['serialNumber'] == have['serialNo']))][0]
                            if (match_have and (str(match_have['isPhysical']).lower() != 'none') and (str(match_have['isPhysical']).lower() == 'true')):

                                if (str(match_have['deletable']).lower() == 'false'):
                                    continue

                                uelem = self.dcnm_intf_get_default_eth_payload(intf['ifName'], intf['serialNumber'], self.fabric)
                                intf_payload = self.dcnm_intf_get_intf_info_from_dcnm(intf)

                                # Before we add the interface to replace list, check if the default payload is same as 
                                # what is already present. If both are same, skip the interface. This is required specifically
                                # for ethernet interfaces because they don't actually get deleted. they will only be defaulted.
                                # So during idempotence, we may add the same interface again if we don't compare
                                if (intf_payload != []):
                                    if (self.dcnm_compare_default_payload (uelem, intf_payload) == 'DCNM_INTF_MATCH'):
                                        continue

                                if (uelem is not None):
                                    # Before defaulting ethernet interfaces, check if they are
                                    # member of any port-channel. If so, do not default that
                                    rc, iface = self.dcnm_intf_can_be_replaced(match_have)
                                    if (True == rc):
                                        self.dcnm_intf_merge_intf_info (uelem, self.diff_replace)
                                        self.changed_dict[0]['replaced'].append(copy.deepcopy(uelem))
                                        delem['serialNumber'] = intf['serialNumber']
                                        delem['ifName']       = if_name
                                        self.diff_deploy.append(delem)
                        else:
                            intf_payload = self.dcnm_intf_get_intf_info_from_dcnm(intf)

                            if (intf_payload != []):
                                delem["interfaceDbId"] = 0
                                delem["interfaceType"] = if_type
                                delem["ifName"]        = if_name
                                delem["serialNumber"]  = intf['serialNumber']
                                delem["fabricName"]    = self.fabric

                                self.diff_delete[self.int_index[if_type]].append(delem)
                                self.changed_dict[0]['deleted'].append(copy.deepcopy(delem))
                else:
                    self.dcnm_intf_get_diff_overridden(cfg)

    def dcnm_extract_if_name(self, cfg):

        if (cfg['name'][0:2].lower() == 'po'):
            if_name,port_id = self.dcnm_intf_get_if_name (cfg['name'], 'pc')
            if_type = 'INTERFACE_PORT_CHANNEL'
        elif (cfg['name'][0:2].lower() == 'lo'):
            if_name,port_id = self.dcnm_intf_get_if_name (cfg['name'], 'lo')
            if_type = 'INTERFACE_LOOPBACK'
        elif (cfg['name'][0:3].lower() == 'eth'):
            if ('.' not in cfg['name']):
                if_name,port_id = self.dcnm_intf_get_if_name (cfg['name'], 'eth')
                if_type = 'INTERFACE_ETHERNET'
            else:
                if_name,port_id = self.dcnm_intf_get_if_name (cfg['name'], 'sub_int')
                if_type = 'SUBINTERFACE'
        elif (cfg['name'][0:3].lower() == 'vpc'):
            if_name,port_id = self.dcnm_intf_get_if_name (cfg['name'], 'vpc')
            if_type = 'INTERFACE_VPC'
        else:
            if_name = ''
            if_type = ''
        return if_name, if_type

    def dcnm_intf_get_diff_query(self):

      for info in self.intf_info:
          sno = self.ip_sn[info['switch'][0]]
          if (info['name'] == ''):
              # GET all interfaces
              path = '/rest/interface/detail?serialNumber=' + sno
          else:
              ifname, if_type = self.dcnm_extract_if_name (info)
              # GET a specific interface
              path = '/rest/interface?serialNumber=' + sno + '&ifName=' +  ifname

          resp = dcnm_send (self.module, 'GET', path)

          if ('DATA' in resp and resp['DATA']):
              self.diff_query.extend(resp['DATA'])
      self.changed_dict[0]['query'].extend(self.diff_query)
      self.result['response'].extend(self.diff_query)

    def dcnm_parse_response (self, resp):

        failed = False

        succ_resp = {
            "DATA": {},
            "MESSAGE": "OK",
            "METHOD": "POST",
            "REQUEST_PATH": "",
            "RETURN_CODE": 200
        }

        # Get a list of entities from the deploy. We will have to check
        # all the responses before we declare changed as True or False

        entities = self.dcnm_intf_get_entities_list (self.diff_deploy)

        ent_resp = {}
        for ent in entities:
            ent_resp[ent] = 'No Error'
            if (isinstance(resp['DATA'], list)):
                for data in resp['DATA']:
                    host = data.get('entity')
                    if (host):
                        if (self.hn_sn.get(host) == ent):
                            ent_resp[ent] = data.get('message')
                    else:
                        ent_resp[ent] = 'No Error'
            elif (isinstance(resp['DATA'], str)):
                ent_resp[ent] = resp['DATA']

        for ent in entities:
            if (ent_resp[ent] == "No Error"):
                # Consider this case as success.
                succ_resp['REQUEST_PATH'] = resp['REQUEST_PATH']
                succ_resp['MESSAGE']      = 'OK'
                succ_resp['METHOD']       = 'DEPLOY'
                return succ_resp, True
            elif ((ent_resp[ent] == 'No Commands to execute.') or
                  (ent_resp[ent] == 'Failed to fetch policies') or
                  (ent_resp[ent] == 'Failed to fetch switch configuration')):
                # Consider this case as success.
                succ_resp['REQUEST_PATH'] = resp['REQUEST_PATH']
                succ_resp['MESSAGE']      = 'OK'
                succ_resp['METHOD']       = 'DEPLOY'
                succ_resp['ORIG_MSG']     = ent_resp[ent]

                changed = False
            else:
                changed = False
                failed = True
                break

        if (failed):
            return resp, False
        else:
            return succ_resp, False

    def dcnm_intf_send_message_handle_retry (self, action, path, payload, cmd):

        count = 1
        while (count < 20):

            resp = dcnm_send(self.module, action, path, payload)

            # No commands to execute is normal when you try to deploy/delete an
            # interface to switch and there is no change.
            # Consider that as success and mark the change flag as 'False; to indicate
            # nothinbg actually changed

            if ((resp.get('MESSAGE') == 'OK') and (resp.get('RETURN_CODE') == 200)):
                return resp, True

            presp, changed = self.dcnm_parse_response (resp)
            resp = presp

            count = count + 1
            time.sleep(0.1)

        return resp, False

    def dcnm_intf_get_entities_list (self, deploy):

        sn_list  = []
        ip_addr  = []
        entities = []
        usno     = []

        [[sn_list.append(v) for k,v in d.items() if k == 'serialNumber'] for d in deploy]

        # For vPC cases, serial numbers will be a combined one. But deploy responses from the DCNM
        # controller will be based on individual switches. So we will have to split up the serial
        # numbers into individual serial numbers and add to the list

        ulist = set(sn_list)

        vpc = False
        for num in ulist:
            if ('~' in num):
                vpc = True
                slist = num.split('~')
                usno.append(slist[0])
                usno.append(slist[1])

        if (vpc is True):
            ulist = usno
        return ulist

    def dcnm_intf_send_message_to_dcnm (self):

        resp    = None
        changed = False

        delete  = False
        create  = False
        deploy  = False
        replace = False

        path = '/rest/globalInterface'

        # First send deletes and then try create and update. This is because during override, the overriding
        # config may conflict with existing configuration.

        for delem in self.diff_delete:

           if (delem == []):
               continue
           json_payload = json.dumps(delem)
           resp = dcnm_send(self.module, 'DELETE', path, json_payload)

           if ((resp.get('MESSAGE') != 'OK') or (resp.get('RETURN_CODE') != 200)):

               # there may be cases which are not actual failures. retry the
               # action
               resp, rc = self.dcnm_intf_send_message_handle_retry ('DELETE', path,
                                                                    json_payload, 'DELETE')

               # Even if one of the elements succeed, changed must be set to
               # True. Once changed becomes True, then it remains True
               if (False is changed):
                   changed = rc

               if (((resp.get('MESSAGE') != 'OK') and (resp.get('MESSAGE') != 'No Commands to execute.')) or
                   (resp.get('RETURN_CODE') != 200)):
                   self.module.fail_json(msg=resp)
           else:
               changed = True

           delete = changed
           self.result['response'].append(resp)

        resp    = None
#time.sleep(1)

        # In 11.4 version of DCNM, sometimes interfaces don't get deleted
        # completely, but only marked for deletion. They get removed only after a
        # deploy. So we will do a deploy on the deleted elements
        path = '/rest/globalInterface/deploy'
        for delem in self.diff_delete:

           if (delem == []):
               continue
           # Deploy just requires ifName and serialNumber
           [[item.pop('interfaceType'), item.pop('fabricName'), item.pop('interfaceDbId')] for item in delem]
           json_payload = json.dumps(delem)
           resp = dcnm_send(self.module, 'POST', path, json_payload)

        resp    = None

        path = '/rest/interface'
        for payload in self.diff_replace:

            json_payload = json.dumps(payload)
            resp = dcnm_send(self.module, 'PUT', path, json_payload)
            self.result['response'].append(resp)

            if ((resp.get('MESSAGE') != 'OK') or (resp.get('RETURN_CODE') != 200)):
                self.module.fail_json(msg=resp)
            else:
                replace  = True

        resp    = None

#time.sleep(1)

        path = '/rest/globalInterface'
        for payload in self.diff_create:

            json_payload = json.dumps(payload)
            resp = dcnm_send(self.module, 'POST', path, json_payload)
            self.result['response'].append(resp)

            if ((resp.get('MESSAGE') != 'OK') or (resp.get('RETURN_CODE') != 200)):
                self.module.fail_json(msg=resp)
            else:
                create = True

        resp    = None

#time.sleep(1)

        path = '/rest/globalInterface/deploy'
        if (self.diff_deploy):

            json_payload = json.dumps(self.diff_deploy)

            resp = dcnm_send(self.module, 'POST', path, json_payload)

            if ((resp.get('MESSAGE') != 'OK') and (resp.get('RETURN_CODE') != 200)):
                resp, rc = self.dcnm_parse_response (resp)
                changed = rc
            else:
                changed = True

            deploy = changed

            self.result['response'].append(resp)

        resp    = None

        # Do a second deploy. Sometimes even if interfaces are created, they are
        # not being deployed. A second deploy solves the same. Don't worry about
        # the return values

        resp = dcnm_send(self.module, 'POST', path, json_payload)

        resp    = None

        # In overridden and deleted states, if no delete or create is happening and we have
        # only replace, then check the return message for deploy. If it says
        # "No Commands to execute", then the interfaces we are replacing are
        # already in the required state and so consider that a no change
        if ((self.module.params['state'] == 'overridden') or
            (self.module.params['state'] == 'deleted')):
                self.result['changed'] = (delete or create or deploy)
        else:
            if (delete or create or replace or deploy):
                self.result['changed'] = True
            else:
                self.result['changed'] = False

    def dcnm_translate_switch_info(self, config, ip_sn, hn_sn):

       if (None is config):
         return

       for cfg in config:

           index = 0

           if (None is cfg.get('switch', None)):
               continue
           for sw_elem in cfg['switch']:
               addr_info = dcnm_get_ip_addr_info (self.module, sw_elem, ip_sn, hn_sn)
               cfg['switch'][index] = addr_info
               index = index + 1

               # Check if the VPC serial number information is already present. If not fetch that

               if (self.vpc_ip_sn.get (addr_info, None) is None) :
                   sno = self.dcnm_intf_get_vpc_serial_number(addr_info)
                   if ('~' in sno):
                       # This switch is part of VPC pair. Populate the VPC serial number DB
                       self.vpc_ip_sn[addr_info] = sno

def main():

    """ main entry point for module execution
    """
    element_spec = dict(
        fabric=dict(required=True, type='str'),
        config=dict(required=False, type='list'),
        state=dict(type='str', default='merged',
                   choices = ['merged', 'replaced', 'overridden', 'deleted',
                              'query']),
    )

    module = AnsibleModule(argument_spec=element_spec,
                           supports_check_mode=True)

    dcnm_intf = DcnmIntf(module)

    start = datetime.datetime.now()

    if not dcnm_intf.ip_sn:
        dcnm_intf.result['msg'] = "Fabric {} missing on DCNM or does not have any switches".format(dcnm_intf.fabric)
        module.fail_json(msg="Fabric {} missing on DCNM or does not have any switches".format(dcnm_intf.fabric))

    state = module.params['state']
    if not dcnm_intf.config:
        if state == 'merged' or state == 'replaced' or state == 'query':
            module.fail_json(msg="'config' element is mandatory for state '{}', given = '{}'".format(state, dcnm_intf.config))

    dcnm_intf.dcnm_translate_switch_info (dcnm_intf.config, dcnm_intf.ip_sn,
                                          dcnm_intf.hn_sn)

    dcnm_intf.dcnm_intf_copy_config()

    dcnm_intf.dcnm_intf_validate_input()

    # state 'deleted' may not include all the information
    if ((module.params['state'] != 'query') and (module.params['state'] != 'deleted')):
        dcnm_intf.dcnm_intf_get_want()
        dcnm_intf.dcnm_intf_get_have()


    if (module.params['state'] == 'merged'):
        dcnm_intf.dcnm_intf_get_diff_merge()

    if (module.params['state'] == 'replaced'):
        dcnm_intf.dcnm_intf_get_diff_replaced()

    if (module.params['state'] == 'overridden'):
        if (dcnm_intf.config is None):
            dcnm_intf.dcnm_intf_get_diff_overridden([])
        else:
            dcnm_intf.dcnm_intf_get_diff_overridden(None)

    if (module.params['state'] == 'deleted'):
        dcnm_intf.dcnm_intf_get_diff_deleted()

    if (module.params['state'] == 'query'):
        dcnm_intf.dcnm_intf_get_diff_query()

    dcnm_intf.result['diff']   = dcnm_intf.changed_dict

    if (dcnm_intf.diff_create or dcnm_intf.diff_replace or dcnm_intf.diff_deploy or
        dcnm_intf.diff_delete[dcnm_intf.int_index['INTERFACE_PORT_CHANNEL']] or
        dcnm_intf.diff_delete[dcnm_intf.int_index['INTERFACE_VPC']] or
        dcnm_intf.diff_delete[dcnm_intf.int_index['INTERFACE_ETHERNET']] or
        dcnm_intf.diff_delete[dcnm_intf.int_index['SUBINTERFACE']] or
        dcnm_intf.diff_delete[dcnm_intf.int_index['INTERFACE_LOOPBACK']]):
        dcnm_intf.result['changed'] = True
    else:
        module.exit_json(**dcnm_intf.result)

    if module.check_mode:
        module.exit_json(**dcnm_intf.result)

    dcnm_intf.dcnm_intf_send_message_to_dcnm()
    # Sleep for 10 secs to ensure that the DCNM will be set to proper state
    # time.sleep(20)
    module.exit_json(**dcnm_intf.result)

if __name__ == '__main__':
    main()
