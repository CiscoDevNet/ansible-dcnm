"""PO G5 / NEXT_MODES (Alpha): promiscuous, trunk promiscuous and trunk secondary on a regular port-channel with ONE member.

NOT LIVE TESTED. G3 refused these creations before any write because the member's `channel-group N force` transition was
measured only for host (H1 preview). G5 models the same transition for the other three modes as an explicit INFERENCE
(PO_FORCE_INFERRED_MODES): the force carries from the parent the mode line, the list pairs and, for the trunk modes, the
PVLAN trunk native/allowed lines; every other member line is kept from the member and must change, if at all, through its
own pending line. The gate is unchanged.

Every preview below is SYNTHETIC (the measured host form transposed, through the existing g1 builders); the profiles are
the existing battery ones (Alpha P1, Alpha2 TP1/TP2/TP4, Alpha3 TS1/TS2), on the harness port-channel10/Ethernet1/7. The
networks 2410 (primary) and 2412 (isolated) are SYNTHETIC additions to the harness fixture for the second primary.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import os

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .test_dcnm_intf_pvlan_harness import IF7, SERIAL, SWITCH_IP, TRUNK, preview, run, trunk_host_nv
from .test_dcnm_intf_pvlan_po_g1 import PoLifecycleController, baseline, create_preview, del_item, delete_preview, item, member_stanza, po_stanza
from .test_dcnm_intf_pvlan_po_host import PO, PO_HOST, PO_ITEM_NAME, PO_MEMBER, RUNNING_MEMBER

NATIVE = "switchport private-vlan trunk native vlan 2301"
ALLOWED = "switchport private-vlan trunk allowed vlan 2301"

# Battery profiles (creation) and their synthetic expected list lines.
CASES = {
    "promiscuous": (
        {"pvlan_mapping": [{"primary_vlan": 2210, "secondary_vlans": "2212"}]},
        ["switchport private-vlan mapping 2210 2212"],
    ),
    "trunk promiscuous": (
        {
            "pvlan_mapping": [{"primary_vlan": 2210, "secondary_vlans": "2211-2212"}, {"primary_vlan": 2410, "secondary_vlans": "2412"}],
            "native_vlan": "2301",
            "allowed_vlans": "2301",
        },
        [
            NATIVE,
            ALLOWED,
            "switchport private-vlan mapping trunk 2210 2211",
            "switchport private-vlan mapping trunk 2210 2212",
            "switchport private-vlan mapping trunk 2410 2412",
        ],
    ),
    "trunk secondary": (
        {
            "pvlan_association": [{"primary_vlan": 2210, "secondary_vlan": 2212}, {"primary_vlan": 2410, "secondary_vlan": 2412}],
            "native_vlan": "2301",
            "allowed_vlans": "2301",
        },
        [NATIVE, ALLOWED, "switchport private-vlan association trunk 2210 2212", "switchport private-vlan association trunk 2410 2412"],
    ),
}
MODES = sorted(CASES)


def with_second_primary(ctrl):
    """SYNTHETIC networks for the battery's second primary: 2410 primary, 2412 isolated (copied shapes of the fixture)."""
    nets = ctrl.networks
    prim = copy.deepcopy([n for n in nets if n["type"] == "Primary"][0])
    iso = copy.deepcopy([n for n in nets if n["type"] == "Isolated"][0])
    prim.update(networkId=30410, networkName="SYN_PRIMARY_2410", networkTemplateConfig=prim["networkTemplateConfig"].replace("2210", "2410"))
    iso.update(
        networkId=30412,
        networkName="SYN_ISOLATED_2412",
        primaryNetworkId=30410,
        networkTemplateConfig=iso["networkTemplateConfig"].replace("2212", "2412"),
    )
    nets += [prim, iso]
    return ctrl


def new_ctrl(mode=None):
    return with_second_primary(baseline(mode))


