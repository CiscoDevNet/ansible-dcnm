#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@file   : ipv4_host.py
@Author : Allen Robel
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
        print(f"Valid: {ipv4_host_address}")
    except ValueError as err:
        print(f"Validation error: {err}")
    ```

    """

    ipv4_host: str = Field(
        ...,
        description="IPv4 address without prefix e.g. 10.1.1.1",
    )

    @field_validator("ipv4_host")
    @classmethod
    def validate(cls, value: str):
        """
        Validate that the input is a valid IPv4 host address

        Note: Broadcast addresses are accepted as valid.
        """
        # Validate the address part
        try:
            result = validate_ipv4_host(value)
        except ValueError as err:
            msg = f"Invalid IPv4 host address: {value}. Error: {err}"
            raise ValueError(msg) from err

        if result is True:
            # If the address is a host address, return it
            return value
        raise ValueError(f"Invalid IPv4 host address: {value}.")
