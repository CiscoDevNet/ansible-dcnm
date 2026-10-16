"""RELEASE-ADMIN: the release of a PVLAN port-channel / vPC member follows the fabric's host-interface default.

Contract (the generic one, dcnm_intf_get_default_eth_payload): a host interface returned to its default takes ADMIN_STATE from the fabric
nvPair HOST_INTF_ADMIN_STATE. The PVLAN release (deletion -- named or by an overridden sweep -- and a member removed by an update) now
targets that value instead of always "false":
  * HOST_INTF_ADMIN_STATE "true" (the NDFC default; ND .90 FAB1 as redeployed): the controller's release (MEASURED: int_trunk_host
    ADMIN_STATE "true") already is the target, so no member write; a release that came back down is set up by the same single modify;
  * "false": unchanged -- the measured up release is corrected to "false" before the deploy;
  * unreadable / not a boolean: refused before any write (never defaulted);
  * the member's OWN administrative state before the release no longer matters (up or down), exactly like the generic reset; an unknown
    member state stays refused.
Administrative state only: the operational link state is never read or asserted here.

Harnesses: the measured G4 Po release (H1/HR fixture: HR-post preview = released member expected `no shutdown`), the membership Po/vPC
harnesses and the vPC harness. The fabric default is the harness knob (`fabric_admin`). Real main(); only the controller boundary is
intercepted.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

import pytest

from . import test_dcnm_intf_pvlan_member_updates as MU
from . import test_dcnm_intf_pvlan_po_g4_release as G4
from . import test_dcnm_intf_pvlan_po_vpc_reconcile as RC
from . import test_dcnm_intf_pvlan_vpc_harness as V
from .test_dcnm_intf_pvlan_harness import SWITCH_IP, TRUNK, run

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
    not implemented`: the E2 guard fires for a PVLAN object the preflight did NOT register. With the registration accepted (true default)
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


# ================================================================== V-7b live shape: the marked parent vPC stays listed
def saved_vpc_with_listed_parent():
    ctrl = RC.vpc_ctrl()
    ctrl.children_marked_deleted = True
    ctrl.parent_marked_listed = True  # MEASURED live V-7a: the parent stays listed, markDeleted True, no policy
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
