#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@file   : ipv6_host.py
@Author : Allen Robel
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
        print(f"Valid: {ipv6_host_address}")
    except ValueError as err:
        print(f"Validation error: {err}")
    ```

    """

    ipv6_host: str = Field(
        ...,
        description="IPv6 address without prefix e.g. 2001::1",
    )

    @field_validator("ipv6_host")
    @classmethod
    def validate(cls, value: str):
        """
        Validate that the input is a valid IPv6 host address

        Note: Broadcast addresses are accepted as valid.
        """
        # Validate the address part
        try:
            result = validate_ipv6_host(value)
        except ValueError as err:
            msg = f"Invalid IPv6 host address: {value}. Error: {err}"
            raise ValueError(msg) from err

        if result is True:
            # If the address is a host address, return it
            return value
        raise ValueError(f"Invalid IPv6 host address: {value}.")
