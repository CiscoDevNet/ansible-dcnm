# -*- coding: utf-8 -*-
import traceback
from typing import List, Optional, Union

try:
    from pydantic import BaseModel, ConfigDict, Field, field_validator

    HAS_PYDANTIC = True
    PYDANTIC_IMPORT_ERROR = None
except ImportError:
    HAS_PYDANTIC = False
    PYDANTIC_IMPORT_ERROR = traceback.format_exc()

    # Fallback: object base class
    BaseModel = object  # type: ignore[assignment]

    # Fallback: Field that does nothing
    def Field(*args, **kwargs):  # type: ignore[no-redef] # pylint: disable=unused-argument,invalid-name
        """Pydantic Field fallback when pydantic is not available."""
        return None

    # Fallback: ConfigDict that does nothing
    def ConfigDict(**kwargs):  # type: ignore[no-redef] # pylint: disable=unused-argument,invalid-name
        """Pydantic ConfigDict fallback when pydantic is not available."""
        return {}

    # Fallback: field_validator decorator that does nothing
    def field_validator(*args, **kwargs):  # type: ignore[no-redef] # pylint: disable=unused-argument,invalid-name
        """Pydantic field_validator fallback when pydantic is not available."""

        def decorator(func):
            return func

        return decorator


class LanDetachListItemV12(BaseModel):
    """
    # Summary

    A single lan detach item within VrfDetachPayloadV12.lan_attach_list.

    ## Structure

    - deployment: bool, alias: deployment, default=False
    - extension_values: Optional[str], alias: extensionValues, default=""
    - fabric: str (min_length=1, max_length=64), alias: fabric
    - freeform_config: Optional[str], alias: freeformConfig, default=""
    - instance_values: Optional[str], alias: instanceValues, default=""
    - is_deploy: Optional[bool], alias: is_deploy
    - serial_number: str, alias: serialNumber
    - vlan: Union(int | None), alias: vlanId
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
    is_attached: Optional[bool] = Field(alias="isAttached", default=True)
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


class VrfDetachPayloadV12(BaseModel):
    """
    # Summary

    Represents a payload for detaching VRF attachments.

    See NdfcVrf12.get_items_to_detach_model

    ## Structure

    - lan_attach_list: List[LanDetachListItemV12]
    - vrf_name: str

    ## Example payload

    ```json
    {
        "lanAttachList": [
            {
                "deployment": false,
                "extensionValues": "",
                "fabric": "test_fabric",
                "freeformConfig": "",
                "instanceValues": "{\"loopbackId\":\"\"}", # content removed for brevity
                "serialNumber": "XYZKSJHSMK2",
                "vlanId": 202,
                "vrfName": "test_vrf_1"
            }
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

    lan_attach_list: List[LanDetachListItemV12] = Field(alias="lanAttachList")
    vrf_name: str = Field(alias="vrfName")
