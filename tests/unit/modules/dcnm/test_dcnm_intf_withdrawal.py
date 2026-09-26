"""Acceptance for the bounded withdrawal core: omission under replaced / retained overridden.

THE CONTRACT UNDER TEST

`merged` preserves an omitted value. `replaced`, and an interface RETAINED under
`overridden`, treat omission of a module-owned registered binding as a WITHDRAWAL
request:

  * a binding with a MEASURED `reset_wire` is reconciled -- the reset is transmitted and
    REPORTED in the public diff;
  * a binding that must be withdrawn but has no established reset (C7), or whose current
    value cannot be classified at all (C8), refuses the WHOLE invocation before any
    configuration or deployment call;
  * a binding the controller cannot carry, or that is absent from authoritative HAVE, is
    out of scope -- no reset is invented and no run is failed over it.

Five rows carry a verified reset today. That is a bounded pilot, not general withdrawal
support for the registry.

WHY THE ASSERTIONS LOOK LIKE THIS

Every integration case drives the real `main()` and asserts on the CAPTURED REQUEST and
the PUBLIC DIFF, never on `changed` alone. The module was measured transmitting an
nvPair it did not report -- `changed_dict` is deep-copied from WANT before the generic
carry-forward runs -- so a suite that trusts `changed` cannot see that class of defect.

Helper-level tests are labelled `test_helper_*`. A direct helper assertion is not
integration coverage and is not counted as such.

NOT LIVE TESTED IN THIS GENERATION. No controller, Nexus or Jenkins is contacted.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json

from unittest.mock import patch

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine as engine
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from .gie_withdrawal_harness import (
    ACCESS,
    BELOW,
    IF_A,
    IF_B,
    NON_ETH_PARENTS,
    PC_PARENTS,
    PILOT_ALL_IDS,
    PILOT_ALL_ITEMS,
    PILOT_IDS,
    PILOT_ITEMS,
    ROUTED,
    SUPPORTED,
    an_unclassifiable_key,
    is_integer_binding,
    wire_of,
    TRUNK,
    base_for,
    build_have,
    cfg,
    cfg_for,
    diff_nvpairs,
    have_for,
    request_nvpairs,
    run,
    run_configs,
    split_calls,
)


def _pkw(parent):
    """`run` takes `parent` for every NON-ethernet parent; ethernet callers stay unchanged.

    This read `parent in PC_PARENTS` while the matrix held only ethernet and port-channel
    rows. Adding the subinterface parent would then have driven a `type: eth` config on
    `Ethernet1/31`, resolved a different policy, and measured the withdrawal against a HAVE
    the module never produces for int_subif -- green, and about the wrong object.
    """
    return {"parent": parent} if parent in NON_ETH_PARENTS else {}


# ===================================================================== coverage guard
def test_the_fixture_matrix_covers_every_registered_reset():
    """Guard the guard. The positive matrix used to carry FIVE identities while the
    registry had grown to seventeen, so twelve promoted rows had no real-main coverage and
    the suite was green anyway. This fails if a row is dropped, if one is registered
    without a fixture, or if the parameter set ever collects empty.

    The parent filter was REMOVED in G25. It used to read `in (ACCESS, TRUNK)`, which meant
    the guard could only ever police the two parents it already knew: registering the
    port-channel family would have left 19 rows untested with the suite still green --
    exactly the failure this test exists to prevent, reappearing one parent family later.
    It now compares against EVERY registered row in the table.
    """
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
        BINDING_TABLE,
    )
    registered = {(b["parent_template"], b["parent_nvpair"]) for b in BINDING_TABLE
                  if b.get("reset_wire") is not None}
    fixtures = {(p, n) for p, n, _k, _a, _r, _e in PILOT_ALL_ITEMS}
    assert fixtures, "the fixture matrix collected nothing; every test below is a no-op"
    assert fixtures == registered, (
        "fixture matrix and registry disagree.\n  registered but untested: %s\n"
        "  tested but unregistered: %s"
        % (sorted(registered - fixtures), sorted(fixtures - registered)))


def test_the_vpc_peer_link_row_is_not_registered():
    """int_port_channel_trunk_host::ENABLE_VPC_PEER_LINK is a ROLE CHANGE, not an ordinary
    field: setting it true turns the port-channel into a vPC peer-link. It was never run,
    has no measured reset, and is deliberately absent from the fixture matrix. If it were
    ever registered, the guard above would fail with a confusing "untested" message; this
    names the real reason so the next reader is not left guessing."""
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
        BINDING_TABLE,
    )
    peer = [b for b in BINDING_TABLE
            if b["parent_template"] == "int_port_channel_trunk_host"
            and b["parent_nvpair"] == "ENABLE_VPC_PEER_LINK"]
    assert peer, "the binding disappeared from the table entirely; that is a separate bug"
    assert peer[0].get("reset_wire") is None, (
        "ENABLE_VPC_PEER_LINK carries a reset_wire. Withdrawing it would silently dissolve "
        "a vPC peer-link. It needs its own scope and live proof, not registration here.")


@pytest.mark.parametrize("parent,nvpair,key,applied,reset,extra",
                         PILOT_ALL_ITEMS, ids=PILOT_ALL_IDS)
def test_every_fixture_reset_matches_the_registered_reset_wire(
    parent, nvpair, key, applied, reset, extra
):
    """A fixture that disagrees with the registry would test a value the module never
    emits, and pass by accident."""
    b = engine.resolve_binding(parent, key)
    assert b is not None and b["parent_nvpair"] == nvpair
    assert b.get("reset_wire") == reset


# ===================================================================== the pilot rows
@pytest.mark.parametrize("parent,nvpair,key,applied,reset,extra",
                         PILOT_ALL_ITEMS, ids=PILOT_ALL_IDS)
def test_omission_alone_under_replaced_emits_the_verified_reset(
    parent, nvpair, key, applied, reset, extra
):
    """Omission with NOTHING else changed must produce the reset in the outbound request."""
    have = build_have(parent, key, applied, **extra)
    result, calls = run(base_for(parent, **extra), "replaced", have, **_pkw(parent))
    nv = request_nvpairs(calls)
    assert nv, ("no request was sent at all: the omission was not detected. changed=%s"
                % result.get("changed"))
    assert nv[0].get(nvpair) == reset, (
        "%s on %s: request carries %r, expected the verified reset %r"
        % (nvpair, parent, nv[0].get(nvpair), reset))


@pytest.mark.parametrize("parent,nvpair,key,applied,reset,extra",
                         PILOT_ALL_ITEMS, ids=PILOT_ALL_IDS)
def test_the_reset_is_reported_in_the_public_diff(parent, nvpair, key, applied, reset, extra):
    """The guard against transmitting what is never reported."""
    have = build_have(parent, key, applied, **extra)
    result, calls = run(base_for(parent, **extra), "replaced", have, **_pkw(parent))
    assert request_nvpairs(calls), "no request was sent; the request half fails first"
    reported = [nv for nv in diff_nvpairs(result) if nvpair in nv]
    assert reported, (
        "%s on %s was reset in the request but is ABSENT from the public diff: the module "
        "would be changing what it does not report" % (nvpair, parent))
    assert reported[0][nvpair] == reset


@pytest.mark.parametrize("parent,nvpair,key,applied,reset,extra",
                         PILOT_ALL_ITEMS, ids=PILOT_ALL_IDS)
def test_retained_interface_under_overridden_follows_the_same_contract(
    parent, nvpair, key, applied, reset, extra
):
    """A RETAINED interface under overridden reconciles exactly as under replaced.

    The excluded-interface half is a MEMBERSHIP decision, not a field withdrawal, and
    keeps its existing coverage in `test_dcnm_intf_override_authority_scope.py`.
    """
    have = build_have(parent, key, applied, **extra)
    result, calls = run_configs([cfg_for(parent, base_for(parent, **extra), deploy=False)],
                                "overridden", have)
    nv = request_nvpairs(calls)
    assert nv, ("retained interface under overridden sent no request (changed=%s)"
                % result.get("changed"))
    assert nv[0].get(nvpair) == reset
    reported = [d for d in diff_nvpairs(result) if nvpair in d]
    assert reported and reported[0][nvpair] == reset, "overridden did not report the reset"


# ============================================================ derived convergence sequence
@pytest.mark.parametrize("parent,nvpair,key,applied,reset,extra",
                         PILOT_ALL_ITEMS, ids=PILOT_ALL_IDS)
def test_apply_then_omit_then_identical_rerun_converges(
    parent, nvpair, key, applied, reset, extra
):
    """apply -> omission -> emitted reset -> the SAME omitted input again.

    The second run's controller state is DERIVED FROM THE ACTUAL EMITTED RESET, not
    hand-written. Deploy is enabled throughout, so the first run is a positive control
    that really writes and deploys -- without it, "zero deploys" on the rerun would be
    unfalsifiable.
    """
    have = build_have(parent, key, applied, **extra)

    first, calls1 = run(base_for(parent, **extra), "replaced", have, **_pkw(parent))
    split1 = split_calls(calls1)
    assert len(split1["updates"]) == 1, "positive control: expected exactly one update"
    assert len(split1["deploys"]) == 1, (
        "deploy was enabled and a value changed, so exactly one deploy is expected; got %d"
        % len(split1["deploys"]))
    emitted = request_nvpairs(calls1)[0][nvpair]
    assert emitted == reset

    have2 = copy.deepcopy(have)
    have2[0]["interfaces"][0]["nvPairs"][nvpair] = emitted
    second, calls2 = run(base_for(parent, **extra), "replaced", have2, **_pkw(parent))
    split2 = split_calls(calls2)
    assert len(split2["updates"]) == 0 and len(split2["deploys"]) == 0, (
        "the same omitted input against the state the module itself produced sent "
        "%d update(s) and %d deploy(s); it must converge"
        % (len(split2["updates"]), len(split2["deploys"])))
    assert second.get("changed") is False


def test_identical_explicit_reapply_with_deploy_enabled_is_also_a_no_op():
    """The separate control. Reapplying an explicit value is NOT a substitute for the
    derived sequence above, but it must hold on the same deploy-enabled path."""
    have = have_for([IF_A], ACCESS, "acl_filter", "ACL-PILOT")
    result, calls = run_configs(
        [cfg(IF_A, base_for(ACCESS, acl_filter="ACL-PILOT"))], "replaced", have,
        allow_failed=False)
    split = split_calls(calls)
    assert len(split["updates"]) == 0 and len(split["deploys"]) == 0


def test_a_real_change_still_writes_and_deploys():
    """The positive control for every zero-deploy assertion in this file."""
    have = have_for([IF_A], ACCESS, "acl_filter", "ACL-PILOT")
    result, calls = run_configs(
        [cfg(IF_A, base_for(ACCESS, acl_filter="ACL-CHANGED"))], "replaced", have,
        allow_failed=False)
    split = split_calls(calls)
    assert len(split["updates"]) == 1 and len(split["deploys"]) == 1
    assert request_nvpairs(calls)[0]["aclFilter"] == "ACL-CHANGED"


# ===================================================================== merged preserves
@pytest.mark.parametrize("parent,nvpair,key,applied,reset,extra", PILOT_ITEMS, ids=PILOT_IDS)
def test_merged_omission_is_a_no_op(parent, nvpair, key, applied, reset, extra):
    have = build_have(parent, key, applied, **extra)
    result, calls = run(base_for(parent, **extra), "merged", have, **_pkw(parent))
    assert len(split_calls(calls)["updates"]) == 0
    assert result.get("changed") is False


@pytest.mark.parametrize("parent,nvpair,key,applied,reset,extra", PILOT_ITEMS, ids=PILOT_IDS)
def test_merged_unrelated_update_preserves_the_omitted_value(
    parent, nvpair, key, applied, reset, extra
):
    """An unrelated edit under merged must re-send the controller's value, not reset it."""
    have = build_have(parent, key, applied, **extra)
    result, calls = run(base_for(parent, description="changed-under-merged", **extra), "merged", have, **_pkw(parent))
    nv = request_nvpairs(calls)
    assert nv, "the description change produced no request"
    assert nv[0].get(nvpair) == wire_of(applied)


