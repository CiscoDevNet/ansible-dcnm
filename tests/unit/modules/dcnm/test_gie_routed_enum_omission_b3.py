"""Withdrawal acceptance for the two routed OSPF ENUM identities.

    int_routed_host :: ospfPassiveMode   reset_wire "noChange"
    int_routed_host :: ospfNetworkType   reset_wire "noChange"

These two are the first registered resets whose WIRE spelling is not their PUBLIC
spelling. The public neutral is `no_change`; the nvPair the controller stores is
`noChange`. Everything here keeps those two vocabularies apart, because collapsing them
is the failure this registration could introduce.

WHAT THE PILOT MATRIX ALREADY COVERS, AND IS NOT REPEATED HERE

`test_dcnm_intf_withdrawal.py` parametrises both rows through the real `main()`: omission
alone under `replaced`, merged preservation, explicit-clear precedence, version gating,
the unsupported-row rejection and the per-row registry assertion. Its fixture uses
`no_passive` and `point_to_point`.

WHAT THIS FILE ADDS

  * the OTHER non-neutral value of each pair -- `passive` and `broadcast`;
  * the neutral already in HAVE: no reset may be sent for a value already neutral;
  * BOTH keys omitted in one config: both resets in one payload;
  * partial omission in both directions: the explicit companion survives untouched;
  * check mode: the plan carries both resets and NOTHING is transmitted;
  * rerun from the neutral state: converges with no configuration or deploy request;
  * a sibling routed enum WITHOUT a reset keeps its own specific rejection, so this
    registration did not open a blanket exemption;
  * positive and negative for the two vocabulary-aware harness helpers.

Offline. Real `main()`, real argument spec, real validation, real serialisation; mocks
only at inventory/transport. Assertions are made against the CAPTURED REQUEST and the
PUBLIC DIFF, never against `changed`.

The `other` request bucket holds the pre-existing bulk-api capability probe
(`dcnm_get_bulk_api_support`, an empty POST to bulk-update/networks). It is counted
separately from configuration and deploy on purpose and is not this work's to fix.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    resolve_binding,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    GIE_WITHDRAW_NONE,
    GIE_WITHDRAW_RESET,
    GIE_WITHDRAW_UNSUPPORTED,
    gie_withdrawal_action,
)

from .gie_withdrawal_harness import (
    IF_A,
    OSPF_CTX,
    ROUTED,
    SUPPORTED,
    SUPPORTED_PATCH,
    base_for,
    build_have,
    cfg,
    diff_nvpairs,
    public_clear_for,
    request_nvpairs,
    run,
    run_configs,
    split_calls,
    wire_for,
)

RESET = "noChange"

# (public profile key, nvPair, the two non-neutral public values, their wire spellings)
PASSIVE = ("ospf_passive_mode", "ospfPassiveMode",
           {"passive": "passive", "no_passive": "noPassive"})
NETWORK = ("ospf_network_type", "ospfNetworkType",
           {"broadcast": "broadcast", "point_to_point": "pointToPoint"})
BOTH = [PASSIVE, NETWORK]

# The variants the pilot fixture does NOT use, so both values of both enums get exercised.
OTHER_VARIANT = [
    (PASSIVE[0], PASSIVE[1], "passive"),
    (NETWORK[0], NETWORK[1], "broadcast"),
]
OTHER_IDS = ["%s=%s" % (k, v) for k, _n, v in OTHER_VARIANT]


def _ospf(**extra):
    """The OSPF base group plus whatever the case pins explicitly."""
    d = dict(OSPF_CTX)
    d.update(extra)
    return d


# =========================================================== the registration itself
@pytest.mark.parametrize("key,nvpair,variants", BOTH, ids=[b[0] for b in BOTH])
def test_the_row_is_registered_with_the_neutral_wire_string(key, nvpair, variants):
    """Guard the guard: every case below is about a registered reset. If the
    regeneration ever dropped it, they would pass for the wrong reason."""
    b = resolve_binding(ROUTED, key)
    assert b is not None, "%s::%s is not in the table at all" % (ROUTED, key)
    assert b["parent_nvpair"] == nvpair
    assert b.get("reset_wire") == RESET
    assert isinstance(b["reset_wire"], str), "the reset must be the wire STRING"
    # The public vocabulary is untouched by the registration.
    assert "no_change" in b["valid_values"]
    assert RESET not in b["valid_values"], (
        "the WIRE spelling leaked into public valid_values")
    assert b["wire_values"]["no_change"] == RESET


# ================================================== the other non-neutral variant
@pytest.mark.parametrize("key,nvpair,applied", OTHER_VARIANT, ids=OTHER_IDS)
def test_omission_from_the_other_variant_emits_the_reset(key, nvpair, applied):
    """The pilot drives `no_passive`/`point_to_point`; these are `passive`/`broadcast`."""
    have = build_have(ROUTED, key, applied, **OSPF_CTX)
    result, calls = run(base_for(ROUTED, **OSPF_CTX), "replaced", have)
    nv = request_nvpairs(calls)
    assert nv, ("no request was sent: the omission went undetected. changed=%s"
                % result.get("changed"))
    assert nv[0].get(nvpair) == RESET, (
        "omitting %s from HAVE=%r must send %r, got %r"
        % (key, applied, RESET, nv[0].get(nvpair)))
    assert not result.get("failed"), result.get("msg")


@pytest.mark.parametrize("key,nvpair,applied", OTHER_VARIANT, ids=OTHER_IDS)
def test_merged_preserves_the_other_variant(key, nvpair, applied):
    """Under `merged` an unrelated edit must re-send the controller's own wire value."""
    have = build_have(ROUTED, key, applied, **OSPF_CTX)
    _result, calls = run(
        base_for(ROUTED, description="b3-merged", **OSPF_CTX), "merged", have)
    nv = request_nvpairs(calls)
    assert nv, "the description change produced no request"
    assert nv[0].get(nvpair) == wire_for(ROUTED, key, applied)


