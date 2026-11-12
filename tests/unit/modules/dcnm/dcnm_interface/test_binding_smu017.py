"""SMU 4.3.1.0175006017 fields: first increment, states, routed port-channel PIM/BFD/OSPF and loopback EIGRP."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_by_nvpair
from unittest.mock import patch
from urllib.parse import parse_qs
from urllib.parse import urlsplit
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import BINDING_TABLE

from .helpers import binding_harness as h
from .helpers.role_reset import nvpairs_of_reset
from .helpers.role_reset import reset_policies
from .helpers.role_reset import run as f2_run
from .helpers.role_reset import _as_have
from .helpers.role_reset import _deploys
from .helpers.role_reset import _emitted
from .helpers.role_reset import _have_for
from .helpers.role_reset import _run as _smu017_states_run


# ====================================================================================================
# Formerly test_gie_smu017_batch1.py
# SMU 4.3.1.0175006017 new interface fields, first increment (registry slice 0b_37).
#
#     int_routed_host  CDP_ENABLE                  enable_cdp                          reset "true"
#     int_routed_host  evpnMultisiteDciTracking    enable_evpn_multisite_dci_tracking  reset "false"
#     int_routed_host  ospfRetransmitInterval      ospf_retransmit_interval            reset "" (OSPF-gated)
#     int_access_host  loggingEventPortLinkStatus  logging_event_port_link_status      reset "false"
#     int_subif        pimBfdInstance              enable_pim_bfd_instance             reset "false"
#
# Real main() through helpers/binding_harness: only inventory, transport and sleep are mocked, and every HAVE is the
# payload the module itself emits for a public profile. The expected values come from the 017 template bodies cited in
# the slice (defaults and the branches that create or delete each child or line), not from the table under test. None of
# this is measured on a controller or a device.
# ====================================================================================================
ROUTED_OFF = dict(h.BASE_ROUTED, enable_ospf=False)
# No other registered key: a refusal or a transport can only come from the field under test.
ROUTED_PLAIN = {k: v for k, v in h.BASE_ROUTED.items() if k not in ("enable_ospf", "ospf_area_id")}
OSPF_ON = {**h.BASE_ROUTED, **h.OSPF_CTX}

# (parent, public key, nvPair, applied public value, applied wire value, template default wire value, base profile)
ROWS = [
    (h.ROUTED, "enable_cdp", "CDP_ENABLE", False, "false", "true", ROUTED_OFF),
    (h.ROUTED, "enable_evpn_multisite_dci_tracking", "evpnMultisiteDciTracking", True, "true", "false", ROUTED_OFF),
    (h.ROUTED, "ospf_retransmit_interval", "ospfRetransmitInterval", 9, "9", "", OSPF_ON),
    (h.ACCESS, "logging_event_port_link_status", "loggingEventPortLinkStatus", True, "true", "false", h.BASE_ACCESS),
    (h.SUBIF, "enable_pim_bfd_instance", "pimBfdInstance", True, "true", "false", h.BASE_SUBIF),
]
IDS = ["%s::%s" % (p.replace("int_", ""), k) for p, k, *_rest in ROWS]
BOOL_ROWS = [r for r in ROWS if isinstance(r[3], bool)]
BOOL_IDS = [i for i, r in zip(IDS, ROWS) if isinstance(r[3], bool)]


def _parent_arg(parent):
    return parent if parent in h.NON_ETH_PARENTS else None


def _run(parent, profile, state, have=None, **kw):
    return h.run(profile, state, have=have, parent=_parent_arg(parent), **kw)


def _sent(calls, nvpair):
    values = [nv[nvpair] for nv in h.request_nvpairs(calls) if nvpair in nv]
    return values


def _have(parent, base, key=None, value=None):
    extra = dict(base)
    if key is not None:
        extra[key] = value
    return h.build_have(parent, **extra)


# ------------------------------------------------------------------ the rows are what the 017 bodies declare
@pytest.mark.parametrize("parent,key,nvpair,applied,wire,default,base", ROWS, ids=IDS)
def test_the_row_matches_the_template_contract(parent, key, nvpair, applied, wire, default, base):
    b = resolve_binding(parent, key)
    assert b is not None and b["parent_nvpair"] == nvpair and b["mechanism"] == "passthrough"
    assert b["reset_wire"] == default, "the reset is the template default whose branch removes the line"
    assert resolve_by_nvpair(parent, nvpair) is b


def test_dependencies_follow_the_bodies():
    rt = resolve_binding(h.ROUTED, "ospf_retransmit_interval")
    assert rt["inert_when"] == {"nvpair": "ospf", "value": "false", "strict": True}
    assert (rt["min_value"], rt["max_value"]) == (1, 65535)
    for parent, key in ((h.ROUTED, "enable_cdp"), (h.ROUTED, "enable_evpn_multisite_dci_tracking"),
                        (h.ACCESS, "logging_event_port_link_status"), (h.SUBIF, "enable_pim_bfd_instance")):
        assert "inert_when" not in resolve_binding(parent, key), key
    # retirement markers computed by the generator from the parent declarations
    for nvpair in ("CDP_ENABLE", "evpnMultisiteDciTracking", "ospfRetransmitInterval"):
        assert resolve_by_nvpair(h.ROUTED, nvpair).get("dropped_on_policy_change") is True
    assert resolve_by_nvpair(h.ACCESS, "loggingEventPortLinkStatus").get("cleared_on_change_to") == (h.ROUTED, h.TRUNK)
    assert not resolve_by_nvpair(h.SUBIF, "pimBfdInstance").get("dropped_on_policy_change")


# ------------------------------------------------------------------ merged / replaced / repeat, real main()
@pytest.mark.parametrize("parent,key,nvpair,applied,wire,default,base", ROWS, ids=IDS)
def test_merged_sets_the_wire_value(parent, key, nvpair, applied, wire, default, base):
    result, calls = _run(parent, dict(base, **{key: applied}), "merged")
    assert not result.get("failed"), result.get("msg")
    assert _sent(calls, nvpair) == [wire]


@pytest.mark.parametrize("parent,key,nvpair,applied,wire,default,base", ROWS, ids=IDS)
def test_merged_preserves_an_omitted_value(parent, key, nvpair, applied, wire, default, base):
    have = _have(parent, base, key, applied)
    assert have[0]["interfaces"][0]["nvPairs"][nvpair] == wire
    result, calls = _run(parent, dict(base, description="changed"), "merged", have=have)
    assert not result.get("failed"), result.get("msg")
    # The description change sends a full replacement of the interface, so the stored value must travel in it.
    assert h.writes(calls), "the description change must produce a modify"
    assert _sent(calls, nvpair) == [wire], "an omitted field must keep the controller value in the modify"


@pytest.mark.parametrize("parent,key,nvpair,applied,wire,default,base", ROWS, ids=IDS)
@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_omission_under_replaced_or_overridden_withdraws_to_the_template_default(
        state, parent, key, nvpair, applied, wire, default, base):
    have = _have(parent, base, key, applied)
    configs = [h.cfg_for(parent, dict(base))] if parent in h.NON_ETH_PARENTS else [h.cfg(h.IF_A, dict(base))]
    result, calls = h.run_configs(configs, state, have)
    assert not result.get("failed"), result.get("msg")
    assert default in _sent(calls, nvpair), "the withdrawal did not reach the request"
    assert any(nv.get(nvpair) == default for nv in h.diff_nvpairs(result)), "the withdrawal is not reported"


@pytest.mark.parametrize("parent,key,nvpair,applied,wire,default,base", ROWS, ids=IDS)
def test_repeating_the_same_request_writes_nothing(parent, key, nvpair, applied, wire, default, base):
    profile = dict(base, **{key: applied})
    have = _have(parent, base, key, applied)
    assert have[0]["interfaces"][0]["nvPairs"][nvpair] == wire, "the HAVE must carry the field, or nothing is repeated"
    for state in ("merged", "replaced"):
        result, calls = _run(parent, profile, state, have=have)
        assert not result.get("failed"), result.get("msg")
        assert h.writes(calls) == [], (state, h.writes(calls))


@pytest.mark.parametrize("parent,key,nvpair,applied,wire,default,base", BOOL_ROWS, ids=BOOL_IDS)
def test_false_and_absent_are_different_requests(parent, key, nvpair, applied, wire, default, base):
    """Absent sends nothing for the field on a create; an explicit value is always transmitted."""
    _r, absent_calls = _run(parent, dict(base), "merged")
    assert _sent(absent_calls, nvpair) == []
    for value in (True, False):
        result, calls = _run(parent, dict(base, **{key: value}), "merged")
        assert not result.get("failed"), result.get("msg")
        assert _sent(calls, nvpair) == [str(value).lower()]


# ------------------------------------------------------------------ input validation, before any write
@pytest.mark.parametrize("value", [0, 65536, "abc"])
def test_retransmit_interval_out_of_range_or_not_an_integer_is_refused(value):
    result, calls = _run(h.ROUTED, dict(OSPF_ON, ospf_retransmit_interval=value), "merged")
    assert result.get("failed") and "'ospf_retransmit_interval' must be a native integer (range 1..65535)" in result["msg"]
    assert h.writes(calls) == []


def test_retransmit_interval_with_ospf_disabled_is_refused():
    """The body refuses an OSPF option while ospf is false (strict gate)."""
    result, calls = _run(h.ROUTED, dict(ROUTED_OFF, ospf_retransmit_interval=9), "merged")
    assert result.get("failed") and "ospf_retransmit_interval (needs enable_ospf)" in result["msg"], result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("parent,key,nvpair,applied,wire,default,base", BOOL_ROWS, ids=BOOL_IDS)
def test_a_string_for_a_boolean_is_refused(parent, key, nvpair, applied, wire, default, base):
    result, calls = _run(parent, dict(base, **{key: "yes"}), "merged")
    assert result.get("failed") and "'%s' must be a native boolean" % key in result["msg"], result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("patch_version", [None, "4.3.1.0175006011"])
def test_the_fields_need_the_supported_patch_version(patch_version):
    result, calls = _run(h.ROUTED, dict(ROUTED_PLAIN, enable_evpn_multisite_dci_tracking=True), "merged",
                         patch_version=patch_version)
    assert result.get("failed") and result["msg"].startswith(
        "'enable_evpn_multisite_dci_tracking' requires caller-supplied patch_version"), result.get("msg")
    assert h.writes(calls) == []


def test_a_numeric_nd_release_is_admitted():
    result, calls = _run(h.ROUTED, dict(ROUTED_PLAIN, enable_evpn_multisite_dci_tracking=True), "merged",
                         patch_version="4.4.1")
    assert not result.get("failed"), result.get("msg")
    assert _sent(calls, "evpnMultisiteDciTracking") == ["true"]


# ------------------------------------------------------------------ enable_cdp: registered on routed, native elsewhere
def test_enable_cdp_is_registered_but_not_generically_guarded():
    assert "enable_cdp" in gie_engine.GIE_NATIVE_ELSEWHERE_KEYS
    assert "enable_cdp" not in gie_engine.gie_guarded_keys()
    assert gie_engine.gie_invalid_parent_key(h.TRUNK, ["mode", "enable_cdp"]) is None


@pytest.mark.parametrize("profile", [dict(h.BASE_TRUNK, enable_cdp=False), dict(h.BASE_ACCESS, enable_cdp=False)],
                         ids=["trunk", "access"])
def test_native_parents_keep_the_native_cdp_path(profile):
    result, calls = h.run(profile, "merged")
    assert not result.get("failed"), result.get("msg")
    assert _sent(calls, "CDP_ENABLE") == [False], "the native builder writes the native bool, as before"


def test_routed_cdp_without_the_supported_patch_is_refused_not_silently_dropped():
    result, calls = _run(h.ROUTED, dict(ROUTED_OFF, enable_cdp=False), "merged", patch_version=None)
    assert result.get("failed") and "enable_cdp" in result["msg"]
    assert h.writes(calls) == []


# ------------------------------------------------------------------ retirement: role default reset (P1/P2/P3 paths)
LEAF_ROUTED = {**OSPF_ON, "enable_cdp": False, "enable_evpn_multisite_dci_tracking": True, "ospf_retransmit_interval": 9}


@pytest.mark.parametrize("state", ["deleted", "overridden"])
def test_leaf_reset_of_a_routed_port_drops_the_three_routed_fields(state):
    """P1: int_routed_host children leave with the policy; nothing is written into int_trunk_host."""
    have = h.build_have(h.ROUTED, **LEAF_ROUTED)
    result, calls = f2_run(state, have, "leaf")
    assert not result.get("failed"), result.get("msg")
    assert reset_policies(calls)[0]["policy"] == h.TRUNK
    nv = nvpairs_of_reset(calls)
    assert not {"evpnMultisiteDciTracking", "ospfRetransmitInterval"} & set(nv)
    # CDP_ENABLE is a native trunk nvPair: the destination default carries its own value (CDP on), not the source's
    assert nv.get("CDP_ENABLE") in (None, True, "true")


@pytest.mark.parametrize("state", ["deleted", "overridden"])
def test_border_reset_of_a_routed_port_sends_each_template_default(state):
    """Same parent: each field takes its own reset; ospf is turned off, so the retransmit interval is cleared."""
    have = h.build_have(h.ROUTED, **LEAF_ROUTED)
    result, calls = f2_run(state, have, "border")
    assert not result.get("failed"), result.get("msg")
    nv = nvpairs_of_reset(calls)
    assert reset_policies(calls)[0]["policy"] == h.ROUTED
    assert (nv["CDP_ENABLE"], nv["evpnMultisiteDciTracking"], nv["ospfRetransmitInterval"]) == ("true", "false", "")


@pytest.mark.parametrize("state", ["deleted", "overridden"])
def test_border_reset_of_an_access_port_leaves_logging_to_the_routed_stanza(state):
    """P2: the inline line is not part of the routed stanza; the routed payload carries no access key."""
    have = h.build_have(h.ACCESS, **dict(h.BASE_ACCESS, logging_event_port_link_status=True))
    assert have[0]["interfaces"][0]["nvPairs"]["loggingEventPortLinkStatus"] == "true"
    result, calls = f2_run(state, have, "border")
    assert not result.get("failed"), result.get("msg")
    assert reset_policies(calls)[0]["policy"] == h.ROUTED
    assert "loggingEventPortLinkStatus" not in nvpairs_of_reset(calls)


@pytest.mark.parametrize("state", ["deleted", "overridden"])
def test_leaf_reset_of_an_access_port_with_logging_on_goes_to_trunk(state):
    """The controller removes the line with the access -> trunk policy change (measured); one reset, no access key.
    The identity, request and control-interface cases are in test_binding_role_resets.py."""
    have = h.build_have(h.ACCESS, **dict(h.BASE_ACCESS, logging_event_port_link_status=True))
    result, calls = f2_run(state, have, "leaf")
    assert not result.get("failed"), result.get("msg")
    assert reset_policies(calls)[0]["policy"] == h.TRUNK
    assert "loggingEventPortLinkStatus" not in nvpairs_of_reset(calls)


def test_leaf_reset_of_an_access_port_with_logging_off_proceeds():
    have = h.build_have(h.ACCESS, **dict(h.BASE_ACCESS, logging_event_port_link_status=False))
    assert have[0]["interfaces"][0]["nvPairs"]["loggingEventPortLinkStatus"] == "false"
    result, calls = f2_run("deleted", have, "leaf")
    assert not result.get("failed"), result.get("msg")
    assert reset_policies(calls)[0]["policy"] == h.TRUNK


def test_deleting_a_subinterface_with_pim_bfd_instance_on_deletes_the_object():
    have = h.build_have(h.SUBIF, **dict(h.BASE_SUBIF, enable_pim_bfd_instance=True))
    result, calls = h.run_configs([{"name": h.IF_SUB, "type": "sub_int", "switch": [h.SWITCH_IP]}], "deleted", have)
    assert not result.get("failed"), result.get("msg")
    paths = [c["path"] for c in h.writes(calls)]
    assert any("delete" in p.lower() for p in paths) and not any("modify" in p for p in paths), paths


# ====================================================================================================
# Formerly test_gie_smu017_batch1_states.py
# SMU 017 batch-1 fields (registry slice 0b_37): the five-state contract that test_binding_smu017.py does not cover.
#
#     merged      explicit update of an existing value
#     replaced    explicit update with the other fields retained; repeat after withdrawal; OSPF gate on and off
#     overridden  a retained interface beside a control, an interface left out of the desired set (role-default reset and
#                 subinterface deletion), the scope of the emitted identities, repeat over the resulting state
#     deleted     repeat over a port already at its role default and over a removed subinterface; an unrelated interface
#                 left untouched
#     query       real main() with controller-shaped responses carrying the five nvPairs: raw response, identity, values,
#                 no write and no deploy
#
# Real main() through helpers/binding_harness; only inventory, transport and sleep are mocked. Every HAVE is the payload the
# module itself emits for a public profile on the named interface. Values are synthetic. Nothing here is live evidence.
# ====================================================================================================
SMU017_STATES_OSPF_ON = {**h.BASE_ROUTED, **h.OSPF_CTX}
SMU017_STATES_ROUTED_OFF = {**h.BASE_ROUTED, "enable_ospf": False}
ROUTED_SET = {**SMU017_STATES_OSPF_ON, "enable_cdp": False, "enable_evpn_multisite_dci_tracking": True, "ospf_retransmit_interval": 10}
ACCESS_SET = {**h.BASE_ACCESS, "logging_event_port_link_status": True}
SUB_SET = {**h.BASE_SUBIF, "enable_pim_bfd_instance": True}
FIELDS = ("CDP_ENABLE", "evpnMultisiteDciTracking", "ospfRetransmitInterval", "loggingEventPortLinkStatus",
          "pimBfdInstance")
IF_CTL = "Ethernet1/40"
IF_SUB2 = "Ethernet1/31.3002"


def _nv(have):
    return have[0]["interfaces"][0]["nvPairs"]


# ====================================================================================================== merged
@pytest.mark.parametrize("profile,changes,expected", [
    (ROUTED_SET, {"enable_cdp": True, "ospf_retransmit_interval": 20},
     {"CDP_ENABLE": "true", "evpnMultisiteDciTracking": "true", "ospfRetransmitInterval": "20"}),
    (ROUTED_SET, {"enable_evpn_multisite_dci_tracking": False},
     {"CDP_ENABLE": "false", "evpnMultisiteDciTracking": "false", "ospfRetransmitInterval": "10"}),
    (ACCESS_SET, {"logging_event_port_link_status": False}, {"loggingEventPortLinkStatus": "false"}),
    (SUB_SET, {"enable_pim_bfd_instance": False}, {"pimBfdInstance": "false"}),
], ids=["routed_cdp_true_and_interval", "routed_dci_false", "access_logging_false", "subif_pim_bfd_false"])
@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_explicit_update_sends_the_new_value_and_keeps_the_other_fields(state, profile, changes, expected):
    """An explicit change is sent; the other new fields keep their values in the same request."""
    iftype = "sub_int" if profile is SUB_SET else "eth"
    name = h.IF_SUB if profile is SUB_SET else h.IF_A
    have = _have_for(name, profile, iftype)
    result, calls = h.run_configs([h.cfg(name, {**profile, **changes}, iftype=iftype)], state, have)
    assert not result.get("failed"), result.get("msg")
    emitted = _emitted(calls)
    assert list(emitted) == [(h.SERIAL, name)]
    nv = emitted[(h.SERIAL, name)][1]
    assert {k: nv.get(k) for k in expected} == expected
    assert nv.get("DESC") == profile["description"], "an unrelated retained setting changed"


def test_merged_omission_carries_the_stored_values_into_the_modify():
    """The request is a full replacement of the interface: the omitted fields must travel with their stored values."""
    have = _have_for(h.IF_A, ROUTED_SET)
    result, calls = h.run_configs([h.cfg(h.IF_A, {**SMU017_STATES_OSPF_ON, "description": "changed"})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _emitted(calls)[(h.SERIAL, h.IF_A)][1]
    assert (nv["CDP_ENABLE"], nv["evpnMultisiteDciTracking"], nv["ospfRetransmitInterval"]) == ("false", "true", "10")
    assert nv["DESC"] == "changed"


# ====================================================================================================== replaced
def test_replaced_with_ospf_disabled_clears_the_interval_and_keeps_the_others():
    have = _have_for(h.IF_A, ROUTED_SET)
    profile = {**SMU017_STATES_ROUTED_OFF, "enable_cdp": False, "enable_evpn_multisite_dci_tracking": True}
    result, calls = h.run_configs([h.cfg(h.IF_A, profile)], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = _emitted(calls)[(h.SERIAL, h.IF_A)][1]
    assert (nv["ospf"], nv["ospfRetransmitInterval"]) == ("false", "")
    assert (nv["CDP_ENABLE"], nv["evpnMultisiteDciTracking"]) == ("false", "true")


def test_replaced_setting_the_interval_with_ospf_disabled_is_refused_before_any_write():
    have = _have_for(h.IF_A, ROUTED_SET)
    result, calls = h.run_configs([h.cfg(h.IF_A, {**SMU017_STATES_ROUTED_OFF, "ospf_retransmit_interval": 10})], "replaced", have)
    assert result.get("failed") and "ospf_retransmit_interval (needs enable_ospf)" in result["msg"], result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("name,profile,base,iftype", [
    (h.IF_A, ROUTED_SET, SMU017_STATES_OSPF_ON, "eth"), (h.IF_A, ACCESS_SET, h.BASE_ACCESS, "eth"),
    (h.IF_SUB, SUB_SET, h.BASE_SUBIF, "sub_int"),
], ids=["routed", "access", "subif"])
@pytest.mark.parametrize("state", ["replaced", "merged"])
def test_repeat_after_withdrawal_writes_nothing(state, name, profile, base, iftype):
    have = _have_for(name, profile, iftype)
    result, calls = h.run_configs([h.cfg(name, dict(base), iftype=iftype)], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    policy, nv = _emitted(calls)[(h.SERIAL, name)]
    withdrawn = _as_have(policy, name, nv)
    result, calls = h.run_configs([h.cfg(name, dict(base), iftype=iftype)], state, withdrawn)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


# ====================================================================================================== overridden
def test_overridden_retained_interface_withdraws_only_its_own_omitted_fields():
    """(a) Retained: the interface stays in the desired set without the fields. The control is retained unchanged."""
    have = _have_for(h.IF_A, ROUTED_SET) + _have_for(IF_CTL, ACCESS_SET)
    configs = [h.cfg(h.IF_A, dict(SMU017_STATES_OSPF_ON)), h.cfg(IF_CTL, dict(ACCESS_SET))]
    result, calls = _smu017_states_run(configs, "overridden", have)
    assert not result.get("failed"), result.get("msg")
    emitted = _emitted(calls)
    assert list(emitted) == [(h.SERIAL, h.IF_A)], "the retained control must not be written"
    policy, nv = emitted[(h.SERIAL, h.IF_A)]
    assert policy == h.ROUTED
    assert (nv["CDP_ENABLE"], nv["evpnMultisiteDciTracking"], nv["ospfRetransmitInterval"]) == ("true", "false", "")


@pytest.mark.parametrize("role,expected_policy", [("leaf", h.TRUNK), ("border", h.ROUTED)])
def test_overridden_interface_left_out_is_retired_to_the_role_default(role, expected_policy):
    """(b) Retirement: the routed port is absent from the desired set; only the control is listed and kept."""
    have = _have_for(h.IF_A, ROUTED_SET) + _have_for(IF_CTL, ACCESS_SET)
    result, calls = _smu017_states_run([h.cfg(IF_CTL, dict(ACCESS_SET))], "overridden", have, role=role)
    assert not result.get("failed"), result.get("msg")
    emitted = _emitted(calls)
    assert list(emitted) == [(h.SERIAL, h.IF_A)], emitted.keys()
    policy, nv = emitted[(h.SERIAL, h.IF_A)]
    assert policy == expected_policy
    if role == "leaf":
        assert not {"evpnMultisiteDciTracking", "ospfRetransmitInterval"} & set(nv)
    else:
        assert (nv["CDP_ENABLE"], nv["evpnMultisiteDciTracking"], nv["ospfRetransmitInterval"], nv["ospf"]) == (
            "true", "false", "", "false")
    assert _deploys(calls) == [(h.SERIAL, h.IF_A)]
    # repeat over the resulting state: the retired port now holds its reset payload
    after = _as_have(policy, h.IF_A, nv) + _have_for(IF_CTL, ACCESS_SET)
    result, calls = _smu017_states_run([h.cfg(IF_CTL, dict(ACCESS_SET))], "overridden", after, role=role)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_overridden_subinterface_left_out_is_deleted_and_the_retained_one_kept():
    have = _have_for(h.IF_SUB, SUB_SET, "sub_int") + _have_for(IF_SUB2, {**SUB_SET, "vlan": 3002}, "sub_int")
    result, calls = _smu017_states_run([h.cfg(IF_SUB2, {**SUB_SET, "vlan": 3002}, iftype="sub_int")], "overridden", have)
    assert not result.get("failed"), result.get("msg")
    writes = h.writes(calls)
    deleted = [e.get("ifName") for c in writes if "delete" in c["path"].lower() for e in (c["payload"] or [])]
    assert deleted == [h.IF_SUB], [(c["path"], c["payload"]) for c in writes]
    assert not any("modify" in c["path"] for c in writes)
    # repeat: the deleted subinterface is gone
    result, calls = _smu017_states_run([h.cfg(IF_SUB2, {**SUB_SET, "vlan": 3002}, iftype="sub_int")], "overridden",
                                       _have_for(IF_SUB2, {**SUB_SET, "vlan": 3002}, "sub_int"))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


# ====================================================================================================== deleted
def test_deleted_resets_only_the_named_port():
    have = _have_for(h.IF_A, ROUTED_SET) + _have_for(IF_CTL, ACCESS_SET)
    result, calls = _smu017_states_run([{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}], "deleted", have, role="border")
    assert not result.get("failed"), result.get("msg")
    emitted = _emitted(calls)
    assert list(emitted) == [(h.SERIAL, h.IF_A)]
    assert _deploys(calls) == [(h.SERIAL, h.IF_A)]


@pytest.mark.parametrize("role", ["leaf", "border"])
def test_deleted_repeat_over_a_port_already_at_its_default_writes_nothing(role):
    have = _have_for(h.IF_A, ROUTED_SET)
    cfg = [{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}]
    result, calls = _smu017_states_run(cfg, "deleted", have, role=role)
    assert not result.get("failed"), result.get("msg")
    policy, nv = _emitted(calls)[(h.SERIAL, h.IF_A)]
    result, calls = _smu017_states_run(cfg, "deleted", _as_have(policy, h.IF_A, nv), role=role)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_deleted_repeat_over_a_removed_subinterface_writes_nothing():
    result, calls = _smu017_states_run([{"name": h.IF_SUB, "type": "sub_int", "switch": [h.SWITCH_IP]}], "deleted", [])
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


# ====================================================================================================== query
def _controller_shaped(have, defaults):
    """The controller returns every nvPair its template declares; fill the template defaults the module omitted."""
    have = copy.deepcopy(have)
    nv = _nv(have)
    for key, value in defaults.items():
        nv.setdefault(key, value)
    return have


def _query_transport(store, writes):
    def factory(calls, _have):
        def send(mod, method, path, payload=None):
            calls.append({"method": method, "path": path, "payload": payload})
            if method != "GET":
                writes.append((method, path))
                return {"RETURN_CODE": 500, "MESSAGE": "query must not write", "DATA": {}}
            q = {k: v[0] for k, v in parse_qs(urlsplit(path).query).items()}
            if "accessmode" in path.lower():
                return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {"readonly": False}}
            if urlsplit(path).path.endswith("/rest/interface") and "ifName" in q:
                return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [
                    copy.deepcopy(p) for p in store for i in p["interfaces"]
                    if i["ifName"] == q["ifName"] and i["serialNumber"] == q.get("serialNumber")]}
            writes.append((method, path))
            return {"RETURN_CODE": 500, "MESSAGE": "unexpected read", "DATA": {}}
        return send
    return factory


ROUTED_DEFAULTS = {"CDP_ENABLE": "true", "evpnMultisiteDciTracking": "false", "ospfRetransmitInterval": ""}


@pytest.mark.parametrize("profile,name,iftype,defaults,expected", [
    (ROUTED_SET, h.IF_A, "eth", ROUTED_DEFAULTS,
     {"CDP_ENABLE": "false", "evpnMultisiteDciTracking": "true", "ospfRetransmitInterval": "10", "ospfCost": None}),
    ({**SMU017_STATES_OSPF_ON, "ospf_cost": 40}, h.IF_A, "eth", ROUTED_DEFAULTS,
     {"CDP_ENABLE": "true", "evpnMultisiteDciTracking": "false", "ospfRetransmitInterval": "", "ospfCost": "40"}),
    (ACCESS_SET, h.IF_A, "eth", {"loggingEventPortLinkStatus": "false"}, {"loggingEventPortLinkStatus": "true"}),
    (h.BASE_ACCESS, h.IF_A, "eth", {"loggingEventPortLinkStatus": "false"}, {"loggingEventPortLinkStatus": "false"}),
    (SUB_SET, h.IF_SUB, "sub_int", {"pimBfdInstance": "false"}, {"pimBfdInstance": "true"}),
    (h.BASE_SUBIF, h.IF_SUB, "sub_int", {"pimBfdInstance": "false"}, {"pimBfdInstance": "false"}),
], ids=["routed_non_default", "routed_defaults_with_ospf_cost_control", "access_true", "access_default_false",
        "subif_true", "subif_default_false"])
def test_query_returns_the_controller_nvpairs_unchanged(profile, name, iftype, defaults, expected):
    """state: query hands back the controller's DATA as-is (raw nvPairs, not profile keys), for the named interface only."""
    target = _controller_shaped(_have_for(name, profile, iftype), defaults)
    other = _controller_shaped(_have_for(IF_CTL, ROUTED_SET), ROUTED_DEFAULTS)
    writes = []
    with patch.object(h, "_transport", _query_transport(target + other, writes)):
        result, calls = h.run_configs([{"name": name, "switch": [h.SWITCH_IP]}], "query", [])
    assert not result.get("failed"), result.get("msg")
    assert writes == [] and h.writes(calls) == []
    response = result["response"]
    assert response == target, "query must return the controller entry unchanged"
    assert result["diff"][0]["query"] == target
    intf = response[0]["interfaces"][0]
    assert (intf["serialNumber"], intf["ifName"]) == (h.SERIAL, name)
    assert {k: intf["nvPairs"].get(k) for k in expected} == expected
    assert not result.get("changed")


