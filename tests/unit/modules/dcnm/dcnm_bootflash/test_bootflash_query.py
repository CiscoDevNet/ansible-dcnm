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
# pylint: disable=unused-import, protected-access, use-implicit-booleaness-not-comparison, unused-variable

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import copy
import inspect

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.response_handler import \
    ResponseHandler
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_file import \
    Sender
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_bootflash import Query
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_bootflash.utils import (
    MockAnsibleModule, configs_query, does_not_raise, params_query,
    responses_ep_all_switches, responses_ep_bootflash_discovery,
    responses_ep_bootflash_info)


def test_bootflash_query_00000() -> None:
    """
    ### Classes and Methods
    - Query()
        - __init__()

    ### Summary
    __init__() happy path with minimal config.
    - Verify class attributes are initialized to expected values.

    ### Test
    -   Class attributes are initialized to expected values.
    -   Exceptions are not not raised.
    """
    with does_not_raise():
        instance = Query(params_query)
    # attributes inherited from Common
    assert instance.bootflash_info.class_name == "BootflashInfo"
    assert instance.params == params_query
    assert instance.check_mode is False
    assert instance.config == params_query.get("config")
    assert instance.convert_target_to_params.class_name == "ConvertTargetToParams"
    assert instance._rest_send is None
    assert instance.results.class_name == "Results"
    assert instance.results.check_mode is False
    assert instance.results.state == "query"
    assert instance.state == "query"
    assert instance.switches == [{"ip_address": "192.168.1.2"}]
    assert instance.targets == params_query.get("config", {}).get("targets", [])
    assert instance.want == []
    assert instance._valid_states == ["deleted", "query"]
    # attributes specific to Query
    assert instance.class_name == "Query"


def test_bootflash_query_00010() -> None:
    """
    ### Classes and Methods
    - Query()
        - __init__()

    ### Summary
    ``__init__()`` sad path.  ``Common().__init__()`` raises exception.

    ### Test
    -   ``Query().__init__()`` catches exception and
        re-raises as ``ValueError``.
    -   Exception message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    params = copy.deepcopy(params_query)
    params["config"] = configs_query(key)

    match = r"Query\.__init__:\s+"
    match += r"Error during super\(\)\.__init__\(\)\.\s+"
    match += r"Error detail: Query\.__init__:\s+"
    match += r"Expected list of dict for params\.config\.targets\.\s+"
    match += r"Got list element of type str\."
    with pytest.raises(ValueError, match=match):
        instance = Query(params)


def test_bootflash_query_01000() -> None:
    """
    ### Classes and Methods
    - Query()
        - commit()

    ### Summary
    -   ``Query().commit()`` happy path.
    -   config.targets contains one entry.
    -   config.switches contains two entries.

    ### Test
    -   No exceptions are raised.
    -   asserts are successful.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    params = copy.deepcopy(params_query)
    params["config"] = configs_query(f"{key}a")

    def responses():
        yield responses_ep_all_switches(f"{key}a")
        yield responses_ep_bootflash_discovery(f"{key}a")
        yield responses_ep_bootflash_info(f"{key}a")
        yield responses_ep_bootflash_discovery(f"{key}b")
        yield responses_ep_bootflash_info(f"{key}b")
        yield responses_ep_all_switches(f"{key}a")
        yield responses_ep_bootflash_info(f"{key}a")

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
        instance = Query(params)
        instance.rest_send = rest_send
        instance.commit()

    assert (
        instance.results.diff[0]["172.22.150.112"][0]["filepath"]
        == "bootflash:/air.txt"
    )
    assert (
        instance.results.diff[0]["172.22.150.113"][0]["filepath"]
        == "bootflash:/black.txt"
    )
    assert instance.results.metadata[0]["action"] == "bootflash_info"
    assert instance.results.metadata[0]["check_mode"] is False
    assert instance.results.metadata[0]["sequence_number"] == 1
    assert instance.results.metadata[0]["state"] == "query"
    assert instance.results.response[0]["172.22.150.112"]["MESSAGE"] == "OK"
    assert instance.results.response[0]["172.22.150.112"]["RETURN_CODE"] == 200
    assert instance.results.response[0]["172.22.150.113"]["MESSAGE"] == "OK"
    assert instance.results.response[0]["172.22.150.113"]["RETURN_CODE"] == 200
    assert instance.results.result[0]["172.22.150.112"]["success"] is True
    assert instance.results.result[0]["172.22.150.112"]["found"] is True
    assert instance.results.result[0]["172.22.150.113"]["success"] is True
    assert instance.results.result[0]["172.22.150.113"]["found"] is True


def test_bootflash_query_01010() -> None:
    """
    ### Classes and Methods
    - Query()
        - commit()

    ### Summary
    -   ``Query().commit()`` happy path with no switches.
    -   config.targets contains one entry.
    -   config.switches contains no entries.

    ### Test
    -   No exceptions are raised.
    -   asserts are successful.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    params = copy.deepcopy(params_query)
    params["config"] = configs_query(f"{key}a")

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Query(params)
        instance.rest_send = rest_send
        instance.commit()

    assert len(instance.results.diff) == 1
    assert instance.results.diff[0]["sequence_number"] == 1
    assert instance.results.metadata[0]["action"] == "bootflash_info"
    assert instance.results.metadata[0]["check_mode"] is False
    assert instance.results.metadata[0]["sequence_number"] == 1
    assert instance.results.metadata[0]["state"] == "query"
    assert instance.results.response[0]["0.0.0.0"]["MESSAGE"] == "OK"
    assert instance.results.response[0]["0.0.0.0"]["DATA"] == "No switches to query."
    assert instance.results.response[0]["0.0.0.0"]["RETURN_CODE"] == 200
    assert instance.results.result[0]["0.0.0.0"]["success"] is True
    assert instance.results.result[0]["0.0.0.0"]["found"] is False
