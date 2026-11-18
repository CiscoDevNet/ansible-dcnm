"""Automatic withdrawal of LACP, CDP and link type on the dot1q-tunnel port-channel parent.

Measured live on int_port_channel_dot1q_tunnel_host (body b17631cd): an explicit DISABLE_LACP_SUSPEND "false",
LACP_PORT_PRIO "32768", LACP_RATE "normal", CDP_ENABLE "true" and LINK_TYPE "auto" made NDFC deploy
`lacp suspend-individual` and `cdp enable` and negate the other three lines; no line was left, and the repeat sent
nothing. These five rows now declare that value as their reset_wire, so replaced and a retained interface of overridden
send it when the field is omitted over a stored non-default value. That automatic reset is new and not tested live.
The BPDU filter row of this parent, the Ethernet and vPC dot1q-tunnel rows and the native LACP keys of the other
port-channel profiles are unchanged.

Every case drives the real main() through helpers/binding_harness. The stored state is the shape of the live
baseline (shut down, BPDU guard "no", BPDU filter "enable", jumbo MTU, access VLAN 1) with the five fields non-default,
plus a field that has no reset on the parent (negotiate_auto false), given again explicitly, so its refusal cannot
stand in for the result of the route under test. Values are synthetic.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine as engine
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import BINDING_TABLE
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_by_nvpair

from .helpers import binding_harness as h

P = h.PC_DOT1Q
MEMBER = "int_port_channel_dot1q_tunnel_member_11_1"
FIELDS = (
    # (public key, nvPair, stored non-default value, its wire form, reset wire)
    ("disable_lacp_suspend_individual", "DISABLE_LACP_SUSPEND", True, "true", "false"),
    ("lacp_port_priority", "LACP_PORT_PRIO", 100, "100", "32768"),
    ("lacp_rate", "LACP_RATE", "fast", "fast", "normal"),
    ("enable_cdp", "CDP_ENABLE", False, "false", "true"),
    ("spanning_tree_link_type", "LINK_TYPE", "point-to-point", "point-to-point", "auto"),
)
KEYS = tuple(f[0] for f in FIELDS)
NVPAIRS = tuple(f[1] for f in FIELDS)
NV = {f[0]: f[1] for f in FIELDS}
RESET = {f[0]: f[4] for f in FIELDS}
RESET_WIRE = {f[1]: f[4] for f in FIELDS}
STORED_WIRE = {f[1]: f[3] for f in FIELDS}
# The explicit defaults as public input values.
DEFAULTS = dict(disable_lacp_suspend_individual=False, lacp_port_priority=32768, lacp_rate="normal", enable_cdp=True,
                spanning_tree_link_type="auto")
# Where the controller renders each field (registry effect rules, read from the body and seen live).
RENDER = {"DISABLE_LACP_SUSPEND": None, "LACP_PORT_PRIO": MEMBER, "LACP_RATE": MEMBER, "CDP_ENABLE": MEMBER,
          "LINK_TYPE": "inline"}

NATIVE = dict(admin_state=False, bpdu_guard="no", bpdu_filter="enable", mtu="jumbo", port_type_fast=True,
              access_vlan="1")
NO_RESET = ("negotiate_auto", False)
OMISSIONS = tuple((k,) for k in KEYS) + (KEYS,)
OMISSION_IDS = KEYS + ("all_five",)


def _stored(**change):
    prof = dict(NATIVE, **{NO_RESET[0]: NO_RESET[1]})
    prof.update({f[0]: f[2] for f in FIELDS})
    prof.update(change)
    return prof


def _want(omit=(), **change):
    w = h.base_for(P, **_stored(**change))
    for k in omit:
        w.pop(k, None)
    return w


def _have(**nv):
    have = h.build_have(P, **_stored())
    have[0]["interfaces"][0]["nvPairs"].update(nv)
    return have


def _nv(have):
    return have[0]["interfaces"][0]["nvPairs"]


def _run(state, want, have, check_mode=False):
    """replaced and the others on the named port-channel; overridden with the port-channel retained in the config."""
    return h.run_configs([h.cfg_for(P, want)], state, have, check_mode=check_mode)


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


def _refused(result, calls, *named):
    msg = str(result.get("msg", ""))
    assert result.get("failed") is True, "the request was accepted"
    assert "No configuration or deployment request was sent" in msg, msg
    for key in named:
        assert "%s on %s" % (key, P) in msg or "%s," % key in msg, (key, msg)
    assert _no_writes(calls)
    return msg


# ------------------------------------------------------------------ registry
def test_the_five_rows_declare_the_measured_reset_as_a_wire_string():
    for key, nvpair, _v, _w, reset in FIELDS:
        b = resolve_by_nvpair(P, nvpair)
        assert b["profile_key"] == key and b["mechanism"] == "passthrough", nvpair
        assert isinstance(b["reset_wire"], str) and b["reset_wire"] == reset, nvpair
        assert engine.gie_declared_default_wire(b) == reset, nvpair
    # The declared defaults keep their native types; only the reset is a wire string.
    assert resolve_by_nvpair(P, "LACP_PORT_PRIO")["default_template"] == 32768
    assert resolve_by_nvpair(P, "CDP_ENABLE")["default_template"] is True
    assert resolve_by_nvpair(P, "DISABLE_LACP_SUSPEND")["default_template"] is False


def test_the_member_and_inline_effects_are_unchanged():
    """Registry documentation only (the generated table does not carry effect rules): the reset does not move a field
    off the member or the port-channel."""
    import yaml
    path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "tools", "registry", "slices",
                        "registry_slice_port_channel_vpc.yaml")
    with open(path) as f:
        rows = {r["parent_nvpair"]: r for r in yaml.safe_load(f)["bindings"] if r["parent_template"] == P}
    for nvpair, where in RENDER.items():
        assert rows[nvpair]["reset_wire"] == RESET_WIRE[nvpair], nvpair
        rules = rows[nvpair].get("effect_rules") or ()
        effects = [(r["ndfc_effect"], r.get("child_template")) for r in rules]
        if where is None:
            assert effects == [], (nvpair, effects)
        elif where == "inline":
            assert effects == [("inline_config", None)], (nvpair, effects)
        else:
            assert effects == [("child_policy", where)], (nvpair, effects)


def test_no_other_row_of_these_nvpairs_gained_a_reset():
    """The measured values stay on this parent. Each other row keeps the reset state of the parent commit."""
    with_reset = {(b["parent_template"], b["parent_nvpair"]): b["reset_wire"] for b in BINDING_TABLE
                  if b["parent_nvpair"] in NVPAIRS + ("BPDUFILTER_ENABLED",) and b.get("reset_wire") is not None}
    expected = {(P, n): r for n, r in RESET_WIRE.items()}
    expected.update({("int_l3_port_channel", "CDP_ENABLE"): "true", ("int_routed_host", "CDP_ENABLE"): "true",
                     ("int_trunk_host", "BPDUFILTER_ENABLED"): "no", ("int_trunk_host", "LINK_TYPE"): "auto",
                     ("int_port_channel_trunk_host", "BPDUFILTER_ENABLED"): "no",
                     ("int_port_channel_trunk_host", "LINK_TYPE"): "auto"})
    assert with_reset == expected, sorted(with_reset)
    assert "reset_wire" not in resolve_by_nvpair(P, "BPDUFILTER_ENABLED")
    lacp = {b["parent_template"] for b in BINDING_TABLE
            if b["parent_nvpair"] in ("DISABLE_LACP_SUSPEND", "LACP_PORT_PRIO", "LACP_RATE")}
    assert lacp == {P}, sorted(lacp)
    for key in ("disable_lacp_suspend_individual", "lacp_port_priority", "lacp_rate"):
        assert key in engine.GIE_NATIVE_ELSEWHERE_KEYS, key


# ------------------------------------------------------------------ replaced and overridden omission
@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("omit", OMISSIONS, ids=OMISSION_IDS)
def test_omission_sends_exactly_the_reset_and_keeps_every_other_nvpair(omit, state):
    have = _have()
    assert {n: _nv(have)[n] for n in NVPAIRS} == STORED_WIRE
    result, calls = _run(state, _want(omit), have)
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
    assert (sent["ADMIN_STATE"], sent["BPDUGUARD_ENABLED"], sent["BPDUFILTER_ENABLED"], sent["MTU"],
            sent["ACCESS_VLAN"], sent["NEGOTIATE_AUTO"]) == ("false", "no", "enable", "jumbo", "1", "false")


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("omit", OMISSIONS, ids=OMISSION_IDS)
def test_the_omission_sends_the_requests_of_the_explicit_defaults(omit, state):
    """Live, the explicit defaults removed all five lines. Omitting the keys over the same stored state now sends the
    same requests."""
    have = _have()
    result, explicit = _run(state, _want(**{k: DEFAULTS[k] for k in omit}), have)
    assert not result.get("failed"), result.get("msg")
    result, omitted = _run(state, _want(omit), have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(omitted) == h.writes(explicit) != []


@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_check_mode_predicts_the_same_reset_and_writes_nothing(state):
    result, calls = _run(state, _want(KEYS), _have(), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert result.get("changed") is True and _no_writes(calls)
    assert _reported(result) == RESET_WIRE


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("omit", OMISSIONS, ids=OMISSION_IDS)
def test_the_readback_of_the_reset_converges_and_a_reapply_sets_the_values_again(omit, state):
    result, calls = _run(state, _want(omit), _have())
    assert not result.get("failed"), result.get("msg")
    readback = h._payload_as_have(calls)
    result, calls = _run(state, _want(omit), readback)
    assert not result.get("failed"), result.get("msg")
    assert _no_writes(calls) and result.get("changed") is False, "the repeat after the readback wrote"
    result, calls = _run(state, _want(), readback)
    assert not result.get("failed"), result.get("msg")
    assert _reported(result) == {NV[k]: STORED_WIRE[NV[k]] for k in omit}


@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_one_field_omitted_while_two_others_change(state):
    result, calls = _run(state, _want(("enable_cdp",), lacp_port_priority=200, spanning_tree_link_type="shared"),
                         _have())
    assert not result.get("failed"), result.get("msg")
    sent = _only(calls)
    assert {n: sent[n] for n in NVPAIRS} == dict(STORED_WIRE, CDP_ENABLE="true", LACP_PORT_PRIO="200",
                                                 LINK_TYPE="shared")


# ------------------------------------------------------------------ stored encodings and readback
# The controller returns every nvPair as a string; the engine also accepts the native bool and int.
DEFAULT_ENCODINGS = {
    "wire": dict(RESET_WIRE),
    "native": dict(DISABLE_LACP_SUSPEND=False, LACP_PORT_PRIO=32768, LACP_RATE="normal", CDP_ENABLE=True,
                   LINK_TYPE="auto"),
}


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("encoding", sorted(DEFAULT_ENCODINGS))
def test_omission_over_the_stored_defaults_writes_nothing(encoding, state):
    result, calls = _run(state, _want(KEYS), _have(**DEFAULT_ENCODINGS[encoding]))
    assert not result.get("failed"), result.get("msg")
    assert _no_writes(calls) and result.get("changed") is False


@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_a_native_bool_or_int_readback_gets_the_same_string_reset(state):
    """Positive-default booleans and the integer: a native False, True or 100 classifies as the same state as its
    string, and the reset is still the declared string."""
    have = _have(DISABLE_LACP_SUSPEND=True, LACP_PORT_PRIO=100, CDP_ENABLE=False)
    result, calls = _run(state, _want(KEYS), have)
    assert not result.get("failed"), result.get("msg")
    sent = _only(calls)
    assert {n: sent[n] for n in NVPAIRS} == RESET_WIRE
    assert all(isinstance(sent[n], str) for n in NVPAIRS)


@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_a_missing_readback_is_not_withdrawn(state):
    have = _have()
    for n in NVPAIRS:
        del _nv(have)[n]
    result, calls = _run(state, _want(KEYS), have)
    assert not result.get("failed"), result.get("msg")
    assert _no_writes(calls) and result.get("changed") is False


@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_an_empty_boolean_or_integer_readback_is_absence(state):
    """NDFC's "" is no value for a boolean or an integer: nothing to withdraw, and it never produces a reset."""
    result, calls = _run(state, _want(KEYS), _have(DISABLE_LACP_SUSPEND="", LACP_PORT_PRIO="", CDP_ENABLE="",
                                                   LACP_RATE="normal", LINK_TYPE="auto"))
    assert not result.get("failed"), result.get("msg")
    assert _no_writes(calls) and result.get("changed") is False


MALFORMED = (
    ("disable_lacp_suspend_individual", "DISABLE_LACP_SUSPEND", ("True", "FALSE", "yes", "1")),
    ("enable_cdp", "CDP_ENABLE", ("True", "FALSE", "no", "0")),
    ("lacp_port_priority", "LACP_PORT_PRIO", ("abc", "100.0", "-1", " 100", "\uff11\uff10\uff10")),
    ("lacp_rate", "LACP_RATE", ("Fast", "NORMAL", "slow", "")),
    ("spanning_tree_link_type", "LINK_TYPE", ("Auto", "POINT-TO-POINT", "network", "")),
)


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("key,nvpair,bad", MALFORMED, ids=[m[0] for m in MALFORMED])
def test_a_malformed_readback_fails_closed(key, nvpair, bad, state):
    """Exact and case-sensitive: a stored value the engine cannot read is not classified as either value."""
    for value in bad:
        result, calls = _run(state, _want(KEYS), _have(**{nvpair: value}))
        assert result.get("failed") is True and "'%s'" % key in result["msg"], (value, result.get("msg"))
        assert "no change was sent" in result["msg"] and _no_writes(calls), value


# ------------------------------------------------------------------ companions without a reset
@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_an_omitted_field_without_a_reset_still_refuses_the_whole_request(state):
    result, calls = _run(state, _want(KEYS + (NO_RESET[0],)), _have())
    msg = _refused(result, calls, NO_RESET[0])
    assert not any(k in msg for k in KEYS), msg


