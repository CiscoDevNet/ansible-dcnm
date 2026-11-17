"""Automatic withdrawal of BPDU filter and link type on the trunk Ethernet and trunk port-channel parents.

Measured live on int_trunk_host (body 99dc8f0a) and int_port_channel_trunk_host (body 25f2582d): an explicit
BPDUFILTER_ENABLED "no" and LINK_TYPE "auto" removed `spanning-tree bpdufilter <value>` and
`spanning-tree link-type <value>`, and the repeat sent nothing. These four rows now declare that value as their
reset_wire, so replaced and a retained interface of overridden send it when the field is omitted over a stored
non-default value. That automatic reset is new and not tested live. The access, dot1q-tunnel and vPC rows keep no reset.

Every case drives the real main() through helpers/binding_harness. The stored state is the shape of the live
baseline (shut down, BPDU guard "no", no allowed VLAN, jumbo MTU) with both fields non-default, plus a field that has
no reset on the parent, given again explicitly, so its refusal cannot stand in for the result of the route under test.
Values are synthetic.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import BINDING_TABLE
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_by_nvpair

from .helpers import binding_harness as h
from .helpers import role_reset

FIELDS = (
    # (public key, nvPair, stored non-default value, another non-default value, reset wire)
    ("bpdu_filter", "BPDUFILTER_ENABLED", "enable", "disable", "no"),
    ("spanning_tree_link_type", "LINK_TYPE", "point-to-point", "shared", "auto"),
)
KEYS = tuple(f[0] for f in FIELDS)
NVPAIRS = tuple(f[1] for f in FIELDS)
RESET = {f[0]: f[4] for f in FIELDS}
NV = {f[0]: f[1] for f in FIELDS}
PARENTS = (h.TRUNK, h.PC_TRUNK)

# The live baseline's native values, and per parent a stored non-default field that has no reset there.
NATIVE = dict(admin_state=False, bpdu_guard="no", allowed_vlans="none", mtu="jumbo", port_type_fast=True)
NO_RESET = {h.TRUNK: ("enable_errdisable_acl", False), h.PC_TRUNK: ("negotiate_auto", False)}
OMISSIONS = (("bpdu_filter",), ("spanning_tree_link_type",), KEYS)
OMISSION_IDS = ("bpdu_filter", "link_type", "both")


def _stored(parent, **change):
    key, value = NO_RESET[parent]
    prof = dict(NATIVE, **{key: value})
    prof.update({f[0]: f[2] for f in FIELDS})
    prof.update(change)
    return prof


def _want(parent, omit=(), **change):
    w = h.base_for(parent, **_stored(parent, **change))
    for k in omit:
        w.pop(k, None)
    return w


def _have(parent, **nv):
    have = h.build_have(parent, **_stored(parent))
    have[0]["interfaces"][0]["nvPairs"].update(nv)
    return have


def _nv(have):
    return have[0]["interfaces"][0]["nvPairs"]


def _run(parent, state, want, have, check_mode=False):
    """replaced and the others on the named interface; overridden with the interface retained in the config."""
    return h.run_configs([h.cfg_for(parent, want)], state, have, check_mode=check_mode)


def _only(calls):
    s = h.split_calls(calls)
    assert len(s["updates"]) == 1 and len(s["deploys"]) == 1 and s["other"] == [], (
        [(c["method"], c["path"]) for c in h.writes(calls)])
    nv = h.request_nvpairs(calls)
    assert len(nv) == 1, nv
    return nv[0]


def _no_writes(calls):
    return h.writes(calls) == []


def _reported(result):
    out = {}
    for d in h.diff_nvpairs(result):
        out.update(d)
    return out


# ------------------------------------------------------------------ registry
def test_the_four_rows_declare_the_measured_reset():
    for parent in PARENTS:
        for key, nvpair, _v, _o, reset in FIELDS:
            b = resolve_by_nvpair(parent, nvpair)
            assert b["profile_key"] == key and b["reset_wire"] == reset == b["default_template"], (parent, nvpair)
            assert isinstance(b["reset_wire"], str)


def test_no_other_parent_gained_a_spanning_tree_reset():
    """The reset measured on the two trunk parents does not move to access, dot1q-tunnel or vPC."""
    rows = {(b["parent_template"], b["parent_nvpair"]): b for b in BINDING_TABLE
            if b["parent_nvpair"] in NVPAIRS + ("ENABLE_ERRDISABLE_ACL", "ENABLE_ORPHAN_PORT")}
    with_reset = {k for k, b in rows.items() if b.get("reset_wire") is not None}
    assert with_reset == {(p, n) for p in PARENTS for n in NVPAIRS}, sorted(with_reset)
    assert len(rows) == 9 * 2 + 3 + 2
    for p in ("int_dot1q_tunnel_host", "int_port_channel_dot1q_tunnel_host", "int_vpc_dot1q_tunnel"):
        assert rows[(p, "BPDUFILTER_ENABLED")]["default_template"] == "enable", p


# ------------------------------------------------------------------ replaced and overridden omission
@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("omit", OMISSIONS, ids=OMISSION_IDS)
@pytest.mark.parametrize("parent", PARENTS)
def test_omission_sends_exactly_the_reset_and_keeps_every_other_nvpair(parent, omit, state):
    have = _have(parent)
    assert {n: _nv(have)[n] for n in NVPAIRS} == {f[1]: f[2] for f in FIELDS}
    result, calls = _run(parent, state, _want(parent, omit), have)
    assert not result.get("failed"), result.get("msg")
    assert result.get("changed") is True
    sent = _only(calls)
    stored = _nv(have)
    expected = {NV[k]: RESET[k] for k in omit}
    for k, v in sent.items():
        assert v == expected.get(k, stored.get(k)), (k, stored.get(k), v)
    assert set(stored) - set(sent) == set(), sorted(set(stored) - set(sent))
    assert _reported(result) == expected
    # The live baseline's native values travel unchanged.
    assert (sent["ADMIN_STATE"], sent["BPDUGUARD_ENABLED"], sent["ALLOWED_VLANS"], sent["MTU"]) == (
        "false", "no", "none", "jumbo")


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("parent", PARENTS)
def test_the_omission_sends_the_requests_of_the_explicit_reset(parent, state):
    """Live, an explicit no + auto removed both lines on both parents. Omitting both keys over the same stored state
    now sends the same requests."""
    have = _have(parent)
    result, explicit = _run(parent, state, _want(parent, **RESET), have)
    assert not result.get("failed"), result.get("msg")
    result, omitted = _run(parent, state, _want(parent, KEYS), have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(omitted) == h.writes(explicit) != []


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("parent", PARENTS)
def test_check_mode_predicts_the_same_reset_and_writes_nothing(parent, state):
    result, calls = _run(parent, state, _want(parent, KEYS), _have(parent), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert result.get("changed") is True and _no_writes(calls)
    assert _reported(result) == {f[1]: f[4] for f in FIELDS}


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("omit", OMISSIONS, ids=OMISSION_IDS)
@pytest.mark.parametrize("parent", PARENTS)
def test_the_readback_of_the_reset_converges_and_a_reapply_sets_the_values_again(parent, omit, state):
    result, calls = _run(parent, state, _want(parent, omit), _have(parent))
    assert not result.get("failed"), result.get("msg")
    readback = h._payload_as_have(calls)
    result, calls = _run(parent, state, _want(parent, omit), readback)
    assert not result.get("failed"), result.get("msg")
    assert _no_writes(calls) and result.get("changed") is False, "the repeat after the readback wrote"
    result, calls = _run(parent, state, _want(parent), readback)
    assert not result.get("failed"), result.get("msg")
    assert _reported(result) == {NV[k]: f[2] for f in FIELDS for k in omit if f[0] == k}


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("parent", PARENTS)
def test_one_field_omitted_while_the_other_changes(parent, state):
    result, calls = _run(parent, state, _want(parent, ("bpdu_filter",), spanning_tree_link_type="shared"),
                         _have(parent))
    assert not result.get("failed"), result.get("msg")
    sent = _only(calls)
    assert (sent["BPDUFILTER_ENABLED"], sent["LINK_TYPE"]) == ("no", "shared")


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("parent", PARENTS)
def test_omission_over_the_stored_defaults_writes_nothing(parent, state):
    result, calls = _run(parent, state, _want(parent, KEYS), _have(parent, BPDUFILTER_ENABLED="no", LINK_TYPE="auto"))
    assert not result.get("failed"), result.get("msg")
    assert _no_writes(calls) and result.get("changed") is False


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("parent", PARENTS)
def test_a_missing_readback_is_not_withdrawn(parent, state):
    have = _have(parent)
    for n in NVPAIRS:
        del _nv(have)[n]
    result, calls = _run(parent, state, _want(parent, KEYS), have)
    assert not result.get("failed"), result.get("msg")
    assert _no_writes(calls) and result.get("changed") is False


@pytest.mark.parametrize("bad", ["No", "AUTO", "bogus", ""])
@pytest.mark.parametrize("parent", PARENTS)
def test_a_readback_outside_the_choices_fails_closed(parent, bad):
    """Exact, case-sensitive: a stored value outside the template choices is not classified as either value."""
    for key, nvpair, _v, _o, _r in FIELDS:
        result, calls = _run(parent, "replaced", _want(parent, KEYS), _have(parent, **{nvpair: bad}))
        assert result.get("failed") is True and "'%s'" % key in result["msg"], result.get("msg")
        assert _no_writes(calls)


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("parent", PARENTS)
def test_an_omitted_field_without_a_reset_still_refuses_the_whole_request(parent, state):
    key, _value = NO_RESET[parent]
    want = _want(parent, KEYS + (key,))
    result, calls = _run(parent, state, want, _have(parent))
    msg = str(result.get("msg", ""))
    assert result.get("failed") is True, "the request was accepted"
    assert "%s on %s" % (key, parent) in msg and "No configuration or deployment request was sent" in msg, msg
    assert not any(k in msg for k in KEYS), msg
    assert _no_writes(calls)


# ------------------------------------------------------------------ unchanged contracts on the same parents
@pytest.mark.parametrize("parent", PARENTS)
def test_merged_omission_keeps_the_stored_values(parent):
    result, calls = _run(parent, "merged", _want(parent, KEYS, description="changed"), _have(parent))
    assert not result.get("failed"), result.get("msg")
    sent = _only(calls)
    for key, nvpair, value, _o, _r in FIELDS:
        assert sent.get(nvpair, value) == value, (nvpair, sent.get(nvpair))
        assert nvpair not in _reported(result)


@pytest.mark.parametrize("state", ["merged", "replaced", "overridden"])
@pytest.mark.parametrize("parent", PARENTS)
def test_explicit_values_and_the_explicit_reset_are_sent(parent, state):
    have = _have(parent)
    other = {f[0]: f[3] for f in FIELDS}
    result, calls = _run(parent, state, _want(parent, **other), have)
    assert not result.get("failed"), result.get("msg")
    assert _reported(result) == {f[1]: f[3] for f in FIELDS}
    result, calls = _run(parent, state, _want(parent, **RESET), have)
    assert not result.get("failed"), result.get("msg")
    sent = _only(calls)
    assert (sent["BPDUFILTER_ENABLED"], sent["LINK_TYPE"]) == ("no", "auto")
    result, calls = _run(parent, state, _want(parent), have)
    assert not result.get("failed"), result.get("msg")
    assert _no_writes(calls) and result.get("changed") is False


@pytest.mark.parametrize("parent", PARENTS)
def test_query_only_reads(parent):
    result, calls = _run(parent, "query", _want(parent), _have(parent))
    assert not result.get("failed"), result.get("msg")
    assert _no_writes(calls) and result.get("changed") is False


def test_deleting_the_port_channel_removes_it_whatever_the_stored_values():
    result, calls = _run(h.PC_TRUNK, "deleted", _want(h.PC_TRUNK), _have(h.PC_TRUNK))
    assert not result.get("failed"), result.get("msg")
    s = h.split_calls(calls)
    assert s["updates"] == [] and len(s["deploys"]) == 1 and len(s["other"]) == 1
    removal = s["other"][0]
    assert removal["method"] == "DELETE" or "markdelete" in removal["path"], (removal["method"], removal["path"])


@pytest.mark.parametrize("state", ["deleted", "overridden"])
def test_the_leaf_role_default_of_a_physical_trunk_port_sends_the_reset(state):
    """The role default of a leaf port is int_trunk_host itself, so the stored values leave through the reset. A stored
    field without a reset on that parent still refuses the whole reset."""
    result, calls = role_reset.run(state, _have(h.TRUNK, ENABLE_ERRDISABLE_ACL="true"), "leaf")
    assert not result.get("failed"), result.get("msg")
    policies = role_reset.reset_policies(calls)
    assert [p["policy"] for p in policies] == [h.TRUNK]
    sent = policies[0]["interfaces"][0]["nvPairs"]
    assert (sent["BPDUFILTER_ENABLED"], sent["LINK_TYPE"]) == ("no", "auto")
    result, calls = role_reset.run(state, _have(h.TRUNK), "leaf")
    assert result.get("failed") is True and "enable_errdisable_acl" in result["msg"], result.get("msg")
    assert not any(k in result["msg"] for k in KEYS) and _no_writes(calls)


@pytest.mark.parametrize("state", ["deleted", "overridden"])
def test_the_border_role_default_still_drops_the_fields(state):
    """On a border the port becomes int_routed_host; the controller negates the trunk lines (cleared_on_change_to)."""
    result, calls = role_reset.run(state, _have(h.TRUNK), "border")
    assert not result.get("failed"), result.get("msg")
    policies = role_reset.reset_policies(calls)
    assert [p["policy"] for p in policies] == [h.ROUTED]
    assert not set(NVPAIRS) & set(policies[0]["interfaces"][0]["nvPairs"])


@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_the_port_channel_reset_is_sent_on_the_parent_only(state):
    result, calls = _run(h.PC_TRUNK, state, _want(h.PC_TRUNK, KEYS), _have(h.PC_TRUNK))
    assert not result.get("failed"), result.get("msg")
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    assert [p["policy"] for p in found] == [h.PC_TRUNK]


# ------------------------------------------------------------------ parents without a measured reset
UNCHANGED = (
    (h.ACCESS, "enable", "point-to-point"),
    (h.PC_ACCESS, "enable", "point-to-point"),
    (h.ETH_DOT1Q, "disable", "point-to-point"),
    (h.PC_DOT1Q, "disable", "point-to-point"),
    (h.VPC_TRUNK, "enable", "point-to-point"),
    (h.VPC_ACCESS, "enable", "point-to-point"),
    (h.VPC_DOT1Q, "disable", "point-to-point"),
)


@pytest.mark.parametrize("parent,bpdu,link", UNCHANGED, ids=[u[0] for u in UNCHANGED])
def test_a_parent_without_a_measured_reset_still_refuses_the_omission(parent, bpdu, link):
    pkw = {"parent": parent} if parent in h.NON_ETH_PARENTS else {}
    for key, value in (("bpdu_filter", bpdu), ("spanning_tree_link_type", link)):
        have = h.build_have(parent, key, value)
        result, calls = h.run(h.want_omitting(parent, key), "replaced", have, **pkw)
        assert result.get("failed") is True and "%s on %s" % (key, parent) in result["msg"], result.get("msg")
        assert "No configuration or deployment request was sent" in result["msg"]
        assert _no_writes(calls)


@pytest.mark.parametrize("parent", [h.ETH_DOT1Q, h.PC_DOT1Q, h.VPC_DOT1Q])
def test_the_dot1q_default_stays_enable(parent):
    """A dot1q-tunnel port stored at `enable` is at its default; one stored at `no` is refused, never reset."""
    pkw = {"parent": parent} if parent in h.NON_ETH_PARENTS else {}
    have = h.build_have(parent, "bpdu_filter", "enable")
    result, calls = h.run(h.want_omitting(parent, "bpdu_filter"), "replaced", have, **pkw)
    assert not result.get("failed"), result.get("msg")
    assert _no_writes(calls)
    have = h.build_have(parent, "bpdu_filter", "no")
    result, calls = h.run(h.want_omitting(parent, "bpdu_filter"), "replaced", have, **pkw)
    assert result.get("failed") is True and "bpdu_filter on %s" % parent in result["msg"], result.get("msg")
    assert _no_writes(calls)
