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

import copy
import inspect

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.response_handler import \
    ResponseHandler
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_file import \
    Sender
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_image_policy.utils import (
    MockAnsibleModule, does_not_raise, image_policy_replace_bulk_fixture,
    params, payloads_image_policy_replace_bulk, responses_ep_policies,
    responses_ep_policy_edit, responses_image_policy_replace_bulk,
    rest_send_result_current, results_image_policy_replace_bulk)


def test_image_policy_replace_bulk_00000(image_policy_replace_bulk) -> None:
    """
    ### Classes and Methods
    - ImagePolicyReplaceBulk
        - __init__

    ### Summary
    Verify that __init__() sets class attributes to the expected values.

    ### Test
    - Class attributes initialized to expected values
    - Exceptions are not raised.
    """
    with does_not_raise():
        instance = image_policy_replace_bulk
    assert instance.class_name == "ImagePolicyReplaceBulk"
    assert instance.action == "replace"
    assert instance.params.get("state") == "replaced"
    assert instance.params.get("check_mode") is False
    assert instance.endpoint.class_name == "EpPolicyEdit"
    assert instance.endpoint.verb == "POST"
    assert instance._mandatory_payload_keys == {
        "nxosVersion",
        "policyName",
        "policyType",
    }
    assert instance.payloads is None
    assert instance._payloads_to_commit == []
    assert instance._image_policies.class_name == "ImagePolicies"
    assert instance._image_policies.results.class_name == "Results"


