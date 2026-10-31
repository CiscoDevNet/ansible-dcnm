"""Companion controls of the three PVLAN parents.

NOT LIVE TESTED. Real main() through the existing Ethernet, port-channel and vPC PVLAN harnesses.
Labels:
  [SRC]       the installed templates (Po HOST 476-560, MEMBER 171-195, vPC HOST 630-860, POVPC 277-321,
              Ethernet 379-386);
  SYNTHETIC   every preview carrying a companion line: a measured or harness preview plus the template line.
              No PVLAN interface with a non-default companion was observed on a controller or a switch;
  INFERRED    the registry resets of the PVLAN parents (siblings' reset_wire), and the NX-OS positive form that withdraws a
              negative-form line (`lldp transmit` for `no lldp transmit`).
The assertions read the module's real results: the sent nvPairs, the reported diff, the request order and, for the vPC, the gate
records per site.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import registered_profile_keys
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_ENABLED_PATCH_VERSIONS

from .test_dcnm_intf_pvlan_harness import IF7, PREVIEW_MARK, PVLAN, authority, preview, pvlan_item, run
from .test_dcnm_intf_pvlan_lifecycle import TPROM_A11, ctrl

SMU = sorted(GIE_ENABLED_PATCH_VERSIONS)[0]
APPROVED = [pytest.param(SMU, id="smu"), pytest.param("4.4.1", id="nd441")]
REFUSED = [
    pytest.param(None, id="absent"),
    pytest.param("4.3.1.0175006010", id="unapproved"),
    pytest.param("4.4", id="malformed"),
    pytest.param("4.3.9", id="below-nd441"),
]


# ================================================================== registry and allowlists (pure)
def test_each_parent_registers_exactly_its_a0_registry_rows_with_the_sibling_contract():
    expected = {
        P.PVLAN_POLICY: {"disable_lldp_transmit": ("lldpTransmit", "boolean", "false"), "disable_lldp_receive": ("lldpReceive", "boolean", "false")},
        P.PO_HOST_POLICY: {
            "disable_lldp_transmit": ("lldpTransmit", "boolean", "false"),
            "disable_lldp_receive": ("lldpReceive", "boolean", "false"),
            "spanning_tree_port_type": ("spanningTreePortType", "enum", "no"),
            "disable_queuing_stats": ("queuingStats", "boolean", "false"),
        },
        P.VPC_HOST_POLICY: {
            "disable_lldp_transmit": ("lldpTransmit", "boolean", "false"),
            "disable_lldp_receive": ("lldpReceive", "boolean", "false"),
            "spanning_tree_port_type": ("spanningTreePortType", "enum", "no"),
            "disable_queuing_stats": ("queuingStats", "boolean", "false"),
            "acl_filter": ("aclFilter", "string", ""),
            # The sibling vPC parents' disable_qos_stats (reset inferred on the PVLAN parent)
            "disable_qos_stats": ("qosStatsSuppressed", "boolean", "false"),
        },
    }
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding

    for policy, rows in expected.items():
        assert registered_profile_keys(policy) == set(rows), policy
        for key, (nvp, typ, reset) in rows.items():
            b = resolve_binding(policy, key)
            assert (b["parent_nvpair"], b["type"], b["reset_wire"], b["min_ndfc_version"]) == (nvp, typ, reset, "12.6.0.267")
            assert b["mechanism"] == "passthrough" and b["no_log"] is False
    # Ingress QoS of the vPC is public now (native enable_qos/qos_policy + the registry disable_qos_stats); the port-channel
    # PVLAN parent still has none (its template declares no ingress QoS).
    assert "disable_qos_stats" in registered_profile_keys(P.VPC_HOST_POLICY)
    assert set(("enable_qos", "qos_policy")) <= P.VPC_PROFILE_KEYS
    assert not set(("enable_qos", "qos_policy", "disable_qos_stats")) & P.PO_PROFILE_KEYS


def test_allowlists_carry_the_native_and_registry_companions_and_nothing_deferred():
    assert P.REGISTRY_KEYS <= P.PROFILE_KEYS
    po_native = set(k for k, _n, _t in P.PO_NATIVE_COMPANIONS)
    vpc_native = set(k for k, _n, _t in P.VPC_NATIVE_COMPANIONS)
    assert po_native == {
        "bpdu_guard",
        "port_type_fast",
        "mtu",
        "copy_description",
        "enable_cdp",
        "orphan_port",
        "duplex",
        "queuing_policy",
        "disable_lacp_suspend_individual",
        "lacp_port_priority",
        "lacp_rate",
        "speed",  # RC1
    }
    assert vpc_native == {
        "bpdu_guard",
        "port_type_fast",
        "mtu",
        "copy_description",
        "enable_cdp",
        "duplex",
        "enable_pfc",
        "queuing_policy",
        "disable_lacp_suspend_individual",
        "enable_lacp_vpc_convergence",
        "lacp_port_priority",
        "lacp_rate",
        "speed",  # RC1
        "enable_qos",  # ingress QoS
        "qos_policy",  # ingress QoS
    }
    assert po_native | P.PO_REGISTRY_KEYS <= P.PO_PROFILE_KEYS and vpc_native | P.VPC_REGISTRY_KEYS <= P.VPC_PROFILE_KEYS
    # RC1: speed (both parents), cmds (port-channel) and peer1_cmds/peer2_cmds (vPC) are modeled now; QoS of the parents stays deferred.
    assert "cmds" in P.PO_PROFILE_KEYS and "cmds" not in P.VPC_PROFILE_KEYS
    assert set(("peer1_cmds", "peer2_cmds")) <= P.VPC_PROFILE_KEYS and not set(("peer1_cmds", "peer2_cmds")) & P.PO_PROFILE_KEYS
    # Ingress QoS is public on the vPC only.
    for key in ("enable_qos", "qos_policy", "disable_qos_stats"):
        assert key not in P.PO_PROFILE_KEYS and key in P.VPC_PROFILE_KEYS, key
    # one owner per nvPair: no nvPair is both native and registry on the same parent
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding

    for policy, table, keys in (
        (P.PO_HOST_POLICY, P.PO_NATIVE_COMPANIONS, P.PO_REGISTRY_KEYS),
        (P.VPC_HOST_POLICY, P.VPC_NATIVE_COMPANIONS, P.VPC_REGISTRY_KEYS),
    ):
        reg = set(resolve_binding(policy, k)["parent_nvpair"] for k in keys)
        assert not reg & set(n for _k, n, _t in table), policy


@pytest.mark.parametrize("fn,ifname", [(P.po_not_implemented, None), (P.vpc_not_implemented, "vpc10")])
@pytest.mark.parametrize(
    "key,value,needle",
    [
        ("bpdu_guard", "yes", "bpdu_guard must be"),
        ("port_type_fast", "true", "port_type_fast must be a boolean"),
        ("mtu", "9216", "mtu must be"),
        ("duplex", "FULL", "duplex must be"),
        ("lacp_rate", "slow", "lacp_rate must be"),
        ("lacp_port_priority", 0, "lacp_port_priority must be an integer 1-65535"),
        ("lacp_port_priority", 65536, "lacp_port_priority must be an integer 1-65535"),
        ("lacp_port_priority", True, "lacp_port_priority must be an integer 1-65535"),
        ("lacp_port_priority", "100", "lacp_port_priority must be an integer 1-65535"),
        ("queuing_policy", "two words", "queuing_policy must be one policy-map name"),
        ("disable_lldp_transmit", "true", "disable_lldp_transmit"),
        ("spanning_tree_port_type", "edge", "spanning_tree_port_type"),
        ("disable_queuing_stats", 1, "disable_queuing_stats"),
    ],
)
def test_raw_companion_values_outside_the_template_contract_are_refused(fn, ifname, key, value, needle):
    base = (
        {"mode": "pvlan", "pvlan_mode": "host", "members": ["Ethernet1/7"]}
        if ifname is None
        else {"mode": "pvlan", "pvlan_mode": "host", "peer1_pcid": 10, "peer2_pcid": 10}
    )
    base[key] = value
    reasons = fn(base) if ifname is None else fn(base, ifname)
    assert any(needle in r for r in reasons), reasons


def test_vpc_only_and_po_only_companions_stay_on_their_parent():
    assert any("enable_pfc" in r for r in P.po_not_implemented({"mode": "pvlan", "pvlan_mode": "host", "enable_pfc": True}))
    assert any(
        "orphan_port" in r
        for r in P.vpc_not_implemented({"mode": "pvlan", "pvlan_mode": "host", "peer1_pcid": 10, "peer2_pcid": 10, "orphan_port": True}, "vpc10")
    )
    assert any("acl_filter" in r for r in P.po_not_implemented({"mode": "pvlan", "pvlan_mode": "host", "acl_filter": "A"}))


def test_template_rules_on_the_resulting_state_are_checked_before_any_write():
    nv = dict(P.PO_TEMPLATE_DEFAULTS)
    assert P.companion_state_problems(dict(nv, spanningTreePortType="network"), {})[0].startswith(
        "spanning_tree_port_type 'network' is rejected by the template while port_type_fast is true"
    )
    assert P.companion_state_problems(dict(nv, spanningTreePortType="network", PORTTYPE_FAST_ENABLED="false"), {}) == []
    assert "disable_queuing_stats true only takes effect" in P.companion_state_problems(nv, {"disable_queuing_stats": True})[0]
    assert P.companion_state_problems(dict(nv, QUEUING_POLICY="Q"), {"disable_queuing_stats": True}) == []
    assert P.companion_state_problems(nv, {"disable_queuing_stats": False}) == []


def test_lacp_rate_change_needs_the_member_admin_down_and_is_never_forced():
    up = {"LACP_RATE": "fast", "ADMIN_STATE": "true"}
    down = {"LACP_RATE": "fast", "ADMIN_STATE": "false"}
    assert P.member_lacp_rate_problems("Ethernet1/7", {"LACP_RATE": "normal"}, up, True)
    assert P.member_lacp_rate_problems("Ethernet1/7", {"LACP_RATE": "normal"}, down, True) == []
    assert P.member_lacp_rate_problems("Ethernet1/7", {"LACP_RATE": "fast"}, up, True) == []  # unchanged
    assert P.member_lacp_rate_problems("Ethernet1/7", {"ADMIN_STATE": "true"}, up, False)  # joining member, first rate fast
    assert P.member_lacp_rate_problems("Ethernet1/7", {}, {"LACP_RATE": "normal", "ADMIN_STATE": "true"}, False) == []


def test_withdrawal_of_a_negative_form_line_accepts_only_its_positive_form():
    pre = P.Model({"switchport", "no lldp transmit", "no shutdown"}, None, (), True)
    post = P.Model({"switchport", "no shutdown"}, None, (), True)
    assert P.validate_transition(["lldp transmit"], pre, post) == []
    assert P.validate_transition(["no no lldp transmit"], pre, post) == []
    assert P.validate_transition([], pre, post) == ["withdrawal of 'no lldp transmit' is absent from the pending"]
    # not owned before -> not a withdrawal
    assert P.validate_transition(["lldp transmit"], post, post) == ["unmodeled command 'lldp transmit'"]
    # the shutdown pair keeps its previous treatment: the ideal pending still writes `no no shutdown` for it
    a = P.Model({"switchport", "no shutdown"}, None, (), True)
    b = P.Model({"switchport", "shutdown"}, None, (), True)
    assert P.vpc_transition_problems(a, b) == P.validate_transition(["shutdown", "no no shutdown"], a, b) == []


# ================================================================== Ethernet int_pvlan_host: disable_lldp_transmit / _receive
def eth_preview(running_extra=(), expected_extra=(), pending=()):
    """SYNTHETIC: the measured converged G6-M0a stanzas plus the template's `no lldp ...` lines (Ethernet 379-386 [SRC])."""
    running, expected = authority("G6-M0a", "post")
    lines = ["interface ethernet1/7"] + list(pending) + ["configure terminal"] if pending else []
    return preview(lines, running=running + list(running_extra), expected=expected + list(expected_extra))


def eth_item(**profile):
    return pvlan_item(pvlan_mode="trunk promiscuous", **profile)


def have_nv(**over):
    nv = copy.deepcopy(TPROM_A11)
    nv.update(over)
    return nv


@pytest.mark.parametrize("patch_version", APPROVED)
@pytest.mark.parametrize(
    "key,nvp,line", [("disable_lldp_transmit", "lldpTransmit", "no lldp transmit"), ("disable_lldp_receive", "lldpReceive", "no lldp receive")]
)
def test_eth_explicit_true_reaches_the_payload_as_the_exact_nvpair_and_deploys(patch_version, key, nvp, line):
    c = ctrl()
    c.previews = [eth_preview(expected_extra=["  " + line], pending=["  " + line])]
    status, res = run(c, [eth_item(**{key: True})], patch_version=patch_version)
    assert status == "exit" and res["changed"] is True, res.get("msg")
    policy, nv = c.sent_nv(IF7)
    assert policy == PVLAN and nv[nvp] == "true"
    for k, v in TPROM_A11.items():
        if k != nvp and k in nv:
            assert nv[k] == v, k  # lists, native/allowed, admin down, every other companion: HAVE
    assert nv["ADMIN_STATE"] == "false"
    assert res["diff"][0]["merged"][0]["interfaces"][0]["nvPairs"] == {nvp: "true"}
    assert c.order() == ["MODIFY", "PREVIEW", "DEPLOY"]


def test_eth_explicit_false_over_a_true_have_is_sent_and_the_positive_withdrawal_deploys():
    c = ctrl(nv=have_nv(lldpTransmit="true"))
    c.previews = [eth_preview(running_extra=["  no lldp transmit"], pending=["  lldp transmit"])]
    status, res = run(c, [eth_item(disable_lldp_transmit=False)], patch_version=SMU)
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert c.sent_nv(IF7)[1]["lldpTransmit"] == "false"
    assert c.order() == ["MODIFY", "PREVIEW", "DEPLOY"]


def test_eth_exact_repeat_writes_nothing():
    c = ctrl(nv=have_nv(lldpTransmit="true"))
    status, res = run(c, [eth_item(disable_lldp_transmit=True, deploy=False)], patch_version=SMU)
    assert status == "exit" and res["changed"] is False, res
    assert c.mutating() == []


def test_eth_merged_omission_keeps_a_true_have_while_the_list_changes():
    c = ctrl(nv=have_nv(lldpReceive="true"))
    status, res = run(c, [eth_item(pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2212"}], deploy=False)])
    assert status == "exit" and res["changed"] is True, res.get("msg")
    nv = c.sent_nv(IF7)[1]
    assert nv["lldpReceive"] == "true" and nv["lldpTransmit"] == "false"
    assert "lldpReceive" not in res["diff"][0]["merged"][0]["interfaces"][0]["nvPairs"]


def full_model(**extra):
    return eth_item(
        pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2211"}],
        native_vlan="2301",
        allowed_vlans="2301",
        admin_state=False,
        bpdu_guard="no",
        deploy=False,
        **extra
    )


def test_eth_replaced_omission_with_an_approved_capability_withdraws_to_the_inferred_reset():
    c = ctrl(nv=have_nv(lldpTransmit="true"))
    status, res = run(c, [full_model()], state="replaced", patch_version=SMU)
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert c.sent_nv(IF7)[1]["lldpTransmit"] == "false"  # INFERRED reset, NOT measured on int_pvlan_host


@pytest.mark.parametrize("patch_version", REFUSED)
def test_eth_replaced_omission_without_the_capability_preserves_the_have(patch_version):
    c = ctrl(nv=have_nv(lldpTransmit="true"))
    status, res = run(c, [full_model()], state="replaced", patch_version=patch_version)
    assert status == "exit" and res["changed"] is False, res
    assert c.mutating() == []


@pytest.mark.parametrize("patch_version", REFUSED)
def test_eth_explicit_without_the_capability_refuses_the_whole_batch_before_any_write(patch_version):
    c = ctrl()
    c.detail["Ethernet1/8"] = copy.deepcopy(c.detail[IF7])
    batch = [eth_item(bpdu_guard="true"), dict(eth_item(disable_lldp_receive=True), name="Ethernet1/8")]
    status, res = run(c, batch, patch_version=patch_version)
    assert status == "fail" and res["msg"].startswith("'disable_lldp_receive' requires caller-supplied patch_version"), res
    assert c.mutating() == [] and c.requests(mark=PREVIEW_MARK) == []


def test_eth_explicit_below_the_ndfc_floor_is_refused_before_any_write():
    c = ctrl()
    status, res = run(c, [eth_item(disable_lldp_transmit=True)], patch_version=SMU, version=(12, "12.5.0.1"))
    assert status == "fail" and "requires NDFC 12.6.0.267" in res["msg"], res
    assert c.mutating() == []


def test_eth_check_mode_writes_nothing_under_the_existing_pvlan_check_mode_contract():
    """The native PVLAN contract for an update in check mode is unchanged: refused read-only (the bulk capability probe is a
    POST), and nothing at all is written."""
    c = ctrl()
    status, res = run(c, [eth_item(disable_lldp_transmit=True)], patch_version=SMU, check_mode=True)
    assert status == "fail" and "could not be verified in check mode" in res["msg"], res
    assert c.mutating() == [] and c.requests(mark=PREVIEW_MARK) == []
    # without the capability the engine refusal comes first, still before anything is sent
    c = ctrl()
    status, res = run(c, [eth_item(disable_lldp_transmit=True)], check_mode=True)
    assert status == "fail" and "requires caller-supplied patch_version" in res["msg"]
    assert c.mutating() == []


def test_eth_policy_change_still_carries_the_have_lldp_when_omitted():
    """Unchanged base behaviour: a trunk host turned PVLAN keeps its lldp booleans (PRESERVE_ALWAYS), the registry resolves only
    the same parent."""
    out = P.reconcile(
        "merged",
        {"pvlan_mode": "host", "pvlan_association": [{"primary_vlan": 2210, "secondary_vlan": 2212}]},
        IF7,
        P.TRUNK_HOST_POLICY,
        {"lldpTransmit": "true", "lldpReceive": "false"},
        ndfc_version="12.6.0.267",
        patch_version=SMU,
    )
    assert out["nv"]["lldpTransmit"] == "true" and out["blocked"] == []


# ================================================================== port-channel int_port_channel_pvlan_host (+ member)
from .test_dcnm_intf_pvlan_harness import SWITCH_IP  # noqa: E402
from .test_dcnm_intf_pvlan_po_g1 import RUNNING_MEMBER as PO_RUNNING_MEMBER  # noqa: E402
from .test_dcnm_intf_pvlan_po_g1 import member_stanza, po_stanza  # noqa: E402
from .test_dcnm_intf_pvlan_po_g5_next_modes import CASES, existing, new_ctrl  # noqa: E402
from .test_dcnm_intf_pvlan_po_host import PO, PO_ITEM_NAME  # noqa: E402
from .test_dcnm_intf_pvlan_po_g1 import item as po_item  # noqa: E402

TP_LINES = CASES["trunk promiscuous"][1]


def po_c1(mode, lines, extra=(), drop=()):
    """SYNTHETIC Po stanza: the harness stanza (g1) with template lines dropped/added (HOST 476-499 [SRC])."""
    return [l for l in po_stanza(mode, lines) if l.strip() not in drop] + ["  " + x for x in extra]


def member_c1(mode, lines, extra=()):
    return member_stanza(mode, lines) + ["  " + x for x in extra]


PO_C1_PROFILE = dict(
    bpdu_guard="false",
    port_type_fast=False,
    spanning_tree_port_type="network",
    orphan_port=True,
    duplex="full",
    speed="1Gb",  # A duplex other than auto needs a fixed speed (the device rejects it with speed Auto)
    disable_lacp_suspend_individual=True,
    queuing_policy="C1-Q",
    disable_queuing_stats=True,
    enable_cdp=False,
    lacp_port_priority=100,
    disable_lldp_transmit=True,
    description="C1-PO",
    copy_description=True,
)
PO_C1_PO_LINES = [
    "spanning-tree bpduguard disable",
    "spanning-tree port type network",
    "description C1-PO",
    "vpc orphan-port suspend",
    "duplex full",
    "speed 1000",
    "no lacp suspend-individual",
    "service-policy type queuing output C1-Q no-stats",
]
PO_C1_PO_DROP = ("spanning-tree bpduguard enable", "spanning-tree port type edge trunk")
PO_C1_MEMBER_LINES = ["description C1-PO", "no cdp enable", "no lldp transmit", "lacp port-priority 100", "duplex full", "speed 1000"]


def po_create_preview(mode, lines, po_extra, po_drop, member_extra):
    """SYNTHETIC creation pending (the g1 measured-form transposition) with the companion lines on the Po and on the member."""
    po = po_c1(mode, lines, po_extra, po_drop)
    pend = (
        ["interface ethernet1/7", "  no spanning-tree port type edge trunk"]
        + po
        + ["interface ethernet1/7", "  channel-group 10 force mode active", "  shutdown"]
        + ["  " + x for x in member_extra]
        + ["configure terminal"]
    )
    return preview(pend, running=PO_RUNNING_MEMBER, expected=po + member_c1(mode, lines, member_extra))


@pytest.mark.parametrize("patch_version", APPROVED)
def test_po_creation_carries_every_companion_in_the_template_types_and_deploys(patch_version):
    mode = "trunk promiscuous"
    profile = dict(CASES[mode][0], **PO_C1_PROFILE)
    c = new_ctrl(mode)
    c.previews = [po_create_preview(mode, TP_LINES, PO_C1_PO_LINES, PO_C1_PO_DROP, PO_C1_MEMBER_LINES)]
    status, res = run(c, [po_item(mode, **profile)], state="replaced", patch_version=patch_version)
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert len(c.creates()) == 1 and len(c.deploys()) == 1
    nv = json.loads(c.creates()[0][2])["interfaces"][0]["nvPairs"]
    expected = {
        "BPDUGUARD_ENABLED": "false",
        "PORTTYPE_FAST_ENABLED": "false",
        "spanningTreePortType": "network",
        "ENABLE_ORPHAN_PORT": "true",
        "PORT_DUPLEX_MODE": "full",
        "DISABLE_LACP_SUSPEND": "true",
        "QUEUING_POLICY": "C1-Q",
        "queuingStats": "true",
        "CDP_ENABLE": "false",
        "LACP_PORT_PRIO": 100,
        "lldpTransmit": "true",
        "lldpReceive": "false",
        "COPY_DESC": "true",
        "DESC": "C1-PO",
        "MTU": "jumbo",
        "SPEED": "1Gb",
        "LACP_RATE": "normal",
        "ADMIN_STATE": "false",
        "PVLAN_MODE": mode,
        "PVLAN_NATIVE_VLAN": "2301",
        "PVLAN_ALLOWED_VLANS": "2301",
        "CONF": "",
    }
    for k, v in expected.items():
        assert nv[k] == v and type(nv[k]) is type(v), (k, nv[k])
    assert P.pairs_from_wire(nv["MAPPING_LIST"], "MAPPING_LIST") == [(2210, 2211), (2210, 2212), (2410, 2412)]


def test_po_creation_without_companions_sends_the_unchanged_base_payload():
    """A creation that names no companion keeps the template declarations exactly as before C1 (byte-identical nvPairs)."""
    mode = "trunk promiscuous"
    raw = dict(CASES[mode][0], pvlan_mode=mode, members=[IF7], admin_state=False)
    nv = P.po_host_nvpairs(raw, PO)
    assert dict((k, nv[k]) for k, _d in P.PO_TEMPLATE_DEFAULTS) == dict(list(P.PO_TEMPLATE_DEFAULTS[:-1]) + [("ADMIN_STATE", "false")])


def po_update_preview(mode, lines, po_extra=(), po_drop=(), member_extra=(), pend_po=(), pend_member=(), running_po=None, running_member=None):
    running = (running_po or po_stanza(mode, lines)) + (running_member or member_stanza(mode, lines))
    pend = []
    if pend_po:
        pend += ["interface port-channel10"] + ["  " + x for x in pend_po]
    if pend_member:
        pend += ["interface Ethernet1/7"] + ["  " + x for x in pend_member]
    return preview(pend, running=running, expected=po_c1(mode, lines, po_extra, po_drop) + member_c1(mode, lines, member_extra))


def po_update_item(mode, **profile):
    prof = dict({"mode": "pvlan", "pvlan_mode": mode}, **profile)
    return {"name": PO_ITEM_NAME, "type": "pc", "switch": [SWITCH_IP], "deploy": True, "profile": prof}


@pytest.mark.parametrize("mode", sorted(CASES))
def test_po_merged_member_companions_reach_the_member_model_and_keep_the_pvlan_core(mode):
    c = existing(mode)
    have = copy.deepcopy(c.detail[PO]["nvPairs"])
    lines = CASES[mode][1]
    member = ["no cdp enable", "no lldp receive", "lacp port-priority 200", "lacp rate fast"]
    c.previews = [po_update_preview(mode, lines, member_extra=member, pend_member=member)]
    upd = po_update_item(mode, enable_cdp=False, disable_lldp_receive=True, lacp_port_priority=200, lacp_rate="fast")
    status, res = run(c, [upd], state="merged", patch_version=SMU)
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert c.creates() == [] and len(c.bulk_bodies()) == 1 and len(c.deploys()) == 1
    sent = c.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]
    assert (sent["CDP_ENABLE"], sent["lldpReceive"], sent["LACP_PORT_PRIO"], sent["LACP_RATE"]) == ("false", "true", 200, "fast")
    for k in (
        "MAPPING_LIST",
        "ASSOCIATION_LIST",
        "PVLAN_NATIVE_VLAN",
        "PVLAN_ALLOWED_VLANS",
        "MEMBER_INTERFACES",
        "ADMIN_STATE",
        "PC_MODE",
        "DESC",
        "lldpTransmit",
        "spanningTreePortType",
        "queuingStats",
    ):
        assert sent[k] == have[k], k
    assert set(res["diff"][0]["merged"][0]["interfaces"][0]["nvPairs"]) == {"CDP_ENABLE", "lldpReceive", "LACP_PORT_PRIO", "LACP_RATE"}


def test_po_lacp_rate_change_on_a_member_that_is_up_is_refused_before_any_write():
    c = existing("trunk promiscuous")
    c.detail[IF7]["nvPairs"]["ADMIN_STATE"] = "true"
    status, res = run(c, [po_update_item("trunk promiscuous", lacp_rate="fast")], state="merged")
    assert status == "fail" and "administratively down (template precondition)" in res["msg"], res
    assert c.writes() == []


@pytest.mark.parametrize(
    "profile,needle",
    [
        (dict(spanning_tree_port_type="normal"), "rejected by the template while port_type_fast is true"),
        (dict(disable_queuing_stats=True), "only takes effect with a queuing_policy"),
    ],
)
def test_po_template_rules_on_the_resulting_state_refuse_before_any_write(profile, needle):
    c = existing("trunk promiscuous")
    status, res = run(c, [po_update_item("trunk promiscuous", **profile)], state="merged", patch_version=SMU)
    assert status == "fail" and needle in res["msg"], res
    assert c.writes() == []


@pytest.mark.parametrize("mode", sorted(CASES))
def test_po_merged_po_companions_render_on_the_po_and_deploy(mode):
    c = existing(mode)
    lines = CASES[mode][1]
    po_lines = ["spanning-tree port type normal", "service-policy type queuing output C1-Q"]  # duplex: see test_dcnm_intf_pvlan_duplex_inherited.py
    c.previews = [
        po_update_preview(
            mode,
            lines,
            po_extra=po_lines,
            po_drop=("spanning-tree port type edge trunk",),
            pend_po=po_lines + ["no spanning-tree port type edge trunk"],
        )
    ]
    upd = po_update_item(mode, port_type_fast=False, spanning_tree_port_type="normal", queuing_policy="C1-Q")
    status, res = run(c, [upd], state="merged", patch_version="4.4.1")
    assert status == "exit" and res["changed"] is True, res.get("msg")
    sent = c.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]
    assert (sent["PORTTYPE_FAST_ENABLED"], sent["spanningTreePortType"], sent["PORT_DUPLEX_MODE"], sent["QUEUING_POLICY"]) == (
        "false",
        "normal",
        "auto",
        "C1-Q",
    )
    assert len(c.deploys()) == 1


@pytest.mark.parametrize("patch_version", REFUSED)
def test_po_explicit_registry_companion_without_the_capability_refuses_the_batch_before_any_write(patch_version):
    c = existing("trunk promiscuous")
    batch = [po_update_item("trunk promiscuous", enable_cdp=False, disable_lldp_transmit=True)]
    status, res = run(c, batch, state="merged", patch_version=patch_version)
    # refused by the payload builder (the bare engine message), i.e. while payloads are built, before the PVLAN reads
    assert status == "fail" and res["msg"].startswith("'disable_lldp_transmit' requires caller-supplied patch_version"), res
    assert c.writes() == [] and c.requests(mark=PREVIEW_MARK) == []


def test_po_native_companions_owe_nothing_to_the_patch_gate():
    mode = "trunk promiscuous"
    c = existing(mode)
    lines = CASES[mode][1]
    c.previews = [po_update_preview(mode, lines, member_extra=["no cdp enable"], pend_member=["no cdp enable"])]
    status, res = run(c, [po_update_item(mode, enable_cdp=False)], state="merged")  # patch_version genuinely absent
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert c.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]["CDP_ENABLE"] == "false"


