"""
controller_version: 12
description: Verify functionality of ImageStage
"""

from contextlib import contextmanager
from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_stage import \
    ImageStage
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import \
    SwitchIssuDetailsBySerialNumber

from .fixture import load_fixture


@contextmanager
def does_not_raise():
    yield


patch_module_utils = "ansible_collections.cisco.dcnm.plugins.module_utils."
patch_image_mgmt = patch_module_utils + "image_mgmt."
patch_common = patch_module_utils + "common."

dcnm_send_controller_version = patch_common + "controller_version.dcnm_send"
dcnm_send_image_stage = patch_image_mgmt + "image_stage.dcnm_send"
dcnm_send_issu_details = patch_image_mgmt + "switch_issu_details.dcnm_send"


def responses_controller_version(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_ControllerVersion"
    response = load_fixture(response_file).get(key)
    print(f"responses_controller_version: {key} : {response}")
    return response

def responses_image_stage(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_ImageStage"
    response = load_fixture(response_file).get(key)
    print(f"responses_image_stage: {key} : {response}")
    return response

def responses_issu_details(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_SwitchIssuDetails"
    response = load_fixture(response_file).get(key)
    print(f"responses_issu_details: {key} : {response}")
    return response


class MockAnsibleModule:
    params = {}

    def fail_json(msg) -> AnsibleFailJson:
        raise AnsibleFailJson(msg)


@pytest.fixture
def module():
    return ImageStage(MockAnsibleModule)


@pytest.fixture
def mock_issu_details() -> SwitchIssuDetailsBySerialNumber:
    return SwitchIssuDetailsBySerialNumber(MockAnsibleModule)


# test_image_mgmt_stage_00001
# test_init (former names)


def test_image_mgmt_stage_00001(module) -> None:
    """
    class attributes are initialized to expected values
    """
    module.__init__(MockAnsibleModule)
    assert module.module == MockAnsibleModule
    assert module.class_name == "ImageStage"
    assert isinstance(module.properties, dict)
    assert isinstance(module.serial_numbers_done, set)
    assert module.controller_version == None
    assert module.path == None
    assert module.verb == None
    assert module.payload == None
    assert isinstance(module.issu_detail, SwitchIssuDetailsBySerialNumber)
    assert isinstance(module.endpoints, ApiEndpoints)

# test_image_mgmt_stage_00002
# test_init_properties (former name)


def test_image_mgmt_stage_00002(module) -> None:
    """
    Properties are initialized to expected values
    """
    module._init_properties()
    assert isinstance(module.properties, dict)
    assert module.properties.get("response_data") == None
    assert module.properties.get("response") == None
    assert module.properties.get("result") == None
    assert module.properties.get("serial_numbers") == None
    assert module.properties.get("check_interval") == 10
    assert module.properties.get("check_timeout") == 1800


# test_image_mgmt_stage_00003
# test_populate_controller_version (former name)


@pytest.mark.parametrize(
    "key, expected",
    [
        ("test_image_mgmt_stage_00003a", "12.1.2e"),
        ("test_image_mgmt_stage_00003b", "12.1.3b"),
    ],
)
def test_image_mgmt_stage_00003(monkeypatch, module, key, expected) -> None:
    """
    _populate_controller_version retrieves the controller version from
    the controller.  This is used in commit() to populate the payload
    with either a misspelled "sereialNum" key/value (12.1.2e) or a
    correctly-spelled "serialNumbers" key/value (12.1.3b).

    Expectations:
    1. module.controller_version should be set

    Expected results:
    1. test_image_mgmt_stage_00003a -> module.controller_version == "12.1.2e"
    2. test_image_mgmt_stage_00003b -> module.controller_version == "12.1.3b"
    """

    def mock_dcnm_send_controller_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_controller_version, mock_dcnm_send_controller_version)

    module._populate_controller_version()
    assert module.controller_version == expected


# test_image_mgmt_stage_00004
# test_prune_serial_numbers (former name)


def test_image_mgmt_stage_00004(monkeypatch, module, mock_issu_details) -> None:
    """
    prune_serial_numbers removes serial numbers from the list for which
    imageStaged == "Success" (TODO: AND policy == <target_policy>)

    Expectations:
    1. module.serial_numbers should contain only serial numbers for which
    imageStaged == "none"
    2. module.serial_numbers should not contain serial numbers for which
    imageStaged == "Success"

    Expected results:
    1. module.serial_numbers == ["FDO2112189M", "FDO211218AX", "FDO211218B5"]
    2. module.serial_numbers != ["FDO211218FV", "FDO211218GC"]
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00004a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

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


# test_image_mgmt_stage_00005
# test_validate_serial_numbers_failed (former name)


def test_image_mgmt_stage_00005(monkeypatch, module, mock_issu_details) -> None:
    """
    fail_json is called when imageStaged == "Failed".

    Expectations:

    FDO21120U5D should pass since imageStaged == "Success"
    FDO2112189M should fail since imageStaged == "Failed"
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00005a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.issu_detail = mock_issu_details
    module.serial_numbers = ["FDO21120U5D", "FDO2112189M"]

    error_message = "Image staging is failing for the following switch: "
    error_message += "cvd-2313-leaf, 172.22.150.108, FDO2112189M. "
    error_message += "Check the switch connectivity to the controller "
    error_message += "and try again."
    with pytest.raises(AnsibleFailJson, match=error_message):
        module.validate_serial_numbers()


# test_commit_serial_numbers

match = r"ImageStage.commit: call instance.serial_numbers "
match += r"before calling commit."


@pytest.mark.parametrize(
    "serial_numbers_is_set, expected",
    [
        (True, does_not_raise()),
        (False, pytest.raises(AnsibleFailJson, match=match)),
    ],
)
def test_image_mgmt_stage_00006(
    monkeypatch, module, serial_numbers_is_set, expected
) -> None:
    """
    fail_json is called when ImageStage.commit() is called without
    setting instance.serial_numbers.

    Expectations:

    1. fail_json is called when serial_numbers is None
    2. fail_json is not called when serial_numbers is set
    """

    def mock_dcnm_send_controller_version(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00006a"
        return responses_controller_version(key)

    def mock_dcnm_send_image_stage(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00006a"
        return responses_image_stage(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00006a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_controller_version, mock_dcnm_send_controller_version)
    monkeypatch.setattr(dcnm_send_image_stage, mock_dcnm_send_image_stage)
    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    if serial_numbers_is_set:
        module.serial_numbers = ["FDO21120U5D"]
    with expected:
        module.commit()


# test_image_mgmt_stage_00007
# test_commit_path_verb (former name)


def test_image_mgmt_stage_00007(monkeypatch, module) -> None:
    """
    ImageStage.path should be set to:
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement/stage-image

    ImageStage.verb should be set to:
    POST

    Expectations:

    1. both self.path and self.verb should be set, per above
    """

    def mock_dcnm_send_controller_version(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00007a"
        return responses_controller_version(key)

    # Needed only for the 200 return code
    def mock_dcnm_send_image_stage(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00007a"
        return responses_image_stage(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00007a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_controller_version, mock_dcnm_send_controller_version)
    monkeypatch.setattr(dcnm_send_image_stage, mock_dcnm_send_image_stage)
    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.serial_numbers = ["FDO21120U5D"]
    module.commit()
    assert (
        module.path
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement/stage-image"
    )
    assert module.verb == "POST"


# test_image_mgmt_stage_00008
# test_commit_payload_serial_number_key_name (former name)


@pytest.mark.parametrize(
    "controller_version, expected_serial_number_key",
    [
        ("12.1.2e", "sereialNum"),
        ("12.1.3b", "serialNumbers"),
    ],
)
def test_image_mgmt_stage_00008(
    monkeypatch, module, controller_version, expected_serial_number_key
) -> None:
    """
    commit() will set the payload key name for the serial number
    based on the NDFC version, per Expected Results below:

    Expectations:
    1. The correct serial number key name should be used based on NDFC version

    Expected results:
    controller_version 12.1.2e -> key name "sereialNum" (yes, misspelled)
    controller_version 12.1.3b -> key name "serialNumbers
    """

    def mock_controller_version(*args, **kwargs) -> None:
        module.controller_version = controller_version

    controller_version_patch = "ansible_collections.cisco.dcnm.plugins."
    controller_version_patch += "modules.dcnm_image_upgrade."
    controller_version_patch += "ImageStage._populate_controller_version"
    monkeypatch.setattr(controller_version_patch, mock_controller_version)

    # Needed only for the 200 return code
    def mock_dcnm_send_image_stage(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00008a"
        return responses_image_stage(key)

    # Needed only for the 200 response
    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00008a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_image_stage, mock_dcnm_send_image_stage)
    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.serial_numbers = ["FDO21120U5D"]
    module.commit()
    assert expected_serial_number_key in module.payload.keys()


# test_image_mgmt_stage_00009
# test_wait_for_image_stage_to_complete (former name)


def test_image_mgmt_stage_00009(
    monkeypatch, module, mock_issu_details
) -> None:
    """
    _wait_for_image_stage_to_complete looks at the imageStaged status for each
    serial number and waits for it to be "Success" or "Failed".
    In the case where all serial numbers are "Success", the module returns.
    In the case where any serial number is "Failed", the module calls fail_json.

    Expectations:
    1. module.serial_numbers_done should be a set()
    2. module.serial_numbers_done should be length 2
    3. module.serial_numbers_done should contain all serial numbers module.serial_numbers
    4. The module should return without calling fail_json.
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00009a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.issu_detail = mock_issu_details
    module.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    module.check_interval = 0
    module._wait_for_image_stage_to_complete()
    assert isinstance(module.serial_numbers_done, set)
    assert len(module.serial_numbers_done) == 2
    assert "FDO21120U5D" in module.serial_numbers_done
    assert "FDO2112189M" in module.serial_numbers_done


# test_image_mgmt_stage_00010
# test_wait_for_image_stage_to_complete_stage_failed (former name)


def test_image_mgmt_stage_00010(
    monkeypatch, module, mock_issu_details
) -> None:
    """
    _wait_for_image_stage_to_complete looks at the imageStaged status for each
    serial number and waits for it to be "Success" or "Failed".
    In the case where all serial numbers are "Success", the module returns.
    In the case where any serial number is "Failed", the module calls fail_json.

    Expectations:
    1. module.serial_numbers_done is a set()
    2. module.serial_numbers_done has length 1
    3. module.serial_numbers_done contains FDO21120U5D, imageStaged is "Success"
    4. Call fail_json on serial number FDO2112189M, imageStaged is "Failed"
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00010a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.issu_detail = mock_issu_details
    module.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    module.check_interval = 0
    match = "Seconds remaining 1800: stage image failed for "
    match += "cvd-2313-leaf, FDO2112189M, 172.22.150.108. image "
    match += "staged percent: 90"
    with pytest.raises(AnsibleFailJson, match=match):
        module._wait_for_image_stage_to_complete()
    assert isinstance(module.serial_numbers_done, set)
    assert len(module.serial_numbers_done) == 1
    assert "FDO21120U5D" in module.serial_numbers_done
    assert "FDO2112189M" not in module.serial_numbers_done


# test_image_mgmt_stage_00011
# test_wait_for_image_stage_to_complete_timout


def test_image_mgmt_stage_00011(
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

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00011a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.issu_detail = mock_issu_details
    module.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    module.check_interval = 1
    module.check_timeout = 1

    match = "ImageStage._wait_for_image_stage_to_complete: "
    match += "Timed out waiting for image stage to complete. "
    match += "serial_numbers_done: FDO21120U5D, "
    match += "serial_numbers_todo: FDO21120U5D,FDO2112189M"
    with pytest.raises(AnsibleFailJson, match=match):
        module._wait_for_image_stage_to_complete()
    assert isinstance(module.serial_numbers_done, set)
    assert len(module.serial_numbers_done) == 1
    assert "FDO21120U5D" in module.serial_numbers_done
    assert "FDO2112189M" not in module.serial_numbers_done


# test_image_mgmt_stage_00012
# test_wait_for_current_actions_to_complete (former name)


def test_image_mgmt_stage_00012(
    monkeypatch, module, mock_issu_details
) -> None:
    """
    _wait_for_current_actions_to_complete waits until staging, validation,
    and upgrade actions are complete for all serial numbers.  It calls
    SwitchIssuDetailsBySerialNumber.actions_in_progress() and expects
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

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00012a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

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

# test_image_mgmt_stage_00013
# test_wait_for_current_actions_to_complete_timout (former name)


def test_image_mgmt_stage_00013(
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

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_stage_00013a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.issu_detail = mock_issu_details
    module.serial_numbers = [
        "FDO21120U5D",
        "FDO2112189M",
    ]
    module.check_interval = 1
    module.check_timeout = 1

    error_message = "ImageStage._wait_for_current_actions_to_complete: "
    error_message += "Timed out waiting for actions to complete. "
    error_message += "serial_numbers_done: FDO21120U5D, "
    error_message += "serial_numbers_todo: FDO21120U5D,FDO2112189M"
    with pytest.raises(AnsibleFailJson, match=error_message):
        module._wait_for_current_actions_to_complete()
    assert isinstance(module.serial_numbers_done, set)
    assert len(module.serial_numbers_done) == 1
    assert "FDO21120U5D" in module.serial_numbers_done
    assert "FDO2112189M" not in module.serial_numbers_done
