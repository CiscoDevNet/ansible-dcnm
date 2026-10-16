"""RC1: a non-Auto speed on the Ethernet, port-channel and vPC PVLAN parents, and freeform commands on the port-channel (`cmds`) and
the vPC (`peer1_cmds`/`peer2_cmds`).

NOT LIVE TESTED. Real main(); only the external boundary is mocked, through the EXISTING harnesses. Every preview below is SYNTHETIC,
written BY HAND from the captured templates (int_pvlan_host 354-361, int_port_channel_pvlan_host 464-471/507-564, int_vpc_pvlan_host
472-499/640-706, int_vpc_pvlan_po 258-269/323-325) and from the captured interface_utility.findInheritedCommandsInPOFF. Measured: only
SPEED "1Gb" -> `speed 1000` (regular int_trunk_host). Inferred: the other speed keywords, the `no negotiate auto` the controller adds by
device capability, the identity of adjustIntfFreeformConfig for a top-level command, and the form of every withdrawal line.

The REFERENCE section drives the regular port-channel/vPC parents (trunk, dot1q) through the same main() and reads the request the
module itself sends, so the PVLAN rule is compared with the module's own regular behaviour, not with a description of it.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from . import gie_withdrawal_harness as G
from . import test_dcnm_intf_pvlan_vpc_harness as V
from .test_dcnm_intf_pvlan_harness import IF7, PVLAN, SWITCH_IP, FakeController, measured_preview, pvlan_nv, preview
from .test_dcnm_intf_pvlan_harness import run as eth_run
from .test_dcnm_intf_pvlan_po_g1 import baseline, created, item, po_stanza, member_stanza
from .test_dcnm_intf_pvlan_po_host import PO, PO_HOST, PO_ITEM_NAME, PO_MEMBER, RUNNING_MEMBER
from .test_dcnm_intf_pvlan_harness import run

FF_A = "logging event port link-status"
FF_B = "no snmp trap link-status"
HOST_LINES = ["switchport private-vlan host-association 2210 2212"]
ASSOC = [{"primary_vlan": 2210, "secondary_vlan": 2212}]


# ====================================================================================== reference: the module's regular rule
def _request(calls):
    found = []
    G._collect_policies([c["payload"] for c in G.writes(calls)], found)
    return found


def _regular(parent, state, have_extra, want_extra):
    """(written, nvPairs) of one regular parent run: HAVE built by the module from `have_extra`, WANT = base + `want_extra`."""
    have = G.build_have(parent, **have_extra) if have_extra is not None else None
    want = G.base_for(parent, **want_extra)
    for key in [k for k, v in want.items() if v is G._UNSET]:
        want.pop(key)
    result, calls = G.run(want, state, have=have, parent=parent)
    assert not result.get("failed"), result.get("msg")
    found = _request(calls)
    return bool(G.split_calls(calls)["updates"]), (found[0]["interfaces"][0]["nvPairs"] if found else None)


OMIT = G._UNSET


@pytest.mark.parametrize("parent", [G.PC_TRUNK, G.PC_DOT1Q])
def test_reference_regular_port_channel_speed_and_cmds_rule(parent):
    """The regular rule PVLAN reuses: create carries SPEED/CONF; merged keeps an omitted field; replaced returns it to Auto / ''."""
    written, nv = _regular(parent, "merged", None, {"speed": "10Gb", "cmds": [FF_A]})
    assert written and nv["SPEED"] == "10Gb" and nv["CONF"] == FF_A
    # merged, both omitted: nothing to change
    written, nv = _regular(parent, "merged", {"speed": "10Gb", "cmds": [FF_A]}, {})
    assert not written
    # replaced, both omitted: SPEED back to Auto, CONF cleared
    written, nv = _regular(parent, "replaced", {"speed": "10Gb", "cmds": [FF_A]}, {})
    assert written and nv["SPEED"].lower() == "auto" and nv["CONF"] == ""
    # merged with a new command: HAVE's command kept, the new one added
    written, nv = _regular(parent, "merged", {"cmds": [FF_A]}, {"cmds": [FF_B]})
    assert written and sorted(nv["CONF"].split("\n")) == sorted([FF_A, FF_B])
    # replaced with an explicit list: exactly that list
    written, nv = _regular(parent, "replaced", {"cmds": [FF_A]}, {"cmds": [FF_B]})
    assert written and nv["CONF"] == FF_B


def test_reference_regular_merged_repeats_a_command_already_held_while_pvlan_does_not():
    """The ONE documented difference: the regular merged rule concatenates HAVE and WANT (dcnm_intf_merge_want_and_have), so a
    request that repeats a held command next to a new one sends it twice; the PVLAN rule (the Ethernet `cmds` precedent) appends only
    what HAVE does not hold."""
    written, nv = _regular(G.PC_DOT1Q, "merged", {"cmds": [FF_A]}, {"cmds": [FF_A, FF_B]})
    assert written and nv["CONF"].split("\n").count(FF_A) == 2
    assert P.freeform_merged(FF_A, [FF_A, FF_B]).split("\n") == [FF_A, FF_B]


def test_reference_regular_vpc_peer_cmds_follow_the_controller_peer():
    """Regular vPC (dot1q): peerN_cmds of the playbook land on the controller's peer that owns the switch (reversed order)."""
    result, calls = G.run_configs([dict(G.cfg_for(G.VPC_DOT1Q, G.base_for(G.VPC_DOT1Q, peer1_cmds=[FF_A], peer2_cmds=[FF_B])),
                                        switch=[G.SWITCH_IP, G.PEER_IP])], "merged")
    assert not result.get("failed"), result.get("msg")
    nv = _request(calls)[0]["interfaces"][0]["nvPairs"]
    assert (nv["PEER1_PO_CONF"], nv["PEER2_PO_CONF"]) == (FF_B, FF_A)


