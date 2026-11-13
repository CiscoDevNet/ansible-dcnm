"""PVLAN input parity for bpdu_guard and speed, fixed speed and freeform commands."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .helpers import binding_harness as GH
from .helpers import ethernet_controller as E
from .helpers import port_channel_controller as PO
from .helpers import vpc_controller as VH
from .helpers.ethernet_controller import run
from .helpers import member_link_settings as D
from .helpers import vpc_controller as V
from .helpers import binding_harness as G
from .helpers.ethernet_controller import IF7
from .helpers.ethernet_controller import PVLAN
from .helpers.ethernet_controller import SWITCH_IP
from .helpers.ethernet_controller import FakeController
from .helpers.ethernet_controller import measured_preview
from .helpers.ethernet_controller import pvlan_nv
from .helpers.ethernet_controller import preview
from .helpers.ethernet_controller import run as eth_run
from .helpers.port_channel_controller import created
from .helpers.port_channel_controller import po_stanza
from .helpers.port_channel_controller import member_stanza
from .helpers.port_channel_controller import PO as SPEED_FREEFORM_PO
from .helpers.port_channel_controller import PO_HOST
from .helpers.port_channel_controller import PO_ITEM_NAME
from .helpers.port_channel_controller import ASSOC
from .helpers.port_channel_controller import FF_A
from .helpers.port_channel_controller import FF_B
from .helpers.port_channel_controller import HOST_LINES
from .helpers.port_channel_controller import created_with
from .helpers.port_channel_controller import PoLifecycleController
from .helpers.port_channel_controller import DEPLOY
from .helpers.port_channel_controller import PO as SPEED_REVIEW_PO


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_input_parity.py
# PVLAN input parity for bpdu_guard and speed (Ethernet, regular port-channel and vPC).
#
# The regular access/trunk profiles of this module accept a boolean bpdu_guard and any letter case of a speed; mode 'pvlan' refused
# both. Every main() case below goes through the EXISTING harnesses of the three PVLAN families (real argument spec and coercion,
# builders, reconciliation, serialisation; mocks only at the controller boundary) and compares the OUTBOUND request of an alternate
# spelling with the one of the canonical spelling: identical bytes, canonical values. Synthetic fixtures; NOT LIVE TESTED.
# ====================================================================================================
# Copyright (c) 2026 Cisco and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


BPDU_ALIASES = [
    ("true", True), ("true", "TRUE"), ("true", "True"),
    ("false", False), ("false", "FALSE"), ("false", "False"),
    ("no", "NO"), ("no", "No"),
]
SPEED_ALIASES = [
    ("Auto", "auto"), ("Auto", "AUTO"), ("1Gb", "1gb"), ("1Gb", "1GB"), ("10Gb", "10gb"), ("10Gb", "10GB"), ("2.5Gb", "2.5gb"),
]
BPDU_INVALID = ["yes", "on", "off", 1, 0, "1", "", " true", "true ", ["true"], {"v": "true"}]
SPEED_INVALID = ["1000", 1000, "1G", "10gbps", " auto", "auto ", "", True, ["Auto"], "Autonegotiate"]


# ------------------------------------------------------------------ the shared rule
@pytest.mark.parametrize("canonical,alias", BPDU_ALIASES + [("true", "true"), ("false", "false"), ("no", "no")])
def test_bpdu_spellings_have_one_canonical_value(canonical, alias):
    assert P.canonical_native("bpdu", alias) == canonical


@pytest.mark.parametrize("canonical,alias", SPEED_ALIASES + [(v, v) for v in P.SPEED_VALUES])
def test_speed_spellings_resolve_to_the_template_enum(canonical, alias):
    assert P.canonical_native("speed", alias) == canonical


@pytest.mark.parametrize("value", BPDU_INVALID)
def test_bpdu_rejects_everything_else(value):
    assert P.canonical_native("bpdu", value) is None


@pytest.mark.parametrize("value", SPEED_INVALID)
def test_speed_rejects_everything_else(value):
    assert P.canonical_native("speed", value) is None


def test_no_is_a_third_state_and_never_a_boolean():
    assert P.canonical_native("bpdu", "no") == "no" and P.canonical_native("bpdu", False) == "false"


# ------------------------------------------------------------------ Ethernet (int_pvlan_host), real main()
def _eth_sent(state, have, **profile):
    c = E.ctrl(copy.deepcopy(have))
    status, res = E.run(c, [E.pvlan_item(deploy=False, pvlan_mode="host", pvlan_association=E.assoc(2211), **profile)], state=state)
    return status, res, c


@pytest.mark.parametrize("state", ["merged", "replaced"])
@pytest.mark.parametrize("canonical,alias", BPDU_ALIASES)
def test_eth_bpdu_alias_sends_the_canonical_request(state, canonical, alias):
    st_c, _r, c_can = _eth_sent(state, E.HOST_A11, bpdu_guard=canonical, speed="1Gb")
    st_a, res, c_alias = _eth_sent(state, E.HOST_A11, bpdu_guard=alias, speed="1Gb")
    assert st_c == st_a == "exit", res.get("msg")
    assert c_alias.modify_bodies() == c_can.modify_bodies()
    assert c_alias.sent_nv()[1]["BPDUGUARD_ENABLED"] == canonical


@pytest.mark.parametrize("state", ["merged", "replaced"])
@pytest.mark.parametrize("canonical,alias", SPEED_ALIASES)
def test_eth_speed_alias_sends_the_canonical_request(state, canonical, alias):
    have = dict(E.HOST_A11, SPEED="100Mb")  # a current speed none of the aliases names, so every case writes
    st_c, _r, c_can = _eth_sent(state, have, speed=canonical)
    st_a, res, c_alias = _eth_sent(state, have, speed=alias)
    assert st_c == st_a == "exit", res.get("msg")
    assert c_alias.modify_bodies() == c_can.modify_bodies()
    assert c_alias.sent_nv()[1]["SPEED"] == canonical


def test_eth_conversion_from_trunk_host_creates_with_canonical_values():
    def convert(**profile):
        c = E.ctrl(E.trunk_host_nv(), E.TRUNK)
        status, res = E.run(c, [E.pvlan_item(deploy=False, pvlan_mode="host", pvlan_association=E.assoc(2211), **profile)])
        return status, res, c

    st_c, _r, canon = convert(bpdu_guard="true", speed="10Gb")
    st_a, res, alias = convert(bpdu_guard=True, speed="10gb")
    assert st_c == st_a == "exit", res.get("msg")
    assert alias.modify_bodies() == canon.modify_bodies()
    assert (alias.sent_nv()[1]["BPDUGUARD_ENABLED"], alias.sent_nv()[1]["SPEED"]) == ("true", "10Gb")


def test_eth_repeat_with_another_spelling_of_the_current_values_is_a_noop():
    have = dict(E.HOST_A11, BPDUGUARD_ENABLED="true", SPEED="1Gb")
    status, res, c = _eth_sent("merged", have, bpdu_guard=True, speed="1GB")
    assert status == "exit" and res["changed"] is False, res.get("msg")
    assert c.mutating() == []
    # replaced also returns OTHER omitted companions of this HAVE to their defaults, so it writes for both spellings: the alias must
    # produce exactly the canonical request and the same reported change
    _s, canon_res, canon = _eth_sent("replaced", have, bpdu_guard="true", speed="1Gb")
    _s, alias_res, alias = _eth_sent("replaced", have, bpdu_guard="TRUE", speed="1gb")
    assert alias.modify_bodies() == canon.modify_bodies() and alias_res["diff"] == canon_res["diff"]


def test_eth_quoted_no_and_boolean_false_stay_different():
    _s, _r, no = _eth_sent("replaced", E.HOST_A11, bpdu_guard="NO")
    _s, _r, false = _eth_sent("replaced", E.HOST_A11, bpdu_guard=False)
    assert no.sent_nv()[1]["BPDUGUARD_ENABLED"] == "no" and false.sent_nv()[1]["BPDUGUARD_ENABLED"] == "false"


def test_eth_omission_semantics_are_unchanged():
    # merged keeps HAVE ("no", "Auto"), replaced returns the omitted companions to the template defaults (also "no", "Auto")
    have = dict(E.HOST_A11, BPDUGUARD_ENABLED="false", SPEED="10Gb")
    _s, _r, merged = _eth_sent("merged", have, description="parity")
    assert (merged.sent_nv()[1]["BPDUGUARD_ENABLED"], merged.sent_nv()[1]["SPEED"]) == ("false", "10Gb")
    _s, _r, replaced = _eth_sent("replaced", have, description="parity")
    assert (replaced.sent_nv()[1]["BPDUGUARD_ENABLED"], replaced.sent_nv()[1]["SPEED"]) == ("no", "Auto")


@pytest.mark.parametrize("field,value", [("bpdu_guard", v) for v in BPDU_INVALID] + [("speed", v) for v in SPEED_INVALID])
def test_eth_invalid_spelling_fails_before_any_write(field, value):
    status, res, c = _eth_sent("merged", E.HOST_A11, **{field: value})
    assert status == "fail" and field in res["msg"], res.get("msg")
    E.assert_no_writes(c)


@pytest.mark.parametrize("state", ["query", "deleted"])
def test_eth_query_and_deleted_are_unaffected(state):
    c = E.ctrl(dict(E.HOST_A11, BPDUGUARD_ENABLED="TRUE", SPEED="auto"))  # a HAVE spelling the module never sends
    status, res = E.run(c, [{"name": E.IF7, "switch": ["10.0.0.1"]}], state=state)
    assert "bpdu_guard" not in (res.get("msg") or "") and "speed must" not in (res.get("msg") or "")
    if state == "query":
        assert status == "exit" and c.mutating() == []


# ------------------------------------------------------------------ regular port-channel (int_port_channel_pvlan_host), real main()
def _po_create_nv(**profile):
    c = PO.baseline_ctrl()
    status, res = PO.run(c, [PO.po_item(deploy=False, **profile)])
    bodies = [b for call in c.creates() for b in PO._as_list(json.loads(call[2]))]
    return status, res, c, bodies


@pytest.mark.parametrize("canonical,alias", BPDU_ALIASES)
def test_po_create_bpdu_alias_sends_the_canonical_request(canonical, alias):
    st_c, _r, _c, canon = _po_create_nv(bpdu_guard=canonical)
    st_a, res, _c, other = _po_create_nv(bpdu_guard=alias)
    assert st_c == st_a == "exit", res.get("msg")
    assert other == canon and other[0]["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"] == canonical


@pytest.mark.parametrize("canonical,alias", SPEED_ALIASES)
def test_po_create_speed_alias_sends_the_canonical_request(canonical, alias):
    st_c, _r, _c, canon = _po_create_nv(speed=canonical)
    st_a, res, _c, other = _po_create_nv(speed=alias)
    assert st_c == st_a == "exit", res.get("msg")
    assert other == canon and other[0]["interfaces"][0]["nvPairs"]["SPEED"] == canonical


def _po_update(**profile):
    c = PO.created_ctrl()  # HAVE parent: BPDUGUARD_ENABLED "true", SPEED "Auto"
    status, res = PO.run(c, [PO.po_item(deploy=False, **profile)])
    return status, res, c


def test_po_update_alias_sends_the_canonical_request():
    st_c, _r, canon = _po_update(bpdu_guard="false")
    st_a, res, alias = _po_update(bpdu_guard="FALSE")
    st_b, res_b, boolean = _po_update(bpdu_guard=False)
    assert st_c == st_a == st_b == "exit", (res.get("msg"), res_b.get("msg"))
    bodies = [[w[2] for w in c.writes()] for c in (canon, alias, boolean)]
    assert bodies[0] and bodies[0] == bodies[1] == bodies[2]


def test_po_repeat_with_another_spelling_of_the_current_values_is_a_noop():
    for state in ("merged", "replaced"):
        status, res, c = _po_update(**({"bpdu_guard": True, "speed": "AUTO"} if state == "merged" else
                                       {"bpdu_guard": "TRUE", "speed": "auto", "members": [PO.IF7]}))
        assert status == "exit" and res["changed"] is False, (state, res.get("msg"))
        assert c.writes() == [], state


@pytest.mark.parametrize("field,value", [("bpdu_guard", v) for v in BPDU_INVALID] + [("speed", v) for v in SPEED_INVALID])
def test_po_invalid_spelling_fails_before_any_write(field, value):
    status, res, c, _bodies = _po_create_nv(**{field: value})
    assert status == "fail" and field in res["msg"], res.get("msg")
    assert c.writes() == []


# ------------------------------------------------------------------ vPC (int_vpc_pvlan_host), real main()
def _vpc_update(**profile):
    c = VH.created_ctrl()  # HAVE parent: BPDUGUARD_ENABLED "true", SPEED "Auto"
    status, res = VH.run_vpc(c, [VH.vpc_item(deploy=False, **profile)])
    return status, res, c


def test_vpc_update_alias_sends_the_canonical_request():
    st_c, _r, canon = _vpc_update(bpdu_guard="no")
    st_a, res, alias = _vpc_update(bpdu_guard="NO")
    assert st_c == st_a == "exit", res.get("msg")
    assert alias.modifies() and [m[2] for m in alias.modifies()] == [m[2] for m in canon.modifies()]
    assert json.loads(alias.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"] == "no"


def test_vpc_update_boolean_false_is_false_not_no():
    _s, res, boolean = _vpc_update(bpdu_guard=False)
    assert _s == "exit", res.get("msg")
    assert json.loads(boolean.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"] == "false"


def test_vpc_repeat_with_another_spelling_of_the_current_values_is_a_noop():
    status, res, c = _vpc_update(bpdu_guard=True, speed="AUTO")
    assert status == "exit" and res["changed"] is False, res.get("msg")
    assert c.writes() == []


@pytest.mark.parametrize("field,value", [("bpdu_guard", "yes"), ("bpdu_guard", 1), ("speed", "1000"), ("speed", " auto")])
def test_vpc_invalid_spelling_fails_before_any_write(field, value):
    status, res, c = _vpc_update(**{field: value})
    assert status == "fail" and field in res["msg"], res.get("msg")
    assert c.writes() == []


# ------------------------------------------------------------------ the reference: the regular access profile already behaves this way
def test_access_reference_sends_the_same_canonical_values():
    have = GH.build_have(GH.ACCESS, bpdu_guard="no", speed="Auto")
    res, calls = GH.run(GH.base_for(GH.ACCESS, bpdu_guard=True, speed="1GB"), "merged", have=have)
    assert not res.get("failed"), res.get("msg")
    sent = {}
    for nv in GH.request_nvpairs(calls):
        sent.update(nv)
    assert (sent.get("BPDUGUARD_ENABLED"), sent.get("SPEED")) == ("true", "1Gb")


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_parity_duplex_interaction.py
# Interaction of the PVLAN input parity (bpdu_guard / speed spellings) with the fixed-speed duplex inheritance and its guards.
#
# Real main() on the regular port-channel and the vPC, reusing the duplex battery's own fixtures and helpers (measured previews, retargeted).
# An alias spelling must produce exactly the canonical request, must not look like a speed change to the combined speed + duplex guard, and
# must not hide a real combined change or an F-A refusal. Synthetic controller doubles; NOT LIVE TESTED.
# ====================================================================================================
# Copyright (c) 2026 Cisco and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


COMBINED = "speed and duplex cannot change in the same request"
FA = "needs a fixed speed"
BPDU_ALIAS = {"true": True, "false": False, "no": "NO"}


def _po_bpdu_alias(ctrl):
    return BPDU_ALIAS[ctrl.detail["Port-channel10"]["nvPairs"].get("BPDUGUARD_ENABLED", "true")]


def _vpc_bpdu_alias(ctrl):
    return BPDU_ALIAS[ctrl.parents[V.VPC]["nvPairs"].get("BPDUGUARD_ENABLED", "true")]


# ------------------------------------------------------------------ regular port-channel
def _po_apply(**profile):
    ctrl = D._created_po()  # HAVE speed 1Gb (fixed), duplex auto
    ctrl.previews = [D._po_preview("apply_preview")]
    status, result = run(ctrl, [D._po_cfg(duplex="full", **profile)], state="merged")
    return status, result, ctrl


def test_po_duplex_apply_with_alias_spellings_sends_the_canonical_request():
    st_c, _r, canon = _po_apply(speed="1Gb", bpdu_guard="true")
    st_a, res, alias = _po_apply(speed="1GB", bpdu_guard=True)
    assert st_c == st_a == "exit", res.get("msg")
    assert alias.bulk_bodies() == canon.bulk_bodies() and len(alias.deploys()) == 1
    sent = alias.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]
    assert (sent["SPEED"], sent["PORT_DUPLEX_MODE"], sent["BPDUGUARD_ENABLED"]) == ("1Gb", "full", "true")
    assert COMBINED not in str(res.get("msg", "")), "restating the speed in another spelling is not a speed change"


def test_po_repeat_with_alias_spellings_writes_nothing():
    ctrl = D._created_po(duplex="full")
    ctrl.previews = [D._po_preview("after_apply_preview")]
    status, result = run(ctrl, [D._po_cfg(duplex="full", speed="1gb", bpdu_guard=_po_bpdu_alias(ctrl))], state="merged")
    assert status == "exit" and result["changed"] is False and ctrl.writes() == [], result.get("msg")


def test_po_real_combined_change_in_alias_spelling_is_still_refused_before_any_write():
    ctrl = D._created_po()
    status, result = run(ctrl, [D._po_cfg(duplex="full", speed="10GB")], state="merged")
    assert status == "fail" and COMBINED in result["msg"], result.get("msg")
    assert ctrl.writes() == [] and ctrl.bulk_bodies() == [] and ctrl.deploys() == []


def test_po_f_a_with_an_alias_auto_is_still_refused_before_any_write():
    ctrl = D._created_po(duplex="full")
    status, result = run(ctrl, [D._po_cfg(speed="AUTO")], state="merged")
    assert status == "fail" and FA in result["msg"], result.get("msg")
    assert ctrl.writes() == [] and ctrl.bulk_bodies() == []


# ------------------------------------------------------------------ vPC, both peers
def _vpc_apply(**profile):
    ctrl = D._vpc_ctrl()  # HAVE speed 1Gb (fixed), duplex auto
    D._queue(ctrl, "after_withdraw_preview", "apply_preview")
    status, res = V.run_vpc(ctrl, [D._vpc_item(duplex="full", **profile)], state="merged")
    return status, res, ctrl


def test_vpc_duplex_apply_with_alias_spellings_sends_the_canonical_request():
    st_c, _r, canon = _vpc_apply(speed="1Gb", bpdu_guard="true")
    st_a, res, alias = _vpc_apply(speed="1gB", bpdu_guard=True)
    assert st_c == st_a == "exit", res.get("msg")
    assert [m[2] for m in alias.modifies()] == [m[2] for m in canon.modifies()] and len(alias.deploys()) == 1
    sent = json.loads(alias.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]
    assert (sent["SPEED"], sent["PORT_DUPLEX_MODE"], sent["BPDUGUARD_ENABLED"]) == ("1Gb", "full", "true")


def test_vpc_repeat_with_alias_spellings_writes_nothing():
    ctrl = D._vpc_ctrl(duplex="full")
    for alias in ("SN-A", "SN-B"):
        ctrl.vpc_previews[D.PEER[alias][0]] = [D._vpc_preview(alias, "after_apply_preview")]
    status, res = V.run_vpc(ctrl, [D._vpc_item(duplex="full", speed="1GB", bpdu_guard=_vpc_bpdu_alias(ctrl))], state="merged")
    assert status == "exit" and res["changed"] is False and ctrl.writes() == [], res.get("msg")


def test_vpc_real_combined_change_in_alias_spelling_is_still_refused_before_any_write():
    ctrl = D._vpc_ctrl()
    status, res = V.run_vpc(ctrl, [D._vpc_item(duplex="full", speed="10gb")], state="merged")
    assert status == "fail" and COMBINED in res["msg"], res.get("msg")
    assert ctrl.writes() == [] and ctrl.deploys() == []


def test_vpc_f_a_with_an_alias_auto_is_still_refused_before_any_write():
    ctrl = D._vpc_ctrl(duplex="full")
    status, res = V.run_vpc(ctrl, [D._vpc_item(speed="auto")], state="merged")
    assert status == "fail" and FA in res["msg"], res.get("msg")
    assert ctrl.writes() == []


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_speed_freeform.py
# RC1: a non-Auto speed on the Ethernet, port-channel and vPC PVLAN parents, and freeform commands on the port-channel (`cmds`) and
# the vPC (`peer1_cmds`/`peer2_cmds`).
#
# NOT LIVE TESTED. Real main(); only the external boundary is mocked, through the EXISTING harnesses. Every preview below is SYNTHETIC,
# written BY HAND from the captured templates (int_pvlan_host 354-361, int_port_channel_pvlan_host 464-471/507-564, int_vpc_pvlan_host
# 472-499/640-706, int_vpc_pvlan_po 258-269/323-325) and from the captured interface_utility.findInheritedCommandsInPOFF. Measured: only
# SPEED "1Gb" -> `speed 1000` (regular int_trunk_host). Inferred: the other speed keywords, the `no negotiate auto` the controller adds by
# device capability, the identity of adjustIntfFreeformConfig for a top-level command, and the form of every withdrawal line.
#
# The REFERENCE section drives the regular port-channel/vPC parents (trunk, dot1q) through the same main() and reads the request the
# module itself sends, so the PVLAN rule is compared with the module's own regular behaviour, not with a description of it.
# ====================================================================================================
# ====================================================================================== reference: the module's regular rule
def _request(calls):
    found = []
    G._collect_policies([c["payload"] for c in G.writes(calls)], found)
    return found


def _regular(parent, state, have_extra, want_extra):
    """(written, nvPairs) of one regular parent run: HAVE built by the module from `have_extra`, WANT = base + `want_extra`."""
    have = G.build_have(parent, **have_extra) if have_extra is not None else None
    want = G.base_for(parent, **want_extra)
    for key in [k for k, v in want.items() if v is G._UNSET]:
        want.pop(key)
    result, calls = G.run(want, state, have=have, parent=parent)
    assert not result.get("failed"), result.get("msg")
    found = _request(calls)
    return bool(G.split_calls(calls)["updates"]), (found[0]["interfaces"][0]["nvPairs"] if found else None)


OMIT = G._UNSET


@pytest.mark.parametrize("parent", [G.PC_TRUNK, G.PC_DOT1Q])
def test_reference_regular_port_channel_speed_and_cmds_rule(parent):
    """The regular rule PVLAN reuses: create carries SPEED/CONF; merged keeps an omitted field; replaced returns it to Auto / ''."""
    written, nv = _regular(parent, "merged", None, {"speed": "10Gb", "cmds": [FF_A]})
    assert written and nv["SPEED"] == "10Gb" and nv["CONF"] == FF_A
    # merged, both omitted: nothing to change
    written, nv = _regular(parent, "merged", {"speed": "10Gb", "cmds": [FF_A]}, {})
    assert not written
    # replaced, both omitted: SPEED back to Auto, CONF cleared
    written, nv = _regular(parent, "replaced", {"speed": "10Gb", "cmds": [FF_A]}, {})
    assert written and nv["SPEED"].lower() == "auto" and nv["CONF"] == ""
    # merged with a new command: HAVE's command kept, the new one added
    written, nv = _regular(parent, "merged", {"cmds": [FF_A]}, {"cmds": [FF_B]})
    assert written and sorted(nv["CONF"].split("\n")) == sorted([FF_A, FF_B])
    # replaced with an explicit list: exactly that list
    written, nv = _regular(parent, "replaced", {"cmds": [FF_A]}, {"cmds": [FF_B]})
    assert written and nv["CONF"] == FF_B


def test_reference_regular_merged_repeats_a_command_already_held_while_pvlan_does_not():
    """The ONE documented difference: the regular merged rule concatenates HAVE and WANT (dcnm_intf_merge_want_and_have), so a
    request that repeats a held command next to a new one sends it twice; the PVLAN rule (the Ethernet `cmds` precedent) appends only
    what HAVE does not hold."""
    written, nv = _regular(G.PC_DOT1Q, "merged", {"cmds": [FF_A]}, {"cmds": [FF_A, FF_B]})
    assert written and nv["CONF"].split("\n").count(FF_A) == 2
    assert P.freeform_merged(FF_A, [FF_A, FF_B]).split("\n") == [FF_A, FF_B]


def test_reference_regular_vpc_peer_cmds_follow_the_controller_peer():
    """Regular vPC (dot1q): peerN_cmds of the playbook land on the controller's peer that owns the switch (reversed order)."""
    result, calls = G.run_configs([dict(G.cfg_for(G.VPC_DOT1Q, G.base_for(G.VPC_DOT1Q, peer1_cmds=[FF_A], peer2_cmds=[FF_B])),
                                        switch=[G.SWITCH_IP, G.PEER_IP])], "merged")
    assert not result.get("failed"), result.get("msg")
    nv = _request(calls)[0]["interfaces"][0]["nvPairs"]
    assert (nv["PEER1_PO_CONF"], nv["PEER2_PO_CONF"]) == (FF_B, FF_A)


