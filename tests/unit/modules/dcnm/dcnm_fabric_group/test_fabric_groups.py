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
Unit tests for FabricGroups class in module_utils/fabric_group/fabric_groups.py
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
    params,
    responses_fabric_groups,
)


@pytest.fixture(name="fabric_groups")
def fabric_groups_fixture():
    """
    Return FabricGroups() instance.
    """
    return FabricGroups()


def test_fabric_groups_00000(fabric_groups) -> None:
    """
    # Summary

    Verify class initialization

    ## Classes and Methods

    - FabricGroups.__init__()

    ## Test

    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_groups
    assert instance.class_name == "FabricGroups"
    assert instance.action == "fabric_groups"
    assert instance.data == {}
    assert instance._fabric_group_names == []
    assert instance._filter == ""
    assert instance._refreshed is False


def test_fabric_groups_00010(fabric_groups) -> None:
    """
    # Summary

    Verify filter property setter and getter

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.filter (setter/getter)

    ## Test

    - filter is set to "MFG1"
    - filter returns "MFG1"
    """
    with does_not_raise():
        instance = fabric_groups
        instance.filter = "MFG1"
    assert instance.filter == "MFG1"


def test_fabric_groups_00020(fabric_groups) -> None:
    """
    # Summary

    Verify rest_send property setter and getter

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.rest_send (setter/getter)

    ## Test

    - rest_send is set to RestSend() instance
    - rest_send returns RestSend() instance
    """
    with does_not_raise():
        instance = fabric_groups
        rest_send = RestSend(params)
        instance.rest_send = rest_send
    assert instance.rest_send == rest_send


def test_fabric_groups_00021(fabric_groups) -> None:
    """
    # Summary

    Verify ValueError is raised when rest_send is accessed before being set

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.rest_send (getter)

    ## Test

    - ValueError is raised with expected message
    """
    match = r"FabricGroups\.rest_send: "
    match += r"rest_send property has not been set\."

    with pytest.raises(ValueError, match=match):
        instance = fabric_groups
        result = instance.rest_send  # pylint: disable=pointless-statement


def test_fabric_groups_00030(fabric_groups) -> None:
    """
    # Summary

    Verify results property setter and getter

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.results (setter/getter)

    ## Test

    - results is set to Results() instance
    - results returns Results() instance
    - results properties are set correctly
    """
    with does_not_raise():
        instance = fabric_groups
        results = Results()
        instance.results = results
    assert instance.results == results
    assert instance.results.action == "fabric_groups"
    assert False in instance.results.changed


def test_fabric_groups_00031(fabric_groups) -> None:
    """
    # Summary

    Verify ValueError is raised when results is accessed before being set

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.results (getter)

    ## Test

    - ValueError is raised with expected message
    """
    match = r"FabricGroups\.results: "
    match += r"results property has not been set\."

    with pytest.raises(ValueError, match=match):
        instance = fabric_groups
        result = instance.results  # pylint: disable=pointless-statement


def test_fabric_groups_00040(fabric_groups) -> None:
    """
    # Summary

    Verify refresh() populates data when fabric group exists

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.refresh()

    ## Test

    - refresh() is called successfully
    - data is populated with fabric group information
    - refreshed is True
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

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
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()

    assert instance._refreshed is True
    assert instance.data.get("MFG1") is not None
    assert instance.data["MFG1"]["fabricName"] == "MFG1"
    assert instance.data["MFG1"]["fabricId"] == "MC-FABRIC-69"
    assert instance.data["MFG1"]["nvPairs"]["FABRIC_NAME"] == "MFG1"
    assert instance.data["MFG1"]["nvPairs"]["FABRIC_TYPE"] == "MFD"


def test_fabric_groups_00041(fabric_groups) -> None:
    """
    # Summary

    Verify refresh() with no fabric groups on controller

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.refresh()

    ## Test

    - refresh() is called successfully
    - data is empty dict
    - refreshed is True
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

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
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()

    assert instance._refreshed is True
    assert instance.data == {}


def test_fabric_groups_00050(fabric_groups) -> None:
    """
    # Summary

    Verify all_data property returns all fabric group data

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.all_data (property)

    ## Test

    - all_data returns self.data
    - all_data contains expected fabric group
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

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
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()

    assert instance.all_data == instance.data
    assert instance.all_data.get("MFG1") is not None


