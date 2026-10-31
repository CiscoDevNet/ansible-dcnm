"""The OSPF family on the routed port-channel (registry slice 0b_40): `type: pc`, `mode: l3`, parent int_l3_port_channel.

The 017 int_l3_port_channel body (81c9392e) declares the nineteen OSPF nvPairs int_routed_host registers, with identical
declarations, normalisation, validation and child rendering (compared offline against int_routed_host b5345584). The
rows therefore copy the routed contracts: gate `ospf`, tag and area required with it, eleven options and the five
authentication nvPairs strict or inert under it, the retransmit interval included.

Real main() through gie_withdrawal_harness: only inventory, transport and sleep are mocked, and every HAVE is the payload
the module itself emits for a public profile. Secrets are synthetic and must not appear in a message. Nothing here is
live evidence; the registry-wide withdrawal matrix and the routed-family suites cover the per-row resets as well.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
from unittest.mock import patch

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import BINDING_TABLE, resolve_binding
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import gie_withdrawal_harness as h
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import test_gie_smu017_l3po_pim_bfd as B

L3PO = h.PC_L3
PO_A, PO_B = B.PO_A, B.PO_B
MEM_A, MEM_B = B.MEM_A, B.MEM_B
SYN_MD5 = "SYNTH-MD5-NOT-REAL-0001"
SYN_SIMPLE = "SYNTH-SIMPLE-NOT-REAL-02"
BASE = dict(h.BASE_PC_L3)
ON = {**BASE, "enable_ospf": True, "ospf_tag": "PILOT-OSPF", "ospf_area_id": "0.0.0.0"}
# Representative non-default options: a residue of any of them after a disable or a withdrawal is visible.
OPTIONS = {"ospf_retransmit_interval": 9, "ospf_cost": 42, "ospf_hello_interval": 11, "ospf_dead_interval": 44,
           "ospf_priority": 77, "ospf_transmit_delay": 3, "ospf_mtu_ignore": True, "ospf_shutdown": True,
           "ospf_passive_mode": "passive", "ospf_network_type": "point_to_point", "ospf_bfd_mode": "enable"}
OPTION_WIRE = {"ospfRetransmitInterval": "9", "ospfCost": "42", "ospfHelloInterval": "11", "ospfDeadInterval": "44",
               "ospfPriority": "77", "ospfTransmitDelay": "3", "ospfMtuIgnore": "true", "ospfShutdown": "true",
               "ospfPassiveMode": "passive", "ospfNetworkType": "pointToPoint", "ospfBfdMode": "enable"}
NEUTRAL = {"ospfRetransmitInterval": "", "ospfCost": "", "ospfHelloInterval": "", "ospfDeadInterval": "",
           "ospfPriority": "", "ospfTransmitDelay": "", "ospfMtuIgnore": "false", "ospfShutdown": "false",
           "ospfPassiveMode": "noChange", "ospfNetworkType": "noChange", "ospfBfdMode": "noChange"}
MD5 = {"enable_ospf_auth": True, "ospf_auth_key_id": 7, "ospf_auth_key": SYN_MD5}
FULL = {**ON, **OPTIONS, **MD5}
NATIVE = ("MEMBER_INTERFACES", "PC_MODE", "IP", "PREFIX", "INTF_VRF", "MTU", "DESC", "pimBfdInstance")
OSPF19 = ["ospf", "ospfTag", "OSPF_AREA_ID", "ospfAuthentication", "OSPF_AUTH_KEY_ID", "OSPF_AUTH_KEY",
          "ospfAuthenticationKeyType", "ospfAuthenticationKey", "ospfPassiveMode", "ospfCost", "ospfMtuIgnore",
          "ospfHelloInterval", "ospfDeadInterval", "ospfShutdown", "ospfTransmitDelay", "ospfRetransmitInterval",
          "ospfPriority", "ospfNetworkType", "ospfBfdMode"]
NO_REQUEST = "No configuration or deployment request was sent"


def _po(profile, ifname=PO_A):
    return B._po(profile, ifname)


def _have(profile, ifname=PO_A):
    return B._have(profile, ifname)


def _sent(calls, ifname=PO_A):
    return B._only(calls, ifname)


def _no_secret(result):
    text = json.dumps(result.get("msg", ""))
    assert SYN_MD5 not in text and SYN_SIMPLE not in text


def _ok(result):
    assert not result.get("failed"), result.get("msg")
    _no_secret(result)


def _refused(result, calls, *needles):
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    for needle in needles:
        assert needle in result["msg"], result["msg"]
    _no_secret(result)


# ------------------------------------------------------------------ the rows are the routed contracts
@pytest.mark.parametrize("nvpair", OSPF19)
def test_each_row_is_the_routed_row_on_the_routed_port_channel(nvpair):
    rows = {(r["parent_template"], r["parent_nvpair"]): r for r in BINDING_TABLE}
    mine, routed = rows[(L3PO, nvpair)], rows[(h.ROUTED, nvpair)]
    assert (mine["applicable_interface_type"], mine["applicable_mode"]) == ("pc", "l3")
    # dropped_on_policy_change is the generator's per-parent declaration for an Ethernet policy change (int_routed_host).
    skip = {"parent_template", "applicable_interface_type", "applicable_mode", "evidence_ref", "validated_on",
            "dropped_on_policy_change"}
    assert {k: v for k, v in mine.items() if k not in skip} == {k: v for k, v in routed.items() if k not in skip}


def test_the_slice_cites_the_l3_port_channel_body_for_every_row():
    """evidence_ref is a slice field (not compiled into the table): one per row, on the 017 body read here."""
    import os
    import yaml
    path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "tools", "registry", "slices",
                        "registry_slice_0b_40_smu017_l3po_ospf.yaml")
    rows = yaml.safe_load(open(path))["bindings"]
    assert [r["parent_nvpair"] for r in rows] == OSPF19
    assert all(r["evidence_ref"].startswith("int_l3_port_channel.template@81c9392e#L") for r in rows)


def test_the_parent_carries_exactly_the_ospf_family_and_pim_bfd():
    nvpairs = sorted(r["parent_nvpair"] for r in BINDING_TABLE if r["parent_template"] == L3PO)
    assert nvpairs == sorted(OSPF19 + ["pimBfdInstance"])
    assert resolve_binding(L3PO, "enable_pim_sparse") is None


# ------------------------------------------------------------------ merged
def test_merged_create_sends_the_family_with_the_native_profile():
    result, calls = h.run_configs([_po(FULL)], "merged", [])
    _ok(result)
    nv = _sent(calls)
    assert (nv["ospf"], nv["ospfTag"], nv["OSPF_AREA_ID"]) == ("true", "PILOT-OSPF", "0.0.0.0")
    assert {k: nv[k] for k in OPTION_WIRE} == OPTION_WIRE
    assert (nv["ospfAuthentication"], nv["OSPF_AUTH_KEY_ID"], nv["OSPF_AUTH_KEY"]) == ("true", "7", SYN_MD5)
    assert (nv["MEMBER_INTERFACES"], nv["IP"], nv["PREFIX"]) == (h.PC_MEMBER, "192.0.2.33", "30")
    assert B._paths(calls) == ["POST globalInterface", "POST globalInterface/deploy"]


def test_merged_description_change_carries_every_stored_ospf_value():
    """An update that names no OSPF key keeps the family."""
    have = _have(FULL)
    result, calls = h.run_configs([_po({**BASE, "description": "changed"})], "merged", have)
    _ok(result)
    nv = _sent(calls)
    stored = have[0]["interfaces"][0]["nvPairs"]
    assert {k: nv[k] for k in OSPF19 if k in stored} == {k: stored[k] for k in OSPF19 if k in stored}
    assert nv["DESC"] == "changed"


def test_merged_interval_update_changes_only_the_interval():
    have = _have(FULL)
    result, calls = h.run_configs([_po({**ON, "ospf_retransmit_interval": 30})], "merged", have)
    _ok(result)
    nv, stored = _sent(calls), have[0]["interfaces"][0]["nvPairs"]
    assert nv["ospfRetransmitInterval"] == "30"
    assert {k for k in OSPF19 if k in stored and nv.get(k) != stored[k]} == {"ospfRetransmitInterval"}


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_repeat_of_the_stored_family_writes_nothing(state):
    result, calls = h.run_configs([_po(FULL)], state, _have(FULL))
    _ok(result)
    assert h.writes(calls) == [] and not result.get("changed")


def test_the_retransmit_default_5_is_transported_as_5_like_the_routed_parent():
    """The body normalises "5" to "" (no line); the module transports the value as on int_routed_host."""
    result, calls = h.run_configs([_po({**ON, "ospf_retransmit_interval": 5})], "merged", [])
    _ok(result)
    assert _sent(calls)["ospfRetransmitInterval"] == "5"


@pytest.mark.parametrize("value,ok", [(1, True), (65535, True), (0, False), (65536, False)])
def test_retransmit_bounds_follow_the_body(value, ok):
    result, calls = h.run_configs([_po({**ON, "ospf_retransmit_interval": value})], "merged", [])
    if ok:
        _ok(result)
    else:
        _refused(result, calls, "ospf_retransmit_interval")


# ------------------------------------------------------------------ replaced and overridden (retained)
def test_replaced_omission_withdraws_the_family_coherently():
    """Omitting the family turns the gate off and neutralises every option and the message-digest material in the same
    request; the tag has no neutral value and stays stored, inert (it configures nothing with the gate off)."""
    have = _have(FULL)
    result, calls = h.run_configs([_po(BASE)], "replaced", have)
    _ok(result)
    nv = _sent(calls)
    assert nv["ospf"] == "false" and {k: nv[k] for k in NEUTRAL} == NEUTRAL
    assert (nv["ospfAuthentication"], nv["OSPF_AUTH_KEY"], nv["OSPF_AUTH_KEY_ID"]) == ("false", "", "1")
    assert nv["ospfTag"] == "PILOT-OSPF" and nv["OSPF_AREA_ID"] == "0.0.0.0"
    assert {k: nv[k] for k in NATIVE if k in nv} == {k: have[0]["interfaces"][0]["nvPairs"][k] for k in NATIVE if k in nv}


def test_replaced_keeping_ospf_withdraws_only_the_omitted_options():
    have = _have(FULL)
    keep = {**ON, "ospf_cost": 42}
    result, calls = h.run_configs([_po(keep)], "replaced", have)
    _ok(result)
    nv = _sent(calls)
    assert (nv["ospf"], nv["ospfTag"], nv["ospfCost"]) == ("true", "PILOT-OSPF", "42")
    assert {k: nv[k] for k in NEUTRAL if k != "ospfCost"} == {k: v for k, v in NEUTRAL.items() if k != "ospfCost"}
    assert (nv["ospfAuthentication"], nv["OSPF_AUTH_KEY"]) == ("false", "")


def test_replaced_withdrawal_repeated_writes_nothing():
    result, calls = h.run_configs([_po(BASE)], "replaced", _have(FULL))
    withdrawn = B._as_have(_sent(calls))
    result, calls = h.run_configs([_po(BASE)], "replaced", withdrawn)
    _ok(result)
    assert h.writes(calls) == []


def test_overridden_retained_port_channel_withdraws_like_replaced_and_keeps_the_control():
    have = (_have({**FULL, "members": [MEM_A]}) + _have({**FULL, "members": [MEM_B]}, PO_B)
            + B._member_have(MEM_A, PO_A) + B._member_have(MEM_B, PO_B))
    result, calls = B._run([_po({**BASE, "members": [MEM_A]}), _po({**FULL, "members": [MEM_B]}, PO_B)], "overridden", have)
    _ok(result)
    assert B._identities(calls) == [(B.MODIFY, [[h.SERIAL, PO_A, L3PO]]), (B.DEPLOY, [[h.SERIAL, PO_A]])]
    nv = _sent(calls)
    assert nv["ospf"] == "false" and {k: nv[k] for k in NEUTRAL} == NEUTRAL and nv["OSPF_AUTH_KEY"] == ""


# ------------------------------------------------------------------ deleted and overridden (omitted)
def test_deleted_retires_the_aggregate_with_its_ospf_and_a_repeat_writes_nothing():
    target = [{"name": PO_A, "type": "pc", "switch": [h.SWITCH_IP]}]
    have = _have({**FULL, "members": [MEM_A]}) + B._member_have(MEM_A, PO_A)
    result, calls = B._run(target, "deleted", have)
    _ok(result)
    assert B._identities(calls) == [(B.MARK, [[h.SERIAL, PO_A]]), (B.DEPLOY, [[h.SERIAL, PO_A]])]
    result, calls = B._run(target, "deleted", [])
    assert h.writes(calls) == []


def test_overridden_omitted_port_channel_is_deleted_with_the_native_member_reset():
    have = (_have({**FULL, "members": [MEM_A]}) + _have({**FULL, "members": [MEM_B]}, PO_B)
            + B._member_have(MEM_A, PO_A) + B._member_have(MEM_B, PO_B))
    result, calls = B._run([_po({**FULL, "members": [MEM_B]}, PO_B)], "overridden", have)
    _ok(result)
    assert B._identities(calls) == [
        (B.MARK, [[h.SERIAL, PO_A]]), (B.DEPLOY, [[h.SERIAL, PO_A]]),
        (B.MODIFY, [[h.SERIAL, MEM_A, h.ROUTED]]), (B.DEPLOY, [[h.SERIAL, MEM_A]]),
    ]


# ------------------------------------------------------------------ query
def test_query_returns_the_configured_ospf_values_unchanged():
    target = _have(FULL)
    writes = []
    with patch.object(h, "_transport", B._query_transport(target, writes)):
        result, calls = h.run_configs([{"name": PO_A, "switch": [h.SWITCH_IP]}], "query", [])
    _ok(result)
    assert writes == [] and h.writes(calls) == []
    assert result["response"] == target
    nv = result["response"][0]["interfaces"][0]["nvPairs"]
    assert (nv["ospf"], nv["ospfRetransmitInterval"], nv["ospfTag"]) == ("true", "9", "PILOT-OSPF")


# ------------------------------------------------------------------ the gate: disable, dependents, the tag
def test_merged_explicit_disable_neutralises_every_stored_option():
    have = _have(FULL)
    result, calls = h.run_configs([_po({**BASE, "enable_ospf": False})], "merged", have)
    _ok(result)
    nv = _sent(calls)
    assert nv["ospf"] == "false" and {k: nv[k] for k in NEUTRAL} == NEUTRAL
    assert (nv["ospfAuthentication"], nv["OSPF_AUTH_KEY"], nv["OSPF_AUTH_KEY_ID"]) == ("false", "", "1")
    assert nv["ospfTag"] == "PILOT-OSPF", "the tag has no neutral value: kept as stored, it configures nothing"


def test_an_explicit_option_while_disabling_is_refused_before_any_write():
    result, calls = h.run_configs([_po({**BASE, "enable_ospf": False, "ospf_retransmit_interval": 9})], "merged",
                                  _have(FULL))
    _refused(result, calls, "ospf_retransmit_interval", NO_REQUEST)


def test_a_tag_cannot_turn_ospf_on_by_itself():
    """Over a port-channel with OSPF off, sending only a tag leaves the gate off: the tag is inert, not a feature."""
    have = _have({**BASE, "enable_ospf": False})
    result, calls = h.run_configs([_po({**BASE, "ospf_tag": "OTHER-TAG"})], "merged", have)
    _ok(result)
    nv = _sent(calls)
    assert nv["ospf"] == "false" and nv["ospfTag"] == "OTHER-TAG"
    assert not any(nv.get(k) not in ("", None, NEUTRAL[k]) for k in NEUTRAL)


def test_disable_then_repeat_is_a_noop():
    result, calls = h.run_configs([_po({**BASE, "enable_ospf": False})], "merged", _have(FULL))
    disabled = B._as_have(_sent(calls))
    result, calls = h.run_configs([_po({**BASE, "enable_ospf": False})], "merged", disabled)
    _ok(result)
    assert h.writes(calls) == []


# ------------------------------------------------------------------ authentication (synthetic secrets, redacted)
def test_message_digest_rotation_changes_only_the_key():
    have = _have(FULL)
    result, calls = h.run_configs([_po({**FULL, "ospf_auth_key": "SYNTH-MD5-NOT-REAL-0002"})], "merged", have)
    _ok(result)
    nv, stored = _sent(calls), have[0]["interfaces"][0]["nvPairs"]
    assert {k for k in OSPF19 if k in stored and nv.get(k) != stored[k]} == {"OSPF_AUTH_KEY"}


def test_message_digest_without_its_key_is_left_to_the_template_refusal():
    """IsMandatory="ospfAuthentication==true" on OSPF_AUTH_KEY: the module does not repeat that rule on any parent; the
    controller answers 207 'Validation failed for following fields: [OSPF_AUTH_KEY]' (measured on int_routed_host)."""
    result, calls = h.run_configs([_po({**ON, "enable_ospf_auth": True, "ospf_auth_key_id": 7})], "merged", [])
    _ok(result)
    nv = _sent(calls)
    assert nv["ospfAuthentication"] == "true" and "OSPF_AUTH_KEY" not in nv


def test_simple_key_with_its_type_and_its_withdrawal():
    simple = {**ON, "ospf_authentication_key": SYN_SIMPLE, "ospf_authentication_key_type": "7"}
    result, calls = h.run_configs([_po(simple)], "merged", [])
    _ok(result)
    assert (_sent(calls)["ospfAuthenticationKey"], _sent(calls)["ospfAuthenticationKeyType"]) == (SYN_SIMPLE, "7")
    result, calls = h.run_configs([_po(ON)], "replaced", _have(simple))
    _ok(result)
    assert _sent(calls)["ospfAuthenticationKey"] == ""


def test_a_stored_key_in_another_form_is_resent_and_that_is_storage_normalisation_not_idempotency():
    """The key compares exactly (string_compare exact, as on int_routed_host). If the controller stores a different
    string for the same secret, every run resends it. That is the storage-normalisation case measured on
    int_routed_host (a type 0 simple key the switch stores as type 3 stays Out-of-Sync); with the stored string sent
    back, the repeat is a no-op (test_repeat_of_the_stored_family_writes_nothing)."""
    have = _have(FULL)
    have[0]["interfaces"][0]["nvPairs"]["OSPF_AUTH_KEY"] = "CONTROLLER-NORMALISED-FORM"
    result, calls = h.run_configs([_po(FULL)], "merged", have)
    _ok(result)
    assert _sent(calls)["OSPF_AUTH_KEY"] == SYN_MD5


def test_neither_secret_appears_in_a_refusal_message():
    bad = {**BASE, "enable_ospf": False, "ospf_auth_key": SYN_MD5, "ospf_authentication_key": SYN_SIMPLE,
           "enable_ospf_auth": True}
    result, calls = h.run_configs([_po(bad)], "merged", _have(FULL))
    _refused(result, calls, NO_REQUEST)


# ------------------------------------------------------------------ unrelated fields, gate, check mode, counts
def test_an_ospf_change_keeps_membership_address_and_pim_bfd():
    have = _have({**FULL, "enable_pim_bfd_instance": True})
    result, calls = h.run_configs([_po({**FULL, "enable_pim_bfd_instance": True, "ospf_cost": 50})], "merged", have)
    _ok(result)
    nv, stored = _sent(calls), have[0]["interfaces"][0]["nvPairs"]
    assert {k: nv[k] for k in NATIVE} == {k: stored[k] for k in NATIVE}
    assert nv["ospfCost"] == "50" and nv["pimBfdInstance"] == "true"


@pytest.mark.parametrize("patch_version", [None, "4.3.1.0175006011"], ids=["no_patch_version", "smu011"])
def test_the_family_needs_an_approved_patch_version(patch_version):
    result, calls = h.run_configs([_po(ON)], "merged", [], patch_version=patch_version)
    assert result.get("failed") and h.writes(calls) == []


def test_numeric_441_is_admitted():
    result, calls = h.run_configs([_po(ON)], "merged", [], patch_version="4.4.1")
    _ok(result)
    assert _sent(calls)["ospf"] == "true"


def test_check_mode_reports_the_withdrawal_and_writes_nothing():
    result, calls = h.run_configs([_po(BASE)], "replaced", _have(FULL), check_mode=True)
    _ok(result)
    assert h.writes(calls) == [] and result.get("changed") is True


@pytest.mark.parametrize("profile,have", [
    (lambda: FULL, lambda: []),
    (lambda: {**FULL, "ospf_cost": 50}, lambda: _have(FULL)),
    (lambda: FULL, lambda: _have(FULL)),
], ids=["create", "update", "repeat"])
def test_ospf_adds_no_read_or_write_over_the_plain_port_channel(profile, have):
    """Matched counts: the OSPF family costs no extra request against the same scenario without OSPF."""
    plain = {"create": (BASE, []), "update": ({**BASE, "description": "x"}, _have(BASE)), "repeat": (BASE, _have(BASE))}
    result, calls = h.run_configs([_po(profile())], "merged", have())
    _ok(result)
    key = "create" if not have() else ("repeat" if profile() == FULL else "update")
    p_prof, p_have = plain[key]
    _r, p_calls = h.run_configs([_po(p_prof)], "merged", p_have)
    got, ref = h.split_calls(calls), h.split_calls(p_calls)
    assert {k: len(v) for k, v in got.items()} == {k: len(v) for k, v in ref.items()}
