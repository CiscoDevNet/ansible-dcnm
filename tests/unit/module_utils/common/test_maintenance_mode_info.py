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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils
from ansible_collections.cisco.dcnm.plugins.module_utils.common.exceptions import \
    ControllerResponseError
from ansible_collections.cisco.dcnm.plugins.module_utils.common.maintenance_mode_info import \
    MaintenanceModeInfo
from ansible_collections.cisco.dcnm.plugins.module_utils.common.response_handler import \
    ResponseHandler
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_file import \
    Sender
from ansible_collections.cisco.dcnm.tests.unit.mocks.mock_fabric_details_by_name import \
    MockFabricDetailsByName
from ansible_collections.cisco.dcnm.tests.unit.mocks.mock_switch_details import \
    MockSwitchDetails
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import (
    ResponseGenerator, does_not_raise, maintenance_mode_info_fixture,
    responses_fabric_details_by_name, responses_switch_details)

FABRIC_NAME = "VXLAN_Fabric"
CONFIG = ["192.168.1.2"]
PARAMS = {"state": "query", "check_mode": False}


def test_maintenance_mode_info_00000(maintenance_mode_info) -> None:
    """
    ### Classes and Methods
    -   ``MaintenanceModeInfo()``
            - ``__init__()``

    ### Summary
    - Verify the __init__() method.

    ### Setup - Data
    -   None

    ### Setup - Code
    -   None

    ### Trigger
    -   ``MaintenanceModeInfo`` is instantiated.

    ### Expected Result
    -   Class attributes are initialized to expected values.
    -   Exception is not raised.

    """
    with does_not_raise():
        instance = maintenance_mode_info
    assert instance._config is None
    assert instance._info is None
    assert instance._rest_send is None
    assert instance._results is None

    assert instance.action == "maintenance_mode_info"
    assert instance.class_name == "MaintenanceModeInfo"
    assert instance.config is None
    assert instance.rest_send is None
    assert instance.results is None

    assert isinstance(instance.conversion, ConversionUtils)


def test_maintenance_mode_info_00100(maintenance_mode_info) -> None:
    """
    ### Classes and Methods
    -   ``MaintenanceModeInfo()``
            - ``verify_refresh_parameters()``
            - ``refresh()``

    ### Summary
    -   Verify MaintenanceModeInfo().refresh() raises ``ValueError`` when
        ``config`` is not set.

    ### Setup - Data
    -   None

    ### Setup - Code
    -   ``MaintenanceModeInfo()`` is instantiated.
    -   Other required attributes are set.

    ### Trigger
    -   ``refresh()`` is called without having first set ``config``.

    ### Expected Result
    -   ``ValueError`` is raised.
    -   Exception message matches expectations.
    """
    with does_not_raise():
        instance = maintenance_mode_info
        instance.rest_send = RestSend({})
        instance.results = Results()

    match = r"MaintenanceModeInfo\.verify_refresh_parameters: "
    match += r"MaintenanceModeInfo\.config must be set before calling\s+"
    match += r"refresh\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_maintenance_mode_info_00110(maintenance_mode_info) -> None:
    """
    ### Classes and Methods
    -   ``MaintenanceModeInfo()``
            - ``verify_refresh_parameters()``
            - ``refresh()``

    ### Summary
    -   Verify ``refresh()`` raises ``ValueError`` when ``rest_send``
        is not set.

    ### Setup - Data
    -   None

    ### Setup - Code
    -   ``MaintenanceModeInfo()`` is instantiated.
    -   Other required attributes are set.

    ### Trigger
    -   ``refresh()`` is called without having first set ``rest_send``.

    ### Expected Result
    -   ``ValueError`` is raised.
    -   Exception message matches expectations.
    """
    with does_not_raise():
        instance = maintenance_mode_info
        instance.results = Results()
        instance.config = CONFIG

    match = r"MaintenanceModeInfo\.verify_refresh_parameters: "
    match += r"MaintenanceModeInfo\.rest_send must be set before calling\s+"
    match += r"refresh\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_maintenance_mode_info_00120(maintenance_mode_info) -> None:
    """
    ### Classes and Methods
    -   ``MaintenanceModeInfo()``
            - ``verify_refresh_parameters()``
            - ``refresh()``

    ### Summary
    -   Verify ``refresh()`` raises ``ValueError`` when ``results`` is not set.

    ### Setup - Data
    -   None

    ### Setup - Code
    -   ``MaintenanceModeInfo()`` is instantiated.
    -   Other required attributes are set.

    ### Trigger
    -   ``refresh()`` is called without having first set ``results``.

    ### Expected Result
    -   ``ValueError`` is raised.
    -   Exception message matches expectations.
    """
    with does_not_raise():
        instance = maintenance_mode_info
        instance.rest_send = RestSend({})
        instance.config = CONFIG

    match = r"MaintenanceModeInfo\.verify_refresh_parameters: "
    match += r"MaintenanceModeInfo\.results must be set before calling\s+"
    match += r"refresh\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


