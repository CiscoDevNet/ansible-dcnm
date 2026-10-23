"""Coexistence of native Ethernet PVLAN (int_pvlan_host) with the caller-supplied patch_version gate.

Native PVLAN owns its fields directly (no registry binding exists for int_pvlan_host), so the
patch_version contract must neither be required for PVLAN nor change what PVLAN sends. Registered
scalars keep their own contract. Real main() through the PVLAN harness; assertions are made on the
ordered request log of the fake controller (method, path, body), not on exit status alone.

NOT LIVE TESTED. No controller or switch is contacted.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import ast
import copy
import json

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    registered_profile_keys,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_ENABLED_PATCH_VERSIONS
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

from .test_dcnm_intf_pvlan_harness import (
    IF7,
    PVLAN,
    PREVIEW_MARK,
    TRUNK,
    measured_preview,
    pvlan_item,
    recreate_preview,
    reset_preview,
    run,
    trunk_host_nv,
)
from .test_dcnm_intf_pvlan_lifecycle import ADD_2212, ctrl

APPROVED = sorted(GIE_ENABLED_PATCH_VERSIONS)[0]
PATCH_VALUES = [
    pytest.param(None, id="omitted"),
    pytest.param(APPROVED, id="approved"),
    pytest.param("4.4.1", id="nd_release"),
    pytest.param("4.3.1.0175006010", id="unapproved"),
]


def _request_log(c):
    return [(m, p, json.loads(b) if isinstance(b, str) else b) for m, p, b in c.calls]


def test_int_pvlan_host_registers_only_the_two_c1_lldp_companions():
    """Precondition for everything below: the PVLAN core fields stay native. Only the two LLDP companions
    of int_pvlan_host are registered (REGISTRY_BINDING rows); every native PVLAN field below still owes nothing to the patch gate."""
    assert registered_profile_keys(PVLAN) == {"disable_lldp_transmit", "disable_lldp_receive"}


def test_every_engine_contribution_call_receives_the_callers_patch_version():
    """All gie_contribute_nvpairs call sites, including the PVLAN builder added after the patch
    gate was designed, forward the module's own patch_version. A site passing only the NDFC
    version would silently evaluate the gate with no caller context."""
    with open(dcnm_interface.__file__) as handle:
        tree = ast.parse(handle.read())
    calls = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "gie_contribute_nvpairs"
    ]
    # + the port-channel and vPC PVLAN builders (7 -> 9).
    assert len(calls) == 9, len(calls)
    for call in calls:
        assert len(call.args) == 4, ast.get_source_segment(open(dcnm_interface.__file__).read(), call)
        fourth = call.args[3]
        assert isinstance(fourth, ast.Call) and getattr(fourth.func, "id", None) == "getattr"
        assert [a.value for a in fourth.args[1:]] == ["patch_version", None]


@pytest.mark.parametrize("patch_version", PATCH_VALUES)
def test_native_pvlan_merged_is_byte_identical_for_any_patch_value(patch_version):
    reference = ctrl()
    reference.previews = [measured_preview("G6-M0b")]
    assert run(reference, [pvlan_item(**ADD_2212)])[0] == "exit"

    c = ctrl()
    c.previews = [measured_preview("G6-M0b")]
    status, res = run(c, [pvlan_item(**ADD_2212)], patch_version=patch_version)
    assert status == "exit", res
    assert c.sent_nv(IF7)[0] == PVLAN
    assert _request_log(c) == _request_log(reference)
    assert "PATCH_VERSION" not in json.dumps(_request_log(c)).upper()


@pytest.mark.parametrize("patch_version", PATCH_VALUES)
def test_native_pvlan_deleted_reset_is_unchanged_by_patch_value(patch_version):
    c = ctrl()
    c.previews = [reset_preview()]
    status, res = run(c, [{"name": IF7, "switch": ["10.0.0.1"]}], state="deleted",
                      patch_version=patch_version)
    assert status == "exit", res
    policy, nv = c.sent_nv()
    assert policy == TRUNK and "PVLAN_MODE" not in nv
    assert c.order() == ["MODIFY", "PREVIEW", "DEPLOY"]


@pytest.mark.parametrize("patch_version", PATCH_VALUES)
def test_native_pvlan_query_is_read_only_for_any_patch_value(patch_version):
    c = ctrl()
    status, _res = run(c, [{"name": IF7, "switch": ["10.0.0.1"]}], state="query",
                       patch_version=patch_version)
    assert status == "exit"
    assert c.mutating() == [] and c.requests(mark=PREVIEW_MARK) == []


@pytest.mark.parametrize("patch_version", PATCH_VALUES)
def test_trunk_to_pvlan_transition_never_carries_registered_trunk_values(patch_version):
    """The registry carry-forward is same-parent only: registered values the controller holds on
    int_trunk_host (GUARD_MODE, aclFilter) must not be copied into the new int_pvlan_host payload,
    whatever the patch context. (lldpTransmit/lldpReceive are a separate, PVLAN-native
    preservation owned by interface_pvlan.PRESERVE_ALWAYS and are not asserted here.)"""
    have = dict(trunk_host_nv(IF7), GUARD_MODE="root", aclFilter="PILOT-ACL")
    c = ctrl(nv=have, policy=TRUNK)
    c.previews = [recreate_preview()]
    item = pvlan_item(
        pvlan_mode="trunk promiscuous", admin_state=False, native_vlan="2301", allowed_vlans="2301",
        pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2211"}],
    )
    status, res = run(c, [item], patch_version=patch_version)
    assert status == "exit", res
    policy, nv = c.sent_nv(IF7)
    assert policy == PVLAN
    assert "GUARD_MODE" not in nv and "aclFilter" not in nv
    assert c.order() == ["MODIFY", "PREVIEW", "DEPLOY"]


@pytest.mark.parametrize("patch_version", [p for p in PATCH_VALUES if p.id in ("omitted", "unapproved")])
def test_registered_key_on_a_pvlan_profile_needs_an_approved_patch(patch_version):
    """Disable_lldp_transmit is a registered int_pvlan_host companion now. Without an approved patch_version the
    explicit field is refused with the engine's patch message before any write or preview (the native siblings of the same
    item included). The approved/ND 4.4.1 side is covered by test_dcnm_intf_pvlan_companions_c1.py."""
    c = ctrl()
    c.previews = [measured_preview("G6-M0b")]
    item = pvlan_item(disable_lldp_transmit=True, **copy.deepcopy(ADD_2212))
    status, res = run(c, [item], patch_version=patch_version)
    assert status == "fail"
    assert "'disable_lldp_transmit' requires caller-supplied patch_version" in res["msg"]
    assert c.mutating() == [] and c.requests(mark=PREVIEW_MARK) == []
