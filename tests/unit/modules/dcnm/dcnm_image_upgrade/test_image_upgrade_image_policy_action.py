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
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.api_endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.image_policy_action import \
    ImagePolicyAction
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.switch_issu_details import \
    SwitchIssuDetailsBySerialNumber

from .fixture import load_fixture
from .utils import (does_not_raise, image_policies_fixture,
                    image_policy_action_fixture,
                    issu_details_by_serial_number_fixture,
                    responses_image_policies, responses_image_policy_action,
                    responses_switch_details, responses_switch_issu_details)

PATCH_MODULE_UTILS = "ansible_collections.cisco.dcnm.plugins.module_utils."
PATCH_IMAGE_UPGRADE = PATCH_MODULE_UTILS + "image_upgrade."

DCNM_SEND_IMAGE_POLICIES = PATCH_IMAGE_UPGRADE + "image_policies.dcnm_send"
DCNM_SEND_IMAGE_UPGRADE_COMMON = PATCH_IMAGE_UPGRADE + "image_upgrade_common.dcnm_send"
DCNM_SEND_SWITCH_DETAILS = PATCH_IMAGE_UPGRADE + "switch_details.RestSend.commit"
DCNM_SEND_SWITCH_ISSU_DETAILS = PATCH_IMAGE_UPGRADE + "switch_issu_details.dcnm_send"


def test_image_upgrade_image_policy_action_00001(image_policy_action) -> None:
    """
    Function
    - ImagePolicyAction.__init__

    Test
    - Class attributes initialized to expected values
    - fail_json is not called
    """
    with does_not_raise():
        instance = image_policy_action
    assert instance.class_name == "ImagePolicyAction"
    assert isinstance(instance.endpoints, ApiEndpoints)
    assert isinstance(instance, ImagePolicyAction)
    assert isinstance(instance.switch_issu_details, SwitchIssuDetailsBySerialNumber)
    assert instance.path is None
    assert instance.payloads == []
    assert instance.valid_actions == {"attach", "detach", "query"}
    assert instance.verb is None


def test_image_upgrade_image_policy_action_00002(image_policy_action) -> None:
    """
    Function
    - ImagePolicyAction._init_properties

    Test
    - Class properties are initialized to expected values
    """
    instance = image_policy_action
    assert isinstance(instance.properties, dict)
    assert instance.properties.get("action") is None
    assert instance.properties.get("response") == []
    assert instance.properties.get("response_current") == {}
    assert instance.properties.get("result") == []
    assert instance.properties.get("result_current") == {}
    assert instance.properties.get("policy_name") is None
    assert instance.properties.get("query_result") is None
    assert instance.properties.get("serial_numbers") is None


def test_image_upgrade_image_policy_action_00003(
    monkeypatch, image_policy_action, issu_details_by_serial_number
) -> None:
    """
    Function
    - ImagePolicyAction.build_payload

    Test
    - fail_json is not called
    - image_policy_action.payloads is a list
    - image_policy_action.payloads has length 5

    Description
    build_payload builds the payload to send in the POST request
    to attach policies to devices
    """

    def mock_dcnm_send_switch_issu_details(*args) -> Dict[str, Any]:
        key = "test_image_upgrade_image_policy_action_00003a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(
        DCNM_SEND_SWITCH_ISSU_DETAILS, mock_dcnm_send_switch_issu_details
    )

    instance = image_policy_action
    instance.switch_issu_details = issu_details_by_serial_number
    instance.policy_name = "KR5M"
    instance.serial_numbers = [
        "FDO2112189M",
        "FDO211218AX",
        "FDO211218B5",
        "FDO211218FV",
        "FDO211218GC",
    ]
    with does_not_raise():
        instance.build_payload()
    assert isinstance(instance.payloads, list)
    assert len(instance.payloads) == 5


