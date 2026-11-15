"""MACsec on the routed port-channel (registry lot rp2).

The int_l3_port_channel body of the supported patch release declares the four MACsec nvPairs of int_routed_host with the
same types, bounds and gates, refuses the enabler without a key chain and a policy, and passes the four values to every
member, whose body renders the MACsec line. The rows reuse the int_routed_host public keys and contracts except the
reset: the int_routed_host resets were measured on a parent that renders MACsec inline, while this one renders it on the
members, so these rows declare none. Under replaced and overridden an omitted MACsec value is refused before any write;
the explicit coordinated disable (enabler false, names empty) is sent as requested. The module writes the port-channel
nvPairs only. The per-route omission cases are in test_binding_rp_omission.py.

Real main() through helpers/binding_harness: only inventory, transport and sleep are mocked, and every HAVE is the
payload the module itself emits for a public profile. Values are synthetic. Nothing here is live evidence.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_by_nvpair

from .helpers import binding_harness as h
from .test_binding_smu017 import L3PO, MARK, DEPLOY, MEM_A, PO_A
from .test_binding_smu017 import _identities, _l3po_pim_bfd_as_have, _l3po_pim_bfd_have, _l3po_pim_bfd_query_transport
from .test_binding_smu017 import _l3po_pim_bfd_run, _member_have, _only, _paths, _po
from unittest.mock import patch

# (public key, nvPair, applied public value, applied wire value, explicit neutral wire)
ROWS = [
    ("enable_macsec_interface_policy", "macsecInterfacePolicy", True, "true", "false"),
    ("macsec_key_chain_name", "macsecKeyChainName", "PILOT-KC", "PILOT-KC", ""),
    ("macsec_policy_name", "macsecPolicyName", "PILOT-POL", "PILOT-POL", ""),
    ("macsec_fallback_key_chain_name", "macsecFallbackKeyChainName", "PILOT-FBKC", "PILOT-FBKC", ""),
]
IDS = [r[0] for r in ROWS]
NVPAIRS = [r[1] for r in ROWS]
BASE = dict(h.BASE_PC_L3)
ON = {**BASE, "enable_macsec_interface_policy": True, "macsec_key_chain_name": "PILOT-KC",
      "macsec_policy_name": "PILOT-POL"}
FULL = {**ON, "macsec_fallback_key_chain_name": "PILOT-FBKC"}
ON_WIRE = {"macsecInterfacePolicy": "true", "macsecKeyChainName": "PILOT-KC", "macsecPolicyName": "PILOT-POL"}
FULL_WIRE = {**ON_WIRE, "macsecFallbackKeyChainName": "PILOT-FBKC"}
OFF_WIRE = {r[1]: r[4] for r in ROWS}
KEPT_NV = ("MEMBER_INTERFACES", "IP", "PREFIX", "INTF_VRF", "MTU", "DESC")


def _sel(nv, keys=NVPAIRS):
    return {k: nv.get(k) for k in keys if k in nv}


def _routed_nv(profile):
    result, calls = h.run_configs([h.cfg(h.IF_A, {**h.BASE_ROUTED, **profile})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    assert [p["policy"] for p in found] == [h.ROUTED], found
    return found[0]["interfaces"][0]["nvPairs"]


def _macsec_keys(profile):
    return {k: v for k, v in profile.items() if k in IDS}


# ------------------------------------------------------------------ the rows are the routed Ethernet contracts
@pytest.mark.parametrize("key,nvpair,applied,wire,neutral", ROWS, ids=IDS)
def test_the_row_reuses_the_routed_ethernet_contract_without_its_reset(key, nvpair, applied, wire, neutral):
    b = resolve_binding(L3PO, key)
    assert b is not None, "%s is not registered on int_l3_port_channel" % key
    assert (b["parent_nvpair"], b["mechanism"]) == (nvpair, "passthrough")
    assert (b["applicable_interface_type"], b["applicable_mode"]) == ("pc", "l3")
    assert resolve_by_nvpair(L3PO, nvpair) is b
    assert "reset_wire" not in b and "inert_when" not in b and b["no_log"] is False
    routed = resolve_binding(h.ROUTED, key)
    for field in ("parent_nvpair", "type", "default_template", "min_length", "max_length",
                  "string_compare", "min_ndfc_version", "no_log"):
        assert b.get(field) == routed.get(field), (key, field)
    # The routed reset stays the evidence for a later measurement on this parent; it is not used here.
    assert routed.get("reset_wire") == neutral


# ------------------------------------------------------------------ merged create and update
@pytest.mark.parametrize("profile,wire", [(ON, ON_WIRE), (FULL, FULL_WIRE)], ids=["no_fallback", "fallback"])
def test_merged_create_sends_the_parent_values_only_and_deploys_the_port_channel(profile, wire):
    """Both child branches of the member body are selected by these parent values; the module writes no member."""
    result, calls = h.run_configs([_po({**profile, "members": [MEM_A]})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert _sel(nv) == wire
    assert nv["MEMBER_INTERFACES"] == MEM_A
    assert _paths(calls) == ["POST globalInterface", "POST globalInterface/deploy"], _paths(calls)
    assert _sel(nv) == _sel(_routed_nv(_macsec_keys(profile))), "same keys, same nvPairs as routed Ethernet"


def test_the_names_are_compared_with_their_case():
    have = _l3po_pim_bfd_have(FULL)
    result, calls = h.run_configs([_po({**FULL, "macsec_key_chain_name": "pilot-kc"})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)["macsecKeyChainName"] == "pilot-kc"


def test_merged_fallback_clear_is_independent_and_differs_from_omission():
    have = _l3po_pim_bfd_have(FULL)
    result, calls = h.run_configs([_po({**BASE, "macsec_fallback_key_chain_name": ""})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert _sel(_only(calls)) == {**ON_WIRE, "macsecFallbackKeyChainName": ""}
    result, calls = h.run_configs([_po(BASE)], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [], "omission under merged keeps the stored values"


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_explicit_coordinated_disable_sends_the_enabler_and_the_names_together(state):
    """Sent as requested. Whether the member lines are removed on deploy is not measured on this parent."""
    have = _l3po_pim_bfd_have(FULL)
    off = {**BASE, "enable_macsec_interface_policy": False, "macsec_key_chain_name": "", "macsec_policy_name": "",
           "macsec_fallback_key_chain_name": ""}
    result, calls = h.run_configs([_po(off)], state, have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert _sel(nv) == OFF_WIRE
    result, calls = h.run_configs([_po(off)], state, _l3po_pim_bfd_as_have(nv))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [], "the state the module produced converges"


def test_the_enabler_without_names_is_transported_as_on_routed_ethernet():
    """The template refuses it ("MACsec keychain and policy are required ..."); the module does not duplicate the rule,
    as on int_routed_host. The controller response is not observed here."""
    profile = {"enable_macsec_interface_policy": True}
    result, calls = h.run_configs([_po({**BASE, **profile})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    assert _sel(_only(calls)) == {"macsecInterfacePolicy": "true"} == _sel(_routed_nv(profile))


@pytest.mark.parametrize("state", ["merged", "replaced"])
@pytest.mark.parametrize("profile", [ON, FULL], ids=["no_fallback", "fallback"])
def test_repeat_of_the_stored_values_writes_nothing(state, profile):
    result, calls = h.run_configs([_po(profile)], state, _l3po_pim_bfd_have(profile))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and not result.get("changed")


# ------------------------------------------------------------------ invalid input
@pytest.mark.parametrize("change,needle", [
    ({"macsec_key_chain_name": "K" * 65}, "macsec_key_chain_name"),
    ({"macsec_policy_name": "P" * 65}, "macsec_policy_name"),
    ({"macsec_fallback_key_chain_name": "F" * 65}, "macsec_fallback_key_chain_name"),
    ({"enable_macsec_interface_policy": "maybe"}, "enable_macsec_interface_policy"),
], ids=["kc_65", "policy_65", "fallback_65", "enabler_not_bool"])
def test_invalid_values_are_refused_before_any_write(change, needle):
    result, calls = h.run_configs([_po({**FULL, **change})], "merged", [])
    assert result.get("failed") and needle in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


# ------------------------------------------------------------------ replaced, overridden, deleted, query, check mode
def test_replaced_without_macsec_is_refused_before_any_write():
    result, calls = h.run_configs([_po(BASE)], "replaced", _l3po_pim_bfd_have(FULL))
    assert result.get("failed") is True
    assert all("%s on %s" % (key, L3PO) in result["msg"] for key in IDS), result["msg"]
    assert not any(v in result["msg"] for v in ("PILOT-KC", "PILOT-POL", "PILOT-FBKC")), "the refusal named a value"
    assert h.writes(calls) == []


def test_replaced_omitting_only_the_fallback_is_refused_and_the_explicit_clear_is_sent():
    result, calls = h.run_configs([_po(ON)], "replaced", _l3po_pim_bfd_have(FULL))
    assert result.get("failed") is True
    assert "macsec_fallback_key_chain_name on %s" % L3PO in result["msg"], result["msg"]
    assert "macsec_key_chain_name on" not in result["msg"]
    assert h.writes(calls) == []
    result, calls = h.run_configs([_po({**ON, "macsec_fallback_key_chain_name": ""})], "replaced", _l3po_pim_bfd_have(FULL))
    assert not result.get("failed"), result.get("msg")
    assert _sel(_only(calls)) == {**ON_WIRE, "macsecFallbackKeyChainName": ""}


def test_replaced_omission_at_the_neutral_values_writes_nothing():
    have = _l3po_pim_bfd_have(BASE)
    have[0]["interfaces"][0]["nvPairs"].update(OFF_WIRE)
    result, calls = h.run_configs([_po(BASE)], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_overridden_retained_port_channel_refuses_the_same_withdrawal():
    have = _l3po_pim_bfd_have({**FULL, "members": [MEM_A]}) + _member_have(MEM_A, PO_A)
    result, calls = _l3po_pim_bfd_run([_po({**BASE, "members": [MEM_A]})], "overridden", have)
    assert result.get("failed") is True
    assert _identities(calls) == [] and h.writes(calls) == []


def test_deleted_removes_the_port_channel_and_a_repeat_writes_nothing():
    target = [{"name": PO_A, "type": "pc", "switch": [h.SWITCH_IP]}]
    have = _l3po_pim_bfd_have({**FULL, "members": [MEM_A]}) + _member_have(MEM_A, PO_A)
    result, calls = _l3po_pim_bfd_run(target, "deleted", have)
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [(MARK, [[h.SERIAL, PO_A]]), (DEPLOY, [[h.SERIAL, PO_A]])]
    result, calls = _l3po_pim_bfd_run(target, "deleted", [])
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == []


def test_query_returns_the_controller_values_unchanged():
    target = _l3po_pim_bfd_have(FULL)
    writes = []
    with patch.object(h, "_transport", _l3po_pim_bfd_query_transport(target, writes)):
        result, calls = h.run_configs([{"name": PO_A, "switch": [h.SWITCH_IP]}], "query", [])
    assert not result.get("failed"), result.get("msg")
    assert writes == [] and h.writes(calls) == [] and not result.get("changed")
    assert result["response"] == target
    assert _sel(result["response"][0]["interfaces"][0]["nvPairs"]) == FULL_WIRE


def test_check_mode_reports_the_change_and_writes_nothing():
    profile = {**FULL, "macsec_policy_name": "PILOT-POL-B"}
    result, calls = h.run_configs([_po(profile)], "merged", _l3po_pim_bfd_have(FULL), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and result.get("changed") is True


def test_check_mode_refuses_the_replaced_omission():
    result, calls = h.run_configs([_po(BASE)], "replaced", _l3po_pim_bfd_have(FULL), check_mode=True)
    assert result.get("failed") is True
    assert h.writes(calls) == []


# ------------------------------------------------------------------ version gate and scope
@pytest.mark.parametrize("patch_version", [None, h.UNSUPPORTED_PATCH], ids=["no_patch_version", "unsupported_patch"])
@pytest.mark.parametrize("key,nvpair,applied,wire,neutral", ROWS, ids=IDS)
def test_each_field_needs_an_approved_patch_version(patch_version, key, nvpair, applied, wire, neutral):
    result, calls = h.run_configs([_po({**BASE, key: applied})], "merged", [], patch_version=patch_version)
    assert result.get("failed") and key in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


def test_numeric_441_is_admitted():
    result, calls = h.run_configs([_po(FULL)], "merged", [], patch_version="4.4.1")
    assert not result.get("failed"), result.get("msg")
    assert _sel(_only(calls)) == FULL_WIRE


@pytest.mark.parametrize("patch_version", [None, h.UNSUPPORTED_PATCH], ids=["no_patch_version", "unsupported_patch"])
def test_omission_under_a_closed_gate_resets_nothing(patch_version):
    result, calls = h.run_configs([_po(BASE)], "replaced", _l3po_pim_bfd_have(FULL), patch_version=patch_version)
    assert not result.get("failed"), result.get("msg")
    for c in h.writes(calls):
        found = []
        h._collect_policies([c["payload"]], found)
        for p in found:
            for i in p["interfaces"]:
                assert _sel(i.get("nvPairs") or {}) in ({}, FULL_WIRE), i


@pytest.mark.parametrize("parent", [h.PC_TRUNK, h.PC_ACCESS, h.PC_DOT1Q])
@pytest.mark.parametrize("key,nvpair,applied,wire,neutral", ROWS, ids=IDS)
def test_the_keys_stay_refused_on_the_layer2_port_channels(parent, key, nvpair, applied, wire, neutral):
    result, calls = h.run_configs([h.cfg_for(parent, {**h.base_for(parent), key: applied})], "merged", [])
    assert result.get("failed") and key in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []
