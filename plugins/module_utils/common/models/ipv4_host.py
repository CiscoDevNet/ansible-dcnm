# -*- coding: utf-8 -*-
# @author: Allen Robel
# @file: plugins/module_utils/common/models/ipv4_host.py
"""
Validate IPv4 host address.
"""
from pydantic import BaseModel, Field, field_validator

from ..validators.ipv4_host import validate_ipv4_host


class IPv4HostModel(BaseModel):
    """
    # Summary

    Model to validate an IPv4 host address without prefix.

    ## Raises

    - ValueError: If the input is not a valid IPv4 host address.

    ## Example usage

    ```python
    try:
        ipv4_host_address = IPv4HostModel(ipv4_host="10.33.0.1")
    except ValueError as err:
        # Handle the error
    ```

    """

    ipv4_host: str = Field(
        ...,
        description="IPv4 address without prefix e.g. 10.1.1.1",
    )

    @field_validator("ipv4_host")
    @classmethod
    def validate(cls, value: str) -> str:
        """
        Validate that the input is a valid IPv4 host address

        Note: Broadcast addresses are accepted as valid.
        """
        # Validate the address part
        try:
            result = validate_ipv4_host(value)
        except ValueError as error:
            msg = f"Invalid IPv4 host address: {value}. "
            msg += f"detail: {error}"
            raise ValueError(msg) from error

        if result is True:
            # Valid IPv4 host address
            return value
        msg = f"Invalid IPv4 host address: {value}."
        raise ValueError(msg)
