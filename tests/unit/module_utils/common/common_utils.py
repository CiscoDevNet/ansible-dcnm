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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.controller_features import \
    ControllerFeatures
from ansible_collections.cisco.dcnm.plugins.module_utils.common.controller_version import \
    ControllerVersion
from ansible_collections.cisco.dcnm.plugins.module_utils.common.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.common.log import Log
from ansible_collections.cisco.dcnm.plugins.module_utils.common.maintenance_mode import \
    MaintenanceMode
from ansible_collections.cisco.dcnm.plugins.module_utils.common.maintenance_mode_info import \
    MaintenanceModeInfo
from ansible_collections.cisco.dcnm.plugins.module_utils.common.merge_dicts import \
    MergeDicts
from ansible_collections.cisco.dcnm.plugins.module_utils.common.merge_dicts_v2 import \
    MergeDicts as MergeDictsV2
from ansible_collections.cisco.dcnm.plugins.module_utils.common.params_validate import \
    ParamsValidate
from ansible_collections.cisco.dcnm.plugins.module_utils.common.params_validate_v2 import \
    ParamsValidate as ParamsValidateV2
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_dcnm import \
    Sender as SenderDcnm
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_file import \
    Sender as SenderFile

from .fixture import load_fixture

params = {
    "state": "merged",
    "config": {"switches": [{"ip_address": "172.22.150.105"}]},
    "check_mode": False,
}


class ResponseGenerator:
    """
    Given a coroutine which yields dictionaries, return the yielded items
    with each call to the next property

    For usage in the context of dcnm_image_policy unit tests, see:
        test: test_image_policy_create_bulk_00037
        file: tests/unit/modules/dcnm/dcnm_image_policy/test_image_policy_create_bulk.py

    Simplified usage example below.

    def responses():
        yield {"key1": "value1"}
        yield {"key2": "value2"}

    gen = ResponseGenerator(responses())

    print(gen.next) # {"key1": "value1"}
    print(gen.next) # {"key2": "value2"}
    """

    def __init__(self, gen):
        self.gen = gen

    @property
    def next(self):
        """
        Return the next item in the generator
        """
        return next(self.gen)

    @property
    def implements(self):
        """
        ### Summary
        Used by Sender() classes to verify Sender().gen is a
        response generator which implements the response_generator
        interfacee.
        """
        return "response_generator"

    def public_method_for_pylint(self):
        """
        Add one public method to appease pylint
        """


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
        raise AnsibleFailJson(msg)

    def public_method_for_pylint(self):
        """
        Add one public method to appease pylint
        """


# See the following for explanation of why fixtures are explicitely named
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html


@pytest.fixture(name="controller_features")
def controller_features_fixture():
    """
    return ControllerFeatures instance.
    """
    return ControllerFeatures()


@pytest.fixture(name="controller_version")
def controller_version_fixture():
    """
    return ControllerVersion instance.
    """
    return ControllerVersion()


@pytest.fixture(name="image_policies")
def image_policies_fixture():
    """
    Return ImagePolicies instance.
    """
    return ImagePolicies()


@pytest.fixture(name="sender_dcnm")
def sender_dcnm_fixture():
    """
    return Send() imported from sender_dcnm.py
    """
    instance = SenderDcnm()
    instance.ansible_module = MockAnsibleModule
    return instance


@pytest.fixture(name="sender_file")
def sender_file_fixture():
    """
    return Send() imported from sender_file.py
    """

    def responses():
        yield {}

    instance = SenderFile()
    instance.gen = ResponseGenerator(responses())
    return instance


@pytest.fixture(name="log")
def log_fixture():
    """
    return Log with mocked AnsibleModule
    """
    return Log(MockAnsibleModule)


@pytest.fixture(name="maintenance_mode")
def maintenance_mode_fixture():
    """
    return MaintenanceMode
    """
    return MaintenanceMode(params)


@pytest.fixture(name="maintenance_mode_info")
def maintenance_mode_info_fixture():
    """
    return MaintenanceModeInfo
    """
    return MaintenanceModeInfo(params)


