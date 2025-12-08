# -*- coding: utf-8 -*-
"""
Validation model for controller responses for the following endpoint:

Path: /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs/attachments?vrf-names={vrf1,vrf2,...}
Verb: GET
"""
from __future__ import annotations

import traceback
from typing import Optional

try:
    from pydantic import BaseModel, ConfigDict, Field
except ImportError:
    from ..common.third_party.pydantic import BaseModel, ConfigDict, Field
    HAS_PYDANTIC = False
    PYDANTIC_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_PYDANTIC = True
    PYDANTIC_IMPORT_ERROR = None

from .model_controller_response_generic_v12 import ControllerResponseGenericV12


class ControllerResponseLanAttachItem(BaseModel):
    """
    # Summary

    A lanAttachList item (see ControllerResponseVrfsAttachmentsDataItem in this file)

    ## Structure

    - `entity_name`: str = alias "entityName"
    - `fabric_name`: str - alias "fabricName", max_length=64
    - `instance_values`: Optional[str] = alias="instanceValues"
    - `ip_address`: str = alias="ipAddress"
    - `is_lan_attached`: bool = alias="isLanAttached"
    - `lan_attach_state`: str = alias="lanAttachState"
    - `peer_serial_no`: Optional[str] = alias="peerSerialNo", default=None
    - `switch_name`: str = alias="switchName"
    - `switch_role`: str = alias="switchRole"
    - `switch_serial_no`: str = alias="switchSerialNo"
    - `vlan_id`: int | None = alias="vlanId", ge=2, le=4094
    - `vrf_id`: int | None = alias="vrfId", ge=1, le=16777214
    - `vrf_name`: str = alias="vrfName", min_length=1, max_length=32
    """

    entity_name: Optional[str] = Field(alias="entityName", default="")
    fabric_name: str = Field(alias="fabricName", max_length=64)
    instance_values: Optional[str] = Field(alias="instanceValues", default="")
    ip_address: str = Field(alias="ipAddress")
    is_lan_attached: bool = Field(alias="isLanAttached")
    lan_attach_state: str = Field(alias="lanAttachState")
    peer_serial_no: Optional[str] = Field(alias="peerSerialNo", default=None)
    switch_name: str = Field(alias="switchName")
    switch_role: str = Field(alias="switchRole")
    switch_serial_no: str = Field(alias="switchSerialNo")
    vlan_id: int | None = Field(alias="vlanId", ge=2, le=4094)
    vrf_id: int | None = Field(alias="vrfId", ge=1, le=16777214)
    vrf_name: str = Field(alias="vrfName", min_length=1, max_length=32)


class ControllerResponseVrfsAttachmentsDataItem(BaseModel):
    """
    # Summary

    A data item in the response for the VRFs attachments endpoint.

    # Structure

    - `lan_attach_list`: list[ControllerResponseLanAttachItem] - alias "lanAttachList"
    - `vrf_name`: str - alias "vrfName"

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
        "lanAttachList": [
            {
                "entityName": "ansible-vrf-int2",
                "fabricName": "f1",
                "instanceValues": "{\"field1\": \"value1\", \"field2\": \"value2\"}",
                "ipAddress": "172.22.150.112",
                "isLanAttached": true,
                "lanAttachState": "DEPLOYED",
                "peerSerialNo": null,
                "switchName": "cvd-1211-spine",
                "switchRole": "border spine",
                "switchSerialNo": "FOX2109PGCS",
                "vlanId": 1500,
                "vrfId": 9008012,
                "vrfName": "ansible-vrf-int2"
            }
        ],
        "vrfName": "ansible-vrf-int1"
    }
    ```
    """

    lan_attach_list: list[ControllerResponseLanAttachItem] = Field(alias="lanAttachList")
    vrf_name: str = Field(alias="vrfName")


class ControllerResponseVrfsAttachmentsV12(ControllerResponseGenericV12):
    """
    # Summary

    Controller response model for the following endpoint.

    # Endpoint

    ## Verb

    GET

    ## Path:

    /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs/attachments?vrf-names={vrf1,vrf2,...}

    # Raises

    ValueError if validation fails

    # Structure

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
    DATA: list[ControllerResponseVrfsAttachmentsDataItem]
    MESSAGE: str
    METHOD: str
    REQUEST_PATH: str
    RETURN_CODE: int
