"""SMU 4.3.1.0175006017 PIM BFD instance on the routed port-channel (registry slice 0b_39).

    int_l3_port_channel  pimBfdInstance  enable_pim_bfd_instance  reset "false"

`type: pc`, `mode: l3` selects int_l3_port_channel (pol_types "pc_l3"). The 017 body declares pimBfdInstance
(L156), creates pim_bfd_instance_interface when it is "true" (L1215) and has no else branch: every add() first deletes
all PTIs of the port-channel (L1015), so "false" leaves no line. The body does not gate the field on PIM sparse mode.

ospfRetransmitInterval is not registered on this parent. The body refuses it unless `ospf` is true with a tag and an
area, and no public key reaches those nvPairs on a routed port-channel; the last tests pin that refusal.

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

L3PO = h.PC_L3
KEY, NVPAIR = "enable_pim_bfd_instance", "pimBfdInstance"
PO_A, PO_B = h.PC_A, "Port-channel302"
BASE = dict(h.BASE_PC_L3)
BFD_ON = {**BASE, KEY: True}
# Native nvPairs a field change must not disturb: membership, admin state, address, VRF, routing tag, MTU.
NATIVE = ("MEMBER_INTERFACES", "PC_MODE", "ADMIN_STATE", "IP", "PREFIX", "INTF_VRF", "ROUTING_TAG", "MTU", "DESC")


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


def _only(calls, ifname=PO_A):
    emitted = _emitted(calls)
    assert len(emitted) == 1, emitted.keys()
    key, (policy, nv) = next(iter(emitted.items()))
    assert policy == L3PO and key[0] == h.SERIAL and key[1].lower() == ifname.lower(), (key, policy)
    return nv


def _paths(calls):
    return [c["method"] + " " + c["path"].split("/rest/")[-1].split("?")[0] for c in h.writes(calls)]


def _po(profile, ifname=PO_A, **kw):
    return h.cfg(ifname, profile, iftype="pc", **kw)


def _have(profile, ifname=PO_A):
    """The payload the module emits for `profile` on `ifname`, as the controller would return it."""
    result, calls = h.run_configs([_po(profile, ifname)], "replaced", [])
    assert not result.get("failed"), result.get("msg")
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    assert len(found) == 1 and found[0]["policy"] == L3PO, found
    have = copy.deepcopy(found)
    have[0]["interfaces"][0]["interfaceType"] = "INTERFACE_PORT_CHANNEL"
    have[0]["interfaces"][0]["fabricName"] = h.FABRIC
    return have


def _as_have(nv, ifname=PO_A):
    return [{"policy": L3PO, "interfaces": [{"interfaceType": "INTERFACE_PORT_CHANNEL", "serialNumber": h.SERIAL,
                                             "ifName": ifname, "fabricName": h.FABRIC, "nvPairs": copy.deepcopy(nv)}]}]


def _native(nv):
    return {k: nv.get(k) for k in NATIVE}


# ------------------------------------------------------------------ the row is what the 017 body declares
def test_the_row_matches_the_017_l3_port_channel_contract():
    b = resolve_binding(L3PO, KEY)
    assert b is not None, "enable_pim_bfd_instance is not registered on int_l3_port_channel"
    assert (b["parent_nvpair"], b["type"], b["reset_wire"], b["mechanism"]) == (NVPAIR, "boolean", "false", "passthrough")
    assert (b["applicable_interface_type"], b["applicable_mode"]) == ("pc", "l3")
    assert resolve_by_nvpair(L3PO, NVPAIR) is b
    assert "inert_when" not in b, "the body does not gate pimBfdInstance on PIM sparse mode"


def test_the_public_key_and_reset_match_the_routed_and_subinterface_rows():
    for parent in (h.ROUTED, h.SUBIF):
        other = resolve_binding(parent, KEY)
        assert other["parent_nvpair"] == NVPAIR and other["reset_wire"] == "false", parent


def test_pim_bfd_is_the_only_pim_row_on_the_parent():
    """pimBfdInstance is the only PIM row; sparse mode stays unregistered. The OSPF family on this parent is slice
    0b_40 (test_gie_smu017_l3po_ospf.py)."""
    assert resolve_binding(L3PO, "enable_pim_sparse") is None
    assert resolve_binding(L3PO, "pim_dr_priority") is None


# ------------------------------------------------------------------ merged
def test_merged_create_sends_the_field_with_the_native_profile_and_deploys_it():
    result, calls = h.run_configs([_po(BFD_ON)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert nv[NVPAIR] == "true"
    assert (nv["MEMBER_INTERFACES"], nv["IP"], nv["PREFIX"], nv["PC_MODE"]) == (h.PC_MEMBER, "192.0.2.33", "30", "active")
    assert _paths(calls) == ["POST globalInterface", "POST globalInterface/deploy"], _paths(calls)


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_explicit_update_sends_false_and_keeps_the_native_values(state):
    have = _have(BFD_ON)
    result, calls = h.run_configs([_po({**BFD_ON, KEY: False})], state, have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert nv[NVPAIR] == "false"
    assert _native(nv) == _native(have[0]["interfaces"][0]["nvPairs"])
    assert _paths(calls) == ["POST interface/modify", "POST globalInterface/deploy"], _paths(calls)


def test_merged_omission_carries_the_stored_value_into_another_change():
    have = _have(BFD_ON)
    result, calls = h.run_configs([_po({**BASE, "description": "changed"})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert (nv[NVPAIR], nv["DESC"]) == ("true", "changed")
    assert nv["MEMBER_INTERFACES"] == h.PC_MEMBER


def test_explicit_false_differs_from_omission_under_merged():
    have = _have(BFD_ON)
    result, calls = h.run_configs([_po({**BASE, KEY: False})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)[NVPAIR] == "false"
    result, calls = h.run_configs([_po(BASE)], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [], "omission under merged keeps the stored true and changes nothing"


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_repeat_of_the_stored_value_writes_nothing(state):
    result, calls = h.run_configs([_po(BFD_ON)], state, _have(BFD_ON))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and not result.get("changed")


# ------------------------------------------------------------------ replaced
def test_replaced_omission_withdraws_the_field_and_keeps_the_native_values():
    have = _have(BFD_ON)
    result, calls = h.run_configs([_po(BASE)], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert nv[NVPAIR] == "false"
    assert _native(nv) == _native(have[0]["interfaces"][0]["nvPairs"])
    assert _paths(calls) == ["POST interface/modify", "POST globalInterface/deploy"], _paths(calls)


@pytest.mark.parametrize("state", ["replaced", "merged"])
def test_repeat_after_withdrawal_writes_nothing(state):
    result, calls = h.run_configs([_po(BASE)], "replaced", _have(BFD_ON))
    assert not result.get("failed"), result.get("msg")
    withdrawn = _as_have(_only(calls))
    result, calls = h.run_configs([_po(BASE)], state, withdrawn)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_replaced_without_the_field_on_a_port_channel_that_never_had_it_writes_nothing():
    result, calls = h.run_configs([_po(BASE)], "replaced", _have(BASE))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_a_member_change_keeps_the_stored_field_under_merged_and_withdraws_it_under_replaced():
    """merged adds the new member to the stored ones (native port-channel behaviour); replaced sets the list."""
    have = _have(BFD_ON)
    moved = {**BASE, "members": ["Ethernet1/49"]}
    result, calls = h.run_configs([_po(moved)], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert (sorted(nv["MEMBER_INTERFACES"].split(",")), nv[NVPAIR]) == (["Ethernet1/49", h.PC_MEMBER], "true")
    result, calls = h.run_configs([_po(moved)], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert (nv["MEMBER_INTERFACES"], nv[NVPAIR]) == ("Ethernet1/49", "false")


def test_admin_state_down_is_sent_with_the_field():
    result, calls = h.run_configs([_po({**BFD_ON, "admin_state": False})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert (nv["ADMIN_STATE"], nv[NVPAIR]) == ("false", "true")


@pytest.mark.parametrize("vrf", ["default", "PILOT-VRF"])
def test_default_and_non_default_vrf_carry_the_field_unchanged(vrf):
    result, calls = h.run_configs([_po({**BFD_ON, "int_vrf": vrf})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert (nv["INTF_VRF"], nv[NVPAIR]) == (vrf, "true")


# ------------------------------------------------------------------ invalid input, version gate, check mode
def test_a_non_boolean_value_is_refused_before_any_write():
    result, calls = h.run_configs([_po({**BASE, KEY: "maybe"})], "merged", [])
    assert result.get("failed") and KEY in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("patch_version", [None, "4.3.1.0175006011"], ids=["no_patch_version", "smu011"])
def test_the_field_needs_an_approved_patch_version(patch_version):
    result, calls = h.run_configs([_po(BFD_ON)], "merged", [], patch_version=patch_version)
    assert result.get("failed"), "a registered field was accepted without SMU 017 or ND >= 4.4.1"
    assert h.writes(calls) == []


@pytest.mark.parametrize("patch_version", [None, "4.3.1.0175006011"], ids=["no_patch_version", "smu011"])
def test_omission_under_a_closed_gate_resets_nothing(patch_version):
    """A disabled gate never invents a reset: replaced without the key leaves the stored value alone."""
    result, calls = h.run_configs([_po(BASE)], "replaced", _have(BFD_ON), patch_version=patch_version)
    assert not result.get("failed"), result.get("msg")
    assert all(nv.get(NVPAIR) != "false" for _p, nv in _emitted(calls).values())


def test_numeric_441_is_admitted():
    result, calls = h.run_configs([_po(BFD_ON)], "merged", [], patch_version="4.4.1")
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)[NVPAIR] == "true"


def test_check_mode_reports_the_change_and_writes_nothing():
    result, calls = h.run_configs([_po(BASE)], "replaced", _have(BFD_ON), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and result.get("changed") is True


# ------------------------------------------------------------------ overridden and deleted
# interface/detail in the measured aggregate shape (NDFC 12.6.0.267): a user port-channel is INTERFACE_PORT_CHANNEL,
# not physical and deletable; each member is a physical INTERFACE_ETHERNET, not deletable, with an underlay policy whose
# source is its port-channel. The harness double answers every port-channel as a physical Ethernet port.
_ORIG = h._transport
MEM_A, MEM_B = h.PC_MEMBER, "Ethernet1/52"
MEMBER_POLICY = "int_l3_port_channel_member"
MARK, DEPLOY, MODIFY = "DELETE interface/markdelete", "POST globalInterface/deploy", "POST interface/modify"


def _measured_detail(calls, have):
    inner = _ORIG(calls, have)
    member_of = dict((i["ifName"].lower(), i["nvPairs"]["PRIMARY_INTF"])
                     for p in have if p["policy"] == MEMBER_POLICY for i in p["interfaces"])

    def send(mod, method, path, payload=None):
        resp = inner(mod, method, path, payload)
        if method == "GET" and "/interface/detail" in path and isinstance(resp.get("DATA"), list):
            for e in resp["DATA"]:
                name = str(e.get("ifName", ""))
                if name.lower() in member_of:
                    e.update(ifType="INTERFACE_ETHERNET", isPhysical="true", deletable=False, editAllowed=True,
                             underlayPolicies=[{"entityName": name, "source": member_of[name.lower()],
                                                "templateName": MEMBER_POLICY, "serialNumber": h.SERIAL}])
                elif name.lower().startswith("port-channel"):
                    e.update(ifType="INTERFACE_PORT_CHANNEL", isPhysical="false", deletable=True, editAllowed=True)
        return resp
    return send


def _member_have(member, po):
    return [{"policy": MEMBER_POLICY, "interfaces": [{
        "interfaceType": "INTERFACE_ETHERNET", "serialNumber": h.SERIAL, "ifName": member, "fabricName": h.FABRIC,
        "nvPairs": {"INTF_NAME": member, "PRIMARY_INTF": po.lower(), "ADMIN_STATE": "true", "DESC": "", "CONF": ""}}]}]


def _aggregate():
    """Po A and Po B with the field set, each with its own member."""
    return (_have({**BFD_ON, "members": [MEM_A]}) + _have({**BFD_ON, "members": [MEM_B]}, PO_B)
            + _member_have(MEM_A, PO_A) + _member_have(MEM_B, PO_B))


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


def _run(configs, state, have):
    with patch.object(h, "_transport", _measured_detail):
        return h.run_configs(configs, state, have)


def test_overridden_retained_port_channel_withdraws_the_field_and_keeps_the_control():
    configs = [_po({**BASE, "members": [MEM_A]}), _po({**BFD_ON, "members": [MEM_B]}, PO_B)]
    result, calls = _run(configs, "overridden", _aggregate())
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [(MODIFY, [[h.SERIAL, PO_A, L3PO]]), (DEPLOY, [[h.SERIAL, PO_A]])]
    nv = _only(calls)
    assert nv[NVPAIR] == "false" and nv["MEMBER_INTERFACES"] == MEM_A


def test_overridden_port_channel_left_out_is_deleted_and_the_retained_one_kept():
    """After the markdelete of Po A, the sweep also resets its former member to the role default. That reset is
    native port-channel behaviour (the same at the base, without the field); Po B and its member are never written."""
    result, calls = _run([_po({**BFD_ON, "members": [MEM_B]}, PO_B)], "overridden", _aggregate())
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [
        (MARK, [[h.SERIAL, PO_A]]), (DEPLOY, [[h.SERIAL, PO_A]]),
        (MODIFY, [[h.SERIAL, MEM_A, h.ROUTED]]), (DEPLOY, [[h.SERIAL, MEM_A]]),
    ]
    retained = _have({**BFD_ON, "members": [MEM_B]}, PO_B) + _member_have(MEM_B, PO_B)
    result, calls = _run([_po({**BFD_ON, "members": [MEM_B]}, PO_B)], "overridden", retained)
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == []


def test_deleted_retires_the_port_channel_and_a_repeat_writes_nothing():
    target = [{"name": PO_A, "type": "pc", "switch": [h.SWITCH_IP]}]
    have = _have({**BFD_ON, "members": [MEM_A]}) + _member_have(MEM_A, PO_A)
    result, calls = _run(target, "deleted", have)
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [(MARK, [[h.SERIAL, PO_A]]), (DEPLOY, [[h.SERIAL, PO_A]])]
    result, calls = _run(target, "deleted", [])
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
    target = _have(BFD_ON)
    writes = []
    with patch.object(h, "_transport", _query_transport(target + _have(BASE, PO_B), writes)):
        result, calls = h.run_configs([{"name": PO_A, "switch": [h.SWITCH_IP]}], "query", [])
    assert not result.get("failed"), result.get("msg")
    assert writes == [] and h.writes(calls) == []
    assert result["response"] == target, "query must return the controller entry unchanged"
    assert result["response"][0]["interfaces"][0]["nvPairs"][NVPAIR] == "true"
    assert not result.get("changed")


# ------------------------------------------------------------------ unaffected controls and the OSPF boundary
def test_a_plain_l3_port_channel_payload_is_unchanged_by_the_new_row():
    result, calls = h.run_configs([_po(BASE)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    assert NVPAIR not in _only(calls)


@pytest.mark.parametrize("parent", [h.PC_TRUNK, h.PC_ACCESS])
def test_the_key_stays_refused_on_the_layer2_port_channels(parent):
    result, calls = h.run_configs([h.cfg_for(parent, {**h.base_for(parent), KEY: True})], "merged", [])
    assert result.get("failed") and KEY in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


def test_the_routed_ethernet_row_is_unchanged():
    result, calls = h.run_configs([h.cfg(h.IF_A, {**h.BASE_ROUTED, KEY: True})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    assert [(p["policy"], p["interfaces"][0]["nvPairs"][NVPAIR]) for p in found] == [(h.ROUTED, "true")]


def test_the_pim_bfd_field_and_the_ospf_family_travel_together():
    """The two increments on this parent are independent rows in one payload: setting both sends both."""
    prof = {**BFD_ON, "enable_ospf": True, "ospf_tag": "PILOT-OSPF", "ospf_area_id": "0.0.0.0"}
    result, calls = h.run_configs([_po(prof)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert (nv[NVPAIR], nv["ospf"], nv["ospfTag"], nv["OSPF_AREA_ID"]) == ("true", "true", "PILOT-OSPF", "0.0.0.0")
