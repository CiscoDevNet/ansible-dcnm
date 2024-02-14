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
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_image_policy.utils import (
    MockImagePolicies, does_not_raise, image_policies_all_policies, image_policy_query_fixture)


def test_image_policy_query_00010(image_policy_query) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
    - ImagePolicyQuery
        - __init__()

    Test
    - Class attributes are initialized to expected values
    - fail_json is not called
    """
    with does_not_raise():
        instance = image_policy_query
    assert instance.class_name == "ImagePolicyQuery"
    assert instance.action == "query"
    assert isinstance(instance._image_policies, ImagePolicies)
    assert instance.policy_names is None
    assert instance.changed is False
    assert instance.failed is False


def test_image_policy_query_00020(image_policy_query) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
    - ImagePolicyQuery
        - __init__()
        - policy_names setter

    Test
    - policy_names is set to expected value
    - fail_json is not called
    """
    policy_names = ["FOO", "BAR"]
    with does_not_raise():
        instance = image_policy_query
        instance.policy_names = policy_names
    assert instance.policy_names == policy_names


def test_image_policy_query_00021(image_policy_query) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
    - ImagePolicyQuery
        - __init__()
        - policy_names setter

    Test
    - fail_json is called because policy_names is not a list
    - instance.policy_names is not modified, hence it retains its initial value of None
    """
    match = "ImagePolicyQuery.policy_names: "
    match += "policy_names must be a list."

    with does_not_raise():
        instance = image_policy_query
    with pytest.raises(AnsibleFailJson, match=match):
        instance.policy_names = "NOT_A_LIST"
    assert instance.policy_names is None


def test_image_policy_query_00022(image_policy_query) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
    - ImagePolicyQuery
        - __init__()
        - policy_names setter

    Test
    - fail_json is called because policy_names is a list with a non-string element
    - instance.policy_names is not modified, hence it retains its initial value of None
    """
    match = "ImagePolicyQuery.policy_names: "
    match += "policy_names must be a list of strings."

    with does_not_raise():
        instance = image_policy_query
    with pytest.raises(AnsibleFailJson, match=match):
        instance.policy_names = [1, 2, 3]
    assert instance.policy_names is None


def test_image_policy_query_00023(image_policy_query) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
    - ImagePolicyQuery
        - __init__()
        - policy_names setter

    Test
    - fail_json is called because policy_names is not set prior to calling commit
    - instance.policy_names is not modified, hence it retains its initial value of None
    """
    match = "ImagePolicyQuery.commit: "
    match += "policy_names must be set prior to calling commit."

    with does_not_raise():
        instance = image_policy_query
    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()
    assert instance.policy_names is None


def test_image_policy_query_00024(image_policy_query) -> None:
    """
    Classes and Methods
    - ImagePolicyQuery
        - policy_names setter

    Setup
    -   ImagePolicyQuery().policy_names is set to an empty list

    Test
    -   fail_json is called from policy_names setter
    -   instance.changed is False
    """
    match = "ImagePolicyQuery.policy_names: policy_names must be a list of "
    match += "at least one string."
    with pytest.raises(AnsibleFailJson, match=match):
        instance = image_policy_query
        instance.policy_names = []
    assert instance.changed is False


def test_image_policy_query_00030(monkeypatch, image_policy_query) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
        - _verify_image_policy_ref_count()
    - ImagePolicyQuery
        - __init__()
        - policy_names setter
        - _get_policies_to_query()
        - commit()

    Setup
    -   ImagePolicies().all_policies, is mocked to indicate that two image policies
        (KR5M, NR3F) exist on the controller.
    -   ImagePolicyQuery.policy_names is set to contain one policy_name (FOO)
        that does not exist on the controller.

    Test
    -   commit() calls _get_policies_to_query() which sets instance._policies_to_query
        to an empty list.
    -   commit() sets instance.changed to False
    -   commit() sets instance.failed to False
    -   commit() returns without doing anything else
    -   fail_json is not called
    """
    key = "test_image_policy_query_00030a"

    with does_not_raise():
        instance = image_policy_query
        instance.policy_names = ["FOO"]
    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
    with does_not_raise():
        instance.commit()
    assert instance._policies_to_query == []
    assert instance.changed is False
    assert instance.failed is False


