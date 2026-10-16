"""DUPLEX: the member's `duplex full` of a PVLAN port-channel / vPC leg carried by the port-channel's own pending (MEASURED inheritance), plus F-A.

Sources (sanitized, read-only extracts of Alpha2's live diagnostics NEXT-A2-SD; raw captures stay outside the product):
  fixtures/pvlan_po_duplex_measured.json  -- G1: Po521 / Ethernet1/8, speed 1000 fixed, `duplex full` apply and withdrawal, previews before the
                                             deploy and the converged previews after each;
  fixtures/pvlan_vpc_duplex_measured.json -- G2: vPC522, Ethernet1/9, the same cases on BOTH peers, each on its own serial.
Measured: NDFC 12.6.0.267, N9K-C9300v 10.5(5), host mode, ONE member per port-channel / leg, admin down, border switches. NOT measured, refused here:
`duplex half`, a speed + duplex change in one transition, another speed, an MTU change with it, an up port. These tests are offline controller
DOUBLES fed with real captured previews; they are not the module's live acceptance. Several members are covered by the per-member validation only.
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
FX = json.load(open(os.path.join(HERE, "fixtures", "pvlan_po_duplex_measured.json")))
VFX = json.load(open(os.path.join(HERE, "fixtures", "pvlan_vpc_duplex_measured.json")))
PO_NAME, MEMBER, MEMBER2 = "Port-channel521", "Ethernet1/8", "Ethernet1/9"
ASSOC_2410 = [{"primary_vlan": 2410, "secondary_vlan": 2412}]
APPLY = ("parent_before_nv", "parent_after_nv", "apply_preview")
WITHDRAW = ("parent_withdraw_before_nv", "parent_withdraw_after_nv", "withdraw_preview")


# ====================================================================================== Po: the module's gate on the measured entries
def _target(before, after, members=(MEMBER,)):
    out = []
    for name in members:
        out.append(
            {
                "name": name,
                "pre": (P.PO_MEMBER_POLICY, FX["member_nv"]),
                "post": (P.PO_MEMBER_POLICY, P.po_member_nvpairs(after, FX["member_nv"], current_is_member=True)),
            }
        )
    return {"name": PO_NAME, "creates": False, "pre": (P.PO_HOST_POLICY, before), "post": (P.PO_HOST_POLICY, after), "members": out}


def _second_member(lines, drop=()):
    """The stanza of Ethernet1/8 duplicated for Ethernet1/9 (same lines), appended after the original."""
    out, grab = list(lines), []
    start = next(i for i, x in enumerate(lines) if x == "interface ethernet1/8")
    end = next((i for i in range(start + 1, len(lines)) if not lines[i].startswith(" ")), len(lines))
    grab = [x.replace("ethernet1/8", "ethernet1/9") for x in lines[start:end] if x.strip() not in drop]
    return out + grab


def _assess(case, pending=None, running=None, expected=None, after=None, before=None, members=(MEMBER,)):
    before_key, after_key, prev_key = case
    pv = FX[prev_key]
    entry = {
        "pendingConfig": list(pv["pendingConfig"] if pending is None else pending),
        "runningConfig": ["!Command: show running-config"] + list(pv["runningConfig"] if running is None else running),
        "expectedConfig": list(pv["expectedConfig"] if expected is None else expected),
    }
    blocks, _g = P.split_blocks(entry["pendingConfig"])
    gate = dcnm_interface.DcnmIntf.__new__(dcnm_interface.DcnmIntf)
    return gate.dcnm_intf_pvlan_po_assess(blocks, entry, _target(before or FX[before_key], after or FX[after_key], members))


def _member_index(lines, line, member="interface ethernet1/8"):
    start = lines.index(member)
    end = next((i for i in range(start + 1, len(lines)) if not lines[i].startswith(" ")), len(lines))
    return next(i for i in range(start + 1, end) if lines[i] == line)


def _swap_member(lines, old, new, member="interface ethernet1/8"):
    out = list(lines)
    out[_member_index(lines, old, member)] = new
    return out


@pytest.mark.parametrize("case", [APPLY, WITHDRAW], ids=["apply", "withdraw"])
def test_measured_po_duplex_apply_and_withdrawal_deploy(case):
    assert _assess(case) == ("deploy", [])


@pytest.mark.parametrize("after_key, nv_key", [("after_apply_preview", "parent_after_nv"), ("after_withdraw_preview", "parent_before_nv")])
def test_measured_post_deploy_previews_are_converged_noop(after_key, nv_key):
    pv = FX[after_key]
    assert pv["pendingConfig"] == [] and pv["status"] == "In-Sync"
    entry = {"pendingConfig": [], "runningConfig": ["!"] + pv["runningConfig"], "expectedConfig": pv["expectedConfig"]}
    gate = dcnm_interface.DcnmIntf.__new__(dcnm_interface.DcnmIntf)
    assert gate.dcnm_intf_pvlan_po_assess({}, entry, _target(FX[nv_key], FX[nv_key])) == ("converged", [])


def test_the_pending_holds_only_the_port_channel_stanza_in_both_directions():
    """The shape the rule relies on (MEASURED): one stanza, the port-channel's; no member stanza."""
    for key in ("apply_preview", "withdraw_preview"):
        heads = [x for x in FX[key]["pendingConfig"] if x.startswith("interface ")]
        assert heads == ["interface port-channel521"], key


