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
    assert instance.mandatory_target_keys == [
        "filepath",
        "ip_address",
        "serial_number",
        "supervisor",
    ]
    assert instance.ok_to_delete_files_reason is None
    assert instance.payload == {"deleteFiles": []}
    assert instance.filename is None
    assert instance.filepath is None
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
    - BootflashFiles()
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


def test_bootflash_files_00110() -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
        - commit()
        - validate_commit_parameters()

    ### Summary
    Verify ``ValueError`` is raised if ``rest_send`` is not set before
    calling commit.

    ### Test
    -   ValueError is raised by validate_commit_parameters().
    -   Error message matches expectation.
    """
    with does_not_raise():
        instance = BootflashFiles()
        instance.results = Results()
        instance.switch_details = SwitchDetails()

    match = r"BootflashFiles.validate_commit_parameters:\s+"
    match += r"rest_send must be set before calling commit\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_bootflash_files_00120() -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
        - commit()
        - validate_commit_parameters()

    ### Summary
    Verify ``ValueError`` is raised if ``results`` is not set before
    calling commit.

    ### Test
    -   ValueError is raised by validate_commit_parameters().
    -   Error message matches expectation.
    """
    with does_not_raise():
        instance = BootflashFiles()
        instance.rest_send = RestSend(params_deleted)
        instance.switch_details = SwitchDetails()

    match = r"BootflashFiles.validate_commit_parameters:\s+"
    match += r"results must be set before calling commit\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_bootflash_files_00130() -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
        - commit()
        - validate_commit_parameters()

    ### Summary
    Verify ``ValueError`` is raised if ``switch_details`` is not set before
    calling commit.

    ### Test
    -   ValueError is raised by validate_commit_parameters().
    -   Error message matches expectation.
    """
    with does_not_raise():
        instance = BootflashFiles()
        instance.rest_send = RestSend(params_deleted)
        instance.results = Results()

    match = r"BootflashFiles.validate_commit_parameters:\s+"
    match += r"switch_details must be set before calling commit\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_bootflash_files_00200() -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
        - add_file()

    ### Summary
    Verify that add_file(), when called twice with the same ip_address,
    and partition, adds the second file to the payload under the same
    serial number (yes, serial number since ip_address is converted to
    serial number when the payload is built) and partition as the
    first file.

    ### Setup
    -   Call add_file() twice with same ip_address and partition.

    ### Test
    -   The second file is added to the payload under the same
        serial number and partition.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    def responses():
        yield responses_ep_all_switches(f"{key}a")

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params_deleted)
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

        instance.filepath = "bootflash:/air.txt"
        instance.filename = "air.txt"
        instance.ip_address = "172.22.150.112"
        instance.partition = "bootflash:"
        instance.supervisor = "active"
        instance.target = targets(f"{key}a")
        instance.add_file()

        instance.filepath = "bootflash:/earth.txt"
        instance.filename = "earth.txt"
        instance.ip_address = "172.22.150.112"
        instance.partition = "bootflash:"
        instance.supervisor = "active"
        instance.target = targets(f"{key}b")
        instance.add_file()

    assert instance.payload == payloads_bootflash_files(f"{key}a")


def test_bootflash_files_00210() -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
        - add_file()

    ### Summary
    Verify that add_file(), when called twice with a different ip_address,
    and partition, adds the second file under the different
    serial number (yes, serial number since ip_address is converted to
    serial number when the payload is built) and partition.

    ### Setup
    -   Call add_file() twice with different ip_address and partition.
    -   Call add_file() a third time with the same ip_address and partition
        as the second call, and with the same filename.  This will not
        change the payload since it is rejected in
        ``add_file_to_existing_payload()``.

    ### Test
    -   The second file is added to the payload under a different serial
        number and partition.
    -   The third (duplicate) file is not added to the payload.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    def responses():
        yield responses_ep_all_switches(f"{key}a")

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params_deleted)
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

        instance.filepath = "bootflash:/air.txt"
        instance.filename = "air.txt"
        instance.ip_address = "172.22.150.112"
        instance.partition = "bootflash:"
        instance.supervisor = "active"
        instance.target = targets(f"{key}a")
        instance.add_file()

        instance.filepath = "bootflash:/black.txt"
        instance.filename = "black.txt"
        instance.ip_address = "172.22.150.113"
        instance.partition = "bootflash:"
        instance.supervisor = "active"
        instance.target = targets(f"{key}b")
        instance.add_file()

        # Try to add the same file again.  This will not change the payload since
        # it is rejected in add_file_to_existing_payload().
        instance.filepath = "bootflash:/black.txt"
        instance.filename = "black.txt"
        instance.ip_address = "172.22.150.113"
        instance.partition = "bootflash:"
        instance.supervisor = "active"
        instance.target = targets(f"{key}b")
        instance.add_file()

    assert instance.payload == payloads_bootflash_files(f"{key}a")


@pytest.mark.parametrize(
    "key_responses_ep_all_switches, reason",
    [
        ("a", "migration"),
        ("b", "inconsistent"),
    ],
)
def test_bootflash_files_00220(key_responses_ep_all_switches, reason) -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
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


def test_bootflash_files_00230() -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
        - add_file()
        - validate_prerequisites_for_add_file()

    ### Summary
    Verify ``ValueError`` is raised if ``filename`` is not set before
    calling add_file().

    ### Test
    -   ValueError is raised by validate_prerequisites_for_add_file().
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = BootflashFiles()
        instance.filepath = "bootflash:/air.txt"
        instance.ip_address = "192.168.1.1"
        instance.rest_send = RestSend(params_deleted)
        instance.results = Results()
        instance.supervisor = "active"
        instance.switch_details = SwitchDetails()
        instance.target = targets(key)

    match = r"BootflashFiles.validate_prerequisites_for_add_file:\s+"
    match += r"filename must be set before calling add_file\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.add_file()


def test_bootflash_files_00240() -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
        - add_file()
        - validate_prerequisites_for_add_file()

    ### Summary
    Verify ``ValueError`` is raised if ``filepath`` is not set before
    calling add_file().

    ### Test
    -   ValueError is raised by validate_prerequisites_for_add_file().
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = BootflashFiles()
        instance.filename = "air.txt"
        instance.ip_address = "192.168.1.1"
        instance.rest_send = RestSend(params_deleted)
        instance.results = Results()
        instance.supervisor = "active"
        instance.switch_details = SwitchDetails()
        instance.target = targets(key)

    match = r"BootflashFiles.validate_prerequisites_for_add_file:\s+"
    match += r"filepath must be set before calling add_file\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.add_file()


def test_bootflash_files_00250() -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
        - add_file()
        - validate_prerequisites_for_add_file()

    ### Summary
    Verify ``ValueError`` is raised if ``ip_address`` is not set before
    calling add_file().

    ### Test
    -   ValueError is raised by validate_prerequisites_for_add_file().
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = BootflashFiles()
        instance.filename = "air.txt"
        instance.filepath = "bootflash:/air.txt"
        instance.rest_send = RestSend(params_deleted)
        instance.results = Results()
        instance.supervisor = "active"
        instance.switch_details = SwitchDetails()
        instance.target = targets(key)

    match = r"BootflashFiles.validate_prerequisites_for_add_file:\s+"
    match += r"ip_address must be set before calling add_file\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.add_file()


def test_bootflash_files_00260() -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
        - add_file()
        - validate_prerequisites_for_add_file()

    ### Summary
    Verify ``ValueError`` is raised if ``supervisor`` is not set before
    calling add_file().

    ### Test
    -   ValueError is raised by validate_prerequisites_for_add_file().
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = BootflashFiles()
        instance.filename = "air.txt"
        instance.filepath = "bootflash:/air.txt"
        instance.ip_address = "192.168.1.1"
        instance.rest_send = RestSend(params_deleted)
        instance.results = Results()
        instance.switch_details = SwitchDetails()
        instance.target = targets(key)

    match = r"BootflashFiles.validate_prerequisites_for_add_file:\s+"
    match += r"supervisor must be set before calling add_file\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.add_file()


def test_bootflash_files_00270() -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
        - add_file()
        - validate_prerequisites_for_add_file()

    ### Summary
    Verify ``ValueError`` is raised if ``switch_details`` is not set before
    calling add_file().

    ### Test
    -   ValueError is raised by validate_prerequisites_for_add_file().
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = BootflashFiles()
        instance.filename = "air.txt"
        instance.filepath = "bootflash:/air.txt"
        instance.ip_address = "192.168.1.1"
        instance.rest_send = RestSend(params_deleted)
        instance.results = Results()
        instance.supervisor = "active"
        instance.target = targets(key)

    match = r"BootflashFiles.validate_prerequisites_for_add_file:\s+"
    match += r"switch_details must be set before calling add_file\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.add_file()


def test_bootflash_files_00280() -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
        - add_file()
        - validate_prerequisites_for_add_file()

    ### Summary
    Verify ``ValueError`` is raised if ``target`` is not set before
    calling add_file().

    ### Test
    -   ValueError is raised by validate_prerequisites_for_add_file().
    -   Error message matches expectation.
    """
    with does_not_raise():
        instance = BootflashFiles()
        instance.filename = "air.txt"
        instance.filepath = "bootflash:/air.txt"
        instance.ip_address = "192.168.1.1"
        instance.rest_send = RestSend(params_deleted)
        instance.results = Results()
        instance.supervisor = "active"
        instance.switch_details = SwitchDetails()

    match = r"BootflashFiles.validate_prerequisites_for_add_file:\s+"
    match += r"target must be set before calling add_file\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.add_file()


def test_bootflash_files_00300() -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
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
    - BootflashFiles()
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


def test_bootflash_files_00400() -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
        - ip_address_to_serial_number()

    ### Summary
    Verify ``ip_address_to_serial_number()`` raises ``ValueError`` if
    ``switch_details`` raises TypeError or ValueError when
    ``switch_details.serial_number`` is accessed.

    ### Test
    -   ``EpAllSwitches`` response is modified such that the ``serialNumber``
        key is missing.
    -   ``ip_address_to_serial_number()`` raises ``ValueError``.
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def configs():
        yield configs_deleted(f"{key}a")

    gen_configs = ResponseGenerator(configs())

    def responses():
        yield responses_ep_all_switches(key)

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

    match = r"BootflashFiles\.ip_address_to_serial_number:\s+"
    match += r"SwitchDetails\._get: 172\.22\.150\.112 does not have\s+"
    match += r"a key named serialNumber\."
    with pytest.raises(ValueError, match=match):
        instance.ip_address_to_serial_number("172.22.150.112")


def test_bootflash_files_00500() -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
        - delete_files()

    ### Summary
    Verify ``delete_files`` generates a synthetic response when there are no
    files to delete.

    ### Test
    -   delete_files() is called directly.
    -   Since the payload is initialized in ``BootflashFiles().__init__()``
        with an empty list, there are no files to delete when
        ``delete_files()`` is called.
    -   assert that the response and result are as expected.
    """
    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    rest_send = RestSend(params_deleted)
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
        instance.delete_files()

    assert instance.results.response_current["RETURN_CODE"] == 200
    assert instance.results.response_current["MESSAGE"] == "No files to delete."
    assert instance.results.result == [
        {"success": True, "changed": False, "sequence_number": 1}
    ]


def test_bootflash_files_00600() -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
        - partition_and_serial_number_exist_in_payload()

    ### Summary
    Verify ``partition_and_serial_number_exist_in_payload`` returns False
    if self.partition does not match the partition in the payload.

    ### Setup
    -   BootflashFiles().payload is set to include a file on partition
        bootflash: on switch with ip_address 172.22.150.112.
    -   BootflashFiles().partition is set to usb1:
    -   BootflashFiles().ip_address is set to 172.22.150.112.

    ### Test
    -   Verify that ``partition_and_serial_number_exist_in_payload()``
        returns False.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_all_switches(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params_deleted)
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
        instance.payload = payloads_bootflash_files(key)
        instance.ip_address = "172.22.150.112"
        instance.partition = "usb1:"

    assert instance.partition_and_serial_number_exist_in_payload() is False


def test_bootflash_files_00610() -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
        - partition_and_serial_number_exist_in_payload()

    ### Summary
    Verify ``partition_and_serial_number_exist_in_payload`` returns True
    if a file in the payload matches the filters ``ip_address`` and
    ``partition``.

    ### Setup
    -   BootflashFiles().payload is set to include a file on partition
        bootflash: on switch with ip_address 172.22.150.112.
    -   BootflashFiles().partition is set to bootflash:
    -   BootflashFiles().ip_address is set to 172.22.150.112.

    ### Test
    -   Verify that partition_and_serial_number_exist_in_payload()
        returns True.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_all_switches(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params_deleted)
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
        instance.payload = payloads_bootflash_files(key)
        instance.ip_address = "172.22.150.112"
        instance.partition = "bootflash:"

    assert instance.partition_and_serial_number_exist_in_payload() is True


def test_bootflash_files_00700() -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
        - switch_details.setter

    ### Summary
    Verify ``switch_details.setter`` raises ``TypeError`` if passed a string
    (i.e. not a class instance and not an instance of ``SwitchDetails()``).

    ### Test
    -   ``TypeError`` is raised.
    -   Error message matches expectations.
    """
    with does_not_raise():
        instance = BootflashFiles()

    match = r"BootflashFiles.switch_details:\s+"
    match += r"value must be an instance of SwitchDetails\.\s+"
    match += r"Got value foo of type str\.\s+"
    match += r"Error detail: 'str' object has no attribute 'class_name'\."
    with pytest.raises(TypeError, match=match):
        instance.switch_details = "foo"