def test_image_upgrade_image_policy_action_00004(
    monkeypatch, image_policy_action, issu_details_by_serial_number
) -> None:
    """
    Function
    - ImagePolicyAction.build_payload

    Test
    - fail_json is called since deviceName is null in the issu_details_by_serial_number response
    - The error message is matched

    Description
    build_payload builds the payload to send in the POST request
    to attach policies to devices.  If any key in the payload has a value
    of None, the function calls fail_json.
    """

    def mock_dcnm_send_switch_issu_details(*args) -> Dict[str, Any]:
        key = "test_image_upgrade_image_policy_action_00004a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(
        DCNM_SEND_SWITCH_ISSU_DETAILS, mock_dcnm_send_switch_issu_details
    )

    instance = image_policy_action
    instance.switch_issu_details = issu_details_by_serial_number
    instance.policy_name = "KR5M"
    instance.serial_numbers = [
        "FDO2112189M",
    ]
    match = "Unable to determine hostName for switch "
    match += "172.22.150.108, FDO2112189M, None. "
    match += "Please verify that the switch is managed by "
    match += "the controller."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.build_payload()


def test_image_upgrade_image_policy_action_00010(
    image_policy_action, issu_details_by_serial_number
) -> None:
    """
    Function
    - ImagePolicyAction.validate_request

    Test
    - fail_json is called because image_policy_action.action is None
    - The error message is matched

    Description
    validate_request performs a number of validations prior to calling commit.
    If any of these validations fail, the function calls fail_json with a
    validation-specific error message.
    """
    instance = image_policy_action
    instance.switch_issu_details = issu_details_by_serial_number
    instance.policy_name = "KR5M"
    instance.serial_numbers = [
        "FDO2112189M",
    ]
    match = "ImagePolicyAction.validate_request: "
    match += "instance.action must be set before calling commit()"
    with pytest.raises(AnsibleFailJson, match=match):
        instance.validate_request()


MATCH_00011 = "ImagePolicyAction.validate_request: "
MATCH_00011 += "instance.policy_name must be set before calling commit()"


@pytest.mark.parametrize(
    "action,expected",
    [
        ("attach", pytest.raises(AnsibleFailJson, match=MATCH_00011)),
        ("detach", pytest.raises(AnsibleFailJson, match=MATCH_00011)),
        ("query", pytest.raises(AnsibleFailJson, match=MATCH_00011)),
    ],
)
def test_image_upgrade_image_policy_action_00011(
    action, expected, image_policy_action, issu_details_by_serial_number
) -> None:
    """
    Function
    - ImagePolicyAction.validate_request

    Test
    - fail_json is called because image_policy_action.policy_name is None
    - The error message is matched

    Description
    validate_request performs a number of validations prior to calling commit.
    If any of these validations fail, the function calls fail_json with a
    validation-specific error message.
    """
    instance = image_policy_action
    instance.switch_issu_details = issu_details_by_serial_number
    instance.action = action
    instance.serial_numbers = [
        "FDO2112189M",
    ]

    with expected:
        instance.validate_request()


MATCH_00012 = "ImagePolicyAction.validate_request: "
MATCH_00012 += "instance.serial_numbers must be set before calling commit()"


@pytest.mark.parametrize(
    "action,expected",
    [
        ("attach", pytest.raises(AnsibleFailJson, match=MATCH_00012)),
        ("detach", pytest.raises(AnsibleFailJson, match=MATCH_00012)),
        ("query", does_not_raise()),
    ],
)
def test_image_upgrade_image_policy_action_00012(
    action, expected, image_policy_action, issu_details_by_serial_number
) -> None:
    """
    Function
    - ImagePolicyAction.validate_request

    Test
    -   fail_json is called for action == attach because
        image_policy_action.serial_numbers is None
    -   fail_json is called for action == detach because
        image_policy_action.serial_numbers is None
    -   fail_json is NOT called for action == query because
        validate_request is exited early for action == "query"
    -   The error message, if any, is matched

    Description
    validate_request performs a number of validations prior to calling commit,
    If any of these validations fail, the function calls fail_json with a
    validation-specific error message.
    """
    instance = image_policy_action
    instance.switch_issu_details = issu_details_by_serial_number
    instance.action = action
    instance.policy_name = "KR5M"

    with expected:
        instance.validate_request()


