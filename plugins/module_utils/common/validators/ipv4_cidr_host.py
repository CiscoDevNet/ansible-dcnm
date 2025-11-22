# -*- coding: utf-8 -*-
# @author: Allen Robel
# @file: plugins/module_utils/common/validators/ipv4_cidr_host.py
"""
Validate CIDR-format IPv4 host address
"""
import ipaddress


def validate_ipv4_cidr_host(value: str) -> bool:
    """
    # Summary

    - Return True if value is an IPv4 CIDR-format host address.
    - Return False otherwise.

    Where: value is a string representation of CIDR-format IPv4 address.

    ## Raises

    None

    ## Examples

    - value: "10.10.10.1/24"  -> True
    - value: "10.10.10.81/28" -> True
    - value: "10.10.10.80/28" -> False (is a network)
    - value: 1                -> False (is not a string)
    """
    try:
        address, prefixlen = value.split("/")
    except (AttributeError, ValueError):
        return False

    if int(prefixlen) == 32:
        # A /32 prefix length is always a host address for our purposes,
        # but the IPv4Interface module treats it as a network_address,
        # as shown below.
        #
        # >>> ipaddress.IPv4Interface("10.1.1.1/32").network.network_address
        # IPv4Address('10.1.1.1')
        # >>>
        return True

    try:
        network = ipaddress.IPv4Interface(value).network.network_address
    except ipaddress.AddressValueError:
        return False

    if address != str(network):
        return True
    return False
