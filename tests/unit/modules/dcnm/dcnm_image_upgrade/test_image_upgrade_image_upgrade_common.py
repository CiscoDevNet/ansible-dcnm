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

from .utils import (does_not_raise, image_upgrade_common_fixture,
                    responses_image_upgrade_common)


def test_image_upgrade_image_upgrade_common_00001(image_upgrade_common) -> None:
    """
    Function
    - ImageUpgradeCommon.__init__

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
    - ImageUpgradeCommon._handle_response

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
    - ImageUpgradeCommon._handle_response

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
    - ImageUpgradeCommon._handle_response

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
    - ImageUpgradeCommon._handle_response

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
    - ImageUpgradeCommon._handle_response

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
    - ImageUpgradeCommon._handle_get_response

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
    - ImageUpgradeCommon._handle_post_put_delete_response

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
    - ImageUpgradeCommon.make_boolean

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
    - ImageUpgradeCommon.make_none

    Test
    - expected values are returned for all cases
    """
    instance = image_upgrade_common
    assert instance.make_none(key) == expected


def test_image_upgrade_image_upgrade_common_00110(image_upgrade_common) -> None:
    """
    Function
    - ImageUpgradeCommon.log.log_msg

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
    - ImageUpgradeCommon.dcnm_send_with_retry

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
    - ImageUpgradeCommon.dcnm_send_with_retry

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


MATCH_00130 = "ImageUpgradeCommon.changed: changed must be a bool."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00130), True),
    ],
)
def test_image_upgrade_upgrade_00130(
    image_upgrade_common, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgradeCommon.changed

    Verify that changed does not call fail_json if passed a boolean.
    Verify that changed does call fail_json if passed a non-boolean.
    Verify that the default value is set if fail_json is called.
    """
    with does_not_raise():
        instance = image_upgrade_common

    with expected:
        instance.changed = value
    if raise_flag is False:
        assert instance.changed == value
    else:
        assert instance.changed is False


