"""SINGLETON-RANGE: a single-value inclusive VLAN range "N-N" in a PVLAN profile is the VLAN N.

NaC's convert_ranges macro renders `secondary_vlans: [{from: 2212, to: 2212}]` (and trunk allowed VLANs) as "2212-2212"; the shared
validator used to refuse it as "not ascending". Now:
  * interface_pvlan.vlan_set accepts N-N as [N] and still refuses descending, repeated (also "2212,2212-2212"), overlapping, out-of-range
    and malformed input;
  * dcnm_interface collapses N-N to N in the raw PVLAN profile (allowed_vlans, peer1/peer2_allowed_vlans, pvlan_mapping secondary_vlans)
    before validation, so the payload and the comparison are exactly those of N - the controller's own form - and an unchanged repeat
    written with N-N writes nothing.
Real main() through the existing Ethernet / port-channel / vPC harnesses; only the controller boundary is faked.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from . import test_dcnm_intf_pvlan as EP
from . import test_dcnm_intf_pvlan_po_g5_next_modes as G5
from . import test_dcnm_intf_pvlan_vpc_modes_e1 as E1
from .test_dcnm_intf_pvlan_harness import PVLAN, TRUNK, measured_preview, pvlan_item, run, trunk_host_nv
from .test_dcnm_intf_pvlan_vpc_harness import run_vpc


# ================================================================== the shared parser
@pytest.mark.parametrize("text, expected", [
    ("2212-2212", [2212]),
    ("2212", [2212]),
    ("2212-2213", [2212, 2213]),
    ("2210-2211,2214-2214", [2210, 2211, 2214]),
    ("1-1", [1]),
    ("4094-4094", [4094]),
    ("1", [1]),
    ("4094", [4094]),
    (" 2212 - 2212 ", [2212]),
])
def test_vlan_set_accepts_a_single_value_range_as_one_vlan(text, expected):
    assert P.vlan_set(text, "secondary_vlans") == expected


@pytest.mark.parametrize("text, needle", [
    ("2213-2212", "not ascending"),
    ("2212,2212-2212", "repeats VLAN 2212"),
    ("2212-2212,2212", "repeats VLAN 2212"),
    ("2210-2212,2211-2211", "repeats VLAN 2211"),
    ("2212-2212,2212-2212", "repeats VLAN 2212"),
    ("4095-4095", "outside 1-4094"),
    ("4094-4095", "outside 1-4094"),
    ("0-0", "is not a VLAN list"),
    ("2212-", "is not a VLAN list"),
    ("-2212", "is not a VLAN list"),
    ("2212--2212", "is not a VLAN list"),
    ("02212-02212", "is not a VLAN list"),
    ("a-a", "is not a VLAN list"),
    ("", "is not a VLAN list"),
    ("2212,,2213", "is not a VLAN list"),
])
def test_vlan_set_keeps_refusing_invalid_input(text, needle):
    with pytest.raises(P.PvlanError) as exc:
        P.vlan_set(text, "secondary_vlans")
    assert needle in str(exc.value)


@pytest.mark.parametrize("text, expected", [
    ("2212-2212", "2212"),
    ("2210-2212,2214-2214", "2210-2212,2214"),
    (" 2212 - 2212 ", "2212"),
    ("2213-2212", "2213-2212"),          # descending: left for the validator to refuse
    ("2212,2212-2212", "2212,2212"),     # duplicate stays a duplicate
    ("0-0", "0-0"),                      # malformed: untouched
    ("4095-4095", "4095"),               # collapsed like any N-N; 4095 is then refused by the validator (outside 1-4094)
    ("none", "none"),
    ("", ""),
    (2212, 2212),                        # not a string: untouched
])
def test_collapse_changes_only_well_formed_single_value_ranges(text, expected):
    assert P.collapse_single_value_ranges(text) == expected


def test_normalize_profile_touches_only_the_vlan_lists():
    profile = {"mode": "pvlan", "pvlan_mode": "trunk promiscuous", "native_vlan": "2301",
               "allowed_vlans": "2301-2301", "peer1_allowed_vlans": "10-10,20", "peer2_allowed_vlans": 5,
               "pvlan_mapping": [{"primary_vlan": 2210, "secondary_vlans": "2212-2212"}, {"primary_vlan": 2410, "secondary_vlans": "2412-2413"}]}
    before = copy.deepcopy(profile)
    changed = P.normalize_single_value_ranges(profile)
    assert changed == ["allowed_vlans", "peer1_allowed_vlans", "pvlan_mapping[0].secondary_vlans"]
    assert profile["allowed_vlans"] == "2301" and profile["peer1_allowed_vlans"] == "10,20" and profile["peer2_allowed_vlans"] == 5
    assert profile["pvlan_mapping"] == [{"primary_vlan": 2210, "secondary_vlans": "2212"}, {"primary_vlan": 2410, "secondary_vlans": "2412-2413"}]
    assert dict((k, v) for k, v in profile.items() if k not in ("allowed_vlans", "peer1_allowed_vlans", "pvlan_mapping")) == \
        dict((k, v) for k, v in before.items() if k not in ("allowed_vlans", "peer1_allowed_vlans", "pvlan_mapping"))


@pytest.mark.parametrize("secondaries, needle", [("4095-4095", "outside 1-4094"), ("2213-2212", "not ascending"),
                                                 ("2212,2212-2212", "repeats VLAN 2212"), ("2211-2213,2212-2212", "repeats VLAN 2212")])
def test_module_still_refuses_invalid_single_value_input_before_any_write(secondaries, needle):
    c = EP.ctrl(trunk_host_nv(), TRUNK)
    status, res = run(c, [eth_tprom(secondaries, "2301")])
    assert status == "fail" and needle in res["msg"], res.get("msg")
    EP.assert_no_writes(c)


def test_requested_pairs_of_a_single_value_range_equal_those_of_the_vlan():
    assert P.requested_pairs("pvlan_mapping", [{"primary_vlan": 2210, "secondary_vlans": "2212-2212"}]) == \
        P.requested_pairs("pvlan_mapping", [{"primary_vlan": 2210, "secondary_vlans": "2212"}]) == [(2210, 2212)]


# ================================================================== Ethernet PVLAN (real main, measured G6-M0a)
def eth_tprom(secondaries, allowed, **kw):
    return pvlan_item(pvlan_mode="trunk promiscuous", admin_state=False,
                      pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": secondaries}], native_vlan="2301", allowed_vlans=allowed, **kw)


def test_ethernet_single_value_ranges_send_the_same_payload_as_the_vlans():
    sent = []
    for secondaries, allowed in (("2211", "2301"), ("2211-2211", "2301-2301")):
        c = EP.ctrl(trunk_host_nv(), TRUNK)
        c.previews = [measured_preview("G6-M0a")]
        status, res = run(c, [eth_tprom(secondaries, allowed)])
        assert status == "exit" and res["changed"] is True, res.get("msg")
        policy, nv = c.sent_nv()
        assert policy == PVLAN
        sent.append(nv)
    assert sent[0] == sent[1]
    assert sent[1]["MAPPING_LIST"] == '{"MAPPING_LIST":[{"P_VLAN":"2210","S_VLAN":"2211"}]}' and sent[1]["PVLAN_ALLOWED_VLANS"] == "2301"


@pytest.mark.parametrize("secondaries, allowed", [("2211", "2301"), ("2211-2211", "2301-2301")])
def test_ethernet_unchanged_repeat_written_with_single_value_ranges_writes_nothing(secondaries, allowed):
    c = EP.ctrl(EP.TPROM_A11)
    status, res = run(c, [eth_tprom(secondaries, allowed, deploy=False)], state="replaced")
    assert status == "exit" and res["changed"] is False, res.get("msg")
    EP.assert_no_writes(c)


# ================================================================== regular port-channel (real main, battery creation profile)
def po_create(mode, profile):
    _profile, lines = G5.CASES[mode]
    ctrl = G5.new_ctrl(mode)
    ctrl.previews = [G5.creation_preview(mode, lines)]
    status, result = run(ctrl, [G5.item(mode, **profile)], state="replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    body = json.loads(ctrl.creates()[0][2])
    return (body[0] if isinstance(body, list) else body)["interfaces"][0]["nvPairs"]


@pytest.mark.parametrize("mode, singleton", [
    ("promiscuous", {"pvlan_mapping": [{"primary_vlan": 2210, "secondary_vlans": "2212-2212"}]}),
    ("trunk promiscuous", {"pvlan_mapping": [{"primary_vlan": 2210, "secondary_vlans": "2211-2212"}, {"primary_vlan": 2410, "secondary_vlans": "2412-2412"}],
                           "native_vlan": "2301", "allowed_vlans": "2301-2301"}),
])
def test_port_channel_single_value_ranges_send_the_same_payload_as_the_vlans(mode, singleton):
    reference = po_create(mode, G5.CASES[mode][0])
    candidate = po_create(mode, singleton)
    assert candidate == reference


# ================================================================== vPC (real main, synthetic submode seed)
def vpc_singleton_item(mode):
    if mode == E1.P_:
        extra = {"pvlan_mapping": [{"primary_vlan": r["primary_vlan"], "secondary_vlans": "-".join([r["secondary_vlans"]] * 2)}
                                   if "-" not in r["secondary_vlans"] and "," not in r["secondary_vlans"] else r for r in E1.MAP_P]}
    else:
        extra = {"pvlan_mapping": [{"primary_vlan": r["primary_vlan"], "secondary_vlans": "-".join([r["secondary_vlans"]] * 2)}
                                   if "-" not in r["secondary_vlans"] and "," not in r["secondary_vlans"] else r for r in E1.MAP_TP]}
        extra.update(dict((k, "-".join([v] * 2) if isinstance(v, str) and v.isdigit() and "allowed" in k else v) for k, v in E1.TRUNK_FIELDS.items()))
    return E1.item(mode, **extra)


@pytest.mark.parametrize("mode", [E1.P_, E1.TP])
def test_vpc_single_value_ranges_send_the_same_parent_payload_as_the_vlans(mode):
    sent = []
    for build in (E1.item, vpc_singleton_item):
        ctrl = E1.baseline_ctrl(mode)
        E1.create_previews(ctrl, mode)
        status, result = run_vpc(ctrl, [build(mode)], state="merged")
        assert status == "exit" and result["changed"] is True, result.get("msg")
        sent.append([json.loads(c[2]) for c in ctrl.calls if c[0] in ("POST", "PUT") and c[1].endswith("/globalInterface")])
    assert sent[0] == sent[1] and sent[0]


@pytest.mark.parametrize("mode", [E1.P_, E1.TP])
def test_vpc_unchanged_repeat_written_with_single_value_ranges_writes_nothing(mode):
    ctrl = E1.seeded_ctrl(mode)
    E1.converged_previews(ctrl, mode)
    status, result = run_vpc(ctrl, [vpc_singleton_item(mode)], state="merged")
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.writes() == [] and ctrl.deploys() == []


def test_the_singleton_item_really_carries_n_n_values():
    """Guard on the test data itself: the vPC singleton items must contain an N-N token (else the vPC rows would prove nothing)."""
    for mode in (E1.P_, E1.TP):
        text = json.dumps(vpc_singleton_item(mode)["profile"])
        assert any("%s-%s" % (v, v) in text for v in ("2212", "2211", "2412", "2301", "2302"))
