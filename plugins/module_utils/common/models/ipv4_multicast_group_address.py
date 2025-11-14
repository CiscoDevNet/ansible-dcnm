# -*- coding: utf-8 -*-
# @author: Allen Robel
# @file: plugins/module_utils/common/models/ipv4_host.py
"""
Validate IPv4 host address.
"""
from pydantic import BaseModel, Field, field_validator

from ..validators.ipv4_multicast_group_address import validate_ipv4_multicast_group_address


class IPv4MulticastGroupModel(BaseModel):
    """
    # Summary

    Model to validate an IPv4 multicast group address without prefix.

    ## Raises

    - ValueError: If the input is not a valid IPv4 multicast group address.

    ## Example usage

    ```python
    try:
        ipv4_multicast_group_address = IPv4MulticastGroupModel(ipv4_multicast_group="224.1.1.1")
    except ValueError as err:
        # Handle the error
    ```

    """

    ipv4_multicast_group: str = Field(
        ...,
        description="IPv4 multicast group address without prefix e.g. 224.1.1.1",
    )

    @field_validator("ipv4_multicast_group")
    @classmethod
    def validate(cls, value: str) -> str:
        """
        Validate that the input is a valid IPv4 multicast group address
        """
        # Validate the address part
        try:
            result = validate_ipv4_multicast_group_address(value)
        except ValueError as error:
            msg = f"Invalid IPv4 multicast group address: {value}. "
            msg += f"detail: {error}"
            raise ValueError(msg) from error

        if result is True:
            # Valid IPv4 multicast group address
            return value
        msg = f"Invalid IPv4 multicast group address: {value}."
        raise ValueError(msg)
