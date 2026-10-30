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

"""Mode 'uplink_access': enabled storm control ends with one unit for every configured traffic type.

The rule is judged on the resulting parent levels (requested, then stored under 'merged' or reset under 'replaced'
and 'overridden') when storm control ends enabled and the request names a storm-control key or changes any other
value. An empty level and a percent of 100 render no line and have no unit. Real main() through the uplink
controller double; every value is synthetic. The tests make no claim about the template or the device.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import gie_withdrawal_harness as h
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.test_dcnm_intf_uplink_access import (
    ROWS, _assert_refused, _cfg, _have, _modify, _run)

DEFAULTS = dict((nv, reset) for _k, nv, reset in ROWS)
ON = dict(DEFAULTS, ENABLE_STORM_CONTROL="true")
MIXED_ON = dict(ON, STORM_CONTROL_ACTION="trap", STORM_CONTROL_BCAST_LEVEL_PERCENT="10.50",
                STORM_CONTROL_MCAST_LEVEL_PPS="1000")
MIXED_OFF = dict(MIXED_ON, ENABLE_STORM_CONTROL="false")
PCT2_ON = dict(ON, STORM_CONTROL_BCAST_LEVEL_PERCENT="10.50", STORM_CONTROL_MCAST_LEVEL_PERCENT="30.25")
PPS3_ON = dict(ON, STORM_CONTROL_BCAST_LEVEL_PPS="500", STORM_CONTROL_MCAST_LEVEL_PPS="1000",
               STORM_CONTROL_UCAST_LEVEL_PPS="2000")
MIXED_REQUEST = dict(enable_storm_control=True, storm_control_action="trap",
                     storm_control_broadcast_level_percent="10.50", storm_control_multicast_level_pps=1000)
REFUSAL = "storm control would end with percent levels"


def _storm(nv):
    return dict((k, v) for k, v in nv.items() if "STORM" in k)


@pytest.mark.parametrize("state,stored,profile,percent,pps", [
    ("merged", DEFAULTS, MIXED_REQUEST, "storm_control_broadcast_level_percent", "storm_control_multicast_level_pps"),
    ("replaced", DEFAULTS, MIXED_REQUEST, "storm_control_broadcast_level_percent", "storm_control_multicast_level_pps"),
    ("overridden", DEFAULTS, MIXED_REQUEST, "storm_control_broadcast_level_percent",
     "storm_control_multicast_level_pps"),
    ("replaced", MIXED_ON, MIXED_REQUEST, "storm_control_broadcast_level_percent", "storm_control_multicast_level_pps"),
    # zero is a level in its unit
    ("merged", DEFAULTS, dict(enable_storm_control=True, storm_control_broadcast_level_percent="0",
                              storm_control_multicast_level_pps=1000),
     "storm_control_broadcast_level_percent", "storm_control_multicast_level_pps"),
    ("merged", DEFAULTS, dict(enable_storm_control=True, storm_control_broadcast_level_percent="10",
                              storm_control_multicast_level_pps=0),
     "storm_control_broadcast_level_percent", "storm_control_multicast_level_pps"),
    # a stored level of another traffic type is carried forward under merged
    ("merged", dict(ON, STORM_CONTROL_MCAST_LEVEL_PPS="1000"), dict(storm_control_broadcast_level_percent="40"),
     "storm_control_broadcast_level_percent", "storm_control_multicast_level_pps"),
    ("merged", dict(ON, STORM_CONTROL_MCAST_LEVEL_PERCENT="30"), dict(storm_control_broadcast_level_pps=500),
     "storm_control_multicast_level_percent", "storm_control_broadcast_level_pps"),
    # switching one traffic type while another keeps the old unit
    ("merged", PCT2_ON, dict(storm_control_broadcast_level_pps=500),
     "storm_control_multicast_level_percent", "storm_control_broadcast_level_pps"),
    # re-enabling dormant mixed levels, and an action change while mixed levels are active
    ("merged", MIXED_OFF, dict(enable_storm_control=True),
     "storm_control_broadcast_level_percent", "storm_control_multicast_level_pps"),
    ("merged", MIXED_ON, dict(storm_control_action="shutdown"),
     "storm_control_broadcast_level_percent", "storm_control_multicast_level_pps"),
], ids=["merged", "replaced", "overridden", "replaced-over-mixed", "zero-percent", "zero-pps", "carried-pps",
        "carried-percent", "one-type-switch", "re-enable", "action-on-mixed"])
def test_a_resulting_mix_of_units_is_refused_before_any_write(state, stored, profile, percent, pps):
    result, calls = _run(_cfg(deploy=False, **profile), state, _have(**stored))
    _assert_refused(result, calls, REFUSAL, percent, pps)


def test_repeating_a_stored_mix_is_refused():
    # Earlier module versions could store this state; repeating the request that stored it no longer passes.
    result, calls = _run(_cfg(deploy=False, **MIXED_REQUEST), "merged", _have(**MIXED_ON))
    _assert_refused(result, calls, REFUSAL)


@pytest.mark.parametrize("state", ["merged", "replaced", "overridden"])
def test_a_valid_first_item_is_not_written_when_the_uplink_item_mixes_units(state):
    configs = [h.cfg_for(h.VPC_TRUNK, h.BASE_VPC_TRUNK), _cfg(deploy=False, **MIXED_REQUEST)]
    result, calls = _run(configs, state, _have(**DEFAULTS))
    _assert_refused(result, calls, REFUSAL)


@pytest.mark.parametrize("state,stored,profile,sent", [
    ("merged", DEFAULTS, dict(enable_storm_control=True, storm_control_broadcast_level_percent="10.50",
                              storm_control_multicast_level_percent="30.25", storm_control_unicast_level_percent="0"),
     dict(STORM_CONTROL_BCAST_LEVEL_PERCENT="10.50", STORM_CONTROL_MCAST_LEVEL_PERCENT="30.25",
          STORM_CONTROL_UCAST_LEVEL_PERCENT="0")),
    ("merged", DEFAULTS, dict(enable_storm_control=True, storm_control_broadcast_level_pps=500,
                              storm_control_multicast_level_pps=0),
     dict(STORM_CONTROL_BCAST_LEVEL_PPS="500", STORM_CONTROL_MCAST_LEVEL_PPS="0")),
    # every configured traffic type changes unit in one request; the other unit is cleared per type
    ("merged", PPS3_ON, dict(storm_control_broadcast_level_percent="15", storm_control_multicast_level_percent="30.25",
                             storm_control_unicast_level_percent="40"),
     dict(STORM_CONTROL_BCAST_LEVEL_PERCENT="15", STORM_CONTROL_MCAST_LEVEL_PERCENT="30.25",
          STORM_CONTROL_UCAST_LEVEL_PERCENT="40", STORM_CONTROL_BCAST_LEVEL_PPS="",
          STORM_CONTROL_MCAST_LEVEL_PPS="", STORM_CONTROL_UCAST_LEVEL_PPS="")),
    ("merged", PCT2_ON, dict(storm_control_broadcast_level_pps=500, storm_control_multicast_level_pps=1000),
     dict(STORM_CONTROL_BCAST_LEVEL_PPS="500", STORM_CONTROL_MCAST_LEVEL_PPS="1000",
          STORM_CONTROL_BCAST_LEVEL_PERCENT="", STORM_CONTROL_MCAST_LEVEL_PERCENT="")),
    # the only configured traffic type changes unit
    ("merged", dict(ON, STORM_CONTROL_BCAST_LEVEL_PERCENT="10.50"), dict(storm_control_broadcast_level_pps=500),
     dict(STORM_CONTROL_BCAST_LEVEL_PPS="500", STORM_CONTROL_BCAST_LEVEL_PERCENT="")),
    # a percent of 100 renders no line
    ("merged", DEFAULTS, dict(enable_storm_control=True, storm_control_broadcast_level_percent="100",
                              storm_control_multicast_level_pps=1000),
     dict(STORM_CONTROL_BCAST_LEVEL_PERCENT="100", STORM_CONTROL_MCAST_LEVEL_PPS="1000")),
    # leaving stored mixed levels with one unit
    ("merged", MIXED_ON, dict(storm_control_broadcast_level_percent=""),
     dict(STORM_CONTROL_BCAST_LEVEL_PERCENT="", STORM_CONTROL_MCAST_LEVEL_PPS="1000")),
    ("merged", MIXED_ON, dict(storm_control_broadcast_level_pps=500),
     dict(STORM_CONTROL_BCAST_LEVEL_PPS="500", STORM_CONTROL_BCAST_LEVEL_PERCENT="",
          STORM_CONTROL_MCAST_LEVEL_PPS="1000")),
    ("replaced", MIXED_ON, dict(enable_storm_control=True, storm_control_broadcast_level_percent="10.50"),
     dict(STORM_CONTROL_BCAST_LEVEL_PERCENT="10.50", STORM_CONTROL_MCAST_LEVEL_PPS="")),
    ("overridden", MIXED_ON, dict(enable_storm_control=True, storm_control_multicast_level_pps=1000),
     dict(STORM_CONTROL_BCAST_LEVEL_PERCENT="", STORM_CONTROL_MCAST_LEVEL_PPS="1000")),
    # no level, and re-enabling levels of one unit
    ("merged", ON, dict(storm_control_action="trap"), dict(STORM_CONTROL_ACTION="trap")),
    ("merged", dict(PPS3_ON, ENABLE_STORM_CONTROL="false"), dict(enable_storm_control=True),
     dict(ENABLE_STORM_CONTROL="true", STORM_CONTROL_BCAST_LEVEL_PPS="500", STORM_CONTROL_MCAST_LEVEL_PPS="1000",
          STORM_CONTROL_UCAST_LEVEL_PPS="2000")),
], ids=["all-percent", "all-pps", "all-types-to-percent", "two-types-to-pps", "only-type-to-pps", "percent-100",
        "clear-percent", "percent-type-to-pps", "replaced-one-unit", "overridden-one-unit", "action-only",
        "re-enable-one-unit"])
def test_one_resulting_unit_is_accepted(state, stored, profile, sent):
    result, calls = _run(_cfg(deploy=False, **profile), state, _have(**stored))
    assert not result.get("failed"), result.get("msg")
    nv = _storm(_modify(calls))
    for k, v in sent.items():
        assert nv[k] == v, k


@pytest.mark.parametrize("state,stored,profile,check", [
    ("merged", MIXED_ON, dict(enable_storm_control=False), ("ENABLE_STORM_CONTROL", "false")),
    ("merged", MIXED_ON, dict(enable_qos=True, qos_policy="UL-QOS", enable_storm_control=False),
     ("ENABLE_STORM_CONTROL", "false")),
    ("merged", MIXED_OFF, dict(spanning_tree_port_type="network"), ("spanningTreePortType", "network")),
    ("replaced", MIXED_ON, {}, ("ENABLE_STORM_CONTROL", "false")),
], ids=["disable", "disable-with-qos", "stp-over-dormant", "replaced-reset"])
def test_stored_mixed_levels_do_not_block_disabling_or_dormant_levels(state, stored, profile, check):
    result, calls = _run(_cfg(deploy=False, **profile), state, _have(**stored))
    assert not result.get("failed"), result.get("msg")
    nv = _modify(calls)
    assert nv[check[0]] == check[1]
    if state == "merged":
        # The stored levels are sent back as they are: nothing is cleared or converted.
        assert nv["STORM_CONTROL_BCAST_LEVEL_PERCENT"] == "10.50" and nv["STORM_CONTROL_MCAST_LEVEL_PPS"] == "1000"


@pytest.mark.parametrize("profile", [
    dict(spanning_tree_port_type="network"),
    dict(enable_qos=True, qos_policy="UL-QOS"),
    dict(disable_qos_stats=True),
], ids=["stp-over-active", "qos-over-active", "qos-stats-over-active"])
@pytest.mark.parametrize("deploy", [True, False])
def test_another_field_over_active_mixed_levels_is_refused_before_any_write(profile, deploy):
    # The update would write the stored levels back, and a deployment would render both units.
    result, calls = _run(_cfg(deploy=deploy, **profile), "merged", _have(**MIXED_ON))
    _assert_refused(result, calls, REFUSAL, "storm_control_broadcast_level_percent",
                    "storm_control_multicast_level_pps")


@pytest.mark.parametrize("profile", [
    dict(enable_qos=True, qos_policy="UL-QOS"),
    dict(enable_qos=True, qos_policy="ul-qos"),
    dict(spanning_tree_port_type="network"),
], ids=["qos", "qos-case-only", "stp"])
def test_an_unchanged_request_over_active_mixed_levels_writes_nothing(profile):
    stored = dict(MIXED_ON, ENABLE_QOS="true", QOS_POLICY="UL-QOS", spanningTreePortType="network")
    result, calls = _run(_cfg(**profile), "merged", _have(**stored))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and result["changed"] is False


@pytest.mark.parametrize("repair,sent", [
    (dict(storm_control_broadcast_level_percent=""),
     dict(STORM_CONTROL_BCAST_LEVEL_PERCENT="", STORM_CONTROL_MCAST_LEVEL_PPS="1000")),
    (dict(storm_control_broadcast_level_pps=500),
     dict(STORM_CONTROL_BCAST_LEVEL_PPS="500", STORM_CONTROL_BCAST_LEVEL_PERCENT="",
          STORM_CONTROL_MCAST_LEVEL_PPS="1000")),
], ids=["clear-percent", "percent-type-to-pps"])
def test_a_qos_change_with_a_unit_repair_over_active_mixed_levels_is_sent(repair, sent):
    result, calls = _run(_cfg(deploy=False, enable_qos=True, qos_policy="UL-QOS", **repair), "merged",
                         _have(**MIXED_ON))
    assert not result.get("failed"), result.get("msg")
    nv = _modify(calls)
    assert nv["ENABLE_QOS"] == "true" and nv["QOS_POLICY"] == "UL-QOS" and nv["ENABLE_STORM_CONTROL"] == "true"
    for k, v in sent.items():
        assert nv[k] == v, k


def test_a_valid_first_item_is_not_written_when_the_uplink_item_resends_active_mixed_levels():
    configs = [h.cfg_for(h.VPC_TRUNK, h.BASE_VPC_TRUNK), _cfg(deploy=True, enable_qos=True, qos_policy="UL-QOS")]
    result, calls = _run(configs, "merged", _have(**MIXED_ON))
    _assert_refused(result, calls, REFUSAL)


@pytest.mark.parametrize("stored,profile", [
    (PPS3_ON, dict(storm_control_unicast_level_pps=2000)),
    (MIXED_OFF, dict(enable_storm_control=False)),
], ids=["one-unit-repeat", "disabled-repeat"])
def test_repeats_write_nothing(stored, profile):
    result, calls = _run(_cfg(deploy=False, **profile), "merged", _have(**stored))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and result["changed"] is False
