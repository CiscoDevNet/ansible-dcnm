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
    assert instance.conversion.class_name == "ConversionUtils"
    assert instance.ep_all_switches.class_name == "EpAllSwitches"
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
    match = r"SwitchDetails\.refresh:\s+"
    match += r"Error updating results\.\s+"
    match += r"Error detail: SwitchDetails\.update_results:\s+"
    match += r"Unable to retrieve switch information from the controller\.\s+"
    match += r"Got response.*"
    with pytest.raises(ValueError, match=match):
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


def test_switch_details_00400() -> None:
    """
    ### Classes and Methods
    -   SwitchDetails()
            -   send_request()
            -   refresh()

    ### Summary
    Verify ``refresh()`` catches ``ValueError`` raised by
    ``send_request()`` when ``Sender()`` is configured to raise
    ``ValueError``.

    ### Setup - Code
    -   Sender() is initialized and configured to raise ``ValueError``.
        in ``commit()``.
    -   RestSend() is initialized and configured.
    -   SwitchDetails() is initialized and configured.

    ### Setup - Data
    responses_switch_details() returns a response with:
    -   RETURN_CODE: 500
    -   MESSAGE: "Internal Server Error".

    ### Trigger
    -   SwitchDetails().refresh() is called.

    ### Expected Result
    -   ``refresh`` re-raises ``ValueError``.
    """

    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_switch_details(key)

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    sender.raise_exception = ValueError
    sender.raise_method = "commit"
    rest_send = RestSend(PARAMS)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    rest_send.unit_test = True
    rest_send.timeout = 1

    with does_not_raise():
        instance = SwitchDetails()
        instance.rest_send = rest_send
        instance.results = Results()
    match = r"SwitchDetails\.refresh:\s+"
    match += r"Error sending request to the controller\.\s+"
    match += r"Error detail: RestSend\.commit:\s+"
    match += r"Error during commit\.\s+"
    match += r"Error details: Sender\.commit:\s+"
    match += r"Simulated ValueError\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_switch_details_00500(monkeypatch) -> None:
    """
    ### Classes and Methods
    -   SwitchDetails()
            -   update_results()
            -   refresh()

    ### Summary
    Verify ``refresh()`` catches and re-raises ``ValueError``
    raised by ``update_results()``.

    ### Setup - Code
    -   Sender() is initialized and configured.
    -   RestSend() is initialized and configured.
    -   SwitchDetails() is initialized and configured.
    -   Results() is mocked to raise ``TypeError`` in
        ``action.setter``.

    ### Setup - Data
    responses_switch_details() returns a response with:
    -   RETURN_CODE: 200
    -   MESSAGE: "OK".

    ### Trigger
    -   SwitchDetails().refresh() is called.

    ### Expected Result
    -   ``update_results`` re-raises ``TypeError``
        as ``ValueError``.
    -   ``refresh`` re-raises ``ValueError``.
    """

    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    # pylint: disable=too-few-public-methods
    class MockResults:
        """
        mock
        """

        def __init__(self):
            self.class_name = "Results"
            self._action = None

        @property
        def action(self):
            """
            mock
            """
            return self._action

        @action.setter
        def action(self, value):
            self._action = value
            raise TypeError("Results().action: simulated TypeError.")

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

    monkeypatch.setattr(instance, "results", MockResults())
    match = r"SwitchDetails\.update_results:\s+"
    match += r"Error updating results\.\s+"
    match += r"Error detail: Results\(\)\.action:\s+"
    match += r"simulated TypeError\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_switch_details_00550() -> None:
    """
    ### Classes and Methods
    -   SwitchDetails()
            -   update_results()
            -   refresh()

    ### Summary
    Verify ``refresh()`` raises ``ValueError`` when ``update_results``
    raises ``ControllerResponseError``.

    ### Setup - Code
    -   Sender() is initialized and configured.
    -   RestSend() is initialized and configured.
    -   SwitchDetails() is initialized and configured.

    ### Setup - Data
    responses_switch_details() returns a response with:
    -   RETURN_CODE: 500
    -   MESSAGE: "NOK".

    ### Trigger
    -   SwitchDetails().refresh() is called.

    ### Expected Result
    -   ``update_results`` raises ``ControllerResponseError``.
    -   ``refresh`` re-raises ``ControllerResponseError`` as ``ValueError``.
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

    match = r"SwitchDetails\.refresh:\s+"
    match += r"Error updating results\.\s+"
    match += r"Error detail:\s+"
    match += r"SwitchDetails\.update_results:\s+"
    match += r"Unable to retrieve switch information from the controller\.\s+"
    match += r"Got response.*"
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_switch_details_00600() -> None:
    """
    ### Classes and Methods
    -   SwitchDetails()
            -   _get()
            -   logical_name.getter

    ### Summary
    Verify ``_get()`` raises ``ValueError`` if ``filter`` is not
    set before accessing properties that use ``_get()``.

    ### Setup - Code
    -   SwitchDetails() is instantiated.
    -   SwitchDetails().filter is NOT set.

    ### Setup - Data
    None

    ### Trigger
    -   SwitchDetails().logical_name is accessed.

    ### Expected Result
    -   ``_get()`` raises ``ValueError``.
    """
    with does_not_raise():
        instance = SwitchDetails()
    match = r"SwitchDetails\._get:\s+"
    match += r"set instance\.filter before accessing property logicalName\."
    with pytest.raises(ValueError, match=match):
        instance.logical_name  # pylint: disable=pointless-statement


def test_switch_details_00700() -> None:
    """
    ### Classes and Methods
    -   SwitchDetails()
            -   validate_refresh_parameters()
            -   refresh()
            -   filter.setter
            -   maintenance_mode

    ### Summary
    Verify ``maintenance_mode`` raises ``ValueError`` if
    ``mode`` is ``null`` in the controller response.

    ### Setup - Code
    -   Sender() is initialized and configured.
    -   RestSend() is initialized and configured.
    -   SwitchDetails() is initialized and configured.
    -   SwitchDetails().refresh() is called.
    -   SwitchDetails().filter is set to the switch
        ip_address in the response.

    ### Setup - Data
    responses_switch_details() returns a response with one switch
    for which the ``mode`` key is set to ``null``.

    ### Trigger
    ``maintenance_mode.getter`` is accessed.

    ### Expected Result
    -   ``maintenance_mode.getter`` raises ``ValueError``
        because ``_get()`` returns None for ``mode``.
    -
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
        instance.filter = "192.168.1.2"

    match = r"SwitchDetails\.maintenance_mode:\s+"
    match += r"mode is not set\. Either 'filter' has not been set,\s+"
    match += r"or the controller response is invalid\."
    with pytest.raises(ValueError, match=match):
        instance.maintenance_mode  # pylint: disable=pointless-statement