def _po_with_have(mode, **have):
    c = existing(mode)
    c.detail[PO]["nvPairs"].update(have)
    return c


PO_NON_DEFAULT_HAVE = dict(lldpTransmit="true", spanningTreePortType="network", PORTTYPE_FAST_ENABLED="false", CDP_ENABLE="false", LACP_PORT_PRIO="300")


def test_po_merged_omission_keeps_every_non_default_companion_of_the_have():
    mode = "trunk promiscuous"
    c = _po_with_have(mode, **PO_NON_DEFAULT_HAVE)
    status, res = run(c, [po_update_item(mode, pvlan_mapping=[{"primary_vlan": 2410, "secondary_vlans": "2411"}])], state="merged")
    sent = c.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"] if c.bulk_bodies() else None
    assert sent is not None, res.get("msg")
    for k, v in PO_NON_DEFAULT_HAVE.items():
        assert sent[k] == v, k


def po_full_model(mode, **extra):
    prof = dict(CASES[mode][0], members=[IF7], admin_state=False)
    prof.update(extra)
    it = po_update_item(mode, **prof)
    it["deploy"] = False
    return it


def test_po_replaced_omission_with_the_capability_resets_registry_and_native_companions():
    mode = "trunk promiscuous"
    c = _po_with_have(mode, **PO_NON_DEFAULT_HAVE)
    status, res = run(c, [po_full_model(mode)], state="replaced", patch_version=SMU)
    assert status == "exit" and res["changed"] is True, res.get("msg")
    sent = c.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]
    # registry: INFERRED resets; native: the template declarations (existing replaced contract)
    assert (sent["lldpTransmit"], sent["spanningTreePortType"]) == ("false", "no")
    assert (sent["PORTTYPE_FAST_ENABLED"], sent["CDP_ENABLE"], sent["LACP_PORT_PRIO"]) == ("true", "true", 32768)


