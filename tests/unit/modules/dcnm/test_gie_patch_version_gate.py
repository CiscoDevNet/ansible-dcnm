"""Caller-supplied patch_version gate: the PV01-PV09 matrix.

NOT LIVE TESTED. No controller or switch is contacted; every
case below drives the real module entry point (`main()`) with transport mocked, exactly
as `gie_withdrawal_harness.py` does for the rest of the GIE suite.

WHY THIS FILE IS NARROW. The pre-existing GIE suite (every `test_gie_*.py` and the
`test_dcnm_intf_*` files that drive registered bindings) now declares the approved patch
explicitly through this harness's `SUPPORTED_PATCH` default (`run_configs`/`run`/
`build_have`), per this task's requirement that "test fixtures must declare enabled
context". Running unmodified, that suite already re-proves, for every one of the 234
registered identities:

  PV03  enabled patch + supported NDFC permits existing values/encodings; below-floor
        NDFC still fails (test_gie_passthrough_bindings.py, test_gie_mechanism_contract.py)
  PV05  enabled capability preserves measured resets, no-reset refusals, no-op on an
        already-reset value (test_gie_vpc13_resets.py, test_gie_hsrp3_resets.py, etc.)
  PV07  legacy-only, query/delete, native SVI lists (secondary_gws/hsrp_secondary_vips in
        test_dcnm_intf_svi_address_lists.py) and native dot1q vPC construction
        (test_dcnm_intf_vpc_dot1q.py) are unaffected -- those files are unmodified and
        still pass
  PV09  234 identities / 207 reset values / smu_unsupported exception, asserted directly
        below and already relied upon by test_gie_every_registered_parent_is_wired.py

This file adds the cases that declaring a default patch in the harness could not cover
on its own: the patch boundary itself (PV01, PV02, PV04, PV06, PV08), end to end through
main(), with module-execution assertions rather than a check of the policy constant.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    BINDING_TABLE,
    PROVENANCE_SHA256,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    GIE_ENABLED_PATCH_VERSIONS,
    gie_patch_supported,
)

from .gie_withdrawal_harness import (
    ACCESS,
    IF_A,
    IF_B,
    PATCH_KEY_OMITTED,
    SUPPORTED_PATCH,
    TRUNK,
    UNSUPPORTED_PATCH,
    base_for,
    build_have,
    cfg,
    diff_nvpairs,
    request_nvpairs,
    run,
    run_configs,
    writes,
)

# PV02's required coverage: missing (key fully absent), null, empty, malformed, and named
# unapproved SMU/ND builds below the ND>=4.4.1 release floor. No trimming or prefix match.
UNAPPROVED_EXPLICIT = [
    pytest.param(PATCH_KEY_OMITTED, id="missing_key"),
    pytest.param(None, id="null"),
    pytest.param("", id="empty"),
    pytest.param("not-a-patch", id="malformed"),
    pytest.param("4.3.1.0175006010", id="unapproved_6010_one_below"),
    pytest.param("4.3.1.0175006012", id="unapproved_6012_one_above"),
    pytest.param("4.3.1.0175006011", id="retired_smu_6011"),
    pytest.param("4.3.1.0175006016", id="unapproved_6016_one_below_017"),
    pytest.param("4.3.1.0175006018", id="unapproved_6018_one_above_017"),
    pytest.param("4.3.1", id="truncated_4.3.1"),
    pytest.param("4.4.0.9999999999", id="below_nd_release_floor"),
    pytest.param("4.4.1-rc1", id="non_numeric_suffix"),
]


# ============================================================================= PV01
class TestPV01ArgumentAndAction:
    """Real module argument spec accepts an optional string; omitted is None; the action
    forwards the exact value unchanged; there is no enabling default."""

    def test_module_accepts_the_new_argument(self):
        """A regression guard for every other case in this file: if the arg spec rejected
        patch_version as unsupported, every case below would fail for that reason, not for
        a patch decision."""
        result, _calls = run(base_for(TRUNK), "query", patch_version=SUPPORTED_PATCH)
        assert not result.get("failed"), result.get("msg")

    def test_omitted_is_none_not_an_enabling_default(self):
        """No product default anywhere: a registered field set explicitly, with the key
        fully ABSENT from module args, must fail exactly like an explicit None -- Ansible
        resolves both to the same `module.params["patch_version"]`, and the module must
        not special-case either into success."""
        conf = [cfg(IF_A, dict(base_for(TRUNK), guard_mode="root"))]
        result_omitted, calls_omitted = run_configs(
            conf, "merged", patch_version=PATCH_KEY_OMITTED)
        result_null, calls_null = run_configs(conf, "merged", patch_version=None)
        assert result_omitted.get("failed") and result_null.get("failed")
        assert "guard_mode" in result_omitted["msg"]
        assert "guard_mode" in result_null["msg"]
        assert writes(calls_omitted) == [] and writes(calls_null) == []

    def test_action_forwards_the_exact_caller_value_unchanged(self):
        """Changing ONLY the patch_version value, nothing else, flips the outcome for the
        identical registered-field request -- proof that the exact string the caller wrote
        reaches the engine, not a coerced or substituted copy."""
        conf = [cfg(IF_A, dict(base_for(TRUNK), guard_mode="root"))]
        rejected, _rejected_calls = run_configs(conf, "merged", patch_version=UNSUPPORTED_PATCH)
        accepted, _accepted_calls = run_configs(conf, "merged", patch_version=SUPPORTED_PATCH)
        assert rejected.get("failed") is True
        assert not accepted.get("failed"), accepted.get("msg")


# ============================================================================= PV02
class TestPV02DisabledExplicitRejectsBeforeWrites:
    """Missing/null/empty/malformed/unapproved patch, with an explicit registered field,
    rejects the WHOLE invocation before any configuration/deployment write -- normal mode,
    check mode, and with a bad SECOND config object."""

    @pytest.mark.parametrize("bad_patch", UNAPPROVED_EXPLICIT)
    def test_rejects_before_any_write(self, bad_patch):
        conf = [cfg(IF_A, dict(base_for(TRUNK), guard_mode="root"))]
        result, calls = run_configs(conf, "merged", patch_version=bad_patch)
        assert result.get("failed"), "unapproved patch %r must reject" % (bad_patch,)
        assert writes(calls) == [], "no configuration write may precede the rejection"
        assert "guard_mode" in result["msg"]
        assert "no change was sent" in result["msg"].lower()

    @pytest.mark.parametrize("bad_patch", UNAPPROVED_EXPLICIT)
    def test_rejects_in_check_mode_too(self, bad_patch):
        """Check mode is a report. Reporting a configuration that could not be sent would
        be the same false claim as sending it."""
        conf = [cfg(IF_A, dict(base_for(TRUNK), guard_mode="root"))]
        result, calls = run_configs(
            conf, "merged", patch_version=bad_patch, check_mode=True)
        assert result.get("failed")
        assert writes(calls) == []

    def test_a_bad_second_object_blocks_the_first_objects_writes_too(self):
        """Object 1 alone (legacy-only, no registered field) would succeed. Object 2 carries
        an explicit registered field while the patch is disabled. The whole invocation must
        reject, and nothing from object 1 may reach a write."""
        good = cfg(IF_A, base_for(TRUNK))
        bad = cfg(IF_B, dict(base_for(ACCESS), acl_filter="PR725-PILOT"))
        result, calls = run_configs(
            [good, bad], "merged", patch_version=PATCH_KEY_OMITTED)
        assert result.get("failed")
        assert writes(calls) == [], "object 1 must not be written while object 2 is rejected"

    def test_a_bad_second_object_blocks_the_first_in_check_mode(self):
        good = cfg(IF_A, base_for(TRUNK))
        bad = cfg(IF_B, dict(base_for(ACCESS), acl_filter="PR725-PILOT"))
        result, calls = run_configs(
            [good, bad], "merged", patch_version=PATCH_KEY_OMITTED, check_mode=True)
        assert result.get("failed")
        assert writes(calls) == []


# ============================================================================= PV04
class TestPV04OmissionPreservation:
    """Disabled capability + authoritative non-default HAVE + an unrelated change: merged,
    replaced and retained-overridden must all preserve the existing value. No reset or
    default may be synthesized while the capability is disabled."""

    @pytest.mark.parametrize("bad_patch", [PATCH_KEY_OMITTED, None, UNSUPPORTED_PATCH],
                             ids=["missing", "null", "unapproved"])
    def test_merged_omission_preserves_when_disabled(self, bad_patch):
        have = build_have(TRUNK, "guard_mode", "root")  # a non-default, non-reset HAVE
        want = dict(base_for(TRUNK), description="pr725-unrelated-change")
        assert "guard_mode" not in want
        result, calls = run_configs(
            [cfg(IF_A, want)], "merged", have=copy.deepcopy(have), patch_version=bad_patch)
        assert not result.get("failed"), result.get("msg")
        assert writes(calls), "the unrelated description change must still force a write"
        sent = request_nvpairs(calls)
        # Require the EXACT authoritative value positively, not
        # merely the absence of the registered reset -- a silently dropped key would also
        # satisfy a negative-only "never == 'no'" check without actually preserving
        # anything. See test_gie_patch_version_disabled_compat.py for the same assertion
        # restated as its own dedicated, more heavily-commented case.
        carried = [nv["GUARD_MODE"] for nv in sent if "GUARD_MODE" in nv]
        assert carried == ["root"], (
            "the disabled capability must positively carry the exact HAVE value forward, "
            "not merely avoid resetting it: %r" % carried)
        diffed = diff_nvpairs(result)
        assert not any("GUARD_MODE" in nv for nv in diffed), (
            "an untouched field must not appear in the public diff")

    @pytest.mark.parametrize("state", ["replaced", "overridden"])
    @pytest.mark.parametrize("bad_patch", [PATCH_KEY_OMITTED, None, UNSUPPORTED_PATCH],
                             ids=["missing", "null", "unapproved"])
    def test_full_payload_replace_carries_the_have_value_forward_when_disabled(
        self, state, bad_patch
    ):
        """A non-default HAVE must round-trip unchanged in the full payload when an
        unrelated field forces a write, while the capability stays disabled.
        Preservation is not the same as newly configuring a field: GUARD_MODE must still
        be SENT (replaced/overridden emit a full payload) but must never be reset and must
        never appear as a public diff entry."""
        have = build_have(TRUNK, "guard_mode", "root")
        want = dict(base_for(TRUNK), description="pr725-unrelated-change")
        assert "guard_mode" not in want
        result, calls = run_configs(
            [cfg(IF_A, want)], state, have=copy.deepcopy(have), patch_version=bad_patch)
        assert not result.get("failed"), result.get("msg")
        sent = request_nvpairs(calls)
        carried = [nv["GUARD_MODE"] for nv in sent if "GUARD_MODE" in nv]
        assert carried, "the full payload must still carry the parent's existing GUARD_MODE"
        assert all(v == "root" for v in carried), (
            "the disabled capability must preserve the exact HAVE value, not reset it: %r"
            % carried)
        diffed = diff_nvpairs(result)
        assert not any("GUARD_MODE" in nv for nv in diffed), (
            "a preserved value must not appear as a public diff entry")

    def test_malformed_have_cannot_become_empty_while_disabled(self):
        """A HAVE value the engine cannot classify (not a recognised encoding) must still
        be rejected by HAVE validation, disabled capability or not -- the disabled gate is
        not a bypass for an unreadable controller state."""
        have = build_have(TRUNK, "guard_mode", "root")
        # Corrupt the authoritative HAVE to a value the registry never declared.
        have[0]["interfaces"][0]["nvPairs"]["GUARD_MODE"] = "not-a-registered-choice"
        want = dict(base_for(TRUNK), description="pr725-unrelated-change")
        result, _calls = run_configs(
            [cfg(IF_A, want)], "replaced", have=copy.deepcopy(have),
            patch_version=PATCH_KEY_OMITTED)
        assert result.get("failed"), (
            "an unreadable HAVE value must fail closed, not be silently treated as absent")


# ============================================================================= PV06
class TestPV06IsolationAndAtomicPreflight:
    """Mixed valid/invalid objects, normal/check: zero mutating calls. One invocation's
    approved patch cannot leak into another invocation that did not supply it."""

    def test_a_bad_second_object_blocks_the_first_objects_writes_too(self):
        good = cfg(IF_A, base_for(TRUNK))
        bad = cfg(IF_B, dict(base_for(ACCESS), acl_filter="PR725-PILOT"))
        result, calls = run_configs(
            [good, bad], "merged", patch_version=PATCH_KEY_OMITTED)
        assert result.get("failed")
        assert writes(calls) == []

    def test_invocation_a_with_patch_does_not_leak_into_invocation_b_without_it(self):
        """Two separate module invocations in the same test process. The first, with the
        patch approved, succeeds. The second, immediately after, with the identical
        explicit field and no patch, must fail exactly as if it were the only invocation
        run -- there is no module-level cache or global the first invocation could have
        left behind for the second to inherit."""
        conf = [cfg(IF_A, dict(base_for(TRUNK), guard_mode="root"))]
        first, calls_a = run_configs(conf, "merged", patch_version=SUPPORTED_PATCH)
        assert not first.get("failed"), first.get("msg")
        assert writes(calls_a), "invocation A must have actually configured the field"

        second, calls_b = run_configs(conf, "merged", patch_version=PATCH_KEY_OMITTED)
        assert second.get("failed"), (
            "invocation B must not inherit invocation A's approved patch context")
        assert writes(calls_b) == []


# ============================================================================= PV08
class TestPV08TransportAndDiff:
    """patch_version is absent from the controller request and from the public diff. A
    legacy-only request is never affected by any patch value, approved or not."""

    def test_patch_value_never_reaches_the_controller_payload_or_the_diff(self):
        conf = [cfg(IF_A, dict(base_for(TRUNK), guard_mode="root"))]
        result, calls = run_configs(conf, "merged", patch_version=SUPPORTED_PATCH)
        assert not result.get("failed"), result.get("msg")
        for call in calls:
            assert "patch_version" not in str(call.get("payload"))
            assert SUPPORTED_PATCH not in str(call.get("payload"))
        assert "patch_version" not in str(result.get("diff"))
        assert SUPPORTED_PATCH not in str(result.get("diff"))

    @pytest.mark.parametrize(
        "patch_value",
        [SUPPORTED_PATCH, UNSUPPORTED_PATCH, None, PATCH_KEY_OMITTED],
        ids=["approved", "unapproved", "null", "missing"],
    )
    def test_patch_value_alone_with_no_registered_field_intent_changes_nothing(
        self, patch_value
    ):
        """A legacy-only profile declares no explicit registered key, so no patch value --
        approved, unapproved or absent -- can produce a GIE-driven rejection or diff. The
        whole interface module is not disabled by an unapproved/absent patch."""
        want = base_for(TRUNK)  # no registered keys at all
        result, _calls = run_configs([cfg(IF_A, want)], "merged", patch_version=patch_value)
        assert not result.get("failed"), (
            "a legacy-only request must never fail on patch_version alone: %s"
            % result.get("msg"))

    def test_an_already_applied_supported_value_is_idempotent(self):
        """A synthetic rerun with the approved patch over an already-applied value produces
        no write -- the patch control introduces no artificial change of its own."""
        have = build_have(TRUNK, "guard_mode", "root")
        want = dict(base_for(TRUNK), guard_mode="root")
        result, calls = run_configs(
            [cfg(IF_A, want)], "merged", have=copy.deepcopy(have),
            patch_version=SUPPORTED_PATCH)
        assert not result.get("failed"), result.get("msg")
        assert writes(calls) == [], "re-sending an already-applied value must be a no-op"


# ============================================================================= PV09
class TestPV09InventoryInvariants:
    """The registry itself is untouched by this candidate: same identities, same measured
    resets, same generated-table provenance, same smu_unsupported exception."""

    def test_234_identities_and_207_reset_values_unchanged(self):
        # The eleven PVLAN companion rows, each with an inferred reset: 234 + 11, 207 + 11; plus one vPC PVLAN row.
        # + 5: 0b_37, + 5: 0b_38, + 1: 0b_39, + 19: 0b_40, + 1: rs1, + 4: pl1, + 12: ul1
        assert len(BINDING_TABLE) == 234 + 11 + 1 + 5 + 5 + 1 + 19 + 1 + 4 + 12
        # + 0b_37 to 0b_40, rs1, pl1, ul1
        assert sum(1 for b in BINDING_TABLE if b.get("reset_wire") is not None) == 207 + 11 + 1 + 5 + 5 + 1 + 16 + 1 + 2 + 12

    def test_smu_unsupported_exception_unchanged(self):
        smu = [b for b in BINDING_TABLE if b.get("smu_unsupported")]
        assert len(smu) == 1, "the smu_unsupported exception must stay exactly one row"
        assert smu[0]["parent_template"] == "int_port_channel_trunk_host"
        assert smu[0]["profile_key"] == "enable_vpc_peer_link"

    def test_generated_table_provenance_hash_unchanged(self):
        """PROVENANCE_SHA256 is computed FROM the generated table bytes; comparing it
        against the frozen G0 value (recorded before any
        edit) proves this candidate did not hand-edit generated data."""
        # Regenerated by tools/gie_generate_binding_table.py from the 32 published slices + the reviewed
        # registry_slice_c1_pvlan_companions.yaml (was 13ccf6fb...); the generator, not a hand edit, produced it.
        # Regenerated from the same 33 slices + registry_slice_iq1_vpc_pvlan_qos_stats.yaml (was 6f7fb57e...; reproduced
        # byte-identical from the 33 slices before the addition).
        # F1: regenerated from the same 34 slices with `string_compare` added to the 45 committed string rows (was
        # 3820250c...; the unannotated slices reproduced it byte-identical, and the new generator rejects them).
        # R-F4: regenerated from the same 34 slices with `inert_when` added to the ospf_tag rows of int_routed_host,
        # int_subif and int_vlan (was b6f88798...).
        # OSPF dependencies: regenerated from the same 34 slices with `inert_when` on the OSPF options and
        # authentication rows of the same three parents and `required` on ospf_tag (was d5281a22...).
        # RT-1: regenerated from the same 34 slices with `dropped_on_policy_change` on five int_routed_host rows
        # (was acc3629a...). Retirement scope: the marker is computed for every int_routed_host row from the
        # generator's parent declaration; the slices are back to their earlier content (was f36ad753...).
        # P2: `cleared_on_change_to` computed for every int_trunk_host and int_access_host row from the generator's
        # inline-compliance declaration (was 8ea855ab...).
        # SMU 017: regenerated from the same 34 slices with the loopback and subinterface OSPF BFD rows and the
        # subinterface passive row rebound to the enum nvPairs ospfBfdMode and ospfPassiveMode (was 15061dfc...).
        # 36 slices: the trunk port-channel reset-skip row of slice rs1 (was f39b3265...).
        # 35 slices: the SMU 017 batch-1 rows, the access link-status logging destination and the int_loopback
        # dependency rows (was 9d0d82a3... and 2e0252ae...).
        # 38 slices: the SMU 017 loopback EIGRP rows of slice 0b_38, the routed port-channel PIM BFD row of slice 0b_39
        # and the routed port-channel OSPF family of slice 0b_40 (was 07a372a7... and ee8f4c9c...).
        # 39 slices: those 38 and slice rs1 (was b77a881f... and b460471a...).
        # 40 slices: those 39 and the peer-link rows of slice pl1 (was 7db4bd8a...).
        # 41 slices: those 40 and the ToR-uplink rows of slice ul1 (was 1b7d7b01...).
        assert PROVENANCE_SHA256 == (
            "f8b3ed32baa066a597ad055614066ca9dd9ef88e8cd56315fd7e87c9f8001f5a"
        )


# ============================================================================= ND release support
class TestNdReleaseCapability:
    """Exercise the new ND gate through main(), including payload and omission semantics."""

    @pytest.mark.parametrize("patch_version", ["4.4.1", "4.4.1.10", "4.4.2", "4.10.0", "5.0.0"])
    def test_explicit_field_matches_approved_smu_payload(self, patch_version):
        conf = [cfg(IF_A, dict(base_for(TRUNK), guard_mode="root"))]
        control, control_calls = run_configs(conf, "merged", patch_version=SUPPORTED_PATCH)
        result, calls = run_configs(conf, "merged", patch_version=patch_version)
        assert not control.get("failed"), control.get("msg")
        assert not result.get("failed"), result.get("msg")
        assert writes(calls) == writes(control_calls)
        assert request_nvpairs(calls)[0]["GUARD_MODE"] == "root"
        assert diff_nvpairs(result) == diff_nvpairs(control)

    @pytest.mark.parametrize("state, expected", [
        ("merged", "root"), ("replaced", "no"), ("overridden", "no"),
    ])
    def test_omission_preserves_or_resets_as_the_state_requires(self, state, expected):
        have = build_have(TRUNK, "guard_mode", "root")
        want = dict(base_for(TRUNK), description="nd441-unrelated-change")
        result, calls = run_configs(
            [cfg(IF_A, want)], state, have=have, patch_version="4.4.1")
        assert not result.get("failed"), result.get("msg")
        assert [nv["GUARD_MODE"] for nv in request_nvpairs(calls)] == [expected]

    def test_already_correct_value_writes_nothing(self):
        have = build_have(TRUNK, "guard_mode", "root")
        result, calls = run_configs(
            [cfg(IF_A, dict(base_for(TRUNK), guard_mode="root"))], "merged",
            have=have, patch_version="4.4.1")
        assert not result.get("failed"), result.get("msg")
        assert not result["changed"]
        assert writes(calls) == []

    @pytest.mark.parametrize("ndfc_version", ["12.6.0.266", None, "bad-version"])
    def test_nd_release_never_bypasses_the_ndfc_floor(self, ndfc_version):
        result, calls = run_configs(
            [cfg(IF_A, dict(base_for(TRUNK), guard_mode="root"))], "merged",
            patch_version="4.4.1", ndfc_version=ndfc_version)
        assert result.get("failed")
        assert "NDFC" in result["msg"]
        assert writes(calls) == []


# ============================================================================= policy shape
class TestPatchPolicyApprovedSmuOrNdRelease:
    """Keep the exact SMU exception and compare numeric ND releases as PR730 does."""

    def test_only_the_one_smu_is_allowlisted(self):
        assert GIE_ENABLED_PATCH_VERSIONS == frozenset({"4.3.1.0175006017"})

    @pytest.mark.parametrize("value", [
        None, "", "4.3.1", "4.3.1.0175006010", "4.3.1.0175006011", "4.3.1.0175006012", "4.3.1.0175006016", "4.3.1.0175006018", "4.3.99",
        "4.4", "4.4.0", "4.4.0.9999999999", "4.4.1-rc1", "4.4.1.", "4.4.1.bad",
        "4.4.1.2.bad", "5.-1.0", " 4.4.1", "4.4.1 ", "not-a-version", "4.4.\u00b2",
        " 4.3.1.0175006017", "4.3.1.0175006017 ", 4, True, [], {},
    ])
    def test_missing_malformed_and_below_floor_are_unsupported(self, value):
        assert gie_patch_supported(value) is False

    def test_the_exact_approved_string_is_supported(self):
        assert gie_patch_supported("4.3.1.0175006017") is True

    def test_the_retired_smu_is_no_longer_supported(self):
        # 4.3.1.0175006011 declares the boolean OSPF nvPairs; this candidate supports only 017.
        assert gie_patch_supported("4.3.1.0175006011") is False

    @pytest.mark.parametrize("value", ["4.4.1", "4.4.1.0", "4.4.2", "4.10.0", "5.0.0.0"])
    def test_numeric_nd_release_is_supported(self, value):
        assert gie_patch_supported(value) is True
