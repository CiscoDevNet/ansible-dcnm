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
module: dcnm_links
short_description: DCNM ansible module for managing Links.
version_added: "2.1.0"
description:
    - DCNM ansible module for creating, modifying, deleting and querying Links
author: Mallik Mudigonda (@mmudigon)
options:
  src_fabric:
    description:
      - Name of the source fabric for links operations.
    type: str
    required: true
  state:
    description:
      - The required state of the configuration after module completion.
    type: str
    required: false
    choices:
      - merged
      - replaced
      - deleted
      - query
    default: merged
  deploy:
    description:
      - Flag to control deployment of links. If set to 'true' then the links included will be deployed to
        specified switches. If set to 'false', the links will be created but not deployed.
      - Setting this flag to 'true' will result in all pending configurations on the source and destination
        devices to be deployed.
    type: bool
    required: false
    default: true
  config:
    description:
      - A list of dictionaries containing Links information.
    type: list
    elements: dict
    default: []
    suboptions:
      dst_fabric:
        description:
          - Name of the destination fabric. If this is same as 'src_fabric' then the link is considered
            intra-fabric link. If this parameter is different from 'src_fabric', then the link is considered
            inter-fabric link.
        type: str
        required: true
      src_device:
        description:
          - IP address or DNS name of the source switch which is part of the link being configured.
        type: str
        required: true
      dst_device:
        description:
          - IP address or DNS name of the destination switch which is part of the link being configured.
        type: str
        required: true
      src_interface:
        description:
          - Interface on the source device which is part of the link being configured.
        type: str
        required: true
      dst_interface:
        description:
          - Interface on the destination device which is part of the link being configured.
        type: str
        required: true
      template:
        description:
          - Name of the template that is applied on the link being configured.
          - The last 3 template choices are applicable for inter-fabric links and the others
            are applicable for intra-fabric links.
          - This parameter is required only for 'merged' and 'replaced' states. It is
          - optional for other states.
        type: str
        required: true
        choices:
          - int_intra_fabric_ipv6_link_local(intra-fabric)
          - int_intra_fabric_num_link (intra-fabric)
          - int_intra_fabric_unnum_link (intra-fabric)
          - int_intra_vpc_peer_keep_alive_link (intra-fabric)
          - int_pre_provision_intra_fabric_link (intra-fabric)
          - ios_xe_int_intra_fabric_num_link (intra-fabric)
          - ext_fabric_setup (inter-fabric)
          - ext_multisite_underlay_setup (inter-fabric)
          - ext_evpn_multisite_overlay_setup (inter-fabric)
      profile:
        description:
          - Additional link related parameters that must be included while creating links.
        suboptions:
          peer1_ipv4_address:
            description:
              - IPV4 address of the source interface.
              - This parameter is optional if the underlying fabric is ipv6 enabled.
              - This parameter is required only if template is 'int_intra_fabric_num_link' or
                'ios_xe_int_intra_fabric_num_link' or 'int_intra_vpc_peer_keep_alive_link'.
            type: str
            required: true
          peer2_ipv4_address:
            description:
              - IPV4 address of the destination interface.
              - This parameter is optional if the underlying fabric is ipv6 enabled.
              - This parameter is required only if template is 'int_intra_fabric_num_link' or
                'ios_xe_int_intra_fabric_num_link' or 'int_intra_vpc_peer_keep_alive_link'.
            type: str
            required: true
          peer1_ipv6_address:
            description:
              - IPV6 address of the source interface.
              - This parameter is required only if the underlying fabric is ipv6 enabled.
              - This parameter is required only if template is 'int_intra_fabric_num_link' or
                'ios_xe_int_intra_fabric_num_link' or 'int_intra_vpc_peer_keep_alive_link'.
            type: str
            required: false
            default: ""
          peer2_ipv6_address:
            description:
              - IPV6 address of the destination interface.
              - This parameter is required only if the underlying fabric is ipv6 enabled.
              - This parameter is required only if template is 'int_intra_fabric_num_link' or
                'ios_xe_int_intra_fabric_num_link' or 'int_intra_vpc_peer_keep_alive_link'.
            type: str
            required: false
            default: ""
          ipv4_subnet:
            description:
              - IPV4 address of the source interface with mask.
              - Required for below templates
              - ext_fabric_setup
              - ext_multisite_underlay_setup
            type: str
            required: true
          ipv4_address:
            description:
              - IPV4 address of the source interface without mask.
              - This parameter is required only if template is 'ext_evpn_multisite_overlay_setup'.
            type: str
            required: true
          neighbor_ip:
            description:
              - IPV4 address of the neighbor switch on the destination fabric.
              - Required for below templates
              - ext_fabric_setup
              - ext_multisite_underlay_setup
              - ext_evpn_multisite_overlay_setup
              - ext_vxlan_mpls_underlay_setup
              - ext_vxlan_mpls_overlay_setup
            type: str
            required: true
          src_asn:
            description:
              - BGP ASN number on the source fabric.
              - Required for below templates
              - ext_fabric_setup
              - ext_multisite_underlay_setup
              - ext_evpn_multisite_overlay_setup
              - ext_vxlan_mpls_overlay_setup
            type: str
            required: true
          dst_asn:
            description:
              - BGP ASN number on the destination fabric.
              - Required for below templates
              - ext_fabric_setup
              - ext_multisite_underlay_setup
              - ext_evpn_multisite_overlay_setup
              - ext_vxlan_mpls_overlay_setup
            type: str
            required: true
          auto_deploy:
            description:
              - Flag that controls auto generation of neighbor VRF Lite configuration for managed neighbor devices.
              - This parameter is required only if template is 'ext_fabric_setup'.
            type: str
            required: true
          max_paths:
            description:
              - Maximum number of iBGP/eBGP paths.
              - This parameter is required only if template is 'ext_multisite_underlay_setup'.
            type: int
            required: false
            default: 1
          ebgp_password_enable:
            description:
              - Flag to enable eBGP password.
              - This parameter is required only if template is 'ext_multisite_underlay_setup' or 'ext_evpn_multisite_overlay_setup'.
            type: bool
            required: false
            default: true
          inherit_from_msd:
            description:
              - Flag indicating whether to inherit BGP password from MSD information.
              - Applicable only when source and destination fabric are in the same MSD fabric.
              - This parameter is required only if template is 'ext_multisite_underlay_setup' or 'ext_evpn_multisite_overlay_setup'
            type: bool
            required: false
            default: true
          ebgp_password:
            description:
              - Encrypted eBGP Password Hex String.
              - This parameter is required only if template is 'ext_multisite_underlay_setup' or 'ext_evpn_multisite_overlay_setup'.
              - This parameter is required only if inherit_from_msd is false.
            type: str
            required: true
          ebgp_auth_key_type:
            description:
              - BGP Key Encryption Type.
              - This parameter is required only if template is 'ext_multisite_underlay_setup' or 'ext_evpn_multisite_overlay_setup'.
              - This parameter is required only if inherit_from_msd is false.
              - Choices are 3 (3DES) or 7 (Cisco)
            type: int
            required: true
            choices:
              - 3
              - 7
          route_tag:
            description:
              - Routing tag associated with interface IP.
              - This parameter is required only if template is 'ext_multisite_underlay_setup'
            type: str
            default: ''
          deploy_dci_tracking:
            description:
              - Flag to enable deploy DCI tracking.
              - This parameter is required only if template is 'ext_multisite_underlay_setup'.
              - This parameter MUST be included only if the fabrics are part of multisite.
            type: bool
            required: false
            default: false
          trm_enabled:
            description:
              - Flag to enable Tenant Routed Multicast.
              - This parameter is required only if template is 'ext_evpn_multisite_overlay_setup'.
            type: bool
            required: false
            default: false
          bgp_multihop:
            description:
              - eBGP Time-To-Live Value for Remote Peer.
              - This parameter is required only if template is 'ext_evpn_multisite_overlay_setup'.
            type: int
            required: false
            default: 5
          admin_state:
            description:
              - Admin state of the link.
              - This parameter is not required if template is 'ext_evpn_multisite_overlay_setup', 'ext_multisite_underlay_setup',
                and 'ext_fabric_setup'.
            type: bool
            required: true
          mtu:
            description:
              - MTU of the link.
              - This parameter is optional if template is 'ios_xe_int_intra_fabric_num_link'. The default value
                in this case will be 1500.
              - This parameter is not required if template is 'ext_evpn_multisite_overlay_setup'.
            type: int
            required: true
          peer1_description:
            description:
              - Description of the source interface.
              - This parameter is not required if template is 'ext_evpn_multisite_overlay_setup'.
            type: str
            required: false
            default: ""
          peer2_description:
            description:
              - Description of the destination interface.
              - This parameter is not required if template is 'ext_evpn_multisite_overlay_setup'.
            type: str
            required: false
            default: ""
          peer1_cmds:
            description:
              - Commands to be included in the configuration under the source interface.
              - This parameter is not required if template is  'ext_evpn_multisite_overlay_setup'.
            type: list
            elements: str
            required: false
            default: []
          peer2_cmds:
            description:
              - Commands to be included in the configuration under the destination interface.
              - This parameter is not required if template is 'ext_evpn_multisite_overlay_setup'.
            type: list
            elements: str
            required: false
            default: []
          enable_macsec:
            description:
              - Enable MACsec on the link.
              - This parameter is applicable only if MACsec feature is enabled on the fabric.
              - This parameter is applicable only if template is 'int_intra_fabric_ipv6_link_local' or
                'int_intra_fabric_num_link' or 'int_intra_fabric_unnum_link'.
            type: bool
            required: false
            default: false
          peer1_bfd_echo_disable:
            description:
              - Enable BFD echo on the source interface. Only applicable if BFD is enabled on the fabric.
              - This parameter is applicable only if template is 'int_intra_fabric_num_link'.
            type: bool
            required: false
            default: false
          peer2_bfd_echo_disable:
            description:
              - Enable BFD echo on the destination interface. Only applicable if BFD is enabled on the fabric.
              - This parameter is applicable only if template is 'int_intra_fabric_num_link'.
            type: bool
            required: false
            default: false
          intf_vrf:
            description:
              - Name of the non-default VRF for the link.
              - Make sure to configure the VRF before using it here.
              - This parameter is applicable only if template is 'int_intra_vpc_peer_keep_alive_link'.
            type: str
            required: false
            default: ""
          mpls_fabric:
            description:
              - MPLS LDP or Segment-Routing
              - This parameter is applicable only if template is `ext_vxlan_mpls_underlay_setup`.
            type: str
            default: "SR"
            choices:
              - SR
              - LDP
          peer1_sr_mpls_index:
            description:
              - Unique SR SID index for the source border
              - This parameter is applicable only if template is `ext_vxlan_mpls_underlay_setup` and `mpls_fabric` is `SR`
            type: int
            default: "0"
          peer2_sr_mpls_index:
            description:
              - Unique SR SID index for the destination border
              - This parameter is applicable only if template is `ext_vxlan_mpls_underlay_setup` and `mpls_fabric` is `SR`
            type: int
            default: "0"
          global_block_range:
            description:
              - For Segment Routing binding
              - This parameter is applicable only if template is `ext_vxlan_mpls_underlay_setup` and `mpls_fabric` is `SR`
            type: str
            default: "16000-23999"
          dci_routing_proto:
            description:
              - Routing protocol used on the DCI MPLS link
              - This parameter is applicable only if template is `ext_vxlan_mpls_underlay_setup` and `mpls_fabric` is `SR`
            type: str
            default: "is-is"
            choices:
              - is-is
              - ospf
          ospf_area_id:
            description:
              - OSPF Area ID in IP address format
              - This parameter is applicable only if template is `ext_vxlan_mpls_underlay_setup` and `dci_routing_proto` is `ospf`
            type: str
            default: "0.0.0.0"
          dci_routing_tag:
            description:
              - Routing Process Tag of DCI Underlay
              - This parameter is applicable only if template is `ext_vxlan_mpls_underlay_setup`
            type: str
            default: "MPLS_UNDERLAY"
"""

EXAMPLES = """

# States:
# This module supports the following states:
#
# Merged:
#   Links defined in the playbook will be merged into the target fabric.
#
#   The links listed in the playbook will be created if not already present on the DCNM
#   server. If the link is already present and the configuration information included
#   in the playbook is either different or not present in DCNM, then the corresponding
#   information is added to the link on DCNM. If a link mentioned in playbook
#   is already present on DCNM and there is no difference in configuration, no operation
#   will be performed for such link.
#
# Replaced:
#   Links defined in the playbook will be replaced in the target fabric.
#
#   The state of the links listed in the playbook will serve as source of truth for the
#   same links present on the DCNM under the fabric mentioned. Additions and updations
#   will be done to bring the DCNM links to the state listed in the playbook.
#   Note: Replace will only work on the links mentioned in the playbook.
#
# Deleted:
#   Links defined in the playbook will be deleted in the target fabric.
#
#   WARNING: Deleting a Link will deploy all pending configurations on the impacted switches
#
# Query:
#   Returns the current DCNM state for the links listed in the playbook. Information included
#    in the playbook will be used as filters to get the desired output.
#
# CREATE LINKS
#
# NUMBERED FABRIC
#
# INTRA-FABRIC

    - name: Create Links
      cisco.dcnm.dcnm_links:
        state: merged                                            # choose from [merged, replaced, deleted, query]
        src_fabric: "ansible_num_fabric"
        config:
          - dst_fabric: "ansible_num_fabric"                     # Destination fabric
            src_interface: "Ethernet1/1"                         # Interface on the Source fabric
            dst_interface: "Ethernet1/1"                         # Interface on the Destination fabric
            src_device: 193.168.1.1                              # Device on the Source fabric
            dst_device: 193.168.1.2                              # Device on the Destination fabric
            template: int_intra_fabric_num_link                  # template to be applied, choose from
                                                                 #   [ int_intra_fabric_ipv6_link_local, int_intra_fabric_num_link,
                                                                 #     int_intra_fabric_unnum_link, int_intra_vpc_peer_keep_alive_link,
                                                                 #     int_pre_provision_intra_fabric_link, ios_xe_int_intra_fabric_num_link ]

            profile:
              peer1_ipv4_addr: 192.168.1.1                       # IP address of the Source interface
              peer2_ipv4_addr: 192.168.1.2                       # IP address of the Destination interface
              admin_state: true                                  # choose from [true, false]
              mtu: 9216                                          #
              peer1_description: "Description of source"         # optional, default is ""
              peer2_description: "Description of dest"           # optional, default is ""
              peer1_bfd_echo_disable: false                      # optional, choose from [true, false]
              peer2_bfd_echo_disable: false                      # optional, choose from [true, false]
              enable_macsec: false                               # optional, choose from [true, false]
              peer1_cmds:                                        # Freeform config for source device
                - no shutdown                                    # optional, default is ""
              peer2_cmds:                                        # Freeform config for destination device
                - no shutdown                                    # optional, default is ""

          - dst_fabric: "ansible_num_fabric"                     # Destination fabric
            src_interface: "Ethernet1/2"                         # Interface on the Source fabric
            dst_interface: "Ethernet1/2"                         # Interface on the Destination fabric
            src_device: 193.168.1.1                              # Device on the Source fabric
            dst_device: 193.168.1.2                              # Device on the Destination fabric
            template: int_pre_provision_intra_fabric_link        # template to be applied, choose from
                                                                 #   [ int_intra_fabric_ipv6_link_local, int_intra_fabric_num_link,
                                                                 #     int_intra_fabric_unnum_link, int_intra_vpc_peer_keep_alive_link,
                                                                 #     int_pre_provision_intra_fabric_link, ios_xe_int_intra_fabric_num_link ]
          - dst_fabric: "ansible_num_fabric"                     # Destination fabric
            src_interface: "Ethernet1/3"                         # Interface on the Source fabric
            dst_interface: "Ethernet1/3"                         # Interface on the Destination fabric
            src_device: 193.168.1.1                              # Device on the Source fabric
            dst_device: 193.168.1.2                              # Device on the Destination fabric
            template: ios_xe_int_intra_fabric_num_link           # template to be applied, choose from
                                                                 #   [ int_intra_fabric_ipv6_link_local, int_intra_fabric_num_link,
                                                                 #     int_intra_fabric_unnum_link, int_intra_vpc_peer_keep_alive_link,
                                                                 #     int_pre_provision_intra_fabric_link, ios_xe_int_intra_fabric_num_link ]

            profile:
              peer1_ipv4_addr: 192.169.2.1                       # IPV4 address of the Source interface
              peer2_ipv4_addr: 192.169.2.2                       # IPV4 address of the Destination interface
              peer1_ipv6_addr: fe80:01::01                       # optional, default is ""
              peer2_ipv6_addr: fe80:01::02                       # optional, default is ""
              admin_state: true                                  # choose from [true, false]
              mtu: 1500                                          # optional, default is 1500
              peer1_description: "Description of source"         # optional, default is ""
              peer2_description: "Description of dest"           # optional, default is ""
              peer1_bfd_echo_disable: false                      # optional, choose from [true, false]
              peer2_bfd_echo_disable: false                      # optional, choose from [true, false]
              enable_macsec: false                               # optional, choose from [true, false]
              peer1_cmds:                                        # Freeform config for source device
                - no shutdown                                    # optional, default is ""
              peer2_cmds:                                        # Freeform config for destination device
                - no shutdown                                    # optional, default is ""
