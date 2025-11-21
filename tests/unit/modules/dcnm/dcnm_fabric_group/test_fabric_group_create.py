# Copyright (c) 2025 Cisco and/or its affiliates.
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
# pylint: disable=line-too-long
"""
Unit tests for FabricGroupCreate class in module_utils/fabric_group/create.py
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2025 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import inspect

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.response_handler import ResponseHandler
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results_v2 import Results
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_file import Sender
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric_group.fabric_groups import FabricGroups
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric_group.utils import (
    MockAnsibleModule,
    does_not_raise,
    fabric_group_create_fixture,
    params,
    payloads_fabric_group_create,
    responses_fabric_group_create,
    responses_fabric_groups,
)


def test_fabric_group_create_00000(fabric_group_create) -> None:
    """
    ### Classes and Methods

    - FabricGroupCommon
        - __init__()
    - FabricGroupCreate
        - __init__()

    ### Test
    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_group_create
        instance.fabric_groups = FabricGroups()
    assert instance.class_name == "FabricGroupCreate"
    assert instance.action == "fabric_group_create"
    assert instance.fabric_groups.class_name == "FabricGroups"


def test_fabric_group_create_00020(fabric_group_create) -> None:
    """
    ### Classes and Methods

    - FabricGroupCommon
        - __init__()
        - payloads setter
    - FabricGroupCreate
        - __init__()
        - payloads setter

    ### Summary
    -   Verify that payloads is set to expected value when a valid list
        of payloads is passed to FabricGroupCreate().payloads
    -   Exception is not raised.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = fabric_group_create
        instance.results = Results()
        instance.payloads = [payloads_fabric_group_create(key)]
    assert instance.payloads == [payloads_fabric_group_create(key)]


def test_fabric_group_create_00021(fabric_group_create) -> None:
    """
    ### Classes and Methods

    - FabricGroupCommon
        - __init__()
        - payloads setter
    - FabricGroupCreate
        - __init__()
        - payloads setter

    ### Summary
    -   Verify ``ValueError`` is raised because payloads is not a ``list``
    -   Verify ``instance.payloads`` is not modified, hence it retains its
        initial value of [] (empty list)
    """
    match = r"FabricGroupCreate\.payloads: "
    match += r"payloads must be a list of dict\."

    with does_not_raise():
        instance = fabric_group_create
        instance.results = Results()
    with pytest.raises(ValueError, match=match):
        instance.payloads = "NOT_A_LIST"
    assert instance.payloads == []


def test_fabric_group_create_00022(fabric_group_create) -> None:
    """
    ### Classes and Methods

    - FabricGroupCommon
        - __init__()
    - FabricGroupCreate
        - __init__()
        - payloads setter

    ### Summary
    Verify that ``ValueError`` is raised because payload is an empty dict
    missing mandatory parameters.
    """
    with does_not_raise():
        instance = fabric_group_create
        instance.results = Results()
        instance.rest_send = RestSend(params)

    match = r"FabricGroupCreate\._verify_payload: "
    match += r"Playbook configuration for fabric group .* is missing mandatory parameters"
    with pytest.raises(ValueError, match=match):
        instance.payloads = [{}]


@pytest.mark.parametrize(
    "mandatory_parameter",
    ["FABRIC_NAME"],
)
def test_fabric_group_create_00023(fabric_group_create, mandatory_parameter) -> None:
    """
    ### Classes and Methods

    - FabricGroupCommon
        - __init__()
    - FabricGroupCreate
        - __init__()
        - payloads setter

    ### Summary
    -   Verify that ``ValueError`` is raised because payload is missing
        mandatory parameters.

    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    payload = payloads_fabric_group_create(key)
    payload.pop(mandatory_parameter, None)

    with does_not_raise():
        instance = fabric_group_create
        instance.results = Results()
        instance.rest_send = RestSend(params)

    match = r"FabricGroupCreate\._verify_payload: "
    match += r"Playbook configuration for fabric group .* is missing mandatory parameters:"
    with pytest.raises(ValueError, match=match):
        instance.payloads = [payload]
    assert instance.payloads == []


def test_fabric_group_create_00024(fabric_group_create) -> None:
    """
    ### Classes and Methods

    - FabricGroupCommon
        - __init__()
        - payloads setter
    - FabricGroupCreate
        - __init__()
        - commit()

    ### Summary
    -   Verify ``ValueError`` is raised because payloads is not set (empty list)
        prior to calling commit
    -   Verify instance.payloads retains its initial value of [] (empty list)
    """
    with does_not_raise():
        instance = fabric_group_create
        instance.results = Results()
        instance.rest_send = RestSend(params)

    match = r"FabricGroupCreate\.commit: "
    match += r"payloads must be set prior to calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()
    assert instance.payloads == []


