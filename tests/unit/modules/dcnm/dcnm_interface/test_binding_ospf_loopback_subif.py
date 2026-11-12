"""OSPF on loopbacks, subinterfaces and SVIs, including authentication and SMU 017 modes."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import inspect
import json
import os
import pytest
import re

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_carry_forward_bindings
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_contribute_nvpairs
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_invalid_parent_key
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_validate_binding_value
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_withdrawal_action
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GieBindingError
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_ENABLED_PATCH_VERSIONS
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_WITHDRAW_NONE
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_WITHDRAW_RESET
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_WITHDRAW_UNCLASSIFIED
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_WITHDRAW_UNSUPPORTED
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding
from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table as table
from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine as engine
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_OSPF_MD_DOMAIN_NVPAIRS
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_READONLY_METADATA_NVPAIRS
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_have_carry_forward_nvpairs
from unittest import mock
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_OSPF_BOOLEAN_ALIASES
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_normalize_ospf_aliases
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import BINDING_TABLE
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_guarded_keys

from .helpers import binding_harness as h
from .helpers import registry_generator as thin
from .helpers.fixture_cases import load_case


# ====================================================================================================
# Formerly test_gie_ospf_auth_lifecycle.py
# The authentication lot through its whole life: apply, repeat, rotate, omit, withdraw.
#
# Offline, at the engine boundary. What a stage means here:
#
#   APPLY     an explicit value reaches the parent nvPair, in wire form
#   REPEAT    the same input twice produces the same payload -- no key is re-pushed for having
#             been read back as a string
#   ROTATE    changing only the key changes only the key
#   OMIT      an omitted field is not emitted, and the controller's value is carried forward
#             rather than blanked
#   WITHDRAW  the shape a removal takes, and what it must NOT do silently
#
# Every stage runs against all three parents, because the lot is one slice for three parents and
# that shortcut is only sound while they behave identically.
#
# NOT LIVE TESTED. No controller or switch is contacted. What is
# asserted is what the module hands the transport -- the device-level half belongs to the live
# cycles, per parent and per state.
# ====================================================================================================
# int_l3_port_channel joined with slice 0b_40 (the int_routed_host contracts on identical 017 declarations).
PARENTS = ["int_routed_host", "int_subif", "int_vlan", "int_l3_port_channel"]
NDFC = "12.6.0.267"
# Declared explicitly for this file's one engine entry point, _emit.
PATCH = sorted(GIE_ENABLED_PATCH_VERSIONS)[0]

KEY_A = "3DES-KEY-ALPHA"
KEY_B = "3DES-KEY-BRAVO"

# A complete, valid authentication intent. Written once: every stage below is a delta on it, so
# a stage that fails points at the delta and not at the setup.
AUTH = {
    "enable_ospf_auth": True,
    "ospf_auth_key_id": 7,
    "ospf_auth_key": KEY_A,
    "ospf_authentication_key_type": "3",
    "ospf_authentication_key": "AUTHENTICATION-KEY-ALPHA",
}
AUTH_NVPAIRS = {
    "ospfAuthentication": "true",
    "OSPF_AUTH_KEY_ID": "7",
    "OSPF_AUTH_KEY": KEY_A,
    "ospfAuthenticationKeyType": "3",
    "ospfAuthenticationKey": "AUTHENTICATION-KEY-ALPHA",
}


def _emit(parent, profile):
    nvpairs, error = gie_contribute_nvpairs(parent, profile, NDFC, PATCH)
    assert error is None, error
    return nvpairs


# =====================================================================================
# APPLY
# =====================================================================================
@pytest.mark.parametrize("parent", PARENTS)
def test_apply_puts_every_field_on_the_wire_in_controller_form(parent):
    emitted = _emit(parent, dict(AUTH))
    for nvpair, expected in AUTH_NVPAIRS.items():
        assert emitted[nvpair] == expected, nvpair
        assert type(emitted[nvpair]) is str, (  # pylint: disable=unidiomatic-typecheck
            "{0} left as a native Python value; nvPairs is a string-valued map and a native "
            "bool or int never converges against what NDFC returns".format(nvpair)
        )


@pytest.mark.parametrize("parent", PARENTS)
def test_apply_emits_the_authentication_family_and_nothing_else(parent):
    """An OSPF-auth intent must not drag unrelated OSPF nvPairs along with it."""
    emitted = _emit(parent, dict(AUTH))
    assert set(emitted) == set(AUTH_NVPAIRS), (
        "extra nvPairs were emitted for an authentication-only profile: {0}".format(
            sorted(set(emitted) - set(AUTH_NVPAIRS)))
    )


@pytest.mark.parametrize("parent", PARENTS)
def test_the_boolean_gate_travels_as_a_string_not_a_python_bool(parent):
    """ENABLE_OSPF_AUTH is the gate; if it never converges the whole family re-pushes."""
    assert _emit(parent, {"enable_ospf_auth": True})["ospfAuthentication"] == "true"
    assert _emit(parent, {"enable_ospf_auth": False})["ospfAuthentication"] == "false"


# =====================================================================================
# REPEAT
# =====================================================================================
@pytest.mark.parametrize("parent", PARENTS)
def test_repeat_produces_a_byte_identical_payload(parent):
    assert _emit(parent, dict(AUTH)) == _emit(parent, dict(AUTH))


@pytest.mark.parametrize("parent", PARENTS)
def test_the_controller_string_form_of_every_field_is_accepted_back(parent):
    """The HAVE side of repetition.

    NDFC returns every nvPair as a string: "true", "7", "3". Those come back through the
    comparator, and a validator that only accepted native types would reject the controller's
    own answer -- reporting a change on every run for a config nobody touched.
    """
    for key, wire in (("enable_ospf_auth", "true"), ("ospf_auth_key_id", "7"),
                      ("ospf_authentication_key_type", "3"), ("ospf_auth_key", KEY_A)):
        gie_validate_binding_value(parent, key, wire, value_source="have")


# =====================================================================================
# ROTATE
# =====================================================================================
@pytest.mark.parametrize("parent", PARENTS)
def test_rotating_the_key_changes_that_field_and_only_that_field(parent):
    before = _emit(parent, dict(AUTH))
    after = _emit(parent, dict(AUTH, ospf_auth_key=KEY_B))
    assert after["OSPF_AUTH_KEY"] == KEY_B
    moved = {k for k in before if before[k] != after[k]}
    assert moved == {"OSPF_AUTH_KEY"}, "rotation also moved {0}".format(moved - {"OSPF_AUTH_KEY"})


@pytest.mark.parametrize("parent", PARENTS)
def test_rotating_the_key_id_alongside_the_key_moves_exactly_those_two(parent):
    """The realistic rotation: a new key under a new id, with the old pair still on the device."""
    before = _emit(parent, dict(AUTH))
    after = _emit(parent, dict(AUTH, ospf_auth_key=KEY_B, ospf_auth_key_id=8))
    assert (after["OSPF_AUTH_KEY"], after["OSPF_AUTH_KEY_ID"]) == (KEY_B, "8")
    assert {k for k in before if before[k] != after[k]} == {"OSPF_AUTH_KEY", "OSPF_AUTH_KEY_ID"}


@pytest.mark.parametrize("parent", PARENTS)
def test_a_key_id_outside_the_template_range_is_refused_before_anything_is_sent(parent):
    """0-255 comes from the template. A rotation typo must fail, not truncate."""
    for bad in (-1, 256):
        with pytest.raises(GieBindingError):
            gie_validate_binding_value(parent, "ospf_auth_key_id", bad,
                                       value_source="explicit")


# =====================================================================================
# OMIT
# =====================================================================================
@pytest.mark.parametrize("parent", PARENTS)
@pytest.mark.parametrize("key", sorted(AUTH))
def test_an_omitted_field_is_not_emitted(parent, key):
    partial = {k: v for k, v in AUTH.items() if k != key}
    assert resolve_binding(parent, key)["parent_nvpair"] not in _emit(parent, partial)


@pytest.mark.parametrize("parent", PARENTS)
@pytest.mark.parametrize("key", sorted(AUTH))
def test_an_omitted_field_is_carried_forward_from_the_controller(parent, key):
    """Omission means "leave it alone", and the module's payload is SPARSE.

    Without carry-forward NDFC re-applies the template over the fields the payload does not
    mention, which resets them to template defaults. For this family that means silently
    removing authentication from an interface whose playbook simply did not mention it -- the
    fabric-loopback drift, repeated on a parent where the fabric cannot put it back.
    """
    carried = {b["profile_key"] for b in gie_carry_forward_bindings(parent)}
    assert key in carried, (
        "omitting {0} on {1} would let NDFC reset it".format(key, parent)
    )


@pytest.mark.parametrize("parent", PARENTS)
def test_omitting_everything_emits_nothing(parent):
    assert _emit(parent, {}) == {}


# =====================================================================================
# WITHDRAW
# =====================================================================================
@pytest.mark.parametrize("parent", PARENTS)
def test_disabling_authentication_is_an_explicit_false_not_an_omission(parent):
    """The two are different intents and the module must not conflate them.

    Omitting the gate means "leave authentication as it is". Setting it false means "turn it
    off". A module that treated the first as the second would disable authentication on every
    interface whose playbook happened not to mention it.
    """
    assert "ospfAuthentication" not in _emit(parent, {"ospf_auth_key_id": 7})
    assert _emit(parent, {"enable_ospf_auth": False})["ospfAuthentication"] == "false"


@pytest.mark.parametrize("parent", PARENTS)
def test_clearing_a_key_travels_as_an_empty_string(parent):
    """"" is how a string nvPair is CLEARED, so it must transport like any other value.

    Same precedent as ACL_FILTER, measured on 12.6.0.267: the empty string is accepted, stored,
    and withdraws the line from the device on deploy. Blocking it would make the key settable
    and never clearable.
    """
    emitted = _emit(parent, {"ospf_auth_key": "", "ospf_authentication_key": ""})
    assert emitted["OSPF_AUTH_KEY"] == ""
    assert emitted["ospfAuthenticationKey"] == ""


# What withdrawal does to each field when it is OMITTED under replaced / overridden. Decided by the engine from the compiled
# `reset_wire` and `default_template` (gie_withdrawal_action), measured here on the shipped table. Three fields have a verified
# reset and are withdrawn with it. The other two have none and FAIL CLOSED (never a silent success), so no key is ever blanked
# by guesswork. This replaces an older test that pinned the registry note `removal_semantics: unresolved` by reading a YAML file
# outside the collection (and skipped when it was not found): that note is registry-only documentation, the engine does not read
# it, and the behaviour it described is now defined, and tested, by the withdrawal contract below.
WITHDRAWAL_CONTRACT = [
    # (public key, a configured HAVE value, expected action, expected wire value)
    ("enable_ospf_auth", "true", GIE_WITHDRAW_RESET, "false"),
    ("ospf_auth_key_id", "7", GIE_WITHDRAW_RESET, "1"),
    ("ospf_authentication_key", KEY_A, GIE_WITHDRAW_RESET, ""),
    ("ospf_authentication_key_type", "7", GIE_WITHDRAW_UNSUPPORTED, None),
    ("ospf_auth_key", KEY_A, GIE_WITHDRAW_UNCLASSIFIED, None),
]


@pytest.mark.parametrize("parent", PARENTS)
@pytest.mark.parametrize("key, have, action, wire", WITHDRAWAL_CONTRACT)
def test_omitting_a_configured_field_follows_its_registered_reset_or_fails_closed(parent, key, have, action, wire):
    assert gie_withdrawal_action(parent, key, have, NDFC, PATCH) == (action, wire)


@pytest.mark.parametrize("parent", PARENTS)
def test_a_field_already_at_its_reset_has_nothing_to_withdraw(parent):
    assert gie_withdrawal_action(parent, "enable_ospf_auth", "false", NDFC, PATCH) == (GIE_WITHDRAW_NONE, None)
    assert gie_withdrawal_action(parent, "ospf_auth_key_id", "1", NDFC, PATCH) == (GIE_WITHDRAW_NONE, None)
    assert gie_withdrawal_action(parent, "ospf_authentication_key", "", NDFC, PATCH) == (GIE_WITHDRAW_NONE, None)


# =====================================================================================
# THE GUARD — the same key on a parent that does not declare it
# =====================================================================================
@pytest.mark.parametrize("key", sorted(AUTH))
def test_an_authentication_key_on_an_unrelated_parent_is_refused(key):
    """int_trunk_host has no OSPF at all. Accepting the key there would drop it in silence.

    This is the guard the withdrawn loopback validator used to own. Nothing else owns it now.
    """
    assert gie_invalid_parent_key("int_trunk_host", {key: "whatever"}) == key


# ====================================================================================================
# Formerly test_gie_loopback_ospf_withdrawal.py
# Disabling OSPF and withdrawing OSPF authentication on a loopback (int_loopback).
#
# NaC renders `ospf_tag`, the area, the options and the authentication keys only while `enable_ospf` is true, and the
# message-digest key ID and key only while `enable_ospf_auth` is true. A disable therefore omits the stored tag, and an
# authentication withdrawal omits the stored key. Without dependent-field rules both were refused before any request.
#
# What int_loopback does with those fields (installed body for SMU 4.3.1.0175006017):
#   * configureOspf = ospf == "true" or (INTF_VRF is the default VRF and the fabric underlay is OSPF). Outside the default
#     VRF, OSPF off renders no OSPF child, and the template refuses an OSPF option with OSPF off. In the default VRF the
#     loopback stays in the underlay process under the stored tag (falling back to the fabric tag when it is empty), so
#     the tag and the options stay live there. A disable cannot remove that underlay line and is not asked to.
#   * The message-digest key ID and key are required and rendered only while ospfAuthentication is "true", and the
#     simple-key encryption type is used only with a non-empty simple key, in every VRF.
#
# So the tag and the options are inert with OSPF off except in the default VRF (`inert_when ... unless INTF_VRF`), and the
# authentication rows follow the same single gates as int_routed_host. In the default VRF a disable that omits a stored
# tag is still refused; stating the tag is the supported direct form.
#
# The HAVE is a real NDFC 12.6.0.267 interface read (fixtures/routing_have_cases.json#dcnm_intf_loopback_ospf_have); the default-VRF HAVE
# changes only INTF_VRF. Profiles are the shapes NaC renders. Real main() through helpers/binding_harness; assertions are
# on the captured request. Synthetic secrets only.
# ====================================================================================================
FIXTURE = load_case("dcnm_intf_loopback_ospf_have")
VRF = FIXTURE["nvPairs"]["INTF_VRF"]
TAG = FIXTURE["nvPairs"]["ospfTag"]
SYN_MD5 = "SYNTH-MD5-KEY-NOT-REAL-0003"
SYN_SIMPLE = "SYNTH-SIMPLE-NOT-REAL-04"
WRITE_PATHS = ["POST interface/modify", "POST globalInterface/deploy"]
IFNAME = "Loopback" + h.IF_LO[len("loopback"):]     # the module sends the canonical name
OPTIONS_NEUTRAL = {
    "ospfAdvertiseSubnet": "false", "ospfAuthentication": "false", "ospfAuthenticationKey": "", "ospfBfdMode": "noChange",
    "ospfCost": "", "ospfDeadInterval": "", "ospfHelloInterval": "", "ospfMtuIgnore": "false",
    "ospfNetworkType": "noChange", "ospfPriority": "", "ospfRetransmitInterval": "", "ospfShutdown": "false",
    "ospfTransmitDelay": "",
}


def have(vrf=VRF, **nv):
    pairs = copy.deepcopy(FIXTURE["nvPairs"])
    pairs["INTF_VRF"] = vrf
    pairs.update(nv)
    return [{"policy": "int_loopback", "interfaces": [{"serialNumber": h.SERIAL, "ifName": h.IF_LO, "fabricName": h.FABRIC,
                                                       "interfaceType": "INTERFACE_LOOPBACK", "nvPairs": pairs}]}]


def base(vrf=VRF):
    return {"mode": "lo", "int_vrf": vrf, "description": FIXTURE["nvPairs"]["DESC"], "admin_state": True,
            "ipv4_addr": FIXTURE["nvPairs"]["IP"], "enable_pim_sparse": False, "cmds": ""}


def ospf_on(vrf=VRF, **extra):
    """The NaC profile of an OSPF-enabled loopback (authentication off, simple-key type at its default)."""
    p = base(vrf)
    p.update(enable_ospf=True, ospf_tag=TAG, ospf_area_id=FIXTURE["nvPairs"]["OSPF_AREA_ID"], enable_ospf_auth=False,
             ospf_authentication_key_type="3", ospf_advertise_subnet=False, ospf_bfd_mode="enable", ospf_mtu_ignore=False,
             ospf_network_type="no_change", ospf_shutdown=False)
    p.update(extra)
    return p


def ospf_off(vrf=VRF):
    """The NaC profile of a disable: enable_ospf false and no other OSPF key."""
    return dict(base(vrf), enable_ospf=False)


def md5_have(vrf=VRF):
    return have(vrf, ospfAuthentication="true", OSPF_AUTH_KEY_ID="5", OSPF_AUTH_KEY=SYN_MD5)


def run(profile, state="replaced", hv=None):
    return h.run(profile, state, have=hv, parent=h.LOOPBACK)


def sent(calls):
    """The single int_loopback interface entry of the request, with its policy."""
    pols = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], pols)
    assert len(pols) == 1 and pols[0]["policy"] == "int_loopback", pols
    assert len(pols[0]["interfaces"]) == 1
    intf = pols[0]["interfaces"][0]
    assert (intf["ifName"], intf["serialNumber"]) == (IFNAME, h.SERIAL)
    return intf["nvPairs"]


def paths(calls):
    return ["%s %s" % (c["method"], c["path"].split("/rest/")[-1].split("?")[0]) for c in h.writes(calls)]


def as_have(calls):
    nv = sent(calls)
    return [{"policy": "int_loopback", "interfaces": [{"serialNumber": h.SERIAL, "ifName": h.IF_LO, "fabricName": h.FABRIC,
                                                       "interfaceType": "INTERFACE_LOOPBACK", "nvPairs": copy.deepcopy(nv)}]}]


def accepted(result, calls):
    assert not result.get("failed"), result.get("msg")
    assert paths(calls) == WRITE_PATHS
    return sent(calls)


def refused(result, calls, *fields):
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    for f in fields:
        assert "%s on int_loopback" % f in result["msg"]
    for s in (SYN_MD5, SYN_SIMPLE):
        assert s not in result["msg"]
    return result["msg"]


# ------------------------------------------------------------------ non-default VRF: OSPF off makes the loopback leave OSPF
def test_nac_disable_is_accepted_and_keeps_the_inert_tag():
    nv = accepted(*run(ospf_off(), hv=have()))
    assert nv["ospf"] == "false" and nv["INTF_VRF"] == VRF
    assert nv["ospfTag"] == TAG, "the stored tag is kept, neither withdrawn nor replaced by an invented value"
    assert nv["OSPF_AREA_ID"] == "0.0.0.0" and nv["OSPF_AUTH_KEY_ID"] == "1" and nv["OSPF_AUTH_KEY"] == ""
    assert dict((k, nv[k]) for k in OPTIONS_NEUTRAL) == OPTIONS_NEUTRAL, "the template refuses options with OSPF off"


def test_the_same_disable_again_is_a_module_noop():
    _r, calls = run(ospf_off(), hv=have())
    result, calls = run(ospf_off(), hv=as_have(calls))
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


def test_unchanged_ospf_on_profile_is_a_noop():
    result, calls = run(ospf_on(), hv=have())
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


def test_merged_explicit_disable_neutralizes_the_options_and_keeps_the_tag():
    nv = accepted(*run(ospf_off(), "merged", hv=have()))
    assert nv["ospf"] == "false" and nv["ospfTag"] == TAG
    assert nv["ospfBfdMode"] == "noChange", "a stored option would make the template refuse OSPF off"
    assert nv["OSPF_AREA_ID"] == FIXTURE["nvPairs"]["OSPF_AREA_ID"], "merged keeps what it is not asked to change"


def test_merged_omission_preserves_ospf():
    nv = accepted(*run(dict(base(), description="changed"), "merged", hv=have()))
    assert (nv["ospf"], nv["ospfTag"], nv["ospfBfdMode"], nv["DESC"]) == ("true", TAG, "enable", "changed")


def test_enable_with_a_new_tag_after_a_disable():
    off = have(ospf="false", OSPF_AREA_ID="0.0.0.0", ospfBfdMode="noChange")
    nv = accepted(*run(ospf_on(ospf_tag="LAB-OSPF-2"), hv=off))
    assert (nv["ospf"], nv["ospfTag"], nv["ospfBfdMode"]) == ("true", "LAB-OSPF-2", "enable")


def test_enable_without_a_tag_over_a_stored_tag_is_refused():
    off = have(ospf="false", OSPF_AREA_ID="0.0.0.0", ospfBfdMode="noChange")
    refused(*run(dict((k, v) for k, v in ospf_on().items() if k != "ospf_tag"), hv=off), "ospf_tag")


def test_enable_with_an_empty_tag_is_refused():
    off = have(ospf="false", ospfTag="", OSPF_AREA_ID="0.0.0.0", ospfBfdMode="noChange")
    result, calls = run(ospf_on(ospf_tag=""), hv=off)
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("vrf", (VRF, "default"))
def test_md5_enable_and_key_id_change(vrf):
    nv = accepted(*run(ospf_on(vrf, enable_ospf_auth=True, ospf_auth_key_id=5, ospf_auth_key=SYN_MD5), hv=have(vrf)))
    assert (nv["ospfAuthentication"], nv["OSPF_AUTH_KEY_ID"], nv["OSPF_AUTH_KEY"]) == ("true", "5", SYN_MD5)
    nv = accepted(*run(ospf_on(vrf, enable_ospf_auth=True, ospf_auth_key_id=6, ospf_auth_key=SYN_MD5), hv=md5_have(vrf)))
    assert (nv["ospfAuthentication"], nv["OSPF_AUTH_KEY_ID"], nv["OSPF_AUTH_KEY"]) == ("true", "6", SYN_MD5)


@pytest.mark.parametrize("vrf", (VRF, "default"))
def test_md5_withdrawal_with_ospf_kept_clears_the_key(vrf):
    nv = accepted(*run(ospf_on(vrf), hv=md5_have(vrf)))
    assert (nv["ospf"], nv["ospfTag"]) == ("true", TAG)
    assert (nv["ospfAuthentication"], nv["OSPF_AUTH_KEY_ID"], nv["OSPF_AUTH_KEY"]) == ("false", "1", "")


@pytest.mark.parametrize("vrf", (VRF, "default"))
def test_md5_withdrawal_again_is_a_module_noop(vrf):
    _r, calls = run(ospf_on(vrf), hv=md5_have(vrf))
    result, calls = run(ospf_on(vrf), hv=as_have(calls))
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("profile, hv", (
    (ospf_on(enable_ospf_auth=True, ospf_auth_key_id=5, ospf_auth_key=SYN_MD5), have()),
    (ospf_on(), md5_have()),
    (ospf_off(), md5_have()),
), ids=("enable", "withdraw", "disable"))
def test_printed_result_never_carries_the_key(profile, hv):
    """What Ansible prints (real result formatting, no_log applied): the key never appears."""
    out, calls = h.emit_real_result([h.cfg_for(h.LOOPBACK, profile)], "replaced", have=hv)
    assert out and SYN_MD5 not in out
    assert '"failed": true' not in out


def test_disable_with_md5_configured_clears_the_key():
    nv = accepted(*run(ospf_off(), hv=md5_have()))
    assert (nv["ospf"], nv["ospfTag"]) == ("false", TAG)
    assert (nv["ospfAuthentication"], nv["OSPF_AUTH_KEY_ID"], nv["OSPF_AUTH_KEY"]) == ("false", "1", "")


@pytest.mark.parametrize("vrf", (VRF, "default"))
def test_simple_key_withdrawal_with_ospf_kept(vrf):
    nv = accepted(*run(ospf_on(vrf), hv=have(vrf, ospfAuthenticationKey=SYN_SIMPLE, ospfAuthenticationKeyType="7")))
    assert (nv["ospf"], nv["ospfAuthenticationKey"], nv["ospfAuthenticationKeyType"]) == ("true", "", "3")


def test_disable_with_a_type_7_simple_key():
    nv = accepted(*run(ospf_off(), hv=have(ospfAuthenticationKey=SYN_SIMPLE, ospfAuthenticationKeyType="7")))
    assert (nv["ospf"], nv["ospfAuthenticationKey"]) == ("false", "")
    assert nv["ospfAuthenticationKeyType"] == "7", "inert once the key is empty: kept as stored, not invented"


def test_merged_disable_with_md5_clears_the_key_through_the_chained_gate():
    nv = accepted(*run(ospf_off(), "merged", hv=md5_have()))
    assert (nv["ospf"], nv["ospfAuthentication"], nv["OSPF_AUTH_KEY"]) == ("false", "false", "")


def test_deleting_the_loopback_with_ospf_and_md5_on():
    result, calls = run(base(), "deleted", hv=md5_have())
    assert not result.get("failed"), result.get("msg")
    assert paths(calls) == ["DELETE interface/markdelete", "POST globalInterface/deploy"]
    assert SYN_MD5 not in json.dumps(calls)


# ------------------------------------------------------------------ default VRF: the loopback stays in the underlay process
def test_default_vrf_nac_disable_omitting_the_tag_is_still_refused():
    msg = refused(*run(ospf_off("default"), hv=have("default")), "ospf_tag")
    assert "ospf_auth_key" not in msg


def test_default_vrf_disable_with_md5_is_refused_for_the_tag_only():
    msg = refused(*run(ospf_off("default"), hv=md5_have("default")), "ospf_tag")
    assert "ospf_auth_key" not in msg, "the key is classified (cleared with authentication off); only the live tag blocks"


def test_default_vrf_disable_stating_the_tag_keeps_the_tag():
    nv = accepted(*run(dict(ospf_off("default"), ospf_tag=TAG), hv=have("default")))
    assert (nv["ospf"], nv["ospfTag"], nv["INTF_VRF"]) == ("false", TAG, "default")


def test_default_vrf_merged_disable_keeps_the_live_options():
    nv = accepted(*run(ospf_off("default"), "merged", hv=have("default")))
    assert (nv["ospf"], nv["ospfTag"], nv["ospfBfdMode"]) == ("false", TAG, "enable"), \
        "in the default VRF the options still apply to the underlay process; they are not neutralized"


def test_empty_vrf_is_the_default_vrf():
    msg = refused(*run(ospf_off("default"), hv=have("")), "ospf_tag")
    assert "ospf_auth_key" not in msg


# ------------------------------------------------------------------ the registry and the engine
LOOPBACK_OSPF_OFF = ("ospfTag", "ospfAdvertiseSubnet", "ospfAuthentication", "ospfAuthenticationKey", "ospfBfdMode",
                     "ospfCost", "ospfDeadInterval", "ospfHelloInterval", "ospfMtuIgnore", "ospfNetworkType", "ospfPriority",
                     "ospfRetransmitInterval", "ospfShutdown", "ospfTransmitDelay")


def test_registry_rows():
    for nvpair in LOOPBACK_OSPF_OFF:
        gate = table.resolve_by_nvpair("int_loopback", nvpair)["inert_when"]
        assert (gate["nvpair"], gate["value"]) == ("ospf", "false")
        assert gate["unless"] == {"nvpair": "INTF_VRF", "values": ("", "default")}
        assert gate.get("strict", False) is (nvpair != "ospfTag") and gate.get("required", False) is (nvpair == "ospfTag")
    assert table.resolve_by_nvpair("int_loopback", "OSPF_AUTH_KEY")["inert_when"] == {
        "nvpair": "ospfAuthentication", "value": "false", "required": True, "clear": ""}
    assert table.resolve_by_nvpair("int_loopback", "OSPF_AUTH_KEY_ID")["inert_when"] == {
        "nvpair": "ospfAuthentication", "value": "false"}
    assert table.resolve_by_nvpair("int_loopback", "ospfAuthenticationKeyType")["inert_when"] == {
        "nvpair": "ospfAuthenticationKey", "value": ""}
    assert "inert_when" not in table.resolve_by_nvpair("int_loopback", "OSPF_AREA_ID")


@pytest.mark.parametrize("nvpairs, inert", (
    ({"ospf": "false", "INTF_VRF": "TENANT-A"}, True),
    ({"ospf": False, "INTF_VRF": "TENANT-A"}, True),
    ({"ospf": "false", "INTF_VRF": "default"}, False),
    ({"ospf": "false", "INTF_VRF": ""}, False),
    ({"ospf": "false"}, False),
    ({"ospf": "false", "INTF_VRF": None}, False),
    ({"ospf": "true", "INTF_VRF": "TENANT-A"}, False),
    ({"INTF_VRF": "TENANT-A"}, False),
))
def test_inert_with_an_exception(nvpairs, inert):
    assert engine.gie_binding_inert(table.resolve_by_nvpair("int_loopback", "ospfTag"), nvpairs) is inert


def test_routed_rows_have_no_exception():
    for parent in ("int_routed_host", "int_subif", "int_vlan"):
        for row in table.BINDING_TABLE:
            if row["parent_template"] == parent and row.get("inert_when"):
                assert "unless" not in row["inert_when"]


def test_dependency_plan_keeps_default_vrf_options_live():
    have_nv = dict(FIXTURE["nvPairs"], INTF_VRF="default")
    writes, conflicts = engine.gie_dependency_plan("int_loopback", {"ospf": "false", "INTF_VRF": "default"}, have_nv,
                                                   {"ospf"}, True, "12.6.0.267", h.SUPPORTED_PATCH)
    assert writes == {} and conflicts == []
    writes, conflicts = engine.gie_dependency_plan("int_loopback", {"ospf": "false", "INTF_VRF": VRF}, FIXTURE["nvPairs"],
                                                   {"ospf"}, True, "12.6.0.267", h.SUPPORTED_PATCH)
    assert writes == {"ospfBfdMode": "noChange"} and conflicts == []
    writes, conflicts = engine.gie_dependency_plan("int_loopback", {"ospf": "false"},
                                                   dict((k, v) for k, v in FIXTURE["nvPairs"].items() if k != "INTF_VRF"),
                                                   {"ospf"}, True, "12.6.0.267", h.SUPPORTED_PATCH)
    assert writes == {} and conflicts == [], "no VRF in WANT or HAVE: not judged"


def _rows_with(nvpair, **row_update):
    rows = thin._as_slice_rows(table.BINDING_TABLE)
    for r in rows:
        if r["parent_template"] == "int_loopback" and r["parent_nvpair"] == nvpair:
            r.update(row_update)
    return rows


GATE = {"nvpair": "ospf", "value": "false", "required": True}


@pytest.mark.parametrize("unless", [
    "INTF_VRF",
    {"nvpair": "INTF_VRF"},
    {"nvpair": "INTF_VRF", "values": []},
    {"nvpair": "INTF_VRF", "values": ["default", "default"]},
    {"nvpair": "INTF_VRF", "values": [False]},
    {"nvpair": "", "values": ["default"]},
    {"nvpair": "ospf", "values": ["default"]},
    {"nvpair": "ospfTag", "values": ["default"]},
    {"nvpair": "INTF_VRF", "values": ["default"], "other": 1},
])
def test_generator_rejects_a_malformed_exception(unless):
    with pytest.raises(ValueError, match="inert_when unless"):
        thin._load_generator().compile_rows(_rows_with("ospfTag", inert_when=dict(GATE, unless=unless)))


def test_generator_compiles_the_exception_in_a_fixed_form():
    rows = thin._load_generator().compile_rows(_rows_with(
        "ospfTag", inert_when={"unless": {"values": ["", "default"], "nvpair": "INTF_VRF"}, "required": True,
                               "value": "false", "nvpair": "ospf"}))
    row = [r for r in rows if r["parent_template"] == "int_loopback" and r["parent_nvpair"] == "ospfTag"][0]
    assert list(row["inert_when"]) == ["nvpair", "value", "required", "unless"]
    assert row["inert_when"]["unless"] == {"nvpair": "INTF_VRF", "values": ("", "default")}


# ====================================================================================================
# Formerly test_gie_loopback_auth_is_fabric_owned.py
# Retiring OSPF-auth support on the fabric loopback must not DELETE the fabric's auth.
#
# THE DECISION BEHIND THIS FILE
#     OSPF authentication on a fabric loopback is underlay authentication, and the fabric owns
#     it. Read from the installed template ``int_fabric_loopback_11_1``:
#
#         if linkStateRouting == "ospf":                       # fabric setting
#             ospfAuthEnable = fabricSettings["OSPF_AUTH_ENABLE"]      # the fabric decides
#             if ospfAuthEnable == "true":
#                 if ospfAuthKeyId == "": ospfAuthKeyId = fabricSettings["OSPF_AUTH_KEY_ID"]
#                 if ospfAuthKey   == "": ospfAuthKey   = fabricSettings["OSPF_AUTH_KEY"]
#             if ospfAuthKeychainName:                                 # also a fabric setting
#                 ...
#                 delete ospf_interface_auth_message_digest_11_1       # overrides the interface
#
#     The interface nvPairs were only a per-loopback override of a fabric-owned key, and a
#     keychain setting silently deletes what they create. That capability is being withdrawn from
#     the product, so the three bindings and their dedicated validators are removed.
#
# THE TRAP THIS FILE EXISTS TO CATCH
#     Withdrawing SUPPORT must not become DELETING CONFIGURATION.
#
#     Those four nvPairs are listed in ``GIE_OSPF_MD_DOMAIN_NVPAIRS``, which is an EXCLUSION set:
#     ``gie_have_carry_forward_nvpairs`` preserves every builder-omitted HAVE nvPair on this
#     parent EXCEPT the ones in it, because the dedicated path used to own them.
#
#     Remove the bindings and the dedicated path but leave the exclusion, and those four fields
#     become orphans: nothing manages them and nothing preserves them. An operator changing a
#     loopback description under ``replaced`` would blank them and switch off authentication the
#     fabric is managing -- on the underlay, across the fabric.
#
#     The fix is to take them OUT of the exclusion set, so the generic HAVE carry-forward keeps
#     whatever the controller holds. The fabric owns the values; the interface simply stops
#     touching them.
#
#     ``test_the_exclusion_set_no_longer_shields_them`` fails if the exclusion is left behind.
#
# Offline: no controller and no device.
# ====================================================================================================
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
    """The required behaviour, asserted per field.

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
    the actual serialiser in test_no_log_and_redaction.py. It cannot be measured here: this
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
    it is asserted in test_no_log_and_redaction.py instead, against real output.
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
# THE TWO HALVES OF THE RULE
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
            mode, {"ospf_auth_keychain_name": "KEYCHAIN-1"}
        )
        assert rejected, "the keychain was accepted on mode '{0}'".format(mode)


