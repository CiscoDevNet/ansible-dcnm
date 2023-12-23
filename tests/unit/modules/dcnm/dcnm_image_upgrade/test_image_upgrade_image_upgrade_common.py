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

"""
ImageUpgradeCommon - unit tests
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

from typing import Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson

from .image_upgrade_utils import (does_not_raise, image_upgrade_common_fixture,
                                  responses_image_upgrade_common)


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
    test_params = {"config": {"switches": [{"ip_address": "172.22.150.105"}]}}

    with does_not_raise():
        instance = image_upgrade_common
    assert instance.params == test_params
    assert instance.log.debug is False
    assert instance.log.logfile == "/tmp/dcnm_image_upgrade.log"


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
    instance = image_upgrade_common

    data = responses_image_upgrade_common(key)
    with does_not_raise():
        result = instance._handle_response(  # pylint: disable=protected-access
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
    instance = image_upgrade_common

    data = responses_image_upgrade_common(key)
    with does_not_raise():
        result = instance._handle_response(  # pylint: disable=protected-access
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
    instance = image_upgrade_common

    data = responses_image_upgrade_common(key)
    with does_not_raise():
        result = instance._handle_response(  # pylint: disable=protected-access
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
    instance = image_upgrade_common

    data = responses_image_upgrade_common(key)
    result = instance._handle_response(  # pylint: disable=protected-access
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
    instance = image_upgrade_common

    data = responses_image_upgrade_common("test_image_mgmt_image_upgrade_common_00060a")
    with pytest.raises(AnsibleFailJson, match=r"Unknown request verb \(FOO\)"):
        instance._handle_response(  # pylint: disable=protected-access
            data.get("response"), data.get("verb")
        )  # pylint: disable=protected-access


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
    instance = image_upgrade_common

    data = responses_image_upgrade_common(key)
    with does_not_raise():
        result = instance._handle_get_response(  # pylint: disable=protected-access
            data.get("response")
        )  # pylint: disable=protected-access

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
    instance = image_upgrade_common

    data = responses_image_upgrade_common(key)
    with does_not_raise():
        result = instance._handle_post_put_delete_response(  # pylint: disable=protected-access
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
    instance = image_upgrade_common
    assert instance.make_boolean(key) == expected


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
    instance = image_upgrade_common
    assert instance.make_none(key) == expected


def test_image_mgmt_image_upgrade_common_00110(image_upgrade_common) -> None:
    """
    Function
    - log.log_msg

    Test
    - log.log_msg returns None when debug is False
    """
    instance = image_upgrade_common

    error_message = "This is an error message"
    instance.log.debug = False
    assert instance.log.log_msg(error_message) is None


def test_image_mgmt_image_upgrade_common_00111(tmp_path, image_upgrade_common) -> None:
    """
    Function
    - log.log_msg

    Test
    - log_msg writes to the log.logfile when log.debug is True
    """
    instance = image_upgrade_common

    directory = tmp_path / "test_log_msg"
    directory.mkdir()
    filename = directory / "test_log_msg.txt"

    error_message = "This is an error message"
    instance.log.debug = True
    instance.log.logfile = filename
    instance.log.log_msg(error_message)

    assert filename.read_text(encoding="UTF-8") == error_message + "\n"
    assert len(list(tmp_path.iterdir())) == 1


def test_image_mgmt_image_upgrade_common_00112(tmp_path, image_upgrade_common) -> None:
    """
    Function
    - log.log_msg

    Test
    - log.log_msg calls fail_json if the logfile cannot be opened

    Description
    To ensure an error is generated, we attempt a write to a filename
    that is too long for the target OS.
    """
    instance = image_upgrade_common

    directory = tmp_path / "test_log_msg"
    directory.mkdir()
    filename = directory / f"test_{'a' * 2000}_log_msg.txt"

    error_message = "This is an error message"
    instance.log.debug = True
    instance.log.logfile = filename
    with pytest.raises(AnsibleFailJson, match="error writing to logfile"):
        instance.log.log_msg(error_message)
