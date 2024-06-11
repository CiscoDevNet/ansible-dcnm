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

import copy
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
    FabricDetailsByNvPair
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    ResponseGenerator, does_not_raise, fabric_details_by_nv_pair_v2_fixture,
    responses_fabric_details_by_nv_pair_v2)

PARAMS = {"state": "query", "check_mode": False}


def test_fabric_details_by_nv_pair_v2_00000(monkeypatch) -> None:
    """
    ### Classes and Methods
    - FabricDetailsByNvPair()
        - __init__()

    ### Summary
    -   Verify that __init__ raises ``ValueError`` if ``super().__init__``
        raises ``ValueError``

    ### Setup - Code
    -   None

    ### Setup - Data
    -   params is modified to remove ``check_mode``.

    ### Trigger
    -   FabricDetailsByNvPair() is instantiated.

    ### Expected Result
    -   FabricDetailsByNvPair().__init__() raises ``ValueError`` because
        FabricDetails().__init__() raises ``ValueError`` because params
        is missing mandatory key ``check_mode``.
    -   Error message matches expectation.
    """
    match = r"FabricDetailsByNvPair\.__init__:\s+"
    match += r"Failed in super\(\)\.__init__\(\)\.\s+"
    match += r"Error detail: FabricDetailsByNvPair\.__init__:\s+"
    match += r"check_mode is missing from params\. params:.*"
    params = copy.copy(PARAMS)
    params.pop("check_mode", None)
    with pytest.raises(ValueError, match=match):
        FabricDetailsByNvPair(params)  # pytest: disable=pointless-statement


def test_fabric_details_by_nv_pair_v2_00200(fabric_details_by_nv_pair_v2) -> None:
    """
    ### Classes and Methods
    - FabricDetailsByNvPair()
        - __init__()
        - refresh_super()

    ### Summary
    - Verify nvPair access after 200 controller response.

    ### Setup - Code
    -   Sender() is initialized and configured.
    -   RestSend() is initialized and configured.
    -   FabricDetailsByNvPair() is instantiated and configured.
    -   FabricDetailsByNvPair().refresh() is called.

    ### Setup - Data
    -   responses_FabricDetailsByNvPair_V2 contains a response with
        -   3x fabrics
        -   2x fabrics that match filter_key and filter_value
        -   1x fabrics do not match filter_key and filter_value.
        -   RETURN_CODE == 200
        -   DATA == [<3x fabrics>]

    ### Trigger
    -   FabricDetailsByNvPair().filtered_data is accessed

    ### Expected Result
    -   Exception is not raised.
    -   All fabrics matching ``filter_key`` and ``filter_value``
        are returned in ``filtered_data``.
    -   ``Results()`` are updated.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_details_by_nv_pair_v2(key)

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    rest_send = RestSend(PARAMS)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    rest_send.unit_test = True
    rest_send.timeout = 1

    with does_not_raise():
        instance = fabric_details_by_nv_pair_v2
        instance.rest_send = rest_send
        instance.results = Results()
        instance.filter_key = "FEATURE_PTP"
        instance.filter_value = "false"
        instance.refresh()

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

    assert (
        instance.filtered_data.get("f1", {}).get("nvPairs", {}).get("FEATURE_PTP", None)
        == "false"
    )
    assert (
        instance.filtered_data.get("f2", {}).get("nvPairs", {}).get("FEATURE_PTP", None)
        == "false"
    )
    assert (
        instance.filtered_data.get("f3", {}).get("nvPairs", {}).get("FEATURE_PTP", None)
        is None
    )


# def test_fabric_details_by_nv_pair_v2_00300(fabric_details_by_nv_pair_v2) -> None:
#     """
#     ### Classes and Methods
#     - FabricDetailsByNvPair()
#         - __init__()
#         - refresh()

#     ### Summary
#     -   Verify missing nvPairs items ``None``.

#     ### Setup - Code
#     -   FabricDetailsByNvPair() is instantiated
#     -   FabricDetailsByNvPair().RestSend() is instantiated
#     -   FabricDetailsByNvPair().Results() is instantiated
#     -   FabricDetailsByNvPair().refresh() is called

#     ### Setup - Data
#     -   responses_FabricDetailsByNvPair_V2 contains a dict with:
#         - RETURN_CODE == 200
#         - DATA[0].nvPairs.FABRIC_NAME == "f1"
#         - DATA[0].nvPairs <all other properties are missing>

