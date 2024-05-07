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
__author__ = "Allen Robel"

DOCUMENTATION = """
---
---
module: dcnm_fabric
short_description: Manage creation and configuration of NDFC fabrics.
version_added: 3.5.0
author: Allen Robel (@quantumonion)
description:
  - Create, delete, update NDFC fabrics.
options:
  state:
    choices:
      - deleted
      - merged
      - query
      - replaced
    default: merged
    description:
      - The state of the feature or object after module completion
    type: str
  config:
    description:
      - A list of fabric configuration dictionaries
    type: list
    elements: dict
    suboptions:
      DEPLOY:
        default: false
        description:
          - Save and deploy the fabric configuration.
        required: false
        type: bool
      FABRIC_NAME:
        description:
          - The name of the fabric.
        required: true
        type: str
      FABRIC_TYPE:
        choices:
          - VXLAN_EVPN
          - VXLAN_EVPN_MSD
          - LAN_CLASSIC
        description:
          - The type of fabric.
        required: true
        type: str
      VXLAN_EVPN_FABRIC_PARAMETERS:
        description:
          - Data Center VXLAN EVPN fabric specific parameters.
          - Fabric for a VXLAN EVPN deployment with Nexus 9000 and 3000 switches.
          - The following parameters are specific to VXLAN EVPN fabrics.
          - The indentation of these parameters is meant only to logically group
            them.
          - They should be at the same YAML level as FABRIC_TYPE and FABRIC_NAME.
        suboptions:
          AAA_REMOTE_IP_ENABLED:
            default: 0
            description:
              - Enable only, when IP Authorization is enabled in the AAA Server
            ndfc_gui_label: Enable AAA IP Authorization
            ndfc_gui_section: Advanced
            required: false
            type: bool
          AAA_SERVER_CONF:
            default: ""
            description:
              - AAA Configurations
            ndfc_gui_label: AAA Freeform Config
            ndfc_gui_section: Manageability
            required: false
            type: str
          ADVERTISE_PIP_BGP:
            default: 0
            description:
              - For Primary VTEP IP Advertisement As Next-Hop Of Prefix Routes
            ndfc_gui_label: vPC advertise-pip
            ndfc_gui_section: vPC
            required: false
            type: bool
          ADVERTISE_PIP_ON_BORDER:
            default: 1
            description:
              - Enable advertise-pip on vPC borders and border gateways only.
                Applicable only when vPC advertise-pip is not enabled
            ndfc_gui_label: vPC advertise-pip on Border only
            ndfc_gui_section: vPC
            required: false
            type: bool
          ANYCAST_BGW_ADVERTISE_PIP:
            default: 0
            description:
              - To advertise Anycast Border Gateway PIP as VTEP. Effective on
                MSD fabric Recalculate Config
            ndfc_gui_label: Anycast Border Gateway advertise-pip
            ndfc_gui_section: Advanced
            required: false
            type: bool
          ANYCAST_GW_MAC:
            default: 2020.0000.00aa
            description:
              - Shared MAC address for all leafs (xxxx.xxxx.xxxx)
            ndfc_gui_label: Anycast Gateway MAC
            ndfc_gui_section: ""
            required: true
            type: macAddress
          ANYCAST_LB_ID:
            default: 10
            description:
              - "Used for vPC Peering in VXLANv6 Fabrics "
            max: 1023
            min: 0
            ndfc_gui_label: Underlay Anycast Loopback Id
            ndfc_gui_section: Protocols
            required: true
            type: int
          ANYCAST_RP_IP_RANGE:
            default: 10.254.254.0/24
            description:
              - Anycast or Phantom RP IP Address Range
            ndfc_gui_label: Underlay RP Loopback IP Range
            ndfc_gui_section: Resources
            required: true
            type: ipv4_subnet
          AUTO_SYMMETRIC_DEFAULT_VRF:
            default: 0
            description:
              - Whether to auto generate Default VRF interface and BGP peering
                configuration on managed neighbor devices. If set, auto created
                VRF Lite IFC links will have Auto Deploy Default VRF for Peer
                enabled.
            ndfc_gui_label: Auto Deploy Default VRF for Peer
            ndfc_gui_section: Resources
            required: false
            type: bool
          AUTO_SYMMETRIC_VRF_LITE:
            default: 0
            description:
              - Whether to auto generate VRF LITE sub-interface and BGP peering
                configuration on managed neighbor devices. If set, auto created
                VRF Lite IFC links will have Auto Deploy for Peer enabled.
            ndfc_gui_label: Auto Deploy for Peer
            ndfc_gui_section: Resources
            required: false
            type: bool
          AUTO_UNIQUE_VRF_LITE_IP_PREFIX:
            default: 0
            description:
              - When enabled, IP prefix allocated to the VRF LITE IFC is not
                reused on VRF extension over VRF LITE IFC. Instead, unique IP
                Subnet is allocated for each VRF extension over VRF LITE IFC.
            ndfc_gui_label: Auto Allocation of Unique IP on VRF Extension over VRF Lite IFC
            ndfc_gui_section: Resources
            required: false
            type: bool
          AUTO_VRFLITE_IFC_DEFAULT_VRF:
            default: 0
            description:
              - Whether to auto generate Default VRF interface and BGP peering
                configuration on VRF LITE IFC auto deployment. If set, auto
                created VRF Lite IFC links will have Auto Deploy Default VRF
                enabled.
            ndfc_gui_label: Auto Deploy Default VRF
            ndfc_gui_section: Resources
            required: false
            type: bool
          BANNER:
            default: ""
            description:
              - Message of the Day (motd) banner. Delimiter char (very first
                char is delimiter char) followed by message ending with
                delimiter
            ndfc_gui_label: Banner
            ndfc_gui_section: Manageability
            required: false
            type: str
          BFD_AUTH_ENABLE:
            default: 0
            description:
              - Valid for P2P Interfaces only
            ndfc_gui_label: Enable BFD Authentication
            ndfc_gui_section: Protocols
            required: false
            type: bool
          BFD_AUTH_KEY:
            default: ""
            description:
              - Encrypted SHA1 secret value
            ndfc_gui_label: BFD Authentication Key
            ndfc_gui_section: Protocols
            required: true
            type: str
          BFD_AUTH_KEY_ID:
            default: 100
            description:
              - No description available
            ndfc_gui_label: BFD Authentication Key ID
            ndfc_gui_section: Protocols
            required: true
            type: int
          BFD_ENABLE:
            default: 0
            description:
              - Valid for IPv4 Underlay only
            ndfc_gui_label: Enable BFD
            ndfc_gui_section: Protocols
            required: false
            type: bool
          BFD_IBGP_ENABLE:
            default: 0
            description:
              - No description available
            ndfc_gui_label: Enable BFD For iBGP
            ndfc_gui_section: Protocols
            required: false
            type: bool
          BFD_ISIS_ENABLE:
            default: 0
            description:
              - No description available
            ndfc_gui_label: Enable BFD For ISIS
            ndfc_gui_section: Protocols
            required: false
            type: bool
          BFD_OSPF_ENABLE:
            default: 0
            description:
              - No description available
            ndfc_gui_label: Enable BFD For OSPF
            ndfc_gui_section: Protocols
            required: false
            type: bool
          BFD_PIM_ENABLE:
            default: 0
            description:
              - No description available
            ndfc_gui_label: Enable BFD For PIM
            ndfc_gui_section: Protocols
            required: false
            type: bool
          BGP_AS:
            default: ""
            description:
              - 1-4294967295 | 1-65535.0-65535 It is a good practice to have a
                unique ASN for each Fabric.
            ndfc_gui_label: BGP ASN
            ndfc_gui_section: ""
            required: true
            type: str
          BGP_AUTH_ENABLE:
            default: 0
            description:
              - No description available
            ndfc_gui_label: Enable BGP Authentication
            ndfc_gui_section: Protocols
            required: false
            type: bool
          BGP_AUTH_KEY:
            default: ""
            description:
              - Encrypted BGP Authentication Key based on type
            ndfc_gui_label: BGP Authentication Key
            ndfc_gui_section: Protocols
            required: true
            type: str
          BGP_AUTH_KEY_TYPE:
            choices:
              - 3
              - 7
            default: 3
            description:
              - "BGP Key Encryption Type: 3 - 3DES, 7 - Cisco"
            ndfc_gui_label: BGP Authentication Key Encryption Type
            ndfc_gui_section: Protocols
            required: true
            type: str
          BGP_LB_ID:
            default: 0
            description:
              - No description available
            max: 1023
            min: 0
            ndfc_gui_label: Underlay Routing Loopback Id
            ndfc_gui_section: Protocols
            required: true
            type: int
          BOOTSTRAP_CONF:
            default: ""
            description:
              - Additional CLIs required during device bootup/login e.g.
                AAA/Radius
            ndfc_gui_label: Bootstrap Freeform Config
            ndfc_gui_section: Bootstrap
            required: false
            type: str
          BOOTSTRAP_ENABLE:
            default: 0
            description:
              - Automatic IP Assignment For POAP
            ndfc_gui_label: Enable Bootstrap
            ndfc_gui_section: Bootstrap
            required: false
            type: bool
          BOOTSTRAP_MULTISUBNET:
            default: "#Scope_Start_IP, Scope_End_IP, Scope_Default_Gateway,
              Scope_Subnet_Prefix"
            description:
              - "lines with # prefix are ignored here"
            ndfc_gui_label: DHCPv4 Multi Subnet Scope
            ndfc_gui_section: Bootstrap
            required: false
            type: str
          BROWNFIELD_NETWORK_NAME_FORMAT:
            default: Auto_Net_VNI$$VNI$$_VLAN$$VLAN_ID$$
            description:
              - Generated network name should be &lt; 64 characters
            ndfc_gui_label: Brownfield Overlay Network Name Format
            ndfc_gui_section: Advanced
            required: false
            type: str
          BROWNFIELD_SKIP_OVERLAY_NETWORK_ATTACHMENTS:
            default: 0
            description:
              - Enable to skip overlay network interface attachments for
                Brownfield and Host Port Resync cases
            ndfc_gui_label: Skip Overlay Network Interface Attachments
            ndfc_gui_section: Advanced
            required: false
            type: bool
          CDP_ENABLE:
            default: 0
            description:
              - Enable CDP on management interface
            ndfc_gui_label: Enable CDP for Bootstrapped Switch
            ndfc_gui_section: Advanced
            required: false
            type: bool
          COPP_POLICY:
            choices:
              - dense
              - lenient
              - moderate
              - strict
              - manual
            default: strict
            description:
              - Fabric Wide CoPP Policy. Customized CoPP policy should be
                provided when manual is selected
            ndfc_gui_label: CoPP Profile
            ndfc_gui_section: Advanced
            required: true
            type: str
          DCI_SUBNET_RANGE:
            default: 10.33.0.0/16
            description:
              - Address range to assign P2P Interfabric Connections
            ndfc_gui_label: VRF Lite Subnet IP Range
            ndfc_gui_section: Resources
            required: true
            type: ipv4_subnet
          DCI_SUBNET_TARGET_MASK:
            default: 30
            description:
              - No description available
            max: 31
            min: 8
            ndfc_gui_label: VRF Lite Subnet Mask
            ndfc_gui_section: Resources
            required: true
            type: int
          DEFAULT_QUEUING_POLICY_CLOUDSCALE:
            choices:
              - queuing_policy_default_4q_cloudscale
              - queuing_policy_default_8q_cloudscale
            default: queuing_policy_default_8q_cloudscale
            description:
              - Queuing Policy for all 92xx, -EX, -FX, -FX2, -FX3, -GX series
                switches in the fabric
            ndfc_gui_label: N9K Cloud Scale Platform Queuing Policy
            ndfc_gui_section: Advanced
            required: true
            type: str
          DEFAULT_QUEUING_POLICY_OTHER:
            choices:
              - queuing_policy_default_other
            default: queuing_policy_default_other
            description:
              - Queuing Policy for all other switches in the fabric
            ndfc_gui_label: Other N9K Platform Queuing Policy
            ndfc_gui_section: Advanced
            required: true
            type: str
          DEFAULT_QUEUING_POLICY_R_SERIES:
            choices:
              - queuing_policy_default_r_series
            default: queuing_policy_default_r_series
            description:
              - Queuing Policy for all R-Series switches in the fabric
            ndfc_gui_label: N9K R-Series Platform Queuing Policy
            ndfc_gui_section: Advanced
            required: true
            type: str
          DEFAULT_VRF_REDIS_BGP_RMAP:
            default: extcon-rmap-filter
            description:
              - Route Map used to redistribute BGP routes to IGP in default vrf
                in auto created VRF Lite IFC links
            ndfc_gui_label: Redistribute BGP Route-map Name
            ndfc_gui_section: Resources
            required: false
            type: str
          DHCP_ENABLE:
            default: 0
            description:
              - Automatic IP Assignment For POAP From Local DHCP Server
            ndfc_gui_label: Enable Local DHCP Server
            ndfc_gui_section: Bootstrap
            required: false
            type: bool
          DHCP_END:
            default: ""
            description:
              - End Address For Switch POAP
            ndfc_gui_label: DHCP Scope End Address
            ndfc_gui_section: Bootstrap
            required: true
            type: ipv4
          DHCP_IPV6_ENABLE:
            choices:
              - DHCPv4
              - DHCPv6
            default: DHCPv4
            description:
              - No description available
            ndfc_gui_label: DHCP Version
            ndfc_gui_section: Bootstrap
            required: false
            type: str
          DHCP_START:
            default: ""
            description:
              - Start Address For Switch POAP
            ndfc_gui_label: DHCP Scope Start Address
            ndfc_gui_section: Bootstrap
            required: true
            type: ipv4
          DNS_SERVER_IP_LIST:
            default: ""
            description:
              - Comma separated list of IP Addresses(v4/v6)
            ndfc_gui_label: DNS Server IPs
            ndfc_gui_section: Manageability
            required: false
            type: ipAddressList
          DNS_SERVER_VRF:
            default: ""
            description:
              - One VRF for all DNS servers or a comma separated list of VRFs,
                one per DNS server
            ndfc_gui_label: DNS Server VRFs
            ndfc_gui_section: Manageability
            required: false
            type: string[]
          ENABLE_AAA:
            default: 0
            description:
              - Include AAA configs from Manageability tab during device bootup
            ndfc_gui_label: Enable AAA Config
            ndfc_gui_section: Bootstrap
            required: false
            type: bool
          ENABLE_DEFAULT_QUEUING_POLICY:
            default: 0
            description:
              - No description available
            ndfc_gui_label: Enable Default Queuing Policies
            ndfc_gui_section: Advanced
            required: false
            type: bool
          ENABLE_FABRIC_VPC_DOMAIN_ID:
            default: 0
            description:
              - (Not Recommended)
            ndfc_gui_label: Enable the same vPC Domain Id for all vPC Pairs
            ndfc_gui_section: vPC
            required: false
            type: bool
          ENABLE_MACSEC:
            default: 0
            description:
              - Enable MACsec in the fabric
            ndfc_gui_label: Enable MACsec
            ndfc_gui_section: Advanced
            required: false
            type: bool
          ENABLE_NETFLOW:
            default: 0
            description:
              - Enable Netflow on VTEPs
            ndfc_gui_label: Enable Netflow
            ndfc_gui_section: Flow Monitor
            required: false
            type: bool
          ENABLE_NGOAM:
            default: 1
            description:
              - Enable the Next Generation (NG) OAM feature for all switches in
                the fabric to aid in trouble-shooting VXLAN EVPN fabrics
            ndfc_gui_label: Enable VXLAN OAM
            ndfc_gui_section: Advanced
            required: false
            type: bool
          ENABLE_NXAPI:
            default: 1
            description:
              - Enable HTTPS NX-API
            ndfc_gui_label: Enable NX-API
            ndfc_gui_section: Advanced
            required: false
            type: bool
          ENABLE_NXAPI_HTTP:
            default: 1
            description:
              - No description available
            ndfc_gui_label: Enable HTTP NX-API
            ndfc_gui_section: Advanced
            required: false
            type: bool
          ENABLE_PBR:
            default: 0
            description:
              - When ESR option is ePBR, enable ePBR will enable pbr, sla sender
                and epbr features on the switch
            ndfc_gui_label: Enable Policy-Based Routing (PBR)/Enhanced PBR (ePBR)
            ndfc_gui_section: Advanced
            required: false
            type: bool
          ENABLE_PVLAN:
            default: 0
            description:
              - Enable PVLAN on switches except spines and super spines
            ndfc_gui_label: Enable Private VLAN (PVLAN)
            ndfc_gui_section: Advanced
            required: false
            type: bool
          ENABLE_TENANT_DHCP:
            default: 1
            description:
              - No description available
            ndfc_gui_label: Enable Tenant DHCP
            ndfc_gui_section: Advanced
            required: false
            type: bool
          ENABLE_TRM:
            default: 0
            description:
              - For Overlay Multicast Support In VXLAN Fabrics
            ndfc_gui_label: Enable Tenant Routed Multicast (TRM)
            ndfc_gui_section: Replication
            required: false
            type: bool
          ENABLE_VPC_PEER_LINK_NATIVE_VLAN:
            default: 0
            description:
              - No description available
            ndfc_gui_label: Make vPC Peer Link VLAN as Native VLAN
            ndfc_gui_section: vPC
            required: false
            type: bool
          ESR_OPTION:
            default: PBR
            description:
              - Policy-Based Routing (PBR) or Enhanced PBR (ePBR)
            ndfc_gui_label: Elastic Services Re-direction (ESR) Options
            ndfc_gui_section: Advanced
            required: false
            type: enum
          EXTRA_CONF_INTRA_LINKS:
            default: ""
            description:
              - Additional CLIs For All Intra-Fabric Links
            ndfc_gui_label: Intra-fabric Links Additional Config
            ndfc_gui_section: Advanced
            required: false
            type: str
          EXTRA_CONF_LEAF:
            default: ""
            description:
              - Additional CLIs For All Leafs As Captured From Show Running
                Configuration
            ndfc_gui_label: Leaf Freeform Config
            ndfc_gui_section: Advanced
            required: false
            type: str
          EXTRA_CONF_SPINE:
            default: ""
            description:
              - Additional CLIs For All Spines As Captured From Show Running
                Configuration
            ndfc_gui_label: Spine Freeform Config
            ndfc_gui_section: Advanced
            required: false
            type: str
          EXTRA_CONF_TOR:
            default: ""
            description:
              - Additional CLIs For All ToRs As Captured From Show Running
                Configuration
            ndfc_gui_label: ToR Freeform Config
            ndfc_gui_section: Advanced
            required: false
            type: str
          FABRIC_INTERFACE_TYPE:
            choices:
              - p2p
              - unnumbered
            default: p2p
            description:
              - Numbered(Point-to-Point) or Unnumbered
            ndfc_gui_label: Fabric Interface Numbering
            ndfc_gui_section: ""
            required: true
            type: str
          FABRIC_MTU:
            default: 9216
            description:
              - . Must be an even number
            max: 9216
            min: 576
            ndfc_gui_label: Intra Fabric Interface MTU
            ndfc_gui_section: Advanced
            required: true
            type: int
          FABRIC_NAME:
            default: ""
            description:
              - Please provide the fabric name to create it (Max Size 32)
            ndfc_gui_label: Fabric Name
            ndfc_gui_section: ""
            required: true
            type: str
          FABRIC_VPC_DOMAIN_ID:
            default: 1
            description:
              - vPC Domain Id to be used on all vPC pairs
            ndfc_gui_label: vPC Domain Id
            ndfc_gui_section: vPC
            required: true
            type: int
          FABRIC_VPC_QOS:
            default: 0
            description:
              - Qos on spines for guaranteed delivery of vPC Fabric Peering
                communication
            ndfc_gui_label: Enable Qos for Fabric vPC-Peering
            ndfc_gui_section: vPC
            required: false
            type: bool
          FABRIC_VPC_QOS_POLICY_NAME:
            default: spine_qos_for_fabric_vpc_peering
            description:
              - Qos Policy name should be same on all spines
            ndfc_gui_label: Qos Policy Name
            ndfc_gui_section: vPC
            required: true
            type: str
          FEATURE_PTP:
            default: 0
            description:
              - No description available
            ndfc_gui_label: Enable Precision Time Protocol (PTP)
            ndfc_gui_section: Advanced
            required: false
            type: bool
          GRFIELD_DEBUG_FLAG:
            choices:
              - Enable
              - Disable
            default: Disable
            description:
              - Enable to clean switch configuration without reload when
                PreserveConfig=no
            ndfc_gui_label: Greenfield Cleanup Option
            ndfc_gui_section: Advanced
            required: true
            type: str
          HD_TIME:
            default: 180
            description:
              - NVE Source Inteface HoldDown Time  in seconds
            max: 1500
            min: 1
            ndfc_gui_label: VTEP HoldDown Time
            ndfc_gui_section: Advanced
            required: false
            type: int
          HOST_INTF_ADMIN_STATE:
            default: 1
            description:
              - No description available
            ndfc_gui_label: Unshut Host Interfaces by Default
            ndfc_gui_section: Advanced
            required: false
            type: bool
          IBGP_PEER_TEMPLATE:
            default: ""
            description:
              - Speficies the iBGP Peer-Template config used for RR and spines
                with border role.
            ndfc_gui_label: iBGP Peer-Template Config
            ndfc_gui_section: Protocols
            required: false
            type: str
          IBGP_PEER_TEMPLATE_LEAF:
            default: ""
            description:
              - Specifies the config used for leaf, border or border gateway. If
                this field is empty, the peer template defined in iBGP
                Peer-Template Config is used on all BGP enabled devices
                (RRs,leafs, border or border gateway roles.
            ndfc_gui_label: Leaf/Border/Border Gateway iBGP Peer-Template Config
            ndfc_gui_section: Protocols
            required: false
            type: str
          INBAND_DHCP_SERVERS:
            default: ""
            description:
              - Comma separated list of IPv4 Addresses (Max 3)
            ndfc_gui_label: External DHCP Server IP Addresses
            ndfc_gui_section: Bootstrap
            required: true
            type: ipAddressList
          INBAND_MGMT:
            default: 0
            description:
              - Manage switches with only Inband connectivity
            ndfc_gui_label: Inband Management
            ndfc_gui_section: Manageability
            required: false
            type: bool
          ISIS_AUTH_ENABLE:
            default: 0
            description:
              - No description available
            ndfc_gui_label: Enable IS-IS Authentication
            ndfc_gui_section: Protocols
            required: false
            type: bool
          ISIS_AUTH_KEY:
            default: ""
            description:
              - Cisco Type 7 Encrypted
            ndfc_gui_label: IS-IS Authentication Key
            ndfc_gui_section: Protocols
            required: true
            type: str
          ISIS_AUTH_KEYCHAIN_KEY_ID:
            default: 127
            description:
              - No description available
            max: 65535
            min: 0
            ndfc_gui_label: IS-IS Authentication Key ID
            ndfc_gui_section: Protocols
            required: true
            type: int
          ISIS_AUTH_KEYCHAIN_NAME:
            default: ""
            description:
              - No description available
            ndfc_gui_label: IS-IS Authentication Keychain Name
            ndfc_gui_section: Protocols
            required: true
            type: str
          ISIS_LEVEL:
            choices:
              - level-1
              - level-2
            default: level-2
            description:
              - "Supported IS types: level-1, level-2"
            ndfc_gui_label: IS-IS Level
            ndfc_gui_section: Protocols
            required: true
            type: str
          ISIS_OVERLOAD_ELAPSE_TIME:
            default: 60
            description:
              - Clear the overload bit after an elapsed time in seconds
            ndfc_gui_label: IS-IS Overload Bit Elapsed Time
            ndfc_gui_section: Protocols
            required: true
            type: int
          ISIS_OVERLOAD_ENABLE:
            default: 1
            description:
              - When enabled, set the overload bit for an elapsed time after a
                reload
            ndfc_gui_label: Set IS-IS Overload Bit
            ndfc_gui_section: Protocols
            required: false
            type: bool
          ISIS_P2P_ENABLE:
            default: 1
            description:
              - This will enable network point-to-point on fabric interfaces
                which are numbered
            ndfc_gui_label: Enable IS-IS Network Point-to-Point
            ndfc_gui_section: Protocols
            required: false
            type: bool
          L2_HOST_INTF_MTU:
            default: 9216
            description:
              - . Must be an even number
            max: 9216
            min: 1500
            ndfc_gui_label: Layer 2 Host Interface MTU
            ndfc_gui_section: Advanced
            required: true
            type: int
          L2_SEGMENT_ID_RANGE:
            default: 30000-49000
            description:
              - "Overlay Network Identifier Range "
            max: 16777214
            min: 1
            ndfc_gui_label: Layer 2 VXLAN VNI Range
            ndfc_gui_section: Resources
            required: true
            type: integerRange
          L3VNI_MCAST_GROUP:
            default: 239.1.1.0
            description:
              - Default Underlay Multicast group IP assigned for every overlay
                VRF.
            ndfc_gui_label: Default MDT Address for TRM VRFs
            ndfc_gui_section: Replication
            required: true
            type: ipv4
          L3_PARTITION_ID_RANGE:
            default: 50000-59000
            description:
              - "Overlay VRF Identifier Range "
            max: 16777214
            min: 1
            ndfc_gui_label: Layer 3 VXLAN VNI Range
            ndfc_gui_section: Resources
            required: true
            type: integerRange
          LINK_STATE_ROUTING:
            choices:
              - ospf
              - is-is
            default: ospf
            description:
              - Used for Spine-Leaf Connectivity
            ndfc_gui_label: Underlay Routing Protocol
            ndfc_gui_section: ""
            required: true
            type: str
          LINK_STATE_ROUTING_TAG:
            default: UNDERLAY
            description:
              - Underlay Routing Process Tag
            ndfc_gui_label: Underlay Routing Protocol Tag
            ndfc_gui_section: Protocols
            required: true
            type: str
          LOOPBACK0_IPV6_RANGE:
            default: fd00::a02:0/119
            description:
              - Typically Loopback0 IPv6 Address Range
            ndfc_gui_label: Underlay Routing Loopback IPv6 Range
            ndfc_gui_section: Resources
            required: true
            type: ipv6_subnet
          LOOPBACK0_IP_RANGE:
            default: 10.2.0.0/22
            description:
              - Typically Loopback0 IP Address Range
            ndfc_gui_label: Underlay Routing Loopback IP Range
            ndfc_gui_section: Resources
            required: true
            type: ipv4_subnet
          LOOPBACK1_IPV6_RANGE:
            default: fd00::a03:0/118
            description:
              - Typically Loopback1 and Anycast Loopback IPv6 Address Range
            ndfc_gui_label: Underlay VTEP Loopback IPv6 Range
            ndfc_gui_section: Resources
            required: true
            type: ipv6_subnet
          LOOPBACK1_IP_RANGE:
            default: 10.3.0.0/22
            description:
              - Typically Loopback1 IP Address Range
            ndfc_gui_label: Underlay VTEP Loopback IP Range
            ndfc_gui_section: Resources
            required: true
            type: ipv4_subnet
          MACSEC_ALGORITHM:
            default: AES_128_CMAC
            description:
              - AES_128_CMAC or AES_256_CMAC
            ndfc_gui_label: MACsec Primary Cryptographic Algorithm
            ndfc_gui_section: Advanced
            required: true
            type: enum
          MACSEC_CIPHER_SUITE:
            default: GCM-AES-XPN-256
            description:
              - Configure Cipher Suite
            ndfc_gui_label: MACsec Cipher Suite
            ndfc_gui_section: Advanced
            required: true
            type: enum
          MACSEC_FALLBACK_ALGORITHM:
            default: AES_128_CMAC
            description:
              - AES_128_CMAC or AES_256_CMAC
            ndfc_gui_label: MACsec Fallback Cryptographic Algorithm
            ndfc_gui_section: Advanced
            required: true
            type: enum
          MACSEC_FALLBACK_KEY_STRING:
            default: ""
            description:
              - Cisco Type 7 Encrypted Octet String
            ndfc_gui_label: MACsec Fallback Key String
            ndfc_gui_section: Advanced
            required: true
            type: str
          MACSEC_KEY_STRING:
            default: ""
            description:
              - Cisco Type 7 Encrypted Octet String
            ndfc_gui_label: MACsec Primary Key String
            ndfc_gui_section: Advanced
            required: true
            type: str
          MACSEC_REPORT_TIMER:
            default: 5
            description:
              - MACsec Operational Status periodic report timer in minutes
            ndfc_gui_label: MACsec Status Report Timer
            ndfc_gui_section: Advanced
            required: true
            type: int
          MGMT_GW:
            default: ""
            description:
              - Default Gateway For Management VRF On The Switch
            ndfc_gui_label: Switch Mgmt Default Gateway
            ndfc_gui_section: Bootstrap
            required: true
            type: ipv4
          MGMT_PREFIX:
            default: 24
            description:
              - No description available
            max: 30
            min: 8
            ndfc_gui_label: Switch Mgmt IP Subnet Prefix
            ndfc_gui_section: Bootstrap
            required: true
            type: int
          MGMT_V6PREFIX:
            default: 64
            description:
              - No description available
            max: 126
            min: 64
            ndfc_gui_label: Switch Mgmt IPv6 Subnet Prefix
            ndfc_gui_section: Bootstrap
            required: false
            type: int
          MPLS_HANDOFF:
            default: 0
            description:
              - No description available
            ndfc_gui_label: Enable MPLS Handoff
            ndfc_gui_section: Advanced
            required: false
            type: bool
          MPLS_LB_ID:
            default: 101
            description:
              - "Used for VXLAN to MPLS SR/LDP Handoff "
            max: 1023
            min: 0
            ndfc_gui_label: Underlay MPLS Loopback Id
            ndfc_gui_section: Advanced
            required: true
            type: int
          MPLS_LOOPBACK_IP_RANGE:
            default: 10.101.0.0/25
            description:
              - Used for VXLAN to MPLS SR/LDP Handoff
            ndfc_gui_label: Underlay MPLS Loopback IP Range
            ndfc_gui_section: Resources
            required: true
            type: ipv4_subnet
          MST_INSTANCE_RANGE:
            default: 0
            description:
              - "MST instance range, Example: 0-3,5,7-9, Default is 0"
            ndfc_gui_label: MST Instance Range
            ndfc_gui_section: Advanced
            required: true
            type: integerRange
          MULTICAST_GROUP_SUBNET:
            default: 239.1.1.0/25
            description:
              - Multicast pool prefix between 8 to 30. A multicast group IP from
                this pool is used for BUM traffic for each overlay network.
            ndfc_gui_label: Multicast Group Subnet
            ndfc_gui_section: Replication
            required: true
            type: ipv4_subnet
          NETFLOW_EXPORTER_LIST:
            default: ""
            description:
              - One or Multiple Netflow Exporters
            ndfc_gui_label: Netflow Exporter
            ndfc_gui_section: Flow Monitor
            required: true
            type: structureArray
          NETFLOW_MONITOR_LIST:
            default: ""
            description:
              - One or Multiple Netflow Monitors
            ndfc_gui_label: Netflow Monitor
            ndfc_gui_section: Flow Monitor
            required: true
            type: structureArray
          NETFLOW_RECORD_LIST:
            default: ""
            description:
              - One or Multiple Netflow Records
            ndfc_gui_label: Netflow Record
            ndfc_gui_section: Flow Monitor
            required: true
            type: structureArray
          NETWORK_VLAN_RANGE:
            default: 2300-2999
            description:
              - "Per Switch Overlay Network VLAN Range "
            max: 4094
            min: 2
            ndfc_gui_label: Network VLAN Range
            ndfc_gui_section: Resources
            required: true
            type: integerRange
          NTP_SERVER_IP_LIST:
            default: ""
            description:
              - Comma separated list of IP Addresses(v4/v6)
            ndfc_gui_label: NTP Server IPs
            ndfc_gui_section: Manageability
            required: false
            type: ipAddressList
          NTP_SERVER_VRF:
            default: ""
            description:
              - One VRF for all NTP servers or a comma separated list of VRFs,
                one per NTP server
            ndfc_gui_label: NTP Server VRFs
            ndfc_gui_section: Manageability
            required: false
            type: string[]
          NVE_LB_ID:
            default: 1
            description:
              - No description available
            max: 1023
            min: 0
            ndfc_gui_label: Underlay VTEP Loopback Id
            ndfc_gui_section: Protocols
            required: true
            type: int
          NXAPI_HTTPS_PORT:
            default: 443
            description:
              - No description available
            ndfc_gui_label: NX-API HTTPS Port Number
            ndfc_gui_section: Advanced
            required: false
            type: int
          NXAPI_HTTP_PORT:
            default: 80
            description:
              - No description available
            ndfc_gui_label: NX-API HTTP Port Number
            ndfc_gui_section: Advanced
            required: false
            type: int
          OBJECT_TRACKING_NUMBER_RANGE:
            default: 100-299
            description:
              - "Per switch tracked object ID Range "
            max: 512
            min: 1
            ndfc_gui_label: Tracked Object ID Range
            ndfc_gui_section: Resources
            required: false
            type: integerRange
          OSPF_AREA_ID:
            default: 0.0.0.0
            description:
              - OSPF Area Id in IP address format
            ndfc_gui_label: OSPF Area Id
            ndfc_gui_section: Protocols
            required: true
            type: str
          OSPF_AUTH_ENABLE:
            default: 0
            description:
              - No description available
            ndfc_gui_label: Enable OSPF Authentication
            ndfc_gui_section: Protocols
            required: false
            type: bool
          OSPF_AUTH_KEY:
            default: ""
            description:
              - 3DES Encrypted
            ndfc_gui_label: OSPF Authentication Key
            ndfc_gui_section: Protocols
            required: true
            type: str
          OSPF_AUTH_KEY_ID:
            default: 127
            description:
              - No description available
            max: 255
            min: 0
            ndfc_gui_label: OSPF Authentication Key ID
            ndfc_gui_section: Protocols
            required: true
            type: int
          OVERLAY_MODE:
            default: cli
            description:
              - VRF/Network configuration using config-profile or CLI
            ndfc_gui_label: Overlay Mode
            ndfc_gui_section: Advanced
            required: false
            type: enum
          PER_VRF_LOOPBACK_AUTO_PROVISION:
            default: 0
            description:
              - Auto provision a loopback on a VTEP on VRF attachment
            ndfc_gui_label: Per VRF Per VTEP Loopback Auto-Provisioning
            ndfc_gui_section: Resources
            required: false
            type: bool
          PER_VRF_LOOPBACK_IP_RANGE:
            default: 10.5.0.0/22
            description:
              - Prefix pool to assign IP addresses to loopbacks on VTEPs on a
                per VRF basis
            ndfc_gui_label: Per VRF Per VTEP IP Pool for Loopbacks
            ndfc_gui_section: Resources
            required: true
            type: ipv4_subnet
          PHANTOM_RP_LB_ID1:
            default: 2
            description:
              - "Used for Bidir-PIM Phantom RP "
            max: 1023
            min: 0
            ndfc_gui_label: Underlay Primary RP Loopback Id
            ndfc_gui_section: Replication
            required: true
            type: int
          PHANTOM_RP_LB_ID2:
            default: 3
            description:
              - "Used for Fallback Bidir-PIM Phantom RP "
            max: 1023
            min: 0
            ndfc_gui_label: Underlay Backup RP Loopback Id
            ndfc_gui_section: Replication
            required: true
            type: int
          PHANTOM_RP_LB_ID3:
            default: 4
            description:
              - "Used for second Fallback Bidir-PIM Phantom RP "
            max: 1023
            min: 0
            ndfc_gui_label: Underlay Second Backup RP Loopback Id
            ndfc_gui_section: Replication
            required: true
            type: int
          PHANTOM_RP_LB_ID4:
            default: 5
            description:
              - "Used for third Fallback Bidir-PIM Phantom RP "
            max: 1023
            min: 0
            ndfc_gui_label: Underlay Third Backup RP Loopback Id
            ndfc_gui_section: Replication
            required: true
            type: int
          PIM_HELLO_AUTH_ENABLE:
            default: 0
            description:
              - Valid for IPv4 Underlay only
            ndfc_gui_label: Enable PIM Hello Authentication
            ndfc_gui_section: Protocols
            required: false
            type: bool
          PIM_HELLO_AUTH_KEY:
            default: ""
            description:
              - 3DES Encrypted
            ndfc_gui_label: PIM Hello Authentication Key
            ndfc_gui_section: Protocols
            required: true
            type: str
          PM_ENABLE:
            default: 0
            description:
              - No description available
            ndfc_gui_label: Enable Performance Monitoring
            ndfc_gui_section: ""
            required: false
            type: bool
          POWER_REDUNDANCY_MODE:
            choices:
              - ps-redundant
              - combined
              - insrc-redundant
            default: ps-redundant
            description:
              - Default Power Supply Mode For The Fabric
            ndfc_gui_label: Power Supply Mode
            ndfc_gui_section: Advanced
            required: true
            type: str
          PTP_DOMAIN_ID:
            default: 0
            description:
              - "Multiple Independent PTP Clocking Subdomains on a Single
                Network "
            max: 127
            min: 0
            ndfc_gui_label: PTP Domain Id
            ndfc_gui_section: Advanced
            required: true
            type: int
          PTP_LB_ID:
            default: 0
            description:
              - No description available
            max: 1023
            min: 0
            ndfc_gui_label: PTP Source Loopback Id
            ndfc_gui_section: Advanced
            required: true
            type: int
          REPLICATION_MODE:
            choices:
              - Multicast
              - Ingress
            default: Multicast
            description:
              - Replication Mode for BUM Traffic
            ndfc_gui_label: Replication Mode
            ndfc_gui_section: Replication
            required: true
            type: str
          ROUTER_ID_RANGE:
            default: 10.2.0.0/23
            description:
              - No description available
            ndfc_gui_label: BGP Router ID Range for IPv6 Underlay
            ndfc_gui_section: Resources
            required: true
            type: ipv4_subnet
          ROUTE_MAP_SEQUENCE_NUMBER_RANGE:
            default: 1-65534
            description:
              - No description available
            max: 65534
            min: 1
            ndfc_gui_label: Route Map Sequence Number Range
            ndfc_gui_section: Resources
            required: true
            type: integerRange
          RP_COUNT:
            choices:
              - 2
              - 4
            default: 2
            description:
              - Number of spines acting as Rendezvous-Point (RP)
            ndfc_gui_label: Rendezvous-Points
            ndfc_gui_section: Replication
            required: true
            type: int
          RP_LB_ID:
            default: 254
            description:
              - No description available
            max: 1023
            min: 0
            ndfc_gui_label: Underlay RP Loopback Id
            ndfc_gui_section: Replication
            required: true
            type: int
          RP_MODE:
            choices:
              - asm
              - bidir
            default: asm
            description:
              - Multicast RP Mode
            ndfc_gui_label: RP Mode
            ndfc_gui_section: Replication
            required: true
            type: str
          RR_COUNT:
            choices:
              - 2
              - 4
            default: 2
            description:
              - Number of spines acting as Route-Reflectors
            ndfc_gui_label: Route-Reflectors
            ndfc_gui_section: ""
            required: true
            type: int
          SEED_SWITCH_CORE_INTERFACES:
            default: ""
            description:
              - Core-facing Interface list on Seed Switch (e.g. e1/1-30,e1/32)
            ndfc_gui_label: Seed Switch Fabric Interfaces
            ndfc_gui_section: Bootstrap
            required: false
            type: interfaceRange
          SERVICE_NETWORK_VLAN_RANGE:
            default: 3000-3199
            description:
              - "Per Switch Overlay Service Network VLAN Range "
            max: 4094
            min: 2
            ndfc_gui_label: Service Network VLAN Range
            ndfc_gui_section: Resources
            required: true
            type: integerRange
          SITE_ID:
            default: ""
            description:
              - For EVPN Multi-Site Support . Defaults to Fabric ASN
            max: 281474976710655
            min: 1
            ndfc_gui_label: Site Id
            ndfc_gui_section: Advanced
            required: false
            type: str
          SLA_ID_RANGE:
            default: 10000-19999
            description:
              - "Per switch SLA ID Range "
            max: 2147483647
            min: 1
            ndfc_gui_label: Service Level Agreement (SLA) ID Range
            ndfc_gui_section: Resources
            required: false
            type: integerRange
          SNMP_SERVER_HOST_TRAP:
            default: 1
            description:
              - Configure NDFC as a receiver for SNMP traps
            ndfc_gui_label: Enable NDFC as Trap Host
            ndfc_gui_section: Advanced
            required: false
            type: bool
          SPINE_SWITCH_CORE_INTERFACES:
            default: ""
            description:
              - Core-facing Interface list on all Spines (e.g. e1/1-30,e1/32)
            ndfc_gui_label: Spine Switch Fabric Interfaces
            ndfc_gui_section: Bootstrap
            required: false
            type: interfaceRange
          STATIC_UNDERLAY_IP_ALLOC:
            default: 0
            description:
              - Checking this will disable Dynamic Underlay IP Address
                Allocations
            ndfc_gui_label: Manual Underlay IP Address Allocation
            ndfc_gui_section: Resources
            required: false
            type: bool
          STP_BRIDGE_PRIORITY:
            default: 0
            description:
              - Bridge priority for the spanning tree in increments of 4096
            ndfc_gui_label: Spanning Tree Bridge Priority
            ndfc_gui_section: Advanced
            required: true
            type: enum
          STP_ROOT_OPTION:
            choices:
              - rpvst+
              - mst
              - unmanaged
            default: unmanaged
            description:
              - "Which protocol to use for configuring root bridge? rpvst+:
                Rapid Per-VLAN Spanning Tree, mst: Multiple Spanning Tree,
                unmanaged (default): STP Root not managed by NDFC"
            ndfc_gui_label: Spanning Tree Root Bridge Protocol
            ndfc_gui_section: Advanced
            required: false
            type: str
          STP_VLAN_RANGE:
            default: 1-3967
            description:
              - "Vlan range, Example: 1,3-5,7,9-11, Default is 1-3967"
            ndfc_gui_label: Spanning Tree VLAN Range
            ndfc_gui_section: Advanced
            required: true
            type: integerRange
          STRICT_CC_MODE:
            default: 0
            description:
              - Enable bi-directional compliance checks to flag additional
                configs in the running config that are not in the
                intent/expected config
            ndfc_gui_label: Enable Strict Config Compliance
            ndfc_gui_section: Advanced
            required: false
            type: bool
          SUBINTERFACE_RANGE:
            default: 2-511
            description:
              - "Per Border Dot1q Range For VRF Lite Connectivity "
            max: 4093
            min: 2
            ndfc_gui_label: Subinterface Dot1q Range
            ndfc_gui_section: Resources
            required: true
            type: integerRange
          SUBNET_RANGE:
            default: 10.4.0.0/16
            description:
              - Address range to assign Numbered and Peer Link SVI IPs
            ndfc_gui_label: Underlay Subnet IP Range
            ndfc_gui_section: Resources
            required: true
            type: ipv4_subnet
          SUBNET_TARGET_MASK:
            choices:
              - 30
              - 31
            default: 30
            description:
              - Mask for Underlay Subnet IP Range
            ndfc_gui_label: Underlay Subnet IP Mask
            ndfc_gui_section: ""
            required: true
            type: int
          SYSLOG_SERVER_IP_LIST:
            default: ""
            description:
              - Comma separated list of IP Addresses(v4/v6)
            ndfc_gui_label: Syslog Server IPs
            ndfc_gui_section: Manageability
            required: false
            type: ipAddressList
          SYSLOG_SERVER_VRF:
            default: ""
            description:
              - One VRF for all Syslog servers or a comma separated list of
                VRFs, one per Syslog server
            ndfc_gui_label: Syslog Server VRFs
            ndfc_gui_section: Manageability
            required: false
            type: string[]
          SYSLOG_SEV:
            default: ""
            description:
              - "Comma separated list of Syslog severity values, one per Syslog
                server "
            max: 7
            min: 0
            ndfc_gui_label: Syslog Server Severity
            ndfc_gui_section: Manageability
            required: false
            type: string[]
          TCAM_ALLOCATION:
            default: 1
            description:
              - TCAM commands are automatically generated for VxLAN and vPC
                Fabric Peering when Enabled
            ndfc_gui_label: Enable TCAM Allocation
            ndfc_gui_section: Advanced
            required: false
            type: bool
          UNDERLAY_IS_V6:
            default: 0
            description:
              - If not enabled, IPv4 underlay is used
            ndfc_gui_label: Enable IPv6 Underlay
            ndfc_gui_section: ""
            required: false
            type: bool
          UNNUM_BOOTSTRAP_LB_ID:
            default: 253
            description:
              - No description available
            ndfc_gui_label: Bootstrap Seed Switch Loopback Interface ID
            ndfc_gui_section: Bootstrap
            required: true
            type: int
          UNNUM_DHCP_END:
            default: ""
            description:
              - Must be a subset of IGP/BGP Loopback Prefix Pool
            ndfc_gui_label: Switch Loopback DHCP Scope End Address
            ndfc_gui_section: Bootstrap
            required: true
            type: ipv4
          UNNUM_DHCP_START:
            default: ""
            description:
              - Must be a subset of IGP/BGP Loopback Prefix Pool
            ndfc_gui_label: Switch Loopback DHCP Scope Start Address
            ndfc_gui_section: Bootstrap
            required: true
            type: ipv4
          USE_LINK_LOCAL:
            default: 1
            description:
              - If not enabled, Spine-Leaf interfaces will use global IPv6
                addresses
            ndfc_gui_label: Enable IPv6 Link-Local Address
            ndfc_gui_section: ""
            required: false
            type: bool
          V6_SUBNET_RANGE:
            default: fd00::a04:0/112
            description:
              - IPv6 Address range to assign Numbered and Peer Link SVI IPs
            ndfc_gui_label: Underlay Subnet IPv6 Range
            ndfc_gui_section: Resources
            required: true
            type: ipv6_subnet
          V6_SUBNET_TARGET_MASK:
            choices:
              - 126
              - 127
            default: 126
            description:
              - Mask for Underlay Subnet IPv6 Range
            ndfc_gui_label: Underlay Subnet IPv6 Mask
            ndfc_gui_section: ""
            required: true
            type: int
          VPC_AUTO_RECOVERY_TIME:
            default: 360
            description:
              - No description available
            max: 3600
            min: 240
            ndfc_gui_label: vPC Auto Recovery Time (In Seconds)
            ndfc_gui_section: vPC
            required: true
            type: int
          VPC_DELAY_RESTORE:
            default: 150
            description:
              - No description available
            max: 3600
            min: 1
            ndfc_gui_label: vPC Delay Restore Time (In Seconds)
            ndfc_gui_section: vPC
            required: true
            type: int
          VPC_DOMAIN_ID_RANGE:
            default: 1-1000
            description:
              - vPC Domain id range to use for new pairings
            ndfc_gui_label: vPC Domain Id Range
            ndfc_gui_section: vPC
            required: false
            type: integerRange
          VPC_ENABLE_IPv6_ND_SYNC:
            default: 1
            description:
              - Enable IPv6 ND synchronization between vPC peers
            ndfc_gui_label: vPC IPv6 ND Synchronize
            ndfc_gui_section: vPC
            required: false
            type: bool
          VPC_PEER_KEEP_ALIVE_OPTION:
            choices:
              - loopback
              - management
            default: management
            description:
              - Use vPC Peer Keep Alive with Loopback or Management
            ndfc_gui_label: vPC Peer Keep Alive option
            ndfc_gui_section: vPC
            required: true
            type: str
          VPC_PEER_LINK_PO:
            default: 500
            description:
              - No description available
            max: 4096
            min: 1
            ndfc_gui_label: vPC Peer Link Port Channel ID
            ndfc_gui_section: vPC
            required: false
            type: integerRange
          VPC_PEER_LINK_VLAN:
            default: 3600
            description:
              - "VLAN range for vPC Peer Link SVI "
            max: 4094
            min: 2
            ndfc_gui_label: vPC Peer Link VLAN Range
            ndfc_gui_section: vPC
            required: true
            type: integerRange
          VRF_LITE_AUTOCONFIG:
            choices:
              - Manual
              - Back2Back&ToExternal
            default: Manual
            description:
              - VRF Lite Inter-Fabric Connection Deployment Options. If
                Back2Back&ToExternal is selected, VRF Lite IFCs are auto created
                between border devices of two Easy Fabrics, and between border
                devices in Easy Fabric and edge routers in External Fabric. The
                IP address is taken from the VRF Lite Subnet IP Range pool.
            ndfc_gui_label: VRF Lite Deployment
            ndfc_gui_section: Resources
            required: true
            type: str
          VRF_VLAN_RANGE:
            default: 2000-2299
            description:
              - "Per Switch Overlay VRF VLAN Range "
            max: 4094
            min: 2
            ndfc_gui_label: VRF VLAN Range
            ndfc_gui_section: Resources
            required: true
            type: integerRange
          default_network:
            choices:
              - Default_Network_Universal
              - Service_Network_Universal
            default: Default_Network_Universal
            description:
              - Default Overlay Network Template For Leafs
            ndfc_gui_label: Network Template
            ndfc_gui_section: Advanced
            required: true
            type: str
          default_pvlan_sec_network:
            choices:
              - Pvlan_Secondary_Network
            default: Pvlan_Secondary_Network
            description:
              - Default PVLAN Secondary Network Template
            ndfc_gui_label: PVLAN Secondary Network Template
            ndfc_gui_section: Advanced
            required: false
            type: str
          default_vrf:
            choices:
              - Default_VRF_Universal
            default: Default_VRF_Universal
            description:
              - Default Overlay VRF Template For Leafs
            ndfc_gui_label: VRF Template
            ndfc_gui_section: Advanced
            required: true
            type: str
          enableRealTimeBackup:
            default: ""
            description:
              - Backup hourly only if there is any config deployment since last
                backup
            ndfc_gui_label: Hourly Fabric Backup
            ndfc_gui_section: Configuration Backup
            required: false
            type: bool
          enableScheduledBackup:
            default: ""
            description:
              - Backup at the specified time
            ndfc_gui_label: Scheduled Fabric Backup
            ndfc_gui_section: Configuration Backup
            required: false
            type: bool
          network_extension_template:
            choices:
              - Default_Network_Extension_Universal
            default: Default_Network_Extension_Universal
            description:
              - Default Overlay Network Template For Borders
            ndfc_gui_label: Network Extension Template
            ndfc_gui_section: Advanced
            required: true
            type: str
          scheduledTime:
            default: ""
            description:
              - Time (UTC) in 24hr format. (00:00 to 23:59)
            ndfc_gui_label: Scheduled Time
            ndfc_gui_section: Configuration Backup
            required: true
            type: str
          vrf_extension_template:
            choices:
              - Default_VRF_Extension_Universal
            default: Default_VRF_Extension_Universal
            description:
              - Default Overlay VRF Template For Borders
            ndfc_gui_label: VRF Extension Template
            ndfc_gui_section: Advanced
            required: true
            type: str
      VXLAN_EVPN_FABRIC_MSD_PARAMETERS:
        description:
          - VXLAN EVPN Multi-Site fabric specific parameters.
          - Domain that can contain multiple VXLAN EVPN Fabrics with
            Layer-2/Layer-3 Overlay Extensions and other Fabric Types.
          - The indentation of these parameters is meant only to logically group
            them.
          - They should be at the same YAML level as FABRIC_TYPE and FABRIC_NAME.
        suboptions:
          ANYCAST_GW_MAC:
            default: 2020.0000.00aa
            description:
              - Shared MAC address for all leaves
            ndfc_gui_label: Anycast-Gateway-MAC
            ndfc_gui_section: ""
            required: false
            type: str
          BGP_RP_ASN:
            default: ""
            description:
              - 1-4294967295 | 1-65535.0-65535, e.g. 65000, 65001
            ndfc_gui_label: Multi-Site Route Server BGP ASN List
            ndfc_gui_section: DCI
            required: false
            type: str
          BGW_ROUTING_TAG:
            default: 54321
            description:
              - Routing tag associated with IP address of loopback and DCI
                interfaces
            ndfc_gui_label: Border Gateway IP TAG
            ndfc_gui_section: ""
            required: false
            type: str
          BORDER_GWY_CONNECTIONS:
            choices:
              - Manual
              - Centralized_To_Route_Server
              - Direct_To_BGWS
            default: Manual
            description:
              - Manual, Auto Overlay EVPN Peering to Route Servers, Auto Overlay
                EVPN Direct Peering to Border Gateways
            ndfc_gui_label: Multi-Site Overlay IFC Deployment Method
            ndfc_gui_section: DCI
            required: true
            type: str
          CLOUDSEC_ALGORITHM:
            default: AES_128_CMAC
            description:
              - AES_128_CMAC or AES_256_CMAC
            ndfc_gui_label: CloudSec Cryptographic Algorithm
            ndfc_gui_section: DCI
            required: true
            type: enum
          CLOUDSEC_AUTOCONFIG:
            default: 0
            description:
              - Auto Config CloudSec on Border Gateways
            ndfc_gui_label: Multi-Site CloudSec
            ndfc_gui_section: DCI
            required: false
            type: bool
          CLOUDSEC_ENFORCEMENT:
            default: ""
            description:
              - If set to strict, data across site must be encrypted.
            ndfc_gui_label: CloudSec Enforcement
            ndfc_gui_section: DCI
            required: true
            type: enum
          CLOUDSEC_KEY_STRING:
            default: ""
            description:
              - Cisco Type 7 Encrypted Octet String
            ndfc_gui_label: CloudSec Key String
            ndfc_gui_section: DCI
            required: true
            type: str
          CLOUDSEC_REPORT_TIMER:
            default: 5
            description:
              - CloudSec Operational Status periodic report timer in minutes
            ndfc_gui_label: CloudSec Status Report Timer
            ndfc_gui_section: DCI
            required: true
            type: int
          DCI_SUBNET_RANGE:
            default: 10.10.1.0/24
            description:
              - Address range to assign P2P DCI Links
            ndfc_gui_label: DCI Subnet IP Range
            ndfc_gui_section: Resources
            required: true
            type: ipv4_subnet
          DCI_SUBNET_TARGET_MASK:
            default: 30
            description:
              - "Target Mask for Subnet Range "
            max: 31
            min: 8
            ndfc_gui_label: Subnet Target Mask
            ndfc_gui_section: Resources
            required: true
            type: int
          DELAY_RESTORE:
            default: 300
            description:
              - Multi-Site underlay and overlay control plane convergence
                time  in seconds
            max: 1000
            min: 30
            ndfc_gui_label: Delay Restore time
            ndfc_gui_section: DCI
            required: false
            type: int
          ENABLE_BGP_BFD:
            default: 0
            description:
              - For auto-created Multi-Site Underlay IFCs
            ndfc_gui_label: BGP BFD on Multi-Site Underlay IFC
            ndfc_gui_section: DCI
            required: false
            type: bool
          ENABLE_BGP_LOG_NEIGHBOR_CHANGE:
            default: 0
            description:
              - For auto-created Multi-Site Underlay IFCs
            ndfc_gui_label: BGP log neighbor change on Multi-Site Underlay IFC
            ndfc_gui_section: DCI
            required: false
            type: bool
          ENABLE_BGP_SEND_COMM:
            default: 0
            description:
              - For auto-created Multi-Site Underlay IFCs
            ndfc_gui_label: BGP Send-community on Multi-Site Underlay IFC
            ndfc_gui_section: DCI
            required: false
            type: bool
          ENABLE_PVLAN:
            default: 0
            description:
              - Enable PVLAN on MSD and its child fabrics
            ndfc_gui_label: Enable Private VLAN (PVLAN)
            ndfc_gui_section: ""
            required: false
            type: bool
          ENABLE_RS_REDIST_DIRECT:
            default: 0
            description:
              - For auto-created Multi-Site overlay IFCs in Route Servers.
                Applicable only when Multi-Site Overlay IFC Deployment Method is
                Centralized_To_Route_Server.
            ndfc_gui_label: Enable redistribute direct on Route Servers
            ndfc_gui_section: DCI
            required: false
            type: bool
          FABRIC_NAME:
            default: ""
            description:
              - Please provide the fabric name to create it (Max Size 64)
            ndfc_gui_label: Fabric Name
            ndfc_gui_section: ""
            required: true
            type: str
          L2_SEGMENT_ID_RANGE:
            default: 30000-49000
            description:
              - "Overlay Network Identifier Range "
            max: 16777214
            min: 1
            ndfc_gui_label: Layer 2 VXLAN VNI Range
            ndfc_gui_section: ""
            required: true
            type: integerRange
          L3_PARTITION_ID_RANGE:
            default: 50000-59000
            description:
              - "Overlay VRF Identifier Range "
            max: 16777214
            min: 1
            ndfc_gui_label: Layer 3 VXLAN VNI Range
            ndfc_gui_section: ""
            required: true
            type: integerRange
          LOOPBACK100_IP_RANGE:
            default: 10.10.0.0/24
            description:
              - Typically Loopback100 IP Address Range
            ndfc_gui_label: Multi-Site VTEP VIP Loopback IP Range
            ndfc_gui_section: Resources
            required: true
            type: ipv4_subnet
          MS_IFC_BGP_AUTH_KEY_TYPE:
            choices:
              - 3
              - 7
            default: 3
            description:
              - "BGP Key Encryption Type: 3 - 3DES, 7 - Cisco"
            ndfc_gui_label: eBGP Authentication Key Encryption Type
            ndfc_gui_section: DCI
            required: true
            type: str
          MS_IFC_BGP_PASSWORD:
            default: ""
            description:
              - Encrypted eBGP Password Hex String
            ndfc_gui_label: eBGP Password
            ndfc_gui_section: DCI
            required: true
            type: str
          MS_IFC_BGP_PASSWORD_ENABLE:
            default: 0
            description:
              - eBGP password for Multi-Site underlay/overlay IFCs
            ndfc_gui_label: Enable Multi-Site eBGP Password
            ndfc_gui_section: DCI
            required: false
            type: bool
          MS_LOOPBACK_ID:
            default: 100
            description:
              - No description available
            max: 1023
            min: 0
            ndfc_gui_label: Multi-Site VTEP VIP Loopback Id
            ndfc_gui_section: ""
            required: true
            type: int
          MS_UNDERLAY_AUTOCONFIG:
            default: 0
            description:
              - No description available
            ndfc_gui_label: Multi-Site Underlay IFC Auto Deployment Flag
            ndfc_gui_section: DCI
            required: false
            type: bool
          RP_SERVER_IP:
            default: ""
            description:
              - Multi-Site Route-Server peer list (typically loopback IP address
                on Route-Server for Multi-Site EVPN peering with BGWs), e.g.
                128.89.0.1, 128.89.0.2
            ndfc_gui_label: Multi-Site Route Server List
            ndfc_gui_section: DCI
            required: false
            type: ipAddressList
          RS_ROUTING_TAG:
            default: 54321
            description:
              - Routing tag associated with Route Server IP for redistribute
                direct. This is the IP used in eBGP EVPN peering.
            ndfc_gui_label: Route Server IP TAG
            ndfc_gui_section: DCI
            required: false
            type: str
          TOR_AUTO_DEPLOY:
            default: 0
            description:
              - Enables Overlay VLANs on uplink between ToRs and Leafs
            ndfc_gui_label: ToR Auto-deploy Flag
            ndfc_gui_section: ""
            required: false
            type: bool
          default_network:
            choices:
              - Default_Network_Universal
              - Service_Network_Universal
            default: Default_Network_Universal
            description:
              - Default Overlay Network Template For Leafs
            ndfc_gui_label: Network Template
            ndfc_gui_section: ""
            required: true
            type: str
          default_pvlan_sec_network:
            choices:
              - Pvlan_Secondary_Network
            default: Pvlan_Secondary_Network
            description:
              - Default PVLAN Secondary Network Template
            ndfc_gui_label: PVLAN Secondary Network Template
            ndfc_gui_section: ""
            required: false
            type: str
          default_vrf:
            choices:
              - Default_VRF_Universal
            default: Default_VRF_Universal
            description:
              - Default Overlay VRF Template For Leafs
            ndfc_gui_label: VRF Template
            ndfc_gui_section: ""
            required: true
            type: str
          enableScheduledBackup:
            default: ""
            description:
              - "Backup at the specified time. Note: Fabric Backup/Restore
                functionality is being deprecated for MSD fabrics.
                Recommendation is to use NDFC Backup & Restore"
            ndfc_gui_label: Scheduled Fabric Backup
            ndfc_gui_section: Configuration Backup
            required: false
            type: bool
          network_extension_template:
            choices:
              - Default_Network_Extension_Universal
            default: Default_Network_Extension_Universal
            description:
              - Default Overlay Network Template For Borders
            ndfc_gui_label: Network Extension Template
            ndfc_gui_section: ""
            required: true
            type: str
          scheduledTime:
            default: ""
            description:
              - Time (UTC) in 24hr format. (00:00 to 23:59)
            ndfc_gui_label: Scheduled Time
            ndfc_gui_section: Configuration Backup
            required: true
            type: str
          vrf_extension_template:
            choices:
              - Default_VRF_Extension_Universal
            default: Default_VRF_Extension_Universal
            description:
              - Default Overlay VRF Template For Borders
            ndfc_gui_label: VRF Extension Template
            ndfc_gui_section: ""
            required: true
            type: str
      LAN_CLASSIC_PARAMETERS:
        description:
          - LAN Classic fabric specific parameters.
          - The following parameters are specific to Classic LAN fabrics.
          - Fabric to manage a legacy Classic LAN deployment with Nexus switches.
          - The indentation of these parameters is meant only to logically group
            them.
          - They should be at the same YAML level as FABRIC_TYPE and FABRIC_NAME.
        type: list
        elements: dict
        suboptions:
          AAA_REMOTE_IP_ENABLED:
            default: 0
            description:
              - Enable only, when IP Authorization is enabled in the AAA Server
            ndfc_gui_label: Enable AAA IP Authorization
            ndfc_gui_section: Advanced
            required: false
            type: bool
          AAA_SERVER_CONF:
            default: ""
            description:
              - AAA Configurations
            ndfc_gui_label: AAA Freeform Config
            ndfc_gui_section: Advanced
            required: false
            type: str
          BOOTSTRAP_CONF:
            default: ""
            description:
              - Additional CLIs required during device bootup/login e.g.
                AAA/Radius
            ndfc_gui_label: Bootstrap Freeform Config
            ndfc_gui_section: Bootstrap
            required: false
            type: str
          BOOTSTRAP_ENABLE:
            default: 0
            description:
              - Automatic IP Assignment For POAP
            ndfc_gui_label: Enable Bootstrap (For NX-OS Switches Only)
            ndfc_gui_section: Bootstrap
            required: false
            type: bool
          BOOTSTRAP_MULTISUBNET:
            default: "#Scope_Start_IP, Scope_End_IP, Scope_Default_Gateway,
              Scope_Subnet_Prefix"
            description:
              - "lines with # prefix are ignored here"
            ndfc_gui_label: DHCPv4 Multi Subnet Scope
            ndfc_gui_section: Bootstrap
            required: false
            type: str
          CDP_ENABLE:
            default: 0
            description:
              - Enable CDP on management interface
            ndfc_gui_label: Enable CDP for Bootstrapped Switch
            ndfc_gui_section: Advanced
            required: false
            type: bool
          DHCP_ENABLE:
            default: 0
            description:
              - Automatic IP Assignment For POAP From Local DHCP Server
            ndfc_gui_label: Enable Local DHCP Server
            ndfc_gui_section: Bootstrap
            required: false
            type: bool
          DHCP_END:
            default: ""
            description:
              - End Address For Switch POAP
            ndfc_gui_label: DHCP Scope End Address
            ndfc_gui_section: Bootstrap
            required: true
            type: ipv4
          DHCP_IPV6_ENABLE:
            choices:
              - DHCPv4
              - DHCPv6
            default: DHCPv4
            description:
              - No description available
            ndfc_gui_label: DHCP Version
            ndfc_gui_section: Bootstrap
            required: false
            type: str
          DHCP_START:
            default: ""
            description:
              - Start Address For Switch POAP
            ndfc_gui_label: DHCP Scope Start Address
            ndfc_gui_section: Bootstrap
            required: true
            type: ipv4
          ENABLE_AAA:
            default: 0
            description:
              - Include AAA configs from Advanced tab during device bootup
            ndfc_gui_label: Enable AAA Config
            ndfc_gui_section: Bootstrap
            required: false
            type: bool
          ENABLE_NETFLOW:
            default: 0
            description:
              - Enable Netflow on VTEPs
            ndfc_gui_label: Enable Netflow
            ndfc_gui_section: Flow Monitor
            required: false
            type: bool
          ENABLE_NXAPI:
            default: 0
            description:
              - Enable HTTPS NX-API
            ndfc_gui_label: Enable NX-API
            ndfc_gui_section: Advanced
            required: false
            type: bool
          ENABLE_NXAPI_HTTP:
            default: 0
            description:
              - No description available
            ndfc_gui_label: Enable HTTP NX-API
            ndfc_gui_section: Advanced
            required: false
            type: bool
          FABRIC_FREEFORM:
            default: ""
            description:
              - Additional supported CLIs for all same OS (e.g. all NxOS etc)
                switches
            ndfc_gui_label: Fabric Freeform
            ndfc_gui_section: Advanced
            required: false
            type: str
          FABRIC_NAME:
            default: ""
            description:
              - Please provide the fabric name to create it (Max Size 64)
            ndfc_gui_label: Fabric Name
            ndfc_gui_section: ""
            required: true
            type: str
          FEATURE_PTP:
            default: 0
            description:
              - No description available
            ndfc_gui_label: Enable Precision Time Protocol (PTP)
            ndfc_gui_section: Advanced
            required: false
            type: bool
          INBAND_ENABLE:
            default: 0
            description:
              - "Enable POAP over Inband Interface (Pre-req: Inband Mgmt Knob
                should be Enabled)"
            ndfc_gui_label: Enable Inband POAP
            ndfc_gui_section: Bootstrap
            required: false
            type: bool
          INBAND_MGMT:
            default: 0
            description:
              - Import switches with inband connectivity
            ndfc_gui_label: Inband Mgmt
            ndfc_gui_section: Advanced
            required: false
            type: bool
          IS_READ_ONLY:
            default: 1
            description:
              - If enabled, fabric is only monitored. No configuration will be
                deployed
            ndfc_gui_label: Fabric Monitor Mode
            ndfc_gui_section: ""
            required: false
            type: bool
          MGMT_GW:
            default: ""
            description:
              - Default Gateway For Management VRF On The Switch
            ndfc_gui_label: Switch Mgmt Default Gateway
            ndfc_gui_section: Bootstrap
            required: true
            type: ipv4
          MGMT_PREFIX:
            default: 24
            description:
              - No description available
            max: 30
            min: 8
            ndfc_gui_label: Switch Mgmt IP Subnet Prefix
            ndfc_gui_section: Bootstrap
            required: true
            type: int
          MGMT_V6PREFIX:
            default: 64
            description:
              - No description available
            max: 126
            min: 64
            ndfc_gui_label: Switch Mgmt IPv6 Subnet Prefix
            ndfc_gui_section: Bootstrap
            required: false
            type: int
          MPLS_HANDOFF:
            default: 0
            description:
              - No description available
            ndfc_gui_label: Enable MPLS Handoff
            ndfc_gui_section: Advanced
            required: false
            type: bool
          MPLS_LB_ID:
            default: 101
            description:
              - No description available
            max: 1023
            min: 0
            ndfc_gui_label: Underlay MPLS Loopback Id
            ndfc_gui_section: Advanced
            required: true
            type: int
          MPLS_LOOPBACK_IP_RANGE:
            default: 10.102.0.0/25
            description:
              - MPLS Loopback IP Address Range
            ndfc_gui_label: Underlay MPLS Loopback IP Range
            ndfc_gui_section: Resources
            required: true
            type: ipv4_subnet
          NETFLOW_EXPORTER_LIST:
            default: ""
            description:
              - One or Multiple Netflow Exporters
            ndfc_gui_label: Netflow Exporter
            ndfc_gui_section: Flow Monitor
            required: true
            type: structureArray
          NETFLOW_MONITOR_LIST:
            default: ""
            description:
              - One or Multiple Netflow Monitors
            ndfc_gui_label: Netflow Monitor
            ndfc_gui_section: Flow Monitor
            required: true
            type: structureArray
          NETFLOW_RECORD_LIST:
            default: ""
            description:
              - One or Multiple Netflow Records
            ndfc_gui_label: Netflow Record
            ndfc_gui_section: Flow Monitor
            required: true
            type: structureArray
          NETFLOW_SAMPLER_LIST:
            default: ""
            description:
              - One or multiple netflow Samplers. Applicable to N7K only
            ndfc_gui_label: Netflow Sampler
            ndfc_gui_section: Flow Monitor
            required: false
            type: structureArray
          NXAPI_HTTPS_PORT:
            default: 443
            description:
              - No description available
            ndfc_gui_label: NX-API HTTPS Port Number
            ndfc_gui_section: Advanced
            required: false
            type: int
          NXAPI_HTTP_PORT:
            default: 80
            description:
              - No description available
            ndfc_gui_label: NX-API HTTP Port Number
            ndfc_gui_section: Advanced
            required: false
            type: int
          PM_ENABLE:
            default: 0
            description:
              - No description available
            ndfc_gui_label: Enable Performance Monitoring (For NX-OS Switches Only)
            ndfc_gui_section: ""
            required: false
            type: bool
          POWER_REDUNDANCY_MODE:
            choices:
              - ps-redundant
              - combined
              - insrc-redundant
            default: ps-redundant
            description:
              - Default Power Supply Mode For Bootstrapped NX-OS Switches
            ndfc_gui_label: Power Supply Mode
            ndfc_gui_section: Advanced
            required: true
            type: str
          PTP_DOMAIN_ID:
            default: 0
            description:
              - "Multiple Independent PTP Clocking Subdomains on a Single
                Network "
            max: 127
            min: 0
            ndfc_gui_label: PTP Domain Id
            ndfc_gui_section: Advanced
            required: true
            type: int
          PTP_LB_ID:
            default: 0
            description:
              - No description available
            max: 1023
            min: 0
            ndfc_gui_label: PTP Source Loopback Id
            ndfc_gui_section: Advanced
            required: true
            type: int
          SNMP_SERVER_HOST_TRAP:
            default: 1
            description:
              - Configure NDFC as a receiver for SNMP traps
            ndfc_gui_label: Enable NDFC as Trap Host
            ndfc_gui_section: Advanced
            required: false
            type: bool
          SUBINTERFACE_RANGE:
            default: 2-511
            description:
              - "Per Border Dot1q Range For VRF Lite Connectivity "
            max: 4093
            min: 2
            ndfc_gui_label: Subinterface Dot1q Range
            ndfc_gui_section: Resources
            required: true
            type: integerRange
          enableRealTimeBackup:
            default: 0
            description:
              - Backup hourly only if there is any config deployment since last
                backup
            ndfc_gui_label: Hourly Fabric Backup
            ndfc_gui_section: Configuration Backup
            required: false
            type: bool
          enableScheduledBackup:
            default: 0
            description:
              - Backup at the specified time
            ndfc_gui_label: Scheduled Fabric Backup
            ndfc_gui_section: Configuration Backup
            required: false
            type: bool
          scheduledTime:
            default: ""
            description:
              - Time (UTC) in 24hr format. (00:00 to 23:59)
            ndfc_gui_label: Scheduled Time
            ndfc_gui_section: Configuration Backup
            required: true
            type: str
"""

