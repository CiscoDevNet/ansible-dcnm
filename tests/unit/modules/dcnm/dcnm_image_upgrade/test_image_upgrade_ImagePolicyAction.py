"""
controller_version: 12
description: Verify functionality of ImageStage
"""

from contextlib import contextmanager
from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policy_action import \
    ImagePolicyAction
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_details import \
    SwitchDetails
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import \
    SwitchIssuDetailsBySerialNumber

from .fixture import load_fixture


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
def mock_image_policy_action():
    return ImagePolicyAction(MockAnsibleModule)

@pytest.fixture
def mock_issu_details() -> SwitchIssuDetailsBySerialNumber:
    return SwitchIssuDetailsBySerialNumber(MockAnsibleModule)

@pytest.fixture
def mock_image_policies() -> ImagePolicies:
    return ImagePolicies(MockAnsibleModule)


# test_init


def test_init(mock_image_policy_action) -> None:
    mock_image_policy_action.__init__(MockAnsibleModule)
    assert isinstance(mock_image_policy_action, ImagePolicyAction)
    assert isinstance(mock_image_policy_action.switch_issu_details, SwitchIssuDetailsBySerialNumber)
    assert mock_image_policy_action.valid_actions == {"attach", "detach", "query"}


# test_init_properties


def test_init_properties(mock_image_policy_action) -> None:
    """
    Properties are initialized to expected values
    """
    mock_image_policy_action._init_properties()
    assert isinstance(mock_image_policy_action.properties, dict)
    assert mock_image_policy_action.properties.get("action") == None
    assert mock_image_policy_action.properties.get("response") == None
    assert mock_image_policy_action.properties.get("result") == None
    assert mock_image_policy_action.properties.get("policy_name") == None
    assert mock_image_policy_action.properties.get("query_result") == None
    assert mock_image_policy_action.properties.get("serial_numbers") == None


# test_build_attach_payload


def test_build_attach_payload(monkeypatch, mock_image_policy_action, mock_issu_details) -> None:
    """
    build_attach_payload builds the payload to send in the POST request
    to attach policies to devices

    Expectations:
    1. mock_image_policy_action.payload should be a list()

    Expected results:
    1. mock_image_policy_action.fail_json should not be called
    2. mock_image_policy_action.payloads should be a list()
    3. mock_image_policy_action.payloads should have length 5
    """

    def mock_dcnm_send_switch_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "ImagePolicyAction_test_build_attach_payload"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_switch_issu_details, mock_dcnm_send_switch_issu_details)

    mock_image_policy_action.switch_issu_details = mock_issu_details
    mock_image_policy_action.policy_name = "KR5M"
    mock_image_policy_action.serial_numbers = [
        "FDO2112189M",
        "FDO211218AX",
        "FDO211218B5",
        "FDO211218FV",
        "FDO211218GC",
    ]
    with does_not_raise():
        mock_image_policy_action.build_attach_payload()
    assert isinstance(mock_image_policy_action.payloads, list)
    assert len(mock_image_policy_action.payloads) == 5


# test_build_attach_payload_fail_json


def test_build_attach_payload_fail_json(monkeypatch, mock_image_policy_action, mock_issu_details) -> None:
    """
    build_attach_payload builds the payload to send in the POST request
    to attach policies to devices.  If any key in the payload has a value
    of None, the function calls fail_json.

    Expected results:
    1. fail_json should be called because deviceName is None in the issu_details response
    """

    def mock_dcnm_send_switch_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "ImagePolicyAction_test_build_attach_payload_fail_json"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_switch_issu_details, mock_dcnm_send_switch_issu_details)

    mock_image_policy_action.switch_issu_details = mock_issu_details
    mock_image_policy_action.policy_name = "KR5M"
    mock_image_policy_action.serial_numbers = [
        "FDO2112189M",
    ]
    error_message = "Unable to determine hostName for switch "
    error_message += "172.22.150.108, FDO2112189M, None. "
    error_message += "Please verify that the switch is managed by "
    error_message += "the controller."
    with pytest.raises(AnsibleFailJson, match=error_message):
        mock_image_policy_action.build_attach_payload()


# test_validate_request_policy_name_none


