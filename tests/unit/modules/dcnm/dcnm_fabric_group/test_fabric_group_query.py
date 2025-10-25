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
Unit tests for FabricGroupQuery class in module_utils/fabric_group/query.py
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
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric_group.utils import (
    MockAnsibleModule,
    does_not_raise,
    fabric_group_query_fixture,
    params_query,
    responses_fabric_group_details,
)


def test_fabric_group_query_00000(fabric_group_query) -> None:
    """
    ### Classes and Methods

    - FabricGroupQuery
        - __init__()

    ### Test
    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_group_query
    assert instance.class_name == "FabricGroupQuery"
    assert instance.action == "fabric_group_query"
    assert instance.fabric_group_details.class_name == "FabricGroupDetails"


def test_fabric_group_query_00020(fabric_group_query) -> None:
    """
    ### Classes and Methods

    - FabricGroupQuery
        - __init__()
        - fabric_group_names setter

    ### Summary
    -   Verify that fabric_group_names is set to expected value when a valid list
        of strings is passed to FabricGroupQuery().fabric_group_names
    -   Exception is not raised.
    """
    with does_not_raise():
        instance = fabric_group_query
        instance.fabric_group_names = ["MFG1", "MFG2"]
    assert instance.fabric_group_names == ["MFG1", "MFG2"]


def test_fabric_group_query_00021(fabric_group_query) -> None:
    """
    ### Classes and Methods

    - FabricGroupQuery
        - __init__()
        - fabric_group_names setter

    ### Summary
    -   Verify ``ValueError`` is raised because fabric_group_names is not a ``list``
    -   Verify ``instance.fabric_group_names`` is not modified, hence it retains its
        initial value of [] (empty list)
    """
    match = r"FabricGroupQuery\.fabric_group_names: "
    match += r"fabric_group_names must be a list\."

    with does_not_raise():
        instance = fabric_group_query
    with pytest.raises(ValueError, match=match):
        instance.fabric_group_names = "NOT_A_LIST"
    assert instance.fabric_group_names == []


def test_fabric_group_query_00022(fabric_group_query) -> None:
    """
    ### Classes and Methods

    - FabricGroupQuery
        - __init__()
        - fabric_group_names setter

    ### Summary
    Verify that ``ValueError`` is raised because fabric_group_names is an empty list.
    """
    with does_not_raise():
        instance = fabric_group_query

    match = r"FabricGroupQuery\.fabric_group_names: "
    match += r"fabric_group_names must be a list of at least one string\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_group_names = []


def test_fabric_group_query_00023(fabric_group_query) -> None:
    """
    ### Classes and Methods

    - FabricGroupQuery
        - __init__()
        - fabric_group_names setter

    ### Summary
    -   Verify that ``ValueError`` is raised because fabric_group_names contains
        non-string values.
    """
    with does_not_raise():
        instance = fabric_group_query

    match = r"FabricGroupQuery\.fabric_group_names: "
    match += r"fabric_group_names must be a list of strings\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_group_names = ["MFG1", 123]
    assert instance.fabric_group_names == []


def test_fabric_group_query_00024(fabric_group_query) -> None:
    """
    ### Classes and Methods

    - FabricGroupQuery
        - __init__()
        - commit()

    ### Summary
    -   Verify ``ValueError`` is raised because fabric_group_names is not set
        prior to calling commit
    -   Verify instance.fabric_group_names retains its initial value of [] (empty list)
    """
    with does_not_raise():
        instance = fabric_group_query
        instance.rest_send = RestSend(params_query)

    match = r"FabricGroupQuery\._validate_commit_parameters: "
    match += r"fabric_group_names must be set before calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()
    assert instance.fabric_group_names == []


def test_fabric_group_query_00025(fabric_group_query) -> None:
    """
    ### Classes and Methods

    - FabricGroupQuery
        - __init__()
        - rest_send setter
        - commit()

    ### Summary
    Verify behavior when attempting to set ``rest_send`` with empty params.

    ### Test
    -   ``ValueError`` is raised when trying to set ``rest_send`` with
        an instance that has empty params (RestSend({})).

    ### Note
    -   The default rest_send (initialized in __init__ as RestSend({}))
        has empty params, so trying to set it explicitly will fail.
    -   The rest_send setter validates that params is not empty.
    """
    with does_not_raise():
        instance = fabric_group_query
        instance.fabric_group_names = ["MFG1"]
        instance.results = Results()

    match = r"FabricGroupQuery\.rest_send must be set to an "
    match += r"instance of RestSend with params set\."

    with pytest.raises(ValueError, match=match):
        instance.rest_send = RestSend({})


def test_fabric_group_query_00026(fabric_group_query) -> None:
    """
    ### Classes and Methods

    - FabricGroupQuery
        - __init__()
        - commit()

    ### Summary
    Verify behavior when ``fabric_group_details`` is set to None prior to calling commit.

    ### Test
    -   ``ValueError`` is raised because ``fabric_group_details`` is set to None prior
        to calling commit.
    """
    with does_not_raise():
        instance = fabric_group_query
        instance.fabric_group_names = ["MFG1"]
        instance.rest_send = RestSend(params_query)
        instance.fabric_group_details = None

    match = r"FabricGroupQuery\._validate_commit_parameters: "
    match += r"fabric_group_details must be set before calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fabric_group_query_00030(fabric_group_query) -> None:
    """
    ### Classes and Methods

    - FabricGroupQuery()
        - __init__()
        - commit()
    - FabricGroupDetails()
        - __init__()
        - refresh()

    ### Summary
    -   Verify behavior when user queries a fabric group that exists on the
        controller and the RestSend() RETURN_CODE is 200.

    ### Code Flow

    -   FabricGroupQuery.fabric_group_names is set to contain one fabric group name
        (MFG1) that exists on the controller.
    -   FabricGroupQuery.commit() calls FabricGroupDetails().refresh()
        which first checks if fabric exists via FabricGroups().refresh(),
        then gets fabric details, returning DATA == [{MFG1 fabric group data dict}],
        RETURN_CODE == 200
    -   FabricGroupQuery.commit() sets results.diff_current to a dict containing
        the fabric group details for MFG1
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # FabricGroups.refresh() - called by FabricGroupDetails to check if fabric exists
        yield responses_fabric_group_details(key)
        # FabricGroupDetails.refresh() - actual fabric details
        yield responses_fabric_group_details(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params_query)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_group_query
        instance.fabric_group_details = FabricGroupDetails()
        instance.fabric_group_details.rest_send = rest_send
        instance.fabric_group_details.results = Results()
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_names = ["MFG1"]
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.metadata) == 1
    assert len(instance.results.response) == 1
    assert len(instance.results.result) == 1

    # Verify MFG1 is in the diff and has the correct data
    assert "MFG1" in instance.results.diff[0]
    assert instance.results.diff[0]["MFG1"].get("nvPairs", {}).get("FABRIC_NAME") == "MFG1"

    assert instance.results.metadata[0].get("action", None) == "fabric_group_query"
    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("state", None) == "query"

    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.response[0].get("METHOD", None) == "GET"

    # Verify result contains found and success
    assert instance.results.result[0].get("found", None) is True
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    # Query operations never set changed to True
    assert True not in instance.results.changed


