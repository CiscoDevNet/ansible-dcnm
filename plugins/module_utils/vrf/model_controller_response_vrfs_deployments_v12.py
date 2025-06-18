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

    Validation model for the DATA field within the controller response to
    the following endpoint, for the case where DATA is a dictionary.

    ## Endpoint

    - Verb: POST
    - Path: /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs/deployments

    ## Raises

    ValueError if validation fails

    ## Structure

    ```json
    {
        "status": "Deployment of VRF(s) has been initiated successfully",
    }
    ```
    """

    model_config = base_vrf_model_config

    status: str = Field(
        default="",
        description="Status of the VRF deployment.",
    )


class ControllerResponseVrfsDeploymentsV12(ControllerResponseGenericV12):
    """
     # Summary

     Validation model for the controller response to the following endpoint:

     ## Endpoint

     - Verb: POST
     - Path: /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs/deployments

     ## Raises

     - `ValueError` if validation fails

     ## Structure

     ### NOTES

     - DATA.status has been observed to contain the following values
       - "Deployment of VRF(s) has been initiated successfully"
       - "No switches PENDING for deployment."

    ```json
     {
         "DATA": {
             "status": "Deployment of VRF(s) has been initiated successfully"
         },
         "MESSAGE": "OK",
         "METHOD": "POST",
         "REQUEST_PATH": "https://172.22.150.244:443/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/f1/vrfs/deployments",
         "RETURN_CODE": 200
     }
     ```
    """

    DATA: Optional[Union[VrfDeploymentsDataDictV12, str]] = Field(default="")
    ERROR: Optional[str] = Field(default="")
    MESSAGE: Optional[str] = Field(default="")
    METHOD: Optional[str] = Field(default="")
    REQUEST_PATH: str
    RETURN_CODE: Optional[int] = Field(default=500)
