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

from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_image_policy.utils import (
    MockImagePolicies, does_not_raise, image_policy_update_fixture,
    payloads_image_policy_update, responses_image_policy_update,
    results_image_policy_update)


def test_image_policy_update_00010(image_policy_update) -> None:
    """
    Classes and Methods
    - ImagePolicyUpdate
        - __init__

    Summary
    Verify that __init__() sets class attributes to the expected values.

    Test
    - Class attributes initialized to expected values
    - fail_json is not called
    """
    with does_not_raise():
        instance = image_policy_update
    assert instance.class_name == "ImagePolicyUpdate"

    assert isinstance(instance.endpoints, ApiEndpoints)

    assert instance.action == "update"
    assert instance.path == ApiEndpoints().policy_edit["path"]
    assert instance.verb == ApiEndpoints().policy_edit["verb"]
    assert instance._mandatory_payload_keys == {
        "nxosVersion",
        "policyName",
        "policyType",
    }
    assert instance.payload is None
    assert instance._payloads_to_commit == []
    assert instance.response_ok == []
    assert instance.response_nok == []
    assert instance.result_ok == []
    assert instance.result_nok == []
    assert instance.diff_ok == []
    assert instance.diff_nok == []


def test_image_policy_update_00020(image_policy_update) -> None:
    """
    Classes and Methods
    - ImagePolicyUpdate
        - __init__
        - payload setter

    Summary
    Verify that the payload setter sets the payload attribute
    to the expected value.

    Test
    - payload is set to expected value
    - fail_json is not called
    """
    key = "test_image_policy_update_00020a"

    with does_not_raise():
        instance = image_policy_update
        instance.payload = payloads_image_policy_update(key)
    assert instance.payload == payloads_image_policy_update(key)


def test_image_policy_update_00021(image_policy_update) -> None:
    """
    Classes and Methods
    - ImagePolicyUpdate
        - __init__
        - payload setter

    Summary
    Verify that the payload setter calls fail_json when payload is not a dict

    Setup
    - payload is set to a list

    Test
    - fail_json is called because payload is not a dict
    - instance.payload is not modified, hence it retains its initial value of None
    """
    key = "test_image_policy_update_00021a"
    match = "ImagePolicyUpdate._verify_payload: "
    match += "payload must be a dict. Got type list, value"

    with does_not_raise():
        instance = image_policy_update
    with pytest.raises(AnsibleFailJson, match=match):
        instance.payload = payloads_image_policy_update(key)
    assert instance.payload is None


@pytest.mark.parametrize(
    "key, match",
    [
        ("test_image_policy_update_00022a", "nxosVersion"),
        ("test_image_policy_update_00022b", "policyName"),
        ("test_image_policy_update_00022c", "policyType"),
    ],
)
def test_image_policy_update_00022(image_policy_update, key, match) -> None:
    """
    Classes and Methods
    - ImagePolicyUpdate
        - __init__
        - payload setter

    Test
    - fail_json is called because payload is missing a mandatory key
    - instance.payload is not modified, hence it retains its initial value of None
    """
    with does_not_raise():
        instance = image_policy_update
    with pytest.raises(AnsibleFailJson, match=match):
        instance.payload = payloads_image_policy_update(key)
    assert instance.payload is None


def test_image_policy_update_00030(monkeypatch, image_policy_update) -> None:
    """
    Classes and Methods
    - ImagePolicyUpdate
        - __init__()
        - _build_payloads_to_commit()
        - _verify_image_policy_ref_count()
        - payload setter

    Summary
    Verify _build_payloads_to_commit() behavior when a request contains one
    image policy that exists on the controller and the caller has requested to
    update it.  The update consists of changing the policyDescr.

    Setup
    -   ImagePolicies().all_policies, is mocked to indicate that two image
        policies (KR5M, NR3F) exist on the controller.
    -   ImagePolicyUpdate().payload is set to contain a payload (KR5M)
        that is present on the controller.

    Test
    -   payloads_to_commit will contain the payload for KR5M since it exists
        on the controller and the caller has requested to update it.
    -   The policyName for this payload will be "KR5M"
    -   The policyDescr for this payload will be "KR5M updated"
    -   fail_json is not called
    """
    key = "test_image_policy_update_00030a"

    instance = image_policy_update
    instance.payload = payloads_image_policy_update(key)
    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
    with does_not_raise():
        instance._build_payloads_to_commit()
    assert instance._payloads_to_commit == [payloads_image_policy_update(key)]
    assert instance._payloads_to_commit[0]["policyName"] == "KR5M"
    assert instance._payloads_to_commit[0]["policyDescr"] == "KR5M updated"