def test_merged_is_never_blocked_by_an_unsupported_row():
    """merged has no withdrawal contract, so C7/C8 must not fire for it at all.
    Rehomed to the routed parent with the rest of the C7 family."""
    have = build_have(ROUTED)
    have[0]["interfaces"][0]["nvPairs"]["lldpReceive"] = "true"
    result, calls = run_configs(
        [cfg(IF_A, base_for(ROUTED, description="x"))], "merged", have)
    assert not result.get("failed"), result.get("msg")


# ===================================================================== explicit precedence
@pytest.mark.parametrize("parent,nvpair,key,applied,reset,extra", PILOT_ITEMS, ids=PILOT_IDS)
def test_an_explicit_clear_retains_precedence_and_is_still_validated(
    parent, nvpair, key, applied, reset, extra
):
    """Explicit input is never this step's business. It must still win, including the
    two spellings a clear takes: native `False` and the empty string."""
    have = build_have(parent, key, applied, **extra)
    # The supported explicit clear IS the registered reset value, spelled the way the
    # public input takes it: a native bool for a boolean binding, the wire string
    # otherwise. The earlier rule mapped anything that was not "false"/"off" to "", which
    # silently turned GUARD_MODE and SPANNING_TREE_PORT_TYPE into an empty enum -- a
    # no-op the module correctly refused to send, so the case proved nothing for them.
    # AN INTEGER BINDING HAS NO SUPPORTED PUBLIC EXPLICIT CLEAR, and that is a guarantee, not
    # a gap to route around. Native-integer validation refuses the empty string before any
    # request is built; that refusal is what made a raw measured probe necessary for the
    # integer reset, and a test that quietly skipped it would let the refusal regress unseen.
    if is_integer_binding(applied):
        result, calls = run(base_for(parent, **dict(extra, **{key: reset})), "replaced", have,
                            **_pkw(parent))
        assert result.get("failed"), (
            "%s is an integer binding: the public empty string must be REFUSED, not accepted"
            % nvpair)
        assert [c for c in calls if c["method"] != "GET"] == [], (
            "the refused integer clear still sent a write")
        return
    clear_input = False if reset == "false" else reset
    result, calls = run(base_for(parent, **dict(extra, **{key: clear_input})), "replaced", have, **_pkw(parent))
    nv = request_nvpairs(calls)
    assert nv, "the explicit clear produced no request"
    assert nv[0].get(nvpair) == reset


