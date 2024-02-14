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
    MockImagePolicies, does_not_raise, image_policies_all_policies,
    image_policy_delete_fixture, responses_image_policy_delete,
    results_image_policy_delete)


def test_image_policy_delete_00010(image_policy_delete) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
    - ImagePolicyDelete
        - __init__()

    Test
    - Class attributes are initialized to expected values
    - fail_json is not called
    """
    with does_not_raise():
        instance = image_policy_delete
    assert instance.class_name == "ImagePolicyDelete"
    assert instance.action == "delete"
    assert isinstance(instance.endpoints, ApiEndpoints)
    assert instance.verb == "DELETE"
    assert (
        instance.path
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policy"
    )
    assert instance.policy_names is None


def test_image_policy_delete_00020(image_policy_delete) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
    - ImagePolicyDelete
        - __init__()
        - policy_names setter

    Test
    - policy_names is set to expected value
    - fail_json is not called
    """
    policy_names = ["FOO", "BAR"]
    with does_not_raise():
        instance = image_policy_delete
        instance.policy_names = policy_names
    assert instance.policy_names == policy_names


def test_image_policy_delete_00021(image_policy_delete) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
    - ImagePolicyDelete
        - __init__()
        - policy_names setter

    Test
    - fail_json is called because policy_names is not a list
    - instance.policy_names is not modified, hence it retains its initial value of None
    """
    match = "ImagePolicyDelete.policy_names: "
    match += "policy_names must be a list."

    with does_not_raise():
        instance = image_policy_delete
    with pytest.raises(AnsibleFailJson, match=match):
        instance.policy_names = "NOT_A_LIST"
    assert instance.policy_names is None


def test_image_policy_delete_00022(image_policy_delete) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
    - ImagePolicyDelete
        - __init__()
        - policy_names setter

    Test
    - fail_json is called because policy_names is a list with a non-string element
    - instance.policy_names is not modified, hence it retains its initial value of None
    """
    match = "ImagePolicyDelete.policy_names: "
    match += "policy_names must be a list of strings."

    with does_not_raise():
        instance = image_policy_delete
    with pytest.raises(AnsibleFailJson, match=match):
        instance.policy_names = [1, 2, 3]
    assert instance.policy_names is None


def test_image_policy_delete_00030(monkeypatch, image_policy_delete) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
        - _verify_image_policy_ref_count()
    - ImagePolicyDelete
        - __init__()
        - policy_names setter
        - _get_policies_to_delete()

    Setup
    -   ImagePolicies().all_policies, is mocked to indicate that two image policies
        (KR5M, NR3F) exist on the controller.
    -   ImagePolicyDelete.policy_names is set to contain one policy_name (FOO)
        that does not exist on the controller.

    Test
    -   instance._policies_to_delete will an empty list because all of the
        policy_names in instance.policy_names do not exist on the controller
        and, hence, nothing needs to be deleted.
    """
    key = "test_image_policy_delete_00030a"

    instance = image_policy_delete
    instance.policy_names = ["FOO"]
    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
    instance._get_policies_to_delete()
    assert instance._policies_to_delete == []


def test_image_policy_delete_00031(monkeypatch, image_policy_delete) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon
        - __init__()
        - _verify_image_policy_ref_count()
    - ImagePolicyDelete
        - __init__()
        - policy_names setter
        - _get_policies_to_delete()

    Setup
    -   ImagePolicies().all_policies is mocked to indicate that two image policies
        (KR5M, NR3F) exist on the controller.
    -   ImagePolicyDelete.policy_names is set to contain one policy_name (KR5M)
        that exists on the controller.

    Test
    -   instance._policies_to_delete will contain one policy name (KR5M)
    """
    key = "test_image_policy_delete_00031a"

    instance = image_policy_delete
    instance.policy_names = ["KR5M"]
    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
    instance._get_policies_to_delete()
    assert instance._policies_to_delete == ["KR5M"]


