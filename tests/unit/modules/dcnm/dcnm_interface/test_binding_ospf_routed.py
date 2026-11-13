"""OSPF on int_routed_host: HAVE representation, field lots, enum omission and dependent fields."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import BINDING_TABLE
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GieBindingError
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_carry_forward_bindings
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_validate_binding_value
from unittest import mock
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_guarded_keys
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_ENABLED_PATCH_VERSIONS
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_WITHDRAW_NONE
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_WITHDRAW_RESET
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_WITHDRAW_UNSUPPORTED
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_withdrawal_action
from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table as table
from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine as engine

from .helpers.binding_harness import FAB
from .helpers.binding_harness import SNO
from .helpers.binding_harness import _instance
from .helpers.binding_harness import _payload_nv
from .helpers.binding_harness import _public_nv
from .helpers.binding_harness import IF_A
from .helpers.binding_harness import OSPF_CTX
from .helpers.binding_harness import ROUTED as ROUTED_ENUM_ROUTED
from .helpers.binding_harness import SUPPORTED
from .helpers.binding_harness import SUPPORTED_PATCH
from .helpers.binding_harness import base_for
from .helpers.binding_harness import build_have
from .helpers.binding_harness import cfg
from .helpers.binding_harness import diff_nvpairs
from .helpers.binding_harness import public_clear_for
from .helpers.binding_harness import request_nvpairs
from .helpers.binding_harness import run
from .helpers.binding_harness import run_configs
from .helpers.binding_harness import split_calls
from .helpers.binding_harness import wire_for
from .helpers import binding_harness as h
from .helpers import role_reset as F2
from .helpers import registry_generator as thin
from .helpers.fixture_cases import load_case


# ====================================================================================================
# Formerly test_gie_routed_ospf_have_representation.py
# How NDFC represents the OSPF nvPairs on read-back, and what the carry-forward does with it.
#
# WHY THIS FILE EXISTS
#     ``OSPF_COST`` is the first ``integer`` binding ever placed on the GENERIC carry-forward
#     path. The table has exactly two integer bindings:
#
#         int_fabric_loopback_11_1 :: OSPF_AUTH_KEY_ID   -> that parent has NO passthrough
#                                                           binding, so it never reaches
#                                                           ``gie_carry_forward_bindings``
#         int_routed_host          :: OSPF_COST          -> reaches it from this slice on
#
#     So this is not a pre-existing defect surfacing. The limitation in
#     ``gie_validate_binding_value`` predates the slice, but nothing had ever exposed it: the
#     registry had no integer on a generic-path parent until now.
#
# WHAT WAS MEASURED (read-only, no mutation)
#     ``GET /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface?serialNumber=<sno>`` — the
#     endpoint that feeds HAVE — against on NDFC 12.6.0.267. 63 ``int_routed_host``
#     interfaces came back in TWO shapes:
#
#       * 62 interfaces, 17-18 nvPairs: every OSPF key ABSENT.
#       * Ethernet1/5, 83 nvPairs: every OSPF key present, every value a ``str``.
#
#     Exact observed values on Ethernet1/5, reproduced in ``ROUTED_HAVE_FULL`` below:
#
#         ENABLE_OSPF   'false'      OSPF_TAG   ''      OSPF_AREA_ID  '0.0.0.0'
#         OSPF_COST     ''           IPV4_ACL_IN ''     DISABLE_LLDP_TRANSMIT 'false'
#
#     NDFC returns every nvPair as a string. No native integer, no ``null``. The fixtures here
#     are a sanitized minimum derived from those responses -- presence and types preserved
#     exactly, the other 77 nvPairs of the full record dropped.
#
#     NOT MEASURED, deliberately: what NDFC does when it RECEIVES ``""`` in OSPF_COST. That is
#     the withdrawal contract and it is characterized, not asserted -- see the last section.
#
# THE SEPARATION THESE TESTS PIN
#     Three contracts that must not collapse into one:
#
#         input        a valid integer the operator writes
#         HAVE         the controller's representation: string, empty, or absent
#         withdrawal   the operation that removes a configured cost
#
#     Accepting ``""`` FROM the controller does not authorize ``""`` AS input, and neither
#     authorizes deleting anything. ``test_an_empty_string_is_still_rejected_as_operator_input``
#     is the guard on that.
#
# NO MODULE WIRING WAS NEEDED FOR THIS SLICE
#     An earlier draft of this file claimed the four keys were unwired. That was wrong, and the
#     mistake is worth recording because it is easy to repeat: grepping ``dcnm_interface.py`` for
#     a literal ``"ospfCost"`` finds nothing, which looks like a missing entry. The wiring is
#     generated, not written:
#
#         dcnm_interface.py:2330   self.keymap.update(gie_nvpair_keymap())
#         dcnm_interface.py:3863   gie_extend_prof_spec(eth_prof_spec_routed_host, ...)
#
#     Both derive from the binding table, so a new row lands in the keymap and the routed arg
#     spec by itself. ``gie_nvpair_keymap()`` returns all four. The five suite tests that failed
#     after regeneration were stale inventory expectations (14 keys where there are now 18), not
#     evidence of missing integration -- they are updated alongside this file.
#
#     ``ROUTED_KEYMAP`` below is therefore a faithful local copy, not a stand-in for something
#     absent. The defect asserted here does not depend on it either way: with every OSPF key
#     removed from the keymap the abort still happens, because the carry-forward reads the
#     binding table and HAVE, never the keymap.
#
# Offline: no controller and no device.
# ====================================================================================================
ROUTED = "int_routed_host"
IFNAME = "Ethernet1/5"


class _Abort(Exception):
    """Stands in for what ``fail_json`` does in production.

    The shared harness sets ``s.module`` to a bare ``Mock``, so ``fail_json`` records the call
    and RETURNS -- the comparator then runs on past the failure. Real Ansible raises
    ``SystemExit`` there. Tests that care whether the module aborts install this as a side
    effect, so the control flow under test matches production instead of the harness.

    Carries the message so a test can assert WHICH abort it caught. An abort assertion that
    accepts any failure would go green on an unrelated regression.
    """


def _fail(**kwargs):
    raise _Abort(kwargs.get("msg", ""))


def _routed_instance():
    s = _instance()
    s.keymap = dict(ROUTED_KEYMAP)
    s.module.fail_json.side_effect = _fail
    return s


def _assert_is_the_cost_have_abort(exc):
    """Pin the cause, not just the fact of an abort."""
    msg = str(exc)
    assert "ospf_cost" in msg, "aborted for a different key: {0}".format(msg)
    assert "authoritative controller value" in msg, (
        "aborted on explicit input, not on the HAVE representation: {0}".format(msg)
    )


# Baseline the builder emits for a routed interface, from the observed 17-nvPair shape.
ROUTED_BUILDER_NV = {
    "INTF_NAME": IFNAME,
    "DESC": "",
    "CONF": "",
    "ADMIN_STATE": "true",
    "SPEED": "Auto",
    "MTU": "9216",
    "INTF_VRF": "",
    "IP": "",
    "PREFIX": "",
}

# Ethernet1/5, as the controller returned it. Every value a str -- that is the whole point.
ROUTED_HAVE_FULL = {
    "ospf": "false",
    "ospfTag": "",
    "OSPF_AREA_ID": "0.0.0.0",
    "ospfCost": "",
    "ipv4AclIn": "",
    "lldpTransmit": "false",
}

ROUTED_KEYMAP = {
    "INTF_NAME": "name", "DESC": "description", "CONF": "cmds",
    "ADMIN_STATE": "admin_state", "SPEED": "speed", "MTU": "mtu",
    "INTF_VRF": "vrf", "IP": "ipv4_addr", "PREFIX": "ipv4_mask_len",
    "ospf": "enable_ospf", "ospfTag": "ospf_tag",
    "OSPF_AREA_ID": "ospf_area_id", "ospfCost": "ospf_cost",
    "ipv4AclIn": "ipv4_acl_in", "lldpTransmit": "disable_lldp_transmit",
}


def _routed_want(nv):
    return {
        "policy": ROUTED,
        "interfaceType": "INTERFACE_ETHERNET",
        "deploy": False,
        "interfaces": [{
            "ifName": IFNAME, "serialNumber": SNO, "fabricName": FAB,
            "interfaceType": "INTERFACE_ETHERNET", "nvPairs": dict(nv),
        }],
    }


def _routed_have(nv):
    return [{
        "policy": ROUTED,
        "interfaces": [{
            "ifName": IFNAME, "serialNumber": SNO,
            "interfaceType": "INTERFACE_ETHERNET", "nvPairs": dict(nv),
        }],
    }]


def _routed_pb(**public_keys):
    item = {"ifname": IFNAME, "sno": SNO, "fabric": FAB}
    item.update(public_keys)
    return item


def _run(s, state="merged"):
    s.dcnm_intf_compare_want_and_have(state)


# =====================================================================================
# SCOPE — why only this binding is affected
# =====================================================================================
def test_every_integer_on_a_generic_carry_forward_parent_is_accounted_for():
    """Pin the blast radius of the HAVE-representation exemption.

    When this file was written OSPF_COST was the only integer binding that could reach the
    generic carry-forward. Lot 2 added four more on the same parent, and registering int_subif
    and int_vlan added ten more across two new parents -- so the entry is now keyed by parent
    as well, because the same nvPair name on a different parent is a different binding.

    What has NOT changed is why it matters: every name below is validated against the string
    NDFC returns, not against a native int. A new integer arriving here silently would inherit
    that exemption without anyone deciding it should.

    OSPF_AUTH_KEY_ID is the newest and the decision was made deliberately: it takes the same
    exemption, for the same reason. It is an ordinary integer that the controller hands back as
    "1", and the fact that it sits beside key material changes nothing about its own
    representation -- an id is not a secret and is not marked no_log, precisely so that Ansible
    does not go scrubbing the digit "1" out of unrelated output.
    """
    exposed = sorted(
        (b["parent_template"], b["parent_nvpair"]) for b in BINDING_TABLE
        if b["type"] == "integer"
        and any(cf["parent_nvpair"] == b["parent_nvpair"]
                for cf in gie_carry_forward_bindings(b["parent_template"]))
    )
    # Compared order-independently: the expected rows below stay in their documented
    # order, but camelCase and UPPER_SNAKE sort differently in ASCII, so the SMU rename
    # reshuffles `exposed` without changing its membership. Membership is still exact --
    # an unreviewed integer binding reaching carry-forward still fails here.
    assert exposed == sorted([
        ("int_loopback", "OSPF_AUTH_KEY_ID"),
        ("int_loopback", "ospfCost"),
        ("int_loopback", "ospfDeadInterval"),
        ("int_loopback", "ospfHelloInterval"),
        ("int_loopback", "ospfPriority"),
        ("int_loopback", "ospfRetransmitInterval"),
        ("int_loopback", "ospfTransmitDelay"),
        # The five dampening integers (slice 0b_6) need the same exemption: NDFC returns
        # them as strings. C9300v lacks their CLI, so device validation is unavailable,
        # but they do reach carry-forward, which is what this list covers.
        # ARP_TIMEOUT, slice 0b_3, on all three parents. It is an integer with no
        # defaultValue, so NDFC returns "" when unset. The existing exemption covers
        # that representation; registering it required no engine change. This list is
        # sorted by (parent, nvpair), placing each row in its parent's section.
        ("int_routed_host", "arpTimeout"),
        ("int_routed_host", "dampeningHalfLife"),
        ("int_routed_host", "dampeningMaxSuppress"),
        ("int_routed_host", "dampeningRestartPenalty"),
        ("int_routed_host", "dampeningReuse"),
        ("int_routed_host", "dampeningSuppress"),
        ("int_routed_host", "OSPF_AUTH_KEY_ID"),
        ("int_routed_host", "ospfCost"),
        ("int_routed_host", "ospfDeadInterval"),
        ("int_routed_host", "ospfHelloInterval"),
        ("int_routed_host", "ospfPriority"),
        # SMU 017 (slice 0b_37): the same OSPF integer shape as its int_subif/int_vlan/int_loopback siblings,
        # which NDFC returns as a string ("" when unset); it takes the same exemption.
        ("int_routed_host", "ospfRetransmitInterval"),
        ("int_routed_host", "ospfTransmitDelay"),
        ("int_routed_host", "PIM_DR_PRIORITY"),
        # The routed port-channel OSPF family (slice 0b_40): the seven OSPF integers of int_routed_host on identical
        # 017 declarations. NDFC returns them as strings ("" when unset) on that parent; the same exemption applies.
        ("int_l3_port_channel", "OSPF_AUTH_KEY_ID"),
        # Slice 0b_41: the int_routed_host PIM_DR_PRIORITY contract on an identical declaration; same exemption.
        ("int_l3_port_channel", "PIM_DR_PRIORITY"),
        ("int_l3_port_channel", "ospfCost"),
        ("int_l3_port_channel", "ospfDeadInterval"),
        ("int_l3_port_channel", "ospfHelloInterval"),
        ("int_l3_port_channel", "ospfPriority"),
        ("int_l3_port_channel", "ospfRetransmitInterval"),
        ("int_l3_port_channel", "ospfTransmitDelay"),
        # The six BFD intervals, committed. Reviewed individually, not generated
        # into this list: each was read off the installed template (tx and min_rx 50-999,
        # multiplier 1-50) and takes the same exemption for the same measured reason -- NDFC
        # hands them back as strings. They are also the first bindings here with a narrow
        # maximum, which is what exposed the flat sample value in test_binding_contracts.
        ("int_subif", "arpTimeout"),
        ("int_subif", "bfdMinRxInterval"),
        ("int_subif", "bfdMultiplier"),
        ("int_subif", "bfdTxInterval"),
        ("int_subif", "OSPF_AUTH_KEY_ID"),
        ("int_subif", "ospfCost"),
        ("int_subif", "ospfDeadInterval"),
        ("int_subif", "ospfHelloInterval"),
        ("int_subif", "ospfPriority"),
        ("int_subif", "ospfRetransmitInterval"),
        ("int_subif", "ospfTransmitDelay"),
        ("int_subif", "PIM_DR_PRIORITY"),
        ("int_vlan", "arpTimeout"),
        ("int_vlan", "bfdMinRxInterval"),
        ("int_vlan", "bfdMultiplier"),
        ("int_vlan", "bfdTxInterval"),
        # The three HSRP integers of slice 0b_26 take the same exemption, and the decision is
        # recorded here rather than absorbed by a passing test. NDFC hands all three back as
        # strings, exactly like OSPF_COST, so validating against the returned string is the same
        # choice for the same reason.
        #
        # What they do NOT inherit: the template's rule that the lower threshold cannot exceed
        # the upper one is a relationship BETWEEN two of these integers. Neither this exemption
        # nor the registry's per-field min/max can express it; NDFC enforces it and fails loudly.
        # This list is about representation, not about that constraint.
        ("int_vlan", "HSRP_GROUPv6"),
        ("int_vlan", "hsrpPreemptDelayMinimum"),
        ("int_vlan", "hsrpPriorityForwardingThresholdLower"),
        ("int_vlan", "hsrpPriorityForwardingThresholdUpper"),
        ("int_vlan", "OSPF_AUTH_KEY_ID"),
        ("int_vlan", "ospfCost"),
        ("int_vlan", "ospfDeadInterval"),
        ("int_vlan", "ospfHelloInterval"),
        ("int_vlan", "ospfPriority"),
        ("int_vlan", "ospfRetransmitInterval"),
        ("int_vlan", "ospfTransmitDelay"),
        ("int_vlan", "PIM_DR_PRIORITY"),
        # The three ToR-uplink storm-control PPS levels (slice ul1). The leaf children of a paired ToR store them as ""
        # when unset (measured); the parent stores none of them until a value is sent. The same exemption applies.
        ("int_vpc_uplink_access", "STORM_CONTROL_BCAST_LEVEL_PPS"),
        ("int_vpc_uplink_access", "STORM_CONTROL_MCAST_LEVEL_PPS"),
        ("int_vpc_uplink_access", "STORM_CONTROL_UCAST_LEVEL_PPS"),
    ]), "an integer binding reached the generic carry-forward without being reviewed here"

    # The loopback OSPF-MD key id stays out: its parent registers no passthrough binding, so it
    # never reaches this path and keeps its dedicated validator's [0,255] check.
    assert not any(
        cf["parent_nvpair"] == "OSPF_AUTH_KEY_ID"
        for cf in gie_carry_forward_bindings("int_fabric_loopback_11_1")
    )


def test_the_slice_is_registered_on_the_generic_path():
    """The precondition for every test below.

    With the four OSPF bindings mislabelled ``child_pti`` they never enter the carry-forward,
    so the regression test would pass for the wrong reason. Assert the classification first.
    """
    carried = {b["parent_nvpair"] for b in gie_carry_forward_bindings(ROUTED)}
    for nvpair in ("ospf", "ospfTag", "OSPF_AREA_ID", "ospfCost"):
        assert nvpair in carried, "{0} is not on the generic path".format(nvpair)


# =====================================================================================
# THE CONTROLLER'S REPRESENTATION, value by value
# =====================================================================================
@pytest.mark.parametrize("profile_key,observed", [
    ("enable_ospf", "false"),            # bool binding, covered by the have-string exemption
    ("ospf_tag", ""),                    # plain string, covered by the "" exemption
    ("ospf_area_id", "0.0.0.0"),
    ("ipv4_acl_in", ""),
    ("disable_lldp_transmit", "false"),
])
def test_the_observed_have_values_are_accepted(profile_key, observed):
    """Everything the controller returned is accepted -- except one, asserted next."""
    gie_validate_binding_value(ROUTED, profile_key, observed, value_source="have")


def test_the_observed_empty_cost_is_accepted_and_returned_unchanged():
    """The measured trigger. ``''`` is what Ethernet1/5 actually holds.

    Accepted, and handed back byte-identical: the carry-forward writes this straight into the
    payload, so any coercion here would send the controller a value it never held.
    """
    out = gie_validate_binding_value(ROUTED, "ospf_cost", "", value_source="have")
    assert out == "" and isinstance(out, str), "the HAVE value must round-trip exactly"


def test_a_numeric_string_from_have_is_accepted_and_returned_unchanged():
    """The configured case, and it is SYNTHETIC.

    ``""`` was observed on Ethernet1/5. ``"100"`` was not: no interface in the lab carries a
    cost, so the string encoding for a configured value is inferred from how every other nvPair
    comes back, not measured. The live run settles it. Registering it anyway because it is the
    same code path -- a fix that only special-cased ``""`` would have left it broken.
    """
    out = gie_validate_binding_value(ROUTED, "ospf_cost", "100", value_source="have")
    assert out == "100" and isinstance(out, str), "no int() coercion on the HAVE path"


def test_a_non_numeric_string_from_have_still_fails_closed():
    """The exemption is scoped to encodings NDFC has actually been observed to return."""
    for bad in ("abc", "1.5", "-1", " 100"):
        with pytest.raises(GieBindingError):
            gie_validate_binding_value(ROUTED, "ospf_cost", bad, value_source="have")


@pytest.mark.parametrize("unicode_digits", [
    "\u00b2",              # superscript two
    "\u0661\u0660\u0660",   # Arabic-Indic one-zero-zero
    "\uff11\uff10\uff10",   # fullwidth one-zero-zero
])
def test_non_ascii_digits_from_have_fail_closed(unicode_digits):
    """``str.isdigit()`` alone is True for all of these.

    None is an encoding NDFC returns, and each would otherwise pass straight through into a
    payload -- the value is carried verbatim, so nothing downstream would normalize it. The
    exemption tests ``isascii()`` as well for exactly this reason.
    """
    assert unicode_digits.isdigit(), "fixture no longer exercises the isdigit() gap"
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(ROUTED, "ospf_cost", unicode_digits, value_source="have")


# =====================================================================================
# THE REGRESSION — through the real comparator, to the abort
# =====================================================================================
@pytest.mark.parametrize("state", ["merged", "replaced", "overridden"])
def test_an_unrelated_update_does_not_abort_when_have_holds_an_empty_cost(state):
    """The user-visible defect.

    The operator changes a description on an interface that once had OSPF touched through the
    GUI. They never mention OSPF. The carry-forward reads ``OSPF_COST`` out of HAVE, re-validates
    it against the INPUT contract, and the module aborts.

    Run across all three states rather than assuming their omission contracts are identical --
    they are not: the loopback generic carry-forward is merged-only, while the registered-binding
    carry-forward under test here is not state-gated. If a state turns out to be genuinely
    unaffected, this parametrization is where that shows up.

    On the 62 interfaces where the key is absent this cannot happen; the control below pins that.
    """
    s = _routed_instance()
    s.want = [_routed_want(dict(ROUTED_BUILDER_NV, DESC="changed"))]
    s.have = _routed_have(dict(ROUTED_BUILDER_NV, **ROUTED_HAVE_FULL))
    s.pb_input = [_routed_pb(description="changed")]
    try:
        _run(s, state)
    except _Abort as exc:
        _assert_is_the_cost_have_abort(exc)       # the right abort, not merely an abort
        raise AssertionError(
            "an update unrelated to OSPF must not abort because the controller "
            "represents an unset cost as an empty string: {0}".format(exc)
        )
    assert not s.module.fail_json.called


def test_the_absent_shape_is_unaffected_and_invents_no_default():
    """The control. 62 of the 63 measured interfaces look like this.

    Absence must stay absence: the carry-forward skips the key entirely, and nothing invents
    a 0 or a 1 to fill it.
    """
    s = _routed_instance()
    s.want = [_routed_want(dict(ROUTED_BUILDER_NV, DESC="changed"))]
    s.have = _routed_have(ROUTED_BUILDER_NV)      # no OSPF keys at all
    s.pb_input = [_routed_pb(description="changed")]
    _run(s)
    assert not s.module.fail_json.called, "the absent shape must not abort"
    payload = _payload_nv(s)
    if payload is not None:
        for nvpair in ("ospfCost", "ospfTag", "ospf", "OSPF_AREA_ID"):
            assert nvpair not in payload, "{0} absent from HAVE must not be invented".format(nvpair)


# =====================================================================================
# THE SEPARATION — reading "" does not authorize writing it
# =====================================================================================
def test_an_empty_string_is_still_rejected_as_operator_input():
    """The guard against the tempting over-broad fix.

    Whatever makes the HAVE representation acceptable must not widen the INPUT contract.
    ``ospf_cost`` is an integer the operator writes; ``""`` is the controller's encoding of
    "unset". A fix that relaxes the type globally would silently turn this green.
    """
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(ROUTED, "ospf_cost", "", value_source="explicit")


def test_an_explicit_cost_is_still_type_checked():
    """The input contract stays an integer, in both directions of wrongness."""
    for bad in ("100", "abc", None, True):
        with pytest.raises(GieBindingError):
            gie_validate_binding_value(ROUTED, "ospf_cost", bad, value_source="explicit")
    gie_validate_binding_value(ROUTED, "ospf_cost", 100, value_source="explicit")


def test_a_controller_value_outside_the_range_is_carried_not_rejected():
    """The range is an INPUT contract; HAVE is not re-litigated.

    Caught by inspection after the fix, not by the suite: the have branch returns early only
    for the string encodings NDFC was measured to send, so a native int would otherwise fall
    through to the range check. Rejecting it would make an interface the controller has already
    accepted unmanageable -- exactly the failure the string exemptions exist to prevent.
    """
    for out_of_range in (999999, 0, "999999"):
        assert gie_validate_binding_value(
            ROUTED, "ospf_cost", out_of_range, value_source="have"
        ) == out_of_range


@pytest.mark.parametrize("value,accepted", [
    (0, False), (1, True), (100, True), (65535, True), (65536, False),
])
def test_the_registered_cost_bounds_are_enforced_at_the_edges(value, accepted):
    """The boundaries themselves, not just a value far outside them."""
    if accepted:
        assert gie_validate_binding_value(
            ROUTED, "ospf_cost", value, value_source="explicit"
        ) == value
    else:
        with pytest.raises(GieBindingError):
            gie_validate_binding_value(ROUTED, "ospf_cost", value, value_source="explicit")


def test_an_out_of_range_cost_is_rejected():
    """Declared in the registry, dropped by the generator, enforced by nobody.

    Separate from the HAVE representation defect and fixed separately, but pinned here because
    both are reasons this slice is not yet acceptable.
    """
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(ROUTED, "ospf_cost", 999999, value_source="explicit")


# =====================================================================================
# PRESERVATION — the carry-forward contract that already holds
# =====================================================================================
def test_an_explicit_value_is_not_overwritten_by_have():
    s = _routed_instance()
    want_nv = dict(ROUTED_BUILDER_NV, DESC="changed")
    want_nv["ospfTag"] = "WP98"
    s.want = [_routed_want(want_nv)]
    have = dict(ROUTED_BUILDER_NV, **dict(ROUTED_HAVE_FULL, ospfTag="OLD"))
    have.pop("ospfCost")                          # isolate from the defect above
    s.have = _routed_have(have)
    s.pb_input = [_routed_pb(ospf_tag="WP98", description="changed")]
    _run(s)
    payload = _payload_nv(s)
    assert payload is not None
    assert payload["ospfTag"] == "WP98", "the explicit value must win over HAVE"


def test_an_explicit_cost_is_not_overwritten_by_have():
    """The precedence test on the problematic binding itself.

    The tag case above cannot exercise this: it is a plain string, so it never reaches the
    rejection. Here the operator DOES supply a cost, so the carry-forward must skip the key
    entirely -- the value never goes through the HAVE path, and the abort must not occur even
    before the fix. That is why this is not an xfail.
    """
    s = _routed_instance()
    want_nv = dict(ROUTED_BUILDER_NV, DESC="changed")
    want_nv["ospfCost"] = "100"                   # builder-emitted wire form
    s.want = [_routed_want(want_nv)]
    s.have = _routed_have(dict(ROUTED_BUILDER_NV, **ROUTED_HAVE_FULL))
    s.pb_input = [_routed_pb(ospf_cost=100, description="changed")]
    _run(s)
    payload = _payload_nv(s)
    assert payload is not None
    assert payload["ospfCost"] == "100", "the explicit cost must win over the HAVE value"


def test_a_carried_value_is_not_reported_as_a_requested_change():
    """Transport preservation must not manufacture a diff the operator did not ask for."""
    s = _routed_instance()
    s.want = [_routed_want(dict(ROUTED_BUILDER_NV, DESC="changed"))]
    have = dict(ROUTED_BUILDER_NV, **dict(ROUTED_HAVE_FULL, ospfTag="WP98"))
    have.pop("ospfCost")                          # isolate from the defect above
    s.have = _routed_have(have)
    s.pb_input = [_routed_pb(description="changed")]
    _run(s)
    public = _public_nv(s)
    if public is not None:
        assert "ospfTag" not in public, "a carried value is not a requested change"


def test_an_unchanged_run_is_a_no_op_with_the_cost_present():
    """Idempotence on the problematic value itself.

    The test below deliberately removes OSPF_COST to isolate the other guarantees, so it does
    NOT show idempotence for the value that actually breaks. This one keeps it, and is expected
    to go green with the fix.
    """
    s = _routed_instance()
    s.want = [_routed_want(dict(ROUTED_BUILDER_NV))]
    s.have = _routed_have(dict(ROUTED_BUILDER_NV, **ROUTED_HAVE_FULL))
    s.pb_input = [_routed_pb()]
    _run(s)
    assert not s.module.fail_json.called
    assert _payload_nv(s) is None, "an unchanged run must not emit an update"


def test_a_second_identical_run_produces_no_payload():
    """Idempotence with the cost removed, so the other guarantees are visible today."""
    s = _routed_instance()
    have = dict(ROUTED_BUILDER_NV, **ROUTED_HAVE_FULL)
    have.pop("ospfCost")                          # isolate from the defect above
    s.want = [_routed_want(dict(ROUTED_BUILDER_NV))]
    s.have = _routed_have(have)
    s.pb_input = [_routed_pb()]
    _run(s)
    assert not s.module.fail_json.called
    assert _payload_nv(s) is None, "an unchanged run must not emit an update"


# =====================================================================================
# CHARACTERIZATION — the withdrawal path, NOT a specification
# =====================================================================================
#
# What the template does is read from its body, in EVERY version we hold (the 1081-line
# "first set", 14sep2026, 15sep2026_partial, 15sep2026_full, and templates-patched):
#
#     if enableOspf == "true":
#         if ospfTag == "":     -> "OSPF process tag is required when OSPF is enabled."
#         if ospfAreaId == "":  -> "OSPF area ID is required when OSPF is enabled."
#     elif (... or ospfCost != "" or ...):
#         -> "Enable OSPF on routed interface before configuring OSPF interface options."
#
# The second branch is a REVERSE gate: with OSPF off, a lingering cost is itself rejected.
# It lists OSPF_COST; it does NOT list OSPF_TAG or OSPF_AREA_ID.
#
# That reading is what makes the natural withdrawal -- set enable_ospf false, say nothing
# about the cost -- worth characterizing: the carry-forward would re-send the old cost into
# exactly the payload shape the reverse gate refuses. But a template reading is not a
# measurement, and this project has been burned before by treating one as the other. What
# NDFC does on receipt is UNKNOWN until it is measured.
#
# So the test below asserts only what the module builds. It does not assert that the cost
# ought to be cleared, or how. Turning this into a test that demands automatic deletion would
# be inventing a contract we have not established.


def test_characterize_the_payload_when_ospf_is_disabled_with_a_cost_in_have():
    """Record the payload shape. No claim about what NDFC should do with it."""
    s = _routed_instance()
    want_nv = dict(ROUTED_BUILDER_NV)
    want_nv["ospf"] = "false"
    s.want = [_routed_want(want_nv)]
    s.have = _routed_have(dict(ROUTED_BUILDER_NV, **dict(ROUTED_HAVE_FULL,
                                                         ospf="true",
                                                         ospfTag="WP98",
                                                         ospfCost="100")))
    s.pb_input = [_routed_pb(enable_ospf=False)]
    # No skips here any more. Before the fix this aborted, and skipping past it was the honest
    # outcome; with the fix in place either an abort or a missing payload is a REGRESSION in the
    # offline characterization, not an open question. Let both fail.
    _run(s)
    payload = _payload_nv(s)
    assert payload is not None, (
        "a payload is expected for this transition; if none is produced the characterization "
        "below is stale and the withdrawal analysis must be redone"
    )

    # MEASURED OFFLINE, with the fix in place: the module builds
    #     ENABLE_OSPF 'false'   OSPF_COST '100'   OSPF_TAG 'WP98'   OSPF_AREA_ID '0.0.0.0'
    # The cost is carried forward because the operator omitted it, which is the carry-forward
    # working as designed -- it has no way to know that turning the gate off should also drop
    # the dependent value.
    #
    # That is precisely the payload shape the template's reverse gate refuses:
    #     elif (... or ospfCost != "" or ...):
    #         "Enable OSPF on routed interface before configuring OSPF interface options."
    # The gate lists ospfCost but NOT ospfTag or ospfAreaId, so carrying those two does not
    # trip THIS gate. That is narrower than calling them harmless: the first branch of the same
    # block rejects an empty tag or area while OSPF is enabled, and nothing here establishes how
    # they behave on other transitions.
    #
    # STILL UNMEASURED: whether NDFC actually rejects it. This asserts what the MODULE builds,
    # which is offline-checkable, and deliberately stops there. It does not assert that the
    # cost ought to be cleared, nor how -- deciding that needs a live observation of the full
    # NDFC cycle, and inventing the contract here would be the mistake this file exists to
    # avoid. When that measurement happens, this test is the baseline it changes against.
    assert payload.get("ospf") == "false"
    assert payload.get("ospfCost") == "100", (
        "the omitted cost is expected to be carried forward verbatim; if this changed, the "
        "withdrawal characterization above is stale and must be re-measured"
    )


# ====================================================================================================
# Formerly test_gie_routed_ospf_lot2.py
# OSPF lot 2 on ``int_routed_host`` — the nine non-authentication fields.
#
# Lot 1 (gate, tag, area, cost) was validated on hardware. These nine sit behind the same gate,
# each with its own child template, so they are independent value fields rather than a composite.
#
# WHAT IS ACTUALLY NEW HERE
#     Nothing structural, and that is the point worth recording: no module change was needed.
#     ``gie_nvpair_keymap()`` and ``gie_extend_prof_spec`` derive from the binding table, so nine
#     table rows reach the arg spec, the payload and the carry-forward on their own.
#
#     The shapes were all already handled:
#
#         boolean with a false default   like ENABLE_OSPF
#         integer with no default        like OSPF_COST
#         enum with a "leave it" default like GUARD_MODE ("no") and SPANNING_TREE_PORT_TYPE
#
# THE no_change SENTINEL IS NDFC's, NOT THE ENGINE's
#     Three of the enums default to ``no_change``, which on the controller means "do not touch
#     this on the device". An earlier analysis treated that as a third state the engine would
#     have to model, distinct from a value and from absence. It is not: the engine validates enum
#     membership and transports the string, exactly as it does for ``GUARD_MODE``. The semantics
#     live in the template.
#
#     ``test_the_no_change_enums_behave_exactly_like_the_enums_already_registered`` pins that, so
#     the claim is checked rather than asserted.
#
# TESTED THROUGH THE REAL PATH
#     The positive cases drive ``dcnm_intf_validate_ethernet_interface_input`` and
#     ``dcnm_intf_get_eth_payload``, not a hand-built fixture. That distinction is not academic:
#     a fixture that skipped the arg spec is what hid the FEC defect for an entire round.
#
# Offline: no controller and no device.
# ====================================================================================================
PARENT = "int_routed_host"
NDFC_VERSION = "12.6.0.267"
# Declared explicitly for this file's one engine-driving instance.
PATCH_VERSION = sorted(GIE_ENABLED_PATCH_VERSIONS)[0]

# profile_key -> (nvPair, type, declared default, declared range)
# Read from the installed template, sha b9b50077cf49f8cb -- not from the Excel or the ledger.
LOT2 = {
    "ospf_mtu_ignore": ("ospfMtuIgnore", "boolean", False, None),
    "ospf_shutdown": ("ospfShutdown", "boolean", False, None),
    "ospf_hello_interval": ("ospfHelloInterval", "integer", None, (1, 65535)),
    "ospf_dead_interval": ("ospfDeadInterval", "integer", None, (1, 65535)),
    "ospf_transmit_delay": ("ospfTransmitDelay", "integer", None, (1, 450)),
    "ospf_priority": ("ospfPriority", "integer", None, (0, 255)),
    "ospf_passive_mode": ("ospfPassiveMode", "enum", "no_change",
                          ("no_change", "passive", "no_passive")),
    "ospf_network_type": ("ospfNetworkType", "enum", "no_change",
                          ("no_change", "broadcast", "point_to_point")),
    "ospf_bfd_mode": ("ospfBfdMode", "enum", "no_change",
                      ("no_change", "enable", "disable")),
}

# A valid value per key, for the end-to-end pass. Deliberately not the default: a stage that
# sends the default proves transport but not that the value survived.
SAMPLE = {
    "ospf_mtu_ignore": True,
    "ospf_shutdown": False,
    "ospf_hello_interval": 15,
    "ospf_dead_interval": 60,
    "ospf_transmit_delay": 3,
    "ospf_priority": 42,
    "ospf_passive_mode": "no_passive",
    "ospf_network_type": "point_to_point",
    "ospf_bfd_mode": "disable",
}

WIRE = {
    "ospfMtuIgnore": "true",
    "ospfShutdown": "false",
    "ospfHelloInterval": "15",
    "ospfDeadInterval": "60",
    "ospfTransmitDelay": "3",
    "ospfPriority": "42",
    "ospfPassiveMode": "noPassive",
    "ospfNetworkType": "pointToPoint",
    "ospfBfdMode": "disable",
}

BASE_PROFILE = {
    "mode": "routed", "admin_state": True, "int_vrf": "default",
    "ipv4_addr": "10.98.103.1", "ipv4_mask_len": 30, "mtu": 9216, "speed": "Auto",
    "route_tag": "", "cmds": [], "description": "lot2",
    "enable_ospf": True, "ospf_tag": "WP98", "ospf_area_id": "0.0.0.0", "ospf_cost": 100,
}


def _ospf_lot2_instance(profile):
    obj = object.__new__(dcnm_interface.DcnmIntf)
    obj.intf_info = []
    obj.dcnm_version = 12
    obj.ndfc_version = NDFC_VERSION
    obj.patch_version = PATCH_VERSION
    obj.module = mock.Mock()
    obj.config = [{"name": "eth1/5", "type": "eth", "switch": ["10.1.1.1"],
                   "profile": dict(profile)}]
    return obj


# =====================================================================================
# REGISTRATION
# =====================================================================================
@pytest.mark.parametrize("key,spec", sorted(LOT2.items()))
def test_the_binding_matches_the_installed_template(key, spec):
    nvpair, native, default, bounds = spec
    b = resolve_binding(PARENT, key)
    assert b is not None, "{0} is not registered".format(key)
    assert b["parent_nvpair"] == nvpair
    assert b["type"] == native
    assert b["applicable_interface_type"] == "eth"
    assert b["applicable_mode"] == "routed"
    if native == "enum":
        assert tuple(b["valid_values"]) == bounds
        assert b["default_template"] == default
    elif native == "integer":
        assert (b.get("min_value"), b.get("max_value")) == bounds
        assert "default_template" not in b, "the template declares no default for {0}".format(key)
    else:
        assert b["default_template"] is default


@pytest.mark.parametrize("key", sorted(LOT2))
def test_the_binding_is_on_the_generic_route(key):
    """All nine are passthrough: none owns a dedicated validation path."""
    assert resolve_binding(PARENT, key)["mechanism"] == "passthrough"
    assert key in gie_guarded_keys()
    carried = {b["profile_key"] for b in gie_carry_forward_bindings(PARENT)}
    assert key in carried, "omitting {0} would drop the controller's value".format(key)


# =====================================================================================
# THE no_change SENTINEL
# =====================================================================================
@pytest.mark.parametrize("key", ["ospf_passive_mode", "ospf_network_type", "ospf_bfd_mode"])
def test_the_no_change_enums_behave_exactly_like_the_enums_already_registered(key):
    """The claim that ``no_change`` needs no new engine handling, checked rather than asserted.

    ``GUARD_MODE`` is the precedent: an enum whose default ("no") also means "off". The engine
    treats both identically -- membership plus transport. If ``no_change`` ever needed special
    handling, this test would be the place it shows up.
    """
    b = resolve_binding(PARENT, key)
    guard = resolve_binding("int_trunk_host", "guard_mode")
    assert b["type"] == guard["type"] == "enum"
    assert b["default_template"] in b["valid_values"]
    assert guard["default_template"] in guard["valid_values"]

    # Accepted as an ordinary value in both directions, like any other enum member.
    assert gie_validate_binding_value(PARENT, key, "no_change") == "no_change"
    assert gie_validate_binding_value(PARENT, key, "no_change", value_source="have") == "no_change"
    # And a non-member still fails closed.
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(PARENT, key, "leave_alone")


# =====================================================================================
# RANGES
# =====================================================================================
@pytest.mark.parametrize("key,lo,hi", [
    ("ospf_hello_interval", 1, 65535),
    ("ospf_dead_interval", 1, 65535),
    ("ospf_transmit_delay", 1, 450),
    ("ospf_priority", 0, 255),
])
def test_the_declared_range_is_enforced_at_the_edges(key, lo, hi):
    """Each bound comes from the template, and they differ per field -- 450 and 255 are not
    copies of 65535. Getting one wrong would silently accept a value NDFC rejects.
    """
    assert gie_validate_binding_value(PARENT, key, lo) == lo
    assert gie_validate_binding_value(PARENT, key, hi) == hi
    for bad in (lo - 1, hi + 1):
        with pytest.raises(GieBindingError):
            gie_validate_binding_value(PARENT, key, bad)


@pytest.mark.parametrize("key", ["ospf_hello_interval", "ospf_priority"])
def test_a_controller_value_outside_the_range_is_carried_not_rejected_ospf_lot2(key):
    """The range is an INPUT contract. HAVE is the controller's, and is not re-litigated."""
    assert gie_validate_binding_value(PARENT, key, "99999", value_source="have") == "99999"
    assert gie_validate_binding_value(PARENT, key, "", value_source="have") == ""


