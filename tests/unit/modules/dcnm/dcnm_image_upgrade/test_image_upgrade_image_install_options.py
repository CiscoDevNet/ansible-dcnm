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

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import \
    ApiEndpoints

from .image_upgrade_utils import (MockAnsibleModule, does_not_raise,
                                  image_install_options_fixture,
                                  responses_image_install_options)

PATCH_MODULE_UTILS = "ansible_collections.cisco.dcnm.plugins.module_utils."
PATCH_IMAGE_MGMT = PATCH_MODULE_UTILS + "image_mgmt."
DCNM_SEND_INSTALL_OPTIONS = PATCH_IMAGE_MGMT + "install_options.dcnm_send"


def test_image_mgmt_install_options_00001(image_install_options) -> None:
    """
    Function
    - __init__

    Test
    - fail_json is not called
    - Class attributes are initialized to expected values
    """
    with does_not_raise():
        instance = image_install_options
    assert instance.module == MockAnsibleModule
    assert instance.class_name == "ImageInstallOptions"
    assert isinstance(instance.endpoints, ApiEndpoints)


def test_image_mgmt_install_options_00002(image_install_options) -> None:
    """
    Function
    - _init_properties

    Test
    - Class properties are initialized to expected values
    """
    with does_not_raise():
        instance = image_install_options
    assert isinstance(instance.properties, dict)
    assert instance.properties.get("epld") is False
    assert instance.properties.get("epld_modules") is None
    assert instance.properties.get("issu") is True
    assert instance.properties.get("package_install") is False
    assert instance.properties.get("policy_name") is None
    assert instance.properties.get("response") is None
    assert instance.properties.get("response_data") is None
    assert instance.properties.get("result") is None
    assert instance.properties.get("serial_number") is None


def test_image_mgmt_install_options_00003(image_install_options) -> None:
    """
    Function
    - refresh
    - serial_number setter

    Test
    - fail_json is called because policy_name is not set when refresh is called
    - fail_json error message is matched
    """
    instance = image_install_options
    instance.serial_number = "FOO"
    match = "ImageInstallOptions.refresh: "
    match += "instance.policy_name must be set before "
    match += r"calling refresh\(\)"
    with pytest.raises(AnsibleFailJson, match=match):
        instance.refresh()


def test_image_mgmt_install_options_00004(image_install_options) -> None:
    """
    Function
    - refresh

    Test
    - fail_json is called because serial_number is not set when refresh is called
    - fail_json error message is matched
    """
    match = "ImageInstallOptions.refresh: "
    match += "instance.serial_number must be set before "
    match += r"calling refresh\(\)"

    instance = image_install_options
    instance.policy_name = "FOO"
    with pytest.raises(AnsibleFailJson, match=match):
        image_install_options.refresh()


def test_image_mgmt_install_options_00005(monkeypatch, image_install_options) -> None:
    """
    Function
    - refresh

    Test
    -   200 response from endpoint
    -   Properties are updated with expected values
    -   endpoint: install-options
    """

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_install_options_00005a"
        return responses_image_install_options(key)

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)

    instance = image_install_options
    instance.policy_name = "KRM5"
    instance.serial_number = "BAR"
    instance.refresh()
    assert isinstance(instance.response, dict)
    assert instance.device_name == "cvd-1314-leaf"
    assert instance.err_message is None
    assert instance.epld_modules is None
    assert instance.install_option == "disruptive"
    assert instance.install_packages is None
    assert instance.ip_address == "172.22.150.105"
    assert instance.os_type == "64bit"
    assert instance.platform == "N9K/N3K"
    assert instance.pre_issu_link == "Not Applicable"
    assert isinstance(instance.raw_data, dict)
    assert isinstance(instance.raw_response, dict)
    assert "compatibilityStatusList" in instance.raw_data
    assert instance.rep_status == "skipped"
    assert instance.serial_number == "BAR"
    assert instance.status == "Success"
    assert instance.timestamp == "NA"
    assert instance.version == "10.2.5"
    comp_disp = "show install all impact nxos bootflash:nxos64-cs.10.2.5.M.bin"
    assert instance.comp_disp == comp_disp
    assert instance.result.get("success") is True


