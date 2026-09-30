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
# Synthetic peer identity; the VPC_SNO shape and reversed pair order come from
# ALPHA's m4-m7 captured GET responses, not from a fabricated transport success.
PEER_SERIAL = "SAL1819SAN9"
PEER_IP = "10.0.0.2"
VPC_PAIR_SERIAL = PEER_SERIAL + "~" + SERIAL
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
VPC_ACCESS = "int_vpc_access_host"
VPC_TRUNK = "int_vpc_trunk_host"
VPC_PARENTS = (VPC_ACCESS, VPC_TRUNK)

# Parents whose config is NOT an `eth` on `IF_A`. Every place that used to ask
# `parent in PC_PARENTS` to decide "does this config need a different type/name?" asks this
# instead, so adding the subinterface parent could not leave one of those places behind
# silently building an ethernet config and measuring the wrong policy.
NON_ETH_PARENTS = PC_PARENTS + VPC_PARENTS + (SUBIF, LOOPBACK, SVI)

PC_A = "Port-channel301"
PC_MEMBER = "Ethernet1/50"
VPC_MEMBER = "Ethernet1/51"

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
LLDP_RX_ON = {"disable_lldp_receive": True}
LLDP_TX_ON = {"disable_lldp_transmit": True}
# The OSPF base group the template makes mandatory under its gate: OSPF_TAG and
# OSPF_AREA_ID carry IsMandatory="ENABLE_OSPF==true", and they feed the same base child as
# the gate itself. Every OSPF value row therefore holds all three explicit, so the omission
# under test is the only moving part. The tag here is SYNTHETIC on purpose -- the live batch
# used an operator-authorised process, and a fixture must not carry a lab resource name.
OSPF_CTX = {"enable_ospf": True, "ospf_tag": "PILOT-OSPF", "ospf_area_id": "0.0.0.0"}
# BFD CONTEXTS. `BFD_GATE` is the gate alone -- what a number needs in order to be visible at
# all (IsShow="bfdInterval==true"). `BFD_INT_CTX` is the gate PLUS the three numbers, which is
# what the parent body requires in order not to refuse the request while the gate is active.
# The three numbers therefore have coordinated coverage, not independent removal: with the gate
# enabled the body will not accept a missing interval, so no independent numeric clear exists to
# test and none is claimed.
BFD_GATE = {"enable_bfd_interval": True}
BFD_INT_CTX = {"enable_bfd_interval": True, "bfd_tx_interval": 250,
               "bfd_min_rx_interval": 350, "bfd_multiplier": 7}
# The same context WITHOUT the area, for the rows whose measurement SUBJECT is the area. A context
# that re-declares the field under test makes it impossible to omit, and then the omission stage
# measures something else.
OSPF_CTX_NO_AREA = {k: v for k, v in OSPF_CTX.items() if k != "ospf_area_id"}
# The message-digest context. The VALUES ARE PLACEHOLDERS: this harness is OFFLINE -- no
# controller and no device is contacted -- and the engine boundary only needs a non-empty string.
# The real dedicated key material lives in the task's `secret/` and NEVER enters a fixture.
#
# Each row carries the context ITS OWN measurement had:
#   the gate was measured with the key and ID explicitly RETAINED -> its context includes them
#   the ID was measured with authentication ENABLED and the key set -> its context includes them
# Keeping the two apart is what stops a disabled gate from masking the ID's result.
AUTH_MD = dict(OSPF_CTX, **{"enable_ospf_auth": True, "ospf_auth_key": "3DES-PLACEHOLDER",
                            "ospf_auth_key_id": 7})
AUTH_MD_NO_GATE = {k: v for k, v in AUTH_MD.items() if k != "enable_ospf_auth"}
AUTH_MD_NO_ID = {k: v for k, v in AUTH_MD.items() if k != "ospf_auth_key_id"}

# The EIGRP gate and the two distribute-list contexts. The tag is MANDATORY for
# ANY EIGRP option: the parent refuses the request with
# "EIGRP process tag is required when EIGRP interface options are enabled."
# The two `direction` rows ALSO require their prefix-list, because without a
# carrier line the direction is not emitted anywhere.
EIGRP_CTX = {"eigrp_process_tag": "PILOT-EIGRP"}
EIGRP_DL4 = {"eigrp_process_tag": "PILOT-EIGRP",
             "eigrp_ipv4_distribute_list_prefix_list": "PILOT-PL4"}
EIGRP_DL6 = {"eigrp_process_tag": "PILOT-EIGRP",
             "eigrp_ipv6_distribute_list_prefix_list": "PILOT-PL6"}
# The mandatory companion of the tag's withdrawal: disabled, because the parent
# does not accept an active option while the tag is empty.
EIGRP_TAG_CTX = {"enable_eigrp_routing": False}

# ------------------------------------------------------------------- MACsec
# The retained contexts below are load-bearing: each one stops its row from
# encoding a transition the product REJECTS.
#
# THE RULE, MEASURED LIVE rather than read off the template. Starting from the
# gate ENABLED with keychain and policy set, the controller refused both attempts
# to empty them, BY FIELD NAME, with `changed=false` and no mutation at all:
#     "Template [int_routed_host] - Validation failed for following fields:
#      [macsecKeyChainName]"            ... and the same for [macsecPolicyName].
# So a fixture that omitted the keychain while LEAVING the gate enabled would
# exercise a request that never lands on a real controller: green in the mock,
# impossible in the lab. This is the same shape as `EIGRP_TAG_CTX` above.
#
# MACSEC_OFF -- for the keychain and policy rows. The gate travels EXPLICITLY
# false, which is the only thing that makes emptying them legal. The resulting
# HAVE (gate off, one name still hanging) is reachable: it is exactly what the
# gate row below leaves behind.
MACSEC_OFF = {"enable_macsec_interface_policy": False}
# MACSEC_NAMES -- for the GATE row. Keychain and policy are RETAINED, which is
# legal: the template rule only fires while the gate is enabled. Turning the gate
# off withdraws the child's CLI line and leaves both names in place.
MACSEC_NAMES = {"macsec_key_chain_name": "PILOT-KC",
                "macsec_policy_name": "PILOT-POL"}
# MACSEC_FB_CTX -- for the FALLBACK row, the ONLY one of the four measured
# withdrawing ON ITS OWN (stage r1b). It reproduces that scenario exactly: gate
# ENABLED, keychain and policy INTACT, and only the fallback omitted. The child
# changes BRANCH, not presence.
MACSEC_FB_CTX = {"enable_macsec_interface_policy": True,
                 "macsec_key_chain_name": "PILOT-KC",
                 "macsec_policy_name": "PILOT-POL"}

# The PIM/ACL campaign kept PIM enabled while clearing its dependent rows.
PIM_ON = {"enable_pim_sparse": True}


