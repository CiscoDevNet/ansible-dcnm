# -*- coding: utf-8 -*-
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DataVrfInfo(BaseModel):
    """
    # Summary

    Data model for VRF information.

    ## Raises

    ValueError if validation fails

    ## Structure

    - l3vni: int - The Layer 3 VNI.
    - vrf_prefix: str - The prefix for the VRF.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        validate_by_alias=True,
    )

    l3_vni: int = Field(alias="l3vni")
    vrf_prefix: str = Field(alias="vrf-prefix")


class ControllerResponseGetFabricsVrfinfoV12(BaseModel):
    """
    # Summary

    Response model for a request to the controller for the following endpoint.

    Verb: GET
    Path: /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/vrfinfo

    ## Raises

    ValueError if validation fails

    ## Controller response

    ```json
    {
        "l3vni": 50000,
        "vrf-prefix": "MyVRF_"
    }
    ```

    ## Structure

    - DATA: DataVrfInfo - JSON containing l3vni and vrf-prefix.
    - ERROR: Optional[str] - Error message if any error occurred.
    - MESSAGE: Optional[str] - Additional message.
    - METHOD: Optional[str] - The HTTP method used for the request.
    - REQUEST_PATH: Optional[str] - The request path for the controller.
    - RETURN_CODE: Optional[int] - The HTTP return code, default is 500.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    DATA: DataVrfInfo
    ERROR: Optional[str] = Field(default="")
    MESSAGE: Optional[str] = Field(default="")
    METHOD: Optional[str] = Field(default="")
    REQUEST_PATH: Optional[str] = Field(default="")
    RETURN_CODE: Optional[int] = Field(default=500)