def creation_preview(mode, lines, pending_member=None, expected_member=None, extra=()):
    """The synthetic creation preview of g1 (measured host form transposed) with an optional named change."""
    pv = create_preview(mode, lines)
    entry = pv["DATA"][0]
    if pending_member is not None:
        pend = entry["pendingConfig"]
        start = len(pend) - 1 - pend[::-1].index("interface ethernet1/7")
        entry["pendingConfig"] = pend[: start + 1] + ["  " + l for l in pending_member] + ["configure terminal"]
    if expected_member is not None:
        entry["expectedConfig"] = ["hostname placeholder-sw-1"] + po_stanza(mode, lines) + expected_member
    if extra:
        entry["pendingConfig"] = entry["pendingConfig"][:-1] + list(extra) + ["configure terminal"]
    return pv


def create(mode, ctrl=None, pv=None):
    profile, lines = CASES[mode]
    ctrl = ctrl or new_ctrl(mode)
    ctrl.previews = [pv or creation_preview(mode, lines)]
    status, result = run(ctrl, [item(mode, **profile)], state="replaced")
    return ctrl, status, result


def existing(mode):
    """A port-channel of `mode` created through main() with the battery profile, then the SYNTHETIC member flip of the g1
    helper (the controller rewriting the member as int_port_channel_pvlan_member)."""
    ctrl, status, result = create(mode)
    assert status == "exit", result.get("msg")
    ctrl.detail[IF7] = {
        "policy": PO_MEMBER,
        "nvPairs": {
            "PO_ID": PO,
            "PC_MODE": "active",
            "PVLAN_MODE": mode,
            "CDP_ENABLE": "true",
            "lldpTransmit": "false",
            "lldpReceive": "false",
            "LACP_PORT_PRIO": "32768",
            "LACP_RATE": "normal",
            "DESC": "",
            "CONF": "",
            "ADMIN_STATE": "false",
            "INTF_NAME": IF7,
        },
    }
    ctrl.next_invocation()
    ctrl.calls = []
    return ctrl


# ------------------------------------------------------------------ creation through main(), battery profiles
@pytest.mark.parametrize("mode", MODES)
def test_creation_with_the_battery_profile_writes_the_lists_native_and_allowed_and_deploys(mode):
    ctrl, status, result = create(mode)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1 and ctrl.bulk_bodies() == []
    body = json.loads(ctrl.creates()[0][2])
    nv = (body[0] if isinstance(body, list) else body)["interfaces"][0]["nvPairs"]
    assert nv["PVLAN_MODE"] == mode and nv["MEMBER_INTERFACES"] == IF7 and nv["ADMIN_STATE"] == "false"
    if mode == "promiscuous":
        assert P.pairs_from_wire(nv["MAPPING_LIST"], "MAPPING_LIST") == [(2210, 2212)]
        assert (nv["PVLAN_NATIVE_VLAN"], nv["PVLAN_ALLOWED_VLANS"], nv["ASSOCIATION_LIST"]) == ("", "", "")
    elif mode == "trunk promiscuous":
        assert P.pairs_from_wire(nv["MAPPING_LIST"], "MAPPING_LIST") == [(2210, 2211), (2210, 2212), (2410, 2412)]
        assert (nv["PVLAN_NATIVE_VLAN"], nv["PVLAN_ALLOWED_VLANS"], nv["ASSOCIATION_LIST"]) == ("2301", "2301", "")
    else:
        assert P.pairs_from_wire(nv["ASSOCIATION_LIST"], "ASSOCIATION_LIST") == [(2210, 2212), (2410, 2412)]
        assert (nv["PVLAN_NATIVE_VLAN"], nv["PVLAN_ALLOWED_VLANS"], nv["MAPPING_LIST"]) == ("2301", "2301", "")
    assert result["pvlan_gate"][0]["targets"][PO] == "deploy"


def test_force_basis_is_measured_for_host_only_and_inferred_for_the_other_modes():
    assert P.po_force_basis("host") == "measured"
    assert [P.po_force_basis(m) for m in MODES] == ["inferred"] * 3
    assert P.po_force_basis("isolated") is None and P.po_force_unmeasured("isolated")


