"""Role-default and parent resets measured live: access, border, vPC, HSRP, routed LLDP and port-channel."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import pytest

from unittest.mock import patch
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import BINDING_TABLE
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_by_nvpair
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module
from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table as table
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_WITHDRAW_NONE
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_WITHDRAW_RESET
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_withdrawal_action
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_ENABLED_PATCH_VERSIONS
from urllib.parse import parse_qs
from urllib.parse import urlsplit

from .helpers import binding_harness as h
from .helpers.binding_harness import _as_slice_rows
from .helpers.binding_harness import _load_generator
from .helpers.role_reset import _as_have
from .helpers.role_reset import _deploys
from .helpers.role_reset import _emitted
from .helpers.role_reset import _have_for
from .helpers.role_reset import _run
from .helpers.role_reset import STATES
from .helpers.role_reset import nvpairs_of_reset
from .helpers.role_reset import reset_policies
from .helpers.role_reset import reset_wire
from .helpers.role_reset import run
from .helpers.binding_harness import GROUPED_ONLY_NO_PER_ROW_FIXTURE
from .helpers.binding_harness import HSRP_CTX
from .helpers.binding_harness import SVI
from .helpers.binding_harness import SUPPORTED_PATCH
from .helpers.binding_harness import base_for
from .helpers.binding_harness import build_have
from .helpers.binding_harness import cfg_for
from .helpers.binding_harness import diff_nvpairs
from .helpers.binding_harness import request_nvpairs
from .helpers.binding_harness import run_configs
from .helpers.binding_harness import split_calls
from .helpers.binding_harness import ACCESS
from .helpers.binding_harness import ROUTED
from .helpers.binding_harness import SUPPORTED as ROUTED_LLDP_SUPPORTED
from .helpers.binding_harness import run as routed_lldp_run


# ====================================================================================================
# Formerly test_gie_access_logging_reset.py
# A leaf role-default reset of an int_access_host Ethernet with loggingEventPortLinkStatus true.
#
# Measured on NDFC 12.6.0.267, SMU 4.3.1.0175006017, NX-OS 10.5(5), one leaf access port: a legacy interface/modify from
# int_access_host with the line configured to the role default int_trunk_host left the pending
# `logging event port link-status default`; after one port deploy the running, intent and children equalled the baseline.
# The registry declares that transition for this field only (POLICY_CHANGE_CLEARS_INLINE_FIELDS in the generator); every
# other access field and destination keeps its contract.
#
# Real main() through helpers/binding_harness; only inventory, transport and sleep are mocked. Values are synthetic.
# ====================================================================================================
LOGGING_ON = {**h.BASE_ACCESS, "logging_event_port_link_status": True}
NEUTRAL = dict(h.BASE_ACCESS)
IF_CTL = "Ethernet1/40"
CONTROL = {**h.BASE_ACCESS, "description": "control"}
NAMED = [{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}]


def _shape(calls):
    return [(c["method"], c["path"].split("/rest/")[-1].split("?")[0]) for c in calls]


# ------------------------------------------------------------------ the declaration is scoped to one field
def test_only_the_logging_row_declares_the_trunk_destination():
    marked = {(r["parent_template"], r["parent_nvpair"]): tuple(r["cleared_on_change_to"])
              for r in BINDING_TABLE if r.get("cleared_on_change_to")}
    assert marked[(h.ACCESS, "loggingEventPortLinkStatus")] == (h.ROUTED, h.TRUNK)
    others = {k: v for k, v in marked.items() if k != (h.ACCESS, "loggingEventPortLinkStatus")}
    assert set(others.values()) == {(h.ROUTED,)}, "no other row may gain a destination"
    assert resolve_by_nvpair(h.TRUNK, "loggingEventPortLinkStatus") is None


def test_the_generator_refuses_the_field_destination_on_another_row():
    gen = _load_generator()
    rows = _as_slice_rows(BINDING_TABLE)
    assert len(gen.compile_rows(rows)) == len(BINDING_TABLE)
    other = next(r for r in rows if (r["parent_template"], r["parent_nvpair"]) == (h.ACCESS, "aclFilter"))
    other["cleared_on_change_to"] = (h.ROUTED, h.TRUNK)
    with pytest.raises(ValueError, match="cleared_on_change_to"):
        gen.compile_rows(rows)


# ------------------------------------------------------------------ named deleted and overridden omission (leaf)
@pytest.mark.parametrize("state", ["deleted", "overridden"])
def test_leaf_reset_with_logging_on_resets_to_trunk_and_leaves_the_control(state):
    have = _have_for(h.IF_A, LOGGING_ON) + _have_for(IF_CTL, CONTROL)
    assert have[0]["interfaces"][0]["nvPairs"]["loggingEventPortLinkStatus"] == "true"
    configs = NAMED if state == "deleted" else [h.cfg(IF_CTL, dict(CONTROL))]
    result, calls = _run(configs, state, have, role="leaf")
    assert not result.get("failed"), result.get("msg")
    emitted = _emitted(calls)
    assert list(emitted) == [(h.SERIAL, h.IF_A)], emitted.keys()
    policy, nv = emitted[(h.SERIAL, h.IF_A)]
    assert policy == h.TRUNK
    assert "loggingEventPortLinkStatus" not in nv, "a source-only nvPair is never written into the destination"
    assert _deploys(calls) == [(h.SERIAL, h.IF_A)]
    assert [c["path"].split("/rest/")[-1] for c in h.writes(calls)] == ["interface/modify", "globalInterface/deploy"]
    # identical request shape and payload to the same reset of a port without logging
    neutral_have = _have_for(h.IF_A, NEUTRAL) + _have_for(IF_CTL, CONTROL)
    n_result, n_calls = _run(configs, state, neutral_have, role="leaf")
    assert not n_result.get("failed"), n_result.get("msg")
    assert _shape(calls) == _shape(n_calls)
    assert _emitted(n_calls)[(h.SERIAL, h.IF_A)] == (policy, nv)


@pytest.mark.parametrize("state", ["deleted", "overridden"])
def test_repeat_after_the_reset_writes_nothing(state):
    have = _have_for(h.IF_A, LOGGING_ON) + _have_for(IF_CTL, CONTROL)
    configs = NAMED if state == "deleted" else [h.cfg(IF_CTL, dict(CONTROL))]
    result, calls = _run(configs, state, have, role="leaf")
    assert not result.get("failed"), result.get("msg")
    policy, nv = _emitted(calls)[(h.SERIAL, h.IF_A)]
    after = _as_have(policy, h.IF_A, nv) + _have_for(IF_CTL, CONTROL)
    result, calls = _run(configs, state, after, role="leaf")
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


# ------------------------------------------------------------------ preserved behaviour
def test_retained_interface_still_withdraws_the_field_on_its_own_policy():
    have = _have_for(h.IF_A, LOGGING_ON) + _have_for(IF_CTL, CONTROL)
    result, calls = _run([h.cfg(h.IF_A, dict(NEUTRAL)), h.cfg(IF_CTL, dict(CONTROL))], "overridden", have, role="leaf")
    assert not result.get("failed"), result.get("msg")
    emitted = _emitted(calls)
    assert list(emitted) == [(h.SERIAL, h.IF_A)]
    assert emitted[(h.SERIAL, h.IF_A)][0] == h.ACCESS
    assert emitted[(h.SERIAL, h.IF_A)][1]["loggingEventPortLinkStatus"] == "false"


@pytest.mark.parametrize("state", ["deleted", "overridden"])
def test_border_reset_is_unchanged(state):
    have = _have_for(h.IF_A, LOGGING_ON)
    configs = NAMED if state == "deleted" else []
    result, calls = _run(configs, state, have, role="border")
    assert not result.get("failed"), result.get("msg")
    policy, nv = _emitted(calls)[(h.SERIAL, h.IF_A)]
    assert policy == h.ROUTED and "loggingEventPortLinkStatus" not in nv


@pytest.mark.parametrize("state", ["deleted", "overridden"])
def test_an_undeclared_destination_is_still_refused(state):
    """Forced role default int_pvlan_host: not declared for the field, so the refusal stands."""
    orig = module.DcnmIntf.dcnm_intf_get_default_eth_payload

    def pvlan_default(self, ifname, sno, fabric):
        payload = orig(self, ifname, sno, fabric)
        payload["policy"] = "int_pvlan_host"
        return payload
    have = _have_for(h.IF_A, LOGGING_ON)
    with patch.object(module.DcnmIntf, "dcnm_intf_get_default_eth_payload", pvlan_default):
        result, calls = _run(NAMED if state == "deleted" else [], state, have, role="leaf")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    assert "loggingEventPortLinkStatus" in result["msg"] and "int_access_host -> int_pvlan_host" in result["msg"]


@pytest.mark.parametrize("state", ["deleted", "overridden"])
def test_an_unreadable_value_is_still_refused(state):
    have = _have_for(h.IF_A, LOGGING_ON)
    have[0]["interfaces"][0]["nvPairs"]["loggingEventPortLinkStatus"] = "maybe"
    result, calls = _run(NAMED if state == "deleted" else [], state, have, role="leaf")
    assert result.get("failed") and h.writes(calls) == []
    assert "not readable as its type" in result["msg"]


# ====================================================================================================
# Formerly test_gie_border_l2_retirement.py
# D-2 / P2: a border (non-leaf) reset of an int_trunk_host or int_access_host Ethernet to the role default int_routed_host
# with a port ACL, spanning-tree port type or guard, or flowcontrol configured.
#
# These parents render their lines inline (no child policy). When the reset replaces them with int_routed_host the
# controller negates every running line the routed stanza does not expect (measured on one border trunk port, flowcontrol
# included). The generator declares that transition per parent and destination (cleared_on_change_to); the reset now
# proceeds with the module's ordinary routed default payload, one write, and never carries a source-only key. The access
# parent is covered by template parity only. A destination that is not declared, an unreadable value, the leaf same-parent
# reset, and P1/P3 are unchanged. Real main() through helpers/binding_harness; values are synthetic.
# ====================================================================================================
ACL = "SYN-ACL"
TRUNK_FIELDS = {"aclFilter": ACL, "spanningTreePortType": "network", "GUARD_MODE": "root",
                "flowcontrolReceive": "on", "flowcontrolSend": "on"}
ACCESS_FIELDS = {"aclFilter": ACL, "spanningTreePortType": "network", "flowcontrolReceive": "on", "flowcontrolSend": "on"}
SOURCE_ONLY = ("aclFilter", "spanningTreePortType", "GUARD_MODE", "flowcontrolReceive", "flowcontrolSend")


def have_of(parent, nv):
    have = copy.deepcopy(h.build_have(parent))
    have[0]["interfaces"][0]["nvPairs"].update(nv)
    return have


# ------------------------------------------------------------------ the finding, fixed
@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("parent, fields", [(h.TRUNK, TRUNK_FIELDS), (h.ACCESS, ACCESS_FIELDS)], ids=["trunk", "access"])
def test_border_reset_sends_the_ordinary_routed_payload(state, parent, fields):
    _r0, calls0 = run(state, have_of(parent, {}), "border")                 # neutral port of the same parent
    result, calls = run(state, have_of(parent, fields), "border")
    assert not result.get("failed"), result.get("msg")
    assert len(h.split_calls(calls)["updates"]) == 1 and reset_policies(calls)[0]["policy"] == h.ROUTED
    sent = nvpairs_of_reset(calls)
    assert not any(k in sent for k in SOURCE_ONLY)                          # never written into int_routed_host
    assert sent == nvpairs_of_reset(calls0)                                  # identical to the neutral port's reset
    assert [(c["method"], c["path"]) for c in calls] == [(c["method"], c["path"]) for c in calls0]
    assert ACL not in str([c.get("payload") for c in calls])


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("field, value", [
    ("aclFilter", ACL), ("spanningTreePortType", "normal"), ("GUARD_MODE", "loop"), ("GUARD_MODE", "none"),
    ("flowcontrolReceive", "on"), ("flowcontrolSend", "on"),
])
def test_each_trunk_field_alone_is_cleared_by_the_reset(state, field, value):
    result, calls = run(state, have_of(h.TRUNK, {field: value}), "border")
    assert not result.get("failed"), result.get("msg")
    assert field not in nvpairs_of_reset(calls) and reset_policies(calls)[0]["policy"] == h.ROUTED


@pytest.mark.parametrize("state", STATES)
def test_fields_both_parents_register_keep_the_destination_reset(state):
    result, calls = run(state, have_of(h.TRUNK, dict(TRUNK_FIELDS, lldpReceive="true", queuingStats="true")), "border")
    assert not result.get("failed"), result.get("msg")
    sent = nvpairs_of_reset(calls)
    assert sent["lldpReceive"] == reset_wire(h.ROUTED, "lldpReceive")
    assert sent["queuingStats"] == reset_wire(h.ROUTED, "queuingStats")


@pytest.mark.parametrize("state", STATES)
def test_second_run_over_the_reset_is_a_noop(state):
    _r1, calls1 = run(state, have_of(h.TRUNK, TRUNK_FIELDS), "border")
    have = copy.deepcopy(reset_policies(calls1))
    have[0]["interfaces"][0].update(interfaceType="INTERFACE_ETHERNET", fabricName=h.FABRIC)
    result, calls = run(state, have, "border")
    assert not result.get("failed") and result["changed"] is False and h.writes(calls) == [], result.get("msg")


# ------------------------------------------------------------------ boundaries
@pytest.mark.parametrize("state", STATES)
def test_without_the_declaration_the_refusal_returns(state):
    rows = [table.resolve_by_nvpair(h.TRUNK, n) for n in SOURCE_ONLY]
    with patch.dict(rows[0], {"cleared_on_change_to": ()}), patch.dict(rows[2], {"cleared_on_change_to": ()}):
        result, calls = run(state, have_of(h.TRUNK, TRUNK_FIELDS), "border")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    msg = result["msg"]
    assert "acl_filter (aclFilter) on %s [%s], int_trunk_host -> int_routed_host" % (h.IF_A, h.SERIAL) in msg
    assert "guard_mode (GUARD_MODE)" in msg and "flowcontrol_receive" not in msg and ACL not in msg


@pytest.mark.parametrize("state", STATES)
def test_a_destination_not_declared_keeps_the_refusal(state):
    """int_trunk_host -> int_access_host is not a declared transition (not reachable by switch role today); forced here by
    making the role default an access payload. GUARD_MODE is not an access field, so it must be refused."""
    orig = module.DcnmIntf.dcnm_intf_get_default_eth_payload

    def access_default(self, ifname, sno, fabric):
        payload = orig(self, ifname, sno, fabric)
        payload["policy"] = h.ACCESS
        return payload
    with patch.object(module.DcnmIntf, "dcnm_intf_get_default_eth_payload", access_default):
        result, calls = run(state, have_of(h.TRUNK, {"GUARD_MODE": "root"}), "leaf")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    assert "guard_mode (GUARD_MODE) on %s [%s], int_trunk_host -> int_access_host" % (h.IF_A, h.SERIAL) in result["msg"]


@pytest.mark.parametrize("state", STATES)
def test_unreadable_value_still_refuses(state):
    result, calls = run(state, have_of(h.TRUNK, {"spanningTreePortType": "edge"}), "border")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    assert "not readable as its type" in result["msg"]


@pytest.mark.parametrize("state", STATES)
def test_leaf_same_parent_reset_keeps_the_verified_wires(state):
    result, calls = run(state, have_of(h.TRUNK, TRUNK_FIELDS), "leaf")
    assert not result.get("failed"), result.get("msg")
    sent = nvpairs_of_reset(calls)
    assert reset_policies(calls)[0]["policy"] == h.TRUNK
    for nvpair in TRUNK_FIELDS:
        assert sent[nvpair] == reset_wire(h.TRUNK, nvpair), nvpair


@pytest.mark.parametrize("state", STATES)
def test_capability_disabled_keeps_the_published_behaviour(state):
    result, calls = run(state, have_of(h.TRUNK, TRUNK_FIELDS), "border", patch_version=None)
    assert not result.get("failed"), result.get("msg")
    assert not any(k in nvpairs_of_reset(calls) for k in SOURCE_ONLY)


def test_only_the_declared_parents_carry_the_inline_marker():
    marked = {(r["parent_template"], tuple(r["cleared_on_change_to"])) for r in table.BINDING_TABLE if r.get("cleared_on_change_to")}
    # access loggingEventPortLinkStatus also declares int_trunk_host (measured for that field only)
    assert marked == {(h.TRUNK, (h.ROUTED,)), (h.ACCESS, (h.ROUTED,)), (h.ACCESS, (h.ROUTED, h.TRUNK))}
    assert sum(1 for r in table.BINDING_TABLE if r.get("cleared_on_change_to")) == 18   # + access loggingEventPortLinkStatus (0b_37)
    assert not any(r.get("cleared_on_change_to") and r.get("dropped_on_policy_change") for r in table.BINDING_TABLE)


# ====================================================================================================
# Formerly test_gie_border_ospf_reset.py
# D-3: a border (non-leaf) reset of a routed Ethernet to its own parent, int_routed_host, with OSPF still on.
#
# The reset already sends ospf "false" (its verified reset). The rows gated on OSPF or on authentication were judged
# against the gate in HAVE (on) and refused. They are now judged against the gate as this reset leaves it: HAVE, then the
# role default payload, then the verified resets of the same reset. Under that final gate the tag and the key type are
# inert and stay stored (never sent); the MD5 key declares `clear` and is cleared; the simple key and the options have
# their own resets. Unreadable values, EIGRP passive, the leaf policy change and the OSPF-off path are unchanged, and no
# stored secret appears in a request or a result. Real main() through helpers/binding_harness; values are synthetic.
# ====================================================================================================
SIMPLE_KEY = "SYN-SIMPLE-KEY"
MD5_KEY = "SYN-MD5-KEY"
OSPF_ON = {"ospf": "true", "ospfTag": "SYN-OSPF", "OSPF_AREA_ID": "0.0.0.1"}
GROUPS = {
    "tag": dict(OSPF_ON),
    "tag_and_options": dict(OSPF_ON, ospfCost="20", ospfNetworkType="point_to_point", ospfPassiveMode="passive",
                            ospfHelloInterval="5", ospfDeadInterval="20", ospfBfdMode="enable", ospfMtuIgnore="true"),
    "simple_key_type7": dict(OSPF_ON, ospfAuthenticationKey=SIMPLE_KEY, ospfAuthenticationKeyType="7"),
    "simple_key_type0": dict(OSPF_ON, ospfAuthenticationKey=SIMPLE_KEY, ospfAuthenticationKeyType="0"),
    "md5": dict(OSPF_ON, ospfAuthentication="true", OSPF_AUTH_KEY_ID="7", OSPF_AUTH_KEY=MD5_KEY),
    "md5_and_simple": dict(OSPF_ON, ospfAuthentication="true", OSPF_AUTH_KEY_ID="7", OSPF_AUTH_KEY=MD5_KEY,
                           ospfAuthenticationKey=SIMPLE_KEY, ospfAuthenticationKeyType="7"),
}


def routed_have(nv):
    have = copy.deepcopy(h.build_have(h.ROUTED))
    base = have[0]["interfaces"][0]["nvPairs"]
    base["ospf"] = "false"
    base.update(nv)
    return have


def no_secret(calls, result):
    text = json.dumps([c.get("payload") for c in calls], default=str) + json.dumps(result, default=str)
    return SIMPLE_KEY not in text and MD5_KEY not in text


# ------------------------------------------------------------------ the finding, fixed
@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("group", sorted(GROUPS))
def test_border_reset_turns_ospf_off_in_the_same_write(state, group):
    result, calls = run(state, routed_have(GROUPS[group]), "border")
    assert not result.get("failed"), result.get("msg")
    assert len(h.split_calls(calls)["updates"]) == 1 and reset_policies(calls)[0]["policy"] == h.ROUTED
    sent = nvpairs_of_reset(calls)
    assert sent["ospf"] == reset_wire(h.ROUTED, "ospf")
    assert "ospfTag" not in sent                                   # inert under the final gate: kept, never sent
    assert "ospfAuthenticationKeyType" not in sent                 # inert once the simple key is reset to ""
    for nvpair in GROUPS[group]:
        if nvpair in ("ospf", "ospfTag", "ospfAuthenticationKeyType"):
            continue
        if nvpair == "OSPF_AUTH_KEY":
            assert sent[nvpair] == ""                              # clear: key material is cleared, not kept
            continue
        assert sent[nvpair] == reset_wire(h.ROUTED, nvpair), nvpair
    assert no_secret(calls, result)


@pytest.mark.parametrize("state", STATES)
def test_requests_equal_the_ospf_off_reset(state):
    _r0, calls0 = run(state, routed_have({"ospf": "false", "ospfTag": "SYN-OSPF"}), "border")
    _r1, calls1 = run(state, routed_have(GROUPS["md5_and_simple"]), "border")
    assert [(c["method"], c["path"]) for c in calls1] == [(c["method"], c["path"]) for c in calls0]


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("keep_tag", (True, False))
def test_second_run_over_the_reset_is_a_noop_border_ospf(state, keep_tag):
    """The controller may keep the inert tag (measured for a disable) or drop it; either HAVE is converged."""
    _r1, calls1 = run(state, routed_have(GROUPS["md5_and_simple"]), "border")
    have = copy.deepcopy(reset_policies(calls1))
    have[0]["interfaces"][0].update(interfaceType="INTERFACE_ETHERNET", fabricName=h.FABRIC)
    if keep_tag:
        have[0]["interfaces"][0]["nvPairs"].update(ospfTag="SYN-OSPF", ospfAuthenticationKeyType="7")
    result, calls = run(state, have, "border")
    assert not result.get("failed") and result["changed"] is False and h.writes(calls) == [], result.get("msg")


# ------------------------------------------------------------------ unchanged boundaries
@pytest.mark.parametrize("state", STATES)
def test_unreadable_gate_still_refuses_and_names_the_gate(state):
    result, calls = run(state, routed_have(dict(OSPF_ON, ospf="True")), "border")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    msg = result["msg"]
    assert "enable_ospf (ospf) on %s [%s], parent int_routed_host" % (h.IF_A, h.SERIAL) in msg
    assert "not readable as its type" in msg
    assert "ospf_tag (ospfTag)" in msg and "disable enable_ospf on the current policy first" in msg


@pytest.mark.parametrize("state", STATES)
def test_unreadable_dependent_still_refuses(state):
    have = routed_have(dict(OSPF_ON, ospfAuthenticationKey=SIMPLE_KEY, ospfAuthenticationKeyType="9"))
    result, calls = run(state, have, "border")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    assert "ospf_authentication_key_type (ospfAuthenticationKeyType)" in result["msg"]
    assert "not readable as its type" in result["msg"] and no_secret(calls, result)


@pytest.mark.parametrize("state", STATES)
def test_eigrp_passive_still_refuses_and_names_only_itself(state):
    have = routed_have(dict(OSPF_ON, eigrpRouting="true", eigrpProcessTag="SYN-EIGRP", eigrpIpv4Passive="true"))
    result, calls = run(state, have, "border")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    assert "eigrp_ipv4_passive (eigrpIpv4Passive)" in result["msg"] and "ospf_tag" not in result["msg"]


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("group", sorted(GROUPS))
def test_leaf_policy_change_is_unchanged(state, group):
    result, calls = run(state, routed_have(GROUPS[group]), "leaf")
    assert not result.get("failed"), result.get("msg")
    sent = nvpairs_of_reset(calls)
    assert reset_policies(calls)[0]["policy"] == h.TRUNK
    assert not any(k in sent for k in GROUPS[group]) and no_secret(calls, result)


@pytest.mark.parametrize("state", STATES)
def test_ospf_off_border_reset_is_unchanged(state):
    have = routed_have({"ospf": "false", "ospfTag": "SYN-OSPF", "ospfAuthenticationKey": "",
                        "ospfAuthenticationKeyType": "7"})
    result, calls = run(state, have, "border")
    assert not result.get("failed"), result.get("msg")
    sent = nvpairs_of_reset(calls)
    assert "ospf" not in sent and "ospfTag" not in sent and "ospfAuthenticationKeyType" not in sent


@pytest.mark.parametrize("state", STATES)
def test_capability_disabled_keeps_the_published_behaviour_border_ospf(state):
    result, calls = run(state, routed_have(GROUPS["md5"]), "border", patch_version=None)
    assert not result.get("failed"), result.get("msg")
    assert no_secret(calls, result)


# ====================================================================================================
# Formerly test_gie_vpc13_resets.py
# ``int_vpc_access_host`` / ``int_vpc_trunk_host``: the thirteen resets, measured live.
#
# Until this lot the two vPC host parents carried thirteen registered identities with no
# ``reset_wire``, so omitting any of them under ``replaced`` refused the whole invocation. All
# thirteen are withdrawable. Six live on both parents; ``guard_mode`` is declared only by the trunk
# parent, which is why the lot is thirteen and not fourteen.
#
# WHERE THE VALUES COME FROM
# Measured on a vPC pair (NDFC 12.6.0.267, NX-OS 10.5(5)), one access and one trunk vPC with one
# member each, observed on BOTH peers::
#
#     stage m1  all thirteen non-neutral   -> every expected line present on both peers
#     stage m2  all thirteen at neutral    -> the target lines gone, prerequisites intact
#
# NEITHER VALUE WAS TRANSFERRED FROM A SIBLING PARENT.
# ``int_access_host`` already carries ``acl_filter -> ''`` and ``disable_lldp_receive -> 'false'``.
# That is not evidence about these parents: a reset is a property of the parent that emits it, and the
# IsShow gate, the emitting child and the default can all differ. Each of the thirteen was measured on
# the vPC parents themselves.
#
# THE EMISSION PLANE IS NOT UNIFORM, AND THAT SHAPED THE MEASUREMENT
# The parents emit no CLI of their own. They instantiate child PTIs and hand the nvPairs down, one per
# peer: ``int_vpc_*_po_11_1`` on the port-channel and ``int_vpc_*_po_member_11_1`` on each physical
# member. So::
#
#     acl_filter, disable_qos_stats, disable_queuing_stats,
#     spanning_tree_port_type, guard_mode          -> observed on the port-channel
#     disable_lldp_receive, disable_lldp_transmit   -> observed on the member
#
# Looking for the LLDP lines on the port-channel would report a false negative for a field that is
# working correctly, and vice versa.
#
# THE TWO STATS FIELDS ARE A SUFFIX, NOT A LINE
# ``disable_qos_stats`` and ``disable_queuing_stats`` append ``" no-stats"`` to a ``service-policy``
# line. Their withdrawal therefore leaves the ``service-policy`` line ALIVE and removes only the
# suffix -- measured, both peers, both subjects. The clear was driven with ``enable_qos: true``,
# ``qos_policy`` and ``queuing_policy`` held explicit: turning QoS off would have removed the line
# itself, which is destroying the prerequisite rather than withdrawing the field.
#
# ``spanning_tree_port_type`` WAS MEASURED WITH ``port_type_fast`` HELD FALSE
# The emitting child branches::
#
#     if spanningTreePortType != "" and != "no":  -> spanning-tree port type <value>
#     elif PORTTYPE_FAST_ENABLED == "true":      -> spanning-tree port type edge trunk
#
# ``port_type_fast`` defaults to ``True`` in the module's own vPC profile spec. With that default in
# play the neutral does not produce absence: it produces a DIFFERENT line. The parent also rejects the
# combination outright with ``setFailureRetCode`` (access L560, trunk L694). Every stage therefore held
# ``port_type_fast: false`` explicit, so the omission under test changed exactly one thing.
#
# WHAT THESE OFFLINE CASES COVER
# They cover registration and engine decisions. The sibling
# ``test_binding_routed.py`` drives the real module entry with the paired
# inventory and VPC_SNO response. Neither offline test certifies the integrated tuple
# on a controller or device.
#
# Offline: no controller and no device.
# ====================================================================================================
VPC_ACCESS = "int_vpc_access_host"
VPC_TRUNK = "int_vpc_trunk_host"
SUPPORTED = "12.6.0.267"
# Declared explicitly so these pre-existing reset fixtures keep
# exercising the NDFC-version boundary alone, not the (new, additional) patch boundary.
PATCH = sorted(GIE_ENABLED_PATCH_VERSIONS)[0]

# (parent, profile_key, parent_nvpair, type, reset_wire, a value evidenced as NON-reset)
#
# The `applied` column is not decoration: a withdrawal case needs a HAVE the field actually had.
# Each value here is the one the live positive stage really sent and the device really rendered --
# `normal` on access and `network` on trunk deliberately differ, so an enum that collapsed to a
# single constant could not pass by accident.
VPC_ROWS = [
    (VPC_ACCESS, "acl_filter", "aclFilter", "string", "", "pr725_vpc13_acl"),
    (VPC_ACCESS, "disable_lldp_receive", "lldpReceive", "boolean", "false", "true"),
    (VPC_ACCESS, "disable_lldp_transmit", "lldpTransmit", "boolean", "false", "true"),
    (VPC_ACCESS, "disable_qos_stats", "qosStatsSuppressed", "boolean", "false", "true"),
    (VPC_ACCESS, "disable_queuing_stats", "queuingStats", "boolean", "false", "true"),
    (VPC_ACCESS, "spanning_tree_port_type", "spanningTreePortType", "enum", "no", "normal"),
    (VPC_TRUNK, "acl_filter", "aclFilter", "string", "", "pr725_vpc13_acl"),
    (VPC_TRUNK, "disable_lldp_receive", "lldpReceive", "boolean", "false", "true"),
    (VPC_TRUNK, "disable_lldp_transmit", "lldpTransmit", "boolean", "false", "true"),
    (VPC_TRUNK, "disable_qos_stats", "qosStatsSuppressed", "boolean", "false", "true"),
    (VPC_TRUNK, "disable_queuing_stats", "queuingStats", "boolean", "false", "true"),
    (VPC_TRUNK, "spanning_tree_port_type", "spanningTreePortType", "enum", "no", "network"),
    (VPC_TRUNK, "guard_mode", "GUARD_MODE", "enum", "no", "root"),
]

VPC_CASES = [pytest.param(*f, id="{0}-{1}".format(f[0].replace("int_vpc_", "").replace("_host", ""), f[1]))
             for f in VPC_ROWS]


def test_the_lot_is_thirteen_and_the_fixture_matches_the_table():
    """Guard the guard, before any case below can pass for the wrong reason.

    Two failure modes this closes. First, a fixture that drifts from the table: every case below
    reads its expectations from ``VPC_ROWS``, so a row silently dropped from the registry would simply
    stop being tested rather than fail. Second, a lot that grew or shrank: the claim is
    thirteen identities on these two parents, and if the table ever carries a fourteenth this case
    fails instead of the count quietly changing underneath the documented claim.
    """
    in_table = {(r["parent_template"], r["profile_key"]) for r in BINDING_TABLE
                if r["parent_template"] in (VPC_ACCESS, VPC_TRUNK)}
    in_fixture = {(f[0], f[1]) for f in VPC_ROWS}
    assert len(VPC_ROWS) == 13, "the fixture lists {0} rows, not 13".format(len(VPC_ROWS))
    assert in_table == in_fixture, (
        "the table and this fixture disagree: only in table {0}, only in fixture {1}".format(
            in_table - in_fixture, in_fixture - in_table))


def test_guard_mode_is_declared_by_the_trunk_parent_only():
    """Why the lot is thirteen and not fourteen.

    ``GUARD_MODE`` is declared by ``int_vpc_trunk_host`` and NOT by ``int_vpc_access_host`` -- read
    from the installed bodies, and the reason 6 + 7 = 13. Asserting it here keeps the asymmetry
    honest: a later change that registered it on access too would make the arithmetic
    wrong, and nothing else in this file would notice.
    """
    assert resolve_binding(VPC_TRUNK, "guard_mode") is not None
    assert resolve_binding(VPC_ACCESS, "guard_mode") is None, (
        "guard_mode appeared on the access parent; the lot is no longer 6 + 7 = 13")


@pytest.mark.parametrize("parent,key,nvpair,nv_type,reset,_applied", VPC_CASES)
def test_the_row_declares_the_measured_reset_with_the_right_type(
        parent, key, nvpair, nv_type, reset, _applied):
    """The registration itself, including the PYTHON type of the reset.

    The type matters as much as the value. The controller returns these nvPairs as STRINGS, so a
    boolean reset has to be the string ``"false"`` and not native ``False``. The two are not
    interchangeable in either direction: ``False == "false"`` is False, so a comparison against the
    HAVE would never match, and in a truth test they are OPPOSITE -- the non-empty string
    ``"false"`` is truthy while native ``False`` is falsy. The same applies to ``acl_filter``, whose
    reset is the empty STRING.
    """
    b = resolve_binding(parent, key)
    assert b is not None, "{0}::{1} is not registered".format(parent, key)
    assert b["parent_nvpair"] == nvpair, (
        "{0}::{1} wire name is {2!r}, expected {3!r}".format(parent, key, b["parent_nvpair"], nvpair))
    assert b["type"] == nv_type
    assert b.get("reset_wire") == reset, (
        "{0}::{1} reset is {2!r}, expected {3!r}".format(parent, key, b.get("reset_wire"), reset))
    assert isinstance(b.get("reset_wire"), str), (
        "{0}::{1} reset must be a str, got {2}".format(parent, key, type(b.get("reset_wire")).__name__))


@pytest.mark.parametrize("parent,key,_nv,_t,reset,applied", VPC_CASES)
def test_the_engine_withdraws_a_configured_value(parent, key, _nv, _t, reset, applied):
    """A HAVE the field actually had yields the measured reset, exactly.

    ``applied`` is the value the live positive stage really sent, not a placeholder, so this asserts
    the decision the engine makes for the state the lab was really in.
    """
    assert gie_withdrawal_action(parent, key, applied, SUPPORTED, PATCH) == (
        GIE_WITHDRAW_RESET, reset)


@pytest.mark.parametrize("parent,key,_nv,_t,reset,_applied", VPC_CASES)
def test_the_engine_withdraws_nothing_when_the_value_already_is_the_reset(
        parent, key, _nv, _t, reset, _applied):
    """NEGATIVE CONTROL. Nothing to withdraw is not the same as withdrawing the reset.

    Without this the case above would pass for an engine that emitted the reset unconditionally,
    which would turn every converged rerun into a write. This is the assertion that makes the rerun
    idempotent rather than merely quiet.
    """
    assert gie_withdrawal_action(parent, key, reset, SUPPORTED, PATCH) == (
        GIE_WITHDRAW_NONE, None)


@pytest.mark.parametrize("parent,key,_nv,_t,reset,applied", VPC_CASES)
def test_the_reset_is_refused_below_the_minimum_version(parent, key, _nv, _t, reset, applied):
    """NEGATIVE CONTROL on the version axis.

    Every one of the thirteen declares ``min_ndfc_version: 12.6.0.267``. On an older controller the
    nvPair does not exist, so emitting a reset for it would write a field the template never had.
    A withdrawal that ignored the floor would look identical to a correct one on the supported
    controller, which is exactly why the floor gets its own case.
    """
    b = resolve_binding(parent, key)
    assert b["min_ndfc_version"] == SUPPORTED
    action, value = gie_withdrawal_action(parent, key, applied, "12.6.0.266", PATCH)
    assert (action, value) != (GIE_WITHDRAW_RESET, reset), (
        "{0}::{1} withdrew on a controller below its declared floor".format(parent, key))


def test_the_two_parents_are_independent_identities():
    """Thirteen bindings, not two parents times a shared list.

    The six shared keys are SEPARATE rows: N proofs of one field are not N fields proved. This case
    fails if the two parents ever start resolving to the same object, which would make half the lot
    untested while every case above still passed.
    """
    shared_keys = ("acl_filter", "disable_lldp_receive", "disable_lldp_transmit",
                   "disable_qos_stats", "disable_queuing_stats", "spanning_tree_port_type")
    for key in shared_keys:
        a = resolve_binding(VPC_ACCESS, key)
        t = resolve_binding(VPC_TRUNK, key)
        assert a is not None and t is not None
        assert a is not t, "{0} resolves to one shared object on both parents".format(key)
        assert a["parent_template"] == VPC_ACCESS
        assert t["parent_template"] == VPC_TRUNK
        # same wire name and same reset, but reached through two distinct rows
        assert a["parent_nvpair"] == t["parent_nvpair"]
        assert a["reset_wire"] == t["reset_wire"]


def test_the_previous_lot_is_untouched():
    """The arithmetic: 128 + 13 = 141, and nothing else moved.

    A merge script that inserted a reset into the wrong row would still leave the count at 141, so
    counting alone is not enough -- the thirteen are named. ``disable_lldp`` is named too and
    asserted to have NO reset: it lives in the same slices, it is a PREFIX of
    ``disable_lldp_receive`` and ``disable_lldp_transmit``, and it is the row a substring match
    would have hit instead. It is not part of this lot and must stay unregistered.
    """
    with_reset = [r for r in BINDING_TABLE if r.get("reset_wire") is not None]
    # 234 = 228 + six int_vpc_dot1q_tunnel rows; 245 = 234 + eleven PVLAN companion rows; 246 = + one vPC PVLAN row.
    assert len(BINDING_TABLE) == 295, "the table has {0} identities".format(len(BINDING_TABLE))   # + slices 0b_37 to 0b_41, rs1, pl1, ul1
    # 197 integrated + 3 int_vlan rows (test_binding_role_resets.py) = 200, + the six
    # int_vpc_dot1q_tunnel resets = 206, + the existing
    # int_vlan::privateVlanMapping reset = 207. Those rows live on other parents, so the
    # access/trunk set below is unchanged.
    # + the eleven PVLAN companion resets (inferred, other parents) = 218, + the vPC PVLAN qosStatsSuppressed reset = 219.
    # + 5 SMU 017 resets read from the bodies (slice 0b_37) = 224, + 5 loopback EIGRP resets (slice 0b_38) = 229,
    # + 1 routed port-channel PIM BFD reset (slice 0b_39) = 230, + 16 routed port-channel OSPF resets (slice 0b_40) = 246,
    # + 1 trunk port-channel reset-skip reset (slice rs1) = 247, + 2 peer-link resets (slice pl1) = 249,
    # + 12 uplink resets (slice ul1) = 261, + 2 routed port-channel PIM resets (slice 0b_41) = 263.
    assert len(with_reset) == 197 + 3 + 6 + 1 + 11 + 1 + 5 + 5 + 1 + 16 + 1 + 2 + 12 + 2, (
        "the integrated table carries {0} resets, expected 263".format(len(with_reset)))
    lot_rows = {(r["parent_template"], r["profile_key"]) for r in with_reset
                if r["parent_template"] in (VPC_ACCESS, VPC_TRUNK)}
    assert lot_rows == {(f[0], f[1]) for f in VPC_ROWS}
    for parent in (VPC_ACCESS, VPC_TRUNK):
        neighbour = resolve_binding(parent, "disable_lldp")
        if neighbour is not None:
            assert neighbour.get("reset_wire") is None, (
                "{0}::disable_lldp got a reset; it is not part of this lot and is the row a "
                "substring match on `disable_lldp` would have hit".format(parent))


# ====================================================================================================
# Formerly test_gie_hsrp3_resets.py
# ``int_vlan`` HSRP: the preempt delay and the forwarding-threshold pair, measured live.
#
# Until this lot the three identities carried no ``reset_wire``, so omitting any of them under
# ``replaced`` refused the whole invocation. All three are now withdrawable.
#
# WHERE THE VALUES COME FROM
# Measured on an SVI, with HSRP version 2, group 79,
# documentation-range VIP 192.0.2.254, priority 120 and preempt enabled::
#
#     positive   preempt delay minimum 45
#                priority 120 forwarding-threshold lower 90 upper 110
#     clear      the three nvPairs to "" through a raw preserving update (they are INTEGERS and the
#                public empty string stays refused), then an interface-scoped deploy
#     device     `preempt` and `priority 120` SURVIVED without their suffixes; the VIP, the version
#                and the interface address were untouched
#
# THE WITHDRAWAL DEGRADES, IT DOES NOT DELETE
# The parent emits no CLI of its own. With PREEMPT true it emits either the delay child
# (``preempt delay minimum <v>``) or the plain ``interface_hsrp_preempt`` child; with a priority other
# than 100 it emits either the threshold child or the plain ``interface_hsrp_priority`` child. So the
# reset leaves the host line in place and removes only the clause. Every case below therefore holds
# ``preempt`` and ``hsrp_priority`` explicit: turning either off would remove the line itself, which is
# destroying the prerequisite, not withdrawing the field.
#
# THE THRESHOLDS ARE A COORDINATED PAIR
# One child emits both, and the installed body rejects either alone ("Both HSRP lower and upper
# forwarding thresholds are required"). They were measured together and are covered together here;
# per-row fixtures for them would describe a request the controller refuses, which is why the shared
# harness lists them as grouped-only.
#
# OUT OF THIS LOT
# ``hsrp_vipv6`` and ``hsrp_groupv6`` are NOT registered. On the measured controller the installed
# ``int_vlan`` body emitted no IPv6 line at all for this subject, so neither has an observable positive
# or a measurable clear. They stay unregistered and a case below pins that.
#
# Offline: no controller and no device.
# ====================================================================================================
# (profile_key, parent_nvpair, reset_wire, the value the live positive really sent)
ROWS = [
    ("hsrp_preempt_delay_minimum", "hsrpPreemptDelayMinimum", "", 45),
    ("hsrp_priority_forwarding_threshold_lower", "hsrpPriorityForwardingThresholdLower", "", 90),
    ("hsrp_priority_forwarding_threshold_upper", "hsrpPriorityForwardingThresholdUpper", "", 110),
]
IDS = [r[0] for r in ROWS]
PAIR = {"hsrp_priority_forwarding_threshold_lower": 90,
        "hsrp_priority_forwarding_threshold_upper": 110}
POSITIVE = dict(HSRP_CTX, hsrp_preempt_delay_minimum=45, **PAIR)


def _have(**extra):
    return build_have(SVI, **dict(POSITIVE, **extra))


def _hsrp_run(profile, state, have, check_mode=False):
    return run_configs([cfg_for(SVI, profile)], state, have=have, check_mode=check_mode)


@pytest.mark.parametrize("key,nvpair,reset,_applied", ROWS, ids=IDS)
def test_the_row_declares_the_measured_reset_as_a_string(key, nvpair, reset, _applied):
    """The registration, including the Python type. The controller returns these nvPairs as
    strings, so the reset is the empty STRING, not ``None`` and not ``0``."""
    b = resolve_binding(SVI, key)
    assert b is not None, "%s::%s is not registered" % (SVI, key)
    assert b["parent_nvpair"] == nvpair
    assert b["type"] == "integer"
    assert b.get("reset_wire") == reset and isinstance(b.get("reset_wire"), str), (
        "%s::%s reset is %r" % (SVI, key, b.get("reset_wire")))


@pytest.mark.parametrize("key,_nv,reset,applied", ROWS, ids=IDS)
def test_the_engine_withdraws_the_applied_value(key, _nv, reset, applied):
    assert gie_withdrawal_action(SVI, key, str(applied), SUPPORTED, SUPPORTED_PATCH) == (
        GIE_WITHDRAW_RESET, reset)


@pytest.mark.parametrize("key,_nv,reset,_applied", ROWS, ids=IDS)
def test_nothing_is_withdrawn_when_the_value_already_is_the_reset(key, _nv, reset, _applied):
    """NEGATIVE CONTROL: without it an engine that always emitted the reset would pass the case
    above and turn every converged rerun into a write."""
    assert gie_withdrawal_action(SVI, key, reset, SUPPORTED, SUPPORTED_PATCH) == (
        GIE_WITHDRAW_NONE, None)


@pytest.mark.parametrize("key,_nv,reset,applied", ROWS, ids=IDS)
def test_the_reset_is_refused_below_the_minimum_version_hsrp(key, _nv, reset, applied):
    assert resolve_binding(SVI, key)["min_ndfc_version"] == SUPPORTED
    assert gie_withdrawal_action(SVI, key, str(applied), "12.6.0.266", SUPPORTED_PATCH) != (
        GIE_WITHDRAW_RESET, reset)


def test_the_threshold_pair_is_declared_grouped_only_and_the_delay_is_not():
    assert (SVI, "hsrpPriorityForwardingThresholdLower") in GROUPED_ONLY_NO_PER_ROW_FIXTURE
    assert (SVI, "hsrpPriorityForwardingThresholdUpper") in GROUPED_ONLY_NO_PER_ROW_FIXTURE
    assert (SVI, "hsrpPreemptDelayMinimum") not in GROUPED_ONLY_NO_PER_ROW_FIXTURE


@pytest.mark.parametrize("key", IDS)
def test_the_public_empty_string_stays_refused(key):
    """The reset is emitted by the engine on withdrawal only. An operator cannot type it."""
    result, calls = _hsrp_run(dict(POSITIVE, **{key: ""}), "merged", have=_have())
    assert result.get("failed"), "the public empty string was accepted for %s" % key
    assert split_calls(calls)["updates"] == [] and split_calls(calls)["deploys"] == []


def test_merged_preserves_all_three():
    """CONTROL: the omission itself withdraws nothing under merged."""
    want = base_for(SVI, **dict(HSRP_CTX, description="hsrp3-merged"))
    result, calls = _hsrp_run(want, "merged", have=_have())
    assert not result.get("failed"), result.get("msg")
    nv = request_nvpairs(calls)
    assert nv, "the description change produced no request"
    for key, nvpair, _r, applied in ROWS:
        assert nv[0].get(nvpair) == str(applied), (nvpair, nv[0].get(nvpair))


def test_check_mode_plans_the_three_and_transmits_nothing():
    result, calls = _hsrp_run(base_for(SVI, **HSRP_CTX), "replaced", have=_have(), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    dnv = diff_nvpairs(result)
    assert dnv, "check mode planned nothing"
    for _k, nvpair, reset, _a in ROWS:
        assert dnv[0].get(nvpair) == reset, (nvpair, dnv[0].get(nvpair))
    assert split_calls(calls)["updates"] == [] and split_calls(calls)["deploys"] == []


def test_replaced_withdraws_the_three_in_one_request_and_keeps_the_hosts():
    """The pair travels in the SAME request -- a split is the shape the controller refuses -- and
    the host lines' prerequisites (PREEMPT, HSRP_PRIORITY, the VIP, the group) travel unchanged."""
    result, calls = _hsrp_run(base_for(SVI, **HSRP_CTX), "replaced", have=_have())
    assert not result.get("failed"), result.get("msg")
    updates = split_calls(calls)["updates"]
    assert len(updates) == 1, "expected exactly one request, got %d" % len(updates)
    nv = request_nvpairs(calls)[0]
    for _k, nvpair, reset, _a in ROWS:
        assert nv.get(nvpair) == reset, (nvpair, nv.get(nvpair))
    assert nv.get("PREEMPT") == "true"
    assert nv.get("HSRP_PRIORITY") == "120"
    assert nv.get("HSRP_VIP") == "192.0.2.254" and nv.get("HSRP_GROUP") == "79"
    assert nv.get("ENABLE_HSRP") == "true"


