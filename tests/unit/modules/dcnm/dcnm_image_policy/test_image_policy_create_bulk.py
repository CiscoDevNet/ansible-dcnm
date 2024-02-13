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
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_image_policy.utils import (
    MockImagePolicies, does_not_raise, image_policies_all_policies,
    image_policy_create_bulk_fixture, payloads_image_policy_create_bulk,
    responses_image_policy_create_bulk, results_image_policy_create_bulk)


def test_image_policy_create_bulk_00010(image_policy_create_bulk) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateCommon
        - __init__()
    - ImagePolicyCreateBulk
        - __init__()

    Test
    - Class attributes are initialized to expected values
    - fail_json is not called
    """
    with does_not_raise():
        instance = image_policy_create_bulk
    assert instance.class_name == "ImagePolicyCreateBulk"
    assert instance.action == "create"
    assert isinstance(instance.endpoints, ApiEndpoints)
    assert instance.path == ApiEndpoints().policy_create["path"]
    assert instance.verb == ApiEndpoints().policy_create["verb"]
    assert instance._mandatory_payload_keys == {
        "nxosVersion",
        "policyName",
        "policyType",
    }
    assert instance.payloads is None


def test_image_policy_create_bulk_00020(image_policy_create_bulk) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateCommon
        - __init__()
        - payloads setter
    - ImagePolicyCreateBulk
        - __init__()

    Test
    - payloads is set to expected value
    - fail_json is not called
    """
    key = "test_image_policy_create_bulk_00020a"

    with does_not_raise():
        instance = image_policy_create_bulk
        instance.payloads = payloads_image_policy_create_bulk(key)
    assert instance.payloads == payloads_image_policy_create_bulk(key)


def test_image_policy_create_bulk_00021(image_policy_create_bulk) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateCommon
        - __init__()
        - payloads setter
    - ImagePolicyCreateBulk
        - __init__()

    Test
    - fail_json is called because payloads is not a list of dict
    - instance.payloads is not modified, hence it retains its initial value of None
    """
    key = "test_image_policy_create_bulk_00021a"
    match = "ImagePolicyCreateBulk.payloads: "
    match += "payloads must be a list of dict. got dict for value"

    with does_not_raise():
        instance = image_policy_create_bulk
    with pytest.raises(AnsibleFailJson, match=match):
        instance.payloads = payloads_image_policy_create_bulk(key)
    assert instance.payloads is None


@pytest.mark.parametrize(
    "key, match",
    [
        ("test_image_policy_create_bulk_00022a", "nxosVersion"),
        ("test_image_policy_create_bulk_00022b", "policyName"),
        ("test_image_policy_create_bulk_00022c", "policyType"),
    ],
)
def test_image_policy_create_bulk_00022(image_policy_create_bulk, key, match) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateCommon
        - __init__()
        - payloads setter
    - ImagePolicyCreateBulk
        - __init__()

    Test
    - fail_json is called because a payload in the payloads list is missing a mandatory key
    - instance.payloads is not modified, hence it retains its initial value of None
    """
    with does_not_raise():
        instance = image_policy_create_bulk
    with pytest.raises(AnsibleFailJson, match=match):
        instance.payloads = payloads_image_policy_create_bulk(key)
    assert instance.payloads is None


def test_image_policy_create_bulk_00030(monkeypatch, image_policy_create_bulk) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateCommon
        - __init__()
        - payloads setter
        - _build_payloads_to_commit()
    - ImagePolicyCreateBulk
        - __init__()

    Setup
    -   ImagePolicies().all_policies, called from instance._build_payloads_to_commit(),
        is mocked to indicate that two image policies (KR5M, NR3F) exist on the
        controller.
    -   ImagePolicyCreateCommon().payloads is set to contain one payload (KR5M)
        that is present in all_policies.

    Test
    -   payloads_to_commit will an empty list because all payloads in
        instance.payloads exist on the controller.
    """
    key = "test_image_policy_create_bulk_00030a"

    instance = image_policy_create_bulk
    instance.payloads = payloads_image_policy_create_bulk(key)
    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
    instance._build_payloads_to_commit()
    assert instance._payloads_to_commit == []


def test_image_policy_create_bulk_00031(monkeypatch, image_policy_create_bulk) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateCommon
        - __init__()
        - payloads setter
        - _build_payloads_to_commit()
    - ImagePolicyCreateBulk
        - __init__()

    Setup
    -   ImagePolicies().all_policies, called from instance._build_payloads_to_commit(),
        is mocked to indicate that two image policies (KR5M, NR3F) exist on the
        controller.
    -   ImagePolicyCreateCommon().payloads is set to contain one payload containing
        an image policy (FOO) that is not present in all_policies.

    Test
    -   _payloads_to_commit will equal instance.payloads since none of the
        image policies in instance.payloads exist on the controller.
    """
    key = "test_image_policy_create_bulk_00031a"

    instance = image_policy_create_bulk
    instance.payloads = payloads_image_policy_create_bulk(key)
    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
    instance._build_payloads_to_commit()
    assert instance._payloads_to_commit == payloads_image_policy_create_bulk(key)