def test_a_member_not_reflecting_the_inherited_duplex_after_the_deploy_is_not_converged():
    pv = FX["after_apply_preview"]
    running = list(pv["runningConfig"])
    del running[_member_index(running, "  duplex full")]
    entry = {"pendingConfig": [], "runningConfig": ["!"] + running, "expectedConfig": pv["expectedConfig"]}
    gate = dcnm_interface.DcnmIntf.__new__(dcnm_interface.DcnmIntf)
    decision, problems = gate.dcnm_intf_pvlan_po_assess({}, entry, _target(FX["parent_after_nv"], FX["parent_after_nv"]))
    assert decision == "refuse" and "missing': ['duplex full']" in problems[0]


def _po_stanza_lines(lines, drop):
    """`lines` without the given line inside the port-channel stanza only (the member keeps its own)."""
    head = lines.index("interface port-channel521")
    return lines[: head + 1] + [x for x in lines[head + 1 :] if x != drop]


def _expected_member_half(pv):
    return dict(
        expected=[
            x.replace("duplex full", "duplex half") if i < pv["expectedConfig"].index("interface port-channel521") else x
            for i, x in enumerate(pv["expectedConfig"])
        ]
    )


def _pending_without_duplex(pv):
    return dict(pending=[x for x in pv["pendingConfig"] if x.strip() != "duplex full"])


def _pending_empty(pv):
    return dict(pending=[])


def _pending_duplex_twice(pv):
    return dict(pending=pv["pendingConfig"][:-1] + ["  duplex full"] + pv["pendingConfig"][-1:])


def _pending_extra_command(pv):
    return dict(pending=pv["pendingConfig"][:-1] + ["  description foreign"] + pv["pendingConfig"][-1:])


def _member_running_without_speed(pv):
    run_ = list(pv["runningConfig"])
    del run_[_member_index(run_, "  speed 1000")]
    return dict(running=run_)


def _member_of_another_po(pv):
    return dict(running=[x.replace("group 521", "group 522") for x in pv["runningConfig"]])


def _member_up(pv):
    return dict(running=_swap_member(pv["runningConfig"], "  shutdown", "  no shutdown"))


def _expected_negotiate_auto(pv):
    return dict(expected=pv["expectedConfig"][:2] + ["  no negotiate auto"] + pv["expectedConfig"][2:])


def _parent_already_holds_duplex(pv):
    return dict(running=pv["runningConfig"][:-1] + ["  duplex full"] + pv["runningConfig"][-1:])


@pytest.mark.parametrize(
    "label, mutate",
    [
        ("member expected with duplex half", _expected_member_half),
        ("parent pending without the duplex command", _pending_without_duplex),
        ("parent pending absent (empty)", _pending_empty),
        ("parent pending with the duplex twice", _pending_duplex_twice),
        ("parent pending with an unexpected extra command", _pending_extra_command),
        ("member drift: member running without its speed", _member_running_without_speed),
        ("member of another port-channel", _member_of_another_po),
        ("member administratively up", _member_up),
        ("capability line, not measured", _expected_negotiate_auto),
        ("parent already holds the duplex", _parent_already_holds_duplex),
    ],
)
def test_apply_boundaries_stay_refused(label, mutate):
    decision, problems = _assess(APPLY, **mutate(FX["apply_preview"]))
    assert decision == "refuse", (label, problems)


def test_a_member_pending_that_carries_the_line_itself_follows_the_ordinary_validation():
    """Not the inheritance rule: a member stanza with its own `duplex full` is validated as an ordinary positive line."""
    pv = FX["apply_preview"]
    pending = pv["pendingConfig"][:-1] + ["interface ethernet1/8", "  duplex full"] + pv["pendingConfig"][-1:]
    assert _assess(APPLY, pending=pending) == ("deploy", [])


def _withdraw_pending_without_no_duplex(pv):
    return dict(pending=[x for x in pv["pendingConfig"] if "duplex" not in x])


def _withdraw_parent_running_without_duplex(pv):
    return dict(running=_po_stanza_lines(pv["runningConfig"], "  duplex full"))


def _withdraw_member_running_half(pv):
    return dict(running=_swap_member(pv["runningConfig"], "  duplex full", "  duplex half"))


def _withdraw_extra_no_speed(pv):
    return dict(pending=pv["pendingConfig"][:-1] + ["  no speed 1000"] + pv["pendingConfig"][-1:])


@pytest.mark.parametrize(
    "label, mutate",
    [
        ("withdrawal without `no duplex full`", _withdraw_pending_without_no_duplex),
        ("parent running without the duplex (nothing to withdraw)", _withdraw_parent_running_without_duplex),
        ("member running with duplex half", _withdraw_member_running_half),
        ("member running without the fixed speed", _member_running_without_speed),
        ("an extra withdrawal in the parent pending", _withdraw_extra_no_speed),
    ],
)
def test_withdrawal_boundaries_stay_refused(label, mutate):
    decision, problems = _assess(WITHDRAW, **mutate(FX["withdraw_preview"]))
    assert decision == "refuse", (label, problems)


