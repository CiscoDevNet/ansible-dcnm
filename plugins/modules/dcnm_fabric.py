#!/usr/bin/python
#
# Copyright (c) 2020-2024 Cisco and/or its affiliates.
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
module: dcnm_fabric
short_description: Manage creation and configuration of NDFC fabrics.
version_added: "3.5.0"
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
    skip_validation:
        default: false
        description:
        - Skip playbook parameter validation.  Useful for debugging.
        type: bool
    config:
        description:
        - A list of fabric configuration dictionaries
        type: list
        elements: dict
        suboptions:
            DEPLOY:
                default: False
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
                - IPFM
                - ISN
                - LAN_CLASSIC
                - VXLAN_EVPN
                - VXLAN_EVPN_MSD
                description:
                - The type of fabric.
                required: true
                type: str
            VXLAN_EVPN_FABRIC_PARAMETERS:
                description:
                - Data Center VXLAN EVPN fabric specific parameters.
                - Fabric for a VXLAN EVPN deployment with Nexus 9000 and 3000 switches.
                - The following parameters are specific to VXLAN EVPN fabrics.
                - The indentation of these parameters is meant only to logically group them.
                - They should be at the same YAML level as FABRIC_TYPE and FABRIC_NAME.
                suboptions:
                    AAA_REMOTE_IP_ENABLED:
                        default: false
                        description:
                        - Enable only, when IP Authorization is enabled in the AAA Server
                        required: false
                        type: bool
                    AAA_SERVER_CONF:
                        default: ''
                        description:
                        - AAA Configurations
                        required: false
                        type: str
                    ADVERTISE_PIP_BGP:
                        default: false
                        description:
                        - For Primary VTEP IP Advertisement As Next-Hop Of Prefix Routes
                        required: false
                        type: bool
                    ADVERTISE_PIP_ON_BORDER:
                        default: true
                        description:
                        - Enable advertise-pip on vPC borders and border gateways only. Applicable
                            only when vPC advertise-pip is not enabled
                        required: false
                        type: bool
                    ANYCAST_BGW_ADVERTISE_PIP:
                        default: false
                        description:
                        - To advertise Anycast Border Gateway PIP as VTEP. Effective on MSD
                            fabric Recalculate Config
                        required: false
                        type: bool
                    ANYCAST_GW_MAC:
                        default: 2020.0000.00aa
                        description:
                        - Shared MAC address for all leafs (xxxx.xxxx.xxxx)
                        required: false
                        type: str
                    ANYCAST_LB_ID:
                        default: 10
                        description:
                        - 'Used for vPC Peering in VXLANv6 Fabrics '
                        required: false
                        type: int
                    ANYCAST_RP_IP_RANGE:
                        default: 10.254.254.0/24
                        description:
                        - Anycast or Phantom RP IP Address Range
                        required: false
                        type: str
                    AUTO_SYMMETRIC_DEFAULT_VRF:
                        default: false
                        description:
                        - Whether to auto generate Default VRF interface and BGP peering configuration
                            on managed neighbor devices. If set, auto created VRF Lite IFC
                            links will have Auto Deploy Default VRF for Peer enabled.
                        required: false
                        type: bool
                    AUTO_SYMMETRIC_VRF_LITE:
                        default: false
                        description:
                        - Whether to auto generate VRF LITE sub-interface and BGP peering
                            configuration on managed neighbor devices. If set, auto created
                            VRF Lite IFC links will have Auto Deploy for Peer enabled.
                        required: false
                        type: bool
                    AUTO_UNIQUE_VRF_LITE_IP_PREFIX:
                        default: false
                        description:
                        - When enabled, IP prefix allocated to the VRF LITE IFC is not reused
                            on VRF extension over VRF LITE IFC. Instead, unique IP Subnet
                            is allocated for each VRF extension over VRF LITE IFC.
                        required: false
                        type: bool
                    AUTO_VRFLITE_IFC_DEFAULT_VRF:
                        default: false
                        description:
                        - Whether to auto generate Default VRF interface and BGP peering configuration
                            on VRF LITE IFC auto deployment. If set, auto created VRF Lite
                            IFC links will have Auto Deploy Default VRF enabled.
                        required: false
                        type: bool
                    BANNER:
                        default: ''
                        description:
                        - Message of the Day (motd) banner. Delimiter char (very first char
                            is delimiter char) followed by message ending with delimiter
                        required: false
                        type: str
                    BFD_AUTH_ENABLE:
                        default: false
                        description:
                        - Valid for P2P Interfaces only
                        required: false
                        type: bool
                    BFD_AUTH_KEY:
                        default: ''
                        description:
                        - Encrypted SHA1 secret value
                        required: false
                        type: str
                    BFD_AUTH_KEY_ID:
                        default: 100
                        description:
                        - No description available
                        required: false
                        type: int
                    BFD_ENABLE:
                        default: false
                        description:
                        - Valid for IPv4 Underlay only
                        required: false
                        type: bool
                    BFD_IBGP_ENABLE:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    BFD_ISIS_ENABLE:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    BFD_OSPF_ENABLE:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    BFD_PIM_ENABLE:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    BGP_AS:
                        default: ''
                        description:
                        - 1-4294967295 | 1-65535.0-65535 It is a good practice to have a unique
                            ASN for each Fabric.
                        required: false
                        type: str
                    BGP_AUTH_ENABLE:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    BGP_AUTH_KEY:
                        default: ''
                        description:
                        - Encrypted BGP Authentication Key based on type
                        required: false
                        type: str
                    BGP_AUTH_KEY_TYPE:
                        choices:
                        - 3
                        - 7
                        default: 3
                        description:
                        - 'BGP Key Encryption Type: 3 - 3DES, 7 - Cisco'
                        required: false
                        type: int
                    BGP_LB_ID:
                        default: 0
                        description:
                        - No description available
                        required: false
                        type: int
                    BOOTSTRAP_CONF:
                        default: ''
                        description:
                        - Additional CLIs required during device bootup/login e.g. AAA/Radius
                        required: false
                        type: str
                    BOOTSTRAP_ENABLE:
                        default: false
                        description:
                        - Automatic IP Assignment For POAP
                        required: false
                        type: bool
                    BOOTSTRAP_MULTISUBNET:
                        default: '#Scope_Start_IP, Scope_End_IP, Scope_Default_Gateway, Scope_Subnet_Prefix'
                        description:
                        - 'lines with # prefix are ignored here'
                        required: false
                        type: str
                    BROWNFIELD_NETWORK_NAME_FORMAT:
                        default: Auto_Net_VNI$$VNI$$_VLAN$$VLAN_ID$$
                        description:
                        - Generated network name should be &lt; 64 characters
                        required: false
                        type: str
                    BROWNFIELD_SKIP_OVERLAY_NETWORK_ATTACHMENTS:
                        default: false
                        description:
                        - Enable to skip overlay network interface attachments for Brownfield
                            and Host Port Resync cases
                        required: false
                        type: bool
                    CDP_ENABLE:
                        default: false
                        description:
                        - Enable CDP on management interface
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
                        - Fabric Wide CoPP Policy. Customized CoPP policy should be provided
                            when manual is selected
                        required: false
                        type: str
                    DCI_SUBNET_RANGE:
                        default: 10.33.0.0/16
                        description:
                        - Address range to assign P2P Interfabric Connections
                        required: false
                        type: str
                    DCI_SUBNET_TARGET_MASK:
                        default: 30
                        description:
                        - No description available
                        required: false
                        type: int
                    DEFAULT_QUEUING_POLICY_CLOUDSCALE:
                        choices:
                        - queuing_policy_default_4q_cloudscale
                        - queuing_policy_default_8q_cloudscale
                        default: queuing_policy_default_8q_cloudscale
                        description:
                        - Queuing Policy for all 92xx, -EX, -FX, -FX2, -FX3, -GX series switches
                            in the fabric
                        required: false
                        type: str
                    DEFAULT_QUEUING_POLICY_OTHER:
                        choices:
                        - queuing_policy_default_other
                        default: queuing_policy_default_other
                        description:
                        - Queuing Policy for all other switches in the fabric
                        required: false
                        type: str
                    DEFAULT_QUEUING_POLICY_R_SERIES:
                        choices:
                        - queuing_policy_default_r_series
                        default: queuing_policy_default_r_series
                        description:
                        - Queuing Policy for all R-Series switches in the fabric
                        required: false
                        type: str
                    DEFAULT_VRF_REDIS_BGP_RMAP:
                        default: extcon-rmap-filter
                        description:
                        - Route Map used to redistribute BGP routes to IGP in default vrf
                            in auto created VRF Lite IFC links
                        required: false
                        type: str
                    DHCP_ENABLE:
                        default: false
                        description:
                        - Automatic IP Assignment For POAP From Local DHCP Server
                        required: false
                        type: bool
                    DHCP_END:
                        default: ''
                        description:
                        - End Address For Switch POAP
                        required: false
                        type: str
                    DHCP_IPV6_ENABLE:
                        choices:
                        - DHCPv4
                        - DHCPv6
                        default: DHCPv4
                        description:
                        - No description available
                        required: false
                        type: str
                    DHCP_START:
                        default: ''
                        description:
                        - Start Address For Switch POAP
                        required: false
                        type: str
                    DNS_SERVER_IP_LIST:
                        default: ''
                        description:
                        - Comma separated list of IP Addresses(v4/v6)
                        required: false
                        type: str
                    DNS_SERVER_VRF:
                        default: ''
                        description:
                        - One VRF for all DNS servers or a comma separated list of VRFs, one
                            per DNS server
                        required: false
                        type: str
                    ENABLE_AAA:
                        default: false
                        description:
                        - Include AAA configs from Manageability tab during device bootup
                        required: false
                        type: bool
                    ENABLE_DEFAULT_QUEUING_POLICY:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    ENABLE_FABRIC_VPC_DOMAIN_ID:
                        default: false
                        description:
                        - (Not Recommended)
                        required: false
                        type: bool
                    ENABLE_MACSEC:
                        default: false
                        description:
                        - Enable MACsec in the fabric
                        required: false
                        type: bool
                    ENABLE_NETFLOW:
                        default: false
                        description:
                        - Enable Netflow on VTEPs
                        required: false
                        type: bool
                    ENABLE_NGOAM:
                        default: true
                        description:
                        - Enable the Next Generation (NG) OAM feature for all switches in
                            the fabric to aid in trouble-shooting VXLAN EVPN fabrics
                        required: false
                        type: bool
                    ENABLE_NXAPI:
                        default: true
                        description:
                        - Enable HTTPS NX-API
                        required: false
                        type: bool
                    ENABLE_NXAPI_HTTP:
                        default: true
                        description:
                        - No description available
                        required: false
                        type: bool
                    ENABLE_PBR:
                        default: false
                        description:
                        - When ESR option is ePBR, enable ePBR will enable pbr, sla sender
                            and epbr features on the switch
                        required: false
                        type: bool
                    ENABLE_PVLAN:
                        default: false
                        description:
                        - Enable PVLAN on switches except spines and super spines
                        required: false
                        type: bool
                    ENABLE_TENANT_DHCP:
                        default: true
                        description:
                        - No description available
                        required: false
                        type: bool
                    ENABLE_TRM:
                        default: false
                        description:
                        - For Overlay Multicast Support In VXLAN Fabrics
                        required: false
                        type: bool
                    ENABLE_VPC_PEER_LINK_NATIVE_VLAN:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    ESR_OPTION:
                        default: PBR
                        description:
                        - Policy-Based Routing (PBR) or Enhanced PBR (ePBR)
                        required: false
                        type: str
                    EXTRA_CONF_INTRA_LINKS:
                        default: ''
                        description:
                        - Additional CLIs For All Intra-Fabric Links
                        required: false
                        type: str
                    EXTRA_CONF_LEAF:
                        default: ''
                        description:
                        - Additional CLIs For All Leafs As Captured From Show Running Configuration
                        required: false
                        type: str
                    EXTRA_CONF_SPINE:
                        default: ''
                        description:
                        - Additional CLIs For All Spines As Captured From Show Running Configuration
                        required: false
                        type: str
                    EXTRA_CONF_TOR:
                        default: ''
                        description:
                        - Additional CLIs For All ToRs As Captured From Show Running Configuration
                        required: false
                        type: str
                    FABRIC_INTERFACE_TYPE:
                        choices:
                        - p2p
                        - unnumbered
                        default: p2p
                        description:
                        - Numbered(Point-to-Point) or Unnumbered
                        required: false
                        type: str
                    FABRIC_MTU:
                        default: 9216
                        description:
                        - . Must be an even number
                        required: false
                        type: int
                    FABRIC_NAME:
                        default: ''
                        description:
                        - Please provide the fabric name to create it (Max Size 32)
                        required: false
                        type: str
                    FABRIC_VPC_DOMAIN_ID:
                        default: 1
                        description:
                        - vPC Domain Id to be used on all vPC pairs
                        required: false
                        type: int
                    FABRIC_VPC_QOS:
                        default: false
                        description:
                        - Qos on spines for guaranteed delivery of vPC Fabric Peering communication
                        required: false
                        type: bool
                    FABRIC_VPC_QOS_POLICY_NAME:
                        default: spine_qos_for_fabric_vpc_peering
                        description:
                        - Qos Policy name should be same on all spines
                        required: false
                        type: str
                    FEATURE_PTP:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    GRFIELD_DEBUG_FLAG:
                        choices:
                        - Enable
                        - Disable
                        default: Disable
                        description:
                        - Enable to clean switch configuration without reload when PreserveConfig=no
                        required: false
                        type: str
                    HD_TIME:
                        default: 180
                        description:
                        - NVE Source Inteface HoldDown Time  in seconds
                        required: false
                        type: int
                    HOST_INTF_ADMIN_STATE:
                        default: true
                        description:
                        - No description available
                        required: false
                        type: bool
                    IBGP_PEER_TEMPLATE:
                        default: ''
                        description:
                        - Speficies the iBGP Peer-Template config used for RR and spines with
                            border role.
                        required: false
                        type: str
                    IBGP_PEER_TEMPLATE_LEAF:
                        default: ''
                        description:
                        - Specifies the config used for leaf, border or border gateway. If
                            this field is empty, the peer template defined in iBGP Peer-Template
                            Config is used on all BGP enabled devices (RRs,leafs, border or
                            border gateway roles.
                        required: false
                        type: str
                    INBAND_DHCP_SERVERS:
                        default: ''
                        description:
                        - Comma separated list of IPv4 Addresses (Max 3)
                        required: false
                        type: str
                    INBAND_MGMT:
                        default: false
                        description:
                        - Manage switches with only Inband connectivity
                        required: false
                        type: bool
                    ISIS_AUTH_ENABLE:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    ISIS_AUTH_KEY:
                        default: ''
                        description:
                        - Cisco Type 7 Encrypted
                        required: false
                        type: str
                    ISIS_AUTH_KEYCHAIN_KEY_ID:
                        default: 127
                        description:
                        - No description available
                        required: false
                        type: int
                    ISIS_AUTH_KEYCHAIN_NAME:
                        default: ''
                        description:
                        - No description available
                        required: false
                        type: str
                    ISIS_LEVEL:
                        choices:
                        - level-1
                        - level-2
                        default: level-2
                        description:
                        - 'Supported IS types: level-1, level-2'
                        required: false
                        type: str
                    ISIS_OVERLOAD_ELAPSE_TIME:
                        default: 60
                        description:
                        - Clear the overload bit after an elapsed time in seconds
                        required: false
                        type: int
                    ISIS_OVERLOAD_ENABLE:
                        default: true
                        description:
                        - When enabled, set the overload bit for an elapsed time after a reload
                        required: false
                        type: bool
                    ISIS_P2P_ENABLE:
                        default: true
                        description:
                        - This will enable network point-to-point on fabric interfaces which
                            are numbered
                        required: false
                        type: bool
                    L2_HOST_INTF_MTU:
                        default: 9216
                        description:
                        - . Must be an even number
                        required: false
                        type: int
                    L2_SEGMENT_ID_RANGE:
                        default: 30000-49000
                        description:
                        - 'Overlay Network Identifier Range '
                        required: false
                        type: str
                    L3VNI_MCAST_GROUP:
                        default: 239.1.1.0
                        description:
                        - Default Underlay Multicast group IP assigned for every overlay VRF.
                        required: false
                        type: str
                    L3_PARTITION_ID_RANGE:
                        default: 50000-59000
                        description:
                        - 'Overlay VRF Identifier Range '
                        required: false
                        type: str
                    LINK_STATE_ROUTING:
                        choices:
                        - ospf
                        - is-is
                        default: ospf
                        description:
                        - Used for Spine-Leaf Connectivity
                        required: false
                        type: str
                    LINK_STATE_ROUTING_TAG:
                        default: UNDERLAY
                        description:
                        - Underlay Routing Process Tag
                        required: false
                        type: str
                    LOOPBACK0_IPV6_RANGE:
                        default: fd00::a02:0/119
                        description:
                        - Typically Loopback0 IPv6 Address Range
                        required: false
                        type: str
                    LOOPBACK0_IP_RANGE:
                        default: 10.2.0.0/22
                        description:
                        - Typically Loopback0 IP Address Range
                        required: false
                        type: str
                    LOOPBACK1_IPV6_RANGE:
                        default: fd00::a03:0/118
                        description:
                        - Typically Loopback1 and Anycast Loopback IPv6 Address Range
                        required: false
                        type: str
                    LOOPBACK1_IP_RANGE:
                        default: 10.3.0.0/22
                        description:
                        - Typically Loopback1 IP Address Range
                        required: false
                        type: str
                    MACSEC_ALGORITHM:
                        default: AES_128_CMAC
                        description:
                        - AES_128_CMAC or AES_256_CMAC
                        required: false
                        type: str
                    MACSEC_CIPHER_SUITE:
                        default: GCM-AES-XPN-256
                        description:
                        - Configure Cipher Suite
                        required: false
                        type: str
                    MACSEC_FALLBACK_ALGORITHM:
                        default: AES_128_CMAC
                        description:
                        - AES_128_CMAC or AES_256_CMAC
                        required: false
                        type: str
                    MACSEC_FALLBACK_KEY_STRING:
                        default: ''
                        description:
                        - Cisco Type 7 Encrypted Octet String
                        required: false
                        type: str
                    MACSEC_KEY_STRING:
                        default: ''
                        description:
                        - Cisco Type 7 Encrypted Octet String
                        required: false
                        type: str
                    MACSEC_REPORT_TIMER:
                        default: 5
                        description:
                        - MACsec Operational Status periodic report timer in minutes
                        required: false
                        type: int
                    MGMT_GW:
                        default: ''
                        description:
                        - Default Gateway For Management VRF On The Switch
                        required: false
                        type: str
                    MGMT_PREFIX:
                        default: 24
                        description:
                        - No description available
                        required: false
                        type: int
                    MGMT_V6PREFIX:
                        default: 64
                        description:
                        - No description available
                        required: false
                        type: int
                    MPLS_HANDOFF:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    MPLS_LB_ID:
                        default: 101
                        description:
                        - 'Used for VXLAN to MPLS SR/LDP Handoff '
                        required: false
                        type: int
                    MPLS_LOOPBACK_IP_RANGE:
                        default: 10.101.0.0/25
                        description:
                        - Used for VXLAN to MPLS SR/LDP Handoff
                        required: false
                        type: str
                    MST_INSTANCE_RANGE:
                        default: "0"
                        description:
                        - 'MST instance range, Example: 0-3,5,7-9, Default is 0'
                        required: false
                        type: str
                    MULTICAST_GROUP_SUBNET:
                        default: 239.1.1.0/25
                        description:
                        - Multicast pool prefix between 8 to 30. A multicast group IP from
                            this pool is used for BUM traffic for each overlay network.
                        required: false
                        type: str
                    NETFLOW_EXPORTER_LIST:
                        default: ''
                        description:
                        - One or Multiple Netflow Exporters
                        required: false
                        type: list
                        elements: str
                    NETFLOW_MONITOR_LIST:
                        default: ''
                        description:
                        - One or Multiple Netflow Monitors
                        required: false
                        type: list
                        elements: str
                    NETFLOW_RECORD_LIST:
                        default: ''
                        description:
                        - One or Multiple Netflow Records
                        required: false
                        type: list
                        elements: str
                    NETWORK_VLAN_RANGE:
                        default: 2300-2999
                        description:
                        - 'Per Switch Overlay Network VLAN Range '
                        required: false
                        type: str
                    NTP_SERVER_IP_LIST:
                        default: ''
                        description:
                        - Comma separated list of IP Addresses(v4/v6)
                        required: false
                        type: str
                    NTP_SERVER_VRF:
                        default: ''
                        description:
                        - One VRF for all NTP servers or a comma separated list of VRFs, one
                            per NTP server
                        required: false
                        type: str
                    NVE_LB_ID:
                        default: 1
                        description:
                        - No description available
                        required: false
                        type: int
                    NXAPI_HTTPS_PORT:
                        default: 443
                        description:
                        - No description available
                        required: false
                        type: int
                    NXAPI_HTTP_PORT:
                        default: 80
                        description:
                        - No description available
                        required: false
                        type: int
                    OBJECT_TRACKING_NUMBER_RANGE:
                        default: 100-299
                        description:
                        - 'Per switch tracked object ID Range '
                        required: false
                        type: str
                    OSPF_AREA_ID:
                        default: 0.0.0.0
                        description:
                        - OSPF Area Id in IP address format
                        required: false
                        type: str
                    OSPF_AUTH_ENABLE:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    OSPF_AUTH_KEY:
                        default: ''
                        description:
                        - 3DES Encrypted
                        required: false
                        type: str
                    OSPF_AUTH_KEY_ID:
                        default: 127
                        description:
                        - No description available
                        required: false
                        type: int
                    OVERLAY_MODE:
                        default: cli
                        description:
                        - VRF/Network configuration using config-profile or CLI
                        required: false
                        type: str
                    PER_VRF_LOOPBACK_AUTO_PROVISION:
                        default: false
                        description:
                        - Auto provision a loopback on a VTEP on VRF attachment
                        required: false
                        type: bool
                    PER_VRF_LOOPBACK_IP_RANGE:
                        default: 10.5.0.0/22
                        description:
                        - Prefix pool to assign IP addresses to loopbacks on VTEPs on a per
                            VRF basis
                        required: false
                        type: str
                    PHANTOM_RP_LB_ID1:
                        default: 2
                        description:
                        - 'Used for Bidir-PIM Phantom RP '
                        required: false
                        type: int
                    PHANTOM_RP_LB_ID2:
                        default: 3
                        description:
                        - 'Used for Fallback Bidir-PIM Phantom RP '
                        required: false
                        type: int
                    PHANTOM_RP_LB_ID3:
                        default: 4
                        description:
                        - 'Used for second Fallback Bidir-PIM Phantom RP '
                        required: false
                        type: int
                    PHANTOM_RP_LB_ID4:
                        default: 5
                        description:
                        - 'Used for third Fallback Bidir-PIM Phantom RP '
                        required: false
                        type: int
                    PIM_HELLO_AUTH_ENABLE:
                        default: false
                        description:
                        - Valid for IPv4 Underlay only
                        required: false
                        type: bool
                    PIM_HELLO_AUTH_KEY:
                        default: ''
                        description:
                        - 3DES Encrypted
                        required: false
                        type: str
                    PM_ENABLE:
                        default: false
                        description:
                        - No description available
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
                        required: false
                        type: str
                    PTP_DOMAIN_ID:
                        default: 0
                        description:
                        - 'Multiple Independent PTP Clocking Subdomains on a Single Network '
                        required: false
                        type: int
                    PTP_LB_ID:
                        default: 0
                        description:
                        - No description available
                        required: false
                        type: int
                    REPLICATION_MODE:
                        choices:
                        - Multicast
                        - Ingress
                        default: Multicast
                        description:
                        - Replication Mode for BUM Traffic
                        required: false
                        type: str
                    ROUTER_ID_RANGE:
                        default: 10.2.0.0/23
                        description:
                        - No description available
                        required: false
                        type: str
                    ROUTE_MAP_SEQUENCE_NUMBER_RANGE:
                        default: 1-65534
                        description:
                        - No description available
                        required: false
                        type: str
                    RP_COUNT:
                        choices:
                        - 2
                        - 4
                        default: 2
                        description:
                        - Number of spines acting as Rendezvous-Point (RP)
                        required: false
                        type: int
                    RP_LB_ID:
                        default: 254
                        description:
                        - No description available
                        required: false
                        type: int
                    RP_MODE:
                        choices:
                        - asm
                        - bidir
                        default: asm
                        description:
                        - Multicast RP Mode
                        required: false
                        type: str
                    RR_COUNT:
                        choices:
                        - 2
                        - 4
                        default: 2
                        description:
                        - Number of spines acting as Route-Reflectors
                        required: false
                        type: int
                    SEED_SWITCH_CORE_INTERFACES:
                        default: ''
                        description:
                        - Core-facing Interface list on Seed Switch (e.g. e1/1-30,e1/32)
                        required: false
                        type: str
                    SERVICE_NETWORK_VLAN_RANGE:
                        default: 3000-3199
                        description:
                        - 'Per Switch Overlay Service Network VLAN Range '
                        required: false
                        type: str
                    SITE_ID:
                        default: ''
                        description:
                        - For EVPN Multi-Site Support . Defaults to Fabric ASN
                        required: false
                        type: str
                    SLA_ID_RANGE:
                        default: 10000-19999
                        description:
                        - 'Per switch SLA ID Range '
                        required: false
                        type: str
                    SNMP_SERVER_HOST_TRAP:
                        default: true
                        description:
                        - Configure NDFC as a receiver for SNMP traps
                        required: false
                        type: bool
                    SPINE_SWITCH_CORE_INTERFACES:
                        default: ''
                        description:
                        - Core-facing Interface list on all Spines (e.g. e1/1-30,e1/32)
                        required: false
                        type: str
                    STATIC_UNDERLAY_IP_ALLOC:
                        default: false
                        description:
                        - Checking this will disable Dynamic Underlay IP Address Allocations
                        required: false
                        type: bool
                    STP_BRIDGE_PRIORITY:
                        default: 0
                        description:
                        - Bridge priority for the spanning tree in increments of 4096
                        required: false
                        type: int
                    STP_ROOT_OPTION:
                        choices:
                        - rpvst+
                        - mst
                        - unmanaged
                        default: unmanaged
                        description:
                        - 'Which protocol to use for configuring root bridge? rpvst+: Rapid
                            Per-VLAN Spanning Tree, mst: Multiple Spanning Tree, unmanaged
                            (default): STP Root not managed by NDFC'
                        required: false
                        type: str
                    STP_VLAN_RANGE:
                        default: 1-3967
                        description:
                        - 'Vlan range, Example: 1,3-5,7,9-11, Default is 1-3967'
                        required: false
                        type: str
                    STRICT_CC_MODE:
                        default: false
                        description:
                        - Enable bi-directional compliance checks to flag additional configs
                            in the running config that are not in the intent/expected config
                        required: false
                        type: bool
                    SUBINTERFACE_RANGE:
                        default: 2-511
                        description:
                        - 'Per Border Dot1q Range For VRF Lite Connectivity '
                        required: false
                        type: str
                    SUBNET_RANGE:
                        default: 10.4.0.0/16
                        description:
                        - Address range to assign Numbered and Peer Link SVI IPs
                        required: false
                        type: str
                    SUBNET_TARGET_MASK:
                        choices:
                        - 30
                        - 31
                        default: 30
                        description:
                        - Mask for Underlay Subnet IP Range
                        required: false
                        type: int
                    SYSLOG_SERVER_IP_LIST:
                        default: ''
                        description:
                        - Comma separated list of IP Addresses(v4/v6)
                        required: false
                        type: str
                    SYSLOG_SERVER_VRF:
                        default: ''
                        description:
                        - One VRF for all Syslog servers or a comma separated list of VRFs,
                            one per Syslog server
                        required: false
                        type: str
                    SYSLOG_SEV:
                        default: ''
                        description:
                        - 'Comma separated list of Syslog severity values, one per Syslog
                            server '
                        required: false
                        type: str
                    TCAM_ALLOCATION:
                        default: true
                        description:
                        - TCAM commands are automatically generated for VxLAN and vPC Fabric
                            Peering when Enabled
                        required: false
                        type: bool
                    UNDERLAY_IS_V6:
                        default: false
                        description:
                        - If not enabled, IPv4 underlay is used
                        required: false
                        type: bool
                    UNNUM_BOOTSTRAP_LB_ID:
                        default: 253
                        description:
                        - No description available
                        required: false
                        type: int
                    UNNUM_DHCP_END:
                        default: ''
                        description:
                        - Must be a subset of IGP/BGP Loopback Prefix Pool
                        required: false
                        type: str
                    UNNUM_DHCP_START:
                        default: ''
                        description:
                        - Must be a subset of IGP/BGP Loopback Prefix Pool
                        required: false
                        type: str
                    USE_LINK_LOCAL:
                        default: true
                        description:
                        - If not enabled, Spine-Leaf interfaces will use global IPv6 addresses
                        required: false
                        type: bool
                    V6_SUBNET_RANGE:
                        default: fd00::a04:0/112
                        description:
                        - IPv6 Address range to assign Numbered and Peer Link SVI IPs
                        required: false
                        type: str
                    V6_SUBNET_TARGET_MASK:
                        choices:
                        - 126
                        - 127
                        default: 126
                        description:
                        - Mask for Underlay Subnet IPv6 Range
                        required: false
                        type: int
                    VPC_AUTO_RECOVERY_TIME:
                        default: 360
                        description:
                        - No description available
                        required: false
                        type: int
                    VPC_DELAY_RESTORE:
                        default: 150
                        description:
                        - No description available
                        required: false
                        type: int
                    VPC_DOMAIN_ID_RANGE:
                        default: 1-1000
                        description:
                        - vPC Domain id range to use for new pairings
                        required: false
                        type: str
                    VPC_ENABLE_IPv6_ND_SYNC:
                        default: true
                        description:
                        - Enable IPv6 ND synchronization between vPC peers
                        required: false
                        type: bool
                    VPC_PEER_KEEP_ALIVE_OPTION:
                        choices:
                        - loopback
                        - management
                        default: management
                        description:
                        - Use vPC Peer Keep Alive with Loopback or Management
                        required: false
                        type: str
                    VPC_PEER_LINK_PO:
                        default: 500
                        description:
                        - No description available
                        required: false
                        type: int
                    VPC_PEER_LINK_VLAN:
                        default: 3600
                        description:
                        - 'VLAN range for vPC Peer Link SVI '
                        required: false
                        type: int
                    VRF_LITE_AUTOCONFIG:
                        choices:
                        - Manual
                        - Back2Back&ToExternal
                        default: Manual
                        description:
                        - VRF Lite Inter-Fabric Connection Deployment Options. If Back2Back&ToExternal
                            is selected, VRF Lite IFCs are auto created between border devices
                            of two Easy Fabrics, and between border devices in Easy Fabric
                            and edge routers in External Fabric. The IP address is taken from
                            the VRF Lite Subnet IP Range pool.
                        required: false
                        type: str
                    VRF_VLAN_RANGE:
                        default: 2000-2299
                        description:
                        - 'Per Switch Overlay VRF VLAN Range '
                        required: false
                        type: str
                    default_network:
                        choices:
                        - Default_Network_Universal
                        - Service_Network_Universal
                        default: Default_Network_Universal
                        description:
                        - Default Overlay Network Template For Leafs
                        required: false
                        type: str
                    default_pvlan_sec_network:
                        choices:
                        - Pvlan_Secondary_Network
                        default: Pvlan_Secondary_Network
                        description:
                        - Default PVLAN Secondary Network Template
                        required: false
                        type: str
                    default_vrf:
                        choices:
                        - Default_VRF_Universal
                        default: Default_VRF_Universal
                        description:
                        - Default Overlay VRF Template For Leafs
                        required: false
                        type: str
                    enableRealTimeBackup:
                        default: ''
                        description:
                        - Backup hourly only if there is any config deployment since last
                            backup
                        required: false
                        type: bool
                    enableScheduledBackup:
                        default: ''
                        description:
                        - Backup at the specified time
                        required: false
                        type: bool
                    network_extension_template:
                        choices:
                        - Default_Network_Extension_Universal
                        default: Default_Network_Extension_Universal
                        description:
                        - Default Overlay Network Template For Borders
                        required: false
                        type: str
                    scheduledTime:
                        default: ''
                        description:
                        - Time (UTC) in 24hr format. (00:00 to 23:59)
                        required: false
                        type: str
                    vrf_extension_template:
                        choices:
                        - Default_VRF_Extension_Universal
                        default: Default_VRF_Extension_Universal
                        description:
                        - Default Overlay VRF Template For Borders
                        required: false
                        type: str
            VXLAN_EVPN_FABRIC_MSD_PARAMETERS:
                description:
                - VXLAN EVPN Multi-Site fabric specific parameters.
                - Domain that can contain multiple VXLAN EVPN Fabrics with Layer-2/Layer-3 Overlay Extensions and other Fabric Types.
                - The indentation of these parameters is meant only to logically group them.
                - They should be at the same YAML level as FABRIC_TYPE and FABRIC_NAME.
                suboptions:
                    ANYCAST_GW_MAC:
                        default: 2020.0000.00aa
                        description:
                        - Shared MAC address for all leaves
                        required: false
                        type: str
                    BGP_RP_ASN:
                        default: ''
                        description:
                        - 1-4294967295 | 1-65535.0-65535, e.g. 65000, 65001
                        required: false
                        type: str
                    BGW_ROUTING_TAG:
                        default: 54321
                        description:
                        - Routing tag associated with IP address of loopback and DCI interfaces
                        required: false
                        type: int
                    BORDER_GWY_CONNECTIONS:
                        choices:
                        - Manual
                        - Centralized_To_Route_Server
                        - Direct_To_BGWS
                        default: Manual
                        description:
                        - Manual, Auto Overlay EVPN Peering to Route Servers, Auto Overlay
                            EVPN Direct Peering to Border Gateways
                        required: false
                        type: str
                    CLOUDSEC_ALGORITHM:
                        default: AES_128_CMAC
                        description:
                        - AES_128_CMAC or AES_256_CMAC
                        required: false
                        type: str
                    CLOUDSEC_AUTOCONFIG:
                        default: false
                        description:
                        - Auto Config CloudSec on Border Gateways
                        required: false
                        type: bool
                    CLOUDSEC_ENFORCEMENT:
                        default: ''
                        description:
                        - If set to strict, data across site must be encrypted.
                        required: false
                        type: str
                    CLOUDSEC_KEY_STRING:
                        default: ''
                        description:
                        - Cisco Type 7 Encrypted Octet String
                        required: false
                        type: str
                    CLOUDSEC_REPORT_TIMER:
                        default: 5
                        description:
                        - CloudSec Operational Status periodic report timer in minutes
                        required: false
                        type: int
                    DCI_SUBNET_RANGE:
                        default: 10.10.1.0/24
                        description:
                        - Address range to assign P2P DCI Links
                        required: false
                        type: str
                    DCI_SUBNET_TARGET_MASK:
                        default: 30
                        description:
                        - 'Target Mask for Subnet Range '
                        required: false
                        type: int
                    DELAY_RESTORE:
                        default: 300
                        description:
                        - Multi-Site underlay and overlay control plane convergence time  in
                            seconds
                        required: false
                        type: int
                    ENABLE_BGP_BFD:
                        default: false
                        description:
                        - For auto-created Multi-Site Underlay IFCs
                        required: false
                        type: bool
                    ENABLE_BGP_LOG_NEIGHBOR_CHANGE:
                        default: false
                        description:
                        - For auto-created Multi-Site Underlay IFCs
                        required: false
                        type: bool
                    ENABLE_BGP_SEND_COMM:
                        default: false
                        description:
                        - For auto-created Multi-Site Underlay IFCs
                        required: false
                        type: bool
                    ENABLE_PVLAN:
                        default: false
                        description:
                        - Enable PVLAN on MSD and its child fabrics
                        required: false
                        type: bool
                    ENABLE_RS_REDIST_DIRECT:
                        default: false
                        description:
                        - For auto-created Multi-Site overlay IFCs in Route Servers. Applicable
                            only when Multi-Site Overlay IFC Deployment Method is Centralized_To_Route_Server.
                        required: false
                        type: bool
                    FABRIC_NAME:
                        default: ''
                        description:
                        - Please provide the fabric name to create it (Max Size 64)
                        required: false
                        type: str
                    L2_SEGMENT_ID_RANGE:
                        default: 30000-49000
                        description:
                        - 'Overlay Network Identifier Range '
                        required: false
                        type: str
                    L3_PARTITION_ID_RANGE:
                        default: 50000-59000
                        description:
                        - 'Overlay VRF Identifier Range '
                        required: false
                        type: str
                    LOOPBACK100_IP_RANGE:
                        default: 10.10.0.0/24
                        description:
                        - Typically Loopback100 IP Address Range
                        required: false
                        type: str
                    MS_IFC_BGP_AUTH_KEY_TYPE:
                        choices:
                        - 3
                        - 7
                        default: 3
                        description:
                        - 'BGP Key Encryption Type: 3 - 3DES, 7 - Cisco'
                        required: false
                        type: int
                    MS_IFC_BGP_PASSWORD:
                        default: ''
                        description:
                        - Encrypted eBGP Password Hex String
                        required: false
                        type: str
                    MS_IFC_BGP_PASSWORD_ENABLE:
                        default: false
                        description:
                        - eBGP password for Multi-Site underlay/overlay IFCs
                        required: false
                        type: bool
                    MS_LOOPBACK_ID:
                        default: 100
                        description:
                        - No description available
                        required: false
                        type: int
                    MS_UNDERLAY_AUTOCONFIG:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    RP_SERVER_IP:
                        default: ''
                        description:
                        - Multi-Site Route-Server peer list (typically loopback IP address
                            on Route-Server for Multi-Site EVPN peering with BGWs), e.g. 128.89.0.1,
                            128.89.0.2
                        required: false
                        type: str
                    RS_ROUTING_TAG:
                        default: 54321
                        description:
                        - Routing tag associated with Route Server IP for redistribute direct.
                            This is the IP used in eBGP EVPN peering.
                        required: false
                        type: int
                    TOR_AUTO_DEPLOY:
                        default: false
                        description:
                        - Enables Overlay VLANs on uplink between ToRs and Leafs
                        required: false
                        type: bool
                    default_network:
                        choices:
                        - Default_Network_Universal
                        - Service_Network_Universal
                        default: Default_Network_Universal
                        description:
                        - Default Overlay Network Template For Leafs
                        required: false
                        type: str
                    default_pvlan_sec_network:
                        choices:
                        - Pvlan_Secondary_Network
                        default: Pvlan_Secondary_Network
                        description:
                        - Default PVLAN Secondary Network Template
                        required: false
                        type: str
                    default_vrf:
                        choices:
                        - Default_VRF_Universal
                        default: Default_VRF_Universal
                        description:
                        - Default Overlay VRF Template For Leafs
                        required: false
                        type: str
                    enableScheduledBackup:
                        default: ''
                        description:
                        - 'Backup at the specified time. Note: Fabric Backup/Restore functionality
                            is being deprecated for MSD fabrics. Recommendation is to use
                            NDFC Backup & Restore'
                        required: false
                        type: bool
                    network_extension_template:
                        choices:
                        - Default_Network_Extension_Universal
                        default: Default_Network_Extension_Universal
                        description:
                        - Default Overlay Network Template For Borders
                        required: false
                        type: str
                    scheduledTime:
                        default: ''
                        description:
                        - Time (UTC) in 24hr format. (00:00 to 23:59)
                        required: false
                        type: str
                    vrf_extension_template:
                        choices:
                        - Default_VRF_Extension_Universal
                        default: Default_VRF_Extension_Universal
                        description:
                        - Default Overlay VRF Template For Borders
                        required: false
                        type: str
            ISN_FABRIC_PARAMETERS:
                description:
                - ISN (Inter-site Network) fabric specific parameters.
                - Also known as Multi-Site External Network.
                - The following parameters are specific to ISN fabrics.
                - Network infrastructure attached to Border Gateways to interconnect VXLAN EVPN fabrics for Multi-Site and Multi-Cloud deployments.
                - The indentation of these parameters is meant only to logically group them.
                - They should be at the same YAML level as FABRIC_TYPE and FABRIC_NAME.
                suboptions:
                    AAA_REMOTE_IP_ENABLED:
                        default: false
                        description:
                        - Enable only, when IP Authorization is enabled in the AAA Server
                        required: false
                        type: bool
                    AAA_SERVER_CONF:
                        default: ''
                        description:
                        - AAA Configurations
                        required: false
                        type: str
                    BGP_AS:
                        default: ''
                        description:
                        - 1-4294967295 | 1-65535.0-65535 It is a good practice to have a unique
                            ASN for each Fabric.
                        required: false
                        type: str
                    BOOTSTRAP_CONF:
                        default: ''
                        description:
                        - Additional CLIs required during device bootup/login e.g. AAA/Radius
                        required: false
                        type: str
                    BOOTSTRAP_CONF_XE:
                        default: ''
                        description:
                        - Additional CLIs required during device bootup/login e.g. AAA/Radius
                        required: false
                        type: str
                    BOOTSTRAP_ENABLE:
                        default: false
                        description:
                        - Automatic IP Assignment For POAP
                        required: false
                        type: bool
                    BOOTSTRAP_MULTISUBNET:
                        default: '#Scope_Start_IP, Scope_End_IP, Scope_Default_Gateway, Scope_Subnet_Prefix'
                        description:
                        - 'lines with # prefix are ignored here'
                        required: false
                        type: str
                    CDP_ENABLE:
                        default: false
                        description:
                        - Enable CDP on management interface
                        required: false
                        type: bool
                    DHCP_ENABLE:
                        default: false
                        description:
                        - Automatic IP Assignment For POAP From Local DHCP Server
                        required: false
                        type: bool
                    DHCP_END:
                        default: ''
                        description:
                        - End Address For Switch POAP
                        required: false
                        type: str
                    DHCP_IPV6_ENABLE:
                        choices:
                        - DHCPv4
                        - DHCPv6
                        default: DHCPv4
                        description:
                        - No description available
                        required: false
                        type: str
                    DHCP_START:
                        default: ''
                        description:
                        - Start Address For Switch POAP
                        required: false
                        type: str
                    DOMAIN_NAME:
                        default: ''
                        description:
                        - Domain name for DHCP server PnP block
                        required: false
                        type: str
                    ENABLE_AAA:
                        default: false
                        description:
                        - Include AAA configs from Advanced tab during device bootup
                        required: false
                        type: bool
                    ENABLE_NETFLOW:
                        default: false
                        description:
                        - Enable Netflow on VTEPs
                        required: false
                        type: bool
                    ENABLE_NXAPI:
                        default: false
                        description:
                        - Enable HTTPS NX-API
                        required: false
                        type: bool
                    ENABLE_NXAPI_HTTP:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    ENABLE_RT_INTF_STATS:
                        default: false
                        description:
                        - Valid for NX-OS only
                        required: false
                        type: bool
                    FABRIC_FREEFORM:
                        default: ''
                        description:
                        - Additional supported CLIs for all same OS (e.g. all NxOS or IOS-XE,
                            etc) switches
                        required: false
                        type: str
                    FABRIC_NAME:
                        default: ''
                        description:
                        - Please provide the fabric name to create it (Max Size 64)
                        required: false
                        type: str
                    FEATURE_PTP:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    INBAND_ENABLE:
                        default: false
                        description:
                        - 'Enable POAP over Inband Interface (Pre-req: Inband Mgmt Knob should
                            be Enabled)'
                        required: false
                        type: bool
                    INBAND_MGMT:
                        default: false
                        description:
                        - Import switches with inband connectivity
                        required: false
                        type: bool
                    INTF_STAT_LOAD_INTERVAL:
                        default: 10
                        description:
                        - 'Time in seconds '
                        required: false
                        type: int
                    IS_READ_ONLY:
                        default: true
                        description:
                        - If enabled, fabric is only monitored. No configuration will be deployed
                        required: false
                        type: bool
                    MGMT_GW:
                        default: ''
                        description:
                        - Default Gateway For Management VRF On The Switch
                        required: false
                        type: str
                    MGMT_PREFIX:
                        default: 24
                        description:
                        - No description available
                        required: false
                        type: int
                    MGMT_V6PREFIX:
                        default: 64
                        description:
                        - No description available
                        required: false
                        type: int
                    MPLS_HANDOFF:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    MPLS_LB_ID:
                        default: 101
                        description:
                        - No description available
                        required: false
                        type: int
                    MPLS_LOOPBACK_IP_RANGE:
                        default: 10.102.0.0/25
                        description:
                        - MPLS Loopback IP Address Range
                        required: false
                        type: str
                    NETFLOW_EXPORTER_LIST:
                        default: ''
                        description:
                        - One or Multiple Netflow Exporters
                        required: false
                        type: list
                        elements: str
                    NETFLOW_MONITOR_LIST:
                        default: ''
                        description:
                        - One or Multiple Netflow Monitors
                        required: false
                        type: list
                        elements: str
                    NETFLOW_RECORD_LIST:
                        default: ''
                        description:
                        - One or Multiple Netflow Records
                        required: false
                        type: list
                        elements: str
                    NETFLOW_SAMPLER_LIST:
                        default: ''
                        description:
                        - One or multiple netflow samplers. Applicable to N7K only
                        required: false
                        type: list
                        elements: str
                    NXAPI_HTTPS_PORT:
                        default: 443
                        description:
                        - No description available
                        required: false
                        type: int
                    NXAPI_HTTP_PORT:
                        default: 80
                        description:
                        - No description available
                        required: false
                        type: int
                    PM_ENABLE:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    PNP_ENABLE:
                        default: false
                        description:
                        - Enable Plug n Play (Automatic IP Assignment) for Cat9K switches
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
                        required: false
                        type: str
                    PTP_DOMAIN_ID:
                        default: 0
                        description:
                        - 'Multiple Independent PTP Clocking Subdomains on a Single Network '
                        required: false
                        type: int
                    PTP_LB_ID:
                        default: 0
                        description:
                        - No description available
                        required: false
                        type: int
                    SNMP_SERVER_HOST_TRAP:
                        default: true
                        description:
                        - Configure NDFC as a receiver for SNMP traps
                        required: false
                        type: bool
                    SUBINTERFACE_RANGE:
                        default: 2-511
                        description:
                        - 'Per Border Dot1q Range For VRF Lite Connectivity '
                        required: false
                        type: str
                    enableRealTimeBackup:
                        default: ''
                        description:
                        - Backup hourly only if there is any config deployment since last
                            backup
                        required: false
                        type: bool
                    enableScheduledBackup:
                        default: ''
                        description:
                        - Backup at the specified time
                        required: false
                        type: bool
                    scheduledTime:
                        default: ''
                        description:
                        - Time (UTC) in 24hr format. (00:00 to 23:59)
                        required: false
                        type: str
            IPFM_FABRIC_PARAMETERS:
                description:
                - IPFM (IP Fabric for Media) fabric specific parameters.
                - The following parameters are specific to IPFM fabrics.
                - Fabric for a fully automated deployment of IP Fabric for Media Network with Nexus 9000 switches.
                - The indentation of these parameters is meant only to logically group them.
                - They should be at the same YAML level as FABRIC_TYPE and FABRIC_NAME.
                suboptions:
                    AAA_REMOTE_IP_ENABLED:
                        default: false
                        description:
                        - Enable only, when IP Authorization is enabled in the AAA Server
                        required: false
                        type: bool
                    AAA_SERVER_CONF:
                        default: ''
                        description:
                        - AAA Configurations
                        required: false
                        type: str
                    ASM_GROUP_RANGES:
                        default: ''
                        description:
                        - 'ASM group ranges with prefixes (len:4-32) example: 239.1.1.0/25,
                            max 20 ranges. Enabling SPT-Threshold Infinity to prevent switchover
                            to source-tree.'
                        required: false
                        type: list
                        elements: str
                    BOOTSTRAP_CONF:
                        default: ''
                        description:
                        - Additional CLIs required during device bootup/login e.g. AAA/Radius
                        required: false
                        type: str
                    BOOTSTRAP_ENABLE:
                        default: false
                        description:
                        - Automatic IP Assignment For POAP
                        required: false
                        type: bool
                    BOOTSTRAP_MULTISUBNET:
                        default: '#Scope_Start_IP, Scope_End_IP, Scope_Default_Gateway, Scope_Subnet_Prefix'
                        description:
                        - 'lines with # prefix are ignored here'
                        required: false
                        type: str
                    CDP_ENABLE:
                        default: false
                        description:
                        - Enable CDP on management interface
                        required: false
                        type: bool
                    DHCP_ENABLE:
                        default: false
                        description:
                        - Automatic IP Assignment For POAP From Local DHCP Server
                        required: false
                        type: bool
                    DHCP_END:
                        default: ''
                        description:
                        - End Address For Switch Out-of-Band POAP
                        required: false
                        type: str
                    DHCP_IPV6_ENABLE:
                        choices:
                        - DHCPv4
                        default: DHCPv4
                        description:
                        - No description available
                        required: false
                        type: str
                    DHCP_START:
                        default: ''
                        description:
                        - Start Address For Switch Out-of-Band POAP
                        required: false
                        type: str
                    DNS_SERVER_IP_LIST:
                        default: ''
                        description:
                        - Comma separated list of IP Addresses (v4/v6)
                        required: false
                        type: str
                    DNS_SERVER_VRF:
                        default: ''
                        description:
                        - One VRF for all DNS servers or a comma separated list of VRFs, one
                            per DNS server
                        required: false
                        type: str
                    ENABLE_AAA:
                        default: false
                        description:
                        - Include AAA configs from Manageability tab during device bootup
                        required: false
                        type: bool
                    ENABLE_ASM:
                        default: false
                        description:
                        - Enable groups with receivers sending (*,G) joins
                        required: false
                        type: bool
                    ENABLE_NBM_PASSIVE:
                        default: false
                        description:
                        - Enable NBM mode to pim-passive for default VRF
                        required: false
                        type: bool
                    EXTRA_CONF_INTRA_LINKS:
                        default: ''
                        description:
                        - Additional CLIs For All Intra-Fabric Links
                        required: false
                        type: str
                    EXTRA_CONF_LEAF:
                        default: ''
                        description:
                        - Additional CLIs For All Leafs and Tier2 Leafs As Captured From Show
                            Running Configuration
                        required: false
                        type: str
                    EXTRA_CONF_SPINE:
                        default: ''
                        description:
                        - Additional CLIs For All Spines As Captured From Show Running Configuration
                        required: false
                        type: str
                    FABRIC_INTERFACE_TYPE:
                        choices:
                        - p2p
                        default: p2p
                        description:
                        - Only Numbered(Point-to-Point) is supported
                        required: false
                        type: str
                    FABRIC_MTU:
                        default: 9216
                        description:
                        - . Must be an even number
                        required: false
                        type: int
                    FABRIC_NAME:
                        default: ''
                        description:
                        - Name of the fabric (Max Size 64)
                        required: false
                        type: str
                    FEATURE_PTP:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    ISIS_AUTH_ENABLE:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    ISIS_AUTH_KEY:
                        default: ''
                        description:
                        - Cisco Type 7 Encrypted
                        required: false
                        type: str
                    ISIS_AUTH_KEYCHAIN_KEY_ID:
                        default: 127
                        description:
                        - No description available
                        required: false
                        type: int
                    ISIS_AUTH_KEYCHAIN_NAME:
                        default: ''
                        description:
                        - No description available
                        required: false
                        type: str
                    ISIS_LEVEL:
                        choices:
                        - level-1
                        - level-2
                        default: level-2
                        description:
                        - 'Supported IS types: level-1, level-2'
                        required: false
                        type: str
                    ISIS_P2P_ENABLE:
                        default: true
                        description:
                        - This will enable network point-to-point on fabric interfaces which
                            are numbered
                        required: false
                        type: bool
                    L2_HOST_INTF_MTU:
                        default: 9216
                        description:
                        - . Must be an even number
                        required: false
                        type: int
                    LINK_STATE_ROUTING:
                        choices:
                        - ospf
                        - is-is
                        default: ospf
                        description:
                        - Used for Spine-Leaf Connectivity
                        required: false
                        type: str
                    LINK_STATE_ROUTING_TAG:
                        default: "1"
                        description:
                        - Routing process tag for the fabric
                        required: false
                        type: str
                    LOOPBACK0_IP_RANGE:
                        default: 10.2.0.0/22
                        description:
                        - Routing Loopback IP Address Range
                        required: false
                        type: str
                    MGMT_GW:
                        default: ''
                        description:
                        - Default Gateway For Management VRF On The Switch
                        required: false
                        type: str
                    MGMT_PREFIX:
                        default: 24
                        description:
                        - No description available
                        required: false
                        type: int
                    NTP_SERVER_IP_LIST:
                        default: ''
                        description:
                        - Comma separated list of IP Addresses (v4/v6)
                        required: false
                        type: str
                    NTP_SERVER_VRF:
                        default: ''
                        description:
                        - One VRF for all NTP servers or a comma separated list of VRFs, one
                            per NTP server
                        required: false
                        type: str
                    NXAPI_VRF:
                        choices:
                        - management
                        - default
                        default: management
                        description:
                        - VRF used for NX-API communication
                        required: false
                        type: str
                    OSPF_AREA_ID:
                        default: 0.0.0.0
                        description:
                        - OSPF Area Id in IP address format
                        required: false
                        type: str
                    OSPF_AUTH_ENABLE:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    OSPF_AUTH_KEY:
                        default: ''
                        description:
                        - 3DES Encrypted
                        required: false
                        type: str
                    OSPF_AUTH_KEY_ID:
                        default: 127
                        description:
                        - No description available
                        required: false
                        type: int
                    PIM_HELLO_AUTH_ENABLE:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    PIM_HELLO_AUTH_KEY:
                        default: ''
                        description:
                        - 3DES Encrypted
                        required: false
                        type: str
                    PM_ENABLE:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    POWER_REDUNDANCY_MODE:
                        choices:
                        - ps-redundant
                        - combined
                        - insrc-redundant
                        default: ps-redundant
                        description:
                        - Default power supply mode for the fabric
                        required: false
                        type: str
                    PTP_DOMAIN_ID:
                        default: 0
                        description:
                        - 'Multiple Independent PTP Clocking Subdomains on a Single Network '
                        required: false
                        type: int
                    PTP_LB_ID:
                        default: 0
                        description:
                        - No description available
                        required: false
                        type: int
                    PTP_PROFILE:
                        choices:
                        - IEEE-1588v2
                        - SMPTE-2059-2
                        - AES67-2015
                        default: SMPTE-2059-2
                        description:
                        - Enabled on ISL links only
                        required: false
                        type: str
                    ROUTING_LB_ID:
                        default: 0
                        description:
                        - No description available
                        required: false
                        type: int
                    RP_IP_RANGE:
                        default: 10.254.254.0/24
                        description:
                        - RP Loopback IP Address Range
                        required: false
                        type: str
                    RP_LB_ID:
                        default: 254
                        description:
                        - No description available
                        required: false
                        type: int
                    SNMP_SERVER_HOST_TRAP:
                        default: true
                        description:
                        - Configure NDFC as a receiver for SNMP traps
                        required: false
                        type: bool
                    STATIC_UNDERLAY_IP_ALLOC:
                        default: false
                        description:
                        - Checking this will disable Dynamic Fabric IP Address Allocations
                        required: false
                        type: bool
                    SUBNET_RANGE:
                        default: 10.4.0.0/16
                        description:
                        - Address range to assign Numbered IPs
                        required: false
                        type: str
                    SUBNET_TARGET_MASK:
                        choices:
                        - 30
                        - 31
                        default: 30
                        description:
                        - Mask for Fabric Subnet IP Range
                        required: false
                        type: int
                    SYSLOG_SERVER_IP_LIST:
                        default: ''
                        description:
                        - Comma separated list of IP Addresses (v4/v6)
                        required: false
                        type: str
                    SYSLOG_SERVER_VRF:
                        default: ''
                        description:
                        - One VRF for all Syslog servers or a comma separated list of VRFs,
                            one per Syslog server
                        required: false
                        type: str
                    SYSLOG_SEV:
                        default: ''
                        description:
                        - 'Comma separated list of Syslog severity values, one per Syslog
                            server '
                        required: false
                        type: str
            LAN_CLASSIC_FABRIC_PARAMETERS:
                description:
                - LAN Classic fabric specific parameters.
                - The following parameters are specific to Classic LAN fabrics.
                - Fabric to manage a legacy Classic LAN deployment with Nexus switches.
                - The indentation of these parameters is meant only to logically group them.
                - They should be at the same YAML level as FABRIC_TYPE and FABRIC_NAME.
                suboptions:
                    AAA_REMOTE_IP_ENABLED:
                        default: false
                        description:
                        - Enable only, when IP Authorization is enabled in the AAA Server
                        required: false
                        type: bool
                    AAA_SERVER_CONF:
                        default: ''
                        description:
                        - AAA Configurations
                        required: false
                        type: str
                    BOOTSTRAP_CONF:
                        default: ''
                        description:
                        - Additional CLIs required during device bootup/login e.g. AAA/Radius
                        required: false
                        type: str
                    BOOTSTRAP_ENABLE:
                        default: false
                        description:
                        - Automatic IP Assignment For POAP
                        required: false
                        type: bool
                    BOOTSTRAP_MULTISUBNET:
                        default: '#Scope_Start_IP, Scope_End_IP, Scope_Default_Gateway, Scope_Subnet_Prefix'
                        description:
                        - 'lines with # prefix are ignored here'
                        required: false
                        type: str
                    CDP_ENABLE:
                        default: false
                        description:
                        - Enable CDP on management interface
                        required: false
                        type: bool
                    DHCP_ENABLE:
                        default: false
                        description:
                        - Automatic IP Assignment For POAP From Local DHCP Server
                        required: false
                        type: bool
                    DHCP_END:
                        default: ''
                        description:
                        - End Address For Switch POAP
                        required: false
                        type: str
                    DHCP_IPV6_ENABLE:
                        choices:
                        - DHCPv4
                        - DHCPv6
                        default: DHCPv4
                        description:
                        - No description available
                        required: false
                        type: str
                    DHCP_START:
                        default: ''
                        description:
                        - Start Address For Switch POAP
                        required: false
                        type: str
                    ENABLE_AAA:
                        default: false
                        description:
                        - Include AAA configs from Advanced tab during device bootup
                        required: false
                        type: bool
                    ENABLE_NETFLOW:
                        default: false
                        description:
                        - Enable Netflow on VTEPs
                        required: false
                        type: bool
                    ENABLE_NXAPI:
                        default: false
                        description:
                        - Enable HTTPS NX-API
                        required: false
                        type: bool
                    ENABLE_NXAPI_HTTP:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    FABRIC_FREEFORM:
                        default: ''
                        description:
                        - Additional supported CLIs for all same OS (e.g. all NxOS etc) switches
                        required: false
                        type: str
                    FABRIC_NAME:
                        default: ''
                        description:
                        - Please provide the fabric name to create it (Max Size 64)
                        required: false
                        type: str
                    FEATURE_PTP:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    INBAND_ENABLE:
                        default: false
                        description:
                        - 'Enable POAP over Inband Interface (Pre-req: Inband Mgmt Knob should
                            be Enabled)'
                        required: false
                        type: bool
                    INBAND_MGMT:
                        default: false
                        description:
                        - Import switches with inband connectivity
                        required: false
                        type: bool
                    IS_READ_ONLY:
                        default: true
                        description:
                        - If enabled, fabric is only monitored. No configuration will be deployed
                        required: false
                        type: bool
                    MGMT_GW:
                        default: ''
                        description:
                        - Default Gateway For Management VRF On The Switch
                        required: false
                        type: str
                    MGMT_PREFIX:
                        default: 24
                        description:
                        - No description available
                        required: false
                        type: int
                    MGMT_V6PREFIX:
                        default: 64
                        description:
                        - No description available
                        required: false
                        type: int
                    MPLS_HANDOFF:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    MPLS_LB_ID:
                        default: 101
                        description:
                        - No description available
                        required: false
                        type: int
                    MPLS_LOOPBACK_IP_RANGE:
                        default: 10.102.0.0/25
                        description:
                        - MPLS Loopback IP Address Range
                        required: false
                        type: str
                    NETFLOW_EXPORTER_LIST:
                        default: ''
                        description:
                        - One or Multiple Netflow Exporters
                        required: false
                        type: list
                        elements: str
                    NETFLOW_MONITOR_LIST:
                        default: ''
                        description:
                        - One or Multiple Netflow Monitors
                        required: false
                        type: list
                        elements: str
                    NETFLOW_RECORD_LIST:
                        default: ''
                        description:
                        - One or Multiple Netflow Records
                        required: false
                        type: list
                        elements: str
                    NETFLOW_SAMPLER_LIST:
                        default: ''
                        description:
                        - One or multiple netflow Samplers. Applicable to N7K only
                        required: false
                        type: list
                        elements: str
                    NXAPI_HTTPS_PORT:
                        default: 443
                        description:
                        - No description available
                        required: false
                        type: int
                    NXAPI_HTTP_PORT:
                        default: 80
                        description:
                        - No description available
                        required: false
                        type: int
                    PM_ENABLE:
                        default: false
                        description:
                        - No description available
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
                        required: false
                        type: str
                    PTP_DOMAIN_ID:
                        default: 0
                        description:
                        - 'Multiple Independent PTP Clocking Subdomains on a Single Network '
                        required: false
                        type: int
                    PTP_LB_ID:
                        default: 0
                        description:
                        - No description available
                        required: false
                        type: int
                    SNMP_SERVER_HOST_TRAP:
                        default: true
                        description:
                        - Configure NDFC as a receiver for SNMP traps
                        required: false
                        type: bool
                    SUBINTERFACE_RANGE:
                        default: 2-511
                        description:
                        - 'Per Border Dot1q Range For VRF Lite Connectivity '
                        required: false
                        type: str
                    enableRealTimeBackup:
                        default: false
                        description:
                        - Backup hourly only if there is any config deployment since last
                            backup
                        required: false
                        type: bool
                    enableScheduledBackup:
                        default: false
                        description:
                        - Backup at the specified time
                        required: false
                        type: bool
                    scheduledTime:
                        default: ''
                        description:
                        - Time (UTC) in 24hr format. (00:00 to 23:59)
                        required: false
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
        EXTRA_CONF_LEAF: |
          interface Ethernet1/1-16
            description managed by NDFC
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

