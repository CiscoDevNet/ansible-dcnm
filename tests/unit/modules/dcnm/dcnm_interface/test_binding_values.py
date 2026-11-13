"""Binding values and wire representation: types, choices, exact strings, renames, enums and clears."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import hashlib
import json
import pytest

from pathlib import Path
from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import BINDING_TABLE
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import PROVENANCE_SHA256
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GieBindingError
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_all_registered_keys
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_carry_forward_bindings
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_contribute_nvpairs
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_extend_prof_spec
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_guarded_keys
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_invalid_parent_key
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_nvpair_keymap
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_validate_binding_value
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_version_supported
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_ENABLED_PATCH_VERSIONS
from unittest import mock
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import resolve_binding as bool_wire_resolve_binding
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface
from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table as table
from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine as engine

from .helpers.binding_harness import _as_slice_rows
from .helpers.binding_harness import _load_generator
from .helpers import binding_harness as h
from .helpers.binding_harness import ACCESS as MECH_NAMES_ACCESS
from .helpers.binding_harness import TRUNK as MECH_NAMES_TRUNK
from .helpers.binding_harness import base_for
from .helpers.binding_harness import build_have
from .helpers.binding_harness import run
from .helpers.binding_harness import split_calls
from .helpers.binding_harness import request_nvpairs
from .helpers.binding_harness import diff_nvpairs
from .helpers.binding_harness import ACCESS as SPECIAL_ENUM_ACCESS
from .helpers.binding_harness import ROUTED
from .helpers.binding_harness import PC_TRUNK as SPECIAL_ENUM_PC_TRUNK
from .helpers.binding_harness import cfg_for
from .helpers.binding_harness import run_configs
from .helpers.binding_harness import SUPPORTED as NEUTRAL_ENUM_SUPPORTED
from .helpers.binding_harness import SUPPORTED_PATCH


# ====================================================================================================
# Formerly test_gie_passthrough_bindings.py
# Simple passthrough bindings, one case per value type.
#
# Covers positive transport on a supported version, omission, wrong parent, native type,
# enum and length constraints, unsupported/unknown/malformed versions, same-parent
# carry-forward, malformed HAVE, and the generator/table integrity guards.
#
# Also regresses the OSPF-MD and FLOWCONTROL_RECEIVE bindings to prove they stay byte- and
# behaviour-compatible as the table grows.
#
# Offline: no controller and no device.
# ====================================================================================================
TRUNK = "int_trunk_host"
ACCESS = "int_access_host"
LOOPBACK = "int_fabric_loopback_11_1"
PC_TRUNK = "int_port_channel_trunk_host"
PC_ACCESS = "int_port_channel_access_host"
PC_DOT1Q = "int_port_channel_dot1q_tunnel_host"

SUPPORTED = "12.6.0.267"
BELOW = "12.6.0.266"
PATCH = sorted(GIE_ENABLED_PATCH_VERSIONS)[0]
UNSUPPORTED_VERSIONS = (BELOW, "12.5.9.999", None, "", "not.a.version", "12.x.0.267")

GUARD_VALUES = ("root", "none", "loop", "no")


def _wire(value):
    """The nvPair form the engine emits for a PASSTHROUGH value.

    nvPairs is a string-valued map, so a boolean is transported as "true"/"false"; strings and
    enums are already in wire form and pass through untouched. Mirrors gie_engine._to_nvpair_wire.

    This slice originally asserted the native bool instead. That contract was reversed after a
    live measurement: the module compared its own True against the "true" the controller returns,
    never converged, and re-pushed DISABLE_LLDP on every run. See test_binding_values.py.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


# (parent, profile_key, nvpair, a valid explicit PLAYBOOK value -- use _wire() for the payload)
NINE = (
    (TRUNK, "guard_mode", "GUARD_MODE", "root"),
    (PC_TRUNK, "guard_mode", "GUARD_MODE", "loop"),
    (ACCESS, "disable_lldp_transmit", "lldpTransmit", True),
    (TRUNK, "disable_lldp_transmit", "lldpTransmit", False),
    (ACCESS, "acl_filter", "aclFilter", "ACL_A"),
    (TRUNK, "acl_filter", "aclFilter", "ACL_B"),
    (PC_ACCESS, "acl_filter", "aclFilter", "ACL_C"),
    (PC_TRUNK, "acl_filter", "aclFilter", "ACL_D"),
    (PC_DOT1Q, "acl_filter", "aclFilter", "ACL_E"),
)


# ------------------------------------------------------------------ table integrity
def test_table_rows_are_unique_and_the_count_is_pinned():
    """The count is deliberately hardcoded rather than derived.

    Deriving it from the generator's own allowlist would make the assertion tautological: a
    regeneration that added or dropped rows would still pass. The number is meant to fail when
    the table changes, so that the change has to be explained.

    45 = 7 eth access + 8 eth trunk + 5 pc access + 6 pc trunk + 5 pc dot1q
       + 5 vPC access + 6 vPC trunk + 3 fabric loopback
    """
    keys = [(b["parent_template"], b["parent_nvpair"]) for b in BINDING_TABLE]
    # 246 = 245 + the IQ1 vPC PVLAN qosStatsSuppressed row.
    assert len(BINDING_TABLE) == 295   # 228 + six int_vpc_dot1q_tunnel rows + eleven PVLAN companion rows + one vPC PVLAN row
    # + slice 0b_37 (5) + slice 0b_38 (5) + slice 0b_39 (1) + slice 0b_40 (19) + slice rs1 (1) + slice pl1 (4) + slice ul1 (12)
    # + slice 0b_41 (2)
    assert len(set(keys)) == 295, "duplicate (parent, nvpair) row"
    pk_keys = [(b["parent_template"], b["profile_key"]) for b in BINDING_TABLE]
    assert len(set(pk_keys)) == 295, "duplicate (parent, profile_key) row"


def test_provenance_recalculates_from_packaged_rows():
    expected = hashlib.sha256(
        json.dumps(BINDING_TABLE, sort_keys=True, default=list).encode()
    ).hexdigest()
    assert PROVENANCE_SHA256 == expected, "packaged table edited after generation"


def test_nine_new_bindings_are_present_with_reviewed_metadata():
    for parent, pk, nvpair, value in NINE:
        b = resolve_binding(parent, pk)
        assert b is not None, f"{parent}::{pk} missing"
        assert b["parent_nvpair"] == nvpair
        assert b["mechanism"] == "passthrough"
        assert b["min_ndfc_version"] == SUPPORTED


def test_reviewed_types_and_constraints_match_the_registry():
    gm = resolve_binding(TRUNK, "guard_mode")
    assert gm["type"] == "enum"
    assert tuple(gm["valid_values"]) == GUARD_VALUES
    assert gm["default_template"] == "no"
    assert isinstance(gm["default_template"], str), "YAML 1.1 'no' must stay a string"

    lldp = resolve_binding(ACCESS, "disable_lldp_transmit")
    assert lldp["type"] == "boolean"
    assert lldp["default_template"] is False

    acl = resolve_binding(ACCESS, "acl_filter")
    assert acl["type"] == "string"
    assert acl["min_length"] == 1
    assert acl["max_length"] == 64
    assert "default_template" not in acl, "the DSL declares no ACL_FILTER default"


def test_applicable_type_and_mode_are_literal_argspec_values():
    expected = {
        (TRUNK, "guard_mode"): ("eth", "trunk"),
        (PC_TRUNK, "guard_mode"): ("pc", "trunk"),
        (ACCESS, "disable_lldp_transmit"): ("eth", "access"),
        (TRUNK, "disable_lldp_transmit"): ("eth", "trunk"),
        (ACCESS, "acl_filter"): ("eth", "access"),
        (TRUNK, "acl_filter"): ("eth", "trunk"),
        (PC_ACCESS, "acl_filter"): ("pc", "access"),
        (PC_TRUNK, "acl_filter"): ("pc", "trunk"),
        (PC_DOT1Q, "acl_filter"): ("pc", "dot1q"),
    }
    for (parent, pk), (itype, mode) in expected.items():
        b = resolve_binding(parent, pk)
        assert (b["applicable_interface_type"], b["applicable_mode"]) == (itype, mode)


# ------------------------------------------------------------------ generator guards
def test_generator_rejects_duplicate_missing_and_profile_key_mismatch():
    gen = _load_generator()
    rows = _as_slice_rows(BINDING_TABLE)
    assert len(gen.compile_rows(rows)) == 295   # 246 + slices 0b_37 to 0b_41, rs1, pl1 and ul1

    with pytest.raises(ValueError, match="duplicate committed binding"):
        gen.compile_rows(rows + [dict(rows[0])])

    with pytest.raises(ValueError, match="missing committed bindings"):
        gen.compile_rows(rows[:-1])

    wrong = [dict(r) for r in rows]
    wrong[0]["profile_key"] = "not_the_reviewed_key"
    with pytest.raises(ValueError, match="unexpected profile_key"):
        gen.compile_rows(wrong)


def test_generator_enforces_the_registry_schema_per_row():
    """The per-row schema gate, which used to live in a standalone checker that went stale.

    There were TWO out-of-tree validator scripts, and both had been
    dead for four lots without anyone noticing: one still expected a flat list of rows when every
    slice had become a mapping with a `bindings:` key, the other required a `sensitive` field
    that only one surviving slice declares. Neither failed loudly, because nothing ran them --
    and a validator you have to remember to invoke is one that goes stale.

    So the gate moved into compile_rows(), which runs on every regeneration. This case exists so
    it cannot quietly stop enforcing: every rule is asserted by sabotage, and the error has to
    NAME the offending row, because "schema error" on a 228-row table is not actionable.

    Not re-asserted here -- compile_rows owns them above, with their own cases: the allowlist,
    duplicates, profile_key mismatch, unknown mechanism, complete-set.
    """
    gen = _load_generator()
    rows = _as_slice_rows(BINDING_TABLE)
    assert len(gen.compile_rows(rows)) == 295   # 246 + slices 0b_37 to 0b_41, rs1, pl1 and ul1

    nvpair = rows[0]["parent_nvpair"]

    # Every required field, dropped one at a time, must abort the compile. FOUR of them abort
    # at an EARLIER guard with a different message, and that is by design rather than a gap:
    #
    #   parent_template, parent_nvpair   the allowlist guard needs them to form the key at all
    #   profile_key                      it is what that guard compares against the allowlist
    #   mechanism                        the fail-open mechanism gate above rejects a missing one
    #
    # Asserting one single message for all eleven would have meant weakening the assertion to
    # "it raised something", which is how a check stops checking.
    EARLIER_GUARDS = {
        "parent_template": ("unexpected binding", "unexpected profile_key"),
        "parent_nvpair": ("unexpected binding", "unexpected profile_key"),
        "profile_key": ("unexpected binding", "unexpected profile_key"),
        "mechanism": ("declares mechanism",),
    }

    for field in gen.SCHEMA_REQUIRED_FIELDS:
        missing = [dict(r) for r in rows]
        del missing[0][field]
        with pytest.raises(ValueError) as exc:
            gen.compile_rows(missing)
        if field in EARLIER_GUARDS:
            assert any(f in str(exc.value) for f in EARLIER_GUARDS[field]), (
                "{0} must still be refused, by its earlier guard: {1}".format(
                    field, exc.value
                )
            )
        else:
            assert "missing required registry field" in str(exc.value)
            assert field in str(exc.value)
            assert nvpair in str(exc.value), "the error must name the offending row"

    for field, bad, fragment in (
        ("presence_model", "one_axis", "declares presence_model"),
        ("emit_when", "always", "declares emit_when"),
        ("type", "float", "declares type"),
    ):
        broken = [dict(r) for r in rows]
        broken[0][field] = bad
        with pytest.raises(ValueError, match=fragment) as exc:
            gen.compile_rows(broken)
        assert nvpair in str(exc.value), "the error must name the offending row"

    # `sensitive` is NOT required: requiring it is what killed the 454-line checker, and it
    # survives in exactly one slice. A table with none of it must still compile -- asserted
    # above, and this pins the premise.
    assert not any("sensitive" in r for r in rows)


def test_generator_rejects_an_unexpected_binding_claiming_a_committed_key():
    """A non-committed parent reusing a committed public key must fail, not be skipped.

    Silently skipping it would make the binding look merely 'not selected' when in fact it was
    never reviewed. The fixture used int_vpc_trunk_host::GUARD_MODE until that binding was
    committed; int_vpc_dot1q_tunnel replaced it because the module cannot reach that parent at
    all -- pol_types has no "vpc_dot1q" entry -- so it is not a registration candidate and will
    not quietly become one.
    """
    gen = _load_generator()
    rows = _as_slice_rows(BINDING_TABLE)
    rows.append({
        "parent_template": "int_vpc_dot1q_tunnel",
        "parent_nvpair": "GUARD_MODE",
        "profile_key": "guard_mode",
        "type": "enum",
        "mechanism": "passthrough",
        "min_ndfc_version": SUPPORTED,
    })
    with pytest.raises(ValueError, match="unexpected binding"):
        gen.compile_rows(rows)


def test_generator_still_ignores_unrelated_uncommitted_rows():
    """A row with no committed public key is simply not selected (legacy behaviour).

    The fixture is a deliberately SYNTHETIC nvPair. It used to be int_routed_host::ARP_TIMEOUT,
    which broke the day that lot was committed -- the row stopped being uncommitted and the
    generator raised "duplicate committed binding" instead. Any real unregistered nvPair is the
    same time bomb, because the whole point of the backlog is that they eventually get
    registered. A name no template will ever declare keeps the assertion about the generator's
    behaviour rather than about which fields happen to be pending.
    """
    gen = _load_generator()
    rows = _as_slice_rows(BINDING_TABLE)
    rows.append({
        "parent_template": "int_routed_host",
        "parent_nvpair": "WP98_SYNTHETIC_NOT_A_REAL_NVPAIR",
        "profile_key": "wp98_synthetic_not_a_real_key",
        "type": "integer",
        "mechanism": "child_pti",
        "min_ndfc_version": SUPPORTED,
    })
    assert len(gen.compile_rows(rows)) == 295   # 246 + slices 0b_37 to 0b_41, rs1, pl1 and ul1


# ------------------------------------------------------------------ positive transport
@pytest.mark.parametrize("parent,pk,nvpair,value", NINE)
def test_supported_version_transports_the_wire_value(parent, pk, nvpair, value):
    add, err = gie_contribute_nvpairs(parent, {pk: value}, SUPPORTED, PATCH)
    assert err is None
    assert add == {nvpair: _wire(value)}
    # Every passthrough nvPair leaves the engine as a string, whatever the registered type.
    assert isinstance(add[nvpair], str)