def test_fabric_groups_00060(fabric_groups) -> None:
    """
    # Summary

    Verify filtered_data property returns data for specified fabric group

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.filtered_data (property)

    ## Test

    - filtered_data returns data for fabric group "MFG1"
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

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
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        instance.filter = "MFG1"

    assert instance.filtered_data.get("fabricName") == "MFG1"
    assert instance.filtered_data.get("fabricId") == "MC-FABRIC-69"


def test_fabric_groups_00061(fabric_groups) -> None:
    """
    # Summary

    Verify ValueError is raised when filtered_data is accessed without setting filter

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.filtered_data (property)

    ## Test

    - ValueError is raised with expected message
    """
    match = r"FabricGroups\.filtered_data: "
    match += r"FabricGroups\.filter must be set before accessing "
    match += r"FabricGroups\.filtered_data\."

    with pytest.raises(ValueError, match=match):
        instance = fabric_groups
        result = instance.filtered_data  # pylint: disable=pointless-statement


def test_fabric_groups_00062(fabric_groups) -> None:
    """
    # Summary

    Verify filtered_data returns empty dict when fabric group does not exist

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.filtered_data (property)

    ## Test

    - filtered_data returns empty dict
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

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
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        instance.filter = "NON_EXISTENT"

    assert instance.filtered_data == {}


def test_fabric_groups_00070(fabric_groups) -> None:
    """
    # Summary

    Verify asn property returns BGP_AS value from nvPairs

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.asn (property)

    ## Test

    - asn returns empty string when BGP_AS is empty
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

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
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        instance.filter = "MFG1"

    # BGP_AS is not in the test data, so it should return ""
    assert instance.asn == ""
    assert instance.bgp_as == ""


def test_fabric_groups_00080(fabric_groups) -> None:
    """
    # Summary

    Verify deployment_freeze property returns DEPLOYMENT_FREEZE value from nvPairs

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.deployment_freeze (property)

    ## Test

    - deployment_freeze returns False when not set
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

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
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        instance.filter = "MFG1"

    # DEPLOYMENT_FREEZE is not in the test data, so it should return False
    assert instance.deployment_freeze is False


def test_fabric_groups_00090(fabric_groups) -> None:
    """
    # Summary

    Verify enable_pbr property returns ENABLE_PBR value from nvPairs

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.enable_pbr (property)

    ## Test

    - enable_pbr returns False when not set
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

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
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        instance.filter = "MFG1"

    # ENABLE_PBR is not in the test data, so it should return False
    assert instance.enable_pbr is False


def test_fabric_groups_00100(fabric_groups) -> None:
    """
    # Summary

    Verify fabric_id property returns fabricId value

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.fabric_id (property)

    ## Test

    - fabric_id returns "MC-FABRIC-69"
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

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
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        instance.filter = "MFG1"

    assert instance.fabric_id == "MC-FABRIC-69"


def test_fabric_groups_00110(fabric_groups) -> None:
    """
    # Summary

    Verify fabric_type property returns FABRIC_TYPE value from nvPairs

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.fabric_type (property)

    ## Test

    - fabric_type returns "MFD"
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

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
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        instance.filter = "MFG1"

    assert instance.fabric_type == "MFD"


def test_fabric_groups_00120(fabric_groups) -> None:
    """
    # Summary

    Verify is_read_only property returns IS_READ_ONLY value from nvPairs

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.is_read_only (property)

    ## Test

    - is_read_only returns False when not set
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

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
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        instance.filter = "MFG1"

    # IS_READ_ONLY is not in the test data, so it should return False
    assert instance.is_read_only is False


def test_fabric_groups_00130(fabric_groups) -> None:
    """
    # Summary

    Verify per_vrf_loopback_auto_provision property returns value from nvPairs

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.per_vrf_loopback_auto_provision (property)

    ## Test

    - per_vrf_loopback_auto_provision returns False when not set
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

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
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        instance.filter = "MFG1"

    # PER_VRF_LOOPBACK_AUTO_PROVISION is not in the test data, so it should return False
    assert instance.per_vrf_loopback_auto_provision is False


def test_fabric_groups_00140(fabric_groups) -> None:
    """
    # Summary

    Verify replication_mode property returns REPLICATION_MODE value from nvPairs

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.replication_mode (property)

    ## Test

    - replication_mode returns empty string when not set
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

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
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        instance.filter = "MFG1"

    # replicationMode is empty string in test data
    assert instance.replication_mode == ""


