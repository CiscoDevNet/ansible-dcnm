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
from ansible_collections.cisco.dcnm.tests.unit.mocks.mock_fabric_details_by_name import \
    MockFabricDetailsByName
from ansible_collections.cisco.dcnm.tests.unit.mocks.mock_switch_details import \
    MockSwitchDetails
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import (
    MockSender, ResponseGenerator, does_not_raise,
    maintenance_mode_info_fixture, responses_switch_details)

FABRIC_NAME = "VXLAN_Fabric"
CONFIG = ["192.168.1.2"]
PARAMS = {"state": "query", "check_mode": False}


def test_maintenance_mode_info_00000(maintenance_mode_info) -> None:
    """
    Classes and Methods
    - MaintenanceModeInfo
        - __init__()

    Test
    - Class attributes are initialized to expected values
    - Exception is not raised
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
    - MaintenanceModeInfo()
        - __init__()
        - verify_refresh_parameters()
        - refresh()

    ### Summary
    -   Verify MaintenanceModeInfo().refresh() raises ``ValueError`` when
        ``config`` is not set.

    ### Code Flow - Setup
    -   MaintenanceModeInfo() is instantiated.
    -   Other required attributes are set.

    ### Code Flow - Test
    -   ``MaintenanceModeInfo().refresh()`` is called without having first set
        ``MaintenanceModeInfo().config``.

    ### Expected Result
    -   ``ValueError`` is raised.
    -   Exception message matches expected.
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
    - ``MaintenanceModeInfo()``
        - __init__()
        - verify_refresh_parameters()
        - refresh()

    ### Summary
    -   Verify ``refresh()`` raises ``ValueError`` when ``rest_send``
        is not set.

    ### Code Flow - Setup
    -   ``MaintenanceModeInfo()`` is instantiated
    -   Other required attributes are set

    Code Flow - Test
    -   ``refresh()`` is called without having first set ``rest_send``.

    ### Expected Result
    -   ``ValueError`` is raised.
    -   Exception message matches expected.
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
    - MaintenanceModeInfo()
        - __init__()
        - verify_refresh_parameters()
        - refresh()

    ### Summary
    -   Verify ``refresh()`` raises ``ValueError`` when ``results`` is not set.

    ### Code Flow - Setup
    -   ``MaintenanceModeInfo()`` is instantiated.
    -   Other required attributes are set.

    ### Code Flow - Test
    -   ``refresh()`` is called without having first set ``results``.

    ### Expected Result
    -   ``ValueError`` is raised.
    -   Exception message matches expected.
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
    - MaintenanceModeInfo()
        - __init__()
        - refresh()

    ### Summary
    -   Verify ``refresh()`` raises ``ValueError`` when:
            -   ``fabric_details`` properties ``rest_send`` and ``results``
                raise ``TypeError``.
            -   ``switch_details`` properties ``rest_send`` and ``results``
                raise ``TypeError``.

    ### Code Flow - Setup
    -   ``MaintenanceModeInfo()`` is instantiated
    -   Required attributes are set
    -   ``FabricDetails()`` is mocked to conditionally raise ``TypeError``.
    -   ``SwitchDetails()`` is mocked to conditionally raise ``TypeError``.

    ### Code Flow - Test
    -   ``refresh()`` is called.

    ### Expected Result
    -   ``ValueError`` is raised.
    -   Exception message matches expected.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_switch_details(key)

    mock_sender = MockSender()
    mock_sender.gen = ResponseGenerator(responses())
    rest_send = RestSend({"state": "query", "check_mode": False})
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = mock_sender

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
        instance.rest_send = rest_send
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
        - __init__()
        - refresh()

    ### Summary
    -   Verify ``refresh()`` raises ``ValueError`` when:
            -   ``switch_details.serial_number`` raises ``ValueError``.

    ### Code Flow - Setup
    -   ``MaintenanceModeInfo()`` is instantiated
    -   Required attributes are set
    -   ``FabricDetails()`` is mocked not to raise any exceptions.
    -   ``SwitchDetails()`` is mocked to conditionally raise ``ValueError``.
        in the ``serial_number.getter`` property.

    ### Code Flow - Test
    -   ``refresh()`` is called.

    ### Expected Result
    -   ``ValueError`` is raised.
    -   Exception message matches expected.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_switch_details(key)

    mock_sender = MockSender()
    mock_sender.gen = ResponseGenerator(responses())
    rest_send = RestSend({"state": "query", "check_mode": False})
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = mock_sender

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
        instance.rest_send = rest_send
        instance.results = Results()

    with pytest.raises(expected_exception, match=mock_message):
        instance.refresh()


def test_maintenance_mode_info_00300(
    monkeypatch,
) -> None:
    """
    ### Classes and Methods
    - MaintenanceModeInfo()
        - __init__()
        - refresh()

    ### Summary
    -   Verify ``refresh()`` raises ``ValueError`` when:
        ``switch_details.serial_number`` is ``None``.  This happens
        when the switch does not exist on the controller.

    ### Code Flow - Setup
    -   ``MaintenanceModeInfo()`` is instantiated
    -   Required attributes are set
    -   ``FabricDetails()`` is mocked not to raise any exceptions.
    -   ``SwitchDetails()`` is mocked not to raise any exceptions.
    -   ``responses_SwitchDetails.json`` contains a 200 response that
        does not contain the switch ip address in CONFIG (192.168.1.2)

    ### Code Flow - Test
    -   ``refresh()`` is called.

    ### Expected Result
    -   ``ValueError`` is raised.
    -   Exception message matches expected.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        pass

    mock_sender = MockSender()
    mock_sender.gen = ResponseGenerator(responses())
    rest_send = RestSend({"state": "query", "check_mode": False})
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = mock_sender

    with does_not_raise():
        instance = MaintenanceModeInfo(PARAMS)

    mock_fabric_details = MockFabricDetailsByName()
    mock_switch_details = MockSwitchDetails()
    mock_switch_details.filter = CONFIG[0]
    mock_switch_details.mock_response_key = key

    monkeypatch.setattr(instance, "fabric_details", mock_fabric_details)
    monkeypatch.setattr(instance, "switch_details", mock_switch_details)

    with does_not_raise():
        instance.config = CONFIG
        instance.rest_send = rest_send
        instance.results = Results()

    match = r"MaintenanceModeInfo\.refresh:\s+"
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
        - __init__()
        - refresh()

    ### Summary
    -   Verify ``refresh()`` raises ``ValueError`` when:
            -   ``fabric_details.filter`` raises ``ValueError``.

    ### Code Flow - Setup
    -   ``MaintenanceModeInfo()`` is instantiated
    -   Required attributes are set
    -   ``FabricDetails().filter`` is mocked to conditionally raise ``ValueError``.
    -   ``SwitchDetails()`` is mocked not to raise any exceptions.
    -   ``responses_SwitchDetails.json`` contains a 200 response that
        contains the switch ip address in CONFIG (192.168.1.2)

    ### Code Flow - Test
    -   ``refresh()`` is called.

    ### Expected Result
    -   ``ValueError`` is raised.
    -   Exception message matches expected.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        pass

    mock_sender = MockSender()
    mock_sender.gen = ResponseGenerator(responses())
    rest_send = RestSend({"state": "query", "check_mode": False})
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = mock_sender

    with does_not_raise():
        instance = MaintenanceModeInfo(PARAMS)

    mock_fabric_details = MockFabricDetailsByName()
    mock_fabric_details.mock_class = mock_class
    mock_fabric_details.mock_exception = mock_exception
    mock_fabric_details.mock_message = mock_message
    mock_fabric_details.mock_property = mock_property

    mock_switch_details = MockSwitchDetails()
    mock_switch_details.filter = CONFIG[0]
    mock_switch_details.mock_response_key = key

    monkeypatch.setattr(instance, "fabric_details", mock_fabric_details)
    monkeypatch.setattr(instance, "switch_details", mock_switch_details)

    with does_not_raise():
        instance.config = CONFIG
        instance.rest_send = rest_send
        instance.results = Results()

    with pytest.raises(expected_exception, match=mock_message):
        instance.refresh()


