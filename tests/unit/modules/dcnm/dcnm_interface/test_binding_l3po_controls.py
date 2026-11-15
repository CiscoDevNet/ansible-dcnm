"""BFD echo, ARP timeout and inbound IPv4 ACL on the routed port-channel (registry lot rp1).

The int_l3_port_channel body of the supported patch release declares bfdEcho, arpTimeout and ipv4AclIn with the types, bounds and
defaults of int_routed_host and renders the same three children. The rows reuse the int_routed_host public keys and
contracts. Replaced and overridden withdrawal of each row runs in test_binding_withdrawal.py through the shared
fixture matrix.

Real main() through helpers/binding_harness: only inventory, transport and sleep are mocked, and every HAVE is the
payload the module itself emits for a public profile. Values are synthetic. Nothing here is live evidence.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_by_nvpair

from .helpers import binding_harness as h
from .test_binding_smu017 import L3PO, MARK, DEPLOY, MEM_A, MODIFY, PO_A
from .test_binding_smu017 import _identities, _l3po_pim_bfd_as_have, _l3po_pim_bfd_have, _l3po_pim_bfd_query_transport
from .test_binding_smu017 import _l3po_pim_bfd_run, _member_have, _only, _paths, _po
from unittest.mock import patch

# (public key, nvPair, applied public value, applied wire value, reset wire)
ROWS = [
    ("disable_bfd_echo", "bfdEcho", True, "true", "false"),
    ("arp_timeout", "arpTimeout", 900, "900", ""),
    ("ipv4_acl_in", "ipv4AclIn", "PILOT-ACL", "PILOT-ACL", ""),
]
IDS = [r[0] for r in ROWS]
NVPAIRS = [r[1] for r in ROWS]
BASE = dict(h.BASE_PC_L3)
SET = {**BASE, **{r[0]: r[2] for r in ROWS}}
SET_WIRE = {r[1]: r[3] for r in ROWS}
RESET_WIRE = {r[1]: r[4] for r in ROWS}
OTHERS = {"enable_ospf": True, "ospf_tag": "PILOT-OSPF", "ospf_area_id": "0.0.0.0", "enable_pim_sparse": True,
          "eigrp_process_tag": "PILOT-EIGRP", "enable_eigrp_routing": True}
KEPT_NV = ("MEMBER_INTERFACES", "IP", "PREFIX", "INTF_VRF", "MTU", "ospf", "ospfTag", "ENABLE_PIM_SPARSE",
           "eigrpProcessTag", "eigrpRouting")


def _sel(nv, keys=NVPAIRS):
    return {k: nv.get(k) for k in keys if k in nv}


def _routed_nv(profile):
    """The nvPairs the routed Ethernet parent emits for the same keys."""
    result, calls = h.run_configs([h.cfg(h.IF_A, {**h.BASE_ROUTED, **profile})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    assert [p["policy"] for p in found] == [h.ROUTED], found
    return found[0]["interfaces"][0]["nvPairs"]


# ------------------------------------------------------------------ the rows are the routed Ethernet contracts
@pytest.mark.parametrize("key,nvpair,applied,wire,reset", ROWS, ids=IDS)
def test_the_row_reuses_the_routed_ethernet_contract(key, nvpair, applied, wire, reset):
    b = resolve_binding(L3PO, key)
    assert b is not None, "%s is not registered on int_l3_port_channel" % key
    assert (b["parent_nvpair"], b["mechanism"]) == (nvpair, "passthrough")
    assert (b["applicable_interface_type"], b["applicable_mode"]) == ("pc", "l3")
    assert resolve_by_nvpair(L3PO, nvpair) is b
    assert b["reset_wire"] == reset and "inert_when" not in b
    routed = resolve_binding(h.ROUTED, key)
    for field in ("parent_nvpair", "type", "reset_wire", "default_template", "min_value", "max_value", "min_length",
                  "max_length", "valid_values", "string_compare", "min_ndfc_version", "no_log"):
        assert b.get(field) == routed.get(field), (key, field)


# ------------------------------------------------------------------ merged create and update
def test_merged_create_sends_the_three_fields_with_the_native_profile_and_deploys_it():
    result, calls = h.run_configs([_po(SET)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert _sel(nv) == SET_WIRE and all(isinstance(nv[k], str) for k in SET_WIRE)
    assert (nv["MEMBER_INTERFACES"], nv["IP"], nv["PREFIX"]) == (h.PC_MEMBER, "192.0.2.33", "30")
    assert _paths(calls) == ["POST globalInterface", "POST globalInterface/deploy"], _paths(calls)
    assert _sel(nv) == _sel(_routed_nv({r[0]: r[2] for r in ROWS})), "same keys, same nvPairs as routed Ethernet"


@pytest.mark.parametrize("key,nvpair,applied,wire,reset", ROWS, ids=IDS)
def test_each_field_alone_reaches_its_nvpair(key, nvpair, applied, wire, reset):
    result, calls = h.run_configs([_po({**BASE, key: applied})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert _sel(nv) == {nvpair: wire}


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_explicit_update_sends_the_new_values_and_keeps_the_other_families(state):
    have = _l3po_pim_bfd_have({**SET, **OTHERS})
    changes = {"disable_bfd_echo": False, "arp_timeout": 28800, "ipv4_acl_in": "PILOT-ACL-B"}
    result, calls = h.run_configs([_po({**SET, **OTHERS, **changes})], state, have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert _sel(nv) == {"bfdEcho": "false", "arpTimeout": "28800", "ipv4AclIn": "PILOT-ACL-B"}
    assert _sel(nv, KEPT_NV) == _sel(have[0]["interfaces"][0]["nvPairs"], KEPT_NV)
    assert _paths(calls) == ["POST interface/modify", "POST globalInterface/deploy"], _paths(calls)


def test_the_acl_name_is_compared_with_its_case():
    """ipv4_acl_in compares byte for byte, as on int_routed_host: a case-only change is sent."""
    have = _l3po_pim_bfd_have({**BASE, "ipv4_acl_in": "pilot-acl"})
    result, calls = h.run_configs([_po({**BASE, "ipv4_acl_in": "PILOT-Acl"})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)["ipv4AclIn"] == "PILOT-Acl"


def test_merged_explicit_acl_clear_differs_from_omission():
    have = _l3po_pim_bfd_have(SET)
    result, calls = h.run_configs([_po({**BASE, "ipv4_acl_in": ""})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert _sel(nv) == {**SET_WIRE, "ipv4AclIn": ""}
    result, calls = h.run_configs([_po(BASE)], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [], "omission under merged keeps the stored values"


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_repeat_of_the_stored_values_writes_nothing(state):
    result, calls = h.run_configs([_po(SET)], state, _l3po_pim_bfd_have(SET))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and not result.get("changed")


# ------------------------------------------------------------------ invalid input
@pytest.mark.parametrize("change,needle", [
    ({"arp_timeout": 59}, "arp_timeout"),
    ({"arp_timeout": 28801}, "arp_timeout"),
    ({"arp_timeout": ""}, "arp_timeout"),
    ({"ipv4_acl_in": "A" * 65}, "ipv4_acl_in"),
    ({"disable_bfd_echo": "maybe"}, "disable_bfd_echo"),
], ids=["arp_59", "arp_28801", "arp_empty", "acl_65", "bfd_not_bool"])
def test_invalid_values_are_refused_before_any_write(change, needle):
    result, calls = h.run_configs([_po({**BASE, **change})], "merged", [])
    assert result.get("failed") and needle in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


def test_the_bounds_are_accepted():
    result, calls = h.run_configs([_po({**BASE, "arp_timeout": 60, "ipv4_acl_in": "A" * 64})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    assert _sel(_only(calls)) == {"arpTimeout": "60", "ipv4AclIn": "A" * 64}


# ------------------------------------------------------------------ replaced, overridden, deleted, query, check mode
def test_replaced_omission_resets_the_three_and_keeps_the_other_families():
    have = _l3po_pim_bfd_have({**SET, **OTHERS})
    result, calls = h.run_configs([_po({**BASE, **OTHERS})], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert _sel(nv) == RESET_WIRE
    assert _sel(nv, KEPT_NV) == _sel(have[0]["interfaces"][0]["nvPairs"], KEPT_NV)
    reset = _l3po_pim_bfd_as_have(nv)
    for state in ("replaced", "merged"):
        result, calls = h.run_configs([_po({**BASE, **OTHERS})], state, reset)
        assert not result.get("failed"), result.get("msg")
        assert h.writes(calls) == [], "the state the module produced converges"


def test_deleted_removes_the_port_channel_and_a_repeat_writes_nothing():
    target = [{"name": PO_A, "type": "pc", "switch": [h.SWITCH_IP]}]
    have = _l3po_pim_bfd_have({**SET, "members": [MEM_A]}) + _member_have(MEM_A, PO_A)
    result, calls = _l3po_pim_bfd_run(target, "deleted", have)
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [(MARK, [[h.SERIAL, PO_A]]), (DEPLOY, [[h.SERIAL, PO_A]])]
    result, calls = _l3po_pim_bfd_run(target, "deleted", [])
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == []


def test_overridden_retained_port_channel_resets_the_three():
    have = _l3po_pim_bfd_have({**SET, "members": [MEM_A]}) + _member_have(MEM_A, PO_A)
    result, calls = _l3po_pim_bfd_run([_po({**BASE, "members": [MEM_A]})], "overridden", have)
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [(MODIFY, [[h.SERIAL, PO_A, L3PO]]), (DEPLOY, [[h.SERIAL, PO_A]])]
    assert _sel(_only(calls)) == RESET_WIRE


def test_query_returns_the_controller_values_unchanged():
    target = _l3po_pim_bfd_have(SET)
    writes = []
    with patch.object(h, "_transport", _l3po_pim_bfd_query_transport(target, writes)):
        result, calls = h.run_configs([{"name": PO_A, "switch": [h.SWITCH_IP]}], "query", [])
    assert not result.get("failed"), result.get("msg")
    assert writes == [] and h.writes(calls) == [] and not result.get("changed")
    assert result["response"] == target
    assert _sel(result["response"][0]["interfaces"][0]["nvPairs"]) == SET_WIRE


@pytest.mark.parametrize("state,profile", [("merged", {**SET, "arp_timeout": 1800}), ("replaced", BASE)],
                         ids=["merged", "replaced"])
def test_check_mode_reports_the_change_and_writes_nothing(state, profile):
    result, calls = h.run_configs([_po(profile)], state, _l3po_pim_bfd_have(SET), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and result.get("changed") is True


# ------------------------------------------------------------------ version gate and scope
@pytest.mark.parametrize("patch_version", [None, h.UNSUPPORTED_PATCH], ids=["no_patch_version", "unsupported_patch"])
@pytest.mark.parametrize("key,nvpair,applied,wire,reset", ROWS, ids=IDS)
def test_each_field_needs_an_approved_patch_version(patch_version, key, nvpair, applied, wire, reset):
    result, calls = h.run_configs([_po({**BASE, key: applied})], "merged", [], patch_version=patch_version)
    assert result.get("failed") and key in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


def test_numeric_441_is_admitted():
    result, calls = h.run_configs([_po(SET)], "merged", [], patch_version="4.4.1")
    assert not result.get("failed"), result.get("msg")
    assert _sel(_only(calls)) == SET_WIRE


@pytest.mark.parametrize("patch_version", [None, h.UNSUPPORTED_PATCH], ids=["no_patch_version", "unsupported_patch"])
def test_omission_under_a_closed_gate_resets_nothing(patch_version):
    result, calls = h.run_configs([_po(BASE)], "replaced", _l3po_pim_bfd_have(SET), patch_version=patch_version)
    assert not result.get("failed"), result.get("msg")
    for c in h.writes(calls):
        found = []
        h._collect_policies([c["payload"]], found)
        for p in found:
            for i in p["interfaces"]:
                assert _sel(i.get("nvPairs") or {}) in ({}, SET_WIRE), i


def test_a_plain_l3_port_channel_carries_none_of_the_three():
    result, calls = h.run_configs([_po(BASE)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    assert _sel(_only(calls)) == {}


@pytest.mark.parametrize("parent", [h.PC_TRUNK, h.PC_ACCESS, h.PC_DOT1Q])
@pytest.mark.parametrize("key,nvpair,applied,wire,reset", ROWS, ids=IDS)
def test_the_keys_stay_refused_on_the_layer2_port_channels(parent, key, nvpair, applied, wire, reset):
    result, calls = h.run_configs([h.cfg_for(parent, {**h.base_for(parent), key: applied})], "merged", [])
    assert result.get("failed") and key in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []
