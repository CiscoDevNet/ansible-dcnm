"""vPC release prevalidation of members released already down, and the bounded extension of the inherited member MTU rule
to the SAME supported PVLAN mode on parent and member (host, promiscuous, trunk promiscuous, trunk secondary).

NOT LIVE TESTED for the three non-host modes. Every preview below is DERIVED: the existing per-mode harness stanzas (SYNTHETIC, from
the templates: test_dcnm_intf_pvlan_po_g1 / _po_g5_next_modes for a regular Po, test_dcnm_intf_pvlan_vpc_modes_e1 for a vPC)
carrying the pending FORMS measured for HOST only (`no mtu 9216` on the port-channel only; the port-channel stanza re-emitted with
`mtu 9216`; the same per vPC peer). Whether NX-OS propagates the MTU to the member in the other modes is not measured; these
fixtures prove only the module's decision rule, never the device.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .test_dcnm_intf_pvlan_harness import preview as po_preview
from .test_dcnm_intf_pvlan_harness import run as po_run
from .test_dcnm_intf_pvlan_harness import SWITCH_IP
from .test_dcnm_intf_pvlan_po_g1 import member_stanza, po_stanza
from .test_dcnm_intf_pvlan_po_g5_next_modes import CASES, existing
from .test_dcnm_intf_pvlan_po_host import PO, PO_ITEM_NAME
from .test_dcnm_intf_pvlan_vpc_harness import IP1, IP2, M1, M2, SN1, SN2, VPC, preview, run_vpc
from .test_dcnm_intf_pvlan_vpc_modes_e1 import PAIRS, member_after, per_peer, seeded_ctrl
from .test_dcnm_intf_pvlan_vpc_modes_e1 import po_stanza as vpc_po_stanza
from .test_dcnm_intf_pvlan_vpc_r5 import ReleaseMtu, queue_delete, release_ctrl, releases
from .test_dcnm_intf_pvlan_vpc_harness import vpc_del_item

MODES = sorted(CASES)  # the three non-host modes of the existing per-mode harness
PEERS = ((SN1, M1), (SN2, M2))


def without_mtu(lines):
    return [l for l in lines if l.strip() != "mtu 9216"]


# ================================================================== already-down members are validated in phase A
class UnsafeDown(ReleaseMtu):
    """The controller releases ONE peer's member already administratively down but unsafe (generalized)."""

    def __init__(self, serial, port, key, value):
        super(UnsafeDown, self).__init__({})
        self.target = (serial, port, key, value)

    def __call__(self, mod, method, path, data=None):
        resp = super(UnsafeDown, self).__call__(mod, method, path, data)
        if method == "DELETE" and path.endswith("/rest/interface/markdelete"):
            serial, port, key, value = self.target
            nv = self.nodes[serial][port]["nvPairs"]
            nv["ADMIN_STATE"] = "false"
            nv[key] = value
        return resp


@pytest.mark.parametrize("serial, port, peer", [(SN1, M1, 1), (SN2, M2, 2)])
@pytest.mark.parametrize("key, value", [("ALLOWED_VLANS", "all"), ("NATIVE_VLAN", "5"), ("CONF", "lldp transmit")])
def test_f1_an_unsafe_member_released_already_down_stops_before_any_member_write_on_either_peer(serial, port, peer, key, value):
    ctrl = UnsafeDown(serial, port, key, value).seed_baseline().seed_vpc()
    ctrl.next_invocation()
    queue_delete(ctrl)
    status, res = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail", res.get("msg")
    assert ctrl.modifies() == [] and ctrl.deploys() == [], "no member write and no deploy on any peer"
    assert len(ctrl.markdeletes()) == 1 and "mark-delete of %s (confirmed" % VPC in res["msg"], "the mark-delete stays counted"
    rec = res["pvlan_vpc_release"][-1]
    assert rec["peer"] == peer and "already administratively down" in res["msg"] and key in res["msg"]
    assert rec["phase"] == "while proving the released member before any member write"
    assert "confirmed" not in rec["member_writes"].values() and "uncertain" not in rec["member_writes"].values()
    assert ctrl.nodes[serial][port]["nvPairs"][key] == value, "the unsafe value is never auto-repaired"