def test_image_policy_update_00031(monkeypatch, image_policy_update) -> None:
    """
    Classes and Methods
    - ImagePolicyUpdate
        - __init__()
        - _build_payloads_to_commit()
        - _verify_image_policy_ref_count()
        - payload setter

    Summary
    Simulate a request to update a policy that does not exist on the controller

    Setup
    -   ImagePolicies().all_policies, is mocked to indicate that two image policies
        (KR5M, NR3F) exist on the controller.
    -   ImagePolicyUpdate().payload is set to contain a payload containing
        an image policy (FOO) that does not exist on the controller.

    Test
    -   fail_json is not called
    -   _payloads_to_commit will be an empty list since policy FOO does not
        exist on the controller.
    """
    key = "test_image_policy_update_00031a"

    with does_not_raise():
        instance = image_policy_update
        instance.payload = payloads_image_policy_update(key)
        monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
        instance._build_payloads_to_commit()
    assert instance._payloads_to_commit == []


def test_image_policy_update_00033(image_policy_update) -> None:
    """
    Classes and Methods
    - ImagePolicyUpdate
        - commit()
        - _build_payloads_to_commit
        - fail_json

    Summary
    Verify that _build_payloads_to_commit() calls fail_json when
    payload is not set.

    Setup
    -   ImagePolicyUpdate().payload is not set

    Test
    -   fail_json is called because payload is None
    """
    with does_not_raise():
        instance = image_policy_update

    match = "ImagePolicyUpdate.commit: payload must be " "set prior to calling commit."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()


def test_image_policy_update_00035(monkeypatch, image_policy_update) -> None:
    """
    Classes and Methods
    - ImagePolicyUpdate
        - _build_payloads_to_commit()
        - _send_payloads()
        - payload setter
        - commit()

    Summary
    Simulate a successful commit for a payload and verify that instance
    attributes are set to the expected values.

    Setup
    -   ImagePolicies().all_policies, is mocked to indicate that two policies
        (KR5M, NR3F) exist on the controller.
    -   ImagePolicyUpdate().payload is set to contain a payload for KR5M
        in which policyDescr is different from the existing policyDescr.
    -   dcnm_send is mocked to return a successful (200) response.

    Test
    -   commit calls _build_payloads_to_commit which returns one payload
    -   commit calls _send_payloads, which populates response_ok, result_ok,
        diff_ok, response_nok, result_nok, and diff_nok based on the payload
        returned from _build_payloads_to_commit
    -  length of instance._payloads_to_commit is 1
    -  response_ok, result_ok, and diff_ok are set to the expected values
    -  response_nok, result_nok, and diff_nok are set to empty lists
    """
    key = "test_image_policy_update_00035a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.image_policy.update.dcnm_send"

    def mock_dcnm_send(*args, **kwargs):
        return responses_image_policy_update(key)

    with does_not_raise():
        instance = image_policy_update
        instance.payload = payloads_image_policy_update(key)

    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
        instance.payload = payloads_image_policy_update(key)
        instance.commit()

    assert instance.response_current == responses_image_policy_update(key)
    assert len(instance._payloads_to_commit) == 1
    assert instance.response_ok[0]["RETURN_CODE"] == 200
    assert instance.result_ok[0]["changed"] is True
    assert instance.result_ok[0]["success"] is True
    assert instance.diff_ok[0]["agnostic"] is False
    assert instance.diff_ok[0]["policyName"] == "KR5M"
    assert instance.diff_ok[0]["policyDescr"] == "KR5M updated"
    assert instance.response_nok == []
    assert instance.result_nok == []
    assert instance.diff_nok == []