# ============================================ neutral already in HAVE: no reset needed
@pytest.mark.parametrize("key,nvpair,variants", BOTH, ids=[b[0] for b in BOTH])
def test_a_value_already_neutral_needs_no_reset(key, nvpair, variants):
    """`noChange` in HAVE is the withdrawn state. Sending a reset for it would claim a
    change that is not needed; the classifier must say NONE."""
    action, wire = gie_withdrawal_action(ROUTED, key, RESET, SUPPORTED, SUPPORTED_PATCH)
    assert (action, wire) == (GIE_WITHDRAW_NONE, None), (
        "a neutral HAVE must classify as NONE, got %r" % ((action, wire),))


@pytest.mark.parametrize("key,nvpair,variants", BOTH, ids=[b[0] for b in BOTH])
def test_a_configured_value_classifies_as_reset(key, nvpair, variants):
    """The complement of the case above, for both non-neutral values."""
    for public, wire_value in variants.items():
        action, wire = gie_withdrawal_action(ROUTED, key, wire_value, SUPPORTED, SUPPORTED_PATCH)
        assert (action, wire) == (GIE_WITHDRAW_RESET, RESET), (
            "HAVE=%r (public %r) must classify as RESET/%r, got %r"
            % (wire_value, public, RESET, (action, wire)))


# ================================================ both keys omitted in one config
def test_both_keys_omitted_together_send_both_resets():
    """One config, two withdrawals. A payload carrying only one of them would leave the
    other value in place while the run reported success."""
    have = build_have(ROUTED, **_ospf(ospf_passive_mode="no_passive",
                                      ospf_network_type="point_to_point"))
    result, calls = run(base_for(ROUTED, **OSPF_CTX), "replaced", have)
    nv = request_nvpairs(calls)
    assert nv, "no request was sent for the paired omission"
    assert nv[0].get("ospfPassiveMode") == RESET, "passive mode reset missing"
    assert nv[0].get("ospfNetworkType") == RESET, "network type reset missing"
    assert not result.get("failed"), result.get("msg")
    # The public diff must own both too, independently of the request.
    dnv = diff_nvpairs(result)
    assert dnv and dnv[0].get("ospfPassiveMode") == RESET
    assert dnv[0].get("ospfNetworkType") == RESET


