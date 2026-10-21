"""Conventional and PVLAN aggregate DELETIONS in ONE dcnm_interface call.

A single `state: deleted` call, each item deploy false, can delete a conventional port-channel and a PVLAN one. The PVLAN
saved-deletion gate (`delete_saved`) then reads a pending that also holds the conventional `no interface port-channel<id>` and
its released member, and must not refuse them.

Rule: a conventional port-channel / vPC whose generic mark-delete THIS invocation sent, and whose ORIGINAL answer is the
measured success naming exactly the requested items, leaves on each physical serial (vPC: both child port-channels, PEERn ->
n-th serial) exactly (a) the global line `no interface port-channel<its id>` and (b) its pre-state members, each judged by the
existing rule (the block must withdraw that channel-group). Any other global line, interface, id or serial stays refused; an
unconfirmed answer grants nothing; nothing survives the invocation.

Shapes: a measured forced-preview pending on the measured deletion harness; the vPC on the existing vPC deletion harness. Real
main(); only the controller boundary is faked.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from . import test_dcnm_intf_pvlan_po_g4_release as G4
from . import test_dcnm_intf_pvlan_po_g5_next_modes as G5
from . import test_dcnm_intf_pvlan_po_vpc_reconcile as R
from . import test_dcnm_intf_pvlan_vpc_harness as V
from .test_dcnm_intf_pvlan_harness import SERIAL, SWITCH_IP, ok, run
from .test_dcnm_intf_pvlan_mixed_batch import released_block

CONV_PO, C14 = "Port-channel301", "Ethernet1/14"
CONV_PO_POLICY, CONV_MEMBER_POLICY = "int_port_channel_trunk_host", "int_port_channel_trunk_member_11_1"
CONV_VPC, V5, V6 = "vPC305", "Ethernet1/5", "Ethernet1/6"


def add_conv_po(ctrl, name=CONV_PO, members=(C14,)):
    """A conventional trunk port-channel ( Po301 shape) with its members, next to the harness's PVLAN Po."""
    nv = {"MEMBER_INTERFACES": ",".join(members), "PO_ID": name, "PC_MODE": "active", "DESC": "INTEG-PO-CONV-V2", "ADMIN_STATE": "true",
          "ALLOWED_VLANS": "none", "MTU": "jumbo", "SPEED": "Auto", "BPDUGUARD_ENABLED": "true", "PORTTYPE_FAST_ENABLED": "true", "CONF": ""}
    ctrl.detail[name] = {"policy": CONV_PO_POLICY, "nvPairs": nv}
    ctrl.po_names.add(name)
    for port in members:
        ctrl.detail[port] = {"policy": CONV_MEMBER_POLICY, "nvPairs": {"PO_ID": name, "ADMIN_STATE": "true", "INTF_NAME": port}}
    return ctrl


def po_preview(extra_global, extra_blocks, base=None):
    """The measured deletion pending of the PVLAN Po (its own `no interface` + released member) plus the conventional sibling's."""
    resp = base or G5.corrected_hr_preview()
    entry = resp["DATA"][0]
    entry["pendingConfig"] = list(extra_global) + list(entry["pendingConfig"]) + list(extra_blocks)
    entry["status"] = "Out-of-Sync"
    return resp


def hr_mixed_ctrl(cls=None):
    ctrl = add_conv_po(R.measured_po(G5.hr_ctrl([])))
    if cls is not None:
        ctrl.__class__ = cls
    return ctrl


T6_GLOBAL = ["no interface port-channel301"]


def t6_po(ctrl, extra_global=None, extra_blocks=None, deploy=False, previews=1):
    """The measured shape on one switch: deleted, conventional Po301 and PVLAN Po502 (harness name of Po310), both deploy false, one call."""
    extra_global = T6_GLOBAL if extra_global is None else extra_global
    extra_blocks = released_block(C14, 301) if extra_blocks is None else extra_blocks
    ctrl.previews = [po_preview(extra_global, extra_blocks) for _i in range(previews)]
    return run(ctrl, [{"name": "port-channel301", "switch": [SWITCH_IP], "deploy": deploy},
                      {"name": "po502", "switch": [SWITCH_IP], "deploy": deploy}], state="deleted")


def writes(ctrl, start=0):
    return R.writes(type("C", (), {"calls": ctrl.calls[start:]}))


