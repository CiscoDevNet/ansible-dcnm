# Copyright (c) 2020-2024 Cisco and/or its affiliates.
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

from __future__ import absolute_import, division, print_function

from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.common.controller_version import \
    ControllerVersion

from .fixture import load_fixture

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

"""
controller_version: 12
description: Verify functionality of ControllerVersion
"""


patch_module_utils = "ansible_collections.cisco.dcnm.plugins.module_utils."
patch_common = patch_module_utils + "common."

dcnm_send_version = patch_common + "controller_version.dcnm_send"


def responses_controller_version(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_ControllerVersion"
    response = load_fixture(response_file).get(key)
    print(f"responses_controller_version: {key} : {response}")
    return response


class MockAnsibleModule:
    """
    Mock the AnsibleModule class
    """

    params = {}

    def fail_json(msg) -> AnsibleFailJson:
        """
        mock the fail_json method
        """
        raise AnsibleFailJson(msg)


@pytest.fixture
def controller_version():
    return ControllerVersion(MockAnsibleModule)


def test_common_version_00001(controller_version) -> None:
    """
    Properties are initialized to expected values
    """
    controller_version._init_properties()
    assert isinstance(controller_version.properties, dict)
    assert controller_version.properties.get("response_data") == None
    assert controller_version.properties.get("response") == None
    assert controller_version.properties.get("result") == None


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
    Function description:

    ControllerVersion.dev returns:
        - True if the controller is a development version
        - False if the controller is not a development version
        - None otherwise

    Expectations:

    1. ControllerVersion.dev returns above values given corresponding responses

    Expected results:

    1. test_common_version_00002a == False
    2. test_common_version_00002b == True
    3. test_common_version_00002c == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    controller_version.refresh()
    assert controller_version.dev == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_common_version_00003a", "EASYFABRIC"),
        ("test_common_version_00003b", None),
    ],
)
def test_common_version_00003(monkeypatch, controller_version, key, expected) -> None:
    """
    Description:

    ControllerVersion.install returns:
        - Value of controller response "install" key, if present
        - None, if controller response "install" key is missing

    Expectations:

    1.  ControllerVersion.install returns above values given
        corresponding responses

    Expected results:

    1. test_common_version_00003a == "EASYFABRIC"
    2. test_common_version_00003b == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    controller_version.refresh()
    assert controller_version.install == expected


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
    Function description:

    ControllerVersion.is_ha_enabled returns:
        - True, if controller response "isHaEnabled" key == "true"
        - False, if controller response "isHaEnabled" key == "false"
        - None, if controller response "isHaEnabled" key is missing

    Expectations:

    1. install returns above values given corresponding responses

    Expected results:

    1. test_common_version_00004a == True
    2. test_common_version_00004b == False
    3. test_common_version_00004c == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    controller_version.refresh()
    assert controller_version.is_ha_enabled == expected


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
    Function description:

    ControllerVersion.is_media_controller returns:
        - True, if controller response "isMediaController" key == "true"
        - False, if controller response "isMediaController" key == "false"
        - None, if controller response "isMediaController" key is missing

    Expectations:

    1.  ControllerVersion.is_media_controller returns above values
        given corresponding responses

    Expected results:

    1. test_common_version_00005a == True
    2. test_common_version_00005b == False
    3. test_common_version_00005c == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    controller_version.refresh()
    assert controller_version.is_media_controller == expected


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
    Function description:

    ControllerVersion.is_ha_enabled returns:
        - True, if NDFC response "is_upgrade_inprogress" key == "true"
        - False, if NDFC response "is_upgrade_inprogress" key == "false"
        - None, if NDFC response "is_upgrade_inprogress" key is missing

    Expectations:

    1.  ControllerVersion.is_upgrade_inprogress returns above values
        given corresponding responses

    Expected results:

    1. test_common_version_00006a == True
    2. test_common_version_00006b == False
    3. test_common_version_00006c == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    controller_version.refresh()
    assert controller_version.is_upgrade_inprogress == expected


def test_common_version_00007(monkeypatch, controller_version) -> None:
    """
    Function description:

    ControllerVersion.response_data returns the "DATA" key in the
    NDFC response, which is a dictionary of key-value pairs.
    If the "DATA" key is absent, fail_json is called.

    Expectations:

    1.  ControllerVersion.response_data will return a dictionary of key-value
        pairs

    Expected results:

    1. test_common_version_00007a, ControllerVersion.response_data == type(dict)
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        key = "test_common_version_00007a"
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    controller_version.refresh()
    assert isinstance(controller_version.response_data, dict)


def test_common_version_00008(monkeypatch, controller_version) -> None:
    """
    Function description:

    See: test_response_data_present

    Expectations:

    1.  fail_json is called if the "DATA" key is absent

    Expected results:

    1. fail_json is called
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        key = "test_common_version_00008a"
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    with pytest.raises(AnsibleFailJson):
        controller_version.refresh()


def test_common_version_00009(monkeypatch, controller_version) -> None:
    """
    Function description:

    ControllerVersion.result returns the result of its superclass
    method ImageUpgradeCommon._handle_response()

    Expectations:

    1.  For a 200 response with "message" key == "OK",
        ControllerVersion.result == {'found': True, 'success': True}

    Expected results:

    1. ControllerVersion_result_200 == {'found': True, 'success': True}
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        key = "test_common_version_00009a"
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    controller_version.refresh()
    assert controller_version.result == {"found": True, "success": True}


