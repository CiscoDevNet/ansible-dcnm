"""Do the OSPF and the EIGRP/MACsec families coexist in ONE real withdrawal request?

WHY THIS FILE EXISTS

`test_gie_smu74_union_coexistence.py` establishes the union at the TABLE level: all 83
additions pinned by lot, by identity, by value and by type, with the lots disjoint and their
closure asserted. That is necessary and it is not the same question as this one.

Every pilot fixture in `gie_withdrawal_harness.py` carries only its OWN family's prerequisite
context -- `OSPF_CTX` for the OSPF rows, `EIGRP_CTX`/`EIGRP_DL4` for the EIGRP rows,
`MACSEC_FB_CTX` and friends for MACsec -- so each row is exercised through the real `main()`
alone, never beside a row from another campaign. Checked before writing this file: no fixture
in the harness mixes families, and no existing test drives two families through one module
invocation. So nothing established that a single `replaced` request can carry a withdrawal
from ALPHA's campaign and a withdrawal from BETA's at the same time, with the fields neither
targets while the other family's prerequisites survive.

WHAT IS AND IS NOT COMBINED, DELIBERATELY

Each case pairs MACsec with exactly ONE routing family. MACsec is a link-layer feature and is
orthogonal to the routing protocol, so "OSPF plus MACsec" and "EIGRP plus MACsec" are
configurations that stand on their own. This file does NOT put OSPF and EIGRP on the same
interface, and does not gather every registered field into one payload to maximise a count:
an invalid combined routing/auth configuration would prove nothing about coexistence and
would be green in a mock while impossible on a controller.

The MACsec target is always the FALLBACK name, because that is the only one of the four whose
EXPLICIT clear was measured ON ITS OWN, with the gate enabled and keychain and policy intact.
What the source campaign measured about the other three, stated exactly:

  * `macsecKeyChainName` and `macsecPolicyName` -- the two primary names -- were REFUSED by
    the controller, by field name, while the gate was enabled. A fixture that omitted either
    here would encode a request that never lands.
  * `macsecInterfacePolicy` -- the gate -- was NOT RUN on its own. Its withdrawal was only
    ever measured inside the coordinated clear. The template rule permits gate-alone (that
    rule fires only while the gate is enabled), so it must not be called impossible or
    refused; it is simply untested.

So "the fallback is the only independently measured explicit clear" is the claim, NOT "the
only independent clear that is possible". And the fallback's ACCEPTANCE UNDER OMISSION was
grouped: `replaced` omitted all four at once and the engine emitted four resets in one
request, so no independent omission was demonstrated live for any of the four, the fallback
included.

Offline. Real `main()`, real argument spec, real validation, real serialisation; mocks only at
inventory/transport. Assertions are made against the CAPTURED REQUEST and the PUBLIC DIFF,
never against `changed`.

NOT LIVE TESTED IN THIS GENERATION, and the integrated tuple is not live tested at all. Each
reset carries the live acceptance of its own source campaign and no other.

Registration is not acceptance in general -- but for this candidate the two campaign gates are
closed: ALPHA's three `enable_ospf` omissions (int_routed_host, int_subif, int_vlan) were
ACCEPTED as grouped source-campaign results, so the earlier "still pending" note is stale and
has been removed rather than left to mislead. All 157 are registered AND source-campaign
accepted, with each campaign's coordinated and platform limits unchanged. That is still not an
integrated live-tested tuple.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    resolve_binding,
)

from .gie_withdrawal_harness import (
    IF_A,
    MACSEC_FB_CTX,
    OSPF_CTX,
    ROUTED,
    base_for,
    build_have,
    cfg,
    diff_nvpairs,
    request_nvpairs,
    run,
    run_configs,
    split_calls,
)

# The MACsec target: the only one of the four whose independent EXPLICIT clear was MEASURED.
# Not "the only one that could possibly be withdrawn alone" -- the gate was never tried alone
# (NOT RUN), and only the two primary names were actually refused. See the module docstring.
MACSEC_TARGET = ("macsec_fallback_key_chain_name", "macsecFallbackKeyChainName", "PILOT-FBKC")

# One routing target per family, each with the prerequisite context its own parent demands.
#   OSPF   -- `ospf_network_type` is an ENUM whose reset is the wire spelling `noChange`,
#             so a copy-paste of the MACsec `""` onto it would be caught.
#   EIGRP  -- `enable_eigrp_shutdown` is a BOOLEAN whose reset is the string `"false"`; the
#             EIGRP process tag is mandatory for ANY EIGRP option, so it travels explicitly
#             and doubles as the non-target field that must survive.
CASES = [
    pytest.param(
        "ospf_network_type", "ospfNetworkType", "point_to_point", "noChange",
        dict(OSPF_CTX),
        {"ospfTag": OSPF_CTX["ospf_tag"], "OSPF_AREA_ID": OSPF_CTX["ospf_area_id"],
         "ospf": "true"},
        id="ospf+macsec",
    ),
    pytest.param(
        "enable_eigrp_shutdown", "eigrpShutdown", True, "false",
        {"eigrp_process_tag": "PILOT-EIGRP"},
        {"eigrpProcessTag": "PILOT-EIGRP"},
        id="eigrp+macsec",
    ),
]


# The EXACT wire value `merged` must leave in place, per routing target.
#
# Written by hand and kept INDEPENDENT of the reset literals above: asserting only
# "it differs from the reset" would pass on any wrong-but-different value, which is
# precisely how a mistranslated enum survives a suite. Measured on this candidate.
MERGED_RETAINS = {
    "ospfNetworkType": "pointToPoint",   # public `point_to_point` -> SMU wire spelling
    "eigrpShutdown": "true",             # public True -> the controller's string
}


def _model(route_ctx, **extra):
    """A routed profile carrying one routing family's context plus the MACsec context."""
    d = dict(route_ctx)
    d.update(MACSEC_FB_CTX)
    d.update(extra)
    return d


