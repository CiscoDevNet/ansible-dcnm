# -*- coding: utf-8 -*-
# @author: Allen Robel
# @file: plugins/module_utils/common/validators/ipv6_host.py
"""
Validate IPv6 host address without a prefix
"""
from ipaddress import AddressValueError, IPv6Address


def validate_ipv6_host(value: str) -> bool:
    """
    # Summary

    - Return True if value is an IPv6 host address without a prefix.
    - Return False otherwise.

    Where: value is a string representation an IPv6 address without a prefix.

    ## Raises

    None

    ## Examples

    - value: "2001::1"            -> True
    - value: "2001:20:20:20::1"   -> True
    - value: "2001:20:20:20::/64" -> False (has a prefix)
    - value: "10.10.10.0"         -> False (is not an IPv6 address)
    - value: 1                    -> False (is not an IPv6 address)
    """
    prefixlen: str = ""
    try:
        __, prefixlen = value.split("/")
    except (AttributeError, ValueError):
        if prefixlen != "":
            # prefixlen is not empty
            return False

    if isinstance(value, int):
        # value is an int and IPv6Address accepts int as a valid address.
        # We don't want to acceps int, so reject it here.
        return False

    try:
        addr = IPv6Address(value)  # pylint: disable=unused-variable
    except AddressValueError:
        return False

    return True
