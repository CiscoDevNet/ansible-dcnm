"""int_vlan SVI address lists through the real ``main()``: ``secondary_gws`` and
``hsrp_secondary_vips``.

Both are native list arguments of ``dcnm_interface``, not registry bindings. Their nvPairs carry
JSON text in the form measured on the controller readback (NDFC 12.6.0.267, installed SMU)::

    secondaryGws       {"secondaryGws":[{"gatewayIpAddress":"192.0.2.254/24"}]}
    hsrpSecondaryVips  {"hsrpSecondaryVips":[{"hsrpSecondaryVip":"192.0.2.123"}]}

and the empty string for "no entries". Every expected wire value below is written out
literally, so the module's own serializer is never its own oracle.

Contract::

    requested   merged                     replaced / overridden (retained object)
    omitted     preserve HAVE              remove every entry
    []          preserve HAVE              remove every entry
    nonempty    union, upsert by address   exact requested membership

List order is not a functional change. Only the harness is imported here, so these cases
also run against a module without the feature, where they fail.

Offline: no controller and no device.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

import pytest

from .gie_withdrawal_harness import (
    IF_SVI,
    SVI,
    SWITCH_IP,
    base_for,
    build_have,
    diff_nvpairs,
    request_nvpairs,
    run_configs,
    split_calls,
)

SGW = "secondaryGws"
SVIP = "hsrpSecondaryVips"

# Primary addressing and HSRP held explicit in every case, so a list change can be shown not
# to touch them.
PRIMARY = {"ipv4_addr": "192.0.2.1", "ipv4_mask_len": 24, "enable_hsrp": True, "hsrp_vip": "192.0.2.253", "hsrp_group": 1, "hsrp_version": 1}

A, B, C = "198.51.100.254/24", "203.0.113.254/24", "192.0.2.254/24"
V1, V2, V3 = "192.0.2.123", "192.0.2.133", "192.0.2.143"

W_A_B = '{"secondaryGws":[{"gatewayIpAddress":"198.51.100.254/24"},{"gatewayIpAddress":"203.0.113.254/24"}]}'
W_A = '{"secondaryGws":[{"gatewayIpAddress":"198.51.100.254/24"}]}'
W_A_B_C = '{"secondaryGws":[{"gatewayIpAddress":"198.51.100.254/24"},{"gatewayIpAddress":"203.0.113.254/24"},{"gatewayIpAddress":"192.0.2.254/24"}]}'
W_A25_B = '{"secondaryGws":[{"gatewayIpAddress":"198.51.100.254/25"},{"gatewayIpAddress":"203.0.113.254/24"}]}'
WV_1_2 = '{"hsrpSecondaryVips":[{"hsrpSecondaryVip":"192.0.2.123"},{"hsrpSecondaryVip":"192.0.2.133"}]}'
WV_1 = '{"hsrpSecondaryVips":[{"hsrpSecondaryVip":"192.0.2.123"}]}'
WV_1_2_3 = '{"hsrpSecondaryVips":[{"hsrpSecondaryVip":"192.0.2.123"},{"hsrpSecondaryVip":"192.0.2.133"},{"hsrpSecondaryVip":"192.0.2.143"}]}'


def gws(*addresses):
    return [{"gateway_ip_address": a} for a in addresses]


def vips(*addresses):
    return [{"hsrp_secondary_vip": a} for a in addresses]


def profile(**extra):
    return base_for(SVI, **dict(PRIMARY, **extra))


def svi(prof, name=IF_SVI):
    return {"name": name, "type": "svi", "switch": [SWITCH_IP], "deploy": True, "profile": copy.deepcopy(prof)}


def have(sgw="", svip="", name=None, **extra):
    """Authoritative HAVE from the module's own payload for the primary profile, with the list
    nvPairs set to controller text. Built without the list keys, so it is the same on a module
    without the feature."""
    h = build_have(SVI, **dict(PRIMARY, **extra))
    nv = h[0]["interfaces"][0]["nvPairs"]
    nv[SGW] = sgw
    nv[SVIP] = svip
    h[0]["interfaces"][0]["interfaceType"] = "INTERFACE_VLAN"
    if name is not None:
        h[0]["interfaces"][0]["ifName"] = name
    return h


def run(prof, state, hv, check=False, configs=None):
    return run_configs(configs or [svi(prof)], state, have=hv, check_mode=check)


def only_request(calls):
    nv = request_nvpairs(calls)
    assert len(split_calls(calls)["updates"]) == 1, split_calls(calls)["updates"]
    assert len(nv) == 1, nv
    return nv[0]


def assert_no_writes(calls):
    buckets = split_calls(calls)
    assert buckets["updates"] == [] and buckets["deploys"] == [] and buckets["other"] == [], buckets


def assert_primary_intact(nv):
    assert nv["IP"] == "192.0.2.1" and nv["PREFIX"] == "24"
    assert nv["ENABLE_HSRP"] == "true" and nv["HSRP_VIP"] == "192.0.2.253"
    assert nv["HSRP_GROUP"] == "1"


# ------------------------------------------------------------------ create
def test_create_emits_both_lists_in_the_measured_wire_form():
    result, calls = run(profile(secondary_gws=gws(A, B), hsrp_secondary_vips=vips(V1, V2)), "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = request_nvpairs(calls)
    assert nv and nv[0][SGW] == W_A_B and nv[0][SVIP] == WV_1_2
    assert_primary_intact(nv[0])


def test_create_without_the_lists_emits_neither_nvpair():
    result, calls = run(profile(), "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = request_nvpairs(calls)
    assert nv and SGW not in nv[0] and SVIP not in nv[0]


# ------------------------------------------------------------------ merged
def test_merged_subset_is_a_union_and_changes_nothing():
    """HAVE=[A,B], WANT=[A] -> still [A,B] under merged: no request at all."""
    result, calls = run(profile(secondary_gws=gws(A), hsrp_secondary_vips=vips(V1)), "merged", have(W_A_B, WV_1_2))
    assert not result.get("failed"), result.get("msg")
    assert split_calls(calls)["updates"] == [], "a subset under merged wrote"
    assert result["changed"] is False


def test_merged_addition_unions_with_have():
    result, calls = run(profile(secondary_gws=gws(C), hsrp_secondary_vips=vips(V3)), "merged", have(W_A_B, WV_1_2))
    assert not result.get("failed"), result.get("msg")
    nv = only_request(calls)
    assert nv[SGW] == W_A_B_C and nv[SVIP] == WV_1_2_3
    assert_primary_intact(nv)
    dnv = diff_nvpairs(result)
    assert dnv[0][SGW] == W_A_B_C and dnv[0][SVIP] == WV_1_2_3


def test_merged_explicit_prefix_updates_that_entry_in_place():
    result, calls = run(profile(secondary_gws=gws("198.51.100.254/25")), "merged", have(W_A_B, ""))
    assert not result.get("failed"), result.get("msg")
    assert only_request(calls)[SGW] == W_A25_B


@pytest.mark.parametrize("lists", [{}, {"secondary_gws": [], "hsrp_secondary_vips": []}], ids=["omitted", "explicit-empty"])
def test_merged_omitted_or_empty_preserves_and_carries_the_have_text(lists):
    """An unrelated change under merged: both lists travel as the exact HAVE text and are not
    reported as a change."""
    result, calls = run(profile(description="unrelated change", **lists), "merged", have(W_A_B, WV_1_2))
    assert not result.get("failed"), result.get("msg")
    nv = only_request(calls)
    assert nv["DESC"] == "unrelated change"
    assert nv[SGW] == W_A_B and nv[SVIP] == WV_1_2
    dnv = diff_nvpairs(result)
    assert SGW not in dnv[0] and SVIP not in dnv[0], dnv


def test_merged_effective_list_over_sixteen_fails_before_any_request():
    have_text = '{"secondaryGws":[%s]}' % ",".join('{"gatewayIpAddress":"198.51.%d.1/24"}' % i for i in range(10))
    want = gws(*["203.0.%d.1/24" % i for i in range(7)])
    result, calls = run(profile(secondary_gws=want), "merged", have(have_text, ""))
    assert result.get("failed") and "16" in result.get("msg", "")
    assert_no_writes(calls)


# ------------------------------------------------------------------ replaced
def test_replaced_subset_is_exact_membership():
    """HAVE=[A,B], WANT=[A] -> [A] under replaced."""
    result, calls = run(profile(secondary_gws=gws(A), hsrp_secondary_vips=vips(V1)), "replaced", have(W_A_B, WV_1_2))
    assert not result.get("failed"), result.get("msg")
    nv = only_request(calls)
    assert nv[SGW] == W_A and nv[SVIP] == WV_1
    assert_primary_intact(nv)


@pytest.mark.parametrize("lists", [{}, {"secondary_gws": [], "hsrp_secondary_vips": []}], ids=["omitted", "explicit-empty"])
def test_replaced_omitted_or_empty_withdraws_both(lists):
    result, calls = run(profile(**lists), "replaced", have(W_A_B, WV_1_2))
    assert not result.get("failed"), result.get("msg")
    nv = only_request(calls)
    assert nv[SGW] == "" and nv[SVIP] == ""
    assert_primary_intact(nv)
    dnv = diff_nvpairs(result)
    assert dnv[0][SGW] == "" and dnv[0][SVIP] == ""


@pytest.mark.parametrize(
    "kept,dropped,kept_wire",
    [
        ("secondary_gws", SVIP, (SGW, W_A_B)),
        ("hsrp_secondary_vips", SGW, (SVIP, WV_1_2)),
    ],
    ids=["keep-gws-drop-vips", "keep-vips-drop-gws"],
)
def test_replaced_withdraws_one_list_independently(kept, dropped, kept_wire):
    keep = {"secondary_gws": gws(A, B)} if kept == "secondary_gws" else {"hsrp_secondary_vips": vips(V1, V2)}
    result, calls = run(profile(**keep), "replaced", have(W_A_B, WV_1_2))
    assert not result.get("failed"), result.get("msg")
    nv = only_request(calls)
    assert nv[dropped] == ""
    assert nv[kept_wire[0]] == kept_wire[1]
    assert_primary_intact(nv)


def test_replaced_reordered_list_is_not_a_change():
    result, calls = run(profile(secondary_gws=gws(B, A), hsrp_secondary_vips=vips(V2, V1)), "replaced", have(W_A_B, WV_1_2))
    assert not result.get("failed"), result.get("msg")
    assert split_calls(calls)["updates"] == [] and result["changed"] is False


def test_replaced_rerun_after_withdrawal_converges():
    result, calls = run(profile(), "replaced", have("", ""))
    assert not result.get("failed"), result.get("msg")
    assert split_calls(calls)["updates"] == [] and result["changed"] is False


def test_replaced_without_lists_on_a_controller_that_omits_the_keys_does_not_write():
    hv = have()
    del hv[0]["interfaces"][0]["nvPairs"][SGW]
    del hv[0]["interfaces"][0]["nvPairs"][SVIP]
    result, calls = run(profile(), "replaced", hv)
    assert not result.get("failed"), result.get("msg")
    assert split_calls(calls)["updates"] == [] and result["changed"] is False


def test_check_mode_plans_the_exact_removal_and_sends_nothing():
    result, calls = run(profile(secondary_gws=gws(A), hsrp_secondary_vips=vips(V1)), "replaced", have(W_A_B, WV_1_2), check=True)
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is True
    dnv = diff_nvpairs(result)
    assert dnv[0][SGW] == W_A and dnv[0][SVIP] == WV_1
    assert_no_writes(calls)


def test_overridden_retained_svi_follows_replaced():
    result, calls = run(profile(secondary_gws=gws(A)), "overridden", have(W_A_B, WV_1_2))
    assert not result.get("failed"), result.get("msg")
    updates = split_calls(calls)["updates"]
    assert updates, "overridden sent no update for the retained SVI"
    nv = request_nvpairs(calls)
    retained = [n for n in nv if n.get("INTF_NAME", "").lower() == IF_SVI.lower()]
    assert retained and retained[0][SGW] == W_A and retained[0][SVIP] == ""


# ------------------------------------------------------------------ coexistence
def test_a_registered_scalar_binding_travels_with_the_lists_unchanged():
    """hsrp_preempt_delay_minimum is a registry binding on int_vlan; it rides in the same
    payload and the list change does not alter it."""
    prof = profile(preempt=True, hsrp_preempt_delay_minimum=45, secondary_gws=gws(C))
    result, calls = run(prof, "merged", have(W_A_B, WV_1_2, preempt=True))
    assert not result.get("failed"), result.get("msg")
    nv = only_request(calls)
    assert nv["hsrpPreemptDelayMinimum"] == "45"
    assert nv[SGW] == W_A_B_C and nv[SVIP] == WV_1_2


# ------------------------------------------------------------------ fail closed
@pytest.mark.parametrize(
    "bad",
    ["not json", '{"other":[]}', '[{"gatewayIpAddress":"1.2.3"}]', '{"secondaryGws":[{"gatewayIpAddress":"192.0.2.9/24","x":1}]}'],
    ids=["not-json", "wrong-wrapper", "bad-address", "extra-key"],
)
def test_malformed_have_fails_closed_and_is_never_read_as_empty(bad):
    result, calls = run(profile(), "replaced", have(bad, ""))
    assert result.get("failed"), "a malformed HAVE was accepted"
    assert_no_writes(calls)


def test_null_have_fails_closed():
    hv = have()
    hv[0]["interfaces"][0]["nvPairs"][SGW] = None
    result, calls = run(profile(), "replaced", hv)
    assert result.get("failed")
    assert_no_writes(calls)


@pytest.mark.parametrize(
    "bad",
    [
        {"secondary_gws": None},
        {"secondary_gws": "198.51.100.254/24"},
        {"secondary_gws": [{"gateway_ip_address": "198.51.100.254"}]},
        {"secondary_gws": [{"gateway_ip_address": "198.51.100.254/24", "tag": 1}]},
        {"secondary_gws": [{"gateway": "198.51.100.254/24"}]},
        {"secondary_gws": gws("198.51.100.254/24", "198.51.100.254/25")},
        {"secondary_gws": gws(*["198.51.%d.1/24" % i for i in range(17)])},
        {"hsrp_secondary_vips": [{"hsrp_secondary_vip": "192.0.2.300"}]},
        {"hsrp_secondary_vips": vips(V1, V1)},
        {"hsrp_secondary_vips": [V1]},
    ],
    ids=["null", "string", "no-prefix", "unknown-key", "wrong-key", "dup-conflicting-prefix", "seventeen", "bad-vip", "dup-vip", "bare-string-element"],
)
def test_invalid_input_is_refused_before_any_request(bad):
    result, calls = run(profile(**bad), "merged", have(W_A_B, WV_1_2))
    assert result.get("failed"), "invalid input was accepted: %r" % (bad,)
    assert_no_writes(calls)


def test_an_invalid_second_object_prevents_a_write_for_the_first():
    first = svi(profile(secondary_gws=gws(C)))
    second = svi(profile(secondary_gws=gws("192.0.2.999/24")), name="Vlan932")
    result, calls = run(None, "merged", have(W_A_B, ""), configs=[first, second])
    assert result.get("failed")
    assert_no_writes(calls)


# ------------------------------------------------------------------ query / deleted
def test_query_returns_the_lists_as_the_controller_holds_them():
    result, calls = run_configs([{"name": IF_SVI, "switch": [SWITCH_IP]}], "query", have=have(W_A_B, WV_1_2))
    assert not result.get("failed"), result.get("msg")
    assert_no_writes(calls)
    text = repr(result.get("response"))
    assert W_A_B in text and WV_1_2 in text


def test_deleted_named_svi_removes_only_that_svi_whatever_its_lists():
    other = have(W_A, "", name="Vlan932")
    result, calls = run_configs(
        [{"name": IF_SVI, "type": "svi", "switch": [SWITCH_IP]}],
        "deleted",
        have=have(W_A_B, WV_1_2) + other,
    )
    assert not result.get("failed"), result.get("msg")
    writes = [c for c in calls if c["method"] != "GET"]
    assert writes, "deleted sent nothing"
    sent = repr([c["payload"] for c in writes]).lower()
    assert IF_SVI.lower() in sent and "vlan932" not in sent