# ====================================================================================================
# Formerly test_dcnm_ospfmd_parent_child_contract.py
# WS6 (G6A.3): source-contract for the fabric-loopback OSPF parent/child.
#
# These tests read the SHIPPING template source and the module source and assert
# the parent/child selection contract, WITHOUT changing the OSPF architecture. They
# exist to correct the overstatement that the parent Boolean alone guarantees the
# final child/PTI state, and to lock the Phase-3 invariant: the module manages the
# message-digest Boolean and the legacy-key pair (key-ID + key) as parent nvPairs,
# while the OSPF keychain field stays fabric-owned and is never a writable
# dcnm_interface field.
#
# What is proven here is the STATIC template/module contract only. PTI selection,
# the effective NX-OS CLI, OSPF adjacency and keychain behavior are NOT LIVE TESTED
# in this offline generation.
#
# Run:
#     DCNM_TEMPLATE_DIR=/path/to/ndfc/templates         pytest tests/unit/modules/dcnm/dcnm_interface/test_binding_ospf_loopback_subif.py
# ====================================================================================================
# The shipping NDFC templates are not part of this repository. Point DCNM_TEMPLATE_DIR at a directory
# holding them to run the template checks; without it they are skipped.
_TEMPLATE_DIRS = [
    d for d in (
        os.environ.get("DCNM_TEMPLATE_DIR"),
        os.path.join(os.path.dirname(__file__), "..", "fixtures", "templates"),
    ) if d
]
OSPFMD_PARENT = "int_fabric_loopback_11_1.template"
CHILD_MD = "ospf_interface_auth_message_digest_11_1.template"

