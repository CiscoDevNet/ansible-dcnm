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
# pylint: disable=invalid-name
"""
Unit tests for FabricSummary (v2) class
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2025 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import inspect

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.exceptions import ControllerResponseError
from ansible_collections.cisco.dcnm.plugins.module_utils.common.response_handler import ResponseHandler
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_file import Sender
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    does_not_raise,
    fabric_summary_v2_fixture,
    responses_fabric_summary_v2,
)


def test_fabric_summary_v2_00010(fabric_summary_v2) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricSummary
        - __init__()

    Test
    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_summary_v2
    assert instance.class_name == "FabricSummary"
    assert instance.data == {}
    assert instance.refreshed is False
    assert instance._conversion.class_name == "ConversionUtils"
    assert instance._ep_fabric_summary.class_name == "EpFabricSummary"
    assert instance._results.class_name == "Results"
    assert instance._border_gateway_count == 0
    assert instance._device_count == 0
    assert instance._fabric_name == ""
    assert instance._leaf_count == 0
    assert instance._spine_count == 0


def test_fabric_summary_v2_00030(fabric_summary_v2) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricSummary()
        - __init__()
        - refresh()

    Summary
    -   Verify FabricSummary().refresh() raises ``ValueError``
        when ``FabricSummary().fabric_name`` is not set.

    Code Flow - Setup
    -   FabricSummary() is instantiated
    -   FabricSummary().rest_send is set

    Code Flow - Test
    -   FabricSummary().refresh() is called without having
        first set FabricSummary().fabric_name

    Expected Result
    -   ``ValueError`` is raised
    -   Exception message matches expected
    """

    def responses():
        yield {"key": "value"}

    with does_not_raise():
        sender = Sender()
        sender.gen = ResponseGenerator(responses())
        instance = fabric_summary_v2
        instance.rest_send = RestSend(params={"check_mode": False, "state": "query"})
        instance.rest_send.sender = sender

    match = r"FabricSummary\.refresh: "
    match += r"Set FabricSummary\.fabric_name prior to calling "
    match += r"FabricSummary\.refresh\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_fabric_summary_v2_00031(fabric_summary_v2) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricSummary()
        - __init__()
        - refresh()

    Summary
    -   Verify FabricSummary().refresh() raises ``ValueError``
        when ``FabricSummary().rest_send`` is not set.

    Code Flow - Setup
    -   FabricSummary() is instantiated
    -   FabricSummary().fabric_name is set

    Code Flow - Test
    -   FabricSummary().refresh() is called without having
        first set FabricSummary().rest_send

    Expected Result
    -   ``ValueError`` is raised
    -   Exception message matches expected
    """
    with does_not_raise():
        instance = fabric_summary_v2
        instance.fabric_name = "MyFabric"

    match = r"FabricSummary\.refresh: "
    match += r"Set FabricSummary\.rest_send prior to calling "
    match += r"FabricSummary\.refresh\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_fabric_summary_v2_00032(monkeypatch, fabric_summary_v2) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricSummary()
        - __init__()
        - refresh()
        - _set_fabric_summary_endpoint()

    Summary
    -   Verify that FabricSummary()._set_fabric_summary_endpoint()
        re-raises ``ValueError`` when EpFabricSummary() raises
        ``ValueError``.
    """

    class MockEpFabricSummary:  # pylint: disable=too-few-public-methods
        """
        Mock the EpFabricSummary.fabric_name getter property to raise ``ValueError``.
        """

        def validate_fabric_name(self, value="MyFabric"):
            """
            Mocked method required for test, but not relevant to test result.
            """

        @property
        def fabric_name(self):
            """
            -   Mocked fabric_name property getter
            """

        @fabric_name.setter
        def fabric_name(self, value):
            """
            -   Mocked fabric_name property setter
            """
            msg = "mocked MockEpFabricSummary().fabric_name setter exception."
            raise ValueError(msg)

    def responses():
        yield {"key": "value"}

    with does_not_raise():
        instance = fabric_summary_v2
        monkeypatch.setattr(instance, "_ep_fabric_summary", MockEpFabricSummary())
        instance.fabric_name = "MyFabric"
        sender = Sender()
        sender.gen = ResponseGenerator(responses())
        instance.rest_send = RestSend(params={"check_mode": False, "state": "query"})
        instance.rest_send.sender = sender

    match = r"Error retrieving fabric_summary endpoint\. Detail: mocked MockEpFabricSummary\(\)\.fabric_name setter exception\."

    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_fabric_summary_v2_00033(fabric_summary_v2) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricSummary()
        - __init__()
        - refresh()
        - _update_device_counts()

    Summary
    - Verify refresh() success case with populated fabric:
        -   RETURN_CODE is 200.
        -   Controller response contains one fabric (f1).
        -   Fabric contains 2x leaf, 1x spine, 1x border_gateway.

    Code Flow - Setup
    -   FabricSummary() is instantiated
    -   FabricSummary().RestSend() is instantiated
    -   FabricSummary().Results() is instantiated
    -   FabricSummary().refresh() is called
    -   responses_FabricSummary contains a dict with:
        - RETURN_CODE == 200
        - DATA == [<fabric_summary_info from controller>]

    Code Flow - Test
    -   FabricSummary().refresh() is called

    Expected Result
    -   Exception is not raised
    -   instance.data returns expected fabric data
    -   Results() are updated
    -   FabricSummary().refreshed is True
    -   FabricSummary()._properties are updated
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_summary_v2(key)

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    rest_send = RestSend(params={"check_mode": False, "state": "query"})
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    with does_not_raise():
        instance = fabric_summary_v2
        instance.rest_send = rest_send
        instance.fabric_name = "MyFabric"

    with does_not_raise():
        instance.refresh()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.result) == 1
    assert len(instance.results.response) == 1

    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.result[0].get("found", None) is True
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed

    assert instance.data.get("switchRoles", {}).get("leaf", None) == 2
    assert instance.data.get("switchRoles", {}).get("spine", None) == 1
    assert instance.data.get("switchRoles", {}).get("border gateway", None) == 1
    assert instance.border_gateway_count == 1
    assert instance.device_count == 4
    assert instance.leaf_count == 2
    assert instance.spine_count == 1
    assert instance.fabric_is_empty is False


