#!/usr/bin/python
#
# Copyright (c) 2020-2025 Cisco and/or its affiliates.
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
__author__ = "Chris Van Heuveln, Shrishail Kariyappanavar, Karthik Babu Harichandra Babu, Praveen Ramoorthy"

DOCUMENTATION = """
---
module: dcnm_network
short_description: Add and remove Networks from a ND managed VXLAN fabric.
version_added: "0.9.0"
description:
    - "Add and remove Networks from a ND managed VXLAN fabric."
    - "For multisite (MSD) fabrics, child fabric configurations can be specified using the child_fabric_config parameter"
    - "The attribute _fabric_type (standalone, multisite_parent, multisite_child) is automatically detected and should not be manually specified by the user"
author: Chris Van Heuveln(@chrisvanheuveln), Shrishail Kariyappanavar(@nkshrishail) Praveen Ramoorthy(@praveenramoorthy)
options:
  fabric:
    description:
    - Name of the target fabric for network operations
    type: str
    required: yes
  _fabric_details:
    description:
    - INTERNAL PARAMETER - DO NOT USE
    - Fabric details dictionary automatically provided by the action plugin
    - Contains fabric_type, cluster_name, and nd_version information
    - This parameter is used internally by the action plugin for MSD/MFD fabric processing
    type: dict
    required: false
    suboptions:
      fabric_type:
        description:
        - Type of fabric (multicluster_parent, multicluster_child, multisite_parent, multisite_child, standalone)
        type: str
        required: true
      cluster_name:
        description:
        - Name of the cluster if applicable
        type: str
        required: false
      nd_version:
        description:
        - ND/NDFC version number used for API path selection
        - Automatically provided by action plugin
        - Module will fail if this is not provided by action plugin
        type: float
        required: true
  _fabric_type:
    description:
    - INTERNAL PARAMETER - DO NOT USE - DEPRECATED
    - This parameter is deprecated in favor of _fabric_details
    - Kept for backward compatibility only
    type: str
    required: false
    default: standalone
    choices: ['multisite_child', 'standalone', 'multisite_parent', 'multicluster_parent', 'multicluster_child']
  state:
    description:
    - The state of ND after module completion.
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
    - List of details of networks being managed. Not required for state deleted
    type: list
    elements: dict
    suboptions:
      net_name:
        description:
        - Name of the network being managed
        type: str
        required: true
      vrf_name:
        description:
        - Name of the VRF to which the network belongs to
        - This field is required for L3 Networks. VRF name should not be specified
          or may be specified as "" for L2 networks
        type: str
      net_id:
        description:
        - ID of the network being managed
        - If not specified in the playbook, ND will auto-select an available net_id
        type: int
        required: false
      net_template:
        description:
        - Name of the config template to be used
        type: str
        default: 'Default_Network_Universal'
      net_extension_template:
        description:
        - Name of the extension config template to be used
        type: str
        default: 'Default_Network_Extension_Universal'
      vlan_id:
        description:
        - VLAN ID for the network.
        - If not specified in the playbook, ND will auto-select an available vlan_id
        type: int
        required: false
      routing_tag:
        description:
        - Routing Tag for the network profile
        type: int
        required: false
        default: 12345
      gw_ip_subnet:
        description:
        - Gateway with subnet for the network
        type: str
        required: false
      is_l2only:
        description:
        - Layer 2 only network
        - If specified as true, VRF Name(vrf_name) should not be specified or can be
          specified as ""
        type: bool
        required: false
        default: false
      vlan_name:
        description:
        - Name of the vlan configured
        - if > 32 chars enable, system vlan long-name on switch
        type: str
        required: false
      int_desc:
        description:
        - Description for the interface
        type: str
        required: false
      mtu_l3intf:
        description:
        - MTU for Layer 3 interfaces
        - Configured MTU value should be in range 68-9216
        type: int
        required: false
      arp_suppress:
        description:
        - ARP suppression
        - ARP suppression is only supported if SVI is present when Layer-2-Only is not enabled
        type: bool
        required: false
        default: false
      dhcp_srvr1_ip:
        description:
        - DHCP relay IP address of the first DHCP server
        - Not applicable at Multisite parent fabric level
        type: str
        required: false
      dhcp_srvr1_vrf:
        description:
        - VRF ID of first DHCP server
        - Not applicable at Multisite parent fabric level
        type: str
        required: false
      dhcp_srvr2_ip:
        description:
        - DHCP relay IP address of the second DHCP server
        - Not applicable at Multisite parent fabric level
        type: str
        required: false
      dhcp_srvr2_vrf:
        description:
        - VRF ID of second DHCP server
        - Not applicable at Multisite parent fabric level
        type: str
        required: false
      dhcp_srvr3_ip:
        description:
        - DHCP relay IP address of the third DHCP server
        - Not applicable at Multisite parent fabric level
        type: str
        required: false
      dhcp_srvr3_vrf:
        description:
        - VRF ID of third DHCP server
        - Not applicable at Multisite parent fabric level
        type: str
        required: false
      dhcp_servers:
        description:
        - List of DHCP server_vrf pairs where 'srvr_ip' is the IP key and 'srvr_vrf' is the VRF key
        - This is an alternative to dhcp_srvr1_ip, dhcp_srvr1_vrf, dhcp_srvr2_ip, dhcp_srvr2_vrf,
            dhcp_srvr3_ip, dhcp_srvr3_vrf
        - If both dhcp_servers and any of dhcp_srvr1_ip, dhcp_srvr1_vrf, dhcp_srvr2_ip,
            dhcp_srvr2_vrf, dhcp_srvr3_ip, dhcp_srvr3_vrf are specified an error message is generated
            indicating these are mutually exclusive options. Max of 16 servers can be specified.
        - Not applicable at Multisite parent fabric level
        type: list
        elements: dict
        required: false
      dhcp_loopback_id:
        description:
        - Loopback ID for DHCP Relay interface
        - Configured ID value should be in range 0-1023
        - Not applicable at Multisite parent fabric level
        type: int
        required: false
      multicast_group_address:
        description:
        - The multicast IP address for the network
        - Not applicable at Multisite parent fabric level
        type: str
        required: false
      gw_ipv6_subnet:
        description:
        - IPv6 Gateway with prefix for the network
        type: str
        required: false
      secondary_ip_gw1:
        description:
        - IP address with subnet for secondary gateway 1
        type: str
        required: false
      secondary_ip_gw2:
        description:
        - IP address with subnet for secondary gateway 2
        type: str
        required: false
      secondary_ip_gw3:
        description:
        - IP address with subnet for secondary gateway 3
        type: str
        required: false
      secondary_ip_gw4:
        description:
        - IP address with subnet for secondary gateway 4
        type: str
        required: false
      trm_enable:
        description:
        - Enable Tenant Routed Multicast
        - Not applicable at Multisite parent fabric level
        type: bool
        required: false
        default: false
      route_target_both:
        description:
        - Enable both L2 VNI Route-Target
        type: bool
        required: false
        default: false
      l3gw_on_border:
        description:
        - Enable L3 Gateway on Border
        - Not applicable at Multisite parent fabric level
        type: bool
        required: false
        default: false
      netflow_enable:
        description:
        - Enable Netflow
        - Netflow is supported only if it is enabled on fabric
        - Netflow configs are supported on NDFC only
        - Not applicable at Multisite parent fabric level
        type: bool
        required: false
        default: false
      intfvlan_nf_monitor:
        description:
        - Interface Vlan Netflow Monitor
        - Applicable only if 'Layer 2 Only' is not enabled. Provide monitor name defined in fabric setting for Layer 3 Record
        - Netflow configs are supported on NDFC only
        type: str
        required: false
      vlan_nf_monitor:
        description:
        - Vlan Netflow Monitor
        - Provide monitor name defined in fabric setting for Layer 3 Record
        - Netflow configs are supported on NDFC only
        - Not applicable at Multisite parent fabric level
        type: str
        required: false
      attach:
        description:
        - List of network attachment details
        type: list
        elements: dict
        suboptions:
          ip_address:
            description:
            - IP address of the switch where the network will be attached or detached
            type: str
            required: true
          ports:
            description:
            - List of switch interfaces where the network will be attached
            type: list
            elements: str
            required: true
          deploy:
            description:
            - Per switch knob to control whether to deploy the attachment
            - This knob has been deprecated from Ansible NDFC Collection Version 2.1.0 onwards.
              There will not be any functional impact if specified in playbook.
            type: bool
            default: true
          tor_ports:
            description:
            - List of interfaces in the paired TOR switch for this leaf where the network will be attached
            - Please attach the same set of TOR ports to both the VPC paired switches.
            type: list
            elements: dict
            required: false
            suboptions:
              ip_address:
                description:
                - IP address of the TOR switch where the network will be attached
                type: str
                required: true
              ports:
                description:
                - List of TOR switch interfaces where the network will be attached
                type: list
                elements: str
                required: true
      deploy:
        description:
        - Global knob to control whether to deploy the attachment
        - Ansible NDFC Collection Behavior for Version 2.0.1 and earlier
        - This knob will create and deploy the attachment in ND only when set to "True" in playbook
        - Ansible NDFC Collection Behavior for Version 2.1.0 and later
        - Attachments specified in the playbook will always be created in DCNM.
          This knob, when set to "True",  will deploy the attachment in DCNM, by pushing the configs to switch.
          If set to "False", the attachments will be created in DCNM, but will not be deployed
        - Defaults to true. For MSD parent fabrics, this value is copied to child fabrics unless overridden at child level
        type: bool
        default: true
      child_fabric_config:
        description:
        - List of child fabric configurations for MSD (Multi-Site Domain) parent fabrics
        - Only valid when the fabric is an MSD parent fabric
        - Child fabric configurations cannot contain 'attach' parameter - attachments are managed at parent level only
        - Child-specific parameters like dhcp_loopback_id, l3gw_on_border, netflow_enable, etc. can be specified per child
        - Deploy setting defaults to parent's deploy value but can be overridden per child fabric
        type: list
        elements: dict
        required: false
        suboptions:
          fabric:
            description:
            - Name of the child fabric
            - Child fabric must be a member of the specified MSD parent fabric
            type: str
            required: true
          deploy:
            description:
            - Override deploy setting for this child fabric
            - If not specified, inherits the deploy value from parent fabric configuration
            type: bool
            required: false
          dhcp_loopback_id:
            description:
            - Child-specific Loopback ID for DHCP Relay interface
            - Configured ID value should be in range 0-1023
            type: int
            required: false
          l3gw_on_border:
            description:
            - Child-specific Enable L3 Gateway on Border setting
            type: bool
            required: false
          netflow_enable:
            description:
            - Child-specific Enable Netflow setting
            - Netflow is supported only if it is enabled on fabric
            - Netflow configs are supported on NDFC only
            type: bool
            required: false
          multicast_group_address:
            description:
            - Child-specific multicast IP address for the network
            type: str
            required: false
          vlan_nf_monitor:
            description:
            - Child-specific Vlan Netflow Monitor
            - Provide monitor name defined in fabric setting for Layer 3 Record
            - Netflow configs are supported on NDFC only
            type: str
            required: false
          dhcp_srvr1_ip:
            description:
            - Child-specific DHCP relay IP address of the first DHCP server
            type: str
            required: false
          dhcp_srvr1_vrf:
            description:
            - Child-specific VRF ID of first DHCP server
            type: str
            required: false
"""

EXAMPLES = """
# This module supports the following states:
#
# Merged:
#   Networks defined in the playbook will be merged into the target fabric.
#     - If the network does not exist it will be added.
#     - If the network exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - Networks that are not specified in the playbook will be untouched.
#
# Replaced:
#   Networks defined in the playbook will be replaced in the target fabric.
#     - If the Networks does not exist it will be added.
#     - If the Networks exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - Properties that can be managed by the module but are not specified
#       in the playbook will be deleted or defaulted if possible.
#     - Networks that are not specified in the playbook will be untouched.
#
# Overridden:
#   Networks defined in the playbook will be overridden in the target fabric.
#     - If the Networks does not exist it will be added.
#     - If the Networks exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - Properties that can be managed by the module but are not specified
#       in the playbook will be deleted or defaulted if possible.
#     - Networks that are not specified in the playbook will be deleted.
#
# Deleted:
#   Networks defined in the playbook will be deleted.
#   If no Networks are provided in the playbook, all Networks present on that ND fabric will be deleted.
#
# Query:
#   Returns the current ND state for the Networks listed in the playbook.
#
# MSD (Multi-Site Domain) Fabric Support:
# - The module automatically detects fabric type (standalone, multisite_parent, multisite_child) using fabric associations API
# - For MSD parent fabrics, use child_fabric_config to specify child-specific network parameters
# - Child fabric configurations inherit deploy setting from parent unless explicitly overridden
# - Attachments (attach parameter) can only be specified at parent fabric level, not in child_fabric_config
# - When parent state is 'overridden', child fabrics use 'replaced' state (never 'overridden')
# - Deploy defaults to true for both parent and child configurations

# ===========================================================================
# Standalone Fabric Examples
# ===========================================================================
# ---------------------------------------------------------------------------
# STATE: MERGED - Merge Network Configuration
# ---------------------------------------------------------------------------

- name: Merge networks
  cisco.dcnm.dcnm_network:
    fabric: vxlan-fabric
    state: merged
    config:
    - net_name: ansible-net13
      vrf_name: Tenant-1
      net_id: 7005
      net_template: Default_Network_Universal
      net_extension_template: Default_Network_Extension_Universal
      vlan_id: 150
      gw_ip_subnet: '192.168.30.1/24'
      attach:
      - ip_address: 192.168.1.224
        ports: [Ethernet1/13, Ethernet1/14]
      - ip_address: 192.168.1.225
        ports: [Ethernet1/13, Ethernet1/14]
      deploy: true
    - net_name: ansible-net12
      vrf_name: Tenant-2
      net_id: 7002
      net_template: Default_Network_Universal
      net_extension_template: Default_Network_Extension_Universal
      vlan_id: 151
      gw_ip_subnet: '192.168.40.1/24'
      attach:
      - ip_address: 192.168.1.224
        ports: [Ethernet1/11, Ethernet1/12]
        tor_ports:
        - ip_address: 192.168.1.120
          ports: [Ethernet1/14, Ethernet1/15]
      - ip_address: 192.168.1.225
        ports: [Ethernet1/11, Ethernet1/12]
      deploy: false

# ---------------------------------------------------------------------------
# STATE: REPLACED - Replace Network Configuration
# ---------------------------------------------------------------------------

- name: Replace networks
  cisco.dcnm.dcnm_network:
    fabric: vxlan-fabric
    state: replaced
    config:
      - net_name: ansible-net13
        vrf_name: Tenant-1
        net_id: 7005
        net_template: Default_Network_Universal
        net_extension_template: Default_Network_Extension_Universal
        vlan_id: 150
        gw_ip_subnet: '192.168.30.1/24'
        dhcp_servers:
        - srvr_ip: 192.168.1.1
          srvr_vrf: vrf_01
        - srvr_ip: 192.168.2.1
          srvr_vrf: vrf_02
        - srvr_ip: 192.168.3.1
          srvr_vrf: vrf_03
        - srvr_ip: 192.168.4.1
          srvr_vrf: vrf_04
        - srvr_ip: 192.168.5.1
          srvr_vrf: vrf_05
        - srvr_ip: 192.168.6.1
          srvr_vrf: vrf_06
        - srvr_ip: 192.168.7.1
          srvr_vrf: vrf_07
        - srvr_ip: 192.168.8.1
          srvr_vrf: vrf_08
        - srvr_ip: 192.168.9.1
          srvr_vrf: vrf_09
        - srvr_ip: 192.168.10.1
          srvr_vrf: vrf_10
        attach:
        - ip_address: 192.168.1.224
          # Replace the ports with new ports
          # ports: [Ethernet1/13, Ethernet1/14]
          ports: [Ethernet1/16, Ethernet1/17]
          # Delete this attachment
        # - ip_address: 192.168.1.225
        #   ports: [Ethernet1/13, Ethernet1/14]
        deploy: true
        # Dont touch this if its present on DCNM
        # - net_name: ansible-net12
        #   vrf_name: Tenant-2
        #   net_id: 7002
        #   net_template: Default_Network_Universal
        #   net_extension_template: Default_Network_Extension_Universal
        #   vlan_id: 151
        #   gw_ip_subnet: '192.168.40.1/24'
        #   attach:
        #     - ip_address: 192.168.1.224
        #       ports: [Ethernet1/11, Ethernet1/12]
        #     - ip_address: 192.168.1.225
        #       ports: [Ethernet1/11, Ethernet1/12]
        #   deploy: false

# ---------------------------------------------------------------------------
# STATE: OVERRIDDEN - Override all Networks
# ---------------------------------------------------------------------------

- name: Override networks
  cisco.dcnm.dcnm_network:
    fabric: vxlan-fabric
    state: overridden
    config:
    - net_name: ansible-net13
      vrf_name: Tenant-1
      net_id: 7005
      net_template: Default_Network_Universal
      net_extension_template: Default_Network_Extension_Universal
      vlan_id: 150
      gw_ip_subnet: '192.168.30.1/24'
      attach:
      - ip_address: 192.168.1.224
        # Replace the ports with new ports
        # ports: [Ethernet1/13, Ethernet1/14]
        ports: [Ethernet1/16, Ethernet1/17]
        # Delete this attachment
        # - ip_address: 192.168.1.225
        #   ports: [Ethernet1/13, Ethernet1/14]
      deploy: true
      # Delete this network
      # - net_name: ansible-net12
      #   vrf_name: Tenant-2
      #   net_id: 7002
      #   net_template: Default_Network_Universal
      #   net_extension_template: Default_Network_Extension_Universal
      #   vlan_id: 151
      #   gw_ip_subnet: '192.168.40.1/24'
      #   attach:
      #   - ip_address: 192.168.1.224
      #     ports: [Ethernet1/11, Ethernet1/12]
      #   - ip_address: 192.168.1.225
      #     ports: [Ethernet1/11, Ethernet1/12]
      #   deploy: false

# ---------------------------------------------------------------------------
# STATE: DELETED - Delete Networks
# ---------------------------------------------------------------------------

- name: Delete selected networks
  cisco.dcnm.dcnm_network:
    fabric: vxlan-fabric
    state: deleted
    config:
    - net_name: ansible-net13
      vrf_name: Tenant-1
      net_id: 7005
      net_template: Default_Network_Universal
      net_extension_template: Default_Network_Extension_Universal
      vlan_id: 150
      gw_ip_subnet: '192.168.30.1/24'
    - net_name: ansible-net12
      vrf_name: Tenant-2
      net_id: 7002
      net_template: Default_Network_Universal
      net_extension_template: Default_Network_Extension_Universal
      vlan_id: 151
      gw_ip_subnet: '192.168.40.1/24'
      deploy: false

- name: Delete all the networkss
  cisco.dcnm.dcnm_network:
    fabric: vxlan-fabric
    state: deleted

# ---------------------------------------------------------------------------
# STATE: QUERY - Query Networks
# ---------------------------------------------------------------------------

- name: Query Networks
  cisco.dcnm.dcnm_network:
    fabric: vxlan-fabric
    state: query
    config:
    - net_name: ansible-net13
    - net_name: ansible-net12

# ===========================================================================
# MSD (Multi-Site Domain) Fabric Examples
# ===========================================================================

# Note: The module automatically detects fabric type using fabric associations API.

# ---------------------------------------------------------------------------
# STATE: MERGED - Create/Update Networks on Parent and Child Fabrics
# ---------------------------------------------------------------------------

- name: MSD MERGE | Create a Network on Parent and extend to Child fabrics
  cisco.dcnm.dcnm_network:
    fabric: vxlan-parent-fabric  # Must be the Parent MSD fabric
    state: merged
    config:
      - net_name: ansible-net-msd-1
        vrf_name: Tenant-1
        net_id: 130001
        vlan_id: 2301
        net_template: Default_Network_Universal
        net_extension_template: Default_Network_Extension_Universal
        gw_ip_subnet: '192.168.12.1/24'
        routing_tag: 1234
        # Attachments are for switches at the Parent fabric
        attach:
          - ip_address: 192.168.10.203
            ports: [Ethernet1/13, Ethernet1/14]
          - ip_address: 192.168.10.204
            ports: [Ethernet1/13, Ethernet1/14]
        # Define how this Network behaves on each Child fabric
        child_fabric_config:
          - fabric: vxlan-child-fabric1
            l3gw_on_border: true
            dhcp_loopback_id: 204
            multicast_group_address: '239.1.1.1'
          - fabric: vxlan-child-fabric2
            l3gw_on_border: false
            dhcp_loopback_id: 205
        deploy: true
      - net_name: ansible-net-msd-2  # A second Network in the same task
        vrf_name: Tenant-2
        net_id: 130002
        vlan_id: 2302
        gw_ip_subnet: '192.168.13.1/24'
        child_fabric_config:
          - fabric: vxlan-child-fabric1
            netflow_enable: false
        # Attachments are for switches at the Parent fabric
        attach:
          - ip_address: 192.168.10.203
            ports: [Ethernet1/15, Ethernet1/16]
          - ip_address: 192.168.10.204
            ports: [Ethernet1/15, Ethernet1/16]

- name: MSD MERGE | Create Network with advanced DHCP and multicast settings
  cisco.dcnm.dcnm_network:
    fabric: vxlan-parent-fabric
    state: merged
    config:
      - net_name: ansible-net-advanced
        vrf_name: Tenant-1
        net_id: 130010
        vlan_id: 2310
        vlan_name: advanced_network_vlan2310
        gw_ip_subnet: '192.168.20.1/24'
        int_desc: "Advanced Network Configuration"
        mtu_l3intf: 9216
        arp_suppress: true
        route_target_both: true
        # Parent-specific DHCP settings
        dhcp_servers:
          - srvr_ip: 192.168.1.1
            srvr_vrf: management
          - srvr_ip: 192.168.1.2
            srvr_vrf: management
        # Child fabric configuration with different settings per child
        child_fabric_config:
          - fabric: vxlan-child-fabric1
            multicast_group_address: '239.2.1.1'
            dhcp_loopback_id: 210
            dhcp_srvr1_ip: '10.1.1.10'
            dhcp_srvr1_vrf: 'management'
          - fabric: vxlan-child-fabric2
            multicast_group_address: '239.2.2.1'
            l3gw_on_border: true
            deploy: false  # Override parent deploy setting
        attach:
          - ip_address: 192.168.10.203
            ports: [Ethernet1/17, Ethernet1/18]
          - ip_address: 192.168.10.204
            ports: [Ethernet1/17, Ethernet1/18]
        deploy: true  # Parent deploy setting, inherited by children unless overridden

# ---------------------------------------------------------------------------
# STATE: REPLACED - Replace Network configuration on Parent and Child Fabrics
# ---------------------------------------------------------------------------

- name: MSD REPLACE | Update Network properties on Parent and Child fabrics
  cisco.dcnm.dcnm_network:
    fabric: vxlan-parent-fabric
    state: replaced
    config:
      - net_name: ansible-net-msd-1
        vrf_name: Tenant-1
        net_id: 130001
        net_template: Default_Network_Universal
        net_extension_template: Default_Network_Extension_Universal
        vlan_id: 2301
        gw_ip_subnet: '192.168.12.1/24'
        mtu_l3intf: 9000  # Update MTU on Parent
        # Child fabric configs are replaced: child1 is updated
        child_fabric_config:
          - fabric: vxlan-child-fabric1
            l3gw_on_border: false  # Value is updated
            dhcp_loopback_id: 205  # Value is updated
        attach:
          - ip_address: 192.168.10.203
          # Delete this attachment
          # - ip_address: 192.168.10.204
          # Create the following attachment
          - ip_address: 192.168.10.205
            ports: [Ethernet1/13, Ethernet1/14]
      # Dont touch this if its present on ND
      # - net_name: ansible-net-msd-2
      #   vrf_name: Tenant-2
      #   net_id: 130002
      #   net_template: Default_Network_Universal
      #   net_extension_template: Default_Network_Extension_Universal
      #   attach:
      #   - ip_address: 192.168.10.203
      #     ports: [Ethernet1/15, Ethernet1/16]
      #   - ip_address: 192.168.10.204
      #     ports: [Ethernet1/15, Ethernet1/16]

- name: MSD REPLACE | Update Network with netflow configuration
  cisco.dcnm.dcnm_network:
    fabric: vxlan-parent-fabric
    state: replaced
    config:
      - net_name: ansible-net-advanced
        vrf_name: Tenant-1
        net_id: 130010
        vlan_id: 2310
        gw_ip_subnet: '192.168.20.1/24'
        # Parent settings
        arp_suppress: false  # Updated value
        # Child fabric configuration updates
        child_fabric_config:
          - fabric: vxlan-child-fabric1
            netflow_enable: true
            vlan_nf_monitor: NETFLOW_MONITOR_2  # Updated monitor
            multicast_group_address: '239.2.1.2'  # Updated address

# ---------------------------------------------------------------------------
# STATE: OVERRIDDEN - Override all Networks on Parent and Child Fabrics
# ---------------------------------------------------------------------------

- name: MSD OVERRIDE | Override all Networks ensuring only specified ones exist
  cisco.dcnm.dcnm_network:
    fabric: vxlan-parent-fabric
    state: overridden
    config:
      - net_name: ansible-net-production
        vrf_name: Tenant-Production
        net_id: 140001
        vlan_id: 3001
        gw_ip_subnet: '172.16.1.1/24'
        int_desc: "Production Network for critical workloads"
        child_fabric_config:
          - fabric: vxlan-child-fabric1
            l3gw_on_border: true
            netflow_enable: true
          - fabric: vxlan-child-fabric2
            l3gw_on_border: true
            netflow_enable: true
        attach:
          - ip_address: 192.168.10.203
            ports: [Ethernet1/19, Ethernet1/20]
          - ip_address: 192.168.10.204
            ports: [Ethernet1/19, Ethernet1/20]
        deploy: true
      # All other Networks will be deleted from both parent and child fabrics

# ---------------------------------------------------------------------------
# STATE: DELETED - Delete Networks from Parent and all Child Fabrics
# ---------------------------------------------------------------------------

- name: MSD DELETE | Delete a Network from the Parent and all associated Child fabrics
  cisco.dcnm.dcnm_network:
    fabric: vxlan-parent-fabric
    state: deleted
    config:
      - net_name: ansible-net-msd-1
      # The 'child_fabric_config' parameter is ignored for 'deleted' state.

- name: MSD DELETE | Delete multiple Networks from Parent and Child fabrics
  cisco.dcnm.dcnm_network:
    fabric: vxlan-parent-fabric
    state: deleted
    config:
      - net_name: ansible-net-msd-1
      - net_name: ansible-net-msd-2
      - net_name: ansible-net-advanced

- name: MSD DELETE | Delete all Networks from the Parent and all associated Child fabrics
  cisco.dcnm.dcnm_network:
    fabric: vxlan-parent-fabric
    state: deleted

# ---------------------------------------------------------------------------
# STATE: QUERY - Query Networks
# ---------------------------------------------------------------------------

- name: MSD QUERY | Query specific Networks on the Parent MSD fabric
  cisco.dcnm.dcnm_network:
    fabric: vxlan-parent-fabric
    state: query
    config:
      - net_name: ansible-net-msd-1
      - net_name: ansible-net-msd-2
      # The query will return the Network's configuration on the parent
      # and its attachments on all associated child fabrics.

- name: MSD QUERY | Query all Networks on the Parent MSD fabric
  cisco.dcnm.dcnm_network:
    fabric: vxlan-parent-fabric
    state: query
    # No config specified - returns all Networks

- name: MSD QUERY | Query specific Networks on the Child MSD fabric
  cisco.dcnm.dcnm_network:
    fabric: vxlan-child-fabric1
    state: query
    config:
      - net_name: ansible-net-msd-1
      - net_name: ansible-net-msd-2
      # The query will return the Network's configuration on the child
      # and its attachments.

- name: MSD QUERY | Query all Networks on the Child MSD fabric
  cisco.dcnm.dcnm_network:
    fabric: vxlan-child-fabric1
    state: query
    # No config specified - returns all Networks on the child.

- name: MSD QUERY | Query specific Networks on Parent & Child fabric
  cisco.dcnm.dcnm_network:
    fabric: vxlan-parent-fabric
    state: query
    config:
      - net_name: ansible-net-msd-1
        child_fabric_config:
          - fabric: vxlan-child-fabric1
      - net_name: ansible-net-msd-2
        child_fabric_config:
          - fabric: vxlan-child-fabric2
      # The query will return the Network's configuration on the parent and the
      # configuration on the specified childs and its attachments at
      # the parent and child level respectively.
"""

