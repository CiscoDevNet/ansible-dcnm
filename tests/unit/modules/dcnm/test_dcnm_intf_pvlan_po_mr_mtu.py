"""The member MTU ADDITION inherited from the port-channel (default -> jumbo), as MEASURED.

MEASURED inputs (fixtures/pvlan_po_mr_measured.json, provenance per field inside it): the GUI preview pending (the port-channel
stanza re-emitted with `mtu 9216`, no member block, no force), intents before/after, the controller's runningConfig before and
expectedConfig after, device stanzas and operational MTU (1500 -> 9216 on BOTH port-channel and member), and one module recompute
preview with its modify body.
The module request reproducing the GUI change is `merged` with `mtu: jumbo` (the GUI payload is not known and not invented). Real
main() on the existing harness; only the controller boundary is simulated. DERIVED inputs are marked; they are predictions. vPC is
not covered here.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import os

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_ENABLED_PATCH_VERSIONS

from .test_dcnm_intf_pvlan_harness import SWITCH_IP, preview, run
from .test_dcnm_intf_pvlan_po_g1 import PoLifecycleController

FX = json.load(open(os.path.join(os.path.dirname(__file__), "fixtures", "pvlan_po_mr_measured.json")))
PO, MEM = "Port-channel501", "Ethernet1/8"
MODIFY = "/rest/interface/modify"
DEPLOY = "/rest/globalInterface/deploy"
SMU = sorted(GIE_ENABLED_PATCH_VERSIONS)[0]
PEND = list(FX["operator_preview_pending"])
RUN_PRE = list(FX["pre"]["preview_running_stanzas"])
EXP_POST = list(FX["post"]["preview_expected_stanzas"])


def harness_nv(nv):
    return dict((k, v) for k, v in nv.items() if k != "POLICY_ID")


class MRController(PoLifecycleController):
    def __init__(self, intent):
        super(MRController, self).__init__()
        po = [v for k, v in intent.items() if k.lower() == "port-channel501"][0]
        mem = [v for k, v in intent.items() if k.lower() == "ethernet1/8"][0]
        self.detail[PO] = {"policy": po["policy"], "nvPairs": harness_nv(po["nvPairs"])}
        self.po_names.add(PO)
        self.detail[MEM] = {"policy": mem["policy"], "nvPairs": harness_nv(mem["nvPairs"])}

    def kinds(self):
        return [
            "modify" if p.endswith(MODIFY) else "deploy" if p.endswith(DEPLOY) else p
            for m, p, _d in self.calls
            if m in ("POST", "PUT", "DELETE") and "/config-preview" not in p and "bulk-update" not in p
        ]

    def modify_nv(self, ifname):
        return [
            i["nvPairs"]
            for c in self.calls
            if c[0] == "POST" and c[1].endswith(MODIFY)
            for p in json.loads(c[2])
            for i in p["interfaces"]
            if i["ifName"].lower() == ifname.lower()
        ]


def entry(pending, running, expected):
    return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [preview(pending, running=running, expected=expected)["DATA"][0]]}


def mr(pending=None, running=None, expected=None):
    ctrl = MRController(FX["pre"]["intent"])
    ctrl.previews = [entry(PEND if pending is None else pending, RUN_PRE if running is None else running, EXP_POST if expected is None else expected)] * 3
    item = {
        "name": "po501",
        "type": "pc",
        "switch": [SWITCH_IP],
        "deploy": True,
        "profile": {"mode": "pvlan", "pvlan_mode": "host", "members": [MEM], "mtu": "jumbo"},
    }
    status, result = run(ctrl, [item], state="merged", patch_version=SMU)
    return ctrl, status, result


def edit(lines, iface, drop=None, replace=None, add=None):
    out, inside = [], False
    for line in lines:
        if not line.startswith(" "):
            inside = line.strip().lower() == "interface " + iface
        if inside and drop is not None and line.strip() == drop:
            continue
        if inside and replace is not None and line.strip() == replace[0]:
            line = "  " + replace[1]
        out.append(line)
        if inside and add is not None and not line.startswith(" "):
            out.append("  " + add)
    return out


BOOK = P.PO_RELEASE_METADATA | {"SERIAL_NUMBER", "FABRIC_NAME"}


# ------------------------------------------------------------------ the measured form
def test_measured_mr_request_reproduces_the_post_intent_of_the_port_channel():
    ctrl, _status, _result = mr()
    sent = ctrl.modify_nv(PO)
    assert len(sent) == 1
    post = harness_nv([v for k, v in FX["post"]["intent"].items() if k.lower() == "port-channel501"][0]["nvPairs"])
    differ = dict((k, (post.get(k), sent[0].get(k))) for k in set(post) | set(sent[0]) if k not in BOOK and str(post.get(k)) != str(sent[0].get(k)))
    assert differ == {}, differ


def test_measured_mr_parent_only_addition_deploys_through_the_inherited_member_mtu():
    ctrl, status, result = mr()
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.kinds() == ["modify", "deploy"]


def test_measured_mr_device_effect_is_recorded_in_the_fixture():
    assert not [l for l in FX["pre"]["running_stanzas"] if l.strip().startswith("mtu")]
    assert [l.strip() for l in FX["post"]["running_stanzas"] if l.strip().startswith("mtu")] == ["mtu 9216", "mtu 9216"]
    assert all(v.startswith("MTU 1500 ") for v in FX["pre"]["operational_mtu"].values())
    assert all(v.startswith("MTU 9216 ") for v in FX["post"]["operational_mtu"].values())
    assert FX["post"]["preview"] == {"status": "In-Sync", "pendingConfig": []}


# ------------------------------------------------------------------ targeted negatives (each refuses, no deploy)
NO_PARENT_CMD = [l for l in PEND if l.strip() != "mtu 9216"]
OTHER_MTU = [("  mtu 9000" if l.strip() == "mtu 9216" else l) for l in PEND]
PARENT_INVALID = PEND[:-1] + ["  switchport trunk allowed vlan 10", "configure terminal"]


@pytest.mark.parametrize(
    "case,kw,needle",
    [
        ("parent transition not validated", dict(pending=PARENT_INVALID), "switchport trunk allowed vlan 10"),
        ("no parent mtu command", dict(pending=NO_PARENT_CMD), "mtu 9216"),
        ("parent adds another MTU", dict(pending=OTHER_MTU), "mtu 9000"),
        ("member device MTU divergent", dict(running=edit(RUN_PRE, "ethernet1/8", add="mtu 9000")), "mtu"),
        (
            "conflicting expected member MTU",
            dict(expected=edit(EXP_POST, "ethernet1/8", replace=("mtu 9216", "mtu 1500"))),
            "disagrees with the intended state",
        ),
        (
            "member in another port-channel",
            dict(running=edit(RUN_PRE, "ethernet1/8", replace=("channel-group 501 mode active", "channel-group 502 mode active"))),
            "channel-group 502 mode active",
        ),
        ("member up on the device", dict(running=edit(RUN_PRE, "ethernet1/8", drop="shutdown")), "Ethernet1/8"),
        ("parent up on the device", dict(running=edit(RUN_PRE, "port-channel501", drop="shutdown")), "Port-channel501"),
        ("conflicting member command", dict(pending=PEND[:-1] + ["interface ethernet1/8", "  no mtu 9216", "configure terminal"]), "mtu 9216"),
        (
            "foreign member command",
            dict(pending=PEND[:-1] + ["interface ethernet1/8", "  switchport trunk allowed vlan 10", "configure terminal"]),
            "switchport trunk allowed vlan 10",
        ),
    ],
)
def test_inherited_mtu_addition_negatives_refuse_before_any_deploy(case, kw, needle):
    ctrl, status, result = mr(**kw)
    assert status == "fail" and needle in result["msg"], (case, result.get("msg"))
    assert "deploy" not in ctrl.kinds(), case


def test_an_explicit_member_addition_keeps_the_ordinary_validation():
    """DERIVED control: the member's own `mtu 9216` in the pending is ordinary validation (the rule is not used)."""
    ctrl, status, result = mr(pending=PEND[:-1] + ["interface ethernet1/8", "  mtu 9216", "configure terminal"])
    assert status == "exit", result.get("msg")
    assert ctrl.kinds() == ["modify", "deploy"]