def test_image_policy_query_00031(monkeypatch, image_policy_query) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
    - ImagePolicyQuery
        - __init__()
        - policy_names setter
        - _get_policies_to_query()
        - commit()

    Setup
    -   ImagePolicies().all_policies is mocked to indicate that two image policies
        (KR5M, NR3F) exist on the controller.
    -   ImagePolicyQuery.policy_names is set to contain one policy_name (KR5M)
        that exists on the controller.

    Test
    -   instance._policies_to_query contains one policy name (KR5M)
    -   instance.diff is a list containing one dict with keys action == "query" and policyName == "KR5M"
    -   instance.response is a list with one element
    -   instance.response_current is a dict with key RETURN_CODE == 200
    -   instance.result is a list with one element
    -   instance.result_current is a dict with key success == True
    """
    key = "test_image_policy_query_00031a"

    with does_not_raise():
        instance = image_policy_query
        instance.policy_names = ["KR5M"]
        monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
        instance.commit()
    assert instance._policies_to_query == ["KR5M"]
    assert isinstance(instance.diff, list)
    assert len(instance.diff) == 1
    assert instance.diff[0]["action"] == "query"
    assert instance.diff[0]["policyName"] == "KR5M"
    assert isinstance(instance.response, list)
    assert len(instance.response) == 1
    assert isinstance(instance.response_current, dict)
    assert instance.response_current["RETURN_CODE"] == 200
    assert isinstance(instance.result, list)
    assert len(instance.result) == 1
    assert isinstance(instance.result_current, dict)
    assert instance.result_current["success"] is True


def test_image_policy_query_00032(monkeypatch, image_policy_query) -> None:
    """
    Classes and Methods
    - ImagePolicyQuery
        - policy_names setter
        - _get_policies_to_query()
        - commit()

    Setup
    -   ImagePolicies().all_policies, is mocked to indicate that two image policies
        (KR5M, NR3F) exist on the controller.
    -   ImagePolicyQuery().policy_names is set to contain one image policy name (FOO)
        that does not exist on the controller and two image policy names (KR5M, NR3F)
        that do exist on the controller.

    Test
    -   instance._policies_to_query contains two policy names (KR5M, NR3F)
    -   instance.diff is a list containing two elements
    -   instance.diff[0] contains keys action == "query" and policyName == "KR5M"
    -   instance.diff[1] contains keys action == "query" and policyName == "NR3F"
    -   instance.response is a list with one element
    -   instance.response_current is a dict with key RETURN_CODE == 200
    -   instance.result is a list with one element
    -   instance.result_current is a dict with key success == True
    """
    key = "test_image_policy_query_00032a"

    with does_not_raise():
        instance = image_policy_query
        instance.policy_names = ["FOO", "KR5M", "NR3F"]
        monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
        instance.commit()
    assert instance._policies_to_query == ["KR5M", "NR3F"]
    assert isinstance(instance.diff, list)
    assert len(instance.diff) == 2
    assert instance.diff[0]["action"] == "query"
    assert instance.diff[1]["action"] == "query"
    assert instance.diff[0]["policyName"] == "KR5M"
    assert instance.diff[1]["policyName"] == "NR3F"
    assert isinstance(instance.response, list)
    assert len(instance.response) == 1
    assert isinstance(instance.response_current, dict)
    assert instance.response_current["RETURN_CODE"] == 200
    assert isinstance(instance.result, list)
    assert len(instance.result) == 1
    assert isinstance(instance.result_current, dict)
    assert instance.result_current["success"] is True


def test_image_policy_query_00033(monkeypatch, image_policy_query) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
    - ImagePolicyQuery
        - __init__()
        - policy_names setter
        - _get_policies_to_query()
        - commit()

    Setup
    -   ImagePolicies().all_policies, is mocked to indicate that no image policies
        exist on the controller.
    -   ImagePolicyQuery.policy_names is set to contain one policy_name (FOO)
        that does not exist on the controller.

    Test
    -   commit() calls _get_policies_to_query() which sets instance._policies_to_query
        to an empty list.
    -   commit() sets instance.changed to False
    -   commit() sets instance.failed to False
    -   commit() returns without doing anything else
    -   fail_json is not called
    """
    key = "test_image_policy_query_00033a"

    with does_not_raise():
        instance = image_policy_query
        instance.policy_names = ["FOO"]
    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
    with does_not_raise():
        instance.commit()
    assert instance._policies_to_query == []
    assert instance.changed is False
    assert instance.failed is False