# Setting skip_validation to True to bypass parameter validation in the module.
# Note, this does not bypass parameter validation in NDFC.  skip_validation
# can be useful to verify that the dcnm_fabric module's parameter validation
# is disallowing parameter combinations that would also be disallowed by
# NDFC.

- name: Update fabrics
  cisco.dcnm.dcnm_fabric:
    state: merged
    skip_validation: True
    config:
    -   FABRIC_NAME: VXLAN_Fabric
        FABRIC_TYPE: VXLAN_EVPN
        BGP_AS: 65000
        ANYCAST_GW_MAC: 0001.aabb.ccdd
        UNDERLAY_IS_V6: false
        EXTRA_CONF_LEAF: |
          interface Ethernet1/1-16
            description managed by NDFC
        DEPLOY: false

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

# When skip_validation is False (the default), some error messages might be
# misleading.  For example, with the playbook below, the error message
# that follows should be interpreted as "ENABLE_PVLAN is mutually-exclusive
# to ENABLE_SGT and should be removed from the playbook if ENABLE_SGT is set
# to True."  In the NDFC GUI, if Security Groups is enabled, NDFC disables
# the ability to modify the PVLAN option.  Hence, even a valid value for
# ENABLE_PVLAN in the playbook will generate an error.

-   name: merge fabric MyFabric
    cisco.dcnm.dcnm_fabric:
        state: merged
        skip_validation: false
        config:
        -   FABRIC_NAME: MyFabric
            FABRIC_TYPE: VXLAN_EVPN
            BGP_AS: 65001
            ENABLE_SGT: true
            ENABLE_PVLAN: false

