"""SP1: the member's `speed 1000` of a PVLAN port-channel / vPC leg, carried by the port-channel's own pending (MEASURED inheritance).

Sources (sanitized, read-only extracts; raw captures and their sha256 stay outside the product):
  fixtures/pvlan_po_speed_diag_measured.json and pvlan_vpc_speed_diag_measured.json -- Alpha2's speed-inheritance diagnosis,
  DIAG-20261012T091312Z: apply / withdraw previews before the deploy and the converged previews after it, Po521 and both peers of vPC522;
  fixtures/pvlan_po_speed_s1_measured.json -- the RC2 S1 refusal (see test_dcnm_intf_pvlan_po_speed_s1_measured.py).
Measured: `speed 1000`, host mode, one member, admin down, NDFC 12.6.0.267, N9K-C9300v 10.5(5). Everything else stays refused, and these
tests are offline: they are not the module's live acceptance (that is Alpha2's runbook in ALPHA_SPEED_INHERITANCE_READY.md).
Po cases run the module's own gate (DcnmIntf.dcnm_intf_pvlan_po_assess) on the real stanza names; the main() cases retarget the measured
stanzas to the harness port-channel / members (only names and numbers change).
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import os

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

from . import test_dcnm_intf_pvlan_vpc_harness as V
from .test_dcnm_intf_pvlan_harness import IF7, SWITCH_IP, preview, run
from .test_dcnm_intf_pvlan_po_g1 import created
from .test_dcnm_intf_pvlan_po_host import PO_ITEM_NAME

HERE = os.path.dirname(__file__)
PO_FX = json.load(open(os.path.join(HERE, "fixtures", "pvlan_po_speed_diag_measured.json")))
VPC_FX = json.load(open(os.path.join(HERE, "fixtures", "pvlan_vpc_speed_diag_measured.json")))
PO_NAME, MEMBER = "Port-channel521", "Ethernet1/8"
ASSOC_2410 = [{"primary_vlan": 2410, "secondary_vlan": 2412}]


# ====================================================================================== Po: the module's gate on the measured entries
def _target(before, after, member_nv=None):
    member_nv = member_nv or PO_FX["member_nv"]
    return {"name": PO_NAME, "creates": False, "pre": (P.PO_HOST_POLICY, before), "post": (P.PO_HOST_POLICY, after),
            "members": [{"name": MEMBER, "pre": (P.PO_MEMBER_POLICY, member_nv),
                         "post": (P.PO_MEMBER_POLICY, P.po_member_nvpairs(after, member_nv, current_is_member=True))}]}


APPLY = ("parent_before_nv", "parent_after_nv", "apply_preview")
WITHDRAW = ("parent_withdraw_before_nv", "parent_withdraw_after_nv", "withdraw_preview")


def _assess(case, pending=None, running=None, expected=None, after=None):
    before_key, after_key, prev_key = case
    pv = PO_FX[prev_key]
    entry = {"pendingConfig": list(pv["pendingConfig"] if pending is None else pending),
             "runningConfig": ["!Command: show running-config"] + list(pv["runningConfig"] if running is None else running),
             "expectedConfig": list(pv["expectedConfig"] if expected is None else expected)}
    blocks, _g = P.split_blocks(entry["pendingConfig"])
    gate = dcnm_interface.DcnmIntf.__new__(dcnm_interface.DcnmIntf)
    return gate.dcnm_intf_pvlan_po_assess(blocks, entry, _target(PO_FX[before_key], after or PO_FX[after_key]))


def _member_index(lines, line, member="interface ethernet1/8"):
    start = lines.index(member)
    end = next((i for i in range(start + 1, len(lines)) if not lines[i].startswith(" ")), len(lines))
    return next(i for i in range(start + 1, end) if lines[i] == line)


@pytest.mark.parametrize("case", [APPLY, WITHDRAW], ids=["apply", "withdraw"])
def test_measured_po_speed_apply_and_withdrawal_deploy(case):
    assert _assess(case) == ("deploy", [])


@pytest.mark.parametrize("after_key, nv_key", [("after_apply_preview", "parent_after_nv"), ("after_withdraw_preview", "parent_withdraw_after_nv")])
def test_measured_post_deploy_previews_are_converged(after_key, nv_key):
    """After the deploy the member's running shows (apply) / lost (withdraw) the line: the same rule is NOT needed, the state converges."""
    pv = PO_FX[after_key]
    assert pv["pendingConfig"] == [] and pv["status"] == "In-Sync"
    entry = {"pendingConfig": [], "runningConfig": ["!"] + pv["runningConfig"], "expectedConfig": pv["expectedConfig"]}
    before = PO_FX[nv_key]
    gate = dcnm_interface.DcnmIntf.__new__(dcnm_interface.DcnmIntf)
    assert gate.dcnm_intf_pvlan_po_assess({}, entry, _target(before, before)) == ("converged", [])


