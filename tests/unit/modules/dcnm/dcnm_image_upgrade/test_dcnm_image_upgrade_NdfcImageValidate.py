"""
ndfc_version: 12
description: Verify functionality of NdfcImageValidate
"""

from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_image_upgrade import (
    NdfcImageValidate, NdfcSwitchIssuDetailsBySerialNumber, NdfcVersion)
from .fixture import load_fixture

dcnm_send_patch = "ansible_collections.cisco.dcnm.plugins.modules.dcnm_image_upgrade.dcnm_send"

def response_data_issu_details(key: str) -> Dict[str, str]:
    response_file = f"dcnm_image_upgrade_responses_NdfcSwitchIssuDetails"
    response = load_fixture(response_file).get(key)
    print(f"response_data_issu_details: {key} : {response}")
    return response


def response_data_ndfc_version(key: str) -> Dict[str, str]:
    response_file = f"dcnm_image_upgrade_responses_NdfcVersion"
    response = load_fixture(response_file).get(key)
    print(f"response_data_ndfc_version: {key} : {response}")
    return response


def response_data_ndfc_image_validate(key: str) -> Dict[str, str]:
    response_file = f"dcnm_image_upgrade_responses_NdfcImageValidate"
    response = load_fixture(response_file).get(key)
    print(f"response_data_ndfc_image_validate: {key} : {response}")
    return response


class MockAnsibleModule:
    params = {}

    def fail_json(msg) -> AnsibleFailJson:
        raise AnsibleFailJson(msg)


@pytest.fixture
def module():
    return NdfcImageValidate(MockAnsibleModule)


@pytest.fixture
def mock_issu_details() -> NdfcSwitchIssuDetailsBySerialNumber:
    return NdfcSwitchIssuDetailsBySerialNumber(MockAnsibleModule)


def test_init_properties(module) -> None:
    """
    Properties are initialized to expected values
    """
    module._init_properties()
    assert isinstance(module.properties, dict)
    assert module.properties.get("check_interval") == 10
    assert module.properties.get("check_timeout") == 1800
    assert module.properties.get("ndfc_data") == None
    assert module.properties.get("ndfc_response") == None
    assert module.properties.get("ndfc_result") == None
    assert module.properties.get("non_disruptive") == False
    assert module.properties.get("serial_numbers") == None


