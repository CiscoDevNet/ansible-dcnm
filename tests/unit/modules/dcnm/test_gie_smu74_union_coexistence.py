"""The union-level guarantee neither source campaign could state: BOTH newly accepted
reset families are present in ONE loaded table, together, with their vocabularies intact.

WHY THIS FILE EXISTS AT ALL

ALPHA measured and registered the two routed LLDP booleans; BETA measured and registered the
two routed OSPF enums. Each shipped its own 72-reset candidate and its own test file, and
neither file can see the other's rows: `test_gie_routed_lldp_reset.py` never names
`ospf_passive_mode`, and `test_gie_routed_enum_omission_b3.py` never names
`disable_lldp_transmit`.

The consequence, stated precisely: EACH family's suite passes on ITS OWN candidate and cannot
detect that the other family is missing, because it never asks about those rows. That is not
the same as both suites passing together on an incomplete table -- they do not. Run both on
either 72-reset candidate and the other family's file fails, since its rows carry no reset
there. What is missing is a case that FAILS when one family is absent while the suite that
would have noticed is the one nobody thought to run. So no single-family suite can certify the
union, and the cheapest wrong ways to produce a "74-reset" artifact -- copying one 72-row
candidate over the other, or concatenating two generated tables -- need a guarantee stated at
the union level. That is this file. Measured: it fails 4 of its 8 cases on ALPHA's candidate,
4 on BETA's, 6 on the 70-reset base, and passes 8/8 only on the union.

WHAT THIS FILE DELIBERATELY DOES NOT DUPLICATE

Two sources of the same truth drift apart, so the guards that already exist are referenced,
not reimplemented:

  * row count, identity uniqueness and the no-duplicate-row contract --
    `test_gie_passthrough_bindings.py::test_table_rows_are_unique_and_the_count_is_pinned`;
  * the table was not hand-edited after generation --
    `test_gie_passthrough_bindings.py::test_provenance_recalculates_from_packaged_rows`;
  * index freshness and a replaced table -- `test_gie_binding_indexes.py`;
  * every registered reset has real-`main()` fixture coverage --
    `test_dcnm_intf_withdrawal.py::test_the_fixture_matrix_covers_every_registered_reset`;
  * per-family withdrawal behaviour -- each family's own file.

What is left, and is only expressible once both families are present, is below.

NOT LIVE TESTED IN THIS GENERATION. No controller, Nexus or Jenkins is contacted. The four
resets carry the live acceptance of their own source campaigns; this integrated tuple does
not inherit a fresh live result from that.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    BINDING_TABLE,
    resolve_binding,
    resolve_by_nvpair,
)

ROUTED = "int_routed_host"

# The four additions this integration is the union of, and nothing else.
# (profile_key, parent_nvpair, reset_wire, declared type, family)
LLDP_FAMILY = [
    ("disable_lldp_transmit", "lldpTransmit", "false", "boolean", "lldp"),
    ("disable_lldp_receive", "lldpReceive", "false", "boolean", "lldp"),
]
ENUM_FAMILY = [
    ("ospf_passive_mode", "ospfPassiveMode", "noChange", "enum", "ospf-enum"),
    ("ospf_network_type", "ospfNetworkType", "noChange", "enum", "ospf-enum"),
]
FOUR = LLDP_FAMILY + ENUM_FAMILY
FOUR_IDS = ["%s::%s" % (ROUTED, f[1]) for f in FOUR]

PREVIOUS_RESET_TOTAL = 70
UNION_RESET_TOTAL = 74

# ------------------------------------------------------------------- base88
# TEST-ONLY CHANGE. This file's union guarantee is unchanged: the four routed
# resets must still be present together. What changed is the TOTAL this checkout
# expects, because this checkout carries the OFFLINE B01 union -- the published
# 74 plus the 8 rows ALPHA measured (`int_routed_host` and `int_subif`) and the
# 6 BETA measured (`int_loopback` and `int_vlan`). The integrated portfolio
# remains 74; nothing here asserts otherwise, and no live evidence is
# invalidated or owed a replay by a change to an expectation. Each of the 14
# carries the live acceptance of its OWN source campaign and no other.
#
# Deliberately NOT used: `>=`, `skip`, `xfail`, or deriving the expectation from
# the table under test. Each would make the pin unable to fail.
#
# ------------------------------------------------------- smu174 integration
# 174 = the 70 that preceded the union
#     +   4  the union's own four
#     +  14  base88
#     +  30  OSPF-ALL
#     +  35  EIGRP-ALL
#     +   4  MACsec
#     +  10  BFD-ALL              <- added by this generation
#     +   7  dampening            <- added by this generation, CONTROLLER-ONLY
#
# The total on its own is reachable by registering something else in place of a measured
# row, so the total is pinned AND EVERY LOT IS NAMED BY IDENTITY below, with pairwise
# disjointness and closure asserted. No campaign's accounting is dissolved into a larger
# one: that is the exact error these pins exist for.
#
# REGISTRATION IS NOT ACCEPTANCE, and in this generation the two genuinely differ:
#   167 rows (the reviewed 157 + the 10 BFD) retain source-campaign live acceptance;
#     7 rows (dampening) are CONTROLLER_OMISSION_VERIFIED / DEVICE_NOT_VALIDATED --
#       observed at the controller with deploy false, never validated on NX-OS, and the
#       lab platform does not support that CLI.
# This file pins REGISTRATION only, which is what a table can be asked about. Acceptance
# lives in the campaign reviews, and 174 must not be described as device-validated.
CANDIDATE_RESET_TOTAL = 197

# The additions this candidate is allowed to carry, and nothing else: ALPHA's
# four `int_routed_host` and four `int_subif` rows, plus BETA's two
# `int_loopback` and four `int_vlan` rows. Fourteen, over four parents.
# (parent_template, parent_nvpair, profile_key, reset_wire)
#
# WHY EVERY ROW IS LISTED SEPARATELY RATHER THAN AS A FIELD LIST PER PARENT.
# The four public fields do NOT apply uniformly: `int_loopback` carries only the
# two OSPF booleans -- it has no `ipv6NdSuppressRa` and no `ipv6LinkLocal` row
# to register -- so a per-parent product of 4 fields x 4 parents would demand 16
# and be wrong by two. Each row here was measured on its own parent; none was
# inferred from a sibling parent's result.
#
# NOTE ON THE THREE `ipv6LinkLocal` ROWS. `ipv6LinkLocal` is a STRING, not a
# boolean, so its measured reset is the EMPTY STRING, not "false". The installed
# template says so in its own condition -- `if ipv6LinkLocal != ""` emits the
# child, while the booleans emit on `== "true"`. Registering "false" for it
# would have registered a reset that withdraws nothing, and a test that assumed
# one value for all fourteen rows could not have caught that.
CANDIDATE_ADDITIONS = (
    # PR725-SMU-B01-ALPHA-001 group R, Leaf-103 Ethernet1/64, 2026-09-28
    ("int_routed_host", "ospfMtuIgnore", "ospf_mtu_ignore", "false"),
    ("int_routed_host", "ospfShutdown", "ospf_shutdown", "false"),
    ("int_routed_host", "ipv6NdSuppressRa", "ipv6_nd_suppress_ra", "false"),
    ("int_routed_host", "ipv6LinkLocal", "ipv6_link_local", ""),
    # PR725-SMU-B01-ALPHA-001 group S, Leaf-103 Ethernet1/64.3001, 2026-09-28
    ("int_subif", "ospfMtuIgnore", "ospf_mtu_ignore", "false"),
    ("int_subif", "ospfShutdown", "ospf_shutdown", "false"),
    ("int_subif", "ipv6NdSuppressRa", "ipv6_nd_suppress_ra", "false"),
    ("int_subif", "ipv6LinkLocal", "ipv6_link_local", ""),
    # PR725-SMU-B01-BETA-001, loopback and SVI groups
    ("int_loopback", "ospfMtuIgnore", "ospf_mtu_ignore", "false"),
    ("int_loopback", "ospfShutdown", "ospf_shutdown", "false"),
    ("int_vlan", "ospfMtuIgnore", "ospf_mtu_ignore", "false"),
    ("int_vlan", "ospfShutdown", "ospf_shutdown", "false"),
    ("int_vlan", "ipv6NdSuppressRa", "ipv6_nd_suppress_ra", "false"),
    ("int_vlan", "ipv6LinkLocal", "ipv6_link_local", ""),
    # PR725-OSPF-ALL-001 profile P1 (options), measured in P1-g2-rM-clear on 2026-09-28 over
    # Leaf-103: Ethernet1/64.3001, Loopback20 and Vlan3789, with the campaign's own SMU90RTD
    # process and VLAN 3789 mounted. `int_routed_host` contributes no row here: those two fields
    # were already registered on it and served as RETENTION CONTROLS -- the clear body excluded it.
    #
    # `ospf_network_type` appears THREE times because these are THREE distinct bindings, one per
    # parent, not an inference from the routed row. And the passive pair is TWO fields: int_subif
    # declares the BOOLEAN `ospfPassiveInterface` (reset 'false') while int_vlan declares the ENUM
    # `ospfPassiveMode` (reset 'noChange'). Both emit the SAME CLI line, so reading the CLI does
    # not tell them apart: each needs its own row and its own reset.
    ("int_subif", "ospfNetworkType", "ospf_network_type", "noChange"),
    ("int_subif", "ospfPassiveInterface", "ospf_passive_interface", "false"),
    ("int_loopback", "ospfNetworkType", "ospf_network_type", "noChange"),
    ("int_loopback", "ospfAdvertiseSubnet", "ospf_advertise_subnet", "false"),
    ("int_vlan", "ospfNetworkType", "ospf_network_type", "noChange"),
    ("int_vlan", "ospfPassiveMode", "ospf_passive_mode", "noChange"),
    # PR725-OSPF-ALL-001 profiles P2-BFD and P4-AREA, measured on 2026-09-28.
    # BFD is asymmetric: ospfBfdMode on routed/vlan, ospfBfd on subif/loopback; no parent carries
    # the other's field, and both render the same `ip ospf bfd` line.
    # The area is the campaign's first reset that does NOT delete its line: it returns it to the
    # declared default 0.0.0.0. Demanding that every reset delete a line would have rejected
    # these four.
    ("int_routed_host", "ospfBfdMode", "ospf_bfd_mode", "noChange"),
    ("int_subif", "ospfBfd", "ospf_bfd", "false"),
    ("int_loopback", "ospfBfd", "ospf_bfd", "false"),
    ("int_vlan", "ospfBfdMode", "ospf_bfd_mode", "noChange"),
    # routed::OSPF_AREA_ID is back: with the key GENUINELY ABSENT, the table without the metadata
    # REFUSES the `replaced` while the table with it withdraws the field. The control that had
    # removed this row was not omitting the field at all (BASE_ROUTED already carries it). See the
    # harness.
    ("int_routed_host", "OSPF_AREA_ID", "ospf_area_id", "0.0.0.0"),
    ("int_subif", "OSPF_AREA_ID", "ospf_area_id", "0.0.0.0"),
    ("int_loopback", "OSPF_AREA_ID", "ospf_area_id", "0.0.0.0"),
    ("int_vlan", "OSPF_AREA_ID", "ospf_area_id", "0.0.0.0"),
    # PR725-OSPF-ALL-001 profile P3a message-digest: the gate (4) and the key-ID (4), measured on
    # 2026-09-28. The gate was measured WITH the key and ID retained; the ID was measured with
    # authentication ENABLED. `ospf_auth_key_id` is an `integer` and its reset travels as the
    # STRING '1', which is its declared defaultValue.
    ("int_routed_host", "ospfAuthentication", "enable_ospf_auth", "false"),
    ("int_subif", "ospfAuthentication", "enable_ospf_auth", "false"),
    ("int_loopback", "ospfAuthentication", "enable_ospf_auth", "false"),
    ("int_vlan", "ospfAuthentication", "enable_ospf_auth", "false"),
    ("int_routed_host", "OSPF_AUTH_KEY_ID", "ospf_auth_key_id", "1"),
    ("int_subif", "OSPF_AUTH_KEY_ID", "ospf_auth_key_id", "1"),
    ("int_loopback", "OSPF_AUTH_KEY_ID", "ospf_auth_key_id", "1"),
    ("int_vlan", "OSPF_AUTH_KEY_ID", "ospf_auth_key_id", "1"),
    # PR725-OSPF-ALL-001 profile P3b, SIMPLE authentication: the key, measured on 2026-09-29.
    # A mechanism independent of message-digest; its type stayed at the declared default 3.
    ("int_routed_host", "ospfAuthenticationKey", "ospf_authentication_key", ""),
    ("int_subif", "ospfAuthenticationKey", "ospf_authentication_key", ""),
    ("int_loopback", "ospfAuthenticationKey", "ospf_authentication_key", ""),
    ("int_vlan", "ospfAuthenticationKey", "ospf_authentication_key", ""),
    # P5, the gate, on ALL FOUR parents.
    #
    # int_loopback joined on 2026-09-29, after correcting the SCENARIO -- not the table and not
    # the engine. The previous round measured it with `int_vrf: default` and the device KEPT the
    # line. The installed body of that parent, line 648, emits the association by DISJUNCTION:
    #   configureOspf = (enableOspf == "true" or
    #                    (intfVrf == "default" and linkStateRouting == "ospf"))
    # The second branch does not look at the gate, so in the `default` VRF of a fabric that routes
    # with OSPF the withdrawal is UNOBSERVABLE. Measured in V3-clear with `int_vrf: PR725VRF`: the
    # `ip router ospf <tag> area <x>` line disappeared while interface, VRF and IP survived.
    ("int_routed_host", "ospf", "enable_ospf", "false"),
    ("int_subif", "ospf", "enable_ospf", "false"),
    ("int_vlan", "ospf", "enable_ospf", "false"),
    ("int_loopback", "ospf", "enable_ospf", "false"),
    # PR725-BFD-ALL-001, measured 2026-09-29. `bfdEcho` travelled through the PUBLIC module path
    # (stage B4-echo-clear, with the interval gate ENABLED, which is what isolates its effect).
    # The interval gate and the six integers were measured through the preserving probe (rc 207,
    # per-field readback), because the public validator refuses "" on an integer before any
    # request is built. The interval group is COORDINATED: the parent body refuses to empty a
    # number while the gate is active, so no independent numeric clear exists to test and none
    # is claimed here.
    ("int_routed_host", "bfdEcho", "disable_bfd_echo", "false"),
    ("int_vlan", "bfdEcho", "disable_bfd_echo", "false"),
    ("int_subif", "bfdInterval", "enable_bfd_interval", "false"),
    ("int_vlan", "bfdInterval", "enable_bfd_interval", "false"),
    ("int_subif", "bfdTxInterval", "bfd_tx_interval", ""),
    ("int_subif", "bfdMinRxInterval", "bfd_min_rx_interval", ""),
    ("int_subif", "bfdMultiplier", "bfd_multiplier", ""),
    ("int_vlan", "bfdTxInterval", "bfd_tx_interval", ""),
    ("int_vlan", "bfdMinRxInterval", "bfd_min_rx_interval", ""),
    ("int_vlan", "bfdMultiplier", "bfd_multiplier", ""),
)

# Generated ONCE from the published base74 table, sha256
# 5833ff78b0dcf3fe1dcae12bc56a2ca1a3639271cdf22b76c9ca6500392688fe
# 74 rows with a reset. A FROZEN LITERAL: it is not recomputed at test time.
BASE74_RESETS = (
    ("int_access_host", "aclFilter", ''),
    ("int_access_host", "flowcontrolReceive", 'off'),
    ("int_access_host", "flowcontrolSend", 'off'),
    ("int_access_host", "lldpReceive", 'false'),
    ("int_access_host", "lldpTransmit", 'false'),
    ("int_access_host", "qosStatsSuppressed", 'false'),
    ("int_access_host", "queuingStats", 'false'),
    ("int_access_host", "spanningTreePortType", 'no'),
    ("int_loopback", "ospfCost", ''),
    ("int_loopback", "ospfDeadInterval", ''),
    ("int_loopback", "ospfHelloInterval", ''),
    ("int_loopback", "ospfPriority", ''),
    ("int_loopback", "ospfRetransmitInterval", ''),
    ("int_loopback", "ospfTransmitDelay", ''),
    ("int_port_channel_access_host", "aclFilter", ''),
    ("int_port_channel_access_host", "lldpReceive", 'false'),
    ("int_port_channel_access_host", "lldpTransmit", 'false'),
    ("int_port_channel_access_host", "qosStatsSuppressed", 'false'),
    ("int_port_channel_access_host", "queuingStats", 'false'),
    ("int_port_channel_access_host", "spanningTreePortType", 'no'),
    ("int_port_channel_dot1q_tunnel_host", "aclFilter", ''),
    ("int_port_channel_dot1q_tunnel_host", "lldpReceive", 'false'),
    ("int_port_channel_dot1q_tunnel_host", "lldpTransmit", 'false'),
    ("int_port_channel_dot1q_tunnel_host", "qosStatsSuppressed", 'false'),
    ("int_port_channel_dot1q_tunnel_host", "queuingStats", 'false'),
    ("int_port_channel_dot1q_tunnel_host", "spanningTreePortType", 'no'),
    ("int_port_channel_trunk_host", "GUARD_MODE", 'no'),
    ("int_port_channel_trunk_host", "aclFilter", ''),
    ("int_port_channel_trunk_host", "lldpReceive", 'false'),
    ("int_port_channel_trunk_host", "lldpTransmit", 'false'),
    ("int_port_channel_trunk_host", "qosStatsSuppressed", 'false'),
    ("int_port_channel_trunk_host", "queuingStats", 'false'),
    ("int_port_channel_trunk_host", "spanningTreePortType", 'no'),
    ("int_routed_host", "arpTimeout", ''),
    ("int_routed_host", "ipv4Redirects", 'false'),
    ("int_routed_host", "ipv6Redirects", 'false'),
    ("int_routed_host", "lldpReceive", 'false'),
    ("int_routed_host", "lldpTransmit", 'false'),
    ("int_routed_host", "ospfCost", ''),
    ("int_routed_host", "ospfDeadInterval", ''),
    ("int_routed_host", "ospfHelloInterval", ''),
    ("int_routed_host", "ospfNetworkType", 'noChange'),
    ("int_routed_host", "ospfPassiveMode", 'noChange'),
    ("int_routed_host", "ospfPriority", ''),
    ("int_routed_host", "ospfTransmitDelay", ''),
    ("int_routed_host", "qosStatsSuppressed", 'false'),
    ("int_routed_host", "queuingStats", 'false'),
    ("int_subif", "arpTimeout", ''),
    ("int_subif", "ipv4Redirects", 'false'),
    ("int_subif", "ipv6Redirects", 'false'),
    ("int_subif", "ospfCost", ''),
    ("int_subif", "ospfDeadInterval", ''),
    ("int_subif", "ospfHelloInterval", ''),
    ("int_subif", "ospfPriority", ''),
    ("int_subif", "ospfRetransmitInterval", ''),
    ("int_subif", "ospfTransmitDelay", ''),
    ("int_trunk_host", "GUARD_MODE", 'no'),
    ("int_trunk_host", "aclFilter", ''),
    ("int_trunk_host", "flowcontrolReceive", 'off'),
    ("int_trunk_host", "flowcontrolSend", 'off'),
    ("int_trunk_host", "lldpReceive", 'false'),
    ("int_trunk_host", "lldpTransmit", 'false'),
    ("int_trunk_host", "qosStatsSuppressed", 'false'),
    ("int_trunk_host", "queuingStats", 'false'),
    ("int_trunk_host", "spanningTreePortType", 'no'),
    ("int_vlan", "arpTimeout", ''),
    ("int_vlan", "ipv4Redirects", 'false'),
    ("int_vlan", "ipv6Redirects", 'false'),
    ("int_vlan", "ospfCost", ''),
    ("int_vlan", "ospfDeadInterval", ''),
    ("int_vlan", "ospfHelloInterval", ''),
    ("int_vlan", "ospfPriority", ''),
    ("int_vlan", "ospfRetransmitInterval", ''),
    ("int_vlan", "ospfTransmitDelay", ''),
)

BASE74_IDENTITIES = frozenset((p, nv) for p, nv, _r in BASE74_RESETS)
CANDIDATE_IDENTITIES = frozenset((p, nv) for p, nv, _k, _r in CANDIDATE_ADDITIONS)

# ===================================================== BETA's two lots, kept apart
# PR725-EIGRP-ALL-001 and the MACsec lot arrive from a DIFFERENT campaign than the
# 44 above, and each keeps its own group for the reason BETA stated when it wrote
# them: folding a lot into a bigger tuple dissolves the check that each campaign
# contributed exactly what it measured. The groups are listed by IDENTITY, never
# derived from the parent template -- both campaigns register rows on
# int_routed_host, int_subif, int_vlan and int_loopback, so a parent-based split
# would file one campaign's measurements under the other while the totals still
# added up.
#
# The values below ARE THE MEASUREMENT, written by hand. They are not read back
# from the table under test: an expectation derived from its own subject cannot
# fail.
EIGRP_ADDITIONS = (
    ("int_routed_host", "eigrpRouting", "enable_eigrp_routing", "false"),
    ("int_routed_host", "eigrpShutdown", "enable_eigrp_shutdown", "false"),
    ("int_routed_host", "eigrpIpv6Routing", "enable_eigrp_ipv6_routing", "false"),
    ("int_routed_host", "eigrpIpv4DistributeListPrefixList", "eigrp_ipv4_distribute_list_prefix_list", ""),
    ("int_routed_host", "eigrpIpv6DistributeListPrefixList", "eigrp_ipv6_distribute_list_prefix_list", ""),
    ("int_routed_host", "eigrpIpv4DistributeListDirection", "eigrp_ipv4_distribute_list_direction", "out"),
    ("int_routed_host", "eigrpIpv6DistributeListDirection", "eigrp_ipv6_distribute_list_direction", "out"),
    ("int_subif", "eigrpRouting", "enable_eigrp_routing", "false"),
    ("int_subif", "eigrpShutdown", "enable_eigrp_shutdown", "false"),
    ("int_subif", "eigrpIpv6Routing", "enable_eigrp_ipv6_routing", "false"),
    ("int_subif", "eigrpIpv4DistributeListPrefixList", "eigrp_ipv4_distribute_list_prefix_list", ""),
    ("int_subif", "eigrpIpv6DistributeListPrefixList", "eigrp_ipv6_distribute_list_prefix_list", ""),
    ("int_subif", "eigrpIpv4DistributeListDirection", "eigrp_ipv4_distribute_list_direction", "out"),
    ("int_subif", "eigrpIpv6DistributeListDirection", "eigrp_ipv6_distribute_list_direction", "out"),
    ("int_vlan", "eigrpRouting", "enable_eigrp_routing", "false"),
    ("int_vlan", "eigrpShutdown", "enable_eigrp_shutdown", "false"),
    ("int_vlan", "eigrpIpv6Routing", "enable_eigrp_ipv6_routing", "false"),
    ("int_vlan", "eigrpIpv4DistributeListPrefixList", "eigrp_ipv4_distribute_list_prefix_list", ""),
    ("int_vlan", "eigrpIpv6DistributeListPrefixList", "eigrp_ipv6_distribute_list_prefix_list", ""),
    ("int_vlan", "eigrpIpv4DistributeListDirection", "eigrp_ipv4_distribute_list_direction", "out"),
    ("int_vlan", "eigrpIpv6DistributeListDirection", "eigrp_ipv6_distribute_list_direction", "out"),
    ("int_loopback", "eigrpRouting", "enable_eigrp_routing", "false"),
    ("int_loopback", "eigrpShutdown", "enable_eigrp_shutdown", "false"),
    # Second round: the eight BFD rows, measured in the ALTERNATE profiles p3a/p3b.
    ("int_routed_host", "eigrpBfd", "enable_eigrp_bfd", "false"),
    ("int_routed_host", "eigrpBfdDisable", "disable_eigrp_bfd", "false"),
    ("int_subif", "eigrpBfd", "enable_eigrp_bfd", "false"),
    ("int_subif", "eigrpBfdDisable", "disable_eigrp_bfd", "false"),
    ("int_vlan", "eigrpBfd", "enable_eigrp_bfd", "false"),
    ("int_vlan", "eigrpBfdDisable", "disable_eigrp_bfd", "false"),
    ("int_loopback", "eigrpBfd", "enable_eigrp_bfd", "false"),
    ("int_loopback", "eigrpBfdDisable", "disable_eigrp_bfd", "false"),
    # Third round: the TAG, measured in Experiment A over a CLEAN context
    # (interfaces that never carried `passive`), as a COORDINATED transition.
    ("int_routed_host", "eigrpProcessTag", "eigrp_process_tag", ""),
    ("int_subif", "eigrpProcessTag", "eigrp_process_tag", ""),
    ("int_vlan", "eigrpProcessTag", "eigrp_process_tag", ""),
    ("int_loopback", "eigrpProcessTag", "eigrp_process_tag", ""),
)
EIGRP_IDENTITIES = frozenset((p, nv) for p, nv, _k, _r in EIGRP_ADDITIONS)

# The EIGRP identities deliberately NOT registered, named so their absence is an
# ASSERTION rather than an oversight: their clear does not converge, or they were
# isolated by operator decision. Their dispositions remain unresolved upstream and
# this integration does not resolve them.
EIGRP_WITHHELD = frozenset(
    [(p, nv) for p in ("int_routed_host", "int_subif", "int_vlan", "int_loopback")
     for nv in ("eigrpIpv4Passive", "eigrpNoIpv6Passive",
                "eigrpNoIpv4Passive")])

# The MACsec lot -- its own group, same reasoning.
#
# All FOUR live on `int_routed_host`, the only parent that declares them, and all
# four were measured live on one routed ethernet interface:
#   `macsecFallbackKeyChainName` was measured ALONE, gate still enabled and
#      keychain and policy intact: the ONLY INDEPENDENT withdrawal this set admits,
#      because it is the only IsShow field that is not IsMandatory.
#   the other THREE were measured TOGETHER. Two live negative controls show the
#      controller refusing, BY FIELD NAME, to empty keychain or policy while the
#      gate is enabled. Independent withdrawal of the GATE ALONE was NOT RUN --
#      not controller-refused; the source review corrects the campaign prose that
#      said three were independently refused.
MACSEC_ADDITIONS = (
    ("int_routed_host", "macsecInterfacePolicy", "enable_macsec_interface_policy", "false"),
    ("int_routed_host", "macsecKeyChainName", "macsec_key_chain_name", ""),
    ("int_routed_host", "macsecPolicyName", "macsec_policy_name", ""),
    ("int_routed_host", "macsecFallbackKeyChainName", "macsec_fallback_key_chain_name", ""),
)
MACSEC_IDENTITIES = frozenset((p, nv) for p, nv, _k, _r in MACSEC_ADDITIONS)

# Every addition this checkout is allowed to carry over the published 74, by lot.


# The DAMPENING lot -- EXPERIMENTAL / CONTROLLER-ONLY, its own named group.
#
# READ THIS BEFORE USING THE NUMBER. These seven are CANDIDATES registered in a LOCAL
# EXPERIMENTAL generation so that the omission path can be executed and observed at the
# controller. They are NOT accepted device resets, they are NOT part of the 157 integration,
# and 134 is NOT a portfolio figure. Nothing was deployed in the campaign that produced them,
# so no device acceptance exists for any of the seven. See
# investigations/pr725-dampening-all/EXPERIMENTAL_LEDGER.md.
#
# Kept apart from the other lots for the same reason they are kept apart from each other:
# folding an experimental group into an accepted total is exactly how an unaccepted row gets
# counted as accepted.
#
# All seven live on `int_routed_host` -- the only parent that declares dampening. Two booleans
# reset with the wire string 'false', five integers with ''.
DAMPENING_EXPERIMENTAL_ADDITIONS = (
    ("int_routed_host", "dampening", "enable_dampening", "false"),
    ("int_routed_host", "dampeningRestart", "dampening_restart", "false"),
    ("int_routed_host", "dampeningHalfLife", "dampening_half_life", ""),
    ("int_routed_host", "dampeningReuse", "dampening_reuse", ""),
    ("int_routed_host", "dampeningSuppress", "dampening_suppress", ""),
    ("int_routed_host", "dampeningMaxSuppress", "dampening_max_suppress", ""),
    ("int_routed_host", "dampeningRestartPenalty", "dampening_restart_penalty", ""),
)
DAMPENING_EXPERIMENTAL_IDENTITIES = frozenset(
    (p, nv) for p, nv, _k, _r in DAMPENING_EXPERIMENTAL_ADDITIONS)

# Two reviewed source campaigns added in this integration. The explicit tuples
# are independent oracles: an addition cannot replace a missing older reset and
# still pass the total or closure checks below.
PIMACL_ADDITIONS = (
    ("int_loopback", "ENABLE_PIM_SPARSE", "enable_pim_sparse", "false"),
    ("int_routed_host", "ENABLE_PIM_SPARSE", "enable_pim_sparse", "false"),
    ("int_subif", "ENABLE_PIM_SPARSE", "enable_pim_sparse", "false"),
    ("int_vlan", "ENABLE_PIM_SPARSE", "enable_pim_sparse", "false"),
    ("int_routed_host", "PIM_DR_PRIORITY", "pim_dr_priority", "1"),
    ("int_subif", "PIM_DR_PRIORITY", "pim_dr_priority", "1"),
    ("int_vlan", "PIM_DR_PRIORITY", "pim_dr_priority", "1"),
    ("int_routed_host", "ipv4AclIn", "ipv4_acl_in", ""),
    ("int_vlan", "ipv4AclIn", "ipv4_acl_in", ""),
    ("int_routed_host", "pimBfdInstance", "enable_pim_bfd_instance", "false"),
)
PIMACL_IDENTITIES = frozenset((p, nv) for p, nv, _k, _r in PIMACL_ADDITIONS)

VPC13_ADDITIONS = tuple(
    (p, nv, key, reset)
    for p in ("int_vpc_access_host", "int_vpc_trunk_host")
    for nv, key, reset in (
        ("aclFilter", "acl_filter", ""),
        ("lldpReceive", "disable_lldp_receive", "false"),
        ("lldpTransmit", "disable_lldp_transmit", "false"),
        ("qosStatsSuppressed", "disable_qos_stats", "false"),
        ("queuingStats", "disable_queuing_stats", "false"),
        ("spanningTreePortType", "spanning_tree_port_type", "no"),
    )
) + (("int_vpc_trunk_host", "GUARD_MODE", "guard_mode", "no"),)
VPC13_IDENTITIES = frozenset((p, nv) for p, nv, _k, _r in VPC13_ADDITIONS)

# Every addition this checkout carries over the published 74, by lot. The dampening lot is
# included in the SET arithmetic -- it is registered, so it must be accounted for -- while its
# controller-only evidence status is recorded above and asserted in its own grouped test.
ALL_ADDITIONS = (CANDIDATE_ADDITIONS + EIGRP_ADDITIONS + MACSEC_ADDITIONS
                 + DAMPENING_EXPERIMENTAL_ADDITIONS + PIMACL_ADDITIONS
                 + VPC13_ADDITIONS)
ALL_ADDED_IDENTITIES = (CANDIDATE_IDENTITIES | EIGRP_IDENTITIES | MACSEC_IDENTITIES
                        | DAMPENING_EXPERIMENTAL_IDENTITIES | PIMACL_IDENTITIES
                        | VPC13_IDENTITIES)


def _rows():
    return list(BINDING_TABLE.values()) if isinstance(BINDING_TABLE, dict) else list(BINDING_TABLE)


def _registered_resets():
    return {(r["parent_template"], r["parent_nvpair"]) for r in _rows()
            if r.get("reset_wire") is not None}


@pytest.mark.parametrize("key,nvpair,reset,declared_type,_family", FOUR, ids=FOUR_IDS)
def test_each_of_the_four_resolves_from_the_actual_loaded_table(
    key, nvpair, reset, declared_type, _family
):
    """Resolved from the table the runtime really imported, by BOTH identity paths, and both
    paths must hand back the SAME row object -- a table assembled by concatenation could
    answer one path and not the other, or answer each from a different row."""
    by_key = resolve_binding(ROUTED, key)
    by_nv = resolve_by_nvpair(ROUTED, nvpair)
    assert by_key is not None, "%s::%s is absent from the loaded table" % (ROUTED, key)
    assert by_nv is not None, "%s::%s is absent from the nvPair index" % (ROUTED, nvpair)
    assert by_key is by_nv, (
        "the two identity paths for %s::%s resolved to different row objects, so the table "
        "or its indexes carry that identity twice" % (ROUTED, nvpair))
    assert by_key["parent_nvpair"] == nvpair
    assert by_key["type"] == declared_type
    assert by_key.get("reset_wire") == reset
    # The type of the reset, not only its text. The controller returns this nvPair as a
    # string, so the reset must be the string. A native bool is not interchangeable with it
    # in either direction: `False == "false"` is False, so the comparison against a HAVE
    # would never match, and in a boolean test the two are OPPOSITE -- the non-empty string
    # "false" is truthy while native False is falsy.
    assert isinstance(by_key["reset_wire"], str), (
        "%s::%s reset_wire is %s; it must be the wire STRING"
        % (ROUTED, nvpair, type(by_key["reset_wire"]).__name__))


def test_both_families_are_present_together_not_one_or_the_other():
    """The defect this file exists for. Either source candidate alone satisfies its own
    suite; only the union satisfies this."""
    registered = _registered_resets()
    lldp = [(ROUTED, nv) for _k, nv, _r, _t, _f in LLDP_FAMILY]
    enums = [(ROUTED, nv) for _k, nv, _r, _t, _f in ENUM_FAMILY]
    missing_lldp = [i for i in lldp if i not in registered]
    missing_enum = [i for i in enums if i not in registered]
    assert not missing_lldp and not missing_enum, (
        "only one family is registered, so this is a single-campaign candidate rather than "
        "the union.\n  LLDP rows missing: %s\n  OSPF enum rows missing: %s"
        % (missing_lldp, missing_enum))


def test_the_registered_reset_total_is_the_previous_seventy_plus_these_four():
    """157 = 70 + the union's 4 + base88's 14 + OSPF-ALL's 30 + EIGRP's 35 + MACsec's 4.

    The total alone is reachable by registering something else instead of one of them, so
    the total is pinned AND EVERY LOT IS NAMED. The union's own four are still required to
    be present together, which is this file's original guarantee and is not weakened by
    the counts growing around it.
    """
    registered = _registered_resets()
    assert len(registered) == CANDIDATE_RESET_TOTAL, (
        "the loaded table registers %d resets, expected %d"
        % (len(registered), CANDIDATE_RESET_TOTAL))

    four = {(ROUTED, nv) for _k, nv, _r, _t, _f in FOUR}
    assert four <= registered, "not all four accepted resets are registered: %s" % (
        sorted(four - registered),)

    assert CANDIDATE_IDENTITIES <= registered, (
        "this candidate's additions are not registered: %s"
        % (sorted(CANDIDATE_IDENTITIES - registered),))
    assert EIGRP_IDENTITIES <= registered, (
        "the EIGRP lot's additions are not registered: %s"
        % (sorted(EIGRP_IDENTITIES - registered),))
    assert MACSEC_IDENTITIES <= registered, (
        "the MACsec lot's additions are not registered: %s"
        % (sorted(MACSEC_IDENTITIES - registered),))
    assert len(PIMACL_IDENTITIES) == len(PIMACL_ADDITIONS) == 10
    assert len(VPC13_IDENTITIES) == len(VPC13_ADDITIONS) == 13
    assert PIMACL_IDENTITIES <= registered and VPC13_IDENTITIES <= registered
    groups = (CANDIDATE_IDENTITIES, EIGRP_IDENTITIES, MACSEC_IDENTITIES,
              DAMPENING_EXPERIMENTAL_IDENTITIES, PIMACL_IDENTITIES, VPC13_IDENTITIES)
    for pos, group in enumerate(groups):
        for prior in groups[:pos]:
            assert not group & prior, "two source lots overlap"

    # The DAMPENING lot, named exactly like the others.
    assert DAMPENING_EXPERIMENTAL_IDENTITIES <= registered, (
        "the dampening additions are not registered: %s"
        % (sorted(DAMPENING_EXPERIMENTAL_IDENTITIES - registered),))
    assert len(DAMPENING_EXPERIMENTAL_IDENTITIES) == len(DAMPENING_EXPERIMENTAL_ADDITIONS) == 7, (
        "the dampening lot declares %d additions over %d distinct identities; expected 7 and 7"
        % (len(DAMPENING_EXPERIMENTAL_ADDITIONS), len(DAMPENING_EXPERIMENTAL_IDENTITIES)))
    assert {p for p, _nv in DAMPENING_EXPERIMENTAL_IDENTITIES} == {"int_routed_host"}, (
        "a dampening addition sits on a parent that does not declare dampening: %s"
        % (sorted({p for p, _nv in DAMPENING_EXPERIMENTAL_IDENTITIES} - {"int_routed_host"}),))
    assert not (DAMPENING_EXPERIMENTAL_IDENTITIES
                & (CANDIDATE_IDENTITIES | EIGRP_IDENTITIES | MACSEC_IDENTITIES)), (
        "the dampening lot overlaps another lot: %s"
        % (sorted(DAMPENING_EXPERIMENTAL_IDENTITIES
                  & (CANDIDATE_IDENTITIES | EIGRP_IDENTITIES | MACSEC_IDENTITIES)),))
    by_id = {(r["parent_template"], r["parent_nvpair"]): r for r in _rows()}
    for parent, nvpair, _key, reset in DAMPENING_EXPERIMENTAL_ADDITIONS:
        row = by_id.get((parent, nvpair))
        assert row is not None, "%s::%s is absent" % (parent, nvpair)
        assert row.get("reset_wire") == reset, (
            "%s::%s reset is %r, declared %r" % (parent, nvpair, row.get("reset_wire"), reset))
        assert isinstance(row["reset_wire"], str), (
            "%s::%s reset_wire is %s; it must be the wire STRING"
            % (parent, nvpair, type(row["reset_wire"]).__name__))

    # Setting EVERY lot aside BY NAME must leave exactly the 70 that preceded the union.
    # Subtracting names rather than a number is what stops a foreign row from entering while a
    # measured one goes missing and the total still balances.
    rest = registered - four - ALL_ADDED_IDENTITIES
    assert len(rest) == PREVIOUS_RESET_TOTAL, (
        "setting the union's four, base88's fourteen, OSPF-ALL's thirty, the EIGRP lot's "
        "thirty-five and the MACsec lot's four aside leaves %d resets, expected %d"
        % (len(rest), PREVIOUS_RESET_TOTAL))

    # The three lots must be pairwise DISJOINT and sized exactly as measured.
    assert len(EIGRP_IDENTITIES) == len(EIGRP_ADDITIONS) == 35, (
        "the EIGRP lot declares %d additions over %d distinct identities; expected 35 and 35"
        % (len(EIGRP_ADDITIONS), len(EIGRP_IDENTITIES)))
    assert len(MACSEC_IDENTITIES) == len(MACSEC_ADDITIONS) == 4, (
        "the MACsec lot declares %d additions over %d distinct identities; expected 4 and 4"
        % (len(MACSEC_ADDITIONS), len(MACSEC_IDENTITIES)))
    assert {p for p, _nv in MACSEC_IDENTITIES} == {"int_routed_host"}, (
        "a MACsec addition sits on a parent that does not declare MACsec: %s"
        % (sorted({p for p, _nv in MACSEC_IDENTITIES} - {"int_routed_host"}),))
    for n1, g1, n2, g2 in (
        ("base88+OSPF-ALL", CANDIDATE_IDENTITIES, "EIGRP", EIGRP_IDENTITIES),
        ("base88+OSPF-ALL", CANDIDATE_IDENTITIES, "MACsec", MACSEC_IDENTITIES),
        ("EIGRP", EIGRP_IDENTITIES, "MACsec", MACSEC_IDENTITIES),
    ):
        assert not (g1 & g2), "%s and %s lots overlap on %s" % (n1, n2, sorted(g1 & g2))
    # 54 = base88's 14 + OSPF-ALL's 30 + BFD-ALL's 10, which ALPHA carried inside
    # CANDIDATE_ADDITIONS; the other three lots keep their own tuples. 54 + 35 + 4 + 7 = 100,
    # and 74 + 100 = 174. Written as the sum so the arithmetic is visible rather than a bare
    # total somebody has to take on trust.
    assert len(ALL_ADDED_IDENTITIES) == 54 + 35 + 4 + 7 + 10 + 13 == len(ALL_ADDITIONS), (
        "the lots together declare %d additions over %d distinct identities; expected 123"
        % (len(ALL_ADDITIONS), len(ALL_ADDED_IDENTITIES)))

    # NEGATIVE CONTROL: the withheld EIGRP identities must still carry NO reset. Without
    # this, promoting one by accident would raise the total and nothing would notice.
    leaked_withheld = EIGRP_WITHHELD & registered
    assert not leaked_withheld, (
        "withheld EIGRP identities appear registered: %s" % (sorted(leaked_withheld),))

    # Value AND type of every lot addition. The gate resets with the STRING "false", not
    # the bool: `False == "false"` is False, so a bool would never match a controller HAVE,
    # and in a boolean test the two are OPPOSITE -- the non-empty string "false" is truthy
    # while native `False` is falsy.
    by_identity = {(r["parent_template"], r["parent_nvpair"]): r for r in _rows()}
    for parent, nvpair, _key, reset in EIGRP_ADDITIONS + MACSEC_ADDITIONS:
        row = by_identity.get((parent, nvpair))
        assert row is not None, "%s::%s is absent from the table" % (parent, nvpair)
        assert row.get("reset_wire") == reset, (
            "%s::%s reset is %r, measured %r"
            % (parent, nvpair, row.get("reset_wire"), reset))
        assert isinstance(row["reset_wire"], str), (
            "%s::%s reset_wire is %s; it must be the wire STRING"
            % (parent, nvpair, type(row["reset_wire"]).__name__))

    # The two authors' contributions must be DISJOINT. Fourteen distinct identities is the
    # property that distinguishes a real union from one author's candidate with the other's
    # count written on it: if a row were claimed by both, the total would still be reachable
    # while one measured row went missing.
    assert len(CANDIDATE_IDENTITIES) == len(CANDIDATE_ADDITIONS) == 54, (
        "the candidate declares %d additions over %d distinct identities; expected 54 and 54"
        % (len(CANDIDATE_ADDITIONS), len(CANDIDATE_IDENTITIES)))
    # THE GROUPS ARE NAMED BY CAMPAIGN, NOT DERIVED FROM THE PARENT.
    #
    # The earlier version split them by parent template: int_routed_host+int_subif = ALPHA,
    # int_loopback+int_vlan = BETA. That held only while each author owned two parents. P1
    # registers rows on int_subif, int_loopback AND int_vlan, so a parent-based split would
    # silently file P1's six rows under B01 while the two counts still added up to 20 --
    # attributing measurements to a campaign that never made them.
    #
    # Each group is therefore listed by identity. Adding rows next means declaring them here,
    # which is the property worth keeping: the total can never be reached by registering
    # something else instead of a measured row.
    B01_ALPHA = {
        ("int_routed_host", "ospfMtuIgnore"), ("int_routed_host", "ospfShutdown"),
        ("int_routed_host", "ipv6NdSuppressRa"), ("int_routed_host", "ipv6LinkLocal"),
        ("int_subif", "ospfMtuIgnore"), ("int_subif", "ospfShutdown"),
        ("int_subif", "ipv6NdSuppressRa"), ("int_subif", "ipv6LinkLocal"),
    }
    B01_BETA = {
        ("int_loopback", "ospfMtuIgnore"), ("int_loopback", "ospfShutdown"),
        ("int_vlan", "ospfMtuIgnore"), ("int_vlan", "ospfShutdown"),
        ("int_vlan", "ipv6NdSuppressRa"), ("int_vlan", "ipv6LinkLocal"),
    }
    OSPF_ALL_P1 = {
        ("int_subif", "ospfNetworkType"), ("int_subif", "ospfPassiveInterface"),
        ("int_loopback", "ospfNetworkType"), ("int_loopback", "ospfAdvertiseSubnet"),
        ("int_vlan", "ospfNetworkType"), ("int_vlan", "ospfPassiveMode"),
    }
    # P2/P4 is a group NAMED apart from P1: it shares parents with both P1 and B01, so a
    # parent-based partition would again file them under the wrong campaign.
    OSPF_ALL_P2_P4 = {
        ("int_routed_host", "ospfBfdMode"), ("int_subif", "ospfBfd"),
        ("int_loopback", "ospfBfd"), ("int_vlan", "ospfBfdMode"),
        ("int_routed_host", "OSPF_AREA_ID"), ("int_subif", "OSPF_AREA_ID"),
        ("int_loopback", "OSPF_AREA_ID"), ("int_vlan", "OSPF_AREA_ID"),
    }
    OSPF_ALL_P3A = {(p, nv) for p in ("int_routed_host", "int_subif", "int_loopback", "int_vlan")
                    for nv in ("ospfAuthentication", "OSPF_AUTH_KEY_ID")}
    OSPF_ALL_P3B = {(p, "ospfAuthenticationKey") for p in
                    ("int_routed_host", "int_subif", "int_loopback", "int_vlan")}
    OSPF_ALL_P5 = {(p, "ospf") for p in
                   ("int_routed_host", "int_subif", "int_loopback", "int_vlan")}
    BFD_ECHO = {(p, "bfdEcho") for p in ("int_routed_host", "int_vlan")}
    BFD_INTERVAL = {(p, nv) for p in ("int_subif", "int_vlan")
                    for nv in ("bfdInterval", "bfdTxInterval", "bfdMinRxInterval",
                               "bfdMultiplier")}
    # The two lots from the other campaign join the SAME named-group discipline, so the
    # closure assertion below covers all 83 additions rather than only the 44.
    groups = (("B01/ALPHA", B01_ALPHA, 8), ("B01/BETA", B01_BETA, 6),
              ("OSPF-ALL/P1", OSPF_ALL_P1, 6), ("OSPF-ALL/P2+P4", OSPF_ALL_P2_P4, 8),
              ("OSPF-ALL/P3a", OSPF_ALL_P3A, 8),
              ("OSPF-ALL/P3b", OSPF_ALL_P3B, 4),
              ("OSPF-ALL/P5", OSPF_ALL_P5, 4),
              # BFD-ALL joins the same named-group discipline, split the way the campaign
              # measured it: `bfdEcho` through the public module path on two parents, and the
              # interval gate plus its three numbers as ONE COORDINATED group on two parents.
              # The eight are not eight independent removals and are not presented as such.
              ("BFD-ALL/echo", BFD_ECHO, 2),
              ("BFD-ALL/interval", BFD_INTERVAL, 8),
              # DAMPENING is registered and therefore counted, but its evidence is
              # CONTROLLER-ONLY. Naming it separately is what keeps an unaccepted row from
              # being counted as accepted inside a larger total.
              ("DAMPENING/controller-only", set(DAMPENING_EXPERIMENTAL_IDENTITIES), 7),
              ("EIGRP-ALL", set(EIGRP_IDENTITIES), 35),
              ("MACSEC", set(MACSEC_IDENTITIES), 4),
              ("PIM/ACL", set(PIMACL_IDENTITIES), 10),
              ("vPC", set(VPC13_IDENTITIES), 13))
    for name, group, expected in groups:
        assert len(group) == expected, (
            "%s declares %d identities, expected %d" % (name, len(group), expected))
    for i, (n1, g1, _e) in enumerate(groups):
        for n2, g2, _e2 in groups[i + 1:]:
            assert not (g1 & g2), "%s and %s overlap on %s" % (n1, n2, sorted(g1 & g2))
    union = (B01_ALPHA | B01_BETA | OSPF_ALL_P1 | OSPF_ALL_P2_P4 | OSPF_ALL_P3A
             | OSPF_ALL_P3B | OSPF_ALL_P5 | BFD_ECHO | BFD_INTERVAL
             | EIGRP_IDENTITIES | MACSEC_IDENTITIES | DAMPENING_EXPERIMENTAL_IDENTITIES
             | PIMACL_IDENTITIES | VPC13_IDENTITIES)
    assert union == set(ALL_ADDED_IDENTITIES), (
        "the named campaign groups are not exactly the declared additions.\n"
        "  in a group but not declared: %s\n  declared but in no group: %s"
        % (sorted(union - set(ALL_ADDED_IDENTITIES)),
           sorted(set(ALL_ADDED_IDENTITIES) - union)))
    assert len(union) == 123, (
        "the named groups cover %d identities; the delta over the published 74 is "
        "14 base88 + 30 OSPF-ALL + 10 BFD-ALL + 35 EIGRP + 4 MACsec + 7 dampening "
        "+ 10 PIM/ACL + 13 vPC = 123, and 74 + 123 = 197" % len(union))


def test_the_published_seventy_four_are_present_unaltered_and_nothing_else_was_added():
    """The 74 published identities, by NAME and by RESET VALUE, plus exactly fourteen additions.

    Pinned against a literal frozen ONCE from the published base74 table
    (sha256 5833ff78...), not recomputed from the table under test: an expectation derived
    from its own subject cannot fail. Therefore a FOREIGN addition, an ABSENCE, or an
    ALTERED reset each fail here.
    """
    rows = _rows()
    registered = _registered_resets()

    # 1. Set equality, so neither a foreign addition nor an absence can hide. EVERY lot is set
    #    aside BY NAME -- base88's 14, OSPF-ALL's 30 and BFD-ALL's 10 inside CANDIDATE_IDENTITIES,
    #    plus EIGRP's 35, MACsec's 4 and dampening's 7 -- and what remains must be EXACTLY the
    #    published 74. Setting them aside by name, rather than subtracting a count, is what stops
    #    a foreign row from entering while a measured one goes missing and the arithmetic works.
    assert registered - ALL_ADDED_IDENTITIES == set(BASE74_IDENTITIES), (
        "the candidate's resets minus its own additions are not exactly the published 74.\n"
        "  unexpected: %s\n  missing: %s"
        % (sorted((registered - ALL_ADDED_IDENTITIES) - BASE74_IDENTITIES),
           sorted(BASE74_IDENTITIES - (registered - ALL_ADDED_IDENTITIES))))

    # 2. Value and type of every published reset, unaltered. A row whose reset text or
    #    type changed keeps its identity, so step 1 alone would not notice.
    by_identity = {(r["parent_template"], r["parent_nvpair"]): r for r in rows}
    for parent, nvpair, reset in BASE74_RESETS:
        row = by_identity.get((parent, nvpair))
        assert row is not None, "%s::%s vanished from the table" % (parent, nvpair)
        assert row.get("reset_wire") == reset, (
            "%s::%s reset changed: %r, published %r"
            % (parent, nvpair, row.get("reset_wire"), reset))
        assert isinstance(row["reset_wire"], type(reset)), (
            "%s::%s reset type changed: %s, published %s"
            % (parent, nvpair, type(row["reset_wire"]).__name__, type(reset).__name__))

    # 3. EVERY addition of EVERY lot, by identity AND by value AND by type -- and reachable
    #    by the public profile_key, not only by nvPair. The MACsec four are included here as
    #    well as in their own value check above, so the public-key resolution property covers
    #    them too.
    for parent, nvpair, profile_key, reset in ALL_ADDITIONS:
        row = by_identity.get((parent, nvpair))
        assert row is not None, "%s::%s is absent" % (parent, nvpair)
        assert row["profile_key"] == profile_key, (
            "%s::%s public key is %r, expected %r"
            % (parent, nvpair, row["profile_key"], profile_key))
        assert row.get("reset_wire") == reset, (
            "%s::%s reset is %r, expected %r" % (parent, nvpair, row.get("reset_wire"), reset))
        assert isinstance(row["reset_wire"], str), (
            "%s::%s reset_wire is %s; the controller returns this nvPair as a string"
            % (parent, nvpair, type(row["reset_wire"]).__name__))
        # THE NEUTRAL VALUE PER DECLARED TYPE, and the rule now covers three types, not two.
        #
        # The earlier form was `"" if type == "string" else "false"`, written when every
        # addition was a boolean or a string. P1 adds ENUM rows whose measured reset is
        # `noChange`, so that form demanded "false" of them and failed -- correctly, against an
        # incomplete rule rather than against the measurement.
        #
        # Pinning per declared type still catches the copy-paste it was built for: putting
        # "false" on a string row, or on an enum row, is rejected. And an enum's neutral is not
        # invented here -- it must be the wire spelling its own `wire_values` maps `no_change`
        # to, checked below, so this table cannot drift from the registry's own vocabulary.
        # A ROW'S NEUTRAL IS ITS DECLARED DEFAULT, not a value fixed per type.
        #
        # The earlier version used a type->neutral map (`string` -> `""`). It failed against
        # `ospf_area_id`, which is a `string` whose declared default is `0.0.0.0`: demanding `""`
        # of it would have rejected four measured rows for the wrong reason, and `""` violates its
        # own `minLength=1`. The map remains as a FALLBACK for rows with no declared default.
        #
        # The ORACLE for the value is still the literal in `CANDIDATE_ADDITIONS`, checked above;
        # this is a COHERENCE check between two independent fields of the row, which catches a
        # drift between the reset and the default the template declares.
        #
        # `integer` is covered DELIBERATELY, as the rule itself demanded: an integer row's neutral
        # is the STRING form of its declared default -- `ospf_auth_key_id` declares
        # `defaultValue = 1` and its measured reset is '1'. The empty string does NOT serve there:
        # it would trip V4.
        neutral_by_type = {"string": "", "boolean": "false", "enum": "noChange", "integer": ""}
        assert row["type"] in neutral_by_type, (
            "%s::%s declares type %r, which this rule does not cover; add it deliberately"
            % (parent, nvpair, row["type"]))
        # THE DECLARED DEFAULT COMES IN PUBLIC VOCABULARY; THE RESET COMES IN WIRE VOCABULARY.
        # An enum's `default_template` is `no_change` while its `reset_wire` is `noChange`:
        # comparing them directly conflates the two vocabularies, which is exactly the distinction
        # this campaign is built on -- and an earlier version of this guard conflated them inside
        # itself. For an enum the default is TRANSLATED through the row's `wire_values` before the
        # comparison.
        declared = row.get("default_template")
        vocab = row.get("wire_values") or {}
        if parent in ("int_vpc_access_host", "int_vpc_trunk_host") and row["type"] == "enum":
            # These vPC templates declare the neutral "no" in validValues but
            # the generated row has no default_template. ALPHA measured "no"
            # on both parents, so use that independent source oracle here.
            expected, source_of_expectation = "no", "the measured vPC enum neutral"
        elif row["type"] == "enum" and isinstance(declared, str) and declared in vocab:
            expected = vocab[declared]
            source_of_expectation = "the declared default %r translated to wire" % declared
        elif isinstance(declared, str) and declared != "":
            expected = declared
            source_of_expectation = "the default the template declares"
        elif declared is False:
            expected, source_of_expectation = "false", "the declared boolean default"
        elif row["type"] == "integer" and isinstance(declared, int):
            expected, source_of_expectation = str(declared), (
                "the declared integer default, in string form")
        else:
            expected, source_of_expectation = neutral_by_type[row["type"]], (
                "the neutral of type %r" % row["type"])
        assert row["reset_wire"] == expected, (
            "%s::%s: its reset is %r while %s is %r. A reset that does not match its own "
            "template's default withdraws something other than what the template would restore."
            % (parent, nvpair, row["reset_wire"], source_of_expectation, expected))
        # THE ENUM POST-CHECK IS GATED ON `wire_values`, AND THAT GATE IS THE MERGE.
        #
        # The OSPF-ALL version asserted, for EVERY enum, that `wire_values["no_change"]`
        # equals the reset and that the reset is NOT among the public `valid_values`. That
        # holds for the OSPF enums, whose public neutral `no_change` maps to the wire-only
        # spelling `noChange`. It is FALSE for the enums the other campaign registered:
        # `eigrp_ipv4_distribute_list_direction` declares `valid_values=('in','out')` with no
        # neutral at all, and its measured reset `out` IS its declared default and IS a public
        # choice. Run unconditionally, that assertion fails on all sixteen enums that have no
        # vocabulary map -- the four EIGRP direction rows plus base88's own flowcontrol,
        # spanning-tree and guard-mode rows.
        #
        # The distinguishing property is not "does it have a no_change choice" but "does the
        # binding declare a wire vocabulary at all". Measured over the integrated table: 25
        # enum rows carry a reset, 9 declare `wire_values` and 16 do not. So:
        #
        #   with `wire_values`    -> public and wire spellings differ; the reset must be the
        #                            wire form of `no_change`, and that wire form must NOT
        #                            have leaked into the public choices.
        #   without `wire_values` -> there is no vocabulary split; the reset IS the declared
        #                            default verbatim, and it legitimately IS a public choice.
        #
        # Both campaigns' guarantees are kept, each applied to the family it governs. Neither
        # is loosened: the branch below asserts something in BOTH cases.
        if row["type"] == "enum":
            vocab = row.get("wire_values") or {}
            choices = row.get("valid_values") or ()
            if vocab:
                assert vocab.get("no_change") == row["reset_wire"], (
                    "%s::%s declares a wire vocabulary, so its reset must be the wire form of "
                    "the public neutral; `no_change` maps to %r, not to %r"
                    % (parent, nvpair, vocab.get("no_change"), row["reset_wire"]))
                assert row["reset_wire"] not in choices, (
                    "%s::%s wire spelling %r leaked into the public valid_values %r"
                    % (parent, nvpair, row["reset_wire"], choices))
            else:
                declared_neutral = ("no" if parent in
                                    ("int_vpc_access_host", "int_vpc_trunk_host")
                                    else row.get("default_template"))
                assert row["reset_wire"] == declared_neutral, (
                    "%s::%s declares no wire vocabulary, so its reset must be its declared "
                    "default verbatim; reset is %r and the default is %r"
                    % (parent, nvpair, row["reset_wire"], declared_neutral))
                assert row["reset_wire"] in choices, (
                    "%s::%s has no wire vocabulary, so its reset %r must be one of its public "
                    "valid_values %r" % (parent, nvpair, row["reset_wire"], choices))
        assert resolve_binding(parent, profile_key) is row, (
            "%s::%s does not resolve to the same row by its public key"
            % (parent, profile_key))


def test_merging_the_two_families_did_not_cross_contaminate_their_vocabularies():
    """The two families express "withdrawn" differently, and the merge must keep them apart.

    A boolean row's reset is the wire string of a native `False` and it declares NO SMU
    vocabulary. An enum row's reset is the neutral WIRE spelling `noChange`, it declares a
    vocabulary whose public neutral is `no_change`, and the wire spelling must NOT have been
    added to the public choices: registering a reset may not widen the public schema.
    """
    for key, nvpair, reset, _t, _f in LLDP_FAMILY:
        b = resolve_binding(ROUTED, key)
        assert b.get("wire_values") is None, (
            "%s::%s gained an SMU vocabulary it never had; the enum family's wire_values "
            "leaked onto a boolean row" % (ROUTED, nvpair))
        assert b["default_template"] is False, (
            "%s::%s declared default changed: %r" % (ROUTED, nvpair, b["default_template"]))
        assert reset == "false"

    for key, nvpair, reset, _t, _f in ENUM_FAMILY:
        b = resolve_binding(ROUTED, key)
        vocabulary = b.get("wire_values")
        assert vocabulary, "%s::%s lost its SMU vocabulary" % (ROUTED, nvpair)
        assert vocabulary["no_change"] == reset, (
            "%s::%s public neutral maps to %r, not to the registered reset %r"
            % (ROUTED, nvpair, vocabulary.get("no_change"), reset))
        assert "no_change" in b["valid_values"]
        assert reset not in b["valid_values"], (
            "%s::%s wire spelling %r leaked into the public valid_values"
            % (ROUTED, nvpair, reset))
        assert b["default_template"] == "no_change"


def test_the_four_share_one_parent_and_did_not_spread_to_its_unmeasured_siblings():
    """The routed four stay independent of their siblings' later measurements.

    Every LLDP sibling is now measured, including both vPC parents. Exact
    membership closes the old anti-leak guard in both directions: an undeclared
    sibling cannot acquire a reset, and a measured one cannot lose its own.
    """
    for _k, nvpair, _r, _t, _f in FOUR:
        b = resolve_by_nvpair(ROUTED, nvpair)
        assert b["parent_template"] == ROUTED

    lldp_parents = {
        "int_access_host", "int_trunk_host", "int_routed_host",
        "int_port_channel_access_host", "int_port_channel_trunk_host",
        "int_port_channel_dot1q_tunnel_host", "int_vpc_access_host",
        "int_vpc_trunk_host",
    }
    expected = {(p, key): "false" for p in lldp_parents
                for key in ("disable_lldp_receive", "disable_lldp_transmit")}
    expected.update({(p, "ospf_network_type"): "noChange" for p in
                     ("int_loopback", "int_routed_host", "int_subif", "int_vlan")})
    expected.update({(p, "ospf_passive_mode"): "noChange" for p in
                     ("int_routed_host", "int_vlan")})
    actual = {(r["parent_template"], r["profile_key"]): r["reset_wire"]
              for r in _rows()
              if r["profile_key"] in ("disable_lldp_receive", "disable_lldp_transmit",
                                      "ospf_network_type", "ospf_passive_mode")
              and "reset_wire" in r}
    assert actual == expected, (
        "measured sibling membership or values drifted: missing=%s unexpected=%s"
        % (sorted(set(expected) - set(actual)), sorted(set(actual) - set(expected))))