def test_image_mgmt_install_options_00006(monkeypatch, image_install_options) -> None:
    """
    Function
    - refresh

    Test
    - fail_json is called because RETURN_CODE != 200 in the response
    """

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_install_options_00006a"
        return responses_image_install_options(key)

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)

    match = "ImageInstallOptions.refresh: "
    match += "Bad result when retrieving install-options from "
    match += "the controller. Controller response:"

    instance = image_install_options
    instance.policy_name = "KRM5"
    instance.serial_number = "BAR"
    with pytest.raises(AnsibleFailJson, match=rf"{match}"):
        instance.refresh()


def test_image_mgmt_install_options_00007(monkeypatch, image_install_options) -> None:
    """
    Function
    - refresh

    Setup
    -  Device has no policy attached
    -   POST REQUEST
        - issu is True
        - epld is False
        - package_install is False

    Test
    - 200 response from endpoint
    - Response contains expected values

    Endpoint
    - install-options
    """

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_install_options_00007a"
        return responses_image_install_options(key)

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)

    instance = image_install_options
    instance.policy_name = "KRM5"
    instance.serial_number = "FDO21120U5D"
    instance.refresh()
    assert isinstance(instance.response, dict)
    assert instance.device_name == "leaf1"
    assert instance.err_message is None
    assert instance.epld_modules is None
    assert instance.install_option == "NA"
    assert instance.install_packages is None
    assert instance.ip_address == "172.22.150.102"
    assert instance.os_type == "64bit"
    assert instance.platform == "N9K/N3K"
    assert instance.pre_issu_link == "Not Applicable"
    assert isinstance(instance.raw_data, dict)
    assert isinstance(instance.raw_response, dict)
    assert "compatibilityStatusList" in image_install_options.raw_data
    assert instance.rep_status == "skipped"
    assert instance.serial_number == "FDO21120U5D"
    assert instance.status == "Skipped"
    assert instance.timestamp == "NA"
    assert instance.version == "10.2.5"
    assert instance.version_check == "Compatibility status skipped."
    assert instance.comp_disp == "Compatibility status skipped."
    assert instance.result.get("success") is True


def test_image_mgmt_install_options_00008(monkeypatch, image_install_options) -> None:
    """
    Function
    - refresh

    Setup
    -  Device has no policy attached
    -   POST REQUEST
        - issu is True
        - epld is True
        - package_install is False

    Test
    - 200 response from endpoint
    - Response contains expected values

    Endpoint
    - install-options
    """

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_install_options_00008a"
        return responses_image_install_options(key)

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)

    instance = image_install_options
    instance.policy_name = "KRM5"
    instance.serial_number = "FDO21120U5D"
    instance.epld = True
    instance.issu = True
    instance.package_install = False
    instance.refresh()
    assert isinstance(instance.response, dict)
    assert instance.device_name == "leaf1"
    assert instance.err_message is None
    assert isinstance(instance.epld_modules, dict)
    assert len(instance.epld_modules.get("moduleList")) == 2
    assert instance.install_option == "NA"
    assert instance.install_packages is None
    assert instance.ip_address == "172.22.150.102"
    assert instance.os_type == "64bit"
    assert instance.platform == "N9K/N3K"
    assert instance.pre_issu_link == "Not Applicable"
    assert isinstance(instance.raw_data, dict)
    assert isinstance(instance.raw_response, dict)
    assert "compatibilityStatusList" in instance.raw_data
    assert instance.rep_status == "skipped"
    assert instance.serial_number == "FDO21120U5D"
    assert instance.status == "Skipped"
    assert instance.timestamp == "NA"
    assert instance.version == "10.2.5"
    assert instance.version_check == "Compatibility status skipped."
    assert instance.comp_disp == "Compatibility status skipped."
    assert instance.result.get("success") is True


