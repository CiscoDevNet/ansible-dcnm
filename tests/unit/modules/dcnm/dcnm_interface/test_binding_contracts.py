"""Binding table contracts: the withdrawal classifier, processing routes, indexes, wiring and the legacy boundary."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import inspect
import pytest
import re

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_withdrawal_action
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_binding_applicable
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_WITHDRAW_NONE
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_WITHDRAW_RESET
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_WITHDRAW_UNSUPPORTED
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_WITHDRAW_UNCLASSIFIED
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_WITHDRAW_INAPPLICABLE
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_ENABLED_PATCH_VERSIONS
from unittest import mock
from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table
from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import BINDING_TABLE
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_carry_forward_bindings
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_contribute_nvpairs
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_invalid_parent_key
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import rebuild_binding_indexes
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import registered_profile_keys
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_by_nvpair
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GieBindingError
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_all_registered_keys
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_guarded_keys
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_no_log_profile_keys
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_nvpair_keymap
from pathlib import Path
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_extend_prof_spec

from .helpers.binding_harness import an_unclassifiable_key


# ====================================================================================================
# Formerly test_gie_withdrawal_classifier.py
# Direct tests of the withdrawal DECISION FUNCTION.
#
# Labelled HELPER tests throughout. They are not a substitute for the real-module coverage
# in `test_binding_withdrawal.py`; they exist because `gie_withdrawal_action` is also the
# function an external caller invokes on its own -- a compatibility probe, or a live
# batch's classification preflight. Such a caller never goes through `main()`, so the gate
# must live inside the function itself, and that copy needs its own proof.
#
# NOT LIVE TESTED.
#
# The unsupported routed fixture is now ``eigrp_ipv4_passive`` because PIM/BFD
# gained a measured reset. ``FIXTURE_CONTRACTS`` checks its registration and
# no-reset property per parent. ACCESS positive cases keep their own measured rows.
# ====================================================================================================
ACCESS = "int_access_host"
ROUTED = "int_routed_host"
SUBIF = "int_subif"
SVI = "int_vlan"
OK = "12.6.0.267"
# This file tests the NDFC-version boundary of the withdrawal
# classifier, which is independent of the (new, additional) patch boundary. Every case below
# declares the approved patch explicitly so a result is attributable to the version alone;
# the patch boundary itself is exercised in test_binding_versions.py.
OK_PATCH = sorted(GIE_ENABLED_PATCH_VERSIONS)[0]


# ------------------------------------------------------------------ version boundary
@pytest.mark.parametrize("version", ["12.6.0.266", "12.4.1", "not-a-version", "", None],
                         ids=["one_below", "far_below", "malformed", "empty", "none"])
def test_classifier_refuses_an_inapplicable_binding(version):
    """The gate mutation 3b targets. Below min_ndfc_version, or on a version we cannot
    parse, the answer is INAPPLICABLE -- never a reset, never a refusal."""
    action, wire = gie_withdrawal_action(ACCESS, "acl_filter", "ACL-PILOT", version, OK_PATCH)
    assert action == GIE_WITHDRAW_INAPPLICABLE, (
        "a binding the controller cannot carry was classified %r; emitting a reset here "
        "transports what an explicit key is refused, and refusing here rejects a run over "
        "a field this controller never had" % action)
    assert wire is None


@pytest.mark.parametrize("version", [OK, "12.6.0.268", "12.7.0.1", "13.0.0.0"],
                         ids=["equal", "patch_above", "minor_above", "major_above"])
def test_classifier_reconciles_once_the_version_supports_it(version):
    action, wire = gie_withdrawal_action(ACCESS, "acl_filter", "ACL-PILOT", version, OK_PATCH)
    assert (action, wire) == (GIE_WITHDRAW_RESET, "")


def test_applicability_helper_agrees_with_the_classifier():
    """Two entry points, one boundary. A caller that selects with the helper and then
    classifies must never see the two disagree."""
    for version in ("12.6.0.266", OK, "nonsense", None):
        applicable = gie_binding_applicable(ACCESS, "acl_filter", version, OK_PATCH)
        action, _reset = gie_withdrawal_action(
            ACCESS, "acl_filter", "ACL-PILOT", version, OK_PATCH)
        assert applicable == (action != GIE_WITHDRAW_INAPPLICABLE), version


# ------------------------------------------------------------------ HAVE encodings
@pytest.mark.parametrize("have", ["false", False], ids=["wire_string", "native_bool"])
def test_both_accepted_encodings_of_the_declared_default_mean_the_same_state(have):
    action, _reset = gie_withdrawal_action(ACCESS, "disable_lldp_receive", have, OK, OK_PATCH)
    assert action == GIE_WITHDRAW_NONE, (
        "encoding %r of the declared default classified as %r; the HAVE validator accepts "
        "both spellings and they describe one controller state" % (have, action))


@pytest.mark.parametrize("have", ["true", True], ids=["wire_string", "native_bool"])
def test_both_encodings_of_a_non_default_also_agree(have):
    """The opposite direction, so the normalisation is not just collapsing everything to
    'no change'.

    REHOMED: this used int_access_host::disable_lldp_receive, which had no reset when the
    test was written. That row is now supported, so the C7 half of the assertion would
    have been silently lost. int_routed_host::disable_lldp_receive is a genuine
    unsupported-but-applicable row -- a declared default, no established reset -- so the
    guarantee moves rather than weakening.
    """
    action, _reset = gie_withdrawal_action(ROUTED, "eigrp_ipv4_passive", have, OK, OK_PATCH)
    assert action == GIE_WITHDRAW_UNSUPPORTED


@pytest.mark.parametrize("have", ["true", True], ids=["wire_string", "native_bool"])
def test_both_encodings_reach_the_same_reset(have):
    action, wire = gie_withdrawal_action(ACCESS, "disable_lldp_transmit", have, OK, OK_PATCH)
    assert (action, wire) == (GIE_WITHDRAW_RESET, "false")


def test_normalisation_does_not_turn_an_empty_string_into_a_false():
    """`""` is NDFC's 'no value', not the boolean false, and the two must not merge.

    A blanket coercion would make an unset field look like a configured default -- and on
    a binding whose declared default is False that silently reclassifies C-nothing as
    already-withdrawn for the wrong reason.
    """
    # REHOMED to int_routed_host for the same reason as above: the access row now has a
    # reset, and this case needs one that does not.
    empty, _empty_reset = gie_withdrawal_action(
        ROUTED, "eigrp_ipv4_passive", "", OK, OK_PATCH)
    false_wire, _false_reset = gie_withdrawal_action(
        ROUTED, "eigrp_ipv4_passive", "false", OK, OK_PATCH)
    assert false_wire == GIE_WITHDRAW_NONE
    assert empty != GIE_WITHDRAW_RESET, (
        "an empty HAVE produced a reset; absence is not a configured value")


def test_an_integer_zero_is_not_an_empty_value():
    """The other half of the same rule: no empty-to-zero conversion in either direction.

    The key is DERIVED, not named: this used `ospf_cost` until its reset was measured, which is
    the second time a registration invalidated a hardcoded example here.
    """
    # REHOMED to `int_vlan`, for the same reason as the decision-table row below and one step
    # further: the dampening rows consumed `int_routed_host`'s last unclassifiable integers,
    # so this moved to `int_subif`, and this union registers the three BFD timers there too.
    # `int_vlan` still carries four (the HSRP integers). The harness asserts loudly when a parent
    # runs out, which is how this was caught.
    key = an_unclassifiable_key(SVI, "integer")
    zero, _zero_reset = gie_withdrawal_action(SVI, key, 0, OK, OK_PATCH)
    empty, _empty_reset = gie_withdrawal_action(SVI, key, "", OK, OK_PATCH)
    assert zero == GIE_WITHDRAW_UNCLASSIFIED, (
        "a real integer value was treated as absence (%s)" % key)
    assert empty == GIE_WITHDRAW_UNCLASSIFIED
    # They classify the same here only because this row has neither metadata; the point is
    # that "0" and "" took different routes to get there, not that they are interchangeable.
    assert gie_withdrawal_action(SVI, key, "0", OK, OK_PATCH)[0] == zero


# ------------------------------------------------------------------ the decision table
@pytest.mark.parametrize("parent,key,have,expected", [
    (ACCESS, "acl_filter", "", GIE_WITHDRAW_NONE),             # already at its reset
    (ACCESS, "acl_filter", "ACL-X", GIE_WITHDRAW_RESET),       # reset known
    (ACCESS, "flowcontrol_receive", "off", GIE_WITHDRAW_NONE),  # reset == default
    (ACCESS, "flowcontrol_receive", "on", GIE_WITHDRAW_RESET),
    (ACCESS, "disable_lldp_receive", "false", GIE_WITHDRAW_NONE),   # at declared default
    # REHOMED: access disable_lldp_receive now carries a reset, so the
    # differs-without-a-reset row moves to a parent where that is still true.
    # BFD echo and PIM/BFD gained measured resets separately. The
    # withheld EIGRP passive row remains a registered no-reset example.
    (ROUTED, "eigrp_ipv4_passive", "true", GIE_WITHDRAW_UNSUPPORTED),
    # DERIVED, and REHOMED THREE TIMES NOW. `ospf_cost` held this slot until its reset was
    # measured; the five dampening integers held it next, which is why it moved to `int_subif`;
    # and THIS union registers the three BFD timers on `int_subif` as well, so that parent has run
    # out too. Measured on the integrated table: int_routed_host 0 candidates, int_subif 0,
    # int_vlan 4 (the HSRP integers). So it moves to `int_vlan`.
    #
    # The harness refuses to let this pass vacuously -- `an_unclassifiable_key` asserts loudly
    # when a parent has no candidate left -- which is exactly how this was caught rather than
    # discovered by a green suite. Deriving the key keeps the row honest the next time a
    # generation consumes the last candidate on a parent.
    (SVI, an_unclassifiable_key(SVI, "integer"), "100", GIE_WITHDRAW_UNCLASSIFIED),
    (ACCESS, an_unclassifiable_key(SVI, "integer"), "100", GIE_WITHDRAW_NONE),
], ids=["reset_already_applied", "reset_needed", "default_is_the_reset",
        "enum_needs_reset", "at_declared_default", "differs_no_reset",
        "no_metadata", "not_on_this_parent"])
def test_the_decision_table_row_by_row(parent, key, have, expected):
    action, wire = gie_withdrawal_action(parent, key, have, OK, OK_PATCH)
    assert action == expected, "%s::%s with HAVE %r" % (parent, key, have)
    assert (wire is not None) == (action == GIE_WITHDRAW_RESET)


# ====================================================================================================
# Formerly test_gie_mechanism_contract.py
# Every binding is on the processing route its contract says, and nothing else.
#
# THE ERROR THIS EXISTS TO CATCH
#     Four ``int_routed_host`` OSPF bindings were registered ``child_pti`` by copying a
#     prediction from the phase-0 ledger. They own no dedicated validation, so the label routed
#     them around the generic path. It was caught by a hand-written test that happened to exist
#     for that parent; on a parent without one it would have shipped.
#
# WHY THE OBVIOUS TEST DOES NOT WORK
#     "Assert a wrong parent is still rejected" is NOT sufficient, and the counterexample is
#     concrete. ``gie_guarded_keys()`` returns bare ``profile_key`` strings with no parent
#     qualification:
#
#         return {b["profile_key"] for b in BINDING_TABLE if b["mechanism"] == "passthrough"}
#
#     Seven parents register ``acl_filter``. Flip ONE of them to ``child_pti`` and the key stays
#     in the guarded set via the other six -- the wrong-parent rejection still fires, looking
#     healthy -- while that parent silently loses its generic arg-spec entry and its
#     carry-forward. Reproduced in ``test_mislabelling_one_parent_of_a_shared_key_is_caught``.
#
#     So every check here is PARENT-QUALIFIED. That is the property the global guard lacks.
#
# WHERE THE EXPECTED ANSWER COMES FROM
#     ``DEDICATED_ROUTE`` below, never from the ``mechanism`` field being tested -- reading the
#     answer off the thing under test would make this vacuous. It names the bindings that own a
#     hand-written validation path, with the validator and the observable message each one is
#     responsible for. Everything else must be generic.
#
#     A new ``child_pti`` binding therefore FAILS here until someone adds it deliberately and
#     states what validates it. It is never skipped.
#
# WHAT THIS FILE COVERS, AND WHAT IT DOES NOT
#     This is a STRUCTURAL contract over the table. It was verified by sabotage: replacing
#     ``dcnm_intf_validate_ethernet_interface_input`` with a function that raises left every test
#     here passing, with zero calls. So placement is all it proves --
#
#       * the positive control drives ``gie_contribute_nvpairs`` (the ENGINE), not survival
#         through the module's validator and builder;
#       * the preservation check asserts a binding appears in the carry-forward SELECTOR, not
#         that its value survives a WANT/HAVE comparison;
#       * finding the key name and guard message in a validator's source shows the code is
#         plausibly responsible, not that it rejects anything.
#
#     The module flow is exercised in the two sections at the end of this file, and end to end
#     through the real comparator in ``test_binding_ospf_routed.py`` and
#     ``test_binding_module_path.py``.
#
# Offline: no controller and no device.
# ====================================================================================================
# The ONLY bindings that own a hand-written validation path, and what each is answerable for.
# Independent of the table: this is the contract the table is checked against.
# EMPTY, and that is an assertion rather than an absence.
#
# It held the three fabric-loopback OSPF-auth bindings, the only child_pti in the table. They
# were withdrawn because OSPF authentication on a loopback is underlay authentication that
# fabricSettings owns, and the two global validators serving them rejected ospf_auth_key on any
# interface whose type was not "lo" -- which blocked registering it on the overlay parents where
# it is a legitimate, self-contained interface feature.
#
# With it empty, every binding is passthrough. The tests below are written so that emptiness
# cannot make them vacuous: a parametrized case over an empty mapping would silently collect
# nothing, so the contract is asserted directly instead, and the mutation controls still prove
# the checks react.
DEDICATED_ROUTE = {}

# A valid explicit value per registry type, for the positive control.
SAMPLE_VALUE = {
    "boolean": True,
    "integer": 100,
    "string": "SAMPLE",
    "enum": None,          # taken from valid_values
}

NDFC_VERSION = "12.6.0.267"
# Declared explicitly, read from the engine's own policy, for every
# positive fixture in this file.
PATCH_VERSION = sorted(gie_engine.GIE_ENABLED_PATCH_VERSIONS)[0]


def _key(binding):
    return (binding["parent_template"], binding["parent_nvpair"])


# The identities are PARTITIONED, not filtered: an identity with no SMU counterpart still
# has a contract, it is just the opposite one, and it is asserted below rather than dropped.
SUPPORTED_KEYS = sorted(
    {_key(b) for b in BINDING_TABLE
     if _key(b) not in DEDICATED_ROUTE and not b.get("smu_unsupported")}
)
UNSUPPORTED_KEYS = sorted(
    {_key(b) for b in BINDING_TABLE
     if _key(b) not in DEDICATED_ROUTE and b.get("smu_unsupported")}
)
assert SUPPORTED_KEYS and UNSUPPORTED_KEYS, "the partition must cover both sides"

# Independently reviewed SMU enum vocabularies, transcribed by hand from the captured
# declarations on .90 (capture-S2, byte-identical to capture-R2 at 12.6.0.267). Deliberately
# NOT obtained from gie_wire_value: a test must not use the production mapper as its own
# oracle. `validValues` in the installed bodies:
#     ospfNetworkType   noChange,broadcast,pointToPoint
#     ospfBfdMode       noChange,enable,disable
#     ospfPassiveMode   noChange,passive,noPassive
REVIEWED_WIRE_ENUM = {
    "no_change": "noChange",
    "point_to_point": "pointToPoint",
    "no_passive": "noPassive",
}


def _reviewed_wire(binding, value):
    """The nvPair value this binding must emit for `value`, from the reviewed table above."""
    if "wire_values" in binding and isinstance(value, str):
        return REVIEWED_WIRE_ENUM.get(value, value)
    return str(value)


def _sample_for(binding):
    if binding["type"] == "enum":
        return binding["valid_values"][0]
    if binding["type"] == "string":
        max_length = binding.get("max_length")
        value = "SAMPLE"
        return value[:max_length] if max_length else value
    if binding["type"] == "integer":
        # Clamp to the registered bounds, the way the string branch above already clamps to
        # max_length. Without this the flat sample of 100 is REJECTED by any binding whose
        # maximum is lower -- bfd_multiplier caps at 50 -- and the positive control fails for
        # being out of range rather than for anything the test is about. The first bounded
        # integer to arrive found the gap; it was always there.
        value = SAMPLE_VALUE["integer"]
        low, high = binding.get("min_value"), binding.get("max_value")
        if high is not None:
            value = min(value, high)
        if low is not None:
            value = max(value, low)
        return value
    return SAMPLE_VALUE[binding["type"]]


def _generic_route_violations(table):
    """Parent-qualified placement check. Returns a list of human-readable violations.

    Exposed as a function rather than inlined in a test so the mutation control below can call
    it on a deliberately corrupted table and prove it reacts.
    """
    violations = []
    guarded = {
        b["profile_key"] for b in table if b.get("mechanism") == "passthrough"
    }
    for binding in table:
        key = _key(binding)
        parent, profile_key = binding["parent_template"], binding["profile_key"]
        expected_dedicated = key in DEDICATED_ROUTE
        is_dedicated = binding.get("mechanism") == "child_pti"

        if is_dedicated != expected_dedicated:
            violations.append(
                "{0}: mechanism {1!r} contradicts the contract (dedicated={2})".format(
                    key, binding.get("mechanism"), expected_dedicated
                )
            )
            continue

        carried = {b["parent_nvpair"] for b in gie_carry_forward_bindings(parent)}
        on_generic = profile_key in gie_engine._generic_keys(parent)

        if expected_dedicated:
            # Must stay OUT of the generic route -- its own validator owns it.
            if binding["parent_nvpair"] in carried:
                violations.append("{0}: dedicated binding is on generic carry-forward".format(key))
            if on_generic:
                violations.append("{0}: dedicated binding is in the generic spec".format(key))
        else:
            # PARENT-QUALIFIED. `profile_key in guarded` alone would pass for a shared key
            # mislabelled on one parent -- that is the counterexample in the module docstring.
            if binding["parent_nvpair"] not in carried:
                violations.append("{0}: generic binding lost its carry-forward".format(key))
            if not on_generic:
                violations.append("{0}: generic binding is missing from the generic spec".format(key))
            if profile_key not in guarded:
                violations.append("{0}: generic binding is unguarded".format(key))
    return violations


# =====================================================================================
# THE CONTRACT HOLDS
# =====================================================================================
def test_every_binding_sits_on_the_route_its_contract_declares():
    assert _generic_route_violations(BINDING_TABLE) == []


def test_no_binding_claims_a_dedicated_route():
    """The contract after the retirement: every binding is on the generic route.

    Not a placeholder. If a child_pti binding reappears, this fails and whoever added it has to
    declare it in DEDICATED_ROUTE with the validator that actually guards it -- which is the
    step that was missing when four OSPF bindings were mislabelled child_pti with no
    implementation behind them.
    """
    in_table = sorted(_key(b) for b in BINDING_TABLE if b.get("mechanism") == "child_pti")
    assert in_table == [], (
        "these declare a dedicated route but DEDICATED_ROUTE is empty, so nothing verifies one "
        "exists: {0}".format(in_table)
    )
    assert DEDICATED_ROUTE == {}, "DEDICATED_ROUTE grew; add the behavioural cases back"


def test_the_retired_validators_are_gone_and_not_merely_unused():
    """The 198 lines that blocked overlay OSPF auth must be absent, not orphaned.

    An unused validator still on the class is a trap: the next person wiring auth would find it,
    assume it is the supported path, and reintroduce the loopback-only type check.
    """
    for name in ("dcnm_intf_validate_ospf_auth_key_input",
                 "dcnm_intf_validate_ospf_auth_message_digest_input"):
        assert not hasattr(dcnm_interface.DcnmIntf, name), (
            "{0} is still on the class".format(name)
        )


def test_no_method_lost_its_decorator_in_the_retirement():
    """Caught in review, not here: two @staticmethod decorators were removed by a cut whose
    boundary ended one line early, leaving methods that worked when called on the class and
    raised TypeError when called on an instance.
    """
    import ast
    src = inspect.getsource(dcnm_interface)
    cls = next(n for n in ast.walk(ast.parse(src))
               if isinstance(n, ast.ClassDef) and n.name == "DcnmIntf")
    broken = [
        f.name for f in cls.body
        if isinstance(f, ast.FunctionDef) and f.args.args and f.args.args[0].arg != "self"
        and not any(getattr(d, "id", "") in ("staticmethod", "classmethod")
                    for d in f.decorator_list)
    ]
    assert broken == [], "methods without self and without a decorator: {0}".format(broken)


# =====================================================================================
# BEHAVIOUR — 1. an unsupported parent is rejected
# =====================================================================================
def _a_parent_that_does_not_register(profile_key):
    """A parent where the key is genuinely unsupported.

    Not merely "a different parent": for a key registered on seven parents, another parent is
    usually equally valid and proves nothing.
    """
    registered = {b["parent_template"] for b in BINDING_TABLE if b["profile_key"] == profile_key}
    for binding in BINDING_TABLE:
        if binding["parent_template"] not in registered:
            return binding["parent_template"]
    return None


@pytest.mark.parametrize(
    "key", sorted({_key(b) for b in BINDING_TABLE if _key(b) not in DEDICATED_ROUTE})
)
def test_a_generic_binding_is_rejected_on_a_parent_that_does_not_support_it(key):
    binding = next(b for b in BINDING_TABLE if _key(b) == key)
    if binding["profile_key"] in gie_engine.GIE_NATIVE_ELSEWHERE_KEYS:
        # Served natively on other parents by name (gie_engine.GIE_NATIVE_ELSEWHERE_KEYS): the generic guard
        # leaves it to the native spec. Its own behaviour is pinned in test_binding_smu017.py.
        assert gie_invalid_parent_key(_a_parent_that_does_not_register(binding["profile_key"]),
                                      ["mode", binding["profile_key"]]) is None
        return
    wrong_parent = _a_parent_that_does_not_register(binding["profile_key"])
    if wrong_parent is None:
        pytest.skip("{0} is registered on every parent in the table".format(binding["profile_key"]))
    assert gie_invalid_parent_key(wrong_parent, ["mode", binding["profile_key"]]) == (
        binding["profile_key"]
    )


# =====================================================================================
# BEHAVIOUR — 2. the correct parent carries the intent through to the nvPair
# =====================================================================================
@pytest.mark.parametrize("key", SUPPORTED_KEYS)
@pytest.mark.parametrize("patch_version", [PATCH_VERSION, "4.4.1"])
def test_a_generic_binding_reaches_the_payload_in_wire_form(key, patch_version):
    """ENGINE-level: gie_contribute_nvpairs, not the module's validator/builder pair.

    Placement is not enough: the value has to survive to an nvPair, in NDFC's encoding.

    nvPairs is a string-valued map, so a native bool left there reproduces the non-convergence
    the wire form exists to prevent.
    """
    binding = next(b for b in BINDING_TABLE if _key(b) == key)
    value = _sample_for(binding)
    nvpairs, error = gie_contribute_nvpairs(
        binding["parent_template"], {binding["profile_key"]: value}, NDFC_VERSION,
        patch_version
    )
    assert error is None, "{0}: {1}".format(key, error)
    assert binding["parent_nvpair"] in nvpairs, "{0}: the nvPair was not emitted".format(key)
    emitted = nvpairs[binding["parent_nvpair"]]
    assert isinstance(emitted, str), (
        "{0}: emitted {1!r}, a {2}; nvPairs must be strings".format(
            key, emitted, type(emitted).__name__
        )
    )
    if binding["type"] == "boolean":
        assert emitted == "true"
    else:
        assert emitted == _reviewed_wire(binding, value), (
            "{0}: emitted {1!r}; the reviewed declaration expects {2!r}".format(
                key, emitted, _reviewed_wire(binding, value)
            )
        )


# =====================================================================================
# 3. omission — the SELECTOR only
# =====================================================================================
@pytest.mark.parametrize("key", SUPPORTED_KEYS)
def test_a_generic_binding_is_offered_to_the_carry_forward_selector(key):
    """Named for what it checks: the binding is OFFERED for carry-forward.

    That a value actually survives a WANT/HAVE comparison is a different claim, and it is
    proven where the real comparator runs -- test_binding_ospf_routed.py
    (test_an_explicit_cost_is_not_overwritten_by_have, test_a_second_identical_run_produces_no_payload)
    and test_binding_module_path.py (test_registered_binding_is_carried_when_omitted).
    """
    binding = next(b for b in BINDING_TABLE if _key(b) == key)
    carried = gie_carry_forward_bindings(binding["parent_template"])
    entry = next((c for c in carried if c["parent_nvpair"] == binding["parent_nvpair"]), None)
    assert entry is not None, "{0}: omission would drop the controller value".format(key)
    assert entry["profile_key"] == binding["profile_key"]


# =====================================================================================
# 4. MUTATION CONTROL — the checks above must actually react
# =====================================================================================
def _with_mechanism(key, mechanism):
    return tuple(
        dict(b, mechanism=mechanism) if _key(b) == key else b for b in BINDING_TABLE
    )


@pytest.fixture
def patched_table(monkeypatch):
    """Swap the table everywhere it is actually read, then REBUILD THE INDEXES.

    Both patch targets are load-bearing, and patching only the first is a trap worth naming:
    it makes the mutation tests pass for the wrong reason. ``gie_engine`` holds its own
    reference, used by ``gie_nvpair_keymap()``; but the structural lookups and per-parent
    selections live in ``gie_binding_table`` and read ITS module global, which is what
    ``_generic_keys()`` and ``gie_carry_forward_bindings()`` go through. Patch only
    ``gie_engine`` and the parent-qualified checks keep reporting the UNMUTATED placement.

    The rebuild is the third load-bearing step, and it is explicit for the same reason.
    ``gie_binding_table`` indexes the packaged registry ONCE, at import, and nothing at
    runtime watches for a replaced table -- a per-lookup fingerprint would put back exactly
    the full-table work the indexes removed. So a fixture that swaps the global without
    rebuilding is not testing its mutated table at all: every lookup still answers from the
    packaged one, and the mutation controls below would pass while measuring nothing.

    Teardown rebuilds from the restored global, so a later test in the same process cannot
    inherit this fixture's indexes.
    """
    def _apply(table):
        monkeypatch.setattr(gie_engine, "BINDING_TABLE", table)
        monkeypatch.setattr(gie_binding_table, "BINDING_TABLE", table)
        gie_binding_table.rebuild_binding_indexes()
        return table
    yield _apply
    monkeypatch.undo()
    gie_binding_table.rebuild_binding_indexes()


def test_mislabelling_one_parent_of_a_shared_key_is_caught(patched_table):
    """The counterexample, pinned.

    ``acl_filter`` is registered on seven parents. Mislabelling ONE leaves the key guarded by
    the other six, so a guard-only test sees nothing wrong. The parent-qualified checks do.
    """
    key = ("int_access_host", "aclFilter")
    table = patched_table(_with_mechanism(key, "child_pti"))

    assert "acl_filter" in {
        b["profile_key"] for b in table if b.get("mechanism") == "passthrough"
    }, "fixture no longer reproduces the counterexample: the key must stay globally guarded"

    violations = _generic_route_violations(table)
    assert violations, "a mislabelled shared key went undetected"
    assert any("int_access_host" in v and "aclFilter" in v for v in violations)


@pytest.mark.parametrize(
    "key",
    sorted({_key(b) for b in BINDING_TABLE if _key(b) not in DEDICATED_ROUTE})[:8],
)
def test_reclassifying_any_generic_binding_breaks_the_contract(key, patched_table):
    """Every generic binding, not just the shared one, must be detectably misplaceable."""
    table = patched_table(_with_mechanism(key, "child_pti"))
    violations = _generic_route_violations(table)
    assert any(str(key) in v for v in violations), (
        "reclassifying {0} as child_pti produced no violation".format(key)
    )


def test_a_binding_claiming_child_pti_breaks_the_contract(patched_table):
    """The direction that still has a subject.

    Previously this degraded a dedicated binding to generic. With none left, the meaningful
    mutation is the opposite and it is the one that actually happened once: a binding claiming
    child_pti with nothing implementing it. It must not compile silently into the table.
    """
    key = ("int_routed_host", "ospfCost")
    table = patched_table(_with_mechanism(key, "child_pti"))
    violations = _generic_route_violations(table)
    assert any(str(key) in v for v in violations), (
        "a binding claiming a dedicated route it does not own produced no violation"
    )


# =====================================================================================
# REAL MODULE FLOW — 1. each dedicated route rejects a wrong parent when actually run
# =====================================================================================
#
# Everything above is structural. These invoke the real methods, and are written so that
# stubbing the method out makes them FAIL rather than silently pass -- the sabotage check that
# exposed the earlier overclaim.


def _config_obj(config):
    """Bare DcnmIntf carrying just the state the validators under test read.

    ``intf_info`` is where the ethernet validator accumulates its results, so it has to exist
    even though nothing here inspects it.
    """
    obj = object.__new__(dcnm_interface.DcnmIntf)
    obj.config = config
    obj.intf_info = []
    # The builder passes this straight to gie_contribute_nvpairs; leaving it unset makes the
    # engine fail closed on an unknown version, which would look like a binding problem.
    obj.ndfc_version = NDFC_VERSION
    # Same reasoning, : leaving this unset makes the engine fail closed
    # on a missing patch, which would look like a binding problem rather than a fixture gap.
    obj.patch_version = PATCH_VERSION
    obj.module = mock.Mock()
    obj.module.fail_json.side_effect = _ValidatorRejected
    return obj


class _ValidatorRejected(Exception):
    """fail_json in production raises; the Mock harness returns. Make it raise."""


def _lo_item(profile_extra, itype="lo", mode="fabric"):
    """A config item that is valid EXCEPT for whatever the caller overrides."""
    profile = {"mode": mode, "ipv4_addr": "10.2.0.1"}
    profile.update(profile_extra)
    return {"name": "lo0", "type": itype, "switch": ["10.1.1.1"], "profile": profile}


# The runnable rejection cases for dedicated routes lived here. With DEDICATED_ROUTE empty they
# had no subjects, and pytest reported "got empty parameter set" -- a SKIP, which is the vacuous
# pass this file exists to prevent. Removed rather than left to collect nothing.
#
# What replaces them is not a weaker check: test_no_binding_claims_a_dedicated_route fails the
# moment a child_pti binding reappears, and whoever adds it has to bring both the declaration and
# the behavioural case back together.


# =====================================================================================
# REAL MODULE FLOW — 2. the OSPF slice through the real validator and builder
# =====================================================================================
OSPF_SLICE = {
    "enable_ospf": True,
    "ospf_tag": "WP98",
    "ospf_area_id": "0.0.0.0",
    "ospf_cost": 100,
}
OSPF_EXPECTED_NVPAIRS = {
    "ospf": "true",
    "ospfTag": "WP98",
    "OSPF_AREA_ID": "0.0.0.0",
    "ospfCost": "100",
}


def _routed_delem():
    return {
        "name": "eth1/5", "type": "eth", "switch": ["10.1.1.1"], "deploy": False,
        "profile": dict(
            OSPF_SLICE,
            mode="routed", admin_state=True, speed="Auto", mtu=9216,
            int_vrf="", ipv4_addr="10.1.1.1", ipv4_mask_len=24, route_tag="",
            description="", cmds=[],
        ),
    }


def _intf_skeleton():
    # `policy` is what the builder hands gie_contribute_nvpairs as the parent template, so it
    # is the field that decides which bindings apply.
    return {
        "policy": "int_routed_host",
        "interfaceType": "INTERFACE_ETHERNET",
        "interfaces": [{"serialNumber": "SNO", "interfaceType": "INTERFACE_ETHERNET",
                        "nvPairs": {}}],
    }


def test_the_ospf_slice_survives_the_real_ethernet_validator():
    """The arg spec is extended from the registry, so the four keys must survive validation.

    This is the failure the dot1q port-channel hit: registered and transported, then rejected
    by the spec before anything was built.
    """
    obj = _config_obj([_routed_delem()])
    obj.dcnm_version = 12
    # cfg is the LIST: the method indexes cfg[0]["profile"] to extend the spec.
    obj.dcnm_intf_validate_ethernet_interface_input(obj.config)
    assert not obj.module.fail_json.called, (
        "the routed arg spec rejected the registered OSPF keys: {0}".format(
            obj.module.fail_json.call_args
        )
    )
    profile = obj.config[0]["profile"]
    for key, value in OSPF_SLICE.items():
        assert key in profile, "{0} was dropped by validation".format(key)
        assert profile[key] == value, "{0} was altered by validation".format(key)


def test_the_ospf_slice_reaches_the_payload_through_the_real_builder():
    """End of the module path: the builder must emit all four nvPairs in wire form."""
    obj = _config_obj([_routed_delem()])
    obj.dcnm_version = 12
    delem = obj.config[0]
    intf = _intf_skeleton()
    obj.dcnm_intf_get_eth_payload(delem, intf, "profile")
    nvpairs = intf["interfaces"][0]["nvPairs"]
    for nvpair, expected in OSPF_EXPECTED_NVPAIRS.items():
        assert nvpair in nvpairs, "{0} never reached the payload".format(nvpair)
        assert nvpairs[nvpair] == expected, (
            "{0}: expected {1!r}, got {2!r}".format(nvpair, expected, nvpairs[nvpair])
        )
        assert isinstance(nvpairs[nvpair], str), "nvPairs must be strings"


# =====================================================================================
# the other half of the partition — an identity with NO SMU counterpart
# =====================================================================================
@pytest.mark.parametrize("key", UNSUPPORTED_KEYS)
def test_an_unsupported_identity_refuses_before_emitting_anything(key):
    """The counterpart of the sweep above. An identity the installed build does not declare
    must refuse at the contribution boundary and emit nothing -- not fall back to the
    pre-SMU nvPair name, and not be quietly dropped from coverage either."""
    binding = next(b for b in BINDING_TABLE if _key(b) == key)
    nvpairs, error = gie_contribute_nvpairs(
        binding["parent_template"],
        {binding["profile_key"]: _sample_for(binding)},
        NDFC_VERSION,
        PATCH_VERSION,
    )
    assert nvpairs is None, "{0}: an unsupported identity produced a payload".format(key)
    assert error and "not supported by the interface templates installed" in error, error
    assert binding["parent_nvpair"] not in (nvpairs or {})


# ====================================================================================================
# Formerly test_gie_binding_indexes.py
# ====================================================================================================
# Structural-index contract for the packaged binding table.
#
# The table used to answer every lookup and every per-parent selection with a full pass over
# BINDING_TABLE. It now answers from indexes built once, at import. These tests pin the two
# halves of that change that a later edit could quietly break:
#
#   1. EQUIVALENCE -- the indexed answers are the answers the scanning comprehensions gave,
#      including the cases that are easy to "improve" by accident: a duplicated identity
#      resolves to None rather than first-wins, a resolved binding is still the ORIGINAL row
#      object, and every helper that hands back a mutable container hands back a fresh one.
#
#   2. THE WORK IS ACTUALLY GONE -- repeated lookups visit zero registry rows. Asserted by
#      COUNTING row visits, never by timing: a wall-clock threshold in a unit test is a
#      flake waiting for a busy CI worker. Each counting test is paired with a mutation
#      control that restores the scanning implementation and requires the same assertion to
#      fail, so a counter that stops counting cannot pass as a result.
#
# The third contract is the one with no runtime enforcement by design: nothing detects a
# REPLACED table, because a per-lookup fingerprint is the full-table work these indexes
# removed. test_a_replaced_table_is_invisible_until_the_indexes_are_rebuilt pins that, so
# the "fix" is recognisable as a regression rather than a correction.


PASSTHROUGH = "passthrough"

# Enough repetitions that a per-call scan cannot hide in rounding, small enough to stay
# instant. The assertion is on the COUNT, so the number only has to be greater than one.
REPETITIONS = 50


class CountingTable(tuple):
    """A BINDING_TABLE that records how many rows anyone walked.

    Only ``__iter__`` is instrumented: ``len()`` and ``in`` on a tuple do not go through it,
    which is what makes an index lookup measurably different from a comprehension.
    """

    def __new__(cls, rows):
        instance = super().__new__(cls, rows)
        instance.visits = 0
        return instance

    def __iter__(self):
        for row in super().__iter__():
            self.visits += 1
            yield row


# ---- scanning implementations, kept for the mutation controls -----------------------------
#
# The pre-index bodies, verbatim. They exist so every "the work is gone" assertion can be
# shown to fail when the work comes back; nothing in the product imports them.
def _scanning_registered_profile_keys(parent_template):
    return {b["profile_key"] for b in gie_binding_table.BINDING_TABLE
            if b["parent_template"] == parent_template}


def _scanning_resolve_binding(parent_template, profile_key):
    hits = [b for b in gie_binding_table.BINDING_TABLE
            if b["parent_template"] == parent_template and b["profile_key"] == profile_key]
    return hits[0] if len(hits) == 1 else None


def _scanning_resolve_by_nvpair(parent_template, parent_nvpair):
    hits = [b for b in gie_binding_table.BINDING_TABLE
            if b["parent_template"] == parent_template and b["parent_nvpair"] == parent_nvpair]
    return hits[0] if len(hits) == 1 else None


def _scanning_all_registered_keys():
    return {b["profile_key"] for b in gie_engine.BINDING_TABLE}


def _scanning_guarded_keys():
    return {b["profile_key"] for b in gie_engine.BINDING_TABLE
            if b.get("mechanism") == PASSTHROUGH} - gie_engine.GIE_NATIVE_ELSEWHERE_KEYS


def _scanning_generic_keys(parent_template):
    keys = set()
    for pk in _scanning_registered_profile_keys(parent_template):
        b = _scanning_resolve_binding(parent_template, pk)
        if b and b.get("mechanism") == PASSTHROUGH:
            keys.add(pk)
    return keys


def _scanning_carry_forward_bindings(parent_template):
    out = []
    if not parent_template:
        return out
    for pk in sorted(_scanning_registered_profile_keys(parent_template)):
        b = _scanning_resolve_binding(parent_template, pk)
        if b and b.get("mechanism") == PASSTHROUGH:
            out.append({"parent_nvpair": b["parent_nvpair"], "profile_key": pk})
    return out


@pytest.fixture
def counted(monkeypatch):
    """Count registry row visits, with the indexes rebuilt from the counting table.

    Rebuilding first is what separates INITIALISATION from the hot path: the fixture hands
    back a table whose counter is reset after construction, so a test measures only what its
    own calls walked.
    """
    rows = CountingTable(gie_binding_table.BINDING_TABLE)
    monkeypatch.setattr(gie_binding_table, "BINDING_TABLE", rows)
    monkeypatch.setattr(gie_engine, "BINDING_TABLE", rows)
    rebuild_binding_indexes()
    rows.visits = 0
    try:
        yield rows
    finally:
        monkeypatch.undo()
        rebuild_binding_indexes()


@pytest.fixture
def scanning(monkeypatch):
    """Mutation control: put the scanning implementation back, everywhere it is read."""
    for name, replacement in (
        ("registered_profile_keys", _scanning_registered_profile_keys),
        ("resolve_binding", _scanning_resolve_binding),
        ("resolve_by_nvpair", _scanning_resolve_by_nvpair),
    ):
        monkeypatch.setattr(gie_binding_table, name, replacement)
        if hasattr(gie_engine, name):
            monkeypatch.setattr(gie_engine, name, replacement)
    monkeypatch.setattr(gie_engine, "gie_all_registered_keys", _scanning_all_registered_keys)
    monkeypatch.setattr(gie_engine, "gie_guarded_keys", _scanning_guarded_keys)
    monkeypatch.setattr(gie_engine, "_generic_keys", _scanning_generic_keys)
    monkeypatch.setattr(
        gie_engine, "gie_carry_forward_bindings", _scanning_carry_forward_bindings)


# =====================================================================================
# 1. EQUIVALENCE -- the indexed answer is the answer the scan gave
# =====================================================================================
def test_every_registered_row_resolves_to_its_own_object_by_both_identities():
    for row in BINDING_TABLE:
        parent = row["parent_template"]
        assert resolve_binding(parent, row["profile_key"]) is row
        assert resolve_by_nvpair(parent, row["parent_nvpair"]) is row


def test_every_parent_reports_exactly_the_keys_the_scan_reported():
    for parent in {b["parent_template"] for b in BINDING_TABLE}:
        assert registered_profile_keys(parent) == _scanning_registered_profile_keys(parent)
        assert gie_engine._generic_keys(parent) == _scanning_generic_keys(parent)
        assert gie_carry_forward_bindings(parent) == _scanning_carry_forward_bindings(parent)


def test_registry_wide_selections_match_the_scan():
    assert gie_all_registered_keys() == _scanning_all_registered_keys()
    assert gie_guarded_keys() == _scanning_guarded_keys()
    assert gie_no_log_profile_keys() == frozenset(
        b["profile_key"] for b in BINDING_TABLE if b.get("no_log"))


@pytest.mark.parametrize("parent,key", [
    ("no_such_parent", "ospf_cost"),
    (ROUTED, "no_such_profile_key"),
    ("no_such_parent", "no_such_profile_key"),
])
def test_a_missing_identity_still_answers_none(parent, key):
    assert resolve_binding(parent, key) is None
    assert resolve_by_nvpair(parent, key.upper()) is None


def test_an_unknown_parent_has_no_keys_and_nothing_to_carry():
    assert registered_profile_keys("no_such_parent") == set()
    assert gie_carry_forward_bindings("no_such_parent") == []
    assert gie_carry_forward_bindings(None) == []


# ---- the mutable-return contract ----------------------------------------------------
#
# Each of these helpers used to build a new container per call because it built it from
# scratch. Now there is a container to leak, so the copy is deliberate rather than incidental.
def test_a_caller_cannot_mutate_the_index_through_a_returned_container():
    keys = registered_profile_keys(ROUTED)
    expected = set(keys)
    keys.clear()
    keys.add("MUTATED-BY-CALLER")
    assert registered_profile_keys(ROUTED) == expected

    all_keys = gie_all_registered_keys()
    expected_all = set(all_keys)
    all_keys.clear()
    assert gie_all_registered_keys() == expected_all

    guarded = gie_guarded_keys()
    expected_guarded = set(guarded)
    guarded.clear()
    assert gie_guarded_keys() == expected_guarded

    generic = gie_engine._generic_keys(ROUTED)
    expected_generic = set(generic)
    generic.clear()
    assert gie_engine._generic_keys(ROUTED) == expected_generic

    carried = gie_carry_forward_bindings(ROUTED)
    expected_carried = [dict(entry) for entry in carried]
    carried[0]["profile_key"] = "MUTATED-BY-CALLER"
    carried.clear()
    assert gie_carry_forward_bindings(ROUTED) == expected_carried

    keymap = gie_nvpair_keymap()
    expected_keymap = dict(keymap)
    keymap.clear()
    assert gie_nvpair_keymap() == expected_keymap


def test_the_sensitive_name_set_is_immutable_so_it_may_be_shared():
    # The one helper that does NOT copy. It is allowed not to because a frozenset gives the
    # caller no way back into the index -- which is exactly why the others copy.
    assert isinstance(gie_no_log_profile_keys(), frozenset)


# ---- duplicates: resolve to None, and drop out of the per-parent selections ----------
def test_a_duplicated_identity_resolves_to_none_and_is_not_selected(monkeypatch):
    row = BINDING_TABLE[0]
    parent, profile_key = row["parent_template"], row["profile_key"]
    monkeypatch.setattr(
        gie_binding_table, "BINDING_TABLE", BINDING_TABLE + (dict(row),))
    rebuild_binding_indexes()
    try:
        # Ambiguous and missing are indistinguishable, on purpose: never first-wins,
        # never last-wins, and never an import-time exception.
        assert resolve_binding(parent, profile_key) is None
        assert resolve_by_nvpair(parent, row["parent_nvpair"]) is None
        # The key is still ENUMERATED for the parent -- the duplicate did not delete it --
        # but nothing that needs a resolved binding can select it.
        assert profile_key in registered_profile_keys(parent)
        assert profile_key not in gie_engine._generic_keys(parent)
        assert row["parent_nvpair"] not in {
            d["parent_nvpair"] for d in gie_carry_forward_bindings(parent)}
        # Registry-wide collections count every row, duplicate included, as before.
        assert profile_key in gie_all_registered_keys()
    finally:
        monkeypatch.undo()
        rebuild_binding_indexes()


def test_an_ambiguous_nvpair_still_fails_at_keymap_call_time(monkeypatch):
    """Error TIMING, not just the message: building the table must stay silent.

    The keymap is deliberately NOT indexed. It is built once per module invocation, so
    there is nothing hot to win here, and moving it into index construction would move its
    exception from a call the module makes to an import the module performs.
    """
    conflicting = dict(BINDING_TABLE[0], profile_key="different_public_key")
    monkeypatch.setattr(
        gie_engine, "BINDING_TABLE", BINDING_TABLE + (conflicting,))
    monkeypatch.setattr(
        gie_binding_table, "BINDING_TABLE", BINDING_TABLE + (conflicting,))
    # Index construction sees the conflict and says nothing.
    rebuild_binding_indexes()
    try:
        with pytest.raises(GieBindingError, match="ambiguous registered nvPair"):
            gie_nvpair_keymap()
    finally:
        monkeypatch.undo()
        rebuild_binding_indexes()


# =====================================================================================
# 2. THE WORK IS GONE -- counted, never timed
# =====================================================================================
PROFILE = {"enable_ospf": True, "ospf_cost": 100}


def _exact_lookups():
    gie_binding_table.resolve_binding(ROUTED, "ospf_cost")
    gie_binding_table.resolve_by_nvpair(ROUTED, "ospfCost")
    gie_binding_table.resolve_binding("no_such_parent", "ospf_cost")
    gie_binding_table.resolve_binding(ROUTED, "no_such_profile_key")


def _registry_wide_selections():
    gie_engine.gie_all_registered_keys()
    gie_engine.gie_guarded_keys()
    gie_engine.gie_no_log_profile_keys()


def _parent_selections():
    gie_binding_table.registered_profile_keys(ROUTED)
    gie_engine._generic_keys(ROUTED)
    gie_engine.gie_carry_forward_bindings(ROUTED)
    gie_engine.gie_extend_prof_spec({}, ROUTED, PROFILE)
    gie_engine.gie_contribute_nvpairs(ROUTED, PROFILE, "12.6.0.267")
    gie_engine.gie_invalid_parent_key(ROUTED, sorted(PROFILE))


def assert_hot_loop_visits_no_rows(counted, action):
    """THE assertion under test. Called by the green tests and by their mutation controls.

    Written once and shared on purpose: a control that re-words the assertion proves that
    its own wording fails, not that the real one does.
    """
    for _repetition in range(REPETITIONS):
        action()
    assert counted.visits == 0, (
        "{0} registry row visits across {1} repetitions; the hot path is scanning "
        "again".format(counted.visits, REPETITIONS)
    )


@pytest.mark.parametrize("action", [
    _exact_lookups, _registry_wide_selections, _parent_selections,
], ids=["exact_lookups", "registry_wide_selections", "parent_selections"])
def test_a_repeated_hot_operation_visits_no_registry_rows(counted, action):
    assert_hot_loop_visits_no_rows(counted, action)


@pytest.mark.parametrize("action", [
    _exact_lookups, _registry_wide_selections, _parent_selections,
], ids=["exact_lookups", "registry_wide_selections", "parent_selections"])
def test_that_assertion_turns_red_when_the_scan_comes_back(counted, scanning, action):
    """The counterfactual, run against the SAME assertion the green test runs.

    Not a restatement of it: ``scanning`` puts the pre-index bodies back in place and the
    identical call must fail. A counter that quietly stopped counting would make the green
    tests above pass while measuring nothing, and this is what catches that.
    """
    with pytest.raises(AssertionError, match="the hot path is scanning again"):
        assert_hot_loop_visits_no_rows(counted, action)


def test_the_module_validator_builds_the_registry_key_set_once_per_invocation():
    """The bounded hoist in dcnm_intf_gie_validate_parent_bindings, pinned.

    Ten interfaces, five profile keys each: the set used to be rebuilt 50 times per run
    because the call sat inside the per-profile-key loop.
    """
    from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

    instance = object.__new__(dcnm_interface.DcnmIntf)
    instance.dcnm_version = 12
    instance.pol_types = {12: {"eth_routed": ROUTED}}
    instance.config = [
        {"name": "Ethernet1/{0}".format(i + 1), "type": "eth",
         "profile": {"mode": "routed", "enable_ospf": True, "ospf_tag": "T",
                     "ospf_area_id": "0.0.0.0", "ospf_cost": 100}}
        for i in range(10)
    ]
    with mock.patch.object(
        dcnm_interface, "gie_all_registered_keys",
        wraps=gie_engine.gie_all_registered_keys,
    ) as global_set:
        instance.dcnm_intf_gie_validate_parent_bindings()
    assert global_set.call_count == 1


# =====================================================================================
# 3. THE CONTRACT WITH NO RUNTIME ENFORCEMENT
# =====================================================================================
def test_a_replaced_table_is_invisible_until_the_indexes_are_rebuilt(monkeypatch):
    """Pinned so that "fixing" it is recognisable as a regression.

    Nothing watches BINDING_TABLE for a replacement, because watching means fingerprinting
    or rescanning the table on every lookup -- the exact cost the indexes removed. The price
    is that a fixture which swaps the table and forgets to rebuild silently exercises the
    packaged registry. That price is paid by tests, once, in a rebuild call; putting a
    detector in the product would charge it to every lookup in every production run.
    """
    synthetic = dict(BINDING_TABLE[0], parent_template="synthetic_parent")
    monkeypatch.setattr(
        gie_binding_table, "BINDING_TABLE", BINDING_TABLE + (synthetic,))
    try:
        assert resolve_binding("synthetic_parent", synthetic["profile_key"]) is None
        rebuild_binding_indexes()
        assert resolve_binding("synthetic_parent", synthetic["profile_key"]) is synthetic
    finally:
        monkeypatch.undo()
        rebuild_binding_indexes()
    assert resolve_binding("synthetic_parent", synthetic["profile_key"]) is None


# ====================================================================================================
# Formerly test_gie_legacy_and_engine_never_collide.py
# The legacy path and the engine must never write the same nvPair.
#
# Both write into the same ``nvPairs`` dict in a payload builder. The legacy path assigns each
# field by hand and always writes, because every one of its keys carries a default in the argument
# spec -- omitting such a key in a playbook sets the default rather than preserving anything. The
# engine writes only keys the operator stated explicitly, and omission means "leave it alone".
#
# Those two contracts are incompatible on a shared key. If a field were written by both, the
# legacy assignment would put its default in before the engine decided to stay silent, and
# ``emit_when: explicit_only`` would quietly stop being true: omitting the key would reset the
# controller's value instead of preserving it. The engine's ``update`` runs last, so the damage
# would only appear on omission -- the one case no single-run test looks at.
#
# Nothing in the code prevents the overlap. Adding a registry row for an nvPair the builder
# already assigns is a two-line change that would pass every other test in this suite.
#
# Offline: no controller and no device.
# ====================================================================================================
MODULE = Path(gie_binding_table.__file__).resolve().parents[1] / "modules" / "dcnm_interface.py"

# Which parents each payload builder serves. Kept explicit rather than derived: the mapping is
# the thing under test, and deriving it from the same source would make the test agree with
# whatever the module happens to do.
BUILDERS = {
    "dcnm_intf_get_eth_payload": (
        "int_access_host",
        "int_trunk_host",
        # int_routed_host rides the same builder: the eth payload path serves every eth mode,
        # and gie_contribute_nvpairs sits at method level there, not inside a mode branch.
        "int_routed_host",
        # The PVLAN branch builds its set in interface_pvlan (no hand-written nvPair here) and then calls the
        # engine. Its own omission contract (merged keeps HAVE, replaced follows the withdrawal classifier) is pinned
        # through the real main() in test_pvlan_companions.py.
        "int_pvlan_host",
    ),
    "dcnm_intf_get_pc_payload": (
        "int_port_channel_access_host",
        "int_port_channel_trunk_host",
        "int_port_channel_dot1q_tunnel_host",
        "int_port_channel_pvlan_host",   # same note as int_pvlan_host
        # The peer-link branch sends only the engine's contribution; every other nvPair comes from HAVE in the comparator.
        "int_vpc_peer_link_po",
        # The routed port-channel (mode l3) shares the builder; its contribution is the method-level call after the
        # mode branches.
        "int_l3_port_channel",
    ),
    "dcnm_intf_get_vpc_payload": (
        "int_vpc_trunk_host",
        "int_vpc_access_host",
        # dot1q-tunnel shares the vPC builder: the base nvPairs come from the access branch and
        # gie_contribute_nvpairs sits at method level, after every mode branch.
        "int_vpc_dot1q_tunnel",
        "int_vpc_pvlan_host",   # same note as int_pvlan_host
        # The uplink branch sends only the engine's contribution and INTF_NAME; every other nvPair comes from HAVE in
        # the comparator.
        "int_vpc_uplink_access",
    ),
    # The two parents wired for the OSPF work. Neither had an engine hook before; both got the
    # same two calls as the eth path -- gie_extend_prof_spec in the validator and
    # gie_contribute_nvpairs in the builder.
    #
    # On the SVI builder the contribution sits at METHOD level, deliberately outside the mode
    # branch that precedes it: the registered keys belong to the parent, not to one SVI mode.
    # Inside the branch they would be emitted for some modes and silently dropped for others.
    "dcnm_intf_get_sub_intf_payload": (
        "int_subif",
    ),
    "dcnm_intf_get_svi_payload": (
        "int_vlan",
    ),
    # ONE builder, BOTH loopback parents. gie_contribute_nvpairs sits at the END of the method,
    # after the mode branches, so it runs for mode 'lo' and mode 'fabric' alike and keys off
    # intf["policy"] -- already resolved to whichever parent this item is.
    #
    # int_loopback was added here as a second key at first, which a dict silently resolves in
    # favour of the last one: the entry looked present and was discarded. Same key, one tuple.
    "dcnm_intf_get_loopback_payload": (
        "int_fabric_loopback_11_1",
        "int_loopback",
    ),
}

# A parent whose builder branch returns before the hand-written block, keyed to the line that opens the branch. The
# collision check runs on that branch alone, and the test requires the branch to end in a return placed before the
# first hand-written assignment of the builder.
EARLY_RETURN_BRANCHES = {
    # The uplink branch sends INTF_NAME and the engine's contribution, then returns; the vPC builder's hand-written
    # ENABLE_QOS and QOS_POLICY below it belong to the ordinary vPC modes.
    "int_vpc_uplink_access": 'if delem[profile]["mode"] == "uplink_access":',
}

ASSIGN = re.compile(r'nvPairs"\]\["([A-Z0-9_]+)"\]\s*=')
UPDATE_LITERAL = re.compile(r'nvPairs"\]\.update\(\{"([A-Z0-9_]+)"')


@pytest.fixture(scope="module")
def source():
    return MODULE.read_text()


def _builder_body(source, name):
    start = source.index("def {0}".format(name))
    nxt = source.find("\n    def ", start + 1)
    return source[start:nxt if nxt != -1 else len(source)]


def _early_return_branch(body, opener):
    """The text of one `if` branch of a builder, which must end in a bare return before any hand-written nvPair."""
    start = body.index(opener)
    indent = len(body[:start]) - len(body[:start].rstrip(" "))
    end = body.index("\n" + " " * (indent + 4) + "return\n", start)
    first_hand = min(m.start() for m in ASSIGN.finditer(body))
    assert end < first_hand, "the branch at {0!r} does not return before the hand-written block".format(opener)
    return body[start:end]


def _legacy_nvpairs(body):
    """nvPair names the builder writes by hand, excluding the engine's own update()."""
    return set(ASSIGN.findall(body)) | set(UPDATE_LITERAL.findall(body))