def test_duplex_half_is_not_inherited():
    pv = FX["apply_preview"]
    after = dict(FX["parent_after_nv"], PORT_DUPLEX_MODE="half")

    def sw(lines):
        return [x.replace("duplex full", "duplex half") for x in lines]

    assert _assess(APPLY, pending=sw(pv["pendingConfig"]), expected=sw(pv["expectedConfig"]), after=after)[0] == "refuse"


@pytest.mark.parametrize("speed, line", [("10Gb", "speed 10000"), ("100Mb", "speed 100")])
def test_a_fixed_speed_other_than_1000_is_not_covered(speed, line):
    pv = FX["apply_preview"]

    def sw(lines):
        return [x.replace("speed 1000", line) for x in lines]

    nv = dict(FX["parent_before_nv"], SPEED=speed)
    decision, _p = _assess(
        APPLY,
        pending=sw(pv["pendingConfig"]),
        expected=sw(pv["expectedConfig"]),
        running=sw(pv["runningConfig"]),
        before=nv,
        after=dict(nv, PORT_DUPLEX_MODE="full"),
    )
    assert decision == "refuse"


def test_a_combined_speed_and_duplex_change_is_not_admitted_by_this_rule():
    """Speed Auto -> 1Gb AND duplex auto -> full in one change: neither line is measured to be inherited together."""
    pv = FX["apply_preview"]
    running = [x for x in pv["runningConfig"] if x.strip() != "speed 1000"]
    before = dict(FX["parent_before_nv"], SPEED="Auto")
    decision, _p = _assess(APPLY, running=running, before=before)
    assert decision == "refuse"


def test_an_mtu_change_next_to_the_duplex_is_not_hidden():
    after = dict(FX["parent_after_nv"], MTU="default")
    assert _assess(APPLY, after=after)[0] == "refuse"


# ---- several members: each is validated on its own state; the rule adds no global limit
def test_two_members_both_following_deploy():
    pv = FX["apply_preview"]
    decision = _assess(APPLY, running=_second_member(pv["runningConfig"]), expected=_second_member(pv["expectedConfig"]), members=(MEMBER, MEMBER2))
    assert decision == ("deploy", [])


def test_two_members_withdrawal_deploys():
    pv = FX["withdraw_preview"]
    decision = _assess(WITHDRAW, running=_second_member(pv["runningConfig"]), expected=_second_member(pv["expectedConfig"]), members=(MEMBER, MEMBER2))
    assert decision == ("deploy", [])


def test_a_second_member_with_drift_refuses_the_whole_target_and_names_it():
    pv = FX["apply_preview"]
    running = _second_member(pv["runningConfig"], drop=("speed 1000",))
    decision, problems = _assess(APPLY, running=running, expected=_second_member(pv["expectedConfig"]), members=(MEMBER, MEMBER2))
    assert decision == "refuse" and any("ethernet1/9" in x.lower() for x in problems), problems


def test_a_second_member_already_holding_the_duplex_is_judged_on_its_own_state():
    """Member 2 already runs `duplex full` (no inheritance needed for it); member 1 still needs the rule. Both are judged separately."""
    pv = FX["apply_preview"]
    running = _second_member(pv["runningConfig"])
    running.insert(running.index("interface ethernet1/9") + 1, "  duplex full")
    assert _assess(APPLY, running=running, expected=_second_member(pv["expectedConfig"]), members=(MEMBER, MEMBER2)) == ("deploy", [])


def test_a_second_member_running_duplex_half_is_refused_even_if_the_first_follows():
    pv = FX["apply_preview"]
    running = _second_member(pv["runningConfig"])
    running.insert(running.index("interface ethernet1/9") + 1, "  duplex half")
    decision, _p = _assess(APPLY, running=running, expected=_second_member(pv["expectedConfig"]), members=(MEMBER, MEMBER2))
    assert decision == "refuse"


# ====================================================================================== Po through main() (retargeted names)
def _retarget_po(lines):
    return [
        x.replace("port-channel521", "port-channel10").replace("channel-group 521", "channel-group 10").replace("ethernet1/8", "ethernet1/7") for x in lines
    ]


def _po_preview(key):
    pv = FX[key]
    return preview(_retarget_po(pv["pendingConfig"]), running=_retarget_po(pv["runningConfig"]), expected=_retarget_po(pv["expectedConfig"]))


def _po_cfg(**profile):
    prof = {"mode": "pvlan", "pvlan_mode": "host"}
    prof.update(profile)
    return {"name": PO_ITEM_NAME, "type": "pc", "switch": [SWITCH_IP], "deploy": True, "profile": prof}


def _created_po(speed="1Gb", duplex="auto"):
    ctrl = created("host", ["switchport private-vlan host-association 2410 2412"], pvlan_association=ASSOC_2410)
    nv = ctrl.detail["Port-channel10"]["nvPairs"]
    nv["SPEED"], nv["PORT_DUPLEX_MODE"] = speed, duplex
    return ctrl


