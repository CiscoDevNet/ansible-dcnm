# Copyright (c) 2026 Cisco and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Trunk port-channel `link_transmit_reset_skip` (nvPair linkTransmitResetSkip on int_port_channel_trunk_host).

The option is the DEFAULT a member takes when it joins the port-channel: a member added while the parent is true
stores true; a member that already exists keeps its stored value when the parent is raised or lowered. These tests
therefore assert only what the module writes for the PARENT: no member child is ever written, and a parent value that
differs from a member's is not treated as corrupt state. They make no claim about the device.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding, resolve_by_nvpair
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import gie_withdrawal_harness as h

PCT = h.PC_TRUNK
KEY = "link_transmit_reset_skip"
NVP = "linkTransmitResetSkip"
MEMBER_TPL = "int_port_channel_trunk_member_11_1"


def _po(extra=None, **kw):
    return h.cfg_for(PCT, {**h.BASE_PC_TRUNK, **(extra or {})}, **kw)


def _have(value):
    """The parent as the controller returns it: built from the module's own payload, then the stored value set."""
    have = h.build_have(PCT, KEY, value) if value is not None else h.build_have(PCT)
    return have


def _stored(have):
    return have[0]["interfaces"][0]["nvPairs"].get(NVP)


def _writes(calls):
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    return found


def _only(calls):
    found = _writes(calls)
    assert len(found) == 1, [p["policy"] for p in found]
    pol = found[0]
    assert pol["policy"] == PCT and len(pol["interfaces"]) == 1, pol["policy"]
    assert pol["interfaces"][0]["ifName"].lower() == h.PC_A.lower()
    return pol["interfaces"][0]["nvPairs"]


def _paths(calls):
    return [c["method"] + " " + c["path"].split("/rest/")[-1].split("?")[0] for c in h.writes(calls)]


def _member_rows(parent_value, member_values):
    """A HAVE with the parent and mixed members, as the saved controller observations show (parent false, one member true)."""
    have = copy.deepcopy(_have(parent_value))
    for name, value in member_values.items():
        have.append({"policy": MEMBER_TPL, "interfaces": [{
            "interfaceType": "INTERFACE_ETHERNET", "serialNumber": h.SERIAL, "ifName": name, "fabricName": h.FABRIC,
            "nvPairs": {"INTF_NAME": name, NVP: "true" if value else "false", "ADMIN_STATE": "false"}}]})
    return have


# ------------------------------------------------------------------ the row
def test_the_row_matches_the_017_body_and_is_only_on_the_trunk_port_channel():
    b = resolve_binding(PCT, KEY)
    assert b is not None, "not registered on int_port_channel_trunk_host"
    assert b["parent_nvpair"] == NVP and b["mechanism"] == "passthrough" and b["type"] == "boolean"
    assert b["reset_wire"] == "false", "the template declares defaultValue=false"
    assert resolve_by_nvpair(PCT, NVP) is b
    assert "inert_when" not in b
    for other in (h.PC_ACCESS, h.PC_DOT1Q, h.VPC_TRUNK, h.TRUNK, h.ROUTED, h.LOOPBACK):
        assert resolve_binding(other, KEY) is None, other


