"""PR725 advisory 5766305127, item 4: a synthetic 1,000 / 5,000-interface regression through the real `main()`.

What runs: the module's real argument spec, validation, builder, `gie_contribute_nvpairs`, comparator, carry-forward / withdrawal and
request assembly (`gie_withdrawal_harness.run_configs`). Only inventory, transport and sleep are replaced. One switch, routed
Ethernet interfaces with the OSPF context and two registered bindings that have a reset (`ospf_mtu_ignore`, `ospf_shutdown`).

What is asserted (deterministic, CI-safe):
- calls per endpoint do not grow with the interface count; writes are one bulk request or none;
- every outbound interface entry equals the model (the module's own single-interface entry, with only the name and address varied),
  so the serialized size is the model's size, byte for byte;
- merged omission preserves the registered fields with zero writes; an identical second application writes nothing;
- replaced / overridden omission withdraw them to their reset (no general carry-forward);
- a persistently failing interface read keeps the refusal with zero writes and a bounded number of requests and scheduled sleeps.

What is NOT asserted: wall-clock time (see `pr725_scale_benchmark.py` for repeatable measurements), controller limits, controller CPU,
or any live performance. Synthetic identities only (RFC 2544 benchmarking range); NOT LIVE TESTED.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import ipaddress
import json
from unittest import mock

import pytest

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from . import gie_withdrawal_harness as H

SIZES = (1000, 5000)
NET = ipaddress.ip_network("198.18.0.0/15")
REGISTERED = {"ospf_mtu_ignore": True, "ospf_shutdown": True}
REGISTERED_WIRE = ("ospfMtuIgnore", "ospfShutdown")
READ_ENDPOINTS = {"accessmode": 1, "policies": 1, "bulk": 1, "summary": 1}
# The bounded-recovery contract (test_pr725_read_budget_bound.py): two failed invocations x three attempts per switch.
FAILED_READ_CEILING = 6
# The harness transport, captured before any test patches `H._transport`.
REAL_TRANSPORT = H._transport


def name(i):
    return "Ethernet1/%d" % (i + 1)


def addr(i):
    return str(NET.network_address + 4 * i + 1)


def configs(n, omit=(), **extra):
    out = []
    for i in range(n):
        prof = H.base_for(H.ROUTED, **dict(H.OSPF_CTX, **dict(REGISTERED, **extra)))
        for key in omit:
            prof.pop(key)
        prof["ipv4_addr"] = addr(i)
        out.append(H.cfg(name(i), prof, deploy=False))
    return out


def endpoint(path):
    if "accessmode" in path:
        return "accessmode"
    if "/control/policies/switches/" in path:
        return "policies"
    if "/interface/detail" in path:
        return "summary"
    if "/interface?" in path:
        return "individual" if "&ifName=" in path else "bulk"
    return "other"


def read_counts(calls):
    counts = {}
    for c in H.split_calls(calls)["reads"]:
        counts[endpoint(c["path"])] = counts.get(endpoint(c["path"]), 0) + 1
    return counts


def entries(calls):
    found = []
    H._collect_policies([c["payload"] for c in H.split_calls(calls)["updates"]], found)
    return found


def have_from(calls):
    """The module's own outbound policies, stored as the controller would return them."""
    have = copy.deepcopy(entries(calls))
    for policy in have:
        for intf in policy["interfaces"]:
            intf["interfaceType"] = "INTERFACE_ETHERNET"
            intf["fabricName"] = H.FABRIC
    return have


def run(n_or_configs, state, have=None, **kw):
    cfgs = configs(n_or_configs) if isinstance(n_or_configs, int) else n_or_configs
    return H.run_configs(cfgs, state, have=have, deploy=False, **kw)


_MODEL = {}


def model():
    """One interface's outbound entry and the nvPairs that carry the per-interface name and address, from two real runs."""
    if not _MODEL:
        result, calls = run(2, "merged")
        assert result.get("changed") is True, result.get("msg")
        (policy,) = entries(calls)
        first, second = policy["interfaces"]
        varying = sorted(k for k in first["nvPairs"] if first["nvPairs"][k] != second["nvPairs"][k])
        _MODEL.update(policy=policy["policy"], template=first, varying=varying,
                      head={k: v for k, v in policy.items() if k != "interfaces"})
    return _MODEL


def expected_entry(i):
    m = model()
    entry = copy.deepcopy(m["template"])
    entry["ifName"] = name(i)
    for key in m["varying"]:
        value = entry["nvPairs"][key]
        entry["nvPairs"][key] = value.replace(name(0), name(i)).replace(addr(0), addr(i))
    return entry


def assert_one_bulk_update_matching_the_model(calls, n):
    split = H.split_calls(calls)
    assert len(split["updates"]) == 1 and split["deploys"] == [] and split["other"] == []
    (policy,) = entries(calls)
    m = model()
    assert {k: v for k, v in policy.items() if k != "interfaces"} == m["head"]
    assert len(policy["interfaces"]) == n
    expected = [expected_entry(i) for i in range(n)]
    assert policy["interfaces"] == expected
    sent = split["updates"][0]["payload"]
    model_policy = dict(m["head"], interfaces=expected)
    model_payload = [model_policy] if isinstance(sent, list) else model_policy
    # Byte for byte, in the module's own key order: the serialized request is exactly the model's.
    assert json.dumps(sent) == json.dumps(model_payload)
    return len(json.dumps(sent))


