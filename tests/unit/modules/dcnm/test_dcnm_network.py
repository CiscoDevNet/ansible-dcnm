# Copyright (c) 2023 Cisco and/or its affiliates.
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

# from units.compat.mock import patch

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_network
from .dcnm_module import TestDcnmModule, set_module_args, loadPlaybookData

import copy


class TestDcnmNetworkModule(TestDcnmModule):

    module = dcnm_network

    test_data = loadPlaybookData("dcnm_network")

    SUCCESS_RETURN_CODE = 200

    version = 11

    mock_ip_sn = test_data.get("mock_ip_sn")
    net_inv_data = test_data.get("net_inv_data")
    fabric_details = test_data.get("fabric_details")

    playbook_config = test_data.get("playbook_config")
    playbook_config_incorrect_netid = test_data.get("playbook_config_incorrect_netid")
    playbook_config_incorrect_vrf = test_data.get("playbook_config_incorrect_vrf")
    playbook_config_update = test_data.get("playbook_config_update")
    playbook_config_novlan = test_data.get("playbook_config_novlan")
    playbook_tor_config = test_data.get("playbook_tor_config")
    playbook_tor_roleerr_config = test_data.get("playbook_tor_roleerr_config")
    playbook_tor_config_update = test_data.get("playbook_tor_config_update")

    playbook_config_replace = test_data.get("playbook_config_replace")
    playbook_config_replace_no_atch = test_data.get("playbook_config_replace_no_atch")
    playbook_config_override = test_data.get("playbook_config_override")
    mock_net_attach_object_del_not_ready = test_data.get(
        "mock_net_attach_object_del_not_ready"
    )
    mock_net_attach_object_del_ready = test_data.get("mock_net_attach_object_del_ready")

    attach_success_resp = test_data.get("attach_success_resp")
    attach_success_resp2 = test_data.get("attach_success_resp2")
    deploy_success_resp = test_data.get("deploy_success_resp")
    error1 = test_data.get("error1")
    error2 = test_data.get("error2")
    error3 = test_data.get("error3")
    get_have_failure = test_data.get("get_have_failure")

    delete_success_resp = test_data.get("delete_success_resp")
    blank_data = test_data.get("blank_data")

    def init_data(self):
        # Some of the mock data is re-initialized after each test as previous test might have altered portions
        # of the mock data.

        self.mock_net_object = copy.deepcopy(self.test_data.get("mock_net_object"))
        self.mock_vrf_object = copy.deepcopy(self.test_data.get("mock_vrf_object"))
        self.mock_net_attach_object = copy.deepcopy(self.test_data.get("mock_net_attach_object"))
        self.mock_net_attach_object_pending = copy.deepcopy(
            self.test_data.get("mock_net_attach_object_pending")
        )
        self.mock_net_query_object = copy.deepcopy(self.test_data.get("mock_net_query_object"))
        self.mock_vlan_get = copy.deepcopy(self.test_data.get("mock_vlan_get"))
        self.mock_net_attach_tor_object = copy.deepcopy(self.test_data.get("mock_net_attach_tor_object"))

    def setUp(self):
        super(TestDcnmNetworkModule, self).setUp()

        self.mock_dcnm_ip_sn = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_network.get_fabric_inventory_details"
        )
        self.run_dcnm_ip_sn = self.mock_dcnm_ip_sn.start()

        self.mock_dcnm_send = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_network.dcnm_send"
        )
        self.run_dcnm_send = self.mock_dcnm_send.start()

        self.mock_dcnm_fabric_details = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_network.get_fabric_details"
        )
        self.run_dcnm_fabric_details = self.mock_dcnm_fabric_details.start()

        self.mock_dcnm_version_supported = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_network.dcnm_version_supported"
        )
        self.run_dcnm_version_supported = self.mock_dcnm_version_supported.start()

        self.mock_dcnm_get_url = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_network.dcnm_get_url"
        )
        self.run_dcnm_get_url = self.mock_dcnm_get_url.start()

    def tearDown(self):
        super(TestDcnmNetworkModule, self).tearDown()
        self.mock_dcnm_send.stop()
        self.mock_dcnm_ip_sn.stop()
        self.mock_dcnm_fabric_details.stop()
        self.mock_dcnm_version_supported.stop()
        self.mock_dcnm_get_url.stop()

    def load_fixtures(self, response=None, device=""):

        if self.version == 12:
            self.run_dcnm_version_supported.return_value = 12
        else:
            self.run_dcnm_version_supported.return_value = 11

        if "net_blank_fabric" in self._testMethodName:
            self.run_dcnm_ip_sn.side_effect = [{}]
        else:
            self.run_dcnm_ip_sn.side_effect = [self.net_inv_data]

        self.run_dcnm_fabric_details.side_effect = [self.fabric_details]

        if "get_have_failure" in self._testMethodName:
            self.run_dcnm_send.side_effect = [self.get_have_failure]

        elif "_check_mode" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
            ]

        elif "_12check_mode" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
            ]

        elif "_merged_new" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "_12merged_new" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "_merged_novlan_new" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
                self.mock_vlan_get,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "error1" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
                self.blank_data,
                self.error1,
                self.blank_data,
            ]

        elif "error2" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
                self.blank_data,
                self.error2,
                self.blank_data,
            ]
        elif "error3" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
                self.blank_data,
                self.attach_success_resp,
                self.error3,
                self.blank_data,
            ]

        elif "_merged_duplicate" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
            ]

        elif "_merged_with_incorrect_netid" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
            ]

        elif "_merged_with_incorrect_vrf" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
            ]

        elif "_merged_with_update" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "replace_with_no_atch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.attach_success_resp,
                self.deploy_success_resp,
                self.delete_success_resp,
            ]

        elif "replace_with_changes" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.attach_success_resp,
                self.deploy_success_resp,
                self.delete_success_resp,
            ]

        elif "replace_without_changes" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
            ]

        elif "_merged_redeploy" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object_pending]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.blank_data,
                self.deploy_success_resp,
            ]

        elif "override_with_additions" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "override_without_changes" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
            ]

        elif "override_with_deletions" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.attach_success_resp,
                self.deploy_success_resp,
                self.mock_net_attach_object_del_not_ready,
                self.mock_net_attach_object_del_ready,
                self.mock_net_attach_object_del_ready,
                self.delete_success_resp,
                self.blank_data,
                self.attach_success_resp2,
                self.deploy_success_resp,
            ]

        elif "delete_std" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
                self.mock_net_attach_object_del_not_ready,
                self.mock_net_attach_object_del_ready,
                self.mock_net_attach_object_del_ready,
                self.delete_success_resp,
            ]

        elif "delete_without_config" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
                self.mock_net_attach_object_del_not_ready,
                self.mock_net_attach_object_del_ready,
                self.mock_net_attach_object_del_ready,
                self.delete_success_resp,
            ]

        elif "query_with_config" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.mock_vrf_object,
                self.mock_net_query_object,
                self.mock_net_attach_object
            ]

        elif "query_without_config" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.mock_vrf_object,
                self.mock_net_object,
                self.mock_net_attach_object
            ]

        elif "_merged_torport_new" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "_merged_torport_vererror" in self._testMethodName:
            self.init_data()

        elif "_merged_torport_roleerror" in self._testMethodName:
            self.init_data()

        elif "_merged_tor_with_update" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_tor_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "_replace_tor_ports" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_tor_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "_override_tor_ports" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_tor_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]
        else:
            pass

    def test_dcnm_net_blank_fabric(self):
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result.get("msg"),
            "Fabric test_network missing on DCNM or does not have any switches",
        )

    def test_dcnm_net_get_have_failure(self):
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(result.get("msg"), "Fabric test_network not present on DCNM")

    def test_dcnm_net_check_mode(self):
        set_module_args(
            dict(
                _ansible_check_mode=True,
                state="merged",
                fabric="test_network",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertTrue(result.get("diff"))
        self.assertFalse(result.get("response"))

    def test_dcnm_net_12check_mode(self):
        self.version = 12
        set_module_args(
            dict(
                _ansible_check_mode=True,
                state="merged",
                fabric="test_network",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.version = 11
        self.assertTrue(result.get("diff"))
        self.assertFalse(result.get("response"))

    def test_dcnm_net_merged_new(self):
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.217"
        )

    def test_dcnm_net_12merged_new(self):
        self.version = 12
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=True, failed=False)
        self.version = 11
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.217"
        )

    def test_dcnm_net_merged_novlan_new(self):
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config_novlan)
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.217"
        )

    def test_dcnm_net_error1(self):
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(result["msg"]["RETURN_CODE"], 400)
        self.assertEqual(result["msg"]["ERROR"], "There is an error")

    def test_dcnm_net_error2(self):
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertIn(
            "Entered Network VLAN ID 203 is in use already",
            str(result["msg"]["DATA"].values()),
        )

    def test_dcnm_net_error3(self):
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertEqual(
            result["response"][2]["DATA"], "No switches PENDING for deployment"
        )

    def test_dcnm_net_merged_duplicate(self):
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))

    def test_dcnm_net_merged_with_incorrect_netid(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_network",
                config=self.playbook_config_incorrect_netid,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result.get("msg"),
            "networkId can not be updated on existing network: test_network",
        )

    def test_dcnm_net_merged_with_incorrect_vrf(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_network",
                config=self.playbook_config_incorrect_vrf,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result.get("msg"),
            "VRF: ansible-vrf-int2 is missing in fabric: test_network",
        )

    def test_dcnm_net_merged_with_update(self):
        set_module_args(
            dict(
                state="merged", fabric="test_network", config=self.playbook_config_update
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.226"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.227"
        )
        self.assertEqual(result.get("diff")[0]["vrf_name"], "ansible-vrf-int1")

    def test_dcnm_net_replace_with_changes(self):
        set_module_args(
            dict(
                state="replaced",
                fabric="test_network",
                config=self.playbook_config_replace,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(result.get("diff")[0]["vlan_id"], 203)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result["response"][0]["DATA"]["test-network--9NN7E41N16A(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["test-network--9YO9A29F27U(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][1]["DATA"]["status"], "")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_net_replace_with_no_atch(self):
        set_module_args(
            dict(
                state="replaced",
                fabric="test_network",
                config=self.playbook_config_replace_no_atch,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertFalse(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["net_name"], "test_network")
        self.assertEqual(
            result["response"][0]["DATA"]["test-network--9NN7E41N16A(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["test-network--9YO9A29F27U(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][1]["DATA"]["status"], "")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_net_replace_without_changes(self):
        set_module_args(
            dict(state="replaced", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertFalse(result.get("response"))

    def test_dcnm_vrf_merged_redeploy(self):
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(result.get("diff")[0]["net_name"], "test_network")

    def test_dcnm_net_override_with_additions(self):
        set_module_args(
            dict(state="overridden", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.217"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.218"
        )
        self.assertEqual(result.get("diff")[0]["net_id"], 9008011)
        self.assertEqual(
            result["response"][1]["DATA"]["test-network--9NN7E41N16A(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][1]["DATA"]["test-network--9YO9A29F27U(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][2]["DATA"]["status"], "")
        self.assertEqual(result["response"][2]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_net_override_without_changes(self):
        set_module_args(
            dict(state="overridden", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertFalse(result.get("response"))

    def test_dcnm_net_override_with_deletions(self):
        set_module_args(
            dict(
                state="overridden",
                fabric="test_network",
                config=self.playbook_config_override,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["vlan_id"], 303)
        self.assertEqual(result.get("diff")[0]["net_id"], 9008012)

        self.assertFalse(result.get("diff")[1]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[1]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[1]["net_name"], "test_network")
        self.assertNotIn("net_id", result.get("diff")[1])

        self.assertEqual(
            result["response"][0]["DATA"]["test-network--9NN7E41N16A(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["test-network--9YO9A29F27U(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][1]["DATA"]["status"], "")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)
        self.assertEqual(
            result["response"][4]["DATA"]["test-network--9YO9A29F27U(leaf2)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][4]["DATA"]["test-network--XYZKSJHSMK3(leaf3)"], "SUCCESS"
        )

    def test_dcnm_net_delete_std(self):
        set_module_args(
            dict(state="deleted", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertFalse(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["net_name"], "test_network")
        self.assertNotIn("net_id", result.get("diff")[0])

        self.assertEqual(
            result["response"][0]["DATA"]["test-network--9NN7E41N16A(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["test-network--9YO9A29F27U(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][1]["DATA"]["status"], "")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_net_delete_without_config(self):
        set_module_args(dict(state="deleted", fabric="test_network", config=[]))
        result = self.execute_module(changed=True, failed=False)
        self.assertFalse(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["net_name"], "test_network")
        self.assertNotIn("net_id", result.get("diff")[0])

        self.assertEqual(
            result["response"][0]["DATA"]["test-network--9NN7E41N16A(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["test-network--9YO9A29F27U(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][1]["DATA"]["status"], "")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_net_query_with_config(self):
        set_module_args(
            dict(state="query", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertEqual(result.get("response")[0]["parent"]["networkName"], "test_network")
        self.assertEqual(result.get("response")[0]["parent"]["networkId"], 9008011)
        self.assertTrue(
            result.get("response")[0]["attach"][0]["deployment"],
        )
        self.assertEqual(
            result.get("response")[0]["attach"][0]["vlan"],
            202,
        )
        self.assertTrue(
            result.get("response")[0]["attach"][1]["deployment"],
        )
        self.assertEqual(
            result.get("response")[0]["attach"][1]["vlan"],
            202,
        )

    def test_dcnm_net_query_without_config(self):
        set_module_args(
            dict(state="query", fabric="test_network", config=[])
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertEqual(result.get("response")[0]["parent"]["networkName"], "test_network")
        self.assertEqual(result.get("response")[0]["parent"]["networkId"], 9008011)
        self.assertTrue(
            result.get("response")[0]["attach"][0]["deployment"],
        )
        self.assertEqual(
            result.get("response")[0]["attach"][0]["vlan"],
            202,
        )
        self.assertTrue(
            result.get("response")[0]["attach"][1]["deployment"],
        )
        self.assertEqual(
            result.get("response")[0]["attach"][1]["vlan"],
            202,
        )

    def test_dcnm_net_merged_torport_new(self):
        self.version = 12
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_tor_config)
        )
        result = self.execute_module(changed=True, failed=False)
        self.version = 11
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.217"
        )

    def test_dcnm_net_merged_torport_vererror(self):
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_tor_config)
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result.get("msg"),
            "Invalid parameters in playbook: tor_ports configurations are supported only on NDFC",
        )

    def test_dcnm_net_merged_torport_roleerror(self):
        self.version = 12
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_tor_roleerr_config)
        )
        result = self.execute_module(changed=False, failed=True)
        self.version = 11
        self.assertEqual(
            result.get("msg"),
            "tor_ports for Networks cannot be attached to switch 10.10.10.228 with role border",
        )

    def test_dcnm_net_merged_tor_with_update(self):
        self.version = 12
        set_module_args(
            dict(
                state="merged", fabric="test_network", config=self.playbook_tor_config_update
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.version = 11
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.218"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.217"
        )
        self.assertEqual(result.get("diff")[0]["vrf_name"], "ansible-vrf-int1")

    def test_dcnm_net_replace_tor_ports(self):
        self.version = 12
        set_module_args(
            dict(
                state="replaced", fabric="test_network", config=self.playbook_tor_config_update
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.version = 11
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.218"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.217"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["tor_ports"], "dt-n9k6(Ethernet1/13,Ethernet1/14)"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][1]["tor_ports"], "dt-n9k7(Ethernet1/13,Ethernet1/14)"
        )
        self.assertEqual(result.get("diff")[0]["vrf_name"], "ansible-vrf-int1")

    def test_dcnm_net_override_tor_ports(self):
        self.version = 12
        set_module_args(
            dict(
                state="overridden", fabric="test_network", config=self.playbook_tor_config_update
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.version = 11
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.218"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.217"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["tor_ports"], "dt-n9k6(Ethernet1/13,Ethernet1/14)"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][1]["tor_ports"], "dt-n9k7(Ethernet1/13,Ethernet1/14)"
        )
        self.assertEqual(result.get("diff")[0]["vrf_name"], "ansible-vrf-int1")