def test_the_rerun_converges():
    have = _have()
    for _k, nvpair, reset, _a in ROWS:
        have[0]["interfaces"][0]["nvPairs"][nvpair] = reset
    result, calls = _hsrp_run(base_for(SVI, **HSRP_CTX), "replaced", have=have)
    assert not result.get("failed"), result.get("msg")
    assert split_calls(calls)["updates"] == [], "a converged rerun wrote"
    assert result.get("changed") is False


def test_the_deferred_ipv6_rows_stay_unregistered():
    """``hsrp_vipv6`` / ``hsrp_groupv6`` had no observable positive on the measured controller.
    Registering them here would claim a withdrawal nobody observed."""
    for key in ("hsrp_vipv6", "hsrp_groupv6"):
        b = resolve_binding(SVI, key)
        assert b is not None and b.get("reset_wire") is None, (key, b and b.get("reset_wire"))


def test_the_arithmetic_is_197_plus_three():
    """246 identities, 219 resets, and these three are the only int_vlan HSRP rows with one."""
    with_reset = [r for r in BINDING_TABLE if r.get("reset_wire") is not None]
    # 228 + six dot1q rows + eleven PVLAN companion rows + one vPC PVLAN row, + slices 0b_37, 0b_38, 0b_39, 0b_40, rs1,
    # pl1, ul1 and 0b_41.
    assert len(BINDING_TABLE) == 234 + 11 + 1 + 5 + 5 + 1 + 19 + 1 + 4 + 12 + 2
    # 200 + six dot1q resets + int_vlan::privateVlanMapping = 207, + 11 PVLAN companion resets (inferred) = 218, + 1 vPC PVLAN reset = 219.
    # + 5 SMU 017 resets read from the bodies (slice 0b_37) = 224, + 5 loopback EIGRP resets (slice 0b_38) = 229,
    # + 1 routed port-channel PIM BFD reset (slice 0b_39) = 230, + 16 routed port-channel OSPF resets (slice 0b_40) = 246,
    # + 1 trunk port-channel reset-skip reset (slice rs1) = 247, + 2 peer-link resets (slice pl1) = 249,
    # + 12 uplink resets (slice ul1) = 261, + 2 routed port-channel PIM resets (slice 0b_41) = 263.
    assert len(with_reset) == 197 + 3 + 6 + 1 + 11 + 1 + 5 + 5 + 1 + 16 + 1 + 2 + 12 + 2, (
        "the table carries %d resets, expected 263" % len(with_reset))
    hsrp = {r["profile_key"] for r in with_reset
            if r["parent_template"] == SVI and r["profile_key"].startswith("hsrp")}
    assert hsrp == set(IDS), sorted(hsrp)


