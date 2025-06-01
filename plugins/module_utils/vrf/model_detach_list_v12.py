# -*- coding: utf-8 -*-
from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LanDetachItem(BaseModel):
    """
    # Summary

    A single lan detach item within DetachList.lan_attach_list.

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

    deployment: bool = Field(alias="deployment", default=False)
    extension_values: Optional[str] = Field(alias="extensionValues", default="")
    fabric: str = Field(alias="fabric", min_length=1, max_length=64)
    freeform_config: Optional[str] = Field(alias="freeformConfig", default="")
    instance_values: Optional[str] = Field(alias="instanceValues", default="")
    is_deploy: Optional[bool] = Field(alias="is_deploy")
    serial_number: str = Field(alias="serialNumber")
    vlan: Union[int | None] = Field(alias="vlanId")
    vrf_name: str = Field(alias="vrfName", min_length=1, max_length=32)

    @field_validator("deployment", mode="after")
    @classmethod
    def force_deployment_to_false(cls, value) -> bool:
        """
        Force deployment to False.  This model is used for detaching
        VRF attachments, so deployment should always be False.
        """
        return False


class DetachList(BaseModel):
    """
    # Summary

    Represents a payload for detaching VRF attachments.

    See NdfcVrf12.get_items_to_detach_model

    ## Structure

    - lan_attach_list: List[LanDetachItem]
    - vrf_name: str
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        validate_by_alias=True,
        validate_by_name=True,
    )

    lan_attach_list: List[LanDetachItem] = Field(alias="lanAttachList")
    vrf_name: str = Field(alias="vrfName")
