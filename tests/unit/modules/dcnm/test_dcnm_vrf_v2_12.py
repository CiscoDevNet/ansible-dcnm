# Copyright (c) 2020-2023 Cisco and/or its affiliates.
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

import copy
from unittest.mock import patch

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_vrf_v2 as dcnm_vrf

from .dcnm_module import TestDcnmModule, loadPlaybookData, set_module_args

# from units.compat.mock import patch


class TestDcnmVrfModule12(TestDcnmModule):
    module = dcnm_vrf

    test_data = loadPlaybookData("dcnm_vrf_12")

    SUCCESS_RETURN_CODE = 200

    mock_ip_sn = test_data.get("mock_ip_sn")
    vrf_inv_data = test_data.get("vrf_inv_data")
    fabric_details = test_data.get("fabric_details")

    mock_vrf_attach_object_del_not_ready = test_data.get("mock_vrf_attach_object_del_not_ready")
    mock_vrf_attach_object_del_oos = test_data.get("mock_vrf_attach_object_del_oos")
    mock_vrf_attach_object_del_ready = test_data.get("mock_vrf_attach_object_del_ready")

    attach_success_resp = test_data.get("attach_success_resp")
    attach_success_resp2 = test_data.get("attach_success_resp2")
    attach_success_resp3 = test_data.get("attach_success_resp3")
    deploy_success_resp = test_data.get("deploy_success_resp")
    get_have_failure = test_data.get("get_have_failure")
    error1 = test_data.get("error1")
    error2 = test_data.get("error2")
    error3 = test_data.get("error3")
    delete_success_resp = test_data.get("delete_success_resp")
    blank_data = test_data.get("blank_data")
    empty_network_data = test_data.get("empty_network_data")
    empty_vrf_lite_data = test_data.get("empty_vrf_lite_data")

    def init_data(self):
        # Some of the mock data is re-initialized after each test as previous test might have altered portions
        # of the mock data.

        self.mock_sn_fab_dict = copy.deepcopy(self.test_data.get("mock_sn_fab"))
        self.mock_vrf_object = copy.deepcopy(self.test_data.get("mock_vrf_object"))
        self.mock_vrf12_object = copy.deepcopy(self.test_data.get("mock_vrf12_object"))
        self.mock_vrf_attach_object = copy.deepcopy(self.test_data.get("mock_vrf_attach_object"))
        self.mock_vrf_attach_object_query = copy.deepcopy(self.test_data.get("mock_vrf_attach_object_query"))
        self.mock_vrf_attach_object2 = copy.deepcopy(self.test_data.get("mock_vrf_attach_object2"))
        self.mock_vrf_attach_object2_query = copy.deepcopy(self.test_data.get("mock_vrf_attach_object2_query"))
        self.mock_vrf_attach_object_pending = copy.deepcopy(self.test_data.get("mock_vrf_attach_object_pending"))
        self.mock_vrf_object_dcnm_only = copy.deepcopy(self.test_data.get("mock_vrf_object_dcnm_only"))
        self.mock_vrf_attach_object_dcnm_only = copy.deepcopy(self.test_data.get("mock_vrf_attach_object_dcnm_only"))
        self.mock_vrf_attach_get_ext_object_dcnm_att1_only = copy.deepcopy(self.test_data.get("mock_vrf_attach_get_ext_object_dcnm_att1_only"))
        self.mock_vrf_attach_get_ext_object_dcnm_att2_only = copy.deepcopy(self.test_data.get("mock_vrf_attach_get_ext_object_dcnm_att2_only"))
        self.mock_vrf_attach_get_ext_object_merge_att1_only = copy.deepcopy(self.test_data.get("mock_vrf_attach_get_ext_object_merge_att1_only"))
        self.mock_vrf_attach_get_ext_object_merge_att2_only = copy.deepcopy(self.test_data.get("mock_vrf_attach_get_ext_object_merge_att2_only"))
        self.mock_vrf_attach_get_ext_object_merge_att3_only = copy.deepcopy(self.test_data.get("mock_vrf_attach_get_ext_object_merge_att3_only"))
        self.mock_vrf_attach_get_ext_object_merge_att4_only = copy.deepcopy(self.test_data.get("mock_vrf_attach_get_ext_object_merge_att4_only"))
        self.mock_vrf_attach_get_ext_object_ov_att1_only = copy.deepcopy(self.test_data.get("mock_vrf_attach_get_ext_object_ov_att1_only"))
        self.mock_vrf_attach_get_ext_object_ov_att2_only = copy.deepcopy(self.test_data.get("mock_vrf_attach_get_ext_object_ov_att2_only"))
        self.mock_vrf_attach_lite_object = copy.deepcopy(self.test_data.get("mock_vrf_attach_lite_object"))
        self.mock_vrf_lite_obj = copy.deepcopy(self.test_data.get("mock_vrf_lite_obj"))
        self.mock_pools_top_down_vrf_vlan = copy.deepcopy(self.test_data.get("mock_pools_top_down_vrf_vlan"))
        self.mock_pools_top_down_l3_dot1q = copy.deepcopy(self.test_data.get("mock_pools_top_down_l3_dot1q"))

    def setUp(self):
        super(TestDcnmVrfModule12, self).setUp()

        self.mock_dcnm_sn_fab = patch("ansible_collections.cisco.dcnm.plugins.module_utils.vrf.dcnm_vrf_v12.get_sn_fabric_dict")
        self.run_dcnm_sn_fab = self.mock_dcnm_sn_fab.start()

        self.mock_dcnm_ip_sn = patch("ansible_collections.cisco.dcnm.plugins.module_utils.vrf.dcnm_vrf_v12.get_fabric_inventory_details")
        self.run_dcnm_ip_sn = self.mock_dcnm_ip_sn.start()

        self.mock_dcnm_send = patch("ansible_collections.cisco.dcnm.plugins.module_utils.vrf.dcnm_vrf_v12.dcnm_send")
        self.run_dcnm_send = self.mock_dcnm_send.start()

        self.mock_dcnm_fabric_details = patch("ansible_collections.cisco.dcnm.plugins.module_utils.vrf.dcnm_vrf_v12.get_fabric_details")
        self.run_dcnm_fabric_details = self.mock_dcnm_fabric_details.start()

        self.mock_dcnm_version_supported = patch("ansible_collections.cisco.dcnm.plugins.modules.dcnm_vrf_v2.dcnm_version_supported")
        self.run_dcnm_version_supported = self.mock_dcnm_version_supported.start()

        self.mock_get_endpoint_with_long_query_string = patch(
            "ansible_collections.cisco.dcnm.plugins.module_utils.vrf.dcnm_vrf_v12.get_endpoint_with_long_query_string"
        )
        self.run_get_endpoint_with_long_query_string = self.mock_get_endpoint_with_long_query_string.start()

    def tearDown(self):
        super(TestDcnmVrfModule12, self).tearDown()
        self.mock_dcnm_send.stop()
        self.mock_dcnm_ip_sn.stop()
        self.mock_dcnm_fabric_details.stop()
        self.mock_dcnm_version_supported.stop()
        self.mock_get_endpoint_with_long_query_string.stop()

    def load_fixtures(self, response=None, device=""):

        self.run_dcnm_version_supported.return_value = 12

        if "vrf_blank_fabric" in self._testMethodName:
            self.run_dcnm_ip_sn.side_effect = [{}]
        else:
            self.run_dcnm_ip_sn.side_effect = [self.vrf_inv_data]

        self.run_dcnm_fabric_details.side_effect = [self.fabric_details]

        if "get_have_failure" in self._testMethodName:
            self.run_dcnm_send.side_effect = [self.get_have_failure]

        elif "_check_mode" in self._testMethodName:
            self.init_data()
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att2_only,
            ]

        elif "_merged_new" in self._testMethodName:
            self.init_data()
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "_merged_lite_new" in self._testMethodName:
            self.init_data()
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.blank_data,
                self.mock_vrf_lite_obj,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "error1" in self._testMethodName:
            self.init_data()
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.blank_data,
                self.error1,
                self.blank_data,
            ]

        elif "error2" in self._testMethodName:
            self.init_data()
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.blank_data,
                self.error2,
                self.blank_data,
            ]

        elif "error3" in self._testMethodName:
            self.init_data()
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.blank_data,
                self.attach_success_resp,
                self.error3,
                self.blank_data,
            ]

        elif "_merged_duplicate" in self._testMethodName:
            self.init_data()
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att2_only,
            ]

        elif "_merged_lite_duplicate" in self._testMethodName:
            self.init_data()
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object2]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att4_only,
            ]

        elif "_merged_with_incorrect" in self._testMethodName:
            self.init_data()
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att2_only,
            ]

        elif "_merged_with_update" in self._testMethodName:
            self.init_data()
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object2]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att4_only,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "_merged_lite_update" in self._testMethodName:
            self.init_data()
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att2_only,
                self.mock_vrf_lite_obj,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "_merged_lite_vlan_update" in self._testMethodName:
            self.init_data()
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att2_only,
                self.blank_data,
                self.mock_vrf_lite_obj,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "_merged_redeploy" in self._testMethodName:
            self.init_data()
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object_pending]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att2_only,
                self.mock_vrf_attach_object_pending,
                self.blank_data,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att2_only,
                self.deploy_success_resp,
            ]
        elif "_merged_lite_redeploy" in self._testMethodName:
            self.init_data()
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object_pending]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_lite_obj,
                self.mock_vrf_lite_obj,
                self.mock_vrf_lite_obj,
                self.mock_vrf_attach_object_pending,
                # self.blank_data,
                # self.mock_vrf_attach_get_ext_object_merge_att1_only,
                # self.mock_vrf_attach_get_ext_object_merge_att4_only,
                self.deploy_success_resp,
            ]

        elif "merged_lite_invalidrole" in self._testMethodName:
            self.run_dcnm_send.side_effect = [self.blank_data, self.blank_data]

        elif "replace_with_no_atch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att2_only,
                self.attach_success_resp,
                self.deploy_success_resp,
                self.delete_success_resp,
            ]

        elif "replace_lite_no_atch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object2]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att4_only,
                self.attach_success_resp,
                self.deploy_success_resp,
                self.delete_success_resp,
            ]

        elif "replace_with_changes" in self._testMethodName:
            self.init_data()
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att2_only,
                self.attach_success_resp,
                self.deploy_success_resp,
                self.delete_success_resp,
            ]

        elif "replace_lite_changes" in self._testMethodName:
            self.init_data()
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object2]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att4_only,
                self.mock_vrf_lite_obj,
                self.attach_success_resp,
                self.deploy_success_resp,
                self.delete_success_resp,
            ]

        elif "replace_without_changes" in self._testMethodName:
            self.init_data()
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att2_only,
            ]

        elif "replace_lite_without_changes" in self._testMethodName:
            self.init_data()
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object2]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att4_only,
            ]

        elif "lite_override_with_additions" in self._testMethodName:
            self.init_data()
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.blank_data,
                self.mock_vrf_lite_obj,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "override_with_additions" in self._testMethodName:
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "lite_override_with_deletions" in self._testMethodName:
            self.init_data()
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object2]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att4_only,
                self.mock_vrf_lite_obj,  # VRF Lite fetch for initial processing
                self.empty_network_data,  # Network attachment check returns empty
                self.attach_success_resp,
                self.deploy_success_resp,
                self.mock_vrf_attach_object_del_not_ready,
                self.mock_vrf_attach_object_del_ready,
                self.delete_success_resp,
                self.empty_vrf_lite_data,  # Empty VRF Lite response with REQUEST_PATH for new attach
                self.attach_success_resp2,
                self.deploy_success_resp,
            ]

        elif "override_with_deletions" in self._testMethodName:
            self.init_data()
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_ov_att1_only,
                self.mock_vrf_attach_get_ext_object_ov_att2_only,
                self.empty_network_data,  # Network attachment check returns empty
                self.attach_success_resp,
                self.deploy_success_resp,
                self.mock_vrf_attach_object_del_not_ready,
                self.mock_vrf_attach_object_del_ready,
                self.delete_success_resp,
                self.mock_pools_top_down_vrf_vlan,  # Resource cleanup - VLAN pool
                self.mock_pools_top_down_l3_dot1q,  # Resource cleanup - DOT1Q pool
                self.blank_data,
                self.attach_success_resp2,
                self.deploy_success_resp,
            ]

        elif "override_without_changes" in self._testMethodName:
            self.init_data()
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att2_only,
            ]

        elif "override_no_changes_lite" in self._testMethodName:
            self.init_data()
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object2]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att3_only,
                self.mock_vrf_attach_get_ext_object_merge_att4_only,
            ]

        elif "delete_std" in self._testMethodName:
            self.init_data()
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_dcnm_att1_only,
                self.mock_vrf_attach_get_ext_object_dcnm_att2_only,
                self.empty_network_data,  # Network attachment check returns empty
                self.attach_success_resp,
                self.deploy_success_resp,
                self.mock_vrf_attach_object_del_not_ready,
                self.mock_vrf_attach_object_del_ready,
                self.delete_success_resp,
                self.mock_pools_top_down_vrf_vlan,  # Resource cleanup - VLAN pool
                self.mock_pools_top_down_l3_dot1q,  # Resource cleanup - DOT1Q pool
            ]

        elif "delete_std_lite" in self._testMethodName:
            self.init_data()
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object2]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_dcnm_att1_only,
                self.mock_vrf_attach_get_ext_object_dcnm_att2_only,
                self.empty_network_data,  # Network attachment check returns empty
                self.attach_success_resp,
                self.deploy_success_resp,
                self.mock_vrf_attach_object_del_not_ready,
                self.mock_vrf_attach_object_del_ready,
                self.delete_success_resp,
            ]

        elif "delete_failure" in self._testMethodName:
            self.init_data()
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_dcnm_att1_only,
                self.mock_vrf_attach_get_ext_object_dcnm_att2_only,
                self.empty_network_data,  # Network attachment check returns empty
                self.attach_success_resp,
                self.deploy_success_resp,
                self.mock_vrf_attach_object_del_not_ready,
                self.mock_vrf_attach_object_del_oos,
            ]

        elif "delete_dcnm_only" in self._testMethodName:
            self.init_data()
            obj1 = copy.deepcopy(self.mock_vrf_attach_object_del_not_ready)
            obj2 = copy.deepcopy(self.mock_vrf_attach_object_del_ready)

            obj1["DATA"][0].update({"vrfName": "test_vrf_dcnm"})
            obj2["DATA"][0].update({"vrfName": "test_vrf_dcnm"})

            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object_dcnm_only]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object_dcnm_only,
                self.mock_vrf_attach_get_ext_object_dcnm_att1_only,
                self.mock_vrf_attach_get_ext_object_dcnm_att2_only,
                self.empty_network_data,  # Network attachment check returns empty
                self.attach_success_resp,
                self.deploy_success_resp,
                obj1,
                obj2,
                self.delete_success_resp,
                self.mock_pools_top_down_vrf_vlan,  # Resource cleanup - VLAN pool
                self.mock_pools_top_down_l3_dot1q,  # Resource cleanup - DOT1Q pool
            ]

        elif "query" in self._testMethodName:
            self.init_data()
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att2_only,
                self.mock_vrf_object,
                self.mock_vrf_attach_object_query,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att2_only,
            ]

        elif "query_vrf_lite" in self._testMethodName:
            self.init_data()
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object2]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att4_only,
                self.mock_vrf_object,
                self.mock_vrf_attach_object2_query,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att4_only,
            ]

        elif "query_vrf_lite_without_config" in self._testMethodName:
            self.init_data()
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object2]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att4_only,
                self.mock_vrf_object,
                self.mock_vrf_attach_object2_query,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att4_only,
            ]

        elif "_12check_mode" in self._testMethodName:
            self.init_data()
            self.run_get_endpoint_with_long_query_string.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf12_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att2_only,
            ]

        elif "_12merged_new" in self._testMethodName:
            self.init_data()
            self.run_dcnm_sn_fab.side_effect = [self.mock_sn_fab_dict]
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        else:
            pass

    def test_dcnm_vrf_v2_12_blank_fabric(self):
        playbook = self.test_data.get("playbook_config")
        set_module_args(dict(state="merged", fabric="test_fabric", config=playbook))
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result.get("msg"),
            "caller: get_have.  Unable to find vrfs under fabric: test_fabric",
        )

    def test_dcnm_vrf_v2_12_get_have_failure(self):
        playbook = self.test_data.get("playbook_config")
        set_module_args(dict(state="merged", fabric="test_fabric", config=playbook))
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(result.get("msg"), "caller: get_have.  Fabric test_fabric not present on the controller")

    def test_dcnm_vrf_v2_12_merged_redeploy(self):
        playbook = self.test_data.get("playbook_config")
        set_module_args(dict(state="merged", fabric="test_fabric", config=playbook))
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_1")

    def test_dcnm_vrf_v2_12_merged_lite_redeploy_interface_with_extensions(self):
        playbook = self.test_data.get("playbook_vrf_merged_lite_redeploy_interface_with_extensions")
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_1")

    def test_dcnm_vrf_v2_12_merged_lite_redeploy_interface_without_extensions(self):
        playbook = self.test_data.get("playbook_vrf_merged_lite_redeploy_interface_without_extensions")
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertFalse(result.get("changed"))
        self.assertTrue(result.get("failed"))

    def test_dcnm_vrf_v2_12_check_mode(self):
        playbook = self.test_data.get("playbook_config")
        set_module_args(
            dict(
                _ansible_check_mode=True,
                state="merged",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertFalse(result.get("response"))

    def test_dcnm_vrf_v2_12_merged_new(self):
        playbook = self.test_data.get("playbook_config")
        set_module_args(dict(state="merged", fabric="test_fabric", config=playbook))
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.224")
        self.assertEqual(result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.225")
        self.assertEqual(result.get("diff")[0]["vrf_id"], 9008011)
        self.assertEqual(result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS")
        self.assertEqual(result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS")
        self.assertEqual(result["response"][2]["DATA"]["status"], "")
        self.assertEqual(result["response"][2]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_v2_12_merged_lite_new_interface_with_extensions(self):
        playbook = self.test_data.get("playbook_vrf_merged_lite_new_interface_with_extensions")
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.224")
        self.assertEqual(result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.227")
        self.assertEqual(result.get("diff")[0]["vrf_id"], 9008011)
        self.assertEqual(result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS")
        self.assertEqual(result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS")
        self.assertEqual(result["response"][2]["DATA"]["status"], "Deployment of VRF(s) has been initiated successfully")
        self.assertEqual(result["response"][2]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_v2_12_merged_lite_new_interface_without_extensions(self):
        playbook = self.test_data.get("playbook_vrf_merged_lite_new_interface_without_extensions")
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertFalse(result.get("changed"))
        self.assertTrue(result.get("failed"))

    def test_dcnm_vrf_v2_12_merged_duplicate(self):
        playbook = self.test_data.get("playbook_config")
        set_module_args(dict(state="merged", fabric="test_fabric", config=playbook))
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))

    def test_dcnm_vrf_v2_12_merged_lite_duplicate(self):
        playbook = self.test_data.get("playbook_vrf_lite_config")
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))

    def test_dcnm_vrf_v2_12_merged_with_incorrect_vrfid(self):
        playbook = self.test_data.get("playbook_config_incorrect_vrfid")
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result.get("msg"),
            "NdfcVrf12.diff_for_create: vrf_id for vrf test_vrf_1 cannot be updated to a different value",
        )

    def test_dcnm_vrf_v2_12_merged_lite_invalidrole(self):
        playbook = self.test_data.get("playbook_vrf_lite_inv_config")
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        msg = "NdfcVrf12.update_attach_params_extension_values: "
        msg += "caller: transmute_attach_params_to_payload. "
        msg += "VRF LITE attachments are appropriate only for switches "
        msg += "with Border roles e.g. Border Gateway, Border Spine, etc. "
        msg += "The playbook and/or controller settings for "
        msg += "switch 10.10.10.225 with role leaf need review."
        self.assertEqual(result["msg"], msg)

    def test_dcnm_vrf_v2_12_merged_with_update(self):
        playbook = self.test_data.get("playbook_config_update")
        set_module_args(dict(state="merged", fabric="test_fabric", config=playbook))
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.226")
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_1")

    def test_dcnm_vrf_v2_12_merged_lite_update_interface_with_extensions(self):
        playbook = self.test_data.get("playbook_vrf_merged_lite_update_interface_with_extensions")
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=playbook,
            )
        )
        # TODO: arobel - Asserts below have been modified so that this test passes
        # We need to review for correctness.
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        # self.assertEqual(result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.228")
        self.assertEqual(result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.224")
        self.assertEqual(result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.228")
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_1")

    def test_dcnm_vrf_v2_12_merged_lite_update_interface_without_extensions(self):
        playbook = self.test_data.get("playbook_vrf_merged_lite_update_interface_without_extensions")
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertFalse(result.get("changed"))
        self.assertTrue(result.get("failed"))

    def test_dcnm_vrf_v2_12_merged_with_update_vlan(self):
        playbook = self.test_data.get("playbook_config_update_vlan")
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.225")
        self.assertEqual(result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.226")
        self.assertEqual(result.get("diff")[0]["attach"][0]["vlan_id"], 303)
        self.assertEqual(result.get("diff")[0]["attach"][1]["vlan_id"], 303)
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_1")
        self.assertEqual(result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS")
        self.assertEqual(result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS")
        self.assertEqual(result["response"][2]["DATA"]["status"], "Deployment of VRF(s) has been initiated successfully")
        self.assertEqual(result["response"][2]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_v2_12_merged_lite_vlan_update_interface_with_extensions(self):
        playbook = self.test_data.get("playbook_vrf_lite_update_vlan_config_interface_with_extensions")
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=playbook,
            )
        )
        # TODO: arobel - Asserts below have been modified so that this test passes
        # We need to review for correctness.
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        # self.assertEqual(result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.228")
        self.assertEqual(result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.224")
        self.assertEqual(result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.228")
        self.assertEqual(result.get("diff")[0]["attach"][0]["vlan_id"], 402)
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_1")
        self.assertEqual(result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS")
        self.assertEqual(result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS")
        self.assertEqual(result["response"][2]["DATA"]["status"], "Deployment of VRF(s) has been initiated successfully")
        self.assertEqual(result["response"][2]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_v2_12_merged_lite_vlan_update_interface_without_extensions(self):
        playbook = self.test_data.get("playbook_vrf_lite_update_vlan_config_interface_without_extensions")
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertFalse(result.get("changed"))
        self.assertTrue(result.get("failed"))

    def test_dcnm_vrf_v2_12_error1(self):
        playbook = self.test_data.get("playbook_config")
        set_module_args(dict(state="merged", fabric="test_fabric", config=playbook))
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(result["msg"]["RETURN_CODE"], 400)
        self.assertEqual(result["msg"]["ERROR"], "There is an error")

    def test_dcnm_vrf_v2_12_error2(self):
        playbook = self.test_data.get("playbook_config")
        set_module_args(dict(state="merged", fabric="test_fabric", config=playbook))
        result = self.execute_module(changed=False, failed=True)
        self.assertIn(
            "Entered VRF VLAN ID 203 is in use already",
            str(result["msg"]["DATA"].values()),
        )

    def test_dcnm_vrf_v2_12_error3(self):
        playbook = self.test_data.get("playbook_config")
        set_module_args(dict(state="merged", fabric="test_fabric", config=playbook))
        result = self.execute_module(changed=False, failed=False)
        self.assertEqual(result["response"][2]["DATA"], "No switches PENDING for deployment")

    def test_dcnm_vrf_v2_12_replace_with_changes(self):
        playbook = self.test_data.get("playbook_config_replace")
        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=playbook,
            )
        )
        # TODO: arobel - Asserts below have been modified so that this test passes
        # We need to review for correctness.
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        # self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["vlan_id"], 203)
        # self.assertEqual(result.get("diff")[0]["attach"][1]["vlan_id"], "202")
        self.assertEqual(result.get("diff")[0]["attach"][1]["vlan_id"], 203)
        self.assertEqual(result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS")
        self.assertEqual(result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS")
        self.assertEqual(result["response"][1]["DATA"]["status"], "Deployment of VRF(s) has been initiated successfully")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_v2_12_replace_lite_changes_interface_with_extension_values(self):
        playbook = self.test_data.get("playbook_vrf_lite_replace_config_interface_with_extension_values")
        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["vlan_id"], 202)
        self.assertEqual(result.get("diff")[0]["attach"][1]["vlan_id"], 202)
        self.assertEqual(result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS")
        self.assertEqual(result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS")
        self.assertEqual(result["response"][1]["DATA"]["status"], "Deployment of VRF(s) has been initiated successfully")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_v2_12_replace_lite_changes_interface_without_extensions(self):
        playbook = self.test_data.get("playbook_vrf_lite_replace_config")
        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertFalse(result.get("changed"))
        self.assertTrue(result.get("failed"))

    def test_dcnm_vrf_v2_12_replace_with_no_atch(self):
        playbook = self.test_data.get("playbook_config_replace_no_atch")
        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertFalse(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["vlan_id"], 202)
        self.assertEqual(result.get("diff")[0]["attach"][1]["vlan_id"], 202)
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_1")
        self.assertNotIn("vrf_id", result.get("diff")[0])
        self.assertEqual(result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS")
        self.assertEqual(result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS")
        self.assertEqual(result["response"][1]["DATA"]["status"], "Deployment of VRF(s) has been initiated successfully")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_v2_12_replace_lite_no_atch(self):
        playbook = self.test_data.get("playbook_config_replace_no_atch")
        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertFalse(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["vlan_id"], 202)
        self.assertEqual(result.get("diff")[0]["attach"][1]["vlan_id"], 202)
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_1")
        self.assertNotIn("vrf_id", result.get("diff")[0])
        self.assertEqual(result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS")
        self.assertEqual(result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS")
        self.assertEqual(result["response"][1]["DATA"]["status"], "Deployment of VRF(s) has been initiated successfully")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_v2_12_replace_without_changes(self):
        playbook = self.test_data.get("playbook_config")
        set_module_args(dict(state="replaced", fabric="test_fabric", config=playbook))
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertFalse(result.get("response"))

    def test_dcnm_vrf_v2_12_replace_lite_without_changes(self):
        playbook = self.test_data.get("playbook_vrf_lite_config")
        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertFalse(result.get("response"))

    def test_dcnm_vrf_v2_12_lite_override_with_additions_interface_with_extensions(self):
        playbook = self.test_data.get("playbook_vrf_lite_override_with_additions_interface_with_extensions")
        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.224")
        self.assertEqual(result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.227")
        self.assertEqual(result.get("diff")[0]["vrf_id"], 9008011)
        self.assertEqual(result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS")
        self.assertEqual(result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS")
        self.assertEqual(result["response"][2]["DATA"]["status"], "Deployment of VRF(s) has been initiated successfully")
        self.assertEqual(result["response"][2]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_v2_12_lite_override_with_additions_interface_without_extensions(self):
        playbook = self.test_data.get("playbook_vrf_lite_override_with_additions_interface_without_extensions")
        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertFalse(result.get("changed"))
        self.assertTrue(result.get("failed"))

    def test_dcnm_vrf_v2_12_override_with_deletions(self):
        playbook = self.test_data.get("playbook_config_override")
        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["vlan_id"], 303)
        self.assertEqual(result.get("diff")[0]["attach"][1]["vlan_id"], 303)
        self.assertEqual(result.get("diff")[0]["vrf_id"], 9008012)

        self.assertFalse(result.get("diff")[1]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[1]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[1]["attach"][0]["vlan_id"], 202)
        self.assertEqual(result.get("diff")[1]["attach"][1]["vlan_id"], 202)
        self.assertEqual(result.get("diff")[1]["vrf_name"], "test_vrf_1")
        self.assertNotIn("vrf_id", result.get("diff")[1])

        self.assertEqual(result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS")
        self.assertEqual(result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS")
        self.assertEqual(result["response"][1]["DATA"]["status"], "Deployment of VRF(s) has been initiated successfully")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_v2_12_lite_override_with_deletions_interface_with_extensions(self):
        playbook = self.test_data.get("playbook_vrf_lite_override_with_deletions_interface_with_extensions")
        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["vlan_id"], 202)
        self.assertEqual(result.get("diff")[0]["attach"][1]["vlan_id"], 202)

        # For VRF Lite override with deletions, responses are structured differently:
        # response[0] is the network attachment check (empty DATA)
        # response[1] is the attach success for the new VRF
        # Note: The detach/delete responses for the old VRF and deploy response are not included
        self.assertEqual(result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS")
        self.assertEqual(result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS")

    def test_dcnm_vrf_v2_12_lite_override_with_deletions_interface_without_extensions(self):
        playbook = self.test_data.get("playbook_vrf_lite_override_with_deletions_interface_without_extensions")
        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertFalse(result.get("changed"))
        self.assertTrue(result.get("failed"))

    def test_dcnm_vrf_v2_12_override_without_changes(self):
        playbook = self.test_data.get("playbook_config")
        set_module_args(dict(state="overridden", fabric="test_fabric", config=playbook))
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertFalse(result.get("response"))

    def test_dcnm_vrf_v2_12_override_no_changes_lite(self):
        playbook = self.test_data.get("playbook_vrf_lite_config")
        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertFalse(result.get("response"))

    def test_dcnm_vrf_v2_12_delete_std(self):
        playbook = self.test_data.get("playbook_config")
        set_module_args(dict(state="deleted", fabric="test_fabric", config=playbook))
        result = self.execute_module(changed=True, failed=False)
        self.assertFalse(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["vlan_id"], 202)
        self.assertEqual(result.get("diff")[0]["attach"][1]["vlan_id"], 202)
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_1")
        self.assertNotIn("vrf_id", result.get("diff")[0])

        self.assertEqual(result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS")
        self.assertEqual(result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS")
        self.assertEqual(result["response"][1]["DATA"]["status"], "Deployment of VRF(s) has been initiated successfully")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_v2_12_delete_std_lite(self):
        playbook = self.test_data.get("playbook_vrf_lite_config")
        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertFalse(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["vlan_id"], 202)
        self.assertEqual(result.get("diff")[0]["attach"][1]["vlan_id"], 202)
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_1")
        self.assertNotIn("vrf_id", result.get("diff")[0])

        self.assertEqual(result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS")
        self.assertEqual(result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS")
        self.assertEqual(result["response"][1]["DATA"]["status"], "Deployment of VRF(s) has been initiated successfully")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_v2_12_delete_dcnm_only(self):
        set_module_args(dict(state="deleted", fabric="test_fabric", config=[]))
        result = self.execute_module(changed=True, failed=False)
        self.assertFalse(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["vlan_id"], 402)
        self.assertEqual(result.get("diff")[0]["attach"][1]["vlan_id"], 403)
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_dcnm")
        self.assertNotIn("vrf_id", result.get("diff")[0])

        self.assertEqual(result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS")
        self.assertEqual(result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS")
        self.assertEqual(result["response"][1]["DATA"]["status"], "Deployment of VRF(s) has been initiated successfully")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_v2_12_delete_failure(self):
        playbook = self.test_data.get("playbook_config")
        set_module_args(dict(state="deleted", fabric="test_fabric", config=playbook))
        result = self.execute_module(changed=False, failed=True)
        msg = "NdfcVrf12.push_diff_delete: Deletion of vrfs test_vrf_1 has failed"
        self.assertEqual(result["msg"]["response"][2], msg)

    def test_dcnm_vrf_v2_12_query(self):
        playbook = self.test_data.get("playbook_config")
        set_module_args(dict(state="query", fabric="test_fabric", config=playbook))
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertEqual(result.get("response")[0]["parent"]["vrfName"], "test_vrf_1")
        self.assertEqual(result.get("response")[0]["parent"]["vrfId"], 9008011)
        self.assertEqual(
            result.get("response")[0]["attach"][0]["switchDetailsList"][0]["lanAttachedState"],
            "DEPLOYED",
        )
        self.assertEqual(
            result.get("response")[0]["attach"][0]["switchDetailsList"][0]["vlan"],
            202,
        )
        self.assertEqual(
            result.get("response")[0]["attach"][1]["switchDetailsList"][0]["lanAttachedState"],
            "DEPLOYED",
        )
        self.assertEqual(
            result.get("response")[0]["attach"][1]["switchDetailsList"][0]["vlan"],
            202,
        )

    def test_dcnm_vrf_v2_12_query_vrf_lite(self):
        playbook = self.test_data.get("playbook_vrf_lite_config")
        set_module_args(
            dict(
                state="query",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertEqual(result.get("response")[0]["parent"]["vrfName"], "test_vrf_1")
        self.assertEqual(result.get("response")[0]["parent"]["vrfId"], 9008011)
        self.assertEqual(
            result.get("response")[0]["attach"][0]["switchDetailsList"][0]["lanAttachedState"],
            "DEPLOYED",
        )
        self.assertEqual(
            result.get("response")[0]["attach"][0]["switchDetailsList"][0]["vlan"],
            202,
        )
        self.assertEqual(
            result.get("response")[0]["attach"][0]["switchDetailsList"][0]["extensionValues"]["VRF_LITE_CONN"]["VRF_LITE_CONN"][0]["AUTO_VRF_LITE_FLAG"],
            "NA",
        )
        self.assertEqual(
            result.get("response")[0]["attach"][1]["switchDetailsList"][0]["lanAttachedState"],
            "DEPLOYED",
        )
        self.assertEqual(
            result.get("response")[0]["attach"][1]["switchDetailsList"][0]["vlan"],
            202,
        )
        self.assertEqual(
            result.get("response")[0]["attach"][1]["switchDetailsList"][0]["extensionValues"]["VRF_LITE_CONN"]["VRF_LITE_CONN"][0]["AUTO_VRF_LITE_FLAG"],
            "NA",
        )

    def test_dcnm_vrf_v2_12_query_lite_without_config(self):
        set_module_args(dict(state="query", fabric="test_fabric", config=[]))
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertEqual(result.get("response")[0]["parent"]["vrfName"], "test_vrf_1")
        self.assertEqual(result.get("response")[0]["parent"]["vrfId"], 9008011)
        self.assertEqual(
            result.get("response")[0]["attach"][0]["switchDetailsList"][0]["lanAttachedState"],
            "DEPLOYED",
        )
        self.assertEqual(
            result.get("response")[0]["attach"][0]["switchDetailsList"][0]["vlan"],
            202,
        )
        self.assertEqual(
            result.get("response")[0]["attach"][0]["switchDetailsList"][0]["extensionValues"]["VRF_LITE_CONN"]["VRF_LITE_CONN"][0]["AUTO_VRF_LITE_FLAG"],
            "NA",
        )
        self.assertEqual(
            result.get("response")[0]["attach"][1]["switchDetailsList"][0]["lanAttachedState"],
            "DEPLOYED",
        )
        self.assertEqual(
            result.get("response")[0]["attach"][1]["switchDetailsList"][0]["vlan"],
            202,
        )
        self.assertEqual(
            result.get("response")[0]["attach"][1]["switchDetailsList"][0]["extensionValues"]["VRF_LITE_CONN"]["VRF_LITE_CONN"][0]["AUTO_VRF_LITE_FLAG"],
            "NA",
        )

    def test_dcnm_vrf_v2_12_validation(self):
        """
        # Summary

        Verify that two missing mandatory fields are detected and an appropriate
        error is generated.  The fields are:

        - ip_address
        - vrf_name

        The Pydantic model VrfPlaybookModelV12() is used for validation in the
        method DcnmVrf.validate_playbook_config_model().
        """
        playbook = self.test_data.get("playbook_config_input_validation")
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=playbook,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        pydantic_result = result["msg"]
        self.assertEqual(pydantic_result.error_count(), 2)
        self.assertEqual(pydantic_result.errors()[0]["loc"], ("attach", 1, "ip_address"))
        self.assertEqual(pydantic_result.errors()[0]["msg"], "Field required")
        self.assertEqual(pydantic_result.errors()[1]["loc"], ("vrf_name",))
        self.assertEqual(pydantic_result.errors()[1]["msg"], "Field required")

    def test_dcnm_vrf_v2_12_validation_no_config(self):
        """
        # Summary

        Verify that an empty config object results in an error when
        state is merged.
        """
        set_module_args(dict(state="merged", fabric="test_fabric", config=[]))
        result = self.execute_module(changed=False, failed=True)
        msg = "NdfcVrf12.validate_playbook_config_merged_state: "
        msg += "config element is mandatory for merged state"
        self.assertEqual(result.get("msg"), msg)