def test_the_omission_want_really_omits():
    """The absence must be effective: the base SVI profile plus the HSRP context carries none of
    the three, so the cases above measure an omission and not an ordinary apply."""
    want = base_for(SVI, **HSRP_CTX)
    assert not [k for k in IDS if k in want]


# ====================================================================================================
# Formerly test_gie_routed_lldp_reset.py
# ``int_routed_host`` LLDP: the two resets, measured live and now registered.
#
# Until this lot, ``disable_lldp_transmit`` and ``disable_lldp_receive`` were registered on
# ``int_routed_host`` with no ``reset_wire``, so omitting either one under ``replaced`` refused the
# whole invocation. They are withdrawable, and the wire value is the string ``"false"``.
#
# WHY THE MEASUREMENT NEEDED A COMPANION HELD AT TRUE
# ``int_routed_host`` does not emit the LLDP CLI itself. Read from the template installed on the
# controller (NDFC 12.6.0.267), the parent instantiates a child and gates it on an OR::
#
#     lldpTransmit = normalize(scope.get("lldpTransmit", "false")).lower()
#     lldpReceive  = normalize(scope.get("lldpReceive",  "false")).lower()
#     if lldpTransmit == "true" or lldpReceive == "true":
#         "interface_lldp_disable",
#         "DISABLE_LLDP_TRANSMIT": lldpTransmit,
#         "DISABLE_LLDP_RECEIVE":  lldpReceive
#
# and the child emits one line per direction::
#
#     if ($$DISABLE_LLDP_TRANSMIT$$ == "true") { no lldp transmit }
#     if ($$DISABLE_LLDP_RECEIVE$$  == "true") { no lldp receive  }
#
# So driving both to ``"false"`` destroys the child and both lines disappear together -- which proves
# nothing about either field on its own. The live measurement therefore held the companion explicitly
# at ``"true"`` so the child stayed alive, and only the target's line went away. Evidence:
#
#     both true          -> both lines present        (positive control)
#     transmit -> false  -> only `no lldp transmit` gone, receive survived
#     both true again    -> both lines present again  (positive control for the mirror)
#     receive  -> false  -> only `no lldp receive` gone, transmit survived
#
# The polarity was read from the child's
# body, not inferred from the positive nvPair name: ``"true"`` means *disable*.
#
# WHAT THESE CASES CANNOT PROVE
# That the child template exists on the controller, or that the device drops the line. A missing child
# would transport the nvPair, return success and produce no CLI -- exercised, never validated. The live
# stages above are what closed that; these cases hold the contract in place afterwards.
#
# Offline: no controller and no device.
# ====================================================================================================
TX = "disable_lldp_transmit"
RX = "disable_lldp_receive"
W_TX = "lldpTransmit"
W_RX = "lldpReceive"
RESET = "false"