# ------------------------------------------------------------------ what the force takes from the parent / keeps from the member
@pytest.mark.parametrize("mode", MODES)
def test_forced_member_state_takes_mode_lists_native_allowed_from_the_parent_and_keeps_the_member_lines(mode):
    profile, lines = CASES[mode]
    parent = P.po_host_nvpairs(dict(item(mode, **profile)["profile"], pvlan_mode=mode), PO)
    member_nv = trunk_host_nv(IF7)
    post_pair = (PO_MEMBER, P.po_member_nvpairs(parent, member_nv))
    post = P.render(*post_pair)
    vocab = P.transition_vocabulary((TRUNK, member_nv), post_pair)
    running = [l.strip() for l in RUNNING_MEMBER[1:]] + ["switchport private-vlan trunk native vlan 99"]
    pre = P.cli_model(running, vocab)
    body = ["no spanning-tree port type edge trunk", "channel-group 10 force mode active", "shutdown"]
    rest, forced, problems = P.po_member_force_transition(body, pre, post, {"po_number": "10", "pc_mode": "active", "mode": mode})
    assert problems == [] and rest == ["no spanning-tree port type edge trunk", "shutdown"]
    trunk = mode != "promiscuous"
    assert (NATIVE in forced.scalars, ALLOWED in forced.scalars) == (trunk, trunk), "parent native/allowed, trunk modes only"
    assert "switchport private-vlan trunk native vlan 99" not in forced.scalars, "a previous PVLAN line does not survive"
    assert {"switchport", "switchport mode private-vlan %s" % mode, "channel-group 10 mode active"} <= forced.scalars
    assert {"mtu 9216", "shutdown", "spanning-tree port type edge trunk"} <= forced.scalars, "kept from the member"
    assert not [l for l in forced.scalars if l == "switchport mode trunk" or l.startswith("switchport trunk ")]
    assert forced.pairs == post.pairs and forced.list_kind == mode
    assert P.validate_transition(rest, forced, post) == []


@pytest.mark.parametrize("mode", MODES)
def test_a_member_line_the_parent_does_not_own_is_not_assumed_by_the_force(mode):
    """Not a blind copy of the intended member: a description the member model holds (kept from the member's intent)
    but the device lacks is NOT delivered by the force; without its own pending line the transition is refused."""
    profile, _lines = CASES[mode]
    parent = P.po_host_nvpairs(dict(item(mode, **profile)["profile"], pvlan_mode=mode), PO)
    member_nv = dict(trunk_host_nv(IF7), DESC="uplink")
    post_pair = (PO_MEMBER, P.po_member_nvpairs(parent, member_nv))
    post = P.render(*post_pair)
    assert "description uplink" in post.scalars
    pre = P.cli_model([l.strip() for l in RUNNING_MEMBER[1:]], P.transition_vocabulary((TRUNK, member_nv), post_pair))
    body = ["no spanning-tree port type edge trunk", "channel-group 10 force mode active", "shutdown"]
    rest, forced, problems = P.po_member_force_transition(body, pre, post, {"po_number": "10", "pc_mode": "active", "mode": mode})
    assert problems == [] and "description uplink" not in forced.scalars
    assert P.validate_transition(rest, forced, post) == ["intended command 'description uplink' is absent from the pending"]
    assert P.validate_transition(rest + ["description uplink"], forced, post) == []


# ------------------------------------------------------------------ the gate still refuses, per mode, before any deploy
def _member(mode, lines, drop=(), swap=None):
    out = [l for l in member_stanza(mode, lines) if l.strip() not in drop]
    if swap:
        out = [("  " + swap[1]) if l.strip() == swap[0] else l for l in out]
    return out


