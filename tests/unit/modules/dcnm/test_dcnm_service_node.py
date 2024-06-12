# Copyright (c) 2021-2022 Cisco and/or its affiliates.
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

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import patch

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_service_node
from .dcnm_module import TestDcnmModule, set_module_args, loadPlaybookData

import copy

__copyright__ = "Copyright (c) 2021 Cisco and/or its affiliates."
__author__ = "Karthik Babu Harichandra Babu"


class TestDcnmServiceNodeModule(TestDcnmModule):

    module = dcnm_service_node

    test_data = loadPlaybookData("dcnm_service_node")

    SUCCESS_RETURN_CODE = 200

    mock_ip_sn = test_data.get("mock_ip_sn")
    sn_inv_data = test_data.get("sn_inv_data")
    playbook_config = test_data.get("playbook_config")
    playbook_config_replace_new = test_data.get("playbook_config_replace_new")
    playbook_config_replace_new1 = test_data.get("playbook_config_replace_new1")
    playbook_new_config = test_data.get("playbook_new_config")
    playbook_config_virtual = test_data.get("playbook_config_virtual")
    playbook_config_load = test_data.get("playbook_config_load")
    playbook_config_vnf = test_data.get("playbook_config_vnf")
    playbook_config_vpc = test_data.get("playbook_config_vpc")
    playbook_config_invalid_vpc = test_data.get("playbook_config_invalid_vpc")
    playbook_config_no_params = test_data.get("playbook_config_no_params")
    playbook_config_no_type = test_data.get("playbook_config_no_type")
    playbook_config_no_ff = test_data.get("playbook_config_no_ff")
    playbook_config_no_vpc = test_data.get("playbook_config_no_vpc")
    playbook_config_more_switch = test_data.get("playbook_config_more_switch")
    playbook_config_name = test_data.get("playbook_config_name")
    playbook_over_config = test_data.get("playbook_over_config")
    playbook_config_query = test_data.get("playbook_config_query")
    get_have_failure = test_data.get("get_have_failure")
    blank_data = test_data.get("blank_data")
    blank_data_null = test_data.get("blank_data_null")
    blank_get_data = test_data.get("blank_get_data")
    error1 = test_data.get("error1")
    sn_delete_success_resp = test_data.get("sn_delete_success_resp")
    sn_query_success_resp = test_data.get("sn_query_success_resp")

    def init_data(self):
        # Some of the mock data is re-initialized after each test as previous test might have altered portions
        # of the mock data.

        self.mock_sn_1_object = copy.deepcopy(self.test_data.get("mock_sn_1_object"))
        self.mock_sn_merge_1_success = copy.deepcopy(
            self.test_data.get("mock_sn_merge_1_success")
        )
        self.mock_sn_merge_2_success = copy.deepcopy(
            self.test_data.get("mock_sn_merge_2_success")
        )
        self.mock_sn_merge_3_success = copy.deepcopy(
            self.test_data.get("mock_sn_merge_3_success")
        )
        self.mock_sn_merge_4_success = copy.deepcopy(
            self.test_data.get("mock_sn_merge_4_success")
        )
        self.mock_sn_merge_5_success = copy.deepcopy(
            self.test_data.get("mock_sn_merge_5_success")
        )
        self.mock_sn_merge_6_success = copy.deepcopy(
            self.test_data.get("mock_sn_merge_6_success")
        )
        self.mock_sn_replace_1_success = copy.deepcopy(
            self.test_data.get("mock_sn_replace_1_success")
        )
        self.mock_sn_replace_2_success = copy.deepcopy(
            self.test_data.get("mock_sn_replace_2_success")
        )
        self.mock_sn_have_success = copy.deepcopy(
            self.test_data.get("mock_sn_have_success")
        )
        self.mock_sn_query_success = copy.deepcopy(
            self.test_data.get("mock_sn_query_success")
        )

    def setUp(self):
        super(TestDcnmServiceNodeModule, self).setUp()

        self.mock_dcnm_ip_sn = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_service_node.get_fabric_inventory_details"
        )
        self.run_dcnm_ip_sn = self.mock_dcnm_ip_sn.start()

        self.mock_dcnm_send = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_service_node.dcnm_send"
        )
        self.run_dcnm_send = self.mock_dcnm_send.start()

        self.mock_dcnm_version_supported = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_service_node.dcnm_version_supported"
        )
        self.run_dcnm_version_supported = self.mock_dcnm_version_supported.start()

    def tearDown(self):
        super(TestDcnmServiceNodeModule, self).tearDown()
        self.mock_dcnm_send.stop()
        self.mock_dcnm_ip_sn.stop()
        self.mock_dcnm_version_supported.stop()

    def load_fixtures(self, response=None, device=""):

        self.run_dcnm_version_supported.return_value = 11

        if "sn_blank_fabric" in self._testMethodName:
            self.run_dcnm_ip_sn.side_effect = [{}]
        else:
            self.run_dcnm_ip_sn.side_effect = [self.sn_inv_data]

        if "get_have_failure" in self._testMethodName:
            self.run_dcnm_send.side_effect = [self.get_have_failure]

        elif "_check_mode" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [self.blank_get_data]

        elif "_merged_one" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.mock_sn_merge_1_success,
            ]

        elif "_merged_two" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.mock_sn_merge_2_success,
            ]

        elif "_merged_three" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.mock_sn_merge_3_success,
            ]

        elif "_merged_four" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.mock_sn_merge_4_success,
            ]

        elif "_merged_five" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.mock_sn_merge_5_success,
            ]

        elif "error1" in self._testMethodName:
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.error1,
                self.blank_data,
            ]

        elif "_merged_invalid_vpc" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = []

        elif "_merged_no_params" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = []

        elif "_merged_no_type" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = []

        elif "_merged_no_ff" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = []

        elif "_merged_more_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = []

        elif "_merged_no_vpc" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = []

        elif "delete_std" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_sn_have_success,
                self.sn_delete_success_resp,
            ]

        elif "delete_all" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_sn_have_success,
                self.sn_delete_success_resp,
            ]

        elif "query_no" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.sn_query_success_resp,
            ]

        elif "query_on" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_sn_have_success,
                self.mock_sn_have_success,
            ]

        elif "query_without_config" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_sn_have_success,
                self.mock_sn_have_success,
            ]

        elif "query_withonly_name" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_sn_have_success,
                self.mock_sn_have_success,
            ]

        elif "query_invalid_param" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = []

        elif "query_null" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [self.blank_data_null]

        elif "override_with_additions" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.mock_sn_merge_1_success,
            ]

        elif "override_with_deletions" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_sn_have_success,
                self.sn_delete_success_resp,
                self.mock_sn_merge_6_success,
            ]

        elif "override_without_changes" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [self.mock_sn_have_success]

        elif "replace_with_changes" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_sn_have_success,
                self.mock_sn_replace_1_success,
            ]

        elif "replace_with_type_changes" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_sn_have_success,
                self.mock_sn_replace_2_success,
            ]

        elif "replace_without_changes" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [self.mock_sn_have_success]

        else:
            pass

    def test_dcnm_sn_blank_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result.get("msg"),
            "Fabric test_fabric missing on DCNM or does not have any switches",
        )

    def test_dcnm_sn_get_have_failure(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(result.get("msg"), "Fabric test_fabric not present on DCNM")

    def test_dcnm_sn_check_mode(self):
        set_module_args(
            dict(
                _ansible_check_mode=True,
                state="merged",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertFalse(result.get("response"))

    def test_dcnm_sn_merged_one(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(
            result["response"][0]["DATA"]["attachedFabricName"], "test_fabric"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["attachedSwitchInterfaceName"], "Ethernet1/1"
        )
        self.assertEqual(result["response"][0]["DATA"]["fabricName"], "external")
        self.assertEqual(result["response"][0]["DATA"]["formFactor"], "Physical")
        self.assertEqual(result["response"][0]["DATA"]["interfaceName"], "scv1")
        self.assertEqual(result["response"][0]["DATA"]["name"], "SN-11")
        self.assertEqual(result["response"][0]["DATA"]["type"], "Firewall")
        self.assertEqual(result["response"][0]["RETURN_CODE"], 200)

    def test_dcnm_sn_merged_two(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config_virtual,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(
            result["response"][0]["DATA"]["attachedFabricName"], "test_fabric"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["attachedSwitchInterfaceName"], "Ethernet1/1"
        )
        self.assertEqual(result["response"][0]["DATA"]["fabricName"], "external")
        self.assertEqual(result["response"][0]["DATA"]["formFactor"], "Virtual")
        self.assertEqual(result["response"][0]["DATA"]["interfaceName"], "scv1")
        self.assertEqual(result["response"][0]["DATA"]["name"], "SN-11")
        self.assertEqual(result["response"][0]["DATA"]["type"], "Firewall")
        self.assertEqual(result["response"][0]["RETURN_CODE"], 200)

    def test_dcnm_sn_merged_three(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config_load,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(
            result["response"][0]["DATA"]["attachedFabricName"], "test_fabric"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["attachedSwitchInterfaceName"], "Ethernet1/1"
        )
        self.assertEqual(result["response"][0]["DATA"]["fabricName"], "external")
        self.assertEqual(result["response"][0]["DATA"]["formFactor"], "Virtual")
        self.assertEqual(result["response"][0]["DATA"]["interfaceName"], "scv1")
        self.assertEqual(result["response"][0]["DATA"]["name"], "SN-11")
        self.assertEqual(result["response"][0]["DATA"]["type"], "AVB")
        self.assertEqual(result["response"][0]["RETURN_CODE"], 200)

    def test_dcnm_sn_merged_four(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config_vnf,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(
            result["response"][0]["DATA"]["attachedFabricName"], "test_fabric"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["attachedSwitchInterfaceName"], "Ethernet1/1"
        )
        self.assertEqual(result["response"][0]["DATA"]["fabricName"], "external")
        self.assertEqual(result["response"][0]["DATA"]["formFactor"], "Virtual")
        self.assertEqual(result["response"][0]["DATA"]["interfaceName"], "scv1")
        self.assertEqual(result["response"][0]["DATA"]["name"], "SN-11")
        self.assertEqual(result["response"][0]["DATA"]["type"], "VNF")
        self.assertEqual(result["response"][0]["RETURN_CODE"], 200)

    def test_dcnm_sn_merged_five(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config_vpc,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(
            result["response"][0]["DATA"]["attachedFabricName"], "test_fabric"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["attachedSwitchInterfaceName"], "vPC1"
        )
        self.assertEqual(result["response"][0]["DATA"]["fabricName"], "external")
        self.assertEqual(result["response"][0]["DATA"]["formFactor"], "Physical")
        self.assertEqual(result["response"][0]["DATA"]["interfaceName"], "scv1")
        self.assertEqual(result["response"][0]["DATA"]["name"], "SN-11")
        self.assertEqual(result["response"][0]["DATA"]["type"], "Firewall")
        self.assertEqual(result["response"][0]["RETURN_CODE"], 200)

    def test_dcnm_sn_error1(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(result["msg"]["RETURN_CODE"], 400)
        self.assertEqual(result["msg"]["ERROR"], "There is an error")

    def test_dcnm_sn_merged_invalid_vpc(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config_invalid_vpc,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result.get("msg"),
            "Fabric: test_fabric - if two switches are provided, vpc is only interface option",
        )

    def test_dcnm_sn_merged_more_switch(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config_more_switch,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result.get("msg"), "Fabric: test_fabric - Upto 2 switches only allowed"
        )

    def test_dcnm_sn_merged_no_params(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config_no_params,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result.get("msg"), "config: element is mandatory for this state merged"
        )

    def test_dcnm_sn_merged_no_type(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config_no_type,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result.get("msg"),
            "Invalid parameters in playbook: karth : Invalid choice [ karth ] provided for param [ type ]",
        )

    def test_dcnm_sn_merged_no_ff(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config_no_ff,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result.get("msg"),
            "Invalid parameters in playbook: babu : Invalid choice [ babu ] provided for param [ form_factor ]",
        )

    def test_dcnm_sn_merged_no_vpc(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config_no_vpc,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result.get("msg"),
            "Fabric: test_fabric - For 1 switch, vpc is not the interface option",
        )

    def test_dcnm_sn_delete_std(self):
        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(result["response"][0]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)
        self.assertEqual(result["response"][0]["METHOD"], "DELETE")

    def test_dcnm_sn_delete_all(self):
        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                service_fabric="external",
                config=[],
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(result["response"][0]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)
        self.assertEqual(result["response"][0]["METHOD"], "DELETE")

    def test_dcnm_sn_query_no(self):
        set_module_args(
            dict(
                state="query",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertEqual(result.get("response"), [])

    def test_dcnm_sn_query_on(self):
        set_module_args(
            dict(
                state="query",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertEqual(result["response"][0]["attachedFabricName"], "test_fabric")
        self.assertEqual(
            result["response"][0]["attachedSwitchInterfaceName"], "Ethernet1/1"
        )
        self.assertEqual(result["response"][0]["fabricName"], "external")
        self.assertEqual(result["response"][0]["formFactor"], "Physical")
        self.assertEqual(result["response"][0]["interfaceName"], "scv1")
        self.assertEqual(result["response"][0]["name"], "SN-11")
        self.assertEqual(result["response"][0]["type"], "Firewall")

    def test_dcnm_sn_query_without_config(self):
        set_module_args(
            dict(
                state="query",
                fabric="test_fabric",
                service_fabric="external",
                config=[],
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertEqual(result["response"][0]["attachedFabricName"], "test_fabric")
        self.assertEqual(
            result["response"][0]["attachedSwitchInterfaceName"], "Ethernet1/1"
        )
        self.assertEqual(result["response"][0]["fabricName"], "external")
        self.assertEqual(result["response"][0]["formFactor"], "Physical")
        self.assertEqual(result["response"][0]["interfaceName"], "scv1")
        self.assertEqual(result["response"][0]["name"], "SN-11")
        self.assertEqual(result["response"][0]["type"], "Firewall")

    def test_dcnm_sn_query_withonly_name(self):
        set_module_args(
            dict(
                state="query",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config_name,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertEqual(result["response"][0]["attachedFabricName"], "test_fabric")
        self.assertEqual(
            result["response"][0]["attachedSwitchInterfaceName"], "Ethernet1/1"
        )
        self.assertEqual(result["response"][0]["fabricName"], "external")
        self.assertEqual(result["response"][0]["formFactor"], "Physical")
        self.assertEqual(result["response"][0]["interfaceName"], "scv1")
        self.assertEqual(result["response"][0]["name"], "SN-11")
        self.assertEqual(result["response"][0]["type"], "Firewall")

    def test_dcnm_sn_query_invalid_param(self):
        set_module_args(
            dict(
                state="query",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config_query,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result.get("msg"),
            "Invalid parameters in playbook: name : Required parameter not found",
        )

    def test_dcnm_sn_query_null(self):
        set_module_args(
            dict(
                state="query",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result.get("msg"), "Unable to Service Node under fabric: test_fabric"
        )

    def test_dcnm_sn_override_with_additions(self):
        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(
            result["response"][0]["DATA"]["attachedFabricName"], "test_fabric"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["attachedSwitchInterfaceName"], "Ethernet1/1"
        )
        self.assertEqual(result["response"][0]["DATA"]["fabricName"], "external")
        self.assertEqual(result["response"][0]["DATA"]["formFactor"], "Physical")
        self.assertEqual(result["response"][0]["DATA"]["interfaceName"], "scv1")
        self.assertEqual(result["response"][0]["DATA"]["name"], "SN-11")
        self.assertEqual(result["response"][0]["DATA"]["type"], "Firewall")
        self.assertEqual(result["response"][0]["RETURN_CODE"], 200)

    def test_dcnm_sn_override_with_deletions(self):
        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_new_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(result["response"][0]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)
        self.assertEqual(result["response"][0]["METHOD"], "DELETE")
        self.assertEqual(
            result["response"][1]["DATA"]["attachedFabricName"], "test_fabric"
        )
        self.assertEqual(
            result["response"][1]["DATA"]["attachedSwitchInterfaceName"], "Ethernet1/2"
        )
        self.assertEqual(result["response"][1]["DATA"]["fabricName"], "external")
        self.assertEqual(result["response"][1]["DATA"]["formFactor"], "Virtual")
        self.assertEqual(result["response"][1]["DATA"]["interfaceName"], "scv12")
        self.assertEqual(result["response"][1]["DATA"]["name"], "SN-12")
        self.assertEqual(result["response"][1]["DATA"]["type"], "ADC")
        self.assertEqual(result["response"][1]["RETURN_CODE"], 200)

    def test_dcnm_sn_override_without_changes(self):
        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_over_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertFalse(result.get("response"))

    def test_dcnm_sn_replace_with_changes(self):
        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config_replace_new,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(result["response"][0]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)
        self.assertEqual(result["response"][0]["METHOD"], "PUT")
        self.assertEqual(
            result["response"][0]["DATA"]["attachedFabricName"], "test_fabric"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["attachedSwitchInterfaceName"], "Ethernet1/1"
        )
        self.assertEqual(result["response"][0]["DATA"]["fabricName"], "external")
        self.assertEqual(result["response"][0]["DATA"]["formFactor"], "Virtual")
        self.assertEqual(result["response"][0]["DATA"]["interfaceName"], "scv11")
        self.assertEqual(result["response"][0]["DATA"]["name"], "SN-11")
        self.assertEqual(result["response"][0]["DATA"]["type"], "Firewall")
        self.assertEqual(result["response"][0]["RETURN_CODE"], 200)

    def test_dcnm_sn_replace_with_type_changes(self):
        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_config_replace_new1,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(result["response"][0]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)
        self.assertEqual(result["response"][0]["METHOD"], "PUT")
        self.assertEqual(
            result["response"][0]["DATA"]["attachedFabricName"], "test_fabric"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["attachedSwitchInterfaceName"], "Ethernet1/1"
        )
        self.assertEqual(result["response"][0]["DATA"]["fabricName"], "external")
        self.assertEqual(result["response"][0]["DATA"]["formFactor"], "Virtual")
        self.assertEqual(result["response"][0]["DATA"]["interfaceName"], "scv11")
        self.assertEqual(result["response"][0]["DATA"]["name"], "SN-11")
        self.assertEqual(result["response"][0]["DATA"]["type"], "ADC")
        self.assertEqual(result["response"][0]["RETURN_CODE"], 200)

    def test_dcnm_sn_replace_without_changes(self):
        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                service_fabric="external",
                config=self.playbook_over_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertFalse(result.get("response"))