EXAMPLES = """

# Create the following fabrics with default configuration values
# if they don't already exist.  If they exist, the playbook will
# exit without doing anything.
# - 1. VXLAN EVPN fabric
# - 1. VXLAN EVPN Multi-Site fabric
# - 1. LAN Classic fabric

- name: Create fabrics
  cisco.dcnm.dcnm_fabric:
    state: merged
    config:
    -   FABRIC_NAME: VXLAN_Fabric
        FABRIC_TYPE: VXLAN_EVPN
        BGP_AS: 65000
    -   FABRIC_NAME: MSD_Fabric
        FABRIC_TYPE: VXLAN_EVPN_MSD
    -   FABRIC_NAME: LAN_Fabric
        FABRIC_TYPE: LAN_CLASSIC
  register: result
- debug:
    var: result

# Update the above fabrics with additional configurations.

- name: Update fabrics
  cisco.dcnm.dcnm_fabric:
    state: merged
    config:
    -   FABRIC_NAME: VXLAN_Fabric
        FABRIC_TYPE: VXLAN_EVPN
        BGP_AS: 65000
        ANYCAST_GW_MAC: 0001.aabb.ccdd
        UNDERLAY_IS_V6: false
        DEPLOY: false
    -   FABRIC_NAME: MSD_Fabric
        FABRIC_TYPE: VXLAN_EVPN_MSD
        LOOPBACK100_IP_RANGE: 10.22.0.0/24
        DEPLOY: false
    -   FABRIC_NAME: LAN_Fabric
        FABRIC_TYPE: LAN_CLASSIC
        BOOTSTRAP_ENABLE: false
        IS_READ_ONLY: false
        DEPLOY: false
  register: result
- debug:
    var: result

# Use replaced state to return the fabrics to their default configurations.

- name: Return fabrics to default configuration.
  cisco.dcnm.dcnm_fabric:
    state: replaced
    config:
    -   FABRIC_NAME: VXLAN_Fabric
        FABRIC_TYPE: VXLAN_EVPN
        BGP_AS: 65000
        DEPLOY: false
    -   FABRIC_NAME: MSD_Fabric
        FABRIC_TYPE: VXLAN_EVPN_MSD
        DEPLOY: false
    -   FABRIC_NAME: LAN_Fabric
        FABRIC_TYPE: LAN_CLASSIC
        DEPLOY: false
  register: result
- debug:
    var: result

# Query the fabrics to get their current configurations.

- name: Query the fabrics.
  cisco.dcnm.dcnm_fabric:
    state: query
    config:
    -   FABRIC_NAME: VXLAN_Fabric
    -   FABRIC_NAME: MSD_Fabric
    -   FABRIC_NAME: LAN_Fabric
  register: result
- debug:
    var: result

# Delete the fabrics.

- name: Delete the fabrics.
  cisco.dcnm.dcnm_fabric:
    state: deleted
    config:
    -   FABRIC_NAME: VXLAN_Fabric
    -   FABRIC_NAME: MSD_Fabric
    -   FABRIC_NAME: LAN_Fabric
  register: result
- debug:
    var: result

"""
# pylint: disable=wrong-import-position
import copy
import inspect
import json
import logging

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.common.exceptions import \
    ControllerResponseError
