"""C1-R2 (Alpha, PR725-PVLAN-COMPANIONS-001): the two pre-deploy refusals MEASURED live in T2-LIVE-G1 (NDFC 12.6.0.267, FAB1 Leaf-102,
port-channel501 host 2210/2212 with member Ethernet1/8, 2026-10-09), replayed offline through the real main().

MEASURED inputs (fixtures/pvlan_po_t2_measured.json, from the redacted natural logs of the T2 run, previews reduced to the two target
stanzas, serial/fabric sanitized): the intents after the P1 creation, the module's own recompute preview of the S1 companion update,
the intents after S1 (never deployed), the member exactly as the controller released it after the R1 mark-delete, the G4 modify body,
and the module's own delete_deploy preview.

What is NOT measured (and therefore not asserted): the DEVICE effect of either pending. S1 and R1 were refused by the C1-R1 gates, so
no deploy was sent. Whether NX-OS makes the member follow the port-channel MTU, and what a re-issued `channel-group N force mode M` does
on an existing member, are open; the corrected gate does not assume either.

DERIVED inputs (marked as such in each test): a variant of the measured S1 preview that edits ONLY the MTU lines (the port-channel keeps
`mtu 9216`), so that the force re-assertion can be exercised without the open MTU question, and minimal edits of the measured previews
for the safety negatives. They are predictions built from a measurement, never live evidence.

SIMULATED, as in the existing G4 tests: the controller's answer to the legacy modifies (207 SUCCESS, sent nvPairs stored).
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import os

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_ENABLED_PATCH_VERSIONS

from .test_dcnm_intf_pvlan_harness import SWITCH_IP, TRUNK, preview, run
from .test_dcnm_intf_pvlan_po_g1 import PoLifecycleController, markdelete_ok

FIXTURE = json.load(open(os.path.join(os.path.dirname(__file__), "fixtures", "pvlan_po_t2_measured.json")))
PO, MEM = "Port-channel501", "Ethernet1/8"
PO_MEMBER = "int_port_channel_pvlan_member"
MARKDELETE = "/rest/interface/markdelete"
MODIFY = "/rest/interface/modify"
DEPLOY = "/rest/globalInterface/deploy"
SMU = sorted(GIE_ENABLED_PATCH_VERSIONS)[0]


def stage(name):
    return copy.deepcopy(FIXTURE["stages"][name])


def harness_nv(nv):
    """Measured nvPairs for the harness: only POLICY_ID dropped (the harness numbers its own policies)."""
    return dict((k, v) for k, v in nv.items() if k != "POLICY_ID")


def intent(stage_name, name):
    found = [v for k, v in stage(stage_name)["intent"].items() if k.lower() == name.lower()]
    assert len(found) == 1, (stage_name, name)
    return found[0]


def entry(pf):
    return {
        "RETURN_CODE": 200,
        "MESSAGE": "OK",
        "DATA": [preview(pf["pendingConfig"], running=pf["runningConfig_stanzas"], expected=pf["expectedConfig_stanzas"])["DATA"][0]],
    }


def measured_preview(stage_name):
    return stage(stage_name)["preview"]


RELEASED = harness_nv(stage("R1-release")["released"][MEM]["nvPairs"])  # MEASURED: int_trunk_host, ADMIN "true", MTU "default"


class T2Controller(PoLifecycleController):
    """The existing Po harness (E2 PoController + G1 lifecycle) seeded with the MEASURED T2 intents. Its mark-delete removes the parent
    and leaves the member as the controller released it in T2 (`released_nv`, default: the measured R1 release)."""

    def __init__(self, stage_name):
        super(T2Controller, self).__init__()
        po, mem = intent(stage_name, PO), intent(stage_name, MEM)
        self.detail[PO] = {"policy": po["policy"], "nvPairs": harness_nv(po["nvPairs"])}
        self.po_names.add(PO)
        self.detail[MEM] = {"policy": mem["policy"], "nvPairs": harness_nv(mem["nvPairs"])}
        self.released_nv = copy.deepcopy(RELEASED)

    def __call__(self, mod, method, path, data=None):
        if method == "DELETE" and path.endswith(MARKDELETE):
            self.calls.append((method, path, data))
            self.detail.pop(PO, None)
            self.po_names.discard(PO)
            self.detail[MEM] = {"policy": TRUNK, "nvPairs": copy.deepcopy(self.released_nv)}
            return markdelete_ok(data)
        return super(T2Controller, self).__call__(mod, method, path, data)

    def kinds(self):
        out = []
        for m, p, _d in self.calls:
            if m == "DELETE" and p.endswith(MARKDELETE):
                out.append("markdelete")
            elif m == "POST" and p.endswith(MODIFY):
                out.append("modify")
            elif m == "POST" and p.endswith(DEPLOY):
                out.append("deploy")
        return out

    def modify_nv(self, ifname):
        bodies = [json.loads(c[2]) for c in self.calls if c[0] == "POST" and c[1].endswith(MODIFY)]
        found = [i["nvPairs"] for b in bodies for p in b for i in p["interfaces"] if i["ifName"].lower() == ifname.lower()]
        return found


def s1_config(**profile_changes):
    cfg = stage("S1-gate")["config"]
    for c in cfg:
        c["switch"] = [SWITCH_IP]
        for k, v in profile_changes.items():
            if v is None:
                c["profile"].pop(k, None)
            else:
                c["profile"][k] = v
    return cfg


def update(pf, config=None):
    ctrl = T2Controller("P1-post")
    ctrl.previews = [entry(pf)] * 3
    status, result = run(ctrl, config or s1_config(), state="merged", patch_version=SMU)
    return ctrl, status, result


# ------------------------------------------------------------------ S1: fidelity of the replay
def test_s1_replay_sends_the_measured_live_modify_payload():
    """The harness replay of S1 builds the same Po modify the live run sent (every writable nvPair, values and types)."""
    ctrl, _status, _result = update(measured_preview("S1-gate"))
    sent = ctrl.modify_nv(PO)
    assert len(sent) == 1
    live = harness_nv(stage("S1-gate")["modify_nvpairs"])
    keys = set(live) | set(sent[0])
    differ = dict((k, (live.get(k), sent[0].get(k))) for k in keys if live.get(k) != sent[0].get(k) and k not in ("SERIAL_NUMBER", "FABRIC_NAME"))
    assert differ == {}, differ


# ------------------------------------------------------------------ S1: the measured refusal, corrected for the modeled part only
def test_s1_measured_update_was_refused_by_c1r2_only_for_the_member_mtu_and_deploys_under_the_c1r3_m1_rule():
    """C1-R2 refused S1 ONLY for the member's `mtu 9216` withdrawal (the force re-assertion was modeled). C1-R3 accounts for that one
    withdrawal by inheritance from the port-channel's own `no mtu 9216` (M-G1 M1, measured in isolation). The COMBINED S1 update deploying
    here is a PREDICTION from two separate measurements (M2 force re-assertion, M1 MTU inheritance); only the live replay can confirm it."""
    ctrl, status, result = update(measured_preview("S1-gate"))
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.kinds() == ["modify", "deploy"]


def test_s1_measured_update_without_the_parent_mtu_withdrawal_is_still_refused():
    """DERIVED negative: the measured S1 preview minus the port-channel's `no mtu 9216` -> no inheritance, ordinary refusal."""
    pf = measured_preview("S1-gate")
    pf["pendingConfig"] = [l for l in pf["pendingConfig"] if l != "  no mtu 9216"]
    ctrl, status, result = update(pf)
    assert status == "fail" and "mtu 9216" in result["msg"], result.get("msg")
    assert "deploy" not in ctrl.kinds()


