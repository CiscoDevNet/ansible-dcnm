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

import logging
from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.common.mock_rest_send import \
    MockRestSend as MockRestSendImageUpgrade
from ansible_collections.cisco.dcnm.plugins.module_utils.common.mock_rest_send import \
    MockRestSend as MockRestSendInstallOptions
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_upgrade import \
    ImageUpgrade

from .image_upgrade_utils import (MockAnsibleModule, does_not_raise,
                                  image_upgrade_fixture,
                                  issu_details_by_ip_address_fixture,
                                  payloads_image_upgrade,
                                  responses_image_install_options,
                                  responses_image_upgrade,
                                  responses_switch_issu_details)

PATCH_MODULE_UTILS = "ansible_collections.cisco.dcnm.plugins.module_utils."
PATCH_IMAGE_MGMT = PATCH_MODULE_UTILS + "image_mgmt."

REST_SEND_IMAGE_UPGRADE = PATCH_IMAGE_MGMT + "image_upgrade.RestSend"
DCNM_SEND_IMAGE_UPGRADE_COMMON = PATCH_IMAGE_MGMT + "image_upgrade_common.dcnm_send"
DCNM_SEND_INSTALL_OPTIONS = PATCH_IMAGE_MGMT + "install_options.dcnm_send"
DCNM_SEND_ISSU_DETAILS = PATCH_IMAGE_MGMT + "switch_issu_details.dcnm_send"


def test_image_mgmt_upgrade_00001(image_upgrade) -> None:
    """
    Function
    - __init__

    Test
    - Class attributes are initialized to expected values
    """
    instance = image_upgrade
    assert isinstance(instance, ImageUpgrade)
    assert isinstance(instance.ipv4_done, set)
    assert isinstance(instance.ipv4_todo, set)
    assert isinstance(instance.payload, dict)
    assert instance.class_name == "ImageUpgrade"
    assert (
        instance.path
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imageupgrade/upgrade-image"
    )
    assert instance.verb == "POST"


def test_image_mgmt_upgrade_00003(image_upgrade) -> None:
    """
    Function
    - _init_properties

    Test
    - Class properties are initialized to expected values
    """
    instance = image_upgrade
    instance._init_properties()
    assert isinstance(instance.properties, dict)
    assert instance.properties.get("bios_force") is False
    assert instance.properties.get("check_interval") == 10
    assert instance.properties.get("check_timeout") == 1800
    assert instance.properties.get("config_reload") is False
    assert instance.properties.get("devices") is None
    assert instance.properties.get("disruptive") is True
    assert instance.properties.get("epld_golden") is False
    assert instance.properties.get("epld_module") == "ALL"
    assert instance.properties.get("epld_upgrade") is False
    assert instance.properties.get("force_non_disruptive") is False
    assert instance.properties.get("response_data") == []
    assert instance.properties.get("response") == []
    assert instance.properties.get("result") == []
    assert instance.properties.get("non_disruptive") is False
    assert instance.properties.get("force_non_disruptive") is False
    assert instance.properties.get("package_install") is False
    assert instance.properties.get("package_uninstall") is False
    assert instance.properties.get("reboot") is False
    assert instance.properties.get("write_erase") is False
    assert instance.valid_nxos_mode == {
        "disruptive",
        "non_disruptive",
        "force_non_disruptive",
    }


def test_image_mgmt_upgrade_00004(monkeypatch, image_upgrade) -> None:
    """
    Function
    - validate_devices

    Test
    -   ip_addresses contains the ip addresses of the devices for which
        validation succeeds

    Description
    ImageUpgrade.validate_devices updates the set ImageUpgrade.ip_addresses
    with the ip addresses of the devices for which validation succeeds.
    Currently, validation succeeds for all devices.  This function may be
    updated in the future to handle various failure scenarios.

    Expected results:

    1.  instance.ip_addresses will contain {"172.22.150.102", "172.22.150.108"}
    """
    devices = [{"ip_address": "172.22.150.102"}, {"ip_address": "172.22.150.108"}]

    instance = image_upgrade
    instance.devices = devices

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_upgrade_00004a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    instance._validate_devices()  # pylint: disable=protected-access
    assert isinstance(instance.ip_addresses, set)
    assert len(instance.ip_addresses) == 2
    assert "172.22.150.102" in instance.ip_addresses
    assert "172.22.150.108" in instance.ip_addresses


def test_image_mgmt_upgrade_00005(image_upgrade) -> None:
    """
    Function
    - commit

    Test
    - fail_json is called because devices is None
    """
    instance = image_upgrade

    match = (
        "ImageUpgrade._validate_devices: call instance.devices before calling commit."
    )
    with pytest.raises(AnsibleFailJson, match=match):
        instance.unit_test = True
        instance.commit()


