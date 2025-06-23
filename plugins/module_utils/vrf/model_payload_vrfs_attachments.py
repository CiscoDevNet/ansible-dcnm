# -*- coding: utf-8 -*-
import json

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, field_serializer
from ..common.models.ipv4_cidr_host import IPv4CidrHostModel
from ..common.models.ipv6_cidr_host import IPv6CidrHostModel

class PayloadVrfsAttachmentsLanAttachListInstanceValues(BaseModel):
    """
    # Summary

    Represents the instance values for a single lan attach item within VrfAttachPayload.lan_attach_list.

    # Structure

    - loopback_id: str, alias: loopbackId
    - loopback_ip_address: str, alias: loopbackIpAddress
    - loopback_ip_v6_address: str, alias: loopbackIpV6Address
    - switch_route_target_import_evpn: str, alias: switchRouteTargetImportEvpn
    - switch_route_target_export_evpn: str, alias: switchRouteTargetExportEvpn

    ## Example

    ```json
        {
            "loopbackId": "1",
            "loopbackIpAddress": "10.1.1.1",
            "loopbackIpV6Address": "f16c:f7ec:cfa2:e1c5:9a3c:cb08:801f:36b8",
            "switchRouteTargetImportEvpn": "5000:100",
            "switchRouteTargetExportEvpn": "5000:100"
        }
    ```
    """

    loopback_id: str = Field(alias="loopbackId", default="")
    loopback_ip_address: str = Field(alias="loopbackIpAddress", default="")
    loopback_ipv6_address: str = Field(alias="loopbackIpV6Address", default="")
    switch_route_target_import_evpn: str = Field(alias="switchRouteTargetImportEvpn", default="")
    switch_route_target_export_evpn: str = Field(alias="switchRouteTargetExportEvpn", default="")

    @field_validator("loopback_ip_address", mode="before")
    def validate_loopback_ip_address(cls, value: str) -> str:
        """
        Validate loopback_ip_address to ensure it is a valid IPv4 CIDR host.
        """
        if value == "":
            return value
        try:
            return IPv4CidrHostModel(ipv4_cidr_host=value).ipv4_cidr_host
        except ValueError as error:
            msg = f"Invalid loopback IP address (loopback_ip_address): {value}. detail: {error}"
            raise ValueError(msg) from error

    @field_validator("loopback_ipv6_address", mode="before")
    def validate_loopback_ipv6_address(cls, value: str) -> str:
        """
        Validate loopback_ipv6_address to ensure it is a valid IPv6 CIDR host.
        """
        if value == "":
            return value
        try:
            return IPv6CidrHostModel(ipv6_cidr_host=value).ipv6_cidr_host
        except ValueError as error:
            msg = f"Invalid loopback IPv6 address (loopback_ipv6_address): {value}. detail: {error}"
            raise ValueError(msg) from error


class PayloadVrfsAttachmentsLanAttachListItem(BaseModel):
    """
    # Summary

    A single lan attach item within VrfAttachPayload.lan_attach_list.

    # Structure

    - deployment: bool, alias: deployment, default=False
    - extension_values: Optional[str], alias: extensionValues, default=""
    - fabric: str (min_length=1, max_length=64), alias: fabric
    - freeform_config: Optional[str], alias: freeformConfig, default=""
    - instance_values: Optional[str], alias: instanceValues, default=""
    - serial_number: str, alias: serialNumber
    - vlan_id: int, alias: vlanId
    - vrf_name: str (min_length=1, max_length=32), alias: vrfName

    ## Notes

    1. extensionValues in the example is shortened for brevity.  It is a JSON string with the following structure::

    ```json
    {
        'MULTISITE_CONN': {'MULTISITE_CONN': []},
        'VRF_LITE_CONN': {
            'VRF_LITE_CONN': [
                {
                    'AUTO_VRF_LITE_FLAG': 'true',
                    'DOT1Q_ID': '2',
                    'IF_NAME': 'Ethernet2/10',
                    'IP_MASK': '10.33.0.2/30',
                    'IPV6_MASK': '2010::10:34:0:7/64',
                    'IPV6_NEIGHBOR': '2010::10:34:0:3',
                    'NEIGHBOR_ASN': '65001',
                    'NEIGHBOR_IP': '10.33.0.1',
                    'PEER_VRF_NAME': 'ansible-vrf-int1',
                    'VRF_LITE_JYTHON_TEMPLATE': 'Ext_VRF_Lite_Jython'
                }
            ]
        }
    }
    ```

    2. instanceValues in the example is shortened for brevity. It is a JSON string with the following fields:

    - It has the following structure:


    - instanceValues in the example is shortened for brevity. It is a JSON string with the following fields:
    - loopbackId: str
    - loopbackIpAddress: str
    - loopbackIpV6Address: str
    - switchRouteTargetImportEvpn: str
    - switchRouteTargetExportEvpn: str
    ## Example

    ```json
        {
            "deployment": true,
            "extensionValues": "{\"field1\":\"field1_value\",\"field2\":\"field2_value\"}",
            "fabric": "f1",
            "freeformConfig": "",
            "instanceValues": "{\"field1\":\"field1_value\",\"field2\":\"field2_value\"}",
            "serialNumber": "FOX2109PGD0",
            "vlan": 0,
            "vrfName": "ansible-vrf-int1"
        }
    ```
    """

    deployment: bool = Field(alias="deployment")
    extension_values: Optional[str] = Field(alias="extensionValues", default="")
    fabric: str = Field(alias="fabric", min_length=1, max_length=64)
    freeform_config: Optional[str] = Field(alias="freeformConfig", default="")
    instance_values: Optional[PayloadVrfsAttachmentsLanAttachListInstanceValues] = Field(alias="instanceValues", default="")
    serial_number: str = Field(alias="serialNumber")
    vlan: int = Field(alias="vlan")
    vrf_name: str = Field(alias="vrfName", min_length=1, max_length=32)


    @field_serializer("instance_values")
    def serialize_instance_values(self, value: PayloadVrfsAttachmentsLanAttachListInstanceValues) -> str:
        """
        Serialize instance_values to a JSON string.
        """
        if value == "":
            return json.dumps({})  # return empty JSON value
        return value.model_dump_json(by_alias=True)


class PayloadVrfsAttachments(BaseModel):
    """
    # Summary

    Represents a POST payload for the following endpoint:

    api.v1.lan_fabric.rest.top_down.fabrics.vrfs.Vrfs.EpVrfPost

    /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/test_fabric/vrfs/attachments

    See NdfcVrf12.push_diff_attach

    ## Structure

    - lan_attach_list: list[PayloadVrfsAttachmentsLanAttachListItem]
    - vrf_name: str

    ## Example payload

    ```json
    {
        "lanAttachList": [
            {
                "deployment": true,
                "extensionValues": "",
                "fabric": "test_fabric",
                "freeformConfig": "",
                "instanceValues": "{\"loopbackId\":\"\"}", # content removed for brevity
                "serialNumber": "XYZKSJHSMK1",
                "vlan": 0,
                "vrfName": "test_vrf_1"
            },
       ],
        "vrfName": "test_vrf"
    }
    ```
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        validate_by_alias=True,
        validate_by_name=True,
    )

    lan_attach_list: list[PayloadVrfsAttachmentsLanAttachListItem] = Field(alias="lanAttachList")
    vrf_name: str = Field(alias="vrfName", min_length=1, max_length=32)