# Resulting error message (edited for brevity)
# "The following parameter(value) combination(s) are invalid and need to be reviewed: Fabric: f3, ENABLE_PVLAN(False) requires ENABLE_SGT != True."

"""
# pylint: disable=wrong-import-position
import copy
import inspect
import json
import logging

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.common.controller_features import ControllerFeatures
from ..module_utils.common.exceptions import ControllerResponseError
from ..module_utils.common.log_v2 import Log
from ..module_utils.common.properties import Properties
from ..module_utils.common.response_handler import ResponseHandler
from ..module_utils.common.rest_send_v2 import RestSend
from ..module_utils.common.results import Results
from ..module_utils.common.sender_dcnm import Sender
from ..module_utils.fabric.common import FabricCommon
from ..module_utils.fabric.create import FabricCreateBulk
from ..module_utils.fabric.delete import FabricDelete
from ..module_utils.fabric.fabric_details_v2 import FabricDetailsByName
from ..module_utils.fabric.fabric_summary import FabricSummary
from ..module_utils.fabric.fabric_types import FabricTypes
from ..module_utils.fabric.query import FabricQuery
from ..module_utils.fabric.replaced import FabricReplacedBulk
from ..module_utils.fabric.template_get import TemplateGet
from ..module_utils.fabric.update import FabricUpdateBulk
from ..module_utils.fabric.verify_playbook_params import VerifyPlaybookParams


def json_pretty(msg):
    """
    Return a pretty-printed JSON string for logging messages
    """
    return json.dumps(msg, indent=4, sort_keys=True)


@Properties.add_rest_send
class Common(FabricCommon):
    """
    Common methods, properties, and resources for all states.
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        super().__init__()
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.controller_features = ControllerFeatures()
        self.features = {}
        self._implemented_states = set()

        self.params = params
        # populated in self.validate_input()
        self.payloads = {}

        self.populate_check_mode()
        self.populate_state()
        self.populate_config()

        self.results = Results()
        self.results.state = self.state
        self.results.check_mode = self.check_mode
        self._rest_send = None
        self._verify_playbook_params = VerifyPlaybookParams()

        self.have = {}
        self.query = []
        self.validated = []
        self.want = []

        msg = "ENTERED Common(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def populate_check_mode(self):
        """
        ### Summary
        Populate ``check_mode`` with the playbook check_mode.

        ### Raises
        -   ValueError if check_mode is not provided.
        """
        method_name = inspect.stack()[0][3]
        self.check_mode = self.params.get("check_mode", None)
        if self.check_mode is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "check_mode is required."
            raise ValueError(msg)

    def populate_config(self):
        """
        ### Summary
        Populate ``config`` with the playbook config.

        ### Raises
        -   ValueError if:
                -   ``state`` is "merged" or "replaced" and ``config`` is None.
                -   ``config`` is not a list.
        """
        method_name = inspect.stack()[0][3]
        states_requiring_config = {"merged", "replaced"}
        self.config = self.params.get("config", None)
        if self.state in states_requiring_config:
            if self.config is None:
                msg = f"{self.class_name}.{method_name}: "
                msg += "params is missing config parameter."
                raise ValueError(msg)
            if not isinstance(self.config, list):
                msg = f"{self.class_name}.{method_name}: "
                msg += "expected list type for self.config. "
                msg += f"got {type(self.config).__name__}"
                raise ValueError(msg)

    def populate_state(self):
        """
        ### Summary
        Populate ``state`` with the playbook state.

        ### Raises
        -   ValueError if:
                -   ``state`` is not provided.
                -   ``state`` is not a valid state.
        """
        method_name = inspect.stack()[0][3]

        valid_states = ["deleted", "merged", "query", "replaced"]

        self.state = self.params.get("state", None)
        if self.state is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "params is missing state parameter."
            raise ValueError(msg)
        if self.state not in valid_states:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Invalid state: {self.state}. "
            msg += f"Expected one of: {','.join(valid_states)}."
            raise ValueError(msg)

    def get_have(self):
        """
        ### Summary
        Build ``self.have``, which is a dict containing the current controller
        fabrics and their details.

        ### Raises
        -   ``ValueError`` if the controller returns an error when attempting to
            retrieve the fabric details.

        ### have structure

        ``have`` is a dict, keyed on fabric_name, where each element is a dict
        with the following structure.

        ```python
        have = {
            "fabric_name": "fabric_name",
            "fabric_config": {
                "fabricName": "fabric_name",
                "fabricType": "VXLAN EVPN",
                "etc...": "etc..."
            }
        }
        ```

        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        try:
            self.have = FabricDetailsByName()
            self.have.rest_send = self.rest_send
            self.have.results = Results()
            self.have.refresh()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Controller returned error when attempting to retrieve "
            msg += "fabric details. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

    def get_want(self) -> None:
        """
        ### Summary
        -   Validate the playbook configs.
        -   Update self.want with the playbook configs.

        ### Raises
        -   ``ValueError`` if the playbook configs are invalid.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        merged_configs = []
        for config in self.config:
            try:
                self._verify_payload(config)
            except ValueError as error:
                raise ValueError(f"{error}") from error
            merged_configs.append(copy.deepcopy(config))

        self.want = []
        for config in merged_configs:
            self.want.append(copy.deepcopy(config))

    def get_controller_features(self) -> None:
        """
        ### Summary

        -   Retrieve the state of relevant controller features
        -   Populate self.features
                -   key: FABRIC_TYPE
                -   value: True or False
                        -   True if feature is started for this fabric type
                        -   False otherwise

        ### Raises

        -   ``ValueError`` if the controller returns an error when attempting to
            retrieve the controller features.
        """
        method_name = inspect.stack()[0][3]
        self.features = {}
        self.controller_features.rest_send = self.rest_send
        try:
            self.controller_features.refresh()
        except ControllerResponseError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Controller returned error when attempting to retrieve "
            msg += "controller features. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        for fabric_type in self.fabric_types.valid_fabric_types:
            self.fabric_types.fabric_type = fabric_type
            self.controller_features.filter = self.fabric_types.feature_name
            self.features[fabric_type] = self.controller_features.started


