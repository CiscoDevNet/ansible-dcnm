"""Readiness: the regular-Po rules reused on the PVLAN vPC path, per leg and per peer.

NOT LIVE TESTED on a vPC. Every preview below is DERIVED: the host stanzas of the existing vPC harness (SYNTHETIC, from the templates)
carrying the pending FORMS measured on a REGULAR host port-channel (NDFC 12.6.0.267 / NX-OS 10.5(5)
  * M2 / T2-R2 S1 (fixtures/pvlan_po_t2_measured.json): an update that renders member lines re-emits the member block WITH
    `channel-group N force mode M` for the port-channel the member already belongs to;
  * Fixtures/pvlan_po_m1_measured.json: MTU jumbo -> default = ONLY `interface port-channelN` / `no mtu 9216`, no member block;
  * Fixtures/pvlan_po_mr_measured.json: MTU default -> jumbo = ONLY the port-channel stanza re-emitted with `mtu 9216`;
  * T2 R1: the controller releases the member with the MTU of the port-channel intent, not always jumbo.
Whether a vPC child/member behaves the same is what T3 measures; nothing here certifies the controller.
G4 (two-phase release) is a module ordering property: proved here with the harness's per-serial knobs.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

import pytest

from .test_dcnm_intf_pvlan_harness import trunk_host_nv
from .test_dcnm_intf_pvlan_vpc_harness import (
    IP1,
    IP2,
    M1,
    M2,
    MODIFY,
    PAIR,
    SN1,
    SN2,
    VPC,
    VpcController,
    created_ctrl,
    delete_preview,
    member_after,
    po_stanza,
    preview,
    release_only,
    run_vpc,
    vpc_del_item,
    vpc_item,
)

PEERS = ((SN1, M1), (SN2, M2))
FORCE = "  channel-group 10 force mode active"


def without_mtu(lines):
    return [l for l in lines if l.strip() != "mtu 9216"]


def gate(result):
    out = {}
    for rec in result.get("pvlan_gate") or []:
        out.setdefault(rec["site"], []).append((rec["peer"], rec["serial"], rec["targets"].get(VPC)))
    return dict((k, sorted(v)) for k, v in out.items())


def releases(result):
    return [r for r in result.get("pvlan_vpc_release") or [] if "member_write" in r or "member_writes" in r]


def jumbo_state(port, member_extra=(), po_extra=()):
    return po_stanza() + ["  " + x for x in po_extra] + member_after(port) + ["  " + x for x in member_extra]


def default_ctrl():
    """A created vPC whose parent intent and device are both at MTU default (the MR starting point), SYNTHETIC."""
    ctrl = created_ctrl()
    ctrl.parents[VPC]["nvPairs"]["MTU"] = "default"
    ctrl._expand_children(ctrl.parents[VPC]["nvPairs"])
    return ctrl


def queue(ctrl, before, after, pendings):
    """Per serial: the prior converged preview, then the DERIVED update preview."""
    for serial, port in PEERS:
        b, a = before(port), after(port)
        ctrl.vpc_previews[serial] = [preview([], serial=serial, running=b, expected=b), preview(pendings[serial](port), serial=serial, running=b, expected=a)]


# ---------------------------------------------------------------- DERIVED pending forms
def cdp_pending(port, force=FORCE):
    """M2/S1 form on the member: the block re-emitted with the force re-assertion + its own explicit line."""
    return ["interface %s" % port.lower()] + ([force] if force else []) + ["  no cdp enable"]


def mtu_default_pending(_port):
    """M1 form: the child Po withdraws `mtu 9216`; no member block."""
    return ["interface port-channel10", "  no mtu 9216"]


def mtu_jumbo_pending(_port):
    """MR form: the child Po stanza re-emitted with `mtu 9216`; no member block."""
    return po_stanza()


# ================================================================== G1: force re-assertion on an existing member, per leg
def test_g1_member_update_re_emitting_its_own_force_is_accepted_on_both_peers_and_deploys_once():
    ctrl = created_ctrl()
    queue(ctrl, jumbo_state, lambda p: jumbo_state(p, ["no cdp enable"]), {SN1: cdp_pending, SN2: cdp_pending})
    status, res = run_vpc(ctrl, [vpc_item(enable_cdp=False)])
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert len(ctrl.modifies()) == 1 and len(ctrl.deploys()) == 1 and ctrl.creates() == []
    assert gate(res)["deploy"] == [(1, SN1, "deploy"), (2, SN2, "deploy")]


def test_g1_the_explicit_member_line_is_still_required_beside_the_force():
    ctrl = created_ctrl()
    queue(ctrl, jumbo_state, lambda p: jumbo_state(p, ["no cdp enable"]), {SN1: cdp_pending, SN2: lambda p: ["interface %s" % p.lower(), FORCE]})
    status, res = run_vpc(ctrl, [vpc_item(enable_cdp=False)])
    assert status == "fail" and ctrl.deploys() == [], res.get("msg")
    assert "no cdp enable" in res["msg"] and "peer 2" in res["msg"]


@pytest.mark.parametrize(
    "foreign",
    [
        pytest.param("  channel-group 11 force mode active", id="other-po-number"),
        pytest.param("  channel-group 10 force mode passive", id="other-pc-mode"),
    ],
)
def test_g1_a_foreign_force_on_one_peer_is_refused_and_nothing_is_deployed(foreign):
    ctrl = created_ctrl()
    queue(ctrl, jumbo_state, lambda p: jumbo_state(p, ["no cdp enable"]), {SN1: cdp_pending, SN2: lambda p: cdp_pending(p, force=foreign)})
    status, res = run_vpc(ctrl, [vpc_item(enable_cdp=False)])
    assert status == "fail" and ctrl.deploys() == [], res.get("msg")
    assert "peer 2" in res["msg"]


def test_g1_control_the_persisted_form_is_a_line_of_the_intended_state_and_stays_ordinary_validation():
    """Not a force: `channel-group 10 mode active` is already in the intended member, which the unchanged validate_transition() accepts
    as a restatement (pre-existing behaviour, not introduced by this change)."""
    ctrl = created_ctrl()
    persisted = "  channel-group 10 mode active"
    queue(ctrl, jumbo_state, lambda p: jumbo_state(p, ["no cdp enable"]), {SN1: cdp_pending, SN2: lambda p: cdp_pending(p, force=persisted)})
    status, res = run_vpc(ctrl, [vpc_item(enable_cdp=False)])
    assert status == "exit" and len(ctrl.deploys()) == 1, res.get("msg")


def test_g1_force_twice_in_one_member_block_is_refused():
    ctrl = created_ctrl()
    queue(ctrl, jumbo_state, lambda p: jumbo_state(p, ["no cdp enable"]), {SN1: cdp_pending, SN2: lambda p: cdp_pending(p) + [FORCE]})
    status, res = run_vpc(ctrl, [vpc_item(enable_cdp=False)])
    assert status == "fail" and ctrl.deploys() == [] and "2 times" in res["msg"], res.get("msg")


def test_g1_force_on_a_member_that_is_up_is_refused():
    ctrl = created_ctrl()
    for serial, port in PEERS:
        ctrl.nodes[serial][port]["nvPairs"]["ADMIN_STATE"] = "true"

    def up(port, extra=()):
        return [l if l.strip() != "shutdown" else "  no shutdown" for l in member_after(port)] + ["  " + x for x in extra]

    queue(ctrl, lambda p: po_stanza() + up(p), lambda p: po_stanza() + up(p, ["no cdp enable"]), {SN1: cdp_pending, SN2: cdp_pending})
    status, res = run_vpc(ctrl, [vpc_item(enable_cdp=False)])
    assert status == "fail" and ctrl.deploys() == [], res.get("msg")


def test_g1_the_member_of_another_po_on_the_device_is_refused():
    ctrl = created_ctrl()

    def other(port, extra=()):
        return po_stanza() + [l.replace("channel-group 10", "channel-group 11") for l in member_after(port)] + ["  " + x for x in extra]

    for serial, port in PEERS:
        if serial == SN2:
            b, a = other(port), jumbo_state(port, ["no cdp enable"])
        else:
            b, a = jumbo_state(port), jumbo_state(port, ["no cdp enable"])
        ctrl.vpc_previews[serial] = [preview([], serial=serial, running=b, expected=b), preview(cdp_pending(port), serial=serial, running=b, expected=a)]
    status, res = run_vpc(ctrl, [vpc_item(enable_cdp=False)])
    assert status == "fail" and ctrl.deploys() == [] and ctrl.modifies() == [], res.get("msg")


# ================================================================== G2: member MTU inherited from THIS leg's child Po
def test_g2_mtu_jumbo_to_default_measured_m1_form_is_accepted_on_both_peers():
    ctrl = created_ctrl()
    queue(ctrl, jumbo_state, lambda p: without_mtu(jumbo_state(p)), {SN1: mtu_default_pending, SN2: mtu_default_pending})
    status, res = run_vpc(ctrl, [vpc_item(mtu="default")])
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert len(ctrl.modifies()) == 1 and len(ctrl.deploys()) == 1
    assert json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]["MTU"] == "default"


def test_g2_mtu_default_to_jumbo_measured_mr_form_is_accepted_on_both_peers():
    ctrl = default_ctrl()
    queue(ctrl, lambda p: without_mtu(jumbo_state(p)), jumbo_state, {SN1: mtu_jumbo_pending, SN2: mtu_jumbo_pending})
    status, res = run_vpc(ctrl, [vpc_item(mtu="jumbo")])
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert len(ctrl.modifies()) == 1 and len(ctrl.deploys()) == 1


def test_g2_combined_s1_like_update_force_plus_mtu_default_is_accepted():
    ctrl = created_ctrl()

    def pend(port):
        return mtu_default_pending(port) + cdp_pending(port)

    queue(ctrl, jumbo_state, lambda p: without_mtu(jumbo_state(p, ["no cdp enable"])), {SN1: pend, SN2: pend})
    status, res = run_vpc(ctrl, [vpc_item(mtu="default", enable_cdp=False)])
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert len(ctrl.deploys()) == 1


def test_g2_serial_isolation_peer1_child_proof_never_covers_peer2():
    """Peer 2's child Po carries NO MTU withdrawal: its member's `mtu 9216` is unexplained there, whatever peer 1 proves."""
    ctrl = created_ctrl()
    queue(ctrl, jumbo_state, lambda p: without_mtu(jumbo_state(p)), {SN1: mtu_default_pending, SN2: lambda p: []})
    status, res = run_vpc(ctrl, [vpc_item(mtu="default")])
    assert status == "fail" and ctrl.deploys() == [], res.get("msg")
    assert "peer 2 (%s): Ethernet1/8" % SN2 in res["msg"] and "peer 1 (" not in res["msg"]


def test_g2_peer_order_peer2_proof_never_covers_peer1():
    ctrl = created_ctrl()
    queue(ctrl, jumbo_state, lambda p: without_mtu(jumbo_state(p)), {SN1: lambda p: [], SN2: mtu_default_pending})
    status, res = run_vpc(ctrl, [vpc_item(mtu="default")])
    assert status == "fail" and ctrl.deploys() == [], res.get("msg")
    assert "peer 1" in res["msg"]


def test_g2_a_refused_parent_never_lends_its_mtu_to_the_member():
    """The child Po's pending carries the withdrawal AND an unexplained line: the child is refused, so the member stays refused too."""
    ctrl = created_ctrl()

    def pend(port):
        return mtu_default_pending(port) + ["  speed 10000"]

    queue(ctrl, jumbo_state, lambda p: without_mtu(jumbo_state(p)), {SN1: pend, SN2: mtu_default_pending})
    status, res = run_vpc(ctrl, [vpc_item(mtu="default")])
    assert status == "fail" and ctrl.deploys() == [], res.get("msg")
    assert "Ethernet1/7" in res["msg"] or "ethernet1/7" in res["msg"].lower()


