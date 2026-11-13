"""Several reset families and deliveries in one loaded table and one real request."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import BINDING_TABLE
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_by_nvpair

from .helpers.binding_harness import IF_A
from .helpers.binding_harness import MACSEC_FB_CTX
from .helpers.binding_harness import OSPF_CTX
from .helpers.binding_harness import ROUTED as FAMILY_ROUTED
from .helpers.binding_harness import base_for
from .helpers.binding_harness import build_have
from .helpers.binding_harness import cfg
from .helpers.binding_harness import diff_nvpairs
from .helpers.binding_harness import request_nvpairs
from .helpers.binding_harness import run
from .helpers.binding_harness import run_configs
from .helpers.binding_harness import split_calls
from .helpers.binding_harness import ROUTED as DAMP_BFD_ROUTED
from .helpers.binding_harness import SVI
from .helpers.binding_harness import VPC_DOT1Q
from .helpers.binding_harness import VPC_PAIR_SERIAL
from .helpers.binding_harness import _collect_policies
from .helpers.binding_harness import cfg_for


# ====================================================================================================
# Formerly test_gie_smu74_union_coexistence.py
# Both newly accepted reset families must be present together in one loaded table.
#
# The routed LLDP booleans and the routed OSPF enums were registered separately, and each
# family's own tests cannot see the other's rows. This file fails when either family is missing
# (4 of 8 cases fail with only one family, 6 on the 70-reset base) and passes only on the union.
#
# Row count, uniqueness, provenance, index freshness, fixture coverage and per-family
# withdrawal are covered by their own files and are not duplicated here.
#
# Offline only: no controller, switch or CI is contacted. The combined set is not live tested.
# ====================================================================================================
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

# Test-only pin of the registered total. The union guarantee above is unchanged.
# Deliberately not `>=`, `skip`, `xfail`, or derived from the table under test.
#
# 174 = 70 + 4 (this union) + 14 (base88) + 30 (OSPF) + 35 (EIGRP) + 4 (MACsec)
#       + 10 (BFD) + 7 (dampening, controller-only).
# Each lot is also named by identity below, with disjointness and closure asserted, so a
# total cannot be reached by registering something else in place of a measured row.
#
# Registration is not acceptance: the 7 dampening rows were observed at the controller only
# and are not validated on NX-OS. This file pins registration only.
# HSRP adds three int_vlan rows (preempt delay, forwarding-threshold pair): 197 + 3 = 200.
# The int_vpc_dot1q_tunnel rows, measured on both vPC peers: 200 + 6 = 206.
# int_vlan::privateVlanMapping: 206 + 1 = 207.
# Eleven PVLAN companion rows (PVLANC1_ADDITIONS), resets inferred, not measured: 207 + 11 = 218.
# int_vpc_pvlan_host::qosStatsSuppressed (IQ1_ADDITIONS), reset inferred: 218 + 1 = 219.
# SMU 017 first increment (BATCH017_ADDITIONS), resets read from the 017 bodies, not measured: 219 + 5 = 224.
# SMU 017 loopback EIGRP (LOEIGRP017_ADDITIONS, slice 0b_38): 224 + 5 = 229; SMU 017 routed port-channel PIM BFD
# (L3PO017_ADDITIONS, slice 0b_39): 229 + 1 = 230. Resets read from the 017 bodies, not measured. The routed
# port-channel OSPF family (L3PO_OSPF_ADDITIONS, slice 0b_40), 16 resets copied from the routed rows on identical 017
# declarations: 230 + 16 = 246. Trunk port-channel reset-skip default (RS1_ADDITIONS), reset read from
# the 017 body: 246 + 1 = 247. Peer-link STP and QoS-statistics rows (PL1_ADDITIONS), resets read from the 017 body:
# 247 + 2 = 249. ToR-uplink parent rows (UL1_ADDITIONS), resets read from the template bodies: 249 + 12 = 261.
# Routed port-channel PIM sparse mode and DR priority (L3PO_PIM_ADDITIONS, slice 0b_41), the routed resets on
# identical declarations, not measured on this parent: 261 + 2 = 263.
CANDIDATE_RESET_TOTAL = 263

# The additions this candidate is allowed to carry, and nothing else: four
# `int_routed_host` and four `int_subif` rows, plus two `int_loopback` and four
# `int_vlan` rows. Fourteen, over four parents.
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
    # Routed rows
    ("int_routed_host", "ospfMtuIgnore", "ospf_mtu_ignore", "false"),
    ("int_routed_host", "ospfShutdown", "ospf_shutdown", "false"),
    ("int_routed_host", "ipv6NdSuppressRa", "ipv6_nd_suppress_ra", "false"),
    ("int_routed_host", "ipv6LinkLocal", "ipv6_link_local", ""),
    # Subinterface rows
    ("int_subif", "ospfMtuIgnore", "ospf_mtu_ignore", "false"),
    ("int_subif", "ospfShutdown", "ospf_shutdown", "false"),
    ("int_subif", "ipv6NdSuppressRa", "ipv6_nd_suppress_ra", "false"),
    ("int_subif", "ipv6LinkLocal", "ipv6_link_local", ""),
    # Loopback and SVI rows
    ("int_loopback", "ospfMtuIgnore", "ospf_mtu_ignore", "false"),
    ("int_loopback", "ospfShutdown", "ospf_shutdown", "false"),
    ("int_vlan", "ospfMtuIgnore", "ospf_mtu_ignore", "false"),
    ("int_vlan", "ospfShutdown", "ospf_shutdown", "false"),
    ("int_vlan", "ipv6NdSuppressRa", "ipv6_nd_suppress_ra", "false"),
    ("int_vlan", "ipv6LinkLocal", "ipv6_link_local", ""),
    # The OSPF options profile, measured on a subinterface, a loopback and an SVI.
    # `int_routed_host` contributes no row here: those two fields
    # were already registered on it and served as RETENTION CONTROLS -- the clear body excluded it.
    #
    # `ospf_network_type` appears THREE times because these are THREE distinct bindings, one per
    # parent, not an inference from the routed row. And the passive pair is TWO fields: int_subif
    # declared the BOOLEAN `ospfPassiveInterface` (reset 'false') on the earlier SMU, while int_vlan declares the ENUM
    # `ospfPassiveMode` (reset 'noChange'). Both emit the SAME CLI line, so reading the CLI does
    # not tell them apart: each needs its own row and its own reset.
    ("int_subif", "ospfNetworkType", "ospf_network_type", "noChange"),
    ("int_subif", "ospfPassiveMode", "ospf_passive_mode", "noChange"),   # SMU 017 row; not measured live
    ("int_loopback", "ospfNetworkType", "ospf_network_type", "noChange"),
    ("int_loopback", "ospfAdvertiseSubnet", "ospf_advertise_subnet", "false"),
    ("int_vlan", "ospfNetworkType", "ospf_network_type", "noChange"),
    ("int_vlan", "ospfPassiveMode", "ospf_passive_mode", "noChange"),
    # OSPF BFD and area, measured.
    # BFD: ospfBfdMode on all four parents since SMU 017 (subif/loopback carried the boolean ospfBfd
    # on the earlier SMU, where the reset was measured; the 017 rows replace it unmeasured).
    # The area is a reset that does NOT delete its line: it returns it to the
    # declared default 0.0.0.0. Demanding that every reset delete a line would have rejected
    # these four.
    ("int_routed_host", "ospfBfdMode", "ospf_bfd_mode", "noChange"),
    ("int_subif", "ospfBfdMode", "ospf_bfd_mode", "noChange"),   # SMU 017 row; not measured live
    ("int_loopback", "ospfBfdMode", "ospf_bfd_mode", "noChange"),   # SMU 017 row; not measured live
    ("int_vlan", "ospfBfdMode", "ospf_bfd_mode", "noChange"),
    # routed::OSPF_AREA_ID is back: with the key GENUINELY ABSENT, the table without the metadata
    # REFUSES the `replaced` while the table with it withdraws the field. The control that had
    # removed this row was not omitting the field at all (BASE_ROUTED already carries it). See the
    # harness.
    ("int_routed_host", "OSPF_AREA_ID", "ospf_area_id", "0.0.0.0"),
    ("int_subif", "OSPF_AREA_ID", "ospf_area_id", "0.0.0.0"),
    ("int_loopback", "OSPF_AREA_ID", "ospf_area_id", "0.0.0.0"),
    ("int_vlan", "OSPF_AREA_ID", "ospf_area_id", "0.0.0.0"),
    # OSPF message-digest: the gate (4) and the key-ID (4), measured.
    # The gate was measured WITH the key and ID retained; the ID was measured with
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
    # OSPF SIMPLE authentication: the key, measured.
    # A mechanism independent of message-digest; its type stayed at the declared default 3.
    ("int_routed_host", "ospfAuthenticationKey", "ospf_authentication_key", ""),
    ("int_subif", "ospfAuthenticationKey", "ospf_authentication_key", ""),
    ("int_loopback", "ospfAuthenticationKey", "ospf_authentication_key", ""),
    ("int_vlan", "ospfAuthenticationKey", "ospf_authentication_key", ""),
    # The OSPF gate, on ALL FOUR parents.
    #
    # int_loopback was first measured with `int_vrf: default`, and the device KEPT the
    # line. The installed body of that parent, line 648, emits the association by DISJUNCTION:
    #   configureOspf = (enableOspf == "true" or
    #                    (intfVrf == "default" and linkStateRouting == "ospf"))
    # The second branch does not look at the gate, so in the `default` VRF of a fabric that routes
    # with OSPF the withdrawal is UNOBSERVABLE. Measured with a non-default `int_vrf`: the
    # `ip router ospf <tag> area <x>` line disappeared while interface, VRF and IP survived.
    ("int_routed_host", "ospf", "enable_ospf", "false"),
    ("int_subif", "ospf", "enable_ospf", "false"),
    ("int_vlan", "ospf", "enable_ospf", "false"),
    ("int_loopback", "ospf", "enable_ospf", "false"),
    # `bfdEcho` travelled through the PUBLIC module path
    # (with the interval gate ENABLED, which is what isolates its effect).
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

# ===================================================== EIGRP and MACsec, kept apart
# Each lot keeps its own group: folding it into a bigger tuple would dissolve the check
# that it contributes exactly what was measured. The groups are listed by IDENTITY, never
# derived from the parent template, because lots share parents.
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
#      not controller-refused.
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
# EXPERIMENTAL registration so that the omission path can be executed and observed at the
# controller. They are NOT accepted device resets, they are NOT part of the 157 integration,
# and 134 is NOT a portfolio figure. Nothing was deployed when they were observed,
# so no device acceptance exists for any of the seven.
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

# Two reviewed lots added in this integration. The explicit tuples
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

# HSRP, IPv4 scope. The two IPv6 rows (HSRP_VIPv6, HSRP_GROUPv6) are NOT
# here: the installed int_vlan body emitted no IPv6 line on the measured controller, so neither
# has an observable positive. The two thresholds are one coordinated group, not two removals.
HSRP3_ADDITIONS = (
    ("int_vlan", "hsrpPreemptDelayMinimum", "hsrp_preempt_delay_minimum", ""),
    ("int_vlan", "hsrpPriorityForwardingThresholdLower", "hsrp_priority_forwarding_threshold_lower", ""),
    ("int_vlan", "hsrpPriorityForwardingThresholdUpper", "hsrp_priority_forwarding_threshold_upper", ""),
)
HSRP3_IDENTITIES = frozenset((p, nv) for p, nv, _k, _r in HSRP3_ADDITIONS)

# The vPC dot1q-tunnel parent's own six. Same public keys and reset forms
# as the VPC13 lot, but separate identities measured on their own parent -- not transferred.
VPC_DOT1Q6_ADDITIONS = tuple(
    ("int_vpc_dot1q_tunnel", nv, key, reset)
    for nv, key, reset in (
        ("aclFilter", "acl_filter", ""),
        ("lldpReceive", "disable_lldp_receive", "false"),
        ("lldpTransmit", "disable_lldp_transmit", "false"),
        ("qosStatsSuppressed", "disable_qos_stats", "false"),
        ("queuingStats", "disable_queuing_stats", "false"),
        ("spanningTreePortType", "spanning_tree_port_type", "no"),
    )
)
VPC_DOT1Q6_IDENTITIES = frozenset((p, nv) for p, nv, _k, _r in VPC_DOT1Q6_ADDITIONS)

# Adds ONE int_vlan row. The explicit empty string clears
# `private-vlan mapping 3214,3216` while protected SVI state remains present.
PVLAN1_ADDITIONS = (
    ("int_vlan", "privateVlanMapping", "private_vlan_mapping", ""),
)
PVLAN1_IDENTITIES = frozenset((p, nv) for p, nv, _k, _r in PVLAN1_ADDITIONS)

# The REGISTRY_BINDING rows of the three PVLAN parents. Same public keys and
# reset forms as the sibling host parents; on these parents the resets are INFERRED (not measured).
PVLANC1_ADDITIONS = tuple(
    (parent, nv, key, reset)
    for parent, rows in (
        ("int_pvlan_host", (("lldpReceive", "disable_lldp_receive", "false"), ("lldpTransmit", "disable_lldp_transmit", "false"))),
        ("int_port_channel_pvlan_host", (("lldpReceive", "disable_lldp_receive", "false"),
                                         ("lldpTransmit", "disable_lldp_transmit", "false"),
                                         ("queuingStats", "disable_queuing_stats", "false"),
                                         ("spanningTreePortType", "spanning_tree_port_type", "no"))),
        ("int_vpc_pvlan_host", (("aclFilter", "acl_filter", ""), ("lldpReceive", "disable_lldp_receive", "false"),
                                ("lldpTransmit", "disable_lldp_transmit", "false"),
                                ("queuingStats", "disable_queuing_stats", "false"),
                                ("spanningTreePortType", "spanning_tree_port_type", "no"))),
    )
    for nv, key, reset in rows
)
PVLANC1_IDENTITIES = frozenset((p, nv) for p, nv, _k, _r in PVLANC1_ADDITIONS)

# The vPC PVLAN qosStatsSuppressed row, the sibling vPC parents' key and reset form (INFERRED on the PVLAN parent).
IQ1_ADDITIONS = (("int_vpc_pvlan_host", "qosStatsSuppressed", "disable_qos_stats", "false"),)
IQ1_IDENTITIES = frozenset((p, nv) for p, nv, _k, _r in IQ1_ADDITIONS)

# SMU 017 first increment, slice 0b_37. Resets read from the 017 bodies, NOT measured live.
BATCH017_ADDITIONS = (
    ("int_routed_host", "CDP_ENABLE", "enable_cdp", "true"),
    ("int_routed_host", "evpnMultisiteDciTracking", "enable_evpn_multisite_dci_tracking", "false"),
    ("int_routed_host", "ospfRetransmitInterval", "ospf_retransmit_interval", ""),
    ("int_access_host", "loggingEventPortLinkStatus", "logging_event_port_link_status", "false"),
    ("int_subif", "pimBfdInstance", "enable_pim_bfd_instance", "false"),
)
BATCH017_IDENTITIES = frozenset((p, nv) for p, nv, _k, _r in BATCH017_ADDITIONS)

# SMU 017 loopback EIGRP, slice 0b_38. Resets read from the 017 int_loopback body, NOT measured live.
LOEIGRP017_ADDITIONS = (
    ("int_loopback", "eigrpIpv6Routing", "enable_eigrp_ipv6_routing", "false"),
    ("int_loopback", "eigrpIpv4DistributeListPrefixList", "eigrp_ipv4_distribute_list_prefix_list", ""),
    ("int_loopback", "eigrpIpv4DistributeListDirection", "eigrp_ipv4_distribute_list_direction", "out"),
    ("int_loopback", "eigrpIpv6DistributeListPrefixList", "eigrp_ipv6_distribute_list_prefix_list", ""),
    ("int_loopback", "eigrpIpv6DistributeListDirection", "eigrp_ipv6_distribute_list_direction", "out"),
)
LOEIGRP017_IDENTITIES = frozenset((p, nv) for p, nv, _k, _r in LOEIGRP017_ADDITIONS)
# SMU 017 routed port-channel PIM BFD, slice 0b_39. Reset read from the 017 int_l3_port_channel body, NOT measured live.
L3PO017_ADDITIONS = (
    ("int_l3_port_channel", "pimBfdInstance", "enable_pim_bfd_instance", "false"),
)
L3PO017_IDENTITIES = frozenset((p, nv) for p, nv, _k, _r in L3PO017_ADDITIONS)

# The routed port-channel OSPF family, slice 0b_40: the 16 rows with a reset (ospfTag, OSPF_AUTH_KEY and
# ospfAuthenticationKeyType have none, as on int_routed_host). NOT measured on this parent.
L3PO_OSPF_ADDITIONS = (
    ("int_l3_port_channel", "ospf", "enable_ospf", "false"),
    ("int_l3_port_channel", "OSPF_AREA_ID", "ospf_area_id", "0.0.0.0"),
    ("int_l3_port_channel", "ospfAuthentication", "enable_ospf_auth", "false"),
    ("int_l3_port_channel", "OSPF_AUTH_KEY_ID", "ospf_auth_key_id", "1"),
    ("int_l3_port_channel", "ospfAuthenticationKey", "ospf_authentication_key", ""),
    ("int_l3_port_channel", "ospfPassiveMode", "ospf_passive_mode", "noChange"),
    ("int_l3_port_channel", "ospfCost", "ospf_cost", ""),
    ("int_l3_port_channel", "ospfMtuIgnore", "ospf_mtu_ignore", "false"),
    ("int_l3_port_channel", "ospfHelloInterval", "ospf_hello_interval", ""),
    ("int_l3_port_channel", "ospfDeadInterval", "ospf_dead_interval", ""),
    ("int_l3_port_channel", "ospfShutdown", "ospf_shutdown", "false"),
    ("int_l3_port_channel", "ospfTransmitDelay", "ospf_transmit_delay", ""),
    ("int_l3_port_channel", "ospfRetransmitInterval", "ospf_retransmit_interval", ""),
    ("int_l3_port_channel", "ospfPriority", "ospf_priority", ""),
    ("int_l3_port_channel", "ospfNetworkType", "ospf_network_type", "noChange"),
    ("int_l3_port_channel", "ospfBfdMode", "ospf_bfd_mode", "noChange"),
)
L3PO_OSPF_IDENTITIES = frozenset((p, nv) for p, nv, _k, _r in L3PO_OSPF_ADDITIONS)

# Trunk port-channel reset-skip default, slice rs1. Reset read from the 017 body (defaultValue=false).
RS1_ADDITIONS = (("int_port_channel_trunk_host", "linkTransmitResetSkip", "link_transmit_reset_skip", "false"),)
RS1_IDENTITIES = frozenset((p, nv) for p, nv, _k, _r in RS1_ADDITIONS)

# Existing vPC peer-link parent, slice pl1: the two rows with a reset (ENABLE_QOS and QOS_POLICY have none, because the
# 017 body keeps the QoS attachment when it is disabled; NOT measured live).
PL1_ADDITIONS = (
    ("int_vpc_peer_link_po", "qosStatsSuppressed", "disable_qos_stats", "false"),
    ("int_vpc_peer_link_po", "spanningTreePortType", "spanning_tree_port_type", "no"),
)
PL1_IDENTITIES = frozenset((p, nv) for p, nv, _k, _r in PL1_ADDITIONS)

# Existing ToR-uplink vPC parent, slice ul1: all twelve rows carry a reset (the child rebuilds its sub-policies from the
# forwarded values). Read from the template bodies, NOT measured live.
UL1_ADDITIONS = tuple(
    ("int_vpc_uplink_access", nv, key, reset) for nv, key, reset in (
        ("ENABLE_QOS", "enable_qos", "false"),
        ("QOS_POLICY", "qos_policy", ""),
        ("qosStatsSuppressed", "disable_qos_stats", "false"),
        ("spanningTreePortType", "spanning_tree_port_type", "no"),
        ("ENABLE_STORM_CONTROL", "enable_storm_control", "false"),
        ("STORM_CONTROL_ACTION", "storm_control_action", "no"),
        ("STORM_CONTROL_BCAST_LEVEL_PERCENT", "storm_control_broadcast_level_percent", ""),
        ("STORM_CONTROL_MCAST_LEVEL_PERCENT", "storm_control_multicast_level_percent", ""),
        ("STORM_CONTROL_UCAST_LEVEL_PERCENT", "storm_control_unicast_level_percent", ""),
        ("STORM_CONTROL_BCAST_LEVEL_PPS", "storm_control_broadcast_level_pps", ""),
        ("STORM_CONTROL_MCAST_LEVEL_PPS", "storm_control_multicast_level_pps", ""),
        ("STORM_CONTROL_UCAST_LEVEL_PPS", "storm_control_unicast_level_pps", ""),
    )
)
UL1_IDENTITIES = frozenset((p, nv) for p, nv, _k, _r in UL1_ADDITIONS)

# PIM sparse mode and DR priority on the routed port-channel, slice 0b_41: the routed resets on identical declarations.
# Read from the template body, NOT measured live.
L3PO_PIM_ADDITIONS = (
    ("int_l3_port_channel", "ENABLE_PIM_SPARSE", "enable_pim_sparse", "false"),
    ("int_l3_port_channel", "PIM_DR_PRIORITY", "pim_dr_priority", "1"),
)
L3PO_PIM_IDENTITIES = frozenset((p, nv) for p, nv, _k, _r in L3PO_PIM_ADDITIONS)

# Every addition this checkout carries over the published 74, by lot. The dampening lot is
# included in the SET arithmetic -- it is registered, so it must be accounted for -- while its
# controller-only evidence status is recorded above and asserted in its own grouped test.
ALL_ADDITIONS = (CANDIDATE_ADDITIONS + EIGRP_ADDITIONS + MACSEC_ADDITIONS
                 + DAMPENING_EXPERIMENTAL_ADDITIONS + PIMACL_ADDITIONS
                 + VPC13_ADDITIONS + HSRP3_ADDITIONS + VPC_DOT1Q6_ADDITIONS
                 + PVLAN1_ADDITIONS + PVLANC1_ADDITIONS + IQ1_ADDITIONS + BATCH017_ADDITIONS
                 + LOEIGRP017_ADDITIONS + L3PO017_ADDITIONS + L3PO_OSPF_ADDITIONS + RS1_ADDITIONS + PL1_ADDITIONS
                 + UL1_ADDITIONS + L3PO_PIM_ADDITIONS)
ALL_ADDED_IDENTITIES = (CANDIDATE_IDENTITIES | EIGRP_IDENTITIES | MACSEC_IDENTITIES
                        | DAMPENING_EXPERIMENTAL_IDENTITIES | PIMACL_IDENTITIES
                        | VPC13_IDENTITIES | HSRP3_IDENTITIES | VPC_DOT1Q6_IDENTITIES
                        | PVLAN1_IDENTITIES | PVLANC1_IDENTITIES | IQ1_IDENTITIES | BATCH017_IDENTITIES
                        | LOEIGRP017_IDENTITIES | L3PO017_IDENTITIES | L3PO_OSPF_IDENTITIES | RS1_IDENTITIES
                        | PL1_IDENTITIES | UL1_IDENTITIES | L3PO_PIM_IDENTITIES)


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
    assert len(HSRP3_IDENTITIES) == len(HSRP3_ADDITIONS) == 3
    assert HSRP3_IDENTITIES <= registered
    assert len(VPC_DOT1Q6_IDENTITIES) == len(VPC_DOT1Q6_ADDITIONS) == 6
    assert VPC_DOT1Q6_IDENTITIES <= registered
    assert len(PVLAN1_IDENTITIES) == len(PVLAN1_ADDITIONS) == 1
    assert PVLAN1_IDENTITIES <= registered
    assert len(PVLANC1_IDENTITIES) == len(PVLANC1_ADDITIONS) == 11
    assert PVLANC1_IDENTITIES <= registered
    assert len(IQ1_IDENTITIES) == len(IQ1_ADDITIONS) == 1
    assert IQ1_IDENTITIES <= registered
    groups = (CANDIDATE_IDENTITIES, EIGRP_IDENTITIES, MACSEC_IDENTITIES,
              DAMPENING_EXPERIMENTAL_IDENTITIES, PIMACL_IDENTITIES, VPC13_IDENTITIES,
              HSRP3_IDENTITIES, VPC_DOT1Q6_IDENTITIES, PVLAN1_IDENTITIES, PVLANC1_IDENTITIES, IQ1_IDENTITIES)
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
    # 54 = base88's 14 + OSPF's 30 + BFD's 10, carried inside
    # CANDIDATE_ADDITIONS; the other three lots keep their own tuples. 54 + 35 + 4 + 7 = 100,
    # and 74 + 100 = 174. Written as the sum so the arithmetic is visible rather than a bare
    # total somebody has to take on trust.
    # + 3 int_vlan rows (HSRP3_ADDITIONS) = 126, and 74 + 126 = 200.
    # + 6 int_vpc_dot1q_tunnel rows (VPC_DOT1Q6_ADDITIONS) = 132, 74 + 132 = 206.
    # + 1 int_vlan row (PVLAN1_ADDITIONS) = 133, and 74 + 133 = 207.
    # + 11 PVLAN companion rows (PVLANC1_ADDITIONS, inferred resets) = 144, and 74 + 144 = 218.
    # + 1 vPC PVLAN qosStatsSuppressed row (IQ1_ADDITIONS, inferred reset) = 145, and 74 + 145 = 219.
    # + 5 SMU 017 rows (BATCH017_ADDITIONS, resets read from the bodies) = 150, and 74 + 150 = 224.
    # + 5 SMU 017 loopback EIGRP rows (LOEIGRP017_ADDITIONS, slice 0b_38) = 155, + 1 routed port-channel PIM BFD row
    # (L3PO017_ADDITIONS, slice 0b_39) = 156, + 16 routed port-channel OSPF rows (L3PO_OSPF_ADDITIONS, slice 0b_40) = 172,
    # + 1 trunk port-channel reset-skip row (RS1_ADDITIONS, reset read from the body) = 173, and 74 + 173 = 247.
    # + 2 peer-link rows (PL1_ADDITIONS, resets read from the body) = 175, + 12 uplink rows (UL1_ADDITIONS, resets read
    # from the bodies) = 187, and 74 + 187 = 261. + 2 routed port-channel PIM rows (L3PO_PIM_ADDITIONS, slice 0b_41)
    # = 189, and 74 + 189 = 263.
    assert len(ALL_ADDED_IDENTITIES) == 54 + 35 + 4 + 7 + 10 + 13 + 3 + 6 + 1 + 11 + 1 + 5 + 5 + 1 + 16 + 1 + 2 + 12 + 2 == len(ALL_ADDITIONS), (
        "the lots together declare %d additions over %d distinct identities; expected 189"
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
    # THE GROUPS ARE NAMED BY LOT, NOT DERIVED FROM THE PARENT.
    #
    # Lots share parents (the options profile registers rows on int_subif, int_loopback AND
    # int_vlan), so a parent-based split would file rows under the wrong lot while the
    # counts still added up.
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
        ("int_subif", "ospfNetworkType"), ("int_subif", "ospfPassiveMode"),
        ("int_loopback", "ospfNetworkType"), ("int_loopback", "ospfAdvertiseSubnet"),
        ("int_vlan", "ospfNetworkType"), ("int_vlan", "ospfPassiveMode"),
    }
    # BFD and area are a group NAMED apart from the options: they share parents, so a
    # parent-based partition would again file them under the wrong lot.
    OSPF_ALL_P2_P4 = {
        ("int_routed_host", "ospfBfdMode"), ("int_subif", "ospfBfdMode"),
        ("int_loopback", "ospfBfdMode"), ("int_vlan", "ospfBfdMode"),
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
    # The EIGRP and MACsec lots join the SAME named-group discipline, so the
    # closure assertion below covers all 83 additions rather than only the 44.
    groups = (("B01/ALPHA", B01_ALPHA, 8), ("B01/BETA", B01_BETA, 6),
              ("OSPF-ALL/P1", OSPF_ALL_P1, 6), ("OSPF-ALL/P2+P4", OSPF_ALL_P2_P4, 8),
              ("OSPF-ALL/P3a", OSPF_ALL_P3A, 8),
              ("OSPF-ALL/P3b", OSPF_ALL_P3B, 4),
              ("OSPF-ALL/P5", OSPF_ALL_P5, 4),
              # BFD joins the same named-group discipline, split the way it was
              # measured: `bfdEcho` through the public module path on two parents, and the
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
              ("vPC", set(VPC13_IDENTITIES), 13),
              ("HSRP/IPv4", set(HSRP3_IDENTITIES), 3),
              ("vPC dot1q-tunnel", set(VPC_DOT1Q6_IDENTITIES), 6),
              ("PVLAN mapping", set(PVLAN1_IDENTITIES), 1),
              # registered with INFERRED resets (not measured on a PVLAN parent): named so it is never read as accepted
              ("PVLAN companions C1/inferred", set(PVLANC1_IDENTITIES), 11),
              ("vPC PVLAN ingress QoS IQ1/inferred", set(IQ1_IDENTITIES), 1),
              # SMU 017 first increment: resets read from the 017 bodies, NOT measured live
              ("SMU017 batch 1/from template", set(BATCH017_IDENTITIES), 5),
              # SMU 017 loopback EIGRP, slice 0b_38: resets read from the 017 body, NOT measured live
              ("SMU017 loopback EIGRP/from template", set(LOEIGRP017_IDENTITIES), 5),
              # SMU 017 routed port-channel PIM BFD, slice 0b_39: reset read from the 017 body, NOT measured live
              ("SMU017 routed port-channel PIM BFD/from template", set(L3PO017_IDENTITIES), 1),
              # The routed port-channel OSPF family, slice 0b_40: routed resets on identical 017 declarations, NOT measured
              ("routed port-channel OSPF/from template", set(L3PO_OSPF_IDENTITIES), 16),
              # trunk port-channel reset-skip default: reset read from the 017 body, NOT measured as a withdrawal
              ("Po reset-skip RS1/from template", set(RS1_IDENTITIES), 1),
              # existing peer-link parent: resets read from the 017 body, NOT measured as a withdrawal
              ("peer-link PL1/from template", set(PL1_IDENTITIES), 2),
              # existing ToR-uplink parent: resets read from the template bodies, NOT measured as a withdrawal
              ("uplink UL1/from template", set(UL1_IDENTITIES), 12),
              # routed port-channel PIM, slice 0b_41: routed resets on identical declarations, NOT measured live
              ("routed port-channel PIM/from template", set(L3PO_PIM_IDENTITIES), 2))
    for name, group, expected in groups:
        assert len(group) == expected, (
            "%s declares %d identities, expected %d" % (name, len(group), expected))
    for i, (n1, g1, _e) in enumerate(groups):
        for n2, g2, _e2 in groups[i + 1:]:
            assert not (g1 & g2), "%s and %s overlap on %s" % (n1, n2, sorted(g1 & g2))
    union = (B01_ALPHA | B01_BETA | OSPF_ALL_P1 | OSPF_ALL_P2_P4 | OSPF_ALL_P3A
             | OSPF_ALL_P3B | OSPF_ALL_P5 | BFD_ECHO | BFD_INTERVAL
             | EIGRP_IDENTITIES | MACSEC_IDENTITIES | DAMPENING_EXPERIMENTAL_IDENTITIES
             | PIMACL_IDENTITIES | VPC13_IDENTITIES | HSRP3_IDENTITIES
             | VPC_DOT1Q6_IDENTITIES | PVLAN1_IDENTITIES | PVLANC1_IDENTITIES | IQ1_IDENTITIES
             | BATCH017_IDENTITIES | LOEIGRP017_IDENTITIES | L3PO017_IDENTITIES | L3PO_OSPF_IDENTITIES | RS1_IDENTITIES
             | PL1_IDENTITIES | UL1_IDENTITIES | L3PO_PIM_IDENTITIES)
    assert union == set(ALL_ADDED_IDENTITIES), (
        "the named campaign groups are not exactly the declared additions.\n"
        "  in a group but not declared: %s\n  declared but in no group: %s"
        % (sorted(union - set(ALL_ADDED_IDENTITIES)),
           sorted(set(ALL_ADDED_IDENTITIES) - union)))
    assert len(union) == 189, (
        "the named groups cover %d identities; the delta over the published 74 is "
        "14 base88 + 30 OSPF-ALL + 10 BFD-ALL + 35 EIGRP + 4 MACsec + 7 dampening "
        "+ 10 PIM/ACL + 13 vPC + 3 HSRP/IPv4 + 6 vPC dot1q-tunnel + 1 PVLAN + 11 PVLAN companions + 1 IQ1 "
        "+ 5 SMU017 batch 1 + 5 SMU017 loopback EIGRP + 1 SMU017 routed port-channel PIM BFD "
        "+ 16 routed port-channel OSPF + 1 trunk port-channel reset-skip + 2 peer-link + 12 uplink "
        "+ 2 routed port-channel PIM = 189, and 74 + 189 = 263"
        % len(union))


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
        # addition was a boolean or a string. The OSPF options add ENUM rows whose measured reset is
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
        # these rows depend on -- and an earlier version of this guard conflated them inside
        # itself. For an enum the default is TRANSLATED through the row's `wire_values` before the
        # comparison.
        declared = row.get("default_template")
        vocab = row.get("wire_values") or {}
        if parent in ("int_vpc_access_host", "int_vpc_trunk_host") and row["type"] == "enum":
            # These vPC templates declare the neutral "no" in validValues but
            # the generated row has no default_template. "no" was measured
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
        elif declared is True:
            # int_routed_host CDP_ENABLE (slice 0b_37): defaultValue=true, and true deletes the `no cdp enable` child.
            expected, source_of_expectation = "true", "the declared boolean default"
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
        # The OSPF version asserted, for EVERY enum, that `wire_values["no_change"]`
        # equals the reset and that the reset is NOT among the public `valid_values`. That
        # holds for the OSPF enums, whose public neutral `no_change` maps to the wire-only
        # spelling `noChange`. It is FALSE for the EIGRP enums:
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
        # Both guarantees are kept, each applied to the family it governs. Neither
        # is loosened: the branch below asserts something in BOTH cases.
        if row["type"] == "enum":
            vocab = row.get("wire_values") or {}
            choices = row.get("valid_values") or ()
            if vocab:
                # The public neutral is the declared default: `no_change` for the OSPF enums, `default` for the uplink
                # storm-control action (slice ul1), which keeps the spelling of the native storm-control key.
                neutral = row.get("default_template")
                assert vocab.get(neutral) == row["reset_wire"], (
                    "%s::%s declares a wire vocabulary, so its reset must be the wire form of "
                    "the public neutral; %r maps to %r, not to %r"
                    % (parent, nvpair, neutral, vocab.get(neutral), row["reset_wire"]))
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
        "int_vpc_trunk_host", "int_vpc_dot1q_tunnel",
    }
    expected = {(p, key): "false" for p in lldp_parents
                for key in ("disable_lldp_receive", "disable_lldp_transmit")}
    # The three PVLAN parents carry the same LLDP reset, INFERRED from the measured siblings above and NOT measured
    # on a PVLAN parent. Declared separately so the measured set above keeps its meaning and the closure still holds.
    expected.update({(p, key): "false" for p in ("int_pvlan_host", "int_port_channel_pvlan_host", "int_vpc_pvlan_host")
                     for key in ("disable_lldp_receive", "disable_lldp_transmit")})
    expected.update({(p, "ospf_network_type"): "noChange" for p in
                     ("int_loopback", "int_routed_host", "int_subif", "int_vlan", "int_l3_port_channel")})
    # int_subif joined with SMU 017 (it declared the boolean ospfPassiveInterface before); that row is not measured live.
    # int_l3_port_channel joined with slice 0b_40 (routed contract on an identical 017 declaration); not measured live.
    expected.update({(p, "ospf_passive_mode"): "noChange" for p in
                     ("int_routed_host", "int_subif", "int_vlan", "int_l3_port_channel")})
    actual = {(r["parent_template"], r["profile_key"]): r["reset_wire"]
              for r in _rows()
              if r["profile_key"] in ("disable_lldp_receive", "disable_lldp_transmit",
                                      "ospf_network_type", "ospf_passive_mode")
              and "reset_wire" in r}
    assert actual == expected, (
        "measured sibling membership or values drifted: missing=%s unexpected=%s"
        % (sorted(set(expected) - set(actual)), sorted(set(actual) - set(expected))))


# ====================================================================================================
# Formerly test_gie_smu157_family_coexistence.py
# Do the OSPF and the EIGRP/MACsec families coexist in ONE real withdrawal request?
#
# WHY THIS FILE EXISTS
#
# `test_binding_coexistence.py` establishes the union at the TABLE level: all 83
# additions pinned by lot, by identity, by value and by type, with the lots disjoint and their
# closure asserted. That is necessary and it is not the same question as this one.
#
# Every pilot fixture in `helpers/binding_harness.py` carries only its OWN family's prerequisite
# context -- `OSPF_CTX` for the OSPF rows, `EIGRP_CTX`/`EIGRP_DL4` for the EIGRP rows,
# `MACSEC_FB_CTX` and friends for MACsec -- so each row is exercised through the real `main()`
# alone, never beside a row from another family. No fixture in the harness mixes families,
# and no other test drives two families through one module invocation. So nothing else
# establishes that a single `replaced` request can carry a withdrawal from each family at the
# same time while the other family's prerequisites survive.
#
# WHAT IS AND IS NOT COMBINED, DELIBERATELY
#
# Each case pairs MACsec with exactly ONE routing family. MACsec is a link-layer feature and is
# orthogonal to the routing protocol, so "OSPF plus MACsec" and "EIGRP plus MACsec" are
# configurations that stand on their own. This file does NOT put OSPF and EIGRP on the same
# interface, and does not gather every registered field into one payload to maximise a count:
# an invalid combined routing/auth configuration would prove nothing about coexistence and
# would be green in a mock while impossible on a controller.
#
# The MACsec target is always the FALLBACK name, because that is the only one of the four whose
# EXPLICIT clear was measured ON ITS OWN, with the gate enabled and keychain and policy intact.
# What was measured about the other three, stated exactly:
#
#   * `macsecKeyChainName` and `macsecPolicyName` -- the two primary names -- were REFUSED by
#     the controller, by field name, while the gate was enabled. A fixture that omitted either
#     here would encode a request that never lands.
#   * `macsecInterfacePolicy` -- the gate -- was NOT RUN on its own. Its withdrawal was only
#     ever measured inside the coordinated clear. The template rule permits gate-alone (that
#     rule fires only while the gate is enabled), so it must not be called impossible or
#     refused; it is simply untested.
#
# So "the fallback is the only independently measured explicit clear" is the claim, NOT "the
# only independent clear that is possible". And the fallback's ACCEPTANCE UNDER OMISSION was
# grouped: `replaced` omitted all four at once and the engine emitted four resets in one
# request, so no independent omission was demonstrated live for any of the four, the fallback
# included.
#
# Offline. Real `main()`, real argument spec, real validation, real serialisation; mocks only at
# inventory/transport. Assertions are made against the CAPTURED REQUEST and the PUBLIC DIFF,
# never against `changed`.
#
# NOT LIVE TESTED as an integrated tuple. Each reset carries its own live acceptance, with its
# coordinated and platform limits; the three grouped `enable_ospf` omissions (int_routed_host,
# int_subif, int_vlan) were accepted as grouped results.
# ====================================================================================================
# The MACsec target: the only one of the four whose independent EXPLICIT clear was MEASURED.
# Not "the only one that could possibly be withdrawn alone" -- the gate was never tried alone
# (NOT RUN), and only the two primary names were actually refused. See the module docstring.
MACSEC_TARGET = ("macsec_fallback_key_chain_name", "macsecFallbackKeyChainName", "PILOT-FBKC")

# One routing target per family, each with the prerequisite context its own parent demands.
#   OSPF   -- `ospf_network_type` is an ENUM whose reset is the wire spelling `noChange`,
#             so a copy-paste of the MACsec `""` onto it would be caught.
#   EIGRP  -- `enable_eigrp_shutdown` is a BOOLEAN whose reset is the string `"false"`; the
#             EIGRP process tag is mandatory for ANY EIGRP option, so it travels explicitly
#             and doubles as the non-target field that must survive.
CASES = [
    pytest.param(
        "ospf_network_type", "ospfNetworkType", "point_to_point", "noChange",
        dict(OSPF_CTX),
        {"ospfTag": OSPF_CTX["ospf_tag"], "OSPF_AREA_ID": OSPF_CTX["ospf_area_id"],
         "ospf": "true"},
        id="ospf+macsec",
    ),
    pytest.param(
        "enable_eigrp_shutdown", "eigrpShutdown", True, "false",
        {"eigrp_process_tag": "PILOT-EIGRP"},
        {"eigrpProcessTag": "PILOT-EIGRP"},
        id="eigrp+macsec",
    ),
]


# The EXACT wire value `merged` must leave in place, per routing target.
#
# Written by hand and kept INDEPENDENT of the reset literals above: asserting only
# "it differs from the reset" would pass on any wrong-but-different value, which is
# precisely how a mistranslated enum survives a suite. Measured on this candidate.
MERGED_RETAINS = {
    "ospfNetworkType": "pointToPoint",   # public `point_to_point` -> SMU wire spelling
    "eigrpShutdown": "true",             # public True -> the controller's string
}


def _model(route_ctx, **extra):
    """A routed profile carrying one routing family's context plus the MACsec context."""
    d = dict(route_ctx)
    d.update(MACSEC_FB_CTX)
    d.update(extra)
    return d


# ============================================================ the registration, guarded
def test_both_families_are_registered_before_anything_below_is_meaningful():
    """Guard the guard. If either side's row lost its reset, every case here would pass for
    the wrong reason -- the module would refuse, and a refusal is not a withdrawal."""
    for parent, key, expected in (
        (FAMILY_ROUTED, "ospf_network_type", "noChange"),
        (FAMILY_ROUTED, "enable_eigrp_shutdown", "false"),
        (FAMILY_ROUTED, MACSEC_TARGET[0], ""),
    ):
        b = resolve_binding(parent, key)
        assert b is not None, "%s::%s is not in the table at all" % (parent, key)
        assert b.get("reset_wire") == expected, (
            "%s::%s reset is %r, expected %r" % (parent, key, b.get("reset_wire"), expected))
        assert isinstance(b["reset_wire"], str), (
            "%s::%s reset_wire is %s; the controller returns this nvPair as a string"
            % (parent, key, type(b["reset_wire"]).__name__))


# ==================================================== one request, two families' resets
@pytest.mark.parametrize("key,nvpair,applied,reset,route_ctx,retained", CASES)
def test_one_replaced_request_carries_a_withdrawal_from_each_family(
    key, nvpair, applied, reset, route_ctx, retained
):
    """The union property no single-family suite can state: both resets in ONE payload."""
    mac_key, mac_nv, mac_applied = MACSEC_TARGET
    have = build_have(FAMILY_ROUTED, **_model(route_ctx, **{key: applied, mac_key: mac_applied}))
    result, calls = run(base_for(FAMILY_ROUTED, **_model(route_ctx)), "replaced", have)
    nv = request_nvpairs(calls)
    assert nv, ("no request was sent, so neither omission was detected. changed=%s msg=%s"
                % (result.get("changed"), result.get("msg")))
    assert not result.get("failed"), result.get("msg")
    # EXACTLY one update. "Both resets are present somewhere" would also be true of a run
    # that split them across two requests, and the union property this file exists to state
    # is that ONE payload carries both.
    assert len(split_calls(calls)["updates"]) == 1, (
        "expected exactly one configuration request carrying both resets, got %d"
        % len(split_calls(calls)["updates"]))
    assert nv[0].get(nvpair) == reset, (
        "the routing family's reset is missing or wrong: %s is %r, expected %r"
        % (nvpair, nv[0].get(nvpair), reset))
    assert nv[0].get(mac_nv) == "", (
        "the MACsec fallback reset is missing or wrong: %s is %r, expected the empty string"
        % (mac_nv, nv[0].get(mac_nv)))
    # The public diff must own both too, independently of the request body.
    dnv = diff_nvpairs(result)
    assert dnv and dnv[0].get(nvpair) == reset, "the routing reset is absent from the diff"
    assert dnv[0].get(mac_nv) == "", "the MACsec reset is absent from the diff"


