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
"""
ImageStage - unit tests
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"


import inspect

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.exceptions import \
    ControllerResponseError
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

from .utils import (MockAnsibleModule, does_not_raise, image_stage_fixture,
                    params, responses_ep_image_stage, responses_ep_issu,
                    responses_ep_version)


def test_image_stage_00000(image_stage) -> None:
    """
    ### Classes and Methods
    -   ``ImageStage``
            - ``__init__``

    ### Test
    - Class attributes are initialized to expected values.
    """
    with does_not_raise():
        instance = image_stage
    assert instance.class_name == "ImageStage"
    assert instance.action == "image_stage"
    assert instance.controller_version is None
    assert instance.diff == {}
    assert instance.payload is None
    assert instance.saved_response_current == {}
    assert instance.saved_result_current == {}
    assert isinstance(instance.serial_numbers_done, set)
    assert isinstance(instance.serial_numbers_todo, set)

    assert instance.controller_version_instance.class_name == "ControllerVersion"
    assert instance.ep_image_stage.class_name == "EpImageStage"
    assert instance.issu_detail.class_name == "SwitchIssuDetailsBySerialNumber"
    assert instance.wait_for_controller_done.class_name == "WaitForControllerDone"

    module_path = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/"
    module_path += "stagingmanagement/stage-image"
    assert instance.ep_image_stage.path == module_path
    assert instance.ep_image_stage.verb == "POST"

    # properties
    assert instance.check_interval == 10
    assert instance.check_timeout == 1800
    assert instance.rest_send is None
    assert instance.results is None
    assert instance.serial_numbers is None


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_image_stage_00100a", "12.1.2e"),
        ("test_image_stage_00100b", "12.1.3b"),
    ],
)
def test_image_stage_00100(image_stage, key, expected) -> None:
    """
    ### Classes and Methods
    -   ``ImageStage``
            - ``_populate_controller_version``

    ### Summary
    Verify that ``_populate_controller_version`` sets the controller version
    correctly based on the response from the controller.

    ### Test
    - test_image_stage_00100a -> instance.controller_version == "12.1.2e"
    - test_image_stage_00100b -> instance.controller_version == "12.1.3b"

    ### Description
    ``_populate_controller_version`` retrieves the controller version from
    the controller.  This is used in commit() to populate the payload
    with either a misspelled "sereialNum" key/value (12.1.2e) or a
    correctly-spelled "serialNumbers" key/value (12.1.3b).
    """

    def responses():
        # ImageStage()._populate_controller_version
        yield responses_ep_version(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_stage
        instance.results = Results()
        instance.rest_send = rest_send
        instance.controller_version_instance.rest_send = rest_send
        instance._populate_controller_version()
    assert instance.controller_version == expected


def test_image_stage_00200(image_stage) -> None:
    """
    ### Classes and Methods
    -   ``ImageStage``
            - ``prune_serial_numbers``

    ### Summary
    Verify that ``prune_serial_numbers`` prunes serial numbers that have already
    been staged.

    ### Setup
    -   ``responses_ep_issu()`` returns 200 response indicating that
        ``imageStaged`` is "none" for three serial numbers and "Success"
        for two serial numbers in the serial_numbers list.

    ### Test
    -   ``serial_numbers`` contains only serial numbers
        for which imageStaged == "none" (FDO2112189M, FDO211218AX, FDO211218B5)
    -   ``serial_numbers`` does not contain serial numbers
        for which imageStaged == "Success" (FDO211218FV, FDO211218GC)

    ### Description
    ``prune_serial_numbers()`` removes serial numbers from the list for which
    imageStaged == "Success"
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageStage().prune_serial_numbers
        yield responses_ep_issu(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_stage
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()
        instance.serial_numbers = [
            "FDO2112189M",
            "FDO211218AX",
            "FDO211218B5",
            "FDO211218FV",
            "FDO211218GC",
        ]
        instance.prune_serial_numbers()
    assert isinstance(instance.serial_numbers, list)
    assert len(instance.serial_numbers) == 3
    assert "FDO2112189M" in instance.serial_numbers
    assert "FDO211218AX" in instance.serial_numbers
    assert "FDO211218B5" in instance.serial_numbers
    assert "FDO211218FV" not in instance.serial_numbers
    assert "FDO211218GC" not in instance.serial_numbers


def test_image_stage_00300(image_stage) -> None:
    """
    ### Classes and Methods
    -   ``ImageStage``
            - ``validate_serial_numbers``

    ### Summary
    Verify that ``validate_serial_numbers`` raises ``ControllerResponseError``
    appropriately.

    ### Setup
    -   ``responses_ep_issu()`` returns 200 response indicating that
        ``imageStaged`` is "Success" for one serial number and "Failed"
        for the other serial number in the serial_numbers list.

    ### Test
    - ``ControllerResponseError`` is not called when imageStaged == "Success"
    - ``ControllerResponseError`` is called when imageStaged == "Failed"

    ### Description
    ``validate_serial_numbers`` checks the imageStaged status for each serial
    number and raises ``ControllerResponseError`` if imageStaged == "Failed"
    for any serial number.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageStage().validate_serial_numbers
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
        instance = image_stage
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()
        instance.serial_numbers = ["FDO21120U5D", "FDO2112189M"]

    match = "Image staging is failing for the following switch: "
    match += "cvd-2313-leaf, 172.22.150.108, FDO2112189M. "
    match += "Check the switch connectivity to the controller "
    match += "and try again."

    with pytest.raises(ControllerResponseError, match=match):
        instance.validate_serial_numbers()


def test_image_stage_00400(image_stage) -> None:
    """
    ### Classes and Methods
    -   ``ImageStage``
            - ``_wait_for_image_stage_to_complete``

    ### Summary
    Verify proper behavior of _wait_for_image_stage_to_complete when
    ``imageStaged`` is "Success" for all serial numbers.

    ### Setup
    -   ``responses_ep_issu()`` returns 200 response indicating that
        ``imageStaged`` is "Success" for all serial numbers in the
        serial_numbers list.

    ### Test
    -   "imageStaged" == "Success" for all serial numbers so
        ``ControllerResponseError`` is not raised.
    -   ``serial_numbers_done`` is a set().
    -   ``serial_numbers_done`` has length 2.
    -   ``serial_numbers_done`` == ``serial_numbers``.

    ### Description
    ``_wait_for_image_stage_to_complete`` looks at the "imageStaged" status for
    each serial number and waits for it to be "Success" or "Failed".
    In the case where all serial numbers are "Success", the module returns.
    In the case where any serial number is "Failed", the module raises
    ``ControllerResponseError``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageStage()._wait_for_image_stage_to_complete
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
        instance = image_stage
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()
        instance.serial_numbers = ["FDO21120U5D", "FDO2112189M"]
        instance._wait_for_image_stage_to_complete()
    assert isinstance(instance.serial_numbers_done, set)
    assert len(instance.serial_numbers_done) == 2
    assert "FDO21120U5D" in instance.serial_numbers_done
    assert "FDO2112189M" in instance.serial_numbers_done


def test_image_stage_00410(image_stage) -> None:
    """
    ### Classes and Methods
    -   ``ImageStage``
            - ``_wait_for_image_stage_to_complete``

    ### Summary
    Verify proper behavior of ``_wait_for_image_stage_to_complete`` when
    imageStaged is "Failed" for one serial number and imageStaged
    is "Success" for one serial number.

    ### Setup
    -   ``responses_ep_issu()`` returns 200 response indicating that
        ``imageStaged`` is "Success" for one of the serial numbers in the
        serial_numbers list and "Failed" for the other.

    ### Test
    -   ``serial_numbers_done`` is a set().
    -   ``serial_numbers_done`` has length 1.
    -   ``serial_numbers_done`` contains FDO21120U5D.
        because imageStaged is "Success".
    -   ``ValueError`` is raised on serial number FDO2112189M
        because imageStaged is "Failed".
    -   Error message matches expectation.

    ### Description
    ``_wait_for_image_stage_to_complete`` looks at the imageStaged status
    for each serial number and waits for it to be "Success" or "Failed".
    In the case where all serial numbers are "Success", the module returns.
    In the case where any serial number is "Failed", the module raises
    ``ValueError``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageStage()._wait_for_image_stage_to_complete
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
        instance = image_stage
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()
        instance.serial_numbers = ["FDO21120U5D", "FDO2112189M"]

    match = "Seconds remaining 1790: stage image failed for "
    match += "cvd-2313-leaf, FDO2112189M, 172.22.150.108. image "
    match += "staged percent: 90"

    with pytest.raises(ValueError, match=match):
        instance._wait_for_image_stage_to_complete()

    assert isinstance(instance.serial_numbers_done, set)
    assert len(instance.serial_numbers_done) == 1
    assert "FDO21120U5D" in instance.serial_numbers_done
    assert "FDO2112189M" not in instance.serial_numbers_done


def test_image_stage_00420(image_stage) -> None:
    """
    ### Classes and Methods
    -   ``ImageStage``
            - ``_wait_for_image_stage_to_complete``

    ### Summary
    Verify proper behavior of ``_wait_for_image_stage_to_complete`` when
    timeout is reached for one serial number (i.e. ``imageStaged`` is
    "In-Progress") and ``imageStaged`` is "Success" for one serial number.

    ### Setup
    -   ``responses_ep_issu()`` returns 200 response indicating that
        ``imageStaged`` is "Success" for one of the serial numbers in the
        serial_numbers list and "In-Progress" for the other.

    ### Test
    -   ``serial_numbers_done`` is a set().
    -   ``serial_numbers_done`` has length 1.
    -   ``serial_numbers_done`` contains FDO21120U5D.
        because imageStaged == "Success".
    -   ``serial_numbers_done`` does not contain FDO2112189M.
    -   ``ValueError`` is raised due to timeout because FDO2112189M
        ``imageStaged`` == "In-Progress".
    -   Error message matches expectation.

    ### Description
    See test_image_stage_410 for functional details.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageStage()._wait_for_image_stage_to_complete
        yield responses_ep_issu(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.send_interval = 1
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_stage
        instance.results = Results()
        instance.rest_send = rest_send
        instance.check_timeout = 1
        instance.check_interval = 1
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()
        instance.serial_numbers = ["FDO21120U5D", "FDO2112189M"]

    match = "ImageStage._wait_for_image_stage_to_complete: "
    match += "Timed out waiting for image stage to complete. "
    match += "serial_numbers_done: FDO21120U5D, "
    match += "serial_numbers_todo: FDO21120U5D,FDO2112189M"

    with pytest.raises(ValueError, match=match):
        instance._wait_for_image_stage_to_complete()
    assert isinstance(instance.serial_numbers_done, set)
    assert len(instance.serial_numbers_done) == 1
    assert "FDO21120U5D" in instance.serial_numbers_todo
    assert "FDO2112189M" in instance.serial_numbers_todo
    assert "FDO21120U5D" in instance.serial_numbers_done
    assert "FDO2112189M" not in instance.serial_numbers_done


def test_image_stage_00500(image_stage) -> None:
    """
    ### Classes and Methods
    -   ``ImageStage``
            - ``wait_for_controller``

    ### Summary
    Verify proper behavior of ``wait_for_controller`` when no actions
    are pending.

    ### Setup
    -   ``responses_ep_issu()`` returns 200 response indicating that no
        actions are "In-Progress".

    ### Test
    -   ``wait_for_controller_done.done`` is a set().
    -   ``serial_numbers_done`` has length 2.
    -   ``serial_numbers_done`` contains all serial numbers in
        ``serial_numbers``.
    -   Exception is not raised.

    ### Description
    ``wait_for_controller`` waits until staging, validation, and upgrade
    actions are complete for all serial numbers.  It calls
    ``SwitchIssuDetailsBySerialNumber.actions_in_progress()`` and expects
    this to return False.  ``actions_in_progress()`` returns True until none
    of the following keys has a value of "In-Progress":
    - ``imageStaged``
    - ``upgrade``
    - ``validated``
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageStage().wait_for_controller
        yield responses_ep_issu(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.send_interval = 1
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_stage
        instance.results = Results()
        instance.rest_send = rest_send
        instance.check_timeout = 1
        instance.check_interval = 1
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()
        instance.serial_numbers = ["FDO21120U5D", "FDO2112189M"]
        instance.wait_for_controller()

    assert isinstance(instance.wait_for_controller_done.done, set)
    assert len(instance.wait_for_controller_done.done) == 2
    assert "FDO21120U5D" in instance.wait_for_controller_done.todo
    assert "FDO2112189M" in instance.wait_for_controller_done.todo
    assert "FDO21120U5D" in instance.wait_for_controller_done.done
    assert "FDO2112189M" in instance.wait_for_controller_done.done


def test_image_stage_00510(image_stage) -> None:
    """
    ### Classes and Methods
    -   ``ImageStage``
            - ``wait_for_controller``

    ### Summary
    Verify proper behavior of ``wait_for_controller`` when there is a timeout
    waiting for actions on the controller to complete.

    ### Setup
    -   ``responses_ep_issu()`` returns 200 response indicating that
        ``imageStaged`` is "In-Progress" for one of the serial numbers in the
        serial_numbers list.

    ### Test
    -   `serial_numbers_done` is a set()
    -   serial_numbers_done has length 1
    -   ``serial_numbers_done`` contains FDO21120U5D
        because imageStaged == "Success"
    -   ``serial_numbers_done`` does not contain FDO2112189M
    -   ``ValueError`` is raised due to timeout because FDO2112189M
        imageStaged == "In-Progress"

    ### Description
    See test_image_stage_00500 for functional details.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageStage().wait_for_controller
        yield responses_ep_issu(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.send_interval = 1
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_stage
        instance.results = Results()
        instance.rest_send = rest_send
        instance.check_timeout = 1
        instance.check_interval = 1
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()
        instance.serial_numbers = ["FDO21120U5D", "FDO2112189M"]

    match = r"ImageStage\.wait_for_controller:\s+"
    match += r"Error while waiting for controller actions to complete\.\s+"
    match += r"Error detail: WaitForControllerDone\.commit:\s+"
    match += r"Timed out after 1 seconds waiting for controller actions to\s+"
    match += r"complete on items: \['FDO21120U5D', 'FDO2112189M'\]\.\s+"
    match += r"The following items did complete: FDO21120U5D\."

    with pytest.raises(ValueError, match=match):
        instance.wait_for_controller()
    assert isinstance(instance.wait_for_controller_done.done, set)
    assert len(instance.wait_for_controller_done.done) == 1
    assert "FDO21120U5D" in instance.wait_for_controller_done.todo
    assert "FDO2112189M" in instance.wait_for_controller_done.todo
    assert "FDO21120U5D" in instance.wait_for_controller_done.done
    assert "FDO2112189M" not in instance.wait_for_controller_done.done


MATCH_00600 = r"ImageStage\.check_interval:\s+"
MATCH_00600 += r"must be a positive integer or zero\."


@pytest.mark.parametrize(
    "arg, value, context",
    [
        (True, None, pytest.raises(TypeError, match=MATCH_00600)),
        (-1, None, pytest.raises(ValueError, match=MATCH_00600)),
        (10, 10, does_not_raise()),
        (0, 0, does_not_raise()),
        ("a", None, pytest.raises(TypeError, match=MATCH_00600)),
    ],
)
def test_image_stage_00600(image_stage, arg, value, context) -> None:
    """
    ### Classes and Methods
    -   ``ImageStage``
            -   ``check_interval``

    ### Summary
    Verify that ``check_interval`` argument validation works as expected.

    ### Test
    - Verify input arguments to ``check_interval`` property

    ### Description
    ``check_interval`` expects a positive integer value, or zero.
    """
    with does_not_raise():
        instance = image_stage
    with context:
        instance.check_interval = arg
    if value is not None:
        assert instance.check_interval == value


MATCH_00700 = r"ImageStage\.check_timeout:\s+"
MATCH_00700 += r"must be a positive integer or zero\."


@pytest.mark.parametrize(
    "arg, value, context",
    [
        (True, None, pytest.raises(TypeError, match=MATCH_00700)),
        (-1, None, pytest.raises(ValueError, match=MATCH_00700)),
        (10, 10, does_not_raise()),
        (0, 0, does_not_raise()),
        ("a", None, pytest.raises(TypeError, match=MATCH_00700)),
    ],
)
def test_image_stage_00700(image_stage, arg, value, context) -> None:
    """
    ### Classes and Methods
    -   ``ImageStage``
        -   ``check_timeout``

    ### Summary
    Verify that ``check_timeout`` argument validation works as expected.

    ### Test
    - Verify input arguments to ``check_timeout`` property

    ### Description
    ``check_timeout`` expects a positive integer value, or zero.
    """
    with does_not_raise():
        instance = image_stage
    with context:
        instance.check_timeout = arg
    if value is not None:
        assert instance.check_timeout == value


MATCH_00800 = r"ImageStage\.serial_numbers:\s+"
MATCH_00800 += r"must be a python list of switch serial numbers\."


@pytest.mark.parametrize(
    "arg, value, context",
    [
        ("foo", None, pytest.raises(TypeError, match=MATCH_00800)),
        (10, None, pytest.raises(TypeError, match=MATCH_00800)),
        (["DD001115F", 10], None, pytest.raises(TypeError, match=MATCH_00800)),
        (["DD001115F"], ["DD001115F"], does_not_raise()),
    ],
)
def test_image_stage_00800(image_stage, arg, value, context) -> None:
    """
    ### Classes and Methods
    -   ``ImageStage``
            -   ``serial_numbers``

    ### Summary
    Verify that ``serial_numbers`` argument validation works as expected.

    ### Test
    -   ``TypeError`` is raised if the input is not a list.
    -   ``TypeError`` is raised if the input is not a list of strings.

    ### Description
    serial_numbers expects a list of serial numbers.
    """
    with does_not_raise():
        instance = image_stage
    with context:
        instance.serial_numbers = arg
    if value is not None:
        assert instance.serial_numbers == value


MATCH_00900 = r"ImageStage\.validate_commit_parameters:\s+"
MATCH_00900 += r"serial_numbers must be set before calling commit\(\)\."


@pytest.mark.parametrize(
    "serial_numbers_is_set, expected",
    [
        (True, does_not_raise()),
        (False, pytest.raises(ValueError, match=MATCH_00900)),
    ],
)
def test_image_stage_00900(image_stage, serial_numbers_is_set, expected) -> None:
    """
    ### Classes and Methods
    -   ``ImageStage``
            `   ``commit``

    ### Summary
    Verify that ``commit`` raises ``ValueError`` appropriately based on value of
    ``serial_numbers``.

    ### Setup
    - responses_ep_issu() returns 200 responses.
    - responses_ep_version() returns a 200 response.
    - responses_ep_image_stage() returns a 200 response.

    ### Test
    -   ``ValueError`` is raised when serial_numbers is not set.
    -   ``ValueError`` is not raised when serial_numbers is set.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageStage().prune_serial_numbers
        yield responses_ep_issu(key)
        # ImageStage().validate_serial_numbers
        yield responses_ep_issu(key)
        # ImageStage()._populate_controller_version
        yield responses_ep_version(key)
        # RestSend.commit_normal_mode
        yield responses_ep_image_stage(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.send_interval = 1
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_stage
        instance.results = Results()
        instance.rest_send = rest_send
        instance.check_timeout = 1
        instance.check_interval = 1
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()

    if serial_numbers_is_set:
        instance.serial_numbers = ["FDO21120U5D"]
    with expected:
        instance.commit()


@pytest.mark.parametrize(
    "key, controller_version, expected_serial_number_key",
    [
        ("test_image_stage_00910a", "12.1.2e", "sereialNum"),
        ("test_image_stage_00910b", "12.1.3b", "serialNumbers"),
    ],
)
def test_image_stage_00910(
    image_stage, key, controller_version, expected_serial_number_key
) -> None:
    """
    ### Classes and Methods
    -   ``ImageStage``
            `   ``commit``

    ### Summary
    Verify that the serial number key name in the payload is set correctly
    based on the controller version.

    ### Setup
    - ``responses_ep_issu()`` returns 200 responses.
    - ``responses_ep_version()`` returns a 200 response.
    - ``responses_ep_image_stage()`` returns a 200 response.
    - ``serial_numbers`` is set to ["FDO21120U5D"]

    ### Test
    - controller_version 12.1.2e -> key name "sereialNum" (yes, misspelled)
    - controller_version 12.1.3b -> key name "serialNumbers

    ### Description
    ``commit()`` will set the payload key name for the serial number
    based on ``controller_version``.
    """

    def responses():
        # ImageStage().prune_serial_numbers
        yield responses_ep_issu(key)
        # ImageStage().validate_serial_numbers
        yield responses_ep_issu(key)
        # ImageStage()._populate_controller_version
        yield responses_ep_version(key)
        # RestSend.commit_normal_mode
        yield responses_ep_image_stage(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.send_interval = 1
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_stage
        instance.results = Results()
        instance.rest_send = rest_send
        instance.check_timeout = 1
        instance.check_interval = 1
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()
        instance.serial_numbers = ["FDO21120U5D"]
        instance.commit()

    assert expected_serial_number_key in instance.payload.keys()


def test_image_stage_00920(image_stage) -> None:
    """
    ### Classes and Methods
    -   ``ImageStage``
            `   ``commit``

    ### Summary
    Verify that commit() sets result, response, and response_data
    appropriately when serial_numbers is empty.

    ### Setup
    - ``serial_numbers`` is set to [] (empty list)

    ### Test
    - commit() sets the following to expected values:
        - self.result, self.result_current
        - self.response, self.response_current
        - self.response_data

    ### Description
    When len(serial_numbers) == 0, commit() will set result and
    response properties, and return without doing anything else.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield None

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.send_interval = 1
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_stage
        instance.results = Results()
        instance.rest_send = rest_send
        instance.check_timeout = 1
        instance.check_interval = 1
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()
        instance.serial_numbers = []
        instance.commit()

    response_msg = "No images to stage."
    assert instance.results.result == [
        {"success": True, "changed": False, "sequence_number": 1}
    ]
    assert instance.results.result_current == {
        "success": True,
        "changed": False,
        "sequence_number": 1,
    }
    assert instance.results.response_current == {
        "DATA": [{"key": "ALL", "value": response_msg}],
        "sequence_number": 1,
    }
    assert instance.results.response == [instance.results.response_current]
    assert instance.results.response_data == [{"response": "No images to stage."}]


def test_image_stage_00930(image_stage) -> None:
    """
    ### Classes and Methods
    -   ``ImageStage``
            `   ``commit``

    ### Summary
    Verify that ``ControllerResponseError`` is raised on 500 response from
    the controller.

    ### Setup
    - ``responses_ep_issu()`` returns 200 responses.
    - ``responses_ep_version()`` returns a 200 response.
    - ``responses_ep_image_stage()`` returns a 500 response.

    ### Test
    - commit() raises ``ControllerResponseError``

    ### Description
    commit() raises ``ControllerResponseError`` on non-success response
    from the controller.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageStage().prune_serial_numbers
        yield responses_ep_issu(key)
        # ImageStage().validate_serial_numbers
        yield responses_ep_issu(key)
        # ImageStage()._populate_controller_version
        yield responses_ep_version(key)
        # RestSend.commit_normal_mode
        yield responses_ep_image_stage(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.send_interval = 1
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_stage
        instance.results = Results()
        instance.rest_send = rest_send
        instance.check_timeout = 1
        instance.check_interval = 1
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()
        instance.serial_numbers = ["FDO21120U5D"]

    match = r"ImageStage\.commit:\s+"
    match += r"failed\. Controller response:.*"
    with pytest.raises(ControllerResponseError, match=match):
        instance.commit()
    assert instance.results.result == [
        {"success": False, "changed": False, "sequence_number": 1}
    ]
    assert instance.results.response_current["RETURN_CODE"] == 500


def test_image_stage_00940(image_stage) -> None:
    """
    ### Classes and Methods
    -   ``ImageStage``
            `   ``commit``

    ### Summary
    Verify that commit() sets self.diff to expected values on 200 response
    from the controller for an image stage request.

    ### Setup
    - ``responses_ep_issu()`` returns 200 responses.
    - ``responses_ep_version()`` returns a 200 response with controller
        version 12.1.3b.
    - ``responses_ep_image_stage()`` returns a 200 response.

    ### Test
    - commit() sets self.diff to the expected values
    """
    method_name = inspect.stack()[0][3]
    key_a = f"{method_name}a"
    key_b = f"{method_name}b"

    def responses():
        # ImageStage().prune_serial_numbers()
        yield responses_ep_issu(key_a)
        # ImageStage().validate_serial_numbers()
        yield responses_ep_issu(key_a)
        # ImageStage().wait_for_controller()
        yield responses_ep_issu(key_a)
        # ImageStage()._populate_controller_version
        yield responses_ep_version(key_a)
        # ImageStage().commit() -> ImageStage().rest_send.commit()
        yield responses_ep_image_stage(key_a)
        # ImageStage()._wait_for_image_stage_to_complete()
        yield responses_ep_issu(key_b)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.send_interval = 1
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_stage
        instance.results = Results()
        instance.rest_send = rest_send
        instance.check_timeout = 1
        instance.check_interval = 1
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()
        instance.serial_numbers = ["FDO21120U5D"]
        instance.commit()

    assert instance.results.result_current == {
        "success": True,
        "changed": True,
        "sequence_number": 1,
    }
    assert instance.results.diff[0]["172.22.150.102"]["policy_name"] == "KR5M"
    assert instance.results.diff[0]["172.22.150.102"]["ip_address"] == "172.22.150.102"
    assert instance.results.diff[0]["172.22.150.102"]["serial_number"] == "FDO21120U5D"
