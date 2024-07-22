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
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.common import \
    FabricCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.config_deploy import \
    FabricConfigDeploy
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.config_save import \
    FabricConfigSave
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.create import (
    FabricCreate, FabricCreateBulk, FabricCreateCommon)
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.delete import \
    FabricDelete
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details import (
    FabricDetails, FabricDetailsByName, FabricDetailsByNvPair)
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details_v2 import \
    FabricDetails as FabricDetailsV2
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details_v2 import \
    FabricDetailsByName as FabricDetailsByNameV2
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details_v2 import \
    FabricDetailsByNvPair as FabricDetailsByNvPairV2
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_summary import \
    FabricSummary
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_types import \
    FabricTypes
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.query import \
    FabricQuery
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.replaced import \
    FabricReplacedBulk
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

    def public_method_for_pylint(self):
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


@pytest.fixture(name="fabric_config_deploy")
def fabric_config_deploy_fixture():
    """
    return instance of FabricConfigDeploy()
    """
    instance = MockAnsibleModule()
    return FabricConfigDeploy(instance.params)


@pytest.fixture(name="fabric_config_save")
def fabric_config_save_fixture():
    """
    return instance of FabricConfigSave()
    """
    instance = MockAnsibleModule()
    return FabricConfigSave(instance.params)


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


@pytest.fixture(name="fabric_details_v2")
def fabric_details_v2_fixture():
    """
    mock FabricDetails() v2
    """
    return FabricDetailsV2(params)


@pytest.fixture(name="fabric_details_by_name")
def fabric_details_by_name_fixture():
    """
    mock FabricDetailsByName
    """
    instance = MockAnsibleModule()
    instance.state = "merged"
    return FabricDetailsByName(instance.params)


@pytest.fixture(name="fabric_details_by_name_v2")
def fabric_details_by_name_v2_fixture():
    """
    mock FabricDetailsByName version 2
    """
    instance = MockAnsibleModule()
    instance.state = "query"
    instance.check_mode = False
    return FabricDetailsByNameV2(instance.params)


@pytest.fixture(name="fabric_details_by_nv_pair")
def fabric_details_by_nv_pair_fixture():
    """
    mock FabricDetailsByNvPair
    """
    instance = MockAnsibleModule()
    instance.state = "merged"
    return FabricDetailsByNvPair(instance.params)


@pytest.fixture(name="fabric_details_by_nv_pair_v2")
def fabric_details_by_nv_pair_v2_fixture():
    """
    mock FabricDetailsByNvPair version 2
    """
    instance = MockAnsibleModule()
    instance.state = "merged"
    return FabricDetailsByNvPairV2(instance.params)


@pytest.fixture(name="fabric_query")
def fabric_query_fixture():
    """
    mock FabricQuery
    """
    instance = MockAnsibleModule()
    instance.state = "query"
    return FabricQuery(instance.params)


@pytest.fixture(name="fabric_replaced_bulk")
def fabric_replaced_bulk_fixture():
    """
    mock FabricReplacedBulk
    """
    instance = MockAnsibleModule()
    instance.state = "replaced"
    return FabricReplacedBulk(instance.params)


@pytest.fixture(name="fabric_summary")
def fabric_summary_fixture():
    """
    mock FabricSummary
    """
    instance = MockAnsibleModule()
    instance.state = "merged"
    return FabricSummary(instance.params)


@pytest.fixture(name="fabric_types")
def fabric_types_fixture():
    """
    mock FabricTypes
    """
    return FabricTypes()


@pytest.fixture(name="fabric_update_bulk")
def fabric_update_bulk_fixture():
    """
    mock FabricUpdateBulk
    """
    instance = MockAnsibleModule()
    instance.state = "merged"
    return FabricUpdateBulk(instance.params)


@pytest.fixture(name="response_handler")
def response_handler_fixture():
    """
    mock ResponseHandler()
    """
    return ResponseHandler()


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


