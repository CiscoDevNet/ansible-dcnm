"""The legacy path and the engine must never write the same nvPair.

Both write into the same ``nvPairs`` dict in a payload builder. The legacy path assigns each
field by hand and always writes, because every one of its keys carries a default in the argument
spec -- omitting such a key in a playbook sets the default rather than preserving anything. The
engine writes only keys the operator stated explicitly, and omission means "leave it alone".

Those two contracts are incompatible on a shared key. If a field were written by both, the
legacy assignment would put its default in before the engine decided to stay silent, and
``emit_when: explicit_only`` would quietly stop being true: omitting the key would reset the
controller's value instead of preserving it. The engine's ``update`` runs last, so the damage
would only appear on omission -- the one case no single-run test looks at.

Nothing in the code prevents the overlap. Adding a registry row for an nvPair the builder
already assigns is a two-line change that would pass every other test in this suite.

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

MODULE = Path(gie_binding_table.__file__).resolve().parents[1] / "modules" / "dcnm_interface.py"

# Which parents each payload builder serves. Kept explicit rather than derived: the mapping is
# the thing under test, and deriving it from the same source would make the test agree with
# whatever the module happens to do.
BUILDERS = {
    "dcnm_intf_get_eth_payload": (
        "int_access_host",
        "int_trunk_host",
    ),
    "dcnm_intf_get_pc_payload": (
        "int_port_channel_access_host",
        "int_port_channel_trunk_host",
        "int_port_channel_dot1q_tunnel_host",
    ),
    "dcnm_intf_get_vpc_payload": (
        "int_vpc_trunk_host",
        "int_vpc_access_host",
    ),
    "dcnm_intf_get_loopback_payload": (
        "int_fabric_loopback_11_1",
    ),
}

ASSIGN = re.compile(r'nvPairs"\]\["([A-Z0-9_]+)"\]\s*=')
UPDATE_LITERAL = re.compile(r'nvPairs"\]\.update\(\{"([A-Z0-9_]+)"')


@pytest.fixture(scope="module")
def source():
    return MODULE.read_text()


def _builder_body(source, name):
    start = source.index("def {0}".format(name))
    nxt = source.find("\n    def ", start + 1)
    return source[start:nxt if nxt != -1 else len(source)]


def _legacy_nvpairs(body):
    """nvPair names the builder writes by hand, excluding the engine's own update()."""
    return set(ASSIGN.findall(body)) | set(UPDATE_LITERAL.findall(body))


@pytest.mark.parametrize("builder,parents", sorted(BUILDERS.items()))
def test_no_registered_nvpair_is_also_written_by_hand(builder, parents, source):
    body = _builder_body(source, builder)
    legacy = _legacy_nvpairs(body)
    engine = {b["parent_nvpair"] for b in BINDING_TABLE if b["parent_template"] in parents}

    collision = legacy & engine
    assert not collision, (
        "{0} assigns {1} by hand and the engine also contributes it for {2}. The hand-written "
        "assignment runs first and always writes, so omitting the key in a playbook would set "
        "the legacy default instead of preserving the controller's value -- explicit_only would "
        "no longer hold. Either drop the registry row or remove the hand-written "
        "assignment.".format(builder, sorted(collision), ", ".join(parents))
    )


def test_every_builder_actually_writes_something_by_hand(source):
    """Guard the guard.

    If the extraction regexes ever stop matching -- a refactor to a helper, a renamed local --
    every test above would pass on an empty set and prove nothing. A builder that assigns no
    nvPair at all is far more likely to mean the extraction broke than that the builder changed.
    """
    for builder in BUILDERS:
        legacy = _legacy_nvpairs(_builder_body(source, builder))
        assert len(legacy) >= 5, (
            "{0}: found only {1} hand-written nvPairs. The collision test above is only "
            "meaningful while this extraction works; this count dropping means the regexes no "
            "longer match how the builder writes.".format(builder, len(legacy))
        )


def test_every_registered_parent_belongs_to_exactly_one_builder():
    """A parent with rows but no builder in the map would be silently unchecked above."""
    registered = {b["parent_template"] for b in BINDING_TABLE}
    mapped = {p for parents in BUILDERS.values() for p in parents}

    assert registered <= mapped, (
        "these parents have rows in the binding table but no builder in BUILDERS, so the "
        "collision check never runs for them: {0}".format(sorted(registered - mapped))
    )

    counts = {}
    for parents in BUILDERS.values():
        for p in parents:
            counts[p] = counts.get(p, 0) + 1
    dupes = [p for p, n in counts.items() if n > 1]
    assert not dupes, "a parent is mapped to more than one builder: {0}".format(sorted(dupes))
