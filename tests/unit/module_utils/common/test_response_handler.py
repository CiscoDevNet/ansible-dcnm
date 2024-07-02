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
# pylint: disable=unused-import
# pylint: disable=redefined-outer-name
# pylint: disable=protected-access
# pylint: disable=unused-argument
# pylint: disable=invalid-name

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import copy
import inspect

import pytest
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    does_not_raise, response_handler_fixture, responses_response_handler)


def test_response_handler_00010(response_handler) -> None:
    """
    Classes and Methods
    - ResponseHandler()
        - __init__()

    Summary
    -   Verify class is instantiated without raising an exception
    -   Verify class properties are set as expected

    """
    with does_not_raise():
        instance = response_handler
    assert instance._response is None
    assert instance._result is None
    assert instance.return_codes_success == {200, 404}
    assert instance.valid_verbs == {"DELETE", "GET", "POST", "PUT"}


def test_response_handler_00020(response_handler) -> None:
    """
    Classes and Methods
    - ResponseHandler()
        - __init__()
        - verb.setter

    Summary
    -   Verify ``ValueError`` is raised when setting an invalid verb

    """
    with does_not_raise():
        instance = response_handler
    match = r"ResponseHandler\.verb:\s+"
    match += r"verb must be one of DELETE, GET, POST, PUT\.\s+"
    match += r"Got INVALID\."
    with pytest.raises(ValueError, match=match):
        instance.verb = "INVALID"


def test_response_handler_00030(response_handler) -> None:
    """
    Classes and Methods
    - ResponseHandler()
        - __init__()
        - response.setter

    Summary
    -   Verify ``TypeError`` is raised when response is not a dict.

    """
    with does_not_raise():
        instance = response_handler
    match = r"ResponseHandler\.response:\s+"
    match += r"ResponseHandler\.response must be a dict\.\s+"
    match += r"Got INVALID\."
    with pytest.raises(TypeError, match=match):
        instance.response = "INVALID"


def test_response_handler_00031(response_handler) -> None:
    """
    Classes and Methods
    - ResponseHandler()
        - __init__()
        - response.setter

    Summary
    -   Verify ``ValueError`` is raised when response is missing
        the MESSAGE key.

    """
    with does_not_raise():
        instance = response_handler
    match = r"ResponseHandler\.response:\s+"
    match += r"response must have a MESSAGE key. Got:\s+"
    with pytest.raises(ValueError, match=match):
        instance.response = {"RETURN_CODE": 200}


def test_response_handler_00032(response_handler) -> None:
    """
    Classes and Methods
    - ResponseHandler()
        - __init__()
        - response.setter

    Summary
    -   Verify ``ValueError`` is raised when response is missing
        the RETURN_CODE key.

    """
    with does_not_raise():
        instance = response_handler
    match = r"ResponseHandler\.response:\s+"
    match += r"response must have a RETURN_CODE key. Got:\s+"
    with pytest.raises(ValueError, match=match):
        instance.response = {"MESSAGE": "OK"}


def test_response_handler_00040(response_handler) -> None:
    """
    Classes and Methods
    - ResponseHandler()
        - __init__()
        - verb.setter
        - response.setter
        - commit()
        - _handle_response()
        - _get_response()
        - result.getter

    Summary
    -   Verify ResponseHandler() behavior for:
        -   MESSAGE: "Not Found"
        -   METHOD: GET
        -   RETURN_CODE: 404

    Test
    - Verify ``ValueError`` is not raised
    - Verify ``result`` values are as expected
    """
    key = "test_response_handler_00040a"
    response = responses_response_handler(key)
    with does_not_raise():
        instance = response_handler
        instance.verb = response.get("METHOD", None)
        instance.response = response
        instance.commit()
        result = instance.result
    assert result.get("found") is False
    assert result.get("success") is True


def test_response_handler_00041(response_handler) -> None:
    """
    Classes and Methods
    - ResponseHandler()
        - __init__()
        - verb.setter
        - response.setter
        - commit()
        - _handle_response()
        - _get_response()
        - result.getter

    Summary
    -   Verify ResponseHandler() behavior for:
        -   MESSAGE: don't care
        -   METHOD: GET
        -   RETURN_CODE: 500 (not in {200, 404})

    Test
    - Verify ``ValueError`` is not raised
    - Verify ``result`` values are as expected
    """
    key = "test_response_handler_00041a"
    response = responses_response_handler(key)
    with does_not_raise():
        instance = response_handler
        instance.verb = response.get("METHOD", None)
        instance.response = response
        instance.commit()
        result = instance.result
    assert result.get("found") is False
    assert result.get("success") is False


