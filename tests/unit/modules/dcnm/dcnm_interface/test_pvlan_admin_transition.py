"""Administrative-state changes of existing PVLAN interfaces: standalone Ethernet and regular port-channels change it; a vPC refuses it.

Real main() through the shared controller doubles; only controller I/O is mocked. The previews are SYNTHETIC: the measured converged
G6-M0a Ethernet stanzas and the port-channel harness stanzas with their administrative line changed. The pending of the change is the
single `no shutdown` or `shutdown` line, with no separate withdrawal: the form NDFC 12.6.0.267 rendered when a down member was released
up and when a down PVLAN port-channel was brought up with the rest of its stanza. An administrative-only change of an existing PVLAN
interface is NOT measured.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .helpers import port_channel_controller as PC
from .helpers import vpc_controller as V
from .helpers.ethernet_controller import DEPLOY
from .helpers.ethernet_controller import IF7
from .helpers.ethernet_controller import MODIFY
from .helpers.ethernet_controller import PREVIEW_MARK
from .helpers.ethernet_controller import PVLAN
from .helpers.ethernet_controller import SWITCH_IP
from .helpers.ethernet_controller import authority
from .helpers.ethernet_controller import eth_item
from .helpers.ethernet_controller import full_model
from .helpers.ethernet_controller import have_nv
from .helpers.ethernet_controller import preview
from .helpers.ethernet_controller import run
from .helpers.ethernet_lifecycle import ctrl

UP_DOWN = [True, False]
ADMIN = ("shutdown", "no shutdown")


def word(up):
    return "true" if up else "false"


def admin_line(up):
    return "no shutdown" if up else "shutdown"


def with_admin(stanza, up, device=False):
    """`stanza` with its administrative line set; the device omits `no shutdown`, the controller's expected configuration shows it."""
    body = [line for line in stanza if line.strip() not in ADMIN]
    return body if up and device else body + ["  " + admin_line(up)]


def without_meta(nv):
    return dict((k, v) for k, v in nv.items() if k not in ("INTF_NAME", "POLICY_ID"))


def changed_keys(before, after):
    keys = set(before) | set(after)
    return sorted(k for k in keys if before.get(k) != after.get(k))


# ================================================================== standalone Ethernet (measured converged G6-M0a stanzas)
RUN_ETH, EXP_ETH = authority("G6-M0a", "post")


def eth_ctrl(up):
    """The existing trunk promiscuous port, deployed and converged in the opposite state of `up`."""
    return ctrl(have_nv(ADMIN_STATE=word(not up)))


def eth_preview(up, pending=None, running=None, expected=None):
    body = ["interface ethernet1/7", "  " + admin_line(up), "configure terminal"] if pending is None else pending
    return preview(body, running=with_admin(RUN_ETH, not up, device=True) if running is None else running,
                   expected=with_admin(EXP_ETH, up) if expected is None else expected)


def eth_converged(up):
    return preview([], running=with_admin(RUN_ETH, up, device=True), expected=with_admin(EXP_ETH, up))


@pytest.mark.parametrize("up", UP_DOWN)
def test_merged_ethernet_admin_change_writes_only_the_state_and_deploys(up):
    c = eth_ctrl(up)
    have = copy.deepcopy(c.detail[IF7]["nvPairs"])
    c.previews = [eth_preview(up)]
    status, res = run(c, [eth_item(admin_state=up)])
    assert status == "exit" and res["changed"] is True, res.get("msg")
    policy, sent = c.sent_nv()
    assert policy == PVLAN and sent["ADMIN_STATE"] == word(up)
    # the omitted mapping, native and allowed VLANs and every other field keep their stored values
    assert changed_keys(without_meta(have), without_meta(sent)) == ["ADMIN_STATE"]
    assert c.order() == ["MODIFY", "PREVIEW", "DEPLOY"]
    assert [g["targets"] for g in res["pvlan_gate"]] == [{IF7: "deploy"}]


@pytest.mark.parametrize("up", UP_DOWN)
def test_ethernet_admin_change_repeats_quietly(up):
    c = eth_ctrl(up)
    c.previews = [eth_preview(up)]
    assert run(c, [eth_item(admin_state=up)])[0] == "exit"
    c.next_invocation()
    c.calls = []
    c.previews = [eth_converged(up)]
    status, res = run(c, [eth_item(admin_state=up)])
    assert status == "exit" and res["changed"] is False, res.get("msg")
    assert c.mutating() == []