def test_po_apply_then_repeat_through_main_with_the_speed_omitted_in_merged():
    """merged resolves the omitted speed from HAVE (fixed 1Gb): it is not Auto, so F-A does not apply."""
    ctrl = _created_po()
    ctrl.previews = [_po_preview("apply_preview")]
    status, result = run(ctrl, [_po_cfg(duplex="full")], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    sent = ctrl.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]
    assert (sent["PORT_DUPLEX_MODE"], sent["SPEED"]) == ("full", "1Gb") and len(ctrl.deploys()) == 1
    ctrl.next_invocation()
    ctrl.calls = []
    ctrl.previews = [_po_preview("after_apply_preview")]
    status, result = run(ctrl, [_po_cfg(duplex="full")], state="merged")
    assert status == "exit" and result["changed"] is False and ctrl.writes() == [], result


def test_po_withdrawal_through_main():
    ctrl = _created_po(duplex="full")
    ctrl.previews = [_po_preview("withdraw_preview")]
    status, result = run(ctrl, [_po_cfg(speed="1Gb", members=[IF7], admin_state=False, pvlan_association=ASSOC_2410)], state="replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    sent = ctrl.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]
    assert (sent["PORT_DUPLEX_MODE"], sent["SPEED"]) == ("auto", "1Gb") and len(ctrl.deploys()) == 1


def test_po_member_that_does_not_converge_after_the_deploy_fails_without_corrective_writes():
    ctrl = _created_po()
    ctrl.previews = [_po_preview("apply_preview")]
    ctrl.compliance = ["Out-of-Sync"] * 20
    status, result = run(ctrl, [_po_cfg(duplex="full")], state="merged")
    assert status == "fail" and "did not reach In-Sync" in result["msg"], result.get("msg")
    assert len(ctrl.bulk_bodies()) == 1 and len(ctrl.deploys()) == 1


@pytest.mark.parametrize(
    "label, ctrl_args, profile, state",
    [
        ("merged duplex full, HAVE speed Auto", dict(speed="Auto"), dict(duplex="full"), "merged"),
        ("merged speed Auto explicit over HAVE duplex full", dict(speed="1Gb", duplex="full"), dict(speed="Auto"), "merged"),
        (
            "replaced duplex full without a speed",
            dict(speed="1Gb"),
            dict(duplex="full", members=[IF7], admin_state=False, pvlan_association=ASSOC_2410),
            "replaced",
        ),
        ("merged duplex half, HAVE speed Auto", dict(speed="Auto"), dict(duplex="half"), "merged"),
    ],
)
def test_f_a_duplex_without_a_fixed_speed_is_refused_before_any_write(label, ctrl_args, profile, state):
    ctrl = _created_po(**ctrl_args)
    status, result = run(ctrl, [_po_cfg(**profile)], state=state)
    assert status == "fail" and "needs a fixed speed" in result["msg"], (label, result.get("msg"))
    assert ctrl.writes() == [] and ctrl.bulk_bodies() == [] and ctrl.deploys() == [], label


def test_f_a_creation_with_duplex_and_speed_auto_is_refused_before_any_write():
    ctrl = created("host", ["switchport private-vlan host-association 2410 2412"], pvlan_association=ASSOC_2410)
    for key in list(ctrl.detail):
        ctrl.detail.pop(key)  # a creation
    status, result = run(ctrl, [_po_cfg(members=[IF7], admin_state=False, pvlan_association=ASSOC_2410, duplex="full")], state="merged")
    assert status == "fail" and "needs a fixed speed" in result["msg"], result.get("msg")
    assert ctrl.bulk_bodies() == [] and ctrl.creates() == [] and ctrl.deploys() == []


def test_f_a_does_not_block_the_withdrawal_towards_auto_nor_query():
    ctrl = _created_po(speed="1Gb", duplex="full")
    ctrl.previews = [_po_preview("withdraw_preview")]
    status, result = run(ctrl, [_po_cfg(duplex="auto")], state="merged")
    assert status == "exit" and "needs a fixed speed" not in str(result.get("msg", "")), result.get("msg")
    ctrl = _created_po(speed="Auto", duplex="full")  # an inconsistent HAVE must still be readable
    status, result = run(ctrl, [{"name": PO_ITEM_NAME, "type": "pc", "switch": [SWITCH_IP]}], state="query")
    assert status == "exit" and ctrl.writes() == [], result.get("msg")


# ====================================================================================== vPC through main(), both peers (retargeted names)
PEER = {"SN-A": (V.SN1, V.M1), "SN-B": (V.SN2, V.M2)}


def _retarget_vpc(lines, port):
    return [
        x.replace("port-channel522", "port-channel10")
        .replace("channel-group 522", "channel-group 10")
        .replace("vpc 522", "vpc 10")
        .replace("ethernet1/9", port.lower())
        for x in lines
    ]


def _vpc_preview(alias, key, mutate=None, serial=None):
    sn, port = PEER[alias]
    pv = copy.deepcopy(VFX["peers"][alias][key])
    if mutate:
        mutate(pv)
    return V.preview(
        _retarget_vpc(pv["pendingConfig"], port),
        serial=serial or sn,
        running=_retarget_vpc(pv["runningConfig"], port),
        expected=_retarget_vpc(pv["expectedConfig"], port),
    )


def _vpc_ctrl(speed="1Gb", duplex="auto"):
    ctrl = V.created_ctrl(association=((2410, 2412),))
    parent = ctrl.parents[V.VPC]["nvPairs"]
    parent["SPEED"], parent["PORT_DUPLEX_MODE"] = speed, duplex
    ctrl._expand_children(parent)
    return ctrl


def _vpc_item(**profile):
    return V.vpc_item(pvlan_association=ASSOC_2410, **profile)


def _queue(ctrl, preflight_key, gate_key, mutate=None, serials=None):
    for alias in ("SN-A", "SN-B"):
        sn = PEER[alias][0]
        ctrl.vpc_previews[sn] = [_vpc_preview(alias, preflight_key), _vpc_preview(alias, gate_key, (mutate or {}).get(alias), (serials or {}).get(alias))]


def _gate(res, site, serial):
    recs = [g for g in res["pvlan_gate"] if g["site"] == site and g["serial"] == serial]
    assert len(recs) == 1, res["pvlan_gate"]
    return recs[0]


def test_vpc_apply_on_both_peers_uses_each_legs_own_child_and_the_repeat_writes_nothing():
    ctrl = _vpc_ctrl()
    _queue(ctrl, "after_withdraw_preview", "apply_preview")
    status, res = V.run_vpc(ctrl, [_vpc_item(duplex="full")], state="merged")
    assert status == "exit" and res["changed"] is True, res.get("msg")
    sent = json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]
    assert (sent["PORT_DUPLEX_MODE"], sent["SPEED"]) == ("full", "1Gb") and len(ctrl.modifies()) == 1 and len(ctrl.deploys()) == 1
    for serial in (V.SN1, V.SN2):
        assert _gate(res, "prior", serial)["targets"] == {V.VPC: "converged"}
        assert _gate(res, "deploy", serial)["targets"] == {V.VPC: "deploy"}
    ctrl.next_invocation()
    before = len(ctrl.writes())
    for alias in ("SN-A", "SN-B"):
        ctrl.vpc_previews[PEER[alias][0]] = [_vpc_preview(alias, "after_apply_preview")]
    status, res = V.run_vpc(ctrl, [_vpc_item(duplex="full")], state="merged")
    assert status == "exit" and res["changed"] is False and len(ctrl.writes()) == before, res


