import json
import logging


class FabricDefaults:
    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self._default_nv_pairs = {}
        self._build_properties()

    def _build_properties(self):
        self.properties = {}
        self.properties["template"] = None
        self.properties["defaults"] = {}

    @property
    def template(self):
        return self.properties["template"]

    @template.setter
    def template(self, value):
        self.properties["template"] = value

    def refresh(self):
        """
        Refresh the defaults based on the template
        """
        if self.template is None:
            msg = "Call instance.template before calling instance.refresh()."
            raise ValueError(msg)
        if self.template.get("parameters") is None:
            msg = "No parameters in template."
            raise ValueError(msg)
        if isinstance(self.template["parameters"], list) is False:
            msg = "template[parameters] is not a list."
            raise ValueError(msg)

        self._build_default_nv_pairs()
        # self._build_default_fabric_params()

    def parameter(self, value):
        try:
            return self._default_nv_pairs[value]
        except KeyError:
            raise KeyError(f"Parameter {value} not found in default NvPairs")

    @staticmethod
    def make_boolean(value):
        if value in ("true", "True", True):
            return True
        if value in ("false", "False", False):
            return False
        return value

    def _build_default_nv_pairs(self):
        """
        Caller: __init__()

        Build a dict() of default fabric nvPairs that will be sent to NDFC.
        The values for these items are what NDFC currently (as of 12.1.2e)
        uses for defaults.  Items that are supported by this module may be
        modified by the user's playbook.
        """
        self._default_nv_pairs = {}
        for parameter in self.template.get("parameters", []):
            key = parameter["name"]
            value = parameter.get("metaProperties", {}).get("defaultValue", None)
            self._default_nv_pairs[key] = self.make_boolean(value)

        msg = f"self._default_nv_pairs: {json.dumps(self._default_nv_pairs, indent=4, sort_keys=True)}"
        msg = f"self._default_nv_pairs: {self._default_nv_pairs}"
        self.log.debug(msg)

    def vxlan_evpn_nv_pairs(self):
        self._default_nv_pairs = {}
        self._default_nv_pairs["AAA_REMOTE_IP_ENABLED"] = False
        self._default_nv_pairs["AAA_SERVER_CONF"] = ""
        self._default_nv_pairs["ACTIVE_MIGRATION"] = False
        self._default_nv_pairs["ADVERTISE_PIP_BGP"] = False
        self._default_nv_pairs["AGENT_INTF"] = "eth0"
        self._default_nv_pairs["ANYCAST_BGW_ADVERTISE_PIP"] = False
        self._default_nv_pairs["ANYCAST_GW_MAC"] = "2020.0000.00aa"
        self._default_nv_pairs["ANYCAST_LB_ID"] = ""
        # self._default_nv_pairs["ANYCAST_RP_IP_RANGE"] = "10.254.254.0/24"
        # self._default_nv_pairs["ANYCAST_RP_IP_RANGE"] = ""
        # self._default_nv_pairs["ANYCAST_RP_IP_RANGE_INTERNAL"] = ""
        self._default_nv_pairs["AUTO_SYMMETRIC_DEFAULT_VRF"] = False
        self._default_nv_pairs["AUTO_SYMMETRIC_VRF_LITE"] = False
        self._default_nv_pairs["AUTO_VRFLITE_IFC_DEFAULT_VRF"] = False
        self._default_nv_pairs["BFD_AUTH_ENABLE"] = False
        self._default_nv_pairs["BFD_AUTH_KEY"] = ""
        self._default_nv_pairs["BFD_AUTH_KEY_ID"] = ""
        self._default_nv_pairs["BFD_ENABLE"] = False
        self._default_nv_pairs["BFD_IBGP_ENABLE"] = False
        self._default_nv_pairs["BFD_ISIS_ENABLE"] = False
        self._default_nv_pairs["BFD_OSPF_ENABLE"] = False
        self._default_nv_pairs["BFD_PIM_ENABLE"] = False
        self._default_nv_pairs["BGP_AS"] = "1"
        self._default_nv_pairs["BGP_AS_PREV"] = ""
        self._default_nv_pairs["BGP_AUTH_ENABLE"] = False
        self._default_nv_pairs["BGP_AUTH_KEY"] = ""
        self._default_nv_pairs["BGP_AUTH_KEY_TYPE"] = ""
        self._default_nv_pairs["BGP_LB_ID"] = "0"
        self._default_nv_pairs["BOOTSTRAP_CONF"] = ""
        self._default_nv_pairs["BOOTSTRAP_ENABLE"] = False
        self._default_nv_pairs["BOOTSTRAP_ENABLE_PREV"] = False
        self._default_nv_pairs["BOOTSTRAP_MULTISUBNET"] = ""
        self._default_nv_pairs["BOOTSTRAP_MULTISUBNET_INTERNAL"] = ""
        self._default_nv_pairs["BRFIELD_DEBUG_FLAG"] = "Disable"
        self._default_nv_pairs["BROWNFIELD_NETWORK_NAME_FORMAT"] = (
            "Auto_Net_VNI$$VNI$$_VLAN$$VLAN_ID$$"
        )
        key = "BROWNFIELD_SKIP_OVERLAY_NETWORK_ATTACHMENTS"
        self._default_nv_pairs[key] = False
        self._default_nv_pairs["CDP_ENABLE"] = False
        self._default_nv_pairs["COPP_POLICY"] = "strict"
        self._default_nv_pairs["DCI_SUBNET_RANGE"] = "10.33.0.0/16"
        self._default_nv_pairs["DCI_SUBNET_TARGET_MASK"] = "30"
        self._default_nv_pairs["DEAFULT_QUEUING_POLICY_CLOUDSCALE"] = ""
        self._default_nv_pairs["DEAFULT_QUEUING_POLICY_OTHER"] = ""
        self._default_nv_pairs["DEAFULT_QUEUING_POLICY_R_SERIES"] = ""
        self._default_nv_pairs["DEFAULT_VRF_REDIS_BGP_RMAP"] = ""
        self._default_nv_pairs["DEPLOYMENT_FREEZE"] = False
        self._default_nv_pairs["DHCP_ENABLE"] = False
        self._default_nv_pairs["DHCP_END"] = ""
        self._default_nv_pairs["DHCP_END_INTERNAL"] = ""
        self._default_nv_pairs["DHCP_IPV6_ENABLE"] = ""
        self._default_nv_pairs["DHCP_IPV6_ENABLE_INTERNAL"] = ""
        self._default_nv_pairs["DHCP_START"] = ""
        self._default_nv_pairs["DHCP_START_INTERNAL"] = ""
        self._default_nv_pairs["DNS_SERVER_IP_LIST"] = ""
        self._default_nv_pairs["DNS_SERVER_VRF"] = ""
        self._default_nv_pairs["ENABLE_AAA"] = False
        self._default_nv_pairs["ENABLE_AGENT"] = False
        self._default_nv_pairs["ENABLE_DEFAULT_QUEUING_POLICY"] = False
        self._default_nv_pairs["ENABLE_EVPN"] = True
        self._default_nv_pairs["ENABLE_FABRIC_VPC_DOMAIN_ID"] = False
        self._default_nv_pairs["ENABLE_FABRIC_VPC_DOMAIN_ID_PREV"] = ""
        self._default_nv_pairs["ENABLE_MACSEC"] = False
        self._default_nv_pairs["ENABLE_NETFLOW"] = False
        self._default_nv_pairs["ENABLE_NETFLOW_PREV"] = ""
        self._default_nv_pairs["ENABLE_NGOAM"] = True
        self._default_nv_pairs["ENABLE_NXAPI"] = True
        self._default_nv_pairs["ENABLE_NXAPI_HTTP"] = True
        self._default_nv_pairs["ENABLE_PBR"] = False
        self._default_nv_pairs["ENABLE_PVLAN"] = False
        self._default_nv_pairs["ENABLE_PVLAN_PREV"] = False
        self._default_nv_pairs["ENABLE_TENANT_DHCP"] = True
        self._default_nv_pairs["ENABLE_TRM"] = False
        self._default_nv_pairs["ENABLE_VPC_PEER_LINK_NATIVE_VLAN"] = False
        self._default_nv_pairs["EXTRA_CONF_INTRA_LINKS"] = ""
        self._default_nv_pairs["EXTRA_CONF_LEAF"] = ""
        self._default_nv_pairs["EXTRA_CONF_SPINE"] = ""
        self._default_nv_pairs["EXTRA_CONF_TOR"] = ""
        self._default_nv_pairs["FABRIC_INTERFACE_TYPE"] = "p2p"
        self._default_nv_pairs["FABRIC_MTU"] = "9216"
        self._default_nv_pairs["FABRIC_MTU_PREV"] = "9216"
        self._default_nv_pairs["FABRIC_NAME"] = "easy-fabric"
        self._default_nv_pairs["FABRIC_TYPE"] = "Switch_Fabric"
        self._default_nv_pairs["FABRIC_VPC_DOMAIN_ID"] = ""
        self._default_nv_pairs["FABRIC_VPC_DOMAIN_ID_PREV"] = ""
        self._default_nv_pairs["FABRIC_VPC_QOS"] = False
        self._default_nv_pairs["FABRIC_VPC_QOS_POLICY_NAME"] = ""
        self._default_nv_pairs["FEATURE_PTP"] = False
        self._default_nv_pairs["FEATURE_PTP_INTERNAL"] = False
        self._default_nv_pairs["FF"] = "Easy_Fabric"
        self._default_nv_pairs["GRFIELD_DEBUG_FLAG"] = "Disable"
        self._default_nv_pairs["HD_TIME"] = "180"
        self._default_nv_pairs["HOST_INTF_ADMIN_STATE"] = True
        self._default_nv_pairs["IBGP_PEER_TEMPLATE"] = ""
        self._default_nv_pairs["IBGP_PEER_TEMPLATE_LEAF"] = ""
        self._default_nv_pairs["INBAND_DHCP_SERVERS"] = ""
        self._default_nv_pairs["INBAND_MGMT"] = False
        self._default_nv_pairs["INBAND_MGMT_PREV"] = False
        self._default_nv_pairs["ISIS_AUTH_ENABLE"] = False
        self._default_nv_pairs["ISIS_AUTH_KEY"] = ""
        self._default_nv_pairs["ISIS_AUTH_KEYCHAIN_KEY_ID"] = ""
        self._default_nv_pairs["ISIS_AUTH_KEYCHAIN_NAME"] = ""
        self._default_nv_pairs["ISIS_LEVEL"] = ""
        self._default_nv_pairs["ISIS_OVERLOAD_ELAPSE_TIME"] = ""
        self._default_nv_pairs["ISIS_OVERLOAD_ENABLE"] = ""
        # self._default_nv_pairs["ISIS_P2P_ENABLE"] = False
        self._default_nv_pairs["ISIS_P2P_ENABLE"] = ""
        self._default_nv_pairs["L2_HOST_INTF_MTU"] = "9216"
        self._default_nv_pairs["L2_HOST_INTF_MTU_PREV"] = "9216"
        self._default_nv_pairs["L2_SEGMENT_ID_RANGE"] = "30000-49000"
        self._default_nv_pairs["L3VNI_MCAST_GROUP"] = ""
        self._default_nv_pairs["L3_PARTITION_ID_RANGE"] = "50000-59000"
        self._default_nv_pairs["LINK_STATE_ROUTING"] = "ospf"
        self._default_nv_pairs["LINK_STATE_ROUTING_TAG"] = "UNDERLAY"
        self._default_nv_pairs["LINK_STATE_ROUTING_TAG_PREV"] = ""
        self._default_nv_pairs["LOOPBACK0_IPV6_RANGE"] = ""
        self._default_nv_pairs["LOOPBACK0_IP_RANGE"] = "10.2.0.0/22"
        self._default_nv_pairs["LOOPBACK1_IPV6_RANGE"] = ""
        self._default_nv_pairs["LOOPBACK1_IP_RANGE"] = "10.3.0.0/22"
        self._default_nv_pairs["MACSEC_ALGORITHM"] = ""
        self._default_nv_pairs["MACSEC_CIPHER_SUITE"] = ""
        self._default_nv_pairs["MACSEC_FALLBACK_ALGORITHM"] = ""
        self._default_nv_pairs["MACSEC_FALLBACK_KEY_STRING"] = ""
        self._default_nv_pairs["MACSEC_KEY_STRING"] = ""
        self._default_nv_pairs["MACSEC_REPORT_TIMER"] = ""
        self._default_nv_pairs["MGMT_GW"] = ""
        self._default_nv_pairs["MGMT_GW_INTERNAL"] = ""
        self._default_nv_pairs["MGMT_PREFIX"] = ""
        self._default_nv_pairs["MGMT_PREFIX_INTERNAL"] = ""
        self._default_nv_pairs["MGMT_V6PREFIX"] = "64"
        self._default_nv_pairs["MGMT_V6PREFIX_INTERNAL"] = ""
        self._default_nv_pairs["MPLS_HANDOFF"] = False
        self._default_nv_pairs["MPLS_LB_ID"] = ""
        self._default_nv_pairs["MPLS_LOOPBACK_IP_RANGE"] = ""
        self._default_nv_pairs["MSO_CONNECTIVITY_DEPLOYED"] = ""
        self._default_nv_pairs["MSO_CONTROLER_ID"] = ""
        self._default_nv_pairs["MSO_SITE_GROUP_NAME"] = ""
        self._default_nv_pairs["MSO_SITE_ID"] = ""
        self._default_nv_pairs["MST_INSTANCE_RANGE"] = ""
        self._default_nv_pairs["MULTICAST_GROUP_SUBNET"] = "239.1.1.0/25"
        self._default_nv_pairs["NETFLOW_EXPORTER_LIST"] = ""
        self._default_nv_pairs["NETFLOW_MONITOR_LIST"] = ""
        self._default_nv_pairs["NETFLOW_RECORD_LIST"] = ""
        self._default_nv_pairs["NETWORK_VLAN_RANGE"] = "2300-2999"
        self._default_nv_pairs["NTP_SERVER_IP_LIST"] = ""
        self._default_nv_pairs["NTP_SERVER_VRF"] = ""
        self._default_nv_pairs["NVE_LB_ID"] = "1"
        self._default_nv_pairs["OSPF_AREA_ID"] = "0.0.0.0"
        self._default_nv_pairs["OSPF_AUTH_ENABLE"] = False
        self._default_nv_pairs["OSPF_AUTH_KEY"] = ""
        self._default_nv_pairs["OSPF_AUTH_KEY_ID"] = ""
        self._default_nv_pairs["OVERLAY_MODE"] = "config-profile"
        self._default_nv_pairs["OVERLAY_MODE_PREV"] = ""
        self._default_nv_pairs["PHANTOM_RP_LB_ID1"] = ""
        self._default_nv_pairs["PHANTOM_RP_LB_ID2"] = ""
        self._default_nv_pairs["PHANTOM_RP_LB_ID3"] = ""
        self._default_nv_pairs["PHANTOM_RP_LB_ID4"] = ""
        self._default_nv_pairs["PIM_HELLO_AUTH_ENABLE"] = False
        self._default_nv_pairs["PIM_HELLO_AUTH_KEY"] = ""
        self._default_nv_pairs["PM_ENABLE"] = False
        self._default_nv_pairs["PM_ENABLE_PREV"] = False
        self._default_nv_pairs["POWER_REDUNDANCY_MODE"] = "ps-redundant"
        self._default_nv_pairs["PREMSO_PARENT_FABRIC"] = ""
        self._default_nv_pairs["PTP_DOMAIN_ID"] = ""
        self._default_nv_pairs["PTP_LB_ID"] = ""
        self._default_nv_pairs["REPLICATION_MODE"] = "Multicast"
        self._default_nv_pairs["ROUTER_ID_RANGE"] = ""
        self._default_nv_pairs["ROUTE_MAP_SEQUENCE_NUMBER_RANGE"] = "1-65534"
        self._default_nv_pairs["RP_COUNT"] = "2"
        self._default_nv_pairs["RP_LB_ID"] = "254"
        self._default_nv_pairs["RP_MODE"] = "asm"
        self._default_nv_pairs["RR_COUNT"] = "2"
        self._default_nv_pairs["SEED_SWITCH_CORE_INTERFACES"] = ""
        self._default_nv_pairs["SERVICE_NETWORK_VLAN_RANGE"] = "3000-3199"
        self._default_nv_pairs["SITE_ID"] = ""
        self._default_nv_pairs["SNMP_SERVER_HOST_TRAP"] = True
        self._default_nv_pairs["SPINE_COUNT"] = "0"
        self._default_nv_pairs["SPINE_SWITCH_CORE_INTERFACES"] = ""
        self._default_nv_pairs["SSPINE_ADD_DEL_DEBUG_FLAG"] = "Disable"
        self._default_nv_pairs["SSPINE_COUNT"] = "0"
        self._default_nv_pairs["STATIC_UNDERLAY_IP_ALLOC"] = False
        self._default_nv_pairs["STP_BRIDGE_PRIORITY"] = ""
        self._default_nv_pairs["STP_ROOT_OPTION"] = "unmanaged"
        self._default_nv_pairs["STP_VLAN_RANGE"] = ""
        self._default_nv_pairs["STRICT_CC_MODE"] = False
        self._default_nv_pairs["SUBINTERFACE_RANGE"] = "2-511"
        self._default_nv_pairs["SUBNET_RANGE"] = "10.4.0.0/16"
        self._default_nv_pairs["SUBNET_TARGET_MASK"] = "30"
        self._default_nv_pairs["SYSLOG_SERVER_IP_LIST"] = ""
        self._default_nv_pairs["SYSLOG_SERVER_VRF"] = ""
        self._default_nv_pairs["SYSLOG_SEV"] = ""
        self._default_nv_pairs["TCAM_ALLOCATION"] = True
        self._default_nv_pairs["UNDERLAY_IS_V6"] = False
        self._default_nv_pairs["UNNUM_BOOTSTRAP_LB_ID"] = ""
        self._default_nv_pairs["UNNUM_DHCP_END"] = ""
        self._default_nv_pairs["UNNUM_DHCP_END_INTERNAL"] = ""
        self._default_nv_pairs["UNNUM_DHCP_START"] = ""
        self._default_nv_pairs["UNNUM_DHCP_START_INTERNAL"] = ""
        self._default_nv_pairs["USE_LINK_LOCAL"] = ""
        self._default_nv_pairs["V6_SUBNET_RANGE"] = ""
        self._default_nv_pairs["V6_SUBNET_TARGET_MASK"] = ""
        self._default_nv_pairs["VPC_AUTO_RECOVERY_TIME"] = "360"
        self._default_nv_pairs["VPC_DELAY_RESTORE"] = "150"
        self._default_nv_pairs["VPC_DELAY_RESTORE_TIME"] = "60"
        self._default_nv_pairs["VPC_DOMAIN_ID_RANGE"] = "1-1000"
        self._default_nv_pairs["VPC_ENABLE_IPv6_ND_SYNC"] = True
        self._default_nv_pairs["VPC_PEER_KEEP_ALIVE_OPTION"] = "management"
        self._default_nv_pairs["VPC_PEER_LINK_PO"] = "500"
        self._default_nv_pairs["VPC_PEER_LINK_VLAN"] = "3600"
        self._default_nv_pairs["VRF_LITE_AUTOCONFIG"] = "Manual"
        self._default_nv_pairs["VRF_VLAN_RANGE"] = "2000-2299"
        self._default_nv_pairs["abstract_anycast_rp"] = "anycast_rp"
        self._default_nv_pairs["abstract_bgp"] = "base_bgp"
        value = "evpn_bgp_rr_neighbor"
        self._default_nv_pairs["abstract_bgp_neighbor"] = value
        self._default_nv_pairs["abstract_bgp_rr"] = "evpn_bgp_rr"
        self._default_nv_pairs["abstract_dhcp"] = "base_dhcp"
        self._default_nv_pairs["abstract_extra_config_bootstrap"] = (
            "extra_config_bootstrap_11_1"
        )
        value = "extra_config_leaf"
        self._default_nv_pairs["abstract_extra_config_leaf"] = value
        value = "extra_config_spine"
        self._default_nv_pairs["abstract_extra_config_spine"] = value
        value = "extra_config_tor"
        self._default_nv_pairs["abstract_extra_config_tor"] = value
        value = "base_feature_leaf_upg"
        self._default_nv_pairs["abstract_feature_leaf"] = value
        value = "base_feature_spine_upg"
        self._default_nv_pairs["abstract_feature_spine"] = value
        self._default_nv_pairs["abstract_isis"] = "base_isis_level2"
        self._default_nv_pairs["abstract_isis_interface"] = "isis_interface"
        self._default_nv_pairs["abstract_loopback_interface"] = (
            "int_fabric_loopback_11_1"
        )
        self._default_nv_pairs["abstract_multicast"] = "base_multicast_11_1"
        self._default_nv_pairs["abstract_ospf"] = "base_ospf"
        value = "ospf_interface_11_1"
        self._default_nv_pairs["abstract_ospf_interface"] = value
        self._default_nv_pairs["abstract_pim_interface"] = "pim_interface"
        self._default_nv_pairs["abstract_route_map"] = "route_map"
        self._default_nv_pairs["abstract_routed_host"] = "int_routed_host"
        self._default_nv_pairs["abstract_trunk_host"] = "int_trunk_host"
        value = "int_fabric_vlan_11_1"
        self._default_nv_pairs["abstract_vlan_interface"] = value
        self._default_nv_pairs["abstract_vpc_domain"] = "base_vpc_domain_11_1"
        value = "Default_Network_Universal"
        self._default_nv_pairs["default_network"] = value
        self._default_nv_pairs["default_pvlan_sec_network"] = ""
        self._default_nv_pairs["default_vrf"] = "Default_VRF_Universal"
        self._default_nv_pairs["enableRealTimeBackup"] = ""
        self._default_nv_pairs["enableScheduledBackup"] = ""
        self._default_nv_pairs["network_extension_template"] = (
            "Default_Network_Extension_Universal"
        )
        self._default_nv_pairs["scheduledTime"] = ""
        self._default_nv_pairs["temp_anycast_gateway"] = "anycast_gateway"
        self._default_nv_pairs["temp_vpc_domain_mgmt"] = "vpc_domain_mgmt"
        self._default_nv_pairs["temp_vpc_peer_link"] = "int_vpc_peer_link_po"
        self._default_nv_pairs["vrf_extension_template"] = (
            "Default_VRF_Extension_Universal"
        )

    def _build_default_fabric_params(self):
        """
        Caller: __init__()

        Initialize default NDFC top-level parameters
        See also: self._build_default_nv_pairs()
        """
        # TODO:3 We may need translation methods for these as well. See the
        #   method for nvPair transation: _translate_to_ndfc_nv_pairs
        self._default_fabric_params = {}
        self._default_fabric_params["deviceType"] = "n9k"
        self._default_fabric_params["fabricTechnology"] = "VXLANFabric"
        self._default_fabric_params["fabricTechnologyFriendly"] = "VXLAN Fabric"
        self._default_fabric_params["fabricType"] = "Switch_Fabric"
        self._default_fabric_params["fabricTypeFriendly"] = "Switch Fabric"
        self._default_fabric_params["networkExtensionTemplate"] = (
            "Default_Network_Extension_Universal"
        )
        value = "Default_Network_Universal"
        self._default_fabric_params["networkTemplate"] = value
        self._default_fabric_params["provisionMode"] = "DCNMTopDown"
        self._default_fabric_params["replicationMode"] = "Multicast"
        self._default_fabric_params["siteId"] = ""
        self._default_fabric_params["templateName"] = "Easy_Fabric"
        self._default_fabric_params["vrfExtensionTemplate"] = (
            "Default_VRF_Extension_Universal"
        )
        self._default_fabric_params["vrfTemplate"] = "Default_VRF_Universal"