def derived_no_mtu_change(pf):
    """DERIVED from the measured S1 preview: the port-channel keeps MTU jumbo, so the Po withdrawal `no mtu 9216` disappears and both
    expected stanzas keep `mtu 9216` (the P1 measured form). Every other line is the measured one."""
    pf = copy.deepcopy(pf)
    pend = [l for l in pf["pendingConfig"] if l != "  no mtu 9216"]
    idx = pend.index("  switchport private-vlan host-association 2210 2212")
    pend.insert(idx + 1, "  mtu 9216")
    pf["pendingConfig"] = pend
    exp = []
    for l in pf["expectedConfig_stanzas"]:
        exp.append(l)
        if l.lower() in ("interface port-channel501", "interface ethernet1/8"):
            exp.append("  mtu 9216")
    pf["expectedConfig_stanzas"] = exp
    return pf


def test_derived_update_without_mtu_change_deploys_through_the_force_reassertion():
    ctrl, status, result = update(derived_no_mtu_change(measured_preview("S1-gate")), s1_config(mtu=None))
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.kinds() == ["modify", "deploy"]


def test_derived_update_without_mtu_change_was_refused_by_c1r1_only_for_the_force_line():
    """The same derived case names the force re-assertion as its ONLY refusal on C1-R1 (recorded by the fail-before run); here it
    documents that no other line of the measured member pending needs a rule."""
    _ctrl, status, result = update(derived_no_mtu_change(measured_preview("S1-gate")), s1_config(mtu=None))
    assert "withdrawal of" not in (result.get("msg") or "") and "unmodeled" not in (result.get("msg") or "")
    assert status == "exit"


