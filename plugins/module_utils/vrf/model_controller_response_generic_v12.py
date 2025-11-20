# -*- coding: utf-8 -*-
import traceback
from typing import Any, Optional

# from pydantic import BaseModel, ConfigDict, Field


try:
    from pydantic import BaseModel, ConfigDict, Field

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