# ---------------------------------------------------------------- DAMPENING
# EXPERIMENTAL / CONTROLLER-ONLY generation. These seven resets are candidates,
# not accepted device resets, and are not part of the 157 integration. See
# investigations/pr725-dampening-all/EXPERIMENTAL_LEDGER.md.
#
# The parent declares FIVE conditional rules over this family, measured against
# `interface_dampening.template`, and they decide every context below:
#
#   1 requires_gate     any explicit value needs the gate
#   2 all_or_none       reuse / suppress / max_suppress together or not at all
#   3 requires          reuse needs half_life
#   4 if_true_requires  restart=true needs half_life+reuse+suppress+max
#   5 requires_true     restart_penalty needs restart=true
#
# WHY ONLY FOUR OF THE SEVEN GET A PER-ROW FIXTURE. Rule 2 makes a per-row
# omission of `reuse`, `suppress` or `max_suppress` describe a state the
# controller cannot hold: two of the three present and one absent. A fixture
# encoding that would be green in the mock and impossible on a controller -- the
# exact failure these fixtures exist to avoid. Those three are covered as a GROUP
# in `test_gie_damp_grouped_omission.py`, and the coverage guard names them
# explicitly rather than letting them slip.
DAMP_GATE_ONLY = {}
DAMP_GATE = {"enable_dampening": True}
DAMP_FULL_GROUP = {"enable_dampening": True, "dampening_half_life": 5,
                   "dampening_reuse": 750, "dampening_suppress": 2000,
                   "dampening_max_suppress": 60}
DAMP_WITH_RESTART = dict(DAMP_FULL_GROUP, dampening_restart=True)


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


def wire_for(parent, key, applied):
    """The wire form of `applied`, CONSULTING the binding's SMU vocabulary.

    `wire_of` above assumes a string fixture is already spelled the way the controller
    stores it. That held for every fixture registered before the SMU rename -- `"ACL-PILOT"`,
    `"on"`, `"network"` are their own wire form -- and it breaks for the eight OSPF enums
    whose public and wire spellings differ (`no_passive` -> `noPassive`,
    `point_to_point` -> `pointToPoint`, `no_change` -> `noChange`).

    Measured: with the B3 resets registered, the preservation assertion compared the
    controller's `noPassive` against the fixture's public `no_passive` and failed. The
    fixture was right; the derivation was vocabulary-blind.

    Bindings without `wire_values` fall through to `wire_of`, so every pre-existing caller
    keeps its exact previous behaviour.
    """
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
        resolve_binding,
    )
    wv = (resolve_binding(parent, key) or {}).get("wire_values")
    if wv and isinstance(applied, str) and applied in wv:
        return wv[applied]
    return wire_of(applied)


def public_clear_for(parent, key, reset):
    """The PUBLIC input that requests the registered `reset`, or None if there is none.

    The registry stores `reset_wire` as the nvPair WIRE string. An explicit-clear test has
    to type what an operator types, and for the OSPF enums that is `no_change`, never
    `noChange` -- the wire spelling is deliberately NOT public vocabulary and the module
    refuses it.

    Measured: feeding `reset` straight through produced no request at all, because the
    module rejected the wire spelling as an invalid public choice. That refusal is correct
    and stays; what was wrong was asking for it in the first place.

    Returns None when the reset has no public spelling, so a caller can say so instead of
    inventing one.
    """
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
        resolve_binding,
    )
    wv = (resolve_binding(parent, key) or {}).get("wire_values")
    if wv:
        for public, wire in wv.items():
            if wire == reset:
                return public
        return None
    # No SMU vocabulary: the wire value IS the public spelling, as before.
    return False if reset == "false" else reset


def is_integer_binding(applied):
    """True for a native-integer fixture. `bool` is a subclass of `int`, so it is excluded
    first -- the distinction matters because the public integer input REFUSES the empty
    string, which is exactly why an integer reset had to be measured through a raw request."""
    return isinstance(applied, int) and not isinstance(applied, bool)


