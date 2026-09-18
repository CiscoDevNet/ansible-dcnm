"""The authentication lot through its whole life: apply, repeat, rotate, omit, withdraw.

Offline, at the engine boundary. What a stage means here:

  APPLY     an explicit value reaches the parent nvPair, in wire form
  REPEAT    the same input twice produces the same payload -- no key is re-pushed for having
            been read back as a string
  ROTATE    changing only the key changes only the key
  OMIT      an omitted field is not emitted, and the controller's value is carried forward
            rather than blanked
  WITHDRAW  the shape a removal takes, and what it must NOT do silently

Every stage runs against all three parents, because the lot is one slice for three parents and
that shortcut is only sound while they behave identically.

NOT LIVE TESTED IN THIS GENERATION. No controller, Nexus or Jenkins is contacted. What is
asserted is what the module hands the transport -- the device-level half belongs to the live
cycles, per parent and per state.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    gie_carry_forward_bindings,
    gie_contribute_nvpairs,
    gie_invalid_parent_key,
    gie_validate_binding_value,
    GieBindingError,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    resolve_binding,
)

PARENTS = ["int_routed_host", "int_subif", "int_vlan"]
NDFC = "12.6.0.267"

KEY_A = "3DES-KEY-ALPHA"
KEY_B = "3DES-KEY-BRAVO"

# A complete, valid authentication intent. Written once: every stage below is a delta on it, so
# a stage that fails points at the delta and not at the setup.
AUTH = {
    "enable_ospf_auth": True,
    "ospf_auth_key_id": 7,
    "ospf_auth_key": KEY_A,
    "ospf_authentication_key_type": "3",
    "ospf_authentication_key": "AUTHENTICATION-KEY-ALPHA",
}
AUTH_NVPAIRS = {
    "ENABLE_OSPF_AUTH": "true",
    "OSPF_AUTH_KEY_ID": "7",
    "OSPF_AUTH_KEY": KEY_A,
    "OSPF_AUTHENTICATION_KEY_TYPE": "3",
    "OSPF_AUTHENTICATION_KEY": "AUTHENTICATION-KEY-ALPHA",
}


def _emit(parent, profile):
    nvpairs, error = gie_contribute_nvpairs(parent, profile, NDFC)
    assert error is None, error
    return nvpairs


# =====================================================================================
# APPLY
# =====================================================================================
@pytest.mark.parametrize("parent", PARENTS)
def test_apply_puts_every_field_on_the_wire_in_controller_form(parent):
    emitted = _emit(parent, dict(AUTH))
    for nvpair, expected in AUTH_NVPAIRS.items():
        assert emitted[nvpair] == expected, nvpair
        assert type(emitted[nvpair]) is str, (  # pylint: disable=unidiomatic-typecheck
            "{0} left as a native Python value; nvPairs is a string-valued map and a native "
            "bool or int never converges against what NDFC returns".format(nvpair)
        )


@pytest.mark.parametrize("parent", PARENTS)
def test_apply_emits_the_authentication_family_and_nothing_else(parent):
    """An OSPF-auth intent must not drag unrelated OSPF nvPairs along with it."""
    emitted = _emit(parent, dict(AUTH))
    assert set(emitted) == set(AUTH_NVPAIRS), (
        "extra nvPairs were emitted for an authentication-only profile: {0}".format(
            sorted(set(emitted) - set(AUTH_NVPAIRS)))
    )


@pytest.mark.parametrize("parent", PARENTS)
def test_the_boolean_gate_travels_as_a_string_not_a_python_bool(parent):
    """ENABLE_OSPF_AUTH is the gate; if it never converges the whole family re-pushes."""
    assert _emit(parent, {"enable_ospf_auth": True})["ENABLE_OSPF_AUTH"] == "true"
    assert _emit(parent, {"enable_ospf_auth": False})["ENABLE_OSPF_AUTH"] == "false"


# =====================================================================================
# REPEAT
# =====================================================================================
@pytest.mark.parametrize("parent", PARENTS)
def test_repeat_produces_a_byte_identical_payload(parent):
    assert _emit(parent, dict(AUTH)) == _emit(parent, dict(AUTH))


@pytest.mark.parametrize("parent", PARENTS)
def test_the_controller_string_form_of_every_field_is_accepted_back(parent):
    """The HAVE side of repetition.

    NDFC returns every nvPair as a string: "true", "7", "3". Those come back through the
    comparator, and a validator that only accepted native types would reject the controller's
    own answer -- reporting a change on every run for a config nobody touched.
    """
    for key, wire in (("enable_ospf_auth", "true"), ("ospf_auth_key_id", "7"),
                      ("ospf_authentication_key_type", "3"), ("ospf_auth_key", KEY_A)):
        gie_validate_binding_value(parent, key, wire, value_source="have")


# =====================================================================================
# ROTATE
# =====================================================================================
@pytest.mark.parametrize("parent", PARENTS)
def test_rotating_the_key_changes_that_field_and_only_that_field(parent):
    before = _emit(parent, dict(AUTH))
    after = _emit(parent, dict(AUTH, ospf_auth_key=KEY_B))
    assert after["OSPF_AUTH_KEY"] == KEY_B
    moved = {k for k in before if before[k] != after[k]}
    assert moved == {"OSPF_AUTH_KEY"}, "rotation also moved {0}".format(moved - {"OSPF_AUTH_KEY"})


@pytest.mark.parametrize("parent", PARENTS)
def test_rotating_the_key_id_alongside_the_key_moves_exactly_those_two(parent):
    """The realistic rotation: a new key under a new id, with the old pair still on the device."""
    before = _emit(parent, dict(AUTH))
    after = _emit(parent, dict(AUTH, ospf_auth_key=KEY_B, ospf_auth_key_id=8))
    assert (after["OSPF_AUTH_KEY"], after["OSPF_AUTH_KEY_ID"]) == (KEY_B, "8")
    assert {k for k in before if before[k] != after[k]} == {"OSPF_AUTH_KEY", "OSPF_AUTH_KEY_ID"}


@pytest.mark.parametrize("parent", PARENTS)
def test_a_key_id_outside_the_template_range_is_refused_before_anything_is_sent(parent):
    """0-255 comes from the template. A rotation typo must fail, not truncate."""
    for bad in (-1, 256):
        with pytest.raises(GieBindingError):
            gie_validate_binding_value(parent, "ospf_auth_key_id", bad,
                                       value_source="explicit")


# =====================================================================================
# OMIT
# =====================================================================================
@pytest.mark.parametrize("parent", PARENTS)
@pytest.mark.parametrize("key", sorted(AUTH))
def test_an_omitted_field_is_not_emitted(parent, key):
    partial = {k: v for k, v in AUTH.items() if k != key}
    assert resolve_binding(parent, key)["parent_nvpair"] not in _emit(parent, partial)


@pytest.mark.parametrize("parent", PARENTS)
@pytest.mark.parametrize("key", sorted(AUTH))
def test_an_omitted_field_is_carried_forward_from_the_controller(parent, key):
    """Omission means "leave it alone", and the module's payload is SPARSE.

    Without carry-forward NDFC re-applies the template over the fields the payload does not
    mention, which resets them to template defaults. For this family that means silently
    removing authentication from an interface whose playbook simply did not mention it -- the
    fabric-loopback drift, repeated on a parent where the fabric cannot put it back.
    """
    carried = {b["profile_key"] for b in gie_carry_forward_bindings(parent)}
    assert key in carried, (
        "omitting {0} on {1} would let NDFC reset it".format(key, parent)
    )


@pytest.mark.parametrize("parent", PARENTS)
def test_omitting_everything_emits_nothing(parent):
    assert _emit(parent, {}) == {}


# =====================================================================================
# WITHDRAW
# =====================================================================================
@pytest.mark.parametrize("parent", PARENTS)
def test_disabling_authentication_is_an_explicit_false_not_an_omission(parent):
    """The two are different intents and the module must not conflate them.

    Omitting the gate means "leave authentication as it is". Setting it false means "turn it
    off". A module that treated the first as the second would disable authentication on every
    interface whose playbook happened not to mention it.
    """
    assert "ENABLE_OSPF_AUTH" not in _emit(parent, {"ospf_auth_key_id": 7})
    assert _emit(parent, {"enable_ospf_auth": False})["ENABLE_OSPF_AUTH"] == "false"


@pytest.mark.parametrize("parent", PARENTS)
def test_clearing_a_key_travels_as_an_empty_string(parent):
    """"" is how a string nvPair is CLEARED, so it must transport like any other value.

    Same precedent as ACL_FILTER, measured on 12.6.0.267: the empty string is accepted, stored,
    and withdraws the line from the device on deploy. Blocking it would make the key settable
    and never clearable.
    """
    emitted = _emit(parent, {"ospf_auth_key": "", "ospf_authentication_key": ""})
    assert emitted["OSPF_AUTH_KEY"] == ""
    assert emitted["OSPF_AUTHENTICATION_KEY"] == ""


@pytest.mark.parametrize("parent", PARENTS)
def test_the_removal_semantics_are_recorded_as_unresolved(parent):
    """Honest pinning: what `deleted`/`overridden` do to these fields is NOT established.

    The registry says `removal_semantics: unresolved` for all fifteen. Overridden-with-an-empty
    config is the path behind two defects already, and it is not in the offline matrix. This
    asserts the admission rather than a behaviour, so that resolving it is a deliberate act.
    """
    import yaml
    import os
    slice_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..", "..", "..", "..",
        "evidence", "generic-interface-engine", "registry",
        "registry_slice_0b_21_ospf_auth.yaml")
    if not os.path.exists(slice_path):
        pytest.skip("registry slice not reachable from the installed collection tree")
    rows = yaml.safe_load(open(slice_path))["bindings"]
    for row in (r for r in rows if r["parent_template"] == parent):
        assert row["removal_semantics"] == "unresolved"


# =====================================================================================
# THE GUARD — the same key on a parent that does not declare it
# =====================================================================================
@pytest.mark.parametrize("key", sorted(AUTH))
def test_an_authentication_key_on_an_unrelated_parent_is_refused(key):
    """int_trunk_host has no OSPF at all. Accepting the key there would drop it in silence.

    This is the guard the withdrawn loopback validator used to own. Nothing else owns it now.
    """
    assert gie_invalid_parent_key("int_trunk_host", {key: "whatever"}) == key
