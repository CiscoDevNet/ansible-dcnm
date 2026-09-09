# Phase 1 thin-engine unit tests (Monday slice: FLOWCONTROL_RECEIVE + OSPF-MD separation).
# Proves: intent survival (profile key -> parent nvPair), explicit-only emission, omission
# semantics, native string type, version fail-closed for a registered key, and that the
# engine transports OSPF-MD on supported versions while its 4-point unsupported-version
# behavior stays with the A1.4.4 compat hook (covered by test_dcnm_intf_ospfmd_have_fetch +
# test_dcnm_ospfmd_parent_child_contract).
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import hashlib
import importlib.util
import json
from pathlib import Path
import pytest
import yaml
from unittest import mock
from ansible_collections.cisco.dcnm.plugins.module_utils import (
    gie_binding_table,
    gie_engine,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    BINDING_TABLE, PROVENANCE_SHA256, registered_profile_keys, resolve_binding,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    gie_version_supported, gie_extend_prof_spec, gie_contribute_nvpairs,
    gie_validator_type, gie_all_registered_keys, gie_guarded_keys,
    gie_invalid_parent_key, gie_nvpair_keymap, gie_carry_forward_bindings,
    gie_validate_binding_value,
    GieBindingError,
)

TRUNK = "int_trunk_host"
ACCESS = "int_access_host"
LOOPBACK = "int_fabric_loopback_11_1"
PC_TRUNK = "int_port_channel_trunk_host"
PC_ACCESS = "int_port_channel_access_host"
PC_DOT1Q = "int_port_channel_dot1q_tunnel_host"

# The A1.5 slice, frozen. These three rows and their behaviour must not change.
A15_ROWS = {
    (ACCESS, "FLOWCONTROL_RECEIVE", "flowcontrol_receive"),
    (LOOPBACK, "ENABLE_OSPF_AUTH_MESSAGE_DIGEST", "enable_ospf_auth_message_digest"),
    (TRUNK, "FLOWCONTROL_RECEIVE", "flowcontrol_receive"),
}
# The A1.6 simple-passthrough slice: nine new rows from registry slices 0b_7/0b_8/0b_9.
A16_ROWS = {
    (TRUNK, "GUARD_MODE", "guard_mode"),
    (PC_TRUNK, "GUARD_MODE", "guard_mode"),
    (ACCESS, "DISABLE_LLDP", "disable_lldp"),
    (TRUNK, "DISABLE_LLDP", "disable_lldp"),
    (ACCESS, "ACL_FILTER", "acl_filter"),
    (TRUNK, "ACL_FILTER", "acl_filter"),
    (PC_ACCESS, "ACL_FILTER", "acl_filter"),
    (PC_TRUNK, "ACL_FILTER", "acl_filter"),
    (PC_DOT1Q, "ACL_FILTER", "acl_filter"),
}
# The A1.9 slice: the OSPF legacy-key pair, from registry slice 0b_10. Both rows feed the
# SAME child (ospf_interface_auth), so both are child_pti on the loopback parent.
A19_ROWS = {
    (LOOPBACK, "OSPF_AUTH_KEY_ID", "ospf_auth_key_id"),
    (LOOPBACK, "OSPF_AUTH_KEY", "ospf_auth_key"),
}


# ---- binding package (G1 runtime contract) ----

def test_package_provenance_and_size():
    expected_keys = A15_ROWS | A16_ROWS | A19_ROWS
    actual_keys = {
        (b["parent_template"], b["parent_nvpair"], b["profile_key"])
        for b in BINDING_TABLE
    }
    assert len(BINDING_TABLE) == len(actual_keys) == 14
    assert actual_keys == expected_keys
    # The A1.5 slice must survive verbatim inside the larger table.
    assert A15_ROWS <= actual_keys
    assert len(A16_ROWS) == 9
    assert len(A19_ROWS) == 2
    expected_provenance = hashlib.sha256(
        json.dumps(BINDING_TABLE, sort_keys=True, default=list).encode()
    ).hexdigest()
    assert PROVENANCE_SHA256 == expected_provenance