# ------------------------------------------------------------------ S6 original (combined) -- PREDICTION, needs the live replay
def s6(pending=None):
    pf = FX["s6"]["preview"]
    ctrl = MRController(FX["s6"]["intent_pre"])
    ctrl.previews = [entry(pf["pendingConfig"] if pending is None else pending, pf["runningConfig_stanzas"], pf["expectedConfig_stanzas"])] * 3
    cfg = [dict(c, switch=[SWITCH_IP]) for c in FX["s6"]["config"]]
    status, result = run(ctrl, cfg, state="replaced", patch_version=SMU)
    return ctrl, status, result


def test_s6_replay_sends_the_measured_live_modify_payload():
    ctrl, _status, _result = s6()
    sent = ctrl.modify_nv(PO)
    assert len(sent) == 1
    live = harness_nv(FX["s6"]["modify_nvpairs"])
    differ = dict((k, (live.get(k), sent[0].get(k))) for k in set(live) | set(sent[0]) if k not in BOOK and str(live.get(k)) != str(sent[0].get(k)))
    assert differ == {}, differ


def test_s6_measured_preview_refused_by_c1r3_deploys_under_c1r4_as_a_prediction():
    """The measured S6 preview (refused it: member `mtu 9216` absent) combines the reverse MTU with companion withdrawals. Deploying
    here is a PREDICTION from the isolated MTU measurement plus the existing validation of the explicit member lines; only the live replay confirms."""
    ctrl, status, result = s6()
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.kinds() == ["modify", "deploy"]