def test_every_guard_mode_choice_transports():
    for parent in (TRUNK, PC_TRUNK):
        for value in GUARD_VALUES:
            add, err = gie_contribute_nvpairs(parent, {"guard_mode": value}, SUPPORTED, PATCH)
            assert err is None and add == {"GUARD_MODE": value}
            # Exact type, not isinstance: a str subclass such as AnsibleUnicode would pass an
        # isinstance check while still being the wrong thing on the wire.
        assert type(add["GUARD_MODE"]) is str  # pylint: disable=unidiomatic-typecheck


def test_disable_lldp_transports_both_booleans():
    for parent in (ACCESS, TRUNK):
        for value, wire in ((True, "true"), (False, "false")):
            add, err = gie_contribute_nvpairs(parent, {"disable_lldp_transmit": value}, SUPPORTED, PATCH)
            assert err is None and add == {"lldpTransmit": wire}
            # Lowercase JSON spelling, which is what the template DSL tests against --
            # not Python's str(True) == "True".
            assert add["lldpTransmit"] == wire != str(value)


def test_acl_filter_accepts_boundary_lengths():
    for parent in (ACCESS, TRUNK, PC_ACCESS, PC_TRUNK, PC_DOT1Q):
        for value in ("A", "A" * 64):
            add, err = gie_contribute_nvpairs(parent, {"acl_filter": value}, SUPPORTED, PATCH)
            assert err is None and add == {"aclFilter": value}


def test_multiple_new_keys_on_one_parent_contribute_together():
    add, err = gie_contribute_nvpairs(
        TRUNK,
        {"guard_mode": "root", "disable_lldp_transmit": True, "acl_filter": "ACL_X",
         "flowcontrol_receive": "on"},
        SUPPORTED,
        PATCH,
    )
    assert err is None
    assert add == {
        "GUARD_MODE": "root",
        "lldpTransmit": "true",
        "aclFilter": "ACL_X",
        "flowcontrolReceive": "on",
    }


# ------------------------------------------------------------------ omission
@pytest.mark.parametrize("parent,pk,nvpair,value", NINE)
def test_omission_contributes_nothing(parent, pk, nvpair, value):
    add, err = gie_contribute_nvpairs(parent, {}, SUPPORTED, PATCH)
    assert err is None and add == {}


@pytest.mark.parametrize("parent,pk,nvpair,value", NINE)
def test_omission_is_not_default_false_or_empty_string(parent, pk, nvpair, value):
    add, err = gie_contribute_nvpairs(parent, {"unrelated": "x"}, SUPPORTED, PATCH)
    assert err is None
    assert nvpair not in add
    assert add.get(nvpair) is not False
    assert add.get(nvpair) != ""


def test_prof_spec_gains_no_default_and_only_for_explicit_keys():
    spec = {}
    gie_extend_prof_spec(spec, TRUNK, {})
    assert spec == {}, "an omitted key must not gain a spec entry"

    spec = {}
    gie_extend_prof_spec(
        spec, TRUNK, {"guard_mode": "root", "disable_lldp_transmit": True, "acl_filter": "A"}
    )
    assert set(spec) == {"guard_mode", "disable_lldp_transmit", "acl_filter"}
    for entry in spec.values():
        assert "default" not in entry, "a default would author intent on omission"
    assert spec["guard_mode"]["type"] == "str"
    assert spec["guard_mode"]["choices"] == list(GUARD_VALUES)
    assert spec["disable_lldp_transmit"]["type"] == "bool"
    assert spec["acl_filter"]["type"] == "str"
    assert "choices" not in spec["acl_filter"]


def test_prof_spec_for_pc_parents():
    spec = {}
    gie_extend_prof_spec(spec, PC_DOT1Q, {"acl_filter": "A", "guard_mode": "root"})
    assert set(spec) == {"acl_filter"}, "guard_mode is not registered on pc/dot1q"


# ------------------------------------------------------------------ exact native type
def test_enum_rejects_non_string_and_unknown_choices():
    for bad in (True, False, 1, None, [], {}, "ROOT", "enabled", ""):
        with pytest.raises(GieBindingError):
            gie_validate_binding_value(TRUNK, "guard_mode", bad)


def test_boolean_rejects_strings_and_ints():
    for bad in ("true", "false", "yes", 1, 0, None, [], {}):
        with pytest.raises(GieBindingError):
            gie_validate_binding_value(ACCESS, "disable_lldp_transmit", bad)


def test_string_rejects_non_strings():
    for bad in (True, False, 1, None, [], {}):
        with pytest.raises(GieBindingError):
            gie_validate_binding_value(ACCESS, "acl_filter", bad)


def test_acl_filter_length_constraints_are_enforced():
    """max_length still bites; min_length no longer rejects the EMPTY string.

    This case used to assert both bounds symmetrically, including that ``""`` was rejected
    for being shorter than the registered minimum of 1. That turned out to be wrong about the
    controller: NDFC accepts ``ACL_FILTER: ""``, stores it, withdraws the ``ip port
    access-group`` line on deploy, and returns ``""`` itself for "no ACL configured".
    Enforcing the lower bound on explicit input made the field settable and never clearable,
    with no way out -- a re-deploy does not clear it either, because NaC does not model the
    field and ``vxlan.yaml`` walks past the value.

    The lower bound is now exempted for the empty string specifically, and that exemption has
    its own suite: ``test_binding_values.py``. A short-but-nonempty value is still
    subject to every other check, and the upper bound is unchanged -- there is no reading of
    "too long" that means "unset".
    """
    assert gie_validate_binding_value(ACCESS, "acl_filter", "") == ""
    with pytest.raises(GieBindingError, match="longer than the registered maximum"):
        gie_validate_binding_value(ACCESS, "acl_filter", "A" * 65)


def test_errors_never_echo_the_rejected_value():
    # Each probe must actually be rejected, and each carries a distinctive marker token so
    # the assertion below is meaningful. A 15-char ACL name is VALID (within 1..64), so the
    # ACL probe reaches rejection via length instead.
    probes = [
        (TRUNK, "guard_mode", "marker-enum-value"),
        (ACCESS, "acl_filter", "marker-acl-name" + "B" * 60),
        (ACCESS, "disable_lldp_transmit", "marker-not-a-bool"),
    ]
    for parent, pk, bad in probes:
        try:
            gie_validate_binding_value(parent, pk, bad)
        except GieBindingError as exc:
            assert str(bad) not in str(exc), f"error echoed the value for {pk}"
        else:
            raise AssertionError(f"expected GieBindingError for {pk}")


def test_invalid_explicit_value_fails_before_any_nvpair_is_produced():
    with pytest.raises(GieBindingError):
        gie_contribute_nvpairs(TRUNK, {"guard_mode": "bogus"}, SUPPORTED, PATCH)


# ------------------------------------------------------------------ wrong parent
@pytest.mark.parametrize("pk", ["guard_mode", "disable_lldp_transmit", "disable_lldp_receive", "acl_filter"])
def test_new_keys_are_generically_guarded(pk):
    assert pk in gie_guarded_keys()


def test_wrong_parent_is_reported_for_each_new_key():
    # A parent belongs here only when the TEMPLATE does not declare the field, or when the
    # module cannot reach that parent at all. A parent that declares the field and IS reachable
    # belongs in test_correct_parents_are_accepted instead. Listing one here turns a gap in the
    # registry into an assertion that the gap is correct -- which is exactly how the
    # port-channel and vPC parents stayed unregistered for months with the suite green.
    cases = [
        # int_vpc_access_host really does not declare GUARD_MODE: read from the DSL loaded on
        # the controller, not assumed from its trunk sibling.
        ("guard_mode", [ACCESS, PC_ACCESS, PC_DOT1Q, "int_routed_host",
                        "int_vpc_access_host", None]),
        # disable_lldp is no longer here: int_routed_host declares it and it is now registered
        # (slice 0b_16), so the guard must ACCEPT it -- asserted in test_binding_routed.
        #
        # acl_filter stays, but the reason was wrong. int_routed_host does NOT declare
        # ACL_FILTER -- it declares IPV4_ACL_IN, a different nvPair with a different child
        # (interface_ip_access_group_in_11_1). So this is a template property after all, not a
        # coverage gap: acl_filter is correctly rejected here and always will be.
        ("acl_filter", ["int_routed_host", LOOPBACK, None]),
    ]
    for pk, parents in cases:
        for parent in parents:
            assert gie_invalid_parent_key(parent, [pk]) == pk, (
                f"{pk} must be rejected on {parent}"
            )


def test_correct_parents_are_accepted():
    for parent, pk, nvpair, value in NINE:
        assert gie_invalid_parent_key(parent, [pk]) is None


def test_unknown_legacy_field_is_still_left_alone():
    assert gie_invalid_parent_key("int_routed_host", ["some_unknown_legacy_field"]) is None


# ------------------------------------------------------------------ versions
@pytest.mark.parametrize("parent,pk,nvpair,value", NINE)
@pytest.mark.parametrize("version", UNSUPPORTED_VERSIONS)
def test_unsupported_unknown_or_malformed_version_fails_before_write(
    parent, pk, nvpair, value, version
):
    add, err = gie_contribute_nvpairs(parent, {pk: value}, version, PATCH)
    assert add is None, f"{pk}@{version!r} must not produce a payload"
    assert err and "No change was sent." in err


def test_four_segment_comparison_still_enforces_the_build_number():
    assert gie_version_supported(SUPPORTED, SUPPORTED) is True
    assert gie_version_supported(BELOW, SUPPORTED) is False
    assert gie_version_supported("12.6.0", SUPPORTED) is False
    assert gie_version_supported("12.6.1.0", SUPPORTED) is True


def test_new_bindings_never_withhold_like_ospf_md():
    """The OSPF-MD compat exception must NOT be generalized to the new bindings."""
    for parent, pk, nvpair, value in NINE:
        add, err = gie_contribute_nvpairs(parent, {pk: value}, BELOW, PATCH)
        assert add is None and err, f"{pk} must fail closed, not withhold"


# ------------------------------------------------------------------ carry forward
def test_carry_forward_covers_every_new_passthrough_binding():
    assert {
        (r["parent_nvpair"], r["profile_key"]) for r in gie_carry_forward_bindings(TRUNK)
    } == {
        ("flowcontrolReceive", "flowcontrol_receive"),
        ("flowcontrolSend", "flowcontrol_send"),
        ("spanningTreePortType", "spanning_tree_port_type"),
        ("GUARD_MODE", "guard_mode"),
        ("lldpTransmit", "disable_lldp_transmit"),
        ("lldpReceive", "disable_lldp_receive"),
        ("aclFilter", "acl_filter"),
        ("qosStatsSuppressed", "disable_qos_stats"),
        ("queuingStats", "disable_queuing_stats"),
    }
    assert {
        (r["parent_nvpair"], r["profile_key"]) for r in gie_carry_forward_bindings(ACCESS)
    } == {
        ("flowcontrolReceive", "flowcontrol_receive"),
        ("flowcontrolSend", "flowcontrol_send"),
        ("spanningTreePortType", "spanning_tree_port_type"),
        ("lldpTransmit", "disable_lldp_transmit"),
        ("lldpReceive", "disable_lldp_receive"),
        ("aclFilter", "acl_filter"),
        ("qosStatsSuppressed", "disable_qos_stats"),
        ("queuingStats", "disable_queuing_stats"),
        ("loggingEventPortLinkStatus", "logging_event_port_link_status"),   # SMU 017, slice 0b_37
    }
    # The port-channel parents carry every field registered for them.
    assert {
        (r["parent_nvpair"], r["profile_key"]) for r in gie_carry_forward_bindings(PC_TRUNK)
    } == {
        # Batch 2, slice 0b_34: only this port-channel parent declares the peer-link.
        # See the slice for its validation scope.
        ("ENABLE_VPC_PEER_LINK", "enable_vpc_peer_link"),
        ("GUARD_MODE", "guard_mode"),
        ("aclFilter", "acl_filter"),
        ("lldpTransmit", "disable_lldp_transmit"),
        ("lldpReceive", "disable_lldp_receive"),
        ("spanningTreePortType", "spanning_tree_port_type"),
        ("qosStatsSuppressed", "disable_qos_stats"),
        ("queuingStats", "disable_queuing_stats"),
        # Trunk port-channel reset-skip default, slice rs1.
        ("linkTransmitResetSkip", "link_transmit_reset_skip"),
    }
    assert gie_carry_forward_bindings(LOOPBACK) == []


def test_carry_forward_accepts_only_exact_authoritative_have_values():
    for value in GUARD_VALUES:
        assert gie_validate_binding_value(
            TRUNK, "guard_mode", value, value_source="have"
        ) == value
    for value in (True, False):
        assert gie_validate_binding_value(
            ACCESS, "disable_lldp_transmit", value, value_source="have"
        ) is value
    assert gie_validate_binding_value(
        ACCESS, "acl_filter", "ACL_OK", value_source="have"
    ) == "ACL_OK"


def test_have_accepts_the_two_encodings_ndfc_actually_returns():
    """Two entries moved out of the malformed list below, because the controller
    contradicted them.

    Captured from GET /rest/interface on a freshly deployed --
    (int_access_host) and Ethernet1/5 (int_trunk_host):

        ACL_FILTER   == ""        no ACL configured: the normal state of a host interface
        DISABLE_LLDP == "false"   NDFC encodes booleans as strings on read-back

    Rejecting them made `state: overridden` abort on any explicitly declared host
    interface, which is every real deployment. They are not malformed -- they are the
    encodings NDFC uses, and carrying them forward asserts "leave as-is".
    """
    assert gie_validate_binding_value(ACCESS, "acl_filter", "", value_source="have") == ""
    assert gie_validate_binding_value(TRUNK, "acl_filter", "", value_source="have") == ""
    for value in ("true", "false"):
        assert gie_validate_binding_value(
            ACCESS, "disable_lldp_transmit", value, value_source="have"
        ) == value


def test_malformed_have_fails_before_diff_or_write():
    """Everything else stays rejected. The two exemptions above are narrow and measured;
    nothing here was loosened by inference.
    """
    bad_have = [
        (TRUNK, "guard_mode", "ROOT"),
        (TRUNK, "guard_mode", True),
        # An EMPTY enum still fails: the ""-exemption is scoped to plain string bindings,
        # so an enum that comes back blank is still treated as malformed.
        (TRUNK, "guard_mode", ""),
        # A boolean accepts "true"/"false" as strings, but not an int.
        (ACCESS, "disable_lldp_transmit", 1),
        (ACCESS, "acl_filter", True),
        (ACCESS, "acl_filter", "C" * 65),
    ]
    for parent, pk, value in bad_have:
        with pytest.raises(GieBindingError):
            gie_validate_binding_value(parent, pk, value, value_source="have")


def test_have_rejection_is_labelled_as_a_controller_value():
    try:
        gie_validate_binding_value(TRUNK, "guard_mode", "ROOT", value_source="have")
    except GieBindingError as exc:
        assert "authoritative controller value" in str(exc)
    else:
        raise AssertionError("expected a GieBindingError")


