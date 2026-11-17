"""Automatic withdrawal of the nine routed port-channel fields whose explicit withdrawal was measured on that parent.

Measured live on int_l3_port_channel (parent body 81c9392e), each as an explicit value: CDP_ENABLE "true",
lldpTransmit "false" and lldpReceive "false"; bfdEcho "false" and ipv4AclIn ""; ipv4Redirects "false" and
ipv6Redirects "false" with the combined option false; ipv6LinkLocal "" and ipv6NdSuppressRa "false". Each row now
declares that value as its reset_wire, so replaced and a retained interface of overridden send it when the field is
omitted over a stored non-default value. That automatic reset is new and not tested live.

Every case drives the real main() through helpers/binding_harness with a full stored state: the nine fields set, and
the fields that still have no reset (ARP timeout, the IPv6 address pair) given again explicitly, so their refusal
cannot stand in for the result of the route under test. The split redirect resets are sent only while
DISABLE_IP_REDIRECTS is stored "false" and ends "false", the state they were measured in. Values are synthetic.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import BINDING_TABLE
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_by_nvpair
from unittest.mock import patch

from .helpers import binding_harness as h
from .test_binding_smu017 import DEPLOY, L3PO, MEM_A, MODIFY, PO_A
from .test_binding_smu017 import _identities, _l3po_pim_bfd_as_have, _l3po_pim_bfd_have, _measured_detail
from .test_binding_smu017 import _member_have, _only, _po

# (public key, nvPair, stored non-default public value, its wire, reset wire)
ROUTES = [
    ("enable_cdp", "CDP_ENABLE", False, "false", "true"),
    ("disable_lldp_transmit", "lldpTransmit", True, "true", "false"),
    ("disable_lldp_receive", "lldpReceive", True, "true", "false"),
    ("disable_bfd_echo", "bfdEcho", True, "true", "false"),
    ("ipv4_acl_in", "ipv4AclIn", "PILOT-ACL", "PILOT-ACL", ""),
    ("ipv6_link_local", "ipv6LinkLocal", "fe80::33:1", "fe80::33:1", ""),
    ("ipv6_nd_suppress_ra", "ipv6NdSuppressRa", True, "true", "false"),
    ("disable_ipv4_redirects", "ipv4Redirects", True, "true", "false"),
    ("disable_ipv6_redirects", "ipv6Redirects", True, "true", "false"),
]
IDS = [r[0] for r in ROUTES]
BOOLS = [r for r in ROUTES if isinstance(r[2], bool)]
BOOL_IDS = [r[0] for r in BOOLS]
SPLIT = [r for r in ROUTES if r[1] in ("ipv4Redirects", "ipv6Redirects")]
SPLIT_IDS = [r[0] for r in SPLIT]

# Fields without a reset on this parent, given again on every request, and the combined redirect option at its default.
RETAINED = {"arp_timeout": 60, "ipv6_addr": "2001:db8:33::5", "ipv6_mask_len": 126, "disable_ip_redirects": False}
STORED = dict(h.BASE_PC_L3, members=[MEM_A], **RETAINED)
STORED.update({key: value for key, _nv, value, _w, _r in ROUTES})
NINE = [r[1] for r in ROUTES]


def _want(key, omit=(), **change):
    """The stored profile with `key` and `omit` omitted and `change` applied."""
    w = dict(STORED, **change)
    for k in (key,) + tuple(omit):
        w.pop(k, None)
    return w


def _have(**nv):
    have = _l3po_pim_bfd_have(STORED) + _member_have(MEM_A, PO_A)
    have[0]["interfaces"][0]["nvPairs"].update(nv)
    return have


def _nv(have):
    return have[0]["interfaces"][0]["nvPairs"]


def _run(state, configs, have, check_mode=False):
    """Replaced, or overridden scoped to port-channels as in the live batch (override_intf_types [pc])."""
    with patch.object(h, "_transport", _measured_detail):
        if state != "overridden":
            return h.run_configs(configs, state, have, check_mode=check_mode)
        original = h.set_module_args
        with patch.object(h, "set_module_args", side_effect=lambda a: original(dict(a, override_intf_types=["pc"]))):
            return h.run_configs(configs, state, have, check_mode=check_mode)


def _reported(result):
    out = {}
    for d in h.diff_nvpairs(result):
        out.update(d)
    return out


def _refused(result, calls, *needles):
    msg = str(result.get("msg", ""))
    assert result.get("failed") is True, "the request was accepted"
    for needle in needles:
        assert needle in msg, msg
    assert "No configuration or deployment request was sent" in msg
    assert h.writes(calls) == []
    return msg


# ------------------------------------------------------------------ registry
def test_the_nine_rows_declare_the_measured_reset_and_nothing_else_changed_on_this_parent():
    for key, nvpair, _value, _wire, reset in ROUTES:
        b = resolve_by_nvpair(L3PO, nvpair)
        assert b["profile_key"] == key and b["reset_wire"] == reset, nvpair
        assert isinstance(b["reset_wire"], str)
    for nvpair in ("arpTimeout", "IPv6", "IPv6_PREFIX", "DISABLE_IP_REDIRECTS", "dhcpServers"):
        assert "reset_wire" not in resolve_by_nvpair(L3PO, nvpair), nvpair


# Every row of the nine nvPairs on another parent, with its reset (None: no reset) exactly as on the parent commit
# c5237776. A reset measured on the routed port-channel does not move to another parent.
OTHER_PARENTS = {
    ("int_access_host", "lldpReceive"): "false",
    ("int_access_host", "lldpTransmit"): "false",
    ("int_dot1q_tunnel_host", "lldpReceive"): None,
    ("int_dot1q_tunnel_host", "lldpTransmit"): None,
    ("int_port_channel_access_host", "lldpReceive"): "false",
    ("int_port_channel_access_host", "lldpTransmit"): "false",
    ("int_port_channel_dot1q_tunnel_host", "CDP_ENABLE"): None,
    ("int_port_channel_dot1q_tunnel_host", "lldpReceive"): "false",
    ("int_port_channel_dot1q_tunnel_host", "lldpTransmit"): "false",
    ("int_port_channel_pvlan_host", "lldpReceive"): "false",
    ("int_port_channel_pvlan_host", "lldpTransmit"): "false",
    ("int_port_channel_trunk_host", "lldpReceive"): "false",
    ("int_port_channel_trunk_host", "lldpTransmit"): "false",
    ("int_pvlan_host", "lldpReceive"): "false",
    ("int_pvlan_host", "lldpTransmit"): "false",
    ("int_routed_host", "CDP_ENABLE"): "true",
    ("int_routed_host", "bfdEcho"): "false",
    ("int_routed_host", "ipv4AclIn"): "",
    ("int_routed_host", "ipv4Redirects"): "false",
    ("int_routed_host", "ipv6LinkLocal"): "",
    ("int_routed_host", "ipv6NdSuppressRa"): "false",
    ("int_routed_host", "ipv6Redirects"): "false",
    ("int_routed_host", "lldpReceive"): "false",
    ("int_routed_host", "lldpTransmit"): "false",
    ("int_subif", "ipv4Redirects"): "false",
    ("int_subif", "ipv6LinkLocal"): "",
    ("int_subif", "ipv6NdSuppressRa"): "false",
    ("int_subif", "ipv6Redirects"): "false",
    ("int_trunk_host", "lldpReceive"): "false",
    ("int_trunk_host", "lldpTransmit"): "false",
    ("int_vlan", "bfdEcho"): "false",
    ("int_vlan", "ipv4AclIn"): "",
    ("int_vlan", "ipv4Redirects"): "false",
    ("int_vlan", "ipv6LinkLocal"): "",
    ("int_vlan", "ipv6NdSuppressRa"): "false",
    ("int_vlan", "ipv6Redirects"): "false",
    ("int_vpc_access_host", "lldpReceive"): "false",
    ("int_vpc_access_host", "lldpTransmit"): "false",
    ("int_vpc_dot1q_tunnel", "lldpReceive"): "false",
    ("int_vpc_dot1q_tunnel", "lldpTransmit"): "false",
    ("int_vpc_pvlan_host", "lldpReceive"): "false",
    ("int_vpc_pvlan_host", "lldpTransmit"): "false",
    ("int_vpc_trunk_host", "lldpReceive"): "false",
    ("int_vpc_trunk_host", "lldpTransmit"): "false",
}


def test_other_parents_keep_their_own_reset_state():
    actual = {(b["parent_template"], b["parent_nvpair"]): b.get("reset_wire")
              for b in BINDING_TABLE if b["parent_nvpair"] in NINE and b["parent_template"] != L3PO}
    assert actual == OTHER_PARENTS


@pytest.mark.parametrize("parent,key,value", [
    (h.PC_DOT1Q, "enable_cdp", False),
    (h.ETH_DOT1Q, "disable_lldp_transmit", True),
    (h.ETH_DOT1Q, "disable_lldp_receive", True),
], ids=["dot1q_port_channel_cdp", "dot1q_ethernet_lldp_transmit", "dot1q_ethernet_lldp_receive"])
def test_a_parent_without_a_measured_reset_still_refuses_the_omission(parent, key, value):
    have = h.build_have(parent, key, value)
    pkw = {"parent": parent} if parent in h.NON_ETH_PARENTS else {}
    result, calls = h.run(h.want_omitting(parent, key), "replaced", have, **pkw)
    _refused(result, calls, "%s on %s" % (key, parent))


# ------------------------------------------------------------------ replaced and scoped overridden omission
@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("key,nvpair,value,wire,reset", ROUTES, ids=IDS)
def test_omission_sends_exactly_the_reset_and_keeps_every_other_nvpair(key, nvpair, value, wire, reset, state):
    have = _have()
    assert _nv(have)[nvpair] == wire and _nv(have)["DISABLE_IP_REDIRECTS"] == "false"
    result, calls = _run(state, [_po(_want(key))], have)
    assert not result.get("failed"), result.get("msg")
    assert result.get("changed") is True
    sent = _only(calls)
    assert sent[nvpair] == reset
    stored = _nv(have)
    for k, v in sent.items():
        if k != nvpair:
            assert stored.get(k) == v, (k, stored.get(k), v)
    assert set(stored) - set(sent) == set(), sorted(set(stored) - set(sent))
    assert _reported(result) == {nvpair: reset}
    assert [i[0] for i in _identities(calls)] == [MODIFY, DEPLOY]


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("key,nvpair,value,wire,reset", ROUTES, ids=IDS)
def test_check_mode_predicts_the_same_reset_and_writes_nothing(key, nvpair, value, wire, reset, state):
    result, calls = _run(state, [_po(_want(key))], _have(), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert result.get("changed") is True and h.writes(calls) == []
    assert _reported(result) == {nvpair: reset}


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("key,nvpair,value,wire,reset", ROUTES, ids=IDS)
def test_the_readback_of_the_reset_converges_and_a_reapply_sets_the_value_again(key, nvpair, value, wire, reset, state):
    result, calls = _run(state, [_po(_want(key))], _have())
    assert not result.get("failed"), result.get("msg")
    readback = _l3po_pim_bfd_as_have(_only(calls)) + _member_have(MEM_A, PO_A)
    result, calls = _run(state, [_po(_want(key))], readback)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and result.get("changed") is False, "the repeat after the readback wrote"
    result, calls = _run(state, [_po(STORED)], readback)
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)[nvpair] == wire and _reported(result) == {nvpair: wire}


@pytest.mark.parametrize("key,nvpair,value,wire,reset", ROUTES, ids=IDS)
def test_omission_of_all_nine_resets_them_together(key, nvpair, value, wire, reset):
    want = {k: v for k, v in STORED.items() if k not in IDS}
    for state in ("replaced", "overridden"):
        result, calls = _run(state, [_po(want)], _have())
        assert not result.get("failed"), (state, result.get("msg"))
        assert _only(calls)[nvpair] == reset, state
        assert _reported(result) == {n: r for _k, n, _v, _w, r in ROUTES}, state


# ------------------------------------------------------------------ unchanged contracts
@pytest.mark.parametrize("key,nvpair,value,wire,reset", ROUTES, ids=IDS)
def test_merged_omission_keeps_the_stored_value(key, nvpair, value, wire, reset):
    result, calls = _run("merged", [_po(_want(key, description="changed"))], _have())
    assert not result.get("failed"), result.get("msg")
    sent = _only(calls)
    assert sent.get(nvpair, wire) == wire, sent.get(nvpair)
    assert nvpair not in _reported(result)


@pytest.mark.parametrize("key,nvpair,value,wire,reset", ROUTES, ids=IDS)
def test_merged_explicit_withdrawal_sends_the_measured_value(key, nvpair, value, wire, reset):
    neutral = {"true": True, "false": False}.get(reset, reset)
    result, calls = _run("merged", [_po(dict(STORED, **{key: neutral}))], _have())
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)[nvpair] == reset and _reported(result) == {nvpair: reset}


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("key,nvpair,value,wire,reset", ROUTES, ids=IDS)
def test_omission_over_a_stored_reset_value_writes_nothing(key, nvpair, value, wire, reset, state):
    result, calls = _run(state, [_po(_want(key))], _have(**{nvpair: reset}))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and result.get("changed") is False


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("key,nvpair,value,wire,reset", ROUTES, ids=IDS)
def test_a_missing_readback_is_not_withdrawn(key, nvpair, value, wire, reset, state):
    have = _have()
    del _nv(have)[nvpair]
    result, calls = _run(state, [_po(_want(key))], have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and result.get("changed") is False


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("key,nvpair,value,wire,reset", BOOLS, ids=BOOL_IDS)
def test_a_wrong_boolean_readback_fails_closed(key, nvpair, value, wire, reset, state):
    result, calls = _run(state, [_po(_want(key))], _have(**{nvpair: "maybe"}))
    assert result.get("failed") is True and h.writes(calls) == []


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("key,nvpair,value,wire,reset", BOOLS, ids=BOOL_IDS)
def test_a_native_boolean_readback_is_classified_as_its_wire_string(key, nvpair, value, wire, reset, state):
    native = {"true": True, "false": False}
    result, calls = _run(state, [_po(_want(key))], _have(**{nvpair: native[wire]}))
    assert not result.get("failed"), result.get("msg")
    assert _only(calls)[nvpair] == reset
    result, calls = _run(state, [_po(_want(key))], _have(**{nvpair: native[reset]}))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_an_omitted_field_without_a_reset_still_refuses_the_whole_request(state):
    """ARP timeout keeps its refusal; the nine resets are not sent with it."""
    want = {k: v for k, v in STORED.items() if k != "arp_timeout" and k not in IDS}
    result, calls = _run(state, [_po(want)], _have())
    msg = _refused(result, calls, "arp_timeout on %s" % L3PO)
    assert not any(k in msg for k in IDS), msg


@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_an_omitted_address_pair_still_refuses_the_whole_request(state):
    want = {k: v for k, v in STORED.items() if k not in ("ipv6_addr", "ipv6_mask_len")}
    result, calls = _run(state, [_po(want)], _have())
    _refused(result, calls, "ipv6_addr on %s" % L3PO, "ipv6_mask_len on %s" % L3PO)


# ------------------------------------------------------------------ the combined redirect option
@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("key,nvpair,value,wire,reset", SPLIT, ids=SPLIT_IDS)
def test_split_reset_with_the_combined_option_stored_false_and_omitted(key, nvpair, value, wire, reset, state):
    result, calls = _run(state, [_po(_want(key, omit=("disable_ip_redirects",)))], _have())
    assert not result.get("failed"), result.get("msg")
    sent = _only(calls)
    assert (sent[nvpair], sent["DISABLE_IP_REDIRECTS"]) == (reset, "false")


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("key,nvpair,value,wire,reset", SPLIT, ids=SPLIT_IDS)
def test_split_option_kept_while_the_combined_option_ends_true(key, nvpair, value, wire, reset, state):
    """The template blanks the split options then: nothing is withdrawn and no false is written over them."""
    for have in (_have(), _have(DISABLE_IP_REDIRECTS="true")):
        result, calls = _run(state, [_po(_want(key, disable_ip_redirects=True))], have)
        assert not result.get("failed"), result.get("msg")
        assert _reported(result).get(nvpair) is None
        for c in h.writes(calls):
            found = []
            h._collect_policies([c["payload"]], found)
            for p in found:
                for i in p["interfaces"]:
                    assert (i.get("nvPairs") or {}).get(nvpair, wire) == wire


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("key,nvpair,value,wire,reset", SPLIT, ids=SPLIT_IDS)
def test_split_reset_refused_when_the_stored_combined_option_true_is_turned_off(key, nvpair, value, wire, reset, state):
    """Counterexample kept as a refusal: the combined option was turned off live only with the split values given
    explicitly, which does not establish the reset of a stored split value in the same request."""
    result, calls = _run(state, [_po(_want(key, disable_ip_redirects=False))], _have(DISABLE_IP_REDIRECTS="true"))
    _refused(result, calls, "%s (combined option disable_ip_redirects) on %s" % (key, L3PO))


@pytest.mark.parametrize("state", ["replaced", "overridden"])
@pytest.mark.parametrize("key,nvpair,value,wire,reset", SPLIT, ids=SPLIT_IDS)
def test_split_reset_refused_without_a_readable_combined_option(key, nvpair, value, wire, reset, state):
    for stored in ("", None):
        have = _have()
        if stored is None:
            del _nv(have)["DISABLE_IP_REDIRECTS"]
        else:
            _nv(have)["DISABLE_IP_REDIRECTS"] = stored
        result, calls = _run(state, [_po(_want(key, omit=("disable_ip_redirects",)))], have)
        _refused(result, calls, "%s (combined option disable_ip_redirects) on %s" % (key, L3PO))


@pytest.mark.parametrize("key,nvpair,value,wire,reset", SPLIT, ids=SPLIT_IDS)
def test_the_explicit_split_withdrawal_under_a_combined_option_turned_off_is_sent(key, nvpair, value, wire, reset):
    """The measured shape: the combined option and the split values all explicit."""
    result, calls = _run("replaced", [_po(dict(STORED, **{key: False, "disable_ip_redirects": False}))],
                         _have(DISABLE_IP_REDIRECTS="true"))
    assert not result.get("failed"), result.get("msg")
    sent = _only(calls)
    assert (sent[nvpair], sent["DISABLE_IP_REDIRECTS"]) == ("false", "false")


def test_an_independent_combined_option_omission_is_still_refused():
    want = {k: v for k, v in STORED.items() if k != "disable_ip_redirects"}
    result, calls = _run("replaced", [_po(want)], _have(DISABLE_IP_REDIRECTS="true"))
    msg = _refused(result, calls, "disable_ip_redirects on %s" % L3PO)
    assert "disable_ipv4_redirects" not in msg and "disable_ipv6_redirects" not in msg


# ------------------------------------------------------------------ the member copies the parent
@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_the_discovery_reset_is_sent_on_the_parent_only(state):
    """The parent forwards CDP and LLDP to the member policy; the module writes no member policy for it."""
    result, calls = _run(state, [_po(_want("enable_cdp"))], _have())
    assert not result.get("failed"), result.get("msg")
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    assert [p["policy"] for p in found] == [L3PO]


def test_the_stored_state_carries_every_routing_value_in_its_wire_form():
    nv = _nv(_have())
    assert {n: nv[n] for n in NINE} == {n: w for _k, n, _v, w, _r in ROUTES}
    assert (nv["arpTimeout"], nv["IPv6"], nv["IPv6_PREFIX"], nv["DISABLE_IP_REDIRECTS"]) == (
        "60", "2001:db8:33::5", "126", "false")
