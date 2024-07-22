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
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details_v2 import \
    FabricDetailsByName as FabricDetailsByNameV2
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_maintenance_mode import \
    Common
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_maintenance_mode.fixture import \
    load_fixture

params_query = {
    "state": "query",
    "config": {"switches": [{"ip_address": "192.168.1.2"}]},
    "check_mode": False,
}


params = {
    "state": "merged",
    "config": {"switches": [{"ip_address": "192.168.1.2"}]},
    "check_mode": False,
}


class MockAnsibleModule:
    """
    Mock the AnsibleModule class
    """

    check_mode = False

    params = params
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

    def public_method_for_pylint(self):
        """
        Add one public method to appease pylint
        """


# See the following for explanation of why fixtures are explicitely named
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html


@pytest.fixture(name="common")
def common_fixture():
    """
    return instance of Common()
    """
    return Common(params)


@pytest.fixture(name="fabric_details_by_name_v2")
def fabric_details_by_name_v2_fixture():
    """
    Return FabricDetailsByName version 2 instance
    """
    return FabricDetailsByNameV2()


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


def configs_common(key: str) -> dict:
    """
    Return playbook configs for Common
    """
    data_file = "configs_Common"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def configs_merged(key: str) -> dict:
    """
    Return playbook configs for Merged
    """
    data_file = "configs_Merged"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def configs_want(key: str) -> dict:
    """
    Return playbook configs for Want
    """
    data_file = "configs_Want"
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


def payloads_merge(key: str) -> dict:
    """
    Return payloads for Merge
    """
    data_file = "payloads_Merge"
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


def responses_common(key: str) -> dict:
    """
    Return responses for Common
    """
    data_file = "responses_Common"
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


def responses_ep_maintenance_mode_deploy(key: str) -> dict:
    """
    Return responses for endpoint EpMaintenanceModeDeploy.
    """
    data_file = "responses_EpMaintenanceModeDeploy"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_ep_maintenance_mode_disable(key: str) -> dict:
    """
    Return responses for EpMaintenanceModeDisable().
    """
    data_file = "responses_EpMaintenanceModeDisable"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_ep_maintenance_mode_enable(key: str) -> dict:
    """
    Return responses for EpMaintenanceModeEnable().
    """
    data_file = "responses_EpMaintenanceModeEnable"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_ep_fabrics(key: str) -> dict:
    """
    Return responses for EpFabrics().
    """
    data_file = "responses_EpFabrics"
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


def responses_fabric_details_by_name_v2(key: str) -> dict:
    """
    Return responses for FabricDetailsByName version 2
    """
    data_file = "responses_FabricDetailsByName_V2"
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


def results_common(key: str) -> dict:
    """
    Return results for Common
    """
    data_file = "results_Common"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def results_merge(key: str) -> dict:
    """
    Return results for Merge
    """
    data_file = "results_Merge"
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
