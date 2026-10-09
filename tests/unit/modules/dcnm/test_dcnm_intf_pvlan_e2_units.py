"""Helper-level E2 supplements (they do not replace the real-main cases in test_dcnm_intf_pvlan_e2.py).

assess_target is replayed on every MEASURED discovery preview that carries device authority:
before the deploy each accepted transition must be deployable and PU3/PX1 refused; after the
deploy every converged read must be recognised as converged; every repeat read is converged.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .test_dcnm_intf_pvlan_harness import DEVICE, FIXTURE, SERIAL, TRANSITIONS, ok


def entry(phase):
    return {"runningConfig": phase["running_stanza"], "expectedConfig": phase["expected_stanza"]}


def body(phase):
    return P.split_blocks(phase["pendingConfig"])[0].get("ethernet1/7", [])


@pytest.mark.parametrize("case", sorted(TRANSITIONS))
def test_measured_pre_deploy_decision(case):
    t = TRANSITIONS[case]
    desired = P.render(t["post_policy"], t["post_nv"])
    decision, problems = P.assess_target(body(DEVICE[case]["pre"]), entry(DEVICE[case]["pre"]), "Ethernet1/7", desired)
    assert decision == ("refuse" if t["expect"] == "reject" else "deploy"), problems


@pytest.mark.parametrize("case", sorted(c for c in TRANSITIONS if "post" in DEVICE[c] and c != "PU3"))
def test_measured_post_deploy_read_is_converged(case):
    t = TRANSITIONS[case]
    desired = P.render(t["post_policy"], t["post_nv"])
    phase = DEVICE[case]["post"]
    assert phase["status"] == "In-Sync" and phase["pendingConfig"] == []
    assert P.assess_target([], entry(phase), "Ethernet1/7", desired) == ("converged", [])


def test_failed_pu3_deploy_is_not_converged_afterwards():
    t = TRANSITIONS["PU3"]
    decision, _problems = P.assess_target(body(DEVICE["PU3"]["post"]), entry(DEVICE["PU3"]["post"]), "Ethernet1/7", P.render(t["post_policy"], t["post_nv"]))
    assert decision == "refuse"


@pytest.mark.parametrize("case", sorted(c for c, d in DEVICE.items() if d["kind"] == "repeat"))
def test_measured_repeat_read_is_converged_with_the_device_state(case):
    phase = DEVICE[case]["pre"]
    assert phase["pendingConfig"] == [] and phase["status"] == "In-Sync"
    device = P.cli_model(P.interface_stanza(phase["running_stanza"], "Ethernet1/7")[1])
    controller = P.cli_model(P.interface_stanza(phase["expected_stanza"], "Ethernet1/7")[1])
    assert P.same_state(device, controller)


def test_cli_model_restores_nxos_defaults():
    m = P.cli_model(["mtu 9216", "switchport mode trunk", "switchport trunk allowed vlan none"])
    assert {"switchport", "no shutdown"} <= m.scalars and m.list_kind is None
    m = P.cli_model(["shutdown", "switchport mode private-vlan trunk promiscuous", "switchport private-vlan mapping trunk 2210 2211-2212"])
    assert m.list_kind == "trunk promiscuous" and m.pairs == {(2210, 2211), (2210, 2212)} and "no shutdown" not in m.scalars


def test_trunk_host_render_follows_the_installed_template():
    nv = {
        "ALLOWED_VLANS": "none",
        "MTU": "jumbo",
        "BPDUGUARD_ENABLED": False,
        "PORTTYPE_FAST_ENABLED": True,
        "ADMIN_STATE": False,
        "NATIVE_VLAN": "",
        "STORM_CONTROL_ACTION": "no",
        "ENABLE_STORM_CONTROL": False,
        "FEC": "auto",
    }
    m = P.render("int_trunk_host", nv)
    assert m.modeled and m.scalars == {
        "switchport",
        "switchport mode trunk",
        "switchport trunk allowed vlan none",
        "mtu 9216",
        "spanning-tree bpduguard disable",
        "spanning-tree port type edge trunk",
        "shutdown",
    }
    for unmodeled in ({"SPEED": "10Gb"}, {"STORM_CONTROL_BCAST_LEVEL_PERCENT": "50"}, {"ENABLE_NETFLOW": "true"}, {"ALLOWED_VLANS": ""}):
        assert not P.render("int_trunk_host", dict(nv, **unmodeled)).modeled


ITEMS = [{"serialNumber": SERIAL, "ifName": "Ethernet1/7"}]


def test_deploy_outcome_accepts_only_evidenced_bodies():
    assert P.deploy_outcome(ok(copy.deepcopy(FIXTURE["deploy_success"])), ITEMS) == ([], False)  # MEASURED
    assert P.deploy_outcome(ok([{"reportItemType": "WARNING", "message": "No Commands to execute"}]), ITEMS) == ([], True)
    rejected = [
        {"RETURN_CODE": 500, "DATA": FIXTURE["deploy_500"]["data"]},
        ok({"reportItemType": "ERROR", "message": "x"}),
        ok({}),
        ok({"message": "Interface deployed successfully", "value": []}),
        ok({"message": "Interface deployed successfully", "value": [{"serialNumber": SERIAL, "IfName": "Ethernet1/8"}]}),
        ok({"message": "Something else", "value": [{"serialNumber": SERIAL, "IfName": "Ethernet1/7"}]}),
        ok([{"reportItemType": "ERROR", "message": "x"}]),
        ok([]),
        ok("text"),
        None,
    ]
    for resp in rejected:
        problems, benign = P.deploy_outcome(resp, ITEMS)
        assert problems and not benign, resp