def test_f1_the_architect_probe_now_refuses_in_phase_a_with_zero_member_modifies():
    ctrl = UnsafeDown(SN2, M2, "ALLOWED_VLANS", "all").seed_baseline().seed_vpc()
    ctrl.next_invocation()
    queue_delete(ctrl)
    status, res = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    rec = res["pvlan_vpc_release"][-1]
    assert (status, len(ctrl.modifies()), len(ctrl.deploys())) == ("fail", 0, 0)
    assert rec["member_writes"] == {SN1: "pending", SN2: "pending"}  # peer1 (still up) was proved first; peer2 refused before any write


def test_f1_control_safe_already_down_on_both_peers_still_deploys_with_zero_member_writes():
    ctrl = release_ctrl()
    ctrl.release_admin_up = False
    queue_delete(ctrl)
    status, res = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and ctrl.modifies() == [] and len(ctrl.deploys()) == 1, res.get("msg")
    assert [r["member_write"] for r in releases(res)] == ["not needed", "not needed"]


@pytest.mark.parametrize("mtu", ["default", "jumbo"])
def test_f1_control_safe_already_down_at_either_mtu_on_one_peer(mtu):
    ctrl = release_ctrl({SN1: mtu}, admin={SN1: "false"})
    queue_delete(ctrl, (mtu == "jumbo", True))
    status, res = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and len(ctrl.modifies()) == 1 and len(ctrl.deploys()) == 1, res.get("msg")
    assert [(r["serial"], r["member_write"]) for r in releases(res)] == [(SN1, "not needed"), (SN2, "confirmed")]
    assert releases(res)[0]["restoration_delta"] == ({} if mtu == "jumbo" else {"MTU": {"released": "default", "release_model": "jumbo"}})


def test_f1_control_uncertain_second_write_after_a_safe_already_down_first():
    ctrl = release_ctrl(admin={SN1: "false"})
    ctrl.member_modify_fail = {SN2}
    queue_delete(ctrl)
    status, res = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and ctrl.deploys() == [], res.get("msg")
    assert res["pvlan_vpc_release"][-1]["member_writes"] == {SN1: "not needed", SN2: "uncertain"}


# ================================================================== mode extension, regular port-channel (DERIVED previews)
def po_mtu_preview(mode, lines, direction, member_running=None, member_expected=None, pend=None, po_extra=()):
    po_j, mem_j = po_stanza(mode, lines), member_stanza(mode, lines)
    if direction == "withdraw":
        running, expected = po_j + mem_j, without_mtu(po_j) + without_mtu(mem_j)
        pending = ["interface port-channel10", "  no mtu 9216"]
    else:
        running, expected = without_mtu(po_j) + without_mtu(mem_j), po_j + mem_j
        pending = list(po_j)
    if member_running is not None:
        running = running[: len(po_j) - (0 if direction == "withdraw" else 1)] + member_running
    if member_expected is not None:
        expected = expected[: len(expected) - len(mem_j) + (0 if direction == "add" else 1)] + member_expected
    pending = (pend if pend is not None else pending) + list(po_extra)
    return po_preview(pending, running=running, expected=expected)


def po_item(mode, **profile):
    return {"name": PO_ITEM_NAME, "type": "pc", "switch": [SWITCH_IP], "deploy": True, "profile": dict({"mode": "pvlan", "pvlan_mode": mode}, **profile)}


def po_ctrl(mode, mtu="jumbo"):
    c = existing(mode)
    c.detail[PO]["nvPairs"]["MTU"] = mtu
    return c


@pytest.mark.parametrize("mode", MODES)
def test_po_mode_withdraw_mtu_jumbo_to_default_same_mode_deploys(mode):
    c = po_ctrl(mode)
    c.previews = [po_mtu_preview(mode, CASES[mode][1], "withdraw")]
    status, res = po_run(c, [po_item(mode, mtu="default")], state="merged")
    assert status == "exit" and res["changed"] is True and len(c.deploys()) == 1, res.get("msg")
    assert c.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]["MTU"] == "default"


@pytest.mark.parametrize("mode", MODES)
def test_po_mode_add_mtu_default_to_jumbo_same_mode_deploys(mode):
    c = po_ctrl(mode, mtu="default")
    c.previews = [po_mtu_preview(mode, CASES[mode][1], "add")]
    status, res = po_run(c, [po_item(mode, mtu="jumbo")], state="merged")
    assert status == "exit" and res["changed"] is True and len(c.deploys()) == 1, res.get("msg")


