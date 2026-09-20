"""Retiring OSPF-auth support on the fabric loopback must not DELETE the fabric's auth.

THE DECISION BEHIND THIS FILE
    OSPF authentication on a fabric loopback is underlay authentication, and the fabric owns
    it. Read from the installed template ``int_fabric_loopback_11_1``:

        if linkStateRouting == "ospf":                       # fabric setting
            ospfAuthEnable = fabricSettings["OSPF_AUTH_ENABLE"]      # the fabric decides
            if ospfAuthEnable == "true":
                if ospfAuthKeyId == "": ospfAuthKeyId = fabricSettings["OSPF_AUTH_KEY_ID"]
                if ospfAuthKey   == "": ospfAuthKey   = fabricSettings["OSPF_AUTH_KEY"]
            if ospfAuthKeychainName:                                 # also a fabric setting
                ...
                delete ospf_interface_auth_message_digest_11_1       # overrides the interface

    The interface nvPairs were only a per-loopback override of a fabric-owned key, and a
    keychain setting silently deletes what they create. That capability is being withdrawn from
    the product, so the three bindings and their dedicated validators are removed.

THE TRAP THIS FILE EXISTS TO CATCH
    Withdrawing SUPPORT must not become DELETING CONFIGURATION.

    Those four nvPairs are listed in ``GIE_OSPF_MD_DOMAIN_NVPAIRS``, which is an EXCLUSION set:
    ``gie_have_carry_forward_nvpairs`` preserves every builder-omitted HAVE nvPair on this
    parent EXCEPT the ones in it, because the dedicated path used to own them.

    Remove the bindings and the dedicated path but leave the exclusion, and those four fields
    become orphans: nothing manages them and nothing preserves them. An operator changing a
    loopback description under ``replaced`` would blank them and switch off authentication the
    fabric is managing -- on the underlay, across the fabric.

    The fix is to take them OUT of the exclusion set, so the generic HAVE carry-forward keeps
    whatever the controller holds. The fabric owns the values; the interface simply stops
    touching them.

    ``test_the_exclusion_set_no_longer_shields_them`` fails if the exclusion is left behind.

Offline: no controller and no device.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    GIE_OSPF_MD_DOMAIN_NVPAIRS,
    GIE_READONLY_METADATA_NVPAIRS,
    gie_have_carry_forward_nvpairs,
)

PARENT = "int_fabric_loopback_11_1"

# The four nvPairs the fabric manages on a loopback. Names read from the installed template.
FABRIC_OWNED = (
    "ENABLE_OSPF_AUTH_MESSAGE_DIGEST",
    "OSPF_AUTH_KEY",
    "OSPF_AUTH_KEY_ID",
    "ospfAuthKeychainName",
)

# A loopback as the controller holds it: the fabric has authentication on, with its key.
HAVE_WITH_FABRIC_AUTH = {
    "INTF_NAME": "loopback0",
    "IP": "10.31.0.6",
    "DESC": "underlay loopback",
    "ROUTE_MAP_TAG": "12345",
    "ENABLE_OSPF_AUTH_MESSAGE_DIGEST": "true",
    "OSPF_AUTH_KEY_ID": "127",
    # Synthetic. Never a value seen on the lab: a fixture is committed, printed in
    # failures and read by anyone with the repo, so real key material must not reach it.
    "OSPF_AUTH_KEY": "0000000000000000",
    "ospfAuthKeychainName": "",
}

# What the builder emits when an operator changes only the description. None of the four
# appears, because the module no longer knows about them.
WANT_DESC_ONLY = {
    "INTF_NAME": "loopback0",
    "IP": "10.31.0.6",
    "DESC": "underlay loopback -- renamed",
}


def test_the_exclusion_set_no_longer_shields_them():
    """The retirement is incomplete until these four leave GIE_OSPF_MD_DOMAIN_NVPAIRS.

    While they are excluded, the generic carry-forward skips them -- which was correct while a
    dedicated path owned them, and is destructive once it does not.
    """
    still_excluded = sorted(set(FABRIC_OWNED) & set(GIE_OSPF_MD_DOMAIN_NVPAIRS))
    assert not still_excluded, (
        "these are excluded from the generic carry-forward but no longer owned by anything, so "
        "an unrelated loopback update would blank them: {0}".format(still_excluded)
    )


@pytest.mark.parametrize("nvpair", FABRIC_OWNED)
def test_a_description_change_preserves_the_fabric_owned_value(nvpair):
    """The behaviour the architect's condition 3 requires, asserted per field.

    An operator renaming a loopback must not switch off underlay authentication.
    """
    carried = gie_have_carry_forward_nvpairs(WANT_DESC_ONLY, HAVE_WITH_FABRIC_AUTH)
    assert nvpair in carried, (
        "{0} was not carried forward; a description change would blank it".format(nvpair)
    )
    assert carried[nvpair] == HAVE_WITH_FABRIC_AUTH[nvpair], (
        "{0} must be carried EXACTLY as the controller holds it, never defaulted".format(nvpair)
    )


def test_the_whole_authenticated_state_survives_an_unrelated_update():
    """The same thing stated once at the level that matters: nothing auth-related is lost."""
    carried = gie_have_carry_forward_nvpairs(WANT_DESC_ONLY, HAVE_WITH_FABRIC_AUTH)
    merged = dict(WANT_DESC_ONLY, **carried)
    for nvpair, value in HAVE_WITH_FABRIC_AUTH.items():
        if nvpair in WANT_DESC_ONLY:
            continue            # the operator set it deliberately
        assert merged.get(nvpair) == value, (
            "{0} changed from {1!r} to {2!r} during a description-only update".format(
                nvpair, value, merged.get(nvpair))
        )


def test_read_only_metadata_is_still_excluded():
    """The other exclusion set is unrelated to this retirement and must not be disturbed.

    Carrying POLICY_ID or FABRIC_NAME forward would send the controller its own identity
    metadata back as if it were intent.
    """
    have = dict(HAVE_WITH_FABRIC_AUTH, POLICY_ID="POLICY-36130", FABRIC_NAME="FAB1")
    carried = gie_have_carry_forward_nvpairs(WANT_DESC_ONLY, have)
    for nvpair in ("POLICY_ID", "FABRIC_NAME"):
        assert nvpair in GIE_READONLY_METADATA_NVPAIRS
        assert nvpair not in carried, "{0} must never be carried".format(nvpair)


def test_an_explicit_value_still_wins_over_the_controller():
    """Preservation is for OMITTED keys. If the builder emitted one, it is intent."""
    want = dict(WANT_DESC_ONLY, OSPF_AUTH_KEY_ID="200")
    carried = gie_have_carry_forward_nvpairs(want, HAVE_WITH_FABRIC_AUTH)
    assert "OSPF_AUTH_KEY_ID" not in carried, (
        "a key already in want must never be overwritten by the carry-forward"
    )


def test_a_loopback_without_fabric_auth_gains_nothing():
    """Preservation must not invent state. A fabric with auth off stays off."""
    have = dict(HAVE_WITH_FABRIC_AUTH,
                ENABLE_OSPF_AUTH_MESSAGE_DIGEST="false", OSPF_AUTH_KEY="", OSPF_AUTH_KEY_ID="")
    carried = gie_have_carry_forward_nvpairs(WANT_DESC_ONLY, have)
    assert carried.get("ENABLE_OSPF_AUTH_MESSAGE_DIGEST") == "false"
    assert carried.get("OSPF_AUTH_KEY") == ""
    assert carried.get("OSPF_AUTH_KEY_ID") == ""


# =====================================================================================
# THROUGH THE REAL COMPARATOR, IN ALL THREE STATES
# =====================================================================================
#
# Everything above calls gie_have_carry_forward_nvpairs directly with prepared dictionaries.
# That proves the helper's contract and nothing about whether the module reaches it: the call
# site is gated on `state == "merged"`, so emptying the exclusion set changes nothing for
# `replaced` or `overridden`.
#
# Widening the whole carry-forward to those states is NOT the fix. `replaced` means "make it
# exactly this", and preserving every omitted field there would change that meaning for every
# nvPair on the parent. What must survive is the narrow set the module no longer manages -- the
# fields the fabric owns -- and only those.

from unittest import mock                                                      # noqa: E402

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface      # noqa: E402

LOOPBACK_HAVE = {
    "INTF_NAME": "loopback0",
    "IP": "10.31.0.6",
    "V6IP": "",
    "ROUTE_MAP_TAG": "12345",
    "DESC": "underlay loopback",
    "CONF": "",
    "ADMIN_STATE": "true",
    "ENABLE_OSPF_AUTH_MESSAGE_DIGEST": "true",
    "OSPF_AUTH_KEY_ID": "127",
    "OSPF_AUTH_KEY": "0000000000000000",
    "ospfAuthKeychainName": "",
}


def _comparator(state, want_nv, have_nv):
    """Drive dcnm_intf_compare_want_and_have on a loopback, returning the payload nvPairs."""
    obj = object.__new__(dcnm_interface.DcnmIntf)
    obj.class_name = "DcnmIntf"
    obj.module = mock.Mock()
    obj.log = mock.Mock()
    obj.fabric = "FAB1"
    obj.dcnm_version = 12
    obj.ndfc_version = "12.6.0.267"
    obj.keymap = {"INTF_NAME": "name", "IP": "ipv4_addr", "DESC": "description",
                  "CONF": "cmds", "ADMIN_STATE": "admin_state",
                  "ROUTE_MAP_TAG": "route_tag", "V6IP": "ipv6_addr"}
    obj.pol_pc_member_types = {12: {}}
    obj.want = [{
        "policy": PARENT, "interfaceType": "INTERFACE_LOOPBACK", "deploy": False,
        "interfaces": [{"ifName": "loopback0", "serialNumber": "SNO", "fabricName": "FAB1",
                        "interfaceType": "INTERFACE_LOOPBACK", "nvPairs": dict(want_nv)}],
    }]
    obj.have = [{
        "policy": PARENT,
        "interfaces": [{"ifName": "loopback0", "serialNumber": "SNO",
                        "interfaceType": "INTERFACE_LOOPBACK", "nvPairs": dict(have_nv)}],
    }]
    obj.pb_input = [{"ifname": "loopback0", "sno": "SNO", "fabric": "FAB1",
                     "description": want_nv.get("DESC", "")}]
    for attr in ("diff_create", "diff_replace", "diff_delete", "diff_deploy",
                 "diff_delete_deploy", "diff_deferred", "diff_query", "changed_dict",
                 "have_all", "want_breakout", "have_breakout", "diff_debugs"):
        setattr(obj, attr, [] if attr != "changed_dict" else [{
            "merged": [], "deleted": [], "replaced": [], "overridden": [], "deploy": [],
            "query": [], "debugs": [], "deferred": [], "delete_deploy": [], "skipped": []}])
    obj._replace_have_lookup = {}
    obj._replace_pb_input_lookup = {}
    obj.dcnm_intf_compare_want_and_have(state)
    if not obj.diff_replace:
        return None
    return obj.diff_replace[0]["interfaces"][0]["nvPairs"]


@pytest.mark.parametrize("state", ["merged", "replaced", "overridden"])
@pytest.mark.parametrize("nvpair", FABRIC_OWNED)
def test_an_unrelated_loopback_update_preserves_fabric_auth_in_every_state(state, nvpair):
    """The behaviour condition 3 asks for, through the path the module actually takes.

    An operator renames a loopback. Under any state, that must not switch off underlay
    authentication -- the module no longer manages those fields, so it must not blank them
    either.
    """
    want = {"INTF_NAME": "loopback0", "IP": "10.31.0.6", "V6IP": "",
            "ROUTE_MAP_TAG": "12345", "DESC": "renamed", "CONF": "", "ADMIN_STATE": "true"}
    payload = _comparator(state, want, LOOPBACK_HAVE)
    assert payload is not None, "a description change must produce an update"
    assert payload.get(nvpair) == LOOPBACK_HAVE[nvpair], (
        "{0}: state={1} sent {2!r}, controller holds {3!r} -- withdrawing support must not "
        "delete the fabric's configuration".format(
            nvpair, state, payload.get(nvpair), LOOPBACK_HAVE[nvpair])
    )


@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_preservation_stays_narrow_and_does_not_redefine_replaced(state):
    """The guard against over-correcting.

    `replaced` means "make it exactly this". Only the fields the module stopped managing are
    preserved there; an ordinary omitted field must still be reset, or this change would have
    quietly redefined the state for every nvPair on the parent.
    """
    have = dict(LOOPBACK_HAVE, ROUTE_MAP_TAG="99999")
    want = {"INTF_NAME": "loopback0", "IP": "10.31.0.6", "V6IP": "",
            "DESC": "renamed", "CONF": "", "ADMIN_STATE": "true"}   # ROUTE_MAP_TAG omitted
    payload = _comparator(state, want, have)
    assert payload is not None
    assert payload.get("ROUTE_MAP_TAG") != "99999", (
        "an ordinary omitted field was preserved under {0}; preservation must stay scoped to "
        "the fabric-owned set".format(state)
    )


# =====================================================================================
# THE REJECTION MUST NOT LEAK THE KEY IT REJECTS
# =====================================================================================
#
# Found in review, and not by reading the message. The error text never prints the value --
# but Ansible serialises the module's arguments into `invocation.module_args` on every result,
# failures included. While ospf_auth_key was still in lo_prof_spec, its `no_log=True` registered
# the value for scrubbing as a side effect of validation. Rejecting the field earlier skips
# that, so the key reached the output in the clear.
#
# Asserting on `msg` alone would have missed it entirely, which is why these look at everything
# the module would hand back.

SYNTHETIC_KEY = "1111111111111111"


def _validate_loopback_source():
    """The body of dcnm_intf_validate_loopback_interface_input, as source."""
    import inspect
    return inspect.getsource(dcnm_interface.DcnmIntf.dcnm_intf_validate_loopback_interface_input)


def _reject_loopback(profile):
    """Run the withdrawn-key rejection, returning (fail_json kwargs, no_log_values)."""
    obj = object.__new__(dcnm_interface.DcnmIntf)
    obj.class_name = "DcnmIntf"
    obj.module = mock.Mock()
    obj.module.no_log_values = set()

    class _Fail(Exception):
        pass

    obj.module.fail_json.side_effect = _Fail
    cfg = [{"name": "lo0", "type": "lo", "switch": ["10.1.1.1"], "profile": dict(profile)}]
    try:
        obj.dcnm_intf_validate_loopback_interface_input(cfg)
    except _Fail:
        pass
    calls = obj.module.fail_json.call_args
    return (calls[1] if calls else {}), obj.module.no_log_values


def test_the_rejection_does_not_scrub_and_is_not_supposed_to():
    """Scrubbing here was the bug, not the fix. This pins that it stays out.

    An earlier version registered the key inside the rejection loop. That loop rejects on the
    FIRST withdrawn key it meets, and ospf_auth_key is the third of three, so 'key_id + key' and
    'boolean + key' leaked; it also stops at the first offending interface, so a key on a second
    interface leaked. Only the arrangement where the key was the sole offender was covered --
    which is exactly the one the mock-based test used, so it passed while three of four real
    cases leaked.

    Registration moved to __init__, over the whole config, before any dispatch. Putting it back
    here would look like defence in depth and would instead re-create a scrub whose coverage
    depends on rejection order.

    The real guarantee -- that the value never reaches the emitted result -- is measured against
    the actual serialiser in test_dcnm_intf_no_log_contract.py. It cannot be measured here: this
    file's helper mocks the module, and a mocked no_log_values accepts anything without ever
    scrubbing.
    """
    body = _validate_loopback_source()
    assert "no_log_values" not in body, (
        "the loopback rejection registers no_log values again. See the module comment on "
        "SECRET_PROFILE_KEYS for why that placement cannot work."
    )


def test_the_key_value_appears_nowhere_in_what_the_module_returns():
    """Check the whole result, not just msg. The leak was never in the message."""
    kwargs, unused_no_log_values = _reject_loopback(
        {"mode": "fabric", "ipv4_addr": "10.2.0.1", "ospf_auth_key": SYNTHETIC_KEY})
    assert SYNTHETIC_KEY not in str(kwargs), (
        "the rejected key value reached the module result: {0}".format(kwargs)
    )
    assert "ospf_auth_key" in kwargs.get("msg", ""), "the message must still name the field"
    assert "OSPF_AUTH_KEY" in kwargs.get("msg", ""), "and the fabric setting that replaces it"


def test_the_non_secret_companions_are_rejected_without_being_scrubbed():
    """Scrubbing is for key material only.

    A key ID is an identifier, not a secret, and adding it to no_log_values would blank an
    unrelated '1' anywhere else in the output -- Ansible substitutes by value, not by field.
    """
    kwargs, no_log = _reject_loopback({"mode": "fabric", "ipv4_addr": "10.2.0.1",
                                       "ospf_auth_key_id": 127})
    assert "ospf_auth_key_id" in kwargs.get("msg", "")
    assert no_log == set(), "a non-secret was registered for scrubbing: {0}".format(no_log)


def test_a_loopback_without_the_withdrawn_keys_is_not_rejected():
    """The control. Without it, a rejection that fired unconditionally would pass every case."""
    obj = object.__new__(dcnm_interface.DcnmIntf)
    obj.class_name = "DcnmIntf"
    obj.module = mock.Mock()
    obj.module.no_log_values = set()
    obj.intf_info = []
    obj.dcnm_version = 12
    cfg = [{"name": "lo0", "type": "lo", "switch": ["10.1.1.1"],
            "profile": {"mode": "fabric", "ipv4_addr": "10.2.0.1", "ipv4_mask_len": 32}}]
    obj.dcnm_intf_validate_loopback_interface_input(cfg)
    assert not obj.module.fail_json.called, "an ordinary loopback profile was rejected"


# =====================================================================================
# SHARED GUARANTEES RE-HOMED FROM THE RETIRED EXECUTION TESTS
# =====================================================================================
#
# Thirty tests in test_dcnm_intf.py exercised the withdrawn capability and went with it. Seven
# of them were not really about OSPF-MD: they used it as a VEHICLE for guarantees that belong to
# the module as a whole --
#
#     check mode issues no mutating call
#     a no-diff run issues no mutating call
#     a duplicate HAVE fails with zero mutation
#     a HAVE GET failure fails closed
#     a rejected field is rejected BEFORE any GET  (three variants)
#     a type failure never echoes the value
#
# Deleting them with the rest would have quietly dropped those. They are re-homed here onto the
# vehicle that replaced the field: the rejection of the withdrawn key. Same guarantees, a
# subject that still exists.


def test_the_rejection_happens_before_any_controller_call():
    """Re-homed from the three *_zero_gets tests.

    A rejected playbook must cost the controller nothing. If validation ran after the HAVE
    fetch, a config the module was always going to refuse would still have hit NDFC.
    """
    obj = object.__new__(dcnm_interface.DcnmIntf)
    obj.class_name = "DcnmIntf"
    obj.module = mock.Mock()
    obj.module.no_log_values = set()

    class _Fail(Exception):
        pass

    obj.module.fail_json.side_effect = _Fail
    # Any controller access would go through these; neither may be touched.
    obj.dcnm_intf_get_have = mock.Mock(side_effect=AssertionError("HAVE was fetched"))
    obj.dcnm_intf_send_message_to_dcnm = mock.Mock(
        side_effect=AssertionError("a request was sent"))

    cfg = [{"name": "lo0", "type": "lo", "switch": ["10.1.1.1"],
            "profile": {"mode": "fabric", "ipv4_addr": "10.2.0.1",
                        "ospf_auth_key": SYNTHETIC_KEY}}]
    with pytest.raises(_Fail):
        obj.dcnm_intf_validate_loopback_interface_input(cfg)

    assert not obj.dcnm_intf_get_have.called, "HAVE was fetched for a config already refused"
    assert not obj.dcnm_intf_send_message_to_dcnm.called, "a mutating call was made"


def test_the_rejection_message_never_echoes_the_value():
    """Re-homed from lo_ospfmd_type_failure_never_echoes_the_value.

    Scope is deliberately narrow: what this file can honestly measure is that the MESSAGE the
    rejection composes does not contain the value. Whether the value survives into the emitted
    result is a serialiser question, and mocking the module makes that unmeasurable here -- so
    it is asserted in test_dcnm_intf_no_log_contract.py instead, against real output.
    """
    kwargs, unused_no_log_values = _reject_loopback(
        {"mode": "fabric", "ipv4_addr": "10.2.0.1", "ospf_auth_key": SYNTHETIC_KEY})
    assert SYNTHETIC_KEY not in kwargs.get("msg", "")
    assert "ospf_auth_key" in kwargs.get("msg", ""), "the message must still name the field"


@pytest.mark.parametrize("key", sorted(dcnm_interface.RETIRED_LOOPBACK_OSPF_AUTH_KEYS))
def test_every_withdrawn_key_is_refused_not_just_the_secret(key):
    """All three, not only the one that carries key material.

    Accepting two and rejecting one would be worse than accepting all three: the playbook would
    half-apply and the operator would have no way to tell which half.
    """
    value = SYNTHETIC_KEY if key == "ospf_auth_key" else (127 if "key_id" in key else True)
    kwargs, unused_no_log_values = _reject_loopback({"mode": "fabric", "ipv4_addr": "10.2.0.1", key: value})
    assert key in kwargs.get("msg", ""), "{0} was accepted silently".format(key)


@pytest.mark.parametrize("key", dcnm_interface.OSPF_AUTH_KEYCHAIN_PROFILE_KEYS)
def test_a_keychain_spelling_is_refused_not_silently_dropped(key):
    """The keychain was never settable here, and silence is the wrong way to say so.

    lo_prof_spec does not declare these, and an undeclared profile key is DROPPED by
    validate_list_of_dicts rather than refused. So without an explicit rejection the run reports
    success, the controller never hears the key, and nothing tells the operator -- the failure
    mode the withdrawn keys above are rejected to avoid.

    This was measured, not assumed: before the rejection existed, all three spellings reached
    validate_interface_input and the module carried on.
    """
    obj = object.__new__(dcnm_interface.DcnmIntf)
    obj.class_name = "DcnmIntf"
    obj.module = mock.Mock()
    obj.module.no_log_values = set()

    class _Fail(Exception):
        pass

    obj.module.fail_json.side_effect = _Fail
    # If the rejection is lost again, validation continues past it -- so make that observable.
    obj.dcnm_intf_validate_interface_input = mock.Mock()

    cfg = [{"name": "lo0", "type": "lo", "switch": ["10.1.1.1"],
            "profile": {"mode": "fabric", "ipv4_addr": "10.2.0.1", key: "SOME-KEYCHAIN"}}]
    with pytest.raises(_Fail):
        obj.dcnm_intf_validate_loopback_interface_input(cfg)

    assert not obj.dcnm_intf_validate_interface_input.called, (
        "validation continued past the keychain key: it is being dropped, not refused"
    )
    msg = obj.module.fail_json.call_args.kwargs["msg"]
    assert key in msg and "fabric" in msg.lower()


# =====================================================================================
# THE TWO HALVES OF THE ARCHITECT'S Q1 RULING (2026-09-19)
#
# The retirement was a decision about OWNERSHIP, not about the word "loopback". On
# int_fabric_loopback_11_1 the authentication is underlay authentication that fabricSettings
# owns. int_loopback is a different template for a different object -- a user loopback is not
# part of the underlay, and its own template takes authentication from the interface fields.
#
# Both halves are asserted here because only one of them is intuitive. "Still refused on the
# fabric parent" is what anyone would check; "now accepted on the user loopback" is the half a
# regression would silently take away, and nothing else in the suite would notice.
# =====================================================================================

def _validate_with_resolved_parents(mode, profile_extra):
    """Run the loopback validator with pol_types populated, so the parent actually resolves.

    _reject_loopback above deliberately leaves them unset, which exercises the fail-closed
    path. These tests need the opposite: a resolved parent, which is the only condition under
    which the exemption can fire at all.
    """
    obj = object.__new__(dcnm_interface.DcnmIntf)
    obj.class_name = "DcnmIntf"
    obj.module = mock.Mock()
    obj.module.no_log_values = set()
    obj.dcnm_version = 12
    obj.pol_types = {12: {"lo_lo": "int_loopback",
                          "lo_fabric": "int_fabric_loopback_11_1"}}

    class _Fail(Exception):
        pass

    obj.module.fail_json.side_effect = _Fail
    profile = {"mode": mode, "ipv4_addr": "10.2.0.1", "ipv4_mask_len": 32}
    profile.update(profile_extra)
    cfg = [{"name": "lo0", "type": "lo", "switch": ["10.1.1.1"], "profile": profile}]
    rejected = False
    try:
        obj.dcnm_intf_validate_loopback_interface_input(cfg)
    except _Fail:
        rejected = True
    except Exception:
        # Validation past the rejection may fail for unrelated reasons (the spec wants fields
        # this minimal profile does not carry). That is not a rejection, and conflating the two
        # is how a test like this ends up asserting nothing.
        pass
    calls = obj.module.fail_json.call_args
    return rejected, (calls[1] if calls else {})


@pytest.mark.parametrize("key", ["ospf_auth_key_id", "ospf_auth_key",
                                 "enable_ospf_auth_message_digest"])
def test_the_fabric_parent_still_refuses_every_withdrawn_key(key):
    """Half one: nothing here reopens G6."""
    rejected, kwargs = _validate_with_resolved_parents("fabric", {key: "1"})
    assert rejected, (
        "{0} was accepted on a FABRIC loopback. The retirement stands there: authentication is "
        "underlay authentication and fabricSettings owns it.".format(key)
    )
    assert "fabric" in str(kwargs.get("msg", "")).lower()


@pytest.mark.parametrize("key,value", [("ospf_auth_key_id", 98),
                                       ("ospf_auth_key", "SYNTHETIC-NOT-A-REAL-KEY"),
                                       ("enable_ospf_auth", True)])
def test_the_user_loopback_now_accepts_its_own_authentication(key, value):
    """Half two: the ruling, made real.

    These keys are registered on int_loopback by slice 0b_23, so the exemption fires and the
    validator lets them through. Before that slice the same call was refused -- and it was
    refused CORRECTLY, because a key with no binding reaches a spec that does not declare it
    and validate_list_of_dicts drops it silently. The exemption is granted by the registry for
    exactly that reason, so the two can never be out of step.
    """
    rejected, kwargs = _validate_with_resolved_parents("lo", {key: value})
    assert not rejected, (
        "{0} was refused on a USER loopback. It is registered on int_loopback, so refusing it "
        "contradicts the binding table: {1}".format(key, kwargs.get("msg", ""))
    )


def test_the_keychain_is_refused_on_both_parents():
    """Neither parent can carry it, so neither accepts it.

    int_fabric_loopback_11_1 declares ospfAuthKeychainName but overwrites it from
    fabricSettings; int_loopback declares no keychain field at all. Scoping this rejection to
    the fabric parent alongside the other one was tried and reverted: on a user loopback the key
    would have been dropped in silence, which is the failure the rejection exists to prevent.
    """
    for mode in ("fabric", "lo"):
        rejected, kwargs = _validate_with_resolved_parents(
            mode, {"ospf_auth_keychain_name": "LLAVERO"}
        )
        assert rejected, "the keychain was accepted on mode '{0}'".format(mode)
