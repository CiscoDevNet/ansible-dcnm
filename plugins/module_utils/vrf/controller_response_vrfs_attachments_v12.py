# -*- coding: utf-8 -*-
from typing import List, Union

from pydantic import BaseModel, ConfigDict, Field


class LanAttachItem(BaseModel):
    fabric_name: str = Field(alias="fabricName", max_length=64)
    ip_address: str = Field(alias="ipAddress")
    is_lan_attached: bool = Field(alias="isLanAttached")
    lan_attach_state: str = Field(alias="lanAttachState")
    switch_name: str = Field(alias="switchName")
    switch_role: str = Field(alias="switchRole")
    switch_serial_no: str = Field(alias="switchSerialNo")
    vlan_id: Union[int, None] = Field(alias="vlanId", ge=2, le=4094)
    vrf_id: Union[int, None] = Field(alias="vrfId", ge=1, le=16777214)
    vrf_name: str = Field(alias="vrfName", min_length=1, max_length=32)


class DataItem(BaseModel):
    lan_attach_list: List[LanAttachItem] = Field(alias="lanAttachList")
    vrf_name: str = Field(alias="vrfName")


class ControllerResponseVrfsAttachmentsV12(BaseModel):
    """
    # Summary

    Controller response model for the following endpoint.

    ## Verb

    GET

    ## Path:
    /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/test_fabric/vrfs/attachments?vrf-names=test_vrf_1
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
        validate_assignment=True,
        validate_by_alias=True,
        validate_by_name=True,
    )
    data: List[DataItem] = Field(alias="DATA")
    message: str = Field(alias="MESSAGE")
    method: str = Field(alias="METHOD")
    return_code: int = Field(alias="RETURN_CODE")