@pytest.mark.parametrize("up", UP_DOWN)
def test_ethernet_admin_change_saved_then_deployed_by_the_next_run(up):
    c = eth_ctrl(up)
    status, res = run(c, [eth_item(admin_state=up, deploy=False)])
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert c.order() == ["MODIFY"] and c.detail[IF7]["nvPairs"]["ADMIN_STATE"] == word(up)
    c.next_invocation()
    c.calls = []
    c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
    c.previews = [eth_preview(up)]
    status, res = run(c, [eth_item(admin_state=up)])
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert c.requests("POST", MODIFY) == [] and len(c.requests("POST", DEPLOY)) == 1


@pytest.mark.parametrize("up", UP_DOWN)
def test_ethernet_admin_change_in_check_mode_writes_nothing(up):
    # As for every planned PVLAN write: the bulk capability has no check-mode probe, so check mode refuses without a request.
    c = eth_ctrl(up)
    status, res = run(c, [eth_item(admin_state=up)], check_mode=True)
    assert status == "fail" and "could not be verified in check mode" in res["msg"], res.get("msg")
    assert c.mutating() == [] and c.requests(mark=PREVIEW_MARK) == []


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("up", UP_DOWN)
def test_replaced_and_overridden_ethernet_admin_change_with_the_complete_model(up, state):
    c = eth_ctrl(up)
    c.previews = [eth_preview(up)]
    item = full_model()
    item["profile"]["admin_state"], item["deploy"] = up, True
    status, res = run(c, [item], state=state)
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert c.sent_nv()[1]["ADMIN_STATE"] == word(up) and len(c.requests("POST", DEPLOY)) == 1


def _not_deployed(c, status, res, needle):
    assert status == "fail" and needle in res["msg"], res.get("msg")
    assert c.requests("POST", DEPLOY) == []


@pytest.mark.parametrize("up", UP_DOWN)
def test_opposite_absent_or_contradictory_pending_is_refused(up):
    for pending, needle in (
        (["interface ethernet1/7", "  " + admin_line(not up)], "is absent from the pending"),
        ([], "the pending for Ethernet1/7 is empty but the device differs"),
        (["interface ethernet1/7", "  " + admin_line(up), "  " + admin_line(not up)], "Ethernet1/7"),
    ):
        c = eth_ctrl(up)
        c.previews = [eth_preview(up, pending=pending)]
        status, res = run(c, [eth_item(admin_state=up)])
        _not_deployed(c, status, res, needle)


def test_a_contradictory_pending_names_the_opposite_line():
    down = P.Model({"switchport", "shutdown"}, None, (), True)
    up = P.Model({"switchport", "no shutdown"}, None, (), True)
    assert P.validate_transition(["no shutdown", "shutdown"], down, up) == ["unmodeled command 'shutdown'"]
    assert P.validate_transition(["shutdown", "no shutdown"], up, down) == ["unexpected removal 'no shutdown'"]


@pytest.mark.parametrize("up", UP_DOWN)
def test_unrelated_mapping_withdrawal_foreign_command_or_interface_is_refused(up):
    for extra, needle in (
        (["  no switchport private-vlan mapping trunk 2210 2211"], "unexpected removal"),
        (["  logging event port link-status"], "unmodeled command"),
        (["interface ethernet1/9", "  no shutdown"], "outside"),
    ):
        c = eth_ctrl(up)
        c.previews = [eth_preview(up, pending=["interface ethernet1/7", "  " + admin_line(up)] + extra + ["configure terminal"])]
        status, res = run(c, [eth_item(admin_state=up)])
        _not_deployed(c, status, res, needle)


@pytest.mark.parametrize("up", UP_DOWN)
def test_stale_ambiguous_or_missing_authority_is_refused(up):
    stale = with_admin(EXP_ETH, not up)
    twice = with_admin(EXP_ETH, up) * 2
    for kw, needle in (({"expected": stale}, "disagrees with the intended state"), ({"expected": twice}, "stanzas")):
        c = eth_ctrl(up)
        c.previews = [eth_preview(up, **kw)]
        status, res = run(c, [eth_item(admin_state=up)])
        _not_deployed(c, status, res, needle)
    c = eth_ctrl(up)
    pv = eth_preview(up)
    del pv["DATA"][0]["runningConfig"]
    c.previews = [pv]
    status, res = run(c, [eth_item(admin_state=up)])
    _not_deployed(c, status, res, "runningConfig")


