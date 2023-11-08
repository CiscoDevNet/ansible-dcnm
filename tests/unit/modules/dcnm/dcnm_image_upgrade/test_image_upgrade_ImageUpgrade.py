"""
controller_version: 12
description: Verify functionality of NdfcSwitchUpgrade
"""
from contextlib import contextmanager
from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_upgrade import \
    ImageUpgrade

from .fixture import load_fixture


@contextmanager
def does_not_raise():
    yield


patch_module_utils = "ansible_collections.cisco.dcnm.plugins.module_utils."
patch_image_mgmt = patch_module_utils + "image_mgmt."


dcnm_send_image_upgrade = patch_image_mgmt + "image_upgrade.dcnm_send"
dcnm_send_install_options = patch_image_mgmt + "install_options.dcnm_send"
dcnm_send_issu_details = patch_image_mgmt + "switch_issu_details.dcnm_send"


def payloads_image_upgrade(key: str) -> Dict[str, str]:
    payload_file = f"image_upgrade_payloads_ImageUpgrade"
    payload = load_fixture(payload_file).get(key)
    print(f"payload_data_image_upgrade: {key} : {payload}")
    return payload

def responses_image_upgrade(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_ImageUpgrade"
    response = load_fixture(response_file).get(key)
    print(f"response_data_image_upgrade: {key} : {response}")
    return response

def responses_install_options(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_ImageInstallOptions"
    response = load_fixture(response_file).get(key)
    print(f"response_data_install_options: {key} : {response}")
    return response

def responses_issu_details(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_SwitchIssuDetails"
    response = load_fixture(response_file).get(key)
    print(f"response_data_issu_details: {key} : {response}")
    return response


class MockAnsibleModule:
    params = {}

    def fail_json(msg) -> AnsibleFailJson:
        raise AnsibleFailJson(msg)


@pytest.fixture
def module():
    return ImageUpgrade(MockAnsibleModule)


def test_image_mgmt_upgrade_00001(module) -> None:
    """
    ImageUpgrade.__init__ initializes class attributes to expected values
    """
    module.__init__(MockAnsibleModule)
    assert isinstance(module, ImageUpgrade)
    assert module.class_name == "ImageUpgrade"


def test_image_mgmt_upgrade_00002(module) -> None:
    """
    ImageUpgrade._init_defaults initializes attributes to expected values
    """
    module._init_defaults()
    assert isinstance(module.defaults, dict)
    assert module.defaults["reboot"] == False
    assert module.defaults["stage"] == True
    assert module.defaults["validate"] == True
    assert module.defaults["upgrade"]["nxos"] == True
    assert module.defaults["upgrade"]["epld"] == False
    assert module.defaults["options"]["nxos"]["mode"] == "disruptive"
    assert module.defaults["options"]["nxos"]["bios_force"] == False
    assert module.defaults["options"]["epld"]["module"] == "ALL"
    assert module.defaults["options"]["epld"]["golden"] == False
    assert module.defaults["options"]["reboot"]["config_reload"] == False
    assert module.defaults["options"]["reboot"]["write_erase"] == False
    assert module.defaults["options"]["package"]["install"] == False
    assert module.defaults["options"]["package"]["uninstall"] == False


def test_image_mgmt_upgrade_00003(module) -> None:
    """
    ImageUpgrade._init_properties initializes properties to expected values
    """
    module._init_properties()
    assert isinstance(module.properties, dict)
    assert module.properties.get("bios_force") == False
    assert module.properties.get("check_interval") == 10
    assert module.properties.get("check_timeout") == 1800
    assert module.properties.get("config_reload") == False
    assert module.properties.get("devices") == None
    assert module.properties.get("disruptive") == True
    assert module.properties.get("epld_golden") == False
    assert module.properties.get("epld_module") == "ALL"
    assert module.properties.get("epld_upgrade") == False
    assert module.properties.get("force_non_disruptive") == False
    assert module.properties.get("response_data") == None
    assert module.properties.get("response") == None
    assert module.properties.get("result") == None
    assert module.properties.get("non_disruptive") == False
    assert module.properties.get("force_non_disruptive") == False
    assert module.properties.get("package_install") == False
    assert module.properties.get("package_uninstall") == False
    assert module.properties.get("reboot") == False
    assert module.properties.get("write_erase") == False
    assert module.valid_nxos_mode == {
        "disruptive",
        "non_disruptive",
        "force_non_disruptive",
    }


def test_image_mgmt_upgrade_00004(monkeypatch, module) -> None:
    """
    Function description:

    ImageUpgrade.validate_devices updates the set ImageUpgrade.ip_addresses
    with the ip addresses of the devices that have issu_detail.upgrade is
    not "Failed"

    Expected results:

    1. instance.ip_addresses will contain {"172.22.150.102", "172.22.150.108"}
    2. fail_json will not be called
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_upgrade_00004a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    devices = [{"ip_address": "172.22.150.102"}, {"ip_address": "172.22.150.108"}]

    module.devices = devices
    module.validate_devices()
    assert isinstance(module.ip_addresses, set)
    assert len(module.ip_addresses) == 2
    assert "172.22.150.102" in module.ip_addresses
    assert "172.22.150.108" in module.ip_addresses


def test_image_mgmt_upgrade_00005(monkeypatch, module) -> None:
    """
    Function description:

    ImageUpgrade.validate_devices updates the set ImageUpgrade.ip_addresses
    with the ip addresses of the devices for which validation succeeds.
    Currently, validation succeeds for all devices.  This function may be
    updated in the future to handle various failure scenarios.

    Expected results:

    1.  instance.ip_addresses will contain {"172.22.150.102", "172.22.150.108"}
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_upgrade_00005a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    devices = [{"ip_address": "172.22.150.102"}, {"ip_address": "172.22.150.108"}]

    module.devices = devices
    module.validate_devices()
    assert isinstance(module.ip_addresses, set)
    assert len(module.ip_addresses) == 2
    assert "172.22.150.102" in module.ip_addresses
    assert "172.22.150.108" in module.ip_addresses


def test_image_mgmt_upgrade_00006(module) -> None:
    """
    Function: ImageUpgrade.commit

    Expected results:

    1.  ImageUpgrade.commit calls fail_json if devices is None
    """
    match = "ImageUpgrade.commit: call instance.devices before calling commit."
    with pytest.raises(AnsibleFailJson, match=match):
        module.commit()


def test_image_mgmt_upgrade_00007(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config

    Setup:
    1.  _merge_defaults_to_switch_config is passed a dictionary with all
        values missing that have defaults defined (see ImageUpgrade._init_defaults)

    Expected results:

    1.  merged_config will contain the expected default values
    """
    config = {"policy": "KR5M", "ip_address": "172.22.150.102", "policy_changed": False}

    merged_config = module._merge_defaults_to_switch_config(config)
    assert merged_config["reboot"] == False
    assert merged_config["stage"] == True
    assert merged_config["validate"] == True
    assert merged_config["upgrade"]["nxos"] == True
    assert merged_config["upgrade"]["epld"] == False
    assert merged_config["options"]["nxos"]["mode"] == "disruptive"
    assert merged_config["options"]["nxos"]["bios_force"] == False
    assert merged_config["options"]["epld"]["module"] == "ALL"
    assert merged_config["options"]["epld"]["golden"] == False
    assert merged_config["options"]["reboot"]["config_reload"] == False
    assert merged_config["options"]["reboot"]["write_erase"] == False
    assert merged_config["options"]["package"]["install"] == False
    assert merged_config["options"]["package"]["uninstall"] == False

def test_image_mgmt_upgrade_00008(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.commit

    Setup:
    1.  ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded.
    2. The methods called by commit are mocked to simulate that the
        the image has already been staged and validated and the device
        has already been upgraded to the desired version.
    3.  Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing.


    Expected results:

    1.  module.payload will equal a payload previously obtained by
        running ansible-playbook against the controller for this scenario
    """
    key = "test_image_mgmt_upgrade_00008a"
    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_install_options(key)
    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_issu_details(key)
    def mock_dcnm_send_image_upgrade(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_upgrade(key)
    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass
    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass
    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)
    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)
    monkeypatch.setattr(dcnm_send_image_upgrade, mock_dcnm_send_image_upgrade)
    monkeypatch.setattr(module, "_wait_for_current_actions_to_complete", mock_wait_for_current_actions_to_complete)
    monkeypatch.setattr(module, "_wait_for_image_upgrade_to_complete", mock_wait_for_image_upgrade_to_complete)

    module.devices = [
        {
            'policy': 'KR5M',
            'stage': True,
            'upgrade': {
                'nxos': False,
                'epld': True
            },
            'options': {
                'nxos': {
                    'mode': 'disruptive',
                    'bios_force': True
                }
            },
            'validate': True,
            'ip_address': '172.22.150.102',
            'policy_changed': False
        }
    ]
    module.commit()

    payload = payloads_image_upgrade(key)
    assert module.payload == payload

def test_image_mgmt_upgrade_00009(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.commit

    Setup:
    1.  ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    2. The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    3.  Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing


    Expected results:

    1.  module.payload will equal a payload previously obtained by
        running ansible-playbook against the controller for this scenario
    """
    key = "test_image_mgmt_upgrade_00009a"
    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_install_options(key)
    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_issu_details(key)
    def mock_dcnm_send_image_upgrade(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_upgrade(key)
    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass
    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass
    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)
    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)
    monkeypatch.setattr(dcnm_send_image_upgrade, mock_dcnm_send_image_upgrade)
    monkeypatch.setattr(module, "_wait_for_current_actions_to_complete", mock_wait_for_current_actions_to_complete)
    monkeypatch.setattr(module, "_wait_for_image_upgrade_to_complete", mock_wait_for_image_upgrade_to_complete)


    module.devices = [
        {
            'policy': 'NR3F',
            'stage': True,
            'upgrade': {
                'nxos': True,
                'epld': True
            },
            'options': {
                'nxos': {
                    'mode': 'disruptive',
                    'bios_force': False
                }
            },
            'validate': True,
            'ip_address': '172.22.150.102',
            'policy_changed': True
        }
    ]
    module.commit()

    payload = payloads_image_upgrade(key)
    assert isinstance(module.payload["devices"], list)
    assert module.payload == payload