# ------------------------------------------------------------------ keymap / comparator
def test_keymap_carries_every_new_nvpair():
    km = gie_nvpair_keymap()
    assert km["GUARD_MODE"] == "guard_mode"
    assert km["lldpTransmit"] == "disable_lldp_transmit"
    assert km["aclFilter"] == "acl_filter"
    assert km["flowcontrolReceive"] == "flowcontrol_receive"
    assert km["flowcontrolSend"] == "flowcontrol_send"
    assert km["spanningTreePortType"] == "spanning_tree_port_type"
    # The OSPF slice on int_routed_host. No module change was needed for these: the keymap is
    # derived from the binding table by gie_nvpair_keymap(), so a new row lands here by itself.
    # Both key-bearing nvPairs reach the keymap like any other. The keymap is how a HAVE
    # nvPair is translated back to a profile key, so leaving a secret out of it would make the
    # controller's value invisible to the comparator -- a re-push on every run, not a leak.
    assert km["OSPF_AUTH_KEY"] == "ospf_auth_key"
    assert km["ospfAuthenticationKey"] == "ospf_authentication_key"
    assert km["OSPF_AUTH_KEY_ID"] == "ospf_auth_key_id"
    assert km["ospfAuthenticationKeyType"] == "ospf_authentication_key_type"
    assert km["ospfAuthentication"] == "enable_ospf_auth"
    assert km["ospf"] == "enable_ospf"
    assert km["ospfTag"] == "ospf_tag"
    assert km["OSPF_AREA_ID"] == "ospf_area_id"
    assert km["ospfCost"] == "ospf_cost"
    # EIGRP, slice 0b_22: thirteen distinct nvPairs, each shared by the three overlay parents,
    # so the keymap grows by thirteen and not by thirty-nine.
    assert km["eigrpProcessTag"] == "eigrp_process_tag"
    assert km["eigrpRouting"] == "enable_eigrp_routing"
    assert km["eigrpIpv4DistributeListDirection"] == "eigrp_ipv4_distribute_list_direction"
    assert km["eigrpBfdDisable"] == "disable_eigrp_bfd"
    assert km["ospfAdvertiseSubnet"] == "ospf_advertise_subnet"
    assert km["bfdInterval"] == "enable_bfd_interval"
    assert km["bfdTxInterval"] == "bfd_tx_interval"
    assert km["hsrpPriorityForwardingThresholdLower"] == "hsrp_priority_forwarding_threshold_lower"
    assert km["hsrpPreemptDelayMinimum"] == "hsrp_preempt_delay_minimum"
    assert km["HSRP_VIPv6"] == "hsrp_vipv6"
    assert km["HSRP_GROUPv6"] == "hsrp_groupv6"
    assert km["ipv4Redirects"] == "disable_ipv4_redirects"
    assert km["ipv6NdSuppressRa"] == "ipv6_nd_suppress_ra"
    assert km["dampening"] == "enable_dampening"
    assert km["dampeningRestartPenalty"] == "dampening_restart_penalty"
    assert km["arpTimeout"] == "arp_timeout"
    assert km["ENABLE_PIM_SPARSE"] == "enable_pim_sparse"
    assert km["PIM_DR_PRIORITY"] == "pim_dr_priority"
    assert km["pimBfdInstance"] == "enable_pim_bfd_instance"
    # Use the parent's spelling, with a lowercase v. The parent translates it to the child's
    # uppercase spelling. These assertions prevent a capitalization "fix" from silently
    # breaking the binding.
    assert km["ipv6LinkLocal"] == "ipv6_link_local"
    assert "IPV6_LINK_LOCAL" not in km, "this is the child's spelling, not the parent's"
    # MACSEC: the parent uses the MACSEC_ prefix and translates to the child's unprefixed name.
    assert km["macsecKeyChainName"] == "macsec_key_chain_name"
    assert km["macsecFallbackKeyChainName"] == "macsec_fallback_key_chain_name"
    assert "KEY_CHAIN_NAME" not in km, "this is the child's spelling, without the MACSEC_ prefix"
    # 66 = 65 + ARP_TIMEOUT: one public key for three rows, shared across the three parents.
    # This is why bindings are keyed by (parent, nvpair), not by name.
    # 69 = 66 + the three PIM keys across eight rows.
    # 70 = 69 + IPv6_LINK_LOCAL, one key for three overlay rows.
    # 74 = 70 + the four MACSEC keys, all on int_routed_host.
    # 76 = 74 + two from batch 2: private_vlan_mapping and enable_vpc_peer_link. IPV4_ACL_IN
    # was already in the int_routed_host keymap: three rows, two new keys.
    assert km["privateVlanMapping"] == "private_vlan_mapping"
    assert km["ENABLE_VPC_PEER_LINK"] == "enable_vpc_peer_link"
    # 74 = 76 - ospfBfd and ospfPassiveInterface, which SMU 017 replaced by the already-mapped ospfBfdMode and ospfPassiveMode.
    # 77 = 74 + CDP_ENABLE, evpnMultisiteDciTracking and loggingEventPortLinkStatus (slice 0b_37); ospfRetransmitInterval
    # and pimBfdInstance were already mapped on other parents.
    assert km["CDP_ENABLE"] == "enable_cdp"
    # 78 = 77 + linkTransmitResetSkip (slice rs1, int_port_channel_trunk_host).
    assert km["linkTransmitResetSkip"] == "link_transmit_reset_skip"
    # 80 = 78 + ENABLE_QOS and QOS_POLICY (slice pl1, int_vpc_peer_link_po); the other two peer-link nvPairs were mapped.
    assert km["ENABLE_QOS"] == "enable_qos" and km["QOS_POLICY"] == "qos_policy"
    # 88 = 80 + ENABLE_STORM_CONTROL, STORM_CONTROL_ACTION and the six storm-control levels (slice ul1,
    # int_vpc_uplink_access); its four QoS and STP nvPairs were mapped.
    assert km["ENABLE_STORM_CONTROL"] == "enable_storm_control"
    assert km["STORM_CONTROL_BCAST_LEVEL_PPS"] == "storm_control_broadcast_level_pps"
    assert len(km) == 88


def test_all_registered_keys():
    assert gie_all_registered_keys() == {
        "flowcontrol_receive", "flowcontrol_send", "spanning_tree_port_type",
        "guard_mode", "disable_lldp_transmit", "disable_lldp_receive", "acl_filter",
        "disable_qos_stats", "disable_queuing_stats",
        "link_transmit_reset_skip",
        # The peer-link QoS keys, slice pl1 (native on the other Ethernet, port-channel and vPC profiles).
        "enable_qos", "qos_policy",
        # The ToR-uplink storm-control keys, slice ul1 (native on the access, trunk and dot1q-tunnel profiles).
        "enable_storm_control", "storm_control_action",
        "storm_control_broadcast_level_percent", "storm_control_multicast_level_percent",
        "storm_control_unicast_level_percent", "storm_control_broadcast_level_pps",
        "storm_control_multicast_level_pps", "storm_control_unicast_level_pps",
        "disable_bfd_echo", "ipv4_acl_in",
        # OSPF, slices 0b_18/0b_19/0b_20. SIXTEEN distinct names across the three overlay
        # parents plus int_loopback, written as one list: the lots share most of their names,
        # so a literal that repeats them per lot asserts less than it appears to. The sharing
        # is the design -- bindings are keyed by (parent, nvpair), not by name.
        "enable_ospf", "ospf_tag", "ospf_area_id", "ospf_cost", "ospf_mtu_ignore",
        "ospf_shutdown", "ospf_hello_interval", "ospf_dead_interval", "ospf_transmit_delay",
        "ospf_priority", "ospf_passive_mode", "ospf_network_type", "ospf_bfd_mode",
        # Only from the second lot (int_subif / int_vlan). ospf_bfd and ospf_passive_interface are input aliases since SMU 017.
        "ospf_retransmit_interval",
        # The authentication lot, shared by int_routed_host, int_subif and int_vlan.
        "enable_ospf_auth", "ospf_auth_key_id", "ospf_auth_key",
        "ospf_authentication_key_type", "ospf_authentication_key",
        # EIGRP, slice 0b_22. Thirteen fields, identical on int_routed_host, int_subif and
        # int_vlan -- measured against the bodies the controller runs, not the batch on disk.
        # EIGRP_PROCESS_TAG gates the other twelve, and the TEMPLATE refuses the tagless
        # case itself ("EIGRP process tag is required when EIGRP interface options are
        # enabled", int_routed_host:897). The engine transports and does not duplicate it.
        "eigrp_process_tag", "enable_eigrp_routing", "enable_eigrp_ipv6_routing",
        "eigrp_ipv4_passive", "eigrp_no_ipv4_passive", "eigrp_no_ipv6_passive",
        "enable_eigrp_shutdown", "enable_eigrp_bfd", "disable_eigrp_bfd",
        "eigrp_ipv4_distribute_list_prefix_list", "eigrp_ipv4_distribute_list_direction",
        "eigrp_ipv6_distribute_list_prefix_list", "eigrp_ipv6_distribute_list_direction",
        # int_loopback, slice 0b_23. Only ONE public key is new -- the other eighteen are names
        # this table already carries on other parents, which is the point of keying bindings by
        # (parent, nvpair) rather than by name.
        # HSRP on int_vlan, slice 0b_26. Three new public keys, and the only lot whose fields
        # sit on top of MODULE-NATIVE ones: enable_hsrp, hsrp_vip, hsrp_group, preempt and
        # hsrp_priority are already in the native SVI arg spec, so the engine adds only these.
        # The template enforces the whole dependency chain, including `lower cannot exceed
        # upper` -- a relationship between two fields that the registry cannot express.
        "hsrp_priority_forwarding_threshold_lower",
        "hsrp_priority_forwarding_threshold_upper",
        "hsrp_preempt_delay_minimum",
        # HSRP IPv6, slice 0b_27: two keys. HSRP_VIPv6 is the first template address field
        # in the table (ipV6Address -> string; NDFC validates the format).
        # IPv6/PREFIXv6 were removed: registering ipv6_addr made the guard reject it on
        # int_subif, where the native spec already supports it. See the slice.
        "hsrp_vipv6",
        "hsrp_groupv6",
        # Split redirects + ND suppress-RA, slice 0b_28: three public keys on each of the
        # three overlay parents. DISABLE_IP_REDIRECTS is native and stays out; registering
        # it would repeat the ipv6_addr defect because gie_guarded_keys() is not parent-scoped.
        "disable_ipv4_redirects",
        "disable_ipv6_redirects",
        "ipv6_nd_suppress_ra",
        # Dampening, slice 0b_6, corrected from child_pti to passthrough: seven keys on
        # int_routed_host only. Neither tested C9300v NX-OS image supports its CLI,
        # so these bindings have controller validation, not device validation.
        "enable_dampening", "dampening_half_life", "dampening_reuse", "dampening_suppress",
        "dampening_max_suppress", "dampening_restart", "dampening_restart_penalty",
        # ARP_TIMEOUT, slice 0b_3, registered: one public key on three
        # overlay parents; int_loopback does not declare it. One field, one child,
        # one CLI line, with no gate or dependencies. See phase41.
        "arp_timeout",
        # PIM, slice 0b_31: three public keys across eight rows, distributed unevenly:
        # sparse on four parents, dr_priority on three (loopbacks do not elect a DR),
        # and bfd_instance on int_routed_host only. See phase42.
        "enable_pim_sparse", "pim_dr_priority", "enable_pim_bfd_instance",
        # IPv6 link-local, slice 0b_32: one public key on three overlay parents,
        # excluding int_loopback. The parent nvPair is `IPv6_LINK_LOCAL`, with a lowercase
        # v; the parent translates it to the uppercase name expected by the child.
        "ipv6_link_local",
        # MACSEC, slice 0b_33: four public keys on int_routed_host, the only parent that
        # declares them. The enable flag and object names (keychain and policy references)
        # are not secrets, hence no_log false. See phase44.
        "enable_macsec_interface_policy", "macsec_key_chain_name", "macsec_policy_name",
        "macsec_fallback_key_chain_name",
        # Batch 2, slice 0b_34: three unrelated fields on two parents. int_vlan reuses
        # ipv4_acl_in from int_routed_host, demonstrating why bindings are keyed by
        # (parent, nvpair). The other two public keys are new.
        "private_vlan_mapping", "enable_vpc_peer_link",
        "ospf_advertise_subnet",
        # BFD, slice 0b_24 and the eight rows of 0b_4/0b_5 committed with their mechanism
        # corrected from child_pti to passthrough. Four public keys; disable_bfd_echo was
        # already here, from int_routed_host.
        "enable_bfd_interval", "bfd_tx_interval", "bfd_min_rx_interval", "bfd_multiplier",
        # SMU 017 first increment, slice 0b_37: three new public keys. enable_cdp is registered on
        # int_routed_host and native elsewhere (GIE_NATIVE_ELSEWHERE_KEYS).
        "enable_cdp", "enable_evpn_multisite_dci_tracking", "logging_event_port_link_status",
    }


def test_same_value_produces_the_same_payload():
    """The engine is deterministic: the same input always yields the same payload.

    This is NOT an idempotency test, and the earlier name and comment here claimed it was:
    "the comparator sees a stable native value, so a repeat run diffs to nothing new". That was
    wrong, and it is the reason a real defect survived offline. Comparing the engine against
    ITSELF is stable no matter what the engine emits -- including a native bool that the
    comparator could never match against the controller's "true".

    Idempotency is a property of want-vs-HAVE, so it can only be pinned by a test that carries a
    controller value on the other side. That test lives in test_binding_values.py
    (test_reapplying_the_same_boolean_is_idempotent), and it drives the real comparison.
    """
    for parent, pk, nvpair, value in NINE:
        first, err1 = gie_contribute_nvpairs(parent, {pk: value}, SUPPORTED, PATCH)
        second, err2 = gie_contribute_nvpairs(parent, {pk: value}, SUPPORTED, PATCH)
        assert err1 is None and err2 is None
        assert first == second == {nvpair: _wire(value)}


# ------------------------------------------------------------ baseline regression
def test_a15_flowcontrol_contract_is_unchanged():
    for parent in (ACCESS, TRUNK):
        b = resolve_binding(parent, "flowcontrol_receive")
        assert b["parent_nvpair"] == "flowcontrolReceive"
        assert b["type"] == "enum"
        assert tuple(b["valid_values"]) == ("on", "off")
        assert b["default_template"] == "off"
        assert b["mechanism"] == "passthrough"
        assert b["min_ndfc_version"] == SUPPORTED
        for value in ("on", "off"):
            add, err = gie_contribute_nvpairs(
                parent, {"flowcontrol_receive": value}, SUPPORTED, PATCH
            )
            assert err is None and add == {"flowcontrolReceive": value}
        add, err = gie_contribute_nvpairs(
            parent, {"flowcontrol_receive": "on"}, BELOW, PATCH
        )
        assert add is None and err, "FLOWCONTROL must still fail closed"


