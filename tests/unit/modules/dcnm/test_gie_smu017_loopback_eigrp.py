"""SMU 4.3.1.0175006017 loopback EIGRP fields (registry slice 0b_38).

    int_loopback  eigrpIpv6Routing                   enable_eigrp_ipv6_routing               reset "false"
    int_loopback  eigrpIpv4DistributeListPrefixList  eigrp_ipv4_distribute_list_prefix_list  reset ""
    int_loopback  eigrpIpv4DistributeListDirection   eigrp_ipv4_distribute_list_direction    reset "out"
    int_loopback  eigrpIpv6DistributeListPrefixList  eigrp_ipv6_distribute_list_prefix_list  reset ""
    int_loopback  eigrpIpv6DistributeListDirection   eigrp_ipv6_distribute_list_direction    reset "out"

The 4.3.1.0175006017 int_loopback body declares these five nvPairs with the declarations of the routed, subinterface
and SVI parents (same types, length, pattern, enum and defaults). Its add() deletes every child of the interface and
recreates only the selected ones, inside `if eigrpProcessTag != ""`, so a field set back to its default leaves no line.

Real main() through gie_withdrawal_harness: only inventory, transport and sleep are mocked, and every HAVE is the payload
the module itself emits for a public profile. Values are synthetic. Nothing here is live evidence.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding, resolve_by_nvpair
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import gie_withdrawal_harness as h

LO = h.LOOPBACK
IF_LO2 = "loopback932"
EIGRP_ON = {**h.BASE_LOOPBACK, "eigrp_process_tag": "PILOT-EIGRP", "enable_eigrp_routing": True}
EIGRP_SET = {**EIGRP_ON, "enable_eigrp_ipv6_routing": True,
             "eigrp_ipv4_distribute_list_prefix_list": "PILOT-PL4", "eigrp_ipv4_distribute_list_direction": "in",
             "eigrp_ipv6_distribute_list_prefix_list": "PILOT-PL6", "eigrp_ipv6_distribute_list_direction": "in"}

# (public key, nvPair, applied public value, applied wire value, template default = reset wire)
ROWS = [
    ("enable_eigrp_ipv6_routing", "eigrpIpv6Routing", True, "true", "false"),
    ("eigrp_ipv4_distribute_list_prefix_list", "eigrpIpv4DistributeListPrefixList", "PILOT-PL4", "PILOT-PL4", ""),
    ("eigrp_ipv4_distribute_list_direction", "eigrpIpv4DistributeListDirection", "in", "in", "out"),
    ("eigrp_ipv6_distribute_list_prefix_list", "eigrpIpv6DistributeListPrefixList", "PILOT-PL6", "PILOT-PL6", ""),
    ("eigrp_ipv6_distribute_list_direction", "eigrpIpv6DistributeListDirection", "in", "in", "out"),
]
IDS = [r[0] for r in ROWS]
NVPAIRS = [r[1] for r in ROWS]
SET_WIRE = {"eigrpIpv6Routing": "true", "eigrpIpv4DistributeListPrefixList": "PILOT-PL4",
            "eigrpIpv4DistributeListDirection": "in", "eigrpIpv6DistributeListPrefixList": "PILOT-PL6",
            "eigrpIpv6DistributeListDirection": "in"}
RESET_WIRE = {r[1]: r[4] for r in ROWS}


def _wire(value):
    return str(value).lower() if isinstance(value, bool) else str(value)


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


def _only(calls):
    emitted = _emitted(calls)
    assert len(emitted) == 1, emitted.keys()
    key, (policy, nv) = next(iter(emitted.items()))
    assert policy == LO and key[0] == h.SERIAL and key[1].lower() == h.IF_LO, (key, policy)
    return nv


def _paths(calls):
    return [c["method"] + " " + c["path"].split("/rest/")[-1].split("?")[0] for c in h.writes(calls)]


def _have(profile, ifname=h.IF_LO):
    """The payload the module emits for `profile` on `ifname`, as the controller would return it."""
    result, calls = h.run_configs([h.cfg(ifname, profile, iftype="lo")], "replaced", [])
    assert not result.get("failed"), result.get("msg")
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    assert len(found) == 1, found
    have = copy.deepcopy(found)
    have[0]["interfaces"][0]["interfaceType"] = "INTERFACE_LOOPBACK"
    have[0]["interfaces"][0]["fabricName"] = h.FABRIC
    return have


def _as_have(nv, ifname=h.IF_LO):
    return [{"policy": LO, "interfaces": [{"interfaceType": "INTERFACE_LOOPBACK", "serialNumber": h.SERIAL,
                                           "ifName": ifname, "fabricName": h.FABRIC, "nvPairs": copy.deepcopy(nv)}]}]


def _lo(profile, ifname=h.IF_LO, **kw):
    return h.cfg(ifname, profile, iftype="lo", **kw)


# ------------------------------------------------------------------ the rows are what the 017 body declares
@pytest.mark.parametrize("key,nvpair,applied,wire,reset", ROWS, ids=IDS)
def test_the_row_matches_the_017_loopback_contract(key, nvpair, applied, wire, reset):
    b = resolve_binding(LO, key)
    assert b is not None, "%s is not registered on int_loopback" % key
    assert b["parent_nvpair"] == nvpair and b["mechanism"] == "passthrough"
    assert b["reset_wire"] == reset, "the reset is the template default whose branch creates no child"
    assert resolve_by_nvpair(LO, nvpair) is b
    assert "inert_when" not in b, "the template gates these fields on the tag, which NDFC enforces"


def test_types_bounds_and_enums_follow_the_body():
    for key in ("eigrp_ipv4_distribute_list_prefix_list", "eigrp_ipv6_distribute_list_prefix_list"):
        assert resolve_binding(LO, key)["max_length"] == 63
    for key in ("eigrp_ipv4_distribute_list_direction", "eigrp_ipv6_distribute_list_direction"):
        assert list(resolve_binding(LO, key)["valid_values"]) == ["in", "out"]
    assert resolve_binding(LO, "enable_eigrp_ipv6_routing")["type"] == "boolean"


@pytest.mark.parametrize("key,nvpair,applied,wire,reset", ROWS, ids=IDS)
def test_the_public_key_and_nvpair_match_the_routed_parent(key, nvpair, applied, wire, reset):
    """Reuse, not a new name: the routed, subinterface and SVI parents serve the same key for the same nvPair."""
    for parent in (h.ROUTED, h.SUBIF, h.SVI):
        other = resolve_binding(parent, key)
        assert other is not None and other["parent_nvpair"] == nvpair and other["reset_wire"] == reset, parent


# ------------------------------------------------------------------ merged
def test_merged_create_sends_every_field_on_the_loopback_and_deploys_it():
    result, calls = h.run_configs([_lo(EIGRP_SET)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert {k: nv.get(k) for k in NVPAIRS} == SET_WIRE
    assert (nv["eigrpProcessTag"], nv["eigrpRouting"], nv["INTF_VRF"]) == ("PILOT-EIGRP", "true", "default")
    assert _paths(calls) == ["POST globalInterface", "POST globalInterface/deploy"]


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_explicit_update_sends_the_new_values_and_keeps_the_others(state):
    have = _have(EIGRP_SET)
    changes = {"eigrp_ipv4_distribute_list_direction": "out", "enable_eigrp_ipv6_routing": False,
               "eigrp_ipv6_distribute_list_prefix_list": "PILOT-PL6B"}
    result, calls = h.run_configs([_lo({**EIGRP_SET, **changes})], state, have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    expected = {**SET_WIRE, "eigrpIpv4DistributeListDirection": "out", "eigrpIpv6Routing": "false",
                "eigrpIpv6DistributeListPrefixList": "PILOT-PL6B"}
    assert {k: nv[k] for k in NVPAIRS} == expected
    assert (nv["eigrpProcessTag"], nv["DESC"], nv["IP"]) == ("PILOT-EIGRP", "pilot", "192.0.2.131")


def test_merged_omission_carries_the_stored_values_into_the_modify():
    have = _have(EIGRP_SET)
    result, calls = h.run_configs([_lo({**EIGRP_ON, "description": "changed"})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert {k: nv[k] for k in NVPAIRS} == SET_WIRE
    assert nv["DESC"] == "changed"


def test_explicit_false_and_default_values_differ_from_omission_under_merged():
    have = _have(EIGRP_SET)
    explicit = {**EIGRP_ON, "enable_eigrp_ipv6_routing": False, "eigrp_ipv4_distribute_list_prefix_list": "",
                "eigrp_ipv6_distribute_list_direction": "out"}
    result, calls = h.run_configs([_lo(explicit)], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert (nv["eigrpIpv6Routing"], nv["eigrpIpv4DistributeListPrefixList"], nv["eigrpIpv6DistributeListDirection"]) == (
        "false", "", "out")
    # the two omitted fields keep their stored values
    assert (nv["eigrpIpv4DistributeListDirection"], nv["eigrpIpv6DistributeListPrefixList"]) == ("in", "PILOT-PL6")


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_repeat_of_the_stored_values_writes_nothing(state):
    result, calls = h.run_configs([_lo(EIGRP_SET)], state, _have(EIGRP_SET))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and not result.get("changed")


# ------------------------------------------------------------------ replaced
def test_replaced_omission_withdraws_every_field_and_keeps_the_tag_and_routing():
    have = _have(EIGRP_SET)
    result, calls = h.run_configs([_lo(EIGRP_ON)], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert {k: nv[k] for k in NVPAIRS} == RESET_WIRE
    assert (nv["eigrpProcessTag"], nv["eigrpRouting"], nv["DESC"]) == ("PILOT-EIGRP", "true", "pilot")
    assert _paths(calls) == ["POST interface/modify", "POST globalInterface/deploy"], _paths(calls)


@pytest.mark.parametrize("key,nvpair,applied,wire,reset", ROWS, ids=IDS)
def test_replaced_withdraws_one_field_and_keeps_the_four_others(key, nvpair, applied, wire, reset):
    have = _have(EIGRP_SET)
    profile = {k: v for k, v in EIGRP_SET.items() if k != key}
    result, calls = h.run_configs([_lo(profile)], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert nv[nvpair] == reset
    assert {k: nv[k] for k in NVPAIRS if k != nvpair} == {k: v for k, v in SET_WIRE.items() if k != nvpair}


@pytest.mark.parametrize("state", ["replaced", "merged"])
def test_repeat_after_withdrawal_writes_nothing(state):
    result, calls = h.run_configs([_lo(EIGRP_ON)], "replaced", _have(EIGRP_SET))
    assert not result.get("failed"), result.get("msg")
    withdrawn = _as_have(_only(calls), _emitted(calls).popitem()[0][1])
    result, calls = h.run_configs([_lo(EIGRP_ON)], state, withdrawn)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_withdrawing_the_tag_with_routing_off_clears_the_five_fields_too():
    """The tag gate: replaced without any EIGRP key withdraws the tag, routing and the five fields together."""
    have = _have(EIGRP_SET)
    result, calls = h.run_configs([_lo(dict(h.BASE_LOOPBACK))], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert {k: nv[k] for k in NVPAIRS} == RESET_WIRE
    assert (nv["eigrpProcessTag"], nv["eigrpRouting"]) == ("", "false")


# ------------------------------------------------------------------ dependencies the template enforces, not the module
def test_a_field_without_the_tag_is_transported_and_left_to_the_template_refusal():
    """int_loopback 017 refuses an EIGRP option with an empty tag ("EIGRP process tag is required ..."). The module does
    not duplicate that rule on any parent (slice 0b_22): it transports the request and NDFC fails it. Live gap."""
    profile = {**h.BASE_LOOPBACK, "eigrp_ipv4_distribute_list_prefix_list": "PILOT-PL4"}
    result, calls = h.run_configs([_lo(profile)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert (nv.get("eigrpProcessTag", ""), nv["eigrpIpv4DistributeListPrefixList"]) == ("", "PILOT-PL4")


def test_a_direction_without_its_prefix_list_is_transported_and_renders_nothing():
    """The direction is IsShow-gated on its prefix list and only used inside the prefix-list branch of the body."""
    profile = {**EIGRP_ON, "eigrp_ipv6_distribute_list_direction": "in"}
    result, calls = h.run_configs([_lo(profile)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert (nv["eigrpIpv6DistributeListDirection"], nv.get("eigrpIpv6DistributeListPrefixList", "")) == ("in", "")


@pytest.mark.parametrize("vrf", ["default", "PILOT-VRF"])
def test_default_and_non_default_vrf_carry_the_fields_unchanged(vrf):
    """The body's EIGRP block is not VRF-gated. Whether NX-OS accepts it in a given VRF is a device question."""
    result, calls = h.run_configs([_lo({**EIGRP_SET, "int_vrf": vrf})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert nv["INTF_VRF"] == vrf and {k: nv[k] for k in NVPAIRS} == SET_WIRE


# ------------------------------------------------------------------ invalid input, boundaries, version gate, check mode
@pytest.mark.parametrize("change,needle", [
    ({"eigrp_ipv4_distribute_list_direction": "both"}, "eigrp_ipv4_distribute_list_direction"),
    ({"eigrp_ipv6_distribute_list_direction": "IN"}, "eigrp_ipv6_distribute_list_direction"),
    ({"eigrp_ipv4_distribute_list_prefix_list": "P" * 64}, "eigrp_ipv4_distribute_list_prefix_list"),
    ({"eigrp_ipv6_distribute_list_prefix_list": "P" * 64}, "eigrp_ipv6_distribute_list_prefix_list"),
    ({"enable_eigrp_ipv6_routing": "maybe"}, "enable_eigrp_ipv6_routing"),
], ids=["v4_direction_both", "v6_direction_upper", "v4_prefix_list_64", "v6_prefix_list_64", "ipv6_routing_not_bool"])
def test_invalid_values_are_refused_before_any_write(change, needle):
    result, calls = h.run_configs([_lo({**EIGRP_SET, **change})], "merged", [])
    assert result.get("failed") and needle in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


def test_a_63_character_prefix_list_is_accepted():
    name = "P" * 63
    result, calls = h.run_configs([_lo({**EIGRP_ON, "eigrp_ipv6_distribute_list_prefix_list": name})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)["eigrpIpv6DistributeListPrefixList"] == name


@pytest.mark.parametrize("patch_version", [None, "4.3.1.0175006011"], ids=["no_patch_version", "smu011"])
def test_the_fields_need_an_approved_patch_version(patch_version):
    result, calls = h.run_configs([_lo(EIGRP_SET)], "merged", [], patch_version=patch_version)
    assert result.get("failed"), "a registered field was accepted without SMU 017 or ND >= 4.4.1"
    assert h.writes(calls) == []


def test_numeric_441_is_admitted():
    result, calls = h.run_configs([_lo(EIGRP_SET)], "merged", [], patch_version="4.4.1")
    assert not result.get("failed"), result.get("msg")
    assert {k: _only(calls)[k] for k in NVPAIRS} == SET_WIRE


def test_check_mode_reports_the_change_and_writes_nothing():
    result, calls = h.run_configs([_lo(EIGRP_ON)], "replaced", _have(EIGRP_SET), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and result.get("changed") is True


# ------------------------------------------------------------------ overridden and deleted
# interface/detail in the measured aggregate shape (NDFC 12.6.0.267): a user loopback is deletable; a fabric loopback
# is not, with an int_fabric_loopback_11_1 underlay whose source is UNDERLAY. The harness double marks neither.
_ORIG = h._transport
FABRIC_LO, FABRIC_LO_POLICY = "loopback0", "int_fabric_loopback_11_1"
MARK, DEPLOY, MODIFY = "DELETE interface/markdelete", "POST globalInterface/deploy", "POST interface/modify"


def _measured_detail(calls, have):
    inner = _ORIG(calls, have)
    policy_of = dict((i["ifName"].lower(), p["policy"]) for p in have for i in p["interfaces"])

    def send(mod, method, path, payload=None):
        resp = inner(mod, method, path, payload)
        if method == "GET" and "/interface/detail" in path and isinstance(resp.get("DATA"), list):
            for e in resp["DATA"]:
                name = str(e.get("ifName", ""))
                if policy_of.get(name.lower()) == FABRIC_LO_POLICY:
                    e.update(ifType="INTERFACE_LOOPBACK", isPhysical="false", deletable=False, editAllowed=True,
                             underlayPolicies=[{"entityName": name, "source": "UNDERLAY",
                                                "templateName": FABRIC_LO_POLICY, "serialNumber": h.SERIAL}])
                elif name.lower().startswith("loopback"):
                    e.update(deletable=True, editAllowed=True)
        return resp
    return send


def _fabric_lo_have():
    return [{"policy": FABRIC_LO_POLICY, "interfaces": [{
        "interfaceType": "INTERFACE_LOOPBACK", "serialNumber": h.SERIAL, "ifName": FABRIC_LO, "fabricName": h.FABRIC,
        "nvPairs": {"INTF_NAME": FABRIC_LO, "IP": "10.2.0.1", "ADMIN_STATE": "true"}}]}]


def _identities(calls):
    """Every write in order, as (request, sorted [serial, ifName(, policy)])."""
    out = []
    for c in h.writes(calls):
        kind = c["method"] + " " + c["path"].split("/rest/")[-1].split("?")[0]
        found = []
        h._collect_policies([c["payload"]], found)
        if found:
            ids = sorted([i["serialNumber"], i["ifName"], p["policy"]] for p in found for i in p["interfaces"])
        else:
            ids = sorted([e.get("serialNumber"), e.get("ifName")] for e in (c["payload"] or []) if isinstance(e, dict))
        out.append((kind, ids))
    return out


def _overridden(configs, have):
    with patch.object(h, "_transport", _measured_detail):
        return h.run_configs(configs, "overridden", have)


def _aggregate():
    """The omitted or withdrawn user loopback, the retained one and the fabric loopback."""
    return _have(EIGRP_SET) + _have(EIGRP_SET, IF_LO2) + _fabric_lo_have()


def test_overridden_retained_loopback_withdraws_its_omitted_fields_and_keeps_the_control():
    result, calls = _overridden([_lo(EIGRP_ON), _lo(EIGRP_SET, IF_LO2)], _aggregate())
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [(MODIFY, [[h.SERIAL, "Loopback931", LO]]), (DEPLOY, [[h.SERIAL, "Loopback931"]])]
    nv = _only(calls)
    assert {k: nv[k] for k in NVPAIRS} == RESET_WIRE
    assert (nv["eigrpProcessTag"], nv["eigrpRouting"]) == ("PILOT-EIGRP", "true")


def test_overridden_loopback_left_out_is_deleted_and_the_retained_and_fabric_ones_kept():
    result, calls = _overridden([_lo(EIGRP_SET, IF_LO2)], _aggregate())
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [(MARK, [[h.SERIAL, "Loopback931"]]), (DEPLOY, [[h.SERIAL, "Loopback931"]])]
    result, calls = _overridden([_lo(EIGRP_SET, IF_LO2)], _have(EIGRP_SET, IF_LO2) + _fabric_lo_have())
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == []


def test_deleted_retires_the_loopback_and_a_repeat_writes_nothing():
    target = [{"name": h.IF_LO, "type": "lo", "switch": [h.SWITCH_IP]}]
    with patch.object(h, "_transport", _measured_detail):
        result, calls = h.run_configs(target, "deleted", _have(EIGRP_SET) + _fabric_lo_have())
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [(MARK, [[h.SERIAL, "Loopback931"]]), (DEPLOY, [[h.SERIAL, "Loopback931"]])]
    with patch.object(h, "_transport", _measured_detail):
        result, calls = h.run_configs(target, "deleted", _fabric_lo_have())
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == []


# ------------------------------------------------------------------ query
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
                    if i["ifName"].lower() == q["ifName"].lower() and i["serialNumber"] == q.get("serialNumber")]}
            writes.append((method, path))
            return {"RETURN_CODE": 500, "MESSAGE": "unexpected read", "DATA": {}}
        return send
    return factory


def test_query_returns_the_controller_nvpairs_unchanged():
    target = _have(EIGRP_SET)
    other = _have(EIGRP_ON, IF_LO2)
    writes = []
    with patch.object(h, "_transport", _query_transport(target + other, writes)):
        result, calls = h.run_configs([{"name": h.IF_LO, "switch": [h.SWITCH_IP]}], "query", [])
    assert not result.get("failed"), result.get("msg")
    assert writes == [] and h.writes(calls) == []
    assert result["response"] == target, "query must return the controller entry unchanged"
    nv = result["response"][0]["interfaces"][0]["nvPairs"]
    assert {k: nv[k] for k in NVPAIRS} == SET_WIRE
    assert not result.get("changed")


# ------------------------------------------------------------------ unaffected controls
def test_loopback_ospf_payload_is_unchanged_by_the_new_rows():
    """Positive control: an OSPF-only loopback carries none of the five nvPairs."""
    result, calls = h.run_configs([_lo({**h.BASE_LOOPBACK, **h.OSPF_CTX})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert nv["ospf"] == "true" and not set(NVPAIRS) & set(nv)
