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
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import \
    SwitchIssuDetailsByIpAddress

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


@pytest.fixture
def mock_issu_details() -> SwitchIssuDetailsByIpAddress:
    return SwitchIssuDetailsByIpAddress(MockAnsibleModule)


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


def test_image_mgmt_upgrade_00005(module) -> None:
    """
    Function: ImageUpgrade.commit

    Expected results:

    1.  ImageUpgrade.commit calls fail_json if devices is None
    """
    match = "ImageUpgrade.commit: call instance.devices before calling commit."
    with pytest.raises(AnsibleFailJson, match=match):
        module.commit()


def test_image_mgmt_upgrade_00006(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config
    Test: merged_config contains all default values

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


def test_image_mgmt_upgrade_00007(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config
    Test: Force code coverage of the upgrade.epld is None path

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
        "upgrade": {"nxos": False},
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


def test_image_mgmt_upgrade_00008(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config
    Test: Force code coverage of the upgrade.nxos is None path

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
        "upgrade": {"epld": True},
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


def test_image_mgmt_upgrade_00009(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config
    Test: Force code coverage of the options.nxos is None path

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


def test_image_mgmt_upgrade_00010(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config
    Test: Force code coverage of the options.nxos.bios_force is None path

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
        "options": {"nxos": {"mode": "non_disruptive"}},
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


def test_image_mgmt_upgrade_00011(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config
    Test: Force code coverage of the options.nxos.mode is None path

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
        "options": {"nxos": {"bios_force": True}},
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


def test_image_mgmt_upgrade_00012(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config
    Test: Force code coverage of the options.epld.golden is None path

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
        "options": {"epld": {"module": 27}},
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


def test_image_mgmt_upgrade_00013(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config
    Test: Force code coverage of the options.epld.module is None path

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
        "options": {"epld": {"golden": True}},
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


def test_image_mgmt_upgrade_00014(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config
    Test: Force code coverage of the options.reboot.write_erase is None path

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
        "options": {"reboot": {"config_reload": True}},
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


def test_image_mgmt_upgrade_00015(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config
    Test: Force code coverage of the options.reboot.config_reload is None path

    Setup:
    1.  _merge_defaults_to_switch_config is passed a dictionary with all
        default values missing except options.reboot.write_erase.  This
        forces the code to take the options.reboot.config_reload is None path.

    Expected results:

    1.  merged_config will contain the expected default values
    2.  merged_config will contain the expected non-default values
    """
    config = {
        "policy": "KR5M",
        "ip_address": "172.22.150.102",
        "policy_changed": False,
        "options": {"reboot": {"write_erase": True}},
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


def test_image_mgmt_upgrade_00016(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config
    Test: Force code coverage of the options.package.uninstall is None path

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
        "options": {"package": {"install": True}},
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


def test_image_mgmt_upgrade_00017(module) -> None:
    """
    Function: ImageUpgrade._merge_defaults_to_switch_config
    Test: Force code coverage of the options.package.install is None path

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
        "options": {"package": {"uninstall": True}},
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


def test_image_mgmt_upgrade_00018(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.commit
    Test: upgrade.nxos set to invalid value

    Setup:
    1.  ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded.
    2. The methods called by commit are mocked to simulate that the
        the image has already been staged and validated and the device
        has already been upgraded to the desired version.
    3.  Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing.

    Expected results:

    1.  commit will call build_payload which will call fail_json
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
    monkeypatch.setattr(
        module,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        module,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    module.devices = [
        {
            "policy": "KR5M",
            "stage": True,
            "upgrade": {"nxos": "FOO", "epld": True},
            "options": {"nxos": {"mode": "disruptive", "bios_force": True}},
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": False,
        }
    ]
    match = r"ImageUpgrade.build_payload: upgrade.nxos must be a boolean. Got FOO\."
    with pytest.raises(AnsibleFailJson, match=match):
        module.commit()


def test_image_mgmt_upgrade_00019(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.commit
    Test: non-default values are set for several options
    Test: policy_changed is set to False


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
        running ansible-playbook against the controller for this
        scenario which verifies that the non-default values are
        included in the payload.
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
    monkeypatch.setattr(
        module,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        module,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    module.devices = [
        {
            "policy": "KR5M",
            "stage": True,
            "upgrade": {"nxos": False, "epld": True},
            "options": {"nxos": {"mode": "disruptive", "bios_force": True}},
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": False,
        }
    ]
    module.commit()

    assert module.payload == payloads_image_upgrade(key)


def test_image_mgmt_upgrade_00020(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.commit
    Test: User explicitely sets default values for several options
    Test: policy_changed is set to True

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
    monkeypatch.setattr(
        module,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        module,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    module.devices = [
        {
            "policy": "NR3F",
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {"nxos": {"mode": "disruptive", "bios_force": False}},
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]
    module.commit()

    assert module.payload == payloads_image_upgrade(key)


def test_image_mgmt_upgrade_00021(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.commit
    Test: Invalid value for nxos.mode

    Setup:
    1.  ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    2. The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    3.  Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    4. module.devices is set to contain an invalid nxos.mode value

    Expected results:

    1.  commit calls build_payload, which calls fail_json
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
    monkeypatch.setattr(
        module,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        module,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    module.devices = [
        {
            "policy": "NR3F",
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {"nxos": {"mode": "FOO", "bios_force": False}},
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]
    match = "ImageUpgrade.build_payload: options.nxos.mode must be one of "
    match += r"\['disruptive', 'force_non_disruptive', 'non_disruptive'\]. "
    match += "Got FOO."
    with pytest.raises(AnsibleFailJson, match=match):
        module.commit()


def test_image_mgmt_upgrade_00022(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.commit
    Test: Force code coverage of nxos.mode == "non_disruptive" path

    Setup:
    1.  ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    2. The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    3.  Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    4.  module.devices is set to contain nxos.mode non_disruptive
        forcing the code to take nxos_mode == "non_disruptive" path

    Expected results:

    1.  self.payload["issuUpgradeOptions1"]["disruptive"] == False
    2.  self.payload["issuUpgradeOptions1"]["forceNonDisruptive"] == False
    3.  self.payload["issuUpgradeOptions1"]["nonDisruptive"] == True
    """
    key = "test_image_mgmt_upgrade_00022a"

    def mock_dcnm_send_image_upgrade(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_upgrade(key)

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)
    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)
    monkeypatch.setattr(dcnm_send_image_upgrade, mock_dcnm_send_image_upgrade)
    monkeypatch.setattr(
        module,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        module,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    module.devices = [
        {
            "policy": "NR3F",
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {"nxos": {"mode": "non_disruptive", "bios_force": False}},
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]
    module.commit()
    assert module.payload["issuUpgradeOptions1"]["disruptive"] == False
    assert module.payload["issuUpgradeOptions1"]["forceNonDisruptive"] == False
    assert module.payload["issuUpgradeOptions1"]["nonDisruptive"] == True


def test_image_mgmt_upgrade_00023(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.commit
    Test: Force code coverage of nxos.mode == "force_non_disruptive" path

    Setup:
    1.  ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    2. The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    3.  Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    4.  module.devices is set to contain nxos.mode force_non_disruptive
        forcing the code to take nxos_mode == "force_non_disruptive" path

    Expected results:

    1.  self.payload["issuUpgradeOptions1"]["disruptive"] == False
    2.  self.payload["issuUpgradeOptions1"]["forceNonDisruptive"] == True
    3.  self.payload["issuUpgradeOptions1"]["nonDisruptive"] == False
    """
    key = "test_image_mgmt_upgrade_00023a"

    def mock_dcnm_send_image_upgrade(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_upgrade(key)

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)
    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)
    monkeypatch.setattr(dcnm_send_image_upgrade, mock_dcnm_send_image_upgrade)
    monkeypatch.setattr(
        module,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        module,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    module.devices = [
        {
            "policy": "NR3F",
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {"nxos": {"mode": "force_non_disruptive", "bios_force": False}},
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]
    module.commit()
    assert module.payload["issuUpgradeOptions1"]["disruptive"] == False
    assert module.payload["issuUpgradeOptions1"]["forceNonDisruptive"] == True
    assert module.payload["issuUpgradeOptions1"]["nonDisruptive"] == False


def test_image_mgmt_upgrade_00024(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.commit
    Test: Invalid value for options.nxos.bios_force

    Setup:
    1.  ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    2. The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    3.  Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    4.  module.devices is set to contain invalid value for
        options.nxos.bios_force

    Expected results:

    1.  commit calls build_payload which calls fail_json
    """
    key = "test_image_mgmt_upgrade_00024a"

    def mock_dcnm_send_image_upgrade(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_upgrade(key)

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)
    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)
    monkeypatch.setattr(dcnm_send_image_upgrade, mock_dcnm_send_image_upgrade)
    monkeypatch.setattr(
        module,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        module,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    module.devices = [
        {
            "policy": "NR3F",
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {"nxos": {"mode": "disruptive", "bios_force": "FOO"}},
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]
    match = "ImageUpgrade.build_payload: "
    match += r"options.nxos.bios_force must be a boolean. Got FOO\."
    with pytest.raises(AnsibleFailJson, match=match):
        module.commit()


def test_image_mgmt_upgrade_00025(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.commit
    Test: Incompatible values for options.epld.golden and upgrade.nxos

    Setup:
    1.  ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    2. The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    3.  Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    4.  module.devices is set to contain epld golden True and
        upgrade.nxos True.

    Expected results:

    1.  commit calls build_payload which calls fail_json
    """
    key = "test_image_mgmt_upgrade_00025a"

    def mock_dcnm_send_image_upgrade(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_upgrade(key)

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)
    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)
    monkeypatch.setattr(dcnm_send_image_upgrade, mock_dcnm_send_image_upgrade)
    monkeypatch.setattr(
        module,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        module,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    module.devices = [
        {
            "policy": "NR3F",
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {"epld": {"module": "ALL", "golden": True}},
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]
    match = "ImageUpgrade.build_payload: Invalid configuration for "
    match += "172.22.150.102. If options.epld.golden is True "
    match += "all other upgrade options, e.g. upgrade.nxos, "
    match += "must be False."
    with pytest.raises(AnsibleFailJson, match=match):
        module.commit()


def test_image_mgmt_upgrade_00026(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.commit
    Test: Invalid value for epld.module

    Setup:
    1.  ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    2. The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    3.  Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing

    4.  module.devices is set to contain invalid epld.module

    Expected results:

    1.  commit calls build_payload which calls fail_json
    """
    key = "test_image_mgmt_upgrade_00026a"

    def mock_dcnm_send_image_upgrade(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_upgrade(key)

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)
    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)
    monkeypatch.setattr(dcnm_send_image_upgrade, mock_dcnm_send_image_upgrade)
    monkeypatch.setattr(
        module,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        module,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    module.devices = [
        {
            "policy": "NR3F",
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "epld": {
                    "module": "FOO",
                }
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]
    match = "ImageUpgrade.build_payload: "
    match += "options.epld.module must either be 'ALL' "
    match += r"or an integer. Got FOO\."
    with pytest.raises(AnsibleFailJson, match=match):
        module.commit()


def test_image_mgmt_upgrade_00027(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.commit
    Test: Invalid value for epld.golden

    Setup:
    1.  ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    2. The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    3.  Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    4.  module.devices is set to contain invalid epld.golden

    Expected results:

    1.  commit calls build_payload which calls fail_json
    """
    key = "test_image_mgmt_upgrade_00027a"

    def mock_dcnm_send_image_upgrade(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_upgrade(key)

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)
    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)
    monkeypatch.setattr(dcnm_send_image_upgrade, mock_dcnm_send_image_upgrade)
    monkeypatch.setattr(
        module,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        module,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    module.devices = [
        {
            "policy": "NR3F",
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "epld": {
                    "golden": "FOO",
                }
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]
    match = "ImageUpgrade.build_payload: "
    match += r"options.epld.golden must be a boolean. Got FOO\."
    with pytest.raises(AnsibleFailJson, match=match):
        module.commit()


def test_image_mgmt_upgrade_00028(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.commit
    Test: Invalid value for reboot

    Setup:
    1.  ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    2. The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    3.  Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    4.  module.devices is set to contain invalid value for reboot

    Expected results:

    1.  commit calls build_payload which calls fail_json
    """
    key = "test_image_mgmt_upgrade_00028a"

    def mock_dcnm_send_image_upgrade(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_upgrade(key)

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)
    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)
    monkeypatch.setattr(dcnm_send_image_upgrade, mock_dcnm_send_image_upgrade)
    monkeypatch.setattr(
        module,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        module,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    module.devices = [
        {
            "policy": "NR3F",
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "reboot": "FOO",
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]
    match = "ImageUpgrade.build_payload: "
    match += r"reboot must be a boolean. Got FOO\."
    with pytest.raises(AnsibleFailJson, match=match):
        module.commit()


def test_image_mgmt_upgrade_00029(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.commit
    Test: Invalid value for options.reboot.config_reload

    Setup:
    1.  ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    2. The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    3.  Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    4.  module.devices is set to contain invalid value for
        options.reboot.config_reload

    Expected results:

    1.  commit calls build_payload which calls fail_json
    """
    key = "test_image_mgmt_upgrade_00029a"

    def mock_dcnm_send_image_upgrade(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_upgrade(key)

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)
    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)
    monkeypatch.setattr(dcnm_send_image_upgrade, mock_dcnm_send_image_upgrade)
    monkeypatch.setattr(
        module,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        module,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    module.devices = [
        {
            "policy": "NR3F",
            "stage": True,
            "upgrade": {"nxos": True, "epld": False},
            "options": {
                "reboot": {
                    "config_reload": "FOO",
                }
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]
    match = "ImageUpgrade.build_payload: "
    match += r"options.reboot.config_reload must be a boolean. Got FOO\."
    with pytest.raises(AnsibleFailJson, match=match):
        module.commit()


def test_image_mgmt_upgrade_00030(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.commit
    Test: Invalid value for options.reboot.write_erase

    Setup:
    1.  ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    2. The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    3.  Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    4.  module.devices is set to contain invalid value for
        options.reboot.write_erase

    Expected results:

    1.  commit calls build_payload which calls fail_json
    """
    key = "test_image_mgmt_upgrade_00030a"

    def mock_dcnm_send_image_upgrade(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_upgrade(key)

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)
    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)
    monkeypatch.setattr(dcnm_send_image_upgrade, mock_dcnm_send_image_upgrade)
    monkeypatch.setattr(
        module,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        module,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    module.devices = [
        {
            "policy": "NR3F",
            "stage": True,
            "upgrade": {"nxos": True, "epld": False},
            "options": {
                "reboot": {
                    "write_erase": "FOO",
                }
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]
    match = "ImageUpgrade.build_payload: "
    match += r"options.reboot.write_erase must be a boolean. Got FOO\."
    with pytest.raises(AnsibleFailJson, match=match):
        module.commit()


def test_image_mgmt_upgrade_00031(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.commit
    Test: Invalid value for options.package.uninstall

    Setup:
    1.  ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    2. The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    3.  Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    4.  module.devices is set to contain invalid value for
        options.package.uninstall

    Expected results:

    1.  commit calls build_payload which calls fail_json

    NOTES:
    1. The corresponding test for options.package.install is missing.
        It's not needed since ImageInstallOptions will call fail_json
        on invalid values before ImageUpgrade has a chance to verify
        the value.
    """
    key = "test_image_mgmt_upgrade_00031a"

    def mock_dcnm_send_image_upgrade(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_upgrade(key)

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)
    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)
    monkeypatch.setattr(dcnm_send_image_upgrade, mock_dcnm_send_image_upgrade)
    monkeypatch.setattr(
        module,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        module,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    module.devices = [
        {
            "policy": "NR3F",
            "stage": True,
            "upgrade": {"nxos": True, "epld": False},
            "options": {
                "package": {
                    "uninstall": "FOO",
                }
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]
    match = "ImageUpgrade.build_payload: "
    match += r"options.package.uninstall must be a boolean. Got FOO\."
    with pytest.raises(AnsibleFailJson, match=match):
        module.commit()


def test_image_mgmt_upgrade_00032(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.commit
    Test: Bad result code in image upgrade response

    Setup:
    1.  ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    2. The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    3.  Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    4.  ImageUpgrade response (mock_dcnm_send_image_upgrade) is set
        to return RESULT_CODE 500 with MESSAGE "Internal Server Error"

    Expected results:

    1.  commit calls fail_json because self.result will not equal "success"

    """
    key = "test_image_mgmt_upgrade_00032a"

    def mock_dcnm_send_image_upgrade(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_upgrade(key)

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)
    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)
    monkeypatch.setattr(dcnm_send_image_upgrade, mock_dcnm_send_image_upgrade)
    monkeypatch.setattr(
        module,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        module,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    module.devices = [
        {
            "policy": "NR3F",
            "stage": True,
            "upgrade": {"nxos": True, "epld": False},
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]
    match = "ImageUpgrade.commit: failed: "
    match += r"\{'success': False, 'changed': False\}. "
    match += r"Controller response: \{'DATA': 123, "
    match += "'MESSAGE': 'Internal Server Error', 'METHOD': 'POST', "
    match += "'REQUEST_PATH': "
    match += "'https://172.22.150.244:443/appcenter/cisco/ndfc/api/v1/"
    match += "imagemanagement/rest/imageupgrade/upgrade-image', "
    match += r"'RETURN_CODE': 500\}"
    with pytest.raises(AnsibleFailJson, match=match):
        module.commit()


def test_image_mgmt_upgrade_00033(monkeypatch, module) -> None:
    """
    Function: ImageUpgrade.commit
    Test: Invalid value for upgrade.epld

    Setup:
    1.  ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    2. The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    3.  Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    4.  module.devices is set to contain invalid value for
        upgrade.epld

    Expected results:

    1.  commit calls build_payload which calls fail_json
    """
    key = "test_image_mgmt_upgrade_00033a"

    def mock_dcnm_send_image_upgrade(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_upgrade(key)

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_issu_details(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(dcnm_send_install_options, mock_dcnm_send_install_options)
    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)
    monkeypatch.setattr(dcnm_send_image_upgrade, mock_dcnm_send_image_upgrade)
    monkeypatch.setattr(
        module,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        module,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    module.devices = [
        {
            "policy": "NR3F",
            "stage": True,
            "upgrade": {"nxos": True, "epld": "FOO"},
            "options": {
                "package": {
                    "uninstall": "FOO",
                }
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]
    match = "ImageUpgrade.build_payload: "
    match += r"upgrade.epld must be a boolean. Got FOO\."
    with pytest.raises(AnsibleFailJson, match=match):
        module.commit()


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
    monkeypatch.setattr(
        module,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        module,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    module.devices = [
        {
            "policy": "KR5M",
            "stage": True,
            "upgrade": {"nxos": False, "epld": True},
            "options": {"nxos": {"mode": "disruptive", "bios_force": True}},
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": False,
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
    monkeypatch.setattr(
        module,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        module,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    module.devices = [
        {
            "policy": "KR5M",
            "stage": True,
            "upgrade": {"nxos": False, "epld": True},
            "options": {"nxos": {"mode": "disruptive", "bios_force": True}},
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": False,
        }
    ]
    module.commit()
    assert module.result == {"success": True, "changed": True}


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
    monkeypatch.setattr(
        module,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        module,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    module.devices = [
        {
            "policy": "KR5M",
            "stage": True,
            "upgrade": {"nxos": False, "epld": True},
            "options": {"nxos": {"mode": "disruptive", "bios_force": True}},
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": False,
        }
    ]
    module.commit()
    print(f"module.response: {module.response}")
    assert isinstance(module.response, dict)
    assert module.response["DATA"] == 121


# setters

match_00060 = "ImageUpgrade.bios_force: instance.bios_force must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00060)),
    ],
)
def test_image_mgmt_upgrade_00060(module, value, expected) -> None:
    """
    ImageUpgrade.bios_force setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00060):
            module.bios_force = value
    else:
        module.bios_force = value
        assert module.bios_force == expected


match_00061 = "ImageUpgrade.config_reload: "
match_00061 += "instance.config_reload must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00061)),
    ],
)
def test_image_mgmt_upgrade_00061(module, value, expected) -> None:
    """
    ImageUpgrade.config_reload setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00061):
            module.config_reload = value
    else:
        module.config_reload = value
        assert module.config_reload == expected


match_00062_common = "ImageUpgrade.devices: "
match_00062_common += "instance.devices must be a python list of dict"

match_00062_fail_1 = f"{match_00062_common}. Got not a list."
match_00062_fail_2 = rf"{match_00062_common}. Got \['not a dict'\]."

match_00062_fail_3 = f"{match_00062_common}, where each dict contains "
match_00062_fail_3 += "the following keys: ip_address. "
match_00062_fail_3 += r"Got \[\{'bad_key_ip_address': '192.168.1.1'\}\]."

data_00062_pass = [{"ip_address": "192.168.1.1"}]
data_00062_fail_1 = "not a list"
data_00062_fail_2 = ["not a dict"]
data_00062_fail_3 = [{"bad_key_ip_address": "192.168.1.1"}]


@pytest.mark.parametrize(
    "value, expected",
    [
        (data_00062_pass, does_not_raise()),
        (data_00062_fail_1, pytest.raises(AnsibleFailJson, match=match_00062_fail_1)),
        (data_00062_fail_2, pytest.raises(AnsibleFailJson, match=match_00062_fail_2)),
        (data_00062_fail_3, pytest.raises(AnsibleFailJson, match=match_00062_fail_3)),
    ],
)
def test_image_mgmt_upgrade_00062(module, value, expected) -> None:
    """
    ImageUpgrade.devices setter
    """
    with expected:
        module.devices = value


match_00063 = "ImageUpgrade.disruptive: "
match_00063 += "instance.disruptive must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00063)),
    ],
)
def test_image_mgmt_upgrade_00063(module, value, expected) -> None:
    """
    ImageUpgrade.disruptive setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00063):
            module.disruptive = value
    else:
        module.disruptive = value
        assert module.disruptive == expected


match_00064 = "ImageUpgrade.epld_golden: "
match_00064 += "instance.epld_golden must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00064)),
    ],
)
def test_image_mgmt_upgrade_00064(module, value, expected) -> None:
    """
    ImageUpgrade.epld_golden setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00064):
            module.epld_golden = value
    else:
        module.epld_golden = value
        assert module.epld_golden == expected


match_00065 = "ImageUpgrade.epld_upgrade: "
match_00065 += "instance.epld_upgrade must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00065)),
    ],
)
def test_image_mgmt_upgrade_00065(module, value, expected) -> None:
    """
    ImageUpgrade.epld_upgrade setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00065):
            module.epld_upgrade = value
    else:
        module.epld_upgrade = value
        assert module.epld_upgrade == expected


match_00066_fail_1 = "ImageUpgrade.epld_module: "
match_00066_fail_1 += "instance.epld_module must be an integer or 'ALL'"


@pytest.mark.parametrize(
    "value, expected",
    [
        ("ALL", does_not_raise()),
        (1, does_not_raise()),
        (27, does_not_raise()),
        ("27", does_not_raise()),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00066_fail_1)),
    ],
)
def test_image_mgmt_upgrade_00066(module, value, expected) -> None:
    """
    ImageUpgrade.epld_module setter
    """
    with expected:
        module.epld_module = value


match_00067 = "ImageUpgrade.force_non_disruptive: "
match_00067 += "instance.force_non_disruptive must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00067)),
    ],
)
def test_image_mgmt_upgrade_00067(module, value, expected) -> None:
    """
    ImageUpgrade.force_non_disruptive setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00067):
            module.force_non_disruptive = value
    else:
        module.force_non_disruptive = value
        assert module.force_non_disruptive == expected


match_00068 = "ImageUpgrade.non_disruptive: "
match_00068 += "instance.non_disruptive must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00068)),
    ],
)
def test_image_mgmt_upgrade_00068(module, value, expected) -> None:
    """
    ImageUpgrade.non_disruptive setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00068):
            module.non_disruptive = value
    else:
        module.non_disruptive = value
        assert module.non_disruptive == expected


match_00069 = "ImageUpgrade.package_install: "
match_00069 += "instance.package_install must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00069)),
    ],
)
def test_image_mgmt_upgrade_00069(module, value, expected) -> None:
    """
    ImageUpgrade.package_install setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00069):
            module.package_install = value
    else:
        module.package_install = value
        assert module.package_install == expected


match_00070 = "ImageUpgrade.package_uninstall: "
match_00070 += "instance.package_uninstall must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00070)),
    ],
)
def test_image_mgmt_upgrade_00070(module, value, expected) -> None:
    """
    ImageUpgrade.package_uninstall setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00070):
            module.package_uninstall = value
    else:
        module.package_uninstall = value
        assert module.package_uninstall == expected


match_00071 = "ImageUpgrade.reboot: "
match_00071 += "instance.reboot must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00071)),
    ],
)
def test_image_mgmt_upgrade_00071(module, value, expected) -> None:
    """
    ImageUpgrade.reboot setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00071):
            module.reboot = value
    else:
        module.reboot = value
        assert module.reboot == expected


match_00072 = "ImageUpgrade.write_erase: "
match_00072 += "instance.write_erase must be a boolean."


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("FOO", pytest.raises(AnsibleFailJson, match=match_00072)),
    ],
)
def test_image_mgmt_upgrade_00072(module, value, expected) -> None:
    """
    ImageUpgrade.write_erase setter
    """
    if value == "FOO":
        with pytest.raises(AnsibleFailJson, match=match_00072):
            module.write_erase = value
    else:
        module.write_erase = value
        assert module.write_erase == expected


def test_image_mgmt_upgrade_00080(monkeypatch, module, mock_issu_details) -> None:
    """
    Function: ImageUpgrade._wait_for_current_actions_to_complete
    Test: Verify that two switches are added to ipv4_done

    _wait_for_current_actions_to_complete waits until staging, validation,
    and upgrade actions are complete for all ip addresses.  It calls
    SwitchIssuDetailsByIpAddress.actions_in_progress() and expects
    this to return False.  actions_in_progress() returns True until none of
    the following keys has a value of "In-Progress":

    ["imageStaged", "upgrade", "validated"]

    Expectations:
    1.  module.ipv4_done should be a set()
    2.  module.ipv4_done should be length 2
    3.  module.ipv4_done should contain all ip addresses in
        module.ip_addresses
    4.  The function should return without calling fail_json.
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_upgrade_00080a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.issu_detail = mock_issu_details
    module.ip_addresses = [
        "172.22.150.102",
        "172.22.150.108",
    ]
    module.check_interval = 0
    module._wait_for_current_actions_to_complete()
    assert isinstance(module.ipv4_done, set)
    assert len(module.ipv4_done) == 2
    assert "172.22.150.102" in module.ipv4_done
    assert "172.22.150.108" in module.ipv4_done


def test_image_mgmt_upgrade_00081(monkeypatch, module, mock_issu_details) -> None:
    """
    Function: ImageUpgrade._wait_for_current_actions_to_complete
    Test: Verify that one switch is added to ipv4_done
    Test: Verify that fail_json is called due to timeout

    See test_image_mgmt_upgrade_00080 for functional details.

    Expectations:
    1.  module.ipv4_done should be a set()
    2.  module.ipv4_done should be length 1
    3.  module.ipv4_done should contain 172.22.150.102
    3.  module.ipv4_done should not contain 172.22.150.108
    4.  The function should call fail_json due to timeout
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_upgrade_00081a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.issu_detail = mock_issu_details
    module.ip_addresses = [
        "172.22.150.102",
        "172.22.150.108",
    ]
    module.check_interval = 1
    module.check_timeout = 1

    match = "ImageUpgrade._wait_for_current_actions_to_complete: "
    match += "Timed out waiting for actions to complete. "
    match += r"ipv4_done: 172\.22\.150\.102, "
    match += r"ipv4_todo: 172\.22\.150\.102,172\.22\.150\.108\. "
    match += r"check the device\(s\) to determine the cause "
    match += r"\(e\.g\. show install all status\)\."
    with pytest.raises(AnsibleFailJson, match=match):
        module._wait_for_current_actions_to_complete()
    assert isinstance(module.ipv4_done, set)
    assert len(module.ipv4_done) == 1
    assert "172.22.150.102" in module.ipv4_done
    assert "172.22.150.108" not in module.ipv4_done


def test_image_mgmt_upgrade_00090(monkeypatch, module, mock_issu_details) -> None:
    """
    Function: ImageUpgrade._wait_for_image_upgrade_to_complete
    Test:   One ip address is added to ipv4_done due to
            issu_detail.upgrade == "Success"
    Test:   fail_json is called due one ip address with
            issu_detail.upgrade == "Failed"

    _wait_for_image_upgrade_to_complete looks at the upgrade status for each
    ip address and waits for it to be "Success" or "Failed".
    In the case where all ip addresses are "Success", the module returns.
    In the case where any ip address is "Failed", the module calls fail_json.

    Expectations:
    1. module.ipv4_done is a set()
    2. module.ipv4_done has length 1
    3. module.ipv4_done contains 172.22.150.102, upgrade is "Success"
    4. Call fail_json on ip address 172.22.150.108, upgrade is "Failed"
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_upgrade_00090a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.issu_detail = mock_issu_details
    module.ip_addresses = [
        "172.22.150.102",
        "172.22.150.108",
    ]
    module.check_interval = 0
    match = "ImageUpgrade._wait_for_image_upgrade_to_complete: "
    match += "Seconds remaining 1800: "
    match += "upgrade image Failed for cvd-2313-leaf, FDO2112189M, "
    match += r"172\.22\.150\.108, upgrade_percent 50\. "
    match += "Check the controller to determine the cause. "
    match += "Operations > Image Management > Devices > View Details."
    with pytest.raises(AnsibleFailJson, match=match):
        module._wait_for_image_upgrade_to_complete()
    assert isinstance(module.ipv4_done, set)
    assert len(module.ipv4_done) == 1
    assert "172.22.150.102" in module.ipv4_done
    assert "172.22.150.108" not in module.ipv4_done


def test_image_mgmt_upgrade_00091(monkeypatch, module, mock_issu_details) -> None:
    """
    Function: ImageUpgrade._wait_for_image_upgrade_to_complete
    Test:   One ip address is added to ipv4_done due to
            issu_detail.upgrade == "Success"
    Test:   fail_json is called due to timeout because one
            ip address has issu_detail.upgrade == "In-Progress"

    _wait_for_image_upgrade_to_complete looks at the upgrade status for each
    ip address and waits for it to be "Success" or "Failed".
    In the case where all ip addresses are "Success", the module returns.
    In the case where any ip address is "Failed", the module calls fail_json.
    In the case where any ip address is "In-Progress", the module waits until
    timeout is exceeded

    Expectations:
    1. module.ipv4_done is a set()
    2. module.ipv4_done has length 1
    3. module.ipv4_done contains 172.22.150.102, upgrade is "Success"
    4. Call fail_json due to timeout exceeded
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_mgmt_upgrade_00091a"
        return responses_issu_details(key)

    monkeypatch.setattr(dcnm_send_issu_details, mock_dcnm_send_issu_details)

    module.issu_detail = mock_issu_details
    module.ip_addresses = [
        "172.22.150.102",
        "172.22.150.108",
    ]
    module.check_interval = 1
    module.check_timeout = 1

    match = "ImageUpgrade._wait_for_image_upgrade_to_complete: "
    match += r"The following device\(s\) did not complete upgrade: "
    match += r"\['172\.22\.150\.108'\]. "
    match += r"Check the device\(s\) to determine the cause "
    match += r"\(e\.g\. show install all status\)\."
    with pytest.raises(AnsibleFailJson, match=match):
        module._wait_for_image_upgrade_to_complete()
    assert isinstance(module.ipv4_done, set)
    assert len(module.ipv4_done) == 1
    assert "172.22.150.102" in module.ipv4_done
    assert "172.22.150.108" not in module.ipv4_done
