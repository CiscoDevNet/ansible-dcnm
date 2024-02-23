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
# Also, fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=unused-import
# pylint: disable=redefined-outer-name
# pylint: disable=protected-access
# pylint: disable=unused-argument
# pylint: disable=invalid-name

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_image_policy.utils import (
    MockImagePolicies, does_not_raise, image_policy_common_fixture,
    responses_image_policy_common, results_image_policy_common)


def test_image_policy_common_00010(image_policy_common) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()

    Summary
    Verify that the class attributes are initialized to expected values
    and that fail_json is not called.

    Test
    - Class attributes are initialized to expected values
    - fail_json is not called
    """
    with does_not_raise():
        instance = image_policy_common
    assert instance.class_name == "ImagePolicyCommon"
    assert instance.changed is False
    assert instance.failed is False
    assert instance.response == []
    assert instance.response_current == {}
    assert instance.result == []
    assert instance.result_current == {}
    assert instance.diff == []
    assert instance.response_data == []


def test_image_policy_common_00020(image_policy_common) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
        - _handle_response()
        - _handle_get_response()

    Summary
    Verify that _handle_response() calls the appropriate methods when verb == GET
    and response is successful (RETURN_CODE == 200) and that a proper result is
    returned.

    Setup
    - verb is set to GET
    - response RETURN_CODE == 200
    - response MESSAGE == "OK"

    Test
    - _handle_response() calls _handle_response_get()
    - _handle_response_get() returns a proper result
    - fail_json is not called
    """
    key = "test_image_policy_common_00020a"
    verb = "GET"

    with does_not_raise():
        instance = image_policy_common
        result = instance._handle_response(responses_image_policy_common(key), verb)
    assert result == {"success": True, "found": True}


def test_image_policy_common_00021(image_policy_common) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
        - _handle_response()
        - _handle_get_response()

    Summary
    Verify that _handle_response() returns a proper result when verb == GET
    and response is unsuccessful (RETURN_CODE == 404 and MESSAGE == "Not Found").

    Setup
    - verb is set to GET
    - response RETURN_CODE == 404
    - response MESSAGE == "Not Found"

    Test
    - _handle_response() calls _handle_response_get()
    - _handle_response_get() returns a proper result
    - fail_json is not called
    """
    key = "test_image_policy_common_00021a"
    verb = "GET"

    with does_not_raise():
        instance = image_policy_common
        result = instance._handle_response(responses_image_policy_common(key), verb)
    assert result == {"success": True, "found": False}


def test_image_policy_common_00022(image_policy_common) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
        - _handle_response()
        - _handle_get_response()

    Summary
    Verify that _handle_response() returns a proper result when verb == GET
    and response is unsuccessful (RETURN_CODE == 500 and MESSAGE == "Internal Server Error").

    Setup
    - verb is set to GET
    - response RETURN_CODE == 500
    - response MESSAGE == "Internal Server Error"

    Test
    - _handle_response() calls _handle_response_get()
    - _handle_response_get() returns a proper result
    - fail_json is not called
    """
    key = "test_image_policy_common_00022a"
    verb = "GET"

    with does_not_raise():
        instance = image_policy_common
        result = instance._handle_response(responses_image_policy_common(key), verb)
    assert result == {"success": False, "found": False}


@pytest.mark.parametrize("verb", ["POST", "PUT", "DELETE"])
def test_image_policy_common_00030(image_policy_common, verb) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
        - _handle_response()
        - _handle_post_put_delete_response()

    Summary
    Verify that _handle_response() calls the appropriate methods when verb == POST
    and response is successful (MESSAGE = "OK") and that a proper result is
    returned.

    Setup
    - verb == POST
    - response MESSAGE == "OK"

    Test
    - _handle_response() calls _handle_post_put_delete_response()
    - _handle_post_put_delete_response() returns a proper result
    - fail_json is not called

    Discussion
    RESULT_CODE is not checked or used in the code, so it is not tested.
    """
    key = "test_image_policy_common_00030a"

    with does_not_raise():
        instance = image_policy_common
        result = instance._handle_response(responses_image_policy_common(key), verb)
    assert result == {"success": True, "changed": True}


@pytest.mark.parametrize("verb", ["POST", "PUT", "DELETE"])
def test_image_policy_common_00031(image_policy_common, verb) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
        - _handle_response()
        - _handle_post_put_delete_response()

    Summary
    Verify that _handle_response() calls the appropriate methods when verb == POST
    and response is unsuccessful (MESSAGE != "OK") and that a proper result is
    returned.

    Setup
    - verb == POST
    - response MESSAGE == "NOK"

    Test
    - _handle_response() calls _handle_post_put_delete_response()
    - _handle_post_put_delete_response() returns a proper result
    - fail_json is not called

    Discussion
    RESULT_CODE is not checked or used in the code, so it is not tested.
    """
    key = "test_image_policy_common_00031a"

    with does_not_raise():
        instance = image_policy_common
        result = instance._handle_response(responses_image_policy_common(key), verb)
    assert result == {"success": False, "changed": False}


