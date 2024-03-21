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
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_image_policy.utils import (
    GenerateResponses, MockImagePolicies, does_not_raise,
    image_policy_replace_bulk_fixture, payloads_image_policy_replace_bulk,
    responses_image_policy_replace_bulk, rest_send_result_current,
    results_image_policy_replace_bulk)


def test_image_policy_replace_bulk_00010(image_policy_replace_bulk) -> None:
    """
    Classes and Methods
    - ImagePolicyReplaceBulk
        - __init__

    Summary
    Verify that __init__() sets class attributes to the expected values.

    Test
    - Class attributes initialized to expected values
    - fail_json is not called
    """
    with does_not_raise():
        instance = image_policy_replace_bulk
    assert instance.class_name == "ImagePolicyReplaceBulk"
    assert instance.action == "replace"
    assert instance.state == "replaced"
    assert instance.check_mode is False
    assert isinstance(instance.endpoints, ApiEndpoints)
    assert instance.path == ApiEndpoints().policy_edit["path"]
    assert instance.verb == ApiEndpoints().policy_edit["verb"]
    assert instance._mandatory_payload_keys == {
        "nxosVersion",
        "policyName",
        "policyType",
    }
    assert instance.payloads is None
    assert instance._payloads_to_commit == []
    assert isinstance(instance._image_policies, ImagePolicies)


def test_image_policy_replace_bulk_00020(image_policy_replace_bulk) -> None:
    """
    Classes and Methods
    - ImagePolicyReplaceBulk
        - __init__
        - payloads setter

    Summary
    Verify that the payloads setter sets the payloads attribute
    to the expected value.

    Test
    - payloads is set to expected value
    - fail_json is not called
    """
    key = "test_image_policy_replace_bulk_00020a"

    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.payloads = payloads_image_policy_replace_bulk(key)
    assert instance.payloads == payloads_image_policy_replace_bulk(key)


def test_image_policy_replace_bulk_00021(image_policy_replace_bulk) -> None:
    """
    Classes and Methods
    - ImagePolicyReplaceBulk
        - __init__
        - payload setter

    Summary
    Verify that the payloads setter calls fail_json when payloads is not a list of dict

    Test
    - fail_json is called because payloads is not a list
    - instance.payloads is not modified, hence it retains its initial value of None
    """
    key = "test_image_policy_replace_bulk_00021a"
    match = "ImagePolicyReplaceBulk.payloads: "
    match += "payloads must be a list of dict. got dict for value"

    with does_not_raise():
        instance = image_policy_replace_bulk
    with pytest.raises(AnsibleFailJson, match=match):
        instance.payloads = payloads_image_policy_replace_bulk(key)
    assert instance.payloads is None


@pytest.mark.parametrize(
    "key, match",
    [
        ("test_image_policy_replace_bulk_00022a", "nxosVersion"),
        ("test_image_policy_replace_bulk_00022b", "policyName"),
        ("test_image_policy_replace_bulk_00022c", "policyType"),
    ],
)
def test_image_policy_replace_bulk_00022(image_policy_replace_bulk, key, match) -> None:
    """
    Classes and Methods
    - ImagePolicyReplaceBulk
        - __init__
        - payloads setter

    Test
    - fail_json is called because a payload in the payloads list is missing a mandatory key
    - instance.payloads is not modified, hence it retains its initial value of None
    """
    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.results = Results()
    with pytest.raises(AnsibleFailJson, match=match):
        instance.payloads = payloads_image_policy_replace_bulk(key)
    assert instance.payloads is None


def test_image_policy_replace_bulk_00023(image_policy_replace_bulk) -> None:
    """
    Classes and Methods
    - ImagePolicyReplaceBulk
        - __init__
        - payload setter

    Summary
    Verify that the payloads setter calls fail_json when payloads is a list
    but contains an element that is not a dict.

    Test
    - fail_json is called because payloads is a list, but contains a non-dict element
    - instance.payloads is not modified, hence it retains its initial value of None
    """
    key = "test_image_policy_replace_bulk_00023a"
    match = "ImagePolicyReplaceBulk._verify_payload: "
    match += "payload must be a dict. Got type str, value "
    match += "IM_A_STRING_BUT_SHOULD_BE_A_DICT"

    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.results = Results()
    with pytest.raises(AnsibleFailJson, match=match):
        instance.payloads = payloads_image_policy_replace_bulk(key)
    assert instance.payloads is None