def _member_variant(mode, lines, transform):
    return [transform(l) for l in member_stanza(mode, lines)]


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize(
    "case",
    [
        "member-other-mode",
        "member-other-po",
        "member-admin-up",
        "parent-invalid",
        "member-explicit-other-mtu",
        "member-expected-other-mtu",
        "parent-other-mtu",
    ],
)
def test_po_mode_negatives_are_refused_without_deploy(mode, case):
    lines = CASES[mode][1]
    c = po_ctrl(mode)
    kw = {}
    if case == "member-other-mode":
        other = "host" if mode != "host" else "promiscuous"
        kw["member_running"] = [l.replace("private-vlan %s" % mode, "private-vlan %s" % other) for l in member_stanza(mode, lines)]
    elif case == "member-other-po":
        kw["member_running"] = _member_variant(mode, lines, lambda l: l.replace("channel-group 10", "channel-group 11"))
    elif case == "member-admin-up":
        kw["member_running"] = _member_variant(mode, lines, lambda l: "  no shutdown" if l.strip() == "shutdown" else l)
    elif case == "parent-invalid":
        kw["po_extra"] = ["  speed 10000"]
    elif case == "member-explicit-other-mtu":
        kw["pend"] = ["interface port-channel10", "  no mtu 9216", "interface ethernet1/7", "  mtu 1500"]
    elif case == "member-expected-other-mtu":
        kw["member_expected"] = [l if l.strip() != "mtu 9216" else "  mtu 1500" for l in member_stanza(mode, lines)]
    elif case == "parent-other-mtu":
        kw["pend"] = ["interface port-channel10", "  mtu 1500"]
    c.previews = [po_mtu_preview(mode, lines, "withdraw", **kw)]
    status, res = po_run(c, [po_item(mode, mtu="default")], state="merged")
    assert status == "fail" and c.deploys() == [], res.get("msg")


# ================================================================== mode extension, vPC (per peer, DERIVED previews)
def vpc_states(mode, i, port, jumbo=True):
    native, allowed = per_peer(mode, i)
    st = vpc_po_stanza(mode, PAIRS[mode], native, allowed) + member_after(port, mode, PAIRS[mode], native, allowed)
    return st if jumbo else without_mtu(st)


def vpc_mtu_queue(ctrl, mode, direction, pend_override=None):
    for i, (serial, port) in enumerate(PEERS):
        before, after = (vpc_states(mode, i, port, True), vpc_states(mode, i, port, False))
        if direction == "add":
            before, after = after, before
        native, allowed = per_peer(mode, i)
        pend = ["interface port-channel10", "  no mtu 9216"] if direction == "withdraw" else vpc_po_stanza(mode, PAIRS[mode], native, allowed)
        if pend_override and serial in pend_override:
            pend = pend_override[serial]
        ctrl.vpc_previews[serial] = [preview([], serial=serial, running=before, expected=before), preview(pend, serial=serial, running=before, expected=after)]


def vpc_item(mode, **profile):
    return {
        "name": "vpc10",
        "type": "vpc",
        "switch": [IP1, IP2],
        "deploy": True,
        "profile": dict({"mode": "pvlan", "pvlan_mode": mode, "peer1_pcid": 10, "peer2_pcid": 10}, **profile),
    }


def vpc_ctrl(mode, mtu="jumbo"):
    ctrl = seeded_ctrl(mode)
    ctrl.parents[VPC]["nvPairs"]["MTU"] = mtu
    ctrl._expand_children(ctrl.parents[VPC]["nvPairs"])
    ctrl.next_invocation()
    return ctrl


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("direction", ["withdraw", "add"])
def test_vpc_mode_mtu_both_directions_same_mode_deploys_on_both_peers(mode, direction):
    ctrl = vpc_ctrl(mode, "jumbo" if direction == "withdraw" else "default")
    vpc_mtu_queue(ctrl, mode, direction)
    status, res = run_vpc(ctrl, [vpc_item(mode, mtu="default" if direction == "withdraw" else "jumbo")])
    assert status == "exit" and res["changed"] is True and len(ctrl.deploys()) == 1, res.get("msg")
    assert json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]["MTU"] == ("default" if direction == "withdraw" else "jumbo")