@pytest.mark.parametrize("parent,nvpair,key,applied,reset,extra", PILOT_ITEMS, ids=PILOT_IDS)
def test_an_explicit_non_default_value_is_not_withdrawn(
    parent, nvpair, key, applied, reset, extra
):
    """The other half: a field the operator DID write keeps its value, unchanged."""
    have = build_have(parent, key, applied, **extra)
    result, calls = run(base_for(parent, **dict(extra, **{key: applied})), "replaced", have, **_pkw(parent))
    for req in request_nvpairs(calls):
        assert req.get(nvpair) != reset or reset == "", (
            "an explicitly supplied value was reset")


# ===================================================================== check mode
@pytest.mark.parametrize("parent,nvpair,key,applied,reset,extra", PILOT_ITEMS, ids=PILOT_IDS)
def test_check_mode_reports_the_reset_without_writing(parent, nvpair, key, applied, reset, extra):
    have = build_have(parent, key, applied, **extra)
    result, calls = run(base_for(parent, **extra), "replaced", have, check_mode=True, **_pkw(parent))
    assert len(split_calls(calls)["updates"]) == 0, "check mode sent a configuration request"
    reported = [nv for nv in diff_nvpairs(result) if nvpair in nv]
    assert reported and reported[0][nvpair] == reset, (
        "check mode did not report the reset it would apply")


