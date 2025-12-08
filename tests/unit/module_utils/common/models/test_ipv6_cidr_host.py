#!/usr/bin/env python
"""
Unit tests for IPv6HostCidrModel
"""
# pylint: disable=line-too-long
# mypy: disable-error-code="import-untyped"
import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.models.ipv6_cidr_host import \
    IPv6CidrHostModel

from ...common.common_utils import does_not_raise


@pytest.mark.parametrize(
    "address",
    [
        ("10.33.0.1"),
        ("2001:db8::1"),
        (100),
        ({}),
        (["2001::1/64"]),
    ],
)
def test_ipv6_cidr_host_model_00010(address) -> None:
    """
    Test IPv6CidrHostModel with invalid input
    """
    match = "1 validation error for IPv6CidrHostModel"
    with pytest.raises(ValueError) as excinfo:
        IPv6CidrHostModel(ipv6_cidr_host=address)
    assert match in str(excinfo.value)


def test_ipv6_cidr_host_model_00020() -> None:
    """
    Test IPv6HostModel with valid input
    """
    with does_not_raise():
        IPv6CidrHostModel(ipv6_cidr_host="2001:db8::1/64")
