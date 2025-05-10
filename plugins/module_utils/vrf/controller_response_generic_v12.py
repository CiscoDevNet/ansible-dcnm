# -*- coding: utf-8 -*-
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class ControllerResponseGenericV12(BaseModel):
    """
    # Summary

    Generic response model for the controller.

    ## Raises

    ValueError if validation fails
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    DATA: Optional[Union[list, dict, str]] = Field(default="")
    ERROR: Optional[str] = Field(default="")
    MESSAGE: Optional[str] = Field(default="")
    METHOD: Optional[str] = Field(default="")
    RETURN_CODE: Optional[int] = Field(default=500)
