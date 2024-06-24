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
    Merged
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_maintenance_mode.utils import (
    MockAnsibleModule, configs_merged, does_not_raise, params,
    responses_ep_all_switches, responses_ep_fabrics,
    responses_ep_maintenance_mode_deploy,
    responses_ep_maintenance_mode_disable,
    responses_ep_maintenance_mode_enable)


def test_dcnm_maintenance_mode_merged_00000() -> None:
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
        instance = Merged(params)
        switches = instance.config.get("switches", None)

    assert instance.class_name == "Merged"
    assert instance.log.name == "dcnm.Merged"

    assert instance.check_mode is False
    assert instance.state == "merged"

    assert isinstance(instance.config, dict)
    assert isinstance(switches, list)
    assert switches[0].get("ip_address", None) == "192.168.1.2"

    assert instance.have == {}
    assert instance.need == []
    assert instance.payloads == {}
    assert instance.query == []
    assert instance.want == []

    assert instance.maintenance_mode.class_name == "MaintenanceMode"
    assert instance.maintenance_mode.state == "merged"
    assert instance.maintenance_mode.check_mode is False

    assert instance.results.class_name == "Results"
    assert instance.results.state == "merged"
    assert instance.results.check_mode is False


def test_dcnm_maintenance_mode_merged_00100() -> None:
    """
    ### Classes and Methods
    - Merged()
        - commit()

    ### Summary
    -   Verify ``commit()`` happy path.
    -   Change switch mode from maintenance to normal.
    -   No exceptions are raised.
    -   want contains expected structure and values.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    def configs():
        yield configs_merged(f"{key}a")

    gen_configs = ResponseGenerator(configs())

    def responses():
        yield responses_ep_all_switches(f"{key}a")
        yield responses_ep_fabrics(f"{key}a")
        yield responses_ep_maintenance_mode_enable(f"{key}a")
        yield responses_ep_maintenance_mode_enable(f"{key}b")
        yield responses_ep_maintenance_mode_deploy(f"{key}a")
        yield responses_ep_maintenance_mode_deploy(f"{key}b")

    gen_responses = ResponseGenerator(responses())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen_configs.next})

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Merged(params)
        instance.rest_send = rest_send
        instance.config = params_test.get("config")
        instance.commit()
    assert instance.want[0].get("deploy", None) is True
    assert instance.want[0].get("ip_address", None) == "192.168.1.2"
    assert instance.want[0].get("mode", None) == "normal"
    assert instance.want[0].get("wait_for_mode_change", None) is True
    assert instance.want[1].get("deploy", None) is True
    assert instance.want[1].get("ip_address", None) == "192.168.1.3"
    assert instance.want[1].get("mode", None) == "normal"
    assert instance.want[1].get("wait_for_mode_change", None) is True

    assert instance.results.diff[2]["maintenance_mode"] == "normal"
    assert instance.results.diff[3]["maintenance_mode"] == "normal"
    assert instance.results.diff[4]["deploy_maintenance_mode"] is True
    assert instance.results.diff[5]["deploy_maintenance_mode"] is True

    assert instance.results.metadata[0]["action"] == "switch_details"
    assert instance.results.metadata[1]["action"] == "fabric_details"
    assert instance.results.metadata[2]["action"] == "change_sytem_mode"
    assert instance.results.metadata[3]["action"] == "change_sytem_mode"
    assert instance.results.metadata[4]["action"] == "deploy_maintenance_mode"
    assert instance.results.metadata[5]["action"] == "deploy_maintenance_mode"

    assert instance.results.metadata[0]["state"] == "merged"
    assert instance.results.metadata[1]["state"] == "merged"
    assert instance.results.metadata[2]["state"] == "merged"
    assert instance.results.metadata[3]["state"] == "merged"
    assert instance.results.metadata[4]["state"] == "merged"
    assert instance.results.metadata[5]["state"] == "merged"

    assert instance.results.metadata[0]["check_mode"] is False
    assert instance.results.metadata[1]["check_mode"] is False
    assert instance.results.metadata[2]["check_mode"] is False
    assert instance.results.metadata[3]["check_mode"] is False
    assert instance.results.metadata[4]["check_mode"] is False
    assert instance.results.metadata[5]["check_mode"] is False

    assert instance.results.result[0]["found"] is True
    assert instance.results.result[1]["found"] is True

    assert instance.results.result[2]["changed"] is True
    assert instance.results.result[3]["changed"] is True
    assert instance.results.result[4]["changed"] is True
    assert instance.results.result[5]["changed"] is True

    assert instance.results.result[0]["success"] is True
    assert instance.results.result[1]["success"] is True
    assert instance.results.result[2]["success"] is True
    assert instance.results.result[3]["success"] is True
    assert instance.results.result[4]["success"] is True
    assert instance.results.result[5]["success"] is True


def test_dcnm_maintenance_mode_merged_00110() -> None:
    """
    ### Classes and Methods
    - Merged()
        - commit()

    ### Summary
    -   Verify ``commit()`` happy path.
    -   Change switch mode from normal to maintenance.
    -   No exceptions are raised.
    -   want contains expected structure and values.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    def configs():
        yield configs_merged(f"{key}a")

    gen_configs = ResponseGenerator(configs())

    def responses():
        yield responses_ep_all_switches(f"{key}a")
        yield responses_ep_fabrics(f"{key}a")
        yield responses_ep_maintenance_mode_disable(f"{key}a")
        yield responses_ep_maintenance_mode_disable(f"{key}b")
        yield responses_ep_maintenance_mode_deploy(f"{key}a")
        yield responses_ep_maintenance_mode_deploy(f"{key}b")

    gen_responses = ResponseGenerator(responses())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen_configs.next})

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Merged(params)
        instance.rest_send = rest_send
        instance.config = params_test.get("config")
        instance.commit()
    assert instance.want[0].get("deploy", None) is True
    assert instance.want[0].get("ip_address", None) == "192.168.1.2"
    assert instance.want[0].get("mode", None) == "maintenance"
    assert instance.want[0].get("wait_for_mode_change", None) is True
    assert instance.want[1].get("deploy", None) is True
    assert instance.want[1].get("ip_address", None) == "192.168.1.3"
    assert instance.want[1].get("mode", None) == "maintenance"
    assert instance.want[1].get("wait_for_mode_change", None) is True

    assert instance.results.diff[2]["maintenance_mode"] == "maintenance"
    assert instance.results.diff[3]["maintenance_mode"] == "maintenance"
    assert instance.results.diff[4]["deploy_maintenance_mode"] is True
    assert instance.results.diff[5]["deploy_maintenance_mode"] is True

    assert instance.results.metadata[0]["action"] == "switch_details"
    assert instance.results.metadata[1]["action"] == "fabric_details"
    assert instance.results.metadata[2]["action"] == "change_sytem_mode"
    assert instance.results.metadata[3]["action"] == "change_sytem_mode"
    assert instance.results.metadata[4]["action"] == "deploy_maintenance_mode"
    assert instance.results.metadata[5]["action"] == "deploy_maintenance_mode"

    assert instance.results.metadata[0]["state"] == "merged"
    assert instance.results.metadata[1]["state"] == "merged"
    assert instance.results.metadata[2]["state"] == "merged"
    assert instance.results.metadata[3]["state"] == "merged"
    assert instance.results.metadata[4]["state"] == "merged"
    assert instance.results.metadata[5]["state"] == "merged"

    assert instance.results.metadata[0]["check_mode"] is False
    assert instance.results.metadata[1]["check_mode"] is False
    assert instance.results.metadata[2]["check_mode"] is False
    assert instance.results.metadata[3]["check_mode"] is False
    assert instance.results.metadata[4]["check_mode"] is False
    assert instance.results.metadata[5]["check_mode"] is False

    assert instance.results.result[0]["found"] is True
    assert instance.results.result[1]["found"] is True

    assert instance.results.result[2]["changed"] is True
    assert instance.results.result[3]["changed"] is True
    assert instance.results.result[4]["changed"] is True
    assert instance.results.result[5]["changed"] is True

    assert instance.results.result[0]["success"] is True
    assert instance.results.result[1]["success"] is True
    assert instance.results.result[2]["success"] is True
    assert instance.results.result[3]["success"] is True
    assert instance.results.result[4]["success"] is True
    assert instance.results.result[5]["success"] is True


def test_dcnm_maintenance_mode_merged_00115() -> None:
    """
    ### Classes and Methods
    - Merged()
        - commit()

    ### Summary
    -   Verify ``commit()`` happy path.
    -   User wants to change switches to maintenance mode, but all
        switches are already in maintenance mode.
    -   send_need() returns without sending any requests since
        instance.need is empty.
    -   No exceptions are raised.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    def configs():
        yield configs_merged(f"{key}a")

    gen_configs = ResponseGenerator(configs())

    def responses():
        yield responses_ep_all_switches(f"{key}a")
        yield responses_ep_fabrics(f"{key}a")

    gen_responses = ResponseGenerator(responses())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen_configs.next})

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Merged(params)
        instance.rest_send = rest_send
        instance.config = params_test.get("config")
        instance.commit()

    assert len(instance.need) == 0

    assert instance.results.metadata[0]["action"] == "switch_details"
    assert instance.results.metadata[1]["action"] == "fabric_details"

    assert instance.results.metadata[0]["state"] == "merged"
    assert instance.results.metadata[1]["state"] == "merged"

    assert instance.results.metadata[0]["check_mode"] is False
    assert instance.results.metadata[1]["check_mode"] is False

    assert instance.results.result[0]["found"] is True
    assert instance.results.result[1]["found"] is True

    assert instance.results.result[0]["success"] is True
    assert instance.results.result[1]["success"] is True


def test_dcnm_maintenance_mode_merged_00120() -> None:
    """
    ### Classes and Methods
    - Merged()
        - get_need()
        - commit()

    ### Summary
    -   Verify ``get_have()`` raises ``ValueError`` when ip_address
        does not exist on the controller.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    def configs():
        yield configs_merged(f"{key}a")

    gen_configs = ResponseGenerator(configs())

    def responses():
        yield responses_ep_all_switches(f"{key}a")
        yield responses_ep_fabrics(f"{key}a")
        yield responses_ep_maintenance_mode_disable(f"{key}a")
        yield responses_ep_maintenance_mode_disable(f"{key}b")
        yield responses_ep_maintenance_mode_deploy(f"{key}a")
        yield responses_ep_maintenance_mode_deploy(f"{key}b")

    gen_responses = ResponseGenerator(responses())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen_configs.next})

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Merged(params)
        instance.rest_send = rest_send
        instance.config = params_test.get("config")
    match = r"Merged\.get_have:\s+"
    match += r"Error while retrieving switch info\.\s+"
    match += r"Error detail: SwitchDetails\._get:\s+"
    match += r"Switch with ip_address 192\.168\.1\.4 does not exist on the controller\."
    with pytest.raises(ValueError, match=match):
        instance.commit()

    assert len(instance.results.diff) == 2

    assert instance.results.metadata[0]["action"] == "switch_details"
    assert instance.results.metadata[1]["action"] == "fabric_details"

    assert instance.results.metadata[0]["state"] == "merged"
    assert instance.results.metadata[1]["state"] == "merged"

    assert instance.results.metadata[0]["check_mode"] is False
    assert instance.results.metadata[1]["check_mode"] is False

    assert instance.results.result[0]["found"] is True
    assert instance.results.result[1]["found"] is True

    assert instance.results.result[0]["success"] is True
    assert instance.results.result[1]["success"] is True


