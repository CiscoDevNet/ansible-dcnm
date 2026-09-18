"""OSPF lot 2 on ``int_routed_host`` — the nine non-authentication fields.

Lot 1 (gate, tag, area, cost) was validated on hardware. These nine sit behind the same gate,
each with its own child template, so they are independent value fields rather than a composite.

WHAT IS ACTUALLY NEW HERE
    Nothing structural, and that is the point worth recording: no module change was needed.
    ``gie_nvpair_keymap()`` and ``gie_extend_prof_spec`` derive from the binding table, so nine
    table rows reach the arg spec, the payload and the carry-forward on their own.

    The shapes were all already handled:

        boolean with a false default   like ENABLE_OSPF
        integer with no default        like OSPF_COST
        enum with a "leave it" default like GUARD_MODE ("no") and SPANNING_TREE_PORT_TYPE

THE no_change SENTINEL IS NDFC's, NOT THE ENGINE's
    Three of the enums default to ``no_change``, which on the controller means "do not touch
    this on the device". An earlier analysis treated that as a third state the engine would
    have to model, distinct from a value and from absence. It is not: the engine validates enum
    membership and transports the string, exactly as it does for ``GUARD_MODE``. The semantics
    live in the template.

    ``test_the_no_change_enums_behave_exactly_like_the_enums_already_registered`` pins that, so
    the claim is checked rather than asserted.

TESTED THROUGH THE REAL PATH
    The positive cases drive ``dcnm_intf_validate_ethernet_interface_input`` and
    ``dcnm_intf_get_eth_payload``, not a hand-built fixture. That distinction is not academic:
    a fixture that skipped the arg spec is what hid the FEC defect for an entire round.

Offline: no controller and no device.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest import mock

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    resolve_binding,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    GieBindingError,
    gie_carry_forward_bindings,
    gie_guarded_keys,
    gie_validate_binding_value,
)
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

PARENT = "int_routed_host"
NDFC_VERSION = "12.6.0.267"

# profile_key -> (nvPair, type, declared default, declared range)
# Read from the installed template, sha b9b50077cf49f8cb -- not from the Excel or the ledger.
LOT2 = {
    "ospf_mtu_ignore":     ("OSPF_MTU_IGNORE",     "boolean", False, None),
    "ospf_shutdown":       ("OSPF_SHUTDOWN",       "boolean", False, None),
    "ospf_hello_interval": ("OSPF_HELLO_INTERVAL", "integer", None, (1, 65535)),
    "ospf_dead_interval":  ("OSPF_DEAD_INTERVAL",  "integer", None, (1, 65535)),
    "ospf_transmit_delay": ("OSPF_TRANSMIT_DELAY", "integer", None, (1, 450)),
    "ospf_priority":       ("OSPF_PRIORITY",       "integer", None, (0, 255)),
    "ospf_passive_mode":   ("OSPF_PASSIVE_MODE",   "enum", "no_change",
                            ("no_change", "passive", "no_passive")),
    "ospf_network_type":   ("OSPF_NETWORK_TYPE",   "enum", "no_change",
                            ("no_change", "broadcast", "point_to_point")),
    "ospf_bfd_mode":       ("OSPF_BFD_MODE",       "enum", "no_change",
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
    "OSPF_MTU_IGNORE": "true",
    "OSPF_SHUTDOWN": "false",
    "OSPF_HELLO_INTERVAL": "15",
    "OSPF_DEAD_INTERVAL": "60",
    "OSPF_TRANSMIT_DELAY": "3",
    "OSPF_PRIORITY": "42",
    "OSPF_PASSIVE_MODE": "no_passive",
    "OSPF_NETWORK_TYPE": "point_to_point",
    "OSPF_BFD_MODE": "disable",
}

BASE_PROFILE = {
    "mode": "routed", "admin_state": True, "int_vrf": "default",
    "ipv4_addr": "10.98.103.1", "ipv4_mask_len": 30, "mtu": 9216, "speed": "Auto",
    "route_tag": "", "cmds": [], "description": "lot2",
    "enable_ospf": True, "ospf_tag": "WP98", "ospf_area_id": "0.0.0.0", "ospf_cost": 100,
}


def _instance(profile):
    obj = object.__new__(dcnm_interface.DcnmIntf)
    obj.intf_info = []
    obj.dcnm_version = 12
    obj.ndfc_version = NDFC_VERSION
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
def test_a_controller_value_outside_the_range_is_carried_not_rejected(key):
    """The range is an INPUT contract. HAVE is the controller's, and is not re-litigated."""
    assert gie_validate_binding_value(PARENT, key, "99999", value_source="have") == "99999"
    assert gie_validate_binding_value(PARENT, key, "", value_source="have") == ""


# =====================================================================================
# THE REAL MODULE PATH
# =====================================================================================
def test_the_lot_survives_the_real_ethernet_validator():
    obj = _instance(dict(BASE_PROFILE, **SAMPLE))
    obj.dcnm_intf_validate_ethernet_interface_input(obj.config)
    assert not obj.module.fail_json.called, (
        "the routed arg spec rejected lot 2: {0}".format(obj.module.fail_json.call_args)
    )
    profile = obj.config[0]["profile"]
    for key, value in SAMPLE.items():
        assert key in profile, "{0} was dropped by validation".format(key)
        assert profile[key] == value, "{0} was altered by validation".format(key)


def test_the_lot_reaches_the_payload_through_the_real_builder():
    obj = _instance(dict(BASE_PROFILE, **SAMPLE))
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
    obj = _instance(BASE_PROFILE)          # none of the nine set
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
# THE AUTHENTICATION FAMILY IS DELIBERATELY ABSENT
# =====================================================================================
@pytest.mark.parametrize("key", [
    "enable_ospf_auth", "ospf_auth_key", "ospf_authentication_key",
    "ospf_auth_key_id", "ospf_authentication_key_type",
])
def test_the_authentication_fields_are_not_registered_on_this_parent_yet(key):
    """Pin the exclusion so it reads as a decision, not an oversight.

    Three of these already exist as ``child_pti`` on ``int_fabric_loopback_11_1`` with a
    dedicated validator. Registering the same nvPair on a second parent is a per-(parent,
    nvpair) mechanism decision -- ACL_FILTER is the precedent for the same key differing by
    parent -- and the key value must never be printed or logged. Their own lot, with their own
    live run.
    """
    assert resolve_binding(PARENT, key) is None
