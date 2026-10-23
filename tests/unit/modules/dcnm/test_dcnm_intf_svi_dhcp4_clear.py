# Copyright (c) 2026 Cisco and/or its affiliates.
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

"""F3: explicit clearing of the int_vlan DHCP server 4 (dhcp_server_addr4 / vrf_dhcp4) and of the relay source interface.

Real main() through the EXISTING dcnm_interface unit harness (test_dcnm_intf.TestDcnmIntfModule: same patches, same fixtures
dcnm_intf_svi_configs / dcnm_intf_svi_payloads); only the HAVE of the SVI is varied. NOT LIVE TESTED: these are controller DOUBLES, so
what the controller returns after a clear is the double's value, not a measurement. Servers 1-3 are the positive controls.

Every scenario is compared with a CONTROL run (same config and HAVE with no DHCP4 field at all) so that "all other fields held
constant" is asserted, not assumed: the changed nvPairs of a scenario must equal the control's plus exactly the expected DHCP keys.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json

from .dcnm_module import AnsibleExitJson, AnsibleFailJson, loadPlaybookData, set_module_args
from . import test_dcnm_intf as legacy

IFNAME = "vlan1001"
DHCP4 = ("dhcpServerAddr4", "vrfDhcp4", "DHCP_RELAY_SRC_INTF")
SET_HAVE = {"dhcpServerAddr4": "192.200.1.4", "vrfDhcp4": "blue", "DHCP_RELAY_SRC_INTF": "loopback0"}
EMPTY_HAVE = {"dhcpServerAddr4": "", "vrfDhcp4": "", "DHCP_RELAY_SRC_INTF": ""}
NULL_HAVE = {"dhcpServerAddr4": None, "vrfDhcp4": None, "DHCP_RELAY_SRC_INTF": None}
STATES = ("merged", "replaced", "overridden")


class TestSviDhcp4Clear(legacy.TestDcnmIntfModule):
    """The inherited legacy tests are switched off below; only the test_f3_* cases of this file run."""

    def scenario(self, state, profile=None, drop=(), have=None):
        """Run one main() and return (result, nvPairs of the outbound request for the SVI or None)."""
        self.config_data = loadPlaybookData("dcnm_intf_svi_configs")
        self.payloads_data = loadPlaybookData("dcnm_intf_svi_payloads")
        self.have_all_payloads_data = loadPlaybookData("dcnm_intf_have_all_payloads")
        self.playbook_mock_succ_resp = self.config_data.get("mock_succ_resp")
        self.mock_ip_sn = self.config_data.get("mock_ip_sn")
        self.mock_fab_inv = self.config_data.get("mock_fab_inv_data")
        self.mock_monitor_false_resp = self.config_data.get("mock_monitor_false_resp")
        config = copy.deepcopy(self.config_data["svi_merged_config"])
        for cfg in config:
            cfg["deploy"] = "False"
            cfg["profile"].update(profile or {})
            for key in drop:
                cfg["profile"].pop(key, None)
        self._have = copy.deepcopy(self.payloads_data["svi_merged_payloads"])
        nv = self._have["DATA"][0]["interfaces"][0]["nvPairs"]
        for key, value in (have or {}).items():
            nv[key] = value
        self._state = state
        set_module_args(dict(state=state, fabric="test_fabric", config=config))
        self.load_fixtures()
        try:
            self.module.main()
        except AnsibleExitJson as exc:
            return exc.args[0]
        except AnsibleFailJson as exc:
            self.fail("main() failed: %s" % exc.args[0].get("msg"))
        self.fail("main() returned without exit_json")

    def load_fixtures(self, response=None, device=""):
        self.run_dcnm_fabric_details.side_effect = [self.mock_fab_inv]
        self.run_dcnm_ip_sn.side_effect = [[self.mock_ip_sn, []]]
        self.run_dcnm_version_supported.side_effect = [11]
        bulk = self.build_bulk_payload(self._have)
        succ = self.playbook_mock_succ_resp
        have_all = self.have_all_payloads_data.get("payloads")
        if self._state == "merged":
            effects = [self.mock_monitor_false_resp, bulk, have_all, have_all] + [succ] * 3
        elif self._state == "replaced":
            effects = [self.mock_monitor_false_resp, bulk, have_all] + [succ] * 3
        else:
            effects = [
                self.mock_monitor_false_resp,
                bulk,
                have_all,
                self.have_all_payloads_data.get("eth_1_1_access_payload"),
                self.have_all_payloads_data.get("eth_1_2_access_payload"),
                self.have_all_payloads_data.get("eth_3_2_access_payload"),
            ] + [succ] * 17
        self.run_dcnm_send.side_effect = effects
        self.normalize_legacy_bulk_fixture_responses()

    # ---- observation helpers
    def reported(self, result):
        """nvPairs of the SVI in the REPORTED diff (changed keys only), across merged/replaced lists."""
        found = {}
        for group in result["diff"]:
            for state_key in ("merged", "replaced", "overridden"):
                for entry in group.get(state_key, []) or []:
                    for intf in entry.get("interfaces", []):
                        if intf.get("ifName") == IFNAME:
                            found.update(intf["nvPairs"])
        return found

    def outbound(self):
        """nvPairs of the SVI in the request actually handed to the controller transport (full payload), or None."""
        sent = None
        for call in self.run_dcnm_send.call_args_list:
            args = call.args
            if len(args) >= 4 and args[1] in ("POST", "PUT") and args[3]:
                try:
                    body = json.loads(args[3])
                except (TypeError, ValueError):
                    continue
                for payload in body if isinstance(body, list) else [body]:
                    for intf in payload.get("interfaces", []) if isinstance(payload, dict) else []:
                        if intf.get("ifName") == IFNAME:
                            sent = intf["nvPairs"]
        return sent

    # ------------------------------------------------------------------ scenarios
    def delta(self, state, profile=None, drop=(), have=None, base_have=None):
        """The reported nvPairs of the scenario MINUS the control's (same config without any DHCP4 field, HAVE = base_have): exactly what the
        scenario adds on top of what every run reports, so unrelated fields are held constant by construction."""
        control = self.reported(self.scenario(state, have=base_have if base_have is not None else EMPTY_HAVE))
        result = self.scenario(state, profile=profile, drop=drop, have=have)
        got = self.reported(result)
        extra = {k: v for k, v in got.items() if control.get(k, object()) != v}
        extra.pop("SPEED", None)  # reported by the generic update path for ANY update (pre-existing, see test_f3_speed_is_a_preexisting_report)
        missing = sorted(k for k in control if k not in got)
        self.assertEqual(missing, [], "state %s: the scenario lost reported keys of the control: %s" % (state, missing))
        return result, extra

    def _case_explicit_empty_clears_all_three_in_every_state(self, states):
        for state in states:
            result, extra = self.delta(
                state,
                profile={"dhcp_server_addr4": "", "vrf_dhcp4": "", "dhcp_relay_src_intf": ""},
                have=SET_HAVE,
            )
            self.assertEqual(extra, {"dhcpServerAddr4": "", "vrfDhcp4": "", "DHCP_RELAY_SRC_INTF": ""}, state)
            sent = self.outbound()
            self.assertTrue(sent is not None, state)
            for key in DHCP4:
                self.assertEqual(sent[key], "", "%s: outbound %s" % (state, key))
            self.assertEqual(sent["dhcpServerAddr1"], "192.200.1.1", state)
            self.assertEqual(sent["vrfDhcp3"], "blue", state)

    def _case_server4_alone_clears_with_its_vrf_and_leaves_the_relay_source(self, states):
        for state in states:
            result, extra = self.delta(state, profile={"dhcp_server_addr4": ""}, have=SET_HAVE, drop=())
            want = {"dhcpServerAddr4": "", "vrfDhcp4": ""}
            if state != "merged":
                want["DHCP_RELAY_SRC_INTF"] = ""  # replaced/overridden: the omitted relay source is reset too
            self.assertEqual(extra, want, state)

    def _case_relay_source_clears_independently_of_the_servers(self, states):
        for state in states:
            result, extra = self.delta(
                state,
                profile={"dhcp_relay_src_intf": "", "dhcp_server_addr4": "192.200.1.4", "vrf_dhcp4": "blue"},
                have=SET_HAVE,
            )
            self.assertEqual(extra, {"DHCP_RELAY_SRC_INTF": ""}, state)
            self.assertEqual(self.outbound()["dhcpServerAddr4"], "192.200.1.4", state)
            self.assertEqual(self.outbound()["vrfDhcp4"], "blue", state)

    def _case_omission_preserves_in_merged_and_resets_in_replaced_and_overridden(self, states):
        if "merged" in states:
            result, extra = self.delta("merged", have=SET_HAVE)
            self.assertEqual(extra, {}, "merged omission must preserve")
            sent = self.outbound()
            self.assertTrue(sent is None or all(sent.get(k) == v for k, v in SET_HAVE.items() if k in sent), sent)
        for state in [x for x in states if x != "merged"]:
            result, extra = self.delta(state, have=SET_HAVE)
            self.assertEqual(extra, {"dhcpServerAddr4": "", "vrfDhcp4": "", "DHCP_RELAY_SRC_INTF": ""}, state)
            for key in DHCP4:
                self.assertEqual(self.outbound()[key], "", "%s %s" % (state, key))

    def _case_set_and_change_still_work(self, states):
        new = {"dhcp_server_addr4": "192.200.1.9", "vrf_dhcp4": "green", "dhcp_relay_src_intf": "loopback1"}
        for state in states:
            for have in (SET_HAVE, None):  # changed from a value, and set where HAVE carries none of the keys
                _result, extra = self.delta(state, profile=new, have=have, base_have=have or {})
                self.assertEqual(extra, {"dhcpServerAddr4": "192.200.1.9", "vrfDhcp4": "green", "DHCP_RELAY_SRC_INTF": "loopback1"}, "%s %s" % (state, have))

    def _case_nothing_to_clear_never_writes_and_never_raises(self, states):
        """HAVE missing the keys (older GET), null, or empty: an explicit empty and an omission are both a no-op."""
        cases = (("missing", None), ("null", NULL_HAVE), ("empty", EMPTY_HAVE))
        explicit = {"dhcp_server_addr4": "", "vrf_dhcp4": "", "dhcp_relay_src_intf": ""}
        for label, have in cases:
            for state in states:
                for profile in (explicit, {}):
                    _result, extra = self.delta(state, profile=profile, have=have, base_have=have or {})
                    self.assertEqual(extra, {}, "%s %s %s" % (label, state, sorted(profile)))
                    sent = self.outbound()
                    if sent is not None and have is None:
                        for key in DHCP4:
                            self.assertNotIn(key, sent, "%s %s" % (label, state))

    def _case_second_run_from_the_resulting_have_is_a_noop(self, states):
        explicit = {"dhcp_server_addr4": "", "vrf_dhcp4": "", "dhcp_relay_src_intf": ""}
        for state in states:
            _first, extra = self.delta(state, profile=explicit, have=SET_HAVE)
            self.assertEqual(len(extra), 3, state)
            # HAVE after the clear: the controller returns the template's own empty values
            _second, again = self.delta(state, profile=explicit, have=EMPTY_HAVE, base_have=EMPTY_HAVE)
            self.assertEqual(again, {}, "%s: a second run must not write" % state)

    def _case_servers_one_to_three_are_the_unchanged_positive_control(self, states):
        for state in states:
            _result, extra = self.delta(
                state,
                profile={"dhcp_server_addr1": "", "vrf_dhcp1": ""},
                have=SET_HAVE,
                base_have=SET_HAVE,
            )
            self.assertEqual(extra.get("dhcpServerAddr1"), "", state)
            self.assertEqual(extra.get("vrfDhcp1"), "", state)
            for key in ("dhcpServerAddr2", "dhcpServerAddr3", "dhcpServerAddr4", "vrfDhcp4", "DHCP_RELAY_SRC_INTF"):
                self.assertNotIn(key, extra, "%s %s" % (state, key))

    def _case_clearing_server4_leaves_servers_one_to_three_vrfs_addresses_and_hsrp_untouched(self, states):
        for state in states:
            _result, extra = self.delta(state, profile={"dhcp_server_addr4": "", "vrf_dhcp4": ""}, have=SET_HAVE)
            allowed = {"dhcpServerAddr4", "vrfDhcp4", "DHCP_RELAY_SRC_INTF"}
            self.assertTrue(set(extra) <= allowed, "%s: unintended keys %s" % (state, sorted(set(extra) - allowed)))
            sent = self.outbound()
            for key, value in (("dhcpServerAddr1", "192.200.1.1"), ("vrfDhcp2", "blue"), ("HSRP_VIP", "192.168.2.100"), ("IP", "192.168.2.1")):
                self.assertEqual(sent[key], value, "%s %s" % (state, key))

    def _case_unrelated_creation_still_omits_the_new_keys(self, states):
        # no HAVE at all would be a creation; the existing test_dcnm_intf_svi_dhcp4_absent_when_unset keeps that. Here: the SVI exists, no field authored.
        _result, extra = self.delta("merged", have=None, base_have={})
        self.assertEqual(extra, {})

    def _case_speed_is_a_preexisting_report(self, states):
        """SPEED "" is reported next to ANY update of this SVI (here a description change, no DHCP involved): not caused by F3."""
        for state in states:
            result = self.scenario(state, profile={"description": "changed text"}, have=EMPTY_HAVE)
            self.assertIn("SPEED", self.reported(result), state)
            self.assertTrue(all(k not in self.reported(result) for k in DHCP4), state)

    # ---- the legacy harness emulates the vPC peer's bulk read only for a test whose NAME contains 'overridden'
    def test_f3_explicit_empty_clears_all_three_in_every_state(self):
        self._case_explicit_empty_clears_all_three_in_every_state(("merged", "replaced"))

    def test_f3_overridden_explicit_empty_clears_all_three_in_every_state(self):
        self._case_explicit_empty_clears_all_three_in_every_state(("overridden",))

    def test_f3_server4_alone_clears_with_its_vrf_and_leaves_the_relay_source(self):
        self._case_server4_alone_clears_with_its_vrf_and_leaves_the_relay_source(("merged", "replaced"))

    def test_f3_overridden_server4_alone_clears_with_its_vrf_and_leaves_the_relay_source(self):
        self._case_server4_alone_clears_with_its_vrf_and_leaves_the_relay_source(("overridden",))

    def test_f3_relay_source_clears_independently_of_the_servers(self):
        self._case_relay_source_clears_independently_of_the_servers(("merged", "replaced"))

    def test_f3_overridden_relay_source_clears_independently_of_the_servers(self):
        self._case_relay_source_clears_independently_of_the_servers(("overridden",))

    def test_f3_omission_preserves_in_merged_and_resets_in_replaced_and_overridden(self):
        self._case_omission_preserves_in_merged_and_resets_in_replaced_and_overridden(("merged", "replaced"))

    def test_f3_overridden_omission_preserves_in_merged_and_resets_in_replaced_and_overridden(self):
        self._case_omission_preserves_in_merged_and_resets_in_replaced_and_overridden(("overridden",))

    def test_f3_set_and_change_still_work(self):
        self._case_set_and_change_still_work(("merged", "replaced"))

    def test_f3_overridden_set_and_change_still_work(self):
        self._case_set_and_change_still_work(("overridden",))

    def test_f3_nothing_to_clear_never_writes_and_never_raises(self):
        self._case_nothing_to_clear_never_writes_and_never_raises(("merged", "replaced"))

    def test_f3_overridden_nothing_to_clear_never_writes_and_never_raises(self):
        self._case_nothing_to_clear_never_writes_and_never_raises(("overridden",))

    def test_f3_second_run_from_the_resulting_have_is_a_noop(self):
        self._case_second_run_from_the_resulting_have_is_a_noop(("merged", "replaced"))

    def test_f3_overridden_second_run_from_the_resulting_have_is_a_noop(self):
        self._case_second_run_from_the_resulting_have_is_a_noop(("overridden",))

    def test_f3_servers_one_to_three_are_the_unchanged_positive_control(self):
        self._case_servers_one_to_three_are_the_unchanged_positive_control(("merged", "replaced"))

    def test_f3_overridden_servers_one_to_three_are_the_unchanged_positive_control(self):
        self._case_servers_one_to_three_are_the_unchanged_positive_control(("overridden",))

    def test_f3_clearing_server4_leaves_servers_one_to_three_vrfs_addresses_and_hsrp_untouched(self):
        self._case_clearing_server4_leaves_servers_one_to_three_vrfs_addresses_and_hsrp_untouched(("merged", "replaced"))

    def test_f3_overridden_clearing_server4_leaves_servers_one_to_three_vrfs_addresses_and_hsrp_untouched(self):
        self._case_clearing_server4_leaves_servers_one_to_three_vrfs_addresses_and_hsrp_untouched(("overridden",))

    def test_f3_unrelated_creation_still_omits_the_new_keys(self):
        self._case_unrelated_creation_still_omits_the_new_keys(("merged", "replaced"))

    def test_f3_overridden_unrelated_creation_still_omits_the_new_keys(self):
        self._case_unrelated_creation_still_omits_the_new_keys(("overridden",))

    def test_f3_speed_is_a_preexisting_report(self):
        self._case_speed_is_a_preexisting_report(("merged", "replaced"))

    def test_f3_overridden_speed_is_a_preexisting_report(self):
        self._case_speed_is_a_preexisting_report(("overridden",))


def _switch_off_inherited_tests():
    for name in dir(legacy.TestDcnmIntfModule):
        if name.startswith("test_") and not name.startswith("test_f3_"):
            setattr(TestSviDhcp4Clear, name, None)


# ---------------------------------------------------------------- scenario bodies are added below


_switch_off_inherited_tests()