def test_common_version_00010(monkeypatch, controller_version) -> None:
    """
    Function description:

    See: test_result_200

    Expectations:

    1.  For a 404 response with "message" key == "Not Found",
        ControllerVersion.result == {'found': False, 'success': True}
        and ControllerVersion.refresh() calls fail_json

    Expected results:

    1. fail_json is called
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        key = "test_common_version_00010a"
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    with pytest.raises(AnsibleFailJson):
        controller_version.refresh()


def test_common_version_00011(monkeypatch, controller_version) -> None:
    """
    Function description:

    See: test_result_200

    Expectations:

    1.  For a 500 response with any "message" key value,
        ControllerVersion.result == {'found': False, 'success': False}
        and ControllerVersion.refresh() calls fail_json

    Expected results:

    1. fail_json is called
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        key = "test_common_version_00011a"
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    with pytest.raises(AnsibleFailJson):
        controller_version.refresh()


@pytest.mark.parametrize(
    "key, expected",
    [("test_common_version_00012a", "LAN"), ("test_common_version_00012b", None)],
)
def test_common_version_00012(monkeypatch, controller_version, key, expected) -> None:
    """
    Function description:

    ControllerVersion.mode returns:
        - If controller response "mode" key is present, its value
        - If controller response "mode" key is not present, None

    Expectations:

    1.  ControllerVersion.mode returns above values
        given corresponding responses

    Expected results:

    1. test_common_version_00012a == "LAN"
    2. test_common_version_00012b == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    controller_version.refresh()
    assert controller_version.mode == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_common_version_00013a", "foo-uuid"),
        ("test_common_version_00013b", None),
    ],
)
def test_common_version_00013(monkeypatch, controller_version, key, expected) -> None:
    """
    Function description:

    ControllerVersion.uuid returns:
        - If controller response "uuid" key is present, its value
        - If controller response "uuid" key is not present, None

    Expectations:

    1.  ControllerVersion.uuid returns above values
        given corresponding responses

    Expected results:

    1. test_common_version_00013a == "foo-uuid"
    2. test_common_version_00013b == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    controller_version.refresh()
    assert controller_version.uuid == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_common_version_00014a", "12.1.3b"),
        ("test_common_version_00014b", None),
    ],
)
def test_common_version_00014(monkeypatch, controller_version, key, expected) -> None:
    """
    Function description:

    ControllerVersion.version returns:
        - If controller response "version" key is present, its value
        - If controller response "version" key is not present, None

    Expectations:

    1.  ControllerVersion.version returns above values
        given corresponding responses

    Expected results:

    1. test_common_version_00014a == "12.1.3b"
    2. test_common_version_00014b == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    controller_version.refresh()
    assert controller_version.version == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_common_version_00015a", "12"),
        ("test_common_version_00015b", None),
    ],
)
def test_common_version_00015(monkeypatch, controller_version, key, expected) -> None:
    """
    Function description:

    version_major returns the major version of NDFC
    It derives this from the "version" key in the NDFC response
    by splitting the string on "." and returning the first element

    ControllerVersion.version_major returns:
        - If controller response "version" key is present, the major version
        - If controller response "version" key is not present, None

    Expectations:

    1.  ControllerVersion.version_major returns above values
        given corresponding responses

    Expected results:

    1. test_common_version_00015a == "12"
    2. test_common_version_00015b == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    controller_version.refresh()
    assert controller_version.version_major == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_common_version_00016a", "1"),
        ("test_common_version_00016b", None),
    ],
)
def test_common_version_00016(monkeypatch, controller_version, key, expected) -> None:
    """
    Function description:

    version_minor returns the minor version of NDFC
    It derives this from the "version" key in the NDFC response
    by splitting the string on "." and returning the second element

    ControllerVersion.version_minor returns:
        - If controller response "version" key is present, the minor version
        - If controller response "version" key is not present, None

    Expectations:

    1.  ControllerVersion.version_minor returns above values
        given corresponding responses

    Expected results:

    1. test_common_version_00016a == "1"
    2. test_common_version_00016b == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    controller_version.refresh()
    assert controller_version.version_minor == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_common_version_00017a", "3b"),
        ("test_common_version_00017b", None),
    ],
)
def test_common_version_00017(monkeypatch, controller_version, key, expected) -> None:
    """
    Function description:

    version_patch returns the patch version of NDFC
    It derives this from the "version" key in the NDFC response
    by splitting the string on "." and returning the third element

    ControllerVersion.version_patch returns:
        - If controller response "version" key is present, the patch version
        - If controller response "version" key is not present, None

    Expectations:

    1.  ControllerVersion.version_patch returns above values
        given corresponding responses

    Expected results:

    1. test_common_version_00017a == "3b"
    2. test_common_version_00017b == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    controller_version.refresh()
    assert controller_version.version_patch == expected
