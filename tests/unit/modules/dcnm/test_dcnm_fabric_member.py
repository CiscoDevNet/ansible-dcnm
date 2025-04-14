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

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2025 Cisco and/or its affiliates."
__author__ = "Prabahal"

import inspect
import pytest
import os
import json
import sys

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
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    MockAnsibleModule, does_not_raise)

from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.fixture import \
    load_fixture

from ansible_collections.cisco.dcnm.plugins.module_utils.msd.add_child_fab import childFabricAdd
from ansible_collections.cisco.dcnm.plugins.module_utils.msd.delete_child_fab import childFabricDelete

from ansible_collections.cisco.dcnm.plugins.module_utils.msd.query_child_fab import childFabricQuery
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_fabric_member import Query
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_fabric_member import Deleted
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_fabric_member import Merged


params = {'state': 'query', "check_mode": False}


# Fixtures path
fixture_path = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture(name="child_fabric_query")
def fabric_member_query_fixture():
    """
    Return childFabricQuery() instance.
    """
    return childFabricQuery()


@pytest.fixture(name="child_fabric_delete")
def fabric_member_delete_fixture():
    """
    Return childFabricDelete() instance.
    """
    return childFabricDelete()


@pytest.fixture(name="child_fabric_add")
def fabric_member_add_fixture():
    """
    Return childFabricAdd() instance.
    """
    return childFabricAdd()


def load_fixture(filename):
    """
    load test inputs from json files
    """
    path = os.path.join(fixture_path, f"{filename}.json")

    try:
        with open(path, encoding="utf-8") as file_handle:
            data = file_handle.read()
    except IOError as exception:
        msg = f"Exception opening test input file {filename}.json : "
        msg += f"Exception detail: {exception}"
        print(msg)
        sys.exit(1)

    try:
        fixture = json.loads(data)
    except json.JSONDecodeError as exception:
        msg = "Exception reading JSON contents in "
        msg += f"test input file {filename}.json : "
        msg += f"Exception detail: {exception}"
        print(msg)
        sys.exit(1)

    return fixture


@pytest.fixture
def mock_params():
    return {
        'check_mode': True,
        'config': [{'FABRIC_NAME': 'fabric1', 'CHILD_FABRIC_NAME': 'child1'}],
        'state': 'merged'
    }


def fabric_member_data(key: str) -> dict[str, str]:
    """
    Return data from test_child_fabric.json for unit tests.
    """
    data_file = "test_fabric_member"
    data = load_fixture(data_file).get(key)
    print(f"fabric member mock data : {key} : {data}")
    return data


def test_fab_mem_query_init_00001():
    query_instance = Query(params)
    assert query_instance.class_name == 'Query'
    assert query_instance.action == 'child_fabric_query'
    assert 'query' in query_instance._implemented_states


def test_fab_mem_query_verify_payload_none_config_00002():
    query_instance = Query(params)
    with pytest.raises(ValueError) as excinfo:
        query_instance.verify_payload()
    assert "Playbook configuration for FABRIC_NAME is missing" in str(excinfo.value)


@pytest.mark.parametrize(
    "invalid_fabric_name",
    ["@123", "", "$abd#", "-!`", "%^&", None],
)
def test_fab_mem_query_verify_payload_invalid_fabric_name_00003(invalid_fabric_name):
    t_params = {'config': [{'FABRIC_NAME': {invalid_fabric_name}}]}
    t_params.update(params)
    query_instance = Query(t_params)
    with pytest.raises(ValueError) as excinfo:
        query_instance.verify_payload()
    assert "contains an invalid FABRIC_NAME" in str(excinfo.value)


def test_fab_mem_query_verify_payload_invalid_config_00004():
    t_params = {'config': None}
    t_params.update(params)
    query_instance = Query(t_params)
    with pytest.raises(ValueError) as excinfo:
        query_instance.verify_payload()
    assert "Playbook configuration for FABRIC_NAME is missing" in str(excinfo.value)


def test_fab_mem_query_verify_payload_invalid_config_00005():
    t_params = {'config': [{'FABRIC_NAME': ''}]}
    t_params.update(params)
    query_instance = Query(t_params)
    with pytest.raises(ValueError) as excinfo:
        query_instance.verify_payload()
    assert "Playbook configuration for FABRIC_NAME is missing" in str(excinfo.value)


def test_fab_mem_query_commit_verify_payload_failure_00006():
    t_params = {
        'config': None,  # This will cause verify_payload to raise an error
    }
    t_params.update(params)
    query_instance = Query(t_params)
    query_instance.rest_send = RestSend(t_params)
    with pytest.raises(ValueError) as excinfo:
        query_instance.commit()
    assert "Playbook configuration for FABRIC_NAME is missing" in str(excinfo.value)


def test_fab_mem_query_00007(child_fabric_query) -> None:
    """
    ### Classes and Methods
    - childFabricQuery
        - __init__()

    ### Test

    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = child_fabric_query
    assert instance.class_name == "childFabricQuery"
    assert instance.action == "child_fabric_query"
    assert instance.fabric_names is None


def test_fab_mem_query_00008(child_fabric_query) -> None:
    """
    ### Classes and Methods

    - childFabricQuery
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
        instance = child_fabric_query
        instance.fabric_names = fabric_names
    assert instance.fabric_names == fabric_names


