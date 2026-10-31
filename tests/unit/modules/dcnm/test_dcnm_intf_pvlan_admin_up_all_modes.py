"""An administratively up member joins a PVLAN regular port-channel or vPC in promiscuous, trunk promiscuous and trunk
secondary (on the access/routed bases prepared for it) and keeps its own state, member by member and peer by peer.

OFFLINE ONLY: no lab measurement of these modes with an up member. The previews are the existing harnesses' down-member previews
of each mode (measured for trunk secondary and for the promiscuous/trunk promiscuous creation form) with the member's admin line
switched by the rule MEASURED for host (fixtures/pvlan_admin_up_join_measured.json): the member pending and expected carry
`no shutdown`; the running of an up switchport member has no `shutdown` line and an up routed port shows `no shutdown`; an up
routed port carries the measured own child `no_shut_interface` instead of `shut_interface`. That switch is SYNTHETIC for these
modes. Real main(); only the controller boundary is intercepted.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from . import test_dcnm_intf_pvlan_member_updates as MU
from . import test_dcnm_intf_pvlan_po_g5_next_modes as G5
from . import test_dcnm_intf_pvlan_po_g6_ts_prepared as G6
from . import test_dcnm_intf_pvlan_vpc_modes_e1 as E1
from .test_dcnm_intf_pvlan_harness import IF7, run, trunk_host_nv
from .test_dcnm_intf_pvlan_vpc_harness import IP1, IP2, M1, M2, SN1, SN2

P_, TP, TS = "promiscuous", "trunk promiscuous", "trunk secondary"
E9 = "Ethernet1/9"


def up_lines(lines, port, kind, routed=False):
    """`lines` with the admin line of `port`'s stanzas switched to the up form (see the module docstring)."""
    out, inside = [], False
    for line in lines:
        if not line.startswith(" "):
            inside = line.strip().lower() == "interface %s" % port.lower()
            out.append(line)
            if inside and kind == "running" and routed:
                out.append("  no shutdown")
            continue
        if inside and line.strip() == "shutdown":
            if kind == "running":
                continue
            line = "  no shutdown"
        out.append(line)
    return out


def up_preview(resp, port, routed=False):
    resp = copy.deepcopy(resp)
    entry = resp["DATA"][0]
    entry["pendingConfig"] = up_lines(entry.get("pendingConfig") or [], port, "pending")
    if entry.get("expectedConfig") is not None:
        entry["expectedConfig"] = up_lines(entry["expectedConfig"], port, "expected")
    if entry.get("runningConfig") is not None:
        entry["runningConfig"] = up_lines(entry["runningConfig"], port, "running", routed)
    return resp


def admin(nv, value):
    nv = dict(nv)
    nv["ADMIN_STATE"] = value
    return nv


def sent_nv(ctrl):
    body = json.loads(ctrl.creates()[0][2])
    return (body[0] if isinstance(body, list) else body)["interfaces"][0]["nvPairs"]


def test_the_up_rule_reproduces_the_measured_host_forms():
    """Guard of the SYNTHETIC switch: applied to the harness host preview it gives the member lines MEASURED in M1."""
    fx = json.load(open(G6.os.path.join(G6.os.path.dirname(__file__), "fixtures", "pvlan_admin_up_join_measured.json")))
    measured = fx["M1"]["pre_deploy"]["<SERIAL_LEAF_B>"]
    pend = up_lines(["interface ethernet1/7", "  channel-group 10 force mode active", "  shutdown"], IF7, "pending")
    assert pend[-1].strip() == measured["pending"][-2].strip() == "no shutdown"
    run_ = up_lines(G5.RUNNING_MEMBER, IF7, "running")
    assert "shutdown" not in [l.strip() for l in run_]
    assert not any(l.strip() == "shutdown" for l in measured["running"] if not l.startswith("interface"))


# ================================================================== helper contract
@pytest.mark.parametrize("mode", [P.MODE_HOST, P_, TP])
@pytest.mark.parametrize("value", ["true", "false", True, False])
def test_trunk_host_member_with_an_explicit_state_is_admitted_in_every_non_secondary_mode(mode, value):
    assert P.po_member_baseline_problems(P.TRUNK_HOST_POLICY, admin(trunk_host_nv(IF7), value), mode) == []