def test_ospf_md_is_still_absent_from_the_generic_eth_and_pc_specs():
    for parent in (TRUNK, ACCESS, PC_TRUNK, PC_ACCESS, PC_DOT1Q):
        spec = {}
        gie_extend_prof_spec(spec, parent, {"enable_ospf_auth_message_digest": True})
        assert spec == {}


# ------------------------------------------------------------------ runtime purity
def test_runtime_still_imports_only_the_packaged_table():
    import ast
    from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine

    for module in (gie_engine, gie_binding_table):
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                called = fn.id if isinstance(fn, ast.Name) else (
                    fn.attr if isinstance(fn, ast.Attribute) else None
                )
                assert called not in ("open", "read_text", "load", "safe_load"), (
                    f"{module.__name__} performs file I/O via {called!r}"
                )
            assert not (isinstance(node, ast.Name) and node.id == "__file__"), (
                f"{module.__name__} references __file__"
            )


# ====================================================================================================
# Formerly test_gie_boolean_wire_form.py
# nvPairs is a STRING-valued map. A boolean binding must be transported as its wire form.
#
# Measured on a live controller (NDFC 12.6.0.267, DISABLE_LLDP on both host eth
# parents). Stage p1 set the field and NDFC stored it. Stage p2 re-sent the IDENTICAL intent and
# the module reported changed=True with 2 API calls again -- the field never converges:
#
#     want (engine)  DISABLE_LLDP = True     <- native Python bool
#     have (NDFC)    DISABLE_LLDP = "true"   <- what the controller stores and returns
#     compare        "true" != True          -> diff on every single run
#
# The module's existing convention normalizes booleans at COMPARISON time, per key, through a
# hardcoded allowlist in dcnm_intf_compare_elements:
#
#     boolean_keys = ["ENABLE_ORPHAN_PORT", "DISABLE_LACP_SUSPEND", "ENABLE_LACP_VPC_CONV",
#                     "ENABLE_PFC", "ENABLE_MONITOR", "CDP_ENABLE", "ENABLE_QOS",
#                     "COPY_DESC", "ENABLE_STORM_CONTROL"]
#
# Adding DISABLE_LLDP to that list would fix the symptom and defeat the point: a generic engine
# whose every new boolean requires editing a per-nvPair allowlist is not generic. It is also not
# reachable from there -- dcnm_intf_compare_elements receives the nvPair name but NOT the parent
# template, so it cannot resolve a parent-scoped binding at all.
#
# The engine emits the wire form instead. Then both sides are strings and the pre-existing generic
# branch in dcnm_intf_compare_elements (isinstance(e, str) -> e.lower()) compares them correctly,
# with no change to that function and no allowlist to maintain.
#
# SCOPE: passthrough only.
#     passthrough -> written straight into nvPairs; transport is the whole job. 15 bindings today:
#                    13 string/enum (serialization is a no-op) and 2 boolean (the fix).
#     child_pti   -> the OSPF-MD domain on int_fabric_loopback_11_1. It has a dedicated normalizer
#                    (dcnm_intf_normalize_ospf_auth_message_digest) and its call site already
#                    stringifies explicitly. Left native so the golden payload snapshots that pin
#                    the pre-migration OSPF emission stay byte-identical.
#
# Run:
#     pytest tests/unit/modules/dcnm/dcnm_interface/test_binding_values.py
# ====================================================================================================
VERSION = "12.6.0.267"

_OMITTED = object()

# Derived from the table, NOT hand-listed. A boolean binding registered later is covered by
# these tests the day it lands, which is the point of a generic engine: the contract belongs to
# the mechanism, not to any one field. Hand-listing would silently leave the next one untested.
BOOL_PASSTHROUGH = sorted(
    (b["parent_template"], b["profile_key"], b["parent_nvpair"])
    for b in BINDING_TABLE
    if b["type"] == "boolean" and b["mechanism"] == "passthrough"
)
BOOL_IDS = ["%s::%s" % (p.replace("int_", ""), k) for p, k, nvpair in BOOL_PASSTHROUGH]

# The inventory above stays COMPLETE: it is what pins the boolean passthrough set, and an
# identity with no SMU counterpart is still registered, still boolean and still passthrough.
# The sweeps that expect a contribution to SUCCEED run on the supported side; the other side
# has its own contract, asserted in test_an_unsupported_boolean_refuses_before_emitting.
_UNSUPPORTED = {
    (b["parent_template"], b["profile_key"])
    for b in BINDING_TABLE
    if b.get("smu_unsupported")
}
BOOL_SUPPORTED = [t for t in BOOL_PASSTHROUGH if (t[0], t[1]) not in _UNSUPPORTED]
BOOL_SUPPORTED_IDS = ["%s::%s" % (p.replace("int_", ""), k) for p, k, nvpair in BOOL_SUPPORTED]
BOOL_UNSUPPORTED = [t for t in BOOL_PASSTHROUGH if (t[0], t[1]) in _UNSUPPORTED]
BOOL_UNSUPPORTED_IDS = ["%s::%s" % (p.replace("int_", ""), k) for p, k, nvpair in BOOL_UNSUPPORTED]
assert BOOL_SUPPORTED and BOOL_UNSUPPORTED, "the partition must cover both sides"

# The three PVLAN parents register booleans too, but they never reach the generic comparator these sweeps drive
# (dcnm_intf_compare_want_and_have on a bare payload): their builders and dcnm_intf_pvlan_*_compare reconcile the FULL PVLAN set
# (lists, members, peers) and call the same engine functions for the companions. Driving them here would test a route the module
# never takes. The same wire-form / idempotency / merged-preservation / withdrawal contract is asserted for them through the real
# main() in test_pvlan_companions.py. They stay in BOOL_PASSTHROUGH (the inventory) and in the engine-only sweep.
PVLAN_ROUTED_PARENTS = frozenset(("int_pvlan_host", "int_port_channel_pvlan_host", "int_vpc_pvlan_host"))
# The peer-link parent reaches the generic comparator only after dcnm_intf_peer_link_admit has read the pair, the intent and
# the detail row, which a bare payload does not carry. Its two booleans (enable_qos, disable_qos_stats) are asserted through
# the real main() in test_mode_peer_link.py.
PEER_LINK_ROUTED_PARENTS = frozenset(("int_vpc_peer_link_po",))
# The same holds for the ToR-uplink parent (dcnm_intf_uplink_admit); its three booleans (enable_qos, disable_qos_stats,
# enable_storm_control) are asserted through the real main() in test_mode_uplink_access.py.
UPLINK_ROUTED_PARENTS = frozenset(("int_vpc_uplink_access",))
BOOL_GENERIC = [t for t in BOOL_SUPPORTED
                if t[0] not in PVLAN_ROUTED_PARENTS | PEER_LINK_ROUTED_PARENTS | UPLINK_ROUTED_PARENTS]
BOOL_GENERIC_IDS = ["%s::%s" % (p.replace("int_", ""), k) for p, k, nvpair in BOOL_GENERIC]
# IQ1 adds int_vpc_pvlan_host::disable_qos_stats: nine. Slice pl1 adds the two peer-link booleans: eleven. Slice ul1
# adds the three uplink booleans: fourteen.
assert len(BOOL_SUPPORTED) - len(BOOL_GENERIC) == 14, (
    "the nine PVLAN companion, two peer-link and three uplink booleans take their own route")


def test_the_derived_set_is_not_empty_and_covers_the_known_fields():
    """Guard the guard: an empty parametrize list turns every test below into a no-op.

    Also pins the fields known to be boolean passthrough today, so a binding silently changing
    type or mechanism shows up here instead of quietly leaving this file with nothing to run.
    """
    assert BOOL_PASSTHROUGH, "no boolean passthrough bindings -- the tests below run on nothing"
    assert {k for parent, k, nvpair in BOOL_PASSTHROUGH} == {
        "disable_lldp_transmit", "disable_lldp_receive", "disable_qos_stats", "disable_queuing_stats", "disable_bfd_echo",
        # SMU 017 first increment, slice 0b_37. enable_cdp is the first boolean whose reset is "true".
        "enable_cdp", "enable_evpn_multisite_dci_tracking", "logging_event_port_link_status",
        # The boolean OSPF names, once. enable_ospf reaches this set from both lots; listing it
        # twice made the literal look like it pinned more than it does.
        "enable_ospf", "ospf_mtu_ignore", "ospf_shutdown",
        # ospf_bfd and ospf_passive_interface are input aliases since SMU 017, not registered keys.
        "enable_ospf_auth",
        # Split redirects + ND suppress-RA, slice 0b_28, on all three overlay parents.
        # The fourth field, disable_ip_redirects, is native and must stay out of the registry;
        # registering it would make the engine claim a name already owned by the arg spec.
        "disable_ipv4_redirects", "disable_ipv6_redirects", "ipv6_nd_suppress_ra",
        # Dampening, slice 0b_6: two of its seven fields are boolean. The other five are
        # integers covered by the HAVE representation tests, not this list.
        "enable_dampening", "dampening_restart",
        # PIM, slice 0b_31: two of its three keys are boolean. The integer pim_dr_priority
        # belongs in the HAVE representation tests, not this list.
        "enable_pim_sparse", "enable_pim_bfd_instance",
        # MACSEC, slice 0b_33: only the enable flag is boolean. The other three fields
        # are names (strings), so they do not appear here.
        "enable_macsec_interface_policy",
        # Batch 2, slice 0b_34: its only boolean. ipv4_acl_in and
        # private_vlan_mapping are strings.
        "enable_vpc_peer_link",
        # Trunk port-channel reset-skip default, slice rs1 (int_port_channel_trunk_host).
        "link_transmit_reset_skip",
        # Peer-link QoS enable, slice pl1 (int_vpc_peer_link_po); disable_qos_stats is already listed.
        "enable_qos",
        # ToR-uplink storm-control enable, slice ul1 (int_vpc_uplink_access); its QoS booleans are already listed.
        "enable_storm_control",
        # EIGRP, slice 0b_22 -- eight distinct keys, each on all three overlay parents.
        "enable_eigrp_routing", "enable_eigrp_ipv6_routing", "enable_eigrp_shutdown",
        "enable_eigrp_bfd", "disable_eigrp_bfd",
        "eigrp_ipv4_passive", "eigrp_no_ipv4_passive", "eigrp_no_ipv6_passive",
        # int_loopback, slice 0b_23. Five of its six booleans are names already here; the sixth,
        # ospf_advertise_subnet, exists on no other parent -- advertising a loopback's subnet is
        # a loopback concept.
        "ospf_advertise_subnet",
        # BFD: enable_bfd_interval is the gate. disable_bfd_echo gains a second parent
        # (int_vlan) for a key int_routed_host already carried, so int_vlan goes 12 -> 13.
        "enable_bfd_interval",
        # There is no eigrp_ipv6_passive: IPv4 declares both the passive and the no-passive
        # field, IPv6 only the no-passive one. The children match -- an ipv6-passive child
        # does not exist either. The asymmetry is the template's.
    }
    # 80 = the per-parent counts below, which are what the table actually holds. Measured
    # against BINDING_TABLE when slice 0b_22 landed, not carried forward by arithmetic:
    #
    #     int_access_host                     4      int_routed_host    17
    #     int_trunk_host                      4      int_subif          14
    #     int_port_channel_access_host        4      int_vlan           12
    #     int_port_channel_trunk_host         4
    #     int_port_channel_dot1q_tunnel_host  4      int_vpc_access_host  4
    #                                                int_vpc_trunk_host   4
    #                                                int_loopback         6
    #
    # The three overlay parents grew by 8 each: the eleven EIGRP booleans are eight distinct
    # keys plus the three that repeat per parent. int_routed_host 9 -> 17, int_subif 6 -> 14,
    # int_vlan 4 -> 12.
    #
    # This used to be a derivation -- "3 x 8 = 24, plus disable_bfd_echo, plus enable_ospf..."
    # -- and the derivation had silently drifted to 28 while the assertion said 44. Nobody
    # noticed, because only the number is executed and only the prose was wrong. A breakdown
    # that can be checked against the table beats a chain of arithmetic that cannot.
    #
    # int_routed_host emits no CLI of its own for any of them -- every value is handed to a
    # child template. Same reasoning as the vPC parents below: that does not exempt it from the
    # wire form, because the value lands in the routed parent's own nvPairs first.
    #
    # The vPC parents emit no CLI of their own -- they hand the value to a child template. They
    # are still passthrough and therefore still need the wire form: the value lands in the vPC
    # parent's own nvPairs first, and nvPairs is a string-valued map. A native bool left there
    # would reproduce exactly the non-convergence this file exists to prevent.
    # 96 = 87 + the NINE of slice 0b_28, all boolean: three fields on each of the three
    # overlay parents. Slice 0b_27 added none here -- hsrp_groupv6 is an integer and
    # hsrp_vipv6 a string.
    # 98 = 96 + the two dampening booleans. Its other five fields are integers.
    # 103 = 98 + the five PIM booleans: enable_pim_sparse on four parents and
    # enable_pim_bfd_instance on int_routed_host. The integer pim_dr_priority is excluded.
    # 104 = 103 + enable_macsec_interface_policy, the only MACSEC boolean; the other three
    # fields are names (strings).
    # 105 = 104 + enable_vpc_peer_link, the only boolean in batch 2.
    # 109 = 105 + the four int_vpc_dot1q_tunnel booleans (disable_lldp_transmit,
    # disable_lldp_receive, disable_qos_stats, disable_queuing_stats).
    # 117 = 109 + the eight PVLAN companion booleans: int_pvlan_host 2 (lldp x2),
    # int_port_channel_pvlan_host 3 and int_vpc_pvlan_host 3 (lldp x2 + queuingStats each). spanning_tree_port_type (enum)
    # and acl_filter (string) are the other three C1 rows. IQ1 registers the vPC PVLAN qosStatsSuppressed (disable_qos_stats,
    # boolean): 117 + 1.
    # 115 = 118 - the three OSPF booleans (ospf_bfd on int_loopback and int_subif, ospf_passive_interface on int_subif)
    # that SMU 017 turned into the enums ospfBfdMode and ospfPassiveMode.
    # 119 = 115 + four SMU 017 booleans (slice 0b_37): enable_cdp and enable_evpn_multisite_dci_tracking on
    # int_routed_host, logging_event_port_link_status on int_access_host, enable_pim_bfd_instance on int_subif.
    # 121 = 119 + enable_eigrp_ipv6_routing on int_loopback (slice 0b_38) + enable_pim_bfd_instance on int_l3_port_channel
    # (slice 0b_39).
    # 125 = 121 + ospf, ospfAuthentication, ospfMtuIgnore and ospfShutdown on int_l3_port_channel (slice 0b_40).
    # 126 = 125 + link_transmit_reset_skip on int_port_channel_trunk_host (slice rs1).
    # 128 = 126 + enable_qos and disable_qos_stats on int_vpc_peer_link_po (slice pl1).
    # 131 = 128 + enable_qos, disable_qos_stats and enable_storm_control on int_vpc_uplink_access (slice ul1).
    # 132 = 131 + enable_pim_sparse on int_l3_port_channel (slice 0b_41).
    assert len(BOOL_PASSTHROUGH) == 132