@pytest.mark.parametrize("mode", MODES)
def test_vpc_mode_wrong_peer_proof_never_covers_the_other_peer(mode):
    ctrl = vpc_ctrl(mode)
    vpc_mtu_queue(ctrl, mode, "withdraw", pend_override={SN2: []})
    status, res = run_vpc(ctrl, [vpc_item(mode, mtu="default")])
    assert status == "fail" and ctrl.deploys() == [], res.get("msg")
    assert "peer 2 (%s)" % SN2 in res["msg"] and "peer 1 (" not in res["msg"]


# ================================================================== the helper itself: same mode, no transition (unit, DERIVED models)
def _models(mode_obs, mode_des, parent_obs, parent_des, direction="withdraw"):
    lines = CASES.get(parent_obs, (None, ["switchport private-vlan host-association 2210 2212"]))[1]
    po_run_lines = po_stanza(parent_obs, lines)
    if direction == "add":
        po_run_lines = without_mtu(po_run_lines)
    entry = {"runningConfig": po_run_lines}
    cg = "channel-group 10 mode active"
    obs = P.Model(
        {"switchport", "switchport mode private-vlan %s" % mode_obs, cg, "shutdown"} | ({"mtu 9216"} if direction == "withdraw" else set()), mode_obs, (), True
    )
    des = P.Model(
        {"switchport", "switchport mode private-vlan %s" % mode_des, cg, "shutdown"} | (set() if direction == "withdraw" else {"mtu 9216"}), mode_des, (), True
    )
    pdes_scalars = {"switchport", "switchport mode private-vlan %s" % parent_des, "shutdown"} | (set() if direction == "withdraw" else {"mtu 9216"})
    ctx = {
        "po_number": "10",
        "pc_mode": "active",
        "parent": "port-channel10",
        "parent_ok": True,
        "parent_desired": P.Model(pdes_scalars, parent_des, (), True),
        "parent_vocabulary": None,
        "parent_body": ["no mtu 9216"] if direction == "withdraw" else ["mtu 9216"],
    }
    return entry, obs, des, ctx


@pytest.mark.parametrize("mode", list(P.PVLAN_MODES))
@pytest.mark.parametrize("direction", ["withdraw", "add"])
def test_unit_same_supported_mode_is_inherited_in_both_directions(mode, direction):
    entry, obs, des, ctx = _models(mode, mode, mode, mode, direction)
    state, inherited = P.po_member_mtu_inherited_state(entry, obs, des, [], ctx)
    assert inherited is True and (("mtu 9216" in state.scalars) == (direction == "add"))


@pytest.mark.parametrize(
    "mobs, mdes, pobs, pdes",
    [
        ("promiscuous", "promiscuous", "host", "host"),  # parent and member in different modes
        ("trunk promiscuous", "trunk promiscuous", "promiscuous", "promiscuous"),
        ("promiscuous", "trunk promiscuous", "promiscuous", "trunk promiscuous"),  # both change mode
        ("trunk secondary", "host", "trunk secondary", "host"),
        ("promiscuous", "promiscuous", "promiscuous", "trunk promiscuous"),  # only the parent changes mode
        ("promiscuous", "isolated", "promiscuous", "promiscuous"),  # a value outside the enums
    ],
)
def test_unit_mode_mismatch_or_transition_is_never_inherited(mobs, mdes, pobs, pdes):
    entry, obs, des, ctx = _models(mobs, mdes, pobs, pdes)
    state, inherited = P.po_member_mtu_inherited_state(entry, obs, des, [], ctx)
    assert inherited is False and state is obs


@pytest.mark.parametrize("mode", list(P.PVLAN_MODES))
def test_unit_other_guards_are_unchanged_for_every_mode(mode):
    entry, obs, des, ctx = _models(mode, mode, mode, mode)
    assert P.po_member_mtu_inherited_state(entry, obs, des, ["mtu 1500"], ctx)[1] is False  # explicit member MTU command
    assert P.po_member_mtu_inherited_state(entry, obs, des, [], dict(ctx, parent_ok=False))[1] is False  # parent not validated
    assert P.po_member_mtu_inherited_state(entry, obs, des, [], dict(ctx, po_number="11"))[1] is False  # another port-channel
    up = P.Model((obs.scalars - {"shutdown"}) | {"no shutdown"}, obs.list_kind, (), True)
    assert P.po_member_mtu_inherited_state(entry, up, des, [], ctx)[1] is False  # member up
