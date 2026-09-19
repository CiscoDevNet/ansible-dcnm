"""Every binding is on the processing route its contract says, and nothing else.

THE ERROR THIS EXISTS TO CATCH
    Four ``int_routed_host`` OSPF bindings were registered ``child_pti`` by copying a
    prediction from the phase-0 ledger. They own no dedicated validation, so the label routed
    them around the generic path. It was caught by a hand-written test that happened to exist
    for that parent; on a parent without one it would have shipped.

WHY THE OBVIOUS TEST DOES NOT WORK
    "Assert a wrong parent is still rejected" is NOT sufficient, and the counterexample is
    concrete. ``gie_guarded_keys()`` returns bare ``profile_key`` strings with no parent
    qualification:

        return {b["profile_key"] for b in BINDING_TABLE if b["mechanism"] == "passthrough"}

    Seven parents register ``acl_filter``. Flip ONE of them to ``child_pti`` and the key stays
    in the guarded set via the other six -- the wrong-parent rejection still fires, looking
    healthy -- while that parent silently loses its generic arg-spec entry and its
    carry-forward. Reproduced in ``test_mislabelling_one_parent_of_a_shared_key_is_caught``.

    So every check here is PARENT-QUALIFIED. That is the property the global guard lacks.

WHERE THE EXPECTED ANSWER COMES FROM
    ``DEDICATED_ROUTE`` below, never from the ``mechanism`` field being tested -- reading the
    answer off the thing under test would make this vacuous. It names the bindings that own a
    hand-written validation path, with the validator and the observable message each one is
    responsible for. Everything else must be generic.

    A new ``child_pti`` binding therefore FAILS here until someone adds it deliberately and
    states what validates it. It is never skipped.

WHAT THIS FILE COVERS, AND WHAT IT DOES NOT
    This is a STRUCTURAL contract over the table. It was verified by sabotage: replacing
    ``dcnm_intf_validate_ethernet_interface_input`` with a function that raises left every test
    here passing, with zero calls. So placement is all it proves --

      * the positive control drives ``gie_contribute_nvpairs`` (the ENGINE), not survival
        through the module's validator and builder;
      * the preservation check asserts a binding appears in the carry-forward SELECTOR, not
        that its value survives a WANT/HAVE comparison;
      * finding the key name and guard message in a validator's source shows the code is
        plausibly responsible, not that it rejects anything.

    The module flow is exercised in the two sections at the end of this file, and end to end
    through the real comparator in ``test_gie_routed_ospf_have_representation.py`` and
    ``test_dcnm_intf_binding_integration.py``.

Offline: no controller and no device.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import inspect
from unittest import mock

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table, gie_engine
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    BINDING_TABLE,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    gie_carry_forward_bindings,
    gie_contribute_nvpairs,
    gie_guarded_keys,
    gie_invalid_parent_key,
)
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

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


def _key(binding):
    return (binding["parent_template"], binding["parent_nvpair"])


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
    wrong_parent = _a_parent_that_does_not_register(binding["profile_key"])
    if wrong_parent is None:
        pytest.skip("{0} is registered on every parent in the table".format(binding["profile_key"]))
    assert gie_invalid_parent_key(wrong_parent, ["mode", binding["profile_key"]]) == (
        binding["profile_key"]
    )


# =====================================================================================
# BEHAVIOUR — 2. the correct parent carries the intent through to the nvPair
# =====================================================================================
@pytest.mark.parametrize(
    "key", sorted({_key(b) for b in BINDING_TABLE if _key(b) not in DEDICATED_ROUTE})
)
def test_a_generic_binding_reaches_the_payload_in_wire_form(key):
    """ENGINE-level: gie_contribute_nvpairs, not the module's validator/builder pair.

    Placement is not enough: the value has to survive to an nvPair, in NDFC's encoding.

    nvPairs is a string-valued map, so a native bool left there reproduces the non-convergence
    the wire form exists to prevent.
    """
    binding = next(b for b in BINDING_TABLE if _key(b) == key)
    value = _sample_for(binding)
    nvpairs, error = gie_contribute_nvpairs(
        binding["parent_template"], {binding["profile_key"]: value}, NDFC_VERSION
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
        assert emitted == str(value)


# =====================================================================================
# 3. omission — the SELECTOR only
# =====================================================================================
@pytest.mark.parametrize(
    "key", sorted({_key(b) for b in BINDING_TABLE if _key(b) not in DEDICATED_ROUTE})
)
def test_a_generic_binding_is_offered_to_the_carry_forward_selector(key):
    """Named for what it checks: the binding is OFFERED for carry-forward.

    That a value actually survives a WANT/HAVE comparison is a different claim, and it is
    proven where the real comparator runs -- test_gie_routed_ospf_have_representation.py
    (test_an_explicit_cost_is_not_overwritten_by_have, test_a_second_identical_run_produces_no_payload)
    and test_dcnm_intf_binding_integration.py (test_registered_binding_is_carried_when_omitted).
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
    """Swap the table everywhere it is actually read.

    Both targets are load-bearing, and patching only the first is a trap worth naming: it makes
    the mutation tests pass for the wrong reason. ``gie_engine`` holds its own reference, used
    by ``gie_guarded_keys()``; but ``resolve_binding`` and ``registered_profile_keys`` live in
    ``gie_binding_table`` and read ITS module global, which is what ``_generic_keys()`` and
    ``gie_carry_forward_bindings()`` go through. Patch only ``gie_engine`` and the
    parent-qualified checks keep reporting the UNMUTATED placement.
    """
    def _apply(table):
        monkeypatch.setattr(gie_engine, "BINDING_TABLE", table)
        monkeypatch.setattr(gie_binding_table, "BINDING_TABLE", table)
        return table
    return _apply


def test_mislabelling_one_parent_of_a_shared_key_is_caught(patched_table):
    """The counterexample, pinned.

    ``acl_filter`` is registered on seven parents. Mislabelling ONE leaves the key guarded by
    the other six, so a guard-only test sees nothing wrong. The parent-qualified checks do.
    """
    key = ("int_access_host", "ACL_FILTER")
    table = patched_table(_with_mechanism(key, "child_pti"))

    assert "acl_filter" in {
        b["profile_key"] for b in table if b.get("mechanism") == "passthrough"
    }, "fixture no longer reproduces the counterexample: the key must stay globally guarded"

    violations = _generic_route_violations(table)
    assert violations, "a mislabelled shared key went undetected"
    assert any("int_access_host" in v and "ACL_FILTER" in v for v in violations)


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
    key = ("int_routed_host", "OSPF_COST")
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
    "ENABLE_OSPF": "true",
    "OSPF_TAG": "WP98",
    "OSPF_AREA_ID": "0.0.0.0",
    "OSPF_COST": "100",
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
