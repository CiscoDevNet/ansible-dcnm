from __future__ import absolute_import, division, print_function
from typing import List, Optional
import re
from ansible.module_utils.six import raise_from
from ansible.errors import AnsibleError

try:
    from pydantic import BaseModel, field_validator
except ImportError as imp_exc:
    PYDANTIC_IMPORT_ERROR = imp_exc
else:
    PYDANTIC_IMPORT_ERROR = None

if PYDANTIC_IMPORT_ERROR:
    raise_from(
        AnsibleError('Pydantic must be installed to use this plugin. Use pip or install test-requirements.'),
        PYDANTIC_IMPORT_ERROR)


def expand_interface_name(name):
    """
    Expand abbreviated interface names to their full forms following DCNM conventions.
    Based on dcnm_intf_get_if_name method from dcnm_interface.py

    Examples:
        po300 -> Port-channel300
        eth1/1 -> Ethernet1/1
        lo100 -> Loopback100
        vpc25 -> vPC25
        vlan10 -> vlan10
    """
    if name.lower().startswith("po"):
        # Port channel: po300 -> Port-channel300
        port_id = re.findall(r"\d+", name)
        if port_id:
            return f"Port-channel{port_id[0]}"
    elif name.lower().startswith("eth"):
        # Ethernet: eth1/1 -> Ethernet1/1, eth1/1.2 -> Ethernet1/1.2, eth1/49/1 -> Ethernet1/49/1
        if re.findall(r"\d+\/\d+\/\d+", name):
            port_id = re.findall(r"\d+\/\d+\/\d+", name)
            return f"Ethernet{port_id[0]}"
        elif re.findall(r"\d+\/\d+.\d+", name):
            port_id = re.findall(r"\d+\/\d+.\d+", name)
            return f"Ethernet{port_id[0]}"
        elif re.findall(r"\d+\/\d+", name):
            port_id = re.findall(r"\d+\/\d+", name)
            return f"Ethernet{port_id[0]}"
    elif name.lower().startswith("lo"):
        # Loopback: lo100 -> Loopback100
        port_id = re.findall(r"\d+", name)
        if port_id:
            return f"Loopback{port_id[0]}"
    elif name.lower().startswith("vpc"):
        # VPC: vpc25 -> vPC25
        port_id = re.findall(r"\d+", name)
        if port_id:
            return f"vPC{port_id[0]}"
    elif name.lower().startswith("vlan"):
        # SVI: vlan10 -> vlan10 (already in correct format)
        port_id = re.findall(r"\d+", name)
        if port_id:
            return f"vlan{port_id[0]}"

    # Return original name if no pattern matches
    return name