NEGATIVE = [
    ("expected member without the parent native", lambda m, l: dict(expected_member=_member(m, l, drop=(NATIVE,))), True, "disagrees"),
    ("expected member with another native", lambda m, l: dict(expected_member=_member(m, l, swap=(NATIVE, NATIVE.replace("2301", "2302")))), True, "disagrees"),
    ("expected member with another allowed", lambda m, l: dict(expected_member=_member(m, l, swap=(ALLOWED, ALLOWED + ",2302"))), True, "disagrees"),
    (
        "expected member in another PVLAN mode",
        lambda m, l: dict(expected_member=_member(m, l, swap=("switchport mode private-vlan %s" % m, "switchport mode private-vlan host"))),
        False,
        "disagrees",
    ),
    (
        "expected member in another port-channel",
        lambda m, l: dict(expected_member=_member(m, l, swap=("channel-group 10 mode active", "channel-group 11 mode active"))),
        False,
        "disagrees",
    ),
    ("force for another port-channel", lambda m, l: dict(pending_member=["channel-group 11 force mode active", "shutdown"]), False, "unmodeled command"),
    ("unauthorized no shutdown", lambda m, l: dict(pending_member=["channel-group 10 force mode active", "no shutdown"]), False, "unexpected removal"),
    (
        "member trunk line kept",
        lambda m, l: dict(pending_member=["channel-group 10 force mode active", "shutdown", "switchport trunk allowed vlan 2301"]),
        False,
        "unmodeled command",
    ),
    ("pending outside the resource", lambda m, l: dict(extra=["interface ethernet1/8", "  shutdown"]), False, "ethernet1/8"),
]


NEGATIVE_CASES = [(m,) + n for m in MODES for n in NEGATIVE if not (n[2] and m == "promiscuous")]  # no trunk lines in P


@pytest.mark.parametrize("mode, label, change, trunk_only, needle", NEGATIVE_CASES, ids=["%s-%s" % (n[0], n[1]) for n in NEGATIVE_CASES])
def test_each_single_change_to_the_synthetic_creation_preview_is_refused_before_deploy(mode, label, change, trunk_only, needle):
    _profile, lines = CASES[mode]
    ctrl, status, result = create(mode, pv=creation_preview(mode, lines, **change(mode, lines)))
    assert status == "fail" and needle in result["msg"].lower(), (label, result.get("msg"))
    assert "Ethernet1/7" in result["msg"] or needle == "ethernet1/8", "the member is the refused target"
    assert len(ctrl.creates()) == 1 and ctrl.deploys() == [], label


def test_trunk_secondary_creation_with_a_community_secondary_for_the_second_primary_is_refused_before_any_write():
    ctrl = new_ctrl("trunk secondary")
    ctrl.networks.append(
        dict(
            copy.deepcopy([n for n in ctrl.networks if n["type"] == "Community"][0]),
            networkId=30411,
            networkName="SYN_COMMUNITY_2411",
            primaryNetworkId=30410,
            networkTemplateConfig='{"type":"Community","vlanId":"2411","networkMode":"layer2","isLayer2Only":"true","vrfName":"NA"}',
        )
    )
    profile = copy.deepcopy(CASES["trunk secondary"][0])
    profile["pvlan_association"] = [{"primary_vlan": 2210, "secondary_vlan": 2212}, {"primary_vlan": 2410, "secondary_vlan": 2411}]
    status, result = run(ctrl, [item("trunk secondary", **profile)], state="replaced")
    assert status == "fail" and "2411 is a community VLAN" in result["msg"] and ctrl.writes() == []


# ------------------------------------------------------------------ merged preserves native/allowed, member and the current list
MERGED = {
    "trunk promiscuous": (
        {"pvlan_mapping": [{"primary_vlan": 2410, "secondary_vlans": "2411-2412"}]},  # Alpha2 TP2
        ["switchport private-vlan mapping trunk 2410 2411"],
        [(2210, 2211), (2210, 2212), (2410, 2411), (2410, 2412)],
        "MAPPING_LIST",
    ),
    "trunk secondary": (
        {"pvlan_association": [{"primary_vlan": 2510, "secondary_vlan": 2512}]},  # Alpha3 TS2 form, third primary
        ["switchport private-vlan association trunk 2510 2512"],
        [(2210, 2212), (2410, 2412), (2510, 2512)],
        "ASSOCIATION_LIST",
    ),
}


