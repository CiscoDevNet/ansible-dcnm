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
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import \
    SwitchIssuDetailsBySerialNumber

from .fixture import load_fixture

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

"""
controller_version: 12
description: Verify functionality of subclass SwitchIssuDetailsBySerialNumber
"""


@contextmanager
def does_not_raise():
    yield


patch_module_utils = "ansible_collections.cisco.dcnm.plugins.module_utils."
patch_image_mgmt = patch_module_utils + "image_mgmt."

dcnm_send_issu_details = patch_image_mgmt + "switch_issu_details.dcnm_send"


class MockAnsibleModule:
    params = {}

    def fail_json(msg) -> AnsibleFailJson:
        raise AnsibleFailJson(msg)


def responses_switch_issu_details(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_SwitchIssuDetails"
    response = load_fixture(response_file).get(key)
    print(f"responses_switch_issu_details: {key} : {response}")
    return response


@pytest.fixture
def issu_details():
    return SwitchIssuDetailsBySerialNumber(MockAnsibleModule)


def test_image_mgmt_switch_issu_details_by_serial_number_00001(issu_details) -> None:
    """
    Function
    - __init__

    Test
    - fail_json is not called
    - issu_details.properties is a dict
    """
    with does_not_raise():
        issu_details.__init__(MockAnsibleModule)
    assert isinstance(issu_details.properties, dict)


def test_image_mgmt_switch_issu_details_by_serial_number_00002(issu_details) -> None:
    """
    Function
    - _init_properties

    Test
    - Class properties initialized to expected values
    - issu_details.properties is a dict
    - issu_details.action_keys is a set
    - action_keys contains expected values
    """
    action_keys = {"imageStaged", "upgrade", "validated"}

    issu_details._init_properties()
    assert isinstance(issu_details.properties, dict)
    assert isinstance(issu_details.properties.get("action_keys"), set)
    assert issu_details.properties.get("action_keys") == action_keys
    assert issu_details.properties.get("response_data") == None
    assert issu_details.properties.get("response") == None
    assert issu_details.properties.get("result") == None
    assert issu_details.properties.get("serial_number") == None


def test_image_mgmt_switch_issu_details_by_serial_number_00020(
    monkeypatch, issu_details
) -> None:
    """
    Function
    - refresh

    Test
    - issu_details.response is a dict
    - issu_details.response_data is a list
    """
    key = "test_image_mgmt_switch_issu_details_by_serial_number_00020a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_issu_details: {responses_switch_issu_details(key)}")
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    issu_details.refresh()
    assert isinstance(issu_details.response, dict)
    assert isinstance(issu_details.response_data, list)


def test_image_mgmt_switch_issu_details_by_serial_number_00021(
    monkeypatch, issu_details
) -> None:
    """
    Function
    - refresh

    Test
    - Properties are set based on device_name
    - Expected property values are returned
    """
    key = "test_image_mgmt_switch_issu_details_by_serial_number_00021a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_issu_details: {responses_switch_issu_details(key)}")
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    issu_details.refresh()
    issu_details.serial_number = "FDO21120U5D"
    assert issu_details.device_name == "leaf1"
    assert issu_details.serial_number == "FDO21120U5D"
    # change serial_number to a different switch, expect different information
    issu_details.serial_number = "FDO2112189M"
    assert issu_details.device_name == "cvd-2313-leaf"
    assert issu_details.serial_number == "FDO2112189M"
    # verify remaining properties using current serial_number
    assert issu_details.eth_switch_id == 39890
    assert issu_details.fabric == "hard"
    assert issu_details.fcoe_enabled == False
    assert issu_details.group == "hard"
    # NOTE: For "id" see switch_id below
    assert issu_details.image_staged == "Success"
    assert issu_details.image_staged_percent == 100
    assert issu_details.ip_address == "172.22.150.108"
    assert issu_details.issu_allowed == None
    assert issu_details.last_upg_action == "2023-Oct-06 03:43"
    assert issu_details.mds == False
    assert issu_details.mode == "Normal"
    assert issu_details.model == "N9K-C93180YC-EX"
    assert issu_details.model_type == 0
    assert issu_details.peer == None
    assert issu_details.platform == "N9K"
    assert issu_details.policy == "KR5M"
    assert issu_details.reason == "Upgrade"
    assert issu_details.role == "leaf"
    assert issu_details.status == "In-Sync"
    assert issu_details.status_percent == 100
    # NOTE: switch_id appears in the response data as "id"
    # NOTE: "id" is a python reserved keyword, so we changed the property name
    assert issu_details.switch_id == 2
    assert issu_details.sys_name == "cvd-2313-leaf"
    assert issu_details.system_mode == "Normal"
    assert issu_details.upg_groups == None
    assert issu_details.upgrade == "Success"
    assert issu_details.upgrade_percent == 100
    assert issu_details.validated == "Success"
    assert issu_details.validated_percent == 100
    assert issu_details.version == "10.2(5)"
    # NOTE: Two vdc_id values exist in the response data for each switch.
    # NOTE: Namely, "vdcId" and "vdc_id"
    # NOTE: Properties are provided for both, as follows.
    # NOTE: vdc_id == vdcId
    # NOTE: vdc_id2 == vdc_id
    assert issu_details.vdc_id == 0
    assert issu_details.vdc_id2 == -1
    assert issu_details.vpc_peer == None
    # NOTE: Two vpc role keys exist in the response data for each switch.
    # NOTE: Namely, "vpcRole" and "vpc_role"
    # NOTE: Properties are provided for both, as follows.
    # NOTE: vpc_role == vpcRole
    # NOTE: vpc_role2 == vpc_role
    # NOTE: Values are synthesized in the response for this test
    assert issu_details.vpc_role == "FOO"
    assert issu_details.vpc_role2 == "BAR"


