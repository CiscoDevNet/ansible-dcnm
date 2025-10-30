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
# pylint: disable=unused-variable
# pylint: disable=invalid-name
# pylint: disable=line-too-long
# pylint: disable=too-many-lines
"""
Unit tests for FabricGroupMemberInfo class in module_utils/fabric_group/fabric_group_member_info.py
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2025 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import inspect

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.operation_type import OperationType
from ansible_collections.cisco.dcnm.plugins.module_utils.common.response_handler import ResponseHandler
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results_v2 import Results
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_file import Sender
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric_group.fabric_group_member_info import FabricGroupMemberInfo
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric_group.utils import (
    MockAnsibleModule,
    does_not_raise,
    params,
    responses_fabric_group_member_info,
)


@pytest.fixture(name="fabric_group_member_info")
def fabric_group_member_info_fixture():
    """
    Return FabricGroupMemberInfo instance
    """
    return FabricGroupMemberInfo()


def test_fabric_group_member_info_00000(fabric_group_member_info) -> None:
    """
    # Summary

    Verify FabricGroupMemberInfo class is initialized correctly

    ## Classes and Methods

    - FabricGroupMemberInfo
        - __init__()

    ## Test

    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_group_member_info

    assert instance.class_name == "FabricGroupMemberInfo"
    assert instance.action == "fabric_group_member_info"
    assert instance._cluster_name == ""
    assert instance._member_fabric_count == 0
    assert instance.data == {}
    assert instance._member_fabric_names == []
    assert instance._fabric_group_name == ""
    assert instance._refreshed is False
    assert instance._rest_send is None
    assert instance._results is None


def test_fabric_group_member_info_00010(fabric_group_member_info) -> None:
    """
    # Summary

    Verify rest_send property setter and getter work correctly

    ## Classes and Methods

    - FabricGroupMemberInfo
        - __init__()
        - rest_send property setter
        - rest_send property getter

    ## Test

    - rest_send property is set and retrieved successfully
    - Exception is not raised
    """
    rest_send = RestSend(params)

    with does_not_raise():
        instance = fabric_group_member_info
        instance.rest_send = rest_send

    assert instance.rest_send == rest_send


def test_fabric_group_member_info_00020(fabric_group_member_info) -> None:
    """
    # Summary

    Verify rest_send property getter raises ValueError when accessed before being set

    ## Classes and Methods

    - FabricGroupMemberInfo
        - __init__()
        - rest_send property getter

    ## Test

    - ValueError is raised with appropriate message
    """
    match = r"FabricGroupMemberInfo\.rest_send: "
    match += r"rest_send property should be set before accessing\."

    with pytest.raises(ValueError, match=match):
        instance = fabric_group_member_info
        result = instance.rest_send  # pylint: disable=pointless-statement


def test_fabric_group_member_info_00030(fabric_group_member_info) -> None:
    """
    # Summary

    Verify results property setter and getter work correctly

    ## Classes and Methods

    - FabricGroupMemberInfo
        - __init__()
        - results property setter
        - results property getter

    ## Test

    - results property is set and retrieved successfully
    - action, changed, and operation_type are set correctly
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_group_member_info
        instance.results = Results()

    assert instance.results.action == "fabric_group_member_info"
    assert False in instance.results.changed
    assert instance.results.operation_type == OperationType.QUERY


def test_fabric_group_member_info_00040(fabric_group_member_info) -> None:
    """
    # Summary

    Verify results property getter raises ValueError when accessed before being set

    ## Classes and Methods

    - FabricGroupMemberInfo
        - __init__()
        - results property getter

    ## Test

    - ValueError is raised with appropriate message
    """
    match = r"FabricGroupMemberInfo\.results: "
    match += r"results property should be set before accessing\."

    with pytest.raises(ValueError, match=match):
        instance = fabric_group_member_info
        result = instance.results  # pylint: disable=pointless-statement


def test_fabric_group_member_info_00050(fabric_group_member_info) -> None:
    """
    # Summary

    Verify fabric_group_name property setter and getter work correctly

    ## Classes and Methods

    - FabricGroupMemberInfo
        - __init__()
        - fabric_group_name property setter
        - fabric_group_name property getter

    ## Test

    - fabric_group_name property is set and retrieved successfully
    - Exception is not raised
    """
    fabric_group_name = "MyFabricGroup"

    with does_not_raise():
        instance = fabric_group_member_info
        instance.fabric_group_name = fabric_group_name

    assert instance.fabric_group_name == fabric_group_name


def test_fabric_group_member_info_00060(fabric_group_member_info) -> None:
    """
    # Summary

    Verify refreshed property returns False before refresh() is called

    ## Classes and Methods

    - FabricGroupMemberInfo
        - __init__()
        - refreshed property getter

    ## Test

    - refreshed property is False by default
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_group_member_info

    assert instance.refreshed is False


def test_fabric_group_member_info_00070(fabric_group_member_info) -> None:
    """
    # Summary

    Verify refresh() populates data correctly when fabric group has members

    ## Classes and Methods

    - FabricGroupMemberInfo
        - __init__()
        - refresh()

    ## Test

    - fabric_group_name is set to "MCFG1"
    - refresh() is called
    - data is populated with member fabric information
    - cluster_name, member_fabric_count, and member_fabric_names are accessible
    - Exception is not raised
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_group_member_info(f"{key}")

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
        instance = fabric_group_member_info
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MCFG1"
        instance.refresh()

    assert instance.refreshed is True
    assert instance.cluster_name == "ND3"
    assert instance.member_fabric_count == 1
    assert "SITE1" in instance.member_fabric_names
    assert instance.data.get("clusterName") == "ND3"
    assert "SITE1" in instance.data.get("fabrics", {})


def test_fabric_group_member_info_00080(fabric_group_member_info) -> None:
    """
    # Summary

    Verify refresh() works correctly when fabric group has no members

    ## Classes and Methods

    - FabricGroupMemberInfo
        - __init__()
        - refresh()

    ## Test

    - fabric_group_name is set to "EMPTY_GROUP"
    - refresh() is called
    - data is set to empty dict
    - cluster_name is empty string
    - member_fabric_count is 0
    - member_fabric_names is empty list
    - Exception is not raised
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_group_member_info(f"{key}")

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
        instance = fabric_group_member_info
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "EMPTY_GROUP"
        instance.refresh()

    assert instance.refreshed is True
    assert instance.cluster_name == ""
    assert instance.member_fabric_count == 0
    assert instance.member_fabric_names == []
    assert instance.data == {}


def test_fabric_group_member_info_00090(fabric_group_member_info) -> None:
    """
    # Summary

    Verify refresh() raises ValueError when fabric_group_name is not set

    ## Classes and Methods

    - FabricGroupMemberInfo
        - __init__()
        - refresh()

    ## Test

    - rest_send and results are set
    - fabric_group_name is NOT set
    - refresh() raises ValueError with appropriate message
    """
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()

    match = r"FabricGroupMemberInfo\.validate_refresh_parameters: "
    match += r"FabricGroupMemberInfo\.fabric_group_name must be set before calling "
    match += r"FabricGroupMemberInfo\.refresh\(\)\."

    with pytest.raises(ValueError, match=match):
        instance = fabric_group_member_info
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()


def test_fabric_group_member_info_00100(fabric_group_member_info) -> None:
    """
    # Summary

    Verify refresh() raises ValueError when rest_send is not set

    ## Classes and Methods

    - FabricGroupMemberInfo
        - __init__()
        - refresh()
        - rest_send property getter

    ## Test

    - results and fabric_group_name are set
    - rest_send is NOT set
    - refresh() raises ValueError when accessing rest_send property
    """
    match = r"FabricGroupMemberInfo\.rest_send: "
    match += r"rest_send property should be set before accessing\."

    with pytest.raises(ValueError, match=match):
        instance = fabric_group_member_info
        instance.results = Results()
        instance.fabric_group_name = "MCFG1"
        instance.refresh()


def test_fabric_group_member_info_00120(fabric_group_member_info) -> None:
    """
    # Summary

    Verify cluster_name property raises ValueError when accessed before refresh()

    ## Classes and Methods

    - FabricGroupMemberInfo
        - __init__()
        - cluster_name property getter

    ## Test

    - rest_send, results, and fabric_group_name are set
    - refresh() is NOT called
    - cluster_name property raises ValueError with appropriate message
    """
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()

    match = r"FabricGroupMemberInfo\.data_cluster_name: "
    match += r"refresh\(\) must be called before accessing data_cluster_name\."

    with pytest.raises(ValueError, match=match):
        instance = fabric_group_member_info
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MCFG1"
        result = instance.cluster_name  # pylint: disable=pointless-statement


def test_fabric_group_member_info_00130(fabric_group_member_info) -> None:
    """
    # Summary

    Verify member_fabric_count property raises ValueError when accessed before refresh()

    ## Classes and Methods

    - FabricGroupMemberInfo
        - __init__()
        - member_fabric_count property getter

    ## Test

    - rest_send, results, and fabric_group_name are set
    - refresh() is NOT called
    - member_fabric_count property raises ValueError with appropriate message
    """
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()

    match = r"FabricGroupMemberInfo\.member_fabric_count: "
    match += r"refresh\(\) must be called before accessing member_fabric_count\."

    with pytest.raises(ValueError, match=match):
        instance = fabric_group_member_info
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MCFG1"
        result = instance.member_fabric_count  # pylint: disable=pointless-statement


def test_fabric_group_member_info_00140(fabric_group_member_info) -> None:
    """
    # Summary

    Verify member_fabric_names property raises ValueError when accessed before refresh()

    ## Classes and Methods

    - FabricGroupMemberInfo
        - __init__()
        - member_fabric_names property getter

    ## Test

    - rest_send, results, and fabric_group_name are set
    - refresh() is NOT called
    - member_fabric_names property raises ValueError with appropriate message
    """
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()

    match = r"FabricGroupMemberInfo\.member_fabric_names: "
    match += r"refresh\(\) must be called before accessing member_fabric_names\."

    with pytest.raises(ValueError, match=match):
        instance = fabric_group_member_info
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MCFG1"
        result = instance.member_fabric_names  # pylint: disable=pointless-statement