# @pytest.mark.parametrize(
#     "mock_exception, expected_exception, mock_message",
#     [
#         (ControllerResponseError, ValueError, "Bad controller response"),
#         (ValueError, ValueError, "Bad value"),
#     ],
# )
# def test_maintenance_mode_info_00210(
#     monkeypatch, maintenance_mode_info, mock_exception, expected_exception, mock_message
# ) -> None:
#     """
#     Classes and Methods
#     - MaintenanceModeInfo()
#         - __init__()
#         - refresh()

#     Summary
#     -   Verify MaintenanceModeInfo().refresh() raises ``ValueError`` when
#         ``MaintenanceModeInfo().deploy_switches`` raises any of:
#             -   ``ControllerResponseError``
#             -   ``ValueError``


#     Code Flow - Setup
#     -   MaintenanceModeInfo() is instantiated
#     -   Required attributes are set
#     -   change_system_mode() is mocked to do nothing
#     -   deploy_switches() is mocked to raise each of the above exceptions

#     Code Flow - Test
#     -   MaintenanceModeInfo().refresh() is called for each exception

#     Expected Result
#     -   ``ValueError`` is raised
#     -   Exception message matches expected
#     """

#     def mock_change_system_mode(*args, **kwargs):
#         pass

#     def mock_deploy_switches(*args, **kwargs):
#         raise mock_exception(mock_message)

