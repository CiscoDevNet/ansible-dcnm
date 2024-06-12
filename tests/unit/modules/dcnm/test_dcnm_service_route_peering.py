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

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_service_route_peering
from .dcnm_module import TestDcnmModule, set_module_args, loadPlaybookData

import copy


class TestDcnmServiceRoutePeeringModule(TestDcnmModule):

    module = dcnm_service_route_peering
    fd = None

    def init_data(self):
        self.fd = None

    def log_msg(self, msg):

        if self.fd is None:
            self.fd = open("srp-ut.log", "w+")
        self.fd.write(msg)

    def setUp(self):

        super(TestDcnmServiceRoutePeeringModule, self).setUp()

        self.mock_dcnm_send = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_service_route_peering.dcnm_send"
        )
        self.run_dcnm_send = self.mock_dcnm_send.start()

        self.mock_dcnm_version_supported = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_service_route_peering.dcnm_version_supported"
        )
        self.run_dcnm_version_supported = self.mock_dcnm_version_supported.start()

        self.mock_dcnm_reset_connection = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_service_route_peering.dcnm_reset_connection"
        )
        self.run_dcnm_reset_connection = self.mock_dcnm_reset_connection.start()

    def tearDown(self):

        super(TestDcnmServiceRoutePeeringModule, self).tearDown()
        self.mock_dcnm_send.stop()
        self.mock_dcnm_version_supported.stop()
        self.mock_dcnm_reset_connection.stop()

    # -------------------------- FIXTURES --------------------------

    def load_srp_fixtures(self):

        if "test_dcnm_srp_merged_new" == self._testMethodName:

            have_rp1_resp = []
            have_rp2_resp = []
            have_rp3_resp = []
            have_rp4_resp = []
            have_rp5_resp = []
            have_rp6_resp = []
            have_rp7_resp = []
            create_rp1_resp = self.payloads_data.get("create_rp1_resp")
            create_rp2_resp = self.payloads_data.get("create_rp2_resp")
            create_rp3_resp = self.payloads_data.get("create_rp3_resp")
            create_rp4_resp = self.payloads_data.get("create_rp4_resp")
            create_rp5_resp = self.payloads_data.get("create_rp5_resp")
            create_rp6_resp = self.payloads_data.get("create_rp6_resp")
            create_rp7_resp = self.payloads_data.get("create_rp7_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            deploy_rp4_rp7_resp = self.payloads_data.get("deploy_rp4_rp7_resp")
            att_rp1_status = self.payloads_data.get("attach_rp1_resp")
            att_rp2_status = self.payloads_data.get("attach_rp2_resp")
            att_rp3_status = self.payloads_data.get("attach_rp3_resp")
            att_rp4_status = self.payloads_data.get("attach_rp4_resp")
            att_rp5_status = self.payloads_data.get("attach_rp5_resp")
            att_rp6_status = self.payloads_data.get("attach_rp6_resp")
            att_rp7_status = self.payloads_data.get("attach_rp7_resp")

            deploy_rp4_resp_unauth_err = self.payloads_data.get(
                "deploy_rp4_resp_unauth_err"
            )

            self.run_dcnm_send.side_effect = [
                have_rp1_resp,
                have_rp2_resp,
                have_rp3_resp,
                have_rp4_resp,
                have_rp5_resp,
                have_rp6_resp,
                have_rp7_resp,
                create_rp1_resp,
                create_rp2_resp,
                create_rp3_resp,
                create_rp4_resp,
                create_rp5_resp,
                create_rp6_resp,
                create_rp7_resp,
                deploy_rp1_rp3_resp,
                deploy_rp4_rp7_resp,
                att_rp1_status,
                att_rp2_status,
                att_rp3_status,
                att_rp4_status,
                att_rp5_status,
                att_rp6_status,
                att_rp7_status,
            ]

        if "test_dcnm_srp_merged_new_no_opt_elems" == self._testMethodName:

            have_rp1_resp = []
            have_rp2_resp = []
            have_rp3_resp = []
            have_rp4_resp = []
            have_rp5_resp = []
            have_rp6_resp = []
            have_rp7_resp = []
            vlan_id_alloc_resp1 = self.payloads_data.get("vlan_id_alloc_resp_rp1")
            vlan_id_alloc_resp2 = self.payloads_data.get("vlan_id_alloc_resp_rp2")
            vlan_id_alloc_resp3 = self.payloads_data.get("vlan_id_alloc_resp_rp3")
            vlan_id_alloc_resp4 = self.payloads_data.get("vlan_id_alloc_resp_rp4")
            vlan_id_alloc_resp5 = self.payloads_data.get("vlan_id_alloc_resp_rp5")
            vlan_id_alloc_resp6 = self.payloads_data.get("vlan_id_alloc_resp_rp6")
            vlan_id_alloc_resp7 = self.payloads_data.get("vlan_id_alloc_resp_rp7")
            create_rp1_resp = self.payloads_data.get("create_rp1_resp")
            create_rp2_resp = self.payloads_data.get("create_rp2_resp")
            create_rp3_resp = self.payloads_data.get("create_rp3_resp")
            create_rp4_resp = self.payloads_data.get("create_rp4_resp")
            create_rp5_resp = self.payloads_data.get("create_rp5_resp")
            create_rp6_resp = self.payloads_data.get("create_rp6_resp")
            create_rp7_resp = self.payloads_data.get("create_rp7_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            deploy_rp4_rp7_resp = self.payloads_data.get("deploy_rp4_rp7_resp")
            att_rp1_status = self.payloads_data.get("attach_rp1_resp")
            att_rp2_status = self.payloads_data.get("attach_rp2_resp")
            att_rp3_status = self.payloads_data.get("attach_rp3_resp")
            att_rp4_status = self.payloads_data.get("attach_rp4_resp")
            att_rp5_status = self.payloads_data.get("attach_rp5_resp")
            att_rp6_status = self.payloads_data.get("attach_rp6_resp")
            att_rp7_status = self.payloads_data.get("attach_rp7_resp")

            self.run_dcnm_send.side_effect = [
                have_rp1_resp,
                have_rp2_resp,
                have_rp3_resp,
                have_rp4_resp,
                have_rp5_resp,
                have_rp6_resp,
                have_rp7_resp,
                vlan_id_alloc_resp1,
                create_rp1_resp,
                vlan_id_alloc_resp2,
                create_rp2_resp,
                vlan_id_alloc_resp3,
                create_rp3_resp,
                vlan_id_alloc_resp4,
                create_rp4_resp,
                vlan_id_alloc_resp5,
                create_rp5_resp,
                vlan_id_alloc_resp6,
                create_rp6_resp,
                vlan_id_alloc_resp7,
                create_rp7_resp,
                deploy_rp1_rp3_resp,
                deploy_rp4_rp7_resp,
                att_rp1_status,
                att_rp2_status,
                att_rp3_status,
                att_rp4_status,
                att_rp5_status,
                att_rp6_status,
                att_rp7_status,
            ]

        if "test_dcnm_srp_merged_existing_no_opt_elems" == self._testMethodName:

            have_rp1_resp = self.payloads_data.get("have_rp1_resp")
            have_rp2_resp = self.payloads_data.get("have_rp2_resp")
            have_rp3_resp = self.payloads_data.get("have_rp3_resp")
            have_rp4_resp = self.payloads_data.get("have_rp4_resp")
            have_rp5_resp = self.payloads_data.get("have_rp5_resp")
            have_rp6_resp = self.payloads_data.get("have_rp6_resp")
            have_rp7_resp = self.payloads_data.get("have_rp7_resp")
            att_rp1_status = self.payloads_data.get("attach_rp1_resp")
            att_rp2_status = self.payloads_data.get("attach_rp2_resp")
            att_rp3_status = self.payloads_data.get("attach_rp3_resp")
            att_rp4_status = self.payloads_data.get("attach_rp4_resp")
            att_rp5_status = self.payloads_data.get("attach_rp5_resp")
            att_rp6_status = self.payloads_data.get("attach_rp6_resp")
            att_rp7_status = self.payloads_data.get("attach_rp7_resp")
            create_rp1_resp = self.payloads_data.get("create_rp1_resp")
            create_rp2_resp = self.payloads_data.get("create_rp2_resp")
            create_rp3_resp = self.payloads_data.get("create_rp3_resp")
            create_rp4_resp = self.payloads_data.get("create_rp4_resp")
            create_rp5_resp = self.payloads_data.get("create_rp5_resp")
            create_rp6_resp = self.payloads_data.get("create_rp6_resp")
            create_rp7_resp = self.payloads_data.get("create_rp7_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            deploy_rp4_rp7_resp = self.payloads_data.get("deploy_rp4_rp7_resp")

            self.run_dcnm_send.side_effect = [
                have_rp1_resp,
                have_rp2_resp,
                have_rp3_resp,
                have_rp4_resp,
                have_rp5_resp,
                have_rp6_resp,
                have_rp7_resp,
                att_rp1_status,
                att_rp2_status,
                att_rp3_status,
                att_rp4_status,
                att_rp5_status,
                att_rp6_status,
                att_rp7_status,
                create_rp1_resp,
                create_rp2_resp,
                create_rp3_resp,
                create_rp4_resp,
                create_rp5_resp,
                create_rp6_resp,
                create_rp7_resp,
                deploy_rp1_rp3_resp,
                deploy_rp4_rp7_resp,
                att_rp1_status,
                att_rp2_status,
                att_rp3_status,
                att_rp4_status,
                att_rp5_status,
                att_rp6_status,
                att_rp7_status,
            ]

        if "test_dcnm_srp_merged_new_check_mode" == self._testMethodName:

            have_rp1_resp = []
            have_rp2_resp = []
            have_rp3_resp = []
            have_rp4_resp = []
            have_rp5_resp = []
            have_rp6_resp = []
            have_rp7_resp = []

            self.run_dcnm_send.side_effect = [
                have_rp1_resp,
                have_rp2_resp,
                have_rp3_resp,
                have_rp4_resp,
                have_rp5_resp,
                have_rp6_resp,
                have_rp7_resp,
            ]

        if "test_dcnm_srp_merged_new_invalid_request_error" == self._testMethodName:

            have_rp1_resp = []
            have_rp2_resp = []
            have_rp3_resp = []
            have_rp4_resp = []
            have_rp5_resp = []
            have_rp6_resp = []
            have_rp7_resp = []
            create_rp1_resp = self.payloads_data.get("create_rp1_resp")
            create_rp2_resp = self.payloads_data.get("create_rp2_resp")
            create_rp3_resp = self.payloads_data.get("create_rp3_resp")
            create_rp4_resp = self.payloads_data.get("create_rp4_resp")
            create_rp5_resp = self.payloads_data.get("create_rp5_resp")
            create_rp6_resp = self.payloads_data.get("create_rp6_resp")
            create_rp7_resp = self.payloads_data.get("create_rp7_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            deploy_rp4_rp7_resp = self.payloads_data.get("deploy_rp4_rp7_resp")
            att_rp1_status = self.payloads_data.get("attach_rp1_resp")
            att_rp2_status = self.payloads_data.get("attach_rp2_resp")
            att_rp3_status = self.payloads_data.get("attach_rp3_resp")
            att_rp4_status = self.payloads_data.get("attach_rp4_resp")
            att_rp5_status = self.payloads_data.get("attach_rp5_resp")
            att_rp6_status = self.payloads_data.get("attach_rp6_resp")
            att_rp7_status = self.payloads_data.get("attach_rp7_resp")

            create_rp7_resp_inv_req_err = self.payloads_data.get(
                "create_rp7_resp_inv_req_err"
            )

            self.run_dcnm_send.side_effect = [
                have_rp1_resp,
                have_rp2_resp,
                have_rp3_resp,
                have_rp4_resp,
                have_rp5_resp,
                have_rp6_resp,
                have_rp7_resp,
                create_rp1_resp,
                create_rp2_resp,
                create_rp3_resp,
                create_rp4_resp,
                create_rp5_resp,
                create_rp6_resp,
                create_rp7_resp_inv_req_err,
                have_rp7_resp,
                create_rp7_resp,
                deploy_rp1_rp3_resp,
                deploy_rp4_rp7_resp,
                att_rp1_status,
                att_rp2_status,
                att_rp3_status,
                att_rp4_status,
                att_rp5_status,
                att_rp6_status,
                att_rp7_status,
            ]

        if "test_dcnm_srp_merged_new_invalid_fabric_error" == self._testMethodName:

            have_rp1_resp = []
            have_rp2_resp = []
            have_rp3_resp = []
            have_rp4_resp = []
            have_rp5_resp = []
            have_rp6_resp = []
            have_rp7_resp = []
            create_rp1_resp = self.payloads_data.get("create_rp1_resp")
            create_rp2_resp = self.payloads_data.get("create_rp2_resp")
            create_rp3_resp = self.payloads_data.get("create_rp3_resp")
            create_rp4_resp = self.payloads_data.get("create_rp4_resp")
            create_rp5_resp = self.payloads_data.get("create_rp5_resp")
            create_rp6_resp = self.payloads_data.get("create_rp6_resp")
            create_rp7_resp = self.payloads_data.get("create_rp7_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            deploy_rp4_rp7_resp = self.payloads_data.get("deploy_rp4_rp7_resp")
            att_rp1_status = self.payloads_data.get("attach_rp1_resp")
            att_rp2_status = self.payloads_data.get("attach_rp2_resp")
            att_rp3_status = self.payloads_data.get("attach_rp3_resp")
            att_rp4_status = self.payloads_data.get("attach_rp4_resp")
            att_rp5_status = self.payloads_data.get("attach_rp5_resp")
            att_rp6_status = self.payloads_data.get("attach_rp6_resp")
            att_rp7_status = self.payloads_data.get("attach_rp7_resp")

            create_rp7_resp_inv_fab_err = self.payloads_data.get(
                "create_rp7_resp_inv_fab_err"
            )

            self.run_dcnm_send.side_effect = [
                have_rp1_resp,
                have_rp2_resp,
                have_rp3_resp,
                have_rp4_resp,
                have_rp5_resp,
                have_rp6_resp,
                have_rp7_resp,
                create_rp1_resp,
                create_rp2_resp,
                create_rp3_resp,
                create_rp4_resp,
                create_rp5_resp,
                create_rp6_resp,
                create_rp7_resp_inv_fab_err,
                have_rp7_resp,
                create_rp7_resp,
                deploy_rp1_rp3_resp,
                deploy_rp4_rp7_resp,
                att_rp1_status,
                att_rp2_status,
                att_rp3_status,
                att_rp4_status,
                att_rp5_status,
                att_rp6_status,
                att_rp7_status,
            ]

        if "test_dcnm_srp_merged_new_unauth_error" == self._testMethodName:

            have_rp1_resp = []
            have_rp2_resp = []
            have_rp3_resp = []
            have_rp4_resp = []
            have_rp5_resp = []
            have_rp6_resp = []
            have_rp7_resp = []
            create_rp1_resp = self.payloads_data.get("create_rp1_resp")
            create_rp2_resp = self.payloads_data.get("create_rp2_resp")
            create_rp3_resp = self.payloads_data.get("create_rp3_resp")
            create_rp4_resp = self.payloads_data.get("create_rp4_resp")
            create_rp5_resp = self.payloads_data.get("create_rp5_resp")
            create_rp6_resp = self.payloads_data.get("create_rp6_resp")
            create_rp7_resp = self.payloads_data.get("create_rp7_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            deploy_rp4_rp7_resp = self.payloads_data.get("deploy_rp4_rp7_resp")
            att_rp1_status = self.payloads_data.get("attach_rp1_resp")
            att_rp2_status = self.payloads_data.get("attach_rp2_resp")
            att_rp3_status = self.payloads_data.get("attach_rp3_resp")
            att_rp4_status = self.payloads_data.get("attach_rp4_resp")
            att_rp5_status = self.payloads_data.get("attach_rp5_resp")
            att_rp6_status = self.payloads_data.get("attach_rp6_resp")
            att_rp7_status = self.payloads_data.get("attach_rp7_resp")

            create_rp7_resp_unauth_err = self.payloads_data.get(
                "create_rp7_resp_unauth_err"
            )

            self.run_dcnm_send.side_effect = [
                have_rp1_resp,
                have_rp2_resp,
                have_rp3_resp,
                have_rp4_resp,
                have_rp5_resp,
                have_rp6_resp,
                have_rp7_resp,
                create_rp1_resp,
                create_rp2_resp,
                create_rp3_resp,
                create_rp4_resp,
                create_rp5_resp,
                create_rp6_resp,
                create_rp7_resp_unauth_err,
                have_rp7_resp,
                create_rp7_resp,
                deploy_rp1_rp3_resp,
                deploy_rp4_rp7_resp,
                att_rp1_status,
                att_rp2_status,
                att_rp3_status,
                att_rp4_status,
                att_rp5_status,
                att_rp6_status,
                att_rp7_status,
            ]

        if "test_dcnm_srp_config_without_state" == self._testMethodName:

            have_rp1_resp = []
            have_rp2_resp = []
            have_rp3_resp = []
            have_rp4_resp = []
            have_rp5_resp = []
            have_rp6_resp = []
            have_rp7_resp = []
            create_rp1_resp = self.payloads_data.get("create_rp1_resp")
            create_rp2_resp = self.payloads_data.get("create_rp2_resp")
            create_rp3_resp = self.payloads_data.get("create_rp3_resp")
            create_rp4_resp = self.payloads_data.get("create_rp4_resp")
            create_rp5_resp = self.payloads_data.get("create_rp5_resp")
            create_rp6_resp = self.payloads_data.get("create_rp6_resp")
            create_rp7_resp = self.payloads_data.get("create_rp7_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            deploy_rp4_rp7_resp = self.payloads_data.get("deploy_rp4_rp7_resp")
            att_rp1_status = self.payloads_data.get("attach_rp1_resp")
            att_rp2_status = self.payloads_data.get("attach_rp2_resp")
            att_rp3_status = self.payloads_data.get("attach_rp3_resp")
            att_rp4_status = self.payloads_data.get("attach_rp4_resp")
            att_rp5_status = self.payloads_data.get("attach_rp5_resp")
            att_rp6_status = self.payloads_data.get("attach_rp6_resp")
            att_rp7_status = self.payloads_data.get("attach_rp7_resp")

            self.run_dcnm_send.side_effect = [
                have_rp1_resp,
                have_rp2_resp,
                have_rp3_resp,
                have_rp4_resp,
                have_rp5_resp,
                have_rp6_resp,
                have_rp7_resp,
                create_rp1_resp,
                create_rp2_resp,
                create_rp3_resp,
                create_rp4_resp,
                create_rp5_resp,
                create_rp6_resp,
                create_rp7_resp,
                deploy_rp1_rp3_resp,
                deploy_rp4_rp7_resp,
                att_rp1_status,
                att_rp2_status,
                att_rp3_status,
                att_rp4_status,
                att_rp5_status,
                att_rp6_status,
                att_rp7_status,
            ]

        if "test_dcnm_srp_merge_no_deploy" == self._testMethodName:

            have_rp1_resp = []
            have_rp2_resp = []
            have_rp3_resp = []
            have_rp4_resp = []
            have_rp5_resp = []
            have_rp6_resp = []
            have_rp7_resp = []
            create_rp1_resp = self.payloads_data.get("create_rp1_resp")
            create_rp2_resp = self.payloads_data.get("create_rp2_resp")
            create_rp3_resp = self.payloads_data.get("create_rp3_resp")
            create_rp4_resp = self.payloads_data.get("create_rp4_resp")
            create_rp5_resp = self.payloads_data.get("create_rp5_resp")
            create_rp6_resp = self.payloads_data.get("create_rp6_resp")
            create_rp7_resp = self.payloads_data.get("create_rp7_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            deploy_rp4_rp7_resp = self.payloads_data.get("deploy_rp4_rp7_resp")
            att_rp1_status = self.payloads_data.get("attach_rp1_resp")
            att_rp2_status = self.payloads_data.get("attach_rp2_resp")
            att_rp3_status = self.payloads_data.get("attach_rp3_resp")
            att_rp4_status = self.payloads_data.get("attach_rp4_resp")
            att_rp5_status = self.payloads_data.get("attach_rp5_resp")
            att_rp6_status = self.payloads_data.get("attach_rp6_resp")
            att_rp7_status = self.payloads_data.get("attach_rp7_resp")

            self.run_dcnm_send.side_effect = [
                have_rp1_resp,
                have_rp2_resp,
                have_rp3_resp,
                have_rp4_resp,
                have_rp5_resp,
                have_rp6_resp,
                have_rp7_resp,
                create_rp1_resp,
                create_rp2_resp,
                create_rp3_resp,
                create_rp4_resp,
                create_rp5_resp,
                create_rp6_resp,
                create_rp7_resp,
                deploy_rp1_rp3_resp,
                deploy_rp4_rp7_resp,
                att_rp1_status,
                att_rp2_status,
                att_rp3_status,
                att_rp4_status,
                att_rp5_status,
                att_rp6_status,
                att_rp7_status,
            ]

        if "test_dcnm_srp_merge_deploy_false" == self._testMethodName:

            have_rp1_resp = []
            have_rp2_resp = []
            have_rp3_resp = []
            have_rp4_resp = []
            have_rp5_resp = []
            have_rp6_resp = []
            have_rp7_resp = []
            create_rp1_resp = self.payloads_data.get("create_rp1_resp")
            create_rp2_resp = self.payloads_data.get("create_rp2_resp")
            create_rp3_resp = self.payloads_data.get("create_rp3_resp")
            create_rp4_resp = self.payloads_data.get("create_rp4_resp")
            create_rp5_resp = self.payloads_data.get("create_rp5_resp")
            create_rp6_resp = self.payloads_data.get("create_rp6_resp")
            create_rp7_resp = self.payloads_data.get("create_rp7_resp")

            self.run_dcnm_send.side_effect = [
                have_rp1_resp,
                have_rp2_resp,
                have_rp3_resp,
                have_rp4_resp,
                have_rp5_resp,
                have_rp6_resp,
                have_rp7_resp,
                create_rp1_resp,
                create_rp2_resp,
                create_rp3_resp,
                create_rp4_resp,
                create_rp5_resp,
                create_rp6_resp,
                create_rp7_resp,
            ]

        if "test_dcnm_srp_merged_existing" == self._testMethodName:

            have_rp1_resp = self.payloads_data.get("have_rp1_resp")
            have_rp2_resp = self.payloads_data.get("have_rp2_resp")
            have_rp3_resp = self.payloads_data.get("have_rp3_resp")
            have_rp4_resp = self.payloads_data.get("have_rp4_resp")
            have_rp5_resp = self.payloads_data.get("have_rp5_resp")
            have_rp6_resp = self.payloads_data.get("have_rp6_resp")
            have_rp7_resp = self.payloads_data.get("have_rp7_resp")
            att_rp1_status = self.payloads_data.get("attach_rp1_resp")
            att_rp2_status = self.payloads_data.get("attach_rp2_resp")
            att_rp3_status = self.payloads_data.get("attach_rp3_resp")
            att_rp4_status = self.payloads_data.get("attach_rp4_resp")
            att_rp5_status = self.payloads_data.get("attach_rp5_resp")
            att_rp6_status = self.payloads_data.get("attach_rp6_resp")
            att_rp7_status = self.payloads_data.get("attach_rp7_resp")

            self.run_dcnm_send.side_effect = [
                have_rp1_resp,
                have_rp2_resp,
                have_rp3_resp,
                have_rp4_resp,
                have_rp5_resp,
                have_rp6_resp,
                have_rp7_resp,
                att_rp1_status,
                att_rp2_status,
                att_rp3_status,
                att_rp4_status,
                att_rp5_status,
                att_rp6_status,
                att_rp7_status,
            ]

        if "test_dcnm_srp_merged_existing_and_non_existing" == self._testMethodName:

            have_rp1_resp = self.payloads_data.get("have_rp1_resp")
            have_rp3_resp = self.payloads_data.get("have_rp3_resp")
            have_rp5_resp = self.payloads_data.get("have_rp5_resp")
            att_rp1_status = self.payloads_data.get("attach_rp1_resp")
            att_rp3_status = self.payloads_data.get("attach_rp3_resp")
            att_rp5_status = self.payloads_data.get("attach_rp5_resp")
            create_rp2_resp = self.payloads_data.get("create_rp2_resp")
            create_rp4_resp = self.payloads_data.get("create_rp4_resp")
            create_rp6_resp = self.payloads_data.get("create_rp6_resp")
            create_rp7_resp = self.payloads_data.get("create_rp7_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            deploy_rp4_rp7_resp = self.payloads_data.get("deploy_rp4_rp7_resp")
            att_rp2_status = self.payloads_data.get("attach_rp2_resp")
            att_rp4_status = self.payloads_data.get("attach_rp4_resp")
            att_rp6_status = self.payloads_data.get("attach_rp6_resp")
            att_rp7_status = self.payloads_data.get("attach_rp7_resp")

            self.run_dcnm_send.side_effect = [
                have_rp1_resp,
                [],
                have_rp3_resp,
                [],
                have_rp5_resp,
                [],
                [],
                att_rp1_status,
                att_rp3_status,
                att_rp5_status,
                create_rp2_resp,
                create_rp4_resp,
                create_rp6_resp,
                create_rp7_resp,
                deploy_rp1_rp3_resp,
                deploy_rp4_rp7_resp,
                att_rp2_status,
                att_rp4_status,
                att_rp6_status,
                att_rp7_status,
            ]

        if "test_dcnm_srp_merged_update_existing" == self._testMethodName:

            have_rp2_resp = self.payloads_data.get("have_rp2_resp")
            have_rp4_resp = self.payloads_data.get("have_rp4_resp")
            att_rp2_status = self.payloads_data.get("attach_rp2_resp")
            att_rp4_status = self.payloads_data.get("attach_rp4_resp")
            create_rp2_resp = self.payloads_data.get("create_rp2_resp")
            create_rp4_resp = self.payloads_data.get("create_rp4_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            deploy_rp4_rp7_resp = self.payloads_data.get("deploy_rp4_rp7_resp")
            att_rp2_status = self.payloads_data.get("attach_rp2_resp")
            att_rp4_status = self.payloads_data.get("attach_rp4_resp")

            self.run_dcnm_send.side_effect = [
                have_rp2_resp,
                have_rp4_resp,
                att_rp2_status,
                att_rp4_status,
                create_rp2_resp,
                att_rp2_status,
                create_rp4_resp,
                att_rp4_status,
                deploy_rp1_rp3_resp,
                deploy_rp4_rp7_resp,
                att_rp2_status,
                att_rp4_status,
            ]

        if "test_dcnm_srp_merged_update_existing_unauth_err" == self._testMethodName:

            have_rp2_resp = self.payloads_data.get("have_rp2_resp")
            have_rp4_resp = self.payloads_data.get("have_rp4_resp")
            att_rp2_status = self.payloads_data.get("attach_rp2_resp")
            att_rp4_status = self.payloads_data.get("attach_rp4_resp")
            create_rp2_resp = self.payloads_data.get("create_rp2_resp")
            create_rp4_resp = self.payloads_data.get("create_rp4_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            deploy_rp4_rp7_resp = self.payloads_data.get("deploy_rp4_rp7_resp")
            att_rp2_status = self.payloads_data.get("attach_rp2_resp")
            att_rp4_status = self.payloads_data.get("attach_rp4_resp")

            create_rp4_resp_unauth_err = self.payloads_data.get(
                "create_rp4_resp_unauth_err"
            )

            self.run_dcnm_send.side_effect = [
                have_rp2_resp,
                have_rp4_resp,
                att_rp2_status,
                att_rp4_status,
                create_rp2_resp,
                att_rp2_status,
                create_rp4_resp_unauth_err,
                create_rp4_resp,
                att_rp4_status,
                deploy_rp1_rp3_resp,
                deploy_rp4_rp7_resp,
                att_rp2_status,
                att_rp4_status,
            ]

        if "test_dcnm_srp_delete_existing" == self._testMethodName:

            have_rp1_resp = self.payloads_data.get("have_rp1_resp")
            have_rp2_resp = self.payloads_data.get("have_rp2_resp")
            have_rp3_resp = self.payloads_data.get("have_rp3_resp")
            have_rp4_resp = self.payloads_data.get("have_rp4_resp")
            have_rp5_resp = self.payloads_data.get("have_rp5_resp")
            have_rp6_resp = self.payloads_data.get("have_rp6_resp")
            have_rp7_resp = self.payloads_data.get("have_rp7_resp")
            det_rp1_rp3_resp = self.payloads_data.get("detach_rp1_rp3_resp")
            det_rp4_rp7_resp = self.payloads_data.get("detach_rp4_rp7_resp")
            delete_rp1_resp = self.payloads_data.get("delete_rp1_resp")
            delete_rp2_resp = self.payloads_data.get("delete_rp2_resp")
            delete_rp3_resp = self.payloads_data.get("delete_rp3_resp")
            delete_rp4_resp = self.payloads_data.get("delete_rp4_resp")
            delete_rp5_resp = self.payloads_data.get("delete_rp5_resp")
            delete_rp6_resp = self.payloads_data.get("delete_rp6_resp")
            delete_rp7_resp = self.payloads_data.get("delete_rp7_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            deploy_rp4_rp7_resp = self.payloads_data.get("deploy_rp4_rp7_resp")
            dd_rp1_status = self.payloads_data.get("del_deploy_rp1_resp")
            dd_rp2_status = self.payloads_data.get("del_deploy_rp2_resp")
            dd_rp3_status = self.payloads_data.get("del_deploy_rp3_resp")
            dd_rp4_status = self.payloads_data.get("del_deploy_rp4_resp")
            dd_rp5_status = self.payloads_data.get("del_deploy_rp5_resp")
            dd_rp6_status = self.payloads_data.get("del_deploy_rp6_resp")
            dd_rp7_status = self.payloads_data.get("del_deploy_rp7_resp")

            self.run_dcnm_send.side_effect = [
                have_rp1_resp,
                have_rp2_resp,
                have_rp3_resp,
                have_rp4_resp,
                have_rp5_resp,
                have_rp6_resp,
                have_rp7_resp,
                det_rp1_rp3_resp,
                det_rp4_rp7_resp,
                deploy_rp1_rp3_resp,
                deploy_rp4_rp7_resp,
                dd_rp1_status,
                dd_rp2_status,
                dd_rp3_status,
                dd_rp4_status,
                dd_rp5_status,
                dd_rp6_status,
                dd_rp7_status,
                delete_rp1_resp,
                delete_rp2_resp,
                delete_rp3_resp,
                delete_rp4_resp,
                delete_rp5_resp,
                delete_rp6_resp,
                delete_rp7_resp,
            ]

        if "test_dcnm_srp_delete_existing_no_config" == self._testMethodName:

            serv_nodes_resp = self.payloads_data.get("serv_nodes_resp")
            have_it_sn1_resp = self.payloads_data.get("have_it_sn1_resp")
            have_it_sn2_resp = self.payloads_data.get("have_it_sn2_resp")
            det_rp1_rp3_resp = self.payloads_data.get("detach_rp1_rp3_resp")
            det_rp4_rp7_resp = self.payloads_data.get("detach_rp4_rp7_resp")
            delete_rp1_resp = self.payloads_data.get("delete_rp1_resp")
            delete_rp2_resp = self.payloads_data.get("delete_rp2_resp")
            delete_rp3_resp = self.payloads_data.get("delete_rp3_resp")
            delete_rp4_resp = self.payloads_data.get("delete_rp4_resp")
            delete_rp5_resp = self.payloads_data.get("delete_rp5_resp")
            delete_rp6_resp = self.payloads_data.get("delete_rp6_resp")
            delete_rp7_resp = self.payloads_data.get("delete_rp7_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            deploy_rp4_rp7_resp = self.payloads_data.get("deploy_rp4_rp7_resp")
            dd_rp1_status = self.payloads_data.get("del_deploy_rp1_resp")
            dd_rp2_status = self.payloads_data.get("del_deploy_rp2_resp")
            dd_rp3_status = self.payloads_data.get("del_deploy_rp3_resp")
            dd_rp4_status = self.payloads_data.get("del_deploy_rp4_resp")
            dd_rp5_status = self.payloads_data.get("del_deploy_rp5_resp")
            dd_rp6_status = self.payloads_data.get("del_deploy_rp6_resp")
            dd_rp7_status = self.payloads_data.get("del_deploy_rp7_resp")

            self.run_dcnm_send.side_effect = [
                serv_nodes_resp,
                have_it_sn1_resp,
                have_it_sn2_resp,
                det_rp1_rp3_resp,
                det_rp4_rp7_resp,
                deploy_rp1_rp3_resp,
                deploy_rp4_rp7_resp,
                dd_rp1_status,
                dd_rp2_status,
                dd_rp3_status,
                dd_rp4_status,
                dd_rp5_status,
                dd_rp6_status,
                dd_rp7_status,
                delete_rp1_resp,
                delete_rp2_resp,
                delete_rp3_resp,
                delete_rp4_resp,
                delete_rp5_resp,
                delete_rp6_resp,
                delete_rp7_resp,
            ]

        if "test_dcnm_srp_delete_existing_with_node_name" == self._testMethodName:

            have_it_sn1_resp = self.payloads_data.get("have_it_sn1_resp")
            have_it_sn2_resp = self.payloads_data.get("have_it_sn2_resp")
            det_rp1_rp3_resp = self.payloads_data.get("detach_rp1_rp3_resp")
            det_rp4_rp7_resp = self.payloads_data.get("detach_rp4_rp7_resp")
            delete_rp1_resp = self.payloads_data.get("delete_rp1_resp")
            delete_rp2_resp = self.payloads_data.get("delete_rp2_resp")
            delete_rp3_resp = self.payloads_data.get("delete_rp3_resp")
            delete_rp4_resp = self.payloads_data.get("delete_rp4_resp")
            delete_rp5_resp = self.payloads_data.get("delete_rp5_resp")
            delete_rp6_resp = self.payloads_data.get("delete_rp6_resp")
            delete_rp7_resp = self.payloads_data.get("delete_rp7_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            deploy_rp4_rp7_resp = self.payloads_data.get("deploy_rp4_rp7_resp")
            dd_rp1_status = self.payloads_data.get("del_deploy_rp1_resp")
            dd_rp2_status = self.payloads_data.get("del_deploy_rp2_resp")
            dd_rp3_status = self.payloads_data.get("del_deploy_rp3_resp")
            dd_rp4_status = self.payloads_data.get("del_deploy_rp4_resp")
            dd_rp5_status = self.payloads_data.get("del_deploy_rp5_resp")
            dd_rp6_status = self.payloads_data.get("del_deploy_rp6_resp")
            dd_rp7_status = self.payloads_data.get("del_deploy_rp7_resp")

            self.run_dcnm_send.side_effect = [
                have_it_sn1_resp,
                have_it_sn2_resp,
                det_rp1_rp3_resp,
                det_rp4_rp7_resp,
                deploy_rp1_rp3_resp,
                deploy_rp4_rp7_resp,
                dd_rp1_status,
                dd_rp2_status,
                dd_rp3_status,
                dd_rp4_status,
                dd_rp5_status,
                dd_rp6_status,
                dd_rp7_status,
                delete_rp1_resp,
                delete_rp2_resp,
                delete_rp3_resp,
                delete_rp4_resp,
                delete_rp5_resp,
                delete_rp6_resp,
                delete_rp7_resp,
            ]

        if "test_dcnm_srp_delete_existing_unauth_err" == self._testMethodName:

            have_rp1_resp = self.payloads_data.get("have_rp1_resp")
            have_rp2_resp = self.payloads_data.get("have_rp2_resp")
            have_rp3_resp = self.payloads_data.get("have_rp3_resp")
            have_rp4_resp = self.payloads_data.get("have_rp4_resp")
            have_rp5_resp = self.payloads_data.get("have_rp5_resp")
            have_rp6_resp = self.payloads_data.get("have_rp6_resp")
            have_rp7_resp = self.payloads_data.get("have_rp7_resp")
            det_rp1_rp3_resp = self.payloads_data.get("detach_rp1_rp3_resp")
            det_rp4_rp7_resp = self.payloads_data.get("detach_rp4_rp7_resp")
            delete_rp1_resp = self.payloads_data.get("delete_rp1_resp")
            delete_rp2_resp = self.payloads_data.get("delete_rp2_resp")
            delete_rp3_resp = self.payloads_data.get("delete_rp3_resp")
            delete_rp4_resp = self.payloads_data.get("delete_rp4_resp")
            delete_rp5_resp = self.payloads_data.get("delete_rp5_resp")
            delete_rp6_resp = self.payloads_data.get("delete_rp6_resp")
            delete_rp7_resp = self.payloads_data.get("delete_rp7_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            deploy_rp4_rp7_resp = self.payloads_data.get("deploy_rp4_rp7_resp")
            dd_rp1_status = self.payloads_data.get("del_deploy_rp1_resp")
            dd_rp2_status = self.payloads_data.get("del_deploy_rp2_resp")
            dd_rp3_status = self.payloads_data.get("del_deploy_rp3_resp")
            dd_rp4_status = self.payloads_data.get("del_deploy_rp4_resp")
            dd_rp5_status = self.payloads_data.get("del_deploy_rp5_resp")
            dd_rp6_status = self.payloads_data.get("del_deploy_rp6_resp")
            dd_rp7_status = self.payloads_data.get("del_deploy_rp7_resp")

            det_rp1_resp_unauth_err = self.payloads_data.get("det_rp1_resp_unauth_err")
            deploy_rp4_resp_unauth_err = self.payloads_data.get(
                "deploy_rp4_resp_unauth_err"
            )
            delete_rp7_resp_unauth_err = self.payloads_data.get(
                "delete_rp7_resp_unauth_err"
            )

            self.run_dcnm_send.side_effect = [
                have_rp1_resp,
                have_rp2_resp,
                have_rp3_resp,
                have_rp4_resp,
                have_rp5_resp,
                have_rp6_resp,
                have_rp7_resp,
                det_rp1_resp_unauth_err,
                det_rp1_rp3_resp,
                det_rp4_rp7_resp,
                deploy_rp1_rp3_resp,
                deploy_rp4_rp7_resp,
                dd_rp1_status,
                dd_rp2_status,
                dd_rp3_status,
                dd_rp4_status,
                dd_rp5_status,
                dd_rp6_status,
                dd_rp7_status,
                delete_rp1_resp,
                delete_rp2_resp,
                delete_rp3_resp,
                delete_rp4_resp,
                delete_rp5_resp,
                delete_rp6_resp,
                delete_rp7_resp_unauth_err,
                deploy_rp4_rp7_resp,
                delete_rp7_resp,
            ]

        if "test_dcnm_srp_delete_existing_and_non_existing" == self._testMethodName:

            have_rp1_resp = self.payloads_data.get("have_rp1_resp")
            have_rp3_resp = self.payloads_data.get("have_rp3_resp")
            have_rp6_resp = self.payloads_data.get("have_rp6_resp")
            have_rp7_resp = self.payloads_data.get("have_rp7_resp")
            det_rp1_rp3_resp = self.payloads_data.get("detach_rp1_rp3_resp")
            det_rp4_rp7_resp = self.payloads_data.get("detach_rp4_rp7_resp")
            delete_rp1_resp = self.payloads_data.get("delete_rp1_resp")
            delete_rp3_resp = self.payloads_data.get("delete_rp3_resp")
            delete_rp6_resp = self.payloads_data.get("delete_rp6_resp")
            delete_rp7_resp = self.payloads_data.get("delete_rp7_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            deploy_rp4_rp7_resp = self.payloads_data.get("deploy_rp4_rp7_resp")
            dd_rp1_status = self.payloads_data.get("del_deploy_rp1_resp")
            dd_rp3_status = self.payloads_data.get("del_deploy_rp3_resp")
            dd_rp6_status = self.payloads_data.get("del_deploy_rp6_resp")
            dd_rp7_status = self.payloads_data.get("del_deploy_rp7_resp")

            self.run_dcnm_send.side_effect = [
                have_rp1_resp,
                [],
                have_rp3_resp,
                [],
                [],
                have_rp6_resp,
                have_rp7_resp,
                det_rp1_rp3_resp,
                det_rp4_rp7_resp,
                deploy_rp1_rp3_resp,
                deploy_rp4_rp7_resp,
                dd_rp1_status,
                dd_rp3_status,
                dd_rp6_status,
                dd_rp7_status,
                delete_rp1_resp,
                delete_rp3_resp,
                delete_rp6_resp,
                delete_rp7_resp,
            ]

        if "test_dcnm_srp_delete_non_existing" == self._testMethodName:

            self.run_dcnm_send.side_effect = [[], [], [], [], [], [], []]

        if "test_dcnm_srp_replace_rp1_to_rp3_non_existing" == self._testMethodName:

            create_rp1_resp = self.payloads_data.get("create_rp1_resp")
            create_rp2_resp = self.payloads_data.get("create_rp2_resp")
            create_rp3_resp = self.payloads_data.get("create_rp3_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            att_rp1_status = self.payloads_data.get("attach_rp1_resp")
            att_rp2_status = self.payloads_data.get("attach_rp2_resp")
            att_rp3_status = self.payloads_data.get("attach_rp3_resp")

            self.run_dcnm_send.side_effect = [
                [],
                [],
                [],
                create_rp1_resp,
                create_rp2_resp,
                create_rp3_resp,
                deploy_rp1_rp3_resp,
                att_rp1_status,
                att_rp2_status,
                att_rp3_status,
            ]

        if "test_dcnm_srp_replace_rp1_to_rp3_existing" == self._testMethodName:

            have_rp1_resp = self.payloads_data.get("have_rp1_resp")
            have_rp2_resp = self.payloads_data.get("have_rp2_resp")
            have_rp3_resp = self.payloads_data.get("have_rp3_resp")
            att_rp1_status = self.payloads_data.get("attach_rp1_resp")
            att_rp2_status = self.payloads_data.get("attach_rp2_resp")
            att_rp3_status = self.payloads_data.get("attach_rp3_resp")
            create_rp1_resp = self.payloads_data.get("create_rp1_resp")
            create_rp2_resp = self.payloads_data.get("create_rp2_resp")
            create_rp3_resp = self.payloads_data.get("create_rp3_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            att_rp1_status = self.payloads_data.get("attach_rp1_resp")
            att_rp2_status = self.payloads_data.get("attach_rp2_resp")
            att_rp3_status = self.payloads_data.get("attach_rp3_resp")

            self.run_dcnm_send.side_effect = [
                have_rp1_resp,
                have_rp2_resp,
                have_rp3_resp,
                att_rp1_status,
                att_rp2_status,
                att_rp3_status,
                create_rp1_resp,
                att_rp1_status,
                create_rp2_resp,
                att_rp2_status,
                create_rp3_resp,
                att_rp3_status,
                deploy_rp1_rp3_resp,
                att_rp1_status,
                att_rp2_status,
                att_rp3_status,
            ]

        if (
            "test_dcnm_srp_replace_rp1_to_rp3_existing_no_change"
            == self._testMethodName
        ):

            have_rp1_resp = self.payloads_data.get("have_rp1_resp")
            have_rp2_resp = self.payloads_data.get("have_rp2_resp")
            have_rp3_resp = self.payloads_data.get("have_rp3_resp")
            att_rp1_status = self.payloads_data.get("attach_rp1_resp")
            att_rp2_status = self.payloads_data.get("attach_rp2_resp")
            att_rp3_status = self.payloads_data.get("attach_rp3_resp")

            self.run_dcnm_send.side_effect = [
                have_rp1_resp,
                have_rp2_resp,
                have_rp3_resp,
                att_rp1_status,
                att_rp2_status,
                att_rp3_status,
            ]

        if "test_dcnm_srp_override_rp1_rp7_with_new_peerings" == self._testMethodName:

            serv_nodes_resp = self.payloads_data.get("serv_nodes_resp")
            have_it_sn1_resp = self.payloads_data.get("have_it_sn1_resp")
            have_it_sn2_resp = self.payloads_data.get("have_it_sn2_resp")
            det_rp1_rp3_resp = self.payloads_data.get("detach_rp1_rp3_resp")
            det_rp4_rp7_resp = self.payloads_data.get("detach_rp4_rp7_resp")
            create_rp1_resp = self.payloads_data.get("create_rp1_resp")
            create_rp4_resp = self.payloads_data.get("create_rp4_resp")
            delete_rp1_resp = self.payloads_data.get("delete_rp1_resp")
            delete_rp2_resp = self.payloads_data.get("delete_rp2_resp")
            delete_rp3_resp = self.payloads_data.get("delete_rp3_resp")
            delete_rp4_resp = self.payloads_data.get("delete_rp4_resp")
            delete_rp5_resp = self.payloads_data.get("delete_rp5_resp")
            delete_rp6_resp = self.payloads_data.get("delete_rp6_resp")
            delete_rp7_resp = self.payloads_data.get("delete_rp7_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            deploy_rp4_rp7_resp = self.payloads_data.get("deploy_rp4_rp7_resp")
            dd_rp1_status = self.payloads_data.get("del_deploy_rp1_resp")
            dd_rp2_status = self.payloads_data.get("del_deploy_rp2_resp")
            dd_rp3_status = self.payloads_data.get("del_deploy_rp3_resp")
            dd_rp4_status = self.payloads_data.get("del_deploy_rp4_resp")
            dd_rp5_status = self.payloads_data.get("del_deploy_rp5_resp")
            dd_rp6_status = self.payloads_data.get("del_deploy_rp6_resp")
            dd_rp7_status = self.payloads_data.get("del_deploy_rp7_resp")
            deploy_rp_ovr1_resp = self.payloads_data.get("deploy_rp_ovr1_resp")
            deploy_rp_ovr4_resp = self.payloads_data.get("deploy_rp_ovr4_resp")
            att_rp1_status = self.payloads_data.get("attach_rp1_resp")
            att_rp4_status = self.payloads_data.get("attach_rp4_resp")

            self.run_dcnm_send.side_effect = [
                [],
                [],
                serv_nodes_resp,
                have_it_sn1_resp,
                have_it_sn2_resp,
                create_rp1_resp,
                create_rp4_resp,
                det_rp1_rp3_resp,
                det_rp4_rp7_resp,
                deploy_rp1_rp3_resp,
                deploy_rp4_rp7_resp,
                dd_rp1_status,
                dd_rp2_status,
                dd_rp3_status,
                dd_rp4_status,
                dd_rp5_status,
                dd_rp6_status,
                dd_rp7_status,
                delete_rp1_resp,
                delete_rp2_resp,
                delete_rp3_resp,
                delete_rp4_resp,
                delete_rp5_resp,
                delete_rp6_resp,
                delete_rp7_resp,
                deploy_rp_ovr1_resp,
                deploy_rp_ovr4_resp,
                att_rp1_status,
                att_rp4_status,
            ]

        if "test_dcnm_srp_override_with_existing_peering" == self._testMethodName:

            serv_nodes_resp = self.payloads_data.get("serv_nodes_resp")
            have_rp6_resp = self.payloads_data.get("have_rp6_resp")
            have_it_sn1_resp = self.payloads_data.get("have_it_sn1_resp")
            have_it_sn2_resp = self.payloads_data.get("have_it_sn2_resp")
            det_rp1_rp3_resp = self.payloads_data.get("detach_rp1_rp3_resp")
            det_rp4_rp7_resp = self.payloads_data.get("detach_rp4_rp7_resp")
            att_rp6_status = self.payloads_data.get("attach_rp6_resp")
            delete_rp1_resp = self.payloads_data.get("delete_rp1_resp")
            delete_rp2_resp = self.payloads_data.get("delete_rp2_resp")
            delete_rp3_resp = self.payloads_data.get("delete_rp3_resp")
            delete_rp4_resp = self.payloads_data.get("delete_rp4_resp")
            delete_rp5_resp = self.payloads_data.get("delete_rp5_resp")
            delete_rp7_resp = self.payloads_data.get("delete_rp7_resp")
            dd_rp1_status = self.payloads_data.get("del_deploy_rp1_resp")
            dd_rp2_status = self.payloads_data.get("del_deploy_rp2_resp")
            dd_rp3_status = self.payloads_data.get("del_deploy_rp3_resp")
            dd_rp4_status = self.payloads_data.get("del_deploy_rp4_resp")
            dd_rp5_status = self.payloads_data.get("del_deploy_rp5_resp")
            dd_rp7_status = self.payloads_data.get("del_deploy_rp7_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            deploy_rp4_rp7_resp = self.payloads_data.get("deploy_rp4_rp7_resp")

            self.run_dcnm_send.side_effect = [
                have_rp6_resp,
                serv_nodes_resp,
                have_it_sn1_resp,
                have_it_sn2_resp,
                att_rp6_status,
                det_rp1_rp3_resp,
                det_rp4_rp7_resp,
                deploy_rp1_rp3_resp,
                deploy_rp4_rp7_resp,
                dd_rp1_status,
                dd_rp2_status,
                dd_rp3_status,
                dd_rp4_status,
                dd_rp5_status,
                dd_rp7_status,
                delete_rp1_resp,
                delete_rp2_resp,
                delete_rp3_resp,
                delete_rp4_resp,
                delete_rp5_resp,
                delete_rp7_resp,
            ]

        if (
            "test_dcnm_srp_override_with_existing_peering_updated"
            == self._testMethodName
        ):

            serv_nodes_resp = self.payloads_data.get("serv_nodes_resp")
            have_rp6_resp = self.payloads_data.get("have_rp6_resp")
            have_it_sn1_resp = self.payloads_data.get("have_it_sn1_resp")
            have_it_sn2_resp = self.payloads_data.get("have_it_sn2_resp")
            create_rp6_resp = self.payloads_data.get("create_rp6_resp")
            att_rp6_status = self.payloads_data.get("attach_rp6_resp")
            det_rp1_rp3_resp = self.payloads_data.get("detach_rp1_rp3_resp")
            det_rp4_rp7_resp = self.payloads_data.get("detach_rp4_rp7_resp")
            delete_rp1_resp = self.payloads_data.get("delete_rp1_resp")
            delete_rp2_resp = self.payloads_data.get("delete_rp2_resp")
            delete_rp3_resp = self.payloads_data.get("delete_rp3_resp")
            delete_rp4_resp = self.payloads_data.get("delete_rp4_resp")
            delete_rp5_resp = self.payloads_data.get("delete_rp5_resp")
            delete_rp7_resp = self.payloads_data.get("delete_rp7_resp")
            dd_rp1_status = self.payloads_data.get("del_deploy_rp1_resp")
            dd_rp2_status = self.payloads_data.get("del_deploy_rp2_resp")
            dd_rp3_status = self.payloads_data.get("del_deploy_rp3_resp")
            dd_rp4_status = self.payloads_data.get("del_deploy_rp4_resp")
            dd_rp5_status = self.payloads_data.get("del_deploy_rp5_resp")
            dd_rp7_status = self.payloads_data.get("del_deploy_rp7_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            deploy_rp4_rp7_resp = self.payloads_data.get("deploy_rp4_rp7_resp")
            att_rp6_status = self.payloads_data.get("attach_rp6_resp")

            self.run_dcnm_send.side_effect = [
                have_rp6_resp,
                serv_nodes_resp,
                have_it_sn1_resp,
                have_it_sn2_resp,
                att_rp6_status,
                create_rp6_resp,
                att_rp6_status,
                det_rp1_rp3_resp,
                det_rp4_rp7_resp,
                deploy_rp1_rp3_resp,
                deploy_rp4_rp7_resp,
                dd_rp1_status,
                dd_rp2_status,
                dd_rp3_status,
                dd_rp4_status,
                dd_rp5_status,
                dd_rp7_status,
                delete_rp1_resp,
                delete_rp2_resp,
                delete_rp3_resp,
                delete_rp4_resp,
                delete_rp5_resp,
                delete_rp7_resp,
                deploy_rp4_rp7_resp,
                att_rp6_status,
            ]

        if "test_dcnm_srp_override_with_no_config" == self._testMethodName:

            serv_nodes_resp = self.payloads_data.get("serv_nodes_resp")
            have_it_sn1_resp = self.payloads_data.get("have_it_sn1_resp")
            have_it_sn2_resp = self.payloads_data.get("have_it_sn2_resp")
            det_rp1_rp3_resp = self.payloads_data.get("detach_rp1_rp3_resp")
            det_rp4_rp7_resp = self.payloads_data.get("detach_rp4_rp7_resp")
            delete_rp1_resp = self.payloads_data.get("delete_rp1_resp")
            delete_rp2_resp = self.payloads_data.get("delete_rp2_resp")
            delete_rp3_resp = self.payloads_data.get("delete_rp3_resp")
            delete_rp4_resp = self.payloads_data.get("delete_rp4_resp")
            delete_rp5_resp = self.payloads_data.get("delete_rp5_resp")
            delete_rp6_resp = self.payloads_data.get("delete_rp6_resp")
            delete_rp7_resp = self.payloads_data.get("delete_rp7_resp")
            dd_rp1_status = self.payloads_data.get("del_deploy_rp1_resp")
            dd_rp2_status = self.payloads_data.get("del_deploy_rp2_resp")
            dd_rp3_status = self.payloads_data.get("del_deploy_rp3_resp")
            dd_rp4_status = self.payloads_data.get("del_deploy_rp4_resp")
            dd_rp5_status = self.payloads_data.get("del_deploy_rp5_resp")
            dd_rp6_status = self.payloads_data.get("del_deploy_rp6_resp")
            dd_rp7_status = self.payloads_data.get("del_deploy_rp7_resp")
            deploy_rp1_rp3_resp = self.payloads_data.get("deploy_rp1_rp3_resp")
            deploy_rp4_rp7_resp = self.payloads_data.get("deploy_rp4_rp7_resp")

            self.run_dcnm_send.side_effect = [
                serv_nodes_resp,
                have_it_sn1_resp,
                have_it_sn2_resp,
                det_rp1_rp3_resp,
                det_rp4_rp7_resp,
                deploy_rp1_rp3_resp,
                deploy_rp4_rp7_resp,
                dd_rp1_status,
                dd_rp2_status,
                dd_rp3_status,
                dd_rp4_status,
                dd_rp5_status,
                dd_rp6_status,
                dd_rp7_status,
                delete_rp1_resp,
                delete_rp2_resp,
                delete_rp3_resp,
                delete_rp4_resp,
                delete_rp5_resp,
                delete_rp6_resp,
                delete_rp7_resp,
            ]

        if "test_dcnm_srp_query_non_existing" == self._testMethodName:

            self.run_dcnm_send.side_effect = [[], []]

        if "test_dcnm_srp_query_with_service_nodes" == self._testMethodName:

            have_it_sn1_resp = self.payloads_data.get("have_it_sn1_resp")
            have_it_sn2_resp = self.payloads_data.get("have_it_sn2_resp")

            self.run_dcnm_send.side_effect = [have_it_sn1_resp, have_it_sn2_resp]

        if "test_dcnm_srp_query_with_peer_names" == self._testMethodName:

            have_rp1_resp = self.payloads_data.get("have_rp1_resp")
            have_rp2_resp = self.payloads_data.get("have_rp2_resp")
            have_rp3_resp = self.payloads_data.get("have_rp3_resp")
            have_rp4_resp = self.payloads_data.get("have_rp4_resp")
            have_rp5_resp = self.payloads_data.get("have_rp5_resp")
            have_rp6_resp = self.payloads_data.get("have_rp6_resp")
            have_rp7_resp = self.payloads_data.get("have_rp7_resp")

            self.run_dcnm_send.side_effect = [
                have_rp1_resp,
                have_rp2_resp,
                have_rp3_resp,
                have_rp4_resp,
                have_rp5_resp,
                have_rp6_resp,
                have_rp7_resp,
            ]

    def load_fixtures(self, response=None, device=""):

        # Load srp related side-effects
        self.load_srp_fixtures()
        self.run_dcnm_version_supported.side_effect = [11]

    # -------------------------- FIXTURES END --------------------------
    # -------------------------- TEST-CASES --------------------------

    def test_dcnm_srp_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_rp1_rp7_config")

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

        self.assertEqual(len(result["diff"][0]["merged"]), 7)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 7)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_srp_merged_new_no_opt_elems(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "create_rp1_rp7_config_no_opt_elems"
        )

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

        self.assertEqual(len(result["diff"][0]["merged"]), 7)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 7)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_srp_merged_existing_no_opt_elems(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "create_rp1_rp7_config_no_opt_elems"
        )

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
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_srp_merged_new_no_intra_fw_mand_elems(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_no_intra_fw_mand_elems")

        # From here we will remove one mandatory element from the config and check if that
        # is detected and errored out

        # No Deploy Mode object
        cfg_no_dm = copy.deepcopy(self.playbook_config)
        cfg_no_dm[0].pop("deploy_mode")
        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=cfg_no_dm,
            )
        )
        result = None
        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            self.assertEqual(
                ("deploy_mode - Required parameter not found" in (str(e))), True
            )
            self.assertEqual(result, None)

        # No name object
        cfg_no_dm = copy.deepcopy(self.playbook_config)
        cfg_no_dm[0].pop("name")
        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=cfg_no_dm,
            )
        )
        result = None
        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            self.assertEqual(("name : Required parameter not found" in (str(e))), True)
            self.assertEqual(result, None)

        # No next_hop object
        cfg_no_dm = copy.deepcopy(self.playbook_config)
        cfg_no_dm[0].pop("next_hop")
        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=cfg_no_dm,
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

        # No node_name object
        cfg_no_dm = copy.deepcopy(self.playbook_config)
        cfg_no_dm[0].pop("node_name")
        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=cfg_no_dm,
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

        nets = ["inside_network", "outside_network"]

        for net in nets:
            # No Inside Name object
            cfg_no_dm = copy.deepcopy(self.playbook_config)
            cfg_no_dm[0][net].pop("name")
            set_module_args(
                dict(
                    state="merged",
                    attach=True,
                    deploy=True,
                    fabric="mmudigon",
                    service_fabric="external",
                    config=cfg_no_dm,
                )
            )
            result = None
            try:
                result = self.execute_module(changed=True, failed=False)
            except Exception as e:
                self.assertEqual(
                    ("name : Required parameter not found" in (str(e))), True
                )
                self.assertEqual(result, None)

            # No Inside Profile IPV4GW object
            cfg_no_dm = copy.deepcopy(self.playbook_config)
            cfg_no_dm[0][net]["profile"].pop("ipv4_gw")
            set_module_args(
                dict(
                    state="merged",
                    attach=True,
                    deploy=True,
                    fabric="mmudigon",
                    service_fabric="external",
                    config=cfg_no_dm,
                )
            )
            result = None
            try:
                result = self.execute_module(changed=True, failed=False)
            except Exception as e:
                self.assertEqual(
                    ("ipv4_gw : Required parameter not found" in (str(e))), True
                )
                self.assertEqual(result, None)

            # No Inside vrf object
            cfg_no_dm = copy.deepcopy(self.playbook_config)
            cfg_no_dm[0][net].pop("vrf")
            set_module_args(
                dict(
                    state="merged",
                    attach=True,
                    deploy=True,
                    fabric="mmudigon",
                    service_fabric="external",
                    config=cfg_no_dm,
                )
            )
            result = None
            try:
                result = self.execute_module(changed=True, failed=False)
            except Exception as e:
                self.assertEqual(
                    ("vrf : Required parameter not found" in (str(e))), True
                )
                self.assertEqual(result, None)

    def test_dcnm_srp_merged_new_no_inter_fw_mand_elems(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_no_inter_fw_mand_elems")

        # From here we will remove one mandatory element from the config and check if that
        # is detected and errored out

        nets = ["inside_network", "outside_network"]

        for net in nets:

            # No Inside ipv4_lo object
            cfg_no_dm = copy.deepcopy(self.playbook_config)
            cfg_no_dm[0][net]["profile"].pop("ipv4_lo")
            set_module_args(
                dict(
                    state="merged",
                    attach=True,
                    deploy=True,
                    fabric="mmudigon",
                    service_fabric="external",
                    config=cfg_no_dm,
                )
            )
            result = None
            try:
                result = self.execute_module(changed=True, failed=False)
            except Exception as e:
                self.assertEqual(
                    ("ipv4_lo : Required parameter not found" in (str(e))), True
                )
                self.assertEqual(result, None)

            # No Inside ipv4_neighbor object
            cfg_no_dm = copy.deepcopy(self.playbook_config)
            cfg_no_dm[0][net]["profile"].pop("ipv4_neighbor")
            set_module_args(
                dict(
                    state="merged",
                    attach=True,
                    deploy=True,
                    fabric="mmudigon",
                    service_fabric="external",
                    config=cfg_no_dm,
                )
            )
            result = None
            try:
                result = self.execute_module(changed=True, failed=False)
            except Exception as e:
                self.assertEqual(
                    ("ipv4_neighbor : Required parameter not found" in (str(e))), True
                )
                self.assertEqual(result, None)

    def test_dcnm_srp_merged_new_no_adc_mand_elems(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_no_adc_mand_elems")

        # From here we will remove one mandatory element from the config and check if that
        # is detected and errored out

        # No reverse_next_hop object
        cfg_no_dm = copy.deepcopy(self.playbook_config)
        cfg_no_dm[0].pop("reverse_next_hop")
        set_module_args(
            dict(
                state="merged",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=cfg_no_dm,
            )
        )
        result = None
        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            self.assertEqual(
                ("reverse_next_hop : Required parameter not found" in (str(e))), True
            )
            self.assertEqual(result, None)

    def test_dcnm_srp_merged_new_check_mode(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_rp1_rp7_config")

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

        self.assertEqual(len(result["diff"][0]["merged"]), 7)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 7)

    def test_dcnm_srp_merged_new_invalid_request_error(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_rp1_rp7_config")

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

        self.assertEqual(len(result["diff"][0]["merged"]), 7)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 7)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_srp_merged_new_invalid_fabric_error(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_rp1_rp7_config")

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

        self.assertEqual(len(result["diff"][0]["merged"]), 7)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 7)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_srp_merged_new_unauth_error(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_rp1_rp7_config")

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

        self.assertEqual(len(result["diff"][0]["merged"]), 7)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 7)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_srp_config_without_state(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_rp1_rp7_config")

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

        self.assertEqual(len(result["diff"][0]["merged"]), 7)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 7)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_srp_merge_no_deploy(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_rp1_rp7_config")

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

        self.assertEqual(len(result["diff"][0]["merged"]), 7)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 7)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_srp_merge_deploy_false(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_rp1_rp7_config")

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

        self.assertEqual(len(result["diff"][0]["merged"]), 7)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_srp_wrong_state(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_rp1_rp7_config")

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

    def test_dcnm_srp_merged_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_rp1_rp7_config")

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
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_srp_merged_existing_and_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("create_rp1_rp7_config")

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

        self.assertEqual(len(result["diff"][0]["merged"]), 4)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 4)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_srp_merged_update_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("update_rp2_rp4_config")

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

    def test_dcnm_srp_merged_update_existing_unauth_err(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("update_rp2_rp4_config")

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

    def test_dcnm_srp_delete_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("delete_rp1_rp7_config")

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
        self.assertEqual(len(result["diff"][0]["deleted"]), 7)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_srp_delete_existing_no_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("delete_rp1_rp7_with_no_cfg")

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
        self.assertEqual(len(result["diff"][0]["deleted"]), 7)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_srp_delete_existing_with_node_name(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("delete_rp1_rp7_with_node_name")

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
        self.assertEqual(len(result["diff"][0]["deleted"]), 7)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_srp_delete_existing_unauth_err(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("delete_rp1_rp7_config")

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
        self.assertEqual(len(result["diff"][0]["deleted"]), 7)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_srp_delete_existing_and_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("delete_rp1_rp7_config")

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
        self.assertEqual(len(result["diff"][0]["deleted"]), 4)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_srp_delete_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("delete_rp1_rp7_config")

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

    def test_dcnm_srp_delete_no_mand_elems(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("delete_no_mand_elems")

        # From here we will remove one mandatory element from the config and check if that
        # is detected and errored out

        # No node_name object
        cfg_no_dm = copy.deepcopy(self.playbook_config)
        cfg_no_dm[0].pop("node_name")
        set_module_args(
            dict(
                state="deleted",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=cfg_no_dm,
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

    def test_dcnm_srp_replace_rp1_to_rp3_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("replace_rp1_to_rp3")

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

    def test_dcnm_srp_replace_rp1_to_rp3_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("replace_rp1_to_rp3")

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

    def test_dcnm_srp_replace_rp1_to_rp3_existing_no_change(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("replace_rp1_to_rp3_no_change")

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

    def test_dcnm_srp_override_rp1_rp7_with_new_peerings(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("override_with_new_peerings")

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

        self.assertEqual(len(result["diff"][0]["merged"]), 2)
        self.assertEqual(len(result["diff"][0]["deleted"]), 7)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 2)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_srp_override_with_existing_peering(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("override_with_existing_peering")

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
        self.assertEqual(len(result["diff"][0]["deleted"]), 6)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_srp_override_with_existing_peering_updated(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "override_with_existing_peering_updated"
        )

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
        self.assertEqual(len(result["diff"][0]["deleted"]), 6)
        self.assertEqual(len(result["diff"][0]["modified"]), 1)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 1)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_srp_override_with_no_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("override_with_no_config")

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
        self.assertEqual(len(result["diff"][0]["deleted"]), 7)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create and deploy responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_srp_query_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("config_query_non_exist")

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
        self.assertEqual(len(result["diff"][0]["query"]), 2)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_srp_query_with_service_nodes(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("config_query_with_node")

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
        self.assertEqual(len(result["diff"][0]["query"]), 2)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        self.assertEqual(len(result["response"]), 7)

    def test_dcnm_srp_query_with_peer_names(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("config_query_with_peername")

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
        self.assertEqual(len(result["diff"][0]["query"]), 7)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        self.assertEqual(len(result["response"]), 7)

    def test_dcnm_srp_query_no_mand_elems(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_srp_configs")
        self.payloads_data = loadPlaybookData("dcnm_srp_payloads")

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
        result = self.execute_module(changed=False, failed=False)

        # From here we will remove one mandatory element from the config and check if that
        # is detected and errored out

        # No node_name object
        cfg_no_dm = copy.deepcopy(self.playbook_config)
        cfg_no_dm[0].pop("node_name")
        set_module_args(
            dict(
                state="deleted",
                attach=True,
                deploy=True,
                fabric="mmudigon",
                service_fabric="external",
                config=cfg_no_dm,
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