def nv_pairs_verify_playbook_params(key: str) -> dict[str, str]:
    """
    Return fabric nvPairs for VerifyPlaybookParams
    """
    data_file = "nv_pairs_VerifyPlaybookParams"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def payloads_fabric_common(key: str) -> dict[str, str]:
    """
    Return payloads for FabricCommon
    """
    data_file = "payloads_FabricCommon"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def payloads_fabric_create(key: str) -> dict[str, str]:
    """
    Return payloads for FabricCreate
    """
    data_file = "payloads_FabricCreate"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def payloads_fabric_create_bulk(key: str) -> dict[str, str]:
    """
    Return payloads for FabricCreateBulk
    """
    data_file = "payloads_FabricCreateBulk"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def payloads_fabric_create_common(key: str) -> dict[str, str]:
    """
    Return payloads for FabricCreateCommon
    """
    data_file = "payloads_FabricCreateCommon"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def payloads_fabric_replaced_bulk(key: str) -> dict[str, str]:
    """
    Return payloads for FabricReplacedBulk
    """
    data_file = "payloads_FabricReplacedBulk"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def payloads_fabric_update_bulk(key: str) -> dict[str, str]:
    """
    Return payloads for FabricUpdateBulk
    """
    data_file = "payloads_FabricUpdateBulk"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def payloads_verify_playbook_params(key: str) -> dict[str, str]:
    """
    Return payloads for VerifyPlaybookParams
    """
    data_file = "payloads_VerifyPlaybookParams"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_config_deploy(key: str) -> dict[str, str]:
    """
    Return responses for config_deploy requests
    """
    data_file = "responses_ConfigDeploy"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_config_save(key: str) -> dict[str, str]:
    """
    Return responses for config_save requests
    """
    data_file = "responses_ConfigSave"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_config_deploy(key: str) -> dict[str, str]:
    """
    Return responses for FabricConfigDeploy() class
    """
    data_file = "responses_FabricConfigDeploy"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_config_save(key: str) -> dict[str, str]:
    """
    Return responses for FabricConfigSave() class
    """
    data_file = "responses_FabricConfigSave"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_common(key: str) -> dict[str, str]:
    """
    Return responses for FabricCommon
    """
    data_file = "responses_FabricCommon"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_create(key: str) -> dict[str, str]:
    """
    Return responses for FabricCreate
    """
    data_file = "responses_FabricCreate"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_create_bulk(key: str) -> dict[str, str]:
    """
    Return responses for FabricCreateBulk
    """
    data_file = "responses_FabricCreateBulk"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_delete(key: str) -> dict[str, str]:
    """
    Return responses for FabricDelete
    """
    data_file = "responses_FabricDelete"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_details(key: str) -> dict[str, str]:
    """
    Return responses for FabricDetails
    """
    data_file = "responses_FabricDetails"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_details_v2(key: str) -> dict[str, str]:
    """
    Return responses for FabricDetails version 2
    """
    data_file = "responses_FabricDetails_V2"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_details_by_name(key: str) -> dict[str, str]:
    """
    Return responses for FabricDetailsByName
    """
    data_file = "responses_FabricDetailsByName"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_details_by_name_v2(key: str) -> dict[str, str]:
    """
    Return responses for FabricDetailsByName version 2
    """
    data_file = "responses_FabricDetailsByName_V2"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_details_by_nv_pair(key: str) -> dict[str, str]:
    """
    Return responses for FabricDetailsByNvPair
    """
    data_file = "responses_FabricDetailsByNvPair"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_details_by_nv_pair_v2(key: str) -> dict[str, str]:
    """
    Return responses for FabricDetailsByNvPair version 2
    """
    data_file = "responses_FabricDetailsByNvPair_V2"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_query(key: str) -> dict[str, str]:
    """
    Return responses for FabricQuery
    """
    data_file = "responses_FabricQuery"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_replaced_bulk(key: str) -> dict[str, str]:
    """
    Return responses for FabricReplacedBulk
    """
    data_file = "responses_FabricReplacedBulk"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_summary(key: str) -> dict[str, str]:
    """
    Return responses for FabricSummary
    """
    data_file = "responses_FabricSummary"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_fabric_update_bulk(key: str) -> dict[str, str]:
    """
    Return responses for FabricUpdateBulk
    """
    data_file = "responses_FabricUpdateBulk"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_response_handler(key: str) -> dict[str, str]:
    """
    Return responses for ResponseHandler
    """
    data_file = "responses_ResponseHandler"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_template_get(key: str) -> dict[str, str]:
    """
    Return responses for TemplateGet
    """
    data_file = "responses_TemplateGet"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def responses_template_get_all(key: str) -> dict[str, str]:
    """
    Return responses for TemplateGetAll
    """
    data_file = "responses_TemplateGetAll"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def results_fabric_details(key: str) -> dict[str, str]:
    """
    Return results for FabricDetails
    """
    data_file = "results_FabricDetails"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def results_fabric_common(key: str) -> dict[str, str]:
    """
    Return results for FabricCommon
    """
    data_file = "results_FabricCommon"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def results_fabric_create_bulk(key: str) -> dict[str, str]:
    """
    Return results for FabricCreateBulk
    """
    data_file = "results_FabricCreateBulk"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def results_fabric_delete(key: str) -> dict[str, str]:
    """
    Return results for FabricDelete
    """
    data_file = "results_FabricDelete"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def rest_send_response_current(key: str) -> dict[str, str]:
    """
    Mocked return values for RestSend().response_current property
    """
    data_file = "response_current_RestSend"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def rest_send_result_current(key: str) -> dict[str, str]:
    """
    Mocked return values for RestSend().result_current property
    """
    data_file = "result_current_RestSend"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


def templates_param_info(key: str) -> dict[str, str]:
    """
    Return fabric templates for ParamInfo
    """
    data_file = "templates_ParamInfo"
    data = load_fixture(data_file).get(key)
    return data


def templates_ruleset(key: str) -> dict[str, str]:
    """
    Return fabric templates for RuleSet
    """
    data_file = "templates_RuleSet"
    data = load_fixture(data_file).get(key)
    return data


def templates_verify_playbook_params(key: str) -> dict[str, str]:
    """
    Return fabric templates for VerifyPlaybookParams
    """
    data_file = "templates_VerifyPlaybookParams"
    data = load_fixture(data_file).get(key)
    return data