# ===================================================================== C7 / C8 refusal
def test_c7_configured_value_without_an_established_reset_refuses_the_run():
    """A registered row that differs from its declared default with no verified reset:
    withdrawal IS required and cannot be completed, so the run must refuse.

    REHOMED to int_routed_host. This case used int_access_host::DISABLE_LLDP_RECEIVE, whose
    reset was measured on hardware in the access/trunk batch. Leaving the case there would
    have quietly deleted the unsupported-capability guarantee along with the C7 branch it
    is the only integration cover for. The routed row is genuinely unsupported today:
    a declared default of false, and no established reset.
    """
    have = build_have(ROUTED)
    have[0]["interfaces"][0]["nvPairs"]["lldpReceive"] = "true"
    result, calls = run_configs([cfg(IF_A, base_for(ROUTED))], "replaced", have)
    split = split_calls(calls)
    assert result.get("failed"), "a required withdrawal that cannot complete reported success"
    assert len(split["updates"]) == 0 and len(split["deploys"]) == 0
    msg = str(result.get("msg", ""))
    assert "disable_lldp_receive" in msg and ROUTED in msg
    assert "must withdraw" in msg


def test_c7_the_same_row_at_its_declared_default_still_succeeds():
    """The control proving the refusal above is not a blanket rejection. Rehomed with it."""
    have = build_have(ROUTED)
    have[0]["interfaces"][0]["nvPairs"]["lldpReceive"] = "false"
    result, calls = run_configs([cfg(IF_A, base_for(ROUTED))], "replaced", have)
    assert not result.get("failed"), result.get("msg")


