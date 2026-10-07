"""PR725-PATCH-VERSION-001 / DELTA R2 finding 3 -- disabled-context PV07 closeout.

R1 review found that `test_gie_patch_version_gate.py`'s PV07 claim leaned on pre-existing
native/legacy test files that pass unmodified -- but those files run through
`gie_withdrawal_harness.run_configs`/`run`, which (since this task) defaults
`patch_version` to the approved constant. Passing unmodified proves nothing about the
ABSENT-argument case specifically, because the default quietly supplies an approved one.

Every case below uses `PATCH_KEY_OMITTED` explicitly -- the patch argument is genuinely
absent from module args, not defaulted by the harness -- and asserts the actual expected
payload/result, not merely the lack of a failure (a silently dropped field, or a silently
empty response, would also pass a bare "not failed" check).

NOT LIVE TESTED IN THIS GENERATION. No controller, Nexus or Jenkins is contacted.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    BINDING_TABLE,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    gie_binding_applicable,
    gie_contribute_nvpairs,
)

from .gie_withdrawal_harness import (
    IF_A,
    PATCH_KEY_OMITTED,
    PC_TRUNK,
    SVI,
    TRUNK,
    VPC_DOT1Q,
    base_for,
    build_have,
    cfg,
    cfg_for,
    diff_nvpairs,
    request_nvpairs,
    run_configs,
    writes,
)

BELOW_NDFC_FLOOR = "12.6.0.266"
SUPPORTED_NDFC = "12.6.0.267"


# ============================================================================= merged
# (strengthens the existing PV04 merged case from test_gie_patch_version_gate.py, which
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
    # from the playbook order (see gie_withdrawal_harness module docstring), so the exact
    # peer1<->peer2 mapping is asserted elsewhere (test_dcnm_intf_vpc_dot1q.py); here it is
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
    for patch_value, label in [(None, "disabled"), ("4.3.1.0175006011", "approved")]:
        add, err = gie_contribute_nvpairs(
            binding["parent_template"], {binding["profile_key"]: True}, SUPPORTED_NDFC,
            patch_value,
        )
        assert add is None, "smu_unsupported must still reject with patch %s" % label
        assert err and "not supported by the interface templates installed" in err, (
            "%s (patch %s) -- the rejection reason must stay template support, not the "
            "patch gate" % (err, label))