MATCH_00140 = "ImageUpgradeCommon.diff: diff must be a dict."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        ({}, does_not_raise(), False),
        ({"foo": "bar"}, does_not_raise(), False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00140), True),
        (True, pytest.raises(AnsibleFailJson, match=MATCH_00140), True),
        (1, pytest.raises(AnsibleFailJson, match=MATCH_00140), True),
    ],
)
def test_image_upgrade_upgrade_00140(
    image_upgrade_common, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgradeCommon.diff

    Verify that diff does not call fail_json if passed a dict.
    Verify that diff does call fail_json if passed a non-dict.
    Verify that diff returns list(value) when its getter is called.
    Verify that the default value ([]) is set if fail_json is called.
    """
    with does_not_raise():
        instance = image_upgrade_common

    with expected:
        instance.diff = value
    if raise_flag is False:
        assert instance.diff == [value]
    else:
        assert instance.diff == []


MATCH_00150 = "ImageUpgradeCommon.failed: failed must be a bool."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00150), True),
    ],
)
def test_image_upgrade_upgrade_00150(
    image_upgrade_common, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgradeCommon.failed

    Verify that failed does not call fail_json if passed a boolean.
    Verify that failed does call fail_json if passed a non-boolean.
    Verify that the default value is set if fail_json is called.
    """
    with does_not_raise():
        instance = image_upgrade_common

    with expected:
        instance.failed = value
    if raise_flag is False:
        assert instance.failed == value
    else:
        assert instance.failed is False


MATCH_00160 = "ImageUpgradeCommon.response_current: response_current must be a dict."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        ({}, does_not_raise(), False),
        ({"foo": "bar"}, does_not_raise(), False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00160), True),
        (True, pytest.raises(AnsibleFailJson, match=MATCH_00160), True),
        (1, pytest.raises(AnsibleFailJson, match=MATCH_00160), True),
    ],
)
def test_image_upgrade_upgrade_00160(
    image_upgrade_common, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgradeCommon.response_current

    Verify that response_current does not call fail_json if passed a dict.
    Verify that response_current does call fail_json if passed a non-dict.
    Verify that response_current returns value when its getter is called.
    Verify that the default value ({}) is set if fail_json is called.
    """
    with does_not_raise():
        instance = image_upgrade_common

    with expected:
        instance.response_current = value
    if raise_flag is False:
        assert instance.response_current == value
    else:
        assert instance.response_current == {}


MATCH_00170 = "ImageUpgradeCommon.response: response must be a dict."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        ({}, does_not_raise(), False),
        ({"foo": "bar"}, does_not_raise(), False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00170), True),
        (True, pytest.raises(AnsibleFailJson, match=MATCH_00170), True),
        (1, pytest.raises(AnsibleFailJson, match=MATCH_00170), True),
    ],
)
def test_image_upgrade_upgrade_00170(
    image_upgrade_common, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgradeCommon.response

    Verify that response does not call fail_json if passed a dict.
    Verify that response does call fail_json if passed a non-dict.
    Verify that response returns list(value) when its getter is called.
    Verify that the default value ([]) is set if fail_json is called.
    """
    with does_not_raise():
        instance = image_upgrade_common

    with expected:
        instance.response = value
    if raise_flag is False:
        assert instance.response == [value]
    else:
        assert instance.response == []


MATCH_00180 = "ImageUpgradeCommon.result: result must be a dict."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        ({}, does_not_raise(), False),
        ({"foo": "bar"}, does_not_raise(), False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00180), True),
        (True, pytest.raises(AnsibleFailJson, match=MATCH_00180), True),
        (1, pytest.raises(AnsibleFailJson, match=MATCH_00180), True),
    ],
)
def test_image_upgrade_upgrade_00180(
    image_upgrade_common, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgradeCommon.result

    Verify that result does not call fail_json if passed a dict.
    Verify that result does call fail_json if passed a non-dict.
    Verify that result returns list(value) when its getter is called.
    Verify that the default value ([]) is set if fail_json is called.
    """
    with does_not_raise():
        instance = image_upgrade_common

    with expected:
        instance.result = value
    if raise_flag is False:
        assert instance.result == [value]
    else:
        assert instance.result == []


MATCH_00190 = "ImageUpgradeCommon.result_current: result_current must be a dict."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        ({}, does_not_raise(), False),
        ({"foo": "bar"}, does_not_raise(), False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00190), True),
        (True, pytest.raises(AnsibleFailJson, match=MATCH_00190), True),
        (1, pytest.raises(AnsibleFailJson, match=MATCH_00190), True),
    ],
)
def test_image_upgrade_upgrade_00190(
    image_upgrade_common, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgradeCommon.result_current

    Verify that result_current does not call fail_json if passed a dict.
    Verify that result_current does call fail_json if passed a non-dict.
    Verify that result_current returns value when its getter is called.
    Verify that the default value ({}) is set if fail_json is called.
    """
    with does_not_raise():
        instance = image_upgrade_common

    with expected:
        instance.result_current = value
    if raise_flag is False:
        assert instance.result_current == value
    else:
        assert instance.result_current == {}


MATCH_00200 = r"ImageUpgradeCommon\.send_interval: send_interval "
MATCH_00200 += r"must be an integer\."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (1, does_not_raise(), False),
        (False, pytest.raises(AnsibleFailJson, match=MATCH_00200), True),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00200), True),
    ],
)
def test_image_upgrade_upgrade_00200(
    image_upgrade_common, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgrade.send_interval

    Summary
    Verify that send_interval does not call fail_json if the value is an integer
    and does call fail_json if the value is not an integer.  Verify that the
    default value is set if fail_json is called.
    """
    with does_not_raise():
        instance = image_upgrade_common
    with expected:
        instance.send_interval = value
    if raise_flag is False:
        assert instance.send_interval == value
    else:
        assert instance.send_interval == 5


MATCH_00210 = r"ImageUpgradeCommon\.timeout: timeout "
MATCH_00210 += r"must be an integer\."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (1, does_not_raise(), False),
        (False, pytest.raises(AnsibleFailJson, match=MATCH_00210), True),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00210), True),
    ],
)
def test_image_upgrade_upgrade_00210(
    image_upgrade_common, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgrade.timeout

    Summary
    Verify that timeout does not call fail_json if the value is an integer
    and does call fail_json if the value is not an integer.  Verify that the
    default value is set if fail_json is called.
    """
    with does_not_raise():
        instance = image_upgrade_common
    with expected:
        instance.timeout = value
    if raise_flag is False:
        assert instance.timeout == value
    else:
        assert instance.timeout == 300


MATCH_00220 = "ImageUpgradeCommon.unit_test: unit_test must be a bool."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00220), True),
    ],
)
def test_image_upgrade_upgrade_00220(
    image_upgrade_common, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgradeCommon.unit_test

    Verify that unit_test does not call fail_json if passed a boolean.
    Verify that unit_test does call fail_json if passed a non-boolean.
    Verify that the default value is set if fail_json is called.
    """
    with does_not_raise():
        instance = image_upgrade_common

    with expected:
        instance.unit_test = value
    if raise_flag is False:
        assert instance.unit_test == value
    else:
        assert instance.unit_test is False