# The module under test, read as text for the "emits no
# per-interface key/keychain field" invariant.
MODULE = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "..",
    "plugins", "modules", "dcnm_interface.py",
)


def _read_template(name):
    for d in _TEMPLATE_DIRS:
        path = os.path.join(d, name)
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                return fh.read()
    pytest.skip("shipping template {0} not available for the source contract".format(name))


@pytest.fixture(scope="module")
def parent_src():
    return _read_template(OSPFMD_PARENT)


@pytest.fixture(scope="module")
def child_md_src():
    return _read_template(CHILD_MD)


# --------------------------------------------------------------------------
# 1. the standalone message-digest child supplies ONLY the mode command
# --------------------------------------------------------------------------
def test_child_supplies_the_message_digest_mode_command(child_md_src):
    assert "ip ospf authentication message-digest" in child_md_src
    # It supplies no key material -- it is the mode command only.
    assert "OSPF_AUTH_KEY" not in child_md_src
    assert "key-chain" not in child_md_src.lower()


# --------------------------------------------------------------------------
# 2. the parent creates the standalone child on true and deletes it on false
# --------------------------------------------------------------------------
def test_parent_creates_child_on_true_and_deletes_on_false(parent_src):
    # createOrUpdate(..., "ospf_interface_auth_message_digest_11_1", ...) under
    # the true branch; delete(...) under the else branch.
    assert re.search(
        r'enableOspfAuthMessageDigest\s*==\s*"true"', parent_src
    ), "parent does not gate the message-digest child on the Boolean"
    assert re.search(
        r'createOrUpdate\([^)]*"ospf_interface_auth_message_digest_11_1"',
        parent_src,
        re.DOTALL,
    )
    assert re.search(
        r'PTIWrapper\.delete\([^)]*"ospf_interface_auth_message_digest_11_1"',
        parent_src,
        re.DOTALL,
    )


