"""Coexistence of the regular port-channel and vPC PVLAN routes with the caller-supplied patch_version gate.

The port-channel (int_port_channel_pvlan_host) and vPC (int_vpc_pvlan_host) PVLAN builders return their own
template payload before the engine contribution that the other port-channel/vPC modes reach. That is equivalent to
an empty contribution only because no registry binding exists for any PVLAN policy; the first test pins that
precondition. The rest drive the real main() through the existing Po/vPC harnesses and compare the ordered request
log (method, path, body) of a run without patch_version against runs with the approved and an unapproved value.

SIMULATED: every controller answer and preview comes from the existing harness builders. No controller is contacted.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import registered_profile_keys
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_ENABLED_PATCH_VERSIONS

from .test_dcnm_intf_pvlan_harness import IF7, IF8, PREVIEW_MARK, SWITCH_IP, TRUNK, run, trunk_host_nv, trunk_item
from .test_dcnm_intf_pvlan_po_g1 import del_item, delete_preview
from .test_dcnm_intf_pvlan_po_g1 import item as po_item
from .test_dcnm_intf_pvlan_po_g5_next_modes import (
    CASES,
    MEM_10,
    MODES,
    corrected_hr_preview,
    creation_preview,
    existing,
    hr_ctrl,
    hr_delete,
    new_ctrl,
)
from .test_dcnm_intf_pvlan_po_host import PO
from .test_dcnm_intf_pvlan_vpc_harness import run_vpc
from .test_dcnm_intf_pvlan_vpc_modes_e1 import P_, TP, TS, baseline_ctrl, converged_previews, create_previews, seeded_ctrl
from .test_dcnm_intf_pvlan_vpc_modes_e1 import item as vpc_item

APPROVED = sorted(GIE_ENABLED_PATCH_VERSIONS)[0]
PATCH_VALUES = [
    pytest.param(APPROVED, id="approved"),
    pytest.param("4.3.1.0175006010", id="unapproved"),
]


def _log(c):
    return [(m, p, json.loads(b) if isinstance(b, str) else b) for m, p, b in c.calls]


def test_port_channel_and_vpc_pvlan_policies_have_no_registered_binding():
    for policy in (P.PO_HOST_POLICY, P.PO_MEMBER_POLICY, P.VPC_HOST_POLICY, P.VPC_PO_POLICY):
        assert registered_profile_keys(policy) == set(), policy


# ------------------------------------------------------------------ regular port-channel
def _po_create(mode, patch_version=None):
    profile, lines = CASES[mode]
    c = new_ctrl(mode)
    c.previews = [creation_preview(mode, lines)]
    status, result = run(c, [po_item(mode, **profile)], state="replaced", patch_version=patch_version)
    return c, status, result


@pytest.mark.parametrize("patch_version", PATCH_VALUES)
@pytest.mark.parametrize("mode", MODES)
def test_po_pvlan_creation_sends_the_same_requests_for_any_patch_value(mode, patch_version):
    reference, status, result = _po_create(mode)
    assert status == "exit", result.get("msg")
    c, status, result = _po_create(mode, patch_version)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert _log(c) == _log(reference)
    assert "PATCH_VERSION" not in json.dumps(_log(c)).upper()


@pytest.mark.parametrize("patch_version", PATCH_VALUES)
def test_po_pvlan_deletion_sends_the_same_requests_for_any_patch_value(patch_version):
    mode = "promiscuous"
    _profile, lines = CASES[mode]
    reference = existing(mode)
    reference.previews = [delete_preview(mode, lines)]
    assert run(reference, [del_item()], state="deleted")[0] == "exit"
    c = existing(mode)
    c.previews = [delete_preview(mode, lines)]
    status, result = run(c, [del_item()], state="deleted", patch_version=patch_version)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert _log(c) == _log(reference)
    assert PO not in c.detail and c.detail[IF7]["policy"] == TRUNK


@pytest.mark.parametrize("patch_version", PATCH_VALUES)
def test_deployed_po_deletion_still_releases_the_member_administratively_down_for_any_patch_value(patch_version):
    """The measured release leaves the member admin-up; the module's correction to ADMIN_STATE false must be the only
    member write and must not depend on the patch context."""
    reference = hr_ctrl([corrected_hr_preview()])
    assert hr_delete(reference)[0] == "exit"
    c = hr_ctrl([corrected_hr_preview()])
    status, result = run(c, [{"name": "po502", "switch": [SWITCH_IP], "deploy": True}], state="deleted", patch_version=patch_version)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert _log(c) == _log(reference)
    assert len(c.markdeletes()) == 1 and len(c.modifies()) == 1 and len(c.deploys()) == 1
    assert json.loads(c.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]["ADMIN_STATE"] == "false"
    assert c.detail[MEM_10]["nvPairs"]["ADMIN_STATE"] == "false"


def test_registered_scalar_sibling_without_patch_stops_a_po_pvlan_batch_before_any_write():
    """The PVLAN port-channel needs no patch, but a sibling that names a registered scalar does: without the approved
    patch the whole invocation is refused before any write or preview, the port-channel included."""
    mode = "host"
    c = new_ctrl(mode)
    c.detail[IF8] = {"policy": TRUNK, "nvPairs": trunk_host_nv(IF8)}
    batch = [
        po_item(mode, pvlan_association=[{"primary_vlan": 2210, "secondary_vlan": 2212}]),
        trunk_item(IF8, deploy=True, disable_lldp_transmit=True, description="scalar sibling"),
    ]
    status, result = run(c, batch, state="merged")
    assert status == "fail"
    assert "disable_lldp_transmit" in result["msg"] and "patch_version" in result["msg"]
    assert c.mutating() == [] and c.requests(mark=PREVIEW_MARK) == []


# ------------------------------------------------------------------ vPC
def _vpc_create(mode, patch_version=None):
    c = baseline_ctrl(mode)
    create_previews(c, mode)
    status, result = run_vpc(c, [vpc_item(mode)], patch_version=patch_version)
    return c, status, result


@pytest.mark.parametrize("patch_version", PATCH_VALUES)
@pytest.mark.parametrize("mode", [P_, TP, TS])
def test_vpc_pvlan_creation_sends_the_same_requests_for_any_patch_value(mode, patch_version):
    reference, status, result = _vpc_create(mode)
    assert status == "exit", result.get("msg")
    c, status, result = _vpc_create(mode, patch_version)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert _log(c) == _log(reference)
    assert "PATCH_VERSION" not in json.dumps(_log(c)).upper()


@pytest.mark.parametrize("patch_version", PATCH_VALUES)
@pytest.mark.parametrize("mode", [P_, TP, TS])
def test_vpc_pvlan_exact_repeat_writes_nothing_for_any_patch_value(mode, patch_version):
    c = seeded_ctrl(mode)
    converged_previews(c, mode)
    status, result = run_vpc(c, [vpc_item(mode)], state="merged", patch_version=patch_version)
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert c.writes() == [] and c.deploys() == []