def test_dcnm_maintenance_mode_merged_00130() -> None:
    """
    ### Classes and Methods
    - Merged()
        - fabric_deployment_disabled()
        - commit()

    ### Summary
    -   Verify ``fabric_deployment_disabled()`` raises ``ValueError`` when
        have ip_address is in migration mode.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    def configs():
        yield configs_merged(f"{key}a")

    gen_configs = ResponseGenerator(configs())

    def responses():
        yield responses_ep_all_switches(f"{key}a")
        yield responses_ep_fabrics(f"{key}a")
        yield responses_ep_maintenance_mode_disable(f"{key}a")
        yield responses_ep_maintenance_mode_disable(f"{key}b")
        yield responses_ep_maintenance_mode_deploy(f"{key}a")
        yield responses_ep_maintenance_mode_deploy(f"{key}b")

    gen_responses = ResponseGenerator(responses())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen_configs.next})

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Merged(params)
        instance.rest_send = rest_send
        instance.config = params_test.get("config")
    match = r"Merged\.fabric_deployment_disabled:\s+"
    match += r"Switch maintenance mode is in migration state\s+"
    match += r"for the switch with ip_address 192\.168\.1\.2,\s+"
    match += r"serial_number FD2222222GA\.\s+"
    match += r"This indicates that the switch configuration is not compatible\s+"
    match += r"with the switch role in the hosting fabric\.\s+"
    match += r"The issue might be resolved by initiating a fabric\s+"
    match += r"Recalculate \& Deploy on the controller\.\s+"
    match += r"Failing that, the switch configuration might need to be\s+"
    match += r"manually modified to match the switch role in the hosting\s+"
    match += r"fabric\.\s+"
    match += r"Additional info:\s+"
    match += r"hosting_fabric: VXLAN_EVPN_Fabric,\s+"
    match += r"fabric_deployment_disabled: False,\s+"
    match += r"fabric_freeze_mode: False,\s+"
    match += r"fabric_read_only: False,\s+"
    match += r"maintenance_mode: migration\."
    with pytest.raises(ValueError, match=match):
        instance.commit()

    assert len(instance.results.diff) == 2

    assert instance.results.metadata[0]["action"] == "switch_details"
    assert instance.results.metadata[1]["action"] == "fabric_details"

    assert instance.results.metadata[0]["state"] == "merged"
    assert instance.results.metadata[1]["state"] == "merged"

    assert instance.results.metadata[0]["check_mode"] is False
    assert instance.results.metadata[1]["check_mode"] is False

    assert instance.results.result[0]["found"] is True
    assert instance.results.result[1]["found"] is True

    assert instance.results.result[0]["success"] is True
    assert instance.results.result[1]["success"] is True


def test_dcnm_maintenance_mode_merged_00140() -> None:
    """
    ### Classes and Methods
    - Merged()
        - fabric_deployment_disabled()
        - commit()

    ### Summary
    -   Verify ``fabric_deployment_disabled()`` raises ``ValueError`` when
        the fabric is in read-only mode.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    def configs():
        yield configs_merged(f"{key}a")

    gen_configs = ResponseGenerator(configs())

    def responses():
        yield responses_ep_all_switches(f"{key}a")
        yield responses_ep_fabrics(f"{key}a")

    gen_responses = ResponseGenerator(responses())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen_configs.next})

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Merged(params)
        instance.rest_send = rest_send
        instance.config = params_test.get("config")
    match = r"Merged\.fabric_deployment_disabled:\s+"
    match += r"The hosting fabric is in read-only mode for the switch with\s+"
    match += r"ip_address 192\.168\.1\.2,\s+"
    match += r"serial_number FD2222222GA\.\s+"
    match += r"The issue can be resolved for LAN_Classic fabrics by\s+"
    match += r"unchecking 'Fabric Monitor Mode' in the fabric settings\s+"
    match += r"on the controller\.\s+"
    match += r"Additional info:\s+"
    match += r"hosting_fabric: LAN_Classic_Fabric,\s+"
    match += r"fabric_deployment_disabled: True,\s+"
    match += r"fabric_freeze_mode: False,\s+"
    match += r"fabric_read_only: True,\s+"
    match += r"maintenance_mode: normal\.\s+"
    with pytest.raises(ValueError, match=match):
        instance.commit()

    assert len(instance.results.diff) == 2

    assert instance.results.metadata[0]["action"] == "switch_details"
    assert instance.results.metadata[1]["action"] == "fabric_details"

    assert instance.results.metadata[0]["state"] == "merged"
    assert instance.results.metadata[1]["state"] == "merged"

    assert instance.results.metadata[0]["check_mode"] is False
    assert instance.results.metadata[1]["check_mode"] is False

    assert instance.results.result[0]["found"] is True
    assert instance.results.result[1]["found"] is True

    assert instance.results.result[0]["success"] is True
    assert instance.results.result[1]["success"] is True


