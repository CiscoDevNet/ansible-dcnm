# Copyright (c) 2020-2022 Cisco and/or its affiliates.
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

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_resource_manager
from .dcnm_module import TestDcnmModule, set_module_args, loadPlaybookData


class TestDcnmResManagerModule(TestDcnmModule):

    module = dcnm_resource_manager
    fd = None

    def init_data(self):
        self.fd = None

    def log_msg(self, msg):

        if self.fd is None:
            self.fd = open("rm-ut.log", "a+")
        self.fd.write(msg)

    def setUp(self):

        super(TestDcnmResManagerModule, self).setUp()

        self.mock_dcnm_ip_sn = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_resource_manager.get_ip_sn_dict"
        )
        self.run_dcnm_ip_sn = self.mock_dcnm_ip_sn.start()

        self.mock_dcnm_fabric_details = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_resource_manager.get_fabric_inventory_details"
        )
        self.run_dcnm_fabric_details = self.mock_dcnm_fabric_details.start()

        self.mock_dcnm_send = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_resource_manager.dcnm_send"
        )
        self.run_dcnm_send = self.mock_dcnm_send.start()

        self.mock_dcnm_version_supported = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_resource_manager.dcnm_version_supported"
        )
        self.run_dcnm_version_supported = (
            self.mock_dcnm_version_supported.start()
        )

    def tearDown(self):

        super(TestDcnmResManagerModule, self).tearDown()
        self.mock_dcnm_send.stop()
        self.mock_dcnm_version_supported.stop()
        self.mock_dcnm_fabric_details.stop()
        self.mock_dcnm_ip_sn.stop()

    # -------------------------- FIXTURES --------------------------

    def load_rm_fixtures(self):

        if "test_dcnm_rm_merged_new" == self._testMethodName:

            get_rm_id_l3vni_resp = []
            get_rm_id_l2vni_resp = []
            get_rm_id_dev_sw1_resp = []
            get_rm_id_dev_sw2_resp = []
            get_rm_vpcid_dev_pair_sw1_resp = []
            get_rm_vpcid_dev_pair_sw2_resp = []
            get_rm_ip_fabric_resp = []
            get_rm_ip_dev_int_resp = []
            get_rm_subnet_link_resp = []
            create_rm_l3vni_resp = self.payloads_data.get(
                "create_rm_l3vni_resp"
            )
            create_rm_l2vni_resp = self.payloads_data.get(
                "create_rm_l2vni_resp"
            )
            create_rm_id_dev_sw1_resp = self.payloads_data.get(
                "create_rm_id_dev_sw1_resp"
            )
            create_rm_id_dev_sw2_resp = self.payloads_data.get(
                "create_rm_id_dev_sw2_resp"
            )
            create_rm_vpcid_dev_pair_sw1_resp = self.payloads_data.get(
                "create_rm_vpcid_dev_pair_sw1_resp"
            )
            create_rm_vpcid_dev_pair_sw2_resp = self.payloads_data.get(
                "create_rm_vpcid_dev_pair_sw2_resp"
            )
            create_rm_ip_fabric_resp = self.payloads_data.get(
                "create_rm_ip_fabric_resp"
            )
            create_rm_ip_dev_int_resp = self.payloads_data.get(
                "create_rm_ip_dev_int_resp"
            )
            create_rm_subnet_link_resp = self.payloads_data.get(
                "create_rm_subnet_link_resp"
            )

            self.run_dcnm_send.side_effect = [
                get_rm_id_l3vni_resp,
                get_rm_id_l2vni_resp,
                get_rm_id_dev_sw1_resp,
                get_rm_id_dev_sw2_resp,
                get_rm_vpcid_dev_pair_sw1_resp,
                get_rm_vpcid_dev_pair_sw2_resp,
                get_rm_ip_fabric_resp,
                get_rm_ip_dev_int_resp,
                get_rm_subnet_link_resp,
                create_rm_l3vni_resp,
                create_rm_l2vni_resp,
                create_rm_id_dev_sw1_resp,
                create_rm_id_dev_sw2_resp,
                create_rm_vpcid_dev_pair_sw1_resp,
                create_rm_vpcid_dev_pair_sw2_resp,
                create_rm_ip_fabric_resp,
                create_rm_ip_dev_int_resp,
                create_rm_subnet_link_resp,
            ]

        if "test_dcnm_rm_merged_existing" == self._testMethodName:

            get_rm_id_l3vni_resp = self.payloads_data.get(
                "get_rm_id_l3vni_resp"
            )
            get_rm_id_l2vni_resp = self.payloads_data.get(
                "get_rm_id_l2vni_resp"
            )
            get_rm_id_dev_sw1_resp = self.payloads_data.get(
                "get_rm_id_dev_sw1_resp"
            )
            get_rm_id_dev_sw2_resp = self.payloads_data.get(
                "get_rm_id_dev_sw2_resp"
            )
            get_rm_vpcid_dev_pair_sw1_resp = self.payloads_data.get(
                "get_rm_vpcid_dev_pair_sw1_resp"
            )
            get_rm_vpcid_dev_pair_sw2_resp = self.payloads_data.get(
                "get_rm_vpcid_dev_pair_sw2_resp"
            )
            get_rm_ip_fabric_resp = self.payloads_data.get(
                "get_rm_ip_fabric_resp"
            )
            get_rm_ip_dev_int_resp = self.payloads_data.get(
                "get_rm_ip_dev_int_resp"
            )
            get_rm_subnet_link_resp = self.payloads_data.get(
                "get_rm_subnet_link_resp"
            )
            create_rm_l3vni_resp = self.payloads_data.get(
                "create_rm_l3vni_resp"
            )
            create_rm_l2vni_resp = self.payloads_data.get(
                "create_rm_l2vni_resp"
            )
            create_rm_id_dev_sw1_resp = self.payloads_data.get(
                "create_rm_id_dev_sw1_resp"
            )
            create_rm_id_dev_sw2_resp = self.payloads_data.get(
                "create_rm_id_dev_sw2_resp"
            )
            create_rm_vpcid_dev_pair_sw1_resp = self.payloads_data.get(
                "create_rm_vpcid_dev_pair_sw1_resp"
            )
            create_rm_vpcid_dev_pair_sw2_resp = self.payloads_data.get(
                "create_rm_vpcid_dev_pair_sw2_resp"
            )
            create_rm_ip_fabric_resp = self.payloads_data.get(
                "create_rm_ip_fabric_resp"
            )
            create_rm_ip_dev_int_resp = self.payloads_data.get(
                "create_rm_ip_dev_int_resp"
            )
            create_rm_subnet_link_resp = self.payloads_data.get(
                "create_rm_subnet_link_resp"
            )

            self.run_dcnm_send.side_effect = [
                get_rm_id_l3vni_resp,
                get_rm_id_l2vni_resp,
                get_rm_id_dev_sw1_resp,
                get_rm_id_dev_sw2_resp,
                get_rm_vpcid_dev_pair_sw1_resp,
                get_rm_vpcid_dev_pair_sw2_resp,
                get_rm_ip_fabric_resp,
                get_rm_ip_dev_int_resp,
                get_rm_subnet_link_resp,
                create_rm_l3vni_resp,
                create_rm_l2vni_resp,
                create_rm_id_dev_sw1_resp,
                create_rm_id_dev_sw2_resp,
                create_rm_vpcid_dev_pair_sw1_resp,
                create_rm_vpcid_dev_pair_sw2_resp,
                create_rm_ip_fabric_resp,
                create_rm_ip_dev_int_resp,
                create_rm_subnet_link_resp,
            ]

        if "test_dcnm_rm_merged_new_no_state" == self._testMethodName:

            get_rm_id_l3vni_resp = []
            get_rm_id_l2vni_resp = []
            get_rm_id_dev_sw1_resp = []
            get_rm_id_dev_sw2_resp = []
            get_rm_vpcid_dev_pair_sw1_resp = []
            get_rm_vpcid_dev_pair_sw2_resp = []
            get_rm_ip_fabric_resp = []
            get_rm_ip_dev_int_resp = []
            get_rm_subnet_link_resp = []
            create_rm_l3vni_resp = self.payloads_data.get(
                "create_rm_l3vni_resp"
            )
            create_rm_l2vni_resp = self.payloads_data.get(
                "create_rm_l2vni_resp"
            )
            create_rm_id_dev_sw1_resp = self.payloads_data.get(
                "create_rm_id_dev_sw1_resp"
            )
            create_rm_id_dev_sw2_resp = self.payloads_data.get(
                "create_rm_id_dev_sw2_resp"
            )
            create_rm_vpcid_dev_pair_sw1_resp = self.payloads_data.get(
                "create_rm_vpcid_dev_pair_sw1_resp"
            )
            create_rm_vpcid_dev_pair_sw2_resp = self.payloads_data.get(
                "create_rm_vpcid_dev_pair_sw2_resp"
            )
            create_rm_ip_fabric_resp = self.payloads_data.get(
                "create_rm_ip_fabric_resp"
            )
            create_rm_ip_dev_int_resp = self.payloads_data.get(
                "create_rm_ip_dev_int_resp"
            )
            create_rm_subnet_link_resp = self.payloads_data.get(
                "create_rm_subnet_link_resp"
            )

            self.run_dcnm_send.side_effect = [
                get_rm_id_l3vni_resp,
                get_rm_id_l2vni_resp,
                get_rm_id_dev_sw1_resp,
                get_rm_id_dev_sw2_resp,
                get_rm_vpcid_dev_pair_sw1_resp,
                get_rm_vpcid_dev_pair_sw2_resp,
                get_rm_ip_fabric_resp,
                get_rm_ip_dev_int_resp,
                get_rm_subnet_link_resp,
                create_rm_l3vni_resp,
                create_rm_l2vni_resp,
                create_rm_id_dev_sw1_resp,
                create_rm_id_dev_sw2_resp,
                create_rm_vpcid_dev_pair_sw1_resp,
                create_rm_vpcid_dev_pair_sw2_resp,
                create_rm_ip_fabric_resp,
                create_rm_ip_dev_int_resp,
                create_rm_subnet_link_resp,
            ]

        if "test_dcnm_rm_merged_new_check_mode" == self._testMethodName:
            pass

        if (
            "test_dcnm_rm_merged_new_existing_and_non_existing"
            == self._testMethodName
        ):

            get_rm_id_l3vni_resp = []
            get_rm_id_l2vni_resp = []
            get_rm_id_dev_sw1_resp = self.payloads_data.get(
                "get_rm_id_dev_sw1_resp"
            )
            get_rm_id_dev_sw2_resp = self.payloads_data.get(
                "get_rm_id_dev_sw2_resp"
            )
            get_rm_vpcid_dev_pair_sw1_resp = self.payloads_data.get(
                "get_rm_vpcid_dev_pair_sw1_resp"
            )
            get_rm_vpcid_dev_pair_sw2_resp = self.payloads_data.get(
                "get_rm_vpcid_dev_pair_sw2_resp"
            )
            get_rm_ip_fabric_resp = self.payloads_data.get(
                "get_rm_ip_fabric_resp"
            )
            get_rm_ip_dev_int_resp = []
            get_rm_subnet_link_resp = []
            create_rm_l3vni_resp = self.payloads_data.get(
                "create_rm_l3vni_resp"
            )
            create_rm_l2vni_resp = self.payloads_data.get(
                "create_rm_l2vni_resp"
            )
            create_rm_id_dev_sw1_resp = self.payloads_data.get(
                "create_rm_id_dev_sw1_resp"
            )
            create_rm_id_dev_sw2_resp = self.payloads_data.get(
                "create_rm_id_dev_sw2_resp"
            )
            create_rm_vpcid_dev_pair_sw1_resp = self.payloads_data.get(
                "create_rm_vpcid_dev_pair_sw1_resp"
            )
            create_rm_vpcid_dev_pair_sw2_resp = self.payloads_data.get(
                "create_rm_vpcid_dev_pair_sw2_resp"
            )
            create_rm_ip_fabric_resp = self.payloads_data.get(
                "create_rm_ip_fabric_resp"
            )
            create_rm_ip_dev_int_resp = self.payloads_data.get(
                "create_rm_ip_dev_int_resp"
            )
            create_rm_subnet_link_resp = self.payloads_data.get(
                "create_rm_subnet_link_resp"
            )

            self.run_dcnm_send.side_effect = [
                get_rm_id_l3vni_resp,
                get_rm_id_l2vni_resp,
                get_rm_id_dev_sw1_resp,
                get_rm_id_dev_sw2_resp,
                get_rm_vpcid_dev_pair_sw1_resp,
                get_rm_vpcid_dev_pair_sw2_resp,
                get_rm_ip_fabric_resp,
                get_rm_ip_dev_int_resp,
                get_rm_subnet_link_resp,
                create_rm_l3vni_resp,
                create_rm_l2vni_resp,
                create_rm_id_dev_sw1_resp,
                create_rm_id_dev_sw2_resp,
                create_rm_vpcid_dev_pair_sw1_resp,
                create_rm_vpcid_dev_pair_sw2_resp,
                create_rm_ip_fabric_resp,
                create_rm_ip_dev_int_resp,
                create_rm_subnet_link_resp,
            ]

        if "test_dcnm_rm_modify_existing" == self._testMethodName:

            get_rm_id_l3vni_resp = self.payloads_data.get(
                "get_rm_id_l3vni_resp"
            )
            get_rm_id_l2vni_resp = self.payloads_data.get(
                "get_rm_id_l2vni_resp"
            )
            get_rm_id_dev_sw1_resp = self.payloads_data.get(
                "get_rm_id_dev_sw1_resp"
            )
            get_rm_id_dev_sw2_resp = self.payloads_data.get(
                "get_rm_id_dev_sw2_resp"
            )
            get_rm_vpcid_dev_pair_sw1_resp = self.payloads_data.get(
                "get_rm_vpcid_dev_pair_sw1_resp"
            )
            get_rm_vpcid_dev_pair_sw2_resp = self.payloads_data.get(
                "get_rm_vpcid_dev_pair_sw2_resp"
            )
            get_rm_ip_fabric_resp = self.payloads_data.get(
                "get_rm_ip_fabric_resp"
            )
            get_rm_ip_dev_int_resp = self.payloads_data.get(
                "get_rm_ip_dev_int_resp"
            )
            get_rm_subnet_link_resp = self.payloads_data.get(
                "get_rm_subnet_link_resp"
            )
            create_rm_l3vni_resp = self.payloads_data.get(
                "create_rm_l3vni_resp"
            )
            create_rm_l2vni_resp = self.payloads_data.get(
                "create_rm_l2vni_resp"
            )
            create_rm_id_dev_sw1_resp = self.payloads_data.get(
                "create_rm_id_dev_sw1_resp"
            )
            create_rm_id_dev_sw2_resp = self.payloads_data.get(
                "create_rm_id_dev_sw2_resp"
            )
            create_rm_vpcid_dev_pair_sw1_resp = self.payloads_data.get(
                "create_rm_vpcid_dev_pair_sw1_resp"
            )
            create_rm_vpcid_dev_pair_sw2_resp = self.payloads_data.get(
                "create_rm_vpcid_dev_pair_sw2_resp"
            )
            create_rm_ip_fabric_resp = self.payloads_data.get(
                "create_rm_ip_fabric_resp"
            )
            create_rm_ip_dev_int_resp = self.payloads_data.get(
                "create_rm_ip_dev_int_resp"
            )
            create_rm_subnet_link_resp = self.payloads_data.get(
                "create_rm_subnet_link_resp"
            )

            self.run_dcnm_send.side_effect = [
                get_rm_id_l3vni_resp,
                get_rm_id_l2vni_resp,
                get_rm_id_dev_sw1_resp,
                get_rm_id_dev_sw2_resp,
                get_rm_vpcid_dev_pair_sw1_resp,
                get_rm_vpcid_dev_pair_sw2_resp,
                get_rm_ip_fabric_resp,
                get_rm_ip_dev_int_resp,
                get_rm_subnet_link_resp,
                create_rm_l3vni_resp,
                create_rm_l2vni_resp,
                create_rm_id_dev_sw1_resp,
                create_rm_id_dev_sw2_resp,
                create_rm_vpcid_dev_pair_sw1_resp,
                create_rm_vpcid_dev_pair_sw2_resp,
                create_rm_ip_fabric_resp,
                create_rm_ip_dev_int_resp,
                create_rm_subnet_link_resp,
            ]

        if "test_dcnm_rm_delete_existing" == self._testMethodName:

            get_rm_id_l3vni_resp = self.payloads_data.get(
                "get_rm_id_l3vni_resp"
            )
            get_rm_id_l2vni_resp = self.payloads_data.get(
                "get_rm_id_l2vni_resp"
            )
            get_rm_id_dev_sw1_resp = self.payloads_data.get(
                "get_rm_id_dev_sw1_resp"
            )
            get_rm_id_dev_sw2_resp = self.payloads_data.get(
                "get_rm_id_dev_sw2_resp"
            )
            get_rm_vpcid_dev_pair_sw1_resp = self.payloads_data.get(
                "get_rm_vpcid_dev_pair_sw1_resp"
            )
            get_rm_vpcid_dev_pair_sw2_resp = self.payloads_data.get(
                "get_rm_vpcid_dev_pair_sw2_resp"
            )
            get_rm_ip_fabric_resp = self.payloads_data.get(
                "get_rm_ip_fabric_resp"
            )
            get_rm_ip_dev_int_resp = self.payloads_data.get(
                "get_rm_ip_dev_int_resp"
            )
            get_rm_subnet_link_resp = self.payloads_data.get(
                "get_rm_subnet_link_resp"
            )
            delete_rm_resp = self.payloads_data.get("delete_rm_resp")

            self.run_dcnm_send.side_effect = [
                get_rm_id_l3vni_resp,
                get_rm_id_l2vni_resp,
                get_rm_id_dev_sw1_resp,
                get_rm_id_dev_sw2_resp,
                get_rm_vpcid_dev_pair_sw1_resp,
                get_rm_vpcid_dev_pair_sw2_resp,
                get_rm_ip_fabric_resp,
                get_rm_ip_dev_int_resp,
                get_rm_subnet_link_resp,
                delete_rm_resp,
            ]

        if (
            "test_dcnm_rm_delete_existing_and_non_existing"
            == self._testMethodName
        ):

            get_rm_id_l3vni_resp = self.payloads_data.get(
                "get_rm_id_l3vni_resp"
            )
            get_rm_id_l2vni_resp = self.payloads_data.get(
                "get_rm_id_l2vni_resp"
            )
            get_rm_id_dev_sw1_resp = []
            get_rm_id_dev_sw2_resp = []
            get_rm_vpcid_dev_pair_sw1_resp = []
            get_rm_vpcid_dev_pair_sw2_resp = self.payloads_data.get(
                "get_rm_vpcid_dev_pair_sw2_resp"
            )
            get_rm_ip_fabric_resp = self.payloads_data.get(
                "get_rm_ip_fabric_resp"
            )
            get_rm_ip_dev_int_resp = []
            get_rm_subnet_link_resp = self.payloads_data.get(
                "get_rm_subnet_link_resp"
            )
            delete_rm_resp = self.payloads_data.get("delete_rm_resp")

            self.run_dcnm_send.side_effect = [
                get_rm_id_l3vni_resp,
                get_rm_id_l2vni_resp,
                get_rm_id_dev_sw1_resp,
                get_rm_id_dev_sw2_resp,
                get_rm_vpcid_dev_pair_sw1_resp,
                get_rm_vpcid_dev_pair_sw2_resp,
                get_rm_ip_fabric_resp,
                get_rm_ip_dev_int_resp,
                get_rm_subnet_link_resp,
                delete_rm_resp,
            ]

        if "test_dcnm_rm_delete_non_existing" == self._testMethodName:

            get_rm_id_l3vni_resp = []
            get_rm_id_l2vni_resp = []
            get_rm_id_dev_sw1_resp = []
            get_rm_id_dev_sw2_resp = []
            get_rm_vpcid_dev_pair_sw1_resp = []
            get_rm_vpcid_dev_pair_sw2_resp = []
            get_rm_ip_fabric_resp = []
            get_rm_ip_dev_int_resp = []
            get_rm_subnet_link_resp = []
            delete_rm_resp = self.payloads_data.get("delete_rm_resp")

            self.run_dcnm_send.side_effect = [
                get_rm_id_l3vni_resp,
                get_rm_id_l2vni_resp,
                get_rm_id_dev_sw1_resp,
                get_rm_id_dev_sw2_resp,
                get_rm_vpcid_dev_pair_sw1_resp,
                get_rm_vpcid_dev_pair_sw2_resp,
                get_rm_ip_fabric_resp,
                get_rm_ip_dev_int_resp,
                get_rm_subnet_link_resp,
                delete_rm_resp,
            ]

        if "test_dcnm_rm_query_no_config" == self._testMethodName:

            query_rm_resp = self.payloads_data.get("query_rm_resp")
            self.run_dcnm_send.side_effect = [query_rm_resp]

        if "test_dcnm_rm_query_with_" in self._testMethodName:

            query_rm_resp = self.payloads_data.get("query_rm_resp")
            self.run_dcnm_send.side_effect = [
                query_rm_resp,
                query_rm_resp,
                query_rm_resp,
                query_rm_resp,
                query_rm_resp,
                query_rm_resp,
                query_rm_resp,
                query_rm_resp,
                query_rm_resp,
                query_rm_resp,
            ]

    def load_fixtures(self, response=None, device=""):

        self.run_dcnm_version_supported.side_effect = [11]
        self.run_dcnm_fabric_details.side_effect = [self.mock_fab_inv]
        self.run_dcnm_ip_sn.side_effect = [[self.mock_ip_sn, []]]
        # Load resoure manager related side-effects
        self.load_rm_fixtures()

    # -------------------------- FIXTURES END --------------------------
    # -------------------------- TEST-CASES ----------------------------

    def test_dcnm_rm_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_rm_config")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(
            dict(
                state="merged", fabric="mmudigon", config=self.playbook_config
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 9)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_rm_merged_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_rm_config")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(
            dict(
                state="merged", fabric="mmudigon", config=self.playbook_config
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_rm_merged_new_no_state(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_rm_config")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(dict(fabric="mmudigon", config=self.playbook_config))
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 9)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_rm_merged_new_check_mode(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_rm_config")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(
            dict(
                _ansible_check_mode=True,
                state="merged",
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 9)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_rm_merged_new_existing_and_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_rm_config")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(
            dict(
                state="merged", fabric="mmudigon", config=self.playbook_config
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 4)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_rm_modify_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("modify_rm_config")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(
            dict(
                state="merged", fabric="mmudigon", config=self.playbook_config
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 9)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_rm_delete_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("delete_rm_config")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(
            dict(
                state="deleted", fabric="mmudigon", config=self.playbook_config
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 9)
        self.assertEqual(len(result["diff"][0]["query"]), 0)

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_rm_delete_existing_and_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("delete_rm_config")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(
            dict(
                state="deleted", fabric="mmudigon", config=self.playbook_config
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 5)
        self.assertEqual(len(result["diff"][0]["query"]), 0)

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_rm_delete_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("delete_rm_config")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(
            dict(
                state="deleted", fabric="mmudigon", config=self.playbook_config
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_rm_query_no_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = []
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(
            dict(state="query", fabric="mmudigon", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) > 0), True)

    def test_dcnm_rm_query_with_entity_name(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "query_rm_with_entity_name_config"
        )
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(
            dict(state="query", fabric="mmudigon", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) > 0), True)

    def test_dcnm_rm_query_with_entity_name_not_exist(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "query_rm_with_non_exist_entity_name_config"
        )
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(
            dict(state="query", fabric="mmudigon", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 0), True)

    def test_dcnm_rm_query_with_switch(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "query_rm_with_switch_config"
        )
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(
            dict(state="query", fabric="mmudigon", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) > 0), True)

    def test_dcnm_rm_query_with_pool_name(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "query_rm_with_poolname_config"
        )
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(
            dict(state="query", fabric="mmudigon", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) > 0), True)

    def test_dcnm_rm_query_with_pool_name_and_switch(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "query_rm_with_poolname_and_switch_config"
        )
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(
            dict(state="query", fabric="mmudigon", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) > 0), True)

    def test_dcnm_rm_query_with_mixed_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "query_rm_with_mixed_config"
        )
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(
            dict(state="query", fabric="mmudigon", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) > 0), True)

    def test_dcnm_rm_merge_l2dev_inv_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "create_rm_inv_ldev_config"
        )
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(
            dict(
                state="merged", fabric="mmudigon", config=self.playbook_config
            )
        )
        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(("is not valid" in str(e)), True)

    def test_dcnm_rm_merge_l2vni_inv_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "create_rm_inv_l2vni_config"
        )
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(
            dict(
                state="merged", fabric="mmudigon", config=self.playbook_config
            )
        )
        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(("is not valid" in str(e)), True)

    def test_dcnm_rm_merge_vpcid_inv_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "create_rm_inv_vpcid_config"
        )
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(
            dict(
                state="merged", fabric="mmudigon", config=self.playbook_config
            )
        )
        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(("is not valid" in str(e)), True)

    def test_dcnm_rm_merge_lip0_inv_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "create_rm_inv_lip0_config"
        )
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(
            dict(
                state="merged", fabric="mmudigon", config=self.playbook_config
            )
        )
        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(("is not valid" in str(e)), True)

    def test_dcnm_rm_merge_lip1_inv_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "create_rm_inv_lip1_config"
        )
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(
            dict(
                state="merged", fabric="mmudigon", config=self.playbook_config
            )
        )
        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(("is not valid" in str(e)), True)

    def test_dcnm_rm_merge_subnet_inv_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_res_manager_configs")
        self.payloads_data = loadPlaybookData("dcnm_res_manager_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "create_rm_inv_subnet_config"
        )
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")

        set_module_args(
            dict(
                state="merged", fabric="mmudigon", config=self.playbook_config
            )
        )
        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(("is not valid" in str(e)), True)