def test_vpc_withdrawal_on_both_peers_deploys():
    ctrl = _vpc_ctrl(duplex="full")
    _queue(ctrl, "after_apply_preview", "withdraw_preview")
    status, res = V.run_vpc(ctrl, [_vpc_item(speed="1Gb")], state="replaced")
    assert status == "exit" and res["changed"] is True, res.get("msg")
    sent = json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]
    assert (sent["PORT_DUPLEX_MODE"], sent["SPEED"]) == ("auto", "1Gb") and len(ctrl.deploys()) == 1


def _peer_b_member_duplex_half(pv):
    exp = pv["expectedConfig"]
    exp[_member_index(exp, "  duplex full", "interface ethernet1/9")] = "  duplex half"


def _peer_b_without_child_pending(pv):
    pv["pendingConfig"] = []
    pv["status"] = "In-Sync"


def _peer_b_unexpected_pending(pv):
    pv["pendingConfig"] = pv["pendingConfig"][:-1] + ["  description foreign"] + pv["pendingConfig"][-1:]


def _peer_b_duplicate_duplex(pv):
    pv["pendingConfig"] = pv["pendingConfig"][:-1] + ["  duplex full"] + pv["pendingConfig"][-1:]


def _peer_b_member_drift(pv):
    run_ = pv["runningConfig"]
    del run_[_member_index(run_, "  speed 1000", "interface ethernet1/9")]


@pytest.mark.parametrize(
    "mutate",
    [_peer_b_member_duplex_half, _peer_b_without_child_pending, _peer_b_unexpected_pending, _peer_b_duplicate_duplex, _peer_b_member_drift],
    ids=["member-duplex-half", "no-child-pending", "unexpected-pending", "duplicate-duplex", "member-drift"],
)
def test_one_wrong_peer_stops_the_whole_vpc_before_any_deploy(mutate):
    """Peer A carries the measured, valid inheritance; peer B does not. Judged per peer on its own serial and preview: B's member is never inferred
    from A, and the whole vPC is refused."""
    ctrl = _vpc_ctrl()
    _queue(ctrl, "after_withdraw_preview", "apply_preview", {"SN-B": mutate})
    status, res = V.run_vpc(ctrl, [_vpc_item(duplex="full")], state="merged")
    assert status == "fail" and ctrl.deploys() == [], res
    assert "peer 2" in res["msg"]


def test_the_child_of_the_other_serial_is_never_used_for_a_leg():
    """Peer B's preview slot answered with peer A's entry (its switchId): the leg of B finds no entry of its own serial and is refused."""
    ctrl = _vpc_ctrl()
    _queue(ctrl, "after_withdraw_preview", "apply_preview", serials={"SN-B": V.SN1})
    status, res = V.run_vpc(ctrl, [_vpc_item(duplex="full")], state="merged")
    assert status == "fail" and ctrl.deploys() == [] and "peer 2" in res["msg"], res


@pytest.mark.parametrize(
    "label, ctrl_args, profile",
    [
        ("merged duplex full, HAVE speed Auto", dict(speed="Auto"), dict(duplex="full")),
        ("merged speed Auto over HAVE duplex full", dict(speed="1Gb", duplex="full"), dict(speed="Auto")),
        ("merged duplex half, HAVE speed Auto", dict(speed="Auto"), dict(duplex="half")),
    ],
)
def test_f_a_vpc_duplex_without_a_fixed_speed_is_refused_before_any_write(label, ctrl_args, profile):
    ctrl = _vpc_ctrl(**ctrl_args)
    status, res = V.run_vpc(ctrl, [_vpc_item(**profile)], state="merged")
    assert status == "fail" and "needs a fixed speed" in res["msg"], (label, res.get("msg"))
    assert ctrl.writes() == [] and ctrl.deploys() == [], label


def test_f_a_vpc_creation_with_duplex_and_speed_auto_is_refused_before_any_write():
    ctrl = V.baseline_ctrl()
    status, res = V.run_vpc(ctrl, [_vpc_item(duplex="full")], state="merged")
    assert status == "fail" and "needs a fixed speed" in res["msg"], res.get("msg")
    assert ctrl.writes() == []


def test_f_a_vpc_withdrawal_towards_auto_is_not_blocked():
    ctrl = _vpc_ctrl(duplex="full")
    _queue(ctrl, "after_apply_preview", "withdraw_preview")
    status, res = V.run_vpc(ctrl, [_vpc_item(duplex="auto")], state="merged")
    assert status == "exit" and "needs a fixed speed" not in str(res.get("msg", "")), res.get("msg")


# ---- the helper-level contract of F-A
@pytest.mark.parametrize(
    "nv, blocked",
    [
        ({"PORT_DUPLEX_MODE": "full", "SPEED": "Auto"}, True),
        ({"PORT_DUPLEX_MODE": "half", "SPEED": ""}, True),
        ({"PORT_DUPLEX_MODE": "full"}, True),
        ({"PORT_DUPLEX_MODE": "full", "SPEED": "1Gb"}, False),
        ({"PORT_DUPLEX_MODE": "auto", "SPEED": "Auto"}, False),
        ({"PORT_DUPLEX_MODE": "auto", "SPEED": "1Gb"}, False),
        ({}, False),
    ],
)
def test_f_a_helper_contract(nv, blocked):
    problems = [p for p in P.companion_state_problems(nv, {}) if "needs a fixed speed" in p]
    assert bool(problems) is blocked, (nv, problems)


# ====================================================================================== R1 / F2: the combined speed + duplex change is refused BEFORE the write
COMBINED = "speed and duplex cannot change in the same request"
PO_CHILD = "port-channel10"


def _no_write(ctrl):
    return ctrl.writes() == [] and ctrl.bulk_bodies() == [] and ctrl.deploys() == []


@pytest.mark.parametrize(
    "label, ctrl_args, profile, state",
    [
        ("Auto/auto -> 1Gb + full (the advice the first F-A message gave)", dict(speed="Auto"), dict(speed="1Gb", duplex="full"), "merged"),
        ("1Gb/auto -> 10Gb + full", dict(speed="1Gb"), dict(speed="10Gb", duplex="full"), "merged"),
        (
            "1Gb/full -> Auto + auto (withdraw both, replaced omits speed)",
            dict(speed="1Gb", duplex="full"),
            dict(duplex="auto", members=[IF7], admin_state=False, pvlan_association=ASSOC_2410),
            "replaced",
        ),
        ("1Gb/full -> speed Auto + duplex auto explicit", dict(speed="1Gb", duplex="full"), dict(speed="Auto", duplex="auto"), "merged"),
    ],
)
def test_f2_po_combined_change_is_refused_before_any_write_with_the_two_step_advice(label, ctrl_args, profile, state):
    ctrl = _created_po(**ctrl_args)
    status, result = run(ctrl, [_po_cfg(**profile)], state=state)
    assert status == "fail" and COMBINED in result["msg"], (label, result.get("msg"))
    assert "first, in its own request" in result["msg"] and "duplex auto first and then speed Auto" in result["msg"]
    assert "ALREADY changed" not in result["msg"] and _no_write(ctrl), label


def test_f2_po_restating_an_equal_value_is_not_a_change():
    """HAVE 1Gb/auto: `speed: 1Gb` restated next to the duplex change is a duplex change only (the measured transition)."""
    ctrl = _created_po(speed="1Gb")
    ctrl.previews = [_po_preview("apply_preview")]
    status, result = run(ctrl, [_po_cfg(speed="1Gb", duplex="full")], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.bulk_bodies()) == 1 and len(ctrl.deploys()) == 1
    ctrl2 = _created_po(speed="1Gb", duplex="full")
    status, result = run(ctrl2, [_po_cfg(speed="1Gb", duplex="full")], state="merged")
    assert status == "exit" and result["changed"] is False and ctrl2.writes() == []