def test_fab_mem_query_00009(child_fabric_query) -> None:
    """
    ### Classes and Methods

    - childFabricQuery
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
        instance = child_fabric_query

    match = r"FabricQuery\.fabric_names: "
    match += r"fabric_names must be a list\."

    with pytest.raises(ValueError, match=match):
        instance.fabric_names = "NOT_A_LIST"

    assert instance.fabric_names is None


def test_fab_mem_query_00010(child_fabric_query) -> None:
    """
    ### Classes and Methods

    - childFabricQuery
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
        instance = child_fabric_query

    match = r"FabricQuery.fabric_names: "
    match += r"fabric_names must be a list of strings."

    with pytest.raises(ValueError, match=match):
        instance.fabric_names = [1, 2, 3]

    assert instance.fabric_names is None


def test_fab_mem_query_00011(child_fabric_query) -> None:
    """
    ### Classes and Methods

    - childFabricQuery
        - fabric_names setter

    ### Summary
    Verify behavior when ``fabric_names`` is set to an empty list.

    ### Setup

    -   childFabricQuery().fabric_names is set to an empty list

    ### Test
    -   ``ValueError`` is raised from ``fabric_names`` setter.
    """
    match = r"FabricQuery\.fabric_names: fabric_names must be a list of "
    match += r"at least one string\."

    with pytest.raises(ValueError, match=match):
        instance = child_fabric_query
        instance.fabric_names = []


def test_fab_mem_query_00012(child_fabric_query) -> None:
    """
    ### Classes and Methods

    - childFabricQuery
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
        instance = child_fabric_query
        instance.rest_send = RestSend(params)
        instance.results = Results()

    match = r"FabricQuery\._validate_commit_parameters:\s+"
    match += r"fabric_names must be set before calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()

    assert instance.fabric_names is None


def test_fab_mem_query_00013(child_fabric_query) -> None:
    """
    ### Classes and Methods

    - childFabricQuery
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
        instance = child_fabric_query
        instance.fabric_names = ["f1"]
        instance.results = Results()

    match = r"FabricQuery\._validate_commit_parameters:\s+"
    match += r"rest_send must be set before calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()

    assert instance.rest_send is None


def test_fab_mem_query_00014(child_fabric_query) -> None:
    """
    ### Classes and Methods

    - childFabricQuery
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
        instance = child_fabric_query
        instance.fabric_names = ["f1"]
        instance.rest_send = RestSend(params)
        instance.results = None

    match = r"FabricQuery\._validate_commit_parameters:\s+"
    match += r"results must be set before calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()

    assert instance.results.class_name == "Results"


def test_fab_mem_query_00015(child_fabric_query) -> None:
    """
    ### Classes and Methods

    - childFabricQuery
        - __init__()
        - fabric_names setter
        - commit()
    - Query()
        - __init__()
        - commit()

    ### Summary
    Verify behavior when user queries child fabric of a MSD fabric and no fabrics exist
    on the controller and the RestSend() RETURN_CODE is 200 and data is empty.

    ### Code Flow

    -   main.Query() is instantiated and instantiates childFabricQuery()
    -   FabricQuery.fabric_names is set to contain one fabric_name (f1)
        that does not exist on the controller.
    -   FabricAssociations.refresh() calls RestSend().commit() which sets
        RestSend().response_current to a dict with keys DATA == [],
        RETURN_CODE == 200, MESSAGE="OK"
    -   Hence, FabricAssociation().data is set to an empty dict: {}
    -   Results().register_task_result() adds sequence_number (with value 1) to
        each of the results dicts
    -   since instance.fab_associations is empty, none of the
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
    key = "Fabric_association_get_data_empty"

    def responses():
        yield fabric_member_data(key)

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
        instance = child_fabric_query
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
    assert len(instance.results.diff[0].get("child", {})) == 0
    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.result[0].get("found", None) is False
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_fab_mem_query_00016(child_fabric_query) -> None:
    """
    ### Classes and Methods
    - childFabricQuery
        - __init__()
        - fabric_names setter
        - commit()
    - Query()
        - __init__()
        - commit()

    ### Summary
    Verify behavior when user queries child fabric of a MSD, child fabrics are not existing
    on the controller. Some other fabric exists on the controller,
    and the RestSend() RETURN_CODE is 200.

    ### Code Flow

    -   main.Query() is instantiated and instantiates childFabricQuery()
    -   childFabricQuery.fabric_names is set to contain one fabric_name (f1)
        that does not exist on the controller.
    -   FabricAssociations.refresh() calls RestSend().commit() which sets
        RestSend().response_current to a dict with keys DATA == [{other fabric}],
        RETURN_CODE == 200, MESSAGE="OK"
    -   Hence, FabricAssociation().data is set to an empty dict: {}
    -   Results().register_task_result() adds sequence_number (with value 1) to
        each of the results dicts

    ### Test

    -   since instance.fab_associations is not empty, none of the
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
    key = "Fabric_association_get_response"

    def responses():
        yield fabric_member_data(key)

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
        instance = child_fabric_query
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
    assert len(instance.results.diff[0].get("child", {})) == 0
    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.result[0].get("found", None) is False
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_fab_mem_query_00017(child_fabric_query) -> None:
    """
    ## Need to Re-visit this Case whether error "RETURN_CODE" is 500 or valueerror is ok
    ### Classes and Methods

    - childFabricQuery
        - __init__()
        - fabric_names setter
        - commit()
    - Query()
        - __init__()
        - commit()

    ### Summary
    Verify behavior when user queries child fabric that does not exist
    on the controller.  One fabric (f2) exists on the controller,
    but the RestSend() RETURN_CODE is 500 for fabric associations.

    ### Setup

    -   RestSend().commit() response is mocked to return a dict with key
        RETURN_CODE == 500
    -   RestSend().timeout is set to 1
    -   RestSend().unit_test is set to True

    """
    method_name = inspect.stack()[0][3]
    key = "childFabric_nok_get_response"

    def responses():
        yield fabric_member_data(key)

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
        instance = child_fabric_query
        instance.fabric_names = ["f1"]
        instance.rest_send = rest_send
        instance.results = Results()
    match = "Fabric Association response from NDFC controller returns failure"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fab_mem_query_00018(child_fabric_query) -> None:
    """
    ### Classes and Methods

    - childFabricQuery
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

    """
    method_name = inspect.stack()[0][3]
    key = "Fabric_association_get_response_exists"

    def responses():
        yield fabric_member_data(key)

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
        instance = child_fabric_query
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
    assert instance.results.diff[0].get("child", {}).get("fabricName", None) == "child"
    assert instance.results.diff[0].get("child", {}).get("fabricParent", None) == "f1"
    assert instance.results.diff[0].get("child", {}).get("fabricState", None) == "member"
    assert instance.results.response[0].get("RETURN_CODE", None) == 200

    assert instance.results.result[0].get("found", None) is True
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_fab_mem_query_00019(child_fabric_query) -> None:
    """
    ### Classes and Methods
    - childFabricQuery
        - __init__()
        - fabric_names setter
        - commit()
    - Query()
        - __init__()
        - commit()

    ### Summary
    Verify behavior when user queries child fabric of a MSD, child fabrics are not existing
    on the controller. MSD exists on the controller
    and the RestSend() RETURN_CODE is 200.

    ### Test

    -   since instance.fab_associations is not empty, none of the
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
    key = "Fabric_association_get_response_00019"

    def responses():
        yield fabric_member_data(key)

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
        instance = child_fabric_query
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
    assert len(instance.results.diff[0].get("child", {})) == 0
    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.result[0].get("found", None) is False
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


del_params = {'state': 'deleted', 'check_mode': False}


def test_fab_mem_delete_init_00020():
    t_params = {'config': [{'FABRIC_NAME': 'valid_fabric'}, {'CHILD_FABRIC_NAME': 'child_fabric'}]}
    t_params.update(del_params)
    deleted_instance = Deleted(t_params)
    assert deleted_instance.class_name == 'Deleted'
    assert deleted_instance.action == 'child_fabric_delete'
    assert 'deleted' in deleted_instance._implemented_states


@pytest.mark.parametrize(
    "invalid_fabric_name",
    ["@123", "", "$abd#", "-!`", "%^&", None],
)
def test_fab_mem_delete_invalid_msd_fabric_name_00021(invalid_fabric_name):
    t_params = {'config': [{'FABRIC_NAME': {invalid_fabric_name}, 'CHILD_FABRIC_NAME': "abc"}]}
    t_params.update(params)
    delete_instance = Deleted(t_params)
    with pytest.raises(ValueError) as excinfo:
        delete_instance.commit()
    assert "contains an invalid FABRIC_NAME" in str(excinfo.value)


@pytest.mark.parametrize(
    "invalid_fabric_name",
    ["@123", "", "$abd#", "-!`", "%^&", None],
)
def test_fab_mem_delete_invalid_child_fabric_name_00022(invalid_fabric_name):
    t_params = {'config': [{'FABRIC_NAME': "abc", 'CHILD_FABRIC_NAME': {invalid_fabric_name}}]}
    t_params.update(params)
    delete_instance = Deleted(t_params)
    with pytest.raises(ValueError) as excinfo:
        delete_instance.commit()
    assert "Playbook configuration for FABRIC_NAME or CHILD_FABRIC_NAME contains an invalid FABRIC_NAME" in str(excinfo.value)


def test_fab_mem_delete_invalid_config_00023():
    t_params = {'config': None}
    t_params.update(params)
    delete_instance = Deleted(t_params)
    with pytest.raises(ValueError) as excinfo:
        delete_instance.commit()
    assert "params is missing config parameter" in str(excinfo.value)


def test_fab_mem_delete_invalid_config_00024():
    t_params = {'config': [{'FABRIC_NAME': ''}]}
    t_params.update(params)
    delete_instance = Deleted(t_params)
    with pytest.raises(ValueError) as excinfo:
        delete_instance.commit()
    assert "CHILD_FABRIC_NAME : Required parameter not found" in str(excinfo.value)


def test_fab_mem_delete_invalid_config_00025():
    t_params = {'config': [{'FABRIC_NAME': 123, 'CHILD_FABRIC_NAME': True}]}
    t_params.update(params)
    delete_instance = Deleted(t_params)
    with pytest.raises(ValueError) as excinfo:
        delete_instance.commit()
    assert "Playbook configuration for FABRIC_NAME or CHILD_FABRIC_NAME contains an invalid FABRIC_NAME" in str(excinfo.value)


def test_fab_mem_delete_00026(child_fabric_delete) -> None:
    """
    ### Classes and Methods
    - childFabricDelete
        - __init__()

    ### Test

    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = child_fabric_delete
    assert instance.class_name == "childFabricDelete"
    assert instance.action == "child_fabric_delete"
    assert instance.fabric_names is None
    assert instance.path is None
    assert instance.verb is None
    assert instance.ep_child_fabric_delete.class_name == "EpChildFabricExit"


def test_fab_mem_delete_00027(child_fabric_delete) -> None:
    """
    ### Classes and Methods

    - childFabricDelete
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
        instance = child_fabric_delete
        instance.fabric_names = fabric_names
    assert instance.fabric_names == fabric_names


def test_fab_mem_delete_00028(child_fabric_delete) -> None:
    """
    ### Classes and Methods

    - childFabricDelete
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
        instance = child_fabric_delete

    match = r"childFabricDelete\.fabric_names: "
    match += r"fabric_names must be a list\."

    with pytest.raises(ValueError, match=match):
        instance.fabric_names = "NOT_A_LIST"

    assert instance.fabric_names is None


def test_fab_mem_delete_00029(child_fabric_delete) -> None:
    """
    ### Classes and Methods

    - childFabricDelete
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
        instance = child_fabric_delete

    match = r"childFabricDelete.fabric_names: "
    match += r"fabric_names must be a list of strings."

    with pytest.raises(ValueError, match=match):
        instance.fabric_names = [1, 2, 3]

    assert instance.fabric_names is None


