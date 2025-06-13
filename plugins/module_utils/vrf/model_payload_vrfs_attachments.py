# -*- coding: utf-8 -*-
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


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
    instance_values: Optional[str] = Field(alias="instanceValues", default="")
    serial_number: str = Field(alias="serialNumber")
    vlan: int = Field(alias="vlan")
    vrf_name: str = Field(alias="vrfName", min_length=1, max_length=32)


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
    vrf_name: str = Field(alias="vrfName")