#     with does_not_raise():
#         instance = maintenance_mode_info
#         instance.config = CONFIG
#         instance.rest_send = RestSend({})
#         instance.results = Results()

#     monkeypatch.setattr(instance, "change_system_mode", mock_change_system_mode)
#     monkeypatch.setattr(instance, "deploy_switches", mock_deploy_switches)
#     with pytest.raises(expected_exception, match=mock_message):
#         instance.refresh()


# @pytest.mark.parametrize(
#     "mode, deploy",
#     [
#         ("maintenance", True),
#         ("maintenance", False),
#         ("normal", True),
#         ("normal", False),
#     ],
# )
# def test_maintenance_mode_info_00220(maintenance_mode_info, mode, deploy) -> None:
#     """
#     Classes and Methods
#     - MaintenanceModeInfo()
#         - __init__()
#         - refresh()
#         - change_system_mode()
#         - deploy_switches()

#     Summary
#     - Verify refresh() success case:
#         -   RETURN_CODE is 200.
#         -   Controller response contains expected structure and values.

#     Code Flow - Setup
#     -   MaintenanceModeInfo() is instantiated
#     -   Sender() is mocked to return expected responses
#     -   Required attributes are set
#     -   MaintenanceModeInfo().refresh() is called
#     -   responses_MaintenanceMode contains a dict with:
#         - RETURN_CODE == 200
#         - DATA == {"status": "Success"}

#     Code Flow - Test
#     -   MaintenanceModeInfo().refresh() is called

#     Expected Result
#     -   Exception is not raised
#     -   instance.response_data returns expected data
#     -   MaintenanceModeInfo()._properties are updated
#     """
#     method_name = inspect.stack()[0][3]
#     key = f"{method_name}a"

#     def responses():
#         yield responses_maintenance_mode_info(key)

#     mock_sender = MockSender()
#     mock_sender.gen = ResponseGenerator(responses())

#     config = copy.deepcopy(CONFIG[0])
#     config["mode"] = mode
#     config["deploy"] = deploy

#     with does_not_raise():
#         rest_send = RestSend({"state": "merged", "check_mode": False})
#         rest_send.sender = mock_sender
#         rest_send.response_handler = ResponseHandler()
#         instance = maintenance_mode_info
#         instance.rest_send = rest_send
#         instance.rest_send.unit_test = True
#         instance.rest_send.timeout = 1
#         instance.results = Results()
#         instance.config = [config]

#     with does_not_raise():
#         instance.refresh()

#     assert isinstance(instance.results.diff, list)
#     assert isinstance(instance.results.metadata, list)
#     assert isinstance(instance.results.response, list)
#     assert isinstance(instance.results.result, list)
#     assert instance.results.diff[0].get("fabric_name", None) == FABRIC_NAME
#     assert instance.results.diff[0].get("ip_address", None) == "192.168.1.2"
#     assert instance.results.diff[0].get("maintenance_mode", None) == mode
#     assert instance.results.diff[0].get("sequence_number", None) == 1
#     assert instance.results.diff[0].get("serial_number", None) == "FDO22180ASJ"

#     assert instance.results.diff[1].get("config_deploy", None) is True
#     assert instance.results.diff[1].get("sequence_number", None) == 2

#     assert instance.results.metadata[0].get("action", None) == "change_sytem_mode"
#     assert instance.results.metadata[0].get("sequence_number", None) == 1
#     assert instance.results.metadata[0].get("state", None) == "merged"

#     assert instance.results.metadata[1].get("action", None) == "config_deploy"
#     assert instance.results.metadata[1].get("sequence_number", None) == 2
#     assert instance.results.metadata[1].get("state", None) == "merged"