@pytest.mark.parametrize("key,nvpair,applied,reset,route_ctx,retained", CASES)
def test_the_untargeted_fields_of_both_families_survive(
    key, nvpair, applied, reset, route_ctx, retained
):
    """A reset that spilled onto a field nobody withdrew would be invisible in a count."""
    mac_key, mac_nv, mac_applied = MACSEC_TARGET
    have = build_have(FAMILY_ROUTED, **_model(route_ctx, **{key: applied, mac_key: mac_applied}))
    _result, calls = run(base_for(FAMILY_ROUTED, **_model(route_ctx)), "replaced", have)
    nv = request_nvpairs(calls)[0]
    # The routing family's own prerequisites.
    for field, value in retained.items():
        assert nv.get(field) == value, (
            "the routing prerequisite %s changed: %r, expected %r"
            % (field, nv.get(field), value))
    # MACsec's gate and the two names it refuses to have emptied while enabled.
    assert nv.get("macsecInterfacePolicy") == "true", (
        "the MACsec gate was withdrawn although nobody omitted it: %r"
        % nv.get("macsecInterfacePolicy"))
    assert nv.get("macsecKeyChainName") == "PILOT-KC", (
        "the MACsec keychain changed: %r" % nv.get("macsecKeyChainName"))
    assert nv.get("macsecPolicyName") == "PILOT-POL", (
        "the MACsec policy changed: %r" % nv.get("macsecPolicyName"))