PILOT = {
    (ACCESS, "aclFilter"): ("acl_filter", "ACL-PILOT", "", {}),
    (ACCESS, "lldpTransmit"): ("disable_lldp_transmit", True, "false", {}),
    (ACCESS, "lldpReceive"): ("disable_lldp_receive", True, "false", {}),
    (ACCESS, "flowcontrolReceive"): ("flowcontrol_receive", "on", "off", {}),
    (ACCESS, "flowcontrolSend"): ("flowcontrol_send", "on", "off", {}),
    (ACCESS, "qosStatsSuppressed"): ("disable_qos_stats", True, "false", dict(QOS)),
    (ACCESS, "queuingStats"): ("disable_queuing_stats", True, "false", dict(QUEUE)),
    (ACCESS, "spanningTreePortType"): ("spanning_tree_port_type", "network", "no", dict(NOFAST)),
    (TRUNK, "aclFilter"): ("acl_filter", "ACL-PILOT", "", {}),
    (TRUNK, "lldpTransmit"): ("disable_lldp_transmit", True, "false", {}),
    (TRUNK, "lldpReceive"): ("disable_lldp_receive", True, "false", {}),
    (TRUNK, "flowcontrolReceive"): ("flowcontrol_receive", "on", "off", {}),
    (TRUNK, "flowcontrolSend"): ("flowcontrol_send", "on", "off", {}),
    (TRUNK, "qosStatsSuppressed"): ("disable_qos_stats", True, "false", dict(QOS)),
    (TRUNK, "queuingStats"): ("disable_queuing_stats", True, "false", dict(QUEUE)),
    (TRUNK, "GUARD_MODE"): ("guard_mode", "root", "no", {}),
    (TRUNK, "spanningTreePortType"): ("spanning_tree_port_type", "network", "no", dict(NOFAST)),
    (ROUTED, "ipv4Redirects"): ("disable_ipv4_redirects", True, "false", dict(IPV6_ON)),
    (ROUTED, "ipv6Redirects"): ("disable_ipv6_redirects", True, "false", dict(IPV4_ON)),
    # The routed stats pair. Same prerequisites as on access/trunk -- the fields are
    # IsShow-gated on ENABLE_QOS==true and QUEUING_POLICY!='' respectively -- but the CLI
    # effect differs in kind: the withdrawal does not delete a line, it removes the
    # ` no-stats` FRAGMENT and leaves the `service-policy` line standing. Measured live in
    # G33 F1-s2/F2-s2 on Leaf-103 Ethernet1/22.
    # B01/ALPHA, measured live 2026-09-28 on Leaf-103 Ethernet1/64 (SMU90, NDFC 12.6.0.267),
    # stages R1 (positive control) and R2 (explicit group clear), task PR725-SMU-B01-ALPHA-001.
    #
    # The two OSPF rows are IsShow-gated on ENABLE_OSPF==true, and ENABLE_OSPF / OSPF_TAG /
    # OSPF_AREA_ID are themselves registered WITHOUT a reset on this parent, so the context is held
    # EXPLICIT: omitting any of it would refuse the whole invocation for a reason unrelated to the
    # row under test. OSPF_CTX already carries exactly those three.
    #
    # The two IPv6 rows need no context at all: IPV6_ND_SUPPRESS_RA declares defaultValue=false with
    # no IsShow, and IPV6_LINK_LOCAL is emitted by a bare `if ipv6LinkLocal != ""` with no IsShow in
    # any of the three parents. `ipv6_addr`/`ipv6_mask_len` are NATIVE and are deliberately not
    # declared: their native default could remove an address on omission.
    #
    # ipv6LinkLocal is the only one of the four whose reset is the EMPTY STRING, and the only one
    # that declares no default_template -- so before registration it classified as UNCLASSIFIED
    # rather than UNSUPPORTED.
    (ROUTED, "ospfMtuIgnore"): ("ospf_mtu_ignore", True, "false", dict(OSPF_CTX)),
    (ROUTED, "ospfShutdown"): ("ospf_shutdown", True, "false", dict(OSPF_CTX)),
    (ROUTED, "ipv6NdSuppressRa"): ("ipv6_nd_suppress_ra", True, "false", {}),
    (ROUTED, "ipv6LinkLocal"): ("ipv6_link_local", "fe80::164:1", "", {}),
    (ROUTED, "qosStatsSuppressed"): ("disable_qos_stats", True, "false", dict(QOS)),
    (ROUTED, "queuingStats"): ("disable_queuing_stats", True, "false", dict(QUEUE)),
    # The routed LLDP pair, measured live 2026-09-28 on Leaf-103 Ethernet1/64 (fabric SMU90,
    # NDFC 12.6.0.267), stages M1-M4 of PR725-SMU-LLDP-ROUTED-002.
    #
    # The companion is held explicit for a reason specific to this parent, read from the
    # template body on the controller rather than assumed: `int_routed_host` emits no LLDP
    # line itself. It instantiates the child `interface_lldp_disable` and gates it on an OR --
    #     if lldpTransmit == "true" or lldpReceive == "true"
    # -- forwarding BOTH values, and the child renders one line per direction. So driving both
    # to "false" destroys the child and both lines vanish together, which proves nothing about
    # either field alone. Holding the companion at True keeps the child alive, so the line that
    # disappears is attributable to the field that was withdrawn.
    (ROUTED, "lldpTransmit"): ("disable_lldp_transmit", True, "false", LLDP_RX_ON),
    (ROUTED, "lldpReceive"): ("disable_lldp_receive", True, "false", LLDP_TX_ON),
    # The subinterface pair, measured on int_subif ITSELF in G35 M1-s2/M2-s2 -- the routed
    # parent's result was not carried over. Same companion-held-explicit prerequisite: the
    # gate field DISABLE_IP_REDIRECTS is absent from `sub_prof_spec` too and sits at the
    # template default `false`, which the live capture confirms.
    # B01/ALPHA group S, measured live 2026-09-28 on Leaf-103 Ethernet1/64.3001 (dot1q 3001),
    # stages S2 (positive control) and S3 (explicit group clear). Its own measurement: the routed
    # result was NOT copied across, because this parent declares the fields differently.
    #
    # THE GATE IS NAMED DIFFERENTLY HERE. On int_routed_host the two OSPF rows are
    # IsShow="ENABLE_OSPF==true"; on int_subif they are IsShow="ospf==true", and the public
    # `enable_ospf` maps to nvPair `ospf`. OSPF_CTX carries enable_ospf/ospf_tag/ospf_area_id, all
    # three registered WITHOUT a reset on this parent -- and ospf_tag declares no default at all, so
    # in a non-empty value its omission would classify as UNCLASSIFIED. Held explicit throughout.
    #
    # The two IPv6 rows need no context: ipv6NdSuppressRa has defaultValue=false and no IsShow, and
    # ipv6LinkLocal is emitted by a bare `if` with no IsShow.
    (SUBIF, "ospfMtuIgnore"): ("ospf_mtu_ignore", True, "false", dict(OSPF_CTX)),
    (SUBIF, "ospfShutdown"): ("ospf_shutdown", True, "false", dict(OSPF_CTX)),
    (SUBIF, "ipv6NdSuppressRa"): ("ipv6_nd_suppress_ra", True, "false", {}),
    (SUBIF, "ipv6LinkLocal"): ("ipv6_link_local", "fe80::3001:1", "", {}),
    (SUBIF, "ipv4Redirects"): ("disable_ipv4_redirects", True, "false", dict(IPV6_ON)),
    (SUBIF, "ipv6Redirects"): ("disable_ipv6_redirects", True, "false", dict(IPV4_ON)),
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
    # B3: the two routed ENUM identities. Their reset is the NEUTRAL WIRE SPELLING
    # `noChange`, not "" -- for an enum the unset state is a named choice, so an empty
    # string would be the typo this suite rejects elsewhere for enums.
    #
    # The applied value of each is the one whose CLI artifact was measured live:
    # `no_passive` renders `no ip ospf passive-interface`, `point_to_point` renders
    # `ip ospf network point-to-point`. The OTHER non-neutral value of each pair
    # (`passive`, `broadcast`) is exercised in test_gie_routed_enum_omission_b3.py, so
    # both variants of both enums are covered.
    (ROUTED, "ospfPassiveMode"): ("ospf_passive_mode", "no_passive", "noChange",
                                  dict(OSPF_CTX)),
    (ROUTED, "ospfNetworkType"): ("ospf_network_type", "point_to_point", "noChange",
                                  dict(OSPF_CTX)),
    # ---------------------------------------------------------------------- P1, OSPF-ALL
    # The six rows of the grouped OPTIONS profile, measured live on 2026-09-28 on Leaf-103
    # (SMU90, NDFC 12.6.0.267), stage P1-g2-rM-clear, task PR725-OSPF-ALL-001. Each was
    # measured on ITS OWN parent and mounted subject:
    #     int_subif     Ethernet1/64.3001 (dot1q 3001)
    #     int_loopback  Loopback20
    #     int_vlan      Vlan3789 (the SVI; VLAN 3789 is a separate object, mounted separately)
    #
    # `int_routed_host` contributes NO new row here: its network_type and passive_mode were
    # already registered, so in that profile it carried RETENTION CONTROLS. Measured: the
    # clear's `interface/modify` body did not include int_routed_host at all, and its three
    # option lines stayed in the device config while the six below disappeared.
    #
    # WHY ospf_network_type IS LISTED THREE TIMES AND NOT INFERRED ONCE. It is a distinct
    # binding per parent -- three rows in the table, three separate reset registrations. The
    # routed one was accepted in an earlier campaign; these three were measured here.
    #
    # AND WHY THE PASSIVE PAIR IS TWO FIELDS, NOT ONE. `int_subif` declares the BOOLEAN
    # `ospfPassiveInterface`; `int_vlan` declares the ENUM `ospfPassiveMode`. Different
    # nvPairs, different types, different reset vocabularies ('false' vs 'noChange') -- and
    # both render the SAME CLI line, `ip ospf passive-interface`. Reading the CLI alone could
    # not tell them apart, which is why each carries its own row and its own reset.
    (SUBIF, "ospfNetworkType"): ("ospf_network_type", "point_to_point", "noChange",
                                 dict(OSPF_CTX)),
    (SUBIF, "ospfPassiveInterface"): ("ospf_passive_interface", True, "false", dict(OSPF_CTX)),
    (LOOPBACK, "ospfNetworkType"): ("ospf_network_type", "point_to_point", "noChange",
                                    dict(OSPF_CTX)),
    (LOOPBACK, "ospfAdvertiseSubnet"): ("ospf_advertise_subnet", True, "false", dict(OSPF_CTX)),
    (SVI, "ospfNetworkType"): ("ospf_network_type", "point_to_point", "noChange",
                               dict(OSPF_CTX)),
    (SVI, "ospfPassiveMode"): ("ospf_passive_mode", "passive", "noChange", dict(OSPF_CTX)),
    # ------------------------------------------------------ P2-BFD and P4-AREA, OSPF-ALL
    # Measured live on 2026-09-28 on Leaf-103, stages P2-a3-clear and P4-a3-clear.
    #
    # BFD IS ASYMMETRIC: `ospfBfdMode` (enum, reset 'noChange') exists on int_routed_host and
    # int_vlan; `ospfBfd` (boolean, reset 'false') on int_subif and int_loopback. No parent
    # declares the other's field. Both render the SAME CLI line, `ip ospf bfd`, so reading the CLI
    # does not tell them apart -- just like the passive pair in P1.
    #
    # PREREQUISITE: `feature bfd` on Leaf-103, enabled through NDFC with the operator's explicit
    # authorisation (policy POLICY-55670, priority 500) and verified in the device running-config.
    # Without it the device rejects `ip ospf bfd` with "CLI command is invalid".
    (ROUTED, "ospfBfdMode"): ("ospf_bfd_mode", "enable", "noChange", dict(OSPF_CTX)),
    (SUBIF, "ospfBfd"): ("ospf_bfd", True, "false", dict(OSPF_CTX)),
    (LOOPBACK, "ospfBfd"): ("ospf_bfd", True, "false", dict(OSPF_CTX)),
    (SVI, "ospfBfdMode"): ("ospf_bfd_mode", "enable", "noChange", dict(OSPF_CTX)),
    # THE AREA IS THIS CAMPAIGN'S FIRST RESET THAT DOES NOT DELETE A LINE.
    # `ip router ospf <tag> area 0.0.0.77` -> `ip router ospf <tag> area 0.0.0.0`: the line is STILL
    # there, carrying the declared default. Restoring a default is a valid withdrawal effect;
    # demanding that every row delete its line would have rejected these four for the wrong reason.
    #
    # THE CONTEXT OF THESE FOUR CANNOT CARRY THE AREA, because the area IS the row under test.
    # `OSPF_CTX` includes `ospf_area_id`, so using it as-is left the field RE-DECLARED in the
    # omission stage's profile: the field was never omitted, and twelve cases failed against a
    # context that contradicted their own row. `OSPF_CTX_NO_AREA` is the same context without it.
    #
    # int_routed_host::ospf_area_id IS BACK, and the reason is a measurement that CORRECTS the
    # earlier one. The control that had removed it used `base_for(ROUTED)`, and `BASE_ROUTED`
    # ALREADY CONTAINS `ospf_area_id: "0.0.0.0"`: the field was never omitted, so the bodies came
    # out identical with and without the metadata, and from that came the claim that "the reset
    # contributed nothing". With the public key GENUINELY ABSENT, a non-default area in the HAVE,
    # OSPF enabled and the tag retained, the A/B measures the opposite:
    #     table WITHOUT metadata -> `replaced` and `replaced+check` REFUSE (fail-closed), 0 writes
    #     table WITH metadata    -> check plans WITHOUT transmitting; `replaced` emits 1 write with
    #                               `0.0.0.0`; omitted under `merged` PRESERVES; a rerun over the
    #                               default is a no-op
    #
    # That the NATIVE path can also produce that same value does not stop the metadata from being
    # what AUTHORISES the transition: without it, main() refuses. No claim is made that the engine
    # is the only producer of the payload's value.
    (ROUTED, "OSPF_AREA_ID"): ("ospf_area_id", "0.0.0.77", "0.0.0.0", dict(OSPF_CTX_NO_AREA)),
    (SUBIF, "OSPF_AREA_ID"): ("ospf_area_id", "0.0.0.77", "0.0.0.0", dict(OSPF_CTX_NO_AREA)),
    (LOOPBACK, "OSPF_AREA_ID"): ("ospf_area_id", "0.0.0.77", "0.0.0.0", dict(OSPF_CTX_NO_AREA)),
    (SVI, "OSPF_AREA_ID"): ("ospf_area_id", "0.0.0.77", "0.0.0.0", dict(OSPF_CTX_NO_AREA)),
    # ----------------------------------------- P3a message-digest: gate (4) and key-ID (4)
    # Measured live on 2026-09-28 on all four subjects, stages P3a-a3-auth-off and
    # P3a-a4-keyid-default, with the dedicated key obtained through the team's procedure.
    #
    # THE GATE: `enable_ospf_auth` -> 'false' WITH the key and ID explicitly retained. The body's
    # V4 predicate only fires while authentication is true, so turning it off while keeping the
    # material is valid -- and it was measured: the whole authentication CLI disappeared on all four.
    #
    # THE ID: `ospf_auth_key_id` -> '1', its DECLARED defaultValue, with authentication ENABLED and
    # the key set. NOT the empty string: the empty string would trip V4. It is an `integer` whose
    # reset travels as a STRING -- the generator rejects a native integer in reset_wire.
    #
    # THE TWO CONTEXTS ARE KEPT SEPARATE on purpose: if the gate were off in the ID's case, its
    # withdrawal would not be observable and the result would be vacuous.
    (ROUTED, "ospfAuthentication"): ("enable_ospf_auth", True, "false", dict(AUTH_MD_NO_GATE)),
    (SUBIF, "ospfAuthentication"): ("enable_ospf_auth", True, "false", dict(AUTH_MD_NO_GATE)),
    (LOOPBACK, "ospfAuthentication"): ("enable_ospf_auth", True, "false", dict(AUTH_MD_NO_GATE)),
    (SVI, "ospfAuthentication"): ("enable_ospf_auth", True, "false", dict(AUTH_MD_NO_GATE)),
    (ROUTED, "OSPF_AUTH_KEY_ID"): ("ospf_auth_key_id", 7, "1", dict(AUTH_MD_NO_ID)),
    (SUBIF, "OSPF_AUTH_KEY_ID"): ("ospf_auth_key_id", 7, "1", dict(AUTH_MD_NO_ID)),
    (LOOPBACK, "OSPF_AUTH_KEY_ID"): ("ospf_auth_key_id", 7, "1", dict(AUTH_MD_NO_ID)),
    (SVI, "OSPF_AUTH_KEY_ID"): ("ospf_auth_key_id", 7, "1", dict(AUTH_MD_NO_ID)),
    # -------------------------------- P3b SIMPLE authentication: the key, on all 4
    # A mechanism DISTINCT from message-digest: `ospfAuthenticationKey` is gated only by
    # `ospf==true`, not by `ospfAuthentication`. Measured live on 2026-09-29: `P3b-b1-apply` left
    # `ip ospf authentication-key 3` on all four and `P3b-b3-clear-key` withdrew it.
    #
    # The context carries the TYPE at its declared default `3`, consistent with 3DES material. The
    # value is a PLACEHOLDER: this harness is offline and the dedicated material lives in `secret/`.
    (ROUTED, "ospfAuthenticationKey"): ("ospf_authentication_key", "3DES-PLACEHOLDER", "",
                                        dict(OSPF_CTX, ospf_authentication_key_type="3")),
    (SUBIF, "ospfAuthenticationKey"): ("ospf_authentication_key", "3DES-PLACEHOLDER", "",
                                       dict(OSPF_CTX, ospf_authentication_key_type="3")),
    (LOOPBACK, "ospfAuthenticationKey"): ("ospf_authentication_key", "3DES-PLACEHOLDER", "",
                                          dict(OSPF_CTX, ospf_authentication_key_type="3")),
    (SVI, "ospfAuthenticationKey"): ("ospf_authentication_key", "3DES-PLACEHOLDER", "",
                                     dict(OSPF_CTX, ospf_authentication_key_type="3")),
    # ------------------------------------ P5: the GATE, on 3 of the 4 parents
    # `enable_ospf` -> 'false'. Its context carries EVERY dependent at its neutral, because the
    # body refuses to turn the gate off while any of them is non-neutral ("Enable OSPF ... before
    # configuring OSPF interface options"). The tag travels explicitly: it has no REGISTERED
    # reset -- unmeasured, not ruled out -- so omitting it would refuse for a different reason.
    #
    (ROUTED, "ospf"): ("enable_ospf", True, "false", dict(OSPF_CTX, ospf_tag="PILOT-OSPF")),
    (SUBIF, "ospf"): ("enable_ospf", True, "false", dict(OSPF_CTX, ospf_tag="PILOT-OSPF")),
    (SVI, "ospf"): ("enable_ospf", True, "false", dict(OSPF_CTX, ospf_tag="PILOT-OSPF")),
    # int_loopback JOINS on 2026-09-29, and its context carries a NON-DEFAULT `int_vrf` on purpose.
    #
    # The previous round excluded it: measured with `int_vrf: default`, the device KEPT
    # `ip router ospf <tag> area <x>` even though the controller stored `ospf=false`. The cause is
    # in THIS parent's installed body, line 648 -- and in none of the other three:
    #
    #   configureOspf = (enableOspf == "true" or (intfVrf == "default" and
    #                                             linkStateRouting == "ospf"))
    #
    # It is a disjunction: in the `default` VRF of a fabric that routes with OSPF the second branch
    # emits the association without looking at the gate, and the withdrawal is UNOBSERVABLE.
    # Measured in V3-clear with `int_vrf: PR725VRF`: the line disappeared while the interface,
    # `vrf member` and `ip address` survived.
    #
    # THE EMISSION THIS ROW CHECKS DOES NOT DEPEND ON THE VRF -- the module does not evaluate the
    # template body, it only emits `ospf: 'false'` when the field is omitted. The context's
    # `int_vrf` is here so the fixture represents THE SCENARIO IN WHICH THE RESET WAS DEMONSTRATED,
    # not because the emission changes with it. The boundary -- that in the `default` VRF this reset
    # does not remove the line, because another input produces it -- is documented in the worklog,
    # not in the table.
    (LOOPBACK, "ospf"): ("enable_ospf", True, "false",
                         dict(OSPF_CTX, ospf_tag="PILOT-OSPF", int_vrf="PILOT-VRF")),
    # B01: the two int_loopback OSPF booleans. Their reset is the wire STRING
    # "false" -- the public input is a native bool, and the generator rejects a
    # native bool in reset_wire, so the two vocabularies stay apart.
    #
    # Applied value `True` renders the measured CLI: `ip ospf mtu-ignore` and
    # `ip ospf shutdown`, both confirmed from the installed children on .90
    # (ospf_interface_mtu_ignore_11_1, ospf_interface_shutdown_11_1), not guessed.
    # The loopback needs its own OSPF base group; it carries no FEC, which
    # belongs to routed ethernet only.
    (LOOPBACK, "ospfMtuIgnore"): ("ospf_mtu_ignore", True, "false", dict(OSPF_CTX)),
    (LOOPBACK, "ospfShutdown"): ("ospf_shutdown", True, "false", dict(OSPF_CTX)),
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
    # ------------------------------------ PR725-BFD-ALL-001: the ten BFD bindings
    #
    # `disable_bfd_echo` / nvPair `bfdEcho`: the public name is NEGATIVE, the nvPair looks
    # POSITIVE, and the sense is NOT inverted. The installed body evaluates
    # `if bfdEcho == "true":` and in that branch instantiates the child
    # `bfd_no_echo_interface`, whose content is `no bfd echo`. Measured on the device
    # (stages B2-mount / B4-echo-clear): public True -> `no bfd echo`; public False -> the line
    # disappears. Only routed and vlan declare it. Its withdrawal is INDEPENDENT: it carries
    # neither a conditional IsShow nor a conditional IsMandatory, and it was measured with the
    # interval gate ENABLED, which is what isolates its effect from the interval group.
    (ROUTED, "bfdEcho"): ("disable_bfd_echo", True, "false", {}),
    (SVI, "bfdEcho"): ("disable_bfd_echo", True, "false", {}),
    #
    # THE COUPLED INTERVAL GROUP, on subif and vlan.
    #
    # The child `interface_bfd_interval_11_1` emits ONE single line carrying all THREE numbers:
    #   `bfd interval <tx> min_rx <rx> multiplier <mult>`
    # All three carry IsMandatory="bfdInterval==true" AND IsShow="bfdInterval==true", and the
    # installed body REFUSES with a failure return code if the gate is active while any of them
    # is empty (subif L595, vlan L1033). So each number's context declares the gate AND the other
    # two: that is THE SCENARIO IN WHICH THE RESET WAS MEASURED, not verbosity.
    #
    # WHAT THESE ROWS ESTABLISH is the EMISSION of the reset on omission. What they do NOT
    # establish is independent withdrawal of one number while the gate stays enabled: the body
    # refuses that, so the coverage is COORDINATED. The reset values were measured with the
    # preserving probe (rc 207, readback '250'/'350'/'7' -> '' with the key PRESENT), not
    # inferred from the fact that turning the feature off takes the whole line with it.
    (SUBIF, "bfdInterval"): ("enable_bfd_interval", True, "false", dict(BFD_INT_CTX)),
    (SVI, "bfdInterval"): ("enable_bfd_interval", True, "false", dict(BFD_INT_CTX)),
    (SUBIF, "bfdTxInterval"): ("bfd_tx_interval", 250, "", dict(BFD_GATE, bfd_min_rx_interval=350, bfd_multiplier=7)),
    (SVI, "bfdTxInterval"): ("bfd_tx_interval", 250, "", dict(BFD_GATE, bfd_min_rx_interval=350, bfd_multiplier=7)),
    (SUBIF, "bfdMinRxInterval"): ("bfd_min_rx_interval", 350, "", dict(BFD_GATE, bfd_tx_interval=250, bfd_multiplier=7)),
    (SVI, "bfdMinRxInterval"): ("bfd_min_rx_interval", 350, "", dict(BFD_GATE, bfd_tx_interval=250, bfd_multiplier=7)),
    (SUBIF, "bfdMultiplier"): ("bfd_multiplier", 7, "", dict(BFD_GATE, bfd_tx_interval=250, bfd_min_rx_interval=350)),
    (SVI, "bfdMultiplier"): ("bfd_multiplier", 7, "", dict(BFD_GATE, bfd_tx_interval=250, bfd_min_rx_interval=350)),
    (SVI, "ospfDeadInterval"): ("ospf_dead_interval", 44, "", dict(OSPF_CTX)),
    (SVI, "ospfHelloInterval"): ("ospf_hello_interval", 11, "", dict(OSPF_CTX)),
    (SVI, "ospfPriority"): ("ospf_priority", 77, "", dict(OSPF_CTX)),
    (SVI, "ospfTransmitDelay"): ("ospf_transmit_delay", 3, "", dict(OSPF_CTX)),
    (SVI, "ospfRetransmitInterval"): ("ospf_retransmit_interval", 9, "", dict(OSPF_CTX)),
    (SVI, "arpTimeout"): ("arp_timeout", 900, "", {}),
    (SVI, "ipv4Redirects"): ("disable_ipv4_redirects", True, "false",
                                      {"disable_ipv6_redirects": True}),
    (SVI, "ipv6Redirects"): ("disable_ipv6_redirects", True, "false",
                                      {"disable_ipv4_redirects": True}),
    # The four int_vlan rows BETA measured live in the B01 SVI group, on BETAENUM /
    # Leaf-105 / Vlan991 (VLAN 991 and the SVI are distinct objects; both were
    # created and recovered separately). Not inferred from int_loopback or
    # int_routed_host: different parent, different template.
    #
    # THREE ARE BOOLEAN and their measured reset is the STRING 'false'. THE FOURTH
    # IS A STRING -- `ipv6LinkLocal` is an `ipV6Address`, max 45 -- and its measured
    # reset is the EMPTY string. The installed template draws exactly that line:
    #     if ipv6LinkLocal != "":         -> emits `ipv6 link-local <value>`
    #     if ipv6NdSuppressRa == "true":  -> emits `ipv6 nd suppress-ra`
    #     if ospfMtuIgnore == "true":     -> emits `ip ospf mtu-ignore`
    #     if ospfShutdown == "true":      -> emits `ip ospf shutdown`
    # Giving the string row 'false' would register a reset that withdraws nothing.
    (SVI, "ospfMtuIgnore"): ("ospf_mtu_ignore", True, "false", dict(OSPF_CTX)),
    (SVI, "ospfShutdown"): ("ospf_shutdown", True, "false", dict(OSPF_CTX)),
    (SVI, "ipv6NdSuppressRa"): ("ipv6_nd_suppress_ra", True, "false", {}),
    (SVI, "ipv6LinkLocal"): ("ipv6_link_local", "fe80::991:1", "", {}),

    # --- PR725-EIGRP-ALL-001: the EIGRP identities with a MEASURED reset -------
    #
    # THE TAG IS THE GATE. The parent wraps the WHOLE EIGRP block in
    # `if eigrpProcessTag != "":`, and it also REFUSES the request if any option is
    # active while the tag is empty. That is why every row carries it explicitly:
    # the omission under test has to be the only thing that moves.
    #
    # SYNTHETIC NAMES, as in OSPF_CTX: the live campaign used an operator-authorised
    # tag and prefix-lists, and a fixture must not carry a lab resource name.
    #
    # THE TWO `direction` ROWS ARE NEITHER BOOLEAN NOR EMPTIABLE. Their measured
    # reset is `"out"`, their declared default, because the public enum has no
    # neutral (`valid_values=('in','out')`, no `no_change`). And their effect is a
    # FRAGMENT: the direction travels INSIDE the prefix-list line, which survives
    # the reset. That is why their context includes the prefix-list: without it
    # there is no carrier line and nothing to observe.
    #
    # `int_loopback` carries ONLY TWO. Its installed parent declares neither
    # eigrpIpv6Routing nor the four distribute-list fields; registering any of
    # those five for it would be exactly the silent loss this registry exists to
    # prevent. Eight fields, not thirteen.
    (ROUTED, "eigrpRouting"): ("enable_eigrp_routing", True, "false", dict(EIGRP_CTX)),
    (ROUTED, "eigrpShutdown"): ("enable_eigrp_shutdown", True, "false", dict(EIGRP_CTX)),
    (ROUTED, "eigrpIpv6Routing"): ("enable_eigrp_ipv6_routing", True, "false", dict(EIGRP_CTX)),
    (ROUTED, "eigrpIpv4DistributeListPrefixList"): ("eigrp_ipv4_distribute_list_prefix_list", "PILOT-PL4", "", dict(EIGRP_CTX)),
    (ROUTED, "eigrpIpv6DistributeListPrefixList"): ("eigrp_ipv6_distribute_list_prefix_list", "PILOT-PL6", "", dict(EIGRP_CTX)),
    (ROUTED, "eigrpIpv4DistributeListDirection"): ("eigrp_ipv4_distribute_list_direction", "in", "out", dict(EIGRP_DL4)),
    (ROUTED, "eigrpIpv6DistributeListDirection"): ("eigrp_ipv6_distribute_list_direction", "in", "out", dict(EIGRP_DL6)),
    (SUBIF, "eigrpRouting"): ("enable_eigrp_routing", True, "false", dict(EIGRP_CTX)),
    (SUBIF, "eigrpShutdown"): ("enable_eigrp_shutdown", True, "false", dict(EIGRP_CTX)),
    (SUBIF, "eigrpIpv6Routing"): ("enable_eigrp_ipv6_routing", True, "false", dict(EIGRP_CTX)),
    (SUBIF, "eigrpIpv4DistributeListPrefixList"): ("eigrp_ipv4_distribute_list_prefix_list", "PILOT-PL4", "", dict(EIGRP_CTX)),
    (SUBIF, "eigrpIpv6DistributeListPrefixList"): ("eigrp_ipv6_distribute_list_prefix_list", "PILOT-PL6", "", dict(EIGRP_CTX)),
    (SUBIF, "eigrpIpv4DistributeListDirection"): ("eigrp_ipv4_distribute_list_direction", "in", "out", dict(EIGRP_DL4)),
    (SUBIF, "eigrpIpv6DistributeListDirection"): ("eigrp_ipv6_distribute_list_direction", "in", "out", dict(EIGRP_DL6)),
    (SVI, "eigrpRouting"): ("enable_eigrp_routing", True, "false", dict(EIGRP_CTX)),
    (SVI, "eigrpShutdown"): ("enable_eigrp_shutdown", True, "false", dict(EIGRP_CTX)),
    (SVI, "eigrpIpv6Routing"): ("enable_eigrp_ipv6_routing", True, "false", dict(EIGRP_CTX)),
    (SVI, "eigrpIpv4DistributeListPrefixList"): ("eigrp_ipv4_distribute_list_prefix_list", "PILOT-PL4", "", dict(EIGRP_CTX)),
    (SVI, "eigrpIpv6DistributeListPrefixList"): ("eigrp_ipv6_distribute_list_prefix_list", "PILOT-PL6", "", dict(EIGRP_CTX)),
    (SVI, "eigrpIpv4DistributeListDirection"): ("eigrp_ipv4_distribute_list_direction", "in", "out", dict(EIGRP_DL4)),
    (SVI, "eigrpIpv6DistributeListDirection"): ("eigrp_ipv6_distribute_list_direction", "in", "out", dict(EIGRP_DL6)),
    (LOOPBACK, "eigrpRouting"): ("enable_eigrp_routing", True, "false", dict(EIGRP_CTX)),
    (LOOPBACK, "eigrpShutdown"): ("enable_eigrp_shutdown", True, "false", dict(EIGRP_CTX)),

    # The eight BFD rows. MUTUALLY EXCLUSIVE: the parent refuses the request if
    # `eigrpBfd` and `eigrpBfdDisable` both travel true, so each row carries ONLY
    # its own and the context does not drag in the companion. It is the same reason
    # they were measured in alternate profiles in the lab and never together.
    #
    # The comparison has to be by WHOLE LINE: `ip eigrp T bfd` is a prefix of
    # `ip eigrp T bfd disable`, and a substring test would score one as PRESENT
    # when only the other is there.
    (ROUTED, "eigrpBfd"): ("enable_eigrp_bfd", True, "false", dict(EIGRP_CTX)),
    (ROUTED, "eigrpBfdDisable"): ("disable_eigrp_bfd", True, "false", dict(EIGRP_CTX)),
    (SUBIF, "eigrpBfd"): ("enable_eigrp_bfd", True, "false", dict(EIGRP_CTX)),
    (SUBIF, "eigrpBfdDisable"): ("disable_eigrp_bfd", True, "false", dict(EIGRP_CTX)),
    (SVI, "eigrpBfd"): ("enable_eigrp_bfd", True, "false", dict(EIGRP_CTX)),
    (SVI, "eigrpBfdDisable"): ("disable_eigrp_bfd", True, "false", dict(EIGRP_CTX)),
    (LOOPBACK, "eigrpBfd"): ("enable_eigrp_bfd", True, "false", dict(EIGRP_CTX)),
    (LOOPBACK, "eigrpBfdDisable"): ("disable_eigrp_bfd", True, "false", dict(EIGRP_CTX)),

    # The four TAG rows. Their retained context carries `enable_eigrp_routing: False`
    # on purpose: live, withdrawing the tag is a COORDINATED TRANSITION -- the parent
    # refuses the request if an option is left active while the tag is empty -- and
    # the fixture reflects that contract, not an imaginary independent withdrawal.
    (ROUTED, "eigrpProcessTag"): ("eigrp_process_tag", "PILOT-EIGRP", "", dict(EIGRP_TAG_CTX)),
    (SUBIF, "eigrpProcessTag"): ("eigrp_process_tag", "PILOT-EIGRP", "", dict(EIGRP_TAG_CTX)),
    (SVI, "eigrpProcessTag"): ("eigrp_process_tag", "PILOT-EIGRP", "", dict(EIGRP_TAG_CTX)),
    (LOOPBACK, "eigrpProcessTag"): ("eigrp_process_tag", "PILOT-EIGRP", "", dict(EIGRP_TAG_CTX)),

    # The 4 MACSEC rows, ALL on int_routed_host: it is the only parent that
    # declares them. Measured live on Ethernet1/64.
    #
    # THE NAMES ARE SYNTHETIC on purpose -- `PILOT-KC`, `PILOT-POL`,
    # `PILOT-FBKC` -- exactly as for the EIGRP tag: a fixture must not carry the
    # name of a lab resource. They are NAMES, not secrets: the key material lives
    # in the keychain, which this module does not create.
    #
    # COMPARISON MUST BE BY WHOLE LINE, the same hazard as EIGRP:
    #     macsec keychain KC policy POL
    # is an EXACT PREFIX of
    #     macsec keychain KC policy POL fallback-keychain FB
    # so a substring test scores branch A as branch B. These cases assert on the
    # request nvPair, but the warning holds for anyone reading the device CLI.
    #
    # ONLY THE FALLBACK ROW IS A MEASURED INDEPENDENT WITHDRAWAL. The other three
    # can only be withdrawn together, and their retained context says so.
    (ROUTED, "macsecInterfacePolicy"): (
        "enable_macsec_interface_policy", True, "false", dict(MACSEC_NAMES)),
    (ROUTED, "macsecKeyChainName"): (
        "macsec_key_chain_name", "PILOT-KC", "", dict(MACSEC_OFF)),
    (ROUTED, "macsecPolicyName"): (
        "macsec_policy_name", "PILOT-POL", "", dict(MACSEC_OFF)),
    (ROUTED, "macsecFallbackKeyChainName"): (
        "macsec_fallback_key_chain_name", "PILOT-FBKC", "", dict(MACSEC_FB_CTX)),

    # The DAMPENING rows whose retained context is VALID. CONTROLLER-ONLY evidence: see the
    # lot note above and the task's support-limitation note -- registered, observed at the
    # controller with deploy false, NX-OS withdrawal never validated.
    (ROUTED, "dampening"): (
        "enable_dampening", True, "false", dict(DAMP_GATE_ONLY)),
    (ROUTED, "dampeningHalfLife"): (
        "dampening_half_life", 5, "", dict(DAMP_GATE)),
    (ROUTED, "dampeningRestart"): (
        "dampening_restart", True, "false", dict(DAMP_FULL_GROUP)),
    (ROUTED, "dampeningRestartPenalty"): (
        "dampening_restart_penalty", 1000, "", dict(DAMP_WITH_RESTART)),

    # Ten source-campaign registrations. The ACL name is synthetic in this fixture;
    # the source campaign separately verified a real prerequisite ACL in the lab.
    (LOOPBACK, "ENABLE_PIM_SPARSE"): ("enable_pim_sparse", True, "false", {}),
    (ROUTED, "ENABLE_PIM_SPARSE"): ("enable_pim_sparse", True, "false", {}),
    (SUBIF, "ENABLE_PIM_SPARSE"): ("enable_pim_sparse", True, "false", {}),
    (SVI, "ENABLE_PIM_SPARSE"): ("enable_pim_sparse", True, "false", {}),
    (ROUTED, "PIM_DR_PRIORITY"): ("pim_dr_priority", 77, "1", dict(PIM_ON)),
    (SUBIF, "PIM_DR_PRIORITY"): ("pim_dr_priority", 77, "1", dict(PIM_ON)),
    (SVI, "PIM_DR_PRIORITY"): ("pim_dr_priority", 77, "1", dict(PIM_ON)),
    (ROUTED, "ipv4AclIn"): ("ipv4_acl_in", "PILOT-ACL", "", {}),
    (SVI, "ipv4AclIn"): ("ipv4_acl_in", "PILOT-ACL", "", {}),
    (ROUTED, "pimBfdInstance"): ("enable_pim_bfd_instance", True, "false", dict(PIM_ON)),
}
# The registered identities that deliberately have NO per-row fixture, each with the reason.
# NAMED, not silently subtracted: the coverage guard requires every member to be registered and
# the set to be non-empty, so this cannot become a place to park an untested row.
GROUPED_ONLY_NO_PER_ROW_FIXTURE = {
    # Rule 2 (all_or_none) makes a per-row omission of any one of these three describe a
    # controller state that cannot exist. Covered as a group in
    # `test_gie_damp_grouped_omission.py`.
    (ROUTED, "dampeningReuse"): "all_or_none with suppress/max_suppress",
    (ROUTED, "dampeningSuppress"): "all_or_none with reuse/max_suppress",
    (ROUTED, "dampeningMaxSuppress"): "all_or_none with reuse/suppress",
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
    (PC_ACCESS, "lldpTransmit"): ("disable_lldp_transmit", True, "false", {}),
    (PC_ACCESS, "lldpReceive"): ("disable_lldp_receive", True, "false", {}),
    (PC_ACCESS, "qosStatsSuppressed"): ("disable_qos_stats", True, "false", dict(QOS)),
    (PC_ACCESS, "queuingStats"): ("disable_queuing_stats", True, "false", dict(QUEUE)),
    (PC_ACCESS, "spanningTreePortType"): ("spanning_tree_port_type", "network", "no", dict(NOFAST)),
    (PC_TRUNK, "aclFilter"): ("acl_filter", "ACL-PILOT", "", {}),
    (PC_TRUNK, "lldpTransmit"): ("disable_lldp_transmit", True, "false", {}),
    (PC_TRUNK, "lldpReceive"): ("disable_lldp_receive", True, "false", {}),
    (PC_TRUNK, "qosStatsSuppressed"): ("disable_qos_stats", True, "false", dict(QOS)),
    (PC_TRUNK, "queuingStats"): ("disable_queuing_stats", True, "false", dict(QUEUE)),
    (PC_TRUNK, "GUARD_MODE"): ("guard_mode", "root", "no", {}),
    (PC_TRUNK, "spanningTreePortType"): ("spanning_tree_port_type", "network", "no", dict(NOFAST)),
    (PC_DOT1Q, "aclFilter"): ("acl_filter", "ACL-PILOT", "", {}),
    (PC_DOT1Q, "lldpTransmit"): ("disable_lldp_transmit", True, "false", {}),
    (PC_DOT1Q, "lldpReceive"): ("disable_lldp_receive", True, "false", {}),
    (PC_DOT1Q, "qosStatsSuppressed"): ("disable_qos_stats", True, "false", dict(QOS)),
    (PC_DOT1Q, "queuingStats"): ("disable_queuing_stats", True, "false", dict(QUEUE)),
    (PC_DOT1Q, "spanningTreePortType"): ("spanning_tree_port_type", "network", "no", dict(NOFAST)),
}
PILOT_PC_IDS = ["%s::%s" % (p, n) for (p, n) in PILOT_PC]
PILOT_PC_ITEMS = [(p, n, k, applied, reset, extra)
                  for (p, n), (k, applied, reset, extra) in PILOT_PC.items()]

