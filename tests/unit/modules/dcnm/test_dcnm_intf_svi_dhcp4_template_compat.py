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

"""F3 / SVI DHCP4: the nvPair names follow the parent template that the controller serves.

The int_vlan parent template exists in (at least) two bodies that name the fourth DHCP server and the relay source interface differently:

    body 0efb09af (pre-SMU)                         body f32ef586 (served with the activated SMU 4.3.1.0175006011)
    dhcpServerAddr4      (profile dhcp_server_addr4)   dhcpServerAddress4
    vrfDhcp4             (profile vrf_dhcp4)           vrfDhcp4
    DHCP_RELAY_SRC_INTF  (profile dhcp_relay_src_intf) dhcpRelaySourceInterface

The EXPECTED names below are NOT taken from the module: they are read out of verbatim excerpts of the two real template bodies
(fixtures/int_vlan_*_dhcp_excerpt.txt, each headed by the sha256 of the full body), so the mapping cannot be its own oracle. The selector is the
module's existing ``patch_version`` capability (approved SMU ``4.3.1.0175006011`` or a numeric ND release >= 4.4.1; see gie_patch_supported):
an approved patch selects the SMU-schema body, a missing or unapproved one keeps the legacy names. 4.4.1 is OFFLINE-ONLY: no capture of an
ND >= 4.4.1 exists, so its names are the existing selector's assumption, not an observation.

Real main() through the EXISTING dcnm_interface unit harness (controller doubles). NOT LIVE TESTED.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import os
import re

import pytest

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module
from . import test_dcnm_intf_svi_dhcp4_clear as f3
from .dcnm_module import AnsibleExitJson, AnsibleFailJson, loadPlaybookData, set_module_args

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
APPROVED_SMU = "4.3.1.0175006017"
IFNAME = f3.IFNAME
PROFILE_KEYS = ("dhcp_server_addr4", "vrf_dhcp4", "dhcp_relay_src_intf")


# ============================================================================== the oracle: names declared by the real template bodies
def _declared(excerpt):
    """{profile key: nvPair name} read from the `type name;` declarations of a template excerpt (no knowledge of the module's mapping)."""
    with open(os.path.join(FIXTURES, excerpt), encoding="utf-8") as handle:
        text = handle.read()
    found = {}
    for kind, name in re.findall(r"^(ipAddress|string|interface)\s+(\w+);", text, re.M):
        if kind == "ipAddress" and re.search(r"dhcp\w*4$", name, re.I):
            found["dhcp_server_addr4"] = name
        elif kind == "string" and re.fullmatch(r"vrfDhcp4", name):
            found["vrf_dhcp4"] = name
        elif kind == "interface" and re.search(r"dhcp.*(relay|src)", name, re.I):
            found["dhcp_relay_src_intf"] = name
    return found


LEGACY = _declared("int_vlan_0efb09af_dhcp_excerpt.txt")
SMU = _declared("int_vlan_f32ef586_dhcp_excerpt.txt")
OLDER = _declared("int_vlan_4d043f65_dhcp_excerpt.txt")
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


class TestSviDhcp4TemplateCompat(f3.TestSviDhcp4Clear):
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


def _switch_off_inherited_tests():
    """Only the test_f3tc_* cases of this file run under this class (the F3 and legacy cases keep running in their own files)."""
    for name in dir(f3.TestSviDhcp4Clear):
        if name.startswith("test_") and not name.startswith("test_f3tc_"):
            setattr(TestSviDhcp4TemplateCompat, name, None)


_switch_off_inherited_tests()