def test_fab_mem_delete_00030(child_fabric_delete) -> None:
    """
    ### Classes and Methods

    - childFabricDelete
        - fabric_names setter

    ### Summary
    Verify behavior when ``fabric_names`` is set to an empty list.

    ### Setup

    -   childFabricQuery().fabric_names is set to an empty list

    ### Test
    -   ``ValueError`` is raised from ``fabric_names`` setter.
    """
    match = r"childFabricDelete.fabric_names: fabric_names must be a list of "
    match += r"at least one string."

    with pytest.raises(ValueError, match=match):
        instance = child_fabric_delete
        instance.fabric_names = []


def test_fab_mem_delete_00031(child_fabric_delete) -> None:
    """
    ### Classes and Methods

    - childFabricDelete
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
    payload = {'destFabric': 'MSD1', 'sourceFabric': 'child'}
    with does_not_raise():
        instance = child_fabric_delete
        instance.rest_send = RestSend(params)
        instance.results = Results()

    match = r"childFabricDelete._validate_commit_parameters: "
    match += r"fabric_names must be set prior to calling commit."

    with pytest.raises(ValueError, match=match):
        instance.commit(payload)

    assert instance.fabric_names is None


def test_fab_mem_delete_00032(child_fabric_delete) -> None:
    """
    ### Classes and Methods

    - childFabricDelete
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
    payload = {'destFabric': 'MSD1', 'sourceFabric': 'child'}
    with does_not_raise():
        instance = child_fabric_delete
        instance.fabric_names = ["f1"]
        instance.results = Results()

    match = r"childFabricDelete._validate_commit_parameters: "
    match += r"rest_send must be set prior to calling commit."

    with pytest.raises(ValueError, match=match):
        instance.commit(payload)

    assert instance.rest_send is None


