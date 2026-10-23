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

"""Interaction of the PVLAN input parity (bpdu_guard / speed spellings) with the fixed-speed duplex inheritance and its guards.

Real main() on the regular port-channel and the vPC, reusing the duplex battery's own fixtures and helpers (measured previews, retargeted).
An alias spelling must produce exactly the canonical request, must not look like a speed change to the combined speed + duplex guard, and
must not hide a real combined change or an F-A refusal. Synthetic controller doubles; NOT LIVE TESTED.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

from .test_dcnm_intf_pvlan_harness import run
from . import test_dcnm_intf_pvlan_duplex_inherited as D
from . import test_dcnm_intf_pvlan_vpc_harness as V

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
