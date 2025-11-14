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
    MockAnsibleModule, configs_query, does_not_raise, params_query,
    responses_ep_all_switches, responses_ep_bootflash_discovery,
    responses_ep_bootflash_info)


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

    params = copy.deepcopy(params_query)
    params.update({"config": gen_configs.next})

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
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
    assert instance.matches[0]["filepath"] == "bootflash:/fire.txt"
    assert instance.matches[0]["ip_address"] == "172.22.150.112"

    with does_not_raise():
        instance.filter_switch = "172.22.150.113"
        instance.filter_supervisor = "active"
        instance.filter_filepath = "bootflash:/*.txt"

    assert len(instance.matches) == 4
    assert instance.matches[0]["date"] == "2024-08-08 22:50:28"
    assert instance.matches[1]["filepath"] == "bootflash:/blue.txt"
    assert instance.matches[2]["ip_address"] == "172.22.150.113"
    assert instance.matches[3]["serial_number"] == "FOX2109PGD0"
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


def test_bootflash_info_00140() -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - refresh()
        - validate_refresh_parameters()

    ### Summary
    - Verify exception is raised if ``switches`` is not set.

    ### Test
    -   ValueError is raised when ``switches`` is not set.
    """
    with does_not_raise():
        instance = BootflashInfo()
        instance.rest_send = RestSend({})
        instance.results = Results()
        instance.switch_details = SwitchDetails()

    match = r"BootflashInfo\.validate_refresh_parameters: "
    match += r"switches must be set prior to calling refresh\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_bootflash_info_00150() -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - refresh()
        - validate_refresh_parameters()

    ### Summary
    -   Verify ``ValueError`` is raised because 172.22.150.112 is missing
        serialNumber key in the ep_all_switches response.

    ### Test
    -    ``ValueError`` is raised.
    -    Error message matches expectations.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    def configs():
        yield configs_query(f"{key}a")

    gen_configs = ResponseGenerator(configs())

    def responses():
        yield responses_ep_all_switches(f"{key}a")

    gen_responses = ResponseGenerator(responses())

    params = copy.deepcopy(params_query)
    params.update({"config": gen_configs.next})

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
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
    match = r"BootflashInfo\.refresh_bootflash_info:\s+"
    match += r"serial_number not found for switch 172.22.150.112.\s+"
    match += r"Error detail SwitchDetails\._get:\s+"
    match += r"172.22.150.112 does not have a key named serialNumber\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_bootflash_info_00200() -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - build_matches()
        - validate_prerequisites_for_build_matches()

    ### Summary
    -   Verify exception is raised if ``build_matches()`` is called
        before ``refresh()``.

    ### Test
    -   ``ValueError`` is raised when ``build_matches()`` called.
    -    Error message matches expectations.
    """
    with does_not_raise():
        instance = BootflashInfo()
        instance.rest_send = RestSend({})
        instance.results = Results()
        instance.switch_details = SwitchDetails()
        instance.switches = ["172.22.150.112", "172.22.150.113"]

    match = r"BootflashInfo\.validate_prerequisites_for_build_matches:\s+"
    match += r"refresh must be called before retrieving bootflash properties\."
    with pytest.raises(ValueError, match=match):
        instance.build_matches()


def test_bootflash_info_00210() -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - refresh()
        - validate_refresh_parameters()
        - build_matches()

    ### Summary
    Verify that ``build_matches()`` returns without updating the
    ``instance.matches`` list when ``filter_switch`` is not found in the
    controller response (i.e. instance.info_dict) retrieved with
    instance.info property.

    ### Test
    -    Refresh is successful.
    -    Exceptions are not raised.
    -    ``instance.matches`` list is empty.
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

    gen_responses = ResponseGenerator(responses())

    params = copy.deepcopy(params_query)
    params.update({"config": gen_configs.next})

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = BootflashInfo()
        instance.rest_send = rest_send
        instance.results = Results()
        instance.switch_details = SwitchDetails()
        instance.switches = ["172.22.150.112"]
        instance.refresh()
        instance.filter_switch = "172.22.150.113"
        instance.filter_supervisor = "active"
        instance.filter_filepath = "bootflash:/air.txt"
    assert instance.matches == []


def test_bootflash_info_00220() -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - refresh()
        - validate_refresh_parameters()
        - build_matches()

    ### Summary
    Verify that when ``filter_supervisor`` is set, but does not match any
    items in the info_dict, ``build_matches()`` does not update the
    matches list.

    ### Test
    -    Refresh is successful.
    -    Exceptions are not raised.
    -    ``instance.matches`` list is empty.
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

    params = copy.deepcopy(params_query)
    params.update({"config": gen_configs.next})

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
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
    with does_not_raise():
        instance.filter_switch = "172.22.150.112"
        instance.filter_supervisor = "standby"
        instance.filter_filepath = "bootflash:/*.txt"
    assert len(instance.matches) == 0
    with does_not_raise():
        instance.filter_switch = "172.22.150.113"
        instance.filter_supervisor = "standby"
        instance.filter_filepath = "bootflash:/*.txt"
    assert len(instance.matches) == 0


