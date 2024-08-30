# Copyright (c) 2024 Cisco and/or its affiliates.
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

# See the following regarding *_fixture imports
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html
# Due to the above, we also need to disable unused-import
# pylint: disable=unused-import
# Some fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=unused-argument
# Some tests require calling protected methods
# pylint: disable=protected-access

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Mallik Mudigonda"

from unittest.mock import patch
from _pytest.monkeypatch import MonkeyPatch

from .dcnm_module import TestDcnmModule, set_module_args, loadPlaybookData

# from typing import Any, Dict

import os
import copy
import json
import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm import (
    dcnm_sgrp_association_utils,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm import (
    dcnm,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.common import (
    sender_dcnm,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm_sgrp_association_utils import (
    dcnm_sgrp_association_paths as sgrp_association_paths,
    Paths,
    dcnm_sgrp_association_utils_check_if_meta,
    dcnm_sgrp_association_utils_validate_devices,
    dcnm_sgrp_association_utils_get_paths,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.common.common_utils import (
    Version,
    InventoryData,
    FabricInfo,
    SwitchInfo,
)

from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import (
    RestSend,
)

from ansible_collections.cisco.dcnm.plugins.module_utils.common.response_handler import (
    ResponseHandler,
)

from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_dcnm import (
    Sender,
)

from ansible_collections.ansible.netcommon.tests.unit.modules.utils import (
    AnsibleFailJson,
)
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_sgrp_association import (
    DcnmSgrpAssociation,
)
from ansible_collections.cisco.dcnm.plugins.modules import (
    dcnm_sgrp_association,
)

from ansible_collections.cisco.dcnm.plugins.module_utils.common import (
    common_utils,
)

# Importing Fixtures
from .fixtures.dcnm_sgrp_association.dcnm_sgrp_association_common import (
    dcnm_sgrp_association_fixture,
)

from unittest.mock import Mock

# Fixtures path
fixture_path = os.path.join(os.path.dirname(__file__), "fixtures")

# UNIT TEST CASES


def load_data(module_name, module_dir):

    module_data_path = fixture_path + "/" + module_dir
    path = os.path.join(module_data_path, "{0}.json".format(module_name))

    with open(path) as f:
        data = f.read()

    try:
        j_data = json.loads(data)
    except Exception as e:
        pass

    return j_data


class TestDcnmSgrpAssociationModule(TestDcnmModule):

    module = dcnm_sgrp_association

    fd = None

    def setUp(self):
        super(TestDcnmSgrpAssociationModule, self).setUp()
        self.monkeypatch = MonkeyPatch()

    def dcnm_mock_version(self, value):
        dcnm_version_supported_side_effect = []
        dcnm_version_supported_side_effect.append(value)
        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            common_utils, "dcnm_version_supported", mock_dcnm_version_supported
        )

    def dcnm_mock_fabric_inv_details(self, value):
        get_fabric_inventory_details_side_effect = []
        get_fabric_inventory_details_side_effect.append(value)
        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            common_utils,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

    def dcnm_mock_dcnm_sender(self, value):
        dcnm_sender_side_effect = []
        dcnm_sender_side_effect.append(value)
        mock_dcnm_sender = Mock(side_effect=dcnm_sender_side_effect)
        self.monkeypatch.setattr(sender_dcnm, "dcnm_send", mock_dcnm_sender)

    def dcnm_mock_dcnm_send(self, value):
        dcnm_send_side_effect = []
        dcnm_send_side_effect.extend(value)
        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(
            dcnm_sgrp_association_utils, "dcnm_send", mock_dcnm_send
        )

    def dcnm_load_required_files(self):
        sgrp_assoc_resp = load_data(
            "dcnm_sgrp_association_response", "dcnm_sgrp_association"
        )
        sgrp_assoc_config = load_data(
            "dcnm_sgrp_association_config", "dcnm_sgrp_association"
        )
        sgrp_assoc_common = load_data("common_responses", "common")
        sgrp_assoc_data = load_data(
            "dcnm_sgrp_association_data", "dcnm_sgrp_association"
        )

        return (
            sgrp_assoc_resp,
            sgrp_assoc_common,
            sgrp_assoc_data,
            sgrp_assoc_config,
        )

    def dcnm_mock_common_information(self, common_resp):
        self.dcnm_mock_version(12)
        self.dcnm_mock_fabric_inv_details(
            common_resp.get("fabric_inventory_details_resp")
        )
        self.dcnm_mock_dcnm_sender(common_resp.get("access_mode_resp"))

    def dcnm_assert_result_common_info(self, result, match_data):
        self.assertEqual(
            len(result["diff"][0]["merged"]), match_data["merged"]
        )
        self.assertEqual(
            len(result["diff"][0]["modified"]), match_data["modified"]
        )
        self.assertEqual(
            len(result["diff"][0]["deleted"]), match_data["deleted"]
        )
        self.assertEqual(len(result["diff"][0]["query"]), match_data["query"])
        self.assertEqual(
            len(result["diff"][0]["deploy"]), match_data["deploy"]
        )

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_sgrp_association_merged_new(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_assoc_config.get("sgrp_assoc_1_2"),
            sgrp_assoc_config.get("sgrp_assoc_1_3"),
            sgrp_assoc_config.get("sgrp_assoc_1_4"),
            sgrp_assoc_config.get("sgrp_assoc_2_3"),
        ]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 4,
                "modified": 0,
                "deleted": 0,
                "query": 0,
                "deploy": 1,
            },
        )

    def test_dcnm_sgrp_association_merged_new_without_group_ids(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_security_groups_resp = sgrp_assoc_resp.get(
            "security_groups_all_resp"
        )
        all_security_groups_resp["DATA"].append(
            {
                "groupName": "LSG_15001",
                "groupId": 15001,
                "ipSelectors": [],
                "networkSelectors": [],
            }
        )
        all_security_groups_resp["DATA"].append(
            {
                "groupName": "LSG_15002",
                "groupId": 15002,
                "ipSelectors": [],
                "networkSelectors": [],
            }
        )
        all_security_groups_resp["DATA"].append(
            {
                "groupName": "LSG_15003",
                "groupId": 15003,
                "ipSelectors": [],
                "networkSelectors": [],
            }
        )
        all_security_groups_resp["DATA"].append(
            {
                "groupName": "LSG_15004",
                "groupId": 15004,
                "ipSelectors": [],
                "networkSelectors": [],
            }
        )
        all_security_groups_resp["DATA"].append(
            {
                "groupName": "LSG_15005",
                "groupId": 15005,
                "ipSelectors": [],
                "networkSelectors": [],
            }
        )

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_security_groups_resp,
                [],
                [],
                [],
                [],
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_12_config = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_2")
        )
        modified_12_config.pop("src_group_id")
        modified_12_config.pop("dst_group_id")

        modified_14_config = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_4")
        )
        modified_14_config.pop("src_group_id")
        modified_14_config.pop("dst_group_id")

        # load required config data
        playbook_config = [
            modified_12_config,
            sgrp_assoc_config.get("sgrp_assoc_1_3"),
            modified_14_config,
            sgrp_assoc_config.get("sgrp_assoc_2_3"),
        ]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 4,
                "modified": 0,
                "deleted": 0,
                "query": 0,
                "deploy": 1,
            },
        )

    def test_dcnm_sgrp_association_merged_new_with_no_groups(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_security_groups_resp = sgrp_assoc_resp.get(
            "security_groups_all_resp"
        )

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_security_groups_resp,
                all_security_groups_resp,
                [],
                [],
                [],
                [],
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_12_config = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_2")
        )
        modified_12_config.pop("src_group_id")
        modified_12_config.pop("dst_group_id")

        modified_14_config = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_4")
        )
        modified_14_config.pop("src_group_id")
        modified_14_config.pop("dst_group_id")

        # load required config data
        playbook_config = [
            modified_12_config,
            sgrp_assoc_config.get("sgrp_assoc_1_3"),
            modified_14_config,
            sgrp_assoc_config.get("sgrp_assoc_2_3"),
        ]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 4,
                "modified": 0,
                "deleted": 0,
                "query": 0,
                "deploy": 1,
            },
        )

    def test_dcnm_sgrp_association_merged_new_deploy_fail(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        deploy_fail_resp = copy.deepcopy(
            sgrp_assoc_resp.get("sgrp_assoc_deploy_resp")
        )
        deploy_fail_resp["RETURN_CODE"] = 500

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                deploy_fail_resp,
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_assoc_config.get("sgrp_assoc_1_2"),
            sgrp_assoc_config.get("sgrp_assoc_1_3"),
            sgrp_assoc_config.get("sgrp_assoc_1_4"),
            sgrp_assoc_config.get("sgrp_assoc_2_3"),
        ]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            result = eval(str(e))
            assert result["msg"]["RETURN_CODE"] == 500

    def test_dcnm_sgrp_association_merged_new_duplicate(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                [],
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_assoc_config.get("sgrp_assoc_1_2"),
            sgrp_assoc_config.get("sgrp_assoc_1_2"),
        ]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 1,
                "modified": 0,
                "deleted": 0,
                "query": 0,
                "deploy": 1,
            },
        )

    def test_dcnm_sgrp_association_merged_new_with_deploy_none(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_assoc_config.get("sgrp_assoc_1_2"),
            sgrp_assoc_config.get("sgrp_assoc_1_3"),
            sgrp_assoc_config.get("sgrp_assoc_1_4"),
            sgrp_assoc_config.get("sgrp_assoc_2_3"),
        ]

        set_module_args(
            dict(
                deploy="none",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 4,
                "modified": 0,
                "deleted": 0,
                "query": 0,
                "deploy": 0,
            },
        )

    def test_dcnm_sgrp_association_merged_new_without_deploy_flag(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_assoc_config.get("sgrp_assoc_1_2"),
            sgrp_assoc_config.get("sgrp_assoc_1_3"),
            sgrp_assoc_config.get("sgrp_assoc_1_4"),
            sgrp_assoc_config.get("sgrp_assoc_2_3"),
        ]

        set_module_args(
            dict(state="merged", fabric="unit-test", config=playbook_config)
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 4,
                "modified": 0,
                "deleted": 0,
                "query": 0,
                "deploy": 1,
            },
        )

    def test_dcnm_sgrp_association_merged_new_without_state(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_assoc_config.get("sgrp_assoc_1_2"),
            sgrp_assoc_config.get("sgrp_assoc_1_3"),
            sgrp_assoc_config.get("sgrp_assoc_1_4"),
            sgrp_assoc_config.get("sgrp_assoc_2_3"),
        ]

        set_module_args(
            dict(deploy="switches", fabric="unit-test", config=playbook_config)
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 4,
                "modified": 0,
                "deleted": 0,
                "query": 0,
                "deploy": 1,
            },
        )

    def test_dcnm_sgrp_association_merged_idempotence(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_assoc_config.get("sgrp_assoc_1_2"),
            sgrp_assoc_config.get("sgrp_assoc_1_3"),
            sgrp_assoc_config.get("sgrp_assoc_1_4"),
            sgrp_assoc_config.get("sgrp_assoc_2_3"),
        ]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 0,
                "modified": 0,
                "deleted": 0,
                "query": 0,
                "deploy": 0,
            },
        )

    def test_dcnm_sgrp_association_merged_existing(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_config_12 = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_2")
        )
        modified_config_12["contract_name"] = "MODIFIED_CONTRACT1"
        modified_config_13 = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_3")
        )
        modified_config_13["contract_name"] = "MODIFIED_CONTRACT2"
        modified_config_14 = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_4")
        )
        modified_config_14["contract_name"] = "MODIFIED_CONTRACT3"
        modified_config_23 = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_2_3")
        )
        modified_config_23["contract_name"] = "MODIFIED_CONTRACT4"

        # load required config data
        playbook_config = [
            modified_config_12,
            modified_config_13,
            modified_config_14,
            modified_config_23,
        ]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 0,
                "modified": 4,
                "deleted": 0,
                "query": 0,
                "deploy": 1,
            },
        )

    def test_dcnm_sgrp_association_merged_existing_duplicate(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_config_12 = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_2")
        )
        modified_config_12["contract_name"] = "MODIFIED_CONTRACT1"

        # load required config data
        playbook_config = [modified_config_12, modified_config_12]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 0,
                "modified": 1,
                "deleted": 0,
                "query": 0,
                "deploy": 1,
            },
        )

    def test_dcnm_sgrp_association_merged_existing_create_fail(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        create_fail_resp = copy.deepcopy(
            sgrp_assoc_resp.get("sgrp_assoc_create_resp")
        )
        create_fail_resp["RETURN_CODE"] = 500
        create_fail_resp["MESSAGE"] = ""

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                create_fail_resp,
                create_fail_resp,
                create_fail_resp,
                create_fail_resp,
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_config_12 = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_2")
        )
        modified_config_12["contract_name"] = "MODIFIED_CONTRACT1"
        modified_config_13 = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_3")
        )
        modified_config_13["contract_name"] = "MODIFIED_CONTRACT2"
        modified_config_14 = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_4")
        )
        modified_config_14["contract_name"] = "MODIFIED_CONTRACT3"
        modified_config_23 = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_2_3")
        )
        modified_config_23["contract_name"] = "MODIFIED_CONTRACT4"

        # load required config data
        playbook_config = [
            modified_config_12,
            modified_config_13,
            modified_config_14,
            modified_config_23,
        ]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            result = eval(str(e))
            assert result["msg"]["RETURN_CODE"] == 500

    def test_dcnm_sgrp_association_merged_new_create_fail(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        create_fail_resp = copy.deepcopy(
            sgrp_assoc_resp.get("sgrp_assoc_create_resp")
        )
        create_fail_resp["RETURN_CODE"] = 500
        create_fail_resp["MESSAGE"] = ""

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                create_fail_resp,
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_assoc_config.get("sgrp_assoc_1_2"),
            sgrp_assoc_config.get("sgrp_assoc_1_3"),
            sgrp_assoc_config.get("sgrp_assoc_1_4"),
            sgrp_assoc_config.get("sgrp_assoc_2_3"),
        ]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            result = eval(str(e))
            assert result["msg"]["RETURN_CODE"] == 500

    def test_dcnm_sgrp_association_merged_existing_and_non_existing(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_assoc_config.get("sgrp_assoc_1_2"),
            sgrp_assoc_config.get("sgrp_assoc_1_3"),
            sgrp_assoc_config.get("sgrp_assoc_1_4"),
            sgrp_assoc_config.get("sgrp_assoc_2_3"),
        ]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 2,
                "modified": 0,
                "deleted": 0,
                "query": 0,
                "deploy": 1,
            },
        )

    def test_dcnm_sgrp_association_merged_no_group_ids(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_security_groups = sgrp_assoc_resp.get("security_groups_all_resp")
        all_security_groups["DATA"] = [
            sgrp_assoc_data.get("security_group_1"),
            sgrp_assoc_data.get("security_group_2"),
            sgrp_assoc_data.get("security_group_3"),
            sgrp_assoc_data.get("security_group_4"),
            sgrp_assoc_data.get("security_group_5"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_security_groups,
                [],
                [],
                [],
                [],
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_13_config = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_3")
        )
        modified_23_config = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_2_3")
        )
        modified_13_config.pop("src_group_id")
        modified_13_config.pop("dst_group_id")
        modified_23_config.pop("src_group_id")

        # load required config data
        playbook_config = [
            sgrp_assoc_config.get("sgrp_assoc_1_2"),
            modified_13_config,
            sgrp_assoc_config.get("sgrp_assoc_1_4"),
            sgrp_assoc_config.get("sgrp_assoc_2_3"),
            modified_23_config,
        ]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 4,
                "modified": 0,
                "deleted": 0,
                "query": 0,
                "deploy": 1,
            },
        )

    def test_dcnm_sgrp_association_merged_deploy_retry(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_assoc_config.get("sgrp_assoc_1_2"),
            sgrp_assoc_config.get("sgrp_assoc_1_3"),
            sgrp_assoc_config.get("sgrp_assoc_1_4"),
            sgrp_assoc_config.get("sgrp_assoc_2_3"),
        ]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 4,
                "modified": 0,
                "deleted": 0,
                "query": 0,
                "deploy": 1,
            },
        )

    def test_dcnm_sgrp_association_merged_deploy_retry_fail(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_assoc_config.get("sgrp_assoc_1_2"),
            sgrp_assoc_config.get("sgrp_assoc_1_3"),
            sgrp_assoc_config.get("sgrp_assoc_1_4"),
            sgrp_assoc_config.get("sgrp_assoc_2_3"),
        ]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            assert "did not reach 'In-Sync' state after deploy" in str(e)

    def test_dcnm_sgrp_association_merged_deploy_sync_status_fail(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        sync_status_fail_resp = copy.deepcopy(
            sgrp_assoc_common.get("switches_sync_status_not_in_sync_resp")
        )
        sync_status_fail_resp["RETURN_CODE"] = 500

        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sync_status_fail_resp,
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_assoc_config.get("sgrp_assoc_1_2"),
            sgrp_assoc_config.get("sgrp_assoc_1_3"),
            sgrp_assoc_config.get("sgrp_assoc_1_4"),
            sgrp_assoc_config.get("sgrp_assoc_2_3"),
        ]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            result = eval(str(e))
            assert result["msg"]["RETURN_CODE"] == 500

    def test_dcnm_sgrp_association_merged_no_config(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        set_module_args(
            dict(deploy="switches", state="merged", fabric="unit-test")
        )

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            assert "'config' element is mandatory for state 'merged'" in str(e)

    def test_dcnm_sgrp_association_merged_missing_src_group_name(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        modified_12_config = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_2")
        )
        modified_12_config.pop("src_group_name")

        # load required config data
        playbook_config = [modified_12_config]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            assert "'src_group_name : Required parameter not found'" in str(e)

    def test_dcnm_sgrp_association_merged_missing_dst_group_name(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        modified_12_config = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_2")
        )
        modified_12_config.pop("dst_group_name")

        # load required config data
        playbook_config = [modified_12_config]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            assert "'dst_group_name : Required parameter not found'" in str(e)

    def test_dcnm_sgrp_association_merged_missing_vrf_name(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        modified_12_config = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_2")
        )
        modified_12_config.pop("vrf_name")

        # load required config data
        playbook_config = [modified_12_config]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            assert "'vrf_name : Required parameter not found'" in str(e)

    def test_dcnm_sgrp_association_merged_missing_contract_name(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        modified_12_config = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_2")
        )
        modified_12_config.pop("contract_name")

        # load required config data
        playbook_config = [modified_12_config]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            assert "'contract_name : Required parameter not found'" in str(e)

    def test_dcnm_sgrp_association_merged_missing_switches(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        modified_12_config = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_2")
        )
        modified_12_config.pop("switch")

        # load required config data
        playbook_config = [modified_12_config]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            assert "'switch : Required parameter not found'" in str(e)

    def test_dcnm_sgrp_association_delete_existing_with_null_cfg(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                sgrp_assoc_resp.get("sgrp_assoc_delete_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = []

        set_module_args(
            dict(
                deploy="switches",
                state="deleted",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 0,
                "modified": 0,
                "deleted": 4,
                "query": 0,
                "deploy": 0,
            },
        )
        assert len(result["diff"][0]["delete_deploy"]) == 4

    def test_dcnm_sgrp_association_delete_existing_with_null_cfg_and_no_associations(
        self
    ):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_assoc_resp.get("sgrp_assoc_delete_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = []

        set_module_args(
            dict(
                deploy="switches",
                state="deleted",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 0,
                "modified": 0,
                "deleted": 0,
                "query": 0,
                "deploy": 0,
            },
        )
        assert len(result["diff"][0]["delete_deploy"]) == 0

    def test_dcnm_sgrp_association_delete_existing_with_no_deploy(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                sgrp_assoc_resp.get("sgrp_assoc_delete_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = []

        set_module_args(
            dict(
                deploy="none",
                state="deleted",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 0,
                "modified": 0,
                "deleted": 4,
                "query": 0,
                "deploy": 0,
            },
        )
        assert len(result["diff"][0]["delete_deploy"]) == 0

    def test_dcnm_sgrp_association_delete_existing_fail(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        delete_fail_resp = copy.deepcopy(
            sgrp_assoc_resp.get("sgrp_assoc_delete_resp")
        )
        delete_fail_resp["RETURN_CODE"] = 500

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                delete_fail_resp,
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = []

        set_module_args(
            dict(
                deploy="switches",
                state="deleted",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            result = eval(str(e))
            assert result["msg"]["RETURN_CODE"] == 500

    def test_dcnm_sgrp_association_delete_existing_duplicate(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                sgrp_assoc_resp.get("sgrp_assoc_delete_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_assoc_config.get("sgrp_assoc_1_2"),
            sgrp_assoc_config.get("sgrp_assoc_1_2"),
        ]

        set_module_args(
            dict(
                deploy="switches",
                state="deleted",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 0,
                "modified": 0,
                "deleted": 1,
                "query": 0,
                "deploy": 0,
            },
        )

    def test_dcnm_sgrp_association_delete_existing_invalid_params(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                sgrp_assoc_resp.get("sgrp_assoc_delete_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_12_config = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_2")
        )
        modified_12_config["src_group_id"] = 10

        # load required config data
        playbook_config = [modified_12_config]

        set_module_args(
            dict(
                deploy="switches",
                state="deleted",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            assert "Invalid parameters in playbook" in str(e)
            assert "The item exceeds the allowed range" in str(e)

    def test_dcnm_sgrp_association_delete_existing_with_group_name(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                sgrp_assoc_resp.get("sgrp_assoc_delete_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_12_config = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_2")
        )
        modified_12_config.pop("vrf_name")
        modified_12_config.pop("contract_name")
        modified_12_config.pop("src_group_name")
        modified_12_config.pop("src_group_id")
        modified_12_config.pop("dst_group_id")

        # load required config data
        playbook_config = [modified_12_config]

        set_module_args(
            dict(
                deploy="switches",
                state="deleted",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 0,
                "modified": 0,
                "deleted": 1,
                "query": 0,
                "deploy": 0,
            },
        )

    def test_dcnm_sgrp_association_delete_existing_with_group_id(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                sgrp_assoc_resp.get("sgrp_assoc_delete_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_12_config = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_2")
        )
        modified_12_config.pop("src_group_id")

        # load required config data
        playbook_config = [modified_12_config]

        set_module_args(
            dict(
                deploy="switches",
                state="deleted",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 0,
                "modified": 0,
                "deleted": 1,
                "query": 0,
                "deploy": 0,
            },
        )

    def test_dcnm_sgrp_association_delete_existing_with_vrf_name(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                sgrp_assoc_resp.get("sgrp_assoc_delete_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_12_config = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_2")
        )
        modified_12_config.pop("src_group_id")
        modified_12_config.pop("dst_group_id")
        modified_12_config.pop("src_group_name")
        modified_12_config.pop("dst_group_name")
        modified_12_config.pop("contract_name")

        # load required config data
        playbook_config = [modified_12_config]

        set_module_args(
            dict(
                deploy="switches",
                state="deleted",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 0,
                "modified": 0,
                "deleted": 1,
                "query": 0,
                "deploy": 0,
            },
        )

    def test_dcnm_sgrp_association_delete_existing_with_contract_name(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                sgrp_assoc_resp.get("sgrp_assoc_delete_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_12_config = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_2")
        )
        modified_12_config.pop("src_group_id")
        modified_12_config.pop("dst_group_id")
        modified_12_config.pop("src_group_name")
        modified_12_config.pop("dst_group_name")
        modified_12_config.pop("vrf_name")

        # load required config data
        playbook_config = [modified_12_config]

        set_module_args(
            dict(
                deploy="switches",
                state="deleted",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)
        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 0,
                "modified": 0,
                "deleted": 1,
                "query": 0,
                "deploy": 0,
            },
        )
        assert len(result["diff"][0]["delete_deploy"]) == 4

    def test_dcnm_sgrp_association_delete_existing_with_mismatching_group_id(
        self
    ):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                sgrp_assoc_resp.get("sgrp_assoc_delete_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_12_config = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_2")
        )
        modified_12_config["src_group_id"] = 100

        # load required config data
        playbook_config = [modified_12_config]

        set_module_args(
            dict(
                deploy="switches",
                state="deleted",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 0,
                "modified": 0,
                "deleted": 0,
                "query": 0,
                "deploy": 0,
            },
        )

    def test_dcnm_sgrp_association_delete_existing_with_mismatching_group_name(
        self
    ):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                sgrp_assoc_resp.get("sgrp_assoc_delete_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_12_config = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_2")
        )
        modified_12_config["dst_group_name"] = "no_such_name"

        # load required config data
        playbook_config = [modified_12_config]

        set_module_args(
            dict(
                deploy="switches",
                state="deleted",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 0,
                "modified": 0,
                "deleted": 0,
                "query": 0,
                "deploy": 0,
            },
        )

    def test_dcnm_sgrp_association_delete_existing_with_mismatching_vrf_name(
        self
    ):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                sgrp_assoc_resp.get("sgrp_assoc_delete_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_12_config = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_2")
        )
        modified_12_config["vrf_name"] = "no_such_name"

        # load required config data
        playbook_config = [modified_12_config]

        set_module_args(
            dict(
                deploy="switches",
                state="deleted",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 0,
                "modified": 0,
                "deleted": 0,
                "query": 0,
                "deploy": 0,
            },
        )

    def test_dcnm_sgrp_association_delete_non_existing(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = []

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                all_sgrp_assocs,
                all_sgrp_assocs,
                sgrp_assoc_resp.get("sgrp_assoc_delete_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_assoc_config.get("sgrp_assoc_1_2"),
            sgrp_assoc_config.get("sgrp_assoc_1_3"),
            sgrp_assoc_config.get("sgrp_assoc_1_4"),
        ]

        set_module_args(
            dict(
                deploy="switches",
                state="deleted",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 0,
                "modified": 0,
                "deleted": 0,
                "query": 0,
                "deploy": 0,
            },
        )

    def test_dcnm_sgrp_association_sync_status_empty(self):
        pass

    def test_dcnm_sgrp_association_replace(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_12_config = copy.deepcopy(
            sgrp_assoc_config.get("sgrp_assoc_1_2")
        )
        modified_12_config["contract_name"] = "CONTRACT12_MODIFIED"

        # load required config data
        playbook_config = [modified_12_config]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 0,
                "modified": 1,
                "deleted": 0,
                "query": 0,
                "deploy": 1,
            },
        )

    def test_dcnm_sgrp_association_override_null_cfg(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                sgrp_assoc_resp.get("sgrp_assoc_delete_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = []

        set_module_args(
            dict(
                deploy="switches",
                state="overridden",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 0,
                "modified": 0,
                "deleted": 4,
                "query": 0,
                "deploy": 0,
            },
        )

    def test_dcnm_sgrp_association_override_new_cfg(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_delete_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_assoc_config.get("sgrp_assoc_1_4"),
            sgrp_assoc_config.get("sgrp_assoc_2_4"),
        ]

        set_module_args(
            dict(
                deploy="switches",
                state="overridden",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 2,
                "modified": 0,
                "deleted": 2,
                "query": 0,
                "deploy": 1,
            },
        )

    def test_dcnm_sgrp_association_override_modified_cfg(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_delete_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_23_config = sgrp_assoc_config.get("sgrp_assoc_2_3")
        modified_23_config["contract_name"] = "MODIFIED_CONTRACT23"

        # load required config data
        playbook_config = [modified_23_config]

        set_module_args(
            dict(
                deploy="switches",
                state="overridden",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 0,
                "modified": 1,
                "deleted": 3,
                "query": 0,
                "deploy": 1,
            },
        )

    def test_dcnm_sgrp_association_override_existing_and_new_cfg(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrp_assocs,
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_delete_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_assoc_config.get("sgrp_assoc_1_2"),
            sgrp_assoc_config.get("sgrp_assoc_1_3"),
            sgrp_assoc_config.get("sgrp_assoc_1_4"),
            sgrp_assoc_config.get("sgrp_assoc_2_3"),
        ]

        set_module_args(
            dict(
                deploy="switches",
                state="overridden",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 1,
                "modified": 0,
                "deleted": 0,
                "query": 0,
                "deploy": 1,
            },
        )

    def test_dcnm_sgrp_association_query_existing_without_any_existing_info(
        self
    ):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = []

        # entries for get_have
        self.dcnm_mock_dcnm_send([all_sgrp_assocs])

        # load required config data
        playbook_config = []

        set_module_args(
            dict(
                deploy="none",
                state="query",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        assert len(result["response"]) == 0

    def test_dcnm_sgrp_association_query_existing_without_cfg(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send([all_sgrp_assocs])

        # load required config data
        playbook_config = []

        set_module_args(
            dict(
                deploy="none",
                state="query",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        assert len(result["response"]) == 4

    def test_dcnm_sgrp_association_query_existing_with_contract_name(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send([all_sgrp_assocs])

        # load required config data
        playbook_config = [{"contract_name": "CONTRACT12"}]

        set_module_args(
            dict(
                deploy="none",
                state="query",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        assert len(result["response"]) == 1

    def test_dcnm_sgrp_association_query_existing_with_src_group_name(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send([all_sgrp_assocs])

        # load required config data
        playbook_config = [
            {"src_group_name": "LSG_15001"},
            {"src_group_name": "LSG_15002"},
        ]

        set_module_args(
            dict(
                deploy="none",
                state="query",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        assert len(result["response"]) == 4

    def test_dcnm_sgrp_association_query_existing_with_dst_group_name(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send([all_sgrp_assocs])

        # load required config data
        playbook_config = [
            {"dst_group_name": "LSG_15003"},
            {"dst_group_name": "LSG_15002"},
        ]

        set_module_args(
            dict(
                deploy="none",
                state="query",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        assert len(result["response"]) == 3

    def test_dcnm_sgrp_association_query_existing_with_src_group_id(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send([all_sgrp_assocs])

        # load required config data
        playbook_config = [{"src_group_id": 15001}]

        set_module_args(
            dict(
                deploy="none",
                state="query",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        assert len(result["response"]) == 3

    def test_dcnm_sgrp_association_query_with_invalid_src_group_id(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send([all_sgrp_assocs])

        # load required config data
        playbook_config = [{"src_group_id": 10}]

        set_module_args(
            dict(
                deploy="none",
                state="query",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            assert "Invalid parameters in playbook" in str(e)
            assert "The item exceeds the allowed range" in str(e)

    def test_dcnm_sgrp_association_query_existing_with_dst_group_id(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send([all_sgrp_assocs])

        # load required config data
        playbook_config = [{"dst_group_id": 15003}]

        set_module_args(
            dict(
                deploy="none",
                state="query",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        assert len(result["response"]) == 2

    def test_dcnm_sgrp_association_query_existing_with_vrf_name(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send([all_sgrp_assocs])

        # load required config data
        playbook_config = [{"vrf_name": "VRF_12"}]

        set_module_args(
            dict(
                deploy="none",
                state="query",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        assert len(result["response"]) == 1

    def test_dcnm_sgrp_association_query_existing_with_mismatching_info(self):

        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        all_sgrp_assocs = sgrp_assoc_resp.get("sgrp_assoc_all_resp")
        all_sgrp_assocs["DATA"] = [
            sgrp_assoc_data.get("sgrp_assoc_have_1_2"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_3"),
            sgrp_assoc_data.get("sgrp_assoc_have_1_4"),
            sgrp_assoc_data.get("sgrp_assoc_have_2_3"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send([all_sgrp_assocs])

        # load required config data
        playbook_config = [
            {"src_group_name": "LSG_15003", "vrf_name": "VRF_12"},
            {"dst_group_name": "LSG_15003", "vrf_name": "VRF_12"},
            {"src_group_id": 15002, "src_group_name": "LSG_15001"},
            {"src_group_id": 15002, "dst_group_name": "LSG_15004"},
        ]

        set_module_args(
            dict(
                deploy="none",
                state="query",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        assert len(result["response"]) == 0

    def test_dcnm_sgrp_association_verify_paths(self):

        try:
            paths = Paths()
            ver = paths.version
            paths.commit()
        except Exception as e:
            assert (
                "Paths.commit(): version is not set, which is required"
                in str(e)
            )

    def test_dcnm_sgrp_association_merged_new_check_mode(self):

        # Load the required files
        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_assoc_config.get("sgrp_assoc_1_2"),
            sgrp_assoc_config.get("sgrp_assoc_1_3"),
            sgrp_assoc_config.get("sgrp_assoc_1_4"),
            sgrp_assoc_config.get("sgrp_assoc_2_3"),
        ]

        set_module_args(
            dict(
                _ansible_check_mode=True,
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.dcnm_assert_result_common_info(
            result,
            {
                "merged": 4,
                "modified": 0,
                "deleted": 0,
                "query": 0,
                "deploy": 1,
            },
        )

    def test_dcnm_sgrp_association_merged_new_with_meta_switches(self):

        # Load the required files
        sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_assoc_common)
        modified_inv_detail_resp = sgrp_assoc_common.get(
            "fabric_inventory_details_resp"
        )
        keys = list(modified_inv_detail_resp.keys())
        print(f"KEYS = {keys}\n")
        modified_inv_detail_resp[keys[0]]["switchRoleEnum"] = None
        self.dcnm_mock_fabric_inv_details(modified_inv_detail_resp)

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_create_resp"),
                sgrp_assoc_resp.get("sgrp_assoc_deploy_resp"),
                sgrp_assoc_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_assoc_config.get("sgrp_assoc_1_2"),
            sgrp_assoc_config.get("sgrp_assoc_1_3"),
            sgrp_assoc_config.get("sgrp_assoc_1_4"),
            sgrp_assoc_config.get("sgrp_assoc_2_3"),
        ]

        set_module_args(
            dict(
                deploy="switches",
                state="merged",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        try:
            result = self.execute_module(changed=True, failed=False)
        except Exception as e:
            assert "is not Manageable" in str(e)


def test_dcnm_sgrp_association_check_if_meta(dcnm_sgrp_association_fixture):

    test_module = TestDcnmSgrpAssociationModule()
    sgrp_association = dcnm_sgrp_association_fixture

    # Load the required files
    sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
        test_module.dcnm_load_required_files()
    )

    sgrp_association.meta_switches = sgrp_assoc_data.get("meta_switches")

    resp = dcnm_sgrp_association_utils_check_if_meta(
        sgrp_association, "172.31.217.103"
    )

    assert resp is True


def test_dcnm_sgrp_association_utils_validate_devices(
    dcnm_sgrp_association_fixture
):

    test_module = TestDcnmSgrpAssociationModule()
    sgrp_association = dcnm_sgrp_association_fixture

    # Load the required files
    sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
        test_module.dcnm_load_required_files()
    )

    # load required config data
    playbook_config = [
        sgrp_assoc_config.get("sgrp_assoc_1_2"),
        sgrp_assoc_config.get("sgrp_assoc_1_3"),
        sgrp_assoc_config.get("sgrp_assoc_1_4"),
        sgrp_assoc_config.get("sgrp_assoc_2_3"),
    ]

    sgrp_association.managable = sgrp_assoc_data.get("managable_switches")
    sgrp_association.meta_switches = sgrp_assoc_data.get("meta_switches")
    try:
        dcnm_sgrp_association_utils_validate_devices(
            sgrp_association, playbook_config[0]
        )
    except Exception as e:
        assert "is not Manageable" in str(e)

    sgrp_association.managable.pop("172.31.217.103")
    try:
        dcnm_sgrp_association_utils_validate_devices(
            sgrp_association, playbook_config[0]
        )
    except Exception as e:
        assert "Switch 172.31.217.103 is not Manageable" in str(e)


def test_dcnm_sgrp_association_utils_validate_common_utils(
    dcnm_sgrp_association_fixture
):

    test_module = TestDcnmSgrpAssociationModule()
    sgrp_association = dcnm_sgrp_association_fixture

    sgrp_assoc_resp, sgrp_assoc_common, sgrp_assoc_data, sgrp_assoc_config = (
        test_module.dcnm_load_required_files()
    )

    version = Version()
    inv_data = InventoryData()
    fabric_info = FabricInfo()
    switch_info = SwitchInfo()

    try:
        module = version.module
        version.commit()
    except Exception as e:
        assert "module is not set, which is required" in str(e)

    try:
        module = inv_data.module
        fabric = inv_data.fabric
        inv_data.commit()
    except Exception as e:
        assert "module is not set, which is required" in str(e)

    try:
        inv_data.module = sgrp_association
        inv_data.commit()
    except Exception as e:
        assert "fabric is not set, which is required" in str(e)

    try:
        module = fabric_info.module
        fabric = fabric_info.fabric
        paths = fabric_info.paths
        rest_send = fabric_info.rest_send
        fabric_info.commit()
    except Exception as e:
        assert "module is not set, which is required" in str(e)

    try:
        fabric_info.module = sgrp_association
        fabric_info.commit()
    except Exception as e:
        assert "fabric is not set, which is required" in str(e)

    try:
        fabric_info.module = sgrp_association
        fabric_info.fabric = "unit-test"
        fabric_info.commit()
    except Exception as e:
        assert "rest_send is not set, which is required" in str(e)

    try:
        fabric_info.module = sgrp_association
        fabric_info.fabric = "unit-test"
        fabric_info.rest_send = RestSend(sgrp_association.params)
        fabric_info.commit()
    except Exception as e:
        assert "paths is not set, which is required" in str(e)

    modified_access_mode_resp = sgrp_assoc_common.get("access_mode_resp")
    modified_access_mode_resp["DATA"]["readonly"] = True
    test_module.monkeypatch = MonkeyPatch()
    test_module.dcnm_mock_dcnm_sender(modified_access_mode_resp)

    sender = Sender()
    sender.ansible_module = sgrp_association
    fabric_info.rest_send = RestSend(sgrp_association.params)
    fabric_info.rest_send.response_handler = ResponseHandler()
    fabric_info.rest_send.sender = sender
    try:
        fabric_info.module = sgrp_association.module
        fabric_info.fabric = "unit-test"
        fabric_info.paths = dcnm_sgrp_association_utils_get_paths(12)
        fabric_info.commit()
    except Exception as e:
        assert (
            "in Monitoring mode, No changes are allowed on the fabric"
            in str(e)
        )

    try:
        switch_info.commit()
    except Exception as e:
        assert "nventory data is not set, which is required" in str(e)