# ====================================================================================================== native CDP
@pytest.mark.parametrize("patch_version", [None, "4.3.1.0175006011"])
@pytest.mark.parametrize("profile", [{**h.BASE_TRUNK, "enable_cdp": False},
                                     {**{k: v for k, v in h.BASE_ACCESS.items() if k not in ("enable_qos", "qos_policy")},
                                      "enable_cdp": False}], ids=["trunk", "access"])
def test_native_cdp_keeps_its_version_behaviour(profile, patch_version):
    """Native enable_cdp needs no patch_version on the profiles that already served it, exactly as on 68a30199."""
    result, calls = h.run(profile, "merged", patch_version=patch_version)
    assert not result.get("failed"), result.get("msg")
    assert [nv["CDP_ENABLE"] for nv in h.request_nvpairs(calls) if "CDP_ENABLE" in nv] == [False]


# ====================================================================================================
# Formerly test_gie_smu017_l3po_pim_bfd.py
# SMU 4.3.1.0175006017 PIM BFD instance on the routed port-channel (registry slice 0b_39).
#
#     int_l3_port_channel  pimBfdInstance  enable_pim_bfd_instance  reset "false"
#
# `type: pc`, `mode: l3` selects int_l3_port_channel (pol_types "pc_l3"). The 017 body declares pimBfdInstance
# (L156), creates pim_bfd_instance_interface when it is "true" (L1215) and has no else branch: every add() first deletes
# all PTIs of the port-channel (L1015), so "false" leaves no line. The body does not gate the field on PIM sparse mode,
# which slice 0b_41 registers on the same parent.
#
# ospfRetransmitInterval is not registered on this parent. The body refuses it unless `ospf` is true with a tag and an
# area, and no public key reaches those nvPairs on a routed port-channel; the last tests pin that refusal.
#
# Real main() through helpers/binding_harness: only inventory, transport and sleep are mocked, and every HAVE is the payload
# the module itself emits for a public profile. Values are synthetic. Nothing here is live evidence.
# ====================================================================================================
L3PO = h.PC_L3
KEY, NVPAIR = "enable_pim_bfd_instance", "pimBfdInstance"
PO_A, PO_B = h.PC_A, "Port-channel302"
BASE = dict(h.BASE_PC_L3)
BFD_ON = {**BASE, KEY: True}
# Native nvPairs a field change must not disturb: membership, admin state, address, VRF, routing tag, MTU.
NATIVE = ("MEMBER_INTERFACES", "PC_MODE", "ADMIN_STATE", "IP", "PREFIX", "INTF_VRF", "ROUTING_TAG", "MTU", "DESC")


