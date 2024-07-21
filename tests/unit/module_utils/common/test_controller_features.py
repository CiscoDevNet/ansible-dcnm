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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.controller_features import \
    ControllerFeatures
from ansible_collections.cisco.dcnm.plugins.module_utils.common.exceptions import \
    ControllerResponseError
from ansible_collections.cisco.dcnm.plugins.module_utils.common.response_handler import \
    ResponseHandler
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_file import \
    Sender
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import (
    MockAnsibleModule, ResponseGenerator, controller_features_fixture,
    does_not_raise, params, responses_controller_features)


def test_controller_features_00000(controller_features) -> None:
    """
    Classes and Methods
    - ControllerFeatures
        - __init__()

    Test
    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = controller_features
    assert instance.class_name == "ControllerFeatures"
    assert instance.ep_features.class_name == "EpFeatures"
    assert instance.conversion.class_name == "ConversionUtils"
    assert instance.filter is None
    assert instance.response_data is None
    assert instance.rest_send is None


def test_controller_features_00030(controller_features) -> None:
    """
    ### Classes and Methods

    - ControllerFeatures()
        - __init__()
        - refresh()

    ### Summary
    Verify ``refresh`` raises ``ValueError`` when ``rest_send`` is not set.

    ### Setup

    -   ControllerFeatures() is instantiated

    ### Test

    -   ``refresh`` is called without having first set ``rest_send``.

    ### Expected Result
    -   ``ValueError`` is raised
    -   Exception message matches expected.
    """
    with does_not_raise():
        instance = controller_features

    match = r"ControllerFeatures\.refresh: "
    match += r"ControllerFeatures\.rest_send must be set before calling\s+"
    match += r"refresh\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_controller_features_00040(monkeypatch, controller_features) -> None:
    """
    ### Classes and Methods

    - ControllerFeatures()
        - __init__()
        - refresh()

    ### Summary

    - Verify refresh() success case:
        -   RETURN_CODE is 200.
        -   Controller response contains expected structure and values.

    ### Setup

    -   ControllerFeatures() is instantiated
    -   ControllerFeatures().RestSend() is instantiated
    -   ControllerFeatures().refresh() is called
    -   responses_ControllerFeatures contains a dict with:
        - RETURN_CODE == 200
        - DATA == [<controller_features_info from controller>]

    ### Test

    -   ControllerFeatures().refresh() is called

    ### Expected Result

    -   Exception is not raised
    -   instance.response_data returns expected controller features data
    -   ControllerFeatures()._properties are updated
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_controller_features(key)

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
        instance = controller_features
        instance.rest_send = rest_send
        instance.refresh()
        instance.filter = "pmn"

    assert instance.filter == "pmn"
    assert instance.admin_state == "enabled"
    assert instance.oper_state == "started"
    assert instance.enabled is True
    assert instance.started is True
    assert isinstance(instance.response_data, dict)
    assert instance.rest_send.response_current.get("MESSAGE", None) == "OK"
    assert instance.rest_send.response_current.get("RETURN_CODE", None) == 200
    assert instance.rest_send.result_current.get("success", None) is True
    assert instance.rest_send.result_current.get("found", None) is True

    with does_not_raise():
        instance.filter = "vxlan"

    assert instance.filter == "vxlan"
    assert instance.admin_state == "disabled"
    assert instance.oper_state == "stopped"
    assert instance.enabled is False
    assert instance.started is False


def test_controller_features_00050(monkeypatch, controller_features) -> None:
    """
    ### Classes and Methods

    - ControllerFeatures()
        - __init__()
        - refresh()

    ### Summary
    Verify refresh() failure behavior. RETURN_CODE is 500.

    ### Setup

    -   ControllerFeatures() is instantiated
    -   ControllerFeatures().RestSend() is instantiated
    -   ControllerFeatures().refresh() is called
    -   responses_ControllerFeatures contains a dict with:
        - RETURN_CODE == 500

    ### Test

    -   ControllerFeatures().refresh() is called

    ### Expected Result

    -   ``ControllerResponseError`` is raised
    -   Exception message matches expected
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_controller_features(key)

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
        instance = controller_features
        instance.rest_send = rest_send

    match = r"ControllerFeatures\.refresh: Bad controller response:"
    with pytest.raises(ControllerResponseError, match=match):
        instance.refresh()


def test_controller_features_00060(monkeypatch, controller_features) -> None:
    """
    ### Classes and Methods

    - ControllerFeatures()
        - __init__()
        - refresh()

    ### Summary
    Verify refresh() failure due to unexpected controller response structure.

        -   RETURN_CODE is 200.
        -   DATA is missing.

    ### Setup

    -   ControllerFeatures() is instantiated
    -   ControllerFeatures().RestSend() is instantiated
    -   ControllerFeatures().refresh() is called
    -   responses_ControllerFeatures contains a dict with:
        - RETURN_CODE == 200
        - DATA is missing

    ### Test
    -   ControllerFeatures().refresh() is called

    ### Expected Result
    -   ``ControllerResponseError`` is raised
    -   Exception message matches expected
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_controller_features(key)

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
        instance = controller_features
        instance.rest_send = rest_send

    match = r"ControllerFeatures\.refresh: "
    match += r"Controller response does not match expected structure:"
    with pytest.raises(ControllerResponseError, match=match):
        instance.refresh()


MATCH_00070 = r"ControllerFeatures\.rest_send: "
MATCH_00070 += r"value must be an instance of RestSend\..*"


@pytest.mark.parametrize(
    "value, does_raise, expected",
    [
        (RestSend(params), False, does_not_raise()),
        (ControllerFeatures(), True, pytest.raises(TypeError, match=MATCH_00070)),
        (None, True, pytest.raises(TypeError, match=MATCH_00070)),
        ("foo", True, pytest.raises(TypeError, match=MATCH_00070)),
        (10, True, pytest.raises(TypeError, match=MATCH_00070)),
        ([10], True, pytest.raises(TypeError, match=MATCH_00070)),
        ({10}, True, pytest.raises(TypeError, match=MATCH_00070)),
    ],
)
def test_controller_features_00070(
    controller_features, value, does_raise, expected
) -> None:
    """
    Classes and Methods
    - ControllerFeatures
        - __init__()
        - rest_send.setter

    Test
    -   ``TypeError`` is raised when ControllerFeatures().rest_send is
         passed a value that is not an instance of RestSend()
    """
    with does_not_raise():
        instance = controller_features
    with expected:
        instance.rest_send = value
    if not does_raise:
        assert instance.rest_send == value