# (target public key, target nvPair, companion public key, companion nvPair)
DIRECTIONS = [
    pytest.param(TX, W_TX, RX, W_RX, id="transmit"),
    pytest.param(RX, W_RX, TX, W_TX, id="receive"),
]


def _both_true_have():
    """HAVE with both directions disabled, taken from the module's own outbound payload.

    Built through ``build_have`` rather than hand-written: a fixture invented by the test can
    assert a shape the module never produces, and this contract is about what the module does with
    a HAVE the controller actually returns.
    """
    return build_have(ROUTED, key=TX, value=True, **{RX: True})


def _profile_holding(companion):
    """The withdrawal profile: the target OMITTED, the companion declared ``True``.

    Omission is the whole point -- an explicit ``False`` would be an ordinary apply, not a
    withdrawal, and would prove nothing about ``replaced``.
    """
    return base_for(ROUTED, **{companion: True})


# --------------------------------------------------------------- the registration itself

@pytest.mark.parametrize("key,nvpair,_c,_cw", DIRECTIONS)
def test_the_reset_is_registered_as_the_string_false(key, nvpair, _c, _cw):
    """Guard the guard.

    Every case below is meaningless if the row stopped declaring the reset, and they would all pass
    for the wrong reason. The type matters as much as the value: the controller returns this nvPair
    as a string, so the reset must be the string ``"false"``. A native bool is not interchangeable
    with it in either direction -- ``False == "false"`` is False, so the comparison against the HAVE
    would never match, and in a boolean test the two are OPPOSITE: the non-empty string ``"false"``
    is truthy while native ``False`` is falsy.
    """
    binding = resolve_binding(ROUTED, key)
    assert binding is not None, "{0}::{1} is not registered".format(ROUTED, key)
    assert binding["parent_nvpair"] == nvpair
    assert binding.get("reset_wire") == RESET
    assert isinstance(binding.get("reset_wire"), str)
    assert binding.get("default_template") is False