def _l3po_pim_bfd_emitted(calls):
    """Every interface of every write, as {(serial, ifName): (policy, nvPairs)}."""
    out = {}
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    for pol in found:
        for intf in pol["interfaces"]:
            key = (intf["serialNumber"], intf["ifName"])
            assert key not in out, ("identity written twice", key)
            out[key] = (pol["policy"], intf.get("nvPairs") or {})
    return out


def _only(calls, ifname=PO_A):
    emitted = _l3po_pim_bfd_emitted(calls)
    assert len(emitted) == 1, emitted.keys()
    key, (policy, nv) = next(iter(emitted.items()))
    assert policy == L3PO and key[0] == h.SERIAL and key[1].lower() == ifname.lower(), (key, policy)
    return nv


def _paths(calls):
    return [c["method"] + " " + c["path"].split("/rest/")[-1].split("?")[0] for c in h.writes(calls)]


def _po(profile, ifname=PO_A, **kw):
    return h.cfg(ifname, profile, iftype="pc", **kw)


def _l3po_pim_bfd_have(profile, ifname=PO_A):
    """The payload the module emits for `profile` on `ifname`, as the controller would return it."""
    result, calls = h.run_configs([_po(profile, ifname)], "replaced", [])
    assert not result.get("failed"), result.get("msg")
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    assert len(found) == 1 and found[0]["policy"] == L3PO, found
    have = copy.deepcopy(found)
    have[0]["interfaces"][0]["interfaceType"] = "INTERFACE_PORT_CHANNEL"
    have[0]["interfaces"][0]["fabricName"] = h.FABRIC
    return have


def _l3po_pim_bfd_as_have(nv, ifname=PO_A):
    return [{"policy": L3PO, "interfaces": [{"interfaceType": "INTERFACE_PORT_CHANNEL", "serialNumber": h.SERIAL,
                                             "ifName": ifname, "fabricName": h.FABRIC, "nvPairs": copy.deepcopy(nv)}]}]


def _native(nv):
    return {k: nv.get(k) for k in NATIVE}


# ------------------------------------------------------------------ the row is what the 017 body declares
def test_the_row_matches_the_017_l3_port_channel_contract():
    b = resolve_binding(L3PO, KEY)
    assert b is not None, "enable_pim_bfd_instance is not registered on int_l3_port_channel"
    assert (b["parent_nvpair"], b["type"], b["reset_wire"], b["mechanism"]) == (NVPAIR, "boolean", "false", "passthrough")
    assert (b["applicable_interface_type"], b["applicable_mode"]) == ("pc", "l3")
    assert resolve_by_nvpair(L3PO, NVPAIR) is b
    assert "inert_when" not in b, "the body does not gate pimBfdInstance on PIM sparse mode"


def test_the_public_key_and_reset_match_the_routed_and_subinterface_rows():
    for parent in (h.ROUTED, h.SUBIF):
        other = resolve_binding(parent, KEY)
        assert other["parent_nvpair"] == NVPAIR and other["reset_wire"] == "false", parent


def test_pim_bfd_has_no_dependency_on_the_other_pim_rows():
    """Sparse mode and DR priority are registered by slice 0b_41 (test_binding_smu017.py) and the
    OSPF family by slice 0b_40 (test_binding_smu017.py). None of them gates pimBfdInstance."""
    assert resolve_binding(L3PO, "enable_pim_sparse") is not None
    assert resolve_binding(L3PO, "pim_dr_priority") is not None
    assert "inert_when" not in resolve_binding(L3PO, KEY)


