"""Contracts of the shared test helpers that the suites rely on."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import hashlib
import json
import os
import pytest

from unittest.mock import patch
from ansible.module_utils import basic
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from .helpers import fixture_cases as fc
from .helpers.binding_harness import ACCESS
from .helpers.binding_harness import IF_A
from .helpers.binding_harness import base_for
from .helpers.binding_harness import cfg
from .helpers.binding_harness import harness_case
from .helpers.binding_harness import run_configs
from .helpers.ethernet_controller import FIXTURE
from .helpers.ethernet_controller import FakeController
from .helpers.ethernet_controller import PREVIEW_MARK
from .helpers.ethernet_controller import RECOMPUTE_FLAGS
from .helpers.ethernet_controller import SERIAL
from .helpers.ethernet_controller import TRANSITIONS
from .helpers.ethernet_controller import preview


# ====================================================================================================
# Formerly test_helper_contracts.py
# Contracts of the shared test helpers that the suites rely on.
# ====================================================================================================
BUNDLE = {
    "_bundle": "synthetic",
    "sources": {"cap": {"file": "cap.json", "sha256": "0" * 64}},
    "baselines": {"cap.base": {"a": "1", "b": False, "c": None, "d": 0}},
    "cases": {"cap": {
        "same": {"$baseline": "cap.base"},
        "changed": {"$baseline": "cap.base", "$set": {"b": "false", "e": "new"}, "$unset": ["d"]},
        "nulled": {"$baseline": "cap.base", "$set": {"a": None}},
        "items": [{"$baseline": "cap.base"}, {"plain": True}],
    }},
}


@pytest.fixture
def synthetic(tmp_path, monkeypatch):
    def install(bundle):
        (tmp_path / "synthetic.json").write_text(json.dumps(bundle))
        monkeypatch.setattr(fc, "FIXTURE_DIR", str(tmp_path))
        monkeypatch.setattr(fc, "_FILES", {})
        monkeypatch.setattr(fc, "SOURCES", {"cap": ("synthetic.json", "cap")})
    return install


def test_baseline_reference_is_expanded_with_types_and_order_kept(synthetic):
    synthetic(BUNDLE)
    case = fc.load_case("cap")
    assert json.dumps(case["same"]) == json.dumps({"a": "1", "b": False, "c": None, "d": 0})
    # $set replaces in place and appends a new key; a string "false" stays a string; $unset deletes
    assert json.dumps(case["changed"]) == json.dumps({"a": "1", "b": "false", "c": None, "e": "new"})
    # a null override sets null, it does not delete the key
    assert "a" in case["nulled"] and case["nulled"]["a"] is None
    assert case["items"] == [{"a": "1", "b": False, "c": None, "d": 0}, {"plain": True}]


def test_every_call_returns_a_fresh_copy(synthetic):
    synthetic(BUNDLE)
    first = fc.load_case("cap")
    first["same"]["a"] = "mutated"
    first["items"].append("extra")
    second = fc.load_case("cap")
    assert second["same"]["a"] == "1" and len(second["items"]) == 2


@pytest.mark.parametrize("ref, error", [
    ({"$baseline": "missing"}, KeyError),
    ({"$baseline": "cap.base", "$unset": ["absent"]}, KeyError),
    ({"$baseline": "cap.base", "$sett": {"a": "2"}}, ValueError),
], ids=["unknown-baseline", "unset-missing-key", "unknown-marker-key"])
def test_malformed_references_are_refused(synthetic, ref, error):
    bundle = json.loads(json.dumps(BUNDLE))
    bundle["cases"]["cap"] = {"node": ref}
    synthetic(bundle)
    with pytest.raises(error):
        fc.load_case("cap")


def test_a_baseline_may_not_refer_to_another_baseline(synthetic):
    bundle = json.loads(json.dumps(BUNDLE))
    bundle["baselines"]["cap.nested"] = {"inner": {"$baseline": "cap.base"}}
    synthetic(bundle)
    with pytest.raises(ValueError):
        fc.load_case("cap")


def test_every_capture_loads_and_every_bundle_lists_exactly_its_captures():
    by_file = {}
    for name, (filename, key) in fc.SOURCES.items():
        by_file.setdefault(filename, set()).add(key)
        if key is not None and set(fc._read(filename)["cases"][key]) == {"text", "sha256"}:
            assert isinstance(fc.load_text(name), str)
            with pytest.raises(TypeError):
                fc.load_case(name)
        else:
            assert fc.load_case(name)
    on_disk = set(os.listdir(fc.FIXTURE_DIR))
    assert on_disk == set(by_file), "every bundle is referenced and every referenced bundle exists"
    for filename, keys in by_file.items():
        if keys != {None}:
            data = fc._read(filename)
            assert set(data["sources"]) == keys == set(data["cases"]), filename


def test_text_captures_match_their_recorded_sha256():
    for name, (filename, key) in fc.SOURCES.items():
        case = fc._read(filename)["cases"].get(key) if key else None
        if isinstance(case, dict) and set(case) == {"text", "sha256"}:
            assert hashlib.sha256(fc.load_text(name).encode("utf-8")).hexdigest() == case["sha256"], name


# ====================================================================================================
# Formerly test_dcnm_intf_withdrawal_harness_cleanup.py
# The harness restores exactly what it installed, and nothing else.
#
# WHY THIS FILE EXISTS
#
# `netcommon`'s `ModuleTestCase.setUp` installs `exit_json`/`fail_json` doubles and
# registers their removal with `addCleanup`. Those callbacks run from `doCleanups()`, which
# a runner calls and a hand-driven TestCase does not. An earlier task-local harness called
# only `tearDown()`, so every invocation left a started patcher behind. Each suite passed
# alone; run in one session with `test_no_log_and_redaction.py` -- which measures
# redaction against the real serialiser -- 19 of its tests failed, because a leaked double
# makes `fail_json` raise instead of serialising.
#
# The first containment was a blanket `patch.stopall()`. That works, and it is too broad:
# `stopall()` stops every patcher started anywhere, including ones this harness never
# installed. These tests pin the narrower contract the harness now implements -- own your
# cleanup, leave everything else alone -- and would fail under either the leak or the
# sledgehammer.
#
# NOT LIVE TESTED.
# ====================================================================================================
def test_the_harness_restores_the_serialiser_it_replaced():
    """After a case, `exit_json`/`fail_json` are whatever they were before it."""
    before = (basic.AnsibleModule.exit_json, basic.AnsibleModule.fail_json)
    run_configs([cfg(IF_A, base_for(ACCESS), deploy=False)], "replaced", None)
    after = (basic.AnsibleModule.exit_json, basic.AnsibleModule.fail_json)
    assert after == before, (
        "the harness left the netcommon doubles installed; the next test in the session "
        "would measure them instead of Ansible's real result formatting")


def test_cleanup_still_runs_when_the_body_raises():
    """Exception safety. A leak on the failure path is the one that poisons a whole run,
    because it happens exactly when something already went wrong."""
    before = (basic.AnsibleModule.exit_json, basic.AnsibleModule.fail_json)
    boom = RuntimeError("deliberate")
    with pytest.raises(RuntimeError):
        with harness_case():
            raise boom
    after = (basic.AnsibleModule.exit_json, basic.AnsibleModule.fail_json)
    assert after == before, "an exception inside a case left the doubles installed"


def test_an_unrelated_active_patch_survives_the_harness():
    """The difference between owning your cleanup and calling `patch.stopall()`.

    An unrelated patcher is started here and must still be active after a full harness
    case. `stopall()` would have stopped it; per-case `tearDown()` + `doCleanups()` does
    not, because it only unwinds what the case itself installed.
    """
    sentinel = object()
    unrelated = patch.object(module, "__doc__", sentinel)
    unrelated.start()
    try:
        assert module.__doc__ is sentinel, "the control patch did not take effect"
        run_configs([cfg(IF_A, base_for(ACCESS), deploy=False)], "replaced", None)
        assert module.__doc__ is sentinel, (
            "a patch this harness never started was stopped by it; cleanup is too broad "
            "and would silently disable an unrelated test's fixture")
    finally:
        unrelated.stop()
    assert module.__doc__ is not sentinel, "the control patch did not unwind"


def test_a_partial_setup_still_unwinds_the_patches_it_installed():
    """The gap: `setUp()` used to run OUTSIDE the try.

    `A161Base.setUp` starts six patchers in sequence and `ModuleTestCase.setUp` registers
    its cleanups as it goes. A failure partway through therefore leaves some already
    installed -- and with setUp outside the try, the exception propagated before any
    cleanup ran. The netcommon `exit_json`/`fail_json` doubles stayed live for the rest of
    the session, on the one path where something had already gone wrong.

    This test FAILS on the pre-fix harness and passes after it. It asserts the serialiser
    methods specifically, not merely "no exception".
    """
    from .helpers.module_runner import A161Base

    before = (basic.AnsibleModule.exit_json, basic.AnsibleModule.fail_json)
    original_setup = A161Base.setUp
    started = []

    def interrupted_setup(case):
        started.append(case)
        original_setup(case)                 # installs the patches...
        raise RuntimeError("synthetic setup interruption")   # ...then fails

    try:
        with patch.object(A161Base, "setUp", interrupted_setup):
            with pytest.raises(RuntimeError, match="synthetic setup interruption"):
                with harness_case():
                    raise AssertionError("the body must not run after a failed setUp")

        after = (basic.AnsibleModule.exit_json, basic.AnsibleModule.fail_json)
        assert after == before, (
            "a partial setUp leaked the netcommon serialiser doubles: exit_json/fail_json "
            "are not what they were before the case, so every later test in this session "
            "would measure the doubles instead of Ansible's real result formatting")
    finally:
        # Belt and braces. If the assertion above fails, the doubles really are still
        # installed and every later test in this file would be measuring them, so the
        # interrupted case is unwound here regardless of the outcome.
        for case in reversed(started):
            try:
                case.tearDown()
            except Exception:                                    # noqa: BLE001
                pass
            finally:
                case.doCleanups()


def test_a_partial_setup_leaves_unrelated_patches_alone():
    """The other half: unwinding a failed case must not become a session-wide reset.

    `patch.stopall()` would make the test above pass while silently stopping patches this
    harness never installed. This one fails under that shortcut.
    """
    from .helpers.module_runner import A161Base

    sentinel = object()
    unrelated = patch.object(module, "__doc__", sentinel)
    unrelated.start()
    original_setup = A161Base.setUp
    started = []

    def interrupted_setup(case):
        started.append(case)
        original_setup(case)
        raise RuntimeError("synthetic setup interruption")

    try:
        with patch.object(A161Base, "setUp", interrupted_setup):
            with pytest.raises(RuntimeError):
                with harness_case():
                    pass
        assert module.__doc__ is sentinel, (
            "unwinding a failed setUp also stopped a patch this harness never started")
    finally:
        for case in reversed(started):
            try:
                case.tearDown()
            except Exception:                                    # noqa: BLE001
                pass
            finally:
                case.doCleanups()
        unrelated.stop()


def test_the_case_does_not_leak_its_version_override_to_the_next_case():
    """`ndfc_version` is set on the INSTANCE. A class attribute would outlive the case and
    silently retune every later test in the session."""
    from .helpers.module_runner import A161Base
    original = A161Base.ndfc_version
    run_configs([cfg(IF_A, base_for(ACCESS), deploy=False)], "replaced", None,
                ndfc_version="12.6.0.266")
    assert A161Base.ndfc_version == original, (
        "the version override was written to the class and now applies to every later "
        "case in this session")


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_harness.py
# Harness for the native Ethernet PVLAN tests: real main(), external boundary mocked only.
#
# Self-contained and collection-local. It mocks ONLY the external boundary -- inventory, version,
# the transport (dcnm_send), the bulk-API probe, fabric details and sleep -- through a stateful,
# path-routed fake controller that records every request in order. Nothing under test (builder,
# reconciliation, preflight, pre-deploy gate) is stubbed. Fixtures come from
# fixtures/pvlan_ethernet_cases.json#dcnm_intf_pvlan_measured, sanitized from measured discovery evidence.
#
# The fake controller APPLIES a successful modify to its stored intent, so later reads (post-deploy
# readback, a second run) see what the module actually sent. Pending is NEVER computed by the fake:
# each preview answer is a fixture or an explicit test value, so the gate is judged against data
# it did not produce.
#
# This file holds the harness plus its own sanity tests; it defines no product behavior.
# ====================================================================================================
# ---------------------------------------------------------------- harness self-tests
def test_harness_fixture_is_sanitized_and_complete():
    raw = json.dumps(FIXTURE)
    for leaked in ("9648E3J5P6M", "FAB1", "Leaf-101", "192.168.", "POLICY-"):
        assert leaked not in raw
    assert {"TU2", "TX1", "TX2", "PU3", "G6-M1", "G6-L1", "G6-MR"} <= set(TRANSITIONS)
    assert "MAPPING_LIST[]" in FIXTURE["template_variables"]


def test_harness_records_before_answering_and_never_computes_pending():
    ctrl = FakeController()
    assert ctrl(None, "GET", "/x" + PREVIEW_MARK + SERIAL + "?" + RECOMPUTE_FLAGS) == preview([])
    assert ctrl.calls[0][0] == "GET" and ctrl.order() == ["PREVIEW"]
