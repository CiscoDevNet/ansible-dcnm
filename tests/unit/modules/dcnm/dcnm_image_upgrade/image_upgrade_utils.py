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

"""
Utilities for image_upgrade unit tests
"""
from __future__ import absolute_import, division, print_function
import pytest
from contextlib import contextmanager

from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.common.controller_version import \
    ControllerVersion
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.install_options import \
    ImageInstallOptions
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policy_action import \
    ImagePolicyAction
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_stage import \
    ImageStage
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_upgrade_common import \
    ImageUpgradeCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_upgrade import \
    ImageUpgrade
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import \
    SwitchIssuDetailsByDeviceName
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import \
    SwitchIssuDetailsByIpAddress
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import \
    SwitchIssuDetailsBySerialNumber

class MockAnsibleModule:
    """
    Mock the AnsibleModule class
    """

    params = {}

    @staticmethod
    def fail_json(msg) -> AnsibleFailJson:
        """
        mock the fail_json method
        """
        raise AnsibleFailJson(msg)

#See the following for explanation of why fixtures are explicitely named
#https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html

@pytest.fixture(name="controller_version")
def controller_version_fixture():
    return ControllerVersion(MockAnsibleModule)

@pytest.fixture(name="image_install_options")
def image_install_options_fixture():
    return ImageInstallOptions(MockAnsibleModule)

@pytest.fixture(name="image_policies")
def image_policies_fixture():
    return ImagePolicies(MockAnsibleModule)

@pytest.fixture(name="image_policy_action")
def image_policy_action_fixture():
    return ImagePolicyAction(MockAnsibleModule)

@pytest.fixture(name="image_stage")
def image_stage_fixture():
    return ImageStage(MockAnsibleModule)

@pytest.fixture(name="image_upgrade_common")
def image_upgrade_common_fixture():
    return ImageUpgradeCommon(MockAnsibleModule)

@pytest.fixture(name="image_upgrade")
def image_upgrade_fixture():
    return ImageUpgrade(MockAnsibleModule)

@pytest.fixture(name="issu_details_by_ip_address")
def issu_details_by_ip_address_fixture():
    return SwitchIssuDetailsByIpAddress(MockAnsibleModule)

@pytest.fixture(name="issu_details_by_device_name")
def issu_details_by_device_name_fixture():
    return SwitchIssuDetailsByDeviceName(MockAnsibleModule)

@pytest.fixture(name="issu_details_by_serial_number")
def issu_details_by_serial_number_fixture() -> SwitchIssuDetailsBySerialNumber:
    return SwitchIssuDetailsBySerialNumber(MockAnsibleModule)

@contextmanager
def does_not_raise():
    """
    A context manager that does not raise an exception.
    """
    yield
