"""Binding capability gates: caller patch_version, controller version and the published examples."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import ast
import copy
import pytest
import yaml

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import BINDING_TABLE
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import PROVENANCE_SHA256
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_ENABLED_PATCH_VERSIONS
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_patch_supported
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_binding_applicable
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_contribute_nvpairs
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface import DcnmIntf

from .helpers.binding_harness import ACCESS
from .helpers.binding_harness import IF_A
from .helpers.binding_harness import IF_B
from .helpers.binding_harness import PATCH_KEY_OMITTED
from .helpers.binding_harness import SUPPORTED_PATCH
from .helpers.binding_harness import TRUNK
from .helpers.binding_harness import UNSUPPORTED_PATCH
from .helpers.binding_harness import base_for
from .helpers.binding_harness import build_have
from .helpers.binding_harness import cfg
from .helpers.binding_harness import diff_nvpairs
from .helpers.binding_harness import request_nvpairs
from .helpers.binding_harness import run
from .helpers.binding_harness import run_configs
from .helpers.binding_harness import writes
from .helpers.binding_harness import PC_TRUNK
from .helpers.binding_harness import SVI
from .helpers.binding_harness import VPC_DOT1Q
from .helpers.binding_harness import cfg_for


# ====================================================================================================
# Formerly test_gie_patch_version_gate.py
# Caller-supplied patch_version gate: the PV01-PV09 matrix.
#
# NOT LIVE TESTED. No controller or switch is contacted; every
# case below drives the real module entry point (`main()`) with transport mocked, exactly
# as `helpers/binding_harness.py` does for the rest of the GIE suite.
#
# WHY THIS FILE IS NARROW. The pre-existing GIE suite (every `test_gie_*.py` and the
# `test_dcnm_intf_*` files that drive registered bindings) now declares the approved patch
# explicitly through this harness's `SUPPORTED_PATCH` default (`run_configs`/`run`/
# `build_have`), per this task's requirement that "test fixtures must declare enabled
# context". Running unmodified, that suite already re-proves, for every one of the 234
# registered identities:
#
#   PV03  enabled patch + supported NDFC permits existing values/encodings; below-floor
#         NDFC still fails (test_binding_values.py, test_binding_contracts.py)
#   PV05  enabled capability preserves measured resets, no-reset refusals, no-op on an
#         already-reset value (test_binding_role_resets.py, test_binding_role_resets.py, etc.)
#   PV07  legacy-only, query/delete, native SVI lists (secondary_gws/hsrp_secondary_vips in
#         test_svi_bindings.py) and native dot1q vPC construction
#         (test_mode_dot1q.py) are unaffected -- those files are unmodified and
#         still pass
#   PV09  234 identities / 207 reset values / smu_unsupported exception, asserted directly
#         below and already relied upon by test_binding_contracts.py
#
# This file adds the cases that declaring a default patch in the harness could not cover
# on its own: the patch boundary itself (PV01, PV02, PV04, PV06, PV08), end to end through
# main(), with module-execution assertions rather than a check of the policy constant.
# ====================================================================================================
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
        # anything. See test_binding_versions.py for the same assertion
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
        # + 5: 0b_37, + 5: 0b_38, + 1: 0b_39, + 19: 0b_40, + 1: rs1, + 4: pl1, + 12: ul1, + 2: 0b_41
        assert len(BINDING_TABLE) == 234 + 11 + 1 + 5 + 5 + 1 + 19 + 1 + 4 + 12 + 2
        # + 0b_37 to 0b_41, rs1, pl1, ul1
        assert sum(1 for b in BINDING_TABLE if b.get("reset_wire") is not None) == 207 + 11 + 1 + 5 + 5 + 1 + 16 + 1 + 2 + 12 + 2

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
        # 42 slices: those 41 and the routed port-channel PIM rows of slice 0b_41 (was f8b3ed32...).
        assert PROVENANCE_SHA256 == (
            "e71748972f93babc31c7cab16a583f5df8797e806ef4f91830148facd5b36af1"
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


# ====================================================================================================
# Formerly test_gie_patch_version_disabled_compat.py
# Disabled-context PV07 closeout.
#
# A review found that `test_binding_versions.py`'s PV07 claim leaned on pre-existing
# native/legacy test files that pass unmodified -- but those files run through
# `helpers/binding_harness.run_configs`/`run`, which (since this task) defaults
# `patch_version` to the approved constant. Passing unmodified proves nothing about the
# ABSENT-argument case specifically, because the default quietly supplies an approved one.
#
# Every case below uses `PATCH_KEY_OMITTED` explicitly -- the patch argument is genuinely
# absent from module args, not defaulted by the harness -- and asserts the actual expected
# payload/result, not merely the lack of a failure (a silently dropped field, or a silently
# empty response, would also pass a bare "not failed" check).
#
# NOT LIVE TESTED. No controller or switch is contacted.
# ====================================================================================================
BELOW_NDFC_FLOOR = "12.6.0.266"
SUPPORTED_NDFC = "12.6.0.267"


# ============================================================================= merged
# (strengthens the existing PV04 merged case from test_binding_versions.py, which
# only checked that GUARD_MODE was never reset to "no" -- a check a silently dropped key
# would also pass. This requires the exact preserved value to be present.)
def test_merged_omission_requires_the_exact_have_value_in_the_forced_outgoing_payload():
    have = build_have(TRUNK, "guard_mode", "root")
    want = dict(base_for(TRUNK), description="r2-unrelated-change")
    assert "guard_mode" not in want
    result, calls = run_configs(
        [cfg(IF_A, want)], "merged", have=copy.deepcopy(have),
        patch_version=PATCH_KEY_OMITTED)
    assert not result.get("failed"), result.get("msg")
    assert writes(calls), "the unrelated description change must still force a write"
    sent = request_nvpairs(calls)
    carried = [nv["GUARD_MODE"] for nv in sent if "GUARD_MODE" in nv]
    assert carried == ["root"], (
        "the outgoing payload must carry the EXACT authoritative value, not merely avoid "
        "the registered reset -- a silently dropped key would also satisfy a negative-only "
        "check: %r" % carried)
    assert not any("GUARD_MODE" in nv for nv in diff_nvpairs(result)), (
        "a preserved value must not appear as a public diff entry")


# ============================================================================= native SVI lists
def test_native_svi_secondary_gw_list_update_with_patch_genuinely_absent():
    """secondary_gws is a native list argument, not a registry binding. It must behave
    identically with the patch argument genuinely omitted."""
    profile = dict(
        base_for(SVI), ipv4_addr="192.0.2.1", ipv4_mask_len=24,
        secondary_gws=[{"gateway_ip_address": "198.51.100.254/24"}],
    )
    result, calls = run_configs(
        [cfg_for(SVI, profile)], "merged", have=[], patch_version=PATCH_KEY_OMITTED)
    assert not result.get("failed"), result.get("msg")
    sent = request_nvpairs(calls)
    matching = [nv for nv in sent if "secondaryGws" in nv]
    assert matching, "the native secondary-gateway list must still reach the payload"
    assert matching[0]["secondaryGws"] == (
        '{"secondaryGws":[{"gatewayIpAddress":"198.51.100.254/24"}]}'
    ), matching[0]["secondaryGws"]


def test_native_svi_hsrp_secondary_vip_list_update_with_patch_genuinely_absent():
    profile = dict(
        base_for(SVI), ipv4_addr="192.0.2.1", ipv4_mask_len=24,
        hsrp_secondary_vips=[{"hsrp_secondary_vip": "192.0.2.123"}],
    )
    result, calls = run_configs(
        [cfg_for(SVI, profile)], "merged", have=[], patch_version=PATCH_KEY_OMITTED)
    assert not result.get("failed"), result.get("msg")
    sent = request_nvpairs(calls)
    matching = [nv for nv in sent if "hsrpSecondaryVips" in nv]
    assert matching, "the native HSRP secondary-VIP list must still reach the payload"
    assert matching[0]["hsrpSecondaryVips"] == (
        '{"hsrpSecondaryVips":[{"hsrpSecondaryVip":"192.0.2.123"}]}'
    ), matching[0]["hsrpSecondaryVips"]


# ============================================================================= native dot1q
def test_native_dot1q_vpc_construction_without_any_registered_scalar_and_patch_absent():
    """A dot1q-tunnel vPC built with ONLY native fields -- no acl_filter, no
    spanning_tree_port_type, no disable_lldp_*, nothing the registry governs -- must
    create successfully with the patch argument genuinely absent, and must carry its
    native per-peer values exactly."""
    profile = base_for(VPC_DOT1Q)
    for key in ("acl_filter", "spanning_tree_port_type", "disable_qos_stats",
                "disable_queuing_stats", "disable_lldp_transmit", "disable_lldp_receive"):
        assert key not in profile, (
            "%s is a registered field; this case must stay registry-free" % key)
    result, calls = run_configs(
        [cfg_for(VPC_DOT1Q, profile)], "merged", have=[], patch_version=PATCH_KEY_OMITTED)
    assert not result.get("failed"), result.get("msg")
    sent = request_nvpairs(calls)
    assert sent, "the native dot1q vPC construction must still produce a payload"
    # The harness's paired-switch transport answers with controller peer order reversed
    # from the playbook order (see helpers/binding_harness module docstring), so the exact
    # peer1<->peer2 mapping is asserted elsewhere (test_mode_dot1q.py); here it is
    # enough to prove both native per-peer VLANs reached the payload at all.
    sent_vlans = {
        nv[key] for nv in sent for key in ("PEER1_ACCESS_VLAN", "PEER2_ACCESS_VLAN")
        if key in nv
    }
    assert sent_vlans == {profile["peer1_access_vlan"], profile["peer2_access_vlan"]}, (
        sent_vlans)


# ============================================================================= query
def test_query_with_patch_genuinely_absent_returns_the_authoritative_registered_value():
    """Reading is not permission to change: a registered field already configured on the
    controller must still be reported by state=query with the patch argument absent --
    the gate guards WRITES of an explicit registered field, not reads of an existing one."""
    have = build_have(TRUNK, "guard_mode", "root")
    result, _calls = run_configs(
        [cfg(IF_A, {"mode": "trunk"})], "query", have=have,
        patch_version=PATCH_KEY_OMITTED)
    assert not result.get("failed"), result.get("msg")
    queried = result["diff"][0]["query"]
    assert queried, "query must return the interface"
    nvpairs = queried[0]["interfaces"][0]["nvPairs"]
    assert nvpairs.get("GUARD_MODE") == "root", (
        "query must report the controller's actual registered-field value unchanged, "
        "patch absent or not: %r" % nvpairs.get("GUARD_MODE"))


# ============================================================================= whole-object lifecycle
def test_whole_object_deletion_with_patch_genuinely_absent():
    """Explicit whole-interface deletion (a Port-channel, which really can be removed,
    unlike a physical Ethernet port) must still reach the real delete/deploy calls with
    the patch argument absent -- the gate must not globally veto legacy delete."""
    have = build_have(PC_TRUNK, "guard_mode", "root")
    ifname = have[0]["interfaces"][0]["ifName"]
    result, calls = run_configs(
        [{"name": ifname}], "deleted", have=have, patch_version=PATCH_KEY_OMITTED)
    assert not result.get("failed"), result.get("msg")
    methods_paths = [(c["method"], c["path"]) for c in calls]
    assert any(
        m == "DELETE" and "markdelete" in p for m, p in methods_paths
    ), "whole-object deletion must still reach the real markdelete call: %r" % (methods_paths,)
    assert any(
        m == "POST" and "deploy" in p for m, p in methods_paths
    ), "deletion must still deploy: %r" % (methods_paths,)


def test_overridden_removal_of_an_absent_object_with_patch_genuinely_absent():
    """An interface the operator's config omits entirely under `overridden` must still be
    reset/defaulted -- the gate must not globally veto legacy overridden removal of
    objects the user explicitly left out."""
    have = build_have(TRUNK, "guard_mode", "root")
    result, calls = run_configs(
        [], "overridden", have=have, patch_version=PATCH_KEY_OMITTED)
    assert not result.get("failed"), result.get("msg")
    assert writes(calls), (
        "an out-of-scope interface under overridden must still be reset to default")


# ============================================================================= disabled applicability, full registry
# Representative explicit false/zero/empty values, across every one of the 234 registered
# identities, confirm the disabled-patch gate treats them exactly like any other explicit
# value -- never mistaking a falsy-but-present value for omission.
def _sample_for(binding):
    """A representative explicit value that passes this binding's OWN input-contract
    validation (so a rejection is attributable to the disabled patch gate, not to an
    unrelated range/length/choice check), while still being the falsy/empty/minimal
    value for its type.

    An integer's registered minimum varies per row (1, 50, ...); using a fixed 0 would
    make many rows fail validation before reaching the patch check at all, for a reason
    unrelated to this test. Falling back to the registered minimum (never a smaller,
    invalid value) keeps the sample both minimal and valid.
    """
    if binding["type"] == "boolean":
        return False
    if binding["type"] == "string":
        return "" if not binding.get("valid_values") else sorted(binding["valid_values"])[0]
    if binding["type"] == "enum":
        return sorted(binding["valid_values"])[0]
    if binding["type"] == "integer":
        return binding.get("min_value", 0)
    raise AssertionError("unexpected registered type %r" % binding["type"])


@pytest.mark.parametrize(
    "binding",
    [b for b in BINDING_TABLE if not b.get("smu_unsupported")],
    ids=[
        "%s::%s" % (b["parent_template"], b["profile_key"])
        for b in BINDING_TABLE if not b.get("smu_unsupported")
    ],
)
def test_every_non_smu_unsupported_identity_is_inapplicable_when_patch_is_disabled(binding):
    """Disabled applicability, across all 233 non-smu_unsupported identities (234 minus
    the one permanently-unsupported row, covered separately below): with a supported
    NDFC version and NO approved patch, the binding is never applicable."""
    assert gie_binding_applicable(
        binding["parent_template"], binding["profile_key"], SUPPORTED_NDFC, None
    ) is False


@pytest.mark.parametrize(
    "binding",
    [b for b in BINDING_TABLE if not b.get("smu_unsupported")],
    ids=[
        "%s::%s" % (b["parent_template"], b["profile_key"])
        for b in BINDING_TABLE if not b.get("smu_unsupported")
    ],
)
def test_every_non_smu_unsupported_identity_rejects_a_representative_falsy_explicit_value(
    binding
):
    """A representative explicit false/zero/empty value for EVERY registered identity must
    still be rejected by the disabled patch gate -- never confused with omission by
    truthiness. (An enum's sample is its lexicographically-first valid choice, not a falsy
    sentinel, since an enum has no registry-neutral falsy value of its own; its explicit
    presence is what matters here, not its particular value.)"""
    sample = _sample_for(binding)
    add, err = gie_contribute_nvpairs(
        binding["parent_template"], {binding["profile_key"]: sample}, SUPPORTED_NDFC,
        None,
    )
    assert add is None, (
        "%s::%s with explicit falsy/empty value %r must be rejected, not treated as "
        "omitted" % (binding["parent_template"], binding["profile_key"], sample))
    assert err and "patch_version" in err, err


def test_smu_unsupported_identity_still_rejects_for_its_own_reason_patch_disabled_or_not():
    """The one smu_unsupported row (int_port_channel_trunk_host::enable_vpc_peer_link)
    must keep rejecting for ITS OWN reason -- the installed templates do not declare it --
    whether or not the patch is approved. An approved patch must never be read as
    creating template support the controller does not have."""
    smu_rows = [b for b in BINDING_TABLE if b.get("smu_unsupported")]
    assert len(smu_rows) == 1
    binding = smu_rows[0]
    for patch_value, label in [(None, "disabled"), ("4.3.1.0175006017", "approved"), ("4.4.1", "nd_release")]:
        add, err = gie_contribute_nvpairs(
            binding["parent_template"], {binding["profile_key"]: True}, SUPPORTED_NDFC,
            patch_value,
        )
        assert add is None, "smu_unsupported must still reject with patch %s" % label
        assert err and "not supported by the interface templates installed" in err, (
            "%s (patch %s) -- the rejection reason must stay template support, not the "
            "patch gate" % (err, label))


# ====================================================================================================
# Formerly test_gie_patch_version_public_example_regression.py
# Regression for the published EXAMPLES
# entry itself, not a hand-written restatement of it.
#
# R1 review found that the module's own "Create a dot1q-tunnel vPC" EXAMPLES entry sets two
# registered generic-binding-registry fields (disable_lldp_transmit/disable_lldp_receive)
# without declaring patch_version, so the documented playbook -- replayed as written -- now
# fails before any write. This file parses `DcnmIntf`'s real EXAMPLES string with the stdlib
# AST/YAML parsers, extracts that exact
# entry's config/profile, and drives it through the real module `main()` with transport
# mocked. It fails if the shipped example ever regresses again, in either direction: if the
# example stops requiring the approved patch, or if the approved patch stops making it work.
#
# NOT LIVE TESTED. No controller or switch is contacted.
# ====================================================================================================
def _parse_examples_block():
    """The module's real EXAMPLES string, parsed exactly as PyYAML/Ansible would read it.

    Reading the live attribute off the imported module (not a copy of the source text)
    means this test sees whatever EXAMPLES actually contains at import time -- it cannot
    drift from the shipped documentation by construction.
    """
    with open(dcnm_interface.__file__) as handle:
        tree = ast.parse(handle.read())
    examples_src = next(
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "EXAMPLES" for t in node.targets)
    )
    return yaml.safe_load(examples_src)


def _dot1q_vpc_task():
    entries = _parse_examples_block()
    task = next(
        e for e in entries
        if e.get("name") == "Create a dot1q-tunnel vPC"
    )
    args = task["cisco.dcnm.dcnm_interface"]
    profile = next(
        c["profile"] for c in args["config"]
        if "disable_lldp_transmit" in (c.get("profile") or {})
    )
    return args, profile


def test_the_example_declares_the_approved_patch_in_source():
    """Guards the fix itself: the shipped task-level argument must be the exact approved
    string, not merely present. A typo or a different value would pass every other case
    in this file for the wrong reason if this check did not exist."""
    args, _profile = _dot1q_vpc_task()
    assert args.get("patch_version") == SUPPORTED_PATCH, (
        "the published dot1q-tunnel vPC example must declare the exact approved patch; "
        "got %r" % args.get("patch_version"))


def test_the_example_profile_still_sets_the_two_registered_lldp_fields():
    """Pins WHY this example needs the argument at all. If a future edit removed both
    registered fields from the example, the two regression cases below would trivially
    pass without exercising the patch gate -- this guards against that silent drift."""
    _args, profile = _dot1q_vpc_task()
    assert profile.get("disable_lldp_transmit") is True
    assert profile.get("disable_lldp_receive") is True


def test_the_documented_task_succeeds_as_shipped():
    """Replays the EXACT shipped task (including its own patch_version) through real
    main(). This is the straightforward regression: the example, run as published, must
    actually work."""
    args, profile = _dot1q_vpc_task()
    result, calls = run(
        profile, args.get("state", "merged"), parent="int_vpc_dot1q_tunnel",
        patch_version=args["patch_version"],
    )
    assert not result.get("failed"), (
        "the published dot1q-tunnel vPC example must succeed as shipped: %s"
        % result.get("msg"))
    assert writes(calls), "the shipped example must actually configure something"


def test_the_same_profile_without_any_patch_argument_fails_before_any_write():
    """The other half of the regression: if an operator deletes the patch_version line the
    fix added (reverting to the pre-R2 shipped example), the module must still reject it
    cleanly -- not silently drop the two LLDP fields and report success."""
    _args, profile = _dot1q_vpc_task()
    result, calls = run(
        profile, "merged", parent="int_vpc_dot1q_tunnel",
        patch_version=PATCH_KEY_OMITTED,
    )
    assert result.get("failed"), (
        "the documented profile without patch_version must fail, not silently succeed")
    assert writes(calls) == [], "no write may precede the rejection"
    assert "disable_lldp_transmit" in result.get("msg", "") or (
        "disable_lldp_receive" in result.get("msg", "")
    ), result.get("msg")


# ====================================================================================================
# Formerly test_dcnm_intf_version_resolver.py
# ====================================================================================================
# Focused tests for the NDFC version resolver (_ndfc_version_gte).
#
# The resolver must compare as many version segments as the TARGET specifies:
#   - a 4-part target (patched OSPF-MD floor "12.6.0.267") enforces the build number
#   - a 3-part target (fec "12.4.1") keeps its original 3-part behavior
# Unknown/invalid versions fail closed.


class _Stub:
    """Minimal stand-in carrying only ndfc_version (all _ndfc_version_gte reads)."""

    def __init__(self, ndfc_version):
        self.ndfc_version = ndfc_version


def gte(current, target):
    return DcnmIntf._ndfc_version_gte(_Stub(current), target)


FLOOR = "12.6.0.267"  # OSPF-MD assumed floor (validated_on)


# --- 4-part target: the build number IS enforced -----------------------------
def test_below_build_not_supported():
    assert gte("12.6.0.266", FLOOR) is False


def test_exact_build_supported():
    assert gte("12.6.0.267", FLOOR) is True


def test_higher_build_supported():
    assert gte("12.6.0.300", FLOOR) is True


def test_higher_patch_supported():
    assert gte("12.6.1.0", FLOOR) is True


def test_lower_build_that_old_3part_would_wrongly_pass():
    # With the old [:3] comparator, (12,6,0) >= (12,6,0) => wrongly True.
    # The 4-part comparator must reject it.
    assert gte("12.6.0.100", FLOOR) is False


# --- fail-closed on unknown/invalid ------------------------------------------
def test_unknown_version_fails_closed():
    assert gte(None, FLOOR) is False


def test_empty_version_fails_closed():
    assert gte("", FLOOR) is False


def test_invalid_version_fails_closed():
    assert gte("not.a.version", FLOOR) is False


# --- 3-part target (fec): behavior unchanged, build ignored ------------------
def test_fec_3part_still_supported():
    assert gte("12.4.1.245", "12.4.1") is True


def test_fec_3part_below_not_supported():
    assert gte("12.4.0.999", "12.4.1") is False


def test_fec_exact_3part_supported():
    assert gte("12.4.1", "12.4.1") is True
