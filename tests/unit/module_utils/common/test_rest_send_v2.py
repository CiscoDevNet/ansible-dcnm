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
# pylint: disable=protected-access

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import copy

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.response_handler import \
    ResponseHandler
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_file import \
    Sender
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import (
    ResponseGenerator, does_not_raise)

PARAMS = {"state": "merged", "check_mode": False}


def test_rest_send_v2_00000() -> None:
    """
    ### Classes and Methods
    -   RestSend()
            -   __init__()

    ### Summary
    -   Verify class properties are initialized to expected values
    """
    with does_not_raise():
        instance = RestSend(PARAMS)
    assert instance.params == PARAMS
    assert instance.properties["check_mode"] is False
    assert instance.properties["path"] is None
    assert instance.properties["payload"] is None
    assert instance.properties["response"] == []
    assert instance.properties["response_current"] == {}
    assert instance.properties["response_handler"] is None
    assert instance.properties["result"] == []
    assert instance.properties["result_current"] == {}
    assert instance.properties["send_interval"] == 5
    assert instance.properties["sender"] is None
    assert instance.properties["timeout"] == 300
    assert instance.properties["unit_test"] is False
    assert instance.properties["verb"] is None

    assert instance.saved_check_mode is None
    assert instance.saved_timeout is None
    assert instance._valid_verbs == {"GET", "POST", "PUT", "DELETE"}
    assert instance.check_mode == PARAMS.get("check_mode", None)
    assert instance.state == PARAMS.get("state", None)


def test_rest_send_v2_00100() -> None:
    """
    ### Classes and Methods
    -   RestSend()
            -   _verify_commit_parameters()
            -   commit_normal_mode()
            -   commit()

    ### Summary
    Verify ``_verify_commit_parameters()`` raises ``ValueError``
    due to ``path`` not being set.

    ### Setup - Code
    -   RestSend() is initialized.
    -   RestSend().path is NOT set.
    -   RestSend().response_handler is set.
    -   RestSend().sender is set.
    -   RestSend().verb is set.

    ### Setup - Data
    None

    ### Trigger
    -   RestSend().commit() is called.

    ### Expected Result
    -   RestSend()._verify_commit_parameters() raises ``ValueError``.
    """
    with does_not_raise():
        instance = RestSend(PARAMS)
        instance.sender = Sender()
        instance.response_handler = ResponseHandler()
        instance.verb = "GET"

    match = r"RestSend\.commit:\s+"
    match += r"Error during commit\.\s+"
    match += r"Error details:\s+"
    match += r"RestSend\._verify_commit_parameters:\s+"
    match += r"path must be set before calling commit\(\)."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_rest_send_v2_00110() -> None:
    """
    ### Classes and Methods
    -   RestSend()
            -   _verify_commit_parameters()
            -   commit_normal_mode()
            -   commit()

    ### Summary
    Verify ``_verify_commit_parameters()`` raises ``ValueError``
    due to ``response_handler`` not being set.

    ### Setup - Code
    -   RestSend() is initialized.
    -   RestSend().path is set.
    -   RestSend().response_handler is NOT set.
    -   RestSend().sender is set.
    -   RestSend().verb is set.

    ### Setup - Data
    None

    ### Trigger
    -   RestSend().commit() is called.

    ### Expected Result
    -   RestSend()._verify_commit_parameters() raises ``ValueError``.
    """
    with does_not_raise():
        instance = RestSend(PARAMS)
        instance.path = "/foo/path"
        instance.sender = Sender()
        instance.verb = "GET"

    match = r"RestSend\.commit:\s+"
    match += r"Error during commit\.\s+"
    match += r"Error details:\s+"
    match += r"RestSend\._verify_commit_parameters:\s+"
    match += r"response_handler must be set before calling commit\(\)."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_rest_send_v2_00120() -> None:
    """
    ### Classes and Methods
    -   RestSend()
            -   _verify_commit_parameters()
            -   commit_normal_mode()
            -   commit()

    ### Summary
    Verify ``_verify_commit_parameters()`` raises ``ValueError``
    due to ``response_handler`` not being set.

    ### Setup - Code
    -   RestSend() is initialized.
    -   RestSend().path is set.
    -   RestSend().response_handler is set.
    -   RestSend().sender is NOT set.
    -   RestSend().verb is set.

    ### Setup - Data
    None

    ### Trigger
    -   RestSend().commit() is called.

    ### Expected Result
    -   RestSend()._verify_commit_parameters() raises ``ValueError``.
    """
    with does_not_raise():
        instance = RestSend(PARAMS)
        instance.path = "/foo/path"
        instance.response_handler = ResponseHandler()
        instance.verb = "GET"

    match = r"RestSend\.commit:\s+"
    match += r"Error during commit\.\s+"
    match += r"Error details:\s+"
    match += r"RestSend\._verify_commit_parameters:\s+"
    match += r"sender must be set before calling commit\(\)."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_rest_send_v2_00130() -> None:
    """
    ### Classes and Methods
    -   RestSend()
            -   _verify_commit_parameters()
            -   commit_normal_mode()
            -   commit()

    ### Summary
    Verify ``_verify_commit_parameters()`` raises ``ValueError``
    due to ``response_handler`` not being set.

    ### Setup - Code
    -   RestSend() is initialized.
    -   RestSend().path is set.
    -   RestSend().response_handler is set.
    -   RestSend().sender is set.
    -   RestSend().verb is NOT set.

    ### Setup - Data
    None

    ### Trigger
    -   RestSend().commit() is called.

    ### Expected Result
    -   RestSend()._verify_commit_parameters() raises ``ValueError``.
    """
    with does_not_raise():
        instance = RestSend(PARAMS)
        instance.path = "/foo/path"
        instance.response_handler = ResponseHandler()
        instance.sender = Sender()

    match = r"RestSend\.commit:\s+"
    match += r"Error during commit\.\s+"
    match += r"Error details:\s+"
    match = r"RestSend\._verify_commit_parameters:\s+"
    match += r"verb must be set before calling commit\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_rest_send_v2_00200() -> None:
    """
    ### Classes and Methods
    -   RestSend()
            -   commit_check_mode()
            -   commit()

    ### Summary
    Verify ``commit_check_mode()`` happy path when
    ``verb`` is "GET".

    ### Setup - Code
    -   PARAMS["check_mode"] is set to True
    -   RestSend() is initialized.
    -   RestSend().path is set.
    -   RestSend().response_handler is set.
    -   RestSend().sender is set.
    -   RestSend().verb is set.

    ### Setup - Data
    None

    ### Trigger
    -   RestSend().commit() is called.

    ### Expected Result
    -   The following are updated to expected values:
            -   ``response``
            -   ``response_current``
            -   ``result``
            -   ``result_current``
    -   result_current["found"] is True
    """
    params = copy.copy(PARAMS)
    params["check_mode"] = True

    with does_not_raise():
        instance = RestSend(params)
        instance.path = "/foo/path"
        instance.response_handler = ResponseHandler()
        instance.sender = Sender()
        instance.verb = "GET"
        instance.commit()
    assert instance.response_current["CHECK_MODE"] == instance.check_mode
    assert (
        instance.response_current["DATA"] == "[simulated-check-mode-response:Success]"
    )
    assert instance.response_current["MESSAGE"] == "OK"
    assert instance.response_current["METHOD"] == instance.verb
    assert instance.response_current["REQUEST_PATH"] == instance.path
    assert instance.response_current["RETURN_CODE"] == 200
    assert instance.result_current["success"] is True
    assert instance.result_current["found"] is True
    assert instance.response == [instance.response_current]
    assert instance.result == [instance.result_current]


def test_rest_send_v2_00210() -> None:
    """
    ### Classes and Methods
    -   RestSend()
            -   commit_check_mode()
            -   commit()

    ### Summary
    Verify ``commit_check_mode()`` happy path when
    ``verb`` is "POST".

    ### Setup - Code
    -   PARAMS["check_mode"] is set to True
    -   RestSend() is initialized.
    -   RestSend().path is set.
    -   RestSend().response_handler is set.
    -   RestSend().sender is set.
    -   RestSend().verb is set.

    ### Setup - Data
    None

    ### Trigger
    -   RestSend().commit() is called.

    ### Expected Result
    -   The following are updated to expected values:
            -   ``response``
            -   ``response_current``
            -   ``result``
            -   ``result_current``
    -   result_current["changed"] is True
    """
    params = copy.copy(PARAMS)
    params["check_mode"] = True

    with does_not_raise():
        instance = RestSend(params)
        instance.path = "/foo/path"
        instance.response_handler = ResponseHandler()
        instance.sender = Sender()
        instance.verb = "POST"
        instance.commit()
    assert instance.response_current["CHECK_MODE"] == instance.check_mode
    assert (
        instance.response_current["DATA"] == "[simulated-check-mode-response:Success]"
    )
    assert instance.response_current["MESSAGE"] == "OK"
    assert instance.response_current["METHOD"] == instance.verb
    assert instance.response_current["REQUEST_PATH"] == instance.path
    assert instance.response_current["RETURN_CODE"] == 200
    assert instance.result_current["success"] is True
    assert instance.result_current["changed"] is True
    assert instance.response == [instance.response_current]
    assert instance.result == [instance.result_current]