#     assert instance.results.response[0].get("DATA", {}).get("status") == "Success"
#     assert instance.results.response[0].get("MESSAGE", None) == "OK"
#     assert instance.results.response[0].get("RETURN_CODE", None) == 200
#     assert instance.results.response[0].get("METHOD", None) == "POST"

#     value = "Configuration deployment completed."
#     assert instance.results.response[1].get("DATA", {}).get("status") == value
#     assert instance.results.response[1].get("MESSAGE", None) == "OK"
#     assert instance.results.response[1].get("RETURN_CODE", None) == 200
#     assert instance.results.response[1].get("METHOD", None) == "POST"

#     assert instance.results.result[0].get("changed", None) is True
#     assert instance.results.result[0].get("success", None) is True

#     assert instance.results.result[1].get("changed", None) is True
#     assert instance.results.result[1].get("success", None) is True


# @pytest.mark.parametrize(
#     "mode",
#     [
#         ("maintenance"),
#         ("normal"),
#     ],
# )
# def test_maintenance_mode_info_00230(maintenance_mode_info, mode) -> None:
#     """
#     Classes and Methods
#     - MaintenanceModeInfo()
#         - __init__()
#         - refresh()
#         - change_system_mode()
#         - deploy_switches()

#     Summary
#     - Verify refresh() unsuccessful case:
#         -   RETURN_CODE == 500.
#         -   refresh raises ``ValueError`` when change_system_mode() raises
#             ``ControllerResponseError``.
#         -   Controller response contains expected structure and values.

#     Code Flow - Setup
#     -   MaintenanceModeInfo() is instantiated
#     -   Sender() is mocked to return expected responses
#     -   Required attributes are set
#     -   MaintenanceModeInfo().refresh() is called
#     -   responses_MaintenanceMode contains a dict with:
#         - RETURN_CODE == 500
#         - DATA == {"status": "Failure"}

#     Code Flow - Test
#     -   ``MaintenanceModeInfo().refresh()`` is called
#     -   ``change_system_mode()`` raises ``ControllerResponseError``
#     -   ``refresh()`` raises ``ValueError``

#     Expected Result
#     -   ``refresh()`` raises ``ValueError``
#     -   instance.response_data returns expected data
#     -   MaintenanceModeInfo()._properties are updated
#     """
#     method_name = inspect.stack()[0][3]
#     key = f"{method_name}a"

#     def responses():
#         yield responses_maintenance_mode_info(key)
#         # yield responses_config_deploy(key)

#     mock_sender = MockSender()
#     mock_sender.gen = ResponseGenerator(responses())

#     config = copy.deepcopy(CONFIG[0])
#     config["mode"] = mode

#     with does_not_raise():
#         rest_send = RestSend({"state": "merged", "check_mode": False})
#         rest_send.sender = mock_sender
#         rest_send.response_handler = ResponseHandler()
#         instance = maintenance_mode_info
#         instance.rest_send = rest_send
#         instance.rest_send.unit_test = True
#         instance.rest_send.timeout = 1
#         instance.results = Results()
#         instance.config = [config]

#     match = r"MaintenanceMode\.change_system_mode:\s+"
#     match += r"Unable to change system mode on switch:\s+"
#     match += rf"fabric_name {config['fabric_name']},\s+"
#     match += rf"ip_address {config['ip_address']},\s+"
#     match += rf"serial_number {config['serial_number']}\.\s+"
#     match += r"Got response\s+.*"
#     with pytest.raises(ValueError, match=match):
#         instance.refresh()

#     assert isinstance(instance.results.diff, list)
#     assert isinstance(instance.results.metadata, list)
#     assert isinstance(instance.results.response, list)
#     assert isinstance(instance.results.result, list)
#     assert len(instance.results.diff[0]) == 1

#     assert instance.results.metadata[0].get("action", None) == "change_sytem_mode"
#     assert instance.results.metadata[0].get("sequence_number", None) == 1
#     assert instance.results.metadata[0].get("state", None) == "merged"

#     assert instance.results.response[0].get("DATA", {}).get("status") == "Failure"
#     assert instance.results.response[0].get("MESSAGE", None) == "Internal Server Error"
#     assert instance.results.response[0].get("RETURN_CODE", None) == 500
#     assert instance.results.response[0].get("METHOD", None) == "POST"

#     assert instance.results.result[0].get("changed", None) is False
#     assert instance.results.result[0].get("success", None) is False