# ------------------------------------------------------- what the engine emits --

@pytest.mark.parametrize("parent,profile_key,nvpair", BOOL_SUPPORTED, ids=BOOL_SUPPORTED_IDS)
@pytest.mark.parametrize(
    "value,wire", [(True, "true"), (False, "false")], ids=["true", "false"]
)
def test_boolean_passthrough_is_emitted_as_its_wire_form(
    parent, profile_key, nvpair, value, wire
):
    """The exact defect: a native bool in nvPairs never matches the controller's string."""
    add, err = gie_contribute_nvpairs(parent, {profile_key: value}, VERSION, PATCH)
    assert err is None
    assert add[nvpair] == wire
    assert isinstance(add[nvpair], str)
    # Not the Python repr: NDFC's template DSL tests `== "true"`, lowercase.
    assert add[nvpair] != str(value)


@pytest.mark.parametrize("parent", [TRUNK, ACCESS])
@pytest.mark.parametrize(
    "key,value",
    [
        ("flowcontrol_receive", "on"),
        ("flowcontrol_send", "off"),
        ("spanning_tree_port_type", "network"),
        ("acl_filter", "MY-FILTER"),
    ],
)
def test_string_and_enum_passthrough_are_untouched(parent, key, value):
    """The other 13 passthrough bindings must come through byte-identical.

    Serializing a str is a no-op, but that has to be proven rather than assumed -- a change
    that silently lowercased ACL_FILTER would corrupt a case-sensitive ACL name.
    """
    add, err = gie_contribute_nvpairs(parent, {key: value}, VERSION, PATCH)
    assert err is None
    assert list(add.values()) == [value]
    assert add[list(add)[0]] is value or add[list(add)[0]] == value


def test_acl_filter_case_is_preserved_exactly():
    """Named explicitly because lowercasing is the plausible way to get this wrong."""
    add, err = gie_contribute_nvpairs(TRUNK, {"acl_filter": "MiXeD-Case_ACL"}, VERSION, PATCH)
    assert err is None
    assert add["aclFilter"] == "MiXeD-Case_ACL"


def test_omitted_boolean_still_contributes_nothing():
    """Serialization must not resurrect the explicit-only contract."""
    add, err = gie_contribute_nvpairs(TRUNK, {"description": "x"}, VERSION, PATCH)
    assert err is None
    assert "lldpTransmit" not in add


# ------------------------------------------- what the operator actually observes --
#
# The tests above pin the engine in isolation, so they would all still pass if the comparison
# path disagreed. These drive dcnm_intf_compare_want_and_have -- the code that decides
# changed=True -- with the exact want/have pair measured on the lab.
#
# CRITICAL: the WANT side is built BY THE ENGINE, from the playbook-level value, exactly as
# dcnm_intf_get_eth_payload does. Hand-writing the wire string into want instead would make
# these pass both before and after the fix -- a test that cannot fail. The want must carry
# whatever the engine currently produces, so the engine's behaviour is what is under test.


def _engine_nvpairs(parent, profile_key, value):
    """The nvPairs the module would build for this profile, via the real engine call."""
    add, err = gie_contribute_nvpairs(parent, {profile_key: value}, VERSION, PATCH)
    assert err is None, err
    return add


def _payload(parent, profile_key, nvpair, value=_OMITTED, description="same",
             engine_built=False):
    nvpairs = {"DESC": description}
    if value is not _OMITTED:
        if engine_built:
            nvpairs.update(_engine_nvpairs(parent, profile_key, value))
        else:
            nvpairs[nvpair] = value
    return {
        "deploy": False,
        "policy": parent,
        "interfaceType": "INTERFACE_ETHERNET",
        "interfaces": [{
            "serialNumber": "SN1",
            "interfaceType": "INTERFACE_ETHERNET",
            "ifName": "Ethernet1/4",
            "fabricName": "FAB1",
            "nvPairs": nvpairs,
        }],
    }


def _compare_obj(state, parent, profile_key, nvpair, want=_OMITTED, have=_OMITTED,
                 want_description="same", have_description="same"):
    """`want` is the PLAYBOOK value (a native bool); the engine turns it into nvPairs.
    `have` is the raw string the controller returns.
    """
    module = mock.Mock()
    module.params = {"fabric": "FAB1", "config": [], "state": state,
                     "patch_version": PATCH}
    module.check_mode = False
    with mock.patch.object(
        dcnm_interface, "dcnm_version_supported", return_value=(12, "12.6.0.267")
    ):
        obj = dcnm_interface.DcnmIntf(module)
    obj.want = [_payload(parent, profile_key, nvpair, want, want_description,
                         engine_built=True)]
    have_payload = _payload(parent, profile_key, nvpair, have, have_description)
    have_payload.pop("deploy")
    obj.have = [have_payload]
    pb = {
        "ifname": "Ethernet1/4",
        "sno": "SN1",
        "fabric": "FAB1",
        "policy": parent,
        "description": want_description,
    }
    if want is not _OMITTED:
        pb[profile_key] = want
    obj.pb_input = [pb]
    return obj


@pytest.mark.parametrize("parent,profile_key,nvpair", BOOL_GENERIC, ids=BOOL_GENERIC_IDS)
@pytest.mark.parametrize(
    "playbook_value,controller_value",
    [(True, "true"), (False, "false")],
    ids=["true", "false"],
)
def test_reapplying_the_same_boolean_is_idempotent(
    parent, profile_key, nvpair, playbook_value, controller_value
):
    """THE regression test. Reproduces live stage p2 exactly.

    The playbook says the field is true, the engine builds want, and the controller already
    holds "true". Before the fix the engine put a native bool in want, "true" != True compared
    unequal, and the module re-pushed on every run -- changed=True forever, with a deploy each
    time and a config-save behind it.
    """
    obj = _compare_obj("merged", parent, profile_key, nvpair,
                       playbook_value, controller_value)
    obj.dcnm_intf_compare_want_and_have("merged")
    assert obj.diff_replace == []
    assert obj.changed_dict[0]["merged"] == []


@pytest.mark.parametrize("parent,profile_key,nvpair", BOOL_GENERIC, ids=BOOL_GENERIC_IDS)
@pytest.mark.parametrize("state", ["merged", "replaced", "overridden"])
def test_a_real_boolean_change_is_still_detected(parent, profile_key, nvpair, state):
    """The opposite direction: the fix must not make the field unwritable.

    A test that only pins idempotency would also pass if the field were dropped entirely.
    """
    obj = _compare_obj(state, parent, profile_key, nvpair, True, "false")
    obj.dcnm_intf_compare_want_and_have(state)
    assert len(obj.diff_replace) == 1
    sent = obj.diff_replace[0]["interfaces"][0]["nvPairs"]
    assert sent[nvpair] == "true"
    reported = obj.changed_dict[0][state][0]["interfaces"][0]["nvPairs"]
    assert reported == {nvpair: "true"}


@pytest.mark.parametrize("parent,profile_key,nvpair", BOOL_GENERIC, ids=BOOL_GENERIC_IDS)
@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_omitted_boolean_under_replaced_follows_the_withdrawal_contract(
    parent, profile_key, nvpair, state
):
    """Omission under `replaced` / retained `overridden` is a WITHDRAWAL request.

    THIS EXPECTATION WAS DELIBERATELY CHANGED, and the previous one is stated here rather
    than deleted. It read:

        "Omission is not intent: an unrelated edit must not reset the controller's value.
         This matters more for the QoS-stats pair than for anything registered before it.
         Both are the ' no-stats' suffix of a service-policy line, so a value silently
         reset to false does not remove a line -- it changes one in place, which is
         exactly the kind of drift nobody notices until statistics quietly come back."

        assert sent[nvpair] == "true"
        assert reported == {"DESC": "new"}

    That was the F1 behaviour PR #725 set out to fix: a field could be set and never
    unset, because omission was read as "no opinion" even while `replaced` claims to
    describe the whole interface. The concern in that docstring is real, which is why the
    replacement is NOT "reset everything on omission": only a row carrying a MEASURED
    `reset_wire` is withdrawn, and a row without one stops the run instead of guessing.

    The `merged` control is untouched and still asserts preservation -- see
    `test_omitted_boolean_is_preserved_under_merged` below. That is the state to use when
    omission really does mean "leave it alone".
    """
    binding = bool_wire_resolve_binding(parent, profile_key)
    reset = binding.get("reset_wire")
    # The controller holds the value OPPOSITE to the reset, so the withdrawal is a change. For every
    # row before slice 0b_37 that is "true"; CDP_ENABLE resets to "true", so it holds "false".
    held = "false" if reset == "true" else "true"
    obj = _compare_obj(
        state, parent, profile_key, nvpair, _OMITTED, held,
        want_description="new", have_description="old",
    )
    obj.dcnm_intf_compare_want_and_have(state)
    sent = obj.diff_replace[0]["interfaces"][0]["nvPairs"]
    reported = obj.changed_dict[0][state][0]["interfaces"][0]["nvPairs"]
    if reset is None:
        # No verified reset for this binding and parent. Transport preservation still
        # applies at this layer; the invocation-wide refusal lives in main() and is
        # covered by the W2 acceptance suite, not here.
        assert sent[nvpair] == held
        assert reported == {"DESC": "new"}
    else:
        assert sent[nvpair] == reset, (
            "the withdrawal did not reach the request; omission must transmit the "
            "registered reset for a row that declares one")
        assert reported == {"DESC": "new", nvpair: reset}, (
            "the withdrawal was sent but not reported -- a change the operator cannot see "
            "in the diff is the defect this contract exists to remove")


@pytest.mark.parametrize("parent,profile_key,nvpair", BOOL_GENERIC, ids=BOOL_GENERIC_IDS)
def test_omitted_boolean_is_preserved_under_merged(parent, profile_key, nvpair):
    """The preserved historical control, now stated as its own test.

    `merged` has no withdrawal contract. Omission there means exactly what the previous
    expectation said it meant everywhere, and nothing in the withdrawal work may change it.
    """
    obj = _compare_obj(
        "merged", parent, profile_key, nvpair, _OMITTED, "true",
        want_description="new", have_description="old",
    )
    obj.dcnm_intf_compare_want_and_have("merged")
    # An EXISTING interface lands in diff_replace whatever the state -- merging into one
    # is still a modify. The surrounding tests read the same list for merged.
    sent = obj.diff_replace[0]["interfaces"][0]["nvPairs"]
    assert sent[nvpair] == "true", "merged must never withdraw an omitted value"
    reported = obj.changed_dict[0]["merged"][0]["interfaces"][0]["nvPairs"]
    assert reported == {"DESC": "new"}, (
        "merged reported a withdrawal it must not perform: %s" % reported)


# ---- HAVE encoding: "" for a boolean the template never defaulted --------------------
#
# Measured on NDFC 12.6.0.267 /, GET of the endpoint that feeds HAVE
# on an int_routed_host interface:
#
#     DISABLE_IPV4_REDIRECTS  ""        template declares no defaultValue
#     IPV6_ND_SUPPRESS_RA     "false"   template declares defaultValue=false
#
# Both are boolean bindings on the same parent and the same interface, so the difference is
# the template's default, not the interface. Before the exemption, registering the first one
# made every operation on that parent abort while reading HAVE -- including operations that
# never mentioned redirects.
def test_have_accepts_empty_string_for_a_boolean_and_returns_it_verbatim():
    out = gie_validate_binding_value(
        "int_routed_host", "disable_ipv4_redirects", "", value_source="have"
    )
    assert out == "", "the carry-forward must round-trip the controller's own encoding"


def test_have_still_rejects_any_other_string_for_a_boolean():
    """The exemption is three values wide, not 'any string'."""
    for bogus in ("yes", "0", "False", "null"):
        with pytest.raises(Exception):
            gie_validate_binding_value(
                "int_routed_host", "disable_ipv4_redirects", bogus, value_source="have"
            )


def test_an_empty_string_is_not_accepted_as_operator_input_for_a_boolean():
    """HAVE-only. An operator writing "" is not saying anything the module can act on."""
    with pytest.raises(Exception):
        gie_validate_binding_value(
            "int_routed_host", "disable_ipv4_redirects", "", value_source="explicit"
        )


# =====================================================================================
# the other half of the partition
# =====================================================================================
@pytest.mark.parametrize(
    "parent,profile_key,nvpair", BOOL_UNSUPPORTED, ids=BOOL_UNSUPPORTED_IDS
)
@pytest.mark.parametrize("value", [True, False])
def test_an_unsupported_boolean_refuses_before_emitting(parent, profile_key, nvpair, value):
    """A boolean identity the installed SMU build does not declare refuses the contribution
    for BOTH values and emits nothing -- neither the SMU name nor the pre-SMU one."""
    add, err = gie_contribute_nvpairs(parent, {profile_key: value}, VERSION, PATCH)
    assert add is None, "{0}::{1} produced a payload".format(parent, profile_key)
    assert err and "not supported by the interface templates installed" in err, err
    assert nvpair not in (add or {})


# ====================================================================================================
# Formerly test_gie_clear_string_binding.py
# A plain-string binding must be clearable with the empty string.
#
# ``ACL_FILTER`` was settable and never clearable. The registry copies ``min_length: 1`` from
# the template's ``metaProperties``, and the validator applied it to explicit input, so ``""``
# was rejected before the module sent anything. There was no other way out either: a re-deploy
# does not clear the field because NaC does not model it, so ``vxlan.yaml`` walks past the value
# and it survives. The field was one-way.
#
# The controller does not agree with that restriction. Measured on NDFC 12.6.0.267: POSTing
# ``ACL_FILTER: ""`` for ``port-channel31`` to ``/interface/modify`` returned 207 SUCCESS, the
# controller stored ``""``, and after deploy ``ip port access-group`` was gone from the device
# while the untouched ``port-channel32`` kept its own. ``""`` is also the exact encoding NDFC
# returns for "no ACL configured" -- the same value its own template claims is too short.
#
# Evidence: an empty-ACL probe on NDFC 12.6.0.267 (raw capture kept outside the repository).
#
# Two things are deliberately NOT relaxed, and are asserted here so a future edit cannot widen
# the hole by accident:
#
#   * an ENUM still rejects ``""``. For an enum the "off" state is a named choice
#     (``GUARD_MODE`` ``"no"``), so an empty enum is a typo, not an intent to clear.
#   * ``max_length`` still applies. Only the lower bound has a documented meaning as "unset".
#
# Offline: no controller and no device.
# ====================================================================================================
# Every registered plain-string binding, i.e. the ones an operator must be able to clear.
STRING_BINDINGS = [
    ("int_access_host", "acl_filter"),
    ("int_trunk_host", "acl_filter"),
    ("int_port_channel_access_host", "acl_filter"),
    ("int_port_channel_trunk_host", "acl_filter"),
    ("int_port_channel_dot1q_tunnel_host", "acl_filter"),
    ("int_vpc_access_host", "acl_filter"),
    ("int_vpc_trunk_host", "acl_filter"),
]


