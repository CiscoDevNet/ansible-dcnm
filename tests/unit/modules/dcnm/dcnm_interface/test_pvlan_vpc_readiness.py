"""vPC PVLAN readiness per leg and peer, read diagnostics and readback."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import hashlib
import json
import pytest

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

from .helpers.ethernet_controller import trunk_host_nv
from .helpers.vpc_controller import IP1
from .helpers.vpc_controller import IP2
from .helpers.vpc_controller import M1
from .helpers.vpc_controller import M2
from .helpers.vpc_controller import MODIFY
from .helpers.vpc_controller import PAIR
from .helpers.vpc_controller import SN1
from .helpers.vpc_controller import SN2
from .helpers.vpc_controller import VPC
from .helpers.vpc_controller import VpcController
from .helpers.vpc_controller import created_ctrl
from .helpers.vpc_controller import member_after
from .helpers.vpc_controller import po_stanza
from .helpers.ethernet_controller import preview
from .helpers.vpc_controller import release_only
from .helpers.vpc_controller import run_vpc
from .helpers.vpc_controller import vpc_del_item
from .helpers.vpc_controller import vpc_item
from .helpers.vpc_controller import PEERS
from .helpers.vpc_controller import ReleaseMtu
from .helpers.vpc_controller import queue_delete
from .helpers.vpc_controller import release_ctrl
from .helpers.vpc_controller import releases
from .helpers.vpc_controller import without_mtu
from .helpers import membership as MU
from .helpers import vpc_controller as V
from .helpers.ethernet_controller import TRUNK
from .helpers.vpc_controller import CANARY
from .helpers.vpc_controller import CanaryController
from .helpers.vpc_controller import mutating
from .helpers.vpc_controller import refused
from .helpers.vpc_controller import DEPLOY
from .helpers.vpc_controller import converged_previews
from .helpers.vpc_controller import create_pending
from .helpers.vpc_controller import create_previews
from .helpers.vpc_controller import delete_previews
from .helpers.vpc_controller import member_running_baseline


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_vpc_r5.py
# Readiness: the regular-Po rules reused on the PVLAN vPC path, per leg and per peer.
#
# NOT LIVE TESTED on a vPC. Every preview below is DERIVED: the host stanzas of the existing vPC harness (SYNTHETIC, from the templates)
# carrying the pending FORMS measured on a REGULAR host port-channel (NDFC 12.6.0.267 / NX-OS 10.5(5)
#   * M2 / T2-R2 S1 (fixtures/pvlan_po_delete_saved.json#pvlan_po_t2_measured): an update that renders member lines re-emits the member block WITH
#     `channel-group N force mode M` for the port-channel the member already belongs to;
#   * Fixtures/pvlan_po_member_mtu.json#pvlan_po_m1_measured: MTU jumbo -> default = ONLY `interface port-channelN` / `no mtu 9216`, no member block;
#   * Fixtures/pvlan_po_member_mtu.json#pvlan_po_mr_measured: MTU default -> jumbo = ONLY the port-channel stanza re-emitted with `mtu 9216`;
#   * T2 R1: the controller releases the member with the MTU of the port-channel intent, not always jumbo.
# Whether a vPC child/member behaves the same is what T3 measures; nothing here certifies the controller.
# G4 (two-phase release) is a module ordering property: proved here with the harness's per-serial knobs.
# ====================================================================================================
FORCE = "  channel-group 10 force mode active"


def gate(result):
    out = {}
    for rec in result.get("pvlan_gate") or []:
        out.setdefault(rec["site"], []).append((rec["peer"], rec["serial"], rec["targets"].get(VPC)))
    return dict((k, sorted(v)) for k, v in out.items())


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


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_vpc_read_diagnostics.py
# vPC PVLAN creation / member join refused on an unreadable peer: the refusal names the peer, the read stage and a controlled reason.
#
# NOT LIVE TESTED. Real main() through the existing vPC harness (helpers/vpc_controller: VpcController + run_vpc) and the
# membership double of test_pvlan_po_members; one trigger per case at the external boundary. Every refusal keeps zero
# mutating requests for the whole invocation; the general refusal lines are kept; the cause appears once per peer and stage. Reasons are
# controlled text (status number, field name, entry index, failure category): a fake canary placed in failing responses never appears.
# The earlier, separate refusal of a total detail failure on the pair's FIRST serial (read before this preflight) is not changed here.
# ====================================================================================================
VPC_READ_DIAG_SN1, VPC_READ_DIAG_SN2, VPC_READ_DIAG_M1, VPC_READ_DIAG_M2 = V.SN1, V.SN2, V.M1, V.M2
SUMMARY, BULK, POLICIES = "/rest/interface/detail?serialNumber=", "/rest/interface?serialNumber=", "/control/policies/switches/"
ABSENT = "the absence of the port-channel and of the vPC children could not be established authoritatively"
UNREAD = "its current state could not be read authoritatively"


def cause(serial, stage, reason):
    return "{0} on {1}: {2} {1} could not be read authoritatively ({3})".format(V.VPC, serial, stage, reason)


def generic(serial, member):
    """The two general lines (kept). The member label is the module's resolved spelling (controller spelling when the bulk detail was
    read, the playbook spelling otherwise), so these two lines are compared case-insensitively; cause lines are compared exactly."""
    return {("{0} on {1}: {2}".format(V.VPC, serial, ABSENT)).lower(), ("{0} on {1}: {2}".format(member, serial, UNREAD)).lower()}


def folded(got):
    return {l.lower() for l in got}


# ------------------------------------------------------------------ positive control: unchanged requests and payloads
def test_coherent_creation_keeps_its_exact_request_sequence_and_payloads():
    ctrl = V.baseline_ctrl()
    V.create_previews(ctrl)
    status, result = V.run_vpc(ctrl, [V.vpc_item()])
    assert status == "exit" and result["changed"] is True, result
    calls = [(m, p.split("/appcenter/cisco/ndfc/api/v1/lan-fabric")[-1]) for m, p, _d in ctrl.calls]
    writes = [d for m, _p, d in ctrl.calls if m in ("POST", "PUT", "DELETE")]
    # measured on the unmodified base 3bfa68cb with the same double: 26 calls, create + deploy (unchanged through d76094b0).
    # PREWRITE-REUSE: the pre-write vPC compare reuses this invocation's own complete generic reads of the same physical serial:
    # the policy list of FDO00000001 and FDO00000002 and the bulk detail of FDO00000002 are no longer read twice -> 23 calls.
    # The writes (create + deploy payloads) are byte-identical to the base.
    assert len(calls) == 23
    assert hashlib.sha256(json.dumps(calls).encode()).hexdigest()[:16] == "052300081d2ad0bf"
    assert hashlib.sha256(json.dumps(writes).encode()).hexdigest()[:16] == "9482b18d85c7f831"


# ------------------------------------------------------------------ creation: each read stage, one peer, peer isolation
def test_summary_http_status_names_peer_stage_and_status_only_for_that_peer():
    ctrl = CanaryController().seed_baseline()
    ctrl.canary_failures.add(SUMMARY + VPC_READ_DIAG_SN1)
    got = refused(ctrl)
    assert generic(VPC_READ_DIAG_SN1, VPC_READ_DIAG_M1) <= folded(got)
    assert cause(VPC_READ_DIAG_SN1, "the interface summary of", "HTTP 500 after 3 attempt(s)") in got
    assert not any(VPC_READ_DIAG_SN2 in l for l in got)


def test_summary_entry_without_markDeleted_on_a_foreign_port_names_the_entry_and_field():
    ctrl = V.baseline_ctrl()
    ctrl.nodes[VPC_READ_DIAG_SN1]["Ethernet1/40"] = {"policy": TRUNK, "nvPairs": trunk_host_nv("Ethernet1/40")}
    orig = ctrl._peer_summary

    def summary(serial):
        out = orig(serial)
        for e in out:
            if serial == VPC_READ_DIAG_SN1 and e["ifName"] == "Ethernet1/40":
                e.pop("markDeleted")
                e["alias"] = CANARY
        return out

    ctrl._peer_summary = summary
    got = refused(ctrl)
    assert generic(VPC_READ_DIAG_SN1, VPC_READ_DIAG_M1) <= folded(got)
    assert cause(VPC_READ_DIAG_SN1, "the interface summary of", "entry 0: field markDeleted missing") in got


def test_bulk_record_without_nvPairs_names_the_record_once_per_peer():
    ctrl = V.baseline_ctrl()
    orig = ctrl._peer_details

    def details(serial):
        out = orig(serial)
        if serial == VPC_READ_DIAG_SN2:
            out.append({"policy": "int_trunk_host", "interfaces": [{"serialNumber": VPC_READ_DIAG_SN2, "ifName": "Ethernet1/42", "note": CANARY}]})
        return out

    ctrl._peer_details = details
    got = refused(ctrl)
    detail = [l for l in got if "the interface detail of" in l]
    assert detail == [cause(VPC_READ_DIAG_SN2, "the interface detail of", "record 1.0 lacks the nvPairs object")], detail
    assert generic(VPC_READ_DIAG_SN2, VPC_READ_DIAG_M2) <= folded(got) and not any(VPC_READ_DIAG_SN1 in l for l in got)


def test_bulk_duplicate_record_is_named():
    ctrl = V.baseline_ctrl()
    orig = ctrl._peer_details

    def details(serial):
        out = orig(serial)
        if serial == VPC_READ_DIAG_SN2:
            dup = copy.deepcopy(out[0])
            dup["interfaces"][0]["nvPairs"]["DESC"] = CANARY
            out.append(dup)
        return out

    ctrl._peer_details = details
    got = refused(ctrl)
    assert cause(VPC_READ_DIAG_SN2, "the interface detail of", "record 1.0 duplicates an earlier record of the same interface") in got


def test_bulk_http_status_on_the_second_peer():
    ctrl = CanaryController().seed_baseline()
    ctrl.canary_failures.add(BULK + VPC_READ_DIAG_SN2)
    got = refused(ctrl)
    assert generic(VPC_READ_DIAG_SN2, VPC_READ_DIAG_M2) <= folded(got)
    assert cause(VPC_READ_DIAG_SN2, "the interface detail of", "HTTP 500 after 3 attempt(s)") in got


def test_policy_list_invalid_element_on_both_peers():
    ctrl = V.baseline_ctrl()
    ctrl.policies_override = {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [CANARY]}
    got = refused(ctrl)
    for serial, member in ((VPC_READ_DIAG_SN1, VPC_READ_DIAG_M1), (VPC_READ_DIAG_SN2, VPC_READ_DIAG_M2)):
        assert generic(serial, member) <= folded(got)
        assert cause(serial, "the switch policy list of", "element 0 is not an object") in got


def test_policy_list_http_status_is_a_single_attempt():
    ctrl = CanaryController().seed_baseline()
    ctrl.canary_failures.add(POLICIES + VPC_READ_DIAG_SN1)
    got = refused(ctrl)
    assert cause(VPC_READ_DIAG_SN1, "the switch policy list of", "HTTP 500 after 1 attempt(s)") in got


def test_summary_failure_on_both_peers_names_both():
    ctrl = V.baseline_ctrl()
    ctrl.read_failures.update({SUMMARY + VPC_READ_DIAG_SN1, SUMMARY + VPC_READ_DIAG_SN2})
    got = refused(ctrl)
    for serial, member in ((VPC_READ_DIAG_SN1, VPC_READ_DIAG_M1), (VPC_READ_DIAG_SN2, VPC_READ_DIAG_M2)):
        assert generic(serial, member) <= folded(got)
        assert cause(serial, "the interface summary of", "HTTP 500 after 3 attempt(s)") in got
    assert len(got) == 6


def test_exhausted_read_budget_says_no_request_was_sent_and_keeps_the_last_real_failure():
    ctrl = V.baseline_ctrl()
    extra = "Ethernet1/9"
    nv = trunk_host_nv(extra)
    nv["ADMIN_STATE"] = "false"
    ctrl.nodes[VPC_READ_DIAG_SN2][extra] = {"policy": TRUNK, "nvPairs": nv}
    ctrl.read_failures.add(BULK + VPC_READ_DIAG_SN2)
    got = refused(ctrl, [V.vpc_item(peer2_members=[VPC_READ_DIAG_M2, extra])])
    detail = [l for l in got if "the interface detail of" in l]
    assert detail == [cause(VPC_READ_DIAG_SN2, "the interface detail of",
                            "read skipped: the read budget of this serial is exhausted (no request sent); "
                            "last failed read: HTTP 500 after 3 attempt(s)")], detail
    # the budget is unchanged: two invoked reads (3 attempts each) and nothing more for this serial
    assert len([p for _m, p, _d in ctrl.calls if BULK + VPC_READ_DIAG_SN2 in p]) == 6


def test_a_failed_read_followed_by_a_valid_one_leaves_no_stale_reason():
    class FirstSummaryFails(V.VpcController):
        def __init__(self):
            super(FirstSummaryFails, self).__init__()
            self.summary_reads = 0

        def __call__(self, mod, method, path, data=None):
            if SUMMARY + VPC_READ_DIAG_SN1 in path:
                self.summary_reads += 1
                if self.summary_reads <= 3:
                    self.calls.append((method, path, data))
                    return {"RETURN_CODE": 500, "MESSAGE": CANARY, "DATA": {}}
            return super(FirstSummaryFails, self).__call__(mod, method, path, data)

    ctrl = FirstSummaryFails().seed_baseline()
    V.create_previews(ctrl)
    status, result = V.run_vpc(ctrl, [V.vpc_item()])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.summary_reads > 3 and "could not be read authoritatively" not in json.dumps(result)


def test_truly_absent_member_stays_absence_not_unreadable():
    ctrl = V.baseline_ctrl()
    del ctrl.nodes[VPC_READ_DIAG_SN1][VPC_READ_DIAG_M1]
    got = refused(ctrl)
    assert any("not an existing physical interface" in l for l in got)
    assert not any("could not be read authoritatively" in l for l in got)


# ------------------------------------------------------------------ member join and a mixed Po / vPC invocation
def test_join_names_the_unreadable_peer_even_when_it_receives_no_new_member():
    ctrl = MU.vpc_seeded({VPC_READ_DIAG_SN1: [VPC_READ_DIAG_M1], VPC_READ_DIAG_SN2: [VPC_READ_DIAG_M2]}, spare={VPC_READ_DIAG_SN1: [MU.E9P]})
    ctrl.read_failures.add(SUMMARY + VPC_READ_DIAG_SN2)
    got = refused(ctrl, [V.vpc_item(peer1_members=[VPC_READ_DIAG_M1, MU.E9P])])
    assert cause(VPC_READ_DIAG_SN2, "the interface summary of", "HTTP 500 after 3 attempt(s)") in got
    assert not any(VPC_READ_DIAG_SN1 in l for l in got)


def test_join_names_the_joining_peer_cause_once():
    ctrl = MU.vpc_seeded({VPC_READ_DIAG_SN1: [VPC_READ_DIAG_M1], VPC_READ_DIAG_SN2: [VPC_READ_DIAG_M2]}, spare={VPC_READ_DIAG_SN1: [MU.E9P]})
    ctrl.read_failures.add(POLICIES + VPC_READ_DIAG_SN1)
    got = refused(ctrl, [V.vpc_item(peer1_members=[VPC_READ_DIAG_M1, MU.E9P])])
    causes = [l for l in got if "the switch policy list of" in l]
    assert causes == [cause(VPC_READ_DIAG_SN1, "the switch policy list of", "HTTP 500 after 1 attempt(s)")], causes
    assert "{0} on {1}: {2}".format(MU.E9P, VPC_READ_DIAG_SN1, UNREAD) in got


def test_mixed_po_and_vpc_invocation_keeps_every_refusal_and_names_the_vpc_cause():
    ctrl = V.baseline_ctrl()
    nv = trunk_host_nv("Ethernet1/5")
    nv["ADMIN_STATE"] = None  # ADMIN-UP-JOIN: "true" now joins; an unknown administrative state is still refused
    ctrl.nodes[VPC_READ_DIAG_SN1]["Ethernet1/5"] = {"policy": TRUNK, "nvPairs": nv}
    ctrl.read_failures.add(SUMMARY + VPC_READ_DIAG_SN2)
    po = {"name": "port-channel50", "type": "pc", "switch": [V.IP1], "deploy": True,
          "profile": {"mode": "pvlan", "pvlan_mode": "host", "members": ["Ethernet1/5"], "admin_state": False,
                      "pvlan_association": [{"primary_vlan": V.PRIMARY, "secondary_vlan": V.SECONDARY}]}}
    got = refused(ctrl, [po, V.vpc_item()])
    assert any(l.startswith("Ethernet1/5 on %s: the member's administrative state is unknown" % VPC_READ_DIAG_SN1) for l in got)
    assert generic(VPC_READ_DIAG_SN2, VPC_READ_DIAG_M2) <= folded(got)
    assert cause(VPC_READ_DIAG_SN2, "the interface summary of", "HTTP 500 after 3 attempt(s)") in got
    assert not any(l.startswith("%s on %s" % (V.VPC, VPC_READ_DIAG_SN1)) for l in got)


def test_total_detail_failure_on_the_first_serial_is_still_the_earlier_refusal():
    """Documented limit, unchanged: the vPC parent's own HAVE is read through the pair's FIRST serial before this preflight."""
    ctrl = V.baseline_ctrl()
    ctrl.read_failures.add(BULK + VPC_READ_DIAG_SN1)
    status, result = V.run_vpc(ctrl, [V.vpc_item()])
    assert status == "fail" and mutating(ctrl) == []
    assert result["msg"].startswith("Current state of interface %s on %s could not be read authoritatively" % (V.VPC, V.PAIR))


def test_reason_classification_accepts_exactly_what_the_readers_accept():
    """Classifying a failure must not tighten a reader: every answer the readers took as `RETURN_CODE == 200` with a DATA list
    (an equal float included) gets no reason; every other answer gets controlled text without the body or message."""
    reason = dcnm_interface.response_failure_reason
    assert reason({"RETURN_CODE": 200, "DATA": []}, 3) is None
    assert reason({"RETURN_CODE": 200.0, "DATA": []}, 3) is None
    assert reason({"RETURN_CODE": 200, "DATA": {"x": CANARY}}, 3) == "the response DATA is not a list"
    assert reason({"RETURN_CODE": 500, "MESSAGE": CANARY}, 3) == "HTTP 500 after 3 attempt(s)"
    assert reason({"RETURN_CODE": True, "DATA": []}, 1) == "the response has no integer status"
    assert reason({"RETURN_CODE": "200", "DATA": []}, 1) == "the response has no integer status"
    assert reason(None, 1) == "no response (transport error) after 1 attempt(s)"
    assert reason([], 1) == "the response body is empty"
    assert reason(CANARY, 1) == "the response is not an object"


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_vpc_readback.py
# Regressions for two readback gaps of the vPC PVLAN host path, with the real main().
#
# NOT LIVE TESTED. First: after the deploy, the MEMBER of a peer is compared with the member model EXPECTED for that peer (values
# inherited from the frozen PRE-state), not only checked for policy/PO_ID/In-Sync. Second: after a deletion, the COMPLETE released
# member is compared with the explicit release contract recorded in the leg (PO_RELEASED_MEMBER_NV), not only for
# policy/ADMIN_STATE/CONF. Same synthetic harness as the rest of the vPC tests; the only addition is a controller that changes ONE
# member AFTER the deploy answer.
# ====================================================================================================
VPC_READBACK_PEERS = [(SN1, M1, 1), (SN2, M2, 2)]


class AfterDeploy(VpcController):
    """Changes one member of one peer right AFTER the deploy answer (a review probe shape): `drift(nv)` edits the nvPairs in place and
    returns None, or returns the replacement value of `nvPairs` itself (for example None or a list)."""

    def __init__(self, serial=None, port=None, drift=None):
        super(AfterDeploy, self).__init__()
        self.target, self.drift = (serial, port), drift

    def __call__(self, mod, method, path, data=None):
        response = super(AfterDeploy, self).__call__(mod, method, path, data)
        if method == "POST" and path.endswith(DEPLOY) and self.drift:
            serial, port = self.target
            node = self.nodes[serial][port]
            replaced = self.drift(node["nvPairs"])
            if replaced is not None:
                node["nvPairs"] = replaced["value"]
        return response


def setter(key, value):
    def apply(nv):
        nv[key] = value

    return apply


def remover(key):
    def apply(nv):
        nv.pop(key, None)

    return apply


def created_after_deploy(serial, port, drift):
    ctrl = AfterDeploy(serial, port, drift)
    ctrl.seed_baseline()
    create_previews(ctrl)
    return ctrl


# ================================================================== R1-01: the member after the deploy
@pytest.mark.parametrize("serial, port, peer", VPC_READBACK_PEERS)
@pytest.mark.parametrize(
    "drift, needle",
    [
        (setter("PC_MODE", "on"), "PC_MODE is 'on', expected 'active'"),
        (setter("ADMIN_STATE", "true"), "ADMIN_STATE is 'true', expected 'false'"),
        (setter("PVLAN_MODE", "promiscuous"), "PVLAN_MODE is 'promiscuous', expected 'host'"),
        (setter("PO_ID", "port-channel99"), "is not the member of port-channel10"),
        (setter("CDP_ENABLE", "false"), "CDP_ENABLE is 'false', expected 'true'"),
        (setter("lldpTransmit", "true"), "lldpTransmit is 'true', expected 'false'"),
        (setter("LACP_RATE", "fast"), "LACP_RATE is 'fast', expected 'normal'"),
        (setter("LACP_PORT_PRIO", "100"), "LACP_PORT_PRIO is '100', expected '32768'"),
        (setter("DESC", "rewritten"), "DESC is 'rewritten', expected ''"),
        (setter("CONF", "mtu 1500"), "CONF is 'mtu 1500', expected ''"),
        (setter("PRIMARY_INTF", "vPC99"), "PRIMARY_INTF is 'vPC99', expected 'vPC10'"),
        (remover("PC_MODE"), "PC_MODE is missing"),
        (remover("ADMIN_STATE"), "ADMIN_STATE is missing"),
        (setter("PVLAN_MODE", ["host"]), "PVLAN_MODE is malformed (list)"),
        (setter("PC_MODE", {"x": 1}), "PC_MODE is malformed (dict)"),
    ],
)
def test_a_member_that_contradicts_its_model_after_the_deploy_fails_the_vpc_on_either_peer(serial, port, peer, drift, needle):
    ctrl = created_after_deploy(serial, port, drift)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "fail", result
    assert "peer %d (%s): member %s differs from the expected member model" % (peer, serial, port) in result["msg"] or needle in result["msg"]
    assert needle in result["msg"] and "peer %d (%s)" % (peer, serial) in result["msg"], result["msg"]
    other = [p for p in VPC_READBACK_PEERS if p[2] != peer][0]
    assert "peer %d (" % other[2] not in result["msg"], "the correct peer is not blamed"
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1
    assert ctrl.modifies() == [] and ctrl.markdeletes() == [], "no repair write after the failed readback"


def test_the_positive_control_and_the_harmless_variations_still_succeed():
    ctrl = created_after_deploy(SN2, M2, None)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "exit" and result["changed"] is True and len(ctrl.deploys()) == 1

    def harmless(nv):
        nv["ADMIN_STATE"] = False  # a boolean instead of 'false'
        nv["LACP_PORT_PRIO"] = 32768  # an integer instead of '32768'
        nv["PC_MODE"] = "Active"  # case
        nv["INTF_NAME"] = "something-else"  # metadata, not a wire field of the member model
        nv["PTP"] = "true"
        nv["INTF_PTP"] = "true"
        nv.pop("CDP_ENABLE")  # an optional field that is absent takes the template default
        nv.pop("PRIMARY_INTF")  # metadata the controller may not return

    ctrl = created_after_deploy(SN2, M2, harmless)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "exit" and result["changed"] is True, result.get("msg")


def test_the_expectation_comes_from_the_frozen_pre_state_not_from_the_state_being_verified():
    # The member inherits its DESCRIPTION from its own pre-state (HOST 727-760). Rewriting it after the deploy must be caught: an expectation
    # rebuilt from the corrupted post-state would accept it.
    ctrl = AfterDeploy(SN2, M2, setter("DESC", ""))
    ctrl.seed_baseline()
    ctrl.nodes[SN2][M2]["nvPairs"]["DESC"] = "inherited-from-baseline"
    ctrl.vpc_previews[SN1] = [_preview(SN1, M1, None)]
    ctrl.vpc_previews[SN2] = [_preview(SN2, M2, "inherited-from-baseline")]
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and "DESC is '', expected 'inherited-from-baseline'" in result["msg"] and "peer 2 (%s)" % SN2 in result["msg"], result.get("msg")
    # and the same member, untouched, is accepted
    ctrl = AfterDeploy()
    ctrl.seed_baseline()
    ctrl.nodes[SN2][M2]["nvPairs"]["DESC"] = "inherited-from-baseline"
    ctrl.vpc_previews[SN1] = [_preview(SN1, M1, None)]
    ctrl.vpc_previews[SN2] = [_preview(SN2, M2, "inherited-from-baseline")]
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "exit", result.get("msg")


def _preview(serial, port, member_desc):
    running = member_running_baseline(port) + (["  description %s" % member_desc] if member_desc else [])
    after = member_after(port) + (["  description %s" % member_desc] if member_desc else [])
    pending = create_pending(port)
    return preview(pending, serial=serial, running=running, expected=po_stanza() + after)


def test_a_wrong_member_is_not_hidden_by_a_correct_other_peer_or_by_a_generic_in_sync():
    ctrl = created_after_deploy(SN1, M1, setter("PC_MODE", "passive"))
    # every interface keeps answering In-Sync (the harness default): that alone must not be accepted as success
    status, result = run_vpc(ctrl, [vpc_item()])
    assert (
        status == "fail"
        and "peer 1 (%s): member %s differs" % (SN1, M1) in result["msg"]
        and "In-Sync but the post-deploy intent readback differs" in result["msg"]
    )


def test_two_wrong_members_are_both_reported():
    class Both(AfterDeploy):
        def __call__(self, mod, method, path, data=None):
            response = super(Both, self).__call__(mod, method, path, data)
            if method == "POST" and path.endswith(DEPLOY):
                self.nodes[SN2][M2]["nvPairs"]["ADMIN_STATE"] = "true"
            return response

    ctrl = Both(SN1, M1, setter("PC_MODE", "passive"))
    ctrl.seed_baseline()
    create_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and "peer 1 (%s)" % SN1 in result["msg"] and "peer 2 (%s)" % SN2 in result["msg"]


def test_update_readback_judges_the_member_against_the_new_model():
    from .helpers.vpc_controller import converged_preview, pc_mode_preview

    for serial, port, peer in VPC_READBACK_PEERS:
        ctrl = AfterDeploy(serial, port, setter("PC_MODE", "active"))  # the controller did NOT apply the new mode on that member
        ctrl.seed_baseline().seed_vpc()
        ctrl.next_invocation()
        ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1), pc_mode_preview(SN1, M1)]
        ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2), pc_mode_preview(SN2, M2)]
        status, result = run_vpc(ctrl, [vpc_item(pc_mode="passive")], state="merged")
        assert status == "fail" and "PC_MODE is 'active', expected 'passive'" in result["msg"] and "peer %d (%s)" % (peer, serial) in result["msg"], result.get(
            "msg"
        )
        assert len(ctrl.modifies()) == 1 and len(ctrl.deploys()) == 1 and ctrl.markdeletes() == []
    ctrl = AfterDeploy()  # positive control of the update
    ctrl.seed_baseline().seed_vpc()
    ctrl.next_invocation()
    ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1), pc_mode_preview(SN1, M1)]
    ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2), pc_mode_preview(SN2, M2)]
    status, result = run_vpc(ctrl, [vpc_item(pc_mode="passive")], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")


# ================================================================== the same coherence BEFORE any change
@pytest.mark.parametrize("serial, port, peer", VPC_READBACK_PEERS)
@pytest.mark.parametrize(
    "drift, needle",
    [
        (setter("PC_MODE", "on"), "PC_MODE is 'on', expected 'active'"),
        (setter("PVLAN_MODE", "promiscuous"), "PVLAN_MODE is 'promiscuous', expected 'host'"),
        (setter("CDP_ENABLE", "false"), "CDP_ENABLE is 'false', expected 'true'"),
        (remover("PC_MODE"), "PC_MODE is missing"),
    ],
)
@pytest.mark.parametrize("flow", ["repeat", "update", "delete"])
def test_a_member_that_already_contradicts_its_model_is_refused_before_any_write(serial, port, peer, drift, needle, flow):
    ctrl = created_ctrl()
    drift(ctrl.nodes[serial][port]["nvPairs"])
    converged_previews(ctrl)
    delete_previews(ctrl)
    if flow == "delete":
        status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    else:
        item = vpc_item(peer1_description="a", peer2_description="b") if flow == "update" else vpc_item()
        status, result = run_vpc(ctrl, [item], state="merged")
    assert status == "fail" and needle in result["msg"] and "member %s differs from the expected member model" % port in result["msg"], result.get("msg")
    assert serial in result["msg"]
    assert ctrl.writes() == [], "refused before the first write"


# ================================================================== R1-02: the released member of a deletion
# Minimal post-deploy reads: the complete judgement of the released member -- the explicit release contract, residual PVLAN /
# channel-group fields, a modelable member and the policy residue -- is made on the FRESH release, BEFORE the deploy (phase C of
# dcnm_intf_pvlan_vpc_release_members), in the same invocation and also when a new process completes a saved deletion. After the deploy only
# the peers' summaries are read. So a divergence the controller RELEASES is refused before any deploy; a change made after the deploy is not
# re-read by the module (the external test harness checks the member's intent and running configuration).
class Released(VpcController):
    """`when` = "release": `drift` is applied when the controller releases the member (at the mark-delete); "deploy": right after the deploy
    answer (the earlier probe shape)."""

    def __init__(self, serial=None, port=None, drift=None, when="release"):
        super(Released, self).__init__()
        self.target, self.drift, self.when = (serial, port), drift, when

    def apply(self, serial, port, drift):
        node = self.nodes[serial][port]
        replaced = drift(node["nvPairs"])
        if replaced is not None:
            node["nvPairs"] = replaced["value"]

    def __call__(self, mod, method, path, data=None):
        response = super(Released, self).__call__(mod, method, path, data)
        moment = "release" if method == "DELETE" and path.endswith("/rest/interface/markdelete") else (
            "deploy" if method == "POST" and path.endswith(DEPLOY) else None)
        if moment == self.when and self.drift:
            self.apply(self.target[0], self.target[1], self.drift)
        return response


def deleted_run(serial=None, port=None, drift=None, when="release", ctrl=None):
    ctrl = ctrl or Released(serial, port, drift, when)
    ctrl.seed_baseline().seed_vpc()
    ctrl.next_invocation()
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    return ctrl, status, result


def reads_after_deploy(ctrl):
    last = max(i for i, c in enumerate(ctrl.calls) if c[0] == "POST" and c[1].endswith(DEPLOY))
    return sorted(set(path.split("?")[0].rsplit("/rest/", 1)[-1] for method, path, _d in ctrl.calls[last + 1:] if method == "GET"))


@pytest.mark.parametrize("serial, port, peer", VPC_READBACK_PEERS)
@pytest.mark.parametrize(
    "drift, needle",
    [
        # refused by the pre-existing safety check while proving the member, before any member write
        (setter("ALLOWED_VLANS", "2301"), "ALLOWED_VLANS is '2301', not 'none'"),
        (setter("ALLOWED_VLANS", "all"), "ALLOWED_VLANS is 'all', not 'none'"),
        (setter("NATIVE_VLAN", "5"), "NATIVE_VLAN is '5', not ''"),
        (remover("ALLOWED_VLANS"), "ALLOWED_VLANS is absent from the released member"),
        (setter("ALLOWED_VLANS", ["none"]), "ALLOWED_VLANS is ['none'], not 'none'"),
        # refused by the release contract check, moved before the deploy (it used to be judged after the deploy)
        (setter("PO_ID", "port-channel10"), "residual PVLAN/channel-group field PO_ID='port-channel10'"),
        (setter("PVLAN_MODE", "host"), "residual PVLAN/channel-group field PVLAN_MODE='host'"),
        (setter("PC_MODE", "active"), "residual PVLAN/channel-group field PC_MODE='active'"),
        (setter("GUARD_MODE", "root"), "the released member's CLI model differs from the contract"),  # a modeled field outside the contract's own keys
        (setter("CDP_ENABLE", "false"), "the released member's CLI model differs from the contract"),
        (setter("SPEED", "10Gb"), "cannot be modeled"),
        (setter("ENABLE_PFC", "true"), "cannot be modeled"),  # a field the model cannot judge is never success
    ],
)
def test_a_released_member_that_diverges_from_the_contract_is_refused_before_the_deploy_on_either_peer(serial, port, peer, drift, needle):
    ctrl, status, result = deleted_run(serial, port, drift)
    assert status == "fail" and needle in result["msg"], result.get("msg")
    assert "(peer %d)" % peer in result["msg"] or "peer %d (%s): member %s" % (peer, serial, port) in result["msg"], result["msg"][:300]
    other = [p for p in VPC_READBACK_PEERS if p[2] != peer][0]
    assert "peer %d (%s)" % (other[2], other[0]) not in result["msg"], "the clean peer is not blamed"
    assert ctrl.deploys() == [] and len(ctrl.markdeletes()) == 1 and ctrl.creates() == [], "nothing is deployed over a released member that fails"
    assert "pvlan_verification" not in result, "the post-deploy verification is never reached"


def residue_policy(entity, template, source="", deleted=False):
    return {"entityName": entity, "templateName": template, "source": source, "deleted": deleted, "entityType": "INTERFACE",
            "policyId": "RES-%s-%s" % (entity, template), "serialNumber": SN1}


class Residue(VpcController):
    """At the mark-delete the controller releases peer 1's member with a residue: extra live policies on that serial, another member
    template, extra member nvPairs, or no member policy at all."""

    def __init__(self, extra=(), member_policy=None, member_nv=None, hide_member=False):
        super(Residue, self).__init__()
        self.extra, self.member_policy, self.member_nv, self.hide_member = list(extra), member_policy, member_nv or {}, hide_member

    def __call__(self, mod, method, path, data=None):
        response = super(Residue, self).__call__(mod, method, path, data)
        if method == "DELETE" and path.endswith("/rest/interface/markdelete"):
            self.policies_extra[SN1] += self.extra
            if self.member_policy:
                self.nodes[SN1][M1]["policy"] = self.member_policy
            self.nodes[SN1][M1]["nvPairs"].update(self.member_nv)
        return response

    def _peer_policies(self, serial):
        out = super(Residue, self)._peer_policies(serial)
        if self.hide_member and self.markdeleted and serial == SN1:
            out = [p for p in out if p["entityName"] != M1]
        return out


@pytest.mark.parametrize(
    "kw, needle",
    [
        # the cases of the former unit test of vpc_leg_residue (once re-read after the deploy), now through main() and the release proof
        (dict(extra=[residue_policy(M1, "int_eth", source=VPC)]), "live policies still reference the vPC or its child port-channel"),
        (dict(extra=[residue_policy("port-channel10", "int_vpc_pvlan_po", source=VPC)]), "live policies still reference the vPC or its child"),
        (dict(extra=[residue_policy("port-channel10", "int_port_channel_trunk_host")]), "live policies still reference the vPC or its child"),
        (dict(extra=[residue_policy(VPC, "int_vpc_pvlan_host")]), "live policies still reference the vPC or its child port-channel"),
        (dict(extra=[residue_policy("Ethernet1/9", "int_eth", source="port-channel10")]), "live policies still reference the vPC or its child"),
        (dict(member_policy="int_port_channel_pvlan_member"), "the released member holds 'int_port_channel_pvlan_member'"),
        (dict(member_policy="int_access_host"), "the released member holds 'int_access_host'"),
        (dict(extra=[residue_policy(M1, "Config_Profile", source="OVERLAY")]), "the released member is not a sole direct int_trunk_host"),
        (dict(extra=[residue_policy(M1, "int_trunk_host", source="someone")]), "the released member is not a sole direct int_trunk_host"),
        (dict(hide_member=True), "holds 0 live policies for this interface"),
        (dict(member_nv={"CONF": "mtu 1500"}), "CONF is 'mtu 1500', not ''"),
    ],
)
def test_a_residue_left_by_the_vpc_is_refused_by_the_release_proof_before_any_member_write(kw, needle):
    ctrl, status, result = deleted_run(ctrl=Residue(**kw))
    assert status == "fail" and needle in result["msg"], result.get("msg")
    assert "while proving the released member before any member write (peer 1)" in result["msg"]
    assert ctrl.modifies() == [] and ctrl.deploys() == [] and len(ctrl.markdeletes()) == 1


def test_a_deleted_policy_entry_is_not_residue():
    ctrl, status, result = deleted_run(ctrl=Residue(extra=[residue_policy(M1, "int_trunk_host", deleted=True)]))
    assert status == "exit" and result["pvlan_verification"][VPC]["state"] == "verified", result.get("msg")


# MTU, BPDUGUARD_ENABLED, PORTTYPE_FAST_ENABLED and DESC released with another value are the release's own values (the contract is built from
# the fresh release) and are reported in `restoration_delta`; the earlier check failed on them only when they CHANGED after the deploy.


@pytest.mark.parametrize("serial, port, peer", VPC_READBACK_PEERS)
@pytest.mark.parametrize("drift", [setter("ALLOWED_VLANS", "2301"), setter("PO_ID", "port-channel10"), lambda nv: {"value": None}])
def test_a_member_changed_after_the_deploy_is_not_re_read_by_the_module(serial, port, peer, drift):
    """Contract change (these used to be detected after the deploy): no intent is read after the deploy, only the two summaries."""
    ctrl, status, result = deleted_run(serial, port, drift, when="deploy")
    assert status == "exit" and result["pvlan_verification"][VPC]["state"] == "verified", result.get("msg")
    assert reads_after_deploy(ctrl) == ["interface/detail"]
    release_only(ctrl)


def test_the_released_baseline_and_harmless_metadata_are_still_accepted():
    ctrl, status, result = deleted_run()
    assert status == "exit" and result["pvlan_verification"][VPC]["state"] == "verified"

    def harmless(nv):
        nv["INTF_NAME"] = "metadata"
        nv["PTP"] = "true"
        nv["ADMIN_STATE"] = False  # boolean form
        nv["ALLOWED_VLANS"] = "none"

    for serial, port, _peer in VPC_READBACK_PEERS:
        ctrl, status, result = deleted_run(serial, port, harmless)
        assert status == "exit" and result["pvlan_verification"][VPC]["peers"] == {SN1: "verified", SN2: "verified"}, result.get("msg")
        assert ctrl.nodes[serial][port]["policy"] == TRUNK


def test_an_absent_nvpairs_member_still_fails_the_deletion_as_before():
    ctrl, status, result = deleted_run(SN2, M2, lambda nv: {"value": None})
    assert status == "fail" and "could not be read authoritatively" in result["msg"] and "(peer 2)" in result["msg"], result.get("msg")
    assert ctrl.deploys() == [] and "pvlan_verification" not in result


def test_both_peers_released_with_divergences_are_both_reported():
    class Two(Released):
        def __call__(self, mod, method, path, data=None):
            response = super(Two, self).__call__(mod, method, path, data)
            if method == "DELETE" and path.endswith("/rest/interface/markdelete"):
                self.nodes[SN1][M1]["nvPairs"]["PC_MODE"] = "active"
            return response

    ctrl, status, result = deleted_run(ctrl=Two(SN2, M2, setter("PO_ID", "port-channel10")))
    assert status == "fail" and "peer 1 (%s)" % SN1 in result["msg"] and "peer 2 (%s)" % SN2 in result["msg"], result.get("msg")
    assert "PC_MODE='active'" in result["msg"] and "PO_ID='port-channel10'" in result["msg"] and ctrl.deploys() == []


def test_the_message_names_peer_interface_and_field():
    ctrl, status, result = deleted_run(SN2, M2, setter("PO_ID", "port-channel10"))
    assert "peer 2 (%s): member %s: residual PVLAN/channel-group field PO_ID='port-channel10'" % (SN2, M2) in result["msg"]
    ctrl = created_after_deploy(SN2, M2, setter("PC_MODE", "on"))
    status, result = run_vpc(ctrl, [vpc_item()])
    assert "peer 2 (%s): member %s differs from the expected member model: PC_MODE is 'on', expected 'active'" % (SN2, M2) in result["msg"]
    assert json.dumps(result)  # the whole result stays serialisable