# def test_maintenance_mode_info_00300(maintenance_mode_info) -> None:
#     """
#     Classes and Methods
#     - MaintenanceModeInfo()
#         - __init__()
#         - verify_config_parameters()
#         - config.setter

#     Summary
#     -   Verify MaintenanceModeInfo().verify_config_parameters() raises
#             -   ``TypeError`` if:
#                     - value is not a list
#     -   Verify MaintenanceModeInfo().config.setter re-raises:
#             -   ``TypeError`` as ``ValueError``

#     Code Flow - Setup
#     -   MaintenanceModeInfo() is instantiated
#     -   config is set to a non-list value

#     Code Flow - Test
#     -   MaintenanceModeInfo().config.setter is accessed with non-list

#     Expected Result
#     -   verify_config_parameters() raises ``TypeError``.
#     -   config.setter re-raises as ``ValueError``.
#     -   Exception message matches expected.
#     """
#     with does_not_raise():
#         instance = maintenance_mode_info
#     match = r"MaintenanceMode\.verify_config_parameters:\s+"
#     match += r"MaintenanceMode\.config must be a list\.\s+"
#     match += r"Got type: str\."
#     with pytest.raises(ValueError, match=match):
#         instance.config = "NOT_A_LIST"


# @pytest.mark.parametrize(
#     "remove_param",
#     [("deploy"), ("fabric_name"), ("ip_address"), ("mode"), ("serial_number")],
# )
# def test_maintenance_mode_info_00310(maintenance_mode_info, remove_param) -> None:
#     """
#     Classes and Methods
#     - MaintenanceModeInfo()
#         - __init__()
#         - verify_config_parameters()
#         - config.setter

#     Summary
#     -   Verify MaintenanceModeInfo().verify_config_parameters() raises
#             -   ``ValueError`` if:
#                     - deploy is missing from config
#                     - fabric_name is missing from config
#                     - ip_address is missing from config
#                     - mode is missing from config
#                     - serial_number is missing from config


#     Code Flow - Setup
#     -   MaintenanceModeInfo() is instantiated

#     Code Flow - Test
#     -   MaintenanceModeInfo().config is set to a dict with all of the above
#         keys present, except that each key, in turn, is removed.

#     Expected Result
#     -   ``ValueError`` is raised
#     -   Exception message matches expected
#     """

#     with does_not_raise():
#         instance = maintenance_mode_info

#     config = copy.deepcopy(CONFIG[0])
#     del config[remove_param]
#     match = rf"MaintenanceMode\.verify_{remove_param}:\s+"
#     match += rf"config is missing mandatory key: {remove_param}\."
#     with pytest.raises(ValueError, match=match):
#         instance.config = [config]


# @pytest.mark.parametrize(
#     "param, raises",
#     [
#         (False, None),
#         (True, None),
#         (10, ValueError),
#         ("FOO", ValueError),
#         (["FOO"], ValueError),
#         ({"FOO": "BAR"}, ValueError),
#     ],
# )
# def test_maintenance_mode_info_00400(maintenance_mode_info, param, raises) -> None:
#     """
#     Classes and Methods
#     - MaintenanceModeInfo()
#         - __init__()
#         - verify_config_parameters()
#         - config.setter

#     Summary
#     -   Verify MaintenanceModeInfo().verify_config_parameters() re-raises
#             -   ``ValueError`` if:
#                     - ``deploy`` raises ``TypeError``

#     Code Flow - Setup
#     -   MaintenanceModeInfo() is instantiated

#     Code Flow - Test
#     -   MaintenanceModeInfo().config is set to a dict.
#     -   The dict is updated with deploy set to valid and invalid
#         values of ``deploy``

#     Expected Result
#     -   ``ValueError`` is raised when deploy is not a boolean
#     -   Exception message matches expected
#     -   Exception is not raised when deploy is a boolean
#     """

#     with does_not_raise():
#         instance = maintenance_mode_info

#     config = copy.deepcopy(CONFIG[0])
#     config["deploy"] = param
#     match = r"MaintenanceMode\.verify_deploy:\s+"
#     match += r"Expected boolean for deploy\.\s+"
#     match += r"Got type\s+"
#     if raises:
#         with pytest.raises(raises, match=match):
#             instance.config = [config]
#     else:
#         instance.config = [config]
#         assert instance.config[0]["deploy"] == param