@pytest.mark.parametrize("patch_version", REFUSED)
def test_po_replaced_omission_without_the_capability_preserves_the_registry_have(patch_version):
    mode = "trunk promiscuous"
    have = dict(lldpTransmit="true", spanningTreePortType="network", PORTTYPE_FAST_ENABLED="false")
    c = _po_with_have(mode, **have)
    status, res = run(c, [po_full_model(mode, port_type_fast=False)], state="replaced", patch_version=patch_version)
    assert status == "exit", res.get("msg")
    sent = c.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"] if c.bulk_bodies() else c.detail[PO]["nvPairs"]
    assert (sent["lldpTransmit"], sent["spanningTreePortType"]) == ("true", "network")


def test_po_exact_repeat_of_the_companions_writes_nothing():
    mode = "trunk promiscuous"
    c = _po_with_have(mode, CDP_ENABLE="false", lldpTransmit="true", LACP_PORT_PRIO="100")
    upd = po_update_item(mode, enable_cdp=False, disable_lldp_transmit=True, lacp_port_priority=100)
    upd["deploy"] = False
    status, res = run(c, [upd], state="merged", patch_version=SMU)
    assert status == "exit" and res["changed"] is False, res
    assert c.writes() == []


# ================================================================== vPC int_vpc_pvlan_host -> int_vpc_pvlan_po x2 -> member x2
from .test_dcnm_intf_pvlan_vpc_harness import IP1, IP2, M1, M2, SN1, SN2, VPC, run_vpc  # noqa: E402
from .test_dcnm_intf_pvlan_vpc_harness import preview as vpc_preview  # noqa: E402
from .test_dcnm_intf_pvlan_vpc_modes_e1 import MODES as VPC_MODES  # noqa: E402
from .test_dcnm_intf_pvlan_vpc_modes_e1 import (
    PAIRS,
    TP,
    baseline_ctrl,
    converged_previews,
    gate,
    member_after,
    per_peer,
    seeded_ctrl,
    sent_parent,
)  # noqa: E402
from .test_dcnm_intf_pvlan_vpc_modes_e1 import item as vpc_item  # noqa: E402
from .test_dcnm_intf_pvlan_vpc_modes_e1 import po_stanza as vpc_po_stanza  # noqa: E402
from .test_dcnm_intf_pvlan_vpc_modes_e1 import create_preview as vpc_create_preview  # noqa: E402

PEERS = ((SN1, M1), (SN2, M2))


def vpc_child(mode, pairs, native, allowed, extra=(), drop=()):
    """SYNTHETIC child stanza (POVPC 277-321 [SRC]) with companion lines."""
    return [l for l in vpc_po_stanza(mode, pairs, native, allowed) if l.strip() not in drop] + ["  " + x for x in extra]


def vpc_member(port, mode, pairs, native, allowed, extra=()):
    return member_after(port, mode, pairs, native, allowed) + ["  " + x for x in extra]