@pytest.mark.parametrize("policy", [P.PO_ACCESS_BASELINE_POLICY, P.PO_ROUTED_BASELINE_POLICY])
@pytest.mark.parametrize("value", ["true", "false"])
def test_prepared_access_or_routed_member_is_admitted_up_or_down_for_trunk_secondary(policy, value):
    nv = dict((k, v[0]) for k, v in P._PO_PREPARED_NEUTRAL[policy])
    assert P.po_member_baseline_problems(policy, admin(nv, value), TS) == []


@pytest.mark.parametrize("value", ["true", "false"])
def test_trunk_member_stays_the_trunk_secondary_incident_whatever_its_admin_state(value):
    assert P.po_member_baseline_problems(P.TRUNK_HOST_POLICY, admin(trunk_host_nv(IF7), value), TS) == [P.PO_TS_TRUNK_MEMBER_INCIDENT]


@pytest.mark.parametrize("mode, policy", [(P_, P.TRUNK_HOST_POLICY), (TP, P.TRUNK_HOST_POLICY), (TS, P.PO_ACCESS_BASELINE_POLICY),
                                          (TS, P.PO_ROUTED_BASELINE_POLICY)])
@pytest.mark.parametrize("value", ["", None, "0", "up"])
def test_unknown_admin_state_is_refused_in_every_mode_and_base(mode, policy, value):
    nv = trunk_host_nv(IF7) if policy == P.TRUNK_HOST_POLICY else dict((k, v[0]) for k, v in P._PO_PREPARED_NEUTRAL[policy])
    problems = P.po_member_baseline_problems(policy, admin(nv, value), mode)
    assert problems and "administrative state is unknown" in problems[0]


def test_routed_own_children_follow_the_member_state_and_never_the_other_one():
    assert P.po_routed_member_self_children({"ADMIN_STATE": "true"}) == P.PO_ROUTED_RELEASE_CHILDREN_UP
    assert P.po_routed_member_self_children({"ADMIN_STATE": "false"}) == P.PO_ROUTED_SELF_CHILDREN
    assert P.po_routed_member_self_children({"ADMIN_STATE": None}) == frozenset()
    assert "no_shut_interface" not in P.po_routed_member_self_children({"ADMIN_STATE": "false"})
    assert "shut_interface" not in P.po_routed_member_self_children({"ADMIN_STATE": "true"})


@pytest.mark.parametrize("mode", [P_, TP, TS])
def test_the_intended_member_keeps_its_own_state_in_every_mode(mode):
    for state, line in (("true", "no shutdown"), ("false", "shutdown")):
        parent = P.po_host_nvpairs(dict(G5.CASES[mode][0], pvlan_mode=mode, members=[IF7], admin_state=False), "Port-channel10")
        member = P.po_member_nvpairs(parent, admin(trunk_host_nv(IF7), state))
        assert member["ADMIN_STATE"] == state and line in P.render(P.PO_MEMBER_POLICY, member).scalars


# ================================================================== regular port-channel: promiscuous / trunk promiscuous
def g5_up_ctrl(mode):
    ctrl = G5.new_ctrl(mode)
    ctrl.detail[IF7]["nvPairs"]["ADMIN_STATE"] = "true"
    return ctrl


@pytest.mark.parametrize("state", ["replaced", "merged"])
@pytest.mark.parametrize("mode", [P_, TP])
def test_po_creation_with_an_up_member_deploys_and_never_writes_the_member(mode, state):
    profile, lines = G5.CASES[mode]
    ctrl = g5_up_ctrl(mode)
    ctrl.previews = [up_preview(G5.creation_preview(mode, lines), IF7)]
    status, result = run(ctrl, [G5.item(mode, **profile)], state=state)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1 and ctrl.bulk_bodies() == []
    nv = sent_nv(ctrl)
    assert nv["PVLAN_MODE"] == mode and nv["MEMBER_INTERFACES"] == IF7 and nv["ADMIN_STATE"] == "false"
    assert result["pvlan_gate"][0]["targets"][G5.PO] == "deploy"


@pytest.mark.parametrize("mode", [P_, TP])
def test_po_creation_whose_pending_would_shut_the_up_member_never_deploys(mode):
    profile, lines = G5.CASES[mode]
    ctrl = g5_up_ctrl(mode)
    ctrl.previews = [G5.creation_preview(mode, lines)]  # the down form: `shutdown` on a member that is up
    status, result = run(ctrl, [G5.item(mode, **profile)], state="replaced")
    assert status == "fail" and "pre-deploy gate" in result["msg"] and "ALREADY changed" in result["msg"], result.get("msg")
    assert len(ctrl.creates()) == 1 and ctrl.deploys() == []