@pytest.mark.parametrize("builder,parents", sorted(BUILDERS.items()))
def test_no_registered_nvpair_is_also_written_by_hand(builder, parents, source):
    body = _builder_body(source, builder)
    for parent in [p for p in parents if p in EARLY_RETURN_BRANCHES]:
        branch = _early_return_branch(body, EARLY_RETURN_BRANCHES[parent])
        own = {b["parent_nvpair"] for b in BINDING_TABLE if b["parent_template"] == parent}
        assert not _legacy_nvpairs(branch) & own, (builder, parent, sorted(_legacy_nvpairs(branch) & own))
    parents = tuple(p for p in parents if p not in EARLY_RETURN_BRANCHES)
    legacy = _legacy_nvpairs(body)
    engine = {b["parent_nvpair"] for b in BINDING_TABLE if b["parent_template"] in parents}

    collision = legacy & engine
    assert not collision, (
        "{0} assigns {1} by hand and the engine also contributes it for {2}. The hand-written "
        "assignment runs first and always writes, so omitting the key in a playbook would set "
        "the legacy default instead of preserving the controller's value -- explicit_only would "
        "no longer hold. Either drop the registry row or remove the hand-written "
        "assignment.".format(builder, sorted(collision), ", ".join(parents))
    )


def test_every_builder_actually_writes_something_by_hand(source):
    """Guard the guard.

    If the extraction regexes ever stop matching -- a refactor to a helper, a renamed local --
    every test above would pass on an empty set and prove nothing. A builder that assigns no
    nvPair at all is far more likely to mean the extraction broke than that the builder changed.
    """
    for builder in BUILDERS:
        legacy = _legacy_nvpairs(_builder_body(source, builder))
        assert len(legacy) >= 5, (
            "{0}: found only {1} hand-written nvPairs. The collision test above is only "
            "meaningful while this extraction works; this count dropping means the regexes no "
            "longer match how the builder writes.".format(builder, len(legacy))
        )