def vpc_update_previews(ctrl, mode, po_extra=(), po_drop=(), member_extra=(), pend_po=(), pend_member=()):
    """Per serial: the prior converged preview, then the SYNTHETIC update preview (the parent-only pending shape + lines)."""
    pairs = PAIRS[mode]
    for i, (serial, port) in enumerate(PEERS):
        native, allowed = per_peer(mode, i)
        before = vpc_po_stanza(mode, pairs, native, allowed) + member_after(port, mode, pairs, native, allowed)
        pend = []
        if pend_po:
            pend += ["interface port-channel10"] + ["  " + x for x in pend_po]
        if pend_member:
            pend += ["interface %s" % port] + ["  " + x for x in pend_member]
        after = vpc_child(mode, pairs, native, allowed, po_extra, po_drop) + vpc_member(port, mode, pairs, native, allowed, member_extra)
        ctrl.vpc_previews[serial] = [
            vpc_preview([], serial=serial, running=before, expected=before),
            vpc_preview(pend, serial=serial, running=before, expected=after),
        ]


def vpc_update_item(mode, **profile):
    prof = dict({"mode": "pvlan", "pvlan_mode": mode, "peer1_pcid": 10, "peer2_pcid": 10}, **profile)
    return {"name": "vpc10", "type": "vpc", "switch": [IP1, IP2], "deploy": True, "profile": prof}


VPC_CHILD_LINES = [
    "priority-flow-control mode on",
    "priority-flow-control watch-dog-interval on",
    "lacp vpc-convergence",
    "ip port access-group C1-ACL in",
    "service-policy type queuing output C1-Q no-stats",
]
VPC_MEMBER_LINES = ["no cdp enable", "no lldp transmit", "lacp port-priority 100"]  # duplex: see test_dcnm_intf_pvlan_duplex_inherited.py
VPC_C1_PROFILE = dict(
    enable_pfc=True,
    enable_lacp_vpc_convergence=True,
    acl_filter="C1-ACL",
    queuing_policy="C1-Q",
    disable_queuing_stats=True,
    enable_cdp=False,
    disable_lldp_transmit=True,
    lacp_port_priority=100,
)


@pytest.mark.parametrize("mode", VPC_MODES)
def test_vpc_merged_companions_reach_both_children_and_both_members_and_keep_the_core(mode):
    ctrl = seeded_ctrl(mode)
    have = copy.deepcopy(ctrl.parents[VPC]["nvPairs"])
    vpc_update_previews(ctrl, mode, po_extra=VPC_CHILD_LINES, member_extra=VPC_MEMBER_LINES, pend_po=VPC_CHILD_LINES, pend_member=VPC_MEMBER_LINES)
    status, res = run_vpc(ctrl, [vpc_update_item(mode, **VPC_C1_PROFILE)], state="merged", patch_version=SMU)
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert ctrl.creates() == [] and len(ctrl.modifies()) == 1 and len(ctrl.deploys()) == 1
    nv = sent_parent(ctrl, ctrl.modifies())
    expected = {
        "ENABLE_PFC": "true",
        "ENABLE_LACP_VPC_CONV": "true",
        "aclFilter": "C1-ACL",
        "QUEUING_POLICY": "C1-Q",
        "queuingStats": "true",
        "PORT_DUPLEX_MODE": "auto",
        "CDP_ENABLE": "false",
        "lldpTransmit": "true",
        "LACP_PORT_PRIO": 100,
    }
    for k, v in expected.items():
        assert nv[k] == v, k
    for k in (
        "MAPPING_LIST",
        "ASSOCIATION_LIST",
        "PEER1_PVLAN_NATIVE_VLAN",
        "PEER2_PVLAN_NATIVE_VLAN",
        "PEER1_PVLAN_ALLOWED_VLANS",
        "PEER2_PVLAN_ALLOWED_VLANS",
        "PEER1_MEMBER_INTERFACES",
        "PEER2_MEMBER_INTERFACES",
        "ADMIN_STATE",
        "createVpc",
        "ENABLE_QOS",
        "QOS_POLICY",
        "qosStatsSuppressed",
        "SPEED",
    ):
        assert nv[k] == have[k], k
    assert gate(res) == {"prior": [(1, SN1, "converged"), (2, SN2, "converged")], "deploy": [(1, SN1, "deploy"), (2, SN2, "deploy")]}


def test_vpc_creation_carries_the_companions_and_judges_both_peers():
    mode = TP
    ctrl = baseline_ctrl(mode)
    pairs = PAIRS[mode]
    for i, (serial, port) in enumerate(PEERS):
        native, allowed = per_peer(mode, i)
        base = vpc_create_preview(serial, port, mode, pairs, native, allowed)
        entry = base["DATA"][0]
        child = vpc_child(
            mode, pairs, native, allowed, ["no lacp suspend-individual", "spanning-tree port type network"], ("spanning-tree port type edge trunk",)
        )
        member = vpc_member(port, mode, pairs, native, allowed, ["lacp rate fast", "no lldp receive"])
        pend = child + [
            "interface %s" % port.lower(),
            "  no spanning-tree port type edge trunk",
            "configure terminal",
            "interface %s" % port.lower(),
            "  channel-group 10 force mode active",
            "  shutdown",
            "  lacp rate fast",
            "  no lldp receive",
            "configure terminal",
        ]
        entry["pendingConfig"] = pend
        entry["expectedConfig"] = ["hostname placeholder-sw-1"] + child + member
        ctrl.vpc_previews[serial] = [base]
    it = vpc_item(
        mode, disable_lacp_suspend_individual=True, port_type_fast=False, spanning_tree_port_type="network", lacp_rate="fast", disable_lldp_receive=True
    )
    status, res = run_vpc(ctrl, [it], state="merged", patch_version="4.4.1")
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1
    nv = json.loads(ctrl.creates()[0][2])["interfaces"][0]["nvPairs"]
    assert (nv["DISABLE_LACP_SUSPEND"], nv["PORTTYPE_FAST_ENABLED"], nv["spanningTreePortType"], nv["LACP_RATE"], nv["lldpReceive"]) == (
        "true",
        "false",
        "network",
        "fast",
        "true",
    )
    assert sorted(r[:2] for r in gate(res)["deploy"]) == [(1, SN1), (2, SN2)]


@pytest.mark.parametrize("patch_version", REFUSED)
def test_vpc_explicit_registry_companion_without_the_capability_refuses_before_any_read_or_write(patch_version):
    ctrl = seeded_ctrl(TP)
    status, res = run_vpc(ctrl, [vpc_update_item(TP, acl_filter="C1-ACL", enable_pfc=True)], state="merged", patch_version=patch_version)
    assert status == "fail" and res["msg"].startswith("'acl_filter' requires caller-supplied patch_version"), res
    assert ctrl.writes() == [] and ctrl.previews_asked() == []