def test_the_member_not_reflecting_the_inherited_speed_after_the_deploy_is_not_converged():
    """A member whose running did not follow (wrong readback) is never masked: with an empty pending it is a refusal."""
    pv = PO_FX["after_apply_preview"]
    running = list(pv["runningConfig"])
    del running[_member_index(running, "  speed 1000")]
    entry = {"pendingConfig": [], "runningConfig": ["!"] + running, "expectedConfig": pv["expectedConfig"]}
    gate = dcnm_interface.DcnmIntf.__new__(dcnm_interface.DcnmIntf)
    decision, problems = gate.dcnm_intf_pvlan_po_assess({}, entry, _target(PO_FX["parent_after_nv"], PO_FX["parent_after_nv"]))
    assert decision == "refuse" and "missing': ['speed 1000']" in problems[0]


def _with(lines, index, value):
    out = list(lines)
    out[index] = value
    return out


def _swap_member(lines, old, new):
    return _with(lines, _member_index(lines, old), new)


@pytest.mark.parametrize(
    "label, mutate",
    [
        ("member expected with another speed", lambda pv: dict(expected=_swap_member(pv["expectedConfig"], "  speed 1000", "  speed 10000"))),
        ("parent pending without the speed command", lambda pv: dict(pending=[x for x in pv["pendingConfig"] if x.strip() != "speed 1000"])),
        ("parent pending absent (empty)", lambda pv: dict(pending=[])),
        ("parent pending with the speed twice", lambda pv: dict(pending=pv["pendingConfig"][:-1] + ["  speed 1000"] + pv["pendingConfig"][-1:])),
        ("another member delta (duplex)", lambda pv: dict(expected=pv["expectedConfig"][:2] + ["  duplex full"] + pv["expectedConfig"][2:])),
        ("member of another port-channel", lambda pv: dict(running=[x.replace("group 521", "group 522") for x in pv["runningConfig"]])),
        ("member administratively up", lambda pv: dict(running=_swap_member(pv["runningConfig"], "  shutdown", "  no shutdown"))),
        ("capability line, not measured", lambda pv: dict(expected=pv["expectedConfig"][:2] + ["  no negotiate auto"] + pv["expectedConfig"][2:])),
    ],
)
def test_apply_boundaries_stay_refused(label, mutate):
    decision, problems = _assess(APPLY, **mutate(PO_FX["apply_preview"]))
    assert decision == "refuse", (label, problems)


def test_a_member_pending_that_carries_the_line_itself_follows_the_ordinary_validation():
    """Not the inheritance exception: a member stanza with its own `speed 1000` is validated as an ordinary positive line (RC1 form)."""
    pv = PO_FX["apply_preview"]
    pending = pv["pendingConfig"][:-1] + ["interface ethernet1/8", "  speed 1000"] + pv["pendingConfig"][-1:]
    assert _assess(APPLY, pending=pending) == ("deploy", [])


def _drop_parent_speed(lines):
    start = lines.index("interface port-channel521")
    return [x for i, x in enumerate(lines) if not (i > start and x == "  speed 1000")]