#     ### Trigger
#     -   All supported properties are accessed and verified.

#     ### Expected Result
#     -   All supported properties return ``None``.
#     """
#     method_name = inspect.stack()[0][3]
#     key = f"{method_name}a"

#     def responses():
#         yield responses_fabric_details_by_nv_pair_v2(key)

#     sender = Sender()
#     sender.gen = ResponseGenerator(responses())
#     rest_send = RestSend(PARAMS)
#     rest_send.response_handler = ResponseHandler()
#     rest_send.sender = sender
#     rest_send.unit_test = True
#     rest_send.timeout = 1

#     with does_not_raise():
#         instance = fabric_details_by_nv_pair_v2
#         instance.rest_send = rest_send
#         instance.results = Results()
#         instance.filter = "f1"
#         instance.refresh()

#     assert instance.asn is None
#     assert instance.bgp_as is None
#     assert instance.deployment_freeze is None
#     assert instance.enable_pbr is None
#     assert instance.fabric_id is None
#     assert instance.fabric_type is None
#     assert instance.is_read_only is None
#     assert instance.replication_mode is None
#     assert instance.template_name is None


# def test_fabric_details_by_nv_pair_v2_00400(fabric_details_by_nv_pair_v2) -> None:
#     """
#     ### Classes and Methods
#     - FabricDetailsByNvPair()
#         - __init__()
#         - refresh()

#     ### Summary
#     -   Verify refresh() raises ``ValueError`` if
#         ``FabricDetails().refresh_super()`` raises ``ValueError``.
#         -   RETURN_CODE is 200.
#         -   Controller response contains one fabric (f1).

#     ### Setup - Code
#     -   FabricDetailsByNvPair() is instantiated
#     -   FabricDetailsByNvPair().RestSend() is instantiated
#     -   FabricDetailsByNvPair().Results() is NOT instantiated.

#     ### Setup - Data
#     -   None

#     ### Expected Result
#     -   ``ValueException`` is raised by ``refresh_super()`` and caught by
#         ``refresh()``.
#     """
#     with does_not_raise():
#         instance = fabric_details_by_nv_pair_v2
#         instance.rest_send = RestSend(PARAMS)
#         instance.filter = "f1"

#     match = r"Failed to refresh fabric details:\s+"
#     match += r"Error detail:\s+"
#     match += r"FabricDetailsByNvPair\.validate_refresh_parameters:\s+"
#     match += r"FabricDetailsByNvPair\.results must be set before calling\s+"
#     match += r"FabricDetailsByNvPair\.refresh\(\)\..*"
#     with pytest.raises(ValueError, match=match):
#         instance.refresh()


# def test_fabric_details_by_nv_pair_v2_00500(fabric_details_by_nv_pair_v2) -> None:
#     """
#     ### Classes and Methods
#     - FabricDetailsByNvPair()
#         - __init__()
#         - refresh()
#         - _get_nv_pair()
#         - bgp_as.getter

#     ### Summary
#     -   Verify that property getters for ``nvPairs`` items return ``None``
#         when ``_get_nv_pair()`` raises ``ValueError`` because ``filter``
#         is not set prior to accessing a property.

#     ### Setup - Code
#     -   Sender() is instantiated and configured.
#     -   RestSend() is instantiated and configured.
#     -   Results() is instantiated.
#     -   FabricDetailsByNvPair() is instantiated and configured.
#     -   FabricDetailsByNvPair().refresh() is called.

#     ### Setup - Data
#     -   responses() yields a 200 response.

#     ### Trigger
#     ``bgp_as`` is accessed before setting ``filter``.

#     ### Expected Result
#     -   ``_get_nv_pair()`` raises ``ValueError``.
#     -   ``bgp_as.getter`` catches ``ValueError`` and returns ``None``.
#     """
#     method_name = inspect.stack()[0][3]
#     key = f"{method_name}a"

#     def responses():
#         yield responses_fabric_details_by_nv_pair_v2(key)

#     sender = Sender()
#     sender.gen = ResponseGenerator(responses())
#     rest_send = RestSend(PARAMS)
#     rest_send.sender = sender
#     rest_send.response_handler = ResponseHandler()
#     with does_not_raise():
#         instance = fabric_details_by_nv_pair_v2
#         instance.rest_send = rest_send
#         instance.results = Results()
#         instance.refresh()
#         bgp_as = instance.bgp_as
#     assert bgp_as is None