def test_fab_mem_delete_00033(child_fabric_delete) -> None:
    """
    ### Classes and Methods

    - childFabricDelete
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
    payload = {'destFabric': 'MSD1', 'sourceFabric': 'child'}
    with does_not_raise():
        instance = child_fabric_delete
        instance.fabric_names = ["f1"]
        instance.rest_send = RestSend(params)

    match = r"childFabricDelete\._validate_commit_parameters:\s+"
    match += r"results must be set prior to calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit(payload)


def test_fab_mem_delete_00034(child_fabric_delete) -> None:
    """
     ### Classes and Methods

     - childFabricCommon
         - __init__()
     - childFabricDelete
         - __init__()

    ### Summary

     -   Verify that an Exception is not raised
    """
    with does_not_raise():
        instance = child_fabric_delete
        instance.rest_send = RestSend(params)
        instance.rest_send.path = instance.ep_child_fabric_delete.path
        instance.rest_send.verb = instance.ep_child_fabric_delete.verb
    path = "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/msdExit"
    assert instance.rest_send.path == path
    assert instance.rest_send.verb == "POST"


@pytest.mark.parametrize("fabric_name", [123, 123.45, [], {}])
def test_fab_mem_delete_00035(fabric_name) -> None:
    t_params = {'config': [{'FABRIC_NAME': fabric_name, 'CHILD_FABRIC_NAME': 'child'}]}
    t_params.update(params)
    delete_instance = Deleted(t_params)
    match = r"ConversionUtils\.validate_fabric_name: "
    match += "Invalid fabric name. Expected string. Got"
    with pytest.raises(ValueError, match=match):
        delete_instance.commit()


@pytest.mark.parametrize("fabric_name", [123, 123.45, [], {}])
def test_fab_mem_delete_00036(fabric_name) -> None:
    t_params = {'config': [{'FABRIC_NAME': 'MSD', 'CHILD_FABRIC_NAME': fabric_name}]}
    t_params.update(params)
    delete_instance = Deleted(t_params)
    match = r"ConversionUtils\.validate_fabric_name: "
    match += "Invalid fabric name. Expected string. Got"
    with pytest.raises(ValueError, match=match):
        delete_instance.commit()


def test_fab_mem_delete_00037() -> None:
    """
    ### Classes and Methods

    - childFabricCommon()
        - __init__()
        - payloads setter
    - childFabricDelete
        - __init__()
        - commit()

    ### Summary

    -   The user attempts to delete a child fabric from the MSD fabric that does not exists on the
        controller. raises ValueError

    """
    key = "Fabric_association_get_response_exists"
    t_params = {'config': [{'FABRIC_NAME': 'f2', 'CHILD_FABRIC_NAME': 'child'}]}
    t_params.update(del_params)

    def responses():
        yield fabric_member_data(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(t_params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Deleted(t_params)
        instance.fabric_names = ["f2"]
        instance.rest_send = rest_send
        instance.results = Results()
    match = "is not found in Controller. Please create and try again"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fab_mem_delete_00038() -> None:
    """
    ### Classes and Methods

    - childFabricCommon()
        - __init__()
        - payloads setter
    - childFabricDelete
        - __init__()
        - commit()

    ### Summary

    -   The user attempts to delete a child fabric from the MSD fabric that does not exists on the
        controller. raises ValueError

    """
    method_name = inspect.stack()[0][3]
    key = "Fabric_association_get_valid_data"
    t_params = {'config': [{'FABRIC_NAME': 'f1', 'CHILD_FABRIC_NAME': 'child'}]}
    t_params.update(del_params)

    def responses():
        yield fabric_member_data(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(t_params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Deleted(t_params)
        instance.fabric_names = ["f1"]
        instance.rest_send = rest_send
        instance.results = Results()
    match = "is not of type MSD"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fab_mem_delete_00039() -> None:
    """
    ### Classes and Methods

    - childFabricCommon()
        - __init__()
        - payloads setter
    - childFabricDelete
        - __init__()
        - commit()

    ### Summary

    -   Verify successful fabric delete code path.
    -   The user attempts to delete a child fabric that is not a child anymore
    """
    method_name = inspect.stack()[0][3]
    key = "Fabric_association_get_response_exists"
    t_params = {'config': [{'FABRIC_NAME': 'f1', 'CHILD_FABRIC_NAME': 'child2'}]}
    t_params.update(del_params)

    def responses():
        yield fabric_member_data(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(t_params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Deleted(t_params)
        instance.fabric_names = ["f1"]
        instance.rest_send = rest_send
        instance.results = Results()
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.metadata) == 1
    assert len(instance.results.response) == 1
    assert len(instance.results.result) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("action", None) == "child_fabric_delete"
    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("state", None) == "deleted"
    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.response[0].get("MESSAGE", None) == "Given child fabric is already not a member of MSD fabric"
    assert instance.results.result[0].get("changed", None) is False
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_fab_mem_delete_00040(child_fabric_delete) -> None:
    """
     ### Classes and Methods

     - childFabricCommon()
         - __init__()
         - payloads setter
     - childFabricDelete
         - __init__()
         - commit()

    ### Summary

     -   Verify successful child fabric delete code path.
     -   The user attempts to delete a child fabric from the MSD fabric.
    """
    method_name = inspect.stack()[0][3]
    key = "childFabric_delete_response_2"

    def responses():
        yield fabric_member_data(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend({"state": "deleted", "check_mode": False})
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    payload = {'destFabric': 'f1', 'sourceFabric': 'child'}
    with does_not_raise():
        instance = child_fabric_delete
        instance.fabric_names = ["f1"]
        instance.rest_send = rest_send
        instance.results = Results()
        instance.commit(payload)

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.metadata) == 1
    assert len(instance.results.response) == 1
    assert len(instance.results.result) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.diff[0].get("destFabric", None) == "f1"
    assert instance.results.diff[0].get("sourceFabric", None) == "child"

    assert instance.results.metadata[0].get("action", None) == "child_fabric_delete"
    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("state", None) == "deleted"

    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.response[0].get("MESSAGE", None) == "OK"

    assert instance.results.result[0].get("changed", None) is True
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert True in instance.results.changed
    assert False not in instance.results.changed


def test_fab_mem_delete_00041(child_fabric_delete) -> None:
    """
     ### Classes and Methods

     - childFabricCommon()
         - __init__()
         - payloads setter
     - childFabricDelete
         - __init__()
         - commit()

    ### Summary

     -   Verify unsuccessful scenario - Failure response from NDFC during child fabric delete is displayed properly.
     -   The user attempts to delete a child fabric from the MSD fabric.
    """

    key = "childFabric_delete_response_3"

    def responses():
        yield fabric_member_data(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend({"state": "deleted", "check_mode": False})
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    payload = {'destFabric': 'f1', 'sourceFabric': 'child'}
    with does_not_raise():
        instance = child_fabric_delete
        instance.fabric_names = ["f1"]
        instance.rest_send = rest_send
        instance.results = Results()
        instance.commit(payload)

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.metadata) == 1
    assert len(instance.results.response) == 1
    assert len(instance.results.result) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.diff[0].get("destFabric", None) is None
    assert instance.results.diff[0].get("sourceFabric", None) is None

    assert instance.results.metadata[0].get("action", None) == "child_fabric_delete"
    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("state", None) == "deleted"

    assert instance.results.response[0].get("RETURN_CODE", None) == 500
    assert instance.results.response[0].get("MESSAGE", None) == "NOK"

    assert instance.results.result[0].get("changed", None) is False
    assert instance.results.result[0].get("success", None) is False

    assert True in instance.results.failed
    assert False not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_fab_mem_delete_00042() -> None:
    """
    ### Classes and Methods

    - childFabricCommon()
        - __init__()
        - payloads setter
    - childFabricDelete
        - __init__()
        - commit()

    ### Summary

    -   Verify unsuccessful fabric-associations response and reaction of child fabric delete class
    -   The user attempts to delete a child fabric
    """
    key = "Fabric_association_get_failure_response"
    t_params = {'config': [{'FABRIC_NAME': 'f1', 'CHILD_FABRIC_NAME': 'child2'}]}
    t_params.update(del_params)

    def responses():
        yield fabric_member_data(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(t_params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Deleted(t_params)
        instance.fabric_names = ["f1"]
        instance.rest_send = rest_send
        instance.results = Results()

    match = "Fabric Association response from NDFC controller returns failure"
    with pytest.raises(ValueError, match=match):
        instance.commit()


merged_params = {'state': 'merged', 'check_mode': False}


def test_fab_mem_merged_init_00043():
    t_params = {'config': [{'FABRIC_NAME': 'valid_fabric'}, {'CHILD_FABRIC_NAME': 'child_fabric'}]}
    t_params.update(merged_params)
    merged_instance = Merged(t_params)
    assert merged_instance.class_name == 'Merged'
    assert merged_instance.action == 'child_fabric_add'
    assert 'merged' in merged_instance._implemented_states


@pytest.mark.parametrize(
    "invalid_fabric_name",
    ["@123", "", "$abd#", "-!`", "%^&", None],
)
def test_fab_mem_merged_invalid_msd_fabric_name_00044(invalid_fabric_name):
    t_params = {'config': [{'FABRIC_NAME': {invalid_fabric_name}, 'CHILD_FABRIC_NAME': "abc"}]}
    t_params.update(params)
    key = "childFabric_add_response"

    def responses():
        yield fabric_member_data(key)

    gen_responses = ResponseGenerator(responses())
    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    rest_send = RestSend(t_params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    sender.gen = gen_responses
    merged_instance = Merged(t_params)
    merged_instance.rest_send = rest_send
    with pytest.raises(ValueError) as excinfo:
        merged_instance.commit()
    assert "contains an invalid FABRIC_NAME" in str(excinfo.value)


@pytest.mark.parametrize(
    "invalid_fabric_name",
    ["@123", "", "$abd#", "-!`", "%^&", None],
)
def test_fab_mem_merged_invalid_child_fabric_name_00045(invalid_fabric_name):
    t_params = {'config': [{'FABRIC_NAME': "abc", 'CHILD_FABRIC_NAME': {invalid_fabric_name}}]}
    t_params.update(params)
    key = "childFabric_add_response"

    def responses():
        yield fabric_member_data(key)

    gen_responses = ResponseGenerator(responses())
    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    rest_send = RestSend(t_params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    sender.gen = gen_responses
    merged_instance = Merged(t_params)
    merged_instance.rest_send = rest_send
    with pytest.raises(ValueError) as excinfo:
        merged_instance.commit()
    assert "Playbook configuration for FABRIC_NAME or CHILD_FABRIC_NAME contains an invalid FABRIC_NAME" in str(excinfo.value)


def test_fab_mem_merged_invalid_config_00046():
    t_params = {'config': None}
    t_params.update(params)
    key = "childFabric_add_response"

    def responses():
        yield fabric_member_data(key)

    gen_responses = ResponseGenerator(responses())
    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    rest_send = RestSend(t_params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    sender.gen = gen_responses
    merged_instance = Merged(t_params)
    merged_instance.rest_send = rest_send
    with pytest.raises(ValueError) as excinfo:
        merged_instance.commit()
    assert "params is missing config parameter" in str(excinfo.value)


def test_fab_mem_merged_invalid_config_00047():
    t_params = {'config': [{'FABRIC_NAME': ''}]}
    t_params.update(params)
    key = "childFabric_add_response"

    def responses():
        yield fabric_member_data(key)

    gen_responses = ResponseGenerator(responses())
    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    rest_send = RestSend(t_params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    sender.gen = gen_responses
    merged_instance = Merged(t_params)
    merged_instance.rest_send = rest_send
    with pytest.raises(ValueError) as excinfo:
        merged_instance.commit()
    assert "CHILD_FABRIC_NAME : Required parameter not found" in str(excinfo.value)


def test_fab_mem_merged_invalid_config_00048():
    t_params = {'config': [{'FABRIC_NAME': 123, 'CHILD_FABRIC_NAME': True}]}
    t_params.update(params)
    key = "childFabric_add_response"

    def responses():
        yield fabric_member_data(key)

    gen_responses = ResponseGenerator(responses())
    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    rest_send = RestSend(t_params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    sender.gen = gen_responses
    merged_instance = Merged(t_params)
    merged_instance.rest_send = rest_send
    with pytest.raises(ValueError) as excinfo:
        merged_instance.commit()
    assert "Playbook configuration for FABRIC_NAME or CHILD_FABRIC_NAME contains an invalid FABRIC_NAME" in str(excinfo.value)


def test_fab_mem_merged_00049(child_fabric_add) -> None:
    """
    ### Classes and Methods
    - childFabricAdd
        - __init__()

    ### Test

    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = child_fabric_add
    assert instance.class_name == "childFabricAdd"
    assert instance.action == "child_fabric_add"
    assert instance.fabric_names is None
    assert instance.path is None
    assert instance.verb is None
    assert instance.ep_fabric_add.class_name == "EpChildFabricAdd"


