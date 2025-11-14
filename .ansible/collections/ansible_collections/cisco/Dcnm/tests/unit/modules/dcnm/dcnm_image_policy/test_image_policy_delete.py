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
    MockAnsibleModule, does_not_raise, image_policy_delete_fixture, params,
    responses_ep_policies, responses_ep_policy_delete,
    results_image_policy_delete)


def test_image_policy_delete_00000(image_policy_delete) -> None:
    """
    ### Classes and Methods
    - ImagePolicyDelete
        - __init__()

    ### Summary
    Verify that the class attributes are initialized to expected values
    and that exceptions are not raised.

    ### Test
    - Class attributes are initialized to expected values
    - Exceptions are not raised.
    """
    with does_not_raise():
        instance = image_policy_delete
    assert instance.action == "delete"
    assert instance.check_mode is None
    assert instance.class_name == "ImagePolicyDelete"
    assert instance.endpoint.class_name == "EpPolicyDelete"
    assert instance.params.get("state") == "deleted"
    assert instance.payload is None
    assert instance.state is None
    assert instance.verb == "DELETE"
    assert (
        instance.path
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policy"
    )
    assert instance.policy_names is None
    assert instance._policies_to_delete == []
    assert instance._policy_names is None
    assert instance._results is None
    assert instance._rest_send is None


def test_image_policy_delete_00020(image_policy_delete) -> None:
    """
    ### Classes and Methods
    - ImagePolicyDelete
        - __init__()
        - policy_names.setter

    ### Summary
    Verify that ``policy_names`` is set correctly to a list of strings.

    ### Test
    -   ``policy_names`` is set to expected value.
    -   Exceptions are not raised.
    """
    policy_names = ["FOO", "BAR"]
    with does_not_raise():
        instance = image_policy_delete
        instance.policy_names = policy_names
    assert instance.policy_names == policy_names


def test_image_policy_delete_00021(image_policy_delete) -> None:
    """
    ### Classes and Methods
    - ImagePolicyDelete
        - __init__()
        - policy_names.setter

    ### Summary
    Verify that ``policy_names.setter`` raises ''TypeError'' when
    ``policy_names`` is not a list.

    ### Test
    -   ``TypeError`` is raised because`` policy_names`` is not a list.
    -   The error message matches expectations.
    -   ``instance.policy_names`` is not modified.
    """

    with does_not_raise():
        instance = image_policy_delete

    match = r"ImagePolicyDelete.policy_names:\s+"
    match += r"policy_names must be a list\."
    with pytest.raises(TypeError, match=match):
        instance.policy_names = "NOT_A_LIST"
    assert instance.policy_names is None


def test_image_policy_delete_00022(image_policy_delete) -> None:
    """
    ### Classes and Methods
    - ImagePolicyDelete
        - __init__()
        - policy_names.setter

    ### Summary
    Verify that ``policy_names.setter`` raises ''TypeError'' when
    ``policy_names`` is a list containing non-strings.

    ### Test
    -   ``TypeError`` is raised because`` policy_names`` contains elements
        that are not strings.
    -   The error message matches expectations.
    -   ``instance.policy_names`` is not modified.
    """
    with does_not_raise():
        instance = image_policy_delete

    match = r"ImagePolicyDelete.policy_names:\s+"
    match += r"policy_names must be a list of strings\."
    with pytest.raises(TypeError, match=match):
        instance.policy_names = [1, 2, 3]
    assert instance.policy_names is None


def test_image_policy_delete_00030(image_policy_delete) -> None:
    """
    ### Classes and Methods
    - ImagePolicyDelete
        - __init__()
        - _verify_image_policy_ref_count()
        - policy_names.setter
        - _get_policies_to_delete()

    ### Summary
    The requested policy to delete does not exist on the controller.
    Verify that instance._policies_to_delete is an empty list.

    ### Setup
    -   EpPolicies() endpoint response is mocked to indicate that two image
        policies (KR5M, NR3F) exist on the controller.
    -   ImagePolicyDelete.policy_names is set to contain one policy_name (FOO)
        that does not exist on the controller.

    ### Test
    -   instance._policies_to_delete will an empty list because all of the
        policy_names in instance.policy_names do not exist on the controller
        and, hence, nothing needs to be deleted.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policy_delete
        instance.results = Results()
        instance.rest_send = rest_send
        instance.policy_names = ["FOO"]
        instance.commit()

    assert instance._policies_to_delete == []
    assert False in instance.results.changed
    assert instance.results.metadata[0]["action"] == "delete"
    assert instance.results.metadata[0]["check_mode"] is False
    assert instance.results.metadata[0]["sequence_number"] == 1
    assert instance.results.metadata[0]["state"] == "deleted"

    assert instance.results.response[0]["RETURN_CODE"] == 200
    assert instance.results.response[0]["MESSAGE"] == "No image policies to delete."
    assert instance.results.response[0]["sequence_number"] == 1

    assert instance.results.result[0]["changed"] is False
    assert instance.results.result[0]["success"] is True
    assert instance.results.result[0]["sequence_number"] == 1


def test_image_policy_delete_00031(image_policy_delete) -> None:
    """
    ### Classes and Methods
    - ImagePolicyDelete
        - __init__()
        - policy_names.setter
        - _get_policies_to_delete()

    ### Summary
    One policy (KR5M) is requested to be deleted and it exists on the controller.
    Verify that instance._policies_to_delete contains the policy name KR5M.

    ### Setup
    -   EpPolicies() endpoint response is mocked to indicate that two image policies
        (KR5M, NR3F) exist on the controller.
    -   ImagePolicyDelete.policy_names is set to contain one policy_name (KR5M)
        that exists on the controller.

    ### Test
    -   instance._policies_to_delete will contain one policy name (KR5M)
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)
        yield responses_ep_policy_delete(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policy_delete
        instance.results = Results()
        instance.rest_send = rest_send
        instance.policy_names = ["KR5M"]
        instance.commit()

    assert instance._policies_to_delete == ["KR5M"]
    assert True in instance.results.changed
    assert instance.results.metadata[0]["action"] == "delete"
    assert instance.results.metadata[0]["check_mode"] is False
    assert instance.results.metadata[0]["sequence_number"] == 1
    assert instance.results.metadata[0]["state"] == "deleted"

    assert instance.results.response[0]["RETURN_CODE"] == 200
    assert instance.results.response[0]["MESSAGE"] == "OK"
    assert instance.results.response[0]["sequence_number"] == 1

    assert instance.results.result[0]["changed"] is True
    assert instance.results.result[0]["success"] is True
    assert instance.results.result[0]["sequence_number"] == 1


def test_image_policy_delete_00032(image_policy_delete) -> None:
    """
    ### Classes and Methods
    - ImagePolicyDelete
        - policy_names.setter
        - _get_policies_to_delete()

    ### Summary
    Of two policies being requested to delete, one policy exists on the controller
    and one policy does not exist on the controller.  Verify that only the policy
    that exists on the controller is added to instance._policies_to_delete.

    ### Setup
    -   EpPolicies() endpoint response is mocked to indicate that two image policies
        (KR5M, NR3F) exist on the controller.
    -   ImagePolicyDelete().policy_names is set to contain one image policy name (FOO)
        that does not exist on the controller and one image policy name (KR5M) that
        does exist on the controller.

    Test
    -   instance._policies_to_delete contains one policy name (KR5M).
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)
        yield responses_ep_policy_delete(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policy_delete
        instance.results = Results()
        instance.rest_send = rest_send
        instance.policy_names = ["FOO", "KR5M"]
        instance.commit()

    assert instance._policies_to_delete == ["KR5M"]
    assert True in instance.results.changed
    assert instance.results.metadata[0]["action"] == "delete"
    assert instance.results.metadata[0]["check_mode"] is False
    assert instance.results.metadata[0]["sequence_number"] == 1
    assert instance.results.metadata[0]["state"] == "deleted"

    assert instance.results.response[0]["RETURN_CODE"] == 200
    assert instance.results.response[0]["MESSAGE"] == "OK"
    assert instance.results.response[0]["sequence_number"] == 1

    assert instance.results.result[0]["changed"] is True
    assert instance.results.result[0]["success"] is True
    assert instance.results.result[0]["sequence_number"] == 1


def test_image_policy_delete_00033(image_policy_delete) -> None:
    """
    ### Classes and Methods
    - ImagePolicyDelete
        - commit()

    ### Summary
    Verify that ``_validate_commit_parameters`` raises ``ValueError`` when
    ``commit`` is called and ``policy_names`` is not set.

    ### Setup
    -   ImagePolicyDelete().policy_names is not set.

    ### Test
    -   ``ValueError`` is raised because policy_names is not set.
    """
    with does_not_raise():
        instance = image_policy_delete
        instance.results = Results()

    match = r"ImagePolicyDelete\._validate_commit_parameters: "
    match += r"policy_names must be set prior to calling commit\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_image_policy_delete_00034(image_policy_delete) -> None:
    """
    ### Classes and Methods
    - ImagePolicyDelete
        - policy_names setter
        - commit()

    ### Summary
    commit() is called with policy_names set to an empty list.

    ### Setup
    -   ImagePolicyDelete().policy_names is set to an empty list
    -   EpPolicies() endpoint response is mocked to indicate that no policies
        exist on the controller.

    ### Test
    -   ImagePolicyDelete().commit returns without doing anything.
    -   Exceptions are not raised.
    -   ``instance.results`` matches expectations.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)
        yield responses_ep_policy_delete(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policy_delete
        instance.results = Results()
        instance.rest_send = rest_send
        instance.policy_names = []
        instance.commit()
    assert False in instance.results.changed
    assert False in instance.results.failed


def test_image_policy_delete_00036(image_policy_delete) -> None:
    """
    ### Classes and Methods
    - ImagePolicyDelete
        - policy_names setter
        - _get_policies_to_delete()
        - commit()

    ### Summary
    commit() is called with policy_names set to a policy_name that does not exist on the controller.

    ### Setup
    -   EpPolicies() endpoint response is mocked to indicate that no policies exist on the controller.
    -   ImagePolicyDelete().policy_names is set a policy_name that is not on the controller.

    ### Test
    -   ImagePolicyDelete()._get_policies_to_delete return an empty list
    -   ImagePolicyDelete().commit returns without doing anything
    -   instance.results match expectations.
    -   Exceptions are not raised.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)
        yield responses_ep_policy_delete(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policy_delete
        instance.results = Results()
        instance.rest_send = rest_send
        instance.policy_names = ["FOO"]
        instance.commit()

    assert len(instance._policies_to_delete) == 0
    assert False in instance.results.changed
    assert False in instance.results.failed


def test_image_policy_delete_00037(monkeypatch, image_policy_delete) -> None:
    """
    ### Classes and Methods
    - ImagePolicyDelete
        - _get_policies_to_delete()
        - policy_names setter
        - commit()

    ### Summary
    commit() is called with policy_names set to a policy_name that exists on
    the controller, and the controller returns a success (200) response.

    ### Setup
    -   EpPolicies() endpoint response is mocked to indicate image policy
        (KR5M) exists on the controller.
    -   ImagePolicyDelete().policy_names is set to contain policy_name KR5M.
    -   EpPolicyDelete() endpoint response is mocked to return a successful
        (200) response.

    ### Test
    -   Exceptions are not raised.
    -   commit calls _get_policies_to_delete which returns a list containing policy_name (KR5M)
    -   instance.results match expectations.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)
        yield responses_ep_policy_delete(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policy_delete
        instance.results = Results()
        instance.rest_send = rest_send
        instance.policy_names = ["KR5M"]
        instance.commit()

    assert instance._policies_to_delete == ["KR5M"]
    assert instance.results.result_current == results_image_policy_delete(key)
    assert True in instance.results.changed
    assert False in instance.results.failed

    assert instance.results.diff[0]["policyNames"] == ["KR5M"]
    assert instance.results.diff[0]["sequence_number"] == 1

    assert instance.results.metadata[0]["action"] == "delete"
    assert instance.results.metadata[0]["check_mode"] is False
    assert instance.results.metadata[0]["sequence_number"] == 1
    assert instance.results.metadata[0]["state"] == "deleted"

    assert instance.results.response[0]["RETURN_CODE"] == 200
    assert instance.results.response[0]["MESSAGE"] == "OK"
    assert instance.results.response[0]["sequence_number"] == 1

    assert instance.results.result[0]["changed"] is True
    assert instance.results.result[0]["success"] is True
    assert instance.results.result[0]["sequence_number"] == 1


def test_image_policy_delete_00038(monkeypatch, image_policy_delete) -> None:
    """
    ### Classes and Methods
    - ImagePolicyDelete
        - _get_policies_to_delete()
        - policy_names setter
        - commit()

    ### Summary
    commit() is called with policy_names set to a policy_name that exists on
    the controller, and the controller returns a failure (500) response.

    ### Setup
    -   EpPolicies() endpoint response is mocked to indicate policy (KR5M) exists on
        the controller.
    -   ImagePolicyDelete().policy_names is set to contain one payload (KR5M).
    -   EpPolicyDelete() endpoint response is mocked to return a failure (500)
        response.

    ### Test
    -   Exceptions are not raised.
    -   commit calls _get_policies_to_delete which returns a list containing
        policy_name (KR5M)
    -   instance.results match expectations.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)
        yield responses_ep_policy_delete(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    rest_send.timeout = 1
    rest_send.unit_test = True

    with does_not_raise():
        instance = image_policy_delete
        instance.results = Results()
        instance.rest_send = rest_send
        instance.policy_names = ["KR5M"]
        instance.commit()

    assert instance._policies_to_delete == ["KR5M"]
    assert instance.results.result_current == results_image_policy_delete(key)
    assert True in instance.results.failed
    assert False in instance.results.changed

    assert instance.results.diff[0]["sequence_number"] == 1

    assert instance.results.metadata[0]["action"] == "delete"
    assert instance.results.metadata[0]["check_mode"] is False
    assert instance.results.metadata[0]["sequence_number"] == 1
    assert instance.results.metadata[0]["state"] == "deleted"

    assert instance.results.response[0]["RETURN_CODE"] == 500
    assert instance.results.response[0]["MESSAGE"] == "NOK"
    assert instance.results.response[0]["sequence_number"] == 1

    assert instance.results.result[0]["changed"] is False
    assert instance.results.result[0]["success"] is False
    assert instance.results.result[0]["sequence_number"] == 1
