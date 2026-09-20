"""Simple passthrough bindings, one case per value type.

Covers positive transport on a supported version, omission, wrong parent, native type,
enum and length constraints, unsupported/unknown/malformed versions, same-parent
carry-forward, malformed HAVE, and the generator/table integrity guards.

Also regresses the OSPF-MD and FLOWCONTROL_RECEIVE bindings to prove they stay byte- and
behaviour-compatible as the table grows.

Offline: no controller and no device.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    BINDING_TABLE,
    PROVENANCE_SHA256,
    resolve_binding,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    GieBindingError,
    gie_all_registered_keys,
    gie_carry_forward_bindings,
    gie_contribute_nvpairs,
    gie_extend_prof_spec,
    gie_guarded_keys,
    gie_invalid_parent_key,
    gie_nvpair_keymap,
    gie_validate_binding_value,
    gie_version_supported,
)

TRUNK = "int_trunk_host"
ACCESS = "int_access_host"
LOOPBACK = "int_fabric_loopback_11_1"
PC_TRUNK = "int_port_channel_trunk_host"
PC_ACCESS = "int_port_channel_access_host"
PC_DOT1Q = "int_port_channel_dot1q_tunnel_host"

SUPPORTED = "12.6.0.267"
BELOW = "12.6.0.266"
UNSUPPORTED_VERSIONS = (BELOW, "12.5.9.999", None, "", "not.a.version", "12.x.0.267")

GUARD_VALUES = ("root", "none", "loop", "no")


def _wire(value):
    """The nvPair form the engine emits for a PASSTHROUGH value.

    nvPairs is a string-valued map, so a boolean is transported as "true"/"false"; strings and
    enums are already in wire form and pass through untouched. Mirrors gie_engine._to_nvpair_wire.

    This slice originally asserted the native bool instead. That contract was reversed after a
    live measurement: the module compared its own True against the "true" the controller returns,
    never converged, and re-pushed DISABLE_LLDP on every run. See test_gie_boolean_wire_form.py.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


# (parent, profile_key, nvpair, a valid explicit PLAYBOOK value -- use _wire() for the payload)
NINE = (
    (TRUNK, "guard_mode", "GUARD_MODE", "root"),
    (PC_TRUNK, "guard_mode", "GUARD_MODE", "loop"),
    (ACCESS, "disable_lldp_transmit", "DISABLE_LLDP_TRANSMIT", True),
    (TRUNK, "disable_lldp_transmit", "DISABLE_LLDP_TRANSMIT", False),
    (ACCESS, "acl_filter", "ACL_FILTER", "ACL_A"),
    (TRUNK, "acl_filter", "ACL_FILTER", "ACL_B"),
    (PC_ACCESS, "acl_filter", "ACL_FILTER", "ACL_C"),
    (PC_TRUNK, "acl_filter", "ACL_FILTER", "ACL_D"),
    (PC_DOT1Q, "acl_filter", "ACL_FILTER", "ACL_E"),
)


