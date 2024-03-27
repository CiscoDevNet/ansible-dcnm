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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_image_policy.utils import (
    MockImagePolicies, does_not_raise, image_policy_update_fixture,
    payloads_image_policy_update, responses_image_policy_update,
    rest_send_result_current, results_image_policy_update)


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
    assert instance.action == "update"
    assert instance.state == "merged"
    assert instance.check_mode is False
    assert isinstance(instance.endpoints, ApiEndpoints)
    assert instance.path == ApiEndpoints().policy_edit["path"]
    assert instance.verb == ApiEndpoints().policy_edit["verb"]
    assert instance._mandatory_payload_keys == {
        "nxosVersion",
        "policyName",
        "policyType",
    }
    assert instance.payload is None
    assert instance._payloads_to_commit == []


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
        instance.results = Results()
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

    Summary
    Verify that the payload setter calls fail_json when a payload is missing
    a mandatory key

    Test
    - fail_json is called because payload is missing a mandatory key
    - instance.payload is not modified, hence it retains its initial value of None
    """
    with does_not_raise():
        instance = image_policy_update
        instance.results = Results()
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

    with does_not_raise():
        instance = image_policy_update
        instance.results = Results()
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
    Verify that instance._build_payloads_to_commit() does not add a payload
    to the payloads_to_commit list when a request is made to update an
    image policy that does not exist on the controller.

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
        instance.results = Results()
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
        instance.results = Results()

    match = "ImagePolicyUpdate.commit: payload must be set prior to calling commit."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()


def test_image_policy_update_00034(monkeypatch, image_policy_update) -> None:
    """
    Classes and Methods
    - ImagePolicyUpdateCommon
        - _build_payloads_to_commit()
    - ImagePolicyUpdate
        - payload setter
        - commit()

    Summary
    Verify that commit() returns without doing anything when payloads
    is set to a policy that does not exist on the controller.

    Setup
    -   ImagePolicies().all_policies, is mocked to indicate that no policies
        exist on the controller.
    -   ImagePolicyUpdate().payload is set to a policy (FOO) that does not
        exist on the controller

    Test
    -   ImagePolicyUpdate().commit returns without doing anything
    -   ImagePolicyUpdate()._payloads_to_commit is an empty list
    -   ImagePolicyUpdate().results.changed is empty
    -   ImagePolicyUpdate().results.failed is empty
    """
    key = "test_image_policy_update_00034a"

    with does_not_raise():
        instance = image_policy_update
        instance.results = Results()
        instance.payload = payloads_image_policy_update(key)

    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))

    with does_not_raise():
        instance.commit()
    assert instance._payloads_to_commit == []
    assert len(instance.results.changed) == 0
    assert len(instance.results.failed) == 0


def test_image_policy_update_00035(monkeypatch, image_policy_update) -> None:
    """
    Classes and Methods
    - ImagePolicyUpdate
        - _build_payloads_to_commit()
        - _send_payloads()
        - payload setter
        - commit()

    Summary
    Verify that ImagePolicyUpdate.commit() behaves as expected when the
    controller responds to an image policy update request with a 200 response.

    Setup
    -   ImagePolicies().all_policies, is mocked to indicate that two policies
        (KR5M, NR3F) exist on the controller.
    -   ImagePolicyUpdate().payload is set to contain a payload for KR5M
        in which policyDescr is different from the existing policyDescr.
    -   dcnm_send is mocked to return a successful (200) response.

    Test
    Test
    -   commit calls _build_payloads_to_commit which returns one payload.
    -   commit calls _send_payloads, which calls rest_send, which populates
        diff_current with the payload due to result_current indicating
        success.
    -   results.result_current is set to the expected value
    -   results.diff_current is set to the expected value
    -   results.response_current is set to the expected value
    -   results.action is set to "update"
    """
    key = "test_image_policy_update_00035a"

    def mock_dcnm_send(*args, **kwargs):
        return responses_image_policy_update(key)

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
        instance = image_policy_update
        instance.results = Results()

    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))

    with does_not_raise():
        instance.payload = payloads_image_policy_update(key)
        instance.commit()

    response_current = responses_image_policy_update(key)
    response_current["sequence_number"] = 1

    result_current = rest_send_result_current(key)
    result_current["sequence_number"] = 1

    payload = payloads_image_policy_update(key)
    payload["sequence_number"] = 1

    assert instance.results.action == "update"
    assert instance.rest_send.result_current == rest_send_result_current(key)
    assert instance.results.result_current == result_current
    assert instance.results.response_current == response_current
    assert instance.results.diff_current == payload
    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False not in instance.results.changed
    assert True in instance.results.changed
    assert len(instance.results.metadata) == 1
    assert instance.results.metadata[0]["action"] == "update"
    assert instance.results.metadata[0]["state"] == "merged"
    assert instance.results.metadata[0]["sequence_number"] == 1


def test_image_policy_update_00036(monkeypatch, image_policy_update) -> None:
    """
    Classes and Methods
    - ImagePolicyUpdate
        - _build_payloads_to_commit()
        - _send_payloads()
        - payload setter
        - commit()

    Summary
    Verify that ImagePolicyUpdate.commit() behaves as expected when the
    controller responds to an image policy update request with a 500 response.

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

    def mock_dcnm_send(*args, **kwargs):
        return responses_image_policy_update(key)

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
        instance = image_policy_update
        instance.rest_send.unit_test = True
        instance.results = Results()

    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))

    with does_not_raise():
        instance.payload = payloads_image_policy_update(key)
        instance.commit()

    response_current = responses_image_policy_update(key)
    response_current["sequence_number"] = 1

    result_current = rest_send_result_current(key)
    result_current["sequence_number"] = 1

    assert instance.results.action == "update"
    assert instance.rest_send.result_current == rest_send_result_current(key)
    assert instance.results.result_current == result_current
    assert instance.results.response_current == response_current
    assert instance.results.diff_current == {"sequence_number": 1}
    assert True in instance.results.failed
    assert False not in instance.results.failed
    assert True not in instance.results.changed
    assert False in instance.results.changed
    assert len(instance.results.metadata) == 1
    assert instance.results.metadata[0]["action"] == "update"
    assert instance.results.metadata[0]["state"] == "merged"
    assert instance.results.metadata[0]["sequence_number"] == 1


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
        instance.results = Results()
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
    Verify that fail_json is called when an image policy update request is made
    for an image policy which has a ref_count != 0 on the controller, i.e.
    switches are attached to the image policy.

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
        instance.results = Results()
        instance.payload = payloads_image_policy_update(key)

    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))

    match = "ImagePolicyUpdate._verify_image_policy_ref_count: "
    match += "One or more policies have devices attached."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()