# ====================================================================================== PVLAN rule (helper), same table as the reference
def _po_have(**extra):
    raw = {"pvlan_mode": "host", "members": [IF7], "pvlan_association": ASSOC}
    raw.update(extra)
    return P.po_host_nvpairs(raw, PO)


def _po_want(**extra):
    raw = {"pvlan_mode": "host", "members": [IF7], "pvlan_association": ASSOC}
    raw.update(extra)
    return raw


@pytest.mark.parametrize(
    "state, have, want, written, speed, conf",
    [
        ("merged", {}, {"speed": "10Gb", "cmds": [FF_A]}, True, "10Gb", [FF_A]),
        ("merged", {"speed": "10Gb", "cmds": [FF_A]}, {}, False, "10Gb", [FF_A]),
        ("replaced", {"speed": "10Gb", "cmds": [FF_A]}, {}, True, "Auto", []),
        ("replaced", {"speed": "10Gb", "cmds": [FF_A]}, {"cmds": []}, True, "Auto", []),
        ("merged", {"cmds": [FF_A]}, {"cmds": [FF_B]}, True, "Auto", [FF_A, FF_B]),
        ("merged", {"cmds": [FF_A]}, {"cmds": []}, False, "Auto", [FF_A]),
        ("merged", {"cmds": [FF_A, FF_B]}, {"cmds": [FF_B, FF_A]}, False, "Auto", [FF_A, FF_B]),
        ("replaced", {"cmds": [FF_A]}, {"cmds": [FF_B]}, True, "Auto", [FF_B]),
        ("replaced", {"cmds": [FF_A, FF_B]}, {"cmds": [FF_B, FF_A]}, False, "Auto", [FF_A, FF_B]),
        ("replaced", {"speed": "10Gb"}, {"speed": "1Gb"}, True, "1Gb", []),
    ],
)
def test_port_channel_rule_matches_the_regular_one(state, have, want, written, speed, conf):
    out = P.reconcile_po(state, _po_want(**want), PO, PO_HOST, _po_have(**have))
    assert out["blocked"] == [], out["blocked"]
    assert out["update"] is written
    assert out["nv"]["SPEED"] == speed and sorted(P.freeform_lines(out["nv"]["CONF"])) == sorted(conf)
    if written:
        assert set(out["changed"]) <= {"SPEED", "CONF"}, out["changed"]


def _vpc_legs(raw):
    return P.vpc_pair_view(raw, V.PAIR, [V.SN1, V.SN2])


def _vpc_raw(**extra):
    raw = {"pvlan_mode": "host", "peer1_members": [V.M1], "peer2_members": [V.M2], "peer1_pcid": 10, "peer2_pcid": 10,
           "pvlan_association": [{"primary_vlan": V.PRIMARY, "secondary_vlan": V.SECONDARY}]}
    raw.update(extra)
    return raw


