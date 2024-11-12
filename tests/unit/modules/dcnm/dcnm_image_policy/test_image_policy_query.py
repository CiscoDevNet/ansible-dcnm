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
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_image_policy.utils import (
    MockAnsibleModule, does_not_raise, image_policies_all_policies,
    image_policy_query_fixture, params, rest_send_response_current)


def test_image_policy_query_00000(image_policy_query) -> None:
    """
    ### Classes and Methods
    - ImagePolicyQuery
        - __init__()

    ### Test
    - Class attributes are initialized to expected values
    - Exceptions are not raised.
    """
    with does_not_raise():
        instance = image_policy_query

    assert instance.class_name == "ImagePolicyQuery"
    assert instance.action == "query"
    assert instance._results is None
    assert instance._policies_to_query == []
    assert instance._policy_names is None


def test_image_policy_query_00010(image_policy_query) -> None:
    """
    ### Classes and Methods
    - ImagePolicyQuery
        - __init__()
        - policy_names.setter

    ### Test
    -   ``policy_names`` is set to expected value.
    -   Exceptions are not raised.
    """
    policy_names = ["FOO", "BAR"]
    with does_not_raise():
        instance = image_policy_query
        instance.policy_names = policy_names

    assert instance.policy_names == policy_names


def test_image_policy_query_00011(image_policy_query) -> None:
    """
    ### Classes and Methods
    - ImagePolicyQuery
        - __init__()
        - policy_names.setter

    ### Summary
    Verify that ``policy_names.setter`` raises ``TypeError`` when
    ``policy_names`` is not a list.

    ### Test
    -   ``TypeError`` is raised because policy_names is not a list.
    -   ``instance.policy_names`` is not modified.
    """
    with does_not_raise():
        instance = image_policy_query

    match = r"ImagePolicyQuery.policy_names:\s+"
    match += r"policy_names must be a list\.\s+"
    match += r"got str for value NOT_A_LIST"
    with pytest.raises(TypeError, match=match):
        instance.policy_names = "NOT_A_LIST"
    assert instance.policy_names is None


def test_image_policy_query_00012(image_policy_query) -> None:
    """
    ### Classes and Methods
    - ImagePolicyQuery
        - __init__()
        - policy_names.setter

    ### Summary
    Verify that ``policy_names.setter`` raises ``ValueError`` when
    ``policy_names`` is set to a list containing non-string elements.

    ### Test
    -   ``policy_names.setter`` raises ``TypeError``.
    -   Error message matches expected value.
    -   ``instance.policy_names`` is not modified.
    """
    with does_not_raise():
        instance = image_policy_query

    match = r"ImagePolicyQuery\.policy_names:\s+"
    match += r"policy_names must be a list of strings\.\s+"
    match += r"got int for value 3"
    with pytest.raises(TypeError, match=match):
        instance.policy_names = ["1", "2", 3]

    assert instance.policy_names is None


def test_image_policy_query_00013(image_policy_query) -> None:
    """
    ### Classes and Methods
    - ImagePolicyQuery
        - policy_names.setter

    ### Summary
    Verify that ``policy_names.setter`` raises ``ValueError`` when
    ``policy_names`` is set to an empty list.

    ### Setup
    -   ``policy_names`` is set to an empty list.

    ### Test
    -   ``policy_names.setter`` raises ``ValueError``.
    -   Error message matches expected value.
    """
    match = r"ImagePolicyQuery\.policy_names:\s+"
    match += r"policy_names must be a list of at least one string\."
    with pytest.raises(ValueError, match=match):
        instance = image_policy_query
        instance.policy_names = []


def test_image_policy_query_00020(image_policy_query) -> None:
    """
    ### Classes and Methods
    - ImagePolicyQuery
        - __init__()
        - commit()

    ### Summary
    Verify ``commit`` raises ``ValueError`` when ``policy_names`` is not.

    ### Test
    -   ``commit`` raises ``ValueError``.
    -   Error message matches expected value.
    -   ``instance.policy_names`` is not modified.
    """

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    image_policies = ImagePolicies()
    image_policies.rest_send = rest_send
    image_policies.results = Results()

    with does_not_raise():
        instance = image_policy_query
        instance._image_policies = image_policies

    match = r"ImagePolicyQuery\.commit:\s+"
    match += r"policy_names must be set prior to calling commit\."
    with pytest.raises(ValueError, match=match):
        instance.commit()

    assert instance.policy_names is None