@pytest.mark.parametrize(
    "mock_class, mock_property, mock_exception, expected_exception, mock_message",
    [
        (
            "FabricDetailsByName",
            "refresh",
            ControllerResponseError,
            ValueError,
            "Bad controller response: fabric_details.refresh",
        ),
        (
            "FabricDetailsByName",
            "results.setter",
            TypeError,
            ValueError,
            "Bad type: fabric_details.results.setter",
        ),
        (
            "FabricDetailsByName",
            "rest_send.setter",
            TypeError,
            ValueError,
            "Bad type: fabric_details.rest_send.setter",
        ),
        (
            "SwitchDetails",
            "refresh",
            ControllerResponseError,
            ValueError,
            "Bad controller response: switch_details.refresh",
        ),
        (
            "SwitchDetails",
            "results.setter",
            TypeError,
            ValueError,
            "Bad type: switch_details.results.setter",
        ),
        (
            "SwitchDetails",
            "rest_send.setter",
            TypeError,
            ValueError,
            "Bad type: switch_details.rest_send.setter",
        ),
    ],
)
def test_maintenance_mode_info_00200(
    monkeypatch,
    mock_class,
    mock_property,
    mock_exception,
    expected_exception,
    mock_message,
) -> None:
    """
    ### Classes and Methods
    - ``MaintenanceModeInfo()``
        - ``refresh()``

    ### Summary
    -   Verify ``refresh()`` raises ``ValueError`` when:
            -   ``fabric_details`` properties ``rest_send`` and ``results``
                raise ``TypeError``.
            -   ``switch_details`` properties ``rest_send`` and ``results``
                raise ``TypeError``.

    ### Setup - Data
    -    None

    ### Setup - Code
    -   ``MaintenanceModeInfo()`` is instantiated
    -   Required attributes are set
    -   ``FabricDetails()`` is mocked to conditionally raise ``TypeError``.
    -   ``SwitchDetails()`` is mocked to conditionally raise ``TypeError``.

    ### Trigger
    -   ``refresh()`` is called.

    ### Expected Result
    -   ``ValueError`` is raised.
    -   Exception message matches expectations.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_switch_details(key)

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    rest_send = RestSend({"state": "query", "check_mode": False})
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = MaintenanceModeInfo(PARAMS)

    mock_fabric_details = MockFabricDetailsByName()
    mock_fabric_details.mock_class = mock_class
    mock_fabric_details.mock_exception = mock_exception
    mock_fabric_details.mock_message = mock_message
    mock_fabric_details.mock_property = mock_property

    mock_switch_details = MockSwitchDetails()
    mock_switch_details.mock_class = mock_class
    mock_switch_details.mock_exception = mock_exception
    mock_switch_details.mock_message = mock_message
    mock_switch_details.mock_property = mock_property

    monkeypatch.setattr(instance, "fabric_details", mock_fabric_details)
    monkeypatch.setattr(instance, "switch_details", mock_switch_details)

    with does_not_raise():
        instance.config = CONFIG
        instance.rest_send = RestSend({"state": "query", "check_mode": False})
        instance.results = Results()

    with pytest.raises(expected_exception, match=mock_message):
        instance.refresh()


@pytest.mark.parametrize(
    "mock_class, mock_property, mock_exception, expected_exception, mock_message",
    [
        (
            "SwitchDetails",
            "serial_number.getter",
            ValueError,
            ValueError,
            "serial_number.getter: ValueError",
        )
    ],
)
def test_maintenance_mode_info_00210(
    monkeypatch,
    mock_class,
    mock_property,
    mock_exception,
    expected_exception,
    mock_message,
) -> None:
    """
    ### Classes and Methods
    - MaintenanceModeInfo()
        - refresh()

    ### Summary
    -   Verify ``refresh()`` raises ``ValueError`` when
        ``switch_details.serial_number`` raises ``ValueError``.

    ### Setup - Data
    -   ``responses_SwitchDetails.json``:
            -   RETURN_CODE: 200
            -   MESSAGE: OK

    ### Setup - Code
    -   ``MaintenanceModeInfo()`` is instantiated
    -   Required attributes are set
    -   ``SwitchDetails()`` is mocked to conditionally raise
        ``ValueError`` in the ``serial_number.getter`` property.

    ### Trigger
    -   ``refresh()`` is called.

    ### Expected Result
    -   ``ValueError`` is raised.
    -   Exception message matches expectations.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_switch_details(key)

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    rest_send = RestSend({"state": "query", "check_mode": False})
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = MaintenanceModeInfo(PARAMS)

    mock_switch_details = MockSwitchDetails()
    mock_switch_details.mock_class = mock_class
    mock_switch_details.mock_exception = mock_exception
    mock_switch_details.mock_message = mock_message
    mock_switch_details.mock_property = mock_property

    monkeypatch.setattr(instance, "switch_details", mock_switch_details)

    with does_not_raise():
        instance.config = CONFIG
        instance.rest_send = rest_send
        instance.results = Results()

    with pytest.raises(expected_exception, match=mock_message):
        instance.refresh()


