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
Unit tests for FabricGroupDetails class in module_utils/fabric_group/fabric_group_details.py
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
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric_group.fabric_groups import FabricGroups
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric_group.utils import (
    MockAnsibleModule,
    does_not_raise,
    params,
    responses_fabric_group_details,
    responses_fabric_groups,
)


@pytest.fixture(name="fabric_group_details")
def fabric_group_details_fixture():
    """
    Return FabricGroupDetails() instance.
    """
    return FabricGroupDetails()


def test_fabric_group_details_00000(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()

    ### Test
    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_group_details
    assert instance.class_name == "FabricGroupDetails"
    assert instance.action == "fabric_group_details"
    assert instance.data == {}
    assert instance.data_subclass == {}
    assert instance._fabric_group_name == ""
    assert instance._refreshed is False


def test_fabric_group_details_00010(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - fabric_group_name setter

    ### Summary
    - Verify that fabric_group_name is set to expected value
    - Exception is not raised

    ### Test
    - fabric_group_name is set to "MFG1"
    - fabric_group_name is returned as "MFG1"
    """
    with does_not_raise():
        instance = fabric_group_details
        instance.fabric_group_name = "MFG1"
    assert instance.fabric_group_name == "MFG1"


def test_fabric_group_details_00020(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - rest_send setter/getter

    ### Summary
    - Verify that rest_send is set to expected value
    - Exception is not raised

    ### Test
    - rest_send is set to RestSend() instance
    - rest_send is returned as RestSend() instance
    """
    with does_not_raise():
        instance = fabric_group_details
        rest_send = RestSend(params)
        instance.rest_send = rest_send
    assert instance.rest_send == rest_send


def test_fabric_group_details_00021(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - rest_send getter

    ### Summary
    - Verify that ValueError is raised when rest_send is accessed before being set

    ### Test
    - ValueError is raised with expected message
    """
    match = r"FabricGroupDetails\.rest_send: "
    match += r"rest_send property should be set before accessing\."

    with pytest.raises(ValueError, match=match):
        instance = fabric_group_details
        result = instance.rest_send  # pylint: disable=pointless-statement


def test_fabric_group_details_00030(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - results setter/getter

    ### Summary
    - Verify that results is set to expected value
    - Exception is not raised

    ### Test
    - results is set to Results() instance
    - results is returned as Results() instance
    - results properties are set correctly
    """
    with does_not_raise():
        instance = fabric_group_details
        results = Results()
        instance.results = results
    assert instance.results == results
    assert instance.results.action == "fabric_group_details"
    assert False in instance.results.changed


def test_fabric_group_details_00031(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - results getter

    ### Summary
    - Verify that ValueError is raised when results is accessed before being set

    ### Test
    - ValueError is raised with expected message
    """
    match = r"FabricGroupDetails\.results: "
    match += r"results property should be set before accessing\."

    with pytest.raises(ValueError, match=match):
        instance = fabric_group_details
        result = instance.results  # pylint: disable=pointless-statement


def test_fabric_group_details_00040(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - refresh()

    ### Summary
    - Verify behavior when refresh() is called and fabric group exists on controller
    - RETURN_CODE is 200

    ### Code Flow
    - FabricGroupDetails.fabric_group_name is set to "MFG1"
    - FabricGroupDetails.refresh() is called
    - FabricGroupDetails.refresh() calls fabric_group_exists() which returns True
    - FabricGroupDetails.refresh() calls RestSend().commit() which sets
      RestSend().response_current to a dict with keys DATA, RETURN_CODE, MESSAGE
    - FabricGroupDetails.refresh() calls build_data() which populates self.data
    - FabricGroupDetails.refresh() sets self._refreshed to True
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")
        yield responses_fabric_group_details(f"{key}")

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
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MFG1"
        instance.refresh()

    assert instance._refreshed is True
    assert instance.data.get("MFG1") is not None
    assert instance.data["MFG1"]["fabricName"] == "MFG1"
    assert instance.data["MFG1"]["fabricId"] == "MC-FABRIC-69"
    assert instance.data["MFG1"]["nvPairs"]["FABRIC_NAME"] == "MFG1"
    assert instance.data["MFG1"]["nvPairs"]["FABRIC_TYPE"] == "MFD"


def test_fabric_group_details_00041(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - refresh()

    ### Summary
    - Verify behavior when refresh() is called and fabric group does not exist on controller

    ### Code Flow
    - FabricGroupDetails.fabric_group_name is set to "MFG1"
    - FabricGroupDetails.refresh() is called
    - FabricGroupDetails.refresh() calls fabric_group_exists() which returns False
    - FabricGroupDetails.refresh() sets self.data to empty dict
    - FabricGroupDetails.refresh() sets self._refreshed to True
    - No REST call is made to get fabric group details
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
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MFG1"
        instance.refresh()

    assert instance._refreshed is True
    assert instance.data == {}


def test_fabric_group_details_00050(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - all_data property

    ### Summary
    - Verify that all_data returns all fabric group data

    ### Test
    - all_data returns self.data
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")
        yield responses_fabric_group_details(f"{key}")

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
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MFG1"
        instance.refresh()

    assert instance.all_data == instance.data
    assert instance.all_data.get("MFG1") is not None


def test_fabric_group_details_00060(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - filtered_data property

    ### Summary
    - Verify that filtered_data returns data for specified fabric group

    ### Test
    - filtered_data returns data for fabric group "MFG1"
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")
        yield responses_fabric_group_details(f"{key}")

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
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MFG1"
        instance.refresh()

    assert instance.filtered_data.get("fabricName") == "MFG1"
    assert instance.filtered_data.get("fabricId") == "MC-FABRIC-69"


def test_fabric_group_details_00061(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - filtered_data property

    ### Summary
    - Verify that ValueError is raised when filtered_data is accessed without
      setting fabric_group_name

    ### Test
    - ValueError is raised with expected message
    """
    match = r"FabricGroupDetails\.filtered_data: "
    match += r"FabricGroupDetails\.fabric_group_name must be set before accessing "
    match += r"FabricGroupDetails\.filtered_data\."

    with pytest.raises(ValueError, match=match):
        instance = fabric_group_details
        result = instance.filtered_data  # pylint: disable=pointless-statement


def test_fabric_group_details_00062(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - filtered_data property

    ### Summary
    - Verify that filtered_data returns empty dict when fabric group does not exist

    ### Test
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
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MFG1"
        instance.refresh()

    assert instance.filtered_data == {}


def test_fabric_group_details_00070(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - asn property

    ### Summary
    - Verify that asn property returns BGP_AS value from nvPairs

    ### Test
    - asn returns empty string (BGP_AS is empty in test data)
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")
        yield responses_fabric_group_details(f"{key}")

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
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MFG1"
        instance.refresh()

    assert instance.asn == ""
    assert instance.bgp_as == ""


def test_fabric_group_details_00080(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - deployment_freeze property

    ### Summary
    - Verify that deployment_freeze property returns DEPLOYMENT_FREEZE value from nvPairs

    ### Test
    - deployment_freeze returns False
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")
        yield responses_fabric_group_details(f"{key}")

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
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MFG1"
        instance.refresh()

    # DEPLOYMENT_FREEZE is not in the test data, so it should return False
    assert instance.deployment_freeze is False


def test_fabric_group_details_00090(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - enable_pbr property

    ### Summary
    - Verify that enable_pbr property returns ENABLE_PBR value from nvPairs

    ### Test
    - enable_pbr returns False
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")
        yield responses_fabric_group_details(f"{key}")

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
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MFG1"
        instance.refresh()

    # ENABLE_PBR is not in the test data, so it should return False
    assert instance.enable_pbr is False


def test_fabric_group_details_00100(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - fabric_id property

    ### Summary
    - Verify that fabric_id property returns fabricId value

    ### Test
    - fabric_id returns "MC-FABRIC-69"
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")
        yield responses_fabric_group_details(f"{key}")

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
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MFG1"
        instance.refresh()

    assert instance.fabric_id == "MC-FABRIC-69"


def test_fabric_group_details_00110(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - fabric_type property

    ### Summary
    - Verify that fabric_type property returns FABRIC_TYPE value from nvPairs

    ### Test
    - fabric_type returns "MFD"
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")
        yield responses_fabric_group_details(f"{key}")

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
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MFG1"
        instance.refresh()

    assert instance.fabric_type == "MFD"


def test_fabric_group_details_00120(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - is_read_only property

    ### Summary
    - Verify that is_read_only property returns IS_READ_ONLY value from nvPairs

    ### Test
    - is_read_only returns False
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")
        yield responses_fabric_group_details(f"{key}")

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
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MFG1"
        instance.refresh()

    # IS_READ_ONLY is not in the test data, so it should return False
    assert instance.is_read_only is False


def test_fabric_group_details_00130(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - per_vrf_loopback_auto_provision property

    ### Summary
    - Verify that per_vrf_loopback_auto_provision property returns
      PER_VRF_LOOPBACK_AUTO_PROVISION value from nvPairs

    ### Test
    - per_vrf_loopback_auto_provision returns False
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")
        yield responses_fabric_group_details(f"{key}")

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
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MFG1"
        instance.refresh()

    # PER_VRF_LOOPBACK_AUTO_PROVISION is not in the test data, so it should return False
    assert instance.per_vrf_loopback_auto_provision is False


def test_fabric_group_details_00140(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - replication_mode property

    ### Summary
    - Verify that replication_mode property returns REPLICATION_MODE value from nvPairs

    ### Test
    - replication_mode returns empty string
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")
        yield responses_fabric_group_details(f"{key}")

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
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MFG1"
        instance.refresh()

    # replicationMode is empty string in test data
    assert instance.replication_mode == ""


def test_fabric_group_details_00150(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - template_name property

    ### Summary
    - Verify that template_name property returns templateName value

    ### Test
    - template_name returns "MSD_Fabric"
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")
        yield responses_fabric_group_details(f"{key}")

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
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MFG1"
        instance.refresh()

    assert instance.template_name == "MSD_Fabric"


def test_fabric_group_details_00160(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - refreshed property

    ### Summary
    - Verify that refreshed property returns correct value before and after refresh

    ### Test
    - refreshed is False before calling refresh()
    - refreshed is True after calling refresh()
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")
        yield responses_fabric_group_details(f"{key}")

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
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MFG1"

    assert instance.refreshed is False

    with does_not_raise():
        instance.refresh()

    assert instance.refreshed is True


def test_fabric_group_details_00170(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - _get()

    ### Summary
    - Verify that ValueError is raised when _get() is called without setting
      fabric_group_name

    ### Test
    - ValueError is raised with expected message
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")
        yield responses_fabric_group_details(f"{key}")

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    match = r"FabricGroupDetails\._get: "
    match += r"set instance\.fabric_group_name to a fabric group name "
    match += r"before accessing property fabricId\."

    with does_not_raise():
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()

    with pytest.raises(ValueError, match=match):
        result = instance._get("fabricId")


def test_fabric_group_details_00171(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - _get()

    ### Summary
    - Verify that ValueError is raised when _get() is called with non-existent
      fabric group name

    ### Test
    - ValueError is raised with expected message
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")
        yield responses_fabric_group_details(f"{key}")

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    match = r"FabricGroupDetails\._get: "
    match += r"fabric_group_name NON_EXISTENT does not exist on the controller\."

    with does_not_raise():
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MFG1"
        instance.refresh()
        instance.fabric_group_name = "NON_EXISTENT"

    with pytest.raises(ValueError, match=match):
        result = instance._get("fabricId")


def test_fabric_group_details_00172(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - _get()

    ### Summary
    - Verify that ValueError is raised when _get() is called with invalid property name

    ### Test
    - ValueError is raised with expected message
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")
        yield responses_fabric_group_details(f"{key}")

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    match = r"FabricGroupDetails\._get: "
    match += r"MFG1 unknown property name: INVALID_PROPERTY\."

    with does_not_raise():
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MFG1"
        instance.refresh()

    with pytest.raises(ValueError, match=match):
        result = instance._get("INVALID_PROPERTY")


def test_fabric_group_details_00180(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - _get_nv_pair()

    ### Summary
    - Verify that ValueError is raised when _get_nv_pair() is called without
      setting fabric_group_name

    ### Test
    - ValueError is raised with expected message
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")
        yield responses_fabric_group_details(f"{key}")

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    match = r"FabricGroupDetails\._get_nv_pair: "
    match += r"set instance\.fabric_group_name to a fabric group name "
    match += r"before accessing property FABRIC_NAME\."

    with does_not_raise():
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()

    with pytest.raises(ValueError, match=match):
        result = instance._get_nv_pair("FABRIC_NAME")


def test_fabric_group_details_00181(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - _get_nv_pair()

    ### Summary
    - Verify that ValueError is raised when _get_nv_pair() is called with
      non-existent fabric group name

    ### Test
    - ValueError is raised with expected message
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")
        yield responses_fabric_group_details(f"{key}")

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    match = r"FabricGroupDetails\._get_nv_pair: "
    match += r"fabric_group_name NON_EXISTENT "
    match += r"does not exist on the controller\."

    with does_not_raise():
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MFG1"
        instance.refresh()
        instance.fabric_group_name = "NON_EXISTENT"

    with pytest.raises(ValueError, match=match):
        result = instance._get_nv_pair("FABRIC_NAME")


def test_fabric_group_details_00182(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - _get_nv_pair()

    ### Summary
    - Verify that ValueError is raised when _get_nv_pair() is called with
      invalid property name

    ### Test
    - ValueError is raised with expected message
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_groups(f"{key}")
        yield responses_fabric_group_details(f"{key}")

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    match = r"FabricGroupDetails\._get_nv_pair: "
    match += r"fabric_group_name MFG1 "
    match += r"unknown property name: INVALID_PROPERTY\."

    with does_not_raise():
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MFG1"
        instance.refresh()

    with pytest.raises(ValueError, match=match):
        result = instance._get_nv_pair("INVALID_PROPERTY")


def test_fabric_group_details_00190(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - fabric_group_exists()

    ### Summary
    - Verify that fabric_group_exists() returns True when fabric group exists

    ### Test
    - fabric_group_exists() returns True for "MFG1"
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
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()

    assert instance.fabric_group_exists("MFG1") is True


def test_fabric_group_details_00191(fabric_group_details) -> None:
    """
    ### Classes and Methods

    - FabricGroupDetails
        - __init__()
        - fabric_group_exists()

    ### Summary
    - Verify that fabric_group_exists() returns False when fabric group does not exist

    ### Test
    - fabric_group_exists() returns False for "NON_EXISTENT"
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
        instance = fabric_group_details
        instance.rest_send = rest_send
        instance.results = Results()

    assert instance.fabric_group_exists("NON_EXISTENT") is False