def test_validate_request_action_none(mock_image_policy_action, mock_issu_details) -> None:
    """
    validate_request performs a number of validations prior to calling commit
    If any of these validations fail, the function calls fail_json with a
    validation-specific error message.

    Expected results:
    1. fail_json should be called because action is None
    """

    mock_image_policy_action.switch_issu_details = mock_issu_details
    mock_image_policy_action.policy_name = "KR5M"
    mock_image_policy_action.serial_numbers = [
        "FDO2112189M",
    ]
    match = "ImagePolicyAction.validate_request: "
    match += "instance.action must be set before calling commit()"
    with pytest.raises(AnsibleFailJson, match=match):
        mock_image_policy_action.validate_request()


# test_validate_request_policy_name_none

match = "ImagePolicyAction.validate_request: "
match += "instance.policy_name must be set before calling commit()"


@pytest.mark.parametrize(
    "action,expected",
    [
        ("attach", pytest.raises(AnsibleFailJson, match=match)),
        ("detach", pytest.raises(AnsibleFailJson, match=match)),
        ("query", pytest.raises(AnsibleFailJson, match=match)),
    ],
)
def test_validate_request_policy_name_none(
    action, expected, mock_image_policy_action, mock_issu_details
) -> None:
    """
    validate_request performs a number of validations prior to calling commit
    If any of these validations fail, the function calls fail_json with a
    validation-specific error message.

    Expected results:
    1. fail_json should be called because policy_name is None
    """

    mock_image_policy_action.switch_issu_details = mock_issu_details
    mock_image_policy_action.action = action
    mock_image_policy_action.serial_numbers = [
        "FDO2112189M",
    ]

    with expected:
        mock_image_policy_action.validate_request()


# test_validate_request_serial_numbers_none

match = "ImagePolicyAction.validate_request: "
match += "instance.serial_numbers must be set before calling commit()"


@pytest.mark.parametrize(
    "action,expected",
    [
        ("attach", pytest.raises(AnsibleFailJson, match=match)),
        ("detach", pytest.raises(AnsibleFailJson, match=match)),
        ("query", does_not_raise()),
    ],
)
def test_validate_request_serial_numbers_none(
    action, expected, mock_image_policy_action, mock_issu_details
) -> None:
    """
    validate_request performs a number of validations prior to calling commit
    If any of these validations fail, the function calls fail_json with a
    validation-specific error message.

    Expected results:
    1.  action == attach fail_json should be called
    2.  action == detach fail_json should be called
    3.  action == query fail_json should NOT be called
    """

    mock_image_policy_action.switch_issu_details = mock_issu_details
    mock_image_policy_action.action = action
    mock_image_policy_action.policy_name = "KR5M"

    with expected:
        mock_image_policy_action.validate_request()


# test_validate_request_image_policy_does_not_support_switch_platform

def test_validate_request_image_policy_does_not_support_switch_platform(monkeypatch, mock_image_policy_action, mock_issu_details, mock_image_policies
) -> None:
    """
    validate_request performs a number of validations prior to calling commit
    If any of these validations fail, the function calls fail_json with a
    validation-specific error message.

    Expected results:
    1.  fail_json should be called since the policy KR5M
        supports "N9K switch platform and the response from ImagePolicies
        contains platform == "TEST_UNKNOWN_PLATFORM"
    """

    def mock_dcnm_send_switch_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "ImagePolicyAction_test_validate_request_1"
        return responses_switch_issu_details(key)

    def mock_dcnm_send_image_policies(*args, **kwargs) -> Dict[str, Any]:
        key = "ImagePolicyAction_test_validate_request_1"
        return responses_image_policies(key)

    monkeypatch.setattr(dcnm_send_switch_issu_details, mock_dcnm_send_switch_issu_details)
    monkeypatch.setattr(dcnm_send_image_policies, mock_dcnm_send_image_policies)

    mock_image_policy_action.switch_issu_details = mock_issu_details
    mock_image_policy_action.image_policies = mock_image_policies
    mock_image_policy_action.action = "attach"
    mock_image_policy_action.policy_name = "KR5M"
    mock_image_policy_action.serial_numbers = ["FDO2112189M"]


    match = "ImagePolicyAction.validate_request: "
    match += "policy KR5M does not support platform TEST_UNKNOWN_PLATFORM. "
    match += r"KR5M supports the following platform\(s\): N9K/N3K"

    with pytest.raises(AnsibleFailJson, match=match):
        mock_image_policy_action.validate_request()


