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


import pytest

from .dcnm_interface.helpers.override_scope import SERIAL, _FailJson, _have, _run, _stub


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


def test_unreadable_summary_refuses_the_sweep_even_when_have_all_is_empty():
    """The summary itself could not be read: have_all is empty for this switch, so no gate inside the walk could fire.
    The sweep must refuse on the summary authority before planning any mutation."""
    stub = _stub([])
    stub.have_all_cached_snos = set()
    stub.have_all_failed_snos = {SERIAL}
    with pytest.raises(_FailJson):
        _run(stub)
    assert "summary" in str(stub.module.fail_json.call_args)
    assert stub.diff_replace == [] and stub.diff_deploy == []
