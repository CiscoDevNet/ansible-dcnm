#!/usr/bin/python
#
# Copyright (c) 2021 Cisco and/or its affiliates.
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

DOCUMENTATION = """
---
module: dcnm_service_route_peering
short_description: DCNM Ansible Module for managing Service Route Peerings.
version_added: "1.1.0"
description:
    - DCNM Ansible Module for Creating, Deleting, Querying and Modifying Route Peerings
author: Mallik Mudigonda
options:
  fabric:
    description:
      - 'Name of the target fabric for route peering operations'
    type: str
    required: true
  service_fabric:
    description:
      - 'Name of the external fabric attached to the service node for route peering operations'
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
      - overridden
      - deleted
      - query
    default: merged
  attach:
    description:
      - A flag specifying if the given route peering is to be attached to the specified service node
    type: bool
    required: false
    default: true
  deploy:
    description:
      - A flag specifying if a route peering is to be deployed on the switches
    type: bool
    required: false
    default: true
  config:
    description:
      - A list of dictionaries containing route peering and switch information
    type: list
    elements: dict
    suboptions:
      name:
        description:
          - A unique name which identifies the route peering
        type: str
        required: true
      node_name:
        description:
          - Name of the service node where the route peering is to be deployed
        type: str
        required: true
      deploy_mode:
        description:
          - Type of service node.
        type: str
        required: true
        choices: ['intra_tenant_fw', 'inter_tenant_fw', 'one_arm_adc', 'two_arm_adc']
      peering_option:
        description:
          - Specifies the type of peering
          - NOTE: This object is applicable only when 'deploy_mode' is either 'inter_tenant_fw'
                  or 'one_arm_adc' or 'two_arm_adc'
        type: str
        required: False
        default: 'static'
        choices: ['static', 'ebgp']
      next_hop:
        description:
          - Nexthop IPV4 information, e.g., 192.168.1.100
          - NOTE: This object is applicable only when 'deploy_mode' is 'intra_tenant_fw'
        type: int
        required: true
      rev_next_hop:
        description:
          - Reverse Nexthop IPV4 information, e.g., 192.169.1.100
          - NOTE: This object is applicable only when 'deploy_mode' is either 'intra_tenant_fw'
                  or 'one_arm_adc' or 'two_arm_adc'
        type: int
        required: false
        default: ""
      inside_network:
        description:
          - Details regarding inside network of the route peering
          - NOTE: This object is applicable only when 'deploy_mode' is 'intra_tenant_fw'
                  or 'inter_tenant_fw'
        type: dict
        required: true
        suboptions:
          vrf:
            description:
              - VRF name for the inside network
            type: str
            required: true
          name:
            description:
              - Network name
            type: str
            required: true
          vlan_id:
            description:
              - Vlan Id for the inside network
            type: int
            required: true
          profile:
            description:
              - Profile information for the inside network
            type: dict
            required: true
            suboptions:
              ipv4_gw:
                description:
                  - IPV4 gateway information including the mask e.g. 192.168.1.1/24
                type: ipv4
                required: true
              ipv6_gw:
                description:
                  - IPV6 gateway information including the mask e.g., 2000:01:01::01/64
                type: ipv6
                required: false
                default: ""
              vlan_name:
                description:
                  - Vlan name
                type: str
                required: false
                default: ""
              int_descr:
                description:
                  - Description of the interface
                type: str
                required: false
                default: ""
              tag:
                description:
                  - Route tag information
                type: int
                required: false
                default: 12345
              static_route:
                description:
                  - Static route information
                  - NOTE: This object is applicable only when 'peering_option' is 'static'
                type: list
                elements: dict
                required: false
                default: ''
                suboptions:
                  subnet:
                    description:
                      - Subnet information, for e.g., 11.0.0.0/24
                    type: ipv4
                    required: True
                  next_hop:
                    description:
                      - Gateway IP addresses, for e.g., 192.168.1.1
                    type: list
                    elements: ipv4
                    required: True
              ipv4_neighobor:
                description:
                  - IPv4 neighbor address
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: ipv4
                required: True
              ipv4_lo:
                description:
                  - IPv4 loopback address
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: ipv4
                required: True
              ipv4_vpc_peer_lo:
                description:
                  - IPv4 vpc peer loopback address
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'. This
                          object will be mandatory if the service node switch is part of VPC
                          pair
                type: ipv4
                required: False
                default: ''
              ipv6_neighbor:
                description:
                  - IPv6 neighbor address
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: ipv6
                required: False
                default: ''
              ipv6_lo:
                description:
                  - IPv6 loopback address
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: ipv6
                required: False
                default: ''
              ipv6_vpc_peer_lo:
                description:
                  - IPv6 vpc peer loopback address
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'. This
                          object will be mandatory if the service node switch is part of VPC
                          pair
                type: ipv6
                required: False
                default: ''
              route_map_tag:
                description:
                  - Route Tag
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: int
                required: True
                default: 12345
              neigh_int_descr:
                description:
                  - Description of the interface
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: str
                required: False
                default: ''
              local_asn:
                description:
                  - Local ASN number
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: int
                required: False
                default: 12345
              adv_host:
                description:
                  - Flag indicating if the host is to be advertised
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: bool
                required: False
                default: True
      outside_network:
        description:
          - Details regarding outside network of the route peering
          - NOTE: This object is applicable only when 'deploy_mode' is 'intra_tenant_fw'
                  or 'inter_tenant_fw'
        type: dict
        required: true
        suboptions:
          vrf:
            description:
              - VRF name for the outside network
            type: str
            required: true
          name:
            description:
              - Network name
            type: str
            required: true
          vlan_id:
            description:
              - Vlan Id for the outside network
            type: int
            required: true
          profile:
            description:
              - Profile information for the outside network
            type: dict
            required: true
            suboptions:
              ipv4_gw:
                description:
                  - IPV4 gateway information including the mask e.g. 192.168.1.1/24
                type: ipv4
                required: true
              ipv6_gw:
                description:
                  - IPV6 gateway information including the mask e.g., 2000:01:01::01/64
                type: ipv6
                required: false
                default: ""
              vlan_name:
                description:
                  - Vlan name
                type: str
                required: false
                default: ""
              int_descr:
                description:
                  - Description of the interface
                type: str
                required: false
                default: ""
              tag:
                description:
                  - Route tag information
                type: int
                required: false
                default: 12345
              static_route:
                description:
                  - Static route information
                  - NOTE: This object is applicable only when 'peering_option' is 'static' and
                          'deploy_mode' is 'intra_tenant_fw'
                type: list
                elements: dict
                required: false
                default: ''
                suboptions:
                  subnet:
                    description:
                      - Subnet information, for e.g., 11.0.0.0/24
                    type: ipv4
                    required: True
                  next_hop:
                    description:
                      - Gateway IP addresses, for e.g., 192.168.1.1
                    type: list
                    elements: ipv4
                    required: True
              ipv4_neighobor:
                description:
                  - IPv4 neighbor address
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: ipv4
                required: True
              ipv4_lo:
                description:
                  - IPv4 loopback address
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: ipv4
                required: True
              ipv4_vpc_peer_lo:
                description:
                  - IPv4 vpc peer loopback address
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: ipv4
                required: False
                default: ''
              ipv6_neighbor:
                description:
                  - IPv6 neighbor address
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: ipv6
                required: False
                default: ''
              ipv6_lo:
                description:
                  - IPv6 loopback address
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: ipv6
                required: False
                default: ''
              ipv6_vpc_peer_lo:
                description:
                  - IPv6 vpc peer loopback address
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: ipv6
                required: False
                default: ''
              route_map_tag:
                description:
                  - Route Tag
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: int
                required: True
                default: 12345
              neigh_int_descr:
                description:
                  - Description of the interface
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: str
                required: False
                default: ''
              local_asn:
                description:
                  - Local ASN number
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: int
                required: False
                default: 12345
              adv_host:
                description:
                  - Flag indicating if the host is to be advertised
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: bool
                required: False
                default: true
      first_arm:
        description:
          - Details regarding firast arm of the route peering
          - NOTE: This object is applicable only when 'deploy_mode' is either
                  'one_arm_adc' or 'two_arm_adc'
        type: dict
        required: true
        suboptions:
          vrf:
            description:
              - VRF name for the first arm
            type: str
            required: true
          name:
            description:
              - Network name
            type: str
            required: true
          vlan_id:
            description:
              - Vlan Id for the  first arm
            type: int
            required: true
          profile:
            description:
              - Profile information for the first arm
            type: dict
            required: true
            suboptions:
              ipv4_gw:
                description:
                  - IPV4 gateway information including the mask e.g. 192.168.1.1/24
                type: ipv4
                required: true
              ipv6_gw:
                description:
                  - IPV6 gateway information including the mask e.g., 2000:01:01::01/64
                type: ipv6
                required: false
                default: ""
              vlan_name:
                description:
                  - Vlan name
                type: str
                required: false
                default: ""
              int_descr:
                description:
                  - Description of the interface
                type: str
                required: false
                default: ""
              tag:
                description:
                  - Route tag information
                type: int
                required: false
                default: 12345
              static_route:
                description:
                  - Static route information
                  - NOTE: This object is applicable only when 'peering_option' is 'static'
                type: list
                elements: dict
                required: false
                default: ''
                suboptions:
                  subnet:
                    description:
                      - Subnet information, for e.g., 11.0.0.0/24
                    type: ipv4
                    required: True
                  next_hop:
                    description:
                      - Gateway IP addresses, for e.g., 192.168.1.1
                    type: list
                    elements: ipv4
                    required: True
              ipv4_neighobor:
                description:
                  - IPv4 neighbor address
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: ipv4
                required: True
              ipv4_lo:
                description:
                  - IPv4 loopback address
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: ipv4
                required: True
              ipv4_vpc_peer_lo:
                description:
                  - IPv4 vpc peer loopback address
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: ipv4
                required: False
                default: ''
              ipv6_neighbor:
                description:
                  - IPv6 neighbor address
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: ipv6
                required: False
                default: ''
              ipv6_lo:
                description:
                  - IPv6 loopback address
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: ipv6
                required: False
                default: ''
              ipv6_vpc_peer_lo:
                description:
                  - IPv6 vpc peer loopback address
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: ipv6
                required: False
                default: ''
              route_map_tag:
                description:
                  - Route Tag
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: int
                required: True
                default: 12345
              neigh_int_descr:
                description:
                  - Description of the interface
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: str
                required: False
                default: ''
              local_asn:
                description:
                  - Local ASN number
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: int
                required: False
                default: 12345
              adv_host:
                description:
                  - Flag indicating if the host is to be advertised
                  - NOTE: This object is applicable only when 'peering_option' is 'ebgp'
                type: bool
                required: False
                default: True
      second_arm:
        description:
          - Details regarding second arm of the route peering
          - NOTE: This object is applicable only when 'deploy_mode' is either
                  'one_arm_adc' or 'two_arm_adc'
        type: dict
        required: true
        suboptions:
          vrf:
            description:
              - VRF name for the second arm
            type: str
            required: true
          name:
            description:
              - Network name
            type: str
            required: true
          vlan_id:
            description:
              - Vlan Id for the second arm
            type: int
            required: true
          profile:
            description:
              - Profile information for the second arm
            type: dict
            required: true
            suboptions:
              ipv4_gw:
                description:
                  - IPV4 gateway information including the mask e.g. 192.168.1.1/24
                type: ipv4
                required: true
              ipv6_gw:
                description:
                  - IPV6 gateway information including the mask e.g., 2000:01:01::01/64
                type: ipv6
                required: false
                default: ""
              vlan_name:
                description:
                  - Vlan name
                type: str
                required: false
                default: ""
              int_descr:
                description:
                  - Description of the interface
                type: str
                required: false
                default: ""
              tag:
                description:
                  - Route tag information
                type: int
                required: false
                default: 12345
"""