# test_commit_unknown_action

def test_commit_action_unknown(monkeypatch, mock_image_policy_action) -> None:
    """
    Verify that fail_json is called if action is unknown.

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

    Expected results:
    1.  action is unknown, so module.fail_json is called
    """

    def mock_dcnm_send_switch_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "ImagePolicyAction_test_commit_all"
        return responses_switch_issu_details(key)

    def mock_dcnm_send_image_policies(*args, **kwargs) -> Dict[str, Any]:
        key = "ImagePolicyAction_test_commit_all"
        return responses_image_policies(key)
    def mock_validate_request(*args, **kwargs) -> None:
        pass

    monkeypatch.setattr(dcnm_send_switch_issu_details, mock_dcnm_send_switch_issu_details)
    monkeypatch.setattr(dcnm_send_image_policies, mock_dcnm_send_image_policies)

    monkeypatch.setattr(mock_image_policy_action, "validate_request", mock_validate_request)
    monkeypatch.setattr(mock_image_policy_action, "valid_actions", {"attach", "detach", "query", "FOO"})

    mock_image_policy_action.policy_name = "KR5M"
    mock_image_policy_action.serial_numbers = ["FDO2112189M"]
    mock_image_policy_action.action = "FOO"

    match = "ImagePolicyAction.commit: Unknown action FOO."

    with pytest.raises(AnsibleFailJson, match=match):
        mock_image_policy_action.commit()


def test_commit_action_detach_success(monkeypatch, mock_image_policy_action) -> None:
    """
    Verify that commit is successful for action == "detach" given a
    200 response from the controller in ImagePolicyAction._detach_policy

    commit calls validate_request() and then calls one of the following
    functions based on the value of action:
        action == "attach" : _attach_policy
        action == "detach" : _detach_policy
        action == "query" : _query_policy

    Expected results:
    1.  action is "detach", so ImagePolicyAction_detach_policy is called
    2.  ImagePolicyAction.response contains RESULT_CODE 200
    3.  commit is successful
    """


    def mock_dcnm_send_image_policies(*args, **kwargs) -> Dict[str, Any]:
        key = "ImagePolicyAction_test_commit_all"
        return responses_image_policies(key)

    def mock_dcnm_send_switch_details(*args, **kwargs) -> Dict[str, Any]:
        key = "ImagePolicyAction_test_commit_all"
        return responses_switch_details(key)

    def mock_dcnm_send_switch_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "ImagePolicyAction_test_commit_all"
        return responses_switch_issu_details(key)

    def mock_dcnm_send_image_policy_action(*args, **kwargs) -> Dict[str, Any]:
        key = "ImagePolicyAction_detach_policy_200"
        return responses_image_policy_action(key)

    monkeypatch.setattr(dcnm_send_image_policies, mock_dcnm_send_image_policies)
    monkeypatch.setattr(dcnm_send_image_policy_action, mock_dcnm_send_image_policy_action)
    monkeypatch.setattr(dcnm_send_switch_details, mock_dcnm_send_switch_details)
    monkeypatch.setattr(dcnm_send_switch_issu_details, mock_dcnm_send_switch_issu_details)

    mock_image_policy_action.policy_name = "KR5M"
    mock_image_policy_action.serial_numbers = ["FDO2112189M"]
    # mock_image_policy_action.serial_numbers = ["FDO21120U5D","FDO211218GC","FOX2109PGD0"]
    mock_image_policy_action.action = "detach"

    mock_image_policy_action.commit()
    assert isinstance(mock_image_policy_action.response, dict)
    assert mock_image_policy_action.response.get("RETURN_CODE") == 200
    assert mock_image_policy_action.response.get("METHOD") == "DELETE"
    assert mock_image_policy_action.response.get("MESSAGE") == "OK"
    assert mock_image_policy_action.response.get("DATA") == "Successfully detach the policy from device."
    assert mock_image_policy_action.result.get("success") == True
    assert mock_image_policy_action.result.get("changed") == True

