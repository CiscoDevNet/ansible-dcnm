from __future__ import absolute_import, division, print_function
from typing import List, Optional, Annotated
from ansible.module_utils.six import raise_from
from ansible.errors import AnsibleError

try:
    from pydantic import BaseModel, model_validator, BeforeValidator
except ImportError as imp_exc:
    PYDANTIC_IMPORT_ERROR = imp_exc
else:
    PYDANTIC_IMPORT_ERROR = None

if PYDANTIC_IMPORT_ERROR:
    raise_from(
        AnsibleError('Pydantic must be installed to use this plugin. Use pip or install test-requirements.'),
        PYDANTIC_IMPORT_ERROR)

# Top level schema
# Format: ModuleMethodSchema
# 1. DcnmNetworkQuerySchema

# replace None with default value if it throws an error
# this can happen if fields are unevenly defined across different networks
# eg: in one network, vrf is defined, in the other it is not


def coerce_int_to_str(data):
    """Transform input int to str, return other types as is"""
    if isinstance(data, int):
        return str(data)
    return data


CoercedStr = Annotated[str, BeforeValidator(coerce_int_to_str)]


class DcnmNetworkQuerySchema(BaseModel):

    class SwitchAttach(BaseModel):
        ipAddress: Optional[str] = None
        portNames: Optional[str] = None
        fabricName: Optional[str] = None
        networkId: Optional[CoercedStr] = None
        networkName: Optional[str] = None
        vlanId: Optional[CoercedStr] = None
        lanAttachState: Optional[str] = None

        @model_validator(mode="after")
        @classmethod
        def sort_portNames(cls, values):
            if getattr(values, "portNames") is not None:
                if getattr(values, "portNames") == "":
                    setattr(values, "portNames", None)
                else:
                    setattr(values, "portNames", ",".join(sorted(getattr(values, "portNames").split(","))))
            return values

    class NetworkTemplateConfig(BaseModel):
        gatewayIpAddress: Optional[str] = None
        vlanId: Optional[CoercedStr] = None
        vrfName: Optional[str] = "NA"
        dhcpServerAddr1: Optional[str] = None
        dhcpServerAddr2: Optional[str] = None
        dhcpServerAddr3: Optional[str] = None
        vrfDhcp: Optional[str] = None
        vrfDhcp2: Optional[str] = None
        vrfDhcp3: Optional[str] = None
        surpressArp: Optional[bool] = None
        isLayer2Only: Optional[bool] = False
        mtu: Optional[CoercedStr] = ""
        vlanName: Optional[str] = None
        intfDescription: Optional[str] = None
        tag: Optional[CoercedStr] = None
        secondaryGW1: Optional[str] = None
        secondaryGW2: Optional[str] = None
        secondaryGW3: Optional[str] = None
        secondaryGW4: Optional[str] = None
        gatewayIpV6Address: Optional[str] = None
        enableL3OnBorder: Optional[bool] = None

    class Parent(BaseModel):
        fabric: Optional[str] = None
        networkId: Optional[CoercedStr] = None
        networkName: Optional[str] = None
        networkTemplate: Optional[str] = None
        networkTemplateConfig: Optional["DcnmNetworkQuerySchema.NetworkTemplateConfig"] = None
        networkStatus: Optional[str] = None
        vrf: Optional[str] = "NA"

    class Network(BaseModel):
        attach: Optional[List["DcnmNetworkQuerySchema.SwitchAttach"]] = None
        parent: Optional["DcnmNetworkQuerySchema.Parent"] = None

        @model_validator(mode="after")
        @classmethod
        def remove_none(cls, values):
            if getattr(values, "attach") is not None:
                setattr(values, "attach", [sw for sw in getattr(values, "attach") if sw.portNames is not None])
            return values

    failed: Optional[bool] = None
    response: Optional[List[Network]] = None

    @classmethod
    def yaml_config_to_dict(cls, expected_config_data, test_fabric):

        # Mapping of fields in the yaml config to the fields in the DCNM API response
        # Format: {yaml_field: api_field}
        # adding fields places them in pydantic model and is checked by deepdiff
        # removing/commenting fields removes them from pydantic model
        # response.parent
        network_parent_fields = {
            "net_id": "networkId",
            "net_name": "networkName",
            "net_template": "networkTemplate",
            "vrf_name": "vrf",
            # "deploy": "networkStatus"
        }
        # response.parent.networkTemplateConfig
        network_template_config_fields = {
            "gw_ip_subnet": "gatewayIpAddress",
            "vlan_id": "vlanId",
            "vrf_name": "vrfName",
            "dhcp_srvr1_ip": "dhcpServerAddr1",
            "dhcp_srvr2_ip": "dhcpServerAddr2",
            "dhcp_srvr3_ip": "dhcpServerAddr3",
            "dhcp_srvr1_vrf": "vrfDhcp",
            "dhcp_srvr2_vrf": "vrfDhcp2",
            "dhcp_srvr3_vrf": "vrfDhcp3",
            "arp_surpress": "surpressArp",
            "is_l2only": "isLayer2Only",
            "mtu_l3intf": "mtu",
            "vlan_name": "vlanName",
            "int_desc": "intfDescription",
            "routing_tag": "tag",
            "secondary_ip_gw1": "secondaryGW1",
            "secondary_ip_gw2": "secondaryGW2",
            "secondary_ip_gw3": "secondaryGW3",
            "secondary_ip_gw4": "secondaryGW4",
            "gw_ipv6_subnet": "gatewayIpV6Address",
            "l3gw_on_border": "enableL3OnBorder"
        }
        # response.attach
        network_attach_fields = {
            "ip_address": "ipAddress",
            "fabric": "fabricName",
            "net_id": "networkId",
            "net_name": "networkName",
            "vlan_id": "vlanId",
            # "lan_attach_state": "lanAttachState"
        }
        expected_data = {}
        expected_data["failed"] = False
        expected_data["response"] = []
        for network in expected_config_data:
            network_dict = {}
            network_dict["attach"] = []
            for switch in network.get('attach', []):
                switch_dict = {}
                switch_dict["fabricName"] = test_fabric
                if 'ports' in switch:
                    switch_dict["portNames"] = ",".join(switch['ports'])
                for key, value in network_attach_fields.items():
                    if key in switch:
                        switch_dict[value] = switch[key]

                network_dict["attach"].append(switch_dict)
            network_dict["parent"] = {}
            network_dict["parent"]["fabric"] = test_fabric
            for key, value in network_parent_fields.items():
                if key in network:
                    network_dict["parent"][value] = network[key]

            network_dict["parent"]["networkTemplateConfig"] = {}
            for key, value in network_template_config_fields.items():
                if key in network:
                    network_dict["parent"]["networkTemplateConfig"][value] = network[key]

            expected_data["response"].append(network_dict)
        return expected_data