def test_image_policy_replace_bulk_00030(
    monkeypatch, image_policy_replace_bulk
) -> None:
    """
    Classes and Methods
    - ImagePolicyReplaceBulk
        - __init__()
        - _build_payloads_to_commit()
        - _verify_image_policy_ref_count()
        - payloads setter

    Summary
    Verify _build_payloads_to_commit() behavior when a request contains one
    image policy that exists on the controller and the caller has requested to
    replace it.  The replaced image policy contains a different policyDescr.

    Setup
    -   ImagePolicies().all_policies, called from instance._build_payloads_to_commit(),
        is mocked to indicate that two image policies (KR5M, NR3F) exist on the
        controller.
    -   ImagePolicyReplaceBulk().payloads is set to contain one payload (KR5M)
        that is present in all_policies.

    Test
    -   payloads_to_commit will contain payload for KR5M since it exists on the controller
        and the caller has requested to replace it.
    -   Since this is a full payload, MergeDicts doesn't apply any defaults to it.
    """
    key = "test_image_policy_replace_bulk_00030a"

    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.results = Results()
        instance.payloads = payloads_image_policy_replace_bulk(key)
        monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
        instance._build_payloads_to_commit()
    assert instance._payloads_to_commit == payloads_image_policy_replace_bulk(key)
    assert instance._payloads_to_commit[0]["policyName"] == "KR5M"
    assert instance._payloads_to_commit[0]["policyDescr"] == "KR5M Replaced"


def test_image_policy_replace_bulk_00031(
    monkeypatch, image_policy_replace_bulk
) -> None:
    """
    Classes and Methods
    - ImagePolicyReplaceBulk
        - __init__()
        - _build_payloads_to_commit()
        - _verify_image_policy_ref_count()
        - payloads setter

    Summary
    Verify behavior when a request to replace an image policy is sent for
    an image policy that does not exist on the controller

    Setup
    -   ImagePolicies().all_policies, called from instance._build_payloads_to_commit(),
        is mocked to indicate that two image policies (KR5M, NR3F) exist on the
        controller.
    -   ImagePolicyReplaceBulk().payloads is set to contain one payload containing
        an image policy (FOO) that is not present on the controller.

    Test
    -   fail_json is not called
    -   _payloads_to_commit be an empty list since policy FOO does not
        exist on the controller.
    """
    key = "test_image_policy_replace_bulk_00031a"

    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.results = Results()
        instance.payloads = payloads_image_policy_replace_bulk(key)
        monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
        instance._build_payloads_to_commit()
    assert instance._payloads_to_commit == []


def test_image_policy_replace_bulk_00032(
    monkeypatch, image_policy_replace_bulk
) -> None:
    """
    Classes and Methods
    - ImagePolicyReplaceBulk
        - __init__()
        - _build_payloads_to_commit()
        - _verify_image_policy_ref_count()
        - payloads setter

    Summary
    Verify _build_payloads_to_commit() behavior when a request contains one
    image policy that does not exist on the controller and one image policy
    that exists on the controller.

    Setup
    -   ImagePolicies().all_policies, called from instance._build_payloads_to_commit(),
        is mocked to indicate that two image policies (KR5M, NR3F) exist on the
        controller.
    -   ImagePolicyReplaceBulk().payloads is set to contain one payload containing
        an image policy (FOO) that does not exist on the controller and one payload
        containing an image policy (KR5M) that exists on the controller.

    Test
    -   _payloads_to_commit will contain one payload
    -   The policyName for this payload will be "KR5M", which is the image policy that
        exists on the controller
    """
    key = "test_image_policy_replace_bulk_00032a"

    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.results = Results()
        instance.payloads = payloads_image_policy_replace_bulk(key)
        monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
        instance._build_payloads_to_commit()
    assert len(instance._payloads_to_commit) == 1
    assert instance._payloads_to_commit[0]["policyName"] == "KR5M"


