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

from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson

from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import (
    controller_version_fixture, responses_controller_version)

PATCH_MODULE_UTILS = "ansible_collections.cisco.dcnm.plugins.module_utils."
PATCH_COMMON = PATCH_MODULE_UTILS + "common."
DCNM_SEND_VERSION = PATCH_COMMON + "controller_version.dcnm_send"


def test_common_version_00001(controller_version) -> None:
    """
    Function
    - __init__

    Test
    - Class properties are initialized to expected values
    """
    instance = controller_version
    assert isinstance(instance.properties, dict)
    assert instance.properties.get("response_data") is None
    assert instance.properties.get("response") is None
    assert instance.properties.get("result") is None


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_common_version_00002a", False),
        ("test_common_version_00002b", True),
        ("test_common_version_00002c", None),
    ],
)
def test_common_version_00002(monkeypatch, controller_version, key, expected) -> None:
    """
    Function
    - refresh
    - dev

    Test
    - dev returns True when the controller is a development version
    - dev returns False when the controller is not a development version
    - dev returns None otherwise
    """

    def mock_dcnm_send_version(*args) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(DCNM_SEND_VERSION, mock_dcnm_send_version)

    instance = controller_version
    instance.refresh()
    assert instance.dev == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_common_version_00003a", "EASYFABRIC"),
        ("test_common_version_00003b", None),
    ],
)
def test_common_version_00003(monkeypatch, controller_version, key, expected) -> None:
    """
    Function
    - refresh
    - install

    Test
    - install returns expected values

    Description
    install returns:
    - Value of the "install" key in the controller response, if present
    - None, if the "install" key is absent from the controller response

    Expected results:

    1. test_common_version_00003a == "EASYFABRIC"
    2. test_common_version_00003b is None
    """

    def mock_dcnm_send_version(*args) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(DCNM_SEND_VERSION, mock_dcnm_send_version)

    instance = controller_version
    instance.refresh()
    assert instance.install == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_common_version_00004a", True),
        ("test_common_version_00004b", False),
        ("test_common_version_00004c", None),
    ],
)
def test_common_version_00004(monkeypatch, controller_version, key, expected) -> None:
    """
    Function
    - refresh
    - is_ha_enabled

    Test
    - is_ha_enabled returns expected values

    Description
    is_ha_enabled returns:
    - True, if "isHaEnabled" key in the controller response == "true"
    - False, if "isHaEnabled" key in the controller response == "false"
    - None, if "isHaEnabled" key is absent from the controller response

    Expected results:

    1. test_common_version_00004a is True
    2. test_common_version_00004b is False
    3. test_common_version_00004c is None
    """

    def mock_dcnm_send_version(*args) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(DCNM_SEND_VERSION, mock_dcnm_send_version)

    instance = controller_version
    instance.refresh()
    assert instance.is_ha_enabled == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_common_version_00005a", True),
        ("test_common_version_00005b", False),
        ("test_common_version_00005c", None),
    ],
)
def test_common_version_00005(monkeypatch, controller_version, key, expected) -> None:
    """
    Function
    - refresh
    - is_media_controller

    Test
    - is_media_controller returns expected values

    Description
    is_media_controller returns:
    - True, if "isMediaController" key in the controller response == "true"
    - False, if "isMediaController" key in the controller response == "false"
    - None, if "isMediaController" key is absent from the controller response

    Expected results:

    1. test_common_version_00005a is True
    2. test_common_version_00005b is False
    3. test_common_version_00005c is None
    """

    def mock_dcnm_send_version(*args) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(DCNM_SEND_VERSION, mock_dcnm_send_version)

    instance = controller_version
    instance.refresh()
    assert instance.is_media_controller == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_common_version_00006a", True),
        ("test_common_version_00006b", False),
        ("test_common_version_00006c", None),
    ],
)
def test_common_version_00006(monkeypatch, controller_version, key, expected) -> None:
    """
    Function
    - refresh
    - is_upgrade_inprogress

    Test
    - is_upgrade_inprogress returns expected values

    Description
    is_upgrade_inprogress returns:
    - True, if "is_upgrade_inprogress" key in the controller response == "true"
    - False, if "is_upgrade_inprogress" key in the controller response == "false"
    - None, if "is_upgrade_inprogress" key is absent from the controller response

    Expected results:

    1. test_common_version_00006a is True
    2. test_common_version_00006b is False
    3. test_common_version_00006c is None
    """

    def mock_dcnm_send_version(*args) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(DCNM_SEND_VERSION, mock_dcnm_send_version)

    instance = controller_version
    instance.refresh()
    assert instance.is_upgrade_inprogress == expected