def test_dcnm_maintenance_mode_merged_00150() -> None:
    """
    ### Classes and Methods
    - Merged()
        - fabric_deployment_disabled()
        - commit()

    ### Summary
    -   Verify ``fabric_deployment_disabled()`` raises ``ValueError`` when
        fabric freeze-mode is True.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    def configs():
        yield configs_merged(f"{key}a")

    gen_configs = ResponseGenerator(configs())

    def responses():
        yield responses_ep_all_switches(f"{key}a")
        yield responses_ep_fabrics(f"{key}a")

    gen_responses = ResponseGenerator(responses())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen_configs.next})

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Merged(params)
        instance.rest_send = rest_send
        instance.config = params_test.get("config")
    match = r"Merged\.fabric_deployment_disabled:\s+"
    match += (
        r"The hosting fabric is in 'Deployment Disable' state for the switch with\s+"
    )
    match += r"ip_address 192\.168\.1\.2,\s+"
    match += r"serial_number FD2222222GA\.\s+"
    match += r"Review the 'Deployment Enable / Deployment Disable' setting on the controller at:\s+"
    match += r"Fabric Controller > Overview > Topology > <fabric>\s+"
    match += r"> Actions > More, and change the setting to 'Deployment Enable'\.\s+"
    match += r"Additional info:\s+"
    match += r"hosting_fabric: VXLAN_EVPN_Fabric,\s+"
    match += r"fabric_deployment_disabled: True,\s+"
    match += r"fabric_freeze_mode: True,\s+"
    match += r"fabric_read_only: False,\s+"
    match += r"maintenance_mode: normal\.\s+"
    with pytest.raises(ValueError, match=match):
        instance.commit()

    assert len(instance.results.diff) == 2

    assert instance.results.metadata[0]["action"] == "switch_details"
    assert instance.results.metadata[1]["action"] == "fabric_details"

    assert instance.results.metadata[0]["state"] == "merged"
    assert instance.results.metadata[1]["state"] == "merged"

    assert instance.results.metadata[0]["check_mode"] is False
    assert instance.results.metadata[1]["check_mode"] is False

    assert instance.results.result[0]["found"] is True
    assert instance.results.result[1]["found"] is True

    assert instance.results.result[0]["success"] is True
    assert instance.results.result[1]["success"] is True


def test_dcnm_maintenance_mode_merged_00200() -> None:
    """
    ### Classes and Methods
    - Merged()
        - commit()

    ### Summary
    -   Verify ``commit()`` raises ``ValueError`` when rest_send has not
        been set.
    """
    with does_not_raise():
        instance = Merged(params)
    match = r"Merged\.commit:\s+"
    match += r"rest_send must be set before calling commit\."
    with pytest.raises(ValueError, match=match):
        instance.commit()

    assert len(instance.results.diff) == 0
    assert len(instance.results.metadata) == 0
    assert len(instance.results.response) == 0
    assert len(instance.results.result) == 0


def test_dcnm_maintenance_mode_merged_00300(monkeypatch) -> None:
    """
    ### Classes and Methods
    - Merged()
        - get_need()
        - commit()

    ### Summary
    -   Verify ``get_need()`` raises ``ValueError`` when ip_address
        does not exist in self.have.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    def configs():
        yield configs_merged(f"{key}a")

    gen_configs = ResponseGenerator(configs())

    def responses():
        yield

    gen_responses = ResponseGenerator(responses())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen_configs.next})

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Merged(params_test)
        instance.rest_send = rest_send
        instance.config = params_test.get("config")

    def mock_get_have():
        return {}

    match = r"Merged\.get_need: Switch 192\.168\.1\.2 not found\s+"
    match += r"on the controller\."
    with pytest.raises(ValueError, match=match):
        monkeypatch.setattr(instance, "get_have", mock_get_have)
        instance.commit()

    assert len(instance.results.diff) == 0
    assert len(instance.results.metadata) == 0
    assert len(instance.results.response) == 0
    assert len(instance.results.result) == 0


