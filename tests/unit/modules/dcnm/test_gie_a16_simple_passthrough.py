"""A1.6 simple-passthrough slice: nine new registered bindings.

Covers, proportional to every value type (enum / boolean / string-with-length):
positive transport on a supported version, omission, wrong parent, exact native type,
enum + length constraints, unsupported/unknown/malformed versions, same-parent
carry-forward, malformed HAVE, and the generator/table integrity guards.

Also regresses the A1.5 slice (OSPF-MD + FLOWCONTROL_RECEIVE) to prove it is byte- and
behaviour-compatible after the table grew from 3 rows to 12.

Offline. No controller, Nexus or Jenkins.
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
    registered_profile_keys,
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

# (parent, profile_key, nvpair, a valid explicit value)
NINE = (
    (TRUNK, "guard_mode", "GUARD_MODE", "root"),
    (PC_TRUNK, "guard_mode", "GUARD_MODE", "loop"),
    (ACCESS, "disable_lldp", "DISABLE_LLDP", True),
    (TRUNK, "disable_lldp", "DISABLE_LLDP", False),
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
def test_table_has_fourteen_unique_rows():
    # 12 (A1.5 + A1.6) + 2 (A1.9: the OSPF legacy-key pair on int_fabric_loopback_11_1).
    keys = [(b["parent_template"], b["parent_nvpair"]) for b in BINDING_TABLE]
    assert len(BINDING_TABLE) == 14
    assert len(set(keys)) == 14, "duplicate (parent, nvpair) row"
    pk_keys = [(b["parent_template"], b["profile_key"]) for b in BINDING_TABLE]
    assert len(set(pk_keys)) == 14, "duplicate (parent, profile_key) row"


def test_provenance_recalculates_from_packaged_rows():
    expected = hashlib.sha256(
        json.dumps(BINDING_TABLE, sort_keys=True, default=list).encode()
    ).hexdigest()
    assert PROVENANCE_SHA256 == expected, "packaged table edited after generation"


def test_nine_new_bindings_are_present_with_reviewed_metadata():
    for parent, pk, nvpair, _ in NINE:
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

    lldp = resolve_binding(ACCESS, "disable_lldp")
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
        (ACCESS, "disable_lldp"): ("eth", "access"),
        (TRUNK, "disable_lldp"): ("eth", "trunk"),
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
    rows = [dict(b) for b in BINDING_TABLE]
    assert len(gen.compile_rows(rows)) == 14

    with pytest.raises(ValueError, match="duplicate committed binding"):
        gen.compile_rows(rows + [dict(rows[0])])

    with pytest.raises(ValueError, match="missing committed bindings"):
        gen.compile_rows(rows[:-1])

    wrong = [dict(r) for r in rows]
    wrong[0]["profile_key"] = "not_the_reviewed_key"
    with pytest.raises(ValueError, match="unexpected profile_key"):
        gen.compile_rows(wrong)


def test_generator_rejects_an_unexpected_binding_claiming_a_committed_key():
    """A non-committed parent reusing a committed public key must fail, not be skipped.

    int_vpc_trunk_host::GUARD_MODE is child_pti in the ledger. Silently skipping it would
    make a non-passthrough binding look merely 'not selected'.
    """
    gen = _load_generator()
    rows = [dict(b) for b in BINDING_TABLE]
    rows.append({
        "parent_template": "int_vpc_trunk_host",
        "parent_nvpair": "GUARD_MODE",
        "profile_key": "guard_mode",
        "type": "enum",
        "mechanism": "child_pti",
        "min_ndfc_version": SUPPORTED,
    })
    with pytest.raises(ValueError, match="unexpected binding"):
        gen.compile_rows(rows)


def test_generator_still_ignores_unrelated_uncommitted_rows():
    """A row with no committed public key is simply not selected (legacy behaviour)."""
    gen = _load_generator()
    rows = [dict(b) for b in BINDING_TABLE]
    rows.append({
        "parent_template": "int_routed_host",
        "parent_nvpair": "ARP_TIMEOUT",
        "profile_key": "arp_timeout",
        "type": "integer",
        "mechanism": "child_pti",
        "min_ndfc_version": SUPPORTED,
    })
    assert len(gen.compile_rows(rows)) == 14


# ------------------------------------------------------------------ positive transport
@pytest.mark.parametrize("parent,pk,nvpair,value", NINE)
def test_supported_version_transports_the_native_value(parent, pk, nvpair, value):
    add, err = gie_contribute_nvpairs(parent, {pk: value}, SUPPORTED)
    assert err is None
    assert add == {nvpair: value}
    assert type(add[nvpair]) is type(value)


def test_every_guard_mode_choice_transports():
    for parent in (TRUNK, PC_TRUNK):
        for value in GUARD_VALUES:
            add, err = gie_contribute_nvpairs(parent, {"guard_mode": value}, SUPPORTED)
            assert err is None and add == {"GUARD_MODE": value}
            assert type(add["GUARD_MODE"]) is str


def test_disable_lldp_transports_both_booleans():
    for parent in (ACCESS, TRUNK):
        for value in (True, False):
            add, err = gie_contribute_nvpairs(parent, {"disable_lldp": value}, SUPPORTED)
            assert err is None and add == {"DISABLE_LLDP": value}
            assert type(add["DISABLE_LLDP"]) is bool


def test_acl_filter_accepts_boundary_lengths():
    for parent in (ACCESS, TRUNK, PC_ACCESS, PC_TRUNK, PC_DOT1Q):
        for value in ("A", "A" * 64):
            add, err = gie_contribute_nvpairs(parent, {"acl_filter": value}, SUPPORTED)
            assert err is None and add == {"ACL_FILTER": value}


def test_multiple_new_keys_on_one_parent_contribute_together():
    add, err = gie_contribute_nvpairs(
        TRUNK,
        {"guard_mode": "root", "disable_lldp": True, "acl_filter": "ACL_X",
         "flowcontrol_receive": "on"},
        SUPPORTED,
    )
    assert err is None
    assert add == {
        "GUARD_MODE": "root",
        "DISABLE_LLDP": True,
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
        spec, TRUNK, {"guard_mode": "root", "disable_lldp": True, "acl_filter": "A"}
    )
    assert set(spec) == {"guard_mode", "disable_lldp", "acl_filter"}
    for entry in spec.values():
        assert "default" not in entry, "a default would author intent on omission"
    assert spec["guard_mode"]["type"] == "str"
    assert spec["guard_mode"]["choices"] == list(GUARD_VALUES)
    assert spec["disable_lldp"]["type"] == "bool"
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
            gie_validate_binding_value(ACCESS, "disable_lldp", bad)


def test_string_rejects_non_strings():
    for bad in (True, False, 1, None, [], {}):
        with pytest.raises(GieBindingError):
            gie_validate_binding_value(ACCESS, "acl_filter", bad)


def test_acl_filter_length_constraints_are_enforced():
    with pytest.raises(GieBindingError, match="shorter than the registered minimum"):
        gie_validate_binding_value(ACCESS, "acl_filter", "")
    with pytest.raises(GieBindingError, match="longer than the registered maximum"):
        gie_validate_binding_value(ACCESS, "acl_filter", "A" * 65)


def test_errors_never_echo_the_rejected_value():
    # Each probe must actually be rejected, and each carries a distinctive marker token so
    # the assertion below is meaningful. A 15-char ACL name is VALID (within 1..64), so the
    # ACL probe reaches rejection via length instead.
    probes = [
        (TRUNK, "guard_mode", "marker-enum-value"),
        (ACCESS, "acl_filter", "marker-acl-name" + "B" * 60),
        (ACCESS, "disable_lldp", "marker-not-a-bool"),
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
@pytest.mark.parametrize("pk", ["guard_mode", "disable_lldp", "acl_filter"])
def test_new_keys_are_generically_guarded(pk):
    assert pk in gie_guarded_keys()


def test_wrong_parent_is_reported_for_each_new_key():
    cases = [
        ("guard_mode", [ACCESS, PC_ACCESS, PC_DOT1Q, "int_routed_host",
                        "int_vpc_trunk_host", None]),
        ("disable_lldp", [PC_TRUNK, PC_ACCESS, PC_DOT1Q, "int_routed_host",
                          "int_vpc_access_host", None]),
        ("acl_filter", ["int_routed_host", "int_vpc_trunk_host", LOOPBACK, None]),
    ]
    for pk, parents in cases:
        for parent in parents:
            assert gie_invalid_parent_key(parent, [pk]) == pk, (
                f"{pk} must be rejected on {parent}"
            )


def test_correct_parents_are_accepted():
    for parent, pk, _, _ in NINE:
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
        ("GUARD_MODE", "guard_mode"),
        ("DISABLE_LLDP", "disable_lldp"),
        ("ACL_FILTER", "acl_filter"),
    }
    assert {
        (r["parent_nvpair"], r["profile_key"]) for r in gie_carry_forward_bindings(ACCESS)
    } == {
        ("FLOWCONTROL_RECEIVE", "flowcontrol_receive"),
        ("DISABLE_LLDP", "disable_lldp"),
        ("ACL_FILTER", "acl_filter"),
    }
    assert {
        (r["parent_nvpair"], r["profile_key"]) for r in gie_carry_forward_bindings(PC_TRUNK)
    } == {("GUARD_MODE", "guard_mode"), ("ACL_FILTER", "acl_filter")}
    assert gie_carry_forward_bindings(LOOPBACK) == []


def test_carry_forward_accepts_only_exact_authoritative_have_values():
    for value in GUARD_VALUES:
        assert gie_validate_binding_value(
            TRUNK, "guard_mode", value, value_source="have"
        ) == value
    for value in (True, False):
        assert gie_validate_binding_value(
            ACCESS, "disable_lldp", value, value_source="have"
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
            ACCESS, "disable_lldp", value, value_source="have"
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
        (ACCESS, "disable_lldp", 1),
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
    assert km["DISABLE_LLDP"] == "disable_lldp"
    assert km["ACL_FILTER"] == "acl_filter"
    assert km["FLOWCONTROL_RECEIVE"] == "flowcontrol_receive"
    assert km["ENABLE_OSPF_AUTH_MESSAGE_DIGEST"] == "enable_ospf_auth_message_digest"
    assert km["OSPF_AUTH_KEY_ID"] == "ospf_auth_key_id"
    assert km["OSPF_AUTH_KEY"] == "ospf_auth_key"
    assert len(km) == 7


def test_all_registered_keys():
    assert gie_all_registered_keys() == {
        "flowcontrol_receive", "enable_ospf_auth_message_digest",
        "guard_mode", "disable_lldp", "acl_filter",
        "ospf_auth_key_id", "ospf_auth_key",
    }


def test_idempotent_same_value_produces_the_same_payload():
    """The comparator sees a stable native value, so a repeat run diffs to nothing new."""
    for parent, pk, nvpair, value in NINE:
        first, err1 = gie_contribute_nvpairs(parent, {pk: value}, SUPPORTED)
        second, err2 = gie_contribute_nvpairs(parent, {pk: value}, SUPPORTED)
        assert err1 is None and err2 is None
        assert first == second == {nvpair: value}


# ------------------------------------------------------------------ A1.5 regression
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


def test_a15_ospf_md_contract_and_compat_exception_are_unchanged():
    b = resolve_binding(LOOPBACK, "enable_ospf_auth_message_digest")
    assert b["parent_nvpair"] == "ENABLE_OSPF_AUTH_MESSAGE_DIGEST"
    assert b["type"] == "boolean"
    assert b["default_template"] is False
    assert b["mechanism"] == "child_pti"
    assert b["min_ndfc_version"] == SUPPORTED

    for value in (True, False):
        add, err = gie_contribute_nvpairs(
            LOOPBACK, {"enable_ospf_auth_message_digest": value}, SUPPORTED
        )
        assert err is None and add == {"ENABLE_OSPF_AUTH_MESSAGE_DIGEST": value}
        assert type(add["ENABLE_OSPF_AUTH_MESSAGE_DIGEST"]) is bool

    # The one compatibility exception: withhold, never fail.
    for version in UNSUPPORTED_VERSIONS:
        add, err = gie_contribute_nvpairs(
            LOOPBACK, {"enable_ospf_auth_message_digest": True}, version
        )
        assert err is None, f"OSPF-MD@{version!r} must withhold, not fail"
        assert add == {}


def test_ospf_md_is_still_not_generically_guarded():
    assert "enable_ospf_auth_message_digest" not in gie_guarded_keys()
    # A1.9 added the legacy-key pair to the same parent. Both are child_pti, so neither is
    # generically guarded either: dcnm_intf_validate_ospf_auth_key_input keeps ownership of
    # the parent/mode check and of its exact error message.
    assert registered_profile_keys(LOOPBACK) == {
        "enable_ospf_auth_message_digest", "ospf_auth_key_id", "ospf_auth_key"
    }
    assert gie_guarded_keys().isdisjoint({"ospf_auth_key_id", "ospf_auth_key"})


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
