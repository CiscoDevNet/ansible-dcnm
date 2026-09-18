"""OSPF on ``int_subif`` and ``int_vlan`` — the first bindings ever registered for either.

WHAT WAS NEW HERE, AND WHAT WAS NOT
    Unlike lot 2 on ``int_routed_host``, these two needed the engine hooked into the module:
    neither parent had a ``gie_extend_prof_spec`` call in its validator nor a
    ``gie_contribute_nvpairs`` call in its builder. Two calls each, mirroring the eth path, with
    no feature-specific key added to either.

    Everything after that was table rows. The shapes were already handled.

THE THREE PARENTS ARE NOT THE SAME, AND THAT IS THE POINT
    The same OSPF concepts are modelled differently per template:

        concept      int_routed_host       int_subif                 int_vlan
        passive      OSPF_PASSIVE_MODE     OSPF_PASSIVE_INTERFACE    OSPF_PASSIVE_MODE
                     enum                  BOOLEAN                   enum
        bfd          OSPF_BFD_MODE         OSPF_BFD                  OSPF_BFD_MODE
                     enum                  BOOLEAN                   enum
        retransmit   absent                OSPF_RETRANSMIT_INTERVAL  OSPF_RETRANSMIT_INTERVAL

    Copying the routed slice would have registered ``OSPF_PASSIVE_MODE`` on a parent that does
    not declare it -- an nvPair the controller would ignore, with the module reporting success.
    Every row here was extracted from its own installed template
    (``int_subif`` a66388c2f21c5507, ``int_vlan`` cee4cfc1d8a66d57).

    ``test_the_parents_differ_where_the_templates_differ`` pins the divergence, so a future
    "cleanup" that unifies them fails here rather than in the lab.

ON THE SVI BUILDER
    The contribution sits at METHOD level, outside the mode branch that precedes it. Registered
    keys belong to the parent, not to one SVI mode; inside the branch they would be emitted for
    some modes and silently dropped for others.

Offline: no controller and no device.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import inspect
from unittest import mock

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    BINDING_TABLE,
    resolve_binding,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    GieBindingError,
    gie_carry_forward_bindings,
    gie_guarded_keys,
    gie_validate_binding_value,
)
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

SUBIF = "int_subif"
VLAN = "int_vlan"
NDFC_VERSION = "12.6.0.267"

# The fourteen each, from their own templates. profile_key -> (nvPair, type)
SUBIF_FIELDS = {
    "enable_ospf": ("ENABLE_OSPF", "boolean"),
    "ospf_tag": ("OSPF_TAG", "string"),
    "ospf_area_id": ("OSPF_AREA_ID", "string"),
    "ospf_cost": ("OSPF_COST", "integer"),
    "ospf_hello_interval": ("OSPF_HELLO_INTERVAL", "integer"),
    "ospf_dead_interval": ("OSPF_DEAD_INTERVAL", "integer"),
    "ospf_transmit_delay": ("OSPF_TRANSMIT_DELAY", "integer"),
    "ospf_retransmit_interval": ("OSPF_RETRANSMIT_INTERVAL", "integer"),
    "ospf_priority": ("OSPF_PRIORITY", "integer"),
    "ospf_mtu_ignore": ("OSPF_MTU_IGNORE", "boolean"),
    "ospf_shutdown": ("OSPF_SHUTDOWN", "boolean"),
    "ospf_network_type": ("OSPF_NETWORK_TYPE", "enum"),
    "ospf_passive_interface": ("OSPF_PASSIVE_INTERFACE", "boolean"),   # boolean here
    "ospf_bfd": ("OSPF_BFD", "boolean"),                               # boolean here
}

VLAN_FIELDS = {
    "enable_ospf": ("ENABLE_OSPF", "boolean"),
    "ospf_tag": ("OSPF_TAG", "string"),
    "ospf_area_id": ("OSPF_AREA_ID", "string"),
    "ospf_cost": ("OSPF_COST", "integer"),
    "ospf_hello_interval": ("OSPF_HELLO_INTERVAL", "integer"),
    "ospf_dead_interval": ("OSPF_DEAD_INTERVAL", "integer"),
    "ospf_transmit_delay": ("OSPF_TRANSMIT_DELAY", "integer"),
    "ospf_retransmit_interval": ("OSPF_RETRANSMIT_INTERVAL", "integer"),
    "ospf_priority": ("OSPF_PRIORITY", "integer"),
    "ospf_mtu_ignore": ("OSPF_MTU_IGNORE", "boolean"),
    "ospf_shutdown": ("OSPF_SHUTDOWN", "boolean"),
    "ospf_network_type": ("OSPF_NETWORK_TYPE", "enum"),
    "ospf_passive_mode": ("OSPF_PASSIVE_MODE", "enum"),                # enum here
    "ospf_bfd_mode": ("OSPF_BFD_MODE", "enum"),                        # enum here
}

CASES = [(SUBIF, SUBIF_FIELDS), (VLAN, VLAN_FIELDS)]


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


@pytest.mark.parametrize("parent,count", [(SUBIF, 14), (VLAN, 14)])
def test_the_parent_registers_exactly_its_own_fields(parent, count):
    rows = [b for b in BINDING_TABLE if b["parent_template"] == parent]
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
    # passive: enum on routed and vlan, boolean on subif
    assert resolve_binding("int_routed_host", "ospf_passive_mode")["type"] == "enum"
    assert resolve_binding(VLAN, "ospf_passive_mode")["type"] == "enum"
    assert resolve_binding(SUBIF, "ospf_passive_interface")["type"] == "boolean"
    assert resolve_binding(SUBIF, "ospf_passive_mode") is None
    assert resolve_binding(VLAN, "ospf_passive_interface") is None

    # bfd: same split
    assert resolve_binding("int_routed_host", "ospf_bfd_mode")["type"] == "enum"
    assert resolve_binding(VLAN, "ospf_bfd_mode")["type"] == "enum"
    assert resolve_binding(SUBIF, "ospf_bfd")["type"] == "boolean"
    assert resolve_binding(SUBIF, "ospf_bfd_mode") is None
    assert resolve_binding(VLAN, "ospf_bfd") is None

    # retransmit interval: absent on the routed parent, present on the other two
    assert resolve_binding("int_routed_host", "ospf_retransmit_interval") is None
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
    "ospf_passive_interface": False, "ospf_bfd": False, "ospf_retransmit_interval": 7,
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
     {"ENABLE_OSPF": "true", "OSPF_COST": "110", "OSPF_RETRANSMIT_INTERVAL": "7",
      "OSPF_PASSIVE_INTERFACE": "false", "OSPF_BFD": "false",
      "OSPF_NETWORK_TYPE": "point_to_point"}),
    ("svi", "vlan1098", "dcnm_intf_validate_vlan_interface_input",
     "dcnm_intf_get_svi_payload", VLAN, VLAN_PROFILE, VLAN_OSPF,
     {"ENABLE_OSPF": "true", "OSPF_COST": "120", "OSPF_RETRANSMIT_INTERVAL": "8",
      "OSPF_PASSIVE_MODE": "no_passive", "OSPF_BFD_MODE": "disable",
      "OSPF_NETWORK_TYPE": "broadcast"}),
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
     ["ENABLE_OSPF", "OSPF_COST", "OSPF_BFD", "OSPF_PASSIVE_INTERFACE"]),
    ("svi", "vlan1098", "dcnm_intf_validate_vlan_interface_input",
     "dcnm_intf_get_svi_payload", VLAN, VLAN_PROFILE,
     ["ENABLE_OSPF", "OSPF_COST", "OSPF_BFD_MODE", "OSPF_PASSIVE_MODE"]),
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
# AUTHENTICATION IS EXCLUDED ON ALL THREE PARENTS
# =====================================================================================
@pytest.mark.parametrize("parent", ["int_routed_host", SUBIF, VLAN])
@pytest.mark.parametrize("key", [
    "enable_ospf_auth", "ospf_auth_key", "ospf_authentication_key",
    "ospf_auth_key_id", "ospf_authentication_key_type",
])
def test_the_authentication_fields_are_not_registered_on_any_ospf_parent(parent, key):
    """One lot across all three, so the mechanism decision is made once, not three times."""
    assert resolve_binding(parent, key) is None