def test_fabric_summary_v2_00034(fabric_summary_v2) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricSummary()
        - __init__()
        - refresh()
        - _update_device_counts()

    Summary
    - Verify refresh() success case with empty fabric:
        -   RETURN_CODE is 200.
        -   Controller response contains one fabric (f1).
        -   Fabric does not contain any switches.

    Code Flow - Setup
    -   FabricSummary() is instantiated
    -   FabricSummary().RestSend() is instantiated
    -   FabricSummary().Results() is instantiated
    -   FabricSummary().refresh() is called
    -   responses_FabricSummary contains a dict with:
        - RETURN_CODE == 200
        - DATA == [<fabric_summary_info from controller>]

    Code Flow - Test
    -   FabricSummary().refresh() is called

    Expected Result
    -   Exception is not raised
    -   instance.all_data returns expected fabric data
    -   Results() are updated
    -   FabricSummary().refreshed is True
    -   FabricSummary()._properties are updated
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_summary_v2(key)

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    rest_send = RestSend(params={"check_mode": False, "state": "query"})
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_summary_v2
        instance.rest_send = rest_send
        instance.fabric_name = "MyFabric"

    with does_not_raise():
        instance.refresh()

    assert instance.refreshed is True

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.result) == 1
    assert len(instance.results.response) == 1

    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.result[0].get("found", None) is True
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed

    assert instance.all_data.get("switchRoles", {}).get("leaf", None) is None
    assert instance.all_data.get("switchRoles", {}).get("spine", None) is None
    assert instance.all_data.get("switchRoles", {}).get("border gateway", None) is None
    assert instance.border_gateway_count == 0
    assert instance.device_count == 0
    assert instance.leaf_count == 0
    assert instance.spine_count == 0
    assert instance.fabric_is_empty is True


def test_fabric_summary_v2_00035(fabric_summary_v2) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricSummary()
        - __init__()
        - refresh()
        - _update_device_counts()

    Summary
    - Verify refresh() failure case:
        -   RETURN_CODE is 404.
        -   Controller response when fabric does not exist

    Code Flow - Setup
    -   FabricSummary() is instantiated.
    -   FabricSummary().RestSend() is instantiated.
    -   FabricSummary().fabric_name is set to a fabric that does not exist.
    -   FabricSummary().refresh() is called.
    -   responses_FabricSummary contains a dict with:
        - RETURN_CODE == 404
        - DATA == {
            "timestamp": 1713467047741,
            "status": 404,
            "error": "Not Found",
            "path": "/rest/control/switches/MyFabric/overview"
        }

    Code Flow - Test
    -   FabricSummary().refresh() is called

    Expected Result
    -   ``ControllerResponseException`` is raised
    -   instance.data contains error data
    -   Results() are updated
    -   FabricSummary().refreshed is False
    -   FabricSummary()._properties remain at their default values
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_summary_v2(key)

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    rest_send = RestSend(params={"check_mode": False, "state": "query"})
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_summary_v2
        instance.rest_send = rest_send
        instance.rest_send.unit_test = True
        instance.rest_send.timeout = 1
        instance.fabric_name = "MyFabric"

    match = r"FabricSummary\._verify_controller_response:\s+"
    match += r"Failed to retrieve fabric_summary for fabric_name MyFabric\.\s+"
    match += r"RETURN_CODE: 404\.\s+"
    match += r"MESSAGE: Not Found\."
    with pytest.raises(ControllerResponseError, match=match):
        instance.refresh()

    assert instance.refreshed is False

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.result) == 1
    assert len(instance.results.response) == 1

    assert instance.results.response[0].get("RETURN_CODE", None) == 404
    assert instance.results.result[0].get("found", None) is False
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed

    assert instance.data.get("switchRoles", {}).get("leaf", None) is None
    assert instance.data.get("switchRoles", {}).get("spine", None) is None
    assert instance.data.get("switchRoles", {}).get("border gateway", None) is None


