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
from ansible_collections.cisco.dcnm.plugins.module_utils.vrf.model_playbook_vrf_v12 import PlaybookVrfConfigModelV12, PlaybookVrfModelV12

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
    "vrf_name, expected",
    [
        ("ansible-vrf-int1", True),
        ("vrf_5678901234567890123456789012", True),  # Valid, exactly 32 characters
        (123, False),  # Invalid, int
        ("vrf_56789012345678901234567890123", False),  # Invalid, longer than 32 characters
    ],
)
def test_vrf_name_00000(vrf_name: Union[str, int], expected: bool) -> None:
    """
    Test the validation of VRF names.

    :param vrf_name: The VRF name to validate.
    :param expected: Expected result of the validation.
    """
    playbook = playbooks("playbook_as_dict")
    playbook["vrf_name"] = vrf_name
    if expected:
        with does_not_raise():
            instance = PlaybookVrfModelV12(**playbook)
            assert instance.vrf_name == vrf_name
    else:
        with pytest.raises(ValueError):
            PlaybookVrfModelV12(**playbook)
