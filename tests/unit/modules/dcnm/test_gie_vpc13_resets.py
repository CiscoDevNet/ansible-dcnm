"""``int_vpc_access_host`` / ``int_vpc_trunk_host``: the thirteen resets, measured live.

Until this lot the two vPC host parents carried thirteen registered identities with no
``reset_wire``, so omitting any of them under ``replaced`` refused the whole invocation. All
thirteen are withdrawable. Six live on both parents; ``guard_mode`` is declared only by the trunk
parent, which is why the lot is thirteen and not fourteen.

WHERE THE VALUES COME FROM
Measured on 2026-09-30 in the source campaign's paired fabric (NDFC 12.6.0.267,
NX-OS 10.5(5)). Peer serials remain in the internal ALPHA evidence. Both subjects
were mounted together --
``vpc11``/``Po11`` access with member ``Ethernet1/6``, ``vpc12``/``Po12`` trunk with member
``Ethernet1/7`` -- and observed on BOTH peers::

    stage m1  all thirteen non-neutral   -> every expected line present on both peers
    stage m2  all thirteen at neutral    -> the target lines gone, prerequisites intact

NEITHER VALUE WAS TRANSFERRED FROM A SIBLING PARENT.
``int_access_host`` already carries ``acl_filter -> ''`` and ``disable_lldp_receive -> 'false'``.
That is not evidence about these parents: a reset is a property of the parent that emits it, and the
IsShow gate, the emitting child and the default can all differ. Each of the thirteen was measured on
the vPC parents themselves.

THE EMISSION PLANE IS NOT UNIFORM, AND THAT SHAPED THE MEASUREMENT
The parents emit no CLI of their own. They instantiate child PTIs and hand the nvPairs down, one per
peer: ``int_vpc_*_po_11_1`` on the port-channel and ``int_vpc_*_po_member_11_1`` on each physical
member. So::

    acl_filter, disable_qos_stats, disable_queuing_stats,
    spanning_tree_port_type, guard_mode          -> observed on Po11 / Po12
    disable_lldp_receive, disable_lldp_transmit   -> observed on Ethernet1/6 / Ethernet1/7

Looking for the LLDP lines on the port-channel would report a false negative for a field that is
working correctly, and vice versa.

THE TWO STATS FIELDS ARE A SUFFIX, NOT A LINE
``disable_qos_stats`` and ``disable_queuing_stats`` append ``" no-stats"`` to a ``service-policy``
line. Their withdrawal therefore leaves the ``service-policy`` line ALIVE and removes only the
suffix -- measured, both peers, both subjects. The clear was driven with ``enable_qos: true``,
``qos_policy`` and ``queuing_policy`` held explicit: turning QoS off would have removed the line
itself, which is destroying the prerequisite rather than withdrawing the field.

``spanning_tree_port_type`` WAS MEASURED WITH ``port_type_fast`` HELD FALSE
The emitting child branches::

    if spanningTreePortType != "" and != "no":  -> spanning-tree port type <value>
    elif PORTTYPE_FAST_ENABLED == "true":      -> spanning-tree port type edge trunk

``port_type_fast`` defaults to ``True`` in the module's own vPC profile spec. With that default in
play the neutral does not produce absence: it produces a DIFFERENT line. The parent also rejects the
combination outright with ``setFailureRetCode`` (access L560, trunk L694). Every stage therefore held
``port_type_fast: false`` explicit, so the omission under test changed exactly one thing.

WHAT THESE OFFLINE CASES COVER
They cover registration and engine decisions. The sibling
``test_gie_smu197_vpc_module_path.py`` drives the real module entry with the paired
inventory and VPC_SNO response. Neither offline test certifies the integrated tuple
on a controller or device.

Offline: no controller and no device.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    BINDING_TABLE,
    resolve_binding,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    GIE_WITHDRAW_NONE,
    GIE_WITHDRAW_RESET,
    gie_withdrawal_action,
)

VPC_ACCESS = "int_vpc_access_host"
VPC_TRUNK = "int_vpc_trunk_host"
SUPPORTED = "12.6.0.267"

# (parent, profile_key, parent_nvpair, type, reset_wire, a value evidenced as NON-reset)
#
# The `applied` column is not decoration: a withdrawal case needs a HAVE the field actually had.
# Each value here is the one the live positive stage really sent and the device really rendered --
# `normal` on access and `network` on trunk deliberately differ, so an enum that collapsed to a
# single constant could not pass by accident.
FILAS = [
    (VPC_ACCESS, "acl_filter", "aclFilter", "string", "", "pr725_vpc13_acl"),
    (VPC_ACCESS, "disable_lldp_receive", "lldpReceive", "boolean", "false", "true"),
    (VPC_ACCESS, "disable_lldp_transmit", "lldpTransmit", "boolean", "false", "true"),
    (VPC_ACCESS, "disable_qos_stats", "qosStatsSuppressed", "boolean", "false", "true"),
    (VPC_ACCESS, "disable_queuing_stats", "queuingStats", "boolean", "false", "true"),
    (VPC_ACCESS, "spanning_tree_port_type", "spanningTreePortType", "enum", "no", "normal"),
    (VPC_TRUNK, "acl_filter", "aclFilter", "string", "", "pr725_vpc13_acl"),
    (VPC_TRUNK, "disable_lldp_receive", "lldpReceive", "boolean", "false", "true"),
    (VPC_TRUNK, "disable_lldp_transmit", "lldpTransmit", "boolean", "false", "true"),
    (VPC_TRUNK, "disable_qos_stats", "qosStatsSuppressed", "boolean", "false", "true"),
    (VPC_TRUNK, "disable_queuing_stats", "queuingStats", "boolean", "false", "true"),
    (VPC_TRUNK, "spanning_tree_port_type", "spanningTreePortType", "enum", "no", "network"),
    (VPC_TRUNK, "guard_mode", "GUARD_MODE", "enum", "no", "root"),
]

CASOS = [pytest.param(*f, id="{0}-{1}".format(f[0].replace("int_vpc_", "").replace("_host", ""), f[1]))
         for f in FILAS]


def test_the_lot_is_thirteen_and_the_fixture_matches_the_table():
    """Guard the guard, before any case below can pass for the wrong reason.

    Two failure modes this closes. First, a fixture that drifts from the table: every case below
    reads its expectations from ``FILAS``, so a row silently dropped from the registry would simply
    stop being tested rather than fail. Second, a lot that grew or shrank: the campaign's claim is
    thirteen identities on these two parents, and if the table ever carries a fourteenth this case
    fails instead of the count quietly changing underneath the worklog.
    """
    en_tabla = {(r["parent_template"], r["profile_key"]) for r in BINDING_TABLE
                if r["parent_template"] in (VPC_ACCESS, VPC_TRUNK)}
    en_fixture = {(f[0], f[1]) for f in FILAS}
    assert len(FILAS) == 13, "the fixture lists {0} rows, not 13".format(len(FILAS))
    assert en_tabla == en_fixture, (
        "the table and this fixture disagree: only in table {0}, only in fixture {1}".format(
            en_tabla - en_fixture, en_fixture - en_tabla))


def test_guard_mode_is_declared_by_the_trunk_parent_only():
    """Why the lot is thirteen and not fourteen.

    ``GUARD_MODE`` is declared by ``int_vpc_trunk_host`` and NOT by ``int_vpc_access_host`` -- read
    from the installed bodies, and the reason 6 + 7 = 13. Asserting it here keeps the asymmetry
    honest: a later change that registered it on access too would make the campaign's own arithmetic
    wrong, and nothing else in this file would notice.
    """
    assert resolve_binding(VPC_TRUNK, "guard_mode") is not None
    assert resolve_binding(VPC_ACCESS, "guard_mode") is None, (
        "guard_mode appeared on the access parent; the lot is no longer 6 + 7 = 13")


@pytest.mark.parametrize("parent,key,nvpair,tipo,reset,_applied", CASOS)
def test_the_row_declares_the_measured_reset_with_the_right_type(
        parent, key, nvpair, tipo, reset, _applied):
    """The registration itself, including the PYTHON type of the reset.

    The type matters as much as the value. The controller returns these nvPairs as STRINGS, so a
    boolean reset has to be the string ``"false"`` and not native ``False``. The two are not
    interchangeable in either direction: ``False == "false"`` is False, so a comparison against the
    HAVE would never match, and in a truth test they are OPPOSITE -- the non-empty string
    ``"false"`` is truthy while native ``False`` is falsy. The same applies to ``acl_filter``, whose
    reset is the empty STRING.
    """
    b = resolve_binding(parent, key)
    assert b is not None, "{0}::{1} is not registered".format(parent, key)
    assert b["parent_nvpair"] == nvpair, (
        "{0}::{1} wire name is {2!r}, expected {3!r}".format(parent, key, b["parent_nvpair"], nvpair))
    assert b["type"] == tipo
    assert b.get("reset_wire") == reset, (
        "{0}::{1} reset is {2!r}, expected {3!r}".format(parent, key, b.get("reset_wire"), reset))
    assert isinstance(b.get("reset_wire"), str), (
        "{0}::{1} reset must be a str, got {2}".format(parent, key, type(b.get("reset_wire")).__name__))


@pytest.mark.parametrize("parent,key,_nv,_t,reset,applied", CASOS)
def test_the_engine_withdraws_a_configured_value(parent, key, _nv, _t, reset, applied):
    """A HAVE the field actually had yields the measured reset, exactly.

    ``applied`` is the value the live positive stage really sent, not a placeholder, so this asserts
    the decision the engine makes for the state the lab was really in.
    """
    assert gie_withdrawal_action(parent, key, applied, SUPPORTED) == (GIE_WITHDRAW_RESET, reset)


@pytest.mark.parametrize("parent,key,_nv,_t,reset,_applied", CASOS)
def test_the_engine_withdraws_nothing_when_the_value_already_is_the_reset(
        parent, key, _nv, _t, reset, _applied):
    """NEGATIVE CONTROL. Nothing to withdraw is not the same as withdrawing the reset.

    Without this the case above would pass for an engine that emitted the reset unconditionally,
    which would turn every converged rerun into a write. This is the assertion that makes the rerun
    idempotent rather than merely quiet.
    """
    assert gie_withdrawal_action(parent, key, reset, SUPPORTED) == (GIE_WITHDRAW_NONE, None)


@pytest.mark.parametrize("parent,key,_nv,_t,reset,applied", CASOS)
def test_the_reset_is_refused_below_the_minimum_version(parent, key, _nv, _t, reset, applied):
    """NEGATIVE CONTROL on the version axis.

    Every one of the thirteen declares ``min_ndfc_version: 12.6.0.267``. On an older controller the
    nvPair does not exist, so emitting a reset for it would write a field the template never had.
    A withdrawal that ignored the floor would look identical to a correct one on the supported
    controller, which is exactly why the floor gets its own case.
    """
    b = resolve_binding(parent, key)
    assert b["min_ndfc_version"] == SUPPORTED
    accion, valor = gie_withdrawal_action(parent, key, applied, "12.6.0.266")
    assert (accion, valor) != (GIE_WITHDRAW_RESET, reset), (
        "{0}::{1} withdrew on a controller below its declared floor".format(parent, key))


def test_the_two_parents_are_independent_identities():
    """Thirteen bindings, not two parents times a shared list.

    The six shared keys are SEPARATE rows: N proofs of one field are not N fields proved. This case
    fails if the two parents ever start resolving to the same object, which would make half the lot
    untested while every case above still passed.
    """
    compartidas = ("acl_filter", "disable_lldp_receive", "disable_lldp_transmit",
                   "disable_qos_stats", "disable_queuing_stats", "spanning_tree_port_type")
    for key in compartidas:
        a = resolve_binding(VPC_ACCESS, key)
        t = resolve_binding(VPC_TRUNK, key)
        assert a is not None and t is not None
        assert a is not t, "{0} resolves to one shared object on both parents".format(key)
        assert a["parent_template"] == VPC_ACCESS
        assert t["parent_template"] == VPC_TRUNK
        # same wire name and same reset, but reached through two distinct rows
        assert a["parent_nvpair"] == t["parent_nvpair"]
        assert a["reset_wire"] == t["reset_wire"]


def test_the_previous_lot_is_untouched():
    """The campaign's arithmetic: 128 + 13 = 141, and nothing else moved.

    A merge script that inserted a reset into the wrong row would still leave the count at 141, so
    counting alone is not enough -- the thirteen are named. ``disable_lldp`` is named too and
    asserted to have NO reset: it lives in the same slices, it is a PREFIX of
    ``disable_lldp_receive`` and ``disable_lldp_transmit``, and it is the row a substring match
    would have hit instead. It is not part of this lot and must stay unregistered.
    """
    con_reset = [r for r in BINDING_TABLE if r.get("reset_wire") is not None]
    assert len(BINDING_TABLE) == 228, "the table has {0} identities".format(len(BINDING_TABLE))
    # 197 integrated + 3 PR725-HSRP5 int_vlan rows (test_gie_hsrp3_resets.py) = 200.
    assert len(con_reset) == 200, (
        "the integrated table carries {0} resets, expected 200".format(len(con_reset)))
    nuestras = {(r["parent_template"], r["profile_key"]) for r in con_reset
                if r["parent_template"] in (VPC_ACCESS, VPC_TRUNK)}
    assert nuestras == {(f[0], f[1]) for f in FILAS}
    for parent in (VPC_ACCESS, VPC_TRUNK):
        vecina = resolve_binding(parent, "disable_lldp")
        if vecina is not None:
            assert vecina.get("reset_wire") is None, (
                "{0}::disable_lldp got a reset; it is not part of this lot and is the row a "
                "substring match on `disable_lldp` would have hit".format(parent))