COMPANIONS = (
    ("bpdu_filter", "disable", "BPDUFILTER_ENABLED"),
    ("bpdu_filter", "no", "BPDUFILTER_ENABLED"),
    ("orphan_port", True, "ENABLE_ORPHAN_PORT"),
)


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("key,value,nvpair", COMPANIONS, ids=["bpdu_filter_disable", "bpdu_filter_no", "orphan_port"])
def test_a_stored_companion_without_a_reset_is_refused_next_to_the_five(key, value, nvpair, state):
    """The BPDU filter keeps its dot1q contract: `enable` is its default and no other value is withdrawn."""
    have = h.build_have(P, **_stored(**{key: value}))
    assert _nv(have)[nvpair] == engine._to_nvpair_wire(value)
    want = _want(KEYS)
    want.pop(key, None)
    result, calls = _run(state, want, have)
    msg = _refused(result, calls, key)
    assert not any(k in msg for k in KEYS), msg


# ------------------------------------------------------------------ unchanged contracts on the same parent
def test_merged_omission_keeps_the_stored_values():
    result, calls = _run("merged", _want(KEYS, description="changed"), _have())
    assert not result.get("failed"), result.get("msg")
    sent = _only(calls)
    for nvpair, wire in STORED_WIRE.items():
        assert sent.get(nvpair, wire) == wire, (nvpair, sent.get(nvpair))
        assert nvpair not in _reported(result)


@pytest.mark.parametrize("state", ["merged", "replaced", "overridden"])
def test_explicit_change_explicit_defaults_and_the_repeat(state):
    """The live sequence on one stored state: a change of two fields, the five explicit defaults, the quiet repeat."""
    have = _have()
    result, calls = _run(state, _want(lacp_port_priority=200, spanning_tree_link_type="shared"), have)
    assert not result.get("failed"), result.get("msg")
    assert _reported(result) == {"LACP_PORT_PRIO": "200", "LINK_TYPE": "shared"}
    result, calls = _run(state, _want(**DEFAULTS), have)
    assert not result.get("failed"), result.get("msg")
    sent = _only(calls)
    assert {n: sent[n] for n in NVPAIRS} == RESET_WIRE
    assert all(isinstance(sent[n], str) for n in NVPAIRS)
    readback = h._payload_as_have(calls)
    result, calls = _run(state, _want(**DEFAULTS), readback)
    assert not result.get("failed"), result.get("msg")
    assert _no_writes(calls) and result.get("changed") is False


@pytest.mark.parametrize("key,value", [("lacp_port_priority", "32768"), ("enable_cdp", "true"),
                                       ("disable_lacp_suspend_individual", "false")])
def test_explicit_input_keeps_its_native_type(key, value):
    """The wire string is the reset; as playbook input the same string is still refused."""
    result, calls = _run("replaced", _want(**{key: value}), _have())
    assert result.get("failed") is True and "'%s' must be a native" % key in result["msg"], result.get("msg")
    assert _no_writes(calls)