# --------------------------------------------------------------------------
# 3. the existing legacy-key path supplies key configuration
# --------------------------------------------------------------------------
def test_legacy_key_path_supplies_key_configuration(parent_src):
    # The legacy branch creates ospf_interface_auth with the key id and key.
    assert re.search(
        r'createOrUpdate\([^)]*"ospf_interface_auth"[^)]*OSPF_AUTH_KEY_ID[^)]*OSPF_AUTH_KEY',
        parent_src,
        re.DOTALL,
    ), "parent legacy branch does not carry OSPF_AUTH_KEY_ID/OSPF_AUTH_KEY"


# --------------------------------------------------------------------------
# 4. the keychain branch supersedes the standalone/legacy children
# --------------------------------------------------------------------------
def test_keychain_branch_supersedes_standalone_and_legacy(parent_src):
    # When a keychain is configured, the parent creates the keychain child and
    # DELETES both the legacy key child and the standalone message-digest child --
    # so the Boolean being true does NOT guarantee the message-digest child
    # survives.
    assert re.search(
        r'createOrUpdate\([^)]*"ospf_interface_auth_keychain"', parent_src, re.DOTALL
    )
    keychain_region = parent_src[parent_src.index("ospf_interface_auth_keychain"):]
    assert '"ospf_interface_auth"' in keychain_region
    assert '"ospf_interface_auth_message_digest_11_1"' in keychain_region


