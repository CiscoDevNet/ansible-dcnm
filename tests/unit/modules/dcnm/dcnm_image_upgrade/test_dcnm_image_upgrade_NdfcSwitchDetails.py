"""
ndfc_version: 12
description: Verify functionality of NdfcSwitchDetails
"""
from contextlib import contextmanager
from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_image_upgrade import (
    NdfcAnsibleImageUpgradeCommon, NdfcSwitchDetails, NdfcVersion)

from .fixture import load_fixture


@contextmanager
def does_not_raise():
    yield


dcnm_send_patch = (
    "ansible_collections.cisco.dcnm.plugins.modules.dcnm_image_upgrade.dcnm_send"
)


def responses_ndfc_switch_details(key: str) -> Dict[str, str]:
    response_file = f"dcnm_image_upgrade_responses_NdfcSwitchDetails"
    response = load_fixture(response_file).get(key)
    print(f"responses_ndfc_switch_details: {key} : {response}")
    return response


class MockAnsibleModule:
    params = {}

    def fail_json(msg) -> AnsibleFailJson:
        raise AnsibleFailJson(msg)


@pytest.fixture
def module():
    return NdfcSwitchDetails(MockAnsibleModule)


def test_init(module) -> None:
    module.__init__(MockAnsibleModule)
    assert isinstance(module, NdfcSwitchDetails)
    assert module.class_name == "NdfcSwitchDetails"


def test_init_properties(module) -> None:
    """
    Properties are initialized to expected values
    """
    module._init_properties()
    assert isinstance(module.properties, dict)
    assert module.properties.get("ip_address") == None
    assert module.properties.get("ndfc_data") == None
    assert module.properties.get("ndfc_response") == None
    assert module.properties.get("ndfc_result") == None


def test_ip_address_not_set(module) -> None:
    """
    Function description:

    NdfcSwitchDetails.ip_address returns:
        - IP Address, if the user has set ip_address
        - None, if the user has not already set ip_address

    Expected results:

    1. instance.ip_address will return None
    """
    assert module.ip_address == None


def test_ip_address_is_set(module) -> None:
    """
    Function description:

    NdfcSwitchDetails.ip_address returns:
        - IP Address, if the user has set ip_address
        - None, if the user has not already set ip_address

    Expected results:

    1. instance.ip_address will return the value set by the user
    """
    module.ip_address = "1.2.3.4"
    assert module.ip_address == "1.2.3.4"


def test_refresh(monkeypatch, module) -> None:
    """
    Function description:

    NdfcSwitchDetails.refresh sets the following properties:
        - ndfc_data
        - ndfc_response
        - ndfc_result

    Expected results:

    1. instance.ndfc_data is a dictionary
    2. instance.ndfc_response is a dictionary
    3. instance.ndfc_data is a list
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        key = "NdfcSwitchDetails_get_return_code_200"
        return responses_ndfc_switch_details(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.refresh()
    assert isinstance(module.ndfc_data, dict)
    assert isinstance(module.ndfc_result, dict)
    assert isinstance(module.ndfc_response, dict)


def test_refresh_ndfc_data(monkeypatch, module) -> None:
    """
    Function description:

    See test_refresh

    Expected results:

    1. instance.ndfc_data is a dictionary
    2. When instance.ip_address is set, getter properties will return values specific to ip_address
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        key = "NdfcSwitchDetails_get_return_code_200"
        return responses_ndfc_switch_details(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.refresh()
    assert isinstance(module.ndfc_data, dict)
    module.ip_address = "172.22.150.110"
    assert module.hostname == "cvd-1111-bgw"
    module.ip_address = "172.22.150.111"
    # We use the above IP address to test the remaining properties
    assert module.fabric_name == "easy"
    assert module.hostname == "cvd-1112-bgw"
    assert module.logical_name == "cvd-1112-bgw"
    assert module.model == "N9K-C9504"
    # This is derived from "model" and is not in the NDFC response
    assert module.platform == "N9K"
    assert module.role == "border gateway"
    assert module.serial_number == "FOX2109PGD1"


match = "Unable to retrieve switch information from NDFC. "


@pytest.mark.parametrize(
    "key,expected",
    [
        ("NdfcSwitchDetails_get_return_code_200", does_not_raise()),
        (
            "NdfcSwitchDetails_get_return_code_404",
            pytest.raises(AnsibleFailJson, match=match),
        ),
        (
            "NdfcSwitchDetails_get_return_code_500",
            pytest.raises(AnsibleFailJson, match=match),
        ),
    ],
)
def test_ndfc_result(monkeypatch, module, key, expected) -> None:
    """
    Function description:

    NdfcSwitchDetails.ndfc_result returns the result of its superclass
    method NdfcAnsibleImageUpgradeCommon._handle_response()

    Expectations:

    1.  200 RETURN_CODE, MESSAGE == "OK",
        NdfcSwitchDetails.ndfc_result == {'found': True, 'success': True}

    2.  404 RETURN_CODE, MESSAGE == "Not Found",
        NdfcSwitchDetails.ndfc_result == {'found': False, 'success': True}

    3.  500 RETURN_CODE, MESSAGE ~= "Internal Server Error",
        NdfcSwitchDetails.ndfc_result == {'found': False, 'success': False}

    Expected results:

    1. NdfcSwitchDetails_result_200 == {'found': True, 'success': True}
    2. NdfcSwitchDetails_result_404 == {'found': False, 'success': True}
    3. NdfcSwitchDetails_result_500 == {'found': False, 'success': False}
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        return responses_ndfc_switch_details(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    with expected:
        module.refresh()


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
def test_get_with_ip_address_set(monkeypatch, module, item, expected) -> None:
    """
    Function description:

    NdfcSwitchDetails._get is called by all getter properties.
    It raises AnsibleFailJson if the user has not set ip_address.
    It returns the value of the requested property if the user has set ip_address.
    The property value is passed to both make_boolean() and make_none(), which
    either:
        - converts it to a boolean
        - converts it to NoneType
        - returns the value unchanged

    Expectations:

    1.  NdfcVersion._get returns above values
        given corresponding responses

    Expected results:

    1. NdfcVersion_mode_LAN == "LAN"
    2. NdfcVersion_mode_none == None
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        key = "NdfcSwitchDetails_get_return_code_200"
        return responses_ndfc_switch_details(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.refresh()
    module.ip_address = "172.22.150.110"
    assert module._get(item) == expected
