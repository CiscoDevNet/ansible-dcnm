from __future__ import absolute_import, division, print_function
from decimal import Decimal, InvalidOperation
from typing import List, Optional
import ast
import json
import re

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_OSPF_BOOLEAN_ALIASES, gie_normalize_ospf_aliases

try:
    from pydantic import BaseModel, ConfigDict, field_validator, model_validator
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    # Create dummy classes to allow import without pydantic
    BaseModel = object
    ConfigDict = dict

    def field_validator(*args, **kwargs):
        """Dummy field_validator decorator that accepts any arguments"""
        def decorator(func):
            return func
        return decorator

    def model_validator(*args, **kwargs):
        """Dummy model_validator decorator that accepts any arguments"""
        def decorator(func):
            return func
        return decorator

# Note: If pydantic is not available, schemas will be imported but non-functional


def expand_interface_name(name):
    """
    Expand abbreviated interface names to their full forms following DCNM conventions.
    Based on dcnm_intf_get_if_name method from dcnm_interface.py

    Examples:
        po300 -> Port-channel300
        eth1/1 -> Ethernet1/1
        lo100 -> Loopback100
        vpc25 -> vPC25
        vlan10 -> vlan10
    """
    if name.lower().startswith("po"):
        # Port channel: po300 -> Port-channel300
        port_id = re.findall(r"\d+", name)
        if port_id:
            return f"Port-channel{port_id[0]}"
    elif name.lower().startswith("eth"):
        # Ethernet: eth1/1 -> Ethernet1/1, eth1/1.2 -> Ethernet1/1.2, eth1/49/1 -> Ethernet1/49/1
        if re.findall(r"\d+\/\d+\/\d+", name):
            port_id = re.findall(r"\d+\/\d+\/\d+", name)
            return f"Ethernet{port_id[0]}"
        elif re.findall(r"\d+\/\d+.\d+", name):
            port_id = re.findall(r"\d+\/\d+.\d+", name)
            return f"Ethernet{port_id[0]}"
        elif re.findall(r"\d+\/\d+", name):
            port_id = re.findall(r"\d+\/\d+", name)
            return f"Ethernet{port_id[0]}"
    elif name.lower().startswith("lo"):
        # Loopback: lo100 -> Loopback100
        port_id = re.findall(r"\d+", name)
        if port_id:
            return f"Loopback{port_id[0]}"
    elif name.lower().startswith("vpc"):
        # VPC: vpc25 -> vPC25
        port_id = re.findall(r"\d+", name)
        if port_id:
            return f"vPC{port_id[0]}"
    elif name.lower().startswith("vlan"):
        # SVI: vlan10 -> vlan10 (already in correct format)
        port_id = re.findall(r"\d+", name)
        if port_id:
            return f"vlan{port_id[0]}"

    # Return original name if no pattern matches
    return name