# =====================================================================================
# THE REAL MODULE PATH
# =====================================================================================
def test_the_lot_survives_the_real_ethernet_validator():
    obj = _ospf_lot2_instance(dict(BASE_PROFILE, **SAMPLE))
    obj.dcnm_intf_validate_ethernet_interface_input(obj.config)
    assert not obj.module.fail_json.called, (
        "the routed arg spec rejected lot 2: {0}".format(obj.module.fail_json.call_args)
    )
    profile = obj.config[0]["profile"]
    for key, value in SAMPLE.items():
        assert key in profile, "{0} was dropped by validation".format(key)
        assert profile[key] == value, "{0} was altered by validation".format(key)


def test_the_lot_reaches_the_payload_through_the_real_builder():
    obj = _ospf_lot2_instance(dict(BASE_PROFILE, **SAMPLE))
    intf = {
        "policy": PARENT, "interfaceType": "INTERFACE_ETHERNET",
        "interfaces": [{"serialNumber": "SNO", "ifName": "Ethernet1/5", "nvPairs": {}}],
    }
    obj.dcnm_intf_get_eth_payload(obj.config[0], intf, "profile")
    nvpairs = intf["interfaces"][0]["nvPairs"]
    for nvpair, expected in WIRE.items():
        assert nvpair in nvpairs, "{0} never reached the payload".format(nvpair)
        assert nvpairs[nvpair] == expected, (
            "{0}: expected {1!r}, got {2!r}".format(nvpair, expected, nvpairs[nvpair])
        )
        assert isinstance(nvpairs[nvpair], str), "nvPairs must be strings"