# =================================================================== negative controls
@pytest.mark.parametrize("key,nvpair,applied,reset,route_ctx,retained", CASES)
def test_merged_sends_no_reset_for_either_family(
    key, nvpair, applied, reset, route_ctx, retained
):
    """CONTROL: the two resets above are attributable to the WITHDRAWAL path, not to the
    shape of the model. Under `merged` the same omission preserves both values."""
    mac_key, mac_nv, mac_applied = MACSEC_TARGET
    have = build_have(FAMILY_ROUTED, **_model(route_ctx, **{key: applied, mac_key: mac_applied}))
    _result, calls = run(
        base_for(FAMILY_ROUTED, description="coexistence-merged", **_model(route_ctx)), "merged", have)
    nv = request_nvpairs(calls)
    assert nv, "the description change produced no request"
    assert len(split_calls(calls)["updates"]) == 1, (
        "expected exactly one configuration request, got %d"
        % len(split_calls(calls)["updates"]))
    assert nv[0].get(mac_nv) == mac_applied, (
        "merged withdrew the MACsec fallback: %r" % nv[0].get(mac_nv))
    # The EXACT retained value, not merely "different from the reset": a wrong-but-different
    # value -- a mistranslated enum, say -- would satisfy an inequality and fail nothing.
    expected_retained = MERGED_RETAINS[nvpair]
    assert nv[0].get(nvpair) == expected_retained, (
        "merged did not preserve the routing value: %s is %r, expected %r"
        % (nvpair, nv[0].get(nvpair), expected_retained))
    # And it is still not the reset -- kept as a separate, explicit statement so the pair of
    # literals cannot silently converge.
    assert expected_retained != reset, (
        "the retained and reset literals for %s are the same value (%r), so this control "
        "can no longer distinguish preservation from withdrawal" % (nvpair, reset))


