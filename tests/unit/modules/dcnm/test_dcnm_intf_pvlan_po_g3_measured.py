"""PO G3 (Alpha, PR725-PVLAN-PO-PLAN-001): the member comparison against the MEASURED H1 capture.

MEASURED inputs (fixtures/pvlan_po_h1_measured.json, from Alpha4's live G2/R2 run on NDFC 12.6.0.267): the forced-preview
pending (complete) and the expected/running stanzas of port-channel502 and Ethernet1/10, their intents and policies. The
member pending held `channel-group 502 force mode active`; the controller's expected member held
`channel-group 502 mode active` plus the inherited PVLAN mode and host-association; G2 refused that expected line.
Every variation below CHANGES one measured line and says so; nothing is derived from the pending to fill the expected.

Gate tests call the real assess_target(); main() tests run the real module through the existing harness (only the
switch serial is the harness one). The G2 module fails the H1 replay (fail-before); the update/repetition/deletion forms
other than those measured stay limits (named in each test)."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import os

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .test_dcnm_intf_pvlan_harness import SWITCH_IP, TRUNK, preview, run
from .test_dcnm_intf_pvlan_po_g1 import PoLifecycleController, markdelete_ok

FIXTURE = json.load(open(os.path.join(os.path.dirname(__file__), "fixtures", "pvlan_po_h1_measured.json")))
STAGES = FIXTURE["stages"]
PO_NAME, MEM = "port-channel502", "Ethernet1/10"
PO = "Port-channel502"  # the module-normalised name
PO_MEMBER = "int_port_channel_pvlan_member"


def stage(name):
    return copy.deepcopy(STAGES[name])


def entry(name, pending=None, expected=None, running=None):
    """The measured forced-preview entry of a stage (Po + member stanzas), optionally with ONE named change."""
    pf = stage(name)["preview_forced"]
    resp = preview(
        pending if pending is not None else pf["pendingConfig"],
        running=running if running is not None else pf["runningConfig_stanzas"],
        expected=expected if expected is not None else pf["expectedConfig_stanzas"],
    )
    return resp["DATA"][0]


def blocks(e):
    return P.split_blocks(e["pendingConfig"])


def po_nv():
    return stage("H1-post")["intent"][PO_NAME]["nvPairs"]


def member_post_nv():
    """What the module models for the joining member: the measured parent + the measured trunk baseline (HOST:536-553)."""
    return P.po_member_nvpairs(po_nv(), stage("H1-pre")["intent"][MEM]["nvPairs"])


def member_pre():
    return (TRUNK, stage("H1-pre")["intent"][MEM]["nvPairs"])


FORCE = {"po_number": "502", "pc_mode": "active", "mode": "host"}


def assess_member(e, member_force="measured", post_nv=None):
    member_force = dict(FORCE) if member_force == "measured" else member_force
    post = (PO_MEMBER, post_nv or member_post_nv())
    body = blocks(e)[0].get(MEM.lower(), [])
    return P.assess_target(body, e, MEM, P.render(*post), P.transition_vocabulary(member_pre(), post), member_force=member_force)


def replace_line(lines, old, new):
    assert old in lines, old
    return [new if line == old else line for line in lines]


# ------------------------------------------------------------------ the measured H1 data itself
def test_fixture_is_the_gate_input_and_states_the_measured_member_forms():
    assert FIXTURE["h1_gate_pending_equals_h1_post"] is True, "the H1-post pending is the one the gate saw"
    pf = stage("H1-post")["preview_forced"]
    assert "  channel-group 502 force mode active" in pf["pendingConfig"]
    assert "  channel-group 502 mode active" in pf["expectedConfig_stanzas"]
    assert not [line for line in pf["expectedConfig_stanzas"] if "force" in line]
    inherited = [p for p in stage("H1-post")["policies"] if p["templateName"] == "int_eth"]
    assert inherited and inherited[0]["source"] == PO_NAME and "host-association 2210 2212" in inherited[0]["nvPairs"]["CONF"]


def test_measured_h1_member_is_accepted_by_the_g3_gate():
    decision, problems = assess_member(entry("H1-post"))
    assert (decision, problems) == ("deploy", [])


def test_measured_h1_parent_is_accepted_unchanged():
    e = entry("H1-post")
    post = (P.PO_HOST_POLICY, po_nv())
    decision, problems = P.assess_target(blocks(e)[0].get(PO_NAME, []), e, PO, P.render(*post), P.transition_vocabulary((None, None), post), absent_ok=True)
    assert (decision, problems) == ("deploy", [])


def test_without_the_force_transition_the_measured_member_is_still_refused():
    """The force line alone carries mode, list and the trunk withdrawal: without the measured transition the pending
    lacks them (this is the second half of the G2 gap, after the expected line)."""
    decision, problems = assess_member(entry("H1-post"), member_force=None)
    assert decision == "refuse" and any("absent from the pending" in p for p in problems)


# ------------------------------------------------------------------ identity, mode and foreign commands stay refused
@pytest.mark.parametrize(
    "where, old, new, needle",
    [
        ("pending", "  channel-group 502 force mode active", "  channel-group 503 force mode active", "unmodeled command"),
        ("pending", "  channel-group 502 force mode active", "  channel-group 502 force mode passive", "unmodeled command"),
        ("expected", "  channel-group 502 mode active", "  channel-group 503 mode active", "disagrees with the intended state"),
        ("expected", "  channel-group 502 mode active", "  channel-group 502 mode passive", "disagrees with the intended state"),
        ("expected", "  channel-group 502 mode active", "  channel-group 502 force mode active", "disagrees with the intended state"),
        ("expected", "  shutdown", "  no shutdown", "disagrees with the intended state"),
        (
            "expected",
            "  switchport private-vlan host-association 2210 2212",
            "  switchport private-vlan host-association 2210 2211",
            "disagrees with the intended state",
        ),
        ("expected", "  switchport mode private-vlan host", "  switchport mode private-vlan promiscuous", "disagrees with the intended state"),
        ("expected", "  mtu 9216", "  ip address 192.0.2.1/24", "outside the modeled contract"),
        ("pending", "  shutdown", "  no shutdown", "unexpected removal"),
    ],
)
def test_each_single_change_to_the_measured_member_is_refused(where, old, new, needle):
    pf = stage("H1-post")["preview_forced"]
    if where == "pending":
        e = entry("H1-post", pending=replace_line(pf["pendingConfig"], old, new))
    else:
        e = entry("H1-post", expected=replace_line(pf["expectedConfig_stanzas"], old, new))
    decision, problems = assess_member(e)
    assert decision == "refuse" and any(needle in p for p in problems), problems


def test_a_missing_inherited_line_in_the_expected_member_is_refused():
    pf = stage("H1-post")["preview_forced"]
    expected = [line for line in pf["expectedConfig_stanzas"] if line != "  switchport private-vlan host-association 2210 2212"]
    decision, problems = assess_member(entry("H1-post", expected=expected))
    assert decision == "refuse" and any("pair 2210/2212" in p for p in problems), problems


def test_a_foreign_line_in_the_member_pending_is_refused():
    pf = stage("H1-post")["preview_forced"]
    pending = list(pf["pendingConfig"])
    pending.insert(pending.index("  channel-group 502 force mode active"), "  ip address 192.0.2.1/24")
    decision, problems = assess_member(entry("H1-post", pending=pending))
    assert decision == "refuse" and any("unmodeled command" in p for p in problems), problems


def test_the_force_command_twice_is_refused():
    pf = stage("H1-post")["preview_forced"]
    pending = pf["pendingConfig"][:-1] + ["  channel-group 502 force mode active", "configure terminal"]
    decision, problems = assess_member(entry("H1-post", pending=pending))
    assert decision == "refuse" and any("2 times" in p for p in problems), problems


def test_the_force_transition_is_not_applied_to_another_mode_or_outside_the_pvlan_modes():
    # G5: the other PVLAN modes are modeled (inferred), so the measured host member under a promiscuous force is refused by
    # the mode check; a mode outside the four is refused as such.
    decision, problems = assess_member(entry("H1-post"), member_force=dict(FORCE, mode="promiscuous"))
    assert decision == "refuse" and any("is not the port-channel's 'promiscuous'" in p for p in problems), problems
    decision, problems = assess_member(entry("H1-post"), member_force=dict(FORCE, mode="isolated"))
    assert decision == "refuse" and any("is not one" in p for p in problems), problems


# ------------------------------------------------------------------ main(): creation, repetition, unmeasured modes, deletion
def item(mode="host", **profile):
    prof = {"mode": "pvlan", "pvlan_mode": mode, "members": [MEM], "admin_state": False, "pvlan_association": [{"primary_vlan": 2210, "secondary_vlan": 2212}]}
    prof.update(profile)
    return {"name": "po502", "type": "pc", "switch": [SWITCH_IP], "deploy": True, "profile": prof}


def harness_nv(nv):
    """Measured nvPairs for the harness: only POLICY_ID is dropped, because the harness numbers its own policies (its
    summary/policy list would otherwise disagree with the measured id, which the ownership check refuses)."""
    return dict((k, v) for k, v in nv.items() if k != "POLICY_ID")


def baseline():
    ctrl = PoLifecycleController()
    ctrl.detail[MEM] = {"policy": TRUNK, "nvPairs": harness_nv(stage("H1-pre")["intent"][MEM]["nvPairs"])}
    return ctrl


def test_main_h1_replay_creates_and_deploys_with_the_measured_preview():
    ctrl = baseline()
    ctrl.previews = [{"RETURN_CODE": 200, "DATA": [entry("H1-post")]}]
    status, result = run(ctrl, [item()], state="replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1
    assert result["pvlan_gate"][0]["targets"][PO] == "deploy"


def test_main_identical_repetition_after_the_creation_writes_nothing():
    ctrl = baseline()
    ctrl.previews = [{"RETURN_CODE": 200, "DATA": [entry("H1-post")]}]
    assert run(ctrl, [item()], state="replaced")[0] == "exit"
    ctrl.detail[MEM] = {"policy": PO_MEMBER, "nvPairs": harness_nv(stage("H1-post")["intent"][MEM]["nvPairs"])}
    ctrl.next_invocation()
    ctrl.calls = []
    status, result = run(ctrl, [item()], state="replaced")
    assert status == "exit" and result["changed"] is False, result
    assert ctrl.writes() == [] and ctrl.deploys() == []


@pytest.mark.parametrize(
    "mode, profile",
    [
        ("promiscuous", {"pvlan_mapping": [{"primary_vlan": 2210, "secondary_vlans": "2212"}], "pvlan_association": None}),
        (
            "trunk promiscuous",
            {"pvlan_mapping": [{"primary_vlan": 2210, "secondary_vlans": "2212"}], "pvlan_association": None, "native_vlan": "2301", "allowed_vlans": "2301"},
        ),
        ("trunk secondary", {"native_vlan": "2301", "allowed_vlans": "2301"}),
    ],
)
def test_main_creation_in_another_mode_against_the_measured_host_preview_is_refused_before_deploy(mode, profile):
    # G5: these modes are no longer refused before the write (inferred force form); the MEASURED H1 preview belongs to a
    # host port-channel, so the gate refuses it for any other mode and nothing is deployed.
    ctrl = baseline()
    it = item(mode, **profile)
    it["profile"] = dict((k, v) for k, v in it["profile"].items() if v is not None)
    ctrl.previews = [{"RETURN_CODE": 200, "DATA": [entry("H1-post")]}]
    status, result = run(ctrl, [it], state="replaced")
    if mode == "trunk secondary":
        # G6: the measured trunk member (int_trunk_host) cannot join a trunk secondary port-channel (TS1/EXP-1 known incident):
        # refused before any write.
        assert status == "fail" and "Known incident pending engineering" in result["msg"], result.get("msg")
        assert ctrl.writes() == []
        return
    assert status == "fail" and "disagrees with the intended state" in result["msg"], result.get("msg")
    assert len(ctrl.creates()) == 1 and ctrl.deploys() == []


def test_main_g2_style_expected_with_force_is_now_refused():
    """The G1/G2 synthetic prediction (expected member WITH force) is not what the controller holds: refused."""
    ctrl = baseline()
    pf = stage("H1-post")["preview_forced"]
    expected = replace_line(pf["expectedConfig_stanzas"], "  channel-group 502 mode active", "  channel-group 502 force mode active")
    ctrl.previews = [{"RETURN_CODE": 200, "DATA": [entry("H1-post", expected=expected)]}]
    status, result = run(ctrl, [item()], state="replaced")
    assert status == "fail" and ctrl.deploys() == []


def test_main_measured_hr_release_with_the_measured_admin_up_preview_is_refused_before_deploy():
    """HR-post as MEASURED: after the mark-delete the member is int_trunk_host ADMIN_STATE true and the preview carries
    `no shutdown`. G4 corrects the member's ADMIN_STATE first (test_dcnm_intf_pvlan_po_g4_release.py covers that path);
    with that same admin-up preview still served, the gate refuses and nothing is deployed.

    G4 correction of THIS test: its G3 version answered the mark-delete with {"RETURN_CODE": 200, "DATA": {}} (no
    MESSAGE "OK"), which the module treats as a failed delete and retried 20 times; it passed without ever reaching the
    release. The mark-delete now answers like the controller (200, MESSAGE OK)."""
    ctrl = PoLifecycleController()
    ctrl.detail[PO] = {"policy": P.PO_HOST_POLICY, "nvPairs": harness_nv(stage("H1-post")["intent"][PO_NAME]["nvPairs"])}
    ctrl.po_names.add(PO)
    ctrl.detail[MEM] = {"policy": PO_MEMBER, "nvPairs": harness_nv(stage("H1-post")["intent"][MEM]["nvPairs"])}
    ctrl.release_member = False
    hr = stage("HR-post")

    def markdelete_then_measured_release(mod, method, path, data=None):
        if method == "DELETE" and path.endswith("/rest/interface/markdelete"):
            ctrl.calls.append((method, path, data))
            ctrl.detail.pop(PO, None)
            ctrl.po_names.discard(PO)
            ctrl.detail[MEM] = {"policy": TRUNK, "nvPairs": harness_nv(hr["intent"][MEM]["nvPairs"])}
            return markdelete_ok(data)
        return PoLifecycleController.__call__(ctrl, mod, method, path, data)

    ctrl.previews = [{"RETURN_CODE": 200, "DATA": [entry("HR-post")]}]
    status, result = run(markdelete_then_measured_release, [{"name": "po502", "switch": [SWITCH_IP], "deploy": True}], state="deleted")
    assert status == "fail" and "'no shutdown'" in result["msg"]
    assert len([c for c in ctrl.calls if c[0] == "DELETE"]) == 1, "one mark-delete, never retried"
    assert ctrl.deploys() == [] and str(ctrl.detail[MEM]["nvPairs"]["ADMIN_STATE"]).lower() == "false"
