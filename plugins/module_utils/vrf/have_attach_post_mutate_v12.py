# -*- coding: utf-8 -*-
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class HaveLanAttachItem(BaseModel):
    deployment: bool = Field(alias="deployment")
    extension_values: Optional[str] = Field(alias="extensionValues", default="")
    fabric: str = Field(alias="fabricName", min_length=1, max_length=64)
    freeform_config: Optional[str] = Field(alias="freeformConfig", default="")
    instance_values: Optional[str] = Field(alias="instanceValues", default="")
    is_attached: bool = Field(alias="isAttached")
    is_deploy: bool = Field(alias="is_deploy")
    serial_number: str = Field(alias="serialNumber")
    vlan: int = Field(alias="vlanId")
    vrf_name: str = Field(alias="vrfName", min_length=1, max_length=32)


class HaveAttachPostMutate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        validate_by_alias=True,
        validate_by_name=True,
    )

    lan_attach_list: List[HaveLanAttachItem] = Field(alias="lanAttachList")
    vrf_name: str = Field(alias="vrfName")
