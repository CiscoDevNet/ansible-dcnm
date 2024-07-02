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
    MockAnsibleModule, does_not_raise, image_policy_update_fixture, params,
    payloads_image_policy_update, responses_ep_policies,
    responses_ep_policy_edit, responses_image_policy_update,
    rest_send_result_current)


def test_image_policy_update_00000(image_policy_update) -> None:
    """
    Classes and Methods
    - ImagePolicyUpdate
        - __init__

    Summary
    Verify that __init__() sets class attributes to the expected values.

    Test
    - Class attributes initialized to expected values
    - Exceptions are not raised.
    """
    with does_not_raise():
        instance = image_policy_update
    assert instance.class_name == "ImagePolicyUpdate"
    assert instance.action == "update"
    assert instance.params.get("state") == "merged"
    assert instance.params.get("check_mode") is False
    assert instance.endpoint.class_name == "EpPolicyEdit"
    assert instance.endpoint.verb == "POST"
    assert instance._mandatory_payload_keys == {
        "nxosVersion",
        "policyName",
        "policyType",
    }
    assert instance.payload is None
    assert instance._payloads_to_commit == []
    assert instance._image_policies.class_name == "ImagePolicies"
    assert instance._image_policies.results.class_name == "Results"


def test_image_policy_update_00020(image_policy_update) -> None:
    """
    ### Classes and Methods
    - ImagePolicyUpdate
        - __init__
        - payload setter

    ### Summary
    Verify that the payload setter sets the payload attribute
    to the expected value.

    ### Test
    - payload is set to expected value
    - Exceptions are not raised.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = image_policy_update
        instance.payload = payloads_image_policy_update(key)
    assert instance.payload == payloads_image_policy_update(key)


def test_image_policy_update_00021(image_policy_update) -> None:
    """
    ### Classes and Methods
    - ImagePolicyUpdate
        - __init__
        - payload setter

    ### Summary
    Verify that the payloads setter raises TypeError when payloads is not
    a dict.

    ### Setup
    - payload is set to a list

    ### Test
    -   ``TypeError`` is raised because payload is not a dict.
    -   ``instance.payload`` is not modified.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = image_policy_update
        instance.results = Results()

    match = r"ImagePolicyUpdate\.verify_payload:\s+"
    match += r"payload must be a dict\. Got type list, value"

    with pytest.raises(TypeError, match=match):
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
    ### Classes and Methods
    - ImagePolicyUpdate
        - __init__
        - payload setter

    ### Summary
    Verify that ``payload.setter`` raises ``ValueError when a payload is
    missing a mandatory key

    ### Test
    -   ``ValueError`` is raised because payload is missing a mandatory key.
    -   ``instance.payload`` is not modified.
    """
    with does_not_raise():
        instance = image_policy_update
        instance.results = Results()
    with pytest.raises(ValueError, match=match):
        instance.payload = payloads_image_policy_update(key)
    assert instance.payload is None


def test_image_policy_update_00030(image_policy_update) -> None:
    """
    ### Classes and Methods
    - ImagePolicyUpdate
        - __init__()
        - build_payloads_to_commit()
        - _verify_image_policy_ref_count()
        - payload setter

    ### Summary
    Verify build_payloads_to_commit() behavior when a request contains one
    image policy that exists on the controller and the caller has requested to
    update it.  The update consists of changing the policyDescr.

    ### Setup
    -   EpPolicies() endpoint response is mocked to indicate that two image
        policies (KR5M, NR3F) exist on the controller.
    -   ImagePolicyUpdate().payload is set to contain a payload (KR5M)
        that is present on the controller.

    ### Test
    -   payloads_to_commit will contain the payload for KR5M since it exists
        on the controller and the caller has requested to update it.
    -   The policyName for this payload will be "KR5M"
    -   The policyDescr for this payload will be "KR5M updated"
    -   Exceptions are not raised.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)
        yield responses_ep_policy_edit(key)

    gen_responses = ResponseGenerator(responses())

    def payloads():
        yield payloads_image_policy_update(key)

    gen_payloads = ResponseGenerator(payloads())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policy_update
        instance.results = Results()
        instance.rest_send = rest_send
        instance.payload = gen_payloads.next
        instance.commit()

    # The controller adds fields to the payload that we need to
    # account for when verifying diff_current, since diff_current
    # will contains these extra fields.
    payload_compare = copy.deepcopy(payloads_image_policy_update(key))
    payload_compare["fabricPolicyName"] = ""
    payload_compare["imagePresent"] = "Present"
    payload_compare["role"] = ""
    payload_compare["unInstall"] = "false"

    assert instance._payloads_to_commit == [payload_compare]
    assert instance._payloads_to_commit[0]["policyName"] == "KR5M"
    assert instance._payloads_to_commit[0]["policyDescr"] == "KR5M updated"