# ------------------------------------------------------------------ merged
@pytest.mark.parametrize("value,wire", [(True, "true"), (False, "false")])
def test_merged_create_sends_the_explicit_parent_value(value, wire):
    result, calls = h.run_configs([_po({KEY: value})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)[NVP] == wire
    assert _paths(calls) == ["POST globalInterface", "POST globalInterface/deploy"]


@pytest.mark.parametrize("stored,new", [(False, True), (True, False)])
def test_merged_explicit_value_updates_the_parent_and_keeps_the_other_fields(stored, new):
    have = _have(stored)
    result, calls = h.run_configs([_po({KEY: new})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert nv[NVP] == ("true" if new else "false")
    assert nv["DESC"] == "pilot" and nv["MEMBER_INTERFACES"] == h.PC_MEMBER
    assert _paths(calls) == ["POST interface/modify", "POST globalInterface/deploy"]


def test_merged_omission_preserves_the_stored_parent_value_in_a_description_only_update():
    """The observed loss: a description-only merged call turned a stored true into false."""
    have = _have(True)
    assert _stored(have) == "true"
    result, calls = h.run_configs([_po({"description": "changed"})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert nv["DESC"] == "changed"
    assert nv[NVP] == "true", "the unregistered key was left out and the controller reset it to the template default"


def test_the_observed_loss_a_description_only_merged_call_keeps_a_stored_true():
    """The observed true-to-false loss, reproduced WITHOUT naming the new option.

    The HAVE is the module's own payload with the controller's stored value written in by hand, so this test is
    meaningful on a tree that does not know the option: there the outbound modify omits the key, the controller
    stores the template default, and the assertion below fails.
    """
    have = h.build_have(PCT)
    have[0]["interfaces"][0]["nvPairs"][NVP] = "true"
    result, calls = h.run_configs([_po({"description": "changed"})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert nv["DESC"] == "changed"
    assert nv.get(NVP) == "true", "the stored parent value is missing from the outbound modify (observed loss)"


def test_merged_omission_keeps_a_stored_false_too():
    have = _have(False)
    result, calls = h.run_configs([_po({"description": "changed"})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)[NVP] == "false"


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_repeating_the_stored_value_writes_nothing(state):
    have = _have(True)
    result, calls = h.run_configs([_po({KEY: True})], state, have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and result.get("changed") is False


# ------------------------------------------------------------------ replaced
def test_replaced_omission_resets_the_parent_to_the_template_default():
    have = _have(True)
    result, calls = h.run_configs([_po()], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)[NVP] == "false"


def test_replaced_with_the_default_stored_and_the_option_omitted_writes_nothing():
    have = _have(False)
    result, calls = h.run_configs([_po()], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_replaced_explicit_true_is_kept_and_the_other_fields_follow_the_request():
    have = _have(True)
    result, calls = h.run_configs([_po({KEY: True, "description": "new"})], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert (nv[NVP], nv["DESC"]) == ("true", "new")


# ------------------------------------------------------------------ members are not written; disagreement is not corruption
@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_a_parent_that_differs_from_its_members_is_not_corrupt_state(state):
    """Saved observation: parent false, one member false, one member true. The same request again writes nothing."""
    have = _member_rows(False, {"Ethernet1/12": False, "Ethernet1/13": True})
    result, calls = h.run_configs([_po({KEY: False})], state, have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_changing_the_parent_never_writes_a_member_interface():
    have = _member_rows(False, {"Ethernet1/12": False, "Ethernet1/13": True})
    result, calls = h.run_configs([_po({KEY: True})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    written = {i["ifName"].lower() for p in _writes(calls) for i in p["interfaces"]}
    assert written == {h.PC_A.lower()}, written
    assert _only(calls)[NVP] == "true"


# ------------------------------------------------------------------ validation
@pytest.mark.parametrize("value", ["true", "yes", 1, "maybe"], ids=["str_true", "str_yes", "int_1", "str_maybe"])
def test_a_non_boolean_value_is_refused_before_any_write(value):
    result, calls = h.run_configs([_po({KEY: value})], "merged", [])
    assert result.get("failed") and KEY in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("patch_version", [None, "4.3.1.0175006011"], ids=["no_patch_version", "smu011"])
def test_the_option_needs_an_approved_patch_version(patch_version):
    result, calls = h.run_configs([_po({KEY: True})], "merged", [], patch_version=patch_version)
    assert result.get("failed"), "the option was accepted without SMU 017 or ND >= 4.4.1"
    assert h.writes(calls) == []


def test_numeric_441_is_admitted():
    result, calls = h.run_configs([_po({KEY: True})], "merged", [], patch_version="4.4.1")
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)[NVP] == "true"


@pytest.mark.parametrize("parent", [h.PC_ACCESS, h.PC_DOT1Q], ids=["pc_access", "pc_dot1q"])
def test_other_port_channel_modes_do_not_accept_the_option(parent):
    profile = {**h.base_for(parent), KEY: True}
    result, calls = h.run_configs([h.cfg_for(parent, profile)], "merged", [])
    assert result.get("failed"), "the option was accepted on a port-channel mode whose body is not read"
    assert h.writes(calls) == []


def test_check_mode_reports_the_change_and_writes_nothing():
    result, calls = h.run_configs([_po()], "replaced", _have(True), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and result.get("changed") is True


# ------------------------------------------------------------------ API calls
@pytest.mark.parametrize("state,have_value", [("merged", None), ("replaced", True)])
def test_the_option_adds_a_field_and_no_request(state, have_value):
    """Same requests with and without the option; only the payload gains the nvPair."""
    have = _have(have_value) if have_value is not None else []
    with_key = h.run_configs([_po({KEY: False})], state, have)[1]
    without = h.run_configs([_po()], state, have)[1]
    assert [(c["method"], c["path"].split("?")[0]) for c in with_key] == [(c["method"], c["path"].split("?")[0]) for c in without]


# ------------------------------------------------------------------ deleted, overridden, query
def _identities(calls):
    """Every write in order, as (request, sorted [serial, ifName])."""
    out = []
    for c in h.writes(calls):
        kind = c["method"] + " " + c["path"].split("/rest/")[-1].split("?")[0]
        found = []
        h._collect_policies([c["payload"]], found)
        if found:
            ids = sorted([i["serialNumber"], i["ifName"]] for p in found for i in p["interfaces"])
        else:
            ids = sorted([e.get("serialNumber"), e.get("ifName")] for e in (c["payload"] or []) if isinstance(e, dict))
        out.append((kind, ids))
    return out


_ORIG = h._transport


def _po_detail(calls, have):
    """interface/detail for port-channels, the shape the user-loopback and PVLAN port-channel reads document.

    For an ordinary trunk port-channel this is a synthesized shape, used only so that the overridden sweep sees a
    deletable aggregate."""
    inner = _ORIG(calls, have)

    def send(mod, method, path, payload=None):
        resp = inner(mod, method, path, payload)
        if method == "GET" and "/interface/detail" in path and isinstance(resp.get("DATA"), list):
            for e in resp["DATA"]:
                if str(e.get("ifName", "")).lower().startswith("port-channel"):
                    e.update(ifType="INTERFACE_PORT_CHANNEL", isPhysical="false", deletable=True, editAllowed=True)
        return resp
    return send


def _second_po(value, name="Port-channel302"):
    other = copy.deepcopy(h.build_have(PCT, KEY, value))
    other[0]["interfaces"][0]["ifName"] = name
    other[0]["interfaces"][0]["nvPairs"]["PO_ID"] = name
    return other


def test_deleted_uses_the_aggregate_removal_and_writes_no_reset_skip_flow():
    have = _have(True)
    result, calls = h.run_configs([_po()], "deleted", have)
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [("DELETE interface/markdelete", [[h.SERIAL, h.PC_A]]),
                                  ("POST globalInterface/deploy", [[h.SERIAL, h.PC_A]])]


def test_overridden_retained_port_channel_follows_replaced():
    have = _have(True)
    with patch.object(h, "_transport", _po_detail):
        result, calls = h.run_configs([_po()], "overridden", have)
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)[NVP] == "false"
    with patch.object(h, "_transport", _po_detail):
        result, calls = h.run_configs([_po({KEY: True})], "overridden", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("omitted_value", [True, False])
def test_overridden_removes_an_omitted_port_channel_whatever_its_stored_value(omitted_value):
    """The omitted aggregate goes through the existing removal; its reset-skip value does not change that path."""
    have = _have(True) + _second_po(omitted_value)
    with patch.object(h, "_transport", _po_detail):
        result, calls = h.run_configs([_po({KEY: True})], "overridden", have)
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [("DELETE interface/markdelete", [[h.SERIAL, "Port-channel302"]]),
                                  ("POST globalInterface/deploy", [[h.SERIAL, "Port-channel302"]])]


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


def test_query_returns_the_parent_value_and_claims_nothing_about_the_members():
    stored = _have(False)
    writes = []
    with patch.object(h, "_transport", _query_transport(stored, writes)):
        result, calls = h.run_configs([{"name": h.PC_A, "switch": [h.SWITCH_IP]}], "query", [])
    assert not result.get("failed"), result.get("msg")
    assert writes == [] and h.writes(calls) == [] and not result.get("changed")
    assert result["response"] == stored, "query must return the controller entry unchanged"
    assert result["response"][0]["interfaces"][0]["nvPairs"][NVP] == "false"
