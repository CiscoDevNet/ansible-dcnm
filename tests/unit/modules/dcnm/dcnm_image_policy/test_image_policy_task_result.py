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
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.image_policy_task_result import \
    ImagePolicyTaskResult
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_image_policy.utils import (
    does_not_raise, image_policy_task_result_fixture,
    results_image_policy_task_result)


def test_image_policy_task_result_00010(image_policy_task_result) -> None:
    """
    Classes and Methods
    - ImagePolicyTaskResult
        - __init__()

    Test
    - Class attributes are initialized to expected values
    - fail_json is not called
    """
    with does_not_raise():
        instance = image_policy_task_result
    assert instance.class_name == "ImagePolicyTaskResult"
    assert isinstance(instance.diff_properties, dict)
    assert isinstance(instance.response_properties, dict)
    assert isinstance(instance.properties, dict)
    assert instance.diff_deleted == []
    assert instance.diff_merged == []
    assert instance.diff_overridden == []
    assert instance.diff_query == []
    assert instance.diff_replaced == []
    assert instance.response_deleted == []
    assert instance.response_merged == []
    assert instance.response_overridden == []
    assert instance.response_query == []
    assert instance.response_replaced == []
    assert instance.diff_properties["diff_deleted"] == "deleted"
    assert instance.diff_properties["diff_merged"] == "merged"
    assert instance.diff_properties["diff_overridden"] == "overridden"
    assert instance.diff_properties["diff_query"] == "query"
    assert instance.diff_properties["diff_replaced"] == "replaced"
    assert instance.response_properties["response_deleted"] == "deleted"
    assert instance.response_properties["response_merged"] == "merged"
    assert instance.response_properties["response_overridden"] == "overridden"
    assert instance.response_properties["response_query"] == "query"
    assert instance.response_properties["response_replaced"] == "replaced"
    assert instance.states == ["deleted", "merged", "overridden", "query", "replaced"]


def test_image_policy_task_result_00020(image_policy_task_result) -> None:
    """
    Classes and Methods
    - ImagePolicyTaskResult
        - __init__()
        - did_anything_change()

    Summary
    -   Verify that did_anything_change() returns False when nothing has changed.

    Setup
    -   diff_properties is not modified, hence all keys have values of empty lists
    """
    with does_not_raise():
        instance = image_policy_task_result
    assert instance.did_anything_change() is False


def test_image_policy_task_result_00021(image_policy_task_result) -> None:
    """
    Classes and Methods
    - ImagePolicyTaskResult
        - __init__()
        - did_anything_change()

    Summary
    -   Verify that did_anything_change() returns False when only query diffs
        have been modified.

    Setup
    - diff_properties["query"] is modified to contain one element
    """
    with does_not_raise():
        instance = image_policy_task_result
        instance.diff_query = {"foo": "bar"}
    assert instance.did_anything_change() is False


@pytest.mark.parametrize("state", ["deleted", "merged", "overridden", "replaced"])
def test_image_policy_task_result_00022(image_policy_task_result, state) -> None:
    """
    Classes and Methods
    - ImagePolicyTaskResult
        - __init__()
        - did_anything_change()

    Summary
    -   Verify that did_anything_change() returns True when other diffs
        have been modified.

    Setup
    - diff_properties["query"] is modified to contain one element
    """
    with does_not_raise():
        instance = image_policy_task_result
        if state == "deleted":
            instance.diff_deleted = {"foo": "bar"}
        if state == "merged":
            instance.diff_merged = {"foo": "bar"}
        if state == "overridden":
            instance.diff_overridden = {"foo": "bar"}
        if state == "replaced":
            instance.diff_replaced = {"foo": "bar"}
    assert instance.did_anything_change() is True


def test_image_policy_task_result_00030(image_policy_task_result) -> None:
    """
    Classes and Methods
    - ImagePolicyTaskResult
        - __init__()
        - @failed_result getter

    Test
    - fail_result returns expected value
    - fail_json is not called
    """
    key = "test_image_policy_task_result_00030a"
    with does_not_raise():
        instance = image_policy_task_result
    assert instance.failed_result == results_image_policy_task_result(key)


@pytest.mark.parametrize(
    "state, key",
    [
        ("deleted", "test_image_policy_task_result_00040a"),
        ("merged", "test_image_policy_task_result_00040b"),
        ("overridden", "test_image_policy_task_result_00040c"),
        ("query", "test_image_policy_task_result_00040d"),
        ("replaced", "test_image_policy_task_result_00040e"),
    ],
)
def test_image_policy_task_result_00040(image_policy_task_result, state, key) -> None:
    """
    Classes and Methods
    - ImagePolicyTaskResult
        - __init__()
        - @module_result getter

    Summary
    Verify that module_result returns expected value when diff_deleted and
    response_deleted are not empty.

    Test
    - module_result returns expected value
    - fail_json is not called
    """
    with does_not_raise():
        instance = image_policy_task_result
        if state == "deleted":
            instance.diff_deleted = {"foo": "bar"}
            instance.response_deleted = {"foo": "bar"}
        if state == "merged":
            instance.diff_merged = {"foo": "bar"}
            instance.response_merged = {"foo": "bar"}
        if state == "overridden":
            instance.diff_overridden = {"foo": "bar"}
            instance.response_overridden = {"foo": "bar"}
        if state == "query":
            instance.diff_query = {"foo": "bar"}
            instance.response_query = {"foo": "bar"}
        if state == "replaced":
            instance.diff_replaced = {"foo": "bar"}
            instance.response_replaced = {"foo": "bar"}
    assert instance.module_result == results_image_policy_task_result(key)


MATCH__00050 = r"ImagePolicyTaskResult\._verify_is_dict: value must be a dict\."


@pytest.mark.parametrize(
    "arg, expected",
    [
        ({"foo": "bar"}, does_not_raise()),
        ("foo", pytest.raises(AnsibleFailJson, match=MATCH__00050)),
        (1, pytest.raises(AnsibleFailJson, match=MATCH__00050)),
        (True, pytest.raises(AnsibleFailJson, match=MATCH__00050)),
        ([], pytest.raises(AnsibleFailJson, match=MATCH__00050)),
    ],
)
def test_image_policy_task_result_00050(
    image_policy_task_result, arg, expected
) -> None:
    """
    Classes and Methods
    - ImagePolicyTaskResult
        - __init__()
        - _verify_is_dict()

    Summary
    Verify proper behavior of ImagePolicyTaskResult()._verify_is_dict()

    Test
    - _verify_is_dict() does not call fail_json when arg is a dict.
    - _verify_is_dict() calls fail_json when arg is not a dict.
    """
    with does_not_raise():
        instance = image_policy_task_result
    with expected:
        instance._verify_is_dict(arg)
