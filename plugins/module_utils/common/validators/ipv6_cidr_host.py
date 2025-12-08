# -*- coding: utf-8 -*-
# @author: Allen Robel
# @file: plugins/module_utils/common/validators/ipv6_cidr_host.py
"""
Validate CIDR-format IPv6 host address
"""
import ipaddress


def validate_ipv6_cidr_host(value: str) -> bool:
    """
    # Summary

    - Return True if value is an IPv6 CIDR-format host address.
    - Return False otherwise.

    Where: value is a string representation of CIDR-format IPv6 address.

    ## Raises

    None

    ## Examples

    - value: "2001::1/128"         -> True
    - value: "2001:20:20:20::1/64" -> True
    - value: "2001:20:20:20::/64"  -> False (is a network)
    - value: 1                     -> False (is not a string)
    """
    try:
        address, prefixlen = value.split("/")
    except (AttributeError, ValueError):
        return False

    if int(prefixlen) == 128:
        # A /128 prefix length is always a host address for our purposes,
        # but the IPv4Interface module treats it as a network_address,
        # as shown below.
        #
        # >>> ipaddress.IPv6Interface("2001:20:20:20::1/128").network.network_address
        # IPv6Address('2001:20:20:20::1')
        # >>>
        return True

    try:
        network = ipaddress.IPv6Interface(value).network.network_address
    except ipaddress.AddressValueError:
        return False

    if address != str(network):
        return True
    return False