@pytest.mark.parametrize("verb", ["POST", "PUT", "DELETE"])
def test_image_policy_common_00032(image_policy_common, verb) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
        - _handle_response()
        - _handle_post_put_delete_response()

    Summary
    Verify that _handle_response() calls the appropriate methods when verb == POST
    and response is unsuccessful (ERROR key is present) and that a proper result is
    returned.

    Setup
    - verb == POST
    - response ERROR == "Oh no!"

    Test
    - _handle_response() calls _handle_post_put_delete_response()
    - _handle_post_put_delete_response() returns a proper result
    - fail_json is not called

    Discussion
    RESULT_CODE is not checked or used in the code, so it is not tested.
    """
    key = "test_image_policy_common_00032a"

    with does_not_raise():
        instance = image_policy_common
        result = instance._handle_response(responses_image_policy_common(key), verb)
    assert result == {"success": False, "changed": False}


@pytest.mark.parametrize(
    "arg, return_value",
    [
        (True, True),
        (False, False),
        ("True", True),
        ("False", False),
        ("true", True),
        ("false", False),
        (1, 1),
        ("tru", "tru"),
        ("fals", "fals"),
        (None, None),
        ({"foo"}, {"foo"}),
    ],
)
def test_image_policy_common_00040(image_policy_common, arg, return_value) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
        - make_boolean()

    Summary
    Verify that make_boolean() returns expected values for various inputs.

    Test
    - make_boolean() returns expected values
    - fail_json is not called
    """
    with does_not_raise():
        instance = image_policy_common
        value = instance.make_boolean(arg)
    assert value == return_value


@pytest.mark.parametrize(
    "arg, return_value",
    [
        ("", None),
        ("none", None),
        ("None", None),
        ("NONE", None),
        ("null", None),
        ("Null", None),
        ("NULL", None),
        (None, None),
        ("False", "False"),
        ("true", "true"),
        (1, 1),
        ({"foo"}, {"foo"}),
        (True, True),
        (False, False),
    ],
)
def test_image_policy_common_00050(image_policy_common, arg, return_value) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
        - make_none()

    Summary
    Verify that make_none() returns expected values for various inputs.

    Test
    - make_none() returns expected values
    - fail_json is not called
    """
    with does_not_raise():
        instance = image_policy_common
        value = instance.make_none(arg)
    assert value == return_value


MATCH_00060 = r"ImagePolicyCommon.changed: changed must be a bool\."


@pytest.mark.parametrize(
    "arg, expected, flag",
    [
        (True, does_not_raise(), True),
        (False, does_not_raise(), True),
        (None, pytest.raises(AnsibleFailJson, match=MATCH_00060), False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00060), False),
    ],
)
def test_image_policy_common_00060(image_policy_common, arg, expected, flag) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
        - @changed getter/setter

    Summary
    Verify that instance.changed returns expected values and
    calls fail_json appropriately.

    Test
    - @changed returns expected values
    - fail_json is called when unexpected values are passed
    - fail_json is not called when expected values are passed
    """
    with does_not_raise():
        instance = image_policy_common
    with expected:
        instance.changed = arg
    if flag is True:
        assert instance.changed == arg
    else:
        assert instance.changed == False


MATCH_00070 = r"ImagePolicyCommon.diff: diff must be a dict\."


@pytest.mark.parametrize(
    "arg, return_value, expected, flag",
    [
        ({}, [{}], does_not_raise(), True),
        ({"foo": "bar"}, [{"foo": "bar"}], does_not_raise(), True),
        (None, None, pytest.raises(AnsibleFailJson, match=MATCH_00070), False),
        ("FOO", None, pytest.raises(AnsibleFailJson, match=MATCH_00070), False),
    ],
)
def test_image_policy_common_00070(
    image_policy_common, arg, return_value, expected, flag
) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
        - @diff getter/setter

    Summary
    Verify that instance.diff returns expected values and
    calls fail_json appropriately.

    Test
    - @diff returns expected values
    - fail_json is called when unexpected values are passed
    - fail_json is not called when expected values are passed
    """
    with does_not_raise():
        instance = image_policy_common
    with expected:
        instance.diff = arg
    if flag is True:
        assert instance.diff == return_value
    else:
        assert instance.diff == []


MATCH_00080 = r"ImagePolicyCommon.failed: failed must be a bool\."


@pytest.mark.parametrize(
    "arg, expected, flag",
    [
        (True, does_not_raise(), True),
        (False, does_not_raise(), True),
        (None, pytest.raises(AnsibleFailJson, match=MATCH_00080), False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00080), False),
    ],
)
def test_image_policy_common_00080(image_policy_common, arg, expected, flag) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
        - @failed getter/setter

    Summary
    Verify that instance.failed returns expected values and
    calls fail_json appropriately.

    Test
    - @failed returns expected values
    - fail_json is called when unexpected values are passed
    - fail_json is not called when expected values are passed
    """
    with does_not_raise():
        instance = image_policy_common
    with expected:
        instance.failed = arg
    if flag is True:
        assert instance.failed == arg
    else:
        assert instance.failed == False


def test_image_policy_common_00090(image_policy_common) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
        - @failed_result getter

    Summary
    Verify that failed_result returns expected value.

    Test
    - @failed_result returns expected value
    - fail_json is not called
    """
    key = "test_image_policy_common_00090a"
    with does_not_raise():
        instance = image_policy_common
        value = instance.failed_result
    assert value == results_image_policy_common(key)
