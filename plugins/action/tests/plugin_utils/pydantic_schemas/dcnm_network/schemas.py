from __future__ import absolute_import, division, print_function

from typing import List, Optional
from pydantic import BaseModel, model_validator, Field


# Top level schema
# Format: ModuleMethodSchema
# 1. DcnmNetworkQuerySchema

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
        vrfName: Optional[str] = None

    class Parent(BaseModel):
        fabric: Optional[str] = None
        networkId: Optional[int] = None
        networkName: Optional[str] = None
        networkTemplate: Optional[str] = None
        networkTemplateConfig: Optional["DcnmNetworkQuerySchema.NetworkTemplateConfig"] = None
        networkStatus: Optional[str] = None
        vrf: Optional[str] = None

    class Network(BaseModel):
        attach: Optional[List["DcnmNetworkQuerySchema.SwitchAttach"]] = None
        parent: Optional["DcnmNetworkQuerySchema.Parent"] = None

        @model_validator(mode="after")
        def remove_none(cls, values):
            if getattr(values, "attach") is not None:
                setattr(values, "attach", [sw for sw in getattr(values, "attach") if sw.portNames is not None])
            return values
        
    failed: Optional[bool] = None
    response: Optional[List[Network]] = None

    def yaml_config_to_dict(expected_config_data, test_fabric, deploy=False):
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
            if 'vrf_name' in network:
                network_dict["parent"]["vrf"] = network['vrf_name']
            # if deploy:
            #     network_dict["parent"]["networkStatus"] = "DEPLOYED"
            # else:
            #     network_dict["parent"]["networkStatus"] = "PENDING"
            expected_data["response"].append(network_dict)
        return expected_data