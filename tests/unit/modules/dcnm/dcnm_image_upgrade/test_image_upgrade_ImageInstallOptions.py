"""
controller_version: 12
description: Verify functionality of class ImageInstallOptions
"""

from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
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


def test_policy_name_not_defined(module) -> None:
    """
    fail_json() is called if policy_name is not set when refresh() is called.
    """
    module.serial_number = "FOO"
    error_message = "ImageInstallOptions.refresh: "
    error_message += "instance.policy_name must be set before "
    error_message += r"calling refresh\(\)"
    with pytest.raises(AnsibleFailJson, match=error_message):
        module.refresh()


def test_serial_number_not_defined(module) -> None:
    """
    fail_json() is called if serial_number is not set when refresh() is called.
    """
    module.policy_name = "FOO"
    error_message = "ImageInstallOptions.refresh: "
    error_message += "instance.serial_number must be set before "
    error_message += r"calling refresh\(\)"
    with pytest.raises(AnsibleFailJson, match=error_message):
        module.refresh()


def test_refresh_return_code_200(monkeypatch, module) -> None:
    """
    Properties are updated based on 200 response from endpoint.
    endpoint: install-options
    """
    key = "imageupgrade_install_options_post_return_code_200"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_install_options(key)

    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)

    module.policy_name = "KRM5"
    module.serial_number = "BAR"
    module.refresh()
    assert isinstance(module.response, dict)
    assert module.device_name == "cvd-1314-leaf"
    assert module.err_message == ""
    assert module.epld_modules is None
    assert module.install_option == "disruptive"
    assert module.install_packages is None
    assert module.os_type == "64bit"
    assert module.platform == "N9K/N3K"
    assert module.serial_number == "BAR"
    assert module.version == "10.2.5"
    comp_disp = "show install all impact nxos bootflash:nxos64-cs.10.2.5.M.bin"
    assert module.comp_disp == comp_disp
    assert module.result.get("success") == True


def test_refresh_return_code_500(monkeypatch, module) -> None:
    """
    fail_json() should be called if the response RETURN_CODE != 200
    """
    key = "imageupgrade_install_options_post_return_code_500"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_install_options(key)

    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)

    module.policy_name = "KRM5"
    module.serial_number = "BAR"
    error_message = "ImageInstallOptions.refresh: "
    error_message += "Bad result when retrieving install-options from "
    error_message += "the controller. Controller response:"
    with pytest.raises(AnsibleFailJson, match=rf"{error_message}"):
        module.refresh()


def test_build_payload_defaults(module) -> None:
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


def test_build_payload_user_changed_defaults(module) -> None:
    """
    Payload contains user-specified values if the user sets them.
    Defaults for issu, epld, and package_install overridden by user values.
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


def test_invalid_value_issu(module) -> None:
    """
    fail_json() is called if issu is not a boolean.
    """
    error_message = "ImageInstallOptions.issu.setter: issu must be a "
    error_message += "boolean value"
    with pytest.raises(AnsibleFailJson, match=error_message):
        module.issu = "FOO"


def test_invalid_value_epld(module) -> None:
    """
    fail_json() is called if epld is not a boolean.
    """
    error_message = "ImageInstallOptions.epld.setter: epld must be a "
    error_message += "boolean value"
    with pytest.raises(AnsibleFailJson, match=error_message):
        module.epld = "FOO"


def test_invalid_value_package_install(module) -> None:
    """
    fail_json() is called if package_install is not a boolean.
    """
    error_message = "ImageInstallOptions.package_install.setter: "
    error_message += "package_install must be a boolean value"
    with pytest.raises(AnsibleFailJson, match=error_message):
        module.package_install = "FOO"