import copy
import inspect
import json
import logging
import re
import time

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_get_ip_addr_info,
    dcnm_get_url,
    dcnm_send,
    get_fabric_details,
    get_nd_fabric_inventory_details,
    get_ip_sn_dict,
    get_ip_sn_fabric_dict,
    has_partial_dhcp_config,
    validate_list_of_dicts,
)

from ..module_utils.common.log_v2 import Log


class DcnmNetwork:

    dcnm_network_paths = {
        11: {
            "GET_VRF": "/rest/top-down/fabrics/{}/vrfs",
            "GET_VRF_NET": "/rest/top-down/fabrics/{}/networks?vrf-name={}",
            "GET_NET_ATTACH": "/rest/top-down/fabrics/{}/networks/attachments?network-names={}",
            "GET_NET_ID": "/rest/managed-pool/fabrics/{}/segments/ids",
            "GET_NET": "/rest/top-down/fabrics/{}/networks",
            "GET_NET_NAME": "/rest/top-down/fabrics/{}/networks/{}",
            "GET_VLAN": "/rest/resource-manager/vlan/{}?vlanUsageType=TOP_DOWN_NETWORK_VLAN",
            "GET_NET_STATUS": "/rest/top-down/fabrics/{}/networks/{}/status",
            "GET_NET_SWITCH_DEPLOY": "/rest/top-down/fabrics/networks/deploy",
            "GET_NET_SWITCH_DEPLOY_ONEMANAGE": "/onemanage/rest/top-down/networks/deploy",
        },
        12: {
            "GET_VRF": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/vrfs",
            "GET_VRF_NET": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/networks?vrf-name={}",
            "GET_NET_ATTACH": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/networks/attachments?network-names={}",
            "GET_NET_ID": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/netinfo",
            "GET_NET": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/networks",
            "GET_NET_NAME": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/networks/{}",
            "GET_VLAN": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/resource-manager/vlan/{}?vlanUsageType=TOP_DOWN_NETWORK_VLAN",
            "GET_NET_STATUS": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/networks/{}/status",
            "GET_NET_SWITCH_DEPLOY": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/networks/deploy",
            "GET_NET_SWITCH_DEPLOY_ONEMANAGE": "/onemanage/appcenter/cisco/ndfc/api/v1/onemanage/top-down/networks/deploy",
        },
    }

    def __init__(self, module):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.module = module
        self.params = module.params

        msg = "self.params: "
        msg += f"{json.dumps(self.params, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        self.fabric = module.params["fabric"]
        self.config = copy.deepcopy(module.params.get("config"))
        self.check_mode = False
        self.have_create = []
        self.want_create = []
        self.diff_create = []
        self.diff_create_update = []
        # This variable is created specifically to hold all the create payloads which are missing a
        # networkId. These payloads are sent to ND out of band (basically in the get_diff_merge())
        # We lose diffs for these without this variable. The content stored here will be helpful for
        # cases like "check_mode" and to print diffs[] in the output of each task.
        self.diff_create_quick = []
        self.have_attach = []
        self.want_attach = []
        self.diff_attach = []
        self.validated = []
        # diff_detach is to list all attachments of a network being deleted, especially for state: OVERRIDDEN
        # The diff_detach and delete operations have to happen before create+attach+deploy for networks being created.
        # This is specifically to address cases where VLAN from a network which is being deleted is used for another
        # network. Without this additional logic, the create+attach+deploy go out first and complain the VLAN is already
        # in use.
        self.diff_detach = []
        self.have_deploy = {}
        self.want_deploy = {}
        self.diff_deploy = {}
        self.diff_undeploy = {}
        self.diff_delete = {}
        self.diff_input_format = []
        self.query = []
        self.deployment_states = {}
        self.network_to_sns = {}
        
        # Get fabric details from parameter (set by action plugin) - MUST be done before inventory call
        fabric_details = module.params.get("_fabric_details")
        
        # Store fabric_details as instance variable for later use
        self.fabric_details = fabric_details
        
        # Get ND version from action plugin (similar to dcnm_vrf)
        # The action plugin must provide nd_version in fabric_details
        action_nd_version = None
        if self.fabric_details and isinstance(self.fabric_details, dict):
            action_nd_version = self.fabric_details.get("nd_version")
        
        if action_nd_version:
            self.dcnm_version = action_nd_version
            msg = f"ND version from action plugin: {self.dcnm_version}"
            self.log.debug(msg)
        else:
            # Fail if nd_version is not provided by action plugin
            msg = "ND version not provided by action plugin. The '_fabric_details' parameter with 'nd_version' is required."
            self.module.fail_json(msg=msg)
        
        msg = f"self.dcnm_version: {self.dcnm_version}"
        self.log.debug(msg)
        
        self.inventory_data = get_nd_fabric_inventory_details(self.module, self.dcnm_version, self.fabric, self.fabric_details)

        msg = "self.inventory_data: "
        msg += f"{json.dumps(self.inventory_data, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        
        self.ip_sn, self.hn_sn = get_ip_sn_dict(self.inventory_data)
        
        self.ip_fab, self.sn_fab = get_ip_sn_fabric_dict(self.inventory_data)
        self.fabric_det = get_fabric_details(module, self.fabric)

        msg = "self.fabric_det: "
        msg += f"{json.dumps(self.fabric_det, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        
        self.is_ms_fabric = True if self.fabric_det.get("fabricType") == "MFD" else False
        if self.dcnm_version > 12:
            self.paths = self.dcnm_network_paths[12]
        else:
            self.paths = self.dcnm_network_paths[self.dcnm_version]

        # Extract fabric_type from fabric_details
        # Note: fabric_details was already retrieved and stored as self.fabric_details earlier
        if self.fabric_details and isinstance(self.fabric_details, dict):
            self.fabric_type = self.fabric_details.get("fabric_type")
            self.cluster_name = self.fabric_details.get("cluster_name", "")
        else:
            # Fail if fabric_details not provided
            self.module.fail_json(msg="Fabric type detection failed. The '_fabric_details' parameter is required but was not provided by the action plugin.")

        if self.fabric_type is None:
            self.module.fail_json(msg="Could not determine fabric type from _fabric_details. Please ensure the action plugin is functioning correctly.")

        # Modify paths based on fabric type for MFD (multicluster) fabrics
        if self.fabric_type == "multicluster_child":
            # For multicluster child fabrics, prepend proxy path based on ND version
            # Version >= 12.4 uses /fedproxy/, < 12.4 uses /onepath/ (similar to dcnm_vrf)
            if self.dcnm_version >= 12.4:
                proxy = "/fedproxy/"
            else:
                proxy = "/onepath/"
            self.module.warn(f"multicluster_child proxy path: {proxy} (version: {self.dcnm_version}, cluster: {self.cluster_name})")
            for path_key in self.paths:
                self.paths[path_key] = proxy + self.cluster_name + self.paths[path_key]
        elif self.fabric_type == "multicluster_parent":
            # For multicluster parent fabrics - ALL versions:
            # 1. Replace "lan-fabric/rest" with "onemanage" (middle replacement) - applies to ALL versions
            # 2. Prepend "/onemanage" proxy - applies to ALL versions
            proxy = "/onemanage"
            for path_key in self.paths:
                if path_key == "GET_NET_SWITCH_DEPLOY":
                    # Use the dedicated onemanage deploy endpoint
                    self.paths[path_key] = self.paths["GET_NET_SWITCH_DEPLOY_ONEMANAGE"]
                else:
                    # Always replace lan-fabric/rest with onemanage AND prepend /onemanage for ALL versions
                    self.paths[path_key] = proxy + self.paths[path_key].replace("lan-fabric/rest", "onemanage")

        self.check_extra_params = True

        self.result = dict(changed=False, diff=[], response=[], warnings=[])

        self.failed_to_rollback = False
        self.WAIT_TIME_FOR_DELETE_LOOP = 5  # in seconds

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
        if search is None:
            return None
        match = (d for d in search if d[key] == value)
        return next(match, None)

    def diff_for_attach_deploy(self, want_a, have_a, replace=False):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        msg += f"replace == {replace}"
        self.log.debug(msg)

        attach_list = []
        atch_tor_ports = []

        if not want_a:
            return attach_list

        dep_net = False
        for want in want_a:
            found = False
            if have_a:
                for have in have_a:
                    if want["serialNumber"] == have["serialNumber"]:
                        found = True

                        if want.get("isAttached") is not None:
                            if bool(have["isAttached"]) and bool(want["isAttached"]):
                                torports_configured = False

                                # Handle tor ports first if configured.
                                if want.get("torports"):
                                    for tor_w in want["torports"]:
                                        torports_present = False
                                        if have.get("torports"):
                                            for tor_h in have["torports"]:
                                                if tor_w["switch"] == tor_h["switch"]:
                                                    torports_present = True
                                                    h_tor_ports = tor_h["torPorts"].split(",") if tor_h["torPorts"] else []
                                                    w_tor_ports = tor_w["torPorts"].split(",") if tor_w["torPorts"] else []

                                                    if sorted(h_tor_ports) != sorted(w_tor_ports):
                                                        atch_tor_ports = list(set(w_tor_ports) - set(h_tor_ports))

                                                    if replace:
                                                        atch_tor_ports = w_tor_ports
                                                    else:
                                                        atch_tor_ports.extend(h_tor_ports)

                                                    torconfig = tor_w["switch"] + "(" + ",".join(atch_tor_ports) + ")"
                                                    want.update({"torPorts": torconfig})
                                                    # Update torports_configured to True. If there is no other config change for attach
                                                    # We will still append this attach to attach_list as there is tor port change
                                                    if sorted(atch_tor_ports) != sorted(h_tor_ports):
                                                        torports_configured = True

                                        if not torports_present:
                                            torconfig = tor_w["switch"] + "(" + tor_w["torPorts"] + ")"
                                            want.update({"torPorts": torconfig})
                                            # Update torports_configured to True. If there is no other config change for attach
                                            # We will still append this attach to attach_list as there is tor port change
                                            torports_configured = True

                                    if have.get("torports"):
                                        del have["torports"]

                                elif have.get("torports"):
                                    if replace:
                                        # There are tor ports configured, but it has to be removed as want tor ports are not present
                                        # and state is replaced/overridden. Update torports_configured to True to remove tor ports
                                        want.update({"torPorts": ""})
                                        torports_configured = True

                                    else:
                                        # Dont update torports_configured to True.
                                        # If at all there is any other config change, this attach to will be appended attach_list there
                                        torconfig_list = []
                                        for tor_h in have.get("torports"):
                                            torconfig_list.append(tor_h["switch"] + "(" + tor_h["torPorts"] + ")")
                                        want.update({"torPorts": " ".join(torconfig_list)})

                                    del have["torports"]

                                if want.get("torports"):
                                    del want["torports"]

                                h_sw_ports = have["switchPorts"].split(",") if have["switchPorts"] else []
                                w_sw_ports = want["switchPorts"].split(",") if want["switchPorts"] else []

                                # This is needed to handle cases where vlan is updated after deploying the network
                                # and attachments. This ensures that the attachments before vlan update will use previous
                                # vlan id. All the active attachments on ND will have a vlan-id.
                                if have.get("vlan"):
                                    want["vlan"] = have.get("vlan")

                                if sorted(h_sw_ports) != sorted(w_sw_ports):
                                    atch_sw_ports = list(set(w_sw_ports) - set(h_sw_ports))

                                    # Adding some logic which is needed for replace and override.
                                    if replace:
                                        dtach_sw_ports = list(set(h_sw_ports) - set(w_sw_ports))

                                        if not atch_sw_ports and not dtach_sw_ports:
                                            if torports_configured:
                                                del want["isAttached"]
                                                attach_list.append(want)
                                                if bool(want["is_deploy"]):
                                                    dep_net = True

                                            continue

                                        want.update({"switchPorts": (",".join(atch_sw_ports) if atch_sw_ports else "")})
                                        want.update({"detachSwitchPorts": (",".join(dtach_sw_ports) if dtach_sw_ports else "")})

                                        del want["isAttached"]
                                        attach_list.append(want)
                                        if bool(want["is_deploy"]):
                                            dep_net = True
                                        continue

                                    if not atch_sw_ports:
                                        # The attachments in the have consist of attachments in want and more.
                                        if torports_configured:
                                            del want["isAttached"]
                                            attach_list.append(want)
                                            if bool(want["is_deploy"]):
                                                dep_net = True

                                        continue
                                    else:
                                        want.update({"switchPorts": ",".join(atch_sw_ports)})

                                    del want["isAttached"]
                                    attach_list.append(want)
                                    if bool(want["is_deploy"]):
                                        dep_net = True
                                    continue

                                elif torports_configured:
                                    del want["isAttached"]
                                    attach_list.append(want)
                                    if bool(want["is_deploy"]):
                                        dep_net = True
                                    continue

                            if bool(have["isAttached"]) is not bool(want["isAttached"]):
                                # When the attachment is to be detached and undeployed, ignore any changes
                                # to the attach section in the want(i.e in the playbook).

                                if not bool(want["isAttached"]):
                                    del have["isAttached"]
                                    have.update({"deployment": False})
                                    attach_list.append(have)
                                    if bool(want["is_deploy"]):
                                        dep_net = True
                                    continue
                                del want["isAttached"]
                                if want.get("torports"):
                                    torconfig_list = []
                                    for tor_w in want["torports"]:
                                        torconfig_list.append(tor_w["switch"] + "(" + tor_w["torPorts"] + ")")
                                    want.update({"torPorts": " ".join(torconfig_list)})
                                    del want["torports"]
                                want.update({"deployment": True})
                                attach_list.append(want)
                                if bool(want["is_deploy"]):
                                    dep_net = True
                                continue

                        if bool(have["deployment"]) is not bool(want["deployment"]):
                            # We hit this section when attachment is successful, but, deployment is stuck in PENDING or
                            # OUT-OF-SYNC. In such cases, we just add the object to deploy list only. have['deployment']
                            # is set to False when deployment is PENDING or OUT-OF-SYNC - ref - get_have()
                            if bool(want["is_deploy"]):
                                dep_net = True

                        if bool(want.get("is_deploy")) is not bool(have.get("is_deploy")):
                            if bool(want.get("is_deploy")):
                                dep_net = True

            if not found:
                if bool(want["isAttached"]):
                    if want.get("torports"):
                        torconfig_list = []
                        for tor_w in want["torports"]:
                            torconfig_list.append(tor_w["switch"] + "(" + tor_w["torPorts"] + ")")
                        want.update({"torPorts": " ".join(torconfig_list)})
                    del want["torports"]
                    del want["isAttached"]
                    want["deployment"] = True
                    attach_list.append(want)
                    if bool(want["is_deploy"]):
                        dep_net = True

        for attach in attach_list[:]:
            for ip, ser in self.ip_sn.items():
                if ser == attach["serialNumber"]:
                    ip_addr = ip
                    break
            is_vpc = self.inventory_data[ip_addr].get("isVpcConfigured")
            if is_vpc is True:
                peer_found = False
                peer_ser = self.inventory_data[ip_addr].get("peerSerialNumber")
                for attch in attach_list:
                    if peer_ser == attch["serialNumber"]:
                        peer_found = True
                if not peer_found:
                    for hav in have_a:
                        if hav["serialNumber"] == peer_ser:
                            havtoattach = copy.deepcopy(hav)
                            havtoattach.update({"switchPorts": ""})
                            del havtoattach["isAttached"]
                            havtoattach["deployment"] = True
                            attach_list.append(havtoattach)
                            break

        # self.module.fail_json(msg="attach done")

        return attach_list, dep_net

    def update_attach_params(self, attach, net_name, deploy):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        torlist = []
        if not attach:
            return {}

        serial = ""
        attach["ip_address"] = dcnm_get_ip_addr_info(self.module, attach["ip_address"], None, None)
        for ip, ser in self.ip_sn.items():
            if ip == attach["ip_address"]:
                serial = ser

        if not serial:
            self.module.fail_json(msg="Fabric: {0} does not have the switch: {1}".format(self.fabric, attach["ip_address"]))

        role = self.inventory_data[attach["ip_address"]].get("switchRole")
        if role.lower() == "spine" or role.lower() == "super spine":
            msg = "Networks cannot be attached to switch {0} with role {1}".format(attach["ip_address"], role)
            self.module.fail_json(msg=msg)

        attach.update({"fabric": self.fabric})
        attach.update({"networkName": net_name})
        attach.update({"serialNumber": serial})
        attach.update({"switchPorts": ",".join(attach["ports"])})
        attach.update({"detachSwitchPorts": ""})  # Is this supported??Need to handle correct
        attach.update({"vlan": 0})
        attach.update({"dot1QVlan": 0})
        attach.update({"untagged": False})
        # This flag is not to be confused for deploy of attachment.
        # "deployment" should be set True for attaching an attachment
        # and set to False for detaching an attachment
        attach.update({"deployment": True})
        attach.update({"isAttached": True})
        attach.update({"extensionValues": ""})
        attach.update({"instanceValues": ""})
        attach.update({"freeformConfig": ""})
        attach.update({"is_deploy": deploy})
        
        if attach.get("tor_ports"):
            if role.lower() != "leaf":
                msg = "tor_ports for Networks cannot be attached to switch {0} with role {1}".format(attach["ip_address"], role)
                self.module.fail_json(msg=msg)
            for tor in attach.get("tor_ports"):
                torports = {}
                torports.update({"switch": self.inventory_data[tor["ip_address"]].get("logicalName")})
                torports.update({"torPorts": ",".join(tor["ports"])})
                torlist.append(torports)
            del attach["tor_ports"]
        attach.update({"torports": torlist})

        if "deploy" in attach:
            del attach["deploy"]
        del attach["ports"]
        del attach["ip_address"]

        return attach

    def transform_deploy_payload_for_multicluster(self, deploy_payload):
        """
        Transform deploy payload for multicluster parent fabrics ONLY.
        
        For multicluster parent, the deploy API expects:
        {"serialNumber1": "net1,net2,net3", "serialNumber2": "net1,net2,net3"}
        
        For all other fabric types (including multicluster_child), use standard format:
        {"networkNames": "net1,net2,net3"}
        
        Uses the network_to_sns mapping built in get_have()
        to efficiently construct the payload for multicluster_parent.
        
        Args:
            deploy_payload: Original payload with networkNames format
            
        Returns:
            Transformed payload for multicluster_parent or original payload for other fabric types
        """
        # Only transform for multicluster_parent, all others (including multicluster_child) use standard format
        if self.fabric_type != "multicluster_parent":
            return deploy_payload
        
        if not deploy_payload or "networkNames" not in deploy_payload:
            return deploy_payload
        
        network_names_str = deploy_payload["networkNames"]
        if not network_names_str:
            return {}
        
        # Parse the comma-separated network names
        network_names_list = [name.strip() for name in network_names_str.split(",")]
        
        # Check if we have the mappings from get_have()
        if not hasattr(self, 'network_to_sns') or not self.network_to_sns:
            return deploy_payload
        
        # Build the multicluster format payload using the mappings
        # For each network in deploy list, find its serial numbers
        # Then invert to get serial -> networks mapping
        serial_to_networks = {}
        
        for network_name in network_names_list:
            # Skip if network not in our mapping (shouldn't happen, but be safe)
            if network_name not in self.network_to_sns:
                continue
            
            # Get all serial numbers for this network
            serial_numbers = self.network_to_sns[network_name]
            
            # Add this network to each serial's list
            for serial in serial_numbers:
                if serial not in serial_to_networks:
                    serial_to_networks[serial] = []
                if network_name not in serial_to_networks[serial]:
                    serial_to_networks[serial].append(network_name)
        
        # If we couldn't build the mapping, fall back to original payload
        if not serial_to_networks:
            return deploy_payload
        
        # Build the multicluster format payload: {serialNumber: "net1,net2,net3"}
        multicluster_payload = {}
        for serial, networks in serial_to_networks.items():
            multicluster_payload[serial] = ",".join(networks)
        
        return multicluster_payload

    def diff_for_create(self, want, have):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        # Possible update scenarios
        # vlanId - Changing vlanId on an already deployed network only affects new attachments
        # gwIpAddress - Changing the gwIpAddress needs all attachments to be re-deployed

        warn_msg = None
        if not have:
            return {}

        # Get skipped attributes for parent fabrics
        skipped_attributes = self.get_skipped_attributes()
        template_mapping = self.get_template_config_mapping()

        # Convert skipped spec attributes to template config keys
        skipped_template_keys = set()
        for attr in skipped_attributes:
            if attr in template_mapping:
                skipped_template_keys.add(template_mapping[attr])

        gw_changed = False
        tg_changed = False
        create = {}
        l2only_changed = False
        vn_changed = False
        intdesc_changed = False
        mtu_changed = False
        arpsup_changed = False
        dhcp1_ip_changed = False
        dhcp2_ip_changed = False
        dhcp3_ip_changed = False
        dhcp1_vrf_changed = False
        dhcp2_vrf_changed = False
        dhcp3_vrf_changed = False
        dhcp_servers_changed = False
        dhcp_loopback_changed = False
        multicast_group_address_changed = False
        gwv6_changed = False
        sec_gw1_changed = False
        sec_gw2_changed = False
        sec_gw3_changed = False
        sec_gw4_changed = False
        trm_en_changed = False
        rt_both_changed = False
        l3gw_onbd_changed = False
        nf_en_changed = False
        intvlan_nfmon_changed = False
        vlan_nfmon_changed = False

        if want.get("networkId") and want["networkId"] != have["networkId"]:
            self.module.fail_json(msg="networkId can not be updated on existing network: {0}".format(want["networkName"]))

        if have["vrf"] != want["vrf"]:
            self.module.fail_json(
                msg="The network {0} existing already can not change"
                " the VRF association from vrf:{1} to vrf:{2}".format(want["networkName"], have["vrf"], want["vrf"])
            )

        json_to_dict_want = json.loads(want["networkTemplateConfig"])
        json_to_dict_have = json.loads(have["networkTemplateConfig"])

        gw_ip_want = json_to_dict_want.get("gatewayIpAddress", "")
        gw_ip_have = json_to_dict_have.get("gatewayIpAddress", "")
        vlanId_want = json_to_dict_want.get("vlanId", "")
        vlanId_have = json_to_dict_have.get("vlanId")
        l2only_want = str(json_to_dict_want.get("isLayer2Only", "")).lower()
        l2only_have = str(json_to_dict_have.get("isLayer2Only", "")).lower()
        vlanName_want = json_to_dict_want.get("vlanName", "")
        vlanName_have = json_to_dict_have.get("vlanName", "")
        intDesc_want = json_to_dict_want.get("intfDescription", "")
        intDesc_have = json_to_dict_have.get("intfDescription", "")
        mtu_want = json_to_dict_want.get("mtu", "")
        mtu_have = json_to_dict_have.get("mtu", "")
        arpsup_want = str(json_to_dict_want.get("suppressArp", "")).lower()
        arpsup_have = str(json_to_dict_have.get("suppressArp", "")).lower()
        dhcp1_ip_want = json_to_dict_want.get("dhcpServerAddr1", "")
        dhcp1_ip_want = json_to_dict_want.get("dhcpServerAddr1", "")
        dhcp1_ip_have = json_to_dict_have.get("dhcpServerAddr1", "")
        dhcp2_ip_want = json_to_dict_want.get("dhcpServerAddr2", "")
        dhcp2_ip_have = json_to_dict_have.get("dhcpServerAddr2", "")
        dhcp3_ip_want = json_to_dict_want.get("dhcpServerAddr3", "")
        dhcp3_ip_have = json_to_dict_have.get("dhcpServerAddr3", "")
        dhcp1_vrf_want = json_to_dict_want.get("vrfDhcp", "")
        dhcp1_vrf_have = json_to_dict_have.get("vrfDhcp", "")
        dhcp2_vrf_want = json_to_dict_want.get("vrfDhcp2", "")
        dhcp2_vrf_have = json_to_dict_have.get("vrfDhcp2", "")
        dhcp3_vrf_want = json_to_dict_want.get("vrfDhcp3", "")
        dhcp3_vrf_have = json_to_dict_have.get("vrfDhcp3", "")
        dhcp_servers_want = json_to_dict_want.get("dhcpServers", "")
        dhcp_servers_have = json_to_dict_have.get("dhcpServers", "")
        dhcp_loopback_want = str(json_to_dict_want.get("loopbackId", ""))
        dhcp_loopback_have = str(json_to_dict_have.get("loopbackId", ""))
        multicast_group_address_want = json_to_dict_want.get("mcastGroup", "")
        multicast_group_address_have = json_to_dict_have.get("mcastGroup", "")
        gw_ipv6_want = json_to_dict_want.get("gatewayIpV6Address", "")
        gw_ipv6_have = json_to_dict_have.get("gatewayIpV6Address", "")
        secip_gw1_want = json_to_dict_want.get("secondaryGW1", "")
        secip_gw1_have = json_to_dict_have.get("secondaryGW1", "")
        secip_gw2_want = json_to_dict_want.get("secondaryGW2", "")
        secip_gw2_have = json_to_dict_have.get("secondaryGW2", "")
        secip_gw3_want = json_to_dict_want.get("secondaryGW3", "")
        secip_gw3_have = json_to_dict_have.get("secondaryGW3", "")
        secip_gw4_want = json_to_dict_want.get("secondaryGW4", "")
        secip_gw4_have = json_to_dict_have.get("secondaryGW4", "")
        trmen_want = str(json_to_dict_want.get("trmEnabled", "")).lower()
        trmen_have = str(json_to_dict_have.get("trmEnabled", "")).lower()
        rt_both_want = str(json_to_dict_want.get("rtBothAuto", "")).lower()
        rt_both_have = str(json_to_dict_have.get("rtBothAuto", "")).lower()
        l3gw_onbd_want = str(json_to_dict_want.get("enableL3OnBorder", "")).lower()
        l3gw_onbd_have = str(json_to_dict_have.get("enableL3OnBorder", "")).lower()
        nf_en_want = str(json_to_dict_want.get("ENABLE_NETFLOW", "")).lower()
        nf_en_have = str(json_to_dict_have.get("ENABLE_NETFLOW", "")).lower()
        intvlan_nfen_want = json_to_dict_want.get("SVI_NETFLOW_MONITOR", "")
        intvlan_nfen_have = json_to_dict_have.get("SVI_NETFLOW_MONITOR", "")
        vlan_nfen_want = json_to_dict_want.get("VLAN_NETFLOW_MONITOR", "")
        vlan_nfen_have = json_to_dict_have.get("VLAN_NETFLOW_MONITOR", "")

        if vlanId_have != "":
            vlanId_have = int(vlanId_have)
        if vlanId_want != "":
            vlanId_want = int(vlanId_want)
        tag_want = json_to_dict_want.get("tag", "")
        tag_have = json_to_dict_have.get("tag")
        if tag_have != "":
            tag_have = int(tag_have)
        if mtu_have != "":
            mtu_have = int(mtu_have)

        if vlanId_want:

            # Build comparison conditions, skipping those in skipped_template_keys
            comparisons = []

            # Always compare network templates
            template_diff = have["networkTemplate"] != want["networkTemplate"]
            comparisons.append(template_diff)

            ext_template_diff = have["networkExtensionTemplate"] != want["networkExtensionTemplate"]
            comparisons.append(ext_template_diff)

            # Compare other attributes only if not skipped
            if "gatewayIpAddress" not in skipped_template_keys:
                gw_diff = gw_ip_have != gw_ip_want
                comparisons.append(gw_diff)

            if "vlanId" not in skipped_template_keys:
                vlan_diff = vlanId_have != vlanId_want
                comparisons.append(vlan_diff)

            if "tag" not in skipped_template_keys:
                tag_diff = tag_have != tag_want
                comparisons.append(tag_diff)

            if "isLayer2Only" not in skipped_template_keys:
                l2_diff = l2only_have != l2only_want
                comparisons.append(l2_diff)

            if "vlanName" not in skipped_template_keys:
                vname_diff = vlanName_have != vlanName_want
                comparisons.append(vname_diff)

            if "intfDescription" not in skipped_template_keys:
                intdesc_diff = intDesc_have != intDesc_want
                comparisons.append(intdesc_diff)

            if "mtu" not in skipped_template_keys:
                mtu_diff = mtu_have != mtu_want
                comparisons.append(mtu_diff)

            if "suppressArp" not in skipped_template_keys:
                arp_diff = arpsup_have != arpsup_want
                comparisons.append(arp_diff)

            if "dhcpServerAddr1" not in skipped_template_keys:
                dhcp1_diff = dhcp1_ip_have != dhcp1_ip_want
                comparisons.append(dhcp1_diff)

            if "dhcpServerAddr2" not in skipped_template_keys:
                dhcp2_diff = dhcp2_ip_have != dhcp2_ip_want
                comparisons.append(dhcp2_diff)

            if "dhcpServerAddr3" not in skipped_template_keys:
                dhcp3_diff = dhcp3_ip_have != dhcp3_ip_want
                comparisons.append(dhcp3_diff)

            if "vrfDhcp" not in skipped_template_keys:
                dhcp1vrf_diff = dhcp1_vrf_have != dhcp1_vrf_want
                comparisons.append(dhcp1vrf_diff)

            if "vrfDhcp2" not in skipped_template_keys:
                dhcp2vrf_diff = dhcp2_vrf_have != dhcp2_vrf_want
                comparisons.append(dhcp2vrf_diff)

            if "vrfDhcp3" not in skipped_template_keys:
                dhcp3vrf_diff = dhcp3_vrf_have != dhcp3_vrf_want
                comparisons.append(dhcp3vrf_diff)

            if "dhcpServers" not in skipped_template_keys:
                dhcp_servers_diff = dhcp_servers_have != dhcp_servers_want
                comparisons.append(dhcp_servers_diff)

            if "loopbackId" not in skipped_template_keys:
                loopback_diff = dhcp_loopback_have != dhcp_loopback_want
                comparisons.append(loopback_diff)

            if "mcastGroup" not in skipped_template_keys:
                mcast_diff = multicast_group_address_have != multicast_group_address_want
                comparisons.append(mcast_diff)

            if "gatewayIpV6Address" not in skipped_template_keys:
                gwv6_diff = gw_ipv6_have != gw_ipv6_want
                comparisons.append(gwv6_diff)

            if "secondaryGW1" not in skipped_template_keys:
                secgw1_diff = secip_gw1_have != secip_gw1_want
                comparisons.append(secgw1_diff)

            if "secondaryGW2" not in skipped_template_keys:
                secgw2_diff = secip_gw2_have != secip_gw2_want
                comparisons.append(secgw2_diff)

            if "secondaryGW3" not in skipped_template_keys:
                secgw3_diff = secip_gw3_have != secip_gw3_want
                comparisons.append(secgw3_diff)

            if "secondaryGW4" not in skipped_template_keys:
                secgw4_diff = secip_gw4_have != secip_gw4_want
                comparisons.append(secgw4_diff)

            if "trmEnabled" not in skipped_template_keys:
                trm_diff = trmen_have != trmen_want
                comparisons.append(trm_diff)

            if "rtBothAuto" not in skipped_template_keys:
                rt_diff = rt_both_have != rt_both_want
                comparisons.append(rt_diff)

            if "enableL3OnBorder" not in skipped_template_keys:
                l3border_diff = l3gw_onbd_have != l3gw_onbd_want
                comparisons.append(l3border_diff)

            if "ENABLE_NETFLOW" not in skipped_template_keys:
                nf_diff = nf_en_have != nf_en_want
                comparisons.append(nf_diff)

            if "SVI_NETFLOW_MONITOR" not in skipped_template_keys:
                svi_nf_diff = intvlan_nfen_have != intvlan_nfen_want
                comparisons.append(svi_nf_diff)

            if "VLAN_NETFLOW_MONITOR" not in skipped_template_keys:
                vlan_nf_diff = vlan_nfen_have != vlan_nfen_want
                comparisons.append(vlan_nf_diff)

            if any(comparisons):
                # The network updates with missing networkId will have to use existing
                # networkId from the instance of the same network on DCNM.

                if vlanId_have != vlanId_want:
                    warn_msg = "The VLAN change will effect only new attachments."

                if gw_ip_have != gw_ip_want:
                    gw_changed = True
                if tag_have != tag_want:
                    tg_changed = True
                if l2only_have != l2only_want:
                    l2only_changed = True
                if vlanName_have != vlanName_want:
                    vn_changed = True
                if intDesc_have != intDesc_want:
                    intdesc_changed = True
                if mtu_have != mtu_want:
                    mtu_changed = True
                if arpsup_have != arpsup_want:
                    arpsup_changed = True
                if dhcp1_ip_have != dhcp1_ip_want:
                    dhcp1_ip_changed = True
                if dhcp2_ip_have != dhcp2_ip_want:
                    dhcp2_ip_changed = True
                if dhcp3_ip_have != dhcp3_ip_want:
                    dhcp3_ip_changed = True
                if dhcp1_vrf_have != dhcp1_vrf_want:
                    dhcp1_vrf_changed = True
                if dhcp2_vrf_have != dhcp2_vrf_want:
                    dhcp2_vrf_changed = True
                if dhcp3_vrf_have != dhcp3_vrf_want:
                    dhcp3_vrf_changed = True
                if dhcp_servers_have != dhcp_servers_want:
                    dhcp_servers_changed = True
                if dhcp_loopback_have != dhcp_loopback_want:
                    dhcp_loopback_changed = True
                if multicast_group_address_have != multicast_group_address_want:
                    multicast_group_address_changed = True
                if gw_ipv6_have != gw_ipv6_want:
                    gwv6_changed = True
                if secip_gw1_have != secip_gw1_want:
                    sec_gw1_changed = True
                if secip_gw2_have != secip_gw2_want:
                    sec_gw2_changed = True
                if secip_gw3_have != secip_gw3_want:
                    sec_gw3_changed = True
                if secip_gw4_have != secip_gw4_want:
                    sec_gw4_changed = True
                if trmen_have != trmen_want:
                    trm_en_changed = True
                if rt_both_have != rt_both_want:
                    rt_both_changed = True
                if l3gw_onbd_have != l3gw_onbd_want:
                    l3gw_onbd_changed = True
                if self.dcnm_version > 11:
                    if nf_en_have != nf_en_want:
                        nf_en_changed = True
                    if intvlan_nfen_have != intvlan_nfen_want:
                        intvlan_nfmon_changed = True
                    if vlan_nfen_have != vlan_nfen_want:
                        vlan_nfmon_changed = True

                want.update({"networkId": have["networkId"]})
                create = want

        else:

            # Build comparison conditions, skipping those in skipped_template_keys
            comparisons = []

            # Always compare network templates
            template_diff = have["networkTemplate"] != want["networkTemplate"]
            comparisons.append(template_diff)

            ext_template_diff = have["networkExtensionTemplate"] != want["networkExtensionTemplate"]
            comparisons.append(ext_template_diff)

            # Compare other attributes only if not skipped
            if "gatewayIpAddress" not in skipped_template_keys:
                gw_diff = gw_ip_have != gw_ip_want
                comparisons.append(gw_diff)

            if "vlanId" not in skipped_template_keys:
                vlan_diff = vlanId_have != vlanId_want
                comparisons.append(vlan_diff)

            if "tag" not in skipped_template_keys:
                tag_diff = tag_have != tag_want
                comparisons.append(tag_diff)

            if "isLayer2Only" not in skipped_template_keys:
                l2_diff = l2only_have != l2only_want
                comparisons.append(l2_diff)

            if "vlanName" not in skipped_template_keys:
                vname_diff = vlanName_have != vlanName_want
                comparisons.append(vname_diff)

            if "intfDescription" not in skipped_template_keys:
                intdesc_diff = intDesc_have != intDesc_want
                comparisons.append(intdesc_diff)

            if "mtu" not in skipped_template_keys:
                mtu_diff = mtu_have != mtu_want
                comparisons.append(mtu_diff)

            if "suppressArp" not in skipped_template_keys:
                arp_diff = arpsup_have != arpsup_want
                comparisons.append(arp_diff)

            if "dhcpServerAddr1" not in skipped_template_keys:
                dhcp1_diff = dhcp1_ip_have != dhcp1_ip_want
                comparisons.append(dhcp1_diff)

            if "dhcpServerAddr2" not in skipped_template_keys:
                dhcp2_diff = dhcp2_ip_have != dhcp2_ip_want
                comparisons.append(dhcp2_diff)

            if "dhcpServerAddr3" not in skipped_template_keys:
                dhcp3_diff = dhcp3_ip_have != dhcp3_ip_want
                comparisons.append(dhcp3_diff)

            if "vrfDhcp" not in skipped_template_keys:
                dhcp1vrf_diff = dhcp1_vrf_have != dhcp1_vrf_want
                comparisons.append(dhcp1vrf_diff)

            if "vrfDhcp2" not in skipped_template_keys:
                dhcp2vrf_diff = dhcp2_vrf_have != dhcp2_vrf_want
                comparisons.append(dhcp2vrf_diff)

            if "vrfDhcp3" not in skipped_template_keys:
                dhcp3vrf_diff = dhcp3_vrf_have != dhcp3_vrf_want
                comparisons.append(dhcp3vrf_diff)

            if "dhcpServers" not in skipped_template_keys:
                dhcp_servers_diff = dhcp_servers_have != dhcp_servers_want
                comparisons.append(dhcp_servers_diff)

            if "loopbackId" not in skipped_template_keys:
                loopback_diff = dhcp_loopback_have != dhcp_loopback_want
                comparisons.append(loopback_diff)

            if "mcastGroup" not in skipped_template_keys:
                mcast_diff = multicast_group_address_have != multicast_group_address_want
                comparisons.append(mcast_diff)

            if "gatewayIpV6Address" not in skipped_template_keys:
                gwv6_diff = gw_ipv6_have != gw_ipv6_want
                comparisons.append(gwv6_diff)

            if "secondaryGW1" not in skipped_template_keys:
                secgw1_diff = secip_gw1_have != secip_gw1_want
                comparisons.append(secgw1_diff)

            if "secondaryGW2" not in skipped_template_keys:
                secgw2_diff = secip_gw2_have != secip_gw2_want
                comparisons.append(secgw2_diff)

            if "secondaryGW3" not in skipped_template_keys:
                secgw3_diff = secip_gw3_have != secip_gw3_want
                comparisons.append(secgw3_diff)

            if "secondaryGW4" not in skipped_template_keys:
                secgw4_diff = secip_gw4_have != secip_gw4_want
                comparisons.append(secgw4_diff)

            if "trmEnabled" not in skipped_template_keys:
                trm_diff = trmen_have != trmen_want
                comparisons.append(trm_diff)

            if "rtBothAuto" not in skipped_template_keys:
                rt_diff = rt_both_have != rt_both_want
                comparisons.append(rt_diff)

            if "enableL3OnBorder" not in skipped_template_keys:
                l3border_diff = l3gw_onbd_have != l3gw_onbd_want
                comparisons.append(l3border_diff)

            if "ENABLE_NETFLOW" not in skipped_template_keys:
                nf_diff = nf_en_have != nf_en_want
                comparisons.append(nf_diff)

            if "SVI_NETFLOW_MONITOR" not in skipped_template_keys:
                svi_nf_diff = intvlan_nfen_have != intvlan_nfen_want
                comparisons.append(svi_nf_diff)

            if "VLAN_NETFLOW_MONITOR" not in skipped_template_keys:
                vlan_nf_diff = vlan_nfen_have != vlan_nfen_want
                comparisons.append(vlan_nf_diff)

            if any(comparisons):
                # The network updates with missing networkId will have to use existing
                # networkId from the instance of the same network on DCNM.

                if gw_ip_have != gw_ip_want:
                    gw_changed = True
                if tag_have != tag_want:
                    tg_changed = True
                if l2only_have != l2only_want:
                    l2only_changed = True
                if vlanName_have != vlanName_want:
                    vn_changed = True
                if intDesc_have != intDesc_want:
                    intdesc_changed = True
                if mtu_have != mtu_want:
                    mtu_changed = True
                if arpsup_have != arpsup_want:
                    arpsup_changed = True
                if dhcp1_ip_have != dhcp1_ip_want:
                    dhcp1_ip_changed = True
                if dhcp2_ip_have != dhcp2_ip_want:
                    dhcp2_ip_changed = True
                if dhcp3_ip_have != dhcp3_ip_want:
                    dhcp3_ip_changed = True
                if dhcp1_vrf_have != dhcp1_vrf_want:
                    dhcp1_vrf_changed = True
                if dhcp2_vrf_have != dhcp2_vrf_want:
                    dhcp2_vrf_changed = True
                if dhcp3_vrf_have != dhcp3_vrf_want:
                    dhcp3_vrf_changed = True
                if dhcp_servers_have != dhcp_servers_want:
                    dhcp_servers_changed = True
                if dhcp_loopback_have != dhcp_loopback_want:
                    dhcp_loopback_changed = True
                if multicast_group_address_have != multicast_group_address_want:
                    multicast_group_address_changed = True
                if gw_ipv6_have != gw_ipv6_want:
                    gwv6_changed = True
                if secip_gw1_have != secip_gw1_want:
                    sec_gw1_changed = True
                if secip_gw2_have != secip_gw2_want:
                    sec_gw2_changed = True
                if secip_gw3_have != secip_gw3_want:
                    sec_gw3_changed = True
                if secip_gw4_have != secip_gw4_want:
                    sec_gw4_changed = True
                if trmen_have != trmen_want:
                    trm_en_changed = True
                if rt_both_have != rt_both_want:
                    rt_both_changed = True
                if l3gw_onbd_have != l3gw_onbd_want:
                    l3gw_onbd_changed = True
                if self.dcnm_version > 11:
                    if nf_en_have != nf_en_want:
                        nf_en_changed = True
                    if intvlan_nfen_have != intvlan_nfen_want:
                        intvlan_nfmon_changed = True
                    if vlan_nfen_have != vlan_nfen_want:
                        vlan_nfmon_changed = True

                want.update({"networkId": have["networkId"]})
                create = want

        return (
            create,
            gw_changed,
            tg_changed,
            warn_msg,
            l2only_changed,
            vn_changed,
            intdesc_changed,
            mtu_changed,
            arpsup_changed,
            dhcp1_ip_changed,
            dhcp2_ip_changed,
            dhcp3_ip_changed,
            dhcp1_vrf_changed,
            dhcp2_vrf_changed,
            dhcp3_vrf_changed,
            dhcp_servers_changed,
            dhcp_loopback_changed,
            multicast_group_address_changed,
            gwv6_changed,
            sec_gw1_changed,
            sec_gw2_changed,
            sec_gw3_changed,
            sec_gw4_changed,
            trm_en_changed,
            rt_both_changed,
            l3gw_onbd_changed,
            nf_en_changed,
            intvlan_nfmon_changed,
            vlan_nfmon_changed,
        )

    def update_create_params(self, net):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        if not net:
            return net

        state = self.params["state"]

        n_template = net.get("net_template", "Default_Network_Universal")
        ne_template = net.get("net_extension_template", "Default_Network_Extension_Universal")

        if state == "deleted":
            net_upd = {
                "fabric": self.fabric,
                "networkName": net["net_name"],
                "networkId": net.get("net_id", None),  # Network id will be auto generated in get_diff_merge()
                "networkTemplate": n_template,
                "networkExtensionTemplate": ne_template,
            }
        else:
            net_upd = {
                "fabric": self.fabric,
                "vrf": net.get("vrf_name"),
                "networkName": net["net_name"],
                "networkId": net.get("net_id", None),  # Network id will be auto generated in get_diff_merge()
                "networkTemplate": n_template,
                "networkExtensionTemplate": ne_template,
            }

        template_conf = {
            "vlanId": net.get("vlan_id"),
            "gatewayIpAddress": net.get("gw_ip_subnet", ""),
            "isLayer2Only": net.get("is_l2only", False),
            "tag": net.get("routing_tag"),
            "vlanName": net.get("vlan_name", ""),
            "intfDescription": net.get("int_desc", ""),
            "mtu": net.get("mtu_l3intf", ""),
            "suppressArp": net.get("arp_suppress", False),
            "dhcpServerAddr1": net.get("dhcp_srvr1_ip", ""),
            "dhcpServerAddr2": net.get("dhcp_srvr2_ip", ""),
            "dhcpServerAddr3": net.get("dhcp_srvr3_ip", ""),
            "vrfDhcp": net.get("dhcp_srvr1_vrf", ""),
            "vrfDhcp2": net.get("dhcp_srvr2_vrf", ""),
            "vrfDhcp3": net.get("dhcp_srvr3_vrf", ""),
            "dhcpServers": [
                {"srvrAddr": srvr["srvr_ip"], "srvrVrf": srvr["srvr_vrf"]} for srvr in net.get("dhcp_servers", [])
            ],
        }

        dhcp_loopback_val = net.get("dhcp_loopback_id", "")

        template_conf.update({
            "loopbackId": dhcp_loopback_val,
            "mcastGroup": net.get("multicast_group_address", ""),
            "gatewayIpV6Address": net.get("gw_ipv6_subnet", ""),
            "secondaryGW1": net.get("secondary_ip_gw1", ""),
            "secondaryGW2": net.get("secondary_ip_gw2", ""),
            "secondaryGW3": net.get("secondary_ip_gw3", ""),
            "secondaryGW4": net.get("secondary_ip_gw4", ""),
            "trmEnabled": net.get("trm_enable", False),
            "rtBothAuto": net.get("route_target_both", False),
            "enableL3OnBorder": net.get("l3gw_on_border", False),
        })

        if self.dcnm_version > 11:
            template_conf.update(ENABLE_NETFLOW=net.get("netflow_enable", False))
            template_conf.update(SVI_NETFLOW_MONITOR=net.get("intfvlan_nf_monitor", ""))
            template_conf.update(VLAN_NETFLOW_MONITOR=net.get("vlan_nf_monitor", ""))

        if template_conf["vlanId"] is None:
            template_conf["vlanId"] = ""
        if template_conf["tag"] is None:
            template_conf["tag"] = ""
        if template_conf["vlanName"] is None:
            template_conf["vlanName"] = ""
        if template_conf["intfDescription"] is None:
            template_conf["intfDescription"] = ""
        if template_conf["mtu"] is None:
            template_conf["mtu"] = ""
        if template_conf["vrfDhcp"] is None:
            template_conf["vrfDhcp"] = ""
        if template_conf["vrfDhcp2"] is None:
            template_conf["vrfDhcp2"] = ""
        if template_conf["vrfDhcp3"] is None:
            template_conf["vrfDhcp3"] = ""
        if template_conf["dhcpServers"] == []:
            dhcp_srvr_list = []
            if template_conf["dhcpServerAddr1"] != "" and template_conf["vrfDhcp"] != "":
                dhcp_srvr_list.append({"srvrAddr": template_conf["dhcpServerAddr1"], "srvrVrf": template_conf["vrfDhcp"]})
            if template_conf["dhcpServerAddr2"] != "" and template_conf["vrfDhcp2"] != "":
                dhcp_srvr_list.append({"srvrAddr": template_conf["dhcpServerAddr2"], "srvrVrf": template_conf["vrfDhcp2"]})
            if template_conf["dhcpServerAddr3"] != "" and template_conf["vrfDhcp3"] != "":
                dhcp_srvr_list.append({"srvrAddr": template_conf["dhcpServerAddr3"], "srvrVrf": template_conf["vrfDhcp3"]})
            if dhcp_srvr_list != []:
                template_conf["dhcpServers"] = json.dumps(dict(dhcpServers=dhcp_srvr_list), separators=(",", ":"))
            else:
                template_conf["dhcpServers"] = ""
        elif template_conf["dhcpServers"] != []:
            dhcp_srvr_list = template_conf["dhcpServers"]
            if dhcp_srvr_list[0:1]:
                template_conf["dhcpServerAddr1"] = dhcp_srvr_list[0]["srvrAddr"]
                template_conf["vrfDhcp"] = dhcp_srvr_list[0]["srvrVrf"]
            if dhcp_srvr_list[1:2]:
                template_conf["dhcpServerAddr2"] = dhcp_srvr_list[1]["srvrAddr"]
                template_conf["vrfDhcp2"] = dhcp_srvr_list[1]["srvrVrf"]
            if dhcp_srvr_list[2:3]:
                template_conf["dhcpServerAddr3"] = dhcp_srvr_list[2]["srvrAddr"]
                template_conf["vrfDhcp3"] = dhcp_srvr_list[2]["srvrVrf"]
            template_conf["dhcpServers"] = json.dumps(dict(dhcpServers=dhcp_srvr_list), separators=(",", ":"))
        if template_conf["loopbackId"] is None:
            template_conf["loopbackId"] = ""
        if self.is_ms_fabric is True:
            template_conf.pop("mcastGroup")
        else:
            if template_conf["mcastGroup"] is None:
                template_conf["mcastGroup"] = ""
        if template_conf["gatewayIpV6Address"] is None:
            template_conf["gatewayIpV6Address"] = ""
        if template_conf["secondaryGW1"] is None:
            template_conf["secondaryGW1"] = ""
        if template_conf["secondaryGW2"] is None:
            template_conf["secondaryGW2"] = ""
        if template_conf["secondaryGW3"] is None:
            template_conf["secondaryGW3"] = ""
        if template_conf["secondaryGW4"] is None:
            template_conf["secondaryGW4"] = ""
        if self.dcnm_version > 11:
            if template_conf["SVI_NETFLOW_MONITOR"] is None:
                template_conf["SVI_NETFLOW_MONITOR"] = ""
            if template_conf["VLAN_NETFLOW_MONITOR"] is None:
                template_conf["VLAN_NETFLOW_MONITOR"] = ""

        net_upd.update({"networkTemplateConfig": json.dumps(template_conf)})

        return net_upd

    def get_have(self):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        have_create = []
        have_deploy = {}

        curr_networks = []
        dep_networks = []

        l2only_configured = False

        state = self.params["state"]

        method = "GET"
        path = self.paths["GET_VRF"].format(self.fabric)

        vrf_objects = dcnm_send(self.module, method, path)

        missing_fabric, not_ok = self.handle_response(vrf_objects, "query_dcnm")

        if missing_fabric or not_ok:
            msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find VRFs under fabric: {0}".format(self.fabric)

            self.module.fail_json(msg=msg1 if missing_fabric else msg2)
            return

        if not state == "deleted" and not state == "query":
            if self.config:
                for net in self.config:
                    vrf_found = False
                    vrf_missing = net.get("vrf_name", "NA")
                    if (vrf_missing == "NA" or vrf_missing == "") and net.get("is_l2only", False) is True:
                        # set vrf_missing to NA again as it can be ""
                        vrf_missing = "NA"
                        vrf_found = True
                        l2only_configured = True
                        continue
                    if vrf_objects["DATA"]:
                        for vrf in vrf_objects["DATA"]:
                            if vrf_missing == vrf["vrfName"]:
                                vrf_found = True
                                break
                    if not vrf_found:
                        self.module.fail_json(msg="VRF: {0} is missing in fabric: {1}".format(vrf_missing, self.fabric))

        for vrf in vrf_objects["DATA"]:

            path = self.paths["GET_VRF_NET"].format(self.fabric, vrf["vrfName"])

            networks_per_vrf = dcnm_send(self.module, method, path)

            if not networks_per_vrf["DATA"]:
                continue

            for net in networks_per_vrf["DATA"]:
                json_to_dict = json.loads(net["networkTemplateConfig"])
                t_conf = {
                    "vlanId": json_to_dict.get("vlanId", ""),
                    "gatewayIpAddress": json_to_dict.get("gatewayIpAddress", ""),
                    "isLayer2Only": json_to_dict.get("isLayer2Only", False),
                    "tag": json_to_dict.get("tag", ""),
                    "vlanName": json_to_dict.get("vlanName", ""),
                    "intfDescription": json_to_dict.get("intfDescription", ""),
                    "mtu": json_to_dict.get("mtu", ""),
                    "suppressArp": json_to_dict.get("suppressArp", False),
                    "dhcpServerAddr1": json_to_dict.get("dhcpServerAddr1", ""),
                    "dhcpServerAddr2": json_to_dict.get("dhcpServerAddr2", ""),
                    "dhcpServerAddr3": json_to_dict.get("dhcpServerAddr3", ""),
                    "vrfDhcp": json_to_dict.get("vrfDhcp", ""),
                    "vrfDhcp2": json_to_dict.get("vrfDhcp2", ""),
                    "vrfDhcp3": json_to_dict.get("vrfDhcp3", ""),
                    "dhcpServers": json_to_dict.get("dhcpServers", ""),
                    "loopbackId": json_to_dict.get("loopbackId", ""),
                    "mcastGroup": json_to_dict.get("mcastGroup", ""),
                    "gatewayIpV6Address": json_to_dict.get("gatewayIpV6Address", ""),
                    "secondaryGW1": json_to_dict.get("secondaryGW1", ""),
                    "secondaryGW2": json_to_dict.get("secondaryGW2", ""),
                    "secondaryGW3": json_to_dict.get("secondaryGW3", ""),
                    "secondaryGW4": json_to_dict.get("secondaryGW4", ""),
                    "trmEnabled": json_to_dict.get("trmEnabled", False),
                    "rtBothAuto": json_to_dict.get("rtBothAuto", False),
                    "enableL3OnBorder": json_to_dict.get("enableL3OnBorder", False),
                }

                if self.dcnm_version > 11:
                    t_conf.update(ENABLE_NETFLOW=json_to_dict.get("ENABLE_NETFLOW", False))
                    t_conf.update(SVI_NETFLOW_MONITOR=json_to_dict.get("SVI_NETFLOW_MONITOR", ""))
                    t_conf.update(VLAN_NETFLOW_MONITOR=json_to_dict.get("VLAN_NETFLOW_MONITOR", ""))

                # Remove mcastGroup when Fabric is MSD
                if "mcastGroup" not in json_to_dict:
                    del t_conf["mcastGroup"]

                net.update({"networkTemplateConfig": json.dumps(t_conf)})
                del net["displayName"]
                del net["serviceNetworkTemplate"]
                del net["source"]

                curr_networks.append(net["networkName"])

                have_create.append(net)

        if l2only_configured is True or state == "deleted":
            path = self.paths["GET_VRF_NET"].format(self.fabric, "NA")
            networks_per_navrf = dcnm_send(self.module, method, path)

            if networks_per_navrf.get("DATA"):
                for l2net in networks_per_navrf["DATA"]:
                    json_to_dict = json.loads(l2net["networkTemplateConfig"])
                    if (json_to_dict.get("vrfName", "")) == "NA":
                        t_conf = {
                            "vlanId": json_to_dict.get("vlanId", ""),
                            "gatewayIpAddress": json_to_dict.get("gatewayIpAddress", ""),
                            "isLayer2Only": json_to_dict.get("isLayer2Only", False),
                            "tag": json_to_dict.get("tag", ""),
                            "vlanName": json_to_dict.get("vlanName", ""),
                            "intfDescription": json_to_dict.get("intfDescription", ""),
                            "mtu": json_to_dict.get("mtu", ""),
                            "suppressArp": json_to_dict.get("suppressArp", False),
                            "dhcpServerAddr1": json_to_dict.get("dhcpServerAddr1", ""),
                            "dhcpServerAddr2": json_to_dict.get("dhcpServerAddr2", ""),
                            "dhcpServerAddr3": json_to_dict.get("dhcpServerAddr3", ""),
                            "vrfDhcp": json_to_dict.get("vrfDhcp", ""),
                            "vrfDhcp2": json_to_dict.get("vrfDhcp2", ""),
                            "vrfDhcp3": json_to_dict.get("vrfDhcp3", ""),
                            "dhcpServers": json_to_dict.get("dhcpServers", ""),
                            "loopbackId": json_to_dict.get("loopbackId", ""),
                            "mcastGroup": json_to_dict.get("mcastGroup", ""),
                            "gatewayIpV6Address": json_to_dict.get("gatewayIpV6Address", ""),
                            "secondaryGW1": json_to_dict.get("secondaryGW1", ""),
                            "secondaryGW2": json_to_dict.get("secondaryGW2", ""),
                            "secondaryGW3": json_to_dict.get("secondaryGW3", ""),
                            "secondaryGW4": json_to_dict.get("secondaryGW4", ""),
                            "trmEnabled": json_to_dict.get("trmEnabled", False),
                            "rtBothAuto": json_to_dict.get("rtBothAuto", False),
                            "enableL3OnBorder": json_to_dict.get("enableL3OnBorder", False),
                        }

                        if self.dcnm_version > 11:
                            t_conf.update(ENABLE_NETFLOW=json_to_dict.get("ENABLE_NETFLOW", False))
                            t_conf.update(SVI_NETFLOW_MONITOR=json_to_dict.get("SVI_NETFLOW_MONITOR", ""))
                            t_conf.update(VLAN_NETFLOW_MONITOR=json_to_dict.get("VLAN_NETFLOW_MONITOR", ""))

                        l2net.update({"networkTemplateConfig": json.dumps(t_conf)})
                        del l2net["displayName"]
                        del l2net["serviceNetworkTemplate"]
                        del l2net["source"]

                        curr_networks.append(l2net["networkName"])

                        have_create.append(l2net)

        if not curr_networks:
            return

        net_attach_objects = dcnm_get_url(
            self.module,
            self.fabric,
            self.paths["GET_NET_ATTACH"],
            ",".join(curr_networks),
            "networks",
        )

        if not net_attach_objects["DATA"]:
            return

        for net_attach in net_attach_objects["DATA"]:
            if not net_attach.get("lanAttachList"):
                continue
            attach_list = net_attach["lanAttachList"]
            dep_net = ""
            for attach in attach_list:
                torlist = []
                attach_state = bool(attach.get("isLanAttached", False))
                deploy = attach_state
                deployed = False
                if attach_state and (attach["lanAttachState"] == "OUT-OF-SYNC" or attach["lanAttachState"] == "PENDING"):
                    deployed = False
                elif attach_state and (attach["lanAttachState"] == "IN-SYNC" or attach["lanAttachState"] == "DEPLOYED"):
                    deployed = True

                if bool(deployed):
                    dep_net = attach["networkName"]

                sn = attach["switchSerialNo"]
                vlan = attach.get("vlanId")

                if attach["portNames"] and re.match(r"\S+\(\S+\d+\/\d+\)", attach["portNames"]):
                    for idx, sw_list in enumerate(re.findall(r"\S+\(\S+\d+\/\d+\)", attach["portNames"])):
                        torports = {}
                        sw = sw_list.split("(")
                        eth_list = sw[1].split(")")
                        if idx == 0:
                            ports = eth_list[0]
                            continue
                        torports.update({"switch": sw[0]})
                        torports.update({"torPorts": eth_list[0]})
                        torlist.append(torports)
                    attach.update({"torports": torlist})
                else:
                    ports = attach["portNames"]

                # The deletes and updates below are done to update the incoming dictionary format to
                # match to what the outgoing payload requirements mandate.
                # Ex: 'vlanId' in the attach section of incoming payload needs to be changed to 'vlan'
                # on the attach section of outgoing payload.

                if "vlanId" in attach:
                    del attach["vlanId"]
                del attach["switchSerialNo"]
                del attach["switchName"]
                del attach["switchRole"]
                del attach["ipAddress"]
                del attach["lanAttachState"]
                del attach["isLanAttached"]
                del attach["fabricName"]
                del attach["portNames"]
                del attach["switchDbId"]
                del attach["networkId"]

                if "displayName" in attach.keys():
                    del attach["displayName"]
                if "interfaceGroups" in attach.keys():
                    del attach["interfaceGroups"]

                attach.update({"fabric": self.fabric})
                attach.update({"vlan": vlan})
                attach.update({"serialNumber": sn})
                attach.update({"deployment": deploy})
                attach.update({"extensionValues": ""})
                attach.update({"instanceValues": ""})
                attach.update({"freeformConfig": ""})
                attach.update({"isAttached": attach_state})
                attach.update({"dot1QVlan": 0})
                attach.update({"detachSwitchPorts": ""})
                attach.update({"switchPorts": ports})
                attach.update({"untagged": False})
                attach.update({"is_deploy": deployed})

            if dep_net:
                dep_networks.append(dep_net)

        have_attach = net_attach_objects["DATA"]

        if dep_networks:
            have_deploy.update({"networkNames": ",".join(dep_networks)})

        # Build mapping for multicluster deploy payload transformation
        # network_to_sns: {networkName: [sn1, sn2, ...]}
        network_to_sns = {}
        
        for net_attach in have_attach:
            network_name = net_attach.get("networkName")
            if not network_name:
                continue
            
            lan_attach_list = net_attach.get("lanAttachList", [])
            for attach in lan_attach_list:
                serial = attach.get("serialNumber")
                if not serial:
                    continue
                
                # Build network_to_sns mapping
                if network_name not in network_to_sns:
                    network_to_sns[network_name] = []
                if serial not in network_to_sns[network_name]:
                    network_to_sns[network_name].append(serial)

        self.have_create = have_create
        self.have_attach = have_attach
        self.have_deploy = have_deploy
        self.network_to_sns = network_to_sns

        msg = "self.have_create: "
        msg += f"{json.dumps(self.have_create, indent=4)}"
        self.log.debug(msg)

        msg = "self.have_attach: "
        msg += f"{self.have_attach}"
        self.log.debug(msg)

        msg = "self.have_deploy: "
        msg += f"{json.dumps(self.have_deploy, indent=4)}"
        self.log.debug(msg)

    def get_want(self):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        want_create = []
        want_attach = []
        want_deploy = {}

        all_networks = ""

        if not self.config:
            return

        for net in self.validated:
            net_attach = {}
            networks = []

            net_deploy = net.get("deploy", True)

            want_create.append(self.update_create_params(net))

            if not net.get("attach"):
                continue
            for attach in net["attach"]:
                deploy = net_deploy
                
                result = self.update_attach_params(attach, net["net_name"], deploy)
                
                networks.append(result)
            if networks:
                for attch in net["attach"]:
                    for ip, ser in self.ip_sn.items():
                        if ser == attch["serialNumber"]:
                            ip_address = ip
                            break
                    # deploy = attch["deployment"]
                    is_vpc = self.inventory_data[ip_address].get("isVpcConfigured")
                    if is_vpc is True:
                        peer_found = False
                        peer_ser = self.inventory_data[ip_address].get("peerSerialNumber")
                        for network in networks:
                            if peer_ser == network["serialNumber"]:
                                peer_found = True
                                break
                        if not peer_found:
                            msg = "Switch {0} in fabric {1} is configured for vPC, " "please attach the peer switch also to network".format(
                                ip_address, self.fabric
                            )
                            self.module.fail_json(msg=msg)
                            # This code add the peer switch in vpc cases automatically
                            # As of now UI return error in such cases. Uncomment this if
                            # UI behaviour changes
                            # attach_dict = dict(ip_address="", ports=[], deploy=True)
                            # for ip, ser in self.ip_sn.items():
                            #     if ser == peer_ser:
                            #         ip_addr = ip
                            #         break
                            # attach_dict.update({"ip_address": ip_addr})
                            # networks.append(
                            #     self.update_attach_params(
                            #         attach_dict, net["net_name"], deploy
                            #     )
                            # )
                net_attach.update({"networkName": net["net_name"]})
                net_attach.update({"lanAttachList": networks})
                want_attach.append(net_attach)

            all_networks += net["net_name"] + ","

        if all_networks:
            want_deploy.update({"networkNames": all_networks[:-1]})

        self.want_create = want_create
        self.want_attach = want_attach
        self.want_deploy = want_deploy

        msg = "self.want_create: "
        msg += f"{json.dumps(self.want_create, indent=4)}"
        self.log.debug(msg)

        msg = "self.want_attach: "
        msg += f"{json.dumps(self.want_attach, indent=4)}"
        self.log.debug(msg)

        msg = "self.want_deploy: "
        msg += f"{json.dumps(self.want_deploy, indent=4)}"
        self.log.debug(msg)

    def check_want_networks_deployment_state(self):
        """
        Check deployment state of wanted networks and wait for networks that are not
        in pending, out-of-sync, or deployed state to become ready before proceeding.

        This method should be called right after get_have() to ensure networks from
        the playbook (want) are in a stable state before making any changes.
        """

        time.sleep(3)
        networks_to_check = set()

        # Get networks from want_create that exist in ND and need to be checked
        for want_net in self.want_create:
            want_net_name = want_net['networkName']

            # Find corresponding network in have_attach to see if it exists
            have_net = next(
                (net for net in self.have_attach if net["networkName"] == want_net_name),
                None
            )

            if have_net:
                # Network exists in DCNM, check if any attachments need deployment check
                needs_check = False
                if have_net.get("lanAttachList"):
                    for attach in have_net["lanAttachList"]:
                        # Check if attachment is not fully deployed (is_deploy=False means not IN-SYNC)
                        if not attach.get("is_deploy", False):
                            needs_check = True
                            break

                if needs_check:
                    networks_to_check.add(want_net_name)

        # Wait for networks to be in ready state before proceeding
        if networks_to_check:
            networks_list = list(networks_to_check)
            deployment_states = self.wait_for_deploy_ready(networks_list)

            # Store deployment_states as instance variable for use in diff methods
            self.deployment_states = deployment_states

            # Check if any networks failed to reach ready state
            # Success states: DEPLOYED, PENDING, OUT-OF-SYNC, NA
            # Failure states: FAILED, TIMEOUT and any other unexpected states
            failed_networks = [net for net, state in deployment_states.items()
                               if state not in ['DEPLOYED', 'PENDING', 'OUT-OF-SYNC', 'NA']]

            if failed_networks:
                error_msg = f"Pre-operation deployment check failed. Want networks not ready: {failed_networks}. Network states: {deployment_states}"

                # Call failure immediately for failed networks
                self.failure(error_msg)
        else:
            # Initialize empty deployment_states when no networks need checking
            self.deployment_states = {}

    def get_diff_delete(self):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        diff_detach = []
        diff_undeploy = {}
        diff_delete = {}

        all_nets = ""

        if self.config:

            for want_c in self.want_create:
                if not next(
                    (have_c for have_c in self.have_create if have_c["networkName"] == want_c["networkName"]),
                    None,
                ):
                    continue
                diff_delete.update({want_c["networkName"]: "DEPLOYED"})

                have_a = next(
                    (attach for attach in self.have_attach if attach["networkName"] == want_c["networkName"]),
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
                    all_nets += have_a["networkName"] + ","
            if all_nets:
                diff_undeploy.update({"networkNames": all_nets[:-1]})

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
                    all_nets += have_a["networkName"] + ","

                diff_delete.update({have_a["networkName"]: "DEPLOYED"})
            if all_nets:
                diff_undeploy.update({"networkNames": all_nets[:-1]})

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

        all_nets = ""
        diff_delete = {}

        warn_msg = self.get_diff_replace()

        diff_create = self.diff_create
        diff_attach = self.diff_attach
        diff_detach = self.diff_detach
        diff_deploy = self.diff_deploy
        diff_undeploy = self.diff_undeploy

        for have_a in self.have_attach:
            # This block will take care of deleting all the networks that are only present on ND but not on playbook
            # The "if not found" block will go through all attachments under those networks and update them so that
            # they will be detached and also the network name will be added to delete payload.

            found = next(
                (net for net in self.want_create if net["networkName"] == have_a["networkName"]),
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
                    all_nets += have_a["networkName"] + ","

                # The following is added just to help in deletion, we need to wait for detach transaction to complete
                # before attempting to delete the network.
                diff_delete.update({have_a["networkName"]: "DEPLOYED"})

        if all_nets:
            diff_undeploy.update({"networkNames": all_nets[:-1]})

        self.diff_create = diff_create
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy
        self.diff_undeploy = diff_undeploy
        self.diff_delete = diff_delete
        self.diff_detach = diff_detach
        return warn_msg

    def get_diff_replace(self):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        all_nets = ""

        warn_msg = self.get_diff_merge(replace=True)
        diff_create = self.diff_create
        diff_attach = self.diff_attach
        diff_deploy = self.diff_deploy

        for have_a in self.have_attach:
            r_net_list = []
            h_in_w = False
            for want_a in self.want_attach:
                # This block will take care of deleting any attachments that are present only on DCNM
                # but, not on the playbook. In this case, the playbook will have a network and few attaches under it,
                # but, the attaches may be different to what the ND has for the same network.
                if have_a["networkName"] == want_a["networkName"]:
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
                            r_net_list.append(a_h)
                    break

            if not h_in_w:
                # This block will take care of deleting all the attachments which are in ND but
                # are not mentioned in the playbook. The playbook just has the network, but, does not have any attach
                # under it.
                found = next(
                    (net for net in self.want_create if net["networkName"] == have_a["networkName"]),
                    None,
                )
                if found:
                    atch_h = have_a["lanAttachList"]
                    for a_h in atch_h:
                        if not a_h["isAttached"]:
                            continue
                        del a_h["isAttached"]
                        a_h.update({"deployment": False})
                        r_net_list.append(a_h)

            if r_net_list:
                in_diff = False
                for d_attach in self.diff_attach:
                    if have_a["networkName"] == d_attach["networkName"]:
                        in_diff = True
                        d_attach["lanAttachList"].extend(r_net_list)
                        break

                if not in_diff:
                    r_net_dict = {
                        "networkName": have_a["networkName"],
                        "lanAttachList": r_net_list,
                    }
                    diff_attach.append(r_net_dict)
                    all_nets += have_a["networkName"] + ","

        if all_nets:
            modified_all_nets = copy.deepcopy(all_nets[:-1].split(","))
            # If the playbook sets the deploy key to False, then we need to remove the network from the deploy list.
            for net in all_nets[:-1].split(","):
                want_net_data = self.find_dict_in_list_by_key_value(search=self.config, key="net_name", value=net)
                if (want_net_data is not None) and (want_net_data.get("deploy") is False):
                    modified_all_nets.remove(net)
            all_nets = ",".join(modified_all_nets)

        if not all_nets:
            self.diff_create = diff_create
            self.diff_attach = diff_attach
            self.diff_deploy = diff_deploy
            return warn_msg

        if not self.diff_deploy:
            diff_deploy.update({"networkNames": all_nets})
        else:
            nets = self.diff_deploy["networkNames"] + "," + all_nets
            diff_deploy.update({"networkNames": nets})

        self.diff_create = diff_create
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy
        return warn_msg

    def get_diff_merge(self, replace=False):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        msg += f"replace == {replace}"
        self.log.debug(msg)

        #
        # Special cases:
        # 1. Update gateway on an existing network:
        #    We need to use the network_update API with PUT method to update the nw with new gw.
        #    attach logic remains same, but, we need to re-deploy the network in any case to reflect the new gw.
        # 2. Update vlan-id on an existing network:
        #    This change will only affect new attachments of the same network.
        # 3. Auto generate networkId if its not mentioned by user:
        #    In this case, we need to query the ND to get a usable ID and use it in the payload.
        #    And also, any such network create requests need to be pushed individually(not bulk op).

        diff_create = []
        diff_create_update = []
        diff_create_quick = []
        diff_attach = []
        diff_deploy = {}
        prev_net_id_fetched = None

        gw_changed = {}
        tg_changed = {}
        warn_msg = None
        l2only_changed = {}
        vn_changed = {}
        intdesc_changed = {}
        mtu_changed = {}
        arpsup_changed = {}
        dhcp1_ip_changed = {}
        dhcp2_ip_changed = {}
        dhcp3_ip_changed = {}
        dhcp1_vrf_changed = {}
        dhcp2_vrf_changed = {}
        dhcp3_vrf_changed = {}
        dhcp_servers_changed = {}
        dhcp_loopback_changed = {}
        multicast_group_address_changed = {}
        gwv6_changed = {}
        sec_gw1_changed = {}
        sec_gw2_changed = {}
        sec_gw3_changed = {}
        sec_gw4_changed = {}
        trm_en_changed = {}
        rt_both_changed = {}
        l3gw_onbd_changed = {}
        nf_en_changed = {}
        intvlan_nfmon_changed = {}
        vlan_nfmon_changed = {}

        for want_c in self.want_create:
            found = False
            for have_c in self.have_create:
                if want_c["networkName"] == have_c["networkName"]:

                    found = True
                    (
                        diff,
                        gw_chg,
                        tg_chg,
                        warn_msg,
                        l2only_chg,
                        vn_chg,
                        idesc_chg,
                        mtu_chg,
                        arpsup_chg,
                        dhcp1_ip_chg,
                        dhcp2_ip_chg,
                        dhcp3_ip_chg,
                        dhcp1_vrf_chg,
                        dhcp2_vrf_chg,
                        dhcp3_vrf_chg,
                        dhcp_servers_chg,
                        dhcp_loopbk_chg,
                        mcast_grp_chg,
                        gwv6_chg,
                        sec_gw1_chg,
                        sec_gw2_chg,
                        sec_gw3_chg,
                        sec_gw4_chg,
                        trm_en_chg,
                        rt_both_chg,
                        l3gw_onbd_chg,
                        nf_en_chg,
                        intvlan_nfmon_chg,
                        vlan_nfmon_chg,
                    ) = self.diff_for_create(want_c, have_c)

                    gw_changed.update({want_c["networkName"]: gw_chg})
                    tg_changed.update({want_c["networkName"]: tg_chg})
                    l2only_changed.update({want_c["networkName"]: l2only_chg})
                    vn_changed.update({want_c["networkName"]: vn_chg})
                    intdesc_changed.update({want_c["networkName"]: idesc_chg})
                    mtu_changed.update({want_c["networkName"]: mtu_chg})
                    arpsup_changed.update({want_c["networkName"]: arpsup_chg})
                    dhcp1_ip_changed.update({want_c["networkName"]: dhcp1_ip_chg})
                    dhcp2_ip_changed.update({want_c["networkName"]: dhcp2_ip_chg})
                    dhcp3_ip_changed.update({want_c["networkName"]: dhcp3_ip_chg})
                    dhcp1_vrf_changed.update({want_c["networkName"]: dhcp1_vrf_chg})
                    dhcp2_vrf_changed.update({want_c["networkName"]: dhcp2_vrf_chg})
                    dhcp3_vrf_changed.update({want_c["networkName"]: dhcp3_vrf_chg})
                    dhcp_servers_changed.update({want_c["networkName"]: dhcp_servers_chg})
                    dhcp_loopback_changed.update({want_c["networkName"]: dhcp_loopbk_chg})
                    if self.is_ms_fabric is False:
                        multicast_group_address_changed.update({want_c["networkName"]: mcast_grp_chg})
                    gwv6_changed.update({want_c["networkName"]: gwv6_chg})
                    sec_gw1_changed.update({want_c["networkName"]: sec_gw1_chg})
                    sec_gw2_changed.update({want_c["networkName"]: sec_gw2_chg})
                    sec_gw3_changed.update({want_c["networkName"]: sec_gw3_chg})
                    sec_gw4_changed.update({want_c["networkName"]: sec_gw4_chg})
                    trm_en_changed.update({want_c["networkName"]: trm_en_chg})
                    rt_both_changed.update({want_c["networkName"]: rt_both_chg})
                    l3gw_onbd_changed.update({want_c["networkName"]: l3gw_onbd_chg})
                    nf_en_changed.update({want_c["networkName"]: nf_en_chg})
                    intvlan_nfmon_changed.update({want_c["networkName"]: intvlan_nfmon_chg})
                    vlan_nfmon_changed.update({want_c["networkName"]: vlan_nfmon_chg})
                    if diff:
                        diff_create_update.append(diff)
                    break
            if not found:
                net_id = want_c.get("networkId", None)

                if not net_id:
                    # networkId(VNI-id) is not provided by user.
                    # Need to query ND to fetch next available networkId and use it here.

                    method = "POST"

                    attempt = 0
                    while attempt < 10:
                        attempt += 1
                        path = self.paths["GET_NET_ID"].format(self.fabric)
                        if self.dcnm_version > 11:
                            net_id_obj = dcnm_send(self.module, "GET", path)
                        else:
                            net_id_obj = dcnm_send(self.module, method, path)

                        missing_fabric, not_ok = self.handle_response(net_id_obj, "query_dcnm")

                        if missing_fabric or not_ok:
                            msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
                            msg2 = "Unable to generate networkId for network: {0} " "under fabric: {1}".format(want_c["networkName"], self.fabric)

                            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

                        if not net_id_obj["DATA"]:
                            continue

                        if self.dcnm_version == 11:
                            net_id = net_id_obj["DATA"].get("segmentId")
                        elif self.dcnm_version >= 12:
                            net_id = net_id_obj["DATA"].get("l2vni")
                        else:
                            msg = "Unsupported ND version: version {0}".format(self.dcnm_version)
                            self.module.fail_json(msg)

                        if net_id != prev_net_id_fetched:
                            want_c.update({"networkId": net_id})
                            prev_net_id_fetched = net_id
                            break

                    if not net_id:
                        self.module.fail_json(
                            msg="Unable to generate networkId for network: {0} " "under fabric: {1}".format(want_c["networkName"], self.fabric)
                        )

                    create_path = self.paths["GET_NET"].format(self.fabric)
                    diff_create_quick.append(want_c)

                    if self.module.check_mode:
                        continue

                    resp = dcnm_send(self.module, method, create_path, json.dumps(want_c))
                    self.result["response"].append(resp)
                    fail, self.result["changed"] = self.handle_response(resp, "create")
                    if fail:
                        self.failure(resp)

                else:
                    diff_create.append(want_c)

        # Check for deployment needed due to configuration changes (without attachment changes)
        all_nets = []
        for want_a in self.want_attach:
            dep_net = ""
            found = False
            for have_a in self.have_attach:
                if want_a["networkName"] == have_a["networkName"]:

                    found = True
                    diff, net = self.diff_for_attach_deploy(want_a["lanAttachList"], have_a["lanAttachList"], replace)

                    if diff:
                        base = want_a.copy()
                        del base["lanAttachList"]
                        base.update({"lanAttachList": diff})
                        diff_attach.append(base)
                        if net:
                            dep_net = want_a["networkName"]
                    else:
                        # Check if any configuration changes require deployment
                        network_name = want_a["networkName"]

                        if (
                            net
                            or gw_changed.get(want_a["networkName"], False)
                            or tg_changed.get(want_a["networkName"], False)
                            or l2only_changed.get(want_a["networkName"], False)
                            or vn_changed.get(want_a["networkName"], False)
                            or intdesc_changed.get(want_a["networkName"], False)
                            or mtu_changed.get(want_a["networkName"], False)
                            or arpsup_changed.get(want_a["networkName"], False)
                            or dhcp1_ip_changed.get(want_a["networkName"], False)
                            or dhcp2_ip_changed.get(want_a["networkName"], False)
                            or dhcp3_ip_changed.get(want_a["networkName"], False)
                            or dhcp1_vrf_changed.get(want_a["networkName"], False)
                            or dhcp2_vrf_changed.get(want_a["networkName"], False)
                            or dhcp3_vrf_changed.get(want_a["networkName"], False)
                            or dhcp_servers_changed.get(want_a["networkName"], False)
                            or dhcp_loopback_changed.get(want_a["networkName"], False)
                            or multicast_group_address_changed.get(want_a["networkName"], False)
                            or gwv6_changed.get(want_a["networkName"], False)
                            or sec_gw1_changed.get(want_a["networkName"], False)
                            or sec_gw2_changed.get(want_a["networkName"], False)
                            or sec_gw3_changed.get(want_a["networkName"], False)
                            or sec_gw4_changed.get(want_a["networkName"], False)
                            or trm_en_changed.get(want_a["networkName"], False)
                            or rt_both_changed.get(want_a["networkName"], False)
                            or l3gw_onbd_changed.get(want_a["networkName"], False)
                            or nf_en_changed.get(want_a["networkName"], False)
                            or intvlan_nfmon_changed.get(want_a["networkName"], False)
                            or vlan_nfmon_changed.get(want_a["networkName"], False)
                        ):
                            dep_net = want_a["networkName"]

            if not found and want_a.get("lanAttachList"):
                atch_list = []
                for attach in want_a["lanAttachList"]:
                    # Saftey check
                    if attach.get("isAttached"):
                        if attach.get("torports"):
                            torconfig_list = []
                            for tor_w in attach["torports"]:
                                torconfig_list.append(tor_w["switch"] + "(" + tor_w["torPorts"] + ")")
                            attach.update({"torPorts": " ".join(torconfig_list)})
                        del attach["torports"]
                        del attach["isAttached"]
                        atch_list.append(attach)
                if atch_list:
                    base = want_a.copy()
                    del base["lanAttachList"]
                    base.update({"lanAttachList": atch_list})
                    diff_attach.append(base)
                    if bool(attach["is_deploy"]):
                        dep_net = want_a["networkName"]
                for atch in atch_list:
                    atch["deployment"] = True

            if dep_net:
                all_nets.append(dep_net)

        modified_all_nets = copy.deepcopy(all_nets)
        if all_nets:
            # If the playbook sets the deploy key to False, then we need to remove the network from the deploy list.
            for net in all_nets:
                want_net_data = self.find_dict_in_list_by_key_value(search=self.config, key="net_name", value=net)
                if (want_net_data is not None) and (want_net_data.get("deploy") is False):
                    modified_all_nets.remove(net)

        # Check for networks that have deploy=True in config but are not in deployed state
        # Use deployment_states from check_want_networks_deployment_state() instead of new API calls
        additional_deploy_nets = []

        for cfg in self.config:
            net_name = cfg.get("net_name")
            deploy_setting = cfg.get("deploy", True)  # Default to True if not specified

            # Only check networks that have deploy=True and are not already in modified_all_nets
            if deploy_setting and net_name and net_name not in modified_all_nets:
                # Check if this network exists in ND (have_attach or have_create)
                network_exists = False
                for have_net in self.have_create:
                    if have_net.get("networkName") == net_name:
                        network_exists = True
                        break

                if not network_exists:
                    for have_net in self.have_attach:
                        if have_net.get("networkName") == net_name:
                            network_exists = True
                            break

                if network_exists:
                    # Check deployment status from cached deployment_states
                    if net_name in self.deployment_states:
                        network_status = self.deployment_states[net_name]

                        # Add to deployment if not in DEPLOYED or NA state
                        if network_status not in ["DEPLOYED", "NA"]:
                            additional_deploy_nets.append(net_name)

        # Add additional networks to the deployment list (avoid duplicates)
        if additional_deploy_nets:
            original_count = len(modified_all_nets)
            modified_all_nets.extend(additional_deploy_nets)
            # Remove duplicates by converting to set and back to list
            modified_all_nets = list(set(modified_all_nets))
            final_count = len(modified_all_nets)
            added_count = final_count - original_count

        if modified_all_nets:
            diff_deploy.update({"networkNames": ",".join(modified_all_nets)})

        self.diff_create = diff_create
        self.diff_create_update = diff_create_update
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy
        self.diff_create_quick = diff_create_quick

        return warn_msg

    def format_diff(self):

        diff = []

        diff_create = copy.deepcopy(self.diff_create)
        diff_create_quick = copy.deepcopy(self.diff_create_quick)
        diff_create_update = copy.deepcopy(self.diff_create_update)
        diff_attach = copy.deepcopy(self.diff_attach)
        diff_detach = copy.deepcopy(self.diff_detach)
        diff_deploy = self.diff_deploy["networkNames"].split(",") if self.diff_deploy else []
        diff_undeploy = self.diff_undeploy["networkNames"].split(",") if self.diff_undeploy else []

        diff_create.extend(diff_create_quick)
        diff_create.extend(diff_create_update)
        diff_attach.extend(diff_detach)
        diff_deploy.extend(diff_undeploy)

        for want_d in diff_create:

            found_a = next(
                (net for net in diff_attach if net["networkName"] == want_d["networkName"]),
                None,
            )

            found_c = want_d

            json_to_dict = json.loads(found_c["networkTemplateConfig"])

            found_c.update({"net_name": found_c["networkName"]})
            found_c.update({"vrf_name": found_c.get("vrf", "NA")})
            found_c.update({"net_id": found_c["networkId"]})
            found_c.update({"vlan_id": json_to_dict.get("vlanId", "")})
            found_c.update({"gw_ip_subnet": json_to_dict.get("gatewayIpAddress", "")})
            found_c.update({"net_template": found_c["networkTemplate"]})
            found_c.update({"net_extension_template": found_c["networkExtensionTemplate"]})
            found_c.update({"is_l2only": json_to_dict.get("isLayer2Only", False)})
            found_c.update({"vlan_name": json_to_dict.get("vlanName", "")})
            found_c.update({"int_desc": json_to_dict.get("intfDescription", "")})
            found_c.update({"mtu_l3intf": json_to_dict.get("mtu", "")})
            found_c.update({"arp_suppress": json_to_dict.get("suppressArp", False)})
            found_c.update({"dhcp_srvr1_ip": json_to_dict.get("dhcpServerAddr1", "")})
            found_c.update({"dhcp_srvr2_ip": json_to_dict.get("dhcpServerAddr2", "")})
            found_c.update({"dhcp_srvr3_ip": json_to_dict.get("dhcpServerAddr3", "")})
            found_c.update({"dhcp_srvr1_vrf": json_to_dict.get("vrfDhcp", "")})
            found_c.update({"dhcp_srvr2_vrf": json_to_dict.get("vrfDhcp2", "")})
            found_c.update({"dhcp_srvr3_vrf": json_to_dict.get("vrfDhcp3", "")})
            found_c.update({"dhcp_servers": json_to_dict.get("dhcpServers", "")})
            found_c.update({"dhcp_loopback_id": json_to_dict.get("loopbackId", "")})
            found_c.update({"multicast_group_address": json_to_dict.get("mcastGroup", "")})
            found_c.update({"gw_ipv6_subnet": json_to_dict.get("gatewayIpV6Address", "")})
            found_c.update({"secondary_ip_gw1": json_to_dict.get("secondaryGW1", "")})
            found_c.update({"secondary_ip_gw2": json_to_dict.get("secondaryGW2", "")})
            found_c.update({"secondary_ip_gw3": json_to_dict.get("secondaryGW3", "")})
            found_c.update({"secondary_ip_gw4": json_to_dict.get("secondaryGW4", "")})
            found_c.update({"trm_enable": json_to_dict.get("trmEnabled", False)})
            found_c.update({"route_target_both": json_to_dict.get("rtBothAuto", False)})
            found_c.update({"l3gw_on_border": json_to_dict.get("enableL3OnBorder", False)})
            if self.dcnm_version > 11:
                found_c.update({"netflow_enable": json_to_dict.get("ENABLE_NETFLOW", False)})
                found_c.update({"intfvlan_nf_monitor": json_to_dict.get("SVI_NETFLOW_MONITOR", "")})
                found_c.update({"vlan_nf_monitor": json_to_dict.get("VLAN_NETFLOW_MONITOR", "")})
            found_c.update({"attach": []})

            del found_c["fabric"]
            del found_c["networkName"]
            del found_c["networkId"]
            del found_c["networkTemplate"]
            del found_c["networkExtensionTemplate"]
            del found_c["networkTemplateConfig"]
            del found_c["vrf"]

            if diff_deploy and found_c["net_name"] in diff_deploy:
                diff_deploy.remove(found_c["net_name"])
            if not found_a:
                diff.append(found_c)
                continue

            attach = found_a["lanAttachList"]

            for a_w in attach:
                attach_d = {}
                detach_d = {}

                for k, v in self.ip_sn.items():
                    if v == a_w["serialNumber"]:
                        attach_d.update({"ip_address": k})
                        break
                if a_w["detachSwitchPorts"]:
                    detach_d.update({"ip_address": attach_d["ip_address"]})
                    detach_d.update({"ports": a_w["detachSwitchPorts"]})
                    detach_d.update({"deploy": False})
                    found_c["attach"].append(detach_d)
                attach_d.update({"ports": a_w["switchPorts"]})
                attach_d.update({"deploy": a_w["deployment"]})
                if a_w.get("torPorts"):
                    attach_d.update({"tor_ports": a_w["torPorts"]})
                found_c["attach"].append(attach_d)

            diff.append(found_c)

            diff_attach.remove(found_a)

        for vrf in diff_attach:
            new_attach_dict = {}
            new_attach_list = []
            attach = vrf["lanAttachList"]

            for a_w in attach:
                attach_d = {}
                detach_d = {}

                for k, v in self.ip_sn.items():
                    if v == a_w["serialNumber"]:
                        attach_d.update({"ip_address": k})
                        break
                if a_w["detachSwitchPorts"]:
                    detach_d.update({"ip_address": attach_d["ip_address"]})
                    detach_d.update({"ports": a_w["detachSwitchPorts"]})
                    detach_d.update({"deploy": False})
                    new_attach_list.append(detach_d)
                attach_d.update({"ports": a_w["switchPorts"]})
                attach_d.update({"deploy": a_w["deployment"]})
                if a_w.get("torPorts"):
                    attach_d.update({"tor_ports": a_w["torPorts"]})
                new_attach_list.append(attach_d)

            if new_attach_list:
                if diff_deploy and vrf["networkName"] in diff_deploy:
                    diff_deploy.remove(vrf["networkName"])
                new_attach_dict.update({"attach": new_attach_list})
                new_attach_dict.update({"net_name": vrf["networkName"]})
                diff.append(new_attach_dict)

        for net in diff_deploy:
            new_deploy_dict = {"net_name": net}
            diff.append(new_deploy_dict)

        self.diff_input_format = diff

    def get_diff_query(self):

        method = "GET"
        path = self.paths["GET_VRF"].format(self.fabric)

        vrf_objects = dcnm_send(self.module, method, path)

        missing_fabric, not_ok = self.handle_response(vrf_objects, "query_dcnm")

        if missing_fabric or not_ok:
            msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find VRFs under fabric: {0}".format(self.fabric)

            self.module.fail_json(msg=msg1 if missing_fabric else msg2)
            return

        if self.config:
            query = []
            if self.have_create or self.have_attach:
                for want_c in self.want_create:
                    # Query the Network
                    item = {"parent": {}, "attach": []}
                    path = self.paths["GET_NET_NAME"].format(self.fabric, want_c["networkName"])
                    network = dcnm_send(self.module, method, path)

                    if not network["DATA"]:
                        continue
                    missing_network, not_ok = self.handle_response(network, "query_dcnm")
                    if missing_network or not_ok:
                        continue

                    net = network["DATA"]
                    if want_c["networkName"] == net["networkName"]:
                        item["parent"] = net
                        item["parent"]["networkTemplateConfig"] = json.loads(net["networkTemplateConfig"])

                        # Query the Attachment for the found Networks
                        path = self.paths["GET_NET_ATTACH"].format(self.fabric, want_c["networkName"])
                        net_attach_objects = dcnm_send(self.module, method, path)

                        if not net_attach_objects["DATA"]:
                            return

                        for net_attach in net_attach_objects["DATA"]:
                            if want_c["networkName"] == net_attach["networkName"]:
                                if not net_attach.get("lanAttachList"):
                                    continue
                                attach_list = net_attach["lanAttachList"]

                                for attach in attach_list:
                                    # append the attach network details
                                    item["attach"].append(attach)
                                query.append(item)

        else:
            query = []
            path = self.paths["GET_NET"].format(self.fabric)
            networks = dcnm_send(self.module, method, path)

            if not networks["DATA"]:
                return

            for net in networks["DATA"]:
                item = {"parent": {}, "attach": []}
                # append the parent network details
                item["parent"] = net
                item["parent"]["networkTemplateConfig"] = json.loads(net["networkTemplateConfig"])

                # fetch the attachment for the network
                path = self.paths["GET_NET_ATTACH"].format(self.fabric, net["networkName"])
                net_attach_objects = dcnm_send(self.module, method, path)

                if not net_attach_objects["DATA"]:
                    return

                for net_attach in net_attach_objects["DATA"]:
                    if not net_attach.get("lanAttachList"):
                        continue
                    attach_list = net_attach["lanAttachList"]

                    for attach in attach_list:
                        # append the attach network details
                        item["attach"].append(attach)
                    query.append(item)

        self.query = query

    def detach_and_deploy_for_del(self, net):
        method = "GET"

        payload_net = {}
        deploy_payload = {}
        payload_net["networkName"] = net["networkName"]
        payload_net["lanAttachList"] = []
        attach_list = net["switchList"]
        for atch in attach_list:
            payload_atch = {}
            if atch["lanAttachedState"].upper() == "PENDING":
                payload_atch["serialNumber"] = atch["serialNumber"]
                payload_atch["networkName"] = net["networkName"]
                payload_atch["fabric"] = net["fabric"]
                payload_atch["deployment"] = False
                payload_net["lanAttachList"].append(payload_atch)

                deploy_payload[atch["serialNumber"]] = net["networkName"]

        if payload_net["lanAttachList"]:
            payload = [payload_net]
            
            # Update the fabric name to specific fabric which the switches are part of.
            self.update_ms_fabric(payload)
            
            method = "POST"
            path = self.paths["GET_NET"].format(self.fabric) + "/attachments"
            
            resp = dcnm_send(self.module, method, path, json.dumps(payload))
            
            self.result["response"].append(resp)
            fail, dummy_changed = self.handle_response(resp, "attach")
            if fail:
                self.failure(resp)

        method = "POST"
        path = self.paths["GET_NET_SWITCH_DEPLOY"].format(self.fabric)
        resp = dcnm_send(self.module, method, path, json.dumps(deploy_payload))
        self.result["response"].append(resp)
        fail, dummy_changed = self.handle_response(resp, "deploy")
        if fail:
            self.failure(resp)

    def wait_for_del_ready(self):

        method = "GET"
        if self.diff_delete:
            for net in self.diff_delete:
                state = False
                # For multicluster_parent, use GET_NET_ATTACH instead of GET_NET_STATUS
                if self.fabric_type == "multicluster_parent":
                    path = self.paths["GET_NET_ATTACH"].format(self.fabric, net)
                else:
                    path = self.paths["GET_NET_STATUS"].format(self.fabric, net)
                
                retry = max(100 // self.WAIT_TIME_FOR_DELETE_LOOP, 1)
                deploy_started = False
                while not state and retry >= 0:
                    retry -= 1
                    resp = dcnm_send(self.module, method, path)      
                    state = True
                    
                    # For multicluster_parent with GET_NET_ATTACH, response structure is different
                    if self.fabric_type == "multicluster_parent":
                        if resp.get("DATA") is None:
                            time.sleep(self.WAIT_TIME_FOR_DELETE_LOOP)
                            state = False
                            continue
                        
                        # GET_NET_ATTACH returns: [{'networkName': 'name', 'lanAttachList': [attachments]}]
                        if isinstance(resp["DATA"], list) and len(resp["DATA"]) > 0:
                            # Get the lanAttachList from the first element
                            attach_list = resp["DATA"][0].get("lanAttachList", [])
                            
                            # Check for PENDING state and trigger detach/deploy if needed
                            for attach in attach_list:
                                if attach.get("lanAttachState") == "PENDING" and not deploy_started:
                                    # For multicluster, we need to convert the response structure
                                    # from: [{'networkName': 'name', 'lanAttachList': [attachments]}]
                                    # to: {'networkName': 'name', 'fabric': 'fabric', 'switchList': [attachments]}
                                    
                                    # Convert multicluster response to format expected by detach_and_deploy_for_del
                                    adapted_net = {
                                        "networkName": resp["DATA"][0]["networkName"],
                                        "fabric": self.fabric,
                                        "switchList": resp["DATA"][0]["lanAttachList"]
                                    }
                                    
                                    # Note: lanAttachList uses 'lanAttachState' while switchList uses 'lanAttachedState'
                                    # We need to rename the key for compatibility
                                    for switch in adapted_net["switchList"]:
                                        if "lanAttachState" in switch:
                                            switch["lanAttachedState"] = switch["lanAttachState"]
                                        if "switchSerialNo" in switch:
                                            switch["serialNumber"] = switch["switchSerialNo"]
                                    
                                    self.detach_and_deploy_for_del(adapted_net)
                                    deploy_started = True
                            
                            for attach in attach_list:
                                if attach.get("lanAttachState") == "OUT-OF-SYNC" or attach.get("lanAttachState") == "FAILED":
                                    self.diff_delete.update({net: "OUT-OF-SYNC"})
                                    break
                                if attach.get("lanAttachState") != "NA":
                                    self.diff_delete.update({net: "DEPLOYED"})
                                    state = False
                                    time.sleep(self.WAIT_TIME_FOR_DELETE_LOOP)
                                    break
                            else:
                                # All attachments are NA or no attachments
                                self.diff_delete.update({net: "NA"})
                        else:
                            # No data found, network is ready
                            self.diff_delete.update({net: "NA"})
                    
                    else:
                        # Original logic for GET_NET_STATUS (non-multicluster)
                        if resp["DATA"]:
                            if resp["DATA"]["networkStatus"].upper() == "PENDING" and not deploy_started:
                                self.detach_and_deploy_for_del(resp["DATA"])
                                deploy_started = True
                            attach_list = resp["DATA"]["switchList"]
                            for atch in attach_list:
                                if atch["lanAttachedState"].upper() == "OUT-OF-SYNC" or atch["lanAttachedState"].upper() == "FAILED":
                                    self.diff_delete.update({net: "OUT-OF-SYNC"})
                                    break
                                if atch["lanAttachedState"].upper() != "NA":
                                    self.diff_delete.update({net: "DEPLOYED"})
                                    state = False
                                    time.sleep(self.WAIT_TIME_FOR_DELETE_LOOP)
                                    break
                                self.diff_delete.update({net: "NA"})
                if retry < 0:
                    self.diff_delete.update({net: "TIMEOUT"})
                    return False

            return True

    def wait_for_deploy_ready(self, networks_to_check):
        """
        Wait for networks to reach a ready state for operations.

        Based on the actual API response structure:
        - networkStatus can be: "DEPLOYED", "PENDING", "OUT-OF-SYNC", "FAILED", etc.
        - DEPLOYED, PENDING, NA are immediately ready
        - OUT-OF-SYNC and FAILED require two consecutive checks to be considered ready

        Parameters:
            networks_to_check (list): List of network names to check deployment status

        Returns:
            dict: Dictionary mapping network names to their final states
        """

        method = "GET"
        network_states = {}

        if not networks_to_check:
            return network_states

        for net in networks_to_check:
            state_achieved = False
            path = self.paths["GET_NET_STATUS"].format(self.fabric, net)
            retry = max(100 // self.WAIT_TIME_FOR_DELETE_LOOP, 1)
            # Track previous state for this network to detect consecutive OUT-OF-SYNC states
            prev_state = None

            while not state_achieved and retry >= 0:
                retry -= 1
                resp = dcnm_send(self.module, method, path)

                if resp["DATA"] and "networkStatus" in resp["DATA"]:
                    network_status = resp["DATA"]["networkStatus"].upper()

                    # Check if network is in ready state
                    if network_status in ["DEPLOYED", "PENDING", "NA"]:
                        # These states are immediately ready
                        network_states[net] = network_status
                        state_achieved = True
                        break
                    elif network_status == "OUT-OF-SYNC":
                        # OUT-OF-SYNC requires two consecutive checks to be considered ready
                        if prev_state == "OUT-OF-SYNC":
                            network_states[net] = network_status
                            state_achieved = True
                            break
                    elif network_status == "FAILED":
                        # FAILED requires two consecutive checks to be considered ready
                        if prev_state == "FAILED":
                            network_states[net] = network_status
                            state_achieved = True
                            break
                    else:
                        # Network not in ready state yet, keep waiting
                        time.sleep(self.WAIT_TIME_FOR_DELETE_LOOP)
                    prev_state = network_status
                else:
                    # No data received, treat as not ready
                    time.sleep(self.WAIT_TIME_FOR_DELETE_LOOP)

            # Handle timeout case
            if retry < 0:
                network_states[net] = "TIMEOUT"

        return network_states

    def update_ms_fabric(self, diff):
        # Update fabric field for both multisite (MFD) and multicluster parent fabrics
        if not self.is_ms_fabric and self.fabric_type != "multicluster_parent":
            return

        for list_elem in diff:
            for node in list_elem["lanAttachList"]:
                old_fabric = node.get("fabric")
                sn = node["serialNumber"]
                new_fabric = self.sn_fab.get(sn, old_fabric)
                node["fabric"] = new_fabric


    def push_to_remote(self, is_rollback=False):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        msg += f"is_rollback: {is_rollback}"
        self.log.debug(msg)

        path = self.paths["GET_NET"].format(self.fabric)

        method = "PUT"
        if self.diff_create_update:
            # Get skipped attributes for parent fabrics
            skipped_attributes = self.get_skipped_attributes()
            template_mapping = self.get_template_config_mapping()

            # Convert skipped spec attributes to template config keys
            skipped_template_keys = set()
            for attr in skipped_attributes:
                if attr in template_mapping:
                    skipped_template_keys.add(template_mapping[attr])

            for net in self.diff_create_update:
                # Remove skipped attributes from template config for parent fabrics
                if net.get("networkTemplateConfig") and skipped_template_keys:
                    json_to_dict = json.loads(net["networkTemplateConfig"])
                    for key in list(json_to_dict.keys()):
                        if key in skipped_template_keys:
                            del json_to_dict[key]
                    net["networkTemplateConfig"] = json.dumps(json_to_dict)

                update_path = path + "/{0}".format(net["networkName"])
                resp = dcnm_send(self.module, method, update_path, json.dumps(net))
                self.result["response"].append(resp)
                fail, self.result["changed"] = self.handle_response(resp, "create")
                if fail:
                    if is_rollback:
                        self.failed_to_rollback = True
                        return
                    self.failure(resp)

        #
        # The detach and un-deploy operations are executed before the create,attach and deploy to particularly
        # address cases where a VLAN of a network being deleted is re-used on a new network being created. This is
        # needed specially for state: overridden
        #

        method = "POST"
        if self.diff_detach:
            detach_path = path + "/attachments"

            # Update the fabric name to specific fabric which the switches are part of.
            self.update_ms_fabric(self.diff_detach)

            for d_a in self.diff_detach:
                for v_a in d_a["lanAttachList"]:
                    if v_a.get("is_deploy"):
                        del v_a["is_deploy"]

            resp = dcnm_send(self.module, method, detach_path, json.dumps(self.diff_detach))
            self.result["response"].append(resp)
            fail, self.result["changed"] = self.handle_response(resp, "attach")
            if fail:
                if is_rollback:
                    self.failed_to_rollback = True
                    return
                self.failure(resp)

        method = "POST"
        payload = copy.deepcopy(self.diff_undeploy)
        if self.diff_undeploy:
            # For multicluster_parent, use special endpoint and payload format
            # For all others (including multicluster_child), use standard /deployments path
            if self.fabric_type == "multicluster_parent":
                deploy_path = self.paths["GET_NET_SWITCH_DEPLOY"].format(self.fabric)
                deploy_payload = self.transform_deploy_payload_for_multicluster(payload)
            else:
                # Standard path for standalone, multisite, and multicluster_child
                path = self.paths["GET_NET"].format(self.fabric)
                deploy_path = path + "/deployments"
                deploy_payload = payload
            
            resp = dcnm_send(self.module, method, deploy_path, json.dumps(deploy_payload))
            # Use the self.wait_for_del_ready() function to refresh the state
            # of self.diff_delete dict and re-attempt the undeploy action if
            # the state of the network is "OUT-OF-SYNC"
            self.wait_for_del_ready()
            for net, state in self.diff_delete.items():
                if state.upper() == "OUT-OF-SYNC":
                    resp = dcnm_send(self.module, method, deploy_path, json.dumps(self.diff_undeploy))

            self.result["response"].append(resp)
            fail, self.result["changed"] = self.handle_response(resp, "deploy")
            if fail:
                if is_rollback:
                    self.failed_to_rollback = True
                    return
                self.failure(resp)

        method = "DELETE"
        del_failure = ""
        if self.diff_delete and self.wait_for_del_ready():
            resp = ""
            for net, state in self.diff_delete.items():
                if state.upper() == "OUT-OF-SYNC" or state == "TIMEOUT":
                    del_failure += net + ","
                    if state == "TIMEOUT":
                        resp = "Timeout waiting for network to be in delete ready state.\n"
                    if state == "OUT-OF-SYNC":
                        resp += "Network is out of sync.\n"
                    continue
                # Use bulk-delete API for multicluster_parent, regular delete for others
                if self.fabric_type == "multicluster_parent":
                    delete_path = path.replace("/networks","") + "/bulk-delete/networks?network-names=" + net
                    delete_payload = None
                else:
                    delete_path = path + "/" + net
                    delete_payload = {net: "NA"}
                
                if delete_payload:
                    resp = dcnm_send(self.module, method, delete_path, json.dumps(delete_payload))
                else:
                    resp = dcnm_send(self.module, method, delete_path)
                self.result["response"].append(resp)
                fail, self.result["changed"] = self.handle_response(resp, "delete")
                if fail:
                    if is_rollback:
                        self.failed_to_rollback = True
                        return
                    self.failure(resp)

        if del_failure:
            fail_msg = "Deletion of Networks {0} has failed: {1}".format(del_failure[:-1], resp)
            self.result["response"].append(resp)
            if is_rollback:
                self.failed_to_rollback = True
                return
            self.failure(fail_msg)

        if self.diff_create:
            # Get skipped attributes for parent fabrics
            skipped_attributes = self.get_skipped_attributes()
            template_mapping = self.get_template_config_mapping()

            # Convert skipped spec attributes to template config keys
            skipped_template_keys = set()
            for attr in skipped_attributes:
                if attr in template_mapping:
                    skipped_template_keys.add(template_mapping[attr])
            for net in self.diff_create:
                json_to_dict = json.loads(net["networkTemplateConfig"])
                vlanId = json_to_dict.get("vlanId", "")

                if not vlanId:
                    vlan_path = self.paths["GET_VLAN"].format(self.fabric)
                    vlan_data = dcnm_send(self.module, "GET", vlan_path)

                    if vlan_data["RETURN_CODE"] != 200:
                        self.module.fail_json(msg="Failure getting autogenerated vlan_id {0}".format(vlan_data))
                    vlanId = vlan_data["DATA"]

                t_conf = {
                    "vlanId": vlanId,
                    "gatewayIpAddress": json_to_dict.get("gatewayIpAddress", ""),
                    "isLayer2Only": json_to_dict.get("isLayer2Only", False),
                    "tag": json_to_dict.get("tag", ""),
                    "vlanName": json_to_dict.get("vlanName", ""),
                    "intfDescription": json_to_dict.get("intfDescription", ""),
                    "mtu": json_to_dict.get("mtu", ""),
                    "suppressArp": json_to_dict.get("suppressArp", False),
                    "dhcpServerAddr1": json_to_dict.get("dhcpServerAddr1", ""),
                    "dhcpServerAddr2": json_to_dict.get("dhcpServerAddr2", ""),
                    "dhcpServerAddr3": json_to_dict.get("dhcpServerAddr3", ""),
                    "vrfDhcp": json_to_dict.get("vrfDhcp", ""),
                    "vrfDhcp2": json_to_dict.get("vrfDhcp2", ""),
                    "vrfDhcp3": json_to_dict.get("vrfDhcp3", ""),
                    "loopbackId": json_to_dict.get("loopbackId", ""),
                    "mcastGroup": json_to_dict.get("mcastGroup", ""),
                    "gatewayIpV6Address": json_to_dict.get("gatewayIpV6Address", ""),
                    "secondaryGW1": json_to_dict.get("secondaryGW1", ""),
                    "secondaryGW2": json_to_dict.get("secondaryGW2", ""),
                    "secondaryGW3": json_to_dict.get("secondaryGW3", ""),
                    "secondaryGW4": json_to_dict.get("secondaryGW4", ""),
                    "trmEnabled": json_to_dict.get("trmEnabled", False),
                    "rtBothAuto": json_to_dict.get("rtBothAuto", False),
                    "enableL3OnBorder": json_to_dict.get("enableL3OnBorder", False),
                }

                if self.dcnm_version > 11:
                    t_conf.update(ENABLE_NETFLOW=json_to_dict.get("ENABLE_NETFLOW", False))
                    t_conf.update(SVI_NETFLOW_MONITOR=json_to_dict.get("SVI_NETFLOW_MONITOR", ""))
                    t_conf.update(VLAN_NETFLOW_MONITOR=json_to_dict.get("VLAN_NETFLOW_MONITOR", ""))

                # Remove skipped attributes from template config for parent fabrics
                for key in list(t_conf.keys()):
                    if key in skipped_template_keys:
                        del t_conf[key]

                net.update({"networkTemplateConfig": json.dumps(t_conf)})

                method = "POST"
                resp = dcnm_send(self.module, method, path, json.dumps(net))
                self.result["response"].append(resp)
                fail, self.result["changed"] = self.handle_response(resp, "create")
                if fail:
                    if is_rollback:
                        self.failed_to_rollback = True
                        return
                    self.failure(resp)

        method = "POST"
        if self.diff_attach:
            attach_path = path + "/attachments"

            # Update the fabric name to specific fabric which the switches are part of.
            self.update_ms_fabric(self.diff_attach)

            for d_a in self.diff_attach:
                for v_a in d_a["lanAttachList"]:
                    if v_a.get("is_deploy"):
                        del v_a["is_deploy"]
                    # Clean up tor_ports/torports keys if they exist and are empty
                    if v_a.get("tor_ports") is not None:
                        if not v_a["tor_ports"]:
                            del v_a["tor_ports"]
                    if v_a.get("torports") is not None:
                        if not v_a["torports"]:
                            del v_a["torports"]

            for attempt in range(0, 50):
                resp = dcnm_send(self.module, method, attach_path, json.dumps(self.diff_attach))
                
                update_in_progress = False
                for key in resp["DATA"].keys():
                    if re.search(r"Failed.*Please try after some time", str(resp["DATA"][key])):
                        update_in_progress = True
                if update_in_progress:
                    time.sleep(1)
                    continue

                break
            self.result["response"].append(resp)
            fail, self.result["changed"] = self.handle_response(resp, "attach")
            # If we get here and an update_in_progress is True then
            # not all of the attachments were successful which represents a
            # failure condition.
            if fail or update_in_progress:
                if is_rollback:
                    self.failed_to_rollback = True
                    return
                self.failure(resp)

        method = "POST"
        if self.diff_deploy:
            # For multicluster_parent, use special endpoint and payload format
            # For all others (including multicluster_child), use standard /deployments path
            if self.fabric_type == "multicluster_parent":
                deploy_path = self.paths["GET_NET_SWITCH_DEPLOY"].format(self.fabric)
                deploy_payload = self.transform_deploy_payload_for_multicluster(self.diff_deploy)
            else:
                # Standard path for standalone, multisite, and multicluster_child
                path = self.paths["GET_NET"].format(self.fabric)
                deploy_path = path + "/deployments"
                deploy_payload = self.diff_deploy
            resp = dcnm_send(self.module, method, deploy_path, json.dumps(deploy_payload))
            self.result["response"].append(resp)
            fail, self.result["changed"] = self.handle_response(resp, "deploy")
            if fail:
                if is_rollback:
                    self.failed_to_rollback = True
                    return
                self.failure(resp)

    def get_fabric_multicast_group_address(self) -> str:
        """
        # Summary

        -   If fabric REPLICATION_MODE is "Ingress", default multicast group
            address should be set to ""
        -   If fabric REPLICATION_MODE is "Multicast", default multicast group
            address is set to 239.1.1.0 for ND version 11, and 239.1.1.1 for
            NDFC version 12

        ## Raises

        Call fail_json for any unhandled combinations of REPLICATION_MODE and
        version.
        """
        controller_version: int = 12
        if self.dcnm_version is not None:
            controller_version = self.dcnm_version

        fabric_multicast_group_address: str = ""
        replication_mode: str = self.fabric_det.get("nvPairs", {}).get("REPLICATION_MODE", "Ingress")
        if replication_mode.lower() == "ingress":
            fabric_multicast_group_address = ""
        elif replication_mode.lower() == "multicast" and controller_version == 11:
            fabric_multicast_group_address = "239.1.1.0"
        elif replication_mode.lower() == "multicast" and controller_version > 11:
            fabric_multicast_group_address = "239.1.1.1"
        else:
            msg = "Unhandled REPLICATION_MODE or controller version. "
            msg += f"REPLICATION_MODE {replication_mode}, "
            msg += f"controller version {self.dcnm_version}."
            self.module.fail_json(msg=msg)
        return fabric_multicast_group_address

    def get_skipped_attributes(self):
        """
        Get list of attributes that should be skipped for parent fabrics.

        For parent fabrics, returns all child spec attributes except net_name and deploy.
        For child and standalone fabrics, returns empty list.

        Returns:
            list: List of attribute names to skip
        """
        if "_parent" != self.fabric_type:
            return []

        # Get child spec dynamically using parameter
        child_net_spec = self.get_network_spec(fabric_type="multisite_child")

        # Extract all attribute names except net_name and deploy
        skipped_attrs = [attr for attr in child_net_spec.keys()
                         if attr not in ["net_name", "deploy", "vlan_id", "vrf_name", "is_l2only"]]

        return skipped_attrs

    def get_template_config_mapping(self):
        """
        Get mapping from network spec attributes to template config keys.

        Returns:
            dict: Mapping from spec attribute to template config key
        """
        mapping = {
            "vlan_id": "vlanId",
            "gw_ip_subnet": "gatewayIpAddress",
            "is_l2only": "isLayer2Only",
            "routing_tag": "tag",
            "vlan_name": "vlanName",
            "int_desc": "intfDescription",
            "mtu_l3intf": "mtu",
            "arp_suppress": "suppressArp",
            "dhcp_srvr1_ip": "dhcpServerAddr1",
            "dhcp_srvr2_ip": "dhcpServerAddr2",
            "dhcp_srvr3_ip": "dhcpServerAddr3",
            "dhcp_srvr1_vrf": "vrfDhcp",
            "dhcp_srvr2_vrf": "vrfDhcp2",
            "dhcp_srvr3_vrf": "vrfDhcp3",
            "dhcp_servers": "dhcpServers",
            "dhcp_loopback_id": "loopbackId",
            "multicast_group_address": "mcastGroup",
            "gw_ipv6_subnet": "gatewayIpV6Address",
            "secondary_ip_gw1": "secondaryGW1",
            "secondary_ip_gw2": "secondaryGW2",
            "secondary_ip_gw3": "secondaryGW3",
            "secondary_ip_gw4": "secondaryGW4",
            "trm_enable": "trmEnabled",
            "route_target_both": "rtBothAuto",
            "l3gw_on_border": "enableL3OnBorder",
            "netflow_enable": "ENABLE_NETFLOW",
            "intfvlan_nf_monitor": "SVI_NETFLOW_MONITOR",
            "vlan_nf_monitor": "VLAN_NETFLOW_MONITOR"
        }
        return mapping

    def get_network_spec(self, fabric_type=None):
        """
        Get network specification based on fabric type and state.

        Args:
            fabric_type (str, optional): Override fabric type. If None, uses self.fabric_type.

        Returns:
            dict: Network specification dictionary
        """
        mcast_group_addr = self.get_fabric_multicast_group_address()
        is_query_state = self.params["state"] == "query"

        # Use parameter if provided, otherwise use instance fabric_type
        net_fabric_type = fabric_type if fabric_type is not None else self.fabric_type

        # Define the restricted spec for MSD child configurations
        if "_child" in net_fabric_type:
            net_spec = dict(
                net_name=dict(required=True, type="str", length_max=64),
                vrf_name=dict(type="str", length_max=32),
                dhcp_loopback_id=dict(type="int", range_min=0, range_max=1023),
                netflow_enable=dict(type="bool", default=False),
                vlan_nf_monitor=dict(type="str"),
                trm_enable=dict(type="bool", default=False),
                multicast_group_address=dict(type="ipv4", default=mcast_group_addr),
                l3gw_on_border=dict(type="bool", default=False),
                dhcp_srvr1_ip=dict(type="ipv4", default=""),
                dhcp_srvr2_ip=dict(type="ipv4", default=""),
                dhcp_srvr3_ip=dict(type="ipv4", default=""),
                dhcp_srvr1_vrf=dict(type="str", length_max=32),
                dhcp_srvr2_vrf=dict(type="str", length_max=32),
                dhcp_srvr3_vrf=dict(type="str", length_max=32),
                dhcp_servers=dict(type="list", elements="dict", default=[]),
                deploy=dict(type="bool", default=True if not is_query_state else None),
                is_l2only=dict(type="bool", default=False),
            )
        elif "_parent" in net_fabric_type:
            # Parent-specific attributes: attributes present in full spec but not in child spec
            net_spec = dict(
                net_name=dict(required=True, type="str", length_max=64),
                net_id=dict(type="int", range_max=16777214),
                vrf_name=dict(type="str", length_max=32),
                attach=dict(type="list"),
                deploy=dict(type="bool", default=True if not is_query_state else None),
                gw_ip_subnet=dict(type="ipv4_subnet", default=""),
                vlan_id=dict(type="int", range_max=4094),
                routing_tag=dict(type="int", default=12345, range_max=4294967295),
                net_template=dict(type="str", default="Default_Network_Universal"),
                net_extension_template=dict(type="str", default="Default_Network_Extension_Universal"),
                is_l2only=dict(type="bool", default=False),
                vlan_name=dict(type="str", length_max=128),
                int_desc=dict(type="str", length_max=258),
                mtu_l3intf=dict(type="int", range_min=68, range_max=9216),
                arp_suppress=dict(type="bool", default=False),
                gw_ipv6_subnet=dict(type="ipv6_subnet", default=""),
                secondary_ip_gw1=dict(type="ipv4", default=""),
                secondary_ip_gw2=dict(type="ipv4", default=""),
                secondary_ip_gw3=dict(type="ipv4", default=""),
                secondary_ip_gw4=dict(type="ipv4", default=""),
                route_target_both=dict(type="bool", default=False),
                intfvlan_nf_monitor=dict(type="str"),
            )

            # Adjust deploy field for query state
            if is_query_state:
                net_spec["deploy"] = dict(type="bool")
        else:
            # Full specification for non-child, non-parent fabrics
            net_spec = dict(
                net_name=dict(required=True, type="str", length_max=64),
                net_id=dict(type="int", range_max=16777214),
                vrf_name=dict(type="str", length_max=32),
                attach=dict(type="list"),
                deploy=dict(type="bool", default=True if not is_query_state else None),
                gw_ip_subnet=dict(type="ipv4_subnet", default=""),
                vlan_id=dict(type="int", range_max=4094),
                routing_tag=dict(type="int", default=12345, range_max=4294967295),
                net_template=dict(type="str", default="Default_Network_Universal"),
                net_extension_template=dict(type="str", default="Default_Network_Extension_Universal"),
                is_l2only=dict(type="bool", default=False),
                vlan_name=dict(type="str", length_max=128),
                int_desc=dict(type="str", length_max=258),
                mtu_l3intf=dict(type="int", range_min=68, range_max=9216),
                arp_suppress=dict(type="bool", default=False),
                dhcp_srvr1_ip=dict(type="ipv4", default=""),
                dhcp_srvr2_ip=dict(type="ipv4", default=""),
                dhcp_srvr3_ip=dict(type="ipv4", default=""),
                dhcp_srvr1_vrf=dict(type="str", length_max=32),
                dhcp_srvr2_vrf=dict(type="str", length_max=32),
                dhcp_srvr3_vrf=dict(type="str", length_max=32),
                dhcp_servers=dict(type="list", elements="dict", default=[]),
                dhcp_loopback_id=dict(type="int", range_min=0, range_max=1023),
                multicast_group_address=dict(type="ipv4", default=mcast_group_addr),
                gw_ipv6_subnet=dict(type="ipv6_subnet", default=""),
                secondary_ip_gw1=dict(type="ipv4", default=""),
                secondary_ip_gw2=dict(type="ipv4", default=""),
                secondary_ip_gw3=dict(type="ipv4", default=""),
                secondary_ip_gw4=dict(type="ipv4", default=""),
                trm_enable=dict(type="bool", default=False),
                route_target_both=dict(type="bool", default=False),
                l3gw_on_border=dict(type="bool", default=False),
                netflow_enable=dict(type="bool", default=False),
                intfvlan_nf_monitor=dict(type="str"),
                vlan_nf_monitor=dict(type="str"),
            )

            # Adjust deploy field for query state
            if is_query_state:
                net_spec["deploy"] = dict(type="bool")

        return net_spec

    def validate_input(self):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        """Parse the playbook values, validate to param specs."""

        # Make sure mutually exclusive dhcp properties are not set
        if self.config:
            for net in self.config:
                if net.get("dhcp_servers"):
                    conflicting_keys = []
                    dhcp_individual_keys = [
                        "dhcp_srvr1_ip", "dhcp_srvr1_vrf",
                        "dhcp_srvr2_ip", "dhcp_srvr2_vrf",
                        "dhcp_srvr3_ip", "dhcp_srvr3_vrf"
                    ]

                    for key in dhcp_individual_keys:
                        if net.get(key) is not None:
                            conflicting_keys.append(key)

                    if conflicting_keys:
                        msg = "Network '{0}': dhcp_servers cannot be used together with individual DHCP server properties: {1}".format(
                            net.get("net_name", "unknown"), ", ".join(conflicting_keys)
                        )
                        self.module.fail_json(msg=msg)

        state = self.params["state"]

        if state == "query":

            mcast_group_addr = self.get_fabric_multicast_group_address()
        state = self.params["state"]

        # Check for invalid state combinations with MSD child
        if self.fabric_type in ["multisite_child", "multicluster_child"]:
            if state in ["overridden", "deleted"]:
                self.module.fail_json(
                    msg=f"State '{state}' is not allowed for MSD child networks. Networks cannot be "
                    "deleted or overridden in MSD child fabrics."
                )

        if state == "query":

            net_spec = self.get_network_spec()
            att_spec = dict(
                ip_address=dict(required=True, type="str"),
                ports=dict(type="list", default=[]),
                deploy=dict(type="bool", default=True),
            )

            if self.config:
                msg = None
                # Validate net params
                valid_net, invalid_params = validate_list_of_dicts(self.config, net_spec, check_extra_params=self.check_extra_params)
                for net in valid_net:
                    # Check for attachment attributes in MSD child fabrics
                    if self.fabric_type in ["multisite_child", "multicluster_child"] and net.get("attach"):
                        self.module.fail_json(
                            msg=f"Network '{net.get('net_name', 'unknown')}': Attachment attributes are "
                            "not allowed for MSD child networks. MSD child fabrics do not support "
                            "network attachments."
                        )

                    if net.get("attach"):
                        valid_att, invalid_att = validate_list_of_dicts(net["attach"], att_spec, check_extra_params=self.check_extra_params)
                        net["attach"] = valid_att
                        invalid_params.extend(invalid_att)

                    if net.get("is_l2only", False) is True:
                        if net.get("vrf_name", "") is None or net.get("vrf_name", "") == "":
                            net["vrf_name"] = "NA"

                    self.validated.append(net)

                if invalid_params:
                    msg = "Invalid parameters in playbook: {0}".format("\n".join(invalid_params))
                    self.module.fail_json(msg=msg)

        else:

            net_spec = self.get_network_spec()
            att_spec = dict(
                ip_address=dict(required=True, type="str"),
                ports=dict(type="list", default=[]),
                deploy=dict(type="bool", default=True),
                tor_ports=dict(required=False, type="list", elements="dict"),
            )
            tor_att_spec = dict(
                ip_address=dict(required=True, type="str"),
                ports=dict(required=False, type="list", default=[]),
            )

            if self.config:
                msg = None
                # Validate net params
                valid_net, invalid_params = validate_list_of_dicts(self.config, net_spec, check_extra_params=self.check_extra_params)
                for net in valid_net:
                    # Check for attachment attributes in MSD child fabrics
                    if self.fabric_type in ["multisite_child", "multicluster_child"] and net.get("attach"):
                        self.module.fail_json(
                            msg=f"Network '{net.get('net_name', 'unknown')}': Attachment attributes are "
                            "not allowed for MSD child networks. MSD child fabrics do not support "
                            "network attachments."
                        )

                    if net.get("attach"):
                        valid_att, invalid_att = validate_list_of_dicts(net["attach"], att_spec, check_extra_params=self.check_extra_params)
                        net["attach"] = valid_att
                        for attach in net["attach"]:
                            attach["deploy"] = net["deploy"]
                            if attach.get("ports"):
                                attach["ports"] = [port.capitalize() for port in attach["ports"]]
                            if attach.get("tor_ports"):
                                if self.dcnm_version == 11:
                                    msg = "Invalid parameters in playbook: tor_ports configurations are supported only on NDFC"
                                    self.module.fail_json(msg=msg)

                                valid_tor_att, invalid_tor_att = validate_list_of_dicts(attach["tor_ports"], tor_att_spec,
                                                                                        check_extra_params=self.check_extra_params)
                                attach["tor_ports"] = valid_tor_att
                                for tor in attach["tor_ports"]:
                                    if tor.get("ports"):
                                        tor["ports"] = [port.capitalize() for port in tor["ports"]]
                                invalid_params.extend(invalid_tor_att)
                        invalid_params.extend(invalid_att)

                    if state != "deleted":
                        if net.get("is_l2only", False) is True:
                            if net.get("vrf_name", "") is not None and net.get("vrf_name", "") != "":
                                invalid_params.append("vrf_name should not be specified for L2 Networks")
                            else:
                                net["vrf_name"] = "NA"
                        else:
                            if net.get("vrf_name", "") is None:
                                invalid_params.append("vrf_name is required for L3 Networks")

                        if any(has_partial_dhcp_config(srvr) for srvr in [
                            dict(srvr_ip=net.get("dhcp_srvr1_ip"), srvr_vrf=net.get("dhcp_srvr1_vrf")),
                            dict(srvr_ip=net.get("dhcp_srvr2_ip"), srvr_vrf=net.get("dhcp_srvr2_vrf")),
                            dict(srvr_ip=net.get("dhcp_srvr3_ip"), srvr_vrf=net.get("dhcp_srvr3_vrf")),
                        ]):
                            invalid_params.append("DHCP server IP should be specified along with DHCP server VRF")

                        if net.get("dhcp_servers"):
                            dhcp_servers = net.get("dhcp_servers")
                            if len(dhcp_servers) > 16:
                                invalid_params.append("A maximum of 16 DHCP servers can be specified")
                            if any(has_partial_dhcp_config(srvr) for srvr in dhcp_servers):
                                invalid_params.append("DHCP server IP should be specified along with DHCP server VRF")

                        if self.dcnm_version == 11:
                            if net.get("netflow_enable") or net.get("intfvlan_nf_monitor") or net.get("vlan_nf_monitor"):
                                invalid_params.append("Netflow configurations are supported only on NDFC")

                        # Check if netflow monitors are specified without enabling netflow
                        netflow_enable = net.get("netflow_enable", False)
                        intfvlan_nf_monitor = net.get("intfvlan_nf_monitor")
                        vlan_nf_monitor = net.get("vlan_nf_monitor")

                        if not netflow_enable:
                            if intfvlan_nf_monitor:
                                invalid_params.append(
                                    f"Network '{net.get('net_name', 'unknown')}': intfvlan_nf_monitor "
                                    "(Interface VLAN Netflow Monitor) cannot be specified when netflow_enable is False or not set"
                                )
                            if vlan_nf_monitor:
                                invalid_params.append(
                                    f"Network '{net.get('net_name', 'unknown')}': vlan_nf_monitor "
                                    "(VLAN Netflow Monitor) cannot be specified when netflow_enable is False or not set"
                                )

                    self.validated.append(net)

                if invalid_params:
                    msg = "Invalid parameters in playbook: {0}".format("\n".join(invalid_params))
                    self.module.fail_json(msg=msg)

            else:
                state = self.params["state"]
                msg = None

                if state == "merged" or state == "replaced" or state == "query":
                    msg = "config: element is mandatory for this state {0}".format(state)

            if msg:
                self.module.fail_json(msg=msg)

    def handle_response(self, resp, op):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        msg += f"op: {op}"
        self.log.debug(msg)

        fail = False
        changed = True

        res = resp.copy()

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
        if op == "attach" and "Invalid interfaces" in str(res.values()):
            fail = True
            changed = True
        if op == "deploy" and "No switches PENDING for deployment" in str(res.values()) and "multisite_" not in self.fabric_type:
            # For parent fabrics, don't set changed=False as they will never have switches
            changed = False

        # Check for VLAN ID already in use errors in DATA section
        # This handles cases where RETURN_CODE is 200 but DATA contains error messages
        if op == "attach" and res.get("DATA") and isinstance(res["DATA"], dict):
            for key, value in res["DATA"].items():
                if isinstance(value, str) and "is already in use" in value.lower():
                    fail = True
                    changed = False
                    break
                # Check for multisite overlay link error
                if isinstance(value, str) and "multisite overlay link should be available to extend multisite" in value.lower():
                    fail = True
                    changed = False
                    break

        return fail, changed

    def failure(self, resp):
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        # Donot Rollback for Multi-site fabrics
        if self.is_ms_fabric or self.fabric_type != "standalone":
            self.failed_to_rollback = True
            self.module.fail_json(msg=resp)
            return

        # Implementing a per task rollback logic here so that we rollback ND to the have state
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
        if isinstance(res, str):
            self.module.fail_json(msg=res)

        res.update({"ROLLBACK_RESULT": msg1})

        if not resp.get("DATA"):
            data = copy.deepcopy(resp.get("DATA"))
            if data.get("stackTrace"):
                data.update({"stackTrace": "Stack trace is hidden, use '-vvvvv' to print it"})
                res.update({"DATA": data})

        if self.module._verbosity >= 5:
            self.module.fail_json(msg=res)

        self.module.fail_json(msg=res)

    def dcnm_update_network_information(self, want, have, cfg):
        # Check if this is a replaced state with MSD child fabric
        is_replaced_multisite_child = (
            self.module.params["state"] == "replaced"
            and self.fabric_type in ["multisite_child", "multicluster_child"]
        )

        # MSD child configurable attributes (can be updated in replaced state):
        # dhcp_loopback_id, netflow_enable, vlan_nf_monitor, trm_enable,
        # multicast_group_address, l3gw_on_border

        # Update basic network information
        if cfg.get("vrf_name", None) is None:
            want["vrf"] = have["vrf"]

        if cfg.get("net_id", None) is None:
            want["networkId"] = have["networkId"]

        if cfg.get("net_template", None) is None:
            want["networkTemplate"] = have["networkTemplate"]

        if cfg.get("net_extension_template", None) is None:
            want["networkExtensionTemplate"] = have["networkExtensionTemplate"]

        json_to_dict_want = json.loads(want["networkTemplateConfig"])
        json_to_dict_have = json.loads(have["networkTemplateConfig"])

        # Update template configuration - common attributes
        if cfg.get("vlan_id", None) is None:
            json_to_dict_want["vlanId"] = json_to_dict_have["vlanId"]
            if json_to_dict_want["vlanId"] != "":
                json_to_dict_want["vlanId"] = int(json_to_dict_want["vlanId"])

        if cfg.get("routing_tag", None) is None:
            json_to_dict_want["tag"] = json_to_dict_have["tag"]
            if json_to_dict_want["tag"] != "":
                json_to_dict_want["tag"] = int(json_to_dict_want["tag"])

        if cfg.get("gw_ip_subnet", None) is None:
            json_to_dict_want["gatewayIpAddress"] = json_to_dict_have["gatewayIpAddress"]

        if cfg.get("is_l2only", None) is None:
            json_to_dict_want["isLayer2Only"] = json_to_dict_have["isLayer2Only"]
            if str(json_to_dict_want["isLayer2Only"]).lower() == "true":
                json_to_dict_want["isLayer2Only"] = True
            elif str(json_to_dict_want["isLayer2Only"]).lower() == "false":
                json_to_dict_want["isLayer2Only"] = False

        if cfg.get("vlan_name", None) is None:
            json_to_dict_want["vlanName"] = json_to_dict_have["vlanName"]

        if cfg.get("int_desc", None) is None:
            json_to_dict_want["intfDescription"] = json_to_dict_have["intfDescription"]

        if cfg.get("mtu_l3intf", None) is None:
            json_to_dict_want["mtu"] = json_to_dict_have["mtu"]
            if json_to_dict_want["mtu"] != "":
                json_to_dict_want["mtu"] = int(json_to_dict_want["mtu"])

        if cfg.get("arp_suppress", None) is None:
            json_to_dict_want["suppressArp"] = json_to_dict_have["suppressArp"]
            if str(json_to_dict_want["suppressArp"]).lower() == "true":
                json_to_dict_want["suppressArp"] = True
            elif str(json_to_dict_want["suppressArp"]).lower() == "false":
                json_to_dict_want["suppressArp"] = False

        # IPv6 and secondary gateway configuration
        if cfg.get("gw_ipv6_subnet", None) is None:
            json_to_dict_want["gatewayIpV6Address"] = json_to_dict_have["gatewayIpV6Address"]

        if cfg.get("secondary_ip_gw1", None) is None:
            json_to_dict_want["secondaryGW1"] = json_to_dict_have["secondaryGW1"]

        if cfg.get("secondary_ip_gw2", None) is None:
            json_to_dict_want["secondaryGW2"] = json_to_dict_have["secondaryGW2"]

        if cfg.get("secondary_ip_gw3", None) is None:
            json_to_dict_want["secondaryGW3"] = json_to_dict_have["secondaryGW3"]

        if cfg.get("secondary_ip_gw4", None) is None:
            json_to_dict_want["secondaryGW4"] = json_to_dict_have["secondaryGW4"]

        # Route target configuration (common for all fabric types)
        if cfg.get("route_target_both", None) is None:
            json_to_dict_want["rtBothAuto"] = json_to_dict_have["rtBothAuto"]
            if str(json_to_dict_want["rtBothAuto"]).lower() == "true":
                json_to_dict_want["rtBothAuto"] = True
            else:
                json_to_dict_want["rtBothAuto"] = False

        # MSD child configurable attributes - grouped together
        # These can be modified in MSD child replaced state
        if not is_replaced_multisite_child:
            # DHCP server configuration
            if cfg.get("dhcp_srvr1_ip", None) is None:
                json_to_dict_want["dhcpServerAddr1"] = json_to_dict_have["dhcpServerAddr1"]

            if cfg.get("dhcp_srvr2_ip", None) is None:
                json_to_dict_want["dhcpServerAddr2"] = json_to_dict_have["dhcpServerAddr2"]

            if cfg.get("dhcp_srvr3_ip", None) is None:
                json_to_dict_want["dhcpServerAddr3"] = json_to_dict_have["dhcpServerAddr3"]

            if cfg.get("dhcp_srvr1_vrf", None) is None:
                json_to_dict_want["vrfDhcp"] = json_to_dict_have["vrfDhcp"]

            if cfg.get("dhcp_srvr2_vrf", None) is None:
                json_to_dict_want["vrfDhcp2"] = json_to_dict_have["vrfDhcp2"]

            if cfg.get("dhcp_srvr3_vrf", None) is None:
                json_to_dict_want["vrfDhcp3"] = json_to_dict_have["vrfDhcp3"]

            # DHCP servers list configuration
            if cfg.get("dhcp_servers", None) is None:
                json_to_dict_want["dhcpServers"] = json_to_dict_have.get("dhcpServers", "")

            # DHCP loopback configuration
            if cfg.get("dhcp_loopback_id", None) is None:
                json_to_dict_want["loopbackId"] = json_to_dict_have["loopbackId"]

            # TRM enable configuration
            if cfg.get("trm_enable", None) is None:
                json_to_dict_want["trmEnabled"] = json_to_dict_have["trmEnabled"]
                if str(json_to_dict_want["trmEnabled"]).lower() == "true":
                    json_to_dict_want["trmEnabled"] = True
                else:
                    json_to_dict_want["trmEnabled"] = False

            # L3 gateway on border configuration
            if cfg.get("l3gw_on_border", None) is None:
                json_to_dict_want["enableL3OnBorder"] = json_to_dict_have["enableL3OnBorder"]
                if str(json_to_dict_want["enableL3OnBorder"]).lower() == "true":
                    json_to_dict_want["enableL3OnBorder"] = True
                else:
                    json_to_dict_want["enableL3OnBorder"] = False

            # Multicast configuration (skip for MS fabric)
            if self.is_ms_fabric is False and cfg.get("multicast_group_address", None) is None:
                json_to_dict_want["mcastGroup"] = json_to_dict_have["mcastGroup"]

            # NetFlow configuration (version 12+ only)
            if self.dcnm_version > 11:
                if cfg.get("netflow_enable", None) is None:
                    json_to_dict_want["ENABLE_NETFLOW"] = json_to_dict_have["ENABLE_NETFLOW"]
                    if str(json_to_dict_want["ENABLE_NETFLOW"]).lower() == "true":
                        json_to_dict_want["ENABLE_NETFLOW"] = True
                    else:
                        json_to_dict_want["ENABLE_NETFLOW"] = False

                if cfg.get("vlan_nf_monitor", None) is None:
                    json_to_dict_want["VLAN_NETFLOW_MONITOR"] = json_to_dict_have["VLAN_NETFLOW_MONITOR"]

        # NetFlow SVI monitor configuration (common for all fabric types, version 12+ only)
        if self.dcnm_version > 11 and cfg.get("intfvlan_nf_monitor", None) is None:
            json_to_dict_want["SVI_NETFLOW_MONITOR"] = json_to_dict_have["SVI_NETFLOW_MONITOR"]

        want.update({"networkTemplateConfig": json.dumps(json_to_dict_want)})

    def update_want(self):
        """
        Routine to compare want and have and make approriate changes to want. This routine checks the existing
        information with the config from playbook and populates the payloads in self.want apropriately.
        This routine updates self.want with final paylload information after comparing self.want and self.have and
        the playbook information.

        Parameters:
            None

        Returns:
            None
        """

        # For child fabrics, copy have attachments to want attachments since child fabrics don't support attachments in config
        if self.fabric_type in ["multisite_child", "multicluster_child"]:
            # Copy have attachments to want attachments for child fabrics
            self.want_attach = copy.deepcopy(self.have_attach)

        # only for 'merged' state we need to update the objects that are not included in playbook with
        # values from self.have.
        # Also for 'replaced' state when MSD exists and is child, we need to ignore certain attributes

        state = self.module.params["state"]
        if state == "merged":
            # Normal merged state processing
            pass
        elif state == "replaced" and self.fabric_type in ["multisite_child", "multicluster_child"]:
            # For MSD child in replaced state, we need special handling
            pass
        else:
            return

        if self.want_create == []:
            return

        for net in self.want_create:

            # Get the matching have to copy values if required
            match_have = [have for have in self.have_create if ((net["networkName"] == have["networkName"]))]
            if match_have == []:
                continue

            # Get the network from self.config to check if a particular object is included or not
            match_cfg = [cfg for cfg in self.config if ((net["networkName"] == cfg["net_name"]))]
            if match_cfg == []:
                continue

            self.dcnm_update_network_information(net, match_have[0], match_cfg[0])


def main():
    """main entry point for module execution"""

    element_spec = dict(
        fabric=dict(required=True, type="str"),
        _fabric_details=dict(
            required=False,
            type="dict",
            options=dict(
                fabric_type=dict(
                    required=True,
                    type="str",
                    choices=["multicluster_parent", "multicluster_child", "multisite_parent", "multisite_child", "standalone"]
                ),
                cluster_name=dict(required=False, type="str", default=""),
                nd_version=dict(required=False, type="float")
            )
        ),
        config=dict(required=False, type="list", elements="dict"),
        state=dict(
            default="merged",
            choices=["merged", "replaced", "deleted", "overridden", "query"],
        ),
    )

    module = AnsibleModule(argument_spec=element_spec, supports_check_mode=True)

    dcnm_net = DcnmNetwork(module)

    if not dcnm_net.ip_sn:
        module.fail_json(msg="Fabric {0} missing on ND or does not have any switches".format(dcnm_net.fabric))

    dcnm_net.validate_input()

    dcnm_net.get_want()
    dcnm_net.get_have()
    if dcnm_net.fabric_type in ["multisite_child", "multicluster_child"]:
        dcnm_net.check_want_networks_deployment_state()

    warn_msg = None

    # self.want would have defaulted all optional objects not included in playbook. But the way
    # these objects are handled is different between 'merged' and 'replaced' states. For 'merged'
    # state, objects not included in the playbook must be left as they are and for state 'replaced'
    # they must be purged or defaulted.
    dcnm_net.update_want()

    if module.params["state"] == "merged":
        warn_msg = dcnm_net.get_diff_merge()

    if module.params["state"] == "replaced":
        warn_msg = dcnm_net.get_diff_replace()

    if module.params["state"] == "overridden":
        warn_msg = dcnm_net.get_diff_override()

    if module.params["state"] == "deleted":
        dcnm_net.get_diff_delete()

    if module.params["state"] == "query":
        dcnm_net.get_diff_query()
        dcnm_net.result["response"] = dcnm_net.query

    dcnm_net.result["warnings"].append(warn_msg) if warn_msg else []

    if (
        dcnm_net.diff_create
        or dcnm_net.diff_create_quick
        or dcnm_net.diff_attach
        or dcnm_net.diff_deploy
        or dcnm_net.diff_delete
        or dcnm_net.diff_create_update
        or dcnm_net.diff_detach
        or dcnm_net.diff_undeploy
    ):
        dcnm_net.result["changed"] = True
    else:
        module.exit_json(**dcnm_net.result)

    dcnm_net.format_diff()
    dcnm_net.result["diff"] = dcnm_net.diff_input_format

    if module.check_mode:
        dcnm_net.result["changed"] = False
        module.exit_json(**dcnm_net.result)

    dcnm_net.push_to_remote()

    module.exit_json(**dcnm_net.result)


if __name__ == "__main__":
    main()
