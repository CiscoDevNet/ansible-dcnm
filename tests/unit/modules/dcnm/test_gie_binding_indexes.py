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
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from unittest import mock
from ansible_collections.cisco.dcnm.plugins.module_utils import (
    gie_binding_table,
    gie_engine,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    BINDING_TABLE,
    rebuild_binding_indexes,
    registered_profile_keys,
    resolve_binding,
    resolve_by_nvpair,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    GieBindingError,
    gie_all_registered_keys,
    gie_carry_forward_bindings,
    gie_guarded_keys,
    gie_no_log_profile_keys,
    gie_nvpair_keymap,
)

ROUTED = "int_routed_host"
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
            if b.get("mechanism") == PASSTHROUGH}


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
    gie_binding_table.resolve_by_nvpair(ROUTED, "OSPF_COST")
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