@pytest.mark.parametrize("mode", sorted(MERGED))
def test_merged_list_addition_keeps_native_allowed_member_and_current_pairs(mode):
    profile, lines = CASES[mode]
    add, new_lines, pairs, key = MERGED[mode]
    ctrl = existing(mode)
    if mode == "trunk secondary":
        nets = ctrl.networks
        for vlan, kind, pid, nid in ((2510, "Primary", -1, 30510), (2512, "Isolated", 30510, 30512)):
            src = copy.deepcopy([n for n in nets if n["type"] == kind][0])
            old = "2210" if kind == "Primary" else "2212"
            nets.append(
                dict(
                    src,
                    networkId=nid,
                    networkName="SYN_%d" % vlan,
                    primaryNetworkId=pid,
                    networkTemplateConfig=src["networkTemplateConfig"].replace(old, str(vlan)),
                )
            )
    have = copy.deepcopy(ctrl.detail[PO]["nvPairs"])
    full = lines + new_lines + (["switchport private-vlan mapping trunk 2410 2412"] if mode == "trunk promiscuous" else [])
    pend = ["interface port-channel10"] + ["  " + l for l in new_lines] + ["interface Ethernet1/7"] + ["  " + l for l in new_lines]
    ctrl.previews = [preview(pend, running=po_stanza(mode, lines) + member_stanza(mode, lines), expected=po_stanza(mode, full) + member_stanza(mode, full))]
    it = {"name": PO_ITEM_NAME, "type": "pc", "switch": [SWITCH_IP], "deploy": True, "profile": dict({"mode": "pvlan", "pvlan_mode": mode}, **add)}
    status, result = run(ctrl, [it], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.creates() == [] and len(ctrl.bulk_bodies()) == 1 and len(ctrl.deploys()) == 1
    sent = ctrl.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]
    assert P.pairs_from_wire(sent[key], key) == pairs
    for k in ("PVLAN_NATIVE_VLAN", "PVLAN_ALLOWED_VLANS", "MEMBER_INTERFACES", "ADMIN_STATE", "PC_MODE", "DESC"):
        assert sent[k] == have[k], k
    assert result["diff"][0]["merged"][0]["interfaces"][0]["nvPairs"] == {key: sent[key]}


# ------------------------------------------------------------------ deletion: G4-R1 outcome contract in the other modes
@pytest.mark.parametrize("mode", MODES)
def test_an_unverified_markdelete_of_a_port_channel_in_another_mode_stops_after_one_delete(mode):
    _profile, lines = CASES[mode]
    ctrl = existing(mode)
    real = ctrl.__class__.__call__

    def transport(mod, method, path, data=None):
        if method == "DELETE" and path.endswith("/rest/interface/markdelete"):
            real(ctrl, mod, method, path, data)  # the deletion is APPLIED, the answer is not the measured one
            return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": []}
        return real(ctrl, mod, method, path, data)

    ctrl.previews = [delete_preview(mode, lines)]
    status, result = run(transport, [del_item()], state="deleted")
    assert status == "fail" and "outcome UNVERIFIED; not retried" in result["msg"], result.get("msg")
    assert len(ctrl.markdeletes()) == 1 and ctrl.bulk_bodies() == [] and ctrl.deploys() == []
    assert not any("/config-preview" in c[1] for c in ctrl.calls)


@pytest.mark.parametrize("mode", MODES)
def test_a_confirmed_markdelete_of_a_port_channel_in_another_mode_releases_and_deploys(mode):
    _profile, lines = CASES[mode]
    ctrl = existing(mode)
    ctrl.previews = [delete_preview(mode, lines)]
    status, result = run(ctrl, [del_item()], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.markdeletes()) == 1 and len(ctrl.deploys()) == 1
    assert PO not in ctrl.detail and ctrl.detail[IF7]["policy"] == TRUNK and PO_HOST not in json.dumps(ctrl.detail[IF7])


