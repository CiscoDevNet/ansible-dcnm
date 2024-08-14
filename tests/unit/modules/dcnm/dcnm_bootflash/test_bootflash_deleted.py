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
import json

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
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_bootflash import \
    Deleted
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_bootflash.utils import (
    MockAnsibleModule, configs_deleted, does_not_raise, params_deleted,
    responses_ep_all_switches, responses_ep_bootflash_discovery,
    responses_ep_bootflash_files, responses_ep_bootflash_info)


def test_bootflash_deleted_00000() -> None:
    """
    ### Classes and Methods
    - Deleted()
        - __init__()

    ### Summary
    __init__() happy path with minimal config.
    - Verify class attributes are initialized to expected values.

    ### Test
    -   Class attributes are initialized to expected values.
    -   Exceptions are not not raised.
    """
    with does_not_raise():
        instance = Deleted(params_deleted)
    # attributes inherited from Common
    assert instance.bootflash_info.class_name == "BootflashInfo"
    assert instance.params == params_deleted
    assert instance.check_mode is False
    assert instance.config == params_deleted.get("config")
    assert instance.convert_target_to_params.class_name == "ConvertTargetToParams"
    assert instance._rest_send is None
    assert instance.results.class_name == "Results"
    assert instance.results.check_mode is False
    assert instance.results.state == "deleted"
    assert instance.state == "deleted"
    assert instance.switches == [{"ip_address": "192.168.1.2"}]
    assert instance.targets == params_deleted.get("config", {}).get("targets", [])
    assert instance.want == []
    assert instance._valid_states == ["deleted", "query"]
    # attributes specific to Deleted
    assert instance.bootflash_files.class_name == "BootflashFiles"
    assert instance.files_to_delete == {}


def test_bootflash_deleted_00010() -> None:
    """
    ### Classes and Methods
    - Deleted()
        - __init__()

    ### Summary
    ``__init__()`` sad path.  ``Common().__init__()`` raises exception.

    ### Test
    -   ``Deleted().__init__()`` catches exception and
        re-raises as ``ValueError``.
    -   Exception message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    params = copy.deepcopy(params_deleted)
    params["config"] = configs_deleted(key)

    match = r"Deleted\.__init__:\s+"
    match += r"Error during super\(\)\.__init__\(\)\.\s+"
    match += r"Error detail: Deleted\.__init__:\s+"
    match += r"Expected list of dict for params\.config\.targets\. Got str\."
    with pytest.raises(ValueError, match=match):
        instance = Deleted(params)


def test_bootflash_deleted_01000() -> None:
    """
    ### Classes and Methods
    - Deleted()
        - commit()

    ### Summary
    -   ``Deleted().commit()`` happy path.
    -   config.targets contains one entry.
    -   config.switches contains two entries.

    ### Test
    -   No exceptions are raised.
    -   asserts are successful.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    params = copy.deepcopy(params_deleted)
    params["config"] = configs_deleted(f"{key}a")

    def responses():
        yield responses_ep_all_switches(f"{key}a")
        yield responses_ep_bootflash_discovery(f"{key}a")
        yield responses_ep_bootflash_info(f"{key}a")
        yield responses_ep_bootflash_discovery(f"{key}b")
        yield responses_ep_bootflash_info(f"{key}b")
        yield responses_ep_all_switches(f"{key}a")
        yield responses_ep_bootflash_files(f"{key}a")

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
        instance = Deleted(params)
        instance.rest_send = rest_send
        instance.commit()

    assert "File(s) Deleted Successfully." in instance.results.response[0]["DATA"]
    assert (
        instance.results.diff[0]["172.22.150.112"][0]["filepath"]
        == "bootflash:/air.txt"
    )
    assert (
        instance.results.diff[0]["172.22.150.113"][0]["filepath"]
        == "bootflash:/black.txt"
    )
    assert instance.results.response[0]["MESSAGE"] == "OK"
    assert instance.results.response[0]["RETURN_CODE"] == 200
    assert instance.results.result[0]["success"] is True
    assert instance.results.result[0]["changed"] is True
