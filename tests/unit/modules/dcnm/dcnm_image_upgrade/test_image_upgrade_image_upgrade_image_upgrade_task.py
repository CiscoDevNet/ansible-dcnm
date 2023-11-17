# Copyright (c) 2020-2024 Cisco and/or its affiliates.
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


"""
ImageUpgradeTask - unit tests
"""

from __future__ import absolute_import, division, print_function

from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_details import \
    SwitchDetails
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_image_upgrade import \
    ImageUpgradeTask

from .image_upgrade_utils import (MockAnsibleModule, does_not_raise,
                                  image_upgrade_fixture,
                                  image_upgrade_task_fixture,
                                  issu_details_by_ip_address_fixture,
                                  load_playbook_config, payloads_image_upgrade,
                                  responses_image_install_options,
                                  responses_image_upgrade,
                                  responses_switch_issu_details)

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

PATCH_MODULE_UTILS = "ansible_collections.cisco.dcnm.plugins.module_utils."
PATCH_IMAGE_MGMT = PATCH_MODULE_UTILS + "image_mgmt."

DCNM_SEND_IMAGE_UPGRADE = PATCH_IMAGE_MGMT + "image_upgrade.dcnm_send"
DCNM_SEND_INSTALL_OPTIONS = PATCH_IMAGE_MGMT + "install_options.dcnm_send"
DCNM_SEND_ISSU_DETAILS = PATCH_IMAGE_MGMT + "switch_issu_details.dcnm_send"


# This fixture differs from image_upgrade_task_fixture
# in that it does not use a patched MockAnsibleModule.
# This is because we need to modify MockAnsibleModule for
# some of the test cases below.
@pytest.fixture(name="image_upgrade_task_bare")
def image_upgrade_task_bare_fixture():
    return ImageUpgradeTask


def test_image_mgmt_upgrade_task_00001(image_upgrade_task_bare) -> None:
    """
    Function
    - __init__

    Test
    - Class attributes are initialized to expected values
    """
    instance = image_upgrade_task_bare(MockAnsibleModule)
    assert isinstance(instance, ImageUpgradeTask)
    assert instance.class_name == "ImageUpgradeTask"
    assert instance.have is None
    assert instance.idempotent_want is None
    assert instance.switch_configs == []
    assert instance.path is None
    assert instance.verb is None
    assert instance.payloads == []
    assert instance.config == {"switches": [{"ip_address": "172.22.150.105"}]}
    assert instance.check_mode is False
    assert instance.validated == {}
    assert instance.want == []
    assert instance.need == []
    assert instance.result == {"changed": False, "diff": [], "response": []}
    assert instance.mandatory_global_keys == {"switches"}
    assert instance.mandatory_switch_keys == {"ip_address"}
    assert isinstance(instance.switch_details, SwitchDetails)
    assert isinstance(instance.image_policies, ImagePolicies)


def test_image_mgmt_upgrade_task_00002(image_upgrade_task_bare) -> None:
    """
    Function
    - __init__

    Test
    - fail_json is called because config is not a dict
    """
    match = "ImageUpgradeTask.__init__: expected dict type for self.config. got str"
    mock_ansible_module = MockAnsibleModule()
    mock_ansible_module.params = {"config": "foo"}
    with pytest.raises(AnsibleFailJson, match=match):
        instance = image_upgrade_task_bare(mock_ansible_module)
        assert isinstance(instance, ImageUpgradeTask)


def test_image_mgmt_upgrade_task_00003(image_upgrade_task_bare) -> None:
    """
    Function
    - __init__

    Test
    - fail_json is called because config.switches is not a list
    """
    match = "ImageUpgradeTask.__init__: expected list type for "
    match += r"self.config\['switches'\]. got str"

    mock_ansible_module = MockAnsibleModule()
    mock_ansible_module.params = {"config": {"switches": "FOO"}}
    with pytest.raises(AnsibleFailJson, match=match):
        instance = image_upgrade_task_bare(mock_ansible_module)
        assert isinstance(instance, ImageUpgradeTask)


def test_image_mgmt_upgrade_task_00004(image_upgrade_task_bare) -> None:
    """
    Function
    - __init__

    Test
    - fail_json is called because config.switches is empty
    """
    match = "ImageUpgradeTask.__init__: missing list of switches "
    match += "in playbook config."
    mock_ansible_module = MockAnsibleModule()
    mock_ansible_module.params = {"config": {"switches": []}}
    with pytest.raises(AnsibleFailJson, match=match):
        instance = image_upgrade_task_bare(mock_ansible_module)
        assert isinstance(instance, ImageUpgradeTask)


def test_image_mgmt_upgrade_task_00005(image_upgrade_task_bare) -> None:
    """
    Function
    - __init__

    Test
    -   fail_json is called because mandatory keys are missing in
        one of the switch configs
    """
    match = "ImageUpgradeTask.__init__: missing mandatory "
    match += r"key\(s\) in playbook switch config. expected "
    match += r"\{'ip_address'\}, got dict_keys\(\['foo'\]\)"

    mock_ansible_module = MockAnsibleModule()
    mock_ansible_module.params = {
        "config": {"switches": [{"ip_address": "1.2.3.4"}, {"foo": "bar"}]}
    }
    with pytest.raises(AnsibleFailJson, match=match):
        instance = image_upgrade_task_bare(mock_ansible_module)
        assert isinstance(instance, ImageUpgradeTask)


def test_image_mgmt_upgrade_task_00020(monkeypatch, image_upgrade_task) -> None:
    """
    Function
    - get_have

    Test
    -   SwitchIssuDetailsByIpAddress attributes are set to expected values
    """
    key = "test_image_mgmt_upgrade_task_00020a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    instance = image_upgrade_task
    instance.get_have()
    instance.have.ip_address = "172.22.150.102"
    assert instance.have.device_name == "leaf1"
    instance.have.ip_address = "172.22.150.108"
    assert instance.have.device_name == "cvd-2313-leaf"
    assert instance.have.serial_number == "FDO2112189M"
    assert instance.have.fabric == "hard"


def test_image_mgmt_upgrade_task_00030(monkeypatch, image_upgrade_task_bare) -> None:
    """
    Function
    - get_want
    - _merge_global_and_switch_configs
    - _validate_switch_configs

    Test
    -   global_config options are all set to default values
        (see ImageUpgrade._init_defaults)
    -   switch_1 does not override any global_config options
        so all values will be default
    -   switch_2 overrides all global_config options
        so all values will be non-default
    """
    key = "test_image_mgmt_upgrade_task_00030a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    mock_ansible_module = MockAnsibleModule()
    mock_ansible_module.params = load_playbook_config(key)
    instance = image_upgrade_task_bare(mock_ansible_module)
    instance.get_want()
    switch_1 = instance.want[0]
    switch_2 = instance.want[1]
    assert switch_1.get("ip_address") == "1.1.1.1"
    assert switch_1.get("options").get("epld").get("golden") is False
    assert switch_1.get("options").get("epld").get("module") == "ALL"
    assert switch_1.get("options").get("nxos").get("bios_force") is False
    assert switch_1.get("options").get("nxos").get("mode") == "disruptive"
    assert switch_1.get("options").get("package").get("install") is False
    assert switch_1.get("options").get("package").get("uninstall") is False
    assert switch_1.get("options").get("reboot").get("config_reload") is False
    assert switch_1.get("options").get("reboot").get("write_erase") is False
    assert switch_1.get("policy") == "NR3F"
    assert switch_1.get("reboot") is False
    assert switch_1.get("stage") is True
    assert switch_1.get("upgrade").get("epld") is False
    assert switch_1.get("upgrade").get("nxos") is True
    assert switch_1.get("validate") is True

    assert switch_2.get("ip_address") == "2.2.2.2"
    assert switch_2.get("options").get("epld").get("golden") is True
    assert switch_2.get("options").get("epld").get("module") == 1
    assert switch_2.get("options").get("nxos").get("bios_force") is True
    assert switch_2.get("options").get("nxos").get("mode") == "non_disruptive"
    assert switch_2.get("options").get("package").get("install") is True
    assert switch_2.get("options").get("package").get("uninstall") is True
    assert switch_2.get("options").get("reboot").get("config_reload") is True
    assert switch_2.get("options").get("reboot").get("write_erase") is True
    assert switch_2.get("policy") == "NR3F"
    assert switch_2.get("reboot") is True
    assert switch_2.get("stage") is False
    assert switch_2.get("upgrade").get("epld") is True
    assert switch_2.get("upgrade").get("nxos") is False
    assert switch_2.get("validate") is False


def test_image_mgmt_upgrade_task_00031(monkeypatch, image_upgrade_task_bare) -> None:
    """
    Function
    - get_want
    - _merge_global_and_switch_configs
    - _validate_switch_configs

    Test
    -   global_config options are all set to default values
    -   switch_1 overrides global_config.options.nxos.bios_force
        with a default value (False)
    -   switch_1 overrides global_config.options.nxos.mode
        with a non-default value (non_disruptive)
    -   switch_1 overrides global_config.options.reboot.write_erase
        with default value (False)
    -   switch_1 overrides global_config.reboot with
        a default value (False)
    -   switch_1 overrides global_config.stage with a
        non-default value (False)
    -   switch_1 overrides global_config.validate with a
        non-default value (False)
    -   switch_2 overrides global_config.upgrade.epld
        with a non-default value (True)
    - All other values for switch_1 and switch_2 are default
    """
    key = "test_image_mgmt_upgrade_task_00031a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_switch_issu_details(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    mock_ansible_module = MockAnsibleModule()
    mock_ansible_module.params = load_playbook_config(key)
    instance = image_upgrade_task_bare(mock_ansible_module)
    instance.get_want()
    switch_1 = instance.want[0]
    switch_2 = instance.want[1]
    assert switch_1.get("ip_address") == "1.1.1.1"
    assert switch_1.get("options").get("epld").get("golden") is False
    assert switch_1.get("options").get("epld").get("module") == "ALL"
    assert switch_1.get("options").get("nxos").get("bios_force") is False
    assert switch_1.get("options").get("nxos").get("mode") == "non_disruptive"
    assert switch_1.get("options").get("package").get("install") is False
    assert switch_1.get("options").get("package").get("uninstall") is False
    assert switch_1.get("options").get("reboot").get("config_reload") is False
    assert switch_1.get("options").get("reboot").get("write_erase") is False
    assert switch_1.get("policy") == "NR3F"
    assert switch_1.get("reboot") is False
    assert switch_1.get("stage") is False
    assert switch_1.get("upgrade").get("epld") is False
    assert switch_1.get("upgrade").get("nxos") is True
    assert switch_1.get("validate") is False

    assert switch_2.get("ip_address") == "2.2.2.2"
    assert switch_2.get("options").get("epld").get("golden") is False
    assert switch_2.get("options").get("epld").get("module") == "ALL"
    assert switch_2.get("options").get("nxos").get("bios_force") is False
    assert switch_2.get("options").get("nxos").get("mode") == "disruptive"
    assert switch_2.get("options").get("package").get("install") is False
    assert switch_2.get("options").get("package").get("uninstall") is False
    assert switch_2.get("options").get("reboot").get("config_reload") is False
    assert switch_2.get("options").get("reboot").get("write_erase") is False
    assert switch_2.get("policy") == "NR3F"
    assert switch_2.get("reboot") is False
    assert switch_2.get("stage") is True
    assert switch_2.get("upgrade").get("epld") is True
    assert switch_2.get("upgrade").get("nxos") is True
    assert switch_2.get("validate") is True