# --------------------------------------------------------------------------
# 5. Phase-3 contract: message-digest + legacy-key managed; keychain excluded
# --------------------------------------------------------------------------
def test_the_module_manages_none_of_it_and_the_fabric_owns_all_of_it():
    """INVERTED. It used to assert the module managed the legacy-key pair.

    That was true and is no longer: the capability was withdrawn because the template shows the
    fabric owning the whole feature. The tests above read that from the shipping source -- the
    block is gated on the fabric's link-state protocol, the enable flag and the key defaults come
    from fabricSettings, and a keychain fabric setting deletes the message-digest child outright.
    A per-loopback override on top of that has no use case.

    So the contract now is the simple one: dcnm_interface declares none of the three as a
    writable field, and rejects them by name if a playbook still carries them.
    """
    src = inspect.getsource(dcnm_interface)
    for field in ("enable_ospf_auth_message_digest", "ospf_auth_key_id", "ospf_auth_key"):
        assert "{0}=dict(".format(field) not in src, (
            "{0} is still a writable field; it was withdrawn".format(field)
        )
    assert "RETIRED_LOOPBACK_OSPF_AUTH_KEYS" in src, (
        "the withdrawn keys must be rejected by name, not silently ignored"
    )
    # The keychain was never writable here and still is not -- that invariant predates the
    # retirement and survives it unchanged.
    for keychain in ("ospf_auth_keychain_name", "ospfAuthKeychainName"):
        assert "{0}=dict(".format(keychain) not in src