# @pytest.mark.parametrize(
#     "param, raises",
#     [
#         ("MyFabric", None),
#         ("MyFabric_123", None),
#         ("10MyFabric", ValueError),
#         ("_MyFabric", ValueError),
#         ("MyFabric&BadFabric", ValueError),
#     ],
# )
# def test_maintenance_mode_info_00500(maintenance_mode_info, param, raises) -> None:
#     """
#     Classes and Methods
#     - MaintenanceModeInfo()
#         - __init__()
#         - verify_config_parameters()
#         - config.setter

#     Summary
#     -   Verify MaintenanceModeInfo().verify_config_parameters() re-raises
#             -   ``ValueError`` if:
#                     - ``fabric_name`` raises ``ValueError`` due to being an
#                         invalid value.

#     Code Flow - Setup
#     -   MaintenanceModeInfo() is instantiated

#     Code Flow - Test
#     -   MaintenanceModeInfo().config is set to a dict.
#     -   The dict is updated with fabric_name set to valid and invalid
#         values of ``fabric_name``

#     Expected Result
#     -   ``ValueError`` is raised when fabric_name is not a valid value
#     -   Exception message matches expected
#     -   Exception is not raised when fabric_name is a valid value
#     """

#     with does_not_raise():
#         instance = maintenance_mode_info

#     config = copy.deepcopy(CONFIG[0])
#     config["fabric_name"] = param
#     match = r"ConversionUtils\.validate_fabric_name:\s+"
#     match += rf"Invalid fabric name: {param}\.\s+"
#     match += r"Fabric name must start with a letter A-Z or a-z and contain\s+"
#     match += r"only the characters in:"
#     if raises:
#         with pytest.raises(raises, match=match):
#             instance.config = [config]
#     else:
#         instance.config = [config]
#         assert instance.config[0]["fabric_name"] == param


# @pytest.mark.parametrize(
#     "param, raises",
#     [
#         ("maintenance", None),
#         ("normal", None),
#         (10, ValueError),
#         (["192.168.1.2"], ValueError),
#         ({"ip_address": "192.168.1.2"}, ValueError),
#     ],
# )
# def test_maintenance_mode_info_00600(maintenance_mode_info, param, raises) -> None:
#     """
#     Classes and Methods
#     - MaintenanceModeInfo()
#         - __init__()
#         - verify_config_parameters()
#         - config.setter

#     Summary
#     -   Verify MaintenanceModeInfo().verify_config_parameters() re-raises
#             -   ``ValueError`` if:
#                     - ``mode`` raises ``ValueError`` due to being an
#                         invalid value.

#     Code Flow - Setup
#     -   MaintenanceModeInfo() is instantiated

#     Code Flow - Test
#     -   MaintenanceModeInfo().config is set to a dict.
#     -   The dict is updated with mode set to valid and invalid
#         values of ``mode``

#     Expected Result
#     -   ``ValueError`` is raised when mode is not a valid value
#     -   Exception message matches expected
#     -   Exception is not raised when mode is a valid value
#     """

#     with does_not_raise():
#         instance = maintenance_mode_info

#     config = copy.deepcopy(CONFIG[0])
#     config["mode"] = param
#     match = r"MaintenanceMode\.verify_mode:\s+"
#     match += r"mode must be one of\s+"
#     if raises:
#         with pytest.raises(raises, match=match):
#             instance.config = [config]
#     else:
#         instance.config = [config]
#         assert instance.config[0]["mode"] == param


# @pytest.mark.parametrize(
#     "endpoint_instance, mock_exception, expected_exception, mock_message",
#     [
#         ("ep_maintenance_mode_disable", TypeError, ValueError, "Bad type"),
#         ("ep_maintenance_mode_disable", ValueError, ValueError, "Bad value"),
#         ("ep_maintenance_mode_enable", TypeError, ValueError, "Bad type"),
#         ("ep_maintenance_mode_enable", ValueError, ValueError, "Bad value"),
#     ],
# )
# def test_maintenance_mode_info_00700(
#     monkeypatch,
#     maintenance_mode_info,
#     endpoint_instance,
#     mock_exception,
#     expected_exception,
#     mock_message,
# ) -> None:
#     """
#     Classes and Methods
#     - MaintenanceModeInfo()
#         - __init__()
#         - refresh()

#     Summary
#     -   Verify MaintenanceModeInfo().change_system_mode() raises ``ValueError``
#         when ``EpMaintenanceModeEnable`` or ``EpMaintenanceModeDisable`` raise
#         any of:
#             -   ``TypeError``
#             -   ``ValueError``

