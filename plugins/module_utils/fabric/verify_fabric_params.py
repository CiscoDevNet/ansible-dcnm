#!/usr/bin/python
#
# Copyright (c) 2023-2023 Cisco and/or its affiliates.
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
"""
Classes and methods to verify NDFC Data Center VXLAN EVPN Fabric parameters.
This should go in:
ansible_collections/cisco/dcnm/plugins/module_utils/fabric/vxlan/verify_fabric_params.py

Example Usage:
import sys
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.verify_fabric_params import \
    VerifyFabricParams

config = {}
config["fabric_name"] = "foo"
config["bgp_as"] = "65000.869"
# If auto_symmetric_vrf_lite == True, several other parameters
# become mandatory. The user has not explicitely set these other
# parameters.  Hence, verify.result would be False (i.e. an error)
# If auto_symmetric_vrf_lite ==  False, no other parameters are required
# and so verify.result would be True and verify.payload would contain
# a valid payload to send to NDFC
config["auto_symmetric_vrf_lite"] = False
verify = VerifyFabricParams()
verify.config = config
verify.state = "merged"
verify.validate_config()
if verify.result == False:
    print(f"result {verify.result}, {verify.msg}")
    sys.exit(1)
print(f"result {verify.result}, {verify.msg}, payload {verify.payload}")
"""
import copy
import inspect
import logging
import re


def translate_mac_address(mac_addr):
    """
    Accept mac address with any (or no) punctuation and convert it
    into the dotted-quad format that NDFC expects.

    Return mac address formatted for NDFC on success
    Return False on failure.
    """
    mac_addr = re.sub(r"[\W\s_]", "", mac_addr)
    if not re.search("^[A-Fa-f0-9]{12}$", mac_addr):
        return False
    return "".join((mac_addr[:4], ".", mac_addr[4:8], ".", mac_addr[8:]))


def translate_vrf_lite_autoconfig(value):
    """
    Translate playbook values to those expected by NDFC
    """
    try:
        value = int(value)
    except ValueError:
        return False
    if value == 0:
        return "Manual"
    if value == 1:
        return "Back2Back&ToExternal"
    return False