def test_image_mgmt_install_options_00009(monkeypatch, image_install_options) -> None:
    """
    Function
    - refresh

    Setup
    -  Device has no policy attached
    -   POST REQUEST
        - issu is False
        - epld is True
        - package_install is False

    Test
    - 200 response from endpoint
    - Response contains expected values

    Endpoint
    - install-options
    """

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_install_options_00009a"
        return responses_image_install_options(key)

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)

    instance = image_install_options
    instance.policy_name = "KRM5"
    instance.serial_number = "FDO21120U5D"
    instance.epld = True
    instance.issu = False
    instance.package_install = False
    instance.refresh()
    assert isinstance(instance.response, dict)
    assert instance.device_name is None
    assert instance.err_message is None
    assert isinstance(instance.epld_modules, dict)
    assert len(instance.epld_modules.get("moduleList")) == 2
    assert instance.install_option is None
    assert instance.install_packages is None
    assert instance.ip_address is None
    assert instance.os_type is None
    assert instance.platform is None
    assert instance.pre_issu_link is None
    assert isinstance(instance.raw_data, dict)
    assert isinstance(instance.raw_response, dict)
    assert "compatibilityStatusList" in instance.raw_data
    assert instance.rep_status is None
    assert instance.serial_number == "FDO21120U5D"
    assert instance.status is None
    assert instance.timestamp is None
    assert instance.version is None
    assert instance.version_check is None
    assert instance.comp_disp is None
    assert instance.result.get("success") is True


def test_image_mgmt_install_options_00010(monkeypatch, image_install_options) -> None:
    """
    Function
    - refresh

    Setup
    -  Device has no policy attached
    -   POST REQUEST
        - issu is False
        - epld is True
        - package_install is True (causes expected error)

    Test
    -   500 response from endpoint due to
        - KR5M policy has no packages defined and
        - package_install set to True
    -   Response contains expected values

    Endpoint
    - install-options
    """

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_install_options_00010a"
        return responses_image_install_options(key)

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)

    match = "Selected policy KR5M does not have package to continue."

    instance = image_install_options
    instance.policy_name = "KRM5"
    instance.serial_number = "FDO21120U5D"
    instance.epld = True
    instance.issu = True
    instance.package_install = True
    with pytest.raises(AnsibleFailJson, match=match):
        instance.refresh()


def test_image_mgmt_install_options_00020(image_install_options) -> None:
    """
    Function
    - build_payload

    Setup
    - Defaults are not specified by the user

    Test
    - Default values for issu, epld, and package_install are applied
    """
    instance = image_install_options
    instance.policy_name = "KRM5"
    instance.serial_number = "BAR"
    instance._build_payload()  # pylint: disable=protected-access
    assert instance.payload.get("devices")[0].get("policyName") == "KRM5"
    assert instance.payload.get("devices")[0].get("serialNumber") == "BAR"
    assert instance.payload.get("issu") is True
    assert instance.payload.get("epld") is False
    assert instance.payload.get("packageInstall") is False


def test_image_mgmt_install_options_00021(image_install_options) -> None:
    """
    Function
    - build_payload

    Setup
    - Values are specified by the user

    Test
    - Payload contains user-specified values if the user sets them
    - Defaults for issu, epld, and package_install are overridden by user values.
    """
    instance = image_install_options
    instance.policy_name = "KRM5"
    instance.serial_number = "BAR"
    instance.issu = False
    instance.epld = True
    instance.package_install = True
    instance._build_payload()  # pylint: disable=protected-access
    assert instance.payload.get("devices")[0].get("policyName") == "KRM5"
    assert instance.payload.get("devices")[0].get("serialNumber") == "BAR"
    assert instance.payload.get("issu") is False
    assert instance.payload.get("epld") is True
    assert instance.payload.get("packageInstall") is True


def test_image_mgmt_install_options_00022(image_install_options) -> None:
    """
    Function
    - issu setter

    Test
    - fail_json is called if issu is not a boolean.
    """
    match = "ImageInstallOptions.issu.setter: issu must be a "
    match += "boolean value"

    instance = image_install_options
    with pytest.raises(AnsibleFailJson, match=match):
        instance.issu = "FOO"


def test_image_mgmt_install_options_00023(image_install_options) -> None:
    """
    Function
    - epld setter

    Test
    - fail_json is called if epld is not a boolean.
    """
    match = "ImageInstallOptions.epld.setter: epld must be a "
    match += "boolean value"

    instance = image_install_options
    with pytest.raises(AnsibleFailJson, match=match):
        instance.epld = "FOO"


def test_image_mgmt_install_options_00024(image_install_options) -> None:
    """
    Function
    - package_install setter

    Test
    - fail_json is called if package_install is not a boolean.
    """
    match = "ImageInstallOptions.package_install.setter: "
    match += "package_install must be a boolean value"

    instance = image_install_options
    with pytest.raises(AnsibleFailJson, match=match):
        instance.package_install = "FOO"