def test_maintenance_mode_info_00300() -> None:
    """
    ### Classes and Methods
    - MaintenanceModeInfo()
        - __init__()
        - refresh()

    ### Summary
    Verify ``refresh()`` raises ``ValueError`` when
    ``switch_details.serial_number`` is ``None``.

    This happens when the switch does not exist on the controller and causes
    SwitchDetails()._get() to raise a ``ValueError``.

    ### Setup - Data
    -   ``ipAddress`` is set to something other than 192.168.1.2
    -   ``responses_SwitchDetails.json``:
            -   "DATA[0].fabricName: VXLAN_Fabric",
            -   "DATA[0].freezeMode: null",
            -   "DATA[0].ipAddress: 192.168.1.1",
            -   "DATA[0].mode: Normal",
            -   "DATA[0].serialNumber: FDO211218FV",
            -   "DATA[0].switchRole: leaf",
            -   "DATA[0].systemMode: Normal"
            -   RETURN_CODE: 200
            -   MESSAGE: OK
    -   ``responses_FabricDetailsByName.json``:
            -   RETURN_CODE: 200
            -   MESSAGE: OK

    ### Setup - Code
    -   ``MaintenanceModeInfo()`` is instantiated
    -   Required attributes are set

    ### Trigger
    -   ``refresh()`` is called.

    ### Expected Result
    -   ``ValueError`` is raised.
    -   Exception message matches expectations.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_switch_details(key)
        yield responses_fabric_details_by_name(key)

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    rest_send = RestSend({"state": "query", "check_mode": False})
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = MaintenanceModeInfo(PARAMS)
        instance.config = CONFIG
        instance.rest_send = rest_send
        instance.results = Results()

    match = r"SwitchDetails\._get:\s+"
    match += r"Switch with ip_address 192\.168\.1\.2\s+"
    match += r"does not exist on the controller\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


@pytest.mark.parametrize(
    "mock_class, mock_property, mock_exception, expected_exception, mock_message",
    [
        (
            "FabricDetailsByName",
            "filter.setter",
            ValueError,
            ValueError,
            "fabric_details.filter.setter: ValueError",
        )
    ],
)
def test_maintenance_mode_info_00400(
    monkeypatch,
    mock_class,
    mock_property,
    mock_exception,
    expected_exception,
    mock_message,
) -> None:
    """
    ### Classes and Methods
    - MaintenanceModeInfo()
        - refresh()

    ### Summary
    -   Verify ``refresh()`` raises ``ValueError`` when
        ``fabric_details.filter`` raises ``ValueError``.

    ### Setup - Data
    -   ``responses_SwitchDetails.json``:
            -   "DATA[0].fabricName: VXLAN_Fabric",
            -   "DATA[0].freezeMode: null",
            -   "DATA[0].ipAddress: 192.168.1.2",
            -   "DATA[0].mode: Normal",
            -   "DATA[0].serialNumber: FDO211218FV",
            -   "DATA[0].switchRole: leaf",
            -   "DATA[0].systemMode: Normal"
            -   RETURN_CODE: 200
            -   MESSAGE: OK

    ### Code Flow - Setup
    -   ``MaintenanceModeInfo()`` is instantiated.
    -   Required attributes are set.
    -   ``FabricDetailsByName().filter`` is mocked to conditionally raise
        ``ValueError``.

    ### Trigger
    -   ``refresh()`` is called.

    ### Expected Result
    -   ``ValueError`` is raised.
    -   Exception message matches expectations.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_switch_details(key)

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    rest_send = RestSend({"state": "query", "check_mode": False})
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = MaintenanceModeInfo(PARAMS)

    mock_fabric_details = MockFabricDetailsByName()
    mock_fabric_details.mock_class = mock_class
    mock_fabric_details.mock_exception = mock_exception
    mock_fabric_details.mock_message = mock_message
    mock_fabric_details.mock_property = mock_property

    monkeypatch.setattr(instance, "fabric_details", mock_fabric_details)

    with does_not_raise():
        instance.config = CONFIG
        instance.rest_send = rest_send
        instance.results = Results()

    with pytest.raises(expected_exception, match=mock_message):
        instance.refresh()


