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
"""
ImageStage - unit tests
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

from typing import Any, Dict
from unittest.mock import MagicMock

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.api_endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.switch_issu_details import \
    SwitchIssuDetailsBySerialNumber

from .utils import (MockAnsibleModule, does_not_raise, image_stage_fixture,
                    issu_details_by_serial_number_fixture,
                    responses_controller_version, responses_image_stage,
                    responses_switch_issu_details)

PATCH_MODULE_UTILS = "ansible_collections.cisco.dcnm.plugins.module_utils."
PATCH_IMAGE_UPGRADE = PATCH_MODULE_UTILS + "image_upgrade."
PATCH_COMMON = PATCH_MODULE_UTILS + "common."
PATCH_IMAGE_STAGE_REST_SEND_COMMIT = PATCH_IMAGE_UPGRADE + "image_stage.RestSend.commit"
PATCH_IMAGE_STAGE_REST_SEND_RESULT_CURRENT = (
    PATCH_IMAGE_UPGRADE + "image_stage.RestSend.result_current"
)
PATCH_IMAGE_STAGE_POPULATE_CONTROLLER_VERSION = (
    "ansible_collections.cisco.dcnm.plugins.modules.dcnm_image_upgrade."
    "ImageStage._populate_controller_version"
)

DCNM_SEND_CONTROLLER_VERSION = PATCH_COMMON + "controller_version.dcnm_send"
DCNM_SEND_ISSU_DETAILS = PATCH_IMAGE_UPGRADE + "switch_issu_details.dcnm_send"


def test_image_upgrade_stage_00001(image_stage) -> None:
    """
    Function
    - __init__

    Test
    - Class attributes are initialized to expected values
    """
    instance = image_stage
    assert instance.ansible_module == MockAnsibleModule
    assert instance.class_name == "ImageStage"
    assert isinstance(instance.properties, dict)
    assert isinstance(instance.serial_numbers_done, set)
    assert instance.controller_version is None
    assert instance.payload is None
    assert isinstance(instance.issu_detail, SwitchIssuDetailsBySerialNumber)
    assert isinstance(instance.endpoints, ApiEndpoints)

    module_path = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/"
    module_path += "stagingmanagement/stage-image"
    assert instance.path == module_path
    assert instance.verb == "POST"


def test_image_upgrade_stage_00002(image_stage) -> None:
    """
    Function
    - _init_properties

    Test
    - Class properties are initialized to expected values
    """
    instance = image_stage
    assert isinstance(instance.properties, dict)
    assert instance.properties.get("response_data") == []
    assert instance.properties.get("response") == []
    assert instance.properties.get("result") == []
    assert instance.properties.get("serial_numbers") is None
    assert instance.properties.get("check_interval") == 10
    assert instance.properties.get("check_timeout") == 1800


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_image_upgrade_stage_00003a", "12.1.2e"),
        ("test_image_upgrade_stage_00003b", "12.1.3b"),
    ],
)
def test_image_upgrade_stage_00003(monkeypatch, image_stage, key, expected) -> None:
    """
    Function
    - _populate_controller_version

    Test
    - test_image_upgrade_stage_00003a -> instance.controller_version == "12.1.2e"
    - test_image_upgrade_stage_00003b -> instance.controller_version == "12.1.3b"

    Description
    _populate_controller_version retrieves the controller version from
    the controller.  This is used in commit() to populate the payload
    with either a misspelled "sereialNum" key/value (12.1.2e) or a
    correctly-spelled "serialNumbers" key/value (12.1.3b).
    """

    def mock_dcnm_send_controller_version(*args) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(DCNM_SEND_CONTROLLER_VERSION, mock_dcnm_send_controller_version)

    instance = image_stage
    instance._populate_controller_version()  # pylint: disable=protected-access
    assert instance.controller_version == expected


def test_image_upgrade_stage_00004(
    monkeypatch, image_stage, issu_details_by_serial_number
) -> None:
    """
    Function
    - prune_serial_numbers

    Summary
    Verify that prune_serial_numbers prunes serial numbers that have already
    been staged.

    Test
    -   module.serial_numbers contains only serial numbers
        for which imageStaged == "none" (FDO2112189M, FDO211218AX, FDO211218B5)
    -   module.serial_numbers does not contain serial numbers
        for which imageStaged == "Success" (FDO211218FV, FDO211218GC)

    Description
    prune_serial_numbers removes serial numbers from the list for which
    imageStaged == "Success"
    """
    key = "test_image_upgrade_stage_00004a"

    def mock_dcnm_send_switch_issu_details(*args) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_switch_issu_details)

    instance = image_stage
    instance.issu_detail = issu_details_by_serial_number
    instance.serial_numbers = [
        "FDO2112189M",
        "FDO211218AX",
        "FDO211218B5",
        "FDO211218FV",
        "FDO211218GC",
    ]
    instance.prune_serial_numbers()
    assert isinstance(instance.serial_numbers, list)
    assert len(instance.serial_numbers) == 3
    assert "FDO2112189M" in instance.serial_numbers
    assert "FDO211218AX" in instance.serial_numbers
    assert "FDO211218B5" in instance.serial_numbers
    assert "FDO211218FV" not in instance.serial_numbers
    assert "FDO211218GC" not in instance.serial_numbers


def test_image_upgrade_stage_00005(
    monkeypatch, image_stage, issu_details_by_serial_number
) -> None:
    """
    Function
    - validate_serial_numbers

    Summary
    Verify that validate_serial_numbers raises fail_json appropriately.

    Test
    - fail_json is not called when imageStaged == "Success"
    - fail_json is called when imageStaged == "Failed"

    Description
    validate_serial_numbers checks the imageStaged status for each serial
    number and raises fail_json if imageStaged == "Failed" for any serial
    number.
    """
    key = "test_image_upgrade_stage_00005a"

    def mock_dcnm_send_switch_issu_details(*args) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_switch_issu_details)

    match = "Image staging is failing for the following switch: "
    match += "cvd-2313-leaf, 172.22.150.108, FDO2112189M. "
    match += "Check the switch connectivity to the controller "
    match += "and try again."

    instance = image_stage
    instance.issu_detail = issu_details_by_serial_number
    instance.serial_numbers = ["FDO21120U5D", "FDO2112189M"]
    with pytest.raises(AnsibleFailJson, match=match):
        instance.validate_serial_numbers()


def test_image_upgrade_stage_00020(
    monkeypatch, image_stage, issu_details_by_serial_number
) -> None:
    """
    Function
    - _wait_for_image_stage_to_complete

    Summary
    Verify proper behavior of _wait_for_image_stage_to_complete when
    imageStaged is "Success" for all serial numbers.

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
    key = "test_image_upgrade_stage_00020a"

    def mock_dcnm_send_switch_issu_details(*args) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_switch_issu_details)

    with does_not_raise():
        instance = image_stage
        instance.unit_test = True
        instance.issu_detail = issu_details_by_serial_number
        instance.serial_numbers = [
            "FDO21120U5D",
            "FDO2112189M",
        ]
        instance._wait_for_image_stage_to_complete()  # pylint: disable=protected-access
    assert isinstance(instance.serial_numbers_done, set)
    assert len(instance.serial_numbers_done) == 2
    assert "FDO21120U5D" in instance.serial_numbers_done
    assert "FDO2112189M" in instance.serial_numbers_done


