"""D-3: a border (non-leaf) reset of a routed Ethernet to its own parent, int_routed_host, with OSPF still on.

The reset already sends ospf "false" (its verified reset). The rows gated on OSPF or on authentication were judged
against the gate in HAVE (on) and refused. They are now judged against the gate as this reset leaves it: HAVE, then the
role default payload, then the verified resets of the same reset. Under that final gate the tag and the key type are
inert and stay stored (never sent); the MD5 key declares `clear` and is cleared; the simple key and the options have
their own resets. Unreadable values, EIGRP passive, the leaf policy change and the OSPF-off path are unchanged, and no
stored secret appears in a request or a result. Real main() through gie_withdrawal_harness; values are synthetic.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json

import pytest

from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import gie_withdrawal_harness as h
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.test_dcnm_intf_default_reset_registered_f2 import (
    STATES,
    nvpairs_of_reset,
    reset_policies,
    reset_wire,
    run,
)

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
def test_second_run_over_the_reset_is_a_noop(state, keep_tag):
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
def test_capability_disabled_keeps_the_published_behaviour(state):
    result, calls = run(state, routed_have(GROUPS["md5"]), "border", patch_version=None)
    assert not result.get("failed"), result.get("msg")
    assert no_secret(calls, result)