MATCH_00500 = r"RestSend\.check_mode:\s+"
MATCH_00500 += r"check_mode must be a boolean\.\s+"
MATCH_00500 += r"Got.*\."


@pytest.mark.parametrize(
    "value, does_raise, expected",
    [
        (10, True, pytest.raises(TypeError, match=MATCH_00500)),
        ([10], True, pytest.raises(TypeError, match=MATCH_00500)),
        ({10}, True, pytest.raises(TypeError, match=MATCH_00500)),
        ("FOO", True, pytest.raises(TypeError, match=MATCH_00500)),
        (None, True, pytest.raises(TypeError, match=MATCH_00500)),
        (False, False, does_not_raise()),
        (True, False, does_not_raise()),
    ],
)
def test_rest_send_v2_00500(value, does_raise, expected) -> None:
    """
    ### Classes and Methods
    -   RestSend()
            -   check_mode.setter

    ### Summary
    Verify ``check_mode.setter`` raises ``TypeError``
    when set to inappropriate types, and does not raise
    when set to boolean.

    ### Setup - Code
    -   PARAMS["check_mode"] is set to True
    -   RestSend() is initialized.

    ### Setup - Data
    None

    ### Trigger
    -   RestSend().check_mode is reset using various types.

    ### Expected Result
    -   ``check_mode`` raises TypeError for non-boolean inputs.
    -   ``check_mode`` accepts boolean values.
    """
    with does_not_raise():
        instance = RestSend(PARAMS)

    with expected:
        instance.check_mode = value
    if does_raise is False:
        assert instance.check_mode == value


MATCH_00600 = r"RestSend\.response_current:\s+"
MATCH_00600 += r"response_current must be a dict\.\s+"
MATCH_00600 += r"Got.*\."


@pytest.mark.parametrize(
    "value, does_raise, expected",
    [
        (10, True, pytest.raises(TypeError, match=MATCH_00600)),
        ([10], True, pytest.raises(TypeError, match=MATCH_00600)),
        ({10}, True, pytest.raises(TypeError, match=MATCH_00600)),
        ("FOO", True, pytest.raises(TypeError, match=MATCH_00600)),
        (None, True, pytest.raises(TypeError, match=MATCH_00600)),
        (False, True, pytest.raises(TypeError, match=MATCH_00600)),
        (True, True, pytest.raises(TypeError, match=MATCH_00600)),
        ({"RESULT_CODE": 200}, False, does_not_raise()),
    ],
)
def test_rest_send_v2_00600(value, does_raise, expected) -> None:
    """
    ### Classes and Methods
    -   RestSend()
            -   response_current.setter

    ### Summary
    Verify ``response_current.setter`` raises ``TypeError``
    when set to inappropriate types, and does not raise
    when set to dict.

    ### Setup - Code
    -   RestSend() is initialized.

    ### Setup - Data
    None

    ### Trigger
    -   RestSend().response_current is reset using various types.

    ### Expected Result
    -   ``response_current`` raises TypeError for non-dict inputs.
    -   ``response_current`` accepts dict values.
    """
    with does_not_raise():
        instance = RestSend(PARAMS)

    with expected:
        instance.response_current = value
    if does_raise is False:
        assert instance.response_current == value


MATCH_00700 = r"RestSend\.response:\s+"
MATCH_00700 += r"response must be a dict\.\s+"
MATCH_00700 += r"Got type.*,\s+"
MATCH_00700 += r"Value:\s+.*\."