@pytest.mark.parametrize("key,value", [("lacp_port_priority", 0), ("lacp_port_priority", 65536),
                                       ("lacp_rate", "slow"), ("spanning_tree_link_type", "network")])
def test_explicit_values_outside_the_bounds_are_refused(key, value):
    result, calls = _run("replaced", _want(**{key: value}), _have())
    assert result.get("failed") is True and "'%s'" % key in result["msg"], result.get("msg")
    assert _no_writes(calls)


def test_query_only_reads():
    result, calls = _run("query", _want(), _have())
    assert not result.get("failed"), result.get("msg")
    assert _no_writes(calls) and result.get("changed") is False


def test_deleting_the_port_channel_removes_it_whatever_the_stored_values():
    result, calls = _run("deleted", _want(), _have())
    assert not result.get("failed"), result.get("msg")
    s = h.split_calls(calls)
    assert s["updates"] == [] and len(s["deploys"]) == 1 and len(s["other"]) == 1
    removal = s["other"][0]
    assert removal["method"] == "DELETE" or "markdelete" in removal["path"], (removal["method"], removal["path"])


@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_the_reset_is_sent_on_the_parent_only(state):
    """The controller copies CDP, priority and rate into the member policy; the module sends the parent only."""
    result, calls = _run(state, _want(KEYS), _have())
    assert not result.get("failed"), result.get("msg")
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    assert [p["policy"] for p in found] == [P]


# ------------------------------------------------------------------ unchanged parents
@pytest.mark.parametrize("state", ["merged", "replaced", "overridden"])
@pytest.mark.parametrize("parent", [h.PC_TRUNK, h.PC_ACCESS, h.VPC_ACCESS])
def test_the_native_lacp_keys_of_the_other_profiles_are_unchanged(parent, state):
    """Native builders: replaced and overridden still write the native defaults with their native types; merged keeps
    the stored values."""
    have = h.build_have(parent, disable_lacp_suspend_individual=True, lacp_port_priority=100, lacp_rate="fast")
    result, calls = h.run_configs([h.cfg_for(parent, h.base_for(parent))], state, have)
    assert not result.get("failed"), result.get("msg")
    if state == "merged":
        assert _no_writes(calls)
        return
    sent = _only(calls)
    assert (sent["DISABLE_LACP_SUSPEND"], sent["LACP_PORT_PRIO"], sent["LACP_RATE"]) == (False, 32768, "normal")


@pytest.mark.parametrize("parent,key,value", [
    (h.ETH_DOT1Q, "spanning_tree_link_type", "point-to-point"),
    (h.VPC_DOT1Q, "spanning_tree_link_type", "point-to-point"),
    (h.ETH_DOT1Q, "bpdu_filter", "disable"),
    (h.VPC_DOT1Q, "bpdu_filter", "disable"),
], ids=["ethernet_link_type", "vpc_link_type", "ethernet_bpdu_filter", "vpc_bpdu_filter"])
def test_the_other_dot1q_parents_still_refuse_the_omission(parent, key, value):
    pkw = {"parent": parent} if parent in h.NON_ETH_PARENTS else {}
    have = h.build_have(parent, key, value)
    result, calls = h.run(h.want_omitting(parent, key), "replaced", have, **pkw)
    assert result.get("failed") is True and "%s on %s" % (key, parent) in result["msg"], result.get("msg")
    assert "No configuration or deployment request was sent" in result["msg"]
    assert _no_writes(calls)
