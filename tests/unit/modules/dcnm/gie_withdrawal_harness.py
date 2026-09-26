"""Shared harness for the generic-interface-engine withdrawal acceptance tests.

Self-contained: it imports only from this collection and its declared test
dependencies. Nothing here reaches into a research directory or an absolute path, so a
clean checkout carries its own acceptance tests.

WHAT IT DRIVES

Every integration helper enters through the module's real `main()`: real argument spec,
real per-type profile validation, real builder, real `gie_contribute_nvpairs`, real
comparator, real serialisation. Mocks sit only at the external boundary -- inventory,
transport and sleep. Assertions belong to the caller and are made against the CAPTURED
REQUEST and the PUBLIC DIFF, never against `changed` alone: the module was measured
sending more than it reported, and a test that trusts `changed` cannot see that.

CLEANUP IS OWNED, NOT GLOBAL

`A161Base` stops the patchers it starts in its own `tearDown`, but `netcommon`'s
`ModuleTestCase.setUp` registers the removal of its `exit_json`/`fail_json` doubles with
`addCleanup`, which runs from `doCleanups()` -- a method a hand-driven TestCase never
calls on its own. Every case below therefore runs `tearDown()` and then `doCleanups()`,
both on success and on an exception, so this harness restores exactly what it installed
and nothing else. A blanket `patch.stopall()` would also stop patches the harness never
started; `test_withdrawal_harness_cleanup.py` pins that difference.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import contextlib
import copy
import io
import json

from unittest.mock import patch

from ansible.module_utils import basic

from ansible_collections.ansible.netcommon.tests.unit.modules.utils import (
    AnsibleExitJson,
    AnsibleFailJson,
)
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from .dcnm_module import set_module_args
from .test_dcnm_intf_binding_module_path import A161Base

# Captured before any TestCase installs the netcommon doubles. Module import happens at
# collection time, so these are the genuine implementations; `real_serialiser_is_genuine`
# turns a wrong capture into a loud failure rather than a silently vacuous assertion.
REAL_EXIT_JSON = basic.AnsibleModule.exit_json
REAL_FAIL_JSON = basic.AnsibleModule.fail_json

SERIAL = "SAL1819SAN8"          # the fixture inventory's serial for SWITCH_IP
SWITCH_IP = "10.0.0.1"
FABRIC = "test_fabric"
IF_A = "Ethernet1/31"
IF_B = "Ethernet1/32"
# The subinterface drives `type: sub_int` on a dotted name. `3001` is the dot1q
# ENCAPSULATION on this interface, which `vlan` carries; it is not a fabric VLAN object.
IF_SUB = "Ethernet1/31.3001"
SUB_VLAN = 3001
# A SYNTHETIC loopback number and a documentation-range address. The live G41 batch used
# loopback193 with 192.0.2.193/32; a fixture must not carry the lab object's identity.
IF_LO = "loopback931"
IF_SVI = "Vlan931"

ACCESS = "int_access_host"
TRUNK = "int_trunk_host"
ROUTED = "int_routed_host"
SUBIF = "int_subif"
# The USER loopback parent. The module keeps two loopback parents apart -- "lo_lo" ->
# int_loopback and "lo_fabric" -> int_fabric_loopback_11_1 -- and this is the first: a user
# loopback the fabric does not own. Driving it as `eth` would resolve a different policy, so it
# gets its own type and name like the subinterface and port-channel parents do.
LOOPBACK = "int_loopback"
# The SVI parent. Its config is `type: svi` on a `Vlan<id>` name, and the VLAN id travels in the
# NAME -- `dcnm_intf_get_svi_payload` extracts it from there and writes no `VLAN` nvPair, unlike
# the subinterface path. A synthetic id, never the lab object's 3784.
SVI = "int_vlan"

# The port-channel host family. Unlike every parent above, these drive `type: pc` configs
# whose interface NAME is a Port-channel. Both follow the parent, which is why
# `iftype_for`/`ifname_for` exist rather than a hardcoded "eth" in `cfg`.
PC_ACCESS = "int_port_channel_access_host"
PC_TRUNK = "int_port_channel_trunk_host"
PC_DOT1Q = "int_port_channel_dot1q_tunnel_host"
PC_PARENTS = (PC_ACCESS, PC_TRUNK, PC_DOT1Q)

# Parents whose config is NOT an `eth` on `IF_A`. Every place that used to ask
# `parent in PC_PARENTS` to decide "does this config need a different type/name?" asks this
# instead, so adding the subinterface parent could not leave one of those places behind
# silently building an ethernet config and measuring the wrong policy.
NON_ETH_PARENTS = PC_PARENTS + (SUBIF, LOOPBACK, SVI)

PC_A = "Port-channel301"
PC_MEMBER = "Ethernet1/50"

SUPPORTED = "12.6.0.267"
BELOW = "12.6.0.266"

# EVERY registered reset identity on the ethernet host parents -- 17 on access/trunk plus
# the two routed redirect rows, not the original five. Each entry is
# (profile_key, applied, reset_wire, prerequisite_profile_fields).
#
# `applied` is a value independently evidenced as non-reset for that binding; `reset` is
# the wire string the registry carries, measured live in G19/G22 (access/trunk) and in G31
# C1-s2/C2-s2 (the routed redirects). The fourth element carries the prerequisites a gated
# row needs, because the template hides the field otherwise: the stats pair needs an
# effective service-policy, and spanning-tree port type is only settable while
# PORTTYPE_FAST_ENABLED is not true. Those fields stay explicit across the whole case, so
# the omission under test changes exactly one thing.
#
# THE REDIRECT PAIR'S PREREQUISITE IS ITS OWN COMPANION, NOT A NATIVE FIELD.
# Both split rows are declared `IsShow="DISABLE_IP_REDIRECTS!=true"`, and on
# int_routed_host that gate field is NOT in the module's native profile spec -- it sits at
# the template default `false`, which the live P0/FRESH captures confirm. So nothing has to
# be sent to keep the global override false here; what must stay explicit is the OTHER
# direction, so a reset of one is never confused with the pair collapsing together. That
# mirrors the live measurement exactly: companion explicitly true, global false.
QOS = {"enable_qos": True, "qos_policy": "pilot_qos"}
QUEUE = {"queuing_policy": "pilot_queue"}
NOFAST = {"port_type_fast": False}
IPV6_ON = {"disable_ipv6_redirects": True}
IPV4_ON = {"disable_ipv4_redirects": True}
# The OSPF base group the template makes mandatory under its gate: OSPF_TAG and
# OSPF_AREA_ID carry IsMandatory="ENABLE_OSPF==true", and they feed the same base child as
# the gate itself. Every OSPF value row therefore holds all three explicit, so the omission
# under test is the only moving part. The tag here is SYNTHETIC on purpose -- the live batch
# used an operator-authorised process, and a fixture must not carry a lab resource name.
OSPF_CTX = {"enable_ospf": True, "ospf_tag": "PILOT-OSPF", "ospf_area_id": "0.0.0.0"}


def an_unclassifiable_key(parent, wanted_type=None):
    """A profile key on `parent` that carries NEITHER a reset nor a declared default.

    Three tests need "a registered row about which nothing is known", and each named one
    explicitly. Both times a campaign measured that row, the tests broke and had to be rehomed
    by hand -- `access disable_lldp_receive` once, and the whole routed OSPF set in G37. Deriving
    the example from the live table ends that: registering more rows can never invalidate it, and
    if the table ever ran out of unclassifiable rows the assertion below would say so loudly
    instead of the tests quietly passing for the wrong reason.
    """
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
        BINDING_TABLE,
    )
    rows = [b for b in BINDING_TABLE
            if b["parent_template"] == parent
            and b.get("reset_wire") is None
            and b.get("default_template") is None
            and not b.get("no_log")
            and (wanted_type is None or b["type"] == wanted_type)]
    assert rows, (
        "no row on %s has neither a reset nor a declared default%s, so the unclassifiable "
        "case can no longer be exercised on this parent -- rehome it deliberately rather than "
        "letting these tests pass vacuously"
        % (parent, "" if wanted_type is None else " of type %s" % wanted_type))

    # DRIVABILITY IS PART OF THE CHOICE. Being unclassifiable in the table is not enough: the
    # row must also be one this harness can actually configure standalone. The first candidate
    # alphabetically, `dampening_half_life`, is refused by input validation, so a naive
    # "sorted()[0]" picks the one row that cannot drive the case at all. Each candidate is
    # therefore tried, and the first that yields a well-formed single-policy HAVE wins.
    tried = []
    for key in sorted(r["profile_key"] for r in rows):
        probe = 100 if _row_type(parent, key) == "integer" else "PILOT-UNCLASSIFIED"
        try:
            build_have(parent, key, probe)
        except Exception as exc:                      # noqa: BLE001 - any refusal disqualifies
            tried.append("%s (%s)" % (key, type(exc).__name__))
            continue
        return key
    raise AssertionError(
        "every unclassifiable row on %s was undrivable: %s" % (parent, ", ".join(tried)))


def _row_type(parent, profile_key):
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
        BINDING_TABLE,
    )
    for b in BINDING_TABLE:
        if b["parent_template"] == parent and b["profile_key"] == profile_key:
            return b["type"]
    return None


def wire_of(applied):
    """The wire form the controller stores for a fixture's `applied` value.

    nvPairs is a string-valued map, so the wire form is what a preservation assertion must
    compare against. This used to be spelled inline as `applied if isinstance(applied, str)
    else "true"`, which was correct only while every non-string fixture was a boolean set to
    True. An integer fixture would have been asserted to preserve as the string "true".
    """
    if isinstance(applied, bool):
        return "true" if applied else "false"
    if isinstance(applied, int):
        return str(applied)
    return applied


def is_integer_binding(applied):
    """True for a native-integer fixture. `bool` is a subclass of `int`, so it is excluded
    first -- the distinction matters because the public integer input REFUSES the empty
    string, which is exactly why an integer reset had to be measured through a raw request."""
    return isinstance(applied, int) and not isinstance(applied, bool)


PILOT = {
    (ACCESS, "aclFilter"): ("acl_filter", "ACL-PILOT", "", {}),
    (ACCESS, "DISABLE_LLDP_TRANSMIT"): ("disable_lldp_transmit", True, "false", {}),
    (ACCESS, "DISABLE_LLDP_RECEIVE"): ("disable_lldp_receive", True, "false", {}),
    (ACCESS, "flowcontrolReceive"): ("flowcontrol_receive", "on", "off", {}),
    (ACCESS, "flowcontrolSend"): ("flowcontrol_send", "on", "off", {}),
    (ACCESS, "DISABLE_QOS_STATS"): ("disable_qos_stats", True, "false", dict(QOS)),
    (ACCESS, "DISABLE_QUEUING_STATS"): ("disable_queuing_stats", True, "false", dict(QUEUE)),
    (ACCESS, "spanningTreePortType"): ("spanning_tree_port_type", "network", "no", dict(NOFAST)),
    (TRUNK, "aclFilter"): ("acl_filter", "ACL-PILOT", "", {}),
    (TRUNK, "DISABLE_LLDP_TRANSMIT"): ("disable_lldp_transmit", True, "false", {}),
    (TRUNK, "DISABLE_LLDP_RECEIVE"): ("disable_lldp_receive", True, "false", {}),
    (TRUNK, "flowcontrolReceive"): ("flowcontrol_receive", "on", "off", {}),
    (TRUNK, "flowcontrolSend"): ("flowcontrol_send", "on", "off", {}),
    (TRUNK, "DISABLE_QOS_STATS"): ("disable_qos_stats", True, "false", dict(QOS)),
    (TRUNK, "DISABLE_QUEUING_STATS"): ("disable_queuing_stats", True, "false", dict(QUEUE)),
    (TRUNK, "GUARD_MODE"): ("guard_mode", "root", "no", {}),
    (TRUNK, "spanningTreePortType"): ("spanning_tree_port_type", "network", "no", dict(NOFAST)),
    (ROUTED, "DISABLE_IPV4_REDIRECTS"): ("disable_ipv4_redirects", True, "false", dict(IPV6_ON)),
    (ROUTED, "DISABLE_IPV6_REDIRECTS"): ("disable_ipv6_redirects", True, "false", dict(IPV4_ON)),
    # The routed stats pair. Same prerequisites as on access/trunk -- the fields are
    # IsShow-gated on ENABLE_QOS==true and QUEUING_POLICY!='' respectively -- but the CLI
    # effect differs in kind: the withdrawal does not delete a line, it removes the
    # ` no-stats` FRAGMENT and leaves the `service-policy` line standing. Measured live in
    # G33 F1-s2/F2-s2 on Leaf-103 Ethernet1/22.
    (ROUTED, "DISABLE_QOS_STATS"): ("disable_qos_stats", True, "false", dict(QOS)),
    (ROUTED, "DISABLE_QUEUING_STATS"): ("disable_queuing_stats", True, "false", dict(QUEUE)),
    # The subinterface pair, measured on int_subif ITSELF in G35 M1-s2/M2-s2 -- the routed
    # parent's result was not carried over. Same companion-held-explicit prerequisite: the
    # gate field DISABLE_IP_REDIRECTS is absent from `sub_prof_spec` too and sits at the
    # template default `false`, which the live capture confirms.
    (SUBIF, "DISABLE_IPV4_REDIRECTS"): ("disable_ipv4_redirects", True, "false", dict(IPV6_ON)),
    (SUBIF, "DISABLE_IPV6_REDIRECTS"): ("disable_ipv6_redirects", True, "false", dict(IPV4_ON)),
    # The first INTEGER row in this matrix. `applied` is a native int and `reset` is the empty
    # string, measured live in G37 P1-arp-probe on Leaf-103 Ethernet1/22. It is ungated: the
    # template declares ARP_TIMEOUT without IsShow, so nothing has to be opened to observe it,
    # and its emission gate is `if arpTimeout != ""` -- which is why "" is the withdrawal
    # representation rather than a guess.
    (ROUTED, "arpTimeout"): ("arp_timeout", 900, "", {}),
    # The five routed OSPF integers, each measured live in G37 on Leaf-103 Ethernet1/20 with the
    # reset observed as the EMPTY STRING and the OSPF association kept. All are gated, so each
    # holds the OSPF base group explicit; all are integers, so each also pins the guarantee that
    # the public empty string stays REFUSED.
    (ROUTED, "ospfCost"): ("ospf_cost", 42, "", dict(OSPF_CTX)),
    (ROUTED, "ospfDeadInterval"): ("ospf_dead_interval", 44, "", dict(OSPF_CTX)),
    (ROUTED, "ospfHelloInterval"): ("ospf_hello_interval", 11, "", dict(OSPF_CTX)),
    (ROUTED, "ospfPriority"): ("ospf_priority", 77, "", dict(OSPF_CTX)),
    (ROUTED, "ospfTransmitDelay"): ("ospf_transmit_delay", 3, "", dict(OSPF_CTX)),
    # The seven int_subif integers, measured live in G39 on Leaf-103 Ethernet1/21.3001. The six
    # OSPF rows hold the subinterface's OWN OSPF base group; ARP_TIMEOUT is ungated and was
    # measured on a deliberately OSPF-free object, so it carries no prerequisite at all.
    # `OSPF_RETRANSMIT_INTERVAL` exists on int_subif, int_vlan and int_loopback but NOT on
    # int_routed_host, which is why it had no counterpart in the routed batch.
    (SUBIF, "ospfCost"): ("ospf_cost", 42, "", dict(OSPF_CTX)),
    (SUBIF, "ospfDeadInterval"): ("ospf_dead_interval", 44, "", dict(OSPF_CTX)),
    (SUBIF, "ospfHelloInterval"): ("ospf_hello_interval", 11, "", dict(OSPF_CTX)),
    (SUBIF, "ospfPriority"): ("ospf_priority", 77, "", dict(OSPF_CTX)),
    (SUBIF, "ospfTransmitDelay"): ("ospf_transmit_delay", 3, "", dict(OSPF_CTX)),
    (SUBIF, "ospfRetransmitInterval"): ("ospf_retransmit_interval", 9, "", dict(OSPF_CTX)),
    (SUBIF, "arpTimeout"): ("arp_timeout", 900, "", {}),
    # int_loopback. Same six OSPF integers, same measured reset -- but measured on THIS parent
    # in G41, not inherited from the subinterface: G39 showed even the envelope differs between
    # parents. The context is held explicit for the same reason it is on subif, and because on
    # this parent an omitted OSPF_TAG makes the template fall back to the FABRIC's process.
    (LOOPBACK, "ospfCost"): ("ospf_cost", 42, "", dict(OSPF_CTX)),
    (LOOPBACK, "ospfDeadInterval"): ("ospf_dead_interval", 44, "", dict(OSPF_CTX)),
    (LOOPBACK, "ospfHelloInterval"): ("ospf_hello_interval", 11, "", dict(OSPF_CTX)),
    (LOOPBACK, "ospfPriority"): ("ospf_priority", 77, "", dict(OSPF_CTX)),
    (LOOPBACK, "ospfTransmitDelay"): ("ospf_transmit_delay", 3, "", dict(OSPF_CTX)),
    (LOOPBACK, "ospfRetransmitInterval"): ("ospf_retransmit_interval", 9, "", dict(OSPF_CTX)),
    # int_vlan. The six OSPF integers behave as on the other parents, but the two SPLIT REDIRECT
    # rows are BOOLEAN and their measured reset is the STRING 'false', not the empty string --
    # measured live in G43, not inferred. Each holds the OTHER split knob true so the shared
    # child survives and only the target's own CLI line is withdrawn.
    (SVI, "ospfCost"): ("ospf_cost", 42, "", dict(OSPF_CTX)),
    (SVI, "ospfDeadInterval"): ("ospf_dead_interval", 44, "", dict(OSPF_CTX)),
    (SVI, "ospfHelloInterval"): ("ospf_hello_interval", 11, "", dict(OSPF_CTX)),
    (SVI, "ospfPriority"): ("ospf_priority", 77, "", dict(OSPF_CTX)),
    (SVI, "ospfTransmitDelay"): ("ospf_transmit_delay", 3, "", dict(OSPF_CTX)),
    (SVI, "ospfRetransmitInterval"): ("ospf_retransmit_interval", 9, "", dict(OSPF_CTX)),
    (SVI, "arpTimeout"): ("arp_timeout", 900, "", {}),
    (SVI, "DISABLE_IPV4_REDIRECTS"): ("disable_ipv4_redirects", True, "false",
                                      {"disable_ipv6_redirects": True}),
    (SVI, "DISABLE_IPV6_REDIRECTS"): ("disable_ipv6_redirects", True, "false",
                                      {"disable_ipv4_redirects": True}),
}
PILOT_IDS = ["%s::%s" % (p, n) for (p, n) in PILOT]
PILOT_ITEMS = [(p, n, k, applied, reset, extra)
               for (p, n), (k, applied, reset, extra) in PILOT.items()]

# The port-channel host family -- the 19 ORDINARY identities of BETA's C3 packet 01,
# measured live in G25 batch B1 on Leaf-101 (Po301/302/303).
#
# The twentieth identity, PC_TRUNK::ENABLE_VPC_PEER_LINK, is deliberately ABSENT. It is a
# ROLE CHANGE, not an ordinary field: setting it true makes the port-channel a vPC
# peer-link. It was never run and carries no measured reset, so it must not appear here --
# `test_the_fixture_matrix_covers_every_registered_row` below turns that absence into a
# real guarantee by failing if it were ever registered without a fixture.
#
# The two LLDP rows are `line_gated_in_child`: the host FORWARDS the value and the CLI
# line renders on the MEMBER interface, not on the port-channel. The contract under test
# here is the nvPair on the parent request, which is the same either way; the member-side
# rendering is what the live campaign verified on the device.
PILOT_PC = {
    (PC_ACCESS, "aclFilter"): ("acl_filter", "ACL-PILOT", "", {}),
    (PC_ACCESS, "DISABLE_LLDP_TRANSMIT"): ("disable_lldp_transmit", True, "false", {}),
    (PC_ACCESS, "DISABLE_LLDP_RECEIVE"): ("disable_lldp_receive", True, "false", {}),
    (PC_ACCESS, "DISABLE_QOS_STATS"): ("disable_qos_stats", True, "false", dict(QOS)),
    (PC_ACCESS, "DISABLE_QUEUING_STATS"): ("disable_queuing_stats", True, "false", dict(QUEUE)),
    (PC_ACCESS, "spanningTreePortType"): ("spanning_tree_port_type", "network", "no", dict(NOFAST)),
    (PC_TRUNK, "aclFilter"): ("acl_filter", "ACL-PILOT", "", {}),
    (PC_TRUNK, "DISABLE_LLDP_TRANSMIT"): ("disable_lldp_transmit", True, "false", {}),
    (PC_TRUNK, "DISABLE_LLDP_RECEIVE"): ("disable_lldp_receive", True, "false", {}),
    (PC_TRUNK, "DISABLE_QOS_STATS"): ("disable_qos_stats", True, "false", dict(QOS)),
    (PC_TRUNK, "DISABLE_QUEUING_STATS"): ("disable_queuing_stats", True, "false", dict(QUEUE)),
    (PC_TRUNK, "GUARD_MODE"): ("guard_mode", "root", "no", {}),
    (PC_TRUNK, "spanningTreePortType"): ("spanning_tree_port_type", "network", "no", dict(NOFAST)),
    (PC_DOT1Q, "aclFilter"): ("acl_filter", "ACL-PILOT", "", {}),
    (PC_DOT1Q, "DISABLE_LLDP_TRANSMIT"): ("disable_lldp_transmit", True, "false", {}),
    (PC_DOT1Q, "DISABLE_LLDP_RECEIVE"): ("disable_lldp_receive", True, "false", {}),
    (PC_DOT1Q, "DISABLE_QOS_STATS"): ("disable_qos_stats", True, "false", dict(QOS)),
    (PC_DOT1Q, "DISABLE_QUEUING_STATS"): ("disable_queuing_stats", True, "false", dict(QUEUE)),
    (PC_DOT1Q, "spanningTreePortType"): ("spanning_tree_port_type", "network", "no", dict(NOFAST)),
}
PILOT_PC_IDS = ["%s::%s" % (p, n) for (p, n) in PILOT_PC]
PILOT_PC_ITEMS = [(p, n, k, applied, reset, extra)
                  for (p, n), (k, applied, reset, extra) in PILOT_PC.items()]

# The combined matrix. Tests parametrized over this cover ethernet and port-channel in one
# pass, so a contract that holds for one and not the other cannot hide.
PILOT_ALL = dict(PILOT)
PILOT_ALL.update(PILOT_PC)
PILOT_ALL_IDS = ["%s::%s" % (p, n) for (p, n) in PILOT_ALL]
PILOT_ALL_ITEMS = [(p, n, k, applied, reset, extra)
                   for (p, n), (k, applied, reset, extra) in PILOT_ALL.items()]

BASE_ACCESS = {"mode": "access", "description": "pilot", "fec": "auto",
               "enable_qos": True, "qos_policy": "pilot_qos"}
BASE_TRUNK = {"mode": "trunk", "description": "pilot", "fec": "auto"}

# Port-channel bases. `fec` is NOT in the port-channel profile spec, so it is absent here
# rather than copied from the ethernet bases. `members` stays a single explicit member for
# the same reason the live campaign used one: it keeps the membership fixed so the only
# moving part is the field under test.
BASE_PC_ACCESS = {"mode": "access", "description": "pilot", "members": [PC_MEMBER],
                  "pc_mode": "active", "enable_qos": True, "qos_policy": "pilot_qos"}
BASE_PC_TRUNK = {"mode": "trunk", "description": "pilot", "members": [PC_MEMBER],
                 "pc_mode": "active"}
BASE_PC_DOT1Q = {"mode": "dot1q", "description": "pilot", "members": [PC_MEMBER],
                 "pc_mode": "active"}
# Distinguishes "the caller said nothing" from "the caller said None". `None` is a real
# case -- an unreachable controller whose version could not be determined -- and the
# boundary must fail closed on it, so it cannot share a default with "unspecified".
_UNSET = object()

# The subinterface base. Built from `sub_prof_spec`, NOT copied from an ethernet base: there
# is no `fec` here (the subif spec does not declare it), no `enable_ospf`, and deliberately NO
# IP -- an offline real-main probe confirmed the object is creatable with none, and the live
# G35 create emitted IP='' / PREFIX=''. `vlan` is the only field the argspec requires.
#
# `ipv4_addr`/`ipv4_mask_len` are `required=False` with NO argspec default, the same hazard
# class as `fec` on the routed parent. They are left out entirely rather than pinned, because
# the probe showed this profile transmits no native `None` at all.
BASE_SUBIF = {"mode": "subint", "vlan": SUB_VLAN, "int_vrf": "default", "mtu": 9216,
              "description": "pilot", "admin_state": True, "route_tag": "", "speed": "Auto"}

BASE_LOOPBACK = {"mode": "lo", "int_vrf": "default", "ipv4_addr": "192.0.2.131",
                 "description": "pilot", "admin_state": True, "route_tag": "", "speed": "Auto"}

# The ADDRESSLESS SVI base. `disable_ip_redirects` is explicit False because its argspec default
# is True and both split redirect rows are hidden while it is true -- omitting it would silently
# hide the very rows under test. `adv_subnet_in_underlay` is explicit False because the keymap
# defect at dcnm_interface.py:2360 means `merged` could not correct a wrong HAVE value later.
BASE_SVI = {"mode": "vlan", "int_vrf": "default", "mtu": 9216, "admin_state": True,
            "description": "pilot", "route_tag": "",
            "disable_ip_redirects": False, "adv_subnet_in_underlay": False}

BASE_ROUTED = {"mode": "routed", "description": "pilot", "fec": "auto",
               "ipv4_addr": "192.0.2.1", "ipv4_mask_len": 30,
               "enable_ospf": True, "ospf_area_id": "0.0.0.0"}


def base_for(parent, **extra):
    """A representative profile for `parent`.

    `fec` is dropped whenever a caller overrides the version: it carries its own
    pre-existing NDFC >= 12.4.1 requirement, and letting that legacy check fail a
    version case would attribute an old problem to this contract.
    """
    base = {TRUNK: BASE_TRUNK, ROUTED: BASE_ROUTED, SUBIF: BASE_SUBIF,
            PC_ACCESS: BASE_PC_ACCESS, PC_TRUNK: BASE_PC_TRUNK,
            PC_DOT1Q: BASE_PC_DOT1Q, LOOPBACK: BASE_LOOPBACK,
            SVI: BASE_SVI}.get(parent, BASE_ACCESS)
    prof = dict(base)
    prof.update(extra)
    return prof


def iftype_for(parent):
    """The module's `type` for a parent. A port-channel driven as `eth` is not a weaker
    test, it is a different object: the module would resolve a different policy."""
    if parent in PC_PARENTS:
        return "pc"
    if parent == LOOPBACK:
        return "lo"
    if parent == SVI:
        return "svi"
    return "sub_int" if parent == SUBIF else "eth"


def ifname_for(parent):
    """The interface name to drive. A `pc` config named Ethernet1/31 is rejected, and a
    `sub_int` config needs the dotted name -- an undotted one resolves a different policy."""
    if parent in PC_PARENTS:
        return PC_A
    if parent == LOOPBACK:
        return IF_LO
    if parent == SVI:
        return IF_SVI
    return IF_SUB if parent == SUBIF else IF_A


def cfg(ifname, profile, deploy=True, iftype="eth"):
    return {"name": ifname, "type": iftype, "switch": [SWITCH_IP],
            "deploy": deploy, "profile": copy.deepcopy(profile)}


def cfg_for(parent, profile, deploy=True):
    """`cfg` with the interface name AND type both taken from the parent."""
    return cfg(ifname_for(parent), profile, deploy=deploy, iftype=iftype_for(parent))


@contextlib.contextmanager
def harness_case(ndfc_version=_UNSET):
    """An `A161Base` driven by hand, with cleanup this harness owns.

    `ndfc_version` is set on the INSTANCE, never on the class: a class attribute would
    outlive the case and silently retune every later test in the session.
    """
    test = A161Base(methodName="runTest")
    if ndfc_version is not _UNSET:
        test.ndfc_version = ndfc_version

    # setUp() is INSIDE the try. `A161Base.setUp` starts six patchers one after another
    # and `ModuleTestCase.setUp` registers its cleanups as it goes, so a failure partway
    # through leaves some of them already installed. With setUp outside the try that
    # failure propagated before any cleanup could run, and the netcommon doubles stayed
    # live for the rest of the session -- the leak this contract exists to prevent,
    # reappearing on the one path where something had already gone wrong.
    setup_completed = False
    try:
        test.setUp()
        setup_completed = True
        yield test
    finally:
        # doCleanups() runs UNCONDITIONALLY, including after a partial setUp: it unwinds
        # exactly the cleanups that were registered, which is precisely the set that was
        # installed. tearDown() runs ONLY if setUp completed -- on a half-built case it
        # would raise AttributeError for a patcher that was never started and mask the
        # real error. Neither call may be replaced by patch.stopall(): that would also
        # stop patches this harness never installed.
        try:
            if setup_completed:
                test.tearDown()
        finally:
            test.doCleanups()


def _transport(calls, have):
    def send(mod, method, path, payload=None):
        parsed = json.loads(payload) if isinstance(payload, str) else copy.deepcopy(payload)
        calls.append({"method": method, "path": path, "payload": parsed})
        if method == "GET":
            if "readonly" in path or "accessmode" in path.lower():
                return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {"readonly": False}}
            if "/interface?" in path:
                return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": copy.deepcopy(have)}
            if "/interface/detail" in path:
                # Shaped from a REAL capture, not invented: on controller 12.6.0.267 both a
                # physical port and a subinterface come back with
                # `ifType: "INTERFACE_ETHERNET"`, and `isPhysical` is a STRING -- `'true'` for
                # the physical port, `'false'` for the subinterface -- never a native bool.
                # The old double hardcoded `isPhysical: True`, which was the wrong TYPE for
                # every parent and the wrong VALUE for a subinterface; a subinterface test
                # driven against it would have been asserting a response NDFC never sends.
                # Evidence: evidence/W2/G35-subif-pair/baseline/K1POST-detail-all.json.
                return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [
                    {"ifName": i["ifName"], "serialNo": i["serialNumber"],
                     "fabricName": FABRIC,
                     # Shapes taken from REAL captures: a loopback comes back
                     # INTERFACE_LOOPBACK and an SVI INTERFACE_VLAN, both with `isPhysical` the
                     # STRING 'false' (G41 and G43 live detail reads).
                     "ifType": {LOOPBACK: "INTERFACE_LOOPBACK",
                                SVI: "INTERFACE_VLAN"}.get(p.get("policy"),
                                                          "INTERFACE_ETHERNET"),
                     "isPhysical": ("false" if p.get("policy") in (SUBIF, LOOPBACK, SVI)
                                    else "true"),
                     "markDeleted": False, "alias": "",
                     "deleteReason": "", "complianceStatus": "In-Sync",
                     "underlayPolicies": []}
                    for p in have for i in p["interfaces"]]}
            return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": []}
        return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": []}
    return send


def run_configs(configs, state, have=None, deploy=True, check_mode=False,
                allow_failed=True, ndfc_version=_UNSET, extra_patch=None):
    """Drive real `main()` over one or more interface configs.

    Returns (result, calls). `calls` is every intercepted REST call, in order, so the
    caller can separate reads from updates and deploys.
    """
    calls = []
    have = copy.deepcopy(have or [])
    with harness_case(ndfc_version) as test:
        test.load_fixtures()
        test.run_bulk.return_value = True
        test.run_send.side_effect = _transport(calls, have)
        args = {"state": state, "fabric": FABRIC, "deploy": deploy,
                "config": copy.deepcopy(configs)}
        if check_mode:
            args["_ansible_check_mode"] = True
        set_module_args(args)
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(module.time, "sleep"))
            if extra_patch is not None:
                stack.enter_context(extra_patch)
            try:
                module.main()
            except (AnsibleExitJson, AnsibleFailJson) as exc:
                result = exc.args[0]
            else:
                raise AssertionError("module did not exit through Ansible")
    if result.get("failed") and not allow_failed:
        raise AssertionError(result.get("msg"))
    return result, calls


def run(profile, state, have=None, parent=None, **kw):
    """One interface on IF_A -- or on the port-channel, when `parent` says so.

    `parent` defaults to None so every existing ethernet caller is byte-for-byte
    unaffected; only a port-channel caller has to name it.
    """
    deploy_iface = kw.pop("deploy_iface", True)
    conf = (cfg_for(parent, profile, deploy=deploy_iface) if parent is not None
            else cfg(IF_A, profile, deploy=deploy_iface))
    return run_configs([conf], state, have, **kw)


def emit_real_result(configs, state, have=None, check_mode=False, extra_patch=None):
    """Run real `main()` and return the BYTES Ansible would actually print.

    The only thing restored is Ansible's own result formatting. Everything external stays
    mocked exactly as `run_configs` mocks it. Without this, `exit_json`/`fail_json` are
    netcommon doubles that raise instead of serialising: `_return_formatted` never runs,
    there is no `invocation` block, and a redaction assertion observes nothing.
    """
    calls = []
    have = copy.deepcopy(have or [])
    buf = io.StringIO()
    with harness_case() as test:
        test.load_fixtures()
        test.run_bulk.return_value = True
        test.run_send.side_effect = _transport(calls, have)
        args = {"state": state, "fabric": FABRIC, "deploy": True,
                "config": copy.deepcopy(configs)}
        if check_mode:
            args["_ansible_check_mode"] = True
        set_module_args(args)
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.multiple(
                basic.AnsibleModule, exit_json=REAL_EXIT_JSON, fail_json=REAL_FAIL_JSON))
            stack.enter_context(patch.object(module.time, "sleep"))
            if extra_patch is not None:
                stack.enter_context(extra_patch)
            stack.enter_context(contextlib.redirect_stdout(buf))
            try:
                module.main()
            except SystemExit:
                pass
    return buf.getvalue(), calls


def real_serialiser_is_genuine():
    return (REAL_EXIT_JSON.__module__ == "ansible.module_utils.basic"
            and REAL_FAIL_JSON.__module__ == "ansible.module_utils.basic")


# ------------------------------------------------------------------ call classification
def writes(calls):
    return [c for c in calls if c["method"] != "GET"]


def split_calls(calls):
    """Reads, configuration updates and deploys, kept apart.

    A single 'writes' bucket cannot show that a run configured nothing but still
    deployed, or the reverse.
    """
    reads, updates, deploys, other = [], [], [], []
    for c in calls:
        p = c["path"]
        if c["method"] == "GET":
            reads.append(c)
        elif "deploy" in p:
            deploys.append(c)
        elif "/interface/modify" in p or p.rstrip("/").endswith("/rest/interface") \
                or "globalInterface" in p:
            updates.append(c)
        else:
            other.append(c)
    return {"reads": reads, "updates": updates, "deploys": deploys, "other": other}


def _walk_nvpairs(node, out):
    if isinstance(node, dict):
        if isinstance(node.get("nvPairs"), dict):
            out.append(node["nvPairs"])
        for v in node.values():
            _walk_nvpairs(v, out)
    elif isinstance(node, list):
        for v in node:
            _walk_nvpairs(v, out)


def request_nvpairs(calls):
    """Every nvPairs map in every non-GET request: the CAPTURED REQUEST."""
    out = []
    _walk_nvpairs([c["payload"] for c in writes(calls)], out)
    return out


def diff_nvpairs(result):
    """Every nvPairs map in the PUBLIC diff. Deliberately separate from the request:
    `changed_dict` is deep-copied from WANT before the carry-forward runs, so a value
    placed only in WANT is transmitted and never reported."""
    out = []
    _walk_nvpairs(result.get("diff", []), out)
    return out


# ------------------------------------------------------------------ HAVE builders
def _payload_as_have(calls):
    found = []
    _collect_policies([c["payload"] for c in writes(calls)], found)
    if len(found) != 1:
        raise AssertionError("expected exactly one emitted policy payload, got %d"
                             % len(found))
    found[0]["interfaces"][0]["interfaceType"] = "INTERFACE_ETHERNET"
    found[0]["interfaces"][0]["fabricName"] = FABRIC
    return found


def _collect_policies(node, out):
    if isinstance(node, dict):
        if "policy" in node and "interfaces" in node:
            out.append(node)
        else:
            for v in node.values():
                _collect_policies(v, out)
    elif isinstance(node, list):
        for v in node:
            _collect_policies(v, out)


def build_have(parent, key=None, value=None, **extra):
    """Authoritative HAVE, taken from the module's OWN outbound payload.

    Nothing is hand-written: a fixture invented by the test can assert a shape the module
    never produces.
    """
    profile = base_for(parent, **extra)
    if key is not None:
        profile[key] = value
    # The parent is threaded through so a port-channel's HAVE is built from a `pc` config
    # on a Port-channel name. Built as `eth` it would carry the wrong policy and the
    # withdrawal under test would be measured against a HAVE the module never produces.
    _, calls = run(profile, "replaced",
                   parent=parent if parent in NON_ETH_PARENTS else None)
    return _payload_as_have(calls)


def have_for(ifnames, parent, key, value):
    """The same authoritative HAVE, replicated across several interfaces."""
    out = []
    for n in ifnames:
        h = build_have(parent, key, value)
        h[0]["interfaces"][0]["ifName"] = n
        out.extend(h)
    return out