from ansible_collections.cisco.dcnm.plugins.module_utils.common.log import Log
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.common import \
    FabricCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.create import \
    FabricCreateBulk
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.delete import \
    FabricDelete
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details import \
    FabricDetailsByName
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_summary import \
    FabricSummary
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_types import \
    FabricTypes
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.query import \
    FabricQuery
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.replaced import \
    FabricReplacedBulk
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.template_get import \
    TemplateGet
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.update import \
    FabricUpdateBulk
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.verify_playbook_params import \
    VerifyPlaybookParams


def json_pretty(msg):
    """
    Return a pretty-printed JSON string for logging messages
    """
    return json.dumps(msg, indent=4, sort_keys=True)


class Common(FabricCommon):
    """
    Common methods, properties, and resources for all states.
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        super().__init__(params)
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.results = Results()
        self.results.state = self.state
        self.results.check_mode = self.check_mode

        msg = "ENTERED Common(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.endpoints = ApiEndpoints()

        self._implemented_states = set()

        self._verify_playbook_params = VerifyPlaybookParams()

        # populated in self.validate_input()
        self.payloads = {}

        self.config = params.get("config")
        if not isinstance(self.config, list):
            msg = "expected list type for self.config. "
            msg += f"got {type(self.config).__name__}"
            raise ValueError(msg)

        self.validated = []
        self.have = {}
        self.want = []
        self.query = []

        self._build_properties()

    def _build_properties(self):
        self._properties["ansible_module"] = None

    def get_have(self):
        """
        Caller: main()

        Build self.have, which is a dict containing the current controller
        fabrics and their details.

        Have is a dict, keyed on fabric_name, where each element is a dict
        with the following structure:

        {
            "fabric_name": "fabric_name",
            "fabric_config": {
                "fabricName": "fabric_name",
                "fabricType": "VXLAN EVPN",
                etc...
            }
        }
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self.have = FabricDetailsByName(self.params)
        self.have.rest_send = RestSend(self.ansible_module)
        self.have.refresh()

    def get_want(self) -> None:
        """
        Caller: main()

        1. Validate the playbook configs
        2. Update self.want with the playbook configs
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        merged_configs = []
        for config in self.config:
            try:
                self._verify_payload(config)
            except ValueError as error:
                self.ansible_module.fail_json(f"{error}", **self.results.failed_result)
            merged_configs.append(copy.deepcopy(config))

        self.want = []
        for config in merged_configs:
            self.want.append(copy.deepcopy(config))

    @property
    def ansible_module(self):
        """
        getter: return an instance of AnsibleModule
        setter: set an instance of AnsibleModule
        """
        return self._properties["ansible_module"]

    @ansible_module.setter
    def ansible_module(self, value):
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        if not isinstance(value, AnsibleModule):
            msg = f"{self.class_name}.{method_name}: "
            msg += "expected AnsibleModule instance. "
            msg += f"got {type(value).__name__}."
            raise ValueError(msg)
        self._properties["ansible_module"] = value


class Deleted(Common):
    """
    Handle deleted state
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        super().__init__(params)
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.fabric_delete = FabricDelete(self.params)

        msg = "ENTERED Deleted(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self._implemented_states.add("deleted")

    def commit(self) -> None:
        """
        delete the fabrics in self.want that exist on the controller
        """
        self.get_want()
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        msg = f"{self.class_name}.{method_name}: "
        msg += "entered"
        self.log.debug(msg)

        self.rest_send = RestSend(self.ansible_module)

        self.fabric_details = FabricDetailsByName(self.params)
        self.fabric_details.rest_send = self.rest_send

        self.fabric_summary = FabricSummary(self.params)
        self.fabric_summary.rest_send = self.rest_send

        self.fabric_delete.rest_send = self.rest_send
        self.fabric_delete.fabric_details = self.fabric_details
        self.fabric_delete.fabric_summary = self.fabric_summary
        self.fabric_delete.results = self.results

        fabric_names_to_delete = []
        for want in self.want:
            fabric_names_to_delete.append(want["FABRIC_NAME"])

        try:
            self.fabric_delete.fabric_names = fabric_names_to_delete
        except ValueError as error:
            self.ansible_module.fail_json(
                f"{error}", **self.fabric_delete.results.failed_result
            )

        try:
            self.fabric_delete.commit()
        except ValueError as error:
            self.ansible_module.fail_json(
                f"{error}", **self.fabric_delete.results.failed_result
            )


