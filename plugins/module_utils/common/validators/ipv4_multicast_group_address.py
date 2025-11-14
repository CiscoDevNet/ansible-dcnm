# -*- coding: utf-8 -*-
# @author: Allen Robel
# @file: plugins/module_utils/common/validators/ipv4_host.py
"""
Validate IPv4 host address without a prefix
"""
from ipaddress import AddressValueError, IPv4Address


def validate_ipv4_multicast_group_address(value: str) -> bool:
    """
    # Summary

    - Return True if value is an IPv4 multicast group address without prefix.
    - Return False otherwise.

    Where: value is a string representation an IPv4 multicast group address without prefix.

    ## Raises

    None

    ## Examples

    - value: "224.10.10.1"     -> True
    - value: "224.10.10.1/24"  -> False (contains prefix)
    - value: "10.10.10.81/28" -> False
    - value: "10.10.10.0"     -> False
    - value: 1                -> False (is not a string)
    """
    prefixlen: str = ""  # pylint: disable=unused-variable
    try:
        __, prefixlen = value.split("/")
    except (AttributeError, ValueError):
        pass

    if isinstance(value, int):
        # value is an int and IPv4Address accepts int as a valid address.
        # We don't want to acceps int, so reject it here.
        return False

    try:
        addr = IPv4Address(value)
    except AddressValueError:
        return False
    if not addr.is_multicast:
        return False

    return True
