"""A plain-string binding must be clearable with the empty string.

``ACL_FILTER`` was settable and never clearable. The registry copies ``min_length: 1`` from
the template's ``metaProperties``, and the validator applied it to explicit input, so ``""``
was rejected before the module sent anything. There was no other way out either: a re-deploy
does not clear the field because NaC does not model it, so ``vxlan.yaml`` walks past the value
and it survives. The field was one-way.

The controller does not agree with that restriction. Measured on NDFC 12.6.0.267: POSTing
``ACL_FILTER: ""`` for ``port-channel31`` to ``/interface/modify`` returned 207 SUCCESS, the
controller stored ``""``, and after deploy ``ip port access-group`` was gone from the device
while the untouched ``port-channel32`` kept its own. ``""`` is also the exact encoding NDFC
returns for "no ACL configured" -- the same value its own template claims is too short.

Evidence: evidence/generic-interface-engine/phase18-acl-empty-probe.

Two things are deliberately NOT relaxed, and are asserted here so a future edit cannot widen
the hole by accident:

  * an ENUM still rejects ``""``. For an enum the "off" state is a named choice
    (``GUARD_MODE`` ``"no"``), so an empty enum is a typo, not an intent to clear.
  * ``max_length`` still applies. Only the lower bound has a documented meaning as "unset".

Offline: no controller and no device.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    resolve_binding,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    GieBindingError,
    gie_validate_binding_value,
)

# Every registered plain-string binding, i.e. the ones an operator must be able to clear.
STRING_BINDINGS = [
    ("int_access_host", "acl_filter"),
    ("int_trunk_host", "acl_filter"),
    ("int_port_channel_access_host", "acl_filter"),
    ("int_port_channel_trunk_host", "acl_filter"),
    ("int_port_channel_dot1q_tunnel_host", "acl_filter"),
    ("int_vpc_access_host", "acl_filter"),
    ("int_vpc_trunk_host", "acl_filter"),
]


@pytest.mark.parametrize("parent,key", STRING_BINDINGS)
def test_explicit_empty_string_clears_a_plain_string_binding(parent, key):
    """The operator writes "" to remove the value. This is the fix."""
    assert gie_validate_binding_value(parent, key, "", value_source="explicit") == ""


@pytest.mark.parametrize("parent,key", STRING_BINDINGS)
def test_controller_empty_string_still_round_trips(parent, key):
    """Unchanged behaviour: the carry-forward reads "" back from HAVE."""
    assert gie_validate_binding_value(parent, key, "", value_source="have") == ""


@pytest.mark.parametrize("parent,key", STRING_BINDINGS)
def test_the_binding_really_carries_a_min_length(parent, key):
    """Guard the guard.

    These cases only mean something while the registry still declares ``min_length``. If a
    future regeneration dropped it, the tests above would pass for the wrong reason -- not
    because the exemption works, but because there was nothing left to exempt.
    """
    binding = resolve_binding(parent, key)
    assert binding is not None, "{0}::{1} is not registered".format(parent, key)
    assert binding.get("min_length") == 1, (
        "{0}::{1} no longer declares min_length 1, so the empty-string cases above no "
        "longer prove the exemption is what lets them through".format(parent, key)
    )


def test_an_enum_still_rejects_the_empty_string():
    """Scope of the exemption: enums fail closed.

    ``GUARD_MODE`` expresses "off" as the named choice ``"no"``. An empty value there is a
    mistake, and letting it through would send a value the template never declared.
    """
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(
            "int_trunk_host", "guard_mode", "", value_source="explicit"
        )


def test_max_length_still_applies_to_a_string_binding():
    """Only the lower bound means "unset"; the upper bound is a real constraint."""
    binding = resolve_binding("int_access_host", "acl_filter")
    too_long = "x" * (binding["max_length"] + 1)
    with pytest.raises(GieBindingError):
        gie_validate_binding_value(
            "int_access_host", "acl_filter", too_long, value_source="explicit"
        )


def test_a_short_but_nonempty_string_is_still_accepted():
    """The exemption is for "" exactly, not for "anything below min_length"."""
    assert (
        gie_validate_binding_value(
            "int_access_host", "acl_filter", "A", value_source="explicit"
        )
        == "A"
    )
