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

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_links
from .dcnm_module import TestDcnmModule, set_module_args, loadPlaybookData


class TestDcnmLinksModule(TestDcnmModule):

    module = dcnm_links
    fd = None

    def init_data(self):
        self.fd = None

    def log_msg(self, msg):
        if self.fd is None:
            self.fd = open("links-ut.log", "a+")
        self.fd.write(msg)

    def setUp(self):

        super(TestDcnmLinksModule, self).setUp()

        self.mock_dcnm_ip_sn = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_links.get_ip_sn_dict"
        )
        self.run_dcnm_ip_sn = self.mock_dcnm_ip_sn.start()

        self.mock_dcnm_fabric_details = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_links.get_fabric_inventory_details"
        )
        self.run_dcnm_fabric_details = self.mock_dcnm_fabric_details.start()

        self.mock_dcnm_fabric_info = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_links.get_fabric_details"
        )
        self.run_dcnm_fabric_info = self.mock_dcnm_fabric_info.start()

        self.mock_dcnm_send = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_links.dcnm_send"
        )
        self.run_dcnm_send = self.mock_dcnm_send.start()

        self.mock_dcnm_version_supported = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_links.dcnm_version_supported"
        )
        self.run_dcnm_version_supported = (
            self.mock_dcnm_version_supported.start()
        )

    def tearDown(self):

        super(TestDcnmLinksModule, self).tearDown()
        self.mock_dcnm_send.stop()
        self.mock_dcnm_version_supported.stop()
        self.mock_dcnm_fabric_details.stop()
        self.mock_dcnm_fabric_info.stop()
        self.mock_dcnm_ip_sn.stop()

    # -------------------------- FIXTURES --------------------------

    def load_links_fixtures(self):

        if "test_dcnm_intra_links_numbered_" in self._testMethodName:
            self.run_dcnm_fabric_info.side_effect = [self.mock_num_fab_info]

        if "test_dcnm_intra_links_unnumbered_" in self._testMethodName:
            self.run_dcnm_fabric_info.side_effect = [self.mock_unnum_fab_info]

        if "test_dcnm_intra_links_ipv6_" in self._testMethodName:
            self.run_dcnm_fabric_info.side_effect = [self.mock_ipv6_fab_info]

        if "test_dcnm_intra_links_invalid_" in self._testMethodName:
            self.run_dcnm_fabric_info.side_effect = [self.mock_num_fab_info]

        if "test_dcnm_intra_links_vpc_" in self._testMethodName:
            self.run_dcnm_fabric_info.side_effect = [self.mock_num_fab_info]

        if "test_dcnm_intra_links_missing_" in self._testMethodName:
            self.run_dcnm_fabric_info.side_effect = [self.mock_num_fab_info]

        if (
            "test_dcnm_intra_links_missing_peer1_ipv6" in self._testMethodName
        ) or (
            (
                "test_dcnm_intra_links_missing_peer2_ipv6"
                in self._testMethodName
            )
        ):
            self.run_dcnm_fabric_info.side_effect = [self.mock_ipv6_fab_info]

        # -------------------------- INTER-MISC --------------------------------------

        if "test_dcnm_inter_links_src_fab_ro" in self._testMethodName:
            self.run_dcnm_send.side_effect = [self.mock_monitor_true_resp, self.mock_monitor_true_resp]

        if "test_dcnm_inter_links_dst_fab_ro_dst_sw_non_mgbl" in self._testMethodName:

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [self.mock_monitor_false_resp,
                                              self.mock_monitor_true_resp,
                                              [],
                                              merge_links_resp,
                                              deploy_resp,
                                              config_preview_resp]

        if "test_dcnm_inter_links_dst_fab_ro_src_sw_non_mgbl" in self._testMethodName:

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [self.mock_monitor_false_resp,
                                              self.mock_monitor_true_resp,
                                              [],
                                              merge_links_resp,
                                              deploy_resp,
                                              config_preview_resp]

        if "test_dcnm_inter_links_dst_fab_ro_src_dst_sw_non_mgbl" in self._testMethodName:

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [self.mock_monitor_false_resp,
                                              self.mock_monitor_true_resp,
                                              [],
                                              merge_links_resp,
                                              deploy_resp,
                                              config_preview_resp]

        if "test_dcnm_inter_links_dst_fab_ro_src_dst_sw_mgbl" in self._testMethodName:

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [self.mock_monitor_false_resp,
                                              self.mock_monitor_true_resp,
                                              [],
                                              merge_links_resp,
                                              deploy_resp,
                                              config_preview_resp]

        if "test_dcnm_inter_links_dst_fab_rw_dst_sw_non_mgbl" in self._testMethodName:

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [self.mock_monitor_false_resp,
                                              self.mock_monitor_false_resp,
                                              [],
                                              merge_links_resp,
                                              deploy_resp,
                                              config_preview_resp]

        if "test_dcnm_inter_links_dst_fab_rw_src_sw_non_mgbl" in self._testMethodName:

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [self.mock_monitor_false_resp,
                                              self.mock_monitor_false_resp,
                                              [],
                                              merge_links_resp,
                                              deploy_resp,
                                              config_preview_resp]

        if "test_dcnm_inter_links_dst_fab_rw_src_dst_sw_non_mgbl" in self._testMethodName:

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [self.mock_monitor_false_resp,
                                              self.mock_monitor_false_resp,
                                              [],
                                              merge_links_resp,
                                              deploy_resp,
                                              config_preview_resp]

        if "test_dcnm_inter_links_dst_fab_rw_src_dst_sw_mgbl" in self._testMethodName:

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [self.mock_monitor_false_resp,
                                              self.mock_monitor_false_resp,
                                              [],
                                              merge_links_resp,
                                              deploy_resp,
                                              deploy_resp,
                                              config_preview_resp,
                                              config_preview_resp,
                                              config_preview_resp]

        if (
            "test_dcnm_intra_links_unnumbered_merged_new_no_opts"
            == self._testMethodName
        ):

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                [],
                [],
                merge_links_resp,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_unnumbered_merged_new"
            == self._testMethodName
        ):

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                [],
                [],
                merge_links_resp,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_unnumbered_merged_new_no_deploy"
            == self._testMethodName
        ):

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                [],
                [],
                merge_links_resp,
                merge_links_resp,
            ]

        if (
            "test_dcnm_intra_links_unnumbered_merged_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_unnum_fabric_response"
            )
            have_links_resp2 = self.payloads_data.get(
                "intra_have_link2_unnum_fabric_response"
            )
            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_unnumbered_merged_new_no_state"
            == self._testMethodName
        ):

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                [],
                [],
                merge_links_resp,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_merged_new_check_mode"
            == self._testMethodName
        ):
            pass

        if (
            "test_dcnm_intra_links_unnumbered_merged_new_existing_and_non_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_unnum_fabric_response"
            )
            have_links_resp2 = []
            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_unnumbered_modify_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_unnum_fabric_response"
            )
            have_links_resp2 = self.payloads_data.get(
                "intra_have_link2_unnum_fabric_response"
            )
            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_unnumbered_replace_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_unnum_fabric_response"
            )
            have_links_resp2 = self.payloads_data.get(
                "intra_have_link2_unnum_fabric_response"
            )
            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_unnumbered_delete_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_unnum_fabric_response"
            )
            have_links_resp2 = self.payloads_data.get(
                "intra_have_link2_unnum_fabric_response"
            )
            delete_links_resp = self.payloads_data.get(
                "delete_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                [],
                [],
                [],
                delete_links_resp,
                delete_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_unnumbered_delete_existing_and_non_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_unnum_fabric_response"
            )
            delete_links_resp = self.payloads_data.get(
                "delete_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                [],
                [],
                [],
                [],
                delete_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_unnumbered_delete_non_existing"
            == self._testMethodName
        ):

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                [], [], [], [], []]

        if (
            "test_dcnm_intra_links_unnumbered_template_change"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_unnum_fabric_response"
            )
            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if "test_dcnm_intra_links_unnumbered_query" in self._testMethodName:

            query_links_resp = self.payloads_data.get(
                "intra_query_links_unnum_fabric_response"
            )
            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                query_links_resp]

        # -------------------------- INTRA-FABRIC-IPV6 ----------------------------------

        if (
            "test_dcnm_intra_links_ipv6_merged_new_no_opts"
            == self._testMethodName
        ):

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                [],
                [],
                [],
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if "test_dcnm_intra_links_ipv6_merged_new" == self._testMethodName:

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                [],
                [],
                [],
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_ipv6_merged_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_ipv6_fabric_response"
            )
            have_links_resp2 = self.payloads_data.get(
                "intra_have_link2_ipv6_fabric_response"
            )
            have_links_resp3 = self.payloads_data.get(
                "intra_have_link3_ipv6_fabric_response"
            )
            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                have_links_resp3,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_ipv6_merged_new_no_state"
            == self._testMethodName
        ):

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                [],
                [],
                [],
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_ipv6_merged_new_existing_and_non_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_ipv6_fabric_response"
            )
            have_links_resp2 = []
            have_links_resp3 = self.payloads_data.get(
                "intra_have_link3_ipv6_fabric_response"
            )

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                have_links_resp3,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_ipv6_modify_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_ipv6_fabric_response"
            )
            have_links_resp2 = self.payloads_data.get(
                "intra_have_link2_ipv6_fabric_response"
            )
            have_links_resp3 = self.payloads_data.get(
                "intra_have_link3_ipv6_fabric_response"
            )
            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                have_links_resp3,
                merge_links_resp,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_ipv6_replace_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_ipv6_fabric_response"
            )
            have_links_resp2 = self.payloads_data.get(
                "intra_have_link2_ipv6_fabric_response"
            )
            have_links_resp3 = self.payloads_data.get(
                "intra_have_link3_ipv6_fabric_response"
            )
            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                have_links_resp3,
                merge_links_resp,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_ipv6_delete_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_ipv6_fabric_response"
            )
            have_links_resp2 = self.payloads_data.get(
                "intra_have_link2_ipv6_fabric_response"
            )
            have_links_resp3 = self.payloads_data.get(
                "intra_have_link3_ipv6_fabric_response"
            )
            delete_links_resp = self.payloads_data.get(
                "delete_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                have_links_resp3,
                [],
                [],
                delete_links_resp,
                delete_links_resp,
                delete_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_ipv6_delete_existing_and_non_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_ipv6_fabric_response"
            )
            have_links_resp2 = self.payloads_data.get(
                "intra_have_link2_ipv6_fabric_response"
            )
            have_links_resp3 = []
            delete_links_resp = self.payloads_data.get(
                "delete_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                have_links_resp3,
                [],
                [],
                delete_links_resp,
                delete_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_ipv6_delete_non_existing"
            == self._testMethodName
        ):

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                [], [], [], [], []]

        if "test_dcnm_intra_links_ipv6_query" in self._testMethodName:

            query_links_resp = self.payloads_data.get(
                "intra_query_links_ipv6_fabric_response"
            )
            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                query_links_resp]

        # -------------------------- INTRA-FABRIC-NUMBERED --------------------------

        if (
            "test_dcnm_intra_links_numbered_merged_new_no_opts"
            == self._testMethodName
        ):

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                [],
                [],
                [],
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if "test_dcnm_intra_links_numbered_merged_new" == self._testMethodName:

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                [],
                [],
                [],
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_numbered_merged_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_num_fabric_response"
            )
            have_links_resp2 = self.payloads_data.get(
                "intra_have_link2_num_fabric_response"
            )
            have_links_resp3 = self.payloads_data.get(
                "intra_have_link3_num_fabric_response"
            )
            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                have_links_resp3,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_numbered_merged_new_no_state"
            == self._testMethodName
        ):

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                [],
                [],
                [],
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_numbered_merged_new_existing_and_non_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_num_fabric_response"
            )
            have_links_resp2 = []
            have_links_resp3 = self.payloads_data.get(
                "intra_have_link3_num_fabric_response"
            )
            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                have_links_resp3,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_numbered_modify_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_num_fabric_response"
            )
            have_links_resp2 = self.payloads_data.get(
                "intra_have_link2_num_fabric_response"
            )
            have_links_resp3 = self.payloads_data.get(
                "intra_have_link3_num_fabric_response"
            )
            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                have_links_resp3,
                merge_links_resp,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_modify_existing_no_template"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link7_num_fabric_response"
            )
            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]
        if (
            "test_dcnm_intra_links_numbered_replace_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_num_fabric_response"
            )
            have_links_resp2 = self.payloads_data.get(
                "intra_have_link2_num_fabric_response"
            )
            have_links_resp3 = self.payloads_data.get(
                "intra_have_link3_num_fabric_response"
            )
            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                have_links_resp3,
                merge_links_resp,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_numbered_delete_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_num_fabric_response"
            )
            have_links_resp2 = self.payloads_data.get(
                "intra_have_link2_num_fabric_response"
            )
            have_links_resp3 = self.payloads_data.get(
                "intra_have_link3_num_fabric_response"
            )
            delete_links_resp = self.payloads_data.get(
                "delete_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                have_links_resp3,
                [],
                [],
                delete_links_resp,
                delete_links_resp,
                delete_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_numbered_delete_existing_and_non_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_num_fabric_response"
            )
            have_links_resp2 = self.payloads_data.get(
                "intra_have_link2_num_fabric_response"
            )
            have_links_resp3 = []
            delete_links_resp = self.payloads_data.get(
                "delete_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                have_links_resp3,
                [],
                [],
                delete_links_resp,
                delete_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_numbered_delete_non_existing"
            == self._testMethodName
        ):

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                [], [], [], [], []]

        if (
            "test_dcnm_intra_links_numbered_template_change"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_num_fabric_response"
            )
            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if "test_dcnm_intra_links_numbered_query" in self._testMethodName:

            query_links_resp = self.payloads_data.get(
                "intra_query_links_num_fabric_response"
            )
            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                query_links_resp]

        # ------------------------------ INTRA-FABRIC-VPC ---------------------------

        if (
            "test_dcnm_intra_links_vpc_merged_new_no_opts"
            == self._testMethodName
        ):

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                [],
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if "test_dcnm_intra_links_vpc_merged_new" == self._testMethodName:

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                [],
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if "test_dcnm_intra_links_vpc_merged_existing" == self._testMethodName:

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_vpc_num_fabric_response"
            )
            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_vpc_merged_new_no_state"
            == self._testMethodName
        ):

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                [],
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_vpc_merged_new_existing_and_non_existing"
            == self._testMethodName
        ):

            have_links_resp1 = []

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if "test_dcnm_intra_links_vpc_modify_existing" == self._testMethodName:

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_vpc_num_fabric_response"
            )
            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_vpc_replace_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_vpc_num_fabric_response"
            )
            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                have_links_resp1,
                merge_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if "test_dcnm_intra_links_vpc_delete_existing" == self._testMethodName:

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_vpc_num_fabric_response"
            )
            delete_links_resp = self.payloads_data.get(
                "delete_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                [],
                [],
                [],
                have_links_resp1,
                [],
                delete_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_vpc_delete_existing_and_non_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "intra_have_link1_vpc_num_fabric_response"
            )
            delete_links_resp = self.payloads_data.get(
                "delete_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                [],
                [],
                [],
                have_links_resp1,
                [],
                delete_links_resp,
                deploy_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_intra_links_vpc_delete_non_existing"
            == self._testMethodName
        ):

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                [], [], [], [], []]

        if "test_dcnm_intra_links_vpc_query" in self._testMethodName:

            query_links_resp = self.payloads_data.get(
                "intra_query_links_vpc_response"
            )
            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                query_links_resp]

        # -------------------------- INTER-FABRIC-NUMBERED --------------------------

        if (
            "test_dcnm_inter_links_numbered_merged_new_no_opts"
            == self._testMethodName
        ):

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                [],
                [],
                [],
                [],
                [],
                [],
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                deploy_resp,
                deploy_resp,
                deploy_resp,
                config_preview_resp,
                config_preview_resp,
                config_preview_resp,
            ]

        if "test_dcnm_inter_links_numbered_merged_new" == self._testMethodName:

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                [],
                [],
                [],
                [],
                [],
                [],
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                deploy_resp,
                deploy_resp,
                deploy_resp,
                config_preview_resp,
                config_preview_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_inter_links_numbered_merged_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "inter_have_link1_num_fabric_response"
            )
            have_links_resp2 = self.payloads_data.get(
                "inter_have_link2_num_fabric_response"
            )
            have_links_resp3 = self.payloads_data.get(
                "inter_have_link3_num_fabric_response"
            )
            have_links_resp4 = self.payloads_data.get(
                "inter_have_link4_num_fabric_response"
            )
            have_links_resp5 = self.payloads_data.get(
                "inter_have_link5_num_fabric_response"
            )
            have_links_resp6 = self.payloads_data.get(
                "inter_have_link6_num_fabric_response"
            )
            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                have_links_resp3,
                have_links_resp4,
                have_links_resp5,
                have_links_resp6,
                deploy_resp,
                deploy_resp,
                deploy_resp,
                config_preview_resp,
                config_preview_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_inter_links_numbered_merged_new_no_state"
            == self._testMethodName
        ):

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                [],
                [],
                [],
                [],
                [],
                [],
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                deploy_resp,
                deploy_resp,
                deploy_resp,
                config_preview_resp,
                config_preview_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_inter_links_numbered_merged_new_existing_and_non_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "inter_have_link1_num_fabric_response"
            )
            have_links_resp2 = []
            have_links_resp3 = self.payloads_data.get(
                "inter_have_link3_num_fabric_response"
            )
            have_links_resp4 = []
            have_links_resp5 = self.payloads_data.get(
                "inter_have_link5_num_fabric_response"
            )
            have_links_resp6 = []

            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                have_links_resp3,
                have_links_resp4,
                have_links_resp5,
                have_links_resp6,
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                deploy_resp,
                deploy_resp,
                deploy_resp,
                config_preview_resp,
                config_preview_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_inter_links_numbered_modify_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "inter_have_link1_num_fabric_response"
            )
            have_links_resp2 = self.payloads_data.get(
                "inter_have_link2_num_fabric_response"
            )
            have_links_resp3 = self.payloads_data.get(
                "inter_have_link3_num_fabric_response"
            )
            have_links_resp4 = self.payloads_data.get(
                "inter_have_link4_num_fabric_response"
            )
            have_links_resp5 = self.payloads_data.get(
                "inter_have_link5_num_fabric_response"
            )
            have_links_resp6 = self.payloads_data.get(
                "inter_have_link6_num_fabric_response"
            )
            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                have_links_resp3,
                have_links_resp4,
                have_links_resp5,
                have_links_resp6,
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                deploy_resp,
                deploy_resp,
                deploy_resp,
                config_preview_resp,
                config_preview_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_inter_links_numbered_replace_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "inter_have_link1_num_fabric_response"
            )
            have_links_resp2 = self.payloads_data.get(
                "inter_have_link2_num_fabric_response"
            )
            have_links_resp3 = self.payloads_data.get(
                "inter_have_link3_num_fabric_response"
            )
            have_links_resp4 = self.payloads_data.get(
                "inter_have_link4_num_fabric_response"
            )
            have_links_resp5 = self.payloads_data.get(
                "inter_have_link5_num_fabric_response"
            )
            have_links_resp6 = self.payloads_data.get(
                "inter_have_link6_num_fabric_response"
            )
            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                have_links_resp3,
                have_links_resp4,
                have_links_resp5,
                have_links_resp6,
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                merge_links_resp,
                deploy_resp,
                deploy_resp,
                deploy_resp,
                config_preview_resp,
                config_preview_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_inter_links_numbered_delete_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "inter_have_link1_num_fabric_response"
            )
            have_links_resp2 = self.payloads_data.get(
                "inter_have_link2_num_fabric_response"
            )
            have_links_resp3 = self.payloads_data.get(
                "inter_have_link3_num_fabric_response"
            )
            have_links_resp4 = self.payloads_data.get(
                "inter_have_link4_num_fabric_response"
            )
            have_links_resp5 = self.payloads_data.get(
                "inter_have_link5_num_fabric_response"
            )
            have_links_resp6 = self.payloads_data.get(
                "inter_have_link6_num_fabric_response"
            )
            delete_links_resp = self.payloads_data.get(
                "delete_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                have_links_resp3,
                have_links_resp4,
                have_links_resp5,
                have_links_resp6,
                delete_links_resp,
                delete_links_resp,
                delete_links_resp,
                delete_links_resp,
                delete_links_resp,
                delete_links_resp,
                deploy_resp,
                deploy_resp,
                deploy_resp,
                config_preview_resp,
                config_preview_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_inter_links_numbered_delete_existing_and_non_existing"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "inter_have_link1_num_fabric_response"
            )
            have_links_resp2 = self.payloads_data.get(
                "inter_have_link2_num_fabric_response"
            )
            have_links_resp3 = []
            have_links_resp4 = self.payloads_data.get(
                "inter_have_link4_num_fabric_response"
            )
            have_links_resp5 = self.payloads_data.get(
                "inter_have_link5_num_fabric_response"
            )
            have_links_resp6 = []
            delete_links_resp = self.payloads_data.get(
                "delete_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                have_links_resp1,
                have_links_resp2,
                have_links_resp3,
                have_links_resp4,
                have_links_resp5,
                have_links_resp6,
                delete_links_resp,
                delete_links_resp,
                delete_links_resp,
                delete_links_resp,
                deploy_resp,
                deploy_resp,
                deploy_resp,
                config_preview_resp,
                config_preview_resp,
                config_preview_resp,
            ]

        if (
            "test_dcnm_inter_links_numbered_delete_non_existing"
            == self._testMethodName
        ):

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                [], [], [], [], [], []]

        if (
            "test_dcnm_inter_links_numbered_template_change"
            == self._testMethodName
        ):

            have_links_resp1 = self.payloads_data.get(
                "inter_have_link1_num_fabric_response"
            )
            merge_links_resp = self.payloads_data.get(
                "merge_links_fabric_response"
            )
            deploy_resp = self.payloads_data.get("deploy_resp")
            config_preview_resp = self.payloads_data.get("config_preview_resp")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                have_links_resp1,
                merge_links_resp,
                deploy_resp,
                deploy_resp,
                config_preview_resp,
                config_preview_resp,
            ]

        if "test_dcnm_inter_links_numbered_query_no_config" in self._testMethodName:

            query_links_resp = self.payloads_data.get(
                "inter_query_links_num_fabric_response"
            )
            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                query_links_resp]
        elif "test_dcnm_inter_links_numbered_query" in self._testMethodName:

            query_links_resp = self.payloads_data.get(
                "inter_query_links_num_fabric_response"
            )
            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.mock_monitor_false_resp,
                query_links_resp]

    def load_fixtures(self, response=None, device=""):

        self.run_dcnm_version_supported.side_effect = [12]
        self.run_dcnm_fabric_details.side_effect = [
            self.mock_fab_inv,
            self.mock_fab_inv,
            self.mock_fab_inv,
        ]
        self.run_dcnm_ip_sn.side_effect = [[self.mock_ip_sn, self.mock_hn_sn]]
        # Load Links related side-effects
        self.load_links_fixtures()

    # -------------------------- FIXTURES END --------------------------
    # -------------------------- TEST-CASES ----------------------------
    # -------------------------- INTRA-FABRIC-NUMBERED ------------------------------

    def test_dcnm_intra_links_numbered_merged_new_no_opts(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_merge_num_no_opts_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_numbered_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_merge_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_numbered_merged_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_merge_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_numbered_merged_new_no_state(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_merge_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_numbered_merged_new_check_mode(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_merge_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                _ansible_check_mode=True,
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_numbered_merged_new_existing_and_non_existing(
        self
    ):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_merge_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_numbered_modify_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_modify_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 2)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_numbered_replace_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_replace_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="replaced",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 2)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_numbered_delete_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_delete_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="deleted",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 3)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 2
        )

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_numbered_delete_existing_and_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_delete_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="deleted",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 2)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 2
        )

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_numbered_delete_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_delete_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="deleted",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_numbered_template_change(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_modify_num_template_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 1)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 2
        )

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_numbered_query_no_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = []
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 3), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_numbered_query_with_dst_fabric(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_num_dest_fabric_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 3), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_numbered_query_with_src_device(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_num_src_dev_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 3), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_numbered_query_with_dst_device(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_num_dst_dev_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 3), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_numbered_query_with_src_interface(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_num_src_intf_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 1), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_numbered_query_with_dst_interface(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_num_dst_intf_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 1), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_numbered_query(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_query_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 3), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    # ------------------------- INTRA-FABRIC-MISC-----------------------------

    def test_dcnm_intra_links_modify_existing_no_template(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_modify_number_no_template")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    # ------------------------- INTRA-FABRIC-UNNUMBERED -----------------------------

    def test_dcnm_intra_links_unnumbered_merged_new_no_opts(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_merge_unnum_no_opts_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_umnum_fab_data"
        )
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 2)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-unnumbered"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_unnumbered_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_merge_unnum_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 2)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-unnumbered"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_unnumbered_merged_new_no_deploy(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_merge_unnum_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
                deploy=False,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 2)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_unnumbered_merged_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_merge_unnum_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-unnumbered"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_unnumbered_merged_new_no_state(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_merge_unnum_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 2)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-unnumbered"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_unnumbered_merged_new_check_mode(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_merge_unnum_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                _ansible_check_mode=True,
                state="merged",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 2)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-unnumbered"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_unnumbered_merged_new_existing_and_non_existing(
        self
    ):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_merge_unnum_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-unnumbered"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_unnumbered_modify_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_modify_unnum_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 1)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-unnumbered"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_unnumbered_replace_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_replace_unnum_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="replaced",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 1)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-unnumbered"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_unnumbered_delete_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_delete_unnum_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="deleted",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 2)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-unnumbered"]), 2
        )

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_unnumbered_delete_existing_and_non_existing(
        self
    ):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_delete_unnum_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="deleted",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 1)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-unnumbered"]), 2
        )

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_unnumbered_delete_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_delete_unnum_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="deleted",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_unnumbered_template_change(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_modify_unnum_template_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 1)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-unnumbered"]), 2
        )

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_unnumbered_query_not_exist(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_unnum_not_exist"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 0), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_unnumbered_query_no_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = []
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 2), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_unnumbered_query_with_dst_fabric(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_unnum_dest_fabric_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 2), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_unnumbered_query_with_src_device(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_unnum_src_dev_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 2), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_unnumbered_query_with_dst_device(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_unnum_dst_dev_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 2), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_unnumbered_query_with_src_interface(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_unnum_src_intf_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 1), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_unnumbered_query_with_dst_interface(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_unnum_dst_intf_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 1), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_unnumbered_query(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_query_unnum_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 2), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    # ------------------------- INTRA-FABRIC-IPV6 -----------------------------------

    def test_dcnm_intra_links_ipv6_merged_new_no_opts(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_merge_ipv6_no_opts_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-ipv6-underlay",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-ipv6-underlay"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_ipv6_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_merge_ipv6_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-ipv6-underlay",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-ipv6-underlay"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_ipv6_merged_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_merge_ipv6_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-ipv6-underlay",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-ipv6-underlay"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_ipv6_merged_new_no_state(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_merge_ipv6_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-ipv6-underlay",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-ipv6-underlay"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_ipv6_merged_new_check_mode(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_merge_ipv6_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                _ansible_check_mode=True,
                state="merged",
                src_fabric="mmudigon-ipv6-underlay",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-ipv6-underlay"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_ipv6_merged_new_existing_and_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_merge_ipv6_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-ipv6-underlay",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-ipv6-underlay"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_ipv6_modify_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_modify_ipv6_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-ipv6-underlay",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 2)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-ipv6-underlay"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_ipv6_replace_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_replace_ipv6_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="replaced",
                src_fabric="mmudigon-ipv6-underlay",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 2)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-ipv6-underlay"]), 2
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_ipv6_delete_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_delete_ipv6_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="deleted",
                src_fabric="mmudigon-ipv6-underlay",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 3)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-ipv6-underlay"]), 2
        )

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_ipv6_delete_existing_and_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_delete_ipv6_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="deleted",
                src_fabric="mmudigon-ipv6-underlay",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 2)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-ipv6-underlay"]), 2
        )

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_ipv6_delete_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_delete_ipv6_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="deleted",
                src_fabric="mmudigon-ipv6-underlay",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_ipv6_query_no_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = []
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-ipv6-underlay",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 3), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_ipv6_query_with_dst_fabric(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_ipv6_dest_fabric_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-ipv6-underlay",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 3), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_ipv6_query_with_src_device(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_ipv6_src_dev_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-ipv6-underlay",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 3), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_ipv6_query_with_dst_device(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_ipv6_dst_dev_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-ipv6-underlay",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 3), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_ipv6_query_with_src_interface(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_ipv6_src_intf_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-ipv6-underlay",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 1), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_ipv6_query_with_dst_interface(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_ipv6_dst_intf_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-ipv6-underlay",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 1), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_ipv6_query(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_query_ipv6_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-ipv6-underlay",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 3), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_ipv6_query_not_exist(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_ipv6_not_exist"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 0), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    # -------------------------- INTRA-FABRIC-VPC ---------------------------------

    def test_dcnm_intra_links_vpc_merged_new_no_opts(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_merge_vpc_no_opts_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon"]), 2)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_vpc_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_merge_vpc_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon"]), 2)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_vpc_merged_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_merge_vpc_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon"]), 2)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_vpc_merged_new_no_state(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_merge_vpc_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon"]), 2)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_vpc_merged_new_check_mode(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_merge_vpc_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                _ansible_check_mode=True,
                state="merged",
                src_fabric="mmudigon",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon"]), 2)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_vpc_merged_new_existing_and_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_merge_vpc_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon"]), 2)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_vpc_modify_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_modify_vpc_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 1)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon"]), 2)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_vpc_replace_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_replace_vpc_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="replaced",
                src_fabric="mmudigon",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 1)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon"]), 2)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_vpc_delete_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_delete_vpc_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="deleted",
                src_fabric="mmudigon",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 1)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon"]), 2)

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_vpc_delete_existing_and_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_delete_vpc_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="deleted",
                src_fabric="mmudigon",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 1)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon"]), 2)

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_vpc_delete_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_delete_vpc_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="deleted",
                src_fabric="mmudigon",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_intra_links_vpc_query_no_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = []
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 1), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_vpc_query_with_dst_fabric(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_vpc_dest_fabric_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 1), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_vpc_query_with_src_device(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_vpc_src_dev_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 1), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_vpc_query_with_dst_device(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_vpc_dst_dev_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 1), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_vpc_query_with_src_interface(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_vpc_src_intf_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 1), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_vpc_query_with_dst_interface(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_query_vpc_dst_intf_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 1), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_intra_links_vpc_query(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_query_vpc_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 1), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    # -------------------------- INTER-FABRIC NUMBERED ------------------------------

    def test_dcnm_inter_links_numbered_merged_new_no_opts(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_merge_num_no_opts_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 6)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 1
        )
        self.assertEqual(len(result["diff"][0]["deploy"][0]["test_net"]), 1)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["test_net1"]), 1)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_inter_links_numbered_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("inter_merge_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 6)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 1
        )
        self.assertEqual(len(result["diff"][0]["deploy"][0]["test_net"]), 1)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["test_net1"]), 1)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_inter_links_numbered_merged_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("inter_merge_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 1
        )
        self.assertEqual(len(result["diff"][0]["deploy"][0]["test_net"]), 1)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["test_net1"]), 1)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_inter_links_numbered_merged_new_no_state(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("inter_merge_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 6)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 1
        )
        self.assertEqual(len(result["diff"][0]["deploy"][0]["test_net"]), 1)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["test_net1"]), 1)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_inter_links_numbered_merged_new_check_mode(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("inter_merge_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                _ansible_check_mode=True,
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 6)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 1
        )
        self.assertEqual(len(result["diff"][0]["deploy"][0]["test_net"]), 1)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["test_net1"]), 1)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_inter_links_numbered_merged_new_existing_and_non_existing(
        self
    ):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("inter_merge_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 1
        )
        self.assertEqual(len(result["diff"][0]["deploy"][0]["test_net"]), 1)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["test_net1"]), 1)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_inter_links_numbered_modify_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("inter_modify_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 6)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 1
        )
        self.assertEqual(len(result["diff"][0]["deploy"][0]["test_net"]), 1)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["test_net1"]), 1)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_inter_links_numbered_replace_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("inter_replace_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="replaced",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 6)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 1
        )
        self.assertEqual(len(result["diff"][0]["deploy"][0]["test_net"]), 1)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["test_net1"]), 1)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_inter_links_numbered_delete_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("inter_delete_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="deleted",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 6)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 1
        )
        self.assertEqual(len(result["diff"][0]["deploy"][0]["test_net"]), 1)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["test_net1"]), 1)

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_inter_links_numbered_delete_existing_and_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("inter_delete_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="deleted",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 4)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 1
        )
        self.assertEqual(len(result["diff"][0]["deploy"][0]["test_net"]), 1)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["test_net1"]), 1)

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_inter_links_numbered_delete_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("inter_delete_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="deleted",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_inter_links_numbered_template_change(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_modify_num_template_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 1)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(
            len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 1
        )
        self.assertEqual(len(result["diff"][0]["deploy"][0]["test_net"]), 1)

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_inter_links_numbered_query_no_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = []
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 6), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_inter_links_numbered_query_with_dst_fabric(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_query_num_dest_fabric_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 3), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_inter_links_numbered_query_with_src_device(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_query_num_src_dev_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 1), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_inter_links_numbered_query_with_dst_device(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_query_num_dst_dev_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 1), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_inter_links_numbered_query_with_src_interface(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_query_num_src_intf_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 1), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_inter_links_numbered_query_with_dst_interface(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_query_num_dst_intf_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 1), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_inter_links_numbered_query(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("inter_query_num_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 3), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_inter_links_numbered_query_not_exist(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_query_num_not_exist"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_unnum_fab_info = self.payloads_data.get(
            "mock_unnum_fab_data"
        )
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual((len(result["response"]) == 0), True)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    # ---------------------- INTRA-FABRIC INVALID PARAMS ----------------------------

    def test_dcnm_intra_links_invalid_template(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_invalid_template_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-unnumbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(("Invalid choice [ dcnm_links_invalid_template ] provided" in str(e)), True)

    def test_dcnm_intra_links_missing_src_fabric(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_missing_src_fabric_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(dict(state="merged", config=self.playbook_config))

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("missing required arguments: src_fabric" in str(e)), True
            )

    def test_dcnm_intra_links_missing_dst_fabric(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_missing_dst_fabric_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("Required parameter not found: dst_fabric" in str(e)), True
            )

    def test_dcnm_intra_links_missing_src_intf(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_missing_src_intf_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("src_interface : Required parameter not found" in str(e)),
                True,
            )

    def test_dcnm_intra_links_missing_dst_intf(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_missing_dst_intf_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("dst_interface : Required parameter not found" in str(e)),
                True,
            )

    def test_dcnm_intra_links_missing_src_device(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_missing_src_device_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("src_device : Required parameter not found" in str(e)), True
            )

    def test_dcnm_intra_links_missing_dst_device(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_missing_dst_device_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("dst_device : Required parameter not found" in str(e)), True
            )

    def test_dcnm_intra_links_missing_template(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_missing_template_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("Required parameter not found: template" in str(e)), True
            )

    def test_dcnm_intra_links_missing_peer1_ipv6(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_missing_peer1_ipv6_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-ipv6-underlay",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("peer1_ipv6_addr : Required parameter not found" in str(e)),
                True,
            )

    def test_dcnm_intra_links_missing_peer2_ipv6(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_missing_peer2_ipv6_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-ipv6-underlay",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("peer2_ipv6_addr : Required parameter not found" in str(e)),
                True,
            )

    def test_dcnm_intra_links_missing_peer1_ipv4(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_missing_peer1_ipv4_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("peer1_ipv4_addr : Required parameter not found" in str(e)),
                True,
            )

    def test_dcnm_intra_links_missing_peer2_ipv4(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_missing_peer2_ipv4_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("peer2_ipv4_addr : Required parameter not found" in str(e)),
                True,
            )

    def test_dcnm_intra_links_missing_mtu(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("intra_missing_mtu_config")
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("mtu : Required parameter not found" in str(e)), True
            )

    def test_dcnm_intra_links_missing_admin_state(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "intra_missing_admin_state_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("admin_state : Required parameter not found" in str(e)), True
            )

    # ---------------------- INTER-FABRIC INVALID PARAMS ----------------------------

    def test_dcnm_inter_links_invalid_template(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_invalid_template_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="query",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(("Invalid choice [ dcnm_links_invalid_template ] provided" in str(e)), True)

    def test_dcnm_inter_links_missing_src_fabric(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_missing_src_fabric_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(dict(state="merged", config=self.playbook_config))

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("missing required arguments: src_fabric" in str(e)), True
            )

    def test_dcnm_inter_links_missing_dst_fabric(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_missing_dst_fabric_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("Required parameter not found: dst_fabric" in str(e)), True
            )

    def test_dcnm_inter_links_missing_src_intf(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_missing_src_intf_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("src_interface : Required parameter not found" in str(e)),
                True,
            )

    def test_dcnm_inter_links_missing_dst_intf(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_missing_dst_intf_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("dst_interface : Required parameter not found" in str(e)),
                True,
            )

    def test_dcnm_inter_links_missing_src_device(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_missing_src_device_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("src_device : Required parameter not found" in str(e)), True
            )

    def test_dcnm_inter_links_missing_dst_device(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_missing_dst_device_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("dst_device : Required parameter not found" in str(e)), True
            )

    def test_dcnm_inter_links_missing_template(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_missing_template_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("Required parameter not found: template" in str(e)), True
            )

    def test_dcnm_inter_links_missing_ipv4_subnet(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_missing_ipv4_subnet_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("ipv4_subnet : Required parameter not found" in str(e)), True
            )

    def test_dcnm_inter_links_missing_neighbor_ip(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_missing_neighbor_ip_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")
        self.mock_ipv6_fab_info = self.payloads_data.get("mock_ipv6_fab_data")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("neighbor_ip : Required parameter not found" in str(e)), True
            )

    def test_dcnm_inter_links_missing_src_asn(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_missing_src_asn_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("src_asn : Required parameter not found" in str(e)), True
            )

    def test_dcnm_inter_links_missing_dst_asn(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_missing_dst_asn_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("dst_asn : Required parameter not found" in str(e)), True
            )

    def test_dcnm_inter_links_missing_ipv4_addr(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_missing_ipv4_addr_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("ipv4_addr : Required parameter not found" in str(e)), True
            )

    # ---------------------- INTER-FABRIC MISC ----------------------------

    def test_dcnm_inter_links_src_fab_ro(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_src_fab_ro_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-src-fab-ro",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(
                ("is in Monitoring mode" in str(e)), True
            )
            self.assertEqual(
                ("No changes are allowed on the fabric" in str(e)), True
            )

    def test_dcnm_inter_links_dst_fab_ro_dst_sw_non_mgbl(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_dst_fab_ro_dst_sw_non_mgbl_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 1)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon-dst-fab-ro"]), 0)

    def test_dcnm_inter_links_dst_fab_ro_src_sw_non_mgbl(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_dst_fab_ro_src_sw_non_mgbl_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon-dst-fab-ro"]), 0)

    def test_dcnm_inter_links_dst_fab_ro_src_dst_sw_non_mgbl(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_dst_fab_ro_src_dst_sw_non_mgbl_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon-dst-fab-ro"]), 0)

    def test_dcnm_inter_links_dst_fab_ro_src_dst_sw_mgbl(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_dst_fab_ro_src_dst_sw_mgbl_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 1)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon-dst-fab-ro"]), 0)

    def test_dcnm_inter_links_dst_fab_rw_dst_sw_non_mgbl(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_dst_fab_rw_dst_sw_non_mgbl_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 1)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon-dst-fab-rw"]), 0)

    def test_dcnm_inter_links_dst_fab_rw_src_sw_non_mgbl(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_dst_fab_rw_src_sw_non_mgbl_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon-dst-fab-rw"]), 0)

    def test_dcnm_inter_links_dst_fab_rw_src_dst_sw_non_mgbl(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_dst_fab_rw_src_dst_sw_non_mgbl_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon-dst-fab-rw"]), 0)

    def test_dcnm_inter_links_dst_fab_rw_src_dst_sw_mgbl(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_links_configs")
        self.payloads_data = loadPlaybookData("dcnm_links_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "inter_dst_fab_rw_src_dst_sw_mgbl_config"
        )
        self.mock_ip_sn = self.payloads_data.get("mock_ip_sn")
        self.mock_hn_sn = self.payloads_data.get("mock_hn_sn")
        self.mock_fab_inv = self.payloads_data.get("mock_fab_inv_data")
        self.mock_num_fab_info = self.payloads_data.get("mock_num_fab_data")
        self.mock_monitor_true_resp = self.payloads_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.payloads_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-numbered",
                config=self.playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon-numbered"]), 1)
        self.assertEqual(len(result["diff"][0]["deploy"][0]["mmudigon-dst-fab-rw"]), 1)