@pytest.fixture(name="merge_dicts")
def merge_dicts_fixture():
    """
    return MergeDicts with mocked AnsibleModule
    """
    return MergeDicts(MockAnsibleModule)


@pytest.fixture(name="merge_dicts_v2")
def merge_dicts_v2_fixture():
    """
    return MergeDicts() version 2
    """
    return MergeDictsV2()


@pytest.fixture(name="params_validate")
def params_validate_fixture():
    """
    return ParamsValidate with mocked AnsibleModule
    """
    return ParamsValidate(MockAnsibleModule)


@pytest.fixture(name="params_validate_v2")
def params_validate_v2_fixture():
    """
    return ParamsValidate version 2
    """
    return ParamsValidateV2()


@contextmanager
def does_not_raise():
    """
    A context manager that does not raise an exception.
    """
    yield


def merge_dicts_data(key: str) -> dict[str, str]:
    """
    Return data from merge_dicts.json for merge_dicts unit tests.
    """
    data_file = "merge_dicts"
    data = load_fixture(data_file).get(key)
    print(f"merge_dicts_data: {key} : {data}")
    return data


def merge_dicts_v2_data(key: str) -> dict[str, str]:
    """
    Return data from merge_dicts_v2.json for merge_dicts_v2 unit tests.
    """
    data_file = "merge_dicts_v2"
    data = load_fixture(data_file).get(key)
    print(f"merge_dicts_v2_data: {key} : {data}")
    return data


def responses_deploy_maintenance_mode(key: str) -> dict[str, str]:
    """
    Return data in responses_DeployMaintenanceMode.json
    """
    response_file = "responses_DeployMaintenanceMode"
    response = load_fixture(response_file).get(key)
    print(f"responses_deploy_maintenance_mode: {key} : {response}")
    return response


def responses_controller_features(key: str) -> dict[str, str]:
    """
    Return data in responses_ControllerFeatures.json
    """
    response_file = "responses_ControllerFeatures"
    response = load_fixture(response_file).get(key)
    return response


def responses_ep_version(key: str) -> dict[str, str]:
    """
    Return responses for endpoint EpVersion.
    """
    response_file = "responses_ep_version"
    response = load_fixture(response_file).get(key)
    print(f"responses_ep_version: {key} : {response}")
    return response


def responses_fabric_details_by_name(key: str) -> dict[str, str]:
    """
    Return data in responses_FabricDetailsByName.json
    """
    response_file = "responses_FabricDetailsByName"
    response = load_fixture(response_file).get(key)
    print(f"responses_fabric_details_by_name: {key} : {response}")
    return response


def responses_ep_policies(key: str) -> dict[str, str]:
    """
    Return controller responses for the EpPolicies() endpoint.
    """
    response_file = "responses_ep_policies"
    response = load_fixture(response_file).get(key)
    print(f"responses_ep_policies: {key} : {response}")
    return response


def responses_maintenance_mode(key: str) -> dict[str, str]:
    """
    Return data in responses_MaintenanceMode.json
    """
    response_file = "responses_MaintenanceMode"
    response = load_fixture(response_file).get(key)
    print(f"responses_maintenance_mode: {key} : {response}")
    return response


def responses_sender_dcnm(key: str) -> dict[str, str]:
    """
    Return data in responses_SenderDcnm.json
    """
    response_file = "responses_SenderDcnm"
    response = load_fixture(response_file).get(key)
    print(f"responses_sender_dcnm: {key} : {response}")
    return response


def responses_sender_file(key: str) -> dict[str, str]:
    """
    Return data in responses_SenderFile.json
    """
    response_file = "responses_SenderFile"
    response = load_fixture(response_file).get(key)
    print(f"responses_sender_file: {key} : {response}")
    return response


def responses_switch_details(key: str) -> dict[str, str]:
    """
    Return data in responses_SwitchDetails.json
    """
    response_file = "responses_SwitchDetails"
    response = load_fixture(response_file).get(key)
    print(f"responses_switch_details: {key} : {response}")
    return response
