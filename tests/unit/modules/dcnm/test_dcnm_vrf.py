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

from unittest.mock import patch

# from units.compat.mock import patch

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_vrf
from .dcnm_module import TestDcnmModule, set_module_args, loadPlaybookData

import copy


class TestDcnmVrfModule(TestDcnmModule):

    module = dcnm_vrf

    test_data = loadPlaybookData("dcnm_vrf")

    SUCCESS_RETURN_CODE = 200

    version = 11

    mock_ip_sn = test_data.get("mock_ip_sn")
    vrf_inv_data = test_data.get("vrf_inv_data")
    fabric_details = test_data.get("fabric_details")
    playbook_config_input_validation = test_data.get("playbook_config_input_validation")
    playbook_config = test_data.get("playbook_config")
    playbook_config_update = test_data.get("playbook_config_update")
    playbook_vrf_lite_config = test_data.get("playbook_vrf_lite_config")
    playbook_vrf_lite_update_config = test_data.get("playbook_vrf_lite_update_config")
    playbook_vrf_lite_update_vlan_config = test_data.get(
        "playbook_vrf_lite_update_vlan_config"
    )
    playbook_vrf_lite_inv_config = test_data.get("playbook_vrf_lite_inv_config")
    playbook_vrf_lite_replace_config = test_data.get("playbook_vrf_lite_replace_config")
    playbook_config_update_vlan = test_data.get("playbook_config_update_vlan")
    playbook_config_override = test_data.get("playbook_config_override")
    playbook_config_incorrect_vrfid = test_data.get("playbook_config_incorrect_vrfid")
    playbook_config_replace = test_data.get("playbook_config_replace")
    playbook_config_replace_no_atch = test_data.get("playbook_config_replace_no_atch")
    mock_vrf_attach_object_del_not_ready = test_data.get(
        "mock_vrf_attach_object_del_not_ready"
    )
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

    def init_data(self):
        # Some of the mock data is re-initialized after each test as previous test might have altered portions
        # of the mock data.

        self.mock_vrf_object = copy.deepcopy(self.test_data.get("mock_vrf_object"))
        self.mock_vrf12_object = copy.deepcopy(self.test_data.get("mock_vrf12_object"))
        self.mock_vrf_attach_object = copy.deepcopy(
            self.test_data.get("mock_vrf_attach_object")
        )
        self.mock_vrf_attach_object_query = copy.deepcopy(
            self.test_data.get("mock_vrf_attach_object_query")
        )
        self.mock_vrf_attach_object2 = copy.deepcopy(
            self.test_data.get("mock_vrf_attach_object2")
        )
        self.mock_vrf_attach_object2_query = copy.deepcopy(
            self.test_data.get("mock_vrf_attach_object2_query")
        )
        self.mock_vrf_attach_object_pending = copy.deepcopy(
            self.test_data.get("mock_vrf_attach_object_pending")
        )
        self.mock_vrf_object_dcnm_only = copy.deepcopy(
            self.test_data.get("mock_vrf_object_dcnm_only")
        )
        self.mock_vrf_attach_object_dcnm_only = copy.deepcopy(
            self.test_data.get("mock_vrf_attach_object_dcnm_only")
        )
        self.mock_vrf_attach_get_ext_object_dcnm_att1_only = copy.deepcopy(
            self.test_data.get("mock_vrf_attach_get_ext_object_dcnm_att1_only")
        )
        self.mock_vrf_attach_get_ext_object_dcnm_att2_only = copy.deepcopy(
            self.test_data.get("mock_vrf_attach_get_ext_object_dcnm_att2_only")
        )
        self.mock_vrf_attach_get_ext_object_merge_att1_only = copy.deepcopy(
            self.test_data.get("mock_vrf_attach_get_ext_object_merge_att1_only")
        )
        self.mock_vrf_attach_get_ext_object_merge_att2_only = copy.deepcopy(
            self.test_data.get("mock_vrf_attach_get_ext_object_merge_att2_only")
        )
        self.mock_vrf_attach_get_ext_object_merge_att3_only = copy.deepcopy(
            self.test_data.get("mock_vrf_attach_get_ext_object_merge_att3_only")
        )
        self.mock_vrf_attach_get_ext_object_merge_att4_only = copy.deepcopy(
            self.test_data.get("mock_vrf_attach_get_ext_object_merge_att4_only")
        )
        self.mock_vrf_attach_get_ext_object_ov_att1_only = copy.deepcopy(
            self.test_data.get("mock_vrf_attach_get_ext_object_ov_att1_only")
        )
        self.mock_vrf_attach_get_ext_object_ov_att2_only = copy.deepcopy(
            self.test_data.get("mock_vrf_attach_get_ext_object_ov_att2_only")
        )
        self.mock_vrf_attach_lite_object = copy.deepcopy(
            self.test_data.get("mock_vrf_attach_lite_object")
        )
        self.mock_vrf_lite_obj = copy.deepcopy(self.test_data.get("mock_vrf_lite_obj"))

    def setUp(self):
        super(TestDcnmVrfModule, self).setUp()

        self.mock_dcnm_ip_sn = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_vrf.get_fabric_inventory_details"
        )
        self.run_dcnm_ip_sn = self.mock_dcnm_ip_sn.start()

        self.mock_dcnm_send = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_vrf.dcnm_send"
        )
        self.run_dcnm_send = self.mock_dcnm_send.start()

        self.mock_dcnm_fabric_details = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_vrf.get_fabric_details"
        )
        self.run_dcnm_fabric_details = self.mock_dcnm_fabric_details.start()

        self.mock_dcnm_version_supported = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_vrf.dcnm_version_supported"
        )
        self.run_dcnm_version_supported = self.mock_dcnm_version_supported.start()

        self.mock_dcnm_get_url = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_vrf.dcnm_get_url"
        )
        self.run_dcnm_get_url = self.mock_dcnm_get_url.start()

    def tearDown(self):
        super(TestDcnmVrfModule, self).tearDown()
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

        if "vrf_blank_fabric" in self._testMethodName:
            self.run_dcnm_ip_sn.side_effect = [{}]
        else:
            self.run_dcnm_ip_sn.side_effect = [self.vrf_inv_data]

        self.run_dcnm_fabric_details.side_effect = [self.fabric_details]

        if "get_have_failure" in self._testMethodName:
            self.run_dcnm_send.side_effect = [self.get_have_failure]

        elif "_check_mode" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att2_only,
            ]

        elif "_merged_new" in self._testMethodName:
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "_merged_lite_new" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.blank_data,
                self.mock_vrf_lite_obj,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "error1" in self._testMethodName:
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.blank_data,
                self.error1,
                self.blank_data,
            ]

        elif "error2" in self._testMethodName:
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.blank_data,
                self.error2,
                self.blank_data,
            ]

        elif "error3" in self._testMethodName:
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.blank_data,
                self.attach_success_resp,
                self.error3,
                self.blank_data,
            ]

        elif "_merged_duplicate" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att2_only,
            ]

        elif "_merged_lite_duplicate" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object2]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att4_only,
            ]

        elif "_merged_with_incorrect" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att2_only,
            ]

        elif "_merged_with_update" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object2]
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
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object]
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
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object]
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
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_object_pending,
                self.blank_data,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att2_only,
                self.deploy_success_resp,
            ]
        elif "_merged_lite_redeploy" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_lite_obj,
                self.mock_vrf_attach_object_pending,
                self.blank_data,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att4_only,
                self.deploy_success_resp,
            ]

        elif "merged_lite_invalidrole" in self._testMethodName:
            self.run_dcnm_send.side_effect = [self.blank_data, self.blank_data]

        elif "replace_with_no_atch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object]
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
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object2]
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
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object]
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
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object2]
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
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att2_only,
            ]

        elif "replace_lite_without_changes" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object2]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att4_only,
            ]

        elif "lite_override_with_additions" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.blank_data,
                self.mock_vrf_lite_obj,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "override_with_additions" in self._testMethodName:
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "lite_override_with_deletions" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object2]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att4_only,
                self.mock_vrf_lite_obj,
                self.attach_success_resp,
                self.deploy_success_resp,
                self.mock_vrf_attach_object_del_not_ready,
                self.mock_vrf_attach_object_del_ready,
                self.delete_success_resp,
                self.blank_data,
                self.attach_success_resp2,
                self.deploy_success_resp,
            ]

        elif "override_with_deletions" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_ov_att1_only,
                self.mock_vrf_attach_get_ext_object_ov_att2_only,
                self.attach_success_resp,
                self.deploy_success_resp,
                self.mock_vrf_attach_object_del_not_ready,
                self.mock_vrf_attach_object_del_ready,
                self.delete_success_resp,
                self.blank_data,
                self.attach_success_resp2,
                self.deploy_success_resp,
            ]

        elif "override_without_changes" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att2_only,
            ]

        elif "override_no_changes_lite" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object2]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_merge_att3_only,
                self.mock_vrf_attach_get_ext_object_merge_att4_only,
            ]

        elif "delete_std" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_dcnm_att1_only,
                self.mock_vrf_attach_get_ext_object_dcnm_att2_only,
                self.attach_success_resp,
                self.deploy_success_resp,
                self.mock_vrf_attach_object_del_not_ready,
                self.mock_vrf_attach_object_del_ready,
                self.delete_success_resp,
            ]

        elif "delete_std_lite" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object2]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_dcnm_att1_only,
                self.mock_vrf_attach_get_ext_object_dcnm_att4_only,
                self.attach_success_resp,
                self.deploy_success_resp,
                self.mock_vrf_attach_object_del_not_ready,
                self.mock_vrf_attach_object_del_ready,
                self.delete_success_resp,
            ]

        elif "delete_failure" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_vrf_attach_get_ext_object_dcnm_att1_only,
                self.mock_vrf_attach_get_ext_object_dcnm_att2_only,
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

            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object_dcnm_only]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object_dcnm_only,
                self.mock_vrf_attach_get_ext_object_dcnm_att1_only,
                self.mock_vrf_attach_get_ext_object_dcnm_att2_only,
                self.attach_success_resp,
                self.deploy_success_resp,
                obj1,
                obj2,
                self.delete_success_resp,
            ]

        elif "query" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object]
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
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object2]
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
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object2]
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
            self.run_dcnm_get_url.side_effect = [self.mock_vrf_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf12_object,
                self.mock_vrf_attach_get_ext_object_merge_att1_only,
                self.mock_vrf_attach_get_ext_object_merge_att2_only,
            ]

        elif "_12merged_new" in self._testMethodName:
            self.run_dcnm_send.side_effect = [
                self.blank_data,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        else:
            pass

    def test_dcnm_vrf_blank_fabric(self):
        set_module_args(
            dict(state="merged", fabric="test_fabric", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result.get("msg"),
            "Fabric test_fabric missing on DCNM or does not have any switches",
        )

    def test_dcnm_vrf_get_have_failure(self):
        set_module_args(
            dict(state="merged", fabric="test_fabric", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(result.get("msg"), "Fabric test_fabric not present on DCNM")

    def test_dcnm_vrf_merged_redeploy(self):
        set_module_args(
            dict(state="merged", fabric="test_fabric", config=self.playbook_config)
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_1")

    def test_dcnm_vrf_merged_lite_redeploy(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_vrf_lite_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_1")

    def test_dcnm_vrf_check_mode(self):
        set_module_args(
            dict(
                _ansible_check_mode=True,
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertFalse(result.get("response"))

    def test_dcnm_vrf_merged_new(self):
        set_module_args(
            dict(state="merged", fabric="test_fabric", config=self.playbook_config)
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.224"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.225"
        )
        self.assertEqual(result.get("diff")[0]["vrf_id"], 9008011)
        self.assertEqual(
            result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][2]["DATA"]["status"], "")
        self.assertEqual(result["response"][2]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_merged_lite_new(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_vrf_lite_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.224"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.227"
        )
        self.assertEqual(result.get("diff")[0]["vrf_id"], 9008011)
        self.assertEqual(
            result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][2]["DATA"]["status"], "")
        self.assertEqual(result["response"][2]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_merged_duplicate(self):
        set_module_args(
            dict(state="merged", fabric="test_fabric", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))

    def test_dcnm_vrf_merged_lite_duplicate(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_vrf_lite_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))

    def test_dcnm_vrf_merged_with_incorrect_vrfid(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config_incorrect_vrfid,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result.get("msg"),
            "vrf_id for vrf:test_vrf_1 cant be updated to a different value",
        )

    def test_dcnm_vrf_merged_lite_invalidrole(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_vrf_lite_inv_config,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result["msg"],
            "VRF LITE cannot be attached to switch 10.10.10.225 with role leaf",
        )

    def test_dcnm_vrf_merged_with_update(self):
        set_module_args(
            dict(
                state="merged", fabric="test_fabric", config=self.playbook_config_update
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.226"
        )
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_1")

    def test_dcnm_vrf_merged_lite_update(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_vrf_lite_update_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.228"
        )
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_1")

    def test_dcnm_vrf_merged_with_update_vlan(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config_update_vlan,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.225"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.226"
        )
        self.assertEqual(result.get("diff")[0]["attach"][0]["vlan_id"], 303)
        self.assertEqual(result.get("diff")[0]["attach"][1]["vlan_id"], 303)
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_1")
        self.assertEqual(
            result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][2]["DATA"]["status"], "")
        self.assertEqual(result["response"][2]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_merged_lite_vlan_update(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_vrf_lite_update_vlan_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.228"
        )
        self.assertEqual(result.get("diff")[0]["attach"][0]["vlan_id"], 402)
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_1")
        self.assertEqual(
            result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][2]["DATA"]["status"], "")
        self.assertEqual(result["response"][2]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_error1(self):
        set_module_args(
            dict(state="merged", fabric="test_fabric", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(result["msg"]["RETURN_CODE"], 400)
        self.assertEqual(result["msg"]["ERROR"], "There is an error")

    def test_dcnm_vrf_error2(self):
        set_module_args(
            dict(state="merged", fabric="test_fabric", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertIn(
            "Entered VRF VLAN ID 203 is in use already",
            str(result["msg"]["DATA"].values()),
        )

    def test_dcnm_vrf_error3(self):
        set_module_args(
            dict(state="merged", fabric="test_fabric", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertEqual(
            result["response"][2]["DATA"], "No switches PENDING for deployment"
        )

    def test_dcnm_vrf_replace_with_changes(self):
        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config_replace,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["vlan_id"], 203)
        self.assertEqual(result.get("diff")[0]["attach"][1]["vlan_id"], "202")
        self.assertEqual(
            result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][1]["DATA"]["status"], "")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_replace_lite_changes(self):
        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_vrf_lite_replace_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["vlan_id"], 202)
        self.assertEqual(result.get("diff")[0]["attach"][1]["vlan_id"], "202")
        self.assertEqual(
            result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][1]["DATA"]["status"], "")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_replace_with_no_atch(self):
        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config_replace_no_atch,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertFalse(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["vlan_id"], "202")
        self.assertEqual(result.get("diff")[0]["attach"][1]["vlan_id"], "202")
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_1")
        self.assertNotIn("vrf_id", result.get("diff")[0])
        self.assertEqual(
            result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][1]["DATA"]["status"], "")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_replace_lite_no_atch(self):
        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config_replace_no_atch,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertFalse(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["vlan_id"], "202")
        self.assertEqual(result.get("diff")[0]["attach"][1]["vlan_id"], "202")
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_1")
        self.assertNotIn("vrf_id", result.get("diff")[0])
        self.assertEqual(
            result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][1]["DATA"]["status"], "")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_replace_without_changes(self):
        set_module_args(
            dict(state="replaced", fabric="test_fabric", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertFalse(result.get("response"))

    def test_dcnm_vrf_replace_lite_without_changes(self):
        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_vrf_lite_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertFalse(result.get("response"))

    def test_dcnm_vrf_override_with_additions(self):
        set_module_args(
            dict(state="overridden", fabric="test_fabric", config=self.playbook_config)
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.224"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.225"
        )
        self.assertEqual(result.get("diff")[0]["vrf_id"], 9008011)
        self.assertEqual(
            result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][2]["DATA"]["status"], "")
        self.assertEqual(result["response"][2]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_lite_override_with_additions(self):
        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=self.playbook_vrf_lite_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.224"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.227"
        )
        self.assertEqual(result.get("diff")[0]["vrf_id"], 9008011)
        self.assertEqual(
            result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][2]["DATA"]["status"], "")
        self.assertEqual(result["response"][2]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_override_with_deletions(self):
        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=self.playbook_config_override,
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
        self.assertEqual(result.get("diff")[1]["attach"][0]["vlan_id"], "202")
        self.assertEqual(result.get("diff")[1]["attach"][1]["vlan_id"], "202")
        self.assertEqual(result.get("diff")[1]["vrf_name"], "test_vrf_1")
        self.assertNotIn("vrf_id", result.get("diff")[1])

        self.assertEqual(
            result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][1]["DATA"]["status"], "")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)
        self.assertEqual(
            result["response"][4]["DATA"]["test-vrf-2--XYZKSJHSMK2(leaf2)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][4]["DATA"]["test-vrf-2--XYZKSJHSMK3(leaf3)"], "SUCCESS"
        )

    def test_dcnm_vrf_lite_override_with_deletions(self):
        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=self.playbook_vrf_lite_replace_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["vlan_id"], 202)
        self.assertEqual(result.get("diff")[0]["attach"][1]["vlan_id"], "202")

        self.assertEqual(
            result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][1]["DATA"]["status"], "")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_override_without_changes(self):
        set_module_args(
            dict(state="overridden", fabric="test_fabric", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertFalse(result.get("response"))

    def test_dcnm_vrf_override_no_changes_lite(self):
        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=self.playbook_vrf_lite_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertFalse(result.get("response"))

    def test_dcnm_vrf_delete_std(self):
        set_module_args(
            dict(state="deleted", fabric="test_fabric", config=self.playbook_config)
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertFalse(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["vlan_id"], "202")
        self.assertEqual(result.get("diff")[0]["attach"][1]["vlan_id"], "202")
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_1")
        self.assertNotIn("vrf_id", result.get("diff")[0])

        self.assertEqual(
            result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][1]["DATA"]["status"], "")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_delete_std_lite(self):
        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_vrf_lite_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        self.assertFalse(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["vlan_id"], "202")
        self.assertEqual(result.get("diff")[0]["attach"][1]["vlan_id"], "202")
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_1")
        self.assertNotIn("vrf_id", result.get("diff")[0])

        self.assertEqual(
            result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][1]["DATA"]["status"], "")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_delete_dcnm_only(self):
        set_module_args(dict(state="deleted", fabric="test_fabric", config=[]))
        result = self.execute_module(changed=True, failed=False)
        self.assertFalse(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["attach"][0]["vlan_id"], "402")
        self.assertEqual(result.get("diff")[0]["attach"][1]["vlan_id"], "403")
        self.assertEqual(result.get("diff")[0]["vrf_name"], "test_vrf_dcnm")
        self.assertNotIn("vrf_id", result.get("diff")[0])

        self.assertEqual(
            result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][1]["DATA"]["status"], "")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_vrf_delete_failure(self):
        set_module_args(
            dict(state="deleted", fabric="test_fabric", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result["msg"]["response"][2], "Deletion of vrfs test_vrf_1 has failed"
        )

    def test_dcnm_vrf_query(self):
        set_module_args(
            dict(state="query", fabric="test_fabric", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertEqual(result.get("response")[0]["parent"]["vrfName"], "test_vrf_1")
        self.assertEqual(result.get("response")[0]["parent"]["vrfId"], 9008011)
        self.assertEqual(
            result.get("response")[0]["attach"][0]["switchDetailsList"][0][
                "lanAttachedState"
            ],
            "DEPLOYED",
        )
        self.assertEqual(
            result.get("response")[0]["attach"][0]["switchDetailsList"][0]["vlan"],
            "202",
        )
        self.assertEqual(
            result.get("response")[0]["attach"][1]["switchDetailsList"][0][
                "lanAttachedState"
            ],
            "DEPLOYED",
        )
        self.assertEqual(
            result.get("response")[0]["attach"][1]["switchDetailsList"][0]["vlan"],
            "202",
        )

    def test_dcnm_vrf_query_vrf_lite(self):
        set_module_args(
            dict(
                state="query",
                fabric="test_fabric",
                config=self.playbook_vrf_lite_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertEqual(result.get("response")[0]["parent"]["vrfName"], "test_vrf_1")
        self.assertEqual(result.get("response")[0]["parent"]["vrfId"], 9008011)
        self.assertEqual(
            result.get("response")[0]["attach"][0]["switchDetailsList"][0][
                "lanAttachedState"
            ],
            "DEPLOYED",
        )
        self.assertEqual(
            result.get("response")[0]["attach"][0]["switchDetailsList"][0]["vlan"],
            "202",
        )
        self.assertEqual(
            result.get("response")[0]["attach"][0]["switchDetailsList"][0][
                "extensionValues"
            ],
            "",
        )
        self.assertEqual(
            result.get("response")[0]["attach"][1]["switchDetailsList"][0][
                "lanAttachedState"
            ],
            "DEPLOYED",
        )
        self.assertEqual(
            result.get("response")[0]["attach"][1]["switchDetailsList"][0]["vlan"],
            "202",
        )
        self.assertEqual(
            result.get("response")[0]["attach"][1]["switchDetailsList"][0][
                "extensionValues"
            ],
            "",
        )

    def test_dcnm_vrf_query_lite_without_config(self):
        set_module_args(dict(state="query", fabric="test_fabric", config=[]))
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get("diff"))
        self.assertEqual(result.get("response")[0]["parent"]["vrfName"], "test_vrf_1")
        self.assertEqual(result.get("response")[0]["parent"]["vrfId"], 9008011)
        self.assertEqual(
            result.get("response")[0]["attach"][0]["switchDetailsList"][0][
                "lanAttachedState"
            ],
            "DEPLOYED",
        )
        self.assertEqual(
            result.get("response")[0]["attach"][0]["switchDetailsList"][0]["vlan"],
            "202",
        )
        self.assertEqual(
            result.get("response")[0]["attach"][0]["switchDetailsList"][0][
                "extensionValues"
            ],
            "",
        )
        self.assertEqual(
            result.get("response")[0]["attach"][1]["switchDetailsList"][0][
                "lanAttachedState"
            ],
            "DEPLOYED",
        )
        self.assertEqual(
            result.get("response")[0]["attach"][1]["switchDetailsList"][0]["vlan"],
            "202",
        )
        self.assertEqual(
            result.get("response")[0]["attach"][1]["switchDetailsList"][0][
                "extensionValues"
            ],
            "",
        )

    def test_dcnm_vrf_validation(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config_input_validation,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result["msg"], "ip_address is mandatory under attach parameters"
        )

    def test_dcnm_vrf_validation_no_config(self):
        set_module_args(dict(state="merged", fabric="test_fabric", config=[]))
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result["msg"], "config: element is mandatory for this state merged"
        )

    def test_dcnm_vrf_12check_mode(self):
        self.version = 12
        set_module_args(
            dict(
                _ansible_check_mode=True,
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.version = 11
        self.assertFalse(result.get("diff"))
        self.assertFalse(result.get("response"))

    def test_dcnm_vrf_12merged_new(self):
        self.version = 12
        set_module_args(
            dict(state="merged", fabric="test_fabric", config=self.playbook_config)
        )
        result = self.execute_module(changed=True, failed=False)
        self.version = 11
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.224"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.225"
        )
        self.assertEqual(result.get("diff")[0]["vrf_id"], 9008011)
        self.assertEqual(
            result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK1(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][1]["DATA"]["test-vrf-1--XYZKSJHSMK2(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][2]["DATA"]["status"], "")
        self.assertEqual(result["response"][2]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)
