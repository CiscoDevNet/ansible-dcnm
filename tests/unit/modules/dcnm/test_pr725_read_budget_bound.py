"""PR725: acceptance tests for the implemented bounded-recovery contract.

The candidate must pass all 11 cases. As a negative control, the scaling cases
fail on the accepted indexing base `64e6b0ce95de0780b9b788aa1eec054ab024b3d0`,
before recovery was implemented. They fail on request-count assertions, not on
an import, a fixture or a skip. The earlier diagnostic base `dd0a456b` has the
same read-path behavior; its evidence remains separate.

Three parametrizations PASS on the baseline, and that is the point: with a single
requested interface and a single pass the baseline already spends 3 + 3 = 6
requests, exactly the accepted ceiling. The contract does not change the small
case; it stops the cost from growing with the interface count, with a second
pass, or across an invalidation. A run of this file on the frozen baseline is
expected to report **8 failed, 3 passed**.

Do not add a skip marker, an `xfail`, or a mock that bypasses the reader. The
file must remain red for the right reason on the baseline and green on the
implemented candidate, without weakening its assertions.

IMPLEMENTED CONTRACT, REVISION 2
--------------------------------
Revision 1 reset the budget on `dcnm_intf_invalidate_serial_authority`. That was
wrong and is withdrawn: the bulk reader invalidates the serial before *every*
read, including a repeated failed one, so the reset would have handed a real
`overridden` run a second full budget. Architect decisions applied here: Design A
(counter), B = 2, per queried physical serial, per module instance.

Unit      one FAILED read invocation = one call to the bounded GET helper from an
          interface-policy reader whose outcome is "unavailable" (transport
          exception, non-200, or a 200 whose payload cannot be trusted).
Key       the normalized physical query serial actually sent to the endpoint,
          `_dcnm_intf_normalize_serial(serialNumber)`, folded case-insensitively.
          One endpoint, one budget.
Bound     B = 2 consecutive failed invocations per serial per module run.
          Two, not one: the first is spent on the bulk endpoint before any
          individual read exists, so B = 1 would delete the per-interface
          fallback that `TestFallbackMustSurvive` requires.
Reset     ONLY a newly obtained, validated response for that same serial in this
          run. NOT on invalidation, NOT on `refresh=True`, NOT on a second pass
          or a different diff phase, NOT on a cache hit, and NOT on a bare
          RETURN_CODE 200 whose payload fails validation.
Lifetime  one `DcnmIntf` instance. It deliberately spans states, diff phases and
          repeated passes over the same serial — that span IS the bound.
Exhausted the reader issues no further request for that serial and marks the
          target unavailable without one. Existing fail-closed guards still
          refuse writes over unknown state. A pathological first individual
          probe can withhold later healthy interfaces; this is an accepted
          availability tradeoff, not proof that those interfaces are absent.

WHAT THE CEILING MEANS, PRECISELY
---------------------------------
During a persistent-failure episode against one switch: at most 6 interface-
policy requests and at most 6 seconds of SCHEDULED sleep for that switch, for the
lifetime of one module run, whatever the interface count. A malformed 200 ends
its invocation after one attempt, so its ceiling is 2 requests and no sleep.

It is NOT a ceiling on the module's wall-clock duration, NOT a ceiling on all of
the module's requests (successful per-interface reads stay unbounded: `3 + N`
remains `3 + N`), and NOT a ceiling on the summary, breakout, access-mode or
`query` endpoints, which stay outside this budget and keep their current
behaviour — see the `24` group in the characterization file.

Baseline for comparison, one switch, N interfaces (measured, see
`evidence/B1-baseline/11_read-call-bounds-table.md`):
    persistent failure   3 + 3N requests, 3(N + 1) scheduled seconds
    malformed HTTP 200   1 + N requests, 0 seconds

NOT LIVE TESTED IN THIS GENERATION. Synthetic identities only.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest import mock

import pytest

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface
from .test_pr725_read_budget_characterization import (
    ERROR_500,
    MALFORMED_200,
    _Clock,
    _Transport,
    _constant,
    _deferred_stub,
    _persistent_500,
    _run_get_have,
    _state,
    _unavailable,
    _want,
    run_module_path,
)

DcnmIntf = dcnm_interface.DcnmIntf

# Historical constant names are retained; these values implement contract r2.
PROPOSED_FAILED_INVOCATIONS = 2
ATTEMPTS_PER_INVOCATION = 3
REQUEST_CEILING_PER_SWITCH = PROPOSED_FAILED_INVOCATIONS * ATTEMPTS_PER_INVOCATION
SLEEP_CEILING_PER_SWITCH = REQUEST_CEILING_PER_SWITCH
# A 200 ends its invocation on the first attempt, so it can never reach the
# three-attempt ceiling.
REQUEST_CEILING_PER_SWITCH_NO_RETRY = PROPOSED_FAILED_INVOCATIONS

LARGE = 50


def _report(transport, clock):
    return "bulk=%d individual=%d total=%d sleeps=%d sleep_s=%g" % (
        transport.counts["bulk"],
        transport.counts["individual"],
        transport.total,
        clock.calls,
        clock.seconds,
    )


@pytest.mark.parametrize(
    "responder,label",
    [
        (_constant(ERROR_500), "persistent HTTP 500"),
        (
            _constant(dcnm_interface.AnsibleConnectionError("synthetic offline failure")),
            "persistent transport exception",
        ),
    ],
    ids=["http_500", "transport_exception"],
)
@pytest.mark.parametrize("count", [1, LARGE])
def test_failed_recovery_is_bounded_per_switch_not_per_interface(
    responder, label, count
):
    """Unreadable switch: the failed work must not scale with the interface count."""
    want = _want(count)

    state, transport, clock = _run_get_have(want, responder)

    assert transport.total <= REQUEST_CEILING_PER_SWITCH, (
        "%s with %d requested interfaces spent %d interface-policy requests; the "
        "proposed contract allows at most %d per switch regardless of N (%s)"
        % (label, count, transport.total, REQUEST_CEILING_PER_SWITCH, _report(transport, clock))
    )
    assert clock.seconds <= SLEEP_CEILING_PER_SWITCH, (
        "%s with %d requested interfaces scheduled %g seconds of sleep; the "
        "proposed contract allows at most %d per switch (%s)"
        % (label, count, clock.seconds, SLEEP_CEILING_PER_SWITCH, _report(transport, clock))
    )
    # Exhausting the budget must change only the COST, never the conclusion.
    assert state.have == []
    assert len(_unavailable(state, want)) == count, (
        "a bound must not turn an unread interface into absence: %d of %d "
        "requested interfaces were still reported unavailable"
        % (len(_unavailable(state, want)), count)
    )
    assert transport.mutations == []


@pytest.mark.parametrize("count", [1, LARGE])
def test_malformed_http_200_is_bounded_and_never_becomes_absence(count):
    """A trusted-looking 200 that cannot be parsed must not be polled per interface."""
    want = _want(count)

    state, transport, clock = _run_get_have(want, _constant(MALFORMED_200))

    assert transport.total <= REQUEST_CEILING_PER_SWITCH_NO_RETRY, (
        "malformed HTTP 200 with %d requested interfaces spent %d interface-policy "
        "requests at full speed; the proposed contract allows at most %d per switch "
        "(%s)"
        % (count, transport.total, REQUEST_CEILING_PER_SWITCH_NO_RETRY, _report(transport, clock))
    )
    assert clock.calls == 0
    assert state.have == []
    assert state.intf_detail_authoritative_absent_keys == set()
    assert len(_unavailable(state, want)) == count


def test_the_budget_is_per_switch_so_it_scales_with_switches_not_interfaces():
    """Two unreadable switches cost two budgets, not two budgets times N."""
    want = _want(LARGE, serial="SN1") + _want(LARGE, serial="SN2", first=LARGE + 1)

    state, transport, clock = _run_get_have(want, _constant(ERROR_500))

    ceiling = 2 * REQUEST_CEILING_PER_SWITCH
    assert transport.total <= ceiling, (
        "two unreadable switches with %d interfaces each spent %d interface-policy "
        "requests; the proposed contract allows at most %d (%s)"
        % (LARGE, transport.total, ceiling, _report(transport, clock))
    )
    assert len(_unavailable(state, want)) == 2 * LARGE
    assert state.intf_detail_fetch_failed_snos == {"SN1", "SN2"}


# ===========================================================================
# Revision 2 additions. These are the cases the withdrawn r1 reset rule would
# have let through: each one crosses an invalidation, a new pass, or both.
# ===========================================================================
def test_budget_survives_invalidation_and_a_repeated_pass_over_one_serial():
    """One serial, one interface, two passes: still one budget.

    This is the real caller order of `overridden` at method level: prefetch,
    per-interface read, then the second prefetch and read of
    `dcnm_intf_get_diff_overridden`. `dcnm_intf_bulk_fetch_intf_info` invalidates
    the serial before every read (line 5346), so if invalidation reset the budget
    the second pass would start from zero and the bound would be meaningless.
    """
    state = _state([])
    transport = _Transport(_constant(ERROR_500))
    clock = _Clock()

    with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
        dcnm_interface, "time", clock
    ):
        DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
        DcnmIntf.dcnm_intf_get_intf_info(state, "Ethernet1/1", "SN1", "INTERFACE_ETHERNET")
        DcnmIntf.dcnm_intf_invalidate_serial_authority(state, "SN1")
        DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=False)
        DcnmIntf.dcnm_intf_get_intf_info(state, "Ethernet1/1", "SN1", "INTERFACE_ETHERNET")

    assert transport.total <= REQUEST_CEILING_PER_SWITCH, (
        "an invalidation and a repeated pass over one serial spent %d "
        "interface-policy requests for a single interface; the proposed contract "
        "allows at most %d per serial for the whole run, because neither "
        "invalidation nor a new pass is a reset (bulk=%d individual=%d sleep_s=%g)"
        % (
            transport.total,
            REQUEST_CEILING_PER_SWITCH,
            transport.counts["bulk"],
            transport.counts["individual"],
            clock.seconds,
        )
    )
    assert clock.seconds <= SLEEP_CEILING_PER_SWITCH
    assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Ethernet1/1", "SN1") is True


@pytest.mark.parametrize("count", [1, 10])
def test_overridden_on_a_populated_switch_stays_within_one_budget(count):
    """The bound holds through the REAL `main()`, across both overridden passes.

    `dcnm_intf_get_have` prefetches the serial, then
    `dcnm_intf_get_diff_overridden` prefetches it again and probes every
    `have_all` entry. A per-pass budget would permit twice the ceiling; the
    contract's budget is per serial per run.
    """
    run = run_module_path(
        count, _persistent_500, state="overridden", already_present=count
    )

    assert run.policy_total <= REQUEST_CEILING_PER_SWITCH, (
        "overridden over a switch already carrying %d interfaces spent %d "
        "interface-policy requests across its two passes; the proposed contract "
        "allows at most %d per serial for the whole run (%s)"
        % (count, run.policy_total, REQUEST_CEILING_PER_SWITCH, run.report())
    )
    assert run.clock.seconds <= SLEEP_CEILING_PER_SWITCH, (
        "overridden scheduled %g seconds of sleep; the proposed contract allows "
        "at most %d per serial (%s)"
        % (run.clock.seconds, SLEEP_CEILING_PER_SWITCH, run.report())
    )
    # Cheaper, never more permissive: the refusal and the zero writes stand.
    assert run.outcome == "fail_json"
    assert "could not be read authoritatively" in run.message
    assert run.counts["mutating"] == 0
    assert run.mutations == []


def test_post_deletion_recovery_does_not_reopen_an_exhausted_budget():
    """An exhausted serial stays exhausted through the deferred-member loop.

    `dcnm_intf_refresh_deferred_deleted_member_defaults` invalidates and re-reads
    inside a ten-iteration loop. Measured on the baseline, that loop already
    aborts inside its first iteration when detail is unavailable
    (`test_deferred_recovery_loop_aborts_inside_its_first_iteration_on_failure`),
    so it does not need a fresh budget to behave correctly -- it needs only to
    stop paying for reads of a switch already proven unreadable.

    The decision must not change: the loop still refuses, still schedules no
    replacement and still writes nothing.
    """
    state = _deferred_stub()
    transport = _Transport(_constant(ERROR_500))
    clock = _Clock()

    with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
        dcnm_interface, "time", clock
    ):
        # Spend the whole budget on this serial first, exactly as an earlier
        # phase of a `deleted` run would.
        DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
        DcnmIntf.dcnm_intf_get_intf_info(state, "Ethernet1/1", "SN1", "INTERFACE_ETHERNET")
        spent_before = transport.total

        with pytest.raises(RuntimeError, match="fail_json"):
            DcnmIntf.dcnm_intf_refresh_deferred_deleted_member_defaults(state)

    spent_by_loop = transport.total - spent_before
    assert spent_by_loop == 0, (
        "the post-deletion recovery loop spent %d further interface-policy "
        "requests on a serial whose budget was already exhausted (%d spent "
        "before); under the proposed contract it must issue none and reach the "
        "same refusal (bulk=%d individual=%d sleep_s=%g)"
        % (
            spent_by_loop,
            spent_before,
            transport.counts["bulk"],
            transport.counts["individual"],
            clock.seconds,
        )
    )
    assert transport.total <= REQUEST_CEILING_PER_SWITCH
    # The conclusion is unchanged: refuse, schedule nothing, write nothing.
    assert state.diff_replace == []
    assert state.diff_deploy == []
    assert state.changed_dict[0]["replaced"] == []
    assert state.changed_dict[0]["deploy"] == []
    assert transport.mutations == []