#
# INTER-FABRIC

    - name: Create Links including optional parameters
      cisco.dcnm.dcnm_links: &links_merge_with_opt
        state: merged                                            # choose from [merged, replaced, deleted, query]
        src_fabric: "{{ ansible_num_fabric }}"
        config:
          - dst_fabric: "{{ ansible_unnum_fabric }}"             # Destination fabric
            src_interface: "{{ intf_1_3 }}"                      # Interface on the Source fabric
            dst_interface: "{{ intf_1_3 }}"                      # Interface on the Destination fabric
            src_device: "{{ ansible_num_switch1 }}"              # Device on the Source fabric
            dst_device: "{{ ansible_unnum_switch1 }}"            # Device on the Destination fabric
            template: ext_fabric_setup                           # template to be applied, choose from
                                                                 #   [ ext_fabric_setup, ext_multisite_underlay_setup,
                                                                 #     ext_evpn_multisite_overlay_setup ]
            profile:
              ipv4_subnet: 193.168.1.1/24                        # IP address of interface in src fabric with mask
              neighbor_ip: 193.168.1.2                           # IP address of the interface in dst fabric
              src_asn: 1000                                      # BGP ASN in source fabric
              dst_asn: 1001                                      # BGP ASN in destination fabric
              mtu: 9216                                          #
              auto_deploy: false                                 # optional, default is false
                                                                 # Flag that controls auto generation of neighbor VRF Lite configuration
              peer1_description: "Description of source"         # optional, default is ""
              peer2_description: "Description of dest"           # optional, default is ""
              peer1_cmds:                                        # Freeform config for source interface
                - no shutdown                                    # optional, default is ""
              peer2_cmds:                                        # Freeform config for destination interface
                - no shutdown                                    # optional, default is ""

          - dst_fabric: "{{ ansible_unnum_fabric }}"             # Destination fabric
            src_interface: "{{ intf_1_4 }}"                      # Interface on the Source fabric
            dst_interface: "{{ intf_1_4 }}"                      # Interface on the Destination fabric
            src_device: "{{ ansible_num_switch1 }}"              # Device on the Source fabric
            dst_device: "{{ ansible_unnum_switch1 }}"            # Device on the Destination fabric
            template: ext_multisite_underlay_setup               # template to be applied, choose from
                                                                 #   [ ext_fabric_setup, ext_multisite_underlay_setup,
                                                                 #     ext_evpn_multisite_overlay_setup ]
            profile:
              ipv4_subnet: 193.168.2.1/24                        # IP address of interface in src fabric with mask
              neighbor_ip: 193.168.2.2                           # IP address of the interface in dst fabric
              src_asn: 1200                                      # BGP ASN in source fabric
              dst_asn: 1201                                      # BGP ASN in destination fabric
              mtu: 9216                                          #
              deploy_dci_tracking: false                         # optional, default is false
              max_paths: 1                                       # optional, default is 1
              route_tag: 12345                                   # optional, optional is ""
              ebgp_password_enable: true                         # optional, default is true
              ebgp_password: 0102030405                          # optional, required only if ebgp_password_enable flag is true, and inherit_from_msd
                                                                 # is false.
              inherit_from_msd: True                             # optional, required only if ebgp_password_enable flag is true, default is false
              ebgp_auth_key_type: 3                              # optional, required only if ebpg_password_enable is true, and inherit_from_msd
                                                                 # is false. Default is 3
                                                                 # choose from [3 - 3DES, 7 - Cisco ]
              peer1_description: "Description of source"         # optional, default is ""
              peer2_description: "Description of dest"           # optional, default is ""
              peer1_cmds:                                        # Freeform config for source interface
                - no shutdown                                    # optional, default is ""
              peer2_cmds:                                        # Freeform config for destination interface
                - no shutdown                                    # optional, default is ""

          - dst_fabric: "{{ ansible_unnum_fabric }}"             # Destination fabric
            src_interface: "{{ intf_1_5 }}"                      # Interface on the Source fabric
            dst_interface: "{{ intf_1_5 }}"                      # Interface on the Destination fabric
            src_device: "{{ ansible_num_switch1 }}"              # Device on the Source fabric
            dst_device: "{{ ansible_unnum_switch1 }}"            # Device on the Destination fabric
            template: ext_evpn_multisite_overlay_setup           # template to be applied, choose from
                                                                 #   [ ext_fabric_setup, ext_multisite_underlay_setup,
                                                                 #     ext_evpn_multisite_overlay_setup ]
            profile:
              ipv4_addr: 193.168.3.1                             # IP address of interface in src fabric
              neighbor_ip: 193.168.3.2                           # IP address of the interface in dst fabric
              src_asn: 1300                                      # BGP ASN in source fabric
              dst_asn: 1301                                      # BGP ASN in destination fabric
              trm_enabled: false                                 # optional, default is false
              bgp_multihop: 5                                    # optional, default is 5
              ebgp_password_enable: true                         # optional, default is true
              ebgp_password: 0102030405                          # optional, required only if ebgp_password_enable flag is true, and inherit_from_msd
                                                                 # is false. Default is 3
              inherit_from_msd: false                            # optional, required only if ebgp_password_enable flag is true, default is false
              ebpg_auth_key_type: 3                              # optional, required only if ebpg_password_enable is true, and inherit_from_msd
                                                                 # is false. Default is 3
                                                                 # choose from [3 - 3DES, 7 - Cisco ]
          - dst_fabric: "{{ ansible_unnum_fabric }}"             # Destination fabric
            src_interface: "{{ intf_1_5 }}"                      # Interface on the Source fabric
            dst_interface: "{{ intf_1_5 }}"                      # Interface on the Destination fabric
            src_device: "{{ ansible_num_switch1 }}"              # Device on the Source fabric
            dst_device: "{{ ansible_unnum_switch1 }}"            # Device on the Destination fabric
            template: ext_vxlan_mpls_underlay_setup              # Template of MPLS handoff underlay link
            profile:
              ipv4_subnet: 193.168.3.1/30                        # IP address of interface in src fabric with the mask
              neighbor_ip: 193.168.3.2                           # IP address of the interface in dst fabric
              mpls_fabric: LDP                                   # MPLS handoff protocol, choose from [LDP, SR]
              dci_routing_proto: isis                            # Routing protocol used on the DCI MPLS link, choose from [is-is, ospf]

          - dst_fabric: "{{ ansible_unnum_fabric }}"             # Destination fabric
            src_interface:  Loopback101                          # Loopback interface on the Source fabric
            dst_interface:  Loopback1                            # Loopback interface on the Destination fabric
            src_device: "{{ ansible_num_switch1 }}"              # Device on the Source fabric
            dst_device: "{{ ansible_unnum_switch1 }}"            # Device on the Destination fabric
            template: ext_vxlan_mpls_overlay_setup               #Template of MPLS handoff overlay link
            profile:
              neighbor_ip: 2.2.2.2 .                             # IP address of the loopback interface of destination device
              src_asn: 498278384                                 # BGP ASN in source fabric
              dst_asn: 498278384                                 # BGP ASN in destination fabric



# FABRIC WITH VPC PAIRED SWITCHES

    - name: Create Links
      cisco.dcnm.dcnm_links:
        state: merged                                            # choose from [merged, replaced, deleted, query]
        src_fabric: "ansible_vpc_fabric"
        config:
          - dst_fabric: "ansible_vpc_fabric"                     # Destination fabric
            src_interface: "Ethernet1/4"                         # Interface on the Source fabric
            dst_interface: "Ethernet1/4"                         # Interface on the Destination fabric
            src_device: "ansible_vpc_switch1"                    # Device on the Source fabric
            dst_device: "ansible_vpc_switch2"                    # Device on the Destination fabric
            template: int_intra_vpc_peer_keep_alive_link         # template to be applied, choose from
                                                                 #   [ int_intra_fabric_ipv6_link_local, int_intra_fabric_num_link,
                                                                 #     int_intra_fabric_unnum_link, int_intra_vpc_peer_keep_alive_link,
                                                                 #     int_pre_provision_intra_fabric_link, ios_xe_int_intra_fabric_num_link ]

            profile:
              peer1_ipv4_addr: 192.170.1.1                       # IPV4 address of the Source interface
              peer2_ipv4_addr: 192.170.1.2                       # IPV4 address of the Destination interface
              peer1_ipv6_addr: fe80:2a::01                       # optional, default is ""
              peer2_ipv6_addr: fe80:2a::02                       # optional, default is ""
              admin_state: true                                  # choose from [true, false]
              mtu: 9216                                          #
              peer1_description: "Description of source"         # optional, default is ""
              peer2_description: "Description of dest"           # optional, default is ""
              enable_macsec: false                               # optional, choose from [true, false]
              peer1_cmds:                                        # Freeform config for source device
                - no shutdown                                    # optional, default is ""
              peer2_cmds:                                        # Freeform config for destination device
                - no shutdown                                    # optional, default is ""
              intf_vrf: "test_vrf"                               # optional, default is ""

# UNNUMBERED FABRIC

    - name: Create Links
      cisco.dcnm.dcnm_links:
        state: merged                                            # choose from [merged, replaced, deleted, query]
        src_fabric: "ansible_unnum_fabric"
        config:
          - dst_fabric: "ansible_unnum_fabric"                   # Destination fabric
            src_interface: "Ethernet1/1"                         # Interface on the Source fabric
            dst_interface: "Ethernet1/1"                         # Interface on the Destination fabric
            src_device: "ansible_unnum_switch1"                  # Device on the Source fabric
            dst_device: "ansible_unnum_switch2"                  # Device on the Destination fabric
            template: int_intra_fabric_unnum_link                # template to be applied, choose from
                                                                 #   [ int_intra_fabric_ipv6_link_local, int_intra_fabric_num_link,
                                                                 #     int_intra_fabric_unnum_link, int_intra_vpc_peer_keep_alive_link,
                                                                 #     int_pre_provision_intra_fabric_link, ios_xe_int_intra_fabric_num_link ]

            profile:
              admin_state: true                                  # choose from [true, false]
              mtu: 9216                                          #
              peer1_description: "Description of source"         # optional, default is ""
              peer2_description: "Description of dest"           # optional, default is ""
              enable_macsec: false                               # optional, choose from [true, false]
              peer1_cmds:                                        # Freeform config for source device
                - no shutdown                                    # optional, default is ""
              peer2_cmds:                                        # Freeform config for destination device
                - no shutdown                                    # optional, default is ""

          - dst_fabric: "ansible_unnum_fabric"                   # Destination fabric
            src_interface: "Ethernet1/2"                         # Interface on the Source fabric
            dst_interface: "Ethernet1/2"                         # Interface on the Destination fabric
            src_device: "ansible_unnum_switch1"                  # Device on the Source fabric
            dst_device: "ansible_unnum_switch2"                  # Device on the Destination fabric
            template: int_pre_provision_intra_fabric_link        # template to be applied, choose from
                                                                 #   [ int_intra_fabric_ipv6_link_local, int_intra_fabric_num_link,
                                                                 #     int_intra_fabric_unnum_link, int_intra_vpc_peer_keep_alive_link,
                                                                 #     int_pre_provision_intra_fabric_link, ios_xe_int_intra_fabric_num_link ]

# IPV6 UNDERLAY FABRIC

    - name: Create Links
      cisco.dcnm.dcnm_links:
        state: merged                                            # choose from [merged, replaced, deleted, query]
        src_fabric: "ansible_ipv6_fabric"
        config:
          - dst_fabric: "ansible_ipv6_fabric"                    # Destination fabric
            src_interface: "Ethernet1/1"                         # Interface on the Source fabric
            dst_interface: "Ethernet1/1"                         # Interface on the Destination fabric
            src_device: "ansible_ipv6_switch1"                   # Device on the Source fabric
            dst_device: "ansible_ipv6_switch2"                   # Device on the Destination fabric
            template: int_intra_fabric_ipv6_link_local           # template to be applied, choose from
                                                                 #   [ int_intra_fabric_ipv6_link_local, int_intra_fabric_num_link,
                                                                 #     int_intra_fabric_unnum_link, int_intra_vpc_peer_keep_alive_link,
                                                                 #     int_pre_provision_intra_fabric_link, ios_xe_int_intra_fabric_num_link ]

            profile:
              peer1_ipv4_addr: 192.169.1.1                       # optional, default is ""
              peer2_ipv4_addr: 192.169.1.2                       # optional, default is ""
              peer1_ipv6_addr: fe80:0201::01                     # IP address of the Source interface
              peer2_ipv6_addr: fe80:0201::02                     # IP address of the Source interface
              admin_state: true                                  # choose from [true, false]
              mtu: 9216                                          #
              peer1_description: "Description of source"         # optional, default is ""
              peer2_description: "Description of dest"           # optional, default is ""
              peer1_bfd_echo_disable: false                      # optional, choose from [true, false]
              peer2_bfd_echo_disable: false                      # optional, choose from [true, false]
              enable_macsec: false                               # optional, choose from [true, false]
              peer1_cmds:                                        # Freeform config for source device
                - no shutdown                                    # optional, default is ""
              peer2_cmds:                                        # Freeform config for destination device
                - no shutdown                                    # optional, default is ""

          - dst_fabric: "ansible_ipv6_fabric"                    # Destination fabric
            src_interface: "Ethernet1/2"                         # Interface on the Source fabric
            dst_interface: "Ethernet1/2"                         # Interface on the Destination fabric
            src_device: "ansible_ipv6_switch1"                   # Device on the Source fabric
            dst_device: "ansible_ipv6_switch2"                   # Device on the Destination fabric
            template: int_pre_provision_intra_fabric_link        # template to be applied, choose from
                                                                 #   [ int_intra_fabric_ipv6_link_local, int_intra_fabric_num_link,
                                                                 #     int_intra_fabric_unnum_link, int_intra_vpc_peer_keep_alive_link,
                                                                 #     int_pre_provision_intra_fabric_link, ios_xe_int_intra_fabric_num_link ]
          - dst_fabric: "ansible_ipv6_fabric"                    # Destination fabric
            src_interface: "Ethernet1/3"                         # Interface on the Source fabric
            dst_interface: "Ethernet1/3"                         # Interface on the Destination fabric
            src_device: "ansible_ipv6_switch1"                   # Device on the Source fabric
            dst_device: "ansible_ipv6_switch2"                   # Device on the Destination fabric
            template: int_intra_fabric_num_link                  # template to be applied, choose from
                                                                 #   [ int_intra_fabric_ipv6_link_local, int_intra_fabric_num_link,
                                                                 #     int_intra_fabric_unnum_link, int_intra_vpc_peer_keep_alive_link,
                                                                 #     int_pre_provision_intra_fabric_link, ios_xe_int_intra_fabric_num_link ]

            profile:
              peer1_ipv4_addr: 192.169.2.1                       # IPV4 address of the Source interface
              peer2_ipv4_addr: 192.169.2.2                       # IPV4 address of the Destination interface
              peer1_ipv6_addr: fe80:0202::01                     # IP address of the Source interface
              peer2_ipv6_addr: fe80:0202::02                     # IP address of the Source interface
              admin_state: true                                  # choose from [true, false]
              mtu: 1500                                          # optional, default is 1500
              peer1_description: "Description of source"         # optional, default is ""
              peer2_description: "Description of dest"           # optional, default is ""
              peer1_bfd_echo_disable: false                      # optional, choose from [true, false]
              peer2_bfd_echo_disable: false                      # optional, choose from [true, false]
              enable_macsec: false                               # optional, choose from [true, false]
              peer1_cmds:                                        # Freeform config for source device
                - no shutdown                                    # optional, default is ""
              peer2_cmds:                                        # Freeform config for destination device
                - no shutdown                                    # optional, default is ""
# DELETE LINKS

    - name: Delete Links
      cisco.dcnm.dcnm_links:
        state: deleted                                           # choose from [merged, replaced, deleted, query]
        src_fabric: "ansible_num_fabric"
        config:
          - dst_fabric: "ansible_num_fabric"                     # Destination fabric
            src_interface: "Ethernet1/1"                         # Interface on the Source fabric
            dst_interface: "Ethernet1/1"                         # Interface on the Destination fabric
            src_device: 193.168.1.1                              # Device on the Source fabric
            dst_device: 193.168.1.2                              # Device on the Destination fabric

# QUERY LINKS

    - name: Query Links - with Src Fabric
      cisco.dcnm.dcnm_links:
        state: query                                             # choose from [merged, replaced, deleted, query]
        src_fabric: "ansible_num_fabric"

    - name: Query Links - with Src & Dst Fabric
      cisco.dcnm.dcnm_links:
        state: query                                             # choose from [merged, replaced, deleted, query]
        src_fabric: "ansible_num_fabric"
        config:
          - dst_fabric: "ansible_num_fabric"                     # optional, Destination fabric

    - name: Query Links - with Src & Dst Fabric, Src Intf
      cisco.dcnm.dcnm_links:
        state: query                                             # choose from [merged, replaced, deleted, query]
        src_fabric: "ansible_num_fabric"
        config:
          - dst_fabric: "ansible_num_fabric"                     # optional, Destination fabric
            src_interface: "Ethernet1/1"                         # optional, Interface on the Source fabric

    - name: Query Links - with Src & Dst Fabric, Src & Dst Intf
      cisco.dcnm.dcnm_links:
        state: query                                             # choose from [merged, replaced, deleted, query]
        src_fabric: "ansible_num_fabric"
        config:
          - dst_fabric: "ansible_num_fabric"                     # optional, Destination fabric
            src_interface: "Ethernet1/1"                         # optional, Interface on the Source fabric
            dst_interface: "Ethernet1/1"                         # optional, Interface on the Destination fabric

    - name: Query Links - with Src & Dst Fabric, Src & Dst Intf, Src Device
      cisco.dcnm.dcnm_links:
        state: query                                             # choose from [merged, replaced, deleted, query]
        src_fabric: "ansible_num_fabric"
        config:
          - dst_fabric: "ansible_num_fabric"                     # optional, Destination fabric
            src_interface: "Ethernet1/1"                         # optional, Interface on the Source fabric
            dst_interface: "Ethernet1/1"                         # optional, Interface on the Destination fabric
            src_device: 193.168.1.1                              # optional, Device on the Source fabric
      register: result

    - assert:
        that:
          '(result["response"] | length) >= 1'

    - name: Query Links - with Src & Dst Fabric, Src & Dst Intf, Src & Dst Device
      cisco.dcnm.dcnm_links:
        state: query                                             # choose from [merged, replaced, deleted, query]
        src_fabric: "ansible_num_fabric"
        config:
          - dst_fabric: "ansible_num_fabric"                     # optional, Destination fabric
            src_interface: "Ethernet1/1"                         # optional, Interface on the Source fabric
            dst_interface: "Ethernet1/1"                         # optional, Interface on the Destination fabric
            src_device: 193.168.1.1                              # optional, Device on the Source fabric
            dst_device: 193.168.1.2                              # optional, Device on the Destination fabric
 #
 # INTRA-FABRIC
 #
    - name: Query Links - with Src & Dst Fabric, Src & Dst Intf, Src & Dst Device, Template
      cisco.dcnm.dcnm_links:
        state: query                                             # choose from [merged, replaced, deleted, query]
        src_fabric: "ansible_num_fabric"
        config:
          - dst_fabric: "ansible_num_fabric"                     # optional, Destination fabric
            src_interface: "Ethernet1/1"                         # optional, Interface on the Source fabric
            dst_interface: "Ethernet1/1"                         # optional, Interface on the Destination fabric
            src_device: 193.168.1.1                              # optional, Device on the Source fabric
            dst_device: 193.168.1.2                              # optional, Device on the Destination fabric
            template: int_intra_fabric_num_link                  # optional, template to be applied, choose from
                                                                 #   [ int_intra_fabric_ipv6_link_local, int_intra_fabric_num_link,
                                                                 #     int_intra_fabric_unnum_link, int_intra_vpc_peer_keep_alive_link,
                                                                 #     int_pre_provision_intra_fabric_link, ios_xe_int_intra_fabric_num_link ]
#
# INTER-FABRIC
#
    - name: Query Links - with Src & Dst Fabric, Src & Dst Intf, Src & Dst Device, Template
      cisco.dcnm.dcnm_links:
        state: query                                             # choose from [merged, replaced, deleted, query]
        src_fabric: "{{ ansible_num_fabric }}"
        config:
          - dst_fabric: "{{ ansible_ipv6_fabric }}"              # optional, Destination fabric
            src_interface: "{{ intf_1_6 }}"                      # optional, Interface on the Source fabric
            dst_interface: "{{ intf_1_6 }}"                      # optional, Interface on the Destination fabric
            src_device: "{{ ansible_num_switch1 }}"              # optional, Device on the Source fabric
            dst_device: "{{ ansible_ipv6_switch1 }}"             # optional, Device on the Destination fabric
            template: ext_fabric_setup                           # optional, template to be applied, choose from
                                                                 #   [ ext_fabric_setup, ext_multisite_underlay_setup,
                                                                 #     ext_evpn_multisite_overlay_setup ]
