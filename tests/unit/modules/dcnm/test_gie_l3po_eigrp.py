"""EIGRP on the routed port-channel (int_l3_port_channel, `type: pc`, `mode: l3`).

The 4.3.1.0175006017 int_l3_port_channel body declares the thirteen EIGRP nvPairs of the routed, subinterface, loopback
and SVI parents with the same types, bounds, enums and defaults. It refuses an enabled boolean option or a non-empty
prefix list without the process tag (a direction alone is not checked), refuses both IPv4 passive options together and
both BFD options together, and renders one child per option inside `if eigrpProcessTag != ""`. Every add() first
deletes all children of the port-channel. The rows reuse the public keys and contracts of the other four parents,
including the three passive options that have no reset.

Real main() through gie_withdrawal_harness: only inventory, transport and sleep are mocked, and every HAVE is the payload
the module itself emits for a public profile. Values are synthetic. Nothing here is live evidence.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import patch

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table as table
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding, resolve_by_nvpair
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import gie_withdrawal_harness as h
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import test_gie_smu017_l3po_pim_bfd as po

L3PO = h.PC_L3
PO_A, PO_B = h.PC_A, po.PO_B
OTHER_PARENTS = (h.ROUTED, h.SUBIF, h.LOOPBACK, h.SVI)

# (public key, nvPair, applied public value, applied wire value, reset wire or None when the row has no reset)
ROWS = [
    ("eigrp_process_tag", "eigrpProcessTag", "PILOT-EIGRP", "PILOT-EIGRP", ""),
    ("enable_eigrp_routing", "eigrpRouting", True, "true", "false"),
    ("enable_eigrp_ipv6_routing", "eigrpIpv6Routing", True, "true", "false"),
    ("eigrp_no_ipv4_passive", "eigrpNoIpv4Passive", True, "true", None),
    ("eigrp_ipv4_passive", "eigrpIpv4Passive", True, "true", None),
    ("eigrp_no_ipv6_passive", "eigrpNoIpv6Passive", True, "true", None),
    ("eigrp_ipv4_distribute_list_prefix_list", "eigrpIpv4DistributeListPrefixList", "PILOT-PL4", "PILOT-PL4", ""),
    ("eigrp_ipv4_distribute_list_direction", "eigrpIpv4DistributeListDirection", "in", "in", "out"),
    ("eigrp_ipv6_distribute_list_prefix_list", "eigrpIpv6DistributeListPrefixList", "PILOT-PL6", "PILOT-PL6", ""),
    ("eigrp_ipv6_distribute_list_direction", "eigrpIpv6DistributeListDirection", "in", "in", "out"),
    ("enable_eigrp_shutdown", "eigrpShutdown", True, "true", "false"),
    ("enable_eigrp_bfd", "eigrpBfd", True, "true", "false"),
    ("disable_eigrp_bfd", "eigrpBfdDisable", True, "true", "false"),
]
IDS = [r[0] for r in ROWS]
NVPAIRS = [r[1] for r in ROWS]
NV_OF = {r[0]: r[1] for r in ROWS}
PASSIVE = [r for r in ROWS if r[4] is None]
RESETTABLE = [r for r in ROWS if r[4] is not None]
RESET_WIRE = {r[1]: r[4] for r in RESETTABLE}

BASE = dict(h.BASE_PC_L3)
TAG = {"eigrp_process_tag": "PILOT-EIGRP"}
ON = {**BASE, **TAG, "enable_eigrp_routing": True}
# Every resettable option applied; enable_eigrp_bfd stands for the BFD pair.
SET = {**ON, "enable_eigrp_ipv6_routing": True, "enable_eigrp_shutdown": True, "enable_eigrp_bfd": True,
       "eigrp_ipv4_distribute_list_prefix_list": "PILOT-PL4", "eigrp_ipv4_distribute_list_direction": "in",
       "eigrp_ipv6_distribute_list_prefix_list": "PILOT-PL6", "eigrp_ipv6_distribute_list_direction": "in"}
SET_WIRE = {"eigrpProcessTag": "PILOT-EIGRP", "eigrpRouting": "true", "eigrpIpv6Routing": "true",
            "eigrpShutdown": "true", "eigrpBfd": "true", "eigrpIpv4DistributeListPrefixList": "PILOT-PL4",
            "eigrpIpv4DistributeListDirection": "in", "eigrpIpv6DistributeListPrefixList": "PILOT-PL6",
            "eigrpIpv6DistributeListDirection": "in"}
# The other members of each mutually exclusive pair, for the creates that cover all thirteen nvPairs.
VARIANTS = {
    "ipv4_passive_and_bfd": ({"eigrp_ipv4_passive": True, "eigrp_no_ipv6_passive": True},
                             {"eigrpIpv4Passive": "true", "eigrpNoIpv6Passive": "true"}),
    "no_ipv4_passive_and_bfd_disable": ({"eigrp_no_ipv4_passive": True, "enable_eigrp_bfd": False,
                                         "disable_eigrp_bfd": True},
                                        {"eigrpNoIpv4Passive": "true", "eigrpBfd": "false", "eigrpBfdDisable": "true"}),
}

# Existing L3 port-channel families that an EIGRP change must not disturb.
OSPF_PIM = {"enable_ospf": True, "ospf_tag": "PILOT-OSPF", "ospf_area_id": "0.0.0.0", "ospf_cost": 42,
            "enable_pim_sparse": True, "pim_dr_priority": 200, "enable_pim_bfd_instance": True}
KEPT_NV = po.NATIVE + ("ospf", "ospfTag", "OSPF_AREA_ID", "ospfCost", "ENABLE_PIM_SPARSE", "PIM_DR_PRIORITY",
                       "pimBfdInstance")


def _eigrp(nv):
    return {k: nv.get(k) for k in NVPAIRS if k in nv}


def _kept(nv):
    return {k: nv.get(k) for k in KEPT_NV}


def _routed_nv(eigrp_profile):
    """The nvPairs the routed Ethernet parent emits for the same EIGRP keys."""
    result, calls = h.run_configs([h.cfg(h.IF_A, {**h.BASE_ROUTED, **eigrp_profile})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    assert [p["policy"] for p in found] == [h.ROUTED], found
    return found[0]["interfaces"][0]["nvPairs"]


def _eigrp_keys(profile):
    return {k: v for k, v in profile.items() if k in NV_OF}


# ------------------------------------------------------------------ the rows are the other parents' contracts
@pytest.mark.parametrize("key,nvpair,applied,wire,reset", ROWS, ids=IDS)
def test_the_row_reuses_the_contract_of_the_other_eigrp_parents(key, nvpair, applied, wire, reset):
    b = resolve_binding(L3PO, key)
    assert b is not None, "%s is not registered on int_l3_port_channel" % key
    assert (b["parent_nvpair"], b["mechanism"]) == (nvpair, "passthrough")
    assert (b["applicable_interface_type"], b["applicable_mode"]) == ("pc", "l3")
    assert resolve_by_nvpair(L3PO, nvpair) is b
    assert b.get("reset_wire") == reset, "a passive option has no reset on any parent"
    assert "inert_when" not in b, "the template enforces the tag; the module transports"
    for parent in OTHER_PARENTS:
        other = resolve_binding(parent, key)
        for field in ("parent_nvpair", "type", "reset_wire", "default_template", "max_length", "valid_values",
                      "string_compare", "min_ndfc_version", "no_log", "inert_when"):
            assert b.get(field) == other.get(field), (parent, key, field)


def test_the_feature_delta_is_the_thirteen_l3_port_channel_rows_only():
    eigrp = [r for r in table.BINDING_TABLE if r["parent_nvpair"] in NVPAIRS]
    on_l3po = sorted(r["parent_nvpair"] for r in eigrp if r["parent_template"] == L3PO)
    assert on_l3po == sorted(NVPAIRS)
    others = [r for r in eigrp if r["parent_template"] != L3PO]
    assert len(others) == 52 and sorted({r["parent_template"] for r in others}) == sorted(OTHER_PARENTS)
    assert "dropped_on_policy_change" not in resolve_binding(L3PO, "eigrp_process_tag")


# ------------------------------------------------------------------ merged create: wire forms and parity with routed
@pytest.mark.parametrize("variant", sorted(VARIANTS))
def test_merged_create_sends_every_field_with_the_native_profile_and_deploys_it(variant):
    extra, extra_wire = VARIANTS[variant]
    profile = {**SET, **extra}
    result, calls = h.run_configs([po._po(profile)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = po._only(calls)
    expected = {**SET_WIRE, **extra_wire}
    assert _eigrp(nv) == expected, "only the given keys are sent on create"
    assert all(isinstance(nv[k], str) for k in expected)
    assert (nv["MEMBER_INTERFACES"], nv["IP"], nv["PREFIX"], nv["PC_MODE"]) == (h.PC_MEMBER, "192.0.2.33", "30", "active")
    assert po._paths(calls) == ["POST globalInterface", "POST globalInterface/deploy"], po._paths(calls)
    assert _eigrp(nv) == _eigrp(_routed_nv(_eigrp_keys(profile))), "same keys, same nvPairs as routed Ethernet"


@pytest.mark.parametrize("key,nvpair,applied,wire,reset", ROWS, ids=IDS)
def test_each_field_alone_reaches_its_nvpair(key, nvpair, applied, wire, reset):
    profile = {**TAG, key: applied}
    result, calls = h.run_configs([po._po({**BASE, **profile})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = po._only(calls)
    assert nv[nvpair] == wire
    assert set(_eigrp(nv)) == {"eigrpProcessTag", nvpair}


@pytest.mark.parametrize("vrf", ["default", "PILOT-VRF"])
def test_the_fields_are_carried_in_any_vrf(vrf):
    """The body's EIGRP block is not VRF-gated. Whether NX-OS accepts it in a given VRF is a device question."""
    result, calls = h.run_configs([po._po({**SET, "int_vrf": vrf})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = po._only(calls)
    assert nv["INTF_VRF"] == vrf and _eigrp(nv) == SET_WIRE


# ------------------------------------------------------------------ invalid input and template-enforced rules
@pytest.mark.parametrize("change,needle", [
    ({"eigrp_process_tag": "T" * 21}, "eigrp_process_tag"),
    ({"eigrp_ipv4_distribute_list_direction": "both"}, "eigrp_ipv4_distribute_list_direction"),
    ({"eigrp_ipv6_distribute_list_direction": "IN"}, "eigrp_ipv6_distribute_list_direction"),
    ({"eigrp_ipv4_distribute_list_prefix_list": "P" * 64}, "eigrp_ipv4_distribute_list_prefix_list"),
    ({"eigrp_ipv6_distribute_list_prefix_list": "P" * 64}, "eigrp_ipv6_distribute_list_prefix_list"),
    ({"enable_eigrp_routing": "maybe"}, "enable_eigrp_routing"),
    ({"eigrp_no_ipv6_passive": "maybe"}, "eigrp_no_ipv6_passive"),
    ({"disable_eigrp_bfd": "maybe"}, "disable_eigrp_bfd"),
], ids=["tag_21", "v4_direction_both", "v6_direction_upper", "v4_prefix_list_64", "v6_prefix_list_64",
        "routing_not_bool", "no_v6_passive_not_bool", "bfd_disable_not_bool"])
def test_invalid_values_are_refused_before_any_write(change, needle):
    result, calls = h.run_configs([po._po({**SET, **change})], "merged", [])
    assert result.get("failed") and needle in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


def test_the_longest_tag_and_prefix_lists_are_accepted():
    profile = {**ON, "eigrp_process_tag": "T" * 20, "eigrp_ipv4_distribute_list_prefix_list": "P" * 63}
    result, calls = h.run_configs([po._po(profile)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = po._only(calls)
    assert (nv["eigrpProcessTag"], nv["eigrpIpv4DistributeListPrefixList"]) == ("T" * 20, "P" * 63)


@pytest.mark.parametrize("eigrp", [
    {"enable_eigrp_routing": True},
    {"eigrp_ipv4_passive": True, "eigrp_no_ipv4_passive": True, **TAG},
    {"enable_eigrp_bfd": True, "disable_eigrp_bfd": True, **TAG},
    {"eigrp_ipv6_distribute_list_direction": "in", **TAG},
], ids=["option_without_tag", "both_ipv4_passive", "both_bfd", "direction_without_prefix_list"])
def test_combinations_the_template_refuses_or_ignores_are_transported_as_on_routed_ethernet(eigrp):
    """The body refuses an enabled option without the tag and each mutually exclusive pair; a direction without its
    prefix list is not checked and renders nothing. As on the other four parents, the module does not duplicate these
    rules: it sends the request unchanged and the controller decides. The controller responses are not observed here."""
    result, calls = h.run_configs([po._po({**BASE, **eigrp})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = po._only(calls)
    assert _eigrp(nv) == _eigrp(_routed_nv(eigrp))
    assert _eigrp(nv) == {NV_OF[k]: (str(v).lower() if isinstance(v, bool) else v) for k, v in eigrp.items()}


def test_switching_bfd_under_merged_needs_the_other_option_cleared_in_the_same_request():
    """Merged keeps an omitted stored value, so a request for disable alone arrives beside the stored enable, the pair
    the template refuses. Clearing the stored option explicitly sends the supported combination."""
    have = po._have(SET)
    result, calls = h.run_configs([po._po({**ON, "disable_eigrp_bfd": True})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = po._only(calls)
    assert (nv["eigrpBfd"], nv["eigrpBfdDisable"]) == ("true", "true")
    result, calls = h.run_configs([po._po({**ON, "disable_eigrp_bfd": True, "enable_eigrp_bfd": False})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = po._only(calls)
    assert (nv["eigrpBfd"], nv["eigrpBfdDisable"]) == ("false", "true")


# ------------------------------------------------------------------ merged update, omission, repeat
@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_explicit_update_sends_the_new_values_and_keeps_the_others(state):
    have = po._have({**SET, **OSPF_PIM})
    changes = {"eigrp_ipv4_distribute_list_direction": "out", "enable_eigrp_shutdown": False,
               "eigrp_ipv6_distribute_list_prefix_list": "PILOT-PL6B"}
    result, calls = h.run_configs([po._po({**SET, **OSPF_PIM, **changes})], state, have)
    assert not result.get("failed"), result.get("msg")
    nv = po._only(calls)
    assert _eigrp(nv) == {**SET_WIRE, "eigrpIpv4DistributeListDirection": "out", "eigrpShutdown": "false",
                          "eigrpIpv6DistributeListPrefixList": "PILOT-PL6B"}
    assert _kept(nv) == _kept(have[0]["interfaces"][0]["nvPairs"])
    assert po._paths(calls) == ["POST interface/modify", "POST globalInterface/deploy"], po._paths(calls)


def test_merged_omission_carries_the_stored_values_into_another_change():
    have = po._have({**SET, **OSPF_PIM})
    result, calls = h.run_configs([po._po({**BASE, "description": "changed"})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = po._only(calls)
    assert _eigrp(nv) == SET_WIRE and nv["DESC"] == "changed"
    assert (nv["ospfCost"], nv["PIM_DR_PRIORITY"], nv["pimBfdInstance"]) == ("42", "200", "true")


def test_explicit_clear_differs_from_omission_under_merged():
    have = po._have(SET)
    explicit = {**BASE, "enable_eigrp_ipv6_routing": False, "eigrp_ipv4_distribute_list_prefix_list": "",
                "eigrp_ipv6_distribute_list_direction": "out"}
    result, calls = h.run_configs([po._po(explicit)], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = po._only(calls)
    assert (nv["eigrpIpv6Routing"], nv["eigrpIpv4DistributeListPrefixList"], nv["eigrpIpv6DistributeListDirection"]) == (
        "false", "", "out")
    assert (nv["eigrpIpv4DistributeListDirection"], nv["eigrpIpv6DistributeListPrefixList"]) == ("in", "PILOT-PL6")
    result, calls = h.run_configs([po._po(BASE)], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [], "omission under merged keeps the stored values"


@pytest.mark.parametrize("state", ["merged", "replaced"])
@pytest.mark.parametrize("variant", sorted(VARIANTS))
def test_repeat_of_the_stored_values_writes_nothing(state, variant):
    profile = {**SET, **VARIANTS[variant][0]}
    result, calls = h.run_configs([po._po(profile)], state, po._have(profile))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and not result.get("changed")


# ------------------------------------------------------------------ replaced: reset of the resettable rows
def test_replaced_omission_resets_every_option_and_keeps_the_tag_routing_and_other_families():
    have = po._have({**SET, **OSPF_PIM})
    result, calls = h.run_configs([po._po({**ON, **OSPF_PIM})], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = po._only(calls)
    assert _eigrp(nv) == {**{k: v for k, v in RESET_WIRE.items() if k in SET_WIRE},
                          "eigrpProcessTag": "PILOT-EIGRP", "eigrpRouting": "true"}
    assert _kept(nv) == _kept(have[0]["interfaces"][0]["nvPairs"])
    assert po._paths(calls) == ["POST interface/modify", "POST globalInterface/deploy"], "a reset is not a removal"


@pytest.mark.parametrize("key,nvpair,applied,wire,reset", [r for r in RESETTABLE if r[0] not in TAG],
                         ids=[r[0] for r in RESETTABLE if r[0] not in TAG])
def test_replaced_resets_one_omitted_field_and_keeps_the_others(key, nvpair, applied, wire, reset):
    base = {**SET, "enable_eigrp_bfd": False, key: applied}
    if key == "eigrp_ipv4_distribute_list_direction":
        base["eigrp_ipv4_distribute_list_prefix_list"] = "PILOT-PL4"
    have = po._have(base)
    stored = have[0]["interfaces"][0]["nvPairs"]
    result, calls = h.run_configs([po._po({k: v for k, v in base.items() if k != key})], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = po._only(calls)
    assert nv[nvpair] == reset
    assert {k: v for k, v in _eigrp(nv).items() if k != nvpair} == {k: v for k, v in _eigrp(stored).items() if k != nvpair}


def test_replaced_without_any_eigrp_key_withdraws_the_tag_with_the_options():
    """The tag gate: the tag and every option are reset in one request, as the template requires."""
    have = po._have({**SET, **OSPF_PIM})
    result, calls = h.run_configs([po._po({**BASE, **OSPF_PIM})], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = po._only(calls)
    assert _eigrp(nv) == {k: v for k, v in RESET_WIRE.items() if k in SET_WIRE}
    assert _kept(nv) == _kept(have[0]["interfaces"][0]["nvPairs"])


@pytest.mark.parametrize("state", ["replaced", "merged"])
def test_repeat_after_the_reset_writes_nothing(state):
    result, calls = h.run_configs([po._po(ON)], "replaced", po._have(SET))
    assert not result.get("failed"), result.get("msg")
    reset = po._as_have(po._only(calls))
    result, calls = h.run_configs([po._po(ON)], state, reset)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_replaced_without_eigrp_on_a_port_channel_that_never_had_it_writes_nothing():
    result, calls = h.run_configs([po._po(BASE)], "replaced", po._have(BASE))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


# ------------------------------------------------------------------ the passive options: no reset on any parent
@pytest.mark.parametrize("key,nvpair,applied,wire,reset", PASSIVE, ids=[r[0] for r in PASSIVE])
def test_replaced_omission_of_a_stored_passive_option_is_refused_before_any_write(key, nvpair, applied, wire, reset):
    """No passive option has a registered reset on any parent, so replaced refuses the withdrawal instead of sending
    one. On the other parents, clearing eigrp_ipv4_passive or eigrp_no_ipv6_passive was measured to render the inverse
    line without converging; eigrp_no_ipv4_passive is operator-reported only. None was tested on this parent."""
    have = po._have({**ON, key: True})
    result, calls = h.run_configs([po._po(ON)], "replaced", have)
    assert result.get("failed"), "a withdrawal with no reset reported success"
    msg = str(result.get("msg", ""))
    assert key in msg and L3PO in msg and "must withdraw" in msg, msg
    assert h.writes(calls) == []


@pytest.mark.parametrize("key,nvpair,applied,wire,reset", PASSIVE, ids=[r[0] for r in PASSIVE])
def test_a_passive_option_restated_under_replaced_lets_the_other_fields_reset(key, nvpair, applied, wire, reset):
    have = po._have({**SET, key: True})
    result, calls = h.run_configs([po._po({**ON, key: True})], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = po._only(calls)
    assert nv[nvpair] == "true" and (nv["eigrpShutdown"], nv["eigrpIpv6Routing"]) == ("false", "false")


@pytest.mark.parametrize("state", ["merged", "replaced"])
@pytest.mark.parametrize("key,nvpair,applied,wire,reset", PASSIVE, ids=[r[0] for r in PASSIVE])
def test_an_explicit_passive_false_is_transported(state, key, nvpair, applied, wire, reset):
    """The module sends the requested "false". The device result is not established here: on the other parents two
    passive fields were measured not to converge after this clear and the third is operator-reported."""
    have = po._have({**ON, key: True})
    result, calls = h.run_configs([po._po({**ON, key: False})], state, have)
    assert not result.get("failed"), result.get("msg")
    assert po._only(calls)[nvpair] == "false"


def test_a_passive_option_stored_false_does_not_block_replaced():
    have = po._have({**SET, "eigrp_ipv4_passive": False})
    result, calls = h.run_configs([po._po(ON)], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    assert po._only(calls)["eigrpIpv4Passive"] == "false"


# ------------------------------------------------------------------ overridden, deleted, query, check mode
def _aggregate(profile_a, profile_b):
    return (po._have({**profile_a, "members": [po.MEM_A]}) + po._have({**profile_b, "members": [po.MEM_B]}, PO_B)
            + po._member_have(po.MEM_A, PO_A) + po._member_have(po.MEM_B, PO_B))


def test_overridden_retained_port_channel_resets_the_options_and_keeps_the_control():
    configs = [po._po({**ON, "members": [po.MEM_A]}), po._po({**SET, "members": [po.MEM_B]}, PO_B)]
    result, calls = po._run(configs, "overridden", _aggregate(SET, SET))
    assert not result.get("failed"), result.get("msg")
    assert po._identities(calls) == [(po.MODIFY, [[h.SERIAL, PO_A, L3PO]]), (po.DEPLOY, [[h.SERIAL, PO_A]])]
    nv = po._only(calls)
    assert _eigrp(nv) == {**{k: v for k, v in RESET_WIRE.items() if k in SET_WIRE},
                          "eigrpProcessTag": "PILOT-EIGRP", "eigrpRouting": "true"}
    assert nv["MEMBER_INTERFACES"] == po.MEM_A


def test_overridden_retained_port_channel_with_a_stored_passive_option_is_refused():
    configs = [po._po({**ON, "members": [po.MEM_A]}), po._po({**SET, "members": [po.MEM_B]}, PO_B)]
    result, calls = po._run(configs, "overridden", _aggregate({**ON, "eigrp_no_ipv6_passive": True}, SET))
    assert result.get("failed"), "a withdrawal with no reset reported success"
    assert "eigrp_no_ipv6_passive" in str(result.get("msg", ""))
    assert po._identities(calls) == []


def test_overridden_port_channel_left_out_is_deleted_with_its_passive_option():
    """Removing the interface is not a field withdrawal, so a stored passive option does not block it."""
    have = _aggregate({**SET, "eigrp_ipv4_passive": True}, SET)
    result, calls = po._run([po._po({**SET, "members": [po.MEM_B]}, PO_B)], "overridden", have)
    assert not result.get("failed"), result.get("msg")
    assert po._identities(calls) == [
        (po.MARK, [[h.SERIAL, PO_A]]), (po.DEPLOY, [[h.SERIAL, PO_A]]),
        (po.MODIFY, [[h.SERIAL, po.MEM_A, h.ROUTED]]), (po.DEPLOY, [[h.SERIAL, po.MEM_A]]),
    ]


def test_deleted_removes_the_port_channel_and_a_repeat_writes_nothing():
    target = [{"name": PO_A, "type": "pc", "switch": [h.SWITCH_IP]}]
    have = po._have({**SET, "eigrp_ipv4_passive": True, "members": [po.MEM_A]}) + po._member_have(po.MEM_A, PO_A)
    result, calls = po._run(target, "deleted", have)
    assert not result.get("failed"), result.get("msg")
    assert po._identities(calls) == [(po.MARK, [[h.SERIAL, PO_A]]), (po.DEPLOY, [[h.SERIAL, PO_A]])]
    result, calls = po._run(target, "deleted", [])
    assert not result.get("failed"), result.get("msg")
    assert po._identities(calls) == []


def test_query_returns_the_controller_values_unchanged():
    target = po._have({**SET, "eigrp_no_ipv4_passive": True})
    writes = []
    with patch.object(h, "_transport", po._query_transport(target + po._have(BASE, PO_B), writes)):
        result, calls = h.run_configs([{"name": PO_A, "switch": [h.SWITCH_IP]}], "query", [])
    assert not result.get("failed"), result.get("msg")
    assert writes == [] and h.writes(calls) == [] and not result.get("changed")
    assert result["response"] == target
    assert _eigrp(result["response"][0]["interfaces"][0]["nvPairs"]) == {**SET_WIRE, "eigrpNoIpv4Passive": "true"}


@pytest.mark.parametrize("state,profile", [("merged", {**ON, "enable_eigrp_shutdown": False}), ("replaced", ON)],
                         ids=["merged", "replaced"])
def test_check_mode_reports_the_change_and_writes_nothing(state, profile):
    result, calls = h.run_configs([po._po(profile)], state, po._have(SET), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and result.get("changed") is True


def test_check_mode_also_refuses_a_passive_withdrawal():
    result, calls = h.run_configs([po._po(ON)], "replaced", po._have({**ON, "eigrp_ipv4_passive": True}),
                                  check_mode=True)
    assert result.get("failed") and h.writes(calls) == []


# ------------------------------------------------------------------ version gate and unaffected controls
@pytest.mark.parametrize("patch_version", [None, "4.3.1.0175006011"], ids=["no_patch_version", "smu011"])
@pytest.mark.parametrize("key,nvpair,applied,wire,reset", ROWS, ids=IDS)
def test_each_field_needs_an_approved_patch_version(patch_version, key, nvpair, applied, wire, reset):
    result, calls = h.run_configs([po._po({**BASE, key: applied})], "merged", [], patch_version=patch_version)
    assert result.get("failed") and key in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


def test_numeric_441_is_admitted():
    result, calls = h.run_configs([po._po(SET)], "merged", [], patch_version="4.4.1")
    assert not result.get("failed"), result.get("msg")
    assert _eigrp(po._only(calls)) == SET_WIRE


@pytest.mark.parametrize("patch_version", [None, "4.3.1.0175006011"], ids=["no_patch_version", "smu011"])
def test_omission_under_a_closed_gate_resets_nothing(patch_version):
    result, calls = h.run_configs([po._po(BASE)], "replaced", po._have(SET), patch_version=patch_version)
    assert not result.get("failed"), result.get("msg")
    for _policy, nv in po._emitted(calls).values():
        assert _eigrp(nv) in ({}, SET_WIRE), nv


def test_a_plain_l3_port_channel_and_its_ospf_and_pim_payload_carry_no_eigrp_nvpair():
    for profile in (BASE, {**BASE, **OSPF_PIM}):
        result, calls = h.run_configs([po._po(profile)], "merged", [])
        assert not result.get("failed"), result.get("msg")
        assert _eigrp(po._only(calls)) == {}


@pytest.mark.parametrize("parent", [h.PC_TRUNK, h.PC_ACCESS, h.PC_DOT1Q])
@pytest.mark.parametrize("key", ["eigrp_process_tag", "enable_eigrp_routing", "eigrp_ipv4_passive"])
def test_the_keys_stay_refused_on_the_layer2_port_channels(parent, key):
    value = dict((r[0], r[2]) for r in ROWS)[key]
    result, calls = h.run_configs([h.cfg_for(parent, {**h.base_for(parent), key: value})], "merged", [])
    assert result.get("failed") and key in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


def test_the_routed_ethernet_payload_is_unchanged():
    assert _eigrp(_routed_nv(_eigrp_keys(SET))) == SET_WIRE