# ============================================================ the registration, guarded
def test_both_families_are_registered_before_anything_below_is_meaningful():
    """Guard the guard. If either side's row lost its reset, every case here would pass for
    the wrong reason -- the module would refuse, and a refusal is not a withdrawal."""
    for parent, key, expected in (
        (ROUTED, "ospf_network_type", "noChange"),
        (ROUTED, "enable_eigrp_shutdown", "false"),
        (ROUTED, MACSEC_TARGET[0], ""),
    ):
        b = resolve_binding(parent, key)
        assert b is not None, "%s::%s is not in the table at all" % (parent, key)
        assert b.get("reset_wire") == expected, (
            "%s::%s reset is %r, expected %r" % (parent, key, b.get("reset_wire"), expected))
        assert isinstance(b["reset_wire"], str), (
            "%s::%s reset_wire is %s; the controller returns this nvPair as a string"
            % (parent, key, type(b["reset_wire"]).__name__))


# ==================================================== one request, two campaigns' resets
@pytest.mark.parametrize("key,nvpair,applied,reset,route_ctx,retained", CASES)
def test_one_replaced_request_carries_a_withdrawal_from_each_family(
    key, nvpair, applied, reset, route_ctx, retained
):
    """The union property no single-family suite can state: both resets in ONE payload."""
    mac_key, mac_nv, mac_applied = MACSEC_TARGET
    have = build_have(ROUTED, **_model(route_ctx, **{key: applied, mac_key: mac_applied}))
    result, calls = run(base_for(ROUTED, **_model(route_ctx)), "replaced", have)
    nv = request_nvpairs(calls)
    assert nv, ("no request was sent, so neither omission was detected. changed=%s msg=%s"
                % (result.get("changed"), result.get("msg")))
    assert not result.get("failed"), result.get("msg")
    # EXACTLY one update. "Both resets are present somewhere" would also be true of a run
    # that split them across two requests, and the union property this file exists to state
    # is that ONE payload carries both.
    assert len(split_calls(calls)["updates"]) == 1, (
        "expected exactly one configuration request carrying both resets, got %d"
        % len(split_calls(calls)["updates"]))
    assert nv[0].get(nvpair) == reset, (
        "the routing family's reset is missing or wrong: %s is %r, expected %r"
        % (nvpair, nv[0].get(nvpair), reset))
    assert nv[0].get(mac_nv) == "", (
        "the MACsec fallback reset is missing or wrong: %s is %r, expected the empty string"
        % (mac_nv, nv[0].get(mac_nv)))
    # The public diff must own both too, independently of the request body.
    dnv = diff_nvpairs(result)
    assert dnv and dnv[0].get(nvpair) == reset, "the routing reset is absent from the diff"
    assert dnv[0].get(mac_nv) == "", "the MACsec reset is absent from the diff"


