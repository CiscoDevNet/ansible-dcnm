"""
controller_version: 12
description: Verify functionality of subclass SwitchIssuDetailsByIpAddress
"""

from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import \
    SwitchIssuDetailsByIpAddress

from .fixture import load_fixture

patch_module_utils = "ansible_collections.cisco.dcnm.plugins.module_utils."
patch_image_mgmt = patch_module_utils + "image_mgmt."

dcnm_send_issu_details = patch_image_mgmt + "switch_issu_details.dcnm_send"


class MockAnsibleModule:
    params = {}

    def fail_json(msg) -> AnsibleFailJson:
        raise AnsibleFailJson(msg)


def responses_switch_issu_details(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_SwitchIssuDetails"
    response = load_fixture(response_file).get(key)
    print(f"responses_switch_issu_details: {key} : {response}")
    return response


@pytest.fixture
def module():
    return SwitchIssuDetailsByIpAddress(MockAnsibleModule)


def test_init_properties(module) -> None:
    """
    Properties are initialized to expected values
    """
    action_keys = {"imageStaged", "upgrade", "validated"}

    module._init_properties()
    assert isinstance(module.properties, dict)
    assert isinstance(module.properties.get("action_keys"), set)
    assert module.properties.get("action_keys") == action_keys
    assert module.properties.get("response_data") == None
    assert module.properties.get("response") == None
    assert module.properties.get("result") == None
    assert module.properties.get("ip_address") == None


def test_refresh_return_code_200(monkeypatch, module) -> None:
    """
    NDFC response data for 200 response has expected types.
    endpoint: .../api/v1/imagemanagement/rest/packagemgnt/issu

    """
    key = "packagemgnt_issu_get_return_code_200_one_switch"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_issu_details: {responses_switch_issu_details(key)}")
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.refresh()
    assert isinstance(module.response, dict)
    assert isinstance(module.response_data, list)


def test_properties_are_set_to_expected_values(monkeypatch, module) -> None:
    """
    Properties are set based on ip_address setter value.
    endpoint: .../api/v1/imagemanagement/rest/packagemgnt/issu
    """
    key = "packagemgnt_issu_get_return_code_200_many_switch"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_issu_details: {responses_switch_issu_details(key)}")
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.refresh()
    module.ip_address = "172.22.150.102"
    assert module.device_name == "leaf1"
    assert module.serial_number == "FDO21120U5D"
    # change ip_address to a different switch, expect different information
    module.ip_address = "172.22.150.108"
    assert module.device_name == "cvd-2313-leaf"
    assert module.serial_number == "FDO2112189M"
    # verify remaining properties using current ip_address
    assert module.eth_switch_id == 39890
    assert module.fabric == "hard"
    assert module.fcoe_enabled == False
    assert module.group == "hard"
    # NOTE: For "id" see switch_id below
    assert module.image_staged == "Success"
    assert module.image_staged_percent == 100
    assert module.ip_address == "172.22.150.108"
    assert module.issu_allowed == None
    assert module.last_upg_action == "2023-Oct-06 03:43"
    assert module.mds == False
    assert module.mode == "Normal"
    assert module.model == "N9K-C93180YC-EX"
    assert module.model_type == 0
    assert module.peer == None
    assert module.platform == "N9K"
    assert module.policy == "KR5M"
    assert module.reason == "Upgrade"
    assert module.role == "leaf"
    assert module.status == "In-Sync"
    assert module.status_percent == 100
    # NOTE: switch_id appears in the response data as "id"
    # NOTE: "id" is a python reserved keyword, so we changed the property name
    assert module.switch_id == 2
    assert module.sys_name == "cvd-2313-leaf"
    assert module.system_mode == "Normal"
    assert module.upg_groups == None
    assert module.upgrade == "Success"
    assert module.upgrade_percent == 100
    assert module.validated == "Success"
    assert module.validated_percent == 100
    assert module.version == "10.2(5)"
    # NOTE: Two vdc_id values exist in the response data for each switch.
    # NOTE: Namely, "vdcId" and "vdc_id"
    # NOTE: Properties are provided for both, as follows.
    # NOTE: vdc_id == vdcId
    # NOTE: vdc_id2 == vdc_id
    assert module.vdc_id == 0
    assert module.vdc_id2 == -1
    assert module.vpc_peer == None
    assert module.vpc_role == None


def test_result_return_code_200(monkeypatch, module) -> None:
    """
    result contains expected key/values on 200 response from endpoint.
    endpoint: .../api/v1/imagemanagement/rest/packagemgnt/issu
    """
    key = "packagemgnt_issu_get_return_code_200_one_switch"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_issu_details: {responses_switch_issu_details(key)}")
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.refresh()
    assert isinstance(module.result, dict)
    assert module.result.get("found") == True
    assert module.result.get("success") == True


def test_result_return_code_404(monkeypatch, module) -> None:
    """
    fail_json is called on 404 response from malformed endpoint.
    endpoint: .../api/v1/imagemanagement/rest/policymgnt/policiess
    """
    key = "packagemgnt_issu_get_return_code_404"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_issu_details: {responses_switch_issu_details(key)}")
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    error_message = "Bad result when retriving switch information from the controller"
    with pytest.raises(AnsibleFailJson, match=error_message):
        module.refresh()


def test_result_return_code_200_empty_data(monkeypatch, module) -> None:
    """
    fail_json is called on 200 response with empty DATA key.
    endpoint: .../api/v1/imagemanagement/rest/policymgnt/policiess
    """
    key = "packagemgnt_issu_get_return_code_200_empty_DATA"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_issu_details: {responses_switch_issu_details(key)}")
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    error_message = "SwitchIssuDetailsByIpAddress.refresh: "
    error_message += "The controller has no switch ISSU information."
    with pytest.raises(AnsibleFailJson, match=error_message):
        module.refresh()


def test_result_return_code_200_switch_issu_info_length_0(monkeypatch, module) -> None:
    """
    fail_json is called on 200 response with DATA.lastOperDataObject length 0.
    endpoint: .../api/v1/imagemanagement/rest/policymgnt/policiess
    """
    key = "packagemgnt_issu_get_return_code_200"
    key += "_switch_issu_info_length_0"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_issu_details: {responses_switch_issu_details(key)}")
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    error_message = "SwitchIssuDetailsByIpAddress.refresh: "
    error_message += "The controller has no switch ISSU information."
    with pytest.raises(AnsibleFailJson, match=error_message):
        module.refresh()


def test_get_with_unknown_ip_address(monkeypatch, module) -> None:
    """
    Function description:

    SwitchIssuDetailsByIpAddress._get is called by all getter properties.
    It raises AnsibleFailJson if the user has not set ip_address or if
    the ip_address is unknown, or if an unknown property name is queried.
    It returns the value of the requested property if the user has set a known
    ip_address.

    Expected results:

    1.  fail_json is called with appropriate error message since an unknown
        ip_address is set.
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "packagemgnt_issu_get_return_code_200_one_switch"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.refresh()
    module.ip_address = "1.1.1.1"
    match = "SwitchIssuDetailsByIpAddress._get: 1.1.1.1 does not exist "
    match += "on the controller."
    with pytest.raises(AnsibleFailJson, match=match):
        module._get("serialNumber")


def test_get_with_unknown_property_name(monkeypatch, module) -> None:
    """
    Function description:

    SwitchIssuDetailsByIpAddress._get is called by all getter properties.
    It raises AnsibleFailJson if the user has not set ip_address or if
    the ip_address is unknown, or if an unknown property name is queried.
    It returns the value of the requested property if the user has set a
    known ip_address and the property name is valid.

    Expected results:

    1.  fail_json is called with appropriate error message since an unknown
        property is queried.
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "packagemgnt_issu_get_return_code_200_one_switch"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.refresh()
    module.ip_address = "172.22.150.102"
    match = "SwitchIssuDetailsByIpAddress._get: 172.22.150.102 unknown "
    match += f"property name: FOO"
    with pytest.raises(AnsibleFailJson, match=match):
        module._get("FOO")
