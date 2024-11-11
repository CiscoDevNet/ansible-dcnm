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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_file import \
    Sender
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import (
    MockAnsibleModule, ResponseGenerator, controller_version_fixture,
    does_not_raise, params, responses_ep_version)


def test_controller_version_00000(controller_version) -> None:
    """
    ### Classes and Methods

    -   ``ControllerVersion()``
            -   ``__init__``

    ### Test
    -   Class properties are initialized to expected values.
    """
    instance = controller_version
    assert instance.class_name == "ControllerVersion"
    assert instance.conversion.class_name == "ConversionUtils"
    assert instance.ep_version.class_name == "EpVersion"
    assert instance.response_data is None
    assert instance.rest_send is None


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_controller_version_00100a", False),
        ("test_controller_version_00100b", True),
        ("test_controller_version_00100c", None),
    ],
)
def test_controller_version_00100(controller_version, key, expected) -> None:
    """
    ### Classes and Methods

    -   ``ControllerVersion()``
            -   ``refresh``
            -   ``dev``

    ### Test

    -   ``dev`` returns True when the controller is a development version.
    -   ``dev`` returns False when the controller is not a development version.
    -   ``dev`` returns None otherwise.
    """

    def responses():
        yield responses_ep_version(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = controller_version
        instance.rest_send = rest_send
        instance.refresh()
    assert instance.dev == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_controller_version_00110a", "EASYFABRIC"),
        ("test_controller_version_00110b", None),
    ],
)
def test_controller_version_00110(controller_version, key, expected) -> None:
    """
    ### Classes and Methods

    -   ``ControllerVersion()``
            -   ``refresh``
            -   ``install``

    ### Test

    - install returns expected values

    ### Description
    install returns:

    -   Value of the "install" key in the controller response, if present.
    -   None, if the "install" key is absent from the controller response.

    ### Expected result

    1. test_controller_version_00110a == "EASYFABRIC"
    2. test_controller_version_00110b is None
    """

    def responses():
        yield responses_ep_version(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = controller_version
        instance.rest_send = rest_send
        instance.refresh()
    assert instance.install == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_controller_version_00120a", True),
        ("test_controller_version_00120b", False),
        ("test_controller_version_00120c", None),
    ],
)
def test_controller_version_00120(controller_version, key, expected) -> None:
    """
    ### Classes and Methods

    -   ``ControllerVersion()``
            -   ``refresh``
            -   ``is_ha_enabled``

    ### Test

    - is_ha_enabled returns expected values

    ### Description

    ``is_ha_enabled`` returns:

    - True, if "isHaEnabled" key in the controller response == "true".
    - False, if "isHaEnabled" key in the controller response == "false".
    - None, if "isHaEnabled" key is absent from the controller response.

    Expected result

    1. test_controller_version_00120a is True
    2. test_controller_version_00120b is False
    3. test_controller_version_00120c is None
    """

    def responses():
        yield responses_ep_version(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = controller_version
        instance.rest_send = rest_send
        instance.refresh()
    assert instance.is_ha_enabled == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_controller_version_00130a", True),
        ("test_controller_version_00130b", False),
        ("test_controller_version_00130c", None),
    ],
)
def test_controller_version_00130(controller_version, key, expected) -> None:
    """
    ### Classes and Methods

    -   ``ControllerVersion()``
            -   ``refresh``
            -   ``is_media_controller``

    ### Test
    -   ``is_media_controller`` returns expected values.

    ### Description

    ``is_media_controller`` returns:

    -   True, if "isMediaController" key in the controller response == "true".
    -   False, if "isMediaController" key in the controller response == "false".
    -   None, if "isMediaController" key is absent from the controller response.

    ### Expected result

    1.  test_controller_version_00130a is True.
    2.  test_controller_version_00130b is False.
    3.  test_controller_version_00130c is None.
    """

    def responses():
        yield responses_ep_version(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = controller_version
        instance.rest_send = rest_send
        instance.refresh()
    assert instance.is_media_controller == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_controller_version_00140a", True),
        ("test_controller_version_00140b", False),
        ("test_controller_version_00140c", None),
    ],
)
def test_controller_version_00140(controller_version, key, expected) -> None:
    """
    ### Classes and Methods

    -   ``ControllerVersion()``
            -   ``refresh``
            -   ``is_upgrade_inprogress``

    ### Test
    - ``is_upgrade_inprogress`` returns expected values.

    ### Description

    ``is_upgrade_inprogress`` returns:
    -   True, if "is_upgrade_inprogress" key in the controller
        response == "true".
    -   False, if "is_upgrade_inprogress" key in the controller
        response == "false".
    -   None, if "is_upgrade_inprogress" key is absent from the
        controller response.

    ### Expected results

    1.  test_controller_version_00140a is True.
    2.  test_controller_version_00140b is False.
    3.  test_controller_version_00140c is None.
    """

    def responses():
        yield responses_ep_version(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = controller_version
        instance.rest_send = rest_send
        instance.refresh()
    assert instance.is_upgrade_inprogress == expected


def test_controller_version_00150(controller_version) -> None:
    """
    ### Classes and Methods

    -   ``ControllerVersion()``
            -   ``refresh``
            -   ``response_data``

    ### Test

    -   ``response_data`` returns the "DATA" key in the controller response.

    ### Description

    -   ``response_data`` returns the "DATA" key in the controller response,
        which is a dictionary of key-value pairs.
    -   ``ValueError`` is raised if the "DATA" key is absent.

    ### Expected results

    1.  test_controller_version_00150a
        ControllerVersion.response_data == type(dict)
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_version(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = controller_version
        instance.rest_send = rest_send
        instance.refresh()
    assert isinstance(instance.response_data, dict)


def test_controller_version_00160(controller_version) -> None:
    """
    ### Classes and Methods

    -   ``ControllerVersion()``
            -   ``refresh``
            -   ``response_data``

    ### Test

    - ValueError is raised because the "DATA" key is absent

    ### Description
    -   ``response_data`` returns the "DATA" key in the controller response,
        which is a dictionary of key-value pairs.
    -   ``ValueError`` is raised if the "DATA" key is absent.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_version(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = controller_version
        instance.rest_send = rest_send

    match = r"ControllerVersion\.refresh\(\) failed:\s+"
    match += r"response does not contain DATA key\.\s+"
    match += r"Controller response:.*"

    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_controller_version_00170(controller_version) -> None:
    """
    ### Classes and Methods

    -   ``ControllerVersion()``
            -   ``refresh``
    -   ``RestSend``
            -   ``result_current``

    ### Test
    -   RestSend.result_current returns expected values.

    ### Expected results

    -   Since a 200 response with "message" key == "OK" is received
        we expect result to return {'found': True, 'success': True}
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_version(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = controller_version
        instance.rest_send = rest_send
        instance.refresh()
    assert instance.rest_send.result_current == {"found": True, "success": True}


def test_controller_version_00180(controller_version) -> None:
    """
    ### Classes and Methods

    -   ``ControllerVersion()``
            -   ``refresh``
    -   ``RestSend``
            -   ``result_current``

    ### Test
    -   RestSend.result_current returns expected values.

    ### Expected results

    -   Since a 404 response with "message" key == "Not Found" is received
        ``ControllerResponseError`` is raised.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_version(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = controller_version
        instance.rest_send = rest_send

    match = r"ControllerVersion\.refresh:\s+"
    match += r"failed:.*"

    with pytest.raises(ControllerResponseError, match=match):
        instance.refresh()
    assert instance.rest_send.result_current == {"found": False, "success": True}


def test_controller_version_00190(controller_version) -> None:
    """
    ### Classes and Methods

    -   ``ControllerVersion()``
            -   ``refresh``
    -   ``RestSend``
            -   ``result_current``

    ### Test
    -   RestSend.result_current returns expected values.

    ### Expected results

    -   Since a 500 response is received (MESSAGE key ignored)
        we expect result to return {'found': False, 'success': False}
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_version(key)

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
        instance = controller_version
        instance.rest_send = rest_send

    match = r"ControllerVersion\.refresh:\s+"
    match += r"failed:.*"

    with pytest.raises(ControllerResponseError, match=match):
        instance.refresh()
    assert instance.rest_send.result_current == {"found": False, "success": False}


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_controller_version_00200a", "LAN"),
        ("test_controller_version_00200b", None),
    ],
)
def test_controller_version_00200(controller_version, key, expected) -> None:
    """
    ### Classes and Methods

    -   ``ControllerVersion()``
            -   ``refresh``
            -   ``mode``

    ### Test

    -   ``mode`` returns expected values.

    ### Description
    ``mode`` returns:

    -   Its value, if the "mode" key is present in the controller response.
    -   None, if the "mode" key is absent from the controller response.

    ### Expected results

    1. test_controller_version_00200a == "LAN"
    2. test_controller_version_00200b is None
    """

    def responses():
        yield responses_ep_version(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = controller_version
        instance.rest_send = rest_send
        instance.refresh()
    assert instance.mode == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_controller_version_00210a", "foo-uuid"),
        ("test_controller_version_00210b", None),
    ],
)
def test_controller_version_00210(controller_version, key, expected) -> None:
    """
    ### Classes and Methods

    -   ``ControllerVersion()``
            -   ``refresh``
            -   ``uuid``

    ### Test

    -   ``uuid`` returns expected values.

    ### Description

    uuid returns:

    -   Its value, if the "uuid" key is present in the controller response.
    -   None, if the "uuid" key is absent from the controller response.

    ### Expected result

    1. test_controller_version_00210a == "foo-uuid"
    2. test_controller_version_00210b is None
    """

    def responses():
        yield responses_ep_version(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = controller_version
        instance.rest_send = rest_send
        instance.refresh()
    assert instance.uuid == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_controller_version_00220a", "12.1.3b"),
        ("test_controller_version_00220b", None),
    ],
)
def test_controller_version_00220(controller_version, key, expected) -> None:
    """
    ### Classes and Methods

    -   ``ControllerVersion()``
            -   ``refresh``
            -   ``version``

    ### Test

    -   ``version`` returns expected values.

    ### Description
    ``version`` returns:

    -   Its value, if the "version" key is present in the controller response.
    -   None, if the "version" key is absent from the controller response.

    ### Expected result

    1. test_controller_version_00220a == "12.1.3b"
    2. test_controller_version_00220b is None
    """

    def responses():
        yield responses_ep_version(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = controller_version
        instance.rest_send = rest_send
        instance.refresh()
    assert instance.version == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_controller_version_00230a", "12"),
        ("test_controller_version_00230b", None),
    ],
)
def test_controller_version_00230(controller_version, key, expected) -> None:
    """
    ### Classes and Methods

    -   ``ControllerVersion()``
            -   ``refresh``
            -   ``version_major``

    ### Test
    -   ``version_major`` returns expected values.

    ### Description
    ``version_major`` returns the major version of the controller.
    It derives this from the "version" key in the controller response
    by splitting the string on "." and returning the first element.

    ### Expected result

    1. test_controller_version_00230a == "12"
    2. test_controller_version_00230b is None
    """

    def responses():
        yield responses_ep_version(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = controller_version
        instance.rest_send = rest_send
        instance.refresh()
    assert instance.version_major == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_controller_version_00240a", "1"),
        ("test_controller_version_00240b", None),
    ],
)
def test_controller_version_00240(controller_version, key, expected) -> None:
    """
    ### Classes and Methods

    -   ``ControllerVersion()``
            -   ``refresh``
            -   ``version_minor``

    ### Test

    -   ``version_minor`` returns expected values.

    ### Description
    ``version_minor`` returns the minor version of the controller.
    It derives this from the "version" key in the controller response
    by splitting the string on "." and returning the second element.

    ### Expected result

    1. test_controller_version_00240a == "1"
    2. test_controller_version_00240b is None
    """

    def responses():
        yield responses_ep_version(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = controller_version
        instance.rest_send = rest_send
        instance.refresh()
    assert instance.version_minor == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_controller_version_00250a", "3b"),
        ("test_controller_version_00250b", None),
    ],
)
def test_controller_version_00250(controller_version, key, expected) -> None:
    """
    ### Classes and Methods

    -   ``ControllerVersion()``
            -   ``refresh``
            -   ``version_patch``

    ### Test

    -   ``version_patch`` returns expected values.

    ### Description
    ``version_patch`` returns the patch version of the controller.
    It derives this from the "version" key in the controller response
    by splitting the string on "." and returning the third element.

    ### Expected result

    1. test_controller_version_00250a == "3b"
    2. test_controller_version_00250b is None
    """

    def responses():
        yield responses_ep_version(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = controller_version
        instance.rest_send = rest_send
        instance.refresh()
    assert instance.version_patch == expected
