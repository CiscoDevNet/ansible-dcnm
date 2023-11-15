# Copyright (c) 2020-2024 Cisco and/or its affiliates.
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

from __future__ import absolute_import, division, print_function

from contextlib import contextmanager
from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson

from .fixture import load_fixture
from .image_upgrade_utils import MockAnsibleModule, does_not_raise, issu_details_by_device_name_fixture

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

"""
controller_version: 12
description: Verify functionality of subclass SwitchIssuDetailsByDeviceName
"""

patch_module_utils = "ansible_collections.cisco.dcnm.plugins.module_utils."
patch_image_mgmt = patch_module_utils + "image_mgmt."

dcnm_send_issu_details = patch_image_mgmt + "switch_issu_details.dcnm_send"


def responses_switch_issu_details(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_SwitchIssuDetails"
    response = load_fixture(response_file).get(key)
    print(f"responses_switch_issu_details: {key} : {response}")
    return response


# @pytest.fixture
# def issu_details():
#     return SwitchIssuDetailsByDeviceName(MockAnsibleModule)


def test_image_mgmt_switch_issu_details_by_device_name_00001(issu_details_by_device_name) -> None:
    """
    Function
    - __init__

    Test
    - fail_json is not called
    - issu_details_by_device_name.properties is a dict
    """
    with does_not_raise():
        issu_details_by_device_name.__init__(MockAnsibleModule)
    assert isinstance(issu_details_by_device_name.properties, dict)


def test_image_mgmt_switch_issu_details_by_device_name_00002(issu_details_by_device_name) -> None:
    """
    Function
    - _init_properties

    Test
    - Class properties initialized to expected values
    - issu_details_by_device_name.properties is a dict
    - issu_details_by_device_name.action_keys is a set
    - action_keys contains expected values
    """
    action_keys = {"imageStaged", "upgrade", "validated"}

    issu_details_by_device_name._init_properties()
    assert isinstance(issu_details_by_device_name.properties, dict)
    assert isinstance(issu_details_by_device_name.properties.get("action_keys"), set)
    assert issu_details_by_device_name.properties.get("action_keys") == action_keys
    assert issu_details_by_device_name.properties.get("response_data") == None
    assert issu_details_by_device_name.properties.get("response") == None
    assert issu_details_by_device_name.properties.get("result") == None
    assert issu_details_by_device_name.properties.get("device_name") == None


def test_image_mgmt_switch_issu_details_by_device_name_00020(
    monkeypatch, issu_details_by_device_name
) -> None:
    """
    Function
    - refresh

    Test
    - issu_details_by_device_name.response is a dict
    - issu_details_by_device_name.response_data is a list
    """
    key = "test_image_mgmt_switch_issu_details_by_device_name_00020a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_issu_details: {responses_switch_issu_details(key)}")
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    issu_details_by_device_name.refresh()
    assert isinstance(issu_details_by_device_name.response, dict)
    assert isinstance(issu_details_by_device_name.response_data, list)


def test_image_mgmt_switch_issu_details_by_device_name_00021(
    monkeypatch, issu_details_by_device_name
) -> None:
    """
    Function
    - refresh

    Test
    - Properties are set based on device_name
    - Expected property values are returned
    """
    key = "test_image_mgmt_switch_issu_details_by_device_name_00021a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_issu_details: {responses_switch_issu_details(key)}")
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    issu_details_by_device_name.refresh()
    issu_details_by_device_name.device_name = "leaf1"
    assert issu_details_by_device_name.device_name == "leaf1"
    assert issu_details_by_device_name.serial_number == "FDO21120U5D"
    # change device_name to a different switch, expect different information
    issu_details_by_device_name.device_name = "cvd-2313-leaf"
    assert issu_details_by_device_name.device_name == "cvd-2313-leaf"
    assert issu_details_by_device_name.serial_number == "FDO2112189M"
    # verify remaining properties using current device_name
    assert issu_details_by_device_name.eth_switch_id == 39890
    assert issu_details_by_device_name.fabric == "hard"
    assert issu_details_by_device_name.fcoe_enabled is False
    assert issu_details_by_device_name.group == "hard"
    # NOTE: For "id" see switch_id below
    assert issu_details_by_device_name.image_staged == "Success"
    assert issu_details_by_device_name.image_staged_percent == 100
    assert issu_details_by_device_name.ip_address == "172.22.150.108"
    assert issu_details_by_device_name.issu_allowed == None
    assert issu_details_by_device_name.last_upg_action == "2023-Oct-06 03:43"
    assert issu_details_by_device_name.mds is False
    assert issu_details_by_device_name.mode == "Normal"
    assert issu_details_by_device_name.model == "N9K-C93180YC-EX"
    assert issu_details_by_device_name.model_type == 0
    assert issu_details_by_device_name.peer == None
    assert issu_details_by_device_name.platform == "N9K"
    assert issu_details_by_device_name.policy == "KR5M"
    assert issu_details_by_device_name.reason == "Upgrade"
    assert issu_details_by_device_name.role == "leaf"
    assert issu_details_by_device_name.status == "In-Sync"
    assert issu_details_by_device_name.status_percent == 100
    # NOTE: switch_id appears in the response data as "id"
    # NOTE: "id" is a python reserved keyword, so we changed the property name
    assert issu_details_by_device_name.switch_id == 2
    assert issu_details_by_device_name.sys_name == "cvd-2313-leaf"
    assert issu_details_by_device_name.system_mode == "Normal"
    assert issu_details_by_device_name.upg_groups == None
    assert issu_details_by_device_name.upgrade == "Success"
    assert issu_details_by_device_name.upgrade_percent == 100
    assert issu_details_by_device_name.validated == "Success"
    assert issu_details_by_device_name.validated_percent == 100
    assert issu_details_by_device_name.version == "10.2(5)"
    # NOTE: Two vdc_id values exist in the response data for each switch.
    # NOTE: Namely, "vdcId" and "vdc_id"
    # NOTE: Properties are provided for both, as follows.
    # NOTE: vdc_id == vdcId
    # NOTE: vdc_id2 == vdc_id
    assert issu_details_by_device_name.vdc_id == 0
    assert issu_details_by_device_name.vdc_id2 == -1
    assert issu_details_by_device_name.vpc_peer == None
    # NOTE: Two vpc role keys exist in the response data for each switch.
    # NOTE: Namely, "vpcRole" and "vpc_role"
    # NOTE: Properties are provided for both, as follows.
    # NOTE: vpc_role == vpcRole
    # NOTE: vpc_role2 == vpc_role
    # NOTE: Values are synthesized in the response for this test
    assert issu_details_by_device_name.vpc_role == "FOO"
    assert issu_details_by_device_name.vpc_role2 == "BAR"


