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

    match = r"RestSend\._verify_commit_parameters:\s+"
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

    match = r"RestSend\._verify_commit_parameters:\s+"
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

    match = r"RestSend\._verify_commit_parameters:\s+"
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

    match = r"RestSend\._verify_commit_parameters:\s+"
    match += r"verb must be set before calling commit\(\)."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_rest_send_v2_00200() -> None:
    """
    ### Classes and Methods
    -   RestSend()
            -   commit_check_mode()
            -   commit()

    ### Summary
    Verify ``commit_check_mode()`` happy path.

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
    -   RestSend().commit() re-raises ``ValueError``.
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