def test_the_paired_omission_preserves_the_ospf_context():
    """The gate and its mandatory group are not collateral of a withdrawal."""
    have = build_have(ROUTED, **_ospf(ospf_passive_mode="no_passive",
                                      ospf_network_type="point_to_point"))
    _result, calls = run(base_for(ROUTED, **OSPF_CTX), "replaced", have)
    nv = request_nvpairs(calls)[0]
    assert nv.get("ospf") == "true", "OSPF was disabled by a withdrawal"
    assert nv.get("ospfTag") == OSPF_CTX["ospf_tag"]
    assert nv.get("OSPF_AREA_ID") == OSPF_CTX["ospf_area_id"]


# ==================================================== partial omission, both directions
@pytest.mark.parametrize(
    "omitted,omitted_nv,kept,kept_nv,kept_value",
    [
        ("ospf_passive_mode", "ospfPassiveMode",
         "ospf_network_type", "ospfNetworkType", "point_to_point"),
        ("ospf_network_type", "ospfNetworkType",
         "ospf_passive_mode", "ospfPassiveMode", "no_passive"),
    ],
    ids=["omit-passive-keep-network", "omit-network-keep-passive"],
)
def test_partial_omission_keeps_the_explicit_companion(
    omitted, omitted_nv, kept, kept_nv, kept_value
):
    """One key omitted, the other still explicit. The companion must keep its own wire
    value -- a reset that spilled onto it would be invisible in a summary count."""
    have = build_have(ROUTED, **_ospf(**{omitted: "passive" if "passive" in omitted
                                         else "broadcast",
                                         kept: kept_value}))
    result, calls = run(base_for(ROUTED, **_ospf(**{kept: kept_value})),
                        "replaced", have)
    nv = request_nvpairs(calls)
    assert nv, "no request was sent for the partial omission"
    assert nv[0].get(omitted_nv) == RESET, "the omitted key did not get its reset"
    assert nv[0].get(kept_nv) == wire_for(ROUTED, kept, kept_value), (
        "the explicit companion %s changed: expected %r, got %r"
        % (kept_nv, wire_for(ROUTED, kept, kept_value), nv[0].get(kept_nv)))
    assert not result.get("failed"), result.get("msg")


# ============================================================== check mode and rerun
def test_check_mode_plans_both_resets_and_transmits_nothing():
    """A plan is not a write. The diff must carry both resets and the transport must
    see no configuration and no deploy request."""
    have = build_have(ROUTED, **_ospf(ospf_passive_mode="no_passive",
                                      ospf_network_type="point_to_point"))
    result, calls = run_configs(
        [cfg(IF_A, base_for(ROUTED, **OSPF_CTX))], "replaced", have, check_mode=True)
    dnv = diff_nvpairs(result)
    assert dnv, "check mode planned nothing at all"
    assert dnv[0].get("ospfPassiveMode") == RESET
    assert dnv[0].get("ospfNetworkType") == RESET
    buckets = split_calls(calls)
    assert buckets["updates"] == [], "check mode sent a configuration request"
    assert buckets["deploys"] == [], "check mode sent a deploy request"


def test_rerun_from_the_neutral_state_converges():
    """With both values already neutral, the same model must configure nothing and
    deploy nothing. `changed` alone is not the evidence: the buckets are."""
    have = build_have(ROUTED, **_ospf(ospf_passive_mode="no_change",
                                      ospf_network_type="no_change"))
    result, calls = run(base_for(ROUTED, **OSPF_CTX), "replaced", have)
    buckets = split_calls(calls)
    assert buckets["updates"] == [], (
        "a converged rerun sent a configuration request: %s"
        % [c["path"] for c in buckets["updates"]])
    assert buckets["deploys"] == [], "a converged rerun sent a deploy request"
    assert not result.get("failed"), result.get("msg")


