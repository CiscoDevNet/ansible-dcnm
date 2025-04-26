# -*- coding: utf-8 -*-
# @author: Allen Robel
# @file: plugins/module_utils/common/models/ipv6_cidr_host.py
"""
Validate CIDR-format IPv6 host address.
"""
from pydantic import BaseModel, Field, field_validator

from ..validators.ipv6_cidr_host import validate_ipv6_cidr_host


class IPv6CidrHostModel(BaseModel):
    """
    # Summary

    Model to validate a CIDR-format IPv6 host address.

    ## Raises

    - ValueError: If the input is not a valid CIDR-format IPv6 host address.

    ## Example usage
    ```python
    try:
        ipv6_cidr_host_address = IPv6CidrHostModel(ipv6_cidr_host="2001:db8::1/64")
    except ValueError as err:
        # Handle the error
    ```

    """

    ipv6_cidr_host: str = Field(
        ...,
        description="CIDR-format IPv6 host address, e.g. 2001:db8::1/64",
    )

    @field_validator("ipv6_cidr_host")
    @classmethod
    def validate(cls, value: str) -> str:
        """
        Validate that the input is a valid IPv6 CIDR-format host address
        and that it is NOT a network address.

        Note: Broadcast addresses are accepted as valid.
        """
        # Validate the address part
        try:
            result = validate_ipv6_cidr_host(value)
        except ValueError as error:
            msg = f"Invalid CIDR-format IPv6 host address: {value}. "
            msg += f"detail: {error}"
            raise ValueError(msg) from error

        if result is True:
            # Valid CIDR-format IPv6 host address
            return value
        msg = f"Invalid CIDR-format IPv6 host address: {value}. "
        msg += "Are the host bits all zero?"
        raise ValueError(msg)
