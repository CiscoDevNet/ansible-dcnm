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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.log import Log

from .image_upgrade_utils import (does_not_raise, image_upgrade_common_fixture,
                                  responses_image_upgrade_common)


def test_image_upgrade_image_upgrade_common_00001(image_upgrade_common) -> None:
    """
    Function
    - __init__

    Summary
    Verify that instance.params accepts well-formed input and that the
    params getter returns the expected value.

    Test
    - fail_json is not called
    - image_upgrade_common.params is set to the expected value
    - All other instance properties are initialized to expected values
    """
    test_params = {"config": {"switches": [{"ip_address": "172.22.150.105"}]}}

    with does_not_raise():
        instance = image_upgrade_common
    assert instance.params == test_params
    assert instance.changed is False
    assert instance.response == []
    assert instance.response_current == {}
    assert instance.response_data == []
    assert instance.result == []
    assert instance.result_current == {}
    assert instance.send_interval == 5
    assert instance.timeout == 300
    assert instance.unit_test is False


@pytest.mark.parametrize(
    "key, expected",
    [
        (
            "test_image_upgrade_image_upgrade_common_00020a",
            {"success": True, "changed": True},
        ),
        (
            "test_image_upgrade_image_upgrade_common_00020b",
            {"success": False, "changed": False},
        ),
        (
            "test_image_upgrade_image_upgrade_common_00020c",
            {"success": False, "changed": False},
        ),
    ],
)
def test_image_upgrade_image_upgrade_common_00020(
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
            "test_image_upgrade_image_upgrade_common_00030a",
            {"success": True, "changed": True},
        ),
        (
            "test_image_upgrade_image_upgrade_common_00030b",
            {"success": False, "changed": False},
        ),
        (
            "test_image_upgrade_image_upgrade_common_00030c",
            {"success": False, "changed": False},
        ),
    ],
)
def test_image_upgrade_image_upgrade_common_00030(
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
            "test_image_upgrade_image_upgrade_common_00040a",
            {"success": True, "changed": True},
        ),
        (
            "test_image_upgrade_image_upgrade_common_00040b",
            {"success": False, "changed": False},
        ),
        (
            "test_image_upgrade_image_upgrade_common_00040c",
            {"success": False, "changed": False},
        ),
    ],
)
def test_image_upgrade_image_upgrade_common_00040(
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
            "test_image_upgrade_image_upgrade_common_00050a",
            {"success": True, "found": True},
        ),
        (
            "test_image_upgrade_image_upgrade_common_00050b",
            {"success": False, "found": False},
        ),
        (
            "test_image_upgrade_image_upgrade_common_00050c",
            {"success": True, "found": False},
        ),
        (
            "test_image_upgrade_image_upgrade_common_00050d",
            {"success": False, "found": False},
        ),
    ],
)
def test_image_upgrade_image_upgrade_common_00050(
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


def test_image_upgrade_image_upgrade_common_00060(image_upgrade_common) -> None:
    """
    Function
    - _handle_response

    Test
    - fail_json is called because an unknown request verb is provided
    """
    instance = image_upgrade_common

    data = responses_image_upgrade_common(
        "test_image_upgrade_image_upgrade_common_00060a"
    )
    with pytest.raises(AnsibleFailJson, match=r"Unknown request verb \(FOO\)"):
        instance._handle_response(  # pylint: disable=protected-access
            data.get("response"), data.get("verb")
        )  # pylint: disable=protected-access


@pytest.mark.parametrize(
    "key, expected",
    [
        (
            "test_image_upgrade_image_upgrade_common_00070a",
            {"success": True, "found": True},
        ),
        (
            "test_image_upgrade_image_upgrade_common_00070b",
            {"success": False, "found": False},
        ),
        (
            "test_image_upgrade_image_upgrade_common_00070c",
            {"success": True, "found": False},
        ),
        (
            "test_image_upgrade_image_upgrade_common_00070d",
            {"success": False, "found": False},
        ),
    ],
)
def test_image_upgrade_image_upgrade_common_00070(
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
            "test_image_upgrade_image_upgrade_common_00080a",
            {"success": True, "changed": True},
        ),
        (
            "test_image_upgrade_image_upgrade_common_00080b",
            {"success": False, "changed": False},
        ),
        (
            "test_image_upgrade_image_upgrade_common_00080c",
            {"success": False, "changed": False},
        ),
    ],
)
def test_image_upgrade_image_upgrade_common_00080(
    image_upgrade_common, key, expected
) -> None:
    """
    Function
    - _handle_post_put_delete_response

    Summary
    Verify that expected values are returned for POST requests.

    Test
    - fail_json is not called
    - return expected values for POST requests, when:
    - 00080a. MESSAGE == "OK"
    - 00080b. MESSAGE != "OK"
    - 00080c. MESSAGE field is missing
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
def test_image_upgrade_image_upgrade_common_00090(
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
def test_image_upgrade_image_upgrade_common_00100(
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


def test_image_upgrade_image_upgrade_common_00110(image_upgrade_common) -> None:
    """
    Function
    - log.log_msg

    Test
    - log.debug returns None when the base logger is disabled
    - Base logger is disabled if Log.config is None (which is the default)
    """
    instance = image_upgrade_common

    message = "This is a message"
    assert instance.log.debug(message) is None
    assert instance.log.info(message) is None


def test_image_upgrade_image_upgrade_common_00120(
    monkeypatch, image_upgrade_common
) -> None:
    """
    Function
    - dcnm_send_with_retry

    Summary
    Verify that result and response are set to the expected values when
    payload is None and the response is successful.

    """

    def mock_dcnm_send(*args, **kwargs):
        return {"MESSAGE": "OK", "RETURN_CODE": 200}

    instance = image_upgrade_common
    instance.timeout = 1
    monkeypatch.setattr(instance, "dcnm_send", mock_dcnm_send)

    instance.dcnm_send_with_retry("PUT", "https://foo.bar.com/endpoint", None)
    assert instance.response_current == {"MESSAGE": "OK", "RETURN_CODE": 200}
    assert instance.result == [{"changed": True, "success": True}]


def test_image_upgrade_image_upgrade_common_00121(
    monkeypatch, image_upgrade_common
) -> None:
    """
    Function
    - dcnm_send_with_retry

    Summary
    Verify that result and response are set to the expected values when
    payload is set and the response is successful.

    """

    def mock_dcnm_send(*args, **kwargs):
        return {"MESSAGE": "OK", "RETURN_CODE": 200}

    with does_not_raise():
        instance = image_upgrade_common
        monkeypatch.setattr(instance, "dcnm_send", mock_dcnm_send)
        instance.dcnm_send_with_retry(
            "PUT", "https://foo.bar.com/endpoint", {"foo": "bar"}
        )
    assert instance.response_current == {"MESSAGE": "OK", "RETURN_CODE": 200}
    assert instance.result == [{"changed": True, "success": True}]
