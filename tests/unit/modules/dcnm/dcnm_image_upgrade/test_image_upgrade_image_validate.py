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
# Some tests require calling protected methods
# pylint: disable=protected-access

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import \
    SwitchIssuDetailsBySerialNumber

from .image_upgrade_utils import (does_not_raise, image_validate_fixture,
                                  issu_details_by_serial_number_fixture,
                                  responses_image_validate,
                                  responses_switch_issu_details)

PATCH_MODULE_UTILS = "ansible_collections.cisco.dcnm.plugins.module_utils."
PATCH_IMAGE_MGMT = PATCH_MODULE_UTILS + "image_mgmt."
DCNM_SEND_IMAGE_VALIDATE = PATCH_IMAGE_MGMT + "image_validate.dcnm_send"
DCNM_SEND_ISSU_DETAILS = PATCH_IMAGE_MGMT + "switch_issu_details.dcnm_send"


def test_image_mgmt_validate_00001(image_validate) -> None:
    """
    Function
    - __init__

    Test
    - Class attributes are initialized to expected values
    """
    instance = image_validate
    assert instance.class_name == "ImageValidate"
    assert isinstance(instance.endpoints, ApiEndpoints)
    assert isinstance(instance.issu_detail, SwitchIssuDetailsBySerialNumber)
    assert isinstance(instance.serial_numbers_done, set)
    assert (
        instance.path
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement/validate-image"
    )
    assert instance.verb == "POST"


def test_image_mgmt_validate_00002(image_validate) -> None:
    """
    Function
    - _init_properties

    Test
    - Class properties are initialized to expected values
    """
    instance = image_validate
    assert isinstance(instance.properties, dict)
    assert instance.properties.get("check_interval") == 10
    assert instance.properties.get("check_timeout") == 1800
    assert instance.properties.get("response_data") == {}
    assert instance.properties.get("response") == {}
    assert instance.properties.get("result") == {}
    assert instance.properties.get("non_disruptive") is False
    assert instance.properties.get("serial_numbers") is None


def test_image_mgmt_validate_00003(
    monkeypatch, image_validate, issu_details_by_serial_number
) -> None:
    """
    Function
    - prune_serial_numbers

    Test
    -   instance.serial_numbers contains only serial numbers for which
        "validated" == "none"
    -   serial_numbers does not contain serial numbers for which
        "validated" == "Success"

    Description
    prune_serial_numbers removes serial numbers from the list for which
    "validated" == "Success" (TODO: AND policy == <target_policy>)

    Expected results:
    1. instance.serial_numbers == ["FDO2112189M", "FDO211218AX", "FDO211218B5"]
    2. instance.serial_numbers != ["FDO211218FV", "FDO211218GC"]
    """
    instance = image_validate

    def mock_dcnm_send_issu_details(*args) -> Dict[str, Any]:
        key = "test_image_mgmt_validate_00003a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

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


def test_image_mgmt_validate_00004(
    monkeypatch, image_validate, issu_details_by_serial_number
) -> None:
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
    instance = image_validate

    def mock_dcnm_send_issu_details(*args) -> Dict[str, Any]:
        key = "test_image_mgmt_validate_00004a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    instance.issu_detail = issu_details_by_serial_number
    instance.serial_numbers = ["FDO21120U5D", "FDO2112189M"]

    match = "ImageValidate.validate_serial_numbers: "
    match += "image validation is failing for the following switch: "
    match += "cvd-2313-leaf, 172.22.150.108, FDO2112189M. If this "
    match += "persists, check the switch connectivity to the "
    match += "controller and try again."

    with pytest.raises(AnsibleFailJson, match=match):
        instance.validate_serial_numbers()