# Both measured vPC parents. Their shared wire values are separate identities;
# guard_mode exists only on the trunk parent. Context keeps the member and QoS
# prerequisites in place, and disables port_type_fast for the neutral enum.
PILOT_VPC = {
    (VPC_ACCESS, "aclFilter"): ("acl_filter", "PILOT-ACL", "", {}),
    (VPC_ACCESS, "lldpReceive"): ("disable_lldp_receive", True, "false", {}),
    (VPC_ACCESS, "lldpTransmit"): ("disable_lldp_transmit", True, "false", {}),
    (VPC_ACCESS, "qosStatsSuppressed"): ("disable_qos_stats", True, "false", {}),
    (VPC_ACCESS, "queuingStats"): ("disable_queuing_stats", True, "false", {}),
    (VPC_ACCESS, "spanningTreePortType"): ("spanning_tree_port_type", "normal", "no", {}),
    (VPC_TRUNK, "aclFilter"): ("acl_filter", "PILOT-ACL", "", {}),
    (VPC_TRUNK, "lldpReceive"): ("disable_lldp_receive", True, "false", {}),
    (VPC_TRUNK, "lldpTransmit"): ("disable_lldp_transmit", True, "false", {}),
    (VPC_TRUNK, "qosStatsSuppressed"): ("disable_qos_stats", True, "false", {}),
    (VPC_TRUNK, "queuingStats"): ("disable_queuing_stats", True, "false", {}),
    (VPC_TRUNK, "spanningTreePortType"): ("spanning_tree_port_type", "network", "no", {}),
    (VPC_TRUNK, "GUARD_MODE"): ("guard_mode", "root", "no", {}),
}

