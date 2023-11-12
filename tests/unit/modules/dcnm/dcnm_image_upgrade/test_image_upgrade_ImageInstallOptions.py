"""
controller_version: 12
description: Verify functionality of class ImageInstallOptions
"""

from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.install_options import \
    ImageInstallOptions

from .fixture import load_fixture

patch_module_utils = "ansible_collections.cisco.dcnm.plugins.module_utils."
patch_image_mgmt = patch_module_utils + "image_mgmt."

dcnm_send_install_options = patch_image_mgmt + "install_options.dcnm_send"


class MockAnsibleModule:
    params = {}

    def fail_json(msg) -> AnsibleFailJson:
        raise AnsibleFailJson(msg)


def responses_image_install_options(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_ImageInstallOptions"
    response = load_fixture(response_file).get(key)
    print(f"{key} : : {response}")
    return response


@pytest.fixture
def module():
    return ImageInstallOptions(MockAnsibleModule)


def test_image_mgmt_install_options_00001(module) -> None:
    """
    Verify attributes set in __init__
    """
    module.__init__(MockAnsibleModule)
    assert module.module == MockAnsibleModule
    assert module.class_name == "ImageInstallOptions"
    assert isinstance(module.endpoints, ApiEndpoints)


def test_image_mgmt_install_options_00002(module) -> None:
    """
    Properties are initialized to expected values
    """
    module._init_properties()
    assert isinstance(module.properties, dict)
    assert module.properties.get("epld") == False
    assert module.properties.get("epld_modules") == None
    assert module.properties.get("issu") == True
    assert module.properties.get("package_install") == False
    assert module.properties.get("policy_name") == None
    assert module.properties.get("response") == None
    assert module.properties.get("response_data") == None
    assert module.properties.get("result") == None
    assert module.properties.get("serial_number") == None


# test_image_mgmt_install_options_00003
# test_policy_name_not_defined (former name)


def test_image_mgmt_install_options_00003(module) -> None:
    """
    fail_json() is called if policy_name is not set when refresh() is called.
    """
    module.serial_number = "FOO"
    match = "ImageInstallOptions.refresh: "
    match += "instance.policy_name must be set before "
    match += r"calling refresh\(\)"
    with pytest.raises(AnsibleFailJson, match=match):
        module.refresh()


# test_image_mgmt_install_options_00004
# test_serial_number_not_defined (former name)


def test_image_mgmt_install_options_00004(module) -> None:
    """
    fail_json() is called if serial_number is not set when refresh() is called.
    """
    module.policy_name = "FOO"
    match = "ImageInstallOptions.refresh: "
    match += "instance.serial_number must be set before "
    match += r"calling refresh\(\)"
    with pytest.raises(AnsibleFailJson, match=match):
        module.refresh()


# test_image_mgmt_install_options_00005
# test_refresh_return_code_200 (former name)


def test_image_mgmt_install_options_00005(monkeypatch, module) -> None:
    """
    Properties are updated based on 200 response from endpoint.
    endpoint: install-options
    """

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_install_options_00005a"
        return responses_image_install_options(key)

    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)

    module.policy_name = "KRM5"
    module.serial_number = "BAR"
    module.refresh()
    assert isinstance(module.response, dict)
    assert module.device_name == "cvd-1314-leaf"
    assert module.err_message is None
    assert module.epld_modules is None
    assert module.install_option == "disruptive"
    assert module.install_packages is None
    assert module.ip_address == "172.22.150.105"
    assert module.os_type == "64bit"
    assert module.platform == "N9K/N3K"
    assert module.pre_issu_link == "Not Applicable"
    assert isinstance(module.raw_data, dict)
    assert isinstance(module.raw_response, dict)
    assert "compatibilityStatusList" in module.raw_data
    print("module.raw_data: ", module.raw_data)
    assert module.rep_status == "skipped"
    assert module.serial_number == "BAR"
    assert module.status == "Success"
    assert module.timestamp == "NA"
    assert module.version == "10.2.5"
    comp_disp = "show install all impact nxos bootflash:nxos64-cs.10.2.5.M.bin"
    assert module.comp_disp == comp_disp
    assert module.result.get("success") == True