def test_image_policy_replace_bulk_00033(image_policy_replace_bulk) -> None:
    """
    Classes and Methods
    - ImagePolicyReplaceBulk
        - commit()
        - _build_payloads_to_commit
        - fail_json

    Summary
    Verify that _build_payloads_to_commit() calls fail_json when
    payloads is not set.

    Setup
    -   ImagePolicyReplaceBulk().payloads is not set

    Test
    -   fail_json is called because payloads is None
    """
    with does_not_raise():
        instance = image_policy_replace_bulk

    match = (
        "ImagePolicyReplaceBulk._build_payloads_to_commit: payloads must be "
        "set prior to calling commit."
    )
    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()


def test_image_policy_replace_bulk_00034(
    monkeypatch, image_policy_replace_bulk
) -> None:
    """
    Classes and Methods
    - ImagePolicyReplaceBulk
        - payloads setter
        - commit()
        - _build_payloads_to_commit()

    Summary
    Verify that commit() returns without doing anything when payloads
    is set to an empty list.

    Setup
    -   ImagePolicyReplaceBulk().payloads is set to an empty list

    Test
    -   ImagePolicyReplaceBulk().commit returns without doing anything
    """
    key = "test_image_policy_replace_bulk_00034a"

    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.results = Results()
        instance.payloads = []

    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))

    with does_not_raise():
        instance.commit()


def test_image_policy_replace_bulk_00035(
    monkeypatch, image_policy_replace_bulk
) -> None:
    """
    Classes and Methods
    - ImagePolicyReplaceBulk
        - _build_payloads_to_commit()
        - _send_payloads()
        - payloads setter
        - commit()

    Summary
    Verify behavior when a request is made to replace two image policies
    that exist on the controller.

    Setup
    -   ImagePolicies().all_policies, called from instance._build_payloads_to_commit(),
        is mocked to indicate that two policies (KR5M, NR3F) exist on the controller.
    -   ImagePolicyReplaceBulk().payloads is set to contain payloads for KR5M and NR3F
        in which policyDescr is different from the existing policyDescr.
    -   dcnm_send is mocked to return a successful (200) response.

    Test
    -   commit calls _build_payloads_to_commit which returns two payloads
    -   commit calls _send_payloads, which calls results.register_task_result()
        to update the results.
    -  results.* are set to the expected values
    """
    key = "test_image_policy_replace_bulk_00035a"

    def mock_dcnm_send(*args, **kwargs):
        return responses_image_policy_replace_bulk(key)

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.results = Results()

    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
        instance.payloads = payloads_image_policy_replace_bulk(key)
        instance.commit()

    payload_0 = payloads_image_policy_replace_bulk(key)[0]
    # sequence_number is added by the Results class
    payload_0["sequence_number"] = 1

    payload_1 = payloads_image_policy_replace_bulk(key)[1]
    payload_1["sequence_number"] = 2

    assert instance.results.action == "replace"
    assert instance.rest_send.result_current == rest_send_result_current(key)
    assert len(instance.results.diff) == 2
    assert len(instance.results.result) == 2
    assert len(instance.results.response) == 2
    assert instance.results.result[0].get("sequence_number") == 1
    assert instance.results.result[1].get("sequence_number") == 2
    assert instance.results.diff[0] == payload_0
    assert instance.results.diff[1] == payload_1
    assert instance.results.diff[0].get("policyDescr") == "KR5M replaced"
    assert instance.results.diff[1].get("policyDescr") == "NR3F replaced"
    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False not in instance.results.changed
    assert True in instance.results.changed
    assert len(instance.results.metadata) == 2
    assert instance.results.metadata[0]["action"] == "replace"
    assert instance.results.metadata[0]["state"] == "replaced"
    assert instance.results.metadata[0]["sequence_number"] == 1
    assert instance.results.metadata[1]["action"] == "replace"
    assert instance.results.metadata[1]["state"] == "replaced"
    assert instance.results.metadata[1]["sequence_number"] == 2


