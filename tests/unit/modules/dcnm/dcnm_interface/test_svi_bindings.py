"""int_vlan SVI: address-list parsing and real-main handling, and private VLAN mapping."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import pytest

from ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface import SviAddressListError
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface import svi_address_list_desired
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface import svi_address_list_from_input
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface import svi_address_list_from_wire
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface import svi_address_list_same
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface import svi_address_list_to_wire
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface import svi_address_normalize

from .helpers.binding_harness import IF_SVI
from .helpers.binding_harness import SVI
from .helpers.binding_harness import SWITCH_IP
from .helpers.binding_harness import base_for
from .helpers.binding_harness import build_have
from .helpers.binding_harness import diff_nvpairs
from .helpers.binding_harness import request_nvpairs
from .helpers.binding_harness import run_configs
from .helpers.binding_harness import split_calls
from .helpers.binding_harness import SUPPORTED_PATCH
from .helpers.binding_harness import cfg
from .helpers.binding_harness import writes


# ====================================================================================================
# Formerly test_dcnm_intf_svi_address_list_parsing.py
# Parsing, normalization and serialization of the int_vlan SVI address lists.
#
# The wire cases use the representation measured on the controller readback and the shapes the
# installed int_vlan template accepts (wrapper object or bare list, legacy element key for the
# HSRP list). Expected values are literals, independent of the serializer under test.
#
# Offline: no controller and no device.
# ====================================================================================================
MEASURED = '{"secondaryGws":[{"gatewayIpAddress":"198.51.100.254/24"},{"gatewayIpAddress":"203.0.113.254/24"},{"gatewayIpAddress":"192.0.2.254/24"}]}'


def test_the_measured_readback_parses_with_host_bits_preserved():
    assert svi_address_list_from_wire("secondary_gws", MEASURED) == [
        ("198.51.100.254", "198.51.100.254/24"),
        ("203.0.113.254", "203.0.113.254/24"),
        ("192.0.2.254", "192.0.2.254/24"),
    ]


def test_serialization_round_trips_to_the_measured_text_byte_for_byte():
    entries = svi_address_list_from_wire("secondary_gws", MEASURED)
    assert svi_address_list_to_wire("secondary_gws", entries) == MEASURED


def test_empty_string_is_the_empty_list_and_serializes_back_to_empty_string():
    assert svi_address_list_from_wire("hsrp_secondary_vips", "") == []
    assert svi_address_list_to_wire("hsrp_secondary_vips", []) == ""


@pytest.mark.parametrize(
    "raw",
    [
        '[{"hsrpSecondaryVip":"192.0.2.123"}]',
        '{"hsrpSecondaryVips":[{"hsrpSecondaryVip":"192.0.2.123"}]}',
        '{"HSRP_SECONDARY_VIPS":[{"HSRP_SECONDARY_VIP":"192.0.2.123"}]}',
    ],
    ids=["bare-list", "wrapper", "legacy-keys"],
)
def test_every_shape_the_template_accepts_is_read(raw):
    assert svi_address_list_from_wire("hsrp_secondary_vips", raw) == [("192.0.2.123", "192.0.2.123")]


def test_an_empty_element_is_skipped_like_the_template_does():
    raw = '{"secondaryGws":[{"gatewayIpAddress":""},{"gatewayIpAddress":"192.0.2.9/24"}]}'
    assert svi_address_list_from_wire("secondary_gws", raw) == [("192.0.2.9", "192.0.2.9/24")]


@pytest.mark.parametrize(
    "raw",
    [
        None,
        7,
        "not json",
        "{}",
        '{"secondaryGws":[],"x":[]}',
        '{"secondaryGws":"a"}',
        "[1]",
        '[{"gatewayIpAddress":"192.0.2.9"}]',
        '[{"gatewayIpAddress":"192.0.2.9/24","x":1}]',
        '[{"gatewayIpAddress":"192.0.2.9/24"},{"gatewayIpAddress":"192.0.2.9/25"}]',
    ],
    ids=[
        "null",
        "int",
        "not-json",
        "empty-object",
        "two-wrappers",
        "wrapper-not-list",
        "non-object-element",
        "missing-prefix",
        "extra-element-key",
        "repeated-address",
    ],
)
def test_malformed_wire_raises(raw):
    with pytest.raises(SviAddressListError):
        svi_address_list_from_wire("secondary_gws", raw)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("192.0.2.254/24", ("192.0.2.254", "192.0.2.254/24")),
        ("192.0.2.0/24", ("192.0.2.0", "192.0.2.0/24")),
        ("192.0.2.254/32", ("192.0.2.254", "192.0.2.254/32")),
    ],
)
def test_secondary_gateway_normalization_keeps_the_host_bits(value, expected):
    assert svi_address_normalize("secondary_gws", value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "192.0.2.254",
        "192.0.2.254/0",
        "192.0.2.254/33",
        "192.0.2.254/024",
        "192.0.2.254/ 24",
        "192.0.2.254/255.255.255.0",
        "2001:db8::1/64",
        "192.0.2.256/24",
        " 192.0.2.254/24",
        24,
        "",
    ],
)
def test_secondary_gateway_rejects(value):
    with pytest.raises(SviAddressListError):
        svi_address_normalize("secondary_gws", value)


@pytest.mark.parametrize("value", ["192.0.2.123/32", "2001:db8::1", "192.0.2.1234", ""])
def test_hsrp_vip_rejects(value):
    with pytest.raises(SviAddressListError):
        svi_address_normalize("hsrp_secondary_vips", value)


def test_input_order_is_kept_and_identity_is_the_address():
    entries = svi_address_list_from_input("secondary_gws", [{"gateway_ip_address": "203.0.113.254/24"}, {"gateway_ip_address": "198.51.100.254/24"}])
    assert entries == [("203.0.113.254", "203.0.113.254/24"), ("198.51.100.254", "198.51.100.254/24")]


def test_sixteen_entries_are_accepted_and_seventeen_refused():
    sixteen = [{"hsrp_secondary_vip": "192.0.2.%d" % i} for i in range(1, 17)]
    assert len(svi_address_list_from_input("hsrp_secondary_vips", sixteen)) == 16
    with pytest.raises(SviAddressListError):
        svi_address_list_from_input("hsrp_secondary_vips", sixteen + [{"hsrp_secondary_vip": "192.0.2.99"}])


A = ("198.51.100.254", "198.51.100.254/24")
B = ("203.0.113.254", "203.0.113.254/24")
A25 = ("198.51.100.254", "198.51.100.254/25")


@pytest.mark.parametrize(
    "state,requested,have,expected",
    [
        ("merged", None, [A, B], [A, B]),
        ("merged", [], [A, B], [A, B]),
        ("merged", [A], [A, B], [A, B]),
        ("merged", [A25], [A, B], [A25, B]),
        ("merged", [B, A], [], [B, A]),
        ("replaced", None, [A, B], []),
        ("replaced", [], [A, B], []),
        ("replaced", [A], [A, B], [A]),
        ("overridden", [A], [A, B], [A]),
    ],
    ids=[
        "merged-omitted",
        "merged-empty",
        "merged-subset",
        "merged-prefix-upsert",
        "merged-create",
        "replaced-omitted",
        "replaced-empty",
        "replaced-subset",
        "overridden-subset",
    ],
)
def test_desired_list_follows_the_contract(state, requested, have, expected):
    assert svi_address_list_desired(state, requested, have) == expected


def test_order_alone_is_not_a_difference_but_a_prefix_is():
    assert svi_address_list_same([A, B], [B, A])
    assert not svi_address_list_same([A25, B], [A, B])


# ====================================================================================================
# Formerly test_dcnm_intf_svi_address_lists.py
# int_vlan SVI address lists through the real ``main()``: ``secondary_gws`` and
# ``hsrp_secondary_vips``.
#
# Both are native list arguments of ``dcnm_interface``, not registry bindings. Their nvPairs carry
# JSON text in the form measured on the controller readback (NDFC 12.6.0.267, installed SMU)::
#
#     secondaryGws       {"secondaryGws":[{"gatewayIpAddress":"192.0.2.254/24"}]}
#     hsrpSecondaryVips  {"hsrpSecondaryVips":[{"hsrpSecondaryVip":"192.0.2.123"}]}
#
# and the empty string for "no entries". Every expected wire value below is written out
# literally, so the module's own serializer is never its own oracle.
#
# Contract::
#
#     requested   merged                     replaced / overridden (retained object)
#     omitted     preserve HAVE              remove every entry
#     []          preserve HAVE              remove every entry
#     nonempty    union, upsert by address   exact requested membership
#
# List order is not a functional change. Only the harness is imported here, so these cases
# also run against a module without the feature, where they fail.
#
# Offline: no controller and no device.
# ====================================================================================================
SGW = "secondaryGws"
SVIP = "hsrpSecondaryVips"

# Primary addressing and HSRP held explicit in every case, so a list change can be shown not
# to touch them.
PRIMARY = {"ipv4_addr": "192.0.2.1", "ipv4_mask_len": 24, "enable_hsrp": True, "hsrp_vip": "192.0.2.253", "hsrp_group": 1, "hsrp_version": 1}

SVI_LISTS_A, SVI_LISTS_B, C = "198.51.100.254/24", "203.0.113.254/24", "192.0.2.254/24"
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
    result, calls = run(profile(secondary_gws=gws(SVI_LISTS_A, SVI_LISTS_B), hsrp_secondary_vips=vips(V1, V2)), "merged", [])
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
    result, calls = run(profile(secondary_gws=gws(SVI_LISTS_A), hsrp_secondary_vips=vips(V1)), "merged", have(W_A_B, WV_1_2))
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
    result, calls = run(profile(secondary_gws=gws(SVI_LISTS_A), hsrp_secondary_vips=vips(V1)), "replaced", have(W_A_B, WV_1_2))
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
    keep = {"secondary_gws": gws(SVI_LISTS_A, SVI_LISTS_B)} if kept == "secondary_gws" else {"hsrp_secondary_vips": vips(V1, V2)}
    result, calls = run(profile(**keep), "replaced", have(W_A_B, WV_1_2))
    assert not result.get("failed"), result.get("msg")
    nv = only_request(calls)
    assert nv[dropped] == ""
    assert nv[kept_wire[0]] == kept_wire[1]
    assert_primary_intact(nv)


def test_replaced_reordered_list_is_not_a_change():
    result, calls = run(profile(secondary_gws=gws(SVI_LISTS_B, SVI_LISTS_A), hsrp_secondary_vips=vips(V2, V1)), "replaced", have(W_A_B, WV_1_2))
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
    result, calls = run(profile(secondary_gws=gws(SVI_LISTS_A), hsrp_secondary_vips=vips(V1)), "replaced", have(W_A_B, WV_1_2), check=True)
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is True
    dnv = diff_nvpairs(result)
    assert dnv[0][SGW] == W_A and dnv[0][SVIP] == WV_1
    assert_no_writes(calls)


def test_overridden_retained_svi_follows_replaced():
    result, calls = run(profile(secondary_gws=gws(SVI_LISTS_A)), "overridden", have(W_A_B, WV_1_2))
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


# ====================================================================================================
# Formerly test_dcnm_intf_svi_private_vlan_mapping.py
# int_vlan::private_vlan_mapping -- apply, update, explicit clear, withdrawal.
#
# The reset for this binding was MEASURED before it was registered: on a live
# SVI holding `private-vlan mapping 3214,3216`, sending the public key as the
# empty string left the controller at '' and removed that line from the running
# configuration, with the primary address, three secondary addresses and HSRP
# untouched and the leaf In-Sync.
#
# Two properties of this field drive almost every test below.
#
# 1. The values are PREFIXES of one another. `private-vlan mapping 3214` is a
#    prefix of `private-vlan mapping 3214,3216`, so every assertion compares the
#    whole value; a substring check cannot tell an apply from an update.
#
# 2. The field is a plain string with `min_length: 1` and no `valid_values`, so
#    the engine's empty-string exemption returns before the length check and the
#    public clear is accepted. A test that only drove non-empty values would not
#    notice if that exemption disappeared.
# ====================================================================================================
# Copyright (c) 2026 Cisco and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


PARENT = SVI
KEY = "private_vlan_mapping"
NVPAIR = "privateVlanMapping"
ONE = "3214"
TWO = "3214,3216"


def svi_profile(**extra):
    prof = base_for(PARENT)
    prof.update(extra)
    return prof


def drive(profile, state, have, check_mode=False):
    conf = cfg("Vlan931", profile, iftype="svi")
    return run_configs([conf], state, have=have, check_mode=check_mode,
                       allow_failed=True)


def sent_nvpairs(calls):
    bodies = [c["payload"] for c in writes(calls)]
    found = []

    def walk(node):
        if isinstance(node, dict):
            if "interfaces" in node and "policy" in node:
                found.append(node)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(bodies)
    assert len(found) == 1, "expected exactly one policy payload, got %d" % len(found)
    return found[0]["interfaces"][0]["nvPairs"]


# --------------------------------------------------------------------------
# Apply and update
# --------------------------------------------------------------------------

@pytest.mark.parametrize("value", [ONE, TWO, "3214-3216"])
def test_the_mapping_reaches_the_wire_on_the_right_parent(value):
    have = build_have(PARENT)
    result, calls = drive(svi_profile(**{KEY: value}), "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert sent_nvpairs(calls)[NVPAIR] == value


def test_an_update_replaces_the_whole_string_rather_than_merging_elements():
    """`3214` -> `3214,3216` is a new value, not a union computed here."""
    have = build_have(PARENT, KEY, ONE)
    _result, calls = drive(svi_profile(**{KEY: TWO}), "merged", have)
    assert sent_nvpairs(calls)[NVPAIR] == TWO


def test_narrowing_the_list_is_also_a_plain_replacement():
    have = build_have(PARENT, KEY, TWO)
    _result, calls = drive(svi_profile(**{KEY: ONE}), "merged", have)
    assert sent_nvpairs(calls)[NVPAIR] == ONE


def test_reapplying_the_same_value_sends_no_configuration_request():
    have = build_have(PARENT, KEY, TWO)
    result, calls = drive(svi_profile(**{KEY: TWO}), "merged", have)
    assert result.get("changed") is False
    assert writes(calls) == []


# --------------------------------------------------------------------------
# The explicit clear -- the measured reset
# --------------------------------------------------------------------------

def test_the_explicit_empty_string_is_accepted_despite_min_length_one():
    have = build_have(PARENT, KEY, TWO)
    result, calls = drive(svi_profile(**{KEY: ""}), "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert sent_nvpairs(calls)[NVPAIR] == ""


def test_the_clear_is_the_registered_reset_wire():
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
        gie_withdrawal_action)
    action, wire = gie_withdrawal_action(
        PARENT, KEY, {NVPAIR: TWO}, "12.6.0.267", SUPPORTED_PATCH)
    assert (action, wire) == ("reset", "")


# --------------------------------------------------------------------------
# Omission. This is where the neutral-baseline probe went wrong: omitting a
# field that is ALREADY empty never enters the withdrawal branch, so every case
# here starts from a CONFIGURED mapping.
# --------------------------------------------------------------------------

def assert_not_withdrawn(calls, expected):
    """Preservation shows up as SILENCE, and silence has to be read correctly.

    When the mapping is the only thing that could differ and the module decides
    to keep it, there is no diff and therefore no request at all. Demanding a
    payload here would fail a correct preservation. What must never happen is a
    payload that carries anything OTHER than the configured value.
    """
    for body in [c["payload"] for c in writes(calls)]:
        found = []

        def walk(node):
            if isinstance(node, dict):
                if "interfaces" in node and "policy" in node:
                    found.append(node)
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(body)
        for policy in found:
            nv = policy["interfaces"][0]["nvPairs"]
            assert nv.get(NVPAIR, expected) == expected, (
                "the mapping was changed to %r" % nv.get(NVPAIR))


def test_merged_omission_preserves_a_configured_mapping():
    have = build_have(PARENT, KEY, TWO)
    result, calls = drive(svi_profile(), "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert result.get("changed") is False, "merged omission must not change anything"
    assert_not_withdrawn(calls, TWO)


def test_replaced_omission_withdraws_a_configured_mapping():
    """PASS-AFTER. Against the 200 table this same call was REFUSED, because
    the binding had no reset_wire and `replaced` fails closed rather than
    guessing. With the measured reset registered it sends it."""
    have = build_have(PARENT, KEY, TWO)
    result, calls = drive(svi_profile(), "replaced", have)
    assert not result.get("failed"), result.get("msg")
    assert sent_nvpairs(calls)[NVPAIR] == ""


def test_replaced_check_plans_the_withdrawal_without_sending_it():
    have = build_have(PARENT, KEY, TWO)
    result, calls = drive(svi_profile(), "replaced", have, check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert writes(calls) == []
    assert result.get("changed") is True


def test_replaced_with_the_value_held_explicitly_keeps_it():
    have = build_have(PARENT, KEY, TWO)
    result, calls = drive(svi_profile(**{KEY: TWO}), "replaced", have)
    assert not result.get("failed"), result.get("msg")
    assert result.get("changed") is False
    assert_not_withdrawn(calls, TWO)


def test_a_rerun_after_the_withdrawal_is_converged():
    have = build_have(PARENT, KEY, "")
    result, calls = drive(svi_profile(), "replaced", have)
    assert not result.get("failed"), result.get("msg")
    assert writes(calls) == []


# --------------------------------------------------------------------------
# The reset must not leak to a sibling that did not earn it
# --------------------------------------------------------------------------

def test_the_reset_does_not_inherit_to_another_parent():
    """`private_vlan_mapping` is keyed on (int_vlan, privateVlanMapping).

    No other parent declares it, so no other parent may be handed this reset.
    MEASURED rather than assumed: the engine answers ('none', None) for a
    parent that does not declare the binding -- the same answer it gives for a
    key that does not exist at all -- not 'inapplicable'. Either way nothing is
    emitted; what this test defends is that registering one parent's reset did
    not start answering for five others."""
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
        gie_withdrawal_action)
    assert gie_withdrawal_action(
        PARENT, KEY, {NVPAIR: TWO}, "12.6.0.267", SUPPORTED_PATCH) == ("reset", "")
    for parent in ("int_routed_host", "int_subif", "int_loopback",
                   "int_trunk_host", "int_access_host"):
        assert gie_withdrawal_action(
            parent, KEY, {NVPAIR: TWO}, "12.6.0.267", SUPPORTED_PATCH) == ("none", None), parent


def test_registering_this_reset_left_the_sibling_svi_bindings_alone():
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
        BINDING_TABLE)
    rows = {(r["parent_template"], r["parent_nvpair"]): r for r in BINDING_TABLE}
    # + the eleven PVLAN companion rows (other parents, inferred resets): 234 -> 245, 207 -> 218; + one vPC PVLAN row: 246, 219.
    # + 5: 0b_37, + 5: 0b_38, + 1: 0b_39, + 19: 0b_40, + 1: rs1, + 4: pl1, + 12: ul1, + 2: 0b_41
    assert len(BINDING_TABLE) == 234 + 11 + 1 + 5 + 5 + 1 + 19 + 1 + 4 + 12 + 2
    assert sum("reset_wire" in r for r in BINDING_TABLE) == 207 + 11 + 1 + 5 + 5 + 1 + 16 + 1 + 2 + 12 + 2   # + 0b_37 to 0b_41, rs1, pl1, ul1
    # The four int_vlan identities that remain deliberately unregistered.
    for nv in ("HSRP_GROUPv6", "HSRP_VIPv6", "OSPF_AUTH_KEY", "ospfTag"):
        assert "reset_wire" not in rows[("int_vlan", nv)], nv


# --------------------------------------------------------------------------
# The protected operator state travels in the SAME payload
# --------------------------------------------------------------------------

def test_the_native_lists_and_hsrp_survive_in_the_same_payload():
    """The withdrawal shares one payload with the addresses and HSRP. If the
    reset travelled alone, or the lists were dropped to make room, the operator
    would lose three secondary addresses to a mapping change."""
    have = build_have(PARENT, KEY, TWO)
    profile = svi_profile(
        ipv4_addr="192.0.2.1", ipv4_mask_len=24,
        enable_hsrp=True, hsrp_vip="192.0.2.2", hsrp_group=1, hsrp_version=1,
        secondary_gws=[{"gateway_ip_address": "198.51.100.1/24"},
                       {"gateway_ip_address": "198.51.100.2/24"}])
    _result, calls = drive(profile, "replaced", have)
    nv = sent_nvpairs(calls)
    assert nv[NVPAIR] == ""
    assert "198.51.100.1/24" in nv["secondaryGws"]
    assert "198.51.100.2/24" in nv["secondaryGws"]
    assert nv["ENABLE_HSRP"] == "true"
    assert nv["HSRP_VIP"] == "192.0.2.2"
    assert nv["IP"] == "192.0.2.1"


def test_dropping_the_secondary_list_under_replaced_withdraws_it():
    """A guard, not a feature: this is what must never appear in a live model."""
    have = build_have(PARENT, KEY, TWO,
                      secondary_gws=[{"gateway_ip_address": "198.51.100.1/24"}])
    _result, calls = drive(svi_profile(), "replaced", have)
    assert sent_nvpairs(calls)["secondaryGws"] == ""
