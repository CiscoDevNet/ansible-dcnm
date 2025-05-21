# -*- coding: utf-8 -*-
# @author: Allen Robel
# @file: plugins/module_utils/common/validators/ipv4_host.py
"""
Validate IPv4 host address without a prefix
"""
from ipaddress import AddressValueError, IPv4Address


def validate_ipv4_host(value: str) -> bool:
    """
    # Summary

    - Return True if value is an IPv4 host address without a prefix.
    - Return False otherwise.

    Where: value is a string representation an IPv4 address without a prefix.

    ## Raises

    None

    ## Examples

    - value: "10.10.10.1"     -> True
    - value: "10.10.10.81/28" -> False
    - value: "10.10.10.0"     -> True
    - value: 1                -> False (is not a string)
    """
    prefixlen: str = ""
    try:
        __, prefixlen = value.split("/")
    except (AttributeError, ValueError):
        pass

    if isinstance(value, int):
        # value is an int and IPv4Address accepts int as a valid address.
        # We don't want to acceps int, so reject it here.
        return False

    try:
        addr = IPv4Address(value)  # pylint: disable=unused-variable
    except AddressValueError:
        return False

    return True