def test_an_omitted_field_emits_nothing():
    """explicit_only: omission is not a value, so nothing is sent and nothing is defaulted."""
    obj = _ospf_lot2_instance(BASE_PROFILE)          # none of the nine set
    intf = {
        "policy": PARENT, "interfaceType": "INTERFACE_ETHERNET",
        "interfaces": [{"serialNumber": "SNO", "ifName": "Ethernet1/5", "nvPairs": {}}],
    }
    obj.dcnm_intf_get_eth_payload(obj.config[0], intf, "profile")
    nvpairs = intf["interfaces"][0]["nvPairs"]
    for nvpair in WIRE:
        assert nvpair not in nvpairs, (
            "{0} was emitted although the operator never set it".format(nvpair)
        )


# =====================================================================================
# THE AUTHENTICATION FAMILY, NOW REGISTERED
# =====================================================================================
#
# This block used to assert the opposite: that the five were deliberately ABSENT, pending their
# own lot. That lot landed. The assertion is inverted rather than deleted, because "absent" and
# "present" are both decisions and the file should say which one is in force.
#
# Their arrival also settled the question the old comment left open. Three of them once existed
# as child_pti on int_fabric_loopback_11_1; that capability was withdrawn, so there is no
# second mechanism to reconcile with -- all five are passthrough, like every other binding.
AUTH_FIELDS = {
    "enable_ospf_auth": ("ospfAuthentication", "boolean", False),
    "ospf_auth_key_id": ("OSPF_AUTH_KEY_ID", "integer", False),
    "ospf_auth_key": ("OSPF_AUTH_KEY", "string", True),
    "ospf_authentication_key_type": ("ospfAuthenticationKeyType", "enum", False),
    "ospf_authentication_key": ("ospfAuthenticationKey", "string", True),
}


