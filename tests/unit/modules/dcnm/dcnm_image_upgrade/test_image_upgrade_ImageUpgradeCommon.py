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

from contextlib import contextmanager
from typing import Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_upgrade_common import \
    ImageUpgradeCommon

from .fixture import load_fixture

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

"""
controller_version: 12
description: Verify functionality of class ImageUpgradeCommon
"""


@contextmanager
def does_not_raise():
    yield


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
def image_upgrade_common():
    return ImageUpgradeCommon(MockAnsibleModule)


def responses_image_upgrade_common(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_ImageUpgradeCommon"
    response = load_fixture(response_file).get(key)
    verb = response.get("METHOD")
    print(f"{key} : {verb} : {response}")
    return {"response": response, "verb": verb}


def test_image_mgmt_image_upgrade_common_00001(image_upgrade_common) -> None:
    """
    Function
    - __init__

    Test
    - fail_json is not called
    - image_upgrade_common.params is a dict
    - image_upgrade_common.debug is False
    - image_upgrade_common.fd is None
    - image_upgrade_common.logfile is /tmp/ansible_dcnm.log
    """
    with does_not_raise():
        image_upgrade_common.__init__(MockAnsibleModule)
    assert image_upgrade_common.params == {}
    assert image_upgrade_common.debug == False
    assert image_upgrade_common.fd == None
    assert image_upgrade_common.logfile == "/tmp/ansible_dcnm.log"


@pytest.mark.parametrize(
    "key, expected",
    [
        (
            "test_image_mgmt_image_upgrade_common_00020a",
            {"success": True, "changed": True},
        ),
        (
            "test_image_mgmt_image_upgrade_common_00020b",
            {"success": False, "changed": False},
        ),
        (
            "test_image_mgmt_image_upgrade_common_00020c",
            {"success": False, "changed": False},
        ),
    ],
)
def test_image_mgmt_image_upgrade_common_00020(
    image_upgrade_common, key, expected
) -> None:
    """
    Function
    - _handle_response

    Test
    - json_fail is not called
    - success and changed are returned as expected for DELETE requests

    Description
    _handle_reponse() calls either _handle_get_reponse if verb is "GET" or
    _handle_post_put_delete_response if verb is "DELETE", "POST", or "PUT"
    """
    data = responses_image_upgrade_common(key)
    with does_not_raise():
        result = image_upgrade_common._handle_response(
            data.get("response"), data.get("verb")
        )
    assert result.get("success") == expected.get("success")
    assert result.get("changed") == expected.get("changed")


@pytest.mark.parametrize(
    "key, expected",
    [
        (
            "test_image_mgmt_image_upgrade_common_00030a",
            {"success": True, "changed": True},
        ),
        (
            "test_image_mgmt_image_upgrade_common_00030b",
            {"success": False, "changed": False},
        ),
        (
            "test_image_mgmt_image_upgrade_common_00030c",
            {"success": False, "changed": False},
        ),
    ],
)
def test_image_mgmt_image_upgrade_common_00030(
    image_upgrade_common, key, expected
) -> None:
    """
    Function
    - _handle_response

    Test
    - json_fail is not called
    - success and changed are returned as expected for POST requests

    Description
    _handle_reponse() calls either _handle_get_reponse if verb is "GET" or
    _handle_post_put_delete_response if verb is "DELETE", "POST", or "PUT"
    """
    data = responses_image_upgrade_common(key)
    with does_not_raise():
        result = image_upgrade_common._handle_response(
            data.get("response"), data.get("verb")
        )
    assert result.get("success") == expected.get("success")
    assert result.get("changed") == expected.get("changed")


@pytest.mark.parametrize(
    "key, expected",
    [
        (
            "test_image_mgmt_image_upgrade_common_00040a",
            {"success": True, "changed": True},
        ),
        (
            "test_image_mgmt_image_upgrade_common_00040b",
            {"success": False, "changed": False},
        ),
        (
            "test_image_mgmt_image_upgrade_common_00040c",
            {"success": False, "changed": False},
        ),
    ],
)
def test_image_mgmt_image_upgrade_common_00040(
    image_upgrade_common, key, expected
) -> None:
    """
    Function
    - _handle_response

    Test
    - json_fail is not called
    - success and changed are returned as expected for PUT requests

    Description
    _handle_reponse() calls either _handle_get_reponse if verb is "GET" or
    _handle_post_put_delete_response if verb is "DELETE", "POST", or "PUT"
    """
    data = responses_image_upgrade_common(key)
    with does_not_raise():
        result = image_upgrade_common._handle_response(
            data.get("response"), data.get("verb")
        )
    assert result.get("success") == expected.get("success")
    assert result.get("changed") == expected.get("changed")


@pytest.mark.parametrize(
    "key, expected",
    [
        (
            "test_image_mgmt_image_upgrade_common_00050a",
            {"success": True, "found": True},
        ),
        (
            "test_image_mgmt_image_upgrade_common_00050b",
            {"success": False, "found": False},
        ),
        (
            "test_image_mgmt_image_upgrade_common_00050c",
            {"success": True, "found": False},
        ),
        (
            "test_image_mgmt_image_upgrade_common_00050d",
            {"success": False, "found": False},
        ),
    ],
)
def test_image_mgmt_image_upgrade_common_00050(
    image_upgrade_common, key, expected
) -> None:
    """
    Function
    - _handle_response

    Test
    - _handle_reponse returns expected values for GET requests
    """
    data = responses_image_upgrade_common(key)
    result = image_upgrade_common._handle_response(
        data.get("response"), data.get("verb")
    )
    assert result.get("success") == expected.get("success")
    assert result.get("changed") == expected.get("changed")


def test_image_mgmt_image_upgrade_common_00060(image_upgrade_common) -> None:
    """
    Function
    - _handle_response

    Test
    - fail_json is called because an unknown request verb is provided
    """
    data = responses_image_upgrade_common("test_image_mgmt_image_upgrade_common_00060a")
    with pytest.raises(AnsibleFailJson, match=r"Unknown request verb \(FOO\)"):
        image_upgrade_common._handle_response(data.get("response"), data.get("verb"))


@pytest.mark.parametrize(
    "key, expected",
    [
        (
            "test_image_mgmt_image_upgrade_common_00070a",
            {"success": True, "found": True},
        ),
        (
            "test_image_mgmt_image_upgrade_common_00070b",
            {"success": False, "found": False},
        ),
        (
            "test_image_mgmt_image_upgrade_common_00070c",
            {"success": True, "found": False},
        ),
        (
            "test_image_mgmt_image_upgrade_common_00070d",
            {"success": False, "found": False},
        ),
    ],
)
def test_image_mgmt_image_upgrade_common_00070(
    image_upgrade_common, key, expected
) -> None:
    """
    Function
    - _handle_get_response

    Test
    - fail_json is not called
    - _handle_get_reponse() returns expected values for GET requests
    """
    data = responses_image_upgrade_common(key)
    with does_not_raise():
        result = image_upgrade_common._handle_get_response(data.get("response"))

    assert result.get("success") == expected.get("success")
    assert result.get("changed") == expected.get("changed")


@pytest.mark.parametrize(
    "key, expected",
    [
        (
            "test_image_mgmt_image_upgrade_common_00080a",
            {"success": True, "changed": True},
        ),
        (
            "test_image_mgmt_image_upgrade_common_00080b",
            {"success": False, "changed": False},
        ),
        (
            "test_image_mgmt_image_upgrade_common_00080c",
            {"success": False, "changed": False},
        ),
    ],
)
def test_image_mgmt_image_upgrade_common_00080(
    image_upgrade_common, key, expected
) -> None:
    """
    Function
    - _handle_post_put_delete_response

    Test
    - return expected values for POST requests
    - fail_json is not called
    """
    data = responses_image_upgrade_common(key)
    with does_not_raise():
        result = image_upgrade_common._handle_post_put_delete_response(
            data.get("response")
        )
    assert result.get("success") == expected.get("success")
    assert result.get("changed") == expected.get("changed")


@pytest.mark.parametrize(
    "key, expected",
    [
        ("True", True),
        ("true", True),
        ("TRUE", True),
        ("True", True),
        ("False", False),
        ("false", False),
        ("FALSE", False),
        ("False", False),
        ("foo", "foo"),
        (0, 0),
        (1, 1),
        (None, None),
        (None, None),
        ({"foo": 10}, {"foo": 10}),
        ([1, 2, "3"], [1, 2, "3"]),
    ],
)
def test_image_mgmt_image_upgrade_common_00090(
    image_upgrade_common, key, expected
) -> None:
    """
    Function
    - make_boolean

    Test
    - expected values are returned for all cases
    """
    assert image_upgrade_common.make_boolean(key) == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("", None),
        ("none", None),
        ("None", None),
        ("NONE", None),
        ("null", None),
        ("Null", None),
        ("NULL", None),
        ("None", None),
        ("foo", "foo"),
        (0, 0),
        (1, 1),
        (True, True),
        (False, False),
        ({"foo": 10}, {"foo": 10}),
        ([1, 2, "3"], [1, 2, "3"]),
    ],
)
def test_image_mgmt_image_upgrade_common_00100(
    image_upgrade_common, key, expected
) -> None:
    """
    Function
    - make_none

    Test
    - expected values are returned for all cases
    """
    assert image_upgrade_common.make_none(key) == expected


def test_image_mgmt_image_upgrade_common_00110(image_upgrade_common) -> None:
    """
    Function
    - log_msg

    Test
    - log_msg returns None when debug is False
    """
    ERROR_MESSAGE = "This is an error message"
    image_upgrade_common.debug = False
    assert image_upgrade_common.log_msg(ERROR_MESSAGE) == None


def test_image_mgmt_image_upgrade_common_00111(tmp_path, image_upgrade_common) -> None:
    """
    Function
    - log_msg

    Test
    - log_msg writes to the logfile when debug is True
    """
    directory = tmp_path / "test_log_msg"
    directory.mkdir()
    filename = directory / f"test_log_msg.txt"

    ERROR_MESSAGE = "This is an error message"
    image_upgrade_common.debug = True
    image_upgrade_common.logfile = filename
    image_upgrade_common.log_msg(ERROR_MESSAGE)

    assert filename.read_text(encoding="UTF-8") == ERROR_MESSAGE + "\n"
    assert len(list(tmp_path.iterdir())) == 1


def test_image_mgmt_image_upgrade_common_00112(tmp_path, image_upgrade_common) -> None:
    """
    Function
    - log_msg

    Test
    - log_msg calls fail_json if the logfile cannot be opened

    Description
    To ensure an error is generated, we attempt a write to a filename
    that is too long for the target OS.
    """
    directory = tmp_path / "test_log_msg"
    directory.mkdir()
    filename = directory / f"test_{'a' * 2000}_log_msg.txt"

    ERROR_MESSAGE = "This is an error message"
    image_upgrade_common.debug = True
    image_upgrade_common.logfile = filename
    with pytest.raises(AnsibleFailJson, match=r"error opening logfile"):
        image_upgrade_common.log_msg(ERROR_MESSAGE)
