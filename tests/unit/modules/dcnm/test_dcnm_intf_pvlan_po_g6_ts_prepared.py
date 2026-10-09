"""PO G6 (Alpha): trunk secondary from a member PREPARED as access/routed, and equivalent member names.

MEASURED inputs (fixtures/pvlan_po_ts_exp1_measured.json, Alpha3's EXP-1 on placeholder-sw-2 Ethernet1/8 / port-channel504, NX-OS 10.5(5),
NDFC 12.6.0.267), extracted read-only:
  * per branch T (trunk), R (routed), A (access): the member state before the creation (intent, policies, running), the creation
    preview (full pending, running/expected stanzas), the deploy answer (T 500 device ERROR; R/A 200) and the post stanzas;
  * branch T clean0: a port-channel created through Manage (INTF_NAME/PO_ID `port-channel504`, MEMBER_INTERFACES `e1/8`) and the
    G5 TSR refusal on it.
SIMULATED: the harness serial; the EXP-1 previews followed a Manage create, here the module's legacy create (same device stanzas);
the release answers of the harness. Real main(); only the controller boundary is intercepted.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import os

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .test_dcnm_intf_pvlan_harness import SWITCH_IP, TRUNK, preview, run, trunk_host_nv
from .test_dcnm_intf_pvlan_po_g1 import PoLifecycleController, markdelete_ok

FX = json.load(open(os.path.join(os.path.dirname(__file__), "fixtures", "pvlan_po_ts_exp1_measured.json")))
MEM, PO_DEV, PO = "Ethernet1/8", "port-channel504", "Port-channel504"
TS = "trunk secondary"
TS1_PROFILE = {  # Alpha3 models/g1/PO_TS1_TS5_replaced_2210_2212_G1.yml (resources PO_TS_RESOURCES.yml)
    "mode": "pvlan",
    "pvlan_mode": TS,
    "members": [MEM],
    "pc_mode": "active",
    "admin_state": False,
    "pvlan_association": [{"primary_vlan": 2210, "secondary_vlan": 2212}],
    "native_vlan": "2301",
    "allowed_vlans": "2301",
}


def branch(b):
    return copy.deepcopy(FX["branches"][b])


def member_nv(b):
    return dict((k, v) for k, v in branch(b)["member_before"]["intent"][MEM]["nvPairs"].items() if k != "POLICY_ID")


def member_policy(b):
    return branch(b)["member_before"]["intent"][MEM]["policy"]


def measured_preview(b, pending=None, running=None, expected=None):
    cp = branch(b)["create_preview"]
    return preview(
        pending if pending is not None else cp["pendingConfig"],
        running=running if running is not None else cp["runningConfig_stanzas"],
        expected=expected if expected is not None else cp["expectedConfig_stanzas"],
    )


def self_children(b):
    """The measured live child policies of the prepared member (routed: routed_interface/interface_mtu/shut_interface, source =
    the member itself)."""
    out = []
    for p in branch(b)["member_before"]["policies"]:
        if p.get("source") and p["source"].lower() == MEM.lower():
            out.append(dict(p, entityType="INTERFACE", serialNumber="x"))
    return out


def ctrl_for(b, nv=None):
    ctrl = PoLifecycleController()
    ctrl.detail[MEM] = {"policy": member_policy(b), "nvPairs": nv if nv is not None else member_nv(b)}
    ctrl.policies_extra = self_children(b)
    return ctrl


def create(ctrl, pv=None, **profile):
    if pv is not None:
        ctrl.previews = [pv]
    prof = dict(TS1_PROFILE, **profile)
    return run(ctrl, [{"name": "po504", "type": "pc", "switch": [SWITCH_IP], "deploy": True, "profile": prof}], state="replaced")


# ------------------------------------------------------------------ the measured EXP-1 data itself
def test_fixture_states_the_measured_branches():
    assert member_policy("T") == TRUNK and member_policy("R") == P.PO_ROUTED_BASELINE_POLICY and member_policy("A") == P.PO_ACCESS_BASELINE_POLICY
    assert branch("T")["deploy_answer"]["http"] == 500 and "PVLAN TRUNK SEC config present" in json.dumps(branch("T")["deploy_answer"])
    assert branch("R")["deploy_answer"]["http"] == 200 and branch("A")["deploy_answer"]["http"] == 200
    assert sorted(p["templateName"] for p in self_children("R")) == sorted(P.PO_ROUTED_SELF_CHILDREN) and self_children("A") == []
    assert branch("R")["member_before"]["running_stanzas"][MEM]["lines"] == ["no switchport", "mtu 9216"]


# ------------------------------------------------------------------ admission of a prepared member (trunk secondary)
@pytest.mark.parametrize("b", ["A", "R"])
def test_trunk_secondary_creation_from_the_measured_prepared_member_creates_and_deploys(b):
    ctrl = ctrl_for(b)
    status, result = create(ctrl, measured_preview(b))
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1 and ctrl.bulk_bodies() == []
    body = json.loads(ctrl.creates()[0][2])
    nv = (body[0] if isinstance(body, list) else body)["interfaces"][0]["nvPairs"]
    assert nv["PVLAN_MODE"] == TS and nv["MEMBER_INTERFACES"] == MEM and nv["ADMIN_STATE"] == "false"
    assert (nv["PVLAN_NATIVE_VLAN"], nv["PVLAN_ALLOWED_VLANS"]) == ("2301", "2301")
    assert P.pairs_from_wire(nv["ASSOCIATION_LIST"], "ASSOCIATION_LIST") == [(2210, 2212)]
    assert result["pvlan_gate"][0]["targets"][PO] == "deploy"
    assert ctrl.detail[MEM]["policy"] == member_policy(b), "the module never writes the member: no conversion"


def test_trunk_secondary_creation_from_the_measured_trunk_member_is_the_known_incident_refused_before_any_write():
    ctrl = ctrl_for("T")
    status, result = create(ctrl, measured_preview("T"))
    assert status == "fail" and "Known incident pending engineering" in result["msg"] and "access" in result["msg"]
    assert ctrl.writes() == [], "no create, no deploy: the device would reject the join (EXP-1 T: deploy 500, partial)"


@pytest.mark.parametrize(
    "b, key, value",
    [
        ("A", "ACCESS_VLAN", "10"),
        ("A", "ENABLE_STORM_CONTROL", "true"),
        ("A", "ADMIN_STATE", "true"),
        ("A", "CONF", "lldp transmit"),
        ("R", "IP", "192.0.2.1"),
        ("R", "INTF_VRF", "blue"),
        ("R", "ospf", "true"),
        ("R", "ADMIN_STATE", "true"),
    ],
)
def test_a_prepared_member_with_configuration_outside_the_contract_is_refused_before_any_write(b, key, value):
    nv = member_nv(b)
    nv[key] = value
    ctrl = ctrl_for(b, nv=nv)
    status, result = create(ctrl, measured_preview(b))
    assert status == "fail" and ctrl.writes() == [], result.get("msg")


@pytest.mark.parametrize(
    "extra, needle",
    [
        ({"entityName": MEM, "templateName": "Config_Profile", "source": "OVERLAY"}, "live policies"),
        ({"entityName": MEM, "templateName": "routed_interface", "source": ""}, "live policies"),
        ({"entityName": MEM, "templateName": "interface_mtu", "source": "Ethernet1/9"}, "live policies"),
    ],
)
def test_routed_member_ownership_admits_only_its_measured_self_children(extra, needle):
    ctrl = ctrl_for("R")
    ctrl.policies_extra.append(dict(extra, entityType="INTERFACE", deleted=False, policyId="POLICY-990001", priority=500, serialNumber="x"))
    status, result = create(ctrl, measured_preview("R"))
    assert status == "fail" and needle in result["msg"] and ctrl.writes() == [], result.get("msg")


def test_an_access_member_is_not_admitted_for_the_other_modes():
    ctrl = ctrl_for("A")
    prof = dict((k, v) for k, v in TS1_PROFILE.items() if k not in ("native_vlan", "allowed_vlans"))
    prof["pvlan_mode"] = "host"
    status, result = run(ctrl, [{"name": "po504", "type": "pc", "switch": [SWITCH_IP], "deploy": True, "profile": prof}], state="replaced")
    assert status == "fail" and "only int_trunk_host is" in result["msg"] and ctrl.writes() == [], result.get("msg")


def _member_lines(lines, old, new):
    out = []
    in_member = False
    for line in lines:
        if not line.startswith(" "):
            in_member = line.strip().lower() == "interface ethernet1/8"
        out.append(new if in_member and line == old else line)
    return out


@pytest.mark.parametrize(
    "b, change, needle",
    [
        ("A", dict(running_add="  switchport access vlan 10"), "cannot interpret"),
        ("A", dict(running_add="  logging event port link-status"), "outside its measured baseline"),
        ("R", dict(running_add="  ip address 192.0.2.1/24"), "cannot interpret"),
        ("R", dict(pending_drop="  shutdown"), "intended command 'shutdown' is absent"),
        ("A", dict(pending_swap=("  channel-group 504 force mode active", "  channel-group 505 force mode active")), "unmodeled command"),
        ("R", dict(expected_swap=("  switchport private-vlan trunk native vlan 2301", "  switchport private-vlan trunk native vlan 2302")), "disagrees"),
        ("A", dict(pending_add="  no shutdown"), "unexpected removal"),
    ],
)
def test_the_gate_still_refuses_each_single_change_of_the_measured_prepared_forms(b, change, needle):
    cp = branch(b)["create_preview"]
    running, pending, expected = list(cp["runningConfig_stanzas"]), list(cp["pendingConfig"]), list(cp["expectedConfig_stanzas"])
    if "running_add" in change:
        running.insert(running.index("interface ethernet1/8") + 1, change["running_add"])
    if "pending_drop" in change:
        idx = len(pending) - 1 - pending[::-1].index(change["pending_drop"])
        pending.pop(idx)
    if "pending_swap" in change:
        pending = [change["pending_swap"][1] if line == change["pending_swap"][0] else line for line in pending]
    if "pending_add" in change:
        pending = pending[:-1] + [change["pending_add"], "configure terminal"]
    if "expected_swap" in change:
        expected = _member_lines(expected, *change["expected_swap"])
    ctrl = ctrl_for(b)
    status, result = create(ctrl, measured_preview(b, pending=pending, running=running, expected=expected))
    assert status == "fail" and needle in result["msg"], (change, result.get("msg"))
    assert len(ctrl.creates()) == 1 and ctrl.deploys() == []


def test_routed_force_state_takes_the_admin_line_from_the_pending_and_drops_no_switchport():
    b = "R"
    po_nv = P.po_host_nvpairs(dict(TS1_PROFILE), PO)
    post_pair = (P.PO_MEMBER_POLICY, P.po_member_nvpairs(po_nv, member_nv(b)))
    post = P.render(*post_pair)
    vocab = P.transition_vocabulary((member_policy(b), member_nv(b)), post_pair)
    pre = P.cli_model(["no switchport", "mtu 9216"], vocab)
    assert "no shutdown" in pre.scalars and "no switchport" in pre.scalars and not pre.foreign
    body = ["channel-group 504 force mode active", "shutdown"]
    member_force = {"po_number": "504", "pc_mode": "active", "mode": TS, "baseline": member_policy(b)}
    rest, forced, problems = P.po_member_force_transition(body, pre, post, member_force)
    assert problems == [] and rest == ["shutdown"]
    assert "no switchport" not in forced.scalars and "no shutdown" not in forced.scalars and "shutdown" not in forced.scalars
    assert P.validate_transition(rest, forced, post) == []
    assert P.validate_transition([], forced, post) == ["intended command 'shutdown' is absent from the pending"]


# ------------------------------------------------------------------ release contract after a prepared creation
def test_deleting_a_trunk_secondary_po_created_from_an_access_member_releases_to_the_trunk_host_not_back_to_access():
    """The release contract (measured in EXP-1 cleanups): the controller releases the member as int_trunk_host; G5 corrects its
    admin state. The module does not restore the prepared access/routed policy: that is a separate, explicit step."""
    ctrl = ctrl_for("A")
    assert create(ctrl, measured_preview("A"))[0] == "exit"
    nv = {
        "PO_ID": PO,
        "PC_MODE": "active",
        "PVLAN_MODE": TS,
        "CDP_ENABLE": "true",
        "lldpTransmit": "false",
        "lldpReceive": "false",
        "LACP_PORT_PRIO": "32768",
        "LACP_RATE": "normal",
        "DESC": "",
        "CONF": "",
        "ADMIN_STATE": "false",
        "INTF_NAME": MEM,
    }
    ctrl.detail[MEM] = {"policy": P.PO_MEMBER_POLICY, "nvPairs": nv}  # SYNTHETIC member flip (as in g1 created())
    ctrl.policies_extra = []
    ctrl.next_invocation()
    ctrl.calls = []
    released = [
        "interface Ethernet1/8",
        "  switchport",
        "  switchport mode trunk",
        "  switchport trunk allowed vlan none",
        "  spanning-tree port type edge trunk",
        "  mtu 9216",
        "  shutdown",
    ]
    post = branch("A")["post"]["running_stanzas"]
    run_cfg = (
        ["interface port-channel504"]
        + ["  " + line for line in post[PO_DEV]["lines"]]
        + ["interface ethernet1/8"]
        + ["  " + line for line in post[MEM]["lines"]]
    )
    pend = [
        "no interface port-channel504",
        "interface ethernet1/8",
        "  no channel-group 504 force mode active",
        "  no switchport private-vlan association trunk 2210 2212",
        "  no switchport private-vlan trunk native vlan 2301",
        "  no switchport private-vlan trunk allowed vlan 2301",
        "  no switchport mode private-vlan trunk secondary",
        "interface ethernet1/8",
        "  switchport",
        "  switchport mode trunk",
        "  switchport trunk allowed vlan none",
        "  spanning-tree port type edge trunk",
        "  shutdown",
        "configure terminal",
    ]  # SYNTHETIC (measured host/P form transposed)
    ctrl.previews = [preview(pend, running=run_cfg, expected=released)]
    status, result = run(ctrl, [{"name": "po504", "switch": [SWITCH_IP], "deploy": True}], state="deleted")
    assert status == "exit", result.get("msg")
    assert len(ctrl.markdeletes()) == 1 and len(ctrl.deploys()) == 1
    assert ctrl.detail[MEM]["policy"] == TRUNK and ctrl.detail[MEM]["nvPairs"]["ADMIN_STATE"] == "false"


# ------------------------------------------------------------------ equivalent names (Manage-created port-channel)
class ManageReleaseController(PoLifecycleController):
    """The g1 lifecycle harness, but the mark-delete releases the member the way the controller did for the Manage-created
    port-channel (EXP-1 T recovery, MEASURED: the member read after the mark-delete was Ethernet1/8 int_trunk_host,
    ADMIN_STATE "true"). The g1 fake would release the literal MEMBER_INTERFACES token `e1/8` instead."""

    def __init__(self):
        super(ManageReleaseController, self).__init__()
        self.release_member = False

    def __call__(self, mod, method, path, data=None):
        resp = super(ManageReleaseController, self).__call__(mod, method, path, data)
        if method == "DELETE" and path.endswith("/rest/interface/markdelete"):
            self.detail[MEM] = {"policy": TRUNK, "nvPairs": dict(trunk_host_nv(MEM), ADMIN_STATE="true")}
        return resp


def manage_ctrl():
    """The MEASURED Manage-created port-channel of EXP-1 T clean0: Po intent `port-channel504` with MEMBER_INTERFACES `e1/8`, the
    member `int_port_channel_pvlan_member` of PO_ID `port-channel504` (POLICY_ID dropped for the harness numbering)."""
    st = FX["manage_created_po_T_clean0"]
    ctrl = ManageReleaseController()
    for name in (PO_DEV, MEM):
        it = st["intent"][name]
        ctrl.detail[name] = {"policy": it["policy"], "nvPairs": dict((k, v) for k, v in it["nvPairs"].items() if k != "POLICY_ID")}
    ctrl.po_names.add(PO_DEV)
    return ctrl


def test_fixture_states_the_manage_names_and_the_g5_refusal():
    st = FX["manage_created_po_T_clean0"]["intent"]
    assert st[PO_DEV]["nvPairs"]["MEMBER_INTERFACES"] == "e1/8" and st[PO_DEV]["nvPairs"]["PO_ID"] == PO_DEV
    assert "not an existing physical interface" in FX["g5_tsr_refusal_msg"] and "outside the port-channel request" in FX["g5_tsr_refusal_msg"]


def test_member_alias_resolution_is_explicit_ports_only():
    for token in ("e1/8", "eth1/8", "Ethernet1/8", " ethernet1/8 "):
        assert P.po_member_canonical(token) == "ethernet1/8"
    for token in ("Ethernet1/8-9", "port-channel504", "", None, "e1/8,e1/9"):
        assert P.po_member_canonical(token) is None
    assert P._po_norm("MEMBER_INTERFACES", "e1/8") == P._po_norm("MEMBER_INTERFACES", "Ethernet1/8")
    assert P._po_norm("MEMBER_INTERFACES", "e1/8") != P._po_norm("MEMBER_INTERFACES", "Ethernet1/9")


def test_a_manage_created_port_channel_is_deleted_through_the_g5_path_with_the_controller_spelling():
    ctrl = manage_ctrl()
    released = [
        "interface Ethernet1/8",
        "  switchport",
        "  switchport mode trunk",
        "  switchport trunk allowed vlan none",
        "  spanning-tree port type edge trunk",
        "  mtu 9216",
        "  shutdown",
    ]
    post = branch("T")["post"]["running_stanzas"]
    run_cfg = (
        ["interface port-channel504"]
        + ["  " + line for line in post[PO_DEV]["lines"]]
        + ["interface ethernet1/8"]
        + ["  " + line for line in post[MEM]["lines"]]
    )
    pend = [
        "no interface port-channel504",
        "interface ethernet1/8",
        "  switchport",
        "  switchport mode trunk",
        "  switchport trunk allowed vlan none",
        "  spanning-tree port type edge trunk",
        "  shutdown",
        "configure terminal",
    ]  # SYNTHETIC
    ctrl.previews = [preview(pend, running=run_cfg, expected=released)]
    status, result = run(ctrl, [{"name": "po504", "switch": [SWITCH_IP], "deploy": True}], state="deleted")
    assert status == "exit", result.get("msg")
    deletes = ctrl.markdeletes()
    assert len(deletes) == 1 and [i["ifName"] for i in json.loads(deletes[0][2])] == [PO_DEV], "the controller's own Po spelling"
    assert PO_DEV not in ctrl.detail and ctrl.detail[MEM]["policy"] == TRUNK and ctrl.detail[MEM]["nvPairs"]["ADMIN_STATE"] == "false"
    modifies = [json.loads(c[2]) for c in ctrl.calls if c[0] == "POST" and c[1].endswith("/rest/interface/modify")]
    assert len(modifies) == 1 and modifies[0][0]["interfaces"][0]["ifName"] == MEM, "the released member, controller spelling"


@pytest.mark.parametrize("member_text, needle", [("e1/9", "not the member of this port-channel"), ("Ethernet1/8-9", "cannot be resolved")])
def test_an_alias_that_does_not_name_the_member_is_still_refused_before_any_write(member_text, needle):
    ctrl = manage_ctrl()
    ctrl.detail[PO_DEV]["nvPairs"]["MEMBER_INTERFACES"] = member_text
    if member_text == "e1/9":
        ctrl.detail["Ethernet1/9"] = {"policy": TRUNK, "nvPairs": dict(ctrl.detail[MEM]["nvPairs"], INTF_NAME="Ethernet1/9")}
    status, result = run(ctrl, [{"name": "po504", "switch": [SWITCH_IP], "deploy": True}], state="deleted")
    assert status == "fail" and ctrl.markdeletes() == [] and ctrl.deploys() == [], result.get("msg")


def test_merged_update_of_a_manage_created_port_channel_keeps_the_member_alias_on_the_wire():
    st = FX["manage_created_po_T_clean0"]["intent"]
    have = dict((k, v) for k, v in st[PO_DEV]["nvPairs"].items())
    raw = {"pvlan_mode": TS, "members": [MEM], "pvlan_association": [{"primary_vlan": 2410, "secondary_vlan": 2412}]}
    out = P.reconcile_po("merged", raw, PO, P.PO_HOST_POLICY, have)
    assert out["blocked"] == [] and out["update"], out["blocked"]
    assert out["nv"]["MEMBER_INTERFACES"] == "e1/8" and out["nv"]["PO_ID"] == PO_DEV
    assert P.pairs_from_wire(out["nv"]["ASSOCIATION_LIST"], "ASSOCIATION_LIST") == [(2210, 2212), (2410, 2412)]


def test_markdelete_helper_is_still_the_measured_shape():
    assert markdelete_ok('[{"ifName": "port-channel504", "serialNumber": "x"}]')["DATA"]["value"][0]["IfName"] == PO_DEV