@pytest.mark.parametrize("key", sorted(AUTH_FIELDS))
def test_the_authentication_fields_are_registered_on_this_parent(key):
    nvpair, typ, unused_is_secret = AUTH_FIELDS[key]
    b = resolve_binding(PARENT, key)
    assert b is not None, "{0} is no longer registered on {1}".format(key, PARENT)
    assert b["parent_nvpair"] == nvpair
    assert b["type"] == typ
    assert b["mechanism"] == "passthrough"


@pytest.mark.parametrize("key", sorted(AUTH_FIELDS))
def test_only_the_two_key_bearing_fields_are_marked_no_log(key):
    """The id and the encryption-type selector must stay visible, and that is not a detail.

    Ansible scrubs by STRING MATCH. Marking ospf_auth_key_id would make it replace the bare
    digits of that id -- "1", "7" -- everywhere they appear in every result, corrupting
    unrelated output while protecting nothing, since an id is not a secret. The same goes for
    the "3" of the encryption type.
    """
    unused_nvpair, unused_typ, is_secret = AUTH_FIELDS[key]
    assert bool(resolve_binding(PARENT, key).get("no_log")) is is_secret


# ====================================================================================================
# Formerly test_gie_routed_enum_omission_b3.py
# Withdrawal acceptance for the two routed OSPF ENUM identities.
#
#     int_routed_host :: ospfPassiveMode   reset_wire "noChange"
#     int_routed_host :: ospfNetworkType   reset_wire "noChange"
#
# These two are the first registered resets whose WIRE spelling is not their PUBLIC
# spelling. The public neutral is `no_change`; the nvPair the controller stores is
# `noChange`. Everything here keeps those two vocabularies apart, because collapsing them
# is the failure this registration could introduce.
#
# WHAT THE PILOT MATRIX ALREADY COVERS, AND IS NOT REPEATED HERE
#
# `test_binding_withdrawal.py` parametrises both rows through the real `main()`: omission
# alone under `replaced`, merged preservation, explicit-clear precedence, version gating,
# the unsupported-row rejection and the per-row registry assertion. Its fixture uses
# `no_passive` and `point_to_point`.
#
# WHAT THIS FILE ADDS
#
#   * the OTHER non-neutral value of each pair -- `passive` and `broadcast`;
#   * the neutral already in HAVE: no reset may be sent for a value already neutral;
#   * BOTH keys omitted in one config: both resets in one payload;
#   * partial omission in both directions: the explicit companion survives untouched;
#   * check mode: the plan carries both resets and NOTHING is transmitted;
#   * rerun from the neutral state: converges with no configuration or deploy request;
#   * a sibling routed enum WITHOUT a reset keeps its own specific rejection, so this
#     registration did not open a blanket exemption;
#   * positive and negative for the two vocabulary-aware harness helpers.
#
# Offline. Real `main()`, real argument spec, real validation, real serialisation; mocks
# only at inventory/transport. Assertions are made against the CAPTURED REQUEST and the
# PUBLIC DIFF, never against `changed`.
#
# The `other` request bucket holds the pre-existing bulk-api capability probe
# (`dcnm_get_bulk_api_support`, an empty POST to bulk-update/networks). It is counted
# separately from configuration and deploy on purpose and is not this work's to fix.
# ====================================================================================================
RESET = "noChange"