# ================================================================== live host findings during G5 (Alpha4 G4R1 run)
# MEASURED (fixtures/pvlan_po_g4r1_host_measured.json, extracted read-only from Alpha4's G4R1 live captures by
# runtime/g5/extract_g4r1_fixture.py; only port-channel502 / Ethernet1/10): H4 (host association 2210/2212 -> 2410/2412 on a
# deployed Po: member pending EMPTY) and the R-B deletion of that DEPLOYED Po (Po listed as interface_delete until the
# deploy; member withdrawn with `no channel-group 502 force mode active`; released member ADMIN_STATE "true").
# SIMULATED: the networks 2410/2412 typing, the legacy modify answer, and the post-correction deletion preview (named below).
G4R1 = json.load(open(os.path.join(os.path.dirname(__file__), "fixtures", "pvlan_po_g4r1_host_measured.json")))
PO_NAME_502, PO_502, MEM_10 = "port-channel502", "Port-channel502", "Ethernet1/10"


def g4r1_stage(name):
    return copy.deepcopy(G4R1["stages"][name])


def g4r1_entry(name, pending=None, expected=None, running=None):
    pf = g4r1_stage(name)["preview_forced"]
    return preview(
        pending if pending is not None else pf["pendingConfig"],
        running=running if running is not None else pf["runningConfig_stanzas"],
        expected=expected if expected is not None else pf["expectedConfig_stanzas"],
    )["DATA"][0]


def h4_parts(e):
    po_nv = g4r1_stage("H4-post")["intent"][PO_NAME_502]["nvPairs"]
    mem_pre_nv = g4r1_stage("H4-pre")["intent"][MEM_10]["nvPairs"]
    post = (PO_MEMBER, P.po_member_nvpairs(po_nv, mem_pre_nv, current_is_member=True))
    body = P.split_blocks(e["pendingConfig"])[0].get(MEM_10.lower(), [])
    return body, post, P.transition_vocabulary((PO_MEMBER, mem_pre_nv), post)


def test_g4r1_fixture_is_the_gate_input_of_h4():
    assert G4R1["h4_gate_pending_equals_h4_post"] is True and G4R1["h4_gate_previews"] == 1
    body, _post, _v = h4_parts(g4r1_entry("H4-post"))
    assert body == [], "MEASURED: no member pending on a host association update"


def test_h4_measured_member_without_pending_is_inherited_only_through_its_port_channel():
    e = g4r1_entry("H4-post")
    body, post, vocab = h4_parts(e)
    desired = P.render(*post)
    assert P.assess_target(body, e, MEM_10, desired, vocab, member_inherit=PO_NAME_502) == ("deploy", [])
    decision, problems = P.assess_target(body, e, MEM_10, desired, vocab)
    assert decision == "refuse" and "the pending for Ethernet1/10 is empty but the device differs" in problems[0], "G4R1 = live H4"


@pytest.mark.parametrize(
    "label, change, needle",
    [
        (
            "member diverged from its port-channel",
            lambda pf: dict(
                running=[
                    "  switchport private-vlan host-association 2210 2211" if l == "  switchport private-vlan host-association 2210 2212" and i < 7 else l
                    for i, l in enumerate(pf["runningConfig_stanzas"])
                ]
            ),
            "is empty but the device differs",
        ),
        (
            "expected member keeps the old pair",
            lambda pf: dict(expected=[l.replace("2410 2412", "2210 2212") if i < 7 else l for i, l in enumerate(pf["expectedConfig_stanzas"])]),
            "disagrees with the intended state",
        ),
        (
            "foreign member line",
            lambda pf: dict(pending=pf["pendingConfig"][:-1] + ["interface ethernet1/10", "  speed 1000", "configure terminal"]),
            "unmodeled command",
        ),
        (
            "member no shutdown",
            lambda pf: dict(pending=pf["pendingConfig"][:-1] + ["interface ethernet1/10", "  no shutdown", "configure terminal"]),
            "unexpected removal",
        ),
    ],
)
def test_h4_inheritance_does_not_hide_a_member_difference(label, change, needle):
    e = g4r1_entry("H4-post", **change(g4r1_stage("H4-post")["preview_forced"]))
    body, post, vocab = h4_parts(e)
    decision, problems = P.assess_target(body, e, MEM_10, P.render(*post), vocab, member_inherit=PO_NAME_502)
    assert decision == "refuse" and any(needle in p for p in problems), (label, problems)


