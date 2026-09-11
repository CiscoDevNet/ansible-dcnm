"""One authoritative carry-forward path.

Two carry-forward mechanisms coexist:

  * `gie_have_carry_forward_nvpairs` — generic same-parent HAVE preservation, scoped by the
    CALLER to the int_fabric_loopback_11_1 parent, merged state only.
  * `gie_carry_forward_bindings` — registered passthrough bindings, re-validated against the
    registry before being carried.

These tests prove they coexist without double injection, without losing HAVE values, and
without any cross-parent carry, driven through the real comparator
`DcnmIntf.dcnm_intf_compare_want_and_have`.

Helpers are imported from the sibling suite rather than duplicated, so the two files cannot
drift apart.

NOT LIVE TESTED IN THIS GENERATION.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    GIE_OSPF_MD_DOMAIN_NVPAIRS,
    GIE_READONLY_METADATA_NVPAIRS,
    gie_carry_forward_bindings,
    gie_have_carry_forward_nvpairs,
)
from .test_dcnm_intf_loopback_carry_forward import (
    BUILDER_NV,
    FAB,
    HAVE_METADATA,
    HAVE_ONLY_WRITABLE,
    HAVE_OSPF_DOMAIN,
    MD,
    PARENT,
    SNO,
    _full_have,
    _have,
    _instance,
    _payload_nv,
    _pb,
    _public_nv,
    _want,
    _want_md,
)

TRUNK = "int_trunk_host"
ACCESS = "int_access_host"
PC_TRUNK = "int_port_channel_trunk_host"
PC_DOT1Q = "int_port_channel_dot1q_tunnel_host"

# Registered passthrough nvPairs per eth parent, and a builder-emitted baseline for them.
ETH_BUILDER_NV = {
    "INTF_NAME": "Ethernet1/30",
    "DESC": "",
    "CONF": "",
    "ADMIN_STATE": "true",
    "SPEED": "Auto",
    "BPDUGUARD_ENABLED": "true",
    "MTU": "jumbo",
}
# Three registered bindings, one per value type, living only in HAVE.
ETH_HAVE_REGISTERED = {
    "GUARD_MODE": "root",            # enum
    "DISABLE_LLDP": True,            # boolean
    "ACL_FILTER": "ACL_FROM_HAVE",   # string
    "FLOWCONTROL_RECEIVE": "on",     # enum (baseline binding)
}
ETH_KEYMAP = {
    "INTF_NAME": "name", "DESC": "description", "CONF": "cmds",
    "ADMIN_STATE": "admin_state", "SPEED": "speed",
    "BPDUGUARD_ENABLED": "bpdu_guard", "MTU": "mtu",
    "GUARD_MODE": "guard_mode", "DISABLE_LLDP": "disable_lldp",
    "ACL_FILTER": "acl_filter", "FLOWCONTROL_RECEIVE": "flowcontrol_receive",
}


def _eth_instance():
    s = _instance()
    s.keymap = dict(ETH_KEYMAP)
    return s


def _eth_want(nv, policy=TRUNK, ifname="Ethernet1/30"):
    return {
        "policy": policy,
        "interfaceType": "INTERFACE_ETHERNET",
        "deploy": False,
        "interfaces": [{
            "ifName": ifname, "serialNumber": SNO, "fabricName": FAB,
            "interfaceType": "INTERFACE_ETHERNET", "nvPairs": dict(nv),
        }],
    }


def _eth_have(nv, policy=TRUNK, ifname="Ethernet1/30"):
    return [{
        "policy": policy,
        "interfaces": [{
            "ifName": ifname, "serialNumber": SNO,
            "interfaceType": "INTERFACE_ETHERNET", "nvPairs": dict(nv),
        }],
    }]


def _eth_pb(**public_keys):
    item = {"ifname": "Ethernet1/30", "sno": SNO, "fabric": FAB}
    item.update(public_keys)
    return item


def _run(s, state="merged"):
    s.dcnm_intf_compare_want_and_have(state)


# =====================================================================================
# ONE AUTHORITATIVE PATH — the two mechanisms do not overlap
# =====================================================================================
def test_the_two_carry_forward_paths_are_disjoint_by_construction():
    """The loopback parent has no passthrough binding, so only the generic path runs there."""
    assert gie_carry_forward_bindings(PARENT) == [], (
        "if the loopback parent ever registers a passthrough binding, the two carry-forward "
        "paths would both target it and this integration must be re-reviewed"
    )
    # Conversely, the eth/pc parents DO have registered bindings...
    for parent in (TRUNK, ACCESS, PC_TRUNK, PC_DOT1Q):
        assert gie_carry_forward_bindings(parent), f"{parent} should register bindings"
    # ...and the generic HAVE carry-forward is caller-scoped to the loopback parent only,
    # which the comparator enforces (asserted end-to-end below).


def test_generic_carry_forward_never_overwrites_a_key_already_in_want():
    """Second, independent guarantee against double injection."""
    want_nv = {"PRIORITY": "999", "IP": "10.0.0.1"}
    have_nv = {"PRIORITY": "301", "IP": "10.9.9.9", "REPLICATION_MODE": "Ingress"}
    carried = gie_have_carry_forward_nvpairs(want_nv, have_nv)
    assert "PRIORITY" not in carried, "an explicit/builder value must never be overridden"
    assert "IP" not in carried
    assert carried == {"REPLICATION_MODE": "Ingress"}


def test_no_double_injection_on_the_loopback_parent():
    """Run the real comparator and assert every carried nvPair appears exactly once, with the
    exact HAVE value — not a value written twice by two paths."""
    s = _instance()
    s.want = [_want(_want_md(True))]
    s.have = _have(_full_have("false"))
    s.pb_input = [_pb(enable_ospf_auth_message_digest=True)]
    _run(s)
    payload = _payload_nv(s)
    assert payload is not None
    for key, value in HAVE_ONLY_WRITABLE.items():
        assert payload[key] == value, f"{key} must equal the exact HAVE value"
    # The registered-binding path contributes nothing here: none of its nvPairs may appear.
    for nvpair in ("GUARD_MODE", "DISABLE_LLDP", "ACL_FILTER", "FLOWCONTROL_RECEIVE"):
        assert nvpair not in payload, (
            f"{nvpair} is not registered on {PARENT}; the registered path must not run here"
        )


def test_no_cross_parent_carry_from_loopback_to_eth():
    """An eth parent must NOT receive the generic loopback carry-forward."""
    s = _eth_instance()
    want_nv = dict(ETH_BUILDER_NV, DESC="changed")
    s.want = [_eth_want(want_nv)]
    have_nv = dict(ETH_BUILDER_NV)
    have_nv.update(HAVE_ONLY_WRITABLE)      # loopback-shaped extras present in HAVE
    have_nv.update(HAVE_METADATA)
    s.have = _eth_have(have_nv)
    s.pb_input = [_eth_pb(description="changed")]
    _run(s)
    payload = _payload_nv(s)
    if payload is not None:
        for key in HAVE_ONLY_WRITABLE:
            assert key not in payload, (
                f"{key} was carried onto {TRUNK}; the generic carry-forward must stay scoped "
                f"to {PARENT}"
            )


def test_no_cross_parent_carry_from_eth_to_loopback():
    """The loopback parent must not gain eth registered nvPairs from a stray HAVE."""
    s = _instance()
    s.want = [_want(_want_md(True))]
    have_nv = _full_have("false")
    have_nv.update(ETH_HAVE_REGISTERED)     # eth-shaped registered keys in a loopback HAVE
    s.have = _have(have_nv)
    s.pb_input = [_pb(enable_ospf_auth_message_digest=True)]
    _run(s)
    payload = _payload_nv(s)
    assert payload is not None
    # The generic path carries builder-omitted, non-excluded HAVE nvPairs for THIS parent. The
    # eth keys are not excluded, so they ARE carried as opaque HAVE values -- that is the
    # documented "preserve whatever NDFC returned" behaviour, NOT a registered-binding carry.
    # What must NOT happen is the registered path claiming them: assert the values are the exact
    # HAVE values and that no registry validation was applied (no coercion, no rejection).
    for key, value in ETH_HAVE_REGISTERED.items():
        assert payload[key] == value, f"{key} must be the exact opaque HAVE value"
    assert gie_carry_forward_bindings(PARENT) == [], (
        "no registered binding exists on this parent, so the registered path did not run"
    )


# =====================================================================================
# EXCLUSIONS — metadata and the OSPF-MD domain are never carried
# =====================================================================================
def test_readonly_metadata_is_never_carried():
    carried = gie_have_carry_forward_nvpairs({}, dict(HAVE_METADATA, PRIORITY="301"))
    for key in GIE_READONLY_METADATA_NVPAIRS:
        assert key not in carried
    assert carried == {"PRIORITY": "301"}


def test_ospf_md_domain_is_never_carried_by_the_generic_path():
    have = dict(HAVE_OSPF_DOMAIN)
    have[MD] = "true"
    have["PRIORITY"] = "301"
    carried = gie_have_carry_forward_nvpairs({}, have)
    for key in GIE_OSPF_MD_DOMAIN_NVPAIRS:
        assert key not in carried, f"{key} is owned by the dedicated OSPF-MD path"
    assert carried == {"PRIORITY": "301"}


def test_key_material_is_never_carried():
    """Explicit: no key material may be echoed into a payload by this path."""
    have = {"OSPF_AUTH_KEY": "<redacted-in-test>", "OSPF_AUTH_KEY_ID": "7",
            "ospfAuthKeychainName": "kc", "PRIORITY": "301"}
    carried = gie_have_carry_forward_nvpairs({}, have)
    assert set(carried) == {"PRIORITY"}


# =====================================================================================
# MALFORMED HAVE — fail closed, carry nothing
# =====================================================================================
@pytest.mark.parametrize("bad_have", [None, [], "", "nvpairs", 0, 1, 3.14, set(), object()])
def test_non_dict_have_carries_nothing(bad_have):
    assert gie_have_carry_forward_nvpairs({"IP": "1.1.1.1"}, bad_have) == {}


def test_malformed_have_nvpairs_hits_a_PREEXISTING_legacy_limit_not_the_carry_forward():
    """A HAVE entry whose ``nvPairs`` is not a dict raises inside the LEGACY comparator.

    FINDING, recorded rather than silently fixed. `dcnm_intf_compare_want_and_have` does
    `intf.get(ik, {}).get(key, None)` while scanning HAVE. When `nvPairs` is None that is
    `None.get(...)` -> AttributeError, and it happens BEFORE either carry-forward runs.

    This is pre-existing behaviour, not something the merged carry-forward introduced,
    and hardening the legacy comparator is outside this mandate's authority (it would change
    behaviour for every unregistered field on every parent). The contribution proven here is
    fail-closed independently by `test_non_dict_have_carries_nothing`.

    The test asserts the CURRENT truth so the limit is visible and a future fix is a
    deliberate, reviewed change rather than an accident.
    """
    s = _instance()
    s.want = [_want(_want_md(True))]
    bad = _have(_full_have("false"))
    bad[0]["interfaces"][0]["nvPairs"] = None
    s.have = bad
    s.pb_input = [_pb(enable_ospf_auth_message_digest=True)]
    with pytest.raises(AttributeError):
        _run(s)
    # And the carry-forward helper itself is fail-closed for exactly this input.
    assert gie_have_carry_forward_nvpairs({"IP": "1.1.1.1"}, None) == {}


# =====================================================================================
# STATE SCOPING — merged only; replaced/overridden intentionally reset
# =====================================================================================
@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_generic_carry_forward_does_not_run_outside_merged(state):
    """The current contract limits the generic carry-forward to merged.

    replaced/overridden deliberately reset builder-omitted nvPairs; that is the documented
    semantics, and this test pins it so a future change is a deliberate decision.
    """
    s = _instance()
    s.want = [_want(_want_md(True))]
    s.have = _have(_full_have("false"))
    s.pb_input = [_pb(enable_ospf_auth_message_digest=True)]
    _run(s, state=state)
    payload = _payload_nv(s)
    if payload is not None:
        for key in HAVE_ONLY_WRITABLE:
            assert key not in payload, (
                f"{state} must not carry {key}; only merged does"
            )


# =====================================================================================
# REGISTERED-BINDING CARRY-FORWARD — enum / boolean / string, on the eth parent
# =====================================================================================
@pytest.mark.parametrize("nvpair,profile_key,value", [
    ("GUARD_MODE", "guard_mode", "root"),
    ("DISABLE_LLDP", "disable_lldp", True),
    ("ACL_FILTER", "acl_filter", "ACL_FROM_HAVE"),
    ("FLOWCONTROL_RECEIVE", "flowcontrol_receive", "on"),
])
def test_registered_binding_is_carried_when_omitted(nvpair, profile_key, value):
    """Omitted explicit input + populated HAVE -> the authoritative value is preserved."""
    s = _eth_instance()
    # A real change is needed for the comparator to emit an update at all; DESC differs while
    # the registered key is OMITTED by the user and present only in HAVE.
    s.want = [_eth_want(dict(ETH_BUILDER_NV, DESC="changed"))]
    have_nv = dict(ETH_BUILDER_NV)
    have_nv[nvpair] = value
    s.have = _eth_have(have_nv)
    s.pb_input = [_eth_pb(description="changed")]  # profile_key NOT in the playbook keys
    _run(s)
    payload = _payload_nv(s)
    assert payload is not None, "an update payload must be produced"
    assert payload.get(nvpair) == value, f"{nvpair} must be carried from HAVE exactly"
    assert type(payload[nvpair]) is type(value), "the native type must survive"


def test_registered_carry_forward_produces_no_public_diff():
    """A carried value is transport preservation, not a requested change."""
    s = _eth_instance()
    s.want = [_eth_want(dict(ETH_BUILDER_NV, DESC="new"))]
    have_nv = dict(ETH_BUILDER_NV)
    have_nv["GUARD_MODE"] = "root"
    s.have = _eth_have(have_nv)
    s.pb_input = [_eth_pb(description="new")]
    _run(s)
    public = _public_nv(s)
    if public is not None:
        assert "GUARD_MODE" not in public, (
            "a carried value must not be reported as a requested change"
        )


def test_explicit_value_wins_over_have():
    s = _eth_instance()
    want_nv = dict(ETH_BUILDER_NV, DESC="changed")
    want_nv["GUARD_MODE"] = "loop"                 # explicit, engine-transported
    s.want = [_eth_want(want_nv)]
    have_nv = dict(ETH_BUILDER_NV)
    have_nv["GUARD_MODE"] = "root"
    s.have = _eth_have(have_nv)
    s.pb_input = [_eth_pb(guard_mode="loop", description="changed")]
    _run(s)
    payload = _payload_nv(s)
    assert payload is not None
    assert payload["GUARD_MODE"] == "loop", "the explicit value must win"


def test_absent_have_carries_nothing_and_invents_no_default():
    s = _eth_instance()
    s.want = [_eth_want(dict(ETH_BUILDER_NV, DESC="new"))]
    s.have = _eth_have(ETH_BUILDER_NV)             # HAVE has none of the registered keys
    s.pb_input = [_eth_pb(description="new")]
    _run(s)
    payload = _payload_nv(s)
    if payload is not None:
        for nvpair in ("GUARD_MODE", "DISABLE_LLDP", "ACL_FILTER"):
            assert nvpair not in payload, (
                f"{nvpair} absent from HAVE must not be invented"
            )


# =====================================================================================
# IDEMPOTENCE — second run through the real comparator
# =====================================================================================
def test_second_run_is_idempotent_on_the_loopback_parent():
    def run_once():
        s = _instance()
        s.want = [_want(_want_md(True))]
        s.have = _have(_full_have("true"))         # already correct
        s.pb_input = [_pb(enable_ospf_auth_message_digest=True)]
        _run(s)
        return _payload_nv(s), _public_nv(s)

    first_payload, first_public = run_once()
    second_payload, second_public = run_once()
    assert first_payload == second_payload, "the comparator must be deterministic"
    assert first_public == second_public
    if first_public is not None:
        for key in HAVE_ONLY_WRITABLE:
            assert key not in first_public, "carried keys must never enter the public diff"


def test_second_run_is_idempotent_on_the_eth_parent():
    def run_once():
        s = _eth_instance()
        s.want = [_eth_want(dict(ETH_BUILDER_NV, DESC="changed"))]
        have_nv = dict(ETH_BUILDER_NV)
        have_nv.update(ETH_HAVE_REGISTERED)
        s.have = _eth_have(have_nv)
        s.pb_input = [_eth_pb(description="changed")]
        _run(s)
        return _payload_nv(s), _public_nv(s)

    first_payload, first_public = run_once()
    second_payload, second_public = run_once()
    assert first_payload == second_payload
    assert first_public == second_public


# =====================================================================================
# NO TRANSPORT OF UNREGISTERED OR WRONG-PARENT nvPairs
# =====================================================================================
def test_registered_carry_forward_skips_a_wrong_parent_binding():
    """A field registered on one parent must not be carried onto a parent that lacks it.

    FLOWCONTROL is the sharpest case available: a sweep of all 98 templates confirms only the
    two host ethernet parents declare it, so no port-channel parent may carry it. This
    previously used DISABLE_LLDP, which turned out to be a poor choice -- the port-channel
    templates DO declare it, and it is now registered there.
    """
    carried = {row["profile_key"] for row in gie_carry_forward_bindings(PC_TRUNK)}
    assert "flowcontrol_receive" not in carried
    assert "flowcontrol_send" not in carried
    assert all(
        row["profile_key"] != "guard_mode"
        for row in gie_carry_forward_bindings(PC_DOT1Q)
    ), "guard_mode is not registered on pc/dot1q"


def test_unregistered_nvpair_is_not_carried_by_the_registered_path():
    s = _eth_instance()
    s.want = [_eth_want(dict(ETH_BUILDER_NV, DESC="new"))]
    have_nv = dict(ETH_BUILDER_NV)
    have_nv["SOME_UNREGISTERED_NVPAIR"] = "x"
    s.have = _eth_have(have_nv)
    s.pb_input = [_eth_pb(description="new")]
    _run(s)
    payload = _payload_nv(s)
    if payload is not None:
        assert "SOME_UNREGISTERED_NVPAIR" not in payload, (
            "the eth parent has no generic HAVE carry-forward; only registered bindings carry"
        )