def test_fabric_group_query_00031(fabric_group_query) -> None:
    """
    Classes and Methods
    - FabricGroupQuery()
        - __init__()
        - commit()
    - FabricGroupDetails()
        - __init__()
        - refresh()

    Summary
    -   Verify behavior when FabricGroupQuery() is used to query multiple
        fabric groups that exist on the controller.

    Setup
    -   FabricGroupDetails().refresh() is set to indicate that fabric groups MFG1
        and MFG2 exist on the controller

    Code Flow
    -   FabricGroupQuery.fabric_group_names is set to contain two fabric group names
        (MFG1 and MFG2) that exist on the controller.
    -   FabricGroupQuery.commit() calls FabricGroupDetails().refresh() twice
        (once for each fabric group), and each refresh() calls FabricGroups().refresh()
        which returns a dict with keys DATA == [{MFG1 fabric group data dict},
        {MFG2 fabric group data dict}], RETURN_CODE == 200
    -   FabricGroupQuery.commit() sets results.diff_current to a dict containing
        the fabric group details for both MFG1 and MFG2

    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # For MFG1:
        # FabricGroups.refresh() - check if MFG1 exists
        yield responses_fabric_group_details(key)
        # FabricGroupDetails.refresh() - get MFG1 details
        yield responses_fabric_group_details(key)
        # For MFG2:
        # FabricGroups.refresh() - check if MFG2 exists
        yield responses_fabric_group_details(key)
        # FabricGroupDetails.refresh() - get MFG2 details
        yield responses_fabric_group_details(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params_query)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_group_query
        instance.fabric_group_details = FabricGroupDetails()
        instance.fabric_group_details.rest_send = rest_send
        instance.fabric_group_details.results = Results()
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_names = ["MFG1", "MFG2"]
        instance.commit()

    assert len(instance.results.diff) == 1
    assert len(instance.results.metadata) == 1
    assert len(instance.results.response) == 1
    assert len(instance.results.result) == 1

    # Verify both fabric groups are in the diff
    assert "MFG1" in instance.results.diff[0]
    assert "MFG2" in instance.results.diff[0]
    assert instance.results.diff[0]["MFG1"].get("nvPairs", {}).get("FABRIC_NAME") == "MFG1"
    assert instance.results.diff[0]["MFG2"].get("nvPairs", {}).get("FABRIC_NAME") == "MFG2"

    # Verify result contains found and success
    assert instance.results.result[0].get("found", None) is True
    assert instance.results.result[0].get("success", None) is True


def test_fabric_group_query_00032(fabric_group_query) -> None:
    """
    Classes and Methods
    - FabricGroupQuery()
        - __init__()
        - commit()
    - FabricGroupDetails()
        - __init__()
        - refresh()

    Summary
    -   Verify behavior when user queries a fabric group that does not exist
        on the controller.

    Setup
    -   FabricGroupDetails().refresh() is set to indicate that no fabric groups
        exist on the controller

    Code Flow
    -   FabricGroupQuery.fabric_group_names is set to contain one fabric group name
        (MFG1) that does not exist on the controller.
    -   FabricGroupQuery.commit() calls FabricGroupDetails().refresh()
        which returns a dict with keys DATA == [], RETURN_CODE == 200
    -   FabricGroupQuery.commit() sets results.diff_current to an empty dict
    -   results.result_current["found"] is set to False
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_group_details(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params_query)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_group_query
        instance.fabric_group_details = FabricGroupDetails()
        instance.fabric_group_details.rest_send = rest_send
        instance.fabric_group_details.results = Results()
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_names = ["MFG1"]
        instance.commit()

    assert len(instance.results.diff) == 1
    assert len(instance.results.metadata) == 1
    assert len(instance.results.response) == 1
    assert len(instance.results.result) == 1

    # Verify diff contains only sequence_number (no fabric group data)
    assert instance.results.diff[0].get("sequence_number", None) == 1
    # Verify no fabric group names are in the diff
    assert "MFG1" not in instance.results.diff[0]

    # Verify found is False
    assert instance.results.result[0].get("found", None) is False
    assert instance.results.result[0].get("success", None) is True