# ====================================================================================== PVLAN rule (helper), same table as the reference
def _po_have(**extra):
    raw = {"pvlan_mode": "host", "members": [IF7], "pvlan_association": ASSOC}
    raw.update(extra)
    return P.po_host_nvpairs(raw, SPEED_FREEFORM_PO)


def _po_want(**extra):
    raw = {"pvlan_mode": "host", "members": [IF7], "pvlan_association": ASSOC}
    raw.update(extra)
    return raw


@pytest.mark.parametrize(
    "state, have, want, written, speed, conf",
    [
        ("merged", {}, {"speed": "10Gb", "cmds": [FF_A]}, True, "10Gb", [FF_A]),
        ("merged", {"speed": "10Gb", "cmds": [FF_A]}, {}, False, "10Gb", [FF_A]),
        ("replaced", {"speed": "10Gb", "cmds": [FF_A]}, {}, True, "Auto", []),
        ("replaced", {"speed": "10Gb", "cmds": [FF_A]}, {"cmds": []}, True, "Auto", []),
        ("merged", {"cmds": [FF_A]}, {"cmds": [FF_B]}, True, "Auto", [FF_A, FF_B]),
        ("merged", {"cmds": [FF_A]}, {"cmds": []}, False, "Auto", [FF_A]),
        ("merged", {"cmds": [FF_A, FF_B]}, {"cmds": [FF_B, FF_A]}, False, "Auto", [FF_A, FF_B]),
        ("replaced", {"cmds": [FF_A]}, {"cmds": [FF_B]}, True, "Auto", [FF_B]),
        ("replaced", {"cmds": [FF_A, FF_B]}, {"cmds": [FF_B, FF_A]}, False, "Auto", [FF_A, FF_B]),
        ("replaced", {"speed": "10Gb"}, {"speed": "1Gb"}, True, "1Gb", []),
    ],
)
def test_port_channel_rule_matches_the_regular_one(state, have, want, written, speed, conf):
    out = P.reconcile_po(state, _po_want(**want), SPEED_FREEFORM_PO, PO_HOST, _po_have(**have))
    assert out["blocked"] == [], out["blocked"]
    assert out["update"] is written
    assert out["nv"]["SPEED"] == speed and sorted(P.freeform_lines(out["nv"]["CONF"])) == sorted(conf)
    if written:
        assert set(out["changed"]) <= {"SPEED", "CONF"}, out["changed"]