# test_image_mgmt_install_options_00006
# test_refresh_return_code_500 (former name)


def test_image_mgmt_install_options_00006(monkeypatch, module) -> None:
    """
    fail_json() should be called if the response RETURN_CODE != 200
    """

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_install_options_00006a"
        return responses_image_install_options(key)

    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)

    module.policy_name = "KRM5"
    module.serial_number = "BAR"
    match = "ImageInstallOptions.refresh: "
    match += "Bad result when retrieving install-options from "
    match += "the controller. Controller response:"
    with pytest.raises(AnsibleFailJson, match=rf"{match}"):
        module.refresh()


def test_image_mgmt_install_options_00007(monkeypatch, module) -> None:
    """
    Properties are updated based on:
    -   200 response from endpoint
    -   Device has no policy attached
    -   POST REQUEST
        - issu == True
        - epld == False
        - package_install == False

    endpoint: install-options
    """

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_install_options_00007a"
        return responses_image_install_options(key)

    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)

    module.policy_name = "KRM5"
    module.serial_number = "FDO21120U5D"
    module.refresh()
    assert isinstance(module.response, dict)
    assert module.device_name == "leaf1"
    assert module.err_message is None
    assert module.epld_modules is None
    assert module.install_option == "NA"
    assert module.install_packages is None
    assert module.ip_address == "172.22.150.102"
    assert module.os_type == "64bit"
    assert module.platform == "N9K/N3K"
    assert module.pre_issu_link == "Not Applicable"
    assert isinstance(module.raw_data, dict)
    assert isinstance(module.raw_response, dict)
    assert "compatibilityStatusList" in module.raw_data
    print("module.raw_data: ", module.raw_data)
    assert module.rep_status == "skipped"
    assert module.serial_number == "FDO21120U5D"
    assert module.status == "Skipped"
    assert module.timestamp == "NA"
    assert module.version == "10.2.5"
    assert module.version_check == "Compatibility status skipped."
    assert module.comp_disp == "Compatibility status skipped."
    assert module.result.get("success") == True


def test_image_mgmt_install_options_00008(monkeypatch, module) -> None:
    """
    Properties are updated based on:
    -   200 response from endpoint
    -   Device has no policy attached
    -   POST REQUEST
        - issu == True
        - epld == True
        - package_install == False

    endpoint: install-options
    """

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_install_options_00008a"
        return responses_image_install_options(key)

    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)

    module.policy_name = "KRM5"
    module.serial_number = "FDO21120U5D"
    module.epld = True
    module.issu = True
    module.package_install = False
    module.refresh()
    assert isinstance(module.response, dict)
    assert module.device_name == "leaf1"
    assert module.err_message is None
    assert isinstance(module.epld_modules, dict)
    assert len(module.epld_modules.get("moduleList")) == 2
    assert module.install_option == "NA"
    assert module.install_packages is None
    assert module.ip_address == "172.22.150.102"
    assert module.os_type == "64bit"
    assert module.platform == "N9K/N3K"
    assert module.pre_issu_link == "Not Applicable"
    assert isinstance(module.raw_data, dict)
    assert isinstance(module.raw_response, dict)
    assert "compatibilityStatusList" in module.raw_data
    assert module.rep_status == "skipped"
    assert module.serial_number == "FDO21120U5D"
    assert module.status == "Skipped"
    assert module.timestamp == "NA"
    assert module.version == "10.2.5"
    assert module.version_check == "Compatibility status skipped."
    assert module.comp_disp == "Compatibility status skipped."
    assert module.result.get("success") == True


