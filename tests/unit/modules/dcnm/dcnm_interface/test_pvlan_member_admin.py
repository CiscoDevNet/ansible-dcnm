"""Administrative state of PVLAN port-channel and vPC members on join and release."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .helpers import port_channel_controller as H
from .helpers import vpc_controller as V
from .helpers import membership as MU
from .helpers.ethernet_controller import IF7
from .helpers.ethernet_controller import trunk_host_nv
from .helpers.membership import LEAF_A
from .helpers.membership import LEAF_B
from .helpers.membership import measured
from .helpers.membership import shut_the_member
from .helpers.membership import up_peers
from .helpers.membership import vpc_preview
from .helpers import port_channel_controller as G5
from .helpers import port_channel_prepared as G6
from .helpers import vpc_modes as E1
from .helpers import vpc_controller as E1_VPC
from .helpers.ethernet_controller import run
from .helpers.vpc_controller import IP1
from .helpers.vpc_controller import IP2
from .helpers.vpc_controller import M1
from .helpers.vpc_controller import M2
from .helpers.vpc_controller import SN1
from .helpers.vpc_controller import SN2
from .helpers.fixture_cases import load_case
from .helpers import port_channel_release as G4
from .helpers import vpc_controller as RC
from .helpers.ethernet_controller import SWITCH_IP
from .helpers.ethernet_controller import TRUNK


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_admin_up_join.py
# ADMIN-UP-JOIN: a free int_trunk_host member whose administrative intent is already UP joins a PVLAN regular port-channel or vPC and
# keeps its own state; every other member keeps its own. This file is the MEASURED host series; the other modes (ADMIN-UP-ALL-MODES,
# offline) are in test_pvlan_member_admin.py.
#
# MEASURED basis (fixtures/pvlan_admin_state.json, NDFC 12.6.0.267 / NX-OS 10.5(5), direct legacy writes with the module's own
# create bodies): M1 regular Po host, parent down; M2 the same with the parent up; M3 vPC host, parent down, one up member per peer. In all
# three the member policy keeps ADMIN_STATE "true", the member pending is `no spanning-tree port type edge trunk` + `channel-group N force
# mode active` + `no shutdown`, and after the deploy the running member holds no `shutdown` and the switch is In-Sync. The measured stanzas
# are transposed to the harness names (port-channel10, Ethernet1/7 / Ethernet1/8). Mixed and multi-member previews are SYNTHETIC
# compositions of the measured up form and the measured down form. Real main(); only the controller boundary is intercepted.
# ====================================================================================================
E9, E10 = "Ethernet1/9", "Ethernet1/10"


def po_preview(case="M1", phase="pre_deploy", number="573", port="ethernet1/13", serial_fx=LEAF_B, mutate=None):
    m = measured(case, phase, serial_fx, number, port, IF7)
    if mutate:
        mutate(m)
    return H.preview(m["pending"], running=m["running"], expected=m["expected"])


def up_nv(port=IF7):
    nv = trunk_host_nv(port)
    nv["ADMIN_STATE"] = "true"
    return nv


# ================================================================== helper contract
@pytest.mark.parametrize("admin", ["true", "True", " TRUE ", True, "false", False])
def test_an_explicit_true_or_false_is_admitted_for_the_trunk_host_baseline(admin):
    nv = trunk_host_nv(IF7)
    nv["ADMIN_STATE"] = admin
    assert P.po_member_baseline_problems(P.TRUNK_HOST_POLICY, nv, P.MODE_HOST) == []


@pytest.mark.parametrize("admin", ["", None, "0", "1", "yes", "up", "shutdown"])
def test_an_unknown_administrative_state_is_refused_and_never_inferred(admin):
    nv = trunk_host_nv(IF7)
    nv["ADMIN_STATE"] = admin
    problems = P.po_member_baseline_problems(P.TRUNK_HOST_POLICY, nv, P.MODE_HOST)
    assert problems and "administrative state is unknown" in problems[0]


def test_absent_admin_state_is_refused():
    nv = trunk_host_nv(IF7)
    nv.pop("ADMIN_STATE")
    assert "administrative state is unknown" in P.po_member_baseline_problems(P.TRUNK_HOST_POLICY, nv, P.MODE_HOST)[0]


def test_the_other_baseline_rules_still_hold_for_an_up_member():
    nv = up_nv()
    nv["CONF"] = "no cdp enable"
    assert any("freeform CONF" in p for p in P.po_member_baseline_problems(P.TRUNK_HOST_POLICY, nv, P.MODE_HOST))
    assert "not covered" in P.po_member_baseline_problems("int_access_host", up_nv(), P.MODE_HOST)[0]
    # trunk secondary: a trunk member stays the known incident, admin up or down
    assert P.po_member_baseline_problems(P.TRUNK_HOST_POLICY, up_nv(), P.MODE_TRUNK_SECONDARY) == [P.PO_TS_TRUNK_MEMBER_INCIDENT]


def test_the_intended_member_keeps_its_own_up_state_whatever_the_parent():
    for parent_admin in (False, True):
        parent = P.po_host_nvpairs({"pvlan_mode": "host", "members": [IF7], "admin_state": parent_admin,
                                    "pvlan_association": [{"primary_vlan": 2210, "secondary_vlan": 2212}]}, H.PO)
        member = P.po_member_nvpairs(parent, up_nv())
        assert member["ADMIN_STATE"] == "true" and "no shutdown" in P.render(H.PO_MEMBER, member).scalars


def test_force_reassertion_on_an_up_member_stays_unmodeled():
    body = ["channel-group 10 force mode active"]
    up = P.Model({"switchport", "channel-group 10 mode active", "no shutdown"}, P.MODE_HOST, (), True)
    _body, problems = P.po_member_force_reassertion(body, up, up, {"po_number": "10", "pc_mode": "active"})
    assert any("re-asserting" in p for p in problems)


# ================================================================== regular port-channel through main()
def test_po_creation_with_an_up_member_deploys_on_the_measured_preview_and_keeps_the_member_state():
    ctrl = H.baseline_ctrl(up_nv())
    ctrl.previews = [po_preview()]
    status, result = H.run(ctrl, [H.po_item()])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1
    body = json.loads(ctrl.creates()[0][2])
    nv = (body[0] if isinstance(body, list) else body)["interfaces"][0]["nvPairs"]
    assert nv["MEMBER_INTERFACES"] == IF7 and nv["ADMIN_STATE"] == "false", "the parent's own state is the request, not the member's"
    assert ctrl.requests("POST", H.MODIFY) == [], "the module never writes the member: no shutdown / no shutdown remedy"


def test_po_creation_with_the_parent_up_deploys_on_the_measured_preview():
    ctrl = H.baseline_ctrl(up_nv())
    ctrl.previews = [po_preview("M2", number="574", port="ethernet1/14")]
    status, result = H.run(ctrl, [H.po_item(admin_state=True)])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.deploys()) == 1 and ctrl.requests("POST", H.MODIFY) == []


def test_po_creation_whose_pending_would_shut_the_up_member_never_deploys_and_reports_the_written_intent():
    ctrl = H.baseline_ctrl(up_nv())
    ctrl.previews = [po_preview(mutate=shut_the_member)]
    status, result = H.run(ctrl, [H.po_item()])
    assert status == "fail" and "pre-deploy gate" in result["msg"] and "'shutdown'" in result["msg"], result.get("msg")
    assert len(ctrl.creates()) == 1 and ctrl.deploys() == [] and "ALREADY changed" in result["msg"]


def test_po_creation_with_a_down_member_is_unchanged():
    ctrl = H.baseline_ctrl()
    ctrl.previews = [H.good_preview()]
    status, result = H.run(ctrl, [H.po_item()])
    assert status == "exit" and len(ctrl.deploys()) == 1, result.get("msg")


def test_po_repetition_after_the_up_join_writes_nothing():
    ctrl = H.baseline_ctrl(up_nv())
    ctrl.previews = [po_preview()]
    assert H.run(ctrl, [H.po_item()])[0] == "exit"
    nv = MU.member_nv(IF7)
    nv["ADMIN_STATE"] = "true"  # MEASURED: the member policy keeps "true" after the join
    ctrl.detail[IF7] = {"policy": H.PO_MEMBER, "nvPairs": nv}
    ctrl.next_invocation()
    ctrl.calls = []
    ctrl.previews = [po_preview(phase="post_deploy")]
    status, result = H.run(ctrl, [H.po_item()])
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.writes() == []


def test_po_with_members_in_different_states_keeps_each_one():
    # SYNTHETIC composition: Ethernet1/7 joins up (measured form), Ethernet1/9 joins down (measured form).
    ctrl = H.baseline_ctrl(up_nv())
    down = trunk_host_nv(E9)
    down["ADMIN_STATE"] = "false"
    ctrl.detail[E9] = {"policy": H.TRUNK, "nvPairs": down}
    m = measured("M1", "pre_deploy", LEAF_B, "573", "ethernet1/13", IF7)
    pend = m["pending"][:-1] + ["interface ethernet1/9", "  no spanning-tree port type edge trunk", "configure terminal",
                                "interface ethernet1/9", "  channel-group 10 force mode active", "  shutdown", "configure terminal"]
    running = m["running"] + V.member_running_baseline("Ethernet1/9")
    expected = m["expected"] + V.member_after("ethernet1/9")
    ctrl.previews = [H.preview(pend, running=running, expected=expected)]
    status, result = H.run(ctrl, [H.po_item(members=[IF7, E9])])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.requests("POST", H.MODIFY) == []


def test_po_member_addition_of_an_up_member_keeps_the_existing_down_member():
    ctrl = MU.seeded(members=(IF7,), spare=(E10,))
    ctrl.detail[E10]["nvPairs"]["ADMIN_STATE"] = "true"
    added = V.create_pending(E10, MU.PAIR)[len(V.po_stanza(MU.PAIR)):]
    added[[i for i, line in enumerate(added) if line.strip() == "shutdown"][-1]] = "  no shutdown"  # the measured up join form
    run = MU.strip_vpc(V.po_stanza(MU.PAIR)) + V.member_after(IF7, MU.PAIR) + [l for l in V.member_running_baseline(E10) if l.strip() != "shutdown"]
    exp = MU.strip_vpc(V.po_stanza(MU.PAIR)) + V.member_after(IF7, MU.PAIR) + [
        "  no shutdown" if l == "  shutdown" else l for l in V.member_after(E10, MU.PAIR)]
    ctrl.previews = [H.preview(added, running=run, expected=exp)]
    status, result = MU.run(ctrl, MU.item([E10]), "merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.po_modifies()) == 1 and ctrl.member_modifies() == [] and len(ctrl.deploys()) == 1


def test_po_lacp_rate_change_with_an_up_member_stays_refused_before_any_write():
    ctrl = H.baseline_ctrl(up_nv())
    status, result = H.run(ctrl, [H.po_item(lacp_rate="fast")])
    assert status == "fail" and "lacp_rate" in result["msg"] and "administratively down" in result["msg"], result.get("msg")
    assert ctrl.writes() == []


def test_po_deletion_with_an_up_member_no_longer_refuses_and_reaches_the_markdelete():
    # Supersedes the admin-down-only release: the up member is released to the fabric default; the full release lifecycle
    # is asserted in test_pvlan_member_admin.py. Here: the old refusal is gone and the deletion's first write is the mark-delete.
    ctrl = MU.seeded(members=(IF7,), spare=())
    ctrl.detail[IF7]["nvPairs"]["ADMIN_STATE"] = "true"
    status, result = H.run(ctrl, [{"name": H.PO_ITEM_NAME, "switch": [H.SWITCH_IP], "deploy": True}], state="deleted")
    assert "not administratively down" not in str(result.get("msg"))
    assert ctrl.writes() and "markdelete" in ctrl.writes()[0][1], ctrl.writes()


def test_vpc_creation_with_both_members_up_deploys_once_on_the_measured_previews():
    ctrl = V.baseline_ctrl()
    up_peers(ctrl)
    ctrl.vpc_previews[V.SN1] = [vpc_preview(V.SN1, V.M1, serial_fx=LEAF_B)]
    ctrl.vpc_previews[V.SN2] = [vpc_preview(V.SN2, V.M2, serial_fx=LEAF_A)]
    status, result = V.run_vpc(ctrl, [V.vpc_item()])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1 and sorted(ctrl.previews_asked()) == [V.SN1, V.SN2]
    assert ctrl.requests("POST", V.MODIFY) == []


def mixed_ctrl():
    ctrl = V.baseline_ctrl()
    up_peers(ctrl, peers=(V.SN1,))
    ctrl.vpc_previews[V.SN1] = [vpc_preview(V.SN1, V.M1, serial_fx=LEAF_B)]
    ctrl.vpc_previews[V.SN2] = [V.create_preview(V.SN2, V.M2)]
    return ctrl


def sent_nv(ctrl):
    body = json.loads(ctrl.creates()[0][2])
    return (body[0] if isinstance(body, list) else body)["interfaces"][0]["nvPairs"]


def test_vpc_creation_with_one_member_up_and_one_down_keeps_each_peer_state():
    ctrl = mixed_ctrl()
    status, result = V.run_vpc(ctrl, [V.vpc_item()])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.deploys()) == 1 and ctrl.requests("POST", V.MODIFY) == []


def test_vpc_mixed_states_with_the_switches_in_the_other_order_judge_each_member_on_its_own_serial():
    a, b = mixed_ctrl(), mixed_ctrl()
    assert V.run_vpc(a, [V.vpc_item()])[0] == "exit"
    status, result = V.run_vpc(b, [V.vpc_item(switches=[V.IP2, V.IP1], peer1_members=[V.M2], peer2_members=[V.M1])])
    assert status == "exit", result.get("msg")
    assert sent_nv(a) == sent_nv(b) and sent_nv(b)["PEER1_MEMBER_INTERFACES"] == V.M1


def test_vpc_peer2_pending_that_would_shut_its_up_member_stops_every_deploy():
    ctrl = V.baseline_ctrl()
    up_peers(ctrl)
    ctrl.vpc_previews[V.SN1] = [vpc_preview(V.SN1, V.M1, serial_fx=LEAF_B)]
    ctrl.vpc_previews[V.SN2] = [vpc_preview(V.SN2, V.M2, serial_fx=LEAF_A, mutate=shut_the_member)]
    status, result = V.run_vpc(ctrl, [V.vpc_item()])
    assert status == "fail" and V.SN2 in result["msg"] and "'shutdown'" in result["msg"], result.get("msg")
    assert len(ctrl.creates()) == 1 and ctrl.deploys() == [] and "ALREADY changed" in result["msg"]


def test_vpc_unreadable_peer_with_up_members_is_refused_before_any_write():
    ctrl = V.baseline_ctrl()
    up_peers(ctrl)
    ctrl.read_failures = {"/rest/interface/detail?serialNumber=" + V.SN2}
    status, result = V.run_vpc(ctrl, [V.vpc_item()])
    assert status == "fail" and "could not be read authoritatively" in result["msg"] and V.SN2 in result["msg"], result.get("msg")
    assert ctrl.writes() == []


def test_vpc_unknown_admin_state_on_one_peer_refuses_the_whole_vpc():
    ctrl = V.baseline_ctrl()
    up_peers(ctrl, peers=(V.SN1,))
    ctrl.nodes[V.SN2][V.M2]["nvPairs"].pop("ADMIN_STATE")
    status, result = V.run_vpc(ctrl, [V.vpc_item()])
    assert status == "fail" and "administrative state is unknown" in result["msg"] and V.SN2 in result["msg"], result.get("msg")
    assert ctrl.writes() == []


def test_vpc_lacp_rate_with_an_up_member_stays_refused_before_any_write():
    ctrl = V.baseline_ctrl()
    up_peers(ctrl)
    status, result = V.run_vpc(ctrl, [V.vpc_item(lacp_rate="fast")])
    assert status == "fail" and "lacp_rate" in result["msg"], result.get("msg")
    assert ctrl.writes() == []


def test_vpc_repetition_after_the_up_join_writes_nothing():
    ctrl = V.VpcController()
    for serial, port in ((V.SN1, V.M1), (V.SN2, V.M2)):
        ctrl.nodes[serial][port] = {"policy": V.TRUNK, "nvPairs": up_nv(port)}
    ctrl = ctrl.seed_vpc()  # the predicted save copies each member's own ADMIN_STATE (MEASURED "true" in M3)
    assert ctrl.nodes[V.SN1][V.M1]["nvPairs"]["ADMIN_STATE"] == "true"
    ctrl.next_invocation()
    ctrl.vpc_previews[V.SN1] = [vpc_preview(V.SN1, V.M1, phase="post_deploy", serial_fx=LEAF_B)]
    ctrl.vpc_previews[V.SN2] = [vpc_preview(V.SN2, V.M2, phase="post_deploy", serial_fx=LEAF_A)]
    status, result = V.run_vpc(ctrl, [V.vpc_item()])
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.writes() == []


def test_vpc_deletion_with_an_up_member_no_longer_refuses_and_reaches_the_markdelete():
    # Supersedes the admin-down-only release: see test_pvlan_member_admin.py for the full lifecycle.
    ctrl = V.VpcController()
    for serial, port in ((V.SN1, V.M1), (V.SN2, V.M2)):
        ctrl.nodes[serial][port] = {"policy": V.TRUNK, "nvPairs": up_nv(port)}
    ctrl = ctrl.seed_vpc()
    ctrl.next_invocation()
    status, result = V.run_vpc(ctrl, [V.vpc_del_item()], state="deleted")
    assert "not administratively down" not in str(result.get("msg"))
    assert len(ctrl.markdeletes()) == 1, result.get("msg")


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_admin_up_all_modes.py
# An administratively up member joins a PVLAN regular port-channel or vPC in promiscuous, trunk promiscuous and trunk
# secondary (on the access/routed bases prepared for it) and keeps its own state, member by member and peer by peer.
#
# OFFLINE ONLY: no lab measurement of these modes with an up member. The previews are the existing harnesses' down-member previews
# of each mode (measured for trunk secondary and for the promiscuous/trunk promiscuous creation form) with the member's admin line
# switched by the rule MEASURED for host (fixtures/pvlan_admin_state.json): the member pending and expected carry
# `no shutdown`; the running of an up switchport member has no `shutdown` line and an up routed port shows `no shutdown`; an up
# routed port carries the measured own child `no_shut_interface` instead of `shut_interface`. That switch is SYNTHETIC for these
# modes. Real main(); only the controller boundary is intercepted.
# ====================================================================================================
P_, TP, TS = "promiscuous", "trunk promiscuous", "trunk secondary"
ADMIN_MODES_E9 = "Ethernet1/9"


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


def test_the_up_rule_reproduces_the_measured_host_forms():
    """Guard of the SYNTHETIC switch: applied to the harness host preview it gives the member lines MEASURED in M1."""
    fx = load_case("pvlan_admin_up_join_measured")
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
def test_po_member_addition_of_an_up_member_keeps_the_existing_down_member_admin_modes(mode):
    profile, lines = G5.CASES[mode]
    ctrl = G5.existing(mode)
    ctrl.__class__ = MU.MembershipPo
    ctrl.detail[ADMIN_MODES_E9] = {"policy": P.TRUNK_HOST_POLICY, "nvPairs": admin(trunk_host_nv(ADMIN_MODES_E9), "true")}
    join = ["interface ethernet1/9", "  no spanning-tree port type edge trunk", "configure terminal",
            "interface ethernet1/9", "  channel-group 10 force mode active", "  no shutdown", "configure terminal"]
    e9_running = up_lines([l.replace("Ethernet1/7", "Ethernet1/9") for l in G5.RUNNING_MEMBER], ADMIN_MODES_E9, "running")
    e9_expected = up_lines([l.replace("ethernet1/7", "ethernet1/9") for l in G5.member_stanza(mode, lines)], ADMIN_MODES_E9, "expected")
    state = G5.po_stanza(mode, lines) + G5.member_stanza(mode, lines)
    ctrl.previews = [G5.preview(join, running=state + e9_running, expected=state + e9_expected)]
    status, result = run(ctrl, [G5.item(mode, members=[ADMIN_MODES_E9], **profile)], state="merged")
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
    status, result = E1_VPC.run_vpc(ctrl, [E1.item(mode)])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1 and sorted(ctrl.previews_asked()) == [SN1, SN2]
    assert E1.gate(result) == {"deploy": [(1, SN1, "deploy"), (2, SN2, "deploy")]}
    assert ctrl.requests("POST", "/rest/interface/modify") == [], "no member is written to make the join possible"


@pytest.mark.parametrize("mode", [P_, TP, TS])
def test_vpc_mixed_states_with_the_switches_reversed_send_the_same_intent(mode):
    a, b = e1_ctrl(mode, (SN1,)), e1_ctrl(mode, (SN1,))
    assert E1_VPC.run_vpc(a, [E1.item(mode)])[0] == "exit"
    swapped = {"peer1_members": [M2], "peer2_members": [M1]}
    if mode in (TP, TS):
        swapped.update({"peer1_native_vlan": "2302", "peer1_allowed_vlans": "2302", "peer2_native_vlan": "2301", "peer2_allowed_vlans": "2301"})
    status, result = E1_VPC.run_vpc(b, [E1.item(mode, switches=[IP2, IP1], **swapped)])
    assert status == "exit", result.get("msg")
    assert sent_nv(a) == sent_nv(b)


@pytest.mark.parametrize("mode", [P_, TP, TS])
def test_vpc_peer2_pending_that_would_shut_its_up_member_stops_every_deploy_admin_modes(mode):
    ctrl = e1_ctrl(mode)
    ctrl.vpc_previews[SN2] = [E1.create_preview(SN2, M2, mode, E1.PAIRS[mode], *E1.per_peer(mode, 1),
                                                baseline="access" if mode == TS else "trunk")]
    status, result = E1_VPC.run_vpc(ctrl, [E1.item(mode)])
    assert status == "fail" and SN2 in result["msg"] and "ALREADY changed" in result["msg"], result.get("msg")
    assert len(ctrl.creates()) == 1 and ctrl.deploys() == []


@pytest.mark.parametrize("mode", [P_, TP, TS])
def test_vpc_unreadable_peer_with_up_members_is_refused_before_any_write_admin_modes(mode):
    ctrl = e1_ctrl(mode)
    ctrl.read_failures = {"/rest/interface/detail?serialNumber=" + SN2}
    status, result = E1_VPC.run_vpc(ctrl, [E1.item(mode)])
    assert status == "fail" and "could not be read authoritatively" in result["msg"] and ctrl.writes() == [], result.get("msg")


@pytest.mark.parametrize("mode", [P_, TP, TS])
def test_vpc_unknown_admin_state_on_one_peer_refuses_the_whole_vpc_admin_modes(mode):
    ctrl = e1_ctrl(mode, (SN1,))
    ctrl.nodes[SN2][M2]["nvPairs"]["ADMIN_STATE"] = None
    status, result = E1_VPC.run_vpc(ctrl, [E1.item(mode)])
    assert status == "fail" and "administrative state is unknown" in result["msg"] and SN2 in result["msg"] and ctrl.writes() == []


def test_vpc_trunk_secondary_up_trunk_member_on_one_peer_is_still_the_known_incident():
    ctrl = e1_ctrl(TS)
    ctrl.nodes[SN2][M2] = {"policy": P.TRUNK_HOST_POLICY, "nvPairs": admin(trunk_host_nv(M2), "true")}
    status, result = E1_VPC.run_vpc(ctrl, [E1.item(TS)])
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
    status, result = E1_VPC.run_vpc(ctrl, [E1.item(TS)])
    assert status == "exit", result.get("msg")
    assert E1.gate(result) == {"deploy": [(1, SN1, "deploy"), (2, SN2, "deploy")]}


def test_vpc_trunk_secondary_up_routed_member_with_the_down_child_is_refused_before_any_write():
    ctrl = E1.routed_ctrl(M2)
    ctrl.nodes[SN2][M2]["nvPairs"]["ADMIN_STATE"] = "true"
    ctrl.vpc_previews[SN2] = [up_preview(ctrl.vpc_previews[SN2][0], M2, routed=True)]
    status, result = E1_VPC.run_vpc(ctrl, [E1.item(TS)])
    assert status == "fail" and "live policies" in result["msg"] and ctrl.writes() == [], result.get("msg")


@pytest.mark.parametrize("mode", [P_, TP, TS])
def test_vpc_repetition_with_up_members_writes_nothing(mode):
    ctrl = E1.seeded_ctrl(mode)
    for serial, port in ((SN1, M1), (SN2, M2)):
        ctrl.nodes[serial][port]["nvPairs"]["ADMIN_STATE"] = "true"
    E1.converged_previews(ctrl, mode)
    for serial, port in ((SN1, M1), (SN2, M2)):
        ctrl.vpc_previews[serial] = [up_preview(ctrl.vpc_previews[serial][0], port)]
    status, result = E1_VPC.run_vpc(ctrl, [E1.item(mode)])
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.writes() == []


@pytest.mark.parametrize("mode", [P_, TP, TS])
def test_vpc_deletion_with_an_up_member_no_longer_refuses_and_reaches_the_markdelete_admin_modes(mode):
    # Supersedes the admin-down-only release: the up member is released to the fabric default in every mode.
    ctrl = E1.seeded_ctrl(mode)
    ctrl.nodes[SN1][M1]["nvPairs"]["ADMIN_STATE"] = "true"
    status, result = E1_VPC.run_vpc(ctrl, [E1_VPC.vpc_del_item()], state="deleted")
    assert "not administratively down" not in str(result.get("msg"))
    assert len(ctrl.markdeletes()) == 1, result.get("msg")


@pytest.mark.parametrize("mode", [P_, TP, TS])
def test_vpc_lacp_rate_fast_with_an_up_member_stays_refused(mode):
    ctrl = e1_ctrl(mode)
    status, result = E1_VPC.run_vpc(ctrl, [E1.item(mode, lacp_rate="fast")])
    assert status == "fail" and "lacp_rate" in result["msg"] and ctrl.writes() == [], result.get("msg")


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_release_admin.py
# The release of a PVLAN port-channel / vPC member follows the fabric's host-interface default.
#
# Contract (the generic one, dcnm_intf_get_default_eth_payload): a host interface returned to its default takes ADMIN_STATE from the
# fabric nvPair HOST_INTF_ADMIN_STATE. The PVLAN release (deletion -- named or by an overridden sweep -- and a member removed by an
# update) now targets that value instead of always "false":
#   * HOST_INTF_ADMIN_STATE "true" (the NDFC default): the controller's release (MEASURED: int_trunk_host ADMIN_STATE "true")
#     already is the target, so no member write; a release that came back down is set up by the same single modify;
#   * "false": unchanged -- the measured up release is corrected to "false" before the deploy;
#   * unreadable / not a boolean: refused before any write (never defaulted);
#   * the member's OWN administrative state before the release no longer matters (up or down), exactly like the generic reset; an
#     unknown member state stays refused.
# Administrative state only: the operational link state is never read or asserted here.
#
# Harnesses: the measured Po release (its post-release preview: released member expected `no shutdown`), the membership Po/vPC
# harnesses and the vPC harness. The fabric default is the harness knob (`fabric_admin`). Real main(); only the controller boundary
# is intercepted.
# ====================================================================================================
UNREADABLE = ("maybe", None, "")


def released_up(resp, port):
    """The same preview with the released `port` expected UP: its expected `shutdown` becomes `no shutdown`, and the pending (which
    takes the device from the PVLAN member, running `shutdown`) carries `no shutdown` for it -- the shape MEASURED for the up release
    (HR-post: expected/pending `no shutdown`)."""
    entry = resp["DATA"][0]
    for key in ("expectedConfig", "pendingConfig"):
        lines, out, cur, seen = entry.get(key) or [], [], None, False
        for line in lines:
            if line.lower().startswith("interface "):
                if cur == port.lower() and key == "pendingConfig" and not seen:
                    out.append("  no shutdown")
                cur, seen = line.split(None, 1)[1].lower(), False
            elif cur == port.lower() and line.strip() == "shutdown":
                line, seen = "  no shutdown", True
            elif cur == port.lower() and line.strip() == "no shutdown":
                seen = True
            out.append(line)
        if cur == port.lower() and key == "pendingConfig" and not seen:
            out.append("  no shutdown")
        entry[key] = out
    return resp


def po_ctrl(fabric_admin, member_admin="false", **knobs):
    ctrl = G4.owned_ctrl(**knobs)
    ctrl.fabric_admin = fabric_admin
    ctrl.detail[G4.MEM]["nvPairs"]["ADMIN_STATE"] = member_admin
    return ctrl


def delete_po(ctrl, deploy=True):
    return run(ctrl, [{"name": "po502", "switch": [SWITCH_IP], "deploy": deploy}], state="deleted")


# ================================================================== regular port-channel, deletion
@pytest.mark.parametrize("member_admin", ["false", "true"])
def test_po_deletion_with_a_true_fabric_default_keeps_the_up_release_and_writes_no_member(member_admin):
    ctrl = po_ctrl("true", member_admin, previews=[G4.entry("HR-post")])
    status, result = delete_po(ctrl)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.write_kinds() == ["markdelete", "deploy"], "the measured up release IS the target: no member write"
    assert G4.PO not in ctrl.detail and ctrl.detail[G4.MEM]["policy"] == TRUNK and ctrl.detail[G4.MEM]["nvPairs"]["ADMIN_STATE"] == "true"
    record = [r for r in result["pvlan_po_release"] if r.get("member") == G4.MEM][0]
    assert record["member_modify"] == "not needed (already administratively up, the fabric's host default)"


@pytest.mark.parametrize("member_admin", ["false", "true"])
def test_po_deletion_with_a_false_fabric_default_corrects_the_release_whatever_the_member_was(member_admin):
    ctrl = po_ctrl("false", member_admin)
    status, result = delete_po(ctrl)
    assert status == "exit", result.get("msg")
    assert ctrl.write_kinds() == ["markdelete", "modify", "deploy"]
    assert ctrl.modify_bodies()[0][0]["interfaces"][0]["nvPairs"]["ADMIN_STATE"] == "false"
    assert ctrl.detail[G4.MEM]["nvPairs"]["ADMIN_STATE"] == "false"


def test_po_release_that_came_back_down_under_a_true_default_is_set_up_by_one_modify():
    ctrl = po_ctrl("true", previews=[G4.entry("HR-post")], released_nv=dict(G4.RELEASED, ADMIN_STATE="false"))
    status, result = delete_po(ctrl)
    assert status == "exit", result.get("msg")
    assert ctrl.write_kinds() == ["markdelete", "modify", "deploy"]
    body = ctrl.modify_bodies()[0][0]
    assert body["policy"] == TRUNK and body["interfaces"][0]["nvPairs"]["ADMIN_STATE"] == "true"
    assert "ADMIN_STATE false -> true" in [r for r in result["pvlan_po_release"] if r.get("member") == G4.MEM][0]["member_modify"]


@pytest.mark.parametrize("fabric_admin", UNREADABLE)
def test_po_deletion_with_an_unreadable_fabric_default_is_refused_before_any_write(fabric_admin):
    ctrl = po_ctrl(fabric_admin)
    status, result = delete_po(ctrl)
    assert status == "fail" and "HOST_INTF_ADMIN_STATE" in result["msg"] and ctrl.writes() == [], result.get("msg")


def test_po_deletion_saved_with_deploy_false_under_a_true_default_writes_only_the_markdelete():
    ctrl = po_ctrl("true", "true", previews=[G4.entry("HR-post")])
    status, result = delete_po(ctrl, deploy=False)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.write_kinds() == ["markdelete"], "no member write and NO deploy"
    assert [s for s in result.get("pvlan_saved", []) if s.get("operation") == "delete"], result.get("pvlan_saved")


def test_po_dropped_by_overridden_under_a_true_default_is_released_up_without_a_member_write():
    ctrl = RC.measured_po(po_ctrl("true", "true", previews=[G4.entry("HR-post")]))
    status, result = run(ctrl, [RC.lo(SWITCH_IP)], state="overridden")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert RC.writes(ctrl) == ["interface/markdelete", "globalInterface/deploy", "globalInterface", "globalInterface/deploy"]
    assert ctrl.detail[G4.MEM]["nvPairs"]["ADMIN_STATE"] == "true"


def test_the_extra_generic_path_refusal_was_secondary_to_the_failed_registration():
    """PO-3-chk listed, after the release refusals, `... holds int_port_channel_pvlan_host; a reset ... outside the port-channel request is
    not implemented`: the guard fires for a PVLAN object the preflight did NOT register. With the registration accepted (true default)
    the same drop exits without it; with a registration refusal (unreadable default) both appear."""
    ok = RC.measured_po(po_ctrl("true", "true", previews=[G4.entry("HR-post")]))
    status, result = run(ok, [RC.lo(SWITCH_IP)], state="overridden")
    assert status == "exit", result.get("msg")
    bad = RC.measured_po(po_ctrl("maybe", "true", previews=[G4.entry("HR-post")]))
    status, result = run(bad, [RC.lo(SWITCH_IP)], state="overridden")
    assert status == "fail" and "HOST_INTF_ADMIN_STATE" in result["msg"] and RC.writes(bad) == []


# ================================================================== regular port-channel, member removed by an update
@pytest.mark.parametrize("fabric_admin, modifies, final", [("true", 0, "true"), ("false", 1, "false")])
def test_po_member_removed_by_replaced_reaches_the_fabric_default(fabric_admin, modifies, final):
    ctrl = MU.seeded()
    ctrl.fabric_admin = fabric_admin
    ctrl.detail[MU.E9]["nvPairs"]["ADMIN_STATE"] = "true"
    pv = MU.fragments(kept=(MU.E7,), removed_trunk=(MU.E9,))
    ctrl.previews = [released_up(pv, MU.E9) if fabric_admin == "true" else pv]
    status, result = MU.run(ctrl, MU.item([MU.E7]), "replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.po_modifies()) == 1 and len(ctrl.member_modifies()) == modifies and len(ctrl.deploys()) == 1
    assert ctrl.detail[MU.E9]["policy"] == TRUNK and ctrl.detail[MU.E9]["nvPairs"]["ADMIN_STATE"] == final


# ================================================================== vPC
def vpc_up_previews(ctrl):
    V.delete_previews(ctrl)
    for serial, port in ((V.SN1, V.M1), (V.SN2, V.M2)):
        ctrl.vpc_previews[serial] = [released_up(ctrl.vpc_previews[serial][0], port)]


@pytest.mark.parametrize("member_admin", ["false", "true"])
def test_vpc_deletion_with_a_true_fabric_default_keeps_both_up_releases_without_member_writes(member_admin):
    ctrl = V.created_ctrl()
    for serial, port in ((V.SN1, V.M1), (V.SN2, V.M2)):
        ctrl.nodes[serial][port]["nvPairs"]["ADMIN_STATE"] = member_admin
    vpc_up_previews(ctrl)
    status, result = V.run_vpc(ctrl, [V.vpc_del_item()], state="deleted", fabric_admin="true")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.markdeletes()) == 1 and ctrl.modifies() == [], "both up releases are the target: no member write"
    assert all(ctrl.nodes[s][p]["nvPairs"]["ADMIN_STATE"] == "true" for s, p in ((V.SN1, V.M1), (V.SN2, V.M2)))
    assert result["pvlan_verification"]["vPC10"]["state"] == "verified"


@pytest.mark.parametrize("fabric_admin", UNREADABLE)
def test_vpc_deletion_with_an_unreadable_fabric_default_is_refused_before_any_write(fabric_admin):
    ctrl = V.created_ctrl()
    V.delete_previews(ctrl)
    status, result = V.run_vpc(ctrl, [V.vpc_del_item()], state="deleted", fabric_admin=fabric_admin)
    assert status == "fail" and "HOST_INTF_ADMIN_STATE" in result["msg"] and ctrl.writes() == [], result.get("msg")


def test_vpc_deletion_with_an_up_member_and_a_false_default_corrects_both_peers():
    ctrl = V.created_ctrl()
    ctrl.nodes[V.SN1][V.M1]["nvPairs"]["ADMIN_STATE"] = "true"
    V.delete_previews(ctrl)
    status, result = V.run_vpc(ctrl, [V.vpc_del_item()], state="deleted", fabric_admin="false")
    assert status == "exit", result.get("msg")
    V.release_only(ctrl)


def test_vpc_dropped_by_overridden_under_a_true_default_is_released_up_on_both_peers():
    ctrl = RC.vpc_ctrl()
    vpc_up_previews(ctrl)
    status, result = V.run_vpc(ctrl, [RC.lo(V.IP1)], state="overridden", fabric_admin="true")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.markdeletes()) == 1 and ctrl.modifies() == []


@pytest.mark.parametrize("fabric_admin, modifies, final", [("true", 0, "true"), ("false", 1, "false")])
def test_vpc_member_removed_by_replaced_reaches_the_fabric_default(fabric_admin, modifies, final):
    ctrl = MU.vpc_seeded({V.SN1: [V.M1, MU.E9P], V.SN2: [V.M2]})  # the member down (the harness's prior preview models it shut)
    MU.queue_peer(ctrl, V.SN1, kept=(V.M1,), removed_trunk=(MU.E9P,))
    MU.queue_peer(ctrl, V.SN2, kept=(V.M2,))
    if fabric_admin == "true":
        ctrl.vpc_previews[V.SN1][1] = released_up(ctrl.vpc_previews[V.SN1][1], MU.E9P)
    status, result = V.run_vpc(ctrl, [V.vpc_item(peer1_members=[V.M1], peer2_members=[V.M2])], state="replaced", fabric_admin=fabric_admin)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.member_modifies()) == modifies
    assert ctrl.nodes[V.SN1][MU.E9P]["policy"] == TRUNK and ctrl.nodes[V.SN1][MU.E9P]["nvPairs"]["ADMIN_STATE"] == final


# ================================================================== helper contract
@pytest.mark.parametrize("admin", ["true", "false"])
def test_helpers_target_the_given_state_and_reject_anything_else(admin):
    from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P
    model = P.released_member_model(admin)
    assert model["ADMIN_STATE"] == admin and dict(model, ADMIN_STATE="false") == P.PO_RELEASED_MEMBER_NV
    assert P.po_released_member_safety_problems(model, admin) == []
    other = "false" if admin == "true" else "true"
    assert P.po_released_member_safety_problems(model, other), "the other state is not safe for this target"
    assert P.po_released_member_payload(dict(model, ADMIN_STATE=other), "Ethernet1/9", "S", "F", admin)["interfaces"][0]["nvPairs"]["ADMIN_STATE"] == admin
    assert P.released_routed_children(admin) == (P.PO_ROUTED_RELEASE_CHILDREN_UP if admin == "true" else P.PO_ROUTED_RELEASE_CHILDREN_DOWN)
    with pytest.raises(ValueError):
        P.released_member_model("maybe")
    assert json.dumps(P.po_released_member_payload(model, "Ethernet1/9", "S", "F")["interfaces"][0]["nvPairs"]["ADMIN_STATE"]) == '"false"'


# ================================================================== V-8: vPC saved member removal, continued by a deploy-true repetition
@pytest.mark.parametrize("fabric_admin", ["true", "false"])
def test_vpc_member_removal_saved_with_deploy_false_is_completed_by_a_later_deploy_true_repetition(fabric_admin):
    ctrl = MU.vpc_seeded({V.SN1: [V.M1, MU.E9P], V.SN2: [V.M2]})
    # deploy false: no prior gate, ONE preview per peer (the saved update's validation)
    MU.queue_peer(ctrl, V.SN1, kept=(V.M1,), removed_trunk=(MU.E9P,))
    MU.queue_peer(ctrl, V.SN2, kept=(V.M2,))
    for serial in (V.SN1, V.SN2):
        ctrl.vpc_previews[serial] = ctrl.vpc_previews[serial][1:]
    if fabric_admin == "true":
        ctrl.vpc_previews[V.SN1][0] = released_up(ctrl.vpc_previews[V.SN1][0], MU.E9P)
    item = V.vpc_item(peer1_members=[V.M1], peer2_members=[V.M2])
    status, result = V.run_vpc(ctrl, [dict(item, deploy=False)], state="replaced", fabric_admin=fabric_admin)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert "DEPLOY" not in ctrl.order(), "saved: never deployed"
    saved_member_writes = len(ctrl.member_modifies())
    assert saved_member_writes == (0 if fabric_admin == "true" else 1)
    released_admin = ctrl.nodes[V.SN1][MU.E9P]["nvPairs"]["ADMIN_STATE"]
    assert released_admin == fabric_admin

    # ANOTHER process: nothing but the controller's state carries over; the device still joins Ethernet1/9 to port-channel10 on peer 1
    ctrl.next_invocation()
    for serial, kw in ((V.SN1, {"kept": (V.M1,), "removed_trunk": (MU.E9P,)}), (V.SN2, {"kept": (V.M2,)})):
        pv = MU.peer_preview(serial, **kw)
        if fabric_admin == "true" and serial == V.SN1:
            pv = released_up(pv, MU.E9P)
        ctrl.vpc_previews[serial] = [pv, json.loads(json.dumps(pv))]
    status, result = V.run_vpc(ctrl, [dict(item, deploy=True)], state="replaced", fabric_admin=fabric_admin)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.order().count("DEPLOY") == 1, ctrl.order()
    assert len(ctrl.member_modifies()) == saved_member_writes, "the resumed member is never released (written) again"
    assert ctrl.parent_modifies() == [] or len(ctrl.parent_modifies()) == 1
    assert any(s.get("state") == "completing the saved removal" and s.get("kind") == "vpc" for s in result["pvlan_saved"]), result.get("pvlan_saved")
    assert ctrl.nodes[V.SN1][MU.E9P]["nvPairs"]["ADMIN_STATE"] == fabric_admin


def test_vpc_repetition_with_a_foreign_pending_port_is_still_refused():
    """A pending port that is NOT a saved removal of this vPC (not joined on the device / not released) keeps the outside refusal."""
    ctrl = MU.vpc_seeded({V.SN1: [V.M1], V.SN2: [V.M2]}, spare={V.SN1: [MU.E9P]})
    for serial, kw in ((V.SN1, {"kept": (V.M1,)}), (V.SN2, {"kept": (V.M2,)})):
        pv = MU.peer_preview(serial, **kw)
        if serial == V.SN1:
            pv["DATA"][0]["pendingConfig"] = list(pv["DATA"][0]["pendingConfig"]) + ["interface %s" % MU.E9P, "  description foreign"]
            pv["DATA"][0]["status"] = "Out-of-Sync"
        ctrl.vpc_previews[serial] = [pv, json.loads(json.dumps(pv))]
    status, result = V.run_vpc(ctrl, [V.vpc_item(peer1_members=[V.M1], peer2_members=[V.M2])], state="replaced", fabric_admin="true")
    assert status == "fail" and "outside" in result["msg"] and "DEPLOY" not in ctrl.order(), result.get("msg")


def test_vpc_saved_member_removal_repeated_with_deploy_false_writes_nothing_and_stays_reported_pending(monkeypatch):
    ctrl = MU.vpc_seeded({V.SN1: [V.M1, MU.E9P], V.SN2: [V.M2]})
    MU.queue_peer(ctrl, V.SN1, kept=(V.M1,), removed_trunk=(MU.E9P,))
    MU.queue_peer(ctrl, V.SN2, kept=(V.M2,))
    for serial in (V.SN1, V.SN2):
        ctrl.vpc_previews[serial] = ctrl.vpc_previews[serial][1:]
    item = V.vpc_item(peer1_members=[V.M1], peer2_members=[V.M2])
    status, result = V.run_vpc(ctrl, [dict(item, deploy=False)], state="replaced", fabric_admin="false")
    assert status == "exit", result.get("msg")
    ctrl.next_invocation()
    before = len(ctrl.writes())
    monkeypatch.setattr(V, "INVENTORY", dict((ip, dict(entry, ccStatus="Out-of-Sync")) for ip, entry in V.INVENTORY.items()))
    for serial, kw in ((V.SN1, {"kept": (V.M1,), "removed_trunk": (MU.E9P,)}), (V.SN2, {"kept": (V.M2,)})):
        ctrl.vpc_previews[serial] = [MU.peer_preview(serial, **kw)]
    status, result = V.run_vpc(ctrl, [dict(item, deploy=False)], state="replaced", fabric_admin="false")
    assert status == "exit" and result["changed"] is False and len(ctrl.writes()) == before, result.get("msg")
    assert [s for s in result["pvlan_saved"] if s.get("kind") == "vpc" and s["state"].startswith("saved, awaiting deployment")], result.get("pvlan_saved")


# ================================================================== live shape: the marked parent vPC stays listed
def saved_vpc_with_listed_parent():
    ctrl = RC.vpc_ctrl()
    ctrl.children_marked_deleted = True
    ctrl.parent_marked_listed = True  # MEASURED live: the parent stays listed, markDeleted True, no policy
    RC.vpc_queue(ctrl, 1)
    status, result = V.run_vpc(ctrl, [V.vpc_del_item(deploy=False)], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    ctrl.next_invocation()
    return ctrl


def test_saved_vpc_deletion_with_the_parent_still_listed_is_reported_pending_by_a_deploy_false_repeat():
    ctrl = saved_vpc_with_listed_parent()
    before = len(ctrl.writes())
    RC.vpc_queue(ctrl, 1)
    status, result = V.run_vpc(ctrl, [V.vpc_del_item(deploy=False)], state="deleted")
    assert status == "exit" and result["changed"] is False and len(ctrl.writes()) == before, result.get("msg")
    assert [s for s in result.get("pvlan_saved", []) if s.get("state", "").startswith("saved, awaiting deployment")], result.get("pvlan_saved")


def test_saved_vpc_deletion_with_the_parent_still_listed_is_completed_by_deploy_true_without_a_second_markdelete():
    ctrl = saved_vpc_with_listed_parent()
    marks = len(ctrl.markdeletes())
    RC.vpc_queue(ctrl, 2)
    status, result = V.run_vpc(ctrl, [V.vpc_del_item(deploy=True)], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.markdeletes()) == marks and "DEPLOY" in ctrl.order(), ctrl.order()