# (public profile key, nvPair, the two non-neutral public values, their wire spellings)
PASSIVE = ("ospf_passive_mode", "ospfPassiveMode",
           {"passive": "passive", "no_passive": "noPassive"})
NETWORK = ("ospf_network_type", "ospfNetworkType",
           {"broadcast": "broadcast", "point_to_point": "pointToPoint"})
BOTH = [PASSIVE, NETWORK]

# The variants the pilot fixture does NOT use, so both values of both enums get exercised.
OTHER_VARIANT = [
    (PASSIVE[0], PASSIVE[1], "passive"),
    (NETWORK[0], NETWORK[1], "broadcast"),
]
OTHER_IDS = ["%s=%s" % (k, v) for k, _n, v in OTHER_VARIANT]


def _ospf(**extra):
    """The OSPF base group plus whatever the case pins explicitly."""
    d = dict(OSPF_CTX)
    d.update(extra)
    return d


# =========================================================== the registration itself
@pytest.mark.parametrize("key,nvpair,variants", BOTH, ids=[b[0] for b in BOTH])
def test_the_row_is_registered_with_the_neutral_wire_string(key, nvpair, variants):
    """Guard the guard: every case below is about a registered reset. If the
    regeneration ever dropped it, they would pass for the wrong reason."""
    b = resolve_binding(ROUTED_ENUM_ROUTED, key)
    assert b is not None, "%s::%s is not in the table at all" % (ROUTED_ENUM_ROUTED, key)
    assert b["parent_nvpair"] == nvpair
    assert b.get("reset_wire") == RESET
    assert isinstance(b["reset_wire"], str), "the reset must be the wire STRING"
    # The public vocabulary is untouched by the registration.
    assert "no_change" in b["valid_values"]
    assert RESET not in b["valid_values"], (
        "the WIRE spelling leaked into public valid_values")
    assert b["wire_values"]["no_change"] == RESET


# ================================================== the other non-neutral variant
@pytest.mark.parametrize("key,nvpair,applied", OTHER_VARIANT, ids=OTHER_IDS)
def test_omission_from_the_other_variant_emits_the_reset(key, nvpair, applied):
    """The pilot drives `no_passive`/`point_to_point`; these are `passive`/`broadcast`."""
    have = build_have(ROUTED_ENUM_ROUTED, key, applied, **OSPF_CTX)
    result, calls = run(base_for(ROUTED_ENUM_ROUTED, **OSPF_CTX), "replaced", have)
    nv = request_nvpairs(calls)
    assert nv, ("no request was sent: the omission went undetected. changed=%s"
                % result.get("changed"))
    assert nv[0].get(nvpair) == RESET, (
        "omitting %s from HAVE=%r must send %r, got %r"
        % (key, applied, RESET, nv[0].get(nvpair)))
    assert not result.get("failed"), result.get("msg")


@pytest.mark.parametrize("key,nvpair,applied", OTHER_VARIANT, ids=OTHER_IDS)
def test_merged_preserves_the_other_variant(key, nvpair, applied):
    """Under `merged` an unrelated edit must re-send the controller's own wire value."""
    have = build_have(ROUTED_ENUM_ROUTED, key, applied, **OSPF_CTX)
    _result, calls = run(
        base_for(ROUTED_ENUM_ROUTED, description="b3-merged", **OSPF_CTX), "merged", have)
    nv = request_nvpairs(calls)
    assert nv, "the description change produced no request"
    assert nv[0].get(nvpair) == wire_for(ROUTED_ENUM_ROUTED, key, applied)


# ============================================ neutral already in HAVE: no reset needed
@pytest.mark.parametrize("key,nvpair,variants", BOTH, ids=[b[0] for b in BOTH])
def test_a_value_already_neutral_needs_no_reset(key, nvpair, variants):
    """`noChange` in HAVE is the withdrawn state. Sending a reset for it would claim a
    change that is not needed; the classifier must say NONE."""
    action, wire = gie_withdrawal_action(ROUTED_ENUM_ROUTED, key, RESET, SUPPORTED, SUPPORTED_PATCH)
    assert (action, wire) == (GIE_WITHDRAW_NONE, None), (
        "a neutral HAVE must classify as NONE, got %r" % ((action, wire),))


@pytest.mark.parametrize("key,nvpair,variants", BOTH, ids=[b[0] for b in BOTH])
def test_a_configured_value_classifies_as_reset(key, nvpair, variants):
    """The complement of the case above, for both non-neutral values."""
    for public, wire_value in variants.items():
        action, wire = gie_withdrawal_action(ROUTED_ENUM_ROUTED, key, wire_value, SUPPORTED, SUPPORTED_PATCH)
        assert (action, wire) == (GIE_WITHDRAW_RESET, RESET), (
            "HAVE=%r (public %r) must classify as RESET/%r, got %r"
            % (wire_value, public, RESET, (action, wire)))


# ================================================ both keys omitted in one config
def test_both_keys_omitted_together_send_both_resets():
    """One config, two withdrawals. A payload carrying only one of them would leave the
    other value in place while the run reported success."""
    have = build_have(ROUTED_ENUM_ROUTED, **_ospf(ospf_passive_mode="no_passive",
                                                  ospf_network_type="point_to_point"))
    result, calls = run(base_for(ROUTED_ENUM_ROUTED, **OSPF_CTX), "replaced", have)
    nv = request_nvpairs(calls)
    assert nv, "no request was sent for the paired omission"
    assert nv[0].get("ospfPassiveMode") == RESET, "passive mode reset missing"
    assert nv[0].get("ospfNetworkType") == RESET, "network type reset missing"
    assert not result.get("failed"), result.get("msg")
    # The public diff must own both too, independently of the request.
    dnv = diff_nvpairs(result)
    assert dnv and dnv[0].get("ospfPassiveMode") == RESET
    assert dnv[0].get("ospfNetworkType") == RESET


def test_the_paired_omission_preserves_the_ospf_context():
    """The gate and its mandatory group are not collateral of a withdrawal."""
    have = build_have(ROUTED_ENUM_ROUTED, **_ospf(ospf_passive_mode="no_passive",
                                                  ospf_network_type="point_to_point"))
    _result, calls = run(base_for(ROUTED_ENUM_ROUTED, **OSPF_CTX), "replaced", have)
    nv = request_nvpairs(calls)[0]
    assert nv.get("ospf") == "true", "OSPF was disabled by a withdrawal"
    assert nv.get("ospfTag") == OSPF_CTX["ospf_tag"]
    assert nv.get("OSPF_AREA_ID") == OSPF_CTX["ospf_area_id"]


# ==================================================== partial omission, both directions
@pytest.mark.parametrize(
    "omitted,omitted_nv,kept,kept_nv,kept_value",
    [
        ("ospf_passive_mode", "ospfPassiveMode",
         "ospf_network_type", "ospfNetworkType", "point_to_point"),
        ("ospf_network_type", "ospfNetworkType",
         "ospf_passive_mode", "ospfPassiveMode", "no_passive"),
    ],
    ids=["omit-passive-keep-network", "omit-network-keep-passive"],
)
def test_partial_omission_keeps_the_explicit_companion(
    omitted, omitted_nv, kept, kept_nv, kept_value
):
    """One key omitted, the other still explicit. The companion must keep its own wire
    value -- a reset that spilled onto it would be invisible in a summary count."""
    have = build_have(ROUTED_ENUM_ROUTED, **_ospf(**{omitted: "passive" if "passive" in omitted
                                                     else "broadcast",
                                                     kept: kept_value}))
    result, calls = run(base_for(ROUTED_ENUM_ROUTED, **_ospf(**{kept: kept_value})),
                        "replaced", have)
    nv = request_nvpairs(calls)
    assert nv, "no request was sent for the partial omission"
    assert nv[0].get(omitted_nv) == RESET, "the omitted key did not get its reset"
    assert nv[0].get(kept_nv) == wire_for(ROUTED_ENUM_ROUTED, kept, kept_value), (
        "the explicit companion %s changed: expected %r, got %r"
        % (kept_nv, wire_for(ROUTED_ENUM_ROUTED, kept, kept_value), nv[0].get(kept_nv)))
    assert not result.get("failed"), result.get("msg")


# ============================================================== check mode and rerun
def test_check_mode_plans_both_resets_and_transmits_nothing():
    """A plan is not a write. The diff must carry both resets and the transport must
    see no configuration and no deploy request."""
    have = build_have(ROUTED_ENUM_ROUTED, **_ospf(ospf_passive_mode="no_passive",
                                                  ospf_network_type="point_to_point"))
    result, calls = run_configs(
        [cfg(IF_A, base_for(ROUTED_ENUM_ROUTED, **OSPF_CTX))], "replaced", have, check_mode=True)
    dnv = diff_nvpairs(result)
    assert dnv, "check mode planned nothing at all"
    assert dnv[0].get("ospfPassiveMode") == RESET
    assert dnv[0].get("ospfNetworkType") == RESET
    buckets = split_calls(calls)
    assert buckets["updates"] == [], "check mode sent a configuration request"
    assert buckets["deploys"] == [], "check mode sent a deploy request"


def test_rerun_from_the_neutral_state_converges():
    """With both values already neutral, the same model must configure nothing and
    deploy nothing. `changed` alone is not the evidence: the buckets are."""
    have = build_have(ROUTED_ENUM_ROUTED, **_ospf(ospf_passive_mode="no_change",
                                                  ospf_network_type="no_change"))
    result, calls = run(base_for(ROUTED_ENUM_ROUTED, **OSPF_CTX), "replaced", have)
    buckets = split_calls(calls)
    assert buckets["updates"] == [], (
        "a converged rerun sent a configuration request: %s"
        % [c["path"] for c in buckets["updates"]])
    assert buckets["deploys"] == [], "a converged rerun sent a deploy request"
    assert not result.get("failed"), result.get("msg")


# =================================================== the sibling row keeps its rejection
def test_a_sibling_routed_enum_without_a_reset_still_rejects():
    """`ospf_bfd_mode` is the third routed OSPF enum and carries NO reset. Registering
    these two must not turn into a blanket exemption for the family."""
    # THE EXAMPLE IS DERIVED, NOT HARDCODED. This case named `ospf_bfd_mode` and asserted that
    # it carried no reset, with the message "this case no longer guards anything" -- which is
    # exactly what happened when the OSPF-ALL P2 profile measured and registered it on
    # int_routed_host. The contract it guards is intact; only the example expired.
    #
    # Deriving it from the loaded table means a future registration can never invalidate this
    # case again, and if routed ever ran out of unregistered enums the assertion below says so
    # loudly instead of the case passing for the wrong reason.
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
        BINDING_TABLE as _BT,
    )
    _rows = list(_BT.values()) if isinstance(_BT, dict) else list(_BT)
    siblings = [r for r in _rows
                if r["parent_template"] == ROUTED_ENUM_ROUTED and r["type"] == "enum"
                and r.get("reset_wire") is None
                and r.get("default_template") is not None]
    assert siblings, (
        "every routed enum now carries a reset; this case has nothing left to guard and must "
        "be rehomed deliberately, not deleted")
    b = siblings[0]
    key, default = b["profile_key"], b["default_template"]
    # A CONFIGURED value, i.e. anything that is not the declared default.
    configured = "0" if default != "0" else "7"
    action, wire = gie_withdrawal_action(ROUTED_ENUM_ROUTED, key, configured, SUPPORTED, SUPPORTED_PATCH)
    assert (action, wire) == (GIE_WITHDRAW_UNSUPPORTED, None), (
        "%s: a configured value with no registered reset must stay UNSUPPORTED, got %r"
        % (key, (action, wire)))
    # And its own declared default is still NONE, for the same reason as the registered rows.
    assert gie_withdrawal_action(ROUTED_ENUM_ROUTED, key, default, SUPPORTED, SUPPORTED_PATCH) == (
        GIE_WITHDRAW_NONE, None), (
        "%s: its own declared default %r must classify NONE" % (key, default))