def test_image_mgmt_upgrade_00018(monkeypatch, image_upgrade) -> None:
    """
    Function
    - ImageUpgrade.commit

    Test
    - upgrade.nxos set to invalid value

    Setup
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded.
    -   The methods called by commit are mocked to simulate that the
        the image has already been staged and validated and the device
        has already been upgraded to the desired version.
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing.

    Expected results:

    1.  commit will call _build_payload which will call fail_json
    """
    instance = image_upgrade

    key = "test_image_mgmt_upgrade_00019a"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_dcnm_send_image_upgrade_commit(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_upgrade(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(
        DCNM_SEND_IMAGE_UPGRADE_COMMON, mock_dcnm_send_image_upgrade_commit
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "KR5M",
            "stage": True,
            "upgrade": {"nxos": "FOO", "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": True},
                "package": {"install": False, "uninstall": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": False,
        }
    ]
    match = r"ImageUpgrade._build_payload_issu_upgrade: upgrade.nxos must be a boolean. Got FOO\."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.unit_test = True
        instance.commit()


def test_image_mgmt_upgrade_00019(monkeypatch, image_upgrade, caplog) -> None:
    """
    Function
    - ImageUpgrade._build_payload

    Test
    - non-default values are set for several options
    - policy_changed is set to False
    - Verify that payload is built correctly


    Setup
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded.
    -   commit -> _build_payload -> issu_details is mocked to simulate
        that the the image has already been staged and validated and the
        device has already been upgraded to the desired version.
    -   commit -> _build_payload -> install_options is mocked to simulate
        that the the image EPLD does not need upgrade.
    -   The following methods, called by commit() are mocked to do nothing:
        - _wait_for_current_actions_to_complete
        - _wait_for_image_upgrade_to_complete
    -   RestSend is mocked to return a successful response


    Expected results:

    1.  instance.payload (built by instance._build_payload and based on
        instance.devices) will equal a payload previously obtained by running
        ansible-playbook against the controller for this scenario, which verifies
        that the non-default values are included in the payload.
    """
    caplog.set_level(logging.DEBUG)
    instance = image_upgrade

    key = "test_image_mgmt_upgrade_00019a"
    image_upgrade_file = "image_upgrade_responses_ImageUpgrade"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(REST_SEND_IMAGE_UPGRADE, MockRestSendImageUpgrade)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "KR5M",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": False, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": True},
                "package": {"install": True, "uninstall": False},
                "epld": {"module": 1, "golden": True},
                "reboot": {"config_reload": True, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": False,
        }
    ]
    MockRestSendImageUpgrade.key = key
    MockRestSendImageUpgrade.file = image_upgrade_file

    instance.unit_test = True
    instance.commit()

    assert instance.payload == payloads_image_upgrade(key)