def _vpc_legs(raw):
    return P.vpc_pair_view(raw, V.PAIR, [V.SN1, V.SN2])


def _vpc_raw(**extra):
    raw = {"pvlan_mode": "host", "peer1_members": [V.M1], "peer2_members": [V.M2], "peer1_pcid": 10, "peer2_pcid": 10,
           "pvlan_association": [{"primary_vlan": V.PRIMARY, "secondary_vlan": V.SECONDARY}]}
    raw.update(extra)
    return raw


def test_vpc_per_peer_cmds_follow_the_controller_peer_and_speed_is_shared():
    raw = _vpc_raw(peer1_cmds=[FF_A], peer2_cmds=[FF_B], speed="10Gb")
    # playbook switch[0] is the controller's SECOND serial: peer1_cmds belong to PEER2
    legs = P.vpc_pair_view(raw, V.PAIR, [V.SN2, V.SN1])
    nv = P.vpc_host_nvpairs(raw, "vPC10", legs)
    assert (nv["PEER1_PO_CONF"], nv["PEER2_PO_CONF"]) == (FF_B, FF_A) and nv["SPEED"] == "10Gb"
    for index, conf in ((0, FF_B), (1, FF_A)):
        child = P.vpc_leg_po_nv(nv, index, "vPC10")
        assert child["CONF"] == conf and child["SPEED"] == "10Gb"
        assert {"speed 10000", conf} <= P.render(P.VPC_PO_POLICY, child).scalars