def test_c8_unclassifiable_value_refuses_with_its_own_distinct_reason():
    """A registered row with no declared default and no verified reset. Nothing says whether
    the present value is untouched or deliberate, and unknown is not converged.

    The row is DERIVED: this named `ospf_cost` until G37 measured its reset.
    """
    key = an_unclassifiable_key(ROUTED)
    have = build_have(ROUTED, key, 100)
    result, calls = run(base_for(ROUTED), "replaced", have)
    split = split_calls(calls)
    assert result.get("failed"), "an unclassifiable configured value must not pass"
    msg = str(result.get("msg", ""))
    assert key in msg and ROUTED in msg
    assert "cannot be classified" in msg, msg
    assert "100" not in msg, "the refusal named the value"
    assert len(split["updates"]) == 0 and len(split["deploys"]) == 0


def test_check_mode_also_refuses_an_unsupported_withdrawal():
    """Check mode is a report. Reporting a replacement that cannot complete is the same
    false claim as performing one."""
    have = build_have(ROUTED)
    have[0]["interfaces"][0]["nvPairs"]["lldpReceive"] = "true"
    result, calls = run_configs([cfg(IF_A, base_for(ROUTED))], "replaced", have,
                                check_mode=True)
    assert result.get("failed")
    assert len(split_calls(calls)["updates"]) == 0


def test_valid_first_interface_unsupported_second_writes_nothing_at_all():
    """The refusal is invocation-wide. This is PREFLIGHT, not transactional rollback: the
    module offers no rollback and none is promised. Reads are counted separately."""
    # Two routed interfaces built from the module's own payload. `have_for` needs a real
    # field to apply, so the HAVE is built per interface and re-keyed here.
    have = []
    for name in (IF_A, IF_B):
        h = build_have(ROUTED)
        h[0]["interfaces"][0]["ifName"] = name
        have.extend(h)
    have[1]["interfaces"][0]["nvPairs"]["lldpReceive"] = "true"
    result, calls = run_configs(
        [cfg(IF_A, base_for(ROUTED)), cfg(IF_B, base_for(ROUTED))], "replaced", have)
    split = split_calls(calls)
    assert result.get("failed"), "the unsupported second interface did not stop the run"
    assert len(split["updates"]) == 0, (
        "the valid first interface was written before the second was rejected: %d update(s)"
        % len(split["updates"]))
    assert len(split["deploys"]) == 0
    assert len(split["reads"]) > 0, "reads are expected and are counted separately"


# ===================================================================== version boundary
@pytest.mark.parametrize("version,applicable", [
    (BELOW, False),
    (SUPPORTED, True),
    ("12.7.0.100", True),
    ("not-a-version", False),
    (None, False),
], ids=["below", "equal", "above", "malformed", "unknown"])
def test_the_version_boundary_governs_the_omission_reset(version, applicable):
    """ACL_FILTER requires 12.6.0.267. A controller that cannot carry it gets NOTHING --
    and the run must not fail over it either.

    `fec` is dropped because it carries its own pre-existing NDFC >= 12.4.1 check that
    fails on a malformed or unknown version for reasons unrelated to withdrawal.
    """
    prof = base_for(ACCESS)
    prof.pop("fec", None)
    have = have_for([IF_A], ACCESS, "acl_filter", "ACL-PILOT")
    result, calls = run_configs([cfg(IF_A, prof)], "replaced", have, ndfc_version=version)
    sent = [nv["aclFilter"] for nv in request_nvpairs(calls) if "aclFilter" in nv]
    if applicable:
        assert len(split_calls(calls)["updates"]) == 1
        assert sent == [""], sent
    else:
        assert not result.get("failed"), (
            "an inapplicable omitted row failed the run: %s" % result.get("msg"))
        # Asserted on the VALUE, not the update count: dropping `fec` is itself a
        # legitimate difference against HAVE, so an update here may be none of
        # withdrawal's business. What must never leave the module is the reset.
        assert "" not in sent, (
            "the reset was transmitted on a controller that refuses the explicit clear")