def test_image_mgmt_validate_00005(
    monkeypatch, image_validate, issu_details_by_serial_number
) -> None:
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
    instance = image_validate

    def mock_dcnm_send_issu_details(*args) -> Dict[str, Any]:
        key = "test_image_mgmt_validate_00005a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    instance.issu_detail = issu_details_by_serial_number
    instance.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    instance.check_interval = 0
    instance._wait_for_image_validate_to_complete()
    assert isinstance(instance.serial_numbers_done, set)
    assert len(instance.serial_numbers_done) == 2
    assert "FDO21120U5D" in instance.serial_numbers_done
    assert "FDO2112189M" in instance.serial_numbers_done


def test_image_mgmt_validate_00006(
    monkeypatch, image_validate, issu_details_by_serial_number
) -> None:
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
    instance = image_validate

    def mock_dcnm_send_issu_details(*args) -> Dict[str, Any]:
        key = "test_image_mgmt_validate_00006a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    instance.issu_detail = issu_details_by_serial_number
    instance.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    instance.check_interval = 0
    match = "Seconds remaining 1800: validate image Failed for "
    match += "cvd-2313-leaf, 172.22.150.108, FDO2112189M, "
    match += "image validated percent: 100. Check the switch e.g. "
    match += "show install log detail, show incompatibility-all nxos "
    match += "<image>.  Or check Operations > Image Management > "
    match += "Devices > View Details > Validate on the controller "
    match += "GUI for more details."

    with pytest.raises(AnsibleFailJson, match=match):
        instance._wait_for_image_validate_to_complete()  # pylint: disable=protected-access
    assert isinstance(instance.serial_numbers_done, set)
    assert len(instance.serial_numbers_done) == 1
    assert "FDO21120U5D" in instance.serial_numbers_done
    assert "FDO2112189M" not in instance.serial_numbers_done


def test_image_mgmt_validate_00007(
    monkeypatch, image_validate, issu_details_by_serial_number
) -> None:
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
    instance = image_validate

    def mock_dcnm_send_issu_details(*args) -> Dict[str, Any]:
        key = "test_image_mgmt_validate_00007a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    instance.issu_detail = issu_details_by_serial_number
    instance.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    instance.check_interval = 1
    instance.check_timeout = 1

    match = "ImageValidate._wait_for_image_validate_to_complete: "
    match += "Timed out waiting for image validation to complete. "
    match += "serial_numbers_done: FDO21120U5D, "
    match += "serial_numbers_todo: FDO21120U5D,FDO2112189M"

    with pytest.raises(AnsibleFailJson, match=match):
        instance._wait_for_image_validate_to_complete()  # pylint: disable=protected-access
    assert isinstance(instance.serial_numbers_done, set)
    assert len(instance.serial_numbers_done) == 1
    assert "FDO21120U5D" in instance.serial_numbers_done
    assert "FDO2112189M" not in instance.serial_numbers_done


def test_image_mgmt_validate_00008(
    monkeypatch, image_validate, issu_details_by_serial_number
) -> None:
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
    instance = image_validate

    def mock_dcnm_send_issu_details(*args) -> Dict[str, Any]:
        key = "test_image_mgmt_validate_00008a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    instance.issu_detail = issu_details_by_serial_number
    instance.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    instance.check_interval = 0
    instance._wait_for_current_actions_to_complete()  # pylint: disable=protected-access
    assert isinstance(instance.serial_numbers_done, set)
    assert len(instance.serial_numbers_done) == 2
    assert "FDO21120U5D" in instance.serial_numbers_done
    assert "FDO2112189M" in instance.serial_numbers_done