@pytest.mark.parametrize(
    "state, have, want, written, conf1, conf2",
    [
        ("merged", {"peer1_cmds": [FF_A], "peer2_cmds": [FF_A]}, {}, False, [FF_A], [FF_A]),
        ("merged", {"peer1_cmds": [FF_A], "peer2_cmds": [FF_A]}, {"peer1_cmds": [FF_B], "peer2_cmds": [FF_B]}, True, [FF_A, FF_B],
         [FF_A, FF_B]),
        ("replaced", {"peer1_cmds": [FF_A], "peer2_cmds": [FF_B]}, {}, True, [], []),
        ("replaced", {"peer1_cmds": [FF_A], "peer2_cmds": [FF_B]}, {"peer1_cmds": [FF_B], "peer2_cmds": [FF_A]}, True, [FF_B], [FF_A]),
        ("replaced", {"peer1_cmds": [FF_A], "peer2_cmds": [FF_B]}, {"peer1_cmds": [FF_A], "peer2_cmds": [FF_B]}, False, [FF_A], [FF_B]),
    ],
)
def test_vpc_freeform_rule_matches_the_regular_one(state, have, want, written, conf1, conf2):
    have_nv = P.vpc_host_nvpairs(_vpc_raw(**have), "vPC10", _vpc_legs(_vpc_raw(**have)))
    out = P.reconcile_vpc(state, _vpc_raw(**want), "vPC10", _vpc_legs(_vpc_raw(**want)), P.VPC_HOST_POLICY, have_nv)
    assert out["blocked"] == [], out["blocked"]
    assert out["update"] is written
    assert P.freeform_lines(out["nv"]["PEER1_PO_CONF"]) == conf1 and P.freeform_lines(out["nv"]["PEER2_PO_CONF"]) == conf2


