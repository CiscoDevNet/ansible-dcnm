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
    dcnm_sgrp_utils,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm import (
    dcnm,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.common import (
    sender_dcnm,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm_sgrp_utils import (
    dcnm_sgrp_paths as sgrp_paths,
    Paths,
    dcnm_sgrp_utils_check_if_meta,
    dcnm_sgrp_utils_validate_devices,
    dcnm_sgrp_utils_get_paths,
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
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_sgrp
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_sgrp import DcnmSgrp
from ansible_collections.cisco.dcnm.plugins.module_utils.common import (
    common_utils,
)

# Importing Fixtures
from .fixtures.dcnm_sgrp.dcnm_sgrp_common import dcnm_sgrp_fixture

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


class TestDcnmSgrpModule(TestDcnmModule):

    module = dcnm_sgrp

    fd = None

    def setUp(self):
        super(TestDcnmSgrpModule, self).setUp()
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
        self.monkeypatch.setattr(dcnm_sgrp_utils, "dcnm_send", mock_dcnm_send)

    def dcnm_load_required_files(self):
        sgrp_resp = load_data("dcnm_sgrp_response", "dcnm_sgrp")
        sgrp_config = load_data("dcnm_sgrp_config", "dcnm_sgrp")
        sgrp_common = load_data("common_responses", "common")
        sgrp_data = load_data("dcnm_sgrp_data", "dcnm_sgrp")

        return (sgrp_resp, sgrp_common, sgrp_data, sgrp_config)

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

    def dcnm_get_group_id_alloc_response(self, sgrp_common):

        alloc_resp1 = copy.deepcopy(sgrp_common.get("alloc_group_id_resp"))
        alloc_resp1["DATA"]["id"] = 15001

        alloc_resp2 = copy.deepcopy(sgrp_common.get("alloc_group_id_resp"))
        alloc_resp2["DATA"]["id"] = 15002

        alloc_resp3 = copy.deepcopy(sgrp_common.get("alloc_group_id_resp"))
        alloc_resp3["DATA"]["id"] = 15003

        alloc_resp4 = copy.deepcopy(sgrp_common.get("alloc_group_id_resp"))
        alloc_resp4["DATA"]["id"] = 15004

        alloc_resp5 = copy.deepcopy(sgrp_common.get("alloc_group_id_resp"))
        alloc_resp5["DATA"]["id"] = 15005

        return (
            alloc_resp1,
            alloc_resp2,
            alloc_resp3,
            alloc_resp4,
            alloc_resp5,
        )

    def test_dcnm_sgrp_merged_new_bulk(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_create_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_config.get("sgrp_1"),
            sgrp_config.get("sgrp_2"),
            sgrp_config.get("sgrp_3"),
            sgrp_config.get("sgrp_4"),
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
                "deploy": 2,
            },
        )

    def test_dcnm_sgrp_merged_new_without_group_ids(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        alloc_resp1, alloc_resp2, alloc_resp3, alloc_resp4, alloc_resp5 = self.dcnm_get_group_id_alloc_response(
            sgrp_common
        )

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                alloc_resp1,
                sgrp_resp.get("sgrp_create_resp"),
                alloc_resp2,
                sgrp_resp.get("sgrp_create_resp"),
                alloc_resp3,
                sgrp_resp.get("sgrp_create_resp"),
                alloc_resp4,
                sgrp_resp.get("sgrp_create_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_sgrp1_config = copy.deepcopy(sgrp_config.get("sgrp_1"))
        modified_sgrp1_config.pop("group_id")

        modified_sgrp2_config = copy.deepcopy(sgrp_config.get("sgrp_2"))
        modified_sgrp2_config.pop("group_id")

        modified_sgrp3_config = copy.deepcopy(sgrp_config.get("sgrp_3"))
        modified_sgrp3_config.pop("group_id")

        modified_sgrp4_config = copy.deepcopy(sgrp_config.get("sgrp_4"))
        modified_sgrp4_config.pop("group_id")

        # load required config data
        playbook_config = [
            modified_sgrp1_config,
            modified_sgrp2_config,
            modified_sgrp3_config,
            modified_sgrp4_config,
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
                "deploy": 2,
            },
        )

    def test_dcnm_sgrp_merged_new_deploy_fail(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        deploy_fail_resp = copy.deepcopy(sgrp_resp.get("sgrp_deploy_resp"))
        deploy_fail_resp["RETURN_CODE"] = 500
        deploy_fail_resp["MESSAGE"] = ""
        deploy_fail_resp["DATA"] = ""

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_create_resp"),
                deploy_fail_resp,
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_config.get("sgrp_1"),
            sgrp_config.get("sgrp_2"),
            sgrp_config.get("sgrp_3"),
            sgrp_config.get("sgrp_4"),
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

    def test_dcnm_sgrp_merged_new_duplicate(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                [],
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_create_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_config.get("sgrp_1"),
            sgrp_config.get("sgrp_1"),
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
                "deploy": 2,
            },
        )

    def test_dcnm_sgrp_merged_new_with_deploy_none(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_create_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_config.get("sgrp_1"),
            sgrp_config.get("sgrp_2"),
            sgrp_config.get("sgrp_3"),
            sgrp_config.get("sgrp_4"),
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

    def test_dcnm_sgrp_merged_new_without_deploy_flag(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_create_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_config.get("sgrp_1"),
            sgrp_config.get("sgrp_2"),
            sgrp_config.get("sgrp_3"),
            sgrp_config.get("sgrp_4"),
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
                "deploy": 2,
            },
        )

    def test_dcnm_sgrp_merged_new_without_state(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_create_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_config.get("sgrp_1"),
            sgrp_config.get("sgrp_2"),
            sgrp_config.get("sgrp_3"),
            sgrp_config.get("sgrp_4"),
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
                "deploy": 2,
            },
        )

    def test_dcnm_sgrp_merged_idempotence(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrps,
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_create_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_config.get("sgrp_1"),
            sgrp_config.get("sgrp_2"),
            sgrp_config.get("sgrp_3"),
            sgrp_config.get("sgrp_4"),
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

    def test_dcnm_sgrp_merged_existing(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrps,
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_create_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_config_1 = copy.deepcopy(sgrp_config.get("sgrp_1"))
        modified_config_1["ip_selectors"].append(
            {
                "type": "External Subnets",
                "ip": "192.1.1.0/24",
                "vrf_name": "VRF_15001",
            }
        )
        modified_config_1["ip_selectors"].append(
            {
                "type": "Connected Endpoints",
                "ip": "192.1.2.0/24",
                "vrf_name": "VRF_15901",
            }
        )
        modified_config_1["ip_selectors"].append(
            {
                "type": "Connected Endpoints",
                "ip": "192.1.1.0/24",
                "vrf_name": "VRF_15001",
            }
        )
        modified_config_1["network_selectors"].append(
            {"network": "Network_15001", "vrf_name": "VRF_15001"}
        )
        modified_config_1["network_selectors"].append(
            {"network": "Network_16001", "vrf_name": "VRF_15001"}
        )

        # load required config data
        playbook_config = [modified_config_1]

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
                "deploy": 2,
            },
        )

        assert len(result["diff"][0]["modified"][0]["ipSelectors"]) == 5
        assert len(result["diff"][0]["modified"][0]["networkSelectors"]) == 2

    def test_dcnm_sgrp_merged_existing_duplicate(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrps,
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_create_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_config_1 = copy.deepcopy(sgrp_config.get("sgrp_1"))
        modified_config_1["ip_selectors"].append(
            {
                "type": "External Subnets",
                "ip": "192.1.1.0/24",
                "vrf_name": "VRF_15001",
            }
        )
        modified_config_1["ip_selectors"].append(
            {
                "type": "Connected Endpoints",
                "ip": "192.1.2.0/24",
                "vrf_name": "VRF_15901",
            }
        )
        modified_config_1["ip_selectors"].append(
            {
                "type": "Connected Endpoints",
                "ip": "192.1.1.0/24",
                "vrf_name": "VRF_15001",
            }
        )
        modified_config_1["network_selectors"].append(
            {"network": "Network_15001", "vrf_name": "VRF_15001"}
        )
        modified_config_1["network_selectors"].append(
            {"network": "Network_16001", "vrf_name": "VRF_15001"}
        )

        # load required config data
        playbook_config = [modified_config_1, modified_config_1]

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
                "deploy": 2,
            },
        )

        assert len(result["diff"][0]["modified"][0]["ipSelectors"]) == 5
        assert len(result["diff"][0]["modified"][0]["networkSelectors"]) == 2

    def test_dcnm_sgrp_merged_existing_create_fail(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
        ]

        create_fail_resp = copy.deepcopy(sgrp_resp.get("sgrp_create_resp"))
        create_fail_resp["RETURN_CODE"] = 500
        create_fail_resp["MESSAGE"] = ""

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrps,
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                create_fail_resp,
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_config_1 = copy.deepcopy(sgrp_config.get("sgrp_1"))
        modified_config_1["ip_selectors"].append(
            {
                "type": "External Subnets",
                "ip": "192.1.1.0/24",
                "vrf_name": "VRF_15001",
            }
        )
        modified_config_1["ip_selectors"].append(
            {
                "type": "Connected Endpoints",
                "ip": "192.1.2.0/24",
                "vrf_name": "VRF_15901",
            }
        )
        modified_config_1["ip_selectors"].append(
            {
                "type": "Connected Endpoints",
                "ip": "192.1.1.0/24",
                "vrf_name": "VRF_15001",
            }
        )
        modified_config_1["network_selectors"].append(
            {"network": "Network_15001", "vrf_name": "VRF_15001"}
        )
        modified_config_1["network_selectors"].append(
            {"network": "Network_16001", "vrf_name": "VRF_15001"}
        )

        # load required config data
        playbook_config = [modified_config_1]

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

    def test_dcnm_sgrp_merged_new_create_fail(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        create_fail_resp = copy.deepcopy(sgrp_resp.get("sgrp_create_resp"))
        create_fail_resp["RETURN_CODE"] = 500
        create_fail_resp["MESSAGE"] = ""

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                create_fail_resp,
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_config.get("sgrp_1"),
            sgrp_config.get("sgrp_2"),
            sgrp_config.get("sgrp_3"),
            sgrp_config.get("sgrp_4"),
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

    def test_dcnm_sgrp_merged_existing_and_non_existing(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_4"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrps,
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_create_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_config.get("sgrp_1"),
            sgrp_config.get("sgrp_2"),
            sgrp_config.get("sgrp_3"),
            sgrp_config.get("sgrp_4"),
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
                "deploy": 2,
            },
        )

    def test_dcnm_sgrp_merged_deploy_retry(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_create_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_config.get("sgrp_1"),
            sgrp_config.get("sgrp_2"),
            sgrp_config.get("sgrp_3"),
            sgrp_config.get("sgrp_4"),
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
                "deploy": 2,
            },
        )

    def test_dcnm_sgrp_merged_deploy_retry_fail(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_create_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
                sgrp_common.get("switches_sync_status_not_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_config.get("sgrp_1"),
            sgrp_config.get("sgrp_2"),
            sgrp_config.get("sgrp_3"),
            sgrp_config.get("sgrp_4"),
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

    def test_dcnm_sgrp_merged_deploy_sync_status_fail(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        sync_status_fail_resp = copy.deepcopy(
            sgrp_common.get("switches_sync_status_not_in_sync_resp")
        )
        sync_status_fail_resp["RETURN_CODE"] = 500

        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_create_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sync_status_fail_resp,
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_config.get("sgrp_1"),
            sgrp_config.get("sgrp_2"),
            sgrp_config.get("sgrp_3"),
            sgrp_config.get("sgrp_4"),
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

    def test_dcnm_sgrp_merged_no_config(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        set_module_args(
            dict(deploy="switches", state="merged", fabric="unit-test")
        )

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            assert "'config' element is mandatory for state 'merged'" in str(e)

    def test_dcnm_sgrp_merged_missing_group_name(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        modified_sgrp1_config = copy.deepcopy(sgrp_config.get("sgrp_1"))
        modified_sgrp1_config.pop("group_name")

        # load required config data
        playbook_config = [modified_sgrp1_config]

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
            assert "'group_name : Required parameter not found'" in str(e)

    def test_dcnm_sgrp_merged_missing_ip_sel_ip(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        modified_sgrp1_config = copy.deepcopy(sgrp_config.get("sgrp_1"))
        modified_sgrp1_config["ip_selectors"][0].pop("ip")

        # load required config data
        playbook_config = [modified_sgrp1_config]

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
            assert "'ip : Required parameter not found'" in str(e)

    def test_dcnm_sgrp_merged_missing_ip_sel_type(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        modified_sgrp1_config = copy.deepcopy(sgrp_config.get("sgrp_1"))
        modified_sgrp1_config["ip_selectors"][0].pop("type")

        # load required config data
        playbook_config = [modified_sgrp1_config]

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
            assert "'type : Required parameter not found'" in str(e)

    def test_dcnm_sgrp_merged_missing_ip_sel_vrf_name(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        modified_sgrp1_config = copy.deepcopy(sgrp_config.get("sgrp_1"))
        modified_sgrp1_config["ip_selectors"][0].pop("vrf_name")

        # load required config data
        playbook_config = [modified_sgrp1_config]

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

    def test_dcnm_sgrp_merged_missing_net_sel_vrf_name(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        modified_sgrp1_config = copy.deepcopy(sgrp_config.get("sgrp_1"))
        modified_sgrp1_config["network_selectors"][0].pop("vrf_name")

        # load required config data
        playbook_config = [modified_sgrp1_config]

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

    def test_dcnm_sgrp_merged_missing_net_sel_network(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        modified_sgrp1_config = copy.deepcopy(sgrp_config.get("sgrp_1"))
        modified_sgrp1_config["network_selectors"][0].pop("network")

        # load required config data
        playbook_config = [modified_sgrp1_config]

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
            assert "'network : Required parameter not found'" in str(e)

    def test_dcnm_sgrp_merged_missing_switches(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        modified_sgrp1_config = copy.deepcopy(sgrp_config.get("sgrp_1"))
        modified_sgrp1_config.pop("switch")

        # load required config data
        playbook_config = [modified_sgrp1_config]

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

    def test_dcnm_sgrp_delete_existing_with_null_cfg(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
            sgrp_data.get("sgrp_have_any"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrps,
                sgrp_resp.get("sgrp_delete_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
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

    def test_dcnm_sgrp_delete_existing_with_null_cfg_and_no_groups(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_resp.get("sgrp_delete_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
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

    def test_dcnm_sgrp_delete_existing_with_no_deploy(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
            sgrp_data.get("sgrp_have_any"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrps,
                sgrp_resp.get("sgrp_delete_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
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

    def test_dcnm_sgrp_delete_existing_fail(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
            sgrp_data.get("sgrp_have_any"),
        ]

        delete_fail_resp = copy.deepcopy(sgrp_resp.get("sgrp_delete_resp"))
        delete_fail_resp["RETURN_CODE"] = 500

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrps,
                delete_fail_resp,
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
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

    def test_dcnm_sgrp_delete_existing_duplicate(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
            sgrp_data.get("sgrp_have_any"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrps,
                sgrp_resp.get("sgrp_delete_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_config.get("sgrp_1"),
            sgrp_config.get("sgrp_1"),
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

    def test_dcnm_sgrp_delete_existing_invalid_params(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrps,
                sgrp_resp.get("sgrp_delete_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_sgrp1_config = copy.deepcopy(sgrp_config.get("sgrp_1"))
        modified_sgrp1_config["group_id"] = 10

        # load required config data
        playbook_config = [modified_sgrp1_config]

        set_module_args(
            dict(
                deploy="switches",
                state="deleted",
                fabric="unit-test",
                config=playbook_config,
            )
        )

        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            assert "Invalid parameters in playbook" in str(e)
            assert "The item exceeds the allowed range" in str(e)

    def test_dcnm_sgrp_delete_existing_with_group_name(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrps,
                sgrp_resp.get("sgrp_delete_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_sgrp1_config = copy.deepcopy(sgrp_config.get("sgrp_1"))
        modified_sgrp1_config.pop("group_id")

        # load required config data
        playbook_config = [modified_sgrp1_config]

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

        assert len(result["diff"][0]["delete_deploy"]) == 2

    def test_dcnm_sgrp_delete_existing_with_group_id(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrps,
                sgrp_resp.get("sgrp_delete_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_sgrp1_config = copy.deepcopy(sgrp_config.get("sgrp_1"))
        modified_sgrp1_config.pop("group_name")

        # load required config data
        playbook_config = [modified_sgrp1_config]

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

        assert len(result["diff"][0]["delete_deploy"]) == 2

    def test_dcnm_sgrp_delete_existing_with_mismatching_group_id(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrps,
                sgrp_resp.get("sgrp_delete_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_sgrp1_config = copy.deepcopy(sgrp_config.get("sgrp_1"))
        modified_sgrp1_config["group_id"] = 100

        # load required config data
        playbook_config = [modified_sgrp1_config]

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

    def test_dcnm_sgrp_delete_existing_with_mismatching_group_name(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrps,
                sgrp_resp.get("sgrp_delete_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_sgrp1_config = copy.deepcopy(sgrp_config.get("sgrp_1"))
        modified_sgrp1_config["group_name"] = "no_such_name"

        # load required config data
        playbook_config = [modified_sgrp1_config]

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

    def test_dcnm_sgrp_delete_non_existing(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = []

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrps,
                all_sgrps,
                all_sgrps,
                sgrp_resp.get("sgrp_delete_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_config.get("sgrp_1"),
            sgrp_config.get("sgrp_2"),
            sgrp_config.get("sgrp_3"),
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

    def test_dcnm_sgrp_replace(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrps,
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_create_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_config_1 = copy.deepcopy(sgrp_config.get("sgrp_1"))
        modified_config_1["ip_selectors"] = [
            {
                "type": "External Subnets",
                "ip": "193.1.1.0/24",
                "vrf_name": "VRF_19001",
            }
        ]
        modified_config_1["network_selectors"] = [
            {"network": "Network_19001", "vrf_name": "VRF_19001"}
        ]

        # load required config data
        playbook_config = [modified_config_1]

        set_module_args(
            dict(
                deploy="switches",
                state="replaced",
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
                "deploy": 2,
            },
        )

        assert len(result["diff"][0]["modified"][0]["ipSelectors"]) == 1
        assert len(result["diff"][0]["modified"][0]["networkSelectors"]) == 1

    def test_dcnm_sgrp_override_null_cfg(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
            sgrp_data.get("sgrp_have_any"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrps,
                sgrp_resp.get("sgrp_delete_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
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

        assert len(result["diff"][0]["delete_deploy"]) == 4

    def test_dcnm_sgrp_override_with_existing_cfg(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
            sgrp_data.get("sgrp_have_any"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrps,
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_config.get("sgrp_1"),
            sgrp_config.get("sgrp_2"),
            sgrp_config.get("sgrp_3"),
            sgrp_config.get("sgrp_4"),
        ]

        set_module_args(
            dict(
                deploy="switches",
                state="overridden",
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

    def test_dcnm_sgrp_override_new_cfg(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_any"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrps,
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_delete_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_create_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_config.get("sgrp_3"),
            sgrp_config.get("sgrp_4"),
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
                "deploy": 2,
            },
        )

        assert len(result["diff"][0]["delete_deploy"]) == 4

    def test_dcnm_sgrp_override_modified_cfg(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
            sgrp_data.get("sgrp_have_any"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrps,
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_delete_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_create_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        modified_config_4 = sgrp_config.get("sgrp_4")
        modified_config_4["ip_selectors"].append(
            {
                "type": "External Subnets",
                "ip": "195.1.1.0/24",
                "vrf_name": "VRF_17001",
            }
        )
        modified_config_4["network_selectors"].append(
            {"network": "Network_16001", "vrf_name": "VRF_15001"}
        )

        # load required config data
        playbook_config = [modified_config_4]

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
                "deploy": 2,
            },
        )

        assert len(result["diff"][0]["delete_deploy"]) == 4

    def test_dcnm_sgrp_override_existing_and_new_cfg(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_any"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                all_sgrps,
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_delete_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_create_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_config.get("sgrp_1"),
            sgrp_config.get("sgrp_2"),
            sgrp_config.get("sgrp_3"),
            sgrp_config.get("sgrp_4"),
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
                "deploy": 2,
            },
        )

    def test_dcnm_sgrp_query_existing_without_any_existing_info(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = []

        # entries for get_have
        self.dcnm_mock_dcnm_send([all_sgrps])

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

    def test_dcnm_sgrp_query_existing_without_cfg(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
            sgrp_data.get("sgrp_have_any"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send([all_sgrps])

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

        assert len(result["response"]) == 5

    def test_dcnm_sgrp_query_existing_with_group_name(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
            sgrp_data.get("sgrp_have_any"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send([all_sgrps])

        # load required config data
        playbook_config = [
            {"group_name": "LSG_15001"},
            {"group_name": "LSG_15002"},
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

        assert len(result["response"]) == 2

    def test_dcnm_sgrp_query_existing_with_group_id(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
            sgrp_data.get("sgrp_have_any"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send([all_sgrps])

        # load required config data
        playbook_config = [
            {"group_id": 15001},
            {"group_id": 15002},
            {"group_id": 15003},
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

    def test_dcnm_sgrp_query_with_invalid_group_id(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
            sgrp_data.get("sgrp_have_any"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send([all_sgrps])

        # load required config data
        playbook_config = [{"group_id": 10}]

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

    def test_dcnm_sgrp_query_existing_with_mismatching_info(self):

        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        all_sgrps = sgrp_resp.get("sgrp_all_resp")
        all_sgrps["DATA"] = [
            sgrp_data.get("sgrp_have_1"),
            sgrp_data.get("sgrp_have_2"),
            sgrp_data.get("sgrp_have_3"),
            sgrp_data.get("sgrp_have_4"),
            sgrp_data.get("sgrp_have_any"),
        ]

        # entries for get_have
        self.dcnm_mock_dcnm_send([all_sgrps])

        # load required config data
        playbook_config = [
            {"group_name": "LSG_15003", "group_id": 12},
            {"group_name": "LSG_15003", "group_id": 13},
            {"group_id": 15002, "group_name": "LSG_15001"},
            {"group_id": 15003, "group_name": "LSG_15004"},
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

    def test_dcnm_sgrp_verify_paths(self):

        try:
            paths = Paths()
            ver = paths.version
            paths.commit()
        except Exception as e:
            assert (
                "Paths.commit(): version is not set, which is required"
                in str(e)
            )

    def test_dcnm_sgrp_merged_new_check_mode(self):

        # Load the required files
        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_create_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_config.get("sgrp_1"),
            sgrp_config.get("sgrp_2"),
            sgrp_config.get("sgrp_3"),
            sgrp_config.get("sgrp_4"),
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
                "deploy": 2,
            },
        )

    def test_dcnm_sgrp_merged_new_with_meta_switches(self):

        # Load the required files
        sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
            self.dcnm_load_required_files()
        )

        self.dcnm_mock_common_information(sgrp_common)
        modified_inv_detail_resp = sgrp_common.get(
            "fabric_inventory_details_resp"
        )
        keys = list(modified_inv_detail_resp.keys())
        modified_inv_detail_resp[keys[0]]["switchRoleEnum"] = None
        self.dcnm_mock_fabric_inv_details(modified_inv_detail_resp)

        # entries for get_have
        self.dcnm_mock_dcnm_send(
            [
                [],
                [],
                [],
                [],
                sgrp_common.get("switches_sync_status_in_sync_resp"),
                sgrp_resp.get("sgrp_create_resp"),
                sgrp_resp.get("sgrp_deploy_resp"),
                sgrp_common.get("switches_sync_status_in_sync_resp"),
            ]
        )

        # load required config data
        playbook_config = [
            sgrp_config.get("sgrp_1"),
            sgrp_config.get("sgrp_2"),
            sgrp_config.get("sgrp_3"),
            sgrp_config.get("sgrp_4"),
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


def test_dcnm_sgrp_check_if_meta(dcnm_sgrp_fixture):

    test_module = TestDcnmSgrpModule()
    sgrp = dcnm_sgrp_fixture

    # Load the required files
    sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
        test_module.dcnm_load_required_files()
    )

    sgrp.meta_switches = sgrp_data.get("meta_switches")

    resp = dcnm_sgrp_utils_check_if_meta(sgrp, "172.31.217.103")

    assert resp is True


def test_dcnm_sgrp_utils_validate_devices(dcnm_sgrp_fixture):

    test_module = TestDcnmSgrpModule()
    sgrp = dcnm_sgrp_fixture

    # Load the required files
    sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
        test_module.dcnm_load_required_files()
    )

    # load required config data
    playbook_config = [
        sgrp_config.get("sgrp_1"),
        sgrp_config.get("sgrp_2"),
        sgrp_config.get("sgrp_3"),
        sgrp_config.get("sgrp_4"),
    ]

    sgrp.managable = sgrp_data.get("managable_switches")
    sgrp.meta_switches = sgrp_data.get("meta_switches")
    try:
        dcnm_sgrp_utils_validate_devices(sgrp, playbook_config[0])
    except Exception as e:
        assert "is not Manageable" in str(e)

    sgrp.managable.pop("172.31.217.103")
    try:
        dcnm_sgrp_utils_validate_devices(sgrp, playbook_config[0])
    except Exception as e:
        assert "Switch 172.31.217.103 is not Manageable" in str(e)


def test_dcnm_sgrp_utils_validate_common_utils(dcnm_sgrp_fixture):

    test_module = TestDcnmSgrpModule()
    sgrp = dcnm_sgrp_fixture

    sgrp_resp, sgrp_common, sgrp_data, sgrp_config = (
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
        inv_data.module = sgrp
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
        fabric_info.module = sgrp
        fabric_info.commit()
    except Exception as e:
        assert "fabric is not set, which is required" in str(e)

    try:
        fabric_info.module = sgrp
        fabric_info.fabric = "unit-test"
        fabric_info.commit()
    except Exception as e:
        assert "rest_send is not set, which is required" in str(e)

    try:
        fabric_info.module = sgrp
        fabric_info.fabric = "unit-test"
        fabric_info.rest_send = RestSend(sgrp.params)
        fabric_info.commit()
    except Exception as e:
        assert "paths is not set, which is required" in str(e)

    modified_access_mode_resp = sgrp_common.get("access_mode_resp")
    modified_access_mode_resp["DATA"]["readonly"] = True
    test_module.monkeypatch = MonkeyPatch()
    test_module.dcnm_mock_dcnm_sender(modified_access_mode_resp)

    sender = Sender()
    sender.ansible_module = sgrp
    fabric_info.rest_send = RestSend(sgrp.params)
    fabric_info.rest_send.response_handler = ResponseHandler()
    fabric_info.rest_send.sender = sender
    try:
        fabric_info.module = sgrp.module
        fabric_info.fabric = "unit-test"
        fabric_info.paths = dcnm_sgrp_utils_get_paths(12)
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