@pytest.mark.parametrize("mode", [P_, TP])
def test_po_member_addition_of_an_up_member_keeps_the_existing_down_member(mode):
    profile, lines = G5.CASES[mode]
    ctrl = G5.existing(mode)
    ctrl.__class__ = MU.MembershipPo
    ctrl.detail[E9] = {"policy": P.TRUNK_HOST_POLICY, "nvPairs": admin(trunk_host_nv(E9), "true")}
    join = ["interface ethernet1/9", "  no spanning-tree port type edge trunk", "configure terminal",
            "interface ethernet1/9", "  channel-group 10 force mode active", "  no shutdown", "configure terminal"]
    e9_running = up_lines([l.replace("Ethernet1/7", "Ethernet1/9") for l in G5.RUNNING_MEMBER], E9, "running")
    e9_expected = up_lines([l.replace("ethernet1/7", "ethernet1/9") for l in G5.member_stanza(mode, lines)], E9, "expected")
    state = G5.po_stanza(mode, lines) + G5.member_stanza(mode, lines)
    ctrl.previews = [G5.preview(join, running=state + e9_running, expected=state + e9_expected)]
    status, result = run(ctrl, [G5.item(mode, members=[E9], **profile)], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.po_modifies()) == 1 and ctrl.member_modifies() == [] and len(ctrl.deploys()) == 1
    sent = ctrl.po_modifies()[0][0]["interfaces"][0]["nvPairs"]["MEMBER_INTERFACES"]
    assert P.normalize_member_list(sent)[0] == {"ethernet1/7", "ethernet1/9"}


def test_po_unknown_admin_state_in_trunk_promiscuous_is_refused_before_any_write():
    profile, _lines = G5.CASES[TP]
    ctrl = G5.new_ctrl(TP)
    ctrl.detail[IF7]["nvPairs"].pop("ADMIN_STATE")
    status, result = run(ctrl, [G5.item(TP, **profile)], state="replaced")
    assert status == "fail" and "administrative state is unknown" in result["msg"] and ctrl.writes() == [], result.get("msg")


# ================================================================== regular port-channel: trunk secondary (prepared access / routed)
def g6_up(b):
    ctrl = G6.ctrl_for(b, nv=admin(G6.member_nv(b), "true"))
    if b == "R":
        ctrl.policies_extra = [dict(p, templateName="no_shut_interface", priority=452) if p["templateName"] == "shut_interface" else p
                               for p in ctrl.policies_extra]
    return ctrl


@pytest.mark.parametrize("b", ["A", "R"])
def test_po_trunk_secondary_creation_from_an_up_prepared_member_deploys(b):
    ctrl = g6_up(b)
    status, result = G6.create(ctrl, up_preview(G6.measured_preview(b), G6.MEM, routed=(b == "R")))
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1 and ctrl.bulk_bodies() == []
    assert ctrl.detail[G6.MEM]["policy"] == G6.member_policy(b), "the module never converts or writes the member"
    assert result["pvlan_gate"][0]["targets"][G6.PO] == "deploy"


@pytest.mark.parametrize("b", ["A", "R"])
def test_po_trunk_secondary_down_prepared_member_is_unchanged(b):
    ctrl = G6.ctrl_for(b)
    status, result = G6.create(ctrl, G6.measured_preview(b))
    assert status == "exit", result.get("msg")


def test_po_trunk_secondary_up_routed_member_whose_down_child_survives_is_refused_before_any_write():
    ctrl = G6.ctrl_for("R", nv=admin(G6.member_nv("R"), "true"))  # an up member still holding the measured down child shut_interface
    status, result = G6.create(ctrl, up_preview(G6.measured_preview("R"), G6.MEM, routed=True))
    assert status == "fail" and "live policies" in result["msg"] and ctrl.writes() == [], result.get("msg")


def test_po_trunk_secondary_up_routed_member_whose_pending_lacks_its_admin_line_never_deploys():
    ctrl = g6_up("R")
    pv = up_preview(G6.measured_preview("R"), G6.MEM, routed=True)
    entry = pv["DATA"][0]
    entry["pendingConfig"] = [l for l in entry["pendingConfig"] if l.strip() != "no shutdown"]
    status, result = G6.create(ctrl, pv)
    assert status == "fail" and "'no shutdown'" in result["msg"] and ctrl.deploys() == [], result.get("msg")