@pytest.mark.parametrize(
    "value, does_raise, expected",
    [
        (10, True, pytest.raises(TypeError, match=MATCH_00700)),
        ([10], True, pytest.raises(TypeError, match=MATCH_00700)),
        ({10}, True, pytest.raises(TypeError, match=MATCH_00700)),
        ("FOO", True, pytest.raises(TypeError, match=MATCH_00700)),
        (None, True, pytest.raises(TypeError, match=MATCH_00700)),
        (False, True, pytest.raises(TypeError, match=MATCH_00700)),
        (True, True, pytest.raises(TypeError, match=MATCH_00700)),
        ({"RESULT_CODE": 200}, False, does_not_raise()),
    ],
)
def test_rest_send_v2_00700(value, does_raise, expected) -> None:
    """
    ### Classes and Methods
    -   RestSend()
            -   response.setter

    ### Summary
    Verify ``response.setter`` raises ``TypeError``
    when set to inappropriate types, and does not raise
    when set to dict.

    ### Setup - Code
    -   RestSend() is initialized.

    ### Setup - Data
    None

    ### Trigger
    -   RestSend().response is reset using various types.

    ### Expected Result
    -   ``response`` raises TypeError for non-dict inputs.
    -   ``response`` accepts dict values.
    -   ``response`` returns a list of dict in the happy path.
    """
    with does_not_raise():
        instance = RestSend(PARAMS)

    with expected:
        instance.response = value
    if does_raise is False:
        assert instance.response == [value]


MATCH_00800 = r"RestSend\.result_current:\s+"
MATCH_00800 += r"result_current must be a dict\.\s+"
MATCH_00800 += r"Got.*\."


@pytest.mark.parametrize(
    "value, does_raise, expected",
    [
        (10, True, pytest.raises(TypeError, match=MATCH_00800)),
        ([10], True, pytest.raises(TypeError, match=MATCH_00800)),
        ({10}, True, pytest.raises(TypeError, match=MATCH_00800)),
        ("FOO", True, pytest.raises(TypeError, match=MATCH_00800)),
        (None, True, pytest.raises(TypeError, match=MATCH_00800)),
        (False, True, pytest.raises(TypeError, match=MATCH_00800)),
        (True, True, pytest.raises(TypeError, match=MATCH_00800)),
        ({"failed": False}, False, does_not_raise()),
    ],
)
def test_rest_send_v2_00800(value, does_raise, expected) -> None:
    """
    ### Classes and Methods
    -   RestSend()
            -   result_current.setter

    ### Summary
    Verify ``result_current.setter`` raises ``TypeError``
    when set to inappropriate types, and does not raise
    when set to dict.

    ### Setup - Code
    -   RestSend() is initialized.

    ### Setup - Data
    None

    ### Trigger
    -   RestSend().result_current is reset using various types.

    ### Expected Result
    -   ``result_current`` raises TypeError for non-dict inputs.
    -   ``result_current`` accepts dict values.
    """
    with does_not_raise():
        instance = RestSend(PARAMS)

    with expected:
        instance.result_current = value
    if does_raise is False:
        assert instance.result_current == value


MATCH_00900 = r"RestSend\.result:\s+"
MATCH_00900 += r"result must be a dict\.\s+"
MATCH_00900 += r"Got type.*,\s+"
MATCH_00900 += r"Value:\s+.*\."


@pytest.mark.parametrize(
    "value, does_raise, expected",
    [
        (10, True, pytest.raises(TypeError, match=MATCH_00900)),
        ([10], True, pytest.raises(TypeError, match=MATCH_00900)),
        ({10}, True, pytest.raises(TypeError, match=MATCH_00900)),
        ("FOO", True, pytest.raises(TypeError, match=MATCH_00900)),
        (None, True, pytest.raises(TypeError, match=MATCH_00900)),
        (False, True, pytest.raises(TypeError, match=MATCH_00900)),
        (True, True, pytest.raises(TypeError, match=MATCH_00900)),
        ({"RESULT_CODE": 200}, False, does_not_raise()),
    ],
)
def test_rest_send_v2_00900(value, does_raise, expected) -> None:
    """
    ### Classes and Methods
    -   RestSend()
            -   result.setter

    ### Summary
    Verify ``result.setter`` raises ``TypeError``
    when set to inappropriate types, and does not raise
    when set to dict.

    ### Setup - Code
    -   RestSend() is initialized.

    ### Setup - Data
    None

    ### Trigger
    -   RestSend().result is reset using various types.

    ### Expected Result
    -   ``result`` raises TypeError for non-dict inputs.
    -   ``result`` accepts dict values.
    -   ``result`` returns a list of dict in the happy path.
    """
    with does_not_raise():
        instance = RestSend(PARAMS)

    with expected:
        instance.result = value
    if does_raise is False:
        assert instance.result == [value]
