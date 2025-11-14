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

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_service_policy
from .dcnm_module import TestDcnmModule, set_module_args, loadPlaybookData

import copy


class TestDcnmServicePolicyModule(TestDcnmModule):

    module = dcnm_service_policy
    fd = None

    def init_data(self):
        self.fd = None

    def log_msg(self, msg):

        if self.fd is None:
            self.fd = open("sp-ut.log", "w+")
        self.fd.write(msg)

    def setUp(self):

        super(TestDcnmServicePolicyModule, self).setUp()

        self.mock_dcnm_send = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_service_policy.dcnm_send"
        )
        self.run_dcnm_send = self.mock_dcnm_send.start()

        self.mock_dcnm_version_supported = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_service_policy.dcnm_version_supported"
        )
        self.run_dcnm_version_supported = self.mock_dcnm_version_supported.start()

        self.mock_dcnm_reset_connection = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_service_policy.dcnm_reset_connection"
        )
        self.run_dcnm_reset_connection = self.mock_dcnm_reset_connection.start()

    def tearDown(self):

        super(TestDcnmServicePolicyModule, self).tearDown()
        self.mock_dcnm_send.stop()
        self.mock_dcnm_version_supported.stop()
        self.mock_dcnm_reset_connection.stop()

    # -------------------------- FIXTURES --------------------------

    def load_sp_fixtures(self):

        if "test_dcnm_sp_merged_new" == self._testMethodName:

            have_sp1_resp = []
            have_sp2_resp = []
            have_sp3_resp = []
            get_snt_resp1 = self.payloads_data.get("get_snt1_response")
            get_snt_resp2 = self.payloads_data.get("get_snt2_response")
            create_sp1_resp = self.payloads_data.get("create_sp1_resp")
            create_sp2_resp = self.payloads_data.get("create_sp2_resp")
            create_sp3_resp = self.payloads_data.get("create_sp3_resp")
            deploy_sp1_resp = self.payloads_data.get("deploy_sp1_resp")
            deploy_sp2_sp3_resp = self.payloads_data.get("deploy_sp2_sp3_resp")
            get_sn1_att_status = self.payloads_data.get("get_sn1_att_status")
            get_sn2_att_status = self.payloads_data.get("get_sn2_att_status")

            self.run_dcnm_send.side_effect = [
                get_snt_resp1,
                get_snt_resp2,
                get_snt_resp2,
                have_sp1_resp,
                have_sp2_resp,
                have_sp3_resp,
                create_sp1_resp,
                create_sp2_resp,
                create_sp3_resp,
                deploy_sp1_resp,
                deploy_sp2_sp3_resp,
                get_sn1_att_status,
                get_sn2_att_status,
                get_sn2_att_status,
            ]

        if "test_dcnm_sp_merged_new_no_opt_elems" == self._testMethodName:

            have_sp1_resp = []
            have_sp2_resp = []
            get_snt_resp1 = self.payloads_data.get("get_snt1_response")
            get_snt_resp2 = self.payloads_data.get("get_snt2_response")
            create_sp1_resp = self.payloads_data.get("create_sp1_resp")
            create_sp2_resp = self.payloads_data.get("create_sp2_resp")
            deploy_sp1_resp = self.payloads_data.get("deploy_sp1_resp")
            deploy_sp2_sp3_resp = self.payloads_data.get("deploy_sp2_sp3_resp")
            get_sn1_att_status = self.payloads_data.get("get_sn1_att_status")
            get_sn2_att_status = self.payloads_data.get("get_sn2_att_status")

            self.run_dcnm_send.side_effect = [
                get_snt_resp1,
                get_snt_resp2,
                have_sp1_resp,
                have_sp2_resp,
                create_sp1_resp,
                create_sp2_resp,
                deploy_sp1_resp,
                deploy_sp2_sp3_resp,
                get_sn1_att_status,
                get_sn2_att_status,
            ]

        if "test_dcnm_sp_merged_existing_no_opt_elems" == self._testMethodName:

            have_sp1_resp = self.payloads_data.get("get_sp1_resp")
            have_sp2_resp = self.payloads_data.get("get_sp2_resp")
            get_sn1_att_status = self.payloads_data.get("get_sn1_att_status")
            get_sn2_att_status = self.payloads_data.get("get_sn2_att_status")
            get_snt_resp1 = self.payloads_data.get("get_snt1_response")
            get_snt_resp2 = self.payloads_data.get("get_snt2_response")
            create_sp1_resp = self.payloads_data.get("create_sp1_resp")
            create_sp2_resp = self.payloads_data.get("create_sp2_resp")
            deploy_sp1_resp = self.payloads_data.get("deploy_sp1_resp")
            deploy_sp2_sp3_resp = self.payloads_data.get("deploy_sp2_sp3_resp")
            get_sn1_att_status = self.payloads_data.get("get_sn1_att_status")
            get_sn2_att_status = self.payloads_data.get("get_sn2_att_status")

            self.run_dcnm_send.side_effect = [
                get_snt_resp1,
                get_snt_resp2,
                have_sp1_resp,
                have_sp2_resp,
                get_sn1_att_status,
                get_sn2_att_status,
                create_sp1_resp,
                create_sp2_resp,
                deploy_sp1_resp,
                deploy_sp2_sp3_resp,
                get_sn1_att_status,
                get_sn2_att_status,
            ]

        if "test_dcnm_sp_merged_new_check_mode" == self._testMethodName:
            pass

        if "test_dcnm_sp_merged_new_unauth_error" == self._testMethodName:

            have_sp1_resp = []
            have_sp2_resp = []
            get_snt_resp1 = self.payloads_data.get("get_snt1_response")
            get_snt_resp2 = self.payloads_data.get("get_snt2_response")
            create_sp1_resp = self.payloads_data.get("create_sp1_resp")
            create_sp2_resp = self.payloads_data.get("create_sp2_resp")
            deploy_sp1_resp = self.payloads_data.get("deploy_sp1_resp")
            deploy_sp2_sp3_resp = self.payloads_data.get("deploy_sp2_sp3_resp")
            resp_unauth_err = self.payloads_data.get("resp_unauth_err")
            get_sn1_att_status = self.payloads_data.get("get_sn1_att_status")
            get_sn2_att_status = self.payloads_data.get("get_sn2_att_status")

            self.run_dcnm_send.side_effect = [
                get_snt_resp1,
                get_snt_resp2,
                have_sp1_resp,
                have_sp2_resp,
                resp_unauth_err,
                [],
                create_sp1_resp,
                create_sp2_resp,
                deploy_sp1_resp,
                deploy_sp2_sp3_resp,
                get_sn1_att_status,
                get_sn2_att_status,
            ]

        if "test_dcnm_sp_config_without_state" == self._testMethodName:

            have_sp1_resp = []
            have_sp2_resp = []
            have_sp3_resp = []
            get_snt_resp1 = self.payloads_data.get("get_snt1_response")
            get_snt_resp2 = self.payloads_data.get("get_snt2_response")
            get_snt_resp3 = self.payloads_data.get("get_snt2_response")
            create_sp1_resp = self.payloads_data.get("create_sp1_resp")
            create_sp2_resp = self.payloads_data.get("create_sp2_resp")
            create_sp3_resp = self.payloads_data.get("create_sp3_resp")
            deploy_sp1_resp = self.payloads_data.get("deploy_sp1_resp")
            deploy_sp2_sp3_resp = self.payloads_data.get("deploy_sp2_sp3_resp")
            get_sn1_att_status = self.payloads_data.get("get_sn1_att_status")
            get_sn2_att_status = self.payloads_data.get("get_sn2_att_status")

            self.run_dcnm_send.side_effect = [
                get_snt_resp1,
                get_snt_resp2,
                get_snt_resp3,
                have_sp1_resp,
                have_sp2_resp,
                have_sp3_resp,
                create_sp1_resp,
                create_sp2_resp,
                create_sp3_resp,
                deploy_sp1_resp,
                deploy_sp2_sp3_resp,
                get_sn1_att_status,
                get_sn2_att_status,
                get_sn2_att_status,
            ]

        if "test_dcnm_sp_merge_no_deploy" == self._testMethodName:

            have_sp1_resp = []
            have_sp2_resp = []
            have_sp3_resp = []
            get_snt_resp1 = self.payloads_data.get("get_snt1_response")
            get_snt_resp2 = self.payloads_data.get("get_snt2_response")
            get_snt_resp3 = self.payloads_data.get("get_snt2_response")
            create_sp1_resp = self.payloads_data.get("create_sp1_resp")
            create_sp2_resp = self.payloads_data.get("create_sp2_resp")
            create_sp3_resp = self.payloads_data.get("create_sp3_resp")
            deploy_sp1_resp = self.payloads_data.get("deploy_sp1_resp")
            deploy_sp2_sp3_resp = self.payloads_data.get("deploy_sp2_sp3_resp")
            get_sn1_att_status = self.payloads_data.get("get_sn1_att_status")
            get_sn2_att_status = self.payloads_data.get("get_sn2_att_status")

            self.run_dcnm_send.side_effect = [
                get_snt_resp1,
                get_snt_resp2,
                get_snt_resp3,
                have_sp1_resp,
                have_sp2_resp,
                have_sp3_resp,
                create_sp1_resp,
                create_sp2_resp,
                create_sp3_resp,
                deploy_sp1_resp,
                deploy_sp2_sp3_resp,
                get_sn1_att_status,
                get_sn2_att_status,
                get_sn2_att_status,
            ]

            pass

        if "test_dcnm_sp_merge_deploy_false" == self._testMethodName:

            have_sp1_resp = []
            have_sp2_resp = []
            have_sp3_resp = []
            get_snt_resp1 = self.payloads_data.get("get_snt1_response")
            get_snt_resp2 = self.payloads_data.get("get_snt2_response")
            get_snt_resp3 = self.payloads_data.get("get_snt2_response")
            create_sp1_resp = self.payloads_data.get("create_sp1_resp")
            create_sp2_resp = self.payloads_data.get("create_sp2_resp")
            create_sp3_resp = self.payloads_data.get("create_sp3_resp")

            self.run_dcnm_send.side_effect = [
                get_snt_resp1,
                get_snt_resp2,
                get_snt_resp3,
                have_sp1_resp,
                have_sp2_resp,
                have_sp3_resp,
                create_sp1_resp,
                create_sp2_resp,
                create_sp3_resp,
            ]

        if "test_dcnm_sp_merged_existing_and_non_existing" == self._testMethodName:

            have_sp1_resp = self.payloads_data.get("get_sp1_resp")
            have_sp2_resp = []
            have_sp3_resp = []
            get_sn1_att_status = self.payloads_data.get("get_sn1_att_status")
            get_sn2_att_status = self.payloads_data.get("get_sn2_att_status")
            get_snt_resp1 = self.payloads_data.get("get_snt1_response")
            get_snt_resp2 = self.payloads_data.get("get_snt2_response")
            get_snt_resp3 = self.payloads_data.get("get_snt2_response")
            create_sp2_resp = self.payloads_data.get("create_sp2_resp")
            create_sp3_resp = self.payloads_data.get("create_sp3_resp")
            deploy_sp2_sp3_resp = self.payloads_data.get("deploy_sp2_sp3_resp")
            get_sn1_att_status = self.payloads_data.get("get_sn1_att_status")
            get_sn2_att_status = self.payloads_data.get("get_sn2_att_status")

            self.run_dcnm_send.side_effect = [
                get_snt_resp1,
                get_snt_resp2,
                get_snt_resp3,
                have_sp1_resp,
                have_sp2_resp,
                have_sp3_resp,
                get_sn1_att_status,
                create_sp2_resp,
                create_sp3_resp,
                deploy_sp2_sp3_resp,
                get_sn2_att_status,
                get_sn2_att_status,
            ]

            pass

        if "test_dcnm_sp_merged_update_existing" == self._testMethodName:
            pass

        if "test_dcnm_sp_delete_existing_no_config" == self._testMethodName:

            get_snodes_resp = self.payloads_data.get("get_service_nodes_resp")
            get_policy_with_sn1 = self.payloads_data.get("get_policy_with_sn1")
            get_policy_with_sn2 = self.payloads_data.get("get_policy_with_sn2")
            det_sp1_resp = self.payloads_data.get("detach_sp1_resp")
            det_sp2_sp3_resp = self.payloads_data.get("detach_sp2_sp3_resp")
            delete_sp1_resp = self.payloads_data.get("delete_sp1_resp")
            delete_sp2_resp = self.payloads_data.get("delete_sp2_resp")
            delete_sp3_resp = self.payloads_data.get("delete_sp3_resp")
            deploy_sp1_resp = self.payloads_data.get("deploy_sp1_resp")
            deploy_sp2_sp3_resp = self.payloads_data.get("deploy_sp2_sp3_resp")
            get_dd_sn1_att_status = self.payloads_data.get("get_dd_sn1_att_status")
            get_dd_sn2_att_status = self.payloads_data.get("get_dd_sn2_att_status")

            self.run_dcnm_send.side_effect = [
                get_snodes_resp,
                get_policy_with_sn1,
                get_policy_with_sn2,
                det_sp1_resp,
                det_sp2_sp3_resp,
                deploy_sp1_resp,
                deploy_sp2_sp3_resp,
                get_dd_sn1_att_status,
                get_dd_sn2_att_status,
                get_dd_sn2_att_status,
                delete_sp1_resp,
                delete_sp2_resp,
                delete_sp3_resp,
            ]

        if "test_dcnm_sp_delete_existing_with_node_names" == self._testMethodName:

            get_policy_with_sn1 = self.payloads_data.get("get_policy_with_sn1")
            get_policy_with_sn2 = self.payloads_data.get("get_policy_with_sn2")
            det_sp1_resp = self.payloads_data.get("detach_sp1_resp")
            det_sp2_sp3_resp = self.payloads_data.get("detach_sp2_sp3_resp")
            delete_sp1_resp = self.payloads_data.get("delete_sp1_resp")
            delete_sp2_resp = self.payloads_data.get("delete_sp2_resp")
            delete_sp3_resp = self.payloads_data.get("delete_sp3_resp")
            deploy_sp1_resp = self.payloads_data.get("deploy_sp1_resp")
            deploy_sp2_sp3_resp = self.payloads_data.get("deploy_sp2_sp3_resp")
            get_dd_sn1_att_status = self.payloads_data.get("get_dd_sn1_att_status")
            get_dd_sn2_att_status = self.payloads_data.get("get_dd_sn2_att_status")

            self.run_dcnm_send.side_effect = [
                get_policy_with_sn1,
                get_policy_with_sn2,
                det_sp1_resp,
                det_sp2_sp3_resp,
                deploy_sp1_resp,
                deploy_sp2_sp3_resp,
                get_dd_sn1_att_status,
                get_dd_sn2_att_status,
                get_dd_sn2_att_status,
                delete_sp1_resp,
                delete_sp2_resp,
                delete_sp3_resp,
            ]

        if (
            "test_dcnm_sp_delete_existing_with_node_name_and_policy_name"
            == self._testMethodName
        ):

            have_sp1_resp = self.payloads_data.get("get_sp1_resp")
            have_sp2_resp = self.payloads_data.get("get_sp2_resp")
            have_sp3_resp = self.payloads_data.get("get_sp3_resp")
            det_sp1_resp = self.payloads_data.get("detach_sp1_resp")
            det_sp2_sp3_resp = self.payloads_data.get("detach_sp2_sp3_resp")
            delete_sp1_resp = self.payloads_data.get("delete_sp1_resp")
            delete_sp2_resp = self.payloads_data.get("delete_sp2_resp")
            delete_sp3_resp = self.payloads_data.get("delete_sp3_resp")
            get_dd_sn1_att_status = self.payloads_data.get("get_dd_sn1_att_status")
            get_dd_sn2_att_status = self.payloads_data.get("get_dd_sn2_att_status")
            deploy_sp1_resp = self.payloads_data.get("deploy_sp1_resp")
            deploy_sp2_sp3_resp = self.payloads_data.get("deploy_sp2_sp3_resp")

            self.run_dcnm_send.side_effect = [
                have_sp1_resp,
                have_sp2_resp,
                have_sp3_resp,
                det_sp1_resp,
                det_sp2_sp3_resp,
                deploy_sp1_resp,
                deploy_sp2_sp3_resp,
                get_dd_sn1_att_status,
                get_dd_sn2_att_status,
                get_dd_sn2_att_status,
                delete_sp1_resp,
                delete_sp2_resp,
                delete_sp3_resp,
            ]

        if (
            "test_dcnm_sp_delete_existing_with_node_name_and_rp_name"
            == self._testMethodName
        ):

            get_policy_with_sn1 = self.payloads_data.get("get_policy_with_sn1")
            get_policy_with_sn2 = self.payloads_data.get("get_policy_with_sn2")
            det_sp1_resp = self.payloads_data.get("detach_sp1_resp")
            det_sp2_sp3_resp = self.payloads_data.get("detach_sp2_sp3_resp")
            delete_sp1_resp = self.payloads_data.get("delete_sp1_resp")
            delete_sp2_resp = self.payloads_data.get("delete_sp2_resp")
            delete_sp3_resp = self.payloads_data.get("delete_sp3_resp")
            deploy_sp1_resp = self.payloads_data.get("deploy_sp1_resp")
            deploy_sp2_sp3_resp = self.payloads_data.get("deploy_sp2_sp3_resp")
            get_dd_sn1_att_status = self.payloads_data.get("get_dd_sn1_att_status")
            get_dd_sn2_att_status = self.payloads_data.get("get_dd_sn2_att_status")

            self.run_dcnm_send.side_effect = [
                get_policy_with_sn1,
                get_policy_with_sn2,
                det_sp1_resp,
                det_sp2_sp3_resp,
                deploy_sp1_resp,
                deploy_sp2_sp3_resp,
                get_dd_sn1_att_status,
                get_dd_sn2_att_status,
                delete_sp1_resp,
                delete_sp2_resp,
            ]

        if "test_dcnm_sp_delete_existing_detach_unauth_err" == self._testMethodName:

            have_sp1_resp = self.payloads_data.get("get_sp1_resp")
            have_sp2_resp = self.payloads_data.get("get_sp2_resp")
            have_sp3_resp = self.payloads_data.get("get_sp3_resp")
            det_sp1_resp = self.payloads_data.get("detach_sp1_resp")
            det_sp2_sp3_resp = self.payloads_data.get("detach_sp2_sp3_resp")
            delete_sp1_resp = self.payloads_data.get("delete_sp1_resp")
            delete_sp2_resp = self.payloads_data.get("delete_sp2_resp")
            delete_sp3_resp = self.payloads_data.get("delete_sp3_resp")
            deploy_sp1_resp = self.payloads_data.get("deploy_sp1_resp")
            deploy_sp2_sp3_resp = self.payloads_data.get("deploy_sp2_sp3_resp")
            resp_unauth_err = self.payloads_data.get("resp_unauth_err")
            get_dd_sn1_att_status = self.payloads_data.get("get_dd_sn1_att_status")
            get_dd_sn2_att_status = self.payloads_data.get("get_dd_sn2_att_status")

            self.run_dcnm_send.side_effect = [
                have_sp1_resp,
                have_sp2_resp,
                have_sp3_resp,
                resp_unauth_err,
                det_sp1_resp,
                det_sp2_sp3_resp,
                deploy_sp1_resp,
                deploy_sp2_sp3_resp,
                get_dd_sn1_att_status,
                get_dd_sn2_att_status,
                get_dd_sn2_att_status,
                delete_sp1_resp,
                delete_sp2_resp,
                delete_sp3_resp,
            ]

        if (
            "test_dcnm_sp_delete_existing_delete_deploy_unauth_err"
            == self._testMethodName
        ):

            have_sp1_resp = self.payloads_data.get("get_sp1_resp")
            have_sp2_resp = self.payloads_data.get("get_sp2_resp")
            have_sp3_resp = self.payloads_data.get("get_sp3_resp")
            det_sp1_resp = self.payloads_data.get("detach_sp1_resp")
            det_sp2_sp3_resp = self.payloads_data.get("detach_sp2_sp3_resp")
            delete_sp1_resp = self.payloads_data.get("delete_sp1_resp")
            delete_sp2_resp = self.payloads_data.get("delete_sp2_resp")
            delete_sp3_resp = self.payloads_data.get("delete_sp3_resp")
            deploy_sp1_resp = self.payloads_data.get("deploy_sp1_resp")
            deploy_sp2_sp3_resp = self.payloads_data.get("deploy_sp2_sp3_resp")
            get_dd_sn1_att_status = self.payloads_data.get("get_dd_sn1_att_status")
            get_dd_sn2_att_status = self.payloads_data.get("get_dd_sn2_att_status")
            resp_unauth_err = self.payloads_data.get("resp_unauth_err")

            self.run_dcnm_send.side_effect = [
                have_sp1_resp,
                have_sp2_resp,
                have_sp3_resp,
                det_sp1_resp,
                det_sp2_sp3_resp,
                resp_unauth_err,
                deploy_sp1_resp,
                deploy_sp2_sp3_resp,
                get_dd_sn1_att_status,
                get_dd_sn2_att_status,
                get_dd_sn2_att_status,
                delete_sp1_resp,
                delete_sp2_resp,
                delete_sp3_resp,
            ]

        if "test_dcnm_sp_delete_existing_delete_unauth_err" == self._testMethodName:

            have_sp1_resp = self.payloads_data.get("get_sp1_resp")
            have_sp2_resp = self.payloads_data.get("get_sp2_resp")
            have_sp3_resp = self.payloads_data.get("get_sp3_resp")
            det_sp1_resp = self.payloads_data.get("detach_sp1_resp")
            det_sp2_sp3_resp = self.payloads_data.get("detach_sp2_sp3_resp")
            delete_sp1_resp = self.payloads_data.get("delete_sp1_resp")
            delete_sp2_resp = self.payloads_data.get("delete_sp2_resp")
            delete_sp3_resp = self.payloads_data.get("delete_sp3_resp")
            deploy_sp1_resp = self.payloads_data.get("deploy_sp1_resp")
            deploy_sp2_sp3_resp = self.payloads_data.get("deploy_sp2_sp3_resp")
            resp_unauth_err = self.payloads_data.get("resp_unauth_err")
            get_dd_sn1_att_status = self.payloads_data.get("get_dd_sn1_att_status")
            get_dd_sn2_att_status = self.payloads_data.get("get_dd_sn2_att_status")

            self.run_dcnm_send.side_effect = [
                have_sp1_resp,
                have_sp2_resp,
                have_sp3_resp,
                det_sp1_resp,
                det_sp2_sp3_resp,
                deploy_sp1_resp,
                deploy_sp2_sp3_resp,
                get_dd_sn1_att_status,
                get_dd_sn2_att_status,
                get_dd_sn2_att_status,
                resp_unauth_err,
                delete_sp1_resp,
                delete_sp2_resp,
                delete_sp3_resp,
            ]

        if "test_dcnm_sp_delete_existing_and_non_existing" == self._testMethodName:

            have_sp1_resp = []
            have_sp2_resp = self.payloads_data.get("get_sp2_resp")
            have_sp3_resp = self.payloads_data.get("get_sp3_resp")
            det_sp2_sp3_resp = self.payloads_data.get("detach_sp2_sp3_resp")
            delete_sp2_resp = self.payloads_data.get("delete_sp2_resp")
            delete_sp3_resp = self.payloads_data.get("delete_sp3_resp")
            deploy_sp2_sp3_resp = self.payloads_data.get("deploy_sp2_sp3_resp")
            get_dd_sn2_att_status = self.payloads_data.get("get_dd_sn2_att_status")

            self.run_dcnm_send.side_effect = [
                have_sp1_resp,
                have_sp2_resp,
                have_sp3_resp,
                det_sp2_sp3_resp,
                deploy_sp2_sp3_resp,
                get_dd_sn2_att_status,
                get_dd_sn2_att_status,
                delete_sp2_resp,
                delete_sp3_resp,
            ]

        if "test_dcnm_sp_delete_non_existing" == self._testMethodName:

            self.run_dcnm_send.side_effect = [[], [], [], [], [], [], []]

        if "test_dcnm_sp_replace_sp1_to_sp3_non_existing" == self._testMethodName:

            have_sp1_resp = []
            have_sp2_resp = []
            have_sp3_resp = []
            get_sp1_resp = self.payloads_data.get("get_sp1_resp")
            get_snt_resp1 = self.payloads_data.get("get_snt1_response")
            get_snt_resp2 = self.payloads_data.get("get_snt2_response")
            get_snt_resp3 = self.payloads_data.get("get_snt2_response")
            create_sp1_resp = self.payloads_data.get("create_sp1_resp")
            create_sp2_resp = self.payloads_data.get("create_sp2_resp")
            create_sp3_resp = self.payloads_data.get("create_sp3_resp")
            deploy_sp1_resp = self.payloads_data.get("deploy_sp1_resp")
            deploy_sp2_sp3_resp = self.payloads_data.get("deploy_sp2_sp3_resp")
            resp_unauth_err = self.payloads_data.get("resp_unauth_err")
            get_sn1_att_status = self.payloads_data.get("get_sn1_att_status")
            get_sn2_att_status = self.payloads_data.get("get_sn2_att_status")

            self.run_dcnm_send.side_effect = [
                get_snt_resp1,
                get_snt_resp2,
                get_snt_resp3,
                have_sp1_resp,
                have_sp2_resp,
                have_sp3_resp,
                resp_unauth_err,
                get_sp1_resp,
                create_sp1_resp,
                create_sp2_resp,
                create_sp3_resp,
                resp_unauth_err,
                deploy_sp1_resp,
                deploy_sp2_sp3_resp,
                get_sn1_att_status,
                get_sn2_att_status,
                get_sn2_att_status,
            ]

        if "test_dcnm_sp_replace_sp1_to_sp3_existing" == self._testMethodName:

            have_sp1_resp = self.payloads_data.get("get_sp1_resp")
            have_sp2_resp = self.payloads_data.get("get_sp2_resp")
            have_sp3_resp = self.payloads_data.get("get_sp3_resp")
            get_snt_resp1 = self.payloads_data.get("get_snt1_response")
            get_snt_resp2 = self.payloads_data.get("get_snt2_response")
            get_snt_resp3 = self.payloads_data.get("get_snt2_response")
            get_sn1_att_status = self.payloads_data.get("get_sn1_att_status")
            get_sn2_att_status = self.payloads_data.get("get_sn2_att_status")
            create_sp1_resp = self.payloads_data.get("create_sp1_resp")
            create_sp2_resp = self.payloads_data.get("create_sp2_resp")
            create_sp3_resp = self.payloads_data.get("create_sp3_resp")
            deploy_sp1_resp = self.payloads_data.get("deploy_sp1_resp")
            deploy_sp2_sp3_resp = self.payloads_data.get("deploy_sp2_sp3_resp")
            get_sn1_att_status = self.payloads_data.get("get_sn1_att_status")
            get_sn2_att_status = self.payloads_data.get("get_sn2_att_status")

            self.run_dcnm_send.side_effect = [
                get_snt_resp1,
                get_snt_resp2,
                get_snt_resp3,
                have_sp1_resp,
                have_sp2_resp,
                have_sp3_resp,
                get_sn1_att_status,
                get_sn2_att_status,
                create_sp1_resp,
                create_sp2_resp,
                create_sp3_resp,
                deploy_sp1_resp,
                deploy_sp2_sp3_resp,
                get_sn1_att_status,
                get_sn2_att_status,
                get_sn2_att_status,
            ]

        if "test_dcnm_sp_replace_sp1_to_sp3_existing_no_change" == self._testMethodName:

            have_sp1_resp = self.payloads_data.get("get_sp1_resp")
            have_sp2_resp = self.payloads_data.get("get_sp2_resp")
            have_sp3_resp = self.payloads_data.get("get_sp3_resp")
            get_sn1_att_status = self.payloads_data.get("get_sn1_att_status")
            get_sn2_att_status = self.payloads_data.get("get_sn2_att_status")
            get_snt_resp1 = self.payloads_data.get("get_snt1_response")
            get_snt_resp2 = self.payloads_data.get("get_snt2_response")
            get_snt_resp3 = self.payloads_data.get("get_snt2_response")

            self.run_dcnm_send.side_effect = [
                get_snt_resp1,
                get_snt_resp2,
                get_snt_resp3,
                have_sp1_resp,
                have_sp2_resp,
                have_sp3_resp,
                get_sn1_att_status,
                get_sn2_att_status,
            ]

        if "test_dcnm_sp_override_with_new_peerings" == self._testMethodName:

            have_sp1_resp = []
            get_snodes_resp = self.payloads_data.get("get_service_nodes_resp")
            get_policy_with_sn1 = self.payloads_data.get("get_policy_with_sn1")
            get_policy_with_sn2 = self.payloads_data.get("get_policy_with_sn2")
            get_snt_resp1 = self.payloads_data.get("get_snt1_response")
            create_sp1_resp = self.payloads_data.get("create_sp1_resp")
            det_sp2_sp3_resp = self.payloads_data.get("detach_sp2_sp3_resp")
            delete_sp2_resp = self.payloads_data.get("delete_sp2_resp")
            delete_sp3_resp = self.payloads_data.get("delete_sp3_resp")
            deploy_sp1_resp = self.payloads_data.get("deploy_sp1_resp")
            deploy_sp2_sp3_resp = self.payloads_data.get("deploy_sp2_sp3_resp")
            get_sn1_att_status = self.payloads_data.get("get_sn1_att_status")
            get_sn2_att_status = self.payloads_data.get("get_sn2_att_status")
            get_dd_sn1_att_status = self.payloads_data.get("get_dd_sn1_att_status")
            get_dd_sn2_att_status = self.payloads_data.get("get_dd_sn2_att_status")

            self.run_dcnm_send.side_effect = [
                get_snt_resp1,
                have_sp1_resp,
                get_snodes_resp,
                get_policy_with_sn1,
                get_policy_with_sn2,
                create_sp1_resp,
                det_sp2_sp3_resp,
                deploy_sp2_sp3_resp,
                get_dd_sn2_att_status,
                get_dd_sn2_att_status,
                delete_sp2_resp,
                delete_sp3_resp,
                deploy_sp1_resp,
                get_sn1_att_status,
            ]

        if "test_dcnm_sp_override_with_existing_peering" == self._testMethodName:

            get_sn1_att_status = self.payloads_data.get("get_sn1_att_status")
            get_sn2_att_status = self.payloads_data.get("get_sn2_att_status")
            have_sp1_resp = self.payloads_data.get("get_sp1_resp")
            get_sn1_att_status = self.payloads_data.get("get_sn1_att_status")
            get_snodes_resp = self.payloads_data.get("get_service_nodes_resp")
            get_policy_with_sn1 = self.payloads_data.get("get_policy_with_sn1")
            get_policy_with_sn2 = self.payloads_data.get("get_policy_with_sn2")
            get_snt_resp1 = self.payloads_data.get("get_snt1_response")
            det_sp2_sp3_resp = self.payloads_data.get("detach_sp2_sp3_resp")
            delete_sp2_resp = self.payloads_data.get("delete_sp2_resp")
            delete_sp3_resp = self.payloads_data.get("delete_sp3_resp")
            deploy_sp2_sp3_resp = self.payloads_data.get("deploy_sp2_sp3_resp")
            get_dd_sn1_att_status = self.payloads_data.get("get_dd_sn1_att_status")
            get_dd_sn2_att_status = self.payloads_data.get("get_dd_sn2_att_status")

            self.run_dcnm_send.side_effect = [
                get_snt_resp1,
                have_sp1_resp,
                get_snodes_resp,
                get_policy_with_sn1,
                get_policy_with_sn2,
                get_sn1_att_status,
                det_sp2_sp3_resp,
                deploy_sp2_sp3_resp,
                get_dd_sn2_att_status,
                get_dd_sn2_att_status,
                delete_sp2_resp,
                delete_sp3_resp,
            ]

        if (
            "test_dcnm_sp_override_with_existing_peering_updated"
            == self._testMethodName
        ):

            have_sp1_resp = self.payloads_data.get("get_sp1_resp")
            get_snodes_resp = self.payloads_data.get("get_service_nodes_resp")
            get_policy_with_sn1 = self.payloads_data.get("get_policy_with_sn1")
            get_policy_with_sn2 = self.payloads_data.get("get_policy_with_sn2")
            get_snt_resp1 = self.payloads_data.get("get_snt1_response")
            get_sn1_att_status = self.payloads_data.get("get_sn1_att_status")
            create_sp1_resp = self.payloads_data.get("create_sp1_resp")
            det_sp2_sp3_resp = self.payloads_data.get("detach_sp2_sp3_resp")
            deploy_sp1_resp = self.payloads_data.get("deploy_sp1_resp")
            deploy_sp2_sp3_resp = self.payloads_data.get("deploy_sp2_sp3_resp")
            delete_sp2_resp = self.payloads_data.get("delete_sp2_resp")
            delete_sp3_resp = self.payloads_data.get("delete_sp3_resp")
            get_sn1_att_status = self.payloads_data.get("get_sn1_att_status")
            get_sn2_att_status = self.payloads_data.get("get_sn2_att_status")
            get_dd_sn1_att_status = self.payloads_data.get("get_dd_sn1_att_status")
            get_dd_sn2_att_status = self.payloads_data.get("get_dd_sn2_att_status")

            self.run_dcnm_send.side_effect = [
                get_snt_resp1,
                have_sp1_resp,
                get_snodes_resp,
                get_policy_with_sn1,
                get_policy_with_sn2,
                get_sn1_att_status,
                create_sp1_resp,
                det_sp2_sp3_resp,
                deploy_sp2_sp3_resp,
                get_dd_sn2_att_status,
                get_dd_sn2_att_status,
                delete_sp2_resp,
                delete_sp3_resp,
                deploy_sp1_resp,
                get_sn1_att_status,
            ]

        if "test_dcnm_sp_override_with_no_config" == self._testMethodName:

            get_snodes_resp = self.payloads_data.get("get_service_nodes_resp")
            get_policy_with_sn1 = self.payloads_data.get("get_policy_with_sn1")
            get_policy_with_sn2 = self.payloads_data.get("get_policy_with_sn2")
            det_sp1_resp = self.payloads_data.get("detach_sp1_resp")
            det_sp2_sp3_resp = self.payloads_data.get("detach_sp2_sp3_resp")
            deploy_sp1_resp = self.payloads_data.get("deploy_sp1_resp")
            deploy_sp2_sp3_resp = self.payloads_data.get("deploy_sp2_sp3_resp")
            delete_sp1_resp = self.payloads_data.get("delete_sp1_resp")
            delete_sp2_resp = self.payloads_data.get("delete_sp2_resp")
            delete_sp3_resp = self.payloads_data.get("delete_sp3_resp")
            get_dd_sn1_att_status = self.payloads_data.get("get_dd_sn1_att_status")
            get_dd_sn2_att_status = self.payloads_data.get("get_dd_sn2_att_status")

            self.run_dcnm_send.side_effect = [
                get_snodes_resp,
                get_policy_with_sn1,
                get_policy_with_sn2,
                det_sp1_resp,
                det_sp2_sp3_resp,
                deploy_sp1_resp,
                deploy_sp2_sp3_resp,
                get_dd_sn1_att_status,
                get_dd_sn2_att_status,
                get_dd_sn2_att_status,
                delete_sp1_resp,
                delete_sp2_resp,
                delete_sp3_resp,
            ]

        if "test_dcnm_sp_query_non_existing" == self._testMethodName:

            self.run_dcnm_send.side_effect = [[], [], []]

        if "test_dcnm_sp_query_with_service_node1" == self._testMethodName:

            get_policy_with_sn1 = self.payloads_data.get("get_policy_with_sn1")

            self.run_dcnm_send.side_effect = [
                get_policy_with_sn1,
            ]

        if "test_dcnm_sp_query_with_service_node2" == self._testMethodName:

            get_policy_with_sn2 = self.payloads_data.get("get_policy_with_sn2")

            self.run_dcnm_send.side_effect = [
                get_policy_with_sn2,
            ]

        if "test_dcnm_sp_query_existing_with_node_and_policy" == self._testMethodName:

            have_sp1_resp = self.payloads_data.get("get_sp1_resp")
            have_sp2_resp = self.payloads_data.get("get_sp2_resp")
            have_sp3_resp = self.payloads_data.get("get_sp3_resp")

            self.run_dcnm_send.side_effect = [
                have_sp1_resp,
                have_sp2_resp,
                have_sp3_resp,
            ]

    def load_fixtures(self, response=None, device=""):

        self.run_dcnm_version_supported.side_effect = [11]
        # Load service policy related side-effects
        self.load_sp_fixtures()

    # -------------------------- FIXTURES END --------------------------
    # -------------------------- TEST-CASES ----------------------------

    def test_dcnm_sp_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_sp1_sp3_config")

        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 3)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_merged_new_no_opt_elems(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_sp1_sp2_no_opt_elems")

        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 2)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 2)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_merged_new_unauth_error(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_sp1_sp2_no_opt_elems")

        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 2)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 2)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_merged_existing_no_opt_elems(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_sp1_sp2_no_opt_elems")

        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 2)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 2)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_merged_new_check_mode(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_sp1_sp3_config")

        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                _ansible_check_mode=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 3)

    def test_dcnm_sp_config_without_state(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_sp1_sp3_config")

        set_module_args(
            dict(
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 3)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_merge_no_deploy(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_sp1_sp3_config")

        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 3)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_merge_deploy_false(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_sp1_sp3_config")

        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=False,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_wrong_state(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_sp1_sp7_config")

        set_module_args(
            dict(
                state="wrong_state",
                attach=True,
                deploy=False,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = None
        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception:
            self.assertEqual(result, None)

    def test_dcnm_sp_merge_no_mand_elems(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_policy_no_mand_elems")

        # No dest_port
        cfg = copy.deepcopy(self.playbook_config)
        cfg[0]["policy"].pop("dest_port")
        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=cfg,
            )
        )
        result = None
        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            self.assertEqual(
                ("dest_port : Required parameter not found" in (str(e))), True
            )
            self.assertEqual(result, None)

        # No src_port
        cfg = copy.deepcopy(self.playbook_config)
        cfg[0]["policy"].pop("src_port")
        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=cfg,
            )
        )
        result = None
        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            self.assertEqual(
                ("src_port : Required parameter not found" in (str(e))), True
            )
            self.assertEqual(result, None)

        # No proto
        cfg = copy.deepcopy(self.playbook_config)
        cfg[0]["policy"].pop("proto")
        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=cfg,
            )
        )
        result = None
        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            self.assertEqual(("proto : Required parameter not found" in (str(e))), True)
            self.assertEqual(result, None)

        # No next hop
        cfg = copy.deepcopy(self.playbook_config)
        cfg[0].pop("next_hop")
        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=cfg,
            )
        )
        result = None
        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            self.assertEqual(
                ("next_hop : Required parameter not found" in (str(e))), True
            )
            self.assertEqual(result, None)

        # No dest_network
        cfg = copy.deepcopy(self.playbook_config)
        cfg[0].pop("dest_network")
        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=cfg,
            )
        )
        result = None
        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            self.assertEqual(
                ("dest_network : Required parameter not found" in (str(e))), True
            )
            self.assertEqual(result, None)

        # No src_network
        cfg = copy.deepcopy(self.playbook_config)
        cfg[0].pop("src_network")
        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=cfg,
            )
        )
        result = None
        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            self.assertEqual(
                ("src_network : Required parameter not found" in (str(e))), True
            )
            self.assertEqual(result, None)

        # No dst_vrf
        cfg = copy.deepcopy(self.playbook_config)
        cfg[0].pop("dest_vrf")
        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=cfg,
            )
        )
        result = None
        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            self.assertEqual(
                ("dest_vrf : Required parameter not found" in (str(e))), True
            )
            self.assertEqual(result, None)

        # No src_vrf
        cfg = copy.deepcopy(self.playbook_config)
        cfg[0].pop("src_vrf")
        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=cfg,
            )
        )
        result = None
        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            self.assertEqual(
                ("src_vrf : Required parameter not found" in (str(e))), True
            )
            self.assertEqual(result, None)

        # No RP name
        cfg = copy.deepcopy(self.playbook_config)
        cfg[0].pop("rp_name")
        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=cfg,
            )
        )
        result = None
        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            self.assertEqual(
                ("rp_name : Required parameter not found" in (str(e))), True
            )
            self.assertEqual(result, None)

        # No policy name
        cfg = copy.deepcopy(self.playbook_config)
        cfg[0].pop("name")
        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=cfg,
            )
        )
        result = None
        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            self.assertEqual(("name : Required parameter not found" in (str(e))), True)
            self.assertEqual(result, None)

        # No node name object
        cfg = copy.deepcopy(self.playbook_config)
        cfg[0].pop("node_name")
        set_module_args(
            dict(
                state="deleted",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=cfg,
            )
        )
        result = None
        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            self.assertEqual(
                ("node_name : Required parameter not found" in (str(e))), True
            )
            self.assertEqual(result, None)

    def test_dcnm_sp_merged_existing_and_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_sp1_sp3_config")

        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 2)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 2)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_delete_existing_no_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("delete_policies_no_config")

        set_module_args(
            dict(
                state="deleted",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 3)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_delete_existing_with_node_names(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("delete_policies_with_node_names")

        set_module_args(
            dict(
                state="deleted",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 3)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_delete_existing_with_node_name_and_policy_name(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "delete_policies_with_name_and_node_name"
        )

        set_module_args(
            dict(
                state="deleted",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 3)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_delete_existing_with_node_name_and_rp_name(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "delete_policies_with_node_name_and_rp_name"
        )

        set_module_args(
            dict(
                state="deleted",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 2)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_delete_existing_detach_unauth_err(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "delete_policies_with_name_and_node_name"
        )

        set_module_args(
            dict(
                state="deleted",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 3)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_delete_existing_delete_deploy_unauth_err(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "delete_policies_with_name_and_node_name"
        )

        set_module_args(
            dict(
                state="deleted",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 3)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_delete_existing_delete_unauth_err(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "delete_policies_with_name_and_node_name"
        )

        set_module_args(
            dict(
                state="deleted",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 3)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_delete_existing_and_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "delete_policies_with_name_and_node_name"
        )

        set_module_args(
            dict(
                state="deleted",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 2)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_delete_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "delete_policies_with_name_and_no_name"
        )

        set_module_args(
            dict(
                state="deleted",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_delete_no_mand_elems(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("delete_policies_no_mand_elems")

        set_module_args(
            dict(
                state="deleted",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = None
        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            self.assertEqual(
                ("node_name : Required parameter not found" in (str(e))), True
            )
            self.assertEqual(result, None)

    def test_dcnm_sp_replace_sp1_to_sp3_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("replace_sp1_sp3_config")

        set_module_args(
            dict(
                state="replaced",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 3)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_replace_sp1_to_sp3_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("replace_sp1_sp3_config")

        set_module_args(
            dict(
                state="replaced",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 3)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 3)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_replace_sp1_to_sp3_existing_no_change(self):

        pass
        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_sp1_sp3_config")

        set_module_args(
            dict(
                state="replaced",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_override_with_new_peerings(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("override_policies_create_new")

        set_module_args(
            dict(
                state="overridden",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["deleted"]), 2)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 1)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_override_with_existing_peering(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("override_policies_no_change")

        set_module_args(
            dict(
                state="overridden",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 2)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_override_with_existing_peering_updated(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("override_policies_modify_exist")

        set_module_args(
            dict(
                state="overridden",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 2)
        self.assertEqual(len(result["diff"][0]["modified"]), 1)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 1)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_override_with_no_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("override_policies_no_config")

        set_module_args(
            dict(
                state="overridden",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 3)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sp_query_existing_with_node_and_policy(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("query_with_node_and_policy_name")

        set_module_args(
            dict(
                state="query",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 3)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)
        self.assertEqual(len(result["response"]), 3)

    def test_dcnm_sp_query_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("query_non_existing")

        set_module_args(
            dict(
                state="query",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 3)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)
        self.assertEqual(len(result["response"]), 0)

    def test_dcnm_sp_query_with_service_node1(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("query_with_node_name_sn1")

        set_module_args(
            dict(
                state="query",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 1)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        self.assertEqual(len(result["response"]), 1)

    def test_dcnm_sp_query_with_service_node2(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("query_with_node_name_sn1")

        set_module_args(
            dict(
                state="query",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 1)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        self.assertEqual(len(result["response"]), 2)

    def test_dcnm_sp_query_no_mand_elems(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_service_policy_configs")
        self.payloads_data = loadPlaybookData("dcnm_service_policy_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("query_no_mand_elems")

        set_module_args(
            dict(
                state="query",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=self.playbook_config,
            )
        )
        result = None
        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            self.assertEqual(
                ("node_name : Required parameter not found" in (str(e))), True
            )
            self.assertEqual(result, None)