def test_image_policy_create_bulk_00032(monkeypatch, image_policy_create_bulk) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateCommon
        - payloads setter
        - _build_payloads_to_commit()
    - ImagePolicyCreateBulk
        - __init__()

    Setup
    -   ImagePolicies().all_policies, called from instance._build_payloads_to_commit(),
        is mocked to indicate that two image policies (KR5M, NR3F) exist on the
        controller.
    -   ImagePolicyCreateCommon().payloads is set to contain one payload containing
        an image policy (FOO) that is not present in all_policies and one payload
        containing an image policy (KR5M) that does exist on the controller.

    Test
    -   _payloads_to_commit will contain one payload
    -   The policyName for this payload will be "FOO", which is the image policy that
        does not exist on the controller
    """
    key = "test_image_policy_create_bulk_00032a"

    instance = image_policy_create_bulk
    instance.payloads = payloads_image_policy_create_bulk(key)
    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
    instance._build_payloads_to_commit()
    assert len(instance._payloads_to_commit) == 1
    assert instance._payloads_to_commit[0]["policyName"] == "FOO"


def test_image_policy_create_bulk_00033(image_policy_create_bulk) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateBulk
        - commit()
        - fail_json

    Setup
    -   ImagePolicyCreateCommon().payloads is not set

    Test
    -   fail_json is called because payloads is None
    """
    with does_not_raise():
        instance = image_policy_create_bulk

    match = (
        "ImagePolicyCreateBulk.commit: payloads must be set prior to calling commit."
    )
    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()


def test_image_policy_create_bulk_00034(monkeypatch, image_policy_create_bulk) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateCommon
        - payloads setter
    - ImagePolicyCreateBulk
        - commit()

    Setup
    -   ImagePolicyCreateCommon().payloads is set to an empty list

    Test
    -   ImagePolicyCreateBulk().commit returns without doing anything
    """
    key = "test_image_policy_create_bulk_00034a"

    with does_not_raise():
        instance = image_policy_create_bulk
        instance.payloads = []

    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))

    with does_not_raise():
        instance.commit()


def test_image_policy_create_bulk_00035(monkeypatch, image_policy_create_bulk) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateCommon
        - _build_payloads_to_commit()
        - _send_payloads()
    - ImagePolicyCreateBulk
        - payloads setter
        - commit()

    Setup
    -   ImagePolicies().all_policies, called from instance._build_payloads_to_commit(),
        is mocked to indicate that no policies exist on the controller.
    -   ImagePolicyCreateCommon().payloads is set to contain one payload that
        contains an image policy (FOO) which does not exist on the controller.
    -   dcnm_send is mocked to return a successful (200) response.

    Test
    -   commit calls _build_payloads_to_commit which returns one payload
    -   commit calls _send_payloads, which populates response_ok, result_ok,
        diff_ok, response_nok, result_nok, and diff_nok based on the payload
        returned from _build_payloads_to_commit
    -  response_ok, result_ok, and diff_ok are set to the expected values
    -  response_nok, result_nok, and diff_nok are set to empty lists
    """
    key = "test_image_policy_create_bulk_00035a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.image_policy.create.dcnm_send"

    def mock_dcnm_send(*args, **kwargs):
        return responses_image_policy_create_bulk(key)

    with does_not_raise():
        instance = image_policy_create_bulk
        instance.payloads = payloads_image_policy_create_bulk(key)

    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
        instance.payloads = payloads_image_policy_create_bulk(key)
        instance.commit()

    assert instance.response_current == responses_image_policy_create_bulk(key)
    assert instance.response_ok[0]["RETURN_CODE"] == 200
    assert instance.result_ok[0]["changed"] is True
    assert instance.result_ok[0]["success"] is True
    assert instance.diff_ok[0]["agnostic"] is False
    assert instance.diff_ok[0]["policyName"] == "FOO"
    assert instance.response_nok == []
    assert instance.result_nok == []
    assert instance.diff_nok == []