@pytest.mark.parametrize("key,_nv,_c,_cw", DIRECTIONS)
def test_the_engine_resets_a_configured_value_and_leaves_a_default_alone(key, _nv, _c, _cw):
    """``have == declared default`` is nothing to withdraw; anything else is the reset."""
    assert gie_withdrawal_action(ROUTED, key, "true", ROUTED_LLDP_SUPPORTED, SUPPORTED_PATCH) == (
        GIE_WITHDRAW_RESET, RESET)
    assert gie_withdrawal_action(ROUTED, key, RESET, ROUTED_LLDP_SUPPORTED, SUPPORTED_PATCH) == (
        GIE_WITHDRAW_NONE, None)


# --------------------------------------------------------------- independence, both directions

@pytest.mark.parametrize("key,nvpair,companion,comp_nv", DIRECTIONS)
def test_replaced_withdraws_only_the_omitted_direction(key, nvpair, companion, comp_nv):
    """The reset for the target travels; the companion keeps the value it was given.

    This is the case the live stages M2 and M4 measured. Both directions are exercised because they
    are two separate identities in the table: N proofs of one field are not N fields proved.
    """
    result, calls = routed_lldp_run(_profile_holding(companion), "replaced", have=_both_true_have())
    assert not result.get("failed"), result.get("msg")

    sent = request_nvpairs(calls)
    assert sent, "the module sent no nvPairs at all, so nothing was withdrawn"
    target = [m[nvpair] for m in sent if nvpair in m]
    held = [m[comp_nv] for m in sent if comp_nv in m]
    assert target == [RESET] * len(target) and target, (
        "expected {0} to travel as {1!r}, got {2!r}".format(nvpair, RESET, target))
    assert held == ["true"] * len(held) and held, (
        "the companion {0} must survive at 'true', got {1!r}".format(comp_nv, held))