def test_image_mgmt_validate_00009(
    monkeypatch, image_validate, issu_details_by_serial_number
) -> None:
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
    instance = image_validate

    def mock_dcnm_send_issu_details(*args) -> Dict[str, Any]:
        key = "test_image_mgmt_validate_00009a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    instance.issu_detail = issu_details_by_serial_number
    instance.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    instance.check_interval = 1
    instance.check_timeout = 1

    match = "ImageValidate._wait_for_current_actions_to_complete: "
    match += "Timed out waiting for actions to complete. "
    match += "serial_numbers_done: FDO21120U5D, "
    match += "serial_numbers_todo: FDO21120U5D,FDO2112189M"

    with pytest.raises(AnsibleFailJson, match=match):
        instance._wait_for_current_actions_to_complete()  # pylint: disable=protected-access
    assert isinstance(instance.serial_numbers_done, set)
    assert len(instance.serial_numbers_done) == 1
    assert "FDO21120U5D" in instance.serial_numbers_done
    assert "FDO2112189M" not in instance.serial_numbers_done


MATCH_00020 = "ImageValidate.commit: call instance.serial_numbers "
MATCH_00020 += "before calling commit."


@pytest.mark.parametrize(
    "serial_numbers_is_set, expected",
    [
        (True, does_not_raise()),
        (False, pytest.raises(AnsibleFailJson, match=MATCH_00020)),
    ],
)
def test_image_mgmt_validate_00020(
    monkeypatch, image_validate, serial_numbers_is_set, expected
) -> None:
    """
    Function
    commit

    Test
    - fail_json is called when serial_numbers is None
    - fail_json is not called when serial_numbers is set
    """

    def mock_dcnm_send_image_validate(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_validate_00020a"
        return responses_image_validate(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_validate_00020a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_IMAGE_VALIDATE, mock_dcnm_send_image_validate)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    instance = image_validate
    assert instance.class_name == "ImageValidate"

    if serial_numbers_is_set:
        instance.serial_numbers = ["FDO21120U5D"]
    with expected:
        instance.commit()


def test_image_mgmt_validate_00021(monkeypatch, image_validate) -> None:
    """
    Function
    - commit

    Test
    - ImageValidate.verb is set to POST
    - ImageValidate.path is set to:
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement/validate-image
    """

    # Needed only for the 200 return code
    def mock_dcnm_send_image_validate(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_validate_00021a"
        return responses_image_validate(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_validate_00021a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_IMAGE_VALIDATE, mock_dcnm_send_image_validate)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    module_path = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/"
    module_path += "stagingmanagement/validate-image"

    instance = image_validate
    instance.serial_numbers = ["FDO21120U5D"]
    instance.commit()
    assert instance.path == module_path
    assert instance.verb == "POST"


def test_image_mgmt_validate_00022(image_validate) -> None:
    """
    Function
    - commit

    Test
    - instance.response is set to {} because dcnm_send was not called
    - instance.result is set to {} because dcnm_send was not called

    Description
    If instance.serial_numbers is an empty list, instance.commit() returns
    without calling dcnm_send.
    """
    with does_not_raise():
        instance = image_validate
        instance.serial_numbers = []
        instance.commit()
    assert instance.response == {}
    assert instance.result == {}


def test_image_mgmt_validate_00023(monkeypatch, image_validate) -> None:
    """
    Function
    - commit

    Test
    -   501 response from controller endpoint:
        POST /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement/validate-image
    """

    # Needed only for the 501 return code
    def mock_dcnm_send_image_validate(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_validate_00023a"
        return responses_image_validate(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_validate_00023a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_IMAGE_VALIDATE, mock_dcnm_send_image_validate)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    with does_not_raise():
        instance = image_validate
        instance.serial_numbers = ["FDO21120U5D"]
    with pytest.raises(AnsibleFailJson, match="failed:"):
        instance.commit()
    assert instance.result["success"] is False
    assert instance.result["changed"] is False
    assert instance.response["RETURN_CODE"] == 501


MATCH_00030 = "ImageValidate.serial_numbers: "
MATCH_00030 += "instance.serial_numbers must be a python list "
MATCH_00030 += "of switch serial numbers."


@pytest.mark.parametrize(
    "value, expected",
    [
        ([], does_not_raise()),
        (True, pytest.raises(AnsibleFailJson, match=MATCH_00030)),
        (False, pytest.raises(AnsibleFailJson, match=MATCH_00030)),
        (None, pytest.raises(AnsibleFailJson, match=MATCH_00030)),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00030)),
        (10, pytest.raises(AnsibleFailJson, match=MATCH_00030)),
        ({1, 2}, pytest.raises(AnsibleFailJson, match=MATCH_00030)),
        ({"a": 1, "b": 2}, pytest.raises(AnsibleFailJson, match=MATCH_00030)),
    ],
)
def test_image_mgmt_validate_00030(image_validate, value, expected) -> None:
    """
    Function
    - serial_numbers.setter

    Test
    - fail_json when serial_numbers is not a list
    """
    with does_not_raise():
        instance = image_validate
    assert instance.class_name == "ImageValidate"

    with expected:
        instance.serial_numbers = value


MATCH_00040 = "ImageValidate.make_boolean: "
MATCH_00040 += "instance.non_disruptive must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, does_not_raise()),
        (False, does_not_raise()),
        (None, pytest.raises(AnsibleFailJson, match=MATCH_00040)),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00040)),
        (10, pytest.raises(AnsibleFailJson, match=MATCH_00040)),
        ([1, 2], pytest.raises(AnsibleFailJson, match=MATCH_00040)),
        ({1, 2}, pytest.raises(AnsibleFailJson, match=MATCH_00040)),
        ({"a": 1, "b": 2}, pytest.raises(AnsibleFailJson, match=MATCH_00040)),
    ],
)
def test_image_mgmt_validate_00040(image_validate, value, expected) -> None:
    """
    Function
    - non_disruptive.setter

    Test
    - fail_json when non_disruptive is not a boolean
    """
    with does_not_raise():
        instance = image_validate
    assert instance.class_name == "ImageValidate"

    with expected:
        instance.non_disruptive = value


