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

"""int_vlan::private_vlan_mapping -- apply, update, explicit clear, withdrawal.

The reset for this binding was MEASURED before it was registered: on a live
SVI holding `private-vlan mapping 3214,3216`, sending the public key as the
empty string left the controller at '' and removed that line from the running
configuration, with the primary address, three secondary addresses and HSRP
untouched and the leaf In-Sync.

Two properties of this field drive almost every test below.

1. The values are PREFIXES of one another. `private-vlan mapping 3214` is a
   prefix of `private-vlan mapping 3214,3216`, so every assertion compares the
   whole value; a substring check cannot tell an apply from an update.

2. The field is a plain string with `min_length: 1` and no `valid_values`, so
   the engine's empty-string exemption returns before the length check and the
   public clear is accepted. A test that only drove non-empty values would not
   notice if that exemption disappeared.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from .gie_withdrawal_harness import (SVI, SUPPORTED_PATCH, base_for, build_have, cfg,
                                     run_configs, writes)

PARENT = SVI
KEY = "private_vlan_mapping"
NVPAIR = "privateVlanMapping"
ONE = "3214"
TWO = "3214,3216"


def svi_profile(**extra):
    prof = base_for(PARENT)
    prof.update(extra)
    return prof


def drive(profile, state, have, check_mode=False):
    conf = cfg("Vlan931", profile, iftype="svi")
    return run_configs([conf], state, have=have, check_mode=check_mode,
                       allow_failed=True)


def sent_nvpairs(calls):
    bodies = [c["payload"] for c in writes(calls)]
    found = []

    def walk(node):
        if isinstance(node, dict):
            if "interfaces" in node and "policy" in node:
                found.append(node)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(bodies)
    assert len(found) == 1, "expected exactly one policy payload, got %d" % len(found)
    return found[0]["interfaces"][0]["nvPairs"]


# --------------------------------------------------------------------------
# Apply and update
# --------------------------------------------------------------------------

@pytest.mark.parametrize("value", [ONE, TWO, "3214-3216"])
def test_the_mapping_reaches_the_wire_on_the_right_parent(value):
    have = build_have(PARENT)
    result, calls = drive(svi_profile(**{KEY: value}), "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert sent_nvpairs(calls)[NVPAIR] == value


def test_an_update_replaces_the_whole_string_rather_than_merging_elements():
    """`3214` -> `3214,3216` is a new value, not a union computed here."""
    have = build_have(PARENT, KEY, ONE)
    _result, calls = drive(svi_profile(**{KEY: TWO}), "merged", have)
    assert sent_nvpairs(calls)[NVPAIR] == TWO


def test_narrowing_the_list_is_also_a_plain_replacement():
    have = build_have(PARENT, KEY, TWO)
    _result, calls = drive(svi_profile(**{KEY: ONE}), "merged", have)
    assert sent_nvpairs(calls)[NVPAIR] == ONE


def test_reapplying_the_same_value_sends_no_configuration_request():
    have = build_have(PARENT, KEY, TWO)
    result, calls = drive(svi_profile(**{KEY: TWO}), "merged", have)
    assert result.get("changed") is False
    assert writes(calls) == []


# --------------------------------------------------------------------------
# The explicit clear -- the measured reset
# --------------------------------------------------------------------------

def test_the_explicit_empty_string_is_accepted_despite_min_length_one():
    have = build_have(PARENT, KEY, TWO)
    result, calls = drive(svi_profile(**{KEY: ""}), "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert sent_nvpairs(calls)[NVPAIR] == ""


def test_the_clear_is_the_registered_reset_wire():
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
        gie_withdrawal_action)
    action, wire = gie_withdrawal_action(
        PARENT, KEY, {NVPAIR: TWO}, "12.6.0.267", SUPPORTED_PATCH)
    assert (action, wire) == ("reset", "")


# --------------------------------------------------------------------------
# Omission. This is where the neutral-baseline probe went wrong: omitting a
# field that is ALREADY empty never enters the withdrawal branch, so every case
# here starts from a CONFIGURED mapping.
# --------------------------------------------------------------------------

def assert_not_withdrawn(calls, expected):
    """Preservation shows up as SILENCE, and silence has to be read correctly.

    When the mapping is the only thing that could differ and the module decides
    to keep it, there is no diff and therefore no request at all. Demanding a
    payload here would fail a correct preservation. What must never happen is a
    payload that carries anything OTHER than the configured value.
    """
    for body in [c["payload"] for c in writes(calls)]:
        found = []

        def walk(node):
            if isinstance(node, dict):
                if "interfaces" in node and "policy" in node:
                    found.append(node)
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(body)
        for policy in found:
            nv = policy["interfaces"][0]["nvPairs"]
            assert nv.get(NVPAIR, expected) == expected, (
                "the mapping was changed to %r" % nv.get(NVPAIR))


def test_merged_omission_preserves_a_configured_mapping():
    have = build_have(PARENT, KEY, TWO)
    result, calls = drive(svi_profile(), "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert result.get("changed") is False, "merged omission must not change anything"
    assert_not_withdrawn(calls, TWO)


def test_replaced_omission_withdraws_a_configured_mapping():
    """PASS-AFTER. Against the 200 table this same call was REFUSED, because
    the binding had no reset_wire and `replaced` fails closed rather than
    guessing. With the measured reset registered it sends it."""
    have = build_have(PARENT, KEY, TWO)
    result, calls = drive(svi_profile(), "replaced", have)
    assert not result.get("failed"), result.get("msg")
    assert sent_nvpairs(calls)[NVPAIR] == ""


def test_replaced_check_plans_the_withdrawal_without_sending_it():
    have = build_have(PARENT, KEY, TWO)
    result, calls = drive(svi_profile(), "replaced", have, check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert writes(calls) == []
    assert result.get("changed") is True


def test_replaced_with_the_value_held_explicitly_keeps_it():
    have = build_have(PARENT, KEY, TWO)
    result, calls = drive(svi_profile(**{KEY: TWO}), "replaced", have)
    assert not result.get("failed"), result.get("msg")
    assert result.get("changed") is False
    assert_not_withdrawn(calls, TWO)


def test_a_rerun_after_the_withdrawal_is_converged():
    have = build_have(PARENT, KEY, "")
    result, calls = drive(svi_profile(), "replaced", have)
    assert not result.get("failed"), result.get("msg")
    assert writes(calls) == []


# --------------------------------------------------------------------------
# The reset must not leak to a sibling that did not earn it
# --------------------------------------------------------------------------

def test_the_reset_does_not_inherit_to_another_parent():
    """`private_vlan_mapping` is keyed on (int_vlan, privateVlanMapping).

    No other parent declares it, so no other parent may be handed this reset.
    MEASURED rather than assumed: the engine answers ('none', None) for a
    parent that does not declare the binding -- the same answer it gives for a
    key that does not exist at all -- not 'inapplicable'. Either way nothing is
    emitted; what this test defends is that registering one parent's reset did
    not start answering for five others."""
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
        gie_withdrawal_action)
    assert gie_withdrawal_action(
        PARENT, KEY, {NVPAIR: TWO}, "12.6.0.267", SUPPORTED_PATCH) == ("reset", "")
    for parent in ("int_routed_host", "int_subif", "int_loopback",
                   "int_trunk_host", "int_access_host"):
        assert gie_withdrawal_action(
            parent, KEY, {NVPAIR: TWO}, "12.6.0.267", SUPPORTED_PATCH) == ("none", None), parent


def test_registering_this_reset_left_the_sibling_svi_bindings_alone():
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
        BINDING_TABLE)
    rows = {(r["parent_template"], r["parent_nvpair"]): r for r in BINDING_TABLE}
    assert len(BINDING_TABLE) == 234
    assert sum("reset_wire" in r for r in BINDING_TABLE) == 207
    # The four int_vlan identities that remain deliberately unregistered.
    for nv in ("HSRP_GROUPv6", "HSRP_VIPv6", "OSPF_AUTH_KEY", "ospfTag"):
        assert "reset_wire" not in rows[("int_vlan", nv)], nv


# --------------------------------------------------------------------------
# The protected operator state travels in the SAME payload
# --------------------------------------------------------------------------

def test_the_native_lists_and_hsrp_survive_in_the_same_payload():
    """The withdrawal shares one payload with the addresses and HSRP. If the
    reset travelled alone, or the lists were dropped to make room, the operator
    would lose three secondary addresses to a mapping change."""
    have = build_have(PARENT, KEY, TWO)
    profile = svi_profile(
        ipv4_addr="192.0.2.1", ipv4_mask_len=24,
        enable_hsrp=True, hsrp_vip="192.0.2.2", hsrp_group=1, hsrp_version=1,
        secondary_gws=[{"gateway_ip_address": "198.51.100.1/24"},
                       {"gateway_ip_address": "198.51.100.2/24"}])
    _result, calls = drive(profile, "replaced", have)
    nv = sent_nvpairs(calls)
    assert nv[NVPAIR] == ""
    assert "198.51.100.1/24" in nv["secondaryGws"]
    assert "198.51.100.2/24" in nv["secondaryGws"]
    assert nv["ENABLE_HSRP"] == "true"
    assert nv["HSRP_VIP"] == "192.0.2.2"
    assert nv["IP"] == "192.0.2.1"


def test_dropping_the_secondary_list_under_replaced_withdraws_it():
    """A guard, not a feature: this is what must never appear in a live model."""
    have = build_have(PARENT, KEY, TWO,
                      secondary_gws=[{"gateway_ip_address": "198.51.100.1/24"}])
    _result, calls = drive(svi_profile(), "replaced", have)
    assert sent_nvpairs(calls)["secondaryGws"] == ""
