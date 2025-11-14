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
# pylint: disable=unused-argument
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
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    ResponseGenerator

from .utils import (MockAnsibleModule, does_not_raise,
                    issu_details_by_device_name_fixture, params,
                    responses_ep_issu)


def test_switch_issu_details_by_device_name_00000(
    issu_details_by_device_name,
) -> None:
    """
    ### Classes and Methods
    -   ``SwitchIssuDetailsByDeviceName``
            - ``__init__``

    ### Summary
    Verify class initialization.

    ### Test
    -   Class properties initialized to expected values.
    -   ``action_keys`` is a set.
    -   ``action_keys`` contains expected values.
    -   Exception is not raised.
    """
    with does_not_raise():
        instance = issu_details_by_device_name

    action_keys = {"imageStaged", "upgrade", "validated"}

    assert isinstance(instance._action_keys, set)
    assert instance._action_keys == action_keys
    assert instance.data == {}
    assert instance.rest_send is None
    assert instance.results is None

    assert instance.ep_issu.class_name == "EpIssu"
    assert instance.conversion.class_name == "ConversionUtils"


def test_switch_issu_details_by_device_name_00100(issu_details_by_device_name) -> None:
    """
    ### Classes and Methods
    -   ``SwitchIssuDetailsBySerialNumber``
            - ``refresh``

    ### Test
    - instance.results.response is a list
    - instance.results.response_current is a dict
    - instance.results.result is a list
    - instance.results.result_current is a dict
    - instance.results.response_data is a list
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_issu(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = issu_details_by_device_name
        instance.results = Results()
        instance.rest_send = rest_send
        instance.refresh()

    assert isinstance(instance.results.response, list)
    assert isinstance(instance.results.response_current, dict)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.result_current, dict)
    assert isinstance(instance.results.response_data, list)


def test_switch_issu_details_by_device_name_00110(issu_details_by_device_name) -> None:
    """
    ### Classes and Methods
    -   ``SwitchIssuDetailsByDeviceName``
            - ``refresh``

    ### Test
    - Properties are set based on device_name
    - Expected property values are returned
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_issu(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = issu_details_by_device_name
        instance.results = Results()
        instance.rest_send = rest_send
        instance.refresh()
        instance.filter = "leaf1"

    assert instance.device_name == "leaf1"
    assert instance.serial_number == "FDO21120U5D"
    # change device_name to a different switch, expect different information
    instance.filter = "cvd-2313-leaf"
    assert instance.device_name == "cvd-2313-leaf"
    assert instance.serial_number == "FDO2112189M"
    # verify remaining properties using current device_name
    assert instance.eth_switch_id == 39890
    assert instance.fabric == "hard"
    assert instance.fcoe_enabled is False
    assert instance.group == "hard"
    # NOTE: For "id" see switch_id below
    assert instance.image_staged == "Success"
    assert instance.image_staged_percent == 100
    assert instance.ip_address == "172.22.150.108"
    assert instance.issu_allowed is None
    assert instance.last_upg_action == "2023-Oct-06 03:43"
    assert instance.mds is False
    assert instance.mode == "Normal"
    assert instance.model == "N9K-C93180YC-EX"
    assert instance.model_type == 0
    assert instance.peer is None
    assert instance.platform == "N9K"
    assert instance.policy == "KR5M"
    assert instance.reason == "Upgrade"
    assert instance.role == "leaf"
    assert instance.status == "In-Sync"
    assert instance.status_percent == 100
    # NOTE: switch_id appears in the response data as "id"
    # NOTE: "id" is a python reserved keyword, so we changed the property name
    assert instance.switch_id == 2
    assert instance.sys_name == "cvd-2313-leaf"
    assert instance.system_mode == "Normal"
    assert instance.upg_groups is None
    assert instance.upgrade == "Success"
    assert instance.upgrade_percent == 100
    assert instance.validated == "Success"
    assert instance.validated_percent == 100
    assert instance.version == "10.2(5)"
    # NOTE: Two vdc_id values exist in the response data for each switch.
    # NOTE: Namely, "vdcId" and "vdc_id"
    # NOTE: Properties are provided for both, as follows.
    # NOTE: vdc_id == vdcId
    # NOTE: vdc_id2 == vdc_id
    assert instance.vdc_id == 0
    assert instance.vdc_id2 == -1
    assert instance.vpc_peer is None
    # NOTE: Two vpc role keys exist in the response data for each switch.
    # NOTE: Namely, "vpcRole" and "vpc_role"
    # NOTE: Properties are provided for both, as follows.
    # NOTE: vpc_role == vpcRole
    # NOTE: vpc_role2 == vpc_role
    # NOTE: Values are synthesized in the response for this test
    assert instance.vpc_role == "FOO"
    assert instance.vpc_role2 == "BAR"
    assert isinstance(instance.filtered_data, dict)
    assert instance.filtered_data.get("deviceName") == "cvd-2313-leaf"


def test_switch_issu_details_by_device_name_00120(issu_details_by_device_name) -> None:
    """
    ### Classes and Methods
    -   ``SwitchIssuDetailsByDeviceName``
            - ``refresh``

    ### Test
    -   ``results.result_current`` is a dict.
    -   ``results.result_current`` contains expected key/values
        for 200 RESULT_CODE.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_issu(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = issu_details_by_device_name
        instance.results = Results()
        instance.rest_send = rest_send
        instance.refresh()
    assert isinstance(instance.results.result_current, dict)
    assert instance.results.result_current.get("found") is True
    assert instance.results.result_current.get("success") is True


def test_switch_issu_details_by_device_name_00130(issu_details_by_device_name) -> None:
    """
    ### Classes and Methods
    -   ``SwitchIssuDetailsByDeviceName``
            - ``refresh``

    ### Summary
    Verify behavior when controller response is 404.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_issu(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = issu_details_by_device_name
        instance.results = Results()
        instance.rest_send = rest_send

    match = r"SwitchIssuDetailsByDeviceName\.refresh_super:\s+"
    match += r"Bad result when retriving switch ISSU details from the\s+"
    match += r"controller\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_switch_issu_details_by_device_name_00140(issu_details_by_device_name) -> None:
    """
    ### Classes and Methods
    -   ``SwitchIssuDetailsByDeviceName``
            - ``refresh``

    ### Test
    -   ``ValueError`` is raised on 200 response with empty DATA key.
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_issu(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = issu_details_by_device_name
        instance.results = Results()
        instance.rest_send = rest_send

    match = r"SwitchIssuDetailsByDeviceName\.refresh_super:\s+"
    match += r"The controller has no switch ISSU information\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_switch_issu_details_by_device_name_00150(issu_details_by_device_name) -> None:
    """
    ### Classes and Methods
    -   ``SwitchIssuDetailsByDeviceName``
            - ``refresh``

    ### Test
    -   ``ValueError`` is raised on 200 response with
        DATA.lastOperDataObject length 0.
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_issu(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = issu_details_by_device_name
        instance.results = Results()
        instance.rest_send = rest_send

    match = r"SwitchIssuDetailsByDeviceName\.refresh_super:\s+"
    match += r"The controller has no switch ISSU information\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_switch_issu_details_by_device_name_00200(issu_details_by_device_name) -> None:
    """
    ### Classes and Methods
    -   ``SwitchIssuDetailsByDeviceName``
            - ``_get``

    ### Summary
    Verify that _get() raises ``ValueError`` because filter is set to an
    unknown device_name

    ### Test
    -   ``ValueError`` is raised because filter is set to an unknown
        device_name.
    -   Error message matches expectation.

    ### Description
    ``SwitchIssuDetailsByDeviceName._get`` is called by all getter
    properties. It raises ``ValueError`` in the following cases:

    -   If the user has not set filter.
    -   If filter is unknown.
    -   If an unknown property name is queried.

    It returns the value of the requested property if ``filter`` is set
    to a serial_number that exists on the controller.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_issu(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = issu_details_by_device_name
        instance.results = Results()
        instance.rest_send = rest_send
        instance.refresh()
        instance.filter = "FOO"

    match = r"SwitchIssuDetailsByDeviceName\._get:\s+"
    match += r"FOO does not exist on the controller\."
    with pytest.raises(ValueError, match=match):
        instance._get("serialNumber")


def test_switch_issu_details_by_device_name_00210(
        issu_details_by_device_name
) -> None:
    """
    ### Classes and Methods
    -   ``SwitchIssuDetailsByDeviceName``
            - ``_get``

    ### Summary
    Verify that ``_get()`` raises ``ValueError`` because an unknown property
    is queried.

    ### Test
    -   ``ValueError`` is raised on access of unknown property name.
    -   Error message matches expectation.

    ### Description
    See test_switch_issu_details_by_device_name_00200.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_issu(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = issu_details_by_device_name
        instance.results = Results()
        instance.rest_send = rest_send
        instance.refresh()
        instance.filter = "leaf1"

    match = r"SwitchIssuDetailsByDeviceName\._get:\s+"
    match += r"leaf1 unknown property name: FOO\."

    with pytest.raises(ValueError, match=match):
        instance._get("FOO")


def test_switch_issu_details_by_device_name_00220(
    issu_details_by_device_name,
) -> None:
    """
    ### Classes and Methods
    -   ``SwitchIssuDetailsByDeviceName``
            - ``_get``

    ### Test
    -   ``_get()`` raises ``ValueError`` because ``filter`` is not set.
    -   Error message matches expectation.
    """
    with does_not_raise():
        instance = issu_details_by_device_name
    match = r"SwitchIssuDetailsByDeviceName\._get: "
    match += r"set instance\.filter to a switch deviceName "
    match += r"before accessing property role\."
    with pytest.raises(ValueError, match=match):
        instance.role  # pylint: disable=pointless-statement
