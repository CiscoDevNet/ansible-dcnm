from __future__ import absolute_import, division, print_function
from typing import List, Optional, Dict
from ansible.module_utils.six import raise_from
from ansible.errors import AnsibleError

try:
    from pydantic import BaseModel, model_validator
except ImportError as imp_exc:
    PYDANTIC_IMPORT_ERROR = imp_exc
else:
    PYDANTIC_IMPORT_ERROR = None

if PYDANTIC_IMPORT_ERROR:
    raise_from(
        AnsibleError('Pydantic must be installed to use this plugin. Use pip or install test-requirements.'),
        PYDANTIC_IMPORT_ERROR)

class DcnmInterfaceQuerySchema(BaseModel):
    class NvPairs(BaseModel):
        ADMIN_STATE: Optional[str] = None
        ALLOWED_VLANS: Optional[str] = None
        BPDUGUARD_ENABLED: Optional[str] = None
        CDP_ENABLE: Optional[str] = None
        CONF: Optional[str] = None
        DESC: Optional[str] = None
        DISABLE_IP_REDIRECTS: Optional[str] = None
        ENABLE_MONITOR: Optional[str] = None
        ENABLE_NETFLOW: Optional[str] = None
        ENABLE_ORPHAN_PORT: Optional[str] = None
        ENABLE_PFC: Optional[str] = None
        ENABLE_PIM_SPARSE: Optional[str] = None
        ENABLE_QOS: Optional[str] = None
        FABRIC_NAME: Optional[str] = None
        INTF_NAME: Optional[str] = None
        INTF_VRF: Optional[str] = None
        IP: Optional[str] = None
        IPv6: Optional[str] = None
        IPv6_PREFIX: Optional[str] = None
        LINK_STATE_ROUTING: Optional[str] = None
        LINK_STATE_ROUTING_TAG: Optional[str] = None
        MTU: Optional[str] = None
        NATIVE_VLAN: Optional[str] = None
        NETFLOW_MONITOR: Optional[str] = None
        NETFLOW_SAMPLER: Optional[str] = None
        PIM_DR_PRIORITY: Optional[str] = None
        POLICY_DESC: Optional[str] = None
        POLICY_ID: Optional[str] = None
        PORTTYPE_FAST_ENABLED: Optional[str] = None
        PORT_DUPLEX_MODE: Optional[str] = None
        PREFIX: Optional[str] = None
        PRIORITY: Optional[str] = None
        PTP: Optional[str] = None
        QOS_POLICY: Optional[str] = None
        QUEUING_POLICY: Optional[str] = None
        ROUTING_TAG: Optional[str] = None
        SERIAL_NUMBER: Optional[str] = None
        SPEED: Optional[str] = None

    class Interface(BaseModel):
        ifName: str
        nvPairs: NvPairs
        serialNumber: str

    class InterfacePolicy(BaseModel):
        interfaces: List[Interface]
        policy: str

    failed: Optional[bool] = False
    response: Optional[List[InterfacePolicy]] = None

    @classmethod
    def yaml_config_to_dict(cls, expected_config_data, test_fabric):
        # Mapping of fields in the yaml config to the fields in the DCNM API response
        # Format: {yaml_field: api_field}
        # adding fields places them in pydantic model and is checked by deepdiff
        # removing/commenting fields removes them from pydantic model

        # response.interfaces
        interface_fields = {
            "name": "ifName",
            "switch": "serialNumber"  # Will take first switch from list
        }

        # response.interfaces.nvPairs
        interface_nvpairs_fields = {
            "admin_state": "ADMIN_STATE",
            "mode": "MODE",
            "speed": "SPEED",
            "description": "DESC",
            "mtu": "MTU",
            "bpdu_guard": "BPDUGUARD_ENABLED",
            "port_type_fast": "PORTTYPE_FAST_ENABLED",
            "allowed_vlans": "ALLOWED_VLANS",
            "access_vlan": "NATIVE_VLAN",
            "int_vrf": "INTF_VRF",
            "ipv4_addr": "IP",
            "ipv4_mask_len": "PREFIX",
            "ipv6_addr": "IPv6",
            "ipv6_mask_len": "IPv6_PREFIX",
            "route_tag": "ROUTING_TAG"
        }

        # Mode to policy mapping
        mode_to_policy = {
            "trunk": "int_trunk_host",
            "routed": "int_routed_host",
            "epl_routed": "epl_routed_intf",
            "monitor": "int_monitor_ethernet"
        }

        expected_data = {}
        expected_data["failed"] = False
        expected_data["response"] = []

        for interface in expected_config_data:
            interface_dict = {}
            interface_dict["interfaces"] = []
            interface_dict["policy"] = mode_to_policy.get(interface["profile"].get("mode", ""), "unknown")

            intf_dict = {}
            # Map base interface fields
            for key, value in interface_fields.items():
                if key in interface:
                    if key == "switch":
                        intf_dict[value] = interface[key][0]
                    else:
                        intf_dict[value] = interface[key]

            # Map nvPairs fields
            intf_dict["nvPairs"] = {
                "FABRIC_NAME": test_fabric,
                "INTF_NAME": interface["name"],
                "POLICY_ID": "",  # Will be filled by NDFC
                "POLICY_DESC": "",
                "PRIORITY": "500"  # Default value
            }

            profile = interface["profile"]
            mode = profile.get("mode", "")

            # Map common nvPairs fields
            for key, value in interface_nvpairs_fields.items():
                if key in profile:
                    val = profile[key]
                    # Convert boolean values to string
                    if isinstance(val, bool):
                        val = str(val).lower()
                    # Convert integer values to string
                    elif isinstance(val, (int)):
                        val = str(val)
                    intf_dict["nvPairs"][value] = val

            # Handle commands
            if "cmds" in profile:
                intf_dict["nvPairs"]["CONF"] = "; ".join(profile["cmds"])

            # Mode specific defaults
            if mode in ["trunk", "access"]:
                intf_dict["nvPairs"].update({
                    "CDP_ENABLE": "true",
                    "PORT_DUPLEX_MODE": "auto",
                    "ALLOWED_VLANS": profile.get("allowed_vlans", "none")
                })
            elif mode == "epl_routed":
                intf_dict["nvPairs"].update({
                    "LINK_STATE_ROUTING": "ospf",
                    "LINK_STATE_ROUTING_TAG": "UNDERLAY"
                })

            interface_dict["interfaces"].append(intf_dict)
            expected_data["response"].append(interface_dict)

        return expected_data
