"""PIM sparse mode and DR priority on the routed port-channel (registry slice 0b_41).

    int_l3_port_channel  ENABLE_PIM_SPARSE  enable_pim_sparse  boolean        reset "false"
    int_l3_port_channel  PIM_DR_PRIORITY    pim_dr_priority    1-4294967295   reset "1"

`type: pc`, `mode: l3` selects int_l3_port_channel. The body declares both fields and handles them independently:
sparse mode "true" creates pim_interface; a priority other than "" and "1" creates interface_pim_dr_priority. Neither
branch deletes its child; every add() first deletes all children of the port-channel. Read from the template body, not
measured live.

Real main() through gie_withdrawal_harness: only inventory, transport and sleep are mocked, and every HAVE is the payload
the module itself emits for a public profile. Values are synthetic.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import patch

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding, resolve_by_nvpair
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import gie_withdrawal_harness as h
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import test_gie_smu017_l3po_pim_bfd as po

L3PO = h.PC_L3
SPARSE, SPARSE_NV = "enable_pim_sparse", "ENABLE_PIM_SPARSE"
PRIO, PRIO_NV = "pim_dr_priority", "PIM_DR_PRIORITY"
PO_A, PO_B = h.PC_A, po.PO_B
BASE = dict(h.BASE_PC_L3)
BOTH = {**BASE, SPARSE: True, PRIO: 200}
OSPF = {"enable_ospf": True, "ospf_tag": "PILOT-OSPF", "ospf_area_id": "0.0.0.0", "ospf_cost": 42}
OSPF_NV = ("ospf", "ospfTag", "OSPF_AREA_ID", "ospfCost")
NATIVE = po.NATIVE + ("pimBfdInstance",) + OSPF_NV


def _native(nv):
    return {k: nv.get(k) for k in NATIVE}


# ------------------------------------------------------------------ the rows are what the body declares
def test_the_rows_match_the_body_and_the_routed_rows():
    for key, nv, typ, reset in ((SPARSE, SPARSE_NV, "boolean", "false"), (PRIO, PRIO_NV, "integer", "1")):
        b = resolve_binding(L3PO, key)
        assert b is not None, key
        assert (b["parent_nvpair"], b["type"], b["reset_wire"], b["mechanism"]) == (nv, typ, reset, "passthrough")
        assert (b["applicable_interface_type"], b["applicable_mode"]) == ("pc", "l3")
        assert resolve_by_nvpair(L3PO, nv) is b
        assert "inert_when" not in b, "the body does not relate the two fields"
        routed = resolve_binding(h.ROUTED, key)
        for field in ("parent_nvpair", "type", "reset_wire", "default_template", "min_value", "max_value"):
            assert b.get(field) == routed.get(field), (key, field)
    prio = resolve_binding(L3PO, PRIO)
    assert (prio["min_value"], prio["max_value"], prio["default_template"]) == (1, 4294967295, 1)


# ------------------------------------------------------------------ wire forms, bounds, independence
@pytest.mark.parametrize("profile, wire", [
    ({SPARSE: True}, {SPARSE_NV: "true"}),
    ({SPARSE: False}, {SPARSE_NV: "false"}),
    ({PRIO: 1}, {PRIO_NV: "1"}),
    ({PRIO: 4294967295}, {PRIO_NV: "4294967295"}),
    ({SPARSE: True, PRIO: 200}, {SPARSE_NV: "true", PRIO_NV: "200"}),
], ids=["sparse_true", "sparse_false", "priority_min", "priority_max", "together"])
def test_create_sends_each_field_alone_or_together_in_wire_form(profile, wire):
    result, calls = h.run_configs([po._po({**BASE, **profile})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = po._only(calls)
    assert {k: nv.get(k) for k in wire} == wire
    for k in (SPARSE_NV, PRIO_NV):
        if k not in wire:
            assert k not in nv, "an omitted field must not be sent on create"
    assert all(isinstance(nv[k], str) for k in wire)
    assert po._paths(calls) == ["POST globalInterface", "POST globalInterface/deploy"], po._paths(calls)


@pytest.mark.parametrize("value", [0, 4294967296, -1, "high"])
def test_an_out_of_range_or_non_integer_priority_is_refused_before_any_write(value):
    result, calls = h.run_configs([po._po({**BASE, PRIO: value})], "merged", [])
    assert result.get("failed") and PRIO in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


def test_a_non_boolean_sparse_value_is_refused_before_any_write():
    result, calls = h.run_configs([po._po({**BASE, SPARSE: "maybe"})], "merged", [])
    assert result.get("failed") and SPARSE in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


def test_a_priority_without_sparse_mode_is_accepted_as_the_body_allows():
    result, calls = h.run_configs([po._po({**BASE, SPARSE: False, PRIO: 50})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = po._only(calls)
    assert (nv[SPARSE_NV], nv[PRIO_NV]) == ("false", "50")


# ------------------------------------------------------------------ merged
@pytest.mark.parametrize("change, wire", [
    ({SPARSE: False}, {SPARSE_NV: "false", PRIO_NV: "200"}),
    ({PRIO: 1}, {SPARSE_NV: "true", PRIO_NV: "1"}),
    ({PRIO: 4294967295}, {SPARSE_NV: "true", PRIO_NV: "4294967295"}),
], ids=["sparse_off", "priority_default", "priority_max"])
def test_merged_change_of_one_field_keeps_the_other_and_the_native_values(change, wire):
    have = po._have(BOTH)
    result, calls = h.run_configs([po._po({**BASE, **change})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = po._only(calls)
    assert {k: nv[k] for k in wire} == wire
    assert _native(nv) == _native(have[0]["interfaces"][0]["nvPairs"])
    assert po._paths(calls) == ["POST interface/modify", "POST globalInterface/deploy"], po._paths(calls)


def test_merged_omission_carries_both_stored_values_into_another_change():
    have = po._have(BOTH)
    result, calls = h.run_configs([po._po({**BASE, "description": "changed"})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = po._only(calls)
    assert (nv[SPARSE_NV], nv[PRIO_NV], nv["DESC"]) == ("true", "200", "changed")


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_repeat_of_the_stored_values_writes_nothing(state):
    result, calls = h.run_configs([po._po(BOTH)], state, po._have(BOTH))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and not result.get("changed")


def test_explicit_false_differs_from_omission_under_merged():
    have = po._have(BOTH)
    result, calls = h.run_configs([po._po({**BASE, SPARSE: False})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert po._only(calls)[SPARSE_NV] == "false"
    result, calls = h.run_configs([po._po(BASE)], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [], "omission under merged keeps the stored values"


def test_a_pim_change_keeps_the_stored_ospf_and_pim_bfd_values():
    have = po._have({**BOTH, **OSPF, "enable_pim_bfd_instance": True})
    stored = have[0]["interfaces"][0]["nvPairs"]
    assert (stored["ospf"], stored["ospfCost"], stored["pimBfdInstance"]) == ("true", "42", "true")
    result, calls = h.run_configs([po._po({**BASE, PRIO: 300})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = po._only(calls)
    assert (nv[PRIO_NV], nv[SPARSE_NV]) == ("300", "true")
    assert _native(nv) == _native(stored)


# ------------------------------------------------------------------ replaced: field reset, not interface removal
@pytest.mark.parametrize("kept, wire", [
    ({}, {SPARSE_NV: "false", PRIO_NV: "1"}),
    ({SPARSE: True}, {SPARSE_NV: "true", PRIO_NV: "1"}),
    ({PRIO: 200}, {SPARSE_NV: "false", PRIO_NV: "200"}),
], ids=["both_omitted", "priority_omitted", "sparse_omitted"])
def test_replaced_omission_resets_only_the_omitted_field_and_keeps_the_port_channel(kept, wire):
    have = po._have({**BOTH, **OSPF, "enable_pim_bfd_instance": True})
    result, calls = h.run_configs([po._po({**BASE, **OSPF, "enable_pim_bfd_instance": True, **kept})], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = po._only(calls)
    assert {k: nv[k] for k in wire} == wire
    assert _native(nv) == _native(have[0]["interfaces"][0]["nvPairs"])
    assert po._paths(calls) == ["POST interface/modify", "POST globalInterface/deploy"], "a reset is an update, not a removal"


@pytest.mark.parametrize("state", ["replaced", "merged"])
def test_repeat_after_the_reset_writes_nothing(state):
    result, calls = h.run_configs([po._po(BASE)], "replaced", po._have(BOTH))
    assert not result.get("failed"), result.get("msg")
    reset = po._as_have(po._only(calls))
    result, calls = h.run_configs([po._po(BASE)], state, reset)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_replaced_without_the_fields_on_a_port_channel_that_never_had_them_writes_nothing():
    result, calls = h.run_configs([po._po(BASE)], "replaced", po._have(BASE))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


# ------------------------------------------------------------------ overridden, deleted, query, check mode
def _aggregate(profile_a, profile_b):
    return (po._have({**profile_a, "members": [po.MEM_A]}) + po._have({**profile_b, "members": [po.MEM_B]}, PO_B)
            + po._member_have(po.MEM_A, PO_A) + po._member_have(po.MEM_B, PO_B))


def test_overridden_retained_port_channel_resets_the_fields_and_keeps_the_control():
    configs = [po._po({**BASE, "members": [po.MEM_A]}), po._po({**BOTH, "members": [po.MEM_B]}, PO_B)]
    result, calls = po._run(configs, "overridden", _aggregate(BOTH, BOTH))
    assert not result.get("failed"), result.get("msg")
    assert po._identities(calls) == [(po.MODIFY, [[h.SERIAL, PO_A, L3PO]]), (po.DEPLOY, [[h.SERIAL, PO_A]])]
    nv = po._only(calls)
    assert (nv[SPARSE_NV], nv[PRIO_NV], nv["MEMBER_INTERFACES"]) == ("false", "1", po.MEM_A)


def test_overridden_port_channel_left_out_is_deleted_and_the_retained_one_kept():
    result, calls = po._run([po._po({**BOTH, "members": [po.MEM_B]}, PO_B)], "overridden", _aggregate(BOTH, BOTH))
    assert not result.get("failed"), result.get("msg")
    assert po._identities(calls) == [
        (po.MARK, [[h.SERIAL, PO_A]]), (po.DEPLOY, [[h.SERIAL, PO_A]]),
        (po.MODIFY, [[h.SERIAL, po.MEM_A, h.ROUTED]]), (po.DEPLOY, [[h.SERIAL, po.MEM_A]]),
    ]


def test_deleted_removes_the_port_channel_not_the_field_and_a_repeat_writes_nothing():
    target = [{"name": PO_A, "type": "pc", "switch": [h.SWITCH_IP]}]
    have = po._have({**BOTH, "members": [po.MEM_A]}) + po._member_have(po.MEM_A, PO_A)
    result, calls = po._run(target, "deleted", have)
    assert not result.get("failed"), result.get("msg")
    assert po._identities(calls) == [(po.MARK, [[h.SERIAL, PO_A]]), (po.DEPLOY, [[h.SERIAL, PO_A]])]
    result, calls = po._run(target, "deleted", [])
    assert not result.get("failed"), result.get("msg")
    assert po._identities(calls) == []


def test_query_returns_the_controller_values_unchanged():
    target = po._have(BOTH)
    writes = []
    with patch.object(h, "_transport", po._query_transport(target + po._have(BASE, PO_B), writes)):
        result, calls = h.run_configs([{"name": PO_A, "switch": [h.SWITCH_IP]}], "query", [])
    assert not result.get("failed"), result.get("msg")
    assert writes == [] and h.writes(calls) == [] and not result.get("changed")
    assert result["response"] == target
    nv = result["response"][0]["interfaces"][0]["nvPairs"]
    assert (nv[SPARSE_NV], nv[PRIO_NV]) == ("true", "200")


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_check_mode_reports_the_change_and_writes_nothing(state):
    result, calls = h.run_configs([po._po({**BASE, PRIO: 5})], state, po._have(BOTH), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and result.get("changed") is True


# ------------------------------------------------------------------ version gate and unaffected controls
@pytest.mark.parametrize("patch_version", [None, "4.3.1.0175006011"], ids=["no_patch_version", "smu011"])
@pytest.mark.parametrize("key, value", [(SPARSE, True), (PRIO, 200)])
def test_each_field_needs_an_approved_patch_version(patch_version, key, value):
    result, calls = h.run_configs([po._po({**BASE, key: value})], "merged", [], patch_version=patch_version)
    assert result.get("failed") and key in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("patch_version", [None, "4.3.1.0175006011"], ids=["no_patch_version", "smu011"])
def test_omission_under_a_closed_gate_resets_nothing(patch_version):
    result, calls = h.run_configs([po._po(BASE)], "replaced", po._have(BOTH), patch_version=patch_version)
    assert not result.get("failed"), result.get("msg")
    for _policy, nv in po._emitted(calls).values():
        assert (nv.get(SPARSE_NV), nv.get(PRIO_NV)) in ((None, None), ("true", "200")), nv


def test_a_plain_l3_port_channel_payload_is_unchanged():
    result, calls = h.run_configs([po._po(BASE)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = po._only(calls)
    assert SPARSE_NV not in nv and PRIO_NV not in nv


@pytest.mark.parametrize("parent", [h.PC_TRUNK, h.PC_ACCESS, h.PC_DOT1Q])
@pytest.mark.parametrize("key, value", [(SPARSE, True), (PRIO, 200)])
def test_the_keys_stay_refused_on_the_layer2_port_channels(parent, key, value):
    result, calls = h.run_configs([h.cfg_for(parent, {**h.base_for(parent), key: value})], "merged", [])
    assert result.get("failed") and key in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


def test_the_routed_ethernet_rows_are_unchanged():
    result, calls = h.run_configs([h.cfg(h.IF_A, {**h.BASE_ROUTED, SPARSE: True, PRIO: 200})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    nv = found[0]["interfaces"][0]["nvPairs"]
    assert [p["policy"] for p in found] == [h.ROUTED] and (nv[SPARSE_NV], nv[PRIO_NV]) == ("true", "200")