# ------------------------------------------------------------------ model sanity
def test_the_model_varies_only_the_name_and_address_and_carries_the_registered_fields():
    m = model()
    assert m["policy"] == H.ROUTED
    assert set(m["varying"]) <= {"INTF_NAME", "IP", "CONF", "DESC"} and "IP" in m["varying"]
    for wire in REGISTERED_WIRE:
        assert m["template"]["nvPairs"][wire] == "true"


# ------------------------------------------------------------------ both sizes: healthy path, repeat, merged omission, failed read
@pytest.mark.parametrize("n", SIZES)
def test_healthy_create_reads_a_constant_number_of_times_and_sends_one_model_payload(n):
    result, calls = run(n, "merged")
    assert result.get("changed") is True, result.get("msg")
    assert read_counts(calls) == READ_ENDPOINTS
    assert_one_bulk_update_matching_the_model(calls, n)


@pytest.mark.parametrize("n", SIZES)
def test_identical_second_application_writes_nothing(n):
    _result, calls = run(n, "merged")
    result, calls2 = run(n, "merged", have=have_from(calls))
    assert result.get("changed") is False, result.get("msg")
    assert H.writes(calls2) == []
    assert read_counts(calls2) == READ_ENDPOINTS


@pytest.mark.parametrize("n", SIZES)
def test_merged_omission_preserves_the_registered_fields_with_zero_writes(n):
    _result, calls = run(n, "merged")
    result, calls2 = run(configs(n, omit=REGISTERED), "merged", have=have_from(calls))
    assert result.get("changed") is False, result.get("msg")
    assert H.writes(calls2) == []


def failing_transport(calls, have):
    real = REAL_TRANSPORT(calls, have)

    def send(mod, method, path, payload=None):
        if method == "GET" and "/interface?" in path:
            calls.append({"method": method, "path": path, "payload": None})
            return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": []}
        return real(mod, method, path, payload)
    return send


@pytest.mark.parametrize("n", SIZES)
def test_failed_interface_read_keeps_the_refusal_with_bounded_requests_and_zero_writes(n):
    sleeps = []
    with mock.patch.object(H, "_transport", failing_transport):
        result, calls = run(n, "merged", extra_patch=mock.patch.object(module.time, "sleep", side_effect=sleeps.append))
    assert result.get("failed") is True
    assert "could not be read authoritatively" in result["msg"]
    assert H.writes(calls) == []
    counts = read_counts(calls)
    assert counts.get("bulk", 0) + counts.get("individual", 0) <= FAILED_READ_CEILING
    assert len(sleeps) <= FAILED_READ_CEILING and sum(sleeps) <= FAILED_READ_CEILING


# ------------------------------------------------------------------ 1,000 only: state semantics at scale
N_STATES = 1000


@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_replaced_and_overridden_omission_withdraw_the_registered_fields_to_their_reset(state):
    _result, calls = run(N_STATES, "merged")
    result, calls2 = run(configs(N_STATES, omit=REGISTERED), state, have=have_from(calls))
    assert result.get("changed") is True, result.get("msg")
    split = H.split_calls(calls2)
    assert len(split["updates"]) == 1 and split["deploys"] == []
    sent = [i for p in entries(calls2) for i in p["interfaces"]]
    assert sorted(i["ifName"] for i in sent) == sorted(name(i) for i in range(N_STATES))
    for intf in sent:
        assert all(intf["nvPairs"][wire] == "false" for wire in REGISTERED_WIRE), intf["ifName"]


def test_merged_unrelated_change_carries_the_omitted_registered_fields_forward():
    _result, calls = run(N_STATES, "merged")
    result, calls2 = run(configs(N_STATES, omit=REGISTERED, description="scale-changed"), "merged", have=have_from(calls))
    assert result.get("changed") is True, result.get("msg")
    sent = [i for p in entries(calls2) for i in p["interfaces"]]
    assert len(sent) == N_STATES and len(H.split_calls(calls2)["updates"]) == 1
    for intf in sent:
        assert intf["nvPairs"]["DESC"] == "scale-changed"
        assert all(intf["nvPairs"][wire] == "true" for wire in REGISTERED_WIRE), intf["ifName"]


def transient_bulk_failure(failed_attempts):
    def factory(calls, have):
        real = REAL_TRANSPORT(calls, have)
        seen = {"bulk": 0}

        def send(mod, method, path, payload=None):
            if method == "GET" and "/interface?" in path and "&ifName=" not in path:
                seen["bulk"] += 1
                if seen["bulk"] <= failed_attempts:
                    calls.append({"method": method, "path": path, "payload": None})
                    return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": []}
            return real(mod, method, path, payload)
        return send
    return factory


@pytest.mark.parametrize("failed_attempts,bulk,individual", [(1, 2, 0), (3, 3, N_STATES)],
                         ids=["recovered_within_the_retry", "bulk_invocation_failed"])
def test_read_recovery_cost_at_scale(failed_attempts, bulk, individual):
    """The existing recovery contract at 1,000 interfaces (test_pr725_read_budget_bound.py): one failed attempt is absorbed by the
    retry; a failed bulk invocation falls back to one successful individual read per interface (3 + N), then writes once."""
    with mock.patch.object(H, "_transport", transient_bulk_failure(failed_attempts)):
        result, calls = run(N_STATES, "merged")
    assert result.get("changed") is True and not result.get("failed"), result.get("msg")
    counts = read_counts(calls)
    assert counts.get("bulk") == bulk and counts.get("individual", 0) == individual
    assert len(H.split_calls(calls)["updates"]) == 1