def test_fabric_group_create_00025(fabric_group_create) -> None:
    """
    Classes and Methods
    - FabricGroupCommon
        - __init__()
        - payloads setter
    - FabricGroupCreate
        - __init__()

    Summary
    -   Verify behavior when payload contains FABRIC_TYPE key with
        an unexpected value.

    Test
    -   ``ValueError`` is raised because the value of FABRIC_TYPE is invalid
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = fabric_group_create
        instance.fabric_groups = FabricGroups()
        instance.fabric_groups.rest_send = RestSend(params)
        instance.fabric_groups.rest_send.unit_test = True
        instance.rest_send = RestSend(params)
        instance.rest_send.unit_test = True
        instance.results = Results()

    match = r"FabricGroupCreate\._verify_payload:\s+"
    match += r"Playbook configuration for fabric group MFG1 contains an invalid\s+"
    match += r"FABRIC_TYPE \(INVALID_FABRIC_TYPE\)\."

    with pytest.raises(ValueError, match=match):
        instance.payloads = [payloads_fabric_group_create(key)]


def test_fabric_group_create_00026(fabric_group_create) -> None:
    """
    ### Classes and Methods

    - FabricGroupCommon
        - __init__()
        - payloads setter
    - FabricGroupCreate
        - __init__()

    ### Summary
    Verify behavior when ``rest_send.params`` is not set prior to calling commit.

    ### Test
    -   ``ValueError`` is raised because ``rest_send.params`` is not set prior
        to calling commit.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = fabric_group_create
        instance.fabric_groups = FabricGroups()
        instance.results = Results()
        instance.payloads = [payloads_fabric_group_create(key)]

    match = r"FabricGroupCreate\.commit: "
    match += r"rest_send\.params must be set prior to calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fabric_group_create_00030(fabric_group_create) -> None:
    """
    ### Classes and Methods

    - FabricGroupCommon()
        - __init__()
        - payloads setter
    - FabricGroups()
        - __init__()
        - refresh()
    - FabricGroupCreate
        - __init__()
        - commit()

    ### Summary
    -   Verify behavior when user attempts to create a fabric group and no
        fabric groups exist on the controller and the RestSend() RETURN_CODE
        is 200.

    ### Code Flow

    -   FabricGroupCreate.payloads is set to contain one payload for a
        fabric group (MFG1) that does not exist on the controller.
    -   FabricGroupCreate.commit() calls FabricGroupCreate()._build_payloads_to_commit()
    -   FabricGroupCreate()._build_payloads_to_commit() calls FabricGroups().refresh()
        which returns a dict with keys DATA == [], RETURN_CODE == 200
    -   FabricGroupCreate()._build_payloads_to_commit() sets
        FabricGroupCreate()._payloads_to_commit to a list containing
        fabric group MFG1 payload
    -   FabricGroupCreate.commit() calls RestSend().commit() which sets
        RestSend().response_current to a dict with keys:
        -   DATA == {MFG1 fabric group data dict}
            RETURN_CODE == 200
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(key)
        yield responses_fabric_group_create(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_group_create
        instance.fabric_groups = FabricGroups()
        instance.fabric_groups.rest_send = rest_send
        instance.fabric_groups.results = Results()
        instance.rest_send = rest_send
        instance.results = Results()
        instance.payloads = [payloads_fabric_group_create(key)]
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 2
    assert len(instance.results.metadata) == 2
    assert len(instance.results.response) == 2
    assert len(instance.results.result) == 2

    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.diff[1].get("fabricName", None) == "MFG1"

    assert instance.results.metadata[1].get("action", None) == "fabric_group_create"
    assert instance.results.metadata[1].get("check_mode", None) is False
    assert instance.results.metadata[1].get("sequence_number", None) == 2
    assert instance.results.metadata[1].get("state", None) == "merged"

    assert instance.results.response[1].get("RETURN_CODE", None) == 200
    assert instance.results.response[1].get("METHOD", None) == "POST"

    assert instance.results.result[1].get("changed", None) is True
    assert instance.results.result[1].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    # Query operations add False to instance.results.changed
    # The CREATE operation adds True to instance.results.changed
    # Hence, both True and False are in instance.results.changed
    assert False in instance.results.changed
    assert True in instance.results.changed


def test_fabric_group_create_00031(fabric_group_create) -> None:
    """
    Classes and Methods
    - FabricGroupCommon()
        - __init__()
    - FabricGroups()
        - __init__()
        - refresh()
    - FabricGroupCreate()
        - __init__()
        - commit()

    Summary
    -   Verify behavior when FabricGroupCreate() is used to create a
        fabric group and the fabric group exists on the controller.

    Setup
    -   FabricGroups().refresh() is set to indicate that fabric group MFG1
        exists on the controller

    Code Flow
    -   FabricGroupCreate.payloads is set to contain one payload for a
        fabric group (MFG1) that already exists on the controller.
    -   FabricGroupCreate.commit() calls FabricGroupCreate()._build_payloads_to_commit()
    -   FabricGroupCreate()._build_payloads_to_commit() calls FabricGroups().refresh()
        which returns a dict with keys DATA == [{MFG1 fabric group data dict}],
        RETURN_CODE == 200
    -   FabricGroupCreate()._build_payloads_to_commit() sets
        FabricGroupCreate()._payloads_to_commit to an empty list since
        fabric group MFG1 already exists on the controller
    -   FabricGroupCreate.commit() returns without doing anything.

    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_group_create
        instance.fabric_groups = FabricGroups()
        instance.fabric_groups.rest_send = rest_send
        instance.fabric_groups.results = Results()
        instance.rest_send = rest_send
        instance.results = Results()
        instance.payloads = [payloads_fabric_group_create(key)]
        instance.commit()

    assert instance._payloads_to_commit == []
    # Results contain data from fabric_groups.refresh() even though no create was performed
    assert len(instance.results.diff) == 1
    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert len(instance.results.metadata) == 1
    assert len(instance.results.response) == 1
    assert len(instance.results.result) == 1


