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
# pylint: disable=unused-import
# Some fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=protected-access

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import copy
import inspect

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.lan_fabric.rest.inventory.inventory import \
    EpAllSwitches
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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.switch_details import \
    SwitchDetails
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import (
    ResponseGenerator, does_not_raise, responses_switch_details)

PARAMS = {"state": "merged", "check_mode": False}


def test_switch_details_00000() -> None:
    """
    ### Classes and Methods
    -   SwitchDetails()
            -   __init__()

    ### Summary
    -   Verify class properties are initialized to expected values
    """
    with does_not_raise():
        instance = SwitchDetails()
    assert instance.action == "switch_details"
    assert instance.class_name == "SwitchDetails"
    assert isinstance(instance.conversion, ConversionUtils)
    assert isinstance(instance.ep_all_switches, EpAllSwitches)
    assert instance.path == EpAllSwitches().path
    assert instance.verb == EpAllSwitches().verb
    assert instance._filter is None
    assert instance._info is None
    assert instance._rest_send is None
    assert instance._results is None


def test_switch_details_00100() -> None:
    """
    ### Classes and Methods
    -   SwitchDetails()
            -   validate_refresh_parameters()
            -   refresh()

    ### Summary
    Verify ``validate_refresh_parameters()`` raises ``ValueError``
    due to ``rest_send`` not being set.

    ### Setup - Code
    -   SwitchDetails() is initialized.
    -   SwitchDetails().rest_send is NOT set.
    -   SwitchDetails().results is set.

    ### Setup - Data
    None

    ### Trigger
    -   SwitchDetails().refresh() is called.

    ### Expected Result
    -   SwitchDetails().validate_refresh_parameters() raises ``ValueError``.
    -   SwitchDetails().refresh() catches and re-raises ``ValueError``.
    """
    with does_not_raise():
        instance = SwitchDetails()
        instance.results = Results()

    match = r"SwitchDetails\.refresh:\s+"
    match += r"Mandatory parameters need review\.\s+"
    match += r"Error detail:\s+"
    match += r"SwitchDetails\.validate_refresh_parameters:\s+"
    match += r"SwitchDetails\.rest_send must be set before calling\s+"
    match += r"SwitchDetails\.refresh\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_switch_details_00110() -> None:
    """
    ### Classes and Methods
    -   SwitchDetails()
            -   validate_refresh_parameters()
            -   refresh()

    ### Summary
    Verify ``validate_refresh_parameters()`` raises ``ValueError``
    due to ``results`` not being set.

    ### Setup - Code
    -   SwitchDetails() is initialized.
    -   SwitchDetails().rest_send is set.
    -   SwitchDetails().results is NOT set.

    ### Setup - Data
    None

    ### Trigger
    -   SwitchDetails().refresh() is called.

    ### Expected Result
    -   SwitchDetails().validate_refresh_parameters() raises ``ValueError``.
    -   SwitchDetails().refresh() catches and re-raises ``ValueError``.
    """
    with does_not_raise():
        instance = SwitchDetails()
        instance.rest_send = RestSend(PARAMS)

    match = r"SwitchDetails\.refresh:\s+"
    match += r"Mandatory parameters need review\.\s+"
    match += r"Error detail:\s+"
    match += r"SwitchDetails\.validate_refresh_parameters:\s+"
    match += r"SwitchDetails\.results must be set before calling\s+"
    match += r"SwitchDetails\.refresh\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_switch_details_00200() -> None:
    """
    ### Classes and Methods
    -   SwitchDetails()
            -   validate_refresh_parameters()
            -   refresh()

    ### Summary
    Verify ``refresh()`` happy path.

    ### Setup - Code
    -   Sender() is initialized and configured.
    -   RestSend() is initialized and configured.
    -   SwitchDetails() is initialized and configured.

    ### Setup - Data
    responses_switch_details() returns a response with two switches.

    ### Trigger
    -   SwitchDetails().refresh() is called.

    ### Expected Result
    -   Results() contains the expected data.
    """

    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_switch_details(key)

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    rest_send = RestSend(PARAMS)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    rest_send.unit_test = True
    rest_send.timeout = 1

    with does_not_raise():
        instance = SwitchDetails()
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
    #  pylint: disable=unsupported-membership-test
    assert False in instance.results.changed
    assert False in instance.results.failed
    #  pylint: enable=unsupported-membership-test
    assert instance.results.action == "switch_details"
    assert instance.results.response_current["MESSAGE"] == "OK"
    assert instance.results.response_current["RETURN_CODE"] == 200
    assert instance.results.response_current["DATA"][0]["ipAddress"] == "192.168.1.2"
    assert instance.results.response_current["DATA"][1]["ipAddress"] == "192.168.2.2"
    assert "192.168.1.2" in instance.info
    assert "192.168.2.2" in instance.info
    instance.filter = "192.168.1.2"
    assert instance.fabric_name == "VXLAN_Fabric"
    assert instance.hostname is None
    assert instance.is_non_nexus is False
    assert instance.logical_name == "cvd-1314-leaf"
    assert instance.managable is True
    assert instance.mode == "normal"
    assert instance.model == "N9K-C93180YC-EX"
    assert instance.oper_status == "Minor"
    assert instance.platform == "N9K"
    assert instance.release == "10.2(5)"
    assert instance.role == "leaf"
    assert instance.serial_number == "FDO123456FV"
    assert instance.source_interface == "mgmt0"
    assert instance.source_vrf == "management"
    assert instance.status == "ok"
    assert instance.switch_db_id == 123456
    assert instance.switch_role == "leaf"
    assert instance.switch_uuid == "DCNM-UUID-7654321"
    assert instance.switch_uuid_id == 7654321
    assert instance.system_mode == "Maintenance"
    instance.filter = "192.168.2.2"
    assert instance.fabric_name == "LAN_Classic_Fabric"
    assert instance.hostname is None
    assert instance.is_non_nexus is False
    assert instance.logical_name == "cvd-2314-spine"
    assert instance.managable is False
    assert instance.mode == "normal"
    assert instance.model == "N9K-C93180YC-FX"
    assert instance.oper_status == "Major"
    assert instance.platform == "N9K"
    assert instance.release == "10.2(4)"
    assert instance.role == "spine"
    assert instance.serial_number == "FD6543210FV"
    assert instance.source_interface == "Ethernet1/1"
    assert instance.source_vrf == "default"
    assert instance.status == "ok"
    assert instance.switch_db_id == 654321
    assert instance.switch_role == "spine"
    assert instance.switch_uuid == "DCNM-UUID-1234567"
    assert instance.switch_uuid_id == 1234567
    assert instance.system_mode == "Normal"


