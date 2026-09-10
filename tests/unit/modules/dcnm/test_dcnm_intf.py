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

import copy
import json
from unittest.mock import Mock, patch

# from units.compat.mock import patch

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface
from .dcnm_module import TestDcnmModule, set_module_args, loadPlaybookData


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

    def build_bulk_payload(self, *payloads):
        data = []

        for payload in payloads:
            if isinstance(payload, dict):
                data.extend(payload.get("DATA") or [])

        return {
            "MESSAGE": "OK",
            "RETURN_CODE": 200,
            "DATA": data,
        }

    def normalize_legacy_bulk_fixture_responses(self):
        """Map legacy positional empty fixtures to authoritative empty GETs.

        Older lifecycle cases supplied arbitrary empty response shapes because
        other policies treated malformed HAVE as absence. The production
        contract is now fail-closed, so those existing tests must represent the
        successful-empty response they intended instead of malformed state.
        """
        effect = self.run_dcnm_send.side_effect
        if effect is None or callable(effect):
            return

        def _next(*args, **kwargs):
            response = next(effect)
            method = args[1] if len(args) > 1 else None
            path = args[2] if len(args) > 2 else ""
            if (
                method == "GET"
                and "interface?serialNumber=FOX1821H035" in path
                and "ifName=" not in path
                and "overridden" in self._testMethodName
            ):
                groups = []
                for payload_name in (
                    "dcnm_intf_vpc_payloads",
                    "dcnm_intf_aa_fex_payloads",
                ):
                    payloads = loadPlaybookData(payload_name)
                    for payload in payloads.values():
                        if isinstance(payload, dict):
                            groups.extend(payload.get("DATA") or [])
                have_all = loadPlaybookData("dcnm_intf_have_all_payloads")
                wanted = {
                    item.get("ifName", "").lower(): item
                    for item in (have_all.get("payloads", {}).get("DATA") or [])
                    if self._dcnm_intf_query_serial_for_test(
                        item.get("serialNo")
                    ) == "FOX1821H035"
                }
                cached_names = {
                    intf.get("ifName", "").lower()
                    for group in groups
                    for intf in (group.get("interfaces") or [])
                }
                for name in sorted(set(wanted) - cached_names):
                    summary = wanted[name]
                    groups.append({
                        "policy": "test_authoritative_policy",
                        "interfaces": [{
                            "ifName": name,
                            "serialNumber": summary["serialNo"],
                            "interfaceType": summary["ifType"],
                            "nvPairs": {},
                        }],
                    })
                return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": groups}
            if self._testMethodName in (
                "test_dcnm_intf_aa_fex_deleted_existing",
                "test_dcnm_intf_aa_fex_overridden_existing",
            ):
                if (
                    method == "GET"
                    and "interface?serialNumber=FOX1821H035" in path
                    and "ifName=" not in path
                ):
                    payload = self.payloads_data.get("aa_fex_merged_payloads_150")
                    return self.build_bulk_payload(payload)
                if method == "GET" and "interface?serialNumber=" in path:
                    return []
            if (
                method == "GET"
                and "/control/policies/switches/" in path
                and "have_get_failure" not in self._testMethodName
            ):
                data = response.get("DATA") if isinstance(response, dict) else None
                if not isinstance(data, list):
                    return {
                        "RETURN_CODE": 200,
                        "MESSAGE": "OK",
                        "DATA": [],
                    }
            is_bulk = (
                method == "GET"
                and "interface?serialNumber=" in path
                and "ifName=" not in path
            )
            if "have_get_failure" in self._testMethodName:
                return response
            if not is_bulk:
                return response
            if response == []:
                return self.build_bulk_payload()
            if isinstance(response, dict) and response.get("RETURN_CODE") == 200:
                data = response.get("DATA")
                if isinstance(data, list) and all(
                    isinstance(group, dict)
                    and isinstance(group.get("policy"), str)
                    and group.get("policy")
                    and isinstance(group.get("interfaces"), list)
                    and group.get("interfaces")
                    for group in data
                ):
                    return response
            return []

        self.run_dcnm_send.side_effect = _next

    @staticmethod
    def _dcnm_intf_query_serial_for_test(serial):
        if not isinstance(serial, str):
            return None
        return serial.split("~", 1)[0]

    def assert_no_mutating_dcnm_calls(self):

        mutating_methods = {"POST", "PUT", "DELETE"}
        self.assertFalse(
            any(
                call.args[1] in mutating_methods
                for call in self.run_dcnm_send.call_args_list
                if len(call.args) > 1
            )
        )
        # dcnm_get_bulk_api_support() sends its own POST through the module_utils
        # dcnm_send, which the mock above cannot observe. Reaching it at all
        # means a POST left the module, so assert it was never called.
        self.assertEqual(
            self.run_dcnm_bulk_api_support.call_count,
            0,
            "dcnm_get_bulk_api_support() was called; it issues a POST to the controller",
        )

    @staticmethod
    def storm_control_default_nvpairs():
        return {
            "ENABLE_STORM_CONTROL": False,
            "STORM_CONTROL_ACTION": "no",
            "STORM_CONTROL_BCAST_LEVEL_PERCENT": "",
            "STORM_CONTROL_BCAST_LEVEL_PPS": "",
            "STORM_CONTROL_MCAST_LEVEL_PERCENT": "",
            "STORM_CONTROL_MCAST_LEVEL_PPS": "",
            "STORM_CONTROL_UCAST_LEVEL_PERCENT": "",
            "STORM_CONTROL_UCAST_LEVEL_PPS": "",
        }

    def assert_leaf_default_storm_control(self, payloads):
        trunk_defaults = [
            payload
            for payload in payloads
            if payload["policy"] in ("int_trunk_host", "int_trunk_host_11_1")
        ]
        self.assertTrue(
            trunk_defaults,
            [payload["policy"] for payload in payloads],
        )
        expected = self.storm_control_default_nvpairs()
        for payload in trunk_defaults:
            nv_pairs = payload["interfaces"][0]["nvPairs"]
            self.assertEqual(
                {key: nv_pairs.get(key) for key in expected},
                expected,
            )

    def test_dcnm_intf_is_vpc_peer_link_port_channel_null_alias_template(self):

        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        intf = {
            "ifType": "INTERFACE_PORT_CHANNEL",
            "alias": None,
            "underlayPolicies": [
                {
                    "templateName": "int_vpc_peer_link_po",
                }
            ],
        }

        self.assertEqual(
            dcnm_intf.dcnm_intf_is_vpc_peer_link_port_channel(intf),
            True,
        )

    def test_dcnm_intf_is_vpc_peer_link_port_channel_alias(self):

        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        intf = {
            "ifType": "INTERFACE_PORT_CHANNEL",
            "alias": "vpc-peer-link leaf1--leaf2",
            "underlayPolicies": [],
        }

        self.assertEqual(
            dcnm_intf.dcnm_intf_is_vpc_peer_link_port_channel(intf),
            True,
        )

    def test_dcnm_intf_is_vpc_peer_link_port_channel_regular_pc(self):

        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        intf = {
            "ifType": "INTERFACE_PORT_CHANNEL",
            "alias": None,
            "underlayPolicies": [
                {
                    "templateName": "int_port_channel_trunk",
                }
            ],
        }

        self.assertEqual(
            dcnm_intf.dcnm_intf_is_vpc_peer_link_port_channel(intf),
            False,
        )

    def test_dcnm_intf_is_vpc_peer_link_port_channel_none_policies(self):

        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        intf = {
            "ifType": "INTERFACE_PORT_CHANNEL",
            "alias": None,
            "underlayPolicies": None,
        }

        self.assertEqual(
            dcnm_intf.dcnm_intf_is_vpc_peer_link_port_channel(intf),
            False,
        )

    def test_dcnm_intf_is_vpc_peer_link_port_channel_none_policy_item(self):

        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        intf = {
            "ifType": "INTERFACE_PORT_CHANNEL",
            "alias": None,
            "underlayPolicies": [
                None,
                {
                    "templateName": "int_vpc_peer_link_po",
                },
            ],
        }

        self.assertEqual(
            dcnm_intf.dcnm_intf_is_vpc_peer_link_port_channel(intf),
            True,
        )

    def test_dcnm_intf_storm_control_percent_payload(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        nv_pairs = {}
        profile = {
            "enable_storm_control": True,
            "storm_control_action": "shutdown",
            "storm_control_broadcast_level_percent": "12",
            "storm_control_multicast_level_percent": "13.00",
            "storm_control_unicast_level_percent": "14.5",
        }

        dcnm_intf.dcnm_intf_set_storm_control_nv_pairs(profile, nv_pairs)

        self.assertEqual(
            nv_pairs,
            {
                "ENABLE_STORM_CONTROL": True,
                "STORM_CONTROL_ACTION": "shutdown",
                "STORM_CONTROL_BCAST_LEVEL_PERCENT": "12",
                "STORM_CONTROL_BCAST_LEVEL_PPS": "",
                "STORM_CONTROL_MCAST_LEVEL_PERCENT": "13.00",
                "STORM_CONTROL_MCAST_LEVEL_PPS": "",
                "STORM_CONTROL_UCAST_LEVEL_PERCENT": "14.5",
                "STORM_CONTROL_UCAST_LEVEL_PPS": "",
            },
        )

    def test_dcnm_intf_storm_control_pps_payload(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        nv_pairs = {}
        profile = {
            "enable_storm_control": True,
            "storm_control_action": "trap",
            "storm_control_broadcast_level_pps": 1000,
            "storm_control_multicast_level_pps": 2000,
            "storm_control_unicast_level_pps": 3000,
        }

        dcnm_intf.dcnm_intf_set_storm_control_nv_pairs(profile, nv_pairs)

        self.assertEqual(nv_pairs["STORM_CONTROL_ACTION"], "trap")
        self.assertEqual(nv_pairs["STORM_CONTROL_BCAST_LEVEL_PPS"], "1000")
        self.assertEqual(nv_pairs["STORM_CONTROL_MCAST_LEVEL_PPS"], "2000")
        self.assertEqual(nv_pairs["STORM_CONTROL_UCAST_LEVEL_PPS"], "3000")
        self.assertEqual(nv_pairs["STORM_CONTROL_BCAST_LEVEL_PERCENT"], "")

    def test_dcnm_intf_storm_control_disable_clears_dependent_values(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        profile = {
            "enable_storm_control": False,
            "storm_control_action": "shutdown",
            "storm_control_broadcast_level_percent": "12",
        }
        nv_pairs = {}

        dcnm_intf.dcnm_intf_expand_storm_control_intent(profile)
        dcnm_intf.dcnm_intf_set_storm_control_nv_pairs(profile, nv_pairs)

        self.assertEqual(profile["storm_control_action"], "default")
        self.assertEqual(nv_pairs["ENABLE_STORM_CONTROL"], False)
        self.assertEqual(nv_pairs["STORM_CONTROL_ACTION"], "no")
        for key, value in nv_pairs.items():
            if key.startswith("STORM_CONTROL_") and key != "STORM_CONTROL_ACTION":
                self.assertEqual(value, "")

    def test_dcnm_intf_storm_control_all_false_aliases_clear_values(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        false_aliases = (
            False,
            0,
            0.0,
            "false",
            "no",
            "off",
            "0",
            "n",
            "f",
        )

        for enabled in false_aliases:
            with self.subTest(enabled=enabled):
                profile = {
                    "enable_storm_control": enabled,
                    "storm_control_action": "trap",
                    "storm_control_broadcast_level_percent": "12.00",
                    "storm_control_multicast_level_pps": 2000,
                }

                dcnm_intf.dcnm_intf_expand_storm_control_intent(profile)

                self.assertEqual(profile["storm_control_action"], "default")
                for percent_key, pps_key, _percent_nvpair, _pps_nvpair in (
                    dcnm_intf.storm_control_level_pairs
                ):
                    self.assertEqual(profile[percent_key], "")
                    self.assertIsNone(profile[pps_key])

    def test_dcnm_intf_storm_control_true_aliases_do_not_disable(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        true_aliases = (
            True,
            1,
            1.0,
            "true",
            "yes",
            "on",
            "1",
            "y",
            "t",
        )

        for enabled in true_aliases:
            with self.subTest(enabled=enabled):
                profile = {"enable_storm_control": enabled}

                dcnm_intf.dcnm_intf_expand_storm_control_intent(profile)

                self.assertEqual(
                    profile,
                    {"enable_storm_control": enabled},
                )

    def test_dcnm_intf_storm_control_invalid_bool_uses_normal_validation(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        profile = {
            "enable_storm_control": "not-a-boolean",
            "storm_control_action": "trap",
        }

        dcnm_intf.dcnm_intf_expand_storm_control_intent(profile)

        self.assertEqual(
            profile,
            {
                "enable_storm_control": "not-a-boolean",
                "storm_control_action": "trap",
            },
        )

    def test_dcnm_intf_leaf_default_payload_clears_storm_control(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        dcnm_intf.dcnm_version = 12
        dcnm_intf.ndfc_version = "12.4.1.245"
        dcnm_intf.pol_types = {
            12: {
                "eth_trunk": "int_trunk_host",
                "eth_routed": "int_routed_host",
            }
        }
        dcnm_intf.sno_to_switch_role = {
            "LEAF_SERIAL": "leaf",
            "SPINE_SERIAL": "spine",
        }

        leaf_payload = dcnm_intf.dcnm_intf_get_default_eth_payload(
            "Ethernet1/50",
            "LEAF_SERIAL",
            "test_fabric",
        )
        leaf_nv_pairs = leaf_payload["interfaces"][0]["nvPairs"]
        expected = self.storm_control_default_nvpairs()

        self.assertEqual(
            {key: leaf_nv_pairs.get(key) for key in expected},
            expected,
        )

        routed_payload = dcnm_intf.dcnm_intf_get_default_eth_payload(
            "Ethernet1/50",
            "SPINE_SERIAL",
            "test_fabric",
        )
        routed_nv_pairs = routed_payload["interfaces"][0]["nvPairs"]
        for key in expected:
            self.assertNotIn(key, routed_nv_pairs)

        self.assertEqual(leaf_nv_pairs["FEC"], "auto")
        self.assertEqual(routed_nv_pairs["FEC"], "auto")

    def test_dcnm_intf_default_compare_detects_storm_only_drift(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        dcnm_intf.dcnm_version = 12
        dcnm_intf.ndfc_version = "12.4.1.245"
        dcnm_intf.pol_types = {
            12: {
                "eth_trunk": "int_trunk_host",
                "eth_routed": "int_routed_host",
            }
        }
        dcnm_intf.sno_to_switch_role = {"LEAF_SERIAL": "leaf"}
        default_payload = dcnm_intf.dcnm_intf_get_default_eth_payload(
            "Ethernet1/50",
            "LEAF_SERIAL",
            "test_fabric",
        )
        have = copy.deepcopy(default_payload)
        have["interfaces"][0]["nvPairs"].update(
            {
                "ENABLE_STORM_CONTROL": True,
                "STORM_CONTROL_ACTION": "trap",
                "STORM_CONTROL_BCAST_LEVEL_PPS": "2100",
            }
        )

        self.assertEqual(
            dcnm_intf.dcnm_compare_default_payload(default_payload, have),
            "DCNM_INTF_NOT_MATCH",
        )

    def test_dcnm_intf_default_compare_detects_fec_only_drift(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        dcnm_intf.dcnm_version = 12
        dcnm_intf.ndfc_version = "12.4.1.245"
        dcnm_intf.pol_types = {
            12: {
                "eth_trunk": "int_trunk_host",
                "eth_routed": "int_routed_host",
            }
        }
        dcnm_intf.sno_to_switch_role = {
            "LEAF_SERIAL": "leaf",
            "SPINE_SERIAL": "spine",
        }

        for serial in ("LEAF_SERIAL", "SPINE_SERIAL"):
            with self.subTest(serial=serial):
                default_payload = dcnm_intf.dcnm_intf_get_default_eth_payload(
                    "Ethernet1/50",
                    serial,
                    "test_fabric",
                )
                have = copy.deepcopy(default_payload)
                have["interfaces"][0]["nvPairs"]["FEC"] = "rs-fec"

                self.assertEqual(
                    dcnm_intf.dcnm_compare_default_payload(
                        default_payload, have
                    ),
                    "DCNM_INTF_NOT_MATCH",
                )

    def test_dcnm_intf_default_compare_treats_omitted_fec_as_auto(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        dcnm_intf.dcnm_version = 12
        dcnm_intf.ndfc_version = "12.4.1.245"
        dcnm_intf.pol_types = {
            12: {
                "eth_trunk": "int_trunk_host",
                "eth_routed": "int_routed_host",
            }
        }
        dcnm_intf.sno_to_switch_role = {"LEAF_SERIAL": "leaf"}
        default_payload = dcnm_intf.dcnm_intf_get_default_eth_payload(
            "Ethernet1/50",
            "LEAF_SERIAL",
            "test_fabric",
        )
        have = copy.deepcopy(default_payload)
        have["interfaces"][0]["nvPairs"].pop("FEC")

        self.assertEqual(
            dcnm_intf.dcnm_compare_default_payload(default_payload, have),
            "DCNM_INTF_MATCH",
        )

    def test_dcnm_intf_default_compare_normalizes_omitted_storm_defaults(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        dcnm_intf.dcnm_version = 12
        dcnm_intf.pol_types = {
            12: {
                "eth_trunk": "int_trunk_host",
                "eth_routed": "int_routed_host",
            }
        }
        dcnm_intf.sno_to_switch_role = {"LEAF_SERIAL": "leaf"}
        default_payload = dcnm_intf.dcnm_intf_get_default_eth_payload(
            "Ethernet1/50",
            "LEAF_SERIAL",
            "test_fabric",
        )
        have = copy.deepcopy(default_payload)
        have_nv_pairs = have["interfaces"][0]["nvPairs"]
        for key in self.storm_control_default_nvpairs():
            have_nv_pairs.pop(key)

        self.assertEqual(
            dcnm_intf.dcnm_compare_default_payload(default_payload, have),
            "DCNM_INTF_MATCH",
        )

        have_nv_pairs.update(
            {
                "ENABLE_STORM_CONTROL": "n",
                "STORM_CONTROL_ACTION": "default",
                "STORM_CONTROL_BCAST_LEVEL_PERCENT": None,
            }
        )
        self.assertEqual(
            dcnm_intf.dcnm_compare_default_payload(default_payload, have),
            "DCNM_INTF_MATCH",
        )

    def test_dcnm_intf_merged_percent_transition_clears_all_pps_fields(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        profile = {
            "ifname": "Ethernet1/15",
            "sno": "SERIAL1",
            "fabric": "fabric1",
            "enable_storm_control": True,
            "storm_control_broadcast_level_percent": "12.00",
        }

        dcnm_intf.dcnm_intf_expand_storm_control_intent(profile)
        dcnm_intf.pb_input = [profile]
        dcnm_intf.keymap = {
            pps_nvpair: pps_key
            for _percent_key, pps_key, _percent_nvpair, pps_nvpair
            in dcnm_intf.storm_control_level_pairs
        }

        for _percent_key, pps_key, _percent_nvpair, pps_nvpair in (
            dcnm_intf.storm_control_level_pairs
        ):
            with self.subTest(pps_key=pps_key):
                self.assertIn(pps_key, profile)
                self.assertIsNone(profile[pps_key])
                result = dcnm_intf.dcnm_intf_compare_elements(
                    profile["ifname"],
                    profile["sno"],
                    profile["fabric"],
                    profile[pps_key],
                    1000,
                    pps_nvpair,
                    "merged",
                )
                self.assertEqual(result, "add")

        self.assertNotIn("storm_control_multicast_level_percent", profile)
        self.assertNotIn("storm_control_unicast_level_percent", profile)

    def test_dcnm_intf_merged_pps_transition_clears_all_percent_fields(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        profile = {
            "ifname": "Ethernet1/15",
            "sno": "SERIAL1",
            "fabric": "fabric1",
            "enable_storm_control": True,
            "storm_control_multicast_level_pps": 2000,
        }

        dcnm_intf.dcnm_intf_expand_storm_control_intent(profile)
        dcnm_intf.pb_input = [profile]
        dcnm_intf.keymap = {
            percent_nvpair: percent_key
            for percent_key, _pps_key, percent_nvpair, _pps_nvpair
            in dcnm_intf.storm_control_level_pairs
        }

        for percent_key, _pps_key, percent_nvpair, _pps_nvpair in (
            dcnm_intf.storm_control_level_pairs
        ):
            with self.subTest(percent_key=percent_key):
                self.assertIn(percent_key, profile)
                self.assertEqual(profile[percent_key], "")
                result = dcnm_intf.dcnm_intf_compare_elements(
                    profile["ifname"],
                    profile["sno"],
                    profile["fabric"],
                    profile[percent_key],
                    "10.00",
                    percent_nvpair,
                    "merged",
                )
                self.assertEqual(result, "add")

        self.assertNotIn("storm_control_broadcast_level_pps", profile)
        self.assertNotIn("storm_control_unicast_level_pps", profile)

    def test_dcnm_intf_storm_control_default_action_uses_controller_no(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        nv_pairs = {}
        profile = {
            "enable_storm_control": True,
            "storm_control_action": "default",
        }

        dcnm_intf.dcnm_intf_set_storm_control_nv_pairs(profile, nv_pairs)

        self.assertEqual(nv_pairs["STORM_CONTROL_ACTION"], "no")
        result = dcnm_intf.dcnm_intf_compare_elements(
            "Ethernet1/15",
            "SERIAL1",
            "fabric1",
            "no",
            "default",
            "STORM_CONTROL_ACTION",
            "replaced",
        )
        self.assertEqual(result, "dont_add")

    def test_dcnm_intf_storm_control_invalid_action_lists_choices(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        dcnm_intf.module = Mock()
        dcnm_intf.intf_info = []

        def fail_json(**kwargs):
            raise ValueError(kwargs["msg"])

        dcnm_intf.module.fail_json.side_effect = fail_json
        config = [
            {
                "name": "Ethernet1/15",
                "switch": ["10.122.84.181"],
                "type": "eth",
                "profile": {
                    "storm_control_action": "no",
                },
            }
        ]
        common_spec = {
            "name": {"required": True, "type": "str"},
            "switch": {"required": True, "type": "list"},
            "type": {"required": True, "type": "str"},
            "profile": {"required": True, "type": "dict"},
        }

        with self.assertRaisesRegex(
            ValueError,
            r"Valid choices are: shutdown, trap, default",
        ):
            dcnm_intf.dcnm_intf_validate_interface_input(
                config,
                common_spec,
                dcnm_intf.dcnm_intf_storm_control_spec(),
            )

    def test_dcnm_intf_storm_control_percent_and_pps_are_mutually_exclusive(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        dcnm_intf.module = Mock()

        def fail_json(**kwargs):
            raise ValueError(kwargs["msg"])

        dcnm_intf.module.fail_json.side_effect = fail_json
        percent_keys = [
            "storm_control_broadcast_level_percent",
            "storm_control_multicast_level_percent",
            "storm_control_unicast_level_percent",
        ]
        pps_keys = [
            "storm_control_broadcast_level_pps",
            "storm_control_multicast_level_pps",
            "storm_control_unicast_level_pps",
        ]

        for percent_key in percent_keys:
            for pps_key in pps_keys:
                with self.subTest(percent_key=percent_key, pps_key=pps_key):
                    profile = {
                        "enable_storm_control": True,
                        "storm_control_action": "shutdown",
                        percent_key: "12",
                        pps_key: 1000,
                    }

                    with self.assertRaisesRegex(
                        ValueError,
                        "configure only one rate mode per interface",
                    ):
                        dcnm_intf.dcnm_intf_validate_storm_control_profile(
                            profile, "Ethernet1/15"
                        )

    def test_dcnm_intf_storm_control_percent_comparison_normalizes_precision(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)

        result = dcnm_intf.dcnm_intf_compare_elements(
            "Ethernet1/15",
            "SERIAL1",
            "fabric1",
            "12",
            "12.00",
            "STORM_CONTROL_BCAST_LEVEL_PERCENT",
            "replaced",
        )

        self.assertEqual(result, "dont_add")

    def test_dcnm_intf_copy_description_comparison(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        dcnm_intf.keymap = {"COPY_DESC": "copy_description"}
        dcnm_intf.pb_input = [
            {
                "ifname": "Port-channel511",
                "sno": "SERIAL1",
                "fabric": "fabric1",
            }
        ]

        result = dcnm_intf.dcnm_intf_compare_elements(
            "Port-channel511",
            "SERIAL1",
            "fabric1",
            False,
            "true",
            "COPY_DESC",
            "merged",
        )
        self.assertEqual(result, "copy_and_add")

        dcnm_intf.pb_input[0]["copy_description"] = False
        result = dcnm_intf.dcnm_intf_compare_elements(
            "Port-channel511",
            "SERIAL1",
            "fabric1",
            False,
            "true",
            "COPY_DESC",
            "merged",
        )
        self.assertEqual(result, "add")

        result = dcnm_intf.dcnm_intf_compare_elements(
            "Port-channel511",
            "SERIAL1",
            "fabric1",
            True,
            "true",
            "COPY_DESC",
            "replaced",
        )
        self.assertEqual(result, "dont_add")

    def _build_intf_skeleton(self, interface_type):
        return {
            "deploy": True,
            "policy": "",
            "interfaceType": interface_type,
            "interfaces": [
                {
                    "serialNumber": "",
                    "interfaceType": interface_type,
                    "ifName": "",
                    "fabricName": "test_fabric",
                    "nvPairs": {"SPEED": "Auto"},
                }
            ],
        }

    def _build_eth_dot1q_delem(self, enable_cdp):
        return {
            "name": "eth1/4",
            "type": "eth",
            "switch": ["10.1.1.1"],
            "deploy": True,
            "profile": {
                "mode": "dot1q",
                "bpdu_guard": "true",
                "port_type_fast": True,
                "mtu": "jumbo",
                "speed": "Auto",
                "access_vlan": "10",
                "cmds": None,
                "description": "test",
                "admin_state": True,
                "enable_cdp": enable_cdp,
                "duplex": "auto",
            },
        }

    def _build_eth_trunk_delem(self, fec):
        return {
            "name": "eth1/4",
            "type": "eth",
            "switch": ["10.1.1.1"],
            "deploy": True,
            "profile": {
                "mode": "trunk",
                "bpdu_guard": "true",
                "port_type_fast": True,
                "mtu": "jumbo",
                "speed": "Auto",
                "allowed_vlans": "all",
                "native_vlan": "",
                "orphan_port": False,
                "cmds": None,
                "description": "test",
                "admin_state": True,
                "enable_cdp": True,
                "enable_pfc": False,
                "enable_monitor": False,
                "duplex": "auto",
                "enable_qos": False,
                "qos_policy": "",
                "queuing_policy": "",
                "fec": fec,
            },
        }

    def _build_vpc_delem(self, mode, enable_cdp):
        profile = {
            "mode": mode,
            "peer1_pcid": 10,
            "peer2_pcid": 10,
            "peer1_members": ["eth1/1"],
            "peer2_members": ["eth1/1"],
            "pc_mode": "active",
            "bpdu_guard": "true",
            "port_type_fast": True,
            "mtu": "jumbo",
            "speed": "Auto",
            "peer1_cmds": None,
            "peer2_cmds": None,
            "peer1_description": "",
            "peer2_description": "",
            "admin_state": True,
            "enable_qos": False,
            "qos_policy": "",
            "queuing_policy": "",
            "copy_description": False,
            "enable_cdp": enable_cdp,
        }
        if mode == "trunk":
            profile.update({
                "peer1_allowed_vlans": "none",
                "peer2_allowed_vlans": "none",
                "peer1_native_vlan": "",
                "peer2_native_vlan": "",
                "disable_lacp_suspend_individual": False,
                "enable_lacp_vpc_convergence": False,
                "lacp_port_priority": 32768,
                "lacp_rate": "normal",
            })
        else:
            profile.update({
                "peer1_access_vlan": "10",
                "peer2_access_vlan": "10",
            })
        return {
            "name": "vpc10",
            "type": "vpc",
            "switch": ["10.1.1.1"],
            "deploy": True,
            "profile": profile,
        }

    def test_dcnm_intf_eth_dot1q_payload_disables_cdp(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        delem = self._build_eth_dot1q_delem(enable_cdp=False)
        intf = self._build_intf_skeleton("INTERFACE_ETHERNET")

        dcnm_intf.dcnm_intf_get_eth_payload(delem, intf, "profile")

        self.assertEqual(intf["interfaces"][0]["ifName"], "Ethernet1/4")
        self.assertIn("CDP_ENABLE", intf["interfaces"][0]["nvPairs"])
        self.assertEqual(
            intf["interfaces"][0]["nvPairs"]["CDP_ENABLE"], False
        )

    def test_dcnm_intf_eth_dot1q_payload_enables_cdp(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        delem = self._build_eth_dot1q_delem(enable_cdp=True)
        intf = self._build_intf_skeleton("INTERFACE_ETHERNET")

        dcnm_intf.dcnm_intf_get_eth_payload(delem, intf, "profile")

        self.assertEqual(
            intf["interfaces"][0]["nvPairs"]["CDP_ENABLE"], True
        )

    def test_dcnm_intf_eth_payload_serializes_requested_fec(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        dcnm_intf.ndfc_version = "12.4.1.245"
        delem = self._build_eth_trunk_delem("rs-fec")
        intf = self._build_intf_skeleton("INTERFACE_ETHERNET")

        dcnm_intf.dcnm_intf_get_eth_payload(delem, intf, "profile")

        self.assertEqual(
            intf["interfaces"][0]["nvPairs"]["FEC"], "rs-fec"
        )

    def test_dcnm_intf_fec_version_validation(self):
        cases = (
            (None, True, "version could not be determined"),
            ("12.3.1", True, "requires NDFC >= 12.4.1"),
            ("12.4.1", False, None),
            ("12.4.1.245", False, None),
        )

        for version, should_fail, expected_message in cases:
            with self.subTest(version=version):
                dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
                dcnm_intf.ndfc_version = version
                dcnm_intf.module = Mock()
                dcnm_intf.module.fail_json.side_effect = RuntimeError(
                    "fail_json"
                )
                dcnm_intf.dcnm_intf_validate_interface_input = Mock()
                config = [self._build_eth_trunk_delem("rs-fec")]

                if should_fail:
                    with self.assertRaisesRegex(
                        RuntimeError, "fail_json"
                    ):
                        dcnm_intf.dcnm_intf_validate_ethernet_interface_input(
                            config
                        )
                    self.assertIn(
                        expected_message,
                        dcnm_intf.module.fail_json.call_args.kwargs["msg"],
                    )
                else:
                    dcnm_intf.dcnm_intf_validate_ethernet_interface_input(
                        config
                    )
                    dcnm_intf.module.fail_json.assert_not_called()

    def test_dcnm_intf_vpc_trunk_payload_disables_cdp(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        dcnm_intf.vpc_ip_sn = {}
        dcnm_intf.ip_sn = {"10.1.1.1": "TESTSN1"}
        delem = self._build_vpc_delem(mode="trunk", enable_cdp=False)
        intf = self._build_intf_skeleton("INTERFACE_VPC")

        dcnm_intf.dcnm_intf_get_vpc_payload(delem, intf, "profile")

        self.assertEqual(intf["interfaces"][0]["ifName"], "vPC10")
        self.assertIn("CDP_ENABLE", intf["interfaces"][0]["nvPairs"])
        self.assertEqual(
            intf["interfaces"][0]["nvPairs"]["CDP_ENABLE"], False
        )

    def test_dcnm_intf_vpc_trunk_payload_enables_cdp(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        dcnm_intf.vpc_ip_sn = {}
        dcnm_intf.ip_sn = {"10.1.1.1": "TESTSN1"}
        delem = self._build_vpc_delem(mode="trunk", enable_cdp=True)
        intf = self._build_intf_skeleton("INTERFACE_VPC")

        dcnm_intf.dcnm_intf_get_vpc_payload(delem, intf, "profile")

        self.assertEqual(
            intf["interfaces"][0]["nvPairs"]["CDP_ENABLE"], True
        )

    def test_dcnm_intf_vpc_access_payload_disables_cdp(self):
        dcnm_intf = object.__new__(dcnm_interface.DcnmIntf)
        dcnm_intf.vpc_ip_sn = {}
        dcnm_intf.ip_sn = {"10.1.1.1": "TESTSN1"}
        delem = self._build_vpc_delem(mode="access", enable_cdp=False)
        intf = self._build_intf_skeleton("INTERFACE_VPC")

        dcnm_intf.dcnm_intf_get_vpc_payload(delem, intf, "profile")

        self.assertIn("CDP_ENABLE", intf["interfaces"][0]["nvPairs"])
        self.assertEqual(
            intf["interfaces"][0]["nvPairs"]["CDP_ENABLE"], False
        )

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

        # Named-template metadata lookup used by the fabric-loopback OSPF
        # message-digest capability probe. It has its own mock so it never
        # consumes entries from run_dcnm_send.side_effect. The default return
        # value means "metadata unavailable", which is exactly the legacy
        # behaviour: the unknown nvPair is not sent at all.
        self.mock_dcnm_template_details = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface.dcnm_get_template_details"
        )
        self.run_dcnm_template_details = self.mock_dcnm_template_details.start()
        self.run_dcnm_template_details.return_value = None

        # dcnm_get_bulk_api_support() issues a POST to the controller. Mock it so
        # tests can assert it is NOT reached on read-only and
        # fail-before-mutation paths; the module-local dcnm_send mock cannot see
        # that POST, because the helper calls its own module_utils dcnm_send.
        self.mock_dcnm_bulk_api_support = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface.dcnm_get_bulk_api_support"
        )
        self.run_dcnm_bulk_api_support = self.mock_dcnm_bulk_api_support.start()
        self.run_dcnm_bulk_api_support.return_value = False

    def tearDown(self):

        super(TestDcnmIntfModule, self).tearDown()
        self.mock_dcnm_bulk_api_support.stop()
        self.mock_dcnm_template_details.stop()
        self.mock_dcnm_send.stop()
        self.mock_dcnm_version_supported.stop()
        self.mock_dcnm_ip_sn.stop()
        self.mock_dcnm_fabric_details.stop()

    # -------------------------- GEN-FIXTURES --------------------------

    def load_general_intf_fixtures(self):

        if (
            "test_dcnm_intf_override_pc_intf_types_only"
            in self._testMethodName
        ):

            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            # Load breakout policies fixture
            self.breakout_policies_data = loadPlaybookData("dcnm_intf_breakout_policies")
            empty_breakout_resp = self.breakout_policies_data.get("empty_breakout_policies")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                empty_breakout_resp,
                empty_breakout_resp,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if (
            "test_dcnm_intf_override_pc_intf_types_with_new_config"
            in self._testMethodName
        ):

            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            # Load breakout policies fixture
            self.breakout_policies_data = loadPlaybookData("dcnm_intf_breakout_policies")
            empty_breakout_resp = self.breakout_policies_data.get("empty_breakout_policies")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                [],
                empty_breakout_resp,
                empty_breakout_resp,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if (
            "test_dcnm_intf_override_all_but_eth_intf_types_only"
            in self._testMethodName
        ):

            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if (
            "test_dcnm_intf_override_svi_intf_types_only"
            in self._testMethodName
        ):

            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            # Load breakout policies fixture
            self.breakout_policies_data = loadPlaybookData("dcnm_intf_breakout_policies")
            empty_breakout_resp = self.breakout_policies_data.get("empty_breakout_policies")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                empty_breakout_resp,
                empty_breakout_resp,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if (
            "test_dcnm_intf_override_vpc_intf_types_only"
            in self._testMethodName
        ):

            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            # Load breakout policies fixture
            self.breakout_policies_data = loadPlaybookData("dcnm_intf_breakout_policies")
            empty_breakout_resp = self.breakout_policies_data.get("empty_breakout_policies")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                empty_breakout_resp,
                empty_breakout_resp,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if (
            "test_dcnm_intf_override_eth_intf_types_skip_non_resolvable_deferred"
            in self._testMethodName
        ):

            playbook_have_all_data = copy.deepcopy(
                self.have_all_payloads_data.get("payloads")
            )
            for intf in playbook_have_all_data["DATA"]:
                if intf["ifName"] == "Ethernet1/1":
                    intf["deletable"] = "False"
                    intf["editAllowed"] = True
                    intf["underlayPolicies"] = None
                    break

            eth_1_2_access_intf = self.have_all_payloads_data.get(
                "eth_1_2_access_payload"
            )
            eth_3_2_access_intf = self.have_all_payloads_data.get(
                "eth_3_2_access_payload"
            )
            eth_bulk_payload = self.build_bulk_payload(
                eth_1_2_access_intf,
                eth_3_2_access_intf,
            )
            eth_vpc_empty_payload = self.build_bulk_payload()
            self.breakout_policies_data = loadPlaybookData(
                "dcnm_intf_breakout_policies"
            )
            empty_breakout_resp = self.breakout_policies_data.get(
                "empty_breakout_policies"
            )

            def dcnm_send_side_effect(*args, **kwargs):
                path = args[2]

                if path.endswith("/accessmode"):
                    return self.mock_monitor_false_resp
                if "/control/policies/switches/" in path:
                    return empty_breakout_resp
                if "interface/detail?serialNumber=" in path:
                    return playbook_have_all_data
                if (
                    "interface?serialNumber=SAL1819SAN8" in path
                    and "ifName=" not in path
                ):
                    return eth_bulk_payload
                if (
                    "interface?serialNumber=" in path
                    and "ifName=" not in path
                ):
                    return eth_vpc_empty_payload
                if (
                    "interface?serialNumber=" in path
                    and "ifName=Ethernet1/1" in path
                ):
                    raise AssertionError(
                        "Skipped deferred interface should not be queried again"
                    )
                if (
                    "interface?serialNumber=" in path
                    and "ifName=Ethernet1/2" in path
                ):
                    return eth_1_2_access_intf
                if (
                    "interface?serialNumber=" in path
                    and "ifName=Ethernet3/2" in path
                ):
                    return eth_3_2_access_intf
                return self.playbook_mock_succ_resp

            self.run_dcnm_send.side_effect = dcnm_send_side_effect

        if (
            "test_dcnm_intf_override_eth_intf_types_only"
            in self._testMethodName
        ):

            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            eth_1_1_access_intf = self.have_all_payloads_data.get(
                "eth_1_1_access_payload"
            )
            eth_1_2_access_intf = self.have_all_payloads_data.get(
                "eth_1_2_access_payload"
            )
            eth_3_2_access_intf = self.have_all_payloads_data.get(
                "eth_3_2_access_payload"
            )

            # Build combined bulk response for SAL1819SAN8 containing all
            # Ethernet interface details.  The real NDFC API groups interfaces
            # that share the same policy into a single DATA element with
            # multiple entries in the "interfaces" array.  Simulate that here
            # to verify the bulk-fetch cache correctly unpacks grouped data.
            shared_policy = eth_1_1_access_intf["DATA"][0]["policy"]
            eth_bulk_payload = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [
                    {
                        "policy": shared_policy,
                        "interfaces": (
                            eth_1_1_access_intf["DATA"][0]["interfaces"]
                            + eth_1_2_access_intf["DATA"][0]["interfaces"]
                            + eth_3_2_access_intf["DATA"][0]["interfaces"]
                        ),
                    }
                ],
            }
            # Empty bulk response for the VPC switch (no eth interfaces there)
            eth_vpc_empty_payload = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [],
            }

            # Load breakout policies fixture
            self.breakout_policies_data = loadPlaybookData("dcnm_intf_breakout_policies")
            empty_breakout_resp = self.breakout_policies_data.get("empty_breakout_policies")

            # Call sequence with bulk interface detail prefetch:
            # [0] FABRIC_ACCESS_MODE
            # [1] IF_DETAIL_WITH_SNO for FOX1821H035 (returns empty)
            # [2] breakout policies for FOX1821H035 (returns empty)
            # [3] IF_DETAIL_WITH_SNO for SAL1819SAN8 (populates have_all)
            # [4] breakout policies for SAL1819SAN8 (returns empty)
            # [5] bulk IF_WITH_SNO for SAL1819SAN8 (all 3 Eth interface details)
            # [6] bulk IF_WITH_SNO for SAL1821T9EF (empty - VPC switch)
            # [7+] PUT/POST for replace/deploy
            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                empty_breakout_resp,
                empty_breakout_resp,
                playbook_have_all_data,
                empty_breakout_resp,
                eth_vpc_empty_payload,
                eth_bulk_payload,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if (
            "test_dcnm_intf_override_eth_intf_types_only_deleted_nd42_switch_only"
            in self._testMethodName
        ):

            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            eth_bulk_payload = self.build_bulk_payload(
                self.have_all_payloads_data.get("eth_1_1_access_payload"),
                self.have_all_payloads_data.get("eth_1_2_access_payload"),
                self.have_all_payloads_data.get("eth_3_2_access_payload"),
            )
            self.breakout_policies_data = loadPlaybookData(
                "dcnm_intf_breakout_policies"
            )
            empty_breakout_resp = self.breakout_policies_data.get(
                "empty_breakout_policies"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                playbook_have_all_data,
                empty_breakout_resp,
                self.build_bulk_payload(),
                eth_bulk_payload,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if (
            "test_dcnm_intf_override_sub_int_intf_types_only"
            in self._testMethodName
        ):

            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            # Load breakout policies fixture
            self.breakout_policies_data = loadPlaybookData("dcnm_intf_breakout_policies")
            empty_breakout_resp = self.breakout_policies_data.get("empty_breakout_policies")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                empty_breakout_resp,
                empty_breakout_resp,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if (
            "test_dcnm_intf_override_lo_intf_types_only"
            in self._testMethodName
        ):

            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            # Load breakout policies fixture
            self.breakout_policies_data = loadPlaybookData("dcnm_intf_breakout_policies")
            empty_breakout_resp = self.breakout_policies_data.get("empty_breakout_policies")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                empty_breakout_resp,
                empty_breakout_resp,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

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
                *([self.playbook_mock_succ_resp] * 20),
                playbook_deployed_data,
            ]

        if "_multi_intf_merged_exist" in self._testMethodName:
            # Interfaces exist case
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

            # Bulk IF_WITH_SNO response for SAL1819SAN8 (PC, subint, lo, eth)
            multi_bulk_sal = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [
                    playbook_pc_intf["DATA"][0],
                    playbook_subint_intf["DATA"][0],
                    playbook_lo_intf["DATA"][0],
                    playbook_eth_intf["DATA"][0],
                ],
            }
            # Bulk IF_WITH_SNO response for FOX1821H035 (VPC)
            multi_bulk_fox = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [
                    playbook_vpc_intf["DATA"][0],
                ],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                self.playbook_mock_vpc_resp,
                multi_bulk_fox,                      # IF_WITH_SNO bulk prefetch for FOX1821H035
                multi_bulk_sal,                      # IF_WITH_SNO bulk prefetch for SAL1819SAN8
                # Individual GETs eliminated — all cache hits
                playbook_have_all_data,
                playbook_have_all_data,
                *([self.playbook_mock_succ_resp] * 20),
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
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            # Bulk IF_WITH_SNO responses — empty since no interfaces exist yet
            bunched_bulk_sal_empty = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [],
            }
            bunched_bulk_fox_empty = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                self.playbook_mock_vpc_resp,
                bunched_bulk_sal_empty,               # IF_WITH_SNO bulk prefetch for SAL1819SAN8
                bunched_bulk_fox_empty,               # IF_WITH_SNO bulk prefetch for FOX1821H035
                # Individual GETs eliminated — all cache misses
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
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            pc_bulk_sal_empty = self.build_bulk_payload()
            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                pc_bulk_sal_empty,
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
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            svi_bulk_empty = self.build_bulk_payload()

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                svi_bulk_empty,
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
            svi_bulk_sal = self.build_bulk_payload(playbook_svi_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                svi_bulk_sal,
                playbook_have_all_data,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        # Use the same payloads that we use for creating new.
        if "_svi_deleted_existing" in self._testMethodName:
            playbook_svi_intf1 = self.payloads_data.get("svi_merged_payloads")
            svi_bulk_sal = self.build_bulk_payload(playbook_svi_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                svi_bulk_sal,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_svi_deleted_non_existing" in self._testMethodName:
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            # Load breakout policies fixture
            self.breakout_policies_data = loadPlaybookData("dcnm_intf_breakout_policies")
            empty_breakout_resp = self.breakout_policies_data.get("empty_breakout_policies")
            svi_bulk_empty = self.build_bulk_payload()

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                svi_bulk_empty,
                playbook_have_all_data,
                empty_breakout_resp,
            ]
        if "_svi_replaced_existing" in self._testMethodName:
            playbook_svi_intf1 = self.payloads_data.get("svi_merged_payloads")
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            svi_bulk_sal = self.build_bulk_payload(playbook_svi_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                svi_bulk_sal,
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
            eth_1_1_access_intf = self.have_all_payloads_data.get(
                "eth_1_1_access_payload"
            )
            eth_1_2_access_intf = self.have_all_payloads_data.get(
                "eth_1_2_access_payload"
            )
            eth_3_2_access_intf = self.have_all_payloads_data.get(
                "eth_3_2_access_payload"
            )
            svi_bulk_sal = self.build_bulk_payload(playbook_svi_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                svi_bulk_sal,
                playbook_have_all_data,
                eth_1_1_access_intf,
                eth_1_2_access_intf,
                eth_3_2_access_intf,
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
            # Load breakout policies fixture
            self.breakout_policies_data = loadPlaybookData("dcnm_intf_breakout_policies")
            empty_breakout_resp = self.breakout_policies_data.get("empty_breakout_policies")

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_aa_fex_intf1,
                empty_breakout_resp,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_aa_fex_merged_idempotent" in self._testMethodName:
            playbook_aa_fex_intf1 = self.payloads_data.get(
                "aa_fex_merged_payloads_150"
            )
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
            playbook_aa_fex_intf1 = self.payloads_data.get(
                "aa_fex_merged_payloads_150"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            aa_fex_bulk_sal_empty = self.build_bulk_payload()
            aa_fex_bulk_fox = self.build_bulk_payload(playbook_aa_fex_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                aa_fex_bulk_sal_empty,
                aa_fex_bulk_fox,
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
            playbook_aa_fex_intf1 = self.payloads_data.get(
                "aa_fex_merged_payloads_150"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            # Bulk IF_WITH_SNO responses.  AA_FEX with vpc-prefixed name
            # uses vpc_ip_sn → FOX1821H035 for lookups.  Prefetch order:
            # SAL (from ip_sn) then FOX (from vpc_ip_sn split).
            aa_fex_bulk_sal_empty = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [],
            }
            aa_fex_bulk_fox = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [
                    playbook_aa_fex_intf1["DATA"][0],
                ],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,       # FABRIC_ACCESS_MODE
                self.playbook_mock_vpc_resp,         # VPC_SNO for 192.168.1.108
                aa_fex_bulk_sal_empty,               # IF_WITH_SNO bulk prefetch for SAL1819SAN8
                aa_fex_bulk_fox,                     # IF_WITH_SNO bulk prefetch for FOX1821H035
                # intf_info for vPC150 is now a cache hit (FOX serial)
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_aa_fex_deleted_non_existing" in self._testMethodName:
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            # Load breakout policies fixture
            self.breakout_policies_data = loadPlaybookData("dcnm_intf_breakout_policies")
            empty_breakout_resp = self.breakout_policies_data.get("empty_breakout_policies")

            # Bulk IF_WITH_SNO responses.  vPC111 does not exist, so the
            # FOX bulk response is empty.  After prefetch, the intf_info
            # lookup for vPC111 on FOX returns [] from cache (SNO already
            # fetched, interface not found) — no individual HTTP call.
            # However, when intf_payload==[] for a non-ETH interface, the
            # code falls through to dcnm_intf_get_have_all(sw) which makes
            # 2 additional calls (have_all_with_sno + breakout_policies).
            aa_fex_bulk_sal_empty = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [],
            }
            aa_fex_bulk_fox_empty = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,       # FABRIC_ACCESS_MODE
                self.playbook_mock_vpc_resp,         # VPC_SNO for 192.168.1.108
                aa_fex_bulk_sal_empty,               # IF_WITH_SNO bulk prefetch for SAL1819SAN8
                aa_fex_bulk_fox_empty,               # IF_WITH_SNO bulk prefetch for FOX1821H035
                # intf_info for vPC111 returns [] from cache — no HTTP call
                # Since intf_payload==[], code falls through to have_all:
                playbook_have_all_data,              # have_all_with_sno for SAL1819SAN8
                empty_breakout_resp,                 # breakout_policies for SAL1819SAN8
            ]

        if "_aa_fex_replaced_existing" in self._testMethodName:
            playbook_aa_fex_intf1 = self.payloads_data.get(
                "aa_fex_merged_payloads_150"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            aa_fex_bulk_sal_empty = self.build_bulk_payload()
            aa_fex_bulk_fox = self.build_bulk_payload(playbook_aa_fex_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                aa_fex_bulk_sal_empty,
                aa_fex_bulk_fox,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_aa_fex_overridden_existing" in self._testMethodName:

            playbook_aa_fex_intf1 = self.payloads_data.get(
                "aa_fex_merged_payloads_150"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            eth_1_1_access_intf = self.have_all_payloads_data.get(
                "eth_1_1_access_payload"
            )
            eth_1_2_access_intf = self.have_all_payloads_data.get(
                "eth_1_2_access_payload"
            )
            eth_3_2_access_intf = self.have_all_payloads_data.get(
                "eth_3_2_access_payload"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_aa_fex_intf1,
                playbook_have_all_data,
                eth_1_1_access_intf,
                eth_1_2_access_intf,
                eth_3_2_access_intf,
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

            playbook_aa_fex_intf1 = self.payloads_data.get(
                "aa_fex_merged_payloads_150"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            eth_1_1_access_intf = self.have_all_payloads_data.get(
                "eth_1_1_access_payload"
            )
            eth_1_2_access_intf = self.have_all_payloads_data.get(
                "eth_1_2_access_payload"
            )
            eth_3_2_access_intf = self.have_all_payloads_data.get(
                "eth_3_2_access_payload"
            )

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                playbook_aa_fex_intf1,
                playbook_have_all_data,
                eth_1_1_access_intf,
                eth_1_2_access_intf,
                eth_3_2_access_intf,
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
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            st_fex_bulk_empty = self.build_bulk_payload()

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                st_fex_bulk_empty,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_st_fex_merged_idempotent" in self._testMethodName:
            playbook_st_fex_intf1 = self.payloads_data.get(
                "st_fex_merged_payloads_150"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            st_fex_bulk_sal = self.build_bulk_payload(playbook_st_fex_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                st_fex_bulk_sal,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_st_fex_merged_existing" in self._testMethodName:
            playbook_st_fex_intf1 = self.payloads_data.get(
                "st_fex_merged_payloads_150"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            st_fex_bulk_sal = self.build_bulk_payload(playbook_st_fex_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                st_fex_bulk_sal,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_st_fex_merged_multi" in self._testMethodName:
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            st_fex_bulk_empty = self.build_bulk_payload()

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                st_fex_bulk_empty,
                st_fex_bulk_empty,
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
            playbook_st_fex_intf1 = self.payloads_data.get(
                "st_fex_merged_payloads_150"
            )
            st_fex_bulk_sal = self.build_bulk_payload(playbook_st_fex_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                st_fex_bulk_sal,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_st_fex_deleted_non_existing" in self._testMethodName:
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            # Load breakout policies fixture
            self.breakout_policies_data = loadPlaybookData("dcnm_intf_breakout_policies")
            empty_breakout_resp = self.breakout_policies_data.get("empty_breakout_policies")
            st_fex_bulk_empty = self.build_bulk_payload()

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                st_fex_bulk_empty,
                playbook_have_all_data,
                empty_breakout_resp,
            ]
        if "_st_fex_replaced_existing" in self._testMethodName:
            playbook_st_fex_intf1 = self.payloads_data.get(
                "st_fex_merged_payloads_150"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            st_fex_bulk_sal = self.build_bulk_payload(playbook_st_fex_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                st_fex_bulk_sal,
                playbook_have_all_data,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
                self.playbook_mock_succ_resp,
            ]

        if "_st_fex_overridden_existing" in self._testMethodName:

            playbook_st_fex_intf1 = self.payloads_data.get(
                "st_fex_merged_payloads_150"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            eth_1_1_access_intf = self.have_all_payloads_data.get(
                "eth_1_1_access_payload"
            )
            eth_1_2_access_intf = self.have_all_payloads_data.get(
                "eth_1_2_access_payload"
            )
            eth_3_2_access_intf = self.have_all_payloads_data.get(
                "eth_3_2_access_payload"
            )
            st_fex_bulk_sal = self.build_bulk_payload(playbook_st_fex_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                st_fex_bulk_sal,
                playbook_have_all_data,
                eth_1_1_access_intf,
                eth_1_2_access_intf,
                eth_3_2_access_intf,
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

            playbook_st_fex_intf1 = self.payloads_data.get(
                "st_fex_merged_payloads_150"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            eth_1_1_access_intf = self.have_all_payloads_data.get(
                "eth_1_1_access_payload"
            )
            eth_1_2_access_intf = self.have_all_payloads_data.get(
                "eth_1_2_access_payload"
            )
            eth_3_2_access_intf = self.have_all_payloads_data.get(
                "eth_3_2_access_payload"
            )
            st_fex_bulk_sal = self.build_bulk_payload(playbook_st_fex_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                st_fex_bulk_sal,
                playbook_have_all_data,
                eth_1_1_access_intf,
                eth_1_2_access_intf,
                eth_3_2_access_intf,
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
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            # Bulk IF_WITH_SNO response — empty since no interfaces exist yet
            pc_bulk_sal_empty = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                pc_bulk_sal_empty,                   # IF_WITH_SNO bulk prefetch for SAL1819SAN8
                # Individual GETs eliminated — all cache misses
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

        if "_pc_merged_vlan_range_new" in self._testMethodName:
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            pc_bulk_sal_empty = self.build_bulk_payload()

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                pc_bulk_sal_empty,
                playbook_have_all_data,
                playbook_have_all_data,
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
            pc_bulk_sal = self.build_bulk_payload(playbook_pc_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                pc_bulk_sal,
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

            # Bulk IF_WITH_SNO response for SAL1819SAN8 combining all 4 PCs
            pc_bulk_sal = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [
                    playbook_pc_intf1["DATA"][0],
                    playbook_pc_intf2["DATA"][0],
                    playbook_pc_intf3["DATA"][0],
                    playbook_pc_intf4["DATA"][0],
                ],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                pc_bulk_sal,                         # IF_WITH_SNO bulk prefetch for SAL1819SAN8
                # Individual GETs eliminated — all cache hits
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

            # Bulk IF_WITH_SNO response for SAL1819SAN8 combining all 4 PCs.
            pc_bulk_sal = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [
                    playbook_pc_intf1["DATA"][0],
                    playbook_pc_intf2["DATA"][0],
                    playbook_pc_intf3["DATA"][0],
                    playbook_pc_intf4["DATA"][0],
                ],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,       # FABRIC_ACCESS_MODE
                pc_bulk_sal,                         # IF_WITH_SNO bulk prefetch for SAL1819SAN8
                # intf_info calls for all 4 PCs are now cache hits
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
            pc_bulk_sal = self.build_bulk_payload(playbook_pc_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                pc_bulk_sal,
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
            playbook_have_all_data = self.have_all_payloads_data.get(
                "deleted_intf_payloads"
            )
            pc_bulk_sal_empty = self.build_bulk_payload()

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                pc_bulk_sal_empty,
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
            pc_bulk_sal = self.build_bulk_payload(playbook_pc_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                pc_bulk_sal,
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

            # Bulk IF_WITH_SNO response for SAL1819SAN8 combining all 4 PCs
            pc_bulk_sal = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [
                    playbook_pc_intf1["DATA"][0],
                    playbook_pc_intf2["DATA"][0],
                    playbook_pc_intf3["DATA"][0],
                    playbook_pc_intf4["DATA"][0],
                ],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                pc_bulk_sal,                         # IF_WITH_SNO bulk prefetch for SAL1819SAN8
                # Individual GETs eliminated — all cache hits
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

            eth_1_1_access_intf = self.have_all_payloads_data.get(
                "eth_1_1_access_payload"
            )
            eth_1_2_access_intf = self.have_all_payloads_data.get(
                "eth_1_2_access_payload"
            )
            eth_3_2_access_intf = self.have_all_payloads_data.get(
                "eth_3_2_access_payload"
            )
            pc_bulk_sal = self.build_bulk_payload(playbook_pc_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                pc_bulk_sal,
                playbook_have_all_data,
                eth_1_1_access_intf,
                eth_1_2_access_intf,
                eth_3_2_access_intf,
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
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )

            # Bulk IF_WITH_SNO response — empty since no interfaces exist yet
            eth_bulk_sal_empty = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                eth_bulk_sal_empty,                  # IF_WITH_SNO bulk prefetch for SAL1819SAN8
                # Individual GETs eliminated — all cache misses (SNO cached, interfaces not found)
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

        if "_eth_merged_missing_native_vlan" in self._testMethodName:
            playbook_eth_intf1 = self.payloads_data.get(
                "eth_merged_trunk_missing_native_vlan_payloads"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            eth_bulk_sal = self.build_bulk_payload(playbook_eth_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                eth_bulk_sal,
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

        if "_eth_merged_existing" in self._testMethodName:
            playbook_eth_intf1 = self.payloads_data.get(
                "eth_merged_routed_payloads_eth_1_2"
            )
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            eth_bulk_sal = self.build_bulk_payload(playbook_eth_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                eth_bulk_sal,
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

            # Bulk IF_WITH_SNO response for SAL1819SAN8 combining all 5 ETH interfaces
            eth_bulk_sal = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [
                    playbook_eth_intf1["DATA"][0],
                    playbook_eth_intf2["DATA"][0],
                    playbook_eth_intf3["DATA"][0],
                    playbook_eth_intf4["DATA"][0],
                    playbook_eth_intf5["DATA"][0],
                ],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                eth_bulk_sal,                        # IF_WITH_SNO bulk prefetch for SAL1819SAN8
                # Individual GETs eliminated — all cache hits
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

            # Bulk IF_WITH_SNO response for SAL1819SAN8 combining all 5 ETH interfaces
            eth_bulk_sal = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [
                    playbook_eth_intf1["DATA"][0],
                    playbook_eth_intf2["DATA"][0],
                    playbook_eth_intf3["DATA"][0],
                    playbook_eth_intf4["DATA"][0],
                    playbook_eth_intf5["DATA"][0],
                ],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                eth_bulk_sal,                        # IF_WITH_SNO bulk prefetch for SAL1819SAN8
                # Individual GETs eliminated — all cache hits
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

            # Bulk IF_WITH_SNO response for SAL1819SAN8 combining all 5 ETH
            # interfaces.  The deleted-state prefetch makes one bulk GET per
            # unique serial number, replacing 5 individual GETs.
            eth_bulk_sal = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [
                    playbook_eth_intf1["DATA"][0],
                    playbook_eth_intf2["DATA"][0],
                    playbook_eth_intf3["DATA"][0],
                    playbook_eth_intf4["DATA"][0],
                    playbook_eth_intf5["DATA"][0],
                ],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,       # FABRIC_ACCESS_MODE
                eth_bulk_sal,                        # IF_WITH_SNO bulk prefetch for SAL1819SAN8
                playbook_have_all_data,              # IF_DETAIL_WITH_SNO (have_all)
                self.playbook_mock_succ_resp,         # breakout_policies (harmless, no breakout match)
                # intf_info calls for all 5 ETH interfaces are now cache hits
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

            eth_1_1_access_intf = self.have_all_payloads_data.get(
                "eth_1_1_access_payload"
            )
            eth_1_2_access_intf = self.have_all_payloads_data.get(
                "eth_1_2_access_payload"
            )
            eth_3_2_access_intf = self.have_all_payloads_data.get(
                "eth_3_2_access_payload"
            )
            if "_fec_" in self._testMethodName:
                # The bulk endpoint returns every configured interface for the
                # switch. Include the physical interfaces exercised by the FEC
                # defaulting test so the cache reflects a real response.
                eth_bulk_sal = self.build_bulk_payload(
                    playbook_eth_intf1,
                    eth_1_1_access_intf,
                    eth_1_2_access_intf,
                    eth_3_2_access_intf,
                )
            else:
                eth_bulk_sal = self.build_bulk_payload(playbook_eth_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                eth_bulk_sal,
                playbook_have_all_data,
                eth_1_1_access_intf,
                eth_1_2_access_intf,
                eth_3_2_access_intf,
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
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )
            subint_bulk_sal_empty = self.build_bulk_payload()

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                subint_bulk_sal_empty,
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

            # Bulk IF_WITH_SNO response for SAL1819SAN8 with both sub-interfaces
            subint_bulk_sal = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [
                    playbook_subint_intf1["DATA"][0],
                    playbook_subint_intf2["DATA"][0],
                ],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                subint_bulk_sal,                     # IF_WITH_SNO bulk prefetch for SAL1819SAN8
                # Individual GETs eliminated — all cache hits
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

            # Bulk IF_WITH_SNO response for SAL1819SAN8 with both sub-interfaces
            subint_bulk_sal = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [
                    playbook_subint_intf1["DATA"][0],
                    playbook_subint_intf2["DATA"][0],
                ],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                subint_bulk_sal,                     # IF_WITH_SNO bulk prefetch for SAL1819SAN8
                # Individual GETs eliminated — all cache hits
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
            subint_bulk_sal = self.build_bulk_payload(playbook_subint_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                subint_bulk_sal,
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

            # Bulk IF_WITH_SNO response for SAL1819SAN8 with both sub-interfaces.
            subint_bulk_sal = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [
                    playbook_subint_intf1["DATA"][0],
                    playbook_subint_intf2["DATA"][0],
                ],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,       # FABRIC_ACCESS_MODE
                subint_bulk_sal,                     # IF_WITH_SNO bulk prefetch for SAL1819SAN8
                # intf_info calls for both sub-interfaces are now cache hits
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

            eth_1_1_access_intf = self.have_all_payloads_data.get(
                "eth_1_1_access_payload"
            )
            eth_1_2_access_intf = self.have_all_payloads_data.get(
                "eth_1_2_access_payload"
            )
            eth_3_2_access_intf = self.have_all_payloads_data.get(
                "eth_3_2_access_payload"
            )
            subint_bulk_sal = self.build_bulk_payload(playbook_subint_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                subint_bulk_sal,
                playbook_have_all_data,
                eth_1_1_access_intf,
                eth_1_2_access_intf,
                eth_3_2_access_intf,
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
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )
            lo_bulk_sal_empty = self.build_bulk_payload()

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                lo_bulk_sal_empty,
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

            # Bulk IF_WITH_SNO response for SAL1819SAN8 with both loopbacks
            lo_bulk_sal = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [
                    playbook_lo_intf1["DATA"][0],
                    playbook_lo_intf2["DATA"][0],
                ],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                lo_bulk_sal,                         # IF_WITH_SNO bulk prefetch for SAL1819SAN8
                # Individual GETs eliminated — all cache hits
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
            lo_bulk_sal = self.build_bulk_payload(playbook_lo_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                lo_bulk_sal,
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

            # Bulk IF_WITH_SNO response for SAL1819SAN8 with both loopbacks
            lo_bulk_sal = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [
                    playbook_lo_intf1["DATA"][0],
                    playbook_lo_intf2["DATA"][0],
                ],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                lo_bulk_sal,                         # IF_WITH_SNO bulk prefetch for SAL1819SAN8
                # Individual GETs eliminated — all cache hits
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

            # Bulk IF_WITH_SNO response for SAL1819SAN8 with both loopbacks.
            lo_bulk_sal = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [
                    playbook_lo_intf1["DATA"][0],
                    playbook_lo_intf2["DATA"][0],
                ],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,       # FABRIC_ACCESS_MODE
                lo_bulk_sal,                         # IF_WITH_SNO bulk prefetch for SAL1819SAN8
                # intf_info calls for both loopbacks are now cache hits
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

            eth_1_1_access_intf = self.have_all_payloads_data.get(
                "eth_1_1_access_payload"
            )
            eth_1_2_access_intf = self.have_all_payloads_data.get(
                "eth_1_2_access_payload"
            )
            eth_3_2_access_intf = self.have_all_payloads_data.get(
                "eth_3_2_access_payload"
            )

            # Bulk IF_WITH_SNO response for SAL1819SAN8 with both loopbacks
            # (consumed by get_have bulk prefetch for the overridden state)
            lo_bulk_sal = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [
                    playbook_lo_intf1["DATA"][0],
                    playbook_lo_intf2["DATA"][0],
                ],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                lo_bulk_sal,                         # IF_WITH_SNO bulk prefetch for SAL1819SAN8
                # Individual GETs eliminated — all cache hits
                playbook_have_all_data,
                eth_1_1_access_intf,
                eth_1_2_access_intf,
                eth_3_2_access_intf,
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

            eth_1_1_access_intf = self.have_all_payloads_data.get(
                "eth_1_1_access_payload"
            )
            eth_1_2_access_intf = self.have_all_payloads_data.get(
                "eth_1_2_access_payload"
            )
            eth_3_2_access_intf = self.have_all_payloads_data.get(
                "eth_3_2_access_payload"
            )
            lo_bulk_sal = self.build_bulk_payload(playbook_lo_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                lo_bulk_sal,
                playbook_have_all_data,
                eth_1_1_access_intf,
                eth_1_2_access_intf,
                eth_3_2_access_intf,
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

            eth_1_1_access_intf = self.have_all_payloads_data.get(
                "eth_1_1_access_payload"
            )
            eth_1_2_access_intf = self.have_all_payloads_data.get(
                "eth_1_2_access_payload"
            )
            eth_3_2_access_intf = self.have_all_payloads_data.get(
                "eth_3_2_access_payload"
            )
            lo_bulk_sal = self.build_bulk_payload(playbook_lo_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                lo_bulk_sal,
                playbook_have_all_data,
                eth_1_1_access_intf,
                eth_1_2_access_intf,
                eth_3_2_access_intf,
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

        # Fabric-loopback OSPF message-digest cases. Each test picks the HAVE
        # payload it needs by setting self.fabric_lo_have before running the
        # module.
        if "_lo_ospfmd_" in self._testMethodName:

            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )

            if "have_get_failure" in self._testMethodName:
                # G6A.4 finding 2: every interface GET fails (non-200) after the
                # initial fabric-mode probe, so the fabric-loopback HAVE cannot be
                # read authoritatively.
                fail_resp = {"RETURN_CODE": 500, "MESSAGE": "ERR", "DATA": {}}
                self.run_dcnm_send.side_effect = (
                    [self.mock_monitor_false_resp] + [fail_resp] * 30
                )
            else:
                lo_bulk_sal = self.build_bulk_payload(self.fabric_lo_have)
                self.run_dcnm_send.side_effect = [
                    self.mock_monitor_false_resp,   # FABRIC_ACCESS_MODE
                    lo_bulk_sal,                    # IF_WITH_SNO bulk prefetch
                    playbook_have_all_data,
                ] + [self.playbook_mock_succ_resp] * 16

    # -------------------------- vPC-FIXTURES --------------------------

    def load_vpc_fixtures(self):

        if "_vpc_merged_new" in self._testMethodName:
            playbook_have_all_data = self.have_all_payloads_data.get(
                "payloads"
            )
            playbook_deployed_data = self.have_all_payloads_data.get(
                "deployed_payloads"
            )
            vpc_bulk_fox_empty = self.build_bulk_payload()

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                self.playbook_mock_vpc_resp,
                vpc_bulk_fox_empty,
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

            # Bulk IF_WITH_SNO response for FOX1821H035 (first part of VPC pair)
            vpc_bulk_fox = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [
                    playbook_vpc_intf1["DATA"][0],
                    playbook_vpc_intf2["DATA"][0],
                ],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                self.playbook_mock_vpc_resp,
                vpc_bulk_fox,                        # IF_WITH_SNO bulk prefetch for FOX1821H035
                # Individual GETs eliminated — all cache hits
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

            # Bulk IF_WITH_SNO responses.  VPC interfaces use the first
            # part of the combined serial (FOX1821H035).  The prefetch
            # fetches both ip_sn serials (FOX, SAL) plus the VPC serial
            # (FOX again, deduped).  Order: FOX first, then SAL.
            vpc_bulk_fox = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [
                    playbook_vpc_intf1["DATA"][0],
                    playbook_vpc_intf2["DATA"][0],
                ],
            }
            vpc_bulk_sal_empty = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,       # FABRIC_ACCESS_MODE
                self.playbook_mock_vpc_resp,         # VPC_SNO for 192.168.1.109
                self.playbook_mock_vpc_resp,         # VPC_SNO for 192.168.1.108
                vpc_bulk_fox,                        # IF_WITH_SNO bulk prefetch for FOX1821H035
                vpc_bulk_sal_empty,                  # IF_WITH_SNO bulk prefetch for SAL1819SAN8
                # intf_info calls for both VPCs are now cache hits (FOX serial)
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

            # Bulk IF_WITH_SNO response for FOX1821H035 (first part of VPC pair)
            vpc_bulk_fox = {
                "MESSAGE": "OK",
                "RETURN_CODE": 200,
                "DATA": [
                    playbook_vpc_intf1["DATA"][0],
                    playbook_vpc_intf2["DATA"][0],
                ],
            }

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                self.playbook_mock_vpc_resp,
                vpc_bulk_fox,                        # IF_WITH_SNO bulk prefetch for FOX1821H035
                # Individual GETs eliminated — all cache hits
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
            eth_1_1_access_intf = self.have_all_payloads_data.get(
                "eth_1_1_access_payload"
            )
            eth_1_2_access_intf = self.have_all_payloads_data.get(
                "eth_1_2_access_payload"
            )
            eth_3_2_access_intf = self.have_all_payloads_data.get(
                "eth_3_2_access_payload"
            )
            vpc_bulk_fox = self.build_bulk_payload(playbook_vpc_intf1)

            self.run_dcnm_send.side_effect = [
                self.mock_monitor_false_resp,
                self.playbook_mock_vpc_resp,
                self.playbook_mock_vpc_resp,
                vpc_bulk_fox,
                playbook_have_all_data,
                eth_1_1_access_intf,
                eth_1_2_access_intf,
                eth_3_2_access_intf,
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
        if "_fec_" in self._testMethodName:
            self.run_dcnm_version_supported.side_effect = [
                (12, "12.4.1.245")
            ]
        elif "_lo_ospfmd_" in self._testMethodName:
            # Fabric loopbacks are only present in the NDFC 12 policy map.
            self.run_dcnm_version_supported.side_effect = [
                (12, getattr(self, "_ospfmd_ndfc_version", "12.2.2.238"))
            ]
        else:
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

        # Load general side-effects
        self.load_general_intf_fixtures()

        # Load missing elements interface configuration related side-effects
        self.load_type_missing_fixtures()
        self.load_missing_state_fixtures()
        self.load_missing_members_fixtures()
        self.load_query_state_fixtures()
        self.load_intf_misc_fixtures()
        self.normalize_legacy_bulk_fixture_responses()

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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )

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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )

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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )

        set_module_args(
            dict(
                state="merged",
                _ansible_check_mode=True,
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 5)
        self.assertFalse(result.get("response"))
        self.assert_no_mutating_dcnm_calls()
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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

    def test_dcnm_intf_pc_merged_vlan_range_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_pc_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_pc_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("pc_merged_vlan_range_config")
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
                self.assertEqual(
                    (
                        intf["ifName"]
                        in [
                            "Port-channel300"
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.playbook_config = self.config_data.get(
            "pc_deleted_config_no_deploy"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
            self.assertEqual((intf["ifName"] in ["Port-channel300"]), True)
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
            "DISABLE_LACP_SUSPEND",
            "LACP_PORT_PRIO",
            "LACP_RATE",
            "ENABLE_QOS",
            "QOS_POLICY",
            "QUEUING_POLICY",
            "COPY_DESC",
            "ENABLE_STORM_CONTROL",
            "STORM_CONTROL_ACTION",
            "STORM_CONTROL_BCAST_LEVEL_PERCENT",
            "STORM_CONTROL_BCAST_LEVEL_PPS",
            "STORM_CONTROL_MCAST_LEVEL_PERCENT",
            "STORM_CONTROL_MCAST_LEVEL_PPS",
            "STORM_CONTROL_UCAST_LEVEL_PERCENT",
            "STORM_CONTROL_UCAST_LEVEL_PPS",
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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

        rep_if_names = ["ethernet1/1", "ethernet1/2", "ethernet3/2"]
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

        # Use Version 12 For This Test Case
        self.run_dcnm_version_supported.side_effect = [12]

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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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

    def test_dcnm_intf_eth_merged_missing_native_vlan(self):

        # Use Version 12 For This Test Case
        self.run_dcnm_version_supported.side_effect = [12]

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_eth_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_eth_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get(
            "eth_merged_config_missing_native_vlan"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
                self.assertEqual((intf["ifName"] in ["Ethernet1/30"]), True)

    def test_dcnm_intf_eth_merged_new(self):

        # Use Version 12 For This Test Case
        self.run_dcnm_version_supported.side_effect = [12]

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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
            "ENABLE_QOS",
            "QOS_POLICY",
            "QUEUING_POLICY",
            "ENABLE_STORM_CONTROL",
            "STORM_CONTROL_ACTION",
            "STORM_CONTROL_BCAST_LEVEL_PERCENT",
            "STORM_CONTROL_BCAST_LEVEL_PPS",
            "STORM_CONTROL_MCAST_LEVEL_PERCENT",
            "STORM_CONTROL_MCAST_LEVEL_PPS",
            "STORM_CONTROL_UCAST_LEVEL_PERCENT",
            "STORM_CONTROL_UCAST_LEVEL_PPS",
        ]

        for d in result["diff"][0]["replaced"]:
            for intf in d["interfaces"]:
                if_keys = list(intf["nvPairs"].keys())
                self.assertEqual(
                    (set(if_keys).issubset(set(changed_objs))), True
                )
        # Monitor port will not bedeployed
        self.assertEqual(len(result["diff"][0]["deploy"]), 4)

    def prepare_eth_deleted_existing_test(self):

        self.config_data = loadPlaybookData("dcnm_intf_eth_configs")
        self.payloads_data = copy.deepcopy(
            loadPlaybookData("dcnm_intf_eth_payloads")
        )
        self.have_all_payloads_data = copy.deepcopy(
            loadPlaybookData("dcnm_intf_have_all_payloads")
        )

        self.playbook_config = self.config_data.get("eth_deleted_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        for switch in self.mock_fab_inv.values():
            switch["switchRole"] = "leaf"
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

    def set_eth_deleted_capabilities(self, deletable, edit_allowed=None):

        for intf in self.have_all_payloads_data["eth_payloads"]["DATA"]:
            intf["deletable"] = deletable
            if edit_allowed is None:
                intf.pop("editAllowed", None)
            else:
                intf["editAllowed"] = edit_allowed

    def prepare_nd42_deleted_all_eth_test(
        self,
        deletable=False,
        edit_allowed=True,
        omit_deletable=False,
        omit_edit_allowed=False,
    ):

        self.config_data = loadPlaybookData("dcnm_intf_common_configs")
        self.have_all_payloads_data = copy.deepcopy(
            loadPlaybookData("dcnm_intf_have_all_payloads")
        )

        for intf in self.have_all_payloads_data["payloads"]["DATA"]:
            if (
                intf["ifType"] == "INTERFACE_ETHERNET"
                and str(intf["isPhysical"]).lower() == "true"
            ):
                if omit_deletable:
                    intf.pop("deletable", None)
                else:
                    intf["deletable"] = deletable
                if omit_edit_allowed:
                    intf.pop("editAllowed", None)
                else:
                    intf["editAllowed"] = edit_allowed

        self.playbook_config = self.config_data.get("override_eth_only_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

    def set_eth_deleted_payloads_to_role_default(
        self, policy="int_trunk_host_11_1"
    ):

        payload_names = [
            "eth_merged_trunk_payloads",
            "eth_merged_access_payloads",
            "eth_merged_routed_payloads",
            "eth_merged_epl_routed_payloads",
            "eth_merged_monitor_payloads",
        ]
        for payload_name in payload_names:
            payload = self.payloads_data[payload_name]["DATA"][0]
            ifname = payload["interfaces"][0]["ifName"]
            payload["policy"] = policy
            payload["interfaces"][0]["nvPairs"] = {
                "interfaceType": "INTERFACE_ETHERNET",
                "MTU": "jumbo",
                "SPEED": "Auto",
                "DESC": "",
                "CONF": "no shutdown",
                "ADMIN_STATE": True,
                "INTF_NAME": ifname,
                "BPDUGUARD_ENABLED": False,
                "PORTTYPE_FAST_ENABLED": True,
                "ALLOWED_VLANS": "none",
                "NATIVE_VLAN": "",
                **self.storm_control_default_nvpairs(),
            }

    def prepare_eth_deleted_fec_only_test(self):
        self.prepare_eth_deleted_existing_test()
        self.set_eth_deleted_payloads_to_role_default(
            policy="int_trunk_host"
        )
        self.payloads_data["eth_merged_trunk_payloads"]["DATA"][0][
            "interfaces"
        ][0]["nvPairs"]["FEC"] = "rs-fec"

    def set_eth_overridden_payloads_to_role_default(
        self, fec_interface=None
    ):
        for payload_name in (
            "eth_1_1_access_payload",
            "eth_1_2_access_payload",
            "eth_3_2_access_payload",
        ):
            payload = self.have_all_payloads_data[payload_name]["DATA"][0]
            ifname = payload["interfaces"][0]["ifName"]
            payload["policy"] = "int_trunk_host"
            payload["interfaces"][0]["nvPairs"] = {
                "interfaceType": "INTERFACE_ETHERNET",
                "MTU": "jumbo",
                "SPEED": "Auto",
                "DESC": "",
                "CONF": "no shutdown",
                "ADMIN_STATE": True,
                "INTF_NAME": ifname,
                "BPDUGUARD_ENABLED": False,
                "PORTTYPE_FAST_ENABLED": True,
                "ALLOWED_VLANS": "none",
                "NATIVE_VLAN": "",
                "FEC": (
                    "rs-fec" if ifname == fec_interface else "auto"
                ),
                **self.storm_control_default_nvpairs(),
            }

    def test_dcnm_intf_eth_deleted_existing(self):

        self.prepare_eth_deleted_existing_test()

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
        self.assert_leaf_default_storm_control(
            result["diff"][0]["replaced"]
        )

    def test_dcnm_intf_eth_deleted_existing_nd42_edit_allowed(self):

        self.prepare_eth_deleted_existing_test()
        self.set_eth_deleted_capabilities(False, True)

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["replaced"]), 5)
        self.assertEqual(len(result["diff"][0]["skipped"]), 0)
        self.assertTrue(
            all(
                payload["policy"] == "int_trunk_host_11_1"
                for payload in result["diff"][0]["replaced"]
            )
        )

    def test_dcnm_intf_eth_deleted_existing_nd42_string_edit_allowed(self):

        self.prepare_eth_deleted_existing_test()
        self.set_eth_deleted_capabilities("False", " TRUE ")

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["replaced"]), 5)
        self.assertEqual(len(result["diff"][0]["skipped"]), 0)

    def test_dcnm_intf_eth_deleted_existing_nd42_check_mode(self):

        self.prepare_eth_deleted_existing_test()
        self.set_eth_deleted_capabilities(False, True)

        set_module_args(
            dict(
                state="deleted",
                _ansible_check_mode=True,
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["replaced"]), 5)
        self.assertFalse(result.get("response"))
        self.assert_no_mutating_dcnm_calls()

    def test_dcnm_intf_eth_deleted_existing_nd42_idempotent(self):

        self.prepare_eth_deleted_existing_test()
        self.set_eth_deleted_capabilities(False, True)
        self.set_eth_deleted_payloads_to_role_default()

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["replaced"]), 0)
        self.assertEqual(len(result["diff"][0]["skipped"]), 0)
        self.assertFalse(result.get("response"))

    def test_dcnm_intf_eth_deleted_existing_nd42_check_mode_idempotent(self):

        self.prepare_eth_deleted_existing_test()
        self.set_eth_deleted_capabilities(False, True)
        self.set_eth_deleted_payloads_to_role_default()

        set_module_args(
            dict(
                state="deleted",
                _ansible_check_mode=True,
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["replaced"]), 0)
        self.assertEqual(len(result["diff"][0]["skipped"]), 0)
        self.assertFalse(result.get("response"))
        self.assert_no_mutating_dcnm_calls()

    def test_dcnm_intf_eth_deleted_existing_fec_only(self):
        self.prepare_eth_deleted_fec_only_test()

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(
            len(result["diff"][0]["replaced"]), 1, result
        )
        replacement = result["diff"][0]["replaced"][0]
        self.assertEqual(
            replacement["interfaces"][0]["ifName"], "Ethernet1/30"
        )
        self.assertEqual(
            replacement["interfaces"][0]["nvPairs"]["FEC"], "auto"
        )

    def test_dcnm_intf_eth_deleted_existing_fec_only_check_mode(self):
        self.prepare_eth_deleted_fec_only_test()

        set_module_args(
            dict(
                state="deleted",
                _ansible_check_mode=True,
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["replaced"]), 1)
        self.assertEqual(
            result["diff"][0]["replaced"][0]["interfaces"][0]["nvPairs"][
                "FEC"
            ],
            "auto",
        )
        self.assertFalse(result.get("response"))
        self.assert_no_mutating_dcnm_calls()

    def test_dcnm_intf_eth_deleted_existing_fec_default_idempotent(self):
        self.prepare_eth_deleted_existing_test()
        self.set_eth_deleted_payloads_to_role_default(
            policy="int_trunk_host"
        )

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["replaced"]), 0)
        self.assertFalse(result.get("response"))

    def test_dcnm_intf_eth_deleted_existing_nd42_underlay_dependency(self):

        self.prepare_eth_deleted_existing_test()
        self.set_eth_deleted_capabilities(False, True)
        self.have_all_payloads_data["eth_payloads"]["DATA"][0][
            "underlayPolicies"
        ] = [{"source": "port-channel300"}]

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        replaced_names = {
            payload["interfaces"][0]["ifName"]
            for payload in result["diff"][0]["replaced"]
        }
        self.assertNotIn("Ethernet1/30", replaced_names)
        self.assertEqual(len(replaced_names), 4)
        self.assertTrue(
            any(
                skipped["Name"] == "Ethernet1/30"
                and "underlay policy source" in skipped["Reason"]
                for skipped in result["diff"][0]["skipped"]
            )
        )

    def test_dcnm_intf_eth_deleted_existing_not_editable(self):

        self.prepare_eth_deleted_existing_test()
        self.set_eth_deleted_capabilities(False, False)

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["replaced"]), 0)
        self.assertEqual(len(result["diff"][0]["skipped"]), 5)

    def test_dcnm_intf_eth_deleted_existing_missing_edit_allowed(self):

        self.prepare_eth_deleted_existing_test()
        self.set_eth_deleted_capabilities(False)

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["replaced"]), 0)
        self.assertEqual(len(result["diff"][0]["skipped"]), 5)

    def test_dcnm_intf_eth_deleted_existing_unknown_deletable_not_editable(
        self,
    ):

        self.prepare_eth_deleted_existing_test()
        self.set_eth_deleted_capabilities(None, False)

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["replaced"]), 0)
        self.assertEqual(len(result["diff"][0]["skipped"]), 5)

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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        ovr_if_names = ["ethernet1/25.1"]

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

        # Use Version 12 For This Test Case
        self.run_dcnm_version_supported.side_effect = [12]

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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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

    # ---------- LOOPBACK OSPF MESSAGE-DIGEST AUTHENTICATION ----------
    #
    # Every test below drives nvPairs.ENABLE_OSPF_AUTH_MESSAGE_DIGEST on policy
    # int_fabric_loopback_11_1. Capability comes from named-template metadata
    # (dcnm_get_template_details), never from an NDFC version threshold, so the
    # capability mock is set explicitly per test.

    OSPF_MD_NVPAIR = "ENABLE_OSPF_AUTH_MESSAGE_DIGEST"

    def _ospfmd_load_common(self, config_key, have_key):
        """Load the shared fixtures for a fabric-loopback OSPF-MD test."""
        self.config_data = loadPlaybookData("dcnm_intf_lo_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_lo_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        self.playbook_config = self.config_data.get(config_key)
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")
        self.fabric_lo_have = self.payloads_data.get(have_key)

    def _ospfmd_set_capability(self, parent_key, child_key):
        """
        Model controller capability through the NDFC version gate. A "supported"
        scenario means a controller new enough to ship the nvPair; anything else
        (unsupported/unavailable/malformed) is modeled as an older controller.
        """
        supported = (
            isinstance(parent_key, str)
            and "supported" in parent_key
            and isinstance(child_key, str)
            and "supported" in child_key
        )
        self._ospfmd_ndfc_version = "12.6.0.267" if supported else "12.2.2.238"

    def _ospfmd_nvpairs(self, result, bucket):
        """Return {ifName: nvPairs} for one diff bucket."""
        return {
            intf["ifName"]: intf["nvPairs"]
            for d in result["diff"][0][bucket]
            for intf in d["interfaces"]
        }

    def _ospfmd_sent_nvpairs(self):
        """
        Return {INTF_NAME: nvPairs} from the payloads actually sent to the
        controller (the outbound full parent payload), parsed from the
        dcnm_send mock. Finding 1 preserves HAVE in the SENT payload, not in the
        reported feature diff, so this reads the wire body, not result['diff'].
        """
        found = {}

        def _walk(node):
            if isinstance(node, dict):
                if "nvPairs" in node and isinstance(node["nvPairs"], dict):
                    key = node["nvPairs"].get("INTF_NAME") or node.get("ifName")
                    if key:
                        found[key] = node["nvPairs"]
                for value in node.values():
                    _walk(value)
            elif isinstance(node, list):
                for item in node:
                    _walk(item)

        for call in self.run_dcnm_send.call_args_list:
            args = call.args
            if len(args) < 4:
                continue
            method, payload = args[1], args[3]
            if method not in ("POST", "PUT"):
                continue
            try:
                body = json.loads(payload) if isinstance(payload, str) else payload
            except (TypeError, ValueError):
                continue
            _walk(body)
        return found

    # ------------------------------------------------------------------
    # G6A.1 finding 1: an omitted option must preserve the HAVE value in the
    # OUTBOUND payload during an update driven by an unrelated field, in every
    # state, without a spurious feature diff and without a capability lookup.
    # ------------------------------------------------------------------
    def _ospfmd_run_unrelated_update(self, state, have_key, bulk=False):
        self._ospfmd_load_common(
            "lo_fabric_omitted_desc_change_config", have_key
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )
        self.run_dcnm_bulk_api_support.return_value = bulk
        set_module_args(
            dict(state=state, fabric="test_fabric", config=self.playbook_config)
        )
        result = self.execute_module(changed=True, failed=False)
        return result, self._ospfmd_sent_nvpairs()

    def test_dcnm_intf_lo_ospfmd_merged_unrelated_update_preserves_have_true(self):
        _r, sent = self._ospfmd_run_unrelated_update(
            "merged", "lo_fabric_payloads_auth_string_true"
        )
        self.assertEqual(sent["Loopback0"][self.OSPF_MD_NVPAIR], "true")

    def test_dcnm_intf_lo_ospfmd_replaced_unrelated_update_preserves_have_true(self):
        _r, sent = self._ospfmd_run_unrelated_update(
            "replaced", "lo_fabric_payloads_auth_string_true"
        )
        self.assertEqual(sent["Loopback0"][self.OSPF_MD_NVPAIR], "true")

    def test_dcnm_intf_lo_ospfmd_overridden_unrelated_update_preserves_have_true(self):
        _r, sent = self._ospfmd_run_unrelated_update(
            "overridden", "lo_fabric_payloads_auth_string_true"
        )
        self.assertEqual(sent["Loopback0"][self.OSPF_MD_NVPAIR], "true")

    def test_dcnm_intf_lo_ospfmd_replaced_unrelated_update_preserves_native_true(self):
        _r, sent = self._ospfmd_run_unrelated_update(
            "replaced", "lo_fabric_payloads_auth_native_true"
        )
        # Native boolean true preserved unnormalized.
        self.assertIs(sent["Loopback0"][self.OSPF_MD_NVPAIR], True)

    def test_dcnm_intf_lo_ospfmd_replaced_unrelated_update_preserves_false(self):
        _r, sent = self._ospfmd_run_unrelated_update(
            "replaced", "lo_fabric_payloads_auth_string_false"
        )
        self.assertEqual(sent["Loopback0"][self.OSPF_MD_NVPAIR], "false")

    def test_dcnm_intf_lo_ospfmd_bulk_unrelated_update_preserves_have_true(self):
        _r, sent = self._ospfmd_run_unrelated_update(
            "replaced", "lo_fabric_payloads_auth_string_true", bulk=True
        )
        self.assertEqual(sent["Loopback0"][self.OSPF_MD_NVPAIR], "true")

    def test_dcnm_intf_lo_ospfmd_replaced_unrelated_update_keeps_absent_absent(self):
        _r, sent = self._ospfmd_run_unrelated_update(
            "replaced", "lo_fabric_payloads_auth_absent"
        )
        # HAVE omits the key, so the outbound payload must omit it too, not
        # invent a false.
        self.assertNotIn(self.OSPF_MD_NVPAIR, sent["Loopback0"])

    def test_dcnm_intf_lo_ospfmd_unrelated_update_no_feature_diff(self):
        result, sent = self._ospfmd_run_unrelated_update(
            "replaced", "lo_fabric_payloads_auth_string_true"
        )
        # Present in the SENT payload (preservation)...
        self.assertEqual(sent["Loopback0"][self.OSPF_MD_NVPAIR], "true")
        # ...but NOT reported as a changed feature key in result['diff'].
        reported = self._ospfmd_nvpairs(result, "replaced")
        self.assertNotIn(self.OSPF_MD_NVPAIR, reported.get("Loopback0", {}))

    # ---- G6A.2 finding 6: the complete preservation matrix.
    # states x HAVE {absent, string/native false, string/native true, unexpected
    # string, unexpected scalar}, asserting the raw value/type is preserved
    # exactly in the sent payload, absence stays absence, the key is absent from
    # the reported diff, and omitted intent triggers zero template GETs. ----
    def test_dcnm_intf_lo_ospfmd_preservation_matrix(self):
        # (HAVE fixture key, expected preserved value or _ABSENT sentinel)
        _ABSENT = object()
        have_cases = [
            ("lo_fabric_payloads_auth_absent", _ABSENT),
            ("lo_fabric_payloads_auth_string_false", "false"),
            ("lo_fabric_payloads_auth_native_false", False),
            ("lo_fabric_payloads_auth_string_true", "true"),
            ("lo_fabric_payloads_auth_native_true", True),
            ("lo_fabric_payloads_auth_unexpected_str", "yes"),
            ("lo_fabric_payloads_auth_unexpected_scalar", 7),
        ]
        for state in ("merged", "replaced", "overridden"):
            for have_key, expected in have_cases:
                with self.subTest(state=state, have=have_key):
                    result, sent = self._ospfmd_run_unrelated_update(state, have_key)
                    lo0 = sent["Loopback0"]
                    if expected is _ABSENT:
                        # Absence must stay absence -- never invented as false.
                        self.assertNotIn(self.OSPF_MD_NVPAIR, lo0)
                    else:
                        # Raw value AND type preserved, unnormalized.
                        actual = lo0[self.OSPF_MD_NVPAIR]
                        self.assertEqual(actual, expected)
                        self.assertIs(type(actual), type(expected))
                    # Never in the reported feature diff.
                    reported = self._ospfmd_nvpairs(result, state)
                    self.assertNotIn(
                        self.OSPF_MD_NVPAIR, reported.get("Loopback0", {})
                    )
                    # Omitted intent triggers zero template metadata GETs.
                    self.assertEqual(
                        self.run_dcnm_template_details.call_count, 0
                    )

    def test_dcnm_intf_lo_ospfmd_preservation_matrix_bulk_path(self):
        for have_key, expected in [
            ("lo_fabric_payloads_auth_string_true", "true"),
            ("lo_fabric_payloads_auth_native_true", True),
            ("lo_fabric_payloads_auth_absent", None),
        ]:
            with self.subTest(have=have_key, path="bulk"):
                _r, sent = self._ospfmd_run_unrelated_update(
                    "replaced", have_key, bulk=True
                )
                if have_key.endswith("absent"):
                    self.assertNotIn(self.OSPF_MD_NVPAIR, sent["Loopback0"])
                else:
                    self.assertEqual(
                        sent["Loopback0"][self.OSPF_MD_NVPAIR], expected
                    )

    # ---- G6A.3 WS5: complete the omitted-HAVE matrix -----------------------
    def _ospfmd_run_update_with_have_value(self, raw_value, state="replaced"):
        """Unrelated (description) update on one omitted-feature loopback, with the
        HAVE nvPair overridden to an arbitrary raw value/type. Returns
        (result, sent)."""
        self._ospfmd_load_common(
            "lo_fabric_omitted_desc_change_config",
            "lo_fabric_payloads_auth_native_true",
        )
        self.fabric_lo_have = copy.deepcopy(self.fabric_lo_have)
        self.fabric_lo_have["DATA"][0]["interfaces"][0]["nvPairs"][
            self.OSPF_MD_NVPAIR
        ] = raw_value
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )
        set_module_args(
            dict(state=state, fabric="test_fabric", config=self.playbook_config)
        )
        result = self.execute_module(changed=True, failed=False)
        return result, self._ospfmd_sent_nvpairs()

    def test_dcnm_intf_lo_ospfmd_preservation_matrix_null_list_dict(self):
        # null, list and dictionary HAVE values are preserved raw and by type,
        # never folded into false or dropped, never in the reported feature diff,
        # and never trigger a capability GET.
        _MISSING = object()
        for raw in (None, ["true"], {"nested": True}):
            for state in ("merged", "replaced", "overridden"):
                with self.subTest(raw=repr(raw), state=state):
                    result, sent = self._ospfmd_run_update_with_have_value(raw, state)
                    actual = sent["Loopback0"].get(self.OSPF_MD_NVPAIR, _MISSING)
                    self.assertIsNot(actual, _MISSING)
                    self.assertEqual(actual, raw)
                    self.assertIs(type(actual), type(raw))
                    reported = self._ospfmd_nvpairs(result, state)
                    self.assertNotIn(
                        self.OSPF_MD_NVPAIR, reported.get("Loopback0", {})
                    )
                    self.assertEqual(
                        self.run_dcnm_template_details.call_count, 0
                    )

    def test_dcnm_intf_lo_ospfmd_omission_only_idempotent(self):
        # A config that omits the feature and otherwise matches HAVE is a true
        # no-op: no change, no mutation, and zero capability GETs.
        self._ospfmd_load_common(
            "lo_fabric_omitted_config", "lo_fabric_payloads_auth_string_true"
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )
        set_module_args(
            dict(state="replaced", fabric="test_fabric",
                 config=self.playbook_config)
        )
        self.execute_module(changed=False, failed=False)
        self.assertEqual(self.run_dcnm_template_details.call_count, 0)
        self.assert_no_mutating_dcnm_calls()

    def _ospfmd_sent_methods(self):
        return [
            call.args[1]
            for call in self.run_dcnm_send.call_args_list
            if len(call.args) > 1 and call.args[1] in ("POST", "PUT")
        ]

    def test_dcnm_intf_lo_ospfmd_preservation_individual_path_is_put(self):
        _r, sent = self._ospfmd_run_unrelated_update(
            "replaced", "lo_fabric_payloads_auth_string_true"
        )
        self.assertEqual(sent["Loopback0"][self.OSPF_MD_NVPAIR], "true")
        self.assertIn("PUT", self._ospfmd_sent_methods())

    def test_dcnm_intf_lo_ospfmd_preservation_bulk_path_is_post(self):
        _r, sent = self._ospfmd_run_unrelated_update(
            "replaced", "lo_fabric_payloads_auth_string_true", bulk=True
        )
        self.assertEqual(sent["Loopback0"][self.OSPF_MD_NVPAIR], "true")
        self.assertIn("POST", self._ospfmd_sent_methods())

    def test_dcnm_intf_lo_ospfmd_two_loopbacks_distinct_have_no_contamination(self):
        # Two loopbacks omitting the feature, with DISTINCT HAVE values, must each
        # preserve their own raw value -- no cross-loopback contamination.
        self._ospfmd_load_common(
            "lo_fabric_two_loopbacks_config",
            "lo_fabric_payloads_auth_native_true",
        )
        config = copy.deepcopy(
            self.config_data.get("lo_fabric_two_loopbacks_config")
        )
        for item in config:
            item["profile"].pop("enable_ospf_auth_message_digest", None)
            item["profile"]["description"] = "changed by test"
        self.playbook_config = config

        have = copy.deepcopy(self.fabric_lo_have)
        have["DATA"][0]["interfaces"][0]["nvPairs"][self.OSPF_MD_NVPAIR] = True
        lo1 = copy.deepcopy(have["DATA"][0])
        lo1["interfaces"][0]["ifName"] = "Loopback1"
        lo1["interfaces"][0]["nvPairs"]["INTF_NAME"] = "Loopback1"
        lo1["interfaces"][0]["nvPairs"]["IP"] = "10.3.0.1"
        lo1["interfaces"][0]["nvPairs"][self.OSPF_MD_NVPAIR] = False
        have["DATA"].append(lo1)
        self.fabric_lo_have = have

        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )
        set_module_args(
            dict(state="replaced", fabric="test_fabric",
                 config=self.playbook_config)
        )
        self.execute_module(changed=True, failed=False)
        sent = self._ospfmd_sent_nvpairs()
        self.assertIs(sent["Loopback0"][self.OSPF_MD_NVPAIR], True)
        self.assertIs(sent["Loopback1"][self.OSPF_MD_NVPAIR], False)

    def test_dcnm_intf_lo_ospfmd_replaced_explicit_true(self):
        self._ospfmd_load_common(
            "lo_fabric_explicit_true_config", "lo_fabric_payloads_auth_absent"
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        nvpairs = self._ospfmd_nvpairs(result, "replaced")
        self.assertIn("Loopback0", nvpairs)
        value = nvpairs["Loopback0"][self.OSPF_MD_NVPAIR]
        # Native JSON boolean, not the string "true".
        self.assertIsInstance(value, bool)
        self.assertIs(value, True)

    def test_dcnm_intf_lo_ospfmd_replaced_explicit_false_clears_true(self):
        self._ospfmd_load_common(
            "lo_fabric_explicit_false_config",
            "lo_fabric_payloads_auth_string_true",
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        nvpairs = self._ospfmd_nvpairs(result, "replaced")
        value = nvpairs["Loopback0"][self.OSPF_MD_NVPAIR]
        self.assertIsInstance(value, bool)
        self.assertIs(value, False)

    def test_dcnm_intf_lo_ospfmd_replaced_omitted_does_not_touch_the_value(self):
        """
        A1 contract: an omitted option emits nothing, in every state.

        This departs from the usual Ansible 'replaced' reading, where an
        unspecified option resets to the template default. It is deliberate. The
        option is capability-gated, and behavioral contract 1 requires that an
        omitted option neither changes behavior nor requires the capability. To
        reset on omission the module would have to classify the capability on
        every fabric-loopback payload, which would make two template GETs and a
        tri-state verdict a precondition for playbooks that never use the
        feature.

        The consequence is real and is reported as an A2 blocker rather than
        hidden: a true -> false transition expressed by REMOVING the option does
        not clear an already enabled child. Expressing it as an explicit false
        does, and that is asserted by
        test_dcnm_intf_lo_ospfmd_replaced_explicit_false*.
        """
        self._ospfmd_load_common(
            "lo_fabric_omitted_config", "lo_fabric_payloads_auth_string_true"
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(result["diff"][0]["replaced"], [])

    def test_dcnm_intf_lo_ospfmd_replaced_omitted_idempotent_absent_have(self):
        # HAVE omits the key entirely, which means the template default false.
        self._ospfmd_load_common(
            "lo_fabric_omitted_config", "lo_fabric_payloads_auth_absent"
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(result["diff"][0]["replaced"], [])
        self.assertEqual(result["diff"][0]["deploy"], [])

    def test_dcnm_intf_lo_ospfmd_replaced_omitted_idempotent_string_false_have(
        self,
    ):
        self._ospfmd_load_common(
            "lo_fabric_omitted_config", "lo_fabric_payloads_auth_string_false"
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(result["diff"][0]["replaced"], [])

    def test_dcnm_intf_lo_ospfmd_replaced_explicit_true_idempotent_string_true_have(
        self,
    ):
        self._ospfmd_load_common(
            "lo_fabric_explicit_true_config",
            "lo_fabric_payloads_auth_string_true",
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(result["diff"][0]["replaced"], [])

    def test_dcnm_intf_lo_ospfmd_replaced_explicit_true_idempotent_native_true_have(
        self,
    ):
        self._ospfmd_load_common(
            "lo_fabric_explicit_true_config",
            "lo_fabric_payloads_auth_native_true",
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(result["diff"][0]["replaced"], [])

    def test_dcnm_intf_lo_ospfmd_merged_omitted_preserves_have_true(self):
        self._ospfmd_load_common(
            "lo_fabric_omitted_config", "lo_fabric_payloads_auth_string_true"
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        # merged with the option omitted must never disable an enabled loopback.
        self.assertEqual(result["diff"][0]["merged"], [])
        self.assertEqual(result["diff"][0]["replaced"], [])

    def test_dcnm_intf_lo_ospfmd_merged_explicit_false_clears_true(self):
        self._ospfmd_load_common(
            "lo_fabric_explicit_false_config",
            "lo_fabric_payloads_auth_string_true",
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )

        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        nvpairs = self._ospfmd_nvpairs(result, "merged")
        self.assertIs(nvpairs["Loopback0"][self.OSPF_MD_NVPAIR], False)

    def test_dcnm_intf_lo_ospfmd_omitted_on_unsupported_controller(self):
        # Parent template exists but does not declare the parameter. Nothing is
        # requested explicitly, so the run must succeed and simply not carry the
        # unknown nvPair.
        self._ospfmd_load_common(
            "lo_fabric_omitted_config", "lo_fabric_payloads_auth_absent"
        )
        self._ospfmd_set_capability("mock_template_parent_without_param", None)

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        for bucket in ("merged", "replaced"):
            for d in result["diff"][0][bucket]:
                for intf in d["interfaces"]:
                    self.assertNotIn(self.OSPF_MD_NVPAIR, intf["nvPairs"])

    def test_dcnm_intf_lo_ospfmd_explicit_fails_on_ordinary_loopback(self):
        self._ospfmd_load_common(
            "lo_ordinary_explicit_true_config", "lo_merged_payloads_1"
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=True)

        self.assertIn("only for loopback interfaces with 'mode: fabric'", result["msg"])
        self.assertIn("given mode = 'lo'", result["msg"])
        # A local input error must never trigger a controller template lookup.
        self.assertEqual(self.run_dcnm_template_details.call_count, 0)
        self.assert_no_mutating_dcnm_calls()

    def test_dcnm_intf_lo_ospfmd_explicit_fails_on_mpls_loopback(self):
        self._ospfmd_load_common(
            "lo_mpls_explicit_true_config", "lo_merged_payloads_1"
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=True)

        self.assertIn("only for loopback interfaces with 'mode: fabric'", result["msg"])
        self.assertIn("given mode = 'mpls'", result["msg"])
        self.assertEqual(self.run_dcnm_template_details.call_count, 0)
        self.assert_no_mutating_dcnm_calls()

    def test_dcnm_intf_lo_ospfmd_overridden_omitted_does_not_touch_the_value(self):
        """
        A1 contract: an omitted option emits nothing, in every state.

        This departs from the usual Ansible 'overridden' reading, where an
        unspecified option resets to the template default. It is deliberate. The
        option is capability-gated, and behavioral contract 1 requires that an
        omitted option neither changes behavior nor requires the capability. To
        reset on omission the module would have to classify the capability on
        every fabric-loopback payload, which would make two template GETs and a
        tri-state verdict a precondition for playbooks that never use the
        feature.

        The consequence is real and is reported as an A2 blocker rather than
        hidden: a true -> false transition expressed by REMOVING the option does
        not clear an already enabled child. Expressing it as an explicit false
        does, and that is asserted by
        test_dcnm_intf_lo_ospfmd_overridden_explicit_false*.
        """
        self._ospfmd_load_common(
            "lo_fabric_omitted_config", "lo_fabric_payloads_auth_string_true"
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        # changed is True for reasons that have nothing to do with this feature:
        # 'overridden' deletes every interface absent from the config. What
        # matters here is that no interface UPDATE was produced, so the target
        # loopback's nvPair was left exactly as the controller had it.
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(result["diff"][0]["overridden"], [])
        for entry in result["diff"][0]["deleted"]:
            self.assertNotEqual(entry.get("ifName", "").lower(), "loopback0")

    def test_dcnm_intf_lo_ospfmd_query_issues_no_mutating_call(self):
        # state 'query' must be genuinely read-only, including the bulk-API
        # capability probe, which is a POST.
        self._ospfmd_load_common(
            "lo_fabric_omitted_config", "lo_fabric_payloads_auth_string_true"
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )

        set_module_args(
            dict(
                state="query",
                fabric="test_fabric",
                config=[
                    {
                        "name": "lo0",
                        "switch": ["192.168.1.108"],
                    }
                ],
            )
        )
        self.execute_module(changed=False, failed=False)

        self.assert_no_mutating_dcnm_calls()

    def test_dcnm_intf_lo_ospfmd_check_mode_issues_no_mutating_call(self):
        # check mode must compute the change without sending anything.
        self._ospfmd_load_common(
            "lo_fabric_explicit_true_config", "lo_fabric_payloads_auth_absent"
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
                _ansible_check_mode=True,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        nvpairs = self._ospfmd_nvpairs(result, "replaced")
        self.assertIs(nvpairs["Loopback0"][self.OSPF_MD_NVPAIR], True)
        self.assert_no_mutating_dcnm_calls()

    def test_dcnm_intf_lo_ospfmd_omitted_survives_metadata_exception(self):
        # A transport or parsing failure inside the template lookup must degrade
        # to "unavailable". A legacy run that never asks for the option must not
        # start crashing because the capability probe raised.
        self._ospfmd_load_common(
            "lo_fabric_omitted_config", "lo_fabric_payloads_auth_absent"
        )
        self.run_dcnm_template_details.side_effect = KeyError("RETURN_CODE")

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        for bucket in ("merged", "replaced"):
            for d in result["diff"][0][bucket]:
                for intf in d["interfaces"]:
                    self.assertNotIn(self.OSPF_MD_NVPAIR, intf["nvPairs"])

    def test_dcnm_intf_lo_ospfmd_omitted_survives_malformed_parameters(self):
        # parameters: [{}] must not raise while scanning for the parameter name.
        self._ospfmd_load_common(
            "lo_fabric_omitted_config", "lo_fabric_payloads_auth_absent"
        )
        self.run_dcnm_template_details.side_effect = None
        self.run_dcnm_template_details.return_value = {
            "name": "int_fabric_loopback_11_1",
            "parameters": [{}, "not-a-dict", {"name": "INTF_NAME"}],
        }

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        for bucket in ("merged", "replaced"):
            for d in result["diff"][0][bucket]:
                for intf in d["interfaces"]:
                    self.assertNotIn(self.OSPF_MD_NVPAIR, intf["nvPairs"])

    def test_dcnm_intf_lo_ospfmd_unknown_controller_value_is_not_idempotent(
        self,
    ):
        # An unrecognized controller representation must not fold into false and
        # be reported as already in sync; the module has to push the intent.
        self._ospfmd_load_common(
            "lo_fabric_explicit_false_config", "lo_fabric_payloads_auth_absent"
        )
        self.fabric_lo_have = copy.deepcopy(self.fabric_lo_have)
        self.fabric_lo_have["DATA"][0]["interfaces"][0]["nvPairs"][
            self.OSPF_MD_NVPAIR
        ] = "yes"
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )

        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        nvpairs = self._ospfmd_nvpairs(result, "replaced")
        self.assertIs(nvpairs["Loopback0"][self.OSPF_MD_NVPAIR], False)

    def test_dcnm_intf_lo_ospfmd_normalizer_tags_unknown_values(self):
        normalize = (
            dcnm_interface.DcnmIntf.dcnm_intf_normalize_ospf_auth_message_digest
        )
        self.assertEqual(normalize(None), "false")
        self.assertEqual(normalize(""), "false")
        self.assertEqual(normalize(False), "false")
        self.assertEqual(normalize("False"), "false")
        self.assertEqual(normalize(True), "true")
        self.assertEqual(normalize("TRUE"), "true")
        # Unknown representations stay distinguishable from both booleans, and
        # report only the value's category so arbitrary content cannot reach a
        # diff or a log line.
        for unknown in ("yes", "1", "invalid"):
            self.assertEqual(normalize(unknown), "unexpected:str")
        for unknown, category in ((1, "int"), (["true"], "list"), ({"v": 1}, "dict")):
            self.assertEqual(normalize(unknown), "unexpected:{0}".format(category))
        for unknown in ("yes", 1, ["true"], {"v": 1}):
            self.assertNotEqual(normalize(unknown), "false")
            self.assertNotEqual(normalize(unknown), "true")

    # ---- Durable metadata and lifecycle coverage ----

    @staticmethod
    def _ospfmd_parent(parameters):
        return {"name": "int_fabric_loopback_11_1", "parameters": parameters}

    @staticmethod
    def _ospfmd_target(parameter_type="boolean", default="false"):
        param = {"name": "ENABLE_OSPF_AUTH_MESSAGE_DIGEST",
                 "parameterType": parameter_type}
        if default is not None:
            param["metaProperties"] = {"defaultValue": default}
        return param

    def _ospfmd_expect_explicit_failure(self, parent, expected_fragment):
        """Explicit intent plus this metadata must fail closed and mutate nothing."""
        self._ospfmd_load_common(
            "lo_fabric_explicit_true_config", "lo_fabric_payloads_auth_absent"
        )
        self._ospfmd_set_capability(parent, "mock_template_child_supported")
        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertIn("Unsupported controller capability", result["msg"])
        self.assertIn(expected_fragment, result["msg"])
        self.assert_no_mutating_dcnm_calls()

    # ---- G6A.1 finding 6: reject a non-native-boolean value locally, before
    # any template GET and before any mutation. ----
    def _ospfmd_expect_local_type_failure(self, bad_value):
        self._ospfmd_load_common(
            "lo_fabric_omitted_config", "lo_fabric_payloads_auth_absent"
        )
        # Valid capability metadata is wired up, but it must NEVER be queried for
        # a malformed value: the type check runs first.
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )
        config = copy.deepcopy(self.config_data.get("lo_fabric_omitted_config"))
        config[0]["profile"]["enable_ospf_auth_message_digest"] = bad_value
        set_module_args(
            dict(state="merged", fabric="test_fabric", config=config)
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertIn("must be a native boolean", result["msg"])
        # Zero template GETs and zero bulk probe: the failure is purely local.
        self.assertEqual(self.run_dcnm_template_details.call_count, 0)
        self.assertEqual(self.run_dcnm_bulk_api_support.call_count, 0)
        self.assert_no_mutating_dcnm_calls()

    # ---- G6A.2 finding 5: a valid interface must not trigger a capability GET
    # before a later malformed interface fails (two-pass validation). ----
    def _ospfmd_expect_multi_local_failure(self, config_key):
        self._ospfmd_load_common(config_key, "lo_fabric_payloads_auth_absent")
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )
        set_module_args(
            dict(state="merged", fabric="test_fabric",
                 config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertIn("must be a native boolean", result["msg"])
        # Two-pass validation: the whole config is validated before any
        # capability lookup, so zero template GETs and zero bulk probe on either
        # ordering, and the "no template metadata was queried" message is true.
        self.assertEqual(self.run_dcnm_template_details.call_count, 0)
        self.assertEqual(self.run_dcnm_bulk_api_support.call_count, 0)
        self.assert_no_mutating_dcnm_calls()

    def test_dcnm_intf_lo_ospfmd_valid_then_invalid_zero_gets(self):
        self._ospfmd_expect_multi_local_failure(
            "lo_fabric_valid_then_invalid_config"
        )

    def test_dcnm_intf_lo_ospfmd_invalid_then_valid_zero_gets(self):
        self._ospfmd_expect_multi_local_failure(
            "lo_fabric_invalid_then_valid_config"
        )

    # ---- G6A.3 WS4: a malformed NON-feature field (ipv4_addr) must also fail
    # during local validation before the single capability GET, in either
    # ordering relative to a valid interface that requested the feature. ----
    def _ospfmd_expect_nonfeature_local_failure(self, bad_first):
        self._ospfmd_load_common(
            "lo_fabric_two_loopbacks_config", "lo_fabric_payloads_auth_absent"
        )
        # Valid capability metadata is wired up; it must NEVER be queried, because
        # a malformed local field fails the whole config first.
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )
        config = copy.deepcopy(
            self.config_data.get("lo_fabric_two_loopbacks_config")
        )
        # Both loopbacks validly request the feature; break one's ipv4_addr.
        config[0 if bad_first else 1]["profile"]["ipv4_addr"] = "not_an_ip"
        set_module_args(
            dict(state="merged", fabric="test_fabric", config=config)
        )
        result = self.execute_module(changed=False, failed=True)
        # WS4: full local validation precedes the capability GET, so zero template
        # GETs and zero bulk probe regardless of ordering.
        self.assertEqual(self.run_dcnm_template_details.call_count, 0)
        self.assertEqual(self.run_dcnm_bulk_api_support.call_count, 0)
        self.assert_no_mutating_dcnm_calls()

    def test_dcnm_intf_lo_ospfmd_bad_ipv4_before_valid_feature_zero_gets(self):
        self._ospfmd_expect_nonfeature_local_failure(bad_first=True)

    def test_dcnm_intf_lo_ospfmd_valid_feature_before_bad_ipv4_zero_gets(self):
        self._ospfmd_expect_nonfeature_local_failure(bad_first=False)

    # ---- G6A.4 finding 4: the feature is validated GLOBALLY; the field is
    # rejected on any non-fabric-loopback interface with zero template GETs. ----
    def _ospfmd_reject_nonloopback(self, config, fragment):
        self._ospfmd_load_common(
            "lo_fabric_omitted_config", "lo_fabric_payloads_auth_absent"
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )
        set_module_args(
            dict(state="merged", fabric="test_fabric", config=config)
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertIn(fragment, result["msg"])
        self.assertEqual(self.run_dcnm_template_details.call_count, 0)
        self.assertEqual(self.run_dcnm_bulk_api_support.call_count, 0)
        self.assert_no_mutating_dcnm_calls()

    def test_dcnm_intf_lo_ospfmd_field_on_ethernet_rejected_zero_gets(self):
        # non-loopback interface type carrying the field -> rejected globally,
        # before any capability GET, even though a loopback is also present.
        config = [
            {"name": "lo0", "type": "lo", "switch": ["192.168.1.108"],
             "deploy": "False",
             "profile": {"mode": "fabric", "ipv4_addr": "10.2.0.1",
                         "enable_ospf_auth_message_digest": True}},
            {"name": "eth1/1", "type": "eth", "switch": ["192.168.1.108"],
             "deploy": "False",
             "profile": {"mode": "trunk",
                         "enable_ospf_auth_message_digest": True}},
        ]
        self._ospfmd_reject_nonloopback(config, "only on fabric loopback")

    def test_dcnm_intf_lo_ospfmd_field_on_ethernet_only_rejected_globally(self):
        # no loopback at all: the loopback-only validator would never run, so the
        # global validation is what rejects it.
        config = [
            {"name": "eth1/1", "type": "eth", "switch": ["192.168.1.108"],
             "deploy": "False",
             "profile": {"mode": "trunk",
                         "enable_ospf_auth_message_digest": False}},
        ]
        self._ospfmd_reject_nonloopback(config, "only on fabric loopback")

    def test_dcnm_intf_lo_ospfmd_field_on_ordinary_loopback_rejected(self):
        # type lo but mode 'lo' (ordinary loopback) -> rejected by the mode check.
        config = [
            {"name": "lo9", "type": "lo", "switch": ["192.168.1.108"],
             "deploy": "False",
             "profile": {"mode": "lo", "ipv4_addr": "10.9.0.1",
                         "enable_ospf_auth_message_digest": True}},
        ]
        self._ospfmd_reject_nonloopback(config, "mode: fabric")

    def test_dcnm_intf_lo_ospfmd_have_get_failure_fails_closed(self):
        # G6A.4 finding 2 (end to end): when every fabric-loopback interface GET
        # fails, the module must FAIL CLOSED, not read unknown state as absence
        # and POST a create.
        self._ospfmd_load_common(
            "lo_fabric_explicit_true_config", "lo_fabric_payloads_auth_absent"
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )
        set_module_args(
            dict(state="merged", fabric="test_fabric",
                 config=self.playbook_config)
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertIn("could not be read", result["msg"])
        self.assert_no_mutating_dcnm_calls()

    def test_dcnm_intf_lo_ospfmd_explicit_null_fails_locally(self):
        self._ospfmd_expect_local_type_failure(None)

    def test_dcnm_intf_lo_ospfmd_string_true_fails_locally(self):
        self._ospfmd_expect_local_type_failure("true")

    def test_dcnm_intf_lo_ospfmd_integer_one_fails_locally(self):
        self._ospfmd_expect_local_type_failure(1)

    def test_dcnm_intf_lo_ospfmd_list_fails_locally(self):
        self._ospfmd_expect_local_type_failure(["true"])

    def test_dcnm_intf_lo_ospfmd_dict_fails_locally(self):
        self._ospfmd_expect_local_type_failure({"v": True})

    # ---- G6A.1 finding 8: the lazy bulk-API probe runs at most once and selects
    # the update path. ----
    def _ospfmd_update_methods(self, bulk):
        """Update an EXISTING fabric loopback (so it takes the replace path) and
        return the methods used against the interface-update endpoint."""
        self._ospfmd_load_common(
            "lo_fabric_omitted_desc_change_config",
            "lo_fabric_payloads_auth_string_true",
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )
        self.run_dcnm_bulk_api_support.return_value = bulk
        set_module_args(
            dict(state="replaced", fabric="test_fabric",
                 config=self.playbook_config)
        )
        self.execute_module(changed=True, failed=False)
        return [
            call.args[1]
            for call in self.run_dcnm_send.call_args_list
            if len(call.args) >= 4
            and "interface" in call.args[2].lower()
            and call.args[1] in ("POST", "PUT")
        ]

    def test_dcnm_intf_lo_ospfmd_bulk_probe_runs_once_on_update(self):
        self._ospfmd_update_methods(True)
        self.assertEqual(self.run_dcnm_bulk_api_support.call_count, 1)

    def test_dcnm_intf_lo_ospfmd_bulk_true_selects_bulk_post(self):
        methods = self._ospfmd_update_methods(True)
        # Bulk update is a POST to the bulk endpoint.
        self.assertIn("POST", methods)
        self.assertNotIn("PUT", methods)

    def test_dcnm_intf_lo_ospfmd_bulk_false_selects_individual_put(self):
        methods = self._ospfmd_update_methods(False)
        # Individual update is a PUT per interface.
        self.assertIn("PUT", methods)

    def test_dcnm_intf_lo_ospfmd_explicit_false_on_unsupported_is_noop_when_have_absent(self):
        # G6A.3 WS3: explicit false on a non-supported controller must NOT fail
        # closed. The unknown nvPair is never sent; with an absent/false HAVE the
        # feature is already off, so the run is an idempotent no-op.
        self._ospfmd_load_common(
            "lo_fabric_explicit_false_config", "lo_fabric_payloads_auth_absent"
        )
        self._ospfmd_set_capability("mock_template_parent_without_param", None)
        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        # the unknown nvPair is never handed to the legacy controller
        for bucket in ("merged", "replaced"):
            for d in result["diff"][0][bucket]:
                for intf in d["interfaces"]:
                    self.assertNotIn(self.OSPF_MD_NVPAIR, intf["nvPairs"])
        self.assert_no_mutating_dcnm_calls()

    def test_dcnm_intf_lo_ospfmd_explicit_false_on_unavailable_is_noop_when_have_absent(self):
        # Metadata unavailable (unreadable): explicit false still must not fail;
        # never send the field, and a false/absent HAVE is a compatibility no-op.
        self._ospfmd_load_common(
            "lo_fabric_explicit_false_config", "lo_fabric_payloads_auth_absent"
        )
        self._ospfmd_set_capability(None, None)
        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        for bucket in ("merged", "replaced"):
            for d in result["diff"][0][bucket]:
                for intf in d["interfaces"]:
                    self.assertNotIn(self.OSPF_MD_NVPAIR, intf["nvPairs"])
        self.assert_no_mutating_dcnm_calls()

    def test_dcnm_intf_lo_ospfmd_explicit_false_on_unsupported_have_true_fails(self):
        # G6A.3 WS3: explicit false to CLEAR the feature, but the controller
        # cannot manage the nvPair and reports it ON. The module must fail loudly
        # rather than silently claim success -- it cannot clear the feature
        # without a parent template that declares the parameter.
        self._ospfmd_load_common(
            "lo_fabric_explicit_false_config",
            "lo_fabric_payloads_auth_native_true",
        )
        self._ospfmd_set_capability("mock_template_parent_without_param", None)
        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertIn("cannot be cleared", result["msg"])
        self.assert_no_mutating_dcnm_calls()

    def test_dcnm_intf_lo_ospfmd_duplicate_have_fails_with_zero_mutation(self):
        self._ospfmd_load_common(
            "lo_fabric_explicit_false_config",
            "lo_fabric_payloads_auth_string_false",
        )
        self.fabric_lo_have = copy.deepcopy(self.fabric_lo_have)
        group = self.fabric_lo_have["DATA"][0]
        group["policy"] = "int_loopback"
        duplicate = copy.deepcopy(group["interfaces"][0])
        duplicate["ifName"] = duplicate["ifName"].lower()
        duplicate["nvPairs"][self.OSPF_MD_NVPAIR] = "true"
        group["interfaces"].append(duplicate)
        self._ospfmd_set_capability("mock_template_parent_without_param", None)
        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertTrue(
            "could not be read" in result["msg"]
            or "could not be determined" in result["msg"]
        )
        self.assert_no_mutating_dcnm_calls()

    def test_dcnm_intf_lo_ospfmd_check_mode_unsupported_fails_closed(self):
        self._ospfmd_load_common(
            "lo_fabric_explicit_true_config", "lo_fabric_payloads_auth_absent"
        )
        self._ospfmd_set_capability("mock_template_parent_without_param", None)
        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
                _ansible_check_mode=True,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        self.assertIn("Unsupported controller capability", result["msg"])
        self.assert_no_mutating_dcnm_calls()

    def test_dcnm_intf_lo_ospfmd_overridden_explicit_true(self):
        self._ospfmd_load_common(
            "lo_fabric_explicit_true_config", "lo_fabric_payloads_auth_absent"
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )
        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        nvpairs = self._ospfmd_nvpairs(result, "overridden")
        self.assertIs(nvpairs["Loopback0"][self.OSPF_MD_NVPAIR], True)

    def test_dcnm_intf_lo_ospfmd_overridden_explicit_false(self):
        self._ospfmd_load_common(
            "lo_fabric_explicit_false_config",
            "lo_fabric_payloads_auth_string_true",
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )
        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)
        nvpairs = self._ospfmd_nvpairs(result, "overridden")
        self.assertIs(nvpairs["Loopback0"][self.OSPF_MD_NVPAIR], False)

    def test_dcnm_intf_lo_ospfmd_no_diff_run_issues_no_mutating_call(self):
        # Already in sync: the module must not reach the bulk-API probe, which
        # is a POST, nor send any mutating verb.
        self._ospfmd_load_common(
            "lo_fabric_explicit_true_config",
            "lo_fabric_payloads_auth_string_true",
        )
        self._ospfmd_set_capability(
            "mock_template_parent_supported", "mock_template_child_supported"
        )
        set_module_args(
            dict(
                state="replaced",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)
        self.assertEqual(result["diff"][0]["replaced"], [])
        self.assert_no_mutating_dcnm_calls()

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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        for cfg in self.playbook_config:
            cfg["deploy"] = "False"
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )

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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
            "ENABLE_LACP_VPC_CONV",
            "DISABLE_LACP_SUSPEND",
            "LACP_PORT_PRIO",
            "LACP_RATE",
            "ENABLE_QOS",
            "QOS_POLICY",
            "QUEUING_POLICY",
            "COPY_DESC",
            "ENABLE_STORM_CONTROL",
            "STORM_CONTROL_ACTION",
            "STORM_CONTROL_BCAST_LEVEL_PERCENT",
            "STORM_CONTROL_BCAST_LEVEL_PPS",
            "STORM_CONTROL_MCAST_LEVEL_PERCENT",
            "STORM_CONTROL_MCAST_LEVEL_PPS",
            "STORM_CONTROL_UCAST_LEVEL_PERCENT",
            "STORM_CONTROL_UCAST_LEVEL_PPS",
            "CDP_ENABLE",
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        ovr_if_names = ["vpc750"]

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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.playbook_config = self.config_data.get(
            "aa_fex_merge_existing_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.playbook_config = self.config_data.get(
            "aa_fex_merge_multi_switches_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
            "PEER1_PCID",
            "PEER2_PCID",
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
        self.playbook_config = self.config_data.get(
            "aa_fex_overridden_new_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.playbook_config = self.config_data.get(
            "aa_fex_overridden_modify_existing_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.playbook_config = self.config_data.get(
            "st_fex_merge_existing_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.playbook_config = self.config_data.get(
            "st_fex_merge_multi_switches_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.playbook_config = self.config_data.get(
            "st_fex_overridden_new_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.playbook_config = self.config_data.get(
            "st_fex_overridden_modify_existing_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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

    def test_dcnm_intf_override_pc_intf_types_only(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_common_configs")
        self.payloads_data = []
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                override_intf_types=["pc"],
                deploy=False,
                config=[],
            )
        )
        result = self.execute_module(changed=True, failed=False)

        del_if_names = [
            "port-channel301",
            "port-channel302",
            "port-channel303",
            "port-channel300",
        ]
        rep_if_names = []
        ovr_if_names = []

        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"].lower() in del_if_names), True)

        self.assertEqual(len(result["diff"][0]["deleted"]), 4)
        self.assertEqual(len(result["diff"][0]["replaced"]), 0)
        self.assertEqual(len(result["diff"][0]["overridden"]), 0)

    def test_dcnm_intf_override_pc_intf_types_with_new_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_common_configs")
        self.payloads_data = []
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("pc_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                override_intf_types=["pc"],
                deploy=False,
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        del_if_names = [
            "port-channel301",
            "port-channel302",
            "port-channel303",
            "port-channel300",
        ]
        rep_if_names = []
        ovr_if_names = ["port-channel900"]

        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"].lower() in del_if_names), True)

        for intf in result["diff"][0]["overridden"]:
            self.assertEqual(
                (intf["interfaces"][0]["ifName"].lower() in ovr_if_names), True
            )

        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["replaced"]), 0)
        self.assertEqual(len(result["diff"][0]["overridden"]), 1)
        self.assertEqual(len(result["diff"][0]["merged"]), 0)

    def test_dcnm_intf_eth_overridden_existing_fec_only(self):
        self.config_data = loadPlaybookData("dcnm_intf_eth_configs")
        self.payloads_data = copy.deepcopy(
            loadPlaybookData("dcnm_intf_eth_payloads")
        )
        self.have_all_payloads_data = copy.deepcopy(
            loadPlaybookData("dcnm_intf_have_all_payloads")
        )
        self.playbook_config = self.config_data.get(
            "eth_overridden_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        for switch in self.mock_fab_inv.values():
            switch["switchRole"] = "leaf"
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")
        self.set_eth_overridden_payloads_to_role_default(
            fec_interface="Ethernet3/2"
        )

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                config=self.playbook_config,
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(
            len(result["diff"][0]["replaced"]), 1, result
        )
        replacement = result["diff"][0]["replaced"][0]
        self.assertEqual(
            replacement["interfaces"][0]["ifName"], "Ethernet3/2"
        )
        self.assertEqual(
            replacement["interfaces"][0]["nvPairs"]["FEC"], "auto"
        )

    def test_dcnm_intf_override_all_but_eth_intf_types_only(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_common_configs")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get(
            "override_all_but_eth_only_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                override_intf_types=["pc", "sub_int", "vpc", "lo", "svi"],
                deploy=False,
                config=[],
            )
        )
        result = self.execute_module(changed=True, failed=False)

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
        rep_if_names = []
        ovr_if_names = []

        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"].lower() in del_if_names), True)

        self.assertEqual(len(result["diff"][0]["deleted"]), 8)
        self.assertEqual(len(result["diff"][0]["replaced"]), 0)
        self.assertEqual(len(result["diff"][0]["overridden"]), 0)

    def test_dcnm_intf_override_svi_intf_types_only(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_common_configs")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("override_svi_only_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                override_intf_types=["svi"],
                deploy=False,
                config=[],
            )
        )
        result = self.execute_module(changed=True, failed=False)

        del_if_names = ["vlan2001"]
        ovr_if_names = []
        rep_if_names = []

        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"].lower() in del_if_names), True)

        self.assertEqual(len(result["diff"][0]["deleted"]), 1)
        self.assertEqual(len(result["diff"][0]["replaced"]), 0)
        self.assertEqual(len(result["diff"][0]["overridden"]), 0)

    def test_dcnm_intf_override_vpc_intf_types_only(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_common_configs")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("override_vpc_only_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                override_intf_types=["vpc"],
                deploy=False,
                config=[],
            )
        )
        result = self.execute_module(changed=True, failed=False)

        del_if_names = ["vpc300"]
        ovr_if_names = []
        rep_if_names = []

        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"].lower() in del_if_names), True)

        self.assertEqual(len(result["diff"][0]["deleted"]), 1)
        self.assertEqual(len(result["diff"][0]["replaced"]), 0)
        self.assertEqual(len(result["diff"][0]["overridden"]), 0)

    def test_dcnm_intf_override_eth_intf_types_only(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_common_configs")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("override_eth_only_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        for switch in self.mock_fab_inv.values():
            switch["switchRole"] = "leaf"
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                override_intf_types=["eth"],
                deploy=False,
                config=[],
            )
        )
        result = self.execute_module(changed=True, failed=False)

        ovr_if_names = []
        del_if_names = []
        rep_if_names = ["ethernet1/1", "ethernet1/2", "ethernet3/2"]

        for intf in result["diff"][0]["replaced"]:
            self.assertEqual(
                (intf["interfaces"][0]["ifName"].lower() in rep_if_names), True
            )

        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["replaced"]), 3)
        self.assertEqual(len(result["diff"][0]["overridden"]), 0)
        self.assert_leaf_default_storm_control(
            result["diff"][0]["replaced"]
        )

    def test_dcnm_intf_override_eth_intf_types_only_deleted_nd42(self):

        self.prepare_nd42_deleted_all_eth_test()

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                override_intf_types=["eth"],
                deploy=False,
                config=[],
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["replaced"]), 3)
        self.assertEqual(len(result["diff"][0]["skipped"]), 0)

    def test_dcnm_intf_override_eth_intf_types_only_deleted_nd42_fec_only(
        self,
    ):

        self.prepare_nd42_deleted_all_eth_test()
        for switch in self.mock_fab_inv.values():
            switch["switchRole"] = "leaf"
        self.set_eth_overridden_payloads_to_role_default(
            fec_interface="Ethernet3/2"
        )

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                override_intf_types=["eth"],
                deploy=False,
                config=[],
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["replaced"]), 1)
        replacement = result["diff"][0]["replaced"][0]
        self.assertEqual(
            replacement["interfaces"][0]["ifName"], "Ethernet3/2"
        )
        self.assertEqual(
            replacement["interfaces"][0]["nvPairs"]["FEC"], "auto"
        )

    def test_dcnm_intf_override_eth_intf_types_only_deleted_nd42_fail_closed(
        self,
    ):

        invalid_capabilities = [
            ("missing deletable", None, False, True, False),
            ("null deletable", None, False, False, False),
            ("blank deletable", "", False, False, False),
            ("numeric zero deletable", 0, False, False, False),
            ("unknown deletable", "unknown", False, False, False),
            ("both false", False, False, False, False),
            ("both missing", None, None, True, True),
        ]

        for (
            description,
            deletable,
            edit_allowed,
            omit_deletable,
            omit_edit_allowed,
        ) in invalid_capabilities:
            with self.subTest(description):
                self.prepare_nd42_deleted_all_eth_test(
                    deletable=deletable,
                    edit_allowed=edit_allowed,
                    omit_deletable=omit_deletable,
                    omit_edit_allowed=omit_edit_allowed,
                )

                set_module_args(
                    dict(
                        state="deleted",
                        fabric="test_fabric",
                        override_intf_types=["eth"],
                        deploy=False,
                        config=[],
                    )
                )
                result = self.execute_module(changed=False, failed=False)

                self.assertEqual(len(result["diff"][0]["deleted"]), 0)
                self.assertEqual(len(result["diff"][0]["replaced"]), 0)
                self.assertEqual(len(result["diff"][0]["deploy"]), 0)
                self.assertEqual(len(result["diff"][0]["skipped"]), 3)
                self.assertTrue(
                    all(
                        skipped["Reason"]
                        == (
                            "Physical interface reset is not allowed because "
                            "neither deletable nor editAllowed is true"
                        )
                        for skipped in result["diff"][0]["skipped"]
                    )
                )
                self.assertFalse(result.get("response"))
                self.assert_no_mutating_dcnm_calls()

    def test_dcnm_intf_override_eth_intf_types_only_deleted_nd42_capability_true(
        self,
    ):

        valid_capabilities = [
            ("boolean deletable", True, False, False, False),
            ("string deletable", " TRUE ", None, False, True),
            ("boolean edit allowed", False, True, False, False),
            ("string edit allowed", None, " TRUE ", True, False),
        ]

        for (
            description,
            deletable,
            edit_allowed,
            omit_deletable,
            omit_edit_allowed,
        ) in valid_capabilities:
            with self.subTest(description):
                self.prepare_nd42_deleted_all_eth_test(
                    deletable=deletable,
                    edit_allowed=edit_allowed,
                    omit_deletable=omit_deletable,
                    omit_edit_allowed=omit_edit_allowed,
                )

                set_module_args(
                    dict(
                        state="deleted",
                        fabric="test_fabric",
                        override_intf_types=["eth"],
                        deploy=False,
                        config=[],
                    )
                )
                result = self.execute_module(changed=True, failed=False)

                self.assertEqual(len(result["diff"][0]["replaced"]), 3)
                self.assertEqual(len(result["diff"][0]["skipped"]), 0)

    def test_dcnm_intf_override_eth_intf_types_only_deleted_nd42_check_mode(
        self,
    ):

        self.prepare_nd42_deleted_all_eth_test()

        set_module_args(
            dict(
                state="deleted",
                _ansible_check_mode=True,
                fabric="test_fabric",
                override_intf_types=["eth"],
                deploy=False,
                config=[],
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["replaced"]), 3)
        self.assertFalse(result.get("response"))
        self.assert_no_mutating_dcnm_calls()

    def test_dcnm_intf_override_eth_intf_types_only_deleted_nd42_switch_only(
        self,
    ):

        self.prepare_nd42_deleted_all_eth_test()

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                override_intf_types=["eth"],
                deploy=False,
                config=[
                    {
                        "switch": ["192.168.1.108"],
                        "deploy": False,
                    }
                ],
            )
        )
        result = self.execute_module(changed=True, failed=False)

        replaced_names = {
            payload["interfaces"][0]["ifName"]
            for payload in result["diff"][0]["replaced"]
        }
        self.assertEqual(
            replaced_names,
            {"Ethernet1/1", "Ethernet1/2", "Ethernet3/2"},
        )
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["skipped"]), 0)

    def test_dcnm_intf_override_eth_intf_types_only_deleted_nd42_switch_only_fail_closed(
        self,
    ):

        self.prepare_nd42_deleted_all_eth_test(
            edit_allowed=False,
            omit_deletable=True,
        )

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                override_intf_types=["eth"],
                deploy=False,
                config=[
                    {
                        "switch": ["192.168.1.108"],
                        "deploy": False,
                    }
                ],
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["replaced"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)
        self.assertEqual(len(result["diff"][0]["skipped"]), 3)
        self.assertTrue(
            all(
                skipped["Reason"]
                == (
                    "Physical interface reset is not allowed because neither "
                    "deletable nor editAllowed is true"
                )
                for skipped in result["diff"][0]["skipped"]
            )
        )
        self.assertFalse(result.get("response"))
        self.assert_no_mutating_dcnm_calls()

    def test_dcnm_intf_override_eth_intf_types_only_deleted_nd42_switch_only_check_mode(
        self,
    ):

        self.prepare_nd42_deleted_all_eth_test()

        set_module_args(
            dict(
                state="deleted",
                _ansible_check_mode=True,
                fabric="test_fabric",
                override_intf_types=["eth"],
                deploy=False,
                config=[
                    {
                        "switch": ["192.168.1.108"],
                        "deploy": False,
                    }
                ],
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["replaced"]), 3)
        self.assertFalse(result.get("response"))
        self.assert_no_mutating_dcnm_calls()

    def test_dcnm_intf_override_eth_intf_types_only_deleted_nd42_dependency(
        self,
    ):

        self.prepare_nd42_deleted_all_eth_test()
        for intf in self.have_all_payloads_data["payloads"]["DATA"]:
            if intf["ifName"] == "Ethernet1/1":
                intf.pop("deletable", None)
                intf["underlayPolicies"] = [
                    {"source": "port-channel300"}
                ]

        set_module_args(
            dict(
                state="deleted",
                fabric="test_fabric",
                override_intf_types=["eth"],
                deploy=False,
                config=[],
            )
        )
        result = self.execute_module(changed=True, failed=False)

        replaced_names = {
            payload["interfaces"][0]["ifName"]
            for payload in result["diff"][0]["replaced"]
        }
        self.assertEqual(
            replaced_names,
            {"Ethernet1/2", "Ethernet3/2"},
        )
        self.assertTrue(
            any(
                deferred["Name"] == "Ethernet1/1"
                and deferred["Source"] == "port-channel300"
                for deferred in result["diff"][0]["deferred"]
            )
        )

    def test_dcnm_intf_override_eth_intf_types_skip_non_resolvable_deferred(
        self,
    ):

        self.config_data = loadPlaybookData("dcnm_intf_common_configs")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        self.playbook_config = self.config_data.get("override_eth_only_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                override_intf_types=["eth"],
                deploy=False,
                config=[],
            )
        )
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deferred"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["replaced"]), 2)
        self.assertEqual(len(result["diff"][0]["overridden"]), 0)

        self.assertEqual(
            {
                intf["interfaces"][0]["ifName"].lower()
                for intf in result["diff"][0]["replaced"]
            },
            {"ethernet1/2", "ethernet3/2"},
        )
        self.assertTrue(
            any(
                intf["Name"].lower() == "ethernet1/1"
                and intf["Reason"]
                == "Non-deletable interface without resolvable underlay policy source"
                for intf in result["diff"][0]["skipped"]
            )
        )

    def test_dcnm_intf_override_sub_int_intf_types_only(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_common_configs")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get(
            "override_sub_int_only_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                override_intf_types=["sub_int"],
                deploy=False,
                config=[],
            )
        )
        result = self.execute_module(changed=True, failed=False)

        rep_if_names = []
        ovr_if_names = []
        del_if_names = ["ethernet1/3.2"]

        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"].lower() in del_if_names), True)

        self.assertEqual(len(result["diff"][0]["deleted"]), 1)
        self.assertEqual(len(result["diff"][0]["replaced"]), 0)
        self.assertEqual(len(result["diff"][0]["overridden"]), 0)

    def test_dcnm_intf_override_lo_intf_types_only(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_common_configs")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get("override_lo_only_config")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
        self.playbook_mock_vpc_resp = self.config_data.get("mock_vpc_resp")

        set_module_args(
            dict(
                state="overridden",
                fabric="test_fabric",
                override_intf_types=["lo"],
                deploy=False,
                config=[],
            )
        )
        result = self.execute_module(changed=True, failed=False)

        rep_if_names = []
        ovr_if_names = []
        del_if_names = ["loopback200"]

        for intf in result["diff"][0]["deleted"]:
            self.assertEqual((intf["ifName"].lower() in del_if_names), True)

        self.assertEqual(len(result["diff"][0]["deleted"]), 1)
        self.assertEqual(len(result["diff"][0]["replaced"]), 0)
        self.assertEqual(len(result["diff"][0]["overridden"]), 0)

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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )

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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )

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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )

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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
            self.assertEqual(
                ("No changes are allowed on the fabric" in str(e)), True
            )

    def test_dcnm_intf_merge_unmanagable_switch(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_intf_pc_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_pc_payloads")
        self.have_all_payloads_data = loadPlaybookData(
            "dcnm_intf_have_all_payloads"
        )

        # load required config data
        self.playbook_config = self.config_data.get(
            "pc_unmanagable_merged_config"
        )
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_true_resp = self.config_data.get(
            "mock_monitor_true_resp"
        )
        self.mock_monitor_false_resp = self.config_data.get(
            "mock_monitor_false_resp"
        )
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
            self.assertEqual(
                ("No changes are allowed on these switches" in str(e)), True
            )
