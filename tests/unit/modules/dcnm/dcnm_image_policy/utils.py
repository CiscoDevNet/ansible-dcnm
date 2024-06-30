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
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.delete import \
    ImagePolicyDelete
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.payload import (
    Config2Payload, Payload2Config)
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.query import \
    ImagePolicyQuery
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.replace import \
    ImagePolicyReplaceBulk
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.update import (
    ImagePolicyUpdate, ImagePolicyUpdateBulk)
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_image_policy.fixture import \
    load_fixture

def get_state(action):
    if action in ["create", "update"]:
        state = "merged"
    elif action == "delete":
        state = "deleted"
    elif action == "query":
        state = "query"
    elif action == "replace":
        state = "replaced"
    else:
        state = "merged"
    return state

params = {
    "state": "merged",
    "check_mode": False,
    "config": [
        {
            "name": "NR1F",
            "agnostic": False,
            "description": "NR1F",
            "platform": "N9K",
            "type": "PLATFORM"}
    ]
}

class GenerateResponses:
    """
    Given a generator, return the items in the generator with
    each call to the next property

    For usage in the context of dcnm_image_policy unit tests, see:
        test: test_image_policy_create_bulk_00037
        file: tests/unit/modules/dcnm/dcnm_image_policy/test_image_policy_create_bulk.py

    Simplified usage example below.

    def responses():
        yield {"key1": "value1"}
        yield {"key2": "value2"}

    gen = GenerateResponses(responses())

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

    def public_method_for_pylint(self) -> Any:
        """
        Add one public method to appease pylint
        """


class MockAnsibleModule:
    """
    Mock the AnsibleModule class
    """

    check_mode = False

    params = {
        "state": "merged",
        "config": {"switches": [{"ip_address": "172.22.150.105"}]},
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

    def public_method_for_pylint(self) -> Any:
        """
        Add one public method to appease pylint
        """


class MockImagePolicies:
    """
    Mock the ImagePolicies class to return various values for all_policies
    """

    def __init__(self, key: str) -> None:
        self.key = key
        self.properties = {}
        self.properties["policy_name"] = None
        self.properties["results"] = None

    def refresh(self) -> None:
        """
        bypass dcnm_send
        """

    @property
    def all_policies(self):
        """
        Mock the return value of all_policies
        all_policies contains all image policies that exist on the controller
        """
        return image_policies_all_policies(self.key)

    @property
    def name(self):
        """
        Return the name of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        try:
            return (
                image_policies_all_policies(self.key)
                .get(self.policy_name, None)
                .get("policyName")
            )
        except AttributeError:
            return None

    @property
    def policy_name(self):
        """
        Set the name of the policy to query.

        This must be set prior to accessing any other properties
        """
        return self.properties.get("policy_name")

    @policy_name.setter
    def policy_name(self, value):
        self.properties["policy_name"] = value

    @property
    def ref_count(self):
        """
        Return the reference count of the policy matching self.policy_name,
        if it exists.  The reference count is the number of switches using
        this policy.
        Return None otherwise
        """
        try:
            return (
                image_policies_all_policies(self.key)
                .get(self.policy_name, None)
                .get("ref_count")
            )
        except AttributeError:
            return None

    @property
    def results(self):
        """
        An instance of the Results class.
        """
        return self.properties["results"]

    @results.setter
    def results(self, value):
        self.properties["results"] = value


# See the following for explanation of why fixtures are explicitely named
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html



@pytest.fixture(name="image_policy_create")
def image_policy_create_fixture():
    """
    Return ImagePolicyCreate with params set.
    """
    instance = ImagePolicyCreate()
    instance.params = params
    params.update({"state": get_state(instance.action)})
    return instance


@pytest.fixture(name="image_policy_create_bulk")
def image_policy_create_bulk_fixture():
    """
    Return ImagePolicyCreateBulk with params set.
    """
    instance = ImagePolicyCreateBulk()
    instance.params = params
    params.update({"state": get_state(instance.action)})
    return instance


@pytest.fixture(name="image_policy_delete")
def image_policy_delete_fixture():
    """
    Return ImagePolicyDelete with params set.
    """
    instance = ImagePolicyDelete()
    instance.params = params
    params.update({"state": get_state(instance.action)})
    return instance


@pytest.fixture(name="image_policy_query")
def image_policy_query_fixture():
    """
    Return ImagePolicyQuery with params set.
    """
    instance = ImagePolicyQuery()
    instance.params = params
    params.update({"state": get_state(instance.action)})
    return instance


@pytest.fixture(name="image_policy_replace_bulk")
def image_policy_replace_bulk_fixture():
    """
    Return ImagePolicyReplaceBulk with params set.
    """
    instance = ImagePolicyReplaceBulk()
    instance.params = params
    params.update({"state": get_state(instance.action)})
    return instance


@pytest.fixture(name="image_policy_update")
def image_policy_update_fixture():
    """
    Return ImagePolicyUpdate with params set.
    """
    instance = ImagePolicyUpdate()
    instance.params = params
    params.update({"state": get_state(instance.action)})
    return instance


@pytest.fixture(name="image_policy_update_bulk")
def image_policy_update_bulk_fixture():
    """
    Return ImagePolicyUpdateBulk with params set.
    """
    instance = ImagePolicyUpdateBulk()
    instance.params = params
    params.update({"state": get_state(instance.action)})
    return instance