def test_image_policy_replace_bulk_00036(
    monkeypatch, image_policy_replace_bulk
) -> None:
    """
    Classes and Methods
    - ImagePolicyReplaceBulk
        - _build_payloads_to_commit()
        - _send_payloads()
        - payloads setter
        - commit()

    Summary
    Verify behavior when the controller returns a 500 response to an
    image policy replace request

    Setup
    -   ImagePolicies().all_policies, is mocked to indicate that one policy
        (KR5M) exists on the controller.
    -   ImagePolicyReplaceBulk().payloads is set to contain the payload for
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
    key = "test_image_policy_replace_bulk_00036a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def mock_dcnm_send(*args, **kwargs):
        return responses_image_policy_replace_bulk(key)

    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.rest_send.unit_test = True
        instance.results = Results()
        instance.payloads = payloads_image_policy_replace_bulk(key)

    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies(key))
    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
        instance.commit()

    response_current = responses_image_policy_replace_bulk(key)
    response_current["sequence_number"] = 1
    assert instance.results.response_current == response_current
    assert instance.results.diff_current == {"sequence_number": 1}
    assert True in instance.results.failed
    assert False not in instance.results.failed
    assert True not in instance.results.changed
    assert False in instance.results.changed
    assert len(instance.results.metadata) == 1
    assert len(instance.results.diff) == 1
    assert instance.results.diff[0] == {"sequence_number": 1}
    assert instance.results.metadata[0]["action"] == "replace"
    assert instance.results.metadata[0]["state"] == "replaced"
    assert instance.results.metadata[0]["sequence_number"] == 1


def test_image_policy_replace_bulk_00037(
    monkeypatch, image_policy_replace_bulk
) -> None:
    """
    Classes and Methods
    - ImagePolicyCreateCommon
        - _process_responses()
    - ImagePolicyCreateBulk
        - __init__()

    Summary
    Verify behavior when the controller returns a 200 response to an image policy
    replace request, followed by a 500 response to a subsequent image policy replace
    request.

    Setup
    -   instance.payloads is set to contain two payloads

    Test
    - Both successful and bad responses are recorded with separate sequence_numbers.
    - instance.results.failed will be a set() containing both True and False
    - instance.results.changed will be a set() containing both True and False
    - instance.results.response contains two responses
    - instance.results.result contains two results
    - instance.results.diff contains two diffs
    """
    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    key_policies = "test_image_policy_replace_bulk_00037a"
    key_ok = "test_image_policy_replace_bulk_00037b"
    key_nok = "test_image_policy_replace_bulk_00037c"
    key_payloads = "test_image_policy_replace_bulk_00037d"

    def responses():
        yield responses_image_policy_replace_bulk(key_policies)
        yield responses_image_policy_replace_bulk(key_ok)
        yield responses_image_policy_replace_bulk(key_nok)

    gen = GenerateResponses(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.rest_send.unit_test = True
        instance.results = Results()
        instance.payloads = payloads_image_policy_replace_bulk(key_payloads)

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
        instance.commit()

    assert len(instance.results.diff) == 2
    assert len(instance.results.result) == 2
    assert len(instance.results.response) == 2
    assert len(instance.results.metadata) == 2
    assert instance.results.response[0]["RETURN_CODE"] == 200
    assert instance.results.response[1]["RETURN_CODE"] == 500
    assert False in instance.results.changed
    assert True in instance.results.changed
    assert False in instance.results.failed
    assert True in instance.results.failed


def test_image_policy_replace_bulk_00040(image_policy_replace_bulk) -> None:
    """
    Classes and Methods
    - ImagePolicyReplaceBulk
        - __init__
        - _default_policy

    Summary
    Verify that instance._default_policy setter calls fail_json when
    passed a policy_name that is not a string.

    Test
    - fail_json is called because policy_name is a list
    """
    match = "ImagePolicyReplaceBulk._default_policy: "
    match += "policy_name must be a string. "
    match += r"Got type list for value \[\]"

    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.results = Results()
    with pytest.raises(AnsibleFailJson, match=match):
        instance._default_policy([])