def edit_member_pending(pf, old=None, new=None, add=None):
    pf = copy.deepcopy(pf)
    pend = pf["pendingConfig"]
    if old is not None:
        i = pend.index(old)
        if new is None:
            pend.pop(i)
        else:
            pend[i] = new
    if add:
        i = len(pend) - 1  # before the member block's closing `configure terminal`
        pend[i:i] = add
    return pf


FORCE = "  channel-group 501 force mode active"


@pytest.mark.parametrize(
    "case,edit,needle",
    [
        (
            "another port-channel number",
            dict(old=FORCE, new="  channel-group 502 force mode active"),
            "unmodeled command 'channel-group 502 force mode active'",
        ),
        ("another LACP mode", dict(old=FORCE, new="  channel-group 501 force mode passive"), "unmodeled command 'channel-group 501 force mode passive'"),
        ("the force twice", dict(add=[FORCE]), "carries 'channel-group 501 force mode active' 2 times"),
        ("a non-force channel-group", dict(old=FORCE, new="  channel-group 777 mode active"), "channel-group 777 mode active"),
        ("a foreign member command", dict(add=["  switchport trunk allowed vlan 10"]), "switchport trunk allowed vlan 10"),
        ("an admin-up command", dict(add=["  no shutdown"]), "no shutdown"),
    ],
)
def test_force_reassertion_safety_negatives_refuse_before_any_deploy(case, edit, needle):
    pf = edit_member_pending(derived_no_mtu_change(measured_preview("S1-gate")), **edit)
    ctrl, status, result = update(pf, s1_config(mtu=None))
    assert status == "fail" and needle in result["msg"], (case, result.get("msg"))
    assert "deploy" not in ctrl.kinds()


def edit_member_running(pf, drop=None, replace=None):
    pf = copy.deepcopy(pf)
    out, inside = [], False
    for l in pf["runningConfig_stanzas"]:
        if not l.startswith(" "):
            inside = l.lower() == "interface ethernet1/8"
        if inside and drop and l.strip() == drop:
            continue
        if inside and replace and l.strip() == replace[0]:
            l = "  " + replace[1]
        out.append(l)
    pf["runningConfig_stanzas"] = out
    return pf


def test_force_reassertion_is_refused_when_the_member_is_up_on_the_device():
    pf = edit_member_running(derived_no_mtu_change(measured_preview("S1-gate")), drop="shutdown")
    ctrl, status, result = update(pf, s1_config(mtu=None))
    assert status == "fail" and "not administratively down" in result["msg"], result.get("msg")
    assert "deploy" not in ctrl.kinds()


def test_force_reassertion_is_refused_when_the_device_member_belongs_to_another_port_channel():
    pf = edit_member_running(derived_no_mtu_change(measured_preview("S1-gate")), replace=("channel-group 501 mode active", "channel-group 502 mode active"))
    ctrl, status, result = update(pf, s1_config(mtu=None))
    assert status == "fail" and "would change its membership" in result["msg"], result.get("msg")
    assert "deploy" not in ctrl.kinds()


# ------------------------------------------------------------------ unit level: the re-assertion rule itself
def _model(scalars, kind="host"):
    return P.Model(set(scalars), kind, (), True)


def test_unit_reassertion_requires_the_same_membership_on_device_and_intent_and_admin_down():
    running = ["channel-group 501 mode active", "shutdown", "switchport", "switchport mode private-vlan host"]
    rule = {"po_number": "501", "pc_mode": "active"}
    body = ["channel-group 501 force mode active", "no cdp enable"]
    obs, des = _model(running), _model(running + ["no cdp enable"])
    rest, problems = P.po_member_force_reassertion(body, obs, des, rule)
    assert problems == [] and rest == ["no cdp enable"]
    # no rule given (creation path, other policies): the body is untouched
    assert P.po_member_force_reassertion(body, obs, des, None) == (body, [])
    # without the force line nothing is consumed
    assert P.po_member_force_reassertion(["no cdp enable"], obs, des, rule) == (["no cdp enable"], [])
    # intended membership differs
    _rest, problems = P.po_member_force_reassertion(body, obs, _model(["shutdown"]), rule)
    assert len(problems) == 1 and "intended member does not hold" in problems[0]
    # device member up
    _rest, problems = P.po_member_force_reassertion(body, _model([x for x in running if x != "shutdown"]), des, rule)
    assert len(problems) == 1 and "not administratively down" in problems[0]
    # mode change
    _rest, problems = P.po_member_force_reassertion(body, obs, _model(running, kind="promiscuous"), rule)
    assert len(problems) == 1 and "PVLAN mode changes" in problems[0]
    # the observed state is never altered by the rule (no assumed synchronisation)
    assert obs.scalars == set(running)