def test_vpc_one_peer_freeform_change_stays_a_refused_unilateral_update():
    """RB2 contract kept: an update that reaches one peer only is refused unless it is membership (MM-B). A per-peer freeform change
    is a per-peer key, exactly like a per-peer description."""
    have_nv = P.vpc_host_nvpairs(_vpc_raw(), "vPC10", _vpc_legs(_vpc_raw()))
    out = P.reconcile_vpc("merged", _vpc_raw(peer1_cmds=[FF_A]), "vPC10", _vpc_legs(_vpc_raw(peer1_cmds=[FF_A])), P.VPC_HOST_POLICY, have_nv)
    assert out["update"] is False and any("changes only peer 1" in b and "PEER1_PO_CONF" in b for b in out["blocked"]), out["blocked"]


# ====================================================================================== refusals before any request
@pytest.mark.parametrize(
    "cmds, needle",
    [
        (["switchport mode trunk"], "copies to every member"),
        (["mtu 1500"], "copies to every member"),
        (["speed 1000"], "copies to every member"),
        (["no negotiate auto"], "copies to every member"),
        (["load-interval counter 1 30"], "copies to every member"),
        (["storm-control broadcast level 5.00"], "copies to every member"),
        (["cts manual"], "copies to every member"),
        (["channel-group 10 mode active"], "'channel-group' command"),
        (["vpc 10"], "'vpc' command"),
        (["no shutdown"], "'shutdown' command"),
        (["description x"], "'description' command"),
        (["no lacp suspend-individual"], "'lacp' command"),
        (["service-policy type queuing output Q"], "'service-policy' command"),
        (["ip port access-group A in"], "'ip port access-group' command"),
        (["interface Ethernet1/9"], "'interface' command"),
        (["  sgt 10"], "indented sub-command"),
        # PO-VPC text parity: a list entry holding a line break is checked line by line (each line must pass); a text is accepted the
        # same way, so these used to be "one command" / "list of strings" refusals and are now the per-line ones below.
        (["logging event port link-status\n  sgt 10"], "indented sub-command"),
        ("logging event port link-status\r\nswitchport mode trunk", "copies to every member"),
        ("no ip redirects, x", "must not contain a comma"),
        (5, "list of strings"),
        ([""], "is empty"),
    ],
)
def test_freeform_rule_refuses_before_any_request(cmds, needle):
    errors = P.po_freeform_errors("cmds", cmds)
    assert any(needle in e for e in errors), errors
    assert P.po_not_implemented({"pvlan_mode": "host", "cmds": cmds}) and P.vpc_not_implemented(
        {"pvlan_mode": "host", "peer1_pcid": 10, "peer2_pcid": 10, "peer1_cmds": cmds}, "vPC10")


def test_accepted_freeform_and_known_speeds():
    assert P.po_freeform_errors("cmds", [FF_A, FF_B, "no ip redirects"]) == []
    for value, keyword in P.SPEED_CLI.items():
        assert P.render(PO_HOST, _po_have(speed=value)).scalars >= {"speed %s" % keyword}
    assert P.SPEED_CLI_MEASURED == frozenset(("1Gb",)) and P.SPEED_CLI["1Gb"] == "1000"
    assert P.native_companion_errors({"speed": "7Gb"}, P.PO_NATIVE_COMPANIONS) == ["speed must be one of: %s" % ", ".join(P.SPEED_VALUES)]


def test_po_refusal_reaches_main_before_any_request():
    ctrl = created("host", HOST_LINES, pvlan_association=ASSOC)
    status, result = run(ctrl, [{"name": PO_ITEM_NAME, "type": "pc", "switch": [SWITCH_IP], "deploy": True,
                                 "profile": {"mode": "pvlan", "pvlan_mode": "host", "cmds": ["mtu 1500"]}}], state="merged")
    assert status == "fail" and "copies to every member" in result["msg"] and ctrl.writes() == []


def test_a_stored_freeform_outside_the_rule_is_refused_not_rewritten():
    have = _po_have()
    have["CONF"] = "cts manual\n  sgt 10"
    out = P.reconcile_po("merged", _po_want(description="x"), SPEED_FREEFORM_PO, PO_HOST, have)
    assert not P.render(PO_HOST, out["nv"]).modeled  # the destination is unmodeled: refused before any write
    vhave = P.vpc_host_nvpairs(_vpc_raw(), "vPC10", _vpc_legs(_vpc_raw()))
    vhave["PEER2_PO_CONF"] = "  sgt 10"
    vout = P.reconcile_vpc("merged", _vpc_raw(), "vPC10", _vpc_legs(_vpc_raw()), P.VPC_HOST_POLICY, vhave)
    assert any("PEER2_PO_CONF" in b and "indented" in b for b in vout["blocked"]), vout["blocked"]


# ====================================================================================== the capability line
def _entry(running, expected):
    return {"runningConfig": ["!Command: show running-config"] + running, "expectedConfig": expected}