def test_image_mgmt_install_options_00009(monkeypatch, module) -> None:
    """
    Properties are updated based on:
    -   200 response from endpoint
    -   Device has no policy attached
    -   POST REQUEST
        - issu == False
        - epld == True
        - package_install == False

    endpoint: install-options
    """

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_install_options_00009a"
        return responses_image_install_options(key)

    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)

    module.policy_name = "KRM5"
    module.serial_number = "FDO21120U5D"
    module.epld = True
    module.issu = False
    module.package_install = False
    module.refresh()
    assert isinstance(module.response, dict)
    assert module.device_name is None
    assert module.err_message is None
    assert isinstance(module.epld_modules, dict)
    assert len(module.epld_modules.get("moduleList")) == 2
    assert module.install_option == None
    assert module.install_packages is None
    assert module.ip_address == None
    assert module.os_type == None
    assert module.platform == None
    assert module.pre_issu_link == None
    assert isinstance(module.raw_data, dict)
    assert isinstance(module.raw_response, dict)
    assert "compatibilityStatusList" in module.raw_data
    assert module.rep_status == None
    assert module.serial_number == "FDO21120U5D"
    assert module.status == None
    assert module.timestamp == None
    assert module.version == None
    assert module.version_check == None
    assert module.comp_disp == None
    assert module.result.get("success") == True


def test_image_mgmt_install_options_00010(monkeypatch, module) -> None:
    """
    Properties are updated based on:
    -   500 response from endpoint due to KR5M policy has no packages defined
        and package_install set to True
    -   KR5M policy is attached to the device
    -   POST REQUEST contains
        - issu == False
        - epld == True
        - package_install == True (this causes the expected error)

    endpoint: install-options
    """

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_install_options_00010a"
        return responses_image_install_options(key)

    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)

    module.policy_name = "KRM5"
    module.serial_number = "FDO21120U5D"
    module.epld = True
    module.issu = True
    module.package_install = True
    match = "Selected policy KR5M does not have package to continue."
    with pytest.raises(AnsibleFailJson, match=match):
        module.refresh()


# test_image_mgmt_install_options_00020


def test_image_mgmt_install_options_00020(module) -> None:
    """
    Payload contains defaults if not specified by the user.
    Defaults for issu, epld, and package_install are applied.
    """
    module.policy_name = "KRM5"
    module.serial_number = "BAR"
    module._build_payload()
    assert module.payload.get("devices")[0].get("policyName") == "KRM5"
    assert module.payload.get("devices")[0].get("serialNumber") == "BAR"
    assert module.payload.get("issu") == True
    assert module.payload.get("epld") == False
    assert module.payload.get("packageInstall") == False


# test_image_mgmt_install_options_00021


def test_image_mgmt_install_options_00021(module) -> None:
    """
    Payload contains user-specified values if the user sets them.
    Defaults for issu, epld, and package_install are overridden by user values.
    """
    module.policy_name = "KRM5"
    module.serial_number = "BAR"
    module.issu = False
    module.epld = True
    module.package_install = True
    module._build_payload()
    assert module.payload.get("devices")[0].get("policyName") == "KRM5"
    assert module.payload.get("devices")[0].get("serialNumber") == "BAR"
    assert module.payload.get("issu") == False
    assert module.payload.get("epld") == True
    assert module.payload.get("packageInstall") == True


# test_image_mgmt_install_options_00022


def test_image_mgmt_install_options_00022(module) -> None:
    """
    fail_json() is called if issu is not a boolean.
    """
    match = "ImageInstallOptions.issu.setter: issu must be a "
    match += "boolean value"
    with pytest.raises(AnsibleFailJson, match=match):
        module.issu = "FOO"


# test_image_mgmt_install_options_00023


def test_image_mgmt_install_options_00023(module) -> None:
    """
    fail_json() is called if epld is not a boolean.
    """
    match = "ImageInstallOptions.epld.setter: epld must be a "
    match += "boolean value"
    with pytest.raises(AnsibleFailJson, match=match):
        module.epld = "FOO"


# test_image_mgmt_install_options_00024


def test_image_mgmt_install_options_00024(module) -> None:
    """
    fail_json() is called if package_install is not a boolean.
    """
    match = "ImageInstallOptions.package_install.setter: "
    match += "package_install must be a boolean value"
    with pytest.raises(AnsibleFailJson, match=match):
        module.package_install = "FOO"