@pytest.mark.parametrize(
    "pend",
    [
        pytest.param(lambda p: ["interface port-channel10", "  mtu 1500"], id="parent-other-mtu"),
        pytest.param(lambda p: ["interface port-channel10", "  no mtu 9216", "  no mtu 9216"], id="withdrawal-twice"),
        pytest.param(lambda p: ["interface port-channel10", "  no mtu 9216", "interface %s" % p.lower(), "  mtu 1500"], id="member-own-conflicting-mtu"),
    ],
)
def test_g2_conflicting_mtu_forms_are_refused(pend):
    ctrl = created_ctrl()
    queue(ctrl, jumbo_state, lambda p: without_mtu(jumbo_state(p)), {SN1: pend, SN2: pend})
    status, res = run_vpc(ctrl, [vpc_item(mtu="default")])
    assert status == "fail" and ctrl.deploys() == [], res.get("msg")


def test_g2_member_expected_with_a_different_mtu_is_refused():
    ctrl = created_ctrl()

    def after(port):
        return without_mtu(po_stanza()) + [l if l.strip() != "mtu 9216" else "  mtu 1500" for l in member_after(port)]

    queue(ctrl, jumbo_state, after, {SN1: mtu_default_pending, SN2: mtu_default_pending})
    status, res = run_vpc(ctrl, [vpc_item(mtu="default")])
    assert status == "fail" and ctrl.deploys() == [], res.get("msg")


