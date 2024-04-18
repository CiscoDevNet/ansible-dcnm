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
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.common import \
    FabricCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.create import (
    FabricCreate, FabricCreateBulk, FabricCreateCommon)
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.delete import \
    FabricDelete
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details import (
    FabricDetails, FabricDetailsByName, FabricDetailsByNvPair)
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_summary import \
    FabricSummary
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.query import \
    FabricQuery
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.template_get import \
    TemplateGet
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.template_get_all import \
    TemplateGetAll
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.update import \
    FabricUpdateBulk
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.fixture import \
    load_fixture

params = {
    "state": "merged",
    "config": {"switches": [{"ip_address": "172.22.150.105"}]},
    "check_mode": False,
}


class ResponseGenerator:
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


# See the following for explanation of why fixtures are explicitely named
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html


@pytest.fixture(name="fabric_common")
def fabric_common_fixture():
    """
    return instance of FabricCommon()
    """
    instance = MockAnsibleModule()
    return FabricCommon(instance.params)


@pytest.fixture(name="fabric_create")
def fabric_create_fixture():
    """
    mock FabricCreate
    """
    instance = MockAnsibleModule()
    instance.state = "merged"
    return FabricCreate(instance.params)


@pytest.fixture(name="fabric_create_bulk")
def fabric_create_bulk_fixture():
    """
    mock FabricCreateBulk
    """
    instance = MockAnsibleModule()
    instance.state = "merged"
    return FabricCreateBulk(instance.params)


@pytest.fixture(name="fabric_create_common")
def fabric_create_common_fixture():
    """
    mock FabricCreateCommon
    """
    instance = MockAnsibleModule()
    instance.state = "merged"
    return FabricCreateCommon(instance.params)


@pytest.fixture(name="fabric_delete")
def fabric_delete_fixture():
    """
    mock FabricDelete
    """
    instance = MockAnsibleModule()
    instance.state = "deleted"
    return FabricDelete(instance.params)


@pytest.fixture(name="fabric_details")
def fabric_details_fixture():
    """
    mock FabricDetails
    """
    instance = MockAnsibleModule()
    instance.state = "merged"
    return FabricDetails(instance.params)


@pytest.fixture(name="fabric_details_by_name")
def fabric_details_by_name_fixture():
    """
    mock FabricDetailsByName
    """
    instance = MockAnsibleModule()
    instance.state = "merged"
    return FabricDetailsByName(instance.params)


@pytest.fixture(name="fabric_details_by_nv_pair")
def fabric_details_by_nv_pair_fixture():
    """
    mock FabricDetailsByNvPair
    """
    instance = MockAnsibleModule()
    instance.state = "merged"
    return FabricDetailsByNvPair(instance.params)


@pytest.fixture(name="fabric_query")
def fabric_query_fixture():
    """
    mock FabricQuery
    """
    instance = MockAnsibleModule()
    instance.state = "query"
    return FabricQuery(instance.params)


@pytest.fixture(name="fabric_summary")
def fabric_summary_fixture():
    """
    mock FabricSummary
    """
    instance = MockAnsibleModule()
    instance.state = "merged"
    return FabricSummary(instance.params)


@pytest.fixture(name="fabric_update_bulk")
def fabric_update_bulk_fixture():
    """
    mock FabricUpdateBulk
    """
    instance = MockAnsibleModule()
    instance.state = "merged"
    return FabricUpdateBulk(instance.params)


@pytest.fixture(name="template_get")
def template_get_fixture():
    """
    mock TemplateGet
    """
    return TemplateGet()


@pytest.fixture(name="template_get_all")
def template_get_all_fixture():
    """
    mock TemplateGetAll
    """
    return TemplateGetAll()


@contextmanager
def does_not_raise():
    """
    A context manager that does not raise an exception.
    """
    yield


def payloads_fabric_common(key: str) -> Dict[str, str]:
    """
    Return payloads for FabricCommon
    """
    data_file = "payloads_FabricCommon"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def payloads_fabric_create(key: str) -> Dict[str, str]:
    """
    Return payloads for FabricCreate
    """
    data_file = "payloads_FabricCreate"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def payloads_fabric_create_bulk(key: str) -> Dict[str, str]:
    """
    Return payloads for FabricCreateBulk
    """
    data_file = "payloads_FabricCreateBulk"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def payloads_fabric_create_common(key: str) -> Dict[str, str]:
    """
    Return payloads for FabricCreateCommon
    """
    data_file = "payloads_FabricCreateCommon"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def payloads_fabric_update_bulk(key: str) -> Dict[str, str]:
    """
    Return payloads for FabricUpdateBulk
    """
    data_file = "payloads_FabricUpdateBulk"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_common(key: str) -> Dict[str, str]:
    """
    Return responses for FabricCommon
    """
    data_file = "responses_FabricCommon"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_create(key: str) -> Dict[str, str]:
    """
    Return responses for FabricCreate
    """
    data_file = "responses_FabricCreate"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_create_bulk(key: str) -> Dict[str, str]:
    """
    Return responses for FabricCreateBulk
    """
    data_file = "responses_FabricCreateBulk"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_delete(key: str) -> Dict[str, str]:
    """
    Return responses for FabricDelete
    """
    data_file = "responses_FabricDelete"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_details(key: str) -> Dict[str, str]:
    """
    Return responses for FabricDetails
    """
    data_file = "responses_FabricDetails"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_details_by_name(key: str) -> Dict[str, str]:
    """
    Return responses for FabricDetailsByName
    """
    data_file = "responses_FabricDetailsByName"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_details_by_nv_pair(key: str) -> Dict[str, str]:
    """
    Return responses for FabricDetailsByNvPair
    """
    data_file = "responses_FabricDetailsByNvPair"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_query(key: str) -> Dict[str, str]:
    """
    Return responses for FabricQuery
    """
    data_file = "responses_FabricQuery"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_summary(key: str) -> Dict[str, str]:
    """
    Return responses for FabricSummary
    """
    data_file = "responses_FabricSummary"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_update_bulk(key: str) -> Dict[str, str]:
    """
    Return responses for FabricUpdateBulk
    """
    data_file = "responses_FabricUpdateBulk"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_template_get(key: str) -> Dict[str, str]:
    """
    Return responses for TemplateGet
    """
    data_file = "responses_TemplateGet"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_template_get_all(key: str) -> Dict[str, str]:
    """
    Return responses for TemplateGetAll
    """
    data_file = "responses_TemplateGetAll"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def results_fabric_details(key: str) -> Dict[str, str]:
    """
    Return results for FabricDetails
    """
    data_file = "results_FabricDetails"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def results_fabric_common(key: str) -> Dict[str, str]:
    """
    Return results for FabricCommon
    """
    data_file = "results_FabricCommon"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def results_fabric_create_bulk(key: str) -> Dict[str, str]:
    """
    Return results for FabricCreateBulk
    """
    data_file = "results_FabricCreateBulk"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def results_fabric_delete(key: str) -> Dict[str, str]:
    """
    Return results for FabricDelete
    """
    data_file = "results_FabricDelete"
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


def templates_param_info(key: str) -> Dict[str, str]:
    """
    Return fabric templates for ParamInfo
    """
    data_file = "templates_ParamInfo"
    data = load_fixture(data_file).get(key)
    return data
