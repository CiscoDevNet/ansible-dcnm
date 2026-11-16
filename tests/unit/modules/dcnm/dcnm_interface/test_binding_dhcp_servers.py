"""DHCP relay servers on the routed Ethernet, routed port-channel and subinterface parents (registry slice dr1).

dhcp_servers is a typed list (struct_list). The parents parse it with ast.literal_eval, create the child policy
interface_dhcp_relay_internal only from a non-empty list; removal by an empty list is not verified, so an empty list
over stored servers is refused. Expected wire strings are written by hand from the template bodies, not produced by the
contract. Module cases run the real main() through helpers/binding_harness on all three parents.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine as engine
from ansible_collections.cisco.dcnm.plugins.module_utils import interface_struct_lists as lists
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding

from .helpers.binding_harness import PC_L3
from .helpers.binding_harness import ROUTED
from .helpers.binding_harness import SUBIF
from .helpers.binding_harness import SUPPORTED
from .helpers.binding_harness import SUPPORTED_PATCH
from .helpers.binding_harness import SVI
from .helpers.binding_harness import TRUNK
from .helpers.binding_harness import base_for
from .helpers.binding_harness import build_have
from .helpers.binding_harness import cfg_for
from .helpers.binding_harness import diff_nvpairs
from .helpers.binding_harness import request_nvpairs
from .helpers.binding_harness import run
from .helpers.binding_harness import run_configs
from .helpers.binding_harness import split_calls
from .helpers import role_reset

PARENTS = (ROUTED, PC_L3, SUBIF)
KEY = "dhcp_servers"
NV = "dhcpServers"
C = lists.CONTRACT_DHCP_SERVERS

TWO = [{"srvr_ip": "192.0.2.10"}, {"srvr_ip": "2001:db8::10", "srvr_vrf": "management"}]
TWO_WIRE = ('{"dhcpServers":[{"srvrAddr":"192.0.2.10","srvrVrf":""},'
            '{"srvrAddr":"2001:db8::10","srvrVrf":"management"}]}')
ONE_WIRE = '{"dhcpServers":[{"srvrAddr":"192.0.2.10","srvrVrf":""}]}'


def _nv(calls, nvpair=NV):
    found = [nv[nvpair] for nv in request_nvpairs(calls) if nvpair in nv]
    assert len(found) == 1, found
    return found[0]


def _have(parent, servers=None):
    return build_have(parent, **({KEY: servers} if servers is not None else {}))


def _set_have_nv(have, **nvpairs):
    have = copy.deepcopy(have)
    have[0]["interfaces"][0]["nvPairs"].update(nvpairs)
    return have


def _no_writes(calls):
    return split_calls(calls)["updates"] == [] and split_calls(calls)["deploys"] == []


# ------------------------------------------------------------------ the list contract
def test_the_wire_is_the_wrapper_of_string_rows():
    assert lists.struct_to_wire(C, KEY, NV, TWO) == TWO_WIRE
    assert lists.struct_to_wire(C, KEY, NV, []) == ""
    # srvr_vrf null is the omitted VRF.
    assert lists.struct_to_wire(C, KEY, NV, [{"srvr_ip": "192.0.2.10", "srvr_vrf": None}]) == ONE_WIRE
    # The same address in two VRFs renders two relay lines.
    both = [{"srvr_ip": "192.0.2.10"}, {"srvr_ip": "192.0.2.10", "srvr_vrf": "red"}]
    assert lists.struct_validate_input(C, KEY, both) == [
        {"srvrAddr": "192.0.2.10", "srvrVrf": ""}, {"srvrAddr": "192.0.2.10", "srvrVrf": "red"}]


@pytest.mark.parametrize("value, rule", [
    ({"srvr_ip": "192.0.2.10"}, "must be a list"),
    (["192.0.2.10"], "must be a mapping"),
    ([{"srvr_ip": "192.0.2.10", "vrf": "red"}], "unsupported key"),
    ([{"srvr_vrf": "red"}], "requires 'srvr_ip'"),
    ([{"srvr_ip": ""}], "requires 'srvr_ip'"),
    ([{"srvr_ip": 3221225994}], "requires 'srvr_ip'"),
    ([{"srvr_ip": "192.0.2.300"}], "not an IPv4 or IPv6 address"),
    ([{"srvr_ip": "192.0.2.10/32"}], "not an IPv4 or IPv6 address"),
    ([{"srvr_ip": "2001:DB8::10"}], "not in canonical form"),
    ([{"srvr_ip": "2001:0db8::10"}], "not in canonical form"),
    ([{"srvr_ip": "192.0.2.10", "srvr_vrf": "red vrf"}], "'srvr_vrf' must be a VRF name"),
    ([{"srvr_ip": "192.0.2.10", "srvr_vrf": "v" * 33}], "'srvr_vrf' must be a VRF name"),
    ([{"srvr_ip": "192.0.2.10", "srvr_vrf": 5}], "'srvr_vrf' must be a VRF name"),
    ([{"srvr_ip": "192.0.2.10"}, {"srvr_ip": "192.0.2.10", "srvr_vrf": ""}], "repeats the server and VRF"),
    ([{"srvr_ip": "192.0.2.%d" % n} for n in range(1, 18)], "at most 16 servers"),
])
def test_the_contract_refuses_what_the_template_would_reject(value, rule):
    with pytest.raises(lists.StructListError, match=rule):
        lists.struct_validate_input(C, KEY, value)


def test_sixteen_servers_are_accepted():
    assert len(lists.struct_validate_input(C, KEY, [{"srvr_ip": "192.0.2.%d" % n} for n in range(1, 17)])) == 16


def test_rows_compare_in_any_order_and_a_literal_equals_its_json():
    def form(raw):
        return lists.struct_compare_form(C, raw)

    reordered = ('{"dhcpServers":[{"srvrAddr":"2001:db8::10","srvrVrf":"management"},'
                 '{"srvrAddr":"192.0.2.10","srvrVrf":""}]}')
    assert form(TWO_WIRE) == form(reordered)
    assert form(ONE_WIRE) == form("{'dhcpServers': [{'srvrAddr': '192.0.2.10', 'srvrVrf': ''}]}")
    # Case is part of the VRF value here; the module compares it exactly.
    assert form(ONE_WIRE.replace('""', '"Red"')) != form(ONE_WIRE.replace('""', '"red"'))
    assert form("") == form('{"dhcpServers":[]}') == ()


@pytest.mark.parametrize("raw", [
    '[{"srvrAddr":"192.0.2.10","srvrVrf":""}]',          # bare list: how the child iterates it is not established
    '{"dhcpServers":null}',                              # not a Python literal
    '{"dhcpServers":[],"other":1}',
    '{"dhcpServers":["192.0.2.10"]}',
    "__import__('os')",
    None,
])
def test_a_value_the_contract_cannot_read_equals_nothing(raw):
    assert lists.struct_read(C, raw) is None
    assert lists.struct_compare_form(C, raw) != lists.struct_compare_form(C, raw)


# ------------------------------------------------------------------ the engine
@pytest.mark.parametrize("parent", PARENTS)
def test_the_row_is_registered_on_the_three_parents(parent):
    b = resolve_binding(parent, KEY)
    assert (b["parent_nvpair"], b["type"], b["struct_contract"]) == (NV, "struct_list", "dhcp_servers")
    assert "reset_wire" not in b and "default_template" not in b and "inert_when" not in b
    assert b.get("dropped_on_policy_change") is (True if parent == ROUTED else None)
    for other in (TRUNK, SVI):
        assert resolve_binding(other, KEY) is None


@pytest.mark.parametrize("parent", PARENTS)
def test_the_engine_transports_reads_and_classifies(parent):
    add, err = engine.gie_contribute_nvpairs(parent, {KEY: TWO}, SUPPORTED, SUPPORTED_PATCH)
    assert err is None and add == {NV: TWO_WIRE}
    for raw in ("", '{"dhcpServers":[]}', ONE_WIRE):
        assert engine.gie_validate_binding_value(parent, KEY, raw, value_source="have") == raw
    with pytest.raises(engine.GieBindingError, match="not a list the template can read"):
        engine.gie_validate_binding_value(parent, KEY, '[{"srvrAddr":"192.0.2.10"}]', value_source="have")

    def action(have):
        return engine.gie_withdrawal_action(parent, KEY, have, SUPPORTED, SUPPORTED_PATCH)[0]

    assert action('{"dhcpServers":[]}') == engine.GIE_WITHDRAW_NONE
    assert action(ONE_WIRE) == engine.GIE_WITHDRAW_UNCLASSIFIED


@pytest.mark.parametrize("want, have, refused", [
    ("", ONE_WIRE, True),
    ('{"dhcpServers":[]}', ONE_WIRE, True),
    ("", "[]", True),                     # unreadable: never shown to be empty
    ("", "", False),
    ("", '{"dhcpServers":[]}', False),
    ("", None, False),                    # absent: nothing stored
    (ONE_WIRE, TWO_WIRE, False),           # a shorter list is not a clear
])
def test_the_clear_refusal(want, have, refused):
    assert engine.gie_struct_clear_refused(resolve_binding(ROUTED, KEY), want, have) is refused
    # VLAN mapping allows an explicit empty list.
    vm = resolve_binding(TRUNK, "vlan_mapping_entries")
    assert engine.gie_struct_clear_refused(vm, "", '{"vlanMappingEntries":[{"a":"1"}]}') is False


# ------------------------------------------------------------------ the module, all three parents
@pytest.mark.parametrize("parent", PARENTS)
def test_merged_create_sends_and_reports_the_list(parent):
    result, calls = run(base_for(parent, **{KEY: TWO}), "merged", parent=parent)
    assert not result.get("failed"), result.get("msg")
    assert _nv(calls) == TWO_WIRE
    assert any(nv.get(NV) == TWO_WIRE for nv in diff_nvpairs(result))


@pytest.mark.parametrize("parent", PARENTS)
def test_merged_repeat_and_reorder_send_nothing(parent):
    have = _have(parent, TWO)
    for value in (TWO, TWO[::-1]):
        result, calls = run(base_for(parent, **{KEY: value}), "merged", have, parent=parent)
        assert not result.get("failed"), result.get("msg")
        assert _no_writes(calls) and result["changed"] is False, value


@pytest.mark.parametrize("state", ["merged", "replaced"])
@pytest.mark.parametrize("parent", PARENTS)
def test_a_shorter_list_sends_the_whole_new_list(parent, state):
    have = _have(parent, TWO)
    result, calls = run(base_for(parent, **{KEY: TWO[:1]}), state, have, parent=parent)
    assert not result.get("failed"), result.get("msg")
    assert _nv(calls) == ONE_WIRE


@pytest.mark.parametrize("parent", PARENTS)
def test_merged_omission_carries_the_stored_text_unchanged(parent):
    stored = "{'dhcpServers': [{'srvrAddr': '192.0.2.99', 'srvrVrf': 'Red'}]}"
    have = _set_have_nv(_have(parent, TWO), dhcpServers=stored)
    result, calls = run(base_for(parent, description="changed"), "merged", have, parent=parent)
    assert not result.get("failed"), result.get("msg")
    assert _nv(calls) == stored
    assert not any(NV in nv for nv in diff_nvpairs(result))


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("parent", PARENTS)
def test_an_omitted_stored_list_is_refused_without_a_reset(parent, state):
    have = _have(parent, TWO)
    result, calls = run(base_for(parent), state, have, parent=parent)
    assert result.get("failed")
    assert "dhcp_servers on {0}".format(parent) in result["msg"]
    assert _no_writes(calls)


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("parent", PARENTS)
def test_an_omitted_empty_list_is_already_withdrawn(parent, state):
    for stored in ("", '{"dhcpServers":[]}'):
        have = _set_have_nv(_have(parent), dhcpServers=stored)
        result, _calls = run(base_for(parent, description="changed"), state, have, parent=parent)
        assert not result.get("failed"), (stored, result.get("msg"))


@pytest.mark.parametrize("check_mode", [False, True], ids=["run", "check"])
@pytest.mark.parametrize("state", ["merged", "replaced"])
@pytest.mark.parametrize("parent", PARENTS)
def test_an_empty_list_over_stored_servers_is_refused(parent, state, check_mode):
    have = _have(parent, TWO)
    result, calls = run(base_for(parent, **{KEY: []}), state, have, parent=parent, check_mode=check_mode)
    assert result.get("failed")
    assert "dhcp_servers on" in result["msg"] and "the module does not support removing every entry" in result["msg"]
    assert _no_writes(calls)


@pytest.mark.parametrize("parent", PARENTS)
def test_an_empty_list_where_nothing_is_stored_is_accepted(parent):
    result, calls = run(base_for(parent, **{KEY: []}), "merged", parent=parent)
    assert not result.get("failed"), result.get("msg")
    assert _nv(calls) == ""
    have = _set_have_nv(_have(parent), dhcpServers="")
    result, calls = run(base_for(parent, **{KEY: []}), "merged", have, parent=parent)
    assert not result.get("failed"), result.get("msg")


@pytest.mark.parametrize("parent", PARENTS)
def test_check_mode_reports_and_sends_nothing(parent):
    have = _have(parent, TWO)
    result, calls = run(base_for(parent, **{KEY: TWO[:1]}), "merged", have, parent=parent, check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert any(nv.get(NV) == ONE_WIRE for nv in diff_nvpairs(result))
    assert _no_writes(calls)


@pytest.mark.parametrize("parent", PARENTS)
def test_an_invalid_list_is_refused_before_any_request(parent):
    result, calls = run(base_for(parent, **{KEY: [{"srvr_ip": "2001:DB8::10"}]}), "merged", parent=parent)
    assert result.get("failed") and "'dhcp_servers' item 1 'srvr_ip' is not in canonical form" in result["msg"]
    assert _no_writes(calls)


@pytest.mark.parametrize("parent", [TRUNK, SVI])
def test_the_key_is_refused_where_the_parent_does_not_declare_it(parent):
    result, calls = run(base_for(parent, **{KEY: TWO}), "merged", parent=parent)
    assert result.get("failed") and "'dhcp_servers' is not supported on this interface" in result["msg"]
    assert _no_writes(calls)


@pytest.mark.parametrize("parent", PARENTS)
def test_query_writes_nothing(parent):
    have = _have(parent, TWO)
    result, calls = run({"mode": base_for(parent)["mode"]}, "query", have, parent=parent)
    assert not result.get("failed"), result.get("msg")
    assert _no_writes(calls)


@pytest.mark.parametrize("parent", (PC_L3, SUBIF))
def test_deleting_the_logical_interface_removes_it(parent):
    have = _have(parent, TWO)
    conf = dict((k, v) for k, v in cfg_for(parent, base_for(parent)).items() if k in ("name", "type", "switch"))
    result, calls = run_configs([conf], "deleted", have)
    assert not result.get("failed"), result.get("msg")
    assert any(c["method"] == "DELETE" and c["path"].endswith("/interface/markdelete") for c in calls)


@pytest.mark.parametrize("state", role_reset.STATES)
def test_a_leaf_reset_of_a_routed_port_drops_the_relay_with_the_policy(state):
    # Policy change int_routed_host -> int_trunk_host: the parent's delete() removes its interface-scoped children.
    have = _have(ROUTED, TWO)
    result, calls = role_reset.run(state, have, "leaf")
    assert not result.get("failed"), result.get("msg")
    sent = role_reset.reset_policies(calls)
    assert len(sent) == 1 and sent[0]["policy"] == TRUNK
    assert NV not in sent[0]["interfaces"][0]["nvPairs"]


@pytest.mark.parametrize("state", role_reset.STATES)
def test_a_border_reset_of_a_routed_port_with_servers_is_refused(state):
    # Same parent: removal of the relay child by the default payload is not verified, and no reset exists.
    have = _have(ROUTED, TWO)
    result, calls = role_reset.run(state, have, "border")
    assert result.get("failed") and "dhcp_servers" in result["msg"]
    assert _no_writes(calls)