def test_dcnm_maintenance_mode_merged_00400(monkeypatch) -> None:
    """
    ### Classes and Methods
    - Merged()
        - get_want()
        - commit()

    ### Summary
    -   Verify ``commit`` re-raises ``ValueError`` when ``get_want()``
        raises ``ValueError``.
    """
    params_test = copy.deepcopy(params)
    params_test.update({"config": {}})

    with does_not_raise():
        instance = Merged(params)
        instance.rest_send = RestSend(params)
        instance.config = params_test.get("config")

    def mock_get_want():
        raise ValueError("get_want(): Mocked ValueError.")

    match = r"Merged\.commit:\s+"
    match += r"Error while retrieving playbook config\.\s+"
    match += r"Error detail: get_want\(\): Mocked ValueError\."
    with pytest.raises(ValueError, match=match):
        monkeypatch.setattr(instance, "get_want", mock_get_want)
        instance.commit()

    assert len(instance.results.diff) == 0
    assert len(instance.results.metadata) == 0
    assert len(instance.results.response) == 0
    assert len(instance.results.result) == 0


def test_dcnm_maintenance_mode_merged_00500() -> None:
    """
    ### Classes and Methods
    - Merged()
        - __init__()

    ### Summary
    -   Verify ``__init__`` re-raises ``ValueError`` when ``Common().__init__``
        raises ``ValueError``.
    """
    params_test = copy.deepcopy(params)
    params_test.update({"config": {}})
    params_test.pop("check_mode", None)

    print(f"params_test: {params_test}")
    match = r"Merged\.__init__:\s+"
    match += r"Error during super\(\)\.__init__\(\)\.\s+"
    match += r"Error detail: Merged\.__init__: check_mode is required\."
    with pytest.raises(ValueError, match=match):
        instance = Merged(params_test)  # pylint: disable=unused-variable


