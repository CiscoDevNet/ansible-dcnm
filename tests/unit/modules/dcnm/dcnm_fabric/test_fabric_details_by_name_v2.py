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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.lan_fabric.rest.control.fabrics.fabrics import \
    EpFabrics
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils
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
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    ResponseGenerator, does_not_raise, fabric_details_by_name_v2_fixture,
    responses_fabric_details_by_name_v2)

PARAMS = {"state": "query", "check_mode": False}


def test_fabric_details_by_name_v2_00200(fabric_details_by_name_v2) -> None:
    """
    ### Classes and Methods
    - FabricDetails()
        - __init__()
        - refresh_super()

    ### Summary
    - Verify property access after 200 controller response:
        -   RETURN_CODE is 200.
        -   Controller response contains one fabric (f1).

    ### Code Flow - Setup
    -   FabricDetails() is instantiated
    -   FabricDetails().RestSend() is instantiated
    -   FabricDetails().Results() is instantiated
    -   FabricDetails().refresh_super() is called
    -   responses_FabricDetails contains a dict with:
        - RETURN_CODE == 200
        - DATA == [<fabric_info from controller>]

    ###Code Flow - Test
    -   FabricDetails().refresh_super() is called.
    -   All properties are accessed and verified.

    ### Expected Result
    -   Exception is not raised.
    -   All properties return expected values.
    -   Results() are updated.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_details_by_name_v2(key)

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    rest_send = RestSend(PARAMS)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    rest_send.unit_test = True
    rest_send.timeout = 1

    with does_not_raise():
        instance = fabric_details_by_name_v2
        instance.rest_send = rest_send
        instance.results = Results()
        instance.filter = "f1"

    with does_not_raise():
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

    assert instance.all_data.get("f1", {}).get("asn", None) == "65001"
    assert instance.all_data.get("f1", {}).get("nvPairs", {}).get("FABRIC_NAME") == "f1"

    assert instance.asn == "65001"
    assert instance.deployment_freeze is False
    assert instance.enable_pbr is False
    assert instance.fabric_id == "FABRIC-2"
    assert instance.fabric_type == "Switch_Fabric"
    assert instance.is_read_only is None
    assert instance.replication_mode == "Multicast"
    assert instance.template_name == "Easy_Fabric"


def test_fabric_details_by_name_v2_00300(fabric_details_by_name_v2) -> None:
    """
    ### Classes and Methods
    - FabricDetails()
        - __init__()
        - refresh()

    ### Summary
    -   Verify properties return None if property is missing in the
        controller response.
        -   RETURN_CODE is 200.
        -   Controller response contains one fabric (f1).

    ### Setup - Code
    -   FabricDetailsByName() is instantiated
    -   FabricDetailsByName().RestSend() is instantiated
    -   FabricDetailsByName().Results() is instantiated
    -   FabricDetailsByName().refresh() is called

    ### Setup - Data
    -   responses_FabricDetailsByName_V2 contains a dict with:
        - RETURN_CODE == 200
        - DATA[0].nvPairs.FABRIC_NAME == "f1"
        - DATA[0].nvPairs <all other properties are missing>

    ### Expected Result
    -   ``ValueError`` is raised for each property.
    -   Results() are updated.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_details_by_name_v2(key)

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    rest_send = RestSend(PARAMS)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    rest_send.unit_test = True
    rest_send.timeout = 1

    with does_not_raise():
        instance = fabric_details_by_name_v2
        instance.rest_send = rest_send
        instance.results = Results()
        instance.filter = "f1"
        instance.refresh()

    assert instance.asn is None
    assert instance.bgp_as is None
    assert instance.deployment_freeze is None
    assert instance.enable_pbr is None
    assert instance.fabric_id is None
    assert instance.fabric_type is None
    assert instance.is_read_only is None
    assert instance.replication_mode is None
    assert instance.template_name is None
