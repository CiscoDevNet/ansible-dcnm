"""PVLAN port-channel `cmds` and vPC `peer1_cmds` / `peer2_cmds` given as text, as NaC renders `freeform_config` for port-channels
(`cmds: |2-` + `interface['freeform_config'] | default('')`) and vPCs (`peerN_cmds: |2-` + `switches[peerN].freeform_config | default('')`).

Real main() through the existing port-channel / vPC harnesses; the generic NaC fragments are rendered with Jinja2 and parsed as YAML
(the colleague's own PVLAN renderer is not known). Synthetic freeform commands; NOT LIVE TESTED.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

import jinja2
import pytest
import yaml

from . import test_dcnm_intf_pvlan_vpc_harness as V
from .test_dcnm_intf_pvlan_harness import SWITCH_IP, preview, run
from .test_dcnm_intf_pvlan_po_g1 import created, po_stanza, member_stanza
from .test_dcnm_intf_pvlan_po_host import PO_ITEM_NAME
from .test_dcnm_intf_pvlan_speed_freeform import ASSOC, FF_A, FF_B, HOST_LINES, created_with

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
