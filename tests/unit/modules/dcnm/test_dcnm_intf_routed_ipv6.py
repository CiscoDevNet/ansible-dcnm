"""IPv6 address and prefix on a routed Ethernet port (mode: routed, int_routed_host).

int_routed_host declares IPv6 and IPv6_PREFIX and renders `ipv6 address` only when both are set. The module accepted
ipv6_addr/ipv6_mask_len only for epl_routed and subinterfaces; for mode routed the inputs were dropped and the request
carried no IPv6 nvPair.

Every case runs real main() through gie_withdrawal_harness and asserts the CAPTURED REQUEST: policy, interface identity
and nvPairs. The default HAVE is the module's own replaced payload with the IPv6 pair set the way the controller stores
it ("" and "" when unset, as in the measured int_routed_host read in fixtures/dcnm_intf_routed_ospf_have.json); the
measured-shape cases use that 84-key read itself. Roles are the lower-case values NDFC returns ("leaf" resets to
int_trunk_host, "border" to int_routed_host). Addresses are documentation values.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import os
from unittest.mock import patch

import pytest

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import gie_withdrawal_harness as h

V6 = "2001:db8:117::1"
V6_B = "2001:db8:118::1"
V4 = "192.0.2.1"
BASE = {"mode": "routed", "ipv4_addr": V4, "ipv4_mask_len": 24, "admin_state": False, "description": "routed-v6"}
DUAL = dict(BASE, ipv6_addr=V6, ipv6_mask_len=64)
V6_ONLY = {"mode": "routed", "ipv6_addr": V6, "ipv6_mask_len": 64, "admin_state": False}

_ORIG_TRANSPORT = h._transport
PHYSICAL = {"deletable": "false", "editAllowed": "true", "mgmtIpAddress": h.SWITCH_IP}
FIXTURES = os.path.join(os.path.dirname(h.__file__), "fixtures")


def _physical_transport(calls, have):
    inner = _ORIG_TRANSPORT(calls, have)

    def send(mod, method, path, payload=None):
        resp = inner(mod, method, path, payload)
        if method == "GET" and "/interface/detail" in path and isinstance(resp.get("DATA"), list):
            for e in resp["DATA"]:
                if str(e.get("isPhysical")).lower() == "true":
                    e.update(PHYSICAL)
        return resp
    return send


def _inventory(role):
    inv = json.load(open(os.path.join(FIXTURES, "dcnm_intf_binding_configs.json")))["mock_fab_inv_data"]
    for v in inv.values():
        v["switchRole"] = role
    return inv


def run(configs, state, have=None, role="leaf"):
    with patch.object(h, "_transport", _physical_transport):
        return h.run_configs(configs, state, have=have,
                             extra_patch=patch.object(module, "get_fabric_inventory_details",
                                                      return_value=_inventory(role)))


def cfg(profile, ifname=h.IF_A):
    return h.cfg(ifname, profile)


def routed_have(ifname=h.IF_A, ipv6="", prefix="", **profile):
    """HAVE = the module's own replaced payload for a routed port, with the IPv6 pair as the controller stores it."""
    p = dict(BASE, **profile)
    p.pop("ipv6_addr", None)
    p.pop("ipv6_mask_len", None)
    _result, calls = run([cfg(p, ifname)], "replaced")
    have = h._payload_as_have(calls)
    nv = have[0]["interfaces"][0]["nvPairs"]
    nv["IPv6"] = ipv6
    nv["IPv6_PREFIX"] = prefix
    have[0]["interfaces"][0]["ifName"] = ifname
    return have


def measured_have(ipv6="", prefix=""):
    """The measured 84-key int_routed_host read (OSPF gate set to its disabled value, tag kept stored as NDFC does)."""
    m = json.load(open(os.path.join(FIXTURES, "dcnm_intf_routed_ospf_have.json")))
    nv = copy.deepcopy(m["nvPairs"])
    nv.update({"ospf": "false", "IPv6": ipv6, "IPv6_PREFIX": prefix, "INTF_NAME": h.IF_A})
    return [{"policy": m["policy"], "interfaces": [{"ifName": h.IF_A, "serialNumber": h.SERIAL, "fabricName": h.FABRIC,
                                                     "interfaceType": "INTERFACE_ETHERNET", "nvPairs": nv}]}]


