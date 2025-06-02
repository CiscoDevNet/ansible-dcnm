# -*- coding: utf-8 -*-
from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LanAttachListItemV12(BaseModel):
    """
    # Summary

    A single lan attach item within VrfAttachPayload.lan_attach_list.

    ## Structure

    - deployment: bool, alias: deployment, default=False
    - extension_values: Optional[str], alias: extensionValues, default=""
    - fabric: str (min_length=1, max_length=64), alias: fabric
    - freeform_config: Optional[str], alias: freeformConfig, default=""
    - instance_values: Optional[str], alias: instanceValues, default=""
    - is_deploy: Optional[bool], alias: is_deploy
    - serial_number: str, alias: serialNumber
    - vlan: Union(int | None), alias: vlan
    - vrf_name: str (min_length=1, max_length=32), alias: vrfName

    ## Notes
    - `deployment` - False indicates that attachment should be detached.
      This model unconditionally forces `deployment` to False.
    """

    deployment: bool = Field(alias="deployment")
    extension_values: Optional[str] = Field(alias="extensionValues", default="")
    fabric: str = Field(alias="fabric", min_length=1, max_length=64)
    freeform_config: Optional[str] = Field(alias="freeformConfig", default="")
    instance_values: Optional[str] = Field(alias="instanceValues", default="")
    serial_number: str = Field(alias="serialNumber")
    vlan: Union[int | None] = Field(alias="vlanId")
    vrf_name: str = Field(alias="vrfName", min_length=1, max_length=32)


class VrfAttachPayloadV12(BaseModel):
    """
    # Summary

    Represents a POST payload for the following endpoint:

    api.v1.lan_fabric.rest.top_down.fabrics.vrfs.Vrfs.EpVrfPost

    See NdfcVrf12.push_diff_attach

    ## Structure

    - lan_attach_list: List[LanAttachListItemV12]
    - vrf_name: str
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        validate_by_alias=True,
        validate_by_name=True,
    )

    lan_attach_list: List[LanAttachListItemV12] = Field(alias="lanAttachList")
    vrf_name: str = Field(alias="vrfName")