# ========================================= the two vocabulary-aware harness helpers
def test_wire_for_translates_only_when_the_binding_declares_a_vocabulary():
    """Positive: the OSPF enums translate. Negative: a binding without `wire_values`
    is returned untouched, so every pre-existing caller keeps its behaviour."""
    assert wire_for(ROUTED_ENUM_ROUTED, "ospf_passive_mode", "no_passive") == "noPassive"
    assert wire_for(ROUTED_ENUM_ROUTED, "ospf_network_type", "point_to_point") == "pointToPoint"
    assert wire_for(ROUTED_ENUM_ROUTED, "ospf_passive_mode", "passive") == "passive"
    # No vocabulary declared: unchanged, including the non-string forms.
    assert wire_for(ROUTED_ENUM_ROUTED, "acl_filter", "ACL-X") == "ACL-X"
    assert wire_for(ROUTED_ENUM_ROUTED, "disable_ipv4_redirects", True) == "true"


def test_public_clear_for_returns_the_public_spelling_not_the_wire_one():
    """Positive: the public input that requests the reset. Negative: the wire spelling
    is NOT public vocabulary, and a binding with no public clear says None."""
    assert public_clear_for(ROUTED_ENUM_ROUTED, "ospf_passive_mode", RESET) == "no_change"
    assert public_clear_for(ROUTED_ENUM_ROUTED, "ospf_network_type", RESET) == "no_change"
    # The wire spelling must never come back as the public answer.
    assert public_clear_for(ROUTED_ENUM_ROUTED, "ospf_passive_mode", RESET) != RESET
    # A reset with no public spelling in the vocabulary is reported as absent.
    assert public_clear_for(ROUTED_ENUM_ROUTED, "ospf_passive_mode", "nonsense") is None
    # A binding without a vocabulary behaves exactly as the old inline rule did.
    assert public_clear_for(ROUTED_ENUM_ROUTED, "acl_filter", "") == ""
    assert public_clear_for(ROUTED_ENUM_ROUTED, "disable_ipv4_redirects", "false") is False


def test_the_public_neutral_is_accepted_and_the_wire_spelling_is_refused():
    """The vocabulary split, through the real argument spec: `no_change` is valid input
    and `noChange` is not. This is what keeps the registration from leaking the wire
    spelling into the public interface."""
    have = build_have(ROUTED_ENUM_ROUTED, "ospf_passive_mode", "no_passive", **OSPF_CTX)
    ok, _calls = run(base_for(ROUTED_ENUM_ROUTED, **_ospf(ospf_passive_mode="no_change")),
                     "replaced", have)
    assert not ok.get("failed"), ok.get("msg")

    bad, calls = run(base_for(ROUTED_ENUM_ROUTED, **_ospf(ospf_passive_mode=RESET)),
                     "replaced", have)
    assert bad.get("failed"), "the WIRE spelling was accepted as public input"
    assert split_calls(calls)["updates"] == [], (
        "the refused wire spelling still sent a configuration request")


# ====================================================================================================
# Formerly test_gie_ospf_gate_inert_withdrawal.py
# R-F4: disabling OSPF and retiring a routed port after an OSPF tag was set.
#
# NaC rule 323 refuses any OSPF sub-field without `enable_ospf: true`, so disabling OSPF sends
# `enable_ospf: false` and no `ospf_tag`. The registry has no verified reset for `ospfTag`
# (the template declares `minLength = 1` and no default), so the omitted tag was classified as
# "cannot be classified as already withdrawn" and every later reset to the leaf default was
# refused with "no verified withdrawal": once a tag was set, the port could not leave
# int_routed_host through the module.
#
# The int_routed_host, int_subif and int_vlan template bodies validate and render `ospfTag` only
# under `ospf == true`, and with OSPF off they neither check it nor create the OSPF child. Those
# rows declare `inert_when: {nvpair: ospf, value: 'false'}`: a stored tag under a disabled gate is
# not a withdrawal target, is kept as stored, and transports nothing new. In the default VRF int_loopback
# falls back to the fabric underlay when OSPF is off, so its tag stays live there (test_binding_ospf_loopback_subif.py).
#
# The routed HAVE is a real NDFC 12.6.0.267 interface read (fixtures/routing_have_cases.json#dcnm_intf_routed_ospf_have).
# Real main() through helpers/binding_harness.
# ====================================================================================================
FIXTURE = load_case("dcnm_intf_routed_ospf_have")
OSPF_OPTIONS_NEUTRAL = {
    "ospfAuthentication": "false", "ospfAuthenticationKey": "", "ospfBfdMode": "noChange", "ospfCost": "",
    "ospfDeadInterval": "", "ospfHelloInterval": "", "ospfMtuIgnore": "false", "ospfNetworkType": "noChange",
    "ospfPassiveMode": "noChange", "ospfPriority": "", "ospfShutdown": "false", "ospfTransmitDelay": "",
}
# The NaC P-OSPF-OFF item for this port: enable_ospf false and no ospf_* key (rule 323).
OSPF_OFF = {"mode": "routed", "enable_ospf": False, "ipv4_addr": "192.0.2.17", "ipv4_mask_len": 30}
STATES = ("deleted", "overridden")


def real_have(**nvpairs):
    nv = copy.deepcopy(FIXTURE["nvPairs"])
    nv.update(nvpairs)
    return [{"policy": FIXTURE["policy"], "interfaces": [{"serialNumber": h.SERIAL, "ifName": h.IF_A, "fabricName": h.FABRIC,
                                                          "interfaceType": "INTERFACE_ETHERNET", "nvPairs": nv}]}]


def ospf_off_have():
    """What the accepted OSPF-off replacement leaves: gate off, options neutral, the tag still stored."""
    return real_have(ospf="false", **OSPF_OPTIONS_NEUTRAL)


def sent_policies(calls):
    return F2.reset_policies(calls)