def test_prune_serial_numbers(monkeypatch, module, mock_issu_details) -> None:
    """
    prune_serial_numbers removes serial numbers from the list for which
    "validated" == "Success" (TODO: AND policy == <target_policy>)

    Expectations:
    1. module.serial_numbers should contain only serial numbers for which
    "validated" == "none"
    2. module.serial_numbers should not contain serial numbers for which
    "validated" == "Success"

    Expected results:
    1. module.serial_numbers == ["FDO2112189M", "FDO211218AX", "FDO211218B5"]
    2. module.serial_numbers != ["FDO211218FV", "FDO211218GC"]
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        key = "NdfcImageValidate_test_prune_serial_numbers"
        return response_data_issu_details(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.issu_detail = mock_issu_details
    module.serial_numbers = [
        "FDO2112189M",
        "FDO211218AX",
        "FDO211218B5",
        "FDO211218FV",
        "FDO211218GC",
    ]
    module.prune_serial_numbers()
    assert isinstance(module.serial_numbers, list)
    assert len(module.serial_numbers) == 3
    assert "FDO2112189M" in module.serial_numbers
    assert "FDO211218AX" in module.serial_numbers
    assert "FDO211218B5" in module.serial_numbers
    assert "FDO211218FV" not in module.serial_numbers
    assert "FDO211218GC" not in module.serial_numbers


def test_validate_serial_numbers_failed(monkeypatch, module, mock_issu_details) -> None:
    """
    fail_json is called when imageStaged == "Failed".

    Expectations:

    FDO21120U5D should pass since validated == "Success"
    FDO2112189M should fail since validated == "Failed"
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        key = "NdfcImageValidate_test_validate_serial_numbers"
        return response_data_issu_details(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.issu_detail = mock_issu_details
    module.serial_numbers = ["FDO21120U5D", "FDO2112189M"]

    error_message = "NdfcImageValidate.validate_serial_numbers: "
    error_message += "image validation is failing for the following switch: "
    error_message += "cvd-2313-leaf, 172.22.150.108, FDO2112189M. If this "
    error_message += "persists, check the switch connectivity to NDFC and "
    error_message += "try again."
    with pytest.raises(AnsibleFailJson, match=error_message):
        module.validate_serial_numbers()


def test_wait_for_image_validate_to_complete(
    monkeypatch, module, mock_issu_details
) -> None:
    """
    _wait_for_image_validate_to_complete looks at the "validated" status for each
    serial number and waits for it to be "Success" or "Failed".
    In the case where all serial numbers are "Success", the module returns.
    In the case where any serial number is "Failed", the module calls fail_json.

    Expectations:
    1.  module.serial_numbers_done should be a set()
    2.  module.serial_numbers_done should be length 2
    3.  module.serial_numbers_done should contain all serial numbers in
        module.serial_numbers
    4.  The module should return without calling fail_json.
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        key = "NdfcImageValidate_test_wait_for_image_validate_to_complete"
        return response_data_issu_details(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.issu_detail = mock_issu_details
    module.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    module.check_interval = 0
    module._wait_for_image_validate_to_complete()
    assert isinstance(module.serial_numbers_done, set)
    assert len(module.serial_numbers_done) == 2
    assert "FDO21120U5D" in module.serial_numbers_done
    assert "FDO2112189M" in module.serial_numbers_done


def test_wait_for_image_validate_to_complete_validate_failed(
    monkeypatch, module, mock_issu_details
) -> None:
    """
    _wait_for_image_validate_to_complete looks at the "validate" status for each
    serial number and waits for it to be "Success" or "Failed".
    In the case where all serial numbers are "Success", the module returns.
    In the case where any serial number is "Failed", the module calls fail_json.

    Expectations:
    1. module.serial_numbers_done is a set()
    2. module.serial_numbers_done has length 1
    3. module.serial_numbers_done contains FDO21120U5D, "validated" is "Success"
    4. Call fail_json on serial number FDO2112189M, "validated" is "Failed"
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        key = "NdfcImageValidate_test_wait_for_image_validate_to_complete_fail_json"
        return response_data_issu_details(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.issu_detail = mock_issu_details
    module.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    module.check_interval = 0
    error_message = "Seconds remaining 1800: validate image Failed for "
    error_message += "cvd-2313-leaf, 172.22.150.108, FDO2112189M, "
    error_message += "image validated percent: 100. Check the switch e.g. "
    error_message += "show install log detail, show incompatibility-all nxos "
    error_message += "<image>.  Or check NDFC Operations > Image Management > "
    error_message += "Devices > View Details > Validate for more details."
    with pytest.raises(AnsibleFailJson, match=error_message):
        module._wait_for_image_validate_to_complete()
    assert isinstance(module.serial_numbers_done, set)
    assert len(module.serial_numbers_done) == 1
    assert "FDO21120U5D" in module.serial_numbers_done
    assert "FDO2112189M" not in module.serial_numbers_done


def test_wait_for_image_validate_to_complete_timeout(
    monkeypatch, module, mock_issu_details
) -> None:
    """
    See test_wait_for_image_stage_to_complete for functional details.

    Expectations:
    1.  module.serial_numbers_done should be a set()
    2.  module.serial_numbers_done should be length 1
    3.  module.serial_numbers_done should contain FDO21120U5D
    3.  module.serial_numbers_done should not contain FDO2112189M
    4.  The function should call fail_json due to timeout
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        key = "NdfcImageValidate_test_wait_for_image_validate_to_complete_timeout"
        return response_data_issu_details(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.issu_detail = mock_issu_details
    module.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    module.check_interval = 1
    module.check_timeout = 1

    error_message = "NdfcImageValidate._wait_for_image_validate_to_complete: "
    error_message += "Timed out waiting for image validation to complete. "
    error_message += "serial_numbers_done: FDO21120U5D, "
    error_message += "serial_numbers_todo: FDO21120U5D,FDO2112189M"
    with pytest.raises(AnsibleFailJson, match=error_message):
        module._wait_for_image_validate_to_complete()
    assert isinstance(module.serial_numbers_done, set)
    assert len(module.serial_numbers_done) == 1
    assert "FDO21120U5D" in module.serial_numbers_done
    assert "FDO2112189M" not in module.serial_numbers_done


def test_wait_for_current_actions_to_complete(
    monkeypatch, module, mock_issu_details
) -> None:
    """
    _wait_for_current_actions_to_complete waits until staging, validation,
    and upgrade actions are complete for all serial numbers.  It calls
    NdfcSwitchIssuDetailsBySerialNumber.actions_in_progress() and expects
    this to return False.  actions_in_progress() returns True until none of
    the following keys has a value of "In-Progress":

    ["imageStaged", "upgrade", "validated"]

    Expectations:
    1.  module.serial_numbers_done should be a set()
    2.  module.serial_numbers_done should be length 2
    3.  module.serial_numbers_done should contain all serial numbers in
        module.serial_numbers
    4.  The function should return without calling fail_json.
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        key = "NdfcImageValidate_test_wait_for_current_actions_to_complete"
        return response_data_issu_details(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.issu_detail = mock_issu_details
    module.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    module.check_interval = 0
    module._wait_for_current_actions_to_complete()
    assert isinstance(module.serial_numbers_done, set)
    assert len(module.serial_numbers_done) == 2
    assert "FDO21120U5D" in module.serial_numbers_done
    assert "FDO2112189M" in module.serial_numbers_done


def test_wait_for_current_actions_to_complete_timeout(
    monkeypatch, module, mock_issu_details
) -> None:
    """
    See test_wait_for_current_actions_to_complete for functional details.

    Expectations:
    1.  module.serial_numbers_done should be a set()
    2.  module.serial_numbers_done should be length 1
    3.  module.serial_numbers_done should contain FDO21120U5D
    3.  module.serial_numbers_done should not contain FDO2112189M
    4.  The function should call fail_json due to timeout
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        key = "NdfcImageValidate_test_wait_for_current_actions_to_complete_timeout"
        return response_data_issu_details(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.issu_detail = mock_issu_details
    module.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    module.check_interval = 1
    module.check_timeout = 1

    error_message = "NdfcImageValidate._wait_for_current_actions_to_complete: "
    error_message += "Timed out waiting for actions to complete. "
    error_message += "serial_numbers_done: FDO21120U5D, "
    error_message += "serial_numbers_todo: FDO21120U5D,FDO2112189M"
    with pytest.raises(AnsibleFailJson, match=error_message):
        module._wait_for_current_actions_to_complete()
    assert isinstance(module.serial_numbers_done, set)
    assert len(module.serial_numbers_done) == 1
    assert "FDO21120U5D" in module.serial_numbers_done
    assert "FDO2112189M" not in module.serial_numbers_done
