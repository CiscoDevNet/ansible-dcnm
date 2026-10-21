"""ADMIN-UP-JOIN: a free int_trunk_host member whose administrative intent is already UP joins a PVLAN regular port-channel or vPC and
keeps its own state; every other member keeps its own. This file is the MEASURED host series; the other modes (ADMIN-UP-ALL-MODES,
offline) are in test_dcnm_intf_pvlan_admin_up_all_modes.py.

MEASURED basis (fixtures/pvlan_admin_up_join_measured.json, NDFC 12.6.0.267 / NX-OS 10.5(5), direct legacy writes with the module's own
create bodies): M1 regular Po host, parent down; M2 the same with the parent up; M3 vPC host, parent down, one up member per peer. In all
three the member policy keeps ADMIN_STATE "true", the member pending is `no spanning-tree port type edge trunk` + `channel-group N force
mode active` + `no shutdown`, and after the deploy the running member holds no `shutdown` and the switch is In-Sync. The measured stanzas
are transposed to the harness names (port-channel10, Ethernet1/7 / Ethernet1/8). Mixed and multi-member previews are SYNTHETIC
compositions of the measured up form and the measured down form. Real main(); only the controller boundary is intercepted.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import os

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from . import test_dcnm_intf_pvlan_po_host as H
from . import test_dcnm_intf_pvlan_vpc_harness as V
from . import test_dcnm_intf_pvlan_member_updates as MU
from .test_dcnm_intf_pvlan_harness import IF7, trunk_host_nv

FX = json.load(open(os.path.join(os.path.dirname(__file__), "fixtures", "pvlan_admin_up_join_measured.json")))
LEAF_A, LEAF_B = "<SERIAL_LEAF_A>", "<SERIAL_LEAF_B>"
E9, E10 = "Ethernet1/9", "Ethernet1/10"


def transpose(lines, number, port, to_port):
    """A measured stanza list renamed to the harness: port-channel<number> -> port-channel10, its channel-group and vpc ids -> 10."""
    out = []
    for line in lines:
        line = line.replace("port-channel%s" % number, "port-channel10").replace("channel-group %s " % number, "channel-group 10 ")
        line = line.replace("vpc %s" % number, "vpc 10").replace("interface %s" % port, "interface %s" % to_port.lower())
        out.append(line)
    return out


def measured(case, phase, serial, number, port, to_port):
    m = FX[case][phase][serial]
    return dict((k, transpose(m[k], number, port, to_port)) for k in ("pending", "expected", "running"))


def po_preview(case="M1", phase="pre_deploy", number="573", port="ethernet1/13", serial_fx=LEAF_B, mutate=None):
    m = measured(case, phase, serial_fx, number, port, IF7)
    if mutate:
        mutate(m)
    return H.preview(m["pending"], running=m["running"], expected=m["expected"])


def vpc_preview(serial, to_port, phase="pre_deploy", serial_fx=LEAF_A, mutate=None):
    m = measured("M3", phase, serial_fx, "575", "ethernet1/16", to_port)
    if mutate:
        mutate(m)
    return V.preview(m["pending"], serial=serial, running=m["running"], expected=m["expected"])


def up_nv(port=IF7):
    nv = trunk_host_nv(port)
    nv["ADMIN_STATE"] = "true"
    return nv


def shut_the_member(m):
    """The pending a controller would produce if it shut the joining member (never measured): its `no shutdown` becomes `shutdown`."""
    idx = max(i for i, line in enumerate(m["pending"]) if line.strip() == "no shutdown")
    m["pending"][idx] = "  shutdown"


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
    # is asserted in test_dcnm_intf_pvlan_release_admin.py. Here: the old refusal is gone and the deletion's first write is the mark-delete.
    ctrl = MU.seeded(members=(IF7,), spare=())
    ctrl.detail[IF7]["nvPairs"]["ADMIN_STATE"] = "true"
    status, result = H.run(ctrl, [{"name": H.PO_ITEM_NAME, "switch": [H.SWITCH_IP], "deploy": True}], state="deleted")
    assert "not administratively down" not in str(result.get("msg"))
    assert ctrl.writes() and "markdelete" in ctrl.writes()[0][1], ctrl.writes()


# ================================================================== vPC through main()
def up_peers(ctrl, peers=(V.SN1, V.SN2)):
    for serial in peers:
        port = V.M1 if serial == V.SN1 else V.M2
        ctrl.nodes[serial][port]["nvPairs"]["ADMIN_STATE"] = "true"


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
    # Supersedes the admin-down-only release: see test_dcnm_intf_pvlan_release_admin.py for the full lifecycle.
    ctrl = V.VpcController()
    for serial, port in ((V.SN1, V.M1), (V.SN2, V.M2)):
        ctrl.nodes[serial][port] = {"policy": V.TRUNK, "nvPairs": up_nv(port)}
    ctrl = ctrl.seed_vpc()
    ctrl.next_invocation()
    status, result = V.run_vpc(ctrl, [V.vpc_del_item()], state="deleted")
    assert "not administratively down" not in str(result.get("msg"))
    assert len(ctrl.markdeletes()) == 1, result.get("msg")
