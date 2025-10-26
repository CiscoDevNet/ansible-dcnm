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
Unit tests for FabricGroupDelete class in module_utils/fabric_group/delete.py
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
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric_group.fabric_group_details import FabricGroupDetails
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric_group.fabric_group_member_info import FabricGroupMemberInfo
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric_group.utils import (
    MockAnsibleModule,
    does_not_raise,
    fabric_group_delete_fixture,
    params_delete,
    responses_fabric_group_delete,
    responses_fabric_group_details,
    responses_fabric_group_member_info,
)


def test_fabric_group_delete_00000(fabric_group_delete) -> None:
    """
    ### Classes and Methods

    - FabricGroupDelete
        - __init__()

    ### Test
    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_group_delete
    assert instance.class_name == "FabricGroupDelete"
    assert instance.action == "fabric_group_delete"
    assert instance.fabric_group_details.class_name == "FabricGroupDetails"
    assert instance._fabric_group_member_info.class_name == "FabricGroupMemberInfo"


def test_fabric_group_delete_00020(fabric_group_delete) -> None:
    """
    ### Classes and Methods

    - FabricGroupDelete
        - __init__()
        - fabric_group_names setter

    ### Summary
    -   Verify that fabric_group_names is set to expected value when a valid list
        of strings is passed to FabricGroupDelete().fabric_group_names
    -   Exception is not raised.
    """
    with does_not_raise():
        instance = fabric_group_delete
        instance.fabric_group_names = ["MFG1", "MFG2"]
    assert instance.fabric_group_names == ["MFG1", "MFG2"]


def test_fabric_group_delete_00021(fabric_group_delete) -> None:
    """
    ### Classes and Methods

    - FabricGroupDelete
        - __init__()
        - fabric_group_names setter

    ### Summary
    -   Verify ``ValueError`` is raised because fabric_group_names is not a ``list``
    -   Verify ``instance.fabric_group_names`` is not modified, hence it retains its
        initial value of [] (empty list)
    """
    match = r"FabricGroupDelete\.fabric_group_names: "
    match += r"fabric_group_names must be a list\."

    with does_not_raise():
        instance = fabric_group_delete
    with pytest.raises(ValueError, match=match):
        instance.fabric_group_names = "NOT_A_LIST"
    assert instance.fabric_group_names == []


def test_fabric_group_delete_00022(fabric_group_delete) -> None:
    """
    ### Classes and Methods

    - FabricGroupDelete
        - __init__()
        - fabric_group_names setter

    ### Summary
    Verify that ``ValueError`` is raised because fabric_group_names is an empty list.
    """
    with does_not_raise():
        instance = fabric_group_delete

    match = r"FabricGroupDelete\.fabric_group_names: "
    match += r"fabric_group_names must be a list of at least one string\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_group_names = []


def test_fabric_group_delete_00023(fabric_group_delete) -> None:
    """
    ### Classes and Methods

    - FabricGroupDelete
        - __init__()
        - fabric_group_names setter

    ### Summary
    -   Verify that ``ValueError`` is raised because fabric_group_names contains
        non-string values.
    """
    with does_not_raise():
        instance = fabric_group_delete

    match = r"FabricGroupDelete\.fabric_group_names: "
    match += r"fabric_group_names must be a list of strings\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_group_names = ["MFG1", 123]
    assert instance.fabric_group_names == []


def test_fabric_group_delete_00024(fabric_group_delete) -> None:
    """
    ### Classes and Methods

    - FabricGroupDelete
        - __init__()
        - commit()

    ### Summary
    -   Verify ``ValueError`` is raised because fabric_group_names is not set
        prior to calling commit
    -   Verify instance.fabric_group_names retains its initial value of [] (empty list)
    """
    with does_not_raise():
        instance = fabric_group_delete
        instance.rest_send = RestSend(params_delete)
        instance.results = Results()

    match = r"FabricGroupDelete\._validate_commit_parameters: "
    match += r"fabric_group_names must be set prior to calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()
    assert instance.fabric_group_names == []


def test_fabric_group_delete_00025(fabric_group_delete) -> None:
    """
    ### Classes and Methods

    - FabricGroupDelete
        - __init__()
        - commit()
        - register_result()

    ### Summary
    Verify behavior when attempting to call commit with fabric_group_names but
    rest_send.params is empty.

    ### Test
    -   ``ValueError`` is raised because rest_send.params is empty
    -   The error is caught and results are registered before re-raising
    -   register_result() properly handles rest_send.state being None by
        defaulting to "deleted"

    ### Note
    -   This test validates the fix in delete.py lines 280-287 where
        check_mode and state are now properly checked and defaulted if None.
    """
    with does_not_raise():
        instance = fabric_group_delete
        instance.fabric_group_names = ["MFG1"]
        instance.results = Results()
        # Set rest_send with empty params - this will trigger validation error
        instance.rest_send = RestSend({})

    match = r"FabricGroupDelete\._validate_commit_parameters: "
    match += r"rest_send\.params must be set prior to calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()

    # Verify that results were registered even though the commit failed
    assert len(instance.results.result) == 1
    assert instance.results.result[0].get("success") is False
    assert instance.results.result[0].get("changed") is False
    # Verify that state was defaulted to "deleted"
    assert instance.results.metadata[0].get("state") == "deleted"


def test_fabric_group_delete_00030(fabric_group_delete) -> None:
    """
    ### Classes and Methods

    - FabricGroupDelete()
        - __init__()
        - commit()
    - FabricGroupDetails()
        - __init__()
        - refresh()
    - FabricGroupMemberInfo()
        - __init__()
        - refresh()

    ### Summary
    -   Verify behavior when user deletes a fabric group that exists on the
        controller and has no members (successful delete).

    ### Code Flow

    -   FabricGroupDelete.fabric_group_names is set to contain one fabric group name
        (MFG1) that exists on the controller.
    -   FabricGroupDelete.commit() calls FabricGroupDetails().refresh()
        which returns fabric group info
    -   FabricGroupDelete.commit() calls FabricGroupMemberInfo().refresh()
        which returns that the fabric group has no members
    -   FabricGroupDelete.commit() sends DELETE request
    -   Controller returns RETURN_CODE 200
    """
    method_name = inspect.stack()[0][3]
    key_members = f"{method_name}a"
    key_delete = f"{method_name}b"

    def responses():
        # FabricGroups.refresh() - called by FabricGroupDetails to check if fabric exists
        yield responses_fabric_group_details("test_fabric_group_query_00030a")
        # FabricGroupDetails.refresh()
        yield responses_fabric_group_details("test_fabric_group_query_00030a")
        # FabricGroupMemberInfo.refresh()
        yield responses_fabric_group_member_info(key_members)
        # DELETE request
        yield responses_fabric_group_delete(key_delete)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params_delete)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_group_delete
        instance.fabric_group_details = FabricGroupDetails()
        instance.fabric_group_details.rest_send = rest_send
        instance.fabric_group_details.results = Results()
        instance._fabric_group_member_info = FabricGroupMemberInfo()
        instance._fabric_group_member_info.rest_send = rest_send
        instance._fabric_group_member_info.results = Results()
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_names = ["MFG1"]
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    # There will be 3 results:
    # 1. FabricGroupDetails.refresh()
    # 2. FabricGroupMemberInfo.refresh()
    # 3. DELETE request
    assert len(instance.results.diff) == 3
    assert len(instance.results.metadata) == 3
    assert len(instance.results.response) == 3
    assert len(instance.results.result) == 3

    # Verify the fabric was deleted (last result)
    assert instance.results.diff[2].get("fabric_group_name") == "MFG1"

    assert instance.results.metadata[2].get("action", None) == "fabric_group_delete"
    assert instance.results.metadata[2].get("check_mode", None) is False
    assert instance.results.metadata[2].get("sequence_number", None) == 3
    assert instance.results.metadata[2].get("state", None) == "deleted"

    assert instance.results.response[2].get("RETURN_CODE", None) == 200
    assert instance.results.response[2].get("METHOD", None) == "DELETE"

    # Delete operations change the controller state
    assert instance.results.result[2].get("changed", None) is True
    assert instance.results.result[2].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    # The final result shows changed=True
    assert True in instance.results.changed
    # Query operations add False to instance.results.changed
    # The DELETE operation adds True to instance.results.changed
    # Hence both are present in instance.results.changed
    assert False in instance.results.changed


def test_fabric_group_delete_00031(fabric_group_delete) -> None:
    """
    ### Classes and Methods

    - FabricGroupDelete()
        - __init__()
        - commit()
    - FabricGroupDetails()
        - __init__()
        - refresh()
    - FabricGroupMemberInfo()
        - __init__()
        - refresh()

    ### Summary
    -   Verify behavior when user attempts to delete a fabric group that has members.

    ### Code Flow

    -   FabricGroupDelete.fabric_group_names is set to contain one fabric group name
        (MFG1) that exists on the controller but has members.
    -   FabricGroupDelete.commit() calls FabricGroupDetails().refresh()
        which first checks if fabric exists via FabricGroups().refresh(),
        then returns fabric group info
    -   FabricGroupDelete.commit() calls FabricGroupMemberInfo().refresh()
        which returns that the fabric group has 1 member
    -   FabricGroupDelete._verify_fabric_group_can_be_deleted() raises ValueError
    -   No DELETE request is sent
    """
    method_name = inspect.stack()[0][3]
    key_members = f"{method_name}a"

    def responses():
        # FabricGroups.refresh() - called by FabricGroupDetails to check if fabric exists
        yield responses_fabric_group_details("test_fabric_group_query_00030a")
        # FabricGroupDetails.refresh()
        yield responses_fabric_group_details("test_fabric_group_query_00030a")
        # FabricGroupMemberInfo.refresh()
        yield responses_fabric_group_member_info(key_members)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params_delete)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_group_delete
        instance.fabric_group_details = FabricGroupDetails()
        instance.fabric_group_details.rest_send = rest_send
        instance.fabric_group_details.results = Results()
        instance._fabric_group_member_info = FabricGroupMemberInfo()
        instance._fabric_group_member_info.rest_send = rest_send
        instance._fabric_group_member_info.results = Results()
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_names = ["MFG1"]

    match = r"Fabric group MFG1.*cannot be deleted since it contains.*members"

    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fabric_group_delete_00032(fabric_group_delete) -> None:
    """
    ### Classes and Methods

    - FabricGroupDelete()
        - __init__()
        - commit()
    - FabricGroupDetails()
        - __init__()
        - refresh()

    ### Summary
    -   Verify behavior when user attempts to delete a fabric group that does not
        exist on the controller.

    ### Code Flow

    -   FabricGroupDelete.fabric_group_names is set to contain one fabric group name
        (MFG1) that does not exist on the controller.
    -   FabricGroupDelete.commit() calls FabricGroupDetails().refresh()
        which first calls FabricGroups().refresh() and discovers the fabric
        does not exist, so it returns early with empty data (no second API call)
    -   No DELETE request is sent
    -   Results indicate no changes made
    """

    def responses():
        # FabricGroups.refresh() - returns empty list (no fabric groups)
        yield responses_fabric_group_details("test_fabric_group_query_00032a")
        # No second response needed - FabricGroupDetails.refresh() returns early

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params_delete)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_group_delete
        instance.fabric_group_details = FabricGroupDetails()
        instance.fabric_group_details.rest_send = rest_send
        instance.fabric_group_details.results = Results()
        instance._fabric_group_member_info = FabricGroupMemberInfo()
        instance._fabric_group_member_info.rest_send = rest_send
        instance._fabric_group_member_info.results = Results()
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_names = ["MFG1"]
        instance.commit()

    # There will be 1 result:
    # FabricGroupDelete final result (no fabrics to delete)
    # Note: FabricGroupDetails.refresh() returns early WITHOUT registering a result
    # when the fabric doesn't exist (it only sets self.data = {} and returns)
    assert len(instance.results.diff) == 1
    assert len(instance.results.metadata) == 1
    assert len(instance.results.response) == 1
    assert len(instance.results.result) == 1

    # Verify no changes were made (fabric didn't exist)
    assert instance.results.result[0].get("changed", None) is False
    assert instance.results.result[0].get("success", None) is True
    assert instance.results.response[0].get("MESSAGE", None) == "No fabric groups to delete"

    # No failures occurred
    assert False in instance.results.failed
    assert True not in instance.results.failed
    # No changes made since fabric didn't exist
    assert False in instance.results.changed
    assert True not in instance.results.changed
