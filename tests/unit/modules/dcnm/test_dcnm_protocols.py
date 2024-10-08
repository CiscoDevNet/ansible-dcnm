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

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm import dcnm_protocols_utils
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm import dcnm
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_protocols
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm_protocols_utils import (
    dcnm_protocols_get_paths as protocols_paths,
)
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_protocols import DcnmProtocols

# Importing Fixtures
from .fixtures.dcnm_protocols.dcnm_protocols_common import dcnm_protocols_fixture

from unittest.mock import Mock

# Fixtures path
fixture_path = os.path.join(os.path.dirname(__file__), "fixtures")
module_data_path = fixture_path + "/dcnm_protocols/"


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


def test_dcnm_protocols_log_msg(monkeypatch, dcnm_protocols_fixture):

    # Testing Function log_msg()

    protocols = dcnm_protocols_fixture
    protocols.log_msg("This is a test message to test logging function\n")

    try:
        os.remove("dcnm_protocols.log")
    except Exception as e:
        print(str(e))


class TestDcnmProtocolsModule(TestDcnmModule):

    module = dcnm_protocols

    fd = None

    def setUp(self):
        super(TestDcnmProtocolsModule, self).setUp()
        self.monkeypatch = MonkeyPatch()

    def test_dcnm_protocols_create_new(self):

        # Testing function for create new protocol
        data = load_data("dcnm_protocols_data")
        resp = load_data("dcnm_protocols_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(resp.get("protocols_inventory_details"))
        get_fabric_details_side_effect.append(resp.get("protocols_fabric_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_protocols, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_protocols,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_protocols, "get_fabric_details", mock_get_fabric_details
        )

        # dcnm_send invocation from module_utils/dcnm_protocols_utils.py
        dcnm_send_side_effect.append(resp.get("dcnm_protocols_empty_resp"))
        dcnm_send_side_effect.append(resp.get("dcnm_protocols_create_resp"))

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(dcnm_protocols_utils, "dcnm_send", mock_dcnm_send)

        config = data.get("protocols_cfg_00001")
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
        self.assertEqual(result["diff"][0]["merged"][0]["protocolName"], "test")
        self.assertEqual(result["diff"][0]["merged"][0]["matchItems"][0]["type"], "ip")

    def test_dcnm_protocols_modify_existing(self):

        # Testing function for modify existing protocol
        data = load_data("dcnm_protocols_data")
        resp = load_data("dcnm_protocols_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(resp.get("protocols_inventory_details"))
        get_fabric_details_side_effect.append(resp.get("protocols_fabric_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_protocols, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_protocols,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_protocols, "get_fabric_details", mock_get_fabric_details
        )

        # dcnm_send invocation from module_utils/dcnm_protocols_utils.py
        dcnm_send_side_effect.append(resp.get("dcnm_protocols_get_resp"))
        dcnm_send_side_effect.append(resp.get("dcnm_protocols_modify_resp"))

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(dcnm_protocols_utils, "dcnm_send", mock_dcnm_send)

        config = data.get("protocols_cfg_00002")
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
        self.assertEqual(result["diff"][0]["modified"][0]["protocolName"], "test")

    def test_dcnm_protocols_delete_existing_with_config(self):

        # Testing function for delete existing protocol with config
        data = load_data("dcnm_protocols_data")
        resp = load_data("dcnm_protocols_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(resp.get("protocols_inventory_details"))
        get_fabric_details_side_effect.append(resp.get("protocols_fabric_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_protocols, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_protocols,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_protocols, "get_fabric_details", mock_get_fabric_details
        )

        # dcnm_send invocation from module_utils/dcnm_protocols_utils.py
        dcnm_send_side_effect.append(resp.get("dcnm_protocols_get_one_resp"))
        dcnm_send_side_effect.append(resp.get("dcnm_protocols_delete_resp"))

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(dcnm_protocols_utils, "dcnm_send", mock_dcnm_send)

        config = data.get("protocols_cfg_00001")
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

    def test_dcnm_protocols_delete_existing_without_config(self):

        # Testing function for delete existing protocols without config
        data = load_data("dcnm_protocols_data")
        resp = load_data("dcnm_protocols_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(resp.get("protocols_inventory_details"))
        get_fabric_details_side_effect.append(resp.get("protocols_fabric_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_protocols, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_protocols,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_protocols, "get_fabric_details", mock_get_fabric_details
        )

        # dcnm_send invocation from module_utils/dcnm_protocols_utils.py
        dcnm_send_side_effect.append(resp.get("dcnm_protocols_get_resp"))
        dcnm_send_side_effect.append(resp.get("dcnm_protocols_delete_resp"))

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(dcnm_protocols_utils, "dcnm_send", mock_dcnm_send)

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fab",
                config=[],
            )
        )

        result = self.execute_module(changed=True, failed=False)

        assert result.get("changed") is True
        self.assertEqual(len(result["diff"][0]["deleted"]), 2)
        self.assertEqual(result["diff"][0]["deleted"][0], "test")
        self.assertEqual(result["diff"][0]["deleted"][1], "test1")

    def test_dcnm_protocols_replace_existing(self):

        # Testing function for replace existing protocols
        data = load_data("dcnm_protocols_data")
        resp = load_data("dcnm_protocols_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(resp.get("protocols_inventory_details"))
        get_fabric_details_side_effect.append(resp.get("protocols_fabric_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_protocols, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_protocols,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_protocols, "get_fabric_details", mock_get_fabric_details
        )

        # dcnm_send invocation from module_utils/dcnm_protocols_utils.py
        dcnm_send_side_effect.append(resp.get("dcnm_protocols_get_resp"))
        dcnm_send_side_effect.append(resp.get("dcnm_protocols_modify_resp"))

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(dcnm_protocols_utils, "dcnm_send", mock_dcnm_send)

        config = data.get("protocols_cfg_00003")
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
        self.assertEqual(result["diff"][0]["modified"][0]["protocolName"], "test")
        self.assertEqual(result["diff"][0]["modified"][0]["matchItems"][0]["type"], "ipv6")

    def test_dcnm_protocols_query_config(self):

        # Testing function for query config
        data = load_data("dcnm_protocols_data")
        resp = load_data("dcnm_protocols_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(resp.get("protocols_inventory_details"))
        get_fabric_details_side_effect.append(resp.get("protocols_fabric_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_protocols, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_protocols,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_protocols, "get_fabric_details", mock_get_fabric_details
        )

        # dcnm_send invocation from module_utils/dcnm_protocols_utils.py
        dcnm_send_side_effect.append(resp.get("dcnm_protocols_get_resp"))

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(dcnm_protocols_utils, "dcnm_send", mock_dcnm_send)

        config = data.get("protocols_cfg_00001")
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
        self.assertEqual(result["response"][0]["protocolName"], "test")

    def test_dcnm_protocols_query_all(self):

        # Testing function for query all
        data = load_data("dcnm_protocols_data")
        resp = load_data("dcnm_protocols_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(resp.get("protocols_inventory_details"))
        get_fabric_details_side_effect.append(resp.get("protocols_fabric_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_protocols, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_protocols,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_protocols, "get_fabric_details", mock_get_fabric_details
        )

        # dcnm_send invocation from module_utils/dcnm_protocols_utils.py
        dcnm_send_side_effect.append(resp.get("dcnm_protocols_get_resp"))

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(dcnm_protocols_utils, "dcnm_send", mock_dcnm_send)

        set_module_args(
            dict(
                state="query",
                fabric="test_fab",
            )
        )

        result = self.execute_module(changed=False, failed=False)

        assert result.get("changed") is False
        self.assertEqual(len(result["response"]), 2)
        self.assertEqual(result["response"][0]["protocolName"], "test")
        self.assertEqual(result["response"][1]["protocolName"], "test1")