def test_every_registered_parent_belongs_to_exactly_one_builder():
    """A parent with rows but no builder in the map would be silently unchecked above."""
    registered = {b["parent_template"] for b in BINDING_TABLE}
    mapped = {p for parents in BUILDERS.values() for p in parents}

    assert registered <= mapped, (
        "these parents have rows in the binding table but no builder in BUILDERS, so the "
        "collision check never runs for them: {0}".format(sorted(registered - mapped))
    )

    counts = {}
    for parents in BUILDERS.values():
        for p in parents:
            counts[p] = counts.get(p, 0) + 1
    dupes = [p for p, n in counts.items() if n > 1]
    assert not dupes, "a parent is mapped to more than one builder: {0}".format(sorted(dupes))


# ====================================================================================================
# Formerly test_gie_every_registered_parent_is_wired.py
# Registering a parent in the table is only half the work; the module has to be wired for it.
#
# A binding needs two things on the module side, and neither is implied by the registry row:
#
#   gie_extend_prof_spec      puts the public key into that parent's argument spec. Without it,
#                             validate_list_of_dicts drops the key as an unknown legacy field and
#                             the value never reaches the payload. No error -- a silent no-op.
#   gie_contribute_nvpairs    puts the value into the parent's nvPairs in the payload builder.
#                             Without it the key validates and then goes nowhere.
#
# Both were missing for the two vPC parents when their eleven bindings were registered. The table
# was correct, the engine was correct, every existing test passed, and nothing would have been
# written to a vPC interface. These tests exist so that the next parent added to the table cannot
# repeat it.
#
# Offline: no controller and no device.
# ====================================================================================================
PARENTS = sorted({b["parent_template"] for b in BINDING_TABLE})