def test_maintenance_mode_info_00500() -> None:
    """
    ### Classes and Methods
    - MaintenanceModeInfo()
        - refresh()

    ### Summary
    -   Verify when ``freezeMode`` == null in the response,
        ``freezeMode`` is set to False.

    ### Setup - Data
    -   ``responses_SwitchDetails.json``:
            -   "DATA[0].fabricName: VXLAN_Fabric",
            -   "DATA[0].freezeMode: null",
            -   "DATA[0].ipAddress: 192.168.1.2",
            -   "DATA[0].mode: Normal",
            -   "DATA[0].serialNumber: FDO211218FV",
            -   "DATA[0].switchRole: leaf",
            -   "DATA[0].systemMode: Normal"
            -   RETURN_CODE: 200
            -   MESSAGE: OK
    -   ``responses_FabricDetailsByName.json``:
            -   RETURN_CODE: 200
            -   MESSAGE: OK

    ### Setup - Code
    -   ``MaintenanceModeInfo()`` is instantiated
    -   Required attributes are set

    ### Trigger
    -   ``refresh()`` is called.

    ### Expected Result
    -   Exception is not raised.
    -   ``MaintenanceModeInfo().results`` contains expected data.

    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_switch_details(key)
        yield responses_fabric_details_by_name(key)

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    rest_send = RestSend({"state": "query", "check_mode": False})
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = MaintenanceModeInfo(PARAMS)
        instance.config = CONFIG
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        instance.filter = CONFIG[0]
    assert instance.fabric_name == FABRIC_NAME
    assert instance.fabric_freeze_mode is False
    assert instance.fabric_read_only is False
    assert instance.fabric_deployment_disabled is False
    assert instance.mode == "normal"
    assert instance.role == "leaf"


def test_maintenance_mode_info_00510() -> None:
    """
    ### Classes and Methods
    - MaintenanceModeInfo()
        - __init__()
        - refresh()

    ### Summary
    -   Verify happy path with:
            -   switch_details: freezeMode is True

    ### Setup - Data
    -   ``responses_SwitchDetails.json``:
            -   "DATA[0].fabricName: VXLAN_Fabric",
            -   "DATA[0].freezeMode: true",
            -   "DATA[0].ipAddress: 192.168.1.2",
            -   "DATA[0].mode: Normal",
            -   "DATA[0].serialNumber: FDO211218FV",
            -   "DATA[0].switchRole: leaf",
            -   "DATA[0].systemMode: Normal"
            -   RETURN_CODE: 200
            -   MESSAGE: OK
    -   ``responses_FabricDetailsByName.json``:
            -   RETURN_CODE: 200
            -   MESSAGE: OK

    ### Setup - Code
    -   ``MaintenanceModeInfo()`` is instantiated
    -   Required attributes are set

    ### Trigger
    -   ``refresh()`` is called.

    ### Expected Result
    -   Exception is not raised.
    -   ``MaintenanceModeInfo().results`` contains expected data.

    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_switch_details(key)
        yield responses_fabric_details_by_name(key)

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    rest_send = RestSend({"state": "query", "check_mode": False})
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = MaintenanceModeInfo(PARAMS)
        instance.config = CONFIG
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        instance.filter = CONFIG[0]
    assert instance.fabric_name == FABRIC_NAME
    assert instance.fabric_freeze_mode is True
    assert instance.fabric_read_only is True
    assert instance.fabric_deployment_disabled is True
    assert instance.mode == "normal"
    assert instance.role == "leaf"