def test_g2_explicit_member_withdrawal_stays_ordinary_validation():
    ctrl = created_ctrl()

    def pend(port):
        return mtu_default_pending(port) + ["interface %s" % port.lower(), "  no mtu 9216"]

    queue(ctrl, jumbo_state, lambda p: without_mtu(jumbo_state(p)), {SN1: pend, SN2: pend})
    status, res = run_vpc(ctrl, [vpc_item(mtu="default")])
    assert status == "exit" and len(ctrl.deploys()) == 1, res.get("msg")


# ================================================================== G3: the FRESH release of each member models the deletion
class ReleaseMtu(VpcController):
    """The controller releases each member with the MTU given per serial (default from a port-channel intent, as measured), SYNTHETIC."""

    def __init__(self, mtu, admin=None):
        super(ReleaseMtu, self).__init__()
        self.release_mtu = mtu
        self.release_admin = admin or {}

    def __call__(self, mod, method, path, data=None):
        resp = super(ReleaseMtu, self).__call__(mod, method, path, data)
        if method == "DELETE" and path.endswith("/rest/interface/markdelete"):
            for serial, port in PEERS:
                nv = self.nodes[serial][port]["nvPairs"]
                nv["MTU"] = self.release_mtu.get(serial, nv["MTU"])
                if serial in self.release_admin:
                    nv["ADMIN_STATE"] = self.release_admin[serial]
        return resp