@pytest.mark.parametrize("parent,key", STRING_BINDINGS)
def test_explicit_empty_string_clears_a_plain_string_binding(parent, key):
    """The operator writes "" to remove the value. This is the fix."""
    assert gie_validate_binding_value(parent, key, "", value_source="explicit") == ""


@pytest.mark.parametrize("parent,key", STRING_BINDINGS)
def test_controller_empty_string_still_round_trips(parent, key):
    """Unchanged behaviour: the carry-forward reads "" back from HAVE."""
    assert gie_validate_binding_value(parent, key, "", value_source="have") == ""


@pytest.mark.parametrize("parent,key", STRING_BINDINGS)
def test_the_binding_really_carries_a_min_length(parent, key):
    """Guard the guard.

    These cases only mean something while the registry still declares ``min_length``. If a
    future regeneration dropped it, the tests above would pass for the wrong reason -- not
    because the exemption works, but because there was nothing left to exempt.
    """
    binding = resolve_binding(parent, key)
    assert binding is not None, "{0}::{1} is not registered".format(parent, key)
    assert binding.get("min_length") == 1, (
        "{0}::{1} no longer declares min_length 1, so the empty-string cases above no "
        "longer prove the exemption is what lets them through".format(parent, key)
    )


def test_an_enum_still_rejects_the_empty_string():
    """Scope of the exemption: enums fail closed.

    ``GUARD_MODE`` expresses "off" as the named choice ``"no"``. An empty value there is a
    mistake, and letting it through would send a value the template never declared.
    """
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(
            "int_trunk_host", "guard_mode", "", value_source="explicit"
        )


def test_max_length_still_applies_to_a_string_binding():
    """Only the lower bound means "unset"; the upper bound is a real constraint."""
    binding = resolve_binding("int_access_host", "acl_filter")
    too_long = "x" * (binding["max_length"] + 1)
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(
            "int_access_host", "acl_filter", too_long, value_source="explicit"
        )


def test_a_short_but_nonempty_string_is_still_accepted():
    """The exemption is for "" exactly, not for "anything below min_length"."""
    assert (
        gie_validate_binding_value(
            "int_access_host", "acl_filter", "A", value_source="explicit"
        )
        == "A"
    )


# ====================================================================================================
# Formerly test_gie_string_compare_f1.py
# F1: a case-only change of a registered string whose case is part of its value is sent.
#
# Review finding F1: the legacy scalar comparison lower-cased both sides, so a
# case-only change of an OSPF key or an ACL name compared equal and was never sent -- in merged,
# replaced and overridden alike. The registry now carries, per (parent template, nvPair), how a
# string binding compares (`string_compare`): only 'exact' bindings stop lower-casing; booleans,
# enums, IPv6 text and the bindings whose case semantics are not established keep the legacy rule.
#
# Every case drives the real main() through helpers/binding_harness (mocks only at inventory,
# transport and sleep). Keys and names are synthetic.
# ====================================================================================================
STATES = ("merged", "replaced", "overridden")

# id: (parent, profile key, nvPair, context, HAVE value, case-only request, different request)
EXACT = {
    "routed-ospf_auth_key": (h.ROUTED, "ospf_auth_key", "OSPF_AUTH_KEY", h.AUTH_MD,
                             "SYNTHETIC-Key-A", "synthetic-key-a", "SYNTHETIC-Key-B"),
    "routed-ospf_authentication_key": (h.ROUTED, "ospf_authentication_key", "ospfAuthenticationKey",
                                       dict(h.OSPF_CTX, ospf_authentication_key_type="3"),
                                       "SYNTHETIC-Md5-A", "synthetic-md5-a", "SYNTHETIC-Md5-B"),
    "trunk-acl_filter": (h.TRUNK, "acl_filter", "aclFilter", {}, "SYNTHETIC-ACL", "synthetic-acl", "SYNTHETIC-ACL-B"),
    "svi-ipv4_acl_in": (h.SVI, "ipv4_acl_in", "ipv4AclIn", {}, "SYNTHETIC-L3-ACL", "synthetic-l3-acl", "SYNTHETIC-L3-ACL-B"),
    "subif-eigrp_ipv4_prefix_list": (h.SUBIF, "eigrp_ipv4_distribute_list_prefix_list", "eigrpIpv4DistributeListPrefixList",
                                     h.EIGRP_CTX, "SYNTHETIC-PL4", "synthetic-pl4", "SYNTHETIC-PL4-B"),
}


def have_of(case):
    parent, key, _nv, ctx, have_value, _c, _d = case
    return h.build_have(parent, key, have_value, **ctx)


def want_of(case, value):
    parent, key, _nv, ctx, _h, _c, _d = case
    prof = h.base_for(parent, **ctx)
    prof[key] = value
    return [h.cfg_for(parent, prof)]


def sent_values(calls, nvpair):
    return [nv[nvpair] for nv in h.request_nvpairs(calls) if nvpair in nv]


# ------------------------------------------------------------------ the registry decision itself
def test_every_registered_string_binding_declares_a_comparison_category():
    strings = [b for b in table.BINDING_TABLE if b["type"] == "string"]
    # 51 = 45 + the two int_loopback EIGRP prefix lists of slice 0b_38 + ospfTag, OSPF_AREA_ID, OSPF_AUTH_KEY and
    # ospfAuthenticationKey on int_l3_port_channel (slice 0b_40). 52 = 51 + QOS_POLICY on int_vpc_peer_link_po (slice pl1).
    # 56 = 52 + QOS_POLICY and the three storm-control percent levels on int_vpc_uplink_access (slice ul1).
    assert len(strings) == 56
    assert {b["string_compare"] for b in strings} == {"exact", "casefold", "case_irrelevant", "unverified"}
    assert not [b for b in table.BINDING_TABLE if b["type"] != "string" and "string_compare" in b]


@pytest.mark.parametrize(
    "nvpair, category",
    [
        ("OSPF_AUTH_KEY", "exact"), ("ospfAuthenticationKey", "exact"), ("aclFilter", "exact"), ("ipv4AclIn", "exact"),
        ("eigrpIpv4DistributeListPrefixList", "exact"), ("eigrpIpv6DistributeListPrefixList", "exact"),
        ("macsecKeyChainName", "exact"), ("macsecFallbackKeyChainName", "exact"), ("macsecPolicyName", "exact"),
        ("ipv6LinkLocal", "casefold"), ("HSRP_VIPv6", "casefold"),
        ("OSPF_AREA_ID", "case_irrelevant"), ("privateVlanMapping", "case_irrelevant"),
        ("ospfTag", "unverified"), ("eigrpProcessTag", "unverified"),
    ],
)
def test_each_string_nvpair_has_one_category_on_every_parent(nvpair, category):
    rows = [b for b in table.BINDING_TABLE if b["parent_nvpair"] == nvpair]
    assert rows and {b["string_compare"] for b in rows} == {category}
    for b in rows:
        assert table.string_compare(b["parent_template"], nvpair) == category


def test_lookup_is_qualified_by_parent_and_answers_none_outside_the_registry():
    assert table.string_compare(h.TRUNK, "aclFilter") == "exact"
    assert table.string_compare(h.ROUTED, "aclFilter") is None      # not registered on that parent
    assert table.string_compare(h.TRUNK, "lldpReceive") is None     # registered, not a string
    assert table.string_compare(h.TRUNK, "DESC") is None            # legacy key


# ------------------------------------------------------------------ the finding, fixed
@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("cid", sorted(EXACT))
def test_case_only_change_is_sent_with_the_requested_value(cid, state):
    case = EXACT[cid]
    result, calls = h.run_configs(want_of(case, case[5]), state, have=have_of(case))
    sc = h.split_calls(calls)
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is True and len(sc["updates"]) == 1
    assert sent_values(calls, case[2]) == [case[5]]


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("cid", sorted(EXACT))
def test_exact_repeat_after_the_updated_have_is_a_noop(cid, state):
    case = EXACT[cid]
    _r1, calls1 = h.run_configs(want_of(case, case[5]), state, have=have_of(case))
    have2 = h._payload_as_have(calls1)          # HAVE = what the first run wrote
    assert have2[0]["interfaces"][0]["nvPairs"][case[2]] == case[5]
    result, calls = h.run_configs(want_of(case, case[5]), state, have=have2)
    assert not result.get("failed") and result["changed"] is False and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("cid", sorted(EXACT))
def test_identical_value_is_a_noop(cid, state):
    case = EXACT[cid]
    result, calls = h.run_configs(want_of(case, case[4]), state, have=have_of(case))
    assert not result.get("failed") and result["changed"] is False and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("cid", ["routed-ospf_auth_key", "trunk-acl_filter"])
def test_genuinely_different_value_still_updates(cid, state):
    case = EXACT[cid]
    result, calls = h.run_configs(want_of(case, case[6]), state, have=have_of(case))
    assert not result.get("failed") and len(h.split_calls(calls)["updates"]) == 1
    assert sent_values(calls, case[2]) == [case[6]]


# ------------------------------------------------------------------ controls: legacy normalization survives
@pytest.mark.parametrize("state", STATES)
def test_ipv6_text_case_only_difference_stays_a_noop(state):
    """casefold: IPv6 hex digits are case-insensitive; the HAVE returns them upper-cased."""
    have = h.build_have(h.ROUTED, "ipv6_link_local", "fe80::164:a1")
    have[0]["interfaces"][0]["nvPairs"]["ipv6LinkLocal"] = "FE80::164:A1"
    result, calls = h.run_configs(want_of((h.ROUTED, "ipv6_link_local", "ipv6LinkLocal", {}, "", "", ""), "fe80::164:a1"),
                                  state, have=have)
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("state", STATES)
def test_boolean_wire_in_another_case_stays_a_noop(state):
    have = h.build_have(h.TRUNK, "disable_lldp_receive", True)
    have[0]["interfaces"][0]["nvPairs"]["lldpReceive"] = "True"
    result, calls = h.run_configs([h.cfg_for(h.TRUNK, h.base_for(h.TRUNK, disable_lldp_receive=True))], state, have=have)
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("state", STATES)
def test_enum_wire_in_another_case_stays_a_noop(state):
    have = h.build_have(h.TRUNK, "spanning_tree_port_type", "network", **h.NOFAST)
    have[0]["interfaces"][0]["nvPairs"]["spanningTreePortType"] = "Network"
    prof = h.base_for(h.TRUNK, spanning_tree_port_type="network", **h.NOFAST)
    result, calls = h.run_configs([h.cfg_for(h.TRUNK, prof)], state, have=have)
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("state", STATES)
def test_unverified_process_tag_keeps_the_legacy_comparison(state):
    """'unverified' is a documented limitation, not a decision: whether NX-OS treats a process tag's
    case as significant is not established here, so a case-only tag change stays unsent, as before."""
    have = h.build_have(h.ROUTED, "ospf_tag", "PILOT-OSPF", **h.OSPF_CTX_NO_AREA)
    ctx = dict(h.OSPF_CTX)
    ctx["ospf_tag"] = "pilot-ospf"
    prof = h.base_for(h.ROUTED, **ctx)
    result, calls = h.run_configs([h.cfg_for(h.ROUTED, prof)], state, have=have)
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("cid", ["routed-ospf_auth_key", "trunk-acl_filter"])
def test_capability_disabled_keeps_the_pre_write_refusal(cid):
    case = EXACT[cid]
    result, calls = h.run_configs(want_of(case, case[5]), "merged", have=have_of(case), patch_version=None)
    assert result.get("failed") and h.writes(calls) == []


# ------------------------------------------------------------------ no_log: the key never reaches the output
@pytest.mark.parametrize("state", STATES)
def test_case_only_key_update_keeps_both_keys_out_of_the_emitted_result(state):
    assert h.real_serialiser_is_genuine()
    case = EXACT["routed-ospf_auth_key"]
    out, calls = h.emit_real_result(want_of(case, case[5]), state, have=have_of(case))
    assert sent_values(calls, "OSPF_AUTH_KEY") == [case[5]]          # the update is real ...
    assert case[5] not in out and case[4] not in out                  # ... and neither key is printed
    assert "OSPF_AUTH_KEY" in out or '"changed": true' in out


# ====================================================================================================
# Formerly test_gie_smu_mechanical_names.py
# S1 of the SMU adaptation: the mechanical UPPER_SNAKE -> camelCase wire renames.
#
# WHAT S1 CHANGED, AND WHAT IT DID NOT
#
# The SMU templates installed on the .90 controller renamed SOME declared variables to
# camelCase. This is NOT a blanket migration: in the captured `int_access_host` body,
# SERIAL_NUMBER, INTF_NAME, MTU, SPEED, DESC, CDP_ENABLE and ENABLE_ORPHAN_PORT are still
# UPPER_SNAKE, while `lldpTransmit` and `aclFilter` are camelCase. So every rename in S1 was
# read out of a declaration in `capture-R2/<parent>.template`, and only the 123 identities
# whose new name is exactly the mechanical transform of the old one are in scope.
#
# The public YAML contract is untouched: `flowcontrol_receive`, `acl_filter`,
# `spanning_tree_port_type`, `guard_mode` and the rest are spelled exactly as before.
#
# EXPECTATIONS ARE LITERALS, NOT DERIVED
#
# Every expected wire name below is written out by hand from the captured declaration, with
# its template line. None is computed by a casing helper or read back from the registry, so a
# wrong mapping in the registry cannot make these tests agree with it.
#
#   int_access_host.template:214   string aclFilter
#   int_access_host.template:~513  enum flowcontrolReceive      (public "on"/"off")
#   int_trunk_host.template:160    enum GUARD_MODE              <- deliberately NOT renamed
#   int_routed_host.template       integer ospfCost
#
# STILL PENDING, deliberately absent here: the 72 special renames such as
# DISABLE_LLDP_TRANSMIT -> lldpTransmit and DISABLE_QOS_STATS -> qosStatsSuppressed, the 8
# enum-value/metadata changes such as no_change -> noChange, and the one unresolved
# counterpart int_port_channel_trunk_host::ENABLE_VPC_PEER_LINK. S1 is partial and not
# deployable on its own.
#
# NOT LIVE TESTED. Offline only; nothing contacts a controller.
# ====================================================================================================
# Reviewed literals. Left side is the public option, right side the declared SMU wire key.
SMU_ACL_FILTER = "aclFilter"
SMU_FLOWCONTROL_RECEIVE = "flowcontrolReceive"
SMU_SPANNING_TREE_PORT_TYPE = "spanningTreePortType"
UNRENAMED_GUARD_MODE = "GUARD_MODE"