def sent(calls):
    """{ifName: (policy, nvPairs)} of every interface in every configuration update."""
    found = []
    h._collect_policies([c["payload"] for c in h.split_calls(calls)["updates"]], found)
    out = {}
    for p in found:
        for i in p["interfaces"]:
            out[i["ifName"]] = (p["policy"], i.get("nvPairs", {}))
    return out


def pair(nv):
    return nv.get("IPv6", "<absent>"), nv.get("IPv6_PREFIX", "<absent>")


# ------------------------------------------------------------------ merged
def test_merged_ipv6_only_create_sends_the_pair():
    result, calls = run([cfg(V6_ONLY)], "merged")
    out = sent(calls)
    assert not result.get("failed"), result.get("msg")
    assert list(out) == [h.IF_A] and out[h.IF_A][0] == h.ROUTED
    assert pair(out[h.IF_A][1]) == (V6, "64")
    assert (out[h.IF_A][1]["IP"], out[h.IF_A][1]["PREFIX"]) == ("", "")


def test_merged_dual_stack_create_sends_both_families():
    result, calls = run([cfg(DUAL)], "merged")
    nv = sent(calls)[h.IF_A][1]
    assert not result.get("failed"), result.get("msg")
    assert (nv["IP"], nv["PREFIX"]) == (V4, "24")
    assert pair(nv) == (V6, "64")


def test_merged_changes_address_and_prefix():
    have = routed_have(ipv6=V6, prefix="64")
    result, calls = run([cfg(dict(BASE, ipv6_addr=V6_B, ipv6_mask_len=127))], "merged", have)
    out = sent(calls)
    assert not result.get("failed"), result.get("msg")
    assert list(out) == [h.IF_A]
    assert pair(out[h.IF_A][1]) == (V6_B, "127")


def test_merged_description_only_keeps_the_stored_ipv6():
    have = routed_have(ipv6=V6, prefix="64")
    result, calls = run([cfg({"mode": "routed", "description": "only-description"})], "merged", have)
    nv = sent(calls)[h.IF_A][1]
    assert not result.get("failed"), result.get("msg")
    assert nv["DESC"] == "only-description"
    assert pair(nv) == (V6, "64")
    assert (nv["IP"], nv["PREFIX"]) == (V4, "24")


