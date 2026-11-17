"""IPv6 addressing, link-local, ND suppress-RA and redirects on the routed port-channel (registry lot rp3).

The int_l3_port_channel body of the supported patch release declares IPv6 and IPv6_PREFIX, requires the prefix while
the address is set and renders the address only when both are set. It blanks the split redirect options while
DISABLE_IP_REDIRECTS is true. The address pair reuses the native public keys of the other routed profiles, and so does
the combined redirect option (the SVI key), with this parent's default. The engine refuses a request that ends with one
half of the address pair, and an explicit split redirect false while the combined option ends true. Link-local, ND and
the split redirects reuse the int_routed_host contracts, with the resets measured live on this parent ("" and "false");
their omission cases are in test_binding_l3po_measured_resets.py. A split reset is sent only while the combined option
is stored "false" and ends "false". The address pair and the combined option have no reset, so under replaced and
overridden an omitted value that differs from the default is refused before any write (per route in
test_binding_rp_omission.py). The integer prefix has no public clear, so clearing the address while a prefix is stored
is refused too: the address is removed only with the port-channel. A split option stored while the combined option
ends true configures nothing and is kept.

Real main() through helpers/binding_harness: only inventory, transport and sleep are mocked, and every HAVE is the
payload the module itself emits for a public profile. Values are synthetic. Nothing here is live evidence.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_by_nvpair

from .helpers import binding_harness as h
from .test_binding_smu017 import L3PO, MARK, DEPLOY, MEM_A, PO_A
from .test_binding_smu017 import _identities, _l3po_pim_bfd_as_have, _l3po_pim_bfd_have, _l3po_pim_bfd_query_transport
from .test_binding_smu017 import _l3po_pim_bfd_run, _member_have, _only, _paths, _po
from unittest.mock import patch

NVPAIRS = ("IPv6", "IPv6_PREFIX", "ipv6LinkLocal", "ipv6NdSuppressRa", "DISABLE_IP_REDIRECTS", "ipv4Redirects",
           "ipv6Redirects")
ROUTED_COPIES = [
    ("ipv6_link_local", "ipv6LinkLocal"),
    ("ipv6_nd_suppress_ra", "ipv6NdSuppressRa"),
    ("disable_ipv4_redirects", "ipv4Redirects"),
    ("disable_ipv6_redirects", "ipv6Redirects"),
]
BASE = dict(h.BASE_PC_L3)
ADDR = {"ipv6_addr": "2001:db8::31", "ipv6_mask_len": 64}
ADDR_WIRE = {"IPv6": "2001:db8::31", "IPv6_PREFIX": "64"}
SET = {**BASE, **ADDR, "ipv6_link_local": "fe80::31", "ipv6_nd_suppress_ra": True, "disable_ipv4_redirects": True,
       "disable_ipv6_redirects": False}
SET_WIRE = {**ADDR_WIRE, "ipv6LinkLocal": "fe80::31", "ipv6NdSuppressRa": "true", "ipv4Redirects": "true",
            "ipv6Redirects": "false"}
# The keys of SET that replaced and overridden cannot withdraw, and the ones they reset (combined option stored false).
REFUSED_KEYS = ("ipv6_addr", "ipv6_mask_len")
RESET_KEYS = ("ipv6_link_local", "ipv6_nd_suppress_ra", "disable_ipv4_redirects", "disable_ipv6_redirects")
KEPT_NV = ("MEMBER_INTERFACES", "IP", "PREFIX", "INTF_VRF", "MTU", "DESC")


def _sel(nv, keys=NVPAIRS):
    return {k: nv.get(k) for k in keys if k in nv}


def _routed_nv(profile, base=None):
    result, calls = h.run_configs([h.cfg(h.IF_A, {**(base or h.BASE_ROUTED), **profile})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    assert [p["policy"] for p in found] == [h.ROUTED], found
    return found[0]["interfaces"][0]["nvPairs"]


def _refused(result, calls, *needles):
    msg = str(result.get("msg", ""))
    assert result.get("failed"), "the request was accepted"
    for needle in needles:
        assert needle in msg, msg
    assert h.writes(calls) == []
    return msg


# ------------------------------------------------------------------ the rows
@pytest.mark.parametrize("key,nvpair", ROUTED_COPIES, ids=[r[0] for r in ROUTED_COPIES])
def test_link_local_nd_and_split_redirects_reuse_the_routed_ethernet_contract(key, nvpair):
    b = resolve_binding(L3PO, key)
    assert b is not None and (b["parent_nvpair"], b["mechanism"]) == (nvpair, "passthrough")
    assert (b["applicable_interface_type"], b["applicable_mode"]) == ("pc", "l3")
    assert resolve_by_nvpair(L3PO, nvpair) is b
    routed = resolve_binding(h.ROUTED, key)
    for field in ("parent_nvpair", "type", "default_template", "max_length", "string_compare",
                  "min_ndfc_version", "no_log", "inert_when"):
        assert b.get(field) == routed.get(field), (key, field)
    # The wire measured on this parent is the routed one.
    assert b["reset_wire"] == routed["reset_wire"]


def test_the_address_pair_and_the_combined_option_have_no_reset():
    for nvpair in ("IPv6", "IPv6_PREFIX", "DISABLE_IP_REDIRECTS"):
        assert "reset_wire" not in resolve_by_nvpair(L3PO, nvpair), nvpair


def test_the_address_pair_uses_the_native_public_keys_and_the_template_bounds():
    addr, prefix = resolve_binding(L3PO, "ipv6_addr"), resolve_binding(L3PO, "ipv6_mask_len")
    assert (addr["parent_nvpair"], addr["type"], addr["max_length"], addr["string_compare"]) == (
        "IPv6", "string", 45, "casefold")
    assert (prefix["parent_nvpair"], prefix["type"], prefix["min_value"], prefix["max_value"]) == (
        "IPv6_PREFIX", "integer", 1, 127)
    for b in (addr, prefix):
        assert not {"reset_wire", "default_template", "inert_when"} & set(b), b
    assert ("int_l3_port_channel", "IPv6", "IPv6_PREFIX") in gie_engine.GIE_PAIRED_NVPAIRS
    assert {"ipv6_addr", "ipv6_mask_len", "disable_ip_redirects"} <= gie_engine.GIE_NATIVE_ELSEWHERE_KEYS


def test_the_combined_redirect_option_has_this_parents_default_not_the_svi_default():
    b = resolve_binding(L3PO, "disable_ip_redirects")
    assert (b["parent_nvpair"], b["type"], b["default_template"]) == ("DISABLE_IP_REDIRECTS", "boolean", False)
    assert "reset_wire" not in b
    assert resolve_binding(h.SVI, "disable_ip_redirects") is None, "the SVI keeps its native field"
    assert gie_engine.GIE_SUPERSEDING_ALIASES == (
        ("int_l3_port_channel", "DISABLE_IP_REDIRECTS", "true", ("ipv4Redirects", "ipv6Redirects")),)


# ------------------------------------------------------------------ merged create and update
def test_merged_create_sends_every_field_and_deploys_it():
    result, calls = h.run_configs([_po(SET)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert _sel(nv) == SET_WIRE and all(isinstance(nv[k], str) for k in SET_WIRE)
    assert _paths(calls) == ["POST globalInterface", "POST globalInterface/deploy"], _paths(calls)


def test_the_address_pair_reaches_the_same_nvpairs_as_routed_ethernet():
    nv_po = _sel(_only(h.run_configs([_po({**BASE, **ADDR})], "merged", [])[1]), ["IPv6", "IPv6_PREFIX"])
    assert nv_po == ADDR_WIRE == _sel(_routed_nv(ADDR), ["IPv6", "IPv6_PREFIX"])


def test_the_combined_redirect_option_alone_is_sent():
    result, calls = h.run_configs([_po({**BASE, "disable_ip_redirects": True})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    assert _sel(_only(calls)) == {"DISABLE_IP_REDIRECTS": "true"}


def test_the_address_is_compared_without_case():
    have = _l3po_pim_bfd_have({**BASE, "ipv6_addr": "2001:DB8::31", "ipv6_mask_len": 64})
    result, calls = h.run_configs([_po({**BASE, **ADDR})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_repeat_of_the_stored_values_writes_nothing(state):
    result, calls = h.run_configs([_po(SET)], state, _l3po_pim_bfd_have(SET))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and not result.get("changed")


# ------------------------------------------------------------------ the address pair
@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_a_new_address_without_a_prefix_is_refused_before_any_write(state):
    result, calls = h.run_configs([_po({**BASE, "ipv6_addr": "2001:db8::31"})], state, [])
    _refused(result, calls, "ipv6_mask_len (with ipv6_addr enabled)")


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_a_prefix_without_an_address_is_refused_before_any_write(state):
    result, calls = h.run_configs([_po({**BASE, "ipv6_mask_len": 64})], state, [])
    _refused(result, calls, "ipv6_mask_len (needs ipv6_addr)")


def test_merged_prefix_change_keeps_the_stored_address():
    result, calls = h.run_configs([_po({**BASE, "ipv6_mask_len": 96})], "merged", _l3po_pim_bfd_have({**BASE, **ADDR}))
    assert not result.get("failed"), result.get("msg")
    assert _sel(_only(calls), ["IPv6", "IPv6_PREFIX"]) == {"IPv6": "2001:db8::31", "IPv6_PREFIX": "96"}


def test_merged_address_change_keeps_the_stored_prefix():
    result, calls = h.run_configs([_po({**BASE, "ipv6_addr": "2001:db8::32"})], "merged",
                                  _l3po_pim_bfd_have({**BASE, **ADDR}))
    assert not result.get("failed"), result.get("msg")
    assert _sel(_only(calls), ["IPv6", "IPv6_PREFIX"]) == {"IPv6": "2001:db8::32", "IPv6_PREFIX": "64"}


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_an_address_clear_over_a_stored_prefix_is_refused_before_any_write(state):
    """The prefix has no reset and no public clear, so the request cannot end with both empty; it is not sent half
    done. The empty prefix is refused as input as well."""
    have = _l3po_pim_bfd_have({**BASE, **ADDR})
    result, calls = h.run_configs([_po({**BASE, "ipv6_addr": ""})], state, have)
    msg = _refused(result, calls, "ipv6_addr (paired with ipv6_mask_len)", "no supported clear")
    assert "2001:db8::31" not in msg and "64" not in msg.replace("Port-channel", ""), "the refusal named a value"
    result, calls = h.run_configs([_po({**BASE, "ipv6_addr": "", "ipv6_mask_len": ""})], state, have)
    _refused(result, calls, "ipv6_mask_len")


def test_an_address_clear_without_a_stored_pair_writes_nothing():
    have = _l3po_pim_bfd_have(BASE)
    have[0]["interfaces"][0]["nvPairs"].update({"IPv6": "", "IPv6_PREFIX": ""})
    result, calls = h.run_configs([_po({**BASE, "ipv6_addr": ""})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_merged_prefix_on_a_port_channel_without_an_address_is_refused():
    result, calls = h.run_configs([_po({**BASE, "ipv6_mask_len": 80})], "merged", _l3po_pim_bfd_have(BASE))
    _refused(result, calls, "ipv6_mask_len (needs ipv6_addr)")


def test_merged_address_on_a_port_channel_without_a_prefix_is_refused():
    result, calls = h.run_configs([_po({**BASE, "ipv6_addr": "2001:db8::31"})], "merged", _l3po_pim_bfd_have(BASE))
    _refused(result, calls, "ipv6_mask_len (with ipv6_addr enabled)")


def test_replaced_address_without_the_prefix_is_refused_even_with_a_stored_prefix():
    """Replaced would have to withdraw the omitted prefix, and the prefix has no reset."""
    result, calls = h.run_configs([_po({**BASE, "ipv6_addr": "2001:db8::31"})], "replaced",
                                  _l3po_pim_bfd_have({**BASE, **ADDR}))
    _refused(result, calls, "ipv6_mask_len")


def test_replaced_without_the_pair_is_refused_before_any_write():
    have = _l3po_pim_bfd_have({**BASE, **ADDR})
    result, calls = h.run_configs([_po(BASE)], "replaced", have)
    _refused(result, calls, "ipv6_addr on %s" % L3PO, "ipv6_mask_len on %s" % L3PO)


def test_replaced_without_the_pair_over_an_empty_pair_writes_nothing():
    have = _l3po_pim_bfd_have(BASE)
    have[0]["interfaces"][0]["nvPairs"].update({"IPv6": "", "IPv6_PREFIX": ""})
    result, calls = h.run_configs([_po(BASE)], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_an_unrelated_change_is_not_judged_by_the_pair_rule():
    """A request that sets neither half leaves the pair to the controller, as stored."""
    have = _l3po_pim_bfd_have(BASE)
    have[0]["interfaces"][0]["nvPairs"]["IPv6"] = "2001:db8::31"     # an inconsistent stored state
    result, calls = h.run_configs([_po({**BASE, "description": "changed"})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)["DESC"] == "changed"


@pytest.mark.parametrize("change,needle", [
    ({"ipv6_mask_len": 0}, "ipv6_mask_len"),
    ({"ipv6_mask_len": 128}, "ipv6_mask_len"),
    ({"ipv6_addr": "2001:db8::" + "1" * 40}, "ipv6_addr"),
    ({"ipv6_link_local": "fe80::" + "1" * 40}, "ipv6_link_local"),
    ({"disable_ip_redirects": "maybe"}, "disable_ip_redirects"),
], ids=["prefix_0", "prefix_128", "addr_46", "link_local_46", "combined_not_bool"])
def test_invalid_values_are_refused_before_any_write(change, needle):
    result, calls = h.run_configs([_po({**BASE, **ADDR, **change})], "merged", [])
    _refused(result, calls, needle)


# ------------------------------------------------------------------ the combined redirect option
@pytest.mark.parametrize("split", ["disable_ipv4_redirects", "disable_ipv6_redirects"])
def test_a_split_false_beside_the_combined_true_is_refused(split):
    result, calls = h.run_configs([_po({**BASE, "disable_ip_redirects": True, split: False})], "merged", [])
    _refused(result, calls, "%s (overridden by disable_ip_redirects)" % split)


@pytest.mark.parametrize("split", ["disable_ipv4_redirects", "disable_ipv6_redirects"])
def test_a_split_false_against_a_stored_combined_true_is_refused_under_merged(split):
    have = _l3po_pim_bfd_have({**BASE, "disable_ip_redirects": True})
    result, calls = h.run_configs([_po({**BASE, split: False})], "merged", have)
    _refused(result, calls, "%s (overridden by disable_ip_redirects)" % split)


def test_clearing_the_combined_option_in_the_same_task_lets_the_split_false_through():
    have = _l3po_pim_bfd_have({**BASE, "disable_ip_redirects": True})
    result, calls = h.run_configs([_po({**BASE, "disable_ip_redirects": False, "disable_ipv4_redirects": False,
                                        "disable_ipv6_redirects": True})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert _sel(_only(calls)) == {"DISABLE_IP_REDIRECTS": "false", "ipv4Redirects": "false", "ipv6Redirects": "true"}


def test_replaced_split_false_with_an_omitted_stored_combined_true_is_refused():
    """The omitted combined option cannot be withdrawn (no reset), so it ends true and supersedes the split false."""
    have = _l3po_pim_bfd_have({**BASE, "disable_ip_redirects": True})
    result, calls = h.run_configs([_po({**BASE, "disable_ipv4_redirects": False})], "replaced", have)
    _refused(result, calls, "disable_ipv4_redirects (overridden by disable_ip_redirects)")


def test_a_split_true_beside_the_combined_true_is_redundant_and_sent():
    result, calls = h.run_configs([_po({**BASE, "disable_ip_redirects": True, "disable_ipv4_redirects": True})],
                                  "merged", [])
    assert not result.get("failed"), result.get("msg")
    assert _sel(_only(calls)) == {"DISABLE_IP_REDIRECTS": "true", "ipv4Redirects": "true"}


def test_replaced_with_the_combined_true_keeps_the_superseded_split_options():
    """The template blanks the split options while the combined option is true, so the stored values configure nothing
    and nothing is sent for them: no false is written over a value the template ignores."""
    have = _l3po_pim_bfd_have({**BASE, "disable_ipv4_redirects": True, "disable_ipv6_redirects": True})
    result, calls = h.run_configs([_po({**BASE, "disable_ip_redirects": True})], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert nv["DISABLE_IP_REDIRECTS"] == "true"
    assert (nv.get("ipv4Redirects", "true"), nv.get("ipv6Redirects", "true")) == ("true", "true"), nv
    result, calls = h.run_configs([_po({**BASE, "disable_ip_redirects": True})], "replaced", _l3po_pim_bfd_as_have(nv))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [], "the state the module produced converges"


def test_replaced_with_a_stored_combined_true_kept_and_a_stored_split_false_writes_nothing():
    have = _l3po_pim_bfd_have({**BASE, "disable_ipv4_redirects": False})
    have[0]["interfaces"][0]["nvPairs"]["DISABLE_IP_REDIRECTS"] = "true"
    result, calls = h.run_configs([_po({**BASE, "disable_ip_redirects": True})], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_replaced_omitting_a_live_split_option_resets_it():
    """With the combined option stored and kept at its default the split option is live and is reset to "false"."""
    have = _l3po_pim_bfd_have({**BASE, "disable_ip_redirects": False, "disable_ipv4_redirects": True})
    result, calls = h.run_configs([_po({**BASE, "disable_ip_redirects": False})], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    assert _sel(_only(calls)) == {"DISABLE_IP_REDIRECTS": "false", "ipv4Redirects": "false"}


def test_replaced_omitting_a_split_option_without_a_stored_combined_option_is_refused():
    have = _l3po_pim_bfd_have({**BASE, "disable_ipv4_redirects": True})
    assert "DISABLE_IP_REDIRECTS" not in have[0]["interfaces"][0]["nvPairs"]
    result, calls = h.run_configs([_po(BASE)], "replaced", have)
    _refused(result, calls, "disable_ipv4_redirects (combined option disable_ip_redirects) on %s" % L3PO)


# ------------------------------------------------------------------ replaced, overridden, deleted, query, check mode
def test_replaced_omission_is_refused_for_the_address_pair_only_and_names_no_value():
    have = _l3po_pim_bfd_have({**SET, "disable_ip_redirects": False})
    result, calls = h.run_configs([_po(BASE)], "replaced", have)
    msg = _refused(result, calls, *("%s on %s" % (k, L3PO) for k in REFUSED_KEYS))
    assert "disable_ip_redirects on" not in msg, "the combined option is stored at its default"
    assert not any(k in msg for k in RESET_KEYS), msg
    assert "2001:db8::31" not in msg and "fe80::31" not in msg


def test_overridden_retained_port_channel_refuses_the_address_pair_withdrawal():
    have = _l3po_pim_bfd_have({**SET, "disable_ip_redirects": False, "members": [MEM_A]}) + _member_have(MEM_A, PO_A)
    result, calls = _l3po_pim_bfd_run([_po({**BASE, "members": [MEM_A]})], "overridden", have)
    msg = _refused(result, calls, *("%s on %s" % (k, L3PO) for k in REFUSED_KEYS))
    assert not any(k in msg for k in RESET_KEYS), msg
    assert _identities(calls) == []


def test_overridden_with_half_of_the_pair_is_refused():
    have = _l3po_pim_bfd_have({**SET, "members": [MEM_A]}) + _member_have(MEM_A, PO_A)
    result, calls = _l3po_pim_bfd_run([_po({**BASE, "members": [MEM_A], "ipv6_mask_len": 64})], "overridden", have)
    assert result.get("failed") and "ipv6_addr" in str(result.get("msg"))
    assert _identities(calls) == []


def test_deleted_removes_the_port_channel_and_a_repeat_writes_nothing():
    target = [{"name": PO_A, "type": "pc", "switch": [h.SWITCH_IP]}]
    have = _l3po_pim_bfd_have({**SET, "members": [MEM_A]}) + _member_have(MEM_A, PO_A)
    result, calls = _l3po_pim_bfd_run(target, "deleted", have)
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [(MARK, [[h.SERIAL, PO_A]]), (DEPLOY, [[h.SERIAL, PO_A]])]
    result, calls = _l3po_pim_bfd_run(target, "deleted", [])
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == []


def test_query_returns_the_controller_values_unchanged():
    target = _l3po_pim_bfd_have(SET)
    writes = []
    with patch.object(h, "_transport", _l3po_pim_bfd_query_transport(target, writes)):
        result, calls = h.run_configs([{"name": PO_A, "switch": [h.SWITCH_IP]}], "query", [])
    assert not result.get("failed"), result.get("msg")
    assert writes == [] and h.writes(calls) == [] and not result.get("changed")
    assert result["response"] == target and _sel(result["response"][0]["interfaces"][0]["nvPairs"]) == SET_WIRE


def test_check_mode_reports_the_change_and_writes_nothing():
    result, calls = h.run_configs([_po({**SET, "ipv6_mask_len": 80})], "merged", _l3po_pim_bfd_have(SET), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and result.get("changed") is True


def test_check_mode_refuses_the_replaced_omission():
    result, calls = h.run_configs([_po(BASE)], "replaced", _l3po_pim_bfd_have(SET), check_mode=True)
    _refused(result, calls, "ipv6_addr on %s" % L3PO)


def test_check_mode_also_refuses_half_of_the_pair():
    result, calls = h.run_configs([_po({**BASE, "ipv6_addr": "2001:db8::31"})], "merged", [], check_mode=True)
    _refused(result, calls, "ipv6_mask_len")


# ------------------------------------------------------------------ version gate and scope
KEYS = [("ipv6_addr", "2001:db8::31"), ("ipv6_mask_len", 64), ("ipv6_link_local", "fe80::31"),
        ("ipv6_nd_suppress_ra", True), ("disable_ip_redirects", True), ("disable_ipv4_redirects", True),
        ("disable_ipv6_redirects", True)]


@pytest.mark.parametrize("patch_version", [None, h.UNSUPPORTED_PATCH], ids=["no_patch_version", "unsupported_patch"])
@pytest.mark.parametrize("key,value", KEYS, ids=[k for k, _v in KEYS])
def test_each_field_needs_an_approved_patch_version(patch_version, key, value):
    result, calls = h.run_configs([_po({**BASE, key: value})], "merged", [], patch_version=patch_version)
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


NATIVE_ELSEWHERE = ("ipv6_addr", "ipv6_mask_len", "disable_ip_redirects")


@pytest.mark.parametrize("parent", [h.PC_TRUNK, h.PC_ACCESS, h.PC_DOT1Q])
@pytest.mark.parametrize("key,value", [kv for kv in KEYS if kv[0] not in NATIVE_ELSEWHERE],
                         ids=[k for k, _v in KEYS if k not in NATIVE_ELSEWHERE])
def test_the_keys_stay_refused_on_the_layer2_port_channels(parent, key, value):
    result, calls = h.run_configs([h.cfg_for(parent, {**h.base_for(parent), key: value})], "merged", [])
    assert result.get("failed") and key in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("parent", [h.PC_TRUNK, h.PC_ACCESS, h.PC_DOT1Q])
@pytest.mark.parametrize("key,value", [kv for kv in KEYS if kv[0] in NATIVE_ELSEWHERE], ids=list(NATIVE_ELSEWHERE))
def test_a_native_key_keeps_the_legacy_discard_on_the_layer2_port_channels(parent, key, value):
    """Listed in GIE_NATIVE_ELSEWHERE_KEYS, so the invalid-parent guard leaves these parents as they were before the
    key was registered: the module drops the unknown key and sends no nvPair for it."""
    result, calls = h.run_configs([h.cfg_for(parent, {**h.base_for(parent), key: value})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    nvpair = resolve_binding(L3PO, key)["parent_nvpair"]
    assert found and all(nvpair not in i["nvPairs"] for p in found for i in p["interfaces"])


# ------------------------------------------------------------------ the native parents keep their paths
def test_the_routed_ethernet_native_pair_is_unchanged():
    """Including the native default prefix of a routed address sent without one."""
    nv = _routed_nv({"ipv6_addr": "2001:db8::41"})
    assert (nv["IPv6"], nv["IPv6_PREFIX"]) == ("2001:db8::41", "64")


def test_the_subinterface_native_pair_is_unchanged():
    result, calls = h.run_configs([h.cfg_for(h.SUBIF, {**h.BASE_SUBIF, "ipv6_addr": "2001:db8::51",
                                                       "ipv6_mask_len": 64})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    nv = found[0]["interfaces"][0]["nvPairs"]
    assert (found[0]["policy"], nv["IPv6"], nv["IPv6_PREFIX"]) == (h.SUBIF, "2001:db8::51", "64")


@pytest.mark.parametrize("value,wire", [(True, "true"), (False, "false"), (None, "true")], ids=["true", "false", "default"])
def test_the_svi_native_combined_redirect_option_is_unchanged(value, wire):
    profile = {k: v for k, v in h.BASE_SVI.items() if k != "disable_ip_redirects"}
    if value is not None:
        profile["disable_ip_redirects"] = value
    result, calls = h.run_configs([h.cfg_for(h.SVI, profile)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    assert found[0]["policy"] == h.SVI and found[0]["interfaces"][0]["nvPairs"]["DISABLE_IP_REDIRECTS"] == wire


# ------------------------------------------------------------------ helper level (not integration coverage)
@pytest.mark.parametrize("want,have,explicit,reason", [
    ({"IPv6": ""}, {"IPv6": "2001:db8::31", "IPv6_PREFIX": "64"}, {"IPv6"}, "no_paired_clear"),
    ({"IPv6_PREFIX": "64"}, {"IPv6": ""}, {"IPv6_PREFIX"}, "set_while_off"),
    ({"IPv6": "2001:db8::31"}, {"IPv6_PREFIX": ""}, {"IPv6"}, "empty_while_on"),
    ({"IPv6": "", "IPv6_PREFIX": ""}, {}, {"IPv6"}, None),
    ({"IPv6": ""}, {"IPv6": "", "IPv6_PREFIX": ""}, {"IPv6"}, None),
], ids=["clear_over_stored_prefix", "prefix_without_address", "address_without_prefix", "both_empty", "already_empty"])
def test_helper_pair_rule_reasons(want, have, explicit, reason):
    _writes, conflicts = gie_engine.gie_dependency_plan(L3PO, want, have, explicit, True, "12.6.0.267", h.SUPPORTED_PATCH)
    assert [c["reason"] for c in conflicts] == ([reason] if reason else []), conflicts


@pytest.mark.parametrize("nvpairs,superseded", [
    ({"DISABLE_IP_REDIRECTS": "true"}, True),
    ({"DISABLE_IP_REDIRECTS": True}, True),
    ({"DISABLE_IP_REDIRECTS": "false"}, False),
    ({}, False),
    ({"DISABLE_IP_REDIRECTS": None}, False),
], ids=["wire_true", "native_true", "false", "absent", "null"])
def test_helper_superseded_reads_the_alias_value(nvpairs, superseded):
    for nvpair in ("ipv4Redirects", "ipv6Redirects"):
        assert gie_engine.gie_superseded(L3PO, nvpair, nvpairs) is superseded
    assert gie_engine.gie_superseded(h.ROUTED, "ipv4Redirects", {"DISABLE_IP_REDIRECTS": "true"}) is False
    assert gie_engine.gie_superseded(L3PO, "DISABLE_IP_REDIRECTS", {"DISABLE_IP_REDIRECTS": "true"}) is False


@pytest.mark.parametrize("have,final,measured", [
    ({"DISABLE_IP_REDIRECTS": "false"}, {"DISABLE_IP_REDIRECTS": "false"}, True),
    ({"DISABLE_IP_REDIRECTS": False}, {"DISABLE_IP_REDIRECTS": "false"}, True),
    ({"DISABLE_IP_REDIRECTS": "true"}, {"DISABLE_IP_REDIRECTS": "false"}, False),
    ({"DISABLE_IP_REDIRECTS": "false"}, {"DISABLE_IP_REDIRECTS": "true"}, False),
    ({}, {"DISABLE_IP_REDIRECTS": "false"}, False),
    ({"DISABLE_IP_REDIRECTS": ""}, {"DISABLE_IP_REDIRECTS": ""}, False),
    ({"DISABLE_IP_REDIRECTS": None}, {"DISABLE_IP_REDIRECTS": "false"}, False),
], ids=["stored_false_kept", "native_false", "stored_true_turned_off", "turned_on", "absent", "empty", "null"])
def test_helper_alias_reset_measured_only_with_the_alias_stored_and_kept_false(have, final, measured):
    for nvpair in ("ipv4Redirects", "ipv6Redirects"):
        assert gie_engine.gie_alias_reset_measured(L3PO, nvpair, have, final) is measured
    # Not a dependent: no alias condition.
    assert gie_engine.gie_alias_reset_measured(L3PO, "bfdEcho", {}, {}) is True
    assert gie_engine.gie_alias_reset_measured(h.ROUTED, "ipv4Redirects", {}, {}) is True