"""

import time
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
    get_fabric_details,
    dcnm_get_ip_addr_info,
)


# Resource Class object which includes all the required methods and data to configure and maintain Links
class DcnmLinks:
    dcnm_links_paths = {
        11: {
            "LINKS_GET_BY_SWITCH_PAIR": "/rest/control/links",
            "LINKS_CREATE": "/rest/control/links",
            "LINKS_DELETE": "/rest/control/links/",
            "LINKS_UPDATE": "/rest/control/links/",
            "LINKS_GET_BY_FABRIC": "/rest/control/links/fabrics/{}",
            "LINKS_CFG_DEPLOY": "/rest/control/fabrics/{}/config-deploy/",
            "CONFIG_PREVIEW": "/rest/control/fabrics/{}/config-preview/",
            "FABRIC_ACCESS_MODE": "/rest/control/fabrics/{}/accessmode",
        },
        12: {
            "LINKS_GET_BY_SWITCH_PAIR": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/links",
            "LINKS_CREATE": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/links",
            "LINKS_DELETE": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/links/",
            "LINKS_UPDATE": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/links/",
            "LINKS_GET_BY_FABRIC": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/links/fabrics/{}",
            "LINKS_CFG_DEPLOY": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{}/config-deploy/",
            "CONFIG_PREVIEW": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{}/config-preview/",
            "FABRIC_ACCESS_MODE": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{}/accessmode",
        },
    }

    dcnm_links_xlate_template = {
        11: {
            "int_intra_fabric_ipv6_link_local": "int_intra_fabric_ipv6_link_local",
            "int_intra_fabric_num_link": "int_intra_fabric_num_link_11_1",
            "int_intra_fabric_unnum_link": "int_intra_fabric_unnum_link_11_1",
            "int_intra_vpc_peer_keep_alive_link": "int_intra_vpc_peer_keep_alive_link_11_1",
            "int_pre_provision_intra_fabric_link": "int_pre_provision_intra_fabric_link",
            "ios_xe_int_intra_fabric_num_link": "ios_xe_int_intra_fabric_num_link",
            "ext_fabric_setup": "ext_fabric_setup_11_1",
            "ext_multisite_underlay_setup": "ext_multisite_underlay_setup_11_1",
            "ext_evpn_multisite_overlay_setup": "ext_evpn_multisite_overlay_setup",
            "ext_vxlan_mpls_overlay_setup": "ext_vxlan_mpls_overlay_setup",
            "ext_vxlan_mpls_underlay_setup": "ext_vxlan_mpls_underlay_setup",
        },
        12: {
            "int_intra_fabric_ipv6_link_local": "int_intra_fabric_ipv6_link_local",
            "int_intra_fabric_num_link": "int_intra_fabric_num_link",
            "int_intra_fabric_unnum_link": "int_intra_fabric_unnum_link",
            "int_intra_vpc_peer_keep_alive_link": "int_intra_vpc_peer_keep_alive_link",
            "int_pre_provision_intra_fabric_link": "int_pre_provision_intra_fabric_link",
            "ios_xe_int_intra_fabric_num_link": "ios_xe_int_intra_fabric_num_link",
            "ext_fabric_setup": "ext_fabric_setup",
            "ext_multisite_underlay_setup": "ext_multisite_underlay_setup",
            "ext_evpn_multisite_overlay_setup": "ext_evpn_multisite_overlay_setup",
            "ext_vxlan_mpls_overlay_setup": "ext_vxlan_mpls_overlay_setup",
            "ext_vxlan_mpls_underlay_setup": "ext_vxlan_mpls_underlay_setup",
        },
    }

    dcnm_links_xlated_template_names = {
        11: [
            "int_intra_fabric_ipv6_link_local",
            "int_intra_fabric_num_link_11_1",
            "int_intra_fabric_unnum_link_11_1",
            "int_intra_vpc_peer_keep_alive_link_11_1",
            "int_pre_provision_intra_fabric_link",
            "ios_xe_int_intra_fabric_num_link",
            "ext_fabric_setup_11_1",
            "ext_multisite_underlay_setup_11_1",
            "ext_evpn_multisite_overlay_setup",
            "ext_vxlan_mpls_overlay_setup",
            "ext_vxlan_mpls_underlay_setup",
        ],
        12: [
            "int_intra_fabric_ipv6_link_local",
            "int_intra_fabric_num_link",
            "int_intra_fabric_unnum_link",
            "int_intra_vpc_peer_keep_alive_link",
            "int_pre_provision_intra_fabric_link",
            "ios_xe_int_intra_fabric_num_link",
            "ext_fabric_setup",
            "ext_multisite_underlay_setup",
            "ext_evpn_multisite_overlay_setup",
            "ext_vxlan_mpls_overlay_setup",
            "ext_vxlan_mpls_underlay_setup",
        ],
    }

    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.fabric = module.params["src_fabric"]
        self.deploy = module.params["deploy"]
        self.config = copy.deepcopy(module.params.get("config", []))
        self.links_info = []
        self.want = []
        self.have = []
        self.diff_create = []
        self.diff_modify = []
        self.diff_delete = []
        self.diff_deploy = {}
        self.monitoring = []
        self.meta_switches = []
        self.fd = None
        self.changed_dict = [
            {
                "merged": [],
                "deleted": [],
                "modified": [],
                "query": [],
                "deploy": [],
                "debugs": [],
            }
        ]

        self.dcnm_version = dcnm_version_supported(self.module)
        self.inventory_data = get_fabric_inventory_details(
            self.module, self.fabric
        )

        self.src_fabric_info = get_fabric_details(self.module, self.fabric)

        self.paths = self.dcnm_links_paths[self.dcnm_version]
        self.templates = self.dcnm_links_xlate_template[self.dcnm_version]
        self.template_choices = self.dcnm_links_xlated_template_names[
            self.dcnm_version
        ]

        self.result = dict(changed=False, diff=[], response=[])

    def log_msg(self, msg):

        if self.fd is None:
            self.fd = open("dcnm_links.log", "a+")
        if self.fd is not None:
            self.fd.write(msg)
            self.fd.write("\n")
            self.fd.flush()

    def dcnm_dump_have_db(self):

        lhave = []

        for have in self.have:
            lhave.append(
                {
                    "UUID": have["link-uuid"],
                    "SRC FABRIC": have["sw1-info"]["fabric-name"],
                    "SRC IF NAME": have["sw1-info"]["if-name"],
                    "SRC SNO": have["sw1-info"]["sw-serial-number"],
                    "SRC SYS NAME": have["sw1-info"]["sw-sys-name"],
                    "DST FABRIC": have["sw2-info"]["fabric-name"],
                    "DST IF NAME": have["sw2-info"]["if-name"],
                    "DST SNO": have["sw2-info"]["sw-serial-number"],
                    "DST SYS NAME": have["sw2-info"]["sw-sys-name"],
                }
            )
        self.log_msg(f"HAVE = {lhave}\n")

    def dcnm_print_have(self, have):

        lhave = []

        lhave.append(
            {
                "UUID": have["link-uuid"],
                "SRC FABRIC": have["sw1-info"]["fabric-name"],
                "SRC IF NAME": have["sw1-info"]["if-name"],
                "SRC SNO": have["sw1-info"]["sw-serial-number"],
                "SRC SYS NAME": have["sw1-info"]["sw-sys-name"],
                "DST FABRIC": have["sw2-info"]["fabric-name"],
                "DST IF NAME": have["sw2-info"]["if-name"],
                "DST SNO": have["sw2-info"]["sw-serial-number"],
                "DST SYS NAME": have["sw2-info"]["sw-sys-name"],
            }
        )

        self.log_msg(f"have = {lhave}\n")

    def dcnm_links_compare_ip_addresses(self, addr1, addr2):

        """
        Routine to compare the IP address values after converting to IP address objects.

        Parameters:
            addrr1 : First IP address value
            addrr2 : Second IP address value

        Returns:
            True - if both addresses are same
            False - otherwise
        """

        rv1 = ""
        rv2 = ""

        if "/" in addr1:
            rv1 = addr1.split("/")
        if "/" in addr2:
            rv2 = addr2.split("/")

        if rv1 and not rv2:
            return False
        if rv2 and not rv1:
            return False
        if rv1 and rv2:
            return (
                ipaddress.ip_address(rv1[0]) == ipaddress.ip_address(rv2[0])
            ) and (rv1[1] == rv2[1])
        else:
            return ipaddress.ip_address(addr1) == ipaddress.ip_address(addr2)

    def dcnm_links_validate_and_build_links_info(self, cfg, link_spec):

        """
        Routine to validate the playbook input and fill up default values for objects not included.
        In this case we validate the playbook against link_spec which includes required information
        This routine updates self.links_info with validated playbook information by defaulting values
        not included

        Parameters:
            cfg (dict): The config from playbook
            link_spec (dict): Links spec

        Returns:
            None
        """

        links_info, invalid_params = validate_list_of_dicts(cfg, link_spec)
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(
                "while processing Link Info related to -  [ "
                + "src_fabric: "
                + self.fabric
                + ", "
                + "dst_fabric: "
                + cfg[0].get("dst_fabric", "NA")
                + ", "
                + "src_device: "
                + cfg[0].get("src_device", "NA")
                + ", "
                + "dst_device: "
                + cfg[0].get("dst_device", "NA")
                + ", "
                + "src_interface: "
                + cfg[0].get("src_interface", "NA")
                + ", "
                + "dst_interface: "
                + cfg[0].get("dst_interface", "NA")
                + ", "
                + "template: "
                + cfg[0].get("template", "NA")
                + " ], "
                + "\n".join(invalid_params)
            )
            self.module.fail_json(msg=mesg)

        if cfg[0].get("profile", "") == "":
            self.links_info.extend(links_info)
            return

        cfg_profile = []
        cfg_profile.append(cfg[0]["profile"])

        profile_info, invalid_params = validate_list_of_dicts(
            cfg_profile, link_spec["profile"]
        )
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(
                "while processing Link Info related to -  [ "
                + "src_fabric: "
                + self.fabric
                + ", "
                + "dst_fabric: "
                + cfg[0].get("dst_fabric", "NA")
                + ", "
                + "src_device: "
                + cfg[0].get("src_device", "NA")
                + ", "
                + "dst_device: "
                + cfg[0].get("dst_device", "NA")
                + ", "
                + "src_interface: "
                + cfg[0].get("src_interface", "NA")
                + ", "
                + "dst_interface: "
                + cfg[0].get("dst_interface", "NA")
                + ", "
                + "template: "
                + cfg[0].get("template", "NA")
                + " ], "
                + "\n".join(invalid_params)
            )
            self.module.fail_json(msg=mesg)

        links_info[0]["profile"] = profile_info[0]
        self.links_info.extend(links_info)

    def dcnm_links_validate_input(self):

        """
        Routine to validate playbook input based on the state. Since each state has a different
        config structure, this routine handles the validation based on the given state

        Parameters:
            None

        Returns:
            None
        """

        if [] is self.config:
            return

        cfg = []
        for item in self.config:

            citem = copy.deepcopy(item)

            cfg.append(citem)

            if self.module.params["state"] == "query":
                # config for query state is different. So validate query state differently
                self.dcnm_links_validate_query_state_input(cfg)
            elif self.module.params["state"] == "deleted":
                # config for deleted state is different. So validate deleted state differently
                self.dcnm_links_validate_deleted_state_input(cfg)
            else:
                self.dcnm_links_validate_links_input(cfg)
            cfg.remove(citem)

    def dcnm_links_get_intra_fabric_link_spec(self, cfg):

        intra_fabric_choices = self.template_choices[0:6]

        link_spec = dict(
            dst_fabric=dict(required=True, type="str"),
            src_device=dict(required=True, type="str"),
            dst_device=dict(required=True, type="str"),
            src_interface=dict(required=True, type="str"),
            dst_interface=dict(required=True, type="str"),
            template=dict(
                required=True, type="str", choices=intra_fabric_choices
            ),
            profile=dict(),
        )

        if cfg[0].get("template", "") == "":
            self.module.fail_json(msg="Required parameter not found: template")

        if (
            cfg[0]["template"]
            != self.templates["int_pre_provision_intra_fabric_link"]
        ):
            if cfg[0].get("profile", None) is None:
                self.module.fail_json(
                    msg="Required information not found: profile"
                )

        if (
            (cfg[0]["template"] == self.templates["int_intra_fabric_num_link"])
            or (
                cfg[0]["template"]
                == self.templates["ios_xe_int_intra_fabric_num_link"]
            )
            or (
                cfg[0]["template"]
                == self.templates["int_intra_vpc_peer_keep_alive_link"]
            )
        ):
            if (
                self.src_fabric_info["nvPairs"]
                .get("UNDERLAY_IS_V6", "false")
                .lower()
                == "false"
            ):
                link_spec["profile"]["peer1_ipv4_addr"] = dict(
                    required=True, type="ipv4"
                )
                link_spec["profile"]["peer2_ipv4_addr"] = dict(
                    required=True, type="ipv4"
                )
            else:
                link_spec["profile"]["peer1_ipv6_addr"] = dict(
                    required=True, type="ipv6"
                )
                link_spec["profile"]["peer2_ipv6_addr"] = dict(
                    required=True, type="ipv6"
                )
                link_spec["profile"]["peer1_ipv4_addr"] = dict(
                    type="ipv4", default=""
                )
                link_spec["profile"]["peer2_ipv4_addr"] = dict(
                    type="ipv4", default=""
                )
        if (
            cfg[0]["template"]
            != self.templates["int_pre_provision_intra_fabric_link"]
        ):
            link_spec["profile"]["admin_state"] = dict(
                required=True, type="bool", choices=[True, False]
            )
            if (
                cfg[0]["template"]
                != self.templates["ios_xe_int_intra_fabric_num_link"]
            ):
                link_spec["profile"]["mtu"] = dict(required=True, type="int")
            else:
                link_spec["profile"]["mtu"] = dict(type="int", default=1500)
            link_spec["profile"]["peer1_description"] = dict(
                type="str", default=""
            )
            link_spec["profile"]["peer2_description"] = dict(
                type="str", default=""
            )
            link_spec["profile"]["peer1_cmds"] = dict(type="list", default=[])
            link_spec["profile"]["peer2_cmds"] = dict(type="list", default=[])

        if (
            (cfg[0]["template"] == self.templates["int_intra_fabric_num_link"])
            or (
                cfg[0]["template"]
                == self.templates["int_intra_fabric_ipv6_link_local"]
            )
            or (
                cfg[0]["template"]
                == self.templates["int_intra_fabric_unnum_link"]
            )
        ):
            link_spec["profile"]["enable_macsec"] = dict(
                type="bool", default=False
            )

        if (
            cfg[0]["template"]
            == self.templates["int_intra_vpc_peer_keep_alive_link"]
        ):
            link_spec["profile"]["intf_vrf"] = dict(type="str", default="")

        if cfg[0]["template"] == self.templates["int_intra_fabric_num_link"]:
            link_spec["profile"]["peer1_bfd_echo_disable"] = dict(
                type="bool", default=False
            )
            link_spec["profile"]["peer2_bfd_echo_disable"] = dict(
                type="bool", default=False
            )

        return link_spec

    def dcnm_links_get_inter_fabric_link_spec(self, cfg):

        inter_fabric_choices = self.template_choices[6:11]

        link_spec = dict(
            dst_fabric=dict(required=True, type="str"),
            src_device=dict(required=True, type="str"),
            dst_device=dict(required=True, type="str"),
            src_interface=dict(required=True, type="str"),
            dst_interface=dict(required=True, type="str"),
            template=dict(
                required=True, type="str", choices=inter_fabric_choices
            ),
            profile=dict(),
        )

        if cfg[0].get("template", "") == "":
            self.module.fail_json(msg="Required parameter not found: template")

        if (
            (
                cfg[0].get("template", "")
                == self.templates["ext_multisite_underlay_setup"]
            )
            or (
                cfg[0].get("template", "")
                == self.templates["ext_fabric_setup"]
            )
            or (
                cfg[0].get("template", "")
                == self.templates["ext_vxlan_mpls_underlay_setup"]
            )
        ):
            link_spec["profile"]["ipv4_subnet"] = dict(
                required=True, type="ipv4_subnet"
            )
            link_spec["profile"]["mtu"] = dict(type="int", default=9216)
            link_spec["profile"]["peer1_description"] = dict(
                type="str", default=""
            )
            link_spec["profile"]["peer2_description"] = dict(
                type="str", default=""
            )
            link_spec["profile"]["peer1_cmds"] = dict(type="list", default=[])
            link_spec["profile"]["peer2_cmds"] = dict(type="list", default=[])
        elif (
            cfg[0].get("template")
            != self.templates["ext_vxlan_mpls_overlay_setup"]
        ):
            link_spec["profile"]["ipv4_addr"] = dict(
                required=True, type="ipv4"
            )

        link_spec["profile"]["neighbor_ip"] = dict(required=True, type="ipv4")
        # src_asn and dst_asn are not common parameters
        if (
            (
                cfg[0].get("template", "")
                == self.templates["ext_multisite_underlay_setup"]
            )
            or (
                cfg[0].get("template", "")
                == self.templates["ext_fabric_setup"]
            )
            or (
                cfg[0].get("template", "")
                == self.templates["ext_vxlan_mpls_overlay_setup"]
            )
        ):
            link_spec["profile"]["src_asn"] = dict(required=True, type="int")
            link_spec["profile"]["dst_asn"] = dict(required=True, type="int")

        if cfg[0].get("template", "") == self.templates["ext_fabric_setup"]:
            link_spec["profile"]["auto_deploy"] = dict(
                type="bool", default=False
            )

        if (
            cfg[0].get("template", "")
            == self.templates["ext_multisite_underlay_setup"]
        ):
            link_spec["profile"]["max_paths"] = dict(type="int", default=1)
            link_spec["profile"]["route_tag"] = dict(type="str", default="")
            link_spec["profile"]["deploy_dci_tracking"] = dict(
                type="bool", default=False
            )

        if (
            cfg[0].get("template", "")
            == self.templates["ext_evpn_multisite_overlay_setup"]
        ):
            link_spec["profile"]["trm_enabled"] = dict(
                type="bool", default=False
            )
            link_spec["profile"]["bgp_multihop"] = dict(type="int", default=5)

        if (
            cfg[0].get("template", "")
            == self.templates["ext_multisite_underlay_setup"]
        ) or (
            cfg[0].get("template", "")
            == self.templates["ext_evpn_multisite_overlay_setup"]
        ):
            link_spec["profile"]["ebgp_password_enable"] = dict(
                type="bool", default=True
            )

            if cfg[0].get("profile", None) is None:
                self.module.fail_json(
                    msg="Required information not found: profile"
                )

            # Other parameters depend on "bgp_password_enable" flag.
            if cfg[0]["profile"].get("ebgp_password_enable", True) is True:
                link_spec["profile"]["inherit_from_msd"] = dict(
                    type="bool", default=True
                )
                if cfg[0]["profile"].get("inherit_from_msd", True) is False:
                    link_spec["profile"]["ebgp_password"] = dict(
                        required=True, type="str"
                    )
                    link_spec["profile"]["ebgp_auth_key_type"] = dict(
                        type="int", default=3, choices=[3, 7]
                    )
        if (
            cfg[0].get("template", "")
            == self.templates["ext_vxlan_mpls_underlay_setup"]
        ):
            link_spec["profile"]["mpls_fabric"] = dict(
                type="str", default="SR", choice=["SR", "LDP"]
            )
            link_spec["profile"]["dci_routing_proto"] = dict(
                type="str", default="is-is", choice=["is-is", "ospf"]
            )
            link_spec["profile"]["dci_routing_tag"] = dict(
                type="str", default="MPLS_UNDERLAY", choice=["is-is", "ospf"]
            )
            link_spec["profile"]["peer1_sr_mpls_index"] = dict(
                type="int", default=0
            )
            link_spec["profile"]["peer2_sr_mpls_index"] = dict(
                type="int", default=0
            )
            link_spec["profile"]["global_block_range"] = dict(
                type="str", default="16000-23999"
            )
            link_spec["profile"]["ospf_area_id"] = dict(
                type="str", default="0.0.0.0"
            )

        return link_spec

    def dcnm_links_validate_links_input(self, cfg):

        """
        Routine to validate the playbook input. This routine updates self.links_info
        with validated playbook information by defaulting values not included

        Parameters:
            cfg (dict): The config from playbook

        Returns:
            None
        """

        if cfg[0].get("dst_fabric", "") == "":
            self.module.fail_json(
                msg="Required parameter not found: dst_fabric"
            )

        if self.fabric == cfg[0]["dst_fabric"]:
            link_spec = self.dcnm_links_get_intra_fabric_link_spec(cfg)
        else:
            link_spec = self.dcnm_links_get_inter_fabric_link_spec(cfg)

        self.dcnm_links_validate_and_build_links_info(cfg, link_spec)

    def dcnm_links_validate_deleted_state_input(self, cfg):

        """
        Playbook input will be different for differnt states. This routine validates the query state
        input. This routine updates self.links_info with validated playbook information related to query
        state.

        Parameters:
            cfg (dict): The config from playbook

        Returns:
           None
        """

        link_spec = dict(
            dst_fabric=dict(required=True, type="str"),
            src_device=dict(required=True, type="str"),
            dst_device=dict(required=True, type="str"),
            src_interface=dict(required=True, type="str"),
            dst_interface=dict(required=True, type="str"),
        )

        links_info, invalid_params = validate_list_of_dicts(cfg, link_spec)
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

        if links_info:
            self.links_info.extend(links_info)

    def dcnm_links_validate_query_state_input(self, cfg):

        """
        Playbook input will be different for differnt states. This routine validates the query state
        input. This routine updates self.links_info with validated playbook information related to query
        state.

        Parameters:
            cfg (dict): The config from playbook

        Returns:
           None
        """

        link_spec = dict(
            dst_fabric=dict(type="str", default=""),
            src_device=dict(type="str", default=""),
            dst_device=dict(type="str", default=""),
            src_interface=dict(type="str", default=""),
            dst_interface=dict(type="str", default=""),
            template=dict(
                type="str", choices=self.template_choices, default=""
            ),
        )

        links_info, invalid_params = validate_list_of_dicts(cfg, link_spec)
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

        if links_info:
            self.links_info.extend(links_info)

    def dcnm_links_get_links_payload(self, link):

        """
        This routine builds the complete Links payload based on the information in self.want

        Parameters:
            link (dict): Link information

        Returns:
            link_payload (dict): Link payload information populated with appropriate data from playbook config
        """

        link_payload = {
            "sourceFabric": self.fabric,
            "destinationFabric": link.get("dst_fabric"),
            "sourceInterface": link.get("src_interface"),
            "destinationInterface": link.get("dst_interface"),
        }

        if link.get("src_device") in self.ip_sn:
            link_payload["sourceDevice"] = self.ip_sn[link.get("src_device")]
        else:
            link_payload["sourceDevice"] = self.hn_sn.get(
                link["src_device"], ""
            )

        if link.get("dst_device") in self.ip_sn:
            link_payload["destinationDevice"] = self.ip_sn[
                link.get("dst_device")
            ]
        else:
            link_payload["destinationDevice"] = self.hn_sn.get(
                link["dst_device"], ""
            )

        # At this point link_payload will have sourceDevice set to proper SNO and destinationDevice is either
        # set to a proper SNO or "".

        if link_payload["sourceDevice"] in self.sn_hn:
            link_payload["sourceSwitchName"] = self.sn_hn.get(
                link_payload["sourceDevice"], "Switch1"
            )
        else:
            link_payload["sourceSwitchName"] = link.get("src_device")

        if link_payload["destinationDevice"] in self.sn_hn:
            link_payload["destinationSwitchName"] = self.sn_hn.get(
                link_payload["destinationDevice"], "Switch2"
            )
        else:
            link_payload["destinationSwitchName"] = link.get("dst_device")

        if self.module.params["state"] == "deleted":
            return link_payload

        link_payload["templateName"] = link.get("template")

        # Intra and Inter fabric payloads are different. Build them separately
        if link_payload["sourceFabric"] == link_payload["destinationFabric"]:
            self.dcnm_links_get_intra_fabric_links_payload(link, link_payload)
        else:
            self.dcnm_links_get_inter_fabric_links_payload(link, link_payload)

        return link_payload

    def dcnm_links_get_inter_fabric_links_payload(self, link, link_payload):

        """
        This routine builds the inter-fabric Links payload based on the information in the given
        link

        Parameters:
            link (dict): Link information
            link_payload (dict): Link payload to be updated

        Returns:
            link_payload (dict): Link payload information populated with appropriate data from playbook config
        """
        link_payload["nvPairs"] = {}
        if (
            (
                link["template"]
                == self.templates["ext_multisite_underlay_setup"]
            )
            or (link["template"] == self.templates["ext_fabric_setup"])
            or (
                link["template"]
                == self.templates["ext_vxlan_mpls_underlay_setup"]
            )
        ):
            ip_prefix = link["profile"]["ipv4_subnet"].split("/")

            link_payload["nvPairs"]["IP_MASK"] = (
                str(ipaddress.ip_address(ip_prefix[0])) + "/" + ip_prefix[1]
            )
            link_payload["nvPairs"]["MTU"] = link["profile"]["mtu"]
            link_payload["nvPairs"]["PEER1_DESC"] = link["profile"][
                "peer1_description"
            ]
            link_payload["nvPairs"]["PEER2_DESC"] = link["profile"][
                "peer2_description"
            ]

            if link["profile"].get("peer1_cmds") == []:
                link_payload["nvPairs"]["PEER1_CONF"] = ""
            else:
                link_payload["nvPairs"]["PEER1_CONF"] = "\n".join(
                    link["profile"].get("peer1_cmds")
                )

            if link["profile"].get("peer2_cmds") == []:
                link_payload["nvPairs"]["PEER2_CONF"] = ""
            else:
                link_payload["nvPairs"]["PEER2_CONF"] = "\n".join(
                    link["profile"].get("peer2_cmds")
                )
        elif (
            link["template"] != self.templates["ext_vxlan_mpls_overlay_setup"]
        ):
            link_payload["nvPairs"]["SOURCE_IP"] = str(
                ipaddress.ip_address(link["profile"]["ipv4_addr"])
            )

        link_payload["nvPairs"]["NEIGHBOR_IP"] = str(
            ipaddress.ip_address(link["profile"]["neighbor_ip"])
        )
        if (
            (
                link["template"]
                == self.templates["ext_multisite_underlay_setup"]
            )
            or (link["template"] == self.templates["ext_fabric_setup"])
            or (
                link["template"]
                == self.templates["ext_vxlan_mpls_overlay_setup"]
            )
        ):
            link_payload["nvPairs"]["asn"] = link["profile"]["src_asn"]
            link_payload["nvPairs"]["NEIGHBOR_ASN"] = link["profile"][
                "dst_asn"
            ]

        if link["template"] == self.templates["ext_fabric_setup"]:
            link_payload["nvPairs"]["AUTO_VRF_LITE_FLAG"] = link["profile"][
                "auto_deploy"
            ]
            link_payload["nvPairs"][
                "VRF_LITE_JYTHON_TEMPLATE"
            ] = "Ext_VRF_Lite_Jython"

        if link["template"] == self.templates["ext_multisite_underlay_setup"]:
            link_payload["nvPairs"]["MAX_PATHS"] = link["profile"]["max_paths"]
            link_payload["nvPairs"]["ROUTING_TAG"] = link["profile"][
                "route_tag"
            ]
            link_payload["nvPairs"]["DEPLOY_DCI_TRACKING"] = link["profile"][
                "deploy_dci_tracking"
            ]

        if (
            link["template"]
            == self.templates["ext_evpn_multisite_overlay_setup"]
        ):
            link_payload["nvPairs"]["TRM_ENABLED"] = link["profile"][
                "trm_enabled"
            ]
            link_payload["nvPairs"]["BGP_MULTIHOP"] = link["profile"][
                "bgp_multihop"
            ]

        if (
            link["template"] == self.templates["ext_multisite_underlay_setup"]
        ) or (
            link["template"]
            == self.templates["ext_evpn_multisite_overlay_setup"]
        ):
            link_payload["nvPairs"]["BGP_PASSWORD_ENABLE"] = link["profile"][
                "ebgp_password_enable"
            ]

            # Other parameters depend on "bgp_password_enable" flag.
            if link["profile"].get("ebgp_password_enable", True) is True:
                link_payload["nvPairs"][
                    "BGP_PASSWORD_INHERIT_FROM_MSD"
                ] = link["profile"]["inherit_from_msd"]
                if link["profile"].get("inherit_from_msd", True) is False:
                    link_payload["nvPairs"]["BGP_PASSWORD"] = link["profile"][
                        "ebgp_password"
                    ]
                    link_payload["nvPairs"]["BGP_AUTH_KEY_TYPE"] = link[
                        "profile"
                    ]["ebgp_auth_key_type"]
        if link["template"] == self.templates["ext_vxlan_mpls_underlay_setup"]:
            link_payload["nvPairs"]["MPLS_FABRIC"] = link["profile"][
                "mpls_fabric"
            ]
            link_payload["nvPairs"]["DCI_ROUTING_PROTO"] = link["profile"][
                "dci_routing_proto"
            ]
            link_payload["nvPairs"]["DCI_ROUTING_TAG"] = link["profile"][
                "dci_routing_tag"
            ]
            link_payload["nvPairs"]["PEER1_SR_MPLS_INDEX"] = link["profile"][
                "peer1_sr_mpls_index"
            ]
            link_payload["nvPairs"]["PEER2_SR_MPLS_INDEX"] = link["profile"][
                "peer2_sr_mpls_index"
            ]
            link_payload["nvPairs"]["GB_BLOCK_RANGE"] = link["profile"][
                "global_block_range"
            ]
            link_payload["nvPairs"]["OSPF_AREA_ID"] = link["profile"][
                "ospf_area_id"
            ]

    def dcnm_links_get_intra_fabric_links_payload(self, link, link_payload):

        """
        This routine builds the intra-fabric Links payload based on the information in the given
        link

        Parameters:
            link (dict): Link information
            link_payload (dict): Link payload to be updated

        Returns:
            link_payload (dict): Link payload information populated with appropriate data from playbook config
        """

        if (
            link["template"]
            != self.templates["int_pre_provision_intra_fabric_link"]
        ):
            link_payload["nvPairs"] = {}
            link_payload["nvPairs"]["ADMIN_STATE"] = link["profile"].get(
                "admin_state"
            )
            link_payload["nvPairs"]["MTU"] = link["profile"].get("mtu")
            link_payload["nvPairs"]["PEER1_DESC"] = link["profile"].get(
                "peer1_description"
            )
            link_payload["nvPairs"]["PEER2_DESC"] = link["profile"].get(
                "peer2_description"
            )

            if link["profile"].get("peer1_cmds") == []:
                link_payload["nvPairs"]["PEER1_CONF"] = ""
            else:
                link_payload["nvPairs"]["PEER1_CONF"] = "\n".join(
                    link["profile"].get("peer1_cmds")
                )

            if link["profile"].get("peer2_cmds") == []:
                link_payload["nvPairs"]["PEER2_CONF"] = ""
            else:
                link_payload["nvPairs"]["PEER2_CONF"] = "\n".join(
                    link["profile"].get("peer2_cmds")
                )

        if (
            (link["template"] == self.templates["int_intra_fabric_num_link"])
            or (
                link["template"]
                == self.templates["ios_xe_int_intra_fabric_num_link"]
            )
            or (
                link["template"]
                == self.templates["int_intra_vpc_peer_keep_alive_link"]
            )
        ):
            if (
                self.src_fabric_info["nvPairs"]
                .get("UNDERLAY_IS_V6", "false")
                .lower()
                == "false"
            ):
                link_payload["nvPairs"]["PEER1_IP"] = str(
                    ipaddress.ip_address(
                        link["profile"].get("peer1_ipv4_addr")
                    )
                )
                link_payload["nvPairs"]["PEER2_IP"] = str(
                    ipaddress.ip_address(
                        link["profile"].get("peer2_ipv4_addr")
                    )
                )
            else:
                if (
                    link["template"]
                    != self.templates["ios_xe_int_intra_fabric_num_link"]
                ):
                    link_payload["nvPairs"]["PEER1_V6IP"] = str(
                        ipaddress.ip_address(
                            link["profile"].get("peer1_ipv6_addr")
                        )
                    )
                    link_payload["nvPairs"]["PEER2_V6IP"] = str(
                        ipaddress.ip_address(
                            link["profile"].get("peer2_ipv6_addr")
                        )
                    )
                    if link["profile"].get("peer1_ipv4_addr", "") != "":
                        link_payload["nvPairs"]["PEER1_IP"] = str(
                            ipaddress.ip_address(
                                link["profile"].get("peer1_ipv4_addr")
                            )
                        )
                    else:
                        link_payload["nvPairs"]["PEER1_IP"] = ""

                    if link["profile"].get("peer2_ipv4_addr", "") != "":
                        link_payload["nvPairs"]["PEER2_IP"] = str(
                            ipaddress.ip_address(
                                link["profile"].get("peer2_ipv4_addr")
                            )
                        )
                    else:
                        link_payload["nvPairs"]["PEER2_IP"] = ""
                else:
                    link_payload["nvPairs"]["PEER1_IP"] = str(
                        ipaddress.ip_address(
                            link["profile"].get("peer1_ipv6_addr")
                        )
                    )
                    link_payload["nvPairs"]["PEER2_IP"] = str(
                        ipaddress.ip_address(
                            link["profile"].get("peer2_ipv6_addr")
                        )
                    )

        if (
            (link["template"] == self.templates["int_intra_fabric_num_link"])
            or (
                link["template"]
                == self.templates["int_intra_fabric_ipv6_link_local"]
            )
            or (
                link["template"]
                == self.templates["int_intra_fabric_unnum_link"]
            )
        ):
            link_payload["nvPairs"]["ENABLE_MACSEC"] = link["profile"].get(
                "enable_macsec"
            )

        if (
            link["template"]
            == self.templates["int_intra_vpc_peer_keep_alive_link"]
        ):
            link_payload["nvPairs"]["INTF_VRF"] = link["profile"].get(
                "intf_vrf"
            )

        if link["template"] == self.templates["int_intra_fabric_num_link"]:
            link_payload["nvPairs"]["PEER1_BFD_ECHO_DISABLE"] = link[
                "profile"
            ].get("peer1_bfd_echo_disable")
            link_payload["nvPairs"]["PEER2_BFD_ECHO_DISABLE"] = link[
                "profile"
            ].get("peer2_bfd_echo_disable")

    def dcnm_links_update_inter_fabric_links_information(
        self, wlink, hlink, cfg
    ):

        if (wlink.get("nvPairs", None) is None) or (
            (hlink.get("nvPairs", None) is None)
        ):
            return

        if (
            (
                wlink["templateName"]
                == self.templates["ext_multisite_underlay_setup"]
            )
            or (wlink["templateName"] == self.templates["ext_fabric_setup"])
            or (
                wlink["templateName"]
                == self.templates["ext_vxlan_mpls_underlay_setup"]
            )
        ):
            if cfg["profile"].get("ipv4_subnet", None) is None:
                wlink["nvPairs"]["IP_MASK"] = hlink["nvPairs"]["IP_MASK"]

            if cfg["profile"].get("mtu", None) is None:
                wlink["nvPairs"]["MTU"] = hlink["nvPairs"]["MTU"]

            if cfg["profile"].get("peer1_description", None) is None:
                wlink["nvPairs"]["PEER1_DESC"] = hlink["nvPairs"]["PEER1_DESC"]
            if cfg["profile"].get("peer2_description", None) is None:
                wlink["nvPairs"]["PEER2_DESC"] = hlink["nvPairs"]["PEER2_DESC"]

            # Note down that 'want' is updated with information from 'have'. We will need
            # this to properly merge 'want' and 'have' during diff_merge.
            if cfg["profile"].get("peer1_cmds", None) is None:
                wlink["nvPairs"]["PEER1_CONF"] = hlink["nvPairs"]["PEER1_CONF"]
                wlink["peer1_conf_defaulted"] = True
            if cfg["profile"].get("peer2_cmds", None) is None:
                wlink["nvPairs"]["PEER2_CONF"] = hlink["nvPairs"]["PEER2_CONF"]
                wlink["peer2_conf_defaulted"] = True
        elif (
            wlink["templateName"]
            != self.templates["ext_vxlan_mpls_overlay_setup"]
        ):
            if cfg["profile"].get("ipv4_addr", None) is None:
                wlink["nvPairs"]["SOURCE_IP"] = hlink["nvPairs"]["SOURCE_IP"]

            # This template does not include PEER1_CONF and PEER2_CONF parameters. Mark the following
            # so that dcnm_links_merge_want_and_have() can be generic for all cases
            wlink["peer1_conf_defaulted"] = True
            wlink["peer2_conf_defaulted"] = True

        if cfg["profile"].get("neighbor_ip", None) is None:
            wlink["nvPairs"]["NEIGHBOR_IP"] = hlink["nvPairs"]["NEIGHBOR_IP"]

        if (
            (
                wlink["templateName"]
                == self.templates["ext_multisite_underlay_setup"]
            )
            or (wlink["templateName"] == self.templates["ext_fabric_setup"])
            or (
                wlink["templateName"]
                == self.templates["ext_vxlan_mpls_overlay_setup"]
            )
        ):
            if cfg["profile"].get("src_asn", None) is None:
                wlink["nvPairs"]["asn"] = hlink["nvPairs"]["asn"]
            if cfg["profile"].get("dst_asn", None) is None:
                wlink["nvPairs"]["NEIGHBOR_ASN"] = hlink["nvPairs"][
                    "NEIGHBOR_ASN"
                ]

        if wlink["templateName"] == self.templates["ext_fabric_setup"]:
            if cfg["profile"].get("auto_deploy", None) is None:
                wlink["nvPairs"]["AUTO_VRF_LITE_FLAG"] = hlink["nvPairs"][
                    "AUTO_VRF_LITE_FLAG"
                ]
            wlink["nvPairs"]["VRF_LITE_JYTHON_TEMPLATE"] = hlink["nvPairs"][
                "VRF_LITE_JYTHON_TEMPLATE"
            ]

        if (
            wlink["templateName"]
            == self.templates["ext_multisite_underlay_setup"]
        ):
            if cfg["profile"].get("max_paths", None) is None:
                wlink["nvPairs"]["MAX_PATHS"] = hlink["nvPairs"]["MAX_PATHS"]
            if cfg["profile"].get("route_tag", None) is None:
                wlink["nvPairs"]["ROUTING_TAG"] = hlink["nvPairs"][
                    "ROUTING_TAG"
                ]
            if cfg["profile"].get("deploy_dci_tracking", None) is None:
                wlink["nvPairs"]["DEPLOY_DCI_TRACKING"] = hlink["nvPairs"][
                    "DEPLOY_DCI_TRACKING"
                ]

        if (
            wlink["templateName"]
            == self.templates["ext_evpn_multisite_overlay_setup"]
        ):
            if cfg["profile"].get("trm_enabled", None) is None:
                wlink["nvPairs"]["TRM_ENABLED"] = hlink["nvPairs"][
                    "TRM_ENABLED"
                ]
            if cfg["profile"].get("bgp_multihop", None) is None:
                wlink["nvPairs"]["BGP_MULTIHOP"] = hlink["nvPairs"][
                    "BGP_MULTIHOP"
                ]

        if (
            wlink["templateName"]
            == self.templates["ext_multisite_underlay_setup"]
        ) or (
            wlink["templateName"]
            == self.templates["ext_evpn_multisite_overlay_setup"]
        ):
            if cfg["profile"].get("ebgp_password_enable", None) is None:
                wlink["nvPairs"]["BGP_PASSWORD_ENABLE"] = hlink["nvPairs"][
                    "BGP_PASSWORD_ENABLE"
                ]

            # Other parameters depend on "bgp_password_enable" flag.
            if wlink["nvPairs"]["BGP_PASSWORD_ENABLE"] is True:
                if cfg["profile"].get("inherit_from_msd", None) is None:
                    wlink["nvPairs"]["BGP_PASSWORD_INHERIT_FROM_MSD"] = hlink[
                        "nvPairs"
                    ]["BGP_PASSWORD_INHERIT_FROM_MSD"]
                if wlink["nvPairs"]["BGP_PASSWORD_INHERIT_FROM_MSD"] is False:
                    if cfg["profile"].get("ebgp_password", None) is None:
                        wlink["nvPairs"]["BGP_PASSWORD"] = hlink["nvPairs"][
                            "BGP_PASSWORD"
                        ]
                    if cfg["profile"].get("ebgp_auth_key_type", None) is None:
                        wlink["nvPairs"]["BGP_AUTH_KEY_TYPE"] = hlink[
                            "nvPairs"
                        ]["BGP_AUTH_KEY_TYPE"]

    def dcnm_links_update_intra_fabric_links_information(
        self, wlink, hlink, cfg
    ):

        if (wlink.get("nvPairs", None) is None) or (
            (hlink.get("nvPairs", None) is None)
        ):
            return

        if cfg["profile"].get("admin_state", None) is None:
            wlink["nvPairs"]["ADMIN_STATE"] = hlink["nvPairs"]["ADMIN_STATE"]
        if cfg["profile"].get("mtu", None) is None:
            wlink["nvPairs"]["MTU"] = hlink["nvPairs"]["MTU"]
        if cfg["profile"].get("peer1_description", None) is None:
            wlink["nvPairs"]["PEER1_DESC"] = hlink["nvPairs"]["PEER1_DESC"]
        if cfg["profile"].get("peer2_description", None) is None:
            wlink["nvPairs"]["PEER2_DESC"] = hlink["nvPairs"]["PEER2_DESC"]

        # Note down that 'want' is updated with information from 'have'. We will need
        # this to properly merge 'want' and 'have' during diff_merge.
        if cfg["profile"].get("peer1_cmds", None) is None:
            wlink["nvPairs"]["PEER1_CONF"] = hlink["nvPairs"]["PEER1_CONF"]
            wlink["peer1_conf_defaulted"] = True
        if cfg["profile"].get("peer2_cmds", None) is None:
            wlink["nvPairs"]["PEER2_CONF"] = hlink["nvPairs"]["PEER2_CONF"]
            wlink["peer2_conf_defaulted"] = True

        if (
            (
                wlink["templateName"]
                == self.templates["int_intra_fabric_num_link"]
            )
            or (
                wlink["templateName"]
                == self.templates["ios_xe_int_intra_fabric_num_link"]
            )
            or (
                wlink["templateName"]
                == self.templates["int_intra_vpc_peer_keep_alive_link"]
            )
        ):
            if (
                self.src_fabric_info["nvPairs"]
                .get("UNDERLAY_IS_V6", "false")
                .lower()
                == "false"
            ):
                if cfg["profile"].get("peer1_ipv4_addr", None) is None:
                    wlink["nvPairs"]["PEER1_IP"] = hlink["nvPairs"]["PEER1_IP"]
                if cfg["profile"].get("peer2_ipv4_addr", None) is None:
                    wlink["nvPairs"]["PEER2_IP"] = hlink["nvPairs"]["PEER2_IP"]
            else:
                if (
                    wlink["templateName"]
                    != self.templates["ios_xe_int_intra_fabric_num_link"]
                ):
                    if cfg["profile"].get("peer1_ipv6_addr", None) is None:
                        wlink["nvPairs"]["PEER1_V6IP"] = hlink["nvPairs"][
                            "PEER1_V6IP"
                        ]
                    if cfg["profile"].get("peer2_ipv6_addr", None) is None:
                        wlink["nvPairs"]["PEER2_V6IP"] = hlink["nvPairs"][
                            "PEER2_V6IP"
                        ]
                else:
                    if cfg["profile"].get("peer1_ipv4_addr", None) is None:
                        wlink["nvPairs"]["PEER1_IP"] = hlink["nvPairs"][
                            "PEER1_IP"
                        ]
                    if cfg["profile"].get("peer2_ipv4_addr", None) is None:
                        wlink["nvPairs"]["PEER2_IP"] = hlink["nvPairs"][
                            "PEER2_IP"
                        ]

        if (
            (
                wlink["templateName"]
                == self.templates["int_intra_fabric_num_link"]
            )
            or (
                wlink["templateName"]
                == self.templates["int_intra_fabric_ipv6_link_local"]
            )
            or (
                wlink["templateName"]
                == self.templates["int_intra_fabric_unnum_link"]
            )
        ):
            if cfg["profile"].get("enable_macsec", None) is None:
                wlink["nvPairs"]["ENABLE_MACSEC"] = hlink["nvPairs"][
                    "ENABLE_MACSEC"
                ]

        if (
            wlink["templateName"]
            == self.templates["int_intra_vpc_peer_keep_alive_link"]
        ):
            if cfg["profile"].get("intf_vrf", None) is None:
                wlink["nvPairs"]["INTF_VRF"] = hlink["nvPairs"]["INTF_VRF"]

        if (
            wlink["templateName"]
            == self.templates["int_intra_fabric_num_link"]
        ):
            if cfg["profile"].get("peer1_bfd_echo_disable", None) is None:
                wlink["nvPairs"]["PEER1_BFD_ECHO_DISABLE"] = hlink["nvPairs"][
                    "PEER1_BFD_ECHO_DISABLE"
                ]
            if cfg["profile"].get("peer2_bfd_echo_disable", None) is None:
                wlink["nvPairs"]["PEER2_BFD_ECHO_DISABLE"] = hlink["nvPairs"][
                    "PEER2_BFD_ECHO_DISABLE"
                ]

    def dcnm_links_update_want(self):

        if self.module.params["state"] != "merged":
            return

        for want in self.want:

            match_links = [
                have
                for have in self.have
                if (
                    (have["sw1-info"]["fabric-name"] == want["sourceFabric"])
                    and (
                        have["sw2-info"]["fabric-name"]
                        == want["destinationFabric"]
                    )
                    and (
                        have["sw1-info"]["if-name"].lower()
                        == want["sourceInterface"].lower()
                    )
                    and (
                        have["sw2-info"]["if-name"].lower()
                        == want["destinationInterface"].lower()
                    )
                    and (
                        have["sw1-info"]["sw-serial-number"]
                        == want["sourceDevice"]
                    )
                    and (
                        have["sw2-info"]["sw-serial-number"]
                        == want["destinationDevice"]
                    )
                    and (
                        have.get("templateName", "")
                        == want.get("templateName", "")
                    )
                )
            ]

            match_cfg = [
                cfg
                for cfg in self.config
                if (
                    (self.fabric == want["sourceFabric"])
                    and (cfg["dst_fabric"] == want["destinationFabric"])
                    and (cfg["src_interface"] == want["sourceInterface"])
                    and (cfg["dst_interface"] == want["destinationInterface"])
                    and (
                        cfg["src_device"] in self.ip_sn
                        and self.ip_sn[cfg["src_device"]]
                        == want["sourceDevice"]
                    )
                    or (
                        cfg["src_device"] in self.hn_sn
                        and self.hn_sn[cfg["src_device"]]
                        == want["sourceDevice"]
                    )
                    and (
                        (
                            cfg["dst_device"] in self.ip_sn
                            and self.ip_sn[cfg["dst_device"]]
                            == want["destinationDevice"]
                        )
                        or (
                            cfg["dst_device"] in self.hn_sn
                            and self.hn_sn[cfg["dst_device"]]
                            == want["destinationDevice"]
                        )
                    )
                    and (cfg["template"] == want["templateName"])
                )
            ]

            if match_cfg == []:
                continue

            for mlink in match_links:
                if want["sourceFabric"] == want["destinationFabric"]:
                    self.dcnm_links_update_intra_fabric_links_information(
                        want, mlink, match_cfg[0]
                    )
                else:
                    self.dcnm_links_update_inter_fabric_links_information(
                        want, mlink, match_cfg[0]
                    )

    def dcnm_links_get_want(self):

        """
        This routine updates self.want with the payload information based on the playbook configuration.

        Parameters:
            None

        Returns:
            None
        """

        if [] is self.config:
            return

        if not self.links_info:
            return

        for link_elem in self.links_info:

            link_payload = self.dcnm_links_get_links_payload(link_elem)
            if link_payload not in self.want:
                self.want.append(link_payload)

    def dcnm_links_get_links_info_from_dcnm(self, link):

        """
        Routine to get existing Links information from DCNM which matches the given Link.

        Parameters:
            link  (dict): Link information

        Returns:
            resp["DATA"] (dict): Link informatikon obtained from the DCNM server if it exists
            [] otherwise
        """

        # link object is from self.want. These objets would have translated devices to serial numbers already.

        if (
            link["sourceDevice"] in self.ip_sn.values()
            and link["destinationDevice"] in self.ip_sn.values()
        ):
            path = self.paths[
                "LINKS_GET_BY_SWITCH_PAIR"
            ] + "?switch1Sn={0}&switch2Sn={1}".format(
                link["sourceDevice"], link["destinationDevice"]
            )
            path = path + "&switch1IfName={0}&switch2IfName={1}".format(
                link["sourceInterface"], link["destinationInterface"]
            )
        else:
            # If devices are not managable, the path should not include them
            path = self.paths["LINKS_GET_BY_SWITCH_PAIR"]
        resp = dcnm_send(self.module, "GET", path)

        if (
            resp
            and (resp["RETURN_CODE"] == 200)
            and (resp["MESSAGE"] == "OK")
            and resp["DATA"]
        ):
            # The response DATA will include all links between src_device and dst_device. We are interested
            # only in a LINK that matches the given 'link'. Try to match for the information in the response

            # resp["DATA"] will be a list if there is more than one link. It will be a dict otherwise

            if not isinstance(resp["DATA"], list):
                resp["DATA"] = [resp["DATA"]]

            match_link = [
                link_elem
                for link_elem in resp["DATA"]
                if (
                    (
                        link_elem["sw1-info"]["fabric-name"]
                        == link["sourceFabric"]
                    )
                    and (
                        link_elem["sw2-info"]["fabric-name"]
                        == link["destinationFabric"]
                    )
                    and (
                        link["sourceDevice"]
                        == link_elem["sw1-info"]["sw-serial-number"]
                    )
                    and (
                        (
                            link["destinationDevice"] in self.ip_sn.values()
                            and link["destinationDevice"]
                            == link_elem["sw2-info"]["sw-serial-number"]
                        )
                        or (
                            link["destinationSwitchName"]
                            + "-"
                            + link["destinationFabric"]
                            == link_elem["sw2-info"]["sw-serial-number"]
                        )
                    )
                    and (
                        link["sourceInterface"].lower()
                        == link_elem["sw1-info"]["if-name"].lower()
                    )
                    and (
                        link["destinationInterface"].lower()
                        == link_elem["sw2-info"]["if-name"].lower()
                    )
                )
            ]

            if match_link != []:
                return match_link[0]
            else:
                return []
        else:
            return []

    def dcnm_links_get_have(self):

        """
        Routine to get exisitng links information from DCNM that matches information in self.want.
        This routine updates self.have with all the Links that match the given playbook configuration

        Parameters:
            None

        Returns:
            None
        """

        if self.want == []:
            return

        for link in self.want:
            have = self.dcnm_links_get_links_info_from_dcnm(link)
            if (have != []) and (have not in self.have):
                self.have.append(have)

    def dcnm_links_compare_inter_fabric_link_params(self, wlink, hlink):

        """
        Routine to compare two links and update mismatch information.

        Parameters:
            wlink (dict): Requested link information
            hlink (dict): Existing link information
        Returns:
            DCNM_LINK_EXIST(str): - if given link is not found
            DCNM_LINK_MERGE(str): - if given link exists but there are changes in parameters
            mismatch_reasons(list): a list identifying objects that differed if required. [] otherwise
            hlink(dict): existing link if required, [] otherwise
        """

        mismatch_reasons = []

        if hlink["templateName"] != wlink["templateName"]:
            # We found a Link that matched all other key values, but the template is different. This means
            # the user is trying to change the template of an existing link. So go ahead and merge the same
            mismatch_reasons.append(
                {
                    "TEMPLATE_MISMATCH": [
                        wlink["templateName"],
                        hlink["templateName"],
                    ]
                }
            )
            return "DCNM_LINK_MERGE", mismatch_reasons, hlink

        if (wlink.get("nvPairs", None) is None) or (
            (hlink.get("nvPairs", None) is None)
        ):
            return "DCNM_LINK_EXIST", [], []

        if (
            (
                wlink["templateName"]
                == self.templates["ext_multisite_underlay_setup"]
            )
            or (wlink["templateName"] == self.templates["ext_fabric_setup"])
            or (
                wlink["templateName"]
                == self.templates["ext_vxlan_mpls_underlay_setup"]
            )
        ):
            if (
                self.dcnm_links_compare_ip_addresses(
                    wlink["nvPairs"]["IP_MASK"], hlink["nvPairs"]["IP_MASK"]
                )
                is False
            ):
                mismatch_reasons.append(
                    {
                        "IP_MASK_MISMATCH": [
                            wlink["nvPairs"]["IP_MASK"],
                            hlink["nvPairs"]["IP_MASK"],
                        ]
                    }
                )
            if (
                str(wlink["nvPairs"]["MTU"]).lower()
                != str(hlink["nvPairs"]["MTU"]).lower()
            ):
                mismatch_reasons.append(
                    {
                        "MTU_MISMATCH": [
                            str(wlink["nvPairs"]["MTU"]).lower(),
                            str(hlink["nvPairs"]["MTU"]).lower(),
                        ]
                    }
                )
            if (
                wlink["nvPairs"]["PEER1_DESC"]
                != hlink["nvPairs"]["PEER1_DESC"]
            ):
                mismatch_reasons.append(
                    {
                        "PEER1_DESC_MISMATCH": [
                            wlink["nvPairs"]["PEER1_DESC"],
                            hlink["nvPairs"]["PEER1_DESC"],
                        ]
                    }
                )
            if (
                wlink["nvPairs"]["PEER2_DESC"]
                != hlink["nvPairs"]["PEER2_DESC"]
            ):
                mismatch_reasons.append(
                    {
                        "PEER2_DESC_MISMATCH": [
                            wlink["nvPairs"]["PEER2_DESC"],
                            hlink["nvPairs"]["PEER2_DESC"],
                        ]
                    }
                )

            if (
                wlink["nvPairs"]["PEER1_CONF"]
                != hlink["nvPairs"]["PEER1_CONF"]
            ):
                mismatch_reasons.append(
                    {
                        "PEER1_CONF_MISMATCH": [
                            wlink["nvPairs"]["PEER1_CONF"],
                            hlink["nvPairs"]["PEER1_CONF"],
                        ]
                    }
                )
            if (
                wlink["nvPairs"]["PEER2_CONF"]
                != hlink["nvPairs"]["PEER2_CONF"]
            ):
                mismatch_reasons.append(
                    {
                        "PEER2_CONF_MISMATCH": [
                            wlink["nvPairs"]["PEER2_CONF"],
                            hlink["nvPairs"]["PEER2_CONF"],
                        ]
                    }
                )
        elif (
            wlink["templateName"]
            != self.templates["ext_vxlan_mpls_overlay_setup"]
        ):
            if (
                self.dcnm_links_compare_ip_addresses(
                    wlink["nvPairs"]["SOURCE_IP"],
                    hlink["nvPairs"]["SOURCE_IP"],
                )
                is False
            ):
                mismatch_reasons.append(
                    {
                        "SOURCE_IP_MISMATCH": [
                            wlink["nvPairs"]["SOURCE_IP"],
                            hlink["nvPairs"]["SOURCE_IP"],
                        ]
                    }
                )

        if (
            self.dcnm_links_compare_ip_addresses(
                wlink["nvPairs"]["NEIGHBOR_IP"],
                hlink["nvPairs"]["NEIGHBOR_IP"],
            )
            is False
        ):
            mismatch_reasons.append(
                {
                    "NEIGHBOR_IP_MISMATCH": [
                        wlink["nvPairs"]["NEIGHBOR_IP"],
                        hlink["nvPairs"]["NEIGHBOR_IP"],
                    ]
                }
            )
        if (
            (
                wlink["templateName"]
                == self.templates["ext_multisite_underlay_setup"]
            )
            or (wlink["templateName"] == self.templates["ext_fabric_setup"])
            or (
                wlink["templateName"]
                == self.templates["ext_vxlan_mpls_overlay_setup"]
            )
        ):
            if (
                str(wlink["nvPairs"]["asn"]).lower()
                != str(hlink["nvPairs"]["asn"]).lower()
            ):
                mismatch_reasons.append(
                    {
                        "ASN_MISMATCH": [
                            str(wlink["nvPairs"]["asn"]).lower(),
                            str(hlink["nvPairs"]["asn"]).lower(),
                        ]
                    }
                )
            if (
                str(wlink["nvPairs"]["NEIGHBOR_ASN"]).lower()
                != str(hlink["nvPairs"]["NEIGHBOR_ASN"]).lower()
            ):
                mismatch_reasons.append(
                    {
                        "NEIGHBOR_ASN_MISMATCH": [
                            str(wlink["nvPairs"]["NEIGHBOR_ASN"]).lower(),
                            str(hlink["nvPairs"]["NEIGHBOR_ASN"]).lower(),
                        ]
                    }
                )

        if wlink["templateName"] == self.templates["ext_fabric_setup"]:

            if (
                str(wlink["nvPairs"]["AUTO_VRF_LITE_FLAG"]).lower()
                != str(hlink["nvPairs"]["AUTO_VRF_LITE_FLAG"]).lower()
            ):
                mismatch_reasons.append(
                    {
                        "AUTO_VRF_LITE_FLAG_MISMATCH": [
                            str(
                                wlink["nvPairs"]["AUTO_VRF_LITE_FLAG"]
                            ).lower(),
                            str(
                                hlink["nvPairs"]["AUTO_VRF_LITE_FLAG"]
                            ).lower(),
                        ]
                    }
                )
            if (
                wlink["nvPairs"]["VRF_LITE_JYTHON_TEMPLATE"]
                != hlink["nvPairs"]["VRF_LITE_JYTHON_TEMPLATE"]
            ):
                mismatch_reasons.append(
                    {
                        "VRF_LITE_JYTHON_TEMPLATE_MISMATCH": [
                            wlink["nvPairs"]["VRF_LITE_JYTHON_TEMPLATE"],
                            hlink["nvPairs"]["VRF_LITE_JYTHON_TEMPLATE"],
                        ]
                    }
                )

        if (
            wlink["templateName"]
            == self.templates["ext_multisite_underlay_setup"]
        ):

            if (
                str(wlink["nvPairs"]["MAX_PATHS"]).lower()
                != str(hlink["nvPairs"]["MAX_PATHS"]).lower()
            ):
                mismatch_reasons.append(
                    {
                        "MAX_PATHS_MISMATCH": [
                            str(wlink["nvPairs"]["MAX_PATHS"]).lower(),
                            str(hlink["nvPairs"]["MAX_PATHS"]).lower(),
                        ]
                    }
                )
            if (
                str(wlink["nvPairs"]["ROUTING_TAG"]).lower()
                != str(hlink["nvPairs"]["ROUTING_TAG"]).lower()
            ):
                mismatch_reasons.append(
                    {
                        "ROUTING_TAG_MISMATCH": [
                            str(wlink["nvPairs"]["ROUTING_TAG"]).lower(),
                            str(hlink["nvPairs"]["ROUTING_TAG"]).lower(),
                        ]
                    }
                )
            if (
                str(wlink["nvPairs"]["DEPLOY_DCI_TRACKING"]).lower()
                != str(hlink["nvPairs"]["DEPLOY_DCI_TRACKING"]).lower()
            ):
                mismatch_reasons.append(
                    {
                        "DEPLOY_DCI_TRACKING_MISMATCH": [
                            str(
                                wlink["nvPairs"]["DEPLOY_DCI_TRACKING"]
                            ).lower(),
                            str(
                                hlink["nvPairs"]["DEPLOY_DCI_TRACKING"]
                            ).lower(),
                        ]
                    }
                )

        if (
            wlink["templateName"]
            == self.templates["ext_evpn_multisite_overlay_setup"]
        ):

            if (
                str(wlink["nvPairs"]["TRM_ENABLED"]).lower()
                != str(hlink["nvPairs"]["TRM_ENABLED"]).lower()
            ):
                mismatch_reasons.append(
                    {
                        "TRM_ENABLED_MISMATCH": [
                            str(wlink["nvPairs"]["TRM_ENABLED"]).lower(),
                            str(hlink["nvPairs"]["TRM_ENABLED"]).lower(),
                        ]
                    }
                )
            if (
                str(wlink["nvPairs"]["BGP_MULTIHOP"]).lower()
                != str(hlink["nvPairs"]["BGP_MULTIHOP"]).lower()
            ):
                mismatch_reasons.append(
                    {
                        "BGP_MULTIHOP_MISMATCH": [
                            str(wlink["nvPairs"]["BGP_MULTIHOP"]).lower(),
                            str(hlink["nvPairs"]["BGP_MULTIHOP"]).lower(),
                        ]
                    }
                )

        if (
            wlink["templateName"]
            == self.templates["ext_multisite_underlay_setup"]
        ) or (
            wlink["templateName"]
            == self.templates["ext_evpn_multisite_overlay_setup"]
        ):

            if (
                str(wlink["nvPairs"]["BGP_PASSWORD_ENABLE"]).lower()
                != str(hlink["nvPairs"]["BGP_PASSWORD_ENABLE"]).lower()
            ):
                mismatch_reasons.append(
                    {
                        "BGP_PASSWORD_ENABLE_MISMATCH": [
                            str(
                                wlink["nvPairs"]["BGP_PASSWORD_ENABLE"]
                            ).lower(),
                            str(
                                hlink["nvPairs"]["BGP_PASSWORD_ENABLE"]
                            ).lower(),
                        ]
                    }
                )
            # Other parameters depend on "bgp_password_enable" flag.
            if wlink["nvPairs"]["BGP_PASSWORD_ENABLE"] is True:

                if (
                    str(
                        wlink["nvPairs"]["BGP_PASSWORD_INHERIT_FROM_MSD"]
                    ).lower()
                    != str(
                        hlink["nvPairs"]["BGP_PASSWORD_INHERIT_FROM_MSD"]
                    ).lower()
                ):
                    mismatch_reasons.append(
                        {
                            "BGP_PASSWORD_INHERIT_FROM_MSD_MISMATCH": [
                                str(
                                    wlink["nvPairs"][
                                        "BGP_PASSWORD_INHERIT_FROM_MSD"
                                    ]
                                ).lower(),
                                str(
                                    hlink["nvPairs"][
                                        "BGP_PASSWORD_INHERIT_FROM_MSD"
                                    ]
                                ).lower(),
                            ]
                        }
                    )
                if wlink["nvPairs"]["BGP_PASSWORD_INHERIT_FROM_MSD"] is False:

                    if wlink["nvPairs"]["BGP_PASSWORD"] != hlink[
                        "nvPairs"
                    ].get("BGP_PASSWORD", ""):
                        mismatch_reasons.append(
                            {
                                "BGP_PASSWORD_MISMATCH": [
                                    wlink["nvPairs"]["BGP_PASSWORD"],
                                    hlink["nvPairs"].get("BGP_PASSWORD", ""),
                                ]
                            }
                        )
                    if (
                        str(wlink["nvPairs"]["BGP_AUTH_KEY_TYPE"]).lower()
                        != str(
                            hlink["nvPairs"].get("BGP_AUTH_KEY_TYPE", "")
                        ).lower()
                    ):
                        mismatch_reasons.append(
                            {
                                "BGP_AUTH_KEY_TYPE_MISMATCH": [
                                    str(
                                        wlink["nvPairs"]["BGP_AUTH_KEY_TYPE"]
                                    ).lower(),
                                    str(
                                        hlink["nvPairs"].get(
                                            "BGP_AUTH_KEY_TYPE", ""
                                        )
                                    ).lower(),
                                ]
                            }
                        )
        if (
            wlink["templateName"]
            == self.templates["ext_vxlan_mpls_underlay_setup"]
        ):
            mpls_underlay_spec_nvpairs = [
                "MPLS_FABRIC",
                "DCI_ROUTING_PROTO",
                "DCI_ROUTING_TAG",
                "PEER1_SR_MPLS_INDEX",
                "PEER2_SR_MPLS_INDEX",
                "GB_BLOCK_RANGE",
                "OSPF_AREA_ID",
            ]
            for nv_pair in mpls_underlay_spec_nvpairs:
                if (
                    str(wlink["nvPairs"][nv_pair]).lower()
                    != str(hlink["nvPairs"][nv_pair]).lower()
                ):
                    mismatch_reasons.append(
                        {
                            f"{nv_pair}_MISMATCH": [
                                str(wlink["nvPairs"][nv_pair]).lower(),
                                str(hlink["nvPairs"][nv_pair]).lower(),
                            ]
                        }
                    )

        if mismatch_reasons != []:
            return "DCNM_LINK_MERGE", mismatch_reasons, hlink
        else:
            return "DCNM_LINK_EXIST", [], []

    def dcnm_links_compare_intra_fabric_link_params(self, wlink, hlink):

        """
        Routine to compare two links and update mismatch information.

        Parameters:
            wlink (dict): Requested link information
            hlink (dict): Existing link information
        Returns:
            DCNM_LINK_EXIST(str): - if given link is not found
            DCNM_LINK_MERGE(str): - if given link exists but there are changes in parameters
            mismatch_reasons(list): a list identifying objects that differed if required. [] otherwise
            hlink(dict): existing link if required, [] otherwise
        """

        mismatch_reasons = []

        if hlink["templateName"] != wlink["templateName"]:
            # We found a Link that matched all other key values, but the template is different. This means
            # the user is trying to change the template of an existing link. So go ahead and merge the same
            mismatch_reasons.append(
                {
                    "TEMPLATE_MISMATCH": [
                        wlink["templateName"],
                        hlink["templateName"],
                    ]
                }
            )
            return "DCNM_LINK_MERGE", mismatch_reasons, hlink

        if (wlink.get("nvPairs", None) is None) or (
            (hlink.get("nvPairs", None) is None)
        ):
            return "DCNM_LINK_EXIST", [], []

        # Compare common info for all templates first
        if (
            str(wlink["nvPairs"]["ADMIN_STATE"]).lower()
            != str(hlink["nvPairs"]["ADMIN_STATE"]).lower()
        ):
            mismatch_reasons.append(
                {
                    "ADMIN_STATE_MISMATCH": [
                        str(wlink["nvPairs"]["ADMIN_STATE"]).lower(),
                        str(hlink["nvPairs"]["ADMIN_STATE"]).lower(),
                    ]
                }
            )
        if (
            str(wlink["nvPairs"]["MTU"]).lower()
            != str(hlink["nvPairs"]["MTU"]).lower()
        ):
            mismatch_reasons.append(
                {
                    "MTU_MISMATCH": [
                        wlink["nvPairs"]["MTU"],
                        hlink["nvPairs"]["MTU"],
                    ]
                }
            )
        if wlink["nvPairs"]["PEER1_DESC"] != hlink["nvPairs"]["PEER1_DESC"]:
            mismatch_reasons.append(
                {
                    "PEER1_DESC_MISMATCH": [
                        wlink["nvPairs"]["PEER1_DESC"],
                        hlink["nvPairs"]["PEER1_DESC"],
                    ]
                }
            )
        if wlink["nvPairs"]["PEER2_DESC"] != hlink["nvPairs"]["PEER2_DESC"]:
            mismatch_reasons.append(
                {
                    "PEER2_DESC_MISMATCH": [
                        wlink["nvPairs"]["PEER2_DESC"],
                        hlink["nvPairs"]["PEER2_DESC"],
                    ]
                }
            )
        if wlink["nvPairs"]["PEER1_CONF"] != hlink["nvPairs"]["PEER1_CONF"]:
            mismatch_reasons.append(
                {
                    "PEER1_CONF_MISMATCH": [
                        wlink["nvPairs"]["PEER1_CONF"],
                        hlink["nvPairs"]["PEER1_CONF"],
                    ]
                }
            )
        if wlink["nvPairs"]["PEER2_CONF"] != hlink["nvPairs"]["PEER2_CONF"]:
            mismatch_reasons.append(
                {
                    "PEER2_CONF_MISMATCH": [
                        wlink["nvPairs"]["PEER2_CONF"],
                        hlink["nvPairs"]["PEER2_CONF"],
                    ]
                }
            )

        if (
            (
                wlink["templateName"]
                == self.templates["int_intra_fabric_num_link"]
            )
            or (
                wlink["templateName"]
                == self.templates["ios_xe_int_intra_fabric_num_link"]
            )
            or (
                wlink["templateName"]
                == self.templates["int_intra_vpc_peer_keep_alive_link"]
            )
        ):
            if (
                self.src_fabric_info["nvPairs"]
                .get("UNDERLAY_IS_V6", "false")
                .lower()
                == "false"
            ):
                if (
                    self.dcnm_links_compare_ip_addresses(
                        wlink["nvPairs"]["PEER1_IP"],
                        hlink["nvPairs"].get("PEER1_IP"),
                    )
                    is False
                ):
                    mismatch_reasons.append(
                        {
                            "PEER1_IP_MISMATCH": [
                                wlink["nvPairs"]["PEER1_IP"],
                                hlink["nvPairs"]["PEER1_IP"],
                            ]
                        }
                    )
                if (
                    self.dcnm_links_compare_ip_addresses(
                        wlink["nvPairs"]["PEER2_IP"],
                        hlink["nvPairs"].get("PEER2_IP"),
                    )
                    is False
                ):
                    mismatch_reasons.append(
                        {
                            "PEER2_IP_MISMATCH": [
                                wlink["nvPairs"]["PEER2_IP"],
                                hlink["nvPairs"]["PEER2_IP"],
                            ]
                        }
                    )
            else:
                if (
                    wlink["templateName"]
                    != self.templates["ios_xe_int_intra_fabric_num_link"]
                ):
                    if (
                        self.dcnm_links_compare_ip_addresses(
                            wlink["nvPairs"]["PEER1_V6IP"],
                            hlink["nvPairs"].get("PEER1_V6IP"),
                        )
                        is False
                    ):
                        mismatch_reasons.append(
                            {
                                "PEER1_IPV6_MISMATCH": [
                                    wlink["nvPairs"]["PEER1_V6IP"],
                                    hlink["nvPairs"]["PEER1_V6IP"],
                                ]
                            }
                        )
                    if (
                        self.dcnm_links_compare_ip_addresses(
                            wlink["nvPairs"]["PEER2_V6IP"],
                            hlink["nvPairs"].get("PEER2_V6IP"),
                        )
                        is False
                    ):
                        mismatch_reasons.append(
                            {
                                "PEER2_IPV6_MISMATCH": [
                                    wlink["nvPairs"]["PEER2_V6IP"],
                                    hlink["nvPairs"]["PEER2_V6IP"],
                                ]
                            }
                        )
                else:
                    if (
                        self.dcnm_links_compare_ip_addresses(
                            wlink["nvPairs"]["PEER1_IP"],
                            hlink["nvPairs"].get("PEER1_IP"),
                        )
                        is False
                    ):
                        mismatch_reasons.append(
                            {
                                "PEER1_IP_MISMATCH": [
                                    wlink["nvPairs"]["PEER1_IP"],
                                    hlink["nvPairs"]["PEER1_IP"],
                                ]
                            }
                        )
                    if (
                        self.dcnm_links_compare_ip_addresses(
                            wlink["nvPairs"]["PEER2_IP"],
                            hlink["nvPairs"].get("PEER2_IP"),
                        )
                        is False
                    ):
                        mismatch_reasons.append(
                            {
                                "PEER2_IP_MISMATCH": [
                                    wlink["nvPairs"]["PEER2_IP"],
                                    hlink["nvPairs"]["PEER2_IP"],
                                ]
                            }
                        )

        if (
            (
                wlink["templateName"]
                == self.templates["int_intra_fabric_num_link"]
            )
            or (
                wlink["templateName"]
                == self.templates["int_intra_fabric_ipv6_link_local"]
            )
            or (
                wlink["templateName"]
                == self.templates["int_intra_fabric_unnum_link"]
            )
        ):
            if (
                str(wlink["nvPairs"]["ENABLE_MACSEC"]).lower()
                != str(hlink["nvPairs"].get("ENABLE_MACSEC")).lower()
            ):
                mismatch_reasons.append(
                    {
                        "ENABLE_MACSEC_MISMATCH": [
                            str(wlink["nvPairs"]["ENABLE_MACSEC"]).lower(),
                            str(hlink["nvPairs"]["ENABLE_MACSEC"]).lower(),
                        ]
                    }
                )

        if (
            wlink["templateName"]
            == self.templates["int_intra_vpc_peer_keep_alive_link"]
        ):

            if wlink["nvPairs"]["INTF_VRF"] != hlink["nvPairs"].get(
                "INTF_VRF"
            ):
                mismatch_reasons.append(
                    {
                        "INTF_VRF_MISMATCH": [
                            wlink["nvPairs"]["INTF_VRF"],
                            hlink["nvPairs"]["INTF_VRF"],
                        ]
                    }
                )

        if (
            wlink["templateName"]
            == self.templates["int_intra_fabric_num_link"]
        ):
            if (
                str(wlink["nvPairs"]["PEER1_BFD_ECHO_DISABLE"]).lower()
                != str(hlink["nvPairs"].get("PEER1_BFD_ECHO_DISABLE")).lower()
            ):
                mismatch_reasons.append(
                    {
                        "PEER1_BFD_ECHO_DISABLE_MISMATCH": [
                            str(
                                wlink["nvPairs"]["PEER1_BFD_ECHO_DISABLE"]
                            ).lower(),
                            str(
                                hlink["nvPairs"]["PEER1_BFD_ECHO_DISABLE"]
                            ).lower(),
                        ]
                    }
                )
            if (
                str(wlink["nvPairs"]["PEER2_BFD_ECHO_DISABLE"]).lower()
                != str(hlink["nvPairs"].get("PEER2_BFD_ECHO_DISABLE")).lower()
            ):
                mismatch_reasons.append(
                    {
                        "PEER2_BFD_ECHO_DISABLE_MISMATCH": [
                            str(
                                wlink["nvPairs"]["PEER2_BFD_ECHO_DISABLE"]
                            ).lower(),
                            str(
                                hlink["nvPairs"]["PEER2_BFD_ECHO_DISABLE"]
                            ).lower(),
                        ]
                    }
                )

        if mismatch_reasons != []:
            return "DCNM_LINK_MERGE", mismatch_reasons, hlink
        else:
            return "DCNM_LINK_EXIST", [], []

    def dcnm_links_compare_Links(self, want):

        """
        This routine finds a link in self.have that matches the given link information. If the given
        link already exist then the link is not added to the links list to be created on
        DCNM server in the current run. The given link is added to the list of Links to be
        created otherwise

        Parameters:
            link : Link to be matched from self.have

        Returns:
            DCNM_LINK_CREATE (str): - if a new link is to be created
            return value of  dcnm_links_compare_intra_fabric_link_params or dcnm_links_compare_inter_fabric_link_params
        """

        match_have = [
            have
            for have in self.have
            if (
                (
                    have.get("templateName") is not None
                )  # if templateName is empty, link is autodicovered, consider link is new
                and (have["sw1-info"]["fabric-name"] == want["sourceFabric"])
                and (
                    have["sw2-info"]["fabric-name"]
                    == want["destinationFabric"]
                )
                and (
                    have["sw1-info"]["if-name"].lower()
                    == want["sourceInterface"].lower()
                )
                and (
                    have["sw2-info"]["if-name"].lower()
                    == want["destinationInterface"].lower()
                )
                and (
                    have["sw1-info"]["sw-serial-number"]
                    == want["sourceDevice"]
                )
                and (
                    have["sw2-info"]["sw-serial-number"]
                    == want["destinationDevice"]
                    or have["sw2-info"]["sw-serial-number"]
                    == want["destinationSwitchName"]
                    + "-"
                    + want["destinationFabric"]
                )
            )
        ]

        for mlink in match_have:
            if want["sourceFabric"] == want["destinationFabric"]:
                return self.dcnm_links_compare_intra_fabric_link_params(
                    want, mlink
                )
            else:
                return self.dcnm_links_compare_inter_fabric_link_params(
                    want, mlink
                )

        return "DCNM_LINK_CREATE", [], []

    def dcnm_links_merge_want_and_have(self, want, have):

        if (want.get("nvPairs", None) is None) or (
            (have.get("nvPairs", None) is None)
        ):
            return

        if want.get("peer1_conf_defaulted", False) is False:

            # In the current run, if want["nvPairs"]["PEER1_CONF"] is not included
            # then it would have been updated with values from 'have' in the function
            # dcnm_links_update_want(). So no need to do the merge here.
            if want["nvPairs"].get("PEER1_CONF", "") == "":
                want["nvPairs"]["PEER1_CONF"] = have["nvPairs"]["PEER1_CONF"]
            elif have["nvPairs"].get("PEER1_CONF", "") == "":
                # Nothing to merge. Leave want as it is
                pass
            else:
                want["nvPairs"]["PEER1_CONF"] = (
                    have["nvPairs"]["PEER1_CONF"]
                    + "\n"
                    + want["nvPairs"]["PEER1_CONF"]
                )
        else:
            # Remove the "peer1_conf_defaulted" from want
            want.pop("peer1_conf_defaulted")

        if want.get("peer2_conf_defaulted", False) is False:

            # In the current run, if want["nvPairs"]["PEER2_CONF"] is not included
            # then it would have been updated with values from 'have' in the function
            # dcnm_links_update_want(). So no need to do the merge here.
            if want["nvPairs"].get("PEER2_CONF", "") == "":
                want["nvPairs"]["PEER2_CONF"] = have["nvPairs"]["PEER2_CONF"]
            elif have["nvPairs"].get("PEER2_CONF", "") == "":
                # Nothing to merge. Leave want as it is
                pass
            else:
                want["nvPairs"]["PEER2_CONF"] = (
                    have["nvPairs"]["PEER2_CONF"]
                    + "\n"
                    + want["nvPairs"]["PEER2_CONF"]
                )
        else:
            # Remove the "peer2_conf_defaulted" from want
            want.pop("peer2_conf_defaulted")

    def dcnm_links_update_diff_deploy(self, fabric, device):

        if self.diff_deploy.get(fabric, "") == "":
            self.diff_deploy[fabric] = []

        if device != "" and device not in self.diff_deploy[fabric]:
            self.diff_deploy[fabric].append(device)

    def dcnm_links_get_diff_merge(self):

        """
        Routine to populate a list of payload information in self.diff_create to create/update Links.

        Parameters:
            None

        Returns:
            None
        """

        if not self.want:
            return
        for link in self.want:

            rc, reasons, have = self.dcnm_links_compare_Links(link)

            if rc == "DCNM_LINK_CREATE":
                # Link does not exists, create a new one.
                if link not in self.diff_create:
                    self.changed_dict[0]["merged"].append(link)
                    self.diff_create.append(link)
            if rc == "DCNM_LINK_MERGE":
                # Link already exists, and needs an update
                if link not in self.diff_modify:
                    # Note down the Link UUID in link. We will need this to update the link
                    link["link-uuid"] = have["link-uuid"]
                    self.changed_dict[0]["modified"].append(link)
                    self.changed_dict[0]["debugs"].append({"REASONS": reasons})
                    # Fields like CONF which are a list of commands should be handled differently in this case.
                    # For existing links, we will have to merge the current list of commands with already existing
                    # ones in have. For replace, no need to merge them. They must be replaced with what is given.
                    if self.module.params["state"] == "merged":
                        # Check if the templates are same. If not dont try to merge want and have, because
                        # the parameters in want and have will be different. Since template has changed, go ahead
                        # and push MODIFY request with the new payload

                        if link["templateName"] == have["templateName"]:
                            self.dcnm_links_merge_want_and_have(link, have)
                    self.diff_modify.append(link)

            # Check if "deploy" flag is True. If True, deploy the changes.
            # NOTE: There is no Link level deploy functionality. Deploy always happens at switch level.
            #       If "deploy" flag is set to "true", then all pending configurations on the source and
            #       destination devices will be deployed.
            if self.deploy:

                if (
                    self.fabric not in self.monitoring
                    and link["sourceDevice"] in self.managable.values()
                ):
                    self.dcnm_links_update_diff_deploy(
                        self.fabric, link["sourceDevice"]
                    )
                else:
                    self.dcnm_links_update_diff_deploy(self.fabric, "")

                # If source swithces are not manageable, then do not deploy anything on destination fabric to
                # avoid inconsitencies.
                if link["sourceDevice"] in self.managable.values():
                    if (
                        link["destinationFabric"] not in self.monitoring
                        and link["destinationDevice"]
                        in self.managable.values()
                    ):
                        self.dcnm_links_update_diff_deploy(
                            link["destinationFabric"],
                            link["destinationDevice"],
                        )
                    else:
                        self.dcnm_links_update_diff_deploy(
                            link["destinationFabric"], ""
                        )
                else:
                    self.dcnm_links_update_diff_deploy(
                        link["destinationFabric"], ""
                    )

        if self.diff_deploy != {}:
            self.changed_dict[0]["deploy"].append(
                copy.deepcopy(self.diff_deploy)
            )

    def dcnm_links_get_diff_deleted(self):

        """
        Routine to get a list of payload information that will be used to delete Links.
        This routine updates self.diff_delete with payloads that are used to delete Links
        from the server.

        Parameters:
            None

        Returns:
            None
        """

        match_links = []
        for link in self.links_info:

            match_links = [
                have
                for have in self.have
                if (
                    (have["sw1-info"]["fabric-name"] == self.fabric)
                    and (have["sw2-info"]["fabric-name"] == link["dst_fabric"])
                    and (
                        have["sw1-info"]["if-name"].lower()
                        == link["src_interface"].lower()
                    )
                    and (
                        have["sw2-info"]["if-name"].lower()
                        == link["dst_interface"].lower()
                    )
                    and (
                        link["src_device"] in self.ip_sn
                        and have["sw1-info"]["sw-serial-number"]
                        == self.ip_sn.get(link["src_device"], "")
                        or have["sw1-info"]["sw-serial-number"]
                        == self.hn_sn.get(link["src_device"], "")
                    )
                    and (
                        link["dst_device"] in self.ip_sn
                        and have["sw2-info"]["sw-serial-number"]
                        == self.ip_sn.get(link["dst_device"], "")
                        or have["sw2-info"]["sw-serial-number"]
                        == self.hn_sn.get(link["dst_device"], "")
                    )
                )
            ]

            for mlink in match_links:
                self.diff_delete.append(mlink["link-uuid"])
                self.changed_dict[0]["deleted"].append(
                    {
                        "src_fabric": self.fabric,
                        "dst_fabric": link["dst_fabric"],
                        "src_interface": link["src_interface"],
                        "dst_interface": link["dst_interface"],
                        "src_device": link["src_device"],
                        "dst_device": link["dst_device"],
                        "UUID": mlink["link-uuid"],
                    }
                )

                if self.deploy:
                    if (
                        self.fabric not in self.monitoring
                        and link["src_device"] in self.managable
                    ):
                        self.dcnm_links_update_diff_deploy(
                            self.fabric, self.ip_sn[link["src_device"]]
                        )
                    else:
                        self.dcnm_links_update_diff_deploy(self.fabric, "")

                    if (
                        link["dst_fabric"] not in self.monitoring
                        and link["dst_device"] in self.managable
                    ):
                        self.dcnm_links_update_diff_deploy(
                            link["dst_fabric"], self.ip_sn[link["dst_device"]]
                        )
                    else:
                        self.dcnm_links_update_diff_deploy(
                            link["dst_fabric"], ""
                        )

        if self.diff_deploy != {}:
            self.changed_dict[0]["deploy"].append(
                copy.deepcopy(self.diff_deploy)
            )

    def dcnm_links_get_diff_query(self):

        """
        Routine to get links information based on the playbook configuration.
        This routine updates self.result with Links requested for in the playbook if they exist on
        the DCNM server.

        Parameters:
            None

        Returns:
            None
        """

        # 'src_fabric' is always given. Use that to get all links and then filter based on arguments
        # included in playbook

        path = self.paths["LINKS_GET_BY_FABRIC"].format(self.fabric)

        resp = dcnm_send(self.module, "GET", path)

        if resp and resp["RETURN_CODE"] == 200 and resp["DATA"]:
            if self.links_info == []:
                # Get all the links based on the 'path' computed above.
                self.result["response"].extend(resp["DATA"])

            for link in self.links_info:

                match_query = []

                match_query = [
                    rlink
                    for rlink in resp["DATA"]
                    if (
                        (
                            (link["dst_fabric"] == "")
                            or (
                                rlink["sw2-info"]["fabric-name"]
                                == link["dst_fabric"]
                            )
                        )
                        and (
                            (link["src_interface"] == "")
                            or (
                                rlink["sw1-info"]["if-name"].lower()
                                == link["src_interface"].lower()
                            )
                        )
                        and (
                            (link["dst_interface"] == "")
                            or (
                                rlink["sw2-info"]["if-name"].lower()
                                == link["dst_interface"].lower()
                            )
                        )
                        and (
                            (link["src_device"] == "")
                            or (
                                link["src_device"] in self.ip_sn
                                and rlink["sw1-info"]["sw-serial-number"]
                                == self.ip_sn[link["src_device"]]
                            )
                            or (
                                link["src_device"] in self.hn_sn
                                and rlink["sw1-info"]["sw-serial-number"]
                                == self.hn_sn[link["src_device"]]
                            )
                        )
                        and (
                            (link["dst_device"] == "")
                            or (
                                link["dst_device"] in self.ip_sn
                                and rlink["sw2-info"]["sw-serial-number"]
                                == self.ip_sn[link["dst_device"]]
                            )
                            or (
                                link["dst_device"] in self.hn_sn
                                and rlink["sw2-info"]["sw-serial-number"]
                                == self.hn_sn[link["dst_device"]]
                            )
                        )
                        and (
                            (link["template"] == "")
                            or (
                                rlink.get("templateName", None)
                                == link["template"]
                            )
                        )
                    )
                ]

                for lelem in match_query:
                    if lelem not in self.result["response"]:
                        self.result["response"].append(lelem)

    def dcnm_links_deploy_to_switches(self):

        resp = {}
        resp["RETURN_CODE"] = 200

        for fabric in self.diff_deploy:
            if self.diff_deploy[fabric] != []:

                deploy_path = self.paths["LINKS_CFG_DEPLOY"].format(fabric)

                switches = ",".join(self.diff_deploy[fabric])
                deploy_path = deploy_path + switches

                resp = dcnm_send(self.module, "POST", deploy_path, "")

                if resp and resp["RETURN_CODE"] == 200:
                    self.result["response"].append(resp)
                else:
                    return resp
        return resp

    def dcnm_links_get_switch_sync_status(self):

        retry = False

        for fabric in self.diff_deploy:

            if self.diff_deploy[fabric] != []:

                path = self.paths["CONFIG_PREVIEW"].format(fabric)
                path = (
                    path
                    + ",".join(self.diff_deploy[fabric])
                    + "?forceShowRun=false&showBrief=true"
                )

                cp_resp = dcnm_send(self.module, "GET", path, "")

                if cp_resp.get("RETURN_CODE", 0) == 200:
                    if cp_resp not in self.result["response"]:
                        self.result["response"].append(cp_resp)
                    match_data = [
                        item
                        for item in cp_resp.get("DATA", [])
                        if item["switchId"] in self.diff_deploy[fabric]
                    ]
                else:
                    cp_resp["CHANGED"] = self.changed_dict[0]
                    self.module.fail_json(msg=cp_resp)

                retry = False
                for item in match_data:
                    if item["status"].lower() != "in-sync":
                        retry = True
                    else:
                        # remove the sno which is in "in-sync" from snos list of that fabric
                        self.diff_deploy[fabric].remove(item["switchId"])
        return retry

    def dcnm_links_send_message_to_dcnm(self):

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
        modified_flag = False
        delete_flag = False
        deploy_flag = False

        for link_uid in self.diff_delete:

            path = self.paths["LINKS_DELETE"]

            del_path = path + link_uid + "?isLogicalLink=false"

            resp = dcnm_send(self.module, "DELETE", del_path)

            if resp != []:
                self.result["response"].append(resp)

            if resp and resp.get("RETURN_CODE") != 200:
                resp["CHANGED"] = self.changed_dict[0]
                self.module.fail_json(msg=resp)
            else:
                delete_flag = True

        path = self.paths["LINKS_CREATE"]

        for link in self.diff_create:

            json_payload = json.dumps(link)
            resp = dcnm_send(self.module, "POST", path, json_payload)

            if resp != []:
                self.result["response"].append(resp)
            if resp and resp.get("RETURN_CODE") != 200:
                resp["CHANGED"] = self.changed_dict[0]
                self.module.fail_json(msg=resp)
            else:
                create_flag = True

        for link in self.diff_modify:

            path = self.paths["LINKS_UPDATE"] + link["link-uuid"]

            json_payload = json.dumps(link)
            resp = dcnm_send(self.module, "PUT", path, json_payload)

            if resp != []:
                self.result["response"].append(resp)

            if resp and resp.get("RETURN_CODE") != 200:
                resp["CHANGED"] = self.changed_dict[0]
                self.module.fail_json(msg=resp)
            else:
                modified_flag = True

        if self.diff_deploy != {}:

            retries = 0
            while retries < 3:

                retry = False
                retries += 1

                resp = self.dcnm_links_deploy_to_switches()

                if resp and (resp["RETURN_CODE"] != 200):
                    resp["CHANGED"] = self.changed_dict[0]
                    self.module.fail_json(msg=resp)
                else:
                    deploy_flag = True

                retry = self.dcnm_links_get_switch_sync_status()

                if retry:
                    time.sleep(1)
                else:
                    break

        self.result["changed"] = (
            create_flag or modified_flag or delete_flag or deploy_flag
        )

    def dcnm_links_update_inventory_data(self):

        """
        Routine to update inventory data for all fabrics included in the playbook. This routine
        also updates ip_sn, sn_hn and hn_sn objetcs from the updated inventory data.

        Parameters:
            None

        Returns:
            None
        """

        processed_fabrics = []

        if [] is self.config:
            return

        # Soure fabric is already processed. Add it to processed list
        processed_fabrics.append(self.fabric)

        for cfg in self.config:
            # For every fabric included in the playbook, get the inventory details. This info is required
            # to get ip_sn, hn_sn and sn_hn details
            if cfg.get("dst_fabric", "") != "":
                if cfg["dst_fabric"] not in processed_fabrics:
                    processed_fabrics.append(cfg["dst_fabric"])
                    inv_data = get_fabric_inventory_details(
                        self.module, cfg["dst_fabric"]
                    )
                    self.inventory_data.update(inv_data)

        # Get all switches which are managable. Deploy must be avoided to all switches which are not part of this list
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
        self.managable = dict(managable_ip + managable_hosts)

        self.meta_switches = [
            self.inventory_data[key]["logicalName"]
            for key in self.inventory_data
            if self.inventory_data[key]["switchRoleEnum"] is None
        ]

        # Get all fabrics which are in monitoring mode. Deploy must be avoided to all fabrics which are part of this list
        for fabric in processed_fabrics:
            path = self.paths["FABRIC_ACCESS_MODE"].format(fabric)
            resp = dcnm_send(self.module, "GET", path)

            if resp and resp["RETURN_CODE"] == 200:
                if str(resp["DATA"]["readonly"]).lower() == "true":
                    self.monitoring.append(fabric)

        # Checkif source fabric is in monitoring mode. If so return an error, since fabrics in monitoring mode do not allow
        # create/modify/delete and deploy operations.
        if self.fabric in self.monitoring:
            self.module.fail_json(
                msg="Error: Source Fabric '{0}' is in Monitoring mode, No changes are allowed on the fabric\n".format(
                    self.fabric
                )
            )

        # Based on the updated inventory_data, update ip_sn, hn_sn and sn_hn objects
        self.ip_sn, self.hn_sn = get_ip_sn_dict(self.inventory_data)
        self.sn_hn = dict(
            [(value, key) for key, value in self.hn_sn.items() if value != ""]
        )

    def dcnm_links_translate_playbook_info(self, config, ip_sn, hn_sn):

        """
        Routine to translate parameters in playbook if required.
            - This routine converts the hostname information included in
              playbook to actual addresses.
            - translates template names based on version of DCNM

        Parameters:
            config - The resource which needs tranlation
            ip_sn - IP address to serial number mappings
            hn_sn - hostname to serial number mappings

        Returns:
            None
        """

        if [] is config:
            return

        for cfg in config:

            if cfg.get("src_device", "") != "":
                if (
                    cfg["src_device"] in self.ip_sn
                    or cfg["src_device"] in self.hn_sn
                ):
                    cfg["src_device"] = dcnm_get_ip_addr_info(
                        self.module, cfg["src_device"], ip_sn, hn_sn
                    )
            if cfg.get("dst_device", "") != "":
                if (
                    cfg["dst_device"] in self.ip_sn
                    or cfg["dst_device"] in self.hn_sn
                    and cfg["dst_device"] not in self.meta_switches
                ):
                    cfg["dst_device"] = dcnm_get_ip_addr_info(
                        self.module, cfg["dst_device"], ip_sn, hn_sn
                    )

            if cfg.get("template", None) is not None:
                cfg["template"] = self.templates.get(
                    cfg["template"], "dcnm_links_invalid_template"
                )


def main():

    """ main entry point for module execution
    """
    element_spec = dict(
        src_fabric=dict(required=True, type="str"),
        config=dict(required=False, type="list", elements="dict", default=[]),
        state=dict(
            type="str",
            default="merged",
            choices=["merged", "deleted", "replaced", "query"],
        ),
        deploy=dict(type="bool", default="true"),
    )

    module = AnsibleModule(
        argument_spec=element_spec, supports_check_mode=True
    )

    dcnm_links = DcnmLinks(module)

    state = module.params["state"]

    if [] is dcnm_links.config:
        if state == "merged" or state == "replaced":
            module.fail_json(
                msg="'config' element is mandatory for state '{0}', given = '{1}'".format(
                    state, dcnm_links.config
                )
            )

    dcnm_links.dcnm_links_update_inventory_data()
    dcnm_links.dcnm_links_translate_playbook_info(
        dcnm_links.config, dcnm_links.ip_sn, dcnm_links.hn_sn
    )

    dcnm_links.dcnm_links_validate_input()

    if module.params["state"] != "query":
        dcnm_links.dcnm_links_get_want()
        dcnm_links.dcnm_links_get_have()

        # self.want would have defaulted all optional objects not included in playbook. But the way
        # these objects are handled is different between 'merged' and 'replaced' states. For 'merged'
        # state, objects not included in the playbook must be left as they are and for state 'replaced'
        # they must be purged or defaulted.

        dcnm_links.dcnm_links_update_want()

    if (module.params["state"] == "merged") or (
        module.params["state"] == "replaced"
    ):
        dcnm_links.dcnm_links_get_diff_merge()

    if module.params["state"] == "deleted":
        dcnm_links.dcnm_links_get_diff_deleted()

    if module.params["state"] == "query":
        dcnm_links.dcnm_links_get_diff_query()

    dcnm_links.result["diff"] = dcnm_links.changed_dict
    dcnm_links.changed_dict[0]["debugs"].append(
        {"Managable": dcnm_links.managable}
    )
    dcnm_links.changed_dict[0]["debugs"].append(
        {"Monitoring": dcnm_links.monitoring}
    )

    if dcnm_links.diff_create or dcnm_links.diff_delete:
        dcnm_links.result["changed"] = True

    if module.check_mode:
        dcnm_links.result["changed"] = False
        module.exit_json(**dcnm_links.result)

    dcnm_links.dcnm_links_send_message_to_dcnm()

    module.exit_json(**dcnm_links.result)


if __name__ == "__main__":
    main()