def test_image_policy_update_00031(image_policy_update) -> None:
    """
    ### Classes and Methods
    - ImagePolicyUpdate
        - __init__()
        - build_payloads_to_commit()
        - _verify_image_policy_ref_count()
        - payload setter

    ### Summary
    Verify behavior when a request is sent to update a policy that does
    not exist on the controller

    ### Expected behavior
    ``instance.build_payloads_to_commit()`` does not add a payload
    to the ``payloads_to_commit`` list if the associated policy
    does not exist on the controller.

    ### Setup
    -   EpPolicies() endpoint response is mocked to indicate that two image
        policies (KR5M, NR3F) exist on the controller.
    -   ImagePolicyUpdate().payload is set to contain a payload containing
        an image policy (FOO) that does not exist on the controller.

    ### Test
    -   Exceptions are not raised.
    -   _payloads_to_commit will be an empty list since policy FOO does not
        exist on the controller.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)

    gen_responses = ResponseGenerator(responses())

    def payloads():
        yield payloads_image_policy_update(key)

    gen_payloads = ResponseGenerator(payloads())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policy_update
        instance.results = Results()
        instance.rest_send = rest_send
        instance.payload = gen_payloads.next
        instance.commit()
    assert instance._payloads_to_commit == []


def test_image_policy_update_00033(image_policy_update) -> None:
    """
    ### Classes and Methods
    - ImagePolicyUpdate
        - commit()
        - build_payloads_to_commit

    ### Summary
    Verify that build_payloads_to_commit() raises ``ValueError`` when
    payload is not set.

    ### Setup
    -   ImagePolicyUpdate().payload is not set

    ### Test
    -   ``ValueError`` is raised because payload is None.
    """
    with does_not_raise():
        instance = image_policy_update
        instance.results = Results()

    match = r"ImagePolicyUpdate.commit:\s+"
    match += r"payload must be set prior to calling commit\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_image_policy_update_00034(image_policy_update) -> None:
    """
    ### Classes and Methods
    - ImagePolicyUpdateCommon
        - build_payloads_to_commit()
    - ImagePolicyUpdate
        - payload setter
        - commit()

    ### Summary
    Verify that commit() returns without doing anything when payloads
    is set to a policy that does not exist on the controller.

    ### Setup
    -   EpPolicies() endpoint response is mocked to indicate that no
        policies exist on the controller.
    -   ImagePolicyUpdate().payload is set to a policy (FOO) that does not
        exist on the controller

    ### Test
    -   ImagePolicyUpdate().commit returns without doing anything
    -   ImagePolicyUpdate()._payloads_to_commit is an empty list
    -   ImagePolicyUpdate().results.changed is empty
    -   ImagePolicyUpdate().results.failed is empty
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)

    gen_responses = ResponseGenerator(responses())

    def payloads():
        yield payloads_image_policy_update(key)

    gen_payloads = ResponseGenerator(payloads())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policy_update
        instance.results = Results()
        instance.rest_send = rest_send
        instance.payload = gen_payloads.next
        instance.commit()
    assert instance._payloads_to_commit == []
    assert len(instance.results.changed) == 0
    assert len(instance.results.failed) == 0


