"""Registering a parent in the table is only half the work; the module has to be wired for it.

A binding needs two things on the module side, and neither is implied by the registry row:

  gie_extend_prof_spec      puts the public key into that parent's argument spec. Without it,
                            validate_list_of_dicts drops the key as an unknown legacy field and
                            the value never reaches the payload. No error -- a silent no-op.
  gie_contribute_nvpairs    puts the value into the parent's nvPairs in the payload builder.
                            Without it the key validates and then goes nowhere.

Both were missing for the two vPC parents when their eleven bindings were registered. The table
was correct, the engine was correct, every existing test passed, and nothing would have been
written to a vPC interface. These tests exist so that the next parent added to the table cannot
repeat it.

Offline: no controller and no device.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import re
from pathlib import Path

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    BINDING_TABLE,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    gie_extend_prof_spec,
)

MODULE = Path(gie_binding_table.__file__).resolve().parents[1] / "modules" / "dcnm_interface.py"

PARENTS = sorted({b["parent_template"] for b in BINDING_TABLE})

# The loopback parent is reached through the OSPF-MD call sites rather than a generic spec
# extension; its keys have their own dedicated validate. It is excluded here deliberately, not
# forgotten -- see the child_pti notes in the engine.
SPEC_EXEMPT = {"int_fabric_loopback_11_1"}


@pytest.fixture(scope="module")
def source():
    return MODULE.read_text()


@pytest.mark.parametrize("parent", [p for p in PARENTS if p not in SPEC_EXEMPT])
def test_every_registered_parent_has_its_spec_extended(parent, source):
    """The public key must be able to survive argument validation for this parent."""
    pattern = re.compile(
        r'gie_extend_prof_spec\([^)]*"' + re.escape(parent) + r'"', re.S
    )
    assert pattern.search(source), (
        "{0} has rows in the binding table but no gie_extend_prof_spec call. Its keys would be "
        "dropped as unknown during argument validation and nothing would reach the "
        "controller.".format(parent)
    )


def test_every_payload_builder_that_can_carry_bindings_calls_the_engine(source):
    """A builder whose parent has rows must hand the profile to the engine.

    Checked by counting call sites per function rather than per parent: a builder serves several
    parents (the three port-channel modes share one), so the meaningful invariant is that no
    builder is left out.
    """
    builders = re.findall(
        r"def (dcnm_intf_get_(?:pc|vpc|eth|loopback)_payload)\b", source
    )
    assert set(builders) == {
        "dcnm_intf_get_pc_payload",
        "dcnm_intf_get_vpc_payload",
        "dcnm_intf_get_eth_payload",
        "dcnm_intf_get_loopback_payload",
    }, "a payload builder was renamed or added; this test needs updating deliberately"

    for name in builders:
        start = source.index("def {0}".format(name))
        nxt = source.find("\n    def ", start + 1)
        body = source[start:nxt if nxt != -1 else len(source)]
        assert "gie_contribute_nvpairs(" in body, (
            "{0} never calls gie_contribute_nvpairs, so registered keys validate and then go "
            "nowhere for every parent it builds.".format(name)
        )


def test_the_vpc_specs_actually_gain_the_registered_keys():
    """Behavioural counterpart to the source check above.

    The source test proves the call exists; this proves the call does what it is there for, so a
    future refactor that keeps the call but breaks the wiring still fails.
    """
    for parent, expected in (
        ("int_vpc_trunk_host",
         {"guard_mode", "disable_lldp", "acl_filter", "spanning_tree_port_type",
          "disable_qos_stats", "disable_queuing_stats"}),
        # access does not declare GUARD_MODE, so guard_mode must NOT appear here.
        ("int_vpc_access_host",
         {"disable_lldp", "acl_filter", "spanning_tree_port_type",
          "disable_qos_stats", "disable_queuing_stats"}),
    ):
        spec = {"mode": {"required": True, "type": "str"}}
        written = {k: "x" for k in expected}
        gie_extend_prof_spec(spec, parent, written)
        gained = set(spec) - {"mode"}
        assert gained == expected, "{0}: spec gained {1}".format(parent, sorted(gained))

    spec = {"mode": {"required": True, "type": "str"}}
    gie_extend_prof_spec(spec, "int_vpc_access_host", {"guard_mode": "root"})
    assert "guard_mode" not in spec, (
        "guard_mode reached the vPC access spec; that template does not declare GUARD_MODE"
    )
