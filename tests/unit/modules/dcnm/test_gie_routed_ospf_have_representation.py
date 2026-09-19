"""How NDFC represents the OSPF nvPairs on read-back, and what the carry-forward does with it.

WHY THIS FILE EXISTS
    ``OSPF_COST`` is the first ``integer`` binding ever placed on the GENERIC carry-forward
    path. The table has exactly two integer bindings:

        int_fabric_loopback_11_1 :: OSPF_AUTH_KEY_ID   -> that parent has NO passthrough
                                                          binding, so it never reaches
                                                          ``gie_carry_forward_bindings``
        int_routed_host          :: OSPF_COST          -> reaches it from this slice on

    So this is not a pre-existing defect surfacing. The limitation in
    ``gie_validate_binding_value`` predates the slice, but nothing had ever exposed it: the
    registry had no integer on a generic-path parent until now.

WHAT WAS MEASURED (read-only, no mutation)
    ``GET /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface?serialNumber=<sno>`` — the
    endpoint that feeds HAVE — against Leaf-103 on NDFC 12.6.0.267. 63 ``int_routed_host``
    interfaces came back in TWO shapes:

      * 62 interfaces, 17-18 nvPairs: every OSPF key ABSENT.
      * Ethernet1/5, 83 nvPairs: every OSPF key present, every value a ``str``.

    Exact observed values on Ethernet1/5, reproduced in ``ROUTED_HAVE_FULL`` below:

        ENABLE_OSPF   'false'      OSPF_TAG   ''      OSPF_AREA_ID  '0.0.0.0'
        OSPF_COST     ''           IPV4_ACL_IN ''     DISABLE_LLDP_TRANSMIT 'false'

    NDFC returns every nvPair as a string. No native integer, no ``null``. The fixtures here
    are a sanitized minimum derived from those responses -- presence and types preserved
    exactly, the other 77 nvPairs of the full record dropped.

    NOT MEASURED, deliberately: what NDFC does when it RECEIVES ``""`` in OSPF_COST. That is
    the withdrawal contract and it is characterized, not asserted -- see the last section.

THE SEPARATION THESE TESTS PIN
    Three contracts that must not collapse into one:

        input        a valid integer the operator writes
        HAVE         the controller's representation: string, empty, or absent
        withdrawal   the operation that removes a configured cost

    Accepting ``""`` FROM the controller does not authorize ``""`` AS input, and neither
    authorizes deleting anything. ``test_an_empty_string_is_still_rejected_as_operator_input``
    is the guard on that.

NO MODULE WIRING WAS NEEDED FOR THIS SLICE
    An earlier draft of this file claimed the four keys were unwired. That was wrong, and the
    mistake is worth recording because it is easy to repeat: grepping ``dcnm_interface.py`` for
    a literal ``"OSPF_COST"`` finds nothing, which looks like a missing entry. The wiring is
    generated, not written:

        dcnm_interface.py:2330   self.keymap.update(gie_nvpair_keymap())
        dcnm_interface.py:3863   gie_extend_prof_spec(eth_prof_spec_routed_host, ...)

    Both derive from the binding table, so a new row lands in the keymap and the routed arg
    spec by itself. ``gie_nvpair_keymap()`` returns all four. The five suite tests that failed
    after regeneration were stale inventory expectations (14 keys where there are now 18), not
    evidence of missing integration -- they are updated alongside this file.

    ``ROUTED_KEYMAP`` below is therefore a faithful local copy, not a stand-in for something
    absent. The defect asserted here does not depend on it either way: with every OSPF key
    removed from the keymap the abort still happens, because the carry-forward reads the
    binding table and HAVE, never the keymap.

Offline: no controller and no device.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    BINDING_TABLE,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    GieBindingError,
    gie_carry_forward_bindings,
    gie_validate_binding_value,
)
from .test_dcnm_intf_loopback_carry_forward import (
    FAB,
    SNO,
    _instance,
    _payload_nv,
    _public_nv,
)

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
    "ENABLE_OSPF": "false",
    "OSPF_TAG": "",
    "OSPF_AREA_ID": "0.0.0.0",
    "OSPF_COST": "",
    "IPV4_ACL_IN": "",
    "DISABLE_LLDP_TRANSMIT": "false",
}

ROUTED_KEYMAP = {
    "INTF_NAME": "name", "DESC": "description", "CONF": "cmds",
    "ADMIN_STATE": "admin_state", "SPEED": "speed", "MTU": "mtu",
    "INTF_VRF": "vrf", "IP": "ipv4_addr", "PREFIX": "ipv4_mask_len",
    "ENABLE_OSPF": "enable_ospf", "OSPF_TAG": "ospf_tag",
    "OSPF_AREA_ID": "ospf_area_id", "OSPF_COST": "ospf_cost",
    "IPV4_ACL_IN": "ipv4_acl_in", "DISABLE_LLDP_TRANSMIT": "disable_lldp_transmit",
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
    assert exposed == [
        ("int_loopback", "OSPF_AUTH_KEY_ID"),
        ("int_loopback", "OSPF_COST"),
        ("int_loopback", "OSPF_DEAD_INTERVAL"),
        ("int_loopback", "OSPF_HELLO_INTERVAL"),
        ("int_loopback", "OSPF_PRIORITY"),
        ("int_loopback", "OSPF_RETRANSMIT_INTERVAL"),
        ("int_loopback", "OSPF_TRANSMIT_DELAY"),
        ("int_routed_host", "OSPF_AUTH_KEY_ID"),
        ("int_routed_host", "OSPF_COST"),
        ("int_routed_host", "OSPF_DEAD_INTERVAL"),
        ("int_routed_host", "OSPF_HELLO_INTERVAL"),
        ("int_routed_host", "OSPF_PRIORITY"),
        ("int_routed_host", "OSPF_TRANSMIT_DELAY"),
        # The six BFD intervals, committed 2026-09-19. Reviewed individually, not generated
        # into this list: each was read off the installed template (tx and min_rx 50-999,
        # multiplier 1-50) and takes the same exemption for the same measured reason -- NDFC
        # hands them back as strings. They are also the first bindings here with a narrow
        # maximum, which is what exposed the flat sample value in test_gie_mechanism_contract.
        ("int_subif", "BFD_MIN_RX_INTERVAL"),
        ("int_subif", "BFD_MULTIPLIER"),
        ("int_subif", "BFD_TX_INTERVAL"),
        ("int_subif", "OSPF_AUTH_KEY_ID"),
        ("int_subif", "OSPF_COST"),
        ("int_subif", "OSPF_DEAD_INTERVAL"),
        ("int_subif", "OSPF_HELLO_INTERVAL"),
        ("int_subif", "OSPF_PRIORITY"),
        ("int_subif", "OSPF_RETRANSMIT_INTERVAL"),
        ("int_subif", "OSPF_TRANSMIT_DELAY"),
        ("int_vlan", "BFD_MIN_RX_INTERVAL"),
        ("int_vlan", "BFD_MULTIPLIER"),
        ("int_vlan", "BFD_TX_INTERVAL"),
        ("int_vlan", "OSPF_AUTH_KEY_ID"),
        ("int_vlan", "OSPF_COST"),
        ("int_vlan", "OSPF_DEAD_INTERVAL"),
        ("int_vlan", "OSPF_HELLO_INTERVAL"),
        ("int_vlan", "OSPF_PRIORITY"),
        ("int_vlan", "OSPF_RETRANSMIT_INTERVAL"),
        ("int_vlan", "OSPF_TRANSMIT_DELAY"),
    ], "an integer binding reached the generic carry-forward without being reviewed here"

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
    for nvpair in ("ENABLE_OSPF", "OSPF_TAG", "OSPF_AREA_ID", "OSPF_COST"):
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
        for nvpair in ("OSPF_COST", "OSPF_TAG", "ENABLE_OSPF", "OSPF_AREA_ID"):
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
    want_nv["OSPF_TAG"] = "WP98"
    s.want = [_routed_want(want_nv)]
    have = dict(ROUTED_BUILDER_NV, **dict(ROUTED_HAVE_FULL, OSPF_TAG="OLD"))
    have.pop("OSPF_COST")                          # isolate from the defect above
    s.have = _routed_have(have)
    s.pb_input = [_routed_pb(ospf_tag="WP98", description="changed")]
    _run(s)
    payload = _payload_nv(s)
    assert payload is not None
    assert payload["OSPF_TAG"] == "WP98", "the explicit value must win over HAVE"


def test_an_explicit_cost_is_not_overwritten_by_have():
    """The precedence test on the problematic binding itself.

    The tag case above cannot exercise this: it is a plain string, so it never reaches the
    rejection. Here the operator DOES supply a cost, so the carry-forward must skip the key
    entirely -- the value never goes through the HAVE path, and the abort must not occur even
    before the fix. That is why this is not an xfail.
    """
    s = _routed_instance()
    want_nv = dict(ROUTED_BUILDER_NV, DESC="changed")
    want_nv["OSPF_COST"] = "100"                   # builder-emitted wire form
    s.want = [_routed_want(want_nv)]
    s.have = _routed_have(dict(ROUTED_BUILDER_NV, **ROUTED_HAVE_FULL))
    s.pb_input = [_routed_pb(ospf_cost=100, description="changed")]
    _run(s)
    payload = _payload_nv(s)
    assert payload is not None
    assert payload["OSPF_COST"] == "100", "the explicit cost must win over the HAVE value"


def test_a_carried_value_is_not_reported_as_a_requested_change():
    """Transport preservation must not manufacture a diff the operator did not ask for."""
    s = _routed_instance()
    s.want = [_routed_want(dict(ROUTED_BUILDER_NV, DESC="changed"))]
    have = dict(ROUTED_BUILDER_NV, **dict(ROUTED_HAVE_FULL, OSPF_TAG="WP98"))
    have.pop("OSPF_COST")                          # isolate from the defect above
    s.have = _routed_have(have)
    s.pb_input = [_routed_pb(description="changed")]
    _run(s)
    public = _public_nv(s)
    if public is not None:
        assert "OSPF_TAG" not in public, "a carried value is not a requested change"


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
    have.pop("OSPF_COST")                          # isolate from the defect above
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
    want_nv["ENABLE_OSPF"] = "false"
    s.want = [_routed_want(want_nv)]
    s.have = _routed_have(dict(ROUTED_BUILDER_NV, **dict(ROUTED_HAVE_FULL,
                                                         ENABLE_OSPF="true",
                                                         OSPF_TAG="WP98",
                                                         OSPF_COST="100")))
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
    assert payload.get("ENABLE_OSPF") == "false"
    assert payload.get("OSPF_COST") == "100", (
        "the omitted cost is expected to be carried forward verbatim; if this changed, the "
        "withdrawal characterization above is stale and must be re-measured"
    )