EXAMPLES = """

States:
This module supports the following states:

Merged:
  Route Peerings defined in the playbook will be merged into the target fabric.
    - If the Route Peerings does not exist it will be added.
    - If the Route Peerings exists but properties managed by the playbook are different
      they will be updated if possible.
    - Route peerings that are not specified in the playbook will be untouched.

Replaced:
  Route Peerings defined in the playbook will be replaced in the target fabric.
    - If the Route Peerings does not exist it will be added.
    - If the Route Peerings exists but properties managed by the playbook are different
      they will be updated if possible.
    - Properties that can be managed by the module but are not specified
      in the playbook will be deleted or defaulted if possible.
    - Route Peerings that are not specified in the playbook will be untouched.

Overridden:
  Route Peerings defined in the playbook will be overridden in the target fabric.
    - If the Route Peerings does not exist it will be added.
    - If the Route Peerings exists but properties managed by the playbook are different
      they will be updated if possible.
    - Properties that can be managed by the module but are not specified
      in the playbook will be deleted or defaulted if possible.
    - Roue Peerings that are not specified in the playbook will be deleted.

Deleted:
  Route Peerings defined in the playbook will be deleted.

Query:
  Returns the current DCNM state for the route peerings listed in the playbook.

CREATING ROUTE PEERINGS
=======================

INTRA-TENANT FIREWALL

- name: Create different new service route peerings including all objects
  cisco.dcnm.dcnm_service_route_peering:
    state: merged
    fabric: test-fabric
    service_fabric: external
    config:
      - name: IT-FW-RP1                                  # mandatory
        node_name: IT-SN-1                               # mandatory
        deploy_mode: intra_tenant_fw                     # mandatory, choices=[intra_tenant_fw, inter_tenant_fw]
        inside_network:                                  #
          vrf: IT-VRF-11                                 # mandatory
          name: rp1-sn1-inside-net                       # mandatory
          vlan_id: 101                                   # mandatory
          profile:
            ipv4_gw: 192.161.1.1/24                      # mandatory
            ipv6_gw: 2001:db01::1/64                     # optional, default is ''
            vlan_name: rp1-sn1-inside                    # optional, default is ''
            int_descr: "RP1 SN1 inside interface"        # optional, default is ''
            tag: 11111                                   # optional, default is 12345
        next_hop: 192.161.1.100                          # mandatory
        outside_network:                                 #
          vrf: IT-VRF-11                                 # mandatory
          name: rp1-sn1-outside-net                      # mandatory
          vlan_id: 102                                   # mandatory
          profile:
            ipv4_gw: 192.161.2.1/24                      # mandatory
            ipv6_gw: 2001:db02::1/64                     # optional, default is ''
            vlan_name: rp1-sn1-outside                   # optional, default is ''
            int_descr: "RP1 SN1 outside interface"       # optionL, default is ''
            tag: 11112                                   # optional, default is 12345
        rev_next_hop: 192.161.2.100                      # optional, default is ''
    attach: true
    deploy: true

INTER-TENANT FIREWALL with STATIC peering

- name: Create different new service route peerings including all objects
  cisco.dcnm.dcnm_service_route_peering:
    state: merged
    fabric: test-fabric
    service_fabric: external
    config:
      - name: IT-FW-RP2                                  # mandatory
        node_name: IT-SN-1                               # mandatory
        deploy_mode: inter_tenant_fw                     # mandatory, choices=[intra_tenant_fw, inter_tenant_fw]
        peering_option: static                           # optional, default is static, choices=[static, ebgp]
        inside_network:                                  #
          vrf: IT-VRF-21                                 # mandatory
          name: rp2-sn1-inside-net                       # mandatory
          vlan_id: 201                                   # mandatory
          profile:
            ipv4_gw: 192.162.1.1/24                      # mandatory
            ipv6_gw: 2002:db01::1/64                     # optional, default is ''
            vlan_name: rp2-sn1-inside                    # optional, default is ''
            int_descr: "RP2 SN1 inside interface"        # optional, default is ''
            static_route:                                # optional, default is ''
              - subnet: 20.20.20.0/24
                next_hop:
                  - 120.120.120.100
                  - 121.121.121.100
            tag: 21111                                   # optional, default is 12345
        outside_network:                                 #
          vrf: IT-VRF-22                                 # mandatory
          name: rp2-sn1-outside-net                      # mandatory
          vlan_id: 202                                   # mandatory
          profile:
            ipv4_gw: 192.162.2.1/24                      # mandatory
            ipv6_gw: 2002:db02::1/64                     # optional, default is ''
            vlan_name: rp2-sn1-outside                   # optional, default is ''
            int_descr: "RP2 SN1 outside interface"       # optional, default is ''
            static_route:                                # optional, default is ''
              - subnet: 21.21.21.0/24
                next_hop:
                  - 122.122.122.100
                  - 123.123.123.100
            tag: 22222                                   # optional, default is 12345
    attach: true
    deploy: true

INTER-TENANT FIREWALL with EBGP peering

- name: Create different new service route peerings including all objects
  cisco.dcnm.dcnm_service_route_peering:
    state: merged
    fabric: test-fabric
    service_fabric: external
    config:
      - name: IT-FW-RP3                                      # mandatory
            node_name: IT-SN-1                               # mandatory
            deploy_mode: inter_tenant_fw                     # mandatory, choices=[intra_tenant_fw, inter_tenant_fw]
            peering_option: ebgp                             # optional, default is static, choices=[static, ebgp]
            inside_network:
              vrf: IT-VRF-31                                 # mandatory
              name: rp3-sn1-inside-net                       # mandatory
              vlan_id: 301                                   # mandatory
              profile:
                ipv4_gw: 192.163.1.1/24                      # mandatory
                ipv6_gw: 2003:db01::1/64                     # optional, default is ''
                vlan_name: rp3-sn1-inside                    # optional, default is ''
                int_descr: "RP3 SN1 inside interface"        # optional, default is ''
                tag: 31111                                   # optional, default is 12345
                ipv4_neighbor: 31.31.31.1                    # mandatory
                ipv4_lo: 31.31.31.2                          # mandatory
                ipv4_vpc_peer_lo: 31.31.31.3                 # optional, default is ''
                ipv6_neighbor: 2003:3131::1                  # optional, default is ''
                ipv6_lo: 2003:3132::1                        # optional, default is ''
                ipv6_vpc_peer_lo: 2003:3133::1               # optional, default is ''
                route_map_tag: 33111                         # optional, default is 12345 ????
                neigh_int_descr: "RP3 SN1 inside interface"  # optional, default is '' ????
                local_asn: 65301                             # optional, default is ''
                adv_host: true                               # optional, default is false
            outside_network:
              vrf: IT-VRF-32                                 # mandatory
              name: rp3-sn1-outside-net                      # mandatory
              vlan_id: 302                                   # mandatory
              profile:
                ipv4_gw: 192.163.2.1/24                      # mandatory
                ipv6_gw: 2003:db02::1/64                     # optional, default is ''
                vlan_name: rp3-sn1-outside                   # optional, default is ''
                int_descr: "RP3 SN1 outside interface"       # optional, default is ''
                tag: 31112                                   # optional, default is 12345
                ipv4_neighbor: 131.131.131.1                 # mandatory
                ipv4_lo: 131.131.131.2                       # mandatory
                ipv4_vpc_peer_lo: 131.131.131.3              # optional, default is ''
                ipv6_neighbor: 2003:8383::1                  # optional, default is ''
                ipv6_lo: 2003:8384::1:100:1                  # optional, default is ''
                ipv6_vpc_peer_lo: 2003:8385::1               # optional, default is ''
                route_map_tag: 31113                         # optional, default is 12345 ????
                neigh_int_descr: "RP3 SN1 outside interface" # optional, default is '' ????
                local_asn: 65302                             # optional, default is ''
                adv_host: true                               # optional, default is false
    attach: true
    deploy: true

ONEARM ADC with EBGP peering

- name: Create different new service route peerings including all objects
  cisco.dcnm.dcnm_service_route_peering:
    state: merged
    fabric: test-fabric
    service_fabric: external
    config:
      - name: IT-ADC-RP4
            node_name: IT-SN-2                               # mandatory
            deploy_mode: one_arm_adc                         # mandatory, choices=[one_arm_adc, two_arm_adc]
            peering_option: ebgp                             # optional, default is static, choices=[static, ebgp]
            first_arm:
              vrf: IT-VRF-41                                 # mandatory
              name: rp4-sn2-first-arm                        # mandatory
              vlan_id: 401                                   # mandatory
              profile:
                ipv4_gw: 192.164.1.1/24                      # mandatory
                ipv6_gw: 2004:db01::1/64                     # optional, default is ''
                vlan_name: rp4-sn2-first-arm                 # optional, default is ''
                int_descr: "RP4 SN2 first arm intf"          # optional, default is ''
                tag: 41111                                   # optional, default is 12345
                ipv4_neighbor: 41.41.41.1                    # mandatory
                ipv4_lo: 41.41.41.2                          # mandatory
                ipv4_vpc_peer_lo: 41.41.41.3                 # optional, default is ''
                ipv6_neighbor: 2004:4141::1                  # optional, default is ''
                ipv6_lo: 2004:4142::1                        # optional, default is ''
                ipv6_vpc_peer_lo: 2004:4143::1               # optional, default is ''
                route_map_tag: 41112                         # optional, default is 12345
                neigh_int_descr: "RP4 SN2 first arm"         # optional, default is ''
                local_asn: 65401                             # optional, default is ''
                adv_host: true                               # optional, default is false
            rev_next_hop: 192.164.1.100                      # mandatory
    attach: true
    deploy: true

TWOARM ADC with EBGP peering

- name: Create different new service route peerings including all objects
  cisco.dcnm.dcnm_service_route_peering:
    state: merged
    fabric: test-fabric
    service_fabric: external
    config:
      - name: IT-ADC-RP5
            node_name: IT-SN-2                               # mandatory
            deploy_mode: two_arm_adc                         # mandatory, choices=[one_arm_adc, two_arm_adc]
            peering_option: ebgp                             # optional, default is static, choices=[static, ebgp]
            first_arm:
              vrf: IT-VRF-51            "                    # mandatory
              name: rp5-sn2-first-arm                        # mandatory
              vlan_id: 501                                   # mandatory
              profile:
                ipv4_gw: 192.165.1.1/24                      # mandatory
                ipv6_gw: 2005:db01::1/64                     # optional, default is ''
                vlan_name: rp5-sn2-first-arm                 # optional, default is ''
                int_descr: "RP5 SN2 first arm intf"          # optional, default is ''
                tag: 51111                                   # optional, default is 12345
                ipv4_neighbor: 51.51.51.1                    # mandatory
                ipv4_lo: 51.51.51.2                          # mandatory
                ipv4_vpc_peer_lo: 51.51.51.3                 # optional, default is ''
                ipv6_neighbor: 2005:5151::1                  # optional, default is ''
                ipv6_lo: 2005:5152::1                        # optional, default is ''
                ipv6_vpc_peer_lo: 2005:5153::1               # optional, default is ''
                route_map_tag: 51115                         # optional, default is 12345
                neigh_int_descr: "RP5 SN2 first arm"         # optional, default is ''
                local_asn: 65501                             # optional, default is ''
                adv_host: true                               # optional, default is false
            second_arm:
              vrf: IT-VRF-52            "                    # mandatory
              name: rp5-sn2-second-arm                       # mandatory
              vlan_id: 502                                   # mandatory
              profile:
                ipv4_gw: 192.165.2.1/24                      # mandatory
                ipv6_gw: 2005:db02::1/64                     # optional, default is ''
                vlan_name: rp5-sn2-second-arm                # optional, default is ''
                int_descr: "RP5 SN2 second arm intf"         # optional, default is ''
                tag: 51112                                   # optional, default is 12345
            rev_next_hop: 192.165.1.100                      # mandatory
    attach: true
    deploy: true

ONEARM ADC with STATIC peering

- name: Create different new service route peerings including all objects
  cisco.dcnm.dcnm_service_route_peering:
    state: merged
    fabric: test-fabric
    service_fabric: external
    config:
      - name: IT-ADC-RP6
            node_name: IT-SN-2                               # mandatory
            deploy_mode: one_arm_adc                         # mandatory, choices=[one_arm_adc, two_arm_adc]
            peering_option: static                           # optional, default is static, choices=[static, ebgp]
            first_arm:
              vrf: IT-VRF-61                                 # mandatory
              name: rp6-sn2-first-arm                        # mandatory
              vlan_id: 601                                   # mandatory
              profile:
                ipv4_gw: 192.166.1.1/24                      # mandatory
                ipv6_gw: 2006:db01::1/64                     # optional, default is ''
                vlan_name: rp6-sn2-first-arm                 # optional, default is ''
                int_descr: "RP6 SN2 first arm intf"          # optional, default is ''
                tag: 61111                                   # optional, default is 12345
                static_route:                                # optional, default is ''
                  - subnet: 61.61.61.1/24
                    next_hop:
                      - 161.161.161.1
                      - 162.162.162.1
                  - subnet: 22.0.0.0/24
                    next_hop:
                      - 163.163.163.1
                      - 164.164.164.1
            rev_next_hop: 192.166.1.100                      # mandatory
    attach: true
    deploy: true

TWOARM ADC with STATIC peering

- name: Create different new service route peerings including all objects
  cisco.dcnm.dcnm_service_route_peering:
    state: merged
    fabric: test-fabric
    service_fabric: external
    config:
      - name: IT-ADC-RP7
            node_name: IT-SN-2                               # mandatory
            deploy_mode: two_arm_adc                         # mandatory, choices=[one_arm_adc, two_arm_adc]
            peering_option: static                           # optional, default is static, choices=[static, ebgp]
            first_arm:
              vrf: IT-VRF-71                                 # mandatory
              name: rp7-sn2-first-arm                        # mandatory
              vlan_id: 701                                   # mandatory
              profile:
                ipv4_gw: 192.167.1.1/24                      # mandatory
                ipv6_gw: 2007:db01::1/64                     # optional, default is ''
                vlan_name: rp7-sn2-first-arm                 # optional, default is ''
                int_descr: "RP6 SN2 first arm  intf"         # optional, default is ''
                tag: 71111                                   # optional, default is 12345
                static_route:                                # optional, default is ''
                  - subnet: 71.71.71.1/24
                    next_hop:
                      - 171.171.171.1
                      - 172.172.172.1
            second_arm:
              vrf: IT-VRF-72                                 # mandatory
              name: rp7-sn2-second-arm                       # mandatory
              vlan_id: 702                                   # mandatory
              profile:
                ipv4_gw: 192.167.2.1/24                      # mandatory
                ipv6_gw: 2007:db02::1/64                     # optional, default is ''
                vlan_name: rp7-sn2-second-arm                # optional, default is ''
                int_descr: "RP7 SN2 second arm intf"         # optional, default is ''
                tag: 71112                                   # optional, default is 12345
            rev_next_hop: 192.167.1.100                      # mandatory
    attach: true
    deploy: true

DELETE ROUTE PEERINGS
=====================

- name: Delete route peerings
  cisco.dcnm.dcnm_service_route_peering:
    state: deleted
    fabric: test-fabric
    service_fabric: external
    config:
      - name: IT-FW-RP1                                   # mandatory
        node_name: IT-SN-1                                # mandatory

OVERRIDE ROUTE PEERINGS
=======================

- name: Override existing route peerings with new peerings
  cisco.dcnm.dcnm_service_route_peering:
    state: overridden
    fabric: test-fabric
    service_fabric: external
    config:
      - name: IT-FW-RP-OVR1                              # mandatory
        node_name: IT-SN-1                               # mandatory
        deploy_mode: intra_tenant_fw                     # mandatory, choices=[intra_tenant_fw, inter_tenant_fw]
        inside_network:                                  #
          vrf: IT-VRF-12                                 # mandatory
          name: rp1-sn1-inside-net-ovr                   # mandatory
          vlan_id: 191                                   # mandatory
          profile:
            ipv4_gw: 192.161.91.1/24                     # mandatory
            ipv6_gw: 2001:db11::1/64                     # optional, default is ''
            vlan_name: rp1-sn1-inside-ovr                # optional, default is ''
            int_descr: "RP1 SN1 inside interface ovr"    # optional, default is ''
            tag: 11191                                   # optional, default is 12345
        next_hop: 192.161.91.100                         # mandatory
        outside_network:                                 #
          vrf: IT-VRF-12                                 # mandatory
          name: rp1-sn1-outside-net-ovr                  # mandatory
          vlan_id: 192                                   # mandatory
          profile:
            ipv4_gw: 192.161.92.1/24                     # mandatory
            ipv6_gw: 2001:db12::1/64                     # optional, default is ''
            vlan_name: rp1-sn1-outside-ovr               # optional, default is ''
            int_descr: "RP1 SN1 outside interface ovr"   # optionL, default is ''
            tag: 11192                                   # optional, default is 12345
        rev_next_hop: 192.161.92.100                     # optional, default is ''
    attach: true
    deploy: true

- name: Override existing route peerings with no new peerings
  cisco.dcnm.dcnm_service_route_peering:
    state: overridden
    fabric: test-fabric
    service_fabric: external
    attach: true
    deploy: true

- name: Override existing route peerings with just service node names
  cisco.dcnm.dcnm_service_route_peering:
    state: overridden
    fabric: test-fabric
    service_fabric: external
    config:
      - node_name: IT-SN-1                                # optional
      - node_name: IT-SN-2                                # optional
    attach: true
    deploy: true

REPLACE ROUTE PEERINGS
======================

- name: Replace service route peerings RP1
  cisco.dcnm.dcnm_service_route_peering: &dcnm_srp_rep_13
    state: replaced
    fabric: test-fabric
    service_fabric: external
    config:
      - name: IT-FW-RP1                                  # mandatory
        node_name: IT-SN-1                               # mandatory
        deploy_mode: intra_tenant_fw                     # mandatory, choices=[intra_tenant_fw, inter_tenant_fw]
        inside_network:                                  #
          vrf: IT-VRF-11                                 # mandatory
          name: rp1-sn1-inside-net                       # mandatory
          vlan_id: 191                                   # mandatory
          profile:
            ipv4_gw: 192.161.1.1/24                      # mandatory
            ipv6_gw: 2101:db01::01/64                    # optional, default is ''
            vlan_name: rp1-sn1-inside-rep                # optional, default is ''
            int_descr: "RP1 SN1 inside interface - REP"  # optional, default is ''
            tag: 11101                                   # optional, default is 12345
        next_hop: 192.161.1.200                          # mandatory
        outside_network:                                 #
          vrf: IT-VRF-11                                 # mandatory
          name: rp1-sn1-outside-net                      # mandatory
          vlan_id: 192                                   # mandatory
          profile:
            ipv4_gw: 192.161.2.1/24                      # mandatory
            ipv6_gw: 2101:db02::1/64                     # optional, default is ''
            vlan_name: rp1-sn1-outside-rep               # optional, default is ''
            int_descr: "RP1 SN1 outside interface- REP"  # optionL, default is ''
            tag: 11102                                   # optional, default is 12345
        rev_next_hop: 192.161.2.200                      # optional, default is ''
    attach: true
    deploy: true

QUERY ROUTE PEERINGS
====================

- name: Query existing route peerings with specific peering names
  cisco.dcnm.dcnm_service_route_peering:
    state: query
    fabric: test-fabric
    service_fabric: external
    config:
      - name: IT-FW-RP1                                   # optional
        node_name: IT-SN-1                                # mandatory

      - name: IT-FW-RP2                                   # optional
        node_name: IT-SN-1                                # mandatory

      - name: IT-FW-RP3                                   # optional
        node_name: IT-SN-1                                # mandatory

      - name: IT-ADC-RP4                                  # optional
        node_name: IT-SN-2                                # mandatory

      - name: IT-ADC-RP5                                  # optional
        node_name: IT-SN-2                                # mandatory

      - name: IT-ADC-RP6                                  # optional
        node_name: IT-SN-2                                # mandatory

      - name: IT-ADC-RP7                                  # optional
        node_name: IT-SN-2                                # mandatory

- name: Query existing route peerings without specific peering names
  cisco.dcnm.dcnm_service_route_peering:
    state: query
    fabric: test-fabric
    service_fabric: external
    config:
        node_name: IT-SN-1                                # mandatory
        node_name: IT-SN-2                                # mandatory

"""

