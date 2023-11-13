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
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_stage import \
    ImageStage
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import \
    SwitchIssuDetailsBySerialNumber

from .fixture import load_fixture

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

"""
controller_version: 12
description: Verify functionality of ImageStage
"""


@contextmanager
def does_not_raise():
    yield


patch_module_utils = "ansible_collections.cisco.dcnm.plugins.module_utils."
patch_image_mgmt = patch_module_utils + "image_mgmt."
patch_common = patch_module_utils + "common."

dcnm_send_controller_version = patch_common + "controller_version.dcnm_send"
dcnm_send_image_stage = patch_image_mgmt + "image_stage.dcnm_send"
dcnm_send_issu_details = patch_image_mgmt + "switch_issu_details.dcnm_send"


def responses_controller_version(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_ControllerVersion"
    response = load_fixture(response_file).get(key)
    print(f"responses_controller_version: {key} : {response}")
    return response


def responses_image_stage(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_ImageStage"
    response = load_fixture(response_file).get(key)
    print(f"responses_image_stage: {key} : {response}")
    return response


def responses_issu_details(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_SwitchIssuDetails"
    response = load_fixture(response_file).get(key)
    print(f"responses_issu_details: {key} : {response}")
    return response


class MockAnsibleModule:
    params = {}

    def fail_json(msg) -> AnsibleFailJson:
        raise AnsibleFailJson(msg)


@pytest.fixture
def module():
    return ImageStage(MockAnsibleModule)


@pytest.fixture
def mock_issu_details() -> SwitchIssuDetailsBySerialNumber:
    return SwitchIssuDetailsBySerialNumber(MockAnsibleModule)


def test_image_mgmt_stage_00001(module) -> None:
    """
    Function
    - __init__

    Test
    - Class attributes are initialized to expected values
    """
    module.__init__(MockAnsibleModule)
    assert module.module == MockAnsibleModule
    assert module.class_name == "ImageStage"
    assert isinstance(module.properties, dict)
    assert isinstance(module.serial_numbers_done, set)
    assert module.controller_version == None
    assert module.path == None
    assert module.verb == None
    assert module.payload == None
    assert isinstance(module.issu_detail, SwitchIssuDetailsBySerialNumber)
    assert isinstance(module.endpoints, ApiEndpoints)


def test_image_mgmt_stage_00002(module) -> None:
    """
    Function
    - _init_properties

    Test
    - Class properties are initialized to expected values
    """
    module._init_properties()
    assert isinstance(module.properties, dict)
    assert module.properties.get("response_data") == None
    assert module.properties.get("response") == None
    assert module.properties.get("result") == None
    assert module.properties.get("serial_numbers") == None
    assert module.properties.get("check_interval") == 10
    assert module.properties.get("check_timeout") == 1800


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_image_mgmt_stage_00003a", "12.1.2e"),
        ("test_image_mgmt_stage_00003b", "12.1.3b"),
    ],
)
def test_image_mgmt_stage_00003(monkeypatch, module, key, expected) -> None:
    """
    Function
    - _populate_controller_version

    Test
    - test_image_mgmt_stage_00003a -> module.controller_version == "12.1.2e"
    - test_image_mgmt_stage_00003b -> module.controller_version == "12.1.3b"

    Description
    _populate_controller_version retrieves the controller version from
    the controller.  This is used in commit() to populate the payload
    with either a misspelled "sereialNum" key/value (12.1.2e) or a
    correctly-spelled "serialNumbers" key/value (12.1.3b).
    """

    def mock_dcnm_send_controller_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_controller_version, mock_dcnm_send_controller_version)

    module._populate_controller_version()
    assert module.controller_version == expected


def test_image_mgmt_stage_00004(monkeypatch, module, mock_issu_details) -> None:
    """
    Function
    - prune_serial_numbers

    Test
    -   module.serial_numbers contains only serial numbers
        for which imageStaged == "none" (FDO2112189M, FDO211218AX, FDO211218B5)
    -   module.serial_numbers does not contain serial numbers
        for which imageStaged == "Success" (FDO211218FV, FDO211218GC)

    Description
    prune_serial_numbers removes serial numbers from the list for which
    imageStaged == "Success" (TODO: AND policy == <target_policy>)
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00004a"
        return responses_issu_details(key)

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


def test_image_mgmt_stage_00005(monkeypatch, module, mock_issu_details) -> None:
    """
    Function
    - validate_serial_numbers

    Test
    - fail_json is not called when imageStaged == "Success"
    - fail_json is called when imageStaged == "Failed"

    Description
    validate_serial_numbers checks the imageStaged status for each serial
    number and raises fail_json if imageStaged == "Failed" for any serial
    number.
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00005a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.issu_detail = mock_issu_details
    module.serial_numbers = ["FDO21120U5D", "FDO2112189M"]

    match = "Image staging is failing for the following switch: "
    match += "cvd-2313-leaf, 172.22.150.108, FDO2112189M. "
    match += "Check the switch connectivity to the controller "
    match += "and try again."
    with pytest.raises(AnsibleFailJson, match=match):
        module.validate_serial_numbers()