def test_fabric_group_create_00032(monkeypatch, fabric_group_create) -> None:
    """
    Classes and Methods
    - FabricGroupCommon()
        - __init__()
        - payloads setter
    - FabricGroups()
        - __init__()
        - refresh()
    - FabricGroupCreate
        - __init__()
        - commit()

    Summary
    -   Verify behavior when user attempts to create a fabric group but the
        controller RETURN_CODE is 500.

    Setup
    -   FabricGroups().refresh() is set to indicate that no fabric groups
        exist on the controller

    Code Flow
    -   FabricGroupCreate.payloads is set to contain one payload for a
        fabric group (MFG1) that does not exist on the controller.
    -   FabricGroupCreate.commit() calls FabricGroupCreate()._build_payloads_to_commit()
    -   FabricGroupCreate()._build_payloads_to_commit() calls FabricGroups().refresh()
        which returns a dict with keys DATA == [], RETURN_CODE == 200
    -   FabricGroupCreate()._build_payloads_to_commit() sets
        FabricGroupCreate()._payloads_to_commit to a list containing
        fabric group MFG1 payload
    -   FabricGroupCreate.commit() calls RestSend().commit() which sets
        RestSend().response_current to a dict with keys:
        -   DATA == "Error in validating provided name value pair"
            RETURN_CODE == 500,
            MESSAGE = "Internal Server Error"
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(key)
        yield responses_fabric_group_create(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_group_create
        instance.fabric_groups = FabricGroups()
        instance.fabric_groups.results = Results()
        instance.fabric_groups.rest_send = rest_send
        instance.rest_send = rest_send
        instance.results = Results()
        instance.payloads = [payloads_fabric_group_create(key)]
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 2
    assert len(instance.results.metadata) == 2
    assert len(instance.results.response) == 2
    assert len(instance.results.result) == 2

    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.diff[1].get("sequence_number", None) == 2

    assert instance.results.metadata[1].get("action", None) == "fabric_group_create"
    assert instance.results.metadata[1].get("check_mode", None) is False
    assert instance.results.metadata[1].get("sequence_number", None) == 2
    assert instance.results.metadata[1].get("state", None) == "merged"

    assert instance.results.response[1].get("RETURN_CODE", None) == 400
    assert instance.results.response[1].get("METHOD", None) == "POST"

    assert instance.results.result[1].get("changed", None) is False
    assert instance.results.result[1].get("success", None) is False

    assert True in instance.results.failed
    # Note: False is also in failed because fabric_groups.refresh() succeeded
    assert False in instance.results.changed
    # Note: True is NOT in changed because the failed operation didn't change anything