def release_ctrl(mtu=None, admin=None):
    ctrl = ReleaseMtu(mtu or {}, admin).seed_baseline().seed_vpc()
    ctrl.next_invocation()
    return ctrl


def released_delete_preview(serial, port, jumbo):
    """The delete preview of ONE peer: released stanza at the fresh MTU; for a default release the member's `mtu 9216` must go (DERIVED)."""
    entry = delete_preview(serial, port)
    if not jumbo:
        e = entry["DATA"][0] if isinstance(entry.get("DATA"), list) else None
        target = e if e is not None else entry
        target["expectedConfig"] = without_mtu(target["expectedConfig"])
        target["pendingConfig"] = target["pendingConfig"] + ["  no mtu 9216"]
    return entry


def queue_delete(ctrl, jumbo=(True, True)):
    for (serial, port), j in zip(PEERS, jumbo):
        ctrl.vpc_previews[serial] = [released_delete_preview(serial, port, j)]


def test_g3_release_at_default_is_the_member_model_and_is_reported_as_restoration_delta():
    ctrl = release_ctrl({SN1: "default", SN2: "default"})
    queue_delete(ctrl, (False, False))
    status, res = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and res["changed"] is True, res.get("msg")
    release_only(ctrl)
    assert len(ctrl.deploys()) == 1 and res["pvlan_verification"][VPC]["state"] == "verified"
    recs = releases(res)
    assert [r["serial"] for r in recs] == [SN1, SN2]
    for r in recs:
        assert r["member_write"] == "confirmed" and r["restoration_delta"] == {"MTU": {"released": "default", "release_model": "jumbo"}}
    for serial, port in PEERS:
        assert ctrl.nodes[serial][port]["nvPairs"]["MTU"] == "default", "jumbo is never imposed"


