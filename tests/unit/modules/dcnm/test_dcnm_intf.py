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

# from units.compat.mock import patch

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface
from .dcnm_module import TestDcnmModule, set_module_args, loadPlaybookData

import json
import copy


class TestDcnmIntfModule(TestDcnmModule):

    module = dcnm_interface
    fd = None

    def init_data(self):
        self.fd = None

    def log_msg(self, msg):

        if self.fd is None:
            self.fd = open("intf-ut.log", "w")
        self.fd.write(msg)
        self.fd.flush()

    def setUp(self):

        super(TestDcnmIntfModule, self).setUp()

        self.mock_dcnm_fabric_details = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface.get_fabric_inventory_details"
        )
        self.run_dcnm_fabric_details = self.mock_dcnm_fabric_details.start()

        self.mock_dcnm_ip_sn = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface.get_ip_sn_dict"
        )
        self.run_dcnm_ip_sn = self.mock_dcnm_ip_sn.start()

        self.mock_dcnm_version_supported = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface.dcnm_version_supported"
        )
        self.run_dcnm_version_supported = (
            self.mock_dcnm_version_supported.start()
        )

        self.mock_dcnm_send = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface.dcnm_send"
        )
        self.run_dcnm_send = self.mock_dcnm_send.start()

    def tearDown(self):

        super(TestDcnmIntfModule, self).tearDown()
        self.mock_dcnm_send.stop()
        self.mock_dcnm_version_supported.stop()
        self.mock_dcnm_ip_sn.stop()
        self.mock_dcnm_fabric_details.stop()

    # -------------------------- GEN-FIXTURES --------------------------

    def load_multi_intf_fixtures(self):

        if "_multi_intf_merged_new" in self._testMethodName:
            # No I/F exists case
            playbook_pc_intf = []
            playbook_vpc_intf = []
            playbook_subint_intf = []
            playbook_lo_intf = []
            playbook_eth_intf = []
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                self.playbook_mock_vpc_resp,
                playbook_pc_intf,
                playbook_vpc_intf,
                playbook_subint_intf,
                playbook_lo_intf,
                playbook_eth_intf,
                playbook_have_all_data,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                playbook_deployed_data,
            ]

        if "_multi_intf_merged_exist" in self._testMethodName:
            # No I/F exists case
            playbook_pc_intf = self.payloads_data.get("pc_payload")
            playbook_lo_intf = self.payloads_data.get("lo_payload")
            playbook_eth_intf = self.payloads_data.get("eth_payload")
            playbook_subint_intf = self.payloads_data.get("subint_payload")
            playbook_vpc_intf = self.payloads_data.get("vpc_payload")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                self.playbook_mock_vpc_resp,
                playbook_pc_intf,
                playbook_vpc_intf,
                playbook_subint_intf,
                playbook_lo_intf,
                playbook_eth_intf,
                playbook_have_all_data,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                playbook_deployed_data,
            ]

    def load_missing_intf_elems_fixtures(self):

        if "_missing_intf_elems" in self._testMethodName:
            # No I/F exists case
            playbook_pc_intf1 = []
            playbook_pc_intf2 = []
            playbook_vpc_intf = []
            playbook_eth_intf = []
            playbook_subint_intf = []
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                self.playbook_mock_vpc_resp,
                playbook_pc_intf1,
                playbook_pc_intf2,
                playbook_vpc_intf,
                playbook_subint_intf,
                playbook_eth_intf,
                playbook_have_all_data,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                playbook_deployed_data,
            ]

    def load_mixed_intf_elems_fixtures(self):

        if "_mixed_intf_merged_new" in self._testMethodName:
            # No I/F exists case
            playbook_pc_intf = []
            playbook_eth_intf = []
            playbook_lo_intf = []
            playbook_subint_intf = []
            playbook_vpc_intf = []
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                self.playbook_mock_vpc_resp,
                playbook_pc_intf,
                playbook_eth_intf,
                playbook_vpc_intf,
                playbook_lo_intf,
                playbook_subint_intf,
                playbook_have_all_data,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                playbook_deployed_data,
            ]

    def load_bunched_intf_elems_fixtures(self):

        if "_bunched_intf_merged_new" in self._testMethodName:
            # No I/F exists case
            playbook_pc_intf1 = []
            playbook_pc_intf2 = []
            playbook_pc_intf3 = []
            playbook_pc_intf4 = []
            playbook_eth_intf1 = []
            playbook_eth_intf2 = []
            playbook_eth_intf3 = []
            playbook_eth_intf4 = []
            playbook_vpc_intf1 = []
            playbook_vpc_intf2 = []
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                self.playbook_mock_vpc_resp,
                playbook_pc_intf1,
                playbook_pc_intf2,
                playbook_pc_intf3,
                playbook_pc_intf4,
                playbook_eth_intf1,
                playbook_eth_intf2,
                playbook_eth_intf3,
                playbook_eth_intf4,
                playbook_vpc_intf1,
                playbook_vpc_intf2,
                playbook_have_all_data,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                playbook_deployed_data,
            ]

    def load_missing_members_fixtures(self):

        if "_missing_peer_members" in self._testMethodName:
            # No I/F exists case
            playbook_intf = []
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                self.playbook_mock_vpc_resp,
                playbook_intf,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                playbook_deployed_data,
            ]

    def load_type_missing_fixtures(self):

        if "_type_missing_merged_new" in self._testMethodName:
            # No I/F exists case
            playbook_pc_intf = []
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_pc_intf,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

    def load_missing_state_fixtures(self):

        if "_missing_state" in self._testMethodName:
            # No I/F exists case
            playbook_pc_intf = []
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_pc_intf,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

    def load_query_state_fixtures(self):

        if "_query" in self._testMethodName:
            playbook_all_intf = self.payloads_data.get("all_payload")
            playbook_pc_intf = self.payloads_data.get("pc_payload")
            playbook_lo_intf = self.payloads_data.get("lo_payload")
            playbook_eth_intf = self.payloads_data.get("eth_payload")
            playbook_sub_intf = self.payloads_data.get("subint_payload")
            playbook_vpc_intf = self.payloads_data.get("vpc_payload")
            playbook_svi_intf = self.payloads_data.get("svi_payload")
            playbook_st_fex_intf = self.payloads_data.get("st_fex_payload")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.playbook_mock_vpc_resp,
                self.playbook_mock_vpc_resp,
                playbook_all_intf,
                playbook_pc_intf,
                playbook_lo_intf,
                playbook_eth_intf,
                playbook_sub_intf,
                playbook_vpc_intf,
                playbook_svi_intf,
                playbook_st_fex_intf,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

    def load_intf_misc_fixtures(self):

        if "test_dcnm_intf_merge_fabric_monitoring" in self._testMethodName:
            self.run_dcnm_send.side_effect = [self.mock_monitor_true_resp]
        if "test_dcnm_intf_merge_unmanagable_switch" in self._testMethodName:
            self.run_dcnm_send.side_effect = [self.mock_monitor_false_resp]

    # -------------------------- SVI-FIXTURES --------------------------

    def load_svi_fixtures(self):

        if "_svi_merged_new" in self._testMethodName:
            # No I/F exists case
            playbook_svi_intf1 = []
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_svi_intf1,
                playbook_have_all_data,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_svi_merged_idempotent" in self._testMethodName:
            playbook_svi_intf1 = self.payloads_data.get("svi_merged_payloads")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_svi_intf1,
                playbook_have_all_data,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        # Use the same payloads that we use for creating new.
        if "_svi_deleted_existing" in self._testMethodName:
            playbook_svi_intf1 = self.payloads_data.get("svi_merged_payloads")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_svi_intf1,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_svi_deleted_non_existing" in self._testMethodName:
            playbook_svi_intf1 = []
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_svi_intf1,
                playbook_svi_intf1,
            ]
        if "_svi_replaced_existing" in self._testMethodName:
            playbook_svi_intf1 = self.payloads_data.get("svi_merged_payloads")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_svi_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_svi_overridden_existing" in self._testMethodName:

            playbook_svi_intf1 = self.payloads_data.get("svi_merged_payloads")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_svi_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

    # -------------------------- AA-FEX-FIXTURES --------------------------

    def load_aa_fex_fixtures(self):

        if "_aa_fex_merged_new" in self._testMethodName:
            # No I/F exists case
            playbook_aa_fex_intf1 = []
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_aa_fex_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_aa_fex_merged_idempotent" in self._testMethodName:
            playbook_aa_fex_intf1 = self.payloads_data.get("aa_fex_merged_payloads_150")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_aa_fex_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_aa_fex_merged_existing" in self._testMethodName:
            playbook_aa_fex_intf1 = self.payloads_data.get("aa_fex_merged_payloads_150")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_aa_fex_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_aa_fex_merged_multi" in self._testMethodName:
            # No I/F exists case
            playbook_aa_fex_intf1 = []
            playbook_aa_fex_intf2 = []
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                self.playbook_mock_vpc_resp,
                playbook_aa_fex_intf1,
                playbook_aa_fex_intf2,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        # Use the same payloads that we use for creating new.
        if "_aa_fex_deleted_existing" in self._testMethodName:
            playbook_aa_fex_intf1 = self.payloads_data.get("aa_fex_merged_payloads_150")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_aa_fex_intf1,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_aa_fex_deleted_non_existing" in self._testMethodName:
            playbook_aa_fex_intf1 = []
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_aa_fex_intf1,
                playbook_aa_fex_intf1,
            ]

        if "_aa_fex_replaced_existing" in self._testMethodName:
            playbook_aa_fex_intf1 = self.payloads_data.get("aa_fex_merged_payloads_150")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_aa_fex_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_aa_fex_overridden_existing" in self._testMethodName:

            playbook_aa_fex_intf1 = self.payloads_data.get("aa_fex_merged_payloads_150")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_aa_fex_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_aa_fex_overridden_modify_existing" in self._testMethodName:

            playbook_aa_fex_intf1 = self.payloads_data.get("aa_fex_merged_payloads_150")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_aa_fex_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

    # -------------------------- ST-FEX-FIXTURES --------------------------

    def load_st_fex_fixtures(self):

        if "_st_fex_merged_new" in self._testMethodName:
            # No I/F exists case
            playbook_st_fex_intf1 = []
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_st_fex_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_st_fex_merged_idempotent" in self._testMethodName:
            playbook_st_fex_intf1 = self.payloads_data.get("st_fex_merged_payloads_150")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_st_fex_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_st_fex_merged_existing" in self._testMethodName:
            playbook_st_fex_intf1 = self.payloads_data.get("st_fex_merged_payloads_150")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_st_fex_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_st_fex_merged_multi" in self._testMethodName:
            # No I/F exists case
            playbook_st_fex_intf1 = []
            playbook_st_fex_intf2 = []
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                self.playbook_mock_vpc_resp,
                playbook_st_fex_intf1,
                playbook_st_fex_intf2,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        # Use the same payloads that we use for creating new.
        if "_st_fex_deleted_existing" in self._testMethodName:
            playbook_st_fex_intf1 = self.payloads_data.get("st_fex_merged_payloads_150")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_st_fex_intf1,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_st_fex_deleted_non_existing" in self._testMethodName:
            playbook_st_fex_intf1 = []
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_st_fex_intf1,
                playbook_st_fex_intf1,
            ]
        if "_st_fex_replaced_existing" in self._testMethodName:
            playbook_st_fex_intf1 = self.payloads_data.get("st_fex_merged_payloads_150")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_st_fex_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_st_fex_overridden_existing" in self._testMethodName:

            playbook_st_fex_intf1 = self.payloads_data.get("st_fex_merged_payloads_150")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_st_fex_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_st_fex_overridden_modify_existing" in self._testMethodName:

            playbook_st_fex_intf1 = self.payloads_data.get("st_fex_merged_payloads_150")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_st_fex_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

    # -------------------------- PC-FIXTURES --------------------------

    def load_pc_fixtures(self):

        if "_pc_merged_new" in self._testMethodName:
            # No I/F exists case
            playbook_pc_intf1 = []
            playbook_pc_intf2 = []
            playbook_pc_intf3 = []
            playbook_pc_intf4 = []
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_pc_intf1,
                playbook_pc_intf2,
                playbook_pc_intf3,
                playbook_pc_intf4,
                playbook_have_all_data,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]
        if "_pc_merged_policy_change" in self._testMethodName:
            playbook_pc_intf1 = self.payloads_data.get(
                "pc_merged_trunk_payloads"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_pc_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_pc_merged_idempotent" in self._testMethodName:
            playbook_pc_intf1 = self.payloads_data.get(
                "pc_merged_trunk_payloads"
            )
            playbook_pc_intf2 = self.payloads_data.get(
                "pc_merged_access_payloads"
            )
            playbook_pc_intf3 = self.payloads_data.get("pc_merged_l3_payloads")
            playbook_pc_intf4 = self.payloads_data.get(
                "pc_merged_monitor_payloads"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_pc_intf1,
                playbook_pc_intf2,
                playbook_pc_intf3,
                playbook_pc_intf4,
                playbook_have_all_data,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        # Use the same payloads that we use for creating new.
        if "_pc_deleted_existing" in self._testMethodName:
            playbook_pc_intf1 = self.payloads_data.get(
                "pc_merged_trunk_payloads"
            )
            playbook_pc_intf2 = self.payloads_data.get(
                "pc_merged_access_payloads"
            )
            playbook_pc_intf3 = self.payloads_data.get("pc_merged_l3_payloads")
            playbook_pc_intf4 = self.payloads_data.get(
                "pc_merged_monitor_payloads"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_pc_intf1,
                playbook_pc_intf2,
                playbook_pc_intf3,
                playbook_pc_intf4,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_intf_deleted_existing_no_deploy" in self._testMethodName:
            playbook_pc_intf1 = self.payloads_data.get(
                "pc_merged_trunk_payloads"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_pc_intf1,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_intf_deleted_deploy" in self._testMethodName:
            playbook_pc_intf1 = []
            playbook_have_all_data = self.have_all_payloads_data.get(
                "deleted_intf_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_pc_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_intf_deleted_existing_no_deploy" in self._testMethodName:
            playbook_pc_intf1 = self.payloads_data.get(
                "pc_merged_trunk_payloads"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_pc_intf1,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_pc_replaced_existing" in self._testMethodName:
            playbook_pc_intf1 = self.payloads_data.get(
                "pc_merged_trunk_payloads"
            )
            playbook_pc_intf2 = self.payloads_data.get(
                "pc_merged_access_payloads"
            )
            playbook_pc_intf3 = self.payloads_data.get("pc_merged_l3_payloads")
            playbook_pc_intf4 = self.payloads_data.get(
                "pc_merged_monitor_payloads"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_pc_intf1,
                playbook_pc_intf2,
                playbook_pc_intf3,
                playbook_pc_intf4,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_pc_overridden_existing" in self._testMethodName:

            playbook_pc_intf1 = self.payloads_data.get(
                "pc_merged_trunk_payloads"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_pc_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

    # -------------------------- ETH-FIXTURES --------------------------

    def load_eth_fixtures(self):

        if "_eth_merged_new" in self._testMethodName:
            # No I/F exists case
            playbook_eth_intf1 = []
            playbook_eth_intf2 = []
            playbook_eth_intf3 = []
            playbook_eth_intf4 = []
            playbook_eth_intf5 = []
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_eth_intf1,
                playbook_eth_intf2,
                playbook_eth_intf3,
                playbook_eth_intf4,
                playbook_eth_intf5,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                playbook_deployed_data,
            ]

        if "_eth_merged_existing" in self._testMethodName:
            # No I/F exists case
            playbook_eth_intf1 = self.payloads_data.get(
                "eth_merged_routed_payloads_eth_1_2"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_eth_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_eth_merged_idempotent" in self._testMethodName:

            playbook_eth_intf1 = self.payloads_data.get(
                "eth_merged_trunk_payloads"
            )
            playbook_eth_intf2 = self.payloads_data.get(
                "eth_merged_access_payloads"
            )
            playbook_eth_intf3 = self.payloads_data.get(
                "eth_merged_routed_payloads"
            )
            playbook_eth_intf4 = self.payloads_data.get(
                "eth_merged_epl_routed_payloads"
            )
            playbook_eth_intf5 = self.payloads_data.get(
                "eth_merged_monitor_payloads"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_eth_intf1,
                playbook_eth_intf2,
                playbook_eth_intf3,
                playbook_eth_intf4,
                playbook_eth_intf5,
                playbook_have_all_data,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_eth_replaced_existing" in self._testMethodName:

            playbook_eth_intf1 = self.payloads_data.get(
                "eth_merged_trunk_payloads"
            )
            playbook_eth_intf2 = self.payloads_data.get(
                "eth_merged_access_payloads"
            )
            playbook_eth_intf3 = self.payloads_data.get(
                "eth_merged_routed_payloads"
            )
            playbook_eth_intf4 = self.payloads_data.get(
                "eth_merged_epl_routed_payloads"
            )
            playbook_eth_intf5 = self.payloads_data.get(
                "eth_merged_monitor_payloads"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_eth_intf1,
                playbook_eth_intf2,
                playbook_eth_intf3,
                playbook_eth_intf4,
                playbook_eth_intf5,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                playbook_deployed_data,
            ]

        if "_eth_deleted_existing" in self._testMethodName:

            playbook_eth_intf1 = self.payloads_data.get(
                "eth_merged_trunk_payloads"
            )
            playbook_eth_intf2 = self.payloads_data.get(
                "eth_merged_access_payloads"
            )
            playbook_eth_intf3 = self.payloads_data.get(
                "eth_merged_routed_payloads"
            )
            playbook_eth_intf4 = self.payloads_data.get(
                "eth_merged_epl_routed_payloads"
            )
            playbook_eth_intf5 = self.payloads_data.get(
                "eth_merged_monitor_payloads"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "eth_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_have_all_data,
                playbook_eth_intf1,
                playbook_eth_intf2,
                playbook_eth_intf3,
                playbook_eth_intf4,
                playbook_eth_intf5,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_eth_overridden_existing" in self._testMethodName:

            playbook_eth_intf1 = self.payloads_data.get(
                "eth_merged_trunk_payloads"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_eth_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                playbook_deployed_data,
            ]

    # -------------------------- SUBINT-FIXTURES --------------------------

    def load_subint_fixtures(self):

        if "_subint_merged_new" in self._testMethodName:
            # No I/F exists case
            playbook_sub_intf1 = []
            playbook_sub_intf2 = []
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_sub_intf1,
                playbook_sub_intf2,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                playbook_deployed_data,
            ]

        if "_subint_merged_idempotent" in self._testMethodName:

            playbook_subint_intf1 = self.payloads_data.get(
                "subint_merged_payloads_1"
            )
            playbook_subint_intf2 = self.payloads_data.get(
                "subint_merged_payloads_2"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_subint_intf1,
                playbook_subint_intf2,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_subint_replaced_existing" in self._testMethodName:

            playbook_subint_intf1 = self.payloads_data.get(
                "subint_merged_payloads_1"
            )
            playbook_subint_intf2 = self.payloads_data.get(
                "subint_merged_payloads_2"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_subint_intf1,
                playbook_subint_intf2,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                playbook_deployed_data,
            ]

        if "_subint_replaced_non_existing" in self._testMethodName:

            playbook_subint_intf1 = self.payloads_data.get(
                "subint_merged_payloads_1"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_subint_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                playbook_deployed_data,
            ]

        if "_subint_deleted_existing" in self._testMethodName:

            playbook_subint_intf1 = self.payloads_data.get(
                "subint_merged_payloads_1"
            )
            playbook_subint_intf2 = self.payloads_data.get(
                "subint_merged_payloads_2"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_subint_intf1,
                playbook_subint_intf2,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_subint_deleted_non_existing" in self._testMethodName:

            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                [],
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_subint_overridden_existing" in self._testMethodName:

            playbook_subint_intf1 = self.payloads_data.get(
                "subint_merged_payloads_1"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_subint_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                playbook_deployed_data,
            ]

    # -------------------------- LOOPBACK-FIXTURES --------------------------

    def load_lo_fixtures(self):

        if "_lo_merged_new" in self._testMethodName:
            # No I/F exists case
            playbook_lo_intf1 = []
            playbook_lo_intf2 = []
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_lo_intf1,
                playbook_lo_intf2,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                playbook_deployed_data,
            ]

        if "_lo_merged_idempotent" in self._testMethodName:

            playbook_lo_intf1 = self.payloads_data.get("lo_merged_payloads_1")
            playbook_lo_intf2 = self.payloads_data.get("lo_merged_payloads_2")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_lo_intf1,
                playbook_lo_intf2,
                playbook_have_all_data,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_lo_merged_existing" in self._testMethodName:

            playbook_lo_intf1 = self.payloads_data.get("lo_merged_payloads_1")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_lo_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                playbook_deployed_data,
            ]

        if "_lo_replaced_existing" in self._testMethodName:

            playbook_lo_intf1 = self.payloads_data.get("lo_merged_payloads_1")
            playbook_lo_intf2 = self.payloads_data.get("lo_merged_payloads_2")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_lo_intf1,
                playbook_lo_intf2,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                playbook_deployed_data,
            ]

        if "_lo_deleted_existing" in self._testMethodName:

            playbook_lo_intf1 = self.payloads_data.get("lo_merged_payloads_1")
            playbook_lo_intf2 = self.payloads_data.get("lo_merged_payloads_2")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_lo_intf1,
                playbook_lo_intf2,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        # We are overriding 2 interfaces here which is different from other cases. So we need
        # side-effects for both
        if "_lo_overridden_existing" in self._testMethodName:

            playbook_lo_intf1 = self.payloads_data.get("lo_merged_payloads_1")
            playbook_lo_intf2 = self.payloads_data.get("lo_merged_payloads_2")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_lo_intf1,
                playbook_lo_intf2,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                playbook_deployed_data,
            ]

        if "_lo_overridden_non_existing" in self._testMethodName:

            playbook_lo_intf1 = self.payloads_data.get("lo_merged_payloads_1")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_lo_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                playbook_deployed_data,
            ]

        if "_lo_overridden_existing_2" in self._testMethodName:

            playbook_lo_intf1 = self.payloads_data.get("lo_merged_payloads_3")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_lo_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

    # -------------------------- vPC-FIXTURES --------------------------

    def load_vpc_fixtures(self):

        if "_vpc_merged_new" in self._testMethodName:
            # No I/F exists case
            playbook_vpc_intf1 = []
            playbook_vpc_intf2 = []
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                self.playbook_mock_vpc_resp,
                playbook_vpc_intf1,
                playbook_vpc_intf2,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                playbook_deployed_data,
            ]

        if "_vpc_merged_idempotent" in self._testMethodName:
            playbook_vpc_intf1 = self.payloads_data.get(
                "vpc_merged_trunk_payloads"
            )
            playbook_vpc_intf2 = self.payloads_data.get(
                "vpc_merged_access_payloads"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                self.playbook_mock_vpc_resp,
                playbook_vpc_intf1,
                playbook_vpc_intf2,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        # Use the same payloads that we use for creating new.
        if "_vpc_deleted_existing" in self._testMethodName:
            playbook_vpc_intf1 = self.payloads_data.get(
                "vpc_merged_trunk_payloads"
            )
            playbook_vpc_intf2 = self.payloads_data.get(
                "vpc_merged_access_payloads"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                self.playbook_mock_vpc_resp,
                playbook_vpc_intf1,
                playbook_vpc_intf2,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_vpc_replaced_existing" in self._testMethodName:
            playbook_vpc_intf1 = self.payloads_data.get(
                "vpc_merged_trunk_payloads"
            )
            playbook_vpc_intf2 = self.payloads_data.get(
                "vpc_merged_access_payloads"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                self.playbook_mock_vpc_resp,
                playbook_vpc_intf1,
                playbook_vpc_intf2,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                playbook_deployed_data,
            ]

        if "_vpc_overridden_existing" in self._testMethodName:

            playbook_vpc_intf1 = self.payloads_data.get(
                "vpc_merged_trunk_payloads"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                self.playbook_mock_vpc_resp,
                playbook_vpc_intf1,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                playbook_deployed_data,
            ]

    # -------------------------- END-FIXTURES --------------------------

    def load_fixtures(self, response=None, device=""):

        # setup the side effects
        self.run_dcnm_fabric_details.side_effect = [self.mock_fab_inv]
        self.run_dcnm_ip_sn.side_effect = [[self.mock_ip_sn, []]]
        self.run_dcnm_version_supported.side_effect = [11]

        # Load AA_FEX fixtures
        self.load_aa_fex_fixtures()

        # Load ST_FEX fixtures
        self.load_st_fex_fixtures()

        # Load SVI fixtures
        self.load_svi_fixtures()

        # Load port channel related side-effects
        self.load_pc_fixtures()

        # Load ethernet related side-effects
        self.load_eth_fixtures()

        # Load subint related side-effects
        self.load_subint_fixtures()

        # Load loopback related side-effects
        self.load_lo_fixtures()

        # Load vPC related side-effects
        self.load_vpc_fixtures()

        # Load Multiple interafces related side-effects
        self.load_multi_intf_fixtures()

        # Load Missing interface elements related side-effects
        self.load_missing_intf_elems_fixtures()

        # Load mixed interface configuration related side-effects
        self.load_mixed_intf_elems_fixtures()

        # Load bunched interface configuration related side-effects
        self.load_bunched_intf_elems_fixtures()

        # Load missing elements interface configuration related side-effects
        self.load_type_missing_fixtures()
        self.load_missing_state_fixtures()
        self.load_missing_members_fixtures()
        self.load_query_state_fixtures()
        self.load_intf_misc_fixtures()

    # -------------------------- GEN-INTF --------------------------

    def test_dcnm_intf_multi_intf_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_multi_intf_configs")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )
        self.payloads_data = []

        # load required config data
        self.playbook_config = self.config_data.get("multi_intf_merged_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 5)
        for d in result["diff"][0]["merged"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (
                        intf["ifName"]
                        in [
                            "Port-channel300",
                            "vPC301",
                            "Ethernet1/1.1",
                            "Ethernet1/10",
                            "Loopback303",
                        ]
                    ),
                    True,
                )

    def test_dcnm_intf_multi_intf_merged_exist(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_multi_intf_configs")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )
        self.payloads_data = loadPlaybookData("dcnm_intf_multi_intf_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "multi_intf_merged_config_exist"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 5)
        for d in result["diff"][0]["merged"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (
                        intf["ifName"]
                        in [
                            "Port-channel300",
                            "vPC301",
                            "Ethernet1/1.1",
                            "Ethernet1/10",
                            "Loopback303",
                        ]
                    ),
                    True,
                )
                for key in intf["nvPairs"]:
                    if "MEMBER_INTERFACES" in key:
                        self.assertEqual(
                            len(intf["nvPairs"][key].split(",")), 2
                        )
                    if "CONF" in key:
                        self.assertEqual(
                            len(intf["nvPairs"][key].split("\n")), 2
                        )

    def test_dcnm_intf_missing_intf_elems_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_multi_intf_configs")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )
        self.payloads_data = []

        # load required config data
        self.playbook_config = self.config_data.get(
            "missing_intf_elems_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 5)
        for d in result["diff"][0]["merged"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (
                        intf["ifName"]
                        in [
                            "Port-channel301",
                            "Port-channel302",
                            "Ethernet1/25.1",
                            "Ethernet1/32",
                            "vPC751",
                        ]
                    ),
                    True,
                )

    def test_dcnm_intf_check_multi_intf_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_multi_intf_configs")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )
        self.payloads_data = []

        # load required config data
        self.playbook_config = self.config_data.get("multi_intf_merged_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                _ansible_check_mode=True,
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 5)
        self.assertFalse(result.get("response"))
        for d in result["diff"][0]["merged"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (
                        intf["ifName"]
                        in [
                            "Port-channel300",
                            "vPC301",
                            "Ethernet1/1.1",
                            "Ethernet1/10",
                            "Loopback303",
                        ]
                    ),
                    True,
                )

    # -------------------------- PC --------------------------

    def test_dcnm_intf_pc_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_pc_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_pc_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("pc_merged_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 4)
        for d in result["diff"][0]["merged"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (
                        intf["ifName"]
                        in [
                            "Port-channel300",
                            "Port-channel301",
                            "Port-channel302",
                            "Port-channel303",
                        ]
                    ),
                    True,
                )

    def test_dcnm_intf_pc_merged_idempotent(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_pc_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_pc_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("pc_merged_config")

        for cfg in self.playbook_config:
            cfg["deploy"] = "False"
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 0)

    def test_dcnm_intf_pc_merged_policy_change(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_pc_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_pc_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config_data = self.config_data.get(
            "pc_merged_config_policy_change"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config_data,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 1)

    def test_dcnm_intf_pc_deleted_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_pc_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_pc_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("pc_deleted_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 4)
        for intf in result["diff"][0]["deleted"]:
            self.assertEqual(
                (
                    intf["ifName"]
                    in [
                        "Port-channel300",
                        "Port-channel301",
                        "Port-channel302",
                        "Port-channel303",
                    ]
                ),
                True,
            )

    def test_dcnm_intf_deleted_existing_no_deploy(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_pc_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_pc_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("pc_deleted_config_no_deploy")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 1)
        for intf in result["diff"][0]["deleted"]:
            self.assertEqual(
                (
                    intf["ifName"]
                    in [
                        "Port-channel300",
                    ]
                ),
                True,
            )
        self.assertEqual(len(result["diff"][0]["delete_deploy"]), 0)

    def test_dcnm_intf_deleted_deploy(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_pc_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_pc_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("pc_deleted_config_deploy")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["delete_deploy"]), 1)

    def test_dcnm_intf_pc_replaced_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_pc_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_pc_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("pc_replaced_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["replaced"]), 3)

        changed_objs = [
            "MEMBER_INTERFACES",
            "PC_MODE",
            "BPDUGUARD_ENABLED",
            "PORTTYPE_FAST_ENABLED",
            "MTU",
            "ALLOWED_VLANS",
            "DESC",
            "ADMIN_STATE",
            "INTF_VRF",
            "IP",
            "PREFIX",
            "ROUTING_TAG",
            "SPEED",
            "CONF",
        ]

        for d in result["diff"][0]["replaced"]:
            for intf in d["interfaces"]:
                if_keys = list(intf["nvPairs"].keys())
                self.assertEqual(
                    (set(if_keys).issubset(set(changed_objs))), True
                )
        # Monitor port wil not be deployes
        self.assertEqual(len(result["diff"][0]["deploy"]), 3)

    def test_dcnm_intf_pc_overridden_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_pc_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_pc_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("pc_overridden_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 7)

        del_if_names = [
            "port-channel301",
            "port-channel302",
            "port-channel303",
            "ethernet1/3.2",
            "loopback200",
            "vpc300",
            "vlan2001",
        ]

        rep_if_names = [
            "ethernet1/3.2",
            "ethernet1/1",
            "ethernet1/2",
            "ethernet3/2",
        ]
        ovr_if_names = ["port-channel300"]

        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"].lower() in del_if_names), True)

        for d in result["diff"][0]["replaced"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in rep_if_names), True
                )

        for d in result["diff"][0]["overridden"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in ovr_if_names), True
                )

    # -------------------------- ETH --------------------------

    def test_dcnm_intf_eth_merged_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_eth_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_eth_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get(
            "eth_merged_config_existing"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        for d in result["diff"][0]["merged"]:
            for intf in d["interfaces"]:
                self.assertEqual((intf["ifName"] in ["Ethernet1/2"]), True)

    def test_dcnm_intf_eth_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_eth_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_eth_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("eth_merged_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 5)
        for d in result["diff"][0]["merged"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (
                        intf["ifName"]
                        in [
                            "Ethernet1/30",
                            "Ethernet1/31",
                            "Ethernet1/32",
                            "Ethernet1/33",
                            "Ethernet1/34",
                        ]
                    ),
                    True,
                )

    def test_dcnm_intf_eth_merged_idempotent(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_eth_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_eth_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("eth_merged_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        for cfg in self.playbook_config:
            cfg["deploy"] = "False"

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 0)

    def test_dcnm_intf_eth_replaced_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_eth_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_eth_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("eth_replaced_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["replaced"]), 4)

        changed_objs = [
            "BPDUGUARD_ENABLED",
            "PORTTYPE_FAST_ENABLED",
            "MTU",
            "CONF",
            "ALLOWED_VLANS",
            "DESC",
            "ADMIN_STATE",
            "INTF_VRF",
            "ACCESS_VLAN",
            "SPEED",
            "IP",
            "PREFIX",
            "ROUTING_TAG",
            "SPEED",
            "IPv6",
            "IPv6_PREFIX",
        ]

        for d in result["diff"][0]["replaced"]:
            for intf in d["interfaces"]:
                if_keys = list(intf["nvPairs"].keys())
                self.assertEqual(
                    (set(if_keys).issubset(set(changed_objs))), True
                )
        # Monitor port will not bedeployed
        self.assertEqual(len(result["diff"][0]["deploy"]), 4)

    def test_dcnm_intf_eth_deleted_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_eth_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_eth_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("eth_deleted_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["replaced"]), 5)

    def test_dcnm_intf_eth_overridden_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_eth_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_eth_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("eth_overridden_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 8)

        del_if_names = [
            "port-channel301",
            "port-channel302",
            "port-channel303",
            "port-channel300",
            "ethernet1/3.2",
            "loopback200",
            "vpc300",
            "vlan2001",
        ]

        rep_if_names = ["ethernet1/1", "ethernet1/2", "ethernet3/2"]
        ovr_if_names = ["ethernet1/30"]

        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"].lower() in del_if_names), True)

        for d in result["diff"][0]["replaced"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in rep_if_names), True
                )

        for d in result["diff"][0]["overridden"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in ovr_if_names), True
                )

    # -------------------------- SUBINT --------------------------

    def test_dcnm_intf_subint_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_subint_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_subint_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("subint_merged_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 2)
        for d in result["diff"][0]["merged"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"] in ["Ethernet1/25.1", "Ethernet1/25.2"]),
                    True,
                )

    def test_dcnm_intf_subint_merged_idempotent(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_subint_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_subint_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("subint_merged_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        for cfg in self.playbook_config:
            cfg["deploy"] = "False"

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 0)

    def test_dcnm_intf_subint_replaced_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_subint_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_subint_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("subint_replaced_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["replaced"]), 2)

        changed_objs = [
            "MTU",
            "CONF",
            "VLAN",
            "DESC",
            "ADMIN_STATE",
            "SPEED",
            "INTF_VRF",
            "IP",
            "PREFIX",
            "IPv6",
            "IPv6_PREFIX",
        ]

        for d in result["diff"][0]["replaced"]:
            for intf in d["interfaces"]:
                if_keys = list(intf["nvPairs"].keys())
                self.assertEqual(
                    (set(if_keys).issubset(set(changed_objs))), True
                )
        # All 2 will be deployed, even though we have not changed the monitor port
        self.assertEqual(len(result["diff"][0]["deploy"]), 2)

    def test_dcnm_intf_subint_replaced_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_subint_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_subint_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get(
            "subint_replaced_config_non_exist"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["replaced"]), 1)
        self.assertEqual(len(result["diff"][0]["merged"]), 0)

    def test_dcnm_intf_subint_deleted_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_subint_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_subint_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("subint_deleted_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 2)
        for intf in result["diff"][0]["deleted"]:
            self.assertEqual(
                (intf["ifName"] in ["Ethernet1/25.1", "Ethernet1/25.2"]), True
            )

    def test_dcnm_intf_subint_deleted_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_subint_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_subint_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get(
            "subint_deleted_non_existing_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 0)

    def test_dcnm_intf_subint_overridden_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_subint_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_subint_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("subint_overridden_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 8)

        del_if_names = [
            "port-channel301",
            "port-channel302",
            "port-channel303",
            "port-channel300",
            "ethernet1/3.2",
            "loopback200",
            "vpc300",
            "vlan2001",
        ]

        rep_if_names = ["ethernet1/1", "ethernet1/2", "ethernet3/2"]
        ovr_if_names = ["Ethernet1/25.1"]

        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"].lower() in del_if_names), True)

        for d in result["diff"][0]["replaced"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in rep_if_names), True
                )

        for d in result["diff"][0]["overridden"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in ovr_if_names), True
                )

    # -------------------------- LOOPBACK --------------------------

    def test_dcnm_intf_lo_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_lo_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_lo_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("lo_merged_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 2)
        for d in result["diff"][0]["merged"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"] in ["Loopback100", "Loopback101"]), True
                )

    def test_dcnm_intf_lo_merged_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_lo_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_lo_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get(
            "lo_merged_existing_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        for d in result["diff"][0]["merged"]:
            for intf in d["interfaces"]:
                self.assertEqual((intf["ifName"] in ["Loopback100"]), True)

    def test_dcnm_intf_lo_merged_idempotent(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_lo_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_lo_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("lo_merged_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        for cfg in self.playbook_config:
            cfg["deploy"] = "False"

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 0)

    def test_dcnm_intf_lo_replaced_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_lo_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_lo_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("lo_replaced_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["replaced"]), 2)

        changed_objs = [
            "CONF",
            "DESC",
            "ADMIN_STATE",
            "ROUTE_MAP_TAG",
            "SPEED",
            "INTF_VRF",
            "IP",
            "V6IP",
        ]

        for d in result["diff"][0]["replaced"]:
            for intf in d["interfaces"]:
                if_keys = list(intf["nvPairs"].keys())
                self.assertEqual(
                    (set(if_keys).issubset(set(changed_objs))), True
                )
        # All 2 will be deployed, even though we have not changed the monitor port
        self.assertEqual(len(result["diff"][0]["deploy"]), 2)

    def test_dcnm_intf_lo_deleted_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_lo_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_lo_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("lo_deleted_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 2)
        for intf in result["diff"][0]["deleted"]:
            self.assertEqual(
                (intf["ifName"] in ["Loopback100", "Loopback101"]), True
            )

    def test_dcnm_intf_lo_overridden_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_lo_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_lo_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("lo_overridden_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 8)

        del_if_names = [
            "port-channel301",
            "port-channel302",
            "port-channel303",
            "port-channel300",
            "ethernet1/3.2",
            "loopback200",
            "vpc300",
            "vlan2001",
        ]

        rep_if_names = ["ethernet1/1", "ethernet1/2", "ethernet3/2"]
        ovr_if_names = ["loopback100", "loopback101"]

        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"].lower() in del_if_names), True)

        for d in result["diff"][0]["replaced"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in rep_if_names), True
                )

        for d in result["diff"][0]["overridden"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in ovr_if_names), True
                )

    def test_dcnm_intf_lo_overridden_existing_2(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_lo_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_lo_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get(
            "lo_overridden_existing_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 7)

        del_if_names = [
            "port-channel301",
            "port-channel302",
            "port-channel303",
            "port-channel300",
            "ethernet1/3.2",
            "vpc300",
            "vlan2001",
        ]

        rep_if_names = ["ethernet1/1", "ethernet1/2", "ethernet3/2"]
        ovr_if_names = ["loopback200"]

        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"].lower() in del_if_names), True)

        for d in result["diff"][0]["replaced"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in rep_if_names), True
                )

        for d in result["diff"][0]["overridden"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in ovr_if_names), True
                )

    def test_dcnm_intf_lo_overridden_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_lo_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_lo_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get(
            "lo_overridden_non_existing_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 8)

        del_if_names = [
            "port-channel301",
            "port-channel302",
            "port-channel303",
            "port-channel300",
            "ethernet1/3.2",
            "loopback200",
            "vpc300",
            "vlan2001",
        ]

        rep_if_names = ["ethernet1/1", "ethernet1/2", "ethernet3/2"]
        ovr_if_names = ["loopback900"]

        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"].lower() in del_if_names), True)

        for d in result["diff"][0]["replaced"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in rep_if_names), True
                )

        for d in result["diff"][0]["overridden"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in ovr_if_names), True
                )

    # -------------------------- vPC --------------------------

    def test_dcnm_intf_vpc_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_vpc_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_vpc_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("vpc_merged_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 2)
        for d in result["diff"][0]["merged"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"] in ["vPC750", "vPC751"]), True
                )

    def test_dcnm_intf_vpc_merged_idempotent(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_vpc_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_vpc_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("vpc_merged_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        for cfg in self.playbook_config:
            cfg["deploy"] = "False"
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 0)

    def test_dcnm_intf_vpc_deleted_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_vpc_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_vpc_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("vpc_deleted_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 2)
        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"] in ["vPC750", "vPC751"]), True)

    def test_dcnm_intf_vpc_replaced_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_vpc_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_vpc_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("vpc_replaced_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["replaced"]), 2)

        changed_objs = [
            "PEER1_MEMBER_INTERFACES",
            "PEER2_MEMBER_INTERFACES",
            "PC_MODE",
            "BPDUGUARD_ENABLED",
            "SPEED",
            "PORTTYPE_FAST_ENABLED",
            "MTU",
            "PEER1_ALLOWED_VLANS",
            "PEER2_ALLOWED_VLANS",
            "PEER1_PO_DESC",
            "PEER2_PO_DESC",
            "ADMIN_STATE",
            "PEER1_ACCESS_VLAN",
            "PEER2_ACCESS_VLAN",
            "PEER1_CONF",
            "PEER2_CONF",
            "PEER1_PO_CONF",
            "PEER2_PO_CONF",
            "INTF_NAME",
        ]

        for d in result["diff"][0]["replaced"]:
            for intf in d["interfaces"]:
                if_keys = list(intf["nvPairs"].keys())
                self.assertEqual(
                    (set(if_keys).issubset(set(changed_objs))), True
                )
        # All 4 will be deployed, even though we have not changed the monitor port
        self.assertEqual(len(result["diff"][0]["deploy"]), 2)

    def test_dcnm_intf_vpc_overridden_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_vpc_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_vpc_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("vpc_overridden_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 8)

        del_if_names = [
            "port-channel301",
            "port-channel302",
            "port-channel303",
            "port-channel300",
            "ethernet1/3.2",
            "loopback200",
            "vpc300",
            "vlan2001",
        ]

        rep_if_names = [
            "ethernet1/3.2",
            "ethernet1/1",
            "ethernet1/2",
            "ethernet3/2",
        ]
        ovr_if_names = ["vPC750"]

        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"].lower() in del_if_names), True)

        for d in result["diff"][0]["replaced"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in rep_if_names), True
                )

        for d in result["diff"][0]["overridden"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in ovr_if_names), True
                )

    # -------------------------- SVI --------------------------

    def test_dcnm_intf_svi_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_svi_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_svi_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("svi_merged_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        for d in result["diff"][0]["merged"]:
            for intf in d["interfaces"]:
                self.assertEqual((intf["ifName"] in ["vlan1001"]), True)

    def test_dcnm_intf_svi_merged_idempotent(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_svi_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_svi_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("svi_merged_config")

        for cfg in self.playbook_config:
            cfg["deploy"] = "False"
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 0)

    def test_dcnm_intf_svi_deleted_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_svi_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_svi_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get(
            "svi_deleted_existing_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 1)
        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"] in ["vlan1001"]), True)

    def test_dcnm_intf_svi_deleted_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_svi_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_svi_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get(
            "svi_deleted_non_existing_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"] in ["vlan1001"]), True)

    def test_dcnm_intf_svi_replaced_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_svi_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_svi_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("svi_replaced_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["replaced"]), 1)

        changed_objs = [
            "MEMBER_INTERFACES",
            "PC_MODE",
            "BPDUGUARD_ENABLED",
            "PORTTYPE_FAST_ENABLED",
            "MTU",
            "ALLOWED_VLANS",
            "DESC",
            "ADMIN_STATE",
            "INTF_VRF",
            "IP",
            "PREFIX",
            "ROUTING_TAG",
            "SPEED",
            "CONF",
            "DISABLE_IP_REDIRECTS",
            "ENABLE_HSRP",
            "ENABLE_NETFLOW",
            "HSRP_GROUP",
            "HSRP_PRIORITY",
            "HSRP_VERSION",
            "HSRP_VIP",
            "INTF_NAME",
            "MAC",
            "NETFLOW_MONITOR",
            "PREEMPT",
            "advSubnetInUnderlay",
            "dhcpServerAddr1",
            "dhcpServerAddr2",
            "dhcpServerAddr3",
            "vrfDhcp1",
            "vrfDhcp2",
            "vrfDhcp3",
        ]

        for d in result["diff"][0]["replaced"]:
            for intf in d["interfaces"]:
                if_keys = list(intf["nvPairs"].keys())
                self.assertEqual(
                    (set(if_keys).issubset(set(changed_objs))), True
                )
        # Monitor port wil not be deployes
        self.assertEqual(len(result["diff"][0]["deploy"]), 1)

    def test_dcnm_intf_svi_overridden_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_svi_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_svi_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("svi_overridden_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 8)

        del_if_names = [
            "port-channel301",
            "port-channel302",
            "port-channel303",
            "port-channel300",
            "ethernet1/3.2",
            "loopback200",
            "vpc300",
            "vlan2001",
        ]

        rep_if_names = [
            "ethernet1/3.2",
            "ethernet1/1",
            "ethernet1/2",
            "ethernet3/2",
        ]
        ovr_if_names = ["vlan1010"]

        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"].lower() in del_if_names), True)

        for d in result["diff"][0]["replaced"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in rep_if_names), True
                )

        for d in result["diff"][0]["overridden"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in ovr_if_names), True
                )

    # -------------------------- AA-FEX --------------------------

    def test_dcnm_intf_aa_fex_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_aa_fex_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_aa_fex_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("aa_fex_merged_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        for d in result["diff"][0]["merged"]:
            for intf in d["interfaces"]:
                self.assertEqual((intf["ifName"] in ["vPC150"]), True)

    def test_dcnm_intf_aa_fex_merged_idempotent(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_aa_fex_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_aa_fex_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("aa_fex_merged_config")

        for cfg in self.playbook_config:
            cfg["deploy"] = "False"
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 0)

    def test_dcnm_intf_aa_fex_merged_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_aa_fex_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_aa_fex_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("aa_fex_merge_existing_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        for d in result["diff"][0]["merged"]:
            for intf in d["interfaces"]:
                self.assertEqual((intf["ifName"] in ["vPC150"]), True)

    def test_dcnm_intf_aa_fex_merged_multi_switches(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_aa_fex_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_aa_fex_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("aa_fex_merge_multi_switches_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        for d in result["diff"][0]["merged"]:
            for intf in d["interfaces"]:
                self.assertEqual((intf["ifName"] in ["vPC155"]), True)

    def test_dcnm_intf_aa_fex_deleted_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_aa_fex_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_aa_fex_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get(
            "aa_fex_deleted_existing_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 1)
        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"] in ["vPC150"]), True)

    def test_dcnm_intf_aa_fex_deleted_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_aa_fex_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_aa_fex_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get(
            "aa_fex_deleted_non_existing_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 0)

    def test_dcnm_intf_aa_fex_replaced_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_aa_fex_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_aa_fex_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("aa_fex_replaced_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["replaced"]), 1)

        changed_objs = [
            "FEX_ID",
            "MTU",
            "DESC",
            "PEER1_PO_DESC",
            "PEER2_PO_DESC",
            "ADMIN_STATE",
            "SPEED",
            "PEER1_MEMBER_INTERFACES",
            "PEER2_MEMBER_INTERFACES",
            "PEER1_PO_CONF",
            "PEER2_PO_CONF",
            "ENABLE_NETFLOW",
            "INTF_NAME",
            "NETFLOW_MONITOR",
        ]

        for d in result["diff"][0]["replaced"]:
            for intf in d["interfaces"]:
                if_keys = list(intf["nvPairs"].keys())
                self.assertEqual(
                    (set(if_keys).issubset(set(changed_objs))), True
                )
        # Monitor port wil not be deployes
        self.assertEqual(len(result["diff"][0]["deploy"]), 1)

    def test_dcnm_intf_aa_fex_overridden_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_aa_fex_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_aa_fex_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("aa_fex_overridden_new_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 8)

        del_if_names = [
            "port-channel301",
            "port-channel302",
            "port-channel303",
            "port-channel300",
            "ethernet1/3.2",
            "loopback200",
            "vpc300",
            "vlan2001",
        ]

        rep_if_names = [
            "ethernet1/3.2",
            "ethernet1/1",
            "ethernet1/2",
            "ethernet3/2",
        ]

        ovr_if_names = ["vpc159"]

        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"].lower() in del_if_names), True)

        for d in result["diff"][0]["replaced"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in rep_if_names), True
                )

        for d in result["diff"][0]["overridden"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in ovr_if_names), True
                )

    def test_dcnm_intf_aa_fex_overridden_modify_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_aa_fex_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_aa_fex_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("aa_fex_overridden_modify_existing_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 8)

        del_if_names = [
            "port-channel301",
            "port-channel302",
            "port-channel303",
            "port-channel300",
            "ethernet1/3.2",
            "loopback200",
            "vpc300",
            "vlan2001",
        ]

        rep_if_names = [
            "ethernet1/3.2",
            "ethernet1/1",
            "ethernet1/2",
            "ethernet3/2",
        ]

        ovr_if_names = ["vpc150"]

        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"].lower() in del_if_names), True)

        for d in result["diff"][0]["replaced"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in rep_if_names), True
                )

        for d in result["diff"][0]["overridden"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in ovr_if_names), True
                )

    # -------------------------- ST-FEX --------------------------

    def test_dcnm_intf_st_fex_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_st_fex_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_st_fex_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("st_fex_merged_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        for d in result["diff"][0]["merged"]:
            for intf in d["interfaces"]:
                self.assertEqual((intf["ifName"] in ["Port-channel150"]), True)

    def test_dcnm_intf_st_fex_merged_idempotent(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_st_fex_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_st_fex_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("st_fex_merged_config")

        for cfg in self.playbook_config:
            cfg["deploy"] = "False"
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertEqual(len(result["diff"][0]["merged"]), 0)

    def test_dcnm_intf_st_fex_merged_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_st_fex_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_st_fex_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("st_fex_merge_existing_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        for d in result["diff"][0]["merged"]:
            for intf in d["interfaces"]:
                self.assertEqual((intf["ifName"] in ["Port-channel150"]), True)

    def test_dcnm_intf_st_fex_merged_multi_switches(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_st_fex_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_st_fex_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("st_fex_merge_multi_switches_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 2)
        for d in result["diff"][0]["merged"]:
            for intf in d["interfaces"]:
                self.assertEqual((intf["ifName"] in ["Port-channel155"]), True)

    def test_dcnm_intf_st_fex_deleted_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_st_fex_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_st_fex_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get(
            "st_fex_deleted_existing_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 1)
        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"] in ["Port-channel150"]), True)

    def test_dcnm_intf_st_fex_deleted_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_st_fex_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_st_fex_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get(
            "st_fex_deleted_non_existing_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 0)

    def test_dcnm_intf_st_fex_replaced_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_st_fex_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_st_fex_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("st_fex_replaced_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["replaced"]), 1)

        changed_objs = [
            "FEX_ID",
            "MTU",
            "DESC",
            "PO_DESC",
            "PO_ID",
            "ADMIN_STATE",
            "SPEED",
            "MEMBER_INTERFACES",
            "CONF",
            "ENABLE_NETFLOW",
            "INTF_NAME",
            "NETFLOW_MONITOR",
        ]

        for d in result["diff"][0]["replaced"]:
            for intf in d["interfaces"]:
                if_keys = list(intf["nvPairs"].keys())
                self.assertEqual(
                    (set(if_keys).issubset(set(changed_objs))), True
                )
        # Monitor port wil not be deployes
        self.assertEqual(len(result["diff"][0]["deploy"]), 1)

    def test_dcnm_intf_st_fex_overridden_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_st_fex_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_st_fex_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("st_fex_overridden_new_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 8)

        del_if_names = [
            "port-channel301",
            "port-channel302",
            "port-channel303",
            "port-channel300",
            "ethernet1/3.2",
            "loopback200",
            "vpc300",
            "vlan2001",
        ]

        rep_if_names = [
            "ethernet1/3.2",
            "ethernet1/1",
            "ethernet1/2",
            "ethernet3/2",
        ]

        ovr_if_names = ["port-channel159"]

        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"].lower() in del_if_names), True)

        for d in result["diff"][0]["replaced"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in rep_if_names), True
                )

        for d in result["diff"][0]["overridden"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in ovr_if_names), True
                )

    def test_dcnm_intf_st_fex_overridden_modify_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_st_fex_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_st_fex_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("st_fex_overridden_modify_existing_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 8)

        del_if_names = [
            "port-channel301",
            "port-channel302",
            "port-channel303",
            "port-channel300",
            "ethernet1/3.2",
            "loopback200",
            "vpc300",
            "vlan2001",
        ]

        rep_if_names = [
            "ethernet1/3.2",
            "ethernet1/1",
            "ethernet1/2",
            "ethernet3/2",
        ]

        ovr_if_names = ["port-channel150"]

        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"].lower() in del_if_names), True)

        for d in result["diff"][0]["replaced"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in rep_if_names), True
                )

        for d in result["diff"][0]["overridden"]:
            for intf in d["interfaces"]:
                self.assertEqual(
                    (intf["ifName"].lower() in ovr_if_names), True
                )

    # -------------------------- GENERAL --------------------------

    def test_dcnm_intf_gen_missing_ip_sn(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_pc_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_pc_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("pc_merged_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = []
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=True)

        self.assertEqual(
            result["msg"],
            "Fabric test_fabric missing on DCNM or does not have any switches",
        )
        self.assertEqual(result["failed"], True)

    def test_dcnm_intf_mixed_intf_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_mixed_configs")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("mixed_merged_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(result["changed"], True)

        self.assertEqual(len(result["diff"][0]["merged"]), 5)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["replaced"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 5)

    def test_dcnm_intf_bunched_intf_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_bunched_configs")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("bunched_merged_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(result["changed"], True)

        self.assertEqual(len(result["diff"][0]["merged"]), 10)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["replaced"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 10)

        if_names = [
            "port-channel300",
            "port-channel400",
            "port-channel301",
            "port-channel401",
            "ethernet1/14",
            "ethernet1/32",
            "ethernet1/22",
            "ethernet1/13",
            "vpc850",
            "vpc750",
        ]

        for d in result["diff"][0]["merged"]:
            for intf in d["interfaces"]:
                self.assertEqual((intf["ifName"].lower() in if_names), True)

    def test_dcnm_intf_type_missing_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_pc_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_pc_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("pc_type_missing_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=True)

        self.assertEqual(
            result["msg"],
            "<type> element, which is mandatory is missing in config",
        )
        self.assertEqual(result["failed"], True)

    def test_dcnm_intf_missing_state(self):

        self.config_data = loadPlaybookData("dcnm_intf_pc_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_pc_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("pc_state_missing_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(fabric="test_fabric", config=self.playbook_config)
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["replaced"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 1)

        if_names = ["port-channel300"]

        for d in result["diff"][0]["merged"]:
            for intf in d["interfaces"]:
                self.assertEqual((intf["ifName"].lower() in if_names), True)

    def test_dcnm_intf_missing_peer_members(self):

        self.config_data = loadPlaybookData("dcnm_intf_vpc_configs")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get(
            "vpc_members_missing_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")

        set_module_args(
            dict(
                fabric="test_fabric",
                state="merged",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["replaced"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 1)

        if_names = ["vpc751"]

        for d in result["diff"][0]["merged"]:
            for intf in d["interfaces"]:
                self.assertEqual((intf["ifName"].lower() in if_names), True)

    def test_dcnm_intf_query(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_query_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_query_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("query_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="query",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(result["changed"], False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["replaced"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 8)

    def test_dcnm_intf_merge_fabric_monitoring(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_pc_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_pc_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("pc_merged_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="fabric_monitoring",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(("is in Monitoring mode" in str(e)), True)
            self.assertEqual(("No changes are allowed on the fabric" in str(e)), True)

    def test_dcnm_intf_merge_unmanagable_switch(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_pc_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_pc_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("pc_unmanagable_merged_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get("mock_monitor_true_resp")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )

        result = None

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            self.assertEqual(result, None)
            self.assertEqual(("are not managable in Fabric" in str(e)), True)
            self.assertEqual(("No changes are allowed on these switches" in str(e)), True)
