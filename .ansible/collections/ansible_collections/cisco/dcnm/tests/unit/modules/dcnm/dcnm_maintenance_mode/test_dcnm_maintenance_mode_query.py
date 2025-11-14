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

# See the following regarding *_fixture imports
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html
# Due to the above, we also need to disable unused-import
# Also, fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=protected-access
# pylint: disable=use-implicit-booleaness-not-comparison

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import copy
import inspect

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.response_handler import \
    ResponseHandler
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_file import \
    Sender
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_maintenance_mode import \
    Query
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_maintenance_mode.utils import (
    MockAnsibleModule, configs_query, does_not_raise, params_query,
    responses_ep_all_switches, responses_ep_fabrics)


def test_dcnm_maintenance_mode_query_00000() -> None:
    """
    ### Classes and Methods
    - Common
        - __init__()

    ### Summary
    - Verify the class attributes are initialized to expected values.

    ### Test
    - Class attributes are initialized to expected values.
    - Exception is not raised.
    """
    with does_not_raise():
        instance = Query(params_query)
        switches = instance.config.get("switches", None)

    assert instance.class_name == "Query"
    assert instance.log.name == "dcnm.Query"

    assert instance.check_mode is False
    assert instance.state == "query"

    assert isinstance(instance.config, dict)
    assert isinstance(switches, list)
    assert switches[0].get("ip_address", None) == "192.168.1.2"

    assert instance.have == {}
    assert instance.query == []
    assert instance.want == []

    assert instance.results.class_name == "Results"
    assert instance.results.state == "query"
    assert instance.results.check_mode is False


def test_dcnm_maintenance_mode_query_00100() -> None:
    """
    ### Classes and Methods
    - Query()
        - commit()

    ### Summary
    -   Verify ``commit()`` happy path.
    -   No exceptions are raised.
    -   want contains expected structure and values.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    def configs():
        yield configs_query(f"{key}a")

    gen_configs = ResponseGenerator(configs())

    def responses():
        yield responses_ep_all_switches(f"{key}a")
        yield responses_ep_fabrics(f"{key}a")

    gen_responses = ResponseGenerator(responses())

    params_test = copy.deepcopy(params_query)
    params_test.update({"config": gen_configs.next})

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params_test)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Query(params_query)
        instance.rest_send = rest_send
        instance.config = params_test.get("config")
        instance.commit()
    assert instance.want[0].get("ip_address", None) == "192.168.1.2"
    assert instance.want[1].get("ip_address", None) == "192.168.1.3"

    switch_2 = instance.results.diff[2]["192.168.1.2"]
    switch_3 = instance.results.diff[2]["192.168.1.3"]

    assert switch_2.get("fabric_deployment_disabled", None) is False
    assert switch_3.get("fabric_deployment_disabled", None) is False

    assert switch_2.get("fabric_freeze_mode", None) is False
    assert switch_3.get("fabric_freeze_mode", None) is False

    assert switch_2.get("fabric_name", None) == "VXLAN_EVPN_Fabric"
    assert switch_3.get("fabric_name", None) == "VXLAN_EVPN_Fabric"

    assert switch_2.get("fabric_read_only", None) is False
    assert switch_3.get("fabric_read_only", None) is False

    assert switch_2.get("ip_address", None) == "192.168.1.2"
    assert switch_3.get("ip_address", None) == "192.168.1.3"

    assert switch_2.get("mode", None) == "maintenance"
    assert switch_3.get("mode", None) == "maintenance"

    assert switch_2.get("role", None) == "leaf"
    assert switch_3.get("role", None) == "leaf"

    assert switch_2.get("serial_number", None) == "FD2222222GA"
    assert switch_3.get("serial_number", None) == "FD3333333GA"

    assert instance.results.metadata[0]["action"] == "switch_details"
    assert instance.results.metadata[1]["action"] == "fabric_details"
    assert instance.results.metadata[2]["action"] == "maintenance_mode_info"

    assert instance.results.metadata[0]["state"] == "query"
    assert instance.results.metadata[1]["state"] == "query"
    assert instance.results.metadata[2]["state"] == "query"

    assert instance.results.metadata[0]["check_mode"] is False
    assert instance.results.metadata[1]["check_mode"] is False
    assert instance.results.metadata[2]["check_mode"] is False

    assert instance.results.result[0]["found"] is True
    assert instance.results.result[1]["found"] is True

    assert instance.results.result[2]["changed"] is False

    assert instance.results.result[0]["success"] is True
    assert instance.results.result[1]["success"] is True
    assert instance.results.result[2]["success"] is True


def test_dcnm_maintenance_mode_query_00200() -> None:
    """
    ### Classes and Methods
    - Query()
        - commit()

    ### Summary
    -   Verify ``commit()`` raises ``ValueError`` when rest_send has not
        been set.
    """
    with does_not_raise():
        instance = Query(params_query)
    match = r"Query\.commit:\s+"
    match += r"rest_send must be set before calling commit\."
    with pytest.raises(ValueError, match=match):
        instance.commit()

    assert len(instance.results.diff) == 0
    assert len(instance.results.metadata) == 0
    assert len(instance.results.response) == 0
    assert len(instance.results.result) == 0


def test_dcnm_maintenance_mode_query_00300(monkeypatch) -> None:
    """
    ### Classes and Methods
    - Query()
        - get_need()
        - commit()

    ### Summary
    -   Verify ``get_need()`` raises ``ValueError`` when ip_address
        does not exist in self.have.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    def configs():
        yield configs_query(f"{key}a")

    gen_configs = ResponseGenerator(configs())

    def responses():
        yield

    gen_responses = ResponseGenerator(responses())

    params_test = copy.deepcopy(params_query)
    params_test.update({"config": gen_configs.next})

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params_query)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Query(params_test)
        instance.rest_send = rest_send
        instance.config = params_test.get("config")

    def mock_get_have():
        raise ValueError("Query.get_need: Mocked ValueError.")

    match = r"Query\.commit:\s+"
    match += r"Error while retrieving switch information from the controller\.\s+"
    match += r"Error detail: Query\.get_need: Mocked ValueError\."
    with pytest.raises(ValueError, match=match):
        monkeypatch.setattr(instance, "get_have", mock_get_have)
        instance.commit()

    assert len(instance.results.diff) == 0
    assert len(instance.results.metadata) == 0
    assert len(instance.results.response) == 0
    assert len(instance.results.result) == 0