# ================================================================== regular port-channels
def test_t6_conventional_deletion_in_the_same_call_owns_its_withdrawal_and_released_member():
    ctrl = hr_mixed_ctrl()
    status, result = t6_po(ctrl)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert writes(ctrl) == ["interface/markdelete", "interface/markdelete", "interface/modify"], "PVLAN, then conventional; no deploy"
    assert result["pvlan_gate_invocation_releases"] == [
        {"site": "delete_saved", "serial": SERIAL, "interfaces": ["ethernet1/14"], "withdrawn": ["no interface port-channel301"]}]
    assert [g["site"] for g in result["pvlan_gate"]] == ["delete_saved"]
    assert "NOT deployed" in result["pvlan_saved"][0]["state"]


@pytest.mark.parametrize("extra_global, needle", [
    (T6_GLOBAL + ["no interface port-channel399"], "outside interface scope"),
    (T6_GLOBAL + ["router bgp 65000"], "outside interface scope"),
    (["no interface port-channel302"], "outside interface scope"),
], ids=["foreign-no-interface", "foreign-global", "wrong-port-channel-id"])
def test_other_global_pending_is_still_refused_with_no_deploy(extra_global, needle):
    ctrl = hr_mixed_ctrl()
    status, result = t6_po(ctrl, extra_global=extra_global)
    assert status == "fail" and needle in result["msg"] and "ALREADY changed" in result["msg"], result.get("msg")
    assert "globalInterface/deploy" not in writes(ctrl)


@pytest.mark.parametrize("blocks, foreign", [
    (released_block(C14, 301) + ["interface ethernet1/30", "  description stray"], "ethernet1/30"),
    (released_block(C14, 399), "ethernet1/14"),
    (released_block(C14, 301, withdrawal=False), "ethernet1/14"),
], ids=["foreign-interface", "member-withdraws-another-id", "member-without-withdrawal"])
def test_other_interface_pending_is_still_refused_with_no_deploy(blocks, foreign):
    ctrl = hr_mixed_ctrl()
    status, result = t6_po(ctrl, extra_blocks=blocks)
    assert status == "fail" and "outside this deploy batch: %s" % foreign in result["msg"], result.get("msg")
    assert "globalInterface/deploy" not in writes(ctrl)


class AmbiguousConventionalMarkdelete(G5.DeployedReleaseController):
    """The conventional Po's mark-delete answers 200/OK but its outcome does not name the requested item (UNVERIFIED)."""

    def __call__(self, mod, method, path, data=None):
        resp = super(AmbiguousConventionalMarkdelete, self).__call__(mod, method, path, data)
        if method == "DELETE" and path.endswith("/rest/interface/markdelete") and "port-channel301" in str(data).lower():
            return ok({"message": "Interface deleted successfully", "value": []})
        return resp


class FailedThenRetriedConventionalMarkdelete(G5.DeployedReleaseController):
    """The conventional Po's first mark-delete answers 500 (the generic path retries it and the retry succeeds)."""

    def __call__(self, mod, method, path, data=None):
        resp = super(FailedThenRetriedConventionalMarkdelete, self).__call__(mod, method, path, data)
        if method == "DELETE" and path.endswith("/rest/interface/markdelete") and "port-channel301" in str(data).lower():
            if not getattr(self, "failed_once", False):
                self.failed_once = True
                return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": [{"message": "transient"}]}
        return resp


@pytest.mark.parametrize("cls", [AmbiguousConventionalMarkdelete, FailedThenRetriedConventionalMarkdelete], ids=["ambiguous", "retried"])
def test_an_unverified_conventional_markdelete_grants_no_ownership(cls):
    ctrl = hr_mixed_ctrl(cls)
    status, result = t6_po(ctrl)
    assert status == "fail" and "pvlan_gate_invocation_releases" not in result, result.get("msg")
    assert "outside interface scope" in result["msg"] and "globalInterface/deploy" not in writes(ctrl)


def test_unchanged_retry_after_the_saved_deletion_writes_nothing_and_owns_nothing():
    ctrl = hr_mixed_ctrl()
    status, result = t6_po(ctrl)
    assert status == "exit", result.get("msg")
    ctrl.next_invocation()
    start = len(ctrl.calls)
    ctrl.previews = [po_preview(T6_GLOBAL, released_block(C14, 301))]
    status, result = run(ctrl, [{"name": "port-channel301", "switch": [SWITCH_IP], "deploy": False},
                                {"name": "po502", "switch": [SWITCH_IP], "deploy": False}], state="deleted")
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert writes(ctrl, start) == [] and "pvlan_gate_invocation_releases" not in result
    assert "awaiting deployment" in result["pvlan_saved"][0]["state"]