# ------------------------------------------------------------------ merged
def test_merged_create_sends_the_field_with_the_native_profile_and_deploys_it():
    result, calls = h.run_configs([_po(BFD_ON)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert nv[NVPAIR] == "true"
    assert (nv["MEMBER_INTERFACES"], nv["IP"], nv["PREFIX"], nv["PC_MODE"]) == (h.PC_MEMBER, "192.0.2.33", "30", "active")
    assert _paths(calls) == ["POST globalInterface", "POST globalInterface/deploy"], _paths(calls)


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_explicit_update_sends_false_and_keeps_the_native_values(state):
    have = _l3po_pim_bfd_have(BFD_ON)
    result, calls = h.run_configs([_po({**BFD_ON, KEY: False})], state, have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert nv[NVPAIR] == "false"
    assert _native(nv) == _native(have[0]["interfaces"][0]["nvPairs"])
    assert _paths(calls) == ["POST interface/modify", "POST globalInterface/deploy"], _paths(calls)


def test_merged_omission_carries_the_stored_value_into_another_change():
    have = _l3po_pim_bfd_have(BFD_ON)
    result, calls = h.run_configs([_po({**BASE, "description": "changed"})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert (nv[NVPAIR], nv["DESC"]) == ("true", "changed")
    assert nv["MEMBER_INTERFACES"] == h.PC_MEMBER


def test_explicit_false_differs_from_omission_under_merged():
    have = _l3po_pim_bfd_have(BFD_ON)
    result, calls = h.run_configs([_po({**BASE, KEY: False})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)[NVPAIR] == "false"
    result, calls = h.run_configs([_po(BASE)], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [], "omission under merged keeps the stored true and changes nothing"


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_repeat_of_the_stored_value_writes_nothing(state):
    result, calls = h.run_configs([_po(BFD_ON)], state, _l3po_pim_bfd_have(BFD_ON))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and not result.get("changed")


# ------------------------------------------------------------------ replaced
def test_replaced_omission_withdraws_the_field_and_keeps_the_native_values():
    have = _l3po_pim_bfd_have(BFD_ON)
    result, calls = h.run_configs([_po(BASE)], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert nv[NVPAIR] == "false"
    assert _native(nv) == _native(have[0]["interfaces"][0]["nvPairs"])
    assert _paths(calls) == ["POST interface/modify", "POST globalInterface/deploy"], _paths(calls)


@pytest.mark.parametrize("state", ["replaced", "merged"])
def test_repeat_after_withdrawal_writes_nothing_l3po_pim_bfd(state):
    result, calls = h.run_configs([_po(BASE)], "replaced", _l3po_pim_bfd_have(BFD_ON))
    assert not result.get("failed"), result.get("msg")
    withdrawn = _l3po_pim_bfd_as_have(_only(calls))
    result, calls = h.run_configs([_po(BASE)], state, withdrawn)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_replaced_without_the_field_on_a_port_channel_that_never_had_it_writes_nothing():
    result, calls = h.run_configs([_po(BASE)], "replaced", _l3po_pim_bfd_have(BASE))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_a_member_change_keeps_the_stored_field_under_merged_and_withdraws_it_under_replaced():
    """merged adds the new member to the stored ones (native port-channel behaviour); replaced sets the list."""
    have = _l3po_pim_bfd_have(BFD_ON)
    moved = {**BASE, "members": ["Ethernet1/49"]}
    result, calls = h.run_configs([_po(moved)], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert (sorted(nv["MEMBER_INTERFACES"].split(",")), nv[NVPAIR]) == (["Ethernet1/49", h.PC_MEMBER], "true")
    result, calls = h.run_configs([_po(moved)], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert (nv["MEMBER_INTERFACES"], nv[NVPAIR]) == ("Ethernet1/49", "false")


def test_admin_state_down_is_sent_with_the_field():
    result, calls = h.run_configs([_po({**BFD_ON, "admin_state": False})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert (nv["ADMIN_STATE"], nv[NVPAIR]) == ("false", "true")


@pytest.mark.parametrize("vrf", ["default", "PILOT-VRF"])
def test_default_and_non_default_vrf_carry_the_field_unchanged(vrf):
    result, calls = h.run_configs([_po({**BFD_ON, "int_vrf": vrf})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert (nv["INTF_VRF"], nv[NVPAIR]) == (vrf, "true")


# ------------------------------------------------------------------ invalid input, version gate, check mode
def test_a_non_boolean_value_is_refused_before_any_write():
    result, calls = h.run_configs([_po({**BASE, KEY: "maybe"})], "merged", [])
    assert result.get("failed") and KEY in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("patch_version", [None, "4.3.1.0175006011"], ids=["no_patch_version", "smu011"])
def test_the_field_needs_an_approved_patch_version(patch_version):
    result, calls = h.run_configs([_po(BFD_ON)], "merged", [], patch_version=patch_version)
    assert result.get("failed"), "a registered field was accepted without SMU 017 or ND >= 4.4.1"
    assert h.writes(calls) == []


@pytest.mark.parametrize("patch_version", [None, "4.3.1.0175006011"], ids=["no_patch_version", "smu011"])
def test_omission_under_a_closed_gate_resets_nothing(patch_version):
    """A disabled gate never invents a reset: replaced without the key leaves the stored value alone."""
    result, calls = h.run_configs([_po(BASE)], "replaced", _l3po_pim_bfd_have(BFD_ON), patch_version=patch_version)
    assert not result.get("failed"), result.get("msg")
    assert all(nv.get(NVPAIR) != "false" for _p, nv in _l3po_pim_bfd_emitted(calls).values())


def test_numeric_441_is_admitted():
    result, calls = h.run_configs([_po(BFD_ON)], "merged", [], patch_version="4.4.1")
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)[NVPAIR] == "true"


def test_check_mode_reports_the_change_and_writes_nothing():
    result, calls = h.run_configs([_po(BASE)], "replaced", _l3po_pim_bfd_have(BFD_ON), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and result.get("changed") is True


# ------------------------------------------------------------------ overridden and deleted
# interface/detail in the measured aggregate shape (NDFC 12.6.0.267): a user port-channel is INTERFACE_PORT_CHANNEL,
# not physical and deletable; each member is a physical INTERFACE_ETHERNET, not deletable, with an underlay policy whose
# source is its port-channel. The harness double answers every port-channel as a physical Ethernet port.
_ORIG = h._transport
MEM_A, MEM_B = h.PC_MEMBER, "Ethernet1/52"
MEMBER_POLICY = "int_l3_port_channel_member"
MARK, DEPLOY, MODIFY = "DELETE interface/markdelete", "POST globalInterface/deploy", "POST interface/modify"


def _measured_detail(calls, have):
    inner = _ORIG(calls, have)
    member_of = dict((i["ifName"].lower(), i["nvPairs"]["PRIMARY_INTF"])
                     for p in have if p["policy"] == MEMBER_POLICY for i in p["interfaces"])

    def send(mod, method, path, payload=None):
        resp = inner(mod, method, path, payload)
        if method == "GET" and "/interface/detail" in path and isinstance(resp.get("DATA"), list):
            for e in resp["DATA"]:
                name = str(e.get("ifName", ""))
                if name.lower() in member_of:
                    e.update(ifType="INTERFACE_ETHERNET", isPhysical="true", deletable=False, editAllowed=True,
                             underlayPolicies=[{"entityName": name, "source": member_of[name.lower()],
                                                "templateName": MEMBER_POLICY, "serialNumber": h.SERIAL}])
                elif name.lower().startswith("port-channel"):
                    e.update(ifType="INTERFACE_PORT_CHANNEL", isPhysical="false", deletable=True, editAllowed=True)
        return resp
    return send


def _member_have(member, po):
    return [{"policy": MEMBER_POLICY, "interfaces": [{
        "interfaceType": "INTERFACE_ETHERNET", "serialNumber": h.SERIAL, "ifName": member, "fabricName": h.FABRIC,
        "nvPairs": {"INTF_NAME": member, "PRIMARY_INTF": po.lower(), "ADMIN_STATE": "true", "DESC": "", "CONF": ""}}]}]


def _aggregate():
    """Po A and Po B with the field set, each with its own member."""
    return (_l3po_pim_bfd_have({**BFD_ON, "members": [MEM_A]}) + _l3po_pim_bfd_have({**BFD_ON, "members": [MEM_B]}, PO_B)
            + _member_have(MEM_A, PO_A) + _member_have(MEM_B, PO_B))


def _identities(calls):
    """Every write in order, as (request, sorted [serial, ifName(, policy)])."""
    out = []
    for c in h.writes(calls):
        kind = c["method"] + " " + c["path"].split("/rest/")[-1].split("?")[0]
        found = []
        h._collect_policies([c["payload"]], found)
        if found:
            ids = sorted([i["serialNumber"], i["ifName"], p["policy"]] for p in found for i in p["interfaces"])
        else:
            ids = sorted([e.get("serialNumber"), e.get("ifName")] for e in (c["payload"] or []) if isinstance(e, dict))
        out.append((kind, ids))
    return out


def _l3po_pim_bfd_run(configs, state, have):
    with patch.object(h, "_transport", _measured_detail):
        return h.run_configs(configs, state, have)


def test_overridden_retained_port_channel_withdraws_the_field_and_keeps_the_control():
    configs = [_po({**BASE, "members": [MEM_A]}), _po({**BFD_ON, "members": [MEM_B]}, PO_B)]
    result, calls = _l3po_pim_bfd_run(configs, "overridden", _aggregate())
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [(MODIFY, [[h.SERIAL, PO_A, L3PO]]), (DEPLOY, [[h.SERIAL, PO_A]])]
    nv = _only(calls)
    assert nv[NVPAIR] == "false" and nv["MEMBER_INTERFACES"] == MEM_A


def test_overridden_port_channel_left_out_is_deleted_and_the_retained_one_kept():
    """After the markdelete of Po A, the sweep also resets its former member to the role default. That reset is
    native port-channel behaviour (the same at the base, without the field); Po B and its member are never written."""
    result, calls = _l3po_pim_bfd_run([_po({**BFD_ON, "members": [MEM_B]}, PO_B)], "overridden", _aggregate())
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [
        (MARK, [[h.SERIAL, PO_A]]), (DEPLOY, [[h.SERIAL, PO_A]]),
        (MODIFY, [[h.SERIAL, MEM_A, h.ROUTED]]), (DEPLOY, [[h.SERIAL, MEM_A]]),
    ]
    retained = _l3po_pim_bfd_have({**BFD_ON, "members": [MEM_B]}, PO_B) + _member_have(MEM_B, PO_B)
    result, calls = _l3po_pim_bfd_run([_po({**BFD_ON, "members": [MEM_B]}, PO_B)], "overridden", retained)
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == []


def test_deleted_retires_the_port_channel_and_a_repeat_writes_nothing():
    target = [{"name": PO_A, "type": "pc", "switch": [h.SWITCH_IP]}]
    have = _l3po_pim_bfd_have({**BFD_ON, "members": [MEM_A]}) + _member_have(MEM_A, PO_A)
    result, calls = _l3po_pim_bfd_run(target, "deleted", have)
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [(MARK, [[h.SERIAL, PO_A]]), (DEPLOY, [[h.SERIAL, PO_A]])]
    result, calls = _l3po_pim_bfd_run(target, "deleted", [])
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == []


# ------------------------------------------------------------------ query
def _l3po_pim_bfd_query_transport(store, writes):
    def factory(calls, _have):
        def send(mod, method, path, payload=None):
            calls.append({"method": method, "path": path, "payload": payload})
            if method != "GET":
                writes.append((method, path))
                return {"RETURN_CODE": 500, "MESSAGE": "query must not write", "DATA": {}}
            q = {k: v[0] for k, v in parse_qs(urlsplit(path).query).items()}
            if "accessmode" in path.lower():
                return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {"readonly": False}}
            if urlsplit(path).path.endswith("/rest/interface") and "ifName" in q:
                return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [
                    copy.deepcopy(p) for p in store for i in p["interfaces"]
                    if i["ifName"].lower() == q["ifName"].lower() and i["serialNumber"] == q.get("serialNumber")]}
            writes.append((method, path))
            return {"RETURN_CODE": 500, "MESSAGE": "unexpected read", "DATA": {}}
        return send
    return factory


def test_query_returns_the_controller_nvpairs_unchanged_l3po_pim_bfd():
    target = _l3po_pim_bfd_have(BFD_ON)
    writes = []
    with patch.object(h, "_transport", _l3po_pim_bfd_query_transport(target + _l3po_pim_bfd_have(BASE, PO_B), writes)):
        result, calls = h.run_configs([{"name": PO_A, "switch": [h.SWITCH_IP]}], "query", [])
    assert not result.get("failed"), result.get("msg")
    assert writes == [] and h.writes(calls) == []
    assert result["response"] == target, "query must return the controller entry unchanged"
    assert result["response"][0]["interfaces"][0]["nvPairs"][NVPAIR] == "true"
    assert not result.get("changed")


# ------------------------------------------------------------------ unaffected controls and the OSPF boundary
def test_a_plain_l3_port_channel_payload_is_unchanged_by_the_new_row():
    result, calls = h.run_configs([_po(BASE)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    assert NVPAIR not in _only(calls)


@pytest.mark.parametrize("parent", [h.PC_TRUNK, h.PC_ACCESS])
def test_the_key_stays_refused_on_the_layer2_port_channels(parent):
    result, calls = h.run_configs([h.cfg_for(parent, {**h.base_for(parent), KEY: True})], "merged", [])
    assert result.get("failed") and KEY in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


def test_the_routed_ethernet_row_is_unchanged():
    result, calls = h.run_configs([h.cfg(h.IF_A, {**h.BASE_ROUTED, KEY: True})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    assert [(p["policy"], p["interfaces"][0]["nvPairs"][NVPAIR]) for p in found] == [(h.ROUTED, "true")]


def test_the_pim_bfd_field_and_the_ospf_family_travel_together():
    """The two increments on this parent are independent rows in one payload: setting both sends both."""
    prof = {**BFD_ON, "enable_ospf": True, "ospf_tag": "PILOT-OSPF", "ospf_area_id": "0.0.0.0"}
    result, calls = h.run_configs([_po(prof)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert (nv[NVPAIR], nv["ospf"], nv["ospfTag"], nv["OSPF_AREA_ID"]) == ("true", "true", "PILOT-OSPF", "0.0.0.0")


# ====================================================================================================
# Formerly test_gie_smu017_loopback_eigrp.py
# SMU 4.3.1.0175006017 loopback EIGRP fields (registry slice 0b_38).
#
#     int_loopback  eigrpIpv6Routing                   enable_eigrp_ipv6_routing               reset "false"
#     int_loopback  eigrpIpv4DistributeListPrefixList  eigrp_ipv4_distribute_list_prefix_list  reset ""
#     int_loopback  eigrpIpv4DistributeListDirection   eigrp_ipv4_distribute_list_direction    reset "out"
#     int_loopback  eigrpIpv6DistributeListPrefixList  eigrp_ipv6_distribute_list_prefix_list  reset ""
#     int_loopback  eigrpIpv6DistributeListDirection   eigrp_ipv6_distribute_list_direction    reset "out"
#
# The 4.3.1.0175006017 int_loopback body declares these five nvPairs with the declarations of the routed, subinterface
# and SVI parents (same types, length, pattern, enum and defaults). Its add() deletes every child of the interface and
# recreates only the selected ones, inside `if eigrpProcessTag != ""`, so a field set back to its default leaves no line.
#
# Real main() through helpers/binding_harness: only inventory, transport and sleep are mocked, and every HAVE is the payload
# the module itself emits for a public profile. Values are synthetic. Nothing here is live evidence.
# ====================================================================================================
LO = h.LOOPBACK
IF_LO2 = "loopback932"
EIGRP_ON = {**h.BASE_LOOPBACK, "eigrp_process_tag": "PILOT-EIGRP", "enable_eigrp_routing": True}
EIGRP_SET = {**EIGRP_ON, "enable_eigrp_ipv6_routing": True,
             "eigrp_ipv4_distribute_list_prefix_list": "PILOT-PL4", "eigrp_ipv4_distribute_list_direction": "in",
             "eigrp_ipv6_distribute_list_prefix_list": "PILOT-PL6", "eigrp_ipv6_distribute_list_direction": "in"}

# (public key, nvPair, applied public value, applied wire value, template default = reset wire)
LO_EIGRP_ROWS = [
    ("enable_eigrp_ipv6_routing", "eigrpIpv6Routing", True, "true", "false"),
    ("eigrp_ipv4_distribute_list_prefix_list", "eigrpIpv4DistributeListPrefixList", "PILOT-PL4", "PILOT-PL4", ""),
    ("eigrp_ipv4_distribute_list_direction", "eigrpIpv4DistributeListDirection", "in", "in", "out"),
    ("eigrp_ipv6_distribute_list_prefix_list", "eigrpIpv6DistributeListPrefixList", "PILOT-PL6", "PILOT-PL6", ""),
    ("eigrp_ipv6_distribute_list_direction", "eigrpIpv6DistributeListDirection", "in", "in", "out"),
]
LO_EIGRP_IDS = [r[0] for r in LO_EIGRP_ROWS]
NVPAIRS = [r[1] for r in LO_EIGRP_ROWS]
SET_WIRE = {"eigrpIpv6Routing": "true", "eigrpIpv4DistributeListPrefixList": "PILOT-PL4",
            "eigrpIpv4DistributeListDirection": "in", "eigrpIpv6DistributeListPrefixList": "PILOT-PL6",
            "eigrpIpv6DistributeListDirection": "in"}
RESET_WIRE = {r[1]: r[4] for r in LO_EIGRP_ROWS}


def _wire(value):
    return str(value).lower() if isinstance(value, bool) else str(value)


def _lo_eigrp_emitted(calls):
    """Every interface of every write, as {(serial, ifName): (policy, nvPairs)}."""
    out = {}
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    for pol in found:
        for intf in pol["interfaces"]:
            key = (intf["serialNumber"], intf["ifName"])
            assert key not in out, ("identity written twice", key)
            out[key] = (pol["policy"], intf.get("nvPairs") or {})
    return out


def _lo_eigrp_only(calls):
    emitted = _lo_eigrp_emitted(calls)
    assert len(emitted) == 1, emitted.keys()
    key, (policy, nv) = next(iter(emitted.items()))
    assert policy == LO and key[0] == h.SERIAL and key[1].lower() == h.IF_LO, (key, policy)
    return nv


def _lo_eigrp_have(profile, ifname=h.IF_LO):
    """The payload the module emits for `profile` on `ifname`, as the controller would return it."""
    result, calls = h.run_configs([h.cfg(ifname, profile, iftype="lo")], "replaced", [])
    assert not result.get("failed"), result.get("msg")
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    assert len(found) == 1, found
    have = copy.deepcopy(found)
    have[0]["interfaces"][0]["interfaceType"] = "INTERFACE_LOOPBACK"
    have[0]["interfaces"][0]["fabricName"] = h.FABRIC
    return have


def _lo_eigrp_as_have(nv, ifname=h.IF_LO):
    return [{"policy": LO, "interfaces": [{"interfaceType": "INTERFACE_LOOPBACK", "serialNumber": h.SERIAL,
                                           "ifName": ifname, "fabricName": h.FABRIC, "nvPairs": copy.deepcopy(nv)}]}]


def _lo(profile, ifname=h.IF_LO, **kw):
    return h.cfg(ifname, profile, iftype="lo", **kw)


# ------------------------------------------------------------------ the rows are what the 017 body declares
@pytest.mark.parametrize("key,nvpair,applied,wire,reset", LO_EIGRP_ROWS, ids=LO_EIGRP_IDS)
def test_the_row_matches_the_017_loopback_contract(key, nvpair, applied, wire, reset):
    b = resolve_binding(LO, key)
    assert b is not None, "%s is not registered on int_loopback" % key
    assert b["parent_nvpair"] == nvpair and b["mechanism"] == "passthrough"
    assert b["reset_wire"] == reset, "the reset is the template default whose branch creates no child"
    assert resolve_by_nvpair(LO, nvpair) is b
    assert "inert_when" not in b, "the template gates these fields on the tag, which NDFC enforces"


def test_types_bounds_and_enums_follow_the_body():
    for key in ("eigrp_ipv4_distribute_list_prefix_list", "eigrp_ipv6_distribute_list_prefix_list"):
        assert resolve_binding(LO, key)["max_length"] == 63
    for key in ("eigrp_ipv4_distribute_list_direction", "eigrp_ipv6_distribute_list_direction"):
        assert list(resolve_binding(LO, key)["valid_values"]) == ["in", "out"]
    assert resolve_binding(LO, "enable_eigrp_ipv6_routing")["type"] == "boolean"


@pytest.mark.parametrize("key,nvpair,applied,wire,reset", LO_EIGRP_ROWS, ids=LO_EIGRP_IDS)
def test_the_public_key_and_nvpair_match_the_routed_parent(key, nvpair, applied, wire, reset):
    """Reuse, not a new name: the routed, subinterface and SVI parents serve the same key for the same nvPair."""
    for parent in (h.ROUTED, h.SUBIF, h.SVI):
        other = resolve_binding(parent, key)
        assert other is not None and other["parent_nvpair"] == nvpair and other["reset_wire"] == reset, parent


# ------------------------------------------------------------------ merged
def test_merged_create_sends_every_field_on_the_loopback_and_deploys_it():
    result, calls = h.run_configs([_lo(EIGRP_SET)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _lo_eigrp_only(calls)
    assert {k: nv.get(k) for k in NVPAIRS} == SET_WIRE
    assert (nv["eigrpProcessTag"], nv["eigrpRouting"], nv["INTF_VRF"]) == ("PILOT-EIGRP", "true", "default")
    assert _paths(calls) == ["POST globalInterface", "POST globalInterface/deploy"]


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_explicit_update_sends_the_new_values_and_keeps_the_others(state):
    have = _lo_eigrp_have(EIGRP_SET)
    changes = {"eigrp_ipv4_distribute_list_direction": "out", "enable_eigrp_ipv6_routing": False,
               "eigrp_ipv6_distribute_list_prefix_list": "PILOT-PL6B"}
    result, calls = h.run_configs([_lo({**EIGRP_SET, **changes})], state, have)
    assert not result.get("failed"), result.get("msg")
    nv = _lo_eigrp_only(calls)
    expected = {**SET_WIRE, "eigrpIpv4DistributeListDirection": "out", "eigrpIpv6Routing": "false",
                "eigrpIpv6DistributeListPrefixList": "PILOT-PL6B"}
    assert {k: nv[k] for k in NVPAIRS} == expected
    assert (nv["eigrpProcessTag"], nv["DESC"], nv["IP"]) == ("PILOT-EIGRP", "pilot", "192.0.2.131")


def test_merged_omission_carries_the_stored_values_into_the_modify_lo_eigrp():
    have = _lo_eigrp_have(EIGRP_SET)
    result, calls = h.run_configs([_lo({**EIGRP_ON, "description": "changed"})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _lo_eigrp_only(calls)
    assert {k: nv[k] for k in NVPAIRS} == SET_WIRE
    assert nv["DESC"] == "changed"


def test_explicit_false_and_default_values_differ_from_omission_under_merged():
    have = _lo_eigrp_have(EIGRP_SET)
    explicit = {**EIGRP_ON, "enable_eigrp_ipv6_routing": False, "eigrp_ipv4_distribute_list_prefix_list": "",
                "eigrp_ipv6_distribute_list_direction": "out"}
    result, calls = h.run_configs([_lo(explicit)], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _lo_eigrp_only(calls)
    assert (nv["eigrpIpv6Routing"], nv["eigrpIpv4DistributeListPrefixList"], nv["eigrpIpv6DistributeListDirection"]) == (
        "false", "", "out")
    # the two omitted fields keep their stored values
    assert (nv["eigrpIpv4DistributeListDirection"], nv["eigrpIpv6DistributeListPrefixList"]) == ("in", "PILOT-PL6")


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_repeat_of_the_stored_values_writes_nothing(state):
    result, calls = h.run_configs([_lo(EIGRP_SET)], state, _lo_eigrp_have(EIGRP_SET))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and not result.get("changed")


# ------------------------------------------------------------------ replaced
def test_replaced_omission_withdraws_every_field_and_keeps_the_tag_and_routing():
    have = _lo_eigrp_have(EIGRP_SET)
    result, calls = h.run_configs([_lo(EIGRP_ON)], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = _lo_eigrp_only(calls)
    assert {k: nv[k] for k in NVPAIRS} == RESET_WIRE
    assert (nv["eigrpProcessTag"], nv["eigrpRouting"], nv["DESC"]) == ("PILOT-EIGRP", "true", "pilot")
    assert _paths(calls) == ["POST interface/modify", "POST globalInterface/deploy"], _paths(calls)


@pytest.mark.parametrize("key,nvpair,applied,wire,reset", LO_EIGRP_ROWS, ids=LO_EIGRP_IDS)
def test_replaced_withdraws_one_field_and_keeps_the_four_others(key, nvpair, applied, wire, reset):
    have = _lo_eigrp_have(EIGRP_SET)
    profile = {k: v for k, v in EIGRP_SET.items() if k != key}
    result, calls = h.run_configs([_lo(profile)], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = _lo_eigrp_only(calls)
    assert nv[nvpair] == reset
    assert {k: nv[k] for k in NVPAIRS if k != nvpair} == {k: v for k, v in SET_WIRE.items() if k != nvpair}


@pytest.mark.parametrize("state", ["replaced", "merged"])
def test_repeat_after_withdrawal_writes_nothing_lo_eigrp(state):
    result, calls = h.run_configs([_lo(EIGRP_ON)], "replaced", _lo_eigrp_have(EIGRP_SET))
    assert not result.get("failed"), result.get("msg")
    withdrawn = _lo_eigrp_as_have(_lo_eigrp_only(calls), _lo_eigrp_emitted(calls).popitem()[0][1])
    result, calls = h.run_configs([_lo(EIGRP_ON)], state, withdrawn)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_withdrawing_the_tag_with_routing_off_clears_the_five_fields_too():
    """The tag gate: replaced without any EIGRP key withdraws the tag, routing and the five fields together."""
    have = _lo_eigrp_have(EIGRP_SET)
    result, calls = h.run_configs([_lo(dict(h.BASE_LOOPBACK))], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = _lo_eigrp_only(calls)
    assert {k: nv[k] for k in NVPAIRS} == RESET_WIRE
    assert (nv["eigrpProcessTag"], nv["eigrpRouting"]) == ("", "false")


# ------------------------------------------------------------------ dependencies the template enforces, not the module
def test_a_field_without_the_tag_is_transported_and_left_to_the_template_refusal():
    """int_loopback 017 refuses an EIGRP option with an empty tag ("EIGRP process tag is required ..."). The module does
    not duplicate that rule on any parent (slice 0b_22): it transports the request and NDFC fails it. Live gap."""
    profile = {**h.BASE_LOOPBACK, "eigrp_ipv4_distribute_list_prefix_list": "PILOT-PL4"}
    result, calls = h.run_configs([_lo(profile)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _lo_eigrp_only(calls)
    assert (nv.get("eigrpProcessTag", ""), nv["eigrpIpv4DistributeListPrefixList"]) == ("", "PILOT-PL4")


def test_a_direction_without_its_prefix_list_is_transported_and_renders_nothing():
    """The direction is IsShow-gated on its prefix list and only used inside the prefix-list branch of the body."""
    profile = {**EIGRP_ON, "eigrp_ipv6_distribute_list_direction": "in"}
    result, calls = h.run_configs([_lo(profile)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _lo_eigrp_only(calls)
    assert (nv["eigrpIpv6DistributeListDirection"], nv.get("eigrpIpv6DistributeListPrefixList", "")) == ("in", "")


@pytest.mark.parametrize("vrf", ["default", "PILOT-VRF"])
def test_default_and_non_default_vrf_carry_the_fields_unchanged(vrf):
    """The body's EIGRP block is not VRF-gated. Whether NX-OS accepts it in a given VRF is a device question."""
    result, calls = h.run_configs([_lo({**EIGRP_SET, "int_vrf": vrf})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _lo_eigrp_only(calls)
    assert nv["INTF_VRF"] == vrf and {k: nv[k] for k in NVPAIRS} == SET_WIRE


# ------------------------------------------------------------------ invalid input, boundaries, version gate, check mode
@pytest.mark.parametrize("change,needle", [
    ({"eigrp_ipv4_distribute_list_direction": "both"}, "eigrp_ipv4_distribute_list_direction"),
    ({"eigrp_ipv6_distribute_list_direction": "IN"}, "eigrp_ipv6_distribute_list_direction"),
    ({"eigrp_ipv4_distribute_list_prefix_list": "P" * 64}, "eigrp_ipv4_distribute_list_prefix_list"),
    ({"eigrp_ipv6_distribute_list_prefix_list": "P" * 64}, "eigrp_ipv6_distribute_list_prefix_list"),
    ({"enable_eigrp_ipv6_routing": "maybe"}, "enable_eigrp_ipv6_routing"),
], ids=["v4_direction_both", "v6_direction_upper", "v4_prefix_list_64", "v6_prefix_list_64", "ipv6_routing_not_bool"])
def test_invalid_values_are_refused_before_any_write(change, needle):
    result, calls = h.run_configs([_lo({**EIGRP_SET, **change})], "merged", [])
    assert result.get("failed") and needle in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


def test_a_63_character_prefix_list_is_accepted():
    name = "P" * 63
    result, calls = h.run_configs([_lo({**EIGRP_ON, "eigrp_ipv6_distribute_list_prefix_list": name})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    assert _lo_eigrp_only(calls)["eigrpIpv6DistributeListPrefixList"] == name


@pytest.mark.parametrize("patch_version", [None, "4.3.1.0175006011"], ids=["no_patch_version", "smu011"])
def test_the_fields_need_an_approved_patch_version(patch_version):
    result, calls = h.run_configs([_lo(EIGRP_SET)], "merged", [], patch_version=patch_version)
    assert result.get("failed"), "a registered field was accepted without SMU 017 or ND >= 4.4.1"
    assert h.writes(calls) == []


def test_numeric_441_is_admitted_lo_eigrp():
    result, calls = h.run_configs([_lo(EIGRP_SET)], "merged", [], patch_version="4.4.1")
    assert not result.get("failed"), result.get("msg")
    assert {k: _lo_eigrp_only(calls)[k] for k in NVPAIRS} == SET_WIRE


def test_check_mode_reports_the_change_and_writes_nothing_lo_eigrp():
    result, calls = h.run_configs([_lo(EIGRP_ON)], "replaced", _lo_eigrp_have(EIGRP_SET), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and result.get("changed") is True


FABRIC_LO, FABRIC_LO_POLICY = "loopback0", "int_fabric_loopback_11_1"


def _lo_eigrp_measured_detail(calls, have):
    inner = _ORIG(calls, have)
    policy_of = dict((i["ifName"].lower(), p["policy"]) for p in have for i in p["interfaces"])

    def send(mod, method, path, payload=None):
        resp = inner(mod, method, path, payload)
        if method == "GET" and "/interface/detail" in path and isinstance(resp.get("DATA"), list):
            for e in resp["DATA"]:
                name = str(e.get("ifName", ""))
                if policy_of.get(name.lower()) == FABRIC_LO_POLICY:
                    e.update(ifType="INTERFACE_LOOPBACK", isPhysical="false", deletable=False, editAllowed=True,
                             underlayPolicies=[{"entityName": name, "source": "UNDERLAY",
                                                "templateName": FABRIC_LO_POLICY, "serialNumber": h.SERIAL}])
                elif name.lower().startswith("loopback"):
                    e.update(deletable=True, editAllowed=True)
        return resp
    return send


def _fabric_lo_have():
    return [{"policy": FABRIC_LO_POLICY, "interfaces": [{
        "interfaceType": "INTERFACE_LOOPBACK", "serialNumber": h.SERIAL, "ifName": FABRIC_LO, "fabricName": h.FABRIC,
        "nvPairs": {"INTF_NAME": FABRIC_LO, "IP": "10.2.0.1", "ADMIN_STATE": "true"}}]}]


def _overridden(configs, have):
    with patch.object(h, "_transport", _lo_eigrp_measured_detail):
        return h.run_configs(configs, "overridden", have)


def _lo_eigrp_aggregate():
    """The omitted or withdrawn user loopback, the retained one and the fabric loopback."""
    return _lo_eigrp_have(EIGRP_SET) + _lo_eigrp_have(EIGRP_SET, IF_LO2) + _fabric_lo_have()


def test_overridden_retained_loopback_withdraws_its_omitted_fields_and_keeps_the_control():
    result, calls = _overridden([_lo(EIGRP_ON), _lo(EIGRP_SET, IF_LO2)], _lo_eigrp_aggregate())
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [(MODIFY, [[h.SERIAL, "Loopback931", LO]]), (DEPLOY, [[h.SERIAL, "Loopback931"]])]
    nv = _lo_eigrp_only(calls)
    assert {k: nv[k] for k in NVPAIRS} == RESET_WIRE
    assert (nv["eigrpProcessTag"], nv["eigrpRouting"]) == ("PILOT-EIGRP", "true")


def test_overridden_loopback_left_out_is_deleted_and_the_retained_and_fabric_ones_kept():
    result, calls = _overridden([_lo(EIGRP_SET, IF_LO2)], _lo_eigrp_aggregate())
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [(MARK, [[h.SERIAL, "Loopback931"]]), (DEPLOY, [[h.SERIAL, "Loopback931"]])]
    result, calls = _overridden([_lo(EIGRP_SET, IF_LO2)], _lo_eigrp_have(EIGRP_SET, IF_LO2) + _fabric_lo_have())
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == []


def test_deleted_retires_the_loopback_and_a_repeat_writes_nothing():
    target = [{"name": h.IF_LO, "type": "lo", "switch": [h.SWITCH_IP]}]
    with patch.object(h, "_transport", _lo_eigrp_measured_detail):
        result, calls = h.run_configs(target, "deleted", _lo_eigrp_have(EIGRP_SET) + _fabric_lo_have())
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [(MARK, [[h.SERIAL, "Loopback931"]]), (DEPLOY, [[h.SERIAL, "Loopback931"]])]
    with patch.object(h, "_transport", _lo_eigrp_measured_detail):
        result, calls = h.run_configs(target, "deleted", _fabric_lo_have())
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == []


# ------------------------------------------------------------------ query
def _lo_eigrp_query_transport(store, writes):
    def factory(calls, _have):
        def send(mod, method, path, payload=None):
            calls.append({"method": method, "path": path, "payload": payload})
            if method != "GET":
                writes.append((method, path))
                return {"RETURN_CODE": 500, "MESSAGE": "query must not write", "DATA": {}}
            q = {k: v[0] for k, v in parse_qs(urlsplit(path).query).items()}
            if "accessmode" in path.lower():
                return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {"readonly": False}}
            if urlsplit(path).path.endswith("/rest/interface") and "ifName" in q:
                return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [
                    copy.deepcopy(p) for p in store for i in p["interfaces"]
                    if i["ifName"].lower() == q["ifName"].lower() and i["serialNumber"] == q.get("serialNumber")]}
            writes.append((method, path))
            return {"RETURN_CODE": 500, "MESSAGE": "unexpected read", "DATA": {}}
        return send
    return factory


def test_query_returns_the_controller_nvpairs_unchanged_lo_eigrp():
    target = _lo_eigrp_have(EIGRP_SET)
    other = _lo_eigrp_have(EIGRP_ON, IF_LO2)
    writes = []
    with patch.object(h, "_transport", _lo_eigrp_query_transport(target + other, writes)):
        result, calls = h.run_configs([{"name": h.IF_LO, "switch": [h.SWITCH_IP]}], "query", [])
    assert not result.get("failed"), result.get("msg")
    assert writes == [] and h.writes(calls) == []
    assert result["response"] == target, "query must return the controller entry unchanged"
    nv = result["response"][0]["interfaces"][0]["nvPairs"]
    assert {k: nv[k] for k in NVPAIRS} == SET_WIRE
    assert not result.get("changed")


# ------------------------------------------------------------------ unaffected controls
def test_loopback_ospf_payload_is_unchanged_by_the_new_rows():
    """Positive control: an OSPF-only loopback carries none of the five nvPairs."""
    result, calls = h.run_configs([_lo({**h.BASE_LOOPBACK, **h.OSPF_CTX})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _lo_eigrp_only(calls)
    assert nv["ospf"] == "true" and not set(NVPAIRS) & set(nv)


# ====================================================================================================
# Formerly test_gie_l3po_pim_sparse_dr_priority.py
# PIM sparse mode and DR priority on the routed port-channel (registry slice 0b_41).
#
#     int_l3_port_channel  ENABLE_PIM_SPARSE  enable_pim_sparse  boolean        reset "false"
#     int_l3_port_channel  PIM_DR_PRIORITY    pim_dr_priority    1-4294967295   reset "1"
#
# `type: pc`, `mode: l3` selects int_l3_port_channel. The body declares both fields and handles them independently:
# sparse mode "true" creates pim_interface; a priority other than "" and "1" creates interface_pim_dr_priority. Neither
# branch deletes its child; every add() first deletes all children of the port-channel. Read from the template body, not
# measured live.
#
# Real main() through helpers/binding_harness: only inventory, transport and sleep are mocked, and every HAVE is the payload
# the module itself emits for a public profile. Values are synthetic.
# ====================================================================================================
SPARSE, SPARSE_NV = "enable_pim_sparse", "ENABLE_PIM_SPARSE"
PRIO, PRIO_NV = "pim_dr_priority", "PIM_DR_PRIORITY"
L3PO_PIM_PO_A, L3PO_PIM_PO_B = h.PC_A, PO_B
L3PO_PIM_BASE = dict(h.BASE_PC_L3)
BOTH = {**L3PO_PIM_BASE, SPARSE: True, PRIO: 200}
OSPF = {"enable_ospf": True, "ospf_tag": "PILOT-OSPF", "ospf_area_id": "0.0.0.0", "ospf_cost": 42}
OSPF_NV = ("ospf", "ospfTag", "OSPF_AREA_ID", "ospfCost")
L3PO_PIM_NATIVE = NATIVE + ("pimBfdInstance",) + OSPF_NV


def _l3po_pim_native(nv):
    return {k: nv.get(k) for k in L3PO_PIM_NATIVE}


# ------------------------------------------------------------------ the rows are what the body declares
def test_the_rows_match_the_body_and_the_routed_rows():
    for key, nv, typ, reset in ((SPARSE, SPARSE_NV, "boolean", "false"), (PRIO, PRIO_NV, "integer", "1")):
        b = resolve_binding(L3PO, key)
        assert b is not None, key
        assert (b["parent_nvpair"], b["type"], b["reset_wire"], b["mechanism"]) == (nv, typ, reset, "passthrough")
        assert (b["applicable_interface_type"], b["applicable_mode"]) == ("pc", "l3")
        assert resolve_by_nvpair(L3PO, nv) is b
        assert "inert_when" not in b, "the body does not relate the two fields"
        routed = resolve_binding(h.ROUTED, key)
        for field in ("parent_nvpair", "type", "reset_wire", "default_template", "min_value", "max_value"):
            assert b.get(field) == routed.get(field), (key, field)
    prio = resolve_binding(L3PO, PRIO)
    assert (prio["min_value"], prio["max_value"], prio["default_template"]) == (1, 4294967295, 1)


# ------------------------------------------------------------------ wire forms, bounds, independence
@pytest.mark.parametrize("profile, wire", [
    ({SPARSE: True}, {SPARSE_NV: "true"}),
    ({SPARSE: False}, {SPARSE_NV: "false"}),
    ({PRIO: 1}, {PRIO_NV: "1"}),
    ({PRIO: 4294967295}, {PRIO_NV: "4294967295"}),
    ({SPARSE: True, PRIO: 200}, {SPARSE_NV: "true", PRIO_NV: "200"}),
], ids=["sparse_true", "sparse_false", "priority_min", "priority_max", "together"])
def test_create_sends_each_field_alone_or_together_in_wire_form(profile, wire):
    result, calls = h.run_configs([_po({**L3PO_PIM_BASE, **profile})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert {k: nv.get(k) for k in wire} == wire
    for k in (SPARSE_NV, PRIO_NV):
        if k not in wire:
            assert k not in nv, "an omitted field must not be sent on create"
    assert all(isinstance(nv[k], str) for k in wire)
    assert _paths(calls) == ["POST globalInterface", "POST globalInterface/deploy"], _paths(calls)


@pytest.mark.parametrize("value", [0, 4294967296, -1, "high"])
def test_an_out_of_range_or_non_integer_priority_is_refused_before_any_write(value):
    result, calls = h.run_configs([_po({**L3PO_PIM_BASE, PRIO: value})], "merged", [])
    assert result.get("failed") and PRIO in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


def test_a_non_boolean_sparse_value_is_refused_before_any_write():
    result, calls = h.run_configs([_po({**L3PO_PIM_BASE, SPARSE: "maybe"})], "merged", [])
    assert result.get("failed") and SPARSE in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


def test_a_priority_without_sparse_mode_is_accepted_as_the_body_allows():
    result, calls = h.run_configs([_po({**L3PO_PIM_BASE, SPARSE: False, PRIO: 50})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert (nv[SPARSE_NV], nv[PRIO_NV]) == ("false", "50")


# ------------------------------------------------------------------ merged
@pytest.mark.parametrize("change, wire", [
    ({SPARSE: False}, {SPARSE_NV: "false", PRIO_NV: "200"}),
    ({PRIO: 1}, {SPARSE_NV: "true", PRIO_NV: "1"}),
    ({PRIO: 4294967295}, {SPARSE_NV: "true", PRIO_NV: "4294967295"}),
], ids=["sparse_off", "priority_default", "priority_max"])
def test_merged_change_of_one_field_keeps_the_other_and_the_native_values(change, wire):
    have = _l3po_pim_bfd_have(BOTH)
    result, calls = h.run_configs([_po({**L3PO_PIM_BASE, **change})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert {k: nv[k] for k in wire} == wire
    assert _l3po_pim_native(nv) == _l3po_pim_native(have[0]["interfaces"][0]["nvPairs"])
    assert _paths(calls) == ["POST interface/modify", "POST globalInterface/deploy"], _paths(calls)


def test_merged_omission_carries_both_stored_values_into_another_change():
    have = _l3po_pim_bfd_have(BOTH)
    result, calls = h.run_configs([_po({**L3PO_PIM_BASE, "description": "changed"})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert (nv[SPARSE_NV], nv[PRIO_NV], nv["DESC"]) == ("true", "200", "changed")


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_repeat_of_the_stored_values_writes_nothing_l3po_pim(state):
    result, calls = h.run_configs([_po(BOTH)], state, _l3po_pim_bfd_have(BOTH))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and not result.get("changed")


def test_explicit_false_differs_from_omission_under_merged_l3po_pim():
    have = _l3po_pim_bfd_have(BOTH)
    result, calls = h.run_configs([_po({**L3PO_PIM_BASE, SPARSE: False})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)[SPARSE_NV] == "false"
    result, calls = h.run_configs([_po(L3PO_PIM_BASE)], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [], "omission under merged keeps the stored values"


def test_a_pim_change_keeps_the_stored_ospf_and_pim_bfd_values():
    have = _l3po_pim_bfd_have({**BOTH, **OSPF, "enable_pim_bfd_instance": True})
    stored = have[0]["interfaces"][0]["nvPairs"]
    assert (stored["ospf"], stored["ospfCost"], stored["pimBfdInstance"]) == ("true", "42", "true")
    result, calls = h.run_configs([_po({**L3PO_PIM_BASE, PRIO: 300})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert (nv[PRIO_NV], nv[SPARSE_NV]) == ("300", "true")
    assert _l3po_pim_native(nv) == _l3po_pim_native(stored)


# ------------------------------------------------------------------ replaced: field reset, not interface removal
@pytest.mark.parametrize("kept, wire", [
    ({}, {SPARSE_NV: "false", PRIO_NV: "1"}),
    ({SPARSE: True}, {SPARSE_NV: "true", PRIO_NV: "1"}),
    ({PRIO: 200}, {SPARSE_NV: "false", PRIO_NV: "200"}),
], ids=["both_omitted", "priority_omitted", "sparse_omitted"])
def test_replaced_omission_resets_only_the_omitted_field_and_keeps_the_port_channel(kept, wire):
    have = _l3po_pim_bfd_have({**BOTH, **OSPF, "enable_pim_bfd_instance": True})
    result, calls = h.run_configs([_po({**L3PO_PIM_BASE, **OSPF, "enable_pim_bfd_instance": True, **kept})], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert {k: nv[k] for k in wire} == wire
    assert _l3po_pim_native(nv) == _l3po_pim_native(have[0]["interfaces"][0]["nvPairs"])
    assert _paths(calls) == ["POST interface/modify", "POST globalInterface/deploy"], "a reset is an update, not a removal"


@pytest.mark.parametrize("state", ["replaced", "merged"])
def test_repeat_after_the_reset_writes_nothing(state):
    result, calls = h.run_configs([_po(L3PO_PIM_BASE)], "replaced", _l3po_pim_bfd_have(BOTH))
    assert not result.get("failed"), result.get("msg")
    reset = _l3po_pim_bfd_as_have(_only(calls))
    result, calls = h.run_configs([_po(L3PO_PIM_BASE)], state, reset)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_replaced_without_the_fields_on_a_port_channel_that_never_had_them_writes_nothing():
    result, calls = h.run_configs([_po(L3PO_PIM_BASE)], "replaced", _l3po_pim_bfd_have(L3PO_PIM_BASE))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


# ------------------------------------------------------------------ overridden, deleted, query, check mode
def _l3po_pim_aggregate(profile_a, profile_b):
    return (_l3po_pim_bfd_have({**profile_a, "members": [MEM_A]}) + _l3po_pim_bfd_have({**profile_b, "members": [MEM_B]}, L3PO_PIM_PO_B)
            + _member_have(MEM_A, L3PO_PIM_PO_A) + _member_have(MEM_B, L3PO_PIM_PO_B))


def test_overridden_retained_port_channel_resets_the_fields_and_keeps_the_control():
    configs = [_po({**L3PO_PIM_BASE, "members": [MEM_A]}), _po({**BOTH, "members": [MEM_B]}, L3PO_PIM_PO_B)]
    result, calls = _l3po_pim_bfd_run(configs, "overridden", _l3po_pim_aggregate(BOTH, BOTH))
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [(MODIFY, [[h.SERIAL, L3PO_PIM_PO_A, L3PO]]), (DEPLOY, [[h.SERIAL, L3PO_PIM_PO_A]])]
    nv = _only(calls)
    assert (nv[SPARSE_NV], nv[PRIO_NV], nv["MEMBER_INTERFACES"]) == ("false", "1", MEM_A)


def test_overridden_port_channel_left_out_is_deleted_and_the_retained_one_kept_l3po_pim():
    result, calls = _l3po_pim_bfd_run([_po({**BOTH, "members": [MEM_B]}, L3PO_PIM_PO_B)], "overridden", _l3po_pim_aggregate(BOTH, BOTH))
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [
        (MARK, [[h.SERIAL, L3PO_PIM_PO_A]]), (DEPLOY, [[h.SERIAL, L3PO_PIM_PO_A]]),
        (MODIFY, [[h.SERIAL, MEM_A, h.ROUTED]]), (DEPLOY, [[h.SERIAL, MEM_A]]),
    ]


def test_deleted_removes_the_port_channel_not_the_field_and_a_repeat_writes_nothing():
    target = [{"name": L3PO_PIM_PO_A, "type": "pc", "switch": [h.SWITCH_IP]}]
    have = _l3po_pim_bfd_have({**BOTH, "members": [MEM_A]}) + _member_have(MEM_A, L3PO_PIM_PO_A)
    result, calls = _l3po_pim_bfd_run(target, "deleted", have)
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [(MARK, [[h.SERIAL, L3PO_PIM_PO_A]]), (DEPLOY, [[h.SERIAL, L3PO_PIM_PO_A]])]
    result, calls = _l3po_pim_bfd_run(target, "deleted", [])
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == []


def test_query_returns_the_controller_values_unchanged():
    target = _l3po_pim_bfd_have(BOTH)
    writes = []
    with patch.object(h, "_transport", _l3po_pim_bfd_query_transport(target + _l3po_pim_bfd_have(L3PO_PIM_BASE, L3PO_PIM_PO_B), writes)):
        result, calls = h.run_configs([{"name": L3PO_PIM_PO_A, "switch": [h.SWITCH_IP]}], "query", [])
    assert not result.get("failed"), result.get("msg")
    assert writes == [] and h.writes(calls) == [] and not result.get("changed")
    assert result["response"] == target
    nv = result["response"][0]["interfaces"][0]["nvPairs"]
    assert (nv[SPARSE_NV], nv[PRIO_NV]) == ("true", "200")


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_check_mode_reports_the_change_and_writes_nothing_l3po_pim(state):
    result, calls = h.run_configs([_po({**L3PO_PIM_BASE, PRIO: 5})], state, _l3po_pim_bfd_have(BOTH), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and result.get("changed") is True


# ------------------------------------------------------------------ version gate and unaffected controls
@pytest.mark.parametrize("patch_version", [None, "4.3.1.0175006011"], ids=["no_patch_version", "smu011"])
@pytest.mark.parametrize("key, value", [(SPARSE, True), (PRIO, 200)])
def test_each_field_needs_an_approved_patch_version(patch_version, key, value):
    result, calls = h.run_configs([_po({**L3PO_PIM_BASE, key: value})], "merged", [], patch_version=patch_version)
    assert result.get("failed") and key in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("patch_version", [None, "4.3.1.0175006011"], ids=["no_patch_version", "smu011"])
def test_omission_under_a_closed_gate_resets_nothing_l3po_pim(patch_version):
    result, calls = h.run_configs([_po(L3PO_PIM_BASE)], "replaced", _l3po_pim_bfd_have(BOTH), patch_version=patch_version)
    assert not result.get("failed"), result.get("msg")
    for _policy, nv in _l3po_pim_bfd_emitted(calls).values():
        assert (nv.get(SPARSE_NV), nv.get(PRIO_NV)) in ((None, None), ("true", "200")), nv


def test_a_plain_l3_port_channel_payload_is_unchanged():
    result, calls = h.run_configs([_po(L3PO_PIM_BASE)], "merged", [])
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert SPARSE_NV not in nv and PRIO_NV not in nv


@pytest.mark.parametrize("parent", [h.PC_TRUNK, h.PC_ACCESS, h.PC_DOT1Q])
@pytest.mark.parametrize("key, value", [(SPARSE, True), (PRIO, 200)])
def test_the_keys_stay_refused_on_the_layer2_port_channels(parent, key, value):
    result, calls = h.run_configs([h.cfg_for(parent, {**h.base_for(parent), key: value})], "merged", [])
    assert result.get("failed") and key in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


def test_the_routed_ethernet_rows_are_unchanged():
    result, calls = h.run_configs([h.cfg(h.IF_A, {**h.BASE_ROUTED, SPARSE: True, PRIO: 200})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    nv = found[0]["interfaces"][0]["nvPairs"]
    assert [p["policy"] for p in found] == [h.ROUTED] and (nv[SPARSE_NV], nv[PRIO_NV]) == ("true", "200")


# ====================================================================================================
# Formerly test_gie_smu017_l3po_ospf.py
# The OSPF family on the routed port-channel (registry slice 0b_40): `type: pc`, `mode: l3`, parent int_l3_port_channel.
#
# The 017 int_l3_port_channel body (81c9392e) declares the nineteen OSPF nvPairs int_routed_host registers, with identical
# declarations, normalisation, validation and child rendering (compared offline against int_routed_host b5345584). The
# rows therefore copy the routed contracts: gate `ospf`, tag and area required with it, eleven options and the five
# authentication nvPairs strict or inert under it, the retransmit interval included.
#
# Real main() through helpers/binding_harness: only inventory, transport and sleep are mocked, and every HAVE is the payload
# the module itself emits for a public profile. Secrets are synthetic and must not appear in a message. Nothing here is
# live evidence; the registry-wide withdrawal matrix and the routed-family suites cover the per-row resets as well.
# ====================================================================================================
L3PO_OSPF_PO_A, L3PO_OSPF_PO_B = PO_A, PO_B
L3PO_OSPF_MEM_A, L3PO_OSPF_MEM_B = MEM_A, MEM_B
SYN_MD5 = "SYNTH-MD5-NOT-REAL-0001"
SYN_SIMPLE = "SYNTH-SIMPLE-NOT-REAL-02"
L3PO_OSPF_BASE = dict(h.BASE_PC_L3)
ON = {**L3PO_OSPF_BASE, "enable_ospf": True, "ospf_tag": "PILOT-OSPF", "ospf_area_id": "0.0.0.0"}
# Representative non-default options: a residue of any of them after a disable or a withdrawal is visible.
OPTIONS = {"ospf_retransmit_interval": 9, "ospf_cost": 42, "ospf_hello_interval": 11, "ospf_dead_interval": 44,
           "ospf_priority": 77, "ospf_transmit_delay": 3, "ospf_mtu_ignore": True, "ospf_shutdown": True,
           "ospf_passive_mode": "passive", "ospf_network_type": "point_to_point", "ospf_bfd_mode": "enable"}
OPTION_WIRE = {"ospfRetransmitInterval": "9", "ospfCost": "42", "ospfHelloInterval": "11", "ospfDeadInterval": "44",
               "ospfPriority": "77", "ospfTransmitDelay": "3", "ospfMtuIgnore": "true", "ospfShutdown": "true",
               "ospfPassiveMode": "passive", "ospfNetworkType": "pointToPoint", "ospfBfdMode": "enable"}
NEUTRAL = {"ospfRetransmitInterval": "", "ospfCost": "", "ospfHelloInterval": "", "ospfDeadInterval": "",
           "ospfPriority": "", "ospfTransmitDelay": "", "ospfMtuIgnore": "false", "ospfShutdown": "false",
           "ospfPassiveMode": "noChange", "ospfNetworkType": "noChange", "ospfBfdMode": "noChange"}
MD5 = {"enable_ospf_auth": True, "ospf_auth_key_id": 7, "ospf_auth_key": SYN_MD5}
FULL = {**ON, **OPTIONS, **MD5}
L3PO_OSPF_NATIVE = ("MEMBER_INTERFACES", "PC_MODE", "IP", "PREFIX", "INTF_VRF", "MTU", "DESC", "pimBfdInstance")
OSPF19 = ["ospf", "ospfTag", "OSPF_AREA_ID", "ospfAuthentication", "OSPF_AUTH_KEY_ID", "OSPF_AUTH_KEY",
          "ospfAuthenticationKeyType", "ospfAuthenticationKey", "ospfPassiveMode", "ospfCost", "ospfMtuIgnore",
          "ospfHelloInterval", "ospfDeadInterval", "ospfShutdown", "ospfTransmitDelay", "ospfRetransmitInterval",
          "ospfPriority", "ospfNetworkType", "ospfBfdMode"]
NO_REQUEST = "No configuration or deployment request was sent"


def _l3po_ospf_po(profile, ifname=L3PO_OSPF_PO_A):
    return _po(profile, ifname)


def _l3po_ospf_have(profile, ifname=L3PO_OSPF_PO_A):
    return _l3po_pim_bfd_have(profile, ifname)


def _l3po_ospf_sent(calls, ifname=L3PO_OSPF_PO_A):
    return _only(calls, ifname)


def _no_secret(result):
    text = json.dumps(result.get("msg", ""))
    assert SYN_MD5 not in text and SYN_SIMPLE not in text


def _ok(result):
    assert not result.get("failed"), result.get("msg")
    _no_secret(result)


def _refused(result, calls, *needles):
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    for needle in needles:
        assert needle in result["msg"], result["msg"]
    _no_secret(result)


# ------------------------------------------------------------------ the rows are the routed contracts
@pytest.mark.parametrize("nvpair", OSPF19)
def test_each_row_is_the_routed_row_on_the_routed_port_channel(nvpair):
    rows = {(r["parent_template"], r["parent_nvpair"]): r for r in BINDING_TABLE}
    mine, routed = rows[(L3PO, nvpair)], rows[(h.ROUTED, nvpair)]
    assert (mine["applicable_interface_type"], mine["applicable_mode"]) == ("pc", "l3")
    # dropped_on_policy_change is the generator's per-parent declaration for an Ethernet policy change (int_routed_host).
    skip = {"parent_template", "applicable_interface_type", "applicable_mode", "evidence_ref", "validated_on",
            "dropped_on_policy_change"}
    assert {k: v for k, v in mine.items() if k not in skip} == {k: v for k, v in routed.items() if k not in skip}


def test_the_slice_cites_the_l3_port_channel_body_for_every_row():
    """evidence_ref is a slice field (not compiled into the table): one per row, on the 017 body read here."""
    import os
    import yaml
    path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "tools", "registry", "slices",
                        "registry_slice_ospf.yaml")
    rows = [r for r in yaml.safe_load(open(path))["bindings"] if r["parent_template"] == L3PO]
    assert [r["parent_nvpair"] for r in rows] == OSPF19
    assert all(r["evidence_ref"].startswith("int_l3_port_channel.template@81c9392e#L") for r in rows)


def test_the_parent_carries_exactly_the_ospf_family_and_the_pim_rows():
    """PIM sparse mode and DR priority are slice 0b_41 (test_binding_smu017.py)."""
    nvpairs = sorted(r["parent_nvpair"] for r in BINDING_TABLE if r["parent_template"] == L3PO)
    assert nvpairs == sorted(OSPF19 + ["pimBfdInstance", "ENABLE_PIM_SPARSE", "PIM_DR_PRIORITY"])


# ------------------------------------------------------------------ merged
def test_merged_create_sends_the_family_with_the_native_profile():
    result, calls = h.run_configs([_l3po_ospf_po(FULL)], "merged", [])
    _ok(result)
    nv = _l3po_ospf_sent(calls)
    assert (nv["ospf"], nv["ospfTag"], nv["OSPF_AREA_ID"]) == ("true", "PILOT-OSPF", "0.0.0.0")
    assert {k: nv[k] for k in OPTION_WIRE} == OPTION_WIRE
    assert (nv["ospfAuthentication"], nv["OSPF_AUTH_KEY_ID"], nv["OSPF_AUTH_KEY"]) == ("true", "7", SYN_MD5)
    assert (nv["MEMBER_INTERFACES"], nv["IP"], nv["PREFIX"]) == (h.PC_MEMBER, "192.0.2.33", "30")
    assert _paths(calls) == ["POST globalInterface", "POST globalInterface/deploy"]


def test_merged_description_change_carries_every_stored_ospf_value():
    """An update that names no OSPF key keeps the family."""
    have = _l3po_ospf_have(FULL)
    result, calls = h.run_configs([_l3po_ospf_po({**L3PO_OSPF_BASE, "description": "changed"})], "merged", have)
    _ok(result)
    nv = _l3po_ospf_sent(calls)
    stored = have[0]["interfaces"][0]["nvPairs"]
    assert {k: nv[k] for k in OSPF19 if k in stored} == {k: stored[k] for k in OSPF19 if k in stored}
    assert nv["DESC"] == "changed"


def test_merged_interval_update_changes_only_the_interval():
    have = _l3po_ospf_have(FULL)
    result, calls = h.run_configs([_l3po_ospf_po({**ON, "ospf_retransmit_interval": 30})], "merged", have)
    _ok(result)
    nv, stored = _l3po_ospf_sent(calls), have[0]["interfaces"][0]["nvPairs"]
    assert nv["ospfRetransmitInterval"] == "30"
    assert {k for k in OSPF19 if k in stored and nv.get(k) != stored[k]} == {"ospfRetransmitInterval"}


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_repeat_of_the_stored_family_writes_nothing(state):
    result, calls = h.run_configs([_l3po_ospf_po(FULL)], state, _l3po_ospf_have(FULL))
    _ok(result)
    assert h.writes(calls) == [] and not result.get("changed")


def test_the_retransmit_default_5_is_transported_as_5_like_the_routed_parent():
    """The body normalises "5" to "" (no line); the module transports the value as on int_routed_host."""
    result, calls = h.run_configs([_l3po_ospf_po({**ON, "ospf_retransmit_interval": 5})], "merged", [])
    _ok(result)
    assert _l3po_ospf_sent(calls)["ospfRetransmitInterval"] == "5"


@pytest.mark.parametrize("value,ok", [(1, True), (65535, True), (0, False), (65536, False)])
def test_retransmit_bounds_follow_the_body(value, ok):
    result, calls = h.run_configs([_l3po_ospf_po({**ON, "ospf_retransmit_interval": value})], "merged", [])
    if ok:
        _ok(result)
    else:
        _refused(result, calls, "ospf_retransmit_interval")


# ------------------------------------------------------------------ replaced and overridden (retained)
def test_replaced_omission_withdraws_the_family_coherently():
    """Omitting the family turns the gate off and neutralises every option and the message-digest material in the same
    request; the tag has no neutral value and stays stored, inert (it configures nothing with the gate off)."""
    have = _l3po_ospf_have(FULL)
    result, calls = h.run_configs([_l3po_ospf_po(L3PO_OSPF_BASE)], "replaced", have)
    _ok(result)
    nv = _l3po_ospf_sent(calls)
    assert nv["ospf"] == "false" and {k: nv[k] for k in NEUTRAL} == NEUTRAL
    assert (nv["ospfAuthentication"], nv["OSPF_AUTH_KEY"], nv["OSPF_AUTH_KEY_ID"]) == ("false", "", "1")
    assert nv["ospfTag"] == "PILOT-OSPF" and nv["OSPF_AREA_ID"] == "0.0.0.0"
    assert {k: nv[k] for k in L3PO_OSPF_NATIVE if k in nv} == {k: have[0]["interfaces"][0]["nvPairs"][k] for k in L3PO_OSPF_NATIVE if k in nv}


def test_replaced_keeping_ospf_withdraws_only_the_omitted_options():
    have = _l3po_ospf_have(FULL)
    keep = {**ON, "ospf_cost": 42}
    result, calls = h.run_configs([_l3po_ospf_po(keep)], "replaced", have)
    _ok(result)
    nv = _l3po_ospf_sent(calls)
    assert (nv["ospf"], nv["ospfTag"], nv["ospfCost"]) == ("true", "PILOT-OSPF", "42")
    assert {k: nv[k] for k in NEUTRAL if k != "ospfCost"} == {k: v for k, v in NEUTRAL.items() if k != "ospfCost"}
    assert (nv["ospfAuthentication"], nv["OSPF_AUTH_KEY"]) == ("false", "")


def test_replaced_withdrawal_repeated_writes_nothing():
    result, calls = h.run_configs([_l3po_ospf_po(L3PO_OSPF_BASE)], "replaced", _l3po_ospf_have(FULL))
    withdrawn = _l3po_pim_bfd_as_have(_l3po_ospf_sent(calls))
    result, calls = h.run_configs([_l3po_ospf_po(L3PO_OSPF_BASE)], "replaced", withdrawn)
    _ok(result)
    assert h.writes(calls) == []


def test_overridden_retained_port_channel_withdraws_like_replaced_and_keeps_the_control():
    have = (_l3po_ospf_have({**FULL, "members": [L3PO_OSPF_MEM_A]}) + _l3po_ospf_have({**FULL, "members": [L3PO_OSPF_MEM_B]}, L3PO_OSPF_PO_B)
            + _member_have(L3PO_OSPF_MEM_A, L3PO_OSPF_PO_A) + _member_have(L3PO_OSPF_MEM_B, L3PO_OSPF_PO_B))
    result, calls = _l3po_pim_bfd_run(
        [_l3po_ospf_po({**L3PO_OSPF_BASE, "members": [L3PO_OSPF_MEM_A]}),
         _l3po_ospf_po({**FULL, "members": [L3PO_OSPF_MEM_B]}, L3PO_OSPF_PO_B)],
        "overridden", have)
    _ok(result)
    assert _identities(calls) == [(MODIFY, [[h.SERIAL, L3PO_OSPF_PO_A, L3PO]]), (DEPLOY, [[h.SERIAL, L3PO_OSPF_PO_A]])]
    nv = _l3po_ospf_sent(calls)
    assert nv["ospf"] == "false" and {k: nv[k] for k in NEUTRAL} == NEUTRAL and nv["OSPF_AUTH_KEY"] == ""


# ------------------------------------------------------------------ deleted and overridden (omitted)
def test_deleted_retires_the_aggregate_with_its_ospf_and_a_repeat_writes_nothing():
    target = [{"name": L3PO_OSPF_PO_A, "type": "pc", "switch": [h.SWITCH_IP]}]
    have = _l3po_ospf_have({**FULL, "members": [L3PO_OSPF_MEM_A]}) + _member_have(L3PO_OSPF_MEM_A, L3PO_OSPF_PO_A)
    result, calls = _l3po_pim_bfd_run(target, "deleted", have)
    _ok(result)
    assert _identities(calls) == [(MARK, [[h.SERIAL, L3PO_OSPF_PO_A]]), (DEPLOY, [[h.SERIAL, L3PO_OSPF_PO_A]])]
    result, calls = _l3po_pim_bfd_run(target, "deleted", [])
    assert h.writes(calls) == []


def test_overridden_omitted_port_channel_is_deleted_with_the_native_member_reset():
    have = (_l3po_ospf_have({**FULL, "members": [L3PO_OSPF_MEM_A]}) + _l3po_ospf_have({**FULL, "members": [L3PO_OSPF_MEM_B]}, L3PO_OSPF_PO_B)
            + _member_have(L3PO_OSPF_MEM_A, L3PO_OSPF_PO_A) + _member_have(L3PO_OSPF_MEM_B, L3PO_OSPF_PO_B))
    result, calls = _l3po_pim_bfd_run([_l3po_ospf_po({**FULL, "members": [L3PO_OSPF_MEM_B]}, L3PO_OSPF_PO_B)], "overridden", have)
    _ok(result)
    assert _identities(calls) == [
        (MARK, [[h.SERIAL, L3PO_OSPF_PO_A]]), (DEPLOY, [[h.SERIAL, L3PO_OSPF_PO_A]]),
        (MODIFY, [[h.SERIAL, L3PO_OSPF_MEM_A, h.ROUTED]]), (DEPLOY, [[h.SERIAL, L3PO_OSPF_MEM_A]]),
    ]


# ------------------------------------------------------------------ query
def test_query_returns_the_configured_ospf_values_unchanged():
    target = _l3po_ospf_have(FULL)
    writes = []
    with patch.object(h, "_transport", _l3po_pim_bfd_query_transport(target, writes)):
        result, calls = h.run_configs([{"name": L3PO_OSPF_PO_A, "switch": [h.SWITCH_IP]}], "query", [])
    _ok(result)
    assert writes == [] and h.writes(calls) == []
    assert result["response"] == target
    nv = result["response"][0]["interfaces"][0]["nvPairs"]
    assert (nv["ospf"], nv["ospfRetransmitInterval"], nv["ospfTag"]) == ("true", "9", "PILOT-OSPF")


# ------------------------------------------------------------------ the gate: disable, dependents, the tag
def test_merged_explicit_disable_neutralises_every_stored_option():
    have = _l3po_ospf_have(FULL)
    result, calls = h.run_configs([_l3po_ospf_po({**L3PO_OSPF_BASE, "enable_ospf": False})], "merged", have)
    _ok(result)
    nv = _l3po_ospf_sent(calls)
    assert nv["ospf"] == "false" and {k: nv[k] for k in NEUTRAL} == NEUTRAL
    assert (nv["ospfAuthentication"], nv["OSPF_AUTH_KEY"], nv["OSPF_AUTH_KEY_ID"]) == ("false", "", "1")
    assert nv["ospfTag"] == "PILOT-OSPF", "the tag has no neutral value: kept as stored, it configures nothing"


def test_an_explicit_option_while_disabling_is_refused_before_any_write():
    result, calls = h.run_configs([_l3po_ospf_po({**L3PO_OSPF_BASE, "enable_ospf": False, "ospf_retransmit_interval": 9})], "merged",
                                  _l3po_ospf_have(FULL))
    _refused(result, calls, "ospf_retransmit_interval", NO_REQUEST)


def test_a_tag_cannot_turn_ospf_on_by_itself():
    """Over a port-channel with OSPF off, sending only a tag leaves the gate off: the tag is inert, not a feature."""
    have = _l3po_ospf_have({**L3PO_OSPF_BASE, "enable_ospf": False})
    result, calls = h.run_configs([_l3po_ospf_po({**L3PO_OSPF_BASE, "ospf_tag": "OTHER-TAG"})], "merged", have)
    _ok(result)
    nv = _l3po_ospf_sent(calls)
    assert nv["ospf"] == "false" and nv["ospfTag"] == "OTHER-TAG"
    assert not any(nv.get(k) not in ("", None, NEUTRAL[k]) for k in NEUTRAL)


def test_disable_then_repeat_is_a_noop():
    result, calls = h.run_configs([_l3po_ospf_po({**L3PO_OSPF_BASE, "enable_ospf": False})], "merged", _l3po_ospf_have(FULL))
    disabled = _l3po_pim_bfd_as_have(_l3po_ospf_sent(calls))
    result, calls = h.run_configs([_l3po_ospf_po({**L3PO_OSPF_BASE, "enable_ospf": False})], "merged", disabled)
    _ok(result)
    assert h.writes(calls) == []


# ------------------------------------------------------------------ authentication (synthetic secrets, redacted)
def test_message_digest_rotation_changes_only_the_key():
    have = _l3po_ospf_have(FULL)
    result, calls = h.run_configs([_l3po_ospf_po({**FULL, "ospf_auth_key": "SYNTH-MD5-NOT-REAL-0002"})], "merged", have)
    _ok(result)
    nv, stored = _l3po_ospf_sent(calls), have[0]["interfaces"][0]["nvPairs"]
    assert {k for k in OSPF19 if k in stored and nv.get(k) != stored[k]} == {"OSPF_AUTH_KEY"}


def test_message_digest_without_its_key_is_left_to_the_template_refusal():
    """IsMandatory="ospfAuthentication==true" on OSPF_AUTH_KEY: the module does not repeat that rule on any parent; the
    controller answers 207 'Validation failed for following fields: [OSPF_AUTH_KEY]' (measured on int_routed_host)."""
    result, calls = h.run_configs([_l3po_ospf_po({**ON, "enable_ospf_auth": True, "ospf_auth_key_id": 7})], "merged", [])
    _ok(result)
    nv = _l3po_ospf_sent(calls)
    assert nv["ospfAuthentication"] == "true" and "OSPF_AUTH_KEY" not in nv


def test_simple_key_with_its_type_and_its_withdrawal():
    simple = {**ON, "ospf_authentication_key": SYN_SIMPLE, "ospf_authentication_key_type": "7"}
    result, calls = h.run_configs([_l3po_ospf_po(simple)], "merged", [])
    _ok(result)
    assert (_l3po_ospf_sent(calls)["ospfAuthenticationKey"], _l3po_ospf_sent(calls)["ospfAuthenticationKeyType"]) == (SYN_SIMPLE, "7")
    result, calls = h.run_configs([_l3po_ospf_po(ON)], "replaced", _l3po_ospf_have(simple))
    _ok(result)
    assert _l3po_ospf_sent(calls)["ospfAuthenticationKey"] == ""


def test_a_stored_key_in_another_form_is_resent_and_that_is_storage_normalisation_not_idempotency():
    """The key compares exactly (string_compare exact, as on int_routed_host). If the controller stores a different
    string for the same secret, every run resends it. That is the storage-normalisation case measured on
    int_routed_host (a type 0 simple key the switch stores as type 3 stays Out-of-Sync); with the stored string sent
    back, the repeat is a no-op (test_repeat_of_the_stored_family_writes_nothing)."""
    have = _l3po_ospf_have(FULL)
    have[0]["interfaces"][0]["nvPairs"]["OSPF_AUTH_KEY"] = "CONTROLLER-NORMALISED-FORM"
    result, calls = h.run_configs([_l3po_ospf_po(FULL)], "merged", have)
    _ok(result)
    assert _l3po_ospf_sent(calls)["OSPF_AUTH_KEY"] == SYN_MD5


def test_neither_secret_appears_in_a_refusal_message():
    bad = {**L3PO_OSPF_BASE, "enable_ospf": False, "ospf_auth_key": SYN_MD5, "ospf_authentication_key": SYN_SIMPLE,
           "enable_ospf_auth": True}
    result, calls = h.run_configs([_l3po_ospf_po(bad)], "merged", _l3po_ospf_have(FULL))
    _refused(result, calls, NO_REQUEST)


# ------------------------------------------------------------------ unrelated fields, gate, check mode, counts
def test_an_ospf_change_keeps_membership_address_and_pim_bfd():
    have = _l3po_ospf_have({**FULL, "enable_pim_bfd_instance": True})
    result, calls = h.run_configs([_l3po_ospf_po({**FULL, "enable_pim_bfd_instance": True, "ospf_cost": 50})], "merged", have)
    _ok(result)
    nv, stored = _l3po_ospf_sent(calls), have[0]["interfaces"][0]["nvPairs"]
    assert {k: nv[k] for k in L3PO_OSPF_NATIVE} == {k: stored[k] for k in L3PO_OSPF_NATIVE}
    assert nv["ospfCost"] == "50" and nv["pimBfdInstance"] == "true"


@pytest.mark.parametrize("patch_version", [None, "4.3.1.0175006011"], ids=["no_patch_version", "smu011"])
def test_the_family_needs_an_approved_patch_version(patch_version):
    result, calls = h.run_configs([_l3po_ospf_po(ON)], "merged", [], patch_version=patch_version)
    assert result.get("failed") and h.writes(calls) == []


def test_numeric_441_is_admitted_l3po_ospf():
    result, calls = h.run_configs([_l3po_ospf_po(ON)], "merged", [], patch_version="4.4.1")
    _ok(result)
    assert _l3po_ospf_sent(calls)["ospf"] == "true"


def test_check_mode_reports_the_withdrawal_and_writes_nothing():
    result, calls = h.run_configs([_l3po_ospf_po(L3PO_OSPF_BASE)], "replaced", _l3po_ospf_have(FULL), check_mode=True)
    _ok(result)
    assert h.writes(calls) == [] and result.get("changed") is True


@pytest.mark.parametrize("profile,have", [
    (lambda: FULL, lambda: []),
    (lambda: {**FULL, "ospf_cost": 50}, lambda: _l3po_ospf_have(FULL)),
    (lambda: FULL, lambda: _l3po_ospf_have(FULL)),
], ids=["create", "update", "repeat"])
def test_ospf_adds_no_read_or_write_over_the_plain_port_channel(profile, have):
    """Matched counts: the OSPF family costs no extra request against the same scenario without OSPF."""
    plain = {"create": (L3PO_OSPF_BASE, []),
             "update": ({**L3PO_OSPF_BASE, "description": "x"}, _l3po_ospf_have(L3PO_OSPF_BASE)),
             "repeat": (L3PO_OSPF_BASE, _l3po_ospf_have(L3PO_OSPF_BASE))}
    result, calls = h.run_configs([_l3po_ospf_po(profile())], "merged", have())
    _ok(result)
    key = "create" if not have() else ("repeat" if profile() == FULL else "update")
    p_prof, p_have = plain[key]
    _r, p_calls = h.run_configs([_l3po_ospf_po(p_prof)], "merged", p_have)
    got, ref = h.split_calls(calls), h.split_calls(p_calls)
    assert {k: len(v) for k, v in got.items()} == {k: len(v) for k, v in ref.items()}
