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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.fm import (
    EpFeatures,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import (
    ConversionUtils,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.common.controller_features import (
    ControllerFeatures,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.common.exceptions import (
    ControllerResponseError,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send import (
    RestSend,
)
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import (
    MockAnsibleModule,
    ResponseGenerator,
    does_not_raise,
    controller_features_fixture,
    responses_controller_features,
    params,
)


def test_controller_features_00010(controller_features) -> None:
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
    assert isinstance(instance.api_features, EpFeatures)
    assert isinstance(instance.conversion, ConversionUtils)
    assert instance.check_mode is False
    assert instance.filter is None
    assert instance.response is None
    assert instance.response_data is None
    assert instance.rest_send is None
    assert instance.result is None


def test_controller_features_00020(controller_features) -> None:
    """
    Classes and Methods
    - ControllerFeatures
        - __init__()

    Test
    - ``ValueError`` is raised when params is missing check_mode
    """
    params = {}
    match = r"ControllerFeatures\.__init__\(\):\s+"
    match += r"check_mode is required\."
    with pytest.raises(ValueError, match=match):
        instance = ControllerFeatures(params)  # pylint: disable=unused-variable


def test_controller_features_00030(controller_features) -> None:
    """
    Classes and Methods
    - ControllerFeatures()
        - __init__()
        - refresh()

    Summary
    -   Verify ControllerFeatures().refresh() raises ``ValueError``
        when ``ControllerFeatures().rest_send`` is not set.

    Code Flow - Setup
    -   ControllerFeatures() is instantiated

    Code Flow - Test
    -   ControllerFeatures().refresh() is called without having
        first set ControllerFeatures().rest_send

    Expected Result
    -   ``ValueError`` is raised
    -   Exception message matches expected
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
    Classes and Methods
    - ControllerFeatures()
        - __init__()
        - refresh()

    Summary
    - Verify refresh() success case:
        -   RETURN_CODE is 200.
        -   Controller response contains expected structure and values.

    Code Flow - Setup
    -   ControllerFeatures() is instantiated
    -   dcnm_send() is patched to return the mocked controller response
    -   ControllerFeatures().RestSend() is instantiated
    -   ControllerFeatures().refresh() is called
    -   responses_ControllerFeatures contains a dict with:
        - RETURN_CODE == 200
        - DATA == [<controller_features_info from controller>]

    Code Flow - Test
    -   ControllerFeatures().refresh() is called

    Expected Result
    -   Exception is not raised
    -   instance.response_data returns expected controller features data
    -   ControllerFeatures()._properties are updated
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_controller_features(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = controller_features
        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True
        instance.rest_send.timeout = 1

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
        instance.refresh()
        instance.filter = "pmn"

    assert instance.filter == "pmn"
    assert instance.admin_state == "enabled"
    assert instance.oper_state == "started"
    assert instance.enabled is True
    assert instance.started is True
    assert isinstance(instance.response, dict)
    assert isinstance(instance.response_data, dict)
    assert isinstance(instance.result, dict)
    assert instance.response.get("MESSAGE", None) == "OK"
    assert instance.response.get("RETURN_CODE", None) == 200
    assert instance.result.get("success", None) is True
    assert instance.result.get("found", None) is True

    with does_not_raise():
        instance.filter = "vxlan"

    assert instance.filter == "vxlan"
    assert instance.admin_state == "disabled"
    assert instance.oper_state == "stopped"
    assert instance.enabled is False
    assert instance.started is False


def test_controller_features_00050(monkeypatch, controller_features) -> None:
    """
    Classes and Methods
    - ControllerFeatures()
        - __init__()
        - refresh()

    Summary
    - Verify refresh() failure behavior:
        -   RETURN_CODE is 500.

    Code Flow - Setup
    -   ControllerFeatures() is instantiated
    -   dcnm_send() is patched to return the mocked controller response
    -   ControllerFeatures().RestSend() is instantiated
    -   ControllerFeatures().refresh() is called
    -   responses_ControllerFeatures contains a dict with:
        - RETURN_CODE == 500

    Code Flow - Test
    -   ControllerFeatures().refresh() is called

    Expected Result
    -   ``ControllerResponseError`` is raised
    -   Exception message matches expected
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_controller_features(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = controller_features
        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True
        instance.rest_send.timeout = 1

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    match = r"ControllerFeatures\.refresh: Bad controller response:"
    with pytest.raises(ControllerResponseError, match=match):
        instance.refresh()


def test_controller_features_00060(monkeypatch, controller_features) -> None:
    """
    Classes and Methods
    - ControllerFeatures()
        - __init__()
        - refresh()

    Summary
    - Verify refresh() failure due to unexpected controller response structure.:
        -   RETURN_CODE is 200.
        -   DATA is missing.

    Code Flow - Setup
    -   ControllerFeatures() is instantiated
    -   dcnm_send() is patched to return the mocked controller response
    -   ControllerFeatures().RestSend() is instantiated
    -   ControllerFeatures().refresh() is called
    -   responses_ControllerFeatures contains a dict with:
        - RETURN_CODE == 200
        - DATA is missing

    Code Flow - Test
    -   ControllerFeatures().refresh() is called

    Expected Result
    -   ``ControllerResponseError`` is raised
    -   Exception message matches expected
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_controller_features(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = controller_features
        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True
        instance.rest_send.timeout = 1

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    match = r"ControllerFeatures\.refresh: "
    match += r"Controller response does not match expected structure:"
    with pytest.raises(ControllerResponseError, match=match):
        instance.refresh()


MATCH_00070 = r"ControllerFeatures\.rest_send: "
MATCH_00070 += r"value must be an instance of RestSend\..*"


@pytest.mark.parametrize(
    "value, does_raise, expected",
    [
        (RestSend(MockAnsibleModule()), False, does_not_raise()),
        (ControllerFeatures(params), True, pytest.raises(TypeError, match=MATCH_00070)),
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