def test_image_upgrade_stage_00021(
    monkeypatch, image_stage, issu_details_by_serial_number
) -> None:
    """
    Function
    - _wait_for_image_stage_to_complete

    Summary
    Verify proper behavior of _wait_for_image_stage_to_complete when
    imageStaged is "Failed" for one serial number and imageStaged
    is "Success" for one serial number.

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
    key = "test_image_upgrade_stage_00021a"

    def mock_dcnm_send_switch_issu_details(*args) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_switch_issu_details)

    with does_not_raise():
        instance = image_stage
        instance.unit_test = True
        instance.issu_detail = issu_details_by_serial_number
        instance.serial_numbers = [
            "FDO21120U5D",
            "FDO2112189M",
        ]

    match = "Seconds remaining 1790: stage image failed for "
    match += "cvd-2313-leaf, FDO2112189M, 172.22.150.108. image "
    match += "staged percent: 90"
    with pytest.raises(AnsibleFailJson, match=match):
        instance._wait_for_image_stage_to_complete()  # pylint: disable=protected-access
    assert isinstance(instance.serial_numbers_done, set)
    assert len(instance.serial_numbers_done) == 1
    assert "FDO21120U5D" in instance.serial_numbers_done
    assert "FDO2112189M" not in instance.serial_numbers_done


def test_image_upgrade_stage_00022(
    monkeypatch, image_stage, issu_details_by_serial_number
) -> None:
    """
    Function
    - _wait_for_image_stage_to_complete

    Summary
    Verify proper behavior of _wait_for_image_stage_to_complete when
    timeout is reached for one serial number (i.e. imageStaged is
    "In-Progress") and imageStaged is "Success" for one serial number.

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
    key = "test_image_upgrade_stage_00022a"

    def mock_dcnm_send_switch_issu_details(*args) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_switch_issu_details)

    with does_not_raise():
        instance = image_stage
        instance.unit_test = True
        instance.issu_detail = issu_details_by_serial_number
        instance.serial_numbers = [
            "FDO21120U5D",
            "FDO2112189M",
        ]

    match = "ImageStage._wait_for_image_stage_to_complete: "
    match += "Timed out waiting for image stage to complete. "
    match += "serial_numbers_done: FDO21120U5D, "
    match += "serial_numbers_todo: FDO21120U5D,FDO2112189M"

    with pytest.raises(AnsibleFailJson, match=match):
        instance._wait_for_image_stage_to_complete()  # pylint: disable=protected-access
    assert isinstance(instance.serial_numbers_done, set)
    assert len(instance.serial_numbers_done) == 1
    assert "FDO21120U5D" in instance.serial_numbers_done
    assert "FDO2112189M" not in instance.serial_numbers_done