# ====================================================================================================
# Formerly test_gie_ospf_017_modes.py
# OSPF BFD and passive on loopback and subinterface under SMU 4.3.1.0175006017.
#
# The 017 parent templates replaced the booleans ospfBfd (int_loopback, int_subif) and
# ospfPassiveInterface (int_subif) with the enums ospfBfdMode and ospfPassiveMode (installed bodies read from
# the 017 controller: int_loopback 8082cbdf, int_subif 1937c6a5; not exercised live by these tests).
#
# Public contract pinned here, through the real main():
#   * ospf_bfd_mode / ospf_passive_mode are the registered keys (no_change, enable, disable / passive, no_passive);
#   * the booleans ospf_bfd and ospf_passive_interface are an INPUT alias: true -> enable / passive, false -> no_change
#     (the old "no local override"), never the explicit disable / no_passive;
#   * the alias is rejected on a parent that does not register the mode key, and a conflicting pair is rejected.
#
# Nothing here claims the controller or the device behave this way: the requests are intercepted.
# ====================================================================================================
CTX = dict(h.OSPF_CTX)
CASES = [  # parent, public mode key, nvPair, alias key, positive word, wire positive
    (h.LOOPBACK, "ospf_bfd_mode", "ospfBfdMode", "ospf_bfd", "enable", "enable"),
    (h.SUBIF, "ospf_bfd_mode", "ospfBfdMode", "ospf_bfd", "enable", "enable"),
    (h.SUBIF, "ospf_passive_mode", "ospfPassiveMode", "ospf_passive_interface", "passive", "passive"),
]
IDS = ["%s::%s" % (c[0], c[1]) for c in CASES]


def ospf017_sent(calls, nvpair):
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
    assert ospf017_sent(calls, nvpair) == wire


@pytest.mark.parametrize("parent,mode_key,nvpair,alias,positive,wire", CASES, ids=IDS)
def test_the_explicit_negative_mode_is_distinct_from_no_change(parent, mode_key, nvpair, alias, positive, wire):
    explicit, wire_value = ("no_passive", "noPassive") if mode_key == "ospf_passive_mode" else ("disable", "disable")
    explicit_result, explicit_calls = create(parent, **{mode_key: explicit})
    neutral_result, neutral_calls = create(parent, **{mode_key: "no_change"})
    assert not explicit_result.get("failed") and not neutral_result.get("failed")
    assert ospf017_sent(explicit_calls, nvpair) == wire_value
    assert ospf017_sent(neutral_calls, nvpair) == "noChange"


@pytest.mark.parametrize("parent,mode_key,nvpair,alias,positive,wire", CASES, ids=IDS)
def test_the_boolean_alias_true_means_the_positive_mode(parent, mode_key, nvpair, alias, positive, wire):
    result, calls = create(parent, **{alias: True})
    assert not result.get("failed"), result.get("msg")
    assert ospf017_sent(calls, nvpair) == wire


@pytest.mark.parametrize("parent,mode_key,nvpair,alias,positive,wire", CASES, ids=IDS)
def test_the_boolean_alias_false_is_no_change_never_an_explicit_negative(parent, mode_key, nvpair, alias, positive, wire):
    result, calls = create(parent, **{alias: False})
    assert not result.get("failed"), result.get("msg")
    assert ospf017_sent(calls, nvpair) == "noChange"
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
    assert ospf017_sent(calls, nvpair) == wire


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
    assert ospf017_sent(calls, nvpair) == wire


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
    assert ospf017_sent(calls, nvpair) == "noChange", "false asks for no override, which is not the stored explicit negative"


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
    assert ospf017_sent(calls, nvpair) == "noChange"


# ====================================================================================================
# Formerly test_gie_ospf_subif_and_vlan.py
# OSPF on ``int_subif`` and ``int_vlan`` — the first bindings ever registered for either.
#
# WHAT WAS NEW HERE, AND WHAT WAS NOT
#     Unlike lot 2 on ``int_routed_host``, these two needed the engine hooked into the module:
#     neither parent had a ``gie_extend_prof_spec`` call in its validator nor a
#     ``gie_contribute_nvpairs`` call in its builder. Two calls each, mirroring the eth path, with
#     no feature-specific key added to either.
#
#     Everything after that was table rows. The shapes were already handled.
#
# THE THREE PARENTS ARE NOT THE SAME, AND THAT IS THE POINT
#     The same OSPF concepts are modelled differently per template:
#
#         concept      int_routed_host       int_subif                 int_vlan
#         passive      OSPF_PASSIVE_MODE     OSPF_PASSIVE_INTERFACE    OSPF_PASSIVE_MODE
#                      enum                  BOOLEAN                   enum
#         bfd          OSPF_BFD_MODE         OSPF_BFD                  OSPF_BFD_MODE
#                      enum                  BOOLEAN                   enum
#         retransmit   absent                OSPF_RETRANSMIT_INTERVAL  OSPF_RETRANSMIT_INTERVAL
#
#     Copying the routed slice would have registered ``OSPF_PASSIVE_MODE`` on a parent that does
#     not declare it -- an nvPair the controller would ignore, with the module reporting success.
#     Every row here was extracted from its own installed template
#     (``int_subif`` a66388c2f21c5507, ``int_vlan`` cee4cfc1d8a66d57).
#
#     ``test_the_parents_differ_where_the_templates_differ`` pins the divergence, so a future
#     "cleanup" that unifies them fails here rather than in the lab.
#
# ON THE SVI BUILDER
#     The contribution sits at METHOD level, outside the mode branch that precedes it. Registered
#     keys belong to the parent, not to one SVI mode; inside the branch they would be emitted for
#     some modes and silently dropped for others.
#
# Offline: no controller and no device.
# ====================================================================================================
SUBIF = "int_subif"
VLAN = "int_vlan"
NDFC_VERSION = "12.6.0.267"
# Declared explicitly for this file's one engine-driving instance.
PATCH_VERSION = sorted(GIE_ENABLED_PATCH_VERSIONS)[0]

