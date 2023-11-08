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
    with the ip addresses of the devices for which issu_detail.upgrade is
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

def test_image_mgmt_upgrade_00008(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config

    Setup:
    1.  _merge_defaults_to_switch_config is passed a dictionary with all
        default values missing except upgrade.nxos.  This forces the code
        to take the upgrade.epld is None path.

    Expected results:

    1.  merged_config will contain the expected default values
    2.  merged_config will contain the expected non-default values
    """
    config = {
        "policy": "KR5M",
        "ip_address": "172.22.150.102",
        "policy_changed": False,
        "upgrade": {
            "nxos": False
        }
    }

    merged_config = module._merge_defaults_to_switch_config(config)
    assert merged_config["reboot"] == False
    assert merged_config["stage"] == True
    assert merged_config["validate"] == True
    assert merged_config["upgrade"]["nxos"] == False
    assert merged_config["upgrade"]["epld"] == False
    assert merged_config["options"]["nxos"]["mode"] == "disruptive"
    assert merged_config["options"]["nxos"]["bios_force"] == False
    assert merged_config["options"]["epld"]["module"] == "ALL"
    assert merged_config["options"]["epld"]["golden"] == False
    assert merged_config["options"]["reboot"]["config_reload"] == False
    assert merged_config["options"]["reboot"]["write_erase"] == False
    assert merged_config["options"]["package"]["install"] == False
    assert merged_config["options"]["package"]["uninstall"] == False


def test_image_mgmt_upgrade_00009(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config

    Setup:
    1.  _merge_defaults_to_switch_config is passed a dictionary with all
        default values missing except upgrade.epld.  This forces the code
        to take the upgrade.nxos is None path.

    Expected results:

    1.  merged_config will contain the expected default values
    2.  merged_config will contain the expected non-default values
    """
    config = {
        "policy": "KR5M",
        "ip_address": "172.22.150.102",
        "policy_changed": False,
        "upgrade": {
            "epld": True
        }
    }

    merged_config = module._merge_defaults_to_switch_config(config)
    assert merged_config["reboot"] == False
    assert merged_config["stage"] == True
    assert merged_config["validate"] == True
    assert merged_config["upgrade"]["nxos"] == True
    assert merged_config["upgrade"]["epld"] == True
    assert merged_config["options"]["nxos"]["mode"] == "disruptive"
    assert merged_config["options"]["nxos"]["bios_force"] == False
    assert merged_config["options"]["epld"]["module"] == "ALL"
    assert merged_config["options"]["epld"]["golden"] == False
    assert merged_config["options"]["reboot"]["config_reload"] == False
    assert merged_config["options"]["reboot"]["write_erase"] == False
    assert merged_config["options"]["package"]["install"] == False
    assert merged_config["options"]["package"]["uninstall"] == False


def test_image_mgmt_upgrade_00010(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config

    Setup:
    1.  _merge_defaults_to_switch_config is passed a dictionary with all
        default values missing except options, which is empty.  This forces
        the code to take the options.nxos is None path and provide default
        values for options.nxos and options.epld.

    Expected results:

    1.  merged_config will contain the expected default values
    """
    config = {
        "policy": "KR5M",
        "ip_address": "172.22.150.102",
        "policy_changed": False,
        "options": {},
    }

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


def test_image_mgmt_upgrade_00011(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config

    Setup:
    1.  _merge_defaults_to_switch_config is passed a dictionary with all
        default values missing except options.nxos.mode.  This forces the code
        to take the options.nxos.bios_force is None path.

    Expected results:

    1.  merged_config will contain the expected default values
    2.  merged_config will contain the expected non-default values
    """
    config = {
        "policy": "KR5M",
        "ip_address": "172.22.150.102",
        "policy_changed": False,
        "options": {
            "nxos": {
                "mode": "non_disruptive"
            }
        }
    }

    merged_config = module._merge_defaults_to_switch_config(config)
    assert merged_config["reboot"] == False
    assert merged_config["stage"] == True
    assert merged_config["validate"] == True
    assert merged_config["upgrade"]["nxos"] == True
    assert merged_config["upgrade"]["epld"] == False
    assert merged_config["options"]["nxos"]["mode"] == "non_disruptive"
    assert merged_config["options"]["nxos"]["bios_force"] == False
    assert merged_config["options"]["epld"]["module"] == "ALL"
    assert merged_config["options"]["epld"]["golden"] == False
    assert merged_config["options"]["reboot"]["config_reload"] == False
    assert merged_config["options"]["reboot"]["write_erase"] == False
    assert merged_config["options"]["package"]["install"] == False
    assert merged_config["options"]["package"]["uninstall"] == False


def test_image_mgmt_upgrade_00012(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config

    Setup:
    1.  _merge_defaults_to_switch_config is passed a dictionary with all
        default values missing except options.nxos.bios_force.  This forces the code
        to take the options.nxos.mode is None path.

    Expected results:

    1.  merged_config will contain the expected default values
    2.  merged_config will contain the expected non-default values
    """
    config = {
        "policy": "KR5M",
        "ip_address": "172.22.150.102",
        "policy_changed": False,
        "options": {
            "nxos": {
                "bios_force": True
            }
        }
    }

    merged_config = module._merge_defaults_to_switch_config(config)
    assert merged_config["reboot"] == False
    assert merged_config["stage"] == True
    assert merged_config["validate"] == True
    assert merged_config["upgrade"]["nxos"] == True
    assert merged_config["upgrade"]["epld"] == False
    assert merged_config["options"]["nxos"]["mode"] == "disruptive"
    assert merged_config["options"]["nxos"]["bios_force"] == True
    assert merged_config["options"]["epld"]["module"] == "ALL"
    assert merged_config["options"]["epld"]["golden"] == False
    assert merged_config["options"]["reboot"]["config_reload"] == False
    assert merged_config["options"]["reboot"]["write_erase"] == False
    assert merged_config["options"]["package"]["install"] == False
    assert merged_config["options"]["package"]["uninstall"] == False


def test_image_mgmt_upgrade_00013(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config

    Setup:
    1.  _merge_defaults_to_switch_config is passed a dictionary with all
        default values missing except options.epld.module.  This forces
        the code to take the options.epld.golden is None path.

    Expected results:

    1.  merged_config will contain the expected default values
    2.  merged_config will contain the expected non-default values
    """
    config = {
        "policy": "KR5M",
        "ip_address": "172.22.150.102",
        "policy_changed": False,
        "options": {
            "epld": {
                "module": 27
            }
        }
    }

    merged_config = module._merge_defaults_to_switch_config(config)
    assert merged_config["reboot"] == False
    assert merged_config["stage"] == True
    assert merged_config["validate"] == True
    assert merged_config["upgrade"]["nxos"] == True
    assert merged_config["upgrade"]["epld"] == False
    assert merged_config["options"]["nxos"]["mode"] == "disruptive"
    assert merged_config["options"]["nxos"]["bios_force"] == False
    assert merged_config["options"]["epld"]["module"] == 27
    assert merged_config["options"]["epld"]["golden"] == False
    assert merged_config["options"]["reboot"]["config_reload"] == False
    assert merged_config["options"]["reboot"]["write_erase"] == False
    assert merged_config["options"]["package"]["install"] == False
    assert merged_config["options"]["package"]["uninstall"] == False


def test_image_mgmt_upgrade_00014(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config

    Setup:
    1.  _merge_defaults_to_switch_config is passed a dictionary with all
        default values missing except options.epld.golden.  This forces
        the code to take the options.epld.module is None path.

    Expected results:

    1.  merged_config will contain the expected default values
    2.  merged_config will contain the expected non-default values
    """
    config = {
        "policy": "KR5M",
        "ip_address": "172.22.150.102",
        "policy_changed": False,
        "options": {
            "epld": {
                "golden": True
            }
        }
    }

    merged_config = module._merge_defaults_to_switch_config(config)
    assert merged_config["reboot"] == False
    assert merged_config["stage"] == True
    assert merged_config["validate"] == True
    assert merged_config["upgrade"]["nxos"] == True
    assert merged_config["upgrade"]["epld"] == False
    assert merged_config["options"]["nxos"]["mode"] == "disruptive"
    assert merged_config["options"]["nxos"]["bios_force"] == False
    assert merged_config["options"]["epld"]["module"] == "ALL"
    assert merged_config["options"]["epld"]["golden"] == True
    assert merged_config["options"]["reboot"]["config_reload"] == False
    assert merged_config["options"]["reboot"]["write_erase"] == False
    assert merged_config["options"]["package"]["install"] == False
    assert merged_config["options"]["package"]["uninstall"] == False


def test_image_mgmt_upgrade_00015(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config

    Setup:
    1.  _merge_defaults_to_switch_config is passed a dictionary with all
        default values missing except options.reboot.config_reload.  This
        forces the code to take the options.reboot.write_erase is None path.

    Expected results:

    1.  merged_config will contain the expected default values
    2.  merged_config will contain the expected non-default values
    """
    config = {
        "policy": "KR5M",
        "ip_address": "172.22.150.102",
        "policy_changed": False,
        "options": {
            "reboot": {
                "config_reload": True
            }
        }
    }

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
    assert merged_config["options"]["reboot"]["config_reload"] == True
    assert merged_config["options"]["reboot"]["write_erase"] == False
    assert merged_config["options"]["package"]["install"] == False
    assert merged_config["options"]["package"]["uninstall"] == False


def test_image_mgmt_upgrade_00016(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config

    Setup:
    1.  _merge_defaults_to_switch_config is passed a dictionary with all
        default values missing except options.reboot.config_reload.  This
        forces the code to take the options.reboot.write_erase is None path.

    Expected results:

    1.  merged_config will contain the expected default values
    2.  merged_config will contain the expected non-default values
    """
    config = {
        "policy": "KR5M",
        "ip_address": "172.22.150.102",
        "policy_changed": False,
        "options": {
            "reboot": {
                "write_erase": True
            }
        }
    }

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
    assert merged_config["options"]["reboot"]["write_erase"] == True
    assert merged_config["options"]["package"]["install"] == False
    assert merged_config["options"]["package"]["uninstall"] == False


def test_image_mgmt_upgrade_00017(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config

    Setup:
    1.  _merge_defaults_to_switch_config is passed a dictionary with all
        default values missing except options.package.install.  This
        forces the code to take the options.package.uninstall is None path.

    Expected results:

    1.  merged_config will contain the expected default values
    2.  merged_config will contain the expected non-default values
    """
    config = {
        "policy": "KR5M",
        "ip_address": "172.22.150.102",
        "policy_changed": False,
        "options": {
            "package": {
                "install": True
            }
        }
    }

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
    assert merged_config["options"]["package"]["install"] == True
    assert merged_config["options"]["package"]["uninstall"] == False


def test_image_mgmt_upgrade_00018(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config

    Setup:
    1.  _merge_defaults_to_switch_config is passed a dictionary with all
        default values missing except options.package.uninstall.  This
        forces the code to take the options.package.install is None path.

    Expected results:

    1.  merged_config will contain the expected default values
    2.  merged_config will contain the expected non-default values
    """
    config = {
        "policy": "KR5M",
        "ip_address": "172.22.150.102",
        "policy_changed": False,
        "options": {
            "package": {
                "uninstall": True
            }
        }
    }

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
    assert merged_config["options"]["package"]["uninstall"] == True


def test_image_mgmt_upgrade_00019(monkeypatch, module) -> None:
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
    key = "test_image_mgmt_upgrade_00019a"
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

def test_image_mgmt_upgrade_00020(monkeypatch, module) -> None:
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
    key = "test_image_mgmt_upgrade_00020a"
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
    assert module.payload == payload


match_00021 = "ImageUpgrade.build_payload: options.nxos.mode must be one of "
match_00021 += r"\['disruptive', 'force_non_disruptive', 'non_disruptive'\]. "
match_00021 += "Got FOO."
def test_image_mgmt_upgrade_00021(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.commit

    Setup:
    1.  ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    2. The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    3.  Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing

    4. module.devices is set to contain an invalid nxos.mode value

    Expected results:

    1.  build_payload will call fail_json
    """
    key = "test_image_mgmt_upgrade_00021a"
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
                    'mode': 'FOO',
                    'bios_force': False
                }
            },
            'validate': True,
            'ip_address': '172.22.150.102',
            'policy_changed': True
        }
    ]
    with pytest.raises(AnsibleFailJson, match=match_00021):
        module.commit()


match_00030 = "ImageUpgrade.bios_force: instance.bios_force must be a boolean."
@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00030))
    ],
)
def test_image_mgmt_upgrade_00030(module, value, expected) -> None:
    """
    ImageUpgrade.bios_force setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00030):
            module.bios_force = value
    else:
        module.bios_force = value
        assert module.bios_force == expected


match_00031 = "ImageUpgrade.config_reload: "
match_00031 += "instance.config_reload must be a boolean."
@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00031))
    ],
)
def test_image_mgmt_upgrade_00031(module, value, expected) -> None:
    """
    ImageUpgrade.config_reload setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00031):
            module.config_reload = value
    else:
        module.config_reload = value
        assert module.config_reload == expected