@pytest.mark.parametrize(
    "profile,needle",
    [
        (dict(spanning_tree_port_type="network"), "rejected by the template while port_type_fast is true"),
        (dict(disable_queuing_stats=True), "only takes effect with a queuing_policy"),
    ],
)
def test_vpc_template_rules_on_the_resulting_state_refuse_before_any_write(profile, needle):
    ctrl = seeded_ctrl(TP)
    status, res = run_vpc(ctrl, [vpc_update_item(TP, **profile)], state="merged", patch_version=SMU)
    assert status == "fail" and needle in res["msg"], res
    assert ctrl.writes() == []


def test_vpc_lacp_rate_change_with_one_member_up_is_refused_on_that_peer_before_any_write():
    ctrl = seeded_ctrl(TP)
    ctrl.nodes[SN2][M2]["nvPairs"]["ADMIN_STATE"] = "true"
    converged_previews(ctrl, TP)
    status, res = run_vpc(ctrl, [vpc_update_item(TP, lacp_rate="fast")], state="merged")
    assert status == "fail" and "needs member %s administratively down" % M2 in res["msg"], res
    assert M1 not in res["msg"].split("administratively down")[0].split("needs member")[-1]
    assert ctrl.writes() == []


def _vpc_with_have(mode, **have):
    ctrl = seeded_ctrl(mode)
    ctrl.parents[VPC]["nvPairs"].update(have)
    ctrl._expand_children(ctrl.parents[VPC]["nvPairs"])
    return ctrl


def vpc_full_model(mode, **extra):
    it = vpc_item(mode, deploy=False, **extra)
    return it


def test_vpc_replaced_omission_with_the_capability_resets_the_acl_to_the_inferred_reset():
    ctrl = _vpc_with_have(TP, aclFilter="OLD-ACL")
    converged_previews(ctrl, TP)
    status, res = run_vpc(ctrl, [vpc_full_model(TP)], state="replaced", patch_version=SMU)
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert sent_parent(ctrl, ctrl.modifies())["aclFilter"] == ""  # INFERRED reset, NOT measured on int_vpc_pvlan_host


@pytest.mark.parametrize("patch_version", REFUSED)
def test_vpc_replaced_omission_without_the_capability_preserves_the_acl(patch_version):
    ctrl = _vpc_with_have(TP, aclFilter="OLD-ACL")
    converged_previews(ctrl, TP)
    status, res = run_vpc(ctrl, [vpc_full_model(TP)], state="replaced", patch_version=patch_version)
    assert status == "exit" and res["changed"] is False, res
    assert ctrl.writes() == []


def vpc_converged_with(ctrl, mode, po_extra=(), member_extra=()):
    """SYNTHETIC converged preview per serial for a vPC whose children/members hold companion lines."""
    pairs = PAIRS[mode]
    for i, (serial, port) in enumerate(PEERS):
        native, allowed = per_peer(mode, i)
        state = vpc_child(mode, pairs, native, allowed, po_extra) + vpc_member(port, mode, pairs, native, allowed, member_extra)
        ctrl.vpc_previews[serial] = [vpc_preview([], serial=serial, running=state, expected=state)]


def test_vpc_merged_omission_keeps_the_non_default_companions_of_the_have():
    have = dict(aclFilter="OLD-ACL", ENABLE_PFC="true", CDP_ENABLE="false", LACP_RATE="fast")
    ctrl = _vpc_with_have(TP, **have)
    vpc_converged_with(
        ctrl,
        TP,
        ["ip port access-group OLD-ACL in", "priority-flow-control mode on", "priority-flow-control watch-dog-interval on"],
        ["no cdp enable", "lacp rate fast"],
    )
    upd = vpc_update_item(TP, peer1_description="d1", peer2_description="d2")
    upd["deploy"] = False
    status, res = run_vpc(ctrl, [upd], state="merged")
    nv = sent_parent(ctrl, ctrl.modifies()) if ctrl.modifies() else None
    assert nv is not None, res.get("msg")
    for k, v in have.items():
        assert nv[k] == v, k


def test_vpc_exact_repeat_of_the_companions_writes_nothing():
    ctrl = _vpc_with_have(TP, aclFilter="C1-ACL", ENABLE_PFC="true", LACP_PORT_PRIO="100")
    vpc_converged_with(
        ctrl, TP, ["ip port access-group C1-ACL in", "priority-flow-control mode on", "priority-flow-control watch-dog-interval on"], ["lacp port-priority 100"]
    )
    status, res = run_vpc(ctrl, [vpc_item(TP, acl_filter="C1-ACL", enable_pfc=True, lacp_port_priority=100)], state="merged", patch_version=SMU)
    assert status == "exit" and res["changed"] is False, res
    assert ctrl.writes() == []


@pytest.mark.parametrize("key,value", [("aclFilter", "OTHER"), ("ENABLE_PFC", "true"), ("queuingStats", "true"), ("spanningTreePortType", "normal")])
def test_vpc_a_child_that_does_not_follow_its_parent_on_a_companion_is_refused_before_any_write(key, value):
    ctrl = seeded_ctrl(TP)
    ctrl.nodes[SN2]["port-channel10"]["nvPairs"][key] = value
    status, res = run_vpc(ctrl, [vpc_update_item(TP, peer1_description="d1", peer2_description="d2")], state="merged")
    assert status == "fail" and key in res["msg"], res
    assert ctrl.writes() == []


def test_vpc_qos_is_in_the_public_contract_and_the_port_channel_still_refuses_it():
    # Accepted by the raw vPC validation; the port-channel PVLAN parent has no ingress QoS.
    assert P.vpc_not_implemented(
        {"mode": "pvlan", "pvlan_mode": "host", "peer1_pcid": 10, "peer2_pcid": 10, "enable_qos": True, "qos_policy": "Q", "disable_qos_stats": True}, "vpc10"
    ) == []
    reasons = P.po_not_implemented({"pvlan_mode": "host", "enable_qos": True, "qos_policy": "Q"})
    assert reasons and "enable_qos" in reasons[0] and "qos_policy" in reasons[0]


# ================================================================== omission contract of EVERY registry companion (real helper)
# (parent, nvPair, public key, non-default HAVE value, reset). Consumed by test_dcnm_intf_withdrawal.py's coverage guard: these
# identities take the PVLAN route, not the generic comparator its fixture matrix drives.
PVLAN_ROUTE_RESET_ROWS = (
    (P.PVLAN_POLICY, "lldpTransmit", "disable_lldp_transmit", "true", "false"),
    (P.PVLAN_POLICY, "lldpReceive", "disable_lldp_receive", "true", "false"),
    (P.PO_HOST_POLICY, "lldpTransmit", "disable_lldp_transmit", "true", "false"),
    (P.PO_HOST_POLICY, "lldpReceive", "disable_lldp_receive", "true", "false"),
    (P.PO_HOST_POLICY, "spanningTreePortType", "spanning_tree_port_type", "network", "no"),
    (P.PO_HOST_POLICY, "queuingStats", "disable_queuing_stats", "true", "false"),
    (P.VPC_HOST_POLICY, "lldpTransmit", "disable_lldp_transmit", "true", "false"),
    (P.VPC_HOST_POLICY, "lldpReceive", "disable_lldp_receive", "true", "false"),
    (P.VPC_HOST_POLICY, "spanningTreePortType", "spanning_tree_port_type", "normal", "no"),
    (P.VPC_HOST_POLICY, "queuingStats", "disable_queuing_stats", "true", "false"),
    (P.VPC_HOST_POLICY, "aclFilter", "acl_filter", "OLD-ACL", ""),
    (P.VPC_HOST_POLICY, "qosStatsSuppressed", "disable_qos_stats", "true", "false"),  # ingress QoS
)
PVLAN_ROUTE_RESET_IDENTITIES = frozenset((p, n) for p, n, _k, _h, _r in PVLAN_ROUTE_RESET_ROWS)
_IDS = ["%s::%s" % (p.replace("int_", ""), n) for p, n, _k, _h, _r in PVLAN_ROUTE_RESET_ROWS]