def test_fab_mem_merged_00050(child_fabric_add) -> None:
    """
    ### Classes and Methods

    - childFabricAdd
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
        instance = child_fabric_add
        instance.fabric_names = fabric_names
    assert instance.fabric_names == fabric_names


def test_fab_mem_merged_00051(child_fabric_add) -> None:
    """
    ### Classes and Methods

    - childFabricAdd
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
        instance = child_fabric_add

    match = r"childFabricAdd\.fabric_names: "
    match += r"fabric_names must be a list\."

    with pytest.raises(ValueError, match=match):
        instance.fabric_names = "NOT_A_LIST"

    assert instance.fabric_names is None


def test_fab_mem_merged_00052(child_fabric_add) -> None:
    """
    ### Classes and Methods

    - childFabricAdd
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
        instance = child_fabric_add

    match = r"childFabricAdd.fabric_names: "
    match += r"fabric_names must be a list of strings."

    with pytest.raises(ValueError, match=match):
        instance.fabric_names = [1, 2, 3]

    assert instance.fabric_names is None


def test_fab_mem_merged_00053(child_fabric_add) -> None:
    """
    ### Classes and Methods

    - childFabricAdd
        - fabric_names setter

    ### Summary
    Verify behavior when ``fabric_names`` is set to an empty list.

    ### Setup

    -   childFabricAdd().fabric_names is set to an empty list

    ### Test
    -   ``ValueError`` is raised from ``fabric_names`` setter.
    """
    match = r"childFabricAdd.fabric_names: fabric_names must be a list of "
    match += r"at least one string."

    with pytest.raises(ValueError, match=match):
        instance = child_fabric_add
        instance.fabric_names = []


def test_fab_mem_merged_00054(child_fabric_add) -> None:
    """
    ### Classes and Methods

    - childFabricAdd
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
    payload = {'destFabric': 'MSD1', 'sourceFabric': 'child'}
    with does_not_raise():
        instance = child_fabric_add
        instance.rest_send = RestSend(params)
        instance.results = Results()

    match = r"childFabricAdd._validate_commit_parameters: "
    match += r"fabric_names must be set prior to calling commit."

    with pytest.raises(ValueError, match=match):
        instance.commit(payload)

    assert instance.fabric_names is None


def test_fab_mem_merged_00055(child_fabric_add) -> None:
    """
    ### Classes and Methods

    - childFabricAdd
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
    payload = {'destFabric': 'MSD1', 'sourceFabric': 'child'}
    with does_not_raise():
        instance = child_fabric_add
        instance.fabric_names = ["f1"]
        instance.results = Results()

    match = r"childFabricAdd._validate_commit_parameters: "
    match += r"rest_send must be set prior to calling commit."

    with pytest.raises(ValueError, match=match):
        instance.commit(payload)

    assert instance.rest_send is None


def test_fab_mem_merged_00056(child_fabric_add) -> None:
    """
    ### Classes and Methods

    - childFabricAdd
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
    payload = {'destFabric': 'MSD1', 'sourceFabric': 'child'}
    with does_not_raise():
        instance = child_fabric_add
        instance.fabric_names = ["f1"]
        instance.rest_send = RestSend(params)

    match = r"childFabricAdd\._validate_commit_parameters:\s+"
    match += r"results must be set prior to calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit(payload)


def test_fab_mem_merged_00057(child_fabric_add) -> None:
    """
     ### Classes and Methods

     - childFabricCommon
         - __init__()
     - childFabricAdd
         - __init__()

    ### Summary

     -   Verify that endpoint values are set correctly when ``fabric_names``
         contains a valid fabric name.
     -   Verify that an Exception is not raised
    """
    with does_not_raise():
        instance = child_fabric_add
        instance.rest_send = RestSend(params)
        instance.rest_send.path = instance.ep_fabric_add.path
        instance.rest_send.verb = instance.ep_fabric_add.verb
    path = "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/msdAdd"
    assert instance.rest_send.path == path
    assert instance.rest_send.verb == "POST"