def test_fabric_groups_00150(fabric_groups) -> None:
    """
    # Summary

    Verify template_name property returns templateName value

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.template_name (property)

    ## Test

    - template_name returns "MSD_Fabric"
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

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
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        instance.filter = "MFG1"

    assert instance.template_name == "MSD_Fabric"


def test_fabric_groups_00160(fabric_groups) -> None:
    """
    # Summary

    Verify refreshed property returns correct value before and after refresh

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.refreshed (property)

    ## Test

    - refreshed is False before calling refresh()
    - refreshed is True after calling refresh()
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

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
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()

    assert instance.refreshed is False

    with does_not_raise():
        instance.refresh()

    assert instance.refreshed is True


def test_fabric_groups_00170(fabric_groups) -> None:
    """
    # Summary

    Verify fabric_group_names property returns list of fabric group names

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.fabric_group_names (property)

    ## Test

    - fabric_group_names returns list containing "MFG1"
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

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
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()

    assert "MFG1" in instance.fabric_group_names
    assert isinstance(instance.fabric_group_names, list)


def test_fabric_groups_00171(fabric_groups) -> None:
    """
    # Summary

    Verify ValueError is raised when fabric_group_names is accessed before refresh

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups.fabric_group_names (property)

    ## Test

    - ValueError is raised with expected message
    """
    match = r"FabricGroups\.fabric_group_names: "
    match += r"Call FabricGroups\.refresh\(\) before accessing fabric_group_names\."

    with pytest.raises(ValueError, match=match):
        instance = fabric_groups
        result = instance.fabric_group_names  # pylint: disable=pointless-statement


def test_fabric_groups_00180(fabric_groups) -> None:
    """
    # Summary

    Verify _get() raises ValueError when filter is not set

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups._get()

    ## Test

    - ValueError is raised with expected message
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    match = r"FabricGroups\._get: "
    match += r"set instance\.filter to a fabric name "
    match += r"before accessing property fabricId\."

    with does_not_raise():
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()

    with pytest.raises(ValueError, match=match):
        result = instance._get("fabricId")


def test_fabric_groups_00181(fabric_groups) -> None:
    """
    # Summary

    Verify _get() raises ValueError with non-existent fabric group name

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups._get()

    ## Test

    - ValueError is raised with expected message
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    match = r"FabricGroups\._get: "
    match += r"fabric_name NON_EXISTENT does not exist on the controller\."

    with does_not_raise():
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        instance.filter = "NON_EXISTENT"

    with pytest.raises(ValueError, match=match):
        result = instance._get("fabricId")


def test_fabric_groups_00182(fabric_groups) -> None:
    """
    # Summary

    Verify _get() raises ValueError with invalid property name

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups._get()

    ## Test

    - ValueError is raised with expected message
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    match = r"FabricGroups\._get: "
    match += r"MFG1 unknown property name: INVALID_PROPERTY\."

    with does_not_raise():
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        instance.filter = "MFG1"

    with pytest.raises(ValueError, match=match):
        result = instance._get("INVALID_PROPERTY")


def test_fabric_groups_00190(fabric_groups) -> None:
    """
    # Summary

    Verify _get_nv_pair() raises ValueError when filter is not set

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups._get_nv_pair()

    ## Test

    - ValueError is raised with expected message
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    match = r"FabricGroups\._get_nv_pair: "
    match += r"set instance\.filter to a fabric name "
    match += r"before accessing property FABRIC_NAME\."

    with does_not_raise():
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()

    with pytest.raises(ValueError, match=match):
        result = instance._get_nv_pair("FABRIC_NAME")


def test_fabric_groups_00191(fabric_groups) -> None:
    """
    # Summary

    Verify _get_nv_pair() raises ValueError with non-existent fabric group name

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups._get_nv_pair()

    ## Test

    - ValueError is raised with expected message
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    match = r"FabricGroups\._get_nv_pair: "
    match += r"fabric_name NON_EXISTENT "
    match += r"does not exist on the controller\."

    with does_not_raise():
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        instance.filter = "NON_EXISTENT"

    with pytest.raises(ValueError, match=match):
        result = instance._get_nv_pair("FABRIC_NAME")


def test_fabric_groups_00192(fabric_groups) -> None:
    """
    # Summary

    Verify _get_nv_pair() raises ValueError with invalid property name

    ## Classes and Methods

    - FabricGroups.__init__()
    - FabricGroups._get_nv_pair()

    ## Test

    - ValueError is raised with expected message
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    match = r"FabricGroups\._get_nv_pair: "
    match += r"fabric_name MFG1 "
    match += r"unknown property name: INVALID_PROPERTY\."

    with does_not_raise():
        instance = fabric_groups
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        instance.filter = "MFG1"

    with pytest.raises(ValueError, match=match):
        result = instance._get_nv_pair("INVALID_PROPERTY")