def test_a_later_deploy_true_continuation_does_not_inherit_the_previous_invocations_ownership():
    """A LATER process with deploy true, on a controller that does NOT list Po301 in the marked-for-deletion form (this harness drops it at
    the mark-delete) while its withdrawal and released member are still pending: nothing in the current controller state proves that
    saved deletion, so it is not this invocation's operation and the gate refuses with nothing deployed. Ownership is never inherited
    from the previous process. The positive continuation backed by the controller's marked listing is in
    test_dcnm_intf_pvlan_mixed_saved_retry.py."""
    ctrl = hr_mixed_ctrl()
    status, result = t6_po(ctrl)
    assert status == "exit", result.get("msg")
    ctrl.next_invocation()
    start = len(ctrl.calls)
    ctrl.previews = [po_preview(T6_GLOBAL, released_block(C14, 301)) for _i in range(2)]
    status, result = run(ctrl, [{"name": "port-channel301", "switch": [SWITCH_IP], "deploy": True},
                                {"name": "po502", "switch": [SWITCH_IP], "deploy": True}], state="deleted")
    assert status == "fail" and "outside interface scope" in result["msg"], result.get("msg")
    assert "globalInterface/deploy" not in writes(ctrl, start) and "pvlan_gate_invocation_releases" not in result


def test_an_immediate_mixed_deletion_deploys_once_with_the_same_ownership():
    ctrl = hr_mixed_ctrl()
    status, result = t6_po(ctrl, deploy=True, previews=3)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert writes(ctrl).count("globalInterface/deploy") == 1
    assert [r["site"] for r in result["pvlan_gate_invocation_releases"]] == ["delete_deploy"]
    assert result["pvlan_gate_invocation_releases"][0]["withdrawn"] == ["no interface port-channel301"]


def test_conventional_only_deletion_makes_no_pvlan_reads():
    ctrl = hr_mixed_ctrl()
    status, result = run(ctrl, [{"name": "port-channel301", "switch": [SWITCH_IP], "deploy": False}], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert not [c for c in ctrl.calls if "config-preview" in c[1]] and "pvlan_gate" not in result


def test_pure_pvlan_saved_deletion_is_unchanged():
    ctrl = R.measured_po(G5.hr_ctrl([G5.corrected_hr_preview()]))
    status, result = run(ctrl, [{"name": "po502", "switch": [SWITCH_IP], "deploy": False}], state="deleted")
    assert status == "exit" and writes(ctrl) == ["interface/markdelete", "interface/modify"], result.get("msg")
    assert "pvlan_gate_invocation_releases" not in result


# ------------------------------------------------------------------ overridden (shared deletion path)
def test_overridden_that_drops_a_conventional_and_a_pvlan_port_channel_owns_the_conventional_pending():
    """The sweep deletes both through the SAME generic / PVLAN deletion paths: the same accounting applies (no new target scope)."""
    ctrl = add_conv_po(R.measured_po(G4.owned_ctrl()))
    ctrl.previews = [po_preview(T6_GLOBAL, released_block(C14, 301), base=G4.entry("H1-verify"))]
    status, result = run(ctrl, [R.lo(SWITCH_IP, deploy=False)], state="overridden")
    assert status == "exit", result.get("msg")
    assert writes(ctrl).count("interface/markdelete") == 2
    assert [(r["interfaces"], r["withdrawn"]) for r in result["pvlan_gate_invocation_releases"]] == [
        (["ethernet1/14"], ["no interface port-channel301"])]


def test_overridden_without_the_conventional_deletion_still_refuses_its_pending():
    """The same pending, but this call deletes no conventional Po (none is on the switch): nothing owns it."""
    ctrl = R.measured_po(G4.owned_ctrl())
    ctrl.previews = [po_preview(T6_GLOBAL, released_block(C14, 301), base=G4.entry("H1-verify"))]
    status, result = run(ctrl, [R.lo(SWITCH_IP, deploy=False)], state="overridden")
    assert status == "fail" and "outside interface scope" in result["msg"], result.get("msg")


# ================================================================== vPC
def vpc_mixed_ctrl(peer_members=(V5, V6), pcids=("305", "305")):
    """The PVLAN vPC10 deletion harness plus a conventional trunk vPC305 whose members DIFFER per peer (peer1 Eth1/5, peer2 Eth1/6), so a
    crossed assignment is visible."""
    ctrl = R.vpc_ctrl()
    ctrl.children_marked_deleted = True
    ctrl.parents[CONV_VPC] = {"policy": "int_vpc_trunk_host", "nvPairs": {
        "PEER1_MEMBER_INTERFACES": peer_members[0], "PEER2_MEMBER_INTERFACES": peer_members[1], "PEER1_PCID": pcids[0], "PEER2_PCID": pcids[1],
        "PC_MODE": "active", "ADMIN_STATE": "true", "PEER1_PO_DESC": "INTEG-VPC-CONV-V2", "PEER2_PO_DESC": "INTEG-VPC-CONV-V2",
        "PEER1_PO_CONF": "", "PEER2_PO_CONF": ""}}
    return ctrl


def vpc_conv_pending(member, pcid=305):
    return ["no interface port-channel%d" % pcid] + released_block(member, pcid)


def t6_vpc(ctrl, extra=None, deploy=False):
    extra = extra if extra is not None else {V.SN1: vpc_conv_pending(V5), V.SN2: vpc_conv_pending(V6)}
    for serial, port in ((V.SN1, V.M1), (V.SN2, V.M2)):
        p = V.delete_preview(serial, port)
        p["DATA"][0]["pendingConfig"] = list(p["DATA"][0]["pendingConfig"]) + list(extra.get(serial, []))
        ctrl.vpc_previews[serial] = [p]
    return V.run_vpc(ctrl, [{"name": "vpc305", "type": "vpc", "switch": [V.IP1, V.IP2], "deploy": deploy}, V.vpc_del_item(deploy=deploy)],
                     state="deleted")


def owned(result):
    return sorted(set((r["serial"], tuple(r["interfaces"]), tuple(r.get("withdrawn") or ())) for r in result.get("pvlan_gate_invocation_releases") or []))


def test_t6_vpc_mixed_deletion_owns_each_peers_own_child_withdrawal_and_member():
    ctrl = vpc_mixed_ctrl()
    status, result = t6_vpc(ctrl)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.markdeletes()) == 2 and ctrl.deploys() == []
    assert owned(result) == [(V.SN1, ("ethernet1/5",), ("no interface port-channel305",)),
                             (V.SN2, ("ethernet1/6",), ("no interface port-channel305",))]