match_00032_common = "ImageUpgrade.devices: "
match_00032_common += "instance.devices must be a python list of dict"

match_00032_fail_1 = f"{match_00032_common}. Got not a list."
match_00032_fail_2 = fr"{match_00032_common}. Got \['not a dict'\]."

match_00032_fail_3 = f"{match_00032_common}, where each dict contains " 
match_00032_fail_3 += "the following keys: ip_address. "
match_00032_fail_3 += r"Got \[\{'bad_key_ip_address': '192.168.1.1'\}\]."

data_00032_pass = [{"ip_address": "192.168.1.1"}]
data_00032_fail_1 = "not a list"
data_00032_fail_2 = ["not a dict"]
data_00032_fail_3 = [{"bad_key_ip_address": "192.168.1.1"}]
@pytest.mark.parametrize(
    "value, expected",
    [
        (data_00032_pass, does_not_raise()),
        (data_00032_fail_1, pytest.raises(AnsibleFailJson, match=match_00032_fail_1)),
        (data_00032_fail_2, pytest.raises(AnsibleFailJson, match=match_00032_fail_2)),
        (data_00032_fail_3, pytest.raises(AnsibleFailJson, match=match_00032_fail_3))
    ],
)
def test_image_mgmt_upgrade_00032(module, value, expected) -> None:
    """
    ImageUpgrade.devices setter
    """
    with expected:
        module.devices = value


match_00033 = "ImageUpgrade.disruptive: "
match_00033 += "instance.disruptive must be a boolean."
@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00033))
    ],
)
def test_image_mgmt_upgrade_00033(module, value, expected) -> None:
    """
    ImageUpgrade.disruptive setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00033):
            module.disruptive = value
    else:
        module.disruptive = value
        assert module.disruptive == expected


match_00034 = "ImageUpgrade.epld_golden: "
match_00034 += "instance.epld_golden must be a boolean."
@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00034))
    ],
)
def test_image_mgmt_upgrade_00034(module, value, expected) -> None:
    """
    ImageUpgrade.epld_golden setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00034):
            module.epld_golden = value
    else:
        module.epld_golden = value
        assert module.epld_golden == expected


match_00035 = "ImageUpgrade.epld_upgrade: "
match_00035 += "instance.epld_upgrade must be a boolean."
@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00035))
    ],
)
def test_image_mgmt_upgrade_00035(module, value, expected) -> None:
    """
    ImageUpgrade.epld_upgrade setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00035):
            module.epld_upgrade = value
    else:
        module.epld_upgrade = value
        assert module.epld_upgrade == expected


match_00036_fail_1 = "ImageUpgrade.epld_module: "
match_00036_fail_1 += "instance.epld_module must be an integer or 'ALL'"
@pytest.mark.parametrize(
    "value, expected",
    [
        ("ALL", does_not_raise()),
        (1, does_not_raise()),
        (27, does_not_raise()),
        ("27", does_not_raise()),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00036_fail_1))
    ],
)
def test_image_mgmt_upgrade_00036(module, value, expected) -> None:
    """
    ImageUpgrade.epld_module setter
    """
    with expected:
        module.epld_module = value


match_00037 = "ImageUpgrade.force_non_disruptive: "
match_00037 += "instance.force_non_disruptive must be a boolean."
@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00037))
    ],
)
def test_image_mgmt_upgrade_00037(module, value, expected) -> None:
    """
    ImageUpgrade.force_non_disruptive setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00037):
            module.force_non_disruptive = value
    else:
        module.force_non_disruptive = value
        assert module.force_non_disruptive == expected


match_00038 = "ImageUpgrade.non_disruptive: "
match_00038 += "instance.non_disruptive must be a boolean."
@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00038))
    ],
)
def test_image_mgmt_upgrade_00038(module, value, expected) -> None:
    """
    ImageUpgrade.non_disruptive setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00038):
            module.non_disruptive = value
    else:
        module.non_disruptive = value
        assert module.non_disruptive == expected


match_00039 = "ImageUpgrade.package_install: "
match_00039 += "instance.package_install must be a boolean."
@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00039))
    ],
)
def test_image_mgmt_upgrade_00039(module, value, expected) -> None:
    """
    ImageUpgrade.package_install setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00039):
            module.package_install = value
    else:
        module.package_install = value
        assert module.package_install == expected


match_00040 = "ImageUpgrade.package_uninstall: "
match_00040 += "instance.package_uninstall must be a boolean."
@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00040))
    ],
)
def test_image_mgmt_upgrade_00040(module, value, expected) -> None:
    """
    ImageUpgrade.package_uninstall setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00040):
            module.package_uninstall = value
    else:
        module.package_uninstall = value
        assert module.package_uninstall == expected


match_00041 = "ImageUpgrade.reboot: "
match_00041 += "instance.reboot must be a boolean."
@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00041))
    ],
)
def test_image_mgmt_upgrade_00041(module, value, expected) -> None:
    """
    ImageUpgrade.reboot setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00041):
            module.reboot = value
    else:
        module.reboot = value
        assert module.reboot == expected


match_00042 = "ImageUpgrade.write_erase: "
match_00042 += "instance.write_erase must be a boolean."
@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00042))
    ],
)
def test_image_mgmt_upgrade_00042(module, value, expected) -> None:
    """
    ImageUpgrade.write_erase setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00042):
            module.write_erase = value
    else:
        module.write_erase = value
        assert module.write_erase == expected


# getters

def test_image_mgmt_upgrade_00043(module) -> None:
    """
    ImageUpgrade.check_interval
    """
    assert module.check_interval == 10


def test_image_mgmt_upgrade_00044(module) -> None:
    """
    ImageUpgrade.check_timeout
    """
    assert module.check_timeout == 1800


def test_image_mgmt_upgrade_00045(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.response_data

    Setup:
    1.  ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded.
    2. The methods called by commit are mocked to simulate that the
        the image has already been staged and validated and the device
        has already been upgraded to the desired version.
    3.  Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing.


    Expected results:

    1.  module.response_data == 121
    """
    key = "test_image_mgmt_upgrade_00045a"
    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return {}
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
    assert module.response_data == 121 


def test_image_mgmt_upgrade_00046(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.result

    Setup:
    1.  ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded.
    2. The methods called by commit are mocked to simulate that the
        the image has already been staged and validated and the device
        has already been upgraded to the desired version.
    3.  Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing.


    Expected results:

    1. module.result == {'success': True, 'changed': True}
    """
    key = "test_image_mgmt_upgrade_00046a"
    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return {}
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
    assert module.result == {'success': True, 'changed': True} 


def test_image_mgmt_upgrade_00047(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.response

    Setup:
    1.  ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded.
    2. The methods called by commit are mocked to simulate that the
        the image has already been staged and validated and the device
        has already been upgraded to the desired version.
    3.  Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing.


    Expected results:

    1. module.response is a dict
    """
    key = "test_image_mgmt_upgrade_00047a"
    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return {}
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
    print(f"module.response: {module.response}")
    assert isinstance(module.response, dict)
    assert module.response["DATA"] == 121