class Deleted(Common):
    """
    ### Summary
    Handle deleted state
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        super().__init__(params)

        self.action = "fabric_delete"
        self.delete = FabricDelete()
        self._implemented_states.add("deleted")

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED Deleted(): "
        msg += f"state: {self.results.state}, "
        msg += f"check_mode: {self.results.check_mode}"
        self.log.debug(msg)

    def commit(self) -> None:
        """
        ### Summary
        delete the fabrics in ``self.want`` that exist on the controller.

        ### Raises

        -   ``ValueError`` if the controller returns an error when attempting to
            delete the fabrics.
        """
        self.get_want()
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED: {self.class_name}.{method_name}"
        self.log.debug(msg)

        self.fabric_details = FabricDetailsByName()
        self.fabric_details.rest_send = self.rest_send
        self.fabric_details.results = Results()

        self.fabric_summary = FabricSummary()
        self.fabric_summary.rest_send = self.rest_send
        self.fabric_summary.results = Results()

        self.delete.rest_send = self.rest_send
        self.delete.fabric_details = self.fabric_details
        self.delete.fabric_summary = self.fabric_summary
        self.delete.results = self.results

        fabric_names_to_delete = []
        for want in self.want:
            fabric_names_to_delete.append(want["FABRIC_NAME"])

        try:
            self.delete.fabric_names = fabric_names_to_delete
        except ValueError as error:
            raise ValueError(f"{error}") from error

        try:
            self.delete.commit()
        except ValueError as error:
            raise ValueError(f"{error}") from error


class Merged(Common):
    """
    ### Summary
    Handle merged state.

    ### Raises

    -   ``ValueError`` if:
        -   The controller features required for the fabric type are not
            running on the controller.
        -   The playbook parameters are invalid.
        -   The controller returns an error when attempting to retrieve
            the template.
        -   The controller returns an error when attempting to retrieve
            the fabric details.
        -   The controller returns an error when attempting to create
            the fabric.
        -   The controller returns an error when attempting to update
            the fabric.
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        super().__init__(params)
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.action = "fabric_create"
        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.fabric_details = FabricDetailsByName()
        self.fabric_summary = FabricSummary()
        self.fabric_create = FabricCreateBulk()
        self.fabric_types = FabricTypes()
        self.fabric_update = FabricUpdateBulk()
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
        ### Summary
        Build ``self.need`` for merged state.

        ### Raises
        -   ``ValueError`` if:
            -   The controller features required for the fabric type are not
                running on the controller.
            -   The playbook parameters are invalid.
            -   The controller returns an error when attempting to retrieve
                the template.
            -   The controller returns an error when attempting to retrieve
                the fabric details.
        """
        method_name = inspect.stack()[0][3]
        self.payloads = {}
        for want in self.want:

            fabric_name = want.get("FABRIC_NAME", None)
            fabric_type = want.get("FABRIC_TYPE", None)

            if self.features[fabric_type] is False:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Features required for fabric {fabric_name} "
                msg += f"of type {fabric_type} are not running on the "
                msg += "controller. Review controller settings at "
                msg += "Fabric Controller -> Admin -> System Settings -> "
                msg += "Feature Management"
                raise ValueError(msg)

            try:
                self._verify_playbook_params.config_playbook = want
            except TypeError as error:
                raise ValueError(f"{error}") from error

            try:
                self.fabric_types.fabric_type = fabric_type
            except ValueError as error:
                raise ValueError(f"{error}") from error

            try:
                template_name = self.fabric_types.template_name
            except ValueError as error:
                raise ValueError(f"{error}") from error

            self.template.rest_send = self.rest_send
            self.template.template_name = template_name

            try:
                self.template.refresh()
            except ValueError as error:
                raise ValueError(f"{error}") from error
            except ControllerResponseError as error:
                msg = f"{self.class_name}.{method_name}: "
                msg += "Controller returned error when attempting to retrieve "
                msg += f"template: {template_name}. "
                msg += f"Error detail: {error}"
                raise ValueError(msg) from error

            try:
                self._verify_playbook_params.template = self.template.template
            except TypeError as error:
                raise ValueError(f"{error}") from error

            # Append to need_create if the fabric does not exist.
            # Otherwise, append to need_update.
            if fabric_name not in self.have.all_data:
                try:
                    self._verify_playbook_params.config_controller = None
                except TypeError as error:
                    raise ValueError(f"{error}") from error

                if self.params.get("skip_validation") is False:
                    try:
                        self._verify_playbook_params.commit()
                    except ValueError as error:
                        raise ValueError(f"{error}") from error
                else:
                    msg = f"{self.class_name}.{method_name}: "
                    msg += "skip_validation: "
                    msg += f"{self.params.get('skip_validation')}, "
                    msg += "skipping parameter validation."
                    self.log.debug(msg)

                self.need_create.append(want)

            else:

                nv_pairs = self.have.all_data[fabric_name]["nvPairs"]
                try:
                    self._verify_playbook_params.config_controller = nv_pairs
                except TypeError as error:
                    raise ValueError(f"{error}") from error
                if self.params.get("skip_validation") is False:
                    try:
                        self._verify_playbook_params.commit()
                    except (ValueError, KeyError) as error:
                        raise ValueError(f"{error}") from error
                else:
                    msg = f"{self.class_name}.{method_name}: "
                    msg += "skip_validation: "
                    msg += f"{self.params.get('skip_validation')}, "
                    msg += "skipping parameter validation."
                    self.log.debug(msg)

                self.need_update.append(want)

    def commit(self):
        """
        ### Summary
        Commit the merged state request.

        ### Raises
        -   ``ValueError`` if:
            -   The controller features required for the fabric type are not
                running on the controller.
            -   The playbook parameters are invalid.
            -   The controller returns an error when attempting to retrieve
                the template.
            -   The controller returns an error when attempting to retrieve
                the fabric details.
            -   The controller returns an error when attempting to create
                the fabric.
            -   The controller returns an error when attempting to update
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        msg = f"{self.class_name}.{method_name}: entered"
        self.log.debug(msg)

        self.fabric_details.rest_send = self.rest_send
        self.fabric_summary.rest_send = self.rest_send

        self.fabric_details.results = Results()
        self.fabric_summary.results = Results()

        self.get_controller_features()
        self.get_want()
        self.get_have()
        self.get_need()
        self.send_need_create()
        self.send_need_update()

    def send_need_create(self) -> None:
        """
        ### Summary
        Build and send the payload to create fabrics specified in the playbook.

        ### Raises

        -   ``ValueError`` if:
            -   Any payload is invalid.
            -   The controller returns an error when attempting to create
                the fabric.
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
            raise ValueError(f"{error}") from error

        try:
            self.fabric_create.commit()
        except ValueError as error:
            raise ValueError(f"{error}") from error

    def send_need_update(self) -> None:
        """
        ### Summary
        Build and send the payload to create fabrics specified in the playbook.

        ### Raises

        -   ``ValueError`` if:
            -   Any payload is invalid.
            -   The controller returns an error when attempting to update
                the fabric.
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
        self.fabric_update.rest_send = self.rest_send
        self.fabric_update.results = self.results

        try:
            self.fabric_update.payloads = self.need_update
        except ValueError as error:
            raise ValueError(f"{error}") from error

        try:
            self.fabric_update.commit()
        except ValueError as error:
            raise ValueError(f"{error}") from error


