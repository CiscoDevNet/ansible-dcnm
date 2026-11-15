"""Link, discovery, STP/protection, LACP and dampening bindings added on parents that lacked them.

Every route is driven through the real ``main()`` with the controller doubled at ``dcnm_send``
(``helpers/binding_harness.py``). None of these rows carries a ``reset_wire``: no reset is measured
on these parents, so an authoritative withdrawal of a stored value that differs from the template
default must be refused before any write, and the explicit template default stays the only clear.
The CLI these values produce (inline, on a member, or on a vPC peer's port-channel) is the
controller's and the device's; it is not observable here and is a live-test question.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine as engine

from .helpers.binding_harness import (
    DAMP_FULL_GROUP,
    DAMP_GATE,
    DAMP_WITH_RESTART,
    ETH_DOT1Q,
    NON_ETH_PARENTS,
    PC_DOT1Q,
    PC_L3,
    PC_TRUNK,
    VPC_ACCESS,
    base_for,
    build_have,
    cfg_for,
    diff_nvpairs,
    request_nvpairs,
    run,
    run_configs,
    split_calls,
    want_omitting,
)


def _pkw(parent):
    return {"parent": parent} if parent in NON_ETH_PARENTS else {}


def wire(value):
    return engine._to_nvpair_wire(value)


# (parent, nvPair) -> (profile key, a non-default value, the template default as a public value or None, context)
ROUTES = {
    # Lot a4_1_discovery.
    (ETH_DOT1Q, "lldpTransmit"): ("disable_lldp_transmit", True, False, {}),
    (ETH_DOT1Q, "lldpReceive"): ("disable_lldp_receive", True, False, {}),
    (PC_L3, "CDP_ENABLE"): ("enable_cdp", False, True, {}),
    (PC_L3, "lldpTransmit"): ("disable_lldp_transmit", True, False, {}),
    (PC_L3, "lldpReceive"): ("disable_lldp_receive", True, False, {}),
    (PC_DOT1Q, "CDP_ENABLE"): ("enable_cdp", False, True, {}),
    # Lot a4_2_l3po_dampening. Context keeps each value inside the template rules (the gate, half-life before the
    # thresholds, the full group before restart, restart before the penalty), so the HAVE is a state the controller can hold.
    (PC_L3, "dampening"): ("enable_dampening", True, False, {}),
    (PC_L3, "dampeningHalfLife"): ("dampening_half_life", 5, None, dict(DAMP_GATE)),
    (PC_L3, "dampeningReuse"): ("dampening_reuse", 750, None, {k: v for k, v in DAMP_FULL_GROUP.items() if k != "dampening_reuse"}),
    (PC_L3, "dampeningSuppress"): ("dampening_suppress", 2000, None,
                                   {k: v for k, v in DAMP_FULL_GROUP.items() if k != "dampening_suppress"}),
    (PC_L3, "dampeningMaxSuppress"): ("dampening_max_suppress", 60, None,
                                      {k: v for k, v in DAMP_FULL_GROUP.items() if k != "dampening_max_suppress"}),
    (PC_L3, "dampeningRestart"): ("dampening_restart", True, False, dict(DAMP_FULL_GROUP)),
    (PC_L3, "dampeningRestartPenalty"): ("dampening_restart_penalty", 100, None, dict(DAMP_WITH_RESTART)),
    # Lot a4_3_lacp (registry rows; the vPC access LACP inputs are native and tested below).
    (PC_DOT1Q, "DISABLE_LACP_SUSPEND"): ("disable_lacp_suspend_individual", True, False, {}),
    (PC_DOT1Q, "LACP_PORT_PRIO"): ("lacp_port_priority", 100, 32768, {}),
    (PC_DOT1Q, "LACP_RATE"): ("lacp_rate", "fast", "normal", {}),
}

ITEMS = [(p, n, k, a, d, e) for (p, n), (k, a, d, e) in sorted(ROUTES.items())]
IDS = ["%s::%s" % (p, n) for p, n, _k, _a, _d, _e in ITEMS]
WITH_DEFAULT = [i for i in ITEMS if i[4] is not None]
WITH_DEFAULT_IDS = ["%s::%s" % (p, n) for p, n, _k, _a, _d, _e in WITH_DEFAULT]
AGGREGATES = NON_ETH_PARENTS


def _no_writes(calls):
    s = split_calls(calls)
    return s["updates"] == [] and s["deploys"] == [] and s["other"] == []


def test_every_route_is_a_registered_row_without_a_reset():
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import BINDING_TABLE
    rows = {(b["parent_template"], b["parent_nvpair"]): b for b in BINDING_TABLE}
    for (parent, nvpair), (key, applied, default, _extra) in ROUTES.items():
        b = rows[(parent, nvpair)]
        assert b["profile_key"] == key and b["mechanism"] == "passthrough"
        assert "reset_wire" not in b, (parent, nvpair)
        if default is None:
            assert "default_template" not in b, (parent, nvpair)
        else:
            assert wire(b["default_template"]) == wire(default), (parent, nvpair)
        assert wire(applied) != wire(b.get("default_template", "")), (parent, nvpair)


@pytest.mark.parametrize("parent,nvpair,key,applied,default,extra", ITEMS, ids=IDS)
def test_merged_explicit_value_reaches_the_parent_request_and_the_diff(parent, nvpair, key, applied, default, extra):
    result, calls = run(base_for(parent, **dict(extra, **{key: applied})), "merged", **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    nv = request_nvpairs(calls)
    assert nv and nv[0].get(nvpair) == wire(applied), nv
    assert any(d.get(nvpair) == wire(applied) for d in diff_nvpairs(result))
    # One parent nvPair, never per-peer copies: a vPC pair shares the value.
    assert not any(k.startswith(("PEER1_", "PEER2_")) and k.endswith(nvpair) for k in nv[0])


@pytest.mark.parametrize("parent,nvpair,key,applied,default,extra", ITEMS, ids=IDS)
def test_merged_omission_keeps_the_stored_value(parent, nvpair, key, applied, default, extra):
    have = build_have(parent, key, applied, **extra)
    want = want_omitting(parent, key, **dict(extra, description="changed"))
    result, calls = run(want, "merged", have, **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    nv = request_nvpairs(calls)
    assert nv, "positive control: the description changed, so an update is expected"
    assert nv[0].get(nvpair, wire(applied)) == wire(applied), nv[0].get(nvpair)


@pytest.mark.parametrize("parent,nvpair,key,applied,default,extra", WITH_DEFAULT, ids=WITH_DEFAULT_IDS)
def test_replaced_omission_at_the_template_default_writes_nothing(parent, nvpair, key, applied, default, extra):
    have = build_have(parent, key, default, **extra)
    result, calls = run(want_omitting(parent, key, **extra), "replaced", have, **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    assert _no_writes(calls) and result.get("changed") is False


@pytest.mark.parametrize("parent,nvpair,key,applied,default,extra", ITEMS, ids=IDS)
def test_replaced_omission_of_a_stored_value_is_refused_before_any_write(parent, nvpair, key, applied, default, extra):
    have = build_have(parent, key, applied, **extra)
    result, calls = run(want_omitting(parent, key, **extra), "replaced", have, **_pkw(parent))
    assert result.get("failed") is True
    assert "%s on %s" % (key, parent) in result["msg"], result["msg"]
    assert "No configuration or deployment request was sent" in result["msg"]
    assert _no_writes(calls)


@pytest.mark.parametrize("parent,nvpair,key,applied,default,extra", ITEMS, ids=IDS)
def test_overridden_retained_interface_refuses_the_same_withdrawal(parent, nvpair, key, applied, default, extra):
    have = build_have(parent, key, applied, **extra)
    result, calls = run_configs([cfg_for(parent, want_omitting(parent, key, **extra), deploy=False)], "overridden", have)
    assert result.get("failed") is True
    assert "%s on %s" % (key, parent) in result["msg"], result["msg"]
    assert _no_writes(calls)


@pytest.mark.parametrize("parent,nvpair,key,applied,default,extra", WITH_DEFAULT, ids=WITH_DEFAULT_IDS)
def test_the_explicit_template_default_is_the_clear(parent, nvpair, key, applied, default, extra):
    have = build_have(parent, key, applied, **extra)
    for state in ("merged", "replaced"):
        result, calls = run(base_for(parent, **dict(extra, **{key: default})), state, have, **_pkw(parent))
        assert not result.get("failed"), (state, result.get("msg"))
        nv = request_nvpairs(calls)
        assert nv and nv[0].get(nvpair) == wire(default), (state, nv)


@pytest.mark.parametrize("parent,nvpair,key,applied,default,extra", ITEMS, ids=IDS)
def test_identical_explicit_repeat_writes_and_deploys_nothing(parent, nvpair, key, applied, default, extra):
    have = build_have(parent, key, applied, **extra)
    result, calls = run(base_for(parent, **dict(extra, **{key: applied})), "merged", have, **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    assert _no_writes(calls) and result.get("changed") is False


@pytest.mark.parametrize("parent,nvpair,key,applied,default,extra", ITEMS, ids=IDS)
def test_check_mode_reports_the_change_and_sends_nothing(parent, nvpair, key, applied, default, extra):
    result, calls = run(base_for(parent, **dict(extra, **{key: applied})), "merged", check_mode=True, **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    assert _no_writes(calls) and result.get("changed") is True


@pytest.mark.parametrize("parent,nvpair,key,applied,default,extra", ITEMS, ids=IDS)
def test_query_only_reads(parent, nvpair, key, applied, default, extra):
    have = build_have(parent, key, applied, **extra)
    result, calls = run(base_for(parent, **extra), "query", have, **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    assert _no_writes(calls)


@pytest.mark.parametrize("parent,nvpair,key,applied,default,extra", ITEMS, ids=IDS)
def test_without_an_approved_patch_version_an_explicit_value_is_refused(parent, nvpair, key, applied, default, extra):
    result, calls = run(base_for(parent, **dict(extra, **{key: applied})), "merged", patch_version=None, **_pkw(parent))
    # The refusal names the first registered key of the profile, which may be one of the context keys.
    assert result.get("failed") is True and "requires caller-supplied patch_version" in result["msg"], result.get("msg")
    assert any("'%s'" % k in result["msg"] for k in [key] + list(extra)), result["msg"]
    assert _no_writes(calls)


@pytest.mark.parametrize("parent,nvpair,key,applied,default,extra",
                         [i for i in ITEMS if i[0] in AGGREGATES],
                         ids=[i for i in IDS if i.split("::")[0] in AGGREGATES])
def test_deleting_the_aggregate_removes_it_whatever_the_stored_value(parent, nvpair, key, applied, default, extra):
    have = build_have(parent, key, applied, **extra)
    result, calls = run(base_for(parent, **extra), "deleted", have, **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    assert any(c["method"] == "DELETE" or "markdelete" in c["path"] or "/interface/delete" in c["path"]
               for c in calls if c["method"] != "GET"), [(c["method"], c["path"]) for c in calls]


@pytest.mark.parametrize("role", ["leaf", "border"])
@pytest.mark.parametrize("parent,nvpair,key,applied,default,extra",
                         [i for i in ITEMS if i[0] not in AGGREGATES],
                         ids=[i for i in IDS if i.split("::")[0] not in AGGREGATES])
def test_deleting_the_physical_interface_resets_it_or_names_the_field(parent, nvpair, key, applied, default, extra, role):
    """Physical deleted resets the port to its role default. The stored value either leaves through a reset the
    destination parent has verified, or the run is refused naming the field; it is never silently kept."""
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding
    from .helpers import role_reset
    have = build_have(parent, key, applied, **extra)
    result, calls = role_reset.run("deleted", have, role)
    if result.get("failed"):
        assert key in result["msg"] and parent in result["msg"], result["msg"]
        assert _no_writes(calls)
        return
    policies = role_reset.reset_policies(calls)
    assert len(policies) == 1, "neither a refusal nor exactly one reset request: %r" % (policies,)
    dst = policies[0]["policy"]
    assert dst != parent
    b = resolve_binding(dst, key)
    assert b is not None and b.get("reset_wire") is not None, (dst, key)
    assert policies[0]["interfaces"][0]["nvPairs"].get(nvpair) == b["reset_wire"], (dst, policies[0])


@pytest.mark.parametrize("parent,key,nvpair,value", [
    (PC_TRUNK, "enable_cdp", "CDP_ENABLE", False),
    (VPC_ACCESS, "enable_cdp", "CDP_ENABLE", False),
    (ETH_DOT1Q, "enable_cdp", "CDP_ENABLE", False),
])
def test_the_native_parents_keep_their_native_cdp(parent, key, nvpair, value):
    """enable_cdp stays native where the module already wrote it (GIE_NATIVE_ELSEWHERE_KEYS)."""
    result, calls = run(base_for(parent, **{key: value}), "merged", **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    nv = request_nvpairs(calls)
    assert nv and wire(nv[0].get(nvpair)) == wire(value)
    # The native builder still writes its default when the key is omitted.
    result, calls = run(base_for(parent), "merged", **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    assert wire(request_nvpairs(calls)[0].get(nvpair)) == "true"


def test_a_key_of_this_family_on_a_parent_that_does_not_declare_it_is_refused():
    """disable_lldp_transmit is not declared by the SVI parent; the generic guard refuses it before any read."""
    result, calls = run(base_for("int_vlan", disable_lldp_transmit=True), "merged", parent="int_vlan")
    assert result.get("failed") is True and "disable_lldp_transmit" in result["msg"], result.get("msg")
    assert _no_writes(calls)


# ------------------------------------------------------------------ vPC access LACP (native, lot a4_3_lacp)
VPC_LACP = [
    ("disable_lacp_suspend_individual", "DISABLE_LACP_SUSPEND", True, False),
    ("enable_lacp_vpc_convergence", "ENABLE_LACP_VPC_CONV", True, False),
    ("lacp_port_priority", "LACP_PORT_PRIO", 100, 32768),
    ("lacp_rate", "LACP_RATE", "fast", "normal"),
]
VPC_LACP_IDS = [k for k, _n, _a, _d in VPC_LACP]


def _vpc_have(**values):
    have = build_have(VPC_ACCESS)
    have[0]["interfaces"][0]["nvPairs"].update(values)
    return have


@pytest.mark.parametrize("key,nvpair,applied,default", VPC_LACP, ids=VPC_LACP_IDS)
def test_vpc_access_lacp_explicit_value_reaches_the_request(key, nvpair, applied, default):
    """Before lot a4_3_lacp the access spec dropped these keys and the builder sent the default."""
    result, calls = run(base_for(VPC_ACCESS, **{key: applied}), "merged", parent=VPC_ACCESS)
    assert not result.get("failed"), result.get("msg")
    assert wire(request_nvpairs(calls)[0][nvpair]) == wire(applied)


@pytest.mark.parametrize("key,nvpair,applied,default", VPC_LACP, ids=VPC_LACP_IDS)
def test_vpc_access_lacp_omission_under_merged_keeps_a_stored_non_default(key, nvpair, applied, default):
    """The spec default must not make an omitted key look authored: merged keeps what the controller holds."""
    have = _vpc_have(**{nvpair: wire(applied)})
    result, calls = run(base_for(VPC_ACCESS, peer1_description="changed"), "merged", have, parent=VPC_ACCESS)
    assert not result.get("failed"), result.get("msg")
    nv = request_nvpairs(calls)
    assert nv, "positive control: the description changed"
    assert wire(nv[0][nvpair]) == wire(applied), nv[0][nvpair]


@pytest.mark.parametrize("key,nvpair,applied,default", VPC_LACP, ids=VPC_LACP_IDS)
def test_vpc_access_lacp_omission_under_replaced_sends_the_native_default(key, nvpair, applied, default):
    """Unchanged native contract: replaced writes the builder default for an omitted key, as it did before."""
    have = _vpc_have(**{nvpair: wire(applied)})
    result, calls = run(base_for(VPC_ACCESS), "replaced", have, parent=VPC_ACCESS)
    assert not result.get("failed"), result.get("msg")
    assert wire(request_nvpairs(calls)[0][nvpair]) == wire(default)


def test_vpc_access_lacp_port_priority_is_bounded_before_any_write():
    for bad in (0, 65536):
        result, calls = run(base_for(VPC_ACCESS, lacp_port_priority=bad), "merged", parent=VPC_ACCESS)
        assert result.get("failed") is True and "lacp_port_priority" in result["msg"], result.get("msg")
        assert _no_writes(calls)


@pytest.mark.parametrize("parent", [PC_TRUNK, "int_port_channel_access_host", "int_vpc_trunk_host", "int_vpc_dot1q_tunnel"])
def test_the_native_lacp_profiles_are_unchanged(parent):
    """GIE_NATIVE_ELSEWHERE_KEYS keeps the generic guard off these native parents."""
    result, calls = run(base_for(parent, lacp_rate="fast", lacp_port_priority=100, disable_lacp_suspend_individual=True),
                        "merged", parent=parent)
    assert not result.get("failed"), result.get("msg")
    nv = request_nvpairs(calls)[0]
    assert (nv["LACP_RATE"], wire(nv["LACP_PORT_PRIO"]), wire(nv["DISABLE_LACP_SUSPEND"])) == ("fast", "100", "true")
