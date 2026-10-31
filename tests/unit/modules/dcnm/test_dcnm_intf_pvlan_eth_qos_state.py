"""Ingress QoS of the Ethernet PVLAN parent int_pvlan_host, judged on the RESULTING state.

NOT LIVE TESTED. Real main() through the existing Ethernet PVLAN harness, deploy false. A requested non-empty qos_policy needs
ENABLE_QOS true after an omitted enable_qos resolves (merged keeps HAVE; replaced, overridden and a policy change take the
template default false). A name kept from HAVE while QoS is disabled stays allowed. Policy names are synthetic.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

import pytest

from .test_dcnm_intf_pvlan_companions_c1 import SMU, eth_item, full_model, have_nv
from .test_dcnm_intf_pvlan_harness import IF7, IF8, PVLAN, TRUNK, pvlan_nv, run, trunk_host_nv
from .test_dcnm_intf_pvlan_lifecycle import ctrl

REFUSAL = "qos_policy requires enable_qos true"
ENABLED = dict(ENABLE_QOS="true", QOS_POLICY="QOS-OLD")
DISABLED_EMPTY = dict(ENABLE_QOS="false", QOS_POLICY="")
DISABLED_NAMED = dict(ENABLE_QOS="false", QOS_POLICY="QOS-OLD")


def _item(state, **profile):
    return eth_item(deploy=False, **profile) if state == "merged" else full_model(**profile)


def _sent_qos(c, ifname=IF7):
    nv = c.sent_nv(ifname)[1]
    return nv["ENABLE_QOS"], nv["QOS_POLICY"]


def _assert_refused(status, res, c):
    assert status == "fail" and REFUSAL in res["msg"], res.get("msg")
    assert c.mutating() == []


@pytest.mark.parametrize("state, stored", [
    ("merged", DISABLED_EMPTY),
    ("merged", DISABLED_NAMED),
    ("replaced", ENABLED),
    ("replaced", DISABLED_EMPTY),
    ("overridden", ENABLED),
    ("overridden", DISABLED_NAMED),
])
def test_a_requested_name_that_resolves_to_disabled_qos_is_refused_before_any_write(state, stored):
    c = ctrl(nv=have_nv(**stored))
    status, res = run(c, [_item(state, qos_policy="QOS-NEW")], state=state, patch_version=SMU)
    _assert_refused(status, res, c)


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_a_requested_name_on_a_policy_change_takes_the_disabled_default_and_is_refused(state):
    c = ctrl(nv=trunk_host_nv(IF7), policy=TRUNK)
    status, res = run(c, [full_model(qos_policy="QOS-NEW")], state=state, patch_version=SMU)
    _assert_refused(status, res, c)


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_a_valid_item_before_the_refused_one_is_not_written(state):
    c = ctrl(nv=have_nv(**DISABLED_EMPTY))
    c.detail[IF8] = {"policy": PVLAN, "nvPairs": dict(pvlan_nv("G6-M0a", ifname=IF8), **DISABLED_EMPTY)}
    valid = _item(state, enable_qos=True, qos_policy="QOS-OK")
    invalid = dict(copy.deepcopy(_item(state, qos_policy="QOS-NEW")), name=IF8)
    status, res = run(c, [valid, invalid], state=state, patch_version=SMU)
    _assert_refused(status, res, c)
    assert IF8 in res["msg"] and IF7 + " on" not in res["msg"]


def test_an_explicit_false_with_a_name_is_still_refused_at_input():
    c = ctrl(nv=have_nv(**ENABLED))
    status, res = run(c, [eth_item(deploy=False, enable_qos=False, qos_policy="QOS-NEW")], patch_version=SMU)
    assert status == "fail" and "Invalid parameters in playbook" in res["msg"] and REFUSAL in res["msg"], res.get("msg")
    assert c.mutating() == []


@pytest.mark.parametrize("state, stored, profile, sent", [
    # merged name-only over enabled QoS: the policy change the module honors
    ("merged", ENABLED, dict(qos_policy="QOS-NEW"), ("true", "QOS-NEW")),
    ("merged", DISABLED_EMPTY, dict(enable_qos=True, qos_policy="QOS-NEW"), ("true", "QOS-NEW")),
    ("replaced", DISABLED_NAMED, dict(enable_qos=True, qos_policy="QOS-NEW"), ("true", "QOS-NEW")),
    ("overridden", ENABLED, dict(enable_qos=True, qos_policy="QOS-NEW"), ("true", "QOS-NEW")),
    # disabling keeps an omitted stored name; re-enabling reuses it
    ("merged", ENABLED, dict(enable_qos=False), ("false", "QOS-OLD")),
    ("merged", DISABLED_NAMED, dict(enable_qos=True), ("true", "QOS-OLD")),
    # an empty name clears
    ("merged", DISABLED_NAMED, dict(qos_policy=""), ("false", "")),
    ("merged", ENABLED, dict(enable_qos=False, qos_policy=""), ("false", "")),
    ("replaced", ENABLED, dict(qos_policy=""), ("false", "")),
    # neither key
    ("merged", DISABLED_NAMED, dict(description="qos untouched"), ("false", "QOS-OLD")),
    ("merged", ENABLED, dict(description="qos untouched"), ("true", "QOS-OLD")),
    ("replaced", ENABLED, dict(), ("false", "")),
])
def test_supported_qos_requests_are_unchanged(state, stored, profile, sent):
    c = ctrl(nv=have_nv(**stored))
    status, res = run(c, [_item(state, **profile)], state=state, patch_version=SMU)
    assert status == "exit" and res["changed"] is True, res.get("msg")
    assert _sent_qos(c) == sent
