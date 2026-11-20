"""SMU 4.3.1.0175006020 fields: the BFD interval of a routed Ethernet (int_routed_host, lot smu020_routed_bfd).

    int_routed_host  bfdInterval       enable_bfd_interval  boolean, default false, no reset
    int_routed_host  bfdTxInterval     bfd_tx_interval      50-999, required while bfdInterval is true, no reset
    int_routed_host  bfdMinRxInterval  bfd_min_rx_interval  50-999, required while bfdInterval is true, no reset
    int_routed_host  bfdMultiplier     bfd_multiplier       1-50, required while bfdInterval is true, no reset

Only the int_routed_host body served with SMU 020 declares these fields; the 017 and 018 bodies, which report the same
NDFC version, do not. The rows are admitted with patch_version 4.3.1.0175006020 only. The 020 parent creates or updates
interface_bfd_interval_11_1 while bfdInterval is true and has no branch that deletes it, so an explicit disable of a
stored true is refused before any request, and so is a withdrawal of a stored true under replaced, overridden or a
same-parent role reset.

Real main() through helpers/binding_harness. A HAVE carries the module's own payload plus the four nvPairs with the
defaults the 020 body reads when they are absent (TEMPLATE-PREDICTED: `scope.get("bfdInterval", "false")`, `""` for the
three values). NOT LIVE TESTED; no controller or switch is contacted.
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


def _run(profile, state, have=None, patch_version=SMU_020, **kw):
    return h.run(profile, state, have=have, patch_version=patch_version, **kw)


def _have(ifname=h.IF_A, **nv):
    """A routed Ethernet as the module writes it, with the 020 BFD nvPairs at their template defaults, then `nv`."""
    _result, calls = _run(dict(ROUTED_PLAIN), "replaced")
    have = h._payload_as_have(calls)
    have[0]["interfaces"][0]["ifName"] = ifname
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
def test_the_four_rows_carry_the_020_contract_and_no_reset():
    for key, nvpair in FIELDS.items():
        b = resolve_binding(h.ROUTED, key)
        assert b["parent_nvpair"] == nvpair
        assert (b["applicable_interface_type"], b["applicable_mode"]) == ("eth", "routed")
        assert b["patch_versions"] == (SMU_020,)
        assert "reset_wire" not in b, "withdrawal is not established; no reset may be declared"
        assert b["dropped_on_policy_change"] is True
    gate = resolve_binding(h.ROUTED, "enable_bfd_interval")
    assert gate["default_template"] is False and gate["disable_unmeasured"] is True
    for key, bounds in (("bfd_tx_interval", (50, 999)), ("bfd_min_rx_interval", (50, 999)), ("bfd_multiplier", (1, 50))):
        b = resolve_binding(h.ROUTED, key)
        assert (b["min_value"], b["max_value"]) == bounds
        assert b["inert_when"] == {"nvpair": "bfdInterval", "value": "false", "required": True}


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
@pytest.mark.parametrize("state", ["merged", "replaced", "overridden"])
def test_an_explicit_disable_of_a_stored_true_is_refused_before_any_request(state):
    profile = dict(ROUTED_PLAIN, **dict(BFD_ON, enable_bfd_interval=False))
    result, calls = _run(profile, state, have=_have(**BFD_ON_WIRE))
    assert result.get("failed"), result
    assert UNMEASURED in result["msg"] and "enable_bfd_interval on %s" % h.IF_A in result["msg"]
    assert NOT_SENT in result["msg"]
    assert h.writes(calls) == []


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_an_explicit_false_over_a_stored_false_is_not_a_transition(state):
    result, calls = _run(dict(ROUTED_PLAIN, enable_bfd_interval=False), state, have=_have())
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is False and h.writes(calls) == []


@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_omitting_a_stored_true_is_refused_as_a_withdrawal_without_a_verified_reset(state):
    result, calls = _run(dict(ROUTED_PLAIN, description="unrelated"), state, have=_have(**BFD_ON_WIRE))
    assert result.get("failed"), result
    assert "enable_bfd_interval" in result["msg"]
    assert h.writes(calls) == []


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


def _role_default_have(role, **nv):
    seed = h.build_have(h.ROUTED, description="legacy-drift")
    _r, calls = role_reset.run("deleted", seed, role, patch_version=SMU_020)
    have = role_reset.as_have(calls)
    have[0]["interfaces"][0]["nvPairs"].update(TEMPLATE_DEFAULTS, **nv)
    return have


@pytest.mark.parametrize("state", role_reset.STATES)
def test_leaf_reset_to_the_trunk_default_leaves_the_bfd_values_with_the_routed_parent(state):
    """routed -> int_trunk_host: int_routed_host realizes the child with entity = source = INTF_NAME, and its delete()
    (identical in the 018 and 020 bodies) removes such children on a policy change. Source analysis, not measured."""
    have = _role_default_have("border", **BFD_ON_WIRE)
    result, calls = role_reset.run(state, have, "leaf", patch_version=SMU_020)
    assert not result.get("failed"), result.get("msg")
    assert role_reset.reset_policies(calls)[0]["policy"] == h.TRUNK
    assert _bfd(role_reset.nvpairs_of_reset(calls)) == {}


@pytest.mark.parametrize("state", role_reset.STATES)
def test_border_reset_on_the_same_parent_with_bfd_enabled_is_refused(state):
    """border: the role default is int_routed_host itself, so the reset would have to withdraw bfdInterval true."""
    have = _role_default_have("border", **BFD_ON_WIRE)
    result, calls = role_reset.run(state, have, "border", patch_version=SMU_020)
    assert result.get("failed"), result
    assert "enable_bfd_interval (bfdInterval)" in result["msg"]
    assert h.writes(calls) == []


@pytest.mark.parametrize("state", role_reset.STATES)
def test_border_reset_with_bfd_disabled_proceeds(state):
    have = _role_default_have("border", bfdTxInterval="300", bfdMinRxInterval="350", bfdMultiplier="5")
    result, calls = role_reset.run(state, have, "border", patch_version=SMU_020)
    assert not result.get("failed"), result.get("msg")


def test_refusals_never_echo_a_value():
    result, _calls = _run(dict(ROUTED_PLAIN, **dict(BFD_ON, enable_bfd_interval=False, bfd_tx_interval=777)), "merged",
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
    ("bfdInterval", {"default_template": None}),
    ("bfdTxInterval", {"disable_unmeasured": True}),
], ids=["string", "false", "no_default", "row_without_default"])
def test_a_malformed_disable_unmeasured_is_rejected(nvpair, changes):
    with pytest.raises(ValueError, match="disable_unmeasured"):
        h._load_generator().compile_rows(_rows_with(nvpair, **changes))