def test_image_upgrade_image_policy_action_00013(
    monkeypatch, image_policy_action, issu_details_by_serial_number, image_policies
) -> None:
    """
    Function
    - ImagePolicyAction.validate_request

    Test
    -   fail_json is called because policy KR5M supports playform N9K/N3K
        and the response from ImagePolicies contains platform
        TEST_UNKNOWN_PLATFORM
    -   The error message is matched

    Description
    validate_request performs a number of validations prior to calling commit.
    If any of these validations fail, the function calls fail_json with a
    validation-specific error message.
    """
    key = "test_image_upgrade_image_policy_action_00013a"

    def mock_dcnm_send_switch_issu_details(*args) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_dcnm_send_image_policies(*args) -> Dict[str, Any]:
        return responses_image_policies(key)

    monkeypatch.setattr(
        DCNM_SEND_SWITCH_ISSU_DETAILS, mock_dcnm_send_switch_issu_details
    )
    monkeypatch.setattr(DCNM_SEND_IMAGE_POLICIES, mock_dcnm_send_image_policies)

    instance = image_policy_action
    instance.switch_issu_details = issu_details_by_serial_number
    instance.image_policies = image_policies
    instance.action = "attach"
    instance.policy_name = "KR5M"
    instance.serial_numbers = ["FDO2112189M"]

    match = "ImagePolicyAction.validate_request: "
    match += "policy KR5M does not support platform TEST_UNKNOWN_PLATFORM. "
    match += r"KR5M supports the following platform\(s\): N9K/N3K"

    with pytest.raises(AnsibleFailJson, match=match):
        instance.validate_request()


def test_image_upgrade_image_policy_action_00014(
    monkeypatch, image_policy_action, issu_details_by_serial_number, image_policies
) -> None:
    """
    Function
    - ImagePolicyAction.validate_request

    Summary
    fail_json is called because policy KR5M does not exist on the controller

    Test
    -   fail_json is called because ImagePolicies returns no policies
    -   The error message is matched

    Description
    validate_request performs a number of validations prior to calling commit.
    If any of these validations fail, the function calls fail_json with a
    validation-specific error message.
    """
    key = "test_image_upgrade_image_policy_action_00014a"

    def mock_dcnm_send_switch_issu_details(*args) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_dcnm_send_image_policies(*args) -> Dict[str, Any]:
        return responses_image_policies(key)

    monkeypatch.setattr(
        DCNM_SEND_SWITCH_ISSU_DETAILS, mock_dcnm_send_switch_issu_details
    )
    monkeypatch.setattr(DCNM_SEND_IMAGE_POLICIES, mock_dcnm_send_image_policies)

    instance = image_policy_action
    instance.switch_issu_details = issu_details_by_serial_number
    instance.image_policies = image_policies
    instance.action = "attach"
    instance.policy_name = "KR5M"
    instance.serial_numbers = ["FDO2112189M"]

    match = r"ImagePolicyAction.validate_request: "
    match += r"policy KR5M does not exist on the controller\."

    with pytest.raises(AnsibleFailJson, match=match):
        instance.validate_request()


def test_image_upgrade_image_policy_action_00020(
    monkeypatch, image_policy_action
) -> None:
    """
    Function
    - ImagePolicyAction.commit

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

    def mock_validate_request(*args) -> None:
        pass

    instance = image_policy_action
    monkeypatch.setattr(instance, "validate_request", mock_validate_request)
    monkeypatch.setattr(instance, "valid_actions", {"attach", "detach", "query", "FOO"})

    instance.policy_name = "KR5M"
    instance.serial_numbers = ["FDO2112189M"]
    instance.action = "FOO"

    match = "ImagePolicyAction.commit: Unknown action FOO."

    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()


def test_image_upgrade_image_policy_action_00030(
    monkeypatch, image_policy_action
) -> None:
    """
    Function
    - ImagePolicyAction.commit
    - ImagePolicyAction._detach_policy

    Summary
    Verify that commit behaves as expected when action is "detach"
    and ImagePolicyAction receives a success (200) response
    from the controller.

    Test
    -   ImagePolicyAction._detach_policy is called
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
    key = "test_image_upgrade_image_policy_action_00030a"

    def mock_dcnm_send_image_policies(*args) -> Dict[str, Any]:
        return responses_image_policies(key)

    def mock_dcnm_send_switch_issu_details(*args) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_dcnm_send_image_upgrade_common(*args) -> Dict[str, Any]:
        return responses_image_policy_action(key)

    monkeypatch.setattr(DCNM_SEND_IMAGE_POLICIES, mock_dcnm_send_image_policies)
    monkeypatch.setattr(
        DCNM_SEND_SWITCH_ISSU_DETAILS, mock_dcnm_send_switch_issu_details
    )

    instance = image_policy_action
    monkeypatch.setattr(instance, "dcnm_send", mock_dcnm_send_image_upgrade_common)
    instance.policy_name = "KR5M"
    instance.serial_numbers = ["FDO2112189M"]
    instance.action = "detach"

    instance.commit()
    assert isinstance(instance.response_current, dict)
    assert instance.response_current.get("RETURN_CODE") == 200
    assert instance.response_current.get("METHOD") == "DELETE"
    assert instance.response_current.get("MESSAGE") == "OK"
    assert (
        instance.response_current.get("DATA")
        == "Successfully detach the policy from device."
    )
    assert instance.result_current.get("success") is True
    assert instance.result_current.get("changed") is True