#     Code Flow - Setup
#     -   MaintenanceModeInfo() is instantiated
#     -   Required attributes are set
#     -   EpMaintenanceModeEnable() is mocked to raise each
#         of the above exceptions
#     -   EpMaintenanceModeDisable() is mocked to raise each
#         of the above exceptions

#     Code Flow - Test
#     -   MaintenanceModeInfo().refresh() is called for each exception

#     Expected Result
#     -   ``ValueError`` is raised.
#     -   Exception message matches expected.
#     """

#     class MockEndpoint:
#         """
#         Mock Ep*() class
#         """

#         def __init__(self):
#             self._fabric_name = None
#             self._serial_number = None

#         @property
#         def fabric_name(self):
#             """
#             Mock fabric_name getter/setter
#             """
#             return self._fabric_name

#         @fabric_name.setter
#         def fabric_name(self, value):
#             raise mock_exception(mock_message)

#         @property
#         def serial_number(self):
#             """
#             Mock serial_number getter/setter
#             """
#             return self._serial_number

#         @serial_number.setter
#         def serial_number(self, value):
#             self._serial_number = value

#     with does_not_raise():
#         instance = maintenance_mode_info
#         config = copy.deepcopy(CONFIG[0])
#         if endpoint_instance == "ep_maintenance_mode_disable":
#             config["mode"] = "normal"
#         instance.config = [config]
#         instance.rest_send = RestSend({})
#         instance.results = Results()

#     monkeypatch.setattr(instance, endpoint_instance, MockEndpoint())
#     with pytest.raises(expected_exception, match=mock_message):
#         instance.refresh()


# @pytest.mark.parametrize(
#     "endpoint_instance, mock_exception, expected_exception, mock_message",
#     [
#         ("ep_fabric_config_deploy", TypeError, ValueError, "Bad type"),
#         ("ep_fabric_config_deploy", ValueError, ValueError, "Bad value"),
#     ],
# )
# def test_maintenance_mode_info_00800(
#     monkeypatch,
#     maintenance_mode_info,
#     endpoint_instance,
#     mock_exception,
#     expected_exception,
#     mock_message,
# ) -> None:
#     """
#     Classes and Methods
#     - MaintenanceModeInfo()
#         - __init__()
#         - refresh()

#     Summary
#     -   Verify MaintenanceModeInfo().deploy_switches() raises ``ValueError``
#         when ``EpFabricConfigDeploy`` raises any of:
#             -   ``TypeError``
#             -   ``ValueError``


#     Code Flow - Setup
#     -   MaintenanceModeInfo() is instantiated
#     -   Required attributes are set
#     -   EpFabricConfigDeploy() is mocked to raise each of the above exceptions

#     Code Flow - Test
#     -   MaintenanceModeInfo().refresh() is called for each exception

#     Expected Result
#     -   ``TypeError`` and ``ValueError`` are raised.
#     -   Exception message matches expected.
#     """

#     class MockEndpoint:
#         """
#         Mock EpFabricConfigDeploy() class
#         """

#         def __init__(self):
#             self._fabric_name = None
#             self._switch_id = None

#         @property
#         def fabric_name(self):
#             """
#             Mock fabric_name getter/setter
#             """
#             return self._fabric_name

#         @fabric_name.setter
#         def fabric_name(self, value):
#             raise mock_exception(mock_message)

#         @property
#         def switch_id(self):
#             """
#             Mock switch_id getter/setter
#             """
#             return self._switch_id

#         @switch_id.setter
#         def switch_id(self, value):
#             self._switch_id = value

#     def responses():
#         yield {"MESSAGE": "OK", "RETURN_CODE": 200, "DATA": {"status": "Success"}}

#     mock_sender = MockSender()
#     mock_sender.gen = ResponseGenerator(responses())
#     rest_send = RestSend({"state": "merged", "check_mode": False})
#     rest_send.sender = mock_sender
#     rest_send.response_handler = ResponseHandler()
#     rest_send.unit_test = True
#     rest_send.timeout = 1

#     config = copy.deepcopy(CONFIG[0])
#     config["deploy"] = True

#     with does_not_raise():
#         instance = maintenance_mode_info
#         instance.config = [config]
#         instance.rest_send = rest_send
#         instance.results = Results()