def test_image_policy_delete_00032(monkeypatch, image_policy_delete) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateCommon
        - payloads setter
        - _build_payloads_to_commit()
    - ImagePolicyCreateBulk
        - __init__()

    Setup
    -   ImagePolicies().all_policies, is mocked to indicate that two image policies
        (KR5M, NR3F) exist on the controller.
    -   ImagePolicyDelete().policy_names is set to contain one image policy name (FOO)
        that does not exist on the controller and one image policy name (KR5M) that
        does exist on the controller.

    Test
    -   instance._policies_to_delete will contain one policy name (KR5M)
    """
    key = "test_image_policy_delete_00032a"

    instance = image_policy_delete
    instance.policy_names = ["FOO", "KR5M"]
    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
    instance._get_policies_to_delete()
    assert instance._policies_to_delete == ["KR5M"]


def test_image_policy_delete_00033(image_policy_delete) -> None:
    """
    Classes and Methods
    - ImagePolicyDelete
        - commit()
        - fail_json

    Setup
    -   ImagePolicyDelete().policy_names is not set

    Test
    -   fail_json is called because policy_names is None
    """
    with does_not_raise():
        instance = image_policy_delete

    match = (
        "ImagePolicyDelete.commit: policy_names must be set prior to calling commit."
    )
    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()


def test_image_policy_delete_00034(monkeypatch, image_policy_delete) -> None:
    """
    Classes and Methods
    - ImagePolicyDelete
        - policy_names setter
        - commit()

    Setup
    -   ImagePolicyDelete().policy_names is set to an empty list

    Test
    -   ImagePolicyDelete().commit returns without doing anything
    -   fail_json is not called
    -   instance.changed is False
    """
    with does_not_raise():
        instance = image_policy_delete
        instance.policy_names = []
        instance.commit()
    assert instance.changed is False


def test_image_policy_delete_00035(monkeypatch, image_policy_delete) -> None:
    """
    Classes and Methods
    - ImagePolicyDelete
        - policy_names setter
        - commit()

    Setup
    -   ImagePolicyDelete().policy_names is set to an empty list

    Test
    -   ImagePolicyDelete().commit returns without doing anything
    -   fail_json is not called
    -   instance.changed is False
    """
    with does_not_raise():
        instance = image_policy_delete
        instance.policy_names = []
        instance.commit()
    assert instance.changed is False


def test_image_policy_delete_00036(monkeypatch, image_policy_delete) -> None:
    """
    Classes and Methods
    - ImagePolicyDelete
        - policy_names setter
        - _get_policies_to_delete()
        - commit()

    Setup
    -   ImagePolicies().all_policies is mocked to indicate that no policies exist on the controller.
    -   ImagePolicyDelete().policy_names is set a policy_name that is not on the controller.

    Test
    -   ImagePolicyDelete()._get_policies_to_delete return an empty list
    -   ImagePolicyDelete().commit returns without doing anything
    -   instance.changed is set to False
    -   fail_json is not called
    """
    key = "test_image_policy_delete_00036a"
    with does_not_raise():
        instance = image_policy_delete
        instance.policy_names = ["FOO"]
    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
    with does_not_raise():
        instance.commit()
    assert len(instance._policies_to_delete) == 0
    assert instance.changed is False


def test_image_policy_delete_00037(monkeypatch, image_policy_delete) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon:
        - __init__()
        - _handle_response()
    - ImagePolicyDelete
        - _get_policies_to_delete()
        - policy_names setter
        - commit()

    Setup
    -   ImagePolicies().all_policies is mocked to indicate policy (KR5M) exists on the controller.
    -   ImagePolicyDelete().policy_names is set to contain one payload (KR5M).
    -   dcnm_send is mocked to return a successful (200) response.

    Test
    -   fail_json is not called
    -   commit calls _get_policies_to_delete which returns a list containing policy_name (KR5M)
    -   commit calls the mocked dcnm_send, which populates instance.response_current
        with a successful (200) response
    -   instance.result_current is populated by instance._handle_response()
    -   instance.result_current contains expected values
    -   instance.changed is set to True
    -   instance.diff contains expected values
    """
    key = "test_image_policy_delete_00037a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.image_policy.delete.dcnm_send"

    def mock_dcnm_send(*args, **kwargs):
        return responses_image_policy_delete(key)

    with does_not_raise():
        instance = image_policy_delete
        instance.policy_names = ["KR5M"]

    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
        instance.commit()
    assert instance._policies_to_delete == ["KR5M"]
    assert instance.result_current == results_image_policy_delete(key)
    assert instance.changed is True
    assert instance.failed is False
    assert instance.diff == [{"policyNames": ["KR5M"], "action": "delete"}]


def test_image_policy_delete_00038(monkeypatch, image_policy_delete) -> None:
    """
    Classes and Methods
    - ImagePolicyCommon:
        - __init__()
        - _handle_response()
    - ImagePolicyDelete
        - _get_policies_to_delete()
        - policy_names setter
        - commit()

    Setup
    -   ImagePolicies().all_policies is mocked to indicate policy (KR5M) exists on the controller.
    -   ImagePolicyDelete().policy_names is set to contain one payload (KR5M).
    -   dcnm_send is mocked to return a failure (500) response.

    Test
    -   fail_json is called
    -   commit calls _get_policies_to_delete which returns a list containing policy_name (KR5M)
    -   commit calls the mocked dcnm_send, which populates instance.response_current
        with a failure (500) response
    -   instance.result_current is populated by instance._handle_response()
    -   instance.result_current contains expected values
    -   instance.changed is set to False
    -   instance.diff is an empty list
    """
    key = "test_image_policy_delete_00038a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.image_policy.delete.dcnm_send"

    def mock_dcnm_send(*args, **kwargs):
        return responses_image_policy_delete(key)

    with does_not_raise():
        instance = image_policy_delete
        instance.policy_names = ["KR5M"]

    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    match = r"ImagePolicyDelete.commit: Bad response during policies delete\. policy_names \['KR5M'\]\."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()
    assert instance._policies_to_delete == ["KR5M"]
    assert instance.result_current == results_image_policy_delete(key)
    assert instance.changed is False
    assert instance.failed is True
    assert instance.diff == []