def replaced(profile, have):
    return F2.run("replaced", have, "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])


def retire(state, have):
    return F2.run(state, have, "leaf", configs=None if state == "deleted" else [])


# ------------------------------------------------------------------ disabling OSPF through the caller's shape
def test_nac_ospf_off_is_accepted_and_keeps_the_inert_tag():
    result, calls = replaced(OSPF_OFF, real_have())
    assert not result.get("failed"), result.get("msg")
    pol = sent_policies(calls)
    assert len(pol) == 1 and pol[0]["policy"] == "int_routed_host"
    nv = pol[0]["interfaces"][0]["nvPairs"]
    assert nv["ospf"] == "false"
    assert nv["ospfTag"] == FIXTURE["nvPairs"]["ospfTag"], "the stored tag is kept, not withdrawn and not invented"
    # The template refuses OSPF options with OSPF off: every one of them is at its neutral value.
    assert dict((k, nv[k]) for k in OSPF_OPTIONS_NEUTRAL) == OSPF_OPTIONS_NEUTRAL


def test_the_same_request_again_is_a_noop():
    first, calls = replaced(OSPF_OFF, real_have())
    assert not first.get("failed"), first.get("msg")
    have = F2.as_have(calls)
    result, calls = replaced(OSPF_OFF, have)
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


def test_omitting_the_gate_resets_it_and_keeps_the_tag():
    profile = dict((k, v) for k, v in OSPF_OFF.items() if k != "enable_ospf")
    result, calls = replaced(profile, real_have())
    assert not result.get("failed"), result.get("msg")
    nv = sent_policies(calls)[0]["interfaces"][0]["nvPairs"]
    assert nv["ospf"] == table.resolve_by_nvpair("int_routed_host", "ospf")["reset_wire"]
    assert nv["ospfTag"] == FIXTURE["nvPairs"]["ospfTag"]


def test_keeping_ospf_on_still_refuses_an_omitted_tag():
    result, calls = replaced(dict(OSPF_OFF, enable_ospf=True), real_have())
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    assert "cannot be classified as already withdrawn" in result["msg"] and "ospf_tag on int_routed_host" in result["msg"]


# ------------------------------------------------------------------ retiring the port to the leaf default
@pytest.mark.parametrize("state", STATES)
def test_retiring_after_disabling_resets_to_trunk(state):
    result, calls = retire(state, ospf_off_have())
    assert not result.get("failed"), result.get("msg")
    pol = sent_policies(calls)
    assert len(pol) == 1 and pol[0]["policy"] == "int_trunk_host"
    nv = pol[0]["interfaces"][0]["nvPairs"]
    assert "ospf" not in nv and "ospfTag" not in nv, "a source-only nvPair is never written into the destination"


@pytest.mark.parametrize("state", STATES)
def test_retiring_with_ospf_on_to_the_leaf_default_drops_ospf_with_the_policy(state):
    """int_routed_host drops every binding with a policy change (its delete() removes the OSPF child policies), so a
    leaf reset with OSPF still on proceeds with one write and sends neither ospf nor the tag."""
    result, calls = retire(state, real_have())
    assert not result.get("failed"), result.get("msg")
    pol = sent_policies(calls)
    assert len(pol) == 1 and pol[0]["policy"] == "int_trunk_host"
    nv = pol[0]["interfaces"][0]["nvPairs"]
    assert "ospf" not in nv and "ospfTag" not in nv
    assert FIXTURE["nvPairs"]["ospfTag"] not in str(calls)


@pytest.mark.parametrize("state", STATES)
def test_resetting_with_ospf_on_to_the_same_parent_turns_the_gate_off_and_keeps_the_tag_inert(state):
    """border: the default is int_routed_host itself; the reset sends ospf "false" and the stored tag, inert under that
    final gate, is neither sent nor refused (D-3)."""
    result, calls = F2.run(state, real_have(), "border", configs=None if state == "deleted" else [])
    assert not result.get("failed"), result.get("msg")
    pol = sent_policies(calls)
    assert len(pol) == 1 and pol[0]["policy"] == "int_routed_host"
    nv = pol[0]["interfaces"][0]["nvPairs"]
    assert nv["ospf"] == table.resolve_by_nvpair("int_routed_host", "ospf")["reset_wire"] and "ospfTag" not in nv


# ------------------------------------------------------------------ the other declared parents, and the excluded one
@pytest.mark.parametrize("parent", (h.SUBIF, h.SVI))
def test_ospf_off_keeps_the_inert_tag_on_subif_and_svi(parent):
    have = h.build_have(parent, **h.OSPF_CTX)
    assert have[0]["interfaces"][0]["nvPairs"]["ospfTag"] == h.OSPF_CTX["ospf_tag"]
    profile = h.base_for(parent, enable_ospf=False)
    result, calls = h.run(profile, "replaced", have=have, parent=parent)
    assert not result.get("failed"), result.get("msg")
    nv = sent_policies(calls)[0]["interfaces"][0]["nvPairs"]
    assert nv["ospf"] == "false" and nv["ospfTag"] == h.OSPF_CTX["ospf_tag"]


def test_default_vrf_loopback_tag_stays_live_and_is_still_refused():
    """int_loopback configures OSPF from the fabric underlay when ospf is false in the default VRF, with the stored tag
    first: there the tag is not inert (`unless` INTF_VRF), and a disable that omits it is still refused."""
    assert table.resolve_by_nvpair(h.LOOPBACK, "ospfTag")["inert_when"]["unless"] == {
        "nvpair": "INTF_VRF", "values": ("", "default")}
    assert h.base_for(h.LOOPBACK)["int_vrf"] == "default"
    have = h.build_have(h.LOOPBACK, **h.OSPF_CTX)
    result, calls = h.run(h.base_for(h.LOOPBACK, enable_ospf=False), "replaced", have=have, parent=h.LOOPBACK)
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    assert "ospf_tag on int_loopback" in result["msg"]


# ------------------------------------------------------------------ engine and generator contract
def test_engine_inertness_compares_the_gate_in_wire_form():
    row = table.resolve_by_nvpair("int_routed_host", "ospfTag")
    assert row["inert_when"] == {"nvpair": "ospf", "value": "false", "required": True}
    assert engine.gie_binding_inert(row, {"ospf": "false"}) and engine.gie_binding_inert(row, {"ospf": False})
    assert not engine.gie_binding_inert(row, {"ospf": "true"}) and not engine.gie_binding_inert(row, {})
    assert not engine.gie_binding_inert(table.resolve_by_nvpair("int_routed_host", "aclFilter"), {"ospf": "false"})


def _rows_with(parent, nvpair, **row_update):
    rows = thin._as_slice_rows(table.BINDING_TABLE)
    for r in rows:
        if r["parent_template"] == parent and r["parent_nvpair"] == nvpair:
            r.update(row_update)
    return rows


@pytest.mark.parametrize("inert_when, match", [
    (("ospf", "false"), "must be a mapping"),
    ({"nvpair": "ospf"}, "must be a mapping"),
    ({"nvpair": "ospf", "value": False}, "must be a mapping"),
    ({"nvpair": "aclFilter", "value": "false"}, "not another committed binding of the same parent"),
    ({"nvpair": "ospfTag", "value": "false"}, "not another committed binding of the same parent"),
    ({"nvpair": "ospf", "value": "true"}, "verified reset or declared default"),
])
def test_generator_rejects_an_unsupported_inert_when(inert_when, match):
    generator = thin._load_generator()
    with pytest.raises(ValueError, match=match):
        generator.compile_rows(_rows_with("int_routed_host", "ospfTag", inert_when=inert_when))


# ====================================================================================================
# Formerly test_gie_ospf_dependency_followup.py
# OSPF dependent fields after a disable: authentication, merged disable, explicit contradictions, reset guidance.
#
# Template evidence (int_routed_host 6d37ea6a, int_subif e9f9bd9c, int_vlan f32ef586, static reads):
#   * every OSPF option is rendered only when `ospf` is true, and a non-neutral option is refused while it is false;
#   * the simple-key encryption type is used and validated only with a non-empty `ospfAuthenticationKey`;
#   * the message-digest key ID and key are validated and rendered only when `ospfAuthentication` is true;
#   * `ospfTag` is required while `ospf` is true.
# NDFC 12.6.0.267 stores `OSPF_AUTH_KEY` as "" with authentication off (read back); a set -> "" transition of a real key
# is NOT measured.
#
# Real main() through helpers/binding_harness. Synthetic secrets only; no message may contain them.
# ====================================================================================================
SYN_MD5 = "SYNTH-MD5-KEY-NOT-REAL-0001"
SYN_SIMPLE = "SYNTH-SIMPLE-NOT-REAL-02"
# The routed port-channel joined with slice 0b_40; it runs through the generic h.run/h.build_have path like subif and SVI.
PARENTS = (h.ROUTED, h.SUBIF, h.SVI, h.PC_L3)
NO_REQUEST = "No configuration or deployment request was sent"


def sent(calls):
    pol = F2.reset_policies(calls)
    return pol[0]["interfaces"][0]["nvPairs"] if pol else None


def assert_no_secret(result):
    text = json.dumps(result.get("msg", ""))
    assert SYN_MD5 not in text and SYN_SIMPLE not in text


def refused(result, calls, *needles):
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    for n in needles:
        assert n in result["msg"], result["msg"]
    assert NO_REQUEST in result["msg"]
    assert_no_secret(result)


def accepted(result, calls):
    assert not result.get("failed"), result.get("msg")
    assert_no_secret(result)
    return sent(calls)


def routed_have(**nv):
    base = dict(ospf="true")
    base.update(nv)
    return real_have(**base)


def disable_profile(parent):
    return OSPF_OFF if parent == h.ROUTED else h.base_for(parent, enable_ospf=False)


def run_parent(parent, profile, state, have):
    if parent == h.ROUTED:
        return F2.run(state, have, "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])
    return h.run(profile, state, have=have, parent=parent)


def have_for(parent, **profile):
    if parent == h.ROUTED:
        return real_have(**dict((table.resolve_binding(parent, k)["parent_nvpair"], v if not isinstance(v, bool)
                                 else json.dumps(v)) for k, v in profile.items()))
    return h.build_have(parent, **profile)


# ------------------------------------------------------------------ R1: reset guidance on a same-parent role default
@pytest.mark.parametrize("state", ("deleted", "overridden"))
def test_border_reset_with_ospf_on_disables_the_gate_in_the_same_reset(state):
    """D-3: the border default is int_routed_host itself and its reset sends ospf "false", so the stored tag is inert under
    the final gate: one reset, no remedy needed (test_binding_role_resets.py has the full matrix)."""
    result, calls = F2.run(state, real_have(), "border", configs=None if state == "deleted" else [])
    accepted(result, calls)
    nv = F2.nvpairs_of_reset(calls)
    assert nv["ospf"] == "false" and "ospfTag" not in nv


@pytest.mark.parametrize("state", ("deleted", "overridden"))
def test_border_reset_after_disable_is_accepted(state):
    result, calls = F2.run(state, ospf_off_have(), "border", configs=None if state == "deleted" else [])
    accepted(result, calls)


# ------------------------------------------------------------------ simple key and its encryption type
@pytest.mark.parametrize("keytype", ("0", "7"))
@pytest.mark.parametrize("with_key", (True, False))
def test_disable_with_a_stored_encryption_type_is_accepted_and_keeps_it_inert(keytype, with_key):
    have = routed_have(ospfAuthenticationKeyType=keytype, ospfAuthenticationKey=SYN_SIMPLE if with_key else "")
    result, calls = replaced(OSPF_OFF, have)
    nv = accepted(result, calls)
    assert nv["ospf"] == "false" and nv["ospfAuthenticationKey"] == ""
    assert nv["ospfAuthenticationKeyType"] == keytype, "the type configures nothing without a key: kept as stored"


@pytest.mark.parametrize("parent", (h.SUBIF, h.SVI))
def test_disable_with_a_stored_encryption_type_on_subif_and_svi(parent):
    have = h.build_have(parent, ospf_authentication_key_type="7", ospf_authentication_key=SYN_SIMPLE, **h.OSPF_CTX)
    result, calls = h.run(h.base_for(parent, enable_ospf=False), "replaced", have=have, parent=parent)
    nv = accepted(result, calls)
    assert nv["ospf"] == "false" and nv["ospfAuthenticationKey"] == "" and nv["ospfAuthenticationKeyType"] == "7"


def test_clearing_the_simple_key_with_ospf_on_keeps_the_type_inert():
    have = routed_have(ospfTag="LAB-OSPF", ospfAuthenticationKeyType="7", ospfAuthenticationKey=SYN_SIMPLE)
    result, calls = replaced(dict(OSPF_OFF, enable_ospf=True, ospf_tag="LAB-OSPF"), have)
    nv = accepted(result, calls)
    assert nv["ospf"] == "true" and nv["ospfAuthenticationKey"] == "" and nv["ospfAuthenticationKeyType"] == "7"


def test_keeping_the_simple_key_and_omitting_its_type_is_still_refused():
    have = routed_have(ospfTag="LAB-OSPF", ospfAuthenticationKeyType="7", ospfAuthenticationKey=SYN_SIMPLE)
    profile = dict(OSPF_OFF, enable_ospf=True, ospf_tag="LAB-OSPF", ospf_authentication_key=SYN_SIMPLE)
    result, calls = replaced(profile, have)
    refused(result, calls, "ospf_authentication_key_type on int_routed_host")


# ------------------------------------------------------------------ message-digest key
@pytest.mark.parametrize("parent", PARENTS)
def test_disabling_ospf_clears_the_message_digest_key(parent):
    have = have_for(parent, enable_ospf=True, ospf_tag="LAB-OSPF", ospf_area_id="0.0.0.0", enable_ospf_auth=True,
                    ospf_auth_key_id=5, ospf_auth_key=SYN_MD5)
    result, calls = run_parent(parent, disable_profile(parent), "replaced", have)
    nv = accepted(result, calls)
    assert nv["ospf"] == "false" and nv["ospfAuthentication"] == "false"
    assert nv["OSPF_AUTH_KEY"] == "" and nv["OSPF_AUTH_KEY_ID"] == "1"
    assert SYN_MD5 not in json.dumps(nv)


def test_disabling_authentication_only_clears_the_key_and_keeps_ospf():
    have = routed_have(ospfTag="LAB-OSPF", ospfAuthentication="true", OSPF_AUTH_KEY_ID="5", OSPF_AUTH_KEY=SYN_MD5)
    result, calls = replaced(dict(OSPF_OFF, enable_ospf=True, ospf_tag="LAB-OSPF"), have)
    nv = accepted(result, calls)
    assert nv["ospf"] == "true" and nv["ospfAuthentication"] == "false" and nv["OSPF_AUTH_KEY"] == ""


def test_the_disable_after_clearing_is_a_noop():
    have = routed_have(ospfAuthentication="true", OSPF_AUTH_KEY_ID="5", OSPF_AUTH_KEY=SYN_MD5)
    first, calls = replaced(OSPF_OFF, have)
    assert not first.get("failed"), first.get("msg")
    result, calls = replaced(OSPF_OFF, F2.as_have(calls))
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("state", ("deleted", "overridden"))
def test_leaf_reset_after_disable_with_leftover_authentication_is_accepted(state):
    leftover = dict(OSPF_OPTIONS_NEUTRAL, ospfAuthenticationKeyType="7", OSPF_AUTH_KEY=SYN_MD5, OSPF_AUTH_KEY_ID="5")
    have = real_have(ospf="false", **leftover)
    result, calls = F2.run(state, have, "leaf", configs=None if state == "deleted" else [])
    nv = accepted(result, calls)
    assert F2.reset_policies(calls)[0]["policy"] == "int_trunk_host"
    assert not [k for k in nv if k.upper().startswith("OSPF")], "a source-only nvPair is never written to the destination"


@pytest.mark.parametrize("state", ("deleted", "overridden"))
def test_border_reset_clears_a_leftover_message_digest_key(state):
    have = real_have(ospf="false", **dict(OSPF_OPTIONS_NEUTRAL, OSPF_AUTH_KEY=SYN_MD5))
    result, calls = F2.run(state, have, "border", configs=None if state == "deleted" else [])
    nv = accepted(result, calls)
    assert nv.get("OSPF_AUTH_KEY") == "", "same policy: key material is cleared, not kept"


# ------------------------------------------------------------------ merged: explicit disable versus omission
@pytest.mark.parametrize("parent", PARENTS)
def test_merged_explicit_disable_neutralizes_the_stored_options(parent):
    option = {h.ROUTED: ("ospf_passive_mode", "passive", "ospfPassiveMode", "noChange"),
              h.SUBIF: ("ospf_passive_mode", "passive", "ospfPassiveMode", "noChange"),
              h.SVI: ("ospf_passive_mode", "passive", "ospfPassiveMode", "noChange"),
              h.PC_L3: ("ospf_passive_mode", "passive", "ospfPassiveMode", "noChange")}[parent]
    have = have_for(parent, enable_ospf=True, ospf_tag="LAB-OSPF", ospf_area_id="0.0.0.0", ospf_cost=10,
                    enable_ospf_auth=True, ospf_auth_key_id=5, ospf_auth_key=SYN_MD5, **{option[0]: option[1]})
    result, calls = run_parent(parent, disable_profile(parent), "merged", have)
    nv = accepted(result, calls)
    assert nv["ospf"] == "false" and nv[option[2]] == option[3] and nv["ospfCost"] == ""
    assert nv["ospfAuthentication"] == "false" and nv["OSPF_AUTH_KEY"] == "" and nv["OSPF_AUTH_KEY_ID"] == "1"
    assert nv["ospfTag"] == "LAB-OSPF", "the tag has no neutral value: kept as stored, it configures nothing"


def test_merged_explicit_authentication_disable_clears_only_its_dependents():
    have = routed_have(ospfTag="LAB-OSPF", ospfPassiveMode="passive", ospfAuthentication="true",
                       OSPF_AUTH_KEY_ID="5", OSPF_AUTH_KEY=SYN_MD5)
    profile = {"mode": "routed", "enable_ospf_auth": False, "ipv4_addr": "192.0.2.17", "ipv4_mask_len": 30}
    result, calls = F2.run("merged", have, "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])
    nv = accepted(result, calls)
    assert nv["ospf"] == "true" and nv["ospfPassiveMode"] == "passive"
    assert nv["ospfAuthentication"] == "false" and nv["OSPF_AUTH_KEY"] == "" and nv["OSPF_AUTH_KEY_ID"] == "1"


def test_merged_omission_of_the_gate_still_preserves_everything():
    have = routed_have(ospfTag="LAB-OSPF", ospfPassiveMode="passive", ospfCost="10")
    profile = {"mode": "routed", "description": "only-this", "ipv4_addr": "192.0.2.17", "ipv4_mask_len": 30}
    result, calls = F2.run("merged", have, "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])
    nv = accepted(result, calls)
    assert nv["ospf"] == "true" and nv["ospfPassiveMode"] == "passive" and nv["ospfCost"] == "10"


def test_merged_explicit_disable_repeated_is_a_noop():
    have = routed_have(ospfTag="LAB-OSPF", ospfPassiveMode="passive")
    first, calls = F2.run("merged", have, "border", configs=[h.cfg(h.IF_A, OSPF_OFF, deploy=False)])
    assert not first.get("failed"), first.get("msg")
    result, calls = F2.run("merged", F2.as_have(calls), "border", configs=[h.cfg(h.IF_A, OSPF_OFF, deploy=False)])
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


# ------------------------------------------------------------------ explicit contradictions
@pytest.mark.parametrize("state", ("merged", "replaced"))
def test_an_explicit_option_while_disabling_ospf_is_refused(state):
    profile = dict(OSPF_OFF, ospf_cost=10)
    result, calls = F2.run(state, real_have(), "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])
    refused(result, calls, "ospf_cost (needs enable_ospf) on %s, parent int_routed_host" % h.IF_A)


@pytest.mark.parametrize("parent", (h.SUBIF, h.SVI))
def test_an_explicit_option_while_disabling_ospf_is_refused_on_subif_and_svi(parent):
    result, calls = h.run(h.base_for(parent, enable_ospf=False, ospf_cost=10), "replaced",
                          have=h.build_have(parent, **h.OSPF_CTX), parent=parent)
    refused(result, calls, "ospf_cost (needs enable_ospf)")


def test_an_explicit_neutral_option_while_disabling_ospf_is_accepted():
    profile = dict(OSPF_OFF, ospf_passive_mode="no_change")
    result, calls = F2.run("merged", real_have(), "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])
    nv = accepted(result, calls)
    assert nv["ospf"] == "false" and nv["ospfPassiveMode"] == "noChange"


def test_an_explicit_option_on_a_new_interface_with_ospf_off_is_refused():
    profile = dict(OSPF_OFF, ospf_cost=10)
    result, calls = F2.run("merged", [], "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])
    refused(result, calls, "ospf_cost (needs enable_ospf)")


@pytest.mark.parametrize("state", ("merged", "replaced"))
def test_an_explicit_empty_tag_while_ospf_is_enabled_is_refused(state):
    profile = dict(OSPF_OFF, enable_ospf=True, ospf_tag="")
    result, calls = F2.run(state, real_have(), "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])
    refused(result, calls, "ospf_tag (with enable_ospf enabled) on %s" % h.IF_A)


def test_an_explicit_empty_tag_under_merged_with_ospf_on_only_in_have_is_refused():
    profile = {"mode": "routed", "ospf_tag": "", "ipv4_addr": "192.0.2.17", "ipv4_mask_len": 30}
    result, calls = F2.run("merged", real_have(), "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])
    refused(result, calls, "ospf_tag (with enable_ospf enabled)")


def test_an_explicit_empty_tag_while_disabling_ospf_is_accepted():
    profile = dict(OSPF_OFF, ospf_tag="")
    result, calls = replaced(profile, real_have())
    nv = accepted(result, calls)
    assert nv["ospf"] == "false" and nv["ospfTag"] == ""


def test_an_explicit_empty_message_digest_key_with_authentication_on_is_refused():
    have = routed_have(ospfTag="LAB-OSPF", ospfAuthentication="true", OSPF_AUTH_KEY_ID="5", OSPF_AUTH_KEY=SYN_MD5)
    profile = dict(OSPF_OFF, enable_ospf=True, ospf_tag="LAB-OSPF", enable_ospf_auth=True, ospf_auth_key_id=5,
                   ospf_auth_key="")
    result, calls = replaced(profile, have)
    refused(result, calls, "ospf_auth_key (with enable_ospf_auth enabled)")


# ------------------------------------------------------------------ re-enable
def test_replaced_reenable_with_a_tag_after_disable_is_accepted():
    result, calls = replaced(dict(OSPF_OFF, enable_ospf=True, ospf_tag="NEW-TAG"), ospf_off_have())
    nv = accepted(result, calls)
    assert nv["ospf"] == "true" and nv["ospfTag"] == "NEW-TAG"


def test_merged_reenable_without_a_tag_reuses_the_stored_tag():
    """Merged preservation, documented: the tag kept by the disable is reused."""
    profile = dict(OSPF_OFF, enable_ospf=True)
    result, calls = F2.run("merged", ospf_off_have(), "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])
    nv = accepted(result, calls)
    assert nv["ospf"] == "true" and nv["ospfTag"] == FIXTURE["nvPairs"]["ospfTag"]


@pytest.mark.parametrize("state", ("merged", "replaced"))
def test_reenabling_authentication_over_a_cleared_key_needs_a_key(state):
    have = routed_have(ospfTag="LAB-OSPF", ospfAuthentication="false", OSPF_AUTH_KEY_ID="1", OSPF_AUTH_KEY="")
    profile = dict(OSPF_OFF, enable_ospf=True, ospf_tag="LAB-OSPF", enable_ospf_auth=True, ospf_auth_key_id=5)
    result, calls = F2.run(state, have, "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])
    refused(result, calls, "ospf_auth_key (with enable_ospf_auth enabled)")


def test_reenabling_authentication_with_a_new_key_is_accepted():
    have = routed_have(ospfTag="LAB-OSPF", ospfAuthentication="false", OSPF_AUTH_KEY_ID="1", OSPF_AUTH_KEY="")
    profile = dict(OSPF_OFF, enable_ospf=True, ospf_tag="LAB-OSPF", enable_ospf_auth=True, ospf_auth_key_id=5,
                   ospf_auth_key=SYN_MD5)
    result, calls = replaced(profile, have)
    nv = accepted(result, calls)
    assert nv["ospfAuthentication"] == "true" and nv["OSPF_AUTH_KEY"] == SYN_MD5


# ------------------------------------------------------------------ registry, engine and generator contract
def test_declared_dependencies_cover_the_three_parents_and_the_loopback_contract():
    for parent in PARENTS:
        rows = dict((r["parent_nvpair"], r.get("inert_when")) for r in table.BINDING_TABLE if r["parent_template"] == parent)
        assert rows["ospfTag"] == {"nvpair": "ospf", "value": "false", "required": True}
        assert rows["OSPF_AUTH_KEY"] == {"nvpair": "ospfAuthentication", "value": "false", "required": True, "clear": ""}
        assert rows["ospfAuthenticationKeyType"] == {"nvpair": "ospfAuthenticationKey", "value": ""}
        assert rows["ospfCost"] == {"nvpair": "ospf", "value": "false", "strict": True}
        assert rows["ospf"] is None and rows["OSPF_AREA_ID"] is None
    # int_loopback: the same authentication gates; the tag and the options also stay live in the default VRF.
    lo = dict((r["parent_nvpair"], r.get("inert_when")) for r in table.BINDING_TABLE if r["parent_template"] == h.LOOPBACK)
    vrf = {"nvpair": "INTF_VRF", "values": ("", "default")}
    assert lo["ospfTag"] == {"nvpair": "ospf", "value": "false", "required": True, "unless": vrf}
    assert lo["ospfCost"] == {"nvpair": "ospf", "value": "false", "strict": True, "unless": vrf}
    assert lo["OSPF_AUTH_KEY"] == {"nvpair": "ospfAuthentication", "value": "false", "required": True, "clear": ""}
    assert lo["ospfAuthenticationKeyType"] == {"nvpair": "ospfAuthenticationKey", "value": ""}
    assert lo["ospf"] is None and lo["OSPF_AREA_ID"] is None


def test_engine_plan_chains_gates_and_never_judges_an_unknown_gate():
    have = {"ospf": "true", "ospfAuthentication": "true", "OSPF_AUTH_KEY_ID": "5", "OSPF_AUTH_KEY": SYN_MD5,
            "ospfCost": "10", "ospfTag": "T"}
    writes, conflicts = engine.gie_dependency_plan("int_routed_host", {"ospf": "false"}, have, {"ospf"}, True,
                                                   "12.6.0.267", h.SUPPORTED_PATCH)
    assert writes == {"ospfAuthentication": "false", "OSPF_AUTH_KEY_ID": "1", "OSPF_AUTH_KEY": "", "ospfCost": ""}
    assert conflicts == []
    writes, conflicts = engine.gie_dependency_plan("int_routed_host", {"ospfTag": ""}, {}, {"ospfTag"}, True,
                                                   "12.6.0.267", h.SUPPORTED_PATCH)
    assert writes == {} and conflicts == [], "no gate in WANT or HAVE: not judged"
    writes, conflicts = engine.gie_dependency_plan("int_routed_host", {"ospf": "false"}, have, {"ospf"}, True,
                                                   "12.6.0.267", None)
    assert writes == {} and conflicts == [], "capability disabled: nothing is written or refused"


@pytest.mark.parametrize("nvpair, inert_when, match", [
    ("ospfCost", {"nvpair": "ospf", "value": "false", "strict": "yes"}, "marker is a boolean"),
    ("ospfTag", {"nvpair": "ospf", "value": "false", "strict": True}, "strict without a reset_wire"),
    ("ospfTag", {"nvpair": "ospf", "value": "false", "clear": "x"}, "only an empty clear"),
    ("ospfCost", {"nvpair": "ospf", "value": "false", "clear": ""}, "only an empty clear"),
    ("ospfTag", {"nvpair": "ospf", "value": "false", "other": True}, "must be a mapping"),
])
def test_generator_rejects_malformed_dependency_markers(nvpair, inert_when, match):
    generator = thin._load_generator()
    with pytest.raises(ValueError, match=match):
        generator.compile_rows(_rows_with("int_routed_host", nvpair, inert_when=inert_when))


def test_generator_rejects_a_dependency_loop():
    generator = thin._load_generator()
    rows = _rows_with("int_routed_host", "ospfAuthentication", inert_when={"nvpair": "OSPF_AUTH_KEY_ID", "value": "1"})
    with pytest.raises(ValueError, match="loops"):
        generator.compile_rows(rows)