def test_image_policy_update_00035(image_policy_update) -> None:
    """
    ### Classes and Methods
    - ImagePolicyUpdate
        - build_payloads_to_commit()
        - send_payloads()
        - payload setter
        - commit()

    ### Summary
    Verify ImagePolicyUpdate.commit() happy path.  Controller returns
    a 200 response to an image policy update request.

    ### Setup
    -   EpPolicies() endpoint response is mocked to indicate that two policies
        (KR5M, NR3F) exist on the controller.
    -   ImagePolicyUpdate().payload is set to contain a payload for KR5M
        in which policyDescr is different from the existing policyDescr.
    -   EpPolicyEdit() endpoint response is mocked to return a successful
        (200) response.

    ### Test
    -   commit calls build_payloads_to_commit which returns one payload.
    -   commit calls send_payloads, which calls rest_send, which populates
        diff_current with the payload due to result_current indicating
        success.
    -   results.result_current is set to the expected value
    -   results.diff_current is set to the expected value
    -   results.response_current is set to the expected value
    -   results.action is set to "update"
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)
        yield responses_ep_policy_edit(key)

    gen_responses = ResponseGenerator(responses())

    def payloads():
        yield payloads_image_policy_update(key)

    gen_payloads = ResponseGenerator(payloads())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policy_update
        instance.results = Results()
        instance.rest_send = rest_send
        instance.payload = gen_payloads.next
        instance.commit()

    response_current = responses_image_policy_update(key)
    response_current["sequence_number"] = 1

    result_current = rest_send_result_current(key)
    result_current["sequence_number"] = 1

    # The controller adds fields to the payload that we need to
    # account for when verifying diff_current, since diff_current
    # will contains these extra fields.
    # Also WE add sequence_number to the diff, so this is added here
    # as well.
    diff_compare = copy.deepcopy(payloads_image_policy_update(key))
    diff_compare["sequence_number"] = 1
    diff_compare["fabricPolicyName"] = ""
    diff_compare["imagePresent"] = "Present"
    diff_compare["role"] = ""
    diff_compare["unInstall"] = "false"

    assert instance.results.action == "update"
    assert instance.rest_send.result_current == rest_send_result_current(key)
    assert instance.results.result_current == result_current
    assert instance.results.response_current == response_current
    assert instance.results.diff_current == diff_compare
    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False not in instance.results.changed
    assert True in instance.results.changed
    assert len(instance.results.metadata) == 1
    assert instance.results.metadata[0]["action"] == "update"
    assert instance.results.metadata[0]["state"] == "merged"
    assert instance.results.metadata[0]["sequence_number"] == 1


def test_image_policy_update_00036(image_policy_update) -> None:
    """
    ### Classes and Methods
    - ImagePolicyUpdate
        - build_payloads_to_commit()
        - send_payloads()
        - payload setter
        - commit()

    ### Summary
    Verify that ImagePolicyUpdate.commit() behaves as expected when the
    controller responds to an image policy update request with a 500 response.

    ### Setup
    -   EpPolicies() endpoint response is mocked to indicate that one policy
        (KR5M) exists on the controller.
    -   ImagePolicyUpdate().payloads is set to contain the payload for
        image policy KR5M with policyDescr changed.
    -   EpPolicyEdit() endpoint response is mocked to return an internal
        server error (500) response.

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
        yield payloads_image_policy_update(key)

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
        instance = image_policy_update
        instance.results = Results()
        instance.rest_send = rest_send
        instance.payload = gen_payloads.next
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


def test_image_policy_update_00050(image_policy_update) -> None:
    """
    ### Classes and Methods
    - ImagePolicyUpdate
        - build_payloads_to_commit()
        - send_payloads()
        - payload setter
        - commit()

    ### Summary
    Verify that ValueError is raised when an image policy update request is made
    for an image policy which has a ref_count != 0 on the controller, i.e.
    switches are attached to the image policy.

    ### Setup
    -   EpPolicies() endpoint response is mocked to indicate that one policy
        (KR5M) exists on the controller with ref_count == 2.
    -   ImagePolicyUpdate().payloads is set to contain the payload for
        image policy KR5M with policyDescr changed.

    ### Test
    -   commit calls ``build_payloads_to_commit``
    -   ``build_payloads_to_commit`` calls ``_verify_image_policy_ref_count``
    -   ``_verify_image_policy_ref_count`` raises ``ValueError`` with the
        expected message.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)

    gen_responses = ResponseGenerator(responses())

    def payloads():
        yield payloads_image_policy_update(key)

    gen_payloads = ResponseGenerator(payloads())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policy_update
        instance.results = Results()
        instance.rest_send = rest_send
        instance.payload = gen_payloads.next

    match = r"ImagePolicyUpdate\._verify_image_policy_ref_count:\s+"
    match += r"One or more policies have devices attached\.\s+"
    match += r"Detach these policies from all devices first using\s+"
    match += r"the dcnm_image_upgrade module with state == deleted\."
    with pytest.raises(ValueError, match=match):
        instance.commit()