def test_dcnm_maintenance_mode_merged_00600(monkeypatch) -> None:
    """
    ### Classes and Methods
    - Merged()
        - send_need()
        - commit()

    ### Summary
    -   Verify ``commit()`` re-raises ``ValueError`` when
        send_need() raises ``ValueError``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    def configs():
        yield configs_merged(f"{key}a")

    gen_configs = ResponseGenerator(configs())

    def responses():
        yield responses_ep_all_switches(f"{key}a")
        yield responses_ep_fabrics(f"{key}a")

    gen_responses = ResponseGenerator(responses())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen_configs.next})

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Merged(params)
        instance.rest_send = rest_send
        instance.config = params_test.get("config")

    def mock_send_need():
        raise ValueError("send_need(): Mocked ValueError.")

    match = r"Merged\.commit:\s+"
    match += r"Error while sending maintenance mode request\.\s+"
    match += r"Error detail: send_need\(\): Mocked ValueError\."
    with pytest.raises(ValueError, match=match):
        monkeypatch.setattr(instance, "send_need", mock_send_need)
        instance.commit()

    assert len(instance.results.diff) == 2

    assert instance.results.metadata[0]["action"] == "switch_details"
    assert instance.results.metadata[1]["action"] == "fabric_details"

    assert instance.results.metadata[0]["state"] == "merged"
    assert instance.results.metadata[1]["state"] == "merged"

    assert instance.results.metadata[0]["check_mode"] is False
    assert instance.results.metadata[1]["check_mode"] is False

    assert instance.results.result[0]["found"] is True
    assert instance.results.result[1]["found"] is True

    assert instance.results.result[0]["success"] is True
    assert instance.results.result[1]["success"] is True


def test_dcnm_maintenance_mode_merged_00700(monkeypatch) -> None:
    """
    ### Classes and Methods
    - Merged()
        - send_need()
        - commit()

    ### Summary
    -   Verify ``send_need()`` re-raises ``ValueError`` when
        MaintenanceMode.commit() raises ``ValueError``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}"

    def configs():
        yield configs_merged(f"{key}a")

    gen_configs = ResponseGenerator(configs())

    def responses():
        yield responses_ep_all_switches(f"{key}a")
        yield responses_ep_fabrics(f"{key}a")

    gen_responses = ResponseGenerator(responses())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen_configs.next})

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = Merged(params)
        instance.rest_send = rest_send
        instance.config = params_test.get("config")

    class MockMaintenanceMode:  # pylint: disable=too-few-public-methods
        """
        Mocked MaintenanceMode class.
        """

        def __init__(self, *args):
            pass

        def commit(self):
            """
            Mocked commit method.
            """
            raise ValueError("MockMaintenanceModeInfo.refresh: Mocked ValueError.")

    match = r"Merged\.commit:\s+"
    match += r"Error while sending maintenance mode request\.\s+"
    match += r"Error detail:\s+"
    match += r"MockMaintenanceModeInfo\.refresh: Mocked ValueError\."
    with pytest.raises(ValueError, match=match):
        monkeypatch.setattr(
            instance, "maintenance_mode", MockMaintenanceMode(params_test)
        )
        instance.commit()

    assert len(instance.results.diff) == 2

    assert instance.results.metadata[0]["action"] == "switch_details"
    assert instance.results.metadata[1]["action"] == "fabric_details"

    assert instance.results.metadata[0]["state"] == "merged"
    assert instance.results.metadata[1]["state"] == "merged"

    assert instance.results.metadata[0]["check_mode"] is False
    assert instance.results.metadata[1]["check_mode"] is False

    assert instance.results.result[0]["found"] is True
    assert instance.results.result[1]["found"] is True

    assert instance.results.result[0]["success"] is True
    assert instance.results.result[1]["success"] is True