def test_image_upgrade_image_policy_action_00031(
    monkeypatch, image_policy_action
) -> None:
    """
    Function
    - ImagePolicyAction.commit
    - ImagePolicyAction._detach_policy

    Summary
    Verify that commit behaves as expected when action is "detach"
    and ImagePolicyAction receives a failure (500) response
    from the controller.

    Test
    -   ImagePolicyAction._detach_policy is called
    -   commit is unsuccessful given a 500 response from the controller in
        ImagePolicyAction._detach_policy
    -   fail_json is called and the error message is matched
    """
    key = "test_image_upgrade_image_policy_action_00031a"

    def mock_dcnm_send_image_policies(*args) -> Dict[str, Any]:
        return responses_image_policies(key)

    def mock_dcnm_send_switch_issu_details(*args) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_dcnm_send_image_upgrade_common(*args) -> Dict[str, Any]:
        return responses_image_policy_action(key)

    monkeypatch.setattr(DCNM_SEND_IMAGE_POLICIES, mock_dcnm_send_image_policies)
    monkeypatch.setattr(
        DCNM_SEND_SWITCH_ISSU_DETAILS, mock_dcnm_send_switch_issu_details
    )

    with does_not_raise():
        instance = image_policy_action
        instance.policy_name = "KR5M"
        instance.serial_numbers = ["FDO2112189M"]
        instance.action = "detach"
        instance.unit_test = True
    monkeypatch.setattr(instance, "dcnm_send", mock_dcnm_send_image_upgrade_common)

    match = r"ImagePolicyAction\._detach_policy_normal_mode: "
    match += r"Bad result when detaching policy KR5M "
    match += r"from the following device\(s\):"

    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()