# ------------------------------------------------------------------------------------------------ registered nvPairs
# The checker used to parse BOTH the expected data and the readback through
# NvPairs, which silently dropped every undeclared nvPair, and its YAML map did not cover the registry: a requested
# flowcontrol_send read back OFF, or not at all, still passed. The checker now keeps every nvPair (extra="allow"), builds
# the expected value of every REGISTERED profile key on the parent the YAML selects, and normalizes both sides by the
# value kind of the nvPair.
#
# This table is the checker's OWN explicit copy of the registry identities: profile key -> (nvPair, comparison kind,
# parents on which a value can be requested). It was written out from the registry at 233ef0a2 and is deliberately NOT
# imported from plugins/module_utils at run time, so the checker never shares the production renderer's wire conversion;
# test_dcnm_interface_validator_r2.py compares it with the registry (names, parents, kinds) so a drift fails a unit test.
# Kinds: bool / int / enum (case-insensitive tokens), str_exact (secrets and case-sensitive names: compared as written),
# str_fold (IPv6 text, numeric or dotted text, and the process tags whose case semantics are unverified: compared
# case-insensitively, as the module does).
R2_REGISTERED_BINDINGS = {
    "acl_filter": ("aclFilter", "str_exact", (
        "int_access_host",
        "int_port_channel_access_host",
        "int_port_channel_dot1q_tunnel_host",
        "int_port_channel_trunk_host",
        "int_trunk_host",
        "int_vpc_access_host",
        "int_vpc_dot1q_tunnel",
        "int_vpc_pvlan_host",
        "int_vpc_trunk_host",
    )),
    "arp_timeout": ("arpTimeout", "int", ("int_routed_host", "int_subif", "int_vlan")),
    "bfd_min_rx_interval": ("bfdMinRxInterval", "int", ("int_subif", "int_vlan")),
    "bfd_multiplier": ("bfdMultiplier", "int", ("int_subif", "int_vlan")),
    "bfd_tx_interval": ("bfdTxInterval", "int", ("int_subif", "int_vlan")),
    "dampening_half_life": ("dampeningHalfLife", "int", ("int_routed_host",)),
    "dampening_max_suppress": ("dampeningMaxSuppress", "int", ("int_routed_host",)),
    "dampening_restart": ("dampeningRestart", "bool", ("int_routed_host",)),
    "dampening_restart_penalty": ("dampeningRestartPenalty", "int", ("int_routed_host",)),
    "dampening_reuse": ("dampeningReuse", "int", ("int_routed_host",)),
    "dampening_suppress": ("dampeningSuppress", "int", ("int_routed_host",)),
    "disable_bfd_echo": ("bfdEcho", "bool", ("int_routed_host", "int_vlan")),
    "disable_eigrp_bfd": ("eigrpBfdDisable", "bool", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "disable_ipv4_redirects": ("ipv4Redirects", "bool", ("int_routed_host", "int_subif", "int_vlan")),
    "disable_ipv6_redirects": ("ipv6Redirects", "bool", ("int_routed_host", "int_subif", "int_vlan")),
    "disable_lldp_receive": ("lldpReceive", "bool", (
        "int_access_host",
        "int_port_channel_access_host",
        "int_port_channel_dot1q_tunnel_host",
        "int_port_channel_pvlan_host",
        "int_port_channel_trunk_host",
        "int_pvlan_host",
        "int_routed_host",
        "int_trunk_host",
        "int_vpc_access_host",
        "int_vpc_dot1q_tunnel",
        "int_vpc_pvlan_host",
        "int_vpc_trunk_host",
    )),
    "disable_lldp_transmit": ("lldpTransmit", "bool", (
        "int_access_host",
        "int_port_channel_access_host",
        "int_port_channel_dot1q_tunnel_host",
        "int_port_channel_pvlan_host",
        "int_port_channel_trunk_host",
        "int_pvlan_host",
        "int_routed_host",
        "int_trunk_host",
        "int_vpc_access_host",
        "int_vpc_dot1q_tunnel",
        "int_vpc_pvlan_host",
        "int_vpc_trunk_host",
    )),
    "disable_qos_stats": ("qosStatsSuppressed", "bool", (
        "int_access_host",
        "int_port_channel_access_host",
        "int_port_channel_dot1q_tunnel_host",
        "int_port_channel_trunk_host",
        "int_routed_host",
        "int_trunk_host",
        "int_vpc_access_host",
        "int_vpc_dot1q_tunnel",
        "int_vpc_pvlan_host",
        "int_vpc_trunk_host",
    )),
    "disable_queuing_stats": ("queuingStats", "bool", (
        "int_access_host",
        "int_port_channel_access_host",
        "int_port_channel_dot1q_tunnel_host",
        "int_port_channel_pvlan_host",
        "int_port_channel_trunk_host",
        "int_routed_host",
        "int_trunk_host",
        "int_vpc_access_host",
        "int_vpc_dot1q_tunnel",
        "int_vpc_pvlan_host",
        "int_vpc_trunk_host",
    )),
    "eigrp_ipv4_distribute_list_direction": ("eigrpIpv4DistributeListDirection", "enum", ("int_routed_host", "int_subif", "int_vlan")),
    "eigrp_ipv4_distribute_list_prefix_list": ("eigrpIpv4DistributeListPrefixList", "str_exact", ("int_routed_host", "int_subif", "int_vlan")),
    "eigrp_ipv4_passive": ("eigrpIpv4Passive", "bool", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "eigrp_ipv6_distribute_list_direction": ("eigrpIpv6DistributeListDirection", "enum", ("int_routed_host", "int_subif", "int_vlan")),
    "eigrp_ipv6_distribute_list_prefix_list": ("eigrpIpv6DistributeListPrefixList", "str_exact", ("int_routed_host", "int_subif", "int_vlan")),
    "eigrp_no_ipv4_passive": ("eigrpNoIpv4Passive", "bool", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "eigrp_no_ipv6_passive": ("eigrpNoIpv6Passive", "bool", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "eigrp_process_tag": ("eigrpProcessTag", "str_fold", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "enable_bfd_interval": ("bfdInterval", "bool", ("int_subif", "int_vlan")),
    "enable_dampening": ("dampening", "bool", ("int_routed_host",)),
    "enable_eigrp_bfd": ("eigrpBfd", "bool", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "enable_eigrp_ipv6_routing": ("eigrpIpv6Routing", "bool", ("int_routed_host", "int_subif", "int_vlan")),
    "enable_eigrp_routing": ("eigrpRouting", "bool", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "enable_eigrp_shutdown": ("eigrpShutdown", "bool", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "enable_macsec_interface_policy": ("macsecInterfacePolicy", "bool", ("int_routed_host",)),
    "enable_ospf": ("ospf", "bool", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "enable_ospf_auth": ("ospfAuthentication", "bool", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "enable_pim_bfd_instance": ("pimBfdInstance", "bool", ("int_routed_host", "int_subif")),
    "enable_pim_sparse": ("ENABLE_PIM_SPARSE", "bool", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    # SMU 017 first increment (registry slice 0b_37). enable_cdp is checked here on the routed parent only; on the
    # other profiles it stays a native field.
    "enable_cdp": ("CDP_ENABLE", "bool", ("int_routed_host",)),
    "enable_evpn_multisite_dci_tracking": ("evpnMultisiteDciTracking", "bool", ("int_routed_host",)),
    "logging_event_port_link_status": ("loggingEventPortLinkStatus", "bool", ("int_access_host",)),
    "enable_vpc_peer_link": ("ENABLE_VPC_PEER_LINK", "bool", ()),
    "flowcontrol_receive": ("flowcontrolReceive", "enum", ("int_access_host", "int_trunk_host")),
    "flowcontrol_send": ("flowcontrolSend", "enum", ("int_access_host", "int_trunk_host")),
    "guard_mode": ("GUARD_MODE", "enum", ("int_port_channel_trunk_host", "int_trunk_host", "int_vpc_trunk_host")),
    "hsrp_groupv6": ("HSRP_GROUPv6", "int", ("int_vlan",)),
    "hsrp_preempt_delay_minimum": ("hsrpPreemptDelayMinimum", "int", ("int_vlan",)),
    "hsrp_priority_forwarding_threshold_lower": ("hsrpPriorityForwardingThresholdLower", "int", ("int_vlan",)),
    "hsrp_priority_forwarding_threshold_upper": ("hsrpPriorityForwardingThresholdUpper", "int", ("int_vlan",)),
    "hsrp_vipv6": ("HSRP_VIPv6", "str_fold", ("int_vlan",)),
    "ipv4_acl_in": ("ipv4AclIn", "str_exact", ("int_routed_host", "int_vlan")),
    "ipv6_link_local": ("ipv6LinkLocal", "str_fold", ("int_routed_host", "int_subif", "int_vlan")),
    "ipv6_nd_suppress_ra": ("ipv6NdSuppressRa", "bool", ("int_routed_host", "int_subif", "int_vlan")),
    "macsec_fallback_key_chain_name": ("macsecFallbackKeyChainName", "str_exact", ("int_routed_host",)),
    "macsec_key_chain_name": ("macsecKeyChainName", "str_exact", ("int_routed_host",)),
    "macsec_policy_name": ("macsecPolicyName", "str_exact", ("int_routed_host",)),
    "ospf_advertise_subnet": ("ospfAdvertiseSubnet", "bool", ("int_loopback",)),
    "ospf_area_id": ("OSPF_AREA_ID", "str_fold", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "ospf_auth_key": ("OSPF_AUTH_KEY", "str_exact", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "ospf_auth_key_id": ("OSPF_AUTH_KEY_ID", "int", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "ospf_authentication_key": ("ospfAuthenticationKey", "str_exact", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "ospf_authentication_key_type": ("ospfAuthenticationKeyType", "enum", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "ospf_bfd_mode": ("ospfBfdMode", "enum", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "ospf_cost": ("ospfCost", "int", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "ospf_dead_interval": ("ospfDeadInterval", "int", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "ospf_hello_interval": ("ospfHelloInterval", "int", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "ospf_mtu_ignore": ("ospfMtuIgnore", "bool", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "ospf_network_type": ("ospfNetworkType", "enum", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "ospf_passive_mode": ("ospfPassiveMode", "enum", ("int_routed_host", "int_subif", "int_vlan")),
    "ospf_priority": ("ospfPriority", "int", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "ospf_retransmit_interval": ("ospfRetransmitInterval", "int", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "ospf_shutdown": ("ospfShutdown", "bool", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "ospf_tag": ("ospfTag", "str_fold", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "ospf_transmit_delay": ("ospfTransmitDelay", "int", ("int_loopback", "int_routed_host", "int_subif", "int_vlan")),
    "pim_dr_priority": ("PIM_DR_PRIORITY", "int", ("int_routed_host", "int_subif", "int_vlan")),
    "private_vlan_mapping": ("privateVlanMapping", "str_fold", ("int_vlan",)),
    "spanning_tree_port_type": ("spanningTreePortType", "enum", (
        "int_access_host",
        "int_port_channel_access_host",
        "int_port_channel_dot1q_tunnel_host",
        "int_port_channel_pvlan_host",
        "int_port_channel_trunk_host",
        "int_trunk_host",
        "int_vpc_access_host",
        "int_vpc_dot1q_tunnel",
        "int_vpc_pvlan_host",
        "int_vpc_trunk_host",
    )),
}
R2_WIRE_VALUES = {
    ("int_loopback", "ospfNetworkType"): {'broadcast': 'broadcast', 'no_change': 'noChange', 'point_to_point': 'pointToPoint'},
    ("int_loopback", "ospfBfdMode"): {'disable': 'disable', 'enable': 'enable', 'no_change': 'noChange'},
    ("int_routed_host", "ospfBfdMode"): {'disable': 'disable', 'enable': 'enable', 'no_change': 'noChange'},
    ("int_routed_host", "ospfNetworkType"): {'broadcast': 'broadcast', 'no_change': 'noChange', 'point_to_point': 'pointToPoint'},
    ("int_routed_host", "ospfPassiveMode"): {'no_change': 'noChange', 'no_passive': 'noPassive', 'passive': 'passive'},
    ("int_subif", "ospfBfdMode"): {'disable': 'disable', 'enable': 'enable', 'no_change': 'noChange'},
    ("int_subif", "ospfNetworkType"): {'broadcast': 'broadcast', 'no_change': 'noChange', 'point_to_point': 'pointToPoint'},
    ("int_subif", "ospfPassiveMode"): {'no_change': 'noChange', 'no_passive': 'noPassive', 'passive': 'passive'},
    ("int_vlan", "ospfBfdMode"): {'disable': 'disable', 'enable': 'enable', 'no_change': 'noChange'},
    ("int_vlan", "ospfNetworkType"): {'broadcast': 'broadcast', 'no_change': 'noChange', 'point_to_point': 'pointToPoint'},
    ("int_vlan", "ospfPassiveMode"): {'no_change': 'noChange', 'no_passive': 'noPassive', 'passive': 'passive'},
}

# A registry identity a playbook can NEVER have as controller state, and why. A request for it is diagnosed, never compared.
R2_EXCEPTIONS = {
    ("int_port_channel_trunk_host", "ENABLE_VPC_PEER_LINK"): (
        "smu_unsupported: the module refuses an explicit enable_vpc_peer_link on this parent before any write"
    ),
}

# The expected parent template, from the YAML type and profile mode (the module's own `<type>_<mode>` policy selection).
R2_PARENT_BY_TYPE_MODE = {
    ("eth", "trunk"): "int_trunk_host",
    ("eth", "access"): "int_access_host",
    ("eth", "routed"): "int_routed_host",
    ("eth", "monitor"): "int_monitor_ethernet",
    ("eth", "epl_routed"): "epl_routed_intf",
    ("eth", "dot1q"): "int_dot1q_tunnel_host",
    ("eth", "pvlan"): "int_pvlan_host",
    ("pc", "monitor"): "int_monitor_port_channel",
    ("pc", "trunk"): "int_port_channel_trunk_host",
    ("pc", "access"): "int_port_channel_access_host",
    ("pc", "l3"): "int_l3_port_channel",
    ("pc", "dot1q"): "int_port_channel_dot1q_tunnel_host",
    ("pc", "pvlan"): "int_port_channel_pvlan_host",
    ("vpc", "trunk"): "int_vpc_trunk_host",
    ("vpc", "access"): "int_vpc_access_host",
    ("vpc", "dot1q"): "int_vpc_dot1q_tunnel",
    ("vpc", "pvlan"): "int_vpc_pvlan_host",
    ("sub_int", "subint"): "int_subif",
    ("lo", "lo"): "int_loopback",
    ("lo", "fabric"): "int_fabric_loopback_11_1",
    ("lo", "mpls"): "int_mpls_loopback",
    ("svi", "vlan"): "int_vlan",
}

# Values that are never printed by the checker (the registry marks their profile keys no_log); diagnostics show the
# key name and "<redacted>" instead. Names matching R2_SENSITIVE_PATTERN are redacted too, as a safety net.
R2_SENSITIVE_NVPAIRS = frozenset(("OSPF_AUTH_KEY", "ospfAuthenticationKey"))
R2_SENSITIVE_PATTERN = re.compile(r"(?i)(passw|secret|auth_?key$|authenticationkey$)")
R2_REDACTED = "<redacted>"

# Native PVLAN nvPairs of the PVLAN parents (not registry rows; the profile keys pvlan_mode / pvlan_association /
# pvlan_mapping / native_vlan / allowed_vlans / members map to them in mode pvlan).
R2_PVLAN_KINDS = {
    "PVLAN_MODE": "str_fold",
    "ASSOCIATION_LIST": "pvlan_pairs",
    "MAPPING_LIST": "pvlan_pairs",
    "PVLAN_NATIVE_VLAN": "str_fold",
    "PVLAN_ALLOWED_VLANS": "vlan_set",
    "PEER1_PVLAN_NATIVE_VLAN": "str_fold",
    "PEER2_PVLAN_NATIVE_VLAN": "str_fold",
    "PEER1_PVLAN_ALLOWED_VLANS": "vlan_set",
    "PEER2_PVLAN_ALLOWED_VLANS": "vlan_set",
    "MEMBER_INTERFACES": "members",
    "PEER1_MEMBER_INTERFACES": "members",
    "PEER2_MEMBER_INTERFACES": "members",
}

R2_NVPAIR_KIND = dict((nv, kind) for nv, kind, _parents in R2_REGISTERED_BINDINGS.values())
R2_NVPAIR_KIND.update(R2_PVLAN_KINDS)


def r2_is_sensitive(nvpair):
    return nvpair in R2_SENSITIVE_NVPAIRS or bool(R2_SENSITIVE_PATTERN.search(str(nvpair)))


def _r2_native(value):
    """A native JSON value as the nvPair string the controller uses: true/false, integers without a decimal part."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else str(value)
    return value


def _r2_vlan_ids(text):
    """'2211-2213, 2215' -> [2211, 2212, 2213, 2215]; None when the text is not a plain VLAN list."""
    ids = []
    for part in str(text).replace(" ", "").split(","):
        if not part:
            continue
        m = re.match(r"^(\d+)(?:-(\d+))?$", part)
        if not m:
            return None
        lo = int(m.group(1))
        hi = int(m.group(2) or lo)
        if hi < lo:
            return None
        ids.extend(range(lo, hi + 1))
    return sorted(set(ids))


def _r2_vlan_set(text):
    s = str(text).strip()
    if s.lower() in ("", "none", "all"):
        return s.lower()
    ids = _r2_vlan_ids(s)
    if ids is None:
        return "unparsed:" + s
    runs = []
    for v in ids:
        if runs and v == runs[-1][1] + 1:
            runs[-1][1] = v
        else:
            runs.append([v, v])
    return ",".join(str(lo) if lo == hi else "%d-%d" % (lo, hi) for lo, hi in runs)


_R2_PAIRS_CANONICAL = re.compile(r"^\d+:\d+(,\d+:\d+)*$")


def r2_pairs_canonical(pairs):
    """[(primary, secondary), ...] -> '2210:2211,2210:2212' (sorted, unique)."""
    return ",".join("%d:%d" % p for p in sorted(set(pairs)))


def _r2_pvlan_pairs(text):
    """The PVLAN list wrapper the controller stores ({"ASSOCIATION_LIST": [{"P_VLAN": .., "S_VLAN": ..}]}, JSON or a
    Python literal; S_VLAN may be a range) -> the canonical form. A canonical string passes through; anything that
    cannot be read is returned marked, so it can never equal an expected value."""
    s = str(text).strip()
    if s == "" or _R2_PAIRS_CANONICAL.match(s):
        return s
    data = None
    for loader in (json.loads, ast.literal_eval):
        try:
            data = loader(s)
            break
        except (ValueError, SyntaxError):
            continue
    if not isinstance(data, dict) or len(data) != 1:
        return "unparsed:" + s
    rows = list(data.values())[0]
    if not isinstance(rows, list):
        return "unparsed:" + s
    pairs = []
    for row in rows:
        if not isinstance(row, dict) or "P_VLAN" not in row or "S_VLAN" not in row:
            return "unparsed:" + s
        secondaries = _r2_vlan_ids(row["S_VLAN"])
        if not str(row["P_VLAN"]).strip().isdigit() or not secondaries:
            return "unparsed:" + s
        pairs.extend((int(str(row["P_VLAN"]).strip()), sec) for sec in secondaries)
    return r2_pairs_canonical(pairs)


_R2_MEMBER_PORT = re.compile(r"^(?:ethernet|eth|e)(\d+/\d+(?:/\d+)?)$", re.IGNORECASE)


def _r2_member(token):
    """One member token -> 'ethernetX/Y' for the accepted spellings (Ethernet1/8, eth1/8, e1/8), else the expanded name."""
    found = _R2_MEMBER_PORT.match(token.strip())
    return "ethernet" + found.group(1) if found else expand_interface_name(token.strip()).lower()


def _r2_members(text):
    """A member list as a sorted set of canonical port names (the order and the spelling are not significant)."""
    return ",".join(sorted(set(_r2_member(x) for x in str(text).split(",") if x.strip())))


def r2_normalize(nvpair, value):
    """The comparison form of one nvPair value, applied identically to the expected data and to the readback."""
    if value is None:
        return None
    value = _r2_native(value)
    kind = R2_NVPAIR_KIND.get(nvpair)
    if kind is None or not isinstance(value, str):
        return value
    s = value.strip()
    if kind in ("bool", "enum", "str_fold"):
        return s.lower()
    if kind == "int":
        try:
            return str(int(s))
        except ValueError:
            return s
    if kind == "str_exact":
        return s
    if kind == "pvlan_pairs":
        return _r2_pvlan_pairs(s)
    if kind == "vlan_set":
        return _r2_vlan_set(s)
    if kind == "members":
        return _r2_members(s)
    return s


def r2_wire(parent, nvpair, kind, value):
    """The nvPair string a requested YAML value must read back as (independent of the production renderer)."""
    value = _r2_native(value)
    value = str(value)
    if kind == "enum":
        return R2_WIRE_VALUES.get((parent, nvpair), {}).get(value, value)
    return value


def r2_apply_ospf_aliases(parent, profile):
    """Translate the documented OSPF boolean aliases of a YAML profile to the registered mode keys.

    The module still accepts ``ospf_bfd`` and ``ospf_passive_interface`` (true -> enable / passive, false -> no_change,
    never the explicit disable / no_passive), but they are not registry identities since SMU 4.3.1.0175006017, so the
    expected-nvPair loop would skip them without a diagnosis. The module's own normalization (``gie_normalize_ospf_aliases``)
    is reused so the checker and the module cannot drift. Returns (profile, problems): a translated COPY, or the unchanged
    profile and one message per reason the module would refuse. Messages name keys and types, never values.
    """
    aliases = sorted(set(key for (_parent, key) in GIE_OSPF_BOOLEAN_ALIASES))
    present = [key for key in aliases if key in profile]
    if not present:
        return profile, []
    translated = dict(profile)
    if parent is None:
        return profile, ["'%s' cannot be validated - the expected parent is unknown, so the alias cannot be mapped to its mode key" % k
                         for k in present]
    _result, reason = gie_normalize_ospf_aliases(parent, translated)
    if reason is None:
        return translated, []
    kind, _sep, rest = reason.partition(":")
    if kind == "not_applicable":
        where = sorted(p for (p, k) in GIE_OSPF_BOOLEAN_ALIASES if k == rest)
        return profile, ["'%s' cannot be validated - it is an alias only on %s, not on the expected parent %s" % (rest, ", ".join(where), parent)]
    if kind == "not_boolean":
        key, _sep, given = rest.partition(":")
        return profile, ["'%s' cannot be validated - it must be a boolean (received %s)" % (key, given)]
    alias, _sep, mode_key = rest.partition(":")
    return profile, ["'%s' and '%s' cannot be validated - they request different settings for the same OSPF field" % (alias, mode_key)]


def r2_expected_parent(interface):
    profile = interface.get("profile") or {}
    return R2_PARENT_BY_TYPE_MODE.get((interface.get("type", ""), profile.get("mode", "")))


def r2_pvlan_rows_to_pairs(field, rows):
    """YAML pvlan_association / pvlan_mapping rows -> [(primary, secondary)]; None when a row is unreadable."""
    pairs = []
    for row in rows or []:
        if not isinstance(row, dict) or "primary_vlan" not in row:
            return None
        secondaries = row.get("secondary_vlan") if field == "pvlan_association" else row.get("secondary_vlans")
        ids = _r2_vlan_ids(secondaries)
        if not ids or not str(row["primary_vlan"]).strip().isdigit():
            return None
        pairs.extend((int(str(row["primary_vlan"]).strip()), sec) for sec in ids)
    return pairs


def r2_redact(data):
    """A copy of a parsed query/expected structure (or a flat nvPairs dict) with every sensitive value replaced."""
    if isinstance(data, dict):
        out = {}
        for k, v in data.items():
            if r2_is_sensitive(k) and v not in (None, ""):
                out[k] = R2_REDACTED
            else:
                out[k] = r2_redact(v)
        return out
    if isinstance(data, list):
        return [r2_redact(x) for x in data]
    if isinstance(data, tuple):
        return tuple(r2_redact(x) for x in data)
    return data


class DcnmInterfaceQuerySchema(BaseModel):
    class NvPairs(BaseModel):
        # Keep every nvPair on both sides (an undeclared requested nvPair used to vanish before the comparison).
        model_config = ConfigDict(extra="allow")

        @model_validator(mode="before")
        @classmethod
        def r2_normalize_values(cls, data):
            """Native values become nvPair strings, and registered / PVLAN nvPairs take their comparison form (r2_normalize)
            -- identically for the expected data and the readback. Declared fields keep their own validators below."""
            if not isinstance(data, dict):
                return data
            return dict((k, r2_normalize(k, v)) for k, v in data.items())

        ACCESS_VLAN: Optional[str] = None
        aclFilter: Optional[str] = None
        ADMIN_STATE: Optional[str] = None
        ALLOWED_VLANS: Optional[str] = None
        BPDUGUARD_ENABLED: Optional[str] = None
        CDP_ENABLE: Optional[str] = None
        CONF: Optional[str] = None
        COPY_DESC: Optional[str] = None
        DESC: Optional[str] = None
        DISABLE_IP_REDIRECTS: Optional[str] = None
        DISABLE_LACP_SUSPEND: Optional[str] = None
        DISABLE_LLDP: Optional[str] = None
        ENABLE_LACP_VPC_CONV: Optional[str] = None
        ENABLE_MIRROR_CONFIG: Optional[str] = None
        ENABLE_MONITOR: Optional[str] = None
        ENABLE_NETFLOW: Optional[str] = None
        ENABLE_ORPHAN_PORT: Optional[str] = None
        ENABLE_OSPF_AUTH_MESSAGE_DIGEST: Optional[str] = None
        ENABLE_PFC: Optional[str] = None
        ENABLE_PIM_SPARSE: Optional[str] = None
        ENABLE_QOS: Optional[str] = None
        ENABLE_STORM_CONTROL: Optional[str] = None
        FABRIC_NAME: Optional[str] = None
        flowcontrolReceive: Optional[str] = None
        GUARD_MODE: Optional[str] = None
        INTF_NAME: Optional[str] = None
        INTF_VRF: Optional[str] = None
        IP: Optional[str] = None
        IPv6: Optional[str] = None
        IPv6_PREFIX: Optional[str] = None
        LACP_PORT_PRIO: Optional[str] = None
        LACP_RATE: Optional[str] = None
        LINK_STATE_ROUTING: Optional[str] = None
        LINK_STATE_ROUTING_TAG: Optional[str] = None
        MTU: Optional[str] = None
        NATIVE_VLAN: Optional[str] = None
        NETFLOW_MONITOR: Optional[str] = None
        NETFLOW_SAMPLER: Optional[str] = None
        PC_MODE: Optional[str] = None
        PEER1_ALLOWED_VLANS: Optional[str] = None
        PEER1_MEMBER_INTERFACES: Optional[str] = None
        PEER1_NATIVE_VLAN: Optional[str] = None
        PEER1_PCID: Optional[str] = None
        PEER1_PO_CONF: Optional[str] = None
        PEER1_PO_DESC: Optional[str] = None
        PEER2_ALLOWED_VLANS: Optional[str] = None
        PEER2_MEMBER_INTERFACES: Optional[str] = None
        PEER2_NATIVE_VLAN: Optional[str] = None
        PEER2_PCID: Optional[str] = None
        PEER2_PO_CONF: Optional[str] = None
        PEER2_PO_DESC: Optional[str] = None
        PIM_DR_PRIORITY: Optional[str] = None
        PO_ID: Optional[str] = None
        POLICY_DESC: Optional[str] = None
        POLICY_ID: Optional[str] = None
        PORTTYPE_FAST_ENABLED: Optional[str] = None
        PORT_DUPLEX_MODE: Optional[str] = None
        PREFIX: Optional[str] = None
        PRIORITY: Optional[str] = None
        PTP: Optional[str] = None
        QOS_POLICY: Optional[str] = None
        QUEUING_POLICY: Optional[str] = None
        ROUTING_TAG: Optional[str] = None
        ROUTE_MAP_TAG: Optional[str] = None
        SERIAL_NUMBER: Optional[str] = None
        SPEED: Optional[str] = None
        STORM_CONTROL_ACTION: Optional[str] = None
        STORM_CONTROL_BCAST_LEVEL_PERCENT: Optional[str] = None
        STORM_CONTROL_BCAST_LEVEL_PPS: Optional[str] = None
        STORM_CONTROL_MCAST_LEVEL_PERCENT: Optional[str] = None
        STORM_CONTROL_MCAST_LEVEL_PPS: Optional[str] = None
        STORM_CONTROL_UCAST_LEVEL_PERCENT: Optional[str] = None
        STORM_CONTROL_UCAST_LEVEL_PPS: Optional[str] = None
        V6IP: Optional[str] = None
        createVpc: Optional[str] = None

        @field_validator('CONF')
        @classmethod
        def normalize_conf_commands(cls, v):
            """
            Normalize CONF field by splitting commands, sorting them, and removing 'no shutdown'.
            This helps with consistent comparison of command lists.
            """
            if v is None or v == "":
                return v

            # Split commands by various delimiters
            commands = []
            if "; " in v:
                commands = v.split("; ")
            elif "\n" in v:
                commands = v.split("\n")
            else:
                commands = [v]

            # Clean up commands and remove 'no shutdown'
            cleaned_commands = []
            for cmd in commands:
                cmd = cmd.strip()
                if cmd and cmd.lower() != "no shutdown":
                    cleaned_commands.append(cmd)

            # Sort commands for consistent comparison
            cleaned_commands.sort()

            # Return empty string if no commands left, otherwise join with "; "
            return "; ".join(cleaned_commands) if cleaned_commands else ""

        @field_validator('INTF_NAME', 'PO_ID')
        @classmethod
        def normalize_interface_name(cls, v):
            """
            Expand abbreviated interface names to full forms and convert to lowercase.
            Examples: po300 -> port-channel300, eth1/1 -> ethernet1/1, vpc25 -> vpc25
            """
            if v is None:
                return v
            expanded = expand_interface_name(v)
            return expanded.lower()

        @field_validator(
            'ADMIN_STATE',
            'BPDUGUARD_ENABLED',
            'PORTTYPE_FAST_ENABLED',
            'PC_MODE',
            'INTF_VRF',
            'MTU',
            'SPEED',
        )
        @classmethod
        def normalize_string_fields(cls, v):
            """Convert common string fields to lowercase for case-insensitive comparison."""
            if v is not None:
                return v.lower()
            return v

        @field_validator('ENABLE_OSPF_AUTH_MESSAGE_DIGEST', mode='before')
        @classmethod
        def normalize_ospf_auth_message_digest(cls, v):
            """
            Normalize ENABLE_OSPF_AUTH_MESSAGE_DIGEST before string validation.

            NDFC returns this nvPair as a native JSON boolean on some builds and
            as the strings "true"/"false" on others. Raw query responses are
            parsed through this model, so a native boolean must be coerced here
            or validation rejects it before any assertion can run.

            Absence stays None: it means the interface predates the parameter,
            which is a different fact from an explicit false and must not be
            rewritten into one here.
            """
            if v is None:
                return v
            if isinstance(v, bool):
                return "true" if v else "false"
            return str(v).strip().lower()

        @field_validator('STORM_CONTROL_ACTION')
        @classmethod
        def normalize_storm_control_action(cls, v):
            """Normalize the public default action to NDFC's low-level nvPair value."""
            if v is None:
                return v
            normalized_action = v.lower()
            return "no" if normalized_action == "default" else normalized_action

        @field_validator(
            'STORM_CONTROL_BCAST_LEVEL_PERCENT',
            'STORM_CONTROL_MCAST_LEVEL_PERCENT',
            'STORM_CONTROL_UCAST_LEVEL_PERCENT',
        )
        @classmethod
        def normalize_storm_control_percent(cls, v):
            """Normalize equivalent percentage representations such as 12 and 12.00."""
            if v in (None, ""):
                return v
            try:
                return format(Decimal(v).normalize(), "f")
            except InvalidOperation:
                return v

    class Interface(BaseModel):
        ifName: str
        nvPairs: "DcnmInterfaceQuerySchema.NvPairs"
        serialNumber: tuple

        @field_validator('ifName')
        @classmethod
        def normalize_ifname(cls, v):
            """
            Expand abbreviated interface names to full forms and convert to lowercase.
            Examples: po300 -> port-channel300, eth1/1 -> ethernet1/1, vpc25 -> vpc25
            """
            expanded = expand_interface_name(v)
            return expanded.lower()

        @field_validator('serialNumber', mode='before')
        @classmethod
        def normalize_serial_number(cls, v):
            """Convert serialNumber string to sorted tuple by splitting on ~."""
            if isinstance(v, str):
                return tuple(sorted(v.split("~")))
            return v

    class InterfacePolicy(BaseModel):
        interfaces: List["DcnmInterfaceQuerySchema.Interface"]
        policy: Optional[str] = None

    failed: Optional[bool] = False
    response: Optional[List["DcnmInterfaceQuerySchema.InterfacePolicy"]] = None

    @classmethod
    def yaml_config_to_dict(cls, expected_config_data, test_fabric, switch_ip_sn_mapping=None, diagnostics=None):
        """
        Convert YAML interface configuration to DCNM API response format for validation.

        Registered fields: every REGISTERED profile key present in the profile (R2_REGISTERED_BINDINGS) becomes an
        expected nvPair on the parent template the YAML type/mode selects (R2_PARENT_BY_TYPE_MODE), with its wire value
        (r2_wire: booleans true/false, integers as text, the parent's enum wire spelling). false, 0 and "" are values,
        never dropped; only an explicit null (= omitted for the module) is skipped. In mode pvlan, pvlan_mode,
        pvlan_association / pvlan_mapping, native_vlan / allowed_vlans (per peer on a vPC) and the members map to the
        PVLAN nvPairs. A registered key the expected parent cannot carry (unknown parent, not registered on it, or an
        R2_EXCEPTIONS identity) is NOT silently skipped: it is reported in `diagnostics` (a list the caller passes), or
        raises ValueError when no list is given. Messages name keys, never values.

        Field Mappings from YAML config to JSON nvPairs:

        Common Fields (all interface types):
        - admin_state → ADMIN_STATE (boolean → string)
        - speed → SPEED (string)
        - description → DESC (string)
        - copy_description → COPY_DESC (boolean → string)
        - mtu → MTU (string)
        - bpdu_guard → BPDUGUARD_ENABLED (boolean/string → string)
        - port_type_fast → PORTTYPE_FAST_ENABLED (boolean → string)
        - cmds → CONF (list → sorted, semicolon-separated string, 'no shutdown' commands filtered out)

        Mode-specific Fields:
        Trunk mode:
        - allowed_vlans → ALLOWED_VLANS (string)
        - native_vlan → NATIVE_VLAN (integer → string)

        Access mode:
        - access_vlan → ACCESS_VLAN (integer → string)

        Routed mode:
        - int_vrf → INTF_VRF (string, excluded if empty)
        - ipv4_addr → IP (string)
        - ipv4_mask_len → PREFIX (integer → string)
        - route_tag → ROUTING_TAG (string, excluded if empty)

        EPL Routed mode (extends routed):
        - ipv6_addr → IPv6 (string) for non-loopback interfaces
        - ipv6_addr → V6IP (string) for loopback interfaces
        - ipv6_mask_len → IPv6_PREFIX (integer → string)

        Interface-specific mappings:
        Loopback interfaces:
        - ipv6_addr → V6IP (instead of IPv6)
        - route_tag → ROUTE_MAP_TAG (instead of ROUTING_TAG)
        - Uses INTF_NAME field (not PO_ID)

        Interface Name Handling:
        - Port-channel interfaces: Use PO_ID field
        - Other interfaces: Use INTF_NAME field

        Policy Mapping (NOT compared in validation):
        - Policy fields are auto-generated by NDFC and excluded from comparison

        Auto-generated fields (excluded from comparison):
        - CDP_ENABLE, ENABLE_MONITOR, ENABLE_NETFLOW, ENABLE_ORPHAN_PORT
        - ENABLE_PFC, ENABLE_QOS, NETFLOW_MONITOR, NETFLOW_SAMPLER
        - POLICY_DESC, POLICY_ID, PORT_DUPLEX_MODE, PRIORITY
        - PTP, QOS_POLICY, QUEUING_POLICY, SERIAL_NUMBER
        - Policy field (auto-determined by NDFC)

        Always included:
        - FABRIC_NAME (from test_fabric parameter)
        - PO_ID (for port-channel interfaces) or INTF_NAME (for other interfaces)
        """
        if switch_ip_sn_mapping is None:
            switch_ip_sn_mapping = {}

        # Mapping of fields in the yaml config to the fields in the DCNM API response
        # Format: {yaml_field: api_field}
        # adding fields places them in pydantic model and is checked by deepdiff
        # removing/commenting fields removes them from pydantic model

        # response.interfaces
        interface_fields = {
            "name": "ifName",
            "switch": "serialNumber"  # Will take first switch from list
        }

        # response.interfaces.nvPairs -- LEGACY (non-registered) fields only. The registered profile keys that used to be
        # listed here (flowcontrol_*, spanning_tree_port_type, guard_mode, disable_lldp_*, acl_filter, disable_qos_stats,
        # disable_queuing_stats) are built per parent from R2_REGISTERED_BINDINGS below.
        interface_nvpairs_fields = {
            "admin_state": "ADMIN_STATE",
            # Fabric loopback only. The generic bool->str conversion below already
            # produces the "true"/"false" strings NDFC echoes back.
            "enable_ospf_auth_message_digest": "ENABLE_OSPF_AUTH_MESSAGE_DIGEST",
            # Simple passthrough bindings. The generic bool->str conversion below
            # produces the "true"/"false" strings NDFC echoes back for these.
            # DISABLE_LLDP was removed by the 14sep2026 template batch and split into two
            # independent fields, so transmit and receive can be turned off separately.
            # The SMU templates renamed both to camelCase without changing meaning: the
            # declarations still read DisplayName "Disable LLDP transmit"/"receive" with
            # defaultValue=false, so "true" still means disabled.
            # QoS statistics slice. Both are the " no-stats" suffix of the service-policy
            # line their dependency emits, never a CLI line of their own.
            # Same: qosStatsSuppressed and queuingStats keep the negative sense the
            # bodies show -- noStats = " no-stats" if <field> == "true" else "".
            "speed": "SPEED",
            "description": "DESC",
            "copy_description": "COPY_DESC",
            "mtu": "MTU",
            "bpdu_guard": "BPDUGUARD_ENABLED",
            "port_type_fast": "PORTTYPE_FAST_ENABLED",
            "allowed_vlans": "ALLOWED_VLANS",
            "native_vlan": "NATIVE_VLAN",
            "access_vlan": "ACCESS_VLAN",
            "int_vrf": "INTF_VRF",
            "ipv4_addr": "IP",
            "ipv4_mask_len": "PREFIX",
            "ipv6_addr": "IPv6",
            "ipv6_mask_len": "IPv6_PREFIX",
            "route_tag": "ROUTING_TAG",
            "enable_storm_control": "ENABLE_STORM_CONTROL",
            "storm_control_action": "STORM_CONTROL_ACTION",
            "storm_control_broadcast_level_percent": "STORM_CONTROL_BCAST_LEVEL_PERCENT",
            "storm_control_broadcast_level_pps": "STORM_CONTROL_BCAST_LEVEL_PPS",
            "storm_control_multicast_level_percent": "STORM_CONTROL_MCAST_LEVEL_PERCENT",
            "storm_control_multicast_level_pps": "STORM_CONTROL_MCAST_LEVEL_PPS",
            "storm_control_unicast_level_percent": "STORM_CONTROL_UCAST_LEVEL_PERCENT",
            "storm_control_unicast_level_pps": "STORM_CONTROL_UCAST_LEVEL_PPS",
        }

        # Mode to policy mapping
        mode_to_policy = {
            "trunk": "int_trunk_host",
            "access": "int_access_host",
            "routed": "int_routed_host",
            "epl_routed": "epl_routed_intf",
            "monitor": "int_monitor_ethernet"
        }

        # Type to policy mapping (for VPC)
        type_to_policy = {
            "vpc": "int_vpc_trunk_host"
        }

        expected_data = {}
        expected_data["failed"] = False
        expected_data["response"] = []
        problems = []

        for interface in expected_config_data:
            interface_dict = {}
            interface_dict["interfaces"] = []

            # Don't include policy in comparison

            intf_dict = {}
            # Map base interface fields
            for key, value in interface_fields.items():
                if key in interface:
                    if key == "name":
                        # Expand abbreviated interface names (field validator will handle lowercase conversion)
                        intf_dict[value] = expand_interface_name(interface[key])
                    elif key == "switch":
                        # Convert IP addresses to serial numbers using mapping
                        switch_list = interface[key]
                        if switch_ip_sn_mapping:
                            switch_list = [switch_ip_sn_mapping.get(sw, sw) for sw in switch_list]

                        # For VPC and AA FEX interfaces, join switches with ~
                        if interface.get("type") in ["vpc", "aa_fex"] and len(switch_list) > 1:
                            intf_dict[value] = "~".join(switch_list)
                        else:
                            intf_dict[value] = switch_list[0]
                    else:
                        intf_dict[value] = interface[key]

            # Map nvPairs fields - only include configured fields
            intf_dict["nvPairs"] = {
                "FABRIC_NAME": test_fabric
            }

            # Use PO_ID for port-channel interfaces, INTF_NAME for others
            expanded_name = expand_interface_name(interface["name"])
            if expanded_name.lower().startswith("port-channel"):
                intf_dict["nvPairs"]["PO_ID"] = expanded_name
            else:
                intf_dict["nvPairs"]["INTF_NAME"] = expanded_name

            profile = interface["profile"]
            mode = profile.get("mode", "")
            interface_type = interface.get("type", "")

            # Map common nvPairs fields - only include fields that are explicitly configured
            for key, value in interface_nvpairs_fields.items():
                if key in profile:
                    val = profile[key]

                    # In mode pvlan these two are the PVLAN trunk native / allowed VLANs (mapped below)
                    if mode == "pvlan" and key in ("native_vlan", "allowed_vlans"):
                        continue

                    # Skip certain fields when they have empty string values
                    if key in ["int_vrf", "route_tag"] and val == "":
                        continue

                    # Skip ALLOWED_VLANS if set to 'none'
                    if key == "allowed_vlans" and val is not None and str(val).lower() == "none":
                        continue

                    # Handle special IPv6 mapping for loopback interfaces
                    if key == "ipv6_addr" and expanded_name.lower().startswith("loopback"):
                        # For loopback interfaces, use V6IP instead of IPv6
                        if isinstance(val, bool):
                            val = str(val).lower()
                        elif isinstance(val, (int)):
                            val = str(val)
                        intf_dict["nvPairs"]["V6IP"] = val
                        continue

                    # Handle special route_tag mapping for loopback interfaces
                    if key == "route_tag" and expanded_name.lower().startswith("loopback"):
                        # For loopback interfaces, use ROUTE_MAP_TAG instead of ROUTING_TAG
                        if val != "":  # Only include if not empty
                            if isinstance(val, bool):
                                val = str(val).lower()
                            elif isinstance(val, (int)):
                                val = str(val)
                            intf_dict["nvPairs"]["ROUTE_MAP_TAG"] = val
                        continue

                    # Convert boolean values to string
                    if isinstance(val, bool):
                        val = str(val).lower()
                    # Convert integer values to string
                    elif isinstance(val, (int)):
                        val = str(val)
                    # Keep string values as-is (field validators will handle case conversion)
                    intf_dict["nvPairs"][value] = val

            # Handle VPC and AA FEX specific fields
            if interface_type in ["vpc", "aa_fex"]:
                vpc_mapping = {
                    "pc_mode": "PC_MODE",
                    "peer1_pcid": "PEER1_PCID",
                    "peer2_pcid": "PEER2_PCID",
                    "peer1_description": "PEER1_PO_DESC",
                    "peer2_description": "PEER2_PO_DESC",
                    "peer1_allowed_vlans": "PEER1_ALLOWED_VLANS",
                    "peer2_allowed_vlans": "PEER2_ALLOWED_VLANS"
                }

                for key, value in vpc_mapping.items():
                    if key in profile:
                        val = profile[key]
                        if mode == "pvlan" and key in ("peer1_allowed_vlans", "peer2_allowed_vlans"):
                            continue  # the per-peer PVLAN allowed VLANs (mapped below)
                        if isinstance(val, bool):
                            val = str(val).lower()
                        elif isinstance(val, (int)):
                            val = str(val)
                        # Keep string values as-is (field validators will handle case conversion)
                        intf_dict["nvPairs"][value] = val

                # Handle member interfaces
                if "peer1_members" in profile:
                    intf_dict["nvPairs"]["PEER1_MEMBER_INTERFACES"] = ",".join(profile["peer1_members"])
                if "peer2_members" in profile:
                    intf_dict["nvPairs"]["PEER2_MEMBER_INTERFACES"] = ",".join(profile["peer2_members"])

                # Handle AA FEX peer-specific commands
                if interface_type == "aa_fex":
                    if "peer1_cmds" in profile and profile["peer1_cmds"] is not None:
                        # Filter out 'no shutdown' commands and sort for consistent comparison
                        filtered_cmds = [cmd.strip() for cmd in profile["peer1_cmds"] if cmd.strip().lower() != "no shutdown"]
                        if filtered_cmds:
                            filtered_cmds.sort()
                            intf_dict["nvPairs"]["PEER1_PO_CONF"] = "; ".join(filtered_cmds)
                    if "peer2_cmds" in profile and profile["peer2_cmds"] is not None:
                        # Filter out 'no shutdown' commands and sort for consistent comparison
                        filtered_cmds = [cmd.strip() for cmd in profile["peer2_cmds"] if cmd.strip().lower() != "no shutdown"]
                        if filtered_cmds:
                            filtered_cmds.sort()
                            intf_dict["nvPairs"]["PEER2_PO_CONF"] = "; ".join(filtered_cmds)

            # Handle commands (for non-AA FEX interfaces)
            if "cmds" in profile and interface_type != "aa_fex":
                if profile["cmds"] is not None and len(profile["cmds"]) > 0:
                    # Filter out 'no shutdown' commands and sort for consistent comparison
                    filtered_cmds = [cmd.strip() for cmd in profile["cmds"] if cmd.strip().lower() != "no shutdown"]
                    if filtered_cmds:
                        filtered_cmds.sort()
                        intf_dict["nvPairs"]["CONF"] = "; ".join(filtered_cmds)
                    else:
                        intf_dict["nvPairs"]["CONF"] = ""
                else:
                    intf_dict["nvPairs"]["CONF"] = ""

            # Registered profile keys, per parent
            parent = r2_expected_parent(interface)
            reg_profile, alias_problems = r2_apply_ospf_aliases(parent, profile)
            problems.extend("%s: %s" % (expanded_name, m) for m in alias_problems)
            for key in sorted(set(reg_profile) & set(R2_REGISTERED_BINDINGS)):
                val = reg_profile[key]
                if val is None:
                    continue  # null is an omission for the module: nothing is requested
                nvpair, kind, parents = R2_REGISTERED_BINDINGS[key]
                if parent is None or parent not in parents:
                    reason = R2_EXCEPTIONS.get((parent, nvpair)) or (
                        "not a registered field of the expected parent %s" % parent if parent
                        else "the expected parent of type '%s' mode '%s' is unknown" % (interface_type, mode))
                    problems.append("%s: '%s' (%s) cannot be validated - %s" % (expanded_name, key, nvpair, reason))
                    continue
                intf_dict["nvPairs"][nvpair] = r2_wire(parent, nvpair, kind, val)

            # Native PVLAN fields of the PVLAN parents
            if mode == "pvlan":
                if profile.get("pvlan_mode") is not None:
                    intf_dict["nvPairs"]["PVLAN_MODE"] = str(profile["pvlan_mode"])
                for field, nvpair in (("pvlan_association", "ASSOCIATION_LIST"), ("pvlan_mapping", "MAPPING_LIST")):
                    if profile.get(field) is not None:
                        pairs = r2_pvlan_rows_to_pairs(field, profile[field])
                        if pairs is None:
                            problems.append("%s: '%s' cannot be validated - a row is not a readable VLAN pair" % (expanded_name, field))
                        else:
                            intf_dict["nvPairs"][nvpair] = r2_pairs_canonical(pairs)
                if interface_type == "vpc":
                    for n in (1, 2):
                        for field, nvpair in (("peer%d_native_vlan" % n, "PEER%d_PVLAN_NATIVE_VLAN" % n),
                                              ("peer%d_allowed_vlans" % n, "PEER%d_PVLAN_ALLOWED_VLANS" % n)):
                            if profile.get(field) is not None:
                                intf_dict["nvPairs"][nvpair] = str(_r2_native(profile[field]))
                else:
                    for field, nvpair in (("native_vlan", "PVLAN_NATIVE_VLAN"), ("allowed_vlans", "PVLAN_ALLOWED_VLANS")):
                        if profile.get(field) is not None:
                            intf_dict["nvPairs"][nvpair] = str(_r2_native(profile[field]))
                    if interface_type == "pc" and profile.get("members") is not None:
                        intf_dict["nvPairs"]["MEMBER_INTERFACES"] = ",".join(str(m) for m in profile["members"])

            interface_dict["interfaces"].append(intf_dict)
            expected_data["response"].append(interface_dict)

        if problems:
            if diagnostics is None:
                raise ValueError("; ".join(problems))
            diagnostics.extend(problems)
        return expected_data
