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

from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_validate import \
    ImageValidate
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import \
    SwitchIssuDetailsBySerialNumber

from .fixture import load_fixture

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

"""
controller_version: 12
description: Verify functionality of ImageValidate
"""

patch_module_utils = "ansible_collections.cisco.dcnm.plugins.module_utils."
patch_image_mgmt = patch_module_utils + "image_mgmt."

dcnm_send_issu_details = patch_image_mgmt + "switch_issu_details.dcnm_send"


def response_data_issu_details(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_SwitchIssuDetails"
    response = load_fixture(response_file).get(key)
    print(f"response_data_issu_details: {key} : {response}")
    return response


class MockAnsibleModule:
    params = {}

    def fail_json(msg) -> AnsibleFailJson:
        raise AnsibleFailJson(msg)


@pytest.fixture
def module():
    return ImageValidate(MockAnsibleModule)


@pytest.fixture
def mock_issu_details() -> SwitchIssuDetailsBySerialNumber:
    return SwitchIssuDetailsBySerialNumber(MockAnsibleModule)


def test_image_mgmt_validate_00001(module) -> None:
    """
    Function
    - __init__

    Test
    - Class attributes are initialized to expected values
    """
    module.__init__(MockAnsibleModule)
    assert module.class_name == "ImageValidate"
    assert isinstance(module.endpoints, ApiEndpoints)
    assert isinstance(module.issu_detail, SwitchIssuDetailsBySerialNumber)


def test_image_mgmt_validate_00002(module) -> None:
    """
    Function
    - _init_properties

    Test
    - Class properties are initialized to expected values
    """
    module._init_properties()
    assert isinstance(module.properties, dict)
    assert module.properties.get("check_interval") == 10
    assert module.properties.get("check_timeout") == 1800
    assert module.properties.get("response_data") == {}
    assert module.properties.get("response") == {}
    assert module.properties.get("result") == {}
    assert module.properties.get("non_disruptive") == False
    assert module.properties.get("serial_numbers") == []


def test_image_mgmt_validate_00003(monkeypatch, module, mock_issu_details) -> None:
    """
    Function
    - prune_serial_numbers

    Test
    -   module.serial_numbers contains only serial numbers for which
        "validated" == "none"
    -   serial_numbers does not contain serial numbers for which
        "validated" == "Success"

    Description
    prune_serial_numbers removes serial numbers from the list for which
    "validated" == "Success" (TODO: AND policy == <target_policy>)

    Expected results:
    1. module.serial_numbers == ["FDO2112189M", "FDO211218AX", "FDO211218B5"]
    2. module.serial_numbers != ["FDO211218FV", "FDO211218GC"]
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_validate_00003a"
        return response_data_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.issu_detail = mock_issu_details
    module.serial_numbers = [
        "FDO2112189M",
        "FDO211218AX",
        "FDO211218B5",
        "FDO211218FV",
        "FDO211218GC",
    ]
    module.prune_serial_numbers()
    assert isinstance(module.serial_numbers, list)
    assert len(module.serial_numbers) == 3
    assert "FDO2112189M" in module.serial_numbers
    assert "FDO211218AX" in module.serial_numbers
    assert "FDO211218B5" in module.serial_numbers
    assert "FDO211218FV" not in module.serial_numbers
    assert "FDO211218GC" not in module.serial_numbers


# test_image_mgmt_validate_00004
# test_validate_serial_numbers_failed (former name)


def test_image_mgmt_validate_00004(monkeypatch, module, mock_issu_details) -> None:
    """
    Function
    - validate_serial_numbers

    Test
    - fail_json is called when imageStaged == "Failed".
    - fail_json error message is matched

    Expectations:

    FDO21120U5D should pass since validated == "Success"
    FDO2112189M should fail since validated == "Failed"
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_validate_00004a"
        return response_data_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.issu_detail = mock_issu_details
    module.serial_numbers = ["FDO21120U5D", "FDO2112189M"]

    match = "ImageValidate.validate_serial_numbers: "
    match += "image validation is failing for the following switch: "
    match += "cvd-2313-leaf, 172.22.150.108, FDO2112189M. If this "
    match += "persists, check the switch connectivity to the "
    match += "controller and try again."
    with pytest.raises(AnsibleFailJson, match=match):
        module.validate_serial_numbers()


def test_image_mgmt_validate_00005(monkeypatch, module, mock_issu_details) -> None:
    """
    Function
    - _wait_for_image_validate_to_complete

    Test
    - serial_numbers_done is a set()
    - serial_numbers_done has length 2
    - serial_numbers_done contains all serial numbers in instance.serial_numbers
    - fail_json is not called

    Description
    _wait_for_image_validate_to_complete looks at the "validated" status for each
    serial number and waits for it to be "Success" or "Failed".
    In the case where all serial numbers are "Success", the module returns.
    In the case where any serial number is "Failed", the module calls fail_json.
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_validate_00005a"
        return response_data_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.issu_detail = mock_issu_details
    module.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    module.check_interval = 0
    module._wait_for_image_validate_to_complete()
    assert isinstance(module.serial_numbers_done, set)
    assert len(module.serial_numbers_done) == 2
    assert "FDO21120U5D" in module.serial_numbers_done
    assert "FDO2112189M" in module.serial_numbers_done


# test_image_mgmt_validate_00006
# test_wait_for_image_validate_to_complete_validate_failed (former name)


def test_image_mgmt_validate_00006(monkeypatch, module, mock_issu_details) -> None:
    """
    Function
    - _wait_for_image_validate_to_complete

    Test
    - serial_numbers_done is a set()
    - serial_numbers_done has length 1
    - serial_numbers_done contains FDO21120U5D since "validated" == "Success"
    - serial_numbers_done does not contain FDO2112189M since "validated" == "Failed"
    - fail_json is called
    - fail_json error message is matched

    Description
    _wait_for_image_validate_to_complete looks at the "validated" status for each
    serial number and waits for it to be "Success" or "Failed".
    In the case where all serial numbers are "Success", the module returns.
    In the case where any serial number is "Failed", the module calls fail_json.
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_validate_00006a"
        return response_data_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.issu_detail = mock_issu_details
    module.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    module.check_interval = 0
    match = "Seconds remaining 1800: validate image Failed for "
    match += "cvd-2313-leaf, 172.22.150.108, FDO2112189M, "
    match += "image validated percent: 100. Check the switch e.g. "
    match += "show install log detail, show incompatibility-all nxos "
    match += "<image>.  Or check Operations > Image Management > "
    match += "Devices > View Details > Validate on the controller "
    match += "GUI for more details."
    with pytest.raises(AnsibleFailJson, match=match):
        module._wait_for_image_validate_to_complete()
    assert isinstance(module.serial_numbers_done, set)
    assert len(module.serial_numbers_done) == 1
    assert "FDO21120U5D" in module.serial_numbers_done
    assert "FDO2112189M" not in module.serial_numbers_done


def test_image_mgmt_validate_00007(monkeypatch, module, mock_issu_details) -> None:
    """
    Function
    - _wait_for_image_validate_to_complete

    Test
    - serial_numbers_done is a set()
    - serial_numbers_done has length 1
    - serial_numbers_done contains FDO21120U5D since "validated" == "Success"
    - serial_numbers_done does not contain FDO2112189M since "validated" == "In-Progress"
    - fail_json is called due to timeout
    - fail_json error message is matched

    Description
    See test_wait_for_image_stage_to_complete for functional details.
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_validate_00007a"
        return response_data_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.issu_detail = mock_issu_details
    module.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    module.check_interval = 1
    module.check_timeout = 1

    error_message = "ImageValidate._wait_for_image_validate_to_complete: "
    error_message += "Timed out waiting for image validation to complete. "
    error_message += "serial_numbers_done: FDO21120U5D, "
    error_message += "serial_numbers_todo: FDO21120U5D,FDO2112189M"
    with pytest.raises(AnsibleFailJson, match=error_message):
        module._wait_for_image_validate_to_complete()
    assert isinstance(module.serial_numbers_done, set)
    assert len(module.serial_numbers_done) == 1
    assert "FDO21120U5D" in module.serial_numbers_done
    assert "FDO2112189M" not in module.serial_numbers_done


def test_image_mgmt_validate_00008(monkeypatch, module, mock_issu_details) -> None:
    """
    Function
    - _wait_for_current_actions_to_complete

    Test
    - serial_numbers_done is a set()
    - serial_numbers_done has length 2
    - serial_numbers_done contains all serial numbers in
      serial_numbers
    - fail_json is not called

    Description
    _wait_for_current_actions_to_complete waits until staging, validation,
    and upgrade actions are complete for all serial numbers.  It calls
    SwitchIssuDetailsBySerialNumber.actions_in_progress() and expects
    this to return False.  actions_in_progress() returns True until none of
    the following keys has a value of "In-Progress":

    ["imageStaged", "upgrade", "validated"]
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_validate_00008a"
        return response_data_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.issu_detail = mock_issu_details
    module.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    module.check_interval = 0
    module._wait_for_current_actions_to_complete()
    assert isinstance(module.serial_numbers_done, set)
    assert len(module.serial_numbers_done) == 2
    assert "FDO21120U5D" in module.serial_numbers_done
    assert "FDO2112189M" in module.serial_numbers_done


def test_image_mgmt_validate_00009(monkeypatch, module, mock_issu_details) -> None:
    """
    Function
    - _wait_for_current_actions_to_complete

    Test
    - serial_numbers_done is a set()
    - serial_numbers_done has length 1
    - serial_numbers_done contains FDO21120U5D since "validated" == "Success"
    - serial_numbers_done does not contain FDO2112189M since "validated" == "In-Progress"
    - fail_json is called due to timeout
    - fail_json error message is matched

    Description
    See test_wait_for_current_actions_to_complete for functional details.
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_validate_00009a"
        return response_data_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.issu_detail = mock_issu_details
    module.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    module.check_interval = 1
    module.check_timeout = 1

    match = "ImageValidate._wait_for_current_actions_to_complete: "
    match += "Timed out waiting for actions to complete. "
    match += "serial_numbers_done: FDO21120U5D, "
    match += "serial_numbers_todo: FDO21120U5D,FDO2112189M"
    with pytest.raises(AnsibleFailJson, match=match):
        module._wait_for_current_actions_to_complete()
    assert isinstance(module.serial_numbers_done, set)
    assert len(module.serial_numbers_done) == 1
    assert "FDO21120U5D" in module.serial_numbers_done
    assert "FDO2112189M" not in module.serial_numbers_done