# The fourteen each, from their own templates. profile_key -> (nvPair, type)
SUBIF_FIELDS = {
    "enable_ospf": ("ospf", "boolean"),
    "ospf_tag": ("ospfTag", "string"),
    "ospf_area_id": ("OSPF_AREA_ID", "string"),
    "ospf_cost": ("ospfCost", "integer"),
    "ospf_hello_interval": ("ospfHelloInterval", "integer"),
    "ospf_dead_interval": ("ospfDeadInterval", "integer"),
    "ospf_transmit_delay": ("ospfTransmitDelay", "integer"),
    "ospf_retransmit_interval": ("ospfRetransmitInterval", "integer"),
    "ospf_priority": ("ospfPriority", "integer"),
    "ospf_mtu_ignore": ("ospfMtuIgnore", "boolean"),
    "ospf_shutdown": ("ospfShutdown", "boolean"),
    "ospf_network_type": ("ospfNetworkType", "enum"),
    "ospf_passive_mode": ("ospfPassiveMode", "enum"),   # SMU 017: enum, as on routed and vlan
    "ospf_bfd_mode": ("ospfBfdMode", "enum"),           # SMU 017: enum, as on routed and vlan
}

VLAN_FIELDS = {
    "enable_ospf": ("ospf", "boolean"),
    "ospf_tag": ("ospfTag", "string"),
    "ospf_area_id": ("OSPF_AREA_ID", "string"),
    "ospf_cost": ("ospfCost", "integer"),
    "ospf_hello_interval": ("ospfHelloInterval", "integer"),
    "ospf_dead_interval": ("ospfDeadInterval", "integer"),
    "ospf_transmit_delay": ("ospfTransmitDelay", "integer"),
    "ospf_retransmit_interval": ("ospfRetransmitInterval", "integer"),
    "ospf_priority": ("ospfPriority", "integer"),
    "ospf_mtu_ignore": ("ospfMtuIgnore", "boolean"),
    "ospf_shutdown": ("ospfShutdown", "boolean"),
    "ospf_network_type": ("ospfNetworkType", "enum"),
    "ospf_passive_mode": ("ospfPassiveMode", "enum"),                # enum here
    "ospf_bfd_mode": ("ospfBfdMode", "enum"),                        # enum here
}

OSPF_SUBIF_CASES = [(SUBIF, SUBIF_FIELDS), (VLAN, VLAN_FIELDS)]


def _ids(parent, fields):
    return [(parent, key) for key in sorted(fields)]


ALL_KEYS = _ids(SUBIF, SUBIF_FIELDS) + _ids(VLAN, VLAN_FIELDS)


# =====================================================================================
# REGISTRATION
# =====================================================================================
@pytest.mark.parametrize("parent,key", ALL_KEYS)
def test_the_binding_matches_its_own_template(parent, key):
    fields = SUBIF_FIELDS if parent == SUBIF else VLAN_FIELDS
    nvpair, native = fields[key]
    b = resolve_binding(parent, key)
    assert b is not None, "{0}::{1} is not registered".format(parent, key)
    assert b["parent_nvpair"] == nvpair
    assert b["type"] == native


@pytest.mark.parametrize("parent,key", ALL_KEYS)
def test_the_binding_is_on_the_generic_route(parent, key):
    assert resolve_binding(parent, key)["mechanism"] == "passthrough"
    assert key in gie_guarded_keys()
    carried = {b["profile_key"] for b in gie_carry_forward_bindings(parent)}
    assert key in carried, "omitting {0} on {1} would drop the controller's value".format(
        key, parent)


# 14 OSPF fields of their own + the 5 shared authentication ones.
#
# Scoped to OSPF on purpose. These parents now also carry the thirteen EIGRP rows of slice
# 0b_22, so an unfiltered row count would stop meaning what the number above says it means --
# and a count that has drifted away from its own comment is worse than no count. The EIGRP
# inventory is pinned by test_gie_eigrp_bindings.py, and the table total by
# test_binding_values.py.
@pytest.mark.parametrize("parent,count", [(SUBIF, 19), (VLAN, 19)])
def test_the_parent_registers_exactly_its_own_fields(parent, count):
    rows = [b for b in BINDING_TABLE
            if b["parent_template"] == parent and "ospf" in b["parent_nvpair"].lower()]
    assert len(rows) == count
    names = [b["parent_nvpair"] for b in rows]
    assert len(names) == len(set(names)), "duplicate nvPair rows for {0}".format(parent)


# =====================================================================================
# THE DIVERGENCE — the reason slices are not copied between parents
# =====================================================================================
def test_the_parents_differ_where_the_templates_differ():
    """Pin the divergence so a future "unify these" change fails here, not in the lab.

    Registering an nvPair a template does not declare is the quiet failure this whole table
    exists to prevent: the controller ignores the key and the module reports success.
    """
    # passive: the enum on all three parents since SMU 017; the retired boolean key is no longer registered anywhere
    for parent in ("int_routed_host", VLAN, SUBIF):
        assert resolve_binding(parent, "ospf_passive_mode")["type"] == "enum"
        assert resolve_binding(parent, "ospf_passive_interface") is None

    # bfd: the same
    for parent in ("int_routed_host", VLAN, SUBIF):
        assert resolve_binding(parent, "ospf_bfd_mode")["type"] == "enum"
        assert resolve_binding(parent, "ospf_bfd") is None

    # retransmit interval: on all three since SMU 017 (int_routed_host declares it from 017, slice 0b_37)
    assert resolve_binding("int_routed_host", "ospf_retransmit_interval")["type"] == "integer"
    assert resolve_binding("int_routed_host", "ospf_retransmit_interval")["inert_when"]["nvpair"] == "ospf"
    assert resolve_binding(SUBIF, "ospf_retransmit_interval")["type"] == "integer"
    assert resolve_binding(VLAN, "ospf_retransmit_interval")["type"] == "integer"


@pytest.mark.parametrize("parent,key,lo,hi", [
    (SUBIF, "ospf_transmit_delay", 1, 450),
    (SUBIF, "ospf_priority", 0, 255),
    (SUBIF, "ospf_retransmit_interval", 1, 65535),
    (VLAN, "ospf_transmit_delay", 1, 450),
    (VLAN, "ospf_priority", 0, 255),
    (VLAN, "ospf_retransmit_interval", 1, 65535),
])
def test_each_range_comes_from_its_own_template(parent, key, lo, hi):
    """450 and 255 are not copies of 65535; a wrong bound accepts what NDFC rejects."""
    assert gie_validate_binding_value(parent, key, lo) == lo
    assert gie_validate_binding_value(parent, key, hi) == hi
    for bad in (lo - 1, hi + 1):
        with pytest.raises(GieBindingError):
            gie_validate_binding_value(parent, key, bad)


# =====================================================================================
# THE MODULE WIRING THAT HAD TO BE ADDED
# =====================================================================================
@pytest.mark.parametrize("validator,parent", [
    ("dcnm_intf_validate_sub_interface_input", SUBIF),
    ("dcnm_intf_validate_vlan_interface_input", VLAN),
])
def test_the_validator_extends_its_spec_from_the_registry(validator, parent):
    """Without this the arg spec rejects the key before anything is built.

    That is the exact failure the dot1q port-channel hit: registered in the table, transported
    by the engine, rejected by the spec.
    """
    src = inspect.getsource(getattr(dcnm_interface.DcnmIntf, validator))
    assert "gie_extend_prof_spec" in src
    assert '"{0}"'.format(parent) in src


@pytest.mark.parametrize("builder", [
    "dcnm_intf_get_sub_intf_payload",
    "dcnm_intf_get_svi_payload",
])
def test_the_builder_contributes_and_fails_closed(builder):
    src = inspect.getsource(getattr(dcnm_interface.DcnmIntf, builder))
    assert "gie_contribute_nvpairs" in src
    assert "fail_json" in src, "a version error must abort, not be silently dropped"


