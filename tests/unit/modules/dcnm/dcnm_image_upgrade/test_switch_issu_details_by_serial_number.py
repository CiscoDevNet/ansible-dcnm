# Copyright (c) 2024 Cisco and/or its affiliates.
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
# pylint: disable=unused-import
# Some fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=unused-argument


from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson

from .utils import (does_not_raise, issu_details_by_serial_number_fixture,
                    responses_ep_issu)

PATCH_MODULE_UTILS = "ansible_collections.cisco.dcnm.plugins.module_utils."
PATCH_IMAGE_UPGRADE = PATCH_MODULE_UTILS + "image_upgrade."
DCNM_SEND_ISSU_DETAILS = PATCH_IMAGE_UPGRADE + "switch_issu_details.dcnm_send"


def test_switch_issu_details_by_serial_number_00001(
    issu_details_by_serial_number,
) -> None:
    """
    Function
    - SwitchIssuDetailsBySerialNumber.__init__

    Test
    - fail_json is not called
    - instance.properties is a dict
    """
    with does_not_raise():
        instance = issu_details_by_serial_number
    assert isinstance(instance.properties, dict)


def test_switch_issu_details_by_serial_number_00002(
    issu_details_by_serial_number,
) -> None:
    """
    Function
    - SwitchIssuDetailsBySerialNumber._init_properties

    Test
    - Class properties initialized to expected values
    - instance.properties is a dict
    - instance.action_keys is a set
    - action_keys contains expected values
    """
    instance = issu_details_by_serial_number
    action_keys = {"imageStaged", "upgrade", "validated"}

    instance._init_properties()  # pylint: disable=protected-access
    assert isinstance(instance.properties, dict)
    assert isinstance(instance.properties.get("action_keys"), set)
    assert instance.properties.get("action_keys") == action_keys
    assert instance.properties.get("response_data") == []
    assert instance.properties.get("response") == []
    assert instance.properties.get("response_current") == {}
    assert instance.properties.get("result") == []
    assert instance.properties.get("result_current") == {}
    assert instance.properties.get("serial_number") is None


