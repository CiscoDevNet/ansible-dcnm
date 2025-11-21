# -*- coding: utf-8 -*-
import traceback
from typing import Optional

try:
    from pydantic import ConfigDict, Field
except ImportError:
    from ..common.third_party.pydantic import ConfigDict, Field
    HAS_PYDANTIC = False
    PYDANTIC_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_PYDANTIC = True
    PYDANTIC_IMPORT_ERROR = None

from .model_controller_response_generic_v12 import ControllerResponseGenericV12


class ControllerResponseGetIntV12(ControllerResponseGenericV12):
    """
    # Summary

    Response model for a GET request to the controller that returns an integer.

    ## Raises

    ValueError if validation fails

    ## Structure

    - DATA: int - The integer data returned by the controller.
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

    DATA: int
    ERROR: Optional[str] = Field(default="")
    MESSAGE: Optional[str] = Field(default="")
    METHOD: Optional[str] = Field(default="")
    REQUEST_PATH: Optional[str] = Field(default="")
    RETURN_CODE: Optional[int] = Field(default=500)
