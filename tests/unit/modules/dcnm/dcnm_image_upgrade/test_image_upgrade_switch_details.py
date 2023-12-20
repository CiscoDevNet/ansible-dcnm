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
# Some tests require calling protected methods
# pylint: disable=protected-access

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_details import \
    SwitchDetails

from .image_upgrade_utils import (does_not_raise, responses_switch_details,
                                  switch_details_fixture)

PATCH_MODULE_UTILS = "ansible_collections.cisco.dcnm.plugins.module_utils."
PATCH_IMAGE_MGMT = PATCH_MODULE_UTILS + "image_mgmt."
DCNM_SEND_SWITCH_DETAILS = PATCH_IMAGE_MGMT + "switch_details.dcnm_send"


def test_image_mgmt_switch_details_00001(switch_details) -> None:
    """
    Function
    - __init__

    Test
    - Class attributes are initialized to expected values
    """
    instance = switch_details
    assert isinstance(instance, SwitchDetails)
    assert instance.class_name == "SwitchDetails"


def test_image_mgmt_switch_details_00002(switch_details) -> None:
    """
    Function
    - _init_properties

    Test
    - Class properties are initialized to expected values
    """
    instance = switch_details

    assert isinstance(instance.properties, dict)
    assert instance.properties.get("ip_address") is None
    assert instance.properties.get("response_data") is None
    assert instance.properties.get("response") is None
    assert instance.properties.get("result") is None


def test_image_mgmt_switch_details_00020(monkeypatch, switch_details) -> None:
    """
    Function
    - refresh

    Test
    - response_data, response, result are dictionaries
    """
    instance = switch_details

    def mock_dcnm_send_switch_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_switch_details_00020a"
        return responses_switch_details(key)

    monkeypatch.setattr(DCNM_SEND_SWITCH_DETAILS, mock_dcnm_send_switch_details)

    instance.refresh()
    assert isinstance(instance.response_data, dict)
    assert isinstance(instance.result, dict)
    assert isinstance(instance.response, dict)


def test_image_mgmt_switch_details_00021(monkeypatch, switch_details) -> None:
    """
    Function
    - refresh

    Test
    - response_data is a dictionary
    - ip_address is set
    - getter properties will return values specific to ip_address
    """
    instance = switch_details

    def mock_dcnm_send_switch_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_switch_details_00021a"
        return responses_switch_details(key)

    monkeypatch.setattr(DCNM_SEND_SWITCH_DETAILS, mock_dcnm_send_switch_details)

    instance.refresh()
    assert isinstance(instance.response_data, dict)
    instance.ip_address = "172.22.150.110"
    assert instance.hostname == "cvd-1111-bgw"
    instance.ip_address = "172.22.150.111"
    # We use the above IP address to test the remaining properties
    assert instance.fabric_name == "easy"
    assert instance.hostname == "cvd-1112-bgw"
    assert instance.logical_name == "cvd-1112-bgw"
    assert instance.model == "N9K-C9504"
    # This is derived from "model" and is not in the controller response
    assert instance.platform == "N9K"
    assert instance.role == "border gateway"
    assert instance.serial_number == "FOX2109PGD1"


MATCH_00022 = "Unable to retrieve switch information from the controller."


@pytest.mark.parametrize(
    "key,expected",
    [
        ("test_image_mgmt_switch_details_00022a", does_not_raise()),
        (
            "test_image_mgmt_switch_details_00022b",
            pytest.raises(AnsibleFailJson, match=MATCH_00022),
        ),
        (
            "test_image_mgmt_switch_details_00022c",
            pytest.raises(AnsibleFailJson, match=MATCH_00022),
        ),
    ],
)
def test_image_mgmt_switch_details_00022(
    monkeypatch, switch_details, key, expected
) -> None:
    """
    Function
    - switch_details.refresh
    - switch_details.result
    - ImageUpgradeCommon._handle_response

    Test
    - test_image_mgmt_switch_details_00022a
        - 200 RETURN_CODE, MESSAGE == "OK"
        - result == {'found': True, 'success': True}
    - test_image_mgmt_switch_details_00022b
        - 404 RETURN_CODE, MESSAGE == "Not Found"
        - result == {'found': False, 'success': True}
    - test_image_mgmt_switch_details_00022c
        - 500 RETURN_CODE, MESSAGE ~= "Internal Server Error"
        - result == {'found': False, 'success': False}
    """
    instance = switch_details

    def mock_dcnm_send_switch_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_details(key)

    monkeypatch.setattr(DCNM_SEND_SWITCH_DETAILS, mock_dcnm_send_switch_details)

    with expected:
        instance.refresh()


