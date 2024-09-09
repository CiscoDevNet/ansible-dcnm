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
__author__ = "Praveen Ramoorthy"

from unittest.mock import patch
from _pytest.monkeypatch import MonkeyPatch

from .dcnm_module import TestDcnmModule, set_module_args, loadPlaybookData

# from typing import Any, Dict

import os
import copy
import json
import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm import dcnm_contracts_utils
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm import dcnm
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_contracts
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm_contracts_utils import (
    dcnm_contracts_get_paths as contracts_paths,
)
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_contracts import DcnmContracts

# Importing Fixtures
from .fixtures.dcnm_contracts.dcnm_contracts_common import dcnm_contracts_fixture

from unittest.mock import Mock

# Fixtures path
fixture_path = os.path.join(os.path.dirname(__file__), "fixtures")
module_data_path = fixture_path + "/dcnm_contracts/"


# UNIT TEST CASES
def load_data(module_name):
    path = os.path.join(module_data_path, "{0}.json".format(module_name))

    with open(path) as f:
        data = f.read()

    try:
        j_data = json.loads(data)
    except Exception as e:
        pass

    return j_data


def test_dcnm_contracts_log_msg(monkeypatch, dcnm_contracts_fixture):

    # Testing Function log_msg()

    contracts = dcnm_contracts_fixture
    contracts.log_msg("This is a test message to test logging function\n")

    try:
        os.remove("dcnm_contracts.log")
    except Exception as e:
        print(str(e))


