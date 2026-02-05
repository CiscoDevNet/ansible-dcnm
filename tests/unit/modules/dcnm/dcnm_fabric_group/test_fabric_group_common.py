# Copyright (c) 2025-2026 Cisco and/or its affiliates.
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

# See the following regarding *_fixture imports
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html
# Due to the above, we also need to disable unused-import
# Also, fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=unused-import
# pylint: disable=redefined-outer-name
# pylint: disable=protected-access
# pylint: disable=unused-argument
# pylint: disable=unused-variable
# pylint: disable=invalid-name
# pylint: disable=line-too-long
"""
Unit tests for FabricGroupCommon class in module_utils/fabric_group/common.py
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2025 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import inspect

import pytest
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric_group.utils import (
    does_not_raise,
    fabric_group_common_fixture,
    payloads_fabric_group_common,
)


def test_fabric_group_common_00010(fabric_group_common) -> None:
    """
    # Summary

    Verify the class attributes are initialized to expected values.

    ## Test

    - Class attributes are initialized to expected values
    - `ValueError` is not called

    ## Classes and Methods

    - FabricGroupCommon.__init__()
    """
    with does_not_raise():
        instance = fabric_group_common
    assert instance.class_name == "FabricGroupCommon"
    assert instance._fabric_type == "VXLAN_EVPN"
    assert instance._payloads_to_commit == []


def test_fabric_group_common_00020(fabric_group_common) -> None:
    """
    # Summary

    Verify `_fixup_anycast_gw_mac` translates MAC at top level.

    ## Test

    - ANYCAST_GW_MAC at top level is translated from Unix format
      (00:11:22:33:44:55) to Cisco format (0011.2233.4455)
    - `ValueError` is not raised

    ## Classes and Methods

    - FabricGroupCommon.__init__()
    - FabricGroupCommon._fixup_anycast_gw_mac()
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = fabric_group_common
        instance._payloads_to_commit = payloads_fabric_group_common(key)
        instance._fixup_anycast_gw_mac()

    assert instance._payloads_to_commit[0]["ANYCAST_GW_MAC"] == "0011.2233.4455"


def test_fabric_group_common_00021(fabric_group_common) -> None:
    """
    # Summary

    Verify `_fixup_anycast_gw_mac` translates MAC in nvPairs (MCFG fabric).

    ## Test

    - ANYCAST_GW_MAC in nvPairs is translated from Unix format
      (aa:bb:cc:dd:ee:ff) to Cisco format (aabb.ccdd.eeff)
    - `ValueError` is not raised
    - This tests the fix for GitHub issue #606

    ## Classes and Methods

    - FabricGroupCommon.__init__()
    - FabricGroupCommon._fixup_anycast_gw_mac()
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = fabric_group_common
        instance._payloads_to_commit = payloads_fabric_group_common(key)
        instance._fixup_anycast_gw_mac()

    assert instance._payloads_to_commit[0]["nvPairs"]["ANYCAST_GW_MAC"] == "aabb.ccdd.eeff"


def test_fabric_group_common_00022(fabric_group_common) -> None:
    """
    # Summary

    Verify `ValueError` is raised when ANYCAST_GW_MAC at top level is malformed.

    ## Test

    - ANYCAST_GW_MAC at top level has invalid format
    - `ValueError` is raised with appropriate error message

    ## Classes and Methods

    - FabricGroupCommon.__init__()
    - FabricGroupCommon._fixup_anycast_gw_mac()
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = fabric_group_common
        instance._payloads_to_commit = payloads_fabric_group_common(key)

    match = r"FabricGroupCommon\._fixup_anycast_gw_mac: "
    match += "Error translating ANYCAST_GW_MAC for fabric f1, "
    match += r"ANYCAST_GW_MAC: 00\.54, Error detail: Invalid MAC address"
    with pytest.raises(ValueError, match=match):
        instance._fixup_anycast_gw_mac()


