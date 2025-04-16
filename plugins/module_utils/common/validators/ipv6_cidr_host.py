#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ipv6_cidr_host.py

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
        # A /128 prefix length is always a host address for our purposees,
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


def test_ipv6() -> None:
    """
    Tests the validate_ipv6_cidr_host function.
    """
    ipv6_items: list = []
    ipv6_items.append("2001:20:20:20::/64")
    ipv6_items.append("2001:20:20:20::1/64")
    ipv6_items.append("2001::1/128")
    ipv6_items.append("10.1.1.1/32")
    ipv6_items.append({})  # type: ignore[arg-type]
    ipv6_items.append(1)  # type: ignore[arg-type]

    for ip in ipv6_items:
        print(f"{ip}: Is IPv4 host: {validate_ipv6_cidr_host(ip)}")


def main() -> None:
    """
    Main function to run tests.
    """
    test_ipv6()


if __name__ == "__main__":
    main()
