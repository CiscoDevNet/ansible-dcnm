"""Harness for the native Ethernet PVLAN tests: real main(), external boundary mocked only.

Self-contained and collection-local. It mocks ONLY the external boundary -- inventory, version,
the transport (dcnm_send), the bulk-API probe, fabric details and sleep -- through a stateful,
path-routed fake controller that records every request in order. Nothing under test (builder,
reconciliation, preflight, pre-deploy gate) is stubbed. Fixtures come from
fixtures/pvlan_ethernet_cases.json#dcnm_intf_pvlan_measured, sanitized from measured discovery evidence.

The fake controller APPLIES a successful modify to its stored intent, so later reads (post-deploy
readback, a second run) see what the module actually sent. Pending is NEVER computed by the fake:
each preview answer is a fixture or an explicit test value, so the gate is judged against data
it did not produce.

This file holds the harness plus its own sanity tests; it defines no product behavior.
"""

from __future__ import absolute_import, division, print_function


import json


from .dcnm_interface.helpers.ethernet_controller import (
    FIXTURE,
    FakeController,
    PREVIEW_MARK,
    RECOMPUTE_FLAGS,
    SERIAL,
    TRANSITIONS,
    preview,
)


# ---------------------------------------------------------------- harness self-tests
def test_harness_fixture_is_sanitized_and_complete():
    raw = json.dumps(FIXTURE)
    for leaked in ("9648E3J5P6M", "FAB1", "Leaf-101", "192.168.", "POLICY-"):
        assert leaked not in raw
    assert {"TU2", "TX1", "TX2", "PU3", "G6-M1", "G6-L1", "G6-MR"} <= set(TRANSITIONS)
    assert "MAPPING_LIST[]" in FIXTURE["template_variables"]


def test_harness_records_before_answering_and_never_computes_pending():
    ctrl = FakeController()
    assert ctrl(None, "GET", "/x" + PREVIEW_MARK + SERIAL + "?" + RECOMPUTE_FLAGS) == preview([])
    assert ctrl.calls[0][0] == "GET" and ctrl.order() == ["PREVIEW"]
