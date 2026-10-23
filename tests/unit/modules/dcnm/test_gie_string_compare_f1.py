"""F1: a case-only change of a registered string whose case is part of its value is sent.

Review finding F1: the legacy scalar comparison lower-cased both sides, so a
case-only change of an OSPF key or an ACL name compared equal and was never sent -- in merged,
replaced and overridden alike. The registry now carries, per (parent template, nvPair), how a
string binding compares (`string_compare`): only 'exact' bindings stop lower-casing; booleans,
enums, IPv6 text and the bindings whose case semantics are not established keep the legacy rule.

Every case drives the real main() through gie_withdrawal_harness (mocks only at inventory,
transport and sleep). Keys and names are synthetic.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table as table
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import gie_withdrawal_harness as h

STATES = ("merged", "replaced", "overridden")

# id: (parent, profile key, nvPair, context, HAVE value, case-only request, different request)
EXACT = {
    "routed-ospf_auth_key": (h.ROUTED, "ospf_auth_key", "OSPF_AUTH_KEY", h.AUTH_MD,
                             "SYNTHETIC-Key-A", "synthetic-key-a", "SYNTHETIC-Key-B"),
    "routed-ospf_authentication_key": (h.ROUTED, "ospf_authentication_key", "ospfAuthenticationKey",
                                       dict(h.OSPF_CTX, ospf_authentication_key_type="3"),
                                       "SYNTHETIC-Md5-A", "synthetic-md5-a", "SYNTHETIC-Md5-B"),
    "trunk-acl_filter": (h.TRUNK, "acl_filter", "aclFilter", {}, "SYNTHETIC-ACL", "synthetic-acl", "SYNTHETIC-ACL-B"),
    "svi-ipv4_acl_in": (h.SVI, "ipv4_acl_in", "ipv4AclIn", {}, "SYNTHETIC-L3-ACL", "synthetic-l3-acl", "SYNTHETIC-L3-ACL-B"),
    "subif-eigrp_ipv4_prefix_list": (h.SUBIF, "eigrp_ipv4_distribute_list_prefix_list", "eigrpIpv4DistributeListPrefixList",
                                     h.EIGRP_CTX, "SYNTHETIC-PL4", "synthetic-pl4", "SYNTHETIC-PL4-B"),
}


def have_of(case):
    parent, key, _nv, ctx, have_value, _c, _d = case
    return h.build_have(parent, key, have_value, **ctx)


def want_of(case, value):
    parent, key, _nv, ctx, _h, _c, _d = case
    prof = h.base_for(parent, **ctx)
    prof[key] = value
    return [h.cfg_for(parent, prof)]


def sent_values(calls, nvpair):
    return [nv[nvpair] for nv in h.request_nvpairs(calls) if nvpair in nv]


# ------------------------------------------------------------------ the registry decision itself
def test_every_registered_string_binding_declares_a_comparison_category():
    strings = [b for b in table.BINDING_TABLE if b["type"] == "string"]
    assert len(strings) == 45
    assert {b["string_compare"] for b in strings} == {"exact", "casefold", "case_irrelevant", "unverified"}
    assert not [b for b in table.BINDING_TABLE if b["type"] != "string" and "string_compare" in b]


@pytest.mark.parametrize(
    "nvpair, category",
    [
        ("OSPF_AUTH_KEY", "exact"), ("ospfAuthenticationKey", "exact"), ("aclFilter", "exact"), ("ipv4AclIn", "exact"),
        ("eigrpIpv4DistributeListPrefixList", "exact"), ("eigrpIpv6DistributeListPrefixList", "exact"),
        ("macsecKeyChainName", "exact"), ("macsecFallbackKeyChainName", "exact"), ("macsecPolicyName", "exact"),
        ("ipv6LinkLocal", "casefold"), ("HSRP_VIPv6", "casefold"),
        ("OSPF_AREA_ID", "case_irrelevant"), ("privateVlanMapping", "case_irrelevant"),
        ("ospfTag", "unverified"), ("eigrpProcessTag", "unverified"),
    ],
)
def test_each_string_nvpair_has_one_category_on_every_parent(nvpair, category):
    rows = [b for b in table.BINDING_TABLE if b["parent_nvpair"] == nvpair]
    assert rows and {b["string_compare"] for b in rows} == {category}
    for b in rows:
        assert table.string_compare(b["parent_template"], nvpair) == category


def test_lookup_is_qualified_by_parent_and_answers_none_outside_the_registry():
    assert table.string_compare(h.TRUNK, "aclFilter") == "exact"
    assert table.string_compare(h.ROUTED, "aclFilter") is None      # not registered on that parent
    assert table.string_compare(h.TRUNK, "lldpReceive") is None     # registered, not a string
    assert table.string_compare(h.TRUNK, "DESC") is None            # legacy key


# ------------------------------------------------------------------ the finding, fixed
@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("cid", sorted(EXACT))
def test_case_only_change_is_sent_with_the_requested_value(cid, state):
    case = EXACT[cid]
    result, calls = h.run_configs(want_of(case, case[5]), state, have=have_of(case))
    sc = h.split_calls(calls)
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is True and len(sc["updates"]) == 1
    assert sent_values(calls, case[2]) == [case[5]]


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("cid", sorted(EXACT))
def test_exact_repeat_after_the_updated_have_is_a_noop(cid, state):
    case = EXACT[cid]
    _r1, calls1 = h.run_configs(want_of(case, case[5]), state, have=have_of(case))
    have2 = h._payload_as_have(calls1)          # HAVE = what the first run wrote
    assert have2[0]["interfaces"][0]["nvPairs"][case[2]] == case[5]
    result, calls = h.run_configs(want_of(case, case[5]), state, have=have2)
    assert not result.get("failed") and result["changed"] is False and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("cid", sorted(EXACT))
def test_identical_value_is_a_noop(cid, state):
    case = EXACT[cid]
    result, calls = h.run_configs(want_of(case, case[4]), state, have=have_of(case))
    assert not result.get("failed") and result["changed"] is False and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("cid", ["routed-ospf_auth_key", "trunk-acl_filter"])
def test_genuinely_different_value_still_updates(cid, state):
    case = EXACT[cid]
    result, calls = h.run_configs(want_of(case, case[6]), state, have=have_of(case))
    assert not result.get("failed") and len(h.split_calls(calls)["updates"]) == 1
    assert sent_values(calls, case[2]) == [case[6]]


# ------------------------------------------------------------------ controls: legacy normalization survives
@pytest.mark.parametrize("state", STATES)
def test_ipv6_text_case_only_difference_stays_a_noop(state):
    """casefold: IPv6 hex digits are case-insensitive; the HAVE returns them upper-cased."""
    have = h.build_have(h.ROUTED, "ipv6_link_local", "fe80::164:a1")
    have[0]["interfaces"][0]["nvPairs"]["ipv6LinkLocal"] = "FE80::164:A1"
    result, calls = h.run_configs(want_of((h.ROUTED, "ipv6_link_local", "ipv6LinkLocal", {}, "", "", ""), "fe80::164:a1"),
                                  state, have=have)
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("state", STATES)
def test_boolean_wire_in_another_case_stays_a_noop(state):
    have = h.build_have(h.TRUNK, "disable_lldp_receive", True)
    have[0]["interfaces"][0]["nvPairs"]["lldpReceive"] = "True"
    result, calls = h.run_configs([h.cfg_for(h.TRUNK, h.base_for(h.TRUNK, disable_lldp_receive=True))], state, have=have)
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("state", STATES)
def test_enum_wire_in_another_case_stays_a_noop(state):
    have = h.build_have(h.TRUNK, "spanning_tree_port_type", "network", **h.NOFAST)
    have[0]["interfaces"][0]["nvPairs"]["spanningTreePortType"] = "Network"
    prof = h.base_for(h.TRUNK, spanning_tree_port_type="network", **h.NOFAST)
    result, calls = h.run_configs([h.cfg_for(h.TRUNK, prof)], state, have=have)
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("state", STATES)
def test_unverified_process_tag_keeps_the_legacy_comparison(state):
    """'unverified' is a documented limitation, not a decision: whether NX-OS treats a process tag's
    case as significant is not established here, so a case-only tag change stays unsent, as before."""
    have = h.build_have(h.ROUTED, "ospf_tag", "PILOT-OSPF", **h.OSPF_CTX_NO_AREA)
    ctx = dict(h.OSPF_CTX)
    ctx["ospf_tag"] = "pilot-ospf"
    prof = h.base_for(h.ROUTED, **ctx)
    result, calls = h.run_configs([h.cfg_for(h.ROUTED, prof)], state, have=have)
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("cid", ["routed-ospf_auth_key", "trunk-acl_filter"])
def test_capability_disabled_keeps_the_pre_write_refusal(cid):
    case = EXACT[cid]
    result, calls = h.run_configs(want_of(case, case[5]), "merged", have=have_of(case), patch_version=None)
    assert result.get("failed") and h.writes(calls) == []


# ------------------------------------------------------------------ no_log: the key never reaches the output
@pytest.mark.parametrize("state", STATES)
def test_case_only_key_update_keeps_both_keys_out_of_the_emitted_result(state):
    assert h.real_serialiser_is_genuine()
    case = EXACT["routed-ospf_auth_key"]
    out, calls = h.emit_real_result(want_of(case, case[5]), state, have=have_of(case))
    assert sent_values(calls, "OSPF_AUTH_KEY") == [case[5]]          # the update is real ...
    assert case[5] not in out and case[4] not in out                  # ... and neither key is printed
    assert "OSPF_AUTH_KEY" in out or '"changed": true' in out
