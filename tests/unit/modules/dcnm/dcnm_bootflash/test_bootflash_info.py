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
# pylint: disable=unused-import, protected-access, use-implicit-booleaness-not-comparison

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import copy
import inspect
import json

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.bootflash.bootflash_info import \
    BootflashInfo
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
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_bootflash.utils import (
    MockAnsibleModule, configs_deleted, configs_query, does_not_raise,
    params_deleted, params_query, responses_ep_all_switches,
    responses_ep_bootflash_discovery, responses_ep_bootflash_info)


def test_bootflash_info_00000() -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - __init__()

    ### Summary
    - Verify class attributes are initialized to expected values.

    ### Test
    -   Class attributes are initialized to expected values.
    -   Exceptions are not not raised.
    """
    with does_not_raise():
        instance = BootflashInfo()
    assert instance.action == "bootflash_info"
    assert instance.class_name == "BootflashInfo"
    assert instance.conversion.class_name == "ConversionUtils"
    assert instance.convert_file_info_to_target.class_name == "ConvertFileInfoToTarget"
    assert instance.ep_bootflash_discovery.class_name == "EpBootflashDiscovery"
    assert instance.ep_bootflash_info.class_name == "EpBootflashInfo"
    assert instance.partitions == []
    assert instance.info_dict == {}
    assert instance._matches == []

    assert instance.diff_dict == {}
    assert instance.response_dict == {}
    assert instance.result_dict == {}

    assert instance._rest_send is None
    assert instance._results is None
    assert instance.switch_details is None
    assert instance.switches is None

    assert instance.filter_filepath is None
    assert instance.filter_supervisor is None
    assert instance.filter_switch is None

    assert instance.valid_supervisor == ["active", "standby"]


def test_bootflash_info_00100() -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - refresh()
        - validate_refresh_parameters()

    ### Summary
    - Verify refresh happy path.

    ### Test
    -    Refresh is successful.
    -    Exceptions are not raised.
    -    Filters work as expected.
    -    Responses match expectations.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    def configs():
        yield configs_query(f"{key}a")

    gen_configs = ResponseGenerator(configs())

    def responses():
        yield responses_ep_all_switches(f"{key}a")
        yield responses_ep_bootflash_discovery(f"{key}a")
        yield responses_ep_bootflash_info(f"{key}a")
        yield responses_ep_bootflash_discovery(f"{key}b")
        yield responses_ep_bootflash_info(f"{key}b")

    gen_responses = ResponseGenerator(responses())

    params_test = copy.deepcopy(params_query)
    params_test.update({"config": gen_configs.next})

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params_test)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = BootflashInfo()
        instance.rest_send = rest_send
        instance.results = Results()
        instance.switch_details = SwitchDetails()
        instance.switches = ["172.22.150.112", "172.22.150.113"]
        instance.refresh()
        instance.filter_switch = "172.22.150.112"
        instance.filter_supervisor = "active"
        instance.filter_filepath = "bootflash:/fire.txt"

    assert len(instance.matches) == 1
    assert instance.matches[0]["date"] == "2024-08-08 22:50:37"
    assert instance.matches[0]["filepath"] == "bootflash:/fire.txt"
    assert instance.matches[0]["ip_address"] == "172.22.150.112"
    assert instance.matches[0]["serial_number"] == "FOX2109PGCS"
    assert instance.matches[0]["size"] == "2"

    with does_not_raise():
        instance.filter_switch = "172.22.150.113"
        instance.filter_supervisor = "active"
        instance.filter_filepath = "bootflash:/*.txt"

    assert len(instance.matches) == 4
    assert instance.matches[0]["date"] == "2024-08-08 22:50:28"
    assert instance.matches[1]["date"] == "2024-08-08 22:51:28"
    assert instance.matches[2]["date"] == "2024-08-08 22:52:28"
    assert instance.matches[3]["date"] == "2024-08-08 22:53:28"
    assert instance.matches[0]["filepath"] == "bootflash:/black.txt"
    assert instance.matches[1]["filepath"] == "bootflash:/blue.txt"
    assert instance.matches[2]["filepath"] == "bootflash:/green.txt"
    assert instance.matches[3]["filepath"] == "bootflash:/red.txt"
    assert instance.matches[0]["ip_address"] == "172.22.150.113"
    assert instance.matches[1]["ip_address"] == "172.22.150.113"
    assert instance.matches[2]["ip_address"] == "172.22.150.113"
    assert instance.matches[3]["ip_address"] == "172.22.150.113"
    assert instance.matches[0]["serial_number"] == "FOX2109PGD0"
    assert instance.matches[1]["serial_number"] == "FOX2109PGD0"
    assert instance.matches[2]["serial_number"] == "FOX2109PGD0"
    assert instance.matches[3]["serial_number"] == "FOX2109PGD0"
    assert instance.matches[0]["size"] == "12043"
    assert instance.matches[1]["size"] == "2"
    assert instance.matches[2]["size"] == "2"
    assert instance.matches[3]["size"] == "2"


def test_bootflash_info_00110() -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - refresh()
        - validate_refresh_parameters()

    ### Summary
    - Verify exception is raised if ``rest_send`` is not set.

    ### Test
    -   ValueError is raised when ``rest_send`` is not set.
    """
    with does_not_raise():
        instance = BootflashInfo()
        instance.results = Results()
        instance.switch_details = SwitchDetails()
        instance.switches = ["192.168.1.1"]

    match = r"BootflashInfo\.validate_refresh_parameters: "
    match += r"rest_send must be set prior to calling refresh\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_bootflash_info_00120() -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - refresh()
        - validate_refresh_parameters()

    ### Summary
    - Verify exception is raised if ``results`` is not set.

    ### Test
    -   ValueError is raised when ``results`` is not set.
    """
    with does_not_raise():
        instance = BootflashInfo()
        instance.rest_send = RestSend({})
        instance.switch_details = SwitchDetails()
        instance.switches = ["192.168.1.1"]

    match = r"BootflashInfo\.validate_refresh_parameters: "
    match += r"results must be set prior to calling refresh\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_bootflash_info_00130() -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - refresh()
        - validate_refresh_parameters()

    ### Summary
    - Verify exception is raised if ``switch_details`` is not set.

    ### Test
    -   ValueError is raised when ``switch_details`` is not set.
    """
    with does_not_raise():
        instance = BootflashInfo()
        instance.rest_send = RestSend({})
        instance.results = Results()
        instance.switches = ["192.168.1.1"]

    match = r"BootflashInfo\.validate_refresh_parameters: "
    match += r"switch_details must be set prior to calling refresh\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()
