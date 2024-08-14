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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.response_handler import \
    ResponseHandler
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_bootflash.fixture import \
    load_fixture

params_query = {
    "state": "query",
    "config": {
        "switches": [{"ip_address": "192.168.1.2"}],
        "targets": [{"filepath": "bootflash:/testfile", "supervisor": "active"}],
    },
    "check_mode": False,
}


params_deleted = {
    "state": "deleted",
    "config": {
        "switches": [{"ip_address": "192.168.1.2"}],
        "targets": [{"filepath": "bootflash:/testfile", "supervisor": "active"}],
    },
    "check_mode": False,
}


class MockAnsibleModule:
    """
    Mock the AnsibleModule class
    """

    check_mode = False

    params = params_query
    argument_spec = {
        "config": {"required": True, "type": "dict"},
        "state": {
            "default": "query",
            "choices": ["deleted", "query"],
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

    def public_method_for_pylint(self):
        """
        Add one public method to appease pylint
        """


# See the following for explanation of why fixtures are explicitely named
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html


@pytest.fixture(name="response_handler")
def response_handler_fixture():
    """
    mock ResponseHandler()
    """
    return ResponseHandler()


@contextmanager
def does_not_raise():
    """
    A context manager that does not raise an exception.
    """
    yield


def configs_deleted(key: str) -> dict:
    """
    Return playbook configs for Deleted
    """
    data_file = "configs_Deleted"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def configs_query(key: str) -> dict:
    """
    Return playbook configs for Query
    """
    data_file = "configs_Query"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def file_info(key: str) -> dict:
    """
    Return file_info for ConvertFileInfoToTarget().file_info.setter
    """
    data_file = "file_info_ConvertFileInfoToTarget"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def payloads_bootflash_files(key: str) -> dict:
    """
    Return payloads for BootflashFiles()
    """
    data_file = "payloads_BootflashFiles"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_ep_all_switches(key: str) -> dict:
    """
    Return EpAllSwitches() responses.
    """
    data_file = "responses_EpAllSwitches"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_ep_bootflash_discovery(key: str) -> dict:
    """
    Return EpBootflashDiscovery() responses.
    """
    data_file = "responses_EpBootflashDiscovery"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_ep_bootflash_files(key: str) -> dict:
    """
    Return EpBootflashFiles() responses.
    """
    data_file = "responses_EpBootflashFiles"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_ep_bootflash_info(key: str) -> dict:
    """
    Return EpBootflashInfo() responses.
    """
    data_file = "responses_EpBootflashInfo"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def targets(key: str) -> dict:
    """
    Return target dictionaries for BootflashFiles unit tests.
    """
    data_file = "targets"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def targets_convert_file_info_to_target(key: str) -> dict:
    """
    Return target dictionaries used for ConvertFileInfoToTarget unit test asserts.
    """
    data_file = "targets_ConvertFileInfoToTarget"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data
