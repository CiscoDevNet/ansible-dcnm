"""OSPF BFD and passive on loopback and subinterface under SMU 4.3.1.0175006017.

The 017 parent templates replaced the booleans ospfBfd (int_loopback, int_subif) and
ospfPassiveInterface (int_subif) with the enums ospfBfdMode and ospfPassiveMode (installed bodies read from
the 017 controller: int_loopback 8082cbdf, int_subif 1937c6a5; not exercised live by these tests).

Public contract pinned here, through the real main():
  * ospf_bfd_mode / ospf_passive_mode are the registered keys (no_change, enable, disable / passive, no_passive);
  * the booleans ospf_bfd and ospf_passive_interface are an INPUT alias: true -> enable / passive, false -> no_change
    (the old "no local override"), never the explicit disable / no_passive;
  * the alias is rejected on a parent that does not register the mode key, and a conflicting pair is rejected.

Nothing here claims the controller or the device behave this way: the requests are intercepted.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    GIE_OSPF_BOOLEAN_ALIASES,
    gie_normalize_ospf_aliases,
)
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import gie_withdrawal_harness as h

CTX = dict(h.OSPF_CTX)
CASES = [  # parent, public mode key, nvPair, alias key, positive word, wire positive
    (h.LOOPBACK, "ospf_bfd_mode", "ospfBfdMode", "ospf_bfd", "enable", "enable"),
    (h.SUBIF, "ospf_bfd_mode", "ospfBfdMode", "ospf_bfd", "enable", "enable"),
    (h.SUBIF, "ospf_passive_mode", "ospfPassiveMode", "ospf_passive_interface", "passive", "passive"),
]
IDS = ["%s::%s" % (c[0], c[1]) for c in CASES]


def sent(calls, nvpair):
    values = [nv[nvpair] for nv in h.request_nvpairs(calls) if nvpair in nv]
    assert values, "%s never reached an outbound request" % nvpair
    return values[-1]


def create(parent, **opts):
    return h.run(h.base_for(parent, **dict(CTX, **opts)), "merged", parent=parent)


# ------------------------------------------------------------------ encoding
@pytest.mark.parametrize("parent,mode_key,nvpair,alias,positive,wire", CASES, ids=IDS)
def test_the_mode_key_reaches_the_payload_in_the_017_vocabulary(parent, mode_key, nvpair, alias, positive, wire):
    result, calls = create(parent, **{mode_key: positive})
    assert not result.get("failed"), result.get("msg")
    assert sent(calls, nvpair) == wire


@pytest.mark.parametrize("parent,mode_key,nvpair,alias,positive,wire", CASES, ids=IDS)
def test_the_explicit_negative_mode_is_distinct_from_no_change(parent, mode_key, nvpair, alias, positive, wire):
    explicit, wire_value = ("no_passive", "noPassive") if mode_key == "ospf_passive_mode" else ("disable", "disable")
    explicit_result, explicit_calls = create(parent, **{mode_key: explicit})
    neutral_result, neutral_calls = create(parent, **{mode_key: "no_change"})
    assert not explicit_result.get("failed") and not neutral_result.get("failed")
    assert sent(explicit_calls, nvpair) == wire_value
    assert sent(neutral_calls, nvpair) == "noChange"


@pytest.mark.parametrize("parent,mode_key,nvpair,alias,positive,wire", CASES, ids=IDS)
def test_the_boolean_alias_true_means_the_positive_mode(parent, mode_key, nvpair, alias, positive, wire):
    result, calls = create(parent, **{alias: True})
    assert not result.get("failed"), result.get("msg")
    assert sent(calls, nvpair) == wire


@pytest.mark.parametrize("parent,mode_key,nvpair,alias,positive,wire", CASES, ids=IDS)
def test_the_boolean_alias_false_is_no_change_never_an_explicit_negative(parent, mode_key, nvpair, alias, positive, wire):
    result, calls = create(parent, **{alias: False})
    assert not result.get("failed"), result.get("msg")
    assert sent(calls, nvpair) == "noChange"
    for nv in h.request_nvpairs(calls):
        assert nv.get(nvpair) not in ("disable", "noPassive")


@pytest.mark.parametrize("parent,mode_key,nvpair,alias,positive,wire", CASES, ids=IDS)
def test_the_retired_nvpair_name_is_never_sent(parent, mode_key, nvpair, alias, positive, wire):
    _result, calls = create(parent, **{alias: True})
    for nv in h.request_nvpairs(calls):
        assert "ospfBfd" not in nv and "ospfPassiveInterface" not in nv


# ------------------------------------------------------------------ alias rules
@pytest.mark.parametrize("parent,mode_key,nvpair,alias,positive,wire", CASES, ids=IDS)
def test_agreeing_spellings_are_accepted(parent, mode_key, nvpair, alias, positive, wire):
    result, calls = create(parent, **{alias: True, mode_key: positive})
    assert not result.get("failed"), result.get("msg")
    assert sent(calls, nvpair) == wire


@pytest.mark.parametrize("parent,mode_key,nvpair,alias,positive,wire", CASES, ids=IDS)
@pytest.mark.parametrize("alias_value,mode_value", [(True, "no_change"), (False, None)])
def test_conflicting_spellings_are_refused_before_any_write(parent, mode_key, nvpair, alias, positive, wire,
                                                            alias_value, mode_value):
    mode_value = mode_value or positive
    result, calls = create(parent, **{alias: alias_value, mode_key: mode_value})
    assert result.get("failed")
    assert h.writes(calls) == []
    assert alias in result["msg"] and mode_key in result["msg"]
    assert "no change was sent" in result["msg"]


@pytest.mark.parametrize("parent,mode_key,nvpair,alias,positive,wire", CASES, ids=IDS)
@pytest.mark.parametrize("bad", ["true", 1, None])
def test_a_non_boolean_alias_is_refused_without_echoing_the_value(parent, mode_key, nvpair, alias, positive, wire, bad):
    result, calls = create(parent, **{alias: bad})
    assert result.get("failed") and h.writes(calls) == []
    assert alias in result["msg"] and "boolean" in result["msg"]
    assert "'true'" not in result["msg"]


@pytest.mark.parametrize("alias", ["ospf_bfd", "ospf_passive_interface"])
def test_the_alias_stays_refused_on_a_parent_that_never_registered_it(alias):
    # int_routed_host and int_vlan register only the mode keys. The key was refused there before 017 too.
    for parent in (h.ROUTED, h.SVI):
        result, calls = create(parent, **{alias: True})
        assert result.get("failed") and h.writes(calls) == []
        assert alias in result["msg"] and "not supported on this interface" in result["msg"]


def test_the_passive_alias_is_not_registered_on_a_loopback():
    result, calls = create(h.LOOPBACK, ospf_passive_interface=True)
    assert result.get("failed") and h.writes(calls) == []
    assert "ospf_passive_interface" in result["msg"]


def test_the_alias_table_names_only_registered_mode_keys():
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding

    for (parent, alias), (mode_key, positive) in GIE_OSPF_BOOLEAN_ALIASES.items():
        binding = resolve_binding(parent, mode_key)
        assert binding is not None and binding["type"] == "enum"
        assert positive in binding["valid_values"]
        assert resolve_binding(parent, alias) is None, "the alias must not also be a registered key"


def test_normalization_is_a_noop_for_a_profile_without_a_legacy_key():
    profile = {"mode": "subint", "ospf_bfd_mode": "disable", "ospf_cost": 5}
    out, reason = gie_normalize_ospf_aliases(h.SUBIF, profile)
    assert reason is None and out is profile
    assert profile == {"mode": "subint", "ospf_bfd_mode": "disable", "ospf_cost": 5}


# ------------------------------------------------------------------ gate
@pytest.mark.parametrize("parent,mode_key,nvpair,alias,positive,wire", CASES, ids=IDS)
@pytest.mark.parametrize("patch", ["4.3.1.0175006011", None, "4.3.1.0175006016"])
def test_an_explicit_mode_is_refused_before_any_write_without_the_017_declaration(
        parent, mode_key, nvpair, alias, positive, wire, patch):
    result, calls = h.run_configs(
        [h.cfg_for(parent, h.base_for(parent, **dict(CTX, **{mode_key: positive})))], "merged", patch_version=patch)
    assert result.get("failed") and h.writes(calls) == []
    # The engine names the first registered key it refuses; the OSPF context fields are gated too.
    assert "4.3.1.0175006017" in result["msg"] and "no change was sent" in result["msg"]


@pytest.mark.parametrize("parent,mode_key,nvpair,alias,positive,wire", CASES, ids=IDS)
def test_the_refusal_names_the_mode_key_when_it_is_the_only_gated_field(parent, mode_key, nvpair, alias, positive, wire):
    result, calls = h.run_configs(
        [h.cfg_for(parent, h.base_for(parent, **{mode_key: positive}))], "merged", patch_version="4.3.1.0175006011")
    assert result.get("failed") and h.writes(calls) == []
    assert mode_key in result["msg"] and "4.3.1.0175006017" in result["msg"]


@pytest.mark.parametrize("parent,mode_key,nvpair,alias,positive,wire", CASES, ids=IDS)
def test_the_alias_is_gated_like_the_mode_key(parent, mode_key, nvpair, alias, positive, wire):
    result, calls = h.run_configs(
        [h.cfg_for(parent, h.base_for(parent, **dict(CTX, **{alias: True})))], "merged",
        patch_version="4.3.1.0175006011")
    assert result.get("failed") and h.writes(calls) == []
    assert "4.3.1.0175006017" in result["msg"]


@pytest.mark.parametrize("parent,mode_key,nvpair,alias,positive,wire", CASES, ids=IDS)
def test_the_numeric_nd_release_path_keeps_its_admission(parent, mode_key, nvpair, alias, positive, wire):
    # The numeric-release mapping is NOT validated: 4.4.1 templates were not read. This pins only that
    # the existing admission precedence did not change, and what name the candidate would send.
    result, calls = h.run_configs(
        [h.cfg_for(parent, h.base_for(parent, **dict(CTX, **{mode_key: positive})))], "merged", patch_version="4.4.1")
    assert not result.get("failed"), result.get("msg")
    assert sent(calls, nvpair) == wire


# ------------------------------------------------------------------ repeat, comparison, preservation, omission
@pytest.mark.parametrize("parent,mode_key,nvpair,alias,positive,wire", CASES, ids=IDS)
def test_an_identical_repeat_sends_nothing(parent, mode_key, nvpair, alias, positive, wire):
    profile = h.base_for(parent, **dict(CTX, **{alias: True}))
    have = h.build_have(parent, **dict(CTX, **{mode_key: positive}))
    result, calls = h.run(profile, "merged", have=have, parent=parent)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [], "the boolean alias must compare equal to the stored enable"
    assert not result.get("changed")


@pytest.mark.parametrize("parent,mode_key,nvpair,alias,positive,wire", CASES, ids=IDS)
def test_a_stored_explicit_negative_differs_from_the_alias_false(parent, mode_key, nvpair, alias, positive, wire):
    negative = "no_passive" if mode_key == "ospf_passive_mode" else "disable"
    profile = h.base_for(parent, **dict(CTX, **{alias: False}))
    have = h.build_have(parent, **dict(CTX, **{mode_key: negative}))
    result, calls = h.run(profile, "merged", have=have, parent=parent)
    assert not result.get("failed"), result.get("msg")
    assert sent(calls, nvpair) == "noChange", "false asks for no override, which is not the stored explicit negative"


@pytest.mark.parametrize("parent,mode_key,nvpair,alias,positive,wire", CASES, ids=IDS)
def test_merged_omission_preserves_the_stored_value(parent, mode_key, nvpair, alias, positive, wire):
    have = h.build_have(parent, **dict(CTX, **{mode_key: positive}))
    profile = h.base_for(parent, **dict(CTX, ospf_cost=77))
    result, calls = h.run(profile, "merged", have=have, parent=parent)
    assert not result.get("failed"), result.get("msg")
    values = [nv[nvpair] for nv in h.request_nvpairs(calls) if nvpair in nv]
    assert values and set(values) == {wire}, "an unrelated update must carry the stored value, not reset it"


@pytest.mark.parametrize("parent,mode_key,nvpair,alias,positive,wire", CASES, ids=IDS)
def test_replaced_omission_withdraws_to_no_change(parent, mode_key, nvpair, alias, positive, wire):
    have = h.build_have(parent, **dict(CTX, **{mode_key: positive}))
    profile = h.base_for(parent, **CTX)
    result, calls = h.run(profile, "replaced", have=have, parent=parent)
    assert not result.get("failed"), result.get("msg")
    assert sent(calls, nvpair) == "noChange"