def test_the_capability_line_is_adopted_only_next_to_a_speed_line():
    voc = P.transition_vocabulary((PO_HOST, _po_have(admin_state=False)), (PO_HOST, _po_have(speed="10Gb", admin_state=False)))
    want = P.render(PO_HOST, _po_have(speed="10Gb", admin_state=False))
    stanza = po_stanza("host", HOST_LINES)
    with_speed = stanza + ["  speed 10000", "  no negotiate auto"]
    decision, problems = P.assess_target(["speed 10000", "no negotiate auto"], _entry(stanza, with_speed), "port-channel10", want, voc)
    assert decision == "deploy", problems
    # the controller without the line (capability "on"/"both") is the plain speed model
    decision, problems = P.assess_target(["speed 10000"], _entry(stanza, stanza + ["  speed 10000"]), "port-channel10", want, voc)
    assert decision == "deploy", problems
    # without a speed line the same controller line is a disagreement
    auto = P.render(PO_HOST, _po_have(admin_state=False))
    decision, problems = P.assess_target(["no negotiate auto"], _entry(stanza, stanza + ["  no negotiate auto"]), "port-channel10", auto, voc)
    assert decision == "refuse" and "disagrees with the intended state" in problems[0]
    # nothing else is ever adopted
    decision, problems = P.assess_target(["speed 10000", "duplex full"], _entry(stanza, with_speed + ["  duplex full"]), "port-channel10",
                                         want, voc)
    assert decision == "refuse"


# ====================================================================================== port-channel through main()
def _po_cfg(**profile):
    prof = {"mode": "pvlan", "pvlan_mode": "host"}
    prof.update(profile)
    return {"name": PO_ITEM_NAME, "type": "pc", "switch": [SWITCH_IP], "deploy": True, "profile": prof}


def test_po_creation_with_speed_and_freeform_payload_and_gate():
    _ctrl, result = created_with(["speed 10000", "no negotiate auto", FF_A], ["speed 10000", "no negotiate auto"], speed="10Gb", cmds=[FF_A])
    assert result["pvlan_gate"][0]["targets"][SPEED_FREEFORM_PO] == "deploy"
    nv = result["created_nv"]
    assert nv["SPEED"] == "10Gb" and nv["CONF"] == FF_A and nv["PVLAN_MODE"] == "host"


def _po_update_preview(old_po, new_po, old_member, new_member, pend):
    return preview(pend, running=old_po + old_member, expected=new_po + new_member)


def test_po_merged_speed_and_freeform_update_deploys_and_the_repeat_writes_nothing():
    ctrl = created("host", HOST_LINES, pvlan_association=ASSOC)
    have = copy.deepcopy(ctrl.detail[SPEED_FREEFORM_PO]["nvPairs"])
    old_po, old_m = po_stanza("host", HOST_LINES), member_stanza("host", HOST_LINES)
    new_po = old_po + ["  speed 10000", "  no negotiate auto", "  " + FF_A]
    new_m = old_m + ["  speed 10000", "  no negotiate auto"]
    pend = ["interface port-channel10", "  speed 10000", "  no negotiate auto", "  " + FF_A,
            "interface ethernet1/7", "  speed 10000", "  no negotiate auto"]
    ctrl.previews = [_po_update_preview(old_po, new_po, old_m, new_m, pend)]
    status, result = run(ctrl, [_po_cfg(speed="10Gb", cmds=[FF_A])], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    sent = ctrl.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]
    assert sent["SPEED"] == "10Gb" and sent["CONF"] == FF_A
    for key in ("ASSOCIATION_LIST", "MEMBER_INTERFACES", "ADMIN_STATE", "DESC", "MTU"):
        assert sent[key] == have[key], key
    assert result["diff"][0]["merged"][0]["interfaces"][0]["nvPairs"] == {"SPEED": "10Gb", "CONF": FF_A}
    assert result["pvlan_gate"][0]["targets"][SPEED_FREEFORM_PO] == "deploy" and len(ctrl.deploys()) == 1
    # the same request again: nothing to write or deploy
    ctrl.next_invocation()
    ctrl.calls = []
    status, result = run(ctrl, [_po_cfg(speed="10Gb", cmds=[FF_A])], state="merged")
    assert status == "exit" and result["changed"] is False, result
    assert ctrl.writes() == [] and ctrl.deploys() == []


def test_po_merged_omission_keeps_speed_and_freeform():
    ctrl, _r = created_with(["speed 10000", FF_A], ["speed 10000"], speed="10Gb", cmds=[FF_A])
    lines = HOST_LINES
    run_cfg = po_stanza("host", lines) + ["  speed 10000", "  " + FF_A] + member_stanza("host", lines) + ["  speed 10000"]
    exp = list(run_cfg)
    exp.insert(1, "  description D1")
    ctrl.previews = [preview(["interface port-channel10", "  description D1"], running=run_cfg, expected=exp)]
    status, result = run(ctrl, [_po_cfg(description="D1")], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    sent = ctrl.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]
    assert sent["SPEED"] == "10Gb" and sent["CONF"] == FF_A and sent["DESC"] == "D1"
    assert result["diff"][0]["merged"][0]["interfaces"][0]["nvPairs"] == {"DESC": "D1"}