def test_f2_po_creation_with_both_values_is_still_supported():
    ctrl = created("host", ["switchport private-vlan host-association 2410 2412"], pvlan_association=ASSOC_2410)
    for key in list(ctrl.detail):
        ctrl.detail.pop(key)
    status, result = run(ctrl, [_po_cfg(members=[IF7], admin_state=False, pvlan_association=ASSOC_2410, speed="1Gb", duplex="full")], state="merged")
    assert COMBINED not in str(result.get("msg", "")) and "needs a fixed speed" not in str(result.get("msg", "")), result.get("msg")
    assert len(ctrl.bulk_bodies()) == 1 or status != "exit"


def test_f2_separate_changes_and_the_duplex_withdrawal_are_not_blocked_and_query_is_untouched():
    ctrl = _created_po(speed="Auto")
    ctrl.previews = []
    status, result = run(ctrl, [_po_cfg(speed="1Gb")], state="merged")  # speed alone
    assert COMBINED not in str(result.get("msg", "")), result.get("msg")
    ctrl = _created_po(speed="1Gb", duplex="full")
    ctrl.previews = [_po_preview("withdraw_preview")]
    status, result = run(ctrl, [_po_cfg(duplex="auto")], state="merged")  # duplex withdrawal alone
    assert status == "exit" and COMBINED not in str(result.get("msg", "")), result.get("msg")
    ctrl = _created_po(speed="Auto", duplex="full")
    status, result = run(ctrl, [{"name": PO_ITEM_NAME, "type": "pc", "switch": [SWITCH_IP]}], state="query")
    assert status == "exit" and ctrl.writes() == []


def test_f2_helper_contract():

    def nv(s, d):
        return {"SPEED": s, "PORT_DUPLEX_MODE": d}

    assert P.speed_duplex_combined_change(nv("Auto", "auto"), nv("1Gb", "full"))
    assert P.speed_duplex_combined_change(nv("1Gb", "full"), nv("Auto", "auto"))
    assert not P.speed_duplex_combined_change(nv("1Gb", "auto"), nv("1Gb", "full"))  # duplex alone
    assert not P.speed_duplex_combined_change(nv("Auto", "auto"), nv("1Gb", "auto"))  # speed alone
    assert not P.speed_duplex_combined_change(nv("1Gb", "full"), nv("1gb ", "FULL"))  # restated, normalized
    assert not P.speed_duplex_combined_change(None, nv("1Gb", "full"))  # creation
    assert not P.speed_duplex_combined_change({}, nv("Auto", "auto"))  # absent = template default


@pytest.mark.parametrize(
    "label, parent, profile",
    [
        ("parent Auto/auto -> 1Gb + full", dict(speed="Auto"), dict(speed="1Gb", duplex="full")),
        ("parent 1Gb/full -> Auto + auto", dict(speed="1Gb", duplex="full"), dict(speed="Auto", duplex="auto")),
    ],
)
def test_f2_vpc_parent_combined_change_is_refused_before_any_write(label, parent, profile):
    ctrl = _vpc_ctrl(**parent)
    status, res = V.run_vpc(ctrl, [_vpc_item(**profile)], state="merged")
    assert status == "fail" and COMBINED in res["msg"], (label, res.get("msg"))
    assert ctrl.writes() == [] and ctrl.deploys() == [], label


def test_f2_vpc_one_peer_needing_the_combined_change_refuses_the_whole_invocation():
    """The parent says 1Gb/auto, so `duplex: full` is a duplex change for the parent; the child of peer 2 diverged to Auto. That peer would
    go Auto -> 1Gb and auto -> full at once: the invocation is refused with no write on EITHER peer."""
    ctrl = _vpc_ctrl(speed="1Gb")
    ctrl.nodes[V.SN2][PO_CHILD]["nvPairs"]["SPEED"] = "Auto"
    status, res = V.run_vpc(ctrl, [_vpc_item(duplex="full")], state="merged")
    assert status == "fail" and COMBINED in res["msg"], res.get("msg")
    assert ctrl.writes() == [] and ctrl.deploys() == []
    assert V.SN2 in res["msg"] and V.SN1 not in res["msg"]


def test_f2_vpc_restating_an_equal_value_and_the_duplex_alone_are_not_blocked():
    ctrl = _vpc_ctrl(speed="1Gb")
    _queue(ctrl, "after_withdraw_preview", "apply_preview")
    status, res = V.run_vpc(ctrl, [_vpc_item(speed="1Gb", duplex="full")], state="merged")
    assert status == "exit" and res["changed"] is True and COMBINED not in str(res.get("msg", "")), res.get("msg")


# ====================================================================================== R1 / F3: the stored duplex is read back
def _force_duplex_after_modify(ctrl, apply):
    base_call = type(ctrl).__call__

    def call(self, mod, method, path, data=None):
        out = base_call(self, mod, method, path, data)
        if method == "POST" and path.endswith("/rest/interface/modify"):
            apply(self)
        return out

    ctrl.__class__ = type("ForcedDuplex", (type(ctrl),), {"__call__": call})
    return ctrl