def test_maintenance_mode_info_00520() -> None:
    """
    ### Classes and Methods
    - MaintenanceModeInfo()
        - __init__()
        - refresh()

    ### Summary
    -   Verify:
            -   ``mode`` == "inconsistent" when ``mode`` != ``systemMode``.

    ### Setup - Data
    -   ``responses_SwitchDetails.json``:
            -   DATA[0].fabricName: VXLAN_Fabric
            -   DATA[0].freezeMode: true
            -   DATA[0].ipAddress: 192.168.1.2
            -   DATA[0].mode: Normal
            -   DATA[0].serialNumber: FDO211218FV
            -   DATA[0].switchRole: leaf
            -   DATA[0].systemMode: Maintenance
            -   RETURN_CODE: 200
            -   MESSAGE: OK
    -   ``responses_FabricDetailsByName.json``:
            -   RETURN_CODE: 200
            -   MESSAGE: OK

    ### Setup - Code
    -   ``MaintenanceModeInfo()`` is instantiated
    -   Required attributes are set

    ### Trigger
    -   ``refresh()`` is called.

    ### Expected Result
    -   Conditions in Summary are confirmed.
    -   Exception is not raised.
    -   ``MaintenanceModeInfo().results`` contains expected data.

    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_switch_details(key)
        yield responses_fabric_details_by_name(key)

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    rest_send = RestSend({"state": "query", "check_mode": False})
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = MaintenanceModeInfo(PARAMS)
        instance.config = CONFIG
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        instance.filter = CONFIG[0]
    assert instance.mode == "inconsistent"
    assert instance.results.response[0]["DATA"][0]["mode"] == "Normal"
    assert instance.results.response[0]["DATA"][0]["systemMode"] == "Maintenance"
    assert instance.results.result[0]["success"] is True
    assert instance.results.result[1]["success"] is True
    assert instance.results.result[0]["found"] is True
    assert instance.results.result[1]["found"] is True
