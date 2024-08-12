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
# pylint: disable=unused-import, protected-access

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import copy
import inspect

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.bootflash.bootflash_files import \
    BootflashFiles
from ansible_collections.cisco.dcnm.plugins.module_utils.bootflash.convert_target_to_params import \
    ConvertTargetToParams
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
    MockAnsibleModule, configs_deleted, does_not_raise, params_deleted,
    payloads_bootflash_files, responses_ep_all_switches,
    responses_ep_bootflash_files, targets)


def test_bootflash_files_00000() -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
        - __init__()

    ### Summary
    - Verify class attributes are initialized to expected values.

    ### Test
    -   Class attributes are initialized to expected values.
    -   Exceptions are not not raised.
    """
    with does_not_raise():
        instance = BootflashFiles()
    assert instance.action == "bootflash_delete"
    assert instance.class_name == "BootflashFiles"
    assert instance.conversion.class_name == "ConversionUtils"
    assert instance.diff == {}  # pylint: disable=use-implicit-booleaness-not-comparison
    assert instance.ep_bootflash_files.class_name == "EpBootflashFiles"
    assert instance.ok_to_delete_files_reason is None
    assert instance.payload == {"deleteFiles": []}
    assert instance.filename is None
    assert instance.filepath is None
    assert instance.filesize is None
    assert instance.ip_address is None
    assert instance.partition is None
    assert instance._rest_send is None
    assert instance._results is None
    assert instance.supervisor is None
    assert instance.switch_details is None
    assert instance.target is None


def test_bootflash_files_00100() -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - commit()
        - validate_commit_parameters()

    ### Summary
    - Verify commit happy path.

    ### Test
    -   Add two files, one for each of two switches, to be deleted.
    -   commit is successful.
    -   Exceptions are not raised.
    -   Responses match expectations.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    def configs():
        yield configs_deleted(f"{key}a")

    gen_configs = ResponseGenerator(configs())

    def yield_targets():
        yield targets(f"{key}a")
        yield targets(f"{key}b")

    gen_targets = ResponseGenerator(yield_targets())

    def responses():
        yield responses_ep_all_switches(f"{key}a")
        yield responses_ep_bootflash_files(f"{key}a")

    gen_responses = ResponseGenerator(responses())

    params = copy.deepcopy(params_deleted)
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
        instance = BootflashFiles()
        instance.rest_send = rest_send
        instance.results = Results()
        instance.switch_details = SwitchDetails()
        instance.switch_details.results = Results()

        convert_target = ConvertTargetToParams()
        convert_target.target = gen_targets.next
        convert_target.commit()

        instance.filepath = convert_target.filepath
        instance.filename = convert_target.filename
        instance.ip_address = "172.22.150.112"
        instance.partition = convert_target.partition
        instance.supervisor = convert_target.supervisor
        instance.target = convert_target.target
        instance.add_file()

        convert_target = ConvertTargetToParams()
        convert_target.target = gen_targets.next
        convert_target.commit()

        instance.filepath = convert_target.filepath
        instance.filename = convert_target.filename
        instance.ip_address = "172.22.150.113"
        instance.partition = convert_target.partition
        instance.supervisor = convert_target.supervisor
        instance.target = convert_target.target
        instance.add_file()

        instance.commit()

    assert instance.payload == payloads_bootflash_files(f"{key}a")
    assert instance.results.response_current["RETURN_CODE"] == 200
    assert instance.results.result == [
        {"success": True, "changed": True, "sequence_number": 1}
    ]


@pytest.mark.parametrize(
    "key_responses_ep_all_switches, reason",
    [
        ("a", "migration"),
        ("b", "inconsistent"),
    ],
)
def test_bootflash_files_00200(key_responses_ep_all_switches, reason) -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - add_file()

    ### Summary
    Verify add_file() raises ValueError if switch mode is either
    "migration" or "inconsistent".

    ### Test
    -   Call add_file() for switch that does not support file deletion
        due to being in migration (key == a) or inconsistent (key == b)
        mode.
    -   ValueError is raised.
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    def configs():
        yield configs_deleted(f"{key}a")

    gen_configs = ResponseGenerator(configs())

    def yield_targets():
        yield targets(f"{key}a")

    gen_targets = ResponseGenerator(yield_targets())

    derived_key = f"{key}{key_responses_ep_all_switches}"

    def responses():
        yield responses_ep_all_switches(derived_key)

    gen_responses = ResponseGenerator(responses())

    params = copy.deepcopy(params_deleted)
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
        instance = BootflashFiles()
        instance.rest_send = rest_send
        instance.results = Results()
        instance.switch_details = SwitchDetails()
        instance.switch_details.results = Results()

        convert_target = ConvertTargetToParams()
        convert_target.target = gen_targets.next
        convert_target.commit()

        instance.filepath = convert_target.filepath
        instance.filename = convert_target.filename
        instance.ip_address = "172.22.150.112"
        instance.partition = convert_target.partition
        instance.supervisor = convert_target.supervisor
        instance.target = convert_target.target

    match = r"BootflashFiles\.add_file:\s+"
    match += r"Cannot delete files on switch 172\.22\.150\.112\.\s+"
    match += rf"Reason: switch mode is {reason}\."
    with pytest.raises(ValueError, match=match):
        instance.add_file()


def test_bootflash_files_00300() -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - refresh_switch_details()

    ### Summary
    Verify ``refresh_switch_details()`` raises ``ValueError`` if
    ``switch_details`` is not set.

    ### Test
    -   Call ``instance.refresh_switch_details()`` without having set
        ``BootflashFiles().switch_details``.
    -   ValueError is raised.
    -   Error message matches expectation.
    """
    with does_not_raise():
        instance = BootflashFiles()
        instance.rest_send = RestSend(params_deleted)

    match = r"BootflashFiles\.refresh_switch_details:\s+"
    match += r"switch_details must be set before calling\s+"
    match += r"refresh_switch_details\."
    with pytest.raises(ValueError, match=match):
        instance.refresh_switch_details()


def test_bootflash_files_00310() -> None:
    """
    ### Classes and Methods
    - BootflashInfo()
        - refresh_switch_details()

    ### Summary
    Verify ``refresh_switch_details()`` raises ``ValueError`` if
    ``rest_send`` is not set.

    ### Test
    -   Call ``instance.refresh_switch_details()`` without having set
        ``BootflashFiles().rest_send``.
    -   ValueError is raised.
    -   Error message matches expectation.
    """
    with does_not_raise():
        instance = BootflashFiles()
        instance.switch_details = SwitchDetails()

    match = r"BootflashFiles\.refresh_switch_details:\s+"
    match += r"rest_send must be set before calling\s+"
    match += r"refresh_switch_details\."
    with pytest.raises(ValueError, match=match):
        instance.refresh_switch_details()
