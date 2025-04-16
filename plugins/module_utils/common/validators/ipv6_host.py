#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ipv6_host.py

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


def test_ipv6() -> None:
    """
    Tests the validate_ipv4_cidr_host function.
    """
    items: list = []
    items.append("2001::1")
    items.append("2001:20:20:20::1")
    items.append("2001:20:20:20::/64")
    items.append("10.10.10.0")
    items.append({})  # type: ignore[arg-type]
    items.append(1)  # type: ignore[arg-type]

    for ipv6 in items:
        print(f"{ipv6}: Is IPv4 host: {validate_ipv6_host(ipv6)}")


def main() -> None:
    """
    Main function to run tests.
    """
    test_ipv6()


if __name__ == "__main__":
    main()
