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
    MockImagePolicies, does_not_raise, image_policy_create_fixture,
    payloads_image_policy_create, responses_image_policy_create,
    rest_send_result_current)


def test_image_policy_create_00010(image_policy_create) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateCommon
        - __init__
    - ImagePolicyCreate
        - __init__

    Summary
    Verify that __init__() sets class attributes to the expected values.

    Test
    - Class attributes initialized to expected values
    - fail_json is not called
    """
    with does_not_raise():
        instance = image_policy_create
    assert instance.class_name == "ImagePolicyCreate"
    assert instance.action == "create"
    assert instance.state == "merged"
    assert instance.check_mode is False
    assert isinstance(instance.endpoints, ApiEndpoints)
    assert instance.path == ApiEndpoints().policy_create["path"]
    assert instance.verb == ApiEndpoints().policy_create["verb"]
    assert instance._mandatory_payload_keys == {
        "nxosVersion",
        "policyName",
        "policyType",
    }
    assert instance.payload is None
    assert instance._payloads_to_commit == []


def test_image_policy_create_00020(image_policy_create) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateCommon
        - __init__
    - ImagePolicyCreate
        - __init__
        - payload setter

    Summary
    Verify that the payloads setter sets the payloads attribute
    to the expected value.

    Test
    - payload is set to expected value
    - fail_json is not called
    """
    key = "test_image_policy_create_00020a"

    with does_not_raise():
        instance = image_policy_create
        instance.payload = payloads_image_policy_create(key)
    assert instance.payload == payloads_image_policy_create(key)


def test_image_policy_create_00021(image_policy_create) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateCommon
        - __init__
    - ImagePolicyCreate
        - __init__
        - payload setter

    Summary
    Verify that the payload setter calls fail_json when payload is not a dict

    Setup
    - payload is set to a list

    Test
    - fail_json is called because payload is not a dict
    """
    key = "test_image_policy_create_00021a"
    match = "ImagePolicyCreate._verify_payload: "
    match += "payload must be a dict. Got type list"

    with does_not_raise():
        instance = image_policy_create
        instance.results = Results()
    with pytest.raises(AnsibleFailJson, match=match):
        instance.payload = payloads_image_policy_create(key)
    assert instance.payload is None


@pytest.mark.parametrize(
    "key, match",
    [
        ("test_image_policy_create_00022a", "nxosVersion"),
        ("test_image_policy_create_00022b", "policyName"),
        ("test_image_policy_create_00022c", "policyType"),
    ],
)
def test_image_policy_create_00022(image_policy_create, key, match) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateCommon
        - __init__
    - ImagePolicyCreate
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
        instance = image_policy_create
        instance.results = Results()
    with pytest.raises(AnsibleFailJson, match=match):
        instance.payload = payloads_image_policy_create(key)
    assert instance.payload is None


def test_image_policy_create_00030(monkeypatch, image_policy_create) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateCommon
        - __init__()
        - _build_payloads_to_commit()
    - ImagePolicyCreate
        - __init__()
        - payload setter

    Summary
    Verify behavior when the user sends an image create payload for an
    image policy that already exists on the controller.

    Setup
    -   ImagePolicies().all_policies, called from instance._build_payloads_to_commit(),
        is mocked to indicate that two image policies (KR5M, NR3F) exist on the
        controller.
    -   ImagePolicyCreate().payload is set to contain one payload (KR5M)
        that is present in all_policies.

    Test
    -   payloads_to_commit will an empty list because the payload in
        instance.payload exists on the controller.
    """
    key = "test_image_policy_create_00030a"

    with does_not_raise():
        instance = image_policy_create
        instance.results = Results()
        instance.payload = payloads_image_policy_create(key)
        monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
        instance._build_payloads_to_commit()
    assert instance._payloads_to_commit == []


