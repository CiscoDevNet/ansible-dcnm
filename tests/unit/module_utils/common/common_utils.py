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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.log import \
    Log
from ansible_collections.cisco.dcnm.plugins.module_utils.common.params_validate import \
    ParamsValidate

from .fixture import load_fixture


class MockAnsibleModule:
    """
    Mock the AnsibleModule class
    """

    params = {"config": {"switches": [{"ip_address": "172.22.150.105"}]}}
    argument_spec = {
        "config": {"required": True, "type": "dict"},
        "state": {"default": "merged", "choices": ["merged", "deleted", "query"]},
    }
    supports_check_mode = True

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


@pytest.fixture(name="log")
def log_fixture():
    """
    mock Log
    """
    return Log(MockAnsibleModule)


@pytest.fixture(name="params_validate")
def params_validate_fixture():
    """
    mock ParamsValidate
    """
    return ParamsValidate(MockAnsibleModule)


@contextmanager
def does_not_raise():
    """
    A context manager that does not raise an exception.
    """
    yield


def load_playbook_config(key: str) -> Dict[str, str]:
    """
    Return playbook configs for common
    """
    playbook_file = "common_playbook_configs"
    playbook_config = load_fixture(playbook_file).get(key)
    print(f"load_playbook_config: {key} : {playbook_config}")
    return playbook_config


def responses_controller_version(key: str) -> Dict[str, str]:
    """
    Return ControllerVersion controller responses
    """
    response_file = "responses_ControllerVersion"
    response = load_fixture(response_file).get(key)
    print(f"responses_controller_version: {key} : {response}")
    return response
