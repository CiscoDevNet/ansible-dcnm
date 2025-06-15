# Copyright (c) 2025 Cisco and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Test cases for PlaybookVrfModelV12 and PlaybookVrfConfigModelV12.
"""
from typing import Union

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.vrf.model_playbook_vrf_v12 import (
    PlaybookVrfConfigModelV12, PlaybookVrfLiteModel, PlaybookVrfModelV12)

from ..common.common_utils import does_not_raise
from .fixtures.load_fixture import playbooks


def test_full_config_00000() -> None:
    """
    Test PlaybookVrfConfigModelV12 with JSON representing the structure passed to a playbook.

    The remaining tests will use the structure associated with PlaybookVrfModelV12 for simplicity.
    """
    playbook = playbooks("playbook_full_config")
    with does_not_raise():
        instance = PlaybookVrfConfigModelV12(**playbook)
    assert instance.config[0].vrf_name == "ansible-vrf-int1"


@pytest.mark.parametrize(
    "value, expected",
    [
        ("ansible-vrf-int1", True),
        ("vrf_5678901234567890123456789012", True),  # Valid, exactly 32 characters
        (123, False),  # Invalid, int
        ("vrf_56789012345678901234567890123", False),  # Invalid, longer than 32 characters
    ],
)
def test_vrf_name_00000(value: Union[str, int], expected: bool) -> None:
    """
    Test the validation of VRF names.

    :param value: The VRF name to validate.
    :param expected: Expected result of the validation.
    """
    playbook = playbooks("playbook_as_dict")
    playbook["vrf_name"] = value
    if expected:
        with does_not_raise():
            instance = PlaybookVrfModelV12(**playbook)
            assert instance.vrf_name == value
    else:
        with pytest.raises(ValueError):
            PlaybookVrfModelV12(**playbook)


@pytest.mark.parametrize(
    "value, expected, valid",
    [
        ("1", "1", True),
        ("4094", "4094", True),
        (1, "1", True),
        (4094, "4094", True),
        ("0", "", True),
        (0, "", True),
        ("4095", None, False),
        (4095, None, False),
        ("-1", None, False),
        ("abc", None, False),
    ],
)
def test_vrf_lite_00000(value: Union[str, int], expected: str, valid: bool) -> None:
    """
    vrf_lite.dot1q validation.

    :param value: The dot1q value to validate.
    :param expected: Expected value after model conversion (None for no expectation).
    :param valid: Whether the value is valid or not.
    """
    playbook = playbooks("vrf_lite")
    playbook["dot1q"] = value
    if valid:
        with does_not_raise():
            instance = PlaybookVrfLiteModel(**playbook)
            assert instance.dot1q == expected
    else:
        with pytest.raises(ValueError):
            PlaybookVrfLiteModel(**playbook)


@pytest.mark.parametrize(
    "value, expected, valid",
    [
        ("10.1.1.1/24", "10.1.1.1/24", True),
        ("168.1.1.1/30", "168.1.1.1/30", True),
        ("172.1.1.1/30", "172.1.1.1/30", True),
        # ("255.255.255.255/30", None, False), TODO: this should not be valid, but currently is
        ("172.1.1.", None, False),
        ("255.255.255.255", None, False),
        ("2010::10:34:0:7", None, False),
        ("2010::10:34:0:7/64", None, False),
        (1, None, False),
        ("abc", None, False),
    ],
)
def test_vrf_lite_00010(value: Union[str, int], expected: str, valid: bool) -> None:
    """
    vrf_lite.ipv4_addr validation.

    :param value: ipv4_addr value to validate.
    :param expected: Expected value after model conversion or validation (None for no expectation).
    :param valid: Whether the value is valid or not.
    """
    playbook = playbooks("vrf_lite")
    playbook["ipv4_addr"] = value
    if valid:
        with does_not_raise():
            instance = PlaybookVrfLiteModel(**playbook)
            assert instance.ipv4_addr == expected
    else:
        with pytest.raises(ValueError):
            PlaybookVrfLiteModel(**playbook)