def _load_generator():
    path = (
        Path(gie_binding_table.__file__).resolve().parents[2]
        / "tools"
        / "gie_generate_binding_table.py"
    )
    spec = importlib.util.spec_from_file_location("gie_table_generator_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_compiler_accepts_exact_committed_binding_set():
    generator = _load_generator()
    rows = generator.compile_rows([dict(binding) for binding in BINDING_TABLE])
    assert len(rows) == 14


def test_compiler_rejects_duplicate_or_missing_binding():
    generator = _load_generator()
    rows = [dict(binding) for binding in BINDING_TABLE]
    with pytest.raises(ValueError, match="duplicate committed binding"):
        generator.compile_rows(rows + [dict(rows[0])])
    with pytest.raises(ValueError, match="missing committed bindings"):
        generator.compile_rows(rows[:-1])


def test_compiler_rejects_profile_key_mismatch():
    generator = _load_generator()
    rows = [dict(binding) for binding in BINDING_TABLE]
    rows[0]["profile_key"] = "wrong_key"
    with pytest.raises(ValueError, match="unexpected profile_key"):
        generator.compile_rows(rows)

def test_registered_keys_per_parent():
    assert registered_profile_keys(TRUNK) == {
        "flowcontrol_receive", "guard_mode", "disable_lldp", "acl_filter"
    }
    assert registered_profile_keys(ACCESS) == {
        "flowcontrol_receive", "disable_lldp", "acl_filter"
    }
    assert registered_profile_keys(LOOPBACK) == {
        "enable_ospf_auth_message_digest", "ospf_auth_key_id", "ospf_auth_key"
    }
    assert registered_profile_keys(PC_TRUNK) == {"guard_mode", "acl_filter"}
    assert registered_profile_keys(PC_ACCESS) == {"acl_filter"}
    assert registered_profile_keys(PC_DOT1Q) == {"acl_filter"}
    # GUARD_MODE is NOT registered on access parents; DISABLE_LLDP not on any pc parent.
    assert "guard_mode" not in registered_profile_keys(ACCESS)
    assert "guard_mode" not in registered_profile_keys(PC_ACCESS)
    assert "disable_lldp" not in registered_profile_keys(PC_TRUNK)

def test_flowcontrol_binding_shape():
    b = resolve_binding(TRUNK, "flowcontrol_receive")
    assert b["parent_nvpair"] == "FLOWCONTROL_RECEIVE"
    assert b["mechanism"] == "passthrough"
    assert b["type"] == "enum" and b["valid_values"] == ("on", "off")
    assert b["min_ndfc_version"] == "12.6.0.267"


def test_flowcontrol_public_documentation_is_enum_without_default():
    documentation = yaml.safe_load(dcnm_interface.DOCUMENTATION)
    option = documentation["options"]["config"]["suboptions"]["profile_eth"][
        "suboptions"
    ]["flowcontrol_receive"]
    assert option["type"] == "str"
    assert option["choices"] == ["on", "off"]
    assert "default" not in option


def test_registry_drives_comparator_keymap_and_carry_forward():
    assert gie_nvpair_keymap()["FLOWCONTROL_RECEIVE"] == "flowcontrol_receive"
    assert {
        (r["parent_nvpair"], r["profile_key"]) for r in gie_carry_forward_bindings(TRUNK)
    } == {
        ("FLOWCONTROL_RECEIVE", "flowcontrol_receive"),
        ("GUARD_MODE", "guard_mode"),
        ("DISABLE_LLDP", "disable_lldp"),
        ("ACL_FILTER", "acl_filter"),
    }
    assert gie_carry_forward_bindings(LOOPBACK) == []


def test_ambiguous_registry_nvpair_keymap_fails_closed(monkeypatch):
    conflicting = dict(BINDING_TABLE[0])
    conflicting["profile_key"] = "different_public_key"
    monkeypatch.setattr(
        gie_engine, "BINDING_TABLE", BINDING_TABLE + (conflicting,)
    )
    with pytest.raises(GieBindingError, match="ambiguous registered nvPair"):
        gie_nvpair_keymap()


@pytest.mark.parametrize("value", [True, "bogus", 1, None])
def test_binding_value_rejects_malformed_native_have(value):
    with pytest.raises(GieBindingError, match="authoritative controller value"):
        gie_validate_binding_value(
            TRUNK, "flowcontrol_receive", value, value_source="have"
        )


@pytest.mark.parametrize("value", ["on", "off"])
def test_binding_value_accepts_exact_native_enum(value):
    assert gie_validate_binding_value(TRUNK, "flowcontrol_receive", value) == value


# ---- FLOWCONTROL transport: intent survival + omission + native type ----

@pytest.mark.parametrize("val", ["on", "off"])
def test_flowcontrol_explicit_contributes_native_string(val):
    add, err = gie_contribute_nvpairs(TRUNK, {"mode": "trunk", "flowcontrol_receive": val}, "12.6.0.267")
    assert err is None
    assert add == {"FLOWCONTROL_RECEIVE": val}
    assert isinstance(add["FLOWCONTROL_RECEIVE"], str)

def test_flowcontrol_omitted_contributes_nothing():
    add, err = gie_contribute_nvpairs(ACCESS, {"mode": "access", "description": "x"}, "12.6.0.267")
    assert err is None and add == {}

def test_flowcontrol_present_on_both_parents():
    for p, m in [(TRUNK, "trunk"), (ACCESS, "access")]:
        add, err = gie_contribute_nvpairs(p, {"mode": m, "flowcontrol_receive": "on"}, "12.6.0.267")
        assert err is None and add == {"FLOWCONTROL_RECEIVE": "on"}


# ---- version fail-closed for a registered explicit key (FLOWCONTROL normal rule) ----

@pytest.mark.parametrize("ver", ["12.6.0.266", "12.5.9.999", None, "", "bogus", "12.x.0.1"])
def test_flowcontrol_below_or_bad_version_fails_closed(ver):
    add, err = gie_contribute_nvpairs(TRUNK, {"flowcontrol_receive": "on"}, ver)
    assert add is None and err is not None

@pytest.mark.parametrize("ver", ["12.6.0.267", "12.6.0.300", "12.7.0.1", "13.0.0.0"])
def test_flowcontrol_at_or_above_floor_ok(ver):
    add, err = gie_contribute_nvpairs(TRUNK, {"flowcontrol_receive": "off"}, ver)
    assert err is None and add == {"FLOWCONTROL_RECEIVE": "off"}

def test_version_supported_matches_semantics():
    assert gie_version_supported("12.6.0.267", "12.6.0.267") is True
    assert gie_version_supported("12.6.0.266", "12.6.0.267") is False
    assert gie_version_supported(None, "12.6.0.267") is False
    assert gie_version_supported("garbage", "12.6.0.267") is False


# ---- spec extension: explicit-only, no default ----

def test_extend_spec_adds_only_present_key_with_choices_no_default():
    spec = {"mode": {"type": "str"}}
    gie_extend_prof_spec(spec, TRUNK, {"mode": "trunk", "flowcontrol_receive": "on"})
    assert "flowcontrol_receive" in spec
    assert spec["flowcontrol_receive"]["choices"] == ["on", "off"]
    assert "default" not in spec["flowcontrol_receive"]

def test_extend_spec_skips_omitted_key():
    spec = {"mode": {"type": "str"}}
    gie_extend_prof_spec(spec, TRUNK, {"mode": "trunk"})
    assert "flowcontrol_receive" not in spec


# ---- B1: engine OWNS OSPF-MD binding resolution + supported-version transport (child_pti) ----

@pytest.mark.parametrize("val", [True, False])
def test_ospfmd_transported_by_engine_on_supported_version(val):
    # B1: the engine resolves the loopback binding and transports the NATIVE boolean nvPair on
    # a supported version. (Would fail if OSPF were excluded from engine resolution/transport.)
    add, err = gie_contribute_nvpairs(LOOPBACK, {"enable_ospf_auth_message_digest": val}, "12.6.0.267")
    assert err is None
    assert add == {"ENABLE_OSPF_AUTH_MESSAGE_DIGEST": val}
    assert isinstance(add["ENABLE_OSPF_AUTH_MESSAGE_DIGEST"], bool)

@pytest.mark.parametrize("val", [True, False])
@pytest.mark.parametrize("ver", ["12.6.0.266", None, "", "bogus"])
def test_ospfmd_withheld_not_failed_on_unsupported_version(val, ver):
    # child_pti: on an unsupported/unknown/malformed version the engine WITHHOLDS (no error),
    # so the module's capability gate + HAVE reconcile (compat hook) owns that path.
    add, err = gie_contribute_nvpairs(LOOPBACK, {"enable_ospf_auth_message_digest": val}, ver)
    assert err is None and add == {}

def test_ospfmd_binding_is_child_pti_boolean():
    b = resolve_binding(LOOPBACK, "enable_ospf_auth_message_digest")
    assert b["mechanism"] == "child_pti"
    assert b["type"] == "boolean"

def test_ospfmd_not_in_generic_eth_spec_extension():
    # OSPF-MD (child_pti) is transported via contribute, but is NOT part of the GENERIC eth spec
    # extension (it keeps its dedicated native-boolean validate). No feature branch either way.
    spec = {}
    gie_extend_prof_spec(spec, LOOPBACK, {"enable_ospf_auth_message_digest": True})
    assert "enable_ospf_auth_message_digest" not in spec

def test_narrow_rule_flowcontrol_uses_passthrough_not_child_pti():
    # FLOWCONTROL uses the version-gate/fail-closed rule, never the child_pti withhold semantics
    assert resolve_binding(TRUNK, "flowcontrol_receive")["mechanism"] == "passthrough"
    assert resolve_binding(LOOPBACK, "enable_ospf_auth_message_digest")["mechanism"] == "child_pti"


def test_non_ospf_child_pti_does_not_inherit_ospf_withhold(monkeypatch):
    synthetic = {
        "parent_template": "synthetic_parent",
        "parent_nvpair": "ENABLE_SYNTHETIC_CHILD",
        "profile_key": "enable_synthetic_child",
        "applicable_interface_type": "svi",
        "applicable_mode": "vlan",
        "type": "boolean",
        "default_template": False,
        "mechanism": "child_pti",
        "min_ndfc_version": "12.6.0.267",
    }
    monkeypatch.setattr(
        gie_binding_table,
        "BINDING_TABLE",
        gie_binding_table.BINDING_TABLE + (synthetic,),
    )
    add, err = gie_contribute_nvpairs(
        "synthetic_parent", {"enable_synthetic_child": True}, "12.6.0.266"
    )
    assert add is None
    assert err is not None


# ---- B4: validator type comes from binding metadata; unknown fails closed ----

def test_validator_type_mapping_known():
    assert gie_validator_type("boolean") == "bool"
    assert gie_validator_type("enum") == "str"
    assert gie_validator_type("string") == "str"
    assert gie_validator_type("integer") == "int"

@pytest.mark.parametrize("bad", ["nonsense", "", None, "list", "dict"])
def test_validator_type_unknown_fails_closed(bad):
    with pytest.raises(GieBindingError):
        gie_validator_type(bad)

def test_extend_spec_flowcontrol_enum_maps_to_str():
    spec = {}
    gie_extend_prof_spec(spec, TRUNK, {"flowcontrol_receive": "on"})
    assert spec["flowcontrol_receive"]["type"] == "str"

def test_contribute_preserves_native_types_no_stringification():
    # enum -> native str; boolean -> native bool (not the "True"/"true" string)
    a1, _ = gie_contribute_nvpairs(TRUNK, {"flowcontrol_receive": "on"}, "12.6.0.267")
    assert a1["FLOWCONTROL_RECEIVE"] == "on" and isinstance(a1["FLOWCONTROL_RECEIVE"], str)
    a2, _ = gie_contribute_nvpairs(LOOPBACK, {"enable_ospf_auth_message_digest": True}, "12.6.0.267")
    assert a2["ENABLE_OSPF_AUTH_MESSAGE_DIGEST"] is True


# ---- B2: registry-known key on an invalid desired parent -> fail closed (engine helper) ----

def test_all_registered_and_guarded_keys():
    assert gie_all_registered_keys() == {
        "flowcontrol_receive", "enable_ospf_auth_message_digest",
        "guard_mode", "disable_lldp", "acl_filter",
        "ospf_auth_key_id", "ospf_auth_key",
    }
    # only passthrough keys are generically guarded; child_pti (OSPF-MD) keeps its own validate
    assert gie_guarded_keys() == {
        "flowcontrol_receive", "guard_mode", "disable_lldp", "acl_filter",
    }
    assert "enable_ospf_auth_message_digest" not in gie_guarded_keys()
    # A1.9: the legacy-key pair is child_pti, so registering it must NOT hand the engine the
    # invalid-parent guard. dcnm_intf_validate_ospf_auth_key_input owns that check and its
    # error message ("supported only on fabric loopback interfaces...") is observable
    # contract; a generic guard firing first would silently change it.
    assert "ospf_auth_key_id" not in gie_guarded_keys()
    assert "ospf_auth_key" not in gie_guarded_keys()

def test_invalid_parent_key_flags_flowcontrol_on_wrong_parent():
    # routed/monitor/dot1q eth parents do not register flowcontrol_receive
    for parent in ("int_routed_host", "int_monitor_ethernet", "int_dot1q_tunnel_host", None):
        assert gie_invalid_parent_key(parent, ["mode", "flowcontrol_receive"]) == "flowcontrol_receive"

def test_invalid_parent_key_ok_on_valid_parents():
    assert gie_invalid_parent_key(TRUNK, ["mode", "flowcontrol_receive"]) is None
    assert gie_invalid_parent_key(ACCESS, ["mode", "flowcontrol_receive"]) is None

def test_invalid_parent_key_ignores_wholly_unknown_field():
    # a field not in the registry is left to the legacy discard path (not reported here)
    assert gie_invalid_parent_key("int_routed_host", ["mode", "some_legacy_field"]) is None


def _parent_guard_obj(profile):
    obj = object.__new__(dcnm_interface.DcnmIntf)
    obj.config = [{"name": "eth1/4", "type": "eth", "profile": profile}]
    obj.dcnm_version = 12
    obj.pol_types = {12: {
        "eth_trunk": TRUNK,
        "eth_access": ACCESS,
        "eth_routed": "int_routed_host",
    }}
    obj.module = mock.Mock()
    obj.module.fail_json.side_effect = RuntimeError("fail_json")
    return obj


def test_module_parent_guard_rejects_registered_key_before_legacy_filtering():
    obj = _parent_guard_obj({"mode": "routed", "flowcontrol_receive": "on"})
    with pytest.raises(RuntimeError, match="fail_json"):
        obj.dcnm_intf_gie_validate_parent_bindings()
    assert "flowcontrol_receive" in obj.module.fail_json.call_args.kwargs["msg"]
    assert "No template metadata was queried and no change was sent" in (
        obj.module.fail_json.call_args.kwargs["msg"]
    )


def test_module_parent_guard_accepts_both_registered_parents():
    for mode in ("trunk", "access"):
        obj = _parent_guard_obj({"mode": mode, "flowcontrol_receive": "on"})
        obj.dcnm_intf_gie_validate_parent_bindings()
        obj.module.fail_json.assert_not_called()


def test_module_parent_guard_preserves_unknown_legacy_discard_behavior():
    obj = _parent_guard_obj({"mode": "routed", "unknown_legacy_key": "x"})
    obj.dcnm_intf_gie_validate_parent_bindings()
    obj.module.fail_json.assert_not_called()


# ---- module path: intent survives profile -> validated field -> parent nvPair -> payload ----

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface  # noqa: E402


def _trunk_delem(val=None):
    prof = {"mode": "trunk", "bpdu_guard": "true", "port_type_fast": True, "mtu": "jumbo",
            "speed": "Auto", "allowed_vlans": "all", "native_vlan": "", "orphan_port": False,
            "cmds": None, "description": "test", "admin_state": True, "enable_cdp": True,
            "enable_pfc": False, "enable_monitor": False, "duplex": "auto", "enable_qos": False,
            "qos_policy": "", "queuing_policy": "", "fec": "auto"}
    if val is not None:
        prof["flowcontrol_receive"] = val
    return {"name": "eth1/4", "type": "eth", "switch": ["10.1.1.1"], "deploy": True, "profile": prof}


def _intf_trunk():
    return {"deploy": True, "policy": "int_trunk_host", "interfaceType": "INTERFACE_ETHERNET",
            "interfaces": [{"serialNumber": "", "interfaceType": "INTERFACE_ETHERNET", "ifName": "",
                            "fabricName": "test_fabric", "nvPairs": {"SPEED": "Auto"}}]}


def _intf_obj(ndfc_version):
    m = object.__new__(dcnm_interface.DcnmIntf)
    m.ndfc_version = ndfc_version
    return m


def test_module_path_flowcontrol_on_reaches_payload_nvpair():
    m, intf = _intf_obj("12.6.0.267"), _intf_trunk()
    m.dcnm_intf_get_eth_payload(_trunk_delem("on"), intf, "profile")
    assert intf["interfaces"][0]["nvPairs"]["FLOWCONTROL_RECEIVE"] == "on"

def test_module_path_flowcontrol_off_reaches_payload_nvpair():
    m, intf = _intf_obj("12.6.0.267"), _intf_trunk()
    m.dcnm_intf_get_eth_payload(_trunk_delem("off"), intf, "profile")
    assert intf["interfaces"][0]["nvPairs"]["FLOWCONTROL_RECEIVE"] == "off"

def test_module_path_flowcontrol_omitted_absent_from_payload():
    m, intf = _intf_obj("12.6.0.267"), _intf_trunk()
    m.dcnm_intf_get_eth_payload(_trunk_delem(None), intf, "profile")
    assert "FLOWCONTROL_RECEIVE" not in intf["interfaces"][0]["nvPairs"]


# ---- module compare/HAVE path: idempotency, preservation, parent transition ----

_OMITTED = object()


def _compare_payload(parent, flow=_OMITTED, description="same"):
    nvpairs = {"DESC": description}
    if flow is not _OMITTED:
        nvpairs["FLOWCONTROL_RECEIVE"] = flow
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


def _compare_obj(state, parent, want_flow=_OMITTED, have_flow=_OMITTED,
                 want_description="same", have_description="same",
                 have_parent=None):
    module = mock.Mock()
    module.params = {"fabric": "FAB1", "config": [], "state": state}
    module.check_mode = False
    with mock.patch.object(
        dcnm_interface, "dcnm_version_supported",
        return_value=(12, "12.6.0.267"),
    ):
        obj = dcnm_interface.DcnmIntf(module)
    obj.want = [_compare_payload(parent, want_flow, want_description)]
    have = _compare_payload(
        have_parent or parent, have_flow, have_description
    )
    have.pop("deploy")
    obj.have = [have]
    pb = {
        "ifname": "Ethernet1/4",
        "sno": "SN1",
        "fabric": "FAB1",
        "policy": parent,
        "description": want_description,
    }
    if want_flow is not _OMITTED:
        pb["flowcontrol_receive"] = want_flow
    obj.pb_input = [pb]
    return obj


@pytest.mark.parametrize("parent", [TRUNK, ACCESS])
@pytest.mark.parametrize("value", ["on", "off"])
def test_flowcontrol_compare_idempotent_on_both_parents(parent, value):
    obj = _compare_obj("merged", parent, value, value)
    obj.dcnm_intf_compare_want_and_have("merged")
    assert obj.diff_replace == []
    assert obj.changed_dict[0]["merged"] == []


@pytest.mark.parametrize("parent", [TRUNK, ACCESS])
@pytest.mark.parametrize("state", ["merged", "replaced", "overridden"])
def test_flowcontrol_compare_drift_is_exact_native_delta(parent, state):
    obj = _compare_obj(state, parent, "off", "on")
    obj.dcnm_intf_compare_want_and_have(state)
    assert len(obj.diff_replace) == 1
    sent = obj.diff_replace[0]["interfaces"][0]["nvPairs"]
    assert sent["FLOWCONTROL_RECEIVE"] == "off"
    assert isinstance(sent["FLOWCONTROL_RECEIVE"], str)
    reported = obj.changed_dict[0][state][0]["interfaces"][0]["nvPairs"]
    assert reported == {"FLOWCONTROL_RECEIVE": "off"}


@pytest.mark.parametrize("parent", [TRUNK, ACCESS])
@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_omitted_flowcontrol_is_carried_from_have_on_unrelated_update(parent, state):
    obj = _compare_obj(
        state, parent, _OMITTED, "on",
        want_description="new", have_description="old",
    )
    obj.dcnm_intf_compare_want_and_have(state)
    sent = obj.diff_replace[0]["interfaces"][0]["nvPairs"]
    assert sent["FLOWCONTROL_RECEIVE"] == "on"
    reported = obj.changed_dict[0][state][0]["interfaces"][0]["nvPairs"]
    assert reported == {"DESC": "new"}


@pytest.mark.parametrize("parent", [TRUNK, ACCESS])
@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("malformed", [True, "bogus"])
def test_malformed_have_flowcontrol_fails_before_diff(
    parent, state, malformed
):
    obj = _compare_obj(
        state, parent, _OMITTED, malformed,
        want_description="new", have_description="old",
    )
    obj.module.fail_json.side_effect = RuntimeError("fail closed")
    with pytest.raises(RuntimeError, match="fail closed"):
        obj.dcnm_intf_compare_want_and_have(state)
    msg = obj.module.fail_json.call_args.kwargs["msg"]
    assert "authoritative controller value" in msg
    assert "no change was sent" in msg
    assert obj.diff_replace == []


def test_explicit_flowcontrol_survives_legacy_parent_transition():
    obj = _compare_obj(
        "replaced", TRUNK, "on", _OMITTED,
        have_parent="int_routed_host",
    )
    obj.dcnm_intf_compare_want_and_have("replaced")
    assert obj.diff_replace[0]["policy"] == TRUNK
    assert (
        obj.diff_replace[0]["interfaces"][0]["nvPairs"]["FLOWCONTROL_RECEIVE"]
        == "on"
    )


def test_missing_have_uses_existing_authority_gate_before_diff():
    obj = _compare_obj("merged", TRUNK, "on", _OMITTED)
    obj.have = []
    obj.dcnm_intf_require_detail_authority = mock.Mock(
        side_effect=RuntimeError("authoritative HAVE unavailable")
    )
    with pytest.raises(RuntimeError, match="authoritative HAVE unavailable"):
        obj.dcnm_intf_compare_want_and_have("merged")
    obj.dcnm_intf_require_detail_authority.assert_called_once_with(
        "Ethernet1/4", "SN1"
    )
    assert obj.diff_create == [] and obj.diff_replace == []


def test_check_mode_diff_keeps_native_flowcontrol_string():
    obj = _compare_obj("merged", TRUNK, "off", "on")
    obj.module.check_mode = True
    obj.dcnm_intf_compare_want_and_have("merged")
    value = obj.changed_dict[0]["merged"][0]["interfaces"][0]["nvPairs"][
        "FLOWCONTROL_RECEIVE"
    ]
    assert value == "off" and isinstance(value, str)


def test_query_keeps_controller_flowcontrol_string_without_normalization(monkeypatch):
    obj = _compare_obj("query", TRUNK)
    obj.intf_info = [{"name": "eth1/4", "switch": ["leaf-101"]}]
    obj.ip_sn = {"leaf-101": "SN1"}
    obj.dcnm_extract_if_name = lambda info: (
        "Ethernet1/4", "INTERFACE_ETHERNET"
    )
    raw = {"nvPairs": {"FLOWCONTROL_RECEIVE": "on"}}
    monkeypatch.setattr(
        dcnm_interface,
        "dcnm_send",
        lambda module, method, path: {"RETURN_CODE": 200, "DATA": [raw]},
    )
    obj.dcnm_intf_get_diff_query()
    assert obj.result["response"][0]["nvPairs"]["FLOWCONTROL_RECEIVE"] == "on"
    assert isinstance(
        obj.changed_dict[0]["query"][0]["nvPairs"]["FLOWCONTROL_RECEIVE"],
        str,
    )


# ---- A1.9: exact registry contract for the OSPF legacy-key pair ----

def test_a19_legacy_key_pair_registry_fields():
    """Pin the fields that drive behaviour, not just the row's identity.

    `type` decides the native type the engine enforces and transports; `mechanism` decides
    whether the key is generically guarded and whether it is carried forward; and
    `min_ndfc_version` is the version gate. A silent change to any of them alters what the
    module sends without changing the row count that the other tests watch.
    """
    key_id = resolve_binding(LOOPBACK, "ospf_auth_key_id")
    key = resolve_binding(LOOPBACK, "ospf_auth_key")
    assert key_id is not None and key is not None

    assert key_id["parent_nvpair"] == "OSPF_AUTH_KEY_ID"
    assert key_id["type"] == "integer"
    assert key["parent_nvpair"] == "OSPF_AUTH_KEY"
    assert key["type"] == "string"
    assert key["min_length"] == 1

    # Both feed the SAME child (ospf_interface_auth), so both are child_pti. Registering
    # either as passthrough would hand the engine the invalid-parent guard and the
    # carry-forward, both of which belong to the dedicated validator.
    for b in (key_id, key):
        assert b["mechanism"] == "child_pti"
        assert b["applicable_interface_type"] == "lo"
        assert b["applicable_mode"] == "fabric"
        assert b["min_ndfc_version"] == "12.6.0.267"

    # No numeric-range field is registered: the [0,255] check stays in
    # dcnm_intf_validate_ospf_auth_key_input, mirroring how the boolean kept its validator.
    assert "min_value" not in key_id and "max_value" not in key_id


def test_a19_pair_is_not_carried_forward():
    """child_pti bindings must stay out of the passthrough carry-forward set.

    Carry-forward preserves an authoritative HAVE value when the key is omitted. For this
    pair, omission is how the operator CLEARS the key, so carrying it forward would make
    removal impossible.
    """
    carried = {b["profile_key"] for b in gie_carry_forward_bindings(LOOPBACK)}
    assert carried.isdisjoint({"ospf_auth_key_id", "ospf_auth_key"})


# ---- native-type acceptance: str SUBCLASSES must pass (regression guard) ----
#
# Ansible never hands a module a plain `str`. A value that came from a playbook arrives as
# AnsibleUnicode, a str subclass. The engine originally checked `type(value) is native_type`,
# which is exact and rejects subclasses, so every string/enum binding was unusable end to end
# while these unit tests -- passing literal `str` -- kept passing.
#
# Every case below is therefore driven with a subclass, not a plain str. A locally defined
# subclass proves the semantics independently of the Ansible version; the AnsibleUnicode case
# proves the real one.


class _SubStr(str):
    """Stand-in for AnsibleUnicode: any str subclass must be accepted."""


def _ansible_unicode(value):
    try:
        from ansible.parsing.yaml.objects import AnsibleUnicode
    except ImportError:  # pragma: no cover - depends on the installed ansible-core
        return None
    return AnsibleUnicode(value)


@pytest.mark.parametrize("wrap", [_SubStr, _ansible_unicode], ids=["str_subclass", "AnsibleUnicode"])
def test_string_and_enum_bindings_accept_str_subclasses(wrap):
    key = wrap("a667d47acc18ea6b")
    if key is None:
        pytest.skip("AnsibleUnicode not importable in this ansible-core")
    # A1.9 string binding
    assert gie_validate_binding_value(LOOPBACK, "ospf_auth_key", key) == key
    # A1.5 enum binding and A1.6 string binding: the same defect made these unusable too.
    assert gie_validate_binding_value(TRUNK, "flowcontrol_receive", wrap("on")) == "on"
    assert gie_validate_binding_value(TRUNK, "acl_filter", wrap("MY_ACL")) == "MY_ACL"


def test_accepting_subclasses_does_not_make_bool_and_int_interchangeable():
    """isinstance(True, int) is True in Python, so a naive isinstance relaxation would let a
    boolean satisfy an integer binding and reach NDFC as 1 (or an int satisfy a boolean).
    """
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(LOOPBACK, "ospf_auth_key_id", True)
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(LOOPBACK, "enable_ospf_auth_message_digest", 1)
    # and the legitimate natives still pass
    assert gie_validate_binding_value(LOOPBACK, "ospf_auth_key_id", 17) == 17
    assert gie_validate_binding_value(LOOPBACK, "enable_ospf_auth_message_digest", True) is True


def test_subclass_acceptance_does_not_bypass_the_other_registered_checks():
    """Relaxing the type check must not relax length or choices."""
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(LOOPBACK, "ospf_auth_key", _SubStr(""))  # min_length 1
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(TRUNK, "flowcontrol_receive", _SubStr("nope"))
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(LOOPBACK, "ospf_auth_key", 17)  # int is not a string


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