def test_vpc_per_peer_cmds_follow_the_controller_peer_and_speed_is_shared():
    raw = _vpc_raw(peer1_cmds=[FF_A], peer2_cmds=[FF_B], speed="10Gb")
    # playbook switch[0] is the controller's SECOND serial: peer1_cmds belong to PEER2
    legs = P.vpc_pair_view(raw, V.PAIR, [V.SN2, V.SN1])
    nv = P.vpc_host_nvpairs(raw, "vPC10", legs)
    assert (nv["PEER1_PO_CONF"], nv["PEER2_PO_CONF"]) == (FF_B, FF_A) and nv["SPEED"] == "10Gb"
    for index, conf in ((0, FF_B), (1, FF_A)):
        child = P.vpc_leg_po_nv(nv, index, "vPC10")
        assert child["CONF"] == conf and child["SPEED"] == "10Gb"
        assert {"speed 10000", conf} <= P.render(P.VPC_PO_POLICY, child).scalars


@pytest.mark.parametrize(
    "state, have, want, written, conf1, conf2",
    [
        ("merged", {"peer1_cmds": [FF_A], "peer2_cmds": [FF_A]}, {}, False, [FF_A], [FF_A]),
        ("merged", {"peer1_cmds": [FF_A], "peer2_cmds": [FF_A]}, {"peer1_cmds": [FF_B], "peer2_cmds": [FF_B]}, True, [FF_A, FF_B],
         [FF_A, FF_B]),
        ("replaced", {"peer1_cmds": [FF_A], "peer2_cmds": [FF_B]}, {}, True, [], []),
        ("replaced", {"peer1_cmds": [FF_A], "peer2_cmds": [FF_B]}, {"peer1_cmds": [FF_B], "peer2_cmds": [FF_A]}, True, [FF_B], [FF_A]),
        ("replaced", {"peer1_cmds": [FF_A], "peer2_cmds": [FF_B]}, {"peer1_cmds": [FF_A], "peer2_cmds": [FF_B]}, False, [FF_A], [FF_B]),
    ],
)
def test_vpc_freeform_rule_matches_the_regular_one(state, have, want, written, conf1, conf2):
    have_nv = P.vpc_host_nvpairs(_vpc_raw(**have), "vPC10", _vpc_legs(_vpc_raw(**have)))
    out = P.reconcile_vpc(state, _vpc_raw(**want), "vPC10", _vpc_legs(_vpc_raw(**want)), P.VPC_HOST_POLICY, have_nv)
    assert out["blocked"] == [], out["blocked"]
    assert out["update"] is written
    assert P.freeform_lines(out["nv"]["PEER1_PO_CONF"]) == conf1 and P.freeform_lines(out["nv"]["PEER2_PO_CONF"]) == conf2


def test_vpc_one_peer_freeform_change_stays_a_refused_unilateral_update():
    """RB2 contract kept: an update that reaches one peer only is refused unless it is membership (MM-B). A per-peer freeform change
    is a per-peer key, exactly like a per-peer description."""
    have_nv = P.vpc_host_nvpairs(_vpc_raw(), "vPC10", _vpc_legs(_vpc_raw()))
    out = P.reconcile_vpc("merged", _vpc_raw(peer1_cmds=[FF_A]), "vPC10", _vpc_legs(_vpc_raw(peer1_cmds=[FF_A])), P.VPC_HOST_POLICY, have_nv)
    assert out["update"] is False and any("changes only peer 1" in b and "PEER1_PO_CONF" in b for b in out["blocked"]), out["blocked"]