def test_image_policy_create_00031(monkeypatch, image_policy_create) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateCommon
        - __init__()
        - _build_payloads_to_commit()
    - ImagePolicyCreate
        - __init__()
        - payload setter

    Summary
    Verify that instance._build_payloads_to_commit() adds a payload to the
    payloads_to_commit list when a request is made to create an image policy
    that does not exist on the controller.

    Setup
    -   ImagePolicies().all_policies, called from instance._build_payloads_to_commit(),
        is mocked to indicate that two image policies (KR5M, NR3F) exist on the
        controller.
    -   ImagePolicyCreate().payload is set to contain one payload containing
        an image policy (FOO) that is not present in all_policies.

    Test
    -   _payloads_to_commit will equal list(instance.payload) since none of the
        image policies in instance.payloads exist on the controller.
    """
    key = "test_image_policy_create_00031a"

    with does_not_raise():
        instance = image_policy_create
        instance.results = Results()
        instance.payload = payloads_image_policy_create(key)
        monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
        instance._build_payloads_to_commit()
    assert len(instance._payloads_to_commit) == 1
    assert instance._payloads_to_commit == [payloads_image_policy_create(key)]


def test_image_policy_create_00033(image_policy_create) -> None:
    """
    Classes and Methods
    - ImagePolicyCreate
        - commit()
        - fail_json

    Summary
    Verify that ImagePolicyCreate.commit() calls fail_json when
    payload is None.

    Setup
    -   ImagePolicyCreate().payload is not set

    Test
    -   fail_json is called because payload is None
    """
    with does_not_raise():
        instance = image_policy_create
        instance.results = Results()

    match = "ImagePolicyCreate.commit: payload must be set prior to calling commit."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()


def test_image_policy_create_00034(monkeypatch, image_policy_create) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateCommon
        - __init__()
        - _build_payloads_to_commit()
    - ImagePolicyCreate
        - __init__()
        - payload setter
        - commit()

    Summary
    Verify that ImagePolicyCreate.commit() works as expected when the image policy
    already exists on the controller.  This is similar to test_image_policy_create_00030
    but tests that the commit method returns when _payloads_to_commit is empty.

    Setup
    -   ImagePolicies().all_policies, called from instance._build_payloads_to_commit(),
        is mocked to indicate that two image policies (KR5M, NR3F) exist on the
        controller.
    -   ImagePolicyCreate().payload is set to contain one payload (KR5M)
        that is present in all_policies.

    Test
    -   payloads_to_commit will an empty list because all payloads in
        instance.payloads exist on the controller.
    -   commit will return without calling _send_payloads
    -   fail_json is not called
    """
    key = "test_image_policy_create_00034a"

    with does_not_raise():
        instance = image_policy_create
        instance.results = Results()
        instance.payload = payloads_image_policy_create(key)
        monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
        instance.commit()
    assert instance._payloads_to_commit == []


def test_image_policy_create_00035(monkeypatch, image_policy_create) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateCommon
        - _build_payloads_to_commit()
        - _send_payloads()
    - ImagePolicyCreate
        - payload setter
        - commit()

    Summary
    Verify that ImagePolicyCreate.commit() behaves as expected when the
    controller responds to an image policy create request with a 200 response.

    Setup
    -   ImagePolicies().all_policies, called from instance._build_payloads_to_commit(),
        is mocked to indicate that no policies exist on the controller.
    -   ImagePolicyCreate().payload is set to contain one payload that
        contains an image policy (FOO) which does not exist on the controller.
    -   dcnm_send is mocked to return a successful (200) response.

    Test
    -   commit calls _build_payloads_to_commit which returns one payload.
    -   commit calls _send_payloads, which calls rest_send, which populates
        diff_current with the payload due to result_current indicating
        success.
    -   results.result_current is set to the expected value
    -   results.diff_current is set to the expected value
    -   results.response_current is set to the expected value
    -   results.action is set to "create"
    """
    key = "test_image_policy_create_00035a"

    def mock_dcnm_send(*args, **kwargs):
        return responses_image_policy_create(key)

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
        instance = image_policy_create
        instance.results = Results()

    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))

    with does_not_raise():
        instance.payload = payloads_image_policy_create(key)
        instance.commit()

    response_current = responses_image_policy_create(key)
    response_current["sequence_number"] = 1

    result_current = rest_send_result_current(key)
    result_current["sequence_number"] = 1

    payload = payloads_image_policy_create(key)
    payload["sequence_number"] = 1

    assert instance.results.action == "create"
    assert instance.rest_send.result_current == rest_send_result_current(key)
    assert instance.results.result_current == result_current
    assert instance.results.response_current == response_current
    assert instance.results.diff_current == payload
    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False not in instance.results.changed
    assert True in instance.results.changed
    assert len(instance.results.metadata) == 1
    assert instance.results.metadata[0]["action"] == "create"
    assert instance.results.metadata[0]["state"] == "merged"
    assert instance.results.metadata[0]["sequence_number"] == 1