def test_common_version_00007(monkeypatch, controller_version) -> None:
    """
    Function
    - refresh
    - response_data

    Test
    - response_data returns the "DATA" key in the controller response

    Description
    response_data returns the "DATA" key in the controller response,
    which is a dictionary of key-value pairs.
    fail_json is called if the "DATA" key is absent.

    Expected results:

    1. test_common_version_00007a, ControllerVersion.response_data == type(dict)
    """

    def mock_dcnm_send_version(*args) -> Dict[str, Any]:
        key = "test_common_version_00007a"
        return responses_controller_version(key)

    monkeypatch.setattr(DCNM_SEND_VERSION, mock_dcnm_send_version)

    instance = controller_version
    instance.refresh()
    assert isinstance(instance.response_data, dict)


def test_common_version_00008(monkeypatch, controller_version) -> None:
    """
    Function
    - refresh

    Test
    - fail_json is called because the "DATA" key is absent

    Description
    response_data returns the "DATA" key in the controller response,
    which is a dictionary of key-value pairs.
    fail_json is called if the "DATA" key is absent.
    """

    def mock_dcnm_send_version(*args) -> Dict[str, Any]:
        key = "test_common_version_00008a"
        return responses_controller_version(key)

    monkeypatch.setattr(DCNM_SEND_VERSION, mock_dcnm_send_version)

    instance = controller_version
    with pytest.raises(AnsibleFailJson):
        instance.refresh()


def test_common_version_00009(monkeypatch, controller_version) -> None:
    """
    Function
    - refresh
    - result

    Test
    - result returns expected values

    Description
    result returns the result of its superclass
    method ImageUpgradeCommon._handle_response()

    Expected results:

    -   Since a 200 response with "message" key == "OK" is received
        we expect result to return {'found': True, 'success': True}
    """

    def mock_dcnm_send_version(*args) -> Dict[str, Any]:
        key = "test_common_version_00009a"
        return responses_controller_version(key)

    monkeypatch.setattr(DCNM_SEND_VERSION, mock_dcnm_send_version)

    instance = controller_version
    instance.refresh()
    assert instance.result == {"found": True, "success": True}


def test_common_version_00010(monkeypatch, controller_version) -> None:
    """
    Function
    - refresh
    - result

    Test
    - result returns expected values

    Description
    result returns the result of its superclass
    method ImageUpgradeCommon._handle_response()

    Expected results:

    -   Since a 404 response with "message" key == "Not Found" is received
        we expect result to return {'found': False, 'success': True}
    """

    def mock_dcnm_send_version(*args) -> Dict[str, Any]:
        key = "test_common_version_00010a"
        return responses_controller_version(key)

    monkeypatch.setattr(DCNM_SEND_VERSION, mock_dcnm_send_version)

    instance = controller_version
    with pytest.raises(AnsibleFailJson):
        instance.refresh()
    assert instance.result == {"found": False, "success": True}


def test_common_version_00011(monkeypatch, controller_version) -> None:
    """
    Function
    - refresh
    - result

    Test
    - result returns expected values
    - fail_json is called

    Description
    result returns the result of its superclass
    method ImageUpgradeCommon._handle_response()

    Expected results:

    -   Since a 500 response is received (MESSAGE key ignored)
        we expect result to return {'found': False, 'success': False}
    """

    def mock_dcnm_send_version(*args) -> Dict[str, Any]:
        key = "test_common_version_00011a"
        return responses_controller_version(key)

    monkeypatch.setattr(DCNM_SEND_VERSION, mock_dcnm_send_version)

    instance = controller_version
    with pytest.raises(AnsibleFailJson):
        instance.refresh()
    assert instance.result == {"found": False, "success": False}