def h4_ctrl():
    ctrl = with_second_primary(PoLifecycleController())
    for name, key in ((PO_502, PO_NAME_502), (MEM_10, MEM_10)):
        nv = dict((k, v) for k, v in g4r1_stage("H4-pre")["intent"][key]["nvPairs"].items() if k != "POLICY_ID")
        ctrl.detail[name] = {"policy": g4r1_stage("H4-pre")["intent"][key]["policy"], "nvPairs": nv}
    ctrl.po_names.add(PO_502)
    return ctrl


H4_ITEM = {
    "name": "po502",
    "type": "pc",
    "switch": [SWITCH_IP],
    "deploy": True,
    "profile": {
        "mode": "pvlan",
        "pvlan_mode": "host",
        "members": [MEM_10],
        "pc_mode": "active",
        "admin_state": False,
        "description": "PR725-POH-DESC-1",
        "pvlan_association": [{"primary_vlan": 2410, "secondary_vlan": 2412}],
    },
}  # Alpha4 models/POH4_replaced_2410_2412.yml


def test_main_h4_replay_with_the_measured_preview_modifies_and_deploys():
    ctrl = h4_ctrl()
    ctrl.previews = [{"RETURN_CODE": 200, "DATA": [g4r1_entry("H4-post")]}]
    status, result = run(ctrl, [H4_ITEM], state="replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.bulk_bodies()) == 1 and len(ctrl.deploys()) == 1 and ctrl.creates() == []
    sent = ctrl.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]
    assert P.pairs_from_wire(sent["ASSOCIATION_LIST"], "ASSOCIATION_LIST") == [(2410, 2412)] and sent["DESC"] == "PR725-POH-DESC-1"
    assert result["pvlan_gate"][0]["targets"][PO_502] == "deploy"


class DeployedReleaseController(PoLifecycleController):
    """The g1 lifecycle harness + the MEASURED release of a DEPLOYED port-channel (G4R1 R-B): after the mark-delete the
    Po's detail is empty, its summary entry stays (markDeleted, NA, interface_delete) and the policy list holds the
    interface_delete (deleted true) until the deploy; the member is the measured released int_trunk_host (ADMIN "true")."""

    def __init__(self, marked_entry=None):
        super(DeployedReleaseController, self).__init__()
        self.release_member = False
        po_summary = [x for x in g4r1_stage("HR-post")["summary"] if x["ifName"] == PO_502][0]
        po_summary["serialNo"] = SERIAL
        po_summary["underlayPolicies"][0]["serialNumber"] = SERIAL
        po_summary.update(marked_entry or {})
        self.marked_template = po_summary
        self.marked = None
        self.released = dict((k, v) for k, v in g4r1_stage("HR-post")["intent"][MEM_10]["nvPairs"].items() if k != "POLICY_ID")

    def __call__(self, mod, method, path, data=None):
        if method == "DELETE" and path.endswith("/rest/interface/markdelete"):
            resp = super(DeployedReleaseController, self).__call__(mod, method, path, data)
            self.detail[MEM_10] = {"policy": TRUNK, "nvPairs": copy.deepcopy(self.released)}
            self.marked = copy.deepcopy(self.marked_template)
            self.policies_extra = [dict(p, serialNumber=SERIAL) for p in g4r1_stage("HR-post")["policies"] if p["templateName"] == "interface_delete"]
            return resp
        resp = super(DeployedReleaseController, self).__call__(mod, method, path, data)
        if method == "POST" and path.endswith("/rest/globalInterface/deploy"):
            self.marked, self.policies_extra = None, []  # the deploy completes the deletion (NOT measured for a deployed Po)
        return resp

    def _summary_list(self):
        return super(DeployedReleaseController, self)._summary_list() + ([copy.deepcopy(self.marked)] if self.marked else [])

    def modifies(self):
        return [c for c in self.calls if c[0] == "POST" and c[1].endswith("/rest/interface/modify")]


