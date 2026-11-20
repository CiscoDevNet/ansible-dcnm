"""SMU 4.3.1.0175006020 fields: the BFD interval of a routed Ethernet (int_routed_host, lot smu020_routed_bfd).

    int_routed_host  bfdInterval       enable_bfd_interval  boolean, default false, reset "false"
    int_routed_host  bfdTxInterval     bfd_tx_interval      50-999, required while bfdInterval is true, inert while false
    int_routed_host  bfdMinRxInterval  bfd_min_rx_interval  50-999, required while bfdInterval is true, inert while false
    int_routed_host  bfdMultiplier     bfd_multiplier       1-50, required while bfdInterval is true, inert while false

Only the int_routed_host body served with SMU 020 declares these fields; the 017 and 018 bodies, which report the same
NDFC version, do not. The rows are admitted with patch_version 4.3.1.0175006020 only. The 020 parent creates or updates
interface_bfd_interval_11_1 while bfdInterval is true. On NDFC 12.6.0.267 with the 020 templates, a modify that set only
bfdInterval "false" and carried every other stored nvPair removed that child and, after the deploy, the device line; the
three values stayed stored and rendered nothing. So the gate is withdrawn with "false" (explicitly, by omission under
replaced/overridden, and by a reset that keeps int_routed_host), and the values are kept stored.

Real main() through helpers/binding_harness. A HAVE carries the module's own payload plus the four nvPairs with the
defaults the 020 body reads when they are absent (TEMPLATE-PREDICTED: `scope.get("bfdInterval", "false")`, `""` for the
three values). No controller or switch is contacted; the module's disable and omission paths are NOT LIVE TESTED.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import BINDING_TABLE
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding

from .helpers import binding_harness as h
from .helpers import role_reset

SMU_017 = "4.3.1.0175006017"
SMU_018 = "4.3.1.0175006018"
SMU_020 = "4.3.1.0175006020"
VERSION = "12.6.0.267"

FIELDS = {
    "enable_bfd_interval": "bfdInterval",
    "bfd_tx_interval": "bfdTxInterval",
    "bfd_min_rx_interval": "bfdMinRxInterval",
    "bfd_multiplier": "bfdMultiplier",
}
BFD_ON = {"enable_bfd_interval": True, "bfd_tx_interval": 300, "bfd_min_rx_interval": 350, "bfd_multiplier": 5}
BFD_ON_WIRE = {"bfdInterval": "true", "bfdTxInterval": "300", "bfdMinRxInterval": "350", "bfdMultiplier": "5"}
TEMPLATE_DEFAULTS = {"bfdInterval": "false", "bfdTxInterval": "", "bfdMinRxInterval": "", "bfdMultiplier": ""}

# No other registered key, so a refusal or a transport can only come from the fields under test.
ROUTED_PLAIN = {k: v for k, v in h.BASE_ROUTED.items() if k not in ("enable_ospf", "ospf_area_id")}

UNMEASURED = "would disable an option that is enabled on the controller"
NOT_SENT = "No configuration or deployment request was sent"
# The gate withdrawn and the values kept, as the controller stored them after the measured disable.
BFD_OFF_WIRE = {"bfdInterval": "false", "bfdTxInterval": "300", "bfdMinRxInterval": "350", "bfdMultiplier": "5"}
# A stored gate that is not a boolean.
BFD_UNREADABLE_WIRE = {"bfdInterval": "maybe", "bfdTxInterval": "300", "bfdMinRxInterval": "350", "bfdMultiplier": "5"}
# Native routed fields that a withdrawal must carry unchanged.
NATIVE = {"DESC": "pilot", "IP": "192.0.2.1", "PREFIX": "30", "MTU": "9216"}


def _run(profile, state, have=None, patch_version=SMU_020, **kw):
    return h.run(profile, state, have=have, patch_version=patch_version, **kw)


def _have(ifname=h.IF_A, **nv):
    """A routed Ethernet as the module writes it, with the 020 BFD nvPairs at their template defaults, then `nv`."""
    _result, calls = _run(dict(ROUTED_PLAIN), "replaced")
    have = h._payload_as_have(calls)
    have[0]["interfaces"][0]["ifName"] = ifname
    if "INTF_NAME" in have[0]["interfaces"][0]["nvPairs"]:
        have[0]["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname
    have[0]["interfaces"][0]["nvPairs"].update(TEMPLATE_DEFAULTS)
    have[0]["interfaces"][0]["nvPairs"].update(nv)
    return have


def _sent(calls):
    return [nv for nv in h.request_nvpairs(calls) if "bfdInterval" in nv or "bfdTxInterval" in nv]


def _bfd(nv):
    return dict((k, nv[k]) for k in TEMPLATE_DEFAULTS if k in nv)


# ====================================================================================================
# Registry rows
# ====================================================================================================
def test_the_four_rows_carry_the_020_contract():
    for key, nvpair in FIELDS.items():
        b = resolve_binding(h.ROUTED, key)
        assert b["parent_nvpair"] == nvpair
        assert (b["applicable_interface_type"], b["applicable_mode"]) == ("eth", "routed")
        assert b["patch_versions"] == (SMU_020,)
        assert b["dropped_on_policy_change"] is True
        assert "disable_unmeasured" not in b
    gate = resolve_binding(h.ROUTED, "enable_bfd_interval")
    assert gate["default_template"] is False and gate["reset_wire"] == "false"
    for key, bounds in (("bfd_tx_interval", (50, 999)), ("bfd_min_rx_interval", (50, 999)), ("bfd_multiplier", (1, 50))):
        b = resolve_binding(h.ROUTED, key)
        assert (b["min_value"], b["max_value"]) == bounds
        assert b["inert_when"] == {"nvpair": "bfdInterval", "value": "false", "required": True}
        assert "reset_wire" not in b, "no clear of the values was measured; they stay stored while the gate is off"


def test_every_declared_patch_version_is_an_approved_patch():
    declared = set(v for b in BINDING_TABLE for v in b.get("patch_versions", ()))
    assert declared == {SMU_020}
    assert declared <= gie_engine.GIE_ENABLED_PATCH_VERSIONS


def test_the_subinterface_and_svi_rows_are_unchanged():
    for parent in (h.SUBIF, h.SVI):
        for key in FIELDS:
            b = resolve_binding(parent, key)
            assert "patch_versions" not in b and "disable_unmeasured" not in b and "inert_when" not in b
            assert b["reset_wire"] == ("false" if key == "enable_bfd_interval" else "")


# ====================================================================================================
# Admission: the new routes need 020; the existing BFD routes keep every approved context
# ====================================================================================================
@pytest.mark.parametrize("patch_version", [SMU_017, SMU_018, "4.4.1"])
@pytest.mark.parametrize("key", sorted(FIELDS))
def test_routed_bfd_is_refused_before_any_request_outside_020(key, patch_version):
    profile = dict(ROUTED_PLAIN, **{key: BFD_ON[key]})
    result, calls = _run(profile, "merged", have=_have(), patch_version=patch_version)
    assert result.get("failed"), result
    assert "'%s' on int_routed_host requires caller-supplied patch_version %s" % (key, SMU_020) in result["msg"]
    assert h.writes(calls) == []


@pytest.mark.parametrize("patch_version", [SMU_017, SMU_018, "4.4.1"])
def test_an_explicit_disable_is_refused_before_any_request_outside_020(patch_version):
    result, calls = _run(dict(ROUTED_PLAIN, enable_bfd_interval=False), "merged", have=_have(**BFD_ON_WIRE),
                         patch_version=patch_version)
    assert result.get("failed"), result
    assert "'enable_bfd_interval' on int_routed_host requires caller-supplied patch_version %s" % SMU_020 in result["msg"]
    assert h.writes(calls) == []


@pytest.mark.parametrize("patch_version", [None, "4.3.1.0175006019"])
def test_an_unapproved_patch_keeps_the_general_refusal(patch_version):
    result, calls = _run(dict(ROUTED_PLAIN, **BFD_ON), "merged", have=_have(), patch_version=patch_version)
    assert result.get("failed") and "requires caller-supplied patch_version 4.3.1.0175006017" in result["msg"]
    assert h.writes(calls) == []


@pytest.mark.parametrize("patch_version", [SMU_017, SMU_018, SMU_020, "4.4.1"])
@pytest.mark.parametrize("parent", [h.SUBIF, h.SVI])
def test_subinterface_and_svi_bfd_are_sent_in_every_approved_context(parent, patch_version):
    add, err = gie_engine.gie_contribute_nvpairs(parent, dict(BFD_ON), VERSION, patch_version)
    assert err is None and add == BFD_ON_WIRE


@pytest.mark.parametrize("patch_version", [SMU_018, SMU_020])
def test_subinterface_bfd_through_main_is_unchanged(patch_version):
    result, calls = h.run(h.base_for(h.SUBIF, **BFD_ON), "merged", parent=h.SUBIF, patch_version=patch_version)
    assert not result.get("failed"), result.get("msg")
    assert _bfd(_sent(calls)[0]) == BFD_ON_WIRE


@pytest.mark.parametrize("patch_version", [SMU_017, SMU_018, "4.4.1", None])
@pytest.mark.parametrize("key", sorted(FIELDS))
def test_outside_020_the_routed_rows_are_inapplicable_for_omission_and_dependencies(key, patch_version):
    assert gie_engine.gie_binding_applicable(h.ROUTED, key, VERSION, patch_version) is False
    action, _wire = gie_engine.gie_withdrawal_action(h.ROUTED, key, BFD_ON_WIRE[FIELDS[key]], VERSION, patch_version)
    assert action == gie_engine.GIE_WITHDRAW_INAPPLICABLE
    writes, conflicts = gie_engine.gie_dependency_plan(
        h.ROUTED, {"bfdInterval": "false"}, dict(BFD_ON_WIRE), {"bfdInterval"}, True, VERSION, patch_version)
    assert (writes, conflicts) == ({}, [])


@pytest.mark.parametrize("key", sorted(FIELDS))
def test_with_020_the_routed_rows_are_applicable(key):
    assert gie_engine.gie_binding_applicable(h.ROUTED, key, VERSION, SMU_020) is True


def test_outside_020_an_unrelated_change_over_stored_bfd_neither_resets_nor_refuses():
    """A HAVE with the four nvPairs under 018 (it cannot hold them there; this checks the boundary only)."""
    have = _have(**BFD_ON_WIRE)
    result, calls = _run(dict(ROUTED_PLAIN, description="smu018-unrelated"), "replaced", have=have, patch_version=SMU_018)
    assert not result.get("failed"), result.get("msg")
    for nv in h.request_nvpairs(calls):
        for nvpair, value in BFD_ON_WIRE.items():
            assert nv.get(nvpair, value) == value, "no reset may be invented for an inapplicable row"


# ====================================================================================================
# Create, update, omission, repetition and several interfaces (merged)
# ====================================================================================================
def test_create_sends_the_gate_and_the_three_values():
    result, calls = _run(dict(ROUTED_PLAIN, **BFD_ON), "merged", have=_have())
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is True
    assert [_bfd(nv) for nv in _sent(calls)] == [BFD_ON_WIRE]


def test_update_of_one_value_carries_the_others_from_have():
    result, calls = _run(dict(ROUTED_PLAIN, bfd_tx_interval=400), "merged", have=_have(**BFD_ON_WIRE))
    assert not result.get("failed"), result.get("msg")
    assert [_bfd(nv) for nv in _sent(calls)] == [dict(BFD_ON_WIRE, bfdTxInterval="400")]


def test_merged_omission_keeps_the_stored_values():
    result, calls = _run(dict(ROUTED_PLAIN, description="unrelated-change"), "merged", have=_have(**BFD_ON_WIRE))
    assert not result.get("failed"), result.get("msg")
    assert [_bfd(nv) for nv in _sent(calls)] == [BFD_ON_WIRE]
    assert not any("bfdInterval" in nv for nv in h.diff_nvpairs(result))


def test_repeating_the_applied_configuration_writes_nothing():
    result, calls = _run(dict(ROUTED_PLAIN, **BFD_ON), "merged", have=_have(**BFD_ON_WIRE))
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is False and h.writes(calls) == []


def test_two_interfaces_of_the_same_parent_keep_their_own_values():
    have = _have(h.IF_A) + _have(h.IF_B, **BFD_ON_WIRE)
    configs = [h.cfg(h.IF_A, dict(ROUTED_PLAIN, **BFD_ON)),
               h.cfg(h.IF_B, dict(ROUTED_PLAIN, bfd_multiplier=9))]
    result, calls = h.run_configs(configs, "merged", have=have, patch_version=SMU_020)
    assert not result.get("failed"), result.get("msg")
    by_if = {}
    for c in h.writes(calls):
        for p in c["payload"] if isinstance(c["payload"], list) else [c["payload"]]:
            for intf in p.get("interfaces", []) if isinstance(p, dict) else []:
                if "bfdInterval" in intf.get("nvPairs", {}):
                    by_if[intf["ifName"]] = _bfd(intf["nvPairs"])
    assert by_if == {h.IF_A: BFD_ON_WIRE, h.IF_B: dict(BFD_ON_WIRE, bfdMultiplier="9")}


def test_values_with_the_gate_off_are_sent_as_the_template_accepts_them():
    """IsShow hides them and the parent creates no child while bfdInterval is false; the template does not refuse them."""
    profile = dict(ROUTED_PLAIN, bfd_tx_interval=300)
    result, calls = _run(profile, "merged", have=_have())
    assert not result.get("failed"), result.get("msg")
    assert [_bfd(nv) for nv in _sent(calls)] == [dict(TEMPLATE_DEFAULTS, bfdTxInterval="300")]


def test_check_mode_reports_the_change_and_writes_nothing():
    result, calls = _run(dict(ROUTED_PLAIN, **BFD_ON), "merged", have=_have(), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is True and h.writes(calls) == []
    assert any(_bfd(nv) == BFD_ON_WIRE for nv in h.diff_nvpairs(result))


def test_query_writes_nothing():
    result, calls = _run({"mode": "routed"}, "query", have=_have(**BFD_ON_WIRE))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


# ====================================================================================================
# Dependency and range errors
# ====================================================================================================
@pytest.mark.parametrize("key,value", [
    ("bfd_tx_interval", 49), ("bfd_tx_interval", 1000),
    ("bfd_min_rx_interval", 49), ("bfd_min_rx_interval", 1000),
    ("bfd_multiplier", 0), ("bfd_multiplier", 51),
])
def test_an_out_of_range_value_is_refused_before_any_request(key, value):
    result, calls = _run(dict(ROUTED_PLAIN, **dict(BFD_ON, **{key: value})), "merged", have=_have())
    assert result.get("failed") and key in result["msg"], result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("missing", ["bfd_tx_interval", "bfd_min_rx_interval", "bfd_multiplier"])
def test_enabling_over_an_empty_stored_value_is_refused_before_any_request(missing):
    profile = dict(ROUTED_PLAIN, **dict((k, v) for k, v in BFD_ON.items() if k != missing))
    result, calls = _run(profile, "merged", have=_have())
    assert result.get("failed"), result
    assert "%s (with enable_bfd_interval enabled)" % missing in result["msg"] and NOT_SENT in result["msg"]
    assert h.writes(calls) == []


def test_enabling_with_values_stored_while_off_needs_no_value():
    have = _have(bfdTxInterval="300", bfdMinRxInterval="350", bfdMultiplier="5")
    result, calls = _run(dict(ROUTED_PLAIN, enable_bfd_interval=True), "merged", have=have)
    assert not result.get("failed"), result.get("msg")
    assert [_bfd(nv) for nv in _sent(calls)] == [BFD_ON_WIRE]


# ====================================================================================================
# Disable, omission under replaced/overridden, deletion
# ====================================================================================================
def _withdrawal_body(calls):
    bodies = _sent(calls)
    assert len(bodies) == 1, bodies
    return bodies[0]


def _assert_withdrawn(result, calls):
    """One modify and one deploy; the gate is "false", the values and the native fields are carried as stored."""
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is True
    assert [c["path"].rsplit("/", 1)[-1] for c in h.writes(calls)] == ["modify", "deploy"]
    body = _withdrawal_body(calls)
    assert _bfd(body) == BFD_OFF_WIRE
    assert dict((k, body.get(k)) for k in NATIVE) == NATIVE


@pytest.mark.parametrize("state", ["merged", "replaced", "overridden"])
def test_an_explicit_disable_sends_the_gate_false_and_keeps_the_values(state):
    result, calls = _run(dict(ROUTED_PLAIN, enable_bfd_interval=False), state, have=_have(**BFD_ON_WIRE))
    _assert_withdrawn(result, calls)
    assert [_bfd(nv) for nv in h.diff_nvpairs(result)] == [{"bfdInterval": "false"}]


@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_omitting_a_stored_true_withdraws_the_gate_and_keeps_the_values(state):
    result, calls = _run(dict(ROUTED_PLAIN), state, have=_have(**BFD_ON_WIRE))
    _assert_withdrawn(result, calls)


def test_an_explicit_disable_with_values_sends_them_as_given():
    """The values are inert while the gate is false; the template accepts them (IsShow only)."""
    profile = dict(ROUTED_PLAIN, **dict(BFD_ON, enable_bfd_interval=False, bfd_tx_interval=400))
    result, calls = _run(profile, "merged", have=_have(**BFD_ON_WIRE))
    assert not result.get("failed"), result.get("msg")
    assert _bfd(_withdrawal_body(calls)) == dict(BFD_OFF_WIRE, bfdTxInterval="400")


def test_replaced_with_a_value_and_no_gate_withdraws_the_gate():
    result, calls = _run(dict(ROUTED_PLAIN, bfd_tx_interval=400), "replaced", have=_have(**BFD_ON_WIRE))
    assert not result.get("failed"), result.get("msg")
    assert _bfd(_withdrawal_body(calls)) == dict(BFD_OFF_WIRE, bfdTxInterval="400")


def test_check_mode_disable_reports_the_change_and_writes_nothing():
    result, calls = _run(dict(ROUTED_PLAIN, enable_bfd_interval=False), "merged", have=_have(**BFD_ON_WIRE),
                         check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is True and h.writes(calls) == []
    assert [_bfd(nv) for nv in h.diff_nvpairs(result)] == [{"bfdInterval": "false"}]


@pytest.mark.parametrize("state", ["merged", "replaced", "overridden"])
@pytest.mark.parametrize("disable", [True, False], ids=["explicit_false", "omitted"])
def test_repeating_a_withdrawal_writes_nothing(state, disable):
    """The HAVE the controller kept after the measured disable: gate false, values stored."""
    profile = dict(ROUTED_PLAIN, enable_bfd_interval=False) if disable else dict(ROUTED_PLAIN)
    result, calls = _run(profile, state, have=_have(**BFD_OFF_WIRE))
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is False and h.writes(calls) == []


def test_query_after_a_withdrawal_writes_nothing():
    result, calls = _run({"mode": "routed"}, "query", have=_have(**BFD_OFF_WIRE))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_an_explicit_false_over_a_stored_false_is_not_a_transition(state):
    result, calls = _run(dict(ROUTED_PLAIN, enable_bfd_interval=False), state, have=_have())
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is False and h.writes(calls) == []


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_an_explicit_false_on_a_port_stored_without_the_bfd_nvpairs_sends_only_the_gate(state):
    """A routed port stored before 020 has no BFD nvPairs (observed on .90). An explicit false is sent, as before this
    change; nothing is invented for the values."""
    have = _have()
    for nvpair in TEMPLATE_DEFAULTS:
        del have[0]["interfaces"][0]["nvPairs"][nvpair]
    result, calls = _run(dict(ROUTED_PLAIN, enable_bfd_interval=False), state, have=have)
    assert not result.get("failed"), result.get("msg")
    assert _bfd(_withdrawal_body(calls)) == {"bfdInterval": "false"}


@pytest.mark.parametrize("state", ["merged", "replaced", "overridden"])
def test_omission_over_an_unreadable_stored_gate_fails_closed(state):
    result, calls = _run(dict(ROUTED_PLAIN), state, have=_have(**BFD_UNREADABLE_WIRE))
    assert result.get("failed"), result
    assert "'enable_bfd_interval' on parent 'int_routed_host' has an invalid native type" in result["msg"]
    assert h.writes(calls) == []


@pytest.mark.parametrize("parent", [h.ROUTED, h.SVI, h.SUBIF])
def test_an_explicit_false_over_an_unreadable_stored_gate_is_sent_as_on_the_other_bfd_parents(parent):
    """An explicit value replaces the stored one without reading it, as for every gate with a verified reset."""
    if parent == h.ROUTED:
        have, profile = _have(**BFD_UNREADABLE_WIRE), dict(ROUTED_PLAIN, enable_bfd_interval=False)
    else:
        have, profile = h.build_have(parent), h.base_for(parent, enable_bfd_interval=False)
        have[0]["interfaces"][0]["nvPairs"]["bfdInterval"] = "maybe"
    result, calls = h.run(profile, "replaced", have=have, parent=parent, patch_version=SMU_020)
    assert not result.get("failed"), result.get("msg")
    assert [nv["bfdInterval"] for nv in h.request_nvpairs(calls) if "bfdInterval" in nv] == ["false"]


@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_omitting_a_stored_false_sends_no_bfd_reset(state):
    result, calls = _run(dict(ROUTED_PLAIN, description="unrelated"), state, have=_have())
    assert not result.get("failed"), result.get("msg")
    for nv in h.request_nvpairs(calls):
        assert _bfd(nv) in ({}, TEMPLATE_DEFAULTS), _bfd(nv)


@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_values_stored_while_off_are_inert_and_not_withdrawn(state):
    have = _have(bfdTxInterval="300", bfdMinRxInterval="350", bfdMultiplier="5")
    result, calls = _run(dict(ROUTED_PLAIN, description="unrelated"), state, have=have)
    assert not result.get("failed"), result.get("msg")
    for nv in h.request_nvpairs(calls):
        assert nv.get("bfdTxInterval", "300") == "300"


def _by_interface(calls):
    out = {}
    for c in h.writes(calls):
        for p in c["payload"] if isinstance(c["payload"], list) else [c["payload"]]:
            for intf in p.get("interfaces", []) if isinstance(p, dict) else []:
                if "bfdInterval" in intf.get("nvPairs", {}):
                    out[intf["ifName"]] = _bfd(intf["nvPairs"])
    return out


def test_one_interface_withdrawn_and_one_enabled_in_one_replaced_task():
    have = _have(h.IF_A, **BFD_ON_WIRE) + _have(h.IF_B)
    configs = [h.cfg(h.IF_A, dict(ROUTED_PLAIN)), h.cfg(h.IF_B, dict(ROUTED_PLAIN, **BFD_ON))]
    result, calls = h.run_configs(configs, "replaced", have=have, patch_version=SMU_020)
    assert not result.get("failed"), result.get("msg")
    assert _by_interface(calls) == {h.IF_A: BFD_OFF_WIRE, h.IF_B: BFD_ON_WIRE}


def test_a_merged_disable_leaves_the_other_interface_alone():
    have = _have(h.IF_A, **BFD_ON_WIRE) + _have(h.IF_B, **BFD_ON_WIRE)
    configs = [h.cfg(h.IF_A, dict(ROUTED_PLAIN, enable_bfd_interval=False)), h.cfg(h.IF_B, dict(ROUTED_PLAIN))]
    result, calls = h.run_configs(configs, "merged", have=have, patch_version=SMU_020)
    assert not result.get("failed"), result.get("msg")
    assert _by_interface(calls) == {h.IF_A: BFD_OFF_WIRE}


def test_another_routed_field_without_a_reset_is_still_refused():
    """Control: the general withdrawal rule is unchanged for a routed field that declares no reset."""
    result, calls = _run(dict(ROUTED_PLAIN), "replaced", have=_have(ENABLE_NETFLOW="true"))
    assert result.get("failed"), result
    assert "enable_netflow" in result["msg"] and "enable_bfd_interval" not in result["msg"]
    assert h.writes(calls) == []


def test_the_disable_unmeasured_marker_still_refuses_a_marked_row(monkeypatch):
    """The compiled marker stays available for a row whose disable is not measured; no committed row declares it."""
    assert not any(b.get("disable_unmeasured") for b in BINDING_TABLE)
    monkeypatch.setitem(resolve_binding(h.ROUTED, "enable_bfd_interval"), "disable_unmeasured", True)
    result, calls = _run(dict(ROUTED_PLAIN, enable_bfd_interval=False), "merged", have=_have(**BFD_ON_WIRE))
    assert result.get("failed") and UNMEASURED in result["msg"] and NOT_SENT in result["msg"], result.get("msg")
    assert h.writes(calls) == []


def _role_default_have(role, **nv):
    seed = h.build_have(h.ROUTED, description="legacy-drift")
    _r, calls = role_reset.run("deleted", seed, role, patch_version=SMU_020)
    have = role_reset.as_have(calls)
    have[0]["interfaces"][0]["nvPairs"].update(TEMPLATE_DEFAULTS, **nv)
    return have


@pytest.mark.parametrize("state", role_reset.STATES)
def test_leaf_reset_to_the_trunk_default_leaves_the_bfd_values_with_the_routed_parent(state):
    """routed -> int_trunk_host: measured on 020 (the child and the line left with the policy change)."""
    have = _role_default_have("border", **BFD_ON_WIRE)
    result, calls = role_reset.run(state, have, "leaf", patch_version=SMU_020)
    assert not result.get("failed"), result.get("msg")
    assert role_reset.reset_policies(calls)[0]["policy"] == h.TRUNK
    assert _bfd(role_reset.nvpairs_of_reset(calls)) == {}


@pytest.mark.parametrize("state", role_reset.STATES)
def test_border_reset_on_the_same_parent_withdraws_the_gate(state):
    """border: the role default is int_routed_host itself. The reset carries bfdInterval "false"; the values are inert
    under that gate and are not written, as for a border reset with the gate already off. NOT LIVE TESTED."""
    have = _role_default_have("border", **BFD_ON_WIRE)
    result, calls = role_reset.run(state, have, "border", patch_version=SMU_020)
    assert not result.get("failed"), result.get("msg")
    assert [p["policy"] for p in role_reset.reset_policies(calls)] == [h.ROUTED]
    assert _bfd(role_reset.nvpairs_of_reset(calls)) == {"bfdInterval": "false"}


@pytest.mark.parametrize("state", role_reset.STATES)
def test_border_reset_with_bfd_disabled_proceeds(state):
    have = _role_default_have("border", bfdTxInterval="300", bfdMinRxInterval="350", bfdMultiplier="5")
    result, calls = role_reset.run(state, have, "border", patch_version=SMU_020)
    assert not result.get("failed"), result.get("msg")
    assert [_bfd(nv) for nv in h.request_nvpairs(calls) if _bfd(nv)] == []


def test_refusals_never_echo_a_value():
    result, _calls = _run(dict(ROUTED_PLAIN, **dict(BFD_ON, bfd_tx_interval=777, bfd_multiplier=0)), "merged",
                          have=_have(**BFD_ON_WIRE))
    assert result.get("failed") and "777" not in result["msg"]


def test_the_have_fixture_is_the_module_payload_plus_the_template_defaults():
    have = _have()
    nv = copy.deepcopy(have[0]["interfaces"][0]["nvPairs"])
    assert _bfd(nv) == TEMPLATE_DEFAULTS and have[0]["policy"] == h.ROUTED


# ====================================================================================================
# Generator: the two compiled fields are validated
# ====================================================================================================
def _rows_with(nvpair, **changes):
    rows = h._as_slice_rows(BINDING_TABLE)
    row = next(r for r in rows if (r["parent_template"], r["parent_nvpair"]) == (h.ROUTED, nvpair))
    for k, v in changes.items():
        if v is None:
            row.pop(k, None)
        else:
            row[k] = v
    return rows


def test_the_generator_compiles_the_committed_rows_unchanged():
    assert len(h._load_generator().compile_rows(h._as_slice_rows(BINDING_TABLE))) == len(BINDING_TABLE)


@pytest.mark.parametrize("value", ["4.3.1.0175006020", [], ["4.3.1.0175006020", "4.3.1.0175006020"], ["4.3.1.020-rc"], [20]])
def test_a_malformed_patch_versions_is_rejected(value):
    with pytest.raises(ValueError, match="patch_versions"):
        h._load_generator().compile_rows(_rows_with("bfdTxInterval", patch_versions=value))


@pytest.mark.parametrize("nvpair,changes", [
    ("bfdInterval", {"disable_unmeasured": "true"}),
    ("bfdInterval", {"disable_unmeasured": False}),
    ("bfdInterval", {"disable_unmeasured": True, "default_template": None}),
    ("bfdTxInterval", {"disable_unmeasured": True}),
], ids=["string", "false", "no_default", "row_without_default"])
def test_a_malformed_disable_unmeasured_is_rejected(nvpair, changes):
    with pytest.raises(ValueError, match="disable_unmeasured"):
        h._load_generator().compile_rows(_rows_with(nvpair, **changes))
