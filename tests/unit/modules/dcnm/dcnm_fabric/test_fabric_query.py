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
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details_v2 import \
    FabricDetailsByName
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    MockAnsibleModule, does_not_raise, fabric_query_fixture,
    responses_fabric_query)

PARAMS = {"state": "query", "check_mode": False}


def test_fabric_query_00000(fabric_query) -> None:
    """
    ### Classes and Methods

    - FabricCommon
        - __init__()
    - FabricQuery
        - __init__()

    ### Test

    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_query
    assert instance.class_name == "FabricQuery"
    assert instance.action == "fabric_query"
    assert instance.fabric_details is None
    assert instance.fabric_names is None
    assert instance._fabrics_to_query == []


def test_fabric_query_00020(fabric_query) -> None:
    """
    ### Classes and Methods

    - FabricCommon
        - __init__()
    - FabricQuery
        - __init__()
        - fabric_names setter

    ### Summary
    Verify behavior when ``fabric_names`` is set to a list of strings.

    ### Test

    -   ``fabric_names`` is set to expected value.
    -   Exception is not raised.
    """
    fabric_names = ["FOO", "BAR"]
    with does_not_raise():
        instance = fabric_query
        instance.fabric_names = fabric_names
    assert instance.fabric_names == fabric_names


def test_fabric_query_00021(fabric_query) -> None:
    """
    ### Classes and Methods

    - FabricCommon
        - __init__()
    - FabricQuery
        - __init__()
        - fabric_names setter

    ### Summary
    Verify behavior when ``fabric_names`` is set to a non-list.

    ### Test
    -   ``ValueError`` is raised because ``fabric_names`` is not a list.
    -   ``fabric_names`` is not modified, hence it retains its initial value
        of None.
    """
    with does_not_raise():
        instance = fabric_query

    match = r"FabricQuery\.fabric_names: "
    match += r"fabric_names must be a list\."

    with pytest.raises(ValueError, match=match):
        instance.fabric_names = "NOT_A_LIST"

    assert instance.fabric_names is None


def test_fabric_query_00022(fabric_query) -> None:
    """
    ### Classes and Methods

    - FabricCommon
        - __init__()
    - FabricQuery
        - __init__()
        - fabric_names setter

    ### Summary
    Verify behavior when ``fabric_names`` is set to a list with a non-string
    element.

    ### Test

    -   ``ValueError`` is raised because fabric_names is a list with a
        non-string element.
    -   ``fabric_names`` is not modified, hence it retains its initial value
        of None.
    """
    with does_not_raise():
        instance = fabric_query

    match = r"FabricQuery.fabric_names: "
    match += r"fabric_names must be a list of strings."

    with pytest.raises(ValueError, match=match):
        instance.fabric_names = [1, 2, 3]

    assert instance.fabric_names is None


def test_fabric_query_00023(fabric_query) -> None:
    """
    ### Classes and Methods

    - FabricQuery
        - fabric_names setter

    ### Summary
    Verify behavior when ``fabric_names`` is set to an empty list.

    ### Setup

    -   FabricQuery().fabric_names is set to an empty list

    ### Test
    -   ``ValueError`` is raised from ``fabric_names`` setter.
    """
    match = r"FabricQuery\.fabric_names: fabric_names must be a list of "
    match += r"at least one string\."

    with pytest.raises(ValueError, match=match):
        instance = fabric_query
        instance.fabric_names = []


def test_fabric_query_00024(fabric_query) -> None:
    """
    ### Classes and Methods

    - FabricCommon
        - __init__()
    - FabricQuery
        - __init__()
        - commit()
        - _validate_commit_parameters()

    ### Summary
    Verify behavior when ``fabric_details`` is not set before calling commit.

    ### Test
    ``ValueError`` is raised because fabric_details is not set before
    calling commit.
    """
    with does_not_raise():
        instance = fabric_query
        instance.fabric_names = ["f1"]
        instance.rest_send = RestSend(PARAMS)
        instance.results = Results()

    match = r"FabricQuery._validate_commit_parameters:\s+"
    match += r"fabric_details must be set before calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()

    assert instance.fabric_names == ["f1"]


def test_fabric_query_00025(fabric_query) -> None:
    """
    ### Classes and Methods

    - FabricCommon
        - __init__()
    - FabricQuery
        - __init__()
        - commit()
        - _validate_commit_parameters()

    ### Summary
    Verify behavior when ``fabric_names`` is not set before calling commit.

    ### Test

    -   ``ValueError`` is raised because fabric_names is not set before
        calling commit.
    -   ``fabric_names`` is not modified, hence it retains its initial value
        of None.
    """
    with does_not_raise():
        instance = fabric_query
        instance.fabric_details = FabricDetailsByName()
        instance.rest_send = RestSend(PARAMS)
        instance.results = Results()

    match = r"FabricQuery\._validate_commit_parameters:\s+"
    match += r"fabric_names must be set before calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()

    assert instance.fabric_names is None


def test_fabric_query_00026(fabric_query) -> None:
    """
    ### Classes and Methods

    - FabricCommon
        - __init__()
    - FabricQuery
        - __init__()
        - commit()
        - _validate_commit_parameters()

    ### Summary
    Verify behavior when ``rest_send`` is not set before calling commit.

    ### Test

    -   ``ValueError`` is raised because ``rest_send`` is not set before
        calling commit.
    -   ``rest_send`` is not modified, hence it retains its initial value
        of None.
    """
    with does_not_raise():
        instance = fabric_query
        instance.fabric_details = FabricDetailsByName()
        instance.fabric_names = ["f1"]
        instance.results = Results()

    match = r"FabricQuery\._validate_commit_parameters:\s+"
    match += r"rest_send must be set before calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()

    assert instance.rest_send is None


def test_fabric_query_00027(fabric_query) -> None:
    """
    ### Classes and Methods

    - FabricCommon
        - __init__()
    - FabricQuery
        - __init__()
        - commit()
        - _validate_commit_parameters()

    ### Summary
    Verify behavior when ``results`` is not set before calling commit.

    ### Test

    -   ``ValueError`` is raised because ``results`` is not set before
        calling commit.
    -   ``Results()`` is instantiated in ``_validate_commit_parameters``
        in order to register a failed result.
    """
    with does_not_raise():
        instance = fabric_query
        instance.fabric_details = FabricDetailsByName()
        instance.fabric_names = ["f1"]
        instance.rest_send = RestSend(PARAMS)

    match = r"FabricQuery\._validate_commit_parameters:\s+"
    match += r"results must be set before calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()

    assert instance.results.class_name == "Results"


def test_fabric_query_00030(fabric_query) -> None:
    """
    ### Classes and Methods

    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByName()
        - __init__()
        - refresh()
    - FabricQuery
        - __init__()
        - fabric_names setter
        - commit()
    - Query()
        - __init__()
        - commit()

    ### Summary
    Verify behavior when user queries a fabric and no fabrics exist
    on the controller and the RestSend() RETURN_CODE is 200.

    ### Code Flow

    -   main.Query() is instantiated and instantiates FabricQuery()
    -   FabricQuery() instantiates FabricDetailsByName()
    -   FabricQuery.fabric_names is set to contain one fabric_name (f1)
        that does not exist on the controller.
    -   FabricQuery().commit() calls FabricDetailsByName().refresh() which
        calls FabricDetails.refresh_super()
    -   FabricDetails.refresh_super() calls RestSend().commit() which sets
        RestSend().response_current to a dict with keys DATA == [],
        RETURN_CODE == 200, MESSAGE="OK"
    -   Hence, FabricDetails().data is set to an empty dict: {}
    -   Hence, FabricDetailsByName().data_subclass is set to an empty dict: {}
    -   Since FabricDetails().all_data is an empty dict, FabricQuery().commit() sets:
        -   instance.results.diff_current to an empty dict
        -   instance.results.response_current to the RestSend().response_current
        -   instance.results.result_current to the RestSend().result_current
    -   FabricQuery.commit() calls Results().register_task_result()
    -   Results().register_task_result() adds sequence_number (with value 1) to
        each of the results dicts
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_query(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(PARAMS)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_query
        instance.fabric_details = FabricDetailsByName()
        instance.fabric_details.rest_send = rest_send
        instance.fabric_details.results = Results()
        instance.fabric_names = ["f1"]
        instance.rest_send = rest_send
        instance.results = Results()
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.result) == 1
    assert len(instance.results.response) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.result[0].get("found", None) is True
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_fabric_query_00031(fabric_query) -> None:
    """
    ### Classes and Methods

    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByName()
        - __init__()
        - refresh()
    - FabricQuery
        - __init__()
        - fabric_names setter
        - commit()
    - Query()
        - __init__()
        - commit()

    ### Summary
    Verify behavior when user queries a fabric that does not exist
    on the controller.  One fabric (f2) exists on the controller,
    and the RestSend() RETURN_CODE is 200.

    ### Code Flow

    -   main.Query() is instantiated and instantiates FabricQuery()
    -   FabricQuery() instantiates FabricDetailsByName()
    -   FabricQuery.fabric_names is set to contain one fabric_name (f1)
        that does not exist on the controller.
    -   FabricQuery().commit() calls FabricDetailsByName().refresh() which
        calls FabricDetails.refresh_super()
    -   FabricDetails.refresh_super() calls RestSend().commit() which sets
        RestSend().response_current to a dict with keys DATA == [{f2 fabric data dict}],
        RETURN_CODE == 200, MESSAGE="OK"
    -   Hence, FabricDetails().data is set to: { "f2": {f2 fabric data dict} }
    -   Hence, FabricDetailsByName().data_subclass is set to: { "f2": {f2 fabric data dict} }
    -   Since FabricDetails.all_data is not an empty dict, FabricQuery().commit() iterates
        over the fabrics in FabricDetails.all_data but does not find any fabrics matching
        the user query.  Hence, it sets:
        -   instance.results.diff_current to an empty dict
        -   instance.results.response_current to the RestSend().response_current
        -   instance.results.result_current to the RestSend().result_current
    -   FabricQuery.commit() calls Results().register_task_result()
    -   Results().register_task_result() adds sequence_number (with value 1) to
        each of the results dicts

    ### Test

    -   FabricQuery.commit() calls instance.fabric_details() which sets
        instance.fabric_details.all_data to a list of dict containing
        all fabrics on the controller.
    -   since instance.fabric_details.all_data is empty, none of the
        following are set:
        - instance.results.diff_current
        - instance.results.response_current
        - instance.results.result_current
    -   instance.results.changed set() contains False
    -   instance.results.failed set() contains False
    -   commit() returns without doing anything else
    -   Exception is not raised
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_query(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(PARAMS)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_query
        instance.fabric_details = FabricDetailsByName()
        instance.fabric_details.rest_send = rest_send
        instance.fabric_details.results = Results()
        instance.fabric_names = ["f1"]
        instance.rest_send = rest_send
        instance.results = Results()
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.result) == 1
    assert len(instance.results.response) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.result[0].get("found", None) is True
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_fabric_query_00032(fabric_query) -> None:
    """
    ### Classes and Methods

    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByName()
        - __init__()
        - refresh()
    - FabricQuery
        - __init__()
        - fabric_names setter
        - commit()
    - Query()
        - __init__()
        - commit()

    ### Summary
    Verify behavior when user queries a fabric that does not exist
    on the controller.  One fabric (f2) exists on the controller,
    but the RestSend() RETURN_CODE is 500.

    ### Code Flow

    -   main.Query() is instantiated and instantiates FabricQuery()
    -   FabricQuery() instantiates FabricDetailsByName()
    -   FabricQuery.fabric_names is set to contain one fabric_name (f1)
        that does not exist on the controller.
    -   FabricQuery().commit() calls FabricDetailsByName().refresh() which
        calls FabricDetails.refresh_super()
    -   FabricDetails.refresh_super() calls RestSend().commit() which sets
        RestSend().response_current to a dict with keys DATA == [{f2 fabric data dict}],
        RETURN_CODE == 200, MESSAGE="OK"
    -   Hence, FabricDetails().data is set to: { "f2": {f2 fabric data dict} }
    -   Hence, FabricDetailsByName().data_subclass is set to: { "f2": {f2 fabric data dict} }
    -   Since FabricDetails.all_data is not an empty dict, FabricQuery().commit() iterates
        over the fabrics in FabricDetails.all_data but does not find any fabrics matching
        the user query.  Hence, it sets:
        -   instance.results.diff_current to an empty dict
        -   instance.results.response_current to the RestSend().response_current
        -   instance.results.result_current to the RestSend().result_current
    -   FabricQuery.commit() calls Results().register_task_result()
    -   Results().register_task_result() adds sequence_number (with value 1) to
        each of the results dicts

    ### Setup

    -   RestSend().commit() response is mocked to return a dict with key
        RETURN_CODE == 500
    -   RestSend().timeout is set to 1
    -   RestSend().unit_test is set to True

    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_query(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(PARAMS)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_query
        instance.fabric_details = FabricDetailsByName()
        instance.fabric_details.rest_send = rest_send
        instance.fabric_details.results = Results()
        instance.fabric_names = ["f1"]
        instance.rest_send = rest_send
        instance.results = Results()
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.result) == 1
    assert len(instance.results.response) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.response[0].get("RETURN_CODE", None) == 500
    assert instance.results.result[0].get("found", None) is False
    assert instance.results.result[0].get("success", None) is False

    assert True in instance.results.failed
    assert False not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_fabric_query_00033(fabric_query) -> None:
    """
    ### Classes and Methods

    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByName()
        - __init__()
        - refresh()
    - FabricQuery
        - __init__()
        - fabric_names setter
        - commit()
    - Query()
        - __init__()
        - commit()

    ### Summary
    Verify behavior when user queries a fabric that exists
    on the controller.  One fabric (f1) exists on the controller,
    and the RestSend() RETURN_CODE is 200.

    ### Code Flow

    -   main.Query() is instantiated and instantiates FabricQuery()
    -   FabricQuery() instantiates FabricDetailsByName()
    -   FabricQuery.fabric_names is set to contain one fabric_name (f1)
        that does not exist on the controller.
    -   FabricQuery().commit() calls FabricDetailsByName().refresh() which
        calls FabricDetails.refresh_super()
    -   FabricDetails.refresh_super() calls RestSend().commit() which sets
        RestSend().response_current to a dict with keys DATA == [{f1 fabric data dict}],
        RETURN_CODE == 200, MESSAGE="OK"
    -   Hence, FabricDetails().data is set to: { "f1": {f1 fabric data dict} }
    -   Hence, FabricDetailsByName().data_subclass is set to: { "f1": {f1 fabric data dict} }
    -   Since FabricDetails.all_data is not an empty dict, FabricQuery().commit() iterates
        over the fabrics in FabricDetails.all_data and finds fabric f1.
        Hence, it sets:
        -   instance.results.diff_current to be the fabric info dict for fabric f1
        -   instance.results.response_current to the RestSend().response_current
        -   instance.results.result_current to the RestSend().result_current
    -   FabricQuery.commit() calls Results().register_task_result()
    -   Results().register_task_result() adds sequence_number (with value 1) to
        each of the results dicts
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_query(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(PARAMS)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_query
        instance.fabric_details = FabricDetailsByName()
        instance.fabric_details.rest_send = rest_send
        instance.fabric_details.results = Results()
        instance.fabric_names = ["f1"]
        instance.rest_send = rest_send
        instance.results = Results()
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.result) == 1
    assert len(instance.results.response) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.diff[0].get("f1", {}).get("asn", None) == "65001"
    assert (
        instance.results.diff[0].get("f1", {}).get("nvPairs", {}).get("BGP_AS")
        == "65001"
    )

    assert instance.results.response[0].get("RETURN_CODE", None) == 200

    assert instance.results.result[0].get("found", None) is True
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed
