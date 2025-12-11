# Copyright (c) 2025 Cisco and/or its affiliates.
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
# pylint: disable=line-too-long
"""
Utilities for dcnm_fabric_group module unit tests.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name


from contextlib import contextmanager

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric_group.create import FabricGroupCreate
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric_group.delete import FabricGroupDelete
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric_group.fabric_groups import FabricGroups
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric_group.query import FabricGroupQuery
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric_group.fixture import load_fixture

params = {
    "state": "merged",
    "config": {"fabric_groups": [{"FABRIC_NAME": "MFG1"}]},
    "check_mode": False,
}

params_query = {
    "state": "query",
    "config": {"fabric_groups": [{"FABRIC_NAME": "MFG1"}]},
    "check_mode": False,
}

params_delete = {
    "state": "deleted",
    "config": {"fabric_groups": [{"FABRIC_NAME": "MFG1"}]},
    "check_mode": False,
}


class MockAnsibleModule:
    """
    Mock the AnsibleModule class
    """

    check_mode = False

    params = {
        "state": "merged",
        "config": {"fabric_groups": [{"FABRIC_NAME": "MFG1"}]},
        "check_mode": False,
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

    def public_method_for_pylint(self):
        """
        Add one public method to appease pylint
        """


# See the following for explanation of why fixtures are explicitely named
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html


@pytest.fixture(name="fabric_group_create")
def fabric_group_create_fixture():
    """
    Return FabricGroupCreate() instance.
    """
    return FabricGroupCreate()


@pytest.fixture(name="fabric_groups")
def fabric_groups_fixture():
    """
    Return FabricGroups() instance.
    """
    return FabricGroups()


@pytest.fixture(name="fabric_group_query")
def fabric_group_query_fixture():
    """
    Return FabricGroupQuery() instance.
    """
    return FabricGroupQuery()


@pytest.fixture(name="fabric_group_delete")
def fabric_group_delete_fixture():
    """
    Return FabricGroupDelete() instance.
    """
    return FabricGroupDelete()


@contextmanager
def does_not_raise():
    """
    A context manager that does not raise an exception.
    """
    yield


def payloads_fabric_group_create(key: str) -> dict[str, str]:
    """
    Return payloads for FabricGroupCreate
    """
    data_file = "payloads_FabricGroupCreate"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_group_create(key: str) -> dict[str, str]:
    """
    Return responses for FabricGroupCreate
    """
    data_file = "responses_FabricGroupCreate"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_groups(key: str) -> dict[str, str]:
    """
    Return responses for FabricGroups
    """
    data_file = "responses_FabricGroups"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def rest_send_response_current(key: str) -> dict[str, str]:
    """
    Responses for RestSend().response_current property
    """
    data_file = "responses_RestSend"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_group_details(key: str) -> dict[str, str]:
    """
    Return responses for FabricGroupDetails
    """
    data_file = "responses_FabricGroupDetails"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_group_member_info(key: str) -> dict[str, str]:
    """
    Return responses for FabricGroupMemberInfo
    """
    data_file = "responses_FabricGroupMemberInfo"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_group_delete(key: str) -> dict[str, str]:
    """
    Return responses for FabricGroupDelete endpoint
    """
    data_file = "responses_FabricGroupDelete"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data