def test_a_pending_admin_line_without_a_requested_change_is_refused():
    # The port stays down; a pending `no shutdown` the request does not explain is an unexpected removal, not an admin change.
    c = eth_ctrl(False)
    c.detail[IF7]["nvPairs"]["ADMIN_STATE"] = "false"
    add = [{"primary_vlan": 2210, "secondary_vlans": "2212"}]
    running = with_admin(RUN_ETH, False, device=True)
    expected = with_admin(EXP_ETH, False) + ["  switchport private-vlan mapping trunk 2210 2212"]
    pend = ["interface ethernet1/7", "  switchport private-vlan mapping trunk 2210 2212", "  no shutdown", "configure terminal"]
    c.previews = [preview(pend, running=running, expected=expected)]
    status, res = run(c, [eth_item(pvlan_mapping=add)])
    _not_deployed(c, status, res, "unexpected removal 'no shutdown'")


# ================================================================== regular port-channels (every supported mode)
PO_CASES = dict(PC.CASES, host=({"pvlan_association": PC.ASSOC}, PC.HOST_LINES))
PO_MODES = sorted(PO_CASES)


def po_ctrl(mode, up):
    c = PC.created(mode, PC.HOST_LINES, **PO_CASES[mode][0]) if mode == "host" else PC.existing(mode)
    c.detail[PC.PO]["nvPairs"]["ADMIN_STATE"] = word(not up)
    return c


def po_preview(mode, up, pending=None):
    _profile, lines = PO_CASES[mode]
    stanza = PC.po_stanza(mode, lines)
    member = PC.member_stanza(mode, lines)
    body = ["interface port-channel10", "  " + admin_line(up), "configure terminal"] if pending is None else pending
    return preview(body, running=with_admin(stanza, not up, device=True) + member, expected=with_admin(stanza, up) + member)


def po_converged(mode, up):
    _profile, lines = PO_CASES[mode]
    stanza = PC.po_stanza(mode, lines)
    member = PC.member_stanza(mode, lines)
    return preview([], running=with_admin(stanza, up, device=True) + member, expected=with_admin(stanza, up) + member)


def po_admin_item(mode, up, deploy=True):
    return {"name": PC.PO_ITEM_NAME, "type": "pc", "switch": [SWITCH_IP], "deploy": deploy,
            "profile": {"mode": "pvlan", "pvlan_mode": mode, "admin_state": up}}


@pytest.mark.parametrize("up", UP_DOWN)
@pytest.mark.parametrize("mode", PO_MODES)
def test_merged_port_channel_admin_change_writes_only_the_state_and_deploys(mode, up):
    c = po_ctrl(mode, up)
    have = copy.deepcopy(c.detail[PC.PO]["nvPairs"])
    member = copy.deepcopy(c.detail[IF7])
    c.previews = [po_preview(mode, up)]
    status, res = run(c, [po_admin_item(mode, up)], state="merged")
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert c.creates() == [] and len(c.bulk_bodies()) == 1 and len(c.deploys()) == 1
    body = c.bulk_bodies()[0]
    assert [p["policy"] for p in body] == [PC.PO_HOST] and [i["ifName"] for i in body[0]["interfaces"]] == [PC.PO]
    sent = body[0]["interfaces"][0]["nvPairs"]
    # the omitted lists, member, mode and every other field keep their stored values; the member is not written
    assert changed_keys(without_meta(have), without_meta(sent)) == ["ADMIN_STATE"] and sent["ADMIN_STATE"] == word(up)
    assert c.detail[IF7] == member


@pytest.mark.parametrize("up", UP_DOWN)
@pytest.mark.parametrize("mode", PO_MODES)
def test_port_channel_admin_change_repeats_quietly(mode, up):
    c = po_ctrl(mode, up)
    c.previews = [po_preview(mode, up)]
    assert run(c, [po_admin_item(mode, up)], state="merged")[0] == "exit"
    c.next_invocation()
    c.calls = []
    c.previews = [po_converged(mode, up)]
    status, res = run(c, [po_admin_item(mode, up)], state="merged")
    assert status == "exit" and res["changed"] is False, res.get("msg")
    assert c.writes() == []


