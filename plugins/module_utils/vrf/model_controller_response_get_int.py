# -*- coding: utf-8 -*-
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ControllerResponseGetIntV12(BaseModel):
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