def test_g3_release_at_jumbo_keeps_an_empty_restoration_delta():
    ctrl = release_ctrl()
    queue_delete(ctrl)
    status, res = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert [r["restoration_delta"] for r in releases(res)] == [{}, {}]


def test_g3_mixed_release_each_peer_judged_by_its_own_fresh_model():
    ctrl = release_ctrl({SN2: "default"})
    queue_delete(ctrl, (True, False))
    status, res = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert [r["restoration_delta"] for r in releases(res)] == [{}, {"MTU": {"released": "default", "release_model": "jumbo"}}]


def test_g3_a_preview_built_for_the_other_peers_release_is_refused():
    """Peer 2 is released at default but its preview still expects the jumbo stanza: the fresh model of THAT peer decides."""
    ctrl = release_ctrl({SN2: "default"})
    queue_delete(ctrl, (True, True))
    status, res = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and ctrl.deploys() == [], res.get("msg")
    assert "peer 2" in res["msg"]


def test_g3_already_down_release_uses_its_fresh_read_and_writes_nothing():
    ctrl = release_ctrl()
    ctrl.release_admin_up = False
    queue_delete(ctrl)
    status, res = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert ctrl.modifies() == [] and len(ctrl.deploys()) == 1
    assert [(r["serial"], r["member_write"]) for r in releases(res)] == [(SN1, "not needed"), (SN2, "not needed")]


def test_g3_already_down_at_default_on_one_peer_only():
    ctrl = release_ctrl({SN1: "default"}, admin={SN1: "false"})
    queue_delete(ctrl, (False, True))
    status, res = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert [(r["serial"], r["member_write"]) for r in releases(res)] == [(SN1, "not needed"), (SN2, "confirmed")]
    assert releases(res)[0]["restoration_delta"] == {"MTU": {"released": "default", "release_model": "jumbo"}}
    bodies = release_only(ctrl, count=1)
    assert bodies[0][0]["interfaces"][0]["ifName"] == M2


@pytest.mark.parametrize(
    "key,value",
    [("ALLOWED_VLANS", "all"), ("NATIVE_VLAN", "5"), ("CONF", "lldp transmit")],
)
def test_g3_an_unsafe_fresh_release_stops_before_any_member_write_and_any_deploy(key, value):
    class Unsafe(ReleaseMtu):
        def __call__(self, mod, method, path, data=None):
            resp = super(Unsafe, self).__call__(mod, method, path, data)
            if method == "DELETE" and path.endswith("/rest/interface/markdelete"):
                self.nodes[SN2][M2]["nvPairs"][key] = value
            return resp

    ctrl = Unsafe({}).seed_baseline().seed_vpc()
    ctrl.next_invocation()
    queue_delete(ctrl)
    status, res = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and ctrl.modifies() == [] and ctrl.deploys() == [], res.get("msg")
    rec = res["pvlan_vpc_release"][-1]
    assert rec["peer"] == 2 and rec["member_writes"] == {SN1: "pending", SN2: "pending"} and key in res["msg"]
    assert len(ctrl.markdeletes()) == 1 and "mark-delete of %s (confirmed" % VPC in res["msg"], "never 'zero writes' globally"


# ================================================================== G4: both proved before the first modify; non-atomic per-serial state
def test_g4_invalid_peer2_is_found_before_peer1_is_written():
    ctrl = release_ctrl()
    ctrl.policies_extra[SN2] = [
        dict(entityName="Ethernet1/60", entityType="INTERFACE", templateName="int_eth", source=VPC, deleted=False, policyId="R", serialNumber=SN2)
    ]
    queue_delete(ctrl)
    status, res = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and ctrl.modifies() == [] and ctrl.deploys() == [], res.get("msg")
    assert res["pvlan_vpc_release"][-1]["member_writes"] == {SN1: "pending", SN2: "pending"}