#     monkeypatch.setattr(instance, endpoint_instance, MockEndpoint())
#     with pytest.raises(expected_exception, match=mock_message):
#         instance.refresh()


# @pytest.mark.parametrize(
#     "mock_exception, expected_exception, mock_message",
#     [
#         (TypeError, ValueError, r"Converted TypeError to ValueError"),
#         (ValueError, ValueError, r"Converted ValueError to ValueError"),
#     ],
# )
# def test_maintenance_mode_info_00900(
#     maintenance_mode_info, mock_exception, expected_exception, mock_message
# ) -> None:
#     """
#     Classes and Methods
#     - MaintenanceModeInfo()
#         - __init__()
#         - change_system_mode()


#     Summary
#     -   Verify MaintenanceModeInfo().change_system_mode() raises ``ValueError``
#         when ``MaintenanceModeInfo().results()`` raises any of:
#             -   ``TypeError``
#             -   ``ValueError``


#     Code Flow - Setup
#     -   MaintenanceModeInfo() is instantiated
#     -   Required attributes are set
#     -   Results().response_current.setter is mocked to raise each of the above
#         exceptions

#     Code Flow - Test
#     -   MaintenanceModeInfo().refresh() is called for each exception

#     Expected Result
#     -   ``ValueError`` is raised
#     -   Exception message matches expected
#     """

#     class MockResults:
#         """
#         Mock the Results class
#         """

#         class_name = "Results"

#         def register_task_result(self, *args):
#             """
#             do nothing
#             """

#         @property
#         def response_current(self):
#             """
#             mock response_current getter
#             """
#             return {"success": True}

#         @response_current.setter
#         def response_current(self, *args):
#             raise mock_exception(mock_message)

#     def responses():
#         yield {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {"status": "Success"}}

#     mock_sender = MockSender()
#     mock_sender.gen = ResponseGenerator(responses())

#     with does_not_raise():
#         rest_send = RestSend({"state": "merged", "check_mode": False})
#         rest_send.sender = mock_sender
#         rest_send.response_handler = ResponseHandler()
#         instance = maintenance_mode_info
#         instance.rest_send = rest_send
#         instance.rest_send.unit_test = True
#         instance.rest_send.timeout = 1
#         instance.config = CONFIG
#         instance.results = MockResults()

#     with pytest.raises(expected_exception, match=mock_message):
#         instance.refresh()


# def test_maintenance_mode_info_01000(monkeypatch, maintenance_mode_info) -> None:
#     """
#     Classes and Methods
#     - MaintenanceModeInfo()
#         - __init__()
#         - refresh()

#     Summary
#     -   Verify MaintenanceModeInfo().refresh() raises ``ValueError`` when
#         ``MaintenanceModeInfo().deploy_switches()`` raises
#         ``ControllerResponseError`` when the RETURN_CODE in the
#         response is not 200.

#     Code Flow - Setup
#     -   MaintenanceModeInfo() is instantiated
#     -   Required attributes are set

#     Code Flow - Test
#     -   MaintenanceModeInfo().refresh() is called with simulated responses:
#             -   200 response for ``change_system_mode()``
#             -   500 response ``deploy_switches()``

#     Expected Result
#     -   ``ValueError``is raised.
#     -   Exception message matches expected.
#     """

#     def responses():
#         yield {"MESSAGE": "OK", "RETURN_CODE": 200, "DATA": {"status": "Success"}}
#         yield {
#             "MESSAGE": "Internal server error",
#             "RETURN_CODE": 500,
#             "DATA": {"status": "Success"},
#         }

#     mock_sender = MockSender()
#     mock_sender.gen = ResponseGenerator(responses())
#     rest_send = RestSend({"state": "merged", "check_mode": False})
#     rest_send.sender = mock_sender
#     rest_send.response_handler = ResponseHandler()
#     rest_send.unit_test = True
#     rest_send.timeout = 1

#     config = copy.deepcopy(CONFIG[0])
#     config["deploy"] = True

#     with does_not_raise():
#         instance = maintenance_mode_info
#         instance.config = [config]
#         instance.rest_send = rest_send
#         instance.results = Results()

#     match = r"MaintenanceMode\.deploy_switches:\s+"
#     match += r"Unable to deploy switches:\s+"
#     match += r"fabric_name VXLAN_Fabric,\s+"
#     match += r"serial_numbers FDO22180ASJ\.\s+"
#     match += r"Got response.*\."
#     with pytest.raises(ValueError, match=match):
#         instance.refresh()