MATCH_00050 = "ImageValidate.check_interval: "
MATCH_00050 += "instance.check_interval must be an integer."


@pytest.mark.parametrize(
    "value, expected",
    [
        (10, does_not_raise()),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00050)),
        (False, pytest.raises(AnsibleFailJson, match=MATCH_00050)),
        (None, pytest.raises(AnsibleFailJson, match=MATCH_00050)),
        ([1, 2], pytest.raises(AnsibleFailJson, match=MATCH_00050)),
        ({1, 2}, pytest.raises(AnsibleFailJson, match=MATCH_00050)),
        ({"a": 1, "b": 2}, pytest.raises(AnsibleFailJson, match=MATCH_00050)),
    ],
)
def test_image_mgmt_validate_00050(image_validate, value, expected) -> None:
    """
    Function
    - check_interval.setter

    Test
    - fail_json when check_interval is not an integer
    """
    with does_not_raise():
        instance = image_validate
    assert instance.class_name == "ImageValidate"

    with expected:
        instance.check_interval = value


MATCH_00060 = "ImageValidate.check_timeout: "
MATCH_00060 += "instance.check_timeout must be an integer."


@pytest.mark.parametrize(
    "value, expected",
    [
        (10, does_not_raise()),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00060)),
        (False, pytest.raises(AnsibleFailJson, match=MATCH_00060)),
        (None, pytest.raises(AnsibleFailJson, match=MATCH_00060)),
        ([1, 2], pytest.raises(AnsibleFailJson, match=MATCH_00060)),
        ({1, 2}, pytest.raises(AnsibleFailJson, match=MATCH_00060)),
        ({"a": 1, "b": 2}, pytest.raises(AnsibleFailJson, match=MATCH_00060)),
    ],
)
def test_image_mgmt_validate_00060(image_validate, value, expected) -> None:
    """
    Function
    - check_timeout.setter

    Test
    - fail_json when check_timeout is not an integer
    """
    with does_not_raise():
        instance = image_validate
    assert instance.class_name == "ImageValidate"

    with expected:
        instance.check_timeout = value