# The combined matrix. Tests parametrized over this cover ethernet and port-channel in one
# pass, so a contract that holds for one and not the other cannot hide.
PILOT_ALL = dict(PILOT)
PILOT_ALL.update(PILOT_PC)
PILOT_ALL.update(PILOT_VPC)
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
BASE_VPC_ACCESS = {"mode": "access", "peer1_pcid": 11, "peer2_pcid": 11,
                   "peer1_members": [VPC_MEMBER], "peer2_members": [VPC_MEMBER],
                   "pc_mode": "active", "admin_state": True,
                   "peer1_description": "pilot peer1", "peer2_description": "pilot peer2",
                   "port_type_fast": False, "bpdu_guard": "no", "enable_qos": True,
                   "qos_policy": "pilot_qos", "queuing_policy": "pilot_queue"}
BASE_VPC_TRUNK = dict(BASE_VPC_ACCESS, mode="trunk", peer1_pcid=12, peer2_pcid=12,
                      peer1_allowed_vlans="none", peer2_allowed_vlans="none")
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
            PC_DOT1Q: BASE_PC_DOT1Q, VPC_ACCESS: BASE_VPC_ACCESS,
            VPC_TRUNK: BASE_VPC_TRUNK, LOOPBACK: BASE_LOOPBACK,
            SVI: BASE_SVI}.get(parent, BASE_ACCESS)
    prof = dict(base)
    prof.update(extra)
    return prof