def test_explicit_and_omitted_agree_on_an_unsupported_version():
    """The pair that exposed the bypass: the explicit route said no while omission sent the
    clear anyway. Both must now refuse to transport it."""
    have = have_for([IF_A], ACCESS, "acl_filter", "ACL-PILOT")
    explicit, ex_calls = run_configs(
        [cfg(IF_A, base_for(ACCESS, acl_filter=""))], "replaced", have, ndfc_version=BELOW)
    omitted, om_calls = run_configs(
        [cfg(IF_A, base_for(ACCESS))], "replaced", have, ndfc_version=BELOW)
    assert explicit.get("failed"), "explicit clear was accepted below min_ndfc_version"
    assert SUPPORTED in str(explicit.get("msg", ""))
    assert len(split_calls(ex_calls)["updates"]) == 0
    assert not omitted.get("failed")
    assert len(split_calls(om_calls)["updates"]) == 0, (
        "omission transported what the explicit route is refused")


# ===================================================================== HAVE shapes
@pytest.mark.parametrize("have_value", ["false", False], ids=["wire_string", "native_bool"])
def test_equivalent_have_encodings_classify_identically(have_value):
    """Both spellings are accepted by the HAVE validator and describe ONE controller state.
    Comparing raw HAVE against a wire string made `"false"` the baseline and native
    `False` a C7 abort."""
    have = have_for([IF_A], ACCESS, "acl_filter", "ACL-PILOT")
    have[0]["interfaces"][0]["nvPairs"]["lldpReceive"] = have_value
    result, calls = run_configs([cfg(IF_A, base_for(ACCESS))], "replaced", have)
    assert not result.get("failed"), (
        "HAVE %r was rejected while its equivalent encoding is accepted: %s"
        % (have_value, result.get("msg")))


@pytest.mark.parametrize("parent,nvpair,key,applied,reset,extra", PILOT_ITEMS, ids=PILOT_IDS)
def test_have_already_at_the_reset_invents_no_write(parent, nvpair, key, applied, reset, extra):
    have = build_have(parent, key, applied, **extra)
    have[0]["interfaces"][0]["nvPairs"][nvpair] = reset
    result, calls = run(base_for(parent, **extra), "replaced", have, **_pkw(parent))
    assert len(split_calls(calls)["updates"]) == 0


@pytest.mark.parametrize("parent,nvpair,key,applied,reset,extra", PILOT_ITEMS, ids=PILOT_IDS)
def test_authoritative_absence_is_nothing_to_withdraw(parent, nvpair, key, applied, reset, extra):
    """An absent key is absent. No default may be invented for it."""
    have = build_have(parent, key, applied, **extra)
    have[0]["interfaces"][0]["nvPairs"].pop(nvpair, None)
    result, calls = run(base_for(parent, **extra), "replaced", have, **_pkw(parent))
    assert len(split_calls(calls)["updates"]) == 0, (
        "an absent HAVE key produced a write: a reset was invented for a field the "
        "controller does not hold")


def test_an_empty_wire_value_is_absence_not_a_configured_value():
    """NDFC returns `""` for a field its template never defaulted. That is absence, and it
    must not be classified as an unclassifiable configured value."""
    have = build_have(ROUTED)
    have[0]["interfaces"][0]["nvPairs"]["ospfCost"] = ""
    result, calls = run(base_for(ROUTED), "replaced", have)
    assert not result.get("failed"), (
        "an empty controller value was treated as a configured one: %s" % result.get("msg"))


@pytest.mark.parametrize("malformed", [1234, {"a": 1}], ids=["native_int", "mapping"])
def test_malformed_have_fails_closed_rather_than_receiving_a_reset(malformed):
    """A value the HAVE validator cannot read must stop the run, not be answered with a
    confident reset."""
    have = have_for([IF_A], ACCESS, "acl_filter", "ACL-PILOT")
    have[0]["interfaces"][0]["nvPairs"]["aclFilter"] = malformed
    result, calls = run_configs([cfg(IF_A, base_for(ACCESS))], "replaced", have)
    assert result.get("failed"), "malformed HAVE was accepted"
    assert "acl_filter" in str(result.get("msg", ""))
    assert len(split_calls(calls)["updates"]) == 0