def test_switch_issu_details_by_serial_number_00020(
    monkeypatch, issu_details_by_serial_number
) -> None:
    """
    Function
    - SwitchIssuDetailsBySerialNumber.refresh

    Test
    - instance.response is a list
    - instance.response_current is a dict
    - instance.result is a list
    - instance.result_current is a dict
    - instance.response_data is a list
    """
    instance = issu_details_by_serial_number

    key = "test_switch_issu_details_by_serial_number_00020a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_issu_details: {responses_ep_issu(key)}")
        return responses_ep_issu(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    instance.refresh()
    assert isinstance(instance.response, list)
    assert isinstance(instance.response_current, dict)
    assert isinstance(instance.result, list)
    assert isinstance(instance.result_current, dict)
    assert isinstance(instance.response_data, list)


def test_switch_issu_details_by_serial_number_00021(
    monkeypatch, issu_details_by_serial_number
) -> None:
    """
    Function
    - SwitchIssuDetailsBySerialNumber.refresh

    Test
    - Properties are set based on device_name
    - Expected property values are returned
    """
    instance = issu_details_by_serial_number

    key = "test_switch_issu_details_by_serial_number_00021a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_ep_issu(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    instance.refresh()
    instance.filter = "FDO21120U5D"
    assert instance.device_name == "leaf1"
    assert instance.serial_number == "FDO21120U5D"
    # change serial_number to a different switch, expect different information
    instance.filter = "FDO2112189M"
    assert instance.device_name == "cvd-2313-leaf"
    assert instance.serial_number == "FDO2112189M"
    # verify remaining properties using current serial_number
    assert instance.eth_switch_id == 39890
    assert instance.fabric == "hard"
    assert instance.fcoe_enabled is False
    assert instance.group == "hard"
    # NOTE: For "id" see switch_id below
    assert instance.image_staged == "Success"
    assert instance.image_staged_percent == 100
    assert instance.ip_address == "172.22.150.108"
    assert instance.issu_allowed is None
    assert instance.last_upg_action == "2023-Oct-06 03:43"
    assert instance.mds is False
    assert instance.mode == "Normal"
    assert instance.model == "N9K-C93180YC-EX"
    assert instance.model_type == 0
    assert instance.peer is None
    assert instance.platform == "N9K"
    assert instance.policy == "KR5M"
    assert instance.reason == "Upgrade"
    assert instance.role == "leaf"
    assert instance.status == "In-Sync"
    assert instance.status_percent == 100
    # NOTE: switch_id appears in the response data as "id"
    # NOTE: "id" is a python reserved keyword, so we changed the property name
    assert instance.switch_id == 2
    assert instance.sys_name == "cvd-2313-leaf"
    assert instance.system_mode == "Normal"
    assert instance.upg_groups is None
    assert instance.upgrade == "Success"
    assert instance.upgrade_percent == 100
    assert instance.validated == "Success"
    assert instance.validated_percent == 100
    assert instance.version == "10.2(5)"
    # NOTE: Two vdc_id values exist in the response data for each switch.
    # NOTE: Namely, "vdcId" and "vdc_id"
    # NOTE: Properties are provided for both, as follows.
    # NOTE: vdc_id == vdcId
    # NOTE: vdc_id2 == vdc_id
    assert instance.vdc_id == 0
    assert instance.vdc_id2 == -1
    assert instance.vpc_peer is None
    # NOTE: Two vpc role keys exist in the response data for each switch.
    # NOTE: Namely, "vpcRole" and "vpc_role"
    # NOTE: Properties are provided for both, as follows.
    # NOTE: vpc_role == vpcRole
    # NOTE: vpc_role2 == vpc_role
    # NOTE: Values are synthesized in the response for this test
    assert instance.vpc_role == "FOO"
    assert instance.vpc_role2 == "BAR"
    assert isinstance(instance.filtered_data, dict)
    assert instance.filtered_data.get("deviceName") == "cvd-2313-leaf"


def test_switch_issu_details_by_serial_number_00022(
    monkeypatch, issu_details_by_serial_number
) -> None:
    """
    Function
    - SwitchIssuDetailsBySerialNumber.refresh

    Test
    - instance.result_current is a dict
    - instance.result_current contains expected key/values for 200 RESULT_CODE
    """
    instance = issu_details_by_serial_number

    key = "test_switch_issu_details_by_serial_number_00022a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_ep_issu(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    instance.refresh()
    assert isinstance(instance.result_current, dict)
    assert instance.result_current.get("found") is True
    assert instance.result_current.get("success") is True


def test_switch_issu_details_by_serial_number_00023(
    monkeypatch, issu_details_by_serial_number
) -> None:
    """
    Function
    - SwitchIssuDetailsBySerialNumber.refresh

    Test
    - refresh calls handle_response, which calls json_fail on 404 response
    - Error message matches expectation
    """
    instance = issu_details_by_serial_number

    key = "test_switch_issu_details_by_serial_number_00023a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_ep_issu(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    match = "Bad result when retriving switch information from the controller"
    with pytest.raises(AnsibleFailJson, match=match):
        instance.refresh()


def test_switch_issu_details_by_serial_number_00024(
    monkeypatch, issu_details_by_serial_number
) -> None:
    """
    Function
    - SwitchIssuDetailsBySerialNumber.refresh

    Test
    - fail_json is called on 200 response with empty DATA key
    - Error message matches expectation
    """
    instance = issu_details_by_serial_number

    key = "test_switch_issu_details_by_serial_number_00024a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_ep_issu(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    match = "SwitchIssuDetailsBySerialNumber.refresh_super: "
    match += "The controller has no switch ISSU information."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.refresh()


def test_switch_issu_details_by_serial_number_00025(
    monkeypatch, issu_details_by_serial_number
) -> None:
    """
    Function
    - SwitchIssuDetailsBySerialNumber.refresh

    Test
    - fail_json is called on 200 response with DATA.lastOperDataObject length 0
    - Error message matches expectation
    """
    instance = issu_details_by_serial_number

    key = "test_switch_issu_details_by_serial_number_00025a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_ep_issu(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    match = "SwitchIssuDetailsBySerialNumber.refresh_super: "
    match += "The controller has no switch ISSU information."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.refresh()


def test_switch_issu_details_by_serial_number_00040(
    monkeypatch, issu_details_by_serial_number
) -> None:
    """
    Function
    - SwitchIssuDetailsBySerialNumber._get

    Summary
    Verify that _get() calls fail_json because filter is set to an
    unknown serial_number

    Test
    - fail_json is called because filter is set to an unknown serial_number
    - Error message matches expectation

    Description
    SwitchIssuDetailsBySerialNumber._get is called by all getter properties.
    It raises AnsibleFailJson if the user has not set filter or if
    filter is unknown, or if an unknown property name is queried.
    It returns the value of the requested property if the user has filter
    to a serial_number that exists on the controller.

    Expected result:
    1.  fail_json is called with appropriate error message since filter
        is set to an unknown serial_number.
    """
    instance = issu_details_by_serial_number

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_switch_issu_details_by_serial_number_00040a"
        return responses_ep_issu(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    match = "SwitchIssuDetailsBySerialNumber._get: FOO00000BAR does not exist "
    match += "on the controller."

    instance.refresh()
    instance.filter = "FOO00000BAR"
    with pytest.raises(AnsibleFailJson, match=match):
        instance._get("serialNumber")  # pylint: disable=protected-access


def test_switch_issu_details_by_serial_number_00041(
    monkeypatch, issu_details_by_serial_number
) -> None:
    """
    Function
    SwitchIssuDetailsBySerialNumber._get

    Summary
    Verify that _get() calls fail_json because an unknown property is queried

    Test
    - fail_json is called on access of unknown property name
    - Error message matches expectation

    Description
    SwitchIssuDetailsBySerialNumber._get is called by all getter properties.
    It raises AnsibleFailJson if the user has not set filter or if
    filter is unknown, or if an unknown property name is queried.
    It returns the value of the requested property if the user has filter
    to a serial_number that exists on the controller.

    Expected results
    1.  fail_json is called with appropriate error message since an unknown
        property is queried.
    """
    instance = issu_details_by_serial_number

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_switch_issu_details_by_serial_number_00041a"
        return responses_ep_issu(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    match = "SwitchIssuDetailsBySerialNumber._get: FDO21120U5D unknown "
    match += "property name: FOO"

    instance.refresh()
    instance.filter = "FDO21120U5D"
    with pytest.raises(AnsibleFailJson, match=match):
        instance._get("FOO")  # pylint: disable=protected-access


def test_switch_issu_details_by_serial_number_00042(
    issu_details_by_serial_number,
) -> None:
    """
    Function
    - SwitchIssuDetailsBySerialNumber._get

    Test
    - _get() calls fail_json because instance.filter is not set
    - Error message matches expectation

    Description
    SwitchIssuDetailsBySerialNumber._get is called by all getter properties.
    It raises AnsibleFailJson if the user has not set filter or if
    filter is unknown, or if an unknown property name is queried.
    It returns the value of the requested property if the user has filter
    to a serial_number that exists on the controller.
    """
    with does_not_raise():
        instance = issu_details_by_serial_number
    match = r"SwitchIssuDetailsBySerialNumber\._get: "
    match += r"set instance\.filter to a switch serialNumber "
    match += r"before accessing property role\."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.role