@pytest.mark.parametrize("value", ["true", "false"])
def test_po_trunk_secondary_trunk_member_up_or_down_is_still_the_known_incident(value):
    ctrl = G6.ctrl_for("T", nv=admin(G6.member_nv("T"), value))
    status, result = G6.create(ctrl, G6.measured_preview("T"))
    assert status == "fail" and "Known incident pending engineering" in result["msg"] and ctrl.writes() == []


# ================================================================== vPC: promiscuous / trunk promiscuous / trunk secondary (access)
def e1_ctrl(mode, up=(SN1, SN2)):
    ctrl = E1.baseline_ctrl(mode)
    E1.create_previews(ctrl, mode)
    for serial, port in ((SN1, M1), (SN2, M2)):
        if serial in up:
            ctrl.nodes[serial][port]["nvPairs"]["ADMIN_STATE"] = "true"
            ctrl.vpc_previews[serial] = [up_preview(ctrl.vpc_previews[serial][0], port)]
    return ctrl


@pytest.mark.parametrize("mode", [P_, TP, TS])
@pytest.mark.parametrize("up", [(SN1, SN2), (SN1,), (SN2,)], ids=["both-up", "peer1-up", "peer2-up"])
def test_vpc_creation_with_up_and_mixed_members_judges_both_peers_and_deploys_once(mode, up):
    ctrl = e1_ctrl(mode, up)
    status, result = E1.run_vpc(ctrl, [E1.item(mode)])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1 and sorted(ctrl.previews_asked()) == [SN1, SN2]
    assert E1.gate(result) == {"deploy": [(1, SN1, "deploy"), (2, SN2, "deploy")]}
    assert ctrl.requests("POST", "/rest/interface/modify") == [], "no member is written to make the join possible"


@pytest.mark.parametrize("mode", [P_, TP, TS])
def test_vpc_mixed_states_with_the_switches_reversed_send_the_same_intent(mode):
    a, b = e1_ctrl(mode, (SN1,)), e1_ctrl(mode, (SN1,))
    assert E1.run_vpc(a, [E1.item(mode)])[0] == "exit"
    swapped = {"peer1_members": [M2], "peer2_members": [M1]}
    if mode in (TP, TS):
        swapped.update({"peer1_native_vlan": "2302", "peer1_allowed_vlans": "2302", "peer2_native_vlan": "2301", "peer2_allowed_vlans": "2301"})
    status, result = E1.run_vpc(b, [E1.item(mode, switches=[IP2, IP1], **swapped)])
    assert status == "exit", result.get("msg")
    assert sent_nv(a) == sent_nv(b)


@pytest.mark.parametrize("mode", [P_, TP, TS])
def test_vpc_peer2_pending_that_would_shut_its_up_member_stops_every_deploy(mode):
    ctrl = e1_ctrl(mode)
    ctrl.vpc_previews[SN2] = [E1.create_preview(SN2, M2, mode, E1.PAIRS[mode], *E1.per_peer(mode, 1),
                                                baseline="access" if mode == TS else "trunk")]
    status, result = E1.run_vpc(ctrl, [E1.item(mode)])
    assert status == "fail" and SN2 in result["msg"] and "ALREADY changed" in result["msg"], result.get("msg")
    assert len(ctrl.creates()) == 1 and ctrl.deploys() == []


@pytest.mark.parametrize("mode", [P_, TP, TS])
def test_vpc_unreadable_peer_with_up_members_is_refused_before_any_write(mode):
    ctrl = e1_ctrl(mode)
    ctrl.read_failures = {"/rest/interface/detail?serialNumber=" + SN2}
    status, result = E1.run_vpc(ctrl, [E1.item(mode)])
    assert status == "fail" and "could not be read authoritatively" in result["msg"] and ctrl.writes() == [], result.get("msg")


@pytest.mark.parametrize("mode", [P_, TP, TS])
def test_vpc_unknown_admin_state_on_one_peer_refuses_the_whole_vpc(mode):
    ctrl = e1_ctrl(mode, (SN1,))
    ctrl.nodes[SN2][M2]["nvPairs"]["ADMIN_STATE"] = None
    status, result = E1.run_vpc(ctrl, [E1.item(mode)])
    assert status == "fail" and "administrative state is unknown" in result["msg"] and SN2 in result["msg"] and ctrl.writes() == []


