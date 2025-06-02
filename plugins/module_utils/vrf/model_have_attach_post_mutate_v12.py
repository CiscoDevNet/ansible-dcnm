# -*- coding: utf-8 -*-
from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class HaveLanAttachItem(BaseModel):
    """
    # Summary

    A single lan attach item within lanAttachList.

    ## Structure

    - deployment: bool, alias: deployment
    - extension_values: Optional[str], alias: extensionValues, default=""
    - fabric: str (min_length=1, max_length=64), alias: fabricName
    - freeform_config: Optional[str], alias: freeformConfig, default=""
    - instance_values: Optional[str], alias: instanceValues, default=""
    - is_attached: bool, alias: isAttached
    - is_deploy: bool, alias: is_deploy
    - serial_number: str, alias: serialNumber
    - vlan: Union(int | None), alias: vlanId
    - vrf_name: str (min_length=1, max_length=32), alias: vrfName
    """
    deployment: bool = Field(alias="deployment")
    extension_values: Optional[str] = Field(alias="extensionValues", default="")
    fabric: str = Field(alias="fabricName", min_length=1, max_length=64)
    freeform_config: Optional[str] = Field(alias="freeformConfig", default="")
    instance_values: Optional[str] = Field(alias="instanceValues", default="")
    is_attached: bool = Field(alias="isAttached")
    is_deploy: bool = Field(alias="is_deploy")
    serial_number: str = Field(alias="serialNumber")
    vlan: Union[int | None] = Field(alias="vlanId")
    vrf_name: str = Field(alias="vrfName", min_length=1, max_length=32)


class HaveAttachPostMutate(BaseModel):
    """
    # Summary

    Validates a mutated VRF attachment.

    See NdfcVrf12.populate_have_attach_model
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        validate_by_alias=True,
        validate_by_name=True,
    )

    lan_attach_list: List[HaveLanAttachItem] = Field(alias="lanAttachList")
    vrf_name: str = Field(alias="vrfName")