@pytest.mark.parametrize("key,nvpair,applied,reset,route_ctx,retained", CASES)
def test_the_untargeted_fields_of_both_families_survive(
    key, nvpair, applied, reset, route_ctx, retained
):
    """A reset that spilled onto a field nobody withdrew would be invisible in a count."""
    mac_key, mac_nv, mac_applied = MACSEC_TARGET
    have = build_have(ROUTED, **_model(route_ctx, **{key: applied, mac_key: mac_applied}))
    _result, calls = run(base_for(ROUTED, **_model(route_ctx)), "replaced", have)
    nv = request_nvpairs(calls)[0]
    # The routing family's own prerequisites.
    for field, value in retained.items():
        assert nv.get(field) == value, (
            "the routing prerequisite %s changed: %r, expected %r"
            % (field, nv.get(field), value))
    # MACsec's gate and the two names it refuses to have emptied while enabled.
    assert nv.get("macsecInterfacePolicy") == "true", (
        "the MACsec gate was withdrawn although nobody omitted it: %r"
        % nv.get("macsecInterfacePolicy"))
    assert nv.get("macsecKeyChainName") == "PILOT-KC", (
        "the MACsec keychain changed: %r" % nv.get("macsecKeyChainName"))
    assert nv.get("macsecPolicyName") == "PILOT-POL", (
        "the MACsec policy changed: %r" % nv.get("macsecPolicyName"))


# =================================================================== negative controls
@pytest.mark.parametrize("key,nvpair,applied,reset,route_ctx,retained", CASES)
def test_merged_sends_no_reset_for_either_family(
    key, nvpair, applied, reset, route_ctx, retained
):
    """CONTROL: the two resets above are attributable to the WITHDRAWAL path, not to the
    shape of the model. Under `merged` the same omission preserves both values."""
    mac_key, mac_nv, mac_applied = MACSEC_TARGET
    have = build_have(ROUTED, **_model(route_ctx, **{key: applied, mac_key: mac_applied}))
    _result, calls = run(
        base_for(ROUTED, description="coexistence-merged", **_model(route_ctx)), "merged", have)
    nv = request_nvpairs(calls)
    assert nv, "the description change produced no request"
    assert len(split_calls(calls)["updates"]) == 1, (
        "expected exactly one configuration request, got %d"
        % len(split_calls(calls)["updates"]))
    assert nv[0].get(mac_nv) == mac_applied, (
        "merged withdrew the MACsec fallback: %r" % nv[0].get(mac_nv))
    # The EXACT retained value, not merely "different from the reset": a wrong-but-different
    # value -- a mistranslated enum, say -- would satisfy an inequality and fail nothing.
    expected_retained = MERGED_RETAINS[nvpair]
    assert nv[0].get(nvpair) == expected_retained, (
        "merged did not preserve the routing value: %s is %r, expected %r"
        % (nvpair, nv[0].get(nvpair), expected_retained))
    # And it is still not the reset -- kept as a separate, explicit statement so the pair of
    # literals cannot silently converge.
    assert expected_retained != reset, (
        "the retained and reset literals for %s are the same value (%r), so this control "
        "can no longer distinguish preservation from withdrawal" % (nvpair, reset))


@pytest.mark.parametrize("key,nvpair,applied,reset,route_ctx,retained", CASES)
def test_check_mode_plans_both_resets_and_transmits_nothing(
    key, nvpair, applied, reset, route_ctx, retained
):
    """CONTROL: a plan is not a write. Both resets appear in the diff and the transport sees
    no configuration and no deploy request. "It did not write" alone would also describe a
    check mode that planned nothing at all."""
    mac_key, mac_nv, mac_applied = MACSEC_TARGET
    have = build_have(ROUTED, **_model(route_ctx, **{key: applied, mac_key: mac_applied}))
    result, calls = run_configs(
        [cfg(IF_A, base_for(ROUTED, **_model(route_ctx)))], "replaced", have, check_mode=True)
    dnv = diff_nvpairs(result)
    assert dnv, "check mode planned nothing at all"
    assert dnv[0].get(nvpair) == reset, "check mode did not plan the routing reset"
    assert dnv[0].get(mac_nv) == "", "check mode did not plan the MACsec reset"
    buckets = split_calls(calls)
    assert buckets["updates"] == [], "check mode sent a configuration request"
    assert buckets["deploys"] == [], "check mode sent a deploy request"