class Query(Common):
    """
    ### Summary
    Handle query state.

    ### Raises

    -   ``ValueError`` if:
        -   The playbook parameters are invalid.
        -   The controller returns an error when attempting to retrieve
            the fabric details.
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        super().__init__(params)

        self.action = "fabric_query"
        self._implemented_states.add("query")

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED Query(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def commit(self) -> None:
        """
        ### Summary
        query the fabrics in ``self.want`` that exist on the controller.

        ### Raises

        -   ``ValueError`` if:
            -   Any fabric names are invalid.
            -   The controller returns an error when attempting to
                query the fabrics.
        """
        self.fabric_details = FabricDetailsByName()
        self.fabric_details.rest_send = self.rest_send
        self.fabric_details.results = Results()

        self.get_want()

        fabric_query = FabricQuery()
        fabric_query.fabric_details = self.fabric_details
        fabric_query.rest_send = self.rest_send
        fabric_query.results = self.results

        fabric_names_to_query = []
        for want in self.want:
            fabric_names_to_query.append(want["FABRIC_NAME"])
        try:
            fabric_query.fabric_names = copy.copy(fabric_names_to_query)
        except ValueError as error:
            raise ValueError(f"{error}") from error

        try:
            fabric_query.commit()
        except ValueError as error:
            raise ValueError(f"{error}") from error


class Replaced(Common):
    """
    ### Summary
    Handle replaced state.

    ### Raises

    -   ``ValueError`` if:
        -   The controller features required for the fabric type are not
            running on the controller.
        -   The playbook parameters are invalid.
        -   The controller returns an error when attempting to retrieve
            the template.
        -   The controller returns an error when attempting to retrieve
            the fabric details.
        -   The controller returns an error when attempting to create
            the fabric.
        -   The controller returns an error when attempting to update
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        super().__init__(params)
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.action = "fabric_replaced"
        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.fabric_details = FabricDetailsByName()
        self.fabric_replaced = FabricReplacedBulk()
        self.fabric_summary = FabricSummary()
        self.fabric_types = FabricTypes()
        self.merged = None
        self.need_create = []
        self.need_replaced = []
        self.template = TemplateGet()
        self._implemented_states.add("replaced")

        msg = f"ENTERED Replaced.{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def get_need(self):
        """
        ### Summary
        Build ``self.need`` for replaced state.

        ### Raises
        -   ``ValueError`` if:
            -   The controller features required for the fabric type are not
                running on the controller.
        """
        method_name = inspect.stack()[0][3]
        self.payloads = {}
        for want in self.want:

            fabric_name = want.get("FABRIC_NAME", None)
            fabric_type = want.get("FABRIC_TYPE", None)

            # If fabrics do not exist on the controller, add them to
            # need_create.  These will be created by Merged() in
            # Replaced.send_need_replaced()
            if fabric_name not in self.have.all_data:
                self.need_create.append(want)
                continue

            if self.features[fabric_type] is False:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Features required for fabric {fabric_name} "
                msg += f"of type {fabric_type} are not running on the "
                msg += "controller. Review controller settings at "
                msg += "Fabric Controller -> Admin -> System Settings -> "
                msg += "Feature Management"
                raise ValueError(msg)

            self.need_replaced.append(want)

    def commit(self):
        """
        ### Summary
        Commit the replaced state request.

        ### Raises

        -   ``ValueError`` if:
            -   The controller features required for the fabric type are not
                running on the controller.
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: entered"
        self.log.debug(msg)

        self.fabric_details.rest_send = self.rest_send
        self.fabric_summary.rest_send = self.rest_send

        self.fabric_details.results = Results()
        self.fabric_summary.results = Results()

        self.get_controller_features()
        self.get_want()
        self.get_have()
        self.get_need()
        self.send_need_replaced()

    def send_need_replaced(self) -> None:
        """
        ### Summary
        Build and send the payload to modify fabrics specified in the
        playbook per replaced state handling.

        ### Raises

        -   ``ValueError`` if:
            -   Any payload is invalid.
            -   The controller returns an error when attempting to
                 update the fabric.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        msg = f"{self.class_name}.{method_name}: entered. "
        msg += "self.need_replaced: "
        msg += f"{json_pretty(self.need_replaced)}"
        self.log.debug(msg)

        if len(self.need_create) != 0:
            self.merged = Merged(self.params)
            self.merged.rest_send = self.rest_send
            self.merged.fabric_details.rest_send = self.rest_send
            self.merged.fabric_summary.rest_send = self.rest_send
            self.merged.results = self.results
            self.merged.need_create = self.need_create
            self.merged.send_need_create()

        if len(self.need_replaced) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "No fabrics to update for replaced state."
            self.log.debug(msg)
            return

        self.fabric_replaced.fabric_details = self.fabric_details
        self.fabric_replaced.fabric_summary = self.fabric_summary
        self.fabric_replaced.rest_send = self.rest_send
        self.fabric_replaced.results = self.results

        try:
            self.fabric_replaced.payloads = self.need_replaced
        except ValueError as error:
            raise ValueError(f"{error}") from error

        try:
            self.fabric_replaced.commit()
        except ValueError as error:
            raise ValueError(f"{error}") from error