# def test_fabric_details_by_nv_pair_v2_00510(fabric_details_by_nv_pair_v2) -> None:
#     """
#     ### Classes and Methods
#     - FabricDetailsByNvPair()
#         - __init__()
#         - refresh()
#         - _get_nv_pair()
#         - bgp_as.getter

#     ### Summary
#     -   Verify that property getters for ``nvPairs`` items return ``None``
#         when ``_get_nv_pair()`` raises ``ValueError`` because fabric
#         does not exist.

#     ### Setup - Code
#     -   Sender() is instantiated and configured.
#     -   RestSend() is instantiated and configured.
#     -   Results() is instantiated.
#     -   FabricDetailsByNvPair() is instantiated and configured.
#     -   FabricDetailsByNvPair().refresh() is called.

#     ### Setup - Data
#     -   responses() yields a 200 response that does not contain any fabrics.

#     ### Trigger
#     ``bgp_as`` is accessed.

#     ### Expected Result
#     -   ``_get_nv_pair()`` raises ``ValueError``.
#     -   ``bgp_as.getter`` catches ``ValueError`` and returns ``None``.
#     """
#     method_name = inspect.stack()[0][3]
#     key = f"{method_name}a"

#     def responses():
#         yield responses_fabric_details_by_nv_pair_v2(key)

#     sender = Sender()
#     sender.gen = ResponseGenerator(responses())
#     rest_send = RestSend(PARAMS)
#     rest_send.sender = sender
#     rest_send.response_handler = ResponseHandler()
#     with does_not_raise():
#         instance = fabric_details_by_nv_pair_v2
#         instance.rest_send = rest_send
#         instance.results = Results()
#         instance.refresh()
#         instance.filter = "FABRIC_DOES_NOT_EXIST"
#         bgp_as = instance.bgp_as
#     assert bgp_as is None


# def test_fabric_details_by_nv_pair_v2_00600(fabric_details_by_nv_pair_v2) -> None:
#     """
#     ### Classes and Methods
#     - FabricDetailsByNvPair()
#         - __init__()
#         - refresh()
#         - filtered_data.getter

#     ### Summary
#     -   Verify that ``filtered_data`` property getter raises ``ValueError``
#         when ``filter`` is not set.

#     ### Setup - Code
#     -   Sender() is instantiated and configured.
#     -   RestSend() is instantiated and configured.
#     -   Results() is instantiated.
#     -   FabricDetailsByNvPair() is instantiated and configured.
#     -   FabricDetailsByNvPair().refresh() is called.

#     ### Setup - Data
#     -   responses() yields a 200 response.

#     ### Trigger
#     ``filtered_data.getter`` is accessed.

#     ### Expected Result
#     -   ``filtered_data.getter`` raises ``ValueError``.
#     """
#     method_name = inspect.stack()[0][3]
#     key = f"{method_name}a"

#     def responses():
#         yield responses_fabric_details_by_nv_pair_v2(key)

#     sender = Sender()
#     sender.gen = ResponseGenerator(responses())
#     rest_send = RestSend(PARAMS)
#     rest_send.sender = sender
#     rest_send.response_handler = ResponseHandler()
#     with does_not_raise():
#         instance = fabric_details_by_nv_pair_v2
#         instance.rest_send = rest_send
#         instance.results = Results()
#         instance.refresh()
#     match = r"FabricDetailsByNvPair\.filtered_data:\s+"
#     match += r"FabricDetailsByNvPair\.filter must be set\s+"
#     match += r"before accessing FabricDetailsByNvPair\.filtered_data\."
#     with pytest.raises(ValueError, match=match):
#         instance.filtered_data  # pylint: disable=pointless-statement


# def test_fabric_details_by_nv_pair_v2_00610(fabric_details_by_nv_pair_v2) -> None:
#     """
#     ### Classes and Methods
#     - FabricDetailsByNvPair()
#         - __init__()
#         - refresh()
#         - filtered_data.getter

#     ### Summary
#     -   Verify that ``filtered_data`` property returns expected values
#         when ``filter`` is set and matches a fabric on the controller.

#     ### Setup - Code
#     -   Sender() is instantiated and configured.
#     -   RestSend() is instantiated and configured.
#     -   Results() is instantiated.
#     -   FabricDetailsByNvPair() is instantiated and configured.
#     -   FabricDetailsByNvPair().refresh() is called.

#     ### Setup - Data
#     -   responses() yields a 200 response with a matching fabric.