def test_merged_repeat_is_a_no_op():
    have = routed_have(ipv6=V6, prefix="64")
    result, calls = run([cfg(DUAL)], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_merged_address_without_prefix_on_a_port_without_ipv6_uses_the_validated_default():
    have = routed_have()
    result, calls = run([cfg(dict(BASE, ipv6_addr=V6))], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert pair(sent(calls)[h.IF_A][1]) == (V6, "64")


def test_merged_address_without_prefix_keeps_the_stored_prefix():
    have = routed_have(ipv6=V6, prefix="127")
    result, calls = run([cfg(dict(BASE, ipv6_addr=V6_B))], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert pair(sent(calls)[h.IF_A][1]) == (V6_B, "127")


def test_merged_prefix_only_change_keeps_the_stored_address():
    have = routed_have(ipv6=V6, prefix="64")
    result, calls = run([cfg({"mode": "routed", "ipv6_mask_len": 127})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert pair(sent(calls)[h.IF_A][1]) == (V6, "127")


def test_merged_explicit_empty_address_clears_the_pair():
    have = routed_have(ipv6=V6, prefix="64")
    result, calls = run([cfg(dict(BASE, ipv6_addr=""))], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert pair(sent(calls)[h.IF_A][1]) == ("", "")


def test_merged_prefix_without_any_address_is_not_stored():
    have = routed_have()
    result, calls = run([cfg(dict(BASE, ipv6_mask_len=127, description="other"))], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert pair(sent(calls)[h.IF_A][1]) == ("", "")


def test_merged_repeat_on_the_measured_controller_shape_is_a_no_op():
    result, calls = run([cfg({"mode": "routed", "ipv6_addr": V6, "ipv6_mask_len": 64})], "merged",
                        measured_have(V6, "64"))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_merged_mixed_case_address_matches_the_stored_lower_case_value():
    result, calls = run([cfg({"mode": "routed", "ipv6_addr": V6.upper(), "ipv6_mask_len": 64})], "merged",
                        measured_have(V6, "64"))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


# ------------------------------------------------------------------ replaced
def test_replaced_changes_address_and_prefix():
    have = routed_have(ipv6=V6, prefix="64")
    result, calls = run([cfg(dict(BASE, ipv6_addr=V6_B, ipv6_mask_len=127))], "replaced", have)
    out = sent(calls)
    assert not result.get("failed"), result.get("msg")
    assert list(out) == [h.IF_A] and out[h.IF_A][0] == h.ROUTED
    assert pair(out[h.IF_A][1]) == (V6_B, "127")


def test_replaced_omission_withdraws_address_and_prefix_together():
    have = routed_have(ipv6=V6, prefix="127")
    result, calls = run([cfg(BASE)], "replaced", have)
    nv = sent(calls)[h.IF_A][1]
    assert not result.get("failed"), result.get("msg")
    assert pair(nv) == ("", "")
    assert (nv["IP"], nv["PREFIX"]) == (V4, "24")


def test_replaced_prefix_without_address_does_not_reintroduce_a_prefix():
    have = routed_have(ipv6=V6, prefix="127")
    result, calls = run([cfg(dict(BASE, ipv6_mask_len=127))], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    assert pair(sent(calls)[h.IF_A][1]) == ("", "")


def test_replaced_repeat_after_withdrawal_is_stable():
    result, calls = run([cfg(BASE)], "replaced", routed_have())
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_replaced_repeat_on_the_measured_controller_shape_is_stable():
    profile = {"mode": "routed", "ipv4_addr": "192.0.2.17", "ipv4_mask_len": 8, "ipv6_addr": V6, "ipv6_mask_len": 64}
    have = measured_have(V6, "64")
    have[0]["interfaces"][0]["nvPairs"]["PREFIX"] = "8"
    result, calls = run([cfg(profile)], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    # The measured read also holds an OSPF passive value this profile omits, so replaced writes for that key; the
    # IPv6 pair is not a reported change and travels unchanged.
    assert not any(k in d for d in h.diff_nvpairs(result) for k in ("IPv6", "IPv6_PREFIX"))
    assert pair(sent(calls)[h.IF_A][1]) == (V6, "64")


# ------------------------------------------------------------------ overridden
def test_overridden_retained_interface_withdraws_omitted_ipv6_and_leaves_the_control_alone():
    have = routed_have(h.IF_A, ipv6=V6, prefix="64") + routed_have(h.IF_B)
    result, calls = run([cfg(BASE, h.IF_A), cfg(BASE, h.IF_B)], "overridden", have)
    out = sent(calls)
    assert not result.get("failed"), result.get("msg")
    assert list(out) == [h.IF_A]
    assert out[h.IF_A][0] == h.ROUTED and pair(out[h.IF_A][1]) == ("", "")


@pytest.mark.parametrize("role, policy", [("leaf", h.TRUNK), ("border", h.ROUTED)])
def test_overridden_omitted_routed_port_is_reset_to_the_role_default_without_ipv6(role, policy):
    have = routed_have(h.IF_A, ipv6=V6, prefix="64") + routed_have(h.IF_B)
    result, calls = run([cfg(BASE, h.IF_B)], "overridden", have, role=role)
    out = sent(calls)
    assert not result.get("failed"), result.get("msg")
    assert list(out) == [h.IF_A]
    assert out[h.IF_A][0] == policy
    assert pair(out[h.IF_A][1]) == (("", "") if policy == h.ROUTED else ("<absent>", "<absent>"))


# ------------------------------------------------------------------ deleted
@pytest.mark.parametrize("role, policy", [("leaf", h.TRUNK), ("border", h.ROUTED)])
def test_deleted_resets_a_routed_port_with_ipv6_to_the_role_default(role, policy):
    have = routed_have(h.IF_A, ipv6=V6, prefix="64")
    result, calls = run([{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}], "deleted", have, role=role)
    out = sent(calls)
    assert not result.get("failed"), result.get("msg")
    assert list(out) == [h.IF_A]
    assert out[h.IF_A][0] == policy
    if policy == h.ROUTED:
        assert pair(out[h.IF_A][1]) == ("", "")
    else:
        assert "IPv6" not in out[h.IF_A][1] and "IPv6_PREFIX" not in out[h.IF_A][1]


@pytest.mark.parametrize("role", ["leaf", "border"])
def test_deleted_repeat_on_the_default_is_stable(role):
    have = routed_have(h.IF_A, ipv6=V6, prefix="64")
    _result, calls = run([{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}], "deleted", have, role=role)
    reset = []
    h._collect_policies([c["payload"] for c in h.split_calls(calls)["updates"]], reset)
    reset[0]["interfaces"][0].update({"interfaceType": "INTERFACE_ETHERNET", "fabricName": h.FABRIC})
    result, calls = run([{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}], "deleted", reset, role=role)
    assert not result.get("failed"), result.get("msg")
    assert h.split_calls(calls)["updates"] == []


def test_border_deleted_repeat_with_an_intent_without_ipv6_keys_is_stable():
    """An intent that lacks the IPv6 keys (not observed: the measured read carries them) reads as default."""
    _result, calls = run([{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}], "deleted", routed_have(), role="border")
    reset = []
    h._collect_policies([c["payload"] for c in h.split_calls(calls)["updates"]], reset)
    reset[0]["interfaces"][0].update({"interfaceType": "INTERFACE_ETHERNET", "fabricName": h.FABRIC})
    for k in ("IPv6", "IPv6_PREFIX"):
        reset[0]["interfaces"][0]["nvPairs"].pop(k)
    result, calls = run([{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}], "deleted", reset, role="border")
    assert not result.get("failed"), result.get("msg")
    assert h.split_calls(calls)["updates"] == []


# ------------------------------------------------------------------ query
def test_query_returns_the_stored_pair_without_writes():
    have = measured_have(V6, "127")
    result, calls = run([{"name": h.IF_A, "switch": [h.SWITCH_IP]}], "query", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []
    got = [i for p in result["response"] for i in p["interfaces"] if i["ifName"] == h.IF_A]
    assert len(got) == 1 and pair(got[0]["nvPairs"]) == (V6, "127")
    assert any("ifName=" + h.IF_A in c["path"] for c in calls if c["method"] == "GET")


# ------------------------------------------------------------------ validation
@pytest.mark.parametrize("profile", [
    dict(BASE, ipv6_addr="2001:db8::zz"),
    dict(BASE, ipv6_addr="192.0.2.9"),
    dict(BASE, ipv6_addr=V6, ipv6_mask_len=63),
    dict(BASE, ipv6_addr=V6, ipv6_mask_len=128),
])
def test_invalid_ipv6_input_is_refused_before_any_request(profile):
    result, calls = run([cfg(profile)], "merged")
    assert result.get("failed")
    assert h.writes(calls) == []


@pytest.mark.parametrize("mask", [64, 127])
def test_prefix_boundaries_are_accepted(mask):
    result, calls = run([cfg(dict(BASE, ipv6_addr=V6, ipv6_mask_len=mask))], "merged")
    assert not result.get("failed"), result.get("msg")
    assert pair(sent(calls)[h.IF_A][1]) == (V6, str(mask))


# ------------------------------------------------------------------ controls
def test_ipv4_only_routed_create_is_unchanged_apart_from_the_empty_pair():
    result, calls = run([cfg(BASE)], "merged")
    nv = sent(calls)[h.IF_A][1]
    assert not result.get("failed"), result.get("msg")
    assert (nv["IP"], nv["PREFIX"], nv["INTF_VRF"], nv["DESC"], nv["ADMIN_STATE"]) == (V4, "24", "default", "routed-v6", "false")
    assert pair(nv) == ("", "")


def test_epl_routed_still_sends_its_ipv6_pair():
    profile = {"mode": "epl_routed", "ipv4_addr": V4, "ipv4_mask_len": 24, "ipv6_addr": V6, "ipv6_mask_len": 127}
    result, calls = run([cfg(profile)], "merged")
    out = sent(calls)
    assert not result.get("failed"), result.get("msg")
    assert out[h.IF_A][0] == "epl_routed_intf"
    assert pair(out[h.IF_A][1]) == (V6, "127")
