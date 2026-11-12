"""int_vlan SVI DHCP server 4 and relay source: clearing, family guard and template-specific names."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import pytest
import re

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from ..dcnm_module import AnsibleExitJson
from ..dcnm_module import AnsibleFailJson
from ..dcnm_module import loadPlaybookData
from ..dcnm_module import set_module_args
from .. import test_dcnm_intf as legacy
from .helpers.fixture_cases import load_text


# ====================================================================================================
# Formerly test_dcnm_intf_svi_dhcp4_clear.py
# F3: explicit clearing of the int_vlan DHCP server 4 (dhcp_server_addr4 / vrf_dhcp4) and of the relay source interface.
#
# Real main() through the EXISTING dcnm_interface unit harness (test_dcnm_intf.TestDcnmIntfModule: same patches, same fixtures
# dcnm_intf_svi_configs / dcnm_intf_svi_payloads); only the HAVE of the SVI is varied. NOT LIVE TESTED: these are controller DOUBLES, so
# what the controller returns after a clear is the double's value, not a measurement. Servers 1-3 are the positive controls.
#
# Every scenario is compared with a CONTROL run (same config and HAVE with no DHCP4 field at all) so that "all other fields held
# constant" is asserted, not assumed: the changed nvPairs of a scenario must equal the control's plus exactly the expected DHCP keys.
# ====================================================================================================
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


# ====================================================================================================
# Formerly test_dcnm_intf_svi_dhcp4_template_compat.py
# F3 / SVI DHCP4: the nvPair names follow the parent template that the controller serves.
#
# The int_vlan parent template exists in (at least) two bodies that name the fourth DHCP server and the relay source interface differently:
#
#     body 0efb09af (pre-SMU)                         body f32ef586 (served with the activated SMU 4.3.1.0175006011)
#     dhcpServerAddr4      (profile dhcp_server_addr4)   dhcpServerAddress4
#     vrfDhcp4             (profile vrf_dhcp4)           vrfDhcp4
#     DHCP_RELAY_SRC_INTF  (profile dhcp_relay_src_intf) dhcpRelaySourceInterface
#
# The EXPECTED names below are NOT taken from the module: they are read out of verbatim excerpts of the two real template bodies
# (fixtures/dhcp_template_excerpts.yaml, each excerpt headed by the sha256 of the full body), so the mapping cannot be its own oracle. The selector is the
# module's existing ``patch_version`` capability (approved SMU ``4.3.1.0175006011`` or a numeric ND release >= 4.4.1; see gie_patch_supported):
# an approved patch selects the SMU-schema body, a missing or unapproved one keeps the legacy names. 4.4.1 is OFFLINE-ONLY: no capture of an
# ND >= 4.4.1 exists, so its names are the existing selector's assumption, not an observation.
#
# Real main() through the EXISTING dcnm_interface unit harness (controller doubles). NOT LIVE TESTED.
# ====================================================================================================
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


APPROVED_SMU = "4.3.1.0175006017"
DHCP_NAMES_IFNAME = IFNAME
PROFILE_KEYS = ("dhcp_server_addr4", "vrf_dhcp4", "dhcp_relay_src_intf")


# ============================================================================== the oracle: names declared by the real template bodies
def _declared(excerpt):
    """{profile key: nvPair name} read from the `type name;` declarations of a template excerpt (no knowledge of the module's mapping)."""
    text = load_text(excerpt)
    found = {}
    for kind, name in re.findall(r"^(ipAddress|string|interface)\s+(\w+);", text, re.M):
        if kind == "ipAddress" and re.search(r"dhcp\w*4$", name, re.I):
            found["dhcp_server_addr4"] = name
        elif kind == "string" and re.fullmatch(r"vrfDhcp4", name):
            found["vrf_dhcp4"] = name
        elif kind == "interface" and re.search(r"dhcp.*(relay|src)", name, re.I):
            found["dhcp_relay_src_intf"] = name
    return found


LEGACY = _declared("int_vlan_0efb09af_dhcp_excerpt")
SMU = _declared("int_vlan_f32ef586_dhcp_excerpt")
OLDER = _declared("int_vlan_4d043f65_dhcp_excerpt")
FAMILIES = {"legacy": (LEGACY, None), "smu": (SMU, APPROVED_SMU)}  # (names declared by the body, patch_version that selects it)


def test_the_oracle_reads_the_two_bodies_as_the_capture_review_found_them():
    assert LEGACY == {"dhcp_server_addr4": "dhcpServerAddr4", "vrf_dhcp4": "vrfDhcp4", "dhcp_relay_src_intf": "DHCP_RELAY_SRC_INTF"}
    assert SMU == {"dhcp_server_addr4": "dhcpServerAddress4", "vrf_dhcp4": "vrfDhcp4", "dhcp_relay_src_intf": "dhcpRelaySourceInterface"}
    assert OLDER == {"dhcp_relay_src_intf": "DHCP_RELAY_SRC_INTF"}, "the oldest body has no fourth server and keeps the legacy relay-source name"


def test_only_the_server_and_relay_source_names_differ_between_the_bodies():
    assert LEGACY["vrf_dhcp4"] == SMU["vrf_dhcp4"]
    assert LEGACY["dhcp_server_addr4"] != SMU["dhcp_server_addr4"] and LEGACY["dhcp_relay_src_intf"] != SMU["dhcp_relay_src_intf"]


# ============================================================================== the selector (pure)
@pytest.mark.parametrize("patch", [APPROVED_SMU, "4.4.1", "4.4.1.10", "4.10.0", "5.0.0.1"])
def test_an_approved_patch_selects_the_smu_names(patch):
    assert dict(module.svi_dhcp4_fields(patch)) == SMU


@pytest.mark.parametrize("patch", [None, "", "4.4.0", "4.4", "4.4.1-rc1", "4.3.1", "4.3.1.0175006010", "4.3.1.0175006012", "latest", 4, 441, ["4.4.1"]])
def test_a_missing_or_unapproved_patch_keeps_the_legacy_names(patch):
    assert dict(module.svi_dhcp4_fields(patch)) == LEGACY


def test_the_two_families_never_mix_and_the_legacy_constant_is_unchanged():
    assert dict(module.SVI_DHCP4_FIELDS) == LEGACY
    assert set(LEGACY.values()) & set(SMU.values()) == {"vrfDhcp4"}


# ============================================================================== real main(), per family
SET = {"dhcp_server_addr4": "192.200.1.4", "vrf_dhcp4": "blue", "dhcp_relay_src_intf": "loopback0"}
CLEAR = {"dhcp_server_addr4": "", "vrf_dhcp4": "", "dhcp_relay_src_intf": ""}
GROUPS = {"": ("merged", "replaced"), "overridden_": ("overridden",)}  # the legacy harness emulates the vPC peer only for a test NAMED *overridden*


class TestSviDhcp4TemplateCompat(TestSviDhcp4Clear):
    """Same harness as the F3 tests; `scenario` takes the patch_version and the HAVE is written with the names of the family under test."""

    def scenario(self, state, profile=None, drop=(), have=None, patch=None):
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
        for key in ("dhcpServerAddr4", "dhcpServerAddress4", "DHCP_RELAY_SRC_INTF", "dhcpRelaySourceInterface"):
            nv.pop(key, None)  # the fixture carries one family; each scenario states its own HAVE
        for key, value in (have or {}).items():
            nv[key] = value
        self._state = state
        args = dict(state=state, fabric="test_fabric", config=config)
        if patch is not None:
            args["patch_version"] = patch
        set_module_args(args)
        self.load_fixtures()
        try:
            self.module.main()
        except AnsibleExitJson as exc:
            return exc.args[0]
        except AnsibleFailJson as exc:
            self.fail("main() failed: %s" % exc.args[0].get("msg"))
        self.fail("main() returned without exit_json")

    # --- helpers that speak in the names of a family
    @staticmethod
    def have_of(names, server="", vrf="", relay=""):
        return {names["dhcp_server_addr4"]: server, names["vrf_dhcp4"]: vrf, names["dhcp_relay_src_intf"]: relay}

    def extra(self, family, state, profile=None, drop=(), have=None, base_have=None):
        """Reported nvPairs of the scenario MINUS the control's (same config without any DHCP4 field and HAVE = base_have)."""
        names, patch = FAMILIES[family]
        control = self.reported(self.scenario(state, have=base_have if base_have is not None else self.have_of(names), patch=patch))
        got = self.reported(self.scenario(state, profile=profile, drop=drop, have=have, patch=patch))
        out = {k: v for k, v in got.items() if control.get(k, object()) != v}
        out.pop("SPEED", None)  # reported by the generic update path for ANY update of this SVI (pre-existing; see the F3 test file)
        return out

    @staticmethod
    def renamed(names, values):
        """{nvPair name of the family: value} from {profile key: value}."""
        return {names[k]: v for k, v in values.items()}

    # ---------------------------------------------------------------- set / change (the family's names, and only those)
    def _run_set(self, family, states):
        names, patch = FAMILIES[family]
        foreign = {v for v in (LEGACY if names is SMU else SMU).values() if v not in names.values()}
        for state in states:
            got = self.extra(family, state, profile=SET, have=self.have_of(names))
            assert got == self.renamed(names, SET), (family, state, got)
            sent = self.outbound()
            assert sent is not None and not (set(sent) & foreign), "no alias of the other family: %s" % sorted(set(sent) & foreign)

    def _run_change(self, family, states):
        names, _patch = FAMILIES[family]
        new = {"dhcp_server_addr4": "192.200.1.9", "vrf_dhcp4": "green", "dhcp_relay_src_intf": "loopback1"}
        for state in states:
            for have in (self.have_of(names, "192.200.1.4", "blue", "loopback0"), {}):  # changed from a value, and set where HAVE carries none of the keys
                got = self.extra(family, state, profile=new, have=have, base_have=have)
                assert got == self.renamed(names, new), (family, state, have, got)

    # ---------------------------------------------------------------- explicit clear, replaced/overridden omission, merged omission
    def _run_clear(self, family, states):
        names, _patch = FAMILIES[family]
        have = self.have_of(names, "192.200.1.4", "blue", "loopback0")
        every = self.renamed(names, CLEAR)
        for state in states:
            assert self.extra(family, state, profile=CLEAR, have=have) == every, (family, state, "explicit empty")
            sent = self.outbound()
            assert sent is not None and all(sent[names[k]] == "" for k in CLEAR), (family, state)
            if state == "merged":
                assert self.extra(family, state, drop=tuple(CLEAR), have=have) == {}, (family, state, "merged omission preserves")
            else:
                assert self.extra(family, state, drop=tuple(CLEAR), have=have) == every, (family, state, "authoritative omission resets")

    # ---------------------------------------------------------------- server 4 and its VRF go together; the relay source is independent
    def _run_independence(self, family, states):
        names, _patch = FAMILIES[family]
        have = self.have_of(names, "192.200.1.4", "blue", "loopback0")
        for state in states:
            got = self.extra(family, state, profile={"dhcp_server_addr4": ""}, have=have)
            want = {names["dhcp_server_addr4"]: "", names["vrf_dhcp4"]: ""}
            if state != "merged":
                want[names["dhcp_relay_src_intf"]] = ""  # replaced/overridden: the omitted source is reset
            assert got == want, (family, state, got)
            got = self.extra(family, state, profile={"dhcp_relay_src_intf": "", "dhcp_server_addr4": "192.200.1.4", "vrf_dhcp4": "blue"}, have=have)
            assert got == {names["dhcp_relay_src_intf"]: ""}, (family, state, got)

    # ---------------------------------------------------------------- absent / null / empty HAVE never writes and never raises
    def _run_have_shapes(self, family, states):
        names, _patch = FAMILIES[family]
        shapes = (("absent", {}), ("null", {v: None for v in names.values()}), ("empty", self.have_of(names)))
        for label, have in shapes:
            for state in states:
                for profile in (CLEAR, {}):
                    got = self.extra(family, state, profile=profile, have=have, base_have=have)
                    assert got == {}, (family, label, state, sorted(profile), got)

    # ---------------------------------------------------------------- servers 1-3 are not part of this change
    def _run_servers_1_to_3(self, family, states):
        names, _patch = FAMILIES[family]
        have = self.have_of(names, "192.200.1.4", "blue", "loopback0")
        for state in states:
            got = self.extra(family, state, profile={"dhcp_server_addr4": "", "vrf_dhcp4": ""}, have=have)
            assert not [k for k in got if re.match(r"(dhcpServerAddr[123]|vrfDhcp[123])$", k)], (family, state, sorted(got))
            sent = self.outbound()
            for key, value in (("dhcpServerAddr1", "192.200.1.1"), ("vrfDhcp2", "blue"), ("HSRP_VIP", "192.168.2.100"), ("IP", "192.168.2.1")):
                assert sent[key] == value, (family, state, key)

    # ---------------------------------------------------------------- idempotency and reseeding
    def _run_idempotent_and_reseeded(self, family, states):
        names, patch = FAMILIES[family]
        have = self.have_of(names, "192.200.1.4", "blue", "loopback0")
        for state in states:
            again = self.extra(family, state, profile=SET, have=have, base_have=have)
            assert again == {}, (family, state, "the request equals HAVE", again)
            first = self.extra(family, state, profile=CLEAR, have=have)
            assert first == self.renamed(names, CLEAR)
            reseeded = self.have_of(names)  # what the controller returns after the clear: the template's own empty values
            second = self.extra(family, state, profile=CLEAR, have=reseeded, base_have=reseeded)
            assert second == {}, (family, state, "second run from the resulting HAVE is a no-op", second)

    def test_f3tc_without_a_patch_a_controller_of_the_smu_family_is_not_addressed_with_its_names(self):
        """A missing patch keeps the legacy names and never probes or switches the family. Since D-F3-1 (conscious change of the contract
        pinned here): when the stored nvPairs carry the SMU names, that DHCP4 change is refused before any write instead of sending legacy
        names that would miss the stored values (only vrfDhcp4 would move)."""
        have = self.have_of(SMU, "192.200.1.4", "blue", "loopback0")
        try:
            self.scenario("merged", profile=CLEAR, have=have, patch=None)
        except AssertionError as exc:
            assert "No configuration or deployment request was sent" in str(exc), exc
        else:
            raise AssertionError("the contradictory family must be refused")
        sent = [c for c in self.run_dcnm_send.call_args_list if len(c.args) >= 2 and c.args[1] in ("POST", "PUT", "DELETE")]
        assert sent == [], "no write; in particular no SMU names without the selector and no legacy names against SMU storage"


def _generate_family_cases():
    cases = {
        "set": "_run_set",
        "change": "_run_change",
        "clear_and_omission": "_run_clear",
        "server_and_source_independence": "_run_independence",
        "absent_null_empty_have": "_run_have_shapes",
        "servers_1_to_3_unchanged": "_run_servers_1_to_3",
        "idempotent_and_reseeded": "_run_idempotent_and_reseeded",
    }
    for case, runner in cases.items():
        for family in FAMILIES:
            for prefix, states in GROUPS.items():

                def make(runner=runner, family=family, states=states):
                    return lambda self: getattr(self, runner)(family, states)

                setattr(TestSviDhcp4TemplateCompat, "test_f3tc_%s_%s%s" % (case, prefix, family), make())


_generate_family_cases()


def test_registered_and_native_selectors_are_one_and_the_same():
    """The names follow the SAME capability as the registered fields of int_vlan (one parent body, one selector)."""
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_patch_supported

    for patch in (None, "", APPROVED_SMU, "4.4.1", "4.4.0", "4.3.1.0175006010", "latest"):
        assert (dict(module.svi_dhcp4_fields(patch)) == SMU) == gie_patch_supported(patch)


def _dhcp_names_switch_off_inherited_tests():
    """Only the test_f3tc_* cases of this file run under this class (the F3 and legacy cases keep running in their own files)."""
    for name in dir(TestSviDhcp4Clear):
        if name.startswith("test_") and not name.startswith("test_f3tc_"):
            setattr(TestSviDhcp4TemplateCompat, name, None)


_dhcp_names_switch_off_inherited_tests()


# ====================================================================================================
# Formerly test_dcnm_intf_svi_dhcp4_family_guard.py
# D-F3-1: an SVI DHCP4 / relay-source change is refused before any write when the stored nvPairs carry the other int_vlan body's
# names than the ones patch_version selects (a partial clear would otherwise move only the shared vrfDhcp4).
#
# Real main() through the existing F3 / template-compat harness; HAVE written with explicit key families. NOT LIVE TESTED.
# ====================================================================================================
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


DHCP_GUARD_LEGACY, DHCP_GUARD_SMU, DHCP_GUARD_APPROVED_SMU = LEGACY, SMU, APPROVED_SMU
DHCP_GUARD_CLEAR = {"dhcp_server_addr4": "", "vrf_dhcp4": "", "dhcp_relay_src_intf": ""}
DHCP_GUARD_SET = {"dhcp_server_addr4": "192.200.1.9", "vrf_dhcp4": "green", "dhcp_relay_src_intf": "loopback1"}
STORED = ("192.200.1.4", "blue", "loopback0")


class TestSviDhcp4FamilyGuard(TestSviDhcp4TemplateCompat):

    def run_any(self, state, profile=None, drop=(), have=None, patch=None, extra_profile=None, valid_target_first=False):
        """One main(); returns ("exit"|"fail", result, number of POST/PUT/DELETE requests sent).
        valid_target_first: a NEW SVI vlan1002 (no HAVE, no DHCP4 fields: a valid creation) is listed before vlan1001."""
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
            cfg["profile"].update(extra_profile or {})
            for key in drop:
                cfg["profile"].pop(key, None)
        if valid_target_first:
            new = copy.deepcopy(self.config_data["svi_merged_config"][0])
            new["name"], new["deploy"] = "vlan1002", "False"
            for key in [k for k in new["profile"] if k.startswith(("dhcp_", "vrf_dhcp"))]:
                new["profile"].pop(key)
            config.insert(0, new)
        self._have = copy.deepcopy(self.payloads_data["svi_merged_payloads"])
        nv = self._have["DATA"][0]["interfaces"][0]["nvPairs"]
        for key in ("dhcpServerAddr4", "dhcpServerAddress4", "DHCP_RELAY_SRC_INTF", "dhcpRelaySourceInterface"):
            nv.pop(key, None)
        for key, value in (have or {}).items():
            nv[key] = value
        self._state = state
        args = dict(state=state, fabric="test_fabric", config=config)
        if patch is not None:
            args["patch_version"] = patch
        set_module_args(args)
        self.load_fixtures()
        status, result = None, None
        try:
            self.module.main()
        except AnsibleExitJson as exc:
            status, result = "exit", exc.args[0]
        except AnsibleFailJson as exc:
            status, result = "fail", exc.args[0]
        writes = [c for c in self.run_dcnm_send.call_args_list if len(c.args) >= 2 and c.args[1] in ("POST", "PUT", "DELETE")]
        return status, result, len(writes)

    def assert_refused(self, status, result, writes, observed):
        assert status == "fail", result
        msg = result["msg"]
        assert writes == 0, writes
        assert "vlan1001" in msg.lower() and "No configuration or deployment request was sent" in msg and "patch_version" in msg
        for name in observed:
            assert name in msg
        for value in STORED + tuple(DHCP_GUARD_SET.values()):
            assert value not in msg, "no field value in the message"

    @staticmethod
    def stored(names, server=STORED[0], vrf=STORED[1], relay=STORED[2]):
        return {names["dhcp_server_addr4"]: server, names["vrf_dhcp4"]: vrf, names["dhcp_relay_src_intf"]: relay}

    # ------------------------------------------------------------------ the unsafe partial clear (C3) and its mirror (C4 / C5)
    def test_f3_guard_smu_declared_legacy_stored_explicit_clear_is_refused(self):
        status, result, writes = self.run_any("merged", profile=DHCP_GUARD_CLEAR, have=self.stored(DHCP_GUARD_LEGACY), patch=DHCP_GUARD_APPROVED_SMU)
        self.assert_refused(status, result, writes, ("dhcpServerAddr4", "DHCP_RELAY_SRC_INTF"))

    def test_f3_guard_undeclared_smu_stored_explicit_clear_is_refused(self):
        status, result, writes = self.run_any("merged", profile=DHCP_GUARD_CLEAR, have=self.stored(DHCP_GUARD_SMU))
        self.assert_refused(status, result, writes, ("dhcpRelaySourceInterface", "dhcpServerAddress4"))
        assert "(not declared)" in result["msg"]

    def test_f3_guard_undeclared_smu_stored_replaced_omission_is_refused(self):
        status, result, writes = self.run_any("replaced", drop=tuple(DHCP_GUARD_CLEAR), have=self.stored(DHCP_GUARD_SMU))
        self.assert_refused(status, result, writes, ("dhcpRelaySourceInterface", "dhcpServerAddress4"))

    def test_f3_guard_overridden_omission_with_foreign_storage_is_refused(self):
        status, result, writes = self.run_any("overridden", drop=tuple(DHCP_GUARD_CLEAR), have=self.stored(DHCP_GUARD_SMU))
        self.assert_refused(status, result, writes, ("dhcpRelaySourceInterface", "dhcpServerAddress4"))

    def test_f3_guard_a_valid_earlier_target_in_the_same_invocation_is_not_written_either(self):
        status, result, writes = self.run_any("merged", profile=DHCP_GUARD_CLEAR, have=self.stored(DHCP_GUARD_LEGACY),
                                              patch=DHCP_GUARD_APPROVED_SMU, valid_target_first=True)
        self.assert_refused(status, result, writes, ("dhcpServerAddr4", "DHCP_RELAY_SRC_INTF"))
        assert "vlan1002" not in result["msg"].lower()
        # control: the same two-target invocation with the matching family writes
        status, result, writes = self.run_any("merged", profile=DHCP_GUARD_CLEAR, have=self.stored(DHCP_GUARD_LEGACY), patch=None, valid_target_first=True)
        assert status == "exit" and writes >= 1, result

    def test_f3_guard_set_with_the_wrong_family_is_refused(self):
        for have, patch in ((self.stored(DHCP_GUARD_LEGACY), DHCP_GUARD_APPROVED_SMU), (self.stored(DHCP_GUARD_SMU), None)):
            status, result, writes = self.run_any("merged", profile=DHCP_GUARD_SET, have=have, patch=patch)
            assert status == "fail" and writes == 0, (patch, result)

    def test_f3_guard_each_alias_alone_is_checked(self):
        only_relay = {DHCP_GUARD_LEGACY["dhcp_relay_src_intf"]: STORED[2]}
        status, result, writes = self.run_any("merged", profile={"dhcp_relay_src_intf": ""}, have=only_relay, patch=DHCP_GUARD_APPROVED_SMU)
        self.assert_refused(status, result, writes, ("DHCP_RELAY_SRC_INTF",))
        only_server = {DHCP_GUARD_SMU["dhcp_server_addr4"]: STORED[0]}
        status, result, writes = self.run_any("merged", profile={"dhcp_server_addr4": ""}, have=only_server)
        self.assert_refused(status, result, writes, ("dhcpServerAddress4",))

    def test_f3_guard_vrf4_alone_is_not_cleared_against_a_foreign_server(self):
        status, result, writes = self.run_any("merged", profile={"vrf_dhcp4": ""}, have=self.stored(DHCP_GUARD_LEGACY), patch=DHCP_GUARD_APPROVED_SMU)
        assert status == "fail" and writes == 0, result

    # ------------------------------------------------------------------ ambiguity: blank foreign keys, mixed families
    def test_f3_guard_blank_foreign_keys_are_still_a_visible_mismatch(self):
        have = self.stored(DHCP_GUARD_LEGACY, server="", vrf="", relay="")
        status, result, writes = self.run_any("merged", profile=DHCP_GUARD_SET, have=have, patch=DHCP_GUARD_APPROVED_SMU)
        assert status == "fail" and writes == 0, result
        status, result, writes = self.run_any("replaced", drop=tuple(DHCP_GUARD_CLEAR), have=have, patch=DHCP_GUARD_APPROVED_SMU)
        assert status == "fail" and writes == 0, result

    def test_f3_guard_mixed_families_are_never_prioritized(self):
        mixed = dict(self.stored(DHCP_GUARD_LEGACY), **self.stored(DHCP_GUARD_SMU))
        for patch in (DHCP_GUARD_APPROVED_SMU, None):
            status, result, writes = self.run_any("merged", profile=DHCP_GUARD_CLEAR, have=mixed, patch=patch)
            assert status == "fail" and writes == 0, (patch, result)

    # ------------------------------------------------------------------ no unnecessary refusal
    def test_f3_guard_matching_families_still_set_and_clear(self):
        for names, patch in ((DHCP_GUARD_LEGACY, None), (DHCP_GUARD_SMU, DHCP_GUARD_APPROVED_SMU)):
            status, result, writes = self.run_any("merged", profile=DHCP_GUARD_CLEAR, have=self.stored(names), patch=patch)
            assert status == "exit" and writes >= 1, (patch, result)
            sent = self.outbound()
            assert sent[names["dhcp_server_addr4"]] == "" and sent[names["dhcp_relay_src_intf"]] == "" and sent["vrfDhcp4"] == ""
            status, result, writes = self.run_any("replaced", drop=tuple(DHCP_GUARD_CLEAR), have=self.stored(names), patch=patch)
            assert status == "exit" and writes >= 1, (patch, result)

    def test_f3_guard_absence_of_both_families_is_not_a_mismatch(self):
        for patch in (DHCP_GUARD_APPROVED_SMU, None):
            status, result, _writes = self.run_any("merged", profile=DHCP_GUARD_SET, have={}, patch=patch)
            assert status == "exit", (patch, result)

    def test_f3_guard_unrelated_merged_change_is_not_refused(self):
        status, result, writes = self.run_any("merged", profile={"description": "unrelated change"},
                                              have=self.stored(DHCP_GUARD_LEGACY), patch=DHCP_GUARD_APPROVED_SMU)
        assert status == "exit" and writes >= 1, result

    def test_f3_guard_null_values_under_a_matching_family_keep_their_semantics(self):
        have = {DHCP_GUARD_SMU["dhcp_server_addr4"]: None, DHCP_GUARD_SMU["vrf_dhcp4"]: None, DHCP_GUARD_SMU["dhcp_relay_src_intf"]: None}
        status, result, _writes = self.run_any("merged", profile=DHCP_GUARD_CLEAR, have=have, patch=DHCP_GUARD_APPROVED_SMU)
        assert status == "exit", result
        assert {k: v for k, v in self.reported(result).items() if k in DHCP_GUARD_SMU.values()} == {}

    # ------------------------------------------------------------------ a VLAN relay source (SMU 017 int_vlan body)
    def svi_writes(self):
        """(method, path, serialNumber, nvPairs) of every write whose payload names the SVI under test."""
        out = []
        for call in self.run_dcnm_send.call_args_list:
            args = call.args
            if len(args) < 4 or args[1] not in ("POST", "PUT") or not args[3]:
                continue
            try:
                body = json.loads(args[3])
            except (TypeError, ValueError):
                continue
            for payload in body if isinstance(body, list) else [body]:
                for intf in payload.get("interfaces", []) if isinstance(payload, dict) else []:
                    if intf.get("ifName") == "vlan1001":
                        out.append((args[1], args[2], intf.get("serialNumber"), intf["nvPairs"]))
        return out

    def test_f3_guard_vlan_relay_source_is_sent_under_the_017_body(self):
        """The SMU 017 int_vlan body accepts a VLAN relay source; the module sends the value unchanged under its SMU name."""
        status, result, writes = self.run_any("merged", profile={"dhcp_relay_src_intf": "vlan2301"},
                                              have=self.stored(DHCP_GUARD_SMU, relay=""), patch=DHCP_GUARD_APPROVED_SMU)
        assert status == "exit" and writes >= 1, result
        sent = self.svi_writes()
        assert len(sent) == 1, sent
        method, path, serial, nv = sent[0]
        assert method == "PUT" and path.endswith("/interface"), (method, path)
        assert serial == "SAL1819SAN8"
        assert nv[DHCP_GUARD_SMU["dhcp_relay_src_intf"]] == "vlan2301"
        assert DHCP_GUARD_LEGACY["dhcp_relay_src_intf"] not in nv and DHCP_GUARD_LEGACY["dhcp_server_addr4"] not in nv
        # the other DHCP values: servers 1-3 as the task sets them; the stored server 4 and its VRF are not in the request
        assert [nv["dhcpServerAddr%d" % i] for i in (1, 2, 3)] == ["192.200.1.1", "192.200.1.2", "192.200.1.3"]
        assert [nv["vrfDhcp%d" % i] for i in (1, 2, 3)] == ["blue", "blue", "blue"]
        assert DHCP_GUARD_SMU["dhcp_server_addr4"] not in nv and DHCP_GUARD_SMU["vrf_dhcp4"] not in nv, nv
        changed = {k: v for k, v in self.reported(result).items() if "dhcp" in k.lower() or "relay" in k.lower()}
        assert changed == {DHCP_GUARD_SMU["dhcp_relay_src_intf"]: "vlan2301"}, changed

    def test_f3_guard_vlan_relay_source_repeat_writes_nothing(self):
        status, result, writes = self.run_any("merged", profile={"dhcp_relay_src_intf": "vlan2301"},
                                              have=self.stored(DHCP_GUARD_SMU, relay="vlan2301"), patch=DHCP_GUARD_APPROVED_SMU)
        assert status == "exit" and writes == 0, (writes, result)


def _dhcp_guard_switch_off_inherited_tests():
    """Only the test_f3_guard_* cases run here; the inherited template-compat and F3 cases run in their own files."""
    for name in dir(TestSviDhcp4FamilyGuard):
        if name.startswith("test_") and not name.startswith("test_f3_guard_"):
            setattr(TestSviDhcp4FamilyGuard, name, None)


_dhcp_guard_switch_off_inherited_tests()
