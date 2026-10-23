"""SMU 017 batch-1 fields (registry slice 0b_37): the five-state contract that test_gie_smu017_batch1.py does not cover.

    merged      explicit update of an existing value
    replaced    explicit update with the other fields retained; repeat after withdrawal; OSPF gate on and off
    overridden  a retained interface beside a control, an interface left out of the desired set (role-default reset and
                subinterface deletion), the scope of the emitted identities, repeat over the resulting state
    deleted     repeat over a port already at its role default and over a removed subinterface; an unrelated interface
                left untouched
    query       real main() with controller-shaped responses carrying the five nvPairs: raw response, identity, values,
                no write and no deploy

Real main() through gie_withdrawal_harness; only inventory, transport and sleep are mocked. Every HAVE is the payload the
module itself emits for a public profile on the named interface. Values are synthetic. Nothing here is live evidence.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import pytest

from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import gie_withdrawal_harness as h
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.test_dcnm_intf_default_reset_registered_f2 import (
    _inventory, _physical_transport, PHYSICAL,
)
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

OSPF_ON = {**h.BASE_ROUTED, **h.OSPF_CTX}
ROUTED_OFF = {**h.BASE_ROUTED, "enable_ospf": False}
ROUTED_SET = {**OSPF_ON, "enable_cdp": False, "enable_evpn_multisite_dci_tracking": True, "ospf_retransmit_interval": 10}
ACCESS_SET = {**h.BASE_ACCESS, "logging_event_port_link_status": True}
SUB_SET = {**h.BASE_SUBIF, "enable_pim_bfd_instance": True}
FIELDS = ("CDP_ENABLE", "evpnMultisiteDciTracking", "ospfRetransmitInterval", "loggingEventPortLinkStatus",
          "pimBfdInstance")
IF_CTL = "Ethernet1/40"
IF_SUB2 = "Ethernet1/31.3002"


def _emitted(calls):
    """Every interface of every write, as {(serial, ifName): (policy, nvPairs)}."""
    out = {}
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    for pol in found:
        for intf in pol["interfaces"]:
            key = (intf["serialNumber"], intf["ifName"])
            assert key not in out, ("identity written twice", key)
            out[key] = (pol["policy"], intf.get("nvPairs") or {})
    return out


def _deploys(calls):
    return sorted((e.get("serialNumber"), e.get("ifName")) for c in h.writes(calls) if "deploy" in c["path"]
                  for e in (c["payload"] or []))


def _have_for(ifname, profile, iftype="eth"):
    """The payload the module emits for `profile` on `ifname`, as the controller would return it."""
    result, calls = h.run_configs([h.cfg(ifname, profile, iftype=iftype)], "replaced", [])
    assert not result.get("failed"), result.get("msg")
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    assert len(found) == 1 and found[0]["interfaces"][0]["ifName"] == ifname, found
    have = copy.deepcopy(found)
    have[0]["interfaces"][0]["interfaceType"] = "INTERFACE_ETHERNET"
    have[0]["interfaces"][0]["fabricName"] = h.FABRIC
    return have


def _as_have(policy, ifname, nv):
    return [{"policy": policy, "interfaces": [{"interfaceType": "INTERFACE_ETHERNET", "serialNumber": h.SERIAL,
                                               "ifName": ifname, "fabricName": h.FABRIC, "nvPairs": copy.deepcopy(nv)}]}]


_ORIG_PHYSICAL = _physical_transport(PHYSICAL)


def _detail_transport(calls, have):
    """The F2 physical-port flags plus the subinterface flag the harness does not model: a live 12.6.0.267
    interface/detail read returned a user subinterface with `isPhysical: "false"` and `deletable: true`.
    `overridden` deletes a non-physical interface only when `deletable` is true."""
    inner = _ORIG_PHYSICAL(calls, have)

    def send(mod, method, path, payload=None):
        resp = inner(mod, method, path, payload)
        if method == "GET" and "/interface/detail" in path and isinstance(resp.get("DATA"), list):
            for e in resp["DATA"]:
                if str(e.get("isPhysical")).lower() == "false" and "." in str(e.get("ifName")):
                    e["deletable"] = True
        return resp
    return send


def _run(configs, state, have, role="leaf"):
    with patch.object(h, "_transport", _detail_transport):
        return h.run_configs(configs, state, have=have,
                             extra_patch=patch.object(module, "get_fabric_inventory_details",
                                                      return_value=_inventory(role)))


def _nv(have):
    return have[0]["interfaces"][0]["nvPairs"]


# ====================================================================================================== merged
@pytest.mark.parametrize("profile,changes,expected", [
    (ROUTED_SET, {"enable_cdp": True, "ospf_retransmit_interval": 20},
     {"CDP_ENABLE": "true", "evpnMultisiteDciTracking": "true", "ospfRetransmitInterval": "20"}),
    (ROUTED_SET, {"enable_evpn_multisite_dci_tracking": False},
     {"CDP_ENABLE": "false", "evpnMultisiteDciTracking": "false", "ospfRetransmitInterval": "10"}),
    (ACCESS_SET, {"logging_event_port_link_status": False}, {"loggingEventPortLinkStatus": "false"}),
    (SUB_SET, {"enable_pim_bfd_instance": False}, {"pimBfdInstance": "false"}),
], ids=["routed_cdp_true_and_interval", "routed_dci_false", "access_logging_false", "subif_pim_bfd_false"])
@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_explicit_update_sends_the_new_value_and_keeps_the_other_fields(state, profile, changes, expected):
    """An explicit change is sent; the other new fields keep their values in the same request."""
    iftype = "sub_int" if profile is SUB_SET else "eth"
    name = h.IF_SUB if profile is SUB_SET else h.IF_A
    have = _have_for(name, profile, iftype)
    result, calls = h.run_configs([h.cfg(name, {**profile, **changes}, iftype=iftype)], state, have)
    assert not result.get("failed"), result.get("msg")
    emitted = _emitted(calls)
    assert list(emitted) == [(h.SERIAL, name)]
    nv = emitted[(h.SERIAL, name)][1]
    assert {k: nv.get(k) for k in expected} == expected
    assert nv.get("DESC") == profile["description"], "an unrelated retained setting changed"


def test_merged_omission_carries_the_stored_values_into_the_modify():
    """The request is a full replacement of the interface: the omitted fields must travel with their stored values."""
    have = _have_for(h.IF_A, ROUTED_SET)
    result, calls = h.run_configs([h.cfg(h.IF_A, {**OSPF_ON, "description": "changed"})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _emitted(calls)[(h.SERIAL, h.IF_A)][1]
    assert (nv["CDP_ENABLE"], nv["evpnMultisiteDciTracking"], nv["ospfRetransmitInterval"]) == ("false", "true", "10")
    assert nv["DESC"] == "changed"


# ====================================================================================================== replaced
def test_replaced_with_ospf_disabled_clears_the_interval_and_keeps_the_others():
    have = _have_for(h.IF_A, ROUTED_SET)
    profile = {**ROUTED_OFF, "enable_cdp": False, "enable_evpn_multisite_dci_tracking": True}
    result, calls = h.run_configs([h.cfg(h.IF_A, profile)], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = _emitted(calls)[(h.SERIAL, h.IF_A)][1]
    assert (nv["ospf"], nv["ospfRetransmitInterval"]) == ("false", "")
    assert (nv["CDP_ENABLE"], nv["evpnMultisiteDciTracking"]) == ("false", "true")


def test_replaced_setting_the_interval_with_ospf_disabled_is_refused_before_any_write():
    have = _have_for(h.IF_A, ROUTED_SET)
    result, calls = h.run_configs([h.cfg(h.IF_A, {**ROUTED_OFF, "ospf_retransmit_interval": 10})], "replaced", have)
    assert result.get("failed") and "ospf_retransmit_interval (needs enable_ospf)" in result["msg"], result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("name,profile,base,iftype", [
    (h.IF_A, ROUTED_SET, OSPF_ON, "eth"), (h.IF_A, ACCESS_SET, h.BASE_ACCESS, "eth"),
    (h.IF_SUB, SUB_SET, h.BASE_SUBIF, "sub_int"),
], ids=["routed", "access", "subif"])
@pytest.mark.parametrize("state", ["replaced", "merged"])
def test_repeat_after_withdrawal_writes_nothing(state, name, profile, base, iftype):
    have = _have_for(name, profile, iftype)
    result, calls = h.run_configs([h.cfg(name, dict(base), iftype=iftype)], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    policy, nv = _emitted(calls)[(h.SERIAL, name)]
    withdrawn = _as_have(policy, name, nv)
    result, calls = h.run_configs([h.cfg(name, dict(base), iftype=iftype)], state, withdrawn)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


# ====================================================================================================== overridden
def test_overridden_retained_interface_withdraws_only_its_own_omitted_fields():
    """(a) Retained: the interface stays in the desired set without the fields. The control is retained unchanged."""
    have = _have_for(h.IF_A, ROUTED_SET) + _have_for(IF_CTL, ACCESS_SET)
    configs = [h.cfg(h.IF_A, dict(OSPF_ON)), h.cfg(IF_CTL, dict(ACCESS_SET))]
    result, calls = _run(configs, "overridden", have)
    assert not result.get("failed"), result.get("msg")
    emitted = _emitted(calls)
    assert list(emitted) == [(h.SERIAL, h.IF_A)], "the retained control must not be written"
    policy, nv = emitted[(h.SERIAL, h.IF_A)]
    assert policy == h.ROUTED
    assert (nv["CDP_ENABLE"], nv["evpnMultisiteDciTracking"], nv["ospfRetransmitInterval"]) == ("true", "false", "")


@pytest.mark.parametrize("role,expected_policy", [("leaf", h.TRUNK), ("border", h.ROUTED)])
def test_overridden_interface_left_out_is_retired_to_the_role_default(role, expected_policy):
    """(b) Retirement: the routed port is absent from the desired set; only the control is listed and kept."""
    have = _have_for(h.IF_A, ROUTED_SET) + _have_for(IF_CTL, ACCESS_SET)
    result, calls = _run([h.cfg(IF_CTL, dict(ACCESS_SET))], "overridden", have, role=role)
    assert not result.get("failed"), result.get("msg")
    emitted = _emitted(calls)
    assert list(emitted) == [(h.SERIAL, h.IF_A)], emitted.keys()
    policy, nv = emitted[(h.SERIAL, h.IF_A)]
    assert policy == expected_policy
    if role == "leaf":
        assert not {"evpnMultisiteDciTracking", "ospfRetransmitInterval"} & set(nv)
    else:
        assert (nv["CDP_ENABLE"], nv["evpnMultisiteDciTracking"], nv["ospfRetransmitInterval"], nv["ospf"]) == (
            "true", "false", "", "false")
    assert _deploys(calls) == [(h.SERIAL, h.IF_A)]
    # repeat over the resulting state: the retired port now holds its reset payload
    after = _as_have(policy, h.IF_A, nv) + _have_for(IF_CTL, ACCESS_SET)
    result, calls = _run([h.cfg(IF_CTL, dict(ACCESS_SET))], "overridden", after, role=role)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_overridden_subinterface_left_out_is_deleted_and_the_retained_one_kept():
    have = _have_for(h.IF_SUB, SUB_SET, "sub_int") + _have_for(IF_SUB2, {**SUB_SET, "vlan": 3002}, "sub_int")
    result, calls = _run([h.cfg(IF_SUB2, {**SUB_SET, "vlan": 3002}, iftype="sub_int")], "overridden", have)
    assert not result.get("failed"), result.get("msg")
    writes = h.writes(calls)
    deleted = [e.get("ifName") for c in writes if "delete" in c["path"].lower() for e in (c["payload"] or [])]
    assert deleted == [h.IF_SUB], [(c["path"], c["payload"]) for c in writes]
    assert not any("modify" in c["path"] for c in writes)
    # repeat: the deleted subinterface is gone
    result, calls = _run([h.cfg(IF_SUB2, {**SUB_SET, "vlan": 3002}, iftype="sub_int")], "overridden",
                         _have_for(IF_SUB2, {**SUB_SET, "vlan": 3002}, "sub_int"))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


# ====================================================================================================== deleted
def test_deleted_resets_only_the_named_port():
    have = _have_for(h.IF_A, ROUTED_SET) + _have_for(IF_CTL, ACCESS_SET)
    result, calls = _run([{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}], "deleted", have, role="border")
    assert not result.get("failed"), result.get("msg")
    emitted = _emitted(calls)
    assert list(emitted) == [(h.SERIAL, h.IF_A)]
    assert _deploys(calls) == [(h.SERIAL, h.IF_A)]


@pytest.mark.parametrize("role", ["leaf", "border"])
def test_deleted_repeat_over_a_port_already_at_its_default_writes_nothing(role):
    have = _have_for(h.IF_A, ROUTED_SET)
    cfg = [{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}]
    result, calls = _run(cfg, "deleted", have, role=role)
    assert not result.get("failed"), result.get("msg")
    policy, nv = _emitted(calls)[(h.SERIAL, h.IF_A)]
    result, calls = _run(cfg, "deleted", _as_have(policy, h.IF_A, nv), role=role)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_deleted_repeat_over_a_removed_subinterface_writes_nothing():
    result, calls = _run([{"name": h.IF_SUB, "type": "sub_int", "switch": [h.SWITCH_IP]}], "deleted", [])
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


# ====================================================================================================== query
def _controller_shaped(have, defaults):
    """The controller returns every nvPair its template declares; fill the template defaults the module omitted."""
    have = copy.deepcopy(have)
    nv = _nv(have)
    for key, value in defaults.items():
        nv.setdefault(key, value)
    return have


def _query_transport(store, writes):
    def factory(calls, _have):
        def send(mod, method, path, payload=None):
            calls.append({"method": method, "path": path, "payload": payload})
            if method != "GET":
                writes.append((method, path))
                return {"RETURN_CODE": 500, "MESSAGE": "query must not write", "DATA": {}}
            q = {k: v[0] for k, v in parse_qs(urlsplit(path).query).items()}
            if "accessmode" in path.lower():
                return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {"readonly": False}}
            if urlsplit(path).path.endswith("/rest/interface") and "ifName" in q:
                return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [
                    copy.deepcopy(p) for p in store for i in p["interfaces"]
                    if i["ifName"] == q["ifName"] and i["serialNumber"] == q.get("serialNumber")]}
            writes.append((method, path))
            return {"RETURN_CODE": 500, "MESSAGE": "unexpected read", "DATA": {}}
        return send
    return factory


ROUTED_DEFAULTS = {"CDP_ENABLE": "true", "evpnMultisiteDciTracking": "false", "ospfRetransmitInterval": ""}


@pytest.mark.parametrize("profile,name,iftype,defaults,expected", [
    (ROUTED_SET, h.IF_A, "eth", ROUTED_DEFAULTS,
     {"CDP_ENABLE": "false", "evpnMultisiteDciTracking": "true", "ospfRetransmitInterval": "10", "ospfCost": None}),
    ({**OSPF_ON, "ospf_cost": 40}, h.IF_A, "eth", ROUTED_DEFAULTS,
     {"CDP_ENABLE": "true", "evpnMultisiteDciTracking": "false", "ospfRetransmitInterval": "", "ospfCost": "40"}),
    (ACCESS_SET, h.IF_A, "eth", {"loggingEventPortLinkStatus": "false"}, {"loggingEventPortLinkStatus": "true"}),
    (h.BASE_ACCESS, h.IF_A, "eth", {"loggingEventPortLinkStatus": "false"}, {"loggingEventPortLinkStatus": "false"}),
    (SUB_SET, h.IF_SUB, "sub_int", {"pimBfdInstance": "false"}, {"pimBfdInstance": "true"}),
    (h.BASE_SUBIF, h.IF_SUB, "sub_int", {"pimBfdInstance": "false"}, {"pimBfdInstance": "false"}),
], ids=["routed_non_default", "routed_defaults_with_ospf_cost_control", "access_true", "access_default_false",
        "subif_true", "subif_default_false"])
def test_query_returns_the_controller_nvpairs_unchanged(profile, name, iftype, defaults, expected):
    """state: query hands back the controller's DATA as-is (raw nvPairs, not profile keys), for the named interface only."""
    target = _controller_shaped(_have_for(name, profile, iftype), defaults)
    other = _controller_shaped(_have_for(IF_CTL, ROUTED_SET), ROUTED_DEFAULTS)
    writes = []
    with patch.object(h, "_transport", _query_transport(target + other, writes)):
        result, calls = h.run_configs([{"name": name, "switch": [h.SWITCH_IP]}], "query", [])
    assert not result.get("failed"), result.get("msg")
    assert writes == [] and h.writes(calls) == []
    response = result["response"]
    assert response == target, "query must return the controller entry unchanged"
    assert result["diff"][0]["query"] == target
    intf = response[0]["interfaces"][0]
    assert (intf["serialNumber"], intf["ifName"]) == (h.SERIAL, name)
    assert {k: intf["nvPairs"].get(k) for k in expected} == expected
    assert not result.get("changed")


# ====================================================================================================== native CDP
@pytest.mark.parametrize("patch_version", [None, "4.3.1.0175006011"])
@pytest.mark.parametrize("profile", [{**h.BASE_TRUNK, "enable_cdp": False},
                                     {**{k: v for k, v in h.BASE_ACCESS.items() if k not in ("enable_qos", "qos_policy")},
                                      "enable_cdp": False}], ids=["trunk", "access"])
def test_native_cdp_keeps_its_version_behaviour(profile, patch_version):
    """Native enable_cdp needs no patch_version on the profiles that already served it, exactly as on 68a30199."""
    result, calls = h.run(profile, "merged", patch_version=patch_version)
    assert not result.get("failed"), result.get("msg")
    assert [nv["CDP_ENABLE"] for nv in h.request_nvpairs(calls) if "CDP_ENABLE" in nv] == [False]