@pytest.mark.parametrize(
    "key, expected",
    [("test_common_version_00012a", "LAN"), ("test_common_version_00012b", None)],
)
def test_common_version_00012(monkeypatch, controller_version, key, expected) -> None:
    """
    Function
    - refresh
    - mode

    Test
    - mode returns expected values

    Description
    mode returns:
    - its value, if the "mode" key is present in the controller response
    - None, if the "mode" key is absent from the controller response

    Expected results:

    1. test_common_version_00012a == "LAN"
    2. test_common_version_00012b is None
    """

    def mock_dcnm_send_version(*args) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(DCNM_SEND_VERSION, mock_dcnm_send_version)

    instance = controller_version
    instance.refresh()
    assert instance.mode == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_common_version_00013a", "foo-uuid"),
        ("test_common_version_00013b", None),
    ],
)
def test_common_version_00013(monkeypatch, controller_version, key, expected) -> None:
    """
    Function
    - refresh
    - uuid

    Test
    - uuid returns expected values

    Description
    uuid returns:
    - its value, if the "uuid" key is present in the controller response
    - None, if the "uuid" key is absent from the controller response

    Expected results:

    1. test_common_version_00013a == "foo-uuid"
    2. test_common_version_00013b is None
    """

    def mock_dcnm_send_version(*args) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(DCNM_SEND_VERSION, mock_dcnm_send_version)

    instance = controller_version
    instance.refresh()
    assert instance.uuid == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_common_version_00014a", "12.1.3b"),
        ("test_common_version_00014b", None),
    ],
)
def test_common_version_00014(monkeypatch, controller_version, key, expected) -> None:
    """
    Function
    - refresh
    - version

    Test
    - version returns expected values

    Description
    mode returns:
    - its value, if the "version" key is present in the controller response
    - None, if the "version" key is absent from the controller response

    Expected results:

    1. test_common_version_00014a == "12.1.3b"
    2. test_common_version_00014b is None
    """

    def mock_dcnm_send_version(*args) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(DCNM_SEND_VERSION, mock_dcnm_send_version)

    instance = controller_version
    instance.refresh()
    assert instance.version == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_common_version_00015a", "12"),
        ("test_common_version_00015b", None),
    ],
)
def test_common_version_00015(monkeypatch, controller_version, key, expected) -> None:
    """
    Function
    - refresh
    - version_major

    Test
    - version_major returns expected values

    Description
    version_major returns the major version of the controller
    It derives this from the "version" key in the controller response
    by splitting the string on "." and returning the first element

    Expected results:

    1. test_common_version_00015a == "12"
    2. test_common_version_00015b is None
    """

    def mock_dcnm_send_version(*args) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(DCNM_SEND_VERSION, mock_dcnm_send_version)

    instance = controller_version
    instance.refresh()
    assert instance.version_major == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_common_version_00016a", "1"),
        ("test_common_version_00016b", None),
    ],
)
def test_common_version_00016(monkeypatch, controller_version, key, expected) -> None:
    """
    Function
    - refresh
    - version_minor

    Test
    - version_minor returns expected values

    Description
    version_minor returns the minor version of the controller
    It derives this from the "version" key in the controller response
    by splitting the string on "." and returning the second element

    Expected results:

    1. test_common_version_00016a == "1"
    2. test_common_version_00016b is None
    """

    def mock_dcnm_send_version(*args) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(DCNM_SEND_VERSION, mock_dcnm_send_version)

    instance = controller_version
    instance.refresh()
    assert instance.version_minor == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_common_version_00017a", "3b"),
        ("test_common_version_00017b", None),
    ],
)
def test_common_version_00017(monkeypatch, controller_version, key, expected) -> None:
    """
    Function
    - refresh
    - version_patch

    Test
    - version_patch returns expected values

    Description
    version_patch returns the patch version of the controller
    It derives this from the "version" key in the controller response
    by splitting the string on "." and returning the third element

    Expected results:

    1. test_common_version_00017a == "3b"
    2. test_common_version_00017b is None
    """

    def mock_dcnm_send_version(*args) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(DCNM_SEND_VERSION, mock_dcnm_send_version)

    instance = controller_version
    instance.refresh()
    assert instance.version_patch == expected
