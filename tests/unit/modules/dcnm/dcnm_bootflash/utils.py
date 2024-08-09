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
    "config": {"switches": [{"ip_address": "192.168.1.2"}]},
    "check_mode": False,
}


params_deleted = {
    "state": "deleted",
    "config": {"switches": [{"ip_address": "192.168.1.2"}]},
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


def payloads_deleted(key: str) -> dict:
    """
    Return payloads for Deleted
    """
    data_file = "payloads_Deleted"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def payloads_query(key: str) -> dict:
    """
    Return payloads for Query
    """
    data_file = "payloads_Query"
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


def responses_ep_bootflash_info(key: str) -> dict:
    """
    Return EpBootflashInfo() responses.
    """
    data_file = "responses_EpBootflashInfo"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_deleted(key: str) -> dict:
    """
    Return responses for Deleted
    """
    data_file = "responses_Deleted"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_query(key: str) -> dict:
    """
    Return responses for Query
    """
    data_file = "responses_Query"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_response_handler(key: str) -> dict:
    """
    Return responses for ResponseHandler
    """
    data_file = "responses_ResponseHandler"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def results_deleted(key: str) -> dict:
    """
    Return results for Deleted
    """
    data_file = "results_Deleted"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def results_query(key: str) -> dict:
    """
    Return results for Query
    """
    data_file = "results_Query"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def rest_send_response_current(key: str) -> dict:
    """
    Mocked return values for RestSend().response_current property
    """
    data_file = "response_current_RestSend"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def rest_send_result_current(key: str) -> dict:
    """
    Mocked return values for RestSend().result_current property
    """
    data_file = "result_current_RestSend"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data