def test_the_svi_contribution_is_outside_the_mode_branch():
    """Registered keys belong to the parent, not to one SVI mode.

    Inside the branch they would be emitted for some modes and silently dropped for others --
    the module would report success and the device would not change.
    """
    src = inspect.getsource(dcnm_interface.DcnmIntf.dcnm_intf_get_svi_payload)
    line = next(ln for ln in src.split("\n") if "gie_contribute_nvpairs" in ln)
    indent = len(line) - len(line.lstrip())
    assert indent == 8, (
        "the contribution is indented {0}, so it sits inside a branch".format(indent)
    )


# =====================================================================================
# THE REAL MODULE PATH
# =====================================================================================
SUBIF_PROFILE = {
    "mode": "subint", "vlan": 1098, "ipv4_addr": "10.98.104.1", "ipv4_mask_len": 30,
    "int_vrf": "default", "mtu": 9216, "speed": "Auto", "cmds": [],
    "description": "wp98 subif", "admin_state": True,
}
SUBIF_OSPF = {
    "enable_ospf": True, "ospf_tag": "WP98", "ospf_area_id": "0.0.0.0", "ospf_cost": 110,
    "ospf_passive_mode": "passive", "ospf_bfd_mode": "enable", "ospf_retransmit_interval": 7,
    "ospf_hello_interval": 15, "ospf_priority": 42, "ospf_network_type": "point_to_point",
}
VLAN_PROFILE = {
    "mode": "vlan", "int_vrf": "default", "ipv4_addr": "10.98.98.1", "ipv4_mask_len": 30,
    "mtu": 9216, "speed": "Auto", "cmds": [], "description": "wp98 svi", "admin_state": True,
}
VLAN_OSPF = {
    "enable_ospf": True, "ospf_tag": "WP98", "ospf_area_id": "0.0.0.0", "ospf_cost": 120,
    "ospf_passive_mode": "no_passive", "ospf_bfd_mode": "disable",
    "ospf_retransmit_interval": 8, "ospf_hello_interval": 15, "ospf_priority": 42,
    "ospf_network_type": "broadcast",
}


def _run_chain(itype, name, validator, builder, parent, profile, ospf):
    obj = object.__new__(dcnm_interface.DcnmIntf)
    obj.intf_info = []
    obj.dcnm_version = 12
    obj.ndfc_version = NDFC_VERSION
    obj.patch_version = PATCH_VERSION
    obj.module = mock.Mock()
    obj.config = [{"name": name, "type": itype, "switch": ["10.1.1.1"],
                   "profile": dict(profile, **ospf)}]
    getattr(obj, validator)(obj.config)
    assert not obj.module.fail_json.called, (
        "{0} rejected the registered keys: {1}".format(validator, obj.module.fail_json.call_args)
    )
    intf = {"policy": parent, "interfaceType": "X",
            "interfaces": [{"serialNumber": "SNO", "ifName": name, "nvPairs": {}}]}
    getattr(obj, builder)(obj.config[0], intf, "profile")
    return intf["interfaces"][0]["nvPairs"]


@pytest.mark.parametrize("itype,name,validator,builder,parent,profile,ospf,wire", [
    ("sub_int", "eth1/5.100", "dcnm_intf_validate_sub_interface_input",
     "dcnm_intf_get_sub_intf_payload", SUBIF, SUBIF_PROFILE, SUBIF_OSPF,
     {"ospf": "true", "ospfCost": "110", "ospfRetransmitInterval": "7",
      "ospfPassiveMode": "passive", "ospfBfdMode": "enable",
      "ospfNetworkType": "pointToPoint"}),
    ("svi", "vlan1098", "dcnm_intf_validate_vlan_interface_input",
     "dcnm_intf_get_svi_payload", VLAN, VLAN_PROFILE, VLAN_OSPF,
     {"ospf": "true", "ospfCost": "120", "ospfRetransmitInterval": "8",
      "ospfPassiveMode": "noPassive", "ospfBfdMode": "disable",
      "ospfNetworkType": "broadcast"}),
])
def test_the_lot_reaches_the_payload_through_the_real_path(
        itype, name, validator, builder, parent, profile, ospf, wire):
    """Real validator, real builder -- not a fixture.

    A fixture that skipped the arg spec is what hid the FEC defect for a whole round.
    """
    nvpairs = _run_chain(itype, name, validator, builder, parent, profile, ospf)
    for nvpair, expected in wire.items():
        assert nvpair in nvpairs, "{0} never reached the payload on {1}".format(nvpair, parent)
        assert nvpairs[nvpair] == expected
        assert isinstance(nvpairs[nvpair], str), "nvPairs must be strings"


@pytest.mark.parametrize("itype,name,validator,builder,parent,profile,absent", [
    ("sub_int", "eth1/5.100", "dcnm_intf_validate_sub_interface_input",
     "dcnm_intf_get_sub_intf_payload", SUBIF, SUBIF_PROFILE,
     ["ospf", "ospfCost", "ospfBfdMode", "ospfPassiveMode"]),
    ("svi", "vlan1098", "dcnm_intf_validate_vlan_interface_input",
     "dcnm_intf_get_svi_payload", VLAN, VLAN_PROFILE,
     ["ospf", "ospfCost", "ospfBfdMode", "ospfPassiveMode"]),
])
def test_an_omitted_field_emits_nothing(
        itype, name, validator, builder, parent, profile, absent):
    """explicit_only: omission is not a value, so nothing is sent and nothing is defaulted."""
    nvpairs = _run_chain(itype, name, validator, builder, parent, profile, {})
    for nvpair in absent:
        assert nvpair not in nvpairs, (
            "{0} was emitted on {1} although the operator never set it".format(nvpair, parent)
        )


# =====================================================================================
# AUTHENTICATION IS REGISTERED ON ALL THREE PARENTS, IDENTICALLY
# =====================================================================================
#
# Inverted from "excluded on all three". The lot landed, and it landed as one slice for three
# parents -- the only OSPF slice that is not per parent.
#
# That shape is itself the claim being tested here. Everywhere else the three templates diverge
# (retransmit does not exist on
# routed), which is why slices are never copied between parents. Authentication is the one
# family where all five fields are byte-identical across the three, so the assertions below
# compare the parents against EACH OTHER rather than against a hardcoded list: if a future
# template changes one parent alone, that divergence is what fails.
AUTH_KEYS = ["enable_ospf_auth", "ospf_auth_key", "ospf_authentication_key",
             "ospf_auth_key_id", "ospf_authentication_key_type"]
OSPF_PARENTS = ["int_routed_host", SUBIF, VLAN]


@pytest.mark.parametrize("parent", OSPF_PARENTS)
@pytest.mark.parametrize("key", AUTH_KEYS)
def test_the_authentication_fields_are_registered_on_every_ospf_parent(parent, key):
    b = resolve_binding(parent, key)
    assert b is not None, "{0} is not registered on {1}".format(key, parent)
    assert b["mechanism"] == "passthrough"


@pytest.mark.parametrize("key", AUTH_KEYS)
def test_an_authentication_field_is_modelled_identically_on_all_three(key):
    """The comparison is parent against parent, not parent against a literal.

    A hardcoded expectation would still pass if all three drifted together; this fails the
    moment one of them stops matching its siblings, which is the only way this family can break
    the assumption that let it share a single slice.
    """
    shape = []
    for parent in OSPF_PARENTS:
        b = resolve_binding(parent, key)
        shape.append((b["parent_nvpair"], b["type"], b.get("valid_values"),
                      b.get("default_template"), b.get("min_value"), b.get("max_value"),
                      bool(b.get("no_log"))))
    assert len(set(shape)) == 1, (
        "{0} is no longer identical across the three OSPF parents: {1}. The single shared "
        "slice is only valid while they agree -- split it.".format(key, shape)
    )


@pytest.mark.parametrize("parent", OSPF_PARENTS)
def test_exactly_the_two_key_bearing_fields_are_no_log(parent):
    """Not "at least": marking anything else would corrupt output via string-match scrubbing."""
    marked = {b["profile_key"] for b in BINDING_TABLE
              if b["parent_template"] == parent and b.get("no_log")}
    assert marked == {"ospf_auth_key", "ospf_authentication_key"}
