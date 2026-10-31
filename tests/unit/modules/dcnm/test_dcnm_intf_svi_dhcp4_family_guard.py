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

"""D-F3-1: an SVI DHCP4 / relay-source change is refused before any write when the stored nvPairs carry the other int_vlan body's
names than the ones patch_version selects (a partial clear would otherwise move only the shared vrfDhcp4).

Real main() through the existing F3 / template-compat harness; HAVE written with explicit key families. NOT LIVE TESTED.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json

from . import test_dcnm_intf_svi_dhcp4_template_compat as compat
from .dcnm_module import AnsibleExitJson, AnsibleFailJson, loadPlaybookData, set_module_args

LEGACY, SMU, APPROVED_SMU = compat.LEGACY, compat.SMU, compat.APPROVED_SMU
CLEAR = {"dhcp_server_addr4": "", "vrf_dhcp4": "", "dhcp_relay_src_intf": ""}
SET = {"dhcp_server_addr4": "192.200.1.9", "vrf_dhcp4": "green", "dhcp_relay_src_intf": "loopback1"}
STORED = ("192.200.1.4", "blue", "loopback0")


class TestSviDhcp4FamilyGuard(compat.TestSviDhcp4TemplateCompat):

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
        for value in STORED + tuple(SET.values()):
            assert value not in msg, "no field value in the message"

    @staticmethod
    def stored(names, server=STORED[0], vrf=STORED[1], relay=STORED[2]):
        return {names["dhcp_server_addr4"]: server, names["vrf_dhcp4"]: vrf, names["dhcp_relay_src_intf"]: relay}

    # ------------------------------------------------------------------ the unsafe partial clear (C3) and its mirror (C4 / C5)
    def test_f3_guard_smu_declared_legacy_stored_explicit_clear_is_refused(self):
        status, result, writes = self.run_any("merged", profile=CLEAR, have=self.stored(LEGACY), patch=APPROVED_SMU)
        self.assert_refused(status, result, writes, ("dhcpServerAddr4", "DHCP_RELAY_SRC_INTF"))

    def test_f3_guard_undeclared_smu_stored_explicit_clear_is_refused(self):
        status, result, writes = self.run_any("merged", profile=CLEAR, have=self.stored(SMU))
        self.assert_refused(status, result, writes, ("dhcpRelaySourceInterface", "dhcpServerAddress4"))
        assert "(not declared)" in result["msg"]

    def test_f3_guard_undeclared_smu_stored_replaced_omission_is_refused(self):
        status, result, writes = self.run_any("replaced", drop=tuple(CLEAR), have=self.stored(SMU))
        self.assert_refused(status, result, writes, ("dhcpRelaySourceInterface", "dhcpServerAddress4"))

    def test_f3_guard_overridden_omission_with_foreign_storage_is_refused(self):
        status, result, writes = self.run_any("overridden", drop=tuple(CLEAR), have=self.stored(SMU))
        self.assert_refused(status, result, writes, ("dhcpRelaySourceInterface", "dhcpServerAddress4"))

    def test_f3_guard_a_valid_earlier_target_in_the_same_invocation_is_not_written_either(self):
        status, result, writes = self.run_any("merged", profile=CLEAR, have=self.stored(LEGACY), patch=APPROVED_SMU, valid_target_first=True)
        self.assert_refused(status, result, writes, ("dhcpServerAddr4", "DHCP_RELAY_SRC_INTF"))
        assert "vlan1002" not in result["msg"].lower()
        # control: the same two-target invocation with the matching family writes
        status, result, writes = self.run_any("merged", profile=CLEAR, have=self.stored(LEGACY), patch=None, valid_target_first=True)
        assert status == "exit" and writes >= 1, result

    def test_f3_guard_set_with_the_wrong_family_is_refused(self):
        for have, patch in ((self.stored(LEGACY), APPROVED_SMU), (self.stored(SMU), None)):
            status, result, writes = self.run_any("merged", profile=SET, have=have, patch=patch)
            assert status == "fail" and writes == 0, (patch, result)

    def test_f3_guard_each_alias_alone_is_checked(self):
        only_relay = {LEGACY["dhcp_relay_src_intf"]: STORED[2]}
        status, result, writes = self.run_any("merged", profile={"dhcp_relay_src_intf": ""}, have=only_relay, patch=APPROVED_SMU)
        self.assert_refused(status, result, writes, ("DHCP_RELAY_SRC_INTF",))
        only_server = {SMU["dhcp_server_addr4"]: STORED[0]}
        status, result, writes = self.run_any("merged", profile={"dhcp_server_addr4": ""}, have=only_server)
        self.assert_refused(status, result, writes, ("dhcpServerAddress4",))

    def test_f3_guard_vrf4_alone_is_not_cleared_against_a_foreign_server(self):
        status, result, writes = self.run_any("merged", profile={"vrf_dhcp4": ""}, have=self.stored(LEGACY), patch=APPROVED_SMU)
        assert status == "fail" and writes == 0, result

    # ------------------------------------------------------------------ ambiguity: blank foreign keys, mixed families
    def test_f3_guard_blank_foreign_keys_are_still_a_visible_mismatch(self):
        have = self.stored(LEGACY, server="", vrf="", relay="")
        status, result, writes = self.run_any("merged", profile=SET, have=have, patch=APPROVED_SMU)
        assert status == "fail" and writes == 0, result
        status, result, writes = self.run_any("replaced", drop=tuple(CLEAR), have=have, patch=APPROVED_SMU)
        assert status == "fail" and writes == 0, result

    def test_f3_guard_mixed_families_are_never_prioritized(self):
        mixed = dict(self.stored(LEGACY), **self.stored(SMU))
        for patch in (APPROVED_SMU, None):
            status, result, writes = self.run_any("merged", profile=CLEAR, have=mixed, patch=patch)
            assert status == "fail" and writes == 0, (patch, result)

    # ------------------------------------------------------------------ no unnecessary refusal
    def test_f3_guard_matching_families_still_set_and_clear(self):
        for names, patch in ((LEGACY, None), (SMU, APPROVED_SMU)):
            status, result, writes = self.run_any("merged", profile=CLEAR, have=self.stored(names), patch=patch)
            assert status == "exit" and writes >= 1, (patch, result)
            sent = self.outbound()
            assert sent[names["dhcp_server_addr4"]] == "" and sent[names["dhcp_relay_src_intf"]] == "" and sent["vrfDhcp4"] == ""
            status, result, writes = self.run_any("replaced", drop=tuple(CLEAR), have=self.stored(names), patch=patch)
            assert status == "exit" and writes >= 1, (patch, result)

    def test_f3_guard_absence_of_both_families_is_not_a_mismatch(self):
        for patch in (APPROVED_SMU, None):
            status, result, _writes = self.run_any("merged", profile=SET, have={}, patch=patch)
            assert status == "exit", (patch, result)

    def test_f3_guard_unrelated_merged_change_is_not_refused(self):
        status, result, writes = self.run_any("merged", profile={"description": "unrelated change"}, have=self.stored(LEGACY), patch=APPROVED_SMU)
        assert status == "exit" and writes >= 1, result

    def test_f3_guard_null_values_under_a_matching_family_keep_their_semantics(self):
        have = {SMU["dhcp_server_addr4"]: None, SMU["vrf_dhcp4"]: None, SMU["dhcp_relay_src_intf"]: None}
        status, result, _writes = self.run_any("merged", profile=CLEAR, have=have, patch=APPROVED_SMU)
        assert status == "exit", result
        assert {k: v for k, v in self.reported(result).items() if k in SMU.values()} == {}

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
                                              have=self.stored(SMU, relay=""), patch=APPROVED_SMU)
        assert status == "exit" and writes >= 1, result
        sent = self.svi_writes()
        assert len(sent) == 1, sent
        method, path, serial, nv = sent[0]
        assert method == "PUT" and path.endswith("/interface"), (method, path)
        assert serial == "SAL1819SAN8"
        assert nv[SMU["dhcp_relay_src_intf"]] == "vlan2301"
        assert LEGACY["dhcp_relay_src_intf"] not in nv and LEGACY["dhcp_server_addr4"] not in nv
        # the other DHCP values: servers 1-3 as the task sets them; the stored server 4 and its VRF are not in the request
        assert [nv["dhcpServerAddr%d" % i] for i in (1, 2, 3)] == ["192.200.1.1", "192.200.1.2", "192.200.1.3"]
        assert [nv["vrfDhcp%d" % i] for i in (1, 2, 3)] == ["blue", "blue", "blue"]
        assert SMU["dhcp_server_addr4"] not in nv and SMU["vrf_dhcp4"] not in nv, nv
        changed = {k: v for k, v in self.reported(result).items() if "dhcp" in k.lower() or "relay" in k.lower()}
        assert changed == {SMU["dhcp_relay_src_intf"]: "vlan2301"}, changed

    def test_f3_guard_vlan_relay_source_repeat_writes_nothing(self):
        status, result, writes = self.run_any("merged", profile={"dhcp_relay_src_intf": "vlan2301"},
                                              have=self.stored(SMU, relay="vlan2301"), patch=APPROVED_SMU)
        assert status == "exit" and writes == 0, (writes, result)


def _switch_off_inherited_tests():
    """Only the test_f3_guard_* cases run here; the inherited template-compat and F3 cases run in their own files."""
    for name in dir(TestSviDhcp4FamilyGuard):
        if name.startswith("test_") and not name.startswith("test_f3_guard_"):
            setattr(TestSviDhcp4FamilyGuard, name, None)


_switch_off_inherited_tests()
