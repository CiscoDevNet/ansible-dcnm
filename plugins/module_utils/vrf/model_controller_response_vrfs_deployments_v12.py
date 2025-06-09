# -*- coding: utf-8 -*-
"""
Validation model for controller responses related to the following endpoint:

Path: /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs/deployments
Verb: POST
"""

import warnings
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field, PydanticExperimentalWarning

from .model_controller_response_generic_v12 import ControllerResponseGenericV12

warnings.filterwarnings("ignore", category=PydanticExperimentalWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Base configuration for the Vrf* models
base_vrf_model_config = ConfigDict(
    str_strip_whitespace=True,
    use_enum_values=True,
    validate_assignment=True,
)


class VrfDeploymentsDataDictV12(BaseModel):
    """
    # Summary

    Validation model for the DATA within the controller response to
    the following endpoint, for the case where DATA is a dictionary.

    Verb: GET
    Path: /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs/deployments

    ## Raises

    ValueError if validation fails

    ## Structure

    ```json
    {
        "status": "",
    }
    ```
    """

    model_config = base_vrf_model_config

    status: str = Field(
        default="",
        description="Status of the VRF deployment. Possible values: 'Success', 'Failure', 'In Progress'.",
    )


class ControllerResponseVrfsDeploymentsV12(ControllerResponseGenericV12):
    """
    # Summary

    Validation model for the controller response to the following endpoint:

    Verb: POST
    Path: /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs

    ## Raises

    ValueError if validation fails
    """

    DATA: Optional[Union[VrfDeploymentsDataDictV12, str]] = Field(default="")
    ERROR: Optional[str] = Field(default="")
    MESSAGE: Optional[str] = Field(default="")
    METHOD: Optional[str] = Field(default="")
    RETURN_CODE: Optional[int] = Field(default=500)
