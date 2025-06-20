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
Test cases for PayloadfVrfsDeployments.
"""
import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.vrf.model_payload_vrfs_deployments import (
    PayloadfVrfsDeployments,
)

from ..common.common_utils import does_not_raise


@pytest.mark.parametrize(
    "value, expected, valid",
    [
        (["vrf2", "vrf1", "vrf3"], "vrf1,vrf2,vrf3", True),
        ([], "", True),
        (["vrf1"], "vrf1", True),
        ([1, "vrf2"], None, False),  # Invalid type in list
    ],
)
def test_vrf_payload_deployments_00000(value, expected, valid) -> None:
    """ """
    if valid:
        with does_not_raise():
            instance = PayloadfVrfsDeployments(vrf_names=value)
            assert instance.vrf_names == value
            assert instance.model_dump(by_alias=True) == {
                "vrfNames": expected
            }
    else:
        with pytest.raises(ValueError):
            PayloadfVrfsDeployments(vrf_names=value)