def test_fabric_summary_v2_00036(fabric_summary_v2) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricSummary()
        - __init__()
        - refresh()
        - _update_device_counts()

    Summary
    - Verify refresh() failure case:
        -   RETURN_CODE is 200.
        -   DATA field is missing in the response.
        -   This shouldn't happen, but we need to handle it.

    Code Flow - Setup
    -   FabricSummary() is instantiated.
    -   FabricSummary().RestSend() is instantiated.
    -   FabricSummary().fabric_name is set to a fabric that does not exist.
    -   FabricSummary().refresh() is called.
    -   responses_FabricSummary contains a dict with:
        - RETURN_CODE == 200
        - DATA missing

    Code Flow - Test
    -   FabricSummary().refresh() is called

    Expected Result
    -   ``ValueError`` is raised in FabricSummary()._verify_controller_response()
    -   instance.data is empty
    -   Results() are updated
    -   FabricSummary().refreshed is False
    -   FabricSummary()._properties remain at their default values
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_summary_v2(key)

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    rest_send = RestSend(params={"check_mode": False, "state": "query"})
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_summary_v2
        instance.rest_send = rest_send
        instance.rest_send.unit_test = True
        instance.rest_send.timeout = 1
        instance.fabric_name = "MyFabric"

    match = r"FabricSummary.\_verify_controller_response:\s+"
    match += r"Controller responded with missing or empty DATA\."
    with pytest.raises(ControllerResponseError, match=match):
        instance.refresh()

    assert instance.refreshed is False

    assert instance.data == {}

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.result) == 1
    assert len(instance.results.response) == 1

    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.result[0].get("found", None) is True
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_fabric_summary_v2_00040(fabric_summary_v2) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricSummary()
        - __init__()
        - all_data getter

    Summary
    -   Verify FabricSummary().all_data raises ``ValueError``
        when ``FabricSummary().refresh()`` has not been called.

    Code Flow - Setup
    -   FabricSummary() is instantiated

    Code Flow - Test
    -   FabricSummary().all_data is accessed without having
        first called FabricSummary().refresh()

    Expected Result
    -   ``ValueError`` is raised
    -   Exception message matches expected
    """
    with does_not_raise():
        instance = fabric_summary_v2

    match = r"FabricSummary\.refresh\(\) must be called before "
    match += r"accessing FabricSummary\.all_data\."
    with pytest.raises(ValueError, match=match):
        instance.all_data  # pylint: disable=pointless-statement


def test_fabric_summary_v2_00050(fabric_summary_v2) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricSummary()
        - __init__()
        - border_gateway_count getter

    Summary
    -   Verify FabricSummary().border_gateway_count raises ``ValueError``
        when ``FabricSummary().refresh()`` has not been called.

    Code Flow - Setup
    -   FabricSummary() is instantiated

    Code Flow - Test
    -   FabricSummary().border_gateway_count is accessed without having
        first called FabricSummary().refresh()

    Expected Result
    -   ``ValueError`` is raised
    -   Exception message matches expected
    """
    with does_not_raise():
        instance = fabric_summary_v2

    match = r"FabricSummary\.refresh\(\) must be called before "
    match += r"accessing FabricSummary\.border_gateway_count\."
    with pytest.raises(ValueError, match=match):
        instance.border_gateway_count  # pylint: disable=pointless-statement


def test_fabric_summary_v2_00060(fabric_summary_v2) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricSummary()
        - __init__()
        - device_count getter

    Summary
    -   Verify FabricSummary().device_count raises ``ValueError``
        when ``FabricSummary().refresh()`` has not been called.

    Code Flow - Setup
    -   FabricSummary() is instantiated

    Code Flow - Test
    -   FabricSummary().device_count is accessed without having
        first called FabricSummary().refresh()

    Expected Result
    -   ``ValueError`` is raised
    -   Exception message matches expected
    """
    with does_not_raise():
        instance = fabric_summary_v2

    match = r"FabricSummary\.refresh\(\) must be called before "
    match += r"accessing FabricSummary\.device_count\."
    with pytest.raises(ValueError, match=match):
        instance.device_count  # pylint: disable=pointless-statement


def test_fabric_summary_v2_00070(fabric_summary_v2) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricSummary()
        - __init__()
        - fabric_is_empty getter

    Summary
    -   Verify FabricSummary().fabric_is_empty raises ``ValueError``
        when ``FabricSummary().refresh()`` has not been called.

    Code Flow - Setup
    -   FabricSummary() is instantiated

    Code Flow - Test
    -   FabricSummary().fabric_is_empty is accessed without having
        first called FabricSummary().refresh()

    Expected Result
    -   ``ValueError`` is raised
    -   Exception message matches expected
    """
    with does_not_raise():
        instance = fabric_summary_v2

    match = r"FabricSummary\.refresh\(\) must be called before "
    match += r"accessing FabricSummary\.fabric_is_empty\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_is_empty  # pylint: disable=pointless-statement


