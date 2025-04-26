# -*- coding: utf-8 -*-
# @author: Allen Robel
# @file: plugins/module_utils/common/models/ipv6_host.py
"""
Validate IPv6 host address.
"""
from pydantic import BaseModel, Field, field_validator

from ..validators.ipv6_host import validate_ipv6_host


class IPv6HostModel(BaseModel):
    """
    # Summary

    Model to validate an IPv6 host address without prefix.

    ## Raises

    - ValueError: If the input is not a valid IPv6 host address.

    ## Example usage

    ```python
    try:
        ipv6_host_address = IPv6HostModel(ipv6_host="2001::1")
        log.debug(f"Valid: {ipv6_host_address}")
    except ValueError as err:
        # Handle the error
    ```

    """

    ipv6_host: str = Field(
        ...,
        description="IPv6 address without prefix e.g. 2001::1",
    )

    @field_validator("ipv6_host")
    @classmethod
    def validate(cls, value: str) -> str:
        """
        Validate that the input is a valid IPv6 host address

        Note: Broadcast addresses are accepted as valid.
        """
        # Validate the address part
        try:
            result = validate_ipv6_host(value)
        except ValueError as error:
            msg = f"Invalid IPv6 host address: {value}. "
            msg += f"detail: {error}"
            raise ValueError(msg) from error

        if result is True:
            # Valid IPv6 host address
            return value
        msg = f"Invalid IPv6 host address: {value}."
        raise ValueError(msg)
