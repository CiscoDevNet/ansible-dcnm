"""Omission contract of the routed port-channel controls, MACsec, IPv6, redirects, PFC, QoS and NetFlow routes.

Every route is driven through the real ``main()`` with the controller doubled at ``dcnm_send``
(``helpers/binding_harness.py``). A reset measured on another parent does not establish a route. The routes in
``MEASURED`` carry a ``reset_wire`` because their explicit withdrawal was measured live on the routed port-channel
itself; their omission contract is in ``test_binding_l3po_measured_resets.py``. For every other route, under
``replaced``, a retained interface of ``overridden`` and the role-default reset of a physical port, an omitted value
that differs from the template default is refused before any write. An explicit value, including the template default,
is sent as requested; sending a default does not prove that the device line is removed. The IPv6 address and prefix
are a pair and are covered in ``test_binding_l3po_ipv6_redirects.py``.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine as engine

from .helpers.binding_harness import (
    ACCESS,
    ETH_DOT1Q,
    MACSEC_FB_CTX,
    MACSEC_NAMES,
    NON_ETH_PARENTS,
    PC_ACCESS,
    PC_DOT1Q,
    PC_L3,
    PC_TRUNK,
    QOS,
    QUEUE,
    ROUTED,
    SUBIF,
    SVI,
    TRUNK,
    VPC_ACCESS,
    VPC_DOT1Q,
    VPC_PARENTS,
    VPC_TRUNK,
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

NETFLOW_MONITOR_ONLY = {"netflow_monitor": "PILOT-FM"}
NETFLOW_ENABLED = {"enable_netflow": True}
NETFLOW_ON = {"enable_netflow": True, "netflow_monitor": "PILOT-FM"}

# (parent, nvPair) -> (profile key, a non-default value, the neutral HAVE wire, context). The neutral wire is the
# declared template default, or "" (the controller's "no value") where the template declares none. The context is sent
# and stored with the value and keeps the gate of a dependent row on, so the omission is not inert.
ROUTES = {
    # rp1: BFD echo, ARP timeout and inbound ACL.
    (PC_L3, "bfdEcho"): ("disable_bfd_echo", True, "false", {}),
    (PC_L3, "arpTimeout"): ("arp_timeout", 900, "", {}),
    (PC_L3, "ipv4AclIn"): ("ipv4_acl_in", "PILOT-ACL", "", {}),
    # rp2: MACsec. The names are required while the policy is enabled.
    (PC_L3, "macsecInterfacePolicy"): ("enable_macsec_interface_policy", True, "false", dict(MACSEC_NAMES)),
    (PC_L3, "macsecKeyChainName"): ("macsec_key_chain_name", "PILOT-KC", "",
                                    {"enable_macsec_interface_policy": True, "macsec_policy_name": "PILOT-POL"}),
    (PC_L3, "macsecPolicyName"): ("macsec_policy_name", "PILOT-POL", "",
                                  {"enable_macsec_interface_policy": True, "macsec_key_chain_name": "PILOT-KC"}),
    (PC_L3, "macsecFallbackKeyChainName"): ("macsec_fallback_key_chain_name", "PILOT-FBKC", "", dict(MACSEC_FB_CTX)),
    # rp3: link-local, ND suppress-RA and the three redirect options. The split options declare no default.
    (PC_L3, "ipv6LinkLocal"): ("ipv6_link_local", "fe80::31", "", {}),
    (PC_L3, "ipv6NdSuppressRa"): ("ipv6_nd_suppress_ra", True, "false", {}),
    (PC_L3, "DISABLE_IP_REDIRECTS"): ("disable_ip_redirects", True, "false", {}),
    (PC_L3, "ipv4Redirects"): ("disable_ipv4_redirects", True, "", {}),
    (PC_L3, "ipv6Redirects"): ("disable_ipv6_redirects", True, "", {}),
    # rp4: priority flow control, the Ethernet dot1q-tunnel QoS and queuing policies, and the routed port-channel
    # policy statistics.
    (ROUTED, "ENABLE_PFC"): ("enable_pfc", True, "false", {}),
    (ETH_DOT1Q, "ENABLE_PFC"): ("enable_pfc", True, "false", {}),
    (PC_L3, "ENABLE_PFC"): ("enable_pfc", True, "false", {}),
    (PC_DOT1Q, "ENABLE_PFC"): ("enable_pfc", True, "false", {}),
    (VPC_ACCESS, "ENABLE_PFC"): ("enable_pfc", True, "false", {}),
    (VPC_TRUNK, "ENABLE_PFC"): ("enable_pfc", True, "false", {}),
    (VPC_DOT1Q, "ENABLE_PFC"): ("enable_pfc", True, "false", {}),
    (ETH_DOT1Q, "ENABLE_QOS"): ("enable_qos", True, "false", {"qos_policy": "pilot_qos"}),
    (ETH_DOT1Q, "QOS_POLICY"): ("qos_policy", "pilot_qos", "", {"enable_qos": True}),
    (ETH_DOT1Q, "QUEUING_POLICY"): ("queuing_policy", "pilot_queue", "", {}),
    (PC_L3, "qosStatsSuppressed"): ("disable_qos_stats", True, "false", dict(QOS)),
    (PC_L3, "queuingStats"): ("disable_queuing_stats", True, "false", dict(QUEUE)),
}
# rp5: NetFlow on twelve parents, and the sampler on the SVI.
NETFLOW_PARENTS = (TRUNK, ACCESS, ROUTED, ETH_DOT1Q, PC_L3, SUBIF, PC_ACCESS, PC_TRUNK, PC_DOT1Q, VPC_ACCESS, VPC_TRUNK,
                   VPC_DOT1Q)
for _p in NETFLOW_PARENTS:
    ROUTES[(_p, "ENABLE_NETFLOW")] = ("enable_netflow", True, "false", dict(NETFLOW_MONITOR_ONLY))
    ROUTES[(_p, "NETFLOW_MONITOR")] = ("netflow_monitor", "PILOT-FM", "", dict(NETFLOW_ENABLED))
    ROUTES[(_p, "NETFLOW_SAMPLER")] = ("netflow_sampler", "PILOT-FS", "", dict(NETFLOW_ON))
ROUTES[(SVI, "NETFLOW_SAMPLER")] = ("netflow_sampler", "PILOT-FS", "", dict(NETFLOW_ON))
PAIR = ((PC_L3, "IPv6"), (PC_L3, "IPv6_PREFIX"))

# Routes with a reset_wire, measured live on this parent, and that wire value.
MEASURED = {
    (PC_L3, "bfdEcho"): "false",
    (PC_L3, "ipv4AclIn"): "",
    (PC_L3, "ipv6LinkLocal"): "",
    (PC_L3, "ipv6NdSuppressRa"): "false",
    (PC_L3, "ipv4Redirects"): "false",
    (PC_L3, "ipv6Redirects"): "false",
}

ITEMS = [(p, n, k, a, z, e) for (p, n), (k, a, z, e) in sorted(ROUTES.items())]
IDS = ["%s::%s" % (p, n) for p, n, _k, _a, _z, _e in ITEMS]
# The routes whose omission of a stored non-default value is refused.
REFUSED = [i for i in ITEMS if (i[0], i[1]) not in MEASURED]
REFUSED_IDS = ["%s::%s" % (p, n) for p, n, _k, _a, _z, _e in REFUSED]
# Rows whose neutral value is the declared template default; the others are cleared with "" where the type allows it.
WITH_DEFAULT = [i for i in ITEMS if i[4] != ""]
WITH_DEFAULT_IDS = ["%s::%s" % (p, n) for p, n, _k, _a, _z, _e in WITH_DEFAULT]
STRINGS = [i for i in ITEMS if isinstance(i[3], str)]
STRINGS_IDS = ["%s::%s" % (p, n) for p, n, _k, _a, _z, _e in STRINGS]
AGGREGATES = NON_ETH_PARENTS
BAD_HAVE = {bool: "maybe", int: "not-a-number"}


def _pkw(parent):
    return {"parent": parent} if parent in NON_ETH_PARENTS else {}


def wire(value):
    return engine._to_nvpair_wire(value)


def _no_writes(calls):
    s = split_calls(calls)
    return s["updates"] == [] and s["deploys"] == [] and s["other"] == []


def _changed(parent):
    return {"peer1_description": "changed"} if parent in VPC_PARENTS else {"description": "changed"}


def test_only_the_measured_routes_carry_a_reset():
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import BINDING_TABLE
    rows = {(b["parent_template"], b["parent_nvpair"]): b for b in BINDING_TABLE}
    assert len(ROUTES) + len(PAIR) == 63
    assert set(MEASURED) <= set(ROUTES)
    for identity in list(ROUTES) + list(PAIR):
        if identity in MEASURED:
            assert rows[identity]["reset_wire"] == MEASURED[identity], identity
        else:
            assert "reset_wire" not in rows[identity], identity
    for (parent, nvpair), (key, applied, neutral, _extra) in ROUTES.items():
        b = rows[(parent, nvpair)]
        assert b["profile_key"] == key and b["mechanism"] == "passthrough"
        assert engine.gie_declared_default_wire(b) == (neutral or None), (parent, nvpair)
        assert wire(applied) != neutral, (parent, nvpair)
    # 273 resets on the parent commit, plus the nine measured on the routed port-channel (six here, three discovery rows),
    # the four trunk spanning-tree resets (test_binding_trunk_stp_resets.py) and the five dot1q-tunnel port-channel
    # resets (test_binding_dot1q_po_resets.py).
    assert sum(1 for b in BINDING_TABLE if "reset_wire" in b) == 273 + 9 + 4 + 5


@pytest.mark.parametrize("parent,nvpair,key,applied,neutral,extra", ITEMS, ids=IDS)
def test_merged_explicit_value_reaches_the_parent_request_and_the_diff(parent, nvpair, key, applied, neutral, extra):
    result, calls = run(base_for(parent, **dict(extra, **{key: applied})), "merged", **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    nv = request_nvpairs(calls)
    assert nv and nv[0].get(nvpair) == wire(applied), nv
    assert any(d.get(nvpair) == wire(applied) for d in diff_nvpairs(result))


@pytest.mark.parametrize("parent,nvpair,key,applied,neutral,extra", ITEMS, ids=IDS)
def test_merged_omission_keeps_the_stored_value(parent, nvpair, key, applied, neutral, extra):
    have = build_have(parent, key, applied, **extra)
    result, calls = run(want_omitting(parent, key, **dict(extra, **_changed(parent))), "merged", have, **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    nv = request_nvpairs(calls)
    assert nv, "positive control: the description changed, so an update is expected"
    assert nv[0].get(nvpair, wire(applied)) == wire(applied), nv[0].get(nvpair)


@pytest.mark.parametrize("parent,nvpair,key,applied,neutral,extra", ITEMS, ids=IDS)
def test_replaced_omission_at_the_neutral_value_writes_nothing(parent, nvpair, key, applied, neutral, extra):
    if nvpair == "NETFLOW_MONITOR":
        # An empty monitor with NetFlow on is refused as required; the neutral state has NetFlow off.
        extra = {"enable_netflow": False}
    have = build_have(parent, **extra)
    have[0]["interfaces"][0]["nvPairs"][nvpair] = neutral
    result, calls = run(want_omitting(parent, key, **extra), "replaced", have, **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    assert _no_writes(calls) and result.get("changed") is False


@pytest.mark.parametrize("parent,nvpair,key,applied,neutral,extra", ITEMS, ids=IDS)
def test_replaced_omission_without_the_nvpair_in_have_writes_nothing(parent, nvpair, key, applied, neutral, extra):
    """A missing readback is nothing to withdraw; no value is invented for it."""
    have = build_have(parent, key, applied, **extra)
    del have[0]["interfaces"][0]["nvPairs"][nvpair]
    result, calls = run(want_omitting(parent, key, **extra), "replaced", have, **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    assert not any(nvpair in nv for nv in request_nvpairs(calls))


@pytest.mark.parametrize("parent,nvpair,key,applied,neutral,extra", REFUSED, ids=REFUSED_IDS)
def test_replaced_omission_of_a_stored_value_is_refused_before_any_write(parent, nvpair, key, applied, neutral, extra):
    have = build_have(parent, key, applied, **extra)
    result, calls = run(want_omitting(parent, key, **extra), "replaced", have, **_pkw(parent))
    assert result.get("failed") is True
    assert "%s on %s" % (key, parent) in result["msg"], result["msg"]
    assert "No configuration or deployment request was sent" in result["msg"]
    if not isinstance(applied, bool):
        assert str(applied) not in result["msg"], "the refusal named the value"
    assert _no_writes(calls)


@pytest.mark.parametrize("parent,nvpair,key,applied,neutral,extra", REFUSED, ids=REFUSED_IDS)
def test_overridden_retained_interface_refuses_the_same_withdrawal(parent, nvpair, key, applied, neutral, extra):
    have = build_have(parent, key, applied, **extra)
    result, calls = run_configs([cfg_for(parent, want_omitting(parent, key, **extra), deploy=False)], "overridden", have)
    assert result.get("failed") is True
    assert "%s on %s" % (key, parent) in result["msg"], result["msg"]
    assert _no_writes(calls)


@pytest.mark.parametrize("parent,nvpair,key,applied,neutral,extra", REFUSED, ids=REFUSED_IDS)
def test_check_mode_refuses_the_same_withdrawal(parent, nvpair, key, applied, neutral, extra):
    have = build_have(parent, key, applied, **extra)
    result, calls = run(want_omitting(parent, key, **extra), "replaced", have, check_mode=True, **_pkw(parent))
    assert result.get("failed") is True
    assert _no_writes(calls)


@pytest.mark.parametrize("parent,nvpair,key,applied,neutral,extra", WITH_DEFAULT, ids=WITH_DEFAULT_IDS)
def test_the_explicit_template_default_is_sent_as_requested(parent, nvpair, key, applied, neutral, extra):
    have = build_have(parent, key, applied, **extra)
    for state in ("merged", "replaced"):
        result, calls = run(base_for(parent, **dict(extra, **{key: False})), state, have, **_pkw(parent))
        assert not result.get("failed"), (state, result.get("msg"))
        nv = request_nvpairs(calls)
        assert nv and nv[0].get(nvpair) == neutral, (state, nv)


@pytest.mark.parametrize("parent,nvpair,key,applied,neutral,extra", STRINGS, ids=STRINGS_IDS)
def test_an_explicit_empty_string_is_sent_as_requested(parent, nvpair, key, applied, neutral, extra):
    """The empty string is the template's "no value" for these names; it is sent, and the device result is a live
    question. A gate-dependent name is cleared with its gate off where the template requires it while on."""
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding
    ctx = dict(extra)
    gate = (resolve_binding(parent, key) or {}).get("inert_when")
    if gate and gate.get("required"):
        ctx["enable_netflow"] = False
    if key in ("macsec_key_chain_name", "macsec_policy_name"):
        ctx["enable_macsec_interface_policy"] = False
    have = build_have(parent, key, applied, **extra)
    result, calls = run(base_for(parent, **dict(ctx, **{key: ""})), "merged", have, **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    nv = request_nvpairs(calls)
    assert nv and nv[0].get(nvpair) == "", nv


@pytest.mark.parametrize("parent,nvpair,key,applied,neutral,extra", ITEMS, ids=IDS)
def test_identical_explicit_repeat_writes_and_deploys_nothing(parent, nvpair, key, applied, neutral, extra):
    have = build_have(parent, key, applied, **extra)
    result, calls = run(base_for(parent, **dict(extra, **{key: applied})), "merged", have, **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    assert _no_writes(calls) and result.get("changed") is False


@pytest.mark.parametrize("parent,nvpair,key,applied,neutral,extra",
                         [i for i in ITEMS if type(i[3]) in BAD_HAVE],
                         ids=[i for i, it in zip(IDS, ITEMS) if type(it[3]) in BAD_HAVE])
def test_an_unreadable_stored_value_fails_closed(parent, nvpair, key, applied, neutral, extra):
    """A wrong readback is refused before any write, under merged as under replaced."""
    have = build_have(parent, key, applied, **extra)
    bad = BAD_HAVE[type(applied)]
    have[0]["interfaces"][0]["nvPairs"][nvpair] = bad
    for state in ("merged", "replaced"):
        result, calls = run(want_omitting(parent, key, **dict(extra, **_changed(parent))), state, have,
                            **_pkw(parent))
        assert result.get("failed") is True, state
        assert bad not in result["msg"], result["msg"]
        assert _no_writes(calls), state


@pytest.mark.parametrize("parent,nvpair,key,applied,neutral,extra", ITEMS, ids=IDS)
def test_query_only_reads(parent, nvpair, key, applied, neutral, extra):
    have = build_have(parent, key, applied, **extra)
    result, calls = run(base_for(parent, **extra), "query", have, **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    assert _no_writes(calls)


@pytest.mark.parametrize("parent,nvpair,key,applied,neutral,extra",
                         [i for i in ITEMS if i[0] in AGGREGATES],
                         ids=[i for i in IDS if i.split("::")[0] in AGGREGATES])
def test_deleting_the_aggregate_removes_it_whatever_the_stored_value(parent, nvpair, key, applied, neutral, extra):
    have = build_have(parent, key, applied, **extra)
    result, calls = run(base_for(parent, **extra), "deleted", have, **_pkw(parent))
    assert not result.get("failed"), result.get("msg")
    assert any(c["method"] == "DELETE" or "markdelete" in c["path"] or "/interface/delete" in c["path"]
               for c in calls if c["method"] != "GET"), [(c["method"], c["path"]) for c in calls]


@pytest.mark.parametrize("role", ["leaf", "border"])
@pytest.mark.parametrize("parent,nvpair,key,applied,neutral,extra",
                         [i for i in ITEMS if i[0] not in AGGREGATES],
                         ids=[i for i in IDS if i.split("::")[0] not in AGGREGATES])
def test_deleting_the_physical_interface_resets_it_or_names_the_field(parent, nvpair, key, applied, neutral, extra, role):
    """Physical deleted resets the port to its role default. The stored value leaves through a reset the destination
    parent has verified or a declared policy-change rule, or the run is refused naming the field; it is never kept
    while the reset is reported."""
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
    assert dst != parent, "a same-parent reset of a row without reset_wire must be refused"
    sent = policies[0]["interfaces"][0]["nvPairs"]
    b = resolve_binding(dst, key)
    if b is not None and b.get("reset_wire") is not None:
        assert sent.get(nvpair) == b["reset_wire"], (dst, sent.get(nvpair))
    else:
        src = resolve_binding(parent, key)
        assert src.get("dropped_on_policy_change") or dst in (src.get("cleared_on_change_to") or ()), (
            parent, dst, key)
        assert sent.get(nvpair) in (None, "", "false"), (dst, sent.get(nvpair))