def test_image_mgmt_upgrade_00020(monkeypatch, image_upgrade, caplog) -> None:
    """
    Function
    - ImageUpgrade.commit

    Test
    - User explicitely sets default values for several options
    - policy_changed is set to True

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   commit -> _build_payload -> issu_details is mocked to simulate
        that the the image has already been staged and validated and the
        device has already been upgraded to the desired version.
    -   commit -> _build_payload -> install_options is mocked to simulate
        that the the image EPLD does not need upgrade.
    -   The following methods, called by commit() are mocked to do nothing:
        - _wait_for_current_actions_to_complete
        - _wait_for_image_upgrade_to_complete
    -   RestSend is mocked to return a successful response


    Expected results:

    1.  instance.payload will equal a payload previously obtained by
        running ansible-playbook against the controller for this scenario
    """
    caplog.set_level(logging.DEBUG)
    instance = image_upgrade

    key = "test_image_mgmt_upgrade_00020a"
    image_upgrade_file = "image_upgrade_responses_ImageUpgrade"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(REST_SEND_IMAGE_UPGRADE, MockRestSendImageUpgrade)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": False},
                "package": {"install": True, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    MockRestSendImageUpgrade.key = key
    MockRestSendImageUpgrade.file = image_upgrade_file

    instance.unit_test = True
    instance.commit()
    assert instance.payload == payloads_image_upgrade(key)


def test_image_mgmt_upgrade_00021(monkeypatch, image_upgrade) -> None:
    """
    Function
    - commit

    Test
    - Invalid value for nxos.mode

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    -   instance.devices is set to contain an invalid nxos.mode value

    Expected results:

    1.  commit calls _build_payload, which calls fail_json
    """
    instance = image_upgrade

    key = "test_image_mgmt_upgrade_00021a"
    image_upgrade_file = "image_upgrade_responses_ImageUpgrade"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(REST_SEND_IMAGE_UPGRADE, MockRestSendImageUpgrade)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "FOO", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    MockRestSendImageUpgrade.key = key
    MockRestSendImageUpgrade.file = image_upgrade_file

    match = "ImageUpgrade._build_payload_issu_options_1: "
    match += "options.nxos.mode must be one of "
    match += r"\['disruptive', 'force_non_disruptive', 'non_disruptive'\]. "
    match += "Got FOO."
    instance.unit_test = True
    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()


def test_image_mgmt_upgrade_00022(monkeypatch, image_upgrade) -> None:
    """
    Function
    - commit

    Test
    - Force code coverage of nxos.mode == "non_disruptive" path

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    -   instance.devices is set to contain nxos.mode non_disruptive
        forcing the code to take nxos_mode == "non_disruptive" path

    Expected results:

    1.  self.payload["issuUpgradeOptions1"]["disruptive"] is False
    2.  self.payload["issuUpgradeOptions1"]["forceNonDisruptive"] is False
    3.  self.payload["issuUpgradeOptions1"]["nonDisruptive"] is True
    """
    instance = image_upgrade

    key = "test_image_mgmt_upgrade_00022a"
    image_upgrade_file = "image_upgrade_responses_ImageUpgrade"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(REST_SEND_IMAGE_UPGRADE, MockRestSendImageUpgrade)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "non_disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    MockRestSendImageUpgrade.key = key
    MockRestSendImageUpgrade.file = image_upgrade_file

    instance.unit_test = True
    instance.commit()
    assert instance.payload["issuUpgradeOptions1"]["disruptive"] is False
    assert instance.payload["issuUpgradeOptions1"]["forceNonDisruptive"] is False
    assert instance.payload["issuUpgradeOptions1"]["nonDisruptive"] is True


def test_image_mgmt_upgrade_00023(monkeypatch, image_upgrade) -> None:
    """
    Function
    - commit

    Test
    - Force code coverage of nxos.mode == "force_non_disruptive" path

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    -   instance.devices is set to contain nxos.mode force_non_disruptive
        forcing the code to take nxos_mode == "force_non_disruptive" path

    Expected results:

    1.  self.payload["issuUpgradeOptions1"]["disruptive"] is False
    2.  self.payload["issuUpgradeOptions1"]["forceNonDisruptive"] is True
    3.  self.payload["issuUpgradeOptions1"]["nonDisruptive"] is False
    """
    instance = image_upgrade

    key = "test_image_mgmt_upgrade_00023a"
    image_upgrade_file = "image_upgrade_responses_ImageUpgrade"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(REST_SEND_IMAGE_UPGRADE, MockRestSendImageUpgrade)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "force_non_disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    MockRestSendImageUpgrade.key = key
    MockRestSendImageUpgrade.file = image_upgrade_file

    instance.unit_test = True
    instance.commit()
    assert instance.payload["issuUpgradeOptions1"]["disruptive"] is False
    assert instance.payload["issuUpgradeOptions1"]["forceNonDisruptive"] is True
    assert instance.payload["issuUpgradeOptions1"]["nonDisruptive"] is False


def test_image_mgmt_upgrade_00024(monkeypatch, image_upgrade) -> None:
    """
    Function
    - commit

    Test
    - Invalid value for options.nxos.bios_force

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    -   instance.devices is set to contain invalid value for
        options.nxos.bios_force

    Expected results:

    1.  commit calls _build_payload which calls fail_json
    """
    instance = image_upgrade

    key = "test_image_mgmt_upgrade_00024a"
    image_upgrade_file = "image_upgrade_responses_ImageUpgrade"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(REST_SEND_IMAGE_UPGRADE, MockRestSendImageUpgrade)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": "FOO"},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    MockRestSendImageUpgrade.key = key
    MockRestSendImageUpgrade.file = image_upgrade_file

    match = "ImageUpgrade._build_payload_issu_options_2: "
    match += r"options.nxos.bios_force must be a boolean. Got FOO\."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.unit_test = True
        instance.commit()


def test_image_mgmt_upgrade_00025(monkeypatch, image_upgrade) -> None:
    """
    Function
    - commit

    Test
    - Incompatible values for options.epld.golden and upgrade.nxos

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    -   instance.devices is set to contain epld golden True and
        upgrade.nxos True.

    Expected results:

    1.  commit calls _build_payload which calls fail_json
    """
    instance = image_upgrade

    key = "test_image_mgmt_upgrade_00025a"
    image_upgrade_file = "image_upgrade_responses_ImageUpgrade"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(REST_SEND_IMAGE_UPGRADE, MockRestSendImageUpgrade)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": True},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]
    MockRestSendImageUpgrade.key = key
    MockRestSendImageUpgrade.file = image_upgrade_file

    match = "ImageUpgrade._build_payload_epld: Invalid configuration for "
    match += "172.22.150.102. If options.epld.golden is True "
    match += "all other upgrade options, e.g. upgrade.nxos, "
    match += "must be False."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.unit_test = True
        instance.commit()


def test_image_mgmt_upgrade_00026(monkeypatch, image_upgrade) -> None:
    """
    Function
    - commit

    Test
    - Invalid value for epld.module

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    -   instance.devices is set to contain invalid epld.module

    Expected results:

    1.  commit calls _build_payload which calls fail_json
    """
    instance = image_upgrade

    key = "test_image_mgmt_upgrade_00026a"
    image_upgrade_file = "image_upgrade_responses_ImageUpgrade"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(REST_SEND_IMAGE_UPGRADE, MockRestSendImageUpgrade)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "FOO", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    MockRestSendImageUpgrade.key = key
    MockRestSendImageUpgrade.file = image_upgrade_file

    match = "ImageUpgrade._build_payload_epld: "
    match += "options.epld.module must either be 'ALL' "
    match += r"or an integer. Got FOO\."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.unit_test = True
        instance.commit()


def test_image_mgmt_upgrade_00027(monkeypatch, image_upgrade) -> None:
    """
    Function
    - commit

    Test
    - Invalid value for epld.golden

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    -   instance.devices is set to contain invalid epld.golden

    Expected results:

    1.  commit calls _build_payload which calls fail_json
    """
    instance = image_upgrade

    key = "test_image_mgmt_upgrade_00027a"
    image_upgrade_file = "image_upgrade_responses_ImageUpgrade"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(REST_SEND_IMAGE_UPGRADE, MockRestSendImageUpgrade)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": "FOO"},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]
    MockRestSendImageUpgrade.key = key
    MockRestSendImageUpgrade.file = image_upgrade_file

    match = "ImageUpgrade._build_payload_epld: "
    match += r"options.epld.golden must be a boolean. Got FOO\."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.unit_test = True
        instance.commit()


def test_image_mgmt_upgrade_00028(monkeypatch, image_upgrade) -> None:
    """
    Function
    - commit

    Test
    - Invalid value for reboot

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    -   instance.devices is set to contain invalid value for reboot

    Expected results:

    1.  commit calls _build_payload which calls fail_json
    """
    instance = image_upgrade

    key = "test_image_mgmt_upgrade_00028a"
    image_upgrade_file = "image_upgrade_responses_ImageUpgrade"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(REST_SEND_IMAGE_UPGRADE, MockRestSendImageUpgrade)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": "FOO",
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    MockRestSendImageUpgrade.key = key
    MockRestSendImageUpgrade.file = image_upgrade_file

    match = "ImageUpgrade._build_payload_reboot: "
    match += r"reboot must be a boolean. Got FOO\."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.unit_test = True
        instance.commit()


def test_image_mgmt_upgrade_00029(monkeypatch, image_upgrade) -> None:
    """
    Function
    - commit

    Test
    - Invalid value for options.reboot.config_reload

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    -   instance.devices is set to contain invalid value for
        options.reboot.config_reload

    Expected results:

    1.  commit calls _build_payload which calls fail_json
    """
    instance = image_upgrade

    key = "test_image_mgmt_upgrade_00029a"
    image_upgrade_file = "image_upgrade_responses_ImageUpgrade"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(REST_SEND_IMAGE_UPGRADE, MockRestSendImageUpgrade)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": True,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": "FOO", "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    MockRestSendImageUpgrade.key = key
    MockRestSendImageUpgrade.file = image_upgrade_file

    match = "ImageUpgrade._build_payload_reboot_options: "
    match += r"options.reboot.config_reload must be a boolean. Got FOO\."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.unit_test = True
        instance.commit()


def test_image_mgmt_upgrade_00030(monkeypatch, image_upgrade) -> None:
    """
    Function
    - commit

    Test
    - Invalid value for options.reboot.write_erase

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    -   instance.devices is set to contain invalid value for
        options.reboot.write_erase

    Expected results:

    1.  commit calls _build_payload which calls fail_json
    """
    instance = image_upgrade

    key = "test_image_mgmt_upgrade_00030a"
    image_upgrade_file = "image_upgrade_responses_ImageUpgrade"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(REST_SEND_IMAGE_UPGRADE, MockRestSendImageUpgrade)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": True,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": "FOO"},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    MockRestSendImageUpgrade.key = key
    MockRestSendImageUpgrade.file = image_upgrade_file

    match = "ImageUpgrade._build_payload_reboot_options: "
    match += r"options.reboot.write_erase must be a boolean. Got FOO\."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.unit_test = True
        instance.commit()


