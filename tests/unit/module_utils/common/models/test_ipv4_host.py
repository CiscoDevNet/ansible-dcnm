#!/usr/bin/env python
"""
Unit tests for IPv6HostModel
"""
# pylint: disable=line-too-long
# mypy: disable-error-code="import-untyped"
import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.models.ipv4_host import \
    IPv4HostModel

from ...common.common_utils import does_not_raise


@pytest.mark.parametrize(
    "address",
    [
        ("10.33.0.1"),
        ("2001:db8::1/64"),
        (100),
        ({}),
        (["2001:db8::1"]),
    ],
)
def test_ipv4_host_model_00010(address) -> None:
    """
    Test IPv4HostModel with invalid input
    """
    match = "1 validation error for IPv4HostModel"
    with pytest.raises(ValueError) as excinfo:
        IPv4HostModel(ipv6_host=address)
    assert match in str(excinfo.value)


def test_ipv4_host_model_00020() -> None:
    """
    Test IPv4HostModel with valid input
    """
    with does_not_raise():
        IPv4HostModel(ipv4_host="10.1.1.1")
