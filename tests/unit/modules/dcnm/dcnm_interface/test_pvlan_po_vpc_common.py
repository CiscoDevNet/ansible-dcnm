"""Port-channel and vPC PVLAN: text commands, patch_version coexistence and overridden reconciliation."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import jinja2
import json
import pytest
import yaml

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import registered_profile_keys
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_ENABLED_PATCH_VERSIONS

from .helpers import vpc_controller as V
from .helpers.ethernet_controller import SWITCH_IP
from .helpers.ethernet_controller import preview
from .helpers.ethernet_controller import run
from .helpers.port_channel_controller import created
from .helpers.port_channel_controller import po_stanza
from .helpers.port_channel_controller import member_stanza
from .helpers.port_channel_controller import PO_ITEM_NAME
from .helpers.port_channel_controller import ASSOC
from .helpers.port_channel_controller import FF_A
from .helpers.port_channel_controller import FF_B
from .helpers.port_channel_controller import HOST_LINES
from .helpers.port_channel_controller import created_with
from .helpers.ethernet_controller import IF7
from .helpers.ethernet_controller import IF8
from .helpers.ethernet_controller import PREVIEW_MARK
from .helpers.ethernet_controller import TRUNK
from .helpers.ethernet_controller import trunk_host_nv
from .helpers.ethernet_controller import trunk_item
from .helpers.port_channel_controller import del_item
from .helpers.port_channel_controller import delete_preview
from .helpers.port_channel_controller import item as po_item
from .helpers.port_channel_controller import CASES
from .helpers.port_channel_controller import MEM_10
from .helpers.port_channel_controller import MODES
from .helpers.port_channel_controller import corrected_hr_preview
from .helpers.port_channel_controller import creation_preview
from .helpers.port_channel_controller import existing
from .helpers.port_channel_controller import hr_ctrl
from .helpers.port_channel_controller import hr_delete
from .helpers.port_channel_controller import new_ctrl
from .helpers.port_channel_controller import PO
from .helpers.vpc_controller import run_vpc
from .helpers.vpc_modes import P_
from .helpers.vpc_modes import TP
from .helpers.vpc_modes import TS
from .helpers.vpc_modes import baseline_ctrl
from .helpers.vpc_modes import converged_previews
from .helpers.vpc_modes import create_previews
from .helpers.vpc_modes import seeded_ctrl
from .helpers.vpc_modes import item as vpc_item
from .helpers import ethernet_controller as HH
from .helpers import membership as MU
from .helpers import port_channel_release as G4
from .helpers.vpc_controller import MeasuredVpc
from .helpers.vpc_controller import lo
from .helpers.vpc_controller import measured_po
from .helpers.vpc_controller import vpc_ctrl
from .helpers.vpc_controller import vpc_queue
from .helpers.vpc_controller import with_args
from .helpers.vpc_controller import writes
from .helpers.fixture_cases import load_case
from .helpers import port_channel_controller as G5


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_po_vpc_cmds_text.py
# PVLAN port-channel `cmds` and vPC `peer1_cmds` / `peer2_cmds` given as text, as NaC renders `freeform_config` for port-channels
# (`cmds: |2-` + `interface['freeform_config'] | default('')`) and vPCs (`peerN_cmds: |2-` + `switches[peerN].freeform_config | default('')`).
#
# Real main() through the existing port-channel / vPC harnesses; the generic NaC fragments are rendered with Jinja2 and parsed as YAML
# (the colleague's own PVLAN renderer is not known). Synthetic freeform commands; NOT LIVE TESTED.
# ====================================================================================================
PO_FRAGMENT = "profile:\n    cmds: |2-\n      {{ interface['freeform_config'] | default('') | indent(6, false) }}\n"
VPC_FRAGMENT = ("profile:\n    peer1_cmds: |2-\n      {{ switches[peer1].freeform_config | default('') | indent(6, false) }}\n"
                "    peer2_cmds: |2-\n      {{ switches[peer2].freeform_config | default('') | indent(6, false)  }}\n")


def nac_po_cmds(**interface):
    return yaml.safe_load(jinja2.Environment().from_string(PO_FRAGMENT).render(interface=interface))["profile"]["cmds"]


def nac_vpc_cmds(peer1=None, peer2=None):
    switches = {"a": {} if peer1 is None else {"freeform_config": peer1}, "b": {} if peer2 is None else {"freeform_config": peer2}}
    prof = yaml.safe_load(jinja2.Environment().from_string(VPC_FRAGMENT).render(switches=switches, peer1="a", peer2="b"))["profile"]
    return prof["peer1_cmds"], prof["peer2_cmds"]


def po_cfg(deploy=True, **profile):
    prof = {"mode": "pvlan", "pvlan_mode": "host"}
    prof.update(profile)
    return {"name": PO_ITEM_NAME, "type": "pc", "switch": [SWITCH_IP], "deploy": deploy, "profile": prof}


def sent_po_conf(ctrl):
    return ctrl.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]["CONF"]


# ------------------------------------------------------------------ the renderer boundary
def test_t_nac_fragments_render_text_for_port_channel_and_both_vpc_peers():
    assert nac_po_cmds(freeform_config=FF_A) == FF_A
    assert nac_po_cmds() == "" and nac_po_cmds(freeform_config="") == ""
    assert nac_po_cmds(freeform_config=FF_A + "\n" + FF_B) == FF_A + "\n" + FF_B
    assert nac_vpc_cmds(FF_A, FF_B) == (FF_A, FF_B)
    assert nac_vpc_cmds(FF_A, None) == (FF_A, ""), "an omitted peer freeform renders as ''"


# ------------------------------------------------------------------ port-channel through main()
@pytest.mark.parametrize("cmds, conf", [
    (FF_A, FF_A),
    (FF_A + "\r\n" + FF_B, FF_A + "\n" + FF_B),
    ([FF_A + "\n" + FF_B], FF_A + "\n" + FF_B),
], ids=["text", "text-crlf", "list-entry-with-line-break"])
def test_t_po_creation_with_text_sends_the_lines_as_conf(cmds, conf):
    lines = conf.split("\n")
    _ctrl, result = created_with(lines, [], cmds=cmds)
    nv = result["created_nv"]
    assert nv["CONF"] == conf and nv["PVLAN_MODE"] == "host"


def test_t_po_text_and_list_create_identical_payloads():
    _c, by_text = created_with([FF_A], [], cmds=nac_po_cmds(freeform_config=FF_A))
    _c, by_list = created_with([FF_A], [], cmds=[FF_A])
    assert by_text["created_nv"] == by_list["created_nv"]


def test_t_po_merged_text_update_deploys_and_the_repeat_writes_nothing():
    ctrl = created("host", HOST_LINES, pvlan_association=ASSOC)
    old_po, old_m = po_stanza("host", HOST_LINES), member_stanza("host", HOST_LINES)
    ctrl.previews = [preview(["interface port-channel10", "  " + FF_A], running=old_po + old_m, expected=old_po + ["  " + FF_A] + old_m)]
    status, result = run(ctrl, [po_cfg(cmds=nac_po_cmds(freeform_config=FF_A))], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert sent_po_conf(ctrl) == FF_A
    assert result["diff"][0]["merged"][0]["interfaces"][0]["nvPairs"] == {"CONF": FF_A}
    ctrl.next_invocation()
    ctrl.calls = []
    status, result = run(ctrl, [po_cfg(cmds=FF_A + "\n")], state="merged")
    assert status == "exit" and result["changed"] is False, result
    assert ctrl.writes() == [] and ctrl.deploys() == []


def test_t_po_merged_text_appends_only_new_lines_in_order_without_duplicates():
    ctrl, _r = created_with([FF_A], [], cmds=[FF_A])
    status, result = run(ctrl, [po_cfg(deploy=False, cmds=FF_B + "\n" + FF_A + "\n" + FF_B)], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert sent_po_conf(ctrl) == FF_A + "\n" + FF_B


@pytest.mark.parametrize("cmds", ["", None], ids=["nac-omitted-empty-text", "absent-key"])
def test_t_po_merged_omitted_or_empty_text_keeps_the_stored_commands(cmds):
    ctrl, _r = created_with([FF_A], [], cmds=[FF_A])
    profile = {} if cmds is None else {"cmds": cmds}
    status, result = run(ctrl, [po_cfg(deploy=False, **profile)], state="merged")
    assert status == "exit" and result["changed"] is False, result
    assert ctrl.writes() == []


def test_t_po_merged_other_change_with_nac_empty_text_sends_the_stored_conf_bytes():
    ctrl, _r = created_with([FF_A], [], cmds=[FF_A])
    status, result = run(ctrl, [po_cfg(deploy=False, description="D1", cmds=nac_po_cmds())], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert sent_po_conf(ctrl) == FF_A, "exact stored bytes: no blank line appended for the empty text"
    assert result["diff"][0]["merged"][0]["interfaces"][0]["nvPairs"] == {"DESC": "D1"}


def test_t_po_replaced_empty_text_is_the_authoritative_reset():
    ctrl, _r = created_with([FF_A], [], cmds=[FF_A])
    status, result = run(ctrl, [po_cfg(deploy=False, members=["Ethernet1/7"], admin_state=False, pvlan_association=ASSOC, cmds="")],
                         state="replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert sent_po_conf(ctrl) == ""


@pytest.mark.parametrize("cmds, needle", [
    (FF_A + "\nswitchport mode trunk", "copies to every member"),
    ([FF_A + "\nmtu 1500"], "copies to every member"),
    (FF_A + "\n  sgt 10", "indented sub-command"),
    ([FF_A, "interface Ethernet1/9"], "'interface' command"),
    (FF_A + "\n\n" + FF_B, "is empty"),
    ("logging event port link-status, trunk-status", "must not contain a comma"),
    (5, "list of strings"),
    ([FF_A, 5], "list of strings"),
], ids=["text-line2-switchport", "list-entry-line2-inherited", "text-indented-block", "list-identity", "text-blank-line", "comma-text",
        "int", "mixed-list"])
def test_t_po_refusals_reach_main_before_any_request_and_never_echo_the_command(cmds, needle):
    ctrl = created("host", HOST_LINES, pvlan_association=ASSOC)
    ctrl.next_invocation()
    ctrl.calls = []
    status, result = run(ctrl, [po_cfg(cmds=cmds)], state="merged")
    assert status == "fail" and needle in result["msg"] and "No change was sent" in result["msg"], result.get("msg")
    assert ctrl.writes() == [] and ctrl.deploys() == []
    assert "link-status" not in result["msg"] and "sgt 10" not in result["msg"]


def test_t_a_valid_earlier_target_is_not_written_when_a_later_freeform_is_invalid():
    ctrl = created("host", HOST_LINES, pvlan_association=ASSOC)
    ctrl.next_invocation()
    ctrl.calls = []
    valid = {"name": "Ethernet1/8", "type": "eth", "switch": [SWITCH_IP], "deploy": False,
             "profile": {"mode": "trunk", "description": "valid earlier target"}}
    status, result = run(ctrl, [valid, po_cfg(cmds=FF_A + "\nswitchport mode trunk")], state="merged")
    assert status == "fail" and "copies to every member" in result["msg"], result.get("msg")
    assert ctrl.writes() == [] and ctrl.deploys() == []


def test_t_po_text_never_reaches_the_payload_as_characters():
    _c, result = created_with([FF_A], [], cmds=FF_A)
    assert result["created_nv"]["CONF"] == FF_A and "\n".join(FF_A) != result["created_nv"]["CONF"]


# ------------------------------------------------------------------ vPC through main()
def _vpc_ff_preview(serial, port, conf_lines):
    po = V.po_stanza() + ["  " + c for c in conf_lines]
    pend = ["interface port-channel10"] + ["  " + c for c in conf_lines]
    return preview(pend, serial=serial, running=V.po_stanza() + V.member_after(port), expected=po + V.member_after(port))


def _vpc_settled(serial, port, conf_lines):
    full = V.po_stanza() + ["  " + c for c in conf_lines] + V.member_after(port)
    return V.preview([], serial=serial, running=full, expected=full)


@pytest.mark.parametrize("peer1, peer2, conf1, conf2", [
    (FF_A, FF_B, FF_A, FF_B),
    (FF_A + "\r\n" + FF_B, FF_B + "\n" + FF_A, FF_A + "\n" + FF_B, FF_B + "\n" + FF_A),
], ids=["text", "multiline-crlf"])
def test_t_vpc_both_peers_text_maps_each_peer_and_the_repeat_writes_nothing(peer1, peer2, conf1, conf2):
    p1, p2 = nac_vpc_cmds(peer1, peer2)
    ctrl = V.created_ctrl()
    ctrl.vpc_previews[V.SN1] = [V.converged_preview(V.SN1, V.M1), _vpc_ff_preview(V.SN1, V.M1, conf1.split("\n"))]
    ctrl.vpc_previews[V.SN2] = [V.converged_preview(V.SN2, V.M2), _vpc_ff_preview(V.SN2, V.M2, conf2.split("\n"))]
    status, result = V.run_vpc(ctrl, [V.vpc_item(peer1_cmds=p1, peer2_cmds=p2)], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    sent = json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]
    assert (sent["PEER1_PO_CONF"], sent["PEER2_PO_CONF"]) == (conf1, conf2)
    assert ctrl.deploys()
    ctrl.next_invocation()
    ctrl.vpc_previews[V.SN1] = [_vpc_settled(V.SN1, V.M1, conf1.split("\n"))]
    ctrl.vpc_previews[V.SN2] = [_vpc_settled(V.SN2, V.M2, conf2.split("\n"))]
    before = len(ctrl.writes())
    status, result = V.run_vpc(ctrl, [V.vpc_item(peer1_cmds=p1, peer2_cmds=p2)], state="merged")
    assert status == "exit" and result["changed"] is False, result
    assert len(ctrl.writes()) == before


def test_t_vpc_text_and_list_send_identical_peer_conf():
    sent = []
    for p1, p2 in ((FF_A, FF_B), ([FF_A], [FF_B])):
        ctrl = V.created_ctrl()
        ctrl.vpc_previews[V.SN1] = [V.converged_preview(V.SN1, V.M1), _vpc_ff_preview(V.SN1, V.M1, [FF_A])]
        ctrl.vpc_previews[V.SN2] = [V.converged_preview(V.SN2, V.M2), _vpc_ff_preview(V.SN2, V.M2, [FF_B])]
        status, result = V.run_vpc(ctrl, [V.vpc_item(peer1_cmds=p1, peer2_cmds=p2)], state="merged")
        assert status == "exit", result.get("msg")
        sent.append(json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"])
    assert sent[0] == sent[1]


def test_t_vpc_nac_render_with_one_peer_freeform_stays_a_refused_one_peer_update():
    p1, p2 = nac_vpc_cmds(FF_A, None)  # peer2's freeform omitted -> ''
    ctrl = V.created_ctrl()
    status, result = V.run_vpc(ctrl, [V.vpc_item(peer1_cmds=p1, peer2_cmds=p2)], state="merged")
    assert status == "fail" and "changes only peer 1" in result["msg"] and "PEER1_PO_CONF" in result["msg"], result.get("msg")
    assert ctrl.writes() == []


def test_t_vpc_both_peers_omitted_render_is_a_no_write():
    p1, p2 = nac_vpc_cmds(None, None)
    assert (p1, p2) == ("", "")
    ctrl = V.created_ctrl()
    ctrl.vpc_previews[V.SN1] = [V.converged_preview(V.SN1, V.M1)]  # the vPC preflight reads the current state first
    ctrl.vpc_previews[V.SN2] = [V.converged_preview(V.SN2, V.M2)]
    status, result = V.run_vpc(ctrl, [V.vpc_item(peer1_cmds=p1, peer2_cmds=p2)], state="merged")
    assert status == "exit" and result["changed"] is False, result
    assert ctrl.writes() == []


@pytest.mark.parametrize("p1, needle", [
    (FF_A + "\nvpc orphan-port suspend", "'vpc' command"),
    ([FF_A + "\n  sgt 10"], "indented sub-command"),
    ("a, b", "must not contain a comma"),
], ids=["text-line2-vpc", "list-entry-indented", "comma-text"])
def test_t_vpc_refusals_reach_main_before_any_request(p1, needle):
    ctrl = V.created_ctrl()
    status, result = V.run_vpc(ctrl, [V.vpc_item(peer1_cmds=p1, peer2_cmds=FF_B)], state="merged")
    assert status == "fail" and needle in result["msg"], result.get("msg")
    assert ctrl.writes() == []


# ------------------------------------------------------------------ helper pins (defensive; the module result is covered above)
def test_t_freeform_request_and_merge_never_add_a_blank_line_or_characters():
    from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P
    assert P.freeform_request("") == [] and P.freeform_request([""]) == [] and P.freeform_request(None) == []
    assert P.freeform_request(FF_A) == [FF_A]
    assert P.freeform_merged(FF_A, [""]) == FF_A and P.freeform_merged(FF_A, "") == FF_A
    with pytest.raises(P.PvlanError):
        P.freeform_request("a, b")


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_po_vpc_patch_version_coexistence.py
# Coexistence of the regular port-channel and vPC PVLAN routes with the caller-supplied patch_version gate.
#
# The port-channel (int_port_channel_pvlan_host) and vPC (int_vpc_pvlan_host) PVLAN builders return their own
# template payload before the engine contribution that the other port-channel/vPC modes reach. That is equivalent to
# an empty contribution only because no registry binding exists for any PVLAN policy; the first test pins that
# precondition. The rest drive the real main() through the existing Po/vPC harnesses and compare the ordered request
# log (method, path, body) of a run without patch_version against runs with the approved and an unapproved value.
#
# SIMULATED: every controller answer and preview comes from the existing harness builders. No controller is contacted.
# ====================================================================================================
APPROVED = sorted(GIE_ENABLED_PATCH_VERSIONS)[0]
PATCH_VALUES = [
    pytest.param(APPROVED, id="approved"),
    pytest.param("4.4.1", id="nd_release"),
    pytest.param("4.3.1.0175006010", id="unapproved"),
]


def _log(c):
    return [(m, p, json.loads(b) if isinstance(b, str) else b) for m, p, b in c.calls]


def test_port_channel_and_vpc_pvlan_policies_register_only_the_c1_companions():
    """The parents register exactly their REGISTRY_BINDING companions; the member and the vPC child register
    nothing (they are written by the parent template). A run that sets none of them is unchanged by the patch value (below)."""
    assert registered_profile_keys(P.PO_HOST_POLICY) == {"disable_lldp_transmit", "disable_lldp_receive", "spanning_tree_port_type", "disable_queuing_stats"}
    assert registered_profile_keys(P.VPC_HOST_POLICY) == {
        "disable_lldp_transmit",
        "disable_lldp_receive",
        "spanning_tree_port_type",
        "disable_queuing_stats",
        "acl_filter",
        "disable_qos_stats",  # ingress QoS
    }
    for policy in (P.PO_MEMBER_POLICY, P.VPC_PO_POLICY):
        assert registered_profile_keys(policy) == set(), policy


# ------------------------------------------------------------------ regular port-channel
def _po_create(mode, patch_version=None):
    profile, lines = CASES[mode]
    c = new_ctrl(mode)
    c.previews = [creation_preview(mode, lines)]
    status, result = run(c, [po_item(mode, **profile)], state="replaced", patch_version=patch_version)
    return c, status, result


@pytest.mark.parametrize("patch_version", PATCH_VALUES)
@pytest.mark.parametrize("mode", MODES)
def test_po_pvlan_creation_sends_the_same_requests_for_any_patch_value(mode, patch_version):
    reference, status, result = _po_create(mode)
    assert status == "exit", result.get("msg")
    c, status, result = _po_create(mode, patch_version)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert _log(c) == _log(reference)
    assert "PATCH_VERSION" not in json.dumps(_log(c)).upper()


@pytest.mark.parametrize("patch_version", PATCH_VALUES)
def test_po_pvlan_deletion_sends_the_same_requests_for_any_patch_value(patch_version):
    mode = "promiscuous"
    _profile, lines = CASES[mode]
    reference = existing(mode)
    reference.previews = [delete_preview(mode, lines)]
    assert run(reference, [del_item()], state="deleted")[0] == "exit"
    c = existing(mode)
    c.previews = [delete_preview(mode, lines)]
    status, result = run(c, [del_item()], state="deleted", patch_version=patch_version)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert _log(c) == _log(reference)
    assert PO not in c.detail and c.detail[IF7]["policy"] == TRUNK


@pytest.mark.parametrize("patch_version", PATCH_VALUES)
def test_deployed_po_deletion_still_releases_the_member_administratively_down_for_any_patch_value(patch_version):
    """The measured release leaves the member admin-up; the module's correction to ADMIN_STATE false must be the only
    member write and must not depend on the patch context."""
    reference = hr_ctrl([corrected_hr_preview()])
    assert hr_delete(reference)[0] == "exit"
    c = hr_ctrl([corrected_hr_preview()])
    status, result = run(c, [{"name": "po502", "switch": [SWITCH_IP], "deploy": True}], state="deleted", patch_version=patch_version)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert _log(c) == _log(reference)
    assert len(c.markdeletes()) == 1 and len(c.modifies()) == 1 and len(c.deploys()) == 1
    assert json.loads(c.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]["ADMIN_STATE"] == "false"
    assert c.detail[MEM_10]["nvPairs"]["ADMIN_STATE"] == "false"


def test_registered_scalar_sibling_without_patch_stops_a_po_pvlan_batch_before_any_write():
    """The PVLAN port-channel needs no patch, but a sibling that names a registered scalar does: without the approved
    patch the whole invocation is refused before any write or preview, the port-channel included."""
    mode = "host"
    c = new_ctrl(mode)
    c.detail[IF8] = {"policy": TRUNK, "nvPairs": trunk_host_nv(IF8)}
    batch = [
        po_item(mode, pvlan_association=[{"primary_vlan": 2210, "secondary_vlan": 2212}]),
        trunk_item(IF8, deploy=True, disable_lldp_transmit=True, description="scalar sibling"),
    ]
    status, result = run(c, batch, state="merged")
    assert status == "fail"
    assert "disable_lldp_transmit" in result["msg"] and "patch_version" in result["msg"]
    assert c.mutating() == [] and c.requests(mark=PREVIEW_MARK) == []


# ------------------------------------------------------------------ vPC
def _vpc_create(mode, patch_version=None):
    c = baseline_ctrl(mode)
    create_previews(c, mode)
    status, result = run_vpc(c, [vpc_item(mode)], patch_version=patch_version)
    return c, status, result


@pytest.mark.parametrize("patch_version", PATCH_VALUES)
@pytest.mark.parametrize("mode", [P_, TP, TS])
def test_vpc_pvlan_creation_sends_the_same_requests_for_any_patch_value(mode, patch_version):
    reference, status, result = _vpc_create(mode)
    assert status == "exit", result.get("msg")
    c, status, result = _vpc_create(mode, patch_version)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert _log(c) == _log(reference)
    assert "PATCH_VERSION" not in json.dumps(_log(c)).upper()


@pytest.mark.parametrize("patch_version", PATCH_VALUES)
@pytest.mark.parametrize("mode", [P_, TP, TS])
def test_vpc_pvlan_exact_repeat_writes_nothing_for_any_patch_value(mode, patch_version):
    c = seeded_ctrl(mode)
    converged_previews(c, mode)
    status, result = run_vpc(c, [vpc_item(mode)], state="merged", patch_version=patch_version)
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert c.writes() == [] and c.deploys() == []


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_po_vpc_reconcile.py
# PVLAN regular port-channel / vPC under `overridden` (A) and the NaC deployment contract (B).
#
# A -- `overridden` reuses the existing paths: a PVLAN aggregate the request keeps goes through its own PVLAN compare (replace
# semantics), and every PVLAN aggregate of the sweep's scope that the request no longer wants is registered by the SAME deletion
# preflight as a named `deleted` (ownership, admin-down members, fabric host default, bulk API), released and verified. The generic
# default reset the sweep queues for the member of a deleted aggregate is withdrawn (the PVLAN release corrects that member itself).
#
# MEASURED inputs: the existing fixtures of the harnesses and, for the vPC summary, `deletable` False on the child port-channel and
# on the physical members, True on the parent (NDFC 12.6.0.267) -- the vPC harness reports True everywhere, so MeasuredVpc restores
# the measured value. Real main(); only the controller boundary is intercepted.
# ====================================================================================================
PO_PROFILE = {"mode": "pvlan", "pvlan_mode": "host", "members": [G4.MEM], "pc_mode": "active", "admin_state": False,
              "pvlan_association": [{"primary_vlan": 2210, "secondary_vlan": 2212}]}
RETAINED_PO = {"name": "po502", "type": "pc", "switch": [SWITCH_IP], "deploy": True, "profile": PO_PROFILE}


def modify_payloads(ctrl):
    return [p for m, path, d in ctrl.calls if m == "POST" and path.endswith("/rest/interface/modify") for p in json.loads(d)]


# ================================================================== A: regular port-channel
def test_po_retained_by_overridden_is_its_own_pvlan_repetition_without_writes():
    ctrl = measured_po(G4.owned_ctrl())
    status, result = run(ctrl, [RETAINED_PO], state="overridden")
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert writes(ctrl) == []


def test_po_dropped_by_overridden_is_deleted_through_the_pvlan_path_and_its_member_released_once():
    ctrl = measured_po(G4.owned_ctrl())
    status, result = run(ctrl, [lo(SWITCH_IP)], state="overridden")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert writes(ctrl) == ["interface/markdelete", "interface/modify", "globalInterface/deploy", "globalInterface", "globalInterface/deploy"]
    payloads = modify_payloads(ctrl)
    assert len(payloads) == 1 and payloads[0]["policy"] == TRUNK, "ONE member write: the G4 correction, never the generic reset"
    nv = payloads[0]["interfaces"][0]["nvPairs"]
    assert nv["ADMIN_STATE"] == "false" and len(nv) == 50
    assert result["diff"][0]["replaced"] == [] and G4.MEM not in json.dumps(result["diff"][0]["deploy"])
    assert G4.PO not in ctrl.detail and ctrl.detail[G4.MEM]["nvPairs"]["ADMIN_STATE"] == "false"


def test_the_last_pvlan_port_channel_goes_with_an_empty_desired_set():
    ctrl = measured_po(G4.owned_ctrl())
    status, result = run(ctrl, [], state="overridden")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert writes(ctrl) == ["interface/markdelete", "interface/modify", "globalInterface/deploy"]


def test_override_intf_types_that_exclude_port_channels_leave_the_pvlan_port_channel_alone():
    ctrl = measured_po(G4.owned_ctrl())
    status, result = with_args(HH, run, ctrl, [lo(SWITCH_IP)], {"override_intf_types": ["lo"]}, state="overridden")
    assert status == "exit", result.get("msg")
    assert writes(ctrl) == ["globalInterface", "globalInterface/deploy"] and G4.PO in ctrl.detail


def test_a_dropped_port_channel_whose_member_is_up_is_released_to_the_fabric_default():
    # The up member is released like a down one; the fabric default here is "false", so it is corrected before the deploy
    ctrl = measured_po(G4.owned_ctrl())
    ctrl.detail[G4.MEM]["nvPairs"]["ADMIN_STATE"] = "true"
    status, result = run(ctrl, [lo(SWITCH_IP)], state="overridden")
    assert status == "exit", result.get("msg")
    assert writes(ctrl) == ["interface/markdelete", "interface/modify", "globalInterface/deploy", "globalInterface", "globalInterface/deploy"]
    assert ctrl.detail[G4.MEM]["nvPairs"]["ADMIN_STATE"] == "false"


def test_an_unreadable_summary_refuses_the_sweep_before_any_write():
    ctrl = measured_po(G4.owned_ctrl())
    ctrl.read_failures = {"/rest/interface/detail?serialNumber="}
    status, result = run(ctrl, [lo(SWITCH_IP)], state="overridden")
    assert status == "fail" and writes(ctrl) == [], result.get("msg")


def test_check_mode_keeps_a_retained_port_channel_and_refuses_an_undemonstrable_deletion():
    ctrl = measured_po(G4.owned_ctrl())
    status, result = run(ctrl, [RETAINED_PO], state="overridden", check_mode=True)
    assert status == "exit" and writes(ctrl) == [], result.get("msg")
    ctrl = measured_po(G4.owned_ctrl())
    status, result = run(ctrl, [lo(SWITCH_IP)], state="overridden", check_mode=True)
    assert status == "fail" and "refused in check mode" in result["msg"] and writes(ctrl) == [], result.get("msg")


def test_overridden_with_fewer_members_releases_the_dropped_member_through_the_membership_path():
    ctrl = measured_po(MU.seeded())
    ctrl.previews = [MU.fragments(kept=(MU.E7,), removed_trunk=(MU.E9,))]
    status, result = run(ctrl, [MU.item([MU.E7])], state="overridden")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.po_modifies()) == 1 and len(ctrl.member_modifies()) == 1 and len(ctrl.deploys()) == 1
    assert ctrl.detail[MU.E9]["policy"] == TRUNK and ctrl.detail[MU.E9]["nvPairs"]["ADMIN_STATE"] == "false"


# ================================================================== A: vPC
def test_vpc_retained_by_overridden_is_its_own_pvlan_repetition_without_writes():
    ctrl = vpc_ctrl()
    V.converged_previews(ctrl)
    status, result = V.run_vpc(ctrl, [V.vpc_item()], state="overridden")
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert writes(ctrl) == []


@pytest.mark.parametrize("switches", [[V.IP1], [V.IP1, V.IP2]], ids=["one-peer-in-request", "both-peers-in-request"])
def test_vpc_dropped_by_overridden_is_deleted_once_released_on_both_peers_and_verified(switches):
    ctrl = vpc_ctrl()
    V.delete_previews(ctrl)
    status, result = V.run_vpc(ctrl, [lo(ip) for ip in switches], state="overridden")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert writes(ctrl)[:4] == ["interface/markdelete", "interface/modify", "interface/modify", "globalInterface/deploy"]
    assert len(ctrl.markdeletes()) == 1, "one identity (pair + name), deleted once even when both peers are swept"
    assert sorted(p["interfaces"][0]["serialNumber"] for p in modify_payloads(ctrl) if p["policy"] == TRUNK) == [V.SN1, V.SN2]
    assert V.VPC not in ctrl.parents


class OtherPair(MeasuredVpc):
    """The controller places the first peer in ANOTHER pair than the summary's vPC identity."""

    def __call__(self, mod, method, path, data=None):
        if "vpcpair_serial_number" in path:
            self.calls.append((method, path, data))
            return HH.ok({"vpc_pair_sn": "FDO00000001~FDO00000009"})
        return super(OtherPair, self).__call__(mod, method, path, data)


