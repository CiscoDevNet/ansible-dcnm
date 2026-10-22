"""SMU 4.3.1.0175006017 new interface fields, first increment (registry slice 0b_37).

    int_routed_host  CDP_ENABLE                  enable_cdp                          reset "true"
    int_routed_host  evpnMultisiteDciTracking    enable_evpn_multisite_dci_tracking  reset "false"
    int_routed_host  ospfRetransmitInterval      ospf_retransmit_interval            reset "" (OSPF-gated)
    int_access_host  loggingEventPortLinkStatus  logging_event_port_link_status      reset "false"
    int_subif        pimBfdInstance              enable_pim_bfd_instance             reset "false"

Real main() through gie_withdrawal_harness: only inventory, transport and sleep are mocked, and every HAVE is the
payload the module itself emits for a public profile. The expected values come from the 017 template bodies cited in
the slice (defaults and the branches that create or delete each child or line), not from the table under test. None of
this is measured on a controller or a device.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding, resolve_by_nvpair
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import gie_withdrawal_harness as h
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.test_dcnm_intf_default_reset_registered_f2 import (
    nvpairs_of_reset, reset_policies, run as f2_run,
)

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
    The identity, request and control-interface cases are in test_gie_access_logging_reset.py."""
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