def test_the_two_families_neutrals_are_not_interchangeable():
    """CONTROL: the assertions above have teeth because each family's reset is a DIFFERENT
    literal. A copy-paste of one onto the other is rejected, which is what makes
    "both resets present" a real claim rather than a coincidence of shapes.

    `''`, `'false'` and `'noChange'` are three distinct values, and none is `False`: a native
    bool would never match a controller HAVE, and in a boolean test `'false'` is truthy while
    `False` is falsy.
    """
    ospf = resolve_binding(ROUTED, "ospf_network_type")["reset_wire"]
    eigrp = resolve_binding(ROUTED, "enable_eigrp_shutdown")["reset_wire"]
    macsec = resolve_binding(ROUTED, MACSEC_TARGET[0])["reset_wire"]
    assert ospf == "noChange" and eigrp == "false" and macsec == ""
    assert len({ospf, eigrp, macsec}) == 3, (
        "two of the three families now share a reset literal, so a copy-paste between them "
        "would no longer be detectable here: %r" % ([ospf, eigrp, macsec],))
    for value in (ospf, eigrp, macsec):
        assert value is not False and not isinstance(value, bool), (
            "a reset arrived as a native bool: %r" % (value,))


def test_omitting_an_eigrp_option_and_its_mandatory_tag_withdraws_both_in_one_request():
    """Omitting the whole EIGRP context withdraws the option AND its mandatory tag together,
    in one request, while the other family's retained context is untouched.

    WHY THIS DOCSTRING CHANGED, and the assertion with it. This case used to be written as
    "refused, not invented" and accepted EITHER outcome:

        if result.get("failed"):
            assert split_calls(calls)["updates"] == []
            return

    That made ANY failure a PASS. It never fired -- the run succeeds on this candidate -- so
    the branch bought nothing today and would have swallowed an unrelated regression
    tomorrow: a future defect that made this invocation fail for a completely different
    reason would have satisfied the early return and reported green.

    The observed behaviour is pinned instead, measured on this candidate: the run SUCCEEDS
    with exactly ONE update carrying

        eigrpShutdown='false'   eigrpProcessTag=''   macsecFallbackKeyChainName=''

    which is a COORDINATED clear -- the parent refuses an active option with an empty tag, so
    withdrawing the option obliges withdrawing the tag in the same payload. The test now
    proves that, which is what it actually observes, rather than a refusal it never saw.
    """
    have = build_have(ROUTED, **_model({"eigrp_process_tag": "PILOT-EIGRP"},
                                       enable_eigrp_shutdown=True,
                                       macsec_fallback_key_chain_name="PILOT-FBKC"))
    # The model drops the EIGRP context entirely: no tag, no option.
    result, calls = run(base_for(ROUTED, **MACSEC_FB_CTX), "replaced", have)

    assert not result.get("failed"), (
        "the coordinated clear was refused; this candidate was measured performing it: %s"
        % (result.get("msg"),))
    updates = split_calls(calls)["updates"]
    assert len(updates) == 1, (
        "expected exactly one configuration request, got %d" % len(updates))

    nv = request_nvpairs(calls)
    assert nv, "no request was sent, so the omission was neither withdrawn nor refused"
    assert nv[0].get("eigrpShutdown") == "false", (
        "the EIGRP option was omitted but not withdrawn: %r" % nv[0].get("eigrpShutdown"))
    assert nv[0].get("eigrpProcessTag") == "", (
        "the option was withdrawn while its mandatory tag kept a value: %r"
        % nv[0].get("eigrpProcessTag"))
    assert nv[0].get("macsecFallbackKeyChainName") == "", (
        "the MACsec fallback was omitted but not withdrawn: %r"
        % nv[0].get("macsecFallbackKeyChainName"))
    # The MACsec context nobody omitted must survive the same payload.
    assert nv[0].get("macsecInterfacePolicy") == "true", (
        "the MACsec gate was withdrawn although nobody omitted it: %r"
        % nv[0].get("macsecInterfacePolicy"))
    assert nv[0].get("macsecKeyChainName") == "PILOT-KC", (
        "the MACsec keychain changed: %r" % nv[0].get("macsecKeyChainName"))
    assert nv[0].get("macsecPolicyName") == "PILOT-POL", (
        "the MACsec policy changed: %r" % nv[0].get("macsecPolicyName"))
