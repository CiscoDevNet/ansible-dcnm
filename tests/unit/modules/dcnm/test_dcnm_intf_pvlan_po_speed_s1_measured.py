"""Speed inheritance on a PVLAN port-channel member: the MEASURED S1 refusal and the boundaries any future inheritance rule must keep.

Source: fixtures/pvlan_po_speed_s1_measured.json, extracted read-only from a live run (step S1,
NDFC 12.6.0.267). After a merged `speed: 1Gb` on an existing host port-channel with one member, the controller's EXPECTED configuration
holds `speed 1000` on the port-channel AND on the member, the PENDING holds only the port-channel stanza (the whole stanza, with
`speed 1000`) and NO member stanza, and both running stanzas lack the line. RC2/IQ1/IQ1-D1 refuse the deploy (fail-before).
SP1: the speed-inheritance diagnosis (DIAG-20261012T091312Z) MEASURED that NX-OS applies the port-channel's speed to the member and
that the return to Auto removes it from both; the S1 shape is that measured form, so SP1 deploys it. The boundaries below stay refused.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import os

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

FX = json.load(open(os.path.join(os.path.dirname(__file__), "fixtures", "pvlan_po_speed_s1_measured.json")))
PO_NAME, MEMBER = "Port-channel521", "Ethernet1/8"
REFUSAL = "the pending for Ethernet1/8 is empty but the device differs from the intended state: {'missing': ['speed 1000'], 'unexpected': []}"


def _target(parent_after=None, member_nv=None):
    parent_after = parent_after or FX["parent_after_nv"]
    member_nv = member_nv or FX["member_nv"]
    return {
        "name": PO_NAME, "creates": False,
        "pre": (P.PO_HOST_POLICY, FX["parent_before_nv"]),
        "post": (P.PO_HOST_POLICY, parent_after),
        "members": [{"name": MEMBER, "pre": (P.PO_MEMBER_POLICY, member_nv),
                     "post": (P.PO_MEMBER_POLICY, P.po_member_nvpairs(parent_after, member_nv, current_is_member=True))}],
    }


def _entry(pending=None, running=None, expected=None):
    pv = FX["preview"]
    return {"pendingConfig": list(pv["pendingConfig"] if pending is None else pending),
            "runningConfig": ["!Command: show running-config"] + list(pv["runningConfig"] if running is None else running),
            "expectedConfig": list(pv["expectedConfig"] if expected is None else expected)}


def _assess(entry, target=None):
    """The module's own port-channel gate (DcnmIntf.dcnm_intf_pvlan_po_assess), on one preview entry."""
    blocks, _global = P.split_blocks(entry["pendingConfig"])
    gate = dcnm_interface.DcnmIntf.__new__(dcnm_interface.DcnmIntf)
    return gate.dcnm_intf_pvlan_po_assess(blocks, entry, target or _target())


def _replace(lines, old, new):
    return [new if x == old else x for x in lines]


# ====================================================================================== the measured S1 preview (fail-before)
def test_the_measured_s1_preview_deploys_through_the_measured_speed_inheritance():
    # IQ1-D1 (and RC2) refused exactly this entry with the measured message; SP1 deploys it.
    assert REFUSAL in FX["module_refusal"]
    decision, problems = _assess(_entry())
    assert (decision, problems) == ("deploy", [])


def test_the_measured_shape_is_what_the_refusal_says():
    pv = FX["preview"]
    blocks, _g = P.split_blocks(pv["pendingConfig"])
    assert list(blocks) == ["port-channel521"] and "speed 1000" in blocks["port-channel521"]
    _rc, member_expected = P.interface_stanza(pv["expectedConfig"], MEMBER)
    _rc, member_running = P.interface_stanza(pv["runningConfig"], MEMBER)
    assert "speed 1000" in [x.strip() for x in member_expected] and "speed 1000" not in [x.strip() for x in member_running]
    assert FX["parent_before_nv"]["SPEED"] == "Auto" and FX["parent_after_nv"]["SPEED"] == "1Gb"
    changed = sorted(k for k in FX["parent_after_nv"] if FX["parent_after_nv"].get(k) != FX["parent_before_nv"].get(k))
    assert changed == ["SPEED"], changed


def test_the_parent_alone_is_a_valid_deploy():
    """The port-channel's own transition is not the problem: its whole-stanza pending leads from its running state to the intended one."""
    entry = _entry()
    blocks, _g = P.split_blocks(entry["pendingConfig"])
    pre, post = (P.PO_HOST_POLICY, FX["parent_before_nv"]), (P.PO_HOST_POLICY, FX["parent_after_nv"])
    decision, found = P.assess_target(blocks["port-channel521"], entry, PO_NAME, P.render(*post), P.transition_vocabulary(pre, post))
    assert (decision, found) == ("deploy", [])


# ====================================================================================== boundaries a future inheritance rule must keep
def test_a_member_expected_with_another_speed_is_refused():
    exp = list(FX["preview"]["expectedConfig"])
    member_at = exp.index("interface ethernet1/8")
    exp[exp.index("  speed 1000", member_at)] = "  speed 10000"
    decision, problems = _assess(_entry(expected=exp))
    assert decision == "refuse" and any(MEMBER in p for p in problems)


def test_a_parent_pending_without_the_speed_line_is_refused():
    pend = [x for x in FX["preview"]["pendingConfig"] if x.strip() != "speed 1000"]
    decision, problems = _assess(_entry(pending=pend))
    assert decision == "refuse"


def test_an_additional_member_command_in_the_expected_is_refused():
    exp = list(FX["preview"]["expectedConfig"])
    exp.insert(exp.index("interface ethernet1/8") + 1, "  duplex full")
    decision, problems = _assess(_entry(expected=exp))
    assert decision == "refuse" and any(MEMBER in p for p in problems)


def test_a_member_of_another_port_channel_is_refused():
    run = _replace(FX["preview"]["runningConfig"], "  channel-group 521 mode active", "  channel-group 522 mode active")
    decision, problems = _assess(_entry(running=run))
    assert decision == "refuse" and any(MEMBER in p for p in problems)


def test_a_member_expected_without_the_speed_is_refused_while_the_parent_has_it():
    exp = list(FX["preview"]["expectedConfig"])
    member_at = exp.index("interface ethernet1/8")
    del exp[exp.index("  speed 1000", member_at)]
    decision, problems = _assess(_entry(expected=exp))
    assert decision == "refuse" and any(MEMBER in p for p in problems)


def test_an_up_member_is_refused():
    run = _replace(FX["preview"]["runningConfig"], "  shutdown", "  no shutdown")
    decision, _problems = _assess(_entry(running=run))
    assert decision == "refuse"


@pytest.mark.parametrize("key, value", [("MTU", "default"), ("PVLAN_MODE", "promiscuous")])
def test_a_second_change_next_to_the_speed_is_not_hidden(key, value):
    after = copy.deepcopy(FX["parent_after_nv"])
    after[key] = value
    decision, _problems = _assess(_entry(), _target(parent_after=after))
    assert decision == "refuse"