def test_image_upgrade_stage_00030(
    monkeypatch, image_stage, issu_details_by_serial_number
) -> None:
    """
    Function
    - _wait_for_current_actions_to_complete

    Summary
    Verify proper behavior of _wait_for_current_actions_to_complete when
    there are no actions pending.

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
    key = "test_image_upgrade_stage_00030a"

    def mock_dcnm_send_switch_issu_details(*args) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_switch_issu_details)

    with does_not_raise():
        instance = image_stage
        instance.unit_test = True
        instance.issu_detail = issu_details_by_serial_number
        instance.serial_numbers = [
            "FDO21120U5D",
            "FDO2112189M",
        ]
        instance._wait_for_current_actions_to_complete()  # pylint: disable=protected-access
    assert isinstance(instance.serial_numbers_done, set)
    assert len(instance.serial_numbers_done) == 2
    assert "FDO21120U5D" in instance.serial_numbers_done
    assert "FDO2112189M" in instance.serial_numbers_done


def test_image_upgrade_stage_00031(
    monkeypatch, image_stage, issu_details_by_serial_number
) -> None:
    """
    Function
    - _wait_for_current_actions_to_complete

    Summary
    Verify proper behavior of _wait_for_current_actions_to_complete when
    there is a timeout waiting for one serial number to complete staging.

    Test
    -   module.serial_numbers_done is a set()
    -   module.serial_numbers_done has length 1
    -   module.serial_numbers_done contains FDO21120U5D
        because imageStaged == "Success"
    -   module.serial_numbers_done does not contain FDO2112189M
    -   fail_json is called due to timeout because FDO2112189M
        imageStaged == "In-Progress"

    Description
    See test_image_upgrade_stage_00030 for functional details.
    """
    key = "test_image_upgrade_stage_00031a"

    def mock_dcnm_send_switch_issu_details(*args) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_switch_issu_details)

    match = "ImageStage._wait_for_current_actions_to_complete: "
    match += "Timed out waiting for actions to complete. "
    match += "serial_numbers_done: FDO21120U5D, "
    match += "serial_numbers_todo: FDO21120U5D,FDO2112189M"

    with does_not_raise():
        instance = image_stage
        instance.unit_test = True
        instance.issu_detail = issu_details_by_serial_number
        instance.serial_numbers = [
            "FDO21120U5D",
            "FDO2112189M",
        ]

    with pytest.raises(AnsibleFailJson, match=match):
        instance._wait_for_current_actions_to_complete()  # pylint: disable=protected-access
    assert isinstance(instance.serial_numbers_done, set)
    assert len(instance.serial_numbers_done) == 1
    assert "FDO21120U5D" in instance.serial_numbers_done
    assert "FDO2112189M" not in instance.serial_numbers_done


MATCH_00040 = "ImageStage.check_interval: must be a positive integer or zero."


@pytest.mark.parametrize(
    "arg, value, context",
    [
        (True, None, pytest.raises(AnsibleFailJson, match=MATCH_00040)),
        (-1, None, pytest.raises(AnsibleFailJson, match=MATCH_00040)),
        (10, 10, does_not_raise()),
        ("a", None, pytest.raises(AnsibleFailJson, match=MATCH_00040)),
    ],
)
def test_image_upgrade_stage_00040(image_stage, arg, value, context) -> None:
    """
    Function
    - check_interval

    Summary
    Verify that check_interval argument validation works as expected.

    Test
    - Verify input arguments to check_interval property

    Description
    check_interval expects a positive integer value, or zero.
    """
    with does_not_raise():
        instance = image_stage
    with context:
        instance.check_interval = arg
    if value is not None:
        assert instance.check_interval == value


MATCH_00050 = "ImageStage.check_timeout: must be a positive integer or zero."


@pytest.mark.parametrize(
    "arg, value, context",
    [
        (True, None, pytest.raises(AnsibleFailJson, match=MATCH_00050)),
        (-1, None, pytest.raises(AnsibleFailJson, match=MATCH_00050)),
        (10, 10, does_not_raise()),
        ("a", None, pytest.raises(AnsibleFailJson, match=MATCH_00050)),
    ],
)
def test_image_upgrade_stage_00050(image_stage, arg, value, context) -> None:
    """
    Function
    - check_interval

    Summary
    Verify that check_timeout argument validation works as expected.

    Test
    - Verify input arguments to check_timeout property

    Description
    check_timeout expects a positive integer value, or zero.
    """
    with does_not_raise():
        instance = image_stage
    with context:
        instance.check_timeout = arg
    if value is not None:
        assert instance.check_timeout == value


MATCH_00060 = (
    "ImageStage.serial_numbers: must be a python list of switch serial numbers."
)


@pytest.mark.parametrize(
    "arg, value, context",
    [
        ("foo", None, pytest.raises(AnsibleFailJson, match=MATCH_00060)),
        (10, None, pytest.raises(AnsibleFailJson, match=MATCH_00060)),
        (["DD001115F"], ["DD001115F"], does_not_raise()),
    ],
)
def test_image_upgrade_stage_00060(image_stage, arg, value, context) -> None:
    """
    Function
    - serial_numbers

    Summary
    Verify that serial_numbers argument validation works as expected.

    Test
    - Verify inputs to serial_numbers property
    - Verify that fail_json is called if the input is not a list

    Description
    serial_numbers expects a list of serial numbers.
    """
    with does_not_raise():
        instance = image_stage
    with context:
        instance.serial_numbers = arg
    if value is not None:
        assert instance.serial_numbers == value


MATCH_00070 = "ImageStage.commit_normal_mode: call instance.serial_numbers "
MATCH_00070 += "before calling commit."


@pytest.mark.parametrize(
    "serial_numbers_is_set, expected",
    [
        (True, does_not_raise()),
        (False, pytest.raises(AnsibleFailJson, match=MATCH_00070)),
    ],
)
def test_image_upgrade_stage_00070(
    monkeypatch, image_stage, serial_numbers_is_set, expected
) -> None:
    """
    Function
    commit

    Summary
    Verify that commit raises fail_json appropriately based on value of
    instance.serial_numbers.

    Test
    - fail_json is called when serial_numbers is None
    - fail_json is not called when serial_numbers is set
    """
    key = "test_image_upgrade_stage_00070a"

    def mock_dcnm_send_controller_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    def mock_rest_send_image_stage(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_stage(key)

    def mock_dcnm_send_switch_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_CONTROLLER_VERSION, mock_dcnm_send_controller_version)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_switch_issu_details)
    monkeypatch.setattr(PATCH_IMAGE_STAGE_REST_SEND_COMMIT, mock_rest_send_image_stage)
    monkeypatch.setattr(PATCH_IMAGE_STAGE_REST_SEND_RESULT_CURRENT, {"success": True})

    instance = image_stage
    if serial_numbers_is_set:
        instance.serial_numbers = ["FDO21120U5D"]
    with expected:
        instance.commit()


@pytest.mark.parametrize(
    "controller_version, expected_serial_number_key",
    [
        ("12.1.2e", "sereialNum"),
        ("12.1.3b", "serialNumbers"),
    ],
)
def test_image_upgrade_stage_00072(
    monkeypatch, image_stage, controller_version, expected_serial_number_key
) -> None:
    """
    Function
    - commit

    Summary
    Verify that the serial number key name in the payload is set correctly
    based on the controller version.

    Test
    - controller_version 12.1.2e -> key name "sereialNum" (yes, misspelled)
    - controller_version 12.1.3b -> key name "serialNumbers

    Description
    commit() will set the payload key name for the serial number
    based on the controller version, per Expected Results below
    """
    key = "test_image_upgrade_stage_00072a"

    def mock_controller_version(*args) -> None:
        instance.controller_version = controller_version

    controller_version_patch = "ansible_collections.cisco.dcnm.plugins."
    controller_version_patch += "modules.dcnm_image_upgrade."
    controller_version_patch += "ImageStage._populate_controller_version"
    monkeypatch.setattr(controller_version_patch, mock_controller_version)

    def mock_rest_send_image_stage(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_stage(key)

    def mock_dcnm_send_switch_issu_details(*args) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_switch_issu_details)
    monkeypatch.setattr(PATCH_IMAGE_STAGE_REST_SEND_COMMIT, mock_rest_send_image_stage)
    monkeypatch.setattr(PATCH_IMAGE_STAGE_REST_SEND_RESULT_CURRENT, {"success": True})

    instance = image_stage
    instance.serial_numbers = ["FDO21120U5D"]
    instance.commit()
    assert expected_serial_number_key in instance.payload.keys()


def test_image_upgrade_stage_00073(monkeypatch, image_stage) -> None:
    """
    Function
    - commit

    Summary
    Verify that commit() sets result, response, and response_data
    appropriately when serial_numbers is empty.

    Setup
    - SwitchIssuDetailsBySerialNumber is mocked to return a successful response
    - self.serial_numbers is set to [] (empty list)

    Test
    - commit() sets the following to expected values:
        - self.result, self.result_current
        - self.response, self.response_current
        - self.response_data

    Description
    When len(serial_numbers) == 0, commit() will set result and
    response properties, and return without doing anything else.
    """
    monkeypatch.setattr(PATCH_IMAGE_STAGE_REST_SEND_RESULT_CURRENT, {"success": True})

    response_msg = "No files to stage."
    with does_not_raise():
        instance = image_stage
        instance.serial_numbers = []
        instance.commit()
    assert instance.result == [{"success": True, "changed": False}]
    assert instance.result_current == {"success": True, "changed": False}
    assert instance.response_current == {
        "DATA": [{"key": "ALL", "value": response_msg}]
    }
    assert instance.response == [instance.response_current]
    assert instance.response_data == [instance.response_current.get("DATA")]


def test_image_upgrade_stage_00074(monkeypatch, image_stage) -> None:
    """
    Function
    - commit

    Summary
    Verify that commit() calls fail_json() on 500 response from the controller.

    Setup
    - IssuDetailsBySerialNumber is mocked to return a successful response
    - ImageStage is mocked to return a non-successful (500) response

    Test
    - commit() will call fail_json()

    Description
    commit() will call fail_json() on non-success response from the controller.
    """
    key = "test_image_upgrade_stage_00074a"

    def mock_controller_version(*args) -> None:
        instance.controller_version = "12.1.3b"

    def mock_dcnm_send_switch_issu_details(*args) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_rest_send_image_stage(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_stage(key)

    monkeypatch.setattr(
        PATCH_IMAGE_STAGE_POPULATE_CONTROLLER_VERSION, mock_controller_version
    )
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_switch_issu_details)
    monkeypatch.setattr(PATCH_IMAGE_STAGE_REST_SEND_COMMIT, mock_rest_send_image_stage)
    monkeypatch.setattr(PATCH_IMAGE_STAGE_REST_SEND_RESULT_CURRENT, {"success": False})

    instance = image_stage
    instance.serial_numbers = ["FDO21120U5D"]
    match = "ImageStage.commit_normal_mode: failed"
    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()


def test_image_upgrade_stage_00075(monkeypatch, image_stage) -> None:
    """
    Function
    - commit

    Summary
    Verify that commit() sets self.diff to expected values on 200 response
    from the controller.

    Setup
    -   IssuDetailsBySerialNumber is mocked to return a successful response
    -   ImageStage._populate_controller_version is mocked to 12.1.3b
    -   ImageStage.rest_send.commit is mocked to return a successful response
    -   ImageStage.rest_send.current_result is mocked to return a successful result
    -   ImageStage.validate_serial_numbers is tracked with MagicMock to ensure
        it's called once

    Test
    - commit() sets self.diff to the expected values
    """
    key = "test_image_upgrade_stage_00075a"

    def mock_controller_version(*args) -> None:
        instance.controller_version = "12.1.3b"

    def mock_dcnm_send_switch_issu_details(*args) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_rest_send_image_stage(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_stage(key)

    def mock_wait_for_image_stage_to_complete(*args) -> None:
        instance.serial_numbers_done = {"FDO21120U5D"}

    monkeypatch.setattr(
        PATCH_IMAGE_STAGE_POPULATE_CONTROLLER_VERSION, mock_controller_version
    )
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_switch_issu_details)
    monkeypatch.setattr(PATCH_IMAGE_STAGE_REST_SEND_COMMIT, mock_rest_send_image_stage)
    monkeypatch.setattr(
        PATCH_IMAGE_STAGE_REST_SEND_RESULT_CURRENT, {"success": True, "changed": True}
    )
    validate_serial_numbers = MagicMock(name="validate_serial_numbers")

    instance = image_stage
    instance.serial_numbers = ["FDO21120U5D"]
    monkeypatch.setattr(
        instance,
        "_wait_for_image_stage_to_complete",
        mock_wait_for_image_stage_to_complete,
    )
    monkeypatch.setattr(instance, "validate_serial_numbers", validate_serial_numbers)
    instance.commit()
    assert validate_serial_numbers.assert_called_once
    assert instance.serial_numbers_done == {"FDO21120U5D"}
    assert instance.result_current == {"success": True, "changed": True}
    assert instance.diff[0]["policy"] == "KR5M"
    assert instance.diff[0]["ip_address"] == "172.22.150.102"
    assert instance.diff[0]["serial_number"] == "FDO21120U5D"