def _load_generator():
    path = (
        Path(gie_binding_table.__file__).resolve().parents[2]
        / "tools"
        / "gie_generate_binding_table.py"
    )
    spec = importlib.util.spec_from_file_location("gie_gen_a16", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    assert len(BINDING_TABLE) == 221
    assert len(set(keys)) == 221, "duplicate (parent, nvpair) row"
    pk_keys = [(b["parent_template"], b["profile_key"]) for b in BINDING_TABLE]
    assert len(set(pk_keys)) == 221, "duplicate (parent, profile_key) row"


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


# compile_rows() valida FILAS DE SLICE, y BINDING_TABLE es su SALIDA. Tres campos del esquema
# -- presence_model, emit_when, parent_resolution -- son documentales y FIELDS no los propaga a
# la tabla, asi que una fila de la tabla no es una entrada valida para el compilador.
#
# Reutilizarla como entrada funcionaba por accidente mientras el generador no validaba esquema.
# Ahora lo valida (el gate se movio ahi porque los dos checkers aparte llevaban cuatro lotes
# muertos sin que nadie lo notara), asi que los casos que ejercitan el compilador reponen esos
# tres campos. Reponerlos aqui es lo correcto y no un parche: lo que se quiere ejercitar son las
# reglas de compilacion -- allowlist, duplicados, profile_key -- no el gate de esquema, que
# tiene sus propios casos.
#
# La alternativa seria meter los tres campos en FIELDS, y eso moveria el binding table y
# engordaria un artefacto de runtime con datos que nadie lee.
def _as_slice_rows(rows):
    """Las filas de la tabla, con los campos de esquema que un slice declara y la tabla no."""
    return [
        dict(r, presence_model="two_axis", emit_when="explicit_only",
             parent_resolution="desired_parent")
        for r in rows
    ]


# ------------------------------------------------------------------ generator guards
def test_generator_rejects_duplicate_missing_and_profile_key_mismatch():
    gen = _load_generator()
    rows = _as_slice_rows(BINDING_TABLE)
    assert len(gen.compile_rows(rows)) == 221

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

    There were TWO validator scripts under evidence/generic-interface-engine/, and both had been
    dead for four lots without anyone noticing: one still expected a flat list of rows when every
    slice had become a mapping with a `bindings:` key, the other required a `sensitive` field
    that only one surviving slice declares. Neither failed loudly, because nothing ran them --
    and a validator you have to remember to invoke is one that goes stale.

    So the gate moved into compile_rows(), which runs on every regeneration. This case exists so
    it cannot quietly stop enforcing: every rule is asserted by sabotage, and the error has to
    NAME the offending row, because "schema error" on a 221-row table is not actionable.

    Not re-asserted here -- compile_rows owns them above, with their own cases: the allowlist,
    duplicates, profile_key mismatch, unknown mechanism, complete-set.
    """
    gen = _load_generator()
    rows = _as_slice_rows(BINDING_TABLE)
    assert len(gen.compile_rows(rows)) == 221

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
    assert len(gen.compile_rows(rows)) == 221


# ------------------------------------------------------------------ positive transport
@pytest.mark.parametrize("parent,pk,nvpair,value", NINE)
def test_supported_version_transports_the_wire_value(parent, pk, nvpair, value):
    add, err = gie_contribute_nvpairs(parent, {pk: value}, SUPPORTED)
    assert err is None
    assert add == {nvpair: _wire(value)}
    # Every passthrough nvPair leaves the engine as a string, whatever the registered type.
    assert isinstance(add[nvpair], str)


def test_every_guard_mode_choice_transports():
    for parent in (TRUNK, PC_TRUNK):
        for value in GUARD_VALUES:
            add, err = gie_contribute_nvpairs(parent, {"guard_mode": value}, SUPPORTED)
            assert err is None and add == {"GUARD_MODE": value}
            # Exact type, not isinstance: a str subclass such as AnsibleUnicode would pass an
        # isinstance check while still being the wrong thing on the wire.
        assert type(add["GUARD_MODE"]) is str  # pylint: disable=unidiomatic-typecheck


def test_disable_lldp_transports_both_booleans():
    for parent in (ACCESS, TRUNK):
        for value, wire in ((True, "true"), (False, "false")):
            add, err = gie_contribute_nvpairs(parent, {"disable_lldp_transmit": value}, SUPPORTED)
            assert err is None and add == {"DISABLE_LLDP_TRANSMIT": wire}
            # Lowercase JSON spelling, which is what the template DSL tests against --
            # not Python's str(True) == "True".
            assert add["DISABLE_LLDP_TRANSMIT"] == wire != str(value)


def test_acl_filter_accepts_boundary_lengths():
    for parent in (ACCESS, TRUNK, PC_ACCESS, PC_TRUNK, PC_DOT1Q):
        for value in ("A", "A" * 64):
            add, err = gie_contribute_nvpairs(parent, {"acl_filter": value}, SUPPORTED)
            assert err is None and add == {"ACL_FILTER": value}


def test_multiple_new_keys_on_one_parent_contribute_together():
    add, err = gie_contribute_nvpairs(
        TRUNK,
        {"guard_mode": "root", "disable_lldp_transmit": True, "acl_filter": "ACL_X",
         "flowcontrol_receive": "on"},
        SUPPORTED,
    )
    assert err is None
    assert add == {
        "GUARD_MODE": "root",
        "DISABLE_LLDP_TRANSMIT": "true",
        "ACL_FILTER": "ACL_X",
        "FLOWCONTROL_RECEIVE": "on",
    }


# ------------------------------------------------------------------ omission
@pytest.mark.parametrize("parent,pk,nvpair,value", NINE)
def test_omission_contributes_nothing(parent, pk, nvpair, value):
    add, err = gie_contribute_nvpairs(parent, {}, SUPPORTED)
    assert err is None and add == {}


@pytest.mark.parametrize("parent,pk,nvpair,value", NINE)
def test_omission_is_not_default_false_or_empty_string(parent, pk, nvpair, value):
    add, err = gie_contribute_nvpairs(parent, {"unrelated": "x"}, SUPPORTED)
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
    its own suite: ``test_gie_clear_string_binding.py``. A short-but-nonempty value is still
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
        gie_contribute_nvpairs(TRUNK, {"guard_mode": "bogus"}, SUPPORTED)


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
        # (slice 0b_16), so the guard must ACCEPT it -- asserted in test_gie_routed_bindings.
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
    add, err = gie_contribute_nvpairs(parent, {pk: value}, version)
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
        add, err = gie_contribute_nvpairs(parent, {pk: value}, BELOW)
        assert add is None and err, f"{pk} must fail closed, not withhold"


# ------------------------------------------------------------------ carry forward
def test_carry_forward_covers_every_new_passthrough_binding():
    assert {
        (r["parent_nvpair"], r["profile_key"]) for r in gie_carry_forward_bindings(TRUNK)
    } == {
        ("FLOWCONTROL_RECEIVE", "flowcontrol_receive"),
        ("FLOWCONTROL_SEND", "flowcontrol_send"),
        ("SPANNING_TREE_PORT_TYPE", "spanning_tree_port_type"),
        ("GUARD_MODE", "guard_mode"),
        ("DISABLE_LLDP_TRANSMIT", "disable_lldp_transmit"),
        ("DISABLE_LLDP_RECEIVE", "disable_lldp_receive"),
        ("ACL_FILTER", "acl_filter"),
        ("DISABLE_QOS_STATS", "disable_qos_stats"),
        ("DISABLE_QUEUING_STATS", "disable_queuing_stats"),
    }
    assert {
        (r["parent_nvpair"], r["profile_key"]) for r in gie_carry_forward_bindings(ACCESS)
    } == {
        ("FLOWCONTROL_RECEIVE", "flowcontrol_receive"),
        ("FLOWCONTROL_SEND", "flowcontrol_send"),
        ("SPANNING_TREE_PORT_TYPE", "spanning_tree_port_type"),
        ("DISABLE_LLDP_TRANSMIT", "disable_lldp_transmit"),
        ("DISABLE_LLDP_RECEIVE", "disable_lldp_receive"),
        ("ACL_FILTER", "acl_filter"),
        ("DISABLE_QOS_STATS", "disable_qos_stats"),
        ("DISABLE_QUEUING_STATS", "disable_queuing_stats"),
    }
    # The port-channel parents carry every field registered for them.
    assert {
        (r["parent_nvpair"], r["profile_key"]) for r in gie_carry_forward_bindings(PC_TRUNK)
    } == {
        ("GUARD_MODE", "guard_mode"),
        ("ACL_FILTER", "acl_filter"),
        ("DISABLE_LLDP_TRANSMIT", "disable_lldp_transmit"),
        ("DISABLE_LLDP_RECEIVE", "disable_lldp_receive"),
        ("SPANNING_TREE_PORT_TYPE", "spanning_tree_port_type"),
        ("DISABLE_QOS_STATS", "disable_qos_stats"),
        ("DISABLE_QUEUING_STATS", "disable_queuing_stats"),
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

    Captured from GET /rest/interface on a freshly deployed FAB1 -- Leaf-101 Ethernet1/4
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
    assert km["DISABLE_LLDP_TRANSMIT"] == "disable_lldp_transmit"
    assert km["ACL_FILTER"] == "acl_filter"
    assert km["FLOWCONTROL_RECEIVE"] == "flowcontrol_receive"
    assert km["FLOWCONTROL_SEND"] == "flowcontrol_send"
    assert km["SPANNING_TREE_PORT_TYPE"] == "spanning_tree_port_type"
    # The OSPF slice on int_routed_host. No module change was needed for these: the keymap is
    # derived from the binding table by gie_nvpair_keymap(), so a new row lands here by itself.
    # Both key-bearing nvPairs reach the keymap like any other. The keymap is how a HAVE
    # nvPair is translated back to a profile key, so leaving a secret out of it would make the
    # controller's value invisible to the comparator -- a re-push on every run, not a leak.
    assert km["OSPF_AUTH_KEY"] == "ospf_auth_key"
    assert km["OSPF_AUTHENTICATION_KEY"] == "ospf_authentication_key"
    assert km["OSPF_AUTH_KEY_ID"] == "ospf_auth_key_id"
    assert km["OSPF_AUTHENTICATION_KEY_TYPE"] == "ospf_authentication_key_type"
    assert km["ENABLE_OSPF_AUTH"] == "enable_ospf_auth"
    assert km["ENABLE_OSPF"] == "enable_ospf"
    assert km["OSPF_TAG"] == "ospf_tag"
    assert km["OSPF_AREA_ID"] == "ospf_area_id"
    assert km["OSPF_COST"] == "ospf_cost"
    # EIGRP, slice 0b_22: thirteen distinct nvPairs, each shared by the three overlay parents,
    # so the keymap grows by thirteen and not by thirty-nine.
    assert km["EIGRP_PROCESS_TAG"] == "eigrp_process_tag"
    assert km["ENABLE_EIGRP_ROUTING"] == "enable_eigrp_routing"
    assert km["EIGRP_IPV4_DISTRIBUTE_LIST_DIRECTION"] == "eigrp_ipv4_distribute_list_direction"
    assert km["DISABLE_EIGRP_BFD"] == "disable_eigrp_bfd"
    assert km["OSPF_ADVERTISE_SUBNET"] == "ospf_advertise_subnet"
    assert km["ENABLE_BFD_INTERVAL"] == "enable_bfd_interval"
    assert km["BFD_TX_INTERVAL"] == "bfd_tx_interval"
    assert km["HSRP_PRIORITY_FORWARDING_THRESHOLD_LOWER"] == "hsrp_priority_forwarding_threshold_lower"
    assert km["HSRP_PREEMPT_DELAY_MINIMUM"] == "hsrp_preempt_delay_minimum"
    assert km["HSRP_VIPv6"] == "hsrp_vipv6"
    assert km["HSRP_GROUPv6"] == "hsrp_groupv6"
    assert km["DISABLE_IPV4_REDIRECTS"] == "disable_ipv4_redirects"
    assert km["IPV6_ND_SUPPRESS_RA"] == "ipv6_nd_suppress_ra"
    assert km["ENABLE_DAMPENING"] == "enable_dampening"
    assert km["DAMPENING_RESTART_PENALTY"] == "dampening_restart_penalty"
    assert km["ARP_TIMEOUT"] == "arp_timeout"
    assert km["ENABLE_PIM_SPARSE"] == "enable_pim_sparse"
    assert km["PIM_DR_PRIORITY"] == "pim_dr_priority"
    assert km["ENABLE_PIM_BFD_INSTANCE"] == "enable_pim_bfd_instance"
    # La forma del PADRE, con v minuscula. El hijo la espera en mayusculas y el padre traduce;
    # esta asercion es lo que impide que alguien "corrija" la capitalizacion y rompa el binding
    # en silencio.
    assert km["IPv6_LINK_LOCAL"] == "ipv6_link_local"
    assert "IPV6_LINK_LOCAL" not in km, "esa es la forma del HIJO, no la del padre"
    # 66 = 65 + ARP_TIMEOUT. Una sola clave nueva para tres filas: el mismo nombre publico en
    # los tres padres, que es el punto de llavear por (parent, nvpair) y no por nombre.
    # 69 = 66 + las TRES de PIM, que entre ellas cubren ocho filas.
    # 70 = 69 + IPv6_LINK_LOCAL, una clave para las tres filas overlay.
    assert len(km) == 70


def test_all_registered_keys():
    assert gie_all_registered_keys() == {
        "flowcontrol_receive", "flowcontrol_send", "spanning_tree_port_type",
        "guard_mode", "disable_lldp_transmit", "disable_lldp_receive", "acl_filter",
        "disable_qos_stats", "disable_queuing_stats",
        "disable_bfd_echo", "ipv4_acl_in",
        # OSPF, slices 0b_18/0b_19/0b_20. SIXTEEN distinct names across the three overlay
        # parents plus int_loopback, written as one list: the lots share most of their names,
        # so a literal that repeats them per lot asserts less than it appears to. The sharing
        # is the design -- bindings are keyed by (parent, nvpair), not by name.
        "enable_ospf", "ospf_tag", "ospf_area_id", "ospf_cost", "ospf_mtu_ignore",
        "ospf_shutdown", "ospf_hello_interval", "ospf_dead_interval", "ospf_transmit_delay",
        "ospf_priority", "ospf_passive_mode", "ospf_network_type", "ospf_bfd_mode",
        # These three only ever came from the second lot (int_subif / int_vlan).
        "ospf_bfd", "ospf_passive_interface", "ospf_retransmit_interval",
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
        # HSRP IPv6, slice 0b_27. Dos: HSRP_VIPv6 es la PRIMERA fila de la tabla que corresponde
        # a un campo de direccion de la plantilla (ipV6Address -> string, NDFC valida el formato).
        # IPv6/PREFIXv6 se retiraron: registrar ipv6_addr hizo que el guard lo rechazara en
        # int_subif, donde el spec nativo si lo soporta. Ver el slice y phase37.
        "hsrp_vipv6",
        "hsrp_groupv6",
        # Redirects partidos + ND suppress-RA, slice 0b_28. Tres claves publicas, cada una en
        # los TRES padres overlay. DISABLE_IP_REDIRECTS queda fuera: es nativo y registrarlo
        # repetiria el fallo de ipv6_addr, porque gie_guarded_keys() no filtra por padre.
        "disable_ipv4_redirects",
        "disable_ipv6_redirects",
        "ipv6_nd_suppress_ra",
        # Dampening, slice 0b_6 con su mecanismo corregido child_pti -> passthrough. Siete
        # claves, SOLO en int_routed_host. Su CLI no existe en el NX-OS de C9300v -- medido en
        # las dos imagenes del lab -- asi que estan registradas y validadas en el CONTROLADOR,
        # nunca en el equipo. Ver phase39.
        "enable_dampening", "dampening_half_life", "dampening_reuse", "dampening_suppress",
        "dampening_max_suppress", "dampening_restart", "dampening_restart_penalty",
        # ARP_TIMEOUT, slice 0b_3, registrado por fin (2026-09-20). UNA clave publica en los
        # tres padres overlay; int_loopback no lo declara. El caso mas simple del registro:
        # un campo, un hijo, una linea de CLI, sin gate ni dependencias. Ver phase41.
        "arp_timeout",
        # PIM, slice 0b_31. TRES claves publicas para OCHO filas, repartidas desigualmente:
        # sparse en los cuatro padres, dr_priority en tres (una loopback no elige DR) y
        # bfd_instance solo en int_routed_host. Ver phase42.
        "enable_pim_sparse", "pim_dr_priority", "enable_pim_bfd_instance",
        # IPv6 link-local, slice 0b_32. UNA clave publica en los TRES padres overlay
        # (int_loopback no lo declara). La clave del nvPair es `IPv6_LINK_LOCAL` con v
        # minuscula -- la forma del PADRE; el hijo la espera en mayusculas y el padre traduce.
        "ipv6_link_local",
        "ospf_advertise_subnet",
        # BFD, slice 0b_24 and the eight rows of 0b_4/0b_5 committed with their mechanism
        # corrected from child_pti to passthrough. Four public keys; disable_bfd_echo was
        # already here, from int_routed_host.
        "enable_bfd_interval", "bfd_tx_interval", "bfd_min_rx_interval", "bfd_multiplier",
    }


def test_same_value_produces_the_same_payload():
    """The engine is deterministic: the same input always yields the same payload.

    This is NOT an idempotency test, and the earlier name and comment here claimed it was:
    "the comparator sees a stable native value, so a repeat run diffs to nothing new". That was
    wrong, and it is the reason a real defect survived offline. Comparing the engine against
    ITSELF is stable no matter what the engine emits -- including a native bool that the
    comparator could never match against the controller's "true".

    Idempotency is a property of want-vs-HAVE, so it can only be pinned by a test that carries a
    controller value on the other side. That test lives in test_gie_boolean_wire_form.py
    (test_reapplying_the_same_boolean_is_idempotent), and it drives the real comparison.
    """
    for parent, pk, nvpair, value in NINE:
        first, err1 = gie_contribute_nvpairs(parent, {pk: value}, SUPPORTED)
        second, err2 = gie_contribute_nvpairs(parent, {pk: value}, SUPPORTED)
        assert err1 is None and err2 is None
        assert first == second == {nvpair: _wire(value)}


# ------------------------------------------------------------ baseline regression
def test_a15_flowcontrol_contract_is_unchanged():
    for parent in (ACCESS, TRUNK):
        b = resolve_binding(parent, "flowcontrol_receive")
        assert b["parent_nvpair"] == "FLOWCONTROL_RECEIVE"
        assert b["type"] == "enum"
        assert tuple(b["valid_values"]) == ("on", "off")
        assert b["default_template"] == "off"
        assert b["mechanism"] == "passthrough"
        assert b["min_ndfc_version"] == SUPPORTED
        for value in ("on", "off"):
            add, err = gie_contribute_nvpairs(
                parent, {"flowcontrol_receive": value}, SUPPORTED
            )
            assert err is None and add == {"FLOWCONTROL_RECEIVE": value}
        add, err = gie_contribute_nvpairs(
            parent, {"flowcontrol_receive": "on"}, BELOW
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
