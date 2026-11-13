"""Withdrawal of registered fields: omission, retirement scope, grouped omission and role-default resets."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import importlib.util
import json
import os
import pytest

from unittest.mock import patch
from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine as engine
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding
from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table as table

from .helpers.binding_harness import ACCESS
from .helpers.binding_harness import GROUPED_ONLY_NO_PER_ROW_FIXTURE
from .helpers.binding_harness import BELOW
from .helpers.binding_harness import IF_A
from .helpers.binding_harness import IF_B
from .helpers.binding_harness import NON_ETH_PARENTS
from .helpers.binding_harness import PILOT_ALL_IDS
from .helpers.binding_harness import PILOT_ALL_ITEMS
from .helpers.binding_harness import PILOT_IDS
from .helpers.binding_harness import PILOT_ITEMS
from .helpers.binding_harness import ROUTED
from .helpers.binding_harness import SUPPORTED
from .helpers.binding_harness import an_unclassifiable_key
from .helpers.binding_harness import is_integer_binding
from .helpers.binding_harness import TRUNK
from .helpers.binding_harness import base_for
from .helpers.binding_harness import want_omitting
from .helpers.binding_harness import build_have
from .helpers.binding_harness import cfg
from .helpers.binding_harness import cfg_for
from .helpers.binding_harness import diff_nvpairs
from .helpers.binding_harness import have_for
from .helpers.binding_harness import public_clear_for
from .helpers.binding_harness import request_nvpairs
from .helpers.binding_harness import wire_for
from .helpers.binding_harness import run
from .helpers.binding_harness import run_configs
from .helpers.binding_harness import split_calls
from .helpers.binding_harness import FABRIC
from .helpers import binding_harness as h
from .helpers.role_reset import PHYSICAL
from .helpers.role_reset import STATES
from .helpers.role_reset import _inventory
from .helpers.role_reset import _physical_transport
from .helpers.role_reset import as_have
from .helpers.role_reset import nvpairs_of_reset
from .helpers.role_reset import reset_policies
from .helpers.role_reset import reset_wire
from .helpers.role_reset import run as role_reset_run


# ====================================================================================================
# Formerly test_dcnm_intf_withdrawal.py
# Acceptance for the bounded withdrawal core: omission under replaced / retained overridden.
#
# THE CONTRACT UNDER TEST
#
# `merged` preserves an omitted value. `replaced`, and an interface RETAINED under
# `overridden`, treat omission of a module-owned registered binding as a WITHDRAWAL
# request:
#
#   * a binding with a MEASURED `reset_wire` is reconciled -- the reset is transmitted and
#     REPORTED in the public diff;
#   * a binding that must be withdrawn but has no established reset (C7), or whose current
#     value cannot be classified at all (C8), refuses the WHOLE invocation before any
#     configuration or deployment call;
#   * a binding the controller cannot carry, or that is absent from authoritative HAVE, is
#     out of scope -- no reset is invented and no run is failed over it.
#
# Five rows carry a verified reset today. That is a bounded pilot, not general withdrawal
# support for the registry.
#
# WHY THE ASSERTIONS LOOK LIKE THIS
#
# Every integration case drives the real `main()` and asserts on the CAPTURED REQUEST and
# the PUBLIC DIFF, never on `changed` alone. The module was measured transmitting an
# nvPair it did not report -- `changed_dict` is deep-copied from WANT before the generic
# carry-forward runs -- so a suite that trusts `changed` cannot see that class of defect.
#
# Helper-level tests are labelled `test_helper_*`. A direct helper assertion is not
# integration coverage and is not counted as such.
#
# NOT LIVE TESTED. No controller or switch is contacted.
#
# The C7 unsupported fixture is now ``int_routed_host::eigrp_ipv4_passive``. PIM/BFD gained
# a measured reset, so it could no longer prove the refusal. The
# per-parent ``FIXTURE_CONTRACTS`` guard checks that the replacement is registered,
# declares a default, and still has no reset. The ACCESS positive cases remain separate.
# serves as a positive example, and ``disable_bfd_echo`` is not registered on that parent at all, so
# rewriting them would have resolved to no binding and passed vacuously.
# ====================================================================================================
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

    The parent filter was REMOVED. It used to read `in (ACCESS, TRUNK)`, which meant
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
    # Identities whose per-row omission cannot describe a reachable controller state are
    # DECLARED, never silently dropped. The two assertions below keep this honest: the set
    # must not be empty (or it is dead weight hiding nothing) and every member must actually
    # be registered (or it is parking a row that does not exist).
    assert GROUPED_ONLY_NO_PER_ROW_FIXTURE, "the grouped-only declaration is empty"
    undeclared = {k for k in GROUPED_ONLY_NO_PER_ROW_FIXTURE if k not in registered}
    assert not undeclared, (
        "grouped-only names an identity that is not registered: %s" % sorted(undeclared))
    registered = registered - set(GROUPED_ONLY_NO_PER_ROW_FIXTURE)
    # The PVLAN parents' registry companions never reach the generic comparator this matrix drives; their omission
    # contract is pinned per identity in test_pvlan_companions.py. Declared by identity, and they must be exactly
    # the PVLAN parents' registered resets (a new PVLAN row without that coverage still fails here).
    from .helpers.ethernet_controller import PVLAN_ROUTE_RESET_IDENTITIES
    pvlan_registered = {k for k in registered if k[0] in ("int_pvlan_host", "int_port_channel_pvlan_host", "int_vpc_pvlan_host")}
    assert pvlan_registered == set(PVLAN_ROUTE_RESET_IDENTITIES), sorted(pvlan_registered ^ set(PVLAN_ROUTE_RESET_IDENTITIES))
    registered = registered - pvlan_registered
    # The same holds for the peer-link parent: its two resets are pinned per identity in test_mode_peer_link.py.
    from .helpers.binding_harness import PEER_LINK_ROUTE_RESET_IDENTITIES
    peer_link_registered = {k for k in registered if k[0] == "int_vpc_peer_link_po"}
    assert peer_link_registered == set(PEER_LINK_ROUTE_RESET_IDENTITIES), sorted(
        peer_link_registered ^ set(PEER_LINK_ROUTE_RESET_IDENTITIES))
    registered = registered - peer_link_registered
    # And for the ToR-uplink parent: its twelve resets are pinned per identity in test_mode_uplink_access.py.
    from .helpers.binding_harness import UPLINK_ROUTE_RESET_IDENTITIES
    uplink_registered = {k for k in registered if k[0] == "int_vpc_uplink_access"}
    assert uplink_registered == set(UPLINK_ROUTE_RESET_IDENTITIES), sorted(
        uplink_registered ^ set(UPLINK_ROUTE_RESET_IDENTITIES))
    registered = registered - uplink_registered
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
    result, calls = run(want_omitting(parent, key, **extra), "replaced", have, **_pkw(parent))
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
    result, calls = run(want_omitting(parent, key, **extra), "replaced", have, **_pkw(parent))
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
    keeps its existing coverage in `test_read_authority.py`.
    """
    have = build_have(parent, key, applied, **extra)
    result, calls = run_configs([cfg_for(parent, want_omitting(parent, key, **extra), deploy=False)],
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

    first, calls1 = run(want_omitting(parent, key, **extra), "replaced", have, **_pkw(parent))
    split1 = split_calls(calls1)
    assert len(split1["updates"]) == 1, "positive control: expected exactly one update"
    assert len(split1["deploys"]) == 1, (
        "deploy was enabled and a value changed, so exactly one deploy is expected; got %d"
        % len(split1["deploys"]))
    emitted = request_nvpairs(calls1)[0][nvpair]
    assert emitted == reset

    have2 = copy.deepcopy(have)
    have2[0]["interfaces"][0]["nvPairs"][nvpair] = emitted
    second, calls2 = run(want_omitting(parent, key, **extra), "replaced", have2, **_pkw(parent))
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
    result, calls = run(want_omitting(parent, key, **extra), "merged", have, **_pkw(parent))
    assert len(split_calls(calls)["updates"]) == 0
    assert result.get("changed") is False


@pytest.mark.parametrize("parent,nvpair,key,applied,reset,extra", PILOT_ITEMS, ids=PILOT_IDS)
def test_merged_unrelated_update_preserves_the_omitted_value(
    parent, nvpair, key, applied, reset, extra
):
    """An unrelated edit under merged must re-send the controller's value, not reset it."""
    have = build_have(parent, key, applied, **extra)
    result, calls = run(want_omitting(parent, key, description="changed-under-merged", **extra), "merged", have, **_pkw(parent))
    nv = request_nvpairs(calls)
    assert nv, "the description change produced no request"
    # `wire_for` rather than `wire_of`: preservation is compared against the WIRE spelling of
    # the applied value, and for the SMU OSPF enums that spelling is not the public one
    # (`no_passive` -> `noPassive`).
    assert nv[0].get(nvpair) == wire_for(parent, key, applied)


def test_merged_is_never_blocked_by_an_unsupported_row():
    """merged has no withdrawal contract, so C7/C8 must not fire for it at all.
    Rehomed to the routed parent with the rest of the C7 family."""
    have = build_have(ROUTED)
    have[0]["interfaces"][0]["nvPairs"]["eigrpIpv4Passive"] = "true"
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
    # The public input that requests the registered reset. For an SMU enum the `reset_wire`
    # is the WIRE spelling (`noChange`), which is deliberately NOT public vocabulary: the
    # module refuses it, and that refusal is correct. What an operator types is `no_change`.
    clear_input = public_clear_for(parent, key, reset)
    # A missing public clear is a fixture/registry DISAGREEMENT, not something to step over.
    # An earlier version skipped here. It never triggered for the two registered enums, whose
    # public clear is `no_change`, but a skip is indistinguishable from a pass in a summary,
    # so the one thing this parametrised suite exists to catch -- a row whose fixture and
    # registry stopped agreeing -- would have gone unreported. A reset that genuinely has no
    # public spelling is a refusal to be asserted, not a case to omit: that is covered
    # explicitly by `test_binding_ospf_routed.py::
    # test_the_public_neutral_is_accepted_and_the_wire_spelling_is_refused`.
    assert clear_input is not None, (
        "no public input spells the registered reset %r of %s::%s, so this pilot fixture and "
        "the registry disagree. If the reset is genuinely not expressible publicly, assert "
        "that refusal in its own case instead of reaching this line." % (reset, parent, nvpair))
    # The public representation is ASSERTED, not merely resolved. Registering a reset must
    # not broaden the public schema, so for a binding with an SMU vocabulary the clear has to
    # be a real public choice that maps to the registered wire reset, and the wire spelling
    # must NOT have become public alongside it.
    binding = engine.resolve_binding(parent, key) or {}
    vocabulary = binding.get("wire_values")
    if vocabulary:
        assert vocabulary.get(clear_input) == reset, (
            "%s::%s public clear %r maps to wire %r, not to the registered reset %r"
            % (parent, nvpair, clear_input, vocabulary.get(clear_input), reset))
        assert clear_input in binding.get("valid_values", ()), (
            "%s::%s public clear %r is not among the public valid_values %r"
            % (parent, nvpair, clear_input, binding.get("valid_values")))
        assert reset not in binding.get("valid_values", ()), (
            "%s::%s wire spelling %r leaked into the public valid_values: registering a reset "
            "widened the public schema" % (parent, nvpair, reset))
    else:
        # A boolean reset is the native bool ("true" first appears with int_routed_host CDP_ENABLE, slice 0b_37).
        expected = {"false": False, "true": True}.get(reset, reset)
        assert clear_input == expected, (
            "%s::%s declares no SMU vocabulary, so its public clear must still be the wire "
            "value itself (a native False for a boolean): expected %r, got %r"
            % (parent, nvpair, expected, clear_input))
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
    result, calls = run(want_omitting(parent, key, **extra), "replaced", have, check_mode=True, **_pkw(parent))
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
    have[0]["interfaces"][0]["nvPairs"]["eigrpIpv4Passive"] = "true"
    result, calls = run_configs([cfg(IF_A, base_for(ROUTED))], "replaced", have)
    split = split_calls(calls)
    assert result.get("failed"), "a required withdrawal that cannot complete reported success"
    assert len(split["updates"]) == 0 and len(split["deploys"]) == 0
    msg = str(result.get("msg", ""))
    assert "eigrp_ipv4_passive" in msg and ROUTED in msg
    assert "must withdraw" in msg


def test_c7_the_same_row_at_its_declared_default_still_succeeds():
    """The control proving the refusal above is not a blanket rejection. Rehomed with it."""
    have = build_have(ROUTED)
    have[0]["interfaces"][0]["nvPairs"]["eigrpIpv4Passive"] = "false"
    result, calls = run_configs([cfg(IF_A, base_for(ROUTED))], "replaced", have)
    assert not result.get("failed"), result.get("msg")


def test_c8_unclassifiable_value_refuses_with_its_own_distinct_reason():
    """A registered row with no declared default and no verified reset. Nothing says whether
    the present value is untouched or deliberate, and unknown is not converged.

    The row is DERIVED: this named `ospf_cost` until its reset was measured.

    THE VALUE IS DERIVED TOO, and that is not cosmetic. It used to be the literal `100`,
    which silently assumed the derived row was an INTEGER. When later rows registered
    the last unclassifiable integers on this parent, the helper started returning a STRING row
    and `build_have` refused the int before any payload was built -- the case then failed deep
    inside the harness ("expected exactly one emitted policy payload, got 0") instead of
    stating the real problem. Deriving the value from the row's declared type keeps the case
    about what it claims to test, whichever row survives as unclassifiable.
    """
    key = an_unclassifiable_key(ROUTED)
    binding = engine.resolve_binding(ROUTED, key)
    declared = binding["type"]
    # The remaining routed example is ospf_tag, whose public length bound makes
    # a longer arbitrary probe invalid before the withdrawal classifier runs.
    value = {"integer": 100, "boolean": True}.get(declared, "PILOT-UNCLASSIFIED")
    have = build_have(ROUTED, key, value)
    result, calls = run(base_for(ROUTED), "replaced", have)
    split = split_calls(calls)
    assert result.get("failed"), (
        "an unclassifiable configured value must not pass (row %r, type %r)" % (key, declared))
    msg = str(result.get("msg", ""))
    assert key in msg and ROUTED in msg
    assert "cannot be classified" in msg, msg
    assert str(value) not in msg, "the refusal named the value"
    assert len(split["updates"]) == 0 and len(split["deploys"]) == 0


def test_check_mode_also_refuses_an_unsupported_withdrawal():
    """Check mode is a report. Reporting a replacement that cannot complete is the same
    false claim as performing one."""
    have = build_have(ROUTED)
    have[0]["interfaces"][0]["nvPairs"]["eigrpIpv4Passive"] = "true"
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
    have[1]["interfaces"][0]["nvPairs"]["eigrpIpv4Passive"] = "true"
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
    # ACCESS, not ROUTED: `bfdEcho` is NOT registered on int_access_host, so assigning it here
    # made the engine ignore the key entirely and this case passed without exercising any
    # registered field. Restored to the row that is registered on this parent.
    assert engine.resolve_binding(ACCESS, "disable_lldp_receive") is not None, (
        "int_access_host::disable_lldp_receive is not registered, so this HAVE carries a key the "
        "engine ignores and the case proves nothing about encoding equivalence")
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
    result, calls = run(want_omitting(parent, key, **extra), "replaced", have, **_pkw(parent))
    assert len(split_calls(calls)["updates"]) == 0


@pytest.mark.parametrize("parent,nvpair,key,applied,reset,extra", PILOT_ITEMS, ids=PILOT_IDS)
def test_authoritative_absence_is_nothing_to_withdraw(parent, nvpair, key, applied, reset, extra):
    """An absent key is absent. No default may be invented for it."""
    have = build_have(parent, key, applied, **extra)
    have[0]["interfaces"][0]["nvPairs"].pop(nvpair, None)
    result, calls = run(want_omitting(parent, key, **extra), "replaced", have, **_pkw(parent))
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
    It is recorded here rather than repaired.
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

    THE OBSERVABLE CHANGED, THE CONTRACT DID NOT. This case used to prove "it was considered"
    by the invocation being REFUSED, because the row carried no verified reset. The OSPF-ALL
    P3a profile measured and registered one (`'1'`, its declared default, measured live on the
    four subjects in P3a-a4-keyid-default), so a refusal is no longer the right observable --
    and the case failed against its own expired premise, not against the rule it guards.

    The replacement observable is STRONGER: proof of consideration is now that the withdrawal
    is EMITTED. The outgoing body must carry the registered reset for this parent's row. A
    name-only exclusion would leave the field untouched, which this assertion would catch.
    """
    b = engine.resolve_binding(ROUTED, "ospf_auth_key_id")
    assert b is not None and b.get("reset_wire") is not None, (
        "the row lost its reset; this case would be asserting the wrong observable again")
    expected = b["reset_wire"]
    have = build_have(ROUTED, enable_ospf_auth=True, ospf_auth_key_id=7,
                      ospf_auth_key="SyntheticSetupKey0001")
    result, calls = run(base_for(ROUTED, enable_ospf_auth=True,
                                 ospf_auth_key="SyntheticSetupKey0001"), "replaced", have)
    assert not result.get("failed"), (
        "the registered row was refused: %s" % result.get("msg"))
    emitted = [nv.get("OSPF_AUTH_KEY_ID") for nv in request_nvpairs(calls)]
    assert expected in emitted, (
        "a user-parent binding whose name matches a fabric-owned field was skipped: the "
        "outgoing body carries %r and the registered reset is %r, so the exclusion is not "
        "parent-qualified" % (emitted, expected))


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
    assert len(collateral) == 10, sorted(   # + the two rows on int_l3_port_channel (slice 0b_40)
        (r["parent_template"], r["parent_nvpair"]) for r in collateral)
    assert {r["parent_template"] for r in collateral} == {
        "int_loopback", ROUTED, "int_subif", "int_vlan", "int_l3_port_channel"}
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
    # ACCESS again, and the old `# a C7 row` comment was wrong even before the LLDP lot:
    # int_access_host::disable_lldp_receive carries a measured reset, so at "true" it is a row that
    # `replaced` WOULD WITHDRAW -- not an unsupported C7 row that `replaced` would refuse. Either
    # way it is the right fixture for this case, because what is under test is that `deleted` does
    # not enter the withdrawal path at all. The claim is now stated as what it is.
    assert engine.resolve_binding(ACCESS, "disable_lldp_receive").get("reset_wire") is not None, (
        "this case needs a row `replaced` would actually withdraw, so that `deleted` skipping the "
        "withdrawal path means something; int_access_host::disable_lldp_receive no longer has a reset")
    have = have_for([IF_A], ACCESS, "acl_filter", "ACL-PILOT")
    have[0]["interfaces"][0]["nvPairs"]["lldpReceive"] = "true"   # a row `replaced` would withdraw
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


# ====================================================================================================
# Formerly test_dcnm_intf_withdrawal_after_upstream.py
# Two withdrawal expectations the existing suite does not cover, added with the
# integration of upstream #727/#728.
#
#   * MULTI-FIELD WITHDRAWAL -- a pre-existing coverage gap, not an integration effect.
#     The existing suite is parametrized one (parent, nvPair) at a time, which shows that
#     each accepted binding can be withdrawn, not that SEVERAL omitted in the same
#     invocation all reach the same payload. A loop that reconciled only the first omission,
#     or that rebuilt the payload per binding, would pass every existing row and still lose
#     every reset after the first. These three cases PASS on the pre-rebase candidate too;
#     they close the gap and pin that the rebase did not disturb the behaviour.
#
#   * OMITTED `fec` TOGETHER WITH AN OMITTED BINDING -- only assertable after the
#     integration. Before #728 an omitted `fec` serialized as a public FEC-null against the
#     controller's stored "auto", so a `replaced` rerun never converged. The live measurement
#     worked around it by holding `fec: auto` explicit, which is why both ethernet bases in
#     the harness still do. These two cases FAIL on the pre-rebase candidate (measured:
#     `FEC` None instead of "auto", and a rerun that configures again) and pass here.
#
# Both cases drive the real `main()` through the existing harness and assert on the CAPTURED
# REQUEST at the transport boundary and on the PUBLIC DIFF, never on `changed`. Update,
# deploy and read calls are counted separately at the stub.
#
# NOT LIVE TESTED. No controller or switch is contacted. These are offline
# integration assertions; they do not revalidate any of the 70 accepted bindings live.
# ====================================================================================================
# Five accepted ACCESS bindings whose PILOT rows carry no prerequisite context, so the
# only moving part is how many omissions one invocation reconciles. Values and resets are
# the PILOT rows verbatim; nothing is re-derived here.
MULTI = {
    "aclFilter": ("acl_filter", "ACL-PILOT", ""),
    "lldpTransmit": ("disable_lldp_transmit", True, "false"),
    "lldpReceive": ("disable_lldp_receive", True, "false"),
    "flowcontrolReceive": ("flowcontrol_receive", "on", "off"),
    "flowcontrolSend": ("flowcontrol_send", "on", "off"),
}


def applied_profile():
    """`base_for(ACCESS)` with all five bindings held explicit."""
    return base_for(ACCESS, **{key: applied for (key, applied, _reset) in MULTI.values()})


def multi_have():
    return build_have(ACCESS, **{key: applied for (key, applied, _reset) in MULTI.values()})


def emitted_policies(calls):
    """The policy objects in the configuration updates, as HAVE for a rerun.

    Taken from the module's OWN outbound payload for the same reason `build_have` does it:
    a HAVE invented by the test can assert a shape the module never produces.
    """
    out = []
    for call in split_calls(calls)["updates"]:
        payload = call["payload"]
        for item in payload if isinstance(payload, list) else [payload]:
            if isinstance(item, dict) and "policy" in item and "interfaces" in item:
                policy = copy.deepcopy(item)
                policy["interfaces"][0]["interfaceType"] = "INTERFACE_ETHERNET"
                policy["interfaces"][0]["fabricName"] = FABRIC
                out.append(policy)
    return out


def sole_update_nvpairs(calls):
    updates = split_calls(calls)["updates"]
    assert len(updates) == 1, "expected exactly one configuration update, got %d" % len(updates)
    policies = emitted_policies(calls)
    assert len(policies) == 1, "expected one policy in the update, got %d" % len(policies)
    return policies[0]["interfaces"][0]["nvPairs"]


# --------------------------------------------------------------------- multi-field
def test_every_omitted_binding_reaches_the_same_payload():
    """Five omissions, one payload, five resets -- not just the first."""
    have = multi_have()
    result, calls = run(base_for(ACCESS), "replaced", have=have)

    assert not result.get("failed"), result.get("msg")
    nvpairs = sole_update_nvpairs(calls)

    missing = {nvpair: reset for nvpair, (_key, _applied, reset) in MULTI.items()
               if nvpairs.get(nvpair) != reset}
    assert not missing, "resets absent or wrong in the single payload: %s (got %s)" % (
        missing,
        {n: nvpairs.get(n) for n in MULTI},
    )


def test_every_omitted_binding_is_reported_in_the_public_diff():
    """A transmitted reset that is not reported is the defect class this pins."""
    have = multi_have()
    result, _calls = run(base_for(ACCESS), "replaced", have=have)

    assert not result.get("failed"), result.get("msg")
    reported = {}
    for entry in result.get("diff", []):
        for bucket in entry.values() if isinstance(entry, dict) else []:
            for item in bucket if isinstance(bucket, list) else []:
                if not isinstance(item, dict) or "interfaces" not in item:
                    continue
                reported.update(item["interfaces"][0].get("nvPairs") or {})

    missing = {nvpair: reset for nvpair, (_key, _applied, reset) in MULTI.items()
               if reported.get(nvpair) != reset}
    assert not missing, "resets transmitted but not reported: %s" % missing


def test_holding_all_five_explicit_withdraws_nothing():
    """The control for the case above: explicit values are retained, not reset."""
    have = multi_have()
    result, calls = run(applied_profile(), "replaced", have=have)

    assert not result.get("failed"), result.get("msg")
    buckets = split_calls(calls)
    assert buckets["updates"] == [], "explicit values produced a configuration update"
    assert buckets["deploys"] == [], "explicit values produced a deploy"


# --------------------------------------------------------- omitted fec + omitted binding
def test_omitted_fec_and_omitted_binding_share_one_payload():
    """#728 normalizes the omitted `fec` while our reset still reaches the same request."""
    have = build_have(ACCESS, acl_filter="ACL-PILOT")
    want = base_for(ACCESS)
    want.pop("fec", None)

    result, calls = run(want, "replaced", have=have)

    assert not result.get("failed"), result.get("msg")
    nvpairs = sole_update_nvpairs(calls)
    assert nvpairs.get("FEC") == "auto", "omitted fec did not normalize to auto: %r" % (nvpairs.get("FEC"),)
    assert nvpairs.get("aclFilter") == "", "the accepted binding was not withdrawn alongside the fec default: %r" % (nvpairs.get("aclFilter"),)


def test_rerun_against_the_controller_stored_fec_is_a_no_op():
    """The convergence the explicit `fec: auto` workaround used to be needed for.

    The HAVE is what the CONTROLLER stores after the withdrawal: `fec` at its stored
    default "auto" -- BASE_ACCESS holds it explicit, so the value comes from the module's
    own payload -- and the accepted binding already at its reset. WANT omits both again.

    Converging against the module's own previous echo proves nothing here: before #728 that
    echo carried FEC None, so a second run matched it and looked idempotent while still
    disagreeing with the controller forever. This asserts against "auto", which is the
    value the historical FEC observation actually diffed against.
    """
    have = build_have(ACCESS, acl_filter="")
    stored = have[0]["interfaces"][0]["nvPairs"]
    assert (
        stored.get("FEC") == "auto"
    ), "the HAVE does not carry the controller's stored default, so this test would not " "reproduce the historical non-convergence: %r" % (stored.get("FEC"),)

    want = base_for(ACCESS)
    want.pop("fec", None)

    result, calls = run(want, "replaced", have=have)

    assert not result.get("failed"), result.get("msg")
    buckets = split_calls(calls)
    assert buckets["updates"] == [], "the rerun configured again instead of converging: %s" % [
        policy["interfaces"][0]["nvPairs"].get("FEC") for policy in emitted_policies(calls)
    ]
    assert buckets["deploys"] == [], "the rerun deployed with nothing to configure"


# ====================================================================================================
# Formerly test_gie_damp_grouped_omission.py
# Dampening: the SEVEN withdrawn as one group, through the real `main()`.
#
# EXPERIMENTAL / CONTROLLER-ONLY. The seven resets these cases rely on are CANDIDATES from a
# local experimental registration, registered so the omission path can be executed and observed at
# a controller. They are NOT accepted device resets, they are NOT part of the 157 integration,
# and nothing was deployed when they were observed -- so no device acceptance exists
# for any of the seven.
#
# WHY THIS FILE EXISTS RATHER THAN SEVEN PER-ROW FIXTURES
#
# The parent declares five conditional rules over this family, and rule 2 (`all_or_none`) makes
# `dampeningReuse`, `dampeningSuppress` and `dampeningMaxSuppress` withdrawable only TOGETHER: a
# per-row omission of any one of them describes a controller state that cannot exist -- two of
# the three present, one absent. A per-row fixture for those would be green in the mock and
# impossible on a controller, which is the failure mode the pilot matrix exists to avoid. They
# are named in `GROUPED_ONLY_NO_PER_ROW_FIXTURE` in the harness and covered here instead.
#
# The other four DO have per-row fixtures in the matrix; they are re-exercised here as part of
# the group, because "each one works alone" and "all seven work together in one request" are
# different statements.
#
# WHAT IS ASSERTED
#
# The captured REQUEST and the PUBLIC DIFF, never `changed` alone. Deploy flags are asserted
# FALSE on every case: the contract is that nothing reaches a device.
#
# Offline. No controller and no device.
# ====================================================================================================
# The valid seven-field positive: it satisfies all five conditional rules and every declared
# range. Written out rather than derived, so a change to the rules shows up as a failure here
# instead of being silently followed.
POSITIVE = {
    "enable_dampening": True,          # rule 1: any explicit value needs the gate
    "dampening_half_life": 5,          # 1..30      -- rule 3: reuse needs it
    "dampening_reuse": 750,            # 1..20000   -- rule 2: with suppress + max
    "dampening_suppress": 2000,        # 1..20000
    "dampening_max_suppress": 60,      # 1..255
    "dampening_restart": True,         # rule 4: needs half_life+reuse+suppress+max
    "dampening_restart_penalty": 1000,  # 1..20000  -- rule 5: needs restart true
}

# nvPair spelling, and the reset each identity is entitled to. Hand-written, independent of the
# table: an expectation read back from the subject under test cannot fail.
EXPECTED_RESET = {
    "dampening": "false",
    "dampeningRestart": "false",
    "dampeningHalfLife": "",
    "dampeningReuse": "",
    "dampeningSuppress": "",
    "dampeningMaxSuppress": "",
    "dampeningRestartPenalty": "",
}

# What the controller holds once the positive is applied, per identity.
EXPECTED_APPLIED = {
    "dampening": "true",
    "dampeningRestart": "true",
    "dampeningHalfLife": "5",
    "dampeningReuse": "750",
    "dampeningSuppress": "2000",
    "dampeningMaxSuppress": "60",
    "dampeningRestartPenalty": "1000",
}


def _have():
    return build_have(ROUTED, **POSITIVE)


def _run(profile, state, **kw):
    """Drive `main()` with `deploy: False`, as the live observation did in EVERY
    step. The harness default is `deploy=True`; leaving it would assert against a model that
    was never sent, and the deploy-flag assertions below would be meaningless."""
    return run_configs([cfg(IF_A, profile, deploy=False)], state, deploy=False, **kw)


def test_the_seven_are_registered_before_anything_below_is_meaningful():
    """Guard the guard. Without the experimental metadata the module REFUSES these omissions,
    and a refusal is not a withdrawal -- every case below would pass for the wrong reason."""
    for nvpair, reset in sorted(EXPECTED_RESET.items()):
        key = [k for k in POSITIVE
               if resolve_binding(ROUTED, k)["parent_nvpair"] == nvpair][0]
        b = resolve_binding(ROUTED, key)
        assert b.get("reset_wire") == reset, (
            "%s::%s reset is %r, declared %r" % (ROUTED, nvpair, b.get("reset_wire"), reset))
        assert isinstance(b["reset_wire"], str), (
            "%s::%s reset_wire is %s; the controller returns this nvPair as a string"
            % (ROUTED, nvpair, type(b["reset_wire"]).__name__))


def test_the_three_all_or_none_members_are_the_declared_grouped_only_set():
    """The harness's declaration and this file's reason must not drift apart. If a per-row
    fixture is ever added for one of the three, this fails and points at the rule that made it
    impossible."""
    # Scoped to this family: other families may declare their own grouped-only members (the HSRP
    # forwarding-threshold pair on int_vlan does), and that must not read as dampening drift.
    assert {k for k in GROUPED_ONLY_NO_PER_ROW_FIXTURE if k[1].startswith("dampening")} == {
        (ROUTED, "dampeningReuse"),
        (ROUTED, "dampeningSuppress"),
        (ROUTED, "dampeningMaxSuppress"),
    }, sorted(GROUPED_ONLY_NO_PER_ROW_FIXTURE)


def test_the_omission_model_carries_none_of_the_seven():
    """The absence must be EFFECTIVE, not a `false`/`''` the fixture slipped in. A model that
    re-declared the targets would make every case below an ordinary apply."""
    want = base_for(ROUTED)
    present = [k for k in POSITIVE if k in want]
    assert not present, "the omission model still declares: %s" % present


def test_merged_preserves_all_seven():
    """CONTROL: the resets below belong to the WITHDRAWAL path, not to the shape of the model.
    Under `merged` the same omission preserves every one of the seven."""
    result, calls = _run(base_for(ROUTED, description="damp-merged"), "merged", have=_have())
    assert not result.get("failed"), result.get("msg")
    nv = request_nvpairs(calls)
    assert nv, "the description change produced no request"
    for nvpair, applied in sorted(EXPECTED_APPLIED.items()):
        assert nv[0].get(nvpair) == applied, (
            "merged did not preserve %s: %r, expected %r"
            % (nvpair, nv[0].get(nvpair), applied))
    assert split_calls(calls)["deploys"] == [], "merged sent a deploy request"


def test_check_mode_plans_all_seven_and_transmits_nothing():
    """A plan is not a write. "It did not write" alone would also describe a check mode that
    planned nothing at all, so both halves are asserted."""
    result, calls = _run(base_for(ROUTED), "replaced", have=_have(), check_mode=True)
    dnv = diff_nvpairs(result)
    assert dnv, "check mode planned nothing at all"
    for nvpair, reset in sorted(EXPECTED_RESET.items()):
        assert dnv[0].get(nvpair) == reset, (
            "check mode did not plan %s: %r, expected %r"
            % (nvpair, dnv[0].get(nvpair), reset))
    buckets = split_calls(calls)
    assert buckets["updates"] == [], "check mode sent a configuration request"
    assert buckets["deploys"] == [], "check mode sent a deploy request"


def test_replaced_withdraws_all_seven_in_one_request():
    """The grouped property: one payload carries all seven resets.

    EXACTLY one update. "All seven appear somewhere" would also be true of a run that split
    them across requests, and the all_or_none rule means a split is precisely the shape the
    controller would refuse.
    """
    result, calls = _run(base_for(ROUTED), "replaced", have=_have())
    assert not result.get("failed"), result.get("msg")
    updates = split_calls(calls)["updates"]
    assert len(updates) == 1, "expected exactly one request, got %d" % len(updates)
    assert split_calls(calls)["deploys"] == [], (
        "the withdrawal sent a deploy request; this campaign is deploy:false throughout")
    nv = request_nvpairs(calls)
    for nvpair, reset in sorted(EXPECTED_RESET.items()):
        assert nv[0].get(nvpair) == reset, (
            "%s travelled as %r, expected the reset %r" % (nvpair, nv[0].get(nvpair), reset))
    # And the public diff owns all seven too, independently of the request body.
    dnv = diff_nvpairs(result)
    assert dnv, "nothing was reported in the public diff"
    for nvpair, reset in sorted(EXPECTED_RESET.items()):
        assert dnv[0].get(nvpair) == reset, (
            "%s was reset in the request but is %r in the diff" % (nvpair, dnv[0].get(nvpair)))


@pytest.mark.parametrize("nvpair", sorted(EXPECTED_RESET))
def test_the_five_numbers_are_cleared_per_identity_not_by_the_gate_alone(nvpair):
    """Per-identity, so turning the gate off cannot masquerade as clearing the numbers.

    This is the whole reason the assertions are per-nvPair rather than "the rendered line is
    gone": on a controller the gate empties the RENDER while the five value nvPairs keep their
    contents, so a line-level check would score a partial clear as complete.
    """
    _result, calls = _run(base_for(ROUTED), "replaced", have=_have())
    nv = request_nvpairs(calls)[0]
    assert nv.get(nvpair) == EXPECTED_RESET[nvpair], (
        "%s is %r, expected %r" % (nvpair, nv.get(nvpair), EXPECTED_RESET[nvpair]))


def test_unrelated_fields_survive_the_grouped_withdrawal():
    """A reset that spilled onto a field nobody withdrew would be invisible in a count."""
    have = _have()
    before = dict(have[0]["interfaces"][0]["nvPairs"])
    _result, calls = _run(base_for(ROUTED), "replaced", have=have)
    nv = request_nvpairs(calls)[0]
    spilled = {
        k: (before[k], nv.get(k))
        for k in before
        if not k.startswith("dampening") and k in nv and nv[k] != before[k]
    }
    assert not spilled, "the withdrawal changed fields nobody omitted: %s" % spilled


# ====================================================================================================
# Formerly test_dcnm_intf_default_reset_registered_f2.py
# Resetting a physical port to its role default also withdraws registered drift.
#
# Named `deleted` and `overridden` used to compare the role default payload with the controller's policy on legacy nvPairs
# only, and the default payload carries no registered nvPair. A port whose only drift was a registered field (an ACL, flow
# control) read as already default; a reset that was sent for another reason left the field in place.
#
# Real main() through helpers/binding_harness. The roles are the ones NDFC returns, lower-case ("leaf" -> int_trunk_host,
# "border" -> int_routed_host); the binding fixture's "Leaf" is not representative and is not used. The transport only adds
# the physical-port flags a real 12.6.0.267 interface-detail read carries (deletable "false", editAllowed "true",
# mgmtIpAddress), so the named `deleted` path is in scope. The "already default" HAVE is the module's own emitted reset
# payload. Values are synthetic.
# ====================================================================================================
ACL = "SYNTHETIC-ACL"
NO_WITHDRAWAL = "This module has no verified withdrawal for it; it must be cleaned up by a separate, verified procedure"
ROLES = {
    "leaf": dict(default=h.TRUNK, drift={"aclFilter": ACL, "flowcontrolReceive": "on"},
                 seed=dict(acl_filter=ACL, flowcontrol_receive="on")),
    "border": dict(default=h.ROUTED, drift={"ipv4AclIn": ACL}, seed=dict(ipv4_acl_in=ACL)),
}


_DEFAULT_HAVE = {}


def default_have(role):
    """The role default exactly as this module writes it (legacy drift reset once, payload taken back)."""
    if role not in _DEFAULT_HAVE:
        seed = h.build_have(ROLES[role]["default"], description="legacy-drift")
        _r, calls = role_reset_run("deleted", seed, role)
        _DEFAULT_HAVE[role] = as_have(calls)
    return copy.deepcopy(_DEFAULT_HAVE[role])


# ------------------------------------------------------------------ the finding, fixed
@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("role", sorted(ROLES))
def test_registered_only_drift_is_reset_with_the_registry_wires(role, state):
    have = default_have(role)
    have[0]["interfaces"][0]["nvPairs"].update(ROLES[role]["drift"])
    result, calls = role_reset_run(state, have, role)
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is True and len(h.split_calls(calls)["updates"]) == 1
    sent = nvpairs_of_reset(calls)
    assert reset_policies(calls)[0]["policy"] == ROLES[role]["default"]
    for nvpair in ROLES[role]["drift"]:
        assert sent[nvpair] == reset_wire(ROLES[role]["default"], nvpair), nvpair


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("role", sorted(ROLES))
def test_legacy_and_registered_drift_reset_carries_both(role, state):
    seed = h.build_have(ROLES[role]["default"], description="legacy-drift", **ROLES[role]["seed"])
    result, calls = role_reset_run(state, seed, role)
    assert not result.get("failed"), result.get("msg")
    sent = nvpairs_of_reset(calls)
    assert sent["DESC"] == ""
    for nvpair in ROLES[role]["drift"]:
        assert sent[nvpair] == reset_wire(ROLES[role]["default"], nvpair), nvpair


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("role", sorted(ROLES))
def test_already_default_stays_a_noop(role, state):
    result, calls = role_reset_run(state, default_have(role), role)
    assert not result.get("failed") and result["changed"] is False and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("role", sorted(ROLES))
def test_second_run_over_the_reset_it_wrote_is_a_noop(role, state):
    have = default_have(role)
    have[0]["interfaces"][0]["nvPairs"].update(ROLES[role]["drift"])
    _r1, calls1 = role_reset_run(state, have, role)
    result, calls = role_reset_run(state, as_have(calls1), role)
    assert not result.get("failed") and result["changed"] is False and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("role", sorted(ROLES))
def test_capability_disabled_keeps_the_published_noop(role, state):
    """Without an approved patch_version the classifier answers 'inapplicable': no reset, no failure."""
    have = default_have(role)
    have[0]["interfaces"][0]["nvPairs"].update(ROLES[role]["drift"])
    result, calls = role_reset_run(state, have, role, patch_version=None)
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


# ------------------------------------------------------------------ no established reset: refused before any write
@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize(
    "nvpair, value, field, reason, gate, remedy",
    [
        ("eigrpIpv4Passive", "true", "eigrp_ipv4_passive", "no verified reset is established", {}, None),
        # D-3: ospfTag with OSPF on is no longer refused here -- the same reset sends ospf "false", which makes the tag
        # inert (test_binding_role_resets.py). The gate remedy is still named when the gate cannot be reset.
    ],
)
def test_registered_drift_without_a_reset_is_refused_before_any_write(state, nvpair, value, field, reason, gate, remedy):
    have = default_have("border")
    have[0]["interfaces"][0]["nvPairs"][nvpair] = value
    have[0]["interfaces"][0]["nvPairs"].update(gate)
    result, calls = role_reset_run(state, have, "border")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    msg = result["msg"]
    assert reason in msg and "%s (%s) on %s [%s], parent int_routed_host" % (field, nvpair, h.IF_A, h.SERIAL) in msg
    assert "No configuration or deployment request was sent" in msg
    # R-F2-1: an explicit empty value is not a verified withdrawal, so it is never offered; the only remedy
    # named is the module's own (disabling the field's gate), and only for a field that has one.
    assert "clear the field on that policy" not in msg and "Clear the field explicitly" not in msg
    if remedy is None:
        assert NO_WITHDRAWAL in msg
    else:
        assert remedy in msg and NO_WITHDRAWAL not in msg
    assert value not in msg


# ------------------------------------------------------------------ policy change (source != role default)
@pytest.mark.parametrize("state", STATES)
def test_policy_change_with_a_source_only_field_is_refused_and_never_injected(state):
    """border: default int_routed_host; HAVE is int_trunk_host with an ACL. int_routed_host does not register aclFilter.
    The controller's negation of inline lines for this transition is declared (cleared_on_change_to, P2); the refusal
    branch and its R-F2-1 remedy are exercised with that declaration removed from this one row for the test."""
    seed = h.build_have(h.TRUNK, acl_filter=ACL)
    with patch.dict(table.resolve_by_nvpair(h.TRUNK, "aclFilter"), {"cleared_on_change_to": ()}):
        result, calls = role_reset_run(state, seed, "border")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    assert "acl_filter (aclFilter) on %s [%s], int_trunk_host -> int_routed_host" % (h.IF_A, h.SERIAL) in result["msg"]
    # R-F2-1: the source parent (int_trunk_host) HAS a verified reset for aclFilter -> the remedy is offered
    assert "Its current policy has a verified reset: clear the field on that policy first" in result["msg"]
    assert NO_WITHDRAWAL not in result["msg"]
    assert ACL not in result["msg"]


@pytest.mark.parametrize("state", STATES)
def test_policy_change_uses_the_destination_reset_for_a_field_both_parents_register(state):
    seed = h.build_have(h.TRUNK, disable_lldp_receive=True)
    assert seed[0]["interfaces"][0]["nvPairs"]["lldpReceive"] == "true"
    result, calls = role_reset_run(state, seed, "border")
    assert not result.get("failed"), result.get("msg")
    pol = reset_policies(calls)
    assert len(pol) == 1 and pol[0]["policy"] == h.ROUTED
    assert pol[0]["interfaces"][0]["nvPairs"]["lldpReceive"] == reset_wire(h.ROUTED, "lldpReceive")
    assert "aclFilter" not in pol[0]["interfaces"][0]["nvPairs"]


@pytest.mark.parametrize("state", STATES)
def test_unrelated_legacy_conversion_is_not_blocked(state):
    seed = h.build_have(h.TRUNK, description="legacy-drift")
    result, calls = role_reset_run(state, seed, "border")
    assert not result.get("failed"), result.get("msg")
    assert [p["policy"] for p in reset_policies(calls)] == [h.ROUTED]


# ------------------------------------------------------------------ scope: a port that is not reset never refuses
def test_named_deleted_skip_when_not_editable_gains_no_refusal():
    have = default_have("border")
    have[0]["interfaces"][0]["nvPairs"]["eigrpIpv4Passive"] = "true"
    result, calls = role_reset_run("deleted", have, "border", flags={"deletable": "false", "editAllowed": "false", "mgmtIpAddress": h.SWITCH_IP})
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


def test_overridden_keeps_a_configured_port_out_of_the_reset_refusal():
    """IF_A stays in the playbook: it is configured, not reset, so its unsupported registered value
    cannot block the run (the retained-interface rules own it)."""
    have = default_have("border")
    have[0]["interfaces"][0]["nvPairs"]["eigrpIpv4Passive"] = "true"
    conf = [h.cfg(h.IF_A, h.base_for(h.ROUTED, eigrp_ipv4_passive=True, **h.EIGRP_CTX))]
    result, _calls = role_reset_run("overridden", have, "border", configs=conf)
    assert "Resetting these interfaces" not in (result.get("msg") or ""), result.get("msg")


# ------------------------------------------------------------------ no_log: a refused secret never reaches the output
def test_a_refused_secret_is_named_by_field_and_never_emitted():
    """OSPF_AUTH_KEY has no verified reset on int_routed_host: a border reset refuses, and the key
    (registered from the controller response as no_log) is absent from the real serialised result."""
    assert h.real_serialiser_is_genuine()
    key = "SYNTHETIC-Secret-K1"
    have = default_have("border")
    have[0]["interfaces"][0]["nvPairs"]["OSPF_AUTH_KEY"] = key
    configs = [{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}]
    with patch.object(h, "_transport", _physical_transport(PHYSICAL)):
        out, calls = h.emit_real_result(configs, "deleted", have=have,
                                        extra_patch=patch.object(module, "get_fabric_inventory_details", return_value=_inventory("border")))
    assert h.writes(calls) == []
    assert "ospf_auth_key (OSPF_AUTH_KEY) on %s" % h.IF_A in out
    assert key not in out


# ------------------------------------------------------------------ R-F2-1: message per case, a remedy only where one exists
@pytest.mark.parametrize("state", STATES)
def test_policy_change_without_a_source_reset_offers_no_module_remedy(state):
    """leaf: default int_trunk_host; HAVE is int_routed_host with EIGRP IPv4 passive set (no verified reset on the
    source, not registered on the destination, no gate that makes it inert). int_routed_host drops every binding with
    the policy change (dropped_on_policy_change), so the message branch is exercised with the marker removed from
    this one row for the duration of the test: refused, and no clear-on-current-policy advice."""
    have = default_have("border")
    have[0]["interfaces"][0]["nvPairs"]["eigrpIpv4Passive"] = "true"
    with patch.dict(table.resolve_by_nvpair(h.ROUTED, "eigrpIpv4Passive"), {"dropped_on_policy_change": False}):
        result, calls = role_reset_run(state, have, "leaf")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    msg = result["msg"]
    assert "eigrp_ipv4_passive (eigrpIpv4Passive) on %s [%s], int_routed_host -> int_trunk_host" % (h.IF_A, h.SERIAL) in msg
    assert NO_WITHDRAWAL in msg and "clear the field on that policy" not in msg and "disable " not in msg


@pytest.mark.parametrize("state", STATES)
def test_unreadable_registered_value_is_refused_without_a_remedy(state):
    have = default_have("border")
    have[0]["interfaces"][0]["nvPairs"]["lldpReceive"] = "True"     # not a boolean wire spelling the validator accepts
    result, calls = role_reset_run(state, have, "border")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    msg = result["msg"]
    assert "not readable as its type" in msg
    assert "disable_lldp_receive (lldpReceive) on %s [%s], parent int_routed_host" % (h.IF_A, h.SERIAL) in msg
    assert NO_WITHDRAWAL in msg


# ------------------------------------------------------------------ R-F2-2: only GIE_WITHDRAW_NONE proves the destination neutral
# Helper-level: the classifier is forced for the DESTINATION parent only, inside the test. Not reachable through main() today
# (every Ethernet binding shares the 12.6.0.267 floor and the one patch gate); a future per-binding floor would make it so.
def _helper():
    intf = object.__new__(module.DcnmIntf)
    intf.ndfc_version = h.SUPPORTED
    intf.patch_version = h.SUPPORTED_PATCH
    return intf


def _payloads(value):
    uelem = {"policy": h.ROUTED, "interfaces": [{"ifName": h.IF_A, "serialNumber": h.SERIAL, "nvPairs": {}}]}
    have = {"policy": h.TRUNK, "interfaces": [{"ifName": h.IF_A, "serialNumber": h.SERIAL, "nvPairs": {"lldpReceive": value}}]}
    return uelem, have


def _force_destination(action):
    real = module.gie_withdrawal_action

    def fake(parent, key, value, ndfc_version, patch_version=None):
        if parent == h.ROUTED:
            return action, None
        return real(parent, key, value, ndfc_version, patch_version)
    return patch.object(module, "gie_withdrawal_action", fake)


def test_destination_inapplicable_is_a_transition_refusal_not_a_neutral_value():
    uelem, have = _payloads("true")
    with _force_destination(engine.GIE_WITHDRAW_INAPPLICABLE):
        resets, blocked = _helper().dcnm_intf_default_registered_resets(uelem, have)
    assert resets == {}
    assert [(b["reason"], b["nvpair"], b["parent"], b["destination"], b["source_reset"]) for b in blocked] == [
        ("transition", "lldpReceive", h.TRUNK, h.ROUTED, True)]
    assert uelem["interfaces"][0]["nvPairs"] == {}          # pure: nothing applied


def test_destination_none_still_proves_neutrality():
    uelem, have = _payloads("true")
    with _force_destination(engine.GIE_WITHDRAW_NONE):
        resets, blocked = _helper().dcnm_intf_default_registered_resets(uelem, have)
    assert resets == {} and blocked == []


def test_destination_verified_reset_is_still_used_unforced():
    uelem, have = _payloads("true")
    resets, blocked = _helper().dcnm_intf_default_registered_resets(uelem, have)
    assert resets == {"lldpReceive": reset_wire(h.ROUTED, "lldpReceive")} and blocked == []


@pytest.mark.parametrize("action", ["GIE_WITHDRAW_UNSUPPORTED", "GIE_WITHDRAW_UNCLASSIFIED"])
def test_destination_unsupported_or_unclassified_still_refuses(action):
    uelem, have = _payloads("true")
    with _force_destination(getattr(engine, action)):
        resets, blocked = _helper().dcnm_intf_default_registered_resets(uelem, have)
    assert resets == {} and [b["reason"] for b in blocked] == ["transition"]


# ====================================================================================================
# Formerly test_gie_retirement_scope.py
# Retirement scope: resetting a physical Ethernet to its role default with registered fields configured.
#
# int_routed_host realizes all its configuration in interface-scoped child policies and removes them in delete(); the
# generator marks every one of its bindings dropped_on_policy_change. A leaf reset (int_routed_host -> int_trunk_host)
# therefore proceeds for every consistent field group, with the same single write as a neutral routed port, and never
# sends a source-only field or its key material. What stays refused: the border same-parent cases (EIGRP passive without
# a verified reset; OSPF on with a tag) and the border transitions from the inline-rendered int_trunk_host and
# int_access_host, whose cleanup is not established. Real main() through helpers/binding_harness; values are synthetic.
# ====================================================================================================
KEY = "SYNTHETIC-KEY-MATERIAL"
ROUTED_GROUPS = {
    "arp_bfd": {"arpTimeout": "1200", "bfdEcho": "true"},
    "dampening": {"dampening": "true", "dampeningHalfLife": "20", "dampeningReuse": "800", "dampeningSuppress": "2500",
                  "dampeningMaxSuppress": "80"},
    "pim": {"ENABLE_PIM_SPARSE": "true", "PIM_DR_PRIORITY": "10", "pimBfdInstance": "true"},
    "eigrp_routing": {"eigrpRouting": "true", "eigrpProcessTag": "SYN-EIGRP", "eigrpShutdown": "true", "eigrpBfd": "true"},
    "eigrp_passive": {"eigrpRouting": "true", "eigrpProcessTag": "SYN-EIGRP", "eigrpIpv4Passive": "true"},
    "eigrp_v6_dist": {"eigrpRouting": "true", "eigrpProcessTag": "SYN-EIGRP", "eigrpIpv6Routing": "true",
                      "eigrpIpv4DistributeListPrefixList": "SYN-PL", "eigrpIpv4DistributeListDirection": "in"},
    "ospf_base": {"ospf": "true", "OSPF_AREA_ID": "0.0.0.0"},
    "ospf_active": {"ospf": "true", "ospfTag": "SYN-OSPF", "OSPF_AREA_ID": "0.0.0.1", "ospfCost": "20",
                    "ospfNetworkType": "point_to_point"},
    "ospf_auth_md5": {"ospf": "true", "ospfTag": "SYN-OSPF", "ospfAuthentication": "true",
                      "ospfAuthenticationKey": "md5", "OSPF_AUTH_KEY_ID": "7", "OSPF_AUTH_KEY": KEY},
    "macsec": {"macsecInterfacePolicy": "true", "macsecKeyChainName": "SYN-KC", "macsecPolicyName": "SYN-MP"},
    "rt1_five": {"ipv4Redirects": "true", "ipv6Redirects": "true", "ipv4AclIn": "SYN-ACL", "ipv6LinkLocal": "fe80::1",
                 "ipv6NdSuppressRa": "true"},
}


def eth_have(parent, nv):
    have = copy.deepcopy(h.build_have(parent))
    base = have[0]["interfaces"][0]["nvPairs"]
    if parent == h.ROUTED and "ospf" not in nv:
        base["ospf"] = "false"          # the harness's routed base enables OSPF; other groups start from it off
    base.update(nv)
    return have


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("group", sorted(ROUTED_GROUPS))
def test_leaf_reset_of_a_routed_port_drops_every_group_with_one_write(state, group):
    _r0, calls0 = role_reset_run(state, eth_have(h.ROUTED, {}), "leaf")
    result, calls = role_reset_run(state, eth_have(h.ROUTED, ROUTED_GROUPS[group]), "leaf")
    assert not result.get("failed"), result.get("msg")
    assert reset_policies(calls)[0]["policy"] == h.TRUNK
    assert nvpairs_of_reset(calls) == nvpairs_of_reset(calls0)      # nothing of the group reaches int_trunk_host
    assert [(c["method"], c["path"]) for c in calls] == [(c["method"], c["path"]) for c in calls0]
    assert KEY not in str(calls) and KEY not in str(result)


@pytest.mark.parametrize("state", STATES)
def test_leaf_reset_keeps_the_destination_reset_for_fields_both_parents_register(state):
    result, calls = role_reset_run(state, eth_have(h.ROUTED, {"lldpReceive": "true", "queuingStats": "true"}), "leaf")
    assert not result.get("failed"), result.get("msg")
    sent = nvpairs_of_reset(calls)
    assert sent["lldpReceive"] == reset_wire(h.TRUNK, "lldpReceive")
    assert sent["queuingStats"] == reset_wire(h.TRUNK, "queuingStats")


@pytest.mark.parametrize("state", STATES)
def test_second_leaf_run_over_the_reset_is_a_noop(state):
    _r1, calls1 = role_reset_run(state, eth_have(h.ROUTED, ROUTED_GROUPS["ospf_auth_md5"]), "leaf")
    have = copy.deepcopy(reset_policies(calls1))
    have[0]["interfaces"][0].update(interfaceType="INTERFACE_ETHERNET", fabricName=h.FABRIC)
    result, calls = role_reset_run(state, have, "leaf")
    assert not result.get("failed") and result["changed"] is False and h.writes(calls) == [], result.get("msg")


# ------------------------------------------------------------------ still refused (same parent, inline parents)
@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("group, text", [
    ("eigrp_passive", "eigrp_ipv4_passive (eigrpIpv4Passive) on %s [%s], parent int_routed_host"),
])
def test_border_same_parent_refusals_are_unchanged(state, group, text):
    result, calls = role_reset_run(state, eth_have(h.ROUTED, ROUTED_GROUPS[group]), "border")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    assert (text % (h.IF_A, h.SERIAL) if "%s" in text else text) in result["msg"]
    assert KEY not in result["msg"]


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("parent, nv, field", [
    (h.TRUNK, {"aclFilter": "SYN-ACL"}, "acl_filter (aclFilter)"),
    (h.TRUNK, {"flowcontrolReceive": "on"}, "flowcontrol_receive (flowcontrolReceive)"),
    (h.TRUNK, {"spanningTreePortType": "network", "GUARD_MODE": "root"}, "guard_mode (GUARD_MODE)"),
    (h.ACCESS, {"aclFilter": "SYN-ACL"}, "acl_filter (aclFilter)"),
    (h.ACCESS, {"spanningTreePortType": "network"}, "spanning_tree_port_type (spanningTreePortType)"),
])
def test_border_transition_from_an_inline_parent_sends_the_routed_default(state, parent, nv, field):
    """P2: the controller negates the inline lines for this transition (cleared_on_change_to); the reset is the ordinary
    routed default and carries none of the source-only keys. test_binding_role_resets.py has the full matrix."""
    result, calls = role_reset_run(state, eth_have(parent, nv), "border")
    assert not result.get("failed"), result.get("msg")
    assert reset_policies(calls)[0]["policy"] == h.ROUTED
    assert not any(k in nvpairs_of_reset(calls) for k in nv), field


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("group", ["arp_bfd", "dampening", "pim", "eigrp_routing", "macsec", "rt1_five", "ospf_base",
                                   "ospf_active"])
def test_border_same_parent_resets_with_verified_wires(state, group):
    result, calls = role_reset_run(state, eth_have(h.ROUTED, ROUTED_GROUPS[group]), "border")
    assert not result.get("failed"), result.get("msg")
    sent = nvpairs_of_reset(calls)
    assert reset_policies(calls)[0]["policy"] == h.ROUTED
    for nvpair in ROUTED_GROUPS[group]:
        if nvpair == "ospfTag":
            assert nvpair not in sent        # D-3: inert under the final gate, kept stored, never sent
            continue
        if ROUTED_GROUPS[group][nvpair] == reset_wire(h.ROUTED, nvpair):
            continue                    # already the neutral value (e.g. area 0.0.0.0): nothing to withdraw
        assert sent.get(nvpair) == reset_wire(h.ROUTED, nvpair), nvpair


# ====================================================================================================
# Formerly test_gie_rt1_policy_change_drop.py
# RT-1: a routed Ethernet whose redirects, inbound ACL, IPv6 link-local or ND suppress-ra is configured can be reset
# to the leaf role default (int_routed_host -> int_trunk_host) in one step.
#
# int_routed_host realizes these five fields only in child policies created with entity and source = the interface,
# and its delete() removes every such child when the policy is replaced (installed template body 6d37ea6a). Their rows
# declare dropped_on_policy_change, so the reset proceeds without writing them into int_trunk_host, which does not
# declare them. Every other source-only field, the same-policy reset, the OSPF gate and the capability boundary are
# unchanged. Real main() through helpers/binding_harness, with the helpers of the F2 tests. Values are synthetic.
# ====================================================================================================
DROPPED = {
    "ipv4Redirects": ("disable_ipv4_redirects", "true"),
    "ipv6Redirects": ("disable_ipv6_redirects", "true"),
    "ipv4AclIn": ("ipv4_acl_in", "SYNTHETIC-ACL"),
    "ipv6LinkLocal": ("ipv6_link_local", "fe80::1"),
    "ipv6NdSuppressRa": ("ipv6_nd_suppress_ra", "true"),
}


def routed_have(**nv):
    have = default_have("border")              # int_routed_host as this module writes it
    have[0]["interfaces"][0]["nvPairs"].update(nv)
    return have


# ------------------------------------------------------------------ the five fields leave with the source parent
@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("nvpair", sorted(DROPPED))
def test_marked_field_does_not_block_the_reset_and_is_never_written(state, nvpair):
    result, calls = role_reset_run(state, routed_have(**{nvpair: DROPPED[nvpair][1]}), "leaf")
    assert not result.get("failed"), result.get("msg")
    assert len(h.split_calls(calls)["updates"]) == 1
    assert reset_policies(calls)[0]["policy"] == h.TRUNK
    assert nvpair not in nvpairs_of_reset(calls)


@pytest.mark.parametrize("state", STATES)
def test_all_five_together_reset_in_one_write_identical_to_the_unconfigured_port(state):
    _r0, calls0 = role_reset_run(state, routed_have(), "leaf")
    result, calls = role_reset_run(state, routed_have(**{k: v[1] for k, v in DROPPED.items()}), "leaf")
    assert not result.get("failed"), result.get("msg")
    assert h.split_calls(calls)["updates"] and nvpairs_of_reset(calls) == nvpairs_of_reset(calls0)
    assert [(c["method"], c["path"]) for c in calls] == [(c["method"], c["path"]) for c in calls0]


@pytest.mark.parametrize("state", STATES)
def test_second_run_over_the_reset_it_wrote_is_a_noop_routed_retire(state):
    _r1, calls1 = role_reset_run(state, routed_have(**{k: v[1] for k, v in DROPPED.items()}), "leaf")
    result, calls = role_reset_run(state, as_have(calls1), "leaf")
    assert not result.get("failed") and result["changed"] is False and h.writes(calls) == [], result.get("msg")


# ------------------------------------------------------------------ boundaries kept
@pytest.mark.parametrize("state", STATES)
def test_a_row_without_the_marker_still_refuses_and_names_only_itself(state):
    """The refusal stays for a binding whose parent is not declared: simulated on one int_routed_host row by
    removing its marker for the duration of the test."""
    have = routed_have(eigrpIpv4Passive="true", **{k: v[1] for k, v in DROPPED.items()})
    with patch.dict(table.resolve_by_nvpair(h.ROUTED, "eigrpIpv4Passive"), {"dropped_on_policy_change": False}):
        result, calls = role_reset_run(state, have, "leaf")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    msg = result["msg"]
    assert "eigrp_ipv4_passive (eigrpIpv4Passive) on %s [%s], int_routed_host -> int_trunk_host" % (h.IF_A, h.SERIAL) in msg
    assert NO_WITHDRAWAL in msg
    for nvpair, (field, value) in DROPPED.items():
        assert "%s (%s)" % (field, nvpair) not in msg
        assert value not in msg


@pytest.mark.parametrize("state", STATES)
def test_ospf_active_on_the_same_parent_is_reset_with_the_acl_in_one_write(state):
    """border: the parent stays int_routed_host; the reset sends ospf "false" (the tag is inert under that final gate,
    D-3) together with the ACL's verified reset."""
    have = routed_have(ospf="true", ospfTag="SYNTHETIC-TAG", ipv4AclIn="SYNTHETIC-ACL")
    result, calls = role_reset_run(state, have, "border")
    assert not result.get("failed"), result.get("msg")
    sent = nvpairs_of_reset(calls)
    assert sent["ospf"] == "false" and "ospfTag" not in sent
    assert sent["ipv4AclIn"] == reset_wire(h.ROUTED, "ipv4AclIn")


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("nvpair", ["ipv4AclIn", "ipv6LinkLocal", "ipv6NdSuppressRa"])
def test_same_policy_reset_still_sends_the_verified_reset(state, nvpair):
    """border: the role default IS int_routed_host. The marker is not a reset: the row's own reset_wire is sent."""
    result, calls = role_reset_run(state, routed_have(**{nvpair: DROPPED[nvpair][1]}), "border")
    assert not result.get("failed"), result.get("msg")
    assert reset_policies(calls)[0]["policy"] == h.ROUTED
    assert nvpairs_of_reset(calls)[nvpair] == reset_wire(h.ROUTED, nvpair)


@pytest.mark.parametrize("state", STATES)
def test_capability_disabled_keeps_the_published_behaviour(state):
    result, calls = role_reset_run(state, routed_have(**{k: v[1] for k, v in DROPPED.items()}), "leaf", patch_version=None)
    assert not result.get("failed"), result.get("msg")
    for nvpair in DROPPED:
        assert all(nvpair not in p["interfaces"][0]["nvPairs"] for p in reset_policies(calls))


@pytest.mark.parametrize("state", STATES)
def test_border_policy_change_from_trunk_uses_the_inline_declaration_not_the_child_marker(state):
    """int_trunk_host is not a child-policy parent (no dropped_on_policy_change); its aclFilter leaves through the
    destination's compliance (cleared_on_change_to, P2), so the reset is the ordinary routed default."""
    assert not table.resolve_by_nvpair(h.TRUNK, "aclFilter").get("dropped_on_policy_change")
    have = copy.deepcopy(h.build_have(h.TRUNK, acl_filter="SYNTHETIC-ACL"))
    result, calls = role_reset_run(state, have, "border")
    assert not result.get("failed"), result.get("msg")
    assert reset_policies(calls)[0]["policy"] == h.ROUTED and "aclFilter" not in nvpairs_of_reset(calls)


# ------------------------------------------------------------------ registry: exactly these rows, and the generator gate
def test_every_int_routed_host_row_and_no_other_carries_the_marker():
    marked = sorted((r["parent_template"], r["parent_nvpair"]) for r in table.BINDING_TABLE if r.get("dropped_on_policy_change"))
    routed = sorted((r["parent_template"], r["parent_nvpair"]) for r in table.BINDING_TABLE if r["parent_template"] == h.ROUTED)
    assert marked == routed and len(routed) == 59   # + 3 SMU 017 routed rows (slice 0b_37)
    assert set(("int_routed_host", n) for n in DROPPED) <= set(marked)
    assert all(r["dropped_on_policy_change"] is True for r in table.BINDING_TABLE if r.get("dropped_on_policy_change"))


def _generator():
    # tests/unit/modules/dcnm/dcnm_interface -> collection root
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir, os.pardir, os.pardir))
    spec = importlib.util.spec_from_file_location("gie_gen", os.path.join(root, "tools", "gie_generate_binding_table.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _row(**over):
    row = {"parent_template": "int_routed_host", "parent_nvpair": "ipv4AclIn", "profile_key": "ipv4_acl_in",
           "applicable_interface_type": "eth", "applicable_mode": "routed", "type": "string", "string_compare": "exact",
           "presence_model": "two_axis", "emit_when": "explicit_only", "mechanism": "passthrough",
           "min_ndfc_version": "12.6.0.267", "parent_resolution": "desired_parent", "reset_wire": ""}
    row.update(over)
    return row


def test_generator_declares_only_the_child_policy_parent():
    assert _generator().POLICY_CHANGE_DROPS_CHILDREN == {"int_routed_host"}
    _generator()._check_registry_schema(_row(), ("int_routed_host", "ipv4AclIn"))


def test_generator_accepts_a_row_that_repeats_the_computed_marker():
    _generator()._check_registry_schema(_row(dropped_on_policy_change=True), ("int_routed_host", "ipv4AclIn"))


@pytest.mark.parametrize("bad", [
    dict(dropped_on_policy_change="true"),
    dict(dropped_on_policy_change=False),
    dict(dropped_on_policy_change=True, parent_template="int_trunk_host", parent_nvpair="aclFilter",
         profile_key="acl_filter", applicable_mode="trunk"),
])
def test_generator_refuses_a_marker_that_differs_from_the_parent(bad):
    with pytest.raises(ValueError) as err:
        _generator()._check_registry_schema(_row(**bad), (bad.get("parent_template", "int_routed_host"), "x"))
    assert "a row may only repeat the computed value" in str(err.value)