def test_a_value_held_only_by_another_interface_is_not_this_ones_have():
    """Non-authoritative HAVE. Two interfaces on one parent: the field is configured on
    IF_B only, and a run that touches IF_A alone must not withdraw IF_B's value nor treat
    it as IF_A's own."""
    have = have_for([IF_A, IF_B], ACCESS, "acl_filter", "ACL-PILOT")
    have[0]["interfaces"][0]["nvPairs"].pop("aclFilter", None)   # absent on IF_A
    result, calls = run_configs([cfg(IF_A, base_for(ACCESS))], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    for req in request_nvpairs(calls):
        assert req.get("aclFilter") != "", (
            "IF_A was reset using a value that belongs to IF_B's authoritative state")


def test_greenfield_creation_carries_no_reset():
    """No HAVE at all. Creation must transmit what was asked for and nothing else."""
    result, calls = run(base_for(ACCESS, acl_filter="ACL-PILOT"), "replaced")
    nv = request_nvpairs(calls)
    assert nv and nv[0].get("aclFilter") == "ACL-PILOT"


def test_a_sparse_have_without_any_registry_nvpair_is_not_a_withdrawal_trigger():
    """A HAVE that carries none of this parent's registered bindings must produce no reset.

    Only the REGISTRY nvPairs are stripped. Structural keys stay, `CONF` in particular:
    the legacy comparator splits the `key_translate` keys with `.strip()` and raises
    `AttributeError: 'NoneType' object has no attribute 'strip'` when one is missing. That
    crash reproduces IDENTICALLY on the base `7e386863` (line 6058 there, 6066 here -- the
    same code, shifted by this work's insertion), so it is pre-existing and out of scope.
    Its reproduction is preserved in `evidence/W2/G17-portable/` rather than repaired here.
    """
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
        BINDING_TABLE,
    )
    registry_nvpairs = {b["parent_nvpair"] for b in BINDING_TABLE
                        if b["parent_template"] == ACCESS}
    have = have_for([IF_A], ACCESS, "acl_filter", "ACL-PILOT")
    nv = have[0]["interfaces"][0]["nvPairs"]
    have[0]["interfaces"][0]["nvPairs"] = {
        k: v for k, v in nv.items() if k not in registry_nvpairs}
    assert not (set(have[0]["interfaces"][0]["nvPairs"]) & registry_nvpairs), (
        "the fixture still carries a registry nvPair; this case would not be sparse")
    result, calls = run_configs([cfg(IF_A, base_for(ACCESS))], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    for req in request_nvpairs(calls):
        assert req.get("aclFilter") != "", "a reset was invented from a sparse HAVE"


# ===================================================================== ownership
def test_ownership_a_user_parent_binding_sharing_a_fabric_owned_name_is_reconciled():
    """OSPF_AUTH_KEY_ID on int_routed_host shares its NAME with a fabric-owned nvPair. A
    name-only exclusion would drop it; the parent-qualified rule must still consider it.

    It has no verified reset, so the observable proof that it WAS considered is that the
    invocation is refused rather than silently succeeding.
    """
    have = build_have(ROUTED, enable_ospf_auth=True, ospf_auth_key_id=7,
                      ospf_auth_key="SyntheticSetupKey0001")
    result, calls = run(base_for(ROUTED, enable_ospf_auth=True,
                                 ospf_auth_key="SyntheticSetupKey0001"), "replaced", have)
    assert result.get("failed"), (
        "a user-parent binding whose name matches a fabric-owned field was skipped; the "
        "exclusion is not parent-qualified")
    assert "ospf_auth_key_id" in str(result.get("msg", ""))
    assert len(split_calls(calls)["updates"]) == 0


def test_helper_ownership_exclusion_is_keyed_on_parent_and_nvpair():
    """The boundary, at helper level: excluded on the OWNING parent, considered elsewhere."""
    assert engine.gie_binding_is_owned_elsewhere(
        "int_fabric_loopback_11_1", "OSPF_AUTH_KEY") is True
    assert engine.gie_binding_is_owned_elsewhere(ROUTED, "OSPF_AUTH_KEY") is False
    assert engine.gie_binding_is_owned_elsewhere("int_subif", "OSPF_AUTH_KEY_ID") is False


def test_helper_a_name_only_exclusion_would_drop_eight_legitimate_rows():
    """Why the rule is parent-qualified. Data, not a code path: a name-only rule is wrong
    on this registry regardless of how it is implemented."""
    from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table as table
    names = set(engine.GIE_FABRIC_OWNED_LOOPBACK_NVPAIRS)
    on_owner = [r for r in table.BINDING_TABLE
                if r["parent_nvpair"] in names
                and r["parent_template"] == "int_fabric_loopback_11_1"]
    collateral = [r for r in table.BINDING_TABLE
                  if r["parent_nvpair"] in names
                  and r["parent_template"] != "int_fabric_loopback_11_1"]
    assert not on_owner, "the owning parent now carries rows with those names; recheck"
    assert len(collateral) == 8, sorted(
        (r["parent_template"], r["parent_nvpair"]) for r in collateral)
    assert {r["parent_template"] for r in collateral} == {
        "int_loopback", ROUTED, "int_subif", "int_vlan"}
    assert any(r.get("no_log") for r in collateral)


def test_helper_fabric_owned_carry_forward_remains_a_separate_mechanism():
    """The narrow fabric-owned allowlist keeps its own raw-HAVE contract, untouched."""
    have_nv = {n: "fabric-value" for n in engine.GIE_FABRIC_OWNED_LOOPBACK_NVPAIRS}
    assert set(engine.gie_fabric_owned_carry_forward({}, have_nv)) == \
        set(engine.GIE_FABRIC_OWNED_LOOPBACK_NVPAIRS)
    assert engine.gie_fabric_owned_carry_forward(
        {n: "explicit" for n in engine.GIE_FABRIC_OWNED_LOOPBACK_NVPAIRS}, have_nv) == {}, \
        "a key already present in want must never be overwritten"


# ===================================================================== parent transition
def test_a_parent_transition_targets_the_new_policy_and_leaks_no_old_parent_reset():
    """trunk -> access. The run must SUCCEED, target the new policy, and carry no binding
    that belongs only to the old parent.

    Non-vacuity matters here: an earlier version ran with failures allowed and then
    iterated a request list that was empty when the module aborted, so it passed having
    observed nothing.
    """
    have = build_have(TRUNK, "guard_mode", "root")
    result, calls = run(base_for(ACCESS), "replaced", have)
    assert not result.get("failed"), (
        "the parent transition aborted, so this test observed nothing: %s"
        % result.get("msg"))
    payloads = [c["payload"] for c in calls if c["method"] != "GET"]
    policies = set()

    def walk(node):
        if isinstance(node, dict):
            if "policy" in node and "interfaces" in node:
                policies.add(node["policy"])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(payloads)
    assert policies == {ACCESS}, (
        "expected the request to target the new parent only; got %s" % sorted(policies))
    for req in request_nvpairs(calls):
        assert "GUARD_MODE" not in req, (
            "a trunk-only binding leaked into an access-parent request")


# ===================================================================== query
def test_query_succeeds_and_returns_the_interface_state():
    """A successful query asserts success AND readback. Zero writes alone is not success:
    an aborted query also writes nothing."""
    have = have_for([IF_A], ACCESS, "acl_filter", "ACL-PILOT")
    result, calls = run_configs([cfg(IF_A, {"mode": "access"}, deploy=False)], "query", have)
    split = split_calls(calls)
    assert not result.get("failed"), "the query itself failed: %s" % result.get("msg")
    assert len(split["updates"]) == 0 and len(split["deploys"]) == 0
    blob = json.dumps(result)
    assert IF_A in blob, "query returned nothing identifying %s" % IF_A
    assert "ACL-PILOT" in blob, (
        "query did not return the configured value it was asked to report")


def test_deleted_state_does_not_enter_the_withdrawal_path():
    """`deleted` is a lifecycle decision with its own contract. No reset is invented for it
    here; its authoritative coverage stays in the module's own lifecycle suites."""
    have = have_for([IF_A], ACCESS, "acl_filter", "ACL-PILOT")
    have[0]["interfaces"][0]["nvPairs"]["lldpReceive"] = "true"   # a C7 row
    result, calls = run_configs([cfg(IF_A, base_for(ACCESS), deploy=False)], "deleted", have)
    assert not result.get("failed"), (
        "the withdrawal preflight fired on `deleted`: %s" % result.get("msg"))


# ===================================================================== negative control
def test_suppressing_the_parent_index_does_not_by_itself_produce_the_reset():
    """Diagnosis, preserved. The candidate reuses the accepted parent INDEX to enumerate a
    parent's bindings, so suppressing it removes the enumeration too. This documents that
    the index is not the mechanism; the mutation suite is what proves the detection."""
    have = have_for([IF_A], ACCESS, "acl_filter", "ACL-PILOT")
    result, calls = run_configs(
        [cfg(IF_A, base_for(ACCESS))], "replaced", have,
        extra_patch=patch.object(module, "gie_carry_forward_bindings", return_value=[]))
    sent = [nv.get("aclFilter") for nv in request_nvpairs(calls) if "aclFilter" in nv]
    assert "" not in sent, (
        "with the parent index suppressed a reset was still emitted; the detection would "
        "not be coming from the enumeration this design reuses")