# ====================================================================================== refusals before any request
@pytest.mark.parametrize(
    "cmds, needle",
    [
        (["switchport mode trunk"], "copies to every member"),
        (["mtu 1500"], "copies to every member"),
        (["speed 1000"], "copies to every member"),
        (["no negotiate auto"], "copies to every member"),
        (["load-interval counter 1 30"], "copies to every member"),
        (["storm-control broadcast level 5.00"], "copies to every member"),
        (["cts manual"], "copies to every member"),
        (["channel-group 10 mode active"], "'channel-group' command"),
        (["vpc 10"], "'vpc' command"),
        (["no shutdown"], "'shutdown' command"),
        (["description x"], "'description' command"),
        (["no lacp suspend-individual"], "'lacp' command"),
        (["service-policy type queuing output Q"], "'service-policy' command"),
        (["ip port access-group A in"], "'ip port access-group' command"),
        (["interface Ethernet1/9"], "'interface' command"),
        (["  sgt 10"], "indented sub-command"),
        # PO-VPC text parity: a list entry holding a line break is checked line by line (each line must pass); a text is accepted the
        # same way, so these used to be "one command" / "list of strings" refusals and are now the per-line ones below.
        (["logging event port link-status\n  sgt 10"], "indented sub-command"),
        ("logging event port link-status\r\nswitchport mode trunk", "copies to every member"),
        ("no ip redirects, x", "must not contain a comma"),
        (5, "list of strings"),
        ([""], "is empty"),
    ],
)
def test_freeform_rule_refuses_before_any_request(cmds, needle):
    errors = P.po_freeform_errors("cmds", cmds)
    assert any(needle in e for e in errors), errors
    assert P.po_not_implemented({"pvlan_mode": "host", "cmds": cmds}) and P.vpc_not_implemented(
        {"pvlan_mode": "host", "peer1_pcid": 10, "peer2_pcid": 10, "peer1_cmds": cmds}, "vPC10")


def test_accepted_freeform_and_known_speeds():
    assert P.po_freeform_errors("cmds", [FF_A, FF_B, "no ip redirects"]) == []
    for value, keyword in P.SPEED_CLI.items():
        assert P.render(PO_HOST, _po_have(speed=value)).scalars >= {"speed %s" % keyword}
    assert P.SPEED_CLI_MEASURED == frozenset(("1Gb",)) and P.SPEED_CLI["1Gb"] == "1000"
    assert P.native_companion_errors({"speed": "7Gb"}, P.PO_NATIVE_COMPANIONS) == ["speed must be one of: %s" % ", ".join(P.SPEED_VALUES)]


def test_po_refusal_reaches_main_before_any_request():
    ctrl = created("host", HOST_LINES, pvlan_association=ASSOC)
    status, result = run(ctrl, [{"name": PO_ITEM_NAME, "type": "pc", "switch": [SWITCH_IP], "deploy": True,
                                 "profile": {"mode": "pvlan", "pvlan_mode": "host", "cmds": ["mtu 1500"]}}], state="merged")
    assert status == "fail" and "copies to every member" in result["msg"] and ctrl.writes() == []


def test_a_stored_freeform_outside_the_rule_is_refused_not_rewritten():
    have = _po_have()
    have["CONF"] = "cts manual\n  sgt 10"
    out = P.reconcile_po("merged", _po_want(description="x"), PO, PO_HOST, have)
    assert not P.render(PO_HOST, out["nv"]).modeled  # the destination is unmodeled: refused before any write
    vhave = P.vpc_host_nvpairs(_vpc_raw(), "vPC10", _vpc_legs(_vpc_raw()))
    vhave["PEER2_PO_CONF"] = "  sgt 10"
    vout = P.reconcile_vpc("merged", _vpc_raw(), "vPC10", _vpc_legs(_vpc_raw()), P.VPC_HOST_POLICY, vhave)
    assert any("PEER2_PO_CONF" in b and "indented" in b for b in vout["blocked"]), vout["blocked"]


# ====================================================================================== the capability line
def _entry(running, expected):
    return {"runningConfig": ["!Command: show running-config"] + running, "expectedConfig": expected}


def test_the_capability_line_is_adopted_only_next_to_a_speed_line():
    voc = P.transition_vocabulary((PO_HOST, _po_have(admin_state=False)), (PO_HOST, _po_have(speed="10Gb", admin_state=False)))
    want = P.render(PO_HOST, _po_have(speed="10Gb", admin_state=False))
    stanza = po_stanza("host", HOST_LINES)
    with_speed = stanza + ["  speed 10000", "  no negotiate auto"]
    decision, problems = P.assess_target(["speed 10000", "no negotiate auto"], _entry(stanza, with_speed), "port-channel10", want, voc)
    assert decision == "deploy", problems
    # the controller without the line (capability "on"/"both") is the plain speed model
    decision, problems = P.assess_target(["speed 10000"], _entry(stanza, stanza + ["  speed 10000"]), "port-channel10", want, voc)
    assert decision == "deploy", problems
    # without a speed line the same controller line is a disagreement
    auto = P.render(PO_HOST, _po_have(admin_state=False))
    decision, problems = P.assess_target(["no negotiate auto"], _entry(stanza, stanza + ["  no negotiate auto"]), "port-channel10", auto, voc)
    assert decision == "refuse" and "disagrees with the intended state" in problems[0]
    # nothing else is ever adopted
    decision, problems = P.assess_target(["speed 10000", "duplex full"], _entry(stanza, with_speed + ["  duplex full"]), "port-channel10",
                                         want, voc)
    assert decision == "refuse"