@pytest.mark.parametrize("fabric_name", [123, 123.45, [], {}])
def test_fab_mem_merged_00058(fabric_name) -> None:
    t_params = {'config': [{'FABRIC_NAME': fabric_name, 'CHILD_FABRIC_NAME': 'child'}]}
    t_params.update(params)
    key = "childFabric_add_response"

    def responses():
        yield fabric_member_data(key)

    gen_responses = ResponseGenerator(responses())
    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    rest_send = RestSend(t_params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    sender.gen = gen_responses
    merged_instance = Merged(t_params)
    merged_instance.rest_send = rest_send
    match = r"ConversionUtils\.validate_fabric_name: "
    match += "Invalid fabric name. Expected string. Got"
    with pytest.raises(ValueError, match=match):
        merged_instance.commit()


@pytest.mark.parametrize("fabric_name", [123, 123.45, [], {}])
def test_fab_mem_merged_00059(fabric_name) -> None:
    t_params = {'config': [{'FABRIC_NAME': 'MSD', 'CHILD_FABRIC_NAME': fabric_name}]}
    t_params.update(params)
    key = "childFabric_add_response"

    def responses():
        yield fabric_member_data(key)

    gen_responses = ResponseGenerator(responses())
    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    rest_send = RestSend(t_params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    sender.gen = gen_responses
    merged_instance = Merged(t_params)
    merged_instance.rest_send = rest_send
    match = r"ConversionUtils\.validate_fabric_name: "
    match += "Invalid fabric name. Expected string. Got"
    with pytest.raises(ValueError, match=match):
        merged_instance.commit()


def test_fab_mem_merged_00060() -> None:
    """
    ### Classes and Methods

    - childFabricCommon()
        - __init__()
        - payloads setter
    - childFabricAdd
        - __init__()
        - commit()

    ### Summary

    -   The user attempts to add a child fabric into the MSD fabric that does not exists on the
        controller. raises ValueError

    """
    method_name = inspect.stack()[0][3]
    key1 = "get_controller_version"
    key2 = "Fabric_association_get_response_exists"

    t_params = {'config': [{'FABRIC_NAME': 'f2', 'CHILD_FABRIC_NAME': 'child'}]}
    t_params.update(merged_params)

    def responses():
        yield fabric_member_data(key1)
        yield fabric_member_data(key2)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(t_params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Merged(t_params)
        instance.fabric_names = ["f2"]
        instance.rest_send = rest_send
        instance.results = Results()
    match = "is not found in Controller. Please create and try again"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fab_mem_merged_00061() -> None:
    """
    ### Classes and Methods

    - childFabricCommon()
        - __init__()
        - payloads setter
    - childFabricAdd
        - __init__()
        - commit()

    ### Summary

    -   The user attempts to add a child fabric into the MSD fabric that is not a MSD fabric.
    -   raises ValueError

    """
    method_name = inspect.stack()[0][3]
    key1 = "get_controller_version"
    key2 = "Fabric_association_get_valid_data"
    t_params = {'config': [{'FABRIC_NAME': 'f1', 'CHILD_FABRIC_NAME': 'child'}]}
    t_params.update(merged_params)

    def responses():
        yield fabric_member_data(key1)
        yield fabric_member_data(key2)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(t_params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Merged(t_params)
        instance.fabric_names = ["f1"]
        instance.rest_send = rest_send
        instance.results = Results()
    match = "is not of type MSD"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fab_mem_merged_00062() -> None:
    """
    ### Classes and Methods

    - childFabricCommon()
        - __init__()
        - payloads setter
    - childFabricAdd
        - __init__()
        - commit()

    ### Summary

    -   Verify unsuccessful child fabric add code path.
    -   The user attempts to add a child fabric that is not exists in the controller
    """
    method_name = inspect.stack()[0][3]
    key1 = "get_controller_version"
    key2 = "Fabric_association_get_response_exists"

    t_params = {'config': [{'FABRIC_NAME': 'f1', 'CHILD_FABRIC_NAME': 'child2'}]}
    t_params.update(del_params)

    def responses():
        yield fabric_member_data(key1)
        yield fabric_member_data(key2)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(t_params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Merged(t_params)
        instance.fabric_names = ["f1"]
        instance.rest_send = rest_send
        instance.results = Results()

    match = r"verify_child_fab_exists_in_controller: Playbook configuration for CHILD_FABRIC_NAME (\S+) "
    match += r"is not found in Controller. Please create and try again"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fab_mem_merged_00063(child_fabric_add) -> None:
    """
     ### Classes and Methods

     - childFabricCommon()
         - __init__()
         - payloads setter
     - childFabricAdd
         - __init__()
         - commit()

    ### Summary

     -   Verify successful child fabric add code path.
     -   The user attempts to add a child fabric into the MSD fabric.
    """

    key1 = "get_controller_version"
    key2 = "childFabric_add_response"

    def responses():
        yield fabric_member_data(key1)
        yield fabric_member_data(key2)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend({"state": "merged", "check_mode": False})
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    payload = {'destFabric': 'f1', 'sourceFabric': 'child'}
    with does_not_raise():
        instance = child_fabric_add
        instance.fabric_names = ["f1"]
        instance.rest_send = rest_send
        instance.results = Results()
        instance.commit(payload)

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.metadata) == 1
    assert len(instance.results.response) == 1
    assert len(instance.results.result) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.diff[0].get("destFabric", None) == "f1"
    assert instance.results.diff[0].get("sourceFabric", None) == "child"

    assert instance.results.metadata[0].get("action", None) == "child_fabric_add"
    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("state", None) == "merged"

    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.response[0].get("MESSAGE", None) == "OK"

    assert instance.results.result[0].get("changed", None) is True
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert True in instance.results.changed
    assert False not in instance.results.changed


def test_fab_mem_merged_00064(child_fabric_add) -> None:
    """
     ### Classes and Methods

     - childFabricCommon()
         - __init__()
         - payloads setter
     - childFabricAdd
         - __init__()
         - commit()

    ### Summary

     -   Verify unsuccessful scenario - Failure response from NDFC during child fabric Add is displayed properly.
     -   The user attempts to Add a child fabric from the MSD fabric.
    """
    key = "childFabric_add_response_3"

    def responses():
        yield fabric_member_data(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend({"state": "merged", "check_mode": False})
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    payload = {'destFabric': 'f1', 'sourceFabric': 'child'}
    with does_not_raise():
        instance = child_fabric_add
        instance.fabric_names = ["f1"]
        instance.rest_send = rest_send
        instance.results = Results()
        instance.commit(payload)

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.metadata) == 1
    assert len(instance.results.response) == 1
    assert len(instance.results.result) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.diff[0].get("destFabric", None) is None
    assert instance.results.diff[0].get("sourceFabric", None) is None

    assert instance.results.metadata[0].get("action", None) == "child_fabric_add"
    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("state", None) == "merged"

    assert instance.results.response[0].get("RETURN_CODE", None) == 500
    assert instance.results.response[0].get("MESSAGE", None) == "NOK"

    assert instance.results.result[0].get("changed", None) is False
    assert instance.results.result[0].get("success", None) is False

    assert True in instance.results.failed
    assert False not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_fab_mem_merged_00065() -> None:
    """
    ### Classes and Methods

    - childFabricCommon()
        - __init__()
        - payloads setter
    - childFabricAdd
        - __init__()
        - commit()

    ### Summary

    -   Verify unsuccessful fabric-associations response and reaction of child add class
    -   The user attempts to add a child fabric
    """

    key1 = "get_controller_version"
    key2 = "Fabric_association_get_failure_response"
    t_params = {'config': [{'FABRIC_NAME': 'f1', 'CHILD_FABRIC_NAME': 'child2'}]}
    t_params.update(merged_params)

    def responses():
        yield fabric_member_data(key1)
        yield fabric_member_data(key2)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(t_params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Merged(t_params)
        instance.fabric_names = ["f1"]
        instance.rest_send = rest_send
        instance.results = Results()

    match = "Fabric Association response from NDFC controller returns failure"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fab_mem_merged_00066() -> None:
    """
    ### Classes and Methods

    - childFabricCommon()
        - __init__()
        - payloads setter
    - childFabricAdd
        - __init__()
        - commit()

    ### Summary

    -   Verify unsuccessful child fabric add code path.
    -   The user attempts to add a child fabric to a MSD. but child fabric alread part of another MSD
    """
    method_name = inspect.stack()[0][3]
    key1 = "get_controller_version"
    key2 = "Fabric_association_get_response_00018"

    t_params = {'config': [{'FABRIC_NAME': 'f1', 'CHILD_FABRIC_NAME': 'child2'}]}
    t_params.update(del_params)

    def responses():
        yield fabric_member_data(key1)
        yield fabric_member_data(key2)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(t_params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Merged(t_params)
        instance.fabric_names = ["f1"]
        instance.rest_send = rest_send
        instance.results = Results()

    match = r"Child fabric (\S+) is member of another Fabric"
    with pytest.raises(ValueError, match=match):
        instance.commit()