@pytest.mark.parametrize("key,nvpair,applied,reset,route_ctx,retained", CASES)
def test_check_mode_plans_both_resets_and_transmits_nothing(
    key, nvpair, applied, reset, route_ctx, retained
):
    """CONTROL: a plan is not a write. Both resets appear in the diff and the transport sees
    no configuration and no deploy request. "It did not write" alone would also describe a
    check mode that planned nothing at all."""
    mac_key, mac_nv, mac_applied = MACSEC_TARGET
    have = build_have(FAMILY_ROUTED, **_model(route_ctx, **{key: applied, mac_key: mac_applied}))
    result, calls = run_configs(
        [cfg(IF_A, base_for(FAMILY_ROUTED, **_model(route_ctx)))], "replaced", have, check_mode=True)
    dnv = diff_nvpairs(result)
    assert dnv, "check mode planned nothing at all"
    assert dnv[0].get(nvpair) == reset, "check mode did not plan the routing reset"
    assert dnv[0].get(mac_nv) == "", "check mode did not plan the MACsec reset"
    buckets = split_calls(calls)
    assert buckets["updates"] == [], "check mode sent a configuration request"
    assert buckets["deploys"] == [], "check mode sent a deploy request"


def test_the_two_families_neutrals_are_not_interchangeable():
    """CONTROL: the assertions above have teeth because each family's reset is a DIFFERENT
    literal. A copy-paste of one onto the other is rejected, which is what makes
    "both resets present" a real claim rather than a coincidence of shapes.

    `''`, `'false'` and `'noChange'` are three distinct values, and none is `False`: a native
    bool would never match a controller HAVE, and in a boolean test `'false'` is truthy while
    `False` is falsy.
    """
    ospf = resolve_binding(FAMILY_ROUTED, "ospf_network_type")["reset_wire"]
    eigrp = resolve_binding(FAMILY_ROUTED, "enable_eigrp_shutdown")["reset_wire"]
    macsec = resolve_binding(FAMILY_ROUTED, MACSEC_TARGET[0])["reset_wire"]
    assert ospf == "noChange" and eigrp == "false" and macsec == ""
    assert len({ospf, eigrp, macsec}) == 3, (
        "two of the three families now share a reset literal, so a copy-paste between them "
        "would no longer be detectable here: %r" % ([ospf, eigrp, macsec],))
    for value in (ospf, eigrp, macsec):
        assert value is not False and not isinstance(value, bool), (
            "a reset arrived as a native bool: %r" % (value,))


