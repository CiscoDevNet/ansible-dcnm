"""C1-R3 (Alpha, PR725-PVLAN-COMPANIONS-001): the member MTU withdrawal inherited from the port-channel, as MEASURED in M-G1 M1.

MEASURED inputs (fixtures/pvlan_po_m1_measured.json, provenance per field inside it):
  * OPERATOR: the GUI preview pending `interface port-channel501` / `no mtu 9216` (supplied by the operator, not captured by Alpha);
  * ALPHA: the intents before/after, the controller's runningConfig before M1 (M2 U1R recompute preview) and its expectedConfig after M1
    (post-M1 recompute preview, intent unchanged since the GUI save), the device running stanzas and the operational MTU (9216 -> 1500 on
    BOTH port-channel and member).
The module request that reproduces the GUI change is `merged` with `mtu: default` on the existing port-channel (the GUI payload itself is
not known and not invented). Real main() on the existing harness; only the controller boundary is simulated (207 SUCCESS modifies).
DERIVED inputs are marked in each test; they are predictions, never live evidence. vPC is not touched by C1-R3.
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

FX = json.load(open(os.path.join(os.path.dirname(__file__), "fixtures", "pvlan_po_m1_measured.json")))
PO, MEM = "Port-channel501", "Ethernet1/8"
MODIFY = "/rest/interface/modify"
DEPLOY = "/rest/globalInterface/deploy"
SMU = sorted(GIE_ENABLED_PATCH_VERSIONS)[0]
PEND = list(FX["operator_preview_pending"])
RUN_PRE = list(FX["pre"]["preview_running_stanzas"])
EXP_POST = list(FX["post"]["preview_expected_stanzas"])
EXP_PRE = list(FX["pre"]["preview_expected_stanzas"])
RUN_POST = list(FX["post"]["preview_running_stanzas"])


def harness_nv(nv):
    return dict((k, v) for k, v in nv.items() if k != "POLICY_ID")


class M1Controller(PoLifecycleController):
    def __init__(self, side="pre"):
        super(M1Controller, self).__init__()
        intent = FX[side]["intent"]
        self.detail[PO] = {"policy": intent["port-channel501"]["policy"], "nvPairs": harness_nv(intent["port-channel501"]["nvPairs"])}
        self.po_names.add(PO)
        self.detail[MEM] = {"policy": intent["Ethernet1/8"]["policy"], "nvPairs": harness_nv(intent["Ethernet1/8"]["nvPairs"])}

    def kinds(self):
        return [
            "modify" if p.endswith(MODIFY) else "deploy" if p.endswith(DEPLOY) else p
            for m, p, _d in self.calls
            if m in ("POST", "PUT", "DELETE") and "/config-preview" not in p and "bulk-update" not in p
        ]


def entry(pending, running, expected):
    return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [preview(pending, running=running, expected=expected)["DATA"][0]]}


def mtu_item(mtu="default"):
    return {
        "name": "po501",
        "type": "pc",
        "switch": [SWITCH_IP],
        "deploy": True,
        "profile": {"mode": "pvlan", "pvlan_mode": "host", "members": [MEM], "mtu": mtu},
    }


def m1(pending=None, running=None, expected=None, side="pre", mtu="default"):
    ctrl = M1Controller(side)
    ctrl.previews = [entry(PEND if pending is None else pending, RUN_PRE if running is None else running, EXP_POST if expected is None else expected)] * 3
    status, result = run(ctrl, [mtu_item(mtu)], state="merged", patch_version=SMU)
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


# ------------------------------------------------------------------ the measured form
def test_measured_m1_request_reproduces_the_post_intent_of_the_port_channel():
    """The module's merged `mtu: default` builds the port-channel intent the controller held after the GUI change (semantic nvPairs)."""
    ctrl, _status, _result = m1()
    sent = [i["nvPairs"] for c in ctrl.calls if c[0] == "POST" and c[1].endswith(MODIFY) for p in json.loads(c[2]) for i in p["interfaces"]]
    assert len(sent) == 1
    post = harness_nv(FX["post"]["intent"]["port-channel501"]["nvPairs"])
    book = P.PO_RELEASE_METADATA | {"SERIAL_NUMBER", "FABRIC_NAME"}
    differ = dict((k, (post.get(k), sent[0].get(k))) for k in set(post) | set(sent[0]) if k not in book and str(post.get(k)) != str(sent[0].get(k)))
    assert differ == {}, differ


def test_measured_m1_parent_only_withdrawal_deploys_through_the_inherited_member_mtu():
    ctrl, status, result = m1()
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.kinds() == ["modify", "deploy"]


def test_measured_m1_device_effect_is_recorded_in_the_fixture():
    """Fact recorded by Alpha's reads: both lost `mtu 9216` and run at operational MTU 1500 after a parent-only withdrawal."""
    assert [l for l in FX["pre"]["running_stanzas"] if l.strip() == "mtu 9216"] == ["  mtu 9216", "  mtu 9216"]
    assert not [l for l in FX["post"]["running_stanzas"] if l.strip().startswith("mtu")]
    assert all(v.startswith("MTU 1500 ") for v in FX["post"]["operational_mtu"].values())
    assert FX["post"]["preview"] == {"status": "In-Sync", "pendingConfig": []}