def want_omitting(parent, key, **extra):
    """The WANT of an OMISSION stage: the parent's base profile WITHOUT the key under test.

    WHY `base_for(parent, **extra)` IS NOT ENOUGH.
    The generic matrix used to build the WANT that way, assuming the row's key never appears in
    the base profile. That is true for almost every row -- and FALSE for
    `int_routed_host::ospf_area_id`: `BASE_ROUTED` carries it explicitly. For that row the
    "omission case" was sending the field, so it was not measuring an omission at all; and when
    the row gained a reset, three cases failed against a WANT that contradicted its own name.

    The defect is a CLASS of defect, not a property of that row: any registered identity whose
    key lives in a base profile would have the same problem, silently. Popping the key here closes
    it at the root, and it leaves `extra` intact -- if the row's context needs the field (the area
    lives in `OSPF_CTX`), the row uses `OSPF_CTX_NO_AREA` and the omission stays real.
    """
    w = dict(base_for(parent, **extra))
    w.pop(key, None)
    return w


def iftype_for(parent):
    """The module's `type` for a parent. A port-channel driven as `eth` is not a weaker
    test, it is a different object: the module would resolve a different policy."""
    if parent in VPC_PARENTS:
        return "vpc"
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
    if parent in VPC_PARENTS:
        return "vpc11" if parent == VPC_ACCESS else "vpc12"
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
    if parent in VPC_PARENTS:
        return {"name": ifname_for(parent), "type": "vpc",
                "switch": [SWITCH_IP, PEER_IP], "deploy": deploy,
                "profile": copy.deepcopy(profile)}
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
            if "vpcpair_serial_number" in path:
                return {"RETURN_CODE": 200, "MESSAGE": "OK",
                        "DATA": {"vpc_pair_sn": VPC_PAIR_SERIAL}}
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
                                VPC_ACCESS: "INTERFACE_VPC",
                                VPC_TRUNK: "INTERFACE_VPC",
                                SVI: "INTERFACE_VLAN"}.get(p.get("policy"),
                                                          "INTERFACE_ETHERNET"),
                     "isPhysical": ("false" if p.get("policy") in (SUBIF, LOOPBACK, SVI)
                                    or p.get("policy") in VPC_PARENTS
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
        if any(config.get("type") == "vpc" for config in configs):
            inventory = copy.deepcopy(test.config_data["mock_fab_inv_data"])
            inventory[SWITCH_IP]["isVpcConfigured"] = "True"
            inventory[SWITCH_IP]["vpcDomain"] = 90
            inventory[PEER_IP] = dict(inventory[SWITCH_IP], serialNumber=PEER_SERIAL,
                                      logicalName="placeholder-sw-2")
            test.run_fabric_details.side_effect = [inventory]
            test.run_ip_sn.side_effect = [[{SWITCH_IP: SERIAL, PEER_IP: PEER_SERIAL}, []]]
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
    found[0]["interfaces"][0]["interfaceType"] = (
        "INTERFACE_VPC" if found[0].get("policy") in VPC_PARENTS else "INTERFACE_ETHERNET")
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
