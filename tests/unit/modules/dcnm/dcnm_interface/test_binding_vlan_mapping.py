"""VLAN mapping on the Ethernet, port-channel and vPC trunk parents (registry slice vm1).

enable_vlan_mapping is a boolean binding. vlan_mapping_entries is a typed list (struct_list): the list contract in
interface_struct_lists validates it, writes the wrapper the parent templates load, reads the controller value only in
that form and compares two values by their rows. Expected wire strings are written by hand from the template bodies,
not produced by the contract. Module cases run the real main() through helpers/binding_harness on all three parents.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine as engine
from ansible_collections.cisco.dcnm.plugins.module_utils import interface_struct_lists as lists
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding

from .helpers.binding_harness import ACCESS
from .helpers.binding_harness import PC_TRUNK
from .helpers.binding_harness import SUPPORTED
from .helpers.binding_harness import SUPPORTED_PATCH
from .helpers.binding_harness import TRUNK
from .helpers.binding_harness import VPC_TRUNK
from .helpers.binding_harness import base_for
from .helpers.binding_harness import build_have
from .helpers.binding_harness import diff_nvpairs
from .helpers.binding_harness import request_nvpairs
from .helpers.binding_harness import run
from .helpers.binding_harness import split_calls
from .helpers import role_reset

PARENTS = (TRUNK, PC_TRUNK, VPC_TRUNK)
ENTRIES = "vlan_mapping_entries"
ENABLE = "enable_vlan_mapping"

TRANSLATION = [{"customer_vlan": 100, "provider_vlan": 200},
               {"customer_vlan": 101, "customer_inner_vlan": 5, "provider_vlan": 201}]
TRANSLATION_WIRE = (
    '{"vlanMappingEntries":['
    '{"customerVlan":"100","dot1qTunnel":"false","customerInnerVlan":"","providerVlan":"200"},'
    '{"customerVlan":"101","dot1qTunnel":"false","customerInnerVlan":"5","providerVlan":"201"}]}'
)
TUNNEL = [{"customer_vlan": "10-20,30", "dot1q_tunnel": True, "provider_vlan": 300},
          {"customer_vlan": 40, "dot1q_tunnel": True, "provider_vlan": 301}]
TUNNEL_WIRE = (
    '{"vlanMappingEntries":['
    '{"customerVlan":"10-20,30","dot1qTunnel":"true","customerInnerVlan":"","providerVlan":"300"},'
    '{"customerVlan":"40","dot1qTunnel":"true","customerInnerVlan":"","providerVlan":"301"}]}'
)


def _nv(calls, nvpair):
    """The value of `nvpair` in the single outgoing interface payload."""
    found = [nv[nvpair] for nv in request_nvpairs(calls) if nvpair in nv]
    assert len(found) == 1, found
    return found[0]


def _have_with(parent, **profile):
    return build_have(parent, **profile)


def _unrelated(parent):
    """A change to a field outside this feature, so that a merged run writes."""
    return {"peer1_description": "changed"} if parent == VPC_TRUNK else {"description": "changed"}


def _set_have_nv(have, **nvpairs):
    have = copy.deepcopy(have)
    have[0]["interfaces"][0]["nvPairs"].update(nvpairs)
    return have


# ------------------------------------------------------------------ the list contract
@pytest.mark.parametrize("value, wire", [
    ([], ""),
    (TRANSLATION, TRANSLATION_WIRE),
    (TUNNEL, TUNNEL_WIRE),
], ids=["empty", "translation", "dot1q-tunnel"])
def test_the_wire_is_the_wrapper_of_string_rows(value, wire):
    assert lists.struct_to_wire(lists.CONTRACT_VLAN_MAPPING, ENTRIES, "vlanMappingEntries", value) == wire
    if wire:
        # The vPC per-peer child reads the same value with ast.literal_eval, the parents with json.loads.
        import ast
        assert ast.literal_eval(wire) == json.loads(wire)


@pytest.mark.parametrize("value, rule", [
    ("100:200", "must be a list"),
    ([["100", "200"]], "must be a mapping"),
    ([{"customer_vlan": 100, "provider_vlan": 200, "inner": 5}], "unsupported key"),
    ([{"provider_vlan": 200}], "requires 'customer_vlan'"),
    ([{"customer_vlan": 100}], "requires 'provider_vlan'"),
    ([{"customer_vlan": 100, "provider_vlan": None}], "requires 'provider_vlan'"),
    ([{"customer_vlan": 100, "provider_vlan": "200"}], "'provider_vlan' must be an integer"),
    ([{"customer_vlan": 100, "provider_vlan": True}], "'provider_vlan' must be an integer"),
    ([{"customer_vlan": 100, "provider_vlan": 4095}], "between 1 and 4094"),
    ([{"customer_vlan": 0, "provider_vlan": 200}], "between 1 and 4094"),
    ([{"customer_vlan": 100, "provider_vlan": 200, "dot1q_tunnel": "true"}], "'dot1q_tunnel' must be a boolean"),
    ([{"customer_vlan": "10-20", "provider_vlan": 200}], "range only with 'dot1q_tunnel' true"),
    ([{"customer_vlan": "10,11", "provider_vlan": 200}], "range only with 'dot1q_tunnel' true"),
    ([{"customer_vlan": "10 - 20", "provider_vlan": 200, "dot1q_tunnel": True}], "no spaces"),
    ([{"customer_vlan": "010", "provider_vlan": 200}], "no spaces"),
    ([{"customer_vlan": "20-10", "provider_vlan": 200, "dot1q_tunnel": True}], "start is not below its end"),
    ([{"customer_vlan": "10-10", "provider_vlan": 200, "dot1q_tunnel": True}], "start is not below its end"),
    ([{"customer_vlan": "10-20,15", "provider_vlan": 200, "dot1q_tunnel": True}], "more than once"),
    ([{"customer_vlan": "10-4095", "provider_vlan": 200, "dot1q_tunnel": True}], "between 1 and 4094"),
    ([{"customer_vlan": 100, "provider_vlan": 200, "dot1q_tunnel": True, "customer_inner_vlan": 5}],
     "cannot set 'customer_inner_vlan'"),
    ([{"customer_vlan": 100, "provider_vlan": 200, "customer_inner_vlan": "5"}], "'customer_inner_vlan' must be an integer"),
    ([{"customer_vlan": 100, "provider_vlan": 200}, {"customer_vlan": 101, "provider_vlan": 200}],
     "provider VLAN 200, which an earlier item already uses"),
    ([{"customer_vlan": 100, "provider_vlan": 200}, {"customer_vlan": 100, "provider_vlan": 201}],
     "repeats a customer VLAN"),
    ([{"customer_vlan": "10-20", "provider_vlan": 200, "dot1q_tunnel": True},
      {"customer_vlan": 15, "provider_vlan": 201, "dot1q_tunnel": True}], "repeats a customer VLAN"),
    ([{"customer_vlan": 100, "provider_vlan": 200},
      {"customer_vlan": 101, "provider_vlan": 201, "dot1q_tunnel": True}], "cannot mix"),
], ids=lambda v: v if isinstance(v, str) and len(v) < 40 else None)
def test_the_contract_refuses_what_the_template_would_drop_or_reject(value, rule):
    with pytest.raises(lists.StructListError, match=rule):
        lists.struct_validate_input(lists.CONTRACT_VLAN_MAPPING, ENTRIES, value)


def test_rows_compare_in_any_order_with_their_types_kept():
    def form(raw):
        return lists.struct_compare_form(lists.CONTRACT_VLAN_MAPPING, raw)

    rows = json.loads(TRANSLATION_WIRE)["vlanMappingEntries"]
    reordered = json.dumps({"vlanMappingEntries": rows[::-1]})
    assert form(TRANSLATION_WIRE) == form(reordered)
    # A native integer is not its string spelling: the template formats both alike but tests "-" in the customer VLAN.
    native = json.dumps({"vlanMappingEntries": [dict(rows[0], providerVlan=200), rows[1]]})
    assert form(native) != form(TRANSLATION_WIRE)
    # A repeated row is a different value.
    assert form(json.dumps({"vlanMappingEntries": rows + rows[:1]})) != form(TRANSLATION_WIRE)
    assert form("") == form('{"vlanMappingEntries":[]}') == ()


@pytest.mark.parametrize("raw", [
    "{'vlanMappingEntries': []}",                      # a Python literal: the parents use json.loads
    '[{"customerVlan":"100"}]',                        # a bare list: the parents index the wrapper
    '{"vlanMappingEntries":[],"other":[]}',
    '{"vlanMappingEntries":["100"]}',
    '{"vlanMappingEntries":',
    None,
    7,
])
def test_a_value_the_template_cannot_read_equals_nothing(raw):
    assert lists.struct_read(lists.CONTRACT_VLAN_MAPPING, raw) is None
    form = lists.struct_compare_form(lists.CONTRACT_VLAN_MAPPING, raw)
    assert form != lists.struct_compare_form(lists.CONTRACT_VLAN_MAPPING, raw)
    assert not lists.struct_is_empty(lists.CONTRACT_VLAN_MAPPING, raw)


# ------------------------------------------------------------------ the engine
@pytest.mark.parametrize("parent", PARENTS)
def test_the_rows_are_registered_on_the_three_trunk_parents(parent):
    enable = resolve_binding(parent, ENABLE)
    entries = resolve_binding(parent, ENTRIES)
    assert (enable["parent_nvpair"], enable["type"], enable["default_template"]) == ("enableVlanMapping", "boolean", False)
    assert (entries["parent_nvpair"], entries["type"], entries["struct_contract"]) == (
        "vlanMappingEntries", "struct_list", "vlan_mapping_entries")
    assert entries["inert_when"] == {"nvpair": "enableVlanMapping", "value": "false", "required": True}
    # No reset is established for either field.
    assert "reset_wire" not in enable and "reset_wire" not in entries
    assert resolve_binding(ACCESS, ENTRIES) is None


@pytest.mark.parametrize("parent", PARENTS)
def test_the_engine_transports_the_list_as_its_wire_string(parent):
    add, err = engine.gie_contribute_nvpairs(parent, {ENABLE: True, ENTRIES: TUNNEL}, SUPPORTED, SUPPORTED_PATCH)
    assert err is None
    assert add == {"enableVlanMapping": "true", "vlanMappingEntries": TUNNEL_WIRE}
    add, err = engine.gie_contribute_nvpairs(parent, {ENTRIES: TUNNEL}, SUPPORTED, None)
    assert add is None and "patch_version" in err


@pytest.mark.parametrize("parent", PARENTS)
def test_the_controller_value_must_be_readable(parent):
    for raw in ("", '{"vlanMappingEntries":[]}', TRANSLATION_WIRE):
        assert engine.gie_validate_binding_value(parent, ENTRIES, raw, value_source="have") == raw
    with pytest.raises(engine.GieBindingError, match="not a list the template can read"):
        engine.gie_validate_binding_value(parent, ENTRIES, "{'vlanMappingEntries': []}", value_source="have")
    with pytest.raises(engine.GieBindingError, match="item 1 requires 'provider_vlan'"):
        engine.gie_validate_binding_value(parent, ENTRIES, [{"customer_vlan": 1}])


@pytest.mark.parametrize("parent", PARENTS)
def test_withdrawal_has_no_reset_to_send(parent):
    def action(key, have):
        return engine.gie_withdrawal_action(parent, key, have, SUPPORTED, SUPPORTED_PATCH)[0]

    assert action(ENTRIES, '{"vlanMappingEntries":[]}') == engine.GIE_WITHDRAW_NONE
    assert action(ENTRIES, TRANSLATION_WIRE) == engine.GIE_WITHDRAW_UNCLASSIFIED
    assert action(ENABLE, "false") == engine.GIE_WITHDRAW_NONE
    assert action(ENABLE, "true") == engine.GIE_WITHDRAW_UNSUPPORTED


# ------------------------------------------------------------------ the module, all three parents
@pytest.mark.parametrize("parent", PARENTS)
@pytest.mark.parametrize("value, wire", [(TRANSLATION, TRANSLATION_WIRE), (TUNNEL, TUNNEL_WIRE)],
                         ids=["translation", "dot1q-tunnel"])
def test_merged_create_sends_and_reports_the_list(parent, value, wire):
    result, calls = run(base_for(parent, **{ENABLE: True, ENTRIES: value}), "merged", parent=parent)
    assert not result.get("failed"), result.get("msg")
    assert _nv(calls, "enableVlanMapping") == "true"
    assert _nv(calls, "vlanMappingEntries") == wire
    assert any(nv.get("vlanMappingEntries") == wire for nv in diff_nvpairs(result))
    assert not any(k.startswith("PEER") and "VlanMapping" in k for nv in request_nvpairs(calls) for k in nv)


@pytest.mark.parametrize("parent", PARENTS)
def test_merged_repeat_and_reorder_send_nothing(parent):
    have = _have_with(parent, **{ENABLE: True, ENTRIES: TRANSLATION})
    for value in (TRANSLATION, TRANSLATION[::-1]):
        result, calls = run(base_for(parent, **{ENABLE: True, ENTRIES: value}), "merged", have, parent=parent)
        assert not result.get("failed"), result.get("msg")
        assert split_calls(calls)["updates"] == [] and split_calls(calls)["deploys"] == [], value
        assert result["changed"] is False


@pytest.mark.parametrize("parent", PARENTS)
def test_merged_change_sends_the_whole_new_list(parent):
    have = _have_with(parent, **{ENABLE: True, ENTRIES: TRANSLATION})
    result, calls = run(base_for(parent, **{ENTRIES: TRANSLATION[:1]}), "merged", have, parent=parent)
    assert not result.get("failed"), result.get("msg")
    assert _nv(calls, "vlanMappingEntries") == (
        '{"vlanMappingEntries":[{"customerVlan":"100","dot1qTunnel":"false","customerInnerVlan":"","providerVlan":"200"}]}')
    assert _nv(calls, "enableVlanMapping") == "true"   # carried from HAVE


@pytest.mark.parametrize("parent", PARENTS)
def test_merged_omission_carries_the_stored_text_unchanged(parent):
    have = _have_with(parent, **{ENABLE: True, ENTRIES: TRANSLATION})
    # A stored value the module would not write itself (native integers, reversed rows) still round-trips as stored.
    stored = json.dumps({"vlanMappingEntries": [
        {"customerVlan": 7, "dot1qTunnel": "false", "customerInnerVlan": "", "providerVlan": 8}]})
    have = _set_have_nv(have, vlanMappingEntries=stored)
    result, calls = run(base_for(parent, **_unrelated(parent)), "merged", have, parent=parent)
    assert not result.get("failed"), result.get("msg")
    assert _nv(calls, "vlanMappingEntries") == stored
    assert _nv(calls, "enableVlanMapping") == "true"
    assert not any("vlanMappingEntries" in nv for nv in diff_nvpairs(result))


@pytest.mark.parametrize("parent", PARENTS)
def test_an_unreadable_stored_list_is_rewritten_when_set_and_refused_when_carried(parent):
    have = _set_have_nv(_have_with(parent, **{ENABLE: True, ENTRIES: TRANSLATION}),
                        vlanMappingEntries="{'vlanMappingEntries': []}")
    result, calls = run(base_for(parent, **{ENTRIES: TRANSLATION}), "merged", have, parent=parent)
    assert not result.get("failed"), result.get("msg")
    assert _nv(calls, "vlanMappingEntries") == TRANSLATION_WIRE
    result, calls = run(base_for(parent, **_unrelated(parent)), "merged", have, parent=parent)
    assert result.get("failed") and "not a list the template can read" in result["msg"]
    assert split_calls(calls)["updates"] == []


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("parent", PARENTS)
def test_an_omitted_enabled_mapping_is_refused_without_a_reset(parent, state):
    have = _have_with(parent, **{ENABLE: True, ENTRIES: TRANSLATION})
    result, calls = run(base_for(parent), state, have, parent=parent)
    assert result.get("failed"), "the omission must not report a replacement that did not happen"
    assert "enable_vlan_mapping on {0}".format(parent) in result["msg"]
    assert split_calls(calls)["updates"] == [] and split_calls(calls)["deploys"] == []


@pytest.mark.parametrize("parent", PARENTS)
def test_replaced_explicit_disable_keeps_the_inert_entries(parent):
    have = _have_with(parent, **{ENABLE: True, ENTRIES: TRANSLATION})
    result, calls = run(base_for(parent, **{ENABLE: False}), "replaced", have, parent=parent)
    assert not result.get("failed"), result.get("msg")
    assert _nv(calls, "enableVlanMapping") == "false"
    # The entries are inert with the option off: kept as stored, not withdrawn and not reported.
    assert _nv(calls, "vlanMappingEntries") == TRANSLATION_WIRE
    assert not any("vlanMappingEntries" in nv for nv in diff_nvpairs(result))


@pytest.mark.parametrize("parent", PARENTS)
def test_an_explicit_empty_list_clears_while_the_option_is_off(parent):
    have = _have_with(parent, **{ENABLE: True, ENTRIES: TRANSLATION})
    result, calls = run(base_for(parent, **{ENABLE: False, ENTRIES: []}), "merged", have, parent=parent)
    assert not result.get("failed"), result.get("msg")
    assert _nv(calls, "enableVlanMapping") == "false"
    assert _nv(calls, "vlanMappingEntries") == ""


@pytest.mark.parametrize("parent", PARENTS)
@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_the_option_on_with_no_entries_is_refused(parent, state):
    result, calls = run(base_for(parent, **{ENABLE: True, ENTRIES: []}), state, parent=parent)
    assert result.get("failed") and "vlan_mapping_entries" in result["msg"]
    assert split_calls(calls)["updates"] == []
    # The controller returns "" for entries never set (measured on trunk and port-channel trunk interfaces); an empty
    # wrapper is the same empty list, and the template would render no mapping line for either.
    for stored in ("", '{"vlanMappingEntries":[]}'):
        have = _set_have_nv(_have_with(parent, **{ENABLE: False}), vlanMappingEntries=stored)
        result, calls = run(base_for(parent, **{ENABLE: True}), state, have, parent=parent)
        assert result.get("failed") and "vlan_mapping_entries" in result["msg"], stored
        assert split_calls(calls)["updates"] == []


def _writes(calls):
    """Every call that is not a read: updates, deploys and anything else."""
    return [c for c in calls if c["method"] != "GET"]


@pytest.mark.parametrize("parent", PARENTS)
@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_enabling_on_a_new_interface_without_entries_is_refused(parent, state):
    # No HAVE and no entries in the request: nothing to render, so the option must not be sent alone.
    result, calls = run(base_for(parent, **{ENABLE: True}), state, parent=parent)
    assert result.get("failed") and "vlan_mapping_entries" in result["msg"], result.get("msg")
    assert _writes(calls) == []


@pytest.mark.parametrize("parent", PARENTS)
@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_enabling_over_a_stored_interface_without_the_entries_key_is_refused(parent, state):
    have = copy.deepcopy(_have_with(parent, **{ENABLE: False}))
    have[0]["interfaces"][0]["nvPairs"].pop("vlanMappingEntries", None)
    assert "vlanMappingEntries" not in have[0]["interfaces"][0]["nvPairs"]
    assert have[0]["interfaces"][0]["nvPairs"]["enableVlanMapping"] == "false"
    result, calls = run(base_for(parent, **{ENABLE: True}), state, have, parent=parent)
    assert result.get("failed") and "vlan_mapping_entries" in result["msg"], result.get("msg")
    assert _writes(calls) == []


@pytest.mark.parametrize("parent", PARENTS)
def test_enabling_over_valid_stored_entries_carries_them(parent):
    have = _set_have_nv(_have_with(parent, **{ENABLE: False}), vlanMappingEntries=TRANSLATION_WIRE)
    result, calls = run(base_for(parent, **{ENABLE: True}), "merged", have, parent=parent)
    assert not result.get("failed"), result.get("msg")
    assert _nv(calls, "enableVlanMapping") == "true"
    assert _nv(calls, "vlanMappingEntries") == TRANSLATION_WIRE


def test_the_engine_counts_a_list_absent_from_both_as_empty_and_leaves_a_scalar_alone():
    plan = engine.gie_dependency_plan
    _writes_, conflicts = plan(TRUNK, {"enableVlanMapping": "true"}, {}, {"enableVlanMapping"}, False,
                               SUPPORTED, SUPPORTED_PATCH)
    assert [(c["nvpair"], c["reason"]) for c in conflicts] == [("vlanMappingEntries", "empty_while_on")]
    # A scalar required dependent absent from both is still left to the controller (the OSPF tag).
    _writes_, conflicts = plan("int_routed_host", {"ospf": "true"}, {}, {"ospf"}, False, SUPPORTED, SUPPORTED_PATCH)
    assert conflicts == []
    _writes_, conflicts = plan("int_routed_host", {"ospf": "true"}, {"ospf": "false", "ospfTag": ""}, {"ospf"}, False,
                               SUPPORTED, SUPPORTED_PATCH)
    assert [(c["nvpair"], c["reason"]) for c in conflicts] == [("ospfTag", "empty_while_on")]


@pytest.mark.parametrize("parent", PARENTS)
def test_an_invalid_list_is_refused_before_any_request(parent):
    bad = [{"customer_vlan": "10-20", "provider_vlan": 200}]
    result, calls = run(base_for(parent, **{ENABLE: True, ENTRIES: bad}), "merged", parent=parent)
    assert result.get("failed")
    assert "'vlan_mapping_entries' item 1 'customer_vlan' can be a range only with 'dot1q_tunnel' true" in result["msg"]
    assert split_calls(calls)["updates"] == []


@pytest.mark.parametrize("parent", PARENTS)
def test_check_mode_reports_and_sends_nothing(parent):
    have = _have_with(parent, **{ENABLE: True, ENTRIES: TRANSLATION})
    result, calls = run(base_for(parent, **{ENTRIES: TUNNEL}), "merged", have, parent=parent, check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert any(nv.get("vlanMappingEntries") == TUNNEL_WIRE for nv in diff_nvpairs(result))
    assert split_calls(calls)["updates"] == [] and split_calls(calls)["deploys"] == []


@pytest.mark.parametrize("state", role_reset.STATES)
def test_a_leaf_reset_to_the_trunk_default_with_an_enabled_mapping_is_refused(state):
    have = _have_with(TRUNK, **{ENABLE: True, ENTRIES: TRANSLATION})
    result, calls = role_reset.run(state, have, "leaf")
    assert result.get("failed"), "a reset to the default must not leave the mapping configured"
    assert "enable_vlan_mapping" in result["msg"] and "vlan_mapping_entries" in result["msg"]
    assert split_calls(calls)["updates"] == [] and split_calls(calls)["deploys"] == []


@pytest.mark.parametrize("state", role_reset.STATES)
def test_a_leaf_reset_with_the_option_off_keeps_the_inert_entries(state):
    have = _set_have_nv(_have_with(TRUNK, **{ENABLE: True, ENTRIES: TRANSLATION}), enableVlanMapping="false")
    result, calls = role_reset.run(state, have, "leaf")
    assert not result.get("failed"), result.get("msg")
    sent = role_reset.reset_policies(calls)
    assert len(sent) == 1 and sent[0]["policy"] == TRUNK
    assert "vlanMappingEntries" not in sent[0]["interfaces"][0]["nvPairs"]


@pytest.mark.parametrize("state", role_reset.STATES)
def test_a_border_reset_to_routed_relies_on_the_inline_negation(state):
    # int_trunk_host renders the mapping inline; the generator declares that NDFC negates its inline lines on a reset
    # to int_routed_host (measured for other fields on SMU 011, inherited here by source analysis).
    have = _have_with(TRUNK, **{ENABLE: True, ENTRIES: TRANSLATION})
    result, calls = role_reset.run(state, have, "border")
    assert not result.get("failed"), result.get("msg")
    sent = role_reset.reset_policies(calls)
    assert len(sent) == 1 and sent[0]["policy"] == "int_routed_host"
    assert not set(sent[0]["interfaces"][0]["nvPairs"]) & {"enableVlanMapping", "vlanMappingEntries"}


def test_the_keys_are_refused_on_a_parent_that_does_not_declare_them():
    result, calls = run(base_for(ACCESS, **{ENTRIES: TRANSLATION}), "merged", parent=None)
    assert result.get("failed") and "'vlan_mapping_entries' is not supported on this interface" in result["msg"]
    assert split_calls(calls)["updates"] == []


@pytest.mark.parametrize("parent", PARENTS)
def test_query_writes_nothing(parent):
    have = _have_with(parent, **{ENABLE: True, ENTRIES: TRANSLATION})
    result, calls = run({"mode": "trunk"}, "query", have, parent=parent)
    assert not result.get("failed"), result.get("msg")
    assert split_calls(calls)["updates"] == [] and split_calls(calls)["deploys"] == []


# ------------------------------------------------------------------ the generator
def _generator():
    from .helpers.binding_harness import _load_generator
    return _load_generator()


def test_the_generator_and_the_module_name_the_same_contracts():
    assert _generator().STRUCT_CONTRACTS == lists.struct_contracts()


@pytest.mark.parametrize("change, error", [
    ({"struct_contract": "no_such_contract"}, "known contracts are"),
    ({"struct_contract": None}, "known contracts are"),
    ({"valid_values": ["a"]}, "its contract owns the value rules"),
    ({"max_length": 4}, "its contract owns the value rules"),
    ({"min": 1}, "its contract owns the value rules"),
], ids=["unknown", "missing", "valid_values", "max_length", "min"])
def test_the_generator_refuses_a_malformed_struct_list_row(change, error):
    from .helpers.binding_harness import _as_slice_rows
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import BINDING_TABLE
    gen = _generator()
    rows = _as_slice_rows(BINDING_TABLE)
    index = next(i for i, r in enumerate(rows) if r["type"] == "struct_list")
    rows[index] = dict(rows[index], **change)
    if change.get("struct_contract", "") is None:
        del rows[index]["struct_contract"]
    with pytest.raises(ValueError, match=error):
        gen.compile_rows(rows)


def test_the_generator_refuses_struct_contract_on_a_scalar_row():
    from .helpers.binding_harness import _as_slice_rows
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import BINDING_TABLE
    gen = _generator()
    rows = _as_slice_rows(BINDING_TABLE)
    index = next(i for i, r in enumerate(rows) if r["profile_key"] == ENABLE)
    rows[index] = dict(rows[index], struct_contract="vlan_mapping_entries")
    with pytest.raises(ValueError, match="applies to struct_list bindings only"):
        gen.compile_rows(rows)