@pytest.mark.parametrize(
    "label, mutate",
    [
        ("withdrawal without `no speed 1000`", lambda pv: dict(pending=[x for x in pv["pendingConfig"] if "speed" not in x])),
        ("parent running without the speed (nothing to withdraw)", lambda pv: dict(running=_drop_parent_speed(pv["runningConfig"]))),
        ("member running with another speed", lambda pv: dict(running=_swap_member(pv["runningConfig"], "  speed 1000", "  speed 10000"))),
    ],
)
def test_withdrawal_boundaries_stay_refused(label, mutate):
    decision, problems = _assess(WITHDRAW, **mutate(PO_FX["withdraw_preview"]))
    assert decision == "refuse", (label, problems)


@pytest.mark.parametrize("speed, line", [("10Gb", "speed 10000"), ("100Mb", "speed 100")])
def test_an_unmeasured_speed_is_not_inherited(speed, line):
    """Only `speed 1000` is measured: the same shape with another speed stays refused (offline coverage, not a device statement)."""
    pv = PO_FX["apply_preview"]
    after = dict(PO_FX["parent_after_nv"], SPEED=speed)
    pending = [x.replace("speed 1000", line) for x in pv["pendingConfig"]]
    expected = [x.replace("speed 1000", line) for x in pv["expectedConfig"]]
    decision, _problems = _assess(APPLY, pending=pending, expected=expected, after=after)
    assert decision == "refuse"


def test_a_second_parent_change_next_to_the_speed_is_not_hidden():
    after = dict(PO_FX["parent_after_nv"], MTU="default")
    decision, _problems = _assess(APPLY, after=after)
    assert decision == "refuse"


# ====================================================================================== Po through main() (retargeted names)
def _retarget_po(lines):
    out = []
    for x in lines:
        x = x.replace("port-channel521", "port-channel10").replace("channel-group 521", "channel-group 10").replace("ethernet1/8", "ethernet1/7")
        out.append(x)
    return out


def _po_preview(key):
    pv = PO_FX[key]
    return preview(_retarget_po(pv["pendingConfig"]), running=_retarget_po(pv["runningConfig"]), expected=_retarget_po(pv["expectedConfig"]))


def _po_cfg(**profile):
    prof = {"mode": "pvlan", "pvlan_mode": "host"}
    prof.update(profile)
    return {"name": PO_ITEM_NAME, "type": "pc", "switch": [SWITCH_IP], "deploy": True, "profile": prof}


def _created_po():
    return created("host", ["switchport private-vlan host-association 2410 2412"], pvlan_association=ASSOC_2410)


def test_po_apply_then_repeat_through_main():
    ctrl = _created_po()
    ctrl.previews = [_po_preview("apply_preview")]
    status, result = run(ctrl, [_po_cfg(speed="1Gb")], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]["SPEED"] == "1Gb" and len(ctrl.deploys()) == 1
    ctrl.next_invocation()
    ctrl.calls = []
    ctrl.previews = [_po_preview("after_apply_preview")]
    status, result = run(ctrl, [_po_cfg(speed="1Gb")], state="merged")
    assert status == "exit" and result["changed"] is False and ctrl.writes() == [], result