class TestDcnmContractsModule(TestDcnmModule):

    module = dcnm_contracts

    fd = None

    def setUp(self):
        super(TestDcnmContractsModule, self).setUp()
        self.monkeypatch = MonkeyPatch()

    def test_dcnm_contracts_create_new(self):

        # Testing Function for creating new contracts
        data = load_data("dcnm_contracts_data")
        resp = load_data("dcnm_contracts_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(resp.get("contracts_inventory_details"))
        get_fabric_details_side_effect.append(resp.get("contracts_fabric_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts, "get_fabric_details", mock_get_fabric_details
        )

        # dcnm_send invocation from module_utils/dcnm_contracts_utils.py
        dcnm_send_side_effect.append(resp.get("dcnm_contracts_empty_resp"))
        dcnm_send_side_effect.append(resp.get("dcnm_contracts_create_resp"))

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(dcnm_contracts_utils, "dcnm_send", mock_dcnm_send)

        config = data.get("contracts_cfg_00001")
        playbook_config = [config]

        set_module_args(
            dict(
                state="merged",
                fabric="test_fab",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        assert result.get("changed") is True
        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(result["diff"][0]["merged"][0]["contractName"], "test")
        self.assertEqual(result["diff"][0]["merged"][0]["rules"][0]["protocolName"], "http")

    def test_dcnm_contracts_modify_existing(self):

        # Testing Function for modifying existing contracts
        data = load_data("dcnm_contracts_data")
        resp = load_data("dcnm_contracts_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(resp.get("contracts_inventory_details"))
        get_fabric_details_side_effect.append(resp.get("contracts_fabric_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts, "get_fabric_details", mock_get_fabric_details
        )

        # dcnm_send invocation from module_utils/dcnm_contracts_utils.py
        dcnm_send_side_effect.append(resp.get("dcnm_contracts_get_resp"))
        dcnm_send_side_effect.append(resp.get("dcnm_contracts_modify_resp"))

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(dcnm_contracts_utils, "dcnm_send", mock_dcnm_send)

        config = data.get("contracts_cfg_00002")
        playbook_config = [config]

        set_module_args(
            dict(
                state="merged",
                fabric="test_fab",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        assert result.get("changed") is True
        self.assertEqual(len(result["diff"][0]["modified"]), 1)
        self.assertEqual(result["diff"][0]["modified"][0]["contractName"], "test")
        self.assertEqual(result["diff"][0]["modified"][0]["rules"][0]["protocolName"], "http")
        self.assertEqual(result["diff"][0]["modified"][0]["rules"][1]["protocolName"], "test1")

    def test_dcnm_contracts_delete_existing_with_config(self):

        # Testing Function for deleting existing contracts
        data = load_data("dcnm_contracts_data")
        resp = load_data("dcnm_contracts_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(resp.get("contracts_inventory_details"))
        get_fabric_details_side_effect.append(resp.get("contracts_fabric_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts, "get_fabric_details", mock_get_fabric_details
        )

        # dcnm_send invocation from module_utils/dcnm_contracts_utils.py
        dcnm_send_side_effect.append(resp.get("dcnm_contracts_get_one_resp"))
        dcnm_send_side_effect.append(resp.get("dcnm_contracts_conf_delete_resp"))

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(dcnm_contracts_utils, "dcnm_send", mock_dcnm_send)

        config = data.get("contracts_cfg_00001")
        playbook_config = [config]

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fab",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        assert result.get("changed") is True
        self.assertEqual(len(result["diff"][0]["deleted"]), 1)
        self.assertEqual(result["diff"][0]["deleted"][0], "test")

    def test_dcnm_contracts_delete_existing_without_config(self):

        # Testing Function for deleting all existing contracts
        data = load_data("dcnm_contracts_data")
        resp = load_data("dcnm_contracts_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(resp.get("contracts_inventory_details"))
        get_fabric_details_side_effect.append(resp.get("contracts_fabric_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts, "get_fabric_details", mock_get_fabric_details
        )

        # dcnm_send invocation from module_utils/dcnm_contracts_utils.py
        dcnm_send_side_effect.append(resp.get("dcnm_contracts_get_resp"))
        dcnm_send_side_effect.append(resp.get("dcnm_contracts_delete_resp"))

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(dcnm_contracts_utils, "dcnm_send", mock_dcnm_send)

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fab",
            )
        )

        result = self.execute_module(changed=True, failed=False)

        assert result.get("changed") is True
        self.assertEqual(len(result["diff"][0]["deleted"]), 2)
        self.assertEqual(result["diff"][0]["deleted"][0], "test1")
        self.assertEqual(result["diff"][0]["deleted"][1], "test")

    def test_dcnm_contracts_replace_existing(self):

        # Testing Function for replacing existing contracts
        data = load_data("dcnm_contracts_data")
        resp = load_data("dcnm_contracts_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(resp.get("contracts_inventory_details"))
        get_fabric_details_side_effect.append(resp.get("contracts_fabric_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts, "get_fabric_details", mock_get_fabric_details
        )

        # dcnm_send invocation from module_utils/dcnm_contracts_utils.py
        dcnm_send_side_effect.append(resp.get("dcnm_contracts_get_resp"))
        dcnm_send_side_effect.append(resp.get("dcnm_contracts_modify_resp"))

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(dcnm_contracts_utils, "dcnm_send", mock_dcnm_send)

        config = data.get("contracts_cfg_00003")
        playbook_config = [config]

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fab",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        assert result.get("changed") is True
        self.assertEqual(len(result["diff"][0]["modified"]), 1)
        self.assertEqual(result["diff"][0]["modified"][0]["contractName"], "test")
        self.assertEqual(result["diff"][0]["modified"][0]["rules"][0]["protocolName"], "test")

    def test_dcnm_contracts_override_exiting(self):

        # Testing Function for overriding existing contracts
        data = load_data("dcnm_contracts_data")
        resp = load_data("dcnm_contracts_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(resp.get("contracts_inventory_details"))
        get_fabric_details_side_effect.append(resp.get("contracts_fabric_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts, "get_fabric_details", mock_get_fabric_details
        )

        # dcnm_send invocation from module_utils/dcnm_contracts_utils.py
        dcnm_send_side_effect.append(resp.get("dcnm_contracts_get_resp"))
        dcnm_send_side_effect.append(resp.get("dcnm_contracts_get_resp"))
        dcnm_send_side_effect.append(resp.get("dcnm_contracts_conf_delete_resp"))
        dcnm_send_side_effect.append(resp.get("dcnm_contracts_modify_resp"))

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(dcnm_contracts_utils, "dcnm_send", mock_dcnm_send)

        config = data.get("contracts_cfg_00003")
        playbook_config = [config]

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fab",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        assert result.get("changed") is True
        self.assertEqual(len(result["diff"][0]["deleted"]), 1)
        self.assertEqual(result["diff"][0]["deleted"][0], "test1")
        self.assertEqual(len(result["diff"][0]["modified"]), 1)
        self.assertEqual(result["diff"][0]["modified"][0]["contractName"], "test")

    def test_dcnm_contracts_query_config(self):

        # Testing Function for querying contracts config
        data = load_data("dcnm_contracts_data")
        resp = load_data("dcnm_contracts_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(resp.get("contracts_inventory_details"))
        get_fabric_details_side_effect.append(resp.get("contracts_fabric_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts, "get_fabric_details", mock_get_fabric_details
        )

        # dcnm_send invocation from module_utils/dcnm_contracts_utils.py
        dcnm_send_side_effect.append(resp.get("dcnm_contracts_get_resp"))

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(dcnm_contracts_utils, "dcnm_send", mock_dcnm_send)

        config = data.get("contracts_cfg_00001")
        playbook_config = [config]

        set_module_args(
            dict(
                state="query",
                fabric="test_fab",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        assert result.get("changed") is False
        self.assertEqual(len(result["response"]), 1)
        self.assertEqual(result["response"][0]["contractName"], "test")

    def test_dcnm_contracts_query_all(self):

        # Testing Function for querying all contracts
        data = load_data("dcnm_contracts_data")
        resp = load_data("dcnm_contracts_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(resp.get("contracts_inventory_details"))
        get_fabric_details_side_effect.append(resp.get("contracts_fabric_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts, "get_fabric_details", mock_get_fabric_details
        )

        # dcnm_send invocation from module_utils/dcnm_contracts_utils.py
        dcnm_send_side_effect.append(resp.get("dcnm_contracts_get_resp"))

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(dcnm_contracts_utils, "dcnm_send", mock_dcnm_send)

        set_module_args(
            dict(
                state="query",
                fabric="test_fab",
            )
        )

        result = self.execute_module(changed=False, failed=False)

        assert result.get("changed") is False
        self.assertEqual(len(result["response"]), 2)
        self.assertEqual(result["response"][0]["contractName"], "test1")
        self.assertEqual(result["response"][1]["contractName"], "test")

    def test_dcnm_contracts_merge_check_mode(self):

        # Testing Function for merging contracts in check mode
        data = load_data("dcnm_contracts_data")
        resp = load_data("dcnm_contracts_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(resp.get("contracts_inventory_details"))
        get_fabric_details_side_effect.append(resp.get("contracts_fabric_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_contracts, "get_fabric_details", mock_get_fabric_details
        )

        # dcnm_send invocation from module_utils/dcnm_contracts_utils.py
        dcnm_send_side_effect.append(resp.get("dcnm_contracts_empty_resp"))
        dcnm_send_side_effect.append(resp.get("dcnm_contracts_create_resp"))

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(dcnm_contracts_utils, "dcnm_send", mock_dcnm_send)

        config = data.get("contracts_cfg_00001")
        playbook_config = [config]

        set_module_args(
            dict(
                state="merged",
                fabric="test_fab",
                config=playbook_config,
                _ansible_check_mode=True,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        assert result.get("changed") is False
        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(result["diff"][0]["merged"][0]["contractName"], "test")