import time
import json
import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
    validate_list_of_dicts,
    dcnm_reset_connection,
)

from datetime import datetime


# Route Peering Class object which includes all the required methods and data to configure and maintain Roue peering objects
class DcnmServiceRoutePeering:
    def __init__(self, module):
        self.debug = False
        self.module = module
        self.params = module.params
        self.fabric = module.params["fabric"]
        self.config = copy.deepcopy(module.params.get("config"))
        self.check_mode = False
        self.srp_info = []
        self.want = []
        self.have = []
        self.diff_create = []
        self.diff_modify = []
        self.diff_delete = []
        self.diff_deploy = []
        self.fd = None
        self.changed_dict = [
            {"merged": [], "modified": [], "deleted": [], "deploy": [], "query": []}
        ]
        self.result = dict(changed=False, diff=[], response=[])

    def log_msg(self, msg):

        if self.fd is None:
            self.fd = open("srp.log", "a+")
        if self.fd is not None:
            self.fd.write(msg)
            self.fd.flush()

    def dcnm_srp_validate_and_build_srp_info(
        self,
        cfg,
        srp_spec,
        srp_network_spec,
        srp_prof1_spec,
        srp_prof2_spec,
        net_name1,
        net_name2,
    ):

        """
        Routine to validate the playbook input and fill up default values for objects not included. It takes specific profiles
        to validate the input against. In this csase we validate the playbook against srp_spec which inlcudes common information
        srp_network_spec which inlcudes network specific information and profile_specX which inlciudes network profile information.
        For route peering we have two networks or arms and hence two profile specs. This routine updates self.srp_info with validated
        playbook information by defaulting values not included

        Parameters:
            cfg (dict): The config from playbook
            srp_spec (dict): Route peering common spec
            srp_network_spec (dict): Rourte peering network related config spec
            srp_prof1_spec (dict): Route peering profile spec for inside-network/outside-network/first-arm
            srp_prof2_spec (dict): Route peering profile spec for second-arm
            net_name1 (string): Name of inside-network/first-arm
            net_name2 (string): Name of outside-network/second-arm

        Returns:
            None
        """

        srp_static_route_spec = dict(
            subnet=dict(required=True, type="ipv4"),
            next_hop=dict(required=True, type="list"),
        )

        srp_info, invalid_params = validate_list_of_dicts(cfg, srp_spec)
        if invalid_params:
            if cfg[0].get("name", " ") != " ":
                mesg = "Invalid parameters in playbook: {}".format(
                    "while processing Route Peering -  "
                    + cfg[0]["name"]
                    + ", "
                    + "\n".join(invalid_params)
                )
            else:
                mesg = "Invalid parameters in playbook: {}".format(
                    "while processing Route Peering -  Unknown, "
                    + "\n".join(invalid_params)
                )
            self.module.fail_json(msg=mesg)

        self.srp_info.extend(srp_info)

        in_list = []
        out_list = []
        for item in srp_info:

            in_list.append(item[net_name1])
            # Validate inside and outside network dicts from route peering info
            in_net, invalid_params = validate_list_of_dicts(in_list, srp_network_spec)
            if invalid_params:
                mesg = "Invalid parameters in playbook: {}".format(
                    "while processing Network/Arm - "
                    + net_name1
                    + ", under Route Peering - "
                    + cfg[0]["name"]
                    + ", "
                    + "\n".join(invalid_params)
                )
                self.module.fail_json(msg=mesg)
            in_list.remove(item[net_name1])
            item[net_name1].update(in_net[0])

            if item.get(net_name2, "") != "":
                out_list.append(item[net_name2])
                out_net, invalid_params = validate_list_of_dicts(
                    out_list, srp_network_spec
                )
                if invalid_params:
                    mesg = "Invalid parameters in playbook: {}".format(
                        "while processing Network/Arm - "
                        + net_name2
                        + ", under Route Peering - "
                        + cfg[0]["name"]
                        + ", "
                        + "\n".join(invalid_params)
                    )
                    self.module.fail_json(msg=mesg)
                out_list.remove(item[net_name2])
                item[net_name2].update(out_net[0])

            in_list.append(item[net_name1]["profile"])
            # Validate inside and outside network profile dicts from route peering info
            in_net_prof, invalid_params = validate_list_of_dicts(
                in_list, srp_prof1_spec
            )
            if invalid_params:
                mesg = "Invalid parameters in playbook: {}".format(
                    "while processing Profile under Network/Arm - "
                    + net_name1
                    + ", under Route Peering - "
                    + cfg[0]["name"]
                    + ", "
                    + "\n".join(invalid_params)
                )
                self.module.fail_json(msg=mesg)
            in_list.remove(item[net_name1]["profile"])
            item[net_name1]["profile"].update(in_net_prof[0])

            if item.get(net_name2, "") != "":
                out_list.append(item[net_name2]["profile"])
                out_net_prof, invalid_params = validate_list_of_dicts(
                    out_list, srp_prof2_spec
                )
                if invalid_params:
                    mesg = "Invalid parameters in playbook: {}".format(
                        "while processing Profile under Network/Arm - "
                        + net_name2
                        + ", under Route Peering - "
                        + cfg[0]["name"]
                        + ", "
                        + "\n".join(invalid_params)
                    )
                    self.module.fail_json(msg=mesg)

                out_list.remove(item[net_name2]["profile"])
                item[net_name2]["profile"].update(out_net_prof[0])

            # Check if static route information is included under networks/arms. If yes, validate the same

            if item[net_name1]["profile"].get("static_route", "") != "":

                # Static Route is a list of route dicts
                for rt in item[net_name1]["profile"]["static_route"]:
                    in_list.append(rt)
                    in_net_route, invalid_params = validate_list_of_dicts(
                        in_list, srp_static_route_spec
                    )
                    if invalid_params:
                        mesg = "Invalid parameters in playbook: {}".format(
                            "while processing Static Route under Network/Arm - "
                            + net_name1
                            + ", under Route Peering - "
                            + cfg[0]["name"]
                            + ", "
                            + "\n".join(invalid_params)
                        )
                        self.module.fail_json(msg=mesg)

                    in_list.remove(rt)
                    rt.update(in_net_route[0])

            if item.get(net_name2, "") != "":
                if item[net_name2]["profile"].get("static_route", "") != "":
                    # Static Route is a list of route dicts
                    for rt in item[net_name2]["profile"]["static_route"]:
                        out_list.append(rt)
                        out_net_route, invalid_params = validate_list_of_dicts(
                            out_list, srp_static_route_spec
                        )
                        if invalid_params:
                            mesg = "Invalid parameters in playbook: {}".format(
                                "while processing Static Route under Network/Arm - "
                                + net_name2
                                + ", under Route Peering - "
                                + cfg[0]["name"]
                                + ", "
                                + "\n".join(invalid_params)
                            )
                            self.module.fail_json(msg=mesg)

                        out_list.remove(rt)
                        rt.update(out_net_route[0])

    def dcnm_srp_translate_deploy_mode(self, item):

        """
        Routine to translate the deploy_mode string from the playbook format to the payload format. The translated
        value is updated in the 'item' object directly

        Parameters:
            item (dict) : route peering block whose 'deploy_mode' object need to be translated

        Returns:
            None
        """

        trans_dict = {
            "intra_tenant_fw": "IntraTenantFW",
            "inter_tenant_fw": "InterTenantFW",
            "one_arm_adc": "OneArmADC",
            "two_arm_adc": "TwoArmADC",
        }

        if item["deploy_mode"] not in trans_dict.keys():
            mesg = "Invalid 'deploy_mode' = {}, in playbook, Expected values = {}".format(
                item["deploy_mode"], trans_dict.keys()
            )
            self.module.fail_json(msg=mesg)

        return trans_dict[item["deploy_mode"]]

    def dcnm_srp_validate_input(self):

        """
        Routine to validate the given playbook input based on the type of peering.
        This routine updates self.srp_info with validated playbook information by defaulting values
        not included. Since each state has a different config structure, this routine handles the
        validation based on the given state

        Parameters:
            None

        Returns:
            None
        """

        if None is self.config:
            return

        # Inputs will vary for Firewall and ADC service nodes and for each state. Make specific checks
        # for each case.

        cfg = []
        for item in self.config:

            citem = copy.deepcopy(item)

            cfg.append(citem)

            if self.module.params["state"] == "deleted":
                # config for delete state is different. So validate deleted state differently
                self.dcnm_srp_validate_delete_state_input(cfg)
            elif self.module.params["state"] == "query":
                # config for query state is different. So validate query state differently
                self.dcnm_srp_validate_query_state_input(cfg)
            # For 'overridden' state, we can have full config for a peering or just service node name alone.
            # In the formar case go down to 'else' block to validate the full config
            elif (self.module.params["state"] == "overridden") and (
                item.get("name", None) is None
            ):
                # config for overridden state is different. So validate overridden state differently
                self.dcnm_srp_validate_overridden_state_input(cfg)
            else:
                if "deploy_mode" not in item:
                    mesg = "Invalid parameters in playbook: {}".format(
                        "while processing Route Peering - "
                        + item["name"]
                        + ", deploy_mode - Required parameter not found"
                    )
                    self.module.fail_json(msg=mesg)

                # Translate the deploy_mode from playbook format to a format that DCNM expects
                item["deploy_mode"] = self.dcnm_srp_translate_deploy_mode(item)
                citem["deploy_mode"] = item["deploy_mode"]

                if (item["deploy_mode"].lower() == "intratenantfw") or (
                    item["deploy_mode"].lower() == "intertenantfw"
                ):
                    self.dcnm_srp_validate_firewall_input(
                        cfg, item["deploy_mode"].lower()
                    )
                if (item["deploy_mode"].lower() == "onearmadc") or (
                    item["deploy_mode"].lower() == "twoarmadc"
                ):
                    self.dcnm_srp_validate_adc_input(cfg, item["deploy_mode"].lower())
            cfg.remove(citem)

    def dcnm_srp_validate_intra_tenant_firewall_input(self, cfg):

        """
        Routine to validate the playbook input based on Firewall perring type intra-tenant.
        This routine updates self.srp_info with validated intra-tenant firewall related playbook
        information by defaulting values not included

        Parameters:
            cfg (dict): The config from playbook

        Returns:
            None
        """

        srp_spec = dict(
            name=dict(required=True, type="str"),
            node_name=dict(required=True, type="str"),
            deploy_mode=dict(required=True, type="str"),
            inside_network=dict(required=True, type="dict"),
            outside_network=dict(required=True, type="dict"),
            next_hop=dict(required=True, type="ipv4"),
            rev_next_hop=dict(type="ipv4", default=""),
        )

        srp_network_spec = dict(
            vrf=dict(required=True, type="str"),
            name=dict(required=True, type="str"),
            vlan_id=dict(required=True, type="int"),
            profile=dict(required=True, type="dict"),
        )

        srp_prof_spec = dict(
            ipv4_gw=dict(required=True, type="ipv4_subnet"),
            ipv6_gw=dict(type="ipv6_subnet", default=""),
            vlan_name=dict(type="str", default=""),
            int_descr=dict(type="str", default=""),
            tag=dict(type="int", default=12345),
        )

        self.dcnm_srp_validate_and_build_srp_info(
            cfg,
            srp_spec,
            srp_network_spec,
            srp_prof_spec,
            srp_prof_spec,
            "inside_network",
            "outside_network",
        )

    def dcnm_srp_validate_inter_tenant_firewall_input(self, cfg):

        """
        Routine to validate the playbook input based on Firewall perring type inter-tenant.
        This routine updates self.srp_info with validated inter-tenant firewall related playbook
        information by defaulting values not included

        Parameters:
            cfg (dict): The config from playbook

        Returns:
            None
        """

        srp_spec = dict(
            name=dict(required=True, type="str"),
            node_name=dict(required=True, type="str"),
            deploy_mode=dict(required=True, type="str"),
            peering_option=dict(type="str", default="static"),
            inside_network=dict(required=True, type="dict"),
            outside_network=dict(required=True, type="dict"),
        )

        srp_network_spec = dict(
            vrf=dict(required=True, type="str"),
            name=dict(required=True, type="str"),
            vlan_id=dict(required=True, type="int"),
            profile=dict(required=True, type="dict"),
        )

        srp_static_prof_spec = dict(
            ipv4_gw=dict(required=True, type="ipv4_subnet"),
            ipv6_gw=dict(type="ipv6_subnet", default=""),
            vlan_name=dict(type="str", default=""),
            int_descr=dict(type="str", default=""),
            tag=dict(type="int", default=12345),
            static_route=dict(type="list", default=""),
        )

        srp_ebgp_prof_spec = dict(
            ipv4_gw=dict(required=True, type="ipv4_subnet"),
            ipv6_gw=dict(type="ipv6_subnet", default=""),
            vlan_name=dict(type="str", default=""),
            int_descr=dict(type="str", default=""),
            tag=dict(type="int", default=12345),
            ipv4_neighbor=dict(required=True, type="ipv4"),
            ipv4_lo=dict(required=True, type="ipv4"),
            ipv4_vpc_peer_lo=dict(type="ipv4", default=""),
            ipv6_neighbor=dict(type="ipv6", default=""),
            ipv6_lo=dict(type="ipv6", default=""),
            ipv6_vpc_peer_lo=dict(type="ipv6", default=""),
            route_map_tag=dict(type="int", default=12345),
            neigh_int_descr=dict(type="str", default=""),
            local_asn=dict(type="int", default=""),
            adv_host=dict(type="bool", default=True),
        )

        if (cfg[0].get("peering_option", "none") == "none") or (
            cfg[0]["peering_option"].lower() == "static"
        ):
            self.dcnm_srp_validate_and_build_srp_info(
                cfg,
                srp_spec,
                srp_network_spec,
                srp_static_prof_spec,
                srp_static_prof_spec,
                "inside_network",
                "outside_network",
            )
        elif cfg[0]["peering_option"].lower() == "ebgp":
            self.dcnm_srp_validate_and_build_srp_info(
                cfg,
                srp_spec,
                srp_network_spec,
                srp_ebgp_prof_spec,
                srp_ebgp_prof_spec,
                "inside_network",
                "outside_network",
            )

    def dcnm_srp_validate_adc_input(self, cfg, deploy_mode):

        """
        Routine to validate the playbook input based on Loadbalance perring type one-arm and two-arm.
        This routine updates self.srp_info with validated adc related playbook information by defaulting
        values not included

        Parameters:
            cfg (dict): The config from playbook
            deploy_mode (string): Deployment mode identifying the type of ADC

        Returns:
            None
        """

        srp_spec = dict(
            name=dict(required=True, type="str"),
            node_name=dict(required=True, type="str"),
            deploy_mode=dict(required=True, type="str"),
            peering_option=dict(type="str", default="static"),
            first_arm=dict(required=True, type="dict"),
            second_arm=dict(type="dict", default=""),
            rev_next_hop=dict(required=True, type="ipv4"),
        )

        srp_network_spec = dict(
            vrf=dict(required=True, type="str"),
            name=dict(required=True, type="str"),
            vlan_id=dict(required=True, type="int"),
            profile=dict(required=True, type="dict"),
        )

        srp_static_prof_spec = dict(
            ipv4_gw=dict(required=True, type="ipv4_subnet"),
            ipv6_gw=dict(type="ipv6_subnet", default=""),
            vlan_name=dict(type="str", default=""),
            int_descr=dict(type="str", default=""),
            tag=dict(type="int", default=12345),
            static_route=dict(type="list", default=""),
        )

        srp_ebgp_first_arm_prof_spec = dict(
            ipv4_gw=dict(required=True, type="ipv4_subnet"),
            ipv6_gw=dict(type="ipv6_subnet", default=""),
            vlan_name=dict(type="str", default=""),
            int_descr=dict(type="str", default=""),
            tag=dict(type="int", default=12345),
            ipv4_neighbor=dict(required=True, type="ipv4"),
            ipv4_lo=dict(required=True, type="ipv4"),
            ipv4_vpc_peer_lo=dict(type="ipv4", default=""),
            ipv6_neighbor=dict(type="ipv6", default=""),
            ipv6_lo=dict(type="ipv6", default=""),
            ipv6_vpc_peer_lo=dict(type="ipv6", default=""),
            route_map_tag=dict(type="int", default=12345),
            neigh_int_descr=dict(type="str", default=""),
            local_asn=dict(type="int", default=""),
            adv_host=dict(type="bool", default=True),
        )

        srp_ebgp_second_arm_prof_spec = dict(
            ipv4_gw=dict(required=True, type="ipv4_subnet"),
            ipv6_gw=dict(type="ipv6_subnet", default=""),
            vlan_name=dict(type="str", default=""),
            int_descr=dict(type="str", default=""),
            tag=dict(type="int", default=12345),
        )

        if (cfg[0].get("peering_option", "none") == "none") or (
            cfg[0]["peering_option"].lower() == "static"
        ):
            self.dcnm_srp_validate_and_build_srp_info(
                cfg,
                srp_spec,
                srp_network_spec,
                srp_static_prof_spec,
                srp_static_prof_spec,
                "first_arm",
                "second_arm",
            )
        elif cfg[0]["peering_option"].lower() == "ebgp":
            self.dcnm_srp_validate_and_build_srp_info(
                cfg,
                srp_spec,
                srp_network_spec,
                srp_ebgp_first_arm_prof_spec,
                srp_ebgp_second_arm_prof_spec,
                "first_arm",
                "second_arm",
            )

    def dcnm_srp_validate_firewall_input(self, cfg, deploy_mode):

        if deploy_mode == "intratenantfw":
            self.dcnm_srp_validate_intra_tenant_firewall_input(cfg)
        elif deploy_mode == "intertenantfw":
            self.dcnm_srp_validate_inter_tenant_firewall_input(cfg)

    def dcnm_srp_validate_delete_state_input(self, cfg):

        """
        Playbook input will be different for differnt states. This routine validates the delete state
        input. This routine updates self.srp_info with validated playbook information related to delete
        state.

        Parameters:
            cfg (dict): The config from playbook

        Returns:
            None
        """

        srp_delete_spec = dict(
            name=dict(required=True, type="str"),
            node_name=dict(required=True, type="str"),
        )

        srp_info, invalid_params = validate_list_of_dicts(cfg, srp_delete_spec)
        if invalid_params:
            if cfg[0].get("name", " ") != " ":
                mesg = "Invalid parameters in playbook: {}".format(
                    "while processing Route Peering -  "
                    + cfg[0]["name"]
                    + ", "
                    + "".join(invalid_params)
                )
            else:
                mesg = "Invalid parameters in playbook: {}".format(
                    "while processing Route Peering -  Unknown, "
                    + "".join(invalid_params)
                )
            self.module.fail_json(msg=mesg)

        self.srp_info.extend(srp_info)

    def dcnm_srp_validate_query_state_input(self, cfg):

        """
        Playbook input will be different for differnt states. This routine validates the query state
        input. This routine updates self.srp_info with validated playbook information related to query
        state.

        Parameters:
            cfg (dict): The config from playbook

        Returns:
           None
        """

        srp_query_spec = dict(
            name=dict(type="str", default="None"),
            node_name=dict(required=True, type="str"),
        )

        srp_info, invalid_params = validate_list_of_dicts(cfg, srp_query_spec)
        if invalid_params:
            mesg = "Invalid parameters in playbook: {}".format(
                "while processing Route Peering -  "
                + cfg[0]["name"]
                + ", "
                + "\n".join(invalid_params)
            )
            self.module.fail_json(msg=mesg)

        self.srp_info.extend(srp_info)

    def dcnm_srp_validate_overridden_state_input(self, cfg):

        """
        Playbook input will be different for differnt states. This routine validates the overridden state
        input. This routine updates self.srp_info with validated playbook information related to overridden
        state.

        Parameters:
            cfg	(dict): The config from playbook

        Returns:
            None
        """

        srp_overridden_spec = dict(
            name=dict(required=False, type="str", default=""),
            node_name=dict(required=False, type="str", default=""),
        )

        srp_info, invalid_params = validate_list_of_dicts(cfg, srp_overridden_spec)
        if invalid_params:
            mesg = "Invalid parameters in playbook: {}".format(
                "while processing Route Peering -  "
                + cfg[0]["name"]
                + ", "
                + "\n".join(invalid_params)
            )
            self.module.fail_json(msg=mesg)

        self.srp_info.extend(srp_info)

    def dcnm_srp_get_payload_route_info(self, srp, srp_payload):

        """
        This routine builds the route peering payload information from the playbook input
        that is related to static of ebgp route information.

        Parameters:
            srp (dict): The route peering information from self.want
            srp_payload (dict): Route peering information to be filled from the given srp config

        Returns:
            None
        """

        in_route_info = {"nvPairs": {}}

        out_route_info = {"nvPairs": {}}

        if (srp["deploy_mode"].lower() == "intratenantfw") or (
            srp["deploy_mode"].lower() == "intertenantfw"
        ):
            net_name1 = "inside_network"
            net_name2 = "outside_network"
        else:
            net_name1 = "first_arm"
            net_name2 = "second_arm"

        srp_payload["routes"] = []
        if srp_payload["peeringOption"] == "StaticPeering":

            srp_payload["routes"].append(in_route_info)
            srp_payload["routes"][0]["templateName"] = "service_static_route"

            nv = srp_payload["routes"][0]["nvPairs"]

            nv["VRF_NAME"] = srp[net_name1]["vrf"]
            srp_payload["routes"][0]["vrfName"] = srp[net_name1]["vrf"]

            # Build Multiroutes object
            routes = srp[net_name1]["profile"]["static_route"]
            multi_routes = ""

            for rt in routes:
                hops = rt["next_hop"]
                for nh in hops:
                    multi_routes += rt["subnet"] + "," + nh + "\n"

            nv["MULTI_ROUTES"] = multi_routes.rstrip("\n")

            if srp_payload["deploymentMode"] == "InterTenantFW":

                srp_payload["routes"].append(out_route_info)
                srp_payload["routes"][1]["templateName"] = "service_static_route"

                nv = srp_payload["routes"][1]["nvPairs"]

                nv["VRF_NAME"] = srp[net_name2]["vrf"]
                srp_payload["routes"][1]["vrfName"] = srp[net_name2]["vrf"]

                # Build Multiroutes object
                routes = srp[net_name2]["profile"]["static_route"]
                multi_routes = ""

                for rt in routes:
                    hops = rt["next_hop"]
                    for nh in hops:
                        multi_routes += rt["subnet"] + "," + nh + "\n"

                nv["MULTI_ROUTES"] = multi_routes.rstrip("\n")

        elif srp_payload["peeringOption"] == "EBGPDynamicPeering":

            srp_payload["routes"].append(in_route_info)
            srp_payload["routes"][0]["templateName"] = "service_ebgp_route"

            nv = srp_payload["routes"][0]["nvPairs"]

            nv["NEIGHBOR_IP"] = srp[net_name1]["profile"]["ipv4_neighbor"]
            nv["LOOPBACK_IP"] = srp[net_name1]["profile"]["ipv4_lo"]
            nv["PEER_LOOPBACK_IP"] = srp[net_name1]["profile"]["ipv4_vpc_peer_lo"]
            nv["NEIGHBOR_IPV6"] = srp[net_name1]["profile"]["ipv6_neighbor"]
            nv["LOOPBACK_IPV6"] = srp[net_name1]["profile"]["ipv6_lo"]
            nv["PEER_LOOPBACK_IPV6"] = srp[net_name1]["profile"]["ipv6_vpc_peer_lo"]
            nv["ROUTE_MAP_TAG"] = srp[net_name1]["profile"]["route_map_tag"]
            nv["DESC"] = srp[net_name1]["profile"]["neigh_int_descr"]
            nv["LOCAL_ASN"] = srp[net_name1]["profile"]["local_asn"]
            nv["ADVERTISE_HOST_ROUTE"] = srp[net_name1]["profile"]["adv_host"]
            nv["ADMIN_STATE"] = True
            nv["VRF_NAME"] = srp[net_name1]["vrf"]

            srp_payload["routes"][0]["vrfName"] = srp[net_name1]["vrf"]

            if srp_payload["deploymentMode"] == "InterTenantFW":

                srp_payload["routes"].append(out_route_info)
                srp_payload["routes"][1]["templateName"] = "service_ebgp_route"

                nv = srp_payload["routes"][1]["nvPairs"]

                nv["NEIGHBOR_IP"] = srp[net_name2]["profile"]["ipv4_neighbor"]
                nv["LOOPBACK_IP"] = srp[net_name2]["profile"]["ipv4_lo"]
                nv["PEER_LOOPBACK_IP"] = srp[net_name2]["profile"]["ipv4_vpc_peer_lo"]
                nv["NEIGHBOR_IPV6"] = srp[net_name2]["profile"]["ipv6_neighbor"]
                nv["LOOPBACK_IPV6"] = srp[net_name2]["profile"]["ipv6_lo"]
                nv["PEER_LOOPBACK_IPV6"] = srp[net_name2]["profile"]["ipv6_vpc_peer_lo"]
                nv["ROUTE_MAP_TAG"] = srp[net_name2]["profile"]["route_map_tag"]
                nv["DESC"] = srp[net_name2]["profile"]["neigh_int_descr"]
                nv["LOCAL_ASN"] = srp[net_name2]["profile"]["local_asn"]
                nv["ADVERTISE_HOST_ROUTE"] = srp[net_name2]["profile"]["adv_host"]
                nv["ADMIN_STATE"] = True
                nv["VRF_NAME"] = srp[net_name2]["vrf"]

                srp_payload["routes"][1]["vrfName"] = srp[net_name2]["vrf"]

    def dcnm_srp_get_common_payload(self, srp, deploy_mode):

        """
        This routine builds the common part of the route peering payload. By common we mean information that is common
        to both inside and outside networks or one-arm and two-arm adc.

        Parameters:
            srp (dict): Route peering information from self.want
            deploy_mode (string): Rourte peering deployment mode

        Returns:
            srp_payload (dict): Route peering common payload information populated from playbook configuration
        """

        in_network_defaults = {
            "templateName": "Service_Network_Universal",
            "nvPairs": {
                "isLayer2Only": False,
                "suppressArp": False,
                "enableIR": False,
                "trmEnabled": False,
                "rtBothAuto": False,
            },
        }

        out_network_defaults = {
            "templateName": "Service_Network_Universal",
            "nvPairs": {
                "isLayer2Only": False,
                "suppressArp": False,
                "enableIR": False,
                "trmEnabled": False,
                "rtBothAuto": False,
            },
        }

        srp_payload = {"serviceNetworks": [], "enabled": self.attach}

        if (deploy_mode == "intratenantfw") or (deploy_mode == "intertenantfw"):
            net_name1 = "inside_network"
            net_name2 = "outside_network"
            networkType1 = "InsideNetworkFW"
            networkType2 = "OutsideNetworkFW"
            serviceNodeType = "Firewall"
        else:
            net_name1 = "first_arm"
            net_name2 = "second_arm"
            networkType1 = "ArmOneADC"
            networkType2 = "ArmTwoADC"
            serviceNodeType = "ADC"

        # Global
        srp_payload["peeringName"] = srp["name"]
        srp_payload["deploymentMode"] = srp["deploy_mode"]
        srp_payload["serviceNodeType"] = serviceNodeType

        # Inside Network
        srp_payload["serviceNetworks"].append(in_network_defaults)

        srp_payload["serviceNetworks"][0]["vrfName"] = srp[net_name1]["vrf"]
        srp_payload["serviceNetworks"][0]["networkType"] = networkType1
        srp_payload["serviceNetworks"][0]["networkName"] = srp[net_name1]["name"]
        srp_payload["serviceNetworks"][0]["vlanId"] = srp[net_name1]["vlan_id"]

        # Inside Network Profile
        srp_payload["serviceNetworks"][0]["nvPairs"]["gatewayIpAddress"] = srp[
            net_name1
        ]["profile"]["ipv4_gw"]
        srp_payload["serviceNetworks"][0]["nvPairs"]["gatewayIpV6Address"] = srp[
            net_name1
        ]["profile"]["ipv6_gw"]
        srp_payload["serviceNetworks"][0]["nvPairs"]["vlanName"] = srp[net_name1][
            "profile"
        ]["vlan_name"]
        srp_payload["serviceNetworks"][0]["nvPairs"]["intfDescription"] = srp[
            net_name1
        ]["profile"]["int_descr"]
        srp_payload["serviceNetworks"][0]["nvPairs"]["tag"] = srp[net_name1]["profile"][
            "tag"
        ]
        srp_payload["serviceNetworks"][0]["nvPairs"]["vlanId"] = srp[net_name1][
            "vlan_id"
        ]

        if deploy_mode != "onearmadc":

            # Outside Network
            srp_payload["serviceNetworks"].append(out_network_defaults)

            srp_payload["serviceNetworks"][1]["vrfName"] = srp[net_name2]["vrf"]
            srp_payload["serviceNetworks"][1]["networkType"] = networkType2
            srp_payload["serviceNetworks"][1]["networkName"] = srp[net_name2]["name"]
            srp_payload["serviceNetworks"][1]["vlanId"] = srp[net_name2]["vlan_id"]

            # Outside Network Profile
            srp_payload["serviceNetworks"][1]["nvPairs"]["gatewayIpAddress"] = srp[
                net_name2
            ]["profile"]["ipv4_gw"]
            srp_payload["serviceNetworks"][1]["nvPairs"]["gatewayIpV6Address"] = srp[
                net_name2
            ]["profile"]["ipv6_gw"]
            srp_payload["serviceNetworks"][1]["nvPairs"]["vlanName"] = srp[net_name2][
                "profile"
            ]["vlan_name"]
            srp_payload["serviceNetworks"][1]["nvPairs"]["intfDescription"] = srp[
                net_name2
            ]["profile"]["int_descr"]
            srp_payload["serviceNetworks"][1]["nvPairs"]["tag"] = srp[net_name2][
                "profile"
            ]["tag"]
            srp_payload["serviceNetworks"][1]["nvPairs"]["vlanId"] = srp[net_name2][
                "vlan_id"
            ]

        # Service Node and Fabric details
        srp_payload["serviceNodeName"] = srp["node_name"]
        srp_payload["attachedFabricName"] = self.module.params["fabric"]
        srp_payload["fabricName"] = self.module.params["service_fabric"]

        return srp_payload

    def dcnm_get_srp_payload(self, srp):

        """
        This routine builds the complete payload step-by-step first by building common part, then other
        parts based on the deploy_mode and peering_option.

        Parameters:
            srp (dict): Route peering information

        Returns:
            self.srp_payuload (dict): SRP payload information populated with appropriate data from playbook config
        """

        deploy_mode = srp["deploy_mode"].lower()
        srp_payload = self.dcnm_srp_get_common_payload(srp, deploy_mode)

        # Based on the deployment mode, add the other required objects
        if deploy_mode == "intratenantfw":

            srp_payload["peeringOption"] = "None"
            # Add NextHop and Reverse NextHop
            srp_payload["nextHopIp"] = srp["next_hop"]
            srp_payload["reverseNextHopIp"] = srp["rev_next_hop"]
        elif deploy_mode == "intertenantfw":

            if srp["peering_option"] == "static":
                srp_payload["peeringOption"] = "StaticPeering"
            else:
                srp_payload["peeringOption"] = "EBGPDynamicPeering"
            self.dcnm_srp_get_payload_route_info(srp, srp_payload)
        elif deploy_mode == "onearmadc":

            if srp["peering_option"] == "static":
                srp_payload["peeringOption"] = "StaticPeering"
            else:
                srp_payload["peeringOption"] = "EBGPDynamicPeering"
            srp_payload["reverseNextHopIp"] = srp["rev_next_hop"]
            self.dcnm_srp_get_payload_route_info(srp, srp_payload)
        elif deploy_mode == "twoarmadc":

            if srp["peering_option"] == "static":
                srp_payload["peeringOption"] = "StaticPeering"
            else:
                srp_payload["peeringOption"] = "EBGPDynamicPeering"
            srp_payload["reverseNextHopIp"] = srp["rev_next_hop"]
            self.dcnm_srp_get_payload_route_info(srp, srp_payload)

        return srp_payload

    def dcnm_srp_update_route_info(self, want, have, cfg):

        """
        This routine is invoked after self.want is populated based on playbook info. For merging route peerings
        all the information that is not included in the playbook must be left as is and the information which
        is included must be updated. This routine checks for playbook info and updates self.want as required
        This routine updates self.want with appriopriate route information from playbook and self.have based on
        objects included in the playbook.

        Parameters:
            cfg (dict): The config from playbook
            want (dict): Route peering payload information populated from playbook config
            have (dict): Rourte peering information that exists on the DCNM server

        Returns:
            None
        """

        if (want["deploymentMode"].lower() == "intratenantfw") or (
            want["deploymentMode"].lower() == "intertenantfw"
        ):
            net_name1 = "inside_network"
            net_name2 = "outside_network"
        else:
            net_name1 = "first_arm"
            net_name2 = "second_arm"

        # Check the peeringOption and if not same, just leave 'want' as it is and do not try to compare it with
        # 'have' since the fields are completely different

        if want["peeringOption"] != have["peeringOption"]:
            return

        # All objects that are not included in the playbook will be copied from have to leave them undisturbed
        if cfg.get("peering_option", None) is None:
            want["peeringOption"] = have["peeringOption"]

        if want["peeringOption"] == "StaticPeering":

            if cfg.get("vrf", None) is None:
                want["routes"][0]["vrfName"] = have["routes"][0]["vrfName"]

            wnv = want["routes"][0]["nvPairs"]
            hnv = have["routes"][0]["nvPairs"]

            if cfg.get("vrf", None) is None:
                wnv["VRF_NAME"] = hnv["VRF_NAME"]

            if cfg[net_name1]["profile"].get("static_route", None) is None:
                wnv["MULTI_ROUTES"] = hnv["MULTI_ROUTES"]

            if want["deploymentMode"] == "InterTenantFW":

                if cfg.get("vrf", None) is None:
                    want["routes"][1]["vrfName"] = have["routes"][1]["vrfName"]

                wnv = want["routes"][1]["nvPairs"]
                hnv = have["routes"][1]["nvPairs"]

                if cfg.get("vrf", None) is None:
                    wnv["VRF_NAME"] = hnv["VRF_NAME"]

                if cfg[net_name2]["profile"].get("static_route", None) is None:
                    wnv["MULTI_ROUTES"] = hnv["MULTI_ROUTES"]

        elif want["peeringOption"] == "EBGPDynamicPeering":

            wnv = want["routes"][0]["nvPairs"]
            hnv = have["routes"][0]["nvPairs"]

            if cfg[net_name1]["profile"].get("ipv4_neighbor", None) is None:
                wnv["NEIGHBOR_IP"] = hnv["NEIGHBOR_IP"]

            if cfg[net_name1]["profile"].get("ipv4_lo", None) is None:
                wnv["LOOPBACK_IP"] = hnv["LOOPBACK_IP"]

            if cfg[net_name1]["profile"].get("ipv4_vpc_peer_lo", None) is None:
                wnv["PEER_LOOPBACK_IP"] = hnv["PEER_LOOPBACK_IP"]

            if cfg[net_name1]["profile"].get("ipv6_neighbor", None) is None:
                wnv["NEIGHBOR_IPV6"] = hnv["NEIGHBOR_IPV6"]

            if cfg[net_name1]["profile"].get("ipv6_lo", None) is None:
                wnv["LOOPBACK_IPV6"] = hnv["LOOPBACK_IPV6"]

            if cfg[net_name1]["profile"].get("ipv6_vpc_peer_lo", None) is None:
                wnv["PEER_LOOPBACK_IPV6"] = hnv["PEER_LOOPBACK_IPV6"]

            if cfg[net_name1]["profile"].get("route_map_tag", None) is None:
                wnv["ROUTE_MAP_TAG"] = hnv["ROUTE_MAP_TAG"]

            if cfg[net_name1]["profile"].get("neigh_int_descr", None) is None:
                wnv["DESC"] = hnv["DESC"]

            if cfg[net_name1]["profile"].get("local_asn", None) is None:
                wnv["LOCAL_ASN"] = hnv["LOCAL_ASN"]

            if cfg[net_name1]["profile"].get("adv_host", None) is None:
                wnv["ADVERTISE_HOST_ROUTE"] = hnv["ADVERTISE_HOST_ROUTE"]

            if cfg.get("vrf", None) is None:
                wnv["VRF_NAME"] = hnv["VRF_NAME"]

            if cfg.get("vrf", None) is None:
                want["routes"][0]["vrfName"] = have["routes"][0]["vrfName"]

            if want["deploymentMode"] == "InterTenantFW":

                wnv = want["routes"][1]["nvPairs"]
                hnv = have["routes"][1]["nvPairs"]

                if cfg[net_name2]["profile"].get("ipv4_neighbor", None) is None:
                    wnv["NEIGHBOR_IP"] = hnv["NEIGHBOR_IP"]

                if cfg[net_name2]["profile"].get("ipv4_lo", None) is None:
                    wnv["LOOPBACK_IP"] = hnv["LOOPBACK_IP"]

                if cfg[net_name2]["profile"].get("ipv4_vpc_peer_lo", None) is None:
                    wnv["PEER_LOOPBACK_IP"] = hnv["PEER_LOOPBACK_IP"]

                if cfg[net_name2]["profile"].get("ipv6_neighbor", None) is None:
                    wnv["NEIGHBOR_IPV6"] = hnv["NEIGHBOR_IPV6"]

                if cfg[net_name2]["profile"].get("ipv6_lo", None) is None:
                    wnv["LOOPBACK_IPV6"] = hnv["LOOPBACK_IPV6"]

                if cfg[net_name2]["profile"].get("ipv6_vpc_peer_lo", None) is None:
                    wnv["PEER_LOOPBACK_IPV6"] = hnv["PEER_LOOPBACK_IPV6"]

                if cfg[net_name2]["profile"].get("route_map_tag", None) is None:
                    wnv["ROUTE_MAP_TAG"] = hnv["ROUTE_MAP_TAG"]

                if cfg[net_name2]["profile"].get("neigh_int_descr", None) is None:
                    wnv["DESC"] = hnv["DESC"]

                if cfg[net_name2]["profile"].get("loacl_asn", None) is None:
                    wnv["LOCAL_ASN"] = hnv["LOCAL_ASN"]

                if cfg[net_name2]["profile"].get("adv_host", None) is None:
                    wnv["ADVERTISE_HOST_ROUTE"] = hnv["ADVERTISE_HOST_ROUTE"]

                if cfg.get("vrf", None) is None:
                    wnv["VRF_NAME"] = hnv["VRF_NAME"]

                if cfg.get("vrf", None) is None:
                    want["routes"][1]["vrfName"] = have["routes"][1]["vrfName"]

    def dcnm_srp_update_common_info(self, want, have, cfg):

        """
        Routine to update the common part of the route peering information in self.want
        This routine updates self.want with common information from playbook and self.have based on objects
        included in the playbook.

        Parameters:
            cfg (dict): The config from playbook
            want (dict): Route peering payload information populated from playbook config
            have (dict): Rourte peering information that exists on the DCNM server

        Returns:
            None
        """

        if (want["deploymentMode"].lower() == "intratenantfw") or (
            want["deploymentMode"].lower() == "intertenantfw"
        ):
            net_name1 = "inside_network"
            net_name2 = "outside_network"
        else:
            net_name1 = "first_arm"
            net_name2 = "second_arm"

        # All objects that are not included in the playbook will be copied from have to leave them undisturbed
        # Inside Network
        if cfg[net_name1].get("vrf", None) is None:
            want["serviceNetworks"][0]["vrfName"] = have["serviceNetworks"][0][
                "vrfName"
            ]

        if cfg[net_name1].get("name", None) is None:
            want["serviceNetworks"][0]["networkName"] = have["serviceNetworks"][0][
                "networkName"
            ]

        if cfg[net_name1].get("vlan_id", None) is None:
            want["serviceNetworks"][0]["vlanId"] = have["serviceNetworks"][0]["vlanId"]

        # Inside Network Profile
        if cfg[net_name1]["profile"].get("ipv4_gw", None) is None:
            want["serviceNetworks"][0]["nvPairs"]["gatewayIpAddress"] = have[
                "serviceNetworks"
            ][0]["nvPairs"]["gatewayIpAddress"]

        if cfg[net_name1]["profile"].get("ipv6_gw", None) is None:
            want["serviceNetworks"][0]["nvPairs"]["gatewayIpV6Address"] = have[
                "serviceNetworks"
            ][0]["nvPairs"]["gatewayIpV6Address"]

        if cfg[net_name1]["profile"].get("vlan_name", None) is None:
            want["serviceNetworks"][0]["nvPairs"]["vlanName"] = have["serviceNetworks"][
                0
            ]["nvPairs"]["vlanName"]

        if cfg[net_name1]["profile"].get("int_descr", None) is None:
            hif_desc = have["serviceNetworks"][0]["nvPairs"]["intfDescription"].split(
                " "
            )[:-1]
            want["serviceNetworks"][0]["nvPairs"]["intfDescription"] = " ".join(
                hif_desc
            )

        if cfg[net_name1]["profile"].get("tag", None) is None:
            want["serviceNetworks"][0]["nvPairs"]["tag"] = have["serviceNetworks"][0][
                "nvPairs"
            ]["tag"]

        if cfg[net_name1]["profile"].get("vlan_id", None) is None:
            want["serviceNetworks"][0]["nvPairs"]["vlanId"] = have["serviceNetworks"][
                0
            ]["nvPairs"]["vlanId"]

        if want["deploymentMode"].lower() != "onearmadc":

            # Outside Network
            if cfg[net_name2].get("vrf", None) is None:
                want["serviceNetworks"][1]["vrfName"] = have["serviceNetworks"][1][
                    "vrfName"
                ]

            if cfg[net_name2].get("name", None) is None:
                want["serviceNetworks"][1]["networkName"] = have["serviceNetworks"][1][
                    "networkName"
                ]

            if cfg[net_name2].get("vlan_id", None) is None:
                want["serviceNetworks"][1]["vlanId"] = have["serviceNetworks"][1][
                    "vlanId"
                ]

            # Outside Network Profile
            if cfg[net_name2]["profile"].get("ipv4_gw", None) is None:
                want["serviceNetworks"][1]["nvPairs"]["gatewayIpAddress"] = have[
                    "serviceNetworks"
                ][1]["nvPairs"]["gatewayIpAddress"]

            if cfg[net_name2]["profile"].get("ipv6_gw", None) is None:
                want["serviceNetworks"][1]["nvPairs"]["gatewayIpV6Address"] = have[
                    "serviceNetworks"
                ][1]["nvPairs"]["gatewayIpV6Address"]

            if cfg[net_name2]["profile"].get("vlan_name", None) is None:
                want["serviceNetworks"][1]["nvPairs"]["vlanName"] = have[
                    "serviceNetworks"
                ][1]["nvPairs"]["vlanName"]

            if cfg[net_name2]["profile"].get("int_descr", None) is None:
                hif_desc = have["serviceNetworks"][1]["nvPairs"][
                    "intfDescription"
                ].split(" ")[:-1]
                want["serviceNetworks"][1]["nvPairs"]["intfDescription"] = " ".join(
                    hif_desc
                )

            if cfg[net_name2]["profile"].get("tag", None) is None:
                want["serviceNetworks"][1]["nvPairs"]["tag"] = have["serviceNetworks"][
                    1
                ]["nvPairs"]["tag"]

            if cfg[net_name2]["profile"].get("vlan_id", None) is None:
                want["serviceNetworks"][1]["nvPairs"]["vlanId"] = have[
                    "serviceNetworks"
                ][1]["nvPairs"]["vlanId"]

        # if self.module.params["attach"] is "default, then attach is not given in Playbook
        if self.module.params["attach"] == "default":
            want["enabled"] = have["enabled"]

    def dcnm_srp_update_want(self):

        """
        Routine to compare want and have and make approriate changes to want. This routine checks the existing
        informationm with the config from playbook and populates the payloads in self.want apropriately.
        This routine updates self.want with final paylload information after comparing self.want and self.have and
        the playbook information.

        Parameters:
            None

        Returns:
            None
        """

        # only for 'merged' state we need to update the objects that are not included in playbook with
        # values from self.have.

        if self.module.params["state"] != "merged":
            return

        if self.want == []:
            return

        for srp in self.want:

            # Get the matching have to copy values if required
            match_have = [
                have
                for have in self.have
                if (
                    (srp["peeringName"] == have["peeringName"])
                    and (srp["fabricName"] == have["fabricName"])
                    and (srp["serviceNodeName"] == have["serviceNodeName"])
                    and (srp["attachedFabricName"] == have["attachedFabricName"])
                )
            ]
            if match_have == []:
                continue

            # Get the SRP from self.config to check if a particular object is included or not
            match_cfg = [
                cfg
                for cfg in self.config
                if (
                    (srp["peeringName"] == cfg["name"])
                    and (srp["fabricName"] == self.module.params["service_fabric"])
                    and (srp["serviceNodeName"] == cfg["node_name"])
                    and (srp["attachedFabricName"] == self.module.params["fabric"])
                )
            ]
            if match_cfg == []:
                continue

            self.dcnm_srp_update_common_info(srp, match_have[0], match_cfg[0])
            self.dcnm_srp_update_route_info(srp, match_have[0], match_cfg[0])

    def dcnm_srp_get_want(self):

        """
        This routine updates self.want with the payload information based on the playbook configuration.

        Parameters:
            None

        Returns:
            None
        """

        if None is self.config:
            return

        if not self.srp_info:
            return

        # self.srp_info is a list of directories each having config related to a particular srp
        for srp_elem in self.srp_info:
            # If route peering name is not given, then that means we are handling the case of Playbook
            # including just the service node name. In such a casse we don't have to worry about filling want
            if srp_elem.get("name", "") == "":
                continue
            srp_payload = self.dcnm_get_srp_payload(srp_elem)
            if srp_payload not in self.want:
                self.want.append(srp_payload)

    def dcnm_srp_get_srp_info_with_service_node(self, node_name):

        """
        Routine to get all route peerings based on the Service Node information included in the playbook.

        Parameters:
            node_name (string): service node name to fetch the route peerings information from

        Returns:
            resp["DATA"] (dict): All route peerings present on the specified service node
        """

        path = (
            "/appcenter/Cisco/elasticservice/elasticservice-api/fabrics/"
            + self.module.params["service_fabric"]
            + "/service-nodes/"
            + node_name
            + "/peerings/"
            + self.module.params["fabric"]
        )

        retries = 0
        while retries < 5:
            retries += 1
            resp = dcnm_send(self.module, "GET", path)

            if resp and resp["RETURN_CODE"] != 200:
                time.sleep(10)
                continue
            else:
                break

        if resp and (resp["RETURN_CODE"] == 200) and resp["DATA"]:
            resp["RETRIES"] = retries
            return resp["DATA"]
        else:
            return []

    def dcnm_srp_get_service_nodes_from_dcnm(self):

        """
        Routine to get list of all service nodes from DCNM.

        Parameters:
            None

        Returns:
            resp["DATA"] (dict): All service nodes on the specified fabric
        """

        path = (
            "/appcenter/Cisco/elasticservice/elasticservice-api/?attached-fabric="
            + self.module.params["fabric"]
        )

        retries = 0
        while retries < 5:
            retries += 1
            resp = dcnm_send(self.module, "GET", path)

            if resp and resp["RETURN_CODE"] != 200:
                time.sleep(10)
                continue
            else:
                break

        if resp and (resp["RETURN_CODE"] == 200) and resp["DATA"]:
            resp["RETRIES"] = retries
            return resp["DATA"]
        else:
            return []

    def dcnm_srp_get_srp_info_from_dcnm(self, srp, srp_type):

        """
        Routine to get existing Route peering information from DCNM which matches the given SRP.

        Parameters:
            srp  (dict): Route peering information
            srp_type (string): String indicating whether the 'srp' passed is in 'PLAYBOOK' format
                            or 'PAYLOAD' format
        Returns:
            resp["DATA"] (dict): SRP informatikon obtained from the DCNM server if it exists
            [] otherwise
        """

        if srp_type == "PAYLOAD":
            path = (
                "/appcenter/Cisco/elasticservice/elasticservice-api/fabrics/"
                + srp["fabricName"]
                + "/service-nodes/"
                + srp["serviceNodeName"]
                + "/peerings/"
                + srp["attachedFabricName"]
                + "/"
                + srp["peeringName"]
            )
        else:
            path = (
                "/appcenter/Cisco/elasticservice/elasticservice-api/fabrics/"
                + self.module.params["service_fabric"]
                + "/service-nodes/"
                + srp["node_name"]
                + "/peerings/"
                + self.module.params["fabric"]
                + "/"
                + srp["name"]
            )

        retries = 0
        while retries < 5:
            retries += 1
            resp = dcnm_send(self.module, "GET", path)

            if resp and resp["RETURN_CODE"] != 200:
                # Check if the error is "ResourceNotFound". In that case we can return without
                # retrying.
                if resp.get("error", None) is not None:
                    if resp["error"].get("code") == "ResourceNotFound":
                        break
                time.sleep(10)
                continue
            else:
                break

        if resp and (resp["RETURN_CODE"] == 200) and resp["DATA"]:
            resp["RETRIES"] = retries
            return resp["DATA"]
        else:
            return []

    def dcnm_srp_get_have(self):

        """
        Routine to get exisitng roue peering information from DCNM that matches information in self.want.
        This routine updates self.have with all the route peerings that match the given playbook configuration

        Parameters:
            None

        Returns:
            None
        """

        if self.want == []:
            return

        for srp in self.want:
            have = self.dcnm_srp_get_srp_info_from_dcnm(srp, "PAYLOAD")
            if (have != []) and (have not in self.have):
                self.have.append(have)

    def dcnm_srp_compare_common_info(self, want, have):

        """
        Routine to compare common information from want and have to decide if the information from self.want is to
        be added to the create list/replace list or not.

        Parameters:
            want (dict): SRP Payload information populated using playbook config
            have (dict): SRP information existing on the DCNM server

        Returns:
            DCNM_SRP_NO_MATCH (string): if information in want and have don't match
            DCNM_SRP_MATCH (string): if want and have match
            mismatch_reasons (list): A list containing strings identifying which objects did not match or []
        """

        mismatch_reasons = []

        if want["deploymentMode"] != have["deploymentMode"]:
            mismatch_reasons.append("DCNM_SRP_DM_NO_MATCH")

        # Global
        if want["serviceNodeType"] != have["serviceNodeType"]:
            mismatch_reasons.append("DCNM_SRP_SNT_NO_MATCH")

        # Inside Network
        if (
            want["serviceNetworks"][0]["vrfName"]
            != have["serviceNetworks"][0]["vrfName"]
        ):
            mismatch_reasons.append("DCNM_SRP_IN_VRF_NO_MATCH")

        if (
            want["serviceNetworks"][0]["networkType"]
            != have["serviceNetworks"][0]["networkType"]
        ):
            mismatch_reasons.append("DCNM_SRP_IN_NT_NO_MATCH")

        if (
            want["serviceNetworks"][0]["networkName"]
            != have["serviceNetworks"][0]["networkName"]
        ):
            mismatch_reasons.append("DCNM_SRP_IN_NN_NO_MATCH")

        if want["serviceNetworks"][0]["vlanId"] != have["serviceNetworks"][0]["vlanId"]:
            mismatch_reasons.append("DCNM_SRP_IN_VID_NO_MATCH")

        # Inside Network Profile
        if (
            want["serviceNetworks"][0]["nvPairs"]["gatewayIpAddress"]
            != have["serviceNetworks"][0]["nvPairs"]["gatewayIpAddress"]
        ):
            mismatch_reasons.append("DCNM_SRP_IN_IPV4GW_NO_MATCH")
        if (
            want["serviceNetworks"][0]["nvPairs"]["gatewayIpV6Address"]
            != have["serviceNetworks"][0]["nvPairs"]["gatewayIpV6Address"]
        ):
            mismatch_reasons.append("DCNM_SRP_IN_IPV6GW_NO_MATCH")
        if (
            want["serviceNetworks"][0]["nvPairs"]["vlanName"]
            != have["serviceNetworks"][0]["nvPairs"]["vlanName"]
        ):
            mismatch_reasons.append("DCNM_SRP_IN_VNAME_NO_MATCH")

        # When we get the SRP inmformation from have, the intfDescription would have been modified and some meta data added. so ignore the meta data
        # when comparing the interface descriptions
        if want["serviceNetworks"][0]["nvPairs"]["intfDescription"] != "":
            wif_desc = want["serviceNetworks"][0]["nvPairs"]["intfDescription"].split(
                " "
            )
        else:
            wif_desc = []
        hif_desc = have["serviceNetworks"][0]["nvPairs"]["intfDescription"].split(" ")[
            :-1
        ]
        if wif_desc != hif_desc:
            mismatch_reasons.append("DCNM_SRP_IN_DESCR_NO_MATCH")
        if (
            str(want["serviceNetworks"][0]["nvPairs"]["tag"])
            != have["serviceNetworks"][0]["nvPairs"]["tag"]
        ):
            mismatch_reasons.append("DCNM_SRP_IN_TAG_NO_MATCH")
        if (
            str(want["serviceNetworks"][0]["nvPairs"]["vlanId"])
            != have["serviceNetworks"][0]["nvPairs"]["vlanId"]
        ):
            mismatch_reasons.append("DCNM_SRP_IN_PROF_VID_NO_MATCH")

        if want["deploymentMode"].lower() != "onearmadc":

            # Outside Network
            if (
                want["serviceNetworks"][1]["vrfName"]
                != have["serviceNetworks"][1]["vrfName"]
            ):
                mismatch_reasons.append("DCNM_SRP_OUT_VRF_NO_MATCH")
            if (
                want["serviceNetworks"][1]["networkType"]
                != have["serviceNetworks"][1]["networkType"]
            ):
                mismatch_reasons.append("DCNM_SRP_OUT_NT_NO_MATCH")
            if (
                want["serviceNetworks"][1]["networkName"]
                != have["serviceNetworks"][1]["networkName"]
            ):
                mismatch_reasons.append("DCNM_SRP_OUT_NN_NO_MATCH")
            if (
                want["serviceNetworks"][1]["vlanId"]
                != have["serviceNetworks"][1]["vlanId"]
            ):
                mismatch_reasons.append("DCNM_SRP_OUT_VID_NO_MATCH")

            # Outside Network Profile
            if (
                want["serviceNetworks"][1]["nvPairs"]["gatewayIpAddress"]
                != have["serviceNetworks"][1]["nvPairs"]["gatewayIpAddress"]
            ):
                mismatch_reasons.append("DCNM_SRP_OUT_IPV4GW_NO_MATCH")
            if (
                want["serviceNetworks"][1]["nvPairs"]["gatewayIpV6Address"]
                != have["serviceNetworks"][1]["nvPairs"]["gatewayIpV6Address"]
            ):
                mismatch_reasons.append("DCNM_SRP_OUT_IPV6GW_NO_MATCH")
            if (
                want["serviceNetworks"][1]["nvPairs"]["vlanName"]
                != have["serviceNetworks"][1]["nvPairs"]["vlanName"]
            ):
                mismatch_reasons.append("DCNM_SRP_OUT_VNAME_NO_MATCH")

            # When we get the SRP inmformation from have, the intfDescription would have been modified and some meta data added. so ignore the meta data
            # when comparing the interface descriptions
            if want["serviceNetworks"][1]["nvPairs"]["intfDescription"] != "":
                wif_desc = want["serviceNetworks"][1]["nvPairs"][
                    "intfDescription"
                ].split(" ")
            else:
                wif_desc = []
            hif_desc = have["serviceNetworks"][1]["nvPairs"]["intfDescription"].split(
                " "
            )[:-1]
            if wif_desc != hif_desc:
                mismatch_reasons.append("DCNM_SRP_OUT_DESCR_NO_MATCH")
            if (
                str(want["serviceNetworks"][1]["nvPairs"]["tag"])
                != have["serviceNetworks"][1]["nvPairs"]["tag"]
            ):
                mismatch_reasons.append("DCNM_SRP_OUT_TAG_NO_MATCH")
            if (
                str(want["serviceNetworks"][1]["nvPairs"]["vlanId"])
                != have["serviceNetworks"][1]["nvPairs"]["vlanId"]
            ):
                mismatch_reasons.append("DCNM_SRP_OUT_PROF_VID_NO_MATCH")

        if str(want["enabled"]).lower() != str(have["enabled"]).lower():
            mismatch_reasons.append("DCNM_SRP_ATT_NO_MATCH")

        if mismatch_reasons == []:
            return "DCNM_SRP_MATCH", mismatch_reasons
        else:
            return "DCNM_SRP_NO_MATCH", mismatch_reasons

    def dcnm_srp_compare_multi_routes(self, wmr, hmr):

        """
        Routine to compare MULTIROUTE object of route peerings from self.want and self.have.

        Parameters:
            wmr (dict): Multi-Route info object from want
            hmr (dict): Multi-Route info object from have

        Returns:
            DCNM_MR_NO_MATCH (string): if multi-route objects do not match
            DCNM_MR_MATCH (string): if multi-route objects match
        """

        wmrl = wmr.split("\n")
        hmrl = hmr.split("\n")

        fwmr = [item.replace(" ", "") for item in wmrl]
        fhmr = [item.replace(" ", "") for item in hmrl]

        for rt in fwmr:
            if rt not in fhmr:
                return "DCNM_MR_NO_MATCH"
        return "DCNM_MR_MATCH"

    def dcnm_srp_compare_route_info(self, want, have):

        """
        Routine to compare route objects of route peerings from self.want and self.have.

        Parameters:
            want (dict): SRP Payload information populated using playbook config
            have (dict): SRP information existing on the DCNM server

        Returns:
            DCNM_SRP_MATCH (string): if route information in want and have match
            DCNM_SRP_NO_MATCH (string): if route information in want and have do not match
            mismatch_reasons (list): A list containing strings indicating which objects did not match
        """

        mismatch_reasons = []

        if want["peeringOption"] != have["peeringOption"]:
            # If peeringOption doesn't match, we cannot compare rest of the fields because they will be
            # entirely different.
            mismatch_reasons.append("DCNM_SRP_PO_NO_MATCH")
            return "DCNM_SRP_NO_MATCH", mismatch_reasons

        if want["peeringOption"] == "StaticPeering":

            if want["routes"][0]["templateName"] != have["routes"][0]["templateName"]:
                mismatch_reasons.append("DCNM_SRP_SP_IN_TN_NO_MATCH")

            if want["routes"][0]["vrfName"] != have["routes"][0]["vrfName"]:
                mismatch_reasons.append("DCNM_SRP_SP_IN_VRF_NO_MATCH")

            wnv = want["routes"][0]["nvPairs"]
            hnv = have["routes"][0]["nvPairs"]

            if wnv["VRF_NAME"] != hnv["VRF_NAME"]:
                mismatch_reasons.append("DCNM_SRP_SP_IN_PROF_VRF_NO_MATCH")

            rc = self.dcnm_srp_compare_multi_routes(
                wnv["MULTI_ROUTES"], hnv["MULTI_ROUTES"]
            )

            if rc == "DCNM_MR_NO_MATCH":
                mismatch_reasons.append("DCNM_SRP_SP_IN_MR_NO_MATCH")

            if want["deploymentMode"] == "InterTenantFW":

                if (
                    want["routes"][1]["templateName"]
                    != have["routes"][1]["templateName"]
                ):
                    mismatch_reasons.append("DCNM_SRP_SP_OUT_TN_NO_MATCH")

                if want["routes"][1]["vrfName"] != have["routes"][1]["vrfName"]:
                    mismatch_reasons.append("DCNM_SRP_SP_OUT_VRF_NO_MATCH")

                wnv = want["routes"][1]["nvPairs"]
                hnv = have["routes"][1]["nvPairs"]

                if wnv["VRF_NAME"] != hnv["VRF_NAME"]:
                    mismatch_reasons.append("DCNM_SRP_SP_OUT_PROF_VRF_NO_MATCH")

                rc = self.dcnm_srp_compare_multi_routes(
                    wnv["MULTI_ROUTES"], hnv["MULTI_ROUTES"]
                )

                if rc == "DCNM_MR_NO_MATCH":
                    mismatch_reasons.append("DCNM_SRP_SP_OUT_MR_NO_MATCH")

        elif want["peeringOption"] == "EBGPDynamicPeering":

            if want["routes"][0]["templateName"] != have["routes"][0]["templateName"]:
                mismatch_reasons.append("DCNM_SRP_EBGP_IN_TN_NO_MATCH")

            wnv = want["routes"][0]["nvPairs"]
            hnv = have["routes"][0]["nvPairs"]

            if wnv["NEIGHBOR_IP"] != hnv["NEIGHBOR_IP"]:
                mismatch_reasons.append("DCNM_SRP_EBGP_IN_NIP4_NO_MATCH")
            if wnv["LOOPBACK_IP"] != hnv["LOOPBACK_IP"]:
                mismatch_reasons.append("DCNM_SRP_EBGP_IN_LIP4_NO_MATCH")
            if wnv["PEER_LOOPBACK_IP"] != hnv["PEER_LOOPBACK_IP"]:
                mismatch_reasons.append("DCNM_SRP_EBGP_IN_PLIP4_NO_MATCH")
            if wnv["NEIGHBOR_IPV6"] != hnv["NEIGHBOR_IPV6"]:
                mismatch_reasons.append("DCNM_SRP_EBGP_IN_NIP6_NO_MATCH")
            if wnv["LOOPBACK_IPV6"] != hnv["LOOPBACK_IPV6"]:
                mismatch_reasons.append("DCNM_SRP_EBGP_IN_LIP6_NO_MATCH")
            if wnv["PEER_LOOPBACK_IPV6"] != hnv["PEER_LOOPBACK_IPV6"]:
                mismatch_reasons.append("DCNM_SRP_EBGP_IN_PLIP6_NO_MATCH")
            if str(wnv["ROUTE_MAP_TAG"]) != hnv["ROUTE_MAP_TAG"]:
                mismatch_reasons.append("DCNM_SRP_EBGP_IN_RMT_NO_MATCH")
            if wnv["DESC"] != hnv["DESC"]:
                mismatch_reasons.append("DCNM_SRP_EBGP_IN_DESCR_NO_MATCH")
            if str(wnv["LOCAL_ASN"]) != hnv["LOCAL_ASN"]:
                mismatch_reasons.append("DCNM_SRP_EBGP_IN_ASN_NO_MATCH")
            if str(wnv["ADVERTISE_HOST_ROUTE"]).lower() != hnv["ADVERTISE_HOST_ROUTE"]:
                mismatch_reasons.append("DCNM_SRP_EBGP_IN_ADV_HR_NO_MATCH")
            if str(wnv["ADMIN_STATE"]).lower() != hnv["ADMIN_STATE"]:
                mismatch_reasons.append("DCNM_SRP_EBGP_IN_AS_NO_MATCH")
            if wnv["VRF_NAME"] != hnv["VRF_NAME"]:
                mismatch_reasons.append("DCNM_SRP_EBGP_IN_PROF_VRF_NO_MATCH")

            if want["routes"][0]["vrfName"] != have["routes"][0]["vrfName"]:
                mismatch_reasons.append("DCNM_SRP_EBGP_IN_VRF_NO_MATCH")

            if want["deploymentMode"] == "InterTenantFW":

                if (
                    want["routes"][1]["templateName"]
                    != have["routes"][1]["templateName"]
                ):
                    mismatch_reasons.append("DCNM_SRP_EBGP_OUT_TN_NO_MATCH")

                wnv = want["routes"][1]["nvPairs"]
                hnv = have["routes"][1]["nvPairs"]

                if wnv["NEIGHBOR_IP"] != hnv["NEIGHBOR_IP"]:
                    mismatch_reasons.append("DCNM_SRP_EBGP_OUT_NIP4_NO_MATCH")
                if wnv["LOOPBACK_IP"] != hnv["LOOPBACK_IP"]:
                    mismatch_reasons.append("DCNM_SRP_EBGP_OUT_LIP4_NO_MATCH")
                if wnv["PEER_LOOPBACK_IP"] != hnv["PEER_LOOPBACK_IP"]:
                    mismatch_reasons.append("DCNM_SRP_EBGP_OUT_PLIP4_NO_MATCH")
                if wnv["NEIGHBOR_IPV6"] != hnv["NEIGHBOR_IPV6"]:
                    mismatch_reasons.append("DCNM_SRP_EBGP_OUT_NIP6_NO_MATCH")
                if wnv["LOOPBACK_IPV6"] != hnv["LOOPBACK_IPV6"]:
                    mismatch_reasons.append("DCNM_SRP_EBGP_OUT_LIP6_NO_MATCH")
                if wnv["PEER_LOOPBACK_IPV6"] != hnv["PEER_LOOPBACK_IPV6"]:
                    mismatch_reasons.append("DCNM_SRP_EBGP_OUT_PLIP6_NO_MATCH")
                if str(wnv["ROUTE_MAP_TAG"]) != hnv["ROUTE_MAP_TAG"]:
                    mismatch_reasons.append("DCNM_SRP_EBGP_OUT_RMT_NO_MATCH")
                if wnv["DESC"] != hnv["DESC"]:
                    mismatch_reasons.append("DCNM_SRP_EBGP_OUT_DESCR_NO_MATCH")
                if str(wnv["LOCAL_ASN"]) != hnv["LOCAL_ASN"]:
                    mismatch_reasons.append("DCNM_SRP_EBGP_OUT_ASN_NO_MATCH")
                if (
                    str(wnv["ADVERTISE_HOST_ROUTE"]).lower()
                    != hnv["ADVERTISE_HOST_ROUTE"]
                ):
                    mismatch_reasons.append("DCNM_SRP_EBGP_OUT_ADV_HR_NO_MATCH")
                if str(wnv["ADMIN_STATE"]).lower() != hnv["ADMIN_STATE"]:
                    mismatch_reasons.append("DCNM_SRP_EBGP_OUT_AS_NO_MATCH")
                if wnv["VRF_NAME"] != hnv["VRF_NAME"]:
                    mismatch_reasons.append("DCNM_SRP_EBGP_OUT_PROF_VRF_NO_MATCH")

                if want["routes"][1]["vrfName"] != have["routes"][1]["vrfName"]:
                    mismatch_reasons.append("DCNM_SRP_EBGP_OUT_VRF_NO_MATCH")

        if mismatch_reasons == []:
            return "DCNM_SRP_MATCH", mismatch_reasons
        else:
            return "DCNM_SRP_NO_MATCH", mismatch_reasons

    def dcnm_srp_compare_route_peerings(self, srp):

        """
        Routine to compare route peerings from self.want and self.have. Used during merge and replace.

        Parameters:
            srp (dict): The SRP payload information

        Returns:
            DCNM_SRP_ADD_NEW (string): if the given SRP does not exist
            DCNM_SRP_DONT_ADD (string): if given SRP already exist and is exactly the same
            DCNM_SRP_MERGE (string): if given SRP already exists but not exactly the same
        """

        found = False

        if self.have == []:
            return ("DCNM_SRP_ADD_NEW", None)

        match_have = [
            have
            for have in self.have
            if (
                (srp["peeringName"] == have["peeringName"])
                and (srp["fabricName"] == have["fabricName"])
                and (srp["serviceNodeName"] == have["serviceNodeName"])
                and (srp["attachedFabricName"] == have["attachedFabricName"])
            )
        ]
        for have in match_have:
            found = True

            # A matching SRP found. Check if it exactly matches with what is being requested for
            rc, reasons = self.dcnm_srp_compare_common_info(srp, have)

            if rc == "DCNM_SRP_MATCH":
                rc, reasons = self.dcnm_srp_compare_route_info(srp, have)

                if rc == "DCNM_SRP_MATCH":
                    return ("DCNM_SRP_DONT_ADD", have)

        if found is True:
            # Found a matching route peering, but some of the objects don't match.
            # Go ahead and merge the objects into the existing srp
            return ("DCNM_SRP_MERGE", have)
        else:
            return ("DCNM_SRP_ADD_NEW", None)

    def dcnm_srp_get_srp_attachment_status(self, srp):

        """
        Routine to get the attachment/deployment information for a given route peering. This information
        is used to implement idempotent operations. Change is deployment state will be treated as a change
        in route peering during merge and replace operations.

        Parameters:
            srp (dict): Route peering information

        Returns:
            attached (bool): a flag indicating is the given SRP is attached
            deployed (bool): a flag indicating is the given SRP is deployed
        """

        path = (
            "/appcenter/Cisco/elasticservice/elasticservice-api/fabrics/"
            + srp["fabricName"]
            + "/service-nodes/"
            + srp["serviceNodeName"]
            + "/peerings/"
            + srp["attachedFabricName"]
            + "/"
            + srp["peeringName"]
            + "/attachments"
        )

        retries = 0
        while retries < 5:
            retries += 1
            resp = dcnm_send(self.module, "GET", path)

            if resp and resp["RETURN_CODE"] != 200:
                time.sleep(10)
                continue
            else:
                break

        if resp:
            resp["RETRIES"] = retries
            self.result["response"].append(resp)

        attached = True
        deployed = True
        if (
            resp
            and (resp["RETURN_CODE"] == 200)
            and (resp.get("DATA", None) is not None)
        ):

            for item in resp["DATA"]:
                for attach in item["switchAttaches"]:
                    # The API will return status for all switches whether the service node is attached to it or not.
                    # Hence check only entries that are relevant. We can find this by checking for 'portNames' and
                    # vlanID which will be updated only for those switches to which the service node is attached. We
                    # can  ignore the rest.
                    if (attach.get("portNames", None) is None) or (
                        attach.get("vlanId", 0) == 0
                    ):
                        continue
                    if attach["lanAttached"] is False:
                        attached = False
                    if (attach["attachState"] == "NA") or (
                        attach["attachState"] == "PENDING"
                    ):
                        deployed = False
        return (attached, deployed)

    def dcnm_srp_get_diff_merge(self):

        """
        Routine to get a list of payload information, self.diff_create/self.diff_modify to create new or modify
        existing peerings. This routine updates self.diff_merge/self.diff_modify	with route peering payloads
        that are to created or modified.

        Parameters:
            None

        Returns:
            None
        """

        if not self.want:
            return

        for srp in self.want:

            rc, have = self.dcnm_srp_compare_route_peerings(srp)

            if rc == "DCNM_SRP_ADD_NEW":
                # A srp does not exists, create a new one.
                if srp not in self.diff_create:
                    self.changed_dict[0]["merged"].append(srp)
                    self.diff_create.append(srp)
            elif rc == "DCNM_SRP_MERGE":
                # A srp exists and it needs to be updated
                self.changed_dict[0]["modified"].append(srp)
                self.diff_modify.append(srp)

            # Check the 'deploy' flag and decide if this srp is to be deployed
            if have is None:
                # A new route peering. If attach and deploy are set, attach and deploy
                if self.deploy is True:
                    ditem = {}
                    ditem["serviceNodeName"] = srp["serviceNodeName"]
                    ditem["attachedFabricName"] = srp["attachedFabricName"]
                    ditem["fabricName"] = srp["fabricName"]
                    ditem["peeringName"] = srp["peeringName"]
                    self.diff_deploy.append(ditem)
            else:

                attached, deployed = self.dcnm_srp_get_srp_attachment_status(srp)

                if self.deploy is True:
                    # We deploy when self.deploy is True and:
                    #   1. there are no changes due to this request(rc is DCNM_SRP_DONT_ADD), but the SRP is not deployed
                    #   2. there are changes due to this request (rc is DCNM_SRP_MERGE)
                    if ((rc == "DCNM_SRP_DONT_ADD") and (deployed is False)) or (
                        rc == "DCNM_SRP_MERGE"
                    ):
                        ditem = {}
                        ditem["serviceNodeName"] = srp["serviceNodeName"]
                        ditem["attachedFabricName"] = srp["attachedFabricName"]
                        ditem["fabricName"] = srp["fabricName"]
                        ditem["peeringName"] = srp["peeringName"]
                        self.diff_deploy.append(ditem)

        if self.diff_deploy != []:
            self.changed_dict[0]["deploy"].extend(self.diff_deploy)

    def dcnm_srp_get_diff_deleted(self):

        """
        Routine to get a list of payload information that will be used to delete route peerings.
        This routine updates self.diff_delete	with payloads that are used to delete route peerings
        from the server.

        Parameters:
            None

        Returns:
            None
        """

        for srp in self.srp_info:

            # Get the route peering that is to be deleted.
            resp = self.dcnm_srp_get_srp_info_from_dcnm(srp, "PLAYBOOK")

            # For deleting route peerings, it must first be detached and then deployed.
            if resp != [] and resp not in self.diff_delete:
                self.diff_delete.append(resp)
                self.changed_dict[0]["deleted"].append(srp)

    def dcnm_srp_get_diff_query(self):

        """
        Routine to get route peering information based on the playbook configuration.
        This routine updates self.result with SRPs requested for in the playbook if they exist on
        the DCNM server.

        Parameters:
            None

        Returns:
            None
        """

        for srp in self.srp_info:

            # Query may or may not include the peeringName. Get the SRP info based on whether
            # a peeringName is included or not. If a peeringName is not included, then get all
            # peerings from the service-node. Otherwise get the specific peering that is requested

            if srp["name"] != "None":
                # peeringName included
                resp = self.dcnm_srp_get_srp_info_from_dcnm(srp, "PLAYBOOK")

                if resp != []:
                    self.result["response"].append(resp)
            else:
                # peeringName not included
                resp = self.dcnm_srp_get_srp_info_with_service_node(srp["node_name"])

                if resp != []:
                    self.result["response"].extend(resp)
            self.changed_dict[0]["query"].append(srp)

    def dcnm_srp_get_diff_overridden(self):

        """
        Routine to build payload information for overridden state. This routine will build delete list,
        merge list, replace list etc. based on what is required and what is already existing on the DCNM server.
        This routine updates self.diff_merge that contains all route peerings that are to be created afresh and
        self.diff_dlete that contains all route peerings that are to be deleted.

        Parameters:
            None

        Returns:
            None
        """

        # There are 3 cases with overridden state:
        #   1. Peering Name and Service Node Name are given
        #   2. Only Service Node Name is given
        #   3. Neither given

        if self.srp_info == []:
            # In this case we need to get all service nodes and all route peerings from those nodes and delete them
            serv_nodes = self.dcnm_srp_get_service_nodes_from_dcnm()
        else:
            serv_nodes = [{"name": d["node_name"]} for d in self.srp_info]

        srp_list = []
        # From each of the service nodes get the list of all route peerings.
        for snode in serv_nodes:
            srps = self.dcnm_srp_get_srp_info_with_service_node(snode["name"])
            srp_list.extend(srps)

        # Before we add a route peering to self.diff_delete, make sure a matching route peering
        # is not included in the current self.want. If it is, then we need not delete the same. We can just update
        # the same

        delete_srps = []

        for srp in srp_list:
            match_want = [
                want
                for want in self.want
                if (
                    (srp["peeringName"] == want["peeringName"])
                    and (srp["fabricName"] == want["fabricName"])
                    and (srp["serviceNodeName"] == want["serviceNodeName"])
                    and (srp["attachedFabricName"] == want["attachedFabricName"])
                )
            ]
            if match_want == []:
                # There is no matching RP in want. The SRP can be deleted
                delete_srps.append(srp)

        self.diff_delete.extend(delete_srps)
        self.changed_dict[0]["deleted"].extend(delete_srps)

        # Now go and handle SRPs in self.want
        self.dcnm_srp_get_diff_merge()

    def dcnm_srp_create_srp(self, srp, command):

        """
        Routine to send create payload to DCNM.

        Parameters:
            srp  (dict): Route peering information
            command (string): REST API command, either POST or PUT

        Returns:
            resp (dict): Response from DCNM server
        """

        if command == "POST":
            path = (
                "/appcenter/Cisco/elasticservice/elasticservice-api/fabrics/"
                + srp["fabricName"]
                + "/service-nodes/"
                + srp["serviceNodeName"]
                + "/peerings"
            )
        else:
            path = (
                "/appcenter/Cisco/elasticservice/elasticservice-api/fabrics/"
                + srp["fabricName"]
                + "/service-nodes/"
                + srp["serviceNodeName"]
                + "/peerings/"
                + srp["attachedFabricName"]
                + "/"
                + srp["peeringName"]
            )

        json_payload = json.dumps(srp)

        resp = dcnm_send(self.module, command, path, json_payload)
        return resp

    def dcnm_srp_detach_srp(self, srp):

        """
        Routine to detach SRP from service node.

        Parameters:
            srp (dict): Route peering to be detached

        Returns:
            resp (dict): Response from DCNM server
        """

        resp = None

        # First detach the route peerings
        path = (
            "/appcenter/Cisco/elasticservice/elasticservice-api/fabrics/"
            + srp["fabricName"]
            + "/service-nodes/"
            + srp["serviceNodeName"]
            + "/peerings/"
            + srp["attachedFabricName"]
            + "/"
            + srp["peeringName"]
            + "/attachments"
        )

        resp = dcnm_send(self.module, "DELETE", path, "")
        return resp

    def dcnm_srp_delete_srp(self, srp):

        """
        Routine to delete an SRP from service node.

        Parameters:
            srp (dict): Route peering information that is to be deleted

        Returns:
            resp (dict): Response from DCNM server
        """

        # Delete the route peering
        path = (
            "/appcenter/Cisco/elasticservice/elasticservice-api/fabrics/"
            + srp["fabricName"]
            + "/service-nodes/"
            + srp["serviceNodeName"]
            + "/peerings/"
            + srp["attachedFabricName"]
            + "/"
            + srp["peeringName"]
        )
        resp = dcnm_send(self.module, "DELETE", path, "")
        return resp

    def dcnm_srp_config_save_and_deploy(self):

        """
        Routine to save and deploy configuration for the entire box.

        Parameters:
            None

        Returns:
            resp (dict): Response from DCNM server
        """

        path = (
            "/rest/control/fabrics/" + self.module.params["fabric"] + "/config-deploy"
        )

        resp = dcnm_send(self.module, "POST", path, "")
        return resp

    def dcnm_srp_deploy_srp(self, srp, command):

        """
        Routine to deploy SRP on the service node.

        Parameters:
            srp (dict): Route peering information to be deployed
            command (string): REST API command which is POST

        Returns:
            resp (dict): Response from DCNM server
        """

        path = (
            "/appcenter/Cisco/elasticservice/elasticservice-api/fabrics/"
            + srp["fabricName"]
            + "/service-nodes/"
            + srp["serviceNodeName"]
            + "/peerings/"
            + srp["attachedFabricName"]
            + "/"
            + srp["peeringName"]
            + "/deployments"
        )

        resp = dcnm_send(self.module, command, path, "")
        return resp

    def dcnm_srp_check_unauthorized_error_in_resp(self, resp):

        """
        Routine to check for "unauthorized" errors in which case the conncetion must be reset by logging out and
        logging in again.

        Parameters:
            resp (dict): Response which has to be checked for "unauthorized error"

        Returns:
            rc (string): unauthorized_error, if resp["DATA"]["error"]["code"] is UserUnauthorized
                         other_error, otherwise
        """

        rc = "other_error"
        if resp.get("DATA"):
            if resp["DATA"].get("error"):
                if resp["DATA"]["error"].get("code") == "UserUnauthorized":
                    # We have seen "unauthorized error" from DCNM even though the token has been allocated and the connection timeout
                    # has not happened. As per suggestions from L4-L7 services team we will reset token by logging out and logging in
                    # again so that a new token is obtained
                    dcnm_reset_connection(self.module)
                    rc = "unauthorized_error"
        return rc

    def dcnm_srp_send_message_to_dcnm(self):

        """
        Routine to push payloads to DCNM server. This routine implements reqquired error checks and retry mechanisms to handle
        transient errors. This routine checks self.diff_create, self.diff_modify, self.diff_delete and self.diff_deploy lists
        and push appropriate requests to DCNM.

        Parameters:
            None

        Returns:
            None
        """

        resp = None
        create_flag = False
        modify_flag = False
        delete_flag = False
        deploy_flag = False

        for srp in self.diff_create:
            retries = 0
            command = "POST"
            while retries < 10:
                retries += 1
                resp = self.dcnm_srp_create_srp(srp, command)
                if resp.get("RETURN_CODE") == 200:
                    create_flag = True
                    break
                else:
                    # We sometimes see "UserUnauthorized" errors while transacting with DCNM server. Suggested remedy is to
                    # logout and login again. We will do the logout from here and expect the login to happen again after this
                    # from the connection module
                    self.dcnm_srp_check_unauthorized_error_in_resp(resp)

                    # There may be a temporary issue on the server. so we should try again. In case
                    # of create or modify, the peering may have been created/updated, but the error may
                    # be due to the attach. So check if the peering is created and if attach flag is set.
                    # If so then try attaching the peering and do not try to recreate
                    get_resp = self.dcnm_srp_get_srp_info_from_dcnm(srp, "PAYLOAD")
                    if get_resp != []:
                        # Since the peering is already created, use PUT to update the peering again with
                        # the same payload
                        command = "PUT"
                    time.sleep(10)
                    continue
            resp["RETRIES"] = retries
            self.result["response"].append(resp)

        for srp in self.diff_modify:
            retries = 0
            while retries < 10:
                retries += 1
                resp = self.dcnm_srp_create_srp(srp, "PUT")
                if resp.get("RETURN_CODE") == 200:
                    modify_flag = True
                    break
                else:
                    # We sometimes see "UserUnauthorized" errors while transacting with DCNM server. Suggested remedy is to
                    # logout and login again. We will do the logout from here and expect the login to happen again after this
                    # from the connection module
                    self.dcnm_srp_check_unauthorized_error_in_resp(resp)
                    time.sleep(10)
                    continue
            resp["RETRIES"] = retries
            self.result["response"].append(resp)

        for srp in self.diff_delete:
            retries = 0
            while retries < 10:
                retries += 1
                resp = self.dcnm_srp_detach_srp(srp)
                if (resp is not None) and (resp.get("RETURN_CODE") == 200):
                    delete_flag = True
                    break
                else:
                    # We sometimes see "UserUnauthorized" errors while transacting with DCNM server. Suggested remedy is to
                    # logout and login again. We will do the logout from here and expect the login to happen again after this
                    # from the connection module
                    self.dcnm_srp_check_unauthorized_error_in_resp(resp)
                    time.sleep(10)
                    continue
            if resp is not None:
                resp["RETRIES"] = retries
                self.result["response"].append(resp)

        # For delete case we have done a detach. do a deploy before actual delete
        for srp in self.diff_delete:
            retries = 0
            while retries < 10:
                retries += 1
                resp = self.dcnm_srp_deploy_srp(srp, "POST")

                if (resp is not None) and (resp.get("RETURN_CODE") == 200):
                    delete_flag = True
                    break
                else:
                    # We sometimes see "UserUnauthorized" errors while transacting with DCNM server. Suggested remedy is to
                    # logout and login again. We will do the logout from here and expect the login to happen again after this
                    # from the connection module
                    self.dcnm_srp_check_unauthorized_error_in_resp(resp)
                    time.sleep(10)
                    continue
            resp["RETRIES"] = retries
            self.result["response"].append(resp)

        if delete_flag is True:
            time.sleep(40)

        for srp in self.diff_delete:
            retries = 0
            deploy_in_prog = False
            while retries < 25:
                retries += 1
                resp = self.dcnm_srp_delete_srp(srp)
                if (resp is not None) and (resp.get("RETURN_CODE") == 200):
                    delete_flag = True
                    break
                else:
                    # We sometimes see "UserUnauthorized" errors while transacting with DCNM server. Suggested remedy is to
                    # logout and login again. We will do the logout from here and expect the login to happen again after this
                    # from the connection module
                    self.dcnm_srp_check_unauthorized_error_in_resp(resp)

                    if retries == 15:
                        # We failed to delete even after all retries. Try a config save and deploy which
                        # may pull out of the situation

                        resp = self.dcnm_srp_config_save_and_deploy()
                        self.result["response"].append(resp)
                    elif deploy_in_prog is False:
                        # We will require a deploy here. Otherwise we may see delete errors in some cases
                        # indicating that a deploy operation is still in progress and peering cannot be deleted
                        resp = self.dcnm_srp_deploy_srp(srp, "POST")
                        if resp.get("RETURN_CODE") == 200:
                            deploy_in_prog = True
                        else:
                            self.dcnm_srp_check_unauthorized_error_in_resp(resp)
                    time.sleep(10)
                    continue
            if resp is not None:
                resp["RETRIES"] = retries
                self.result["response"].append(resp)

        for srp in self.diff_deploy:
            retries = 0
            while retries < 10:
                retries += 1
                resp = self.dcnm_srp_deploy_srp(srp, "POST")
                if resp.get("RETURN_CODE") == 200:
                    deploy_flag = True
                    break
                else:
                    # We sometimes see "UserUnauthorized" errors while transacting with DCNM server. Suggested remedy is to
                    # logout and login again. We will do the logout from here and expect the login to happen again after this
                    # from the connection module
                    self.dcnm_srp_check_unauthorized_error_in_resp(resp)
                    time.sleep(10)
                    continue
            resp["RETRIES"] = retries
            self.result["response"].append(resp)

        self.result["changed"] = (
            create_flag or modify_flag or delete_flag or deploy_flag
        )