def test_vpc_whose_pair_the_controller_does_not_confirm_is_refused_before_any_write():
    ctrl = vpc_ctrl(OtherPair)
    V.delete_previews(ctrl)
    status, result = V.run_vpc(ctrl, [lo(V.IP1)], state="overridden")
    assert status == "fail" and "vPC pair" in result["msg"] and writes(ctrl) == [], result.get("msg")


def test_vpc_dropped_with_an_up_member_on_one_peer_is_released_to_the_fabric_default():
    # An up member no longer blocks the drop; both released members reach the fabric default ("false") before the deploy
    ctrl = vpc_ctrl()
    ctrl.nodes[V.SN2][V.M2]["nvPairs"]["ADMIN_STATE"] = "true"
    V.delete_previews(ctrl)
    status, result = V.run_vpc(ctrl, [lo(V.IP1)], state="overridden")
    assert status == "exit", result.get("msg")
    V.release_only(ctrl)


# ================================================================== B: deploy false saves; a later process completes from controller state


def po_saved_ctrl():
    """The DEPLOYED-Po release harness (G4R1 measured marked-for-deletion listing) after a deletion saved with deploy false."""
    ctrl = measured_po(G5.hr_ctrl([G5.corrected_hr_preview()]))
    status, result = run(ctrl, [{"name": "po502", "switch": [SWITCH_IP], "deploy": False}], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    return ctrl, result


def test_po_deletion_with_deploy_false_is_saved_member_corrected_pending_gated_and_never_deployed():
    ctrl, result = po_saved_ctrl()
    assert writes(ctrl) == ["interface/markdelete", "interface/modify"], "no deployment request at all"
    assert ctrl.marked is not None and ctrl.detail[G5.MEM_10]["nvPairs"]["ADMIN_STATE"] == "false"
    assert [r["operation"] for r in result["pvlan_saved"]] == ["delete"] and "NOT deployed" in result["pvlan_saved"][0]["state"]
    assert [g["site"] for g in result["pvlan_gate"]] == ["delete_saved"]


def test_a_saved_deletion_repeated_with_deploy_false_writes_nothing_and_stays_reported_pending():
    ctrl = po_saved_ctrl()[0]
    ctrl.previews = [G5.corrected_hr_preview()]
    calls = len(ctrl.calls)
    status, result = run(ctrl, [{"name": "po502", "switch": [SWITCH_IP], "deploy": False}], state="deleted")
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert writes(type("C", (), {"calls": ctrl.calls[calls:]})) == []
    assert "awaiting deployment" in result["pvlan_saved"][0]["state"], "pending, never reported as done"


@pytest.mark.parametrize("state, config", [("deleted", [{"name": "po502", "switch": [SWITCH_IP], "deploy": True}]),
                                           ("overridden", [lo(SWITCH_IP)])])
def test_a_saved_deletion_is_completed_and_verified_by_a_later_deploy_true_request_without_a_second_mark_delete(state, config):
    ctrl = po_saved_ctrl()[0]
    ctrl.previews = [G5.corrected_hr_preview(), G5.corrected_hr_preview()]
    calls = len(ctrl.calls)
    status, result = run(ctrl, config, state=state)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    later = writes(type("C", (), {"calls": ctrl.calls[calls:]}))
    assert later[0] == "globalInterface/deploy" and "interface/markdelete" not in later and "interface/modify" not in later
    assert ctrl.marked is None and G5.PO_502 not in ctrl.detail
    assert any(r.get("state") == "completing the saved deletion" for r in result["pvlan_saved"])


def test_a_saved_deletion_whose_pending_would_bring_the_member_up_never_deploys():
    ctrl = measured_po(G5.hr_ctrl([{"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [G5.g4r1_entry("HR-post")]}]))
    status, result = run(ctrl, [{"name": "po502", "switch": [SWITCH_IP], "deploy": False}], state="deleted")
    assert status == "fail" and "'no shutdown'" in result["msg"] and "ALREADY changed" in result["msg"], result.get("msg")
    assert "globalInterface/deploy" not in writes(ctrl)


def test_a_saved_deletion_whose_preview_cannot_be_read_is_refused_before_any_write():
    ctrl = po_saved_ctrl()[0]
    ctrl.read_failures = {"/config-preview/"}
    calls = len(ctrl.calls)
    status, result = run(ctrl, [{"name": "po502", "switch": [SWITCH_IP], "deploy": True}], state="deleted")
    assert status == "fail" and "cannot be classified" in result["msg"], result.get("msg")
    assert writes(type("C", (), {"calls": ctrl.calls[calls:]})) == []


def saved_removal_ctrl():
    """A member removal SAVED with deploy false; the next invocation sees the MEASURED state (live PO-8b/8c, F-RA-1): the port-channel
    itself stays In-Sync (no pending of its own), the released member carries the pending and the switch is not In-Sync."""
    ctrl = measured_po(MU.seeded())
    ctrl.previews = [MU.fragments(kept=(MU.E7,), removed_trunk=(MU.E9,))]
    status, result = run(ctrl, [MU.item([MU.E7], deploy=False)], state="replaced")
    assert status == "exit" and ctrl.deploys() == [] and len(ctrl.member_modifies()) == 1, result.get("msg")
    ctrl.next_invocation()
    return ctrl


@pytest.fixture
def switch_out_of_sync(monkeypatch):
    monkeypatch.setitem(HH.INVENTORY, SWITCH_IP, dict(HH.INVENTORY[SWITCH_IP], ccStatus="Out-of-Sync"))


def test_member_removal_saved_with_deploy_false_is_completed_by_a_later_deploy_true_repetition(switch_out_of_sync):
    ctrl = saved_removal_ctrl()
    ctrl.previews = [MU.fragments(kept=(MU.E7,), removed_trunk=(MU.E9,)) for _i in range(2)]  # the saved-removal check, then the gate
    status, result = run(ctrl, [MU.item([MU.E7], deploy=True)], state="replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.deploys()) == 1 and len(ctrl.member_modifies()) == 1, "deployed once; the member is not written again"
    assert any(r.get("state") == "completing the saved removal" for r in result["pvlan_saved"])


def test_a_saved_member_removal_repeated_with_deploy_false_writes_nothing_and_stays_reported_pending(switch_out_of_sync):
    ctrl = saved_removal_ctrl()
    before = len(ctrl.writes())  # the saving invocation's writes
    ctrl.previews = [MU.fragments(kept=(MU.E7,), removed_trunk=(MU.E9,))]
    status, result = run(ctrl, [MU.item([MU.E7], deploy=False)], state="replaced")
    assert status == "exit" and result["changed"] is False and len(ctrl.writes()) == before, result.get("msg")
    assert [s for s in result["pvlan_saved"] if s["operation"] == "remove member" and s["members"] == [MU.E9]
            and s["state"].startswith("saved, awaiting deployment")], result.get("pvlan_saved")


def test_a_repetition_whose_saved_removal_check_cannot_read_the_preview_is_refused(switch_out_of_sync):
    ctrl = saved_removal_ctrl()
    ctrl.previews = [{"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}]
    status, result = run(ctrl, [MU.item([MU.E7], deploy=True)], state="replaced")
    assert status == "fail" and "rule out a saved member removal" in result["msg"] and ctrl.deploys() == [], result.get("msg")


def vpc_saved_ctrl():
    ctrl = vpc_ctrl()
    ctrl.children_marked_deleted = True  # MEASURED: the children stay listed, marked, until the deploy
    vpc_queue(ctrl, 1)
    status, result = V.run_vpc(ctrl, [V.vpc_del_item(deploy=False)], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    return ctrl, result


def test_vpc_deletion_with_deploy_false_is_saved_on_both_peers_and_never_deployed():
    ctrl, result = vpc_saved_ctrl()
    assert writes(ctrl) == ["interface/markdelete", "interface/modify", "interface/modify"]
    assert all(ctrl.nodes[s][p]["nvPairs"]["ADMIN_STATE"] == "false" for s, p in ((V.SN1, V.M1), (V.SN2, V.M2)))
    assert result["pvlan_saved"][0]["kind"] == "vpc"


@pytest.mark.parametrize("deploy, expected_writes", [(False, []), (True, ["globalInterface/deploy"])])
def test_a_saved_vpc_deletion_is_read_from_both_peers_by_the_next_process(deploy, expected_writes):
    ctrl = vpc_saved_ctrl()[0]
    vpc_queue(ctrl, 2)
    ctrl.next_invocation()
    calls = len(ctrl.calls)
    status, result = V.run_vpc(ctrl, [V.vpc_del_item(deploy=deploy)], state="deleted")
    assert status == "exit", result.get("msg")
    assert writes(type("C", (), {"calls": ctrl.calls[calls:]})) == expected_writes
    assert sorted(ctrl.previews_asked()[-4:] if deploy else ctrl.previews_asked()[-2:])[0] == V.SN1


def test_a_vpc_deletion_marked_on_one_peer_only_is_refused_with_that_diagnosis():
    ctrl = vpc_saved_ctrl()[0]
    ctrl.summary_extra[V.SN2] = []  # the second peer no longer lists its marked child: applied on one peer only
    vpc_queue(ctrl, 2)
    ctrl.next_invocation()
    calls = len(ctrl.calls)
    status, result = V.run_vpc(ctrl, [V.vpc_del_item()], state="deleted")
    assert status == "fail" and "applied on one peer only" in result["msg"], result.get("msg")
    assert writes(type("C", (), {"calls": ctrl.calls[calls:]})) == []


def test_overridden_with_deploy_false_saves_the_dropped_vpc():
    ctrl = vpc_ctrl()
    ctrl.children_marked_deleted = True
    vpc_queue(ctrl, 1)
    status, result = with_args(V, V.run_vpc, ctrl, [lo(V.IP1, deploy=False)], {"deploy": False}, state="overridden")
    assert status == "exit", result.get("msg")
    assert "globalInterface/deploy" not in writes(ctrl) and len(ctrl.markdeletes()) == 1


# ================================================================== NaC PR895 argument shapes (fixtures/nac_case_models.yaml#nac_pr895_pvlan_args)

NAC = load_case("nac_pr895_pvlan_args")


def nac_po(members, deploy=False):
    """The rendered NaC PR895 PVLAN Po entry (types and keys as NaC sends them) on the harness names: switch, name and members only."""
    e = copy.deepcopy([x for x in NAC["create_pvlan"] if x["type"] == "pc"][0])
    e.update(name="po10", switch=[SWITCH_IP], deploy=deploy)
    e["profile"]["members"] = list(members)
    return e


def nac_vpc(deploy=False):
    e = copy.deepcopy([x for x in NAC["create_pvlan"] if x["type"] == "vpc"][0])
    e.update(name="vpc10", switch=[V.IP1, V.IP2], deploy=deploy)
    e["profile"].update(peer1_members=[V.M1], peer2_members=[V.M2], peer1_pcid=10, peer2_pcid=10, peer1_description="", peer2_description="")
    return e


def test_nac_rendered_po_member_removal_in_the_create_phase_is_saved():
    # NaC create phase: state replaced, the rendered entry with deploy false and one member fewer.
    # The port-channel already carries NaC's rendered description (intent and device), as after NaC created it.
    desc = "NetAsCode PVLAN Port-Channel Interface"
    ctrl = measured_po(MU.seeded())
    ctrl.detail[MU.H.PO]["nvPairs"]["DESC"] = desc
    pv = MU.fragments(kept=(MU.E7,), removed_trunk=(MU.E9,))
    for key in ("runningConfig", "expectedConfig"):
        lines = pv["DATA"][0][key]
        i = lines.index("interface port-channel10")
        pv["DATA"][0][key] = lines[:i + 1] + ["  description " + desc] + lines[i + 1:]
    ctrl.previews = [pv]
    entry = nac_po([MU.E7])
    status, result = run(ctrl, [entry], state="replaced")
    assert status == "exit", result.get("msg")
    assert ctrl.deploys() == [] and len(ctrl.member_modifies()) == 1
    assert any(r["operation"] == "remove member" for r in result.get("pvlan_saved", []))


def test_nac_rendered_vpc_kept_by_the_full_run_overridden_is_accepted_without_writes():
    ctrl = vpc_ctrl()
    V.converged_previews(ctrl)
    status, result = V.run_vpc(ctrl, [nac_vpc()], state="overridden")
    assert status == "exit" and writes(ctrl) == [], result.get("msg")