def test_image_mgmt_switch_issu_details_by_device_name_00022(
    monkeypatch, issu_details_by_device_name
) -> None:
    """
    Function
    - refresh

    Test
    - issu_details_by_device_name.result is a dict
    - issu_details_by_device_name.result contains expected key/values for 200 RESULT_CODE
    """
    key = "test_image_mgmt_switch_issu_details_by_device_name_00022a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_issu_details: {responses_switch_issu_details(key)}")
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    issu_details_by_device_name.refresh()
    assert isinstance(issu_details_by_device_name.result, dict)
    assert issu_details_by_device_name.result.get("found") is True
    assert issu_details_by_device_name.result.get("success") is True


def test_image_mgmt_switch_issu_details_by_device_name_00023(
    monkeypatch, issu_details_by_device_name
) -> None:
    """
    Function
    - refresh

    Test
    - refresh calls handle_response, which calls json_fail on 404 response
    - Error message matches expectation
    """
    key = "test_image_mgmt_switch_issu_details_by_device_name_00023a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    match = "Bad result when retriving switch information from the controller"
    with pytest.raises(AnsibleFailJson, match=match):
        issu_details_by_device_name.refresh()


def test_image_mgmt_switch_issu_details_by_device_name_00024(
    monkeypatch, issu_details_by_device_name
) -> None:
    """
    Function
    - refresh

    Test
    - fail_json is called on 200 response with empty DATA key
    - Error message matches expectation
    """
    key = "test_image_mgmt_switch_issu_details_by_device_name_00024a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    match = "SwitchIssuDetailsByDeviceName.refresh: "
    match += "The controller has no switch ISSU information."
    with pytest.raises(AnsibleFailJson, match=match):
        issu_details_by_device_name.refresh()


def test_image_mgmt_switch_issu_details_by_device_name_00025(
    monkeypatch, issu_details_by_device_name
) -> None:
    """
    Function
    - refresh

    Test
    - fail_json is called on 200 response with DATA.lastOperDataObject length 0
    - Error message matches expectation
    """
    key = "test_image_mgmt_switch_issu_details_by_device_name_00025a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_issu_details: {responses_switch_issu_details(key)}")
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    match = "SwitchIssuDetailsByDeviceName.refresh: "
    match += "The controller has no switch ISSU information."
    with pytest.raises(AnsibleFailJson, match=match):
        issu_details_by_device_name.refresh()


def test_image_mgmt_switch_issu_details_by_device_name_00040(
    monkeypatch, issu_details_by_device_name
) -> None:
    """
    Function
    - _get

    Test
    - fail_json is called due to unknown device_name is set
    - Error message matches expectation

    SwitchIssuDetailsByDeviceName._get is called by all getter properties.
    It raises AnsibleFailJson if the user has not set device_name or if
    device_name is unknown, or if an unknown property name is queried.
    It returns the value of the requested property if the user has set a known
    device_name.
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_switch_issu_details_by_device_name_00040a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    issu_details_by_device_name.refresh()
    issu_details_by_device_name.device_name = "FOO"
    match = "SwitchIssuDetailsByDeviceName._get: FOO does not exist "
    match += "on the controller."
    with pytest.raises(AnsibleFailJson, match=match):
        issu_details_by_device_name._get("serialNumber")


def test_image_mgmt_switch_issu_details_by_device_name_00041(
    monkeypatch, issu_details_by_device_name
) -> None:
    """
    Function
    - _get

    Test
    - fail_json is called on access of unknown property name
    - Error message matches expectation

    Description
    SwitchIssuDetailsByDeviceName._get is called by all getter properties.
    It raises AnsibleFailJson if the user has not set device_name or if
    device_name is unknown, or if an unknown property name is queried.
    It returns the value of the requested property if the user has set a known
    ip_address.
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_switch_issu_details_by_device_name_00041a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    issu_details_by_device_name.refresh()
    issu_details_by_device_name.device_name = "leaf1"
    match = "SwitchIssuDetailsByDeviceName._get: leaf1 unknown "
    match += f"property name: FOO"
    with pytest.raises(AnsibleFailJson, match=match):
        issu_details_by_device_name._get("FOO")
