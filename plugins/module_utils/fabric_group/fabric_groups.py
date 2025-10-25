#
# Copyright (c) 2025 Cisco and/or its affiliates.
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
# pylint: disable=too-many-lines,too-many-instance-attributes
"""
# Summary

Provides one public class:
-   FabricGroups
    Retrieve details about fabric groups.

## Example response

[
    {
        "id": 31,
        "clusterName": "",
        "fabricId": "MC-FABRIC-31",
        "fabricName": "MCFG_TEST",
        "fabricType": "MFD",
        "fabricTypeFriendly": "VXLAN EVPN Multi-Site",
        "fabricTechnology": "VXLANFabric",
        "fabricTechnologyFriendly": "VXLAN EVPN",
        "provisionMode": "",
        "deviceType": "",
        "replicationMode": "",
        "operStatus": "HEALTHY",
        "asn": "",
        "siteId": "",
        "templateName": "MSD_Fabric",
        "nvPairs": {
            "ANYCAST_GW_MAC": "2020.0000.00aa",
            "BGP_RP_ASN": "",
            "BGW_ROUTING_TAG": "54321",
            "BGW_ROUTING_TAG_PREV": "54321",
            "BORDER_GWY_CONNECTIONS": "Manual",
            "CLOUDSEC_ALGORITHM": "",
            "CLOUDSEC_AUTOCONFIG": "false",
            "CLOUDSEC_ENFORCEMENT": "",
            "CLOUDSEC_KEY_STRING": "",
            "CLOUDSEC_REPORT_TIMER": "",
            "DCI_SUBNET_RANGE": "10.10.1.0/24",
            "DCI_SUBNET_TARGET_MASK": "30",
            "DCNM_ID": "",
            "DELAY_RESTORE": "300",
            "ENABLE_BGP_BFD": false,
            "ENABLE_BGP_LOG_NEIGHBOR_CHANGE": false,
            "ENABLE_BGP_SEND_COMM": false,
            "ENABLE_PVLAN": "false",
            "ENABLE_PVLAN_PREV": "",
            "ENABLE_RS_REDIST_DIRECT": false,
            "ENABLE_SGT": "off",
            "ENABLE_SGT_PREV": "off",
            "ENABLE_TRM_TRMv6": "false",
            "ENABLE_TRM_TRMv6_PREV": "",
            "EXT_FABRIC_TYPE": "",
            "FABRIC_NAME": "MCFG_TEST",
            "FABRIC_TYPE": "MFD",
            "FF": "MSD",
            "L2_SEGMENT_ID_RANGE": "30000-49000",
            "L3_PARTITION_ID_RANGE": "50000-59000",
            "LOOPBACK100_IPV6_RANGE": "",
            "LOOPBACK100_IP_RANGE": "10.10.0.0/24",
            "MSO_CONTROLER_ID": "",
            "MSO_SITE_GROUP_NAME": "",
            "MS_IFC_BGP_AUTH_KEY_TYPE": "",
            "MS_IFC_BGP_AUTH_KEY_TYPE_PREV": "",
            "MS_IFC_BGP_PASSWORD": "",
            "MS_IFC_BGP_PASSWORD_ENABLE": "false",
            "MS_IFC_BGP_PASSWORD_ENABLE_PREV": "",
            "MS_IFC_BGP_PASSWORD_PREV": "",
            "MS_LOOPBACK_ID": "100",
            "MS_UNDERLAY_AUTOCONFIG": "false",
            "PARENT_ONEMANAGE_FABRIC": "",
            "PREMSO_PARENT_FABRIC": "",
            "RP_SERVER_IP": "",
            "RS_ROUTING_TAG": "",
            "SGT_ID_RANGE": "",
            "SGT_ID_RANGE_PREV": "10000-14000",
            "SGT_NAME_PREFIX": "",
            "SGT_NAME_PREFIX_PREV": "SG_",
            "SGT_OPER_STATUS": "off",
            "SGT_PREPROVISION": false,
            "SGT_PREPROVISION_PREV": "false",
            "SGT_PREPROV_RECALC_STATUS": "empty",
            "SGT_RECALC_STATUS": "empty",
            "TOR_AUTO_DEPLOY": "false",
            "V6_DCI_SUBNET_RANGE": "",
            "V6_DCI_SUBNET_TARGET_MASK": "",
            "VXLAN_UNDERLAY_IS_V6": "false",
            "default_network": "Default_Network_Universal",
            "default_pvlan_sec_network": "",
            "default_vrf": "Default_VRF_Universal",
            "enableScheduledBackup": "",
            "network_extension_template": "Default_Network_Extension_Universal",
            "scheduledTime": "",
            "vrf_extension_template": "Default_VRF_Extension_Universal"
        },
        "vrfTemplate": "",
        "networkTemplate": "",
        "vrfExtensionTemplate": "",
        "networkExtensionTemplate": "",
        "createdOn": 1761097106,
        "modifiedOn": 1761097106,
        "members": [
            {
                "clusterName": "ND3",
                "fabricId": 3,
                "fabricName": "SITE3",
                "templateName": "Easy_Fabric",
                "fabricType": "Switch_Fabric",
                "fabricState": "member",
                "fabricParent": "MCFG_TEST",
                "fabricTechnology": "VXLANFabric",
                "fabricTypeFriendly": "Data Center VXLAN EVPN",
                "fabricTechnologyFriendly": "VXLAN EVPN",
                "asn": "65001",
                "ndfcIpAddress": "192.168.7.8",
                "clusterIpAddresses": [
                    "192.168.7.8"
                ],
                "operStatus": "HEALTHY",
                "nvPairs": {
                    "AAA_REMOTE_IP_ENABLED": "false",
                    "AAA_SERVER_CONF": "",
                    "ACTIVE_MIGRATION": "false",
                    "ADVERTISE_PIP_BGP": "false",
                    "ADVERTISE_PIP_ON_BORDER": "true",
                    "AGENT_INTF": "eth0",
                    "AGG_ACC_VPC_PO_ID_RANGE": "",
                    "AI_ML_QOS_POLICY": "AI_Fabric_QOS_400G",
                    "ALLOW_L3VNI_NO_VLAN": "true",
                    "ALLOW_L3VNI_NO_VLAN_PREV": "true",
                    "ALLOW_NXC": "true",
                    "ALLOW_NXC_PREV": "true",
                    "ANYCAST_BGW_ADVERTISE_PIP": "false",
                    "ANYCAST_GW_MAC": "2020.0000.00aa",
                    "ANYCAST_LB_ID": "",
                    "ANYCAST_RP_IP_RANGE": "10.13.254.0/24",
                    "ANYCAST_RP_IP_RANGE_INTERNAL": "10.13.254.0/24",
                    "AUTO_SYMMETRIC_DEFAULT_VRF": "false",
                    "AUTO_SYMMETRIC_VRF_LITE": "true",
                    "AUTO_UNIQUE_VRF_LITE_IP_PREFIX": "false",
                    "AUTO_UNIQUE_VRF_LITE_IP_PREFIX_PREV": "false",
                    "AUTO_VRFLITE_IFC_DEFAULT_VRF": "false",
                    "BANNER": "",
                    "BFD_AUTH_ENABLE": "false",
                    "BFD_AUTH_KEY": "",
                    "BFD_AUTH_KEY_ID": "",
                    "BFD_ENABLE": "false",
                    "BFD_ENABLE_PREV": "false",
                    "BFD_IBGP_ENABLE": "false",
                    "BFD_ISIS_ENABLE": "false",
                    "BFD_OSPF_ENABLE": "false",
                    "BFD_PIM_ENABLE": "false",
                    "BGP_AS": "65001",
                    "BGP_AS_PREV": "65001",
                    "BGP_AUTH_ENABLE": "false",
                    "BGP_AUTH_KEY": "",
                    "BGP_AUTH_KEY_TYPE": "3",
                    "BGP_LB_ID": "0",
                    "BOOTSTRAP_CONF": "",
                    "BOOTSTRAP_ENABLE": "true",
                    "BOOTSTRAP_ENABLE_PREV": "true",
                    "BOOTSTRAP_MULTISUBNET": "#Scope_Start_IP, Scope_End_IP, Scope_Default_Gateway, Scope_Subnet_Prefix",
                    "BOOTSTRAP_MULTISUBNET_INTERNAL": "",
                    "BRFIELD_DEBUG_FLAG": "Disable",
                    "BROWNFIELD_NETWORK_NAME_FORMAT": "Auto_Net_VNI$$VNI$$_VLAN$$VLAN_ID$$",
                    "BROWNFIELD_SKIP_OVERLAY_NETWORK_ATTACHMENTS": "false",
                    "CDP_ENABLE": "false",
                    "COPP_POLICY": "strict",
                    "DCI_MACSEC_ALGORITHM": "",
                    "DCI_MACSEC_CIPHER_SUITE": "",
                    "DCI_MACSEC_FALLBACK_ALGORITHM": "",
                    "DCI_MACSEC_FALLBACK_KEY_STRING": "",
                    "DCI_MACSEC_KEY_STRING": "",
                    "DCI_SUBNET_RANGE": "10.15.0.0/16",
                    "DCI_SUBNET_TARGET_MASK": "30",
                    "DEAFULT_QUEUING_POLICY_CLOUDSCALE": "queuing_policy_default_8q_cloudscale",
                    "DEAFULT_QUEUING_POLICY_OTHER": "queuing_policy_default_other",
                    "DEAFULT_QUEUING_POLICY_R_SERIES": "queuing_policy_default_r_series",
                    "DEFAULT_VRF_REDIS_BGP_RMAP": "",
                    "DEPLOYMENT_FREEZE": "false",
                    "DHCP_ENABLE": "false",
                    "DHCP_END": "",
                    "DHCP_END_INTERNAL": "",
                    "DHCP_IPV6_ENABLE": "",
                    "DHCP_IPV6_ENABLE_INTERNAL": "",
                    "DHCP_START": "",
                    "DHCP_START_INTERNAL": "",
                    "DNS_SERVER_IP_LIST": "",
                    "DNS_SERVER_VRF": "",
                    "DOMAIN_NAME_INTERNAL": "",
                    "ENABLE_AAA": "false",
                    "ENABLE_AGENT": "false",
                    "ENABLE_AGG_ACC_ID_RANGE": "false",
                    "ENABLE_AI_ML_QOS_POLICY": "false",
                    "ENABLE_AI_ML_QOS_POLICY_FLAP": "false",
                    "ENABLE_DCI_MACSEC": "false",
                    "ENABLE_DCI_MACSEC_PREV": "false",
                    "ENABLE_DEFAULT_QUEUING_POLICY": "false",
                    "ENABLE_EVPN": "true",
                    "ENABLE_FABRIC_VPC_DOMAIN_ID": "false",
                    "ENABLE_FABRIC_VPC_DOMAIN_ID_PREV": "false",
                    "ENABLE_L3VNI_NO_VLAN": "false",
                    "ENABLE_MACSEC": "false",
                    "ENABLE_MACSEC_PREV": "false",
                    "ENABLE_NETFLOW": "false",
                    "ENABLE_NETFLOW_PREV": "false",
                    "ENABLE_NGOAM": "true",
                    "ENABLE_NXAPI": "true",
                    "ENABLE_NXAPI_HTTP": "true",
                    "ENABLE_PBR": "false",
                    "ENABLE_PVLAN": "false",
                    "ENABLE_PVLAN_PREV": "false",
                    "ENABLE_QKD": "false",
                    "ENABLE_RT_INTF_STATS": "false",
                    "ENABLE_SGT": "false",
                    "ENABLE_SGT_PREV": "false",
                    "ENABLE_TENANT_DHCP": "true",
                    "ENABLE_TRM": "false",
                    "ENABLE_TRMv6": "false",
                    "ENABLE_VPC_PEER_LINK_NATIVE_VLAN": "false",
                    "ENABLE_VRI_ID_REALLOC": "false",
                    "EXTRA_CONF_INTRA_LINKS": "",
                    "EXTRA_CONF_LEAF": "",
                    "EXTRA_CONF_SPINE": "",
                    "EXTRA_CONF_TOR": "",
                    "EXT_FABRIC_TYPE": "",
                    "FABRIC_INTERFACE_TYPE": "p2p",
                    "FABRIC_MTU": "9216",
                    "FABRIC_MTU_PREV": "9216",
                    "FABRIC_NAME": "SITE3",
                    "FABRIC_TYPE": "Switch_Fabric",
                    "FABRIC_VPC_DOMAIN_ID": "",
                    "FABRIC_VPC_DOMAIN_ID_PREV": "",
                    "FABRIC_VPC_QOS": "false",
                    "FABRIC_VPC_QOS_POLICY_NAME": "spine_qos_for_fabric_vpc_peering",
                    "FEATURE_PTP": "false",
                    "FEATURE_PTP_INTERNAL": "false",
                    "FF": "Easy_Fabric",
                    "GRFIELD_DEBUG_FLAG": "Disable",
                    "HD_TIME": "180",
                    "HOST_INTF_ADMIN_STATE": "true",
                    "IBGP_PEER_TEMPLATE": "",
                    "IBGP_PEER_TEMPLATE_LEAF": "",
                    "IGNORE_CERT": "false",
                    "INBAND_DHCP_SERVERS": "",
                    "INBAND_MGMT": "false",
                    "INBAND_MGMT_PREV": "false",
                    "INTF_STAT_LOAD_INTERVAL": "",
                    "IPv6_ANYCAST_RP_IP_RANGE": "",
                    "IPv6_ANYCAST_RP_IP_RANGE_INTERNAL": "",
                    "IPv6_MULTICAST_GROUP_SUBNET": "",
                    "ISIS_AREA_NUM": "0001",
                    "ISIS_AREA_NUM_PREV": "",
                    "ISIS_AUTH_ENABLE": "false",
                    "ISIS_AUTH_KEY": "",
                    "ISIS_AUTH_KEYCHAIN_KEY_ID": "",
                    "ISIS_AUTH_KEYCHAIN_NAME": "",
                    "ISIS_LEVEL": "level-2",
                    "ISIS_OVERLOAD_ELAPSE_TIME": "",
                    "ISIS_OVERLOAD_ENABLE": "false",
                    "ISIS_P2P_ENABLE": "false",
                    "KME_SERVER_IP": "",
                    "KME_SERVER_PORT": "",
                    "L2_HOST_INTF_MTU": "9216",
                    "L2_HOST_INTF_MTU_PREV": "9216",
                    "L2_SEGMENT_ID_RANGE": "30000-49000",
                    "L3VNI_IPv6_MCAST_GROUP": "",
                    "L3VNI_MCAST_GROUP": "",
                    "L3_PARTITION_ID_RANGE": "50000-59000",
                    "LINK_STATE_ROUTING": "ospf",
                    "LINK_STATE_ROUTING_TAG": "UNDERLAY",
                    "LINK_STATE_ROUTING_TAG_PREV": "UNDERLAY",
                    "LOOPBACK0_IPV6_RANGE": "",
                    "LOOPBACK0_IP_RANGE": "10.11.0.0/22",
                    "LOOPBACK1_IPV6_RANGE": "",
                    "LOOPBACK1_IP_RANGE": "10.12.0.0/22",
                    "MACSEC_ALGORITHM": "",
                    "MACSEC_CIPHER_SUITE": "",
                    "MACSEC_FALLBACK_ALGORITHM": "",
                    "MACSEC_FALLBACK_KEY_STRING": "",
                    "MACSEC_KEY_STRING": "",
                    "MACSEC_REPORT_TIMER": "",
                    "MGMT_GW": "",
                    "MGMT_GW_INTERNAL": "",
                    "MGMT_PREFIX": "",
                    "MGMT_PREFIX_INTERNAL": "",
                    "MGMT_V6PREFIX": "",
                    "MGMT_V6PREFIX_INTERNAL": "",
                    "MPLS_HANDOFF": "false",
                    "MPLS_ISIS_AREA_NUM": "0001",
                    "MPLS_ISIS_AREA_NUM_PREV": "",
                    "MPLS_LB_ID": "",
                    "MPLS_LOOPBACK_IP_RANGE": "",
                    "MSO_CONNECTIVITY_DEPLOYED": "",
                    "MSO_CONTROLER_ID": "",
                    "MSO_SITE_GROUP_NAME": "",
                    "MSO_SITE_ID": "",
                    "MST_INSTANCE_RANGE": "",
                    "MULTICAST_GROUP_SUBNET": "239.1.1.0/25",
                    "MVPN_VRI_ID_RANGE": "",
                    "NETFLOW_EXPORTER_LIST": "",
                    "NETFLOW_MONITOR_LIST": "",
                    "NETFLOW_RECORD_LIST": "",
                    "NETWORK_VLAN_RANGE": "2300-2999",
                    "NTP_SERVER_IP_LIST": "",
                    "NTP_SERVER_VRF": "",
                    "NVE_LB_ID": "1",
                    "NXAPI_HTTPS_PORT": "443",
                    "NXAPI_HTTP_PORT": "80",
                    "NXC_DEST_VRF": "management",
                    "NXC_PROXY_PORT": "8080",
                    "NXC_PROXY_SERVER": "",
                    "NXC_SRC_INTF": "",
                    "OBJECT_TRACKING_NUMBER_RANGE": "100-299",
                    "OSPF_AREA_ID": "0.0.0.0",
                    "OSPF_AUTH_ENABLE": "false",
                    "OSPF_AUTH_KEY": "",
                    "OSPF_AUTH_KEY_ID": "",
                    "OVERLAY_MODE": "cli",
                    "OVERLAY_MODE_PREV": "cli",
                    "OVERWRITE_GLOBAL_NXC": "false",
                    "PER_VRF_LOOPBACK_AUTO_PROVISION": "false",
                    "PER_VRF_LOOPBACK_AUTO_PROVISION_PREV": "false",
                    "PER_VRF_LOOPBACK_AUTO_PROVISION_V6": "false",
                    "PER_VRF_LOOPBACK_AUTO_PROVISION_V6_PREV": "false",
                    "PER_VRF_LOOPBACK_IP_RANGE": "",
                    "PER_VRF_LOOPBACK_IP_RANGE_V6": "",
                    "PFC_WATCH_INT": "",
                    "PFC_WATCH_INT_PREV": "",
                    "PHANTOM_RP_LB_ID1": "",
                    "PHANTOM_RP_LB_ID2": "",
                    "PHANTOM_RP_LB_ID3": "",
                    "PHANTOM_RP_LB_ID4": "",
                    "PIM_HELLO_AUTH_ENABLE": "false",
                    "PIM_HELLO_AUTH_KEY": "",
                    "PM_ENABLE": "false",
                    "PM_ENABLE_PREV": "false",
                    "PNP_ENABLE_INTERNAL": "",
                    "POWER_REDUNDANCY_MODE": "ps-redundant",
                    "PREMSO_PARENT_FABRIC": "",
                    "PTP_DOMAIN_ID": "",
                    "PTP_LB_ID": "",
                    "PTP_VLAN_ID": "",
                    "QKD_PROFILE_NAME": "",
                    "QKD_PROFILE_NAME_PREV": "",
                    "REPLICATION_MODE": "Multicast",
                    "ROUTER_ID_RANGE": "",
                    "ROUTE_MAP_SEQUENCE_NUMBER_RANGE": "1-65534",
                    "RP_COUNT": "2",
                    "RP_LB_ID": "254",
                    "RP_MODE": "asm",
                    "RR_COUNT": "2",
                    "SEED_SWITCH_CORE_INTERFACES": "",
                    "SERVICE_NETWORK_VLAN_RANGE": "3000-3199",
                    "SGT_ID_RANGE": "",
                    "SGT_NAME_PREFIX": "",
                    "SGT_OPER_STATUS": "off",
                    "SGT_PREPROVISION": "false",
                    "SGT_PREPROVISION_PREV": "false",
                    "SGT_PREPROV_RECALC_STATUS": "empty",
                    "SGT_RECALC_STATUS": "empty",
                    "SITE_ID": "6001",
                    "SITE_ID_POLICY_ID": "",
                    "SLA_ID_RANGE": "10000-19999",
                    "SNMP_SERVER_HOST_TRAP": "true",
                    "SPINE_COUNT": "0",
                    "SPINE_SWITCH_CORE_INTERFACES": "",
                    "SSPINE_ADD_DEL_DEBUG_FLAG": "Disable",
                    "SSPINE_COUNT": "0",
                    "STATIC_UNDERLAY_IP_ALLOC": "false",
                    "STP_BRIDGE_PRIORITY": "",
                    "STP_ROOT_OPTION": "unmanaged",
                    "STP_VLAN_RANGE": "",
                    "STRICT_CC_MODE": "false",
                    "SUBINTERFACE_RANGE": "2-511",
                    "SUBNET_RANGE": "10.14.0.0/16",
                    "SUBNET_TARGET_MASK": "30",
                    "SYSLOG_SERVER_IP_LIST": "",
                    "SYSLOG_SERVER_VRF": "",
                    "SYSLOG_SEV": "",
                    "TCAM_ALLOCATION": "true",
                    "TOPDOWN_CONFIG_RM_TRACKING": "notstarted",
                    "TRUSTPOINT_LABEL": "",
                    "UNDERLAY_IS_V6": "false",
                    "UNDERLAY_IS_V6_PREV": "false",
                    "UNNUM_BOOTSTRAP_LB_ID": "",
                    "UNNUM_DHCP_END": "",
                    "UNNUM_DHCP_END_INTERNAL": "",
                    "UNNUM_DHCP_START": "",
                    "UNNUM_DHCP_START_INTERNAL": "",
                    "UPGRADE_FROM_VERSION": "",
                    "USE_LINK_LOCAL": "false",
                    "V6_SUBNET_RANGE": "",
                    "V6_SUBNET_TARGET_MASK": "126",
                    "VPC_AUTO_RECOVERY_TIME": "360",
                    "VPC_DELAY_RESTORE": "150",
                    "VPC_DELAY_RESTORE_TIME": "60",
                    "VPC_DOMAIN_ID_RANGE": "1-1000",
                    "VPC_ENABLE_IPv6_ND_SYNC": "true",
                    "VPC_PEER_KEEP_ALIVE_OPTION": "management",
                    "VPC_PEER_LINK_PO": "500",
                    "VPC_PEER_LINK_VLAN": "3600",
                    "VRF_LITE_AUTOCONFIG": "Back2Back&ToExternal",
                    "VRF_VLAN_RANGE": "2000-2299",
                    "abstract_anycast_rp": "anycast_rp",
                    "abstract_bgp": "base_bgp",
                    "abstract_bgp_neighbor": "evpn_bgp_rr_neighbor",
                    "abstract_bgp_rr": "evpn_bgp_rr",
                    "abstract_dhcp": "base_dhcp",
                    "abstract_extra_config_bootstrap": "extra_config_bootstrap_11_1",
                    "abstract_extra_config_leaf": "extra_config_leaf",
                    "abstract_extra_config_spine": "extra_config_spine",
                    "abstract_extra_config_tor": "extra_config_tor",
                    "abstract_feature_leaf": "base_feature_leaf_upg",
                    "abstract_feature_spine": "base_feature_spine_upg",
                    "abstract_isis": "base_isis_level2",
                    "abstract_isis_interface": "isis_interface",
                    "abstract_loopback_interface": "int_fabric_loopback_11_1",
                    "abstract_multicast": "base_multicast_11_1",
                    "abstract_ospf": "base_ospf",
                    "abstract_ospf_interface": "ospf_interface_11_1",
                    "abstract_pim_interface": "pim_interface",
                    "abstract_route_map": "route_map",
                    "abstract_routed_host": "int_routed_host",
                    "abstract_trunk_host": "int_trunk_host",
                    "abstract_vlan_interface": "int_fabric_vlan_11_1",
                    "abstract_vpc_domain": "base_vpc_domain_11_1",
                    "allowVlanOnLeafTorPairing": "none",
                    "default_network": "Default_Network_Universal",
                    "default_pvlan_sec_network": "",
                    "default_vrf": "Default_VRF_Universal",
                    "enableRealTimeBackup": "",
                    "enableScheduledBackup": "",
                    "network_extension_template": "Default_Network_Extension_Universal",
                    "preInterfaceConfigLeaf": "",
                    "preInterfaceConfigSpine": "",
                    "preInterfaceConfigTor": "",
                    "scheduledTime": "",
                    "temp_anycast_gateway": "anycast_gateway",
                    "temp_vpc_domain_mgmt": "vpc_domain_mgmt",
                    "temp_vpc_peer_link": "int_vpc_peer_link_po",
                    "vpcTorDelayRestoreTimer": "30",
                    "vrf_extension_template": "Default_VRF_Extension_Universal"
                }
            }
        ]
    }
]
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

import copy
import inspect
import logging

from ..common.api.onemanage.endpoints import EpOneManageFabricsGet
from ..common.conversion import ConversionUtils
from ..common.rest_send_v2 import RestSend
from ..common.results_v2 import Results


class FabricGroups:
    """
    # Summary

    Retrieve all fabric groups from the controller and set self.data
    with the response.

    Provide filtering based on fabric_group_name and property accessors for
    the filtered fabric group's attributes.

    ### Raises
    -   ``ValueError`` if:
            -   ``refresh()`` raises ``ValueError``.
            -   ``filter`` is not set before accessing properties.
            -   An attempt is made to access a key that does not exist
                for the filtered fabric.

    ### Usage

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import RestSend
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import Results
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_dcnm import Sender

    params = {"check_mode": False, "state": "merged"}
    sender = Sender()
    sender.ansible_module = ansible_module

    rest_send = RestSend(params)
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = FabricGroups()
    instance.rest_send = rest_send
    instance.results = Results()
    instance.refresh()
    instance.filter = "MyFabricGroup"
    # access individual fabric properties
    # TODO: Complete this section

    # all fabric details for "MyFabricGroup"
    fabric_group_dict = instance.filtered_data
    if fabric_group_dict is None:
        # fabric group MyFabricGroup does not exist on the controller
    # etc...
    ```

    Or:

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import RestSend
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import Results
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_dcnm import Sender

    params = {"check_mode": False, "state": "merged"}
    sender = Sender()
    sender.ansible_module = ansible_module

    rest_send = RestSend(params)
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = FabricGroups()
    instance.rest_send = rest_send
    instance.results = Results()
    instance.refresh()
    all_fabric_groups = instance.all_data
    ```

    Where ``all_fabric_groups`` will be a dictionary of all fabric groups on the
    controller, keyed on fabric group name.
    """

    def __init__(self) -> None:
        self.class_name: str = self.__class__.__name__

        self.action: str = "fabric_groups"
        self.log: logging.Logger = logging.getLogger(f"dcnm.{self.class_name}")

        msg = f"ENTERED {self.class_name}"
        self.log.debug(msg)

        self.data: dict = {}
        self.conversion: ConversionUtils = ConversionUtils()
        self.endpoint: EpOneManageFabricsGet = EpOneManageFabricsGet()

        self._fabric_group_names: list[str] = []
        self._filter: str = ""
        self._refreshed: bool = False
        self._rest_send: RestSend = None  # type: ignore[assignment]
        self._results: Results = None  # type: ignore[assignment]

    def register_result(self) -> None:
        """
        ### Summary
        Update the results object with the current state of the fabric
        details and register the result.

        ### Raises
        -   ``ValueError``if:
                -    ``Results()`` raises ``TypeError``
        """
        method_name = inspect.stack()[0][3]
        try:
            self.results.action = self.action
            self.results.response_current = self.rest_send.response_current
            self.results.result_current = self.rest_send.result_current
            if self.results.response_current.get("RETURN_CODE") == 200:
                self.results.failed = False
            else:
                self.results.failed = True
            # FabricDetails never changes the controller state
            self.results.changed = False
            self.results.register_task_result()
        except TypeError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Failed to register result. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

    def validate_refresh_parameters(self) -> None:
        """
        ### Summary
        Validate that mandatory parameters are set before calling refresh().

        ### Raises
        -   ``ValueError``if:
                -   ``rest_send`` is not set.
                -   ``results`` is not set.
        """

    def refresh(self) -> None:
        """
        # Summary

        Refresh fabric groups information from the controller.

        ## Raises

        -   `ValueError` if:
                -   Mandatory properties are not set.
                -   `validate_refresh_parameters()` raises `ValueError`.
                -   `RestSend` raises `TypeError` or `ValueError`.
                -   `register_result()` raises `ValueError`.

        ## Notes

        -   `self.data` is a dictionary of fabric details, keyed on
            fabric group name.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        try:
            self.validate_refresh_parameters()
        except ValueError as error:
            msg = "Failed to refresh fabric details: "
            msg += f"Error detail: {error}."
            raise ValueError(msg) from error

        try:
            self.rest_send.path = self.endpoint.path
            self.rest_send.verb = self.endpoint.verb

            # We always want to get the controller's current fabric state,
            # regardless of the current value of check_mode.
            # We save the current check_mode and timeout settings, set
            # rest_send.check_mode to False so the request will be sent
            # to the controller, and then restore the original settings.

            self.rest_send.save_settings()
            self.rest_send.check_mode = False
            self.rest_send.timeout = 1
            self.rest_send.commit()
            self.rest_send.restore_settings()
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error

        self.data = {}
        if self.rest_send is None:
            # We should never hit this.
            return
        if self.rest_send.response_current is None:
            # We should never hit this.
            return
        if self.rest_send.response_current["DATA"] is None:
            # The DATA key should always be present. We should never hit this.
            return
        for item in self.rest_send.response_current["DATA"]:
            fabric_name = item.get("nvPairs", {}).get("FABRIC_NAME", None)
            if fabric_name is None:
                return
            self.data[fabric_name] = item

        try:
            self.register_result()
        except ValueError as error:
            raise ValueError(error) from error

        self.data = copy.deepcopy(self.data)
        self._refreshed = True

        self._fabric_group_names = list(self.data.keys())

    def _get(self, item):
        """
        Retrieve the value of the top-level (non-nvPair) item for fabric_name
        (anything not in the nvPairs dictionary).

        -   raise ``ValueError`` if ``self.filter`` has not been set.
        -   raise ``ValueError`` if ``self.filter`` (fabric_name) does not exist
            on the controller.
        -   raise ``ValueError`` if item is not a valid property name for the fabric.

        See also: ``_get_nv_pair()``
        """
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"instance.filter {self.filter} "
        self.log.debug(msg)

        if not self.filter:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.filter to a fabric name "
            msg += f"before accessing property {item}."
            raise ValueError(msg)

        if self.data.get(self.filter) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"fabric_name {self.filter} does not exist on the controller."
            raise ValueError(msg)

        if self.data[self.filter].get(item) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} unknown property name: {item}."
            raise ValueError(msg)

        return self.conversion.make_none(self.conversion.make_boolean(self.data[self.filter].get(item)))

    def _get_nv_pair(self, item):
        """
        ### Summary
        Retrieve the value of the nvPair item for fabric_name.

        ### Raises
        - ``ValueError`` if:
                -   ``self.filter`` has not been set.
                -   ``self.filter`` (fabric_name) does not exist on the controller.
                -   ``item`` is not a valid property name for the fabric.

        ### See also
        ``self._get()``
        """
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"instance.filter {self.filter} "
        self.log.debug(msg)

        if not self.filter:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.filter to a fabric name "
            msg += f"before accessing property {item}."
            raise ValueError(msg)

        if not self.data.get(self.filter):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"fabric_name {self.filter} "
            msg += "does not exist on the controller."
            raise ValueError(msg)

        if self.data[self.filter].get("nvPairs", {}).get(item) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"fabric_name {self.filter} "
            msg += f"unknown property name: {item}."
            raise ValueError(msg)

        return self.conversion.make_none(self.conversion.make_boolean(self.data[self.filter].get("nvPairs").get(item)))

    @property
    def all_data(self) -> dict:
        """
        ### Summary
        Return all fabric details from the controller (i.e. self.data)

        ``refresh`` must be called before accessing this property.

        ### Raises
        None
        """
        return self.data

    @property
    def asn(self) -> str:
        """
        ### Summary
        Return the BGP asn of the fabric specified with filter, if it exists.
        Return "" (empty string) otherwise.

        This is an alias of bgp_as.

        ### Raises
        None

        ### Type
        string

        ### Returns
            - e.g. "65000"
            - "" (empty string) if BGP_AS is not set
        """
        try:
            return self._get_nv_pair("BGP_AS") or ""
        except ValueError as error:
            msg = f"Failed to retrieve asn: Error detail: {error}"
            self.log.debug(msg)
            return ""

    @property
    def bgp_as(self) -> str:
        """
        ### Summary
        Return ``nvPairs.BGP_AS`` of the fabric specified with filter, if it exists.
        Return "" (empty string) otherwise

        ### Raises
        None

        ### Type
        string

        ### Returns
            - e.g. "65000"
            - "" (empty string) if BGP_AS is not set
        """
        try:
            return self._get_nv_pair("BGP_AS") or ""
        except ValueError as error:
            msg = f"Failed to retrieve bgp_as: Error detail: {error}"
            self.log.debug(msg)
            return ""

    @property
    def deployment_freeze(self) -> bool:
        """
        ### Summary
        The nvPairs.DEPLOYMENT_FREEZE of the fabric specified with filter.

        ### Raises
        None

        ### Type
        boolean

        ### Returns
        - False (if set to False, or not set)
        - True
        """
        try:
            return self._get_nv_pair("DEPLOYMENT_FREEZE") or False
        except ValueError as error:
            msg = f"Failed to retrieve deployment_freeze: Error detail: {error}"
            self.log.debug(msg)
            return False

    @property
    def enable_pbr(self) -> bool:
        """
        ### Summary
        The PBR enable state of the fabric specified with filter.

        ### Raises
        None

        ### Type
        boolean

        ### Returns
        - False (if set to False, or not set)
        - True
        """
        try:
            return self._get_nv_pair("ENABLE_PBR") or False
        except ValueError as error:
            msg = f"Failed to retrieve enable_pbr: Error detail: {error}"
            self.log.debug(msg)
            return False

    @property
    def fabric_group_names(self) -> list:
        """
        ### Summary
        A list of all fabric group names on the controller.

        ### Raises
        None

        ### Type
        list

        ### Returns
        - e.g. ["FABRIC-1", "FABRIC-2", "FABRIC-3"]
        - [] (empty list) if no fabrics exist on the controller
        """
        method_name = inspect.stack()[0][3]
        if self.refreshed is False:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Call {self.class_name}.refresh() before accessing fabric_group_names."
            self.log.debug(msg)
            raise ValueError(msg)
        return self._fabric_group_names

    @property
    def fabric_id(self) -> str:
        """
        ### Summary
        The ``fabricId`` value of the fabric specified with filter.

        ### Raises
        None

        ### Type
        string

        ### Returns
        - e.g. FABRIC-5
        - "" if fabricId is not set
        """
        try:
            return self._get("fabricId") or ""
        except ValueError as error:
            msg = f"Failed to retrieve fabric_id: Error detail: {error}"
            self.log.debug(msg)
            return ""

    @property
    def fabric_type(self) -> str:
        """
        ### Summary
        The ``nvPairs.FABRIC_TYPE`` value of the fabric specified with filter.

        ### Raises
        None

        ### Type
        string

        ### Returns
        - e.g. Switch_Fabric
        - "" (empty string) if FABRIC_TYPE is not set
        """
        try:
            return self._get_nv_pair("FABRIC_TYPE") or ""
        except ValueError as error:
            msg = f"Failed to retrieve fabric_type: Error detail: {error}"
            self.log.debug(msg)
            return ""

    @property
    def is_read_only(self) -> bool:
        """
        ### Summary
        The ``nvPairs.IS_READ_ONLY`` value of the fabric specified with filter.

        ### Raises
        None

        ### Type
        boolean

        ### Returns
        - True
        - False (if set to False, or not set)
        """
        try:
            return self._get_nv_pair("IS_READ_ONLY") or False
        except ValueError as error:
            msg = f"Failed to retrieve is_read_only: Error detail: {error}"
            self.log.debug(msg)
            return False

    @property
    def per_vrf_loopback_auto_provision(self) -> bool:
        """
        ### Summary
        The ``nvPairs.PER_VRF_LOOPBACK_AUTO_PROVISION`` value of the fabric
        specified with filter.

        ### Raises
        None

        ### Type
        boolean

        ### Returns
        - True
        - False (if set to False, or not set)
        """
        try:
            return self._get_nv_pair("PER_VRF_LOOPBACK_AUTO_PROVISION") or False
        except ValueError as error:
            msg = "Failed to retrieve per_vrf_loopback_auto_provision: "
            msg += f"Error detail: {error}"
            self.log.debug(msg)
            return False

    @property
    def replication_mode(self) -> str:
        """
        ### Summary
        The ``nvPairs.REPLICATION_MODE`` value of the fabric specified
        with filter.

        ### Raises
        None

        ### Type
        string

        ### Returns
        - Ingress
        - Multicast
        - "" (empty string) if REPLICATION_MODE is not set
        """
        try:
            return self._get_nv_pair("REPLICATION_MODE") or ""
        except ValueError as error:
            msg = f"Failed to retrieve replication_mode: Error detail: {error}"
            self.log.debug(msg)
            return ""

    @property
    def refreshed(self) -> bool:
        """
        Indicates whether the fabric details have been refreshed.
        """
        return self._refreshed

    @property
    def template_name(self) -> str:
        """
        ### Summary
        The ``templateName`` value of the fabric specified
        with filter.

        ### Raises
        None

        ### Type
        string

        ### Returns
        - e.g. Easy_Fabric
        - Empty string, if templateName is not set
        """
        try:
            return self._get("templateName") or ""
        except ValueError as error:
            msg = f"Failed to retrieve template_name: Error detail: {error}"
            self.log.debug(msg)
            return ""

    @property
    def filtered_data(self) -> dict:
        """
        ### Summary
        The DATA portion of the dictionary for the fabric specified with filter.

        ### Raises
        -   ``ValueError`` if:
                -   ``self.filter`` has not been set.

        ### Returns
        - A dictionary of the fabric matching self.filter.
        - Empty dictionary, if the fabric does not exist on the controller.
        """
        method_name = inspect.stack()[0][3]
        if not self.filter:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.filter must be set before accessing "
            msg += f"{self.class_name}.filtered_data."
            raise ValueError(msg)
        return self.data.get(self.filter, {})

    @property
    def filter(self) -> str:
        """
        # Summary

        Set the fabric_name of the fabric to query.

        ## Raises

        None

        ## NOTES

        `filter` must be set before accessing this class's properties.
        """
        return self._filter

    @filter.setter
    def filter(self, value: str) -> None:
        self._filter = value

    @property
    def rest_send(self) -> RestSend:
        """
        An instance of the RestSend class.
        """
        method_name = inspect.stack()[0][3]
        if self._rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send property has not been set."
            self.log.debug(msg)
            raise ValueError(msg)
        return self._rest_send

    @rest_send.setter
    def rest_send(self, value: RestSend) -> None:
        self._rest_send = value

    @property
    def results(self) -> Results:
        """
        An instance of the Results class.
        """
        method_name = inspect.stack()[0][3]
        if self._results is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "results property has not been set."
            self.log.debug(msg)
            raise ValueError(msg)
        return self._results

    @results.setter
    def results(self, value: Results) -> None:
        self._results = value