def test_image_mgmt_switch_issu_details_by_serial_number_00022(
    monkeypatch, issu_details
) -> None:
    """
    Function
    - refresh

    Test
    - issu_details.result is a dict
    - issu_details.result contains expected key/values for 200 RESULT_CODE
    """
    key = "test_image_mgmt_switch_issu_details_by_serial_number_00022a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_issu_details: {responses_switch_issu_details(key)}")
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    issu_details.refresh()
    assert isinstance(issu_details.result, dict)
    assert issu_details.result.get("found") == True
    assert issu_details.result.get("success") == True


def test_image_mgmt_switch_issu_details_by_serial_number_00023(
    monkeypatch, issu_details
) -> None:
    """
    Function
    - refresh

    Test
    - refresh calls handle_response, which calls json_fail on 404 response
    - Error message matches expectation
    """
    key = "test_image_mgmt_switch_issu_details_by_serial_number_00023a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_issu_details: {responses_switch_issu_details(key)}")
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    match = "Bad result when retriving switch information from the controller"
    with pytest.raises(AnsibleFailJson, match=match):
        issu_details.refresh()


def test_image_mgmt_switch_issu_details_by_serial_number_00024(
    monkeypatch, issu_details
) -> None:
    """
    Function
    - refresh

    Test
    - fail_json is called on 200 response with empty DATA key
    - Error message matches expectation
    """
    key = "test_image_mgmt_switch_issu_details_by_serial_number_00024a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    match = "SwitchIssuDetailsBySerialNumber.refresh: "
    match += "The controller has no switch ISSU information."
    with pytest.raises(AnsibleFailJson, match=match):
        issu_details.refresh()


def test_image_mgmt_switch_issu_details_by_serial_number_00025(
    monkeypatch, issu_details
) -> None:
    """
    Function
    - refresh

    Test
    - fail_json is called on 200 response with DATA.lastOperDataObject length 0
    - Error message matches expectation
    """
    key = "test_image_mgmt_switch_issu_details_by_serial_number_00025a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_issu_details: {responses_switch_issu_details(key)}")
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    match = "SwitchIssuDetailsBySerialNumber.refresh: "
    match += "The controller has no switch ISSU information."
    with pytest.raises(AnsibleFailJson, match=match):
        issu_details.refresh()


def test_image_mgmt_switch_issu_details_by_serial_number_00040(
    monkeypatch, issu_details
) -> None:
    """
    Function description:

    SwitchIssuDetailsBySerialNumber._get is called by all getter properties.
    It raises AnsibleFailJson if the user has not set serial_number or if
    serial_number is unknown, or if an unknown property name is queried.
    It returns the value of the requested property if the user has set a known
    serial_number and the property name is valid.

    Expected results:

    1.  fail_json is called with appropriate error message since an unknown
        serial_number is set.
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_switch_issu_details_by_serial_number_00040a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    issu_details.refresh()
    issu_details.serial_number = "FOO00000BAR"
    match = "SwitchIssuDetailsBySerialNumber._get: FOO00000BAR does not exist "
    match += "on the controller."
    with pytest.raises(AnsibleFailJson, match=match):
        issu_details._get("serialNumber")


def test_image_mgmt_switch_issu_details_by_serial_number_00041(
    monkeypatch, issu_details
) -> None:
    """
    Function description:

    SwitchIssuDetailsBySerialNumber._get is called by all getter properties.
    It raises AnsibleFailJson if the user has not set serial_number or if
    serial_number is unknown, or if an unknown property name is queried.
    It returns the value of the requested property if the user has set a known
    serial_number and the property name is valid.

    Expected results:

    1.  fail_json is called with appropriate error message since an unknown
        property is queried.
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_switch_issu_details_by_serial_number_00041a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    issu_details.refresh()
    issu_details.serial_number = "FDO21120U5D"
    match = "SwitchIssuDetailsBySerialNumber._get: FDO21120U5D unknown "
    match += f"property name: FOO"
    with pytest.raises(AnsibleFailJson, match=match):
        issu_details._get("FOO")
