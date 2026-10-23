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

"""PVLAN input parity for bpdu_guard and speed (Ethernet, regular port-channel and vPC).

The regular access/trunk profiles of this module accept a boolean bpdu_guard and any letter case of a speed; mode 'pvlan' refused
both. Every main() case below goes through the EXISTING harnesses of the three PVLAN families (real argument spec and coercion,
builders, reconciliation, serialisation; mocks only at the controller boundary) and compares the OUTBOUND request of an alternate
spelling with the one of the canonical spelling: identical bytes, canonical values. Synthetic fixtures; NOT LIVE TESTED.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from . import gie_withdrawal_harness as GH
from . import test_dcnm_intf_pvlan as E
from . import test_dcnm_intf_pvlan_po_host as PO
from . import test_dcnm_intf_pvlan_vpc_harness as VH

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
