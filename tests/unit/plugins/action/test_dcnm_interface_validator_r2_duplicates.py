"""PR725-R2 integration review: several readback entries for ONE interface identity must not make the verdict order dependent.

The R2 checker compares per identity (sorted serial tuple + ifName). Its first version kept only the first readback entry of an
identity, so two contradictory entries passed or failed depending on their order. Every entry must now hold the requested values.
Identical duplicates, entries that differ only in nvPairs the test did not request, and the same interface name on another switch
(a different identity) are not conflicts and still pass. Runs the REAL action plugin through the R2 harness. NOT LIVE.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from .test_dcnm_interface_validator_r2 import FABRIC, SN1, SN2, S, r2_back, r2_cfg, r2_eth, r2_run

R2DUP_CFG = [r2_eth("trunk", flowcontrol_send="on")]
R2DUP_ON = {"INTF_NAME": "Ethernet1/21", "flowcontrolSend": "on"}
R2DUP_OFF = {"INTF_NAME": "Ethernet1/21", "flowcontrolSend": "off"}
R2DUP_NONE = {"INTF_NAME": "Ethernet1/21"}


def r2dup_intf(nvpairs, ifname="Ethernet1/21", serial=SN1):
    nv = {"FABRIC_NAME": FABRIC}
    nv.update(nvpairs)
    return {"ifName": ifname, "serialNumber": serial, "nvPairs": nv}


def r2dup_readback(*interfaces, one_policy=False):
    if one_policy:
        return {"changed": False, "failed": False, "response": [{"policy": "int_trunk_host", "interfaces": list(interfaces)}]}
    return {"changed": False, "failed": False, "response": [{"policy": "int_trunk_host", "interfaces": [i]} for i in interfaces]}


@pytest.mark.parametrize("first, second", [(R2DUP_ON, R2DUP_OFF), (R2DUP_OFF, R2DUP_ON), (R2DUP_ON, R2DUP_NONE), (R2DUP_NONE, R2DUP_ON)])
@pytest.mark.parametrize("one_policy", [False, True])
def test_r2dup_contradictory_entries_fail_in_either_order(tmp_path, first, second, one_policy):
    res = r2_run(tmp_path, R2DUP_CFG, r2dup_readback(r2dup_intf(first), r2dup_intf(second), one_policy=one_policy))
    assert res["failed"] is True, res["msg"]
    assert "ambiguous_readback" in res["msg"]


def test_r2dup_an_ifname_case_variant_is_the_same_identity(tmp_path):
    res = r2_run(tmp_path, R2DUP_CFG, r2dup_readback(r2dup_intf(R2DUP_ON), r2dup_intf(R2DUP_OFF, ifname="ethernet1/21")))
    assert res["failed"] is True, res["msg"]


def test_r2dup_identical_entries_are_not_a_conflict(tmp_path):
    res = r2_run(tmp_path, R2DUP_CFG, r2dup_readback(r2dup_intf(R2DUP_ON), r2dup_intf(R2DUP_ON)))
    assert res["failed"] is False, res["msg"]


def test_r2dup_entries_differing_only_in_unrequested_nvpairs_are_not_a_conflict(tmp_path):
    rb = r2dup_readback(r2dup_intf(dict(R2DUP_ON, MTU="jumbo")), r2dup_intf(dict(R2DUP_ON, MTU="default")))
    assert r2_run(tmp_path, R2DUP_CFG, rb)["failed"] is False


def test_r2dup_the_same_name_on_another_switch_is_another_identity(tmp_path):
    rb = r2dup_readback(r2dup_intf(R2DUP_ON), r2dup_intf(R2DUP_OFF, serial=SN2))
    assert r2_run(tmp_path, R2DUP_CFG, rb)["failed"] is False


def test_r2dup_two_wrong_entries_still_fail(tmp_path):
    res = r2_run(tmp_path, R2DUP_CFG, r2dup_readback(r2dup_intf(R2DUP_OFF), r2dup_intf(R2DUP_OFF)))
    assert res["failed"] is True


def test_r2dup_a_single_entry_keeps_the_plain_difference_report(tmp_path):
    res = r2_run(tmp_path, R2DUP_CFG, r2dup_readback(r2dup_intf(R2DUP_OFF)))
    assert res["failed"] is True
    assert "ambiguous_readback" not in res["msg"] and "flowcontrolSend" in res["msg"]


R2DUP_FAKE_VALUE = "R2-Synthetic-D1"


def test_r2dup_conflicting_sensitive_values_are_reported_redacted(tmp_path, capsys):
    cfg = [r2_cfg("int_routed_host", ospf_authentication_key=R2DUP_FAKE_VALUE)]
    good = r2_back("int_routed_host", {"ospfAuthenticationKey": R2DUP_FAKE_VALUE})
    bad = r2_back("int_routed_host", {"ospfAuthenticationKey": R2DUP_FAKE_VALUE + "-other"})
    for entries in ((good, bad), (bad, good)):
        rb = {"changed": False, "failed": False, "response": entries[0]["response"] + entries[1]["response"]}
        res = r2_run(tmp_path, cfg, rb)
        out = capsys.readouterr().out
        assert res["failed"] is True and "ambiguous_readback" in res["msg"]
        assert R2DUP_FAKE_VALUE not in res["msg"] and R2DUP_FAKE_VALUE not in out
        assert "ospfAuthenticationKey" in res["msg"] and S.R2_REDACTED in res["msg"]
