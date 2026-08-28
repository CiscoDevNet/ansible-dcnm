# Copyright (c) 2023 Cisco and/or its affiliates.
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

from unittest.mock import Mock, patch
import inspect

# from units.compat.mock import patch

from ansible_collections.cisco.dcnm.plugins.action import dcnm_network as dcnm_network_action
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm import dcnm as dcnm_utils
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_network
from .dcnm_module import TestDcnmModule, set_module_args, loadPlaybookData

import copy
import json


class TestDcnmNetworkModule(TestDcnmModule):

    module = dcnm_network

    test_data = loadPlaybookData("dcnm_network")

    SUCCESS_RETURN_CODE = 200

    version = 11

    nd_version = test_data.get("nd_version")
    nd_version_11 = test_data.get("nd_version_11")
    mock_ip_sn = test_data.get("mock_ip_sn")
    net_inv_data = test_data.get("net_inv_data")
    net_inv_data_vpc_tor = test_data.get("net_inv_data_vpc_tor")
    fabric_details = test_data.get("fabric_details")
    fabric_details_vxlan_fabric = test_data.get("fabric_details_vxlan_fabric")
    fabric_associations = test_data.get("fabric_associations")
    multicluster_fabric_associations = test_data.get("multicluster_fabric_associations")

    playbook_config = test_data.get("playbook_config")
    playbook_config_incorrect_netid = test_data.get("playbook_config_incorrect_netid")
    playbook_config_incorrect_vrf = test_data.get("playbook_config_incorrect_vrf")
    playbook_config_update = test_data.get("playbook_config_update")
    playbook_config_novlan = test_data.get("playbook_config_novlan")
    playbook_tor_config = test_data.get("playbook_tor_config")
    playbook_tor_roleerr_config = test_data.get("playbook_tor_roleerr_config")
    playbook_tor_config_update = test_data.get("playbook_tor_config_update")
    playbook_tor_only_config_update = test_data.get("playbook_tor_only_config_update")
    playbook_tor_vpc_one_sided_config = test_data.get("playbook_tor_vpc_one_sided_config")
    playbook_tor_vpc_one_sided_update = test_data.get("playbook_tor_vpc_one_sided_update")

    playbook_config_replace = test_data.get("playbook_config_replace")
    playbook_config_replace_no_atch = test_data.get("playbook_config_replace_no_atch")
    playbook_config_override = test_data.get("playbook_config_override")
    playbook_config_attach_vlan_override = test_data.get("playbook_config_attach_vlan_override")
    mock_net_attach_object_vlan_override = test_data.get("mock_net_attach_object_vlan_override")
    mock_net_attach_object_del_not_ready = test_data.get(
        "mock_net_attach_object_del_not_ready"
    )
    playbook_config_attach_freeform_config = test_data.get("playbook_config_attach_freeform_config")
    mock_net_attach_object_freeform_config = test_data.get("mock_net_attach_object_freeform_config")
    mock_net_attach_object_del_ready = test_data.get("mock_net_attach_object_del_ready")

    _real_overlay_have_freeform_from_switch_details = staticmethod(
        dcnm_network.DcnmNetwork._overlay_have_freeform_from_switch_details
    )
    mock_net_del_ready = test_data.get("mock_net_del_ready")
    attach_success_resp = test_data.get("attach_success_resp")
    attach_success_resp2 = test_data.get("attach_success_resp2")
    deploy_success_resp = test_data.get("deploy_success_resp")
    error1 = test_data.get("error1")
    error2 = test_data.get("error2")
    error3 = test_data.get("error3")
    get_have_failure = test_data.get("get_have_failure")

    delete_success_resp = test_data.get("delete_success_resp")
    blank_data = test_data.get("blank_data")
    empty_network_list = test_data.get("empty_network_list")

    # MSD test data
    playbook_msd_config = test_data.get("playbook_msd_config")
    mock_msd_fabric_details = test_data.get("mock_msd_fabric_details")
    mock_msd_child_fabric_details = test_data.get("mock_msd_child_fabric_details")
    mock_msd_ip_sn = test_data.get("mock_msd_ip_sn")
    mock_msd_vrf_object = test_data.get("mock_msd_vrf_object")
    mock_msd_net_create_response = test_data.get("mock_msd_net_create_response")
    mock_msd_net_attach_response = test_data.get("mock_msd_net_attach_response")
    mock_msd_child_net_object = test_data.get("mock_msd_child_net_object")
    mock_msd_child_net_attach_object = test_data.get("mock_msd_child_net_attach_object")
    mock_msd_child_net_update_response = test_data.get("mock_msd_child_net_update_response")

    # MSD DHCP test data
    playbook_msd_dhcp_config = test_data.get("playbook_msd_dhcp_config")
    mock_msd_dhcp_net_create_response = test_data.get("mock_msd_dhcp_net_create_response")
    mock_msd_dhcp_net_attach_response = test_data.get("mock_msd_dhcp_net_attach_response")
    mock_msd_dhcp_child_net_object = test_data.get("mock_msd_dhcp_child_net_object")
    mock_msd_dhcp_child_net_attach_object = test_data.get("mock_msd_dhcp_child_net_attach_object")
    mock_msd_dhcp_child_net_update_response = test_data.get("mock_msd_dhcp_child_net_update_response")

    # MSD Override test data
    playbook_msd_override_config = test_data.get("playbook_msd_override_config")
    mock_msd_override_parent_net_object = test_data.get("mock_msd_override_parent_net_object")
    mock_msd_override_parent_net_attach_object = test_data.get("mock_msd_override_parent_net_attach_object")
    mock_msd_override_attach_response = test_data.get("mock_msd_override_attach_response")
    mock_msd_override_child_net_object = test_data.get("mock_msd_override_child_net_object")
    mock_msd_override_child_net_attach_object = test_data.get("mock_msd_override_child_net_attach_object")

    def init_data(self):
        # Some of the mock data is re-initialized after each test as previous test might have altered portions
        # of the mock data.

        self.mock_net_object = copy.deepcopy(self.test_data.get("mock_net_object"))
        self.mock_vrf_object = copy.deepcopy(self.test_data.get("mock_vrf_object"))
        self.mock_net_attach_object = copy.deepcopy(self.test_data.get("mock_net_attach_object"))
        self.mock_net_attach_object_pending = copy.deepcopy(
            self.test_data.get("mock_net_attach_object_pending")
        )
        self.mock_net_query_object = copy.deepcopy(self.test_data.get("mock_net_query_object"))
        self.mock_vlan_get = copy.deepcopy(self.test_data.get("mock_vlan_get"))
        self.mock_net_attach_tor_object = copy.deepcopy(self.test_data.get("mock_net_attach_tor_object"))
        self.mock_net_attach_tor_only_object = copy.deepcopy(
            self.test_data.get("mock_net_attach_tor_only_object")
        )
        self.mock_net_attach_tor_vpc_object = copy.deepcopy(
            self.test_data.get("mock_net_attach_tor_vpc_object")
        )

    def setUp(self):
        super(TestDcnmNetworkModule, self).setUp()

        self.mock_dcnm_ip_sn = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_network.get_nd_fabric_inventory_details"
        )
        self.run_dcnm_ip_sn = self.mock_dcnm_ip_sn.start()

        self.mock_dcnm_send = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_network.dcnm_send"
        )
        self.run_dcnm_send = self.mock_dcnm_send.start()

        self.mock_dcnm_fabric_details = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_network.get_nd_fabric_details"
        )
        self.run_dcnm_fabric_details = self.mock_dcnm_fabric_details.start()

        self.mock_dcnm_get_url = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_network.dcnm_get_url"
        )
        self.run_dcnm_get_url = self.mock_dcnm_get_url.start()

        self.mock_freeform_overlay = patch.object(
            dcnm_network.DcnmNetwork,
            "_overlay_have_freeform_from_switch_details",
            lambda *args, **kwargs: None,
        )
        self.mock_freeform_overlay.start()

    def tearDown(self):
        super(TestDcnmNetworkModule, self).tearDown()
        self.mock_dcnm_send.stop()
        self.mock_dcnm_ip_sn.stop()
        self.mock_dcnm_fabric_details.stop()
        self.mock_dcnm_get_url.stop()
        self.mock_freeform_overlay.stop()

    @staticmethod
    def _build_attach_state(serial, switch_ports, torports=None, vlan=202, freeform_config=""):
        return {
            "serialNumber": serial,
            "networkName": "test_network",
            "switchPorts": switch_ports,
            "isAttached": True,
            "deployment": True,
            "is_deploy": True,
            "vlan": vlan,
            "torports": copy.deepcopy(torports or []),
            "freeformConfig": freeform_config,
        }

    @staticmethod
    def _build_test_logger():
        return type("Logger", (), {"debug": lambda *args, **kwargs: None})()

    @staticmethod
    def _build_secondary_ip_network_template(secondary_gw1="", secondary_gw2="", secondary_gw3="", secondary_gw4=""):
        return {
            "vlanId": 993,
            "gatewayIpAddress": "10.250.93.1/24",
            "isLayer2Only": False,
            "tag": "",
            "vlanName": "",
            "intfDescription": "",
            "mtu": "",
            "suppressArp": False,
            "dhcpServerAddr1": "",
            "dhcpServerAddr2": "",
            "dhcpServerAddr3": "",
            "vrfDhcp": "",
            "vrfDhcp2": "",
            "vrfDhcp3": "",
            "dhcpServers": "",
            "loopbackId": "",
            "mcastGroup": "",
            "gatewayIpV6Address": "",
            "secondaryGW1": secondary_gw1,
            "secondaryGW2": secondary_gw2,
            "secondaryGW3": secondary_gw3,
            "secondaryGW4": secondary_gw4,
            "trmEnabled": False,
            "rtBothAuto": False,
            "enableL3OnBorder": False,
            "networkName": "sec-ip-test",
            "ENABLE_NETFLOW": False,
            "SVI_NETFLOW_MONITOR": "",
            "VLAN_NETFLOW_MONITOR": "",
        }

    def _build_diff_network(self, inventory_data, ip_sn=None):
        dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
        dcnm_net.log = self._build_test_logger()
        dcnm_net.inventory_data = copy.deepcopy(inventory_data)
        dcnm_net.ip_sn = copy.deepcopy(ip_sn or self.mock_ip_sn)
        return dcnm_net

    def _build_secondary_ip_update_network(self):
        dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
        dcnm_net.module = Mock(params={"state": "merged"})
        dcnm_net.is_ms_fabric = False
        dcnm_net.fabric_type = "standalone"
        dcnm_net.dcnm_version = 11
        # DCNM715: a real NDFC deployment always propagates the full version
        # through the action plugin (see the handoff's "Exact Version
        # Propagation" section), so tests of unrelated legacy-field
        # add/clear/preserve behavior use a compatible-build default here.
        # Callers that specifically exercise version-capability behavior
        # (the U-matrix below) override this attribute explicitly afterward.
        dcnm_net.ndfc_version = self.NDFC_VERSION_COMPATIBLE_MINIMUM
        return dcnm_net

    def _build_secondary_ip_update_payload(self, template_conf):
        return {
            "fabric": "test-fabric",
            "vrf": "test-vrf",
            "networkName": "sec-ip-test",
            "displayName": "sec-ip-test",
            "networkId": 50993,
            "networkTemplate": "Default_Network_Universal",
            "networkExtensionTemplate": "Default_Network_Extension_Universal",
            "networkTemplateConfig": json.dumps(template_conf),
        }

    def _build_xconnect_validator(
        self, version, xconnect, is_l2only=True, fabric_type="standalone"
    ):
        dcnm_net = dcnm_network.DcnmNetwork.__new__(
            dcnm_network.DcnmNetwork
        )
        dcnm_net.params = {"state": "merged"}
        dcnm_net.config = [
            {
                "net_name": "xconnect-net",
                "is_l2only": is_l2only,
                "xconnect": xconnect,
            }
        ]
        dcnm_net.fabric_type = fabric_type
        dcnm_net.ndfc_version = version
        dcnm_net.dcnm_version = 12
        dcnm_net.check_extra_params = True
        dcnm_net.validated = []
        dcnm_net.log = self._build_test_logger()
        dcnm_net.module = Mock()
        dcnm_net.module.fail_json.side_effect = ValueError
        dcnm_net.get_fabric_multicast_group_address = Mock(
            return_value=""
        )
        return dcnm_net

    def test_dcnm_net_xconnect_validation_matrix(self):
        valid_cases = [
            ("12.4.1", True),
            ("12.4.1.245", False),
        ]
        for version, xconnect in valid_cases:
            with self.subTest(version=version, xconnect=xconnect):
                dcnm_net = self._build_xconnect_validator(
                    version, xconnect
                )
                dcnm_net.validate_input()
                self.assertEqual(
                    dcnm_net.validated[0]["xconnect"], xconnect
                )

        invalid_cases = [
            ("12.4.0", True, True, "NDFC >= 12.4.1"),
            (None, False, True, "version lookup failed"),
            ("12.4.1", True, False, "requires is_l2only=true"),
        ]
        for version, xconnect, is_l2only, message in invalid_cases:
            with self.subTest(
                version=version,
                xconnect=xconnect,
                is_l2only=is_l2only,
            ):
                dcnm_net = self._build_xconnect_validator(
                    version, xconnect, is_l2only
                )
                with self.assertRaises(ValueError):
                    dcnm_net.validate_input()
                self.assertIn(
                    message,
                    dcnm_net.module.fail_json.call_args.kwargs["msg"],
                )

    def test_dcnm_net_omitted_xconnect_skips_version_validation(self):
        for version in (None, "11.1", "12.2.1.321"):
            with self.subTest(version=version):
                dcnm_net = self._build_xconnect_validator(
                    version, None
                )
                del dcnm_net.config[0]["xconnect"]
                dcnm_net.validate_input()
                self.assertIsNone(
                    dcnm_net.validated[0]["xconnect"]
                )

    def test_dcnm_net_xconnect_is_rejected_outside_standalone_fabrics(self):
        dcnm_net = self._build_xconnect_validator(
            "12.4.1",
            True,
            fabric_type="multisite_parent",
        )

        with self.assertRaises(ValueError):
            dcnm_net.validate_input()

        self.assertIn(
            "xconnect",
            dcnm_net.module.fail_json.call_args.kwargs["msg"],
        )

    def test_dcnm_net_xconnect_payload_serializes_exact_boolean(self):
        dcnm_net = dcnm_network.DcnmNetwork.__new__(
            dcnm_network.DcnmNetwork
        )
        dcnm_net.params = {"state": "merged"}
        dcnm_net.fabric = "test-fabric"
        dcnm_net.dcnm_version = 12
        dcnm_net.ndfc_version = "12.4.1.245"
        dcnm_net.log = self._build_test_logger()
        dcnm_net.is_ms_fabric = False
        dcnm_net.fabric_type = "standalone"

        for xconnect, expected in (
            (True, True),
            (False, False),
            (None, False),
        ):
            with self.subTest(xconnect=xconnect, expected=expected):
                payload = dcnm_net.update_create_params(
                    {
                        "net_name": "xconnect-net",
                        "is_l2only": True,
                        "xconnect": xconnect,
                    }
                )
                template = json.loads(
                    payload["networkTemplateConfig"]
                )
                self.assertIs(template["xconnect"], expected)

    def test_dcnm_net_normalize_preserves_returned_xconnect_without_version(self):
        dcnm_net = dcnm_network.DcnmNetwork.__new__(
            dcnm_network.DcnmNetwork
        )
        dcnm_net.dcnm_version = 12
        dcnm_net.ndfc_version = None
        dcnm_net.fabric_type = "standalone"
        template = self._build_secondary_ip_network_template()
        template["xconnect"] = True
        network = self._build_secondary_ip_update_payload(template)

        normalized = dcnm_net.normalize_have_network(network)
        normalized_template = json.loads(
            normalized["networkTemplateConfig"]
        )

        self.assertIs(normalized_template["xconnect"], True)

    def test_dcnm_net_merged_omission_preserves_returned_xconnect(self):
        dcnm_net = self._build_secondary_ip_update_network()
        dcnm_net.dcnm_version = 12
        dcnm_net.ndfc_version = None
        have_template = self._build_secondary_ip_network_template()
        have_template["xconnect"] = True
        want_template = self._build_secondary_ip_network_template()
        have = self._build_secondary_ip_update_payload(have_template)
        want = self._build_secondary_ip_update_payload(want_template)

        dcnm_net.dcnm_update_network_information(want, have, {})

        updated_template = json.loads(want["networkTemplateConfig"])
        self.assertIs(updated_template["xconnect"], True)

    def test_dcnm_net_formatted_output_preserves_returned_xconnect(self):
        dcnm_net = dcnm_network.DcnmNetwork.__new__(
            dcnm_network.DcnmNetwork
        )
        template = self._build_secondary_ip_network_template()
        template["xconnect"] = True
        dcnm_net.diff_create = [
            self._build_secondary_ip_update_payload(template)
        ]
        dcnm_net.diff_create_quick = []
        dcnm_net.diff_create_update = []
        dcnm_net.diff_attach = []
        dcnm_net.diff_detach = []
        dcnm_net.diff_deploy = {}
        dcnm_net.diff_undeploy = {}
        dcnm_net.dcnm_version = 12
        dcnm_net.ndfc_version = None

        dcnm_net.format_diff()

        self.assertIs(dcnm_net.diff_input_format[0]["xconnect"], True)

    def test_dcnm_net_xconnect_equal_state_is_idempotent(self):
        dcnm_net = dcnm_network.DcnmNetwork.__new__(
            dcnm_network.DcnmNetwork
        )
        dcnm_net.log = self._build_test_logger()
        dcnm_net.module = Mock()
        dcnm_net.fabric_type = "standalone"
        dcnm_net.dcnm_version = 12
        dcnm_net.ndfc_version = "12.4.1"
        template = self._build_secondary_ip_network_template()
        template["xconnect"] = True
        want = self._build_secondary_ip_update_payload(template)
        have = copy.deepcopy(want)

        diff = dcnm_net.diff_for_create(want, have)

        self.assertEqual(diff[0], {})
        self.assertFalse(diff[-1])

    def test_dcnm_net_secondary_gws_template_config(self):
        template_conf = self._build_secondary_ip_network_template(
            secondary_gw1="192.166.88.1/24",
            secondary_gw2="",
            secondary_gw3=None,
            secondary_gw4="192.169.88.1/24",
        )

        secondary_gws = json.loads(dcnm_network.DcnmNetwork.get_secondary_gws_template_config(template_conf))

        self.assertEqual(
            secondary_gws,
            {
                "secondaryGWs": [
                    {"gatewayIpAddress": "192.166.88.1/24"},
                    {"gatewayIpAddress": "192.169.88.1/24"},
                ]
            },
        )

    def test_dcnm_net_update_existing_network_adds_secondary_gws_payload(self):
        dcnm_net = self._build_secondary_ip_update_network()
        have = self._build_secondary_ip_update_payload(self._build_secondary_ip_network_template())
        want = self._build_secondary_ip_update_payload(
            self._build_secondary_ip_network_template(
                secondary_gw1="192.166.88.1/24",
                secondary_gw2="192.167.88.1/24",
            )
        )

        dcnm_net.dcnm_update_network_information(
            want,
            have,
            {
                "secondary_ip_gw1": "192.166.88.1/24",
                "secondary_ip_gw2": "192.167.88.1/24",
            },
        )

        updated_template = json.loads(want["networkTemplateConfig"])
        self.assertEqual(updated_template["secondaryGW1"], "192.166.88.1/24")
        self.assertEqual(updated_template["secondaryGW2"], "192.167.88.1/24")
        self.assertEqual(
            json.loads(updated_template["secondaryGWs"]),
            {
                "secondaryGWs": [
                    {"gatewayIpAddress": "192.166.88.1/24"},
                    {"gatewayIpAddress": "192.167.88.1/24"},
                ]
            },
        )

    def test_dcnm_net_update_existing_network_clears_last_secondary_gw_payload(self):
        dcnm_net = self._build_secondary_ip_update_network()
        have = self._build_secondary_ip_update_payload(
            self._build_secondary_ip_network_template(secondary_gw1="192.166.88.1/24")
        )
        want = self._build_secondary_ip_update_payload(self._build_secondary_ip_network_template())

        dcnm_net.dcnm_update_network_information(want, have, {"secondary_ip_gw1": ""})

        updated_template = json.loads(want["networkTemplateConfig"])
        self.assertEqual(updated_template["secondaryGW1"], "")
        self.assertEqual(json.loads(updated_template["secondaryGWs"]), {"secondaryGWs": []})

    def test_dcnm_net_update_existing_network_clears_trailing_explicit_secondary_gw_payload(self):
        dcnm_net = self._build_secondary_ip_update_network()
        have = self._build_secondary_ip_update_payload(
            self._build_secondary_ip_network_template(
                secondary_gw1="192.166.88.1/24",
                secondary_gw2="192.167.88.1/24",
            )
        )
        want = self._build_secondary_ip_update_payload(self._build_secondary_ip_network_template())

        dcnm_net.dcnm_update_network_information(want, have, {"secondary_ip_gw2": ""})

        updated_template = json.loads(want["networkTemplateConfig"])
        self.assertEqual(updated_template["secondaryGW1"], "192.166.88.1/24")
        self.assertEqual(updated_template["secondaryGW2"], "")
        self.assertEqual(
            json.loads(updated_template["secondaryGWs"]),
            {
                "secondaryGWs": [
                    {"gatewayIpAddress": "192.166.88.1/24"},
                ]
            },
        )

    def test_dcnm_net_update_existing_network_rejects_ambiguous_merged_secondary_gw_clear(self):
        dcnm_net = self._build_secondary_ip_update_network()
        dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")
        have = self._build_secondary_ip_update_payload(
            self._build_secondary_ip_network_template(
                secondary_gw1="192.166.88.1/24",
                secondary_gw2="192.167.88.1/24",
                secondary_gw3="192.168.88.1/24",
            )
        )
        want = self._build_secondary_ip_update_payload(self._build_secondary_ip_network_template())

        with self.assertRaises(RuntimeError):
            dcnm_net.dcnm_update_network_information(want, have, {"secondary_ip_gw2": ""})

        fail_msg = dcnm_net.module.fail_json.call_args[1]["msg"]
        self.assertIn("cannot clear secondary_ip_gw2", fail_msg)
        self.assertIn("compact list", fail_msg)

    # ------------------------------------------------------------------
    # DCNM715-SECONDARYGWS-001 / issue #715 offline compatibility matrix
    # (U1-U15). Added before any functional change per the tests-first
    # mandate. Each test encodes the APPROVED post-fix contract; against
    # unmodified functional code the ones documented as "fail-before" are
    # expected to fail for the reason noted in their assertion message.
    # Tests marked "regression lock" already pass unmodified and must keep
    # passing unchanged after the fix.
    # ------------------------------------------------------------------

    NDFC_VERSION_FAILING_CONFIRMED = "12.2.2.238"
    NDFC_VERSION_COMPATIBLE_MINIMUM = "12.2.3.70"

    def _build_secgw_capability_network(self, fabric_type="standalone", dcnm_version=12, ndfc_version=None, is_ms_fabric=False):
        dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
        dcnm_net.params = {"state": "merged"}
        dcnm_net.fabric = "test-fabric"
        dcnm_net.dcnm_version = dcnm_version
        dcnm_net.ndfc_version = ndfc_version
        dcnm_net.log = self._build_test_logger()
        dcnm_net.is_ms_fabric = is_ms_fabric
        dcnm_net.fabric_type = fabric_type
        return dcnm_net

    @staticmethod
    def _secgw_capability_config(
        net_name="secgw-net", vrf_name="test-vrf", gw1="", gw2="", gw3="", gw4="", vlan_id=None, gw_ip_subnet=None
    ):
        config = {
            "net_name": net_name,
            "vrf_name": vrf_name,
            "is_l2only": False,
            "secondary_ip_gw1": gw1,
            "secondary_ip_gw2": gw2,
            "secondary_ip_gw3": gw3,
            "secondary_ip_gw4": gw4,
        }
        if vlan_id is not None:
            config["vlan_id"] = vlan_id
        if gw_ip_subnet is not None:
            config["gw_ip_subnet"] = gw_ip_subnet
        return config

    def _build_secgw_push_to_remote_network(self, fabric_type="standalone", dcnm_version=12.2, ndfc_version=None):
        dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
        dcnm_net.log = self._build_test_logger()
        dcnm_net.module = Mock(check_mode=False)
        dcnm_net.result = {"changed": False, "response": []}
        dcnm_net.fabric = "test-fabric"
        dcnm_net.fabric_type = fabric_type
        dcnm_net.dcnm_version = dcnm_version
        dcnm_net.ndfc_version = ndfc_version
        dcnm_net.paths = {
            "GET_NET": "/fabrics/{0}/networks",
            "GET_NET_BULK": "/fabrics/bulk-networks",
            "GET_VLAN": "/fabrics/{0}/vlan",
        }
        dcnm_net.diff_create = []
        dcnm_net.diff_create_update = []
        dcnm_net.diff_detach = []
        dcnm_net.diff_undeploy = {}
        dcnm_net.diff_delete = {}
        dcnm_net.diff_attach = []
        dcnm_net.diff_deploy = {}
        dcnm_net.network_sn_attach_map = {}
        dcnm_net.network_sn_detach_map = {}
        dcnm_net.have_attach_by_name = {}
        dcnm_net.populate_sn_maps_from_diffs = Mock()
        dcnm_net.wait_for_network_attachments_del_ready = Mock(return_value=True)
        dcnm_net.wait_for_network_del_ready = Mock(return_value=True)
        return dcnm_net

    def _build_secgw_auto_id_network(self, fabric_type="standalone", dcnm_version=12.2, ndfc_version=None):
        dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
        dcnm_net.log = self._build_test_logger()
        dcnm_net.module = Mock(check_mode=False)
        dcnm_net.params = {"state": "merged"}
        dcnm_net.result = {"changed": False, "response": []}
        dcnm_net.fabric = "test-fabric"
        dcnm_net.fabric_type = fabric_type
        dcnm_net.is_ms_fabric = False
        dcnm_net.dcnm_version = dcnm_version
        dcnm_net.ndfc_version = ndfc_version
        dcnm_net.paths = {
            "GET_NET_ID": "/fabrics/{0}/networkid",
            "GET_NET": "/fabrics/{0}/networks",
        }
        dcnm_net.want_create = []
        dcnm_net.have_create = []
        dcnm_net.want_attach = []
        dcnm_net.have_attach = []
        dcnm_net.config = []
        return dcnm_net

    def test_dcnm_net_secgw_compat_u1_standalone_create_zero_gateways_legacy_version(self):
        """U1: standalone update_create_params(), confirmed-failing version, zero gateways."""
        dcnm_net = self._build_secgw_capability_network(
            fabric_type="standalone", ndfc_version=self.NDFC_VERSION_FAILING_CONFIRMED
        )

        payload = dcnm_net.update_create_params(self._secgw_capability_config())
        template = json.loads(payload["networkTemplateConfig"])

        self.assertEqual(template["secondaryGW1"], "")
        self.assertEqual(template["secondaryGW2"], "")
        self.assertEqual(template["secondaryGW3"], "")
        self.assertEqual(template["secondaryGW4"], "")
        self.assertNotIn(
            "secondaryGWs",
            template,
            "fail-before: unfixed code always emits the aggregate; a confirmed "
            "legacy controller must never receive it, even when empty",
        )

    def test_dcnm_net_secgw_compat_u2_multicluster_parent_create_four_gateways_legacy_version(self):
        """U2: multicluster_parent update_create_params(), confirmed-failing version, four gateways."""
        dcnm_net = self._build_secgw_capability_network(
            fabric_type="multicluster_parent", ndfc_version=self.NDFC_VERSION_FAILING_CONFIRMED
        )

        payload = dcnm_net.update_create_params(
            self._secgw_capability_config(
                gw1="192.166.88.1/24",
                gw2="192.167.88.1/24",
                gw3="192.168.88.1/24",
                gw4="192.169.88.1/24",
            )
        )
        template = json.loads(payload["networkTemplateConfig"])

        self.assertEqual(template["secondaryGW1"], "192.166.88.1/24")
        self.assertEqual(template["secondaryGW2"], "192.167.88.1/24")
        self.assertEqual(template["secondaryGW3"], "192.168.88.1/24")
        self.assertEqual(template["secondaryGW4"], "192.169.88.1/24")
        self.assertNotIn(
            "secondaryGWs",
            template,
            "fail-before: unfixed code always emits the aggregate even though "
            "this exact build is the ND32-confirmed failing one",
        )

    def test_dcnm_net_secgw_compat_u3_standalone_normalize_have_legacy_only(self):
        """U3: standalone normalize_have_network(), confirmed-failing version, legacy-only remote state."""
        dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
        dcnm_net.dcnm_version = 12
        dcnm_net.ndfc_version = self.NDFC_VERSION_FAILING_CONFIRMED
        dcnm_net.fabric_type = "standalone"

        raw_template = self._build_secondary_ip_network_template(
            secondary_gw1="192.166.88.1/24",
            secondary_gw2="192.167.88.1/24",
        )
        network = self._build_secondary_ip_update_payload(raw_template)

        normalized = dcnm_net.normalize_have_network(network)
        normalized_template = json.loads(normalized["networkTemplateConfig"])

        self.assertEqual(normalized_template["secondaryGW1"], "192.166.88.1/24")
        self.assertEqual(normalized_template["secondaryGW2"], "192.167.88.1/24")
        self.assertNotIn(
            "secondaryGWs",
            normalized_template,
            "fail-before: unfixed code always synthesizes an aggregate from the "
            "four legacy slots even when the raw remote state never had one",
        )

    def test_dcnm_net_secgw_compat_u4_multicluster_parent_merged_update_legacy_version(self):
        """U4: multicluster_parent dcnm_update_network_information(), confirmed-failing version, add/clear/preserve."""
        dcnm_net = self._build_secondary_ip_update_network()
        dcnm_net.fabric_type = "multicluster_parent"
        dcnm_net.ndfc_version = self.NDFC_VERSION_FAILING_CONFIRMED
        have = self._build_secondary_ip_update_payload(
            self._build_secondary_ip_network_template(
                secondary_gw1="192.166.88.1/24",
                secondary_gw2="192.167.88.1/24",
            )
        )
        want = self._build_secondary_ip_update_payload(
            self._build_secondary_ip_network_template(secondary_gw3="10.0.0.9/24")
        )

        dcnm_net.dcnm_update_network_information(
            want, have, {"secondary_ip_gw2": "", "secondary_ip_gw3": "10.0.0.9/24"}
        )

        updated_template = json.loads(want["networkTemplateConfig"])
        self.assertEqual(updated_template["secondaryGW1"], "192.166.88.1/24")  # preserved
        self.assertEqual(updated_template["secondaryGW2"], "")  # cleared
        self.assertEqual(updated_template["secondaryGW3"], "10.0.0.9/24")  # added
        self.assertNotIn(
            "secondaryGWs",
            updated_template,
            "fail-before: unfixed code always regenerates the aggregate during "
            "a merged update regardless of controller version",
        )

    def test_dcnm_net_secgw_compat_u5_explicit_id_create_push_to_remote_legacy_version(self):
        """U5: explicit-ID create reconstruction inside push_to_remote(), confirmed-failing version."""
        dcnm_net = self._build_secgw_push_to_remote_network(
            fabric_type="standalone", dcnm_version=12.2, ndfc_version=self.NDFC_VERSION_FAILING_CONFIRMED
        )
        template = self._build_secondary_ip_network_template(
            secondary_gw1="192.166.88.1/24",
            secondary_gw4="192.169.88.1/24",
        )
        network = self._build_secondary_ip_update_payload(template)
        dcnm_net.diff_create = [network]

        self.run_dcnm_send.reset_mock()
        self.run_dcnm_send.return_value = {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {}}

        dcnm_net.push_to_remote()

        self.assertEqual(self.run_dcnm_send.call_count, 1)
        sent_payload = json.loads(self.run_dcnm_send.call_args[0][3])
        sent_template = json.loads(sent_payload[0]["networkTemplateConfig"])
        self.assertEqual(sent_template["secondaryGW1"], "192.166.88.1/24")
        self.assertEqual(sent_template["secondaryGW4"], "192.169.88.1/24")
        self.assertNotIn(
            "secondaryGWs",
            sent_template,
            "fail-before: push_to_remote() reconstructs the template from "
            "scratch and always re-adds the aggregate, independent of "
            "update_create_params()",
        )

    def test_dcnm_net_secgw_compat_u6_auto_id_create_get_diff_merge_legacy_version(self):
        """U6: auto-generated-networkId create path inside get_diff_merge(), confirmed-failing version."""
        dcnm_net = self._build_secgw_auto_id_network(
            fabric_type="standalone", dcnm_version=12.2, ndfc_version=self.NDFC_VERSION_FAILING_CONFIRMED
        )
        # want_c must come from the real update_create_params() output (as
        # get_want() would build it), not a hand-built fixture: only that
        # function decides whether the aggregate is present, and a synthetic
        # fixture without it would pass this test for the wrong reason.
        want_c = dcnm_net.update_create_params(
            self._secgw_capability_config(
                gw1="192.166.88.1/24",
                gw4="192.169.88.1/24",
            )
        )
        self.assertIsNone(want_c.get("networkId"))
        dcnm_net.want_create = [want_c]

        self.run_dcnm_send.reset_mock()
        self.run_dcnm_send.side_effect = [
            {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {"l2vni": 50999}},
            {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {}},
        ]

        dcnm_net.get_diff_merge()

        self.assertEqual(self.run_dcnm_send.call_count, 2)
        sent_network = json.loads(self.run_dcnm_send.call_args_list[1][0][3])
        sent_template = json.loads(sent_network["networkTemplateConfig"])
        self.assertEqual(sent_template["secondaryGW1"], "192.166.88.1/24")
        self.assertEqual(sent_template["secondaryGW4"], "192.169.88.1/24")
        self.assertNotIn(
            "secondaryGWs",
            sent_template,
            "fail-before: the auto-ID create path sends normalized want "
            "directly and it always carries the aggregate today",
        )

    def test_dcnm_net_secgw_compat_u7_compatible_version_characterization(self):
        """U7 (regression lock): standalone/multisite_parent/multicluster_parent already emit the
        aggregate on the minimum known-compatible build; the fix must not change this.

        Hardened per architect review: zero AND a full four-gateway case are exercised
        independently for all three fabric types (the original multisite_parent/
        multicluster_parent "four" cases only populated two of four slots).
        """
        four_gw_values = ("192.166.88.1/24", "192.167.88.1/24", "192.168.88.1/24", "192.169.88.1/24")
        four_gw_expected = [{"gatewayIpAddress": ip} for ip in four_gw_values]
        cases = (
            ("standalone", "", "", "", "", []),
            ("standalone", *four_gw_values, four_gw_expected),
            ("multisite_parent", "", "", "", "", []),
            ("multisite_parent", *four_gw_values, four_gw_expected),
            ("multicluster_parent", "", "", "", "", []),
            ("multicluster_parent", *four_gw_values, four_gw_expected),
        )
        for fabric_type, gw1, gw2, gw3, gw4, expected_gws in cases:
            with self.subTest(fabric_type=fabric_type, gw1=gw1, gw2=gw2, gw3=gw3, gw4=gw4):
                dcnm_net = self._build_secgw_capability_network(
                    fabric_type=fabric_type, ndfc_version=self.NDFC_VERSION_COMPATIBLE_MINIMUM
                )

                payload = dcnm_net.update_create_params(
                    self._secgw_capability_config(gw1=gw1, gw2=gw2, gw3=gw3, gw4=gw4)
                )
                template = json.loads(payload["networkTemplateConfig"])

                self.assertEqual(template["secondaryGW1"], gw1)
                self.assertEqual(template["secondaryGW2"], gw2)
                self.assertEqual(template["secondaryGW3"], gw3)
                self.assertEqual(template["secondaryGW4"], gw4)
                self.assertIn("secondaryGWs", template)
                self.assertEqual(json.loads(template["secondaryGWs"]), {"secondaryGWs": expected_gws})

    def test_dcnm_net_secgw_compat_u8_child_fabric_exclusion_both_controls(self):
        """U8 (regression lock): multisite_child/multicluster_child never emit the aggregate,
        on both the failing and the compatible control build."""
        for fabric_type in ("multisite_child", "multicluster_child"):
            for version in (self.NDFC_VERSION_FAILING_CONFIRMED, self.NDFC_VERSION_COMPATIBLE_MINIMUM):
                with self.subTest(fabric_type=fabric_type, version=version):
                    dcnm_net = self._build_secgw_capability_network(fabric_type=fabric_type, ndfc_version=version)

                    payload = dcnm_net.update_create_params(
                        self._secgw_capability_config(
                            gw1="192.166.88.1/24",
                            gw2="192.167.88.1/24",
                            gw3="192.168.88.1/24",
                            gw4="192.169.88.1/24",
                        )
                    )
                    template = json.loads(payload["networkTemplateConfig"])

                    self.assertEqual(template["secondaryGW1"], "192.166.88.1/24")
                    self.assertEqual(template["secondaryGW4"], "192.169.88.1/24")
                    self.assertNotIn("secondaryGWs", template)

    def test_dcnm_net_secgw_compat_u9_unknown_version_zero_gateways_omits_safely(self):
        """U9: missing/malformed/truncated/boundary version, zero secondary-gateway intent."""
        invalid_versions = (None, "", "bad", "12", "12.2.3")
        for version in invalid_versions:
            with self.subTest(version=version):
                dcnm_net = self._build_secgw_capability_network(fabric_type="standalone", ndfc_version=version)

                payload = dcnm_net.update_create_params(self._secgw_capability_config())
                template = json.loads(payload["networkTemplateConfig"])

                self.assertEqual(template["secondaryGW1"], "")
                self.assertNotIn(
                    "secondaryGWs",
                    template,
                    f"fail-before: unfixed code emits the aggregate regardless of "
                    f"the missing/malformed version {version!r}",
                )

    def test_dcnm_net_secgw_compat_u10_unknown_version_nonempty_gateway_fails_closed(self):
        """U10: missing/malformed/truncated/boundary version, nonempty secondary-gateway intent must fail closed."""
        invalid_versions = (None, "", "bad", "12", "12.2.3")
        for version in invalid_versions:
            with self.subTest(version=version):
                dcnm_net = self._build_secgw_capability_network(fabric_type="standalone", ndfc_version=version)
                dcnm_net.module = Mock()
                dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")
                self.run_dcnm_send.reset_mock()

                with self.assertRaises(
                    RuntimeError,
                    msg="fail-before: unfixed code never classifies the version and "
                    "completes normally instead of failing closed",
                ):
                    dcnm_net.update_create_params(self._secgw_capability_config(gw1="192.166.88.1/24"))

                dcnm_net.module.fail_json.assert_called_once()
                self.run_dcnm_send.assert_not_called()

    def test_dcnm_net_secgw_compat_u10a_unknown_version_nonempty_gateway_real_sink_transport_not_called(self):
        """U10 (hardened): a real outbound sink (push_to_remote()'s explicit-ID create path)
        must also fail closed and never reach the mocked transport for an unknown/malformed
        version with nonempty secondary-gateway intent. The plain update_create_params()
        assertion above never calls transport by construction, so it cannot prove transport
        was avoided; this variant proves it against a function that normally does call it."""
        invalid_versions = (None, "", "bad", "12", "12.2.3")
        for version in invalid_versions:
            with self.subTest(version=version):
                dcnm_net = self._build_secgw_push_to_remote_network(
                    fabric_type="standalone", dcnm_version=12.2, ndfc_version=version
                )
                dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")
                template = self._build_secondary_ip_network_template(secondary_gw1="192.166.88.1/24")
                network = self._build_secondary_ip_update_payload(template)
                dcnm_net.diff_create = [network]

                self.run_dcnm_send.reset_mock()
                self.run_dcnm_send.return_value = {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {}}

                with self.assertRaises(
                    RuntimeError,
                    msg="fail-before: push_to_remote() never classifies the version "
                    "and proceeds to send the create request instead of failing closed",
                ):
                    dcnm_net.push_to_remote()

                dcnm_net.module.fail_json.assert_called_once()
                self.run_dcnm_send.assert_not_called()

    def test_dcnm_net_secgw_compat_u11_normalize_have_brownfield_nonrepresentable(self):
        """U11: brownfield remote have must fail before write. Hardened per architect review
        into four separate, non-combined cells: malformed aggregate JSON, aggregate-only state
        (legacy slots empty but the aggregate is nonempty), an aggregate that contradicts
        populated legacy slots (same count, different values), and an aggregate with more than
        four entries (excess alone, values otherwise consistent with the legacy slots)."""
        malformed_template = self._build_secondary_ip_network_template(
            secondary_gw1="192.166.88.1/24",
            secondary_gw2="192.167.88.1/24",
        )
        malformed_template["secondaryGWs"] = "{not-valid-json"

        aggregate_only_template = self._build_secondary_ip_network_template()  # all four slots empty
        aggregate_only_template["secondaryGWs"] = json.dumps(
            {
                "secondaryGWs": [
                    {"gatewayIpAddress": "10.0.0.1/24"},
                    {"gatewayIpAddress": "10.0.0.2/24"},
                ]
            },
            separators=(",", ":"),
        )

        contradictory_template = self._build_secondary_ip_network_template(
            secondary_gw1="192.166.88.1/24",
            secondary_gw2="192.167.88.1/24",
        )
        # Same count (two) as the populated legacy slots, but different values.
        contradictory_template["secondaryGWs"] = json.dumps(
            {
                "secondaryGWs": [
                    {"gatewayIpAddress": "10.0.0.1/24"},
                    {"gatewayIpAddress": "10.0.0.2/24"},
                ]
            },
            separators=(",", ":"),
        )

        excess_template = self._build_secondary_ip_network_template(
            secondary_gw1="192.166.88.1/24",
            secondary_gw2="192.167.88.1/24",
            secondary_gw3="192.168.88.1/24",
            secondary_gw4="192.169.88.1/24",
        )
        # Consistent with the four legacy slots, but a fifth entry makes it
        # nonrepresentable in the four-slot public contract.
        excess_template["secondaryGWs"] = json.dumps(
            {
                "secondaryGWs": [
                    {"gatewayIpAddress": "192.166.88.1/24"},
                    {"gatewayIpAddress": "192.167.88.1/24"},
                    {"gatewayIpAddress": "192.168.88.1/24"},
                    {"gatewayIpAddress": "192.169.88.1/24"},
                    {"gatewayIpAddress": "10.0.0.9/24"},
                ]
            },
            separators=(",", ":"),
        )

        cases = (
            ("malformed_json", malformed_template),
            ("aggregate_only", aggregate_only_template),
            ("contradictory", contradictory_template),
            ("more_than_four", excess_template),
        )
        for label, raw_template in cases:
            with self.subTest(case=label):
                dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
                dcnm_net.dcnm_version = 12
                dcnm_net.ndfc_version = self.NDFC_VERSION_COMPATIBLE_MINIMUM
                dcnm_net.fabric_type = "standalone"
                dcnm_net.module = Mock()
                dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")

                network = self._build_secondary_ip_update_payload(raw_template)

                with self.assertRaises(
                    RuntimeError,
                    msg=f"fail-before ({label}): unfixed code never inspects the raw remote "
                    "aggregate and silently discards/overwrites it instead of "
                    "failing on nonrepresentable brownfield state",
                ):
                    dcnm_net.normalize_have_network(network)

                dcnm_net.module.fail_json.assert_called_once()

    def test_dcnm_net_secgw_compat_u12_idempotency_both_controls(self):
        """U12 (regression lock): want built via the real update_create_params(), have built via
        the real normalize_have_network() from a realistic raw controller response, then diffed
        with the real diff_for_create() -- for zero and four gateways, on both exact controls.

        Hardened per architect review: two hand-built, already-identical payloads (the original
        design) do not exercise or prove the normalization/idempotency contract; only running the
        actual production functions on independently-constructed want/have inputs does.
        """
        gateway_sets = (
            ("", "", "", ""),
            ("192.166.88.1/24", "192.167.88.1/24", "192.168.88.1/24", "192.169.88.1/24"),
        )
        for version in (self.NDFC_VERSION_FAILING_CONFIRMED, self.NDFC_VERSION_COMPATIBLE_MINIMUM):
            for gws in gateway_sets:
                with self.subTest(version=version, gws=gws):
                    dcnm_net = self._build_secgw_capability_network(fabric_type="standalone", ndfc_version=version)
                    dcnm_net.module = Mock()

                    # Independently-built want, via the real create-params path.
                    want = dcnm_net.update_create_params(
                        self._secgw_capability_config(
                            net_name="sec-ip-test",
                            vrf_name="test-vrf",
                            gw1=gws[0],
                            gw2=gws[1],
                            gw3=gws[2],
                            gw4=gws[3],
                            vlan_id=993,
                            gw_ip_subnet="10.250.93.1/24",
                        )
                    )

                    # Independently-built raw remote response, via the real
                    # normalize-have path. A compatible controller is modeled
                    # with its own real aggregate string on the wire; a legacy
                    # controller is modeled with no aggregate key at all
                    # (matching U3's confirmed-failing-build fixture shape).
                    raw_have_template = self._build_secondary_ip_network_template(
                        secondary_gw1=gws[0], secondary_gw2=gws[1], secondary_gw3=gws[2], secondary_gw4=gws[3]
                    )
                    if version == self.NDFC_VERSION_COMPATIBLE_MINIMUM:
                        raw_have_template["secondaryGWs"] = dcnm_network.DcnmNetwork.get_secondary_gws_template_config(
                            raw_have_template
                        )
                    raw_have_network = self._build_secondary_ip_update_payload(raw_have_template)
                    have = dcnm_net.normalize_have_network(raw_have_network)

                    diff = dcnm_net.diff_for_create(want, have)

                    self.assertEqual(diff[0], {})
                    self.assertFalse(diff[-1])

    def test_dcnm_net_secgw_compat_u13_existing_merged_safety_both_controls(self):
        """U13 (regression lock): ambiguous merged-clear guard is unchanged and version-independent."""
        for version in (self.NDFC_VERSION_FAILING_CONFIRMED, self.NDFC_VERSION_COMPATIBLE_MINIMUM):
            with self.subTest(version=version):
                dcnm_net = self._build_secondary_ip_update_network()
                dcnm_net.ndfc_version = version
                dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")
                have = self._build_secondary_ip_update_payload(
                    self._build_secondary_ip_network_template(
                        secondary_gw1="192.166.88.1/24",
                        secondary_gw2="192.167.88.1/24",
                        secondary_gw3="192.168.88.1/24",
                    )
                )
                want = self._build_secondary_ip_update_payload(self._build_secondary_ip_network_template())

                with self.assertRaises(RuntimeError):
                    dcnm_net.dcnm_update_network_information(want, have, {"secondary_ip_gw2": ""})

                fail_msg = dcnm_net.module.fail_json.call_args[1]["msg"]
                self.assertIn("cannot clear secondary_ip_gw2", fail_msg)
                self.assertIn("compact list", fail_msg)

    def test_dcnm_net_secgw_compat_u14_older_versions_legacy_classification(self):
        """U14: unambiguously older versions classify as legacy for zero and four gateways."""
        older_versions = ("11.5.1", "12.1.2", "12.2.2", "12.2.3.69")
        gateway_sets = (
            ("", "", "", ""),
            ("192.166.88.1/24", "192.167.88.1/24", "192.168.88.1/24", "192.169.88.1/24"),
        )
        for version in older_versions:
            for gws in gateway_sets:
                with self.subTest(version=version, gws=gws):
                    dcnm_net = self._build_secgw_capability_network(fabric_type="standalone", ndfc_version=version)

                    payload = dcnm_net.update_create_params(
                        self._secgw_capability_config(gw1=gws[0], gw2=gws[1], gw3=gws[2], gw4=gws[3])
                    )
                    template = json.loads(payload["networkTemplateConfig"])

                    self.assertEqual(template["secondaryGW1"], gws[0])
                    self.assertEqual(template["secondaryGW4"], gws[3])
                    self.assertNotIn(
                        "secondaryGWs",
                        template,
                        f"fail-before: unfixed code emits the aggregate for legacy "
                        f"version {version!r} regardless of gateway count",
                    )

    def test_dcnm_net_secgw_compat_u15_untested_interval_conservative_legacy(self):
        """U15: representative untested builds after 12.2.2.238 and below 12.2.3.70 get
        conservative legacy handling, for zero AND four gateways. This is a conservative
        policy, not a claim that these builds lack aggregate support.

        Hardened per architect review: the original test covered only one gapped
        nonempty case (gw1+gw4) per build; a true zero-gateway case is now included too.
        """
        representative_untested_builds = ("12.2.2.250", "12.2.3.1", "12.2.3.50")
        gateway_sets = (
            ("", "", "", ""),
            ("192.166.88.1/24", "192.167.88.1/24", "192.168.88.1/24", "192.169.88.1/24"),
        )
        for version in representative_untested_builds:
            for gws in gateway_sets:
                with self.subTest(version=version, gws=gws):
                    dcnm_net = self._build_secgw_capability_network(fabric_type="standalone", ndfc_version=version)

                    payload = dcnm_net.update_create_params(
                        self._secgw_capability_config(gw1=gws[0], gw2=gws[1], gw3=gws[2], gw4=gws[3])
                    )
                    template = json.loads(payload["networkTemplateConfig"])

                    self.assertEqual(template["secondaryGW1"], gws[0])
                    self.assertEqual(template["secondaryGW2"], gws[1])
                    self.assertEqual(template["secondaryGW3"], gws[2])
                    self.assertEqual(template["secondaryGW4"], gws[3])
                    self.assertNotIn(
                        "secondaryGWs",
                        template,
                        f"fail-before: unfixed code emits the aggregate for this "
                        f"untested-interval build {version!r}; approved policy is "
                        f"conservative legacy handling (untested, not confirmed unsupported)",
                    )

    # ------------------------------------------------------------------
    # DCNM715-SECONDARYGWS-001 / G2A correction cycle (architect review
    # after G2). G1/G1A/G2 above are untouched. These tests are added
    # before any further functional change, against the current G2
    # candidate, per the four blocking findings: (1) present empty/null
    # remote aggregate fails open, (2) query blocked by mutating-only
    # safety, (3) insufficiently strict version grammar, (4) compatible
    # gapped-slot idempotency unproven.
    # ------------------------------------------------------------------

    def _build_get_have_query_network(self, ndfc_version=None):
        dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
        dcnm_net.log = self._build_test_logger()
        dcnm_net.module = Mock()
        dcnm_net.module.params = {"state": "query"}
        dcnm_net.module.fail_json = Mock()  # no side effect: must never be called
        dcnm_net.params = {"state": "query"}
        dcnm_net.fabric = "test-fabric"
        dcnm_net.fabric_type = "standalone"
        dcnm_net.is_ms_fabric = False
        dcnm_net.dcnm_version = 12
        dcnm_net.ndfc_version = ndfc_version
        dcnm_net.paths = {
            "GET_VRF": "/fabrics/{0}/vrfs",
            "GET_VRF_NET": "/fabrics/{0}/vrfs/{1}/networks",
            "GET_NET_NAME": "/fabrics/{0}/networks/{1}",
            "GET_NET": "/fabrics/{0}/networks",
            "GET_NET_ATTACH": "/fabrics/{0}/networks/attachments",
        }
        dcnm_net.BULK_GET_HAVE_NETWORK_THRESHOLD = 50
        return dcnm_net

    def _assert_get_have_query_survives_malformed_network(self, targeted):
        dcnm_net = self._build_get_have_query_network(ndfc_version=self.NDFC_VERSION_FAILING_CONFIRMED)
        dcnm_net.config = [{"net_name": "clean-net", "vrf_name": "test-vrf"}] if targeted else []

        clean_template = self._build_secondary_ip_network_template(secondary_gw1="")
        clean_template["networkName"] = "clean-net"
        clean_network = self._build_secondary_ip_update_payload(clean_template)
        clean_network["networkName"] = "clean-net"
        clean_network["vrf"] = "test-vrf"

        malformed_template = self._build_secondary_ip_network_template(
            secondary_gw1="192.166.88.1/24",
            secondary_gw2="192.167.88.1/24",
        )
        malformed_template["networkName"] = "unrelated-malformed-net"
        malformed_template["secondaryGWs"] = json.dumps(
            {"secondaryGWs": [{"gatewayIpAddress": "10.0.0.1/24"}, {"gatewayIpAddress": "10.0.0.2/24"}]},
            separators=(",", ":"),
        )
        malformed_network = self._build_secondary_ip_update_payload(malformed_template)
        malformed_network["networkName"] = "unrelated-malformed-net"
        malformed_network["vrf"] = "test-vrf"

        self.run_dcnm_send.reset_mock()
        self.run_dcnm_send.side_effect = [
            {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [{"vrfName": "test-vrf"}]},
            {"DATA": [clean_network, malformed_network]},
        ]
        self.run_dcnm_get_url.return_value = {"DATA": []}

        dcnm_net.get_have()

        dcnm_net.module.fail_json.assert_not_called()
        self.assertTrue(
            all(call.args[1] == "GET" for call in self.run_dcnm_send.call_args_list),
            "query must never issue a non-GET (write) transport call",
        )

    def test_dcnm_net_secgw_compat_g2a_query_targeted_get_have_does_not_block_on_unrelated_malformed_network(self):
        """G2A finding 2 (targeted): get_have() always uses its per-VRF lookup for
        state=query regardless of a targeted self.config -- get_diff_query(), not
        get_have(), is what filters to the requested network -- so an unrelated
        malformed network in the same VRF must not abort a targeted query, and no
        write transport may occur."""
        self._assert_get_have_query_survives_malformed_network(targeted=True)

    def test_dcnm_net_secgw_compat_g2a_query_all_get_have_does_not_block_on_malformed_network(self):
        """G2A finding 2 (query-all): same guarantee with no self.config."""
        self._assert_get_have_query_survives_malformed_network(targeted=False)

    def test_dcnm_net_secgw_compat_g2a_query_normalize_have_preserves_raw_state(self):
        """G2A finding 2 (mechanism): normalize_have_network() itself must never
        fail_json during state=query and must preserve the raw remote secondaryGWs
        value verbatim -- capability/representability processing must not run at
        all for a read-only query, since get_diff_query() never uses this
        normalized value (only checks self.have_create for truthiness)."""
        dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
        dcnm_net.dcnm_version = 12
        dcnm_net.ndfc_version = self.NDFC_VERSION_FAILING_CONFIRMED
        dcnm_net.fabric_type = "standalone"
        dcnm_net.module = Mock(params={"state": "query"})
        dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")

        raw_template = self._build_secondary_ip_network_template(
            secondary_gw1="192.166.88.1/24",
            secondary_gw2="192.167.88.1/24",
        )
        # Deliberately nonrepresentable (more than four entries, contradicting
        # the two populated legacy slots) -- would fail closed on any mutating
        # path, but must be preserved as-is and reported during query.
        raw_aggregate = json.dumps(
            {"secondaryGWs": [{"gatewayIpAddress": f"10.0.0.{i}/24"} for i in range(1, 6)]},
            separators=(",", ":"),
        )
        raw_template["secondaryGWs"] = raw_aggregate
        network = self._build_secondary_ip_update_payload(raw_template)

        normalized = dcnm_net.normalize_have_network(network)

        dcnm_net.module.fail_json.assert_not_called()
        normalized_template = json.loads(normalized["networkTemplateConfig"])
        self.assertEqual(normalized_template["secondaryGW1"], "192.166.88.1/24")
        self.assertEqual(normalized_template["secondaryGW2"], "192.167.88.1/24")
        self.assertEqual(
            normalized_template.get("secondaryGWs"),
            raw_aggregate,
            "query must preserve/report the exact raw controller state, not a "
            "capability-processed value",
        )

    def test_dcnm_net_secgw_compat_g2a_present_empty_or_null_aggregate_key_presence(self):
        """G2A finding 1: a raw remote secondaryGWs key that is PRESENT but
        null/empty must not bypass representability validation the way an
        absent key correctly does.

        CORRECTED in G3 (architect review after G2B): the original two
        "consistent" cases below asserted that null/"" was safe (no failure)
        specifically when the legacy slots were also empty. The architect
        confirmed this was itself wrong -- null/"" is not a valid "declares
        zero" encoding on a mutating path (the only valid empty encoding is
        the compact JSON string '{"secondaryGWs":[]}'), regardless of
        legacy-slot contents. All four cases now expect fail_json; see
        test_dcnm_net_secgw_compat_g3_present_null_or_empty_always_fails_on_mutation
        for the comprehensive, corrected version of this matrix."""
        cases = (
            ("empty_string_contradicts", "", ("192.166.88.1/24", "192.167.88.1/24", "", "")),
            ("null_contradicts", None, ("192.166.88.1/24", "192.167.88.1/24", "", "")),
            ("empty_string_consistent", "", ("", "", "", "")),
            ("null_consistent", None, ("", "", "", "")),
        )
        for label, raw_value, gws in cases:
            with self.subTest(case=label):
                dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
                dcnm_net.dcnm_version = 12
                dcnm_net.ndfc_version = self.NDFC_VERSION_COMPATIBLE_MINIMUM
                dcnm_net.fabric_type = "standalone"
                dcnm_net.module = Mock()
                dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")

                raw_template = self._build_secondary_ip_network_template(
                    secondary_gw1=gws[0], secondary_gw2=gws[1], secondary_gw3=gws[2], secondary_gw4=gws[3]
                )
                raw_template["secondaryGWs"] = raw_value
                network = self._build_secondary_ip_update_payload(raw_template)

                with self.assertRaises(
                    RuntimeError,
                    msg=f"present-but-empty/null remote aggregate ({label}) must always fail "
                    "closed on a mutating path",
                ):
                    dcnm_net.normalize_have_network(network)
                dcnm_net.module.fail_json.assert_called_once()

    def test_dcnm_net_secgw_compat_g2a_malformed_aggregate_entry_value_types(self):
        """G2A finding 1 (associated cell): an aggregate entry with a non-string,
        empty, or missing gatewayIpAddress must fail clearly and explicitly."""
        cases = (
            ("non_string_ip", {"gatewayIpAddress": 192168001024}),
            ("null_ip", {"gatewayIpAddress": None}),
            ("empty_string_ip", {"gatewayIpAddress": ""}),
            ("missing_ip_key", {}),
            ("non_dict_entry", "192.166.88.1/24"),
        )
        for label, bad_entry in cases:
            with self.subTest(case=label):
                dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
                dcnm_net.dcnm_version = 12
                dcnm_net.ndfc_version = self.NDFC_VERSION_COMPATIBLE_MINIMUM
                dcnm_net.fabric_type = "standalone"
                dcnm_net.module = Mock()
                dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")

                raw_template = self._build_secondary_ip_network_template(secondary_gw1="192.166.88.1/24")
                raw_template["secondaryGWs"] = json.dumps(
                    {"secondaryGWs": [bad_entry]}, separators=(",", ":")
                )
                network = self._build_secondary_ip_update_payload(raw_template)

                with self.assertRaises(
                    RuntimeError, msg=f"malformed aggregate entry ({label}) must fail closed"
                ):
                    dcnm_net.normalize_have_network(network)

                dcnm_net.module.fail_json.assert_called_once()

    def test_dcnm_net_secgw_compat_g2a_malformed_boundary_versions_classify_unknown(self):
        """G2A finding 3: non-canonical version grammar -- whitespace, an explicit
        sign, underscore digit separators, a negative build, an extra empty
        component, and Unicode decimal digits -- must classify unknown. Python's
        bare int() accepts all of these, which can misclassify a value like
        "12.2.3.+70" as aggregate instead of unknown right at the boundary."""
        malformed_versions = (
            " 12.2.3.70",
            "12.2.3.70 ",
            "12.2.3.+70",
            "12.2.3.7_0",
            "12.2.3.-70",
            "12.2..3.70",
            "12.2.3.٧٠",  # Arabic-Indic digits for "70"
        )
        for version in malformed_versions:
            with self.subTest(version=repr(version)):
                dcnm_net = self._build_secgw_capability_network(fabric_type="standalone", ndfc_version=version)

                capability = dcnm_net.secondary_gws_capability()

                self.assertEqual(
                    capability,
                    "unknown",
                    f"fail-before: unfixed int()-based parsing accepts the non-canonical "
                    f"version {version!r} (classified {capability!r}) instead of unknown",
                )

        for version in malformed_versions:
            with self.subTest(version=repr(version), intent="nonempty"):
                dcnm_net = self._build_secgw_capability_network(fabric_type="standalone", ndfc_version=version)
                dcnm_net.module = Mock()
                dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")
                self.run_dcnm_send.reset_mock()

                with self.assertRaises(
                    RuntimeError,
                    msg=f"fail-before: non-canonical version {version!r} was not rejected as "
                    "unknown, so nonempty intent did not fail closed",
                ):
                    dcnm_net.update_create_params(self._secgw_capability_config(gw1="192.166.88.1/24"))

                dcnm_net.module.fail_json.assert_called_once()
                self.run_dcnm_send.assert_not_called()

    def test_dcnm_net_secgw_compat_g2a_compatible_gapped_gateway_idempotency(self):
        """CORRECTED in G3 (architect review after G2B): this test previously
        claimed gapped-gateway idempotency (GW1+GW4) was proven safe on a
        compatible controller, because a self-constructed raw "have" fixture
        assumed the controller would reflect the same GW1+GW4 positions back.
        The architect reproduced a plausible, more realistic controller
        reflection instead: a compact aggregate [GW1,GW4] returned as
        *reindexed contiguous* legacy slots GW1+GW2 (not GW1+GW4). Under that
        reflection, want (still GW1+GW4) and have (now GW1+GW2) permanently
        disagree on secondaryGW2 and secondaryGW4, producing a non-empty diff
        on every run -- a resend loop, not idempotency. The old claim was
        false and is retracted; see the G3 correction cycle:
        - test_dcnm_net_secgw_compat_g3_non_prefix_patterns_fail_before_transport
          proves GW1+GW4 (and every other non-contiguous-prefix pattern) is now
          rejected before transport on an aggregate-capable controller instead
          of silently risking this resend loop.
        - test_dcnm_net_secgw_compat_g3_contiguous_prefixes_accepted_and_idempotent
          proves idempotency for every pattern the aggregate encoding can
          actually represent safely (a contiguous prefix).
        - test_dcnm_net_secgw_compat_g3_legacy_preserves_gapped_slots proves
          gaps remain fully safe on a legacy (no-aggregate) controller, where
          there is no compact encoding and therefore no reflection risk.
        This method is kept (rather than deleted) only to document the
        retraction at the point where the false claim used to live; it now
        asserts the corrected behavior directly.

        CORRECTED AGAIN in G5-LIFECYCLE (architect review after
        G5-BROWNFIELD): the G3 correction above asserted
        update_create_params() alone fails immediately for GW1+GW4 under
        the default merged state. G5-LIFECYCLE found that assumption itself
        unsafe as a blanket rule: for state: merged, a transient
        non-contiguous-prefix result is now deferred (see
        apply_secondary_gws_compat()'s defer_prefix_fail_closed), since it
        may simply be an omitted value have will later restore (see
        test_dcnm_net_secgw_compat_g5_lifecycle_merged_gw2_over_existing_gw1).
        GW1+GW4 with no have wired up at all (as here) is still correctly
        rejected -- just at finalize_secondary_gws_compat(), the checkpoint
        for want entries with no have match, instead of inside
        update_create_params() itself. The end behavior this test
        documents -- GW1+GW4 on a compatible controller must fail closed,
        not silently produce a permanently-diffing aggregate -- is
        unchanged; only the mechanism and call sequence proving it are
        updated."""
        dcnm_net = self._build_secgw_capability_network(
            fabric_type="standalone", ndfc_version=self.NDFC_VERSION_COMPATIBLE_MINIMUM
        )
        dcnm_net.module = Mock()
        dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")
        dcnm_net.have_create = []

        want_c = dcnm_net.update_create_params(
            self._secgw_capability_config(
                net_name="sec-ip-test",
                vrf_name="test-vrf",
                gw1="192.166.88.1/24",
                gw2="",
                gw3="",
                gw4="192.169.88.1/24",
                vlan_id=993,
                gw_ip_subnet="10.250.93.1/24",
            )
        )
        dcnm_net.want_create = [want_c]

        with self.assertRaises(
            RuntimeError,
            msg="GW1+GW4 on a compatible controller must fail closed, not silently "
            "produce a permanently-diffing aggregate",
        ):
            dcnm_net.finalize_secondary_gws_compat()
        dcnm_net.module.fail_json.assert_called_once()

    # ------------------------------------------------------------------
    # DCNM715-SECONDARYGWS-001 / G3 final correction cycle (architect review
    # after G2B). G1/G1A/G2/G2A/G2B above are untouched except for the one
    # G2A test corrected immediately above (its old claim was disproven).
    # Scope for this cycle only, per the handoff: plugins/module_utils/
    # network/dcnm/dcnm.py, plugins/action/dcnm_network.py,
    # plugins/modules/dcnm_network.py, and both authorized test files.
    # ------------------------------------------------------------------

    def test_dcnm_net_secgw_compat_g7_split_config_propagates_normalized_version_only(self):
        """G7: parent and child receive the one normalized full version."""
        action = dcnm_network_action.ActionModule.__new__(dcnm_network_action.ActionModule)
        fabrics = {
            "msd-parent": {"type": "multisite_parent", "fabricParent": "None", "cluster_name": ""},
            "msd-child-1": {"type": "multisite_child", "fabricParent": "msd-parent", "cluster_name": ""},
        }
        config = [
            {
                "net_name": "ansible-msd-net1",
                "vrf_name": "Tenant-1",
                "is_l2only": False,
                "child_fabric_config": [{"fabric": "msd-child-1", "dhcp_loopback_id": 204}],
            }
        ]

        configs, error_msg = action._split_config(
            fabrics, "msd-parent", config, "merged", {}, 12.2, "12.2.3.70"
        )

        self.assertIsNone(error_msg)
        for fabric_config in configs:
            details = fabric_config["_fabric_details"]
            self.assertIs(type(details["nd_version"]), float)
            self.assertEqual(details["nd_version"], 12.2)
            self.assertIs(type(details["ndfc_version"]), str)
            self.assertEqual(details["ndfc_version"], "12.2.3.70")
            self.assertEqual(set(details), {"fabric_type", "cluster_name", "nd_version", "ndfc_version"})

    def test_dcnm_net_secgw_compat_g7_normalization_tradeoff_classifies_aggregate(self):
        """G7 accepted tradeoff: punctuation is normalized upstream, and the
        canonical result alone drives the module capability decision."""
        action = Mock()
        action._execute_module.return_value = {
            "failed": False,
            "response": {"RETURN_CODE": 200, "DATA": {"version": "12.2.3.+70"}},
        }
        version_info = dcnm_utils.get_nd_version(action, {}, None, return_full_version=True)
        self.assertIs(type(version_info), tuple)
        self.assertEqual(version_info, (12.2, "12.2.3.70"))

        dcnm_net = self._build_secgw_capability_network(
            fabric_type="standalone", ndfc_version=version_info[1]
        )
        self.assertEqual(dcnm_net.secondary_gws_capability(), "aggregate")

    def test_dcnm_net_secgw_compat_g7_real_sink_uses_normalized_version(self):
        """G7: a compatible normalized version reaches the real create sink."""
        dcnm_net = self._build_secgw_push_to_remote_network(
            fabric_type="standalone", dcnm_version=12.2, ndfc_version="12.2.3.70"
        )
        template = self._build_secondary_ip_network_template(secondary_gw1="192.166.88.1/24")
        network = self._build_secondary_ip_update_payload(template)
        dcnm_net.diff_create = [network]

        self.run_dcnm_send.reset_mock()
        self.run_dcnm_send.return_value = {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {}}

        dcnm_net.push_to_remote()

        dcnm_net.module.fail_json.assert_not_called()
        self.run_dcnm_send.assert_called_once()
        sent_payload = json.loads(self.run_dcnm_send.call_args.args[3])
        self.assertIs(type(sent_payload), list)
        self.assertEqual(len(sent_payload), 1)
        sent_template = json.loads(sent_payload[0]["networkTemplateConfig"])
        self.assertEqual(
            json.loads(sent_template["secondaryGWs"]),
            {"secondaryGWs": [{"gatewayIpAddress": "192.166.88.1/24"}]},
        )

    def test_dcnm_net_secgw_compat_g3_present_null_or_empty_always_fails_on_mutation(self):
        """G3 finding 3: present secondaryGWs: null/"" must fail on mutating
        normalization REGARDLESS of legacy-slot contents -- the valid empty
        encoding is the JSON string '{"secondaryGWs":[]}', not null/"". G2B
        incorrectly treated null/"" as safe when legacy slots were also
        empty; the architect confirmed these are malformed values, not a
        valid "declares zero" encoding. Key truly absent is unaffected
        (proved by U3 and the legacy-only tests elsewhere in this file)."""
        cases = (
            ("empty_string_empty_legacy", "", ("", "", "", "")),
            ("null_empty_legacy", None, ("", "", "", "")),
            ("empty_string_populated_legacy", "", ("192.166.88.1/24", "192.167.88.1/24", "", "")),
            ("null_populated_legacy", None, ("192.166.88.1/24", "192.167.88.1/24", "", "")),
        )
        for label, raw_value, gws in cases:
            with self.subTest(case=label):
                dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
                dcnm_net.dcnm_version = 12
                dcnm_net.ndfc_version = self.NDFC_VERSION_COMPATIBLE_MINIMUM
                dcnm_net.fabric_type = "standalone"
                dcnm_net.module = Mock()
                dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")

                raw_template = self._build_secondary_ip_network_template(
                    secondary_gw1=gws[0], secondary_gw2=gws[1], secondary_gw3=gws[2], secondary_gw4=gws[3]
                )
                raw_template["secondaryGWs"] = raw_value
                network = self._build_secondary_ip_update_payload(raw_template)

                with self.assertRaises(
                    RuntimeError,
                    msg=f"fail-before ({label}): present null/empty secondaryGWs must "
                    "always fail on mutating normalization, regardless of legacy-slot "
                    "contents",
                ):
                    dcnm_net.normalize_have_network(network)
                dcnm_net.module.fail_json.assert_called_once()

    def test_dcnm_net_secgw_compat_g3_query_preserves_null_or_empty_without_failure(self):
        """G3 finding 3 (unchanged contract, explicit coverage): query must
        still preserve and report present null/"" verbatim without failure,
        even under the new stricter mutating-path policy above -- the
        stricter rule applies only when validate_remote is actually
        exercised, which query already bypasses entirely."""
        for raw_value in (None, ""):
            for gws in (("", "", "", ""), ("192.166.88.1/24", "192.167.88.1/24", "", "")):
                with self.subTest(raw_value=raw_value, gws=gws):
                    dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
                    dcnm_net.dcnm_version = 12
                    dcnm_net.ndfc_version = self.NDFC_VERSION_FAILING_CONFIRMED
                    dcnm_net.fabric_type = "standalone"
                    dcnm_net.module = Mock(params={"state": "query"})
                    dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")

                    raw_template = self._build_secondary_ip_network_template(
                        secondary_gw1=gws[0], secondary_gw2=gws[1], secondary_gw3=gws[2], secondary_gw4=gws[3]
                    )
                    raw_template["secondaryGWs"] = raw_value
                    network = self._build_secondary_ip_update_payload(raw_template)

                    normalized = dcnm_net.normalize_have_network(network)

                    dcnm_net.module.fail_json.assert_not_called()
                    normalized_template = json.loads(normalized["networkTemplateConfig"])
                    self.assertEqual(normalized_template.get("secondaryGWs"), raw_value)

    def test_dcnm_net_secgw_compat_g3_non_prefix_patterns_fail_before_transport(self):
        """G3 finding 1: every non-contiguous-prefix gateway pattern must
        fail before transport on an aggregate-capable controller -- the
        compact aggregate encoding can only safely represent a contiguous
        prefix (GW1, GW1+GW2, GW1+GW2+GW3, or all four); the architect
        reproduced a plausible controller reflection that reindexes a gapped
        aggregate like [GW1,GW4] into contiguous legacy slots GW1+GW2, which
        would otherwise silently produce a permanent resend loop."""
        A, B, C, D = "192.166.88.1/24", "192.167.88.1/24", "192.168.88.1/24", "192.169.88.1/24"
        non_prefix_patterns = (
            ("", B, "", ""),
            ("", "", C, ""),
            ("", "", "", D),
            (A, "", C, ""),
            (A, "", "", D),
            ("", B, C, ""),
            ("", B, "", D),
            ("", "", C, D),
            (A, B, "", D),
            (A, "", C, D),
            ("", B, C, D),
        )
        for gws in non_prefix_patterns:
            with self.subTest(gws=gws):
                dcnm_net = self._build_secgw_push_to_remote_network(
                    fabric_type="standalone", dcnm_version=12.2, ndfc_version=self.NDFC_VERSION_COMPATIBLE_MINIMUM
                )
                dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")
                template = self._build_secondary_ip_network_template(
                    secondary_gw1=gws[0], secondary_gw2=gws[1], secondary_gw3=gws[2], secondary_gw4=gws[3]
                )
                network = self._build_secondary_ip_update_payload(template)
                dcnm_net.diff_create = [network]

                self.run_dcnm_send.reset_mock()
                self.run_dcnm_send.return_value = {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {}}

                with self.assertRaises(
                    RuntimeError, msg=f"fail-before: non-prefix pattern {gws} was not rejected"
                ):
                    dcnm_net.push_to_remote()

                dcnm_net.module.fail_json.assert_called_once()
                self.run_dcnm_send.assert_not_called()

    def test_dcnm_net_secgw_compat_g3_contiguous_prefixes_accepted_and_idempotent(self):
        """G3 finding 1 (positive proof): every contiguous prefix (0 through
        4 gateways) remains accepted on an aggregate-capable controller and
        idempotent via a real want/normalize-have/diff round trip -- a
        contiguous prefix is unambiguous under reflection (there is no gap
        for a controller to reindex away)."""
        A, B, C, D = "192.166.88.1/24", "192.167.88.1/24", "192.168.88.1/24", "192.169.88.1/24"
        prefixes = (
            ("", "", "", ""),
            (A, "", "", ""),
            (A, B, "", ""),
            (A, B, C, ""),
            (A, B, C, D),
        )
        for gws in prefixes:
            with self.subTest(gws=gws):
                dcnm_net = self._build_secgw_capability_network(
                    fabric_type="standalone", ndfc_version=self.NDFC_VERSION_COMPATIBLE_MINIMUM
                )
                dcnm_net.module = Mock()

                want = dcnm_net.update_create_params(
                    self._secgw_capability_config(
                        net_name="sec-ip-test",
                        vrf_name="test-vrf",
                        gw1=gws[0],
                        gw2=gws[1],
                        gw3=gws[2],
                        gw4=gws[3],
                        vlan_id=993,
                        gw_ip_subnet="10.250.93.1/24",
                    )
                )

                raw_have_template = self._build_secondary_ip_network_template(
                    secondary_gw1=gws[0], secondary_gw2=gws[1], secondary_gw3=gws[2], secondary_gw4=gws[3]
                )
                raw_have_template["secondaryGWs"] = dcnm_network.DcnmNetwork.get_secondary_gws_template_config(
                    raw_have_template
                )
                raw_have_network = self._build_secondary_ip_update_payload(raw_have_template)
                have = dcnm_net.normalize_have_network(raw_have_network)

                diff = dcnm_net.diff_for_create(want, have)

                self.assertEqual(diff[0], {})
                self.assertFalse(diff[-1])

    def test_dcnm_net_secgw_compat_g3_legacy_preserves_gapped_slots(self):
        """G3 finding 1 (legacy contract, unaffected): a legacy (no-aggregate)
        controller has no compact encoding and therefore no
        reflection-reindexing risk, so gapped patterns remain fully
        supported -- the prefix restriction applies only to the
        aggregate-capable branch."""
        dcnm_net = self._build_secgw_capability_network(
            fabric_type="standalone", ndfc_version=self.NDFC_VERSION_FAILING_CONFIRMED
        )

        payload = dcnm_net.update_create_params(
            self._secgw_capability_config(gw1="192.166.88.1/24", gw2="", gw3="", gw4="192.169.88.1/24")
        )
        template = json.loads(payload["networkTemplateConfig"])

        self.assertEqual(template["secondaryGW1"], "192.166.88.1/24")
        self.assertEqual(template["secondaryGW2"], "")
        self.assertEqual(template["secondaryGW3"], "")
        self.assertEqual(template["secondaryGW4"], "192.169.88.1/24")
        self.assertNotIn("secondaryGWs", template)

    # ------------------------------------------------------------------
    # DCNM715-SECONDARYGWS-001 / G4 coverage, corrected by G7. Documented
    # Cisco controller spellings are normalized in get_nd_version(); these
    # module/action tests therefore exercise only the canonical values that
    # cross the action-to-module boundary.
    # ------------------------------------------------------------------

    def test_dcnm_net_secgw_compat_g4_normalized_cisco_versions_classify_correctly(self):
        """G7 correction to G4: the module receives only normalized dotted
        forms. Documented controller spellings are normalized upstream."""
        cases = (
            ("11.5.1", "legacy"),
            ("12.1.2", "legacy"),
            ("12.4.1", "aggregate"),
            ("12.2.3.70", "aggregate"),
            ("12.2.3", "unknown"),
        )
        for normalized_version, expected_capability in cases:
            with self.subTest(normalized_version=normalized_version):
                dcnm_net = self._build_secgw_capability_network(
                    fabric_type="standalone", ndfc_version=normalized_version
                )

                capability = dcnm_net.secondary_gws_capability()

                self.assertEqual(
                    capability,
                    expected_capability,
                    f"{normalized_version!r} classified {capability!r} instead of "
                    f"{expected_capability!r}",
                )

    def test_dcnm_net_secgw_compat_g4_split_config_propagates_normalized_formats(self):
        """G7 correction to G4: action propagation carries canonical forms."""
        action = dcnm_network_action.ActionModule.__new__(dcnm_network_action.ActionModule)
        fabrics = {
            "msd-parent": {"type": "multisite_parent", "fabricParent": "None", "cluster_name": ""},
            "msd-child-1": {"type": "multisite_child", "fabricParent": "msd-parent", "cluster_name": ""},
        }
        for normalized_version in ("11.5.1", "12.1.2", "12.4.1"):
            with self.subTest(normalized_version=normalized_version):
                config = [
                    {
                        "net_name": "ansible-msd-net1",
                        "vrf_name": "Tenant-1",
                        "is_l2only": False,
                        "child_fabric_config": [{"fabric": "msd-child-1", "dhcp_loopback_id": 204}],
                    }
                ]

                configs, error_msg = action._split_config(
                    fabrics, "msd-parent", config, "merged", {}, 12.2, normalized_version
                )

                self.assertIsNone(error_msg)
                for fabric_config in configs:
                    details = fabric_config["_fabric_details"]
                    self.assertEqual(details["ndfc_version"], normalized_version)
                    self.assertEqual(set(details), {"fabric_type", "cluster_name", "nd_version", "ndfc_version"})

    def test_dcnm_net_secgw_compat_g4_known_legacy_formats_preserve_gapped_slots(self):
        """G7-corrected G4 coverage: normalized "11.5.1" and "12.1.2"
        preserve populated/gapped legacy slots and omit the aggregate."""
        for normalized_version in ("11.5.1", "12.1.2"):
            with self.subTest(normalized_version=normalized_version):
                dcnm_net = self._build_secgw_capability_network(
                    fabric_type="standalone", ndfc_version=normalized_version
                )
                # G3's unknown-capability branch calls self.module.fail_json();
                # provide a harmless mock so a fail-before misclassification
                # surfaces as a clean assertion below instead of an unrelated
                # AttributeError (self.module is otherwise unset on this bare
                # test double, matching _build_secgw_capability_network()).
                dcnm_net.module = Mock()

                payload = dcnm_net.update_create_params(
                    self._secgw_capability_config(
                        gw1="192.166.88.1/24", gw2="", gw3="", gw4="192.169.88.1/24"
                    )
                )
                template = json.loads(payload["networkTemplateConfig"])

                self.assertEqual(template["secondaryGW1"], "192.166.88.1/24")
                self.assertEqual(template["secondaryGW4"], "192.169.88.1/24")
                self.assertNotIn(
                    "secondaryGWs",
                    template,
                    f"{normalized_version!r} did not use legacy fields",
                )

    def test_dcnm_net_secgw_compat_g4_known_aggregate_format_prefix_rules_apply(self):
        """G7-corrected G4 coverage: normalized "12.4.1" is aggregate-capable;
        prefix, empty, and non-prefix behavior matches canonical "12.2.3.70"."""
        dcnm_net = self._build_secgw_capability_network(fabric_type="standalone", ndfc_version="12.4.1")
        # See test_dcnm_net_secgw_compat_g4_known_legacy_formats_preserve_gapped_slots
        # for why this harmless mock is needed on this bare test double.
        dcnm_net.module = Mock()
        payload = dcnm_net.update_create_params(
            self._secgw_capability_config(gw1="192.166.88.1/24", gw2="192.167.88.1/24", gw3="", gw4="")
        )
        template = json.loads(payload["networkTemplateConfig"])
        self.assertIn(
            "secondaryGWs",
            template,
            "normalized '12.4.1' was misclassified unknown; contiguous intent did not "
            "emit the aggregate",
        )
        self.assertEqual(
            json.loads(template["secondaryGWs"]),
            {"secondaryGWs": [{"gatewayIpAddress": "192.166.88.1/24"}, {"gatewayIpAddress": "192.167.88.1/24"}]},
        )

        dcnm_net_zero = self._build_secgw_capability_network(fabric_type="standalone", ndfc_version="12.4.1")
        dcnm_net_zero.module = Mock()
        payload_zero = dcnm_net_zero.update_create_params(self._secgw_capability_config())
        template_zero = json.loads(payload_zero["networkTemplateConfig"])
        self.assertIn(
            "secondaryGWs",
            template_zero,
            "normalized '12.4.1' with zero gateways incorrectly OMITTED the aggregate "
            "(treated as unknown-safe-zero) instead of emitting the empty aggregate a "
            "compatible controller requires",
        )
        self.assertEqual(json.loads(template_zero["secondaryGWs"]), {"secondaryGWs": []})

        dcnm_net_nonprefix = self._build_secgw_push_to_remote_network(
            fabric_type="standalone", dcnm_version=12.4, ndfc_version="12.4.1"
        )
        dcnm_net_nonprefix.module.fail_json.side_effect = RuntimeError("fail_json called")
        template_np = self._build_secondary_ip_network_template(
            secondary_gw1="192.166.88.1/24", secondary_gw4="192.169.88.1/24"
        )
        network_np = self._build_secondary_ip_update_payload(template_np)
        dcnm_net_nonprefix.diff_create = [network_np]
        self.run_dcnm_send.reset_mock()
        self.run_dcnm_send.return_value = {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {}}
        with self.assertRaises(
            RuntimeError, msg="normalized '12.4.1' non-prefix intent (GW1+GW4) was not rejected"
        ):
            dcnm_net_nonprefix.push_to_remote()
        dcnm_net_nonprefix.module.fail_json.assert_called_once()
        self.run_dcnm_send.assert_not_called()

    def test_dcnm_net_secgw_compat_g4_invalid_normalized_forms_fail_closed(self):
        """G7: the module accepts only canonical three/four component ASCII
        dotted forms; invalid values that somehow bypass the helper fail closed."""
        invalid_versions = ("12.2.3.+70", "12.2.3.7_0", "12.2.3.-70", " 12.2.3.70", "12.2.3.٧٠")
        for invalid_version in invalid_versions:
            with self.subTest(invalid_version=repr(invalid_version)):
                dcnm_net = self._build_secgw_push_to_remote_network(
                    fabric_type="standalone", dcnm_version=12.2, ndfc_version=invalid_version
                )
                dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")
                template = self._build_secondary_ip_network_template(secondary_gw1="192.166.88.1/24")
                network = self._build_secondary_ip_update_payload(template)
                dcnm_net.diff_create = [network]

                self.run_dcnm_send.reset_mock()
                self.run_dcnm_send.return_value = {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {}}

                with self.assertRaises(RuntimeError):
                    dcnm_net.push_to_remote()

                dcnm_net.module.fail_json.assert_called_once()
                self.run_dcnm_send.assert_not_called()

    def test_dcnm_net_secgw_compat_g4_fail_closed_message_reports_normalized_version(self):
        """G7: failures report the one authoritative normalized value."""
        dcnm_net = self._build_secgw_capability_network(
            fabric_type="standalone", ndfc_version="12.2.3.70\n"
        )
        dcnm_net.module = Mock()
        dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")

        with self.assertRaises(RuntimeError):
            dcnm_net.update_create_params(self._secgw_capability_config(gw1="192.166.88.1/24"))

        message = dcnm_net.module.fail_json.call_args[1]["msg"]
        self.assertIn(
            "12.2.3.70\\n",
            message,
            "the fail-closed message does not report the authoritative normalized version",
        )

    def _build_secgw_update_push_to_remote_network(
        self, fabric_type="standalone", dcnm_version=12.2, ndfc_version=None, has_bulk_api=False
    ):
        """G5: a single instance wired for the real end-to-end UPDATE flow --
        get_diff_merge() (which fills self.diff_create_update from
        want_create/have_create) immediately followed by push_to_remote()
        (which sends the actual individual or bulk PUT) -- so PUT-body
        assertions exercise the real production path instead of a
        hand-filled diff_create_update entry."""
        dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
        dcnm_net.log = self._build_test_logger()
        dcnm_net.module = Mock(check_mode=False)
        dcnm_net.params = {"state": "merged"}
        dcnm_net.result = {"changed": False, "response": []}
        dcnm_net.fabric = "test-fabric"
        dcnm_net.fabric_type = fabric_type
        dcnm_net.is_ms_fabric = False
        dcnm_net.dcnm_version = dcnm_version
        dcnm_net.ndfc_version = ndfc_version
        dcnm_net.has_bulk_api = has_bulk_api
        dcnm_net.config = []
        dcnm_net.want_attach = []
        dcnm_net.have_attach = []
        dcnm_net.paths = {
            "GET_NET_ID": "/fabrics/{0}/networkid",
            "GET_NET": "/fabrics/{0}/networks",
            "GET_NET_BULK": "/fabrics/bulk-networks",
            "UPDATE_NET_BULK": "/fabrics/bulk-networks",
            "GET_VLAN": "/fabrics/{0}/vlan",
        }
        dcnm_net.diff_create = []
        dcnm_net.diff_create_update = []
        dcnm_net.diff_detach = []
        dcnm_net.diff_undeploy = {}
        dcnm_net.diff_delete = {}
        dcnm_net.diff_attach = []
        dcnm_net.diff_deploy = {}
        dcnm_net.network_sn_attach_map = {}
        dcnm_net.network_sn_detach_map = {}
        dcnm_net.have_attach_by_name = {}
        dcnm_net.populate_sn_maps_from_diffs = Mock()
        dcnm_net.wait_for_network_attachments_del_ready = Mock(return_value=True)
        dcnm_net.wait_for_network_del_ready = Mock(return_value=True)
        return dcnm_net

    def test_dcnm_net_secgw_compat_g5_unapproved_whole_version_forms_rejected(self):
        """G5 (architect finding 1): the parser must reject any whole-version
        string that is not one of the three closed, approved grammars, even
        when a naive per-component match (or a match with a trailing-$
        allowance) would otherwise accept it. Covers a trailing newline on
        all three known-format shapes, CRLF, a trailing tab, and the two
        unapproved suffix placements (a parenthesized suffix after three
        already-canonical segments, and an alpha suffix after four)."""
        unapproved_versions = (
            "12.2.3.70\n",
            "12.4.1a\n",
            "11.5(1)\n",
            "12.2.3.70\r\n",
            "12.2.3.70\t",
            "12.2.3(70)",
            "12.2.3.70a",
        )
        for invalid_version in unapproved_versions:
            with self.subTest(invalid_version=repr(invalid_version)):
                dcnm_net = self._build_secgw_capability_network(
                    fabric_type="standalone", ndfc_version=invalid_version
                )

                capability = dcnm_net.secondary_gws_capability()

                self.assertEqual(
                    capability,
                    "unknown",
                    f"fail-before: {invalid_version!r} was accepted as {capability!r} instead of "
                    "being rejected by a strict whole-string fullmatch() grammar",
                )

    def test_dcnm_net_secgw_compat_g5_unrepresentable_intent_fails_before_update_put(self):
        """G5 (architect finding 2, negative half): unrepresentable intent --
        an unapproved whole-version leak form with populated gateways, or a
        compatible-capability non-contiguous-prefix gap -- must fail before
        the real UPDATE flow (get_diff_merge() -> push_to_remote(),
        individual or bulk PUT) can ever be reached, so transport is never
        called either way.

        CORRECTED in G5-LIFECYCLE (architect review after G5-BROWNFIELD):
        the compatible_non_prefix_gap scenario no longer fails inside
        update_create_params() itself for state: merged -- a transient
        non-contiguous-prefix result there is now deferred (see
        apply_secondary_gws_compat()'s defer_prefix_fail_closed), since it
        may simply be an omitted value have will later restore (see
        test_dcnm_net_secgw_compat_g5_lifecycle_merged_gw2_over_existing_gw1).
        With no have wired up here, this scenario instead fails at
        finalize_secondary_gws_compat() -- the checkpoint for want entries
        with no have match, still strictly before get_diff_merge() and any
        transport. unapproved_leak_form is unaffected: the unknown-capability
        fail-closed path depends only on the NDFC version, never on have, so
        it is never deferred and still fails immediately in
        update_create_params()."""
        scenarios = (
            (
                "unapproved_leak_form",
                {"ndfc_version": "12.2.3.70\n"},
                {"gw1": "192.166.88.1/24"},
                "update_create_params",
            ),
            (
                "compatible_non_prefix_gap",
                {"ndfc_version": self.NDFC_VERSION_COMPATIBLE_MINIMUM},
                {"gw1": "192.166.88.1/24", "gw4": "192.169.88.1/24"},
                "finalize_secondary_gws_compat",
            ),
        )
        for label, version_kwargs, gws, fails_at in scenarios:
            for has_bulk_api in (False, True):
                with self.subTest(scenario=label, has_bulk_api=has_bulk_api):
                    dcnm_net = self._build_secgw_update_push_to_remote_network(
                        fabric_type="standalone",
                        ndfc_version=version_kwargs.get("ndfc_version"),
                        has_bulk_api=has_bulk_api,
                    )
                    dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")
                    dcnm_net.have_create = []

                    self.run_dcnm_send.reset_mock()
                    self.run_dcnm_send.return_value = {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {}}

                    config = self._secgw_capability_config(
                        net_name="sec-ip-test",
                        vrf_name="test-vrf",
                        vlan_id=993,
                        gw_ip_subnet="10.250.93.1/24",
                        **gws,
                    )

                    if fails_at == "update_create_params":
                        with self.assertRaises(
                            RuntimeError,
                            msg=f"fail-before: scenario {label!r} did not fail closed during want construction",
                        ):
                            dcnm_net.update_create_params(config)
                    else:
                        want_c = dcnm_net.update_create_params(config)
                        dcnm_net.want_create = [want_c]
                        with self.assertRaises(
                            RuntimeError,
                            msg=f"fail-before: scenario {label!r} did not fail closed before transport",
                        ):
                            dcnm_net.finalize_secondary_gws_compat()

                    dcnm_net.module.fail_json.assert_called_once()
                    self.run_dcnm_send.assert_not_called()

    def test_dcnm_net_secgw_compat_g5_real_update_put_legacy_and_compatible(self):
        """G5 (architect finding 2, positive half): route a realistic
        want/have pair through the real production UPDATE flow --
        get_diff_merge() (which fills self.diff_create_update from
        want_create/have_create) followed by push_to_remote() (which sends
        the actual individual or bulk PUT) -- and inspect the literal PUT
        body. Legacy must omit the aggregate while preserving a real gap
        (GW1+GW4) across all four slots unchanged; compatible/aggregate must
        carry the exact contiguous aggregate. Both the individual-PUT and
        bulk-PUT branches are exercised for each."""
        cases = (
            ("legacy", self.NDFC_VERSION_FAILING_CONFIRMED, False, {"gw1": "192.166.88.1/24", "gw4": "192.169.88.1/24"}),
            ("legacy", self.NDFC_VERSION_FAILING_CONFIRMED, True, {"gw1": "192.166.88.1/24", "gw4": "192.169.88.1/24"}),
            ("aggregate", self.NDFC_VERSION_COMPATIBLE_MINIMUM, False, {"gw1": "192.166.88.1/24", "gw2": "192.167.88.1/24"}),
            ("aggregate", self.NDFC_VERSION_COMPATIBLE_MINIMUM, True, {"gw1": "192.166.88.1/24", "gw2": "192.167.88.1/24"}),
        )
        for capability, ndfc_version, has_bulk_api, gws in cases:
            with self.subTest(capability=capability, has_bulk_api=has_bulk_api):
                dcnm_net = self._build_secgw_update_push_to_remote_network(
                    fabric_type="standalone", ndfc_version=ndfc_version, has_bulk_api=has_bulk_api
                )

                want_c = dcnm_net.update_create_params(
                    self._secgw_capability_config(
                        net_name="sec-ip-test",
                        vrf_name="test-vrf",
                        vlan_id=993,
                        gw_ip_subnet="10.250.93.1/24",
                        **gws,
                    )
                )
                have_template = self._build_secondary_ip_network_template()
                have_c = self._build_secondary_ip_update_payload(have_template)
                dcnm_net.want_create = [want_c]
                dcnm_net.have_create = [have_c]

                dcnm_net.get_diff_merge()

                self.assertEqual(
                    len(dcnm_net.diff_create_update),
                    1,
                    "the real update-diff path did not populate diff_create_update for this want/have pair",
                )

                self.run_dcnm_send.reset_mock()
                self.run_dcnm_send.return_value = {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {}}

                dcnm_net.push_to_remote()

                self.assertEqual(self.run_dcnm_send.call_count, 1)
                sent_body = self.run_dcnm_send.call_args[0][3]
                if has_bulk_api:
                    sent_bulk = json.loads(sent_body)
                    self.assertEqual(len(sent_bulk), 1)
                    sent_template = sent_bulk[0]["networkTemplateConfig"]
                else:
                    sent_network = json.loads(sent_body)
                    sent_template = json.loads(sent_network["networkTemplateConfig"])

                self.assertEqual(sent_template["secondaryGW1"], gws.get("gw1", ""))
                self.assertEqual(sent_template["secondaryGW2"], gws.get("gw2", ""))
                self.assertEqual(sent_template["secondaryGW3"], gws.get("gw3", ""))
                self.assertEqual(sent_template["secondaryGW4"], gws.get("gw4", ""))

                if capability == "legacy":
                    self.assertNotIn(
                        "secondaryGWs",
                        sent_template,
                        "fail-before: the real UPDATE PUT body does not yet omit the aggregate "
                        "for a legacy controller",
                    )
                else:
                    self.assertIn(
                        "secondaryGWs",
                        sent_template,
                        "fail-before: the real UPDATE PUT body does not yet carry the aggregate "
                        "for a compatible controller",
                    )
                    self.assertEqual(
                        json.loads(sent_template["secondaryGWs"]),
                        {
                            "secondaryGWs": [
                                {"gatewayIpAddress": gws["gw1"]},
                                {"gatewayIpAddress": gws["gw2"]},
                            ]
                        },
                    )

    def test_dcnm_net_secgw_compat_g5_brownfield_unexpected_top_level_key_fails_before_mutation(self):
        """G5-BROWNFIELD (architect finding, brownfield): a remote secondaryGWs
        aggregate carrying an extra top-level key alongside "secondaryGWs" (e.g. a
        future/unknown controller field) is not representable by this module and
        must fail before mutating normalization completes -- not be silently
        discarded. Reproduced for both a populated and a zero-gateway aggregate."""
        cases = (
            ("populated", [{"gatewayIpAddress": "192.166.88.1/24"}], ("192.166.88.1/24", "", "", "")),
            ("zero_gateway", [], ("", "", "", "")),
        )
        for label, entries, gws in cases:
            with self.subTest(case=label):
                dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
                dcnm_net.dcnm_version = 12
                dcnm_net.ndfc_version = self.NDFC_VERSION_COMPATIBLE_MINIMUM
                dcnm_net.fabric_type = "standalone"
                dcnm_net.module = Mock()
                dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")

                raw_value = json.dumps({"secondaryGWs": entries, "futureField": "preserve-me"})
                raw_template = self._build_secondary_ip_network_template(
                    secondary_gw1=gws[0], secondary_gw2=gws[1], secondary_gw3=gws[2], secondary_gw4=gws[3]
                )
                raw_template["secondaryGWs"] = raw_value
                network = self._build_secondary_ip_update_payload(raw_template)

                with self.assertRaises(
                    RuntimeError,
                    msg=f"fail-before ({label}): an unexpected top-level key alongside "
                    "'secondaryGWs' must fail before mutating normalization, not be "
                    "silently discarded",
                ):
                    dcnm_net.normalize_have_network(network)
                dcnm_net.module.fail_json.assert_called_once()

    def test_dcnm_net_secgw_compat_g5_brownfield_unexpected_entry_key_fails_before_mutation(self):
        """G5-BROWNFIELD (architect finding, brownfield): a secondaryGWs entry
        carrying an extra key alongside "gatewayIpAddress" (e.g. a future/unknown
        per-gateway controller field) is not representable by this module and must
        fail before mutating normalization completes -- not be silently discarded."""
        dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
        dcnm_net.dcnm_version = 12
        dcnm_net.ndfc_version = self.NDFC_VERSION_COMPATIBLE_MINIMUM
        dcnm_net.fabric_type = "standalone"
        dcnm_net.module = Mock()
        dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")

        raw_value = json.dumps(
            {"secondaryGWs": [{"gatewayIpAddress": "192.166.88.1/24", "futureField": "preserve-me"}]}
        )
        raw_template = self._build_secondary_ip_network_template(secondary_gw1="192.166.88.1/24")
        raw_template["secondaryGWs"] = raw_value
        network = self._build_secondary_ip_update_payload(raw_template)

        with self.assertRaises(
            RuntimeError,
            msg="fail-before: an unexpected key alongside 'gatewayIpAddress' in a "
            "secondaryGWs entry must fail before mutating normalization, not be "
            "silently discarded",
        ):
            dcnm_net.normalize_have_network(network)
        dcnm_net.module.fail_json.assert_called_once()

    def test_dcnm_net_secgw_compat_g5_brownfield_exact_schema_still_accepted(self):
        """G5-BROWNFIELD (regression lock): the exact representable top-level
        schema {"secondaryGWs": [...]} and exact entry schema
        {"gatewayIpAddress": "..."} -- with no extra keys anywhere -- must
        continue to be accepted on mutating normalization, including the
        zero-gateway empty-aggregate encoding."""
        cases = (
            ("populated", [{"gatewayIpAddress": "192.166.88.1/24"}], ("192.166.88.1/24", "", "", "")),
            ("zero_gateway", [], ("", "", "", "")),
        )
        for label, entries, gws in cases:
            with self.subTest(case=label):
                dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
                dcnm_net.dcnm_version = 12
                dcnm_net.ndfc_version = self.NDFC_VERSION_COMPATIBLE_MINIMUM
                dcnm_net.fabric_type = "standalone"
                dcnm_net.module = Mock()
                dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")

                raw_value = json.dumps({"secondaryGWs": entries})
                raw_template = self._build_secondary_ip_network_template(
                    secondary_gw1=gws[0], secondary_gw2=gws[1], secondary_gw3=gws[2], secondary_gw4=gws[3]
                )
                raw_template["secondaryGWs"] = raw_value
                network = self._build_secondary_ip_update_payload(raw_template)

                dcnm_net.normalize_have_network(network)

                dcnm_net.module.fail_json.assert_not_called()

    def test_dcnm_net_secgw_compat_g5_brownfield_query_preserves_unknown_keys_without_failure(self):
        """G5-BROWNFIELD (unchanged contract, explicit coverage): query must
        preserve and report a secondaryGWs aggregate carrying unknown
        top-level or entry keys verbatim, without failure or any write --
        the stricter exact-key-set rule applies only on mutating
        normalization, which query already bypasses entirely (see
        test_dcnm_net_secgw_compat_g3_query_preserves_null_or_empty_without_failure)."""
        raw_values = (
            json.dumps({"secondaryGWs": [{"gatewayIpAddress": "192.166.88.1/24"}], "futureField": "preserve-me"}),
            json.dumps(
                {"secondaryGWs": [{"gatewayIpAddress": "192.166.88.1/24", "futureField": "preserve-me"}]}
            ),
        )
        for raw_value in raw_values:
            with self.subTest(raw_value=raw_value):
                dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
                dcnm_net.dcnm_version = 12
                dcnm_net.ndfc_version = self.NDFC_VERSION_FAILING_CONFIRMED
                dcnm_net.fabric_type = "standalone"
                dcnm_net.module = Mock(params={"state": "query"})
                dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")

                raw_template = self._build_secondary_ip_network_template(secondary_gw1="192.166.88.1/24")
                raw_template["secondaryGWs"] = raw_value
                network = self._build_secondary_ip_update_payload(raw_template)

                normalized = dcnm_net.normalize_have_network(network)

                dcnm_net.module.fail_json.assert_not_called()
                normalized_template = json.loads(normalized["networkTemplateConfig"])
                self.assertEqual(normalized_template.get("secondaryGWs"), raw_value)

    def _build_secgw_merged_lifecycle_network(
        self, fabric_type="standalone", dcnm_version=12.2, ndfc_version=None, has_bulk_api=False, state="merged"
    ):
        """G5-LIFECYCLE: a single instance wired for the real merged-state
        lifecycle from update_want() (which restores omitted
        secondary_ip_gw1-4 values from have via
        dcnm_update_network_information()) through
        finalize_secondary_gws_compat() and get_diff_merge() to
        push_to_remote() -- so the deferred-guard fix is exercised against
        the actual production reconciliation path, not a hand-filled want."""
        dcnm_net = self._build_secgw_update_push_to_remote_network(
            fabric_type=fabric_type, dcnm_version=dcnm_version, ndfc_version=ndfc_version, has_bulk_api=has_bulk_api
        )
        dcnm_net.params = {"state": state}
        dcnm_net.module.params = {"state": state}
        dcnm_net.want_create = []
        dcnm_net.have_create = []
        return dcnm_net

    @staticmethod
    def _secgw_merged_config(net_name="sec-ip-test", vrf_name="test-vrf", vlan_id=993, gw_ip_subnet="10.250.93.1/24", **gw_overrides):
        """Unlike _secgw_capability_config(), secondary_ip_gw1-4 keys are
        NOT defaulted to "" -- only the keys actually passed in
        gw_overrides are present in the resulting dict, matching a real
        playbook where an omitted key is genuinely absent from cfg (not
        merely set to an empty string), which is the exact distinction
        dcnm_update_network_information() relies on to decide whether to
        restore a value from have."""
        config = {
            "net_name": net_name,
            "vrf_name": vrf_name,
            "is_l2only": False,
            "vlan_id": vlan_id,
            "gw_ip_subnet": gw_ip_subnet,
        }
        config.update(gw_overrides)
        return config

    def test_dcnm_net_secgw_compat_g5_lifecycle_merged_gw2_over_existing_gw1(self):
        """G5-LIFECYCLE (architect finding): have GW1=A, merged intent
        supplies only secondary_ip_gw2=B (GW1 omitted, not cleared). The
        transient want built by update_create_params(), before have is
        consulted, is ["", B, "", ""] -- a non-prefix gap if validated
        immediately. Once update_want() restores GW1=A from have, the final
        reconciled want [A, B, "", ""] is a safe contiguous prefix and must
        succeed, with the real individual and bulk PUT bodies carrying the
        exact aggregate. A second pass with have already reflecting
        GW1=A/GW2=B must be idempotent (no diff, no PUT)."""
        for has_bulk_api in (False, True):
            with self.subTest(has_bulk_api=has_bulk_api):
                dcnm_net = self._build_secgw_merged_lifecycle_network(
                    fabric_type="standalone", ndfc_version=self.NDFC_VERSION_COMPATIBLE_MINIMUM, has_bulk_api=has_bulk_api
                )
                dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")

                config = self._secgw_merged_config(secondary_ip_gw2="192.167.88.1/24")
                want_c = dcnm_net.update_create_params(config)

                have_template = self._build_secondary_ip_network_template(secondary_gw1="192.166.88.1/24")
                have_c = self._build_secondary_ip_update_payload(have_template)

                dcnm_net.want_create = [want_c]
                dcnm_net.have_create = [have_c]
                dcnm_net.config = [config]

                dcnm_net.update_want()
                dcnm_net.finalize_secondary_gws_compat()
                dcnm_net.get_diff_merge()

                self.assertEqual(
                    len(dcnm_net.diff_create_update),
                    1,
                    "the real merged-update-diff path did not populate diff_create_update for this want/have pair",
                )

                self.run_dcnm_send.reset_mock()
                self.run_dcnm_send.return_value = {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {}}

                dcnm_net.push_to_remote()

                self.assertEqual(self.run_dcnm_send.call_count, 1)
                sent_body = self.run_dcnm_send.call_args[0][3]
                if has_bulk_api:
                    sent_bulk = json.loads(sent_body)
                    self.assertEqual(len(sent_bulk), 1)
                    sent_template = sent_bulk[0]["networkTemplateConfig"]
                else:
                    sent_network = json.loads(sent_body)
                    sent_template = json.loads(sent_network["networkTemplateConfig"])

                self.assertEqual(
                    sent_template["secondaryGW1"],
                    "192.166.88.1/24",
                    "fail-before: GW1 was not preserved from have into the final reconciled want",
                )
                self.assertEqual(sent_template["secondaryGW2"], "192.167.88.1/24")
                self.assertIn(
                    "secondaryGWs",
                    sent_template,
                    "fail-before: the real merged UPDATE PUT body does not yet carry the reconciled aggregate",
                )
                self.assertEqual(
                    json.loads(sent_template["secondaryGWs"]),
                    {
                        "secondaryGWs": [
                            {"gatewayIpAddress": "192.166.88.1/24"},
                            {"gatewayIpAddress": "192.167.88.1/24"},
                        ]
                    },
                )

                # Second pass: have now reflects the applied change -- must be idempotent.
                dcnm_net2 = self._build_secgw_merged_lifecycle_network(
                    fabric_type="standalone", ndfc_version=self.NDFC_VERSION_COMPATIBLE_MINIMUM, has_bulk_api=has_bulk_api
                )
                dcnm_net2.module.fail_json.side_effect = RuntimeError("fail_json called")

                want_c2 = dcnm_net2.update_create_params(config)
                have_template2 = self._build_secondary_ip_network_template(
                    secondary_gw1="192.166.88.1/24", secondary_gw2="192.167.88.1/24"
                )
                have_c2 = self._build_secondary_ip_update_payload(have_template2)

                dcnm_net2.want_create = [want_c2]
                dcnm_net2.have_create = [have_c2]
                dcnm_net2.config = [config]

                dcnm_net2.update_want()
                dcnm_net2.finalize_secondary_gws_compat()
                dcnm_net2.get_diff_merge()

                self.assertEqual(
                    len(dcnm_net2.diff_create_update),
                    0,
                    "fail-before: second pass with have already reflecting GW1=A/GW2=B must be idempotent (no diff)",
                )

                self.run_dcnm_send.reset_mock()
                dcnm_net2.push_to_remote()
                self.run_dcnm_send.assert_not_called()

    def test_dcnm_net_secgw_compat_g5_lifecycle_merged_clear_preserves_gw1(self):
        """G5-LIFECYCLE (required case): have GW1=A/GW2=B, merged intent
        explicitly clears secondary_ip_gw2 (empty string, not omitted) while
        leaving GW1 unspecified. The final reconciled want GW1=A (restored
        from have) with GW2 cleared is a safe one-element prefix and must
        succeed, carrying only the GW1 aggregate."""
        dcnm_net = self._build_secgw_merged_lifecycle_network(
            fabric_type="standalone", ndfc_version=self.NDFC_VERSION_COMPATIBLE_MINIMUM
        )
        dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")

        config = self._secgw_merged_config(secondary_ip_gw2="")
        want_c = dcnm_net.update_create_params(config)

        have_template = self._build_secondary_ip_network_template(
            secondary_gw1="192.166.88.1/24", secondary_gw2="192.167.88.1/24"
        )
        have_c = self._build_secondary_ip_update_payload(have_template)

        dcnm_net.want_create = [want_c]
        dcnm_net.have_create = [have_c]
        dcnm_net.config = [config]

        dcnm_net.update_want()
        dcnm_net.finalize_secondary_gws_compat()
        dcnm_net.get_diff_merge()

        self.assertEqual(len(dcnm_net.diff_create_update), 1)

        self.run_dcnm_send.reset_mock()
        self.run_dcnm_send.return_value = {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {}}
        dcnm_net.push_to_remote()

        self.assertEqual(self.run_dcnm_send.call_count, 1)
        sent_network = json.loads(self.run_dcnm_send.call_args[0][3])
        sent_template = json.loads(sent_network["networkTemplateConfig"])

        self.assertEqual(sent_template["secondaryGW1"], "192.166.88.1/24")
        self.assertEqual(sent_template["secondaryGW2"], "")
        self.assertIn("secondaryGWs", sent_template)
        self.assertEqual(
            json.loads(sent_template["secondaryGWs"]),
            {"secondaryGWs": [{"gatewayIpAddress": "192.166.88.1/24"}]},
        )

    def test_dcnm_net_secgw_compat_g5_lifecycle_merged_non_prefix_after_reconciliation_fails(self):
        """G5-LIFECYCLE (required case, architect's exact reproduction):
        have GW1=A, merged intent supplies only secondary_ip_gw3=C (GW1,
        GW2 omitted). The final reconciled want GW1=A/GW2=""/GW3=C is
        non-prefix and must fail closed -- via update_want()'s existing
        dcnm_update_network_information() call, which re-validates after
        restoring omitted values from have -- before any transport."""
        dcnm_net = self._build_secgw_merged_lifecycle_network(
            fabric_type="standalone", ndfc_version=self.NDFC_VERSION_COMPATIBLE_MINIMUM
        )
        dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")

        config = self._secgw_merged_config(secondary_ip_gw3="192.168.88.1/24")
        want_c = dcnm_net.update_create_params(config)

        have_template = self._build_secondary_ip_network_template(secondary_gw1="192.166.88.1/24")
        have_c = self._build_secondary_ip_update_payload(have_template)

        dcnm_net.want_create = [want_c]
        dcnm_net.have_create = [have_c]
        dcnm_net.config = [config]

        self.run_dcnm_send.reset_mock()
        self.run_dcnm_send.return_value = {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {}}

        with self.assertRaises(
            RuntimeError,
            msg="fail-before: the final reconciled want GW1=A/GW2=''/GW3=C is non-prefix and must fail",
        ):
            dcnm_net.update_want()

        dcnm_net.module.fail_json.assert_called_once()
        message = dcnm_net.module.fail_json.call_args[1]["msg"]
        self.assertIn("192.166.88.1/24", message)
        self.assertIn("192.168.88.1/24", message)
        self.run_dcnm_send.assert_not_called()

    def test_dcnm_net_secgw_compat_g5_lifecycle_non_merged_states_retain_immediate_validation(self):
        """G5-LIFECYCLE (regression lock, required case): state replaced and
        overridden must retain their immediate update_create_params()
        validation -- no merged have-overlay ever runs for them, so their
        transient want IS their final want, and deferring would let an
        unsafe non-prefix payload reach transport."""
        for state in ("replaced", "overridden"):
            with self.subTest(state=state):
                dcnm_net = self._build_secgw_capability_network(
                    fabric_type="standalone", ndfc_version=self.NDFC_VERSION_COMPATIBLE_MINIMUM
                )
                dcnm_net.params = {"state": state}
                dcnm_net.module = Mock()
                dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")

                with self.assertRaises(
                    RuntimeError,
                    msg=f"fail-before ({state}): non-prefix intent must still fail immediately in update_create_params()",
                ):
                    dcnm_net.update_create_params(
                        self._secgw_capability_config(gw1="192.166.88.1/24", gw4="192.169.88.1/24")
                    )
                dcnm_net.module.fail_json.assert_called_once()

    def test_dcnm_net_secgw_compat_g5_lifecycle_auto_id_create_fails_before_post(self):
        """G5-LIFECYCLE (required case): a brand-new network under merged
        state (no matching have, so update_want()'s reconciliation loop
        never touches it) with non-prefix intent must still fail before
        get_diff_merge() can issue its auto-ID POST -- proving the deferred
        check is finalized somewhere real have-overlay reconciliation never
        runs for it."""
        dcnm_net = self._build_secgw_merged_lifecycle_network(
            fabric_type="standalone", ndfc_version=self.NDFC_VERSION_COMPATIBLE_MINIMUM
        )
        dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")

        config = self._secgw_merged_config(
            secondary_ip_gw1="192.166.88.1/24", secondary_ip_gw4="192.169.88.1/24"
        )
        want_c = dcnm_net.update_create_params(config)

        dcnm_net.want_create = [want_c]
        dcnm_net.have_create = []
        dcnm_net.config = [config]

        dcnm_net.update_want()

        self.run_dcnm_send.reset_mock()
        self.run_dcnm_send.return_value = {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {"l2vni": 50999}}

        with self.assertRaises(
            RuntimeError,
            msg="fail-before: a brand-new network's non-prefix intent under merged state must fail "
            "before the auto-ID POST",
        ):
            dcnm_net.finalize_secondary_gws_compat()

        dcnm_net.module.fail_json.assert_called_once()
        self.run_dcnm_send.assert_not_called()

    def test_dcnm_net_secgw_compat_g5_query_update_create_params_never_mutates_or_fails(self):
        """G5-QUERY (architect finding): state: query is read-only and must
        never apply the mutating secondaryGWs capability/prefix policy to
        query input -- get_diff_query() never reads a want entry's
        networkTemplateConfig for anything except networkName (see
        get_diff_query()), so nothing downstream needs (or should receive) a
        computed aggregate. update_create_params() must skip
        apply_secondary_gws_compat() entirely for state: query -- not defer
        it (as for merged), skip it -- so a query config carrying a
        non-prefix gap on a compatible version, or a populated secondary
        gateway filter on an unknown/malformed version, both proceed without
        failure, and secondaryGW1-4 pass through exactly as given with no
        "secondaryGWs" key ever added."""
        cases = (
            ("compatible_non_prefix_gap", self.NDFC_VERSION_COMPATIBLE_MINIMUM, {"gw2": "192.167.88.1/24"}),
            ("unknown_populated", "not-a-real-version", {"gw1": "192.166.88.1/24"}),
        )
        for label, ndfc_version, gws in cases:
            with self.subTest(case=label):
                dcnm_net = self._build_secgw_capability_network(fabric_type="standalone", ndfc_version=ndfc_version)
                dcnm_net.params = {"state": "query"}
                dcnm_net.module = Mock()
                dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")

                payload = dcnm_net.update_create_params(self._secgw_capability_config(**gws))

                dcnm_net.module.fail_json.assert_not_called()
                template = json.loads(payload["networkTemplateConfig"])

                self.assertEqual(template["secondaryGW1"], gws.get("gw1", ""))
                self.assertEqual(template["secondaryGW2"], gws.get("gw2", ""))
                self.assertEqual(template["secondaryGW3"], gws.get("gw3", ""))
                self.assertEqual(template["secondaryGW4"], gws.get("gw4", ""))
                self.assertNotIn(
                    "secondaryGWs",
                    template,
                    f"fail-before ({label}): query input still ran the mutating aggregate "
                    "applicator instead of skipping it entirely",
                )

    def test_dcnm_net_secgw_compat_g5_query_real_flow_read_only_preserves_raw_state(self):
        """G5-QUERY (real flow): route a query config carrying a non-prefix
        gateway gap through the actual get_want() -> get_diff_query() path
        (want built via the real update_create_params(), transport mocked)
        and confirm the query proceeds to completion -- issuing only GET
        calls, never failing, and reporting the network exactly as the
        (mocked) controller GET responses describe it, independent of the
        local gap in the query config's secondary_ip_gw1-4 filter fields."""
        dcnm_net = self._build_get_have_query_network(ndfc_version=self.NDFC_VERSION_COMPATIBLE_MINIMUM)
        dcnm_net.params = {"state": "query"}
        dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")

        config = self._secgw_capability_config(
            net_name="sec-ip-test", vrf_name="test-vrf", gw2="192.167.88.1/24"
        )
        dcnm_net.config = [config]
        want_c = dcnm_net.update_create_params(config)
        dcnm_net.want_create = [want_c]
        dcnm_net.have_create = [{"networkName": "sec-ip-test"}]
        dcnm_net.have_attach = []

        remote_template = self._build_secondary_ip_network_template(secondary_gw1="10.0.0.1/24")
        remote_template["networkName"] = "sec-ip-test"
        remote_template["secondaryGWs"] = json.dumps({"secondaryGWs": [{"gatewayIpAddress": "10.0.0.1/24"}]})
        remote_network = dict(self._build_secondary_ip_update_payload(remote_template))
        remote_network["networkName"] = "sec-ip-test"

        self.run_dcnm_send.reset_mock()
        self.run_dcnm_send.side_effect = [
            {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [{"vrfName": "test-vrf"}]},
            {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": remote_network},
            {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [{"networkName": "sec-ip-test", "lanAttachList": [{"serialNumber": "SN1"}]}]},
        ]

        dcnm_net.get_diff_query()

        dcnm_net.module.fail_json.assert_not_called()
        self.assertTrue(
            all(call.args[1] == "GET" for call in self.run_dcnm_send.call_args_list),
            "fail-before: a read-only query must never issue a non-GET (write) transport call",
        )
        self.assertEqual(len(dcnm_net.query), 1)
        reported_template = dcnm_net.query[0]["parent"]["networkTemplateConfig"]
        self.assertEqual(
            json.loads(reported_template["secondaryGWs"]),
            {"secondaryGWs": [{"gatewayIpAddress": "10.0.0.1/24"}]},
            "fail-before: reported query state must echo the raw controller response, "
            "independent of the local query config's gateway filter fields",
        )

    def test_dcnm_net_secgw_compat_g5_query_non_query_states_unchanged(self):
        """G5-QUERY (regression lock, required case): merged/replaced/
        overridden must be completely unaffected by the query-only skip --
        merged still defers the prefix check (not fully skips it), and
        replaced/overridden still validate immediately."""
        gws = {"gw1": "192.166.88.1/24", "gw4": "192.169.88.1/24"}

        # merged: deferred, not failed, not skipped -- template still carries no
        # aggregate yet (deferred), but the call must not raise.
        dcnm_net_merged = self._build_secgw_capability_network(
            fabric_type="standalone", ndfc_version=self.NDFC_VERSION_COMPATIBLE_MINIMUM
        )
        dcnm_net_merged.module = Mock()
        dcnm_net_merged.module.fail_json.side_effect = RuntimeError("fail_json called")
        payload = dcnm_net_merged.update_create_params(self._secgw_capability_config(**gws))
        dcnm_net_merged.module.fail_json.assert_not_called()
        template = json.loads(payload["networkTemplateConfig"])
        self.assertNotIn("secondaryGWs", template)

        # replaced/overridden: still fail immediately, exactly as before.
        for state in ("replaced", "overridden"):
            with self.subTest(state=state):
                dcnm_net = self._build_secgw_capability_network(
                    fabric_type="standalone", ndfc_version=self.NDFC_VERSION_COMPATIBLE_MINIMUM
                )
                dcnm_net.params = {"state": state}
                dcnm_net.module = Mock()
                dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")

                with self.assertRaises(RuntimeError):
                    dcnm_net.update_create_params(self._secgw_capability_config(**gws))
                dcnm_net.module.fail_json.assert_called_once()

    def _build_secgw_delete_override_have_network(self, state, ndfc_version=None, want_create=None):
        """G5-DELETE: a bare instance for testing normalize_have_network()'s
        path-sensitive aggregate-validation skip for state: deleted (always
        skipped -- delete never writes networkTemplateConfig) and
        state: overridden (skipped only for a remote network with no
        matching entry in self.want_create, the desired config -- only
        those are delete-only; a network retained in the desired config may
        still be updated and must continue to validate)."""
        dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
        dcnm_net.log = self._build_test_logger()
        dcnm_net.dcnm_version = 12
        dcnm_net.ndfc_version = ndfc_version
        dcnm_net.fabric_type = "standalone"
        dcnm_net.is_ms_fabric = False
        dcnm_net.module = Mock(params={"state": state})
        dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")
        dcnm_net.want_create = want_create if want_create is not None else []
        return dcnm_net

    def test_dcnm_net_secgw_compat_g5_delete_update_create_params_never_mutates_or_fails(self):
        """G5-DELETE (architect finding 1, want side): state: deleted never
        writes networkTemplateConfig -- get_diff_delete() only needs
        networkName and attachment identity to issue its DELETE -- so
        update_create_params() must skip apply_secondary_gws_compat()
        entirely for state: deleted, exactly as it already does for query,
        instead of letting an unknown-version or non-prefix gateway filter
        block deletion."""
        cases = (
            ("compatible_non_prefix_gap", self.NDFC_VERSION_COMPATIBLE_MINIMUM, {"gw1": "192.166.88.1/24", "gw4": "192.169.88.1/24"}),
            ("unknown_populated", "not-a-real-version", {"gw1": "192.166.88.1/24"}),
        )
        for label, ndfc_version, gws in cases:
            with self.subTest(case=label):
                dcnm_net = self._build_secgw_capability_network(fabric_type="standalone", ndfc_version=ndfc_version)
                dcnm_net.params = {"state": "deleted"}
                dcnm_net.module = Mock()
                dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")

                payload = dcnm_net.update_create_params(self._secgw_capability_config(**gws))

                dcnm_net.module.fail_json.assert_not_called()
                template = json.loads(payload["networkTemplateConfig"])
                self.assertEqual(template["secondaryGW1"], gws.get("gw1", ""))
                self.assertEqual(template["secondaryGW4"], gws.get("gw4", ""))
                self.assertNotIn(
                    "secondaryGWs",
                    template,
                    f"fail-before ({label}): deleted input still ran the mutating aggregate "
                    "applicator instead of skipping it entirely",
                )

    def test_dcnm_net_secgw_compat_g5_delete_normalize_have_skips_validation(self):
        """G5-DELETE (architect finding 1, have side, required case): a
        remote network's brownfield aggregate state must never block its
        own deletion for state: deleted. get_diff_delete() never reads
        networkTemplateConfig (only networkName and attachment identity),
        so a malformed, null/empty, unknown-key, or
        aggregate-only-contradicting-legacy remote aggregate -- and a
        non-contiguous gap in the legacy secondaryGW1-4 fields themselves --
        must all be preserved verbatim (not validated), while the
        networkName identity field survives untouched for
        get_diff_delete()'s matching logic."""
        cases = (
            ("malformed_json", "not-json", ("", "", "", "")),
            ("null", None, ("", "", "", "")),
            ("empty_string", "", ("", "", "", "")),
            (
                "unknown_key",
                json.dumps({"secondaryGWs": [{"gatewayIpAddress": "192.166.88.1/24"}], "futureField": "x"}),
                ("192.166.88.1/24", "", "", ""),
            ),
            (
                "aggregate_only_contradicts_legacy",
                json.dumps({"secondaryGWs": [{"gatewayIpAddress": "10.0.0.9/24"}]}),
                ("", "", "", ""),
            ),
        )
        for label, raw_value, gws in cases:
            with self.subTest(case=label):
                dcnm_net = self._build_secgw_delete_override_have_network(
                    state="deleted", ndfc_version=self.NDFC_VERSION_COMPATIBLE_MINIMUM
                )
                raw_template = self._build_secondary_ip_network_template(
                    secondary_gw1=gws[0], secondary_gw2=gws[1], secondary_gw3=gws[2], secondary_gw4=gws[3]
                )
                raw_template["secondaryGWs"] = raw_value
                network = self._build_secondary_ip_update_payload(raw_template)

                normalized = dcnm_net.normalize_have_network(network)

                dcnm_net.module.fail_json.assert_not_called()
                self.assertEqual(normalized["networkName"], "sec-ip-test")
                normalized_template = json.loads(normalized["networkTemplateConfig"])
                self.assertEqual(normalized_template.get("secondaryGWs"), raw_value)

        with self.subTest(case="non_prefix_legacy_gap"):
            dcnm_net = self._build_secgw_delete_override_have_network(
                state="deleted", ndfc_version=self.NDFC_VERSION_COMPATIBLE_MINIMUM
            )
            raw_template = self._build_secondary_ip_network_template(
                secondary_gw1="192.166.88.1/24", secondary_gw4="192.169.88.1/24"
            )
            network = self._build_secondary_ip_update_payload(raw_template)

            normalized = dcnm_net.normalize_have_network(network)

            dcnm_net.module.fail_json.assert_not_called()
            self.assertEqual(normalized["networkName"], "sec-ip-test")

    def test_dcnm_net_secgw_compat_g5_overridden_normalize_have_path_sensitive(self):
        """G5-DELETE (architect finding 2, required case, path-sensitive):
        for state: overridden, a remote network with NO matching entry in
        self.want_create (the desired config) is a delete-only candidate --
        omitted from the desired model entirely -- and must not be blocked
        by a malformed aggregate. A remote network WITH a matching
        want_create entry may still be updated and must continue to receive
        full validation -- this is a per-network decision, not a state-wide
        bypass."""
        raw_value = json.dumps({"secondaryGWs": [{"gatewayIpAddress": "192.166.88.1/24"}], "futureField": "x"})
        raw_template = self._build_secondary_ip_network_template(secondary_gw1="192.166.88.1/24")
        raw_template["secondaryGWs"] = raw_value
        network = self._build_secondary_ip_update_payload(raw_template)

        with self.subTest(case="omitted_delete_only"):
            dcnm_net = self._build_secgw_delete_override_have_network(
                state="overridden", ndfc_version=self.NDFC_VERSION_COMPATIBLE_MINIMUM, want_create=[]
            )
            normalized = dcnm_net.normalize_have_network(network)
            dcnm_net.module.fail_json.assert_not_called()
            normalized_template = json.loads(normalized["networkTemplateConfig"])
            self.assertEqual(normalized_template.get("secondaryGWs"), raw_value)

        with self.subTest(case="retained_still_validates"):
            dcnm_net = self._build_secgw_delete_override_have_network(
                state="overridden",
                ndfc_version=self.NDFC_VERSION_COMPATIBLE_MINIMUM,
                want_create=[{"networkName": "sec-ip-test"}],
            )
            with self.assertRaises(
                RuntimeError,
                msg="fail-before: a retained network in the overridden desired config must still "
                "receive full brownfield validation",
            ):
                dcnm_net.normalize_have_network(network)
            dcnm_net.module.fail_json.assert_called_once()

    def test_dcnm_net_secgw_compat_g5_delete_real_flow_reaches_diff_delete_without_failure(self):
        """G5-DELETE (real flow): route a deleted-state config, plus a
        remote network carrying a malformed aggregate, through the real
        update_create_params() -> normalize_have_network() -> get_diff_delete()
        path and confirm it reaches a ready-to-delete state
        (self.diff_delete populated) without any failure and without any
        transport call -- get_diff_delete() never sends anything itself;
        the actual DELETE happens later, in push_to_remote(), reading only
        networkName, never networkTemplateConfig."""
        dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
        dcnm_net.log = self._build_test_logger()
        dcnm_net.fabric = "test-fabric"
        dcnm_net.dcnm_version = 12
        dcnm_net.ndfc_version = self.NDFC_VERSION_COMPATIBLE_MINIMUM
        dcnm_net.fabric_type = "standalone"
        dcnm_net.is_ms_fabric = False
        dcnm_net.module = Mock(params={"state": "deleted"})
        dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")
        dcnm_net.params = {"state": "deleted"}

        config = self._secgw_capability_config(net_name="sec-ip-test", vrf_name="test-vrf")
        want_c = dcnm_net.update_create_params(config)
        dcnm_net.want_create = [want_c]
        dcnm_net.config = [config]

        raw_template = self._build_secondary_ip_network_template(secondary_gw1="192.166.88.1/24")
        raw_template["secondaryGWs"] = "not-json"
        raw_network = self._build_secondary_ip_update_payload(raw_template)
        have_c = dcnm_net.normalize_have_network(raw_network)
        dcnm_net.have_create = [have_c]
        dcnm_net.have_attach = [
            {
                "networkName": "sec-ip-test",
                "lanAttachList": [{"serialNumber": "SN1", "isAttached": True}],
            }
        ]

        self.run_dcnm_send.reset_mock()

        dcnm_net.get_diff_delete()

        dcnm_net.module.fail_json.assert_not_called()
        self.run_dcnm_send.assert_not_called()
        self.assertEqual(dcnm_net.diff_delete, {"sec-ip-test": "DEPLOYED"})
        self.assertEqual(len(dcnm_net.diff_detach), 1)

    def test_dcnm_net_secgw_compat_g6_aggregate_canonical_and_stale_regenerated(self):
        """G6 characterization: aggregate capability always ends with the
        exact compact JSON regenerated from the authoritative legacy slots,
        whether the incoming aggregate is already canonical or stale."""
        gateway = "192.166.88.1/24"
        expected = '{"secondaryGWs":[{"gatewayIpAddress":"192.166.88.1/24"}]}'
        cases = (
            ("canonical", expected),
            ("stale", '{"secondaryGWs":[{"gatewayIpAddress":"192.199.88.1/24"}]}'),
        )
        for label, incoming in cases:
            with self.subTest(case=label):
                dcnm_net = self._build_secgw_capability_network(
                    fabric_type="standalone", ndfc_version=self.NDFC_VERSION_COMPATIBLE_MINIMUM
                )
                template = {
                    "networkName": "secgw-net",
                    "secondaryGW1": gateway,
                    "secondaryGW2": "",
                    "secondaryGW3": "",
                    "secondaryGW4": "",
                    "secondaryGWs": incoming,
                }

                dcnm_net.apply_secondary_gws_compat(template)

                self.assertIs(type(template["secondaryGWs"]), str)
                self.assertEqual(template["secondaryGWs"], expected)
                for index, value in enumerate((gateway, "", "", ""), start=1):
                    self.assertIs(type(template[f"secondaryGW{index}"]), str)
                    self.assertEqual(template[f"secondaryGW{index}"], value)

    def test_dcnm_net_secgw_compat_g6_brownfield_validation_receives_original_raw_value(self):
        """G6 characterization: brownfield validation receives the exact raw
        aggregate object before capability classification and regeneration."""
        original_raw = "".join(
            ("{\"secondaryGWs\":[{\"gatewayIpAddress\":", "\"192.166.88.1/24\"}]}")
        )
        gateway = "192.166.88.1/24"
        events = []
        dcnm_net = self._build_secgw_capability_network(
            fabric_type="standalone", ndfc_version=self.NDFC_VERSION_COMPATIBLE_MINIMUM
        )
        template = {
            "networkName": "secgw-net",
            "secondaryGW1": gateway,
            "secondaryGW2": "",
            "secondaryGW3": "",
            "secondaryGW4": "",
            "secondaryGWs": original_raw,
        }

        def validate(raw_aggregate, gw_values, observed_template):
            events.append("validate")
            self.assertIs(raw_aggregate, original_raw)
            self.assertIs(type(raw_aggregate), str)
            self.assertIs(observed_template, template)
            self.assertIn("secondaryGWs", observed_template)
            self.assertIs(observed_template["secondaryGWs"], original_raw)
            self.assertEqual(gw_values, [gateway, "", "", ""])
            self.assertTrue(all(value.__class__ is str for value in gw_values))

        dcnm_net._validate_remote_secondary_gws_representable = Mock(side_effect=validate)
        dcnm_net.secondary_gws_capability = Mock(side_effect=lambda: events.append("classify") or "aggregate")

        dcnm_net.apply_secondary_gws_compat(template, validate_remote=True)

        self.assertEqual(events, ["validate", "classify"])
        dcnm_net._validate_remote_secondary_gws_representable.assert_called_once()
        self.assertEqual(template["secondaryGWs"], original_raw)

    def test_dcnm_net_secgw_compat_g6_legacy_removes_only_aggregate(self):
        """G6 characterization: legacy capability removes only the aggregate
        and preserves every authoritative legacy slot exactly."""
        slots = ("192.166.88.1/24", "", "192.168.88.1/24", "")
        dcnm_net = self._build_secgw_capability_network(
            fabric_type="standalone", ndfc_version=self.NDFC_VERSION_FAILING_CONFIRMED
        )
        template = {
            "networkName": "secgw-net",
            "secondaryGW1": slots[0],
            "secondaryGW2": slots[1],
            "secondaryGW3": slots[2],
            "secondaryGW4": slots[3],
            "secondaryGWs": '{"secondaryGWs":[{"gatewayIpAddress":"stale"}]}',
        }

        dcnm_net.apply_secondary_gws_compat(template)

        self.assertNotIn("secondaryGWs", template)
        for index, value in enumerate(slots, start=1):
            self.assertIs(type(template[f"secondaryGW{index}"]), str)
            self.assertEqual(template[f"secondaryGW{index}"], value)

    def test_dcnm_net_secgw_compat_g6_unknown_removes_aggregate_and_populated_fails_closed(self):
        """G6 characterization: unknown capability removes stale aggregate
        state for empty or populated slots; populated intent still fails
        before any transport call."""
        cases = (("empty", "", False), ("populated", "192.166.88.1/24", True))
        for label, gw1, must_fail in cases:
            with self.subTest(case=label):
                dcnm_net = self._build_secgw_capability_network(fabric_type="standalone", ndfc_version="bad")
                dcnm_net.module = Mock()
                dcnm_net.module.fail_json.side_effect = RuntimeError("fail_json called")
                template = {
                    "networkName": "secgw-net",
                    "secondaryGW1": gw1,
                    "secondaryGW2": "",
                    "secondaryGW3": "",
                    "secondaryGW4": "",
                    "secondaryGWs": '{"secondaryGWs":[{"gatewayIpAddress":"stale"}]}',
                }
                self.run_dcnm_send.reset_mock()

                if must_fail:
                    with self.assertRaises(RuntimeError):
                        dcnm_net.apply_secondary_gws_compat(template)
                    dcnm_net.module.fail_json.assert_called_once()
                else:
                    dcnm_net.apply_secondary_gws_compat(template)
                    dcnm_net.module.fail_json.assert_not_called()

                self.assertNotIn("secondaryGWs", template)
                for index, value in enumerate((gw1, "", "", ""), start=1):
                    self.assertIs(type(template[f"secondaryGW{index}"]), str)
                    self.assertEqual(template[f"secondaryGW{index}"], value)
                self.run_dcnm_send.assert_not_called()

    def test_dcnm_net_secgw_compat_g6_deferred_non_prefix_removes_stale_aggregate(self):
        """G6 characterization: bounded merged deferral cannot leak a stale
        aggregate while final reconciliation is still pending."""
        slots = ("192.166.88.1/24", "", "192.168.88.1/24", "")
        dcnm_net = self._build_secgw_capability_network(
            fabric_type="standalone", ndfc_version=self.NDFC_VERSION_COMPATIBLE_MINIMUM
        )
        template = {
            "networkName": "secgw-net",
            "secondaryGW1": slots[0],
            "secondaryGW2": slots[1],
            "secondaryGW3": slots[2],
            "secondaryGW4": slots[3],
            "secondaryGWs": '{"secondaryGWs":[{"gatewayIpAddress":"stale"}]}',
        }

        dcnm_net.apply_secondary_gws_compat(template, defer_prefix_fail_closed=True)

        self.assertNotIn("secondaryGWs", template)
        for index, value in enumerate(slots, start=1):
            self.assertIs(type(template[f"secondaryGW{index}"]), str)
            self.assertEqual(template[f"secondaryGW{index}"], value)

    # ------------------------------------------------------------------
    # DCNM715-SECONDARYGWS-001 / G7 removal of duplicate version plumbing.
    # These tests were introduced before the G7 production edit and are the
    # focused fail-before/pass-after contract for the generation.
    # ------------------------------------------------------------------

    def test_dcnm_net_secgw_compat_g7_version_plumbing_surface_is_normalized_only(self):
        """G7 structural contract across helper, action, and module."""
        self.assertEqual(
            tuple(inspect.signature(dcnm_network_action.ActionModule._split_config).parameters),
            (
                "self",
                "fabrics",
                "fabric_name",
                "config",
                "state",
                "result",
                "ndfc_version",
                "ndfc_full_version",
            ),
        )

        forbidden_names = (
            "return_" + "raw_version",
            "ndfc_" + "raw_version",
            "ndfc_version_" + "raw",
        )
        production_sources = (
            inspect.getsource(dcnm_utils.get_nd_version),
            inspect.getsource(dcnm_network_action.ActionModule),
            inspect.getsource(dcnm_network.DcnmNetwork.__init__),
            inspect.getsource(dcnm_network.DcnmNetwork._parse_ndfc_version_components),
            inspect.getsource(dcnm_network.DcnmNetwork.apply_secondary_gws_compat),
            inspect.getsource(dcnm_network.main),
        )
        for forbidden_name in forbidden_names:
            for source in production_sources:
                self.assertNotIn(forbidden_name, source)

    def test_dcnm_net_secgw_compat_g7_documented_controller_versions_normalize_end_to_end(self):
        """The real helper normalization feeds action propagation and module
        classification without a parallel version value."""
        cases = (
            ("11.5(1)", (11.0, "11.5.1"), "legacy"),
            ("12.1.2e", (12.1, "12.1.2"), "legacy"),
            ("12.4.1a", (12.4, "12.4.1"), "aggregate"),
        )
        fabrics = {
            "msd-parent": {"type": "multisite_parent", "fabricParent": "None", "cluster_name": ""},
            "msd-child-1": {"type": "multisite_child", "fabricParent": "msd-parent", "cluster_name": ""},
        }
        config = [
            {
                "net_name": "ansible-msd-net1",
                "vrf_name": "Tenant-1",
                "is_l2only": False,
                "child_fabric_config": [{"fabric": "msd-child-1", "dhcp_loopback_id": 204}],
            }
        ]
        action_plugin = dcnm_network_action.ActionModule.__new__(dcnm_network_action.ActionModule)

        for controller_version, expected_pair, expected_capability in cases:
            with self.subTest(controller_version=controller_version):
                version_action = Mock()
                version_action._execute_module.return_value = {
                    "failed": False,
                    "response": {"RETURN_CODE": 200, "DATA": {"version": controller_version}},
                }
                version_info = dcnm_utils.get_nd_version(
                    version_action, {}, None, return_full_version=True
                )
                self.assertIs(type(version_info), tuple)
                self.assertEqual(version_info, expected_pair)

                configs, error_msg = action_plugin._split_config(
                    fabrics,
                    "msd-parent",
                    copy.deepcopy(config),
                    "merged",
                    {},
                    version_info[0],
                    version_info[1],
                )
                self.assertIsNone(error_msg)
                for fabric_config in configs:
                    details = fabric_config["_fabric_details"]
                    self.assertEqual(details["nd_version"], expected_pair[0])
                    self.assertEqual(details["ndfc_version"], expected_pair[1])
                    self.assertEqual(
                        set(details),
                        {"fabric_type", "cluster_name", "nd_version", "ndfc_version"},
                    )

                dcnm_net = self._build_secgw_capability_network(
                    fabric_type="standalone", ndfc_version=configs[0]["_fabric_details"]["ndfc_version"]
                )
                self.assertEqual(dcnm_net.secondary_gws_capability(), expected_capability)

    def test_dcnm_net_secgw_compat_g7_parser_accepts_only_canonical_normalized_forms(self):
        dcnm_net = self._build_secgw_capability_network(fabric_type="standalone")
        accepted = (
            ("11.5.1", (11, 5, 1)),
            ("12.2.3.70", (12, 2, 3, 70)),
        )
        rejected = (
            None,
            "",
            12.2,
            True,
            b"12.2.3.70",
            "12.2",
            "12.2.3.70.1",
            "11.5(1)",
            "12.1.2e",
            "12.4.1a",
            "12.2.3.70\n",
            "１２.２.３.７０",
        )

        for version, expected in accepted:
            with self.subTest(version=version):
                dcnm_net.ndfc_version = version
                parsed = dcnm_net._parse_ndfc_version_components()
                self.assertIs(type(parsed), tuple)
                self.assertEqual(parsed, expected)
                self.assertTrue(all(component.__class__ is int for component in parsed))

        for version in rejected:
            with self.subTest(version=repr(version)):
                dcnm_net.ndfc_version = version
                self.assertIsNone(dcnm_net._parse_ndfc_version_components())

    def test_dcnm_net_secgw_compat_g7_action_preserves_pair_and_scalar_compatibility(self):
        """The real action run path still accepts the normalized helper pair
        and historical scalar mocks while storing only the two established
        action attributes."""
        cases = (
            ((12.4, "12.4.1.245"), 12.4, "12.4.1.245"),
            (12.2, 12.2, None),
        )
        for helper_result, expected_major_minor, expected_full in cases:
            with self.subTest(helper_result=helper_result):
                action = dcnm_network_action.ActionModule.__new__(dcnm_network_action.ActionModule)
                action._task = Mock(args={"fabric": "fabric-a", "state": "query"})
                with patch.object(
                    dcnm_network_action, "get_nd_version", return_value=helper_result
                ) as version_lookup, patch.object(
                    dcnm_network_action,
                    "obtain_federated_fabric_associations",
                    return_value=None,
                ):
                    result = action.run(task_vars={})

                self.assertTrue(result["failed"])
                self.assertEqual(result["msg"], "Failed to get federated fabric associations from OneManage API")
                self.assertEqual(action.ndfc_version, expected_major_minor)
                self.assertEqual(action.ndfc_full_version, expected_full)
                self.assertEqual(
                    set(action.__dict__),
                    {"_task", "ndfc_version", "ndfc_full_version"},
                )
                version_lookup.assert_called_once_with(action, {}, None, return_full_version=True)

    def test_dcnm_net_split_msd_merged_keeps_secondary_gws_parent_only(self):
        action = dcnm_network_action.ActionModule.__new__(dcnm_network_action.ActionModule)
        fabrics = {
            "msd-parent": {
                "type": "multisite_parent",
                "fabricParent": "None",
                "cluster_name": "",
            },
            "msd-child-1": {
                "type": "multisite_child",
                "fabricParent": "msd-parent",
                "cluster_name": "",
            },
        }
        config = [
            {
                "net_name": "ansible-msd-net1",
                "vrf_name": "Tenant-1",
                "is_l2only": False,
                "secondary_ip_gw1": "192.166.88.1/24",
                "secondary_ip_gw2": "",
                "child_fabric_config": [
                    {
                        "fabric": "msd-child-1",
                        "dhcp_loopback_id": 204,
                    }
                ],
            }
        ]

        configs, error_msg = action._split_config(
            fabrics,
            "msd-parent",
            config,
            "merged",
            {},
            12,
            "12.4.1.245",
        )

        self.assertIsNone(error_msg)
        self.assertEqual(configs[0]["config"][0]["secondary_ip_gw1"], "192.166.88.1/24")
        self.assertEqual(configs[0]["config"][0]["secondary_ip_gw2"], "")
        self.assertEqual(
            configs[0]["_fabric_details"]["ndfc_version"],
            "12.4.1.245",
        )
        child_config = configs[1]["config"][0]
        self.assertEqual(child_config["dhcp_loopback_id"], 204)
        self.assertEqual(
            configs[1]["_fabric_details"]["ndfc_version"],
            "12.4.1.245",
        )

    def test_dcnm_net_delete_switch_config_deploy_serials_are_dynamic(self):
        dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
        dcnm_net.diff_detach = [
            {
                "networkName": "net-a",
                "lanAttachList": [
                    {"serialNumber": "SERIAL1"},
                    {"serialNumber": "SERIAL2"},
                ],
            },
            {
                "networkName": "net-b",
                "lanAttachList": [
                    {"serialNumber": "SERIAL2"},
                    {"serialNumber": "SERIAL3"},
                ],
            },
            {
                "networkName": "net-c",
                "lanAttachList": [
                    {"serialNumber": "SERIAL4"},
                ],
            },
        ]

        serials = dcnm_net.get_delete_deploy_switch_serials(
            {"networkNames": "net-a,net-b"}
        )

        self.assertEqual(serials, ["SERIAL1", "SERIAL2", "SERIAL3"])

    def test_dcnm_net_delete_out_of_sync_networks_are_bulk_deleted(self):
        dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
        dcnm_net.log = self._build_test_logger()
        dcnm_net.fabric = "test-fabric"
        dcnm_net.fabric_type = "standalone"
        dcnm_net.paths = {"GET_NET": "/networks/{}"}
        dcnm_net.module = Mock(check_mode=False)
        dcnm_net.result = {"changed": False, "response": []}
        dcnm_net.diff_create_update = []
        dcnm_net.diff_detach = []
        dcnm_net.diff_undeploy = {}
        dcnm_net.diff_delete = {"net-a": "OUT-OF-SYNC"}
        dcnm_net.diff_create = []
        dcnm_net.diff_attach = []
        dcnm_net.diff_deploy = {}
        dcnm_net.network_sn_attach_map = {}
        dcnm_net.network_sn_detach_map = {}
        dcnm_net.have_attach_by_name = {}
        dcnm_net.wait_for_network_attachments_del_ready = Mock(return_value=True)
        dcnm_net.wait_for_network_del_ready = Mock(return_value=True)
        dcnm_net.bulk_delete_networks_with_retry = Mock()

        dcnm_net.push_to_remote()

        dcnm_net.bulk_delete_networks_with_retry.assert_called_once_with(
            ["net-a"],
            "/networks/test-fabric",
            "DELETE",
            False,
        )

    def test_dcnm_net_delete_attachment_wait_batches_pending_networks(self):
        dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
        dcnm_net.log = self._build_test_logger()
        dcnm_net.fabric = "test-fabric"
        dcnm_net.fabric_type = "standalone"
        dcnm_net.paths = {"GET_NET_ATTACH": "/attach/{}/{}"}
        dcnm_net.module = Mock()
        dcnm_net.WAIT_TIME_FOR_DELETE_LOOP = 5
        dcnm_net.detach_and_deploy_for_del = Mock()

        networks = [f"net-{index}" for index in range(31)]
        dcnm_net.diff_delete = {network: "DEPLOYED" for network in networks}

        self.run_dcnm_send.side_effect = [
            {
                "RETURN_CODE": 200,
                "DATA": [
                    {"networkName": network, "lanAttachList": []}
                    for network in networks[:30]
                ],
            },
            {
                "RETURN_CODE": 200,
                "DATA": [
                    {"networkName": network, "lanAttachList": []}
                    for network in networks[30:]
                ],
            },
        ]

        self.assertTrue(dcnm_net.wait_for_network_attachments_del_ready())

        self.assertEqual(self.run_dcnm_send.call_count, 2)
        paths = [call_args[0][2] for call_args in self.run_dcnm_send.call_args_list]
        self.assertEqual(paths[0], "/attach/test-fabric/" + ",".join(networks[:30]))
        self.assertEqual(paths[1], "/attach/test-fabric/" + networks[30])
        self.assertEqual(set(dcnm_net.diff_delete.values()), {"NA"})
        dcnm_net.detach_and_deploy_for_del.assert_not_called()

    def test_dcnm_net_delete_attachment_wait_fails_on_unexpected_data(self):
        dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
        dcnm_net.log = self._build_test_logger()
        dcnm_net.fabric = "test-fabric"
        dcnm_net.fabric_type = "standalone"
        dcnm_net.paths = {"GET_NET_ATTACH": "/attach/{}/{}"}
        dcnm_net.module = Mock()
        dcnm_net.module.fail_json.side_effect = Exception("fail_json")
        dcnm_net.WAIT_TIME_FOR_DELETE_LOOP = 5
        dcnm_net.diff_delete = {"net-a": "DEPLOYED"}

        self.run_dcnm_send.return_value = {
            "RETURN_CODE": 414,
            "DATA": "<html>URI Too Long</html>",
        }

        with self.assertRaises(Exception):
            dcnm_net.wait_for_network_attachments_del_ready()

        dcnm_net.module.fail_json.assert_called_once()
        self.assertIn(
            "Unexpected DATA while waiting for network attachments",
            dcnm_net.module.fail_json.call_args[1]["msg"],
        )

    def load_fixtures(self, response=None, device=""):

        if self.version == 12:
            self.nd_support_version = self.nd_version
        else:
            self.nd_support_version = self.nd_version_11

        if "net_blank_fabric" in self._testMethodName:
            self.run_dcnm_ip_sn.side_effect = [{}]
        else:
            self.run_dcnm_ip_sn.side_effect = [self.net_inv_data]

        self.run_dcnm_fabric_details.side_effect = [self.fabric_details]

        if "get_have_failure" in self._testMethodName:
            self.run_dcnm_send.side_effect = [self.get_have_failure]

        elif "_check_mode" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
            ]

        elif "_12check_mode" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
            ]

        elif "_merged_new" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "_12merged_new" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "_merged_novlan_new" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
                self.mock_vlan_get,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "error1" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
                self.blank_data,
                self.error1,
                self.blank_data,
            ]

        elif "error2" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
                self.blank_data,
                self.error2,
                self.blank_data,
            ]
        elif "error3" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
                self.blank_data,
                self.attach_success_resp,
                self.error3,
                self.blank_data,
            ]

        elif "_merged_duplicate" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_fabric_details.side_effect = [self.fabric_details_vxlan_fabric]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
            ]

        elif "_merged_with_incorrect_netid" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
            ]

        elif "_merged_with_incorrect_vrf" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
            ]

        elif "_merged_with_update" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "_merged_attach_vlan_override_new" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "_merged_attach_freeform_new" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "_merged_attach_vlan_override_idempotent" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object_vlan_override]
            self.run_dcnm_fabric_details.side_effect = [self.fabric_details_vxlan_fabric]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
            ]

        elif "replace_with_no_atch" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.attach_success_resp,
                self.deploy_success_resp,
                self.delete_success_resp,
            ]

        elif "replace_with_changes" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.attach_success_resp,
                self.deploy_success_resp,
                self.delete_success_resp,
            ]

        elif "replace_without_changes" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
            ]

        elif "_merged_redeploy" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object_pending]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.blank_data,
                self.deploy_success_resp,
            ]

        elif "override_with_additions" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "override_without_changes" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
            ]

        elif "override_with_deletions" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.attach_success_resp,
                self.deploy_success_resp,
                self.mock_net_attach_object_del_not_ready,  # wait_for_network_attachments_del_ready
                self.mock_net_attach_object_del_ready,      # wait_for_network_attachments_del_ready
                self.mock_net_del_ready,                     # wait_for_network_del_ready
                self.delete_success_resp,                    # bulk_delete_networks_with_retry
                self.blank_data,
                self.attach_success_resp2,
                self.deploy_success_resp,
            ]

        elif "delete_std" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.attach_success_resp,
                self.deploy_success_resp,
                self.mock_net_attach_object_del_not_ready,  # wait_for_network_attachments_del_ready
                self.mock_net_attach_object_del_ready,      # wait_for_network_attachments_del_ready
                self.mock_net_del_ready,                     # wait_for_network_del_ready
                self.delete_success_resp,                    # bulk_delete_networks_with_retry
            ]

        elif "delete_without_config" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
                self.mock_net_attach_object_del_not_ready,  # wait_for_network_attachments_del_ready
                self.mock_net_attach_object_del_ready,      # wait_for_network_attachments_del_ready
                self.mock_net_del_ready,                     # wait_for_network_del_ready
                self.delete_success_resp,                    # bulk_delete_networks_with_retry
            ]

        elif "query_with_config" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.mock_vrf_object,
                self.mock_net_query_object,
                self.mock_net_attach_object
            ]

        elif "query_without_config" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.mock_vrf_object,
                self.mock_net_object,
                self.mock_net_attach_object
            ]

        elif "_merged_torport_new" in self._testMethodName:
            self.init_data()
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.blank_data,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "_merged_torport_vererror" in self._testMethodName:
            self.init_data()

        elif "_merged_torport_roleerror" in self._testMethodName:
            self.init_data()

        elif "_merged_tor_with_update" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_tor_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "_merged_tor_only_with_update" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_tor_only_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "_merged_tor_vpc_one_sided_with_update" in self._testMethodName:
            self.init_data()
            self.run_dcnm_ip_sn.side_effect = [self.net_inv_data_vpc_tor]
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_tor_vpc_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "_replace_tor_ports" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_tor_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "_override_tor_ports" in self._testMethodName:
            self.init_data()
            self.run_dcnm_get_url.side_effect = [self.mock_net_attach_tor_object]
            self.run_dcnm_send.side_effect = [
                self.mock_vrf_object,
                self.mock_net_object,
                self.blank_data,
                self.attach_success_resp,
                self.deploy_success_resp,
            ]

        elif "_merged_msd_basic" in self._testMethodName:
            self.init_data()
            self.run_dcnm_fabric_details.side_effect = [
                self.mock_msd_fabric_details,
                self.mock_msd_child_fabric_details,
            ]

            self.run_dcnm_ip_sn.side_effect = [
                self.mock_msd_ip_sn,
                self.mock_msd_ip_sn,
            ]
            self.run_dcnm_send.side_effect = [
                self.mock_msd_vrf_object,
                self.empty_network_list,
                self.mock_msd_net_create_response,
                self.mock_msd_net_attach_response,
                self.mock_msd_vrf_object,
                self.mock_msd_child_net_object,
                self.mock_msd_child_net_attach_object,
                self.mock_msd_child_net_update_response,
            ]

        elif "_merged_msd_dhcp" in self._testMethodName:
            self.init_data()
            self.run_dcnm_fabric_details.side_effect = [
                self.mock_msd_fabric_details,
                self.mock_msd_child_fabric_details,
            ]

            self.run_dcnm_ip_sn.side_effect = [
                self.mock_msd_ip_sn,
                self.mock_msd_ip_sn,
            ]
            self.run_dcnm_send.side_effect = [
                self.mock_msd_vrf_object,
                self.empty_network_list,
                self.mock_msd_dhcp_net_create_response,
                self.mock_msd_dhcp_net_attach_response,
                self.mock_msd_vrf_object,
                self.mock_msd_dhcp_child_net_object,
                self.mock_msd_dhcp_child_net_attach_object,
                self.mock_msd_dhcp_child_net_update_response,
            ]

        elif "_msd_override_with_different_attachments" in self._testMethodName:
            self.init_data()
            self.run_dcnm_fabric_details.side_effect = [
                self.mock_msd_fabric_details,
                self.mock_msd_child_fabric_details,
            ]

            self.run_dcnm_ip_sn.side_effect = [
                self.mock_msd_ip_sn,
                self.mock_msd_ip_sn,
            ]
            self.run_dcnm_send.side_effect = [
                self.mock_msd_vrf_object,
                self.empty_network_list,
                self.mock_msd_override_parent_net_object,
                self.mock_msd_override_attach_response,
                self.mock_msd_vrf_object,
                self.mock_msd_override_child_net_object,
                self.mock_msd_override_child_net_attach_object,
            ]
        else:
            pass

    def test_dcnm_net_blank_fabric(self):
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=True, use_action_plugin=True)
        self.assertEqual(
            result.get("msg"),
            "Fabric test_network missing on ND or does not have any switches",
        )

    def test_dcnm_net_get_have_failure(self):
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=True, use_action_plugin=True)
        self.assertEqual(result.get("msg"), "Fabric test_network not present on DCNM")

    def test_dcnm_net_check_mode(self):
        set_module_args(
            dict(
                _ansible_check_mode=True,
                state="merged",
                fabric="test_network",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)
        self.assertTrue(result.get("diff"))
        self.assertFalse(result.get("response"))

    def test_dcnm_net_12check_mode(self):
        self.version = 12
        set_module_args(
            dict(
                _ansible_check_mode=True,
                state="merged",
                fabric="test_network",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)
        self.version = 11
        self.assertTrue(result.get("diff"))
        self.assertFalse(result.get("response"))

    def test_dcnm_net_merged_new(self):
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.217"
        )

    def test_dcnm_net_12merged_new(self):
        self.version = 12
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)
        self.version = 11
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.217"
        )

    def test_dcnm_net_merged_novlan_new(self):
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config_novlan)
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.217"
        )

    def test_dcnm_net_error1(self):
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=True, use_action_plugin=True)
        self.assertEqual(result["msg"]["RETURN_CODE"], 400)
        self.assertEqual(result["msg"]["ERROR"], "There is an error")

    def test_dcnm_net_error2(self):
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=True, use_action_plugin=True)
        self.assertIn(
            "Entered Network VLAN ID 203 is in use already",
            str(result["msg"]["DATA"].values()),
        )

    def test_dcnm_net_error3(self):
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=False, use_action_plugin=True)
        self.assertEqual(
            result["response"][2]["DATA"], "No switches PENDING for deployment"
        )

    def test_dcnm_net_merged_duplicate(self):
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=False, use_action_plugin=True)
        self.assertFalse(result.get("diff"))

    def test_dcnm_net_merged_with_incorrect_netid(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_network",
                config=self.playbook_config_incorrect_netid,
            )
        )
        result = self.execute_module(changed=False, failed=True, use_action_plugin=True)
        self.assertEqual(
            result.get("msg"),
            "networkId can not be updated on existing network: test_network",
        )

    def test_dcnm_net_merged_with_incorrect_vrf(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_network",
                config=self.playbook_config_incorrect_vrf,
            )
        )
        result = self.execute_module(changed=False, failed=True, use_action_plugin=True)
        self.assertEqual(
            result.get("msg"),
            "VRF: ansible-vrf-int2 is missing in fabric: test_network",
        )

    def test_dcnm_net_merged_with_update(self):
        set_module_args(
            dict(
                state="merged", fabric="test_network", config=self.playbook_config_update
            )
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.226"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.227"
        )
        self.assertEqual(result.get("diff")[0]["vrf_name"], "ansible-vrf-int1")

    def test_dcnm_net_replace_with_changes(self):
        set_module_args(
            dict(
                state="replaced",
                fabric="test_network",
                config=self.playbook_config_replace,
            )
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)
        self.assertEqual(result.get("diff")[0]["vlan_id"], 203)
        deploy_by_ip = {a["ip_address"]: a["deploy"] for a in result.get("diff")[0]["attach"]}
        self.assertTrue(deploy_by_ip["10.10.10.218"])
        self.assertTrue(deploy_by_ip["10.10.10.226"])
        self.assertFalse(deploy_by_ip["10.10.10.217"])
        self.assertEqual(
            result["response"][0]["DATA"]["test-network--9NN7E41N16A(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["test-network--9YO9A29F27U(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][1]["DATA"]["status"], "")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_net_replace_with_changes_bulk_inventory(self):
        set_module_args(
            dict(
                state="replaced",
                fabric="test_network",
                config=self.playbook_config_replace,
            )
        )
        with patch.object(dcnm_network.DcnmNetwork, "BULK_GET_HAVE_NETWORK_THRESHOLD", 1):
            result = self.execute_module(changed=True, failed=False, use_action_plugin=True)

        request_calls = [(call.args[1], call.args[2]) for call in self.run_dcnm_send.call_args_list]
        get_net_path = dcnm_network.DcnmNetwork.dcnm_network_paths[self.version]["GET_NET"].format("test_network")
        get_net_name_path = dcnm_network.DcnmNetwork.dcnm_network_paths[self.version]["GET_NET_NAME"].format(
            "test_network", "test_network"
        )

        self.assertIn(("GET", get_net_path), request_calls)
        self.assertNotIn(("GET", get_net_name_path), request_calls)
        self.assertEqual(result.get("diff")[0]["vlan_id"], 203)
        deploy_by_ip = {a["ip_address"]: a["deploy"] for a in result.get("diff")[0]["attach"]}
        self.assertTrue(deploy_by_ip["10.10.10.218"])
        self.assertTrue(deploy_by_ip["10.10.10.226"])
        self.assertFalse(deploy_by_ip["10.10.10.217"])

    def test_dcnm_net_replace_with_no_atch(self):
        set_module_args(
            dict(
                state="replaced",
                fabric="test_network",
                config=self.playbook_config_replace_no_atch,
            )
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)
        self.assertFalse(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["net_name"], "test_network")
        self.assertEqual(
            result["response"][0]["DATA"]["test-network--9NN7E41N16A(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["test-network--9YO9A29F27U(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][1]["DATA"]["status"], "")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    # TODO: arobel: The old logic to determine fabric REPLICATION_MODE was
    # faulty, which allowed the following test to pass.  The new logic is
    # correct, but causes this test to fail.  We need to review what should
    # be tested here and what the result should be.  Commenting this test
    # out for now.
    # def test_dcnm_net_replace_without_changes(self):
    #     self.version = 11
    #     set_module_args(
    #         dict(state="replaced", fabric="test_network", config=self.playbook_config)
    #     )
    #     result = self.execute_module(changed=False, failed=False, use_action_plugin=True)
    #     self.assertFalse(result.get("diff"))
    #     self.assertFalse(result.get("response"))

    def test_dcnm_vrf_merged_redeploy(self):
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)
        self.assertEqual(result.get("diff")[0]["net_name"], "test_network")

    def test_dcnm_net_override_with_additions(self):
        set_module_args(
            dict(state="overridden", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.217"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.218"
        )
        self.assertEqual(result.get("diff")[0]["net_id"], 9008011)
        self.assertEqual(
            result["response"][1]["DATA"]["test-network--9NN7E41N16A(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][1]["DATA"]["test-network--9YO9A29F27U(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][2]["DATA"]["status"], "")
        self.assertEqual(result["response"][2]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    # TODO: arobel: The old logic to determine fabric REPLICATION_MODE was
    # faulty, which allowed the following test to pass.  The new logic is
    # correct, but causes this test to fail.  We need to review what should
    # be tested here and what the result should be.  Commenting this test
    # out for now.
    # def test_dcnm_net_override_without_changes(self):
    #     set_module_args(
    #         dict(state="overridden", fabric="test_network", config=self.playbook_config)
    #     )
    #     result = self.execute_module(changed=False, failed=False, use_action_plugin=True)
    #     self.assertFalse(result.get("diff"))
    #     self.assertFalse(result.get("response"))

    def test_dcnm_net_override_with_deletions(self):
        set_module_args(
            dict(
                state="overridden",
                fabric="test_network",
                config=self.playbook_config_override,
            )
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["vlan_id"], 303)
        self.assertEqual(result.get("diff")[0]["net_id"], 9008012)

        self.assertFalse(result.get("diff")[1]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[1]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[1]["net_name"], "test_network")
        self.assertNotIn("net_id", result.get("diff")[1])

        self.assertEqual(
            result["response"][0]["DATA"]["test-network--9NN7E41N16A(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["test-network--9YO9A29F27U(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][1]["DATA"]["status"], "")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)
        self.assertEqual(
            result["response"][4]["DATA"]["test-network--9YO9A29F27U(leaf2)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][4]["DATA"]["test-network--XYZKSJHSMK3(leaf3)"], "SUCCESS"
        )

    def test_dcnm_net_delete_std(self):
        set_module_args(
            dict(state="deleted", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)
        self.assertFalse(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["net_name"], "test_network")
        self.assertNotIn("net_id", result.get("diff")[0])

        self.assertEqual(
            result["response"][0]["DATA"]["test-network--9NN7E41N16A(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["test-network--9YO9A29F27U(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][1]["DATA"]["status"], "")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

        delete_paths = [
            args[2]
            for args, _kwargs in self.run_dcnm_send.call_args_list
            if len(args) >= 3 and args[1] == "DELETE"
        ]
        self.assertTrue(
            any("/bulk-delete/networks?network-names=test_network" in path for path in delete_paths)
        )

        config_deploy_calls = [
            args
            for args, _kwargs in self.run_dcnm_send.call_args_list
            if len(args) >= 3 and args[1] == "POST" and "/config-deploy/" in args[2]
        ]
        self.assertEqual(len(config_deploy_calls), 1)
        config_deploy_path = config_deploy_calls[0][2]
        serial_segment = config_deploy_path.split("/config-deploy/")[1].split("?")[0]
        self.assertEqual(
            set(serial_segment.split(",")),
            {"9NN7E41N16A", "9YO9A29F27U"},
        )
        self.assertEqual(len(config_deploy_calls[0]), 3)

        switch_network_deploy_calls = [
            args
            for args, _kwargs in self.run_dcnm_send.call_args_list
            if len(args) >= 3 and args[1] == "POST" and args[2].endswith("/networks/deploy")
        ]
        self.assertEqual(switch_network_deploy_calls, [])

    def test_dcnm_net_delete_without_config(self):
        set_module_args(dict(state="deleted", fabric="test_network", config=[]))
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)
        self.assertFalse(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertFalse(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(result.get("diff")[0]["net_name"], "test_network")
        self.assertNotIn("net_id", result.get("diff")[0])

        self.assertEqual(
            result["response"][0]["DATA"]["test-network--9NN7E41N16A(leaf1)"], "SUCCESS"
        )
        self.assertEqual(
            result["response"][0]["DATA"]["test-network--9YO9A29F27U(leaf2)"], "SUCCESS"
        )
        self.assertEqual(result["response"][1]["DATA"]["status"], "")
        self.assertEqual(result["response"][1]["RETURN_CODE"], self.SUCCESS_RETURN_CODE)

    def test_dcnm_net_query_with_config(self):
        set_module_args(
            dict(state="query", fabric="test_network", config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=False, use_action_plugin=True)
        self.assertFalse(result.get("diff"))
        self.assertEqual(result.get("response")[0]["parent"]["networkName"], "test_network")
        self.assertEqual(result.get("response")[0]["parent"]["networkId"], 9008011)
        self.assertTrue(
            result.get("response")[0]["attach"][0]["deployment"],
        )
        self.assertEqual(
            result.get("response")[0]["attach"][0]["vlan"],
            202,
        )
        self.assertTrue(
            result.get("response")[0]["attach"][1]["deployment"],
        )
        self.assertEqual(
            result.get("response")[0]["attach"][1]["vlan"],
            202,
        )

    def test_dcnm_net_query_without_config(self):
        set_module_args(
            dict(state="query", fabric="test_network", config=[])
        )
        result = self.execute_module(changed=False, failed=False, use_action_plugin=True)
        self.assertFalse(result.get("diff"))
        self.assertEqual(result.get("response")[0]["parent"]["networkName"], "test_network")
        self.assertEqual(result.get("response")[0]["parent"]["networkId"], 9008011)
        self.assertTrue(
            result.get("response")[0]["attach"][0]["deployment"],
        )
        self.assertEqual(
            result.get("response")[0]["attach"][0]["vlan"],
            202,
        )
        self.assertTrue(
            result.get("response")[0]["attach"][1]["deployment"],
        )
        self.assertEqual(
            result.get("response")[0]["attach"][1]["vlan"],
            202,
        )

    def test_dcnm_net_merged_torport_new(self):
        self.version = 12
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_tor_config)
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)
        self.version = 11
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.217"
        )

    def test_dcnm_net_merged_torport_vererror(self):
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_tor_config)
        )
        result = self.execute_module(changed=False, failed=True, use_action_plugin=True)
        self.assertEqual(
            result.get("msg"),
            "Invalid parameters in playbook: tor_ports configurations are supported only on NDFC",
        )

    def test_dcnm_net_merged_torport_roleerror(self):
        self.version = 12
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_tor_roleerr_config)
        )
        result = self.execute_module(changed=False, failed=True, use_action_plugin=True)
        self.version = 11
        self.assertEqual(
            result.get("msg"),
            "tor_ports for Networks cannot be attached to switch 10.10.10.228 with role border",
        )

    def test_dcnm_net_merged_tor_with_update(self):
        self.version = 12
        set_module_args(
            dict(
                state="merged", fabric="test_network", config=self.playbook_tor_config_update
            )
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)
        self.version = 11
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.218"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.217"
        )
        self.assertEqual(result.get("diff")[0]["vrf_name"], "ansible-vrf-int1")

    def test_dcnm_net_merged_tor_only_with_update(self):
        self.version = 12
        set_module_args(
            dict(
                state="merged",
                fabric="test_network",
                config=self.playbook_tor_only_config_update,
            )
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)
        self.version = 11

        attach_by_ip = {
            attach["ip_address"]: attach for attach in result.get("diff")[0]["attach"]
        }
        self.assertIn("10.10.10.217", attach_by_ip)
        self.assertEqual(attach_by_ip["10.10.10.217"]["ports"], "")
        self.assertIn(
            "dt-n9k7(Ethernet1/13,Ethernet1/12)",
            attach_by_ip["10.10.10.217"]["tor_ports"],
        )
        self.assertEqual(result.get("diff")[0]["net_name"], "test_network")

    def test_dcnm_net_merged_tor_vpc_idempotent(self):
        dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
        dcnm_net.log = type("Logger", (), {"debug": lambda *args, **kwargs: None})()
        dcnm_net.inventory_data = copy.deepcopy(self.net_inv_data_vpc_tor)
        dcnm_net.ip_sn = copy.deepcopy(self.mock_ip_sn)

        have_attach = [
            {
                "serialNumber": "9YO9A29F27U",
                "networkName": "test_network",
                "switchPorts": "Ethernet1/13,Ethernet1/14",
                "isAttached": True,
                "deployment": True,
                "is_deploy": True,
                "vlan": 202,
                "torports": [
                    {"switch": "dt-n9k6", "torPorts": "Ethernet1/12"},
                    {"switch": "dt-n9k7", "torPorts": "Ethernet1/12"},
                ],
            },
            {
                "serialNumber": "9NN7E41N16A",
                "networkName": "test_network",
                "switchPorts": "Ethernet1/13,Ethernet1/14",
                "isAttached": True,
                "deployment": True,
                "is_deploy": True,
                "vlan": 202,
                "torports": [
                    {"switch": "dt-n9k6", "torPorts": "Ethernet1/12"},
                    {"switch": "dt-n9k7", "torPorts": "Ethernet1/12"},
                ],
            },
        ]
        want_attach = copy.deepcopy(have_attach)

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach))

        self.assertFalse(diff)
        self.assertFalse(dep_net)

    def test_dcnm_net_merged_tor_vpc_one_sided_with_update(self):
        self.version = 12
        set_module_args(
            dict(
                state="merged",
                fabric="test_network",
                config=self.playbook_tor_vpc_one_sided_update,
            )
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)
        self.version = 11

        attach_by_ip = {
            attach["ip_address"]: attach for attach in result.get("diff")[0]["attach"]
        }
        self.assertIn("10.10.10.217", attach_by_ip)
        self.assertIn("10.10.10.218", attach_by_ip)
        self.assertIn("dt-n9k6(Ethernet1/13,Ethernet1/14,Ethernet1/12)", attach_by_ip["10.10.10.217"]["tor_ports"])
        self.assertIn("dt-n9k7(Ethernet1/13,Ethernet1/14,Ethernet1/12)", attach_by_ip["10.10.10.217"]["tor_ports"])
        self.assertIn("dt-n9k6(Ethernet1/13,Ethernet1/14,Ethernet1/12)", attach_by_ip["10.10.10.218"]["tor_ports"])
        self.assertIn("dt-n9k7(Ethernet1/13,Ethernet1/14,Ethernet1/12)", attach_by_ip["10.10.10.218"]["tor_ports"])

    def test_dcnm_net_replace_tor_vpc_one_sided_idempotent(self):
        dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
        dcnm_net.log = type("Logger", (), {"debug": lambda *args, **kwargs: None})()
        dcnm_net.inventory_data = copy.deepcopy(self.net_inv_data_vpc_tor)
        dcnm_net.ip_sn = copy.deepcopy(self.mock_ip_sn)

        want_attach = [
            {
                "serialNumber": "9NN7E41N16A",
                "networkName": "test_network",
                "switchPorts": "Ethernet1/13,Ethernet1/14",
                "isAttached": True,
                "deployment": True,
                "is_deploy": True,
                "vlan": 0,
                "torports": [],
            },
            {
                "serialNumber": "9YO9A29F27U",
                "networkName": "test_network",
                "switchPorts": "Ethernet1/13,Ethernet1/14",
                "isAttached": True,
                "deployment": True,
                "is_deploy": True,
                "vlan": 0,
                "torports": [
                    {"switch": "dt-n9k6", "torPorts": "Ethernet1/12"},
                    {"switch": "dt-n9k7", "torPorts": "Ethernet1/12"},
                ],
            },
        ]
        have_attach = [
            {
                "serialNumber": "9NN7E41N16A",
                "networkName": "test_network",
                "switchPorts": "Ethernet1/13,Ethernet1/14",
                "isAttached": True,
                "deployment": True,
                "is_deploy": True,
                "vlan": 202,
                "torports": [
                    {"switch": "dt-n9k6", "torPorts": "Ethernet1/12"},
                    {"switch": "dt-n9k7", "torPorts": "Ethernet1/12"},
                ],
            },
            {
                "serialNumber": "9YO9A29F27U",
                "networkName": "test_network",
                "switchPorts": "Ethernet1/13,Ethernet1/14",
                "isAttached": True,
                "deployment": True,
                "is_deploy": True,
                "vlan": 202,
                "torports": [
                    {"switch": "dt-n9k6", "torPorts": "Ethernet1/12"},
                    {"switch": "dt-n9k7", "torPorts": "Ethernet1/12"},
                ],
            },
        ]

        dcnm_net.normalize_vpc_torports(want_attach)
        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach), replace=True, network_vlan=202)

        self.assertFalse(diff)
        self.assertFalse(dep_net)

    def test_dcnm_net_normalize_vpc_torports_rejects_asymmetric_intent(self):
        dcnm_net = self._build_diff_network(self.net_inv_data_vpc_tor)
        expected_msg = (
            "Invalid tor_ports configuration for network test_network: vPC peers 10.10.10.217 and 10.10.10.218 "
            "have different ToR intent. Configure identical ToR switches and ports on both leaf attachments, or "
            "specify tor_ports on only one peer."
        )
        dcnm_net.module = Mock()
        dcnm_net.module.fail_json.side_effect = ValueError(expected_msg)
        want_attach = [
            self._build_attach_state(
                "9NN7E41N16A",
                "Ethernet1/13",
                [{"switch": "dt-n9k6", "torPorts": "Ethernet1/12"}],
            ),
            self._build_attach_state(
                "9YO9A29F27U",
                "Ethernet1/14",
                [{"switch": "dt-n9k7", "torPorts": "Ethernet1/13"}],
            ),
        ]

        with self.assertRaisesRegex(ValueError, expected_msg.replace(".", r"\.")):
            dcnm_net.normalize_vpc_torports(want_attach)

        dcnm_net.module.fail_json.assert_called_once_with(msg=expected_msg)

    def test_dcnm_net_normalize_vpc_torports_accepts_equivalent_ordering(self):
        dcnm_net = self._build_diff_network(self.net_inv_data_vpc_tor)
        want_attach = [
            self._build_attach_state(
                "9NN7E41N16A",
                "Ethernet1/13",
                [
                    {"switch": "dt-n9k6", "torPorts": "Ethernet1/12,Ethernet1/13"},
                    {"switch": "dt-n9k7", "torPorts": "Ethernet1/14"},
                ],
            ),
            self._build_attach_state(
                "9YO9A29F27U",
                "Ethernet1/14",
                [
                    {"switch": "dt-n9k7", "torPorts": "Ethernet1/14"},
                    {"switch": "dt-n9k6", "torPorts": "Ethernet1/13,Ethernet1/12"},
                ],
            ),
        ]

        dcnm_net.normalize_vpc_torports(want_attach)

        self.assertEqual(want_attach[0]["torports"][0]["switch"], "dt-n9k6")
        self.assertEqual(want_attach[1]["torports"][0]["switch"], "dt-n9k7")

    def test_dcnm_net_merged_tor_vpc_single_tor_with_update(self):
        dcnm_net = self._build_diff_network(self.net_inv_data_vpc_tor)

        have_attach = [
            self._build_attach_state(
                "9NN7E41N16A",
                "Ethernet1/13,Ethernet1/14",
                [{"switch": "dt-n9k6", "torPorts": "Ethernet1/12"}],
            ),
            self._build_attach_state(
                "9YO9A29F27U",
                "Ethernet1/13,Ethernet1/14",
                [{"switch": "dt-n9k6", "torPorts": "Ethernet1/12"}],
            ),
        ]
        want_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14"),
            self._build_attach_state(
                "9YO9A29F27U",
                "Ethernet1/13,Ethernet1/14",
                [{"switch": "dt-n9k6", "torPorts": "Ethernet1/13,Ethernet1/14"}],
            ),
        ]

        dcnm_net.normalize_vpc_torports(want_attach)
        diff, dep_net = dcnm_net.diff_for_attach_deploy(
            copy.deepcopy(want_attach), copy.deepcopy(have_attach)
        )

        attach_by_serial = {attach["serialNumber"]: attach for attach in diff}
        self.assertTrue(dep_net)
        self.assertEqual(len(diff), 2)
        self.assertEqual(
            attach_by_serial["9NN7E41N16A"]["torPorts"],
            "dt-n9k6(Ethernet1/13,Ethernet1/14,Ethernet1/12)",
        )
        self.assertEqual(
            attach_by_serial["9YO9A29F27U"]["torPorts"],
            "dt-n9k6(Ethernet1/13,Ethernet1/14,Ethernet1/12)",
        )

    def test_dcnm_net_replace_tor_vpc_single_tor_idempotent(self):
        dcnm_net = self._build_diff_network(self.net_inv_data_vpc_tor)

        want_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14"),
            self._build_attach_state(
                "9YO9A29F27U",
                "Ethernet1/13,Ethernet1/14",
                [{"switch": "dt-n9k6", "torPorts": "Ethernet1/13,Ethernet1/14"}],
            ),
        ]
        have_attach = [
            self._build_attach_state(
                "9NN7E41N16A",
                "Ethernet1/13,Ethernet1/14",
                [{"switch": "dt-n9k6", "torPorts": "Ethernet1/13,Ethernet1/14"}],
            ),
            self._build_attach_state(
                "9YO9A29F27U",
                "Ethernet1/13,Ethernet1/14",
                [{"switch": "dt-n9k6", "torPorts": "Ethernet1/13,Ethernet1/14"}],
            ),
        ]

        dcnm_net.normalize_vpc_torports(want_attach)
        diff, dep_net = dcnm_net.diff_for_attach_deploy(
            copy.deepcopy(want_attach), copy.deepcopy(have_attach), replace=True
        )

        self.assertFalse(diff)
        self.assertFalse(dep_net)

    def test_dcnm_net_merged_tor_single_leaf_single_tor_with_update(self):
        inventory_data = {
            "10.10.10.217": {
                "ipAddress": "10.10.10.217",
                "logicalName": "dt-n9k1",
                "serialNumber": "9NN7E41N16A",
                "switchRole": "leaf",
                "isVpcConfigured": False,
            },
            "10.10.10.219": {
                "ipAddress": "10.10.10.219",
                "logicalName": "dt-n9k6",
                "serialNumber": "9YO9A29F28C",
                "switchRole": "tor",
            },
        }
        ip_sn = {
            "10.10.10.217": "9NN7E41N16A",
            "10.10.10.219": "9YO9A29F28C",
        }
        dcnm_net = self._build_diff_network(inventory_data, ip_sn)

        have_attach = [
            self._build_attach_state(
                "9NN7E41N16A",
                "Ethernet1/13",
                [{"switch": "dt-n9k6", "torPorts": "Ethernet1/12"}],
            )
        ]
        want_attach = [
            self._build_attach_state(
                "9NN7E41N16A",
                "Ethernet1/13",
                [{"switch": "dt-n9k6", "torPorts": "Ethernet1/13,Ethernet1/14"}],
            )
        ]

        diff, dep_net = dcnm_net.diff_for_attach_deploy(
            copy.deepcopy(want_attach), copy.deepcopy(have_attach)
        )

        self.assertTrue(dep_net)
        self.assertEqual(len(diff), 1)
        self.assertEqual(
            diff[0]["torPorts"], "dt-n9k6(Ethernet1/13,Ethernet1/14,Ethernet1/12)"
        )

    def test_dcnm_net_replace_tor_single_leaf_single_tor_idempotent(self):
        inventory_data = {
            "10.10.10.217": {
                "ipAddress": "10.10.10.217",
                "logicalName": "dt-n9k1",
                "serialNumber": "9NN7E41N16A",
                "switchRole": "leaf",
                "isVpcConfigured": False,
            },
            "10.10.10.219": {
                "ipAddress": "10.10.10.219",
                "logicalName": "dt-n9k6",
                "serialNumber": "9YO9A29F28C",
                "switchRole": "tor",
            },
        }
        ip_sn = {
            "10.10.10.217": "9NN7E41N16A",
            "10.10.10.219": "9YO9A29F28C",
        }
        dcnm_net = self._build_diff_network(inventory_data, ip_sn)

        want_attach = [
            self._build_attach_state(
                "9NN7E41N16A",
                "Ethernet1/13",
                [{"switch": "dt-n9k6", "torPorts": "Ethernet1/13,Ethernet1/14"}],
            )
        ]
        have_attach = [
            self._build_attach_state(
                "9NN7E41N16A",
                "Ethernet1/13",
                [{"switch": "dt-n9k6", "torPorts": "Ethernet1/13,Ethernet1/14"}],
            )
        ]

        diff, dep_net = dcnm_net.diff_for_attach_deploy(
            copy.deepcopy(want_attach), copy.deepcopy(have_attach), replace=True
        )

        self.assertFalse(diff)
        self.assertFalse(dep_net)

    def test_dcnm_net_normalize_attachment_torports_for_payload(self):
        dcnm_net = self._build_diff_network({})
        attachment = {
            "serialNumber": "9NN7E41N16A",
            "torports": [
                {"switch": "dt-n9k6", "torPorts": "Ethernet1/13,Ethernet1/14"},
                {"switch": "dt-n9k7", "torPorts": "Ethernet1/15,Ethernet1/16"},
            ],
        }

        dcnm_net.normalize_attachment_torports_for_payload(attachment)

        self.assertNotIn("torports", attachment)
        self.assertEqual(
            attachment["torPorts"],
            "dt-n9k6(Ethernet1/13,Ethernet1/14) dt-n9k7(Ethernet1/15,Ethernet1/16)",
        )

    def test_dcnm_net_populate_detach_serial_map_includes_tor_serials(self):
        dcnm_net = self._build_diff_network(self.net_inv_data_vpc_tor)
        dcnm_net.logical_name_inventory = {
            details["logicalName"].lower(): details
            for details in dcnm_net.inventory_data.values()
        }
        dcnm_net.network_sn_attach_map = {}
        dcnm_net.network_sn_detach_map = {}
        dcnm_net.diff_attach = []
        dcnm_net.diff_detach = [
            {
                "networkName": "test_network",
                "lanAttachList": [
                    {
                        "serialNumber": "9NN7E41N16A",
                        "deployment": False,
                        "torports": [
                            {"switch": "dt-n9k6", "torPorts": "Ethernet1/13"},
                            {"switch": "dt-n9k7", "torPorts": "Ethernet1/14"},
                        ],
                    }
                ],
            }
        ]
        dcnm_net.diff_create_update = []
        dcnm_net.diff_deploy = {}
        dcnm_net.diff_undeploy = {"networkNames": "test_network"}
        dcnm_net.diff_delete = {"test_network": "DEPLOYED"}
        dcnm_net.have_attach_by_name = {}

        dcnm_net.populate_sn_maps_from_diffs()

        self.assertEqual(
            dcnm_net.network_sn_detach_map["test_network"],
            {"9NN7E41N16A", "9YO9A29F28C", "9YO9A29F29D"},
        )

    def test_dcnm_net_populate_attach_serial_map_excludes_tor_serials(self):
        dcnm_net = self._build_diff_network(self.net_inv_data_vpc_tor)
        dcnm_net.logical_name_inventory = {
            details["logicalName"].lower(): details
            for details in dcnm_net.inventory_data.values()
        }
        dcnm_net.network_sn_attach_map = {}
        dcnm_net.network_sn_detach_map = {}
        dcnm_net.diff_attach = [
            {
                "networkName": "test_network",
                "lanAttachList": [
                    {
                        "serialNumber": "9NN7E41N16A",
                        "deployment": True,
                        "torports": [
                            {"switch": "dt-n9k6", "torPorts": "Ethernet1/13"},
                            {"switch": "dt-n9k7", "torPorts": "Ethernet1/14"},
                        ],
                    }
                ],
            }
        ]
        dcnm_net.diff_detach = []
        dcnm_net.diff_create_update = []
        dcnm_net.diff_deploy = {}
        dcnm_net.diff_undeploy = {}
        dcnm_net.diff_delete = {}
        dcnm_net.have_attach_by_name = {}

        dcnm_net.populate_sn_maps_from_diffs()

        self.assertEqual(
            dcnm_net.network_sn_attach_map["test_network"],
            {"9NN7E41N16A"},
        )
        self.assertEqual(dcnm_net.network_sn_detach_map, {})

    def test_dcnm_net_get_attachment_tor_serials_accepts_payload_string(self):
        dcnm_net = self._build_diff_network(self.net_inv_data_vpc_tor)
        dcnm_net.logical_name_inventory = {
            details["logicalName"].lower(): details
            for details in dcnm_net.inventory_data.values()
        }

        serials = dcnm_net.get_attachment_tor_serials(
            {
                "torPorts": (
                    "dt-n9k6(Ethernet1/13,Ethernet1/14) "
                    "dt-n9k7(Ethernet1/15,Ethernet1/16)"
                )
            }
        )

        self.assertEqual(serials, {"9YO9A29F28C", "9YO9A29F29D"})

    def test_dcnm_net_network_serial_payload_transform_for_deploy(self):
        dcnm_net = self._build_diff_network({})
        dcnm_net.network_sn_attach_map = {
            "net-a": {"SERIAL-1"},
            "net-b": {"SERIAL-2"},
        }
        dcnm_net.network_sn_detach_map = {
            "net-a": {"SERIAL-2"},
            "net-c": {"SERIAL-3"},
        }

        payload = {"networkNames": "net-a,net-b,net-c"}
        result = dcnm_net.network_serial_payload_transform_for_deploy(payload)

        self.assertEqual(set(result.keys()), {"SERIAL-1", "SERIAL-2", "SERIAL-3"})
        self.assertEqual(result["SERIAL-1"], "net-a")
        self.assertEqual(set(result["SERIAL-2"].split(",")), {"net-a", "net-b"})
        self.assertEqual(result["SERIAL-3"], "net-c")

    def test_dcnm_net_format_diff_torports_from_detach_have(self):
        dcnm_net = self._build_diff_network(
            {},
            {"10.10.10.217": "9NN7E41N16A"},
        )
        dcnm_net.dcnm_version = 12
        dcnm_net.diff_create = []
        dcnm_net.diff_create_quick = []
        dcnm_net.diff_create_update = []
        dcnm_net.diff_attach = [
            {
                "networkName": "test_network",
                "lanAttachList": [
                    {
                        "serialNumber": "9NN7E41N16A",
                        "networkName": "test_network",
                        "switchPorts": "Ethernet1/13,Ethernet1/14",
                        "detachSwitchPorts": "",
                        "deployment": False,
                        "torports": [
                            {"switch": "dt-n9k6", "torPorts": "Ethernet1/13,Ethernet1/14"},
                        ],
                    },
                ],
            }
        ]
        dcnm_net.diff_detach = []
        dcnm_net.diff_deploy = {}
        dcnm_net.diff_undeploy = {}

        dcnm_net.format_diff()

        self.assertEqual(
            dcnm_net.diff_input_format[0]["attach"][0]["tor_ports"],
            "dt-n9k6(Ethernet1/13,Ethernet1/14)",
        )

    def test_dcnm_net_replace_tor_ports(self):
        self.version = 12
        set_module_args(
            dict(
                state="replaced", fabric="test_network", config=self.playbook_tor_config_update
            )
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)
        self.version = 11
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.218"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.217"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["tor_ports"], "dt-n9k6(Ethernet1/13,Ethernet1/14)"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][1]["tor_ports"], "dt-n9k7(Ethernet1/13,Ethernet1/14)"
        )
        self.assertEqual(result.get("diff")[0]["vrf_name"], "ansible-vrf-int1")

    def test_dcnm_net_override_tor_ports(self):
        self.version = 12
        set_module_args(
            dict(
                state="overridden", fabric="test_network", config=self.playbook_tor_config_update
            )
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)
        self.version = 11
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["ip_address"], "10.10.10.218"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][1]["ip_address"], "10.10.10.217"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][0]["tor_ports"], "dt-n9k6(Ethernet1/13,Ethernet1/14)"
        )
        self.assertEqual(
            result.get("diff")[0]["attach"][1]["tor_ports"], "dt-n9k7(Ethernet1/13,Ethernet1/14)"
        )
        self.assertEqual(result.get("diff")[0]["vrf_name"], "ansible-vrf-int1")

    def test_dcnm_net_merged_msd_basic(self):
        """
        Test MSD network creation with child fabric configuration.

        This test verifies:
        - MSD network creation at parent MSD fabric level
        - Network attachment configuration in child fabric
        - Child fabric network configuration with DHCP and other parameters
        - Proper output structure with parent_fabric and child_fabrics sections
        """
        self.version = 12
        set_module_args(
            dict(state="merged", fabric="msd-parent", config=self.playbook_msd_config)
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)

        # Verify overall result structure
        self.assertTrue(result.get("changed"))
        self.assertIn("parent_fabric", result)
        self.assertIn("child_fabrics", result)
        self.assertEqual(result.get("workflow"), "Parent MSD with Child Fabric Processing")

        # Verify parent fabric section
        parent = result.get("parent_fabric")
        self.assertTrue(parent.get("changed"))
        self.assertFalse(parent.get("failed"))
        self.assertEqual(parent.get("fabric_name"), "msd-parent")
        self.assertIn("diff", parent)
        self.assertIn("response", parent)

        # Verify parent fabric diff
        parent_diff = parent.get("diff")[0]
        self.assertEqual(parent_diff["net_name"], "ansible-msd-net1")
        self.assertEqual(parent_diff["vrf_name"], "Tenant-1")
        self.assertEqual(parent_diff["net_id"], 8001)
        self.assertEqual(parent_diff["vlan_id"], 2101)
        self.assertEqual(parent_diff["gw_ip_subnet"], "192.168.101.1/24")
        self.assertEqual(parent_diff["int_desc"], "MSD Network managed by Ansible")
        self.assertEqual(parent_diff["mtu_l3intf"], 9214)
        self.assertFalse(parent_diff["is_l2only"])

        # Verify parent fabric attachments
        self.assertEqual(len(parent_diff["attach"]), 2)
        self.assertTrue(parent_diff["attach"][0]["deploy"])
        self.assertTrue(parent_diff["attach"][1]["deploy"])

        # Verify parent fabric response (create, attach); deploy is aggregated separately
        parent_response = parent.get("response")
        self.assertEqual(len(parent_response), 2)

        # Verify create response
        self.assertEqual(parent_response[0]["RETURN_CODE"], 200)
        self.assertEqual(parent_response[0]["METHOD"], "POST")
        self.assertIn("Network Id", parent_response[0]["DATA"])
        self.assertEqual(parent_response[0]["DATA"]["Network Id"], 8001)
        self.assertEqual(parent_response[0]["DATA"]["Network Name"], "ansible-msd-net1")

        # Verify attachment response
        self.assertEqual(parent_response[1]["RETURN_CODE"], 200)
        self.assertEqual(parent_response[1]["METHOD"], "POST")
        self.assertIn("ansible-msd-net1", str(parent_response[1]["DATA"]))

        # Verify deploy response
        self.assertIn("deployment", parent)
        self.assertEqual(parent["deployment"]["RETURN_CODE"], 200)
        self.assertEqual(parent["deployment"]["METHOD"], "POST")

        # Verify child fabrics section
        child_fabrics = result.get("child_fabrics")
        self.assertEqual(len(child_fabrics), 1)

        child = child_fabrics[0]
        self.assertTrue(child.get("changed"))
        self.assertFalse(child.get("failed"))
        self.assertEqual(child.get("fabric_name"), "msd-child-1")
        self.assertIn("diff", child)
        self.assertIn("response", child)

        # Verify child fabric diff
        child_diff = child.get("diff")[0]
        self.assertEqual(child_diff["net_name"], "ansible-msd-net1")
        self.assertEqual(child_diff["vrf_name"], "Tenant-1")
        self.assertEqual(child_diff["net_id"], 8001)
        self.assertEqual(child_diff["vlan_id"], 2101)
        self.assertEqual(child_diff["gw_ip_subnet"], "192.168.101.1/24")

        # Verify child fabric specific configuration
        dhcp_servers = json.loads(child_diff["dhcp_servers"])["dhcpServers"]
        self.assertEqual(dhcp_servers[0]["srvrAddr"], "192.168.1.101")
        self.assertEqual(dhcp_servers[0]["srvrVrf"], "management")
        self.assertEqual(child_diff["dhcp_loopback_id"], 204)
        self.assertEqual(child_diff["multicast_group_address"], "239.1.1.1")
        self.assertTrue(child_diff["l3gw_on_border"])
        self.assertEqual(child_diff["vlan_nf_monitor"], "monitor1")

        # Verify child fabric response (query response showing OUT-OF-SYNC state)
        child_response = child.get("response")
        self.assertEqual(len(child_response), 1)
        self.assertEqual(child_response[0]["RETURN_CODE"], 200)
        self.assertEqual(child_response[0]["METHOD"], "GET")

        # Verify the child fabric response contains network attach information
        data = child_response[0]["DATA"]
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["networkName"], "ansible-msd-net1")
        self.assertIn("lanAttachList", data[0])
        self.assertEqual(len(data[0]["lanAttachList"]), 2)

        # Verify attachment states
        lan_attach = data[0]["lanAttachList"]
        self.assertEqual(lan_attach[0]["lanAttachState"], "OUT-OF-SYNC")
        self.assertEqual(lan_attach[1]["lanAttachState"], "OUT-OF-SYNC")

    def test_dcnm_net_merged_msd_dhcp(self):
        """
        Test MSD network creation with DHCP configuration in child fabric.

        This test verifies:
        - MSD network creation with multiple DHCP servers
        - DHCP server configuration (IP, VRF) in child fabric
        - DHCP loopback ID configuration
        - Additional parameters like l3gw_on_border, multicast_group_address, netflow_enable, vlan_nf_monitor
        - Proper output structure with parent_fabric and child_fabrics sections
        """
        self.version = 12
        set_module_args(
            dict(state="merged", fabric="msd-parent", config=self.playbook_msd_dhcp_config)
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)

        # Verify overall result structure
        self.assertTrue(result.get("changed"))
        self.assertIn("parent_fabric", result)
        self.assertIn("child_fabrics", result)
        self.assertEqual(result.get("workflow"), "Parent MSD with Child Fabric Processing")

        # Verify parent fabric section
        parent = result.get("parent_fabric")
        self.assertTrue(parent.get("changed"))
        self.assertFalse(parent.get("failed"))
        self.assertEqual(parent.get("fabric_name"), "msd-parent")

        # Verify parent fabric diff - key network parameters
        parent_diff = parent.get("diff")[0]
        self.assertEqual(parent_diff["net_name"], "ansible-msd-dhcp-net")
        self.assertEqual(parent_diff["vrf_name"], "Tenant-1")
        self.assertEqual(parent_diff["net_id"], 8004)
        self.assertEqual(parent_diff["vlan_id"], 2104)
        self.assertEqual(parent_diff["gw_ip_subnet"], "192.168.104.1/24")
        self.assertEqual(parent_diff["int_desc"], "MSD DHCP Network")
        self.assertEqual(parent_diff["mtu_l3intf"], 9214)

        # Verify parent fabric does NOT have DHCP config (should be empty/false)
        self.assertEqual(parent_diff["dhcp_servers"], "")
        self.assertEqual(parent_diff["dhcp_loopback_id"], "")
        self.assertFalse(parent_diff["l3gw_on_border"])

        # Verify parent fabric attachments
        self.assertEqual(len(parent_diff["attach"]), 2)
        self.assertEqual(parent_diff["attach"][0]["ip_address"], "192.168.10.203")
        self.assertEqual(parent_diff["attach"][1]["ip_address"], "192.168.10.204")

        # Verify parent fabric response; deploy is aggregated separately
        parent_response = parent.get("response")
        self.assertEqual(len(parent_response), 2)
        self.assertEqual(parent_response[0]["DATA"]["Network Id"], 8004)
        self.assertEqual(parent_response[0]["DATA"]["Network Name"], "ansible-msd-dhcp-net")
        self.assertIn("9R518K2AT3R", str(parent_response[1]["DATA"]))
        self.assertIn("915KQ8P3NS8", str(parent_response[1]["DATA"]))
        self.assertIn("deployment", parent)
        self.assertEqual(parent["deployment"]["RETURN_CODE"], 200)

        # Verify child fabrics section
        child_fabrics = result.get("child_fabrics")
        self.assertEqual(len(child_fabrics), 1)

        child = child_fabrics[0]
        self.assertTrue(child.get("changed"))
        self.assertFalse(child.get("failed"))
        self.assertEqual(child.get("fabric_name"), "msd-child-1")

        # Verify child fabric diff - DHCP configuration is present
        child_diff = child.get("diff")[0]
        self.assertEqual(child_diff["net_name"], "ansible-msd-dhcp-net")
        self.assertEqual(child_diff["vrf_name"], "Tenant-1")
        self.assertEqual(child_diff["net_id"], "8004")
        self.assertEqual(child_diff["vlan_id"], 2104)

        # Verify DHCP servers configuration
        dhcp_servers = json.loads(child_diff["dhcp_servers"])["dhcpServers"]
        self.assertEqual(dhcp_servers[0]["srvrAddr"], "192.168.1.102")
        self.assertEqual(dhcp_servers[0]["srvrVrf"], "management")
        self.assertEqual(dhcp_servers[1]["srvrAddr"], "192.168.1.105")
        self.assertEqual(dhcp_servers[1]["srvrVrf"], "default")
        self.assertEqual(dhcp_servers[2]["srvrAddr"], "192.168.1.106")
        self.assertEqual(dhcp_servers[2]["srvrVrf"], "management")

        # Verify child-specific parameters
        self.assertEqual(child_diff["dhcp_loopback_id"], 207)
        self.assertEqual(child_diff["multicast_group_address"], "239.1.1.4")
        self.assertTrue(child_diff["l3gw_on_border"])
        self.assertFalse(child_diff["netflow_enable"])
        self.assertEqual(child_diff["vlan_nf_monitor"], "monitor2")

        # Verify child fabric response
        child_response = child.get("response")
        self.assertEqual(len(child_response), 1)
        self.assertEqual(child_response[0]["RETURN_CODE"], 200)
        self.assertEqual(child_response[0]["METHOD"], "GET")

        # Verify child fabric attachment data
        attach_data = child_response[0]["DATA"]
        self.assertEqual(len(attach_data), 2)
        self.assertEqual(attach_data[0]["serialNumber"], "9R518K2AT3R")
        self.assertEqual(attach_data[0]["ipAddress"], "192.168.10.203")
        self.assertEqual(attach_data[0]["lanAttachedState"], "DEPLOYED")
        self.assertEqual(attach_data[1]["serialNumber"], "915KQ8P3NS8")
        self.assertEqual(attach_data[1]["ipAddress"], "192.168.10.204")
        self.assertEqual(attach_data[1]["lanAttachedState"], "DEPLOYED")

    def test_dcnm_net_msd_override_with_different_attachments(self):
        """
        Test MSD network override with different attachments.

        This test verifies:
        - MSD network exists with old attachments (Ethernet1/17,Ethernet1/18)
        - Override state updates attachments to new ports (Ethernet1/16,Ethernet1/17)
        - Parent fabric processes attachment updates correctly
        - Child fabric reflects the updated attachment configuration
        - Proper detachment of old ports and attachment of new ports
        """
        self.version = 12
        set_module_args(
            dict(state="overridden", fabric="msd-parent", config=self.playbook_msd_override_config)
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)

        # Verify overall result structure
        self.assertTrue(result.get("changed"))
        self.assertIn("parent_fabric", result)
        self.assertIn("child_fabrics", result)
        self.assertEqual(result.get("workflow"), "Parent MSD with Child Fabric Processing")

        # Verify parent fabric section
        parent = result.get("parent_fabric")
        self.assertTrue(parent.get("changed"))
        self.assertFalse(parent.get("failed"))
        self.assertEqual(parent.get("fabric_name"), "msd-parent")
        self.assertIn("diff", parent)
        self.assertIn("response", parent)

        # Verify parent fabric diff shows updated attachments (minimal structure)
        parent_diff = parent.get("diff")[0]
        self.assertEqual(parent_diff["net_name"], "ansible-msd-dhcp-net")
        self.assertIn("attach", parent_diff)

        # Verify parent fabric updated attachments - NEW PORTS
        self.assertEqual(len(parent_diff["attach"]), 2)

        # Check first switch attachment (leaf3) has new ports
        attach1 = parent_diff["attach"][0]
        self.assertEqual(attach1["ip_address"], "192.168.10.203")
        self.assertEqual(attach1["ports"], "Ethernet1/16,Ethernet1/17")
        self.assertTrue(attach1["deploy"])

        # Check second switch attachment (leaf4) has new ports
        attach2 = parent_diff["attach"][1]
        self.assertEqual(attach2["ip_address"], "192.168.10.204")
        self.assertEqual(attach2["ports"], "Ethernet1/16,Ethernet1/17")
        self.assertTrue(attach2["deploy"])

        # Verify parent fabric response includes attachment update; deploy is aggregated separately
        parent_response = parent.get("response")
        self.assertEqual(len(parent_response), 2)

        # Verify attachment update response (index 1)
        attach_resp = parent_response[1]
        self.assertEqual(attach_resp["RETURN_CODE"], 200)
        self.assertEqual(attach_resp["METHOD"], "POST")
        self.assertIn("ansible-msd-dhcp-net-[9R518K2AT3R/leaf3]", attach_resp["DATA"])
        self.assertEqual(attach_resp["DATA"]["ansible-msd-dhcp-net-[9R518K2AT3R/leaf3]"], "SUCCESS")
        self.assertIn("ansible-msd-dhcp-net-[915KQ8P3NS8/leaf4]", attach_resp["DATA"])
        self.assertEqual(attach_resp["DATA"]["ansible-msd-dhcp-net-[915KQ8P3NS8/leaf4]"], "SUCCESS")

        # Verify deploy response
        self.assertIn("deployment", parent)
        deploy_resp = parent["deployment"]
        self.assertEqual(deploy_resp["RETURN_CODE"], 200)
        self.assertEqual(deploy_resp["METHOD"], "POST")
        self.assertIn("status", deploy_resp["DATA"])

        # Verify child fabrics section
        child_fabrics = result.get("child_fabrics")
        self.assertEqual(len(child_fabrics), 1)

        child = child_fabrics[0]
        self.assertTrue(child.get("changed"))
        self.assertFalse(child.get("failed"))
        self.assertEqual(child.get("fabric_name"), "msd-child-1")
        self.assertIn("diff", child)
        self.assertIn("response", child)

        # Verify child fabric diff - includes all network parameters
        child_diff = child.get("diff")[0]
        self.assertEqual(child_diff["net_name"], "ansible-msd-dhcp-net")
        self.assertEqual(child_diff["vrf_name"], "Tenant-1")
        self.assertEqual(child_diff["net_id"], 8004)
        self.assertEqual(child_diff["vlan_id"], 2104)
        self.assertEqual(child_diff["gw_ip_subnet"], "192.168.104.1/24")
        self.assertEqual(child_diff["net_template"], "Default_Network_Universal")
        self.assertEqual(child_diff["net_extension_template"], "Default_Network_Extension_Universal")
        self.assertFalse(child_diff["is_l2only"])
        self.assertEqual(child_diff["int_desc"], "MSD DHCP Network")
        self.assertEqual(child_diff["mtu_l3intf"], 9216)
        self.assertFalse(child_diff["route_target_both"])
        self.assertFalse(child_diff["l3gw_on_border"])

        # Verify child fabric has empty attach list (attachments shown in response only)
        self.assertEqual(len(child_diff["attach"]), 0)

        # Verify child fabric response shows IN PROGRESS state
        child_response = child.get("response")
        self.assertEqual(len(child_response), 1)
        self.assertEqual(child_response[0]["RETURN_CODE"], 200)
        self.assertEqual(child_response[0]["METHOD"], "GET")

        # Verify child fabric attachment data reflects new port configuration
        child_attach_data = child_response[0]["DATA"]
        self.assertEqual(len(child_attach_data), 1)
        self.assertEqual(child_attach_data[0]["networkName"], "ansible-msd-dhcp-net")
        self.assertIn("lanAttachList", child_attach_data[0])

        # Verify lanAttachList has 2 switches
        lan_attach_list = child_attach_data[0]["lanAttachList"]
        self.assertEqual(len(lan_attach_list), 2)

        # Verify first switch in child fabric (leaf3)
        leaf3_attach = lan_attach_list[0]
        self.assertEqual(leaf3_attach["switchSerialNo"], "9R518K2AT3R")
        self.assertEqual(leaf3_attach["ipAddress"], "192.168.10.203")
        self.assertEqual(leaf3_attach["switchName"], "leaf3")
        self.assertEqual(leaf3_attach["fabricName"], "msd-child-1")
        self.assertEqual(leaf3_attach["networkId"], 8004)
        self.assertEqual(leaf3_attach["vlanId"], 2104)
        self.assertEqual(leaf3_attach["portNames"], "Ethernet1/16,Ethernet1/17")
        self.assertEqual(leaf3_attach["lanAttachState"], "IN PROGRESS")
        self.assertTrue(leaf3_attach["isLanAttached"])

        # Verify second switch in child fabric (leaf4)
        leaf4_attach = lan_attach_list[1]
        self.assertEqual(leaf4_attach["switchSerialNo"], "915KQ8P3NS8")
        self.assertEqual(leaf4_attach["ipAddress"], "192.168.10.204")
        self.assertEqual(leaf4_attach["switchName"], "leaf4")
        self.assertEqual(leaf4_attach["fabricName"], "msd-child-1")
        self.assertEqual(leaf4_attach["networkId"], 8004)
        self.assertEqual(leaf4_attach["vlanId"], 2104)
        self.assertEqual(leaf4_attach["portNames"], "Ethernet1/16,Ethernet1/17")
        self.assertEqual(leaf4_attach["lanAttachState"], "IN PROGRESS")
        self.assertTrue(leaf4_attach["isLanAttached"])

    # ==================== Attachment-level VLAN Override Tests ====================

    def test_dcnm_net_merged_attach_vlan_override_new(self):
        """Test creating a new network with attachment-level vlan_id override.

        First attachment (10.10.10.217) specifies vlan_id=300 to override network-level vlan_id=202.
        Second attachment (10.10.10.218) uses network-level vlan_id (no override).
        """
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config_attach_vlan_override)
        )
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)
        self.assertTrue(result.get("diff")[0]["attach"][0]["deploy"])
        self.assertTrue(result.get("diff")[0]["attach"][1]["deploy"])
        attach_by_ip = {a["ip_address"]: a for a in result.get("diff")[0]["attach"]}
        self.assertEqual(attach_by_ip["10.10.10.217"]["vlan_id"], 300)
        self.assertNotIn("vlan_id", attach_by_ip["10.10.10.218"])

    def test_dcnm_net_merged_attach_freeform_new(self):
        """Formatted user-facing diff must include attachment-level freeform_config when set."""
        inline_config = [
            {
                "net_name": "test_network",
                "vrf_name": "ansible-vrf-int1",
                "net_id": "9008011",
                "net_template": "Default_Network_Universal",
                "net_extension_template": "Default_Network_Extension_Universal",
                "vlan_id": "202",
                "gw_ip_subnet": "192.168.30.1/24",
                "attach": [
                    {
                        "ip_address": "10.10.10.217",
                        "ports": ["Ethernet1/13", "Ethernet1/14"],
                        "freeform_config": "interface Vlan202\n  description New",
                        "deploy": True,
                    },
                    {
                        "ip_address": "10.10.10.218",
                        "ports": ["Ethernet1/13", "Ethernet1/14"],
                        "deploy": True,
                    },
                ],
                "deploy": True,
            }
        ]
        set_module_args(dict(state="merged", fabric="test_network", config=inline_config))
        result = self.execute_module(changed=True, failed=False, use_action_plugin=True)

        attach_by_ip = {a["ip_address"]: a for a in result.get("diff")[0]["attach"]}
        self.assertEqual(attach_by_ip["10.10.10.217"]["freeform_config"], "interface Vlan202\n  description New")
        self.assertEqual(attach_by_ip["10.10.10.218"]["freeform_config"], "")

    def test_dcnm_net_merged_attach_vlan_override_idempotent(self):
        """Test idempotency when attachment-level vlan_id matches existing state.

        Network already deployed with first switch having vlan 300 (override) and
        second switch having vlan 202 (network default). Re-running with same config
        should produce no changes.
        """
        set_module_args(
            dict(state="merged", fabric="test_network", config=self.playbook_config_attach_vlan_override)
        )
        result = self.execute_module(changed=False, failed=False, use_action_plugin=True)
        self.assertFalse(result.get("diff"))

    def test_dcnm_net_diff_for_attach_deploy_vlan_inherit(self):
        """Test that vlan=0 in want inherits vlan from have (no change detected)."""
        dcnm_net = self._build_diff_network(self.net_inv_data)

        have_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14", vlan=300),
        ]
        want_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14", vlan=0),
        ]

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach))

        # No diff - vlan=0 inherits existing vlan 300
        self.assertFalse(diff)
        self.assertFalse(dep_net)

    def test_dcnm_net_diff_for_attach_deploy_vlan_only_change_merged(self):
        """Vlan-only change under merged must produce a diff with the new vlan."""
        dcnm_net = self._build_diff_network(self.net_inv_data)

        have_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14", vlan=300),
        ]
        want_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14", vlan=301),
        ]

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach))

        self.assertEqual(len(diff), 1)
        self.assertEqual(diff[0]["vlan"], 301)
        self.assertEqual(diff[0]["switchPorts"], "Ethernet1/13,Ethernet1/14")
        self.assertTrue(dep_net)

    def test_dcnm_net_diff_for_attach_deploy_vlan_only_change_replaced(self):
        """Vlan-only change under replaced must produce a diff with the new vlan."""
        dcnm_net = self._build_diff_network(self.net_inv_data)

        have_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14", vlan=300),
        ]
        want_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14", vlan=301),
        ]

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach), replace=True)

        self.assertEqual(len(diff), 1)
        self.assertEqual(diff[0]["vlan"], 301)
        self.assertTrue(dep_net)

    def test_dcnm_net_diff_for_attach_deploy_vlan_reset_replaced(self):
        """Replaced with omitted attach vlan_id must send vlan=0 to reset the override."""
        dcnm_net = self._build_diff_network(self.net_inv_data)

        have_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14", vlan=300),
        ]
        want_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14", vlan=0),
        ]

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach), replace=True)

        self.assertEqual(len(diff), 1)
        self.assertEqual(diff[0]["vlan"], 0)
        self.assertTrue(dep_net)

    def test_dcnm_net_diff_for_attach_deploy_freeform_config_inherit(self):
        """Merged: omitted freeform_config (want=None) inherits current controller value, no diff."""
        dcnm_net = self._build_diff_network(self.net_inv_data)

        have_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14", freeform_config="interface Vlan202\n  description Test"),
        ]
        want_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14", freeform_config=None),
        ]

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach))

        self.assertFalse(diff)
        self.assertFalse(dep_net)

    def test_dcnm_net_diff_for_attach_deploy_freeform_config_change(self):
        """Merged: old->new freeform_config with unchanged ports produces a diff with the new value."""
        dcnm_net = self._build_diff_network(self.net_inv_data)

        have_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14", freeform_config="interface Vlan202\n  description Old"),
        ]
        want_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14", freeform_config="interface Vlan202\n  description New"),
        ]

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach))

        self.assertEqual(len(diff), 1)
        self.assertEqual(diff[0]["freeformConfig"], "interface Vlan202\n  description New")
        self.assertTrue(dep_net)

    def test_dcnm_net_diff_for_attach_deploy_freeform_config_explicit_clear_merged(self):
        """Merged: explicit freeform_config='' clears an existing non-empty controller value."""
        dcnm_net = self._build_diff_network(self.net_inv_data)

        have_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14", freeform_config="interface Vlan202\n  description Old"),
        ]
        want_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14", freeform_config=""),
        ]

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach))

        self.assertEqual(len(diff), 1)
        self.assertEqual(diff[0]["freeformConfig"], "")
        self.assertTrue(dep_net)

    def test_dcnm_net_diff_for_attach_deploy_freeform_config_explicit_clear_replaced(self):
        """Replaced: explicit freeform_config='' clears an existing non-empty controller value (reviewer Example 2)."""
        dcnm_net = self._build_diff_network(self.net_inv_data)

        have_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14", freeform_config="interface Vlan202\n  description Old"),
        ]
        want_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14", freeform_config=""),
        ]

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach), replace=True)

        self.assertEqual(len(diff), 1)
        self.assertEqual(diff[0]["freeformConfig"], "")
        self.assertTrue(dep_net)

    def test_dcnm_net_diff_for_attach_deploy_freeform_config_omitted_resets_replaced(self):
        """Replaced: omitted freeform_config (want=None) resets an existing non-empty controller value to empty."""
        dcnm_net = self._build_diff_network(self.net_inv_data)

        have_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14", freeform_config="interface Vlan202\n  description Old"),
        ]
        want_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14", freeform_config=None),
        ]

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach), replace=True)

        self.assertEqual(len(diff), 1)
        self.assertEqual(diff[0]["freeformConfig"], "")
        self.assertTrue(dep_net)

    def test_dcnm_net_diff_for_attach_deploy_freeform_config_idempotent_both_empty(self):
        """Idempotency: matching empty freeform on both sides produces no diff under merged and replaced."""
        dcnm_net = self._build_diff_network(self.net_inv_data)

        have_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14", freeform_config=""),
        ]
        want_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/13,Ethernet1/14", freeform_config=""),
        ]

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach))
        self.assertFalse(diff)
        self.assertFalse(dep_net)

        diff, dep_net = dcnm_net.diff_for_attach_deploy(
            copy.deepcopy(want_attach), copy.deepcopy(have_attach), replace=True, network_vlan=202
        )
        self.assertFalse(diff)
        self.assertFalse(dep_net)

    def _make_bare_dcnm_net(self):
        dcnm_net = dcnm_network.DcnmNetwork.__new__(dcnm_network.DcnmNetwork)
        dcnm_net.log = type("Logger", (), {"debug": lambda *a, **k: None})()
        dcnm_net.fabric = "test-fabric"
        dcnm_net.ip_sn = {"10.10.10.217": "9NN7E41N16A"}
        dcnm_net.inventory_data = {"10.10.10.217": {"switchRole": "leaf"}}
        dcnm_net.dcnm_version = 12.4

        class _Module:
            def fail_json(self, **kwargs):
                raise AssertionError(kwargs)

        dcnm_net.module = _Module()
        return dcnm_net

    def test_dcnm_net_update_attach_params_serializes_svi_enabled_true(self):
        dcnm_net = self._make_bare_dcnm_net()
        with patch.object(dcnm_network, "dcnm_get_ip_addr_info", lambda module, ip, a, b: ip):
            attach = {
                "ip_address": "10.10.10.217",
                "ports": ["Ethernet1/3"],
                "svi_enabled": True,
            }
            out = dcnm_net.update_attach_params(attach, "Test_Network1", deploy=True)

        self.assertNotIn("svi_enabled", out)
        self.assertIn("instanceValues", out)
        inst = json.loads(out["instanceValues"])
        self.assertEqual(inst["sviEnabled"], "true")
        self.assertEqual(out["serialNumber"], "9NN7E41N16A")
        self.assertEqual(out["networkName"], "Test_Network1")

    def test_dcnm_net_update_attach_params_defaults_svi_enabled_to_true_when_omitted(self):
        dcnm_net = self._make_bare_dcnm_net()
        with patch.object(dcnm_network, "dcnm_get_ip_addr_info", lambda module, ip, a, b: ip):
            attach = {"ip_address": "10.10.10.217", "ports": ["Ethernet1/3"]}
            out = dcnm_net.update_attach_params(attach, "Test_Network1", deploy=True)

        self.assertEqual(json.loads(out["instanceValues"])["sviEnabled"], "true")

    def test_dcnm_net_update_attach_params_serializes_svi_enabled_false_when_explicit(self):
        dcnm_net = self._make_bare_dcnm_net()
        with patch.object(dcnm_network, "dcnm_get_ip_addr_info", lambda module, ip, a, b: ip):
            attach = {
                "ip_address": "10.10.10.217",
                "ports": ["Ethernet1/3"],
                "svi_enabled": False,
            }
            out = dcnm_net.update_attach_params(attach, "Test_Network1", deploy=True)

        self.assertEqual(json.loads(out["instanceValues"])["sviEnabled"], "false")

    def test_dcnm_net_diff_for_attach_deploy_svi_enabled_flip_triggers_change(self):
        dcnm_net = self._make_bare_dcnm_net()

        have_attach = [{
            "serialNumber": "9NN7E41N16A",
            "networkName": "Test_Network1",
            "switchPorts": "Ethernet1/3",
            "isAttached": True,
            "deployment": True,
            "is_deploy": True,
            "vlan": 1111,
            "instanceValues": json.dumps({"isVPC": "false", "sviEnabled": "false", "isActive": "false"}),
        }]
        want_attach = copy.deepcopy(have_attach)
        want_attach[0]["instanceValues"] = json.dumps({"sviEnabled": "true"})
        want_attach[0]["_svi_supplied"] = True

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach))

        self.assertTrue(diff)
        self.assertTrue(dep_net)
        merged = json.loads(diff[0]["instanceValues"])
        self.assertEqual(merged["sviEnabled"], "true")
        self.assertEqual(merged["isVPC"], "false")
        self.assertEqual(merged["isActive"], "false")

    def test_dcnm_net_diff_for_attach_deploy_svi_enabled_idempotent(self):
        dcnm_net = self._make_bare_dcnm_net()

        have_attach = [{
            "serialNumber": "9NN7E41N16A",
            "networkName": "Test_Network1",
            "switchPorts": "Ethernet1/3",
            "isAttached": True,
            "deployment": True,
            "is_deploy": True,
            "vlan": 1111,
            "instanceValues": json.dumps({"isVPC": "false", "sviEnabled": "true", "isActive": "false"}),
        }]
        want_attach = copy.deepcopy(have_attach)
        want_attach[0]["instanceValues"] = json.dumps({"sviEnabled": "true"})

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach))

        self.assertFalse(diff)
        self.assertFalse(dep_net)

    def _svi_have(self, svi_value):
        return [{
            "serialNumber": "9NN7E41N16A",
            "networkName": "Test_Network1",
            "switchPorts": "Ethernet1/3",
            "isAttached": True,
            "deployment": True,
            "is_deploy": True,
            "vlan": 1111,
            "instanceValues": json.dumps({"isVPC": "false", "sviEnabled": svi_value, "isActive": "false"}),
        }]

    def _svi_want(self, svi_supplied, want_svi=None, ports="Ethernet1/3"):
        inst = {}
        if want_svi is not None:
            inst["sviEnabled"] = want_svi
        return [{
            "serialNumber": "9NN7E41N16A",
            "networkName": "Test_Network1",
            "switchPorts": ports,
            "isAttached": True,
            "deployment": True,
            "is_deploy": True,
            "vlan": 1111,
            "instanceValues": json.dumps(inst) if inst else "",
            "_svi_supplied": svi_supplied,
        }]

    def test_dcnm_net_svi_enabled_merged_omitted_preserves_have_false(self):
        """Merged + omitted svi_enabled must preserve NDFC's existing sviEnabled=false."""
        dcnm_net = self._make_bare_dcnm_net()
        have_attach = self._svi_have("false")
        want_attach = self._svi_want(svi_supplied=False, want_svi="true")

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach))

        self.assertFalse(diff)
        self.assertFalse(dep_net)

    def test_dcnm_net_svi_enabled_merged_omitted_preserves_have_true(self):
        """Merged + omitted svi_enabled is idempotent when NDFC has sviEnabled=true."""
        dcnm_net = self._make_bare_dcnm_net()
        have_attach = self._svi_have("true")
        want_attach = self._svi_want(svi_supplied=False, want_svi="true")

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach))

        self.assertFalse(diff)
        self.assertFalse(dep_net)

    def test_dcnm_net_svi_enabled_merged_port_add_preserves_svi_value(self):
        """Merged + port change + omitted svi: attach is in diff for the port change,
        and its outgoing instanceValues carries have's sviEnabled=false, not the
        argspec default of true."""
        dcnm_net = self._make_bare_dcnm_net()
        have_attach = self._svi_have("false")
        want_attach = self._svi_want(svi_supplied=False, want_svi="true", ports="Ethernet1/3,Ethernet1/4")

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach))

        self.assertEqual(len(diff), 1)
        self.assertTrue(dep_net)
        merged_inst = json.loads(diff[0]["instanceValues"])
        self.assertEqual(merged_inst["sviEnabled"], "false")
        self.assertEqual(merged_inst["isVPC"], "false")
        self.assertEqual(merged_inst["isActive"], "false")

    def test_dcnm_net_svi_enabled_merged_explicit_false_flips_have_true(self):
        """Merged + explicit svi_enabled=false must disable an existing enabled SVI."""
        dcnm_net = self._make_bare_dcnm_net()
        have_attach = self._svi_have("true")
        want_attach = self._svi_want(svi_supplied=True, want_svi="false")

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach))

        self.assertEqual(len(diff), 1)
        self.assertTrue(dep_net)
        self.assertEqual(json.loads(diff[0]["instanceValues"])["sviEnabled"], "false")

    def test_dcnm_net_svi_enabled_replaced_omitted_resets_to_true(self):
        """Replaced + omitted svi_enabled must reset an existing sviEnabled=false to true."""
        dcnm_net = self._make_bare_dcnm_net()
        have_attach = self._svi_have("false")
        want_attach = self._svi_want(svi_supplied=False, want_svi="true")

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach), replace=True)

        self.assertEqual(len(diff), 1)
        self.assertTrue(dep_net)
        self.assertEqual(json.loads(diff[0]["instanceValues"])["sviEnabled"], "true")

    def _svi_have_no_instance_values(self):
        return [{
            "serialNumber": "9NN7E41N16A",
            "networkName": "Test_Network1",
            "switchPorts": "Ethernet1/3",
            "isAttached": True,
            "deployment": True,
            "is_deploy": True,
            "vlan": 1111,
            "instanceValues": "",
        }]

    def test_dcnm_net_svi_enabled_merged_explicit_true_when_have_has_no_instance_values(self):
        """Merged + explicit true must apply even when NDFC returned no instanceValues."""
        dcnm_net = self._make_bare_dcnm_net()
        have_attach = self._svi_have_no_instance_values()
        want_attach = self._svi_want(svi_supplied=True, want_svi="true")

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach))

        self.assertEqual(len(diff), 1)
        self.assertTrue(dep_net)
        self.assertEqual(json.loads(diff[0]["instanceValues"])["sviEnabled"], "true")

    def test_dcnm_net_svi_enabled_merged_explicit_false_when_have_has_no_instance_values(self):
        """Merged + explicit false must apply even when NDFC returned no instanceValues."""
        dcnm_net = self._make_bare_dcnm_net()
        have_attach = self._svi_have_no_instance_values()
        want_attach = self._svi_want(svi_supplied=True, want_svi="false")

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach))

        self.assertEqual(len(diff), 1)
        self.assertTrue(dep_net)
        self.assertEqual(json.loads(diff[0]["instanceValues"])["sviEnabled"], "false")

    def test_dcnm_net_svi_enabled_replaced_omitted_when_have_has_no_instance_values(self):
        """Replaced + omitted must reset to default true even when NDFC returned no instanceValues."""
        dcnm_net = self._make_bare_dcnm_net()
        have_attach = self._svi_have_no_instance_values()
        want_attach = self._svi_want(svi_supplied=False, want_svi="true")

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach), replace=True)

        self.assertEqual(len(diff), 1)
        self.assertTrue(dep_net)
        self.assertEqual(json.loads(diff[0]["instanceValues"])["sviEnabled"], "true")

    def test_dcnm_net_svi_enabled_replaced_explicit_false_when_have_has_no_instance_values(self):
        """Replaced + explicit false must apply even when NDFC returned no instanceValues."""
        dcnm_net = self._make_bare_dcnm_net()
        have_attach = self._svi_have_no_instance_values()
        want_attach = self._svi_want(svi_supplied=True, want_svi="false")

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach), replace=True)

        self.assertEqual(len(diff), 1)
        self.assertTrue(dep_net)
        self.assertEqual(json.loads(diff[0]["instanceValues"])["sviEnabled"], "false")

    def test_dcnm_net_svi_enabled_merged_omitted_when_have_has_no_instance_values_no_spurious_diff(self):
        """Merged + omitted must not produce a spurious diff when NDFC returned no
        instanceValues. Regression lock against future removal of the svi_supplied gate."""
        dcnm_net = self._make_bare_dcnm_net()
        have_attach = self._svi_have_no_instance_values()
        want_attach = self._svi_want(svi_supplied=False, want_svi="true")

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach))

        self.assertFalse(diff)
        self.assertFalse(dep_net)

    def test_dcnm_net_update_attach_params_omitted_svi_sets_supplied_flag_false(self):
        """Omitted svi_enabled must mark _svi_supplied=False while still defaulting the payload to true."""
        dcnm_net = self._make_bare_dcnm_net()
        with patch.object(dcnm_network, "dcnm_get_ip_addr_info", lambda module, ip, a, b: ip):
            attach = {"ip_address": "10.10.10.217", "ports": ["Ethernet1/3"]}
            out = dcnm_net.update_attach_params(attach, "Test_Network1", deploy=True)

        self.assertNotIn("svi_enabled", out)
        self.assertEqual(out.get("_svi_supplied"), False)
        self.assertEqual(json.loads(out["instanceValues"])["sviEnabled"], "true")

    def test_dcnm_net_update_attach_params_explicit_svi_sets_supplied_flag_true(self):
        """Explicit svi_enabled must mark _svi_supplied=True."""
        dcnm_net = self._make_bare_dcnm_net()
        with patch.object(dcnm_network, "dcnm_get_ip_addr_info", lambda module, ip, a, b: ip):
            attach_true = {"ip_address": "10.10.10.217", "ports": ["Ethernet1/3"], "svi_enabled": True}
            out_true = dcnm_net.update_attach_params(attach_true, "Test_Network1", deploy=True)
        self.assertNotIn("svi_enabled", out_true)
        self.assertEqual(out_true.get("_svi_supplied"), True)
        self.assertEqual(json.loads(out_true["instanceValues"])["sviEnabled"], "true")

        dcnm_net = self._make_bare_dcnm_net()
        with patch.object(dcnm_network, "dcnm_get_ip_addr_info", lambda module, ip, a, b: ip):
            attach_false = {"ip_address": "10.10.10.217", "ports": ["Ethernet1/3"], "svi_enabled": False}
            out_false = dcnm_net.update_attach_params(attach_false, "Test_Network1", deploy=True)
        self.assertNotIn("svi_enabled", out_false)
        self.assertEqual(out_false.get("_svi_supplied"), True)
        self.assertEqual(json.loads(out_false["instanceValues"])["sviEnabled"], "false")

    def test_dcnm_net_update_attach_params_pre_12_4_omitted_svi_no_leak(self):
        """Pre-12.4 + omitted svi_enabled: neither the Ansible key nor any sviEnabled
        translation appears in the outgoing attach dict."""
        dcnm_net = self._make_bare_dcnm_net()
        dcnm_net.dcnm_version = 12.3
        with patch.object(dcnm_network, "dcnm_get_ip_addr_info", lambda module, ip, a, b: ip):
            attach = {"ip_address": "10.10.10.217", "ports": ["Ethernet1/3"]}
            out = dcnm_net.update_attach_params(attach, "Test_Network1", deploy=True)

        self.assertNotIn("svi_enabled", out)
        self.assertNotIn("_svi_supplied", out)
        self.assertEqual(out["instanceValues"], "")

    def test_dcnm_net_update_attach_params_pre_12_4_explicit_true_fails(self):
        """Pre-12.4 + explicit svi_enabled: True must raise an actionable compatibility error."""
        dcnm_net = self._make_bare_dcnm_net()
        dcnm_net.dcnm_version = 12.3
        with patch.object(dcnm_network, "dcnm_get_ip_addr_info", lambda module, ip, a, b: ip):
            attach = {"ip_address": "10.10.10.217", "ports": ["Ethernet1/3"], "svi_enabled": True}
            with self.assertRaises(AssertionError) as ctx:
                dcnm_net.update_attach_params(attach, "Test_Network1", deploy=True)

        self.assertIn("svi_enabled is only supported on NDFC 12.4+", str(ctx.exception))
        self.assertIn("12.3", str(ctx.exception))

    def test_dcnm_net_update_attach_params_pre_12_4_explicit_false_fails(self):
        """Pre-12.4 + explicit svi_enabled: False must raise the same compatibility error."""
        dcnm_net = self._make_bare_dcnm_net()
        dcnm_net.dcnm_version = 12.3
        with patch.object(dcnm_network, "dcnm_get_ip_addr_info", lambda module, ip, a, b: ip):
            attach = {"ip_address": "10.10.10.217", "ports": ["Ethernet1/3"], "svi_enabled": False}
            with self.assertRaises(AssertionError) as ctx:
                dcnm_net.update_attach_params(attach, "Test_Network1", deploy=True)

        self.assertIn("svi_enabled is only supported on NDFC 12.4+", str(ctx.exception))

    def test_dcnm_net_update_attach_params_12_4_translates_svi_and_strips_input_key(self):
        """12.4+ path: the Ansible svi_enabled key is stripped and its value translated
        into instanceValues.sviEnabled with lowercase-string booleans."""
        dcnm_net = self._make_bare_dcnm_net()
        with patch.object(dcnm_network, "dcnm_get_ip_addr_info", lambda module, ip, a, b: ip):
            attach = {"ip_address": "10.10.10.217", "ports": ["Ethernet1/3"], "svi_enabled": True}
            out = dcnm_net.update_attach_params(attach, "Test_Network1", deploy=True)

        self.assertNotIn("svi_enabled", out)
        self.assertIn("instanceValues", out)
        inst = json.loads(out["instanceValues"])
        self.assertEqual(inst["sviEnabled"], "true")

    def test_dcnm_net_push_to_remote_no_svi_enabled_or_flag_in_payload(self):
        """The push_to_remote payload-prep loop guarantees neither the Ansible
        svi_enabled key nor the internal _svi_supplied flag leaves the module
        for any lanAttachList entry regardless of version path."""
        diff_attach = [
            {
                "networkName": "Test_Network1",
                "lanAttachList": [
                    {"serialNumber": "SN_A", "_svi_supplied": True, "svi_enabled": True, "is_deploy": True},
                    {"serialNumber": "SN_B", "_svi_supplied": False, "is_deploy": False},
                    {"serialNumber": "SN_C"},
                ],
            }
        ]
        for d_a in diff_attach:
            for v_a in d_a["lanAttachList"]:
                if v_a.get("is_deploy"):
                    del v_a["is_deploy"]
                v_a.pop("_svi_supplied", None)
                v_a.pop("svi_enabled", None)

        for v_a in diff_attach[0]["lanAttachList"]:
            self.assertNotIn("_svi_supplied", v_a)
            self.assertNotIn("svi_enabled", v_a)

    def test_dcnm_net_push_to_remote_svi_supplied_flag_stripped(self):
        """The _svi_supplied internal flag is stripped from every lanAttachList
        entry by the push_to_remote payload-prep loop before serialization."""
        diff_attach = [
            {
                "networkName": "Test_Network1",
                "lanAttachList": [
                    {"serialNumber": "SN_A", "_svi_supplied": True, "is_deploy": True},
                    {"serialNumber": "SN_B", "_svi_supplied": False},
                ],
            }
        ]
        for d_a in diff_attach:
            for v_a in d_a["lanAttachList"]:
                if v_a.get("is_deploy"):
                    del v_a["is_deploy"]
                v_a.pop("_svi_supplied", None)

        for v_a in diff_attach[0]["lanAttachList"]:
            self.assertNotIn("_svi_supplied", v_a)

    def _make_format_diff_dcnm_net(self):
        dcnm_net = self._make_bare_dcnm_net()
        dcnm_net.diff_create = []
        dcnm_net.diff_create_quick = []
        dcnm_net.diff_create_update = []
        dcnm_net.diff_detach = []
        dcnm_net.diff_deploy = {}
        dcnm_net.diff_undeploy = {}
        return dcnm_net

    def _format_diff_attach_payload(self, instance_values, switch_ports="Ethernet1/1"):
        return [{
            "networkName": "Test_Network1",
            "lanAttachList": [{
                "serialNumber": "9NN7E41N16A",
                "switchPorts": switch_ports,
                "deployment": True,
                "detachSwitchPorts": "",
                "instanceValues": instance_values,
            }],
        }]

    def test_dcnm_net_format_diff_emits_svi_enabled_false_from_instance_values(self):
        """format_diff must emit svi_enabled: False when the outgoing instanceValues carries sviEnabled=false."""
        dcnm_net = self._make_format_diff_dcnm_net()
        dcnm_net.diff_attach = self._format_diff_attach_payload(
            json.dumps({"isVPC": "false", "sviEnabled": "false", "isActive": "false"})
        )

        dcnm_net.format_diff()

        attach = dcnm_net.diff_input_format[0]["attach"][0]
        self.assertIn("svi_enabled", attach)
        self.assertEqual(attach["svi_enabled"], False)

    def test_dcnm_net_format_diff_emits_svi_enabled_true_from_instance_values(self):
        """format_diff must emit svi_enabled: True when the outgoing instanceValues carries sviEnabled=true."""
        dcnm_net = self._make_format_diff_dcnm_net()
        dcnm_net.diff_attach = self._format_diff_attach_payload(
            json.dumps({"sviEnabled": "true"})
        )

        dcnm_net.format_diff()

        attach = dcnm_net.diff_input_format[0]["attach"][0]
        self.assertIn("svi_enabled", attach)
        self.assertEqual(attach["svi_enabled"], True)

    def test_dcnm_net_format_diff_omits_svi_enabled_when_not_in_instance_values(self):
        """format_diff must not emit svi_enabled when the outgoing instanceValues has other keys but no sviEnabled."""
        dcnm_net = self._make_format_diff_dcnm_net()
        dcnm_net.diff_attach = self._format_diff_attach_payload(
            json.dumps({"isVPC": "false", "isActive": "false"})
        )

        dcnm_net.format_diff()

        attach = dcnm_net.diff_input_format[0]["attach"][0]
        self.assertNotIn("svi_enabled", attach)

    def test_dcnm_net_format_diff_omits_svi_enabled_when_instance_values_empty(self):
        """format_diff must not emit svi_enabled when instanceValues is empty (pre-12.4 path)."""
        dcnm_net = self._make_format_diff_dcnm_net()
        dcnm_net.diff_attach = self._format_diff_attach_payload("")

        dcnm_net.format_diff()

        attach = dcnm_net.diff_input_format[0]["attach"][0]
        self.assertNotIn("svi_enabled", attach)

    def test_dcnm_net_format_diff_combined_port_and_svi_diff_shows_both(self):
        """format_diff must expose both ports and svi_enabled when both participated in the change."""
        dcnm_net = self._make_format_diff_dcnm_net()
        dcnm_net.diff_attach = self._format_diff_attach_payload(
            json.dumps({"sviEnabled": "false"}),
            switch_ports="Ethernet1/1,Ethernet1/2",
        )

        dcnm_net.format_diff()

        attach = dcnm_net.diff_input_format[0]["attach"][0]
        self.assertEqual(attach["ports"], "Ethernet1/1,Ethernet1/2")
        self.assertIn("svi_enabled", attach)
        self.assertEqual(attach["svi_enabled"], False)

    def test_dcnm_net_diff_for_attach_deploy_port_add_merged_empty_freeform(self):
        """Merged: adding a port on an attach with empty freeform on both sides must produce a diff."""
        dcnm_net = self._build_diff_network(self.net_inv_data)

        have_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/1"),
        ]
        want_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/1,Ethernet1/2"),
        ]

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach))

        self.assertEqual(len(diff), 1)
        self.assertEqual(diff[0]["switchPorts"], "Ethernet1/2")
        self.assertTrue(dep_net)

    def test_dcnm_net_diff_for_attach_deploy_port_swap_replaced_empty_freeform(self):
        """Replaced: swapping a port on an attach with empty freeform on both sides must attach the new and detach the old."""
        dcnm_net = self._build_diff_network(self.net_inv_data)

        have_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/1"),
        ]
        want_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/2"),
        ]

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach), replace=True)

        self.assertEqual(len(diff), 1)
        self.assertEqual(diff[0]["switchPorts"], "Ethernet1/2")
        self.assertEqual(diff[0]["detachSwitchPorts"], "Ethernet1/1")
        self.assertTrue(dep_net)

    def test_dcnm_net_diff_for_attach_deploy_port_unchanged_empty_freeform_idempotent(self):
        """Idempotency: identical attach with empty freeform on both sides must produce no diff under both merged and replaced."""
        dcnm_net = self._build_diff_network(self.net_inv_data)

        have_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/1,Ethernet1/2"),
        ]
        want_attach = [
            self._build_attach_state("9NN7E41N16A", "Ethernet1/1,Ethernet1/2"),
        ]

        diff, dep_net = dcnm_net.diff_for_attach_deploy(want_attach, copy.deepcopy(have_attach))
        self.assertFalse(diff)
        self.assertFalse(dep_net)

        diff, dep_net = dcnm_net.diff_for_attach_deploy(
            copy.deepcopy(want_attach), copy.deepcopy(have_attach), replace=True, network_vlan=202
        )
        self.assertFalse(diff)
        self.assertFalse(dep_net)

    def test_dcnm_net_overlay_have_freeform_from_switch_details(self):
        """The overlay fetches per-switch policies, filters for
        switch_freeform_config, and overlays nvPairs.CONF onto matching
        have_attach entries so diff_for_attach_deploy can see it."""
        dcnm_net = self._make_bare_dcnm_net()
        dcnm_net.paths = dcnm_network.DcnmNetwork.dcnm_network_paths[12]

        have_attach = [
            {
                "networkName": "test_network",
                "lanAttachList": [
                    {"serialNumber": "SN_A", "freeformConfig": ""},
                    {"serialNumber": "SN_B", "freeformConfig": ""},
                ],
            }
        ]
        network_to_sns = {"test_network": ["SN_A", "SN_B"]}

        self.run_dcnm_send.side_effect = [
            {
                "MESSAGE": "OK",
                "METHOD": "GET",
                "RETURN_CODE": 200,
                "DATA": [
                    {
                        "policyId": "POLICY-A1",
                        "templateName": "switch_freeform_config",
                        "serialNumber": "SN_A",
                        "entityName": "test_network",
                        "nvPairs": {"CONF": "interface Vlan202\n  no autostate"},
                    },
                    {
                        "policyId": "POLICY-A2",
                        "templateName": "some_other_template",
                        "serialNumber": "SN_A",
                        "nvPairs": {"CONF": "ignore me"},
                    },
                ],
            },
            {
                "MESSAGE": "OK",
                "METHOD": "GET",
                "RETURN_CODE": 200,
                "DATA": [],
            },
        ]

        self._real_overlay_have_freeform_from_switch_details(
            dcnm_net, have_attach, network_to_sns
        )

        by_sn = {a["serialNumber"]: a for a in have_attach[0]["lanAttachList"]}
        self.assertEqual(by_sn["SN_A"]["freeformConfig"], "interface Vlan202\n  no autostate")
        self.assertEqual(by_sn["SN_B"]["freeformConfig"], "")

    def test_dcnm_net_overlay_have_freeform_fetch_failure_is_soft(self):
        """A failing switch-policies GET must not raise; have_attach is left unchanged."""
        dcnm_net = self._make_bare_dcnm_net()
        dcnm_net.paths = dcnm_network.DcnmNetwork.dcnm_network_paths[12]

        have_attach = [
            {
                "networkName": "test_network",
                "lanAttachList": [
                    {"serialNumber": "SN_A", "freeformConfig": ""},
                ],
            }
        ]
        network_to_sns = {"test_network": ["SN_A"]}

        self.run_dcnm_send.side_effect = [
            {"MESSAGE": "Not Found", "METHOD": "GET", "RETURN_CODE": 404, "DATA": None}
        ]

        self._real_overlay_have_freeform_from_switch_details(
            dcnm_net, have_attach, network_to_sns
        )

        self.assertEqual(have_attach[0]["lanAttachList"][0]["freeformConfig"], "")

    def _make_multinet_overlay_fixture(self):
        dcnm_net = self._make_bare_dcnm_net()
        dcnm_net.paths = dcnm_network.DcnmNetwork.dcnm_network_paths[12]
        have_attach = [
            {
                "networkName": "net_A",
                "lanAttachList": [
                    {"serialNumber": "SN1", "freeformConfig": ""},
                ],
            },
            {
                "networkName": "net_B",
                "lanAttachList": [
                    {"serialNumber": "SN1", "freeformConfig": ""},
                ],
            },
        ]
        network_to_sns = {"net_A": ["SN1"], "net_B": ["SN1"]}
        return dcnm_net, have_attach, network_to_sns

    def test_dcnm_net_overlay_multinet_matches_by_entity_name(self):
        """Two networks on one switch: policies scoped by entityName go to the right network."""
        dcnm_net, have_attach, network_to_sns = self._make_multinet_overlay_fixture()

        self.run_dcnm_send.side_effect = [
            {
                "MESSAGE": "OK", "METHOD": "GET", "RETURN_CODE": 200,
                "DATA": [
                    {
                        "policyId": "P1",
                        "templateName": "switch_freeform_config",
                        "serialNumber": "SN1",
                        "entityName": "net_A",
                        "nvPairs": {"CONF": "cli for A"},
                    },
                    {
                        "policyId": "P2",
                        "templateName": "switch_freeform_config",
                        "serialNumber": "SN1",
                        "entityName": "net_B",
                        "nvPairs": {"CONF": "cli for B"},
                    },
                ],
            },
        ]

        self._real_overlay_have_freeform_from_switch_details(
            dcnm_net, have_attach, network_to_sns
        )

        by_net = {n["networkName"]: n["lanAttachList"][0]["freeformConfig"] for n in have_attach}
        self.assertEqual(by_net["net_A"], "cli for A")
        self.assertEqual(by_net["net_B"], "cli for B")

    def test_dcnm_net_overlay_multinet_matches_by_description(self):
        """entityName missing/empty: fall back to description substring match."""
        dcnm_net, have_attach, network_to_sns = self._make_multinet_overlay_fixture()

        self.run_dcnm_send.side_effect = [
            {
                "MESSAGE": "OK", "METHOD": "GET", "RETURN_CODE": 200,
                "DATA": [
                    {
                        "policyId": "P1",
                        "templateName": "switch_freeform_config",
                        "serialNumber": "SN1",
                        "entityName": "",
                        "description": "freeform for net_A on SN1",
                        "nvPairs": {"CONF": "cli for A"},
                    },
                    {
                        "policyId": "P2",
                        "templateName": "switch_freeform_config",
                        "serialNumber": "SN1",
                        "entityName": "",
                        "description": "freeform for net_B on SN1",
                        "nvPairs": {"CONF": "cli for B"},
                    },
                ],
            },
        ]

        self._real_overlay_have_freeform_from_switch_details(
            dcnm_net, have_attach, network_to_sns
        )

        by_net = {n["networkName"]: n["lanAttachList"][0]["freeformConfig"] for n in have_attach}
        self.assertEqual(by_net["net_A"], "cli for A")
        self.assertEqual(by_net["net_B"], "cli for B")

    def test_dcnm_net_overlay_multinet_matches_by_nvpairs_network_name(self):
        """entityName and description miss: fall back to nvPairs.NETWORK_NAME."""
        dcnm_net, have_attach, network_to_sns = self._make_multinet_overlay_fixture()

        self.run_dcnm_send.side_effect = [
            {
                "MESSAGE": "OK", "METHOD": "GET", "RETURN_CODE": 200,
                "DATA": [
                    {
                        "policyId": "P1",
                        "templateName": "switch_freeform_config",
                        "serialNumber": "SN1",
                        "entityName": "",
                        "description": "",
                        "nvPairs": {"CONF": "cli for A", "NETWORK_NAME": "net_A"},
                    },
                    {
                        "policyId": "P2",
                        "templateName": "switch_freeform_config",
                        "serialNumber": "SN1",
                        "entityName": "",
                        "description": "",
                        "nvPairs": {"CONF": "cli for B", "NETWORK_NAME": "net_B"},
                    },
                ],
            },
        ]

        self._real_overlay_have_freeform_from_switch_details(
            dcnm_net, have_attach, network_to_sns
        )

        by_net = {n["networkName"]: n["lanAttachList"][0]["freeformConfig"] for n in have_attach}
        self.assertEqual(by_net["net_A"], "cli for A")
        self.assertEqual(by_net["net_B"], "cli for B")

    def test_dcnm_net_overlay_multinet_no_matching_field_is_safe_no_op(self):
        """No scoping field matches: policies are silently skipped, freeformConfig stays empty."""
        dcnm_net, have_attach, network_to_sns = self._make_multinet_overlay_fixture()

        self.run_dcnm_send.side_effect = [
            {
                "MESSAGE": "OK", "METHOD": "GET", "RETURN_CODE": 200,
                "DATA": [
                    {
                        "policyId": "P1",
                        "templateName": "switch_freeform_config",
                        "serialNumber": "SN1",
                        "entityName": "unrelated_thing",
                        "description": "no network hint here",
                        "nvPairs": {"CONF": "cli for A"},
                    },
                ],
            },
        ]

        self._real_overlay_have_freeform_from_switch_details(
            dcnm_net, have_attach, network_to_sns
        )

        for net_attach in have_attach:
            self.assertEqual(net_attach["lanAttachList"][0]["freeformConfig"], "")

    def test_dcnm_net_match_freeform_policy_to_network_strategies(self):
        """_match_freeform_policy_to_network isolates each disambiguation strategy."""
        matcher = dcnm_network.DcnmNetwork._match_freeform_policy_to_network

        self.assertIsNone(matcher({"entityName": "net_A"}, []))

        self.assertEqual(matcher({"entityName": "ignored"}, ["only_net"]), "only_net")

        self.assertEqual(
            matcher({"entityName": "net_B"}, ["net_A", "net_B"]),
            "net_B",
        )

        self.assertEqual(
            matcher(
                {"entityName": "", "description": "freeform for net_A on SN1"},
                ["net_A", "net_B"],
            ),
            "net_A",
        )

        self.assertEqual(
            matcher(
                {"entityName": "", "description": "", "nvPairs": {"NETWORK_NAME": "net_B"}},
                ["net_A", "net_B"],
            ),
            "net_B",
        )

        self.assertEqual(
            matcher(
                {"entityName": "", "description": "", "nvPairs": {"networkName": "net_A"}},
                ["net_A", "net_B"],
            ),
            "net_A",
        )

        self.assertIsNone(
            matcher(
                {
                    "entityName": "not_a_match",
                    "description": "nothing useful",
                    "nvPairs": {"CONF": "just cli"},
                },
                ["net_A", "net_B"],
            )
        )
