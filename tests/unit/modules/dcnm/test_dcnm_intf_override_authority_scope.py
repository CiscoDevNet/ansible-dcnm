"""The authority gate must guard mutations, not the enumeration that precedes them.

``dcnm_intf_get_diff_overridden`` walks ``have_all``: every interface on every switch. It only
acts on a subset of that walk -- physical Ethernet in one branch, and port-channel, loopback,
sub-interface, vPC, VLAN and FEX in another. ``INTERFACE_MGMT`` matches neither, so an override
sweep never creates, deletes, resets or deploys mgmt0.

The gate used to run once at the top of that walk. On a switch whose interface state could not
be read, it therefore failed on whichever interface came first -- in practice mgmt0 -- and the
error named an interface the sweep was never going to touch. A NAC remove step running
``state: overridden`` with an empty config hit this on every run.

Moving the gate to each mutation decision fixes that, but the fix is only correct if the gate is
still armed. Both properties are asserted here: an out-of-scope interface must not trip it, and
an in-scope one on the same unreadable switch still must.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import types
from unittest import mock

import pytest

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

DcnmIntf = dcnm_interface.DcnmIntf

SERIAL = "9U3E8ZSI94T"
FABRIC = "juarocha-nac-fabric1"


class _FailJson(Exception):
    """Stand-in for AnsibleModule.fail_json, which terminates the module."""


def _have(if_name, if_type, is_physical="false"):
    """One entry as ``have_all`` carries it.

    ``underlayPolicies`` is an empty list rather than ``None`` on purpose: the sweep reads
    ``None`` as "already being deleted by the controller" and skips the interface, which would
    make a deletion candidate look like a non-candidate and hide what these tests assert.
    """
    return {
        "ifName": if_name,
        "serialNo": SERIAL,
        "fabricName": FABRIC,
        "ifType": if_type,
        "isPhysical": is_physical,
        "alias": "",
        "deleteReason": None,
        "markDeleted": "false",
        "deletable": "true",
        "complianceStatus": "In-Sync",
        "underlayPolicies": [],
        "mgmtIpAddress": "192.0.2.10",
        "interfaceDbId": 0,
    }


def _stub(have_all):
    """A sweep over an unreadable switch, with nothing in the desired state.

    ``config: []`` with ``state: overridden`` is what a NAC remove step sends: reset every
    interface in the fabric. ``want`` is empty, so nothing in ``have_all`` is protected by being
    wanted -- every in-scope interface is a deletion candidate.
    """
    s = types.SimpleNamespace()

    s.have_all = have_all
    s.want = []
    s.fabric = FABRIC

    # The switch could not be read: a bulk GET for this serial failed.
    s.intf_detail_cache = {}
    s.intf_detail_cached_snos = set()
    s.intf_detail_failed_keys = set()
    s.intf_detail_authoritative_absent_keys = set()
    s.intf_detail_fetch_failed_snos = {SERIAL}

    s.module = mock.Mock()
    s.module.params = {"override_intf_types": [], "state": "overridden", "deploy": True}
    s.module.fail_json.side_effect = _FailJson

    s.changed_dict = [
        {
            "deleted": [], "deploy": [], "delete_deploy": [], "replaced": [],
            "skipped": [], "deferred": [], "debugs": [], "merged": [],
            "overridden": [], "query": [],
        }
    ]
    # The method resets these itself; they exist so the stub is complete before the call.
    s.diff_create = []
    s.diff_delete = [[] for _slot in range(9)]
    s.diff_delete_deploy = [[] for _slot in range(9)]
    s.diff_deploy = []
    s.diff_replace = []

    # The module's real mapping. Note it has no INTERFACE_MGMT entry at all: management
    # interfaces are not a type the override sweep indexes for mutation.
    s.int_index = {
        "INTERFACE_PORT_CHANNEL": 0,
        "INTERFACE_VPC": 1,
        "INTERFACE_ETHERNET": 2,
        "INTERFACE_LOOPBACK": 3,
        "SUBINTERFACE": 4,
        "INTERFACE_VLAN": 5,
        "STRAIGHT_TROUGH_FEX": 6,
        "AA_FEX": 7,
        "BREAKOUT": 8,
    }
    s.int_types = {"breakout": "BREAKOUT"}

    # cfg == [] makes the method fetch have_all per switch; ours is already populated for this
    # serial, so the fetch is never reached.
    s.ip_sn = {"192.0.2.10": SERIAL}
    s.dcnm_intf_get_have_all = mock.Mock()

    # A no-op: the authority sets above already express the outcome this fetch would have had,
    # so the real one would only overwrite the condition under test.
    s.dcnm_intf_bulk_fetch_intf_info = mock.Mock()

    # Real: the gate and everything it reads its verdict from.
    s.dcnm_intf_require_detail_authority = types.MethodType(
        DcnmIntf.dcnm_intf_require_detail_authority, s
    )
    s.dcnm_intf_detail_unavailable = types.MethodType(
        DcnmIntf.dcnm_intf_detail_unavailable, s
    )
    s._dcnm_intf_authority_key = DcnmIntf._dcnm_intf_authority_key
    s._dcnm_intf_query_serial = DcnmIntf._dcnm_intf_query_serial
    s._dcnm_intf_serial_parts = DcnmIntf._dcnm_intf_serial_parts

    # Stubbed: everything the sweep would otherwise reach out to.
    s.dcnm_intf_build_can_be_replaced_lookups = mock.Mock()
    s.dcnm_intf_compare_want_and_have = mock.Mock()
    s.dcnm_intf_capability_enabled = mock.Mock(return_value=True)
    s.dcnm_intf_get_default_eth_payload = mock.Mock(return_value={})
    s.dcnm_intf_get_intf_info = mock.Mock(return_value=[])
    s.dcnm_intf_merge_intf_info = mock.Mock()
    s.dcnm_intf_can_be_replaced = mock.Mock(return_value=(False, {}))
    s.dcnm_intf_is_vpc_peer_link_port_channel = mock.Mock(return_value=False)
    s.dcnm_intf_get_underlay_policy_source = mock.Mock(return_value=None)
    s.dcnm_intf_skip_non_resolvable_deferred = mock.Mock()
    s.dcnm_intf_skip_physical_default_not_allowed = mock.Mock()
    s.dcnm_compare_default_payload = mock.Mock(return_value="DCNM_INTF_NO_MATCH")
    s.dcnm_intf_get_parent = mock.Mock(return_value=(False, ""))
    return s


def _run(stub):
    """``cfg == []`` is what a NAC remove step sends: no desired state at all."""
    return types.MethodType(DcnmIntf.dcnm_intf_get_diff_overridden, stub)([])


def test_out_of_scope_mgmt_interface_does_not_trip_the_gate():
    """mgmt0 on an unreadable switch must not fail the sweep.

    INTERFACE_MGMT matches neither branch of the override, so no mutation is ever decided for
    it. Failing here reported an interface that was not at stake and masked whichever one
    actually lacked state.
    """
    stub = _stub([_have("mgmt0", "INTERFACE_MGMT")])

    _run(stub)

    assert stub.module.fail_json.call_count == 0, (
        "the gate fired on mgmt0, an interface the override sweep never touches"
    )
    assert all(bucket == [] for bucket in stub.diff_delete)
    assert stub.diff_deploy == []
    assert stub.changed_dict[0]["deleted"] == []


def test_in_scope_interface_on_the_same_unreadable_switch_still_trips_the_gate():
    """The guard must stay armed -- otherwise the fix is just a removal.

    A port-channel absent from ``want`` is a deletion candidate. Deciding to delete it over
    state the controller never confirmed is exactly what the gate exists to stop.
    """
    stub = _stub([_have("Port-channel10", "INTERFACE_PORT_CHANNEL")])

    with pytest.raises(_FailJson):
        _run(stub)

    msg = stub.module.fail_json.call_args.kwargs["msg"]
    assert "Port-channel10" in msg
    assert "no change was sent" in msg


def test_mgmt_interface_does_not_mask_a_real_gap_on_the_same_switch():
    """With both present, the failure must name the interface actually at stake.

    This is the shape of the reported bug: mgmt0 is walked first, so a top-of-loop gate blamed
    it and the port-channel behind it was never reached.
    """
    stub = _stub([
        _have("mgmt0", "INTERFACE_MGMT"),
        _have("Port-channel10", "INTERFACE_PORT_CHANNEL"),
    ])

    with pytest.raises(_FailJson):
        _run(stub)

    msg = stub.module.fail_json.call_args.kwargs["msg"]
    assert "Port-channel10" in msg
    assert "mgmt0" not in msg, "the failure still names the wrong interface"


def test_readable_switch_sweeps_without_the_gate_firing():
    """Nothing above weakens the normal path: readable state proceeds as before."""
    stub = _stub([_have("Port-channel10", "INTERFACE_PORT_CHANNEL")])
    stub.intf_detail_fetch_failed_snos = set()
    stub.intf_detail_cached_snos = {SERIAL}

    _run(stub)

    assert stub.module.fail_json.call_count == 0
    assert stub.changed_dict[0]["deleted"], "an unwanted port-channel should be deleted"
