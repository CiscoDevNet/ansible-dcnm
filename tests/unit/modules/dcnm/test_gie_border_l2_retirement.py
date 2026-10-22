"""D-2 / P2: a border (non-leaf) reset of an int_trunk_host or int_access_host Ethernet to the role default int_routed_host
with a port ACL, spanning-tree port type or guard, or flowcontrol configured.

These parents render their lines inline (no child policy). When the reset replaces them with int_routed_host the
controller negates every running line the routed stanza does not expect (measured on one border trunk port, flowcontrol
included). The generator declares that transition per parent and destination (cleared_on_change_to); the reset now
proceeds with the module's ordinary routed default payload, one write, and never carries a source-only key. The access
parent is covered by template parity only. A destination that is not declared, an unreadable value, the leaf same-parent
reset, and P1/P3 are unchanged. Real main() through gie_withdrawal_harness; values are synthetic.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
from unittest.mock import patch

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table as table
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import gie_withdrawal_harness as h
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.test_dcnm_intf_default_reset_registered_f2 import (
    STATES,
    nvpairs_of_reset,
    reset_policies,
    reset_wire,
    run,
)

ACL = "SYN-ACL"
TRUNK_FIELDS = {"aclFilter": ACL, "spanningTreePortType": "network", "GUARD_MODE": "root",
                "flowcontrolReceive": "on", "flowcontrolSend": "on"}
ACCESS_FIELDS = {"aclFilter": ACL, "spanningTreePortType": "network", "flowcontrolReceive": "on", "flowcontrolSend": "on"}
SOURCE_ONLY = ("aclFilter", "spanningTreePortType", "GUARD_MODE", "flowcontrolReceive", "flowcontrolSend")


def have_of(parent, nv):
    have = copy.deepcopy(h.build_have(parent))
    have[0]["interfaces"][0]["nvPairs"].update(nv)
    return have


# ------------------------------------------------------------------ the finding, fixed
@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("parent, fields", [(h.TRUNK, TRUNK_FIELDS), (h.ACCESS, ACCESS_FIELDS)], ids=["trunk", "access"])
def test_border_reset_sends_the_ordinary_routed_payload(state, parent, fields):
    _r0, calls0 = run(state, have_of(parent, {}), "border")                 # neutral port of the same parent
    result, calls = run(state, have_of(parent, fields), "border")
    assert not result.get("failed"), result.get("msg")
    assert len(h.split_calls(calls)["updates"]) == 1 and reset_policies(calls)[0]["policy"] == h.ROUTED
    sent = nvpairs_of_reset(calls)
    assert not any(k in sent for k in SOURCE_ONLY)                          # never written into int_routed_host
    assert sent == nvpairs_of_reset(calls0)                                  # identical to the neutral port's reset
    assert [(c["method"], c["path"]) for c in calls] == [(c["method"], c["path"]) for c in calls0]
    assert ACL not in str([c.get("payload") for c in calls])


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("field, value", [
    ("aclFilter", ACL), ("spanningTreePortType", "normal"), ("GUARD_MODE", "loop"), ("GUARD_MODE", "none"),
    ("flowcontrolReceive", "on"), ("flowcontrolSend", "on"),
])
def test_each_trunk_field_alone_is_cleared_by_the_reset(state, field, value):
    result, calls = run(state, have_of(h.TRUNK, {field: value}), "border")
    assert not result.get("failed"), result.get("msg")
    assert field not in nvpairs_of_reset(calls) and reset_policies(calls)[0]["policy"] == h.ROUTED


@pytest.mark.parametrize("state", STATES)
def test_fields_both_parents_register_keep_the_destination_reset(state):
    result, calls = run(state, have_of(h.TRUNK, dict(TRUNK_FIELDS, lldpReceive="true", queuingStats="true")), "border")
    assert not result.get("failed"), result.get("msg")
    sent = nvpairs_of_reset(calls)
    assert sent["lldpReceive"] == reset_wire(h.ROUTED, "lldpReceive")
    assert sent["queuingStats"] == reset_wire(h.ROUTED, "queuingStats")


@pytest.mark.parametrize("state", STATES)
def test_second_run_over_the_reset_is_a_noop(state):
    _r1, calls1 = run(state, have_of(h.TRUNK, TRUNK_FIELDS), "border")
    have = copy.deepcopy(reset_policies(calls1))
    have[0]["interfaces"][0].update(interfaceType="INTERFACE_ETHERNET", fabricName=h.FABRIC)
    result, calls = run(state, have, "border")
    assert not result.get("failed") and result["changed"] is False and h.writes(calls) == [], result.get("msg")


# ------------------------------------------------------------------ boundaries
@pytest.mark.parametrize("state", STATES)
def test_without_the_declaration_the_refusal_returns(state):
    rows = [table.resolve_by_nvpair(h.TRUNK, n) for n in SOURCE_ONLY]
    with patch.dict(rows[0], {"cleared_on_change_to": ()}), patch.dict(rows[2], {"cleared_on_change_to": ()}):
        result, calls = run(state, have_of(h.TRUNK, TRUNK_FIELDS), "border")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    msg = result["msg"]
    assert "acl_filter (aclFilter) on %s [%s], int_trunk_host -> int_routed_host" % (h.IF_A, h.SERIAL) in msg
    assert "guard_mode (GUARD_MODE)" in msg and "flowcontrol_receive" not in msg and ACL not in msg


@pytest.mark.parametrize("state", STATES)
def test_a_destination_not_declared_keeps_the_refusal(state):
    """int_trunk_host -> int_access_host is not a declared transition (not reachable by switch role today); forced here by
    making the role default an access payload. GUARD_MODE is not an access field, so it must be refused."""
    orig = module.DcnmIntf.dcnm_intf_get_default_eth_payload

    def access_default(self, ifname, sno, fabric):
        payload = orig(self, ifname, sno, fabric)
        payload["policy"] = h.ACCESS
        return payload
    with patch.object(module.DcnmIntf, "dcnm_intf_get_default_eth_payload", access_default):
        result, calls = run(state, have_of(h.TRUNK, {"GUARD_MODE": "root"}), "leaf")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    assert "guard_mode (GUARD_MODE) on %s [%s], int_trunk_host -> int_access_host" % (h.IF_A, h.SERIAL) in result["msg"]


@pytest.mark.parametrize("state", STATES)
def test_unreadable_value_still_refuses(state):
    result, calls = run(state, have_of(h.TRUNK, {"spanningTreePortType": "edge"}), "border")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    assert "not readable as its type" in result["msg"]


@pytest.mark.parametrize("state", STATES)
def test_leaf_same_parent_reset_keeps_the_verified_wires(state):
    result, calls = run(state, have_of(h.TRUNK, TRUNK_FIELDS), "leaf")
    assert not result.get("failed"), result.get("msg")
    sent = nvpairs_of_reset(calls)
    assert reset_policies(calls)[0]["policy"] == h.TRUNK
    for nvpair in TRUNK_FIELDS:
        assert sent[nvpair] == reset_wire(h.TRUNK, nvpair), nvpair


@pytest.mark.parametrize("state", STATES)
def test_capability_disabled_keeps_the_published_behaviour(state):
    result, calls = run(state, have_of(h.TRUNK, TRUNK_FIELDS), "border", patch_version=None)
    assert not result.get("failed"), result.get("msg")
    assert not any(k in nvpairs_of_reset(calls) for k in SOURCE_ONLY)


def test_only_the_declared_parents_carry_the_inline_marker():
    marked = {(r["parent_template"], tuple(r["cleared_on_change_to"])) for r in table.BINDING_TABLE if r.get("cleared_on_change_to")}
    # access loggingEventPortLinkStatus also declares int_trunk_host (measured for that field only)
    assert marked == {(h.TRUNK, (h.ROUTED,)), (h.ACCESS, (h.ROUTED,)), (h.ACCESS, (h.ROUTED, h.TRUNK))}
    assert sum(1 for r in table.BINDING_TABLE if r.get("cleared_on_change_to")) == 18   # + access loggingEventPortLinkStatus (0b_37)
    assert not any(r.get("cleared_on_change_to") and r.get("dropped_on_policy_change") for r in table.BINDING_TABLE)