def test_switch_details_00300() -> None:
    """
    ### Classes and Methods
    -   SwitchDetails()
            -   validate_refresh_parameters()
            -   refresh()

    ### Summary
    Verify ``refresh()`` sad path where 500 response is returned.

    ### Setup - Code
    -   Sender() is initialized and configured.
    -   RestSend() is initialized and configured.
    -   SwitchDetails() is initialized and configured.

    ### Setup - Data
    responses_switch_details() returns a response with:
    -   RETURN_CODE: 500
    -   MESSAGE: "Internal Server Error".

    ### Trigger
    -   SwitchDetails().refresh() is called.

    ### Expected Result
    -   Results() contains the expected data.
    """

    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_switch_details(key)

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    rest_send = RestSend(PARAMS)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    rest_send.unit_test = True
    rest_send.timeout = 1

    with does_not_raise():
        instance = SwitchDetails()
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
    #  pylint: disable=unsupported-membership-test
    assert False in instance.results.changed
    assert True in instance.results.failed
    #  pylint: enable=unsupported-membership-test
    assert instance.results.result_current["sequence_number"] == 1
    assert instance.results.result_current["found"] is False
    assert instance.results.result_current["success"] is False
    assert instance.results.diff_current["sequence_number"] == 1
    assert instance.results.response_current["MESSAGE"] == "Internal server error"
    assert instance.results.response_current["RETURN_CODE"] == 500
    assert instance.results.response == [instance.results.response_current]
    assert instance.results.result == [instance.results.result_current]
    assert instance.results.diff == [instance.results.diff_current]