# The old names must not reappear anywhere in an outbound payload.
OLD_ACL_FILTER = "ACL_FILTER"
OLD_FLOWCONTROL_RECEIVE = "FLOWCONTROL_RECEIVE"

# Native module fields. They are NOT registry bindings and the captured bodies still declare
# them in UPPER_SNAKE, so a blanket casing pass would show up here.
NATIVE_UPPER = ("MTU", "SPEED", "DESC", "ADMIN_STATE", "CONF")


def rows():
    t = table.BINDING_TABLE
    return list(t.values()) if isinstance(t, dict) else list(t)


def wire_of(parent, profile_key):
    for r in rows():
        if r["parent_template"] == parent and r["profile_key"] == profile_key:
            return r["parent_nvpair"]
    raise AssertionError("no registry row for %s::%s" % (parent, profile_key))


def emitted(calls):
    """Every nvPair the module actually put on the wire, merged into one map."""
    out = {}
    for nv in request_nvpairs(calls):
        out.update(nv)
    return out


# ------------------------------------------------------- registry says the reviewed literal
def test_registry_carries_the_declared_smu_names():
    """The table's wire key equals the hand-reviewed declaration, per parent."""
    assert wire_of(MECH_NAMES_ACCESS, "acl_filter") == SMU_ACL_FILTER
    assert wire_of(MECH_NAMES_ACCESS, "flowcontrol_receive") == SMU_FLOWCONTROL_RECEIVE
    assert wire_of(MECH_NAMES_TRUNK, "flowcontrol_receive") == SMU_FLOWCONTROL_RECEIVE
    assert wire_of(MECH_NAMES_ACCESS, "spanning_tree_port_type") == SMU_SPANNING_TREE_PORT_TYPE


def test_a_field_the_smu_did_not_rename_keeps_its_upper_name():
    """GUARD_MODE is declared UPPER_SNAKE in int_trunk_host.template:160. The control that
    proves S1 renamed a confirmed SET, not everything it could reach."""
    assert wire_of(MECH_NAMES_TRUNK, "guard_mode") == UNRENAMED_GUARD_MODE


def test_the_public_option_names_did_not_change():
    """The YAML contract is the thing S1 must NOT move."""
    keys = {r["profile_key"] for r in rows()}
    for public in ("acl_filter", "flowcontrol_receive", "spanning_tree_port_type", "guard_mode"):
        assert public in keys, public


# ------------------------------------------------------------------- production, real main()
def test_public_input_emits_the_smu_key_and_not_the_old_one():
    """Unchanged public input -> the SMU key, correct value, and no duplicate old key."""
    profile = base_for(MECH_NAMES_ACCESS, flowcontrol_receive="on", acl_filter="ACL-PILOT")
    result, calls = run(profile, "merged")

    assert not result.get("failed"), result.get("msg")
    nv = emitted(calls)
    assert nv.get(SMU_FLOWCONTROL_RECEIVE) == "on", nv
    assert nv.get(SMU_ACL_FILTER) == "ACL-PILOT", nv
    assert OLD_FLOWCONTROL_RECEIVE not in nv, "the old wire key was emitted as well"
    assert OLD_ACL_FILTER not in nv, "the old wire key was emitted as well"


def test_native_fields_were_not_swept_into_camel_case():
    """Only declared renames moved. The native payload keys are still UPPER_SNAKE."""
    result, calls = run(base_for(MECH_NAMES_ACCESS, flowcontrol_receive="on"), "merged")
    assert not result.get("failed"), result.get("msg")
    nv = emitted(calls)
    for key in NATIVE_UPPER:
        assert key in nv, "native field %s vanished from the payload: %s" % (key, sorted(nv))
    for key in NATIVE_UPPER:
        camel = key.lower() if "_" not in key else key.split("_", maxsplit=1)[0].lower() + "".join(p.capitalize() for p in key.split("_")[1:])
        assert camel not in nv, "native field %s was camelCased to %s" % (key, camel)


def test_have_carrying_the_smu_key_is_preserved_under_merged():
    """A HAVE written with the SMU key is read, and an omission under merged keeps it.

    The HAVE is built with the literal SMU key injected by hand rather than taken from the
    module's own output, so the read path is tested against the declaration, not against
    whatever the producer happens to emit.
    """
    have = build_have(MECH_NAMES_ACCESS, "acl_filter", "ACL-PILOT")
    nv = have[0]["interfaces"][0]["nvPairs"]
    assert SMU_ACL_FILTER in nv, "the producer did not use the SMU key: %s" % sorted(nv)
    # Injected literal: prove the reader keys on this name and nothing else.
    nv.pop(OLD_ACL_FILTER, None)
    nv[SMU_ACL_FILTER] = "ACL-PILOT"

    result, calls = run(base_for(MECH_NAMES_ACCESS), "merged", have=copy.deepcopy(have))

    assert not result.get("failed"), result.get("msg")
    buckets = split_calls(calls)
    assert buckets["updates"] == [], "merged omission did not preserve; it configured again"
    assert buckets["deploys"] == []


def test_registered_binding_still_withdraws_under_the_new_name():
    """replaced / check / rerun for a registered binding, all through real main()."""
    have = build_have(MECH_NAMES_ACCESS, "flowcontrol_receive", "on")
    want = base_for(MECH_NAMES_ACCESS)  # omits flowcontrol_receive -> withdrawal

    # check mode: reports the reset, writes nothing
    checked, check_calls = run(want, "replaced", have=copy.deepcopy(have), check_mode=True)
    assert not checked.get("failed"), checked.get("msg")
    assert split_calls(check_calls)["updates"] == [], "check mode configured"
    reported = {}
    for nv in diff_nvpairs(checked):
        reported.update(nv)
    assert reported.get(SMU_FLOWCONTROL_RECEIVE) == "off", reported
    assert OLD_FLOWCONTROL_RECEIVE not in reported

    # real run: the reset reaches the wire under the SMU key
    applied, apply_calls = run(want, "replaced", have=copy.deepcopy(have))
    assert not applied.get("failed"), applied.get("msg")
    nv = emitted(apply_calls)
    assert nv.get(SMU_FLOWCONTROL_RECEIVE) == "off", nv
    assert OLD_FLOWCONTROL_RECEIVE not in nv

    # rerun against a HAVE already at the reset: nothing left to send
    at_reset = build_have(MECH_NAMES_ACCESS, "flowcontrol_receive", "off")
    rerun, rerun_calls = run(want, "replaced", have=at_reset)
    assert not rerun.get("failed"), rerun.get("msg")
    assert split_calls(rerun_calls)["updates"] == [], "the rerun configured again"


# ====================================================================================================
# Formerly test_gie_smu_special_and_enum.py
# S2 of the SMU adaptation: special renames, enum vocabularies, and the unsupported identity.
#
# WHAT THE BODIES SAY, WHICH IS WHY NOTHING IS INVERTED
#
# Every `DISABLE_*` name that lost its prefix kept its MEANING. Read from the freshly captured
# bodies (capture-S2, byte-identical to capture-R2 at 12.6.0.267):
#
#   boolean lldpReceive          DisplayName "Disable LLDP receive"      defaultValue=false
#   boolean queuingStats         DisplayName "Disable queuing policy statistics"
#                                content: noStats = " no-stats" if queuingStats == "true" else ""
#   boolean qosStatsSuppressed   content: noStats = " no-stats" if qosStatsSuppressed == "true"
#   boolean ipv4Redirects        content: disableIpv4Redirects = interfaceOptions["ipv4Redirects"]
#
# So `true` still means "disable" on every one of them; the template even renames ipv4Redirects
# back to a `disable`-prefixed local. All 21 unique pairs adjudicated RENAME_ONLY, none inverted,
# and the public option names (`disable_lldp_receive`, …) keep their meaning unchanged.
#
# THE THREE ENUM VOCABULARIES DID CHANGE
#
#     ospfNetworkType   no_change,broadcast,point_to_point -> noChange,broadcast,pointToPoint
#     ospfBfdMode       no_change,enable,disable           -> noChange,enable,disable
#     ospfPassiveMode   no_change,passive,no_passive       -> noChange,passive,noPassive
#
# and the installed body validates the SMU spelling directly:
#
#     if ospfPassiveMode not in ["noChange", "passive", "noPassive"]:
#
# `valid_values` stays the PUBLIC contract, so a playbook still writes `no_change` and an SMU
# spelling is still refused as input. Translation happens only at the wire boundary.
#
# Expected values below are hand-written from those declarations, never read back from the
# registry or computed by a helper.
#
# NOT LIVE TESTED ON SMU. Offline; nothing contacts a controller.
# ====================================================================================================
# Reviewed literals from the captured declarations.
SMU_LLDP_RECEIVE = "lldpReceive"
SMU_LLDP_TRANSMIT = "lldpTransmit"
SMU_QOS_STATS = "qosStatsSuppressed"
SMU_QUEUING_STATS = "queuingStats"
SMU_OSPF_GATE = "ospf"
SMU_PASSIVE_MODE = "ospfPassiveMode"

OLD_LLDP_RECEIVE = "DISABLE_LLDP_RECEIVE"
OLD_QOS_STATS = "DISABLE_QOS_STATS"
OLD_OSPF_GATE = "ENABLE_OSPF"

# The fabric-owned key that merely CONTAINS "ENABLE_OSPF" and must never be renamed with it.
FABRIC_OSPF_MD = "ENABLE_OSPF_AUTH_MESSAGE_DIGEST"


def row_of(parent, profile_key):
    for r in rows():
        if r["parent_template"] == parent and r["profile_key"] == profile_key:
            return r
    raise AssertionError("no registry row for %s::%s" % (parent, profile_key))


def special_enum_emitted(calls):
    out = {}
    for nv in request_nvpairs(calls):
        out.update(nv)
    return out


# --------------------------------------------------------------- special renames, no inversion
def test_special_renames_landed_on_the_declared_names():
    assert row_of(SPECIAL_ENUM_ACCESS, "disable_lldp_receive")["parent_nvpair"] == SMU_LLDP_RECEIVE
    assert row_of(SPECIAL_ENUM_ACCESS, "disable_lldp_transmit")["parent_nvpair"] == SMU_LLDP_TRANSMIT
    assert row_of(SPECIAL_ENUM_ACCESS, "disable_qos_stats")["parent_nvpair"] == SMU_QOS_STATS
    assert row_of(SPECIAL_ENUM_ACCESS, "disable_queuing_stats")["parent_nvpair"] == SMU_QUEUING_STATS
    assert row_of(ROUTED, "enable_ospf")["parent_nvpair"] == SMU_OSPF_GATE


def test_the_fabric_ospf_md_key_was_not_dragged_along_by_its_prefix():
    """ENABLE_OSPF_AUTH_MESSAGE_DIGEST contains ENABLE_OSPF. It is fabric-owned and must keep
    its name; a substring rename would have silently taken it."""
    assert FABRIC_OSPF_MD in open(engine.__file__).read()
    assert not any(r["parent_nvpair"] == "ospfAuthMessageDigest" for r in rows())


@pytest.mark.parametrize("public_value,wire", [(True, "true"), (False, "false")])
def test_both_boolean_values_survive_the_special_rename(public_value, wire):
    """The rename did not invert anything: true still means "disable" on the wire."""
    profile = base_for(SPECIAL_ENUM_ACCESS, disable_lldp_receive=public_value)
    result, calls = run(profile, "merged")

    assert not result.get("failed"), result.get("msg")
    nv = special_enum_emitted(calls)
    assert nv.get(SMU_LLDP_RECEIVE) == wire, nv
    assert OLD_LLDP_RECEIVE not in nv, "the pre-SMU key was emitted as well"


def test_the_public_option_names_and_meanings_are_unchanged():
    keys = {r["profile_key"] for r in rows()}
    for public in ("disable_lldp_receive", "disable_lldp_transmit", "disable_qos_stats",
                   "disable_queuing_stats", "enable_ospf"):
        assert public in keys, public


# ----------------------------------------------------------------------- enum vocabularies
def test_public_enum_contract_is_unchanged_and_refuses_the_smu_spelling():
    r = row_of(ROUTED, "ospf_passive_mode")
    assert r["valid_values"] == ("no_change", "passive", "no_passive"), r["valid_values"]
    with pytest.raises(engine.GieBindingError):
        engine.gie_validate_binding_value(ROUTED, "ospf_passive_mode", "noPassive")


def test_public_enum_value_is_translated_on_the_wire():
    profile = base_for(ROUTED, enable_ospf=True, ospf_passive_mode="no_passive")
    result, calls = run(profile, "merged", parent=ROUTED)

    assert not result.get("failed"), result.get("msg")
    nv = special_enum_emitted(calls)
    assert nv.get(SMU_PASSIVE_MODE) == "noPassive", nv
    assert "no_passive" not in nv.values(), "a public spelling reached the wire"


def test_a_have_in_the_smu_vocabulary_is_accepted_not_rejected():
    """A controller answer of noChange must not be refused by the public validator."""
    engine.gie_validate_binding_value(
        ROUTED, "ospf_passive_mode", "noChange", value_source="have"
    )
    r = row_of(ROUTED, "ospf_passive_mode")
    assert engine.gie_public_value(r, "noPassive") == "no_passive"
    assert engine.gie_wire_value(r, "no_passive") == "noPassive"


def test_a_binding_without_wire_values_is_identity():
    r = row_of(SPECIAL_ENUM_ACCESS, "acl_filter")
    assert "wire_values" not in r
    assert engine.gie_wire_value(r, "ACL-PILOT") == "ACL-PILOT"
    assert engine.gie_public_value(r, "ACL-PILOT") == "ACL-PILOT"


def test_a_second_invocation_against_the_smu_have_sends_nothing():
    """The rerun that proves the wire spelling round-trips, at the stub boundary."""
    have = build_have(ROUTED, "ospf_passive_mode", "no_passive")
    nv = have[0]["interfaces"][0]["nvPairs"]
    assert nv.get(SMU_PASSIVE_MODE) == "noPassive", sorted(nv)

    profile = base_for(ROUTED, enable_ospf=True, ospf_passive_mode="no_passive")
    result, calls = run(profile, "replaced", have=copy.deepcopy(have), parent=ROUTED)

    assert not result.get("failed"), result.get("msg")
    buckets = split_calls(calls)
    assert buckets["updates"] == [], "the second invocation configured again"
    assert buckets["deploys"] == []


def test_an_omitted_smu_field_survives_an_unrelated_change():
    """A no-op alone would not prove the omitted field survives a LATER write, so this
    changes a different field in the same payload and checks the omitted one is still there."""
    have = build_have(SPECIAL_ENUM_ACCESS, "disable_lldp_receive", True)
    want = base_for(SPECIAL_ENUM_ACCESS, description="changed-by-this-run")
    result, calls = run(want, "merged", have=copy.deepcopy(have))

    assert not result.get("failed"), result.get("msg")
    nv = special_enum_emitted(calls)
    assert nv.get("DESC") == "changed-by-this-run", nv
    assert nv.get(SMU_LLDP_RECEIVE) == "true", "the omitted SMU field was dropped by the write"


