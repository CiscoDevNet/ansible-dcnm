#!/usr/bin/env python
# -*- coding: utf-8 -*-
# mypy: disable-error-code="import-untyped"
"""
@file   : ipv4_host.py
@Author : Allen Robel
"""
PYDANTIC_IMPORT_ERROR: ImportError | None

try:
    from pydantic import BaseModel, Field, field_validator
except ImportError as pydantic_import_error:
    PYDANTIC_IMPORT_ERROR = pydantic_import_error
else:
    PYDANTIC_IMPORT_ERROR = None

from ..validators.ipv4_host import validate_ipv4_host

if not PYDANTIC_IMPORT_ERROR:

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
            msg = f"Invalid IPv4 host address: {value}."
            raise ValueError(msg)