def main():

    """ main entry point for module execution
    """
    element_spec = dict(
        fabric=dict(required=True, type="str"),
        service_fabric=dict(required=True, type="str"),
        config=dict(required=False, type="list"),
        state=dict(
            type="str",
            default="merged",
            choices=["merged", "deleted", "replaced", "query", "overridden"],
        ),
        deploy=dict(required=False, type="bool", default=True),
        attach=dict(required=False, type="str", default="default"),
        check_mode=dict(required=False, type="bool", default=False),
        debug=dict(required=False, type="bool", default=False),
    )

    module = AnsibleModule(argument_spec=element_spec, supports_check_mode=True)

    dcnm_srp = DcnmServiceRoutePeering(module)

    dcnm_srp.result["StartTime"] = datetime.now().strftime("%H:%M:%S")

    dcnm_srp.deploy = module.params["deploy"]
    if (module.params["attach"] == "default") or (
        module.params["attach"].lower() == "true"
    ):
        dcnm_srp.attach = True
    else:
        dcnm_srp.attach = False

    dcnm_srp.debug = module.params["debug"]

    state = module.params["state"]

    if not dcnm_srp.config:
        if state == "merged" or state == "deleted" or state == "query":
            module.fail_json(
                msg="'config' element is mandatory for state '{}', given = '{}'".format(
                    state, dcnm_srp.config
                )
            )

    dcnm_srp.dcnm_srp_validate_input()

    if (module.params["state"] != "query") and (module.params["state"] != "deleted"):

        dcnm_srp.dcnm_srp_get_want()
        dcnm_srp.dcnm_srp_get_have()

        # self.want would have defaulted all optional objects not included in playbook. But the way
        # these objects are handled is different between 'merged' and 'replaced' states. For 'merged'
        # state, objects not included in the playbook must be left as they are and for state 'replaced'
        # they must be purged or defaulted.

        dcnm_srp.dcnm_srp_update_want()

    if (module.params["state"] == "merged") or (module.params["state"] == "replaced"):
        dcnm_srp.dcnm_srp_get_diff_merge()

    if module.params["state"] == "deleted":
        dcnm_srp.dcnm_srp_get_diff_deleted()

    if module.params["state"] == "query":
        dcnm_srp.dcnm_srp_get_diff_query()

    if module.params["state"] == "overridden":
        dcnm_srp.dcnm_srp_get_diff_overridden()

    dcnm_srp.result["diff"] = dcnm_srp.changed_dict

    if dcnm_srp.diff_create or dcnm_srp.diff_modify or dcnm_srp.diff_delete:
        dcnm_srp.result["changed"] = True

    if module.params["check_mode"]:
        dcnm_srp.result["changed"] = False
        dcnm_srp.result["EndTime"] = datetime.now().strftime("%H:%M:%S")
        module.exit_json(**dcnm_srp.result)

    dcnm_srp.dcnm_srp_send_message_to_dcnm()

    dcnm_srp.result["EndTime"] = datetime.now().strftime("%H:%M:%S")
    module.exit_json(**dcnm_srp.result)


if __name__ == "__main__":
    main()