def test_switch_details_00710() -> None:
    """
    ### Classes and Methods
    -   SwitchDetails()
            -   validate_refresh_parameters()
            -   refresh()
            -   filter.setter
            -   maintenance_mode

    ### Summary
    Verify ``maintenance_mode`` raises ``ValueError`` if
    system_mode is ``null`` in the controller response.

    ### Setup - Code
    -   Sender() is initialized and configured.
    -   RestSend() is initialized and configured.
    -   SwitchDetails() is initialized and configured.
    -   SwitchDetails().refresh() is called.
    -   SwitchDetails().filter is set to the switch
        ip_address in the response.

    ### Setup - Data
    responses_switch_details() returns a response with one switch
    for which the ``system_mode`` key is set to ``null``.

    ### Trigger
    ``maintenance_mode.getter`` is accessed.

    ### Expected Result
    -   ``maintenance_mode.getter`` raises ``ValueError``
        because ``_get()`` returns None for ``system_mode``.
    -
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
        instance.filter = "192.168.1.2"

    match = r"SwitchDetails\.maintenance_mode:\s+"
    match += r"system_mode is not set\. Either 'filter' has not been set,\s+"
    match += r"or the controller response is invalid\."
    with pytest.raises(ValueError, match=match):
        instance.maintenance_mode  # pylint: disable=pointless-statement


def test_switch_details_00720() -> None:
    """
    ### Classes and Methods
    -   SwitchDetails()
            -   validate_refresh_parameters()
            -   refresh()
            -   filter.setter
            -   maintenance_mode

    ### Summary
    Verify ``maintenance_mode`` returns "migration" if
    mode == "Migration" in the controller response.

    ### Setup - Code
    -   Sender() is initialized and configured.
    -   RestSend() is initialized and configured.
    -   SwitchDetails() is initialized and configured.
    -   SwitchDetails().refresh() is called.
    -   SwitchDetails().filter is set to the switch
        ip_address in the response.

    ### Setup - Data
    responses_switch_details() returns a response containing:
    -   1x` switch
    -   ``mode`` == Migration

    ### Trigger
    ``maintenance_mode.getter`` is accessed.

    ### Expected Result
    -   ``maintenance_mode.getter`` returns "migration"
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
        instance.filter = "192.168.1.2"
    assert instance.maintenance_mode == "migration"


def test_switch_details_00730() -> None:
    """
    ### Classes and Methods
    -   SwitchDetails()
            -   validate_refresh_parameters()
            -   refresh()
            -   filter.setter
            -   maintenance_mode

    ### Summary
    Verify ``maintenance_mode`` returns "inconsistent" if
    mode != system_mode in the controller response.

    ### Setup - Code
    -   Sender() is initialized and configured.
    -   RestSend() is initialized and configured.
    -   SwitchDetails() is initialized and configured.
    -   SwitchDetails().refresh() is called.
    -   SwitchDetails().filter is set to the switch
        ip_address in the response.

    ### Setup - Data
    responses_switch_details() returns a response containing:
    -   1x switch
    -   ``mode`` == Normal
    -   ``system_mode`` == Maintenance
    -   i.e. ``mode`` != ``system_mode``

    ### Trigger
    ``maintenance_mode.getter`` is accessed.

    ### Expected Result
    -   ``maintenance_mode.getter`` returns "inconsistent"
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
        instance.filter = "192.168.1.2"
    assert instance.maintenance_mode == "inconsistent"


def test_switch_details_00740() -> None:
    """
    ### Classes and Methods
    -   SwitchDetails()
            -   validate_refresh_parameters()
            -   refresh()
            -   filter.setter
            -   maintenance_mode

    ### Summary
    Verify ``maintenance_mode`` returns "maintenance" if
    ``mode == "Maintenance" and ``system_mode`` == "Maintenance"
    in the controller response.

    ### Setup - Code
    -   Sender() is initialized and configured.
    -   RestSend() is initialized and configured.
    -   SwitchDetails() is initialized and configured.
    -   SwitchDetails().refresh() is called.
    -   SwitchDetails().filter is set to the switch
        ip_address in the response.

    ### Setup - Data
    responses_switch_details() returns a response containing:
    -   1x switch
    -   ``mode`` == Maintenance
    -   ``system_mode`` == Maintenance

    ### Trigger
    ``maintenance_mode.getter`` is accessed.

    ### Expected Result
    -   ``maintenance_mode.getter`` returns "maintenance"
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
        instance.filter = "192.168.1.2"
    assert instance.maintenance_mode == "maintenance"


def test_switch_details_00750() -> None:
    """
    ### Classes and Methods
    -   SwitchDetails()
            -   validate_refresh_parameters()
            -   refresh()
            -   filter.setter
            -   maintenance_mode

    ### Summary
    Verify ``maintenance_mode`` returns "normal" if
    mode == "Normal" and system_mode == "Normal"
    in the controller response.

    ### Setup - Code
    -   Sender() is initialized and configured.
    -   RestSend() is initialized and configured.
    -   SwitchDetails() is initialized and configured.
    -   SwitchDetails().refresh() is called.
    -   SwitchDetails().filter is set to the switch
        ip_address in the response.

    ### Setup - Data
    responses_switch_details() returns a response containing:
    -   1x switch
    -   ``mode`` == Normal
    -   ``system_mode`` == Normal

    ### Trigger
    ``maintenance_mode.getter`` is accessed.

    ### Expected Result
    -   ``maintenance_mode.getter`` returns "normal"
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
        instance.filter = "192.168.1.2"
    assert instance.maintenance_mode == "normal"


def test_switch_details_00800() -> None:
    """
    ### Classes and Methods
    -   SwitchDetails()
            -   validate_refresh_parameters()
            -   refresh()
            -   filter.setter
            -   platform.getter

    ### Summary
    Verify ``platform`` returns ``None`` if model == ``null``
    in the controller response.

    ### Setup - Code
    -   Sender() is initialized and configured.
    -   RestSend() is initialized and configured.
    -   SwitchDetails() is initialized and configured.
    -   SwitchDetails().refresh() is called.
    -   SwitchDetails().filter is set to the switch
        ip_address in the response.

    ### Setup - Data
    responses_switch_details() returns a response containing:
    -   1x switch
    -   ``model`` == null

    ### Trigger
    ``platform.getter`` is accessed.

    ### Expected Result
    -   ``platform.getter`` returns ``None``
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
        instance.filter = "192.168.1.2"
    assert instance.platform is None
