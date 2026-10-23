"""PVLAN Ethernet `cmds` given as text, as NAC renders `freeform_config` (`cmds: |2-` + `default('')`).

Real main() through the PVLAN harness; the NAC fragment is rendered with Jinja2 and parsed as YAML. NOT LIVE TESTED."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

import jinja2
import pytest
import yaml

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .test_dcnm_intf_pvlan_harness import (
    IF7,
    IF8,
    PREVIEW_MARK,
    PVLAN,
    SWITCH_IP,
    TRUNK,
    FakeController,
    pvlan_item,
    pvlan_nv,
    run,
    trunk_host_nv,
)

NAC_FRAGMENT = "profile:\n    cmds: |2-\n      {{ interface['freeform_config'] | default('') | indent(6, false) }}\n"
HOST_A11 = pvlan_nv("H3a")
ASSOC = [{"primary_vlan": 2210, "secondary_vlan": 2211}]
FF_1 = "no autostate"
FF_2 = "logging event port link-status"


def nac_cmds(**interface):
    """The value NAC hands to the module for `freeform_config` (absent when the keyword is not given)."""
    rendered = jinja2.Environment().from_string(NAC_FRAGMENT).render(interface=interface)
    return yaml.safe_load(rendered)["profile"]["cmds"]


def ctrl(nv, policy=PVLAN, ifname=IF7):
    c = FakeController()
    c.detail[ifname] = {"policy": policy, "nvPairs": copy.deepcopy(nv)}
    return c


def host_item(cmds, deploy=False, ifname=IF7):
    return pvlan_item(ifname, deploy=deploy, pvlan_mode="host", admin_state=False, pvlan_association=copy.deepcopy(ASSOC), cmds=cmds)


def regular_item(mode, cmds, ifname=IF8):
    return {"name": ifname, "type": "eth", "switch": [SWITCH_IP], "deploy": False, "profile": {"mode": mode, "cmds": cmds}}


def assert_refused_before_any_write(c, status, res, fragment):
    assert status == "fail", res
    assert fragment in res["msg"], res["msg"]
    assert "No change was sent" in res["msg"]
    assert c.mutating() == [] and c.requests(mark=PREVIEW_MARK) == []


# ------------------------------------------------------------------ the renderer boundary
def test_r_nac_fragment_renders_text_for_scalar_omitted_and_empty():
    assert nac_cmds(freeform_config=FF_1) == FF_1
    assert nac_cmds() == ""
    assert nac_cmds(freeform_config="") == ""
    assert nac_cmds(freeform_config=FF_1 + "\n" + FF_2) == FF_1 + "\n" + FF_2


# ------------------------------------------------------------------ PVLAN Ethernet accepts the rendered text (real main())
@pytest.mark.parametrize(
    "freeform, conf",
    [
        ({"freeform_config": FF_1}, FF_1),
        ({}, ""),
        ({"freeform_config": ""}, ""),
        ({"freeform_config": FF_1 + "\n" + FF_2}, FF_1 + "\n" + FF_2),
    ],
    ids=["scalar", "omitted", "empty", "multiline"],
)
def test_r_pvlan_host_accepts_the_nac_text_and_sends_it_as_conf(freeform, conf):
    c = ctrl(trunk_host_nv(), TRUNK)
    status, res = run(c, [host_item(nac_cmds(**freeform))])
    assert status == "exit", res
    policy, nv = c.sent_nv()
    assert policy == PVLAN and nv["PVLAN_MODE"] == "host"
    assert nv["CONF"] == conf


@pytest.mark.parametrize("cmds, conf", [([FF_1], FF_1), ([], ""), ([FF_1, FF_2], FF_1 + "\n" + FF_2)], ids=["one", "empty", "two"])
def test_r_pvlan_host_list_control_is_unchanged(cmds, conf):
    c = ctrl(trunk_host_nv(), TRUNK)
    status, res = run(c, [host_item(cmds)])
    assert status == "exit", res
    assert c.sent_nv()[1]["CONF"] == conf


# ------------------------------------------------------------------ parity with the regular Ethernet modes (reference, same text)
@pytest.mark.parametrize("mode", ["trunk", "access"])
@pytest.mark.parametrize(
    "freeform, conf",
    [({"freeform_config": FF_1}, FF_1), ({}, ""), ({"freeform_config": FF_1 + "\n" + FF_2}, FF_1 + "\n" + FF_2)],
    ids=["scalar", "omitted", "multiline"],
)
def test_r_regular_ethernet_sends_the_same_conf_for_the_same_text(mode, freeform, conf):
    c = ctrl(trunk_host_nv(IF8), TRUNK, IF8)
    status, res = run(c, [regular_item(mode, nac_cmds(**freeform))])
    assert status == "exit", res
    sent = c.sent_nv(IF8)
    if sent is None:  # trunk -> trunk with '' against a stored '' is no change: nothing is sent
        assert mode == "trunk" and conf == "" and trunk_host_nv(IF8).get("CONF", "") == ""
    else:
        assert sent[1]["CONF"] == conf


def test_r_regular_path_splits_a_comma_which_pvlan_refuses_instead_of_guessing():
    text = "logging event port link-status, trunk-status"
    c = ctrl(trunk_host_nv(IF8), TRUNK, IF8)
    status, res = run(c, [regular_item("trunk", text)])
    assert status == "exit", res
    assert c.sent_nv(IF8)[1]["CONF"] == "logging event port link-status\n trunk-status"  # the regular conversion, recorded as reference
    c = ctrl(trunk_host_nv(), TRUNK)
    status, res = run(c, [host_item(text)])
    assert_refused_before_any_write(c, status, res, "must not contain a comma")


# ------------------------------------------------------------------ structured-command protection on every line
@pytest.mark.parametrize(
    "cmds",
    [
        FF_1 + "\nswitchport mode trunk",
        FF_1 + "\n  no switchport",
        FF_1 + "\nswitchport private-vlan host-association 2210 2212",
        [FF_1 + "\nswitchport mode trunk"],
        [FF_1, "switchport mode trunk"],
        "switchport mode trunk",
    ],
    ids=["text-line2", "text-line2-no-indented", "text-line2-private-vlan", "list-entry-line2", "list-second-entry", "text-line1"],
)
def test_r_a_structured_command_on_any_line_is_refused_before_any_write(cmds):
    c = ctrl(trunk_host_nv(), TRUNK)
    status, res = run(c, [host_item(cmds)])
    assert_refused_before_any_write(c, status, res, "must not manage private-vlan or switchport")


@pytest.mark.parametrize("cmds", [5, {"line": FF_1}, True, [FF_1, 7], [{"x": 1}]], ids=["int", "dict", "bool", "list-int", "list-dict"])
def test_r_non_text_values_stay_refused(cmds):
    c = ctrl(trunk_host_nv(), TRUNK)
    status, res = run(c, [host_item(cmds)])
    assert_refused_before_any_write(c, status, res, "cmds must be a list of strings")


# ------------------------------------------------------------------ lifecycle: merged keeps, replaced follows the text, repeat is a no-op
@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_r_repeat_of_the_same_text_sends_nothing(state):
    c = ctrl(dict(HOST_A11, CONF=FF_1))
    status, res = run(c, [host_item(nac_cmds(freeform_config=FF_1))], state=state)
    assert status == "exit" and res["changed"] is False, res
    assert c.mutating() == []


def test_r_omitted_freeform_under_merged_keeps_the_stored_commands():
    c = ctrl(dict(HOST_A11, CONF=FF_1))
    status, res = run(c, [host_item(nac_cmds())], state="merged")
    assert status == "exit" and res["changed"] is False, res
    assert c.mutating() == []


def test_r_omitted_freeform_under_replaced_clears_them_like_the_regular_path():
    c = ctrl(dict(HOST_A11, CONF=FF_1))
    status, res = run(c, [host_item(nac_cmds())], state="replaced")
    assert status == "exit" and res["changed"] is True, res
    assert c.sent_nv()[1]["CONF"] == ""


def test_r_merged_text_appends_only_new_lines():
    c = ctrl(dict(HOST_A11, CONF=FF_1))
    status, res = run(c, [host_item(nac_cmds(freeform_config=FF_1 + "\n" + FF_2))], state="merged")
    assert status == "exit" and res["changed"] is True, res
    assert c.sent_nv()[1]["CONF"] == FF_1 + "\n" + FF_2


# ------------------------------------------------------------------ the helper itself
@pytest.mark.parametrize(
    "value, lines",
    [
        ("", []),
        (FF_1, [FF_1]),
        (FF_1 + "\n", [FF_1]),
        (FF_1 + "\r\n" + FF_2, [FF_1, FF_2]),
        (FF_1 + "\n\n" + FF_2, [FF_1, "", FF_2]),
        ("  " + FF_1, ["  " + FF_1]),
        ([FF_1, FF_2], [FF_1, FF_2]),
        ([FF_1 + "\n" + FF_2], [FF_1, FF_2]),
        ([""], [""]),
        ([], []),
        ("a, b", None),
        (5, None),
        ([1], None),
    ],
)
def test_r_cmds_lines(value, lines):
    assert P.cmds_lines(value) == lines


@pytest.mark.parametrize(
    "value, conf",
    [(FF_1, FF_1), (FF_1 + "\n", FF_1), (FF_1 + "\r\n" + FF_2 + "\n", FF_1 + "\n" + FF_2), ([FF_1 + "\n"], FF_1), ("", "")],
    ids=["text", "text-trailing-break", "text-crlf", "list-entry-trailing-break", "empty"],
)
def test_r_companion_wire_sends_the_lines_never_the_characters_or_a_trailing_break(value, conf):
    assert P.companion_wire("cmds", value) == conf
