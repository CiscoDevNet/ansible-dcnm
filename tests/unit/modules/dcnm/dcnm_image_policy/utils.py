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
from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.common.controller_version import \
    ControllerVersion
from ansible_collections.cisco.dcnm.plugins.module_utils.common.params_validate import \
    ParamsValidate
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policy_action import \
    ImagePolicyAction
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.common import \
    ImagePolicyCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.payload import (
    Config2Payload, Payload, Payload2Config)
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_image_policy.fixture import \
    load_fixture


class MockAnsibleModule:
    """
    Mock the AnsibleModule class
    """

    params = {
        "state": "merged",
        "config": {"switches": [{"ip_address": "172.22.150.105"}]},
    }
    argument_spec = {
        "config": {"required": True, "type": "dict"},
        "state": {"default": "merged", "choices": ["merged", "deleted", "query"]},
    }
    supports_check_mode = True

    @property
    def state(self):
        """
        return the state
        """
        return self.params["state"]

    @state.setter
    def state(self, value):
        """
        set the state
        """
        self.params["state"] = value

    @staticmethod
    def fail_json(msg) -> AnsibleFailJson:
        """
        mock the fail_json method
        """
        raise AnsibleFailJson(msg)

    def public_method_for_pylint(self) -> Any:
        """
        Add one public method to appease pylint
        """


# See the following for explanation of why fixtures are explicitely named
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html


@pytest.fixture(name="controller_version")
def controller_version_fixture():
    """
    mock ControllerVersion
    """
    return ControllerVersion(MockAnsibleModule)


@pytest.fixture(name="image_policy_common")
def image_policy_common_fixture():
    """
    mock ImagePolicyCommon
    """
    return ImagePolicyCommon(MockAnsibleModule)


@pytest.fixture(name="image_policies")
def image_policies_fixture():
    """
    mock ImagePolicies
    """
    return ImagePolicies(MockAnsibleModule)


@pytest.fixture(name="image_policy_action")
def image_policy_action_fixture():
    """
    mock ImagePolicyAction
    """
    return ImagePolicyAction(MockAnsibleModule)


@pytest.fixture(name="params_validate")
def params_validate_fixture():
    """
    mock ParamsValidate
    """
    return ParamsValidate(MockAnsibleModule)


@pytest.fixture(name="config2payload")
def config2payload_fixture():
    """
    mock Config2Payload
    """
    return Config2Payload(MockAnsibleModule)


@pytest.fixture(name="payload2config")
def payload2config_fixture():
    """
    mock Payload2Config
    """
    return Payload2Config(MockAnsibleModule)


@contextmanager
def does_not_raise():
    """
    A context manager that does not raise an exception.
    """
    yield


def load_playbook_config(key: str) -> Dict[str, str]:
    """
    Return playbook configs for ImagePolicyTask
    """
    playbook_file = "image_policy_playbook_configs"
    playbook_config = load_fixture(playbook_file).get(key)
    print(f"load_playbook_config: {key} : {playbook_config}")
    return playbook_config


def payloads_image_policy(key: str) -> Dict[str, str]:
    """
    Return payloads for ImagePolicy
    """
    payload_file = "image_policy_payloads_ImagePolicy"
    payload = load_fixture(payload_file).get(key)
    print(f"payload_data_image_policy: {key} : {payload}")
    return payload


def responses_controller_version(key: str) -> Dict[str, str]:
    """
    Return ControllerVersion controller responses
    """
    response_file = "image_policy_responses_ControllerVersion"
    response = load_fixture(response_file).get(key)
    print(f"responses_controller_version: {key} : {response}")
    return response


def responses_image_policies(key: str) -> Dict[str, str]:
    """
    Return ImagePolicies controller responses
    """
    response_file = "image_policy_responses_ImagePolicies"
    response = load_fixture(response_file).get(key)
    print(f"responses_image_policies: {key} : {response}")
    return response


def responses_image_policy_action(key: str) -> Dict[str, str]:
    """
    Return ImagePolicyAction controller responses
    """
    response_file = "image_policy_responses_ImagePolicyAction"
    response = load_fixture(response_file).get(key)
    print(f"responses_image_policy_action: {key} : {response}")
    return response


def responses_image_policy_common(key: str) -> Dict[str, str]:
    """
    Return ImagePolicyCommon controller responses
    """
    response_file = "image_policy_responses_ImagePolicyCommon"
    response = load_fixture(response_file).get(key)
    verb = response.get("METHOD")
    print(f"{key} : {verb} : {response}")
    return {"response": response, "verb": verb}


def data_payload(key: str) -> Dict[str, str]:
    """
    Return data for Payload unit tests
    """
    response_file = "data_payload"
    response = load_fixture(response_file).get(key)
    print(f"data_payload: {key} : {response}")
    return response