@pytest.mark.parametrize(
    "item, expected",
    [
        ("fabricName", "easy"),
        ("hostName", "cvd-1111-bgw"),
        ("licenseViolation", False),
        ("location", None),
        ("logicalName", "cvd-1111-bgw"),
        ("managable", True),
        ("model", "N9K-C9504"),
        ("present", True),
        ("serialNumber", "FOX2109PGCT"),
        ("switchRole", "border gateway"),
    ],
)
def test_image_mgmt_switch_details_00023(
    monkeypatch, switch_details, item, expected
) -> None:
    """
    Function
    - switch_details.refresh
    - switch_details.ip_address
    - switch_details._get

    Test
    - _get returns correct property values

    Description

    SwitchDetails._get is called by all getter properties.

    It raises AnsibleFailJson if the user has not set ip_address or if
    the ip_address is unknown, or if an unknown property name is queried.

    It returns the value of the requested property if the user has set
    ip_address and the property name is known.

    Property values are passed to make_boolean() and make_none(), which either:
        - converts value to a boolean
        - converts value to NoneType
        - returns value unchanged
    """
    instance = switch_details

    def mock_dcnm_send_switch_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_switch_details_00023a"
        return responses_switch_details(key)

    monkeypatch.setattr(DCNM_SEND_SWITCH_DETAILS, mock_dcnm_send_switch_details)

    instance.refresh()
    instance.ip_address = "172.22.150.110"
    assert instance._get(item) == expected


def test_image_mgmt_switch_details_00024(monkeypatch, switch_details) -> None:
    """
    Function
    - switch_details.refresh
    - switch_details.ip_address
    - switch_details._get

    Test
    - _get calls fail_json when switch_details.ip_address is unknown

    Description
    SwitchDetails._get is called by all getter properties.
    It raises AnsibleFailJson if the user has not set ip_address or if
    the ip_address is unknown, or if an unknown property name is queried.
    It returns the value of the requested property if the user has set a known
    ip_address.
    """
    instance = switch_details

    def mock_dcnm_send_switch_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_switch_details_00024a"
        return responses_switch_details(key)

    monkeypatch.setattr(DCNM_SEND_SWITCH_DETAILS, mock_dcnm_send_switch_details)

    match = "SwitchDetails._get: 1.1.1.1 does not exist "
    match += "on the controller."

    instance.refresh()
    instance.ip_address = "1.1.1.1"
    with pytest.raises(AnsibleFailJson, match=match):
        instance._get("hostName")


def test_image_mgmt_switch_details_00025(monkeypatch, switch_details) -> None:
    """
    Function
    - switch_details.refresh
    - switch_details.ip_address
    - switch_details._get

    Test
    - _get calls fail_json when an unknown property name is queried

    Description
    SwitchDetails._get is called by all getter properties.
    It raises AnsibleFailJson if the user has not set ip_address or if
    the ip_address is unknown, or if an unknown property name is queried.
    """
    instance = switch_details

    def mock_dcnm_send_switch_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_switch_details_00025a"
        return responses_switch_details(key)

    monkeypatch.setattr(DCNM_SEND_SWITCH_DETAILS, mock_dcnm_send_switch_details)

    match = "SwitchDetails._get: 172.22.150.110 does not have a key named FOO."

    instance.refresh()
    instance.ip_address = "172.22.150.110"
    with pytest.raises(AnsibleFailJson, match=match):
        instance._get("FOO")


# setters


@pytest.mark.parametrize(
    "ip_address_is_set, expected",
    [
        (True, "1.2.3.4"),
        (False, None),
    ],
)
def test_image_mgmt_switch_details_00060(
    switch_details, ip_address_is_set, expected
) -> None:
    """
    Function
    - ip_address.setter

    Test
    - return IP address, if set
    - return None, if not set
    """
    instance = switch_details

    if ip_address_is_set:
        instance.ip_address = "1.2.3.4"
    assert instance.ip_address == expected