class DcnmInterfaceQuerySchema(BaseModel):
    class NvPairs(BaseModel):
        ACCESS_VLAN: Optional[str] = None
        ADMIN_STATE: Optional[str] = None
        ALLOWED_VLANS: Optional[str] = None
        BPDUGUARD_ENABLED: Optional[str] = None
        CDP_ENABLE: Optional[str] = None
        CONF: Optional[str] = None
        COPY_DESC: Optional[str] = None
        DESC: Optional[str] = None
        DISABLE_IP_REDIRECTS: Optional[str] = None
        DISABLE_LACP_SUSPEND: Optional[str] = None
        ENABLE_LACP_VPC_CONV: Optional[str] = None
        ENABLE_MIRROR_CONFIG: Optional[str] = None
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
        LACP_PORT_PRIO: Optional[str] = None
        LACP_RATE: Optional[str] = None
        LINK_STATE_ROUTING: Optional[str] = None
        LINK_STATE_ROUTING_TAG: Optional[str] = None
        MTU: Optional[str] = None
        NATIVE_VLAN: Optional[str] = None
        NETFLOW_MONITOR: Optional[str] = None
        NETFLOW_SAMPLER: Optional[str] = None
        PC_MODE: Optional[str] = None
        PEER1_ALLOWED_VLANS: Optional[str] = None
        PEER1_MEMBER_INTERFACES: Optional[str] = None
        PEER1_NATIVE_VLAN: Optional[str] = None
        PEER1_PCID: Optional[str] = None
        PEER1_PO_CONF: Optional[str] = None
        PEER1_PO_DESC: Optional[str] = None
        PEER2_ALLOWED_VLANS: Optional[str] = None
        PEER2_MEMBER_INTERFACES: Optional[str] = None
        PEER2_NATIVE_VLAN: Optional[str] = None
        PEER2_PCID: Optional[str] = None
        PEER2_PO_CONF: Optional[str] = None
        PEER2_PO_DESC: Optional[str] = None
        PIM_DR_PRIORITY: Optional[str] = None
        PO_ID: Optional[str] = None
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
        ROUTE_MAP_TAG: Optional[str] = None
        SERIAL_NUMBER: Optional[str] = None
        SPEED: Optional[str] = None
        V6IP: Optional[str] = None
        createVpc: Optional[str] = None

        @field_validator('CONF')
        @classmethod
        def normalize_conf_commands(cls, v):
            """
            Normalize CONF field by splitting commands, sorting them, and removing 'no shutdown'.
            This helps with consistent comparison of command lists.
            """
            if v is None or v == "":
                return v

            # Split commands by various delimiters
            commands = []
            if "; " in v:
                commands = v.split("; ")
            elif "\n" in v:
                commands = v.split("\n")
            else:
                commands = [v]

            # Clean up commands and remove 'no shutdown'
            cleaned_commands = []
            for cmd in commands:
                cmd = cmd.strip()
                if cmd and cmd.lower() != "no shutdown":
                    cleaned_commands.append(cmd)

            # Sort commands for consistent comparison
            cleaned_commands.sort()

            # Return empty string if no commands left, otherwise join with "; "
            return "; ".join(cleaned_commands) if cleaned_commands else ""

        @field_validator('INTF_NAME', 'PO_ID')
        @classmethod
        def normalize_interface_name(cls, v):
            """
            Expand abbreviated interface names to full forms and convert to lowercase.
            Examples: po300 -> port-channel300, eth1/1 -> ethernet1/1, vpc25 -> vpc25
            """
            if v is None:
                return v
            expanded = expand_interface_name(v)
            return expanded.lower()

        @field_validator('ADMIN_STATE', 'BPDUGUARD_ENABLED', 'PORTTYPE_FAST_ENABLED', 'PC_MODE', 'INTF_VRF', 'MTU', 'SPEED')
        @classmethod
        def normalize_string_fields(cls, v):
            """Convert common string fields to lowercase for case-insensitive comparison."""
            if v is not None:
                return v.lower()
            return v

    class Interface(BaseModel):
        ifName: str
        nvPairs: "DcnmInterfaceQuerySchema.NvPairs"
        serialNumber: tuple

        @field_validator('ifName')
        @classmethod
        def normalize_ifname(cls, v):
            """
            Expand abbreviated interface names to full forms and convert to lowercase.
            Examples: po300 -> port-channel300, eth1/1 -> ethernet1/1, vpc25 -> vpc25
            """
            expanded = expand_interface_name(v)
            return expanded.lower()

        @field_validator('serialNumber', mode='before')
        @classmethod
        def normalize_serial_number(cls, v):
            """Convert serialNumber string to sorted tuple by splitting on ~."""
            if isinstance(v, str):
                return tuple(sorted(v.split("~")))
            return v

    class InterfacePolicy(BaseModel):
        interfaces: List["DcnmInterfaceQuerySchema.Interface"]
        policy: Optional[str] = None

    failed: Optional[bool] = False
    response: Optional[List["DcnmInterfaceQuerySchema.InterfacePolicy"]] = None

    @classmethod
    def yaml_config_to_dict(cls, expected_config_data, test_fabric, switch_ip_sn_mapping=None):
        """
        Convert YAML interface configuration to DCNM API response format for validation.

        Field Mappings from YAML config to JSON nvPairs:

        Common Fields (all interface types):
        - admin_state → ADMIN_STATE (boolean → string)
        - speed → SPEED (string)
        - description → DESC (string)
        - mtu → MTU (string)
        - bpdu_guard → BPDUGUARD_ENABLED (boolean/string → string)
        - port_type_fast → PORTTYPE_FAST_ENABLED (boolean → string)
        - cmds → CONF (list → sorted, semicolon-separated string, 'no shutdown' commands filtered out)

        Mode-specific Fields:
        Trunk mode:
        - allowed_vlans → ALLOWED_VLANS (string)
        - native_vlan → NATIVE_VLAN (integer → string)

        Access mode:
        - access_vlan → ACCESS_VLAN (integer → string)

        Routed mode:
        - int_vrf → INTF_VRF (string, excluded if empty)
        - ipv4_addr → IP (string)
        - ipv4_mask_len → PREFIX (integer → string)
        - route_tag → ROUTING_TAG (string, excluded if empty)

        EPL Routed mode (extends routed):
        - ipv6_addr → IPv6 (string) for non-loopback interfaces
        - ipv6_addr → V6IP (string) for loopback interfaces
        - ipv6_mask_len → IPv6_PREFIX (integer → string)

        Interface-specific mappings:
        Loopback interfaces:
        - ipv6_addr → V6IP (instead of IPv6)
        - route_tag → ROUTE_MAP_TAG (instead of ROUTING_TAG)
        - Uses INTF_NAME field (not PO_ID)

        Interface Name Handling:
        - Port-channel interfaces: Use PO_ID field
        - Other interfaces: Use INTF_NAME field

        Policy Mapping (NOT compared in validation):
        - Policy fields are auto-generated by NDFC and excluded from comparison

        Auto-generated fields (excluded from comparison):
        - CDP_ENABLE, ENABLE_MONITOR, ENABLE_NETFLOW, ENABLE_ORPHAN_PORT
        - ENABLE_PFC, ENABLE_QOS, NETFLOW_MONITOR, NETFLOW_SAMPLER
        - POLICY_DESC, POLICY_ID, PORT_DUPLEX_MODE, PRIORITY
        - PTP, QOS_POLICY, QUEUING_POLICY, SERIAL_NUMBER
        - Policy field (auto-determined by NDFC)

        Always included:
        - FABRIC_NAME (from test_fabric parameter)
        - PO_ID (for port-channel interfaces) or INTF_NAME (for other interfaces)
        """
        if switch_ip_sn_mapping is None:
            switch_ip_sn_mapping = {}

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
            "speed": "SPEED",
            "description": "DESC",
            "mtu": "MTU",
            "bpdu_guard": "BPDUGUARD_ENABLED",
            "port_type_fast": "PORTTYPE_FAST_ENABLED",
            "allowed_vlans": "ALLOWED_VLANS",
            "native_vlan": "NATIVE_VLAN",
            "access_vlan": "ACCESS_VLAN",
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
            "access": "int_access_host",
            "routed": "int_routed_host",
            "epl_routed": "epl_routed_intf",
            "monitor": "int_monitor_ethernet"
        }

        # Type to policy mapping (for VPC)
        type_to_policy = {
            "vpc": "int_vpc_trunk_host"
        }

        expected_data = {}
        expected_data["failed"] = False
        expected_data["response"] = []

        for interface in expected_config_data:
            interface_dict = {}
            interface_dict["interfaces"] = []

            # Don't include policy in comparison

            intf_dict = {}
            # Map base interface fields
            for key, value in interface_fields.items():
                if key in interface:
                    if key == "name":
                        # Expand abbreviated interface names (field validator will handle lowercase conversion)
                        intf_dict[value] = expand_interface_name(interface[key])
                    elif key == "switch":
                        # Convert IP addresses to serial numbers using mapping
                        switch_list = interface[key]
                        if switch_ip_sn_mapping:
                            switch_list = [switch_ip_sn_mapping.get(sw, sw) for sw in switch_list]

                        # For VPC and AA FEX interfaces, join switches with ~
                        if interface.get("type") in ["vpc", "aa_fex"] and len(switch_list) > 1:
                            intf_dict[value] = "~".join(switch_list)
                        else:
                            intf_dict[value] = switch_list[0]
                    else:
                        intf_dict[value] = interface[key]

            # Map nvPairs fields - only include configured fields
            intf_dict["nvPairs"] = {
                "FABRIC_NAME": test_fabric
            }

            # Use PO_ID for port-channel interfaces, INTF_NAME for others
            expanded_name = expand_interface_name(interface["name"])
            if expanded_name.lower().startswith("port-channel"):
                intf_dict["nvPairs"]["PO_ID"] = expanded_name
            else:
                intf_dict["nvPairs"]["INTF_NAME"] = expanded_name

            profile = interface["profile"]
            mode = profile.get("mode", "")
            interface_type = interface.get("type", "")

            # Map common nvPairs fields - only include fields that are explicitly configured
            for key, value in interface_nvpairs_fields.items():
                if key in profile:
                    val = profile[key]

                    # Skip certain fields when they have empty string values
                    if key in ["int_vrf", "route_tag"] and val == "":
                        continue

                    # Skip ALLOWED_VLANS if set to 'none'
                    if key == "allowed_vlans" and val is not None and str(val).lower() == "none":
                        continue

                    # Handle special IPv6 mapping for loopback interfaces
                    if key == "ipv6_addr" and expanded_name.lower().startswith("loopback"):
                        # For loopback interfaces, use V6IP instead of IPv6
                        if isinstance(val, bool):
                            val = str(val).lower()
                        elif isinstance(val, (int)):
                            val = str(val)
                        intf_dict["nvPairs"]["V6IP"] = val
                        continue

                    # Handle special route_tag mapping for loopback interfaces
                    if key == "route_tag" and expanded_name.lower().startswith("loopback"):
                        # For loopback interfaces, use ROUTE_MAP_TAG instead of ROUTING_TAG
                        if val != "":  # Only include if not empty
                            if isinstance(val, bool):
                                val = str(val).lower()
                            elif isinstance(val, (int)):
                                val = str(val)
                            intf_dict["nvPairs"]["ROUTE_MAP_TAG"] = val
                        continue

                    # Convert boolean values to string
                    if isinstance(val, bool):
                        val = str(val).lower()
                    # Convert integer values to string
                    elif isinstance(val, (int)):
                        val = str(val)
                    # Keep string values as-is (field validators will handle case conversion)
                    intf_dict["nvPairs"][value] = val

            # Handle VPC and AA FEX specific fields
            if interface_type in ["vpc", "aa_fex"]:
                vpc_mapping = {
                    "pc_mode": "PC_MODE",
                    "peer1_pcid": "PEER1_PCID",
                    "peer2_pcid": "PEER2_PCID",
                    "peer1_description": "PEER1_PO_DESC",
                    "peer2_description": "PEER2_PO_DESC",
                    "peer1_allowed_vlans": "PEER1_ALLOWED_VLANS",
                    "peer2_allowed_vlans": "PEER2_ALLOWED_VLANS"
                }

                for key, value in vpc_mapping.items():
                    if key in profile:
                        val = profile[key]
                        if isinstance(val, bool):
                            val = str(val).lower()
                        elif isinstance(val, (int)):
                            val = str(val)
                        # Keep string values as-is (field validators will handle case conversion)
                        intf_dict["nvPairs"][value] = val

                # Handle member interfaces
                if "peer1_members" in profile:
                    intf_dict["nvPairs"]["PEER1_MEMBER_INTERFACES"] = ",".join(profile["peer1_members"])
                if "peer2_members" in profile:
                    intf_dict["nvPairs"]["PEER2_MEMBER_INTERFACES"] = ",".join(profile["peer2_members"])

                # Handle AA FEX peer-specific commands
                if interface_type == "aa_fex":
                    if "peer1_cmds" in profile and profile["peer1_cmds"] is not None:
                        # Filter out 'no shutdown' commands and sort for consistent comparison
                        filtered_cmds = [cmd.strip() for cmd in profile["peer1_cmds"] if cmd.strip().lower() != "no shutdown"]
                        if filtered_cmds:
                            filtered_cmds.sort()
                            intf_dict["nvPairs"]["PEER1_PO_CONF"] = "; ".join(filtered_cmds)
                    if "peer2_cmds" in profile and profile["peer2_cmds"] is not None:
                        # Filter out 'no shutdown' commands and sort for consistent comparison
                        filtered_cmds = [cmd.strip() for cmd in profile["peer2_cmds"] if cmd.strip().lower() != "no shutdown"]
                        if filtered_cmds:
                            filtered_cmds.sort()
                            intf_dict["nvPairs"]["PEER2_PO_CONF"] = "; ".join(filtered_cmds)

            # Handle commands (for non-AA FEX interfaces)
            if "cmds" in profile and interface_type != "aa_fex":
                if profile["cmds"] is not None and len(profile["cmds"]) > 0:
                    # Filter out 'no shutdown' commands and sort for consistent comparison
                    filtered_cmds = [cmd.strip() for cmd in profile["cmds"] if cmd.strip().lower() != "no shutdown"]
                    if filtered_cmds:
                        filtered_cmds.sort()
                        intf_dict["nvPairs"]["CONF"] = "; ".join(filtered_cmds)
                    else:
                        intf_dict["nvPairs"]["CONF"] = ""
                else:
                    intf_dict["nvPairs"]["CONF"] = ""

            interface_dict["interfaces"].append(intf_dict)
            expected_data["response"].append(interface_dict)

        return expected_data