# -------------------------------------------------------- the identity with no counterpart
def test_the_unsupported_identity_is_kept_in_the_registry():
    """Its history is preserved; it is marked, not deleted."""
    r = row_of(SPECIAL_ENUM_PC_TRUNK, "enable_vpc_peer_link")
    assert r["smu_unsupported"] is True
    assert r["parent_nvpair"] == "ENABLE_VPC_PEER_LINK", "do not rename what has no counterpart"


@pytest.mark.parametrize("value", [True, False])
def test_explicit_unsupported_input_refuses_before_any_write(value):
    """Both values, and the refusal happens with NO mutating call at the stub."""
    profile = base_for(SPECIAL_ENUM_PC_TRUNK, enable_vpc_peer_link=value)
    result, calls = run(profile, "merged", parent=SPECIAL_ENUM_PC_TRUNK)

    assert result.get("failed"), "an unsupported field was accepted"
    assert "not supported by the interface templates installed" in str(result.get("msg"))
    buckets = split_calls(calls)
    assert buckets["updates"] == [] and buckets["deploys"] == [], calls


@pytest.mark.parametrize("value", [True, False])
def test_the_refusal_also_holds_in_check_mode(value):
    profile = base_for(SPECIAL_ENUM_PC_TRUNK, enable_vpc_peer_link=value)
    result, calls = run(profile, "merged", parent=SPECIAL_ENUM_PC_TRUNK, check_mode=True)

    assert result.get("failed"), "check mode accepted an unsupported field"
    assert split_calls(calls)["updates"] == []


def test_a_valid_object_before_the_unsupported_one_is_still_not_written():
    """The refusal is invocation-wide: a supported interface listed FIRST must not be
    configured before the unsupported one is reached."""
    good = cfg_for(SPECIAL_ENUM_ACCESS, base_for(SPECIAL_ENUM_ACCESS, disable_lldp_receive=True))
    bad = cfg_for(SPECIAL_ENUM_PC_TRUNK, base_for(SPECIAL_ENUM_PC_TRUNK, enable_vpc_peer_link=True))
    result, calls = run_configs([good, bad], "merged")

    assert result.get("failed"), "the unsupported object did not fail the invocation"
    buckets = split_calls(calls)
    assert buckets["updates"] == [], "the preceding valid object was written anyway"
    assert buckets["deploys"] == []


def test_omitting_the_unsupported_field_does_not_block_a_supported_sibling():
    """Omission must never reach the refusal, and must not invent a withdrawal."""
    profile = base_for(SPECIAL_ENUM_PC_TRUNK, disable_lldp_receive=True)
    assert "enable_vpc_peer_link" not in profile
    result, calls = run(profile, "merged", parent=SPECIAL_ENUM_PC_TRUNK)

    assert not result.get("failed"), result.get("msg")
    nv = special_enum_emitted(calls)
    assert nv.get(SMU_LLDP_RECEIVE) == "true", nv
    assert "ENABLE_VPC_PEER_LINK" not in nv, "the pre-SMU key leaked onto the wire"


# ====================================================================================================
# Formerly test_gie_smu_neutral_enum_regression.py
# Regression for the S2 neutral-enum omission defect, on all eight rows.
#
# THE DEFECT
#
# `gie_declared_default_wire()` serialized `default_template` -- which is recorded in the PUBLIC
# vocabulary -- without the wire-value mapping, while `gie_withdrawal_action()` compares a HAVE
# that came FROM the controller against it. So a field already sitting at its SMU declared
# neutral read as `no_change` on one side and `noChange` on the other, classified as an
# unclassifiable value, and refused the whole invocation. `merged` was unaffected, which is why
# it is the positive control below.
#
# The fix translates at the declared-default boundary, so both sides of that comparison are in
# the wire representation. No reset was registered for these rows, the public vocabulary did not
# move, and the general withdrawal contract is untouched.
#
# WHY THESE EXPECTATIONS ARE INDEPENDENT
#
# The neutral spellings are transcribed by hand from the captured declarations (capture-S2,
# byte-identical to capture-R2 at 12.6.0.267), not obtained from the mapper under test:
#
#     ospfNetworkType   validValues=noChange,broadcast,pointToPoint   defaultValue=noChange
#     ospfBfdMode       validValues=noChange,enable,disable           defaultValue=noChange
#     ospfPassiveMode   validValues=noChange,passive,noPassive        defaultValue=noChange
#
# NOT LIVE TESTED ON SMU. Offline only.
# ====================================================================================================
# Hand-transcribed neutral value per enum wire key.
REVIEWED_NEUTRAL = {
    "ospfNetworkType": "noChange",
    "ospfBfdMode": "noChange",
    "ospfPassiveMode": "noChange",
}


def _rows():
    t = table.BINDING_TABLE
    return list(t.values()) if isinstance(t, dict) else list(t)


NEUTRAL_ROWS = sorted((b["parent_template"], b["profile_key"], b["parent_nvpair"]) for b in _rows() if b["parent_nvpair"] in REVIEWED_NEUTRAL)
NEUTRAL_IDS = ["%s::%s" % (p.replace("int_", ""), k) for p, k, _nv in NEUTRAL_ROWS]


def test_the_derived_set_covers_all_eleven_neutral_enum_rows():
    """Guard the guard: eleven rows over three fields -- the eight of the earlier SMU plus the loopback BFD and
    subinterface BFD and passive rows that SMU 017 turned into enums."""
    # + 3: ospfPassiveMode, ospfNetworkType and ospfBfdMode on int_l3_port_channel (slice 0b_40) = 14.
    assert len(NEUTRAL_ROWS) == 14, NEUTRAL_ROWS
    assert {nv for _p, _k, nv in NEUTRAL_ROWS} == set(REVIEWED_NEUTRAL)


@pytest.mark.parametrize("parent,profile_key,nvpair", NEUTRAL_ROWS, ids=NEUTRAL_IDS)
def test_the_declared_default_is_serialized_in_the_wire_vocabulary(parent, profile_key, nvpair):
    """The exact boundary that was wrong: the default must be the controller's spelling."""
    binding = engine.resolve_binding(parent, profile_key)
    assert engine.gie_declared_default_wire(binding) == REVIEWED_NEUTRAL[nvpair]


@pytest.mark.parametrize("parent,profile_key,nvpair", NEUTRAL_ROWS, ids=NEUTRAL_IDS)
def test_a_have_at_the_declared_neutral_is_already_withdrawn(parent, profile_key, nvpair):
    """No reset exists for these rows, so a HAVE already neutral must be a no-op -- not an
    unclassifiable value, and not an invented reset."""
    action, wire = engine.gie_withdrawal_action(
        parent, profile_key, REVIEWED_NEUTRAL[nvpair], NEUTRAL_ENUM_SUPPORTED, SUPPORTED_PATCH)
    assert action == engine.GIE_WITHDRAW_NONE, (action, wire)


@pytest.mark.parametrize("parent,profile_key,nvpair", NEUTRAL_ROWS, ids=NEUTRAL_IDS)
def test_the_pre_smu_spelling_is_not_silently_accepted_as_neutral(parent, profile_key, nvpair):
    """This build is SMU-only, so there is exactly ONE neutral representation.

    Before the fix the comparison held the PUBLIC spelling, so `no_change` in a HAVE read as
    neutral and the controller's own `noChange` did not. The fix moves the comparison to the
    wire representation; the mirror image must NOT be introduced as a second accepted
    spelling, because dual-schema support is explicitly out of scope. A controller on this
    build never returns `no_change`, so seeing it is an unrecognised value and is refused --
    not quietly treated as already-withdrawn.
    """
    action, _wire = engine.gie_withdrawal_action(
        parent, profile_key, "no_change", NEUTRAL_ENUM_SUPPORTED, SUPPORTED_PATCH)
    # THE GUARANTEE, invariant and the whole reason this case exists: the pre-SMU spelling is
    # NEVER read as already-withdrawn.
    assert action != engine.GIE_WITHDRAW_NONE, (
        "the pre-SMU spelling was read as already-withdrawn: %r" % action)
    # The CONCRETE outcome depends on whether the row carries a registered reset, and both
    # branches are declared rather than letting a future registration invalidate the case:
    #
    #   no reset   -> UNSUPPORTED: there is no known way to withdraw it, so it fails closed.
    #   with reset -> RESET: it differs from the neutral, so it is NORMALISED by sending it.
    #
    # B3 registered two of these eight rows, which is what stopped the second branch from
    # being hypothetical. The first version of this case covered only the first branch.
    binding = engine.resolve_binding(parent, profile_key)
    if binding.get("reset_wire") is None:
        assert action == engine.GIE_WITHDRAW_UNSUPPORTED, action
    else:
        assert action == engine.GIE_WITHDRAW_RESET, action


@pytest.mark.parametrize("state", ["replaced", "merged"])
@pytest.mark.parametrize("check_mode", [False, True])
def test_main_omitting_a_neutral_field_writes_nothing(state, check_mode):
    """Through real main(): omission of a field already at its neutral sends nothing, in
    replaced and in check mode. merged is the positive control that never regressed."""
    have = build_have("int_routed_host", "ospf_passive_mode", "no_change", enable_ospf=True)
    nv = have[0]["interfaces"][0]["nvPairs"]
    assert nv.get("ospfPassiveMode") == "noChange", sorted(nv)

    want = base_for("int_routed_host", enable_ospf=True)
    assert "ospf_passive_mode" not in want

    result, calls = run(
        want,
        state,
        have=copy.deepcopy(have),
        parent="int_routed_host",
        check_mode=check_mode,
    )
    assert not result.get("failed"), result.get("msg")
    buckets = split_calls(calls)
    assert buckets["updates"] == [], "a neutral field produced a configuration update"
    assert buckets["deploys"] == []


# ------------------------------------------------------------------- positive controls
@pytest.mark.parametrize(
    "public,wire",
    [("no_change", "noChange"), ("passive", "passive"), ("no_passive", "noPassive")],
)
def test_an_explicit_public_value_still_encodes_to_its_reviewed_wire_value(public, wire):
    add, err = engine.gie_contribute_nvpairs(
        "int_routed_host", {"enable_ospf": True, "ospf_passive_mode": public},
        NEUTRAL_ENUM_SUPPORTED, SUPPORTED_PATCH)
    assert err is None, err
    assert add["ospfPassiveMode"] == wire, add


def test_an_unknown_value_does_not_become_neutral():
    """The fix must not turn anything it does not recognise into the neutral default."""
    with pytest.raises(engine.GieBindingError):
        engine.gie_validate_binding_value("int_routed_host", "ospf_passive_mode", "bogus")
    action, _wire = engine.gie_withdrawal_action(
        "int_routed_host", "ospf_passive_mode", "somethingElse", NEUTRAL_ENUM_SUPPORTED, SUPPORTED_PATCH)
    assert action != engine.GIE_WITHDRAW_NONE, "an unknown value was read as neutral"


def test_a_configured_enum_without_a_measured_reset_still_fails_closed_when_omitted():
    """The contract that must NOT have been weakened: a non-neutral configured value on a row
    with no measured reset still refuses, rather than being silently left or reset.

    The example is DERIVED from the table instead of hardcoded. It used to name
    `int_routed_host::ospf_passive_mode`, and B3 registered a reset for exactly that row --
    which made the case fail while the contract it guards was intact. Deriving it means a
    future registration can never invalidate this case; if the table ever ran out of
    unregistered neutral enums, the guard below says so loudly instead of the case passing
    for the wrong reason.
    """
    # MEASURED: the table no longer holds a SINGLE enum that lacks a reset while
    # carrying `no_change` in its vocabulary -- zero rows. The OSPF options and BFD
    # measurements registered the last of them (`ospf_network_type` on three parents,
    # `ospf_passive_mode` on int_vlan, `ospf_bfd_mode` on routed and vlan). This case ran out of
    # an example, and its own message asked for it to be rehomed deliberately, not deleted.
    #
    # THE CONTRACT IT GUARDS DID NOT CHANGE: a configured value on a row WITHOUT a measured
    # reset still refuses. What changed is where the example comes from: no longer "an enum with
    # a neutral vocabulary" -- there is none -- but "an enum with a declared default and no
    # reset", which is the same engine property without depending on a vocabulary that ran out.
    without_reset = [(p, k, nv) for (p, k, nv) in NEUTRAL_ROWS
                     if (engine.resolve_binding(p, k) or {}).get("reset_wire") is None]
    if not without_reset:
        rows = list(engine.BINDING_TABLE.values()) if isinstance(engine.BINDING_TABLE, dict) \
            else list(engine.BINDING_TABLE)
        without_reset = [(r["parent_template"], r["profile_key"], r["parent_nvpair"])
                         for r in rows
                         if r["type"] == "enum" and r.get("reset_wire") is None
                         and r.get("default_template") is not None]
    assert without_reset, (
        "every enum in the table now carries a reset; this case has nothing left to guard and "
        "must be rehomed deliberately, not deleted")
    for parent, profile_key, _nvpair in without_reset:
        binding = engine.resolve_binding(parent, profile_key)
        vocab = binding.get("wire_values") or {}
        if vocab:
            configured = next(v for pub, v in vocab.items() if pub != "no_change")
        else:
            # no declared vocabulary: any value other than the default counts as "configured"
            d = binding["default_template"]
            configured = "0" if str(d) != "0" else "7"
        action, _wire = engine.gie_withdrawal_action(
            parent, profile_key, configured, NEUTRAL_ENUM_SUPPORTED, SUPPORTED_PATCH)
        assert action == engine.GIE_WITHDRAW_UNSUPPORTED, (
            "%s::%s has no reset, so HAVE=%r must fail closed, got %r"
            % (parent, profile_key, configured, action))


def test_merged_preservation_still_works_for_a_neutral_row():
    have = build_have("int_routed_host", "ospf_passive_mode", "passive", enable_ospf=True)
    want = base_for("int_routed_host", enable_ospf=True)
    result, calls = run(want, "merged", have=copy.deepcopy(have), parent="int_routed_host")
    assert not result.get("failed"), result.get("msg")
    assert split_calls(calls)["updates"] == []


def test_unrelated_default_handling_is_untouched():
    """A boolean, a string and an integer default keep their previous wire serialization."""
    cases = [
        ("int_access_host", "disable_lldp_receive", "false"),
        ("int_access_host", "acl_filter", None),
        ("int_routed_host", "ospf_cost", None),
    ]
    for parent, key, expected in cases:
        binding = engine.resolve_binding(parent, key)
        got = engine.gie_declared_default_wire(binding)
        if expected is None:
            assert got is None or isinstance(got, str), (parent, key, got)
        else:
            assert got == expected, (parent, key, got)