def test_image_upgrade_image_policy_action_00040(
    monkeypatch, image_policy_action
) -> None:
    """
    Function
    - ImagePolicyAction.commit
    - ImagePolicyAction._attach_policy

    Summary
    Verify that commit behaves as expected when action is "attach"
    and ImagePolicyAction receives a success (200) response
    from the controller.

    Test
    -   ImagePolicyAction._attach_policy is called
    -   commit is successful given a 200 response from the controller in
        ImagePolicyAction._attach_policy
    -   ImagePolicyAction.response contains RESULT_CODE 200

    Description
    commit calls validate_request() and then calls one of the following
    functions based on the value of action:
        action == "attach" : _attach_policy
        action == "detach" : _detach_policy
        action == "query" : _query_policy
    """
    key = "test_image_upgrade_image_policy_action_00040a"

    def mock_dcnm_send_image_policies(*args) -> Dict[str, Any]:
        return responses_image_policies(key)

    def mock_dcnm_send_switch_issu_details(*args) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_dcnm_send_image_upgrade_common(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_policy_action(key)

    monkeypatch.setattr(DCNM_SEND_IMAGE_POLICIES, mock_dcnm_send_image_policies)
    monkeypatch.setattr(
        DCNM_SEND_SWITCH_ISSU_DETAILS, mock_dcnm_send_switch_issu_details
    )

    instance = image_policy_action
    monkeypatch.setattr(instance, "dcnm_send", mock_dcnm_send_image_upgrade_common)
    instance.policy_name = "KR5M"
    instance.serial_numbers = ["FDO2112189M"]
    instance.action = "attach"

    instance.commit()
    assert isinstance(instance.response_current, dict)
    assert instance.response_current.get("RETURN_CODE") == 200
    assert instance.response_current.get("METHOD") == "POST"
    assert instance.response_current.get("MESSAGE") == "OK"
    assert instance.response_current.get("DATA") == "[cvd-1313-leaf:Success]"
    assert instance.result_current.get("success") is True
    assert instance.result_current.get("changed") is True


def test_image_upgrade_image_policy_action_00041(
    monkeypatch, image_policy_action
) -> None:
    """
    Function
    - ImagePolicyAction.commit
    - ImagePolicyAction._attach_policy

    Summary
    Verify that commit behaves as expected when action is "attach"
    and ImagePolicyAction receives a failure (500) response
    from the controller.

    Test
    -   ImagePolicyAction._attach_policy is called
    -   commit is unsuccessful given a 500 response from the controller in
        ImagePolicyAction._attach_policy
    -   ImagePolicyAction.response contains RESULT_CODE 500
    """
    key = "test_image_upgrade_image_policy_action_00041a"

    def mock_dcnm_send_image_policies(*args) -> Dict[str, Any]:
        return responses_image_policies(key)

    def mock_dcnm_send_switch_issu_details(*args) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_dcnm_send_image_upgrade_common(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_policy_action(key)

    monkeypatch.setattr(DCNM_SEND_IMAGE_POLICIES, mock_dcnm_send_image_policies)
    monkeypatch.setattr(
        DCNM_SEND_SWITCH_ISSU_DETAILS, mock_dcnm_send_switch_issu_details
    )
    with does_not_raise():
        instance = image_policy_action
    monkeypatch.setattr(instance, "dcnm_send", mock_dcnm_send_image_upgrade_common)
    instance.policy_name = "KR5M"
    instance.serial_numbers = ["FDO2112189M"]
    instance.action = "attach"
    instance.unit_test = True

    match = r"ImagePolicyAction\._attach_policy_normal_mode: "
    match += r"Bad result when attaching policy KR5M to switch\. Payload:"
    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()


def test_image_upgrade_image_policy_action_00050(
    monkeypatch, image_policy_action
) -> None:
    """
    Function
    - ImagePolicyAction.commit
    - ImagePolicyAction._query_policy

    Summary
    Verify that commit behaves as expected when action is "query"
    and ImagePolicyAction receives a success (200) response
    from the controller.

    Test
    -   ImagePolicyAction._query_policy is called
    -   commit is successful given a 200 response from the controller in
        ImagePolicyAction._query_policy
    -   ImagePolicyAction.response contains RESULT_CODE 200

    Description
    commit calls validate_request() and then calls one of the following
    functions based on the value of action:
        action == "attach" : _attach_policy
        action == "detach" : _detach_policy
        action == "query" : _query_policy
    """
    key = "test_image_upgrade_image_policy_action_00050a"

    def mock_dcnm_send_image_policies(*args) -> Dict[str, Any]:
        return responses_image_policies(key)

    def mock_dcnm_send_switch_issu_details(*args) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_dcnm_send_image_upgrade_common(*args) -> Dict[str, Any]:
        return responses_image_policy_action(key)

    monkeypatch.setattr(DCNM_SEND_IMAGE_POLICIES, mock_dcnm_send_image_policies)
    monkeypatch.setattr(
        DCNM_SEND_SWITCH_ISSU_DETAILS, mock_dcnm_send_switch_issu_details
    )

    instance = image_policy_action
    monkeypatch.setattr(instance, "dcnm_send", mock_dcnm_send_image_upgrade_common)
    instance.policy_name = "KR5M"
    instance.serial_numbers = ["FDO2112189M"]
    instance.action = "query"

    instance.commit()
    assert isinstance(instance.response_current, dict)
    assert instance.response_current.get("RETURN_CODE") == 200
    assert instance.response_current.get("METHOD") == "GET"
    assert instance.response_current.get("MESSAGE") == "OK"
    assert instance.result_current.get("success") is True
    assert instance.result_current.get("found") is True


def test_image_upgrade_image_policy_action_00051(
    monkeypatch, image_policy_action
) -> None:
    """
    Function
    - ImagePolicyAction.commit
    - ImagePolicyAction._query_policy

    Summary
    Verify that commit behaves as expected when action is "query"
    and ImagePolicyAction receives a failure (500) response
    from the controller.

    Test
    -   fail_json is called and the error message is matched
    """
    key = "test_image_upgrade_image_policy_action_00051a"

    def mock_dcnm_send_image_policies(*args) -> Dict[str, Any]:
        return responses_image_policies(key)

    def mock_dcnm_send_switch_issu_details(*args) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_dcnm_send_image_upgrade_common(*args) -> Dict[str, Any]:
        return responses_image_policy_action(key)

    monkeypatch.setattr(DCNM_SEND_IMAGE_POLICIES, mock_dcnm_send_image_policies)
    monkeypatch.setattr(
        DCNM_SEND_SWITCH_ISSU_DETAILS, mock_dcnm_send_switch_issu_details
    )

    instance = image_policy_action
    monkeypatch.setattr(instance, "dcnm_send", mock_dcnm_send_image_upgrade_common)
    instance.policy_name = "KR5M"
    instance.serial_numbers = ["FDO2112189M"]
    instance.action = "query"
    instance.unit_test = True

    match = r"ImagePolicyAction\._query_policy: "
    match += r"Bad result when querying image policy KR5M\."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()


MATCH_00060 = "ImagePolicyAction.action: instance.action must be "
MATCH_00060 += "one of attach,detach,query. Got FOO."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        ("attach", does_not_raise(), False),
        ("detach", does_not_raise(), False),
        ("query", does_not_raise(), False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00060), True),
    ],
)
def test_image_upgrade_image_policy_action_00060(
    image_policy_action, value, expected, raise_flag
) -> None:
    """
    Function
    - ImagePolicyAction.action setter

    Test
    - Expected values are set
    - fail_json is called when value is not a valid action
    - fail_json error message is matched
    """
    with does_not_raise():
        instance = image_policy_action
    with expected:
        instance.action = value
    if not raise_flag:
        assert instance.action == value