def main():
    """
    ### Summary
    main entry point for module execution.

    -   In the event that ``ValueError`` is raised, ``AnsibleModule.fail_json``
        is called with the error message.
    -   Else, ``AnsibleModule.exit_json`` is called with the final result.

    ### Raises
    -   ``ValueError`` if:
        -   The playbook parameters are invalid.
        -   The controller returns an error when attempting to
            delete, create, query, or update the fabrics.
    """

    argument_spec = {}
    argument_spec["config"] = {"required": False, "type": "list", "elements": "dict"}
    argument_spec["skip_validation"] = {
        "required": False,
        "type": "bool",
        "default": False,
    }
    argument_spec["state"] = {
        "default": "merged",
        "choices": ["deleted", "merged", "query", "replaced"],
    }

    ansible_module = AnsibleModule(
        argument_spec=argument_spec, supports_check_mode=True
    )
    params = copy.deepcopy(ansible_module.params)
    params["check_mode"] = ansible_module.check_mode

    # Logging setup
    try:
        log = Log()
        log.commit()
    except ValueError as error:
        ansible_module.fail_json(str(error))

    sender = Sender()
    sender.ansible_module = ansible_module
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    try:
        task = None
        if params["state"] == "merged":
            task = Merged(params)
        elif params["state"] == "deleted":
            task = Deleted(params)
        elif params["state"] == "query":
            task = Query(params)
        elif params["state"] == "replaced":
            task = Replaced(params)
        if task is None:
            ansible_module.fail_json(f"Invalid state: {params['state']}")
        task.rest_send = rest_send
        task.commit()
    except ValueError as error:
        ansible_module.fail_json(f"{error}", **task.results.failed_result)

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