#     ### Trigger
#     ``filtered_data.getter`` is accessed.

#     ### Expected Result
#     -   ``filtered_data.getter`` returns expected value.
#     """
#     method_name = inspect.stack()[0][3]
#     key = f"{method_name}a"

#     def responses():
#         yield responses_fabric_details_by_nv_pair_v2(key)

#     sender = Sender()
#     sender.gen = ResponseGenerator(responses())
#     rest_send = RestSend(PARAMS)
#     rest_send.sender = sender
#     rest_send.response_handler = ResponseHandler()
#     with does_not_raise():
#         instance = fabric_details_by_nv_pair_v2
#         instance.rest_send = rest_send
#         instance.results = Results()
#         instance.refresh()
#         instance.filter = "MATCHING_FABRIC"
#         data = instance.filtered_data
#     assert data.get("nvPairs", {}).get("BGP_AS") == "65001"
#     assert data.get("nvPairs", {}).get("ENABLE_NETFLOW") == "false"


# def test_fabric_details_by_nv_pair_v2_00700(fabric_details_by_nv_pair_v2) -> None:
#     """
#     ### Classes and Methods
#     - FabricDetailsByNvPair()
#         - __init__()
#         - refresh()
#         - _get()
#         - template_name.getter

#     ### Summary
#     -   Verify that property getters for top-level items return ``None``
#         when ``_get()`` raises ``ValueError`` because ``filter``
#         is not set prior to accessing a property.

#     ### Setup - Code
#     -   Sender() is instantiated and configured.
#     -   RestSend() is instantiated and configured.
#     -   Results() is instantiated.
#     -   FabricDetailsByNvPair() is instantiated and configured.
#     -   FabricDetailsByNvPair().refresh() is called.

#     ### Setup - Data
#     -   responses() yields a 200 response.

#     ### Trigger
#     ``template_name`` is accessed before setting ``filter``.

#     ### Expected Result
#     -   ``_get()`` raises ``ValueError``.
#     -   ``template_name.getter`` catches ``ValueError`` and returns ``None``.
#     """
#     method_name = inspect.stack()[0][3]
#     key = f"{method_name}a"

#     def responses():
#         yield responses_fabric_details_by_nv_pair_v2(key)

#     sender = Sender()
#     sender.gen = ResponseGenerator(responses())
#     rest_send = RestSend(PARAMS)
#     rest_send.sender = sender
#     rest_send.response_handler = ResponseHandler()
#     with does_not_raise():
#         instance = fabric_details_by_nv_pair_v2
#         instance.rest_send = rest_send
#         instance.results = Results()
#         instance.refresh()
#         template_name = instance.template_name
#     assert template_name is None


# def test_fabric_details_by_nv_pair_v2_00710(fabric_details_by_nv_pair_v2) -> None:
#     """
#     ### Classes and Methods
#     - FabricDetailsByNvPair()
#         - __init__()
#         - refresh()
#         - _get()
#         - template_name.getter

#     ### Summary
#     -   Verify that property getters for top-level items return ``None``
#         when ``_get()`` raises ``ValueError`` because fabric
#         does not exist.

#     ### Setup - Code
#     -   Sender() is instantiated and configured.
#     -   RestSend() is instantiated and configured.
#     -   Results() is instantiated.
#     -   FabricDetailsByNvPair() is instantiated and configured.
#     -   FabricDetailsByNvPair().refresh() is called.

#     ### Setup - Data
#     -   responses() yields a 200 response that does not contain any fabrics.

#     ### Trigger
#     ``template_name.getter`` is accessed.

#     ### Expected Result
#     -   ``_get()`` raises ``ValueError``.
#     -   ``template_name.getter`` catches ``ValueError`` and returns ``None``.
#     """
#     method_name = inspect.stack()[0][3]
#     key = f"{method_name}a"

#     def responses():
#         yield responses_fabric_details_by_nv_pair_v2(key)

#     sender = Sender()
#     sender.gen = ResponseGenerator(responses())
#     rest_send = RestSend(PARAMS)
#     rest_send.sender = sender
#     rest_send.response_handler = ResponseHandler()
#     with does_not_raise():
#         instance = fabric_details_by_nv_pair_v2
#         instance.rest_send = rest_send
#         instance.results = Results()
#         instance.refresh()
#         instance.filter = "FABRIC_DOES_NOT_EXIST"
#         template_name = instance.template_name
#     assert template_name is None