def test_response_handler_00042(response_handler) -> None:
    """
    Classes and Methods
    - ResponseHandler()
        - __init__()
        - verb.setter
        - response.setter
        - commit()
        - _handle_response()
        - _get_response()
        - result.getter

    Summary
    -   Verify ResponseHandler() behavior for:
        -   MESSAGE: "ERROR" (!= "OK")
        -   METHOD: GET
        -   RETURN_CODE: 200 (don't care)

    Test
    - Verify ``ValueError`` is not raised
    - Verify ``result`` values are as expected
    """
    key = "test_response_handler_00042a"
    response = responses_response_handler(key)
    with does_not_raise():
        instance = response_handler
        instance.verb = response.get("METHOD", None)
        instance.response = response
        instance.commit()
        result = instance.result
    assert result.get("found") is False
    assert result.get("success") is False


def test_response_handler_00043(response_handler) -> None:
    """
    Classes and Methods
    - ResponseHandler()
        - __init__()
        - verb.setter
        - response.setter
        - commit()
        - _handle_response()
        - _get_response()
        - result.getter

    Summary
    -   Verify ResponseHandler() behavior for:
        -   MESSAGE: "OK"
        -   METHOD: GET
        -   RETURN_CODE: 200

    """
    key = "test_response_handler_00043a"
    response = responses_response_handler(key)
    with does_not_raise():
        instance = response_handler
        instance.verb = response.get("METHOD", None)
        instance.response = response
        instance.commit()
        result = instance.result
    assert result.get("found") is True
    assert result.get("success") is True


def test_response_handler_00050(response_handler) -> None:
    """
    Classes and Methods
    - ResponseHandler()
        - __init__()
        - verb.setter
        - response.setter
        - commit()
        - _handle_response()
        - _post_put_delete_response()
        - result.getter

    Summary
    -   Verify ResponseHandler() behavior for:
        -   ERROR: key is present
        -   MESSAGE: "OK" (don't care)
        -   METHOD: POST
        -   RETURN_CODE: 200 (don't care)

    """
    key = "test_response_handler_00050a"
    response = responses_response_handler(key)
    with does_not_raise():
        instance = response_handler
        instance.verb = response.get("METHOD", None)
        instance.response = response
        instance.commit()
        result = instance.result
    assert result.get("changed") is False
    assert result.get("success") is False


def test_response_handler_00051(response_handler) -> None:
    """
    Classes and Methods
    - ResponseHandler()
        - __init__()
        - verb.setter
        - response.setter
        - commit()
        - _handle_response()
        - _post_put_delete_response()
        - result.getter

    Summary
    -   Verify ResponseHandler() behavior for:
        -   ERROR: not present (don't care)
        -   MESSAGE: "NOK" (!= OK)
        -   METHOD: POST
        -   RETURN_CODE: 200 (don't care)

    """
    key = "test_response_handler_00051a"
    response = responses_response_handler(key)
    with does_not_raise():
        instance = response_handler
        instance.verb = response.get("METHOD", None)
        instance.response = response
        instance.commit()
        result = instance.result
    assert result.get("changed") is False
    assert result.get("success") is False


def test_response_handler_00052(response_handler) -> None:
    """
    Classes and Methods
    - ResponseHandler()
        - __init__()
        - verb.setter
        - response.setter
        - commit()
        - _handle_response()
        - _post_put_delete_response()
        - result.getter

    Summary
    -   Verify ResponseHandler() behavior for:
        -   ERROR: not present
        -   MESSAGE: "OK"
        -   METHOD: POST
        -   RETURN_CODE: don't care

    """
    key = "test_response_handler_00052a"
    response = responses_response_handler(key)
    with does_not_raise():
        instance = response_handler
        instance.verb = response.get("METHOD", None)
        instance.response = response
        instance.commit()
        result = instance.result
    assert result.get("changed") is True
    assert result.get("success") is True


def test_response_handler_00060(response_handler) -> None:
    """
    Classes and Methods
    - ResponseHandler()
        - __init__()
        - commit()

    Summary
    -   Verify ``ValueError`` is raised when commit() is called
        without first setting verb.
    """
    with does_not_raise():
        instance = response_handler
        instance.response = {"MESSAGE": "OK", "RETURN_CODE": 200}
    match = r"ResponseHandler\.commit:\s+"
    match += r"ResponseHandler\.verb must be set prior to calling\s+"
    match += r"ResponseHandler\.commit"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_response_handler_00070(response_handler) -> None:
    """
    Classes and Methods
    - ResponseHandler()
        - __init__()
        - commit()

    Summary
    -   Verify ``ValueError`` is raised when commit() is called
        without first setting response.
    """
    with does_not_raise():
        instance = response_handler
        instance.verb = "GET"
    match = r"ResponseHandler\.commit:\s+"
    match += r"ResponseHandler\.response must be set prior to calling\s+"
    match += r"ResponseHandler\.commit"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_response_handler_00080(response_handler) -> None:
    """
    Classes and Methods
    - ResponseHandler()
        - __init__()
        - result.setter

    Summary
    -   Verify ``TypeError`` is raised when result is not a dict.

    """
    with does_not_raise():
        instance = response_handler
    match = r"ResponseHandler\.result:\s+"
    match += r"ResponseHandler\.result must be a dict\.\s+"
    match += r"Got INVALID\."
    with pytest.raises(TypeError, match=match):
        instance.result = "INVALID"
