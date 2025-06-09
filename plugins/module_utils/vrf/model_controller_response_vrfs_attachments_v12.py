# -*- coding: utf-8 -*-
"""
Validation model for controller responses related to the following endpoint:

Path:  /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs/attachments?vrf-names={vrf1,vrf2,...}
Verb: GET
"""
from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from .model_controller_response_generic_v12 import ControllerResponseGenericV12


class LanAttachItem(BaseModel):
    """
    # Summary

    A lanAttachList item (see VrfsAttachmentsDataItem in this file)

    ## Structure

    - `extension_values`: Optional[str] - alias "extensionValues"
    - `fabric_name`: str - alias "fabricName", max_length=64
    - `freeform_config`: Optional[str] = alias "freeformConfig"
    - `instance_values`: Optional[str] = alias="instanceValues"
    - `ip_address`: str = alias="ipAddress"
    - `is_lan_attached`: bool = alias="isLanAttached"
    - `lan_attach_state`: str = alias="lanAttachState"
    - `switch_name`: str = alias="switchName"
    - `switch_role`: str = alias="switchRole"
    - `switch_serial_no`: str = alias="switchSerialNo"
    - `vlan_id`: Union[int, None] = alias="vlanId", ge=2, le=4094
    - `vrf_id`: Union[int, None] = alias="vrfId", ge=1, le=16777214
    - `vrf_name`: str = alias="vrfName", min_length=1, max_length=32
    """

    extension_values: Optional[str] = Field(alias="extensionValues", default="")
    fabric_name: str = Field(alias="fabricName", max_length=64)
    freeform_config: Optional[str] = Field(alias="freeformConfig", default="")
    instance_values: Optional[str] = Field(alias="instanceValues", default="")
    ip_address: str = Field(alias="ipAddress")
    is_lan_attached: bool = Field(alias="isLanAttached")
    lan_attach_state: str = Field(alias="lanAttachState")
    switch_name: str = Field(alias="switchName")
    switch_role: str = Field(alias="switchRole")
    switch_serial_no: str = Field(alias="switchSerialNo")
    vlan_id: Union[int, None] = Field(alias="vlanId", ge=2, le=4094)
    vrf_id: Union[int, None] = Field(alias="vrfId", ge=1, le=16777214)
    vrf_name: str = Field(alias="vrfName", min_length=1, max_length=32)


class VrfsAttachmentsDataItem(BaseModel):
    """
    # Summary

    A data item in the response for the VRFs attachments endpoint.

    ## Structure

    - `lan_attach_list`: List[LanAttachItem] - alias "lanAttachList"
    - `vrf_name`: str - alias "vrfName"

    ## Example

    ```json
    {
        "lanAttachList": [
            {
                "extensionValues": "",
                "fabricName": "f1",
                "freeformConfig": "",
                "instanceValues": "",
                "ipAddress": "10.1.2.3",
                "isLanAttached": true,
                "lanAttachState": "DEPLOYED",
                "switchName": "cvd-1211-spine",
                "switchRole": "border spine",
                "switchSerialNo": "ABC1234DEFG",
                "vlanId": 500,
                "vrfId": 9008011,
                "vrfName": "ansible-vrf-int1"
            }
        ],
        "vrfName": "ansible-vrf-int1"
    }
    ```
    """

    lan_attach_list: List[LanAttachItem] = Field(alias="lanAttachList")
    vrf_name: str = Field(alias="vrfName")


class ControllerResponseVrfsAttachmentsV12(ControllerResponseGenericV12):
    """
    # Summary

    Controller response model for the following endpoint.

    ## Verb

    GET

    ## Path:

    /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs/attachments?vrf-names={vrf1,vrf2,...}

    ## Raises

    ValueError if validation fails

    ## Notes

    `instanceValues` is shortened for brevity in the example.  It is a JSON string with the following fields:

    - deviceSupportL3VniNoVlan
    - loopbackId
    - loopbackIpAddress
    - loopbackIpV6Address
    - switchRouteTargetExportEvpn
    - switchRouteTargetImportEvpn

    ## Example

    ```json
    {
        "DATA": [
            {
                "lanAttachList": [
                    {
                        "entityName": "ansible-vrf-int1",
                        "fabricName": "f1",
                        "instanceValues": "{\"field1\": \"value1\", \"field2\": \"value2\"}",
                        "ipAddress": "10.1.2.3",
                        "isLanAttached": true,
                        "lanAttachState": "DEPLOYED",
                        "peerSerialNo": null,
                        "switchName": "cvd-1211-spine",
                        "switchRole": "border spine",
                        "switchSerialNo": "ABC1234DEFG",
                        "vlanId": 500,
                        "vrfId": 9008011,
                        "vrfName": "ansible-vrf-int1"
                    },
                ],
                "vrfName": "ansible-vrf-int1"
            }
        ],
        "MESSAGE": "OK",
        "METHOD": "GET",
        "REQUEST_PATH": "https://192.168.1.1:443/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/f1/vrfs/attachments?vrf-names=ansible-vrf-int1",
        "RETURN_CODE": 200
    }
    ```
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
        validate_assignment=True,
        validate_by_alias=True,
        validate_by_name=True,
    )
    DATA: List[VrfsAttachmentsDataItem]
    MESSAGE: str
    METHOD: str
    RETURN_CODE: int