def test_vpc_trunk_secondary_up_trunk_member_on_one_peer_is_still_the_known_incident():
    ctrl = e1_ctrl(TS)
    ctrl.nodes[SN2][M2] = {"policy": P.TRUNK_HOST_POLICY, "nvPairs": admin(trunk_host_nv(M2), "true")}
    status, result = E1.run_vpc(ctrl, [E1.item(TS)])
    assert status == "fail" and "Known incident pending engineering" in result["msg"] and ctrl.writes() == []


class UpRoutedVpcController(E1.RoutedVpcController):
    """The routed vPC harness with the member's UP own children vanishing on the creation (the down set's measured behaviour, INFERRED)."""

    def __call__(self, mod, method, path, data=None):
        resp = super(UpRoutedVpcController, self).__call__(mod, method, path, data)
        if method == "POST" and path.endswith("/rest/globalInterface") and self.children_vanish:
            self.policies_extra[SN2] = [p for p in self.policies_extra[SN2] if p.get("templateName") not in P.PO_ROUTED_RELEASE_CHILDREN_UP]
        return resp


def test_vpc_trunk_secondary_up_routed_member_with_its_up_children_deploys():
    ctrl = E1.routed_ctrl(M2)
    ctrl.__class__ = UpRoutedVpcController
    ctrl.nodes[SN2][M2]["nvPairs"]["ADMIN_STATE"] = "true"
    for p in ctrl.policies_extra[SN2]:
        if p["templateName"] == "shut_interface":
            p["templateName"] = "no_shut_interface"
    ctrl.vpc_previews[SN2] = [up_preview(ctrl.vpc_previews[SN2][0], M2, routed=True)]
    status, result = E1.run_vpc(ctrl, [E1.item(TS)])
    assert status == "exit", result.get("msg")
    assert E1.gate(result) == {"deploy": [(1, SN1, "deploy"), (2, SN2, "deploy")]}


def test_vpc_trunk_secondary_up_routed_member_with_the_down_child_is_refused_before_any_write():
    ctrl = E1.routed_ctrl(M2)
    ctrl.nodes[SN2][M2]["nvPairs"]["ADMIN_STATE"] = "true"
    ctrl.vpc_previews[SN2] = [up_preview(ctrl.vpc_previews[SN2][0], M2, routed=True)]
    status, result = E1.run_vpc(ctrl, [E1.item(TS)])
    assert status == "fail" and "live policies" in result["msg"] and ctrl.writes() == [], result.get("msg")


@pytest.mark.parametrize("mode", [P_, TP, TS])
def test_vpc_repetition_with_up_members_writes_nothing(mode):
    ctrl = E1.seeded_ctrl(mode)
    for serial, port in ((SN1, M1), (SN2, M2)):
        ctrl.nodes[serial][port]["nvPairs"]["ADMIN_STATE"] = "true"
    E1.converged_previews(ctrl, mode)
    for serial, port in ((SN1, M1), (SN2, M2)):
        ctrl.vpc_previews[serial] = [up_preview(ctrl.vpc_previews[serial][0], port)]
    status, result = E1.run_vpc(ctrl, [E1.item(mode)])
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.writes() == []


@pytest.mark.parametrize("mode", [P_, TP, TS])
def test_vpc_deletion_with_an_up_member_no_longer_refuses_and_reaches_the_markdelete(mode):
    # Supersedes the admin-down-only release: the up member is released to the fabric default in every mode.
    ctrl = E1.seeded_ctrl(mode)
    ctrl.nodes[SN1][M1]["nvPairs"]["ADMIN_STATE"] = "true"
    status, result = E1.run_vpc(ctrl, [E1.vpc_del_item()], state="deleted")
    assert "not administratively down" not in str(result.get("msg"))
    assert len(ctrl.markdeletes()) == 1, result.get("msg")


@pytest.mark.parametrize("mode", [P_, TP, TS])
def test_vpc_lacp_rate_fast_with_an_up_member_stays_refused(mode):
    ctrl = e1_ctrl(mode)
    status, result = E1.run_vpc(ctrl, [E1.item(mode, lacp_rate="fast")])
    assert status == "fail" and "lacp_rate" in result["msg"] and ctrl.writes() == [], result.get("msg")