def test_image_policy_query_00030(image_policy_query) -> None:
    """
    ### Classes and Methods
    - ImagePolicyQuery
        - __init__()
        - _verify_image_policy_ref_count()
        - policy_names.setter
        - _get_policies_to_query()
        - commit()

    ### Summary
    Verify behavior when user queries a policy that does not exist on the
    controller.

    ### Setup
    -   ImagePolicies().all_policies, is mocked to indicate that one image
        policy (KR5M) exists on the controller.
    -   ImagePolicyQuery.policy_names is set to contain one policy_name (FOO)
        that does not exist on the controller.

    ### Test
    -   ImagePolicyQuery.commit() calls _get_policies_to_query() which sets
        instance._policies_to_query to an empty list.
    -   instance.results.changed set() contains False
    -   instance.results.failed set() contains False
    -   commit() returns without doing anything else
    -   Exceptions are not raised.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield rest_send_response_current(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    image_policies = ImagePolicies()
    image_policies.rest_send = rest_send
    image_policies.results = Results()

    with does_not_raise():
        instance = image_policy_query
        instance._image_policies = image_policies
        instance.policy_names = ["FOO"]
        instance.results = Results()
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)
    assert len(instance.results.diff) == 1
    assert len(instance.results.result) == 1
    assert len(instance.results.response) == 1
    assert instance.results.diff[0].get("policyName", None) is None
    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_image_policy_query_00031(image_policy_query) -> None:
    """
    ### Classes and Methods
    - ImagePolicyQuery
        - __init__()
        - policy_names.setter
        - _get_policies_to_query()
        - commit()

    ### Summary
    Verify behavior when user queries a policy that exists on the controller.

    ### Setup
    -   ImagePolicies().all_policies is mocked to indicate that one image
        policy (KR5M) exists on the controller.
    -   ImagePolicyQuery.policy_names is set to contain one policy_name (KR5M)
        that exists on the controller.

    ### Test
    -   instance.diff is a list containing one dict with keys action == "query"
        and policyName == "KR5M"
    -   instance.response is a list with one element
    -   instance.response_current is a dict with key RETURN_CODE == 200
    -   instance.result is a list with one element
    -   instance.result_current is a dict with key success == True
    -   Exceptions are not raised.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield rest_send_response_current(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    image_policies = ImagePolicies()
    image_policies.rest_send = rest_send
    image_policies.results = Results()

    with does_not_raise():
        instance = image_policy_query
        instance._image_policies = image_policies
        instance.policy_names = ["KR5M"]
        instance.results = Results()
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)
    assert len(instance.results.diff) == 1
    assert len(instance.results.result) == 1
    assert len(instance.results.response) == 1
    assert instance.results.diff[0].get("policyName", None) == "KR5M"
    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_image_policy_query_00032(image_policy_query) -> None:
    """
    ### Classes and Methods
    - ImagePolicyQuery
        - policy_names.setter
        - _get_policies_to_query()
        - commit()

    ### Summary
    Verify behavior when user queries multiple policies, some of which exist
    on the controller and some of which do not exist on the controller.

    ### Setup
    -   ImagePolicies().all_policies, is mocked to indicate that two image
        policies (KR5M, NR3F) exist on the controller.
    -   ImagePolicyQuery().policy_names is set to contain one image policy
        name (FOO) that does not exist on the controller and two image policy
        names (KR5M, NR3F) that do exist on the controller.

    ### Test
    -   instance.diff is a list containing two elements
    -   instance.diff[0] contains keys action == "query" and policyName == "KR5M"
    -   instance.diff[1] contains keys action == "query" and policyName == "NR3F"
    -   instance.response is a list with one element
    -   instance.response_current is a dict with key RETURN_CODE == 200
    -   instance.result is a list with one element
    -   instance.result_current is a dict with key success == True
    -   Exceptions are not raised.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield rest_send_response_current(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    image_policies = ImagePolicies()
    image_policies.rest_send = rest_send
    image_policies.results = Results()

    with does_not_raise():
        instance = image_policy_query
        instance._image_policies = image_policies
        instance.policy_names = ["KR5M", "NR3F", "FOO"]
        instance.results = Results()
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)
    assert len(instance.results.diff) == 2
    assert len(instance.results.result) == 2
    assert len(instance.results.response) == 2
    assert instance.results.diff[0].get("policyName", None) == "KR5M"
    assert instance.results.diff[1].get("policyName", None) == "NR3F"
    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.diff[1].get("sequence_number", None) == 2
    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_image_policy_query_00033(image_policy_query) -> None:
    """
    ### Classes and Methods
    - ImagePolicyQuery
        - __init__()
        - policy_names.setter
        - _get_policies_to_query()
        - commit()

    ### Summary
    Verify behavior when no image policies exist on the controller and the user
    queries for an image policy that, of course, does not exist.

    ### Setup
    -   ImagePolicies().all_policies, is mocked to indicate that no image
        policies exist on the controller.
    -   ImagePolicyQuery.policy_names is set to contain one policy_name
        (FOO) that does not exist on the controller.

    ### Test
    -   commit() calls _get_policies_to_query() which sets
        ``instance._policies_to_query`` to an empty list.
    -   commit() sets instance.changed to False
    -   commit() sets instance.failed to False
    -   commit() returns without doing anything else
    -   Exceptions are not raised.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield rest_send_response_current(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    image_policies = ImagePolicies()
    image_policies.rest_send = rest_send
    image_policies.results = Results()

    with does_not_raise():
        instance = image_policy_query
        instance._image_policies = image_policies
        instance.policy_names = ["FOO"]
        instance.results = Results()
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)
    assert len(instance.results.diff) == 1
    assert len(instance.results.result) == 1
    assert len(instance.results.response) == 1
    assert instance.results.diff[0].get("policyName", None) is None
    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed
