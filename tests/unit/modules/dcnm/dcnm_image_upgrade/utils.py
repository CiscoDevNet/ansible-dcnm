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

from __future__ import absolute_import, division, print_function

__metaclass__ = type


from contextlib import contextmanager

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.common.params_validate_v2 import \
    ParamsValidate
from ansible_collections.cisco.dcnm.plugins.module_utils.common.switch_details import \
    SwitchDetails
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.image_stage import \
    ImageStage
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.image_upgrade import \
    ImageUpgrade
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.image_validate import \
    ImageValidate
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.install_options import \
    ImageInstallOptions
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.switch_issu_details import (
    SwitchIssuDetailsByDeviceName, SwitchIssuDetailsByIpAddress,
    SwitchIssuDetailsBySerialNumber)
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_image_upgrade.fixture import \
    load_fixture

params = {
    "state": "merged",
    "check_mode": False,
    "config": [
        {
            "name": "NR1F",
            "agnostic": False,
            "description": "NR1F",
            "platform": "N9K",
            "type": "PLATFORM",
        }
    ],
}


class MockAnsibleModule:
    """
    Mock the AnsibleModule class
    """

    check_mode = False

    params = {"config": {"switches": [{"ip_address": "172.22.150.105"}]}}
    argument_spec = {
        "config": {"required": True, "type": "dict"},
        "state": {"default": "merged", "choices": ["merged", "deleted", "query"]},
        "check_mode": False,
    }
    supports_check_mode = True

    @staticmethod
    def fail_json(msg, **kwargs) -> AnsibleFailJson:
        """
        mock the fail_json method
        """
        raise AnsibleFailJson(msg, kwargs)

    def public_method_for_pylint(self):
        """
        Add one public method to appease pylint
        """


# See the following for explanation of why fixtures are explicitely named
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html


@pytest.fixture(name="image_install_options")
def image_install_options_fixture():
    """
    Return ImageInstallOptions instance.
    """
    return ImageInstallOptions()


@pytest.fixture(name="image_stage")
def image_stage_fixture():
    """
    Return ImageStage instance.
    """
    return ImageStage()


@pytest.fixture(name="image_upgrade")
def image_upgrade_fixture():
    """
    Return ImageUpgrade instance.
    """
    return ImageUpgrade()


@pytest.fixture(name="image_validate")
def image_validate_fixture():
    """
    Return ImageValidate instance.
    """
    return ImageValidate()


@pytest.fixture(name="params_validate")
def params_validate_fixture():
    """
    Return ParamsValidate instance.
    """
    return ParamsValidate()


@pytest.fixture(name="issu_details_by_device_name")
def issu_details_by_device_name_fixture() -> SwitchIssuDetailsByDeviceName:
    """
    Return SwitchIssuDetailsByDeviceName instance.
    """
    return SwitchIssuDetailsByDeviceName()


@pytest.fixture(name="issu_details_by_ip_address")
def issu_details_by_ip_address_fixture() -> SwitchIssuDetailsByIpAddress:
    """
    Return SwitchIssuDetailsByIpAddress instance.
    """
    return SwitchIssuDetailsByIpAddress()


@pytest.fixture(name="issu_details_by_serial_number")
def issu_details_by_serial_number_fixture() -> SwitchIssuDetailsBySerialNumber:
    """
    Return SwitchIssuDetailsBySerialNumber instance.
    """
    return SwitchIssuDetailsBySerialNumber()


@pytest.fixture(name="switch_details")
def switch_details_fixture():
    """
    Return SwitchDetails instance.
    """
    return SwitchDetails()


@contextmanager
def does_not_raise():
    """
    A context manager that does not raise an exception.
    """
    yield


def load_playbook_config(key: str) -> dict[str, str]:
    """
    Return playbook configs for ImageUpgradeTask
    """
    playbook_file = "image_upgrade_playbook_configs"
    playbook_config = load_fixture(playbook_file).get(key)
    print(f"load_playbook_config: {key} : {playbook_config}")
    return playbook_config


def devices_image_upgrade(key: str) -> dict[str, str]:
    """
    Return data for the ImageUpgrade().devices property.
    Used by test_image_upgrade.py
    """
    devices_file = "devices_image_upgrade"
    devices = load_fixture(devices_file).get(key)
    print(f"devices_image_upgrade: {key} : {devices}")
    return devices


def payloads_ep_image_upgrade(key: str) -> dict[str, str]:
    """
    Return payloads for EpImageUpgrade
    """
    payload_file = "payloads_ep_image_upgrade"
    payload = load_fixture(payload_file).get(key)
    print(f"payloads_ep_image_upgrade: {key} : {payload}")
    return payload


def responses_ep_image_stage(key: str) -> dict[str, str]:
    """
    Return EpImageStage controller responses
    """
    response_file = "responses_ep_image_stage"
    response = load_fixture(response_file).get(key)
    print(f"responses_ep_image_stage: {key} : {response}")
    return response


def responses_ep_image_upgrade(key: str) -> dict[str, str]:
    """
    Return EpImageUpgrade responses
    """
    response_file = "responses_ep_image_upgrade"
    response = load_fixture(response_file).get(key)
    print(f"responses_ep_image_upgrade: {key} : {response}")
    return response


def responses_ep_image_validate(key: str) -> dict[str, str]:
    """
    Return EpImageValidate responses
    """
    response_file = "responses_ep_image_validate"
    response = load_fixture(response_file).get(key)
    print(f"responses_ep_image_validate: {key} : {response}")
    return response


def responses_ep_issu(key: str) -> dict[str, str]:
    """
    Return EpIssu responses
    """
    response_file = "responses_ep_issu"
    response = load_fixture(response_file).get(key)
    print(f"responses_ep_issu: {key} : {response}")
    return response


def responses_ep_version(key: str) -> dict[str, str]:
    """
    Return EpVersion responses
    """
    response_file = "responses_ep_version"
    response = load_fixture(response_file).get(key)
    print(f"responses_ep_version: {key} : {response}")
    return response


def responses_ep_install_options(key: str) -> dict[str, str]:
    """
    Return EpInstallOptions responses
    """
    response_file = "responses_ep_install_options"
    response = load_fixture(response_file).get(key)
    print(f"responses_ep_install_options: {key} : {response}")
    return response


def responses_image_policy_action(key: str) -> dict[str, str]:
    """
    Return ImagePolicyAction responses
    """
    response_file = "image_upgrade_responses_ImagePolicyAction"
    response = load_fixture(response_file).get(key)
    print(f"responses_image_policy_action: {key} : {response}")
    return response


def responses_image_upgrade_common(key: str) -> dict[str, str]:
    """
    Return ImageUpgradeCommon responses
    """
    response_file = "image_upgrade_responses_ImageUpgradeCommon"
    response = load_fixture(response_file).get(key)
    verb = response.get("METHOD")
    print(f"{key} : {verb} : {response}")
    return {"response": response, "verb": verb}


def responses_switch_details(key: str) -> dict[str, str]:
    """
    Return SwitchDetails responses
    """
    response_file = "image_upgrade_responses_SwitchDetails"
    response = load_fixture(response_file).get(key)
    print(f"responses_switch_details: {key} : {response}")
    return response
