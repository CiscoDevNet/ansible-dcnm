#!/usr/bin/env python
# -*- coding: utf-8 -*-
# mypy: disable-error-code="import-untyped"
"""
@file   : validate_ipv6.py
@Author : Allen Robel
"""
from pydantic import BaseModel, Field, field_validator

from ..validators.ipv6_cidr_host import validate_ipv6_cidr_host


class IPv6CidrHostModel(BaseModel):
    """
    # Summary

    Model to validate a CIDR-format IPv4 host address.

    ## Raises

    - ValueError: If the input is not a valid CIDR-format IPv4 host address.

    ## Example usage
    ```python
    try:
        ipv6_cidr_host_address = IPv6CidrHostModel(ipv6_cidr_host="2001:db8::1/64")
        print(f"Valid: {ipv6_cidr_host_address}")
    except ValueError as err:
        print(f"Validation error: {err}")
    ```

    """

    ipv6_cidr_host: str = Field(
        ...,
        description="CIDR-format IPv6 host address, e.g. 2001:db8::1/64",
    )

    @field_validator("ipv6_cidr_host")
    @classmethod
    def validate(cls, value: str):
        """
        Validate that the input is a valid IPv6 CIDR-format host address
        and that it is NOT a network address.

        Note: Broadcast addresses are accepted as valid.
        """
        # Validate the address part
        try:
            result = validate_ipv6_cidr_host(value)
        except ValueError as err:
            msg = f"Invalid CIDR-format IPv6 host address: {value}. "
            msg += f"detail: {err}"
            raise ValueError(msg) from err

        if result is True:
            # If the address is a host address, return it
            return value
        msg = f"Invalid CIDR-format IPv6 host address: {value}. "
        msg += "Are the host bits all zero?"
        raise ValueError(msg)