def test_image_mgmt_upgrade_00031(monkeypatch, image_upgrade) -> None:
    """
    Function
    - commit
    Test
    - Invalid value for options.package.uninstall

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    -   instance.devices is set to contain invalid value for
        options.package.uninstall

    Expected results:

    1.  commit calls _build_payload which calls fail_json

    NOTES:
    1. The corresponding test for options.package.install is missing.
        It's not needed since ImageInstallOptions will call fail_json
        on invalid values before ImageUpgrade has a chance to verify
        the value.
    """
    instance = image_upgrade

    key = "test_image_mgmt_upgrade_00031a"
    image_upgrade_file = "image_upgrade_responses_ImageUpgrade"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(REST_SEND_IMAGE_UPGRADE, MockRestSendImageUpgrade)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": True,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": "FOO"},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    MockRestSendImageUpgrade.key = key
    MockRestSendImageUpgrade.file = image_upgrade_file

    match = "ImageUpgrade._build_payload_package: "
    match += r"options.package.uninstall must be a boolean. Got FOO\."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.unit_test = True
        instance.commit()


def test_image_mgmt_upgrade_00032(monkeypatch, image_upgrade) -> None:
    """
    Function
    - commit

    Test
    - Bad result code in image upgrade response

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    -   ImageUpgrade response (mock_dcnm_send_image_upgrade_commit) is set
        to return RESULT_CODE 500 with MESSAGE "Internal Server Error"

    Expected results:

    1.  commit calls fail_json because self.result will not equal "success"

    """
    instance = image_upgrade

    key = "test_image_mgmt_upgrade_00032a"
    image_upgrade_file = "image_upgrade_responses_ImageUpgrade"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(REST_SEND_IMAGE_UPGRADE, MockRestSendImageUpgrade)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]
    MockRestSendImageUpgrade.key = key
    MockRestSendImageUpgrade.file = image_upgrade_file
    MockRestSendImageUpgrade.unit_test = True

    match = "ImageUpgrade.commit: failed: "
    match += r"\{'success': False, 'changed': False\}. "
    match += r"Controller response: \{'DATA': 123, "
    match += "'MESSAGE': 'Internal Server Error', 'METHOD': 'POST', "
    match += "'REQUEST_PATH': "
    match += "'https://172.22.150.244:443/appcenter/cisco/ndfc/api/v1/"
    match += "imagemanagement/rest/imageupgrade/upgrade-image', "
    match += r"'RETURN_CODE': 500\}"
    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()


def test_image_mgmt_upgrade_00033(monkeypatch, image_upgrade) -> None:
    """
    Function
    - commit

    Test
    - Invalid value for upgrade.epld

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    -   instance.devices is set to contain invalid value for
        upgrade.epld

    Expected results:

    1.  commit calls _build_payload which calls fail_json
    """
    instance = image_upgrade

    key = "test_image_mgmt_upgrade_00033a"
    image_upgrade_file = "image_upgrade_responses_ImageUpgrade"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(REST_SEND_IMAGE_UPGRADE, MockRestSendImageUpgrade)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "NR3F",
            "stage": True,
            "upgrade": {"nxos": True, "epld": "FOO"},
            "options": {
                "package": {
                    "uninstall": False,
                }
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    MockRestSendImageUpgrade.key = key
    MockRestSendImageUpgrade.file = image_upgrade_file

    match = "ImageInstallOptions.epld: "
    match += r"epld must be a boolean value. Got FOO\."
    with pytest.raises(AnsibleFailJson, match=match):
        instance.unit_test = True
        instance.commit()


# test getter properties


def test_image_mgmt_upgrade_00043(image_upgrade) -> None:
    """
    Function
    - check_interval
    """
    instance = image_upgrade
    assert instance.check_interval == 10


def test_image_mgmt_upgrade_00044(image_upgrade) -> None:
    """
    Function
    - check_timeout
    """
    instance = image_upgrade
    assert instance.check_timeout == 1800


def test_image_mgmt_upgrade_00045(monkeypatch, image_upgrade) -> None:
    """
    Function
    - response_data

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded.
    -   The methods called by commit are mocked to simulate that the
        the image has already been staged and validated and the device
        has already been upgraded to the desired version.
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing.


    Expected results:

    1.  instance.response_data == 121
    """
    instance = image_upgrade

    key = "test_image_mgmt_upgrade_00045a"
    image_upgrade_file = "image_upgrade_responses_ImageUpgrade"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return {}

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_dcnm_send_image_upgrade_commit(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_upgrade(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(REST_SEND_IMAGE_UPGRADE, MockRestSendImageUpgrade)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    MockRestSendImageUpgrade.key = key
    MockRestSendImageUpgrade.file = image_upgrade_file

    # instance.unit_test = True
    instance.commit()
    assert instance.response_data == [121]


def test_image_mgmt_upgrade_00046(monkeypatch, image_upgrade) -> None:
    """
    Function
    - result_current
    - result

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded.
    -   The methods called by commit are mocked to simulate that the
        the image has already been staged and validated and the device
        has already been upgraded to the desired version.
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing.


    Expected results:

    1. instance.rest_send.result_current == {'success': True, 'changed': True}
    1. instance.rest_send.result == [{'success': True, 'changed': True}]
    """
    instance = image_upgrade

    key = "test_image_mgmt_upgrade_00046a"
    image_upgrade_file = "image_upgrade_responses_ImageUpgrade"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return {}

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(REST_SEND_IMAGE_UPGRADE, MockRestSendImageUpgrade)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "KR5M",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": False, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": True},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": False,
        }
    ]

    MockRestSendImageUpgrade.key = key
    MockRestSendImageUpgrade.file = image_upgrade_file

    instance.unit_test = True
    instance.commit()
    assert instance.rest_send.result_current == {"success": True, "changed": True}
    assert instance.rest_send.result == [{"success": True, "changed": True}]


def test_image_mgmt_upgrade_00047(monkeypatch, image_upgrade) -> None:
    """
    Function
    - response

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded.
    -   The methods called by commit are mocked to simulate that the
        the image has already been staged and validated and the device
        has already been upgraded to the desired version.
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing.


    Expected results:

    1. instance.response is a list
    """
    instance = image_upgrade

    key = "test_image_mgmt_upgrade_00047a"
    image_upgrade_file = "image_upgrade_responses_ImageUpgrade"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return {}

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(REST_SEND_IMAGE_UPGRADE, MockRestSendImageUpgrade)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "KR5M",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": False, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": True},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": False,
        }
    ]

    MockRestSendImageUpgrade.key = key
    MockRestSendImageUpgrade.file = image_upgrade_file

    # instance.unit_test = True
    instance.commit()
    print(f"instance.response: {instance.response}")
    assert isinstance(instance.response, list)
    assert instance.response[0]["DATA"] == 121


# setters

MATCH_00060 = "ImageUpgrade.bios_force: instance.bios_force must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00060)),
    ],
)
def test_image_mgmt_upgrade_00060(image_upgrade, value, expected) -> None:
    """
    Function
    - bios_force setter
    """
    instance = image_upgrade

    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=MATCH_00060):
            instance.bios_force = value
    else:
        instance.bios_force = value
        assert instance.bios_force == expected


MATCH_00061 = "ImageUpgrade.config_reload: "
MATCH_00061 += "instance.config_reload must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00061)),
    ],
)
def test_image_mgmt_upgrade_00061(image_upgrade, value, expected) -> None:
    """
    Function
    - config_reload setter
    """
    instance = image_upgrade

    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=MATCH_00061):
            instance.config_reload = value
    else:
        instance.config_reload = value
        assert instance.config_reload == expected


MATCH_00062_COMMON = "ImageUpgrade.devices: "
MATCH_00062_COMMON += "instance.devices must be a python list of dict"

MATCH_00062_FAIL_1 = f"{MATCH_00062_COMMON}. Got not a list."
MATCH_00062_FAIL_2 = rf"{MATCH_00062_COMMON}. Got \['not a dict'\]."

MATCH_00062_FAIL_3 = f"{MATCH_00062_COMMON}, where each dict contains "
MATCH_00062_FAIL_3 += "the following keys: ip_address. "
MATCH_00062_FAIL_3 += r"Got \[\{'bad_key_ip_address': '192.168.1.1'\}\]."

DATA_00062_PASS = [{"ip_address": "192.168.1.1"}]
DATA_00062_FAIL_1 = "not a list"
DATA_00062_FAIL_2 = ["not a dict"]
DATA_00062_FAIL_3 = [{"bad_key_ip_address": "192.168.1.1"}]


@pytest.mark.parametrize(
    "value, expected",
    [
        (DATA_00062_PASS, does_not_raise()),
        (DATA_00062_FAIL_1, pytest.raises(AnsibleFailJson, match=MATCH_00062_FAIL_1)),
        (DATA_00062_FAIL_2, pytest.raises(AnsibleFailJson, match=MATCH_00062_FAIL_2)),
        (DATA_00062_FAIL_3, pytest.raises(AnsibleFailJson, match=MATCH_00062_FAIL_3)),
    ],
)
def test_image_mgmt_upgrade_00062(image_upgrade, value, expected) -> None:
    """
    Function
    - devices setter
    """
    instance = image_upgrade

    with expected:
        instance.devices = value


MATCH_00063 = "ImageUpgrade.disruptive: "
MATCH_00063 += "instance.disruptive must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00063)),
    ],
)
def test_image_mgmt_upgrade_00063(image_upgrade, value, expected) -> None:
    """
    Function
    - disruptive setter
    """
    instance = image_upgrade

    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=MATCH_00063):
            instance.disruptive = value
    else:
        instance.disruptive = value
        assert instance.disruptive == expected


MATCH_00064 = "ImageUpgrade.epld_golden: "
MATCH_00064 += "instance.epld_golden must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00064)),
    ],
)
def test_image_mgmt_upgrade_00064(image_upgrade, value, expected) -> None:
    """
    Function
    - epld_golden setter
    """
    instance = image_upgrade

    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=MATCH_00064):
            instance.epld_golden = value
    else:
        instance.epld_golden = value
        assert instance.epld_golden == expected


MATCH_00065 = "ImageUpgrade.epld_upgrade: "
MATCH_00065 += "instance.epld_upgrade must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00065)),
    ],
)
def test_image_mgmt_upgrade_00065(image_upgrade, value, expected) -> None:
    """
    Function
    - epld_upgrade setter
    """
    instance = image_upgrade

    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=MATCH_00065):
            instance.epld_upgrade = value
    else:
        instance.epld_upgrade = value
        assert instance.epld_upgrade == expected


MATCH_00066_FAIL_1 = "ImageUpgrade.epld_module: "
MATCH_00066_FAIL_1 += "instance.epld_module must be an integer or 'ALL'"


@pytest.mark.parametrize(
    "value, expected",
    [
        ("ALL", does_not_raise()),
        (1, does_not_raise()),
        (27, does_not_raise()),
        ("27", does_not_raise()),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00066_FAIL_1)),
    ],
)
def test_image_mgmt_upgrade_00066(image_upgrade, value, expected) -> None:
    """
    Function
    - epld_module setter
    """
    instance = image_upgrade
    with expected:
        instance.epld_module = value


MATCH_00067 = "ImageUpgrade.force_non_disruptive: "
MATCH_00067 += "instance.force_non_disruptive must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00067)),
    ],
)
def test_image_mgmt_upgrade_00067(image_upgrade, value, expected) -> None:
    """
    Function
    - force_non_disruptive setter
    """
    instance = image_upgrade

    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=MATCH_00067):
            instance.force_non_disruptive = value
    else:
        instance.force_non_disruptive = value
        assert instance.force_non_disruptive == expected


MATCH_00068 = "ImageUpgrade.non_disruptive: "
MATCH_00068 += "instance.non_disruptive must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00068)),
    ],
)
def test_image_mgmt_upgrade_00068(image_upgrade, value, expected) -> None:
    """
    Function
    - non_disruptive setter
    """
    instance = image_upgrade

    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=MATCH_00068):
            instance.non_disruptive = value
    else:
        instance.non_disruptive = value
        assert instance.non_disruptive == expected


MATCH_00069 = "ImageUpgrade.package_install: "
MATCH_00069 += "instance.package_install must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00069)),
    ],
)
def test_image_mgmt_upgrade_00069(image_upgrade, value, expected) -> None:
    """
    Function
    - package_install setter
    """
    instance = image_upgrade

    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=MATCH_00069):
            instance.package_install = value
    else:
        instance.package_install = value
        assert instance.package_install == expected


MATCH_00070 = "ImageUpgrade.package_uninstall: "
MATCH_00070 += "instance.package_uninstall must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00070)),
    ],
)
def test_image_mgmt_upgrade_00070(image_upgrade, value, expected) -> None:
    """
    Function
    - package_uninstall setter
    """
    instance = image_upgrade

    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=MATCH_00070):
            instance.package_uninstall = value
    else:
        instance.package_uninstall = value
        assert instance.package_uninstall == expected


MATCH_00071 = "ImageUpgrade.reboot: "
MATCH_00071 += "instance.reboot must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00071)),
    ],
)
def test_image_mgmt_upgrade_00071(image_upgrade, value, expected) -> None:
    """
    Function
    - reboot setter
    """
    instance = image_upgrade

    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=MATCH_00071):
            instance.reboot = value
    else:
        instance.reboot = value
        assert instance.reboot == expected


MATCH_00072 = "ImageUpgrade.write_erase: "
MATCH_00072 += "instance.write_erase must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=MATCH_00072)),
    ],
)
def test_image_mgmt_upgrade_00072(image_upgrade, value, expected) -> None:
    """
    Function
    - write_erase setter
    """
    instance = image_upgrade

    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=MATCH_00072):
            instance.write_erase = value
    else:
        instance.write_erase = value
        assert instance.write_erase == expected


def test_image_mgmt_upgrade_00080(
    monkeypatch, image_upgrade, issu_details_by_ip_address
) -> None:
    """
    Function
    - _wait_for_current_actions_to_complete

    Test
    - Two switches are added to ipv4_done

    Description
    _wait_for_current_actions_to_complete waits until staging, validation,
    and upgrade actions are complete for all ip addresses.  It calls
    SwitchIssuDetailsByIpAddress.actions_in_progress() and expects
    this to return False.  actions_in_progress() returns True until none of
    the following keys has a value of "In-Progress":

    ["imageStaged", "upgrade", "validated"]

    Expectations:
    1.  instance.ipv4_done is a set()
    2.  instance.ipv4_done is length 2
    3.  instance.ipv4_done contains all ip addresses in
        instance.ip_addresses
    4.  fail_json is not called
    """
    instance = image_upgrade

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_upgrade_00080a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    instance.issu_detail = issu_details_by_ip_address
    instance.ip_addresses = [
        "172.22.150.102",
        "172.22.150.108",
    ]
    instance.check_interval = 0
    with does_not_raise():
        instance._wait_for_current_actions_to_complete()
    assert isinstance(instance.ipv4_done, set)
    assert len(instance.ipv4_done) == 2
    assert "172.22.150.102" in instance.ipv4_done
    assert "172.22.150.108" in instance.ipv4_done


def test_image_mgmt_upgrade_00081(
    monkeypatch, image_upgrade, issu_details_by_ip_address
) -> None:
    """
    Function
    - _wait_for_current_actions_to_complete

    Test
    - one switch is added to ipv4_done
    - fail_json is called due to timeout

    See test_image_mgmt_upgrade_00080 for functional details.

    Expectations:
    - instance.ipv4_done is a set()
    - instance.ipv4_done is length 1
    - instance.ipv4_done contains 172.22.150.102
    - instance.ipv4_done does not contain 172.22.150.108
    - fail_json is called due to timeout
    - fail_json error message is matched
    """
    instance = image_upgrade

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_upgrade_00081a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    instance.issu_detail = issu_details_by_ip_address
    instance.ip_addresses = [
        "172.22.150.102",
        "172.22.150.108",
    ]
    instance.check_interval = 1
    instance.check_timeout = 1

    match = "ImageUpgrade._wait_for_current_actions_to_complete: "
    match += "Timed out waiting for actions to complete. "
    match += r"ipv4_done: 172\.22\.150\.102, "
    match += r"ipv4_todo: 172\.22\.150\.102,172\.22\.150\.108\. "
    match += r"check the device\(s\) to determine the cause "
    match += r"\(e\.g\. show install all status\)\."
    with pytest.raises(AnsibleFailJson, match=match):
        instance._wait_for_current_actions_to_complete()
    assert isinstance(instance.ipv4_done, set)
    assert len(instance.ipv4_done) == 1
    assert "172.22.150.102" in instance.ipv4_done
    assert "172.22.150.108" not in instance.ipv4_done


def test_image_mgmt_upgrade_00090(
    monkeypatch, image_upgrade, issu_details_by_ip_address
) -> None:
    """
    Function
    - _wait_for_image_upgrade_to_complete

    Test
    - One ip address is added to ipv4_done due to issu_detail.upgrade == "Success"
    - fail_json is called due one ip address with issu_detail.upgrade == "Failed"

    Description
    _wait_for_image_upgrade_to_complete looks at the upgrade status for each
    ip address and waits for it to be "Success" or "Failed".
    In the case where all ip addresses are "Success", the module returns.
    In the case where any ip address is "Failed", the module calls fail_json.

    Expectations:
    - instance.ipv4_done is a set()
    - instance.ipv4_done has length 1
    - instance.ipv4_done contains 172.22.150.102, upgrade is "Success"
    - Call fail_json on ip address 172.22.150.108, upgrade is "Failed"
    """
    instance = image_upgrade

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_upgrade_00090a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    instance.issu_detail = issu_details_by_ip_address
    instance.ip_addresses = [
        "172.22.150.102",
        "172.22.150.108",
    ]
    instance.check_interval = 0
    match = "ImageUpgrade._wait_for_image_upgrade_to_complete: "
    match += "Seconds remaining 1800: "
    match += "upgrade image Failed for cvd-2313-leaf, FDO2112189M, "
    match += r"172\.22\.150\.108, upgrade_percent 50\. "
    match += "Check the controller to determine the cause. "
    match += "Operations > Image Management > Devices > View Details."
    with pytest.raises(AnsibleFailJson, match=match):
        instance._wait_for_image_upgrade_to_complete()
    assert isinstance(instance.ipv4_done, set)
    assert len(instance.ipv4_done) == 1
    assert "172.22.150.102" in instance.ipv4_done
    assert "172.22.150.108" not in instance.ipv4_done


def test_image_mgmt_upgrade_00091(
    monkeypatch, image_upgrade, issu_details_by_ip_address
) -> None:
    """
    Function
    - _wait_for_image_upgrade_to_complete
    Test
    -   One ip address is added to ipv4_done as
        issu_detail.upgrade == "Success"
    -   fail_json is called due to timeout since one
        ip address has value issu_detail.upgrade == "In-Progress"

    Description
    _wait_for_image_upgrade_to_complete looks at the upgrade status for each
    ip address and waits for it to be "Success" or "Failed".
    In the case where all ip addresses are "Success", the module returns.
    In the case where any ip address is "Failed", the module calls fail_json.
    In the case where any ip address is "In-Progress", the module waits until
    timeout is exceeded

    Expectations:
    - instance.ipv4_done is a set()
    - instance.ipv4_done has length 1
    - instance.ipv4_done contains 172.22.150.102, upgrade is "Success"
    - fail_json is called due to timeout exceeded
    """
    instance = image_upgrade

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_upgrade_00091a"
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    instance.issu_detail = issu_details_by_ip_address
    instance.ip_addresses = [
        "172.22.150.102",
        "172.22.150.108",
    ]
    instance.check_interval = 1
    instance.check_timeout = 1

    match = "ImageUpgrade._wait_for_image_upgrade_to_complete: "
    match += r"The following device\(s\) did not complete upgrade: "
    match += r"\['172\.22\.150\.108'\]. "
    match += "Check the controller to determine the cause. "
    match += "Operations > Image Management > Devices > View Details. "
    match += r"And/or check the device\(s\) "
    match += r"\(e\.g\. show install all status\)\."
    with pytest.raises(AnsibleFailJson, match=match):
        instance._wait_for_image_upgrade_to_complete()
    assert isinstance(instance.ipv4_done, set)
    assert len(instance.ipv4_done) == 1
    assert "172.22.150.102" in instance.ipv4_done
    assert "172.22.150.108" not in instance.ipv4_done