def test_g4_second_modify_error_after_a_confirmed_first_names_each_serial_and_deploys_nothing():
    ctrl = release_ctrl()
    ctrl.member_modify_fail = {SN2}
    queue_delete(ctrl)
    status, res = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and ctrl.deploys() == [], res.get("msg")
    rec = res["pvlan_vpc_release"][-1]
    assert rec["member_writes"] == {SN1: "confirmed", SN2: "uncertain"} and rec["peer"] == 2
    assert "Member writes per serial: %s=confirmed, %s=uncertain" % (SN1, SN2) in res["msg"]
    assert [json.loads(c[2])[0]["interfaces"][0]["serialNumber"] for c in ctrl.modifies()] == [SN1, SN2]


@pytest.mark.parametrize(
    "answer",
    [
        pytest.param({"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}, id="http-500"),
        pytest.param({"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": []}, id="207-without-items"),
    ],
)
def test_g4_second_modify_uncertain_answer_after_a_confirmed_first(answer):
    ctrl = release_ctrl()
    ctrl.modify_responses = [None, answer]
    queue_delete(ctrl)
    status, res = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and ctrl.deploys() == [], res.get("msg")
    assert res["pvlan_vpc_release"][-1]["member_writes"] == {SN1: "confirmed", SN2: "uncertain"}


def test_g4_incomplete_readback_of_the_second_member_stops_before_the_deploy():
    class LostRead(VpcController):
        def __call__(self, mod, method, path, data=None):
            resp = super(LostRead, self).__call__(mod, method, path, data)
            if method == "POST" and path.endswith(MODIFY) and SN2 in data:
                self.read_failures.add("/rest/interface?serialNumber=%s" % SN2)
            return resp

    ctrl = LostRead().seed_baseline().seed_vpc()
    ctrl.next_invocation()
    queue_delete(ctrl)
    status, res = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and ctrl.deploys() == [], res.get("msg")
    rec = res["pvlan_vpc_release"][-1]
    assert rec["phase"] == "at the member readback" and rec["member_writes"] == {SN1: "confirmed", SN2: "confirmed"}


def test_g4_pair_order_is_the_controllers_whatever_the_playbook_order():
    ctrl = release_ctrl()
    queue_delete(ctrl)
    item = vpc_del_item()
    item["switch"] = [IP2, IP1]
    status, res = run_vpc(ctrl, [item], state="deleted")
    assert status == "exit", res.get("msg")
    assert [json.loads(c[2])[0]["interfaces"][0]["serialNumber"] for c in ctrl.modifies()] == [SN1, SN2]
    assert ctrl.order().index("DEPLOY") > max(i for i, x in enumerate(ctrl.order()) if x == "MODIFY")


# ================================================================== recovery: delete from an UNAPPLIED intent (MTU default saved, not deployed)
def test_delete_from_an_unapplied_mtu_default_intent_releases_at_default_and_verifies():
    ctrl = release_ctrl({SN1: "default", SN2: "default"})
    ctrl.parents[VPC]["nvPairs"]["MTU"] = "default"
    for serial, port in PEERS:
        po = ctrl.nodes[serial]["port-channel10"]["nvPairs"]
        po["MTU"] = "default"  # the intent changed; the device (previews) still holds `mtu 9216`
    queue_delete(ctrl, (False, False))
    status, res = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert res["pvlan_verification"][VPC]["state"] == "verified" and len(ctrl.deploys()) == 1


def test_an_update_on_an_unapplied_intent_is_still_refused():
    ctrl = created_ctrl()
    ctrl.parents[VPC]["nvPairs"]["MTU"] = "default"
    ctrl._expand_children(ctrl.parents[VPC]["nvPairs"])
    for serial, port in PEERS:  # the device still holds the jumbo stanzas: the saved intent was never applied
        ctrl.vpc_previews[serial] = [preview(mtu_default_pending(port), serial=serial, running=jumbo_state(port), expected=without_mtu(jumbo_state(port)))]
    status, res = run_vpc(ctrl, [vpc_item(mtu="default", enable_cdp=False)])
    assert status == "fail" and ctrl.writes() == [], res.get("msg")


def test_release_nvpairs_of_the_harness_are_the_measured_trunk_host_baseline():
    """Guard of the derivation: the released member starts from the harness's measured int_trunk_host baseline (jumbo)."""
    assert trunk_host_nv(M1)["MTU"] == "jumbo" and PAIR == SN1 + "~" + SN2