def test_image_policy_replace_bulk_00020(image_policy_replace_bulk) -> None:
    """
    ### Classes and Methods
    - ImagePolicyReplaceBulk
        - __init__
        - payloads setter

    ### Summary
    Verify that the payloads setter sets the payloads attribute
    to the expected value.

    ### Test
    - payloads is set to expected value
    - Exceptions are not raised.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.payloads = payloads_image_policy_replace_bulk(key)
    assert instance.payloads == payloads_image_policy_replace_bulk(key)


def test_image_policy_replace_bulk_00021(image_policy_replace_bulk) -> None:
    """
    ### Classes and Methods
    - ImagePolicyReplaceBulk
        - __init__
        - payload setter

    ### Summary
    Verify that the payloads setter raises ``TypeError`` when payloads is not
    a list of dict.

    ### Test
    -   ``TypeError`` is raised because payloads is not a list.
    -  ``instance.payloads`` is not modified.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = image_policy_replace_bulk

    match = r"ImagePolicyReplaceBulk.payloads:\s+"
    match += r"payloads must be a list of dict\. got dict for value.*"
    with pytest.raises(TypeError, match=match):
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
    ### Classes and Methods
    - ImagePolicyReplaceBulk
        - __init__
        - payloads setter

    ### Summary
    Verify that ``payloads.setter`` raises ``ValueError when a payload is
    missing a mandatory key

    ### Test
    -   ``ValueError`` is raised because payload is missing a mandatory key.
    -   ``instance.payload`` is not modified.
    """
    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.results = Results()
    with pytest.raises(ValueError, match=match):
        instance.payloads = payloads_image_policy_replace_bulk(key)
    assert instance.payloads is None


def test_image_policy_replace_bulk_00023(image_policy_replace_bulk) -> None:
    """
    ### Classes and Methods
    - ImagePolicyReplaceBulk
        - __init__
        - payload setter

    ### Summary
    Verify that ``payloads.setter` raises ``TypeError`` when payloads is
    a list but contains an element that is not a dict.

    ### Test
    -   ``TypeError`` is raised because payloads is a list, but contains a
        non-dict element.
    -   ``instance.payloads`` is not modified.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.results = Results()

    match = r"ImagePolicyReplaceBulk\.verify_payload:\s+"
    match += r"payload must be a dict\. Got type str, value\s+"
    match += r"IM_A_STRING_BUT_SHOULD_BE_A_DICT"
    with pytest.raises(TypeError, match=match):
        instance.payloads = payloads_image_policy_replace_bulk(key)
    assert instance.payloads is None


def test_image_policy_replace_bulk_00030(image_policy_replace_bulk) -> None:
    """
    ### Classes and Methods
    - ImagePolicyReplaceBulk
        - __init__()
        - build_payloads_to_commit()
        - _verify_image_policy_ref_count()
        - payloads setter

    ### Summary
    Verify build_payloads_to_commit() behavior when a request contains one
    image policy that exists on the controller and the caller has requested to
    replace it.  The replaced image policy contains a different policyDescr.

    ### Setup
    -   EpPolicies() endpoint response is mocked to indicate that two image
        policies (KR5M, NR3F) exist on the controller.
    -   ImagePolicyReplaceBulk().payloads is set to contain one payload (KR5M)
        that is present on the controller.

    ### Test
    -   payloads_to_commit will contain payload for KR5M since it exists on
        the controller and the caller has requested to update it.
    -   Since this is a full payload, MergeDicts doesn't apply any defaults
        to it.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)
        yield responses_ep_policy_edit(key)
    gen_responses = ResponseGenerator(responses())

    def payloads():
        yield payloads_image_policy_replace_bulk(key)
    gen_payloads = ResponseGenerator(payloads())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.results = Results()
        instance.rest_send = rest_send
        instance.payloads = gen_payloads.next
        instance.commit()

    assert instance._payloads_to_commit == payloads_image_policy_replace_bulk(key)
    assert instance._payloads_to_commit[0]["policyName"] == "KR5M"
    assert instance._payloads_to_commit[0]["policyDescr"] == "KR5M Replaced"


def test_image_policy_replace_bulk_00031(image_policy_replace_bulk) -> None:
    """
    ### Classes and Methods
    - ImagePolicyReplaceBulk
        - __init__()
        - build_payloads_to_commit()
        - _verify_image_policy_ref_count()
        - payloads setter

    ### Summary
    Verify behavior when a request is sent to replace an image policy
    that does not exist on the controller

    ### Expected behavior
    ``instance.build_payloads_to_commit()`` does not add a payload
    to the ``payloads_to_commit`` list if the associated policy
    does not exist on the controller.

    ### Setup
    -   EpPolicies() endpoint response is mocked to indicate that two image
        policies (KR5M, NR3F) exist on the controller.
    -   ImagePolicyReplaceBulk().payloads is set to contain one payload containing
        an image policy (FOO) that is not present on the controller.

    ### Test
    -   Exceptions are not raised.
    -   _payloads_to_commit is an empty list since policy FOO does not
        exist on the controller.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)
    gen_responses = ResponseGenerator(responses())

    def payloads():
        yield payloads_image_policy_replace_bulk(key)
    gen_payloads = ResponseGenerator(payloads())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.results = Results()
        instance.rest_send = rest_send
        instance.payloads = gen_payloads.next
        instance.commit()

    assert instance._payloads_to_commit == []
    assert len(instance.results.failed) == 0
    assert len(instance.results.changed) == 0


def test_image_policy_replace_bulk_00032(image_policy_replace_bulk) -> None:
    """
    ### Classes and Methods
    - ImagePolicyReplaceBulk
        - __init__()
        - build_payloads_to_commit()
        - _verify_image_policy_ref_count()
        - payloads setter

    ### Summary
    Verify build_payloads_to_commit() behavior when a request contains one
    image policy that does not exist on the controller and one image policy
    that exists on the controller.

    ### Setup
    -   EpPolicies() endpoint response is mocked to indicate that two image
        policies (KR5M, NR3F) exist on the controller.
    -   ImagePolicyReplaceBulk().payloads is set to contain one payload containing
        an image policy (FOO) that does not exist on the controller and one payload
        containing an image policy (KR5M) that exists on the controller.

    ### Test
    -   _payloads_to_commit contains one payload.
    -   The policyName for this payload is "KR5M", which is the image policy
        that exists on the controller.
    -   The policyDesc for this payload is "KR5M replaced", which is the new
        image policy description sent to the controller for the replaced state
        update.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)
        yield responses_ep_policy_edit(key)
    gen_responses = ResponseGenerator(responses())

    def payloads():
        yield payloads_image_policy_replace_bulk(key)
    gen_payloads = ResponseGenerator(payloads())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.results = Results()
        instance.rest_send = rest_send
        instance.payloads = gen_payloads.next
        instance.commit()

    assert len(instance._payloads_to_commit) == 1
    assert instance._payloads_to_commit[0]["policyName"] == "KR5M"
    assert instance._payloads_to_commit[0]["policyDescr"] == "KR5M replaced"


def test_image_policy_replace_bulk_00033(image_policy_replace_bulk) -> None:
    """
    ### Classes and Methods
    - ImagePolicyReplaceBulk
        - commit()

    ### Summary
    Verify that commit() raises ``ValueError`` when payloads is not set.

    ### Setup
    -   ImagePolicyReplaceBulk().payloads is not set.

    ### Test
    -   ``ValueError`` is raised because payloads is None.
    """
    with does_not_raise():
        instance = image_policy_replace_bulk

    match = r"ImagePolicyReplaceBulk\.commit:\s+"
    match += r"payloads must be set prior to calling commit\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_image_policy_replace_bulk_00034(image_policy_replace_bulk) -> None:
    """
    ### Classes and Methods
    - ImagePolicyReplaceBulk
        - payloads setter
        - commit()
        - build_payloads_to_commit()

    ### Summary
    Verify that commit() returns without doing anything when payloads
    is set to a policy that does not exist on the controller.

    ### Setup
    ### Setup
    -   EpPolicies() endpoint response is mocked to indicate that no
        policies exist on the controller.
    -   ImagePolicyReplaceBulk().payload is set to a policy (FOO) that does not
        exist on the controller

    ### Test
    -   ImagePolicyReplaceBulk().commit returns without doing anything.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)
    gen_responses = ResponseGenerator(responses())

    def payloads():
        yield payloads_image_policy_replace_bulk(key)
    gen_payloads = ResponseGenerator(payloads())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.results = Results()
        instance.rest_send = rest_send
        instance.payloads = gen_payloads.next
        instance.commit()
    assert instance._payloads_to_commit == []
    assert len(instance.results.changed) == 0
    assert len(instance.results.failed) == 0


def test_image_policy_replace_bulk_00035(image_policy_replace_bulk) -> None:
    """
    ### Classes and Methods
    - ImagePolicyReplaceBulk
        - build_payloads_to_commit()
        - send_payloads()
        - payloads.setter
        - commit()

    ### Summary
    Verify ImagePolicyUpdateBulk.commit() happy path.  Controller returns
    a 200 response to an image policy update request.

    ### Setup
    -   EpPolicies() endpoint response is mocked to indicate that two policies
        (KR5M, NR3F) exist on the controller.
    -   ImagePolicyReplaceBulk().payloads is set to contain payloads for KR5M and NR3F
        in which policyDescr is different from the existing policyDescr.
    -   EpPolicyEdit() endpoint response is mocked to return a successful
        (200) response.

    ### Test
    -   commit calls build_payloads_to_commit which returns two payloads.
    -   commit calls ``send_payloads``, which calls
        ``results.register_task_result()`` to update the results.
    -  results.* are set to the expected values
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)
        yield responses_ep_policy_edit(key)
        yield responses_ep_policy_edit(key)
    gen_responses = ResponseGenerator(responses())

    def payloads():
        yield payloads_image_policy_replace_bulk(key)
    gen_payloads = ResponseGenerator(payloads())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.results = Results()
        instance.rest_send = rest_send
        instance.payloads = gen_payloads.next
        instance.commit()

    response_current = responses_image_policy_replace_bulk(key)
    response_current["sequence_number"] = 1

    result_current = rest_send_result_current(key)
    result_current["sequence_number"] = 1

    # Add the sequence_number to the diff for comparison, since we add
    # it in the results.register_task_result() method.
    diff_compare = copy.deepcopy(payloads_image_policy_replace_bulk(key))
    sequence_number = 1
    for item in diff_compare:
        item.update({"sequence_number": sequence_number})
        sequence_number += 1

    assert instance.results.action == "replace"
    assert instance.rest_send.result_current == rest_send_result_current(key)
    assert len(instance.results.diff) == 2
    assert len(instance.results.result) == 2
    assert len(instance.results.response) == 2
    assert instance.results.result[0].get("sequence_number") == 1
    assert instance.results.result[1].get("sequence_number") == 2
    assert instance.results.diff[0] == diff_compare[0]
    assert instance.results.diff[1] == diff_compare[1]
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


def test_image_policy_replace_bulk_00036(image_policy_replace_bulk) -> None:
    """
    ### Classes and Methods
    - ImagePolicyReplaceBulk
        - build_payloads_to_commit()
        - send_payloads()
        - payloads setter
        - commit()

    ### Summary
    Verify ImagePolicyReplaceBulk.commit() sad path.  Controller returns
    a 500 response to an image policy update request.

    ### Setup
    -   EpPolicies() endpoint response is mocked to indicate that one policy
        (KR5M) exists on the controller.
    -   ImagePolicyReplaceBulk().payloads is set to contain the payload for
        image policy KR5M with policyDescr changed.
    -   EpPolicyEdit() endpoint response is mocked to return a failed
        (500) response.

    ### Test
    -   commit calls build_payloads_to_commit which returns one payload
    -   commit calls send_payloads, which populates response_ok, result_ok,
        diff_ok, response_nok, result_nok, and diff_nok based on the payload
        returned from build_payloads_to_commit and the failure response
    -  response_ok, result_ok, and diff_ok are set to empty lists
    -  response_nok, result_nok, and diff_nok are set to expected values
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)
        yield responses_ep_policy_edit(key)
    gen_responses = ResponseGenerator(responses())

    def payloads():
        yield payloads_image_policy_replace_bulk(key)
    gen_payloads = ResponseGenerator(payloads())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    rest_send.timeout = 1
    rest_send.unit_test = True

    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.results = Results()
        instance.rest_send = rest_send
        instance.payloads = gen_payloads.next
        instance.commit()

    response_current = responses_image_policy_replace_bulk(key)
    response_current["sequence_number"] = 1

    result_current = rest_send_result_current(key)
    result_current["sequence_number"] = 1

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


def test_image_policy_replace_bulk_00037(image_policy_replace_bulk) -> None:
    """
    ### Classes and Methods
    - ImagePolicyCreateCommon
        - _process_responses()
    - ImagePolicyCreateBulk
        - __init__()

    ### Summary
    Verify behavior when the controller returns a 200 response to an image policy
    replace request, followed by a 500 response to a subsequent image policy replace
    request.

    ### Setup
    -   instance.payloads is set to contain two payloads.

    ### Test
    - Both successful and bad responses are recorded with separate sequence_numbers.
    - instance.results.failed will be a set() containing both True and False
    - instance.results.changed will be a set() containing both True and False
    - instance.results.response contains two responses
    - instance.results.result contains two results
    - instance.results.diff contains two diffs
    """
    key_policies = "test_image_policy_replace_bulk_00037a"
    key_ok = "test_image_policy_replace_bulk_00037a"
    key_nok = "test_image_policy_replace_bulk_00037b"
    key_payloads = "test_image_policy_replace_bulk_00037a"

    def responses():
        yield responses_ep_policies(key_policies)
        yield responses_ep_policy_edit(key_ok)
        yield responses_ep_policy_edit(key_nok)
    gen_responses = ResponseGenerator(responses())

    def payloads():
        yield payloads_image_policy_replace_bulk(key_payloads)
    gen_payloads = ResponseGenerator(payloads())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    rest_send.timeout = 1
    rest_send.unit_test = True

    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.results = Results()
        instance.rest_send = rest_send
        instance.payloads = gen_payloads.next
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
    ### Classes and Methods
    - ImagePolicyReplaceBulk
        - __init__
        - default_policy

    ### Summary
    Verify that instance.default_policy raises ``TypeError`` when
    ``policy_name`` is not a string.

    ### Test
    - ``TypeError``is raised because ``policy_name`` is a list.
    """
    with does_not_raise():
        instance = image_policy_replace_bulk
        instance.results = Results()

    match = r"ImagePolicyReplaceBulk\.default_policy:\s+"
    match += r"policy_name must be a string\.\s+"
    match += r"Got type list for value \[\]"
    with pytest.raises(TypeError, match=match):
        instance.default_policy([])
