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
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    does_not_raise, fabric_details_by_nv_pair_v2_fixture,
    responses_fabric_details_by_nv_pair_v2)

PARAMS = {"state": "query", "check_mode": False}


def test_fabric_details_by_nv_pair_v2_00000(fabric_details_by_nv_pair_v2) -> None:
    """
    ### Classes and Methods
    - FabricDetailsByNvPair()
        - __init__()

    ### Summary
    -   Verify instance attributes are set correctly.

    ### Setup - Code
    -   None

    ### Setup - Data
    -   None

    ### Trigger
    -   FabricDetailsByNvPair() is instantiated.

    ### Expected Result
    -   Instance attribute values are as expected.
    -   No expections are raised.
    """
    with does_not_raise():
        instance = fabric_details_by_nv_pair_v2
    assert instance.rest_send is None
    assert instance.results is None
    assert instance.filter_key is None
    assert instance.filter_value is None
    assert instance.filtered_data == {}


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


def test_fabric_details_by_nv_pair_v2_00210(fabric_details_by_nv_pair_v2) -> None:
    """
    ### Classes and Methods
    - FabricDetailsByNvPair()
        - __init__()
        - refresh_super()

    ### Summary
    -   Negative test case.
    -   Verify behavior when FABRIC_NAME is missing from nvPairs.

    ### Setup - Code
    -   Sender() is initialized and configured.
    -   RestSend() is initialized and configured.
    -   FabricDetailsByNvPair() is instantiated and configured.
    -   FabricDetailsByNvPair().refresh() is called.

    ### Setup - Data
    -   responses_FabricDetailsByNvPair_V2 contains a response with
        -   1x fabrics
        -   RETURN_CODE == 200
        -   DATA[0].nvPairs is missing FABRIC_NAME key/value.

    ### Trigger
    -   FabricDetailsByNvPair().refresh() is called.

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
        instance.filter_key = "SOME_KEY"
        instance.filter_value = "SOME_VALUE"
        instance.refresh()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.result) == 1
    assert len(instance.results.response) == 1

    assert True in instance.results.failed
    assert False not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_fabric_details_by_nv_pair_v2_00400(fabric_details_by_nv_pair_v2) -> None:
    """
    ### Classes and Methods
    - FabricDetailsByNvPair()
        - __init__()
        - refresh()

    ### Summary
    -   Verify refresh() raises ``ValueError`` if
        ``FabricDetails().refresh_super()`` raises ``ValueError``.
        -   RETURN_CODE is 200.
        -   Controller response contains one fabric (f1).

    ### Setup - Code
    -   FabricDetailsByNvPair() is instantiated
    -   FabricDetailsByNvPair().RestSend() is instantiated
    -   FabricDetailsByNvPair().Results() is NOT instantiated.

    ### Setup - Data
    -   None

    ### Expected Result
    -   ``ValueException`` is raised by ``refresh_super()`` and caught by
        ``refresh()``.
    """
    with does_not_raise():
        instance = fabric_details_by_nv_pair_v2
        instance.rest_send = RestSend(PARAMS)
        instance.filter_key = "SOME_KEY"
        instance.filter_value = "SOME_VALUE"

    match = r"Failed to refresh fabric details:\s+"
    match += r"Error detail:\s+"
    match += r"FabricDetailsByNvPair\.validate_refresh_parameters:\s+"
    match += r"FabricDetailsByNvPair\.results must be set before\s+"
    match += r"calling FabricDetailsByNvPair\.refresh\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_fabric_details_by_nv_pair_v2_00600(fabric_details_by_nv_pair_v2) -> None:
    """
    ### Classes and Methods
    - FabricDetailsByNvPair()
        - __init__()
        - refresh()

    ### Summary
    -   Verify that ``refresh()`` raises ``ValueError``
        when ``filter_key`` is not set.

    ### Setup - Code
    -   Sender() is instantiated and configured.
    -   RestSend() is instantiated and configured.
    -   Results() is instantiated.
    -   FabricDetailsByNvPair() is instantiated and configured.
    -   FabricDetailsByNvPair().filter_value is set

    ### Setup - Data
    -   responses() yields empty dict (i.e. a noop)

    ### Trigger
    -   FabricDetailsByNvPair().refresh() is called.

    ### Expected Result
    -   ``refresh()`` raises ``ValueError`` because ``filter_key`` is not set.
    """

    def responses():
        yield {}

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    rest_send = RestSend(PARAMS)
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()
    with does_not_raise():
        instance = fabric_details_by_nv_pair_v2
        instance.rest_send = rest_send
        instance.results = Results()
        instance.filter_value = "SOME_VALUE"
    match = r"FabricDetailsByNvPair\.refresh:\s+"
    match += r"set FabricDetailsByNvPair\.filter_key\s+"
    match += r"to a nvPair key before calling\s+"
    match += r"FabricDetailsByNvPair\.refresh\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_fabric_details_by_nv_pair_v2_00610(fabric_details_by_nv_pair_v2) -> None:
    """
    ### Classes and Methods
    - FabricDetailsByNvPair()
        - __init__()
        - refresh()

    ### Summary
    -   Verify that ``refresh()`` raises ``ValueError``
        when ``filter_value`` is not set.

    ### Setup - Code
    -   Sender() is instantiated and configured.
    -   RestSend() is instantiated and configured.
    -   Results() is instantiated.
    -   FabricDetailsByNvPair() is instantiated and configured.
    -   FabricDetailsByNvPair().filter_key is set

    ### Setup - Data
    -   responses() yields empty dict (i.e. a noop)

    ### Trigger
    -   FabricDetailsByNvPair().refresh() is called.

    ### Expected Result
    -   ``refresh()`` raises ``ValueError`` because ``filter_value`` is not set.
    """

    def responses():
        yield {}

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    rest_send = RestSend(PARAMS)
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()
    with does_not_raise():
        instance = fabric_details_by_nv_pair_v2
        instance.rest_send = rest_send
        instance.results = Results()
        instance.filter_key = "SOME_KEY"
    match = r"FabricDetailsByNvPair\.refresh:\s+"
    match += r"set FabricDetailsByNvPair\.filter_value\s+"
    match += r"to a nvPair value before calling\s+"
    match += r"FabricDetailsByNvPair\.refresh\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()