def test_image_policy_update_00036(monkeypatch, image_policy_update) -> None:
    """
    Classes and Methods
    - ImagePolicyUpdate
        - _build_payloads_to_commit()
        - _send_payloads()
        - payload setter
        - commit()

    Summary
    Simulate a 500 response from the controller during policy update.
    In this case, the following holds true:
    - The bad response is recorded in response_nok, result_nok, and diff_nok.
    - response_ok, result_ok, and diff_ok are set to empty lists
    - instance.failed is set to True
    - instance.changed is set to False
    - instance.response is set to the bad response
    - instance.result is set to the bad result
    - instance.diff is set to the bad diff
    - fail_json is called with the expected message

    Setup
    -   ImagePolicies().all_policies, is mocked to indicate that one policy
        (KR5M) exists on the controller.
    -   ImagePolicyUpdate().payloads is set to contain the payload for
        image policy KR5M with policyDescr changed.
    -   dcnm_send is mocked to return a failure (500) response.

    Test
    -   commit calls _build_payloads_to_commit which returns one payload
    -   commit calls _send_payloads, which populates response_ok, result_ok,
        diff_ok, response_nok, result_nok, and diff_nok based on the payload
        returned from _build_payloads_to_commit and the failure response
    -  response_ok, result_ok, and diff_ok are set to empty lists
    -  response_nok, result_nok, and diff_nok are set to expected values
    """
    key = "test_image_policy_update_00036a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.image_policy.update.dcnm_send"

    def mock_dcnm_send(*args, **kwargs):
        return responses_image_policy_update(key)

    with does_not_raise():
        instance = image_policy_update
        instance.payload = payloads_image_policy_update(key)

    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with pytest.raises(AnsibleFailJson):
        instance.payload = payloads_image_policy_update(key)
        instance.commit()

    assert instance.response_current == responses_image_policy_update(key)
    assert len(instance._payloads_to_commit) == 1
    assert instance.response_ok == []
    assert instance.result_ok == []
    assert instance.diff_ok == []
    assert instance.response_nok[0]["RETURN_CODE"] == 500
    assert instance.result_nok[0]["changed"] is False
    assert instance.result_nok[0]["success"] is False
    assert instance.diff_nok[0]["agnostic"] is False
    assert instance.diff_nok[0]["policyName"] == "KR5M"
    assert instance.diff_nok[0]["policyDescr"] == "KR5M updated"


def test_image_policy_update_00040(image_policy_update) -> None:
    """
    Classes and Methods
    - ImagePolicyUpdate
        - __init__
        - _default_policy

    Summary
    Verify that instance._default_policy setter calls fail_json when
    passed a policy_name that is not a string.

    Test
    - fail_json is called because policy_name is a list
    """
    match = "ImagePolicyUpdate._default_policy: "
    match += "policy_name must be a string. "
    match += r"Got type list for value \[\]"

    with does_not_raise():
        instance = image_policy_update
    with pytest.raises(AnsibleFailJson, match=match):
        instance._default_policy([])


def test_image_policy_update_00050(monkeypatch, image_policy_update) -> None:
    """
    Classes and Methods
    - ImagePolicyUpdate
        - _build_payloads_to_commit()
        - _send_payloads()
        - payload setter
        - commit()

    Summary
    Simulate an attempt to update an image policy for which ref_count is != 0
    on the controller, i.e. switches are attached to the image policy.

    Setup
    -   ImagePolicies().all_policies, is mocked to indicate that one policy
        (KR5M) exists on the controller with ref_count == 2.
    -   ImagePolicyUpdate().payloads is set to contain the payload for
        image policy KR5M with policyDescr changed.

    Test
    -   commit calls _build_payloads_to_commit
    -   _build_payloads_to_commit calls _verify_image_policy_ref_count
    -   _verify_image_policy_ref_count calls fail_json with the expected message
    """
    key = "test_image_policy_update_00050a"

    with does_not_raise():
        instance = image_policy_update
        instance.payload = payloads_image_policy_update(key)

    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))

    match = "ImagePolicyUpdate._verify_image_policy_ref_count: "
    match += "One or more policies have devices attached."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()
