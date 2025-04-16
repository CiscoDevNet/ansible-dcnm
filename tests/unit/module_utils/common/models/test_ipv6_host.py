#!/usr/bin/env python
"""
Unit tests for IPv6HostModel
"""
# pylint: disable=line-too-long
# mypy: disable-error-code="import-untyped"
import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.models.ipv6_host import \
    IPv6HostModel

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
def test_ipv6_host_model_00010(address) -> None:
    """
    Test IPv6HostModel with invalid input
    """
    match = "1 validation error for IPv6HostModel"
    with pytest.raises(ValueError) as excinfo:
        IPv6HostModel(ipv6_host=address)
    assert match in str(excinfo.value)


def test_ipv6_host_model_00020() -> None:
    """
    Test IPv6HostModel with valid input
    """
    with does_not_raise():
        IPv6HostModel(ipv6_host="2001:db8::1")
