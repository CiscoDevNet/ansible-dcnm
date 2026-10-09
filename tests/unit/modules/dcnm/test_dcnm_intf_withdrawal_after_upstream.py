"""Two withdrawal expectations the existing suite does not cover, added with the
integration of upstream #727/#728.

  * MULTI-FIELD WITHDRAWAL -- a pre-existing coverage gap, not an integration effect.
    The existing suite is parametrized one (parent, nvPair) at a time, which shows that
    each accepted binding can be withdrawn, not that SEVERAL omitted in the same
    invocation all reach the same payload. A loop that reconciled only the first omission,
    or that rebuilt the payload per binding, would pass every existing row and still lose
    every reset after the first. These three cases PASS on the pre-rebase candidate too;
    they close the gap and pin that the rebase did not disturb the behaviour.

  * OMITTED `fec` TOGETHER WITH AN OMITTED BINDING -- only assertable after the
    integration. Before #728 an omitted `fec` serialized as a public FEC-null against the
    controller's stored "auto", so a `replaced` rerun never converged. The live campaign
    worked around it by holding `fec: auto` explicit, which is why both ethernet bases in
    the harness still do. These two cases FAIL on the pre-rebase candidate (measured:
    `FEC` None instead of "auto", and a rerun that configures again) and pass here.

Both cases drive the real `main()` through the existing harness and assert on the CAPTURED
REQUEST at the transport boundary and on the PUBLIC DIFF, never on `changed`. Update,
deploy and read calls are counted separately at the stub.

NOT LIVE TESTED. No controller, Nexus or Jenkins is contacted. These are offline
integration assertions; they do not revalidate any of the 70 accepted bindings live.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

from .gie_withdrawal_harness import (
    ACCESS,
    FABRIC,
    base_for,
    build_have,
    run,
    split_calls,
)

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
