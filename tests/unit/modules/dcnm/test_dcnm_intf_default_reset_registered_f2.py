"""F2: resetting a physical port to its role default also withdraws registered drift.

Review finding F2 (Kapa, KAPA-OCT12-1): named `deleted` and `overridden` compare the role default
payload with the controller's policy on legacy nvPairs only, and the default payload carries no
registered nvPair. A port whose only drift was a registered field (an ACL, flow control) read as
already default; a reset that was sent for another reason left the field in place.

Real main() through gie_withdrawal_harness. The roles are the ones NDFC returns, lower-case
("leaf" -> int_trunk_host, "border" -> int_routed_host); the binding fixture's "Leaf" is not
representative and is not used. The transport only adds the physical-port flags a real 12.6.0.267
interface-detail read carries (deletable "false", editAllowed "true", mgmtIpAddress), so the named
`deleted` path is in scope. The "already default" HAVE is the module's own emitted reset payload.
Values are synthetic.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import os
from unittest.mock import patch

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table as table
from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine as engine
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import gie_withdrawal_harness as h

ACL = "SYNTHETIC-ACL"
NO_WITHDRAWAL = "This module has no verified withdrawal for it; it must be cleaned up by a separate, verified procedure"
STATES = ("deleted", "overridden")
ROLES = {
    "leaf": dict(default=h.TRUNK, drift={"aclFilter": ACL, "flowcontrolReceive": "on"},
                 seed=dict(acl_filter=ACL, flowcontrol_receive="on")),
    "border": dict(default=h.ROUTED, drift={"ipv4AclIn": ACL}, seed=dict(ipv4_acl_in=ACL)),
}
_ORIG_TRANSPORT = h._transport


def _physical_transport(flags):
    def factory(calls, have):
        inner = _ORIG_TRANSPORT(calls, have)

        def send(mod, method, path, payload=None):
            resp = inner(mod, method, path, payload)
            if method == "GET" and "/interface/detail" in path and isinstance(resp.get("DATA"), list):
                for e in resp["DATA"]:
                    if str(e.get("isPhysical")).lower() == "true":
                        e.update(flags)
            return resp
        return send
    return factory


PHYSICAL = {"deletable": "false", "editAllowed": "true", "mgmtIpAddress": h.SWITCH_IP}


def _inventory(role):
    path = os.path.join(os.path.dirname(h.__file__), "fixtures", "dcnm_intf_binding_configs.json")
    inv = json.load(open(path))["mock_fab_inv_data"]
    for v in inv.values():
        v["switchRole"] = role
    return inv


def run(state, have, role, configs=None, flags=None, patch_version=h._UNSET):
    if configs is None:
        configs = [{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}] if state == "deleted" else []
    with patch.object(h, "_transport", _physical_transport(flags or PHYSICAL)):
        return h.run_configs(configs, state, have=have, patch_version=patch_version,
                             extra_patch=patch.object(module, "get_fabric_inventory_details", return_value=_inventory(role)))


def reset_policies(calls):
    found = []
    h._collect_policies([c["payload"] for c in h.split_calls(calls)["updates"]], found)
    return found


def as_have(calls):
    found = reset_policies(calls)
    assert len(found) == 1, found
    have = copy.deepcopy(found)
    have[0]["interfaces"][0]["interfaceType"] = "INTERFACE_ETHERNET"
    have[0]["interfaces"][0]["fabricName"] = h.FABRIC
    return have


_DEFAULT_HAVE = {}


def default_have(role):
    """The role default exactly as this module writes it (legacy drift reset once, payload taken back)."""
    if role not in _DEFAULT_HAVE:
        seed = h.build_have(ROLES[role]["default"], description="legacy-drift")
        _r, calls = run("deleted", seed, role)
        _DEFAULT_HAVE[role] = as_have(calls)
    return copy.deepcopy(_DEFAULT_HAVE[role])


def nvpairs_of_reset(calls):
    return reset_policies(calls)[0]["interfaces"][0]["nvPairs"]


def reset_wire(parent, nvpair):
    return table.resolve_by_nvpair(parent, nvpair)["reset_wire"]


# ------------------------------------------------------------------ the finding, fixed
@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("role", sorted(ROLES))
def test_registered_only_drift_is_reset_with_the_registry_wires(role, state):
    have = default_have(role)
    have[0]["interfaces"][0]["nvPairs"].update(ROLES[role]["drift"])
    result, calls = run(state, have, role)
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is True and len(h.split_calls(calls)["updates"]) == 1
    sent = nvpairs_of_reset(calls)
    assert reset_policies(calls)[0]["policy"] == ROLES[role]["default"]
    for nvpair in ROLES[role]["drift"]:
        assert sent[nvpair] == reset_wire(ROLES[role]["default"], nvpair), nvpair


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("role", sorted(ROLES))
def test_legacy_and_registered_drift_reset_carries_both(role, state):
    seed = h.build_have(ROLES[role]["default"], description="legacy-drift", **ROLES[role]["seed"])
    result, calls = run(state, seed, role)
    assert not result.get("failed"), result.get("msg")
    sent = nvpairs_of_reset(calls)
    assert sent["DESC"] == ""
    for nvpair in ROLES[role]["drift"]:
        assert sent[nvpair] == reset_wire(ROLES[role]["default"], nvpair), nvpair


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("role", sorted(ROLES))
def test_already_default_stays_a_noop(role, state):
    result, calls = run(state, default_have(role), role)
    assert not result.get("failed") and result["changed"] is False and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("role", sorted(ROLES))
def test_second_run_over_the_reset_it_wrote_is_a_noop(role, state):
    have = default_have(role)
    have[0]["interfaces"][0]["nvPairs"].update(ROLES[role]["drift"])
    _r1, calls1 = run(state, have, role)
    result, calls = run(state, as_have(calls1), role)
    assert not result.get("failed") and result["changed"] is False and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("role", sorted(ROLES))
def test_capability_disabled_keeps_the_published_noop(role, state):
    """Without an approved patch_version the classifier answers 'inapplicable': no reset, no failure."""
    have = default_have(role)
    have[0]["interfaces"][0]["nvPairs"].update(ROLES[role]["drift"])
    result, calls = run(state, have, role, patch_version=None)
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


# ------------------------------------------------------------------ no established reset: refused before any write
@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize(
    "nvpair, value, field, reason",
    [
        ("eigrpIpv4Passive", "true", "eigrp_ipv4_passive", "no verified reset is established"),
        ("ospfTag", "SYNTHETIC-TAG", "ospf_tag", "no verified reset is established"),
    ],
)
def test_registered_drift_without_a_reset_is_refused_before_any_write(state, nvpair, value, field, reason):
    have = default_have("border")
    have[0]["interfaces"][0]["nvPairs"][nvpair] = value
    result, calls = run(state, have, "border")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    msg = result["msg"]
    assert reason in msg and "%s (%s) on %s [%s], parent int_routed_host" % (field, nvpair, h.IF_A, h.SERIAL) in msg
    assert "No configuration or deployment request was sent" in msg
    # R-F2-1: no module remedy is promised; an explicit empty value is not a verified withdrawal
    assert NO_WITHDRAWAL in msg and "clear the field on that policy" not in msg and "Clear the field explicitly" not in msg
    assert value not in msg


# ------------------------------------------------------------------ policy change (source != role default)
@pytest.mark.parametrize("state", STATES)
def test_policy_change_with_a_source_only_field_is_refused_and_never_injected(state):
    """border: default int_routed_host; HAVE is int_trunk_host with an ACL. int_routed_host does not
    register aclFilter, and whether the controller drops it with the policy change is not measured."""
    seed = h.build_have(h.TRUNK, acl_filter=ACL)
    result, calls = run(state, seed, "border")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    assert "acl_filter (aclFilter) on %s [%s], int_trunk_host -> int_routed_host" % (h.IF_A, h.SERIAL) in result["msg"]
    # R-F2-1: the source parent (int_trunk_host) HAS a verified reset for aclFilter -> the remedy is offered
    assert "Its current policy has a verified reset: clear the field on that policy first" in result["msg"]
    assert NO_WITHDRAWAL not in result["msg"]
    assert ACL not in result["msg"]


@pytest.mark.parametrize("state", STATES)
def test_policy_change_uses_the_destination_reset_for_a_field_both_parents_register(state):
    seed = h.build_have(h.TRUNK, disable_lldp_receive=True)
    assert seed[0]["interfaces"][0]["nvPairs"]["lldpReceive"] == "true"
    result, calls = run(state, seed, "border")
    assert not result.get("failed"), result.get("msg")
    pol = reset_policies(calls)
    assert len(pol) == 1 and pol[0]["policy"] == h.ROUTED
    assert pol[0]["interfaces"][0]["nvPairs"]["lldpReceive"] == reset_wire(h.ROUTED, "lldpReceive")
    assert "aclFilter" not in pol[0]["interfaces"][0]["nvPairs"]


@pytest.mark.parametrize("state", STATES)
def test_unrelated_legacy_conversion_is_not_blocked(state):
    seed = h.build_have(h.TRUNK, description="legacy-drift")
    result, calls = run(state, seed, "border")
    assert not result.get("failed"), result.get("msg")
    assert [p["policy"] for p in reset_policies(calls)] == [h.ROUTED]


# ------------------------------------------------------------------ scope: a port that is not reset never refuses
def test_named_deleted_skip_when_not_editable_gains_no_refusal():
    have = default_have("border")
    have[0]["interfaces"][0]["nvPairs"]["eigrpIpv4Passive"] = "true"
    result, calls = run("deleted", have, "border", flags={"deletable": "false", "editAllowed": "false", "mgmtIpAddress": h.SWITCH_IP})
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


def test_overridden_keeps_a_configured_port_out_of_the_reset_refusal():
    """IF_A stays in the playbook: it is configured, not reset, so its unsupported registered value
    cannot block the run (the retained-interface rules own it)."""
    have = default_have("border")
    have[0]["interfaces"][0]["nvPairs"]["eigrpIpv4Passive"] = "true"
    conf = [h.cfg(h.IF_A, h.base_for(h.ROUTED, eigrp_ipv4_passive=True, **h.EIGRP_CTX))]
    result, _calls = run("overridden", have, "border", configs=conf)
    assert "Resetting these interfaces" not in (result.get("msg") or ""), result.get("msg")


# ------------------------------------------------------------------ no_log: a refused secret never reaches the output
def test_a_refused_secret_is_named_by_field_and_never_emitted():
    """OSPF_AUTH_KEY has no verified reset on int_routed_host: a border reset refuses, and the key
    (registered from the controller response as no_log) is absent from the real serialised result."""
    assert h.real_serialiser_is_genuine()
    key = "SYNTHETIC-Secret-K1"
    have = default_have("border")
    have[0]["interfaces"][0]["nvPairs"]["OSPF_AUTH_KEY"] = key
    configs = [{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}]
    with patch.object(h, "_transport", _physical_transport(PHYSICAL)):
        out, calls = h.emit_real_result(configs, "deleted", have=have,
                                        extra_patch=patch.object(module, "get_fabric_inventory_details", return_value=_inventory("border")))
    assert h.writes(calls) == []
    assert "ospf_auth_key (OSPF_AUTH_KEY) on %s" % h.IF_A in out
    assert key not in out


# ------------------------------------------------------------------ R-F2-1: message per case, a remedy only where one exists
@pytest.mark.parametrize("state", STATES)
def test_policy_change_without_a_source_reset_offers_no_module_remedy(state):
    """leaf: default int_trunk_host; HAVE is int_routed_host with an OSPF tag (no verified reset on the source,
    not registered on the destination): refused, and no clear-on-current-policy advice."""
    have = default_have("border")
    have[0]["interfaces"][0]["nvPairs"]["ospfTag"] = "SYNTHETIC-TAG"
    result, calls = run(state, have, "leaf")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    msg = result["msg"]
    assert "ospf_tag (ospfTag) on %s [%s], int_routed_host -> int_trunk_host" % (h.IF_A, h.SERIAL) in msg
    assert NO_WITHDRAWAL in msg and "clear the field on that policy" not in msg
    assert "SYNTHETIC-TAG" not in msg


@pytest.mark.parametrize("state", STATES)
def test_unreadable_registered_value_is_refused_without_a_remedy(state):
    have = default_have("border")
    have[0]["interfaces"][0]["nvPairs"]["lldpReceive"] = "True"     # not a boolean wire spelling the validator accepts
    result, calls = run(state, have, "border")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    msg = result["msg"]
    assert "not readable as its type" in msg
    assert "disable_lldp_receive (lldpReceive) on %s [%s], parent int_routed_host" % (h.IF_A, h.SERIAL) in msg
    assert NO_WITHDRAWAL in msg


# ------------------------------------------------------------------ R-F2-2: only GIE_WITHDRAW_NONE proves the destination neutral
# Helper-level: the classifier is forced for the DESTINATION parent only, inside the test. Not reachable through main() today
# (every Ethernet binding shares the 12.6.0.267 floor and the one patch gate); a future per-binding floor would make it so.
def _helper():
    intf = object.__new__(module.DcnmIntf)
    intf.ndfc_version = h.SUPPORTED
    intf.patch_version = h.SUPPORTED_PATCH
    return intf


def _payloads(value):
    uelem = {"policy": h.ROUTED, "interfaces": [{"ifName": h.IF_A, "serialNumber": h.SERIAL, "nvPairs": {}}]}
    have = {"policy": h.TRUNK, "interfaces": [{"ifName": h.IF_A, "serialNumber": h.SERIAL, "nvPairs": {"lldpReceive": value}}]}
    return uelem, have


def _force_destination(action):
    real = module.gie_withdrawal_action

    def fake(parent, key, value, ndfc_version, patch_version=None):
        if parent == h.ROUTED:
            return action, None
        return real(parent, key, value, ndfc_version, patch_version)
    return patch.object(module, "gie_withdrawal_action", fake)


def test_destination_inapplicable_is_a_transition_refusal_not_a_neutral_value():
    uelem, have = _payloads("true")
    with _force_destination(engine.GIE_WITHDRAW_INAPPLICABLE):
        resets, blocked = _helper().dcnm_intf_default_registered_resets(uelem, have)
    assert resets == {}
    assert [(b["reason"], b["nvpair"], b["parent"], b["destination"], b["source_reset"]) for b in blocked] == [
        ("transition", "lldpReceive", h.TRUNK, h.ROUTED, True)]
    assert uelem["interfaces"][0]["nvPairs"] == {}          # pure: nothing applied


def test_destination_none_still_proves_neutrality():
    uelem, have = _payloads("true")
    with _force_destination(engine.GIE_WITHDRAW_NONE):
        resets, blocked = _helper().dcnm_intf_default_registered_resets(uelem, have)
    assert resets == {} and blocked == []


def test_destination_verified_reset_is_still_used_unforced():
    uelem, have = _payloads("true")
    resets, blocked = _helper().dcnm_intf_default_registered_resets(uelem, have)
    assert resets == {"lldpReceive": reset_wire(h.ROUTED, "lldpReceive")} and blocked == []


@pytest.mark.parametrize("action", ["GIE_WITHDRAW_UNSUPPORTED", "GIE_WITHDRAW_UNCLASSIFIED"])
def test_destination_unsupported_or_unclassified_still_refuses(action):
    uelem, have = _payloads("true")
    with _force_destination(getattr(engine, action)):
        resets, blocked = _helper().dcnm_intf_default_registered_resets(uelem, have)
    assert resets == {} and [b["reason"] for b in blocked] == ["transition"]