def test_bootflash_files_00710() -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
        - switch_details.setter

    ### Summary
    Verify ``switch_details.setter`` raises ``TypeError`` if passed
    a class instance other than ``SwitchDetails()``.

    ### Test
    -   ``TypeError`` is raised.
    -   Error message matches expectations.
    """
    with does_not_raise():
        instance = BootflashFiles()

    match = r"BootflashFiles.switch_details:\s+"
    match += r"value must be an instance of SwitchDetails\.\s+"
    match += r"Got value .* of type Results\."
    with pytest.raises(TypeError, match=match):
        instance.switch_details = Results()


def test_bootflash_files_00800() -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
        - target.setter

    ### Summary
    Verify ``target.setter`` raises ``TypeError`` if passed a value
    that is not a dictionary.

    ### Test
    -   ``TypeError`` is raised.
    -   Error message matches expectations.
    """
    with does_not_raise():
        instance = BootflashFiles()

    match = r"BootflashFiles.target:\s+"
    match += r"target must be a dictionary\. Got type str for value foo\."
    with pytest.raises(TypeError, match=match):
        instance.target = "foo"


@pytest.mark.parametrize(
    "parameter", ["filepath", "ip_address", "serial_number", "supervisor"]
)
def test_bootflash_files_00810(parameter) -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
        - target.setter

    ### Summary
    Verify ``target.setter`` raises ``ValueError`` if passed a dictionary
    that is missing a mandatory parameter.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectations.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    target = targets(key)
    target.pop(parameter)

    with does_not_raise():
        instance = BootflashFiles()

    match = r"BootflashFiles.target:\s+"
    match += rf"{parameter} key missing from value.*\."
    with pytest.raises(ValueError, match=match):
        instance.target = target
