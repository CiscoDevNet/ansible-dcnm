"""The harness restores exactly what it installed, and nothing else.

WHY THIS FILE EXISTS

`netcommon`'s `ModuleTestCase.setUp` installs `exit_json`/`fail_json` doubles and
registers their removal with `addCleanup`. Those callbacks run from `doCleanups()`, which
a runner calls and a hand-driven TestCase does not. An earlier task-local harness called
only `tearDown()`, so every invocation left a started patcher behind. Each suite passed
alone; run in one session with `test_dcnm_intf_no_log_contract.py` -- which measures
redaction against the real serialiser -- 19 of its tests failed, because a leaked double
makes `fail_json` raise instead of serialising.

The first containment was a blanket `patch.stopall()`. That works, and it is too broad:
`stopall()` stops every patcher started anywhere, including ones this harness never
installed. These tests pin the narrower contract the harness now implements -- own your
cleanup, leave everything else alone -- and would fail under either the leak or the
sledgehammer.

NOT LIVE TESTED IN THIS GENERATION.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import patch

import pytest

from ansible.module_utils import basic

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from .gie_withdrawal_harness import (
    ACCESS,
    IF_A,
    base_for,
    cfg,
    harness_case,
    run_configs,
)


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
    """The gap G18 characterized: `setUp()` used to run OUTSIDE the try.

    `A161Base.setUp` starts six patchers in sequence and `ModuleTestCase.setUp` registers
    its cleanups as it goes. A failure partway through therefore leaves some already
    installed -- and with setUp outside the try, the exception propagated before any
    cleanup ran. The netcommon `exit_json`/`fail_json` doubles stayed live for the rest of
    the session, on the one path where something had already gone wrong.

    This test FAILS on the pre-fix harness and passes after it. It asserts the serialiser
    methods specifically, not merely "no exception".
    """
    from .test_dcnm_intf_binding_module_path import A161Base

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
    from .test_dcnm_intf_binding_module_path import A161Base

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
    from .test_dcnm_intf_binding_module_path import A161Base
    original = A161Base.ndfc_version
    run_configs([cfg(IF_A, base_for(ACCESS), deploy=False)], "replaced", None,
                ndfc_version="12.6.0.266")
    assert A161Base.ndfc_version == original, (
        "the version override was written to the class and now applies to every later "
        "case in this session")