@pytest.mark.parametrize("key,nvpair,companion,comp_nv", DIRECTIONS)
def test_merged_does_not_withdraw_the_omitted_direction(key, nvpair, companion, comp_nv):
    """Under ``merged`` an omission preserves. Only ``replaced`` withdraws.

    Without this the reset cases above would not establish that the withdrawal belongs to
    ``replaced``: an omission that cleared the field under every state would be a different, much
    worse behaviour that the same assertions would happily accept.
    """
    result, calls = routed_lldp_run(_profile_holding(companion), "merged", have=_both_true_have())
    assert not result.get("failed"), result.get("msg")
    sent = request_nvpairs(calls)
    assert RESET not in [m[nvpair] for m in sent if nvpair in m], (
        "{0} was reset under `merged`; an omission there must preserve".format(nvpair))


@pytest.mark.parametrize("key,nvpair,companion,comp_nv", DIRECTIONS)
def test_check_mode_plans_the_reset_and_writes_nothing(key, nvpair, companion, comp_nv):
    """The plan is visible and the controller is untouched.

    ``updates`` and ``deploys`` are asserted separately: a single "writes" bucket cannot show a run
    that configured nothing yet still deployed.
    """
    result, calls = routed_lldp_run(_profile_holding(companion), "replaced",
                                    have=_both_true_have(), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    # `split_calls` returns a DICT, not a tuple. Unpacking it bound the four KEYS as strings, so
    # `len(updates)` was `len("updates")` == 7 and the message read like a real request count. An
    # assertion phrased `>= 1` would have passed for an entirely wrong reason.
    buckets = split_calls(calls)
    assert buckets["updates"] == [], (
        "check mode sent {0} configuration request(s)".format(len(buckets["updates"])))
    assert buckets["deploys"] == [], (
        "check mode sent {0} deploy request(s)".format(len(buckets["deploys"])))
    # The name of this case promises the reset is PLANNED, so it has to assert that too. Asserting
    # only "nothing was written" would pass for a run that also planned nothing -- which is the
    # difference between a working check mode and a check mode that quietly does no work.
    planned = [m[nvpair] for m in diff_nvpairs(result) if nvpair in m]
    assert planned == [RESET], (
        "check mode did not plan the reset for {0}: {1!r}".format(nvpair, planned))


@pytest.mark.parametrize("key,nvpair,companion,comp_nv", DIRECTIONS)
def test_rerun_over_the_reset_converges(key, nvpair, companion, comp_nv):
    """``have == reset_wire`` is nothing to withdraw, so the second run must not write.

    Idempotency here is the absence of a configuration request, not a ``changed`` flag.
    """
    have = build_have(ROUTED, key=key, value=False, **{companion: True})
    result, calls = routed_lldp_run(_profile_holding(companion), "replaced", have=have)
    assert not result.get("failed"), result.get("msg")
    buckets = split_calls(calls)
    assert buckets["updates"] == [], (
        "a rerun over the established reset sent {0} configuration request(s)"
        .format(len(buckets["updates"])))


# --------------------------------------------------------------- scope of the registration

# `ospf_area_id` LEAVES this list: its reset `0.0.0.0` was measured and registered
# on all four parents, so it is no longer a sister WITHOUT a reset,
# and demanding that it refuse would assert the opposite of the evidence.
#
# `enable_ospf` LEAVES it too: its reset `'false'` was measured and registered on int_routed_host, int_subif and int_vlan, with every dependent
# field at its neutral. int_loopback IS ALSO REGISTERED, in a non-default VRF:
#
#   * In the `default` VRF of a fabric that routes with OSPF the withdrawal is UNOBSERVABLE on
#     the device -- the parent emits the association by DISJUNCTION and the second branch does
#     not consult the gate, so the line survives while the controller stores `ospf=false`. That
#     boundary is real and stays documented here.
#   * With `intfVrf != "default"` the second branch is false and the withdrawal IS visible, which
#     is what was measured and what the row was registered on.
#
# `disable_bfd_echo` LEAVES it too: its reset `'false'` was measured and registered on
# int_routed_host and int_vlan. PIM/BFD were registered later, so the unsupported fixture now uses
# `eigrp_ipv4_passive`, a declared routed row with default false and no reset.
#
# The two that remain carry NO REGISTERED reset: `ospf_tag` and `eigrp_ipv4_passive`.
#
# Said precisely, because an earlier wording overreached. `ospf_tag` declares no defaultValue and
# carries minLength=1, so NOTHING WAS MEASURED for it -- which is not the same as "no withdrawal
# value exists": the engine's reviewed `""` exemption does admit the empty string on a plain
# string binding, and the withdrawal path transports a declared wire value without passing
# through public input validation. `eigrp_ipv4_passive` is a withheld EIGRP
# identity; this integration does not infer a reset from a different EIGRP row.
# Both are UNMEASURED, and they stay in this list because fail-closed is what an unregistered row
# must do, not because their behaviour has been ruled out.
#
# The list stays EXPLICIT on purpose: deriving it from the table would make it unable to detect
# a registration nobody declared.
SISTERS_WITHOUT_RESET = ["ospf_tag", "eigrp_ipv4_passive"]


@pytest.mark.parametrize("key", SISTERS_WITHOUT_RESET)
def test_a_sister_binding_on_the_same_parent_still_refuses(key):
    """Registering these two must not relax fail-closed for the rest of the parent.

    ``int_routed_host`` carries many registered fields with no measured reset. If this lot had
    widened the behaviour instead of registering two rows, these would have started returning a
    reset for a value nobody measured -- the failure mode this registry exists to prevent.
    """
    binding = resolve_binding(ROUTED, key)
    assert binding is not None, "{0}::{1} is not registered".format(ROUTED, key)
    assert binding.get("reset_wire") is None, (
        "{0}::{1} gained a reset this lot never measured".format(ROUTED, key))
    action, wire = gie_withdrawal_action(ROUTED, key, "true", ROUTED_LLDP_SUPPORTED, SUPPORTED_PATCH)
    assert action not in (GIE_WITHDRAW_RESET, GIE_WITHDRAW_NONE), (
        "{0}::{1} now answers {2!r} for a configured value with no registered reset"
        .format(ROUTED, key, action))
    assert wire is None


# Both vPC parents were measured on a paired fabric. These checks name the
# per-parent result; the routed measurement alone is not their evidence.
VPC_PARENTS = ["int_vpc_access_host", "int_vpc_trunk_host"]


@pytest.mark.parametrize("parent", VPC_PARENTS)
@pytest.mark.parametrize("key", [TX, RX])
def test_the_measured_vpc_parents_have_their_own_reset(parent, key):
    """Both vPC parents were measured; keep their exact independent registrations."""
    binding = resolve_binding(parent, key)
    assert binding is not None, "{0}::{1} is not registered".format(parent, key)
    assert binding.get("reset_wire") == "false"
    assert isinstance(binding["reset_wire"], str)


# --------------------------------------------------------------- fixtures other suites depend on

# Registering a reset has consequences the suite's own guards enforce, and it bit three times.
#
# `test_binding_withdrawal.py` and `test_binding_contracts.py` each pick a concrete
# (parent, key) as the fixture for a property. When a row's registration status changes under them,
# those cases stop testing what their names say -- and several keep PASSING, which is worse than
# failing because nobody looks.
#
# History of this exact fixture:
#   * it was ``int_access_host::disable_lldp_receive``; the access batch measured its reset, so the
#     C7 cases were rehomed to ``int_routed_host::disable_lldp_receive``;
#   * a later lot measured that one, so they were rehomed again, to ``int_routed_host::disable_bfd_echo``;
#   * `disable_bfd_echo` was then measured on routed and vlan, and PIM/BFD later, so this
#     integration uses routed `eigrp_ipv4_passive`;
#   * an over-replacement once put ``bfdEcho`` into two ACCESS cases where it is NOT
#     registered at all, making them pass while exercising nothing.
#
# So the guard is no longer about one row. It is a table of every fixture those suites rely on, with
# the property each one needs, checked by that property rather than by name. `reset` means the row
# must carry a measured reset; `no_reset` means it must not, and must declare a default so a
# configured value classifies as UNSUPPORTED rather than UNCLASSIFIED.
FIXTURE_CONTRACTS = [
    # (parent, key, requirement, which cases depend on it)
    pytest.param(ROUTED, "eigrp_ipv4_passive", "no_reset",
                 "the C7 unsupported row: test_c7_*, test_check_mode_also_refuses_*, "
                 "test_valid_first_interface_unsupported_second_*, "
                 "test_merged_is_never_blocked_by_an_unsupported_row, and the classifier's "
                 "differs_no_reset row",
                 id="routed-eigrp_ipv4_passive-no_reset"),
    pytest.param(ACCESS, "disable_lldp_receive", "reset",
                 "test_equivalent_have_encodings_classify_identically (needs a REGISTERED row so "
                 "the HAVE validator processes both encodings) and "
                 "test_deleted_state_does_not_enter_the_withdrawal_path (needs a row `replaced` "
                 "would actually withdraw, so `deleted` skipping it means something)",
                 id="access-lldp_receive-reset"),
]


@pytest.mark.parametrize("parent,key,requirement,dependents", FIXTURE_CONTRACTS)
def test_the_fixtures_other_suites_rely_on_still_have_the_property_they_need(
        parent, key, requirement, dependents):
    """Every fixture must be REGISTERED on its own parent, and hold the property it was picked for.

    The first half is what the review caught: an unregistered key resolves to no binding, the engine
    answers NONE, and the dependent cases pass having exercised nothing. Registration is checked per
    parent because support is per parent -- the same public key can be registered on one and absent
    on another, which is exactly how the mistake happened.

    When this fails, do NOT relax the dependent cases. Pick another row that has the required
    property, rehome them, and update this table. If none is left, that is the real news and belongs
    in a report rather than in a test edit.
    """
    binding = resolve_binding(parent, key)
    assert binding is not None, (
        "{0}::{1} is not registered on that parent, so a HAVE carrying it is ignored by the engine "
        "and these cases pass while exercising nothing: {2}".format(parent, key, dependents))
    reset = binding.get("reset_wire")
    if requirement == "reset":
        assert reset is not None, (
            "{0}::{1} lost its reset, so the cases that need a withdrawable row no longer have "
            "one: {2}".format(parent, key, dependents))
    elif requirement == "no_reset":
        assert reset is None, (
            "{0}::{1} gained a reset, so it is no longer an unsupported row and these cases are no "
            "longer testing a refusal: {2}".format(parent, key, dependents))
        assert binding.get("default_template") is not None, (
            "{0}::{1} declares no default_template, so a configured value classifies as "
            "UNCLASSIFIED rather than UNSUPPORTED and the message those cases assert would "
            "differ".format(parent, key))
    else:
        raise AssertionError("unknown requirement %r" % requirement)


# The earlier guard, `test_the_rehomed_c7_row_is_genuinely_unsupported`, covered ONLY the ROUTED
# row and is subsumed by FIXTURE_CONTRACTS above. It was REMOVED rather than left alongside: two
# sources of the same truth drift apart.


# ====================================================================================================
# Formerly test_gie_po_link_transmit_reset_skip.py
# Trunk port-channel `link_transmit_reset_skip` (nvPair linkTransmitResetSkip on int_port_channel_trunk_host).
#
# The option is the DEFAULT a member takes when it joins the port-channel: a member added while the parent is true
# stores true; a member that already exists keeps its stored value when the parent is raised or lowered. These tests
# therefore assert only what the module writes for the PARENT: no member child is ever written, and a parent value that
# differs from a member's is not treated as corrupt state. They make no claim about the device.
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


PCT = h.PC_TRUNK
KEY = "link_transmit_reset_skip"
NVP = "linkTransmitResetSkip"
MEMBER_TPL = "int_port_channel_trunk_member_11_1"


def _po(extra=None, **kw):
    return h.cfg_for(PCT, {**h.BASE_PC_TRUNK, **(extra or {})}, **kw)


def _po_link_have(value):
    """The parent as the controller returns it: built from the module's own payload, then the stored value set."""
    have = h.build_have(PCT, KEY, value) if value is not None else h.build_have(PCT)
    return have


def _stored(have):
    return have[0]["interfaces"][0]["nvPairs"].get(NVP)


def _writes(calls):
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    return found


def _only(calls):
    found = _writes(calls)
    assert len(found) == 1, [p["policy"] for p in found]
    pol = found[0]
    assert pol["policy"] == PCT and len(pol["interfaces"]) == 1, pol["policy"]
    assert pol["interfaces"][0]["ifName"].lower() == h.PC_A.lower()
    return pol["interfaces"][0]["nvPairs"]


def _paths(calls):
    return [c["method"] + " " + c["path"].split("/rest/")[-1].split("?")[0] for c in h.writes(calls)]


def _member_rows(parent_value, member_values):
    """A HAVE with the parent and mixed members, as the saved controller observations show (parent false, one member true)."""
    have = copy.deepcopy(_po_link_have(parent_value))
    for name, value in member_values.items():
        have.append({"policy": MEMBER_TPL, "interfaces": [{
            "interfaceType": "INTERFACE_ETHERNET", "serialNumber": h.SERIAL, "ifName": name, "fabricName": h.FABRIC,
            "nvPairs": {"INTF_NAME": name, NVP: "true" if value else "false", "ADMIN_STATE": "false"}}]})
    return have


# ------------------------------------------------------------------ the row
def test_the_row_matches_the_017_body_and_is_only_on_the_trunk_port_channel():
    b = resolve_binding(PCT, KEY)
    assert b is not None, "not registered on int_port_channel_trunk_host"
    assert b["parent_nvpair"] == NVP and b["mechanism"] == "passthrough" and b["type"] == "boolean"
    assert b["reset_wire"] == "false", "the template declares defaultValue=false"
    assert resolve_by_nvpair(PCT, NVP) is b
    assert "inert_when" not in b
    for other in (h.PC_ACCESS, h.PC_DOT1Q, h.VPC_TRUNK, h.TRUNK, h.ROUTED, h.LOOPBACK):
        assert resolve_binding(other, KEY) is None, other


# ------------------------------------------------------------------ merged
@pytest.mark.parametrize("value,wire", [(True, "true"), (False, "false")])
def test_merged_create_sends_the_explicit_parent_value(value, wire):
    result, calls = h.run_configs([_po({KEY: value})], "merged", [])
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)[NVP] == wire
    assert _paths(calls) == ["POST globalInterface", "POST globalInterface/deploy"]