def test_po_replaced_omission_withdraws_speed_and_freeform_and_the_pending_must_carry_it():
    base = dict(members=[IF7], admin_state=False)
    lines = HOST_LINES
    run_po = po_stanza("host", lines) + ["  speed 10000", "  " + FF_A]
    run_m = member_stanza("host", lines) + ["  speed 10000"]
    pend = ["interface port-channel10", "  no speed 10000", "  no " + FF_A, "interface ethernet1/7", "  no speed 10000"]
    ctrl, _r = created_with(["speed 10000", FF_A], ["speed 10000"], speed="10Gb", cmds=[FF_A])
    ctrl.previews = [preview(pend, running=run_po + run_m, expected=po_stanza("host", lines) + member_stanza("host", lines))]
    status, result = run(ctrl, [_po_cfg(pvlan_association=ASSOC, **base)], state="replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    sent = ctrl.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]
    assert sent["SPEED"] == "Auto" and sent["CONF"] == ""
    assert result["pvlan_gate"][0]["targets"][SPEED_FREEFORM_PO] == "deploy"
    # the same withdrawal with the freeform removal missing from the pending: refused before any deploy
    ctrl, _r = created_with(["speed 10000", FF_A], ["speed 10000"], speed="10Gb", cmds=[FF_A])
    short = [x for x in pend if FF_A not in x]
    ctrl.previews = [preview(short, running=run_po + run_m, expected=po_stanza("host", lines) + member_stanza("host", lines))]
    status, result = run(ctrl, [_po_cfg(pvlan_association=ASSOC, **base)], state="replaced")
    assert status == "fail" and "withdrawal of %r is absent from the pending" % FF_A in result["msg"] and ctrl.deploys() == []


def test_po_member_without_the_inherited_speed_in_its_pending_is_refused():
    """The member's speed arrives through the parent's 'Inherited Commands' child (HOST 517-518). Whether NX-OS then needs a member
    pending line is NOT measured; when the controller expects it but the pending does not carry it, the gate refuses (fail-closed)."""
    ctrl = created("host", HOST_LINES, pvlan_association=ASSOC)
    old_po, old_m = po_stanza("host", HOST_LINES), member_stanza("host", HOST_LINES)
    pend = ["interface port-channel10", "  speed 10000"]
    ctrl.previews = [_po_update_preview(old_po, old_po + ["  speed 10000"], old_m, old_m + ["  speed 10000"], pend)]
    status, result = run(ctrl, [_po_cfg(speed="10Gb")], state="merged")
    assert status == "fail" and "Ethernet1/7" in result["msg"] and ctrl.deploys() == []


# ====================================================================================== vPC through main()
def _vpc_speed_ff_preview(serial, port, conf):
    po = V.po_stanza() + ["  speed 10000", "  " + conf]
    member = V.member_after(port) + ["  speed 10000"]
    pend = ["interface port-channel10", "  speed 10000", "  " + conf, "interface %s" % port.lower(), "  speed 10000"]
    return preview(pend, serial=serial, running=V.po_stanza() + V.member_after(port), expected=po + member)


def test_vpc_merged_speed_and_both_peer_freeform_update_maps_each_peer_and_deploys():
    ctrl = V.created_ctrl()
    # the vPC preflight reads the CURRENT (converged) state first, then the gate reads the post-write preview
    ctrl.vpc_previews[V.SN1] = [V.converged_preview(V.SN1, V.M1), _vpc_speed_ff_preview(V.SN1, V.M1, FF_A)]
    ctrl.vpc_previews[V.SN2] = [V.converged_preview(V.SN2, V.M2), _vpc_speed_ff_preview(V.SN2, V.M2, FF_B)]
    status, result = V.run_vpc(ctrl, [V.vpc_item(speed="10Gb", peer1_cmds=[FF_A], peer2_cmds=[FF_B])], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    sent = [json.loads(c[2]) for c in ctrl.modifies()][0][0]["interfaces"][0]["nvPairs"]
    assert sent["SPEED"] == "10Gb" and (sent["PEER1_PO_CONF"], sent["PEER2_PO_CONF"]) == (FF_A, FF_B)
    assert ctrl.deploys()
    # the repeat: nothing to write
    ctrl.next_invocation()
    ctrl.vpc_previews[V.SN1] = [V.preview([], serial=V.SN1, running=V.po_stanza() + ["  speed 10000", "  " + FF_A] + V.member_after(V.M1)
                                          + ["  speed 10000"], expected=V.po_stanza() + ["  speed 10000", "  " + FF_A]
                                          + V.member_after(V.M1) + ["  speed 10000"])]
    ctrl.vpc_previews[V.SN2] = [V.preview([], serial=V.SN2, running=V.po_stanza() + ["  speed 10000", "  " + FF_B] + V.member_after(V.M2)
                                          + ["  speed 10000"], expected=V.po_stanza() + ["  speed 10000", "  " + FF_B]
                                          + V.member_after(V.M2) + ["  speed 10000"])]
    before = len(ctrl.writes())
    status, result = V.run_vpc(ctrl, [V.vpc_item(speed="10Gb", peer1_cmds=[FF_A], peer2_cmds=[FF_B])], state="merged")
    assert status == "exit" and result["changed"] is False, result
    assert len(ctrl.writes()) == before


def test_vpc_refusal_reaches_main_before_any_request():
    ctrl = V.created_ctrl()
    status, result = V.run_vpc(ctrl, [V.vpc_item(peer1_cmds=["vpc orphan-port suspend"], peer2_cmds=[FF_B])], state="merged")
    assert status == "fail" and "'vpc' command" in result["msg"] and ctrl.writes() == []


# ====================================================================================== Ethernet through main()
def test_ethernet_speed_update_deploys_with_the_adopted_capability_line():
    """int_pvlan_host already carried `speed` in its payload; RC1 models the line, so a non-Auto speed is no longer refused as
    unmodeled. The device stanza is the MEASURED converged G6-M0b one; the speed lines are SYNTHETIC (template 354-361)."""
    base = measured_preview("G6-M0b", "post")
    entry = copy.deepcopy(base["DATA"][0])
    idx = next(i for i, x in enumerate(entry["expectedConfig"]) if x.strip().lower() == "interface ethernet1/7")
    entry["expectedConfig"][idx + 1:idx + 1] = ["  speed 10000", "  no negotiate auto"]
    entry["pendingConfig"] = ["interface ethernet1/7", "  speed 10000", "  no negotiate auto"]
    entry["status"] = "Out-of-Sync"
    ctrl = FakeController()
    ctrl.detail[IF7] = {"policy": PVLAN, "nvPairs": pvlan_nv("G6-M0b")}
    ctrl.previews = [{"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [entry]}]
    status, result = eth_run(ctrl, [{"name": IF7, "type": "eth", "switch": [SWITCH_IP], "deploy": True,
                                     "profile": {"mode": "pvlan", "pvlan_mode": "trunk promiscuous", "speed": "10Gb"}}])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.requests("POST", "/rest/globalInterface/deploy")


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_speed_freeform_rc2.py
# Three low-severity review findings on speed and freeform handling.
#
# NOT LIVE TESTED. Real main() through the EXISTING harnesses, with the SYNTHETIC template-predicted previews of the speed/freeform
# tests.
#   1 - a command repeated inside ONE freeform request is kept once, in the order of its first appearance (creation, merged, replaced,
#       idempotency; port-channel and vPC);
#   2 - the port-channel post-deploy intent readback compares SPEED and CONF, with the existing normalization; a difference is
#       reported, never retried or rewritten;
#   3 - the INFERRED withdrawal of an adopted `no negotiate auto` when the speed returns to Auto: deployed only when the pending
#       carries it (as `negotiate auto`), refused before any deploy otherwise. This documents existing behaviour; it is not a
#       behaviour change.
# ====================================================================================================
# ====================================================================================== repeated commands inside one request
def test_freeform_request_keeps_each_command_once_in_first_appearance_order():
    assert P.freeform_request([FF_B, FF_A, FF_B, " " + FF_A, FF_A + " "]) == [FF_B, FF_A]
    assert P.freeform_request([]) == [] and P.freeform_request(None) == []


@pytest.mark.parametrize(
    "state, have, want, conf",
    [
        ("merged", None, [FF_A, FF_B, FF_A], [FF_A, FF_B]),            # creation
        ("merged", [FF_A], [FF_B, FF_B, FF_A], [FF_A, FF_B]),          # merged appends the new command once
        ("replaced", [FF_A], [FF_B, FF_A, FF_B], [FF_B, FF_A]),        # replaced: exact list, first appearance order
        ("replaced", None, [FF_B, FF_B], [FF_B]),                      # creation through replaced
    ],
)
def test_port_channel_request_duplicates_are_stored_once(state, have, want, conf):
    have_nv = _po_have(cmds=have) if have is not None else None
    out = P.reconcile_po(state, _po_want(cmds=want), SPEED_REVIEW_PO, PO_HOST if have_nv else None, have_nv)
    assert out["blocked"] == [], out["blocked"]
    assert P.freeform_lines(out["nv"]["CONF"]) == conf
    # idempotency: the same request against the intent it produced writes nothing
    again = P.reconcile_po(state, _po_want(cmds=want), SPEED_REVIEW_PO, PO_HOST, out["nv"])
    assert again["blocked"] == [] and again["update"] is False


def test_vpc_request_duplicates_are_stored_once_per_peer_and_repeat_is_a_no_op():
    raw = _vpc_raw(peer1_cmds=[FF_A, FF_A], peer2_cmds=[FF_B, FF_A, FF_B])
    nv = P.vpc_host_nvpairs(raw, "vPC10", _vpc_legs(raw))
    assert (P.freeform_lines(nv["PEER1_PO_CONF"]), P.freeform_lines(nv["PEER2_PO_CONF"])) == ([FF_A], [FF_B, FF_A])
    for state in ("merged", "replaced"):
        out = P.reconcile_vpc(state, raw, "vPC10", _vpc_legs(raw), P.VPC_HOST_POLICY, nv)
        assert out["blocked"] == [] and out["update"] is False, (state, out["blocked"], out["changed"])
    have_raw = _vpc_raw(peer1_cmds=[FF_A], peer2_cmds=[FF_A])
    have = P.vpc_host_nvpairs(have_raw, "vPC10", _vpc_legs(have_raw))
    want = _vpc_raw(peer1_cmds=[FF_B, FF_B], peer2_cmds=[FF_B, FF_A, FF_B])
    out = P.reconcile_vpc("merged", want, "vPC10", _vpc_legs(want), P.VPC_HOST_POLICY, have)
    assert out["blocked"] == [] and out["update"] is True
    assert P.freeform_lines(out["nv"]["PEER1_PO_CONF"]) == [FF_A, FF_B] and P.freeform_lines(out["nv"]["PEER2_PO_CONF"]) == [FF_A, FF_B]


def test_po_merged_request_with_a_repeated_command_sends_it_once_through_main_and_the_repeat_writes_nothing():
    ctrl, _r = created_with([], [])
    old_po, old_m = po_stanza("host", HOST_LINES), member_stanza("host", HOST_LINES)
    ctrl.previews = [_po_update_preview(old_po, old_po + ["  " + FF_A], old_m, old_m, ["interface port-channel10", "  " + FF_A])]
    status, result = run(ctrl, [_po_cfg(cmds=[FF_A, FF_A])], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]["CONF"] == FF_A
    ctrl.next_invocation()
    ctrl.calls = []
    status, result = run(ctrl, [_po_cfg(cmds=[FF_A, FF_A])], state="merged")
    assert status == "exit" and result["changed"] is False, result
    assert ctrl.writes() == [] and ctrl.deploys() == []


# ====================================================================================== L2: Po post-deploy readback of SPEED / CONF
def test_po_intent_same_reuses_the_existing_normalization():
    sent = {"SPEED": "10Gb", "CONF": FF_A + "\n" + FF_B}
    assert P.po_intent_same("SPEED", {"SPEED": "10Gb"}, sent)
    assert P.po_intent_same("CONF", {"CONF": FF_B + "\n" + FF_A + "\n"}, sent)  # order and blank lines ignored, as _po_same
    assert P.po_intent_same("SPEED", {}, {"SPEED": "Auto"}) and P.po_intent_same("CONF", {}, {"CONF": ""})  # absent = template value
    assert not P.po_intent_same("SPEED", {"SPEED": "Auto"}, sent)
    assert not P.po_intent_same("CONF", {"CONF": FF_A}, sent)


class DriftAfterDeploy(PoLifecycleController):
    """SYNTHETIC: after the deploy the controller returns a port-channel intent that differs in `drift` (e.g. a value it did not keep)."""

    drift = {}

    def __call__(self, mod, method, path, data=None):
        resp = super(DriftAfterDeploy, self).__call__(mod, method, path, data)
        if method == "POST" and path.endswith(DEPLOY) and SPEED_REVIEW_PO in self.detail:
            self.detail[SPEED_REVIEW_PO]["nvPairs"].update(self.drift)
        return resp


@pytest.mark.parametrize("drift, key", [({"SPEED": "Auto"}, "SPEED"), ({"CONF": ""}, "CONF"), ({"SPEED": "1Gb", "CONF": FF_B}, "SPEED, CONF")])
def test_po_readback_reports_a_lost_speed_or_freeform_without_retry_or_rewrite(drift, key):
    ctrl, _r = created_with([], [])
    ctrl.__class__ = DriftAfterDeploy
    ctrl.drift = drift
    old_po, old_m = po_stanza("host", HOST_LINES), member_stanza("host", HOST_LINES)
    new_po = old_po + ["  speed 10000", "  " + FF_A]
    new_m = old_m + ["  speed 10000"]
    pend = ["interface port-channel10", "  speed 10000", "  " + FF_A, "interface ethernet1/7", "  speed 10000"]
    ctrl.previews = [_po_update_preview(old_po, new_po, old_m, new_m, pend)]
    status, result = run(ctrl, [_po_cfg(speed="10Gb", cmds=[FF_A])], state="merged")
    assert status == "fail" and "post-deploy intent readback differs in %s" % key in result["msg"], result.get("msg")
    # reported only: one intent write, one deploy, nothing written after the deploy
    assert len(ctrl.bulk_bodies()) == 1 and len(ctrl.deploys()) == 1
    deploy_at = max(i for i, c in enumerate(ctrl.calls) if c[0] == "POST" and c[1].endswith(DEPLOY))
    assert [c for c in ctrl.calls[deploy_at + 1:] if c[0] in ("POST", "PUT", "DELETE") and "/config-preview" not in c[1]] == []


def test_po_readback_with_the_kept_speed_and_freeform_passes():
    ctrl, _r = created_with([], [])
    ctrl.__class__ = DriftAfterDeploy
    ctrl.drift = {"CONF": FF_A + "\n"}  # same commands, a trailing line break: not a difference
    old_po, old_m = po_stanza("host", HOST_LINES), member_stanza("host", HOST_LINES)
    pend = ["interface port-channel10", "  speed 10000", "  " + FF_A, "interface ethernet1/7", "  speed 10000"]
    ctrl.previews = [_po_update_preview(old_po, old_po + ["  speed 10000", "  " + FF_A], old_m, old_m + ["  speed 10000"], pend)]
    status, result = run(ctrl, [_po_cfg(speed="10Gb", cmds=[FF_A])], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")


# ====================================================================================== L3: withdrawal of the adopted capability line
def _back_to_auto(pend_negotiate):
    base = dict(members=[IF7], admin_state=False)
    ctrl, _r = created_with(["speed 10000", "no negotiate auto"], ["speed 10000", "no negotiate auto"], speed="10Gb")
    run_po = po_stanza("host", HOST_LINES) + ["  speed 10000", "  no negotiate auto"]
    run_m = member_stanza("host", HOST_LINES) + ["  speed 10000", "  no negotiate auto"]
    po_pend = ["interface port-channel10", "  no speed 10000"] + (["  negotiate auto"] if pend_negotiate else [])
    m_pend = ["interface ethernet1/7", "  no speed 10000"] + (["  negotiate auto"] if pend_negotiate else [])
    ctrl.previews = [preview(po_pend + m_pend, running=run_po + run_m,
                             expected=po_stanza("host", HOST_LINES) + member_stanza("host", HOST_LINES))]
    return run(ctrl, [_po_cfg(pvlan_association=ASSOC, **base)], state="replaced"), ctrl


def test_speed_back_to_auto_deploys_when_the_pending_withdraws_the_adopted_capability_line():
    (status, result), ctrl = _back_to_auto(True)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.bulk_bodies()[0][0]["interfaces"][0]["nvPairs"]["SPEED"] == "Auto" and len(ctrl.deploys()) == 1


def test_speed_back_to_auto_is_refused_before_any_deploy_when_the_capability_line_is_not_withdrawn():
    (status, result), ctrl = _back_to_auto(False)
    assert status == "fail" and "withdrawal of 'no negotiate auto' is absent from the pending" in result["msg"], result.get("msg")
    assert ctrl.deploys() == []