MATCH_00061 = "ImagePolicyAction.serial_numbers: instance.serial_numbers "
MATCH_00061 += "must be a python list of switch serial numbers. Got FOO."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (["FDO2112189M", "FDO21120U5D"], does_not_raise(), False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00061), True),
    ],
)
def test_image_upgrade_image_policy_action_00061(
    image_policy_action, value, expected, raise_flag
) -> None:
    """
    Function
    - ImagePolicyAction.serial_numbers setter

    Test
    - fail_json is not called with value is a list
    - fail_json is called when value is not a list
    - fail_json error message is matched
    """
    with does_not_raise():
        instance = image_policy_action
    with expected:
        instance.serial_numbers = value
    if not raise_flag:
        assert instance.serial_numbers == value


def test_image_upgrade_image_policy_action_00062(image_policy_action) -> None:
    """
    Function
    - ImagePolicyAction.serial_numbers setter

    Test
    - fail_json is called when value is an empty list
    - fail_json error message is matched
    """
    with does_not_raise():
        instance = image_policy_action
    match = r"ImagePolicyAction\.serial_numbers: instance.serial_numbers "
    match += r"must contain at least one switch serial number\."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.serial_numbers = []


MATCH_00070 = r"ImagePolicyAction\.query_result: instance.query_result must be a dict\."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        ({"found": "true", "success": "true"}, does_not_raise(), False),
        ("FOO", does_not_raise(), False),
    ],
)
def test_image_upgrade_image_policy_action_00070(
    image_policy_action, value, expected, raise_flag
) -> None:
    """
    Function
    - ImagePolicyAction.query_result setter

    Summary
    Verify correct behavior of ImagePolicyAction.query_result

    Test
    - fail_json is never called
    """
    with does_not_raise():
        instance = image_policy_action
    with expected:
        instance.query_result = value
    if not raise_flag:
        assert instance.query_result == value


def test_image_upgrade_image_policy_action_00080(image_policy_action) -> None:
    """
    Function
    - ImagePolicyAction.diff_null getter

    Summary
    Verify ImagePolicyAction.diff_null returns the expected value
    """
    with does_not_raise():
        instance = image_policy_action
        diff_null = instance.diff_null
    assert diff_null["action"] is None
    assert diff_null["ip_address"] is None
    assert diff_null["logical_name"] is None
    assert diff_null["policy"] is None
    assert diff_null["serial_number"] is None