def test_dcnm_maintenance_mode_query_00400(monkeypatch) -> None:
    """
    ### Classes and Methods
    - Merged()
        - get_want()
        - commit()

    ### Summary
    -   Verify ``commit`` re-raises ``ValueError`` when ``get_want()``
        raises ``ValueError``.
    """
    params_test = copy.deepcopy(params_query)
    params_test.update({"config": {}})

    with does_not_raise():
        instance = Query(params_test)
        instance.rest_send = RestSend(params_test)
        instance.config = params_test.get("config")

    def mock_get_want():
        raise ValueError("get_want(): Mocked ValueError.")

    match = r"Query\.commit:\s+"
    match += r"Error while retrieving playbook config\.\s+"
    match += r"Error detail: get_want\(\): Mocked ValueError\."
    with pytest.raises(ValueError, match=match):
        monkeypatch.setattr(instance, "get_want", mock_get_want)
        instance.commit()

    assert len(instance.results.diff) == 0
    assert len(instance.results.metadata) == 0
    assert len(instance.results.response) == 0
    assert len(instance.results.result) == 0


def test_dcnm_maintenance_mode_query_00500() -> None:
    """
    ### Classes and Methods
    - Query()
        - __init__()

    ### Summary
    -   Verify ``__init__`` re-raises ``ValueError`` when ``Common().__init__``
        raises ``ValueError``.
    """
    params_test = copy.deepcopy(params_query)
    params_test.update({"config": {}})
    params_test.pop("check_mode", None)

    print(f"params_test: {params_test}")
    match = r"Query\.__init__:\s+"
    match += r"Error during super\(\)\.__init__\(\)\.\s+"
    match += r"Error detail: Query\.__init__: check_mode is required\."
    with pytest.raises(ValueError, match=match):
        instance = Query(params_test)  # pylint: disable=unused-variable


def test_dcnm_maintenance_mode_query_00600(monkeypatch) -> None:
    """
    ### Classes and Methods
    - Query()
        - commit()

    ### Summary
    -   Verify ``commit`` re-raises ``ValueError`` when ``get_have()``
        raises ``ValueError``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    def configs():
        yield configs_query(f"{key}a")

    gen_configs = ResponseGenerator(configs())

    def responses():
        yield

    gen_responses = ResponseGenerator(responses())

    params_test = copy.deepcopy(params_query)
    params_test.update({"config": gen_configs.next})

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params_query)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Query(params_test)
        instance.rest_send = RestSend(params_test)
        instance.config = params_test.get("config")

    class MockMaintenanceModeInfo:  # pylint: disable=too-few-public-methods
        """
        Mocked MaintenanceModeInfo class.
        """
        def __init__(self, *args):
            pass

        def refresh(self):
            """
            Mocked refresh method.
            """
            raise ValueError("MockMaintenanceModeInfo.refresh: Mocked ValueError.")

    match = r"Query\.commit:\s+"
    match += r"Error while retrieving switch information from the\s+"
    match += r"controller\.\s+"
    match += r"Error detail:\s+"
    match += r"Query\.get_have: Error while retrieving switch info\.\s+"
    match += r"Error detail: MockMaintenanceModeInfo\.refresh:\s+"
    match += r"Mocked ValueError\."
    with pytest.raises(ValueError, match=match):
        monkeypatch.setattr(
            instance, "maintenance_mode_info", MockMaintenanceModeInfo()
        )
        instance.commit()
