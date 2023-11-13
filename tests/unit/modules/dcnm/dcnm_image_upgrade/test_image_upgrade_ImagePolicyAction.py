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
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policy_action import \
    ImagePolicyAction
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import \
    SwitchIssuDetailsBySerialNumber

from .fixture import load_fixture

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

"""
controller_version: 12
Description: Verify functionality of ImagePolicyAction
"""


@contextmanager
def does_not_raise():
    yield


patch_module_utils = "ansible_collections.cisco.dcnm.plugins.module_utils."
patch_image_mgmt = patch_module_utils + "image_mgmt."

dcnm_send_image_policies = patch_image_mgmt + "image_policies.dcnm_send"
dcnm_send_image_policy_action = patch_image_mgmt + "image_policy_action.dcnm_send"
dcnm_send_switch_details = patch_image_mgmt + "switch_details.dcnm_send"
dcnm_send_switch_issu_details = patch_image_mgmt + "switch_issu_details.dcnm_send"


def responses_image_policies(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_ImagePolicies"
    response = load_fixture(response_file).get(key)
    print(f"responses_image_policies: {key} : {response}")
    return response


def responses_image_policy_action(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_ImagePolicyAction"
    response = load_fixture(response_file).get(key)
    print(f"responses_image_policy_action: {key} : {response}")
    return response


def responses_switch_details(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_SwitchDetails"
    response = load_fixture(response_file).get(key)
    print(f"responses_switch_details: {key} : {response}")
    return response


def responses_switch_issu_details(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_SwitchIssuDetails"
    response = load_fixture(response_file).get(key)
    print(f"responses_switch_issu_details: {key} : {response}")
    return response


class MockAnsibleModule:
    params = {}

    def fail_json(msg) -> AnsibleFailJson:
        raise AnsibleFailJson(msg)


@pytest.fixture
def image_policy_action():
    return ImagePolicyAction(MockAnsibleModule)


@pytest.fixture
def issu_details() -> SwitchIssuDetailsBySerialNumber:
    return SwitchIssuDetailsBySerialNumber(MockAnsibleModule)


@pytest.fixture
def image_policies() -> ImagePolicies:
    return ImagePolicies(MockAnsibleModule)


def test_image_mgmt_image_policy_action_00001(image_policy_action) -> None:
    """
    Function
    - __init__

    Test
    - Class attributes initialized to expected values
    """
    image_policy_action.__init__(MockAnsibleModule)
    assert isinstance(image_policy_action, ImagePolicyAction)
    assert isinstance(
        image_policy_action.switch_issu_details, SwitchIssuDetailsBySerialNumber
    )
    assert image_policy_action.valid_actions == {"attach", "detach", "query"}


def test_image_mgmt_image_policy_action_00002(image_policy_action) -> None:
    """
    Function
    - _init_properties

    Test
    - Class properties are initialized to expected values
    """
    image_policy_action._init_properties()
    assert isinstance(image_policy_action.properties, dict)
    assert image_policy_action.properties.get("action") == None
    assert image_policy_action.properties.get("response") == None
    assert image_policy_action.properties.get("result") == None
    assert image_policy_action.properties.get("policy_name") == None
    assert image_policy_action.properties.get("query_result") == None
    assert image_policy_action.properties.get("serial_numbers") == None


def test_image_mgmt_image_policy_action_00003(
    monkeypatch, image_policy_action, issu_details
) -> None:
    """
    Function
    - build_payload

    Test
    - fail_json is not called
    - image_policy_action.payloads is a list
    - image_policy_action.payloads has length 5

    Description
    build_payload builds the payload to send in the POST request
    to attach policies to devices
    """

    def mock_dcnm_send_switch_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_image_policy_action_00003a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(
        dcnm_send_switch_issu_details, mock_dcnm_send_switch_issu_details
    )

    image_policy_action.switch_issu_details = issu_details
    image_policy_action.policy_name = "KR5M"
    image_policy_action.serial_numbers = [
        "FDO2112189M",
        "FDO211218AX",
        "FDO211218B5",
        "FDO211218FV",
        "FDO211218GC",
    ]
    with does_not_raise():
        image_policy_action.build_payload()
    assert isinstance(image_policy_action.payloads, list)
    assert len(image_policy_action.payloads) == 5


def test_image_mgmt_image_policy_action_00004(
    monkeypatch, image_policy_action, issu_details
) -> None:
    """
    Function
    - build_payload

    Test
    - fail_json is called since deviceName is null in the issu_details response
    - The error message is matched

    Description
    build_payload builds the payload to send in the POST request
    to attach policies to devices.  If any key in the payload has a value
    of None, the function calls fail_json.
    """

    def mock_dcnm_send_switch_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_image_policy_action_00004a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(
        dcnm_send_switch_issu_details, mock_dcnm_send_switch_issu_details
    )

    image_policy_action.switch_issu_details = issu_details
    image_policy_action.policy_name = "KR5M"
    image_policy_action.serial_numbers = [
        "FDO2112189M",
    ]
    match = "Unable to determine hostName for switch "
    match += "172.22.150.108, FDO2112189M, None. "
    match += "Please verify that the switch is managed by "
    match += "the controller."
    with pytest.raises(AnsibleFailJson, match=match):
        image_policy_action.build_payload()


def test_image_mgmt_image_policy_action_00010(
    image_policy_action, issu_details
) -> None:
    """
    Function
    - validate_request

    Test
    - fail_json is called because image_policy_action.action is None
    - The error message is matched

    Description
    validate_request performs a number of validations prior to calling commit
    If any of these validations fail, the function calls fail_json with a
    validation-specific error message.
    """

    image_policy_action.switch_issu_details = issu_details
    image_policy_action.policy_name = "KR5M"
    image_policy_action.serial_numbers = [
        "FDO2112189M",
    ]
    match = "ImagePolicyAction.validate_request: "
    match += "instance.action must be set before calling commit()"
    with pytest.raises(AnsibleFailJson, match=match):
        image_policy_action.validate_request()


match_00011 = "ImagePolicyAction.validate_request: "
match_00011 += "instance.policy_name must be set before calling commit()"


@pytest.mark.parametrize(
    "action,expected",
    [
        ("attach", pytest.raises(AnsibleFailJson, match=match_00011)),
        ("detach", pytest.raises(AnsibleFailJson, match=match_00011)),
        ("query", pytest.raises(AnsibleFailJson, match=match_00011)),
    ],
)
def test_image_mgmt_image_policy_action_00011(
    action, expected, image_policy_action, issu_details
) -> None:
    """
    Function
    - validate_request

    Test
    - fail_json is called because image_policy_action.policy_name is None
    - The error message is matched

    Description
    validate_request performs a number of validations prior to calling commit
    If any of these validations fail, the function calls fail_json with a
    validation-specific error message.
    """

    image_policy_action.switch_issu_details = issu_details
    image_policy_action.action = action
    image_policy_action.serial_numbers = [
        "FDO2112189M",
    ]

    with expected:
        image_policy_action.validate_request()


match_00012 = "ImagePolicyAction.validate_request: "
match_00012 += "instance.serial_numbers must be set before calling commit()"


@pytest.mark.parametrize(
    "action,expected",
    [
        ("attach", pytest.raises(AnsibleFailJson, match=match_00012)),
        ("detach", pytest.raises(AnsibleFailJson, match=match_00012)),
        ("query", does_not_raise()),
    ],
)
def test_image_mgmt_image_policy_action_00012(
    action, expected, image_policy_action, issu_details
) -> None:
    """
    Function
    - validate_request

    Test
    -   fail_json is called for action == attach because
        image_policy_action.serial_numbers is None
    -   fail_json is called for action == detach because
        image_policy_action.serial_numbers is None
    -   fail_json is NOT called for action == query because
        validate_request is exited early for action == "query"
    -   The error message, if any, is matched

    Description
    validate_request performs a number of validations prior to calling commit
    If any of these validations fail, the function calls fail_json with a
    validation-specific error message.
    """

    image_policy_action.switch_issu_details = issu_details
    image_policy_action.action = action
    image_policy_action.policy_name = "KR5M"

    with expected:
        image_policy_action.validate_request()


def test_image_mgmt_image_policy_action_00013(
    monkeypatch, image_policy_action, issu_details, image_policies
) -> None:
    """
    Function
    - validate_request

    Test
    -   fail_json is called because policy KR5M supports playform N9K/N3K
        and the response from ImagePolicies contains platform
        TEST_UNKNOWN_PLATFORM
    -   The error message is matched

    Description
    validate_request performs a number of validations prior to calling commit
    validate_request performs a number of validations prior to calling commit
    If any of these validations fail, the function calls fail_json with a
    validation-specific error message.
    """
    key = "test_image_mgmt_image_policy_action_00013a"

    def mock_dcnm_send_switch_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_dcnm_send_image_policies(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_policies(key)

    monkeypatch.setattr(
        dcnm_send_switch_issu_details, mock_dcnm_send_switch_issu_details
    )
    monkeypatch.setattr(dcnm_send_image_policies, mock_dcnm_send_image_policies)

    image_policy_action.switch_issu_details = issu_details
    image_policy_action.image_policies = image_policies
    image_policy_action.action = "attach"
    image_policy_action.policy_name = "KR5M"
    image_policy_action.serial_numbers = ["FDO2112189M"]

    match = "ImagePolicyAction.validate_request: "
    match += "policy KR5M does not support platform TEST_UNKNOWN_PLATFORM. "
    match += r"KR5M supports the following platform\(s\): N9K/N3K"

    with pytest.raises(AnsibleFailJson, match=match):
        image_policy_action.validate_request()


def test_image_mgmt_image_policy_action_00020(monkeypatch, image_policy_action) -> None:
    """
    Function
    - commit

    Test
    -   fail_json is called because action is unknown
    -   The error message is matched

    Description
    commit calls validate_request() and then calls one of the following
    functions based on the value of action:
        action == "attach" : _attach_policy
        action == "detach" : _detach_policy
        action == "query" : _query_policy

    If action is not one of [attach, detach, query], commit() calls fail_json.

    This test mocks valid_actions to include "FOO" so that action.setter
    will accept it (effectively bypassing the check in the setter).
    It also mocks validate_request() to remove it from consideration.

    Since action == "FOO" is not covered in commit()'s if clauses,
    the else clause is taken and fail_json is called.
    """
    key = "test_image_mgmt_image_policy_action_00020a"

    def mock_dcnm_send_switch_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_dcnm_send_image_policies(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_policies(key)

    def mock_validate_request(*args, **kwargs) -> None:
        pass

    monkeypatch.setattr(
        dcnm_send_switch_issu_details, mock_dcnm_send_switch_issu_details
    )
    monkeypatch.setattr(dcnm_send_image_policies, mock_dcnm_send_image_policies)

    monkeypatch.setattr(image_policy_action, "validate_request", mock_validate_request)
    monkeypatch.setattr(
        image_policy_action, "valid_actions", {"attach", "detach", "query", "FOO"}
    )

    image_policy_action.policy_name = "KR5M"
    image_policy_action.serial_numbers = ["FDO2112189M"]
    image_policy_action.action = "FOO"

    match = "ImagePolicyAction.commit: Unknown action FOO."

    with pytest.raises(AnsibleFailJson, match=match):
        image_policy_action.commit()


def test_image_mgmt_image_policy_action_00021(monkeypatch, image_policy_action) -> None:
    """
    Function
    - commit

    Test
    -   action is "detach", so ImagePolicyAction._detach_policy is called
    -   commit is successful given a 200 response from the controller in
        ImagePolicyAction._detach_policy
    -   ImagePolicyAction.response contains RESULT_CODE 200

    Description
    commit calls validate_request() and then calls one of the following
    functions based on the value of action:
        action == "attach" : _attach_policy
        action == "detach" : _detach_policy
        action == "query" : _query_policy
    """
    key = "test_image_mgmt_image_policy_action_00021a"

    def mock_dcnm_send_image_policies(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_policies(key)

    def mock_dcnm_send_switch_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_details(key)

    def mock_dcnm_send_switch_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_dcnm_send_image_policy_action(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_policy_action(key)

    monkeypatch.setattr(dcnm_send_image_policies, mock_dcnm_send_image_policies)
    monkeypatch.setattr(
        dcnm_send_image_policy_action, mock_dcnm_send_image_policy_action
    )
    monkeypatch.setattr(dcnm_send_switch_details, mock_dcnm_send_switch_details)
    monkeypatch.setattr(
        dcnm_send_switch_issu_details, mock_dcnm_send_switch_issu_details
    )

    image_policy_action.policy_name = "KR5M"
    image_policy_action.serial_numbers = ["FDO2112189M"]
    image_policy_action.action = "detach"

    image_policy_action.commit()
    assert isinstance(image_policy_action.response, dict)
    assert image_policy_action.response.get("RETURN_CODE") == 200
    assert image_policy_action.response.get("METHOD") == "DELETE"
    assert image_policy_action.response.get("MESSAGE") == "OK"
    assert (
        image_policy_action.response.get("DATA")
        == "Successfully detach the policy from device."
    )
    assert image_policy_action.result.get("success") == True
    assert image_policy_action.result.get("changed") == True


match_00060 = "ImagePolicyAction.action: instance.action must be "
match_00060 += "one of attach,detach,query. Got FOO."


@pytest.mark.parametrize(
    "value, expected",
    [
        ("attach", "attach"),
        ("detach", "detach"),
        ("query", "query"),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00060)),
    ],
)
def test_image_mgmt_image_policy_action_00060(
    image_policy_action, value, expected
) -> None:
    """
    ImagePolicyAction.action setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00060):
            image_policy_action.action = value
    else:
        image_policy_action.action = value
        assert image_policy_action.action == expected


match_00061 = "ImagePolicyAction.serial_numbers: instance.serial_numbers "
match_00061 += "must be a python list of switch serial numbers. Got FOO."


@pytest.mark.parametrize(
    "value, expected",
    [
        (["FDO2112189M", "FDO21120U5D"], ["FDO2112189M", "FDO21120U5D"]),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00061)),
    ],
)
def test_image_mgmt_image_policy_action_00061(
    image_policy_action, value, expected
) -> None:
    """
    ImagePolicyAction.serial_numbers setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00061):
            image_policy_action.serial_numbers = value
    else:
        image_policy_action.serial_numbers = value
        assert image_policy_action.serial_numbers == expected