@pytest.mark.parametrize("stored", ["auto", None, "MISSING"], ids=["auto", "null", "absent"])
def test_f3_po_readback_fails_when_the_controller_does_not_hold_the_requested_duplex(stored):
    ctrl = _created_po(speed="1Gb")
    ctrl.previews = [_po_preview("apply_preview")]

    def force(self):
        nv = self.detail["Port-channel10"]["nvPairs"]
        nv.pop("PORT_DUPLEX_MODE", None) if stored == "MISSING" else nv.__setitem__("PORT_DUPLEX_MODE", stored)

    status, result = run(_force_duplex_after_modify(ctrl, force), [_po_cfg(duplex="full")], state="merged")
    assert status == "fail" and "readback differs in" in result["msg"] and "PORT_DUPLEX_MODE" in result["msg"], result.get("msg")
    assert len(ctrl.bulk_bodies()) == 1 and len(ctrl.deploys()) == 1  # no corrective write


def test_f3_po_readback_control_positive_and_withdrawal_to_auto_with_an_absent_key():
    ctrl = _created_po(speed="1Gb")
    ctrl.previews = [_po_preview("apply_preview")]
    status, result = run(ctrl, [_po_cfg(duplex="full")], state="merged")
    assert status == "exit", result.get("msg")  # the stored full is read back equal (also in another case)
    ctrl = _created_po(speed="1Gb", duplex="full")
    ctrl.previews = [_po_preview("withdraw_preview")]

    def force(self):
        self.detail["Port-channel10"]["nvPairs"].pop("PORT_DUPLEX_MODE", None)  # absent = the template's own `auto`

    status, result = run(_force_duplex_after_modify(ctrl, force), [_po_cfg(duplex="auto")], state="merged")
    assert status == "exit", result.get("msg")


def test_f3_vpc_parent_readback_fails_on_a_wrong_stored_duplex_without_a_corrective_write():
    ctrl = _vpc_ctrl(speed="1Gb")
    _queue(ctrl, "after_withdraw_preview", "apply_preview")

    def force(self):
        self.parents[V.VPC]["nvPairs"]["PORT_DUPLEX_MODE"] = "auto"

    status, res = V.run_vpc(_force_duplex_after_modify(ctrl, force), [_vpc_item(duplex="full")], state="merged")
    assert status == "fail" and "parent PORT_DUPLEX_MODE" in res["msg"], res.get("msg")
    assert len(ctrl.modifies()) == 1


@pytest.mark.parametrize("serial_alias, stored", [("SN-A", "auto"), ("SN-B", "auto"), ("SN-B", None)])
def test_f3_vpc_child_readback_names_the_peer_that_does_not_hold_the_duplex(serial_alias, stored):
    ctrl = _vpc_ctrl(speed="1Gb")
    _queue(ctrl, "after_withdraw_preview", "apply_preview")
    target = PEER[serial_alias][0]

    def force(self):
        self.nodes[target][PO_CHILD]["nvPairs"]["PORT_DUPLEX_MODE"] = stored

    status, res = V.run_vpc(_force_duplex_after_modify(ctrl, force), [_vpc_item(duplex="full")], state="merged")
    other = V.SN2 if target == V.SN1 else V.SN1
    assert status == "fail" and "PORT_DUPLEX_MODE" in res["msg"] and target in res["msg"] and other not in res["msg"], res.get("msg")


def test_f3_vpc_child_differences_helper_levels():
    expected = {"PORT_DUPLEX_MODE": "full", "SPEED": "1Gb", "PVLAN_MODE": "host"}
    base = dict(expected)
    assert "PORT_DUPLEX_MODE" not in P.vpc_child_differences(base, expected)
    assert "PORT_DUPLEX_MODE" in P.vpc_child_differences(dict(base, PORT_DUPLEX_MODE="auto"), expected)
    assert "PORT_DUPLEX_MODE" in P.vpc_child_differences(dict(base, PORT_DUPLEX_MODE=None), expected)
    absent = dict(base)
    del absent["PORT_DUPLEX_MODE"]
    assert "PORT_DUPLEX_MODE" in P.vpc_child_differences(absent, expected)


def test_f3_po_and_vpc_same_normalize_only_the_case():
    assert P.po_intent_same("PORT_DUPLEX_MODE", {"PORT_DUPLEX_MODE": "Full"}, {"PORT_DUPLEX_MODE": "full"})
    assert not P.po_intent_same("PORT_DUPLEX_MODE", {"PORT_DUPLEX_MODE": None}, {"PORT_DUPLEX_MODE": "full"})
    assert not P.po_intent_same("PORT_DUPLEX_MODE", {}, {"PORT_DUPLEX_MODE": "full"})
    assert P.po_intent_same("PORT_DUPLEX_MODE", {}, {})
    assert P.vpc_same("PORT_DUPLEX_MODE", "FULL", "full") and not P.vpc_same("PORT_DUPLEX_MODE", None, "full")
