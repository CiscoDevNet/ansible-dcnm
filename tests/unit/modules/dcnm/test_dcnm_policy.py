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

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_policy
from .dcnm_module import TestDcnmModule, set_module_args, loadPlaybookData


class TestDcnmPolicyModule(TestDcnmModule):

    module = dcnm_policy

    fd = None

    def init_data(self):
        pass

    def log_msg(self, msg):

        if self.fd is None:
            self.fd = open("policy-ut.log", "w+")
        self.fd.write(msg)
        self.fd.flush()

    def setUp(self):

        super(TestDcnmPolicyModule, self).setUp()

        self.mock_dcnm_fabric_details = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_policy.get_fabric_inventory_details"
        )
        self.run_dcnm_fabric_details = self.mock_dcnm_fabric_details.start()

        self.mock_dcnm_ip_sn = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_policy.get_ip_sn_dict"
        )
        self.run_dcnm_ip_sn = self.mock_dcnm_ip_sn.start()

        self.mock_dcnm_version_supported = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_policy.dcnm_version_supported"
        )
        self.run_dcnm_version_supported = self.mock_dcnm_version_supported.start()

        self.mock_dcnm_send = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_policy.dcnm_send"
        )
        self.run_dcnm_send = self.mock_dcnm_send.start()

    def tearDown(self):

        super(TestDcnmPolicyModule, self).tearDown()
        self.mock_dcnm_send.stop()
        self.mock_dcnm_version_supported.stop()

    # -------------------------- FIXTURES --------------------------

    def load_policy_fixtures(self):

        if "test_dcnm_policy_merged_new" == self._testMethodName:

            create_succ_resp1 = self.payloads_data.get("success_create_response_101")
            create_succ_resp2 = self.payloads_data.get("success_create_response_102")
            create_succ_resp3 = self.payloads_data.get("success_create_response_103")
            create_succ_resp4 = self.payloads_data.get("success_create_response_104")
            create_succ_resp5 = self.payloads_data.get("success_create_response_105")
            deploy_succ_resp = self.payloads_data.get("success_deploy_response_101_105")
            have_all_resp = self.payloads_data.get("policy_have_all_resp")

            self.run_dcnm_send.side_effect = [
                have_all_resp,
                create_succ_resp1,
                create_succ_resp2,
                create_succ_resp3,
                create_succ_resp4,
                create_succ_resp5,
                deploy_succ_resp,
            ]

        if "test_dcnm_policy_merged_diff_templates" == self._testMethodName:

            create_succ_resp1 = self.payloads_data.get("success_create_response_101")
            deploy_succ_resp = self.payloads_data.get(
                "success_deploy_response_101_105_11"
            )

            self.run_dcnm_send.side_effect = [
                [],
                create_succ_resp1,
                create_succ_resp1,
                create_succ_resp1,
                create_succ_resp1,
                create_succ_resp1,
                create_succ_resp1,
                create_succ_resp1,
                create_succ_resp1,
                create_succ_resp1,
                create_succ_resp1,
                create_succ_resp1,
                deploy_succ_resp,
            ]

        if "test_dcnm_policy_merged_same_template" == self._testMethodName:

            have_101_105_resp = self.payloads_data.get("have_response_101_105")
            create_succ_resp1 = self.payloads_data.get("success_create_response_101")
            deploy_succ_resp = self.payloads_data.get(
                "success_deploy_response_101_101_2"
            )

            self.run_dcnm_send.side_effect = [
                have_101_105_resp,
                create_succ_resp1,
                create_succ_resp1,
                deploy_succ_resp,
            ]

        if "test_dcnm_policy_merged_new_check_mode" == self._testMethodName:

            have_all_resp = self.payloads_data.get("policy_have_all_resp")

            self.run_dcnm_send.side_effect = [have_all_resp]

        if "test_dcnm_policy_merged_existing" == self._testMethodName:

            create_succ_resp1 = self.payloads_data.get("success_create_response_101")
            create_succ_resp2 = self.payloads_data.get("success_create_response_102")
            create_succ_resp3 = self.payloads_data.get("success_create_response_103")
            create_succ_resp4 = self.payloads_data.get("success_create_response_104")
            create_succ_resp5 = self.payloads_data.get("success_create_response_105")
            deploy_succ_resp = self.payloads_data.get("success_deploy_response_101_105")
            have_101_105_resp = self.payloads_data.get("have_response_101_105")

            self.run_dcnm_send.side_effect = [have_101_105_resp, deploy_succ_resp]

        if "test_dcnm_policy_merged_existing_and_non_exist" == self._testMethodName:

            create_succ_resp4 = self.payloads_data.get("success_create_response_104")
            create_succ_resp5 = self.payloads_data.get("success_create_response_105")
            deploy_succ_resp = self.payloads_data.get("success_deploy_response_101_105")
            have_101_103_resp = self.payloads_data.get("have_response_101_103")

            self.run_dcnm_send.side_effect = [
                have_101_103_resp,
                create_succ_resp4,
                create_succ_resp5,
                deploy_succ_resp,
            ]

        if (
            "test_dcnm_policy_merged_existing_and_non_exist_desc_as_key"
            == self._testMethodName
        ):

            have_101_103_resp = self.payloads_data.get("have_response_101_103")
            create_succ_resp4 = self.payloads_data.get("success_create_response_104")
            create_succ_resp5 = self.payloads_data.get("success_create_response_105")
            deploy_succ_resp = self.payloads_data.get("success_deploy_response_101_105")

            self.run_dcnm_send.side_effect = [
                have_101_103_resp,
                create_succ_resp4,
                create_succ_resp5,
                deploy_succ_resp,
            ]

        if "test_dcnm_policy_without_state" == self._testMethodName:

            create_succ_resp4 = self.payloads_data.get("success_create_response_104")
            create_succ_resp5 = self.payloads_data.get("success_create_response_105")
            deploy_succ_resp = self.payloads_data.get("success_deploy_response_104_105")

            self.run_dcnm_send.side_effect = [
                [],
                create_succ_resp4,
                create_succ_resp5,
                deploy_succ_resp,
            ]

        if "test_dcnm_policy_merge_additional_policies" == self._testMethodName:

            create_succ_resp4 = self.payloads_data.get("success_create_response_104")
            create_succ_resp4_1 = self.payloads_data.get(
                "success_create_response_104_1"
            )
            deploy_succ_resp = self.payloads_data.get(
                "success_deploy_response_104_104_1"
            )

            self.run_dcnm_send.side_effect = [
                [],
                create_succ_resp4,
                create_succ_resp4_1,
                deploy_succ_resp,
            ]

        if "test_dcnm_policy_merge_additional_policies_exist" == self._testMethodName:

            have_resp_104 = self.payloads_data.get("have_response_104")
            create_succ_resp4 = self.payloads_data.get("success_create_response_104")
            create_succ_resp4_1 = self.payloads_data.get(
                "success_create_response_104_1"
            )
            deploy_succ_resp = self.payloads_data.get(
                "success_deploy_response_104_104_1"
            )

            self.run_dcnm_send.side_effect = [
                have_resp_104,
                create_succ_resp4,
                create_succ_resp4_1,
                deploy_succ_resp,
            ]

        if "test_dcnm_policy_merge_multiple_switches" == self._testMethodName:

            create_succ_resp11 = self.payloads_data.get(
                "success_create_response_101"
            )
            create_succ_resp12 = self.payloads_data.get(
                "success_create_response_101_sw2"
            )
            create_succ_resp13 = self.payloads_data.get(
                "success_create_response_101_sw3"
            )
            create_succ_resp21 = self.payloads_data.get(
                "success_create_response_102"
            )
            create_succ_resp22 = self.payloads_data.get(
                "success_create_response_102_sw2"
            )
            create_succ_resp23 = self.payloads_data.get(
                "success_create_response_102_sw3"
            )
            create_succ_resp31 = self.payloads_data.get(
                "success_create_response_103"
            )
            create_succ_resp32 = self.payloads_data.get(
                "success_create_response_103_sw2"
            )
            create_succ_resp33 = self.payloads_data.get(
                "success_create_response_103_sw3"
            )
            create_succ_resp4 = self.payloads_data.get("success_create_response_104")
            create_succ_resp5 = self.payloads_data.get("success_create_response_105")
            deploy_succ_resp_multi_sw = self.payloads_data.get(
                "success_deploy_response_101_105_multi_switch"
            )

            self.run_dcnm_send.side_effect = [
                [],
                create_succ_resp11,
                create_succ_resp12,
                create_succ_resp13,
                create_succ_resp21,
                create_succ_resp22,
                create_succ_resp23,
                create_succ_resp31,
                create_succ_resp32,
                create_succ_resp33,
                create_succ_resp4,
                create_succ_resp5,
                deploy_succ_resp_multi_sw,
            ]

        if "test_dcnm_policy_merge_deploy_false" == self._testMethodName:

            create_succ_resp4 = self.payloads_data.get("success_create_response_104")

            self.run_dcnm_send.side_effect = [[], create_succ_resp4]

        if "test_dcnm_policy_merge_no_deploy" == self._testMethodName:

            create_succ_resp1 = self.payloads_data.get("success_create_response_101")
            create_succ_resp2 = self.payloads_data.get("success_create_response_102")
            create_succ_resp3 = self.payloads_data.get("success_create_response_103")
            create_succ_resp4 = self.payloads_data.get("success_create_response_104")
            create_succ_resp5 = self.payloads_data.get("success_create_response_105")
            deploy_succ_resp = self.payloads_data.get("success_deploy_response_101_105")
            have_all_resp = self.payloads_data.get("policy_have_all_resp")

            self.run_dcnm_send.side_effect = [
                have_all_resp,
                create_succ_resp1,
                create_succ_resp2,
                create_succ_resp3,
                create_succ_resp4,
                create_succ_resp5,
                deploy_succ_resp,
            ]

        if "test_dcnm_policy_merged_new_with_vars" == self._testMethodName:

            create_succ_resp1 = self.payloads_data.get("success_create_response_125")
            create_succ_resp2 = self.payloads_data.get("success_create_response_126")
            create_succ_resp3 = self.payloads_data.get("success_create_response_127")
            deploy_succ_resp = self.payloads_data.get("success_deploy_response_125_127")
            have_all_resp = self.payloads_data.get("policy_have_all_resp")

            self.run_dcnm_send.side_effect = [
                have_all_resp,
                create_succ_resp1,
                create_succ_resp2,
                create_succ_resp3,
                deploy_succ_resp,
            ]

        if "test_dcnm_policy_modify_with_template_name" == self._testMethodName:

            deploy_succ_resp = self.payloads_data.get("success_deploy_response_104")
            have_all_resp = self.payloads_data.get("have_response_101_105")
            create_succ_resp1 = self.payloads_data.get("success_create_response_104")

            self.run_dcnm_send.side_effect = [
                have_all_resp,
                create_succ_resp1,
                deploy_succ_resp,
            ]

        if (
            "test_dcnm_policy_merged_existing_different_template_desc_as_key"
            == self._testMethodName
        ):
            have_all_resp = self.payloads_data.get("have_response_101_105")
            create_succ_resp_101 = self.payloads_data.get("success_create_response_101")
            create_succ_resp_102 = self.payloads_data.get("success_create_response_102")
            get_resp_101 = self.payloads_data.get("get_response_101")
            get_resp_102 = self.payloads_data.get("get_response_102")
            mark_delete_resp_101 = self.payloads_data.get("mark_delete_response_101")
            mark_delete_resp_102 = self.payloads_data.get("mark_delete_response_102")
            self.run_dcnm_send.side_effect = [
                have_all_resp,
                get_resp_101,
                get_resp_102,
                mark_delete_resp_101,
                mark_delete_resp_102,
                create_succ_resp_101,
                create_succ_resp_102,
            ]
        if "test_dcnm_policy_modify_with_policy_id" == self._testMethodName:

            create_succ_resp4 = self.payloads_data.get("success_create_response_104")
            deploy_succ_resp = self.payloads_data.get("success_deploy_response_104")
            get_response_104 = self.payloads_data.get("get_response_104")
            have_all_resp = self.payloads_data.get("have_response_101_105")

            self.run_dcnm_send.side_effect = [
                get_response_104,
                have_all_resp,
                create_succ_resp4,
                deploy_succ_resp,
            ]

        if "test_dcnm_policy_modify_policy_with_vars" == self._testMethodName:

            create_succ_resp1 = self.payloads_data.get("success_create_response_125")
            deploy_succ_resp = self.payloads_data.get("success_deploy_response_125")
            have_all_resp = self.payloads_data.get("have_response_125")
            get_response_125 = self.payloads_data.get("get_response_125")

            self.run_dcnm_send.side_effect = [
                get_response_125,
                have_all_resp,
                create_succ_resp1,
                deploy_succ_resp,
            ]

        if "test_dcnm_policy_delete_with_template_name" == self._testMethodName:

            have_resp_101_105 = self.payloads_data.get("have_response_101_105")
            mark_delete_resp_101 = self.payloads_data.get("mark_delete_response_101")
            mark_delete_resp_102 = self.payloads_data.get("mark_delete_response_102")
            mark_delete_resp_103 = self.payloads_data.get("mark_delete_response_103")
            mark_delete_resp_104 = self.payloads_data.get("mark_delete_response_104")
            mark_delete_resp_105 = self.payloads_data.get("mark_delete_response_105")
            delete_config_save_resp = self.payloads_data.get(
                "delete_config_deploy_response_101_105"
            )
            config_preview = self.payloads_data.get("config_preview")

            self.run_dcnm_send.side_effect = [
                have_resp_101_105,
                mark_delete_resp_101,
                mark_delete_resp_102,
                mark_delete_resp_103,
                mark_delete_resp_104,
                mark_delete_resp_105,
                delete_config_save_resp,
                config_preview,
                [],
                [],
                [],
                [],
                [],
            ]

        if "test_dcnm_policy_delete_with_policy_id" == self._testMethodName:

            get_response_101 = self.payloads_data.get("get_response_101")
            get_response_102 = self.payloads_data.get("get_response_102")
            get_response_103 = self.payloads_data.get("get_response_103")
            get_response_104 = self.payloads_data.get("get_response_104")
            get_response_105 = self.payloads_data.get("get_response_105")
            have_resp_101_105 = self.payloads_data.get("have_response_101_105")
            mark_delete_resp_101 = self.payloads_data.get("mark_delete_response_101")
            mark_delete_resp_102 = self.payloads_data.get("mark_delete_response_102")
            mark_delete_resp_103 = self.payloads_data.get("mark_delete_response_103")
            mark_delete_resp_104 = self.payloads_data.get("mark_delete_response_104")
            mark_delete_resp_105 = self.payloads_data.get("mark_delete_response_105")
            delete_config_save_resp = self.payloads_data.get(
                "delete_config_deploy_response_101_105"
            )
            config_preview = self.payloads_data.get("config_preview")

            self.run_dcnm_send.side_effect = [
                get_response_101,
                get_response_102,
                get_response_103,
                get_response_104,
                get_response_105,
                have_resp_101_105,
                mark_delete_resp_101,
                mark_delete_resp_102,
                mark_delete_resp_103,
                mark_delete_resp_104,
                mark_delete_resp_105,
                delete_config_save_resp,
                config_preview,
                [],
                [],
                [],
                [],
                [],
            ]
        if (
            "test_dcnm_policy_delete_multiple_policies_with_template_name"
            == self._testMethodName
        ):

            have_resp_101_105_multi = self.payloads_data.get(
                "have_response_101_105_multi"
            )
            mark_delete_resp_101 = self.payloads_data.get("mark_delete_response_101")
            mark_delete_resp_102 = self.payloads_data.get("mark_delete_response_102")
            mark_delete_resp_103 = self.payloads_data.get("mark_delete_response_103")
            mark_delete_resp_104 = self.payloads_data.get("mark_delete_response_104")
            mark_delete_resp_105 = self.payloads_data.get("mark_delete_response_105")
            delete_config_save_resp = self.payloads_data.get(
                "delete_config_deploy_response_101_105"
            )
            config_preview = self.payloads_data.get("config_preview")

            self.run_dcnm_send.side_effect = [
                have_resp_101_105_multi,
                mark_delete_resp_101,
                mark_delete_resp_101,
                mark_delete_resp_101,
                mark_delete_resp_102,
                mark_delete_resp_102,
                mark_delete_resp_103,
                mark_delete_resp_104,
                mark_delete_resp_105,
                delete_config_save_resp,
                config_preview,
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
            ]
        if "test_dcnm_policy_delete_with_desc_as_key" == self._testMethodName:

            have_resp_101_105_multi = self.payloads_data.get(
                "have_response_101_105_multi"
            )
            mark_delete_resp_101 = self.payloads_data.get("mark_delete_response_101")
            mark_delete_resp_104 = self.payloads_data.get("mark_delete_response_104")
            mark_delete_resp_105 = self.payloads_data.get("mark_delete_response_105")
            get_response_101 = self.payloads_data.get("get_response_101")
            get_response_104 = self.payloads_data.get("get_response_104")
            get_response_105 = self.payloads_data.get("get_response_105")
            delete_config_save_resp = self.payloads_data.get(
                "delete_config_deploy_response_101_105"
            )

            self.run_dcnm_send.side_effect = [
                have_resp_101_105_multi,
                mark_delete_resp_101,
                mark_delete_resp_104,
                mark_delete_resp_105,
                [],
                [],
                [],
            ]

        if (
            "test_dcnm_policy_delete_with_template_name_with_second_delete"
            == self._testMethodName
        ):

            have_resp_101_105 = self.payloads_data.get("have_response_101_105")
            get_response_101 = self.payloads_data.get("get_response_101")
            get_response_102 = self.payloads_data.get("get_response_102")
            get_response_103 = self.payloads_data.get("get_response_103")
            get_response_104 = self.payloads_data.get("get_response_104")
            get_response_105 = self.payloads_data.get("get_response_105")
            mark_delete_resp_101 = self.payloads_data.get("mark_delete_response_101")
            mark_delete_resp_102 = self.payloads_data.get("mark_delete_response_102")
            mark_delete_resp_103 = self.payloads_data.get("mark_delete_response_103")
            mark_delete_resp_104 = self.payloads_data.get("mark_delete_response_104")
            mark_delete_resp_105 = self.payloads_data.get("mark_delete_response_105")
            delete_config_save_resp = self.payloads_data.get(
                "delete_config_deploy_response_101_105"
            )
            config_preview = self.payloads_data.get("config_preview")
            delete_resp_101 = self.payloads_data.get("delete_response_101")
            delete_resp_102 = self.payloads_data.get("delete_response_102")
            delete_resp_103 = self.payloads_data.get("delete_response_103")
            delete_resp_104 = self.payloads_data.get("delete_response_104")
            delete_resp_105 = self.payloads_data.get("delete_response_105")

            self.run_dcnm_send.side_effect = [
                have_resp_101_105,
                mark_delete_resp_101,
                mark_delete_resp_102,
                mark_delete_resp_103,
                mark_delete_resp_104,
                mark_delete_resp_105,
                delete_config_save_resp,
                config_preview,
                get_response_101,
                delete_resp_101,
                get_response_102,
                delete_resp_102,
                get_response_103,
                delete_resp_103,
                get_response_104,
                delete_resp_104,
                get_response_105,
                delete_resp_105,
                delete_config_save_resp,
            ]

        if "test_dcnm_policy_query_with_switch_info" == self._testMethodName:

            have_resp_101_105 = self.payloads_data.get("have_response_101_105")

            self.run_dcnm_send.side_effect = [
                have_resp_101_105,
            ]
        if "test_dcnm_policy_query_with_policy_id" == self._testMethodName:

            get_resp_101 = self.payloads_data.get("get_response_101")
            get_resp_102 = self.payloads_data.get("get_response_102")
            get_resp_103 = self.payloads_data.get("get_response_103")
            get_resp_104 = self.payloads_data.get("get_response_104")
            get_resp_105 = self.payloads_data.get("get_response_105")

            self.run_dcnm_send.side_effect = [
                get_resp_101,
                get_resp_102,
                get_resp_103,
                get_resp_104,
                get_resp_105,
            ]
        if "test_dcnm_policy_query_with_template_name" == self._testMethodName:

            have_resp_101_105 = self.payloads_data.get("have_response_101_105")

            self.run_dcnm_send.side_effect = [
                have_resp_101_105,
            ]
        if (
            "test_dcnm_policy_query_with_template_name_match_multi"
            == self._testMethodName
        ):

            have_resp_101_105_multi = self.payloads_data.get(
                "have_response_101_105_multi"
            )

            self.run_dcnm_send.side_effect = [
                have_resp_101_105_multi,
            ]

    def load_fixtures(self, response=None, device=""):

        # setup the side effects
        self.run_dcnm_fabric_details.side_effect = [self.mock_fab_inv]
        self.run_dcnm_ip_sn.side_effect = [[self.mock_ip_sn, []]]
        self.run_dcnm_version_supported.side_effect = [11]

        # Load policy related side-effects
        self.load_policy_fixtures()

    # -------------------------- FIXTURES END --------------------------
    # -------------------------- TEST-CASES --------------------------

    def test_dcnm_policy_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get("create_policy_101_105")

        set_module_args(
            dict(
                state="merged",
                deploy=True,
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 5)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 5)

        # Validate create and deploy responses
        count = 0
        max_count = len(result["diff"][0]["merged"])
        for resp in result["response"]:
            if count < max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (
                        "is created successfully"
                        in resp["DATA"]["successList"][0]["message"]
                    ),
                    True,
                )
            elif count == max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (len(resp["DATA"][0]["successPTIList"].split(",")) == 5), True
                )
            count = count + 1

    def test_dcnm_policy_merged_diff_templates(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get("create_policy_101_105_5")

        set_module_args(
            dict(
                state="merged",
                deploy=True,
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 11)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 1)

        # Validate create and deploy responses
        count = 0
        max_count = len(result["diff"][0]["merged"])
        for resp in result["response"]:
            if count < max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (
                        "is created successfully"
                        in resp["DATA"]["successList"][0]["message"]
                    ),
                    True,
                )
            elif count == max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (len(resp["DATA"][0]["successPTIList"].split(",")) == 11), True
                )
            count = count + 1

    def test_dcnm_policy_merged_same_template(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get("create_policy_101_101_5")

        set_module_args(
            dict(
                state="merged",
                deploy=True,
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 2)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 1)

        # Validate create and deploy responses
        count = 0
        max_count = len(result["diff"][0]["merged"])
        for resp in result["response"]:
            if count < max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (
                        "is created successfully"
                        in resp["DATA"]["successList"][0]["message"]
                    ),
                    True,
                )
            elif count == max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (len(resp["DATA"][0]["successPTIList"].split(",")) == 2), True
                )
            count = count + 1

    def test_dcnm_policy_merged_new_check_mode(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get("create_policy_101_105")

        set_module_args(
            dict(
                state="merged",
                deploy=True,
                fabric="mmudigon",
                _ansible_check_mode=True,
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 5)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)
        self.assertEqual(len(result["response"]), 0)

    def test_dcnm_policy_merged_existing(self):

        # Idempotence case
        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get("create_policy_101_105")

        set_module_args(
            dict(
                state="merged",
                deploy=True,
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 5)

        # Validate create and deploy responses
        count = 0
        max_count = len(result["diff"][0]["merged"])
        for resp in result["response"]:
            if count < max_count:
                count = count + 1
                continue

            if count == max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (len(resp["DATA"][0]["successPTIList"].split(",")) == 5), True
                )
            count = count + 1

    def test_dcnm_policy_merged_existing_and_non_exist(self):

        # Idempotence case
        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get("create_policy_101_105")

        set_module_args(
            dict(
                state="merged",
                deploy=True,
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 2)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 5)

        # Validate create and deploy responses
        count = 0
        max_count = len(result["diff"][0]["merged"])
        for resp in result["response"]:
            if count < max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (
                        "is created successfully"
                        in resp["DATA"]["successList"][0]["message"]
                    ),
                    True,
                )
            elif count == max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (len(resp["DATA"][0]["successPTIList"].split(",")) == 5), True
                )
            count = count + 1

    def test_dcnm_policy_merged_existing_and_non_exist_desc_as_key(self):

        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get("create_policy_101_105")

        set_module_args(
            dict(
                state="merged",
                deploy=True,
                fabric="mmudigon",
                use_desc_as_key=True,
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 2)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 5)

    def test_dcnm_policy_merged_existing_different_template_desc_as_key(self):

        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get("modify_policy_101_102")

        set_module_args(
            dict(
                state="merged",
                deploy=False,
                fabric="mmudigon",
                use_desc_as_key=True,
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 2)
        self.assertEqual(len(result["diff"][0]["deleted"]), 2)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_policy_without_state(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get(
            "create_policy_without_state_104_105"
        )

        set_module_args(
            dict(deploy=True, fabric="mmudigon", config=self.playbook_config)
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 2)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 2)

        # Validate create and deploy responses
        count = 0
        max_count = len(result["diff"][0]["merged"])
        for resp in result["response"]:
            if count < max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (
                        "is created successfully"
                        in resp["DATA"]["successList"][0]["message"]
                    ),
                    True,
                )
            elif count == max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (len(resp["DATA"][0]["successPTIList"].split(",")) == 2), True
                )
            count = count + 1

    def test_dcnm_policy_merge_additional_policies(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get(
            "create_policy_additional_flags_104"
        )

        set_module_args(
            dict(
                state="merged",
                deploy=True,
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 2)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 2)

        # Validate create and deploy responses
        count = 0
        max_count = len(result["diff"][0]["merged"])
        for resp in result["response"]:
            if count < max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (
                        "is created successfully"
                        in resp["DATA"]["successList"][0]["message"]
                    ),
                    True,
                )
            elif count == max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (len(resp["DATA"][0]["successPTIList"].split(",")) == 2), True
                )
            count = count + 1

    def test_dcnm_policy_merge_additional_policies_exist(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get(
            "create_policy_additional_flags_104"
        )

        set_module_args(
            dict(
                state="merged",
                deploy=True,
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 2)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 2)

        # Validate create and deploy responses
        count = 0
        max_count = len(result["diff"][0]["merged"])
        for resp in result["response"]:
            if count < max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (
                        "is created successfully"
                        in resp["DATA"]["successList"][0]["message"]
                    ),
                    True,
                )
            elif count == max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (len(resp["DATA"][0]["successPTIList"].split(",")) == 2), True
                )
            count = count + 1

    def test_dcnm_policy_merge_multiple_switches(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get(
            "create_policy_multi_switch_101_105"
        )

        set_module_args(
            dict(
                state="merged",
                deploy=True,
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 11)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 11)

        # Validate create and deploy responses
        count = 0
        max_count = len(result["diff"][0]["merged"])
        for resp in result["response"]:
            if count < max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (
                        "is created successfully"
                        in resp["DATA"]["successList"][0]["message"]
                    ),
                    True,
                )
            elif count == max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (len(resp["DATA"][0]["successPTIList"].split(",")) == 2), True
                )
                self.assertEqual(
                    (len(resp["DATA"][1]["successPTIList"].split(",")) == 3), True
                )
                self.assertEqual(
                    (len(resp["DATA"][2]["successPTIList"].split(",")) == 3), True
                )
            count = count + 1

    def test_dcnm_policy_merge_no_deploy(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get("create_policy_101_105")

        set_module_args(
            dict(state="merged", fabric="mmudigon", config=self.playbook_config)
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 5)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 5)

        # Validate create and deploy responses
        count = 0
        max_count = len(result["diff"][0]["merged"])
        for resp in result["response"]:
            if count < max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (
                        "is created successfully"
                        in resp["DATA"]["successList"][0]["message"]
                    ),
                    True,
                )
            elif count == max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (len(resp["DATA"][0]["successPTIList"].split(",")) == 5), True
                )
            count = count + 1

    def test_dcnm_policy_merge_deploy_false(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get("create_policy_no_deploy_104")

        set_module_args(
            dict(
                state="merged",
                deploy=False,
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        count = 0
        max_count = len(result["diff"][0]["merged"])
        for resp in result["response"]:
            if count < max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (
                        "is created successfully"
                        in resp["DATA"]["successList"][0]["message"]
                    ),
                    True,
                )
            elif count == max_count:
                self.assertEqual((count < max_count), True)
            count = count + 1

    def test_dcnm_policy_merged_new_with_vars(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get("create_policy_125_127_with_vars")

        set_module_args(
            dict(
                state="merged",
                deploy=True,
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 3)

        # Validate create and deploy responses
        count = 0
        max_count = len(result["diff"][0]["merged"])
        for resp in result["response"]:
            if count < max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (
                        "is created successfully"
                        in resp["DATA"]["successList"][0]["message"]
                    ),
                    True,
                )
            elif count == max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (len(resp["DATA"][0]["successPTIList"].split(",")) == 3), True
                )
            count = count + 1

    def test_dcnm_policy_modify_with_template_name(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get(
            "modify_policy_104_with_template_name"
        )

        set_module_args(
            dict(
                state="merged",
                deploy=True,
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 1)

        # Validate create and deploy responses
        count = 0
        max_count = len(result["diff"][0]["merged"])
        for resp in result["response"]:
            if count < max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (
                        "is created successfully"
                        in resp["DATA"]["successList"][0]["message"]
                    ),
                    True,
                )
            elif count == max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (len(resp["DATA"][0]["successPTIList"].split(",")) == 1), True
                )
            count = count + 1

    def test_dcnm_policy_modify_with_policy_id(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get("modify_policy_104_with_policy_id")

        set_module_args(
            dict(
                state="merged",
                deploy=True,
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(result["diff"][0]["merged"][0]["description"], "modifying policy with policy ID")

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 1)
        self.assertEqual(len(result["diff"][0]["skipped"]), 0)

        # Validate create and deploy responses
        count = 0
        max_count = len(result["diff"][0]["merged"])
        for resp in result["response"]:
            if count < max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (
                        "is created successfully"
                        in resp["DATA"]["successList"][0]["message"]
                    ),
                    True,
                )
            elif count == max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (len(resp["DATA"][0]["successPTIList"].split(",")) == 1), True
                )
            count = count + 1

    def test_dcnm_policy_modify_policy_with_vars(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get("modify_policy_125_with_vars")

        set_module_args(
            dict(
                state="merged",
                deploy=True,
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 1)
        self.assertEqual(len(result["diff"][0]["skipped"]), 0)

        # Validate create and deploy responses
        count = 0
        max_count = len(result["diff"][0]["merged"])
        for resp in result["response"]:
            if count < max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (
                        "is created successfully"
                        in resp["DATA"]["successList"][0]["message"]
                    ),
                    True,
                )
            elif count == max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    (len(resp["DATA"][0]["successPTIList"].split(",")) == 1), True
                )
            count = count + 1

    def test_dcnm_policy_delete_with_template_name(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get(
            "delete_policy_template_name_101_105"
        )

        set_module_args(
            dict(
                state="deleted",
                deploy=True,
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 5)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)
        self.assertEqual(len(result["diff"][0]["skipped"]), 0)

        # Validate create and deploy responses
        count = 0
        max_count = len(result["diff"][0]["deleted"])
        for resp in result["response"]:
            if count < max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertTrue(resp["DATA"]["deleted"])
                # MGW: self.assertEqual((resp["DATA"]["deleted"] == True), True)
            elif count == max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    ("Config deployment has been triggered" in resp["DATA"]["status"]),
                    True,
                )
            else:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    ("Deleted successfully" in resp["DATA"]["message"]), True
                )
            count = count + 1

    def test_dcnm_policy_delete_with_desc_as_key(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get(
            "delete_policy_template_desc_101_105"
        )

        set_module_args(
            dict(
                state="deleted",
                deploy=False,
                fabric="mmudigon",
                use_desc_as_key=True,
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 3)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)
        self.assertEqual(len(result["diff"][0]["skipped"]), 0)

    def test_dcnm_policy_delete_with_policy_id(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get("delete_policy_policy_id_101_105")

        set_module_args(
            dict(
                state="deleted",
                deploy=True,
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 5)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)
        self.assertEqual(len(result["diff"][0]["skipped"]), 0)

        # Validate create and deploy responses
        count = 0
        max_count = len(result["diff"][0]["deleted"])
        for resp in result["response"]:
            if count < max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertTrue(resp["DATA"]["deleted"])
                # MGW: self.assertEqual((resp["DATA"]["deleted"] == True), True)
            elif count == max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    ("Config deployment has been triggered" in resp["DATA"]["status"]),
                    True,
                )
            else:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    ("Deleted successfully" in resp["DATA"]["message"]), True
                )
            count = count + 1

    def test_dcnm_policy_delete_multiple_policies_with_template_name(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get("delete_policy_template_name_multi")

        set_module_args(
            dict(
                state="deleted",
                deploy=True,
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 8)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)
        self.assertEqual(len(result["diff"][0]["skipped"]), 0)

        # Validate create and deploy responses
        count = 0
        max_count = len(result["diff"][0]["deleted"])
        for resp in result["response"]:
            if count < max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertTrue(resp["DATA"]["deleted"])
                # MGW: self.assertEqual((resp["DATA"]["deleted"] == True), True)
            elif count == max_count:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    ("Config deployment has been triggered" in resp["DATA"]["status"]),
                    True,
                )
            else:
                self.assertEqual(resp["RETURN_CODE"], 200)
                self.assertEqual(
                    ("Deleted successfully" in resp["DATA"]["message"]), True
                )
            count = count + 1

    def test_dcnm_policy_delete_with_template_name_with_second_delete(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get(
            "delete_policy_template_name_101_105"
        )

        set_module_args(
            dict(
                state="deleted",
                deploy=True,
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 5)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)
        self.assertEqual(len(result["diff"][0]["skipped"]), 0)

        # Validate create and deploy responses
        max_count = len(result["diff"][0]["deleted"])
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_policy_query_with_switch_info(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get("query_policy_with_switch_info")

        set_module_args(
            dict(
                state="query",
                deploy=True,
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 5)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)
        self.assertEqual(len(result["diff"][0]["skipped"]), 0)
        self.assertEqual((len(result["response"]) == 5), True)

    def test_dcnm_policy_query_with_policy_id(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get("query_policy_with_policy_id")

        set_module_args(
            dict(
                state="query",
                deploy=True,
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 5)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)
        self.assertEqual(len(result["diff"][0]["skipped"]), 0)
        self.assertEqual((len(result["response"]) == 5), True)

    def test_dcnm_policy_query_with_template_name(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get("query_policy_with_template_name")

        set_module_args(
            dict(
                state="query",
                deploy=True,
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 5)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)
        self.assertEqual(len(result["diff"][0]["skipped"]), 0)
        self.assertEqual((len(result["response"]) == 5), True)

    def test_dcnm_policy_query_with_template_name_match_multi(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get("query_policy_with_template_name")

        set_module_args(
            dict(
                state="query",
                deploy=True,
                fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 5)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)
        self.assertEqual(len(result["diff"][0]["skipped"]), 0)
        self.assertEqual((len(result["response"]) == 8), True)

    def test_dcnm_policy_wrong_state(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_policy_payloads")

        # get mock ip_sn and fabric_inventory_details
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")

        # load required config data
        self.playbook_config = self.config_data.get("create_policy_wrong_state_104")

        set_module_args(
            dict(state="replaced", fabric="mmudigon", config=self.playbook_config)
        )
        result = None
        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception:
            self.assertEqual(result, None)