@pytest.mark.parametrize("policy,nvp,key,have_value,reset", PVLAN_ROUTE_RESET_ROWS, ids=_IDS)
@pytest.mark.parametrize(
    "state,patch_version,expect",
    [
        ("merged", SMU, "have"),
        ("merged", None, "have"),
        ("replaced", SMU, "reset"),
        ("replaced", "4.4.1", "reset"),
        ("overridden", SMU, "reset"),
        ("replaced", None, "have"),
        ("replaced", "4.3.1.0175006010", "have"),
        ("overridden", None, "have"),
    ],
)
def test_every_registry_companion_follows_the_engine_omission_contract(policy, nvp, key, have_value, reset, state, patch_version, expect):
    have = {nvp: have_value}
    values, blocked = P.registry_companions(state, policy, {}, have, "12.6.0.267", patch_version)
    assert blocked == []
    assert values[nvp] == (have_value if expect == "have" else reset)
    # an explicit value always wins over HAVE (and needs the capability)
    b_value = True if have_value in ("true", "false") else ("normal" if key == "spanning_tree_port_type" else "NEW-ACL")
    values, blocked = P.registry_companions(state, policy, {key: b_value}, have, "12.6.0.267", SMU)
    assert blocked == [] and values[nvp] == ("true" if b_value is True else b_value)
    values, blocked = P.registry_companions(state, policy, {key: b_value}, have, "12.6.0.267", None)
    assert values == {} and "requires caller-supplied patch_version" in blocked[0]


def test_a_have_value_the_binding_cannot_read_fails_closed_under_replaced():
    values, blocked = P.registry_companions("replaced", P.PO_HOST_POLICY, {}, {"spanningTreePortType": "edge"}, "12.6.0.267", SMU)
    assert "spanningTreePortType" not in values and blocked


def test_po_and_vpc_check_mode_with_companions_write_nothing():
    c = existing("trunk promiscuous")
    status, res = run(
        c, [po_update_item("trunk promiscuous", enable_cdp=False, disable_lldp_transmit=True)], state="merged", patch_version=SMU, check_mode=True
    )
    assert c.writes() == [], res
    ctrl = seeded_ctrl(TP)
    converged_previews(ctrl, TP)
    status, res = run_vpc(ctrl, [vpc_update_item(TP, acl_filter="C1-ACL")], state="merged", patch_version=SMU, check_mode=True)
    assert ctrl.writes() == [], res


# ================================================================== exact object names in the vPC child readback
_R1_BASE = dict(PVLAN_MODE="host", ADMIN_STATE="false", DESC="", BPDUGUARD_ENABLED="true", PORTTYPE_FAST_ENABLED="true", MTU="jumbo")


@pytest.mark.parametrize("key", ["aclFilter", "QUEUING_POLICY"])
@pytest.mark.parametrize("child_value,differs", [("POLICY_A", False), ("policy_a", True), ("Policy_A", True), ("POLICY_B", True)])
def test_r1_child_object_names_are_compared_exactly(key, child_value, differs):
    """An expected POLICY_A against a child policy_a used to be reported equal. Object names keep case."""
    expected = dict(_R1_BASE, **{key: "POLICY_A"})
    child = dict(expected, **{key: child_value})
    assert (key in P.vpc_child_differences(child, expected)) is differs


@pytest.mark.parametrize(
    "child_over,expected_over",
    [
        ({"ENABLE_PFC": "True"}, {"ENABLE_PFC": "true"}),
        ({"queuingStats": "FALSE"}, {}),  # expected omits it: template default "false"
        ({}, {"ENABLE_LACP_VPC_CONV": "false", "DISABLE_LACP_SUSPEND": "False"}),
        ({"spanningTreePortType": "No"}, {}),
        ({"PORT_DUPLEX_MODE": "AUTO"}, {"PORT_DUPLEX_MODE": "auto"}),
        ({}, {"aclFilter": "", "QUEUING_POLICY": ""}),  # absent names = template default ''
    ],
)
def test_r1_boolean_enum_and_default_normalization_is_kept(child_over, expected_over):
    assert P.vpc_child_differences(dict(_R1_BASE, **child_over), dict(_R1_BASE, **expected_over)) == []


@pytest.mark.parametrize("key,parent_value,child_value", [("aclFilter", "C1-ACL", "c1-acl"), ("QUEUING_POLICY", "C1-Q", "c1-q")])
def test_r1_a_peer_whose_child_differs_only_in_name_case_is_refused_before_any_write(key, parent_value, child_value):
    """The route that consumes the check (the pre-write leg read of an existing vPC update): peer 2's child holds the parent's
    object name in another case; peer 1's child matches exactly and is the control."""
    ctrl = _vpc_with_have(TP, **{key: parent_value})
    assert ctrl.nodes[SN1]["port-channel10"]["nvPairs"][key] == parent_value
    ctrl.nodes[SN2]["port-channel10"]["nvPairs"][key] = child_value
    status, res = run_vpc(ctrl, [vpc_update_item(TP, peer1_description="d1", peer2_description="d2")], state="merged")
    assert status == "fail" and key in res["msg"], res
    flagged = [l for l in res["msg"].splitlines() if key in l]
    assert flagged and all(SN2 in l for l in flagged) and not any(SN1 in l and SN2 not in l for l in flagged), flagged
    assert ctrl.writes() == []


def test_r1_control_the_same_vpc_with_both_children_exact_passes_the_child_check():
    ctrl = _vpc_with_have(TP, aclFilter="C1-ACL", QUEUING_POLICY="C1-Q")
    vpc_converged_with(ctrl, TP, ["ip port access-group C1-ACL in", "service-policy type queuing output C1-Q"])
    upd = vpc_update_item(TP, acl_filter="C1-ACL", queuing_policy="C1-Q")
    upd["deploy"] = False
    status, res = run_vpc(ctrl, [upd], state="merged", patch_version=SMU)
    assert status == "exit" and res["changed"] is False, res
    assert ctrl.writes() == []