def test_s6_measured_preview_without_the_parent_mtu_is_refused():
    """DERIVED negative: the measured S6 preview minus the parent's `mtu 9216` line -> no inheritance, ordinary refusal."""
    pend = [l for l in FX["s6"]["preview"]["pendingConfig"] if l.strip() != "mtu 9216"]
    ctrl, status, result = s6(pending=pend)
    assert status == "fail" and "mtu 9216" in result["msg"], result.get("msg")
    assert "deploy" not in ctrl.kinds()


# ------------------------------------------------------------------ unit level: the addition branch
def _m(scalars, kind=P.MODE_HOST):
    return P.Model(set(scalars), kind, (), True)


MEM_PRE = {"channel-group 501 mode active", "shutdown", "switchport"}
MEM_POST = MEM_PRE | {"mtu 9216"}


def _ctx(**over):
    ctx = {
        "po_number": "501",
        "pc_mode": "active",
        "parent": "port-channel501",
        "parent_desired": _m({"shutdown", "switchport", "mtu 9216"}),
        "parent_vocabulary": None,
        "parent_body": ["switchport", "mtu 9216", "shutdown"],
        "parent_ok": True,
    }
    ctx.update(over)
    return ctx


def _entry(parent_lines):
    return {"runningConfig": ["interface port-channel501"] + ["  " + x for x in parent_lines]}


PARENT_RUN = ["shutdown", "switchport mode private-vlan host", "switchport private-vlan host-association 2210 2212"]


@pytest.mark.parametrize(
    "label,args,applied",
    [
        ("measured addition", dict(), True),
        ("parent not validated", dict(ctx=_ctx(parent_ok=False)), False),
        ("parent adds twice", dict(ctx=_ctx(parent_body=["mtu 9216", "mtu 9216"])), False),
        ("parent also withdraws", dict(ctx=_ctx(parent_body=["no mtu 9216", "mtu 9216"])), False),
        ("parent wants another MTU", dict(ctx=_ctx(parent_desired=_m({"shutdown", "mtu 1500"}), parent_body=["mtu 1500"])), False),
        ("parent running already has an MTU", dict(parent_running=PARENT_RUN + ["mtu 1500"]), False),
        ("parent mode not host", dict(ctx=_ctx(parent_desired=_m({"shutdown", "mtu 9216"}, kind=P.MODE_PROMISCUOUS))), False),
        ("member wants another MTU", dict(desired=_m(MEM_PRE | {"mtu 1500"})), False),
        ("member running holds an MTU", dict(observed=_m(MEM_PRE | {"mtu 1500"})), False),
        ("member pending carries an MTU line", dict(body=["mtu 9216"]), False),
        ("member mode changes", dict(desired=_m(MEM_POST, kind=P.MODE_PROMISCUOUS)), False),
        ("member not in this port-channel", dict(observed=_m((MEM_PRE - {"channel-group 501 mode active"}) | {"channel-group 502 mode active"})), False),
        ("member up", dict(observed=_m(MEM_PRE - {"shutdown"})), False),
        ("no context (vPC / creation / other paths)", dict(ctx=None), False),
    ],
)
def test_unit_inherited_mtu_addition_conditions(label, args, applied):
    observed = args.get("observed", _m(MEM_PRE))
    state, inherited = P.po_member_mtu_inherited_state(
        _entry(args.get("parent_running", PARENT_RUN)), observed, args.get("desired", _m(MEM_POST)), args.get("body", []), args.get("ctx", _ctx())
    )
    assert inherited is applied, label
    if applied:
        assert state.scalars == MEM_POST and observed.scalars == MEM_PRE
    else:
        assert state is observed, label