@pytest.fixture(name="config2payload")
def config2payload_fixture():
    """
    mock Config2Payload
    Used in test_image_policy_payload.py
    """
    instance = MockAnsibleModule()
    instance.state = "merged"
    return Config2Payload(instance)


@pytest.fixture(name="payload2config")
def payload2config_fixture():
    """
    mock Payload2Config
    Used in test_image_policy_payload.py
    """
    instance = MockAnsibleModule()
    instance.state = "merged"
    return Payload2Config(instance)


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
    data_file = "data_payload"
    data = load_fixture(data_file).get(key)
    print(f"data_payload: {key} : {data}")
    return data


def payloads_image_policy_create(key: str) -> Dict[str, str]:
    """
    Return payloads for ImagePolicyCreate
    """
    data_file = "payloads_ImagePolicyCreate"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def payloads_image_policy_create_bulk(key: str) -> Dict[str, str]:
    """
    Return payloads for ImagePolicyCreateBulk
    """
    data_file = "payloads_ImagePolicyCreateBulk"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def payloads_image_policy_replace_bulk(key: str) -> Dict[str, str]:
    """
    Return payloads for ImagePolicyReplaceBulk
    """
    data_file = "payloads_ImagePolicyReplaceBulk"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def payloads_image_policy_update(key: str) -> Dict[str, str]:
    """
    Return payloads for ImagePolicyUpdate
    """
    data_file = "payloads_ImagePolicyUpdate"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def payloads_image_policy_update_bulk(key: str) -> Dict[str, str]:
    """
    Return payloads for ImagePolicyUpdateBulk
    """
    data_file = "payloads_ImagePolicyUpdateBulk"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_ep_policies(key: str) -> Dict[str, str]:
    """
    Return responses for EpPolicies() endpoint
    """
    data_file = "responses_EpPolicies"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_ep_policy_create(key: str) -> Dict[str, str]:
    """
    Return responses for EpPolicyCreate() endpoint
    """
    data_file = "responses_EpPolicyCreate"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_ep_policy_edit(key: str) -> Dict[str, str]:
    """
    Return responses for EpPolicyEdit() endpoint
    """
    data_file = "responses_EpPolicyEdit"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_image_policies(key: str) -> Dict[str, str]:
    """
    Return responses for ImagePolicies
    Used in MockImagePolicies
    """
    data_file = "responses_ImagePolicies"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_image_policy_create(key: str) -> Dict[str, str]:
    """
    Return responses for ImagePolicyCreate
    """
    data_file = "responses_ImagePolicyCreate"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_image_policy_create_bulk(key: str) -> Dict[str, str]:
    """
    Return responses for ImagePolicyCreateBulk
    """
    data_file = "responses_ImagePolicyCreateBulk"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_image_policy_delete(key: str) -> Dict[str, str]:
    """
    Return responses for ImagePolicyDelete
    """
    data_file = "responses_ImagePolicyDelete"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_image_policy_replace_bulk(key: str) -> Dict[str, str]:
    """
    Return responses for ImagePolicyReplaceBulk
    """
    data_file = "responses_ImagePolicyReplaceBulk"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_image_policy_update(key: str) -> Dict[str, str]:
    """
    Return responses for ImagePolicyUpdate
    """
    data_file = "responses_ImagePolicyUpdate"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_image_policy_update_bulk(key: str) -> Dict[str, str]:
    """
    Return responses for ImagePolicyUpdateBulk
    """
    data_file = "responses_ImagePolicyUpdateBulk"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def results_image_policies(key: str) -> Dict[str, str]:
    """
    Return results for ImagePolicies
    Used in MockImagePolicies
    """
    data_file = "results_ImagePolicies"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def results_image_policy_create_bulk(key: str) -> Dict[str, str]:
    """
    Return results for ImagePolicyCreateBulk
    """
    data_file = "results_ImagePolicyCreateBulk"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def results_image_policy_delete(key: str) -> Dict[str, str]:
    """
    Return results for ImagePolicyDelete
    """
    data_file = "results_ImagePolicyDelete"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def results_image_policy_replace_bulk(key: str) -> Dict[str, str]:
    """
    Return results for ImagePolicyReplaceBulk
    """
    data_file = "results_ImagePolicyReplaceBulk"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def results_image_policy_task_result(key: str) -> Dict[str, str]:
    """
    Return results for ImagePolicyTaskResult
    """
    data_file = "results_ImagePolicyTaskResult"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def results_image_policy_update(key: str) -> Dict[str, str]:
    """
    Return results for ImagePolicyUpdate
    """
    data_file = "results_ImagePolicyUpdate"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def results_image_policy_update_bulk(key: str) -> Dict[str, str]:
    """
    Return results for ImagePolicyUpdateBulk
    """
    data_file = "results_ImagePolicyUpdateBulk"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def image_policies_all_policies(key: str) -> Dict[str, str]:
    """
    Return mocked return values for ImagePolicies().all_policies property
    """
    data_file = "all_policies_ImagePolicies"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def rest_send_response_current(key: str) -> Dict[str, str]:
    """
    Mocked return values for RestSend().response_current property
    """
    data_file = "response_current_RestSend"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def rest_send_result_current(key: str) -> Dict[str, str]:
    """
    Mocked return values for RestSend().result_current property
    """
    data_file = "result_current_RestSend"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data