def test_bootflash_info_00230() -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - refresh()
        - validate_refresh_parameters()
        - build_matches()

    ### Summary
    Verify that ``ValueError`` is raised by ``ConvertFileInfoToTarget()`` if an
    ``EpBootflashInfo`` response is missing the ``ipAddr`` key.

    ### Test
    -   Refresh is successful.
    -   ``ValueError`` is raised by ``ConvertFileInfoToTarget()`` because
        the response from ``EpBootflashInfo`` is missing the ``ipAddr`` key.
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

    gen_responses = ResponseGenerator(responses())

    params = copy.deepcopy(params_query)
    params.update({"config": gen_configs.next})

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = BootflashInfo()
        instance.rest_send = rest_send
        instance.results = Results()
        instance.switch_details = SwitchDetails()
        instance.switches = ["172.22.150.112"]
        instance.refresh()
    with does_not_raise():
        instance.filter_switch = "172.22.150.112"
        instance.filter_supervisor = "active"
        instance.filter_filepath = "bootflash:/*.txt"

    match = r"ConvertFileInfoToTarget\.commit:\s+.*"
    match += r"Error detail: ConvertFileInfoToTarget\._get:\s+"
    match += r"Missing key ipAddr in file_info:.*\."
    with pytest.raises(ValueError, match=match):
        instance.matches  # pylint: disable=pointless-statement


@pytest.mark.parametrize(
    "filter_filepath,filepath,expected",
    [
        (None, "bootflash:/black.txt", False),
        ("bootflash:/black.txt", "bootflash:/black.txt", True),
        ("bootflash:/black.txt", "bootflash:/blue.txt", False),
        ("bootflash:/*.txt", "bootflash:/black.txt", True),
        ("bootflash:/*.txt", "bootflash:/blue.txt", True),
        ("*:/*.txt", "usb1:/green.txt", True),
        ("usb1:/*.txt", "bootflash:/red.txt", False),
        ("bootflash:/*", "bootflash:/foo", True),
        ("bootflash:/???.txt", "bootflash:/foo.txt", True),
        ("bootflash:/???.txt", "bootflash:/foobar.txt", False),
        ("bootflash:/???1.*", "bootflash:/foo1.txt", True),
        ("*:/*", "blahdevice:/blahfile.bing.bang.bong", True),
        ("*:/*", "/b", False),
    ],
)
def test_bootflash_info_00300(filter_filepath, filepath, expected) -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - match_filter_filepath()
        - filter_filepath.setter
        - filepath.setter

    ### Summary
    Verify that ``match_filter_filepath()`` returns appropriate value
    (True or False) for various inputs.

    ### Test
    -   Exception is not raised.
    -   True is returned when ``filter_filepath`` matches ``filepath``.
    -   False is returned when ``filter_filepath`` does not
        match ``filepath``.
    """
    with does_not_raise():
        instance = BootflashInfo()
        instance.rest_send = RestSend({})
        instance.results = Results()
        instance.switch_details = SwitchDetails()
        instance.switches = ["172.22.150.112"]
        if filter_filepath is not None:
            instance.filter_filepath = filter_filepath

    target = {"filepath": filepath, "ip_address": "192.168.1.1", "supervisor": "active"}
    assert instance.match_filter_filepath(target) == expected


@pytest.mark.parametrize(
    "filter_supervisor,supervisor,expected",
    [
        (None, "active", False),
        ("active", "active", True),
        ("active", "standby", False),
        ("standby", "standby", True),
        ("standby", "active", False),
    ],
)
def test_bootflash_info_00310(filter_supervisor, supervisor, expected) -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - match_filter_supervisor()
        - filter_supervisor.setter
        - supervisor.setter

    ### Summary
    Verify that ``match_filter_supervisor()`` returns appropriate value
    (True or False) for various inputs.

    ### Test
    -   Exception is not raised.
    -   True is returned when ``filter_supervisor`` matches ``supervisor``.
    -   False is returned when ``filter_supervisor`` does not
        match ``supervisor``.
    """
    with does_not_raise():
        instance = BootflashInfo()
        instance.rest_send = RestSend({})
        instance.results = Results()
        instance.switch_details = SwitchDetails()
        instance.switches = ["172.22.150.112"]
        if filter_supervisor is not None:
            instance.filter_supervisor = filter_supervisor

    target = {
        "filepath": "bootflash:/foo.txt",
        "ip_address": "192.168.1.1",
        "supervisor": supervisor,
    }
    assert instance.match_filter_supervisor(target) == expected