@pytest.mark.parametrize("stored,new", [(False, True), (True, False)])
def test_merged_explicit_value_updates_the_parent_and_keeps_the_other_fields(stored, new):
    have = _po_link_have(stored)
    result, calls = h.run_configs([_po({KEY: new})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert nv[NVP] == ("true" if new else "false")
    assert nv["DESC"] == "pilot" and nv["MEMBER_INTERFACES"] == h.PC_MEMBER
    assert _paths(calls) == ["POST interface/modify", "POST globalInterface/deploy"]


def test_merged_omission_preserves_the_stored_parent_value_in_a_description_only_update():
    """The observed loss: a description-only merged call turned a stored true into false."""
    have = _po_link_have(True)
    assert _stored(have) == "true"
    result, calls = h.run_configs([_po({"description": "changed"})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert nv["DESC"] == "changed"
    assert nv[NVP] == "true", "the unregistered key was left out and the controller reset it to the template default"


def test_the_observed_loss_a_description_only_merged_call_keeps_a_stored_true():
    """The observed true-to-false loss, reproduced WITHOUT naming the new option.

    The HAVE is the module's own payload with the controller's stored value written in by hand, so this test is
    meaningful on a tree that does not know the option: there the outbound modify omits the key, the controller
    stores the template default, and the assertion below fails.
    """
    have = h.build_have(PCT)
    have[0]["interfaces"][0]["nvPairs"][NVP] = "true"
    result, calls = h.run_configs([_po({"description": "changed"})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert nv["DESC"] == "changed"
    assert nv.get(NVP) == "true", "the stored parent value is missing from the outbound modify (observed loss)"


def test_merged_omission_keeps_a_stored_false_too():
    have = _po_link_have(False)
    result, calls = h.run_configs([_po({"description": "changed"})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)[NVP] == "false"


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_repeating_the_stored_value_writes_nothing(state):
    have = _po_link_have(True)
    result, calls = h.run_configs([_po({KEY: True})], state, have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and result.get("changed") is False


# ------------------------------------------------------------------ replaced
def test_replaced_omission_resets_the_parent_to_the_template_default():
    have = _po_link_have(True)
    result, calls = h.run_configs([_po()], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)[NVP] == "false"


def test_replaced_with_the_default_stored_and_the_option_omitted_writes_nothing():
    have = _po_link_have(False)
    result, calls = h.run_configs([_po()], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_replaced_explicit_true_is_kept_and_the_other_fields_follow_the_request():
    have = _po_link_have(True)
    result, calls = h.run_configs([_po({KEY: True, "description": "new"})], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    nv = _only(calls)
    assert (nv[NVP], nv["DESC"]) == ("true", "new")


# ------------------------------------------------------------------ members are not written; disagreement is not corruption
@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_a_parent_that_differs_from_its_members_is_not_corrupt_state(state):
    """Saved observation: parent false, one member false, one member true. The same request again writes nothing."""
    have = _member_rows(False, {"Ethernet1/12": False, "Ethernet1/13": True})
    result, calls = h.run_configs([_po({KEY: False})], state, have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_changing_the_parent_never_writes_a_member_interface():
    have = _member_rows(False, {"Ethernet1/12": False, "Ethernet1/13": True})
    result, calls = h.run_configs([_po({KEY: True})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    written = {i["ifName"].lower() for p in _writes(calls) for i in p["interfaces"]}
    assert written == {h.PC_A.lower()}, written
    assert _only(calls)[NVP] == "true"


# ------------------------------------------------------------------ validation
@pytest.mark.parametrize("value", ["true", "yes", 1, "maybe"], ids=["str_true", "str_yes", "int_1", "str_maybe"])
def test_a_non_boolean_value_is_refused_before_any_write(value):
    result, calls = h.run_configs([_po({KEY: value})], "merged", [])
    assert result.get("failed") and KEY in result.get("msg", ""), result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("patch_version", [None, "4.3.1.0175006011"], ids=["no_patch_version", "smu011"])
def test_the_option_needs_an_approved_patch_version(patch_version):
    result, calls = h.run_configs([_po({KEY: True})], "merged", [], patch_version=patch_version)
    assert result.get("failed"), "the option was accepted without SMU 017 or ND >= 4.4.1"
    assert h.writes(calls) == []


def test_numeric_441_is_admitted():
    result, calls = h.run_configs([_po({KEY: True})], "merged", [], patch_version="4.4.1")
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)[NVP] == "true"


@pytest.mark.parametrize("parent", [h.PC_ACCESS, h.PC_DOT1Q], ids=["pc_access", "pc_dot1q"])
def test_other_port_channel_modes_do_not_accept_the_option(parent):
    profile = {**h.base_for(parent), KEY: True}
    result, calls = h.run_configs([h.cfg_for(parent, profile)], "merged", [])
    assert result.get("failed"), "the option was accepted on a port-channel mode whose body is not read"
    assert h.writes(calls) == []


def test_check_mode_reports_the_change_and_writes_nothing():
    result, calls = h.run_configs([_po()], "replaced", _po_link_have(True), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and result.get("changed") is True


# ------------------------------------------------------------------ API calls
@pytest.mark.parametrize("state,have_value", [("merged", None), ("replaced", True)])
def test_the_option_adds_a_field_and_no_request(state, have_value):
    """Same requests with and without the option; only the payload gains the nvPair."""
    have = _po_link_have(have_value) if have_value is not None else []
    with_key = h.run_configs([_po({KEY: False})], state, have)[1]
    without = h.run_configs([_po()], state, have)[1]
    assert [(c["method"], c["path"].split("?")[0]) for c in with_key] == [(c["method"], c["path"].split("?")[0]) for c in without]


# ------------------------------------------------------------------ deleted, overridden, query
def _identities(calls):
    """Every write in order, as (request, sorted [serial, ifName])."""
    out = []
    for c in h.writes(calls):
        kind = c["method"] + " " + c["path"].split("/rest/")[-1].split("?")[0]
        found = []
        h._collect_policies([c["payload"]], found)
        if found:
            ids = sorted([i["serialNumber"], i["ifName"]] for p in found for i in p["interfaces"])
        else:
            ids = sorted([e.get("serialNumber"), e.get("ifName")] for e in (c["payload"] or []) if isinstance(e, dict))
        out.append((kind, ids))
    return out


_ORIG = h._transport


def _po_detail(calls, have):
    """interface/detail for port-channels, the shape the user-loopback and PVLAN port-channel reads document.

    For an ordinary trunk port-channel this is a synthesized shape, used only so that the overridden sweep sees a
    deletable aggregate."""
    inner = _ORIG(calls, have)

    def send(mod, method, path, payload=None):
        resp = inner(mod, method, path, payload)
        if method == "GET" and "/interface/detail" in path and isinstance(resp.get("DATA"), list):
            for e in resp["DATA"]:
                if str(e.get("ifName", "")).lower().startswith("port-channel"):
                    e.update(ifType="INTERFACE_PORT_CHANNEL", isPhysical="false", deletable=True, editAllowed=True)
        return resp
    return send


def _second_po(value, name="Port-channel302"):
    other = copy.deepcopy(h.build_have(PCT, KEY, value))
    other[0]["interfaces"][0]["ifName"] = name
    other[0]["interfaces"][0]["nvPairs"]["PO_ID"] = name
    return other


def test_deleted_uses_the_aggregate_removal_and_writes_no_reset_skip_flow():
    have = _po_link_have(True)
    result, calls = h.run_configs([_po()], "deleted", have)
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [("DELETE interface/markdelete", [[h.SERIAL, h.PC_A]]),
                                  ("POST globalInterface/deploy", [[h.SERIAL, h.PC_A]])]


def test_overridden_retained_port_channel_follows_replaced():
    have = _po_link_have(True)
    with patch.object(h, "_transport", _po_detail):
        result, calls = h.run_configs([_po()], "overridden", have)
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)[NVP] == "false"
    with patch.object(h, "_transport", _po_detail):
        result, calls = h.run_configs([_po({KEY: True})], "overridden", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("omitted_value", [True, False])
def test_overridden_removes_an_omitted_port_channel_whatever_its_stored_value(omitted_value):
    """The omitted aggregate goes through the existing removal; its reset-skip value does not change that path."""
    have = _po_link_have(True) + _second_po(omitted_value)
    with patch.object(h, "_transport", _po_detail):
        result, calls = h.run_configs([_po({KEY: True})], "overridden", have)
    assert not result.get("failed"), result.get("msg")
    assert _identities(calls) == [("DELETE interface/markdelete", [[h.SERIAL, "Port-channel302"]]),
                                  ("POST globalInterface/deploy", [[h.SERIAL, "Port-channel302"]])]


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
                    if i["ifName"].lower() == q["ifName"].lower() and i["serialNumber"] == q.get("serialNumber")]}
            writes.append((method, path))
            return {"RETURN_CODE": 500, "MESSAGE": "unexpected read", "DATA": {}}
        return send
    return factory


def test_query_returns_the_parent_value_and_claims_nothing_about_the_members():
    stored = _po_link_have(False)
    writes = []
    with patch.object(h, "_transport", _query_transport(stored, writes)):
        result, calls = h.run_configs([{"name": h.PC_A, "switch": [h.SWITCH_IP]}], "query", [])
    assert not result.get("failed"), result.get("msg")
    assert writes == [] and h.writes(calls) == [] and not result.get("changed")
    assert result["response"] == stored, "query must return the controller entry unchanged"
    assert result["response"][0]["interfaces"][0]["nvPairs"][NVP] == "false"
