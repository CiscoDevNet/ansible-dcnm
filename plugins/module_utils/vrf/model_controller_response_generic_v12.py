# -*- coding: utf-8 -*-
"""
Generic response model for the controller
"""
import traceback
from typing import Any, Optional

try:
    from pydantic import BaseModel, ConfigDict, Field
except ImportError:
    from ..common.third_party.pydantic import BaseModel, ConfigDict, Field

    HAS_PYDANTIC = False
    PYDANTIC_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_PYDANTIC = True
    PYDANTIC_IMPORT_ERROR = None


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

    DATA: Optional[Any] = Field(default="")
    ERROR: Optional[str] = Field(default="")
    MESSAGE: Optional[str] = Field(default="")
    METHOD: Optional[str] = Field(default="")
    REQUEST_PATH: Optional[str] = Field(default="")
    RETURN_CODE: Optional[int] = Field(default=500)