@pytest.mark.parametrize(
    "filter_switch,switch,expected",
    [
        (None, "192.168.1.1", False),
        ("192.168.1.1", "192.168.1.1", True),
        ("192.168.1.1", "192.168.1.2", False),
        ("192.168.1.1", "foo", False),
        (["standby"], "192.168.1.2", False),
    ],
)
def test_bootflash_info_00320(filter_switch, switch, expected) -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - match_filter_switch()
        - filter_switch.setter

    ### Summary
    Verify that ``match_filter_switch()`` returns appropriate value
    (True or False) for various inputs.

    ### Test
    -   Exception is not raised.
    -   True is returned when ``filter_supervisor`` matches ``supervisor``.
    -   False is returned when ``filter_supervisor`` does not
        match ``supervisor``.
    """
    with does_not_raise():
        instance = BootflashInfo()
        instance.rest_send = RestSend({})
        instance.results = Results()
        instance.switch_details = SwitchDetails()
        instance.switches = ["172.22.150.112"]
        if filter_switch is not None:
            instance.filter_switch = filter_switch

    target = {
        "filepath": "bootflash:/foo.txt",
        "ip_address": switch,
        "supervisor": "active",
    }
    assert instance.match_filter_switch(target) == expected


def test_bootflash_info_00400() -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - filter_supervisor.setter

    ### Summary
    Verify that ``filter_supervisor.setter`` raises ``ValueError``
    if the value is not in ``valid_supervisor``.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectations.
    """
    with does_not_raise():
        instance = BootflashInfo()
        instance.rest_send = RestSend({})
        instance.results = Results()
        instance.switch_details = SwitchDetails()
        instance.switches = ["172.22.150.112"]
    match = r"BootflashInfo\.filter_supervisor\.setter:\s+"
    match += r"value foo is not a valid value for supervisor\.\s+"
    match += r"Valid values: active,standby\."
    with pytest.raises(ValueError, match=match):
        instance.filter_supervisor = "foo"


def test_bootflash_info_00500() -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - switch_details.setter

    ### Summary
    Verify that ``switch_details.setter`` raises ``TypeError``
    if the value is not an instance if ``SwitchDetails()``
    and the value is not a class instance.

    ### Test
    -   ``TypeError`` is raised.
    -   Error message matches expectations.
    """
    with does_not_raise():
        instance = BootflashInfo()
        instance.rest_send = RestSend({})
        instance.results = Results()
        instance.switches = ["172.22.150.112"]
    match = r"BootflashInfo.switch_details:\s+"
    match += r"value must be an instance of SwitchDetails\.\s+"
    match += r"Got value foo of type str\.\s+"
    match += r"Error detail: 'str' object has no attribute 'class_name'\."
    with pytest.raises(TypeError, match=match):
        instance.switch_details = "foo"


def test_bootflash_info_00510() -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - switch_details.setter

    ### Summary
    Verify that ``switch_details.setter`` raises ``TypeError``
    if the value is not an instance if ``SwitchDetails()``
    and the value is a class instance with ``class_name``
    attribute.

    ### Test
    -   ``TypeError`` is raised.
    -   Error message matches expectations.
    """
    with does_not_raise():
        instance = BootflashInfo()
        instance.rest_send = RestSend({})
        instance.results = Results()
        instance.switches = ["172.22.150.112"]
    match = r"BootflashInfo.switch_details:\s+"
    match += r"value must be an instance of SwitchDetails\.\s+"
    match += r"Got value .* of type Results\."
    with pytest.raises(TypeError, match=match):
        instance.switch_details = Results()


def test_bootflash_info_00600() -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - switches.setter

    ### Summary
    Verify that ``switches.setter`` raises ``TypeError``
    if the value is not a list

    ### Test
    -   ``TypeError`` is raised.
    -   Error message matches expectations.
    """
    with does_not_raise():
        instance = BootflashInfo()
        instance.rest_send = RestSend({})
        instance.results = Results()
    match = r"BootflashInfo\.switches:\s+"
    match += r"switches must be a list\. got str for value foo\."
    with pytest.raises(TypeError, match=match):
        instance.switches = "foo"


def test_bootflash_info_00610() -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - switches.setter

    ### Summary
    Verify that ``switches.setter`` raises ``ValueError``
    if the value is an empty list.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectations.
    """
    with does_not_raise():
        instance = BootflashInfo()
        instance.rest_send = RestSend({})
        instance.results = Results()
    match = r"BootflashInfo.switches:\s+"
    match += r"switches must be a list with at least one ip address\.\s+"
    match += r"got \[\]\."
    with pytest.raises(ValueError, match=match):
        instance.switches = []


def test_bootflash_info_00620() -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - switches.setter

    ### Summary
    Verify that ``switches.setter`` raises ``TypeError``
    if the value is a list containing a non-string.

    ### Test
    -   ``TypeError`` is raised.
    -   Error message matches expectations.
    """
    with does_not_raise():
        instance = BootflashInfo()
        instance.rest_send = RestSend({})
        instance.results = Results()
    match = r"BootflashInfo\.switches:\s+"
    match += r"switches must be a list of ip addresses\.\s+"
    match += r"got type int for value 10\."
    with pytest.raises(TypeError, match=match):
        instance.switches = ["192.168.1.1", 10]