def hr_ctrl(previews, **marked):
    ctrl = DeployedReleaseController(marked or None)
    for name, key in ((PO_502, PO_NAME_502), (MEM_10, MEM_10)):
        nv = dict((k, v) for k, v in g4r1_stage("HR-pre")["intent"][key]["nvPairs"].items() if k != "POLICY_ID")
        ctrl.detail[name] = {"policy": g4r1_stage("HR-pre")["intent"][key]["policy"], "nvPairs": nv}
    ctrl.po_names.add(PO_502)
    ctrl.previews = previews
    return ctrl


def corrected_hr_preview():
    """SYNTHETIC, one named change of the MEASURED HR-post entry: the member corrected to ADMIN_STATE false, so the
    controller's expected member holds `shutdown` and the pending no longer carries `no shutdown` (the post-correction
    pending of a DEPLOYED Po is NOT measured; for the never-deployed Po the measured correction gave In-Sync)."""
    pf = g4r1_stage("HR-post")["preview_forced"]
    pending = [l for l in pf["pendingConfig"] if l != "  no shutdown"]
    expected = ["  shutdown" if l == "  no shutdown" else l for l in pf["expectedConfig_stanzas"]]
    return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [g4r1_entry("HR-post", pending=pending, expected=expected)]}


def hr_delete(ctrl):
    return run(ctrl, [{"name": "po502", "switch": [SWITCH_IP], "deploy": True}], state="deleted")


def test_marked_deleted_listing_is_only_the_measured_form():
    entry = [x for x in g4r1_stage("HR-post")["summary"] if x["ifName"] == PO_502][0]
    assert P.po_marked_deleted_problem(entry, PO_502) is None
    assert "not marked for deletion" in P.po_marked_deleted_problem(dict(entry, markDeleted=False), PO_502)
    other = copy.deepcopy(entry)
    other["underlayPolicies"][0]["templateName"] = P.PO_HOST_POLICY
    assert "not the controller's interface_delete" in P.po_marked_deleted_problem(other, PO_502)
    assert "source" in P.po_marked_deleted_problem(dict(entry, underlayPolicies=[dict(entry["underlayPolicies"][0], source="port-channel503")]), PO_502)


def test_main_deployed_port_channel_deletion_corrects_the_member_and_deploys_with_the_corrected_preview():
    ctrl = hr_ctrl([corrected_hr_preview()])
    status, result = hr_delete(ctrl)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.markdeletes()) == 1 and len(ctrl.modifies()) == 1 and len(ctrl.deploys()) == 1
    sent = json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]
    assert sent["ADMIN_STATE"] == "false" and dict(sent, ADMIN_STATE="true") == dict((k, v) for k, v in ctrl.released.items() if k not in P.PO_RELEASE_METADATA)
    assert PO_502 not in ctrl.detail and ctrl.detail[MEM_10]["nvPairs"]["ADMIN_STATE"] == "false"


def test_main_deployed_deletion_with_the_measured_admin_up_preview_never_deploys():
    ctrl = hr_ctrl([{"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [g4r1_entry("HR-post")]}])
    status, result = hr_delete(ctrl)
    assert status == "fail" and "'no shutdown'" in result["msg"], result.get("msg")
    assert len(ctrl.markdeletes()) == 1 and len(ctrl.modifies()) == 1 and ctrl.deploys() == []


def test_main_deployed_deletion_still_listed_in_another_form_stops_before_any_member_write():
    ctrl = hr_ctrl([corrected_hr_preview()], markDeleted=False)
    status, result = hr_delete(ctrl)
    assert status == "fail" and "the port-channel is still listed: it is listed and not marked for deletion" in result["msg"], result.get("msg")
    assert len(ctrl.markdeletes()) == 1 and ctrl.modifies() == [] and ctrl.deploys() == []


def test_main_deployed_deletion_with_a_foreign_membership_withdrawal_is_refused():
    pv = corrected_hr_preview()
    e = pv["DATA"][0]
    e["pendingConfig"] = [l.replace("channel-group 502 force", "channel-group 503 force") for l in e["pendingConfig"]]
    ctrl = hr_ctrl([pv])
    status, result = hr_delete(ctrl)
    assert status == "fail" and "channel-group 503 force mode active" in result["msg"] and ctrl.deploys() == [], result.get("msg")