# =================================================== the sibling row keeps its rejection
def test_a_sibling_routed_enum_without_a_reset_still_rejects():
    """`ospf_bfd_mode` is the third routed OSPF enum and carries NO reset. Registering
    these two must not turn into a blanket exemption for the family."""
    # THE EXAMPLE IS DERIVED, NOT HARDCODED. This case named `ospf_bfd_mode` and asserted that
    # it carried no reset, with the message "this case no longer guards anything" -- which is
    # exactly what happened when the OSPF-ALL P2 profile measured and registered it on
    # int_routed_host. The contract it guards is intact; only the example expired.
    #
    # Deriving it from the loaded table means a future registration can never invalidate this
    # case again, and if routed ever ran out of unregistered enums the assertion below says so
    # loudly instead of the case passing for the wrong reason.
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
        BINDING_TABLE as _BT,
    )
    _rows = list(_BT.values()) if isinstance(_BT, dict) else list(_BT)
    siblings = [r for r in _rows
                if r["parent_template"] == ROUTED and r["type"] == "enum"
                and r.get("reset_wire") is None
                and r.get("default_template") is not None]
    assert siblings, (
        "every routed enum now carries a reset; this case has nothing left to guard and must "
        "be rehomed deliberately, not deleted")
    b = siblings[0]
    key, default = b["profile_key"], b["default_template"]
    # A CONFIGURED value, i.e. anything that is not the declared default.
    configured = "0" if default != "0" else "7"
    action, wire = gie_withdrawal_action(ROUTED, key, configured, SUPPORTED, SUPPORTED_PATCH)
    assert (action, wire) == (GIE_WITHDRAW_UNSUPPORTED, None), (
        "%s: a configured value with no registered reset must stay UNSUPPORTED, got %r"
        % (key, (action, wire)))
    # And its own declared default is still NONE, for the same reason as the registered rows.
    assert gie_withdrawal_action(ROUTED, key, default, SUPPORTED, SUPPORTED_PATCH) == (
        GIE_WITHDRAW_NONE, None), (
        "%s: its own declared default %r must classify NONE" % (key, default))


# ========================================= the two vocabulary-aware harness helpers
def test_wire_for_translates_only_when_the_binding_declares_a_vocabulary():
    """Positive: the OSPF enums translate. Negative: a binding without `wire_values`
    is returned untouched, so every pre-existing caller keeps its behaviour."""
    assert wire_for(ROUTED, "ospf_passive_mode", "no_passive") == "noPassive"
    assert wire_for(ROUTED, "ospf_network_type", "point_to_point") == "pointToPoint"
    assert wire_for(ROUTED, "ospf_passive_mode", "passive") == "passive"
    # No vocabulary declared: unchanged, including the non-string forms.
    assert wire_for(ROUTED, "acl_filter", "ACL-X") == "ACL-X"
    assert wire_for(ROUTED, "disable_ipv4_redirects", True) == "true"


def test_public_clear_for_returns_the_public_spelling_not_the_wire_one():
    """Positive: the public input that requests the reset. Negative: the wire spelling
    is NOT public vocabulary, and a binding with no public clear says None."""
    assert public_clear_for(ROUTED, "ospf_passive_mode", RESET) == "no_change"
    assert public_clear_for(ROUTED, "ospf_network_type", RESET) == "no_change"
    # The wire spelling must never come back as the public answer.
    assert public_clear_for(ROUTED, "ospf_passive_mode", RESET) != RESET
    # A reset with no public spelling in the vocabulary is reported as absent.
    assert public_clear_for(ROUTED, "ospf_passive_mode", "nonsense") is None
    # A binding without a vocabulary behaves exactly as the old inline rule did.
    assert public_clear_for(ROUTED, "acl_filter", "") == ""
    assert public_clear_for(ROUTED, "disable_ipv4_redirects", "false") is False


def test_the_public_neutral_is_accepted_and_the_wire_spelling_is_refused():
    """The vocabulary split, through the real argument spec: `no_change` is valid input
    and `noChange` is not. This is what keeps the registration from leaking the wire
    spelling into the public interface."""
    have = build_have(ROUTED, "ospf_passive_mode", "no_passive", **OSPF_CTX)
    ok, _calls = run(base_for(ROUTED, **_ospf(ospf_passive_mode="no_change")),
                     "replaced", have)
    assert not ok.get("failed"), ok.get("msg")

    bad, calls = run(base_for(ROUTED, **_ospf(ospf_passive_mode=RESET)),
                     "replaced", have)
    assert bad.get("failed"), "the WIRE spelling was accepted as public input"
    assert split_calls(calls)["updates"] == [], (
        "the refused wire spelling still sent a configuration request")
