"""A leaf role-default reset of an int_access_host Ethernet with loggingEventPortLinkStatus true.

Measured on NDFC 12.6.0.267, SMU 4.3.1.0175006017, NX-OS 10.5(5), one leaf access port: a legacy interface/modify from
int_access_host with the line configured to the role default int_trunk_host left the pending
`logging event port link-status default`; after one port deploy the running, intent and children equalled the baseline.
The registry declares that transition for this field only (POLICY_CHANGE_CLEARS_INLINE_FIELDS in the generator); every
other access field and destination keeps its contract.

Real main() through gie_withdrawal_harness; only inventory, transport and sleep are mocked. Values are synthetic.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import patch

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import BINDING_TABLE, resolve_by_nvpair
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import gie_withdrawal_harness as h
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.test_gie_passthrough_bindings import (
    _as_slice_rows, _load_generator,
)
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.test_gie_smu017_batch1_states import (
    _as_have, _deploys, _emitted, _have_for, _run,
)

LOGGING_ON = {**h.BASE_ACCESS, "logging_event_port_link_status": True}
NEUTRAL = dict(h.BASE_ACCESS)
IF_CTL = "Ethernet1/40"
CONTROL = {**h.BASE_ACCESS, "description": "control"}
NAMED = [{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}]


def _shape(calls):
    return [(c["method"], c["path"].split("/rest/")[-1].split("?")[0]) for c in calls]


# ------------------------------------------------------------------ the declaration is scoped to one field
def test_only_the_logging_row_declares_the_trunk_destination():
    marked = {(r["parent_template"], r["parent_nvpair"]): tuple(r["cleared_on_change_to"])
              for r in BINDING_TABLE if r.get("cleared_on_change_to")}
    assert marked[(h.ACCESS, "loggingEventPortLinkStatus")] == (h.ROUTED, h.TRUNK)
    others = {k: v for k, v in marked.items() if k != (h.ACCESS, "loggingEventPortLinkStatus")}
    assert set(others.values()) == {(h.ROUTED,)}, "no other row may gain a destination"
    assert resolve_by_nvpair(h.TRUNK, "loggingEventPortLinkStatus") is None


def test_the_generator_refuses_the_field_destination_on_another_row():
    gen = _load_generator()
    rows = _as_slice_rows(BINDING_TABLE)
    assert len(gen.compile_rows(rows)) == len(BINDING_TABLE)
    other = next(r for r in rows if (r["parent_template"], r["parent_nvpair"]) == (h.ACCESS, "aclFilter"))
    other["cleared_on_change_to"] = (h.ROUTED, h.TRUNK)
    with pytest.raises(ValueError, match="cleared_on_change_to"):
        gen.compile_rows(rows)


# ------------------------------------------------------------------ named deleted and overridden omission (leaf)
@pytest.mark.parametrize("state", ["deleted", "overridden"])
def test_leaf_reset_with_logging_on_resets_to_trunk_and_leaves_the_control(state):
    have = _have_for(h.IF_A, LOGGING_ON) + _have_for(IF_CTL, CONTROL)
    assert have[0]["interfaces"][0]["nvPairs"]["loggingEventPortLinkStatus"] == "true"
    configs = NAMED if state == "deleted" else [h.cfg(IF_CTL, dict(CONTROL))]
    result, calls = _run(configs, state, have, role="leaf")
    assert not result.get("failed"), result.get("msg")
    emitted = _emitted(calls)
    assert list(emitted) == [(h.SERIAL, h.IF_A)], emitted.keys()
    policy, nv = emitted[(h.SERIAL, h.IF_A)]
    assert policy == h.TRUNK
    assert "loggingEventPortLinkStatus" not in nv, "a source-only nvPair is never written into the destination"
    assert _deploys(calls) == [(h.SERIAL, h.IF_A)]
    assert [c["path"].split("/rest/")[-1] for c in h.writes(calls)] == ["interface/modify", "globalInterface/deploy"]
    # identical request shape and payload to the same reset of a port without logging
    neutral_have = _have_for(h.IF_A, NEUTRAL) + _have_for(IF_CTL, CONTROL)
    n_result, n_calls = _run(configs, state, neutral_have, role="leaf")
    assert not n_result.get("failed"), n_result.get("msg")
    assert _shape(calls) == _shape(n_calls)
    assert _emitted(n_calls)[(h.SERIAL, h.IF_A)] == (policy, nv)


@pytest.mark.parametrize("state", ["deleted", "overridden"])
def test_repeat_after_the_reset_writes_nothing(state):
    have = _have_for(h.IF_A, LOGGING_ON) + _have_for(IF_CTL, CONTROL)
    configs = NAMED if state == "deleted" else [h.cfg(IF_CTL, dict(CONTROL))]
    result, calls = _run(configs, state, have, role="leaf")
    assert not result.get("failed"), result.get("msg")
    policy, nv = _emitted(calls)[(h.SERIAL, h.IF_A)]
    after = _as_have(policy, h.IF_A, nv) + _have_for(IF_CTL, CONTROL)
    result, calls = _run(configs, state, after, role="leaf")
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


# ------------------------------------------------------------------ preserved behaviour
def test_retained_interface_still_withdraws_the_field_on_its_own_policy():
    have = _have_for(h.IF_A, LOGGING_ON) + _have_for(IF_CTL, CONTROL)
    result, calls = _run([h.cfg(h.IF_A, dict(NEUTRAL)), h.cfg(IF_CTL, dict(CONTROL))], "overridden", have, role="leaf")
    assert not result.get("failed"), result.get("msg")
    emitted = _emitted(calls)
    assert list(emitted) == [(h.SERIAL, h.IF_A)]
    assert emitted[(h.SERIAL, h.IF_A)][0] == h.ACCESS
    assert emitted[(h.SERIAL, h.IF_A)][1]["loggingEventPortLinkStatus"] == "false"


@pytest.mark.parametrize("state", ["deleted", "overridden"])
def test_border_reset_is_unchanged(state):
    have = _have_for(h.IF_A, LOGGING_ON)
    configs = NAMED if state == "deleted" else []
    result, calls = _run(configs, state, have, role="border")
    assert not result.get("failed"), result.get("msg")
    policy, nv = _emitted(calls)[(h.SERIAL, h.IF_A)]
    assert policy == h.ROUTED and "loggingEventPortLinkStatus" not in nv


@pytest.mark.parametrize("state", ["deleted", "overridden"])
def test_an_undeclared_destination_is_still_refused(state):
    """Forced role default int_pvlan_host: not declared for the field, so the refusal stands."""
    orig = module.DcnmIntf.dcnm_intf_get_default_eth_payload

    def pvlan_default(self, ifname, sno, fabric):
        payload = orig(self, ifname, sno, fabric)
        payload["policy"] = "int_pvlan_host"
        return payload
    have = _have_for(h.IF_A, LOGGING_ON)
    with patch.object(module.DcnmIntf, "dcnm_intf_get_default_eth_payload", pvlan_default):
        result, calls = _run(NAMED if state == "deleted" else [], state, have, role="leaf")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    assert "loggingEventPortLinkStatus" in result["msg"] and "int_access_host -> int_pvlan_host" in result["msg"]


@pytest.mark.parametrize("state", ["deleted", "overridden"])
def test_an_unreadable_value_is_still_refused(state):
    have = _have_for(h.IF_A, LOGGING_ON)
    have[0]["interfaces"][0]["nvPairs"]["loggingEventPortLinkStatus"] = "maybe"
    result, calls = _run(NAMED if state == "deleted" else [], state, have, role="leaf")
    assert result.get("failed") and h.writes(calls) == []
    assert "not readable as its type" in result["msg"]
