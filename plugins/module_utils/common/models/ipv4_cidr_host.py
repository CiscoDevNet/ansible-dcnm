# -*- coding: utf-8 -*-
# @author: Allen Robel
# @file: plugins/module_utils/common/models/ipv4_cidr_host.py
"""
Validate CIDR-format IPv4 host address.
"""
import traceback
try:
    from pydantic import BaseModel, Field, field_validator
except ImportError:
    HAS_PYDANTIC = False
    PYDANTIC_IMPORT_ERROR = traceback.format_exc()
    from ..third_party.pydantic import BaseModel, Field, field_validator
else:
    HAS_PYDANTIC = True
    PYDANTIC_IMPORT_ERROR = None

from ..validators.ipv4_cidr_host import validate_ipv4_cidr_host


class IPv4CidrHostModel(BaseModel):
    """
    # Summary

    Model to validate a CIDR-format IPv4 host address.

    ## Raises

    - ValueError: If the input is not a valid CIDR-format IPv4 host address.

    ## Example usage
    ```python
    try:
        ipv4_cidr_host_address = IPv4CidrHostModel(ipv4_cidr_host="192.168.1.1/24")
    except ValueError as err:
        # Handle the error
    ```

    """

    ipv4_cidr_host: str = Field(
        ...,
        description="CIDR-format IPv4 host address, e.g. 10.1.1.1/24",
    )

    @field_validator("ipv4_cidr_host")
    @classmethod
    def validate(cls, value: str) -> str:
        """
        Validate that the input is a valid CIDR-format IPv4 host address
        and that it is NOT a network address.

        Note: Broadcast addresses are accepted as valid.
        """
        # Validate the address part
        try:
            result = validate_ipv4_cidr_host(value)
        except ValueError as error:
            msg = f"Invalid CIDR-format IPv4 host address: {value}. "
            msg += f"detail: {error}"
            raise ValueError(msg) from error

        if result is True:
            # Valid CIDR-format IPv4 host address
            return value
        msg = f"Invalid CIDR-format IPv4 host address: {value}. "
        msg += "Are the host bits all zero?"
        raise ValueError(msg)