def test_fabric_group_common_00023(fabric_group_common) -> None:
    """
    # Summary

    Verify `ValueError` is raised when ANYCAST_GW_MAC in nvPairs is malformed.

    ## Test

    - ANYCAST_GW_MAC in nvPairs has invalid format
    - `ValueError` is raised with appropriate error message
    - This tests error handling for the fix for GitHub issue #606

    ## Classes and Methods

    - FabricGroupCommon.__init__()
    - FabricGroupCommon._fixup_anycast_gw_mac()
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = fabric_group_common
        instance._payloads_to_commit = payloads_fabric_group_common(key)

    match = r"FabricGroupCommon\._fixup_anycast_gw_mac: "
    match += "Error translating ANYCAST_GW_MAC for fabric MFG1, "
    match += r"ANYCAST_GW_MAC: invalid-mac, Error detail: Invalid MAC address"
    with pytest.raises(ValueError, match=match):
        instance._fixup_anycast_gw_mac()


def test_fabric_group_common_00024(fabric_group_common) -> None:
    """
    # Summary

    Verify `_fixup_anycast_gw_mac` skips payloads without ANYCAST_GW_MAC.

    ## Test

    - Payload has no ANYCAST_GW_MAC at top level or in nvPairs
    - Method completes without error
    - Payload is unchanged

    ## Classes and Methods

    - FabricGroupCommon.__init__()
    - FabricGroupCommon._fixup_anycast_gw_mac()
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = fabric_group_common
        instance._payloads_to_commit = payloads_fabric_group_common(key)
        original_payload = instance._payloads_to_commit[0].copy()
        instance._fixup_anycast_gw_mac()

    # Verify payload is unchanged (no ANYCAST_GW_MAC was added)
    assert "ANYCAST_GW_MAC" not in instance._payloads_to_commit[0]
    assert instance._payloads_to_commit[0]["FABRIC_NAME"] == original_payload["FABRIC_NAME"]


def test_fabric_group_common_00030(fabric_group_common) -> None:
    """
    # Summary

    Verify `_fixup_deploy` removes DEPLOY from top level.

    ## Test

    - DEPLOY at top level is removed
    - `ValueError` is not raised

    ## Classes and Methods

    - FabricGroupCommon.__init__()
    - FabricGroupCommon._fixup_deploy()
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = fabric_group_common
        instance._payloads_to_commit = payloads_fabric_group_common(key)
        assert "DEPLOY" in instance._payloads_to_commit[0]
        instance._fixup_deploy()

    assert "DEPLOY" not in instance._payloads_to_commit[0]


def test_fabric_group_common_00031(fabric_group_common) -> None:
    """
    # Summary

    Verify `_fixup_deploy` removes DEPLOY from nvPairs (MCFG fabric).

    ## Test

    - DEPLOY in nvPairs is removed
    - `ValueError` is not raised
    - This tests the fix for GitHub issue #626

    ## Classes and Methods

    - FabricGroupCommon.__init__()
    - FabricGroupCommon._fixup_deploy()
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = fabric_group_common
        instance._payloads_to_commit = payloads_fabric_group_common(key)
        assert "DEPLOY" in instance._payloads_to_commit[0]["nvPairs"]
        instance._fixup_deploy()

    assert "DEPLOY" not in instance._payloads_to_commit[0]["nvPairs"]
    # Verify other nvPairs keys are preserved
    assert "ANYCAST_GW_MAC" in instance._payloads_to_commit[0]["nvPairs"]


def test_fabric_group_common_00032(fabric_group_common) -> None:
    """
    # Summary

    Verify `_fixup_deploy` removes DEPLOY from both top level and nvPairs.

    ## Test

    - DEPLOY at top level is removed
    - DEPLOY in nvPairs is removed
    - `ValueError` is not raised
    - This tests the fix for GitHub issue #626

    ## Classes and Methods

    - FabricGroupCommon.__init__()
    - FabricGroupCommon._fixup_deploy()
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = fabric_group_common
        instance._payloads_to_commit = payloads_fabric_group_common(key)
        assert "DEPLOY" in instance._payloads_to_commit[0]
        assert "DEPLOY" in instance._payloads_to_commit[0]["nvPairs"]
        instance._fixup_deploy()

    assert "DEPLOY" not in instance._payloads_to_commit[0]
    assert "DEPLOY" not in instance._payloads_to_commit[0]["nvPairs"]
    # Verify other nvPairs keys are preserved
    assert "ANYCAST_GW_MAC" in instance._payloads_to_commit[0]["nvPairs"]


def test_fabric_group_common_00033(fabric_group_common) -> None:
    """
    # Summary

    Verify `_fixup_deploy` handles payloads without DEPLOY gracefully.

    ## Test

    - Payload has no DEPLOY at top level or in nvPairs
    - Method completes without error
    - Payload is unchanged

    ## Classes and Methods

    - FabricGroupCommon.__init__()
    - FabricGroupCommon._fixup_deploy()
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = fabric_group_common
        instance._payloads_to_commit = payloads_fabric_group_common(key)
        original_payload = instance._payloads_to_commit[0].copy()
        instance._fixup_deploy()

    # Verify payload is unchanged (no DEPLOY was present)
    assert "DEPLOY" not in instance._payloads_to_commit[0]
    assert instance._payloads_to_commit[0]["FABRIC_NAME"] == original_payload["FABRIC_NAME"]