MATCH_00080a = r"ConversionUtils\.validate_fabric_name: "
MATCH_00080a += r"Invalid fabric name\. "
MATCH_00080a += r"Expected string\. Got.*\."

MATCH_00080b = r"ConversionUtils\.validate_fabric_name: "
MATCH_00080b += r"Invalid fabric name:.*\. "
MATCH_00080b += "Fabric name must start with a letter A-Z or a-z and "
MATCH_00080b += r"contain only the characters in: \[A-Z,a-z,0-9,-,_\]\."


@pytest.mark.parametrize(
    "fabric_name, expected, does_raise",
    [
        ("MyFabric", does_not_raise(), False),
        ("My_Fabric", does_not_raise(), False),
        ("My-Fabric", does_not_raise(), False),
        ("M", does_not_raise(), False),
        (1, pytest.raises(ValueError, match=MATCH_00080a), True),
        ({}, pytest.raises(ValueError, match=MATCH_00080a), True),
        ([1, 2, 3], pytest.raises(ValueError, match=MATCH_00080a), True),
        ("1", pytest.raises(ValueError, match=MATCH_00080b), True),
        ("-MyFabric", pytest.raises(ValueError, match=MATCH_00080b), True),
        ("_MyFabric", pytest.raises(ValueError, match=MATCH_00080b), True),
        ("1MyFabric", pytest.raises(ValueError, match=MATCH_00080b), True),
        ("My Fabric", pytest.raises(ValueError, match=MATCH_00080b), True),
        ("My*Fabric", pytest.raises(ValueError, match=MATCH_00080b), True),
    ],
)
def test_fabric_summary_v2_00080(fabric_summary_v2, fabric_name, expected, does_raise) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricSummary()
        - __init__()
        - fabric_name setter/getter

    Summary
    -   Verify FabricSummary().fabric_name re-raises ``ValueError``
        when fabric_name is invalid.

    Code Flow - Setup
    -   FabricSummary() is instantiated

    Code Flow - Test
    -   FabricSummary().fabric_name is set to a value that would
        cause the controller to return an error.

    Expected Result
    -   ``ValueError`` is raised
    -   Exception message matches expected
    """
    with does_not_raise():
        instance = fabric_summary_v2
    with expected:
        instance.fabric_name = fabric_name
    if does_raise is False:
        assert instance.fabric_name == fabric_name


def test_fabric_summary_v2_00090(fabric_summary_v2) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricSummary()
        - __init__()
        - leaf_count getter

    Summary
    -   Verify FabricSummary().leaf_count raises ``ValueError``
        when ``FabricSummary().refresh()`` has not been called.

    Code Flow - Setup
    -   FabricSummary() is instantiated

    Code Flow - Test
    -   FabricSummary().leaf_count is accessed without having
        first called FabricSummary().refresh()

    Expected Result
    -   ``ValueError`` is raised
    -   Exception message matches expected
    """
    with does_not_raise():
        instance = fabric_summary_v2

    match = r"FabricSummary\.refresh\(\) must be called before "
    match += r"accessing FabricSummary\.leaf_count\."
    with pytest.raises(ValueError, match=match):
        instance.leaf_count  # pylint: disable=pointless-statement


def test_fabric_summary_v2_00100(fabric_summary_v2) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricSummary()
        - __init__()
        - spine_count getter

    Summary
    -   Verify FabricSummary().spine_count raises ``ValueError``
        when ``FabricSummary().refresh()`` has not been called.

    Code Flow - Setup
    -   FabricSummary() is instantiated

    Code Flow - Test
    -   FabricSummary().spine_count is accessed without having
        first called FabricSummary().refresh()

    Expected Result
    -   ``ValueError`` is raised
    -   Exception message matches expected
    """
    with does_not_raise():
        instance = fabric_summary_v2

    match = r"FabricSummary\.refresh\(\) must be called before "
    match += r"accessing FabricSummary\.spine_count\."
    with pytest.raises(ValueError, match=match):
        instance.spine_count  # pylint: disable=pointless-statement