# ------------------------------------------------------------------ targeted negatives (each refuses, no deploy)
@pytest.mark.parametrize(
    "case,kw,needle",
    [
        ("parent withdraws another value", dict(pending=["interface port-channel501", "  no mtu 9000", "configure terminal"]), "no mtu 9000"),
        ("no parent withdrawal", dict(pending=["interface port-channel501", "  shutdown", "configure terminal"]), "mtu 9216"),
        ("member device MTU differs", dict(running=edit(RUN_PRE, "ethernet1/8", replace=("mtu 9216", "mtu 9000"))), "mtu 9000"),
        (
            "member in another port-channel",
            dict(running=edit(RUN_PRE, "ethernet1/8", replace=("channel-group 501 mode active", "channel-group 502 mode active"))),
            "channel-group 502 mode active",
        ),
        ("member up on the device", dict(running=edit(RUN_PRE, "ethernet1/8", drop="shutdown")), "Ethernet1/8"),
        ("parent up on the device", dict(running=edit(RUN_PRE, "port-channel501", drop="shutdown")), "Port-channel501"),
        ("conflicting expected member MTU", dict(expected=edit(EXP_POST, "ethernet1/8", add="mtu 1500")), "disagrees with the intended state"),
        (
            "foreign member command",
            dict(pending=PEND[:-1] + ["interface ethernet1/8", "  switchport trunk allowed vlan 10", "configure terminal"]),
            "switchport trunk allowed vlan 10",
        ),
        ("member admin-up command", dict(pending=PEND[:-1] + ["interface ethernet1/8", "  no shutdown", "configure terminal"]), "no shutdown"),
    ],
)
def test_inherited_mtu_withdrawal_negatives_refuse_before_any_deploy(case, kw, needle):
    ctrl, status, result = m1(**kw)
    assert status == "fail" and needle in result["msg"], (case, result.get("msg"))
    assert "deploy" not in ctrl.kinds(), case


def test_an_explicit_member_withdrawal_keeps_the_ordinary_validation():
    """DERIVED control: the member's own `no mtu 9216` in the pending is ordinary validation (the rule does not apply to it)."""
    pend = PEND[:-1] + ["interface ethernet1/8", "  no mtu 9216", "configure terminal"]
    ctrl, status, result = m1(pending=pend)
    assert status == "exit", result.get("msg")
    assert ctrl.kinds() == ["modify", "deploy"]


def test_the_reverse_default_to_jumbo_without_a_member_command_follows_the_c1r4_mr_rule():
    """DERIVED from the M1 captures (reverse direction): `mtu 9216` only on the parent. Refused by C1-R3 (not measured then); C1-R4 models
    it because MR-G1 MEASURED this direction (fixtures/pvlan_po_mr_measured.json, test_dcnm_intf_pvlan_po_mr_mtu.py)."""
    pend = ["interface port-channel501", "  mtu 9216", "configure terminal"]
    ctrl, status, result = m1(pending=pend, running=list(FX["post"]["preview_running_stanzas"]), expected=EXP_PRE, side="post", mtu="jumbo")
    assert status == "exit", result.get("msg")
    assert ctrl.kinds() == ["modify", "deploy"]


# ------------------------------------------------------------------ unit level: the rule
def _m(scalars, kind=P.MODE_HOST):
    return P.Model(set(scalars), kind, (), True)


MEMBER_PRE = {"channel-group 501 mode active", "shutdown", "switchport", "mtu 9216"}
MEMBER_POST = MEMBER_PRE - {"mtu 9216"}


def _ctx(**over):
    ctx = {
        "po_number": "501",
        "pc_mode": "active",
        "parent": "port-channel501",
        "parent_desired": _m({"shutdown", "switchport"}),
        "parent_vocabulary": None,
        "parent_body": ["no mtu 9216"],
        "parent_ok": True,
    }
    ctx.update(over)
    return ctx


def _entry(parent_lines):
    return {"runningConfig": ["interface port-channel501"] + ["  " + x for x in parent_lines]}


@pytest.mark.parametrize(
    "label,args,applied",
    [
        ("measured", dict(), True),
        ("parent not validated", dict(ctx=_ctx(parent_ok=False)), False),
        ("parent withdrawal twice", dict(ctx=_ctx(parent_body=["no mtu 9216", "no mtu 9216"])), False),
        ("parent wants an MTU", dict(ctx=_ctx(parent_desired=_m({"shutdown", "mtu 1500"}))), False),
        ("parent running without mtu 9216", dict(parent_running=["shutdown", "switchport mode private-vlan host"]), False),
        ("parent mode not host", dict(ctx=_ctx(parent_desired=_m({"shutdown"}, kind=P.MODE_PROMISCUOUS))), False),
        ("member wants an MTU", dict(desired=_m(MEMBER_POST | {"mtu 1500"})), False),
        ("member pending carries an MTU line", dict(body=["mtu 1500"]), False),
        ("member mode changes", dict(desired=_m(MEMBER_POST, kind=P.MODE_PROMISCUOUS)), False),
        ("member not in this port-channel", dict(observed=_m((MEMBER_PRE - {"channel-group 501 mode active"}) | {"channel-group 502 mode active"})), False),
        ("member up", dict(observed=_m(MEMBER_PRE - {"shutdown"})), False),
        ("no context (vPC / creation / other paths)", dict(ctx=None), False),
    ],
)
def test_unit_inherited_mtu_rule_conditions(label, args, applied):
    parent_running = args.get(
        "parent_running", ["shutdown", "switchport mode private-vlan host", "switchport private-vlan host-association 2210 2212", "mtu 9216"]
    )
    observed = args.get("observed", _m(MEMBER_PRE))
    state, inherited = P.po_member_mtu_inherited_state(
        _entry(parent_running), observed, args.get("desired", _m(MEMBER_POST)), args.get("body", []), args.get("ctx", _ctx())
    )
    assert inherited is applied, label
    if applied:
        assert state.scalars == MEMBER_POST and observed.scalars == MEMBER_PRE, "only `mtu 9216` is substituted; the input is not mutated"
    else:
        assert state is observed, label
