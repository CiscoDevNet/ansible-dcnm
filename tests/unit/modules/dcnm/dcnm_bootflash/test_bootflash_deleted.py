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
    match += r"Expected list of dict for params\.config\.targets\.\s+"
    match += r"Got list element of type str\."
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


def test_bootflash_deleted_02000() -> None:
    """
    ### Classes and Methods
    - Deleted()
        - populate_files_to_delete()

    ### Summary
    -   ``Deleted().populate_files_to_delete()`` sad path.
    -   BootflashInfo().filter_supervisor raises ValueError.

    ### Test
    -   ValueError is raised.
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    params = copy.deepcopy(params_deleted)
    params["config"] = configs_deleted(f"{key}a")

    switch = {
        "ip_address": params["config"]["switches"][0]["ip_address"],
        "targets": params["config"]["targets"],
    }
    with does_not_raise():
        instance = Deleted(params)
    match = r"Deleted\.populate_files_to_delete:\s+"
    match += r"Error assigning BootflashInfo\.filter_supervisor\.\s+"
    match += r"Error detail:\s+"
    match += r"BootflashInfo\.filter_supervisor.setter:\s+"
    match += r"value foo is not a valid value for supervisor\.\s+"
    match += r"Valid values: active,standby\."
    with pytest.raises(ValueError, match=match):
        instance.populate_files_to_delete(switch)


@pytest.mark.parametrize("missing_param", ["filepath", "supervisor"])
def test_bootflash_deleted_03000(missing_param) -> None:
    """
    ### Classes and Methods
    - Deleted()
        - update_bootflash_files()

    ### Summary
    -   ``Deleted().update_bootflash_files()`` sad path.
    -   ConvertTargetToParams().parse_target raises ValueError
        because target is missing a mandatory key.

    ### Setup
    -   target is manually constructed and target.pop() is used
        to remove mandatory keys.

    ### Test
    -   ValueError is raised.
    -   Error message matches expectation.

    ### Notes
    1.  We test ip_address parameter in test_bootflash_deleted_03100, since
        that raises a different error.
    """
    target = {
        "filepath": "bootflash:/foo.txt",
        "ip_address": "192.168.1.1",
        "supervisor": "active",
    }
    with does_not_raise():
        instance = Deleted(params_deleted)

    target.pop(missing_param)
    match = r"Deleted\.update_bootflash_files:\s+"
    match += r"Error converting target to params\.\s+"
    match += r"Error detail:\s+"
    match += r"ConvertTargetToParams\.parse_target:\s+"
    match += rf"Expected {missing_param} in target dict\. Got.*\."
    with pytest.raises(ValueError, match=match):
        instance.update_bootflash_files("192.168.1.1", target)


def test_bootflash_deleted_03100() -> None:
    """
    ### Classes and Methods
    - Deleted()
        - update_bootflash_files()

    ### Summary
    -   ``Deleted().update_bootflash_files()`` sad path.
    -   ConvertTargetToParams().parse_target raises ValueError
        because target is missing a mandatory key.

    ### Setup
    -   target is manually constructed without ip_address key.

    ### Test
    -   ValueError is raised.
    -   Error message matches expectation.
    """
    target = {"filepath": "bootflash:/foo.txt", "supervisor": "active"}
    with does_not_raise():
        instance = Deleted(params_deleted)

    match = r"Deleted\.update_bootflash_files:\s+"
    match += r"Error assigning BootflashFiles properties\.\s+"
    match += r"Error detail:\s+"
    match += r"BootflashFiles\.target:\s+"
    match += r"ip_address key missing from value .*\."
    with pytest.raises(ValueError, match=match):
        instance.update_bootflash_files("192.168.1.1", target)


def test_bootflash_deleted_03200() -> None:
    """
    ### Classes and Methods
    - Deleted()
        - update_bootflash_files()

    ### Summary
    -   ``Deleted().update_bootflash_files()`` sad path.
    -   BootflashFiles().add_file() raises ValueError
        because target switch mode is "Migration".

    ### Setup
    -   A valid ``target`` is manually constructed.
    -   ``responses_ep_all_switches`` returns a switch in "Migration" mode.

    ### Test
    -   update_bootflash_files() re-raises ``ValueError``
        raised by ``BootflashFiles().add_file()``.
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    params = copy.deepcopy(params_deleted)
    params["config"] = configs_deleted(f"{key}a")

    def responses():
        yield responses_ep_all_switches(f"{key}a")

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    target = {
        "filepath": "bootflash:/foo.txt",
        "ip_address": "172.22.150.112",
        "serial_number": "FOX2109PGCS",
        "supervisor": "active",
    }

    with does_not_raise():
        instance = Deleted(params)
        instance.rest_send = rest_send
        instance.bootflash_files.switch_details = SwitchDetails()
        instance.bootflash_files.rest_send = rest_send
        instance.bootflash_files.switch_details.results = Results()
    match = r"Deleted\.update_bootflash_files:\s+"
    match += r"Error adding file to bootflash_files\.\s+"
    match += r"Error detail:\s+"
    match += r"BootflashFiles\.add_file:\s+"
    match += r"Cannot delete files on switch 172\.22\.150\.112\.\s+"
    match += r"Reason: switch mode is migration."

    with pytest.raises(ValueError, match=match):
        instance.update_bootflash_files("172.22.150.112", target)


def test_bootflash_deleted_03210() -> None:
    """
    ### Classes and Methods
    - Deleted()
        - update_bootflash_files()

    ### Summary
    -   ``Deleted().update_bootflash_files()`` sad path.
    -   BootflashFiles().add_file() raises ValueError
        because target switch mode is "Inconsistent".

    ### Setup
    -   A valid ``target`` is manually constructed.
    -   ``responses_ep_all_switches`` returns a switch in "Inconsistent" mode.

    ### Test
    -   update_bootflash_files() re-raises ``ValueError``
        raised by ``BootflashFiles().add_file()``.
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    params = copy.deepcopy(params_deleted)
    params["config"] = configs_deleted(f"{key}a")

    def responses():
        yield responses_ep_all_switches(f"{key}a")

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    target = {
        "filepath": "bootflash:/foo.txt",
        "ip_address": "172.22.150.112",
        "serial_number": "FOX2109PGCS",
        "supervisor": "active",
    }

    with does_not_raise():
        instance = Deleted(params)
        instance.rest_send = rest_send
        instance.bootflash_files.switch_details = SwitchDetails()
        instance.bootflash_files.rest_send = rest_send
        instance.bootflash_files.switch_details.results = Results()
    match = r"Deleted\.update_bootflash_files:\s+"
    match += r"Error adding file to bootflash_files\.\s+"
    match += r"Error detail:\s+"
    match += r"BootflashFiles\.add_file:\s+"
    match += r"Cannot delete files on switch 172\.22\.150\.112\.\s+"
    match += r"Reason: switch mode is inconsistent."

    with pytest.raises(ValueError, match=match):
        instance.update_bootflash_files("172.22.150.112", target)
