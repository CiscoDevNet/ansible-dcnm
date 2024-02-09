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
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.create import (
    ImagePolicyCreate, ImagePolicyCreateBulk)
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.payload import (
    Config2Payload, Payload2Config)
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
        "state": {
            "default": "merged",
            "choices": ["deleted", "overridden", "merged", "query", "replaced"],
        },
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
    def fail_json(msg, **kwargs) -> AnsibleFailJson:
        """
        mock the fail_json method
        """
        raise AnsibleFailJson(msg, kwargs)

    def public_method_for_pylint(self) -> Any:
        """
        Add one public method to appease pylint
        """


# See the following for explanation of why fixtures are explicitely named
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html


@pytest.fixture(name="image_policy_create")
def image_policy_create_fixture():
    """
    mock ImagePolicyCreate
    """
    return ImagePolicyCreate(MockAnsibleModule)


@pytest.fixture(name="image_policy_create_bulk")
def image_policy_create_bulk_fixture():
    """
    mock ImagePolicyCreateBulk
    """
    return ImagePolicyCreateBulk(MockAnsibleModule)


@pytest.fixture(name="config2payload")
def config2payload_fixture():
    """
    mock Config2Payload
    Used in test_image_policy_payload.py
    """
    return Config2Payload(MockAnsibleModule)


@pytest.fixture(name="payload2config")
def payload2config_fixture():
    """
    mock Payload2Config
    Used in test_image_policy_payload.py
    """
    return Payload2Config(MockAnsibleModule)


@contextmanager
def does_not_raise():
    """
    A context manager that does not raise an exception.
    """
    yield


def data_payload(key: str) -> Dict[str, str]:
    """
    Return data for unit tests of the Payload() class
    """
    response_file = "data_payload"
    response = load_fixture(response_file).get(key)
    print(f"data_payload: {key} : {response}")
    return response


def payloads_image_policy_create(key: str) -> Dict[str, str]:
    """
    Return payloads for ImagePolicyCreate
    """
    payload_file = "payloads_ImagePolicyCreate"
    payload = load_fixture(payload_file).get(key)
    print(f"{payload_file}: {key} : {payload}")
    return payload


def payloads_image_policy_create_bulk(key: str) -> Dict[str, str]:
    """
    Return payloads for ImagePolicyCreateBulk
    """
    payload_file = "payloads_ImagePolicyCreateBulk"
    payload = load_fixture(payload_file).get(key)
    print(f"{payload_file}: {key} : {payload}")
    return payload