@pytest.mark.parametrize("up", UP_DOWN)
def test_port_channel_admin_change_saved_in_check_mode_and_refused_on_a_wrong_pending(up):
    mode = "promiscuous"
    c = po_ctrl(mode, up)
    status, res = run(c, [po_admin_item(mode, up)], state="merged", check_mode=True)
    assert status == "fail" and "could not be verified in check mode" in res["msg"] and c.writes() == [], res.get("msg")
    status, res = run(c, [po_admin_item(mode, up, deploy=False)], state="merged")
    assert status == "exit" and res["changed"] is True and len(c.bulk_bodies()) == 1 and c.deploys() == [], res.get("msg")
    assert c.detail[PC.PO]["nvPairs"]["ADMIN_STATE"] == word(up)
    c = po_ctrl(mode, up)
    c.previews = [po_preview(mode, up, pending=["interface port-channel10", "  " + admin_line(not up), "configure terminal"])]
    status, res = run(c, [po_admin_item(mode, up)], state="merged")
    assert status == "fail" and c.deploys() == [], res.get("msg")


# ================================================================== vPC: refused before any write, in both directions
@pytest.mark.parametrize("up", UP_DOWN)
def test_a_vpc_admin_change_is_refused_before_any_write_in_both_directions(up):
    c = V.created_ctrl(admin=word(not up))
    for serial, port in ((V.SN1, V.M1), (V.SN2, V.M2)):
        # the deployed current state (the opposite of `up`); the refusal comes before any preview is read
        c.vpc_previews[serial] = [preview([], serial=serial, running=V.po_stanza(shut=up) + V.member_after(port),
                                          expected=V.po_stanza(shut=up) + V.member_after(port))]
    status, res = V.run_vpc(c, [V.vpc_item(admin_state=up)], state="merged")
    assert status == "fail" and "the administrative state of an existing PVLAN vPC is not changed" in res["msg"], res.get("msg")
    assert c.writes() == [] and c.modifies() == [] and not any("config-preview" in call[1] for call in c.calls)


@pytest.mark.parametrize("up", UP_DOWN)
def test_a_vpc_repeat_does_not_deploy_an_admin_change_saved_outside_the_module(up):
    # The controller already holds the other state (saved elsewhere, not deployed); the unchanged request with deploy true is refused.
    c = V.created_ctrl(admin=word(up))
    for serial, port in ((V.SN1, V.M1), (V.SN2, V.M2)):
        running = with_admin(V.po_stanza(shut=not up), not up, device=True) + V.member_after(port)
        c.vpc_previews[serial] = [preview(["interface port-channel10", "  " + admin_line(up), "configure terminal"], serial=serial,
                                          running=running, expected=V.po_stanza(shut=not up) + V.member_after(port))]
    status, res = V.run_vpc(c, [V.vpc_item(admin_state=up)], state="merged")
    assert status == "fail" and "which this target does not allow" in res["msg"], res.get("msg")
    assert c.writes() == [] and c.deploys() == []


def test_the_vpc_gates_keep_refusing_an_admin_change_they_did_not_request():
    down = P.Model({"switchport", "shutdown"}, None, (), True)
    up = P.Model({"switchport", "no shutdown"}, None, (), True)
    assert P.admin_change(down, up) == ("shutdown", "no shutdown") and P.admin_change(up, down) == ("no shutdown", "shutdown")
    assert P.admin_change(down, down) is None
    assert P.validate_transition(["no shutdown"], down, up) == P.validate_transition(["shutdown"], up, down) == []
    assert P.validate_transition(["no shutdown"], down, up, admin_fixed=True) == [
        "the administrative state changes from 'shutdown' to 'no shutdown', which this target does not allow"]
    assert P.vpc_transition_problems(up, down) == [
        "the administrative state of an existing PVLAN vPC is not changed by this module ('no shutdown' -> 'shutdown')"]
    # an unchanged administrative state is not a change, with or without the restriction
    d_pre = P.Model({"switchport", "shutdown"}, None, (), True)
    d_post = P.Model({"switchport", "shutdown", "description x"}, None, (), True)
    assert P.vpc_transition_problems(d_pre, d_post) == [] == P.validate_transition(["description x"], d_pre, d_post, admin_fixed=True)


def test_the_request_and_payload_carry_the_state_as_admin_state():
    raw = {"pvlan_mode": "host", "members": [IF7], "admin_state": True,
           "pvlan_association": [{"primary_vlan": 2210, "secondary_vlan": 2212}]}
    assert P.po_host_nvpairs(raw, PC.PO)["ADMIN_STATE"] == "true"
    assert P.po_host_nvpairs(dict(raw, admin_state=False), PC.PO)["ADMIN_STATE"] == "false"
    assert "no shutdown" in P.render(PC.PO_HOST, P.po_host_nvpairs(raw, PC.PO)).scalars
    assert "shutdown" in P.render(PC.PO_HOST, P.po_host_nvpairs(dict(raw, admin_state=False), PC.PO)).scalars