# ====================================================================================== port-channel through main()
def _po_cfg(**profile):
    prof = {"mode": "pvlan", "pvlan_mode": "host"}
    prof.update(profile)
    return {"name": PO_ITEM_NAME, "type": "pc", "switch": [SWITCH_IP], "deploy": True, "profile": prof}


def created_with(po_extra, member_extra, **profile):
    """An EXISTING host port-channel created through main() with RC1 fields: the po_g1 creation shape plus the extra Po / member lines
    (SYNTHETIC, template-predicted), then the member flip of po_g1.created()."""
    ctrl = baseline("host")
    po = po_stanza("host", HOST_LINES) + ["  " + x for x in po_extra]
    member = member_stanza("host", HOST_LINES) + ["  " + x for x in member_extra]
    pend = (["interface ethernet1/7", "  no spanning-tree port type edge trunk"] + po
            + ["interface ethernet1/7", "  channel-group 10 force mode active", "  shutdown"]
            + ["  " + x for x in member_extra] + ["configure terminal"])
    ctrl.previews = [preview(pend, running=RUNNING_MEMBER, expected=po + member)]
    status, result = run(ctrl, [item("host", pvlan_association=ASSOC, **profile)], state="replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    body = json.loads(ctrl.creates()[0][2])
    result["created_nv"] = (body[0] if isinstance(body, list) else body)["interfaces"][0]["nvPairs"]
    ctrl.detail[IF7] = {"policy": PO_MEMBER, "nvPairs": {
        "PO_ID": PO, "PC_MODE": "active", "PVLAN_MODE": "host", "CDP_ENABLE": "true", "lldpTransmit": "false", "lldpReceive": "false",
        "LACP_PORT_PRIO": "32768", "LACP_RATE": "normal", "DESC": "", "CONF": "", "ADMIN_STATE": "false", "INTF_NAME": IF7}}
    ctrl.next_invocation()
    ctrl.calls = []
    return ctrl, result


def test_po_creation_with_speed_and_freeform_payload_and_gate():
    _ctrl, result = created_with(["speed 10000", "no negotiate auto", FF_A], ["speed 10000", "no negotiate auto"], speed="10Gb", cmds=[FF_A])
    assert result["pvlan_gate"][0]["targets"][PO] == "deploy"
    nv = result["created_nv"]
    assert nv["SPEED"] == "10Gb" and nv["CONF"] == FF_A and nv["PVLAN_MODE"] == "host"


def _po_update_preview(old_po, new_po, old_member, new_member, pend):
    return preview(pend, running=old_po + old_member, expected=new_po + new_member)


def test_po_merged_speed_and_freeform_update_deploys_and_the_repeat_writes_nothing():
    ctrl = created("host", HOST_LINES, pvlan_association=ASSOC)
    have = copy.deepcopy(ctrl.detail[PO]["nvPairs"])
    old_po, old_m = po_stanza("host", HOST_LINES), member_stanza("host", HOST_LINES)
    new_po = old_po + ["  speed 10000", "  no negotiate auto", "  " + FF_A]
    new_m = old_m + ["  speed 10000", "  no negotiate auto"]
    pend = ["interface port-channel10", "  speed 10000", "  no negotiate auto", "  " + FF_A,
            "interface ethernet1/7", "  speed 10000", "  no negotiate auto"]
    ctrl.previews = [_po_update_preview(old_po, new_po, old_m, new_m, pend)]
    status, result = run(ctrl, [_po_cfg(speed="10Gb", cmds=[FF_A])], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    sent = ctrl.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]
    assert sent["SPEED"] == "10Gb" and sent["CONF"] == FF_A
    for key in ("ASSOCIATION_LIST", "MEMBER_INTERFACES", "ADMIN_STATE", "DESC", "MTU"):
        assert sent[key] == have[key], key
    assert result["diff"][0]["merged"][0]["interfaces"][0]["nvPairs"] == {"SPEED": "10Gb", "CONF": FF_A}
    assert result["pvlan_gate"][0]["targets"][PO] == "deploy" and len(ctrl.deploys()) == 1
    # the same request again: nothing to write or deploy
    ctrl.next_invocation()
    ctrl.calls = []
    status, result = run(ctrl, [_po_cfg(speed="10Gb", cmds=[FF_A])], state="merged")
    assert status == "exit" and result["changed"] is False, result
    assert ctrl.writes() == [] and ctrl.deploys() == []


def test_po_merged_omission_keeps_speed_and_freeform():
    ctrl, _r = created_with(["speed 10000", FF_A], ["speed 10000"], speed="10Gb", cmds=[FF_A])
    lines = HOST_LINES
    run_cfg = po_stanza("host", lines) + ["  speed 10000", "  " + FF_A] + member_stanza("host", lines) + ["  speed 10000"]
    exp = list(run_cfg)
    exp.insert(1, "  description D1")
    ctrl.previews = [preview(["interface port-channel10", "  description D1"], running=run_cfg, expected=exp)]
    status, result = run(ctrl, [_po_cfg(description="D1")], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    sent = ctrl.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]
    assert sent["SPEED"] == "10Gb" and sent["CONF"] == FF_A and sent["DESC"] == "D1"
    assert result["diff"][0]["merged"][0]["interfaces"][0]["nvPairs"] == {"DESC": "D1"}


def test_po_replaced_omission_withdraws_speed_and_freeform_and_the_pending_must_carry_it():
    base = dict(members=[IF7], admin_state=False)
    lines = HOST_LINES
    run_po = po_stanza("host", lines) + ["  speed 10000", "  " + FF_A]
    run_m = member_stanza("host", lines) + ["  speed 10000"]
    pend = ["interface port-channel10", "  no speed 10000", "  no " + FF_A, "interface ethernet1/7", "  no speed 10000"]
    ctrl, _r = created_with(["speed 10000", FF_A], ["speed 10000"], speed="10Gb", cmds=[FF_A])
    ctrl.previews = [preview(pend, running=run_po + run_m, expected=po_stanza("host", lines) + member_stanza("host", lines))]
    status, result = run(ctrl, [_po_cfg(pvlan_association=ASSOC, **base)], state="replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    sent = ctrl.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]
    assert sent["SPEED"] == "Auto" and sent["CONF"] == ""
    assert result["pvlan_gate"][0]["targets"][PO] == "deploy"
    # the same withdrawal with the freeform removal missing from the pending: refused before any deploy
    ctrl, _r = created_with(["speed 10000", FF_A], ["speed 10000"], speed="10Gb", cmds=[FF_A])
    short = [x for x in pend if FF_A not in x]
    ctrl.previews = [preview(short, running=run_po + run_m, expected=po_stanza("host", lines) + member_stanza("host", lines))]
    status, result = run(ctrl, [_po_cfg(pvlan_association=ASSOC, **base)], state="replaced")
    assert status == "fail" and "withdrawal of %r is absent from the pending" % FF_A in result["msg"] and ctrl.deploys() == []


def test_po_member_without_the_inherited_speed_in_its_pending_is_refused():
    """The member's speed arrives through the parent's 'Inherited Commands' child (HOST 517-518). Whether NX-OS then needs a member
    pending line is NOT measured; when the controller expects it but the pending does not carry it, the gate refuses (fail-closed)."""
    ctrl = created("host", HOST_LINES, pvlan_association=ASSOC)
    old_po, old_m = po_stanza("host", HOST_LINES), member_stanza("host", HOST_LINES)
    pend = ["interface port-channel10", "  speed 10000"]
    ctrl.previews = [_po_update_preview(old_po, old_po + ["  speed 10000"], old_m, old_m + ["  speed 10000"], pend)]
    status, result = run(ctrl, [_po_cfg(speed="10Gb")], state="merged")
    assert status == "fail" and "Ethernet1/7" in result["msg"] and ctrl.deploys() == []


# ====================================================================================== vPC through main()
def _vpc_speed_ff_preview(serial, port, conf):
    po = V.po_stanza() + ["  speed 10000", "  " + conf]
    member = V.member_after(port) + ["  speed 10000"]
    pend = ["interface port-channel10", "  speed 10000", "  " + conf, "interface %s" % port.lower(), "  speed 10000"]
    return preview(pend, serial=serial, running=V.po_stanza() + V.member_after(port), expected=po + member)


def test_vpc_merged_speed_and_both_peer_freeform_update_maps_each_peer_and_deploys():
    ctrl = V.created_ctrl()
    # the vPC preflight reads the CURRENT (converged) state first, then the gate reads the post-write preview
    ctrl.vpc_previews[V.SN1] = [V.converged_preview(V.SN1, V.M1), _vpc_speed_ff_preview(V.SN1, V.M1, FF_A)]
    ctrl.vpc_previews[V.SN2] = [V.converged_preview(V.SN2, V.M2), _vpc_speed_ff_preview(V.SN2, V.M2, FF_B)]
    status, result = V.run_vpc(ctrl, [V.vpc_item(speed="10Gb", peer1_cmds=[FF_A], peer2_cmds=[FF_B])], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    sent = [json.loads(c[2]) for c in ctrl.modifies()][0][0]["interfaces"][0]["nvPairs"]
    assert sent["SPEED"] == "10Gb" and (sent["PEER1_PO_CONF"], sent["PEER2_PO_CONF"]) == (FF_A, FF_B)
    assert ctrl.deploys()
    # the repeat: nothing to write
    ctrl.next_invocation()
    ctrl.vpc_previews[V.SN1] = [V.preview([], serial=V.SN1, running=V.po_stanza() + ["  speed 10000", "  " + FF_A] + V.member_after(V.M1)
                                          + ["  speed 10000"], expected=V.po_stanza() + ["  speed 10000", "  " + FF_A]
                                          + V.member_after(V.M1) + ["  speed 10000"])]
    ctrl.vpc_previews[V.SN2] = [V.preview([], serial=V.SN2, running=V.po_stanza() + ["  speed 10000", "  " + FF_B] + V.member_after(V.M2)
                                          + ["  speed 10000"], expected=V.po_stanza() + ["  speed 10000", "  " + FF_B]
                                          + V.member_after(V.M2) + ["  speed 10000"])]
    before = len(ctrl.writes())
    status, result = V.run_vpc(ctrl, [V.vpc_item(speed="10Gb", peer1_cmds=[FF_A], peer2_cmds=[FF_B])], state="merged")
    assert status == "exit" and result["changed"] is False, result
    assert len(ctrl.writes()) == before


def test_vpc_refusal_reaches_main_before_any_request():
    ctrl = V.created_ctrl()
    status, result = V.run_vpc(ctrl, [V.vpc_item(peer1_cmds=["vpc orphan-port suspend"], peer2_cmds=[FF_B])], state="merged")
    assert status == "fail" and "'vpc' command" in result["msg"] and ctrl.writes() == []


# ====================================================================================== Ethernet through main()
def test_ethernet_speed_update_deploys_with_the_adopted_capability_line():
    """int_pvlan_host already carried `speed` in its payload; RC1 models the line, so a non-Auto speed is no longer refused as
    unmodeled. The device stanza is the MEASURED converged G6-M0b one; the speed lines are SYNTHETIC (template 354-361)."""
    base = measured_preview("G6-M0b", "post")
    entry = copy.deepcopy(base["DATA"][0])
    idx = next(i for i, x in enumerate(entry["expectedConfig"]) if x.strip().lower() == "interface ethernet1/7")
    entry["expectedConfig"][idx + 1:idx + 1] = ["  speed 10000", "  no negotiate auto"]
    entry["pendingConfig"] = ["interface ethernet1/7", "  speed 10000", "  no negotiate auto"]
    entry["status"] = "Out-of-Sync"
    ctrl = FakeController()
    ctrl.detail[IF7] = {"policy": PVLAN, "nvPairs": pvlan_nv("G6-M0b")}
    ctrl.previews = [{"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [entry]}]
    status, result = eth_run(ctrl, [{"name": IF7, "type": "eth", "switch": [SWITCH_IP], "deploy": True,
                                     "profile": {"mode": "pvlan", "pvlan_mode": "trunk promiscuous", "speed": "10Gb"}}])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.requests("POST", "/rest/globalInterface/deploy")
