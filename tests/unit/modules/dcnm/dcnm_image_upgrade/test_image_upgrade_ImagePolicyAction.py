"""
controller_version: 12
description: Verify functionality of ImageStage
"""

from contextlib import contextmanager
from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson

from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policy_action import ImagePolicyAction
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import SwitchIssuDetailsBySerialNumber

from .fixture import load_fixture


@contextmanager
def does_not_raise():
    yield


patch_module_utils = "ansible_collections.cisco.dcnm.plugins.module_utils."
patch_image_mgmt  = patch_module_utils + "image_mgmt."

dcnm_send_issu_details = patch_image_mgmt + "switch_issu_details.dcnm_send"

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
    return ImagePolicyAction(MockAnsibleModule)


@pytest.fixture
def mock_issu_details() -> SwitchIssuDetailsBySerialNumber:
    return SwitchIssuDetailsBySerialNumber(MockAnsibleModule)


# test_init


def test_init(module) -> None:
    module.__init__(MockAnsibleModule)
    assert isinstance(module, ImagePolicyAction)
    assert isinstance(module.switch_issu_details, SwitchIssuDetailsBySerialNumber)
    assert module.valid_actions == {"attach", "detach", "query"}


# test_init_properties


def test_init_properties(module) -> None:
    """
    Properties are initialized to expected values
    """
    module._init_properties()
    assert isinstance(module.properties, dict)
    assert module.properties.get("action") == None
    assert module.properties.get("response") == None
    assert module.properties.get("result") == None
    assert module.properties.get("policy_name") == None
    assert module.properties.get("query_result") == None
    assert module.properties.get("serial_numbers") == None


# test_build_attach_payload


def test_build_attach_payload(monkeypatch, module, mock_issu_details) -> None:
    """
    build_attach_payload builds the payload to send in the POST request
    to attach policies to devices

    Expectations:
    1. module.payload should be a list()

    Expected results:
    1. module.fail_json should not be called
    2. module.payloads should be a list()
    3. module.payloads should have length 5
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "ImagePolicyAction_test_build_attach_payload"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.switch_issu_details = mock_issu_details
    module.policy_name = "KR5M"
    module.serial_numbers = [
        "FDO2112189M",
        "FDO211218AX",
        "FDO211218B5",
        "FDO211218FV",
        "FDO211218GC",
    ]
    with does_not_raise():
        module.build_attach_payload()
    assert isinstance(module.payloads, list)
    assert len(module.payloads) == 5


# test_build_attach_payload_fail_json


def test_build_attach_payload_fail_json(monkeypatch, module, mock_issu_details) -> None:
    """
    build_attach_payload builds the payload to send in the POST request
    to attach policies to devices.  If any key in the payload has a value
    of None, the function calls fail_json.

    Expected results:
    1. module.fail_json should be called because deviceName is None in the issu_details response
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "ImagePolicyAction_test_build_attach_payload_fail_json"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.switch_issu_details = mock_issu_details
    module.policy_name = "KR5M"
    module.serial_numbers = [
        "FDO2112189M",
    ]
    error_message = "Unable to determine hostName for switch "
    error_message += "172.22.150.108, FDO2112189M, None. "
    error_message += "Please verify that the switch is managed by NDFC."
    with pytest.raises(AnsibleFailJson, match=error_message):
        module.build_attach_payload()


# test_validate_request_policy_name_none


def test_validate_request_action_none(module, mock_issu_details) -> None:
    """
    validate_request performs a number of validations prior to calling commit
    If any of these validations fail, the function calls fail_json with a
    validation-specific error message.

    Expected results:
    1. module.fail_json should be called because module.action is None
    """

    module.switch_issu_details = mock_issu_details
    module.policy_name = "KR5M"
    module.serial_numbers = [
        "FDO2112189M",
    ]
    match = "ImagePolicyAction.validate_request: "
    match += "instance.action must be set before calling commit()"
    with pytest.raises(AnsibleFailJson, match=match):
        module.validate_request()


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
    action, expected, module, mock_issu_details
) -> None:
    """
    validate_request performs a number of validations prior to calling commit
    If any of these validations fail, the function calls fail_json with a
    validation-specific error message.

    Expected results:
    1. module.fail_json should be called because module.policy_name is None
    """

    module.switch_issu_details = mock_issu_details
    module.action = action
    module.serial_numbers = [
        "FDO2112189M",
    ]

    with expected:
        module.validate_request()


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
    action, expected, module, mock_issu_details
) -> None:
    """
    validate_request performs a number of validations prior to calling commit
    If any of these validations fail, the function calls fail_json with a
    validation-specific error message.

    Expected results:
    1.  action == attach module.fail_json should be called
    2.  action == detach module.fail_json should be called
    3.  action == query module.fail_json should NOT be called
    """

    module.switch_issu_details = mock_issu_details
    module.action = action
    module.policy_name = "KR5M"

    with expected:
        module.validate_request()