def test_image_policy_create_bulk_00036(monkeypatch, image_policy_create_bulk) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateCommon
        - _build_payloads_to_commit()
        - _send_payloads()
    - ImagePolicyCreateBulk
        - commit()

    Setup
    -   ImagePolicies().all_policies, called from instance._build_payloads_to_commit(),
        is mocked to indicate that no policies exist on the controller.
    -   ImagePolicyCreateBulk().payloads is set to contain one payload that
        contains an image policy (FOO) which does not exist on the controller.
    -   dcnm_send is mocked to return a failure (500) response.

    Test
    -   commit calls _build_payloads_to_commit which returns one payload
    -   commit calls _send_payloads, which populates response_ok, result_ok,
        diff_ok, response_nok, result_nok, and diff_nok based on the payload
        returned from _build_payloads_to_commit and the failure response
    -  response_ok, result_ok, and diff_ok are set to empty lists
    -  response_nok, result_nok, and diff_nok are set to expected values
    """
    key = "test_image_policy_create_bulk_00036a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.image_policy.create.dcnm_send"

    def mock_dcnm_send(*args, **kwargs):
        return responses_image_policy_create_bulk(key)

    with does_not_raise():
        instance = image_policy_create_bulk
        instance.payloads = payloads_image_policy_create_bulk(key)

    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with pytest.raises(AnsibleFailJson):
        instance.payloads = payloads_image_policy_create_bulk(key)
        instance.commit()

    assert instance.response_current == responses_image_policy_create_bulk(key)
    assert instance.response_ok == []
    assert instance.result_ok == []
    assert instance.diff_ok == []
    assert instance.response_nok[0]["RETURN_CODE"] == 500
    assert instance.result_nok[0]["changed"] == False
    assert instance.result_nok[0]["success"] == False
    assert instance.diff_nok[0]["agnostic"] is False
    assert instance.diff_nok[0]["policyName"] == "FOO"


def test_image_policy_create_bulk_00037(monkeypatch, image_policy_create_bulk) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateCommon
        - _process_responses()
    - ImagePolicyCreateBulk
        - __init__()

    Setup
    -   result_ok is set to contain one result
    -   result_nok is set to contain one result
    -   response_ok is set to contain one response
    -   response_nok is set to contain one response
    -   diff_ok is set to contain one diff
    -   diff_nok is set to contain one diff
    -   _payloads_to_commit is set to contain two payloads

    Test
    -   instance._process_responses() will call fail_json with the expected message
    -   instance.result will be set to the successful result
    -   instance.response will be set to the successful response
    -   instance.diff will be set to the successful diff (with action key added)
    -   instance.changed will be set to True
    -   instanced.failed will be set to True
    """
    key_ok = "test_image_policy_create_bulk_00037a"
    key_nok = "test_image_policy_create_bulk_00037b"
    key_payloads = "test_image_policy_create_bulk_00037c"

    with does_not_raise():
        instance = image_policy_create_bulk

    monkeypatch.setattr(instance, "diff_ok", payloads_image_policy_create_bulk(key_ok))
    monkeypatch.setattr(
        instance, "diff_nok", payloads_image_policy_create_bulk(key_nok)
    )
    monkeypatch.setattr(
        instance, "_payloads_to_commit", payloads_image_policy_create_bulk(key_payloads)
    )
    monkeypatch.setattr(
        instance, "response_ok", responses_image_policy_create_bulk(key_ok)
    )
    monkeypatch.setattr(
        instance, "response_nok", responses_image_policy_create_bulk(key_nok)
    )
    monkeypatch.setattr(instance, "result_ok", results_image_policy_create_bulk(key_ok))
    monkeypatch.setattr(
        instance, "result_nok", results_image_policy_create_bulk(key_nok)
    )

    match = r"ImagePolicyCreateBulk._process_responses: Bad response\(s\) during policy create\."
    with pytest.raises(AnsibleFailJson, match=match):
        instance._process_responses()

    assert len(instance.diff) == 1  # only the succcessful payload
    # We need to add an "action" key to success payload to form the expected diff
    diff = payloads_image_policy_create_bulk(key_ok)
    diff[0]["action"] = "create"
    assert instance.diff[0] == diff[0]
    assert instance.result == results_image_policy_create_bulk(key_ok)
    assert instance.response == responses_image_policy_create_bulk(key_ok)
    assert instance.changed is True
    assert instance.failed is True