def test_omitting_an_eigrp_option_and_its_mandatory_tag_withdraws_both_in_one_request():
    """Omitting the whole EIGRP context withdraws the option AND its mandatory tag together,
    in one request, while the other family's retained context is untouched.

    WHY THIS DOCSTRING CHANGED, and the assertion with it. This case used to be written as
    "refused, not invented" and accepted EITHER outcome:

        if result.get("failed"):
            assert split_calls(calls)["updates"] == []
            return

    That made ANY failure a PASS. It never fired -- the run succeeds on this candidate -- so
    the branch bought nothing today and would have swallowed an unrelated regression
    tomorrow: a future defect that made this invocation fail for a completely different
    reason would have satisfied the early return and reported green.

    The observed behaviour is pinned instead, measured on this candidate: the run SUCCEEDS
    with exactly ONE update carrying

        eigrpShutdown='false'   eigrpProcessTag=''   macsecFallbackKeyChainName=''

    which is a COORDINATED clear -- the parent refuses an active option with an empty tag, so
    withdrawing the option obliges withdrawing the tag in the same payload. The test now
    proves that, which is what it actually observes, rather than a refusal it never saw.
    """
    have = build_have(FAMILY_ROUTED, **_model({"eigrp_process_tag": "PILOT-EIGRP"},
                                              enable_eigrp_shutdown=True,
                                              macsec_fallback_key_chain_name="PILOT-FBKC"))
    # The model drops the EIGRP context entirely: no tag, no option.
    result, calls = run(base_for(FAMILY_ROUTED, **MACSEC_FB_CTX), "replaced", have)

    assert not result.get("failed"), (
        "the coordinated clear was refused; this candidate was measured performing it: %s"
        % (result.get("msg"),))
    updates = split_calls(calls)["updates"]
    assert len(updates) == 1, (
        "expected exactly one configuration request, got %d" % len(updates))

    nv = request_nvpairs(calls)
    assert nv, "no request was sent, so the omission was neither withdrawn nor refused"
    assert nv[0].get("eigrpShutdown") == "false", (
        "the EIGRP option was omitted but not withdrawn: %r" % nv[0].get("eigrpShutdown"))
    assert nv[0].get("eigrpProcessTag") == "", (
        "the option was withdrawn while its mandatory tag kept a value: %r"
        % nv[0].get("eigrpProcessTag"))
    assert nv[0].get("macsecFallbackKeyChainName") == "", (
        "the MACsec fallback was omitted but not withdrawn: %r"
        % nv[0].get("macsecFallbackKeyChainName"))
    # The MACsec context nobody omitted must survive the same payload.
    assert nv[0].get("macsecInterfacePolicy") == "true", (
        "the MACsec gate was withdrawn although nobody omitted it: %r"
        % nv[0].get("macsecInterfacePolicy"))
    assert nv[0].get("macsecKeyChainName") == "PILOT-KC", (
        "the MACsec keychain changed: %r" % nv[0].get("macsecKeyChainName"))
    assert nv[0].get("macsecPolicyName") == "PILOT-POL", (
        "the MACsec policy changed: %r" % nv[0].get("macsecPolicyName"))


# ====================================================================================================
# Formerly test_gie_smu174_damp_bfd_coexistence.py
# Do the seven dampening resets and the routed BFD echo reset coexist in ONE real request?
#
# WHY THIS FILE EXISTS
#
# `test_binding_withdrawal.py` drives the seven dampening identities as a group, and the
# pilot matrix in `test_binding_withdrawal.py` drives `int_routed_host::disable_bfd_echo` on its
# own. Neither asks whether a single `replaced` request can carry BOTH withdrawals: the dampening
# suite omits only dampening keys, and the BFD row is exercised with an empty prerequisite context.
# Checked before writing this file -- no fixture in the harness mixes the two families, and no
# existing test drives them through one module invocation.
#
# WHY THIS COMBINATION IS A VALID ONE TO BUILD
#
# Both identities live on `int_routed_host`, and neither gates the other: dampening is an interface
# dampening feature with its own gate and numeric group, while `bfdEcho` is a BFD interface option.
# The dampening group is supplied in full -- gate, half-life, reuse, suppress, max-suppress and
# restart -- because the parent refuses a partial group, and `disable_bfd_echo` needs no
# prerequisite of its own. So this is a configuration that stands on its own rather than a pile of
# fields assembled to inflate a payload.
#
# Deploy travels FALSE, as in every live dampening step. The harness default is `deploy=True`;
# leaving it would assert against a model that was never sent.
#
# EVIDENCE STATUS, KEPT APART DELIBERATELY
#
# The BFD reset retains its live acceptance. The seven dampening resets are
# CONTROLLER_OMISSION_VERIFIED / DEVICE_NOT_VALIDATED: their omission was observed at the
# controller with deploy false, NX-OS withdrawal was never validated, and the lab platform does not
# support that CLI. Putting them in one offline request proves they coexist in the module's
# withdrawal path. It does not upgrade the dampening evidence, and nothing here should be read as
# device validation of anything.
#
# Offline. Real `main()`, real argument spec, real validation, real serialisation; mocks only at
# inventory/transport. Assertions are against the CAPTURED REQUEST and the PUBLIC DIFF, never
# against `changed`. NOT LIVE TESTED.
# ====================================================================================================
# The full dampening group the parent requires, plus the BFD echo option. Written by hand: an
# expectation read back from the subject under test cannot fail.
POSITIVE = {
    "enable_dampening": True,
    "dampening_half_life": 5,
    "dampening_reuse": 750,
    "dampening_suppress": 2000,
    "dampening_max_suppress": 60,
    "dampening_restart": True,
    "dampening_restart_penalty": 1000,
    "disable_bfd_echo": True,
}

# nvPair spelling -> the reset each identity is entitled to. Eight rows: seven dampening and
# the BFD echo. Two of the dampening rows and the BFD row reset with the wire STRING 'false';
# the five dampening numbers reset with the EMPTY STRING. Those are different values and the
# distinction is the point -- a copy-paste of one onto the other must fail here.
EXPECTED_RESET = {
    "dampening": "false",
    "dampeningRestart": "false",
    "dampeningHalfLife": "",
    "dampeningReuse": "",
    "dampeningSuppress": "",
    "dampeningMaxSuppress": "",
    "dampeningRestartPenalty": "",
    "bfdEcho": "false",
}
DAMP_NVPAIRS = [nv for nv in EXPECTED_RESET if nv != "bfdEcho"]

# What the controller holds once the positive is applied.
EXPECTED_APPLIED = {
    "dampening": "true",
    "dampeningRestart": "true",
    "dampeningHalfLife": "5",
    "dampeningReuse": "750",
    "dampeningSuppress": "2000",
    "dampeningMaxSuppress": "60",
    "dampeningRestartPenalty": "1000",
    "bfdEcho": "true",
}


def _have():
    return build_have(DAMP_BFD_ROUTED, **POSITIVE)


def _run(profile, state, **kw):
    return run_configs([cfg(IF_A, profile, deploy=False)], state, deploy=False, **kw)


def _omitting_everything():
    """The withdrawal model: the base routed profile with NONE of the eight keys present.

    `base_for` is not enough on its own for a key that the base profile itself declares, so each
    target is popped explicitly and the result asserted empty of all eight. A model that still
    carried one of them would make this an ordinary apply for that row.
    """
    w = dict(base_for(DAMP_BFD_ROUTED))
    for key in POSITIVE:
        w.pop(key, None)
    return w


# ===================================================== the registration, guarded
def test_all_eight_are_registered_before_anything_below_is_meaningful():
    """Guard the guard. If any of the eight lost its reset the module would REFUSE, and a
    refusal is not a withdrawal -- every case below would pass for the wrong reason."""
    pairs = [(nv, EXPECTED_RESET[nv]) for nv in EXPECTED_RESET]
    for nvpair, reset in pairs:
        rows = [r for r in [resolve_binding(DAMP_BFD_ROUTED, k) for k in POSITIVE] if r]
        row = [r for r in rows if r["parent_nvpair"] == nvpair]
        assert row, "%s::%s is not in the table at all" % (DAMP_BFD_ROUTED, nvpair)
        got = row[0].get("reset_wire")
        assert got == reset, "%s::%s reset is %r, expected %r" % (DAMP_BFD_ROUTED, nvpair, got, reset)
        assert isinstance(got, str), (
            "%s::%s reset_wire is %s; the controller returns this nvPair as a string"
            % (DAMP_BFD_ROUTED, nvpair, type(got).__name__))


def test_the_withdrawal_model_carries_none_of_the_eight():
    """The omission has to be real. If a target survived in the model this would be an apply."""
    w = _omitting_everything()
    present = sorted(k for k in POSITIVE if k in w)
    assert not present, "the withdrawal model still declares %r" % (present,)


# ============================================ one request, both families withdrawn
def test_one_replaced_request_carries_all_seven_dampening_resets_and_the_bfd_echo_reset():
    """The union property neither family's own suite states: eight resets, one payload.

    Each of the eight is checked SEPARATELY, by nvPair and by exact value. A count would pass
    while one row carried the wrong neutral.
    """
    result, calls = _run(_omitting_everything(), "replaced", have=_have())
    assert not result.get("failed"), result.get("msg")
    nv = request_nvpairs(calls)
    assert nv, ("no request was sent, so neither family's omission was detected. changed=%s"
                % result.get("changed"))
    assert len(split_calls(calls)["updates"]) == 1, (
        "expected exactly one configuration request, got %d"
        % len(split_calls(calls)["updates"]))
    for nvpair, reset in EXPECTED_RESET.items():
        assert nv[0].get(nvpair) == reset, (
            "%s travelled as %r, expected %r" % (nvpair, nv[0].get(nvpair), reset))
    # The public diff must own all eight too, independently of the request body.
    dnv = diff_nvpairs(result)
    assert dnv, "the run reported no public diff at all"
    for nvpair, reset in EXPECTED_RESET.items():
        assert dnv[0].get(nvpair) == reset, (
            "%s is absent from or wrong in the public diff: %r" % (nvpair, dnv[0].get(nvpair)))


# Explicit wire values from the routed base profile and its stable defaults. These are not
# derived from a second module request: that request can be a no-op and compare nothing.
EXPECTED_RETAINED_WIRE = {
    "DESC": "pilot",
    "FEC": "auto",
    "IP": "192.0.2.1",
    "PREFIX": "30",
    "INTF_VRF": "default",
    "OSPF_AREA_ID": "0.0.0.0",
    "ospf": "true",
    "MTU": "9216",
}


def _assert_untargeted_wire(nv):
    assert EXPECTED_RETAINED_WIRE, "no retained wire fields were specified"
    assert not set(EXPECTED_RETAINED_WIRE) & set(EXPECTED_RESET), (
        "a withdrawal target was included among retained fields")
    for field, value in EXPECTED_RETAINED_WIRE.items():
        assert field in nv, "untargeted %s is absent from the withdrawal request" % field
        assert nv[field] == value, (
            "untargeted %s changed during the combined withdrawal: %r, expected %r"
            % (field, nv[field], value))


def test_the_untargeted_prerequisites_survive_the_combined_withdrawal():
    """A reset that spilled onto a field nobody withdrew would be invisible in a count.

    `base_for(ROUTED)` supplies description, FEC, IP/prefix and OSPF; the module supplies the
    stable MTU and VRF defaults. None is a withdrawal target here; each must arrive unchanged.
    """
    result, calls = _run(_omitting_everything(), "replaced", have=_have())
    assert not result.get("failed"), result.get("msg")
    nv = request_nvpairs(calls)
    assert len(nv) == 1, "expected one actual withdrawal request, got %d" % len(nv)
    _assert_untargeted_wire(nv[0])


@pytest.mark.parametrize("corruption", ("missing_desc", "changed_fec"))
def test_the_retained_context_guard_rejects_a_missing_or_changed_field(corruption):
    result, calls = _run(_omitting_everything(), "replaced", have=_have())
    assert not result.get("failed"), result.get("msg")
    requests = request_nvpairs(calls)
    assert len(requests) == 1, "the negative control has no withdrawal payload"
    nv = dict(requests[0])
    _assert_untargeted_wire(nv)  # the untouched candidate must pass the same guard
    if corruption == "missing_desc":
        del nv["DESC"]
        field = "DESC"
    else:
        nv["FEC"] = "unexpected"
        field = "FEC"
    with pytest.raises(AssertionError, match="untargeted %s" % field):
        _assert_untargeted_wire(nv)


# =================================================================== controls
def test_merged_withdraws_nothing_from_either_family():
    """CONTROL: the eight resets above belong to the WITHDRAWAL path, not to the model's shape.
    Under `merged` the same omission preserves every one of them."""
    result, calls = _run(dict(_omitting_everything(), description="damp-bfd-merged"),
                         "merged", have=_have())
    assert not result.get("failed"), result.get("msg")
    nv = request_nvpairs(calls)
    assert nv, "the description change produced no request"
    for nvpair, applied in EXPECTED_APPLIED.items():
        assert nv[0].get(nvpair) == applied, (
            "merged changed %s to %r; an omission there must preserve %r"
            % (nvpair, nv[0].get(nvpair), applied))


def test_check_mode_plans_all_eight_and_transmits_nothing():
    """CONTROL: a plan is not a write. "It did not write" alone would also describe a check
    mode that planned nothing at all, so both halves are asserted."""
    result, calls = _run(_omitting_everything(), "replaced", have=_have(), check_mode=True)
    dnv = diff_nvpairs(result)
    assert dnv, "check mode planned nothing at all"
    for nvpair, reset in EXPECTED_RESET.items():
        assert dnv[0].get(nvpair) == reset, (
            "check mode did not plan %s as %r: %r" % (nvpair, reset, dnv[0].get(nvpair)))
    buckets = split_calls(calls)
    assert buckets["updates"] == [], "check mode sent a configuration request"
    assert buckets["deploys"] == [], "check mode sent a deploy request"


def test_rerun_from_the_withdrawn_state_converges():
    """CONTROL: with all eight already at their reset, the same model must configure nothing.
    `changed` alone is not the evidence -- the request buckets are."""
    withdrawn = build_have(DAMP_BFD_ROUTED)
    for nvpair, reset in EXPECTED_RESET.items():
        withdrawn[0]["interfaces"][0]["nvPairs"][nvpair] = reset
    result, calls = _run(_omitting_everything(), "replaced", have=withdrawn)
    buckets = split_calls(calls)
    assert buckets["updates"] == [], (
        "a converged rerun sent a configuration request: %s"
        % [c["path"] for c in buckets["updates"]])
    assert buckets["deploys"] == [], "a converged rerun sent a deploy request"
    assert not result.get("failed"), result.get("msg")


def test_the_two_families_neutrals_are_not_interchangeable_damp_bfd():
    """CONTROL: the assertions above have teeth because the neutrals differ. Three booleans
    reset to the STRING 'false' and five numbers to the EMPTY string; neither is the native
    `False`, which would never match a controller HAVE and is falsy where `'false'` is truthy."""
    booleans = {"dampening", "dampeningRestart", "bfdEcho"}
    for nvpair, reset in EXPECTED_RESET.items():
        if nvpair in booleans:
            assert reset == "false", "%s should reset to the string 'false'" % nvpair
        else:
            assert reset == "", "%s should reset to the empty string" % nvpair
        assert reset is not False and not isinstance(reset, bool), (
            "%s reset is a native bool: %r" % (nvpair, reset))
    assert len({EXPECTED_RESET[n] for n in EXPECTED_RESET}) == 2, (
        "the two neutral shapes collapsed into one, so a copy-paste between a boolean and a "
        "number would no longer be detectable here")


def test_the_dampening_evidence_status_is_not_upgraded_by_this_coexistence():
    """The seven dampening rows are registered and their omission was observed at the
    CONTROLLER with deploy false. NX-OS withdrawal was never validated and the lab platform
    does not support that CLI.

    This case asserts the only part of that a table can carry: the rows are registered, and the
    BFD row they travel beside is registered too. It deliberately asserts NOTHING about device
    behaviour, and its presence must not be read as device validation of dampening. The
    evidence split is documented with the review of these rows.
    """
    for key in ("enable_dampening", "dampening_restart", "dampening_half_life",
                "dampening_reuse", "dampening_suppress", "dampening_max_suppress",
                "dampening_restart_penalty"):
        b = resolve_binding(DAMP_BFD_ROUTED, key)
        assert b is not None and isinstance(b.get("reset_wire"), str), (
            "%s::%s is not registered with a string reset" % (DAMP_BFD_ROUTED, key))
    echo = resolve_binding(DAMP_BFD_ROUTED, "disable_bfd_echo")
    assert echo is not None and echo.get("reset_wire") == "false"


# ====================================================================================================
# Formerly test_dcnm_intf_smu207_coexistence.py
# OFFLINE coexistence of the SVI-list, mapping-reset and vPC-dot1q deliveries.
# ====================================================================================================
MAPPING = "3214,3216"
SECONDARY_GWS = [
    {"gateway_ip_address": "198.51.100.254/24"},
    {"gateway_ip_address": "203.0.113.254/24"},
]
SECONDARY_VIPS = [
    {"hsrp_secondary_vip": "192.0.2.123"},
    {"hsrp_secondary_vip": "192.0.2.133"},
]
GWS_WIRE = '{"secondaryGws":[{"gatewayIpAddress":"198.51.100.254/24"},{"gatewayIpAddress":"203.0.113.254/24"}]}'
VIPS_WIRE = '{"hsrpSecondaryVips":[{"hsrpSecondaryVip":"192.0.2.123"},{"hsrpSecondaryVip":"192.0.2.133"}]}'
PRIMARY = {
    "ipv4_addr": "192.0.2.1",
    "ipv4_mask_len": 24,
    "enable_hsrp": True,
    "hsrp_vip": "192.0.2.253",
    "hsrp_group": 1,
    "hsrp_version": 1,
}
DOT1Q_POSITIVE = {
    "acl_filter": "PILOT-ACL",
    "spanning_tree_port_type": "normal",
    "disable_qos_stats": True,
    "disable_queuing_stats": True,
    "disable_lldp_transmit": True,
    "disable_lldp_receive": True,
}
DOT1Q_RESETS = {
    "aclFilter": "",
    "spanningTreePortType": "no",
    "qosStatsSuppressed": "false",
    "queuingStats": "false",
    "lldpTransmit": "false",
    "lldpReceive": "false",
}


def configs():
    svi = base_for(SVI, **dict(PRIMARY, secondary_gws=copy.deepcopy(SECONDARY_GWS), hsrp_secondary_vips=copy.deepcopy(SECONDARY_VIPS)))
    # The mapping is intentionally omitted. Both lists are explicit and nonempty.
    return [cfg_for(SVI, svi), cfg_for(VPC_DOT1Q, base_for(VPC_DOT1Q))]


def configured_have():
    svi = build_have(SVI, "private_vlan_mapping", MAPPING, **PRIMARY)
    svi_nv = svi[0]["interfaces"][0]["nvPairs"]
    svi_nv["secondaryGws"] = GWS_WIRE
    svi_nv["hsrpSecondaryVips"] = VIPS_WIRE
    svi[0]["interfaces"][0]["interfaceType"] = "INTERFACE_VLAN"
    return svi + build_have(VPC_DOT1Q, **DOT1Q_POSITIVE)


def request_policies(calls):
    found = []
    _collect_policies([c["payload"] for c in split_calls(calls)["updates"]], found)
    return {policy["policy"]: policy for policy in found}


def assert_exact_resets_and_preservation(policies):
    assert set(policies) == {SVI, VPC_DOT1Q}

    svi = policies[SVI]["interfaces"][0]
    svi_nv = svi["nvPairs"]
    assert svi["interfaceType"] == "INTERFACE_VLAN"
    assert svi_nv["privateVlanMapping"] == ""
    assert svi_nv["secondaryGws"] == GWS_WIRE
    assert svi_nv["hsrpSecondaryVips"] == VIPS_WIRE
    assert svi_nv["IP"] == "192.0.2.1" and svi_nv["PREFIX"] == "24"
    assert svi_nv["ENABLE_HSRP"] == "true" and svi_nv["HSRP_VIP"] == "192.0.2.253"

    dot1q = policies[VPC_DOT1Q]["interfaces"][0]
    dot1q_nv = dot1q["nvPairs"]
    assert dot1q["interfaceType"] == "INTERFACE_VPC"
    assert dot1q["serialNumber"] == VPC_PAIR_SERIAL
    assert {key: dot1q_nv[key] for key in DOT1Q_RESETS} == DOT1Q_RESETS
    # The pair is controller-ordered in the request; every peer-specific identity differs.
    assert (dot1q_nv["PEER1_PCID"], dot1q_nv["PEER2_PCID"]) == ("14", "13")
    assert (dot1q_nv["PEER1_MEMBER_INTERFACES"], dot1q_nv["PEER2_MEMBER_INTERFACES"]) == (
        "Ethernet1/54",
        "Ethernet1/53",
    )
    assert (dot1q_nv["PEER1_ACCESS_VLAN"], dot1q_nv["PEER2_ACCESS_VLAN"]) == (
        "3802",
        "3801",
    )


def synthetic_post_apply_have(policies):
    have = []
    for policy in (policies[SVI], policies[VPC_DOT1Q]):
        item = copy.deepcopy(policy)
        item["interfaces"][0]["fabricName"] = "test_fabric"
        have.append(item)
    return have


def test_offline_union_resets_both_objects_and_preserves_explicit_lists_in_one_main_call():
    result, calls = run_configs(configs(), "replaced", have=configured_have())
    assert not result.get("failed"), result.get("msg")
    policies = request_policies(calls)
    assert_exact_resets_and_preservation(policies)


def test_offline_union_check_mode_plans_without_mutating_stub_calls():
    result, calls = run_configs(configs(), "replaced", have=configured_have(), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert result.get("changed") is True
    buckets = split_calls(calls)
    assert buckets["updates"] == [] and buckets["deploys"] == [] and buckets["other"] == []
    planned = diff_nvpairs(result)
    svi = next(nv for nv in planned if "privateVlanMapping" in nv)
    dot1q = next(nv for nv in planned if "aclFilter" in nv)
    assert svi["privateVlanMapping"] == ""
    assert "secondaryGws" not in svi and "hsrpSecondaryVips" not in svi
    assert {key: dot1q[key] for key in DOT1Q_RESETS} == DOT1Q_RESETS


def test_offline_union_synthetic_post_apply_have_converges():
    applied, calls = run_configs(configs(), "replaced", have=configured_have())
    assert not applied.get("failed"), applied.get("msg")
    post_apply = synthetic_post_apply_have(request_policies(calls))

    result, rerun_calls = run_configs(configs(), "replaced", have=post_apply)
    assert not result.get("failed"), result.get("msg")
    assert result.get("changed") is False
    buckets = split_calls(rerun_calls)
    assert buckets["updates"] == [] and buckets["deploys"] == [] and buckets["other"] == []
