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

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_inventory
from .dcnm_module import TestDcnmModule, set_module_args, loadPlaybookData

import copy

__copyright__ = "Copyright (c) 2020 Cisco and/or its affiliates."
__author__ = "Karthik Babu Harichandra Babu, Praveen Ramoorthy"


class TestDcnmInvModule(TestDcnmModule):

    module = dcnm_inventory

    fd = open("dcnm-ut", "w")

    test_data = loadPlaybookData("dcnm_inventory")

    SUCCESS_RETURN_CODE = 200

    version = 11

    playbook_merge_switch_config = test_data.get("playbook_merge_switch_config")
    playbook_merge_role_switch_config = test_data.get(
        "playbook_merge_role_switch_config"
    )
    playbook_merge_bf_switch_config = test_data.get("playbook_merge_bf_switch_config")
    playbook_merge_multiple_switch_config = test_data.get(
        "playbook_merge_multiple_switch_config"
    )
    playbook_merge_bf_multiple_switch_config = test_data.get(
        "playbook_merge_bf_multiple_switch_config"
    )
    playbook_merge_bf_gf_multiple_switch_config = test_data.get(
        "playbook_merge_bf_multiple_switch_config"
    )
    playbook_delete_switch_config = test_data.get("playbook_delete_switch_config")
    playbook_delete_multiple_switch_config = test_data.get(
        "playbook_delete_multiple_switch_config"
    )
    playbook_delete_all_switch_config = test_data.get(
        "playbook_delete_all_switch_config"
    )
    playbook_override_switch_config = test_data.get("playbook_override_switch_config")
    playbook_invalid_param_config = test_data.get("playbook_invalid_param_config")
    playbook_invalid_discover_payload_config = test_data.get(
        "playbook_invalid_discover_payload_config"
    )
    playbook_query_switch_config = test_data.get("playbook_query_switch_config")
    playbook_poap_switch_config = test_data.get("playbook_poap_switch_config")
    playbook_poap_role_switch_config = test_data.get("playbook_poap_role_switch_config")
    playbook_preprovision_switch_config = test_data.get("playbook_preprovision_switch_config")
    playbook_preprovision_role_switch_config = test_data.get("playbook_preprovision_role_switch_config")
    playbook_poap_wrong_user_switch_config = test_data.get("playbook_poap_wrong_user_switch_config")
    playbook_merge_multi_type_switch_config = test_data.get("playbook_merge_multi_type_switch_config")
    playbook_poap_no_pre_ser_switch_config = test_data.get("playbook_poap_no_pre_ser_switch_config")
    playbook_poap_no_model_switch_config = test_data.get("playbook_poap_no_model_switch_config")
    playbook_poap_swap_dcnm11_switch_config = test_data.get("playbook_poap_swap_dcnm11_switch_config")
    playbook_no_user_switch_config = test_data.get("playbook_no_user_switch_config")
    playbook_no_ip_deleted_switch_config = test_data.get("playbook_no_ip_deleted_switch_config")
    playbook_poap_no_merged_query_switch_config = test_data.get("playbook_poap_no_merged_query_switch_config")
    playbook_poap_swap_switch_config = test_data.get("playbook_poap_swap_switch_config")
    playbook_rma_switch_noserial_config = test_data.get("playbook_rma_switch_noserial_config")
    playbook_rma_switch_nooldserial_config = test_data.get("playbook_rma_switch_nooldserial_config")
    playbook_rma_switch_config = test_data.get("playbook_rma_switch_config")
    playbook_poap_missing_credentials_password = test_data.get("playbook_poap_missing_credentials_password")
    playbook_poap_missing_credentials_username = test_data.get("playbook_poap_missing_credentials_username")
    playbook_rma_missing_credentials_password = test_data.get("playbook_rma_missing_credentials_password")
    playbook_rma_missing_credentials_username = test_data.get("playbook_rma_missing_credentials_username")
    rma_inv_data = test_data.get("rma_inv_data")

    # initial merge switch success
    get_have_initial_success = test_data.get("get_have_initial_success")
    get_have_two_switch_success = test_data.get("get_have_two_switch_success")
    get_have_override_switch_success = test_data.get("get_have_override_switch_success")
    get_have_null_config_switch_success = test_data.get(
        "get_have_null_config_switch_success"
    )
    get_have_migration_switch_success = test_data.get(
        "get_have_migration_switch_success"
    )
    get_have_already_created_switch_success = test_data.get(
        "get_have_already_created_switch_success"
    )
    import_switch_discover_success = test_data.get("import_switch_discover_success")
    get_inventory_initial_switch_success = test_data.get(
        "get_inventory_initial_switch_success"
    )
    get_inventory_query_switch_success = test_data.get(
        "get_inventory_query_switch_success"
    )
    get_inventory_query_no_switch_success = test_data.get(
        "get_inventory_query_no_switch_success"
    )
    get_inventory_multiple_switch_success = test_data.get(
        "get_inventory_multiple_switch_success"
    )
    get_inventory_multiple_bf_switch_success = test_data.get(
        "get_inventory_multiple_bf_switch_success"
    )
    get_inventory_multiple_bf_gf_switch_success = test_data.get(
        "get_inventory_multiple_bf_gf_switch_success"
    )
    get_inventory_override_switch_success = test_data.get(
        "get_inventory_override_switch_success"
    )
    get_inventory_blank_success = test_data.get("get_inventory_blank_success")
    rediscover_switch_success = test_data.get("rediscover_switch_success")
    rediscover_switch107_success = test_data.get("rediscover_switch107_success")
    get_lan_switch_cred_success = test_data.get("get_lan_switch_cred_success")
    get_lan_multiple_switch_cred_success = test_data.get(
        "get_lan_multiple_switch_cred_success"
    )
    get_lan_multiple_new_switch_cred_success = test_data.get(
        "get_lan_multiple_new_switch_cred_success"
    )
    get_lan_multiple_new_bf_switch_cred_success = test_data.get(
        "get_lan_multiple_new_bf_switch_cred_success"
    )
    get_lan_switch_override_cred_success = test_data.get(
        "get_lan_switch_override_cred_success"
    )
    set_lan_switch_cred_success = test_data.get("set_lan_switch_cred_success")
    set_assign_role_success = test_data.get("set_assign_role_success")
    set_assign_bg_role_success = test_data.get("set_assign_bg_role_success")
    get_fabric_id_success = test_data.get("get_fabric_id_success")
    config_save_switch_success = test_data.get("config_save_switch_success")
    config_deploy_switch_success = test_data.get("config_deploy_switch_success")
    get_inventory_query_poap_switch_success = test_data.get(
        "get_inventory_query_poap_switch_success"
    )
    get_inventory_query_poap_success = test_data.get(
        "get_inventory_query_poap_success"
    )
    get_inventory_poap_switch_success = test_data.get(
        "get_inventory_poap_switch_success"
    )
    config_poap_switch_success = test_data.get("config_poap_switch_success")
    get_inventory_prepro_switch_success = test_data.get(
        "get_inventory_prepro_switch_success"
    )
    config_poap_switch_success = test_data.get("config_poap_switch_success")
    poap_inv_discover_params = test_data.get("poap_inv_discover_params")
    get_inventory_merge_multi_type_switch_success = test_data.get(
        "get_inventory_merge_multi_type_switch_success"
    )

    # initial delete switch success
    get_have_one_switch_success = test_data.get("get_have_one_switch_success")
    delete_switch_success = test_data.get("delete_switch_success")
    get_have_multiple_switch_success = test_data.get("get_have_multiple_switch_success")
    delete_switch109_success = test_data.get("delete_switch109_success")
    delete_switch107_success = test_data.get("delete_switch107_success")

    # negative cases
    get_have_initial_failure = test_data.get("get_have_initial_failure")
    get_have_failure = test_data.get("get_have_failure")
    import_switch_discover_failure = test_data.get("import_switch_discover_failure")
    get_inventory_initial_switch_failure = test_data.get(
        "get_inventory_initial_switch_failure"
    )
    rediscover_switch_failure = test_data.get("rediscover_switch_failure")
    get_lan_switch_cred_failure = test_data.get("get_lan_switch_cred_failure")
    set_lan_switch_cred_failure = test_data.get("set_lan_switch_cred_failure")
    set_assign_role_failure = test_data.get("set_assign_role_failure")
    get_fabric_id_failure = test_data.get("get_fabric_id_failure")
    config_save_switch_failure = test_data.get("config_save_switch_failure")
    config_deploy_switch_failure = test_data.get("config_deploy_switch_failure")
    invalid_remove_switch = test_data.get("invalid_remove_switch")

    def init_data(self):
        # Some of the mock data is re-initialized after each test as previous test might have altered portions
        # of the mock data.

        self.mock_inv_discover_params = copy.deepcopy(
            self.test_data.get("mock_inv_discover_params")
        )
        self.mock_inv_discover109_params = copy.deepcopy(
            self.test_data.get("mock_inv_discover109_params")
        )
        self.mock_inv_discover107_params = copy.deepcopy(
            self.test_data.get("mock_inv_discover107_params")
        )
        self.mock_inv_blank_discover_params = copy.deepcopy(
            self.test_data.get("mock_inv_blank_discover_params")
        )

        pass

    def setUp(self):
        super(TestDcnmInvModule, self).setUp()

        self.mock_dcnm_send = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_inventory.dcnm_send"
        )
        self.run_dcnm_send = self.mock_dcnm_send.start()
        self.mock_dcnm_version_supported = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_inventory.dcnm_version_supported"
        )
        self.run_dcnm_version_supported = self.mock_dcnm_version_supported.start()
        self.mock_dcnm_fabric_details = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_inventory.get_fabric_details"
        )
        self.run_dcnm_fabric_details = self.mock_dcnm_fabric_details.start()

        self.mock_dcnm_ip_sn = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_inventory.get_fabric_inventory_details"
        )
        self.run_dcnm_ip_sn = self.mock_dcnm_ip_sn.start()

    def tearDown(self):
        super(TestDcnmInvModule, self).tearDown()
        self.mock_dcnm_send.stop()
        self.mock_dcnm_version_supported.stop()
        self.mock_dcnm_fabric_details.stop()
        self.mock_dcnm_ip_sn.stop()

    def load_fixtures(self, response=None, device=""):

        if self.version == 12:
            self.run_dcnm_version_supported.return_value = 12
        else:
            self.run_dcnm_version_supported.return_value = 11

        self.run_dcnm_fabric_details.return_value = {
            "nvPairs": {"GRFIELD_DEBUG_FLAG": "Enable"}
        }

        self.run_dcnm_ip_sn.side_effect = [self.rma_inv_data]

        if "get_have_failure" in self._testMethodName:
            self.run_dcnm_send.side_effect = [
                self.get_have_failure,
            ]

        elif "merge_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_inventory_initial_switch_success,
                self.mock_inv_discover_params,
                self.get_have_initial_success,
                self.import_switch_discover_success,
                self.get_inventory_initial_switch_success,
                self.get_inventory_initial_switch_success,
                self.rediscover_switch_success,
                self.get_inventory_initial_switch_success,
                self.get_inventory_initial_switch_success,
                self.get_lan_switch_cred_success,
                self.set_lan_switch_cred_success,
                self.get_inventory_initial_switch_success,
                self.set_assign_role_success,
                self.get_fabric_id_success,
                self.config_save_switch_success,
                self.config_deploy_switch_success,
            ]

        elif "merge_role_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_inventory_initial_switch_success,
                self.mock_inv_discover_params,
                self.get_have_initial_success,
                self.import_switch_discover_success,
                self.get_inventory_initial_switch_success,
                self.get_inventory_initial_switch_success,
                self.rediscover_switch_success,
                self.get_inventory_initial_switch_success,
                self.get_inventory_initial_switch_success,
                self.get_lan_switch_cred_success,
                self.set_lan_switch_cred_success,
                self.get_inventory_initial_switch_success,
                self.set_assign_bg_role_success,
                self.get_fabric_id_success,
                self.config_save_switch_success,
                self.config_deploy_switch_success,
            ]

        elif "merge_brownfield_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_inventory_initial_switch_success,
                self.mock_inv_discover_params,
                self.get_have_initial_success,
                self.import_switch_discover_success,
                self.get_inventory_initial_switch_success,
                self.rediscover_switch_success,
                self.get_inventory_initial_switch_success,
                self.get_inventory_initial_switch_success,
                self.get_lan_switch_cred_success,
                self.set_lan_switch_cred_success,
                self.get_inventory_initial_switch_success,
                self.set_assign_role_success,
                self.get_fabric_id_success,
                self.config_save_switch_success,
                self.config_deploy_switch_success,
            ]

        elif "merge_multiple_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_initial_success,
                self.mock_inv_discover109_params,
                self.mock_inv_discover_params,
                self.import_switch_discover_success,
                self.import_switch_discover_success,
                self.get_inventory_multiple_switch_success,
                self.get_inventory_multiple_switch_success,
                self.get_inventory_multiple_switch_success,
                self.rediscover_switch_success,
                self.rediscover_switch_success,
                self.get_inventory_multiple_switch_success,
                self.get_inventory_multiple_switch_success,
                self.get_lan_multiple_new_switch_cred_success,
                self.set_lan_switch_cred_success,
                self.set_lan_switch_cred_success,
                self.get_inventory_multiple_switch_success,
                self.set_assign_role_success,
                self.set_assign_role_success,
                self.get_fabric_id_success,
                self.config_save_switch_success,
                self.config_deploy_switch_success,
            ]

        elif "merge_multiple_brownfield_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_initial_success,
                self.mock_inv_discover_params,
                self.mock_inv_discover107_params,
                self.import_switch_discover_success,
                self.import_switch_discover_success,
                self.get_inventory_multiple_bf_switch_success,
                self.get_inventory_multiple_bf_switch_success,
                self.rediscover_switch_success,
                self.rediscover_switch_success,
                self.get_inventory_multiple_bf_switch_success,
                self.get_inventory_multiple_bf_switch_success,
                self.get_lan_multiple_new_bf_switch_cred_success,
                self.set_lan_switch_cred_success,
                self.set_lan_switch_cred_success,
                self.get_inventory_multiple_bf_switch_success,
                self.set_assign_role_success,
                self.set_assign_role_success,
                self.get_fabric_id_success,
                self.config_save_switch_success,
                self.config_deploy_switch_success,
            ]

        elif "merge_multiple_dcnm12_brown_green_field_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_initial_success,
                self.mock_inv_discover_params,
                self.mock_inv_discover107_params,
                self.import_switch_discover_success,
                self.import_switch_discover_success,
                self.get_inventory_multiple_bf_gf_switch_success,
                self.get_inventory_multiple_bf_gf_switch_success,
                self.rediscover_switch107_success,
                self.rediscover_switch_success,
                self.get_inventory_multiple_bf_gf_switch_success,
                self.get_inventory_multiple_bf_gf_switch_success,
                self.get_lan_multiple_new_bf_switch_cred_success,
                self.get_inventory_multiple_bf_gf_switch_success,
                self.set_assign_role_success,
                self.set_assign_role_success,
                self.get_fabric_id_success,
                self.config_save_switch_success,
                self.config_deploy_switch_success,
            ]

        elif "merge_multiple_brown_green_field_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_initial_success,
                self.mock_inv_discover_params,
                self.mock_inv_discover107_params,
                self.import_switch_discover_success,
                self.import_switch_discover_success,
                self.get_inventory_multiple_bf_gf_switch_success,
                self.get_inventory_multiple_bf_gf_switch_success,
                self.rediscover_switch107_success,
                self.rediscover_switch_success,
                self.get_inventory_multiple_bf_gf_switch_success,
                self.get_inventory_multiple_bf_gf_switch_success,
                self.get_lan_multiple_new_bf_switch_cred_success,
                self.set_lan_switch_cred_success,
                self.set_lan_switch_cred_success,
                self.get_inventory_multiple_bf_gf_switch_success,
                self.set_assign_role_success,
                self.set_assign_role_success,
                self.get_fabric_id_success,
                self.config_save_switch_success,
                self.config_deploy_switch_success,
            ]

        elif "delete_dcnm12_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_one_switch_success,
                self.delete_switch_success,
            ]

        elif "delete_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_one_switch_success,
                self.delete_switch_success,
            ]

        elif "delete_multiple_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_multiple_switch_success,
                self.delete_switch109_success,
                self.delete_switch_success,
            ]

        elif "delete_all_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_null_config_switch_success,
                self.delete_switch_success,
            ]

        elif "query_dcnm12_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_one_switch_success,
                self.get_inventory_query_switch_success,
            ]

        elif "query_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_one_switch_success,
                self.get_inventory_query_switch_success,
            ]

        elif "query_no_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_one_switch_success,
                self.get_inventory_query_no_switch_success,
            ]

        elif "override_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_override_switch_success,
                self.mock_inv_discover_params,
                self.delete_switch107_success,
                self.import_switch_discover_success,
                self.get_inventory_override_switch_success,
                self.get_inventory_initial_switch_success,
                self.get_inventory_initial_switch_success,
                self.rediscover_switch_success,
                self.get_inventory_override_switch_success,
                self.get_inventory_override_switch_success,
                self.get_lan_switch_override_cred_success,
                self.set_lan_switch_cred_success,
                self.get_inventory_override_switch_success,
                self.set_assign_role_success,
                self.get_fabric_id_success,
                self.config_save_switch_success,
                self.config_deploy_switch_success,
            ]

        elif "migration_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_migration_switch_success,
                self.mock_inv_discover_params,
                self.get_inventory_initial_switch_success,
                self.set_assign_role_success,
                self.get_inventory_initial_switch_success,
                self.get_fabric_id_success,
                self.config_save_switch_success,
                self.config_deploy_switch_success,
            ]

        elif "invalid_param_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = []

        elif "have_initial_failure" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_initial_failure,
            ]

        elif "import_switch_discover_failure" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_initial_success,
                self.mock_inv_discover_params,
                self.import_switch_discover_failure,
            ]

        elif "get_inventory_initial_switch_failure" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_inventory_initial_switch_failure,
                self.mock_inv_discover_params,
                self.get_have_initial_success,
                self.import_switch_discover_success,
            ]

        elif "rediscover_switch_failure" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_inventory_initial_switch_success,
                self.mock_inv_discover_params,
                self.get_have_initial_success,
                self.import_switch_discover_success,
                self.get_inventory_initial_switch_success,
                self.get_inventory_initial_switch_success,
                self.rediscover_switch_failure,
            ]

        elif "get_lan_switch_cred_failure" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_inventory_initial_switch_success,
                self.mock_inv_discover_params,
                self.get_have_initial_success,
                self.import_switch_discover_success,
                self.get_inventory_initial_switch_success,
                self.get_inventory_initial_switch_success,
                self.rediscover_switch_success,
                self.get_inventory_initial_switch_success,
                self.get_inventory_initial_switch_success,
                self.get_lan_switch_cred_failure,
            ]

        elif "set_lan_switch_cred_failure" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_inventory_initial_switch_success,
                self.mock_inv_discover_params,
                self.get_have_initial_success,
                self.import_switch_discover_success,
                self.get_inventory_initial_switch_success,
                self.get_inventory_initial_switch_success,
                self.rediscover_switch_success,
                self.get_inventory_initial_switch_success,
                self.get_inventory_initial_switch_success,
                self.get_lan_switch_cred_success,
                self.set_lan_switch_cred_failure,
            ]

        elif "set_assign_role_failure" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_inventory_initial_switch_success,
                self.mock_inv_discover_params,
                self.get_have_initial_success,
                self.import_switch_discover_success,
                self.get_inventory_initial_switch_success,
                self.get_inventory_initial_switch_success,
                self.rediscover_switch_success,
                self.get_inventory_initial_switch_success,
                self.get_inventory_initial_switch_success,
                self.get_lan_switch_cred_success,
                self.set_lan_switch_cred_success,
                self.get_inventory_initial_switch_success,
                self.set_assign_role_failure,
            ]

        elif "get_fabric_id_failure" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_inv_discover_params,
                self.get_have_initial_success,
                self.import_switch_discover_success,
                self.get_inventory_initial_switch_success,
                self.rediscover_switch_success,
                self.get_inventory_initial_switch_success,
                self.get_inventory_initial_switch_success,
                self.get_lan_switch_cred_success,
                self.set_lan_switch_cred_success,
                self.get_inventory_initial_switch_success,
                self.set_assign_role_success,
                self.get_fabric_id_failure,
            ]

        elif "config_save_switch_failure" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_inventory_initial_switch_success,
                self.mock_inv_discover_params,
                self.get_have_initial_success,
                self.import_switch_discover_success,
                self.get_inventory_initial_switch_success,
                self.get_inventory_initial_switch_success,
                self.rediscover_switch_success,
                self.get_inventory_initial_switch_success,
                self.get_inventory_initial_switch_success,
                self.get_lan_switch_cred_success,
                self.set_lan_switch_cred_success,
                self.get_inventory_initial_switch_success,
                self.set_assign_role_success,
                self.get_fabric_id_success,
                self.config_save_switch_failure,
            ]

        elif "config_deploy_switch_failure" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_inventory_initial_switch_success,
                self.mock_inv_discover_params,
                self.get_have_initial_success,
                self.import_switch_discover_success,
                self.get_inventory_initial_switch_success,
                self.get_inventory_initial_switch_success,
                self.rediscover_switch_success,
                self.get_inventory_initial_switch_success,
                self.get_inventory_initial_switch_success,
                self.get_lan_switch_cred_success,
                self.set_lan_switch_cred_success,
                self.get_inventory_initial_switch_success,
                self.set_assign_role_success,
                self.get_fabric_id_success,
                self.config_save_switch_success,
                self.config_deploy_switch_failure,
            ]

        elif "invalid_remove_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_one_switch_success,
                self.invalid_remove_switch,
            ]

        elif "blank_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = []

        elif "already_created_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_already_created_switch_success,
                self.mock_inv_discover_params,
            ]

        elif "already_deleted_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [self.get_inventory_blank_success]

        elif "query_poap_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_one_switch_success,
                self.get_inventory_query_poap_switch_success,
                self.get_inventory_query_poap_success,
            ]

        elif "poap_dcnm12_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_initial_success,
                self.get_inventory_query_poap_success,
                self.config_poap_switch_success,
                self.get_inventory_poap_switch_success,
                self.get_inventory_poap_switch_success,
                self.rediscover_switch_success,
                self.get_inventory_poap_switch_success,
                self.get_inventory_poap_switch_success,
                self.get_lan_switch_cred_success,
                self.get_inventory_poap_switch_success,
                self.set_assign_role_success,
                self.get_fabric_id_success,
                self.config_save_switch_success,
                self.config_deploy_switch_success,
            ]

        elif "poap_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_initial_success,
                self.get_inventory_query_poap_success,
                self.config_poap_switch_success,
                self.get_inventory_poap_switch_success,
                self.get_inventory_poap_switch_success,
                self.rediscover_switch_success,
                self.get_inventory_poap_switch_success,
                self.get_inventory_poap_switch_success,
                self.get_lan_switch_cred_success,
                self.get_inventory_poap_switch_success,
                self.set_assign_role_success,
                self.get_fabric_id_success,
                self.config_save_switch_success,
                self.config_deploy_switch_success,
            ]

        elif "poap_swap_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_initial_success,
                self.get_inventory_query_poap_success,
                self.config_poap_switch_success,
                self.get_inventory_query_poap_success,
                self.config_poap_switch_success,
                self.get_inventory_poap_switch_success,
                self.get_inventory_poap_switch_success,
                self.rediscover_switch_success,
                self.get_inventory_poap_switch_success,
                self.get_inventory_poap_switch_success,
                self.get_lan_switch_cred_success,
                self.get_inventory_poap_switch_success,
                self.set_assign_role_success,
                self.get_fabric_id_success,
                self.config_save_switch_success,
                self.config_deploy_switch_success,
            ]

        elif "poap_role_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_initial_success,
                self.get_inventory_query_poap_success,
                self.config_poap_switch_success,
                self.get_inventory_poap_switch_success,
                self.get_inventory_poap_switch_success,
                self.rediscover_switch_success,
                self.get_inventory_poap_switch_success,
                self.get_inventory_poap_switch_success,
                self.get_lan_switch_cred_success,
                self.get_inventory_poap_switch_success,
                self.set_assign_bg_role_success,
                self.get_fabric_id_success,
                self.config_save_switch_success,
                self.config_deploy_switch_success,
            ]

        elif "preprovision_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_initial_success,
                self.config_poap_switch_success,
                self.get_inventory_prepro_switch_success,
                self.get_inventory_prepro_switch_success,
                self.get_inventory_prepro_switch_success,
                self.get_inventory_prepro_switch_success,
                self.get_lan_switch_cred_success,
                self.get_inventory_prepro_switch_success,
                self.set_assign_role_success,
                self.get_fabric_id_success,
                self.config_save_switch_success,
            ]

        elif "preprovision_role_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_initial_success,
                self.config_poap_switch_success,
                self.get_inventory_prepro_switch_success,
                self.get_inventory_prepro_switch_success,
                self.get_inventory_prepro_switch_success,
                self.get_inventory_prepro_switch_success,
                self.get_lan_switch_cred_success,
                self.get_inventory_prepro_switch_success,
                self.set_assign_bg_role_success,
                self.get_fabric_id_success,
                self.config_save_switch_success,
            ]

        elif "poap_wrong_user_switch" in self._testMethodName:
            self.init_data()

        elif "poap_no_pre_ser_switch" in self._testMethodName:
            self.init_data()

        elif "poap_no_model_switch" in self._testMethodName:
            self.init_data()

        elif "poap_swap_dcnm11_switch" in self._testMethodName:
            self.init_data()

        elif "no_user_switch" in self._testMethodName:
            self.init_data()

        elif "no_ip_deleted_switch" in self._testMethodName:
            self.init_data()

        elif "poap_no_merged_query_switch" in self._testMethodName:
            self.init_data()

        elif "poap_overridden_switch" in self._testMethodName:
            self.init_data()

        elif "poap_missing_credentials" in self._testMethodName:
            self.init_data()

        elif "poap_idempotent_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_inventory_merge_multi_type_switch_success,
            ]

        elif "prepro_idempotent_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_inventory_merge_multi_type_switch_success,
            ]

        elif "merge_multi_type_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_initial_success,
                self.get_inventory_query_poap_success,
                self.poap_inv_discover_params,
                self.import_switch_discover_success,
                self.config_poap_switch_success,
                self.get_inventory_merge_multi_type_switch_success,
                self.get_inventory_merge_multi_type_switch_success,
                self.get_inventory_merge_multi_type_switch_success,
                self.rediscover_switch_success,
                self.rediscover_switch_success,
                self.get_inventory_merge_multi_type_switch_success,
                self.get_inventory_merge_multi_type_switch_success,
                self.get_lan_switch_cred_success,
                self.get_inventory_merge_multi_type_switch_success,
                self.set_assign_bg_role_success,
                self.set_assign_bg_role_success,
                self.set_assign_bg_role_success,
                self.get_fabric_id_success,
                self.config_save_switch_success,
                self.config_deploy_switch_success,
            ]

        elif "rma_no_ser_switch" in self._testMethodName:
            self.init_data()

        elif "rma_no_oldser_switch" in self._testMethodName:
            self.init_data()

        elif "rma_switch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.get_have_initial_success,
                self.get_inventory_query_poap_success,
                self.config_poap_switch_success,
                self.get_inventory_poap_switch_success,
                self.get_inventory_poap_switch_success,
                self.rediscover_switch_success,
                self.get_inventory_poap_switch_success,
                self.get_inventory_poap_switch_success,
                self.get_lan_switch_cred_success,
                self.get_inventory_poap_switch_success,
                self.get_fabric_id_success,
                self.config_save_switch_success,
                self.config_deploy_switch_success,
            ]

        else:
            pass

    def test_dcnm_inv_merge_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_merge_switch_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["MESSAGE"], "OK")

    def test_dcnm_inv_merge_role_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_merge_role_switch_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["MESSAGE"], "OK")

    def test_dcnm_check_inv_merge_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                _ansible_check_mode=True,
                fabric="kharicha-fabric",
                config=self.playbook_merge_switch_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertFalse(result.get("diff"))
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["MESSAGE"], "OK")

    def test_dcnm_inv_merge_brownfield_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_merge_bf_switch_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["MESSAGE"], "OK")

    def test_dcnm_inv_merge_multiple_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_merge_multiple_switch_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["MESSAGE"], "OK")

    def test_dcnm_inv_merge_multiple_brownfield_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_merge_bf_multiple_switch_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["MESSAGE"], "OK")

    def test_dcnm_inv_merge_multiple_brown_green_field_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_merge_bf_gf_multiple_switch_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["MESSAGE"], "OK")

    def test_dcnm_inv_override_switch_fabric(self):
        set_module_args(
            dict(
                state="overridden",
                fabric="kharicha-fabric",
                config=self.playbook_override_switch_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["MESSAGE"], "OK")

    def test_dcnm_inv_migration_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_merge_switch_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["MESSAGE"], "OK")

    def test_dcnm_inv_delete_switch_fabric(self):
        set_module_args(
            dict(
                state="deleted",
                fabric="kharicha-fabric",
                config=self.playbook_delete_switch_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["MESSAGE"], "OK")

    def test_dcnm_inv_delete_multiple_switch_fabric(self):
        set_module_args(
            dict(
                state="deleted",
                fabric="kharicha-fabric",
                config=self.playbook_delete_multiple_switch_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["MESSAGE"], "OK")

    def test_dcnm_inv_delete_all_switch_fabric(self):
        set_module_args(dict(state="deleted", fabric="kharicha-fabric"))

        result = self.execute_module(changed=True, failed=False)

        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["MESSAGE"], "OK")

    def test_dcnm_inv_invalid_param_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_invalid_param_config,
            )
        )

        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result.get("msg"),
            "Invalid parameters in playbook: password: : The string exceeds the allowed range of max 32 char",
        )

    def test_dcnm_inv_have_initial_failure_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_invalid_discover_payload_config,
            )
        )

        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result.get("msg"),
            "Unable to find inventories under fabric: kharicha-fabric",
        )

    def test_dcnm_inv_import_switch_discover_failure_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_merge_switch_config,
            )
        )

        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(result["msg"]["DATA"], "import switch discover failure")
        self.assertEqual(result["msg"]["MESSAGE"], "Not OK")
        self.assertEqual(result["msg"]["RETURN_CODE"], 400)

    def test_dcnm_inv_get_inventory_initial_switch_failure_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_merge_switch_config,
            )
        )

        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result.get("msg"),
            "Unable to find inventories under fabric: kharicha-fabric",
        )

    def test_dcnm_inv_rediscover_switch_failure_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_merge_switch_config,
            )
        )

        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(result["msg"]["DATA"], "rediscover switch failure")
        self.assertEqual(result["msg"]["MESSAGE"], "Not OK")
        self.assertEqual(result["msg"]["RETURN_CODE"], 400)

    def test_dcnm_inv_get_lan_switch_cred_failure_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_merge_switch_config,
            )
        )

        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result.get("msg"),
            "Unable to getLanSwitchCredentials under fabric: kharicha-fabric",
        )

    def test_dcnm_inv_set_lan_switch_cred_failure_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_merge_switch_config,
            )
        )

        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(result["msg"]["DATA"], "set lan switch credentials failure")
        self.assertEqual(result["msg"]["MESSAGE"], "Not OK")
        self.assertEqual(result["msg"]["RETURN_CODE"], 400)

    def test_dcnm_inv_set_assign_role_failure_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_merge_switch_config,
            )
        )

        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(result["msg"]["DATA"], "set assign role failure")
        self.assertEqual(result["msg"]["MESSAGE"], "Not OK")
        self.assertEqual(result["msg"]["RETURN_CODE"], 400)

    def test_dcnm_inv_config_save_switch_failure_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_merge_switch_config,
            )
        )

        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(result["msg"]["DATA"], "config save switch failure")
        self.assertEqual(result["msg"]["MESSAGE"], "Not OK")
        self.assertEqual(result["msg"]["RETURN_CODE"], 400)

    def test_dcnm_inv_config_deploy_switch_failure_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_merge_switch_config,
            )
        )

        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(result["msg"]["DATA"], "config deploy switch failure")
        self.assertEqual(result["msg"]["MESSAGE"], "Not OK")
        self.assertEqual(result["msg"]["RETURN_CODE"], 400)

    def test_dcnm_inv_invalid_remove_switch_fabric(self):
        set_module_args(
            dict(
                state="deleted",
                fabric="kharicha-fabric",
                config=self.playbook_delete_switch_config,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(result["msg"]["DATA"], "Delete switch failed")
        self.assertEqual(result["msg"]["MESSAGE"], "Not OK")
        self.assertEqual(result["msg"]["RETURN_CODE"], 400)

    def test_dcnm_inv_blank_switch_fabric(self):
        set_module_args(dict(state="merged", fabric="kharicha-fabric"))
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(
            result["msg"], "config: element is mandatory for this state merged"
        )

    def test_dcnm_inv_already_created_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_merge_switch_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertEqual(
            result["response"],
            "The switch provided is already part of the fabric and cannot be created again",
        )

    def test_dcnm_inv_already_deleted_switch_fabric(self):
        set_module_args(
            dict(
                state="deleted",
                fabric="kharicha-fabric",
                config=self.playbook_merge_switch_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertEqual(
            result["response"],
            "The switch provided is not part of the fabric and cannot be deleted",
        )

    def test_dcnm_inv_get_have_failure_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_merge_switch_config,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(result["msg"], "Fabric kharicha-fabric not present on DCNM")

    def test_dcnm_inv_query_switch_fabric(self):
        set_module_args(
            dict(
                state="query",
                fabric="kharicha-fabric",
                config=self.playbook_query_switch_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertEqual(result["response"][0]["ipAddress"], "192.168.1.110")
        self.assertEqual(result["response"][0]["switchRole"], "leaf")

    def test_dcnm_inv_query_no_switch_fabric(self):
        set_module_args(
            dict(
                state="query",
                fabric="kharicha-fabric",
                config=self.playbook_query_switch_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertEqual(
            result["response"],
            "The queried switch is not part of the fabric configured",
        )

    def test_dcnm_inv_query_poap_switch_fabric(self):
        set_module_args(
            dict(
                state="query",
                fabric="kharicha-fabric",
                query_poap="true",
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertEqual(result["response"][0]["ipAddress"], "192.168.1.217")
        self.assertEqual(result["response"][0]["switchRole"], "leaf")
        self.assertEqual(result["response"][1]["model"], "N9K-C9300v")
        self.assertEqual(result["response"][1]["serialNumber"], "9D2DAUJJFQQ")
        self.assertEqual(result["response"][1]["version"], "9.3(7)")

    def test_dcnm_inv_poap_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_poap_switch_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["MESSAGE"], "OK")

    def test_dcnm_inv_poap_role_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_poap_role_switch_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(result["response"][3]["DATA"]["newRole"], "border gateway")
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["MESSAGE"], "OK")

    def test_dcnm_inv_preprovision_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_preprovision_switch_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["MESSAGE"], "OK")

    def test_dcnm_inv_preprovision_role_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_preprovision_role_switch_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(result["response"][1]["DATA"]["newRole"], "border gateway")
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["MESSAGE"], "OK")

    def test_dcnm_inv_poap_wrong_user_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_poap_wrong_user_switch_config,
            )
        )

        result = self.execute_module(changed=False, failed=True)

        self.assertEqual(
            result.get("msg"),
            "user_name must be 'admin' for POAP",
        )

    def test_dcnm_inv_poap_merge_multi_type_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_merge_multi_type_switch_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_inv_poap_no_pre_ser_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_poap_no_pre_ser_switch_config,
            )
        )

        result = self.execute_module(changed=False, failed=True)

        self.assertEqual(
            result.get("msg"),
            "Please provide 'serial_number' for bootstrap or 'preprovision_serial' for preprovision",
        )

    def test_dcnm_inv_poap_no_model_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_poap_no_model_switch_config,
            )
        )

        result = self.execute_module(changed=False, failed=True)

        self.assertEqual(
            result.get("msg"),
            "model, version, hostname and config_data must be provided for Preprovisioning/Bootstraping a switch",
        )

    def test_dcnm_inv_poap_swap_dcnm11_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_poap_swap_dcnm11_switch_config,
            )
        )

        result = self.execute_module(changed=False, failed=True)

        self.assertEqual(
            result.get("msg"),
            "Serial number swap is not supported in DCNM version 11",
        )

    def test_dcnm_inv_no_user_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_no_user_switch_config,
            )
        )

        result = self.execute_module(changed=False, failed=True)

        self.assertEqual(
            result.get("msg"),
            "seed ip/user name and password are mandatory under inventory parameters",
        )

    def test_dcnm_inv_poap_no_merged_query_switch_fabric(self):
        set_module_args(
            dict(
                state="deleted",
                fabric="kharicha-fabric",
                config=self.playbook_poap_switch_config,
            )
        )

        result = self.execute_module(changed=False, failed=True)

        self.assertEqual(
            result.get("msg"),
            "'merged' and 'query' are only supported states for POAP",
        )

    def test_dcnm_inv_no_ip_deleted_switch_fabric(self):
        set_module_args(
            dict(
                state="deleted",
                fabric="kharicha-fabric",
                config=self.playbook_no_ip_deleted_switch_config,
            )
        )

        result = self.execute_module(changed=False, failed=True)

        self.assertEqual(
            result.get("msg"),
            "seed ip is mandatory under inventory parameters for switch deletion",
        )

    def test_dcnm_inv_poap_overridden_switch_fabric(self):
        set_module_args(
            dict(
                state="overridden",
                fabric="kharicha-fabric",
                config=self.playbook_poap_switch_config,
            )
        )

        result = self.execute_module(changed=False, failed=True)

        self.assertEqual(
            result.get("msg"),
            "'merged' and 'query' are only supported states for POAP",
        )

    def test_dcnm_inv_poap_idempotent_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_poap_switch_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(
            result.get("response"),
            "The switch provided is already part of the fabric and cannot be created again",
        )

    def test_dcnm_inv_prepro_idempotent_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_preprovision_switch_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(
            result.get("response"),
            "The switch provided is already part of the fabric and cannot be created again",
        )

    def test_dcnm_inv_merge_multiple_dcnm12_brown_green_field_switch_fabric(self):
        self.version = 12
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_merge_bf_gf_multiple_switch_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.version = 11

        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["MESSAGE"], "OK")

    def test_dcnm_inv_delete_dcnm12_switch_fabric(self):
        self.version = 12
        set_module_args(
            dict(
                state="deleted",
                fabric="kharicha-fabric",
                config=self.playbook_delete_switch_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.version = 11

        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["MESSAGE"], "OK")

    def test_dcnm_inv_query_dcnm12_switch_fabric(self):
        self.version = 12
        set_module_args(
            dict(
                state="query",
                fabric="kharicha-fabric",
                config=self.playbook_query_switch_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.version = 11

        self.assertEqual(result["response"][0]["ipAddress"], "192.168.1.110")
        self.assertEqual(result["response"][0]["switchRole"], "leaf")

    def test_dcnm_inv_poap_dcnm12_switch_fabric(self):
        self.version = 12
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_poap_switch_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.version = 11

        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["MESSAGE"], "OK")

    def test_dcnm_inv_poap_swap_switch_fabric(self):
        self.version = 12
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_poap_swap_switch_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.version = 11

        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["MESSAGE"], "OK")

    def test_dcnm_inv_rma_no_ser_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_rma_switch_noserial_config,
            )
        )

        result = self.execute_module(changed=False, failed=True)

        self.assertEqual(
            result.get("msg"),
            "Please provide 'serial_number' and 'old_serial' for RMA",
        )

    def test_dcnm_inv_rma_no_oldser_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_rma_switch_nooldserial_config,
            )
        )

        result = self.execute_module(changed=False, failed=True)

        self.assertEqual(
            result.get("msg"),
            "Please provide 'serial_number' and 'old_serial' for RMA",
        )

    def test_dcnm_inv_rma_switch_fabric(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_rma_switch_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["MESSAGE"], "OK")

    def test_dcnm_inv_poap_missing_credentials_password(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_poap_missing_credentials_password,
            )
        )

        result = self.execute_module(changed=False, failed=True)

        self.assertEqual(
            result.get("msg"),
            "discovery_password must be set when discovery_username is specified",
        )

    def test_dcnm_inv_poap_missing_credentials_username(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_poap_missing_credentials_username,
            )
        )

        result = self.execute_module(changed=False, failed=True)

        self.assertEqual(
            result.get("msg"),
            "discovery_username must be set when discovery_password is specified",
        )

    def test_dcnm_inv_rma_missing_credentials_password(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_rma_missing_credentials_password,
            )
        )

        result = self.execute_module(changed=False, failed=True)

        self.assertEqual(
            result.get("msg"),
            "discovery_password must be set when discovery_username is specified",
        )

    def test_dcnm_inv_rma_missing_credentials_username(self):
        set_module_args(
            dict(
                state="merged",
                fabric="kharicha-fabric",
                config=self.playbook_rma_missing_credentials_username,
            )
        )

        result = self.execute_module(changed=False, failed=True)

        self.assertEqual(
            result.get("msg"),
            "discovery_username must be set when discovery_password is specified",
        )