def test_vpc_member_names_are_not_interchangeable_across_peer_serials():
    ctrl = vpc_mixed_ctrl()
    status, result = t6_vpc(ctrl, extra={V.SN1: vpc_conv_pending(V6), V.SN2: vpc_conv_pending(V6)})
    assert status == "fail" and "peer 1 (%s): pending exists for interfaces outside this deploy batch: ethernet1/6" % V.SN1 in result["msg"], \
        result.get("msg")
    assert ctrl.deploys() == []


def test_vpc_withdrawal_of_another_child_id_is_refused():
    ctrl = vpc_mixed_ctrl()
    status, result = t6_vpc(ctrl, extra={V.SN1: vpc_conv_pending(V5, 306), V.SN2: vpc_conv_pending(V6)})
    assert status == "fail" and "peer 1 (%s): pending carries commands outside interface scope" % V.SN1 in result["msg"], result.get("msg")


def test_a_peer_whose_child_identity_is_unknown_is_not_authorised_by_the_other_peer():
    """PEER2_PCID unknown in the pre-state: peer 1 is owned, peer 2's withdrawal and member stay foreign."""
    ctrl = vpc_mixed_ctrl(pcids=("305", ""))
    status, result = t6_vpc(ctrl)
    assert status == "fail" and "peer 2 (%s)" % V.SN2 in result["msg"] and "peer 1 (%s): pending" % V.SN1 not in result["msg"], result.get("msg")
    assert ctrl.deploys() == []


class UnverifiedConventionalVpcMarkdelete(R.MeasuredVpc):
    """The conventional vPC's mark-delete answers 200/OK without naming it; the PVLAN vPC keeps the default measured answer."""

    def __call__(self, mod, method, path, data=None):
        resp = super(UnverifiedConventionalVpcMarkdelete, self).__call__(mod, method, path, data)
        if method == "DELETE" and path.endswith(V.MARKDELETE) and "vpc305" in str(data).lower():
            return ok({"message": "Interface deleted successfully", "value": []})
        return resp


def test_an_unverified_conventional_vpc_markdelete_grants_no_ownership():
    ctrl = vpc_mixed_ctrl()
    ctrl.__class__ = UnverifiedConventionalVpcMarkdelete
    status, result = t6_vpc(ctrl)
    assert len(ctrl.markdeletes()) == 2
    assert status == "fail" and "pvlan_gate_invocation_releases" not in result and ctrl.deploys() == [], result.get("msg")