# The loopback parent is reached through the OSPF-MD call sites rather than a generic spec
# extension; its keys have their own dedicated validate. It is excluded here deliberately, not
# forgotten -- see the child_pti notes in the engine.
# The loopback parent registers no bindings at all since the OSPF-auth retirement, so it is
# exempt from the spec plumbing for the stronger reason: there is nothing to plumb.
SPEC_EXEMPT = {"int_fabric_loopback_11_1"}


@pytest.mark.parametrize("parent", [p for p in PARENTS if p not in SPEC_EXEMPT])
def test_every_registered_parent_has_its_spec_extended(parent, source):
    """The public key must be able to survive argument validation for this parent."""
    # A literal parent name is the usual shape, but it cannot be the only one accepted. The
    # loopback validator serves TWO parents -- int_loopback and int_fabric_loopback_11_1 -- and
    # resolves which one per config item at run time, so no literal exists for either. Requiring
    # one would force the code to be written worse to satisfy the grep.
    #
    # The dynamic form is recognised instead, and the behavioural assertion below is what
    # actually proves the property: a grep can only say a call was written, never that it works.
    pattern = re.compile(
        r'gie_extend_prof_spec\([^)]*"' + re.escape(parent) + r'"'
        r'|gie_extend_prof_spec\(\s*lo_prof_spec,\s*parent\b', re.S
    )
    assert pattern.search(source), (
        "{0} has rows in the binding table but no gie_extend_prof_spec call. Its keys would be "
        "dropped as unknown during argument validation and nothing would reach the "
        "controller.".format(parent)
    )