class Merged(Common):
    """
    Handle merged state
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        super().__init__(params)
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.fabric_details = FabricDetailsByName(self.params)
        self.fabric_summary = FabricSummary(self.params)
        self.fabric_create = FabricCreateBulk(self.params)
        self.fabric_types = FabricTypes()
        self.fabric_update = FabricUpdateBulk(self.params)
        self.template = TemplateGet()

        msg = f"ENTERED Merged.{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.need_create = []
        self.need_update = []

        self._implemented_states.add("merged")

    def get_need(self):
        """
        Caller: commit()

        Build self.need for merged state
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self.payloads = {}
        for want in self.want:

            fabric_name = want.get("FABRIC_NAME", None)
            fabric_type = want.get("FABRIC_TYPE", None)

            try:
                self._verify_playbook_params.config_playbook = want
            except TypeError as error:
                self.ansible_module.fail_json(f"{error}", **self.results.failed_result)

            try:
                self.fabric_types.fabric_type = fabric_type
            except ValueError as error:
                self.ansible_module.fail_json(f"{error}", **self.results.failed_result)

            try:
                template_name = self.fabric_types.template_name
            except ValueError as error:
                self.ansible_module.fail_json(f"{error}", **self.results.failed_result)

            self.template.rest_send = self.rest_send
            self.template.template_name = template_name

            try:
                self.template.refresh()
            except ValueError as error:
                self.ansible_module.fail_json(f"{error}", **self.results.failed_result)
            except ControllerResponseError as error:
                msg = f"{self.class_name}.{method_name}: "
                msg += "Controller returned error when attempting to retrieve "
                msg += f"template: {template_name}. "
                msg += f"Error detail: {error}"
                self.ansible_module.fail_json(f"{msg}", **self.results.failed_result)

            try:
                self._verify_playbook_params.template = self.template.template
            except TypeError as error:
                self.ansible_module.fail_json(f"{error}", **self.results.failed_result)

            # Append to need_create if the fabric does not exist.
            # Otherwise, append to need_update.
            if fabric_name not in self.have.all_data:
                try:
                    self._verify_playbook_params.config_controller = None
                except TypeError as error:
                    self.ansible_module.fail_json(
                        f"{error}", **self.results.failed_result
                    )

                try:
                    self._verify_playbook_params.commit()
                except ValueError as error:
                    self.ansible_module.fail_json(
                        f"{error}", **self.results.failed_result
                    )

                self.need_create.append(want)

            else:

                nv_pairs = self.have.all_data[fabric_name]["nvPairs"]
                try:
                    self._verify_playbook_params.config_controller = nv_pairs
                except TypeError as error:
                    self.ansible_module.fail_json(
                        f"{error}", **self.results.failed_result
                    )
                try:
                    self._verify_playbook_params.commit()
                except (ValueError, KeyError) as error:
                    self.ansible_module.fail_json(
                        f"{error}", **self.results.failed_result
                    )

                self.need_update.append(want)

    def commit(self):
        """
        Commit the merged state request
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        msg = f"{self.class_name}.{method_name}: entered"
        self.log.debug(msg)

        self.rest_send = RestSend(self.ansible_module)
        self.fabric_details.rest_send = self.rest_send
        self.fabric_summary.rest_send = self.rest_send

        self.get_want()
        self.get_have()
        self.get_need()
        self.send_need_create()
        self.send_need_update()

    def send_need_create(self) -> None:
        """
        Caller: commit()

        Build and send the payload to create fabrics specified in the playbook.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        msg = f"{self.class_name}.{method_name}: entered. "
        msg += f"self.need_create: {json_pretty(self.need_create)}"
        self.log.debug(msg)

        if len(self.need_create) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "No fabrics to create."
            self.log.debug(msg)
            return

        self.fabric_create.fabric_details = self.fabric_details
        self.fabric_create.rest_send = self.rest_send
        self.fabric_create.results = self.results

        try:
            self.fabric_create.payloads = self.need_create
        except ValueError as error:
            self.ansible_module.fail_json(
                f"{error}", **self.fabric_create.results.failed_result
            )

        try:
            self.fabric_create.commit()
        except ValueError as error:
            self.ansible_module.fail_json(
                f"{error}", **self.fabric_create.results.failed_result
            )

    def send_need_update(self) -> None:
        """
        Caller: commit()

        Build and send the payload to create fabrics specified in the playbook.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        msg = f"{self.class_name}.{method_name}: entered. "
        msg += "self.need_update: "
        msg += f"{json_pretty(self.need_update)}"
        self.log.debug(msg)

        if len(self.need_update) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "No fabrics to update for merged state."
            self.log.debug(msg)
            return

        self.fabric_update.fabric_details = self.fabric_details
        self.fabric_update.fabric_summary = self.fabric_summary
        self.fabric_update.rest_send = RestSend(self.ansible_module)
        self.fabric_update.results = self.results

        try:
            self.fabric_update.payloads = self.need_update
        except ValueError as error:
            self.ansible_module.fail_json(
                f"{error}", **self.fabric_update.results.failed_result
            )

        try:
            self.fabric_update.commit()
        except ValueError as error:
            self.ansible_module.fail_json(
                f"{error}", **self.fabric_update.results.failed_result
            )


class Query(Common):
    """
    Handle query state
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        super().__init__(ansible_module)
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED Query(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self._implemented_states.add("query")

    def commit(self) -> None:
        """
        1.  query the fabrics in self.want that exist on the controller
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.fabric_details = FabricDetailsByName(self.params)
        self.fabric_details.rest_send = RestSend(self.ansible_module)

        self.get_want()

        fabric_query = FabricQuery(self.params)
        fabric_query.fabric_details = self.fabric_details

        fabric_query.results = self.results
        fabric_names_to_query = []
        for want in self.want:
            fabric_names_to_query.append(want["FABRIC_NAME"])
        try:
            fabric_query.fabric_names = copy.copy(fabric_names_to_query)
        except ValueError as error:
            self.ansible_module.fail_json(
                f"{error}", **fabric_query.results.failed_result
            )

        try:
            fabric_query.commit()
        except ValueError as error:
            self.ansible_module.fail_json(
                f"{error}", **fabric_query.results.failed_result
            )


class Replaced(Common):
    """
    Handle replaced state
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        super().__init__(params)
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.fabric_details = FabricDetailsByName(self.params)
        self.fabric_replaced = FabricReplacedBulk(self.params)
        self.fabric_summary = FabricSummary(self.params)
        self.fabric_types = FabricTypes()
        self.template = TemplateGet()

        msg = f"ENTERED Replaced.{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.need_replaced = []

        self._implemented_states.add("replaced")

    def get_need(self):
        """
        Caller: commit()

        Build self.need for replaced state
        """
        self.payloads = {}
        for want in self.want:
            # Skip fabrics that do not exist on the controller
            if want["FABRIC_NAME"] not in self.have.all_data:
                continue
            self.need_replaced.append(want)

    def commit(self):
        """
        Commit the replaced state request
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        msg = f"{self.class_name}.{method_name}: entered"
        self.log.debug(msg)

        self.rest_send = RestSend(self.ansible_module)
        self.fabric_details.rest_send = self.rest_send
        self.fabric_summary.rest_send = self.rest_send

        self.get_want()
        self.get_have()
        self.get_need()
        self.send_need_replaced()

    def send_need_replaced(self) -> None:
        """
        Caller: commit()

        Build and send the payload to modify fabrics specified in the
        playbook per replaced state handling.

        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        msg = f"{self.class_name}.{method_name}: entered. "
        msg += "self.need_replaced: "
        msg += f"{json_pretty(self.need_replaced)}"
        self.log.debug(msg)

        if len(self.need_replaced) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "No fabrics to update for replaced state."
            self.log.debug(msg)
            return

        self.fabric_replaced.fabric_details = self.fabric_details
        self.fabric_replaced.fabric_summary = self.fabric_summary
        self.fabric_replaced.rest_send = RestSend(self.ansible_module)
        self.fabric_replaced.results = self.results

        try:
            self.fabric_replaced.payloads = self.need_replaced
        except ValueError as error:
            self.ansible_module.fail_json(
                f"{error}", **self.fabric_replaced.results.failed_result
            )

        try:
            self.fabric_replaced.commit()
        except ValueError as error:
            self.ansible_module.fail_json(
                f"{error}", **self.fabric_replaced.results.failed_result
            )


def main():
    """main entry point for module execution"""

    argument_spec = {}
    argument_spec["config"] = {"required": False, "type": "list", "elements": "dict"}
    argument_spec["state"] = {
        "default": "merged",
        "choices": ["deleted", "merged", "query", "replaced"],
    }

    ansible_module = AnsibleModule(
        argument_spec=argument_spec, supports_check_mode=True
    )

    # Create the base/parent logger for the dcnm collection.
    # To enable logging, set enable_logging to True.
    # log.config can be either a dictionary, or a path to a JSON file
    # Both dictionary and JSON file formats must be conformant with
    # logging.config.dictConfig and must not log to the console.
    # For an example configuration, see:
    # $ANSIBLE_COLLECTIONS_PATH/cisco/dcnm/plugins/module_utils/common/logging_config.json
    enable_logging = False
    log = Log(ansible_module)
    if enable_logging is True:
        collection_path = (
            "/Users/arobel/repos/collections/ansible_collections/cisco/dcnm"
        )
        config_file = (
            f"{collection_path}/plugins/module_utils/common/logging_config.json"
        )
        log.config = config_file
    log.commit()

    ansible_module.params["check_mode"] = ansible_module.check_mode
    if ansible_module.params["state"] == "merged":
        task = Merged(ansible_module.params)
        task.ansible_module = ansible_module
        task.commit()
    elif ansible_module.params["state"] == "deleted":
        task = Deleted(ansible_module.params)
        task.ansible_module = ansible_module
        task.commit()
    elif ansible_module.params["state"] == "query":
        task = Query(ansible_module.params)
        task.ansible_module = ansible_module
        task.commit()
    elif ansible_module.params["state"] == "replaced":
        task = Replaced(ansible_module.params)
        task.ansible_module = ansible_module
        task.commit()
    else:
        # We should never get here since the state parameter has
        # already been validated.
        msg = f"Unknown state {task.ansible_module.params['state']}"
        ansible_module.fail_json(msg)

    task.results.build_final_result()

    # Results().failed is a property that returns a set()
    # of boolean values.  pylint doesn't seem to understand this so we've
    # disabled the unsupported-membership-test warning.
    if True in task.results.failed:  # pylint: disable=unsupported-membership-test
        msg = "Module failed."
        ansible_module.fail_json(msg, **task.results.final_result)
    ansible_module.exit_json(**task.results.final_result)


if __name__ == "__main__":
    main()
