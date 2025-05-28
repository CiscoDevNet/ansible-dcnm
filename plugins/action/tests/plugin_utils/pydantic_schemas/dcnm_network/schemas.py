from __future__ import absolute_import, division, print_function
from ansible.module_utils.six import raise_from

from typing import List, Optional

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

# Top level schema
# Format: ModuleMethodSchema
# 1. DcnmNetworkQuerySchema

# replace None with default value if it throws an error
# this can happen if fields are unevenly defined across different networks
# eg: in one network, vrf is defined, in the other it is not


class DcnmNetworkQuerySchema(BaseModel):

    class SwitchAttach(BaseModel):
        ipAddress: Optional[str] = None
        portNames: Optional[str] = None
        fabricName: Optional[str] = None
        networkId: Optional[int] = None
        networkName: Optional[str] = None
        vlanId: Optional[int] = None
        lanAttachState: Optional[str] = None

        @model_validator(mode="after")
        def sort_portNames(cls, values):
            if getattr(values, "portNames") is not None:
                setattr(values, "portNames", ",".join(sorted(getattr(values, "portNames").split(","))))
            return values

    class NetworkTemplateConfig(BaseModel):
        gatewayIpAddress: Optional[str] = None
        vlanId: Optional[int] = None
        vrfName: Optional[str] = "NA"
        dhcpServerAddr1: Optional[str] = None
        dhcpServerAddr2: Optional[str] = None
        dhcpServerAddr3: Optional[str] = None
        vrfDhcp: Optional[str] = None
        vrfDhcp2: Optional[str] = None
        vrfDhcp3: Optional[str] = None
        surpressArp: Optional[bool] = None
        isLayer2Only: Optional[bool] = False
        mtu: Optional[int] = None
        vlanName: Optional[str] = None
        intfDescription: Optional[str] = None

    class Parent(BaseModel):
        fabric: Optional[str] = None
        networkId: Optional[int] = None
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

    def yaml_config_to_dict(self, expected_config_data, test_fabric):
        expected_data = {}
        expected_data["failed"] = False
        expected_data["response"] = []
        for network in expected_config_data:
            network_dict = {}
            network_dict["attach"] = []
            for switch in network.get('attach', []):
                switch_dict = {}
                if 'ip_address' in switch:
                    switch_dict["ipAddress"] = switch['ip_address']
                if 'ports' in switch:
                    switch_dict["portNames"] = ",".join(switch['ports'])
                switch_dict["fabricName"] = test_fabric
                if 'net_id' in network:
                    switch_dict["networkId"] = network['net_id']
                if 'net_name' in network:
                    switch_dict["networkName"] = network['net_name']
                if 'vlan_id' in network:
                    switch_dict["vlanId"] = network['vlan_id']
                # if deploy:
                #     switch_dict["lanAttachState"] = "DEPLOYED"
                # else:
                #     switch_dict["lanAttachState"] = "PENDING"
                network_dict["attach"].append(switch_dict)
            network_dict["parent"] = {}
            network_dict["parent"]["fabric"] = test_fabric
            if 'net_id' in network:
                network_dict["parent"]["networkId"] = network['net_id']
            if 'net_name' in network:
                network_dict["parent"]["networkName"] = network['net_name']
            if 'net_template' in network:
                network_dict["parent"]["networkTemplate"] = network['net_template']
            if 'gw_ip_subnet' in network or 'vlan_id' in network or 'vrf_name' in network:
                network_dict["parent"]["networkTemplateConfig"] = {}
                if 'gw_ip_subnet' in network:
                    network_dict["parent"]["networkTemplateConfig"]["gatewayIpAddress"] = network['gw_ip_subnet']
                if 'vlan_id' in network:
                    network_dict["parent"]["networkTemplateConfig"]["vlanId"] = network['vlan_id']
                if 'vrf_name' in network:
                    network_dict["parent"]["networkTemplateConfig"]["vrfName"] = network['vrf_name']
                if 'dhcp_srvr1_ip' in network:
                    network_dict["parent"]["networkTemplateConfig"]["dhcpServerAddr1"] = network['dhcp_srvr1_ip']
                if 'dhcp_srvr2_ip' in network:
                    network_dict["parent"]["networkTemplateConfig"]["dhcpServerAddr2"] = network['dhcp_srvr2_ip']
                if 'dhcp_srvr3_ip' in network:
                    network_dict["parent"]["networkTemplateConfig"]["dhcpServerAddr3"] = network['dhcp_srvr3_ip']
                if 'dhcp_srvr1_vrf' in network:
                    network_dict["parent"]["networkTemplateConfig"]["vrfDhcp"] = network['dhcp_srvr1_vrf']
                if 'dhcp_srvr2_vrf' in network:
                    network_dict["parent"]["networkTemplateConfig"]["vrfDhcp2"] = network['dhcp_srvr2_vrf']
                if 'dhcp_srvr3_vrf' in network:
                    network_dict["parent"]["networkTemplateConfig"]["vrfDhcp3"] = network['dhcp_srvr3_vrf']
                if 'arp_surpress' in network:
                    network_dict["parent"]["networkTemplateConfig"]["surpressArp"] = network['arp_surpress']
                if 'is_l2only' in network:
                    network_dict["parent"]["networkTemplateConfig"]["isLayer2Only"] = network['is_l2only']
                if 'mtu_l3intf' in network:
                    network_dict["parent"]["networkTemplateConfig"]["mtu"] = network['mtu_l3intf']
                if 'vlan_name' in network:
                    network_dict["parent"]["networkTemplateConfig"]["vlanName"] = network['vlan_name']
                if 'int_desc' in network:
                    network_dict["parent"]["networkTemplateConfig"]["intfDescription"] = network['int_desc']
            if 'vrf_name' in network:
                network_dict["parent"]["vrf"] = network['vrf_name']
            # if deploy:
            #     network_dict["parent"]["networkStatus"] = "DEPLOYED"
            # else:
            #     network_dict["parent"]["networkStatus"] = "PENDING"
            expected_data["response"].append(network_dict)
        return expected_data