match_00006 = "ImageStage.commit: call instance.serial_numbers "
match_00006 += "before calling commit."


@pytest.mark.parametrize(
    "serial_numbers_is_set, expected",
    [
        (True, does_not_raise()),
        (False, pytest.raises(AnsibleFailJson, match=match_00006)),
    ],
)
def test_image_mgmt_stage_00006(
    monkeypatch, module, serial_numbers_is_set, expected
) -> None:
    """
    Function
    commit

    Test
    - fail_json is called when serial_numbers is None
    - fail_json is not called when serial_numbers is set
    """

    def mock_dcnm_send_controller_version(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00006a"
        return responses_controller_version(key)

    def mock_dcnm_send_image_stage(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00006a"
        return responses_image_stage(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00006a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_controller_version, mock_dcnm_send_controller_version)
    monkeypatch.setattr(dcnm_send_image_stage, mock_dcnm_send_image_stage)
    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    if serial_numbers_is_set:
        module.serial_numbers = ["FDO21120U5D"]
    with expected:
        module.commit()


def test_image_mgmt_stage_00007(monkeypatch, module) -> None:
    """
    Function
    - commit

    Test
    - ImageStage.verb is set to POST
    - ImageStage.path is set to:
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement/stage-image
    """

    def mock_dcnm_send_controller_version(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00007a"
        return responses_controller_version(key)

    # Needed only for the 200 return code
    def mock_dcnm_send_image_stage(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00007a"
        return responses_image_stage(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00007a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_controller_version, mock_dcnm_send_controller_version)
    monkeypatch.setattr(dcnm_send_image_stage, mock_dcnm_send_image_stage)
    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module_path = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/"
    module_path += "stagingmanagement/stage-image"

    module.serial_numbers = ["FDO21120U5D"]
    module.commit()
    assert module.path == module_path
    assert module.verb == "POST"


# test_image_mgmt_stage_00008
# test_commit_payload_serial_number_key_name (former name)


@pytest.mark.parametrize(
    "controller_version, expected_serial_number_key",
    [
        ("12.1.2e", "sereialNum"),
        ("12.1.3b", "serialNumbers"),
    ],
)
def test_image_mgmt_stage_00008(
    monkeypatch, module, controller_version, expected_serial_number_key
) -> None:
    """
    Function
    - commit

    Test
    - controller_version 12.1.2e -> key name "sereialNum" (yes, misspelled)
    - controller_version 12.1.3b -> key name "serialNumbers

    Description
    commit() will set the payload key name for the serial number
    based on the controller version, per Expected Results below
    """

    def mock_controller_version(*args, **kwargs) -> None:
        module.controller_version = controller_version

    controller_version_patch = "ansible_collections.cisco.dcnm.plugins."
    controller_version_patch += "modules.dcnm_image_upgrade."
    controller_version_patch += "ImageStage._populate_controller_version"
    monkeypatch.setattr(controller_version_patch, mock_controller_version)

    def mock_dcnm_send_image_stage(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00008a"
        return responses_image_stage(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00008a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_image_stage, mock_dcnm_send_image_stage)
    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.serial_numbers = ["FDO21120U5D"]
    module.commit()
    assert expected_serial_number_key in module.payload.keys()


def test_image_mgmt_stage_00009(monkeypatch, module, mock_issu_details) -> None:
    """
    Function
    - _wait_for_image_stage_to_complete

    Test
    -   imageStaged == "Success" for all serial numbers so
        fail_json is not called
    -   instance.serial_numbers_done is a set()
    -   instance.serial_numbers_done has length 2
    -   instance.serial_numbers_done == module.serial_numbers

    Description
    _wait_for_image_stage_to_complete looks at the imageStaged status for each
    serial number and waits for it to be "Success" or "Failed".
    In the case where all serial numbers are "Success", the module returns.
    In the case where any serial number is "Failed", the module calls fail_json.
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00009a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.issu_detail = mock_issu_details
    module.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    module.check_interval = 0
    module._wait_for_image_stage_to_complete()
    assert isinstance(module.serial_numbers_done, set)
    assert len(module.serial_numbers_done) == 2
    assert "FDO21120U5D" in module.serial_numbers_done
    assert "FDO2112189M" in module.serial_numbers_done


def test_image_mgmt_stage_00010(monkeypatch, module, mock_issu_details) -> None:
    """
    Function
    - _wait_for_image_stage_to_complete

    Test
    -   module.serial_numbers_done is a set()
    -   module.serial_numbers_done has length 1
    -   module.serial_numbers_done contains FDO21120U5D
        because imageStaged is "Success"
    -   fail_json is called on serial number FDO2112189M
        because imageStaged is "Failed"
    -   error message matches expected

    Description
    _wait_for_image_stage_to_complete looks at the imageStaged status for each
    serial number and waits for it to be "Success" or "Failed".
    In the case where all serial numbers are "Success", the module returns.
    In the case where any serial number is "Failed", the module calls fail_json.
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00010a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.issu_detail = mock_issu_details
    module.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    module.check_interval = 0
    match = "Seconds remaining 1800: stage image failed for "
    match += "cvd-2313-leaf, FDO2112189M, 172.22.150.108. image "
    match += "staged percent: 90"
    with pytest.raises(AnsibleFailJson, match=match):
        module._wait_for_image_stage_to_complete()
    assert isinstance(module.serial_numbers_done, set)
    assert len(module.serial_numbers_done) == 1
    assert "FDO21120U5D" in module.serial_numbers_done
    assert "FDO2112189M" not in module.serial_numbers_done


def test_image_mgmt_stage_00011(monkeypatch, module, mock_issu_details) -> None:
    """
    Function
    - _wait_for_image_stage_to_complete

    Test
    -   module.serial_numbers_done is a set()
    -   module.serial_numbers_done has length 1
    -   module.serial_numbers_done contains FDO21120U5D
        because imageStaged == "Success"
    -   module.serial_numbers_done does not contain FDO2112189M
    -   fail_json is called due to timeout because FDO2112189M
        imageStaged == "In-Progress"
    -  error message matches expected

    Description
    See test_wait_for_image_stage_to_complete for functional details.
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00011a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.issu_detail = mock_issu_details
    module.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    module.check_interval = 1
    module.check_timeout = 1

    match = "ImageStage._wait_for_image_stage_to_complete: "
    match += "Timed out waiting for image stage to complete. "
    match += "serial_numbers_done: FDO21120U5D, "
    match += "serial_numbers_todo: FDO21120U5D,FDO2112189M"

    with pytest.raises(AnsibleFailJson, match=match):
        module._wait_for_image_stage_to_complete()
    assert isinstance(module.serial_numbers_done, set)
    assert len(module.serial_numbers_done) == 1
    assert "FDO21120U5D" in module.serial_numbers_done
    assert "FDO2112189M" not in module.serial_numbers_done


# test_image_mgmt_stage_00012
# test_wait_for_current_actions_to_complete (former name)


def test_image_mgmt_stage_00012(monkeypatch, module, mock_issu_details) -> None:
    """
    Function
    - _wait_for_current_actions_to_complete

    Test
    -   instance.serial_numbers_done is a set()
    -   instance.serial_numbers_done has length 2
    -   instance.serial_numbers_done contains all serial numbers
        in instance.serial_numbers
    -   fail_json is not called

    Description
    _wait_for_current_actions_to_complete waits until staging, validation,
    and upgrade actions are complete for all serial numbers.  It calls
    SwitchIssuDetailsBySerialNumber.actions_in_progress() and expects
    this to return False.  actions_in_progress() returns True until none of
    the following keys has a value of "In-Progress":
    - imageStaged
    - upgrade
    - validated
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00012a"
        return responses_issu_details(key)

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


def test_image_mgmt_stage_00013(monkeypatch, module, mock_issu_details) -> None:
    """
    Function
    - _wait_for_current_actions_to_complete

    Test
    -   module.serial_numbers_done is a set()
    -   module.serial_numbers_done has length 1
    -   module.serial_numbers_done contains FDO21120U5D
        because imageStaged == "Success"
    -   module.serial_numbers_done does not contain FDO2112189M
    -   fail_json is called due to timeout because FDO2112189M
        imageStaged == "In-Progress"

    Description
    See test_image_mgmt_stage_00012
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00013a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.issu_detail = mock_issu_details
    module.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    module.check_interval = 1
    module.check_timeout = 1

    error_message = "ImageStage._wait_for_current_actions_to_complete: "
    error_message += "Timed out waiting for actions to complete. "
    error_message += "serial_numbers_done: FDO21120U5D, "
    error_message += "serial_numbers_todo: FDO21120U5D,FDO2112189M"
    with pytest.raises(AnsibleFailJson, match=error_message):
        module._wait_for_current_actions_to_complete()
    assert isinstance(module.serial_numbers_done, set)
    assert len(module.serial_numbers_done) == 1
    assert "FDO21120U5D" in module.serial_numbers_done
    assert "FDO2112189M" not in module.serial_numbers_done