def test_po_withdrawal_through_main():
    ctrl = _created_po()
    ctrl.detail["Port-channel10"]["nvPairs"]["SPEED"] = "1Gb"
    ctrl.previews = [_po_preview("withdraw_preview")]
    status, result = run(ctrl, [_po_cfg(members=[IF7], admin_state=False, pvlan_association=ASSOC_2410)], state="replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]["SPEED"] == "Auto" and len(ctrl.deploys()) == 1


def test_po_member_that_does_not_converge_after_the_deploy_fails_without_corrective_writes():
    ctrl = _created_po()
    ctrl.previews = [_po_preview("apply_preview")]
    ctrl.compliance = ["Out-of-Sync"] * 20
    status, result = run(ctrl, [_po_cfg(speed="1Gb")], state="merged")
    assert status == "fail" and "did not reach In-Sync" in result["msg"], result.get("msg")
    assert len(ctrl.bulk_bodies()) == 1 and len(ctrl.deploys()) == 1


# ====================================================================================== vPC through main(), both peers (retargeted names)
PEER = {"SN-A": (V.SN1, V.M1), "SN-B": (V.SN2, V.M2)}


def _retarget_vpc(lines, port):
    return [x.replace("port-channel522", "port-channel10").replace("channel-group 522", "channel-group 10").replace("vpc 522", "vpc 10")
            .replace("ethernet1/9", port.lower()) for x in lines]


def _vpc_preview(alias, key, mutate=None):
    serial, port = PEER[alias]
    pv = copy.deepcopy(VPC_FX["peers"][alias][key])
    if mutate:
        mutate(pv)
    return V.preview(_retarget_vpc(pv["pendingConfig"], port), serial=serial, running=_retarget_vpc(pv["runningConfig"], port),
                     expected=_retarget_vpc(pv["expectedConfig"], port))


def _vpc_ctrl(speed="Auto"):
    ctrl = V.created_ctrl(association=((2410, 2412),))
    parent = ctrl.parents[V.VPC]["nvPairs"]
    parent["SPEED"] = speed
    ctrl._expand_children(parent)
    return ctrl


def _vpc_item(**profile):
    return V.vpc_item(pvlan_association=ASSOC_2410, **profile)


def _queue(ctrl, preflight_key, gate_key, mutate=None):
    for alias in ("SN-A", "SN-B"):
        serial = PEER[alias][0]
        ctrl.vpc_previews[serial] = [_vpc_preview(alias, preflight_key), _vpc_preview(alias, gate_key, (mutate or {}).get(alias))]


def test_vpc_apply_on_both_peers_deploys_and_the_repeat_writes_nothing():
    ctrl = _vpc_ctrl()
    _queue(ctrl, "after_withdraw_preview", "apply_preview")
    status, res = V.run_vpc(ctrl, [_vpc_item(speed="1Gb")], state="merged")
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]["SPEED"] == "1Gb" and len(ctrl.deploys()) == 1
    ctrl.next_invocation()
    before = len(ctrl.writes())
    for alias in ("SN-A", "SN-B"):
        ctrl.vpc_previews[PEER[alias][0]] = [_vpc_preview(alias, "after_apply_preview")]
    status, res = V.run_vpc(ctrl, [_vpc_item(speed="1Gb")], state="merged")
    assert status == "exit" and res["changed"] is False and len(ctrl.writes()) == before, res


def test_vpc_withdrawal_on_both_peers_deploys():
    ctrl = _vpc_ctrl(speed="1Gb")
    _queue(ctrl, "after_apply_preview", "withdraw_preview")
    status, res = V.run_vpc(ctrl, [_vpc_item()], state="replaced")
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]["SPEED"] == "Auto" and len(ctrl.deploys()) == 1


def _peer_b_member_other_speed(pv):
    exp = pv["expectedConfig"]
    exp[_member_index(exp, "  speed 1000", "interface ethernet1/9")] = "  speed 10000"


def _peer_b_without_child_pending(pv):
    pv["pendingConfig"] = []
    pv["status"] = "In-Sync"


@pytest.mark.parametrize("mutate", [_peer_b_member_other_speed, _peer_b_without_child_pending], ids=["member-other-speed", "no-child-pending"])
def test_one_wrong_peer_stops_the_whole_vpc_before_any_deploy(mutate):
    """Peer A carries the measured, valid inheritance; peer B does not. The vPC is judged per peer on its own serial and preview: B's
    member is never inferred from A, and the whole batch is refused."""
    ctrl = _vpc_ctrl()
    _queue(ctrl, "after_withdraw_preview", "apply_preview", {"SN-B": mutate})
    status, res = V.run_vpc(ctrl, [_vpc_item(speed="1Gb")], state="merged")
    assert status == "fail" and ctrl.deploys() == [], res
    assert "peer 2" in res["msg"]