# dcnm_intf_get_loopback_payload is deliberately absent from the list below. WITHDRAWN: the
# fabric loopback registers no bindings since OSPF authentication there was returned to
# fabricSettings, so requiring it to call the engine would assert plumbing for an empty set.
# test_binding_engine.test_the_loopback_parent_registers_nothing pins the other half.
def test_every_payload_builder_that_can_carry_bindings_calls_the_engine(source):
    """A builder whose parent has rows must hand the profile to the engine.

    Checked by counting call sites per function rather than per parent: a builder serves several
    parents (the three port-channel modes share one), so the meaningful invariant is that no
    builder is left out.
    """
    # loopback dropped from the pattern with the OSPF-auth retirement: its parent registers no
    # bindings, so requiring it to call the engine would assert plumbing for an empty set.
    # sub_int and svi joined when int_subif and int_vlan were wired for OSPF.
    builders = re.findall(
        r"def (dcnm_intf_get_(?:pc|vpc|eth|sub_intf|svi)_payload)\b", source
    )
    assert set(builders) == {
        "dcnm_intf_get_pc_payload",
        "dcnm_intf_get_vpc_payload",
        "dcnm_intf_get_eth_payload",
        "dcnm_intf_get_sub_intf_payload",
        "dcnm_intf_get_svi_payload",
    }, "a payload builder was renamed or added; this test needs updating deliberately"

    for name in builders:
        start = source.index("def {0}".format(name))
        nxt = source.find("\n    def ", start + 1)
        body = source[start:nxt if nxt != -1 else len(source)]
        assert "gie_contribute_nvpairs(" in body, (
            "{0} never calls gie_contribute_nvpairs, so registered keys validate and then go "
            "nowhere for every parent it builds.".format(name)
        )


def test_the_vpc_specs_actually_gain_the_registered_keys():
    """Behavioural counterpart to the source check above.

    The source test proves the call exists; this proves the call does what it is there for, so a
    future refactor that keeps the call but breaks the wiring still fails.
    """
    for parent, expected in (
        ("int_vpc_trunk_host",
         {"guard_mode", "disable_lldp_transmit", "acl_filter", "spanning_tree_port_type",
          "disable_qos_stats", "disable_queuing_stats"}),
        # access does not declare GUARD_MODE, so guard_mode must NOT appear here.
        ("int_vpc_access_host",
         {"disable_lldp_transmit", "acl_filter", "spanning_tree_port_type",
          "disable_qos_stats", "disable_queuing_stats"}),
    ):
        spec = {"mode": {"required": True, "type": "str"}}
        written = {k: "x" for k in expected}
        gie_extend_prof_spec(spec, parent, written)
        gained = set(spec) - {"mode"}
        assert gained == expected, "{0}: spec gained {1}".format(parent, sorted(gained))

    spec = {"mode": {"required": True, "type": "str"}}
    gie_extend_prof_spec(spec, "int_vpc_access_host", {"guard_mode": "root"})
    assert "guard_mode" not in spec, (
        "guard_mode reached the vPC access spec; that template does not declare GUARD_MODE"
    )