class VerifyFabricParams:
    """
    Parameter validation for NDFC Data Center VXLAN EVPN
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self._initialize_properties()

        self.msg = None
        self.payload = {}
        self._default_fabric_params = {}
        self._default_nv_pairs = {}
        # See self._build_parameter_aliases
        self._parameter_aliases = {}
        # See self._build_mandatory_params()
        self._mandatory_params = {}
        # See self._validate_dependencies()
        self._requires_validation = set()
        # See self._build_failed_dependencies()
        self._failed_dependencies = {}
        # nvPairs that are safe to translate from lowercase dunder
        # (as used in the playbook) to uppercase dunder (as used
        # in the NDFC payload).
        self._translatable_nv_pairs = set()
        # A dictionary that holds the set of nvPairs that have been
        # translated for use in the NDFC payload.  These include only
        # parameters that the user has changed.  Keyed on the NDFC-expected
        # parameter name, value is the user's setting for the parameter.
        # Populated in:
        #  self._translate_to_ndfc_nv_pairs()
        #  self._build_translatable_nv_pairs()
        self._translated_nv_pairs = {}
        self._valid_states = {"merged"}
        self._mandatory_keys = {"FABRIC_NAME", "BGP_AS"}
        self._build_default_fabric_params()
        self._build_default_nv_pairs()

    def _initialize_properties(self):
        self.properties = {}
        self.properties["msg"] = None
        self.properties["result"] = True
        self.properties["state"] = None
        self.properties["config"] = {}

    def _append_msg(self, msg):
        if self.msg is None:
            self.msg = msg
        else:
            self.msg += f" {msg}"

    def _validate_config(self, config):
        """
        verify that self.config is a dict and that it contains
        the minimal set of mandatory keys.

        Caller: self.config (@property setter)

        On success:
            return True
        On failure:
            set self.result to False
            set self.msg to an approprate error message
            return False
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        if not isinstance(config, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "expected a dict for config. "
            msg += f"Got {type(config)}."
            self.result = False
            self._append_msg(msg)
            return False
        if not self._mandatory_keys.issubset(config):
            missing_keys = self._mandatory_keys.difference(config.keys())
            msg = f"{self.class_name}.{method_name}: "
            msg += f"missing mandatory keys {','.join(sorted(missing_keys))}."
            self.result = False
            self._append_msg(msg)
            return False
        return True

    def validate_config(self):
        """
        Caller: public method, called by the user
        Validate the items in self.config are appropriate for self.state
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.state: {self.state}"
        self.log.debug(msg)

        if self.state is None:
            msg = "call instance.state before calling instance.validate_config"
            self._append_msg(msg)
            self.result = False
            return
        if self.state == "merged":
            self._validate_merged_state_config()

    def _validate_merged_state_config(self):
        """
        Caller: self.validate_config()

        Update self.config with a verified version of the users playbook
        parameters.


        Verify the user's playbook parameters for an individual fabric
        configuration.  Whenever possible, throw the user a bone by
        converting values to NDFC's expectations. For example, NDFC's
        REST API accepts mac addresses in any format (does not return
        an error), since the NDFC GUI validates that it is in the expected
        format, but the fabric will be in an errored state if the mac address
        sent via REST is any format other than dotted-quad format
        (xxxx.xxxx.xxxx). So, we convert all mac address formats to
        dotted-quad before passing them to NDFC.

        Set self.result to False and update self.msg if anything is not valid
        that we couldn't fix
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += "ENTERED"
        if not self.config:
            msg = "config: element is mandatory for state merged"
            self._append_msg(msg)
            self.result = False
            return
        if "FABRIC_NAME" not in self.config:
            msg = "FABRIC_NAME is mandatory"
            self._append_msg(msg)
            self.result = False
            return
        if "BGP_AS" not in self.config:
            msg = "BGP_AS is mandatory"
            self._append_msg(msg)
            self.result = False
            return
        if "ANYCAST_GW_MAC" in self.config:
            result = translate_mac_address(self.config["ANYCAST_GW_MAC"])
            if result is False:
                msg = f"invalid ANYCAST_GW_MAC {self.config['ANYCAST_GW_MAC']}"
                self._append_msg(msg)
                self.result = False
                return
            self.config["ANYCAST_GW_MAC"] = result

        if "VRF_LITE_AUTOCONFIG" in self.config:
            result = translate_vrf_lite_autoconfig(self.config["VRF_LITE_AUTOCONFIG"])
            if result is False:
                msg = "invalid VRF_LITE_AUTOCONFIG "
                msg += f"{self.config['VRF_LITE_AUTOCONFIG']}. Expected one of 0,1"
                self._append_msg(msg)
                self.result = False
                return
            self.config["VRF_LITE_AUTOCONFIG"] = result

        msg = f"{self.class_name}.{method_name}: "
        msg += "Calling self._validate_dependencies()"
        self.log.debug(msg)
        self._validate_dependencies()

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.result: {self.result}"
        self.log.debug(msg)

        if self.result is False:
            return

        msg = f"{self.class_name}.{method_name}: "
        msg += "Calling self._build_payload()"
        self.log.debug(msg)
        self._build_payload()

    def _build_default_nv_pairs(self):
        """
        Caller: __init__()

        Build a dict() of default fabric nvPairs that will be sent to NDFC.
        The values for these items are what NDFC currently (as of 12.1.2e)
        uses for defaults.  Items that are supported by this module may be
        modified by the user's playbook.
        """
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

    def _build_translatable_nv_pairs(self):
        """
        Caller: _translate_to_ndfc_nv_pairs()

        All parameters in the playbook are lowercase dunder, while
        NDFC nvPairs contains a mish-mash of styles, for example:
        - enableScheduledBackup
        - default_vrf
        - REPLICATION_MODE

        This method builds a set of playbook parameters that conform to the
        most common case (uppercase dunder e.g. REPLICATION_MODE) and so
        can safely be translated to uppercase dunder style that NDFC expects
        in the payload.

        See also: self._translate_to_ndfc_nv_pairs, where the actual
        translation happens.
        """
        # self._default_nv_pairs is already built via create_fabric()
        # Given we have a specific controlled input, we can use a more
        # relaxed regex here.  We just want to exclude camelCase e.g.
        # "thisThing", lowercase dunder e.g. "this_thing", and lowercase
        # e.g. "thisthing".
        re_uppercase_dunder = "^[A-Z0-9_]+$"
        self._translatable_nv_pairs = set()
        for param in self._default_nv_pairs:
            if re.search(re_uppercase_dunder, param):
                self._translatable_nv_pairs.add(param.lower())

    def _translate_to_ndfc_nv_pairs(self, params):
        self._translated_nv_pairs = copy.deepcopy(params)

    # def _translate_to_ndfc_nv_pairs_orig(self, params):
    #     """
    #     Caller: self._build_payload()

    #     translate keys in params dict into what NDFC
    #     expects in nvPairs and populate dict
    #     self._translated_nv_pairs

    #     """
    #     self._build_translatable_nv_pairs()
    #     # TODO:4 We currently don't handle non-dunder uppercase and lowercase,
    #     #   e.g. THIS or that.  But (knock on wood), so far there are no
    #     #   cases like this (or THAT).
    #     self._translated_nv_pairs = {}
    #     # upper-case dunder keys
    #     for param in self._translatable_nv_pairs:
    #         if param not in params:
    #             continue
    #         self._translated_nv_pairs[param.upper()] = params[param]
    #     # special cases
    #     # dunder keys, these need no modification
    #     dunder_keys = {
    #         "default_network",
    #         "default_vrf",
    #         "network_extension_template",
    #         "vrf_extension_template",
    #     }
    #     for key in dunder_keys:
    #         if key not in params:
    #             continue
    #         self._translated_nv_pairs[key] = params[key]
    #     # camelCase keys
    #     # These are currently manually mapped with a dictionary.
    #     camel_keys = {
    #         "enableRealTimeBackup": "enable_real_time_backup",
    #         "enableScheduledBackup": "enable_scheduled_backup",
    #         "scheduledTime": "scheduled_time",
    #     }
    #     for ndfc_key, user_key in camel_keys.items():
    #         if user_key not in params:
    #             continue
    #         self._translated_nv_pairs[ndfc_key] = params[user_key]

    def _build_mandatory_params(self):
        """
        Caller: self._validate_dependencies()

        build a map of mandatory parameters.

        Certain parameters become mandatory only if another parameter is
        set, or only if it's set to a specific value.  For example, if
        UNDERLAY_IS_V6 is set to True, the following parameters become
        mandatory:
        -   ANYCAST_LB_ID
        -   LOOPBACK0_IPV6_RANGE
        -   LOOPBACK1_IPV6_RANGE
        -   ROUTER_ID_RANGE
        -   V6_SUBNET_RANGE
        -   V6_SUBNET_TARGET_MASK

        self._mandatory_params is a dictionary, keyed on parameter.
        The value is a dictionary with the following keys:

        value:  The parameter value that makes the dependent parameters
                mandatory.  Using UNDERLAY_IS_V6 as an example, it must
                have a value of True, for the six dependent parameters to
                be considered mandatory.
        mandatory:  a python dict() containing mandatory parameters and what
                    value (if any) they must have.  Indicate that the value
                    should not be considered by setting it to None.

        NOTE: Generalized parameter value validation is handled elsewhere

        Hence, we have the following structure for the
        self._mandatory_params dictionary, to handle the case where
        underlay_is_v6 is set to True.  Below, we don't care what the
        value for any of the mandatory parameters is.  We only care that
        they are set.

        self._mandatory_params = {
            "UNDERLAY_IS_V6": {
                "value": True,
                "mandatory": {
                    "ANYCAST_LB_ID": None
                    "LOOPBACK0_IPV6_RANGE": None
                    "LOOPBACK1_IPV6_RANGE": None
                    "ROUTER_ID_RANGE": None
                    "V6_SUBNET_RANGE": None
                    "V6_SUBNET_TARGET_MASK": None
                }
            }
        }

        Above, we validate that all mandatory parameters are set, only
        if the value of UNDERLAY_IS_V6 is True.

        Set "value:" above to "__any__" if the dependent parameters are
        mandatory regardless of the parameter's value.  For example, if
        we wanted to verify that UNDERLAY_IS_V6 is set to True in the case
        that ANYCAST_LB_ID is set (which can be a value between 1-1023) we
        don't care what the value of ANYCAST_LB_ID is.  We only care that
        UNDERLAY_IS_V6 is set to True.  In this case, we could add the following:

        self._mandatory_params.update = {
            "ANYCAST_LB_ID": {
                "value": "__any__",
                "mandatory": {
                    "UNDERLAY_IS_V6": True
                }
            }
        }

        """
        self._mandatory_params = {}
        self._mandatory_params.update(
            {
                "ANYCAST_LB_ID": {
                    "value": "__any__",
                    "mandatory": {"UNDERLAY_IS_V6": True},
                }
            }
        )
        self._mandatory_params.update(
            {
                "AUTO_SYMMETRIC_DEFAULT_VRF": {
                    "value": True,
                    "mandatory": {
                        "VRF_LITE_AUTOCONFIG": "Back2Back&ToExternal",
                        "AUTO_VRFLITE_IFC_DEFAULT_VRF": True,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "AUTO_SYMMETRIC_VRF_LITE": {
                    "value": True,
                    "mandatory": {"VRF_LITE_AUTOCONFIG": "Back2Back&ToExternal"},
                }
            }
        )
        self._mandatory_params.update(
            {
                "AUTO_VRFLITE_IFC_DEFAULT_VRF": {
                    "value": True,
                    "mandatory": {
                        "VRF_LITE_AUTOCONFIG": "Back2Back&ToExternal",
                        "DEFAULT_VRF_REDIS_BGP_RMAP": None,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "BFD_AUTH_ENABLE": {
                    "value": True,
                    "mandatory": {
                        "BFD_ENABLE": True,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "BFD_AUTH_KEY": {
                    "value": "__any__",
                    "mandatory": {
                        "BFD_ENABLE": True,
                        "BFD_AUTH_ENABLE": True,
                        "BFD_AUTH_KEY_ID": None,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "BFD_AUTH_KEY_ID": {
                    "value": "__any__",
                    "mandatory": {
                        "BFD_ENABLE": True,
                        "BFD_AUTH_ENABLE": True,
                        "BFD_AUTH_KEY": None,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "BFD_IBGP_ENABLE": {
                    "value": True,
                    "mandatory": {
                        "BFD_ENABLE": True,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "BFD_ISIS_ENABLE": {
                    "value": True,
                    "mandatory": {
                        "BFD_ENABLE": True,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "BFD_OSPF_ENABLE": {
                    "value": True,
                    "mandatory": {
                        "BFD_ENABLE": True,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "BFD_PIM_ENABLE": {
                    "value": True,
                    "mandatory": {
                        "BFD_ENABLE": True,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "BGP_AUTH_ENABLE": {
                    "value": True,
                    "mandatory": {
                        "BGP_AUTH_KEY": None,
                        "BGP_AUTH_KEY_TYPE": None,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "BOOTSTRAP_MULTISUBNET": {
                    "value": True,
                    "mandatory": {
                        "BOOTSTRAP_ENABLE": True,
                        "DHCP_ENABLE": True,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "DHCP_ENABLE": {
                    "value": True,
                    "mandatory": {
                        "BOOTSTRAP_ENABLE": True,
                        "DHCP_END": None,
                        # dhcp_ipv6_enable _is_ mandatory, when
                        # dhcp_enable is set to True.  However,
                        # NDFC currently only has one value for this
                        # (DHCPv4), and does set this value for the
                        # user when dhcp_enable is True. BUT, this may
                        # change in the future.
                        # "dhcp_ipv6_enable": "DHCPv4",
                        "DHCP_START": None,
                        "MGMT_GW": None,
                        "MGMT_PREFIX": None,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "DNS_SERVER_IP_LIST": {
                    "value": "__any__",
                    "mandatory": {
                        "DNS_SERVER_VRF": None,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "DNS_SERVER_VRF": {
                    "value": "__any__",
                    "mandatory": {
                        "DNS_SERVER_IP_LIST": None,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "ENABLE_DEFAULT_QUEUING_POLICY": {
                    "value": True,
                    "mandatory": {
                        "DEFAULT_QUEUING_POLICY_CLOUDSCALE": None,
                        "DEFAULT_QUEUING_POLICY_OTHER": None,
                        "DEFAULT_QUEUING_POLICY_R_SERIES": None,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "ENABLE_FABRIC_VPC_DOMAIN_ID": {
                    "value": True,
                    "mandatory": {
                        "FABRIC_VPC_DOMAIN_ID": None,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "ENABLE_MACSEC": {
                    "value": True,
                    "mandatory": {
                        "MACSEC_ALGORITHM": None,
                        "MACSEC_CIPHER_SUITE": None,
                        "MACSEC_FALLBACK_ALGORITHM": None,
                        "MACSEC_FALLBACK_KEY_STRING": None,
                        "MACSEC_KEY_STRING": None,
                        "MACSEC_REPORT_TIMER": None,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "ENABLE_NETFLOW": {
                    "value": True,
                    "mandatory": {
                        "NETFLOW_EXPORTER_LIST": None,
                        "NETFLOW_RECORD_LIST": None,
                        "NETFLOW_MONITOR_LIST": None,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "ENABLE_NXAPI_HTTP": {
                    "value": True,
                    "mandatory": {
                        "ENABLE_NXAPI": True,
                        "NXAPI_HTTPS_PORT": None,
                        "NXAPI_HTTP_PORT": None,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "FEATURE_PTP": {
                    "value": True,
                    "mandatory": {
                        "PTP_DOMAIN_ID": None,
                        "PTP_LB_ID": None,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "MPLS_HANDOFF": {
                    "value": True,
                    "mandatory": {
                        "MPLS_LB_ID": None,
                        "MPLS_LOOPBACK_IP_RANGE": None,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "NXAPI_HTTPS_PORT": {
                    "value": "__any__",
                    "mandatory": {
                        "ENABLE_NXAPI": True,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "NXAPI_HTTP_PORT": {
                    "value": "__any__",
                    "mandatory": {
                        "ENABLE_NXAPI": True,
                        "ENABLE_NXAPI_HTTP": True,
                        "NXAPI_HTTPS_PORT": None,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "SYSLOG_SERVER_IP_LIST": {
                    "value": "__any__",
                    "mandatory": {
                        "SYSLOG_SEV": None,
                    },
                }
            }
        )
        self._mandatory_params.update(
            {
                "UNDERLAY_IS_V6": {
                    "value": True,
                    "mandatory": {
                        "ANYCAST_LB_ID": None,
                        "LOOPBACK0_IPV6_RANGE": None,
                        "LOOPBACK1_IPV6_RANGE": None,
                        "ROUTER_ID_RANGE": None,
                        "V6_SUBNET_RANGE": None,
                        "V6_SUBNET_TARGET_MASK": None,
                    },
                }
            }
        )

    def _build_parameter_aliases(self):
        """
        Caller self._validate_dependencies()

        For some parameters, like VRF_LITE_AUTOCONFIG, we don't
        want the user to have to remember the spelling for
        their values e.g. Back2Back&ToExternal.  So, we alias
        the value NDFC expects (Back2Back&ToExternal) to something
        easier.  In this case, 1.

        See also: _get_parameter_alias()
        """
        self._parameter_aliases = {}
        self._parameter_aliases["VRF_LITE_AUTOCONFIG"] = {
            "Back2Back&ToExternal": 1,
            "Manual": 0,
        }

    def _get_parameter_alias(self, param, value):
        """
        Caller: self._validate_dependencies()

        Accessor method for self._parameter_aliases

        param: the parameter
        value: the parameter's value that NDFC expects

        Return the value alias for param (i.e. param's value
        prior to translation, i.e. the value that's used in the
        playbook) if it exists.

        Return None otherwise

        See also: self._build_parameter_aliases()
        """
        if param not in self._parameter_aliases:
            return None
        if value not in self._parameter_aliases[param]:
            return None
        return self._parameter_aliases[param][value]

    def _build_failed_dependencies(self):
        """
        If the user has set one or more parameters that, in turn, cause
        other parameters to become mandatory, build a dictionary of these
        dependencies and what value is expected for each.

        Example self._failed_dependencies.

        In this example, the user set AUTO_SYMMETRIC_VRF_LITE to True,
        which makes VRF_LITE_AUTOCONFIG mandatory. Too, VRF_LITE_AUTOCONFIG
        MUST have a value of Back2Back&ToExternal. Though, in the playbook,
        the user sets VRF_LITE_AUTOCONFIG to 1, since 1 is an alias for
        Back2Back&ToExternal.  See self._handle_failed_dependencies()
        for how we handle aliased parameters.

        {
            'VRF_LITE_AUTOCONFIG': 'Back2Back&ToExternal'
        }
        """
        method_name = inspect.stack()[0][3]
        if not self._requires_validation:
            return
        self._failed_dependencies = {}

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.config: {self.config}"
        self.log.debug(msg)

        for user_param in self._requires_validation:
            # mandatory_params associated with user_param
            mandatory_params = self._mandatory_params[user_param]["mandatory"]
            for check_param in mandatory_params:
                check_value = mandatory_params[check_param]

                msg = f"{self.class_name}.{method_name}: "
                msg += f"check_param {check_param}, "
                msg += f"check_value {check_value} "
                self.log.debug(msg)

                if check_param not in self.config and check_value is not None:
                    # The playbook doesn't contain this mandatory parameter.
                    # We care what the value is (since it's not None).
                    # If the mandatory parameter's default value is not equal
                    # to the required value, add it to the failed dependencies.
                    param_up = check_param.upper()
                    if param_up in self._default_nv_pairs:
                        if self._default_nv_pairs[param_up] != check_value:
                            self._failed_dependencies[check_param] = check_value
                            continue
                else:
                    # The playbook does not contain this mandatory parameter.
                    # We don't care what the value is (since it's None).
                    # Add it to the failed dependencies.
                    if check_value is None:
                        msg = f"{self.class_name}.{method_name}: "
                        msg += f"check_param {check_param}, check_value None "
                        msg += "adding to failed dependencies."
                        self._failed_dependencies[check_param] = check_value
                        continue

                if self.config[check_param] != check_value and check_value is not None:
                    # The playbook does contain this mandatory parameter, but
                    # the value in the playbook does not match the required value
                    # and we care about what the required value is.
                    msg = f"{self.class_name}.{method_name}: "
                    msg += f"check_param {check_param}, check_value: {check_value} "
                    msg += "adding to failed dependencies."
                    self._failed_dependencies[check_param] = check_value
                    continue
        msg = f"{self.class_name}.{method_name}: "
        msg += f"self._failed_dependencies {self._failed_dependencies}"
        self.log.debug(msg)

    def _validate_dependencies(self):
        """
        Validate cross-parameter dependencies.

        Caller: self._validate_config_for_merged_state()

        On failure to validate cross-parameter dependencies:
           set self.result to False
           set self.msg to an appropriate error message

        See also: docstring for self._build_mandatory_params()
        """
        method_name = inspect.stack()[0][3]
        self._build_mandatory_params()
        self._build_parameter_aliases()
        self._requires_validation = set()
        for user_param in self.config:
            msg = f"{self.class_name}.{method_name}: "
            msg = f"{user_param}, "
            msg += f"value {self.config[user_param]}"
            self.log.debug(msg)
            # param doesn't have any dependent parameters
            if user_param not in self._mandatory_params:
                msg = f"{self.class_name}.{method_name}: "
                msg = f"{user_param} has no dependent parameters."
                self.log.debug(msg)
                continue
            # need to run validation for user_param with value "__any__"
            if self._mandatory_params[user_param]["value"] == "__any__":
                msg = f"{self.class_name}.{method_name}: "
                msg = f"{user_param} has value __any__."
                self.log.debug(msg)
                self._requires_validation.add(user_param)
            # need to run validation because user_param is a specific value
            if self.config[user_param] == self._mandatory_params[user_param]["value"]:
                msg = f"{self.class_name}.{method_name}: "
                msg = f"{user_param} has specific value "
                msg += f"{self.config[user_param]}."
                self.log.debug(msg)
                self._requires_validation.add(user_param)
        if not self._requires_validation:
            msg = f"{self.class_name}.{method_name}: "
            msg += "No parameters require validation."
            self.log.debug(msg)
            return
        self._build_failed_dependencies()
        self._handle_failed_dependencies()

    def _handle_failed_dependencies(self):
        """
        If there are failed dependencies:
        1.  Set self.result to False
        2.  Build a useful message for the user that lists
            the additional parameters that NDFC expects
        """
        if not self._failed_dependencies:
            return
        for user_param in self._requires_validation:
            if self._mandatory_params[user_param]["value"] == "any":
                msg = f"When {user_param} is set, "
            else:
                msg = f"When {user_param} is set to "
                msg += f"{self._mandatory_params[user_param]['value']}, "
            msg += "the following parameters are mandatory: "

            for key, value in self._failed_dependencies.items():
                msg += f"parameter {key} "
                if value is None:
                    msg += "value <any value>, "
                else:
                    # If the value expected in the playbook is different
                    # from the value sent to NDFC, use the value expected in
                    # the playbook so as not to confuse the user.
                    alias = self._get_parameter_alias(key, value)
                    if alias is None:
                        msg_value = value
                    else:
                        msg_value = alias
                    msg += f"value {msg_value}, "
            self._append_msg(msg)
            self.result = False

    def _build_payload(self):
        """
        Build the payload to create the fabric specified self.config
        Caller: _validate_dependencies
        """
        self.payload = copy.deepcopy(self.config)

    def _build_payload_orig(self):
        """
        Build the payload to create the fabric specified self.config
        Caller: _validate_dependencies
        """
        self.payload = {}
        self._translate_to_ndfc_nv_pairs(self.config)
        for key, value in self._translated_nv_pairs.items():
            self.payload[key] = value

    @property
    def config(self):
        """
        Basic initial validatation for individual fabric configuration
        Verifies that config is a dict() and that mandatory keys are
        present.
        """
        return self.properties["config"]

    @config.setter
    def config(self, param):
        if not self._validate_config(param):
            return
        self.properties["config"] = param

    @property
    def msg(self):
        """
        messages to return to the caller
        """
        return self.properties["msg"]

    @msg.setter
    def msg(self, param):
        self.properties["msg"] = param

    @property
    def payload(self):
        """
        The payload to send to NDFC
        """
        return self.properties["payload"]

    @payload.setter
    def payload(self, param):
        self.properties["payload"] = param

    @property
    def result(self):
        """
        get/set intermediate results and final result
        """
        return self.properties["result"]

    @result.setter
    def result(self, param):
        self.properties["result"] = param

    @property
    def state(self):
        """
        The Ansible state provided by the caller
        """
        return self.properties["state"]

    @state.setter
    def state(self, param):
        if param not in self._valid_states:
            msg = f"invalid state {param}. "
            msg += f"expected one of: {','.join(sorted(self._valid_states))}"
            self.result = False
            self._append_msg(msg)
        self.properties["state"] = param