# ------------------------------------------------------------------ R1: the measured release, modeled from the fresh controller state
def delete(released=None, pf=None):
    ctrl = T2Controller("S1-post")
    if released is not None:
        ctrl.released_nv = released
    ctrl.previews = [entry(pf or measured_preview("R1-gate"))] * 3
    status, result = run(ctrl, [{"name": "po501", "switch": [SWITCH_IP], "deploy": True}], state="deleted")
    return ctrl, status, result


def test_r1_replay_sends_the_measured_live_release_modify():
    ctrl, _status, _result = delete()
    sent = ctrl.modify_nv(MEM)
    assert len(sent) == 1
    live = stage("R1-release")["modify_nvpairs"]
    differ = dict(
        (k, (live.get(k), sent[0].get(k))) for k in set(live) | set(sent[0]) if live.get(k) != sent[0].get(k) and k not in ("SERIAL_NUMBER", "FABRIC_NAME")
    )
    assert differ == {} and sent[0]["ADMIN_STATE"] == "false" and sent[0]["MTU"] == "default", differ


def test_r1_measured_delete_deploys_against_the_fresh_release_and_reports_the_restoration_delta():
    ctrl, status, result = delete()
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.kinds() == ["markdelete", "modify", "deploy"]
    record = [r for r in result["pvlan_po_release"] if r.get("member") == MEM][0]
    assert record["released_admin_state"] == "true"
    assert record["restoration_delta"] == {"MTU": {"released": "default", "release_model": "jumbo"}}, record
    assert ctrl.detail[MEM]["policy"] == TRUNK and ctrl.detail[MEM]["nvPairs"]["MTU"] == "default"


@pytest.mark.parametrize(
    "key,value,needle",
    [
        ("ALLOWED_VLANS", "all", "ALLOWED_VLANS"),
        ("ALLOWED_VLANS", "2210", "ALLOWED_VLANS"),
        ("NATIVE_VLAN", "2210", "NATIVE_VLAN"),
        ("CONF", "no cdp enable", "CONF"),
    ],
)
def test_r1_a_release_that_is_not_a_safe_standalone_port_stops_before_the_deploy(key, value, needle):
    released = dict(RELEASED, **{key: value})
    ctrl, status, result = delete(released=released)
    assert status == "fail" and needle in result["msg"] and "safe standalone" in result["msg"], result.get("msg")
    assert "deploy" not in ctrl.kinds()


def test_r1_the_controller_expected_member_must_still_equal_the_fresh_release():
    """DERIVED: the measured R1 preview with `mtu 9216` added to the expected member while the released intent says MTU default."""
    pf = measured_preview("R1-gate")
    exp = []
    for l in pf["expectedConfig_stanzas"]:
        exp.append(l)
        if l.lower() == "interface ethernet1/8":
            exp.append("  mtu 9216")
    pf["expectedConfig_stanzas"] = exp
    ctrl, status, result = delete(pf=pf)
    assert status == "fail" and "disagrees with the intended state" in result["msg"], result.get("msg")
    assert "deploy" not in ctrl.kinds()


def test_r1_the_member_mtu_withdrawal_must_be_in_the_pending():
    """DERIVED: the measured R1 preview without the member's `no mtu 9216`."""
    pf = measured_preview("R1-gate")
    pf["pendingConfig"] = [l for l in pf["pendingConfig"] if l != "  no mtu 9216"]
    ctrl, status, result = delete(pf=pf)
    assert status == "fail" and "withdrawal of 'mtu 9216' is absent from the pending" in result["msg"], result.get("msg")
    assert "deploy" not in ctrl.kinds()


def test_r1_a_release_whose_intent_equals_the_model_reports_no_restoration_delta():
    """DERIVED control: the measured release with MTU jumbo (the G5 case) and the measured preview with the member keeping `mtu 9216`."""
    pf = measured_preview("R1-gate")
    pf["pendingConfig"] = [l for l in pf["pendingConfig"] if l != "  no mtu 9216"]
    exp = []
    for l in pf["expectedConfig_stanzas"]:
        exp.append(l)
        if l.lower() == "interface ethernet1/8":
            exp.append("  mtu 9216")
    pf["expectedConfig_stanzas"] = exp
    ctrl, status, result = delete(released=dict(RELEASED, MTU="jumbo"), pf=pf)
    assert status == "exit", result.get("msg")
    record = [r for r in result["pvlan_po_release"] if r.get("member") == MEM][0]
    assert record["restoration_delta"] == {}
