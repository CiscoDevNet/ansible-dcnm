# Typed list contracts for registry bindings of type `struct_list`.
#
# Pure helpers only: no HTTP path and no AnsibleModule. gie_engine calls them for the four steps a
# scalar binding gets from its registered type: validate the raw playbook value, serialize it to the
# nvPair wire string, read an authoritative controller value, and compare two values.
#
# A struct[] template field travels as ONE nvPair whose value is a JSON object string that wraps the
# list under the nvPair's own name, the form the parent templates load:
#
#     vlanMappingEntries  {"vlanMappingEntries":[{"customerVlan":"10","dot1qTunnel":"false",...}]}
#
# The empty list is sent as "", the value an untouched interface returns.
#
# Each contract mirrors the validation of the template that consumes the list. The templates run that
# validation inside `try: ... except: pass`, so an item the validator cannot read (a missing key, a
# native boolean where the template compares with "true") renders no configuration and reports no
# error. Input that the template would only reject that way is refused here instead.
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import ast
import ipaddress
import json
import re

STRUCT_LIST_TYPE = "struct_list"

CONTRACT_VLAN_MAPPING = "vlan_mapping_entries"
CONTRACT_DHCP_SERVERS = "dhcp_servers"

_VLAN_MIN = 1
_VLAN_MAX = 4094
# An integerRange in canonical text: ASCII digits, single IDs or "lo-hi" ranges, comma-separated, no
# whitespace and no leading zeros.
_ID = r"(?:0|[1-9][0-9]*)"
_RANGE_TEXT = re.compile(r"^{0}(?:-{0})?(?:,{0}(?:-{0})?)*$".format(_ID))


class StructListError(Exception):
    """A list value that its contract refuses. The message names the field, the item and the rule."""


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _vlan_id(value, where):
    if not _is_int(value):
        raise StructListError("{0} must be an integer VLAN ID".format(where))
    if not _VLAN_MIN <= value <= _VLAN_MAX:
        raise StructListError("{0} must be between {1} and {2}".format(where, _VLAN_MIN, _VLAN_MAX))
    return value


def _vlan_range(value, where):
    """A customer VLAN as (wire text, set of IDs, is_range). An int is one VLAN; a string is an integerRange."""
    if _is_int(value):
        vlan = _vlan_id(value, where)
        return str(vlan), {vlan}, False
    if not isinstance(value, str) or not _RANGE_TEXT.match(value):
        raise StructListError(
            "{0} must be a VLAN ID, or a string of VLAN IDs and ranges such as '10-20,30' with no spaces".format(where)
        )
    ids = set()
    for part in value.split(","):
        lo, _sep, hi = part.partition("-")
        lo = int(lo)
        hi = int(hi) if hi else lo
        if not (_VLAN_MIN <= lo <= _VLAN_MAX and _VLAN_MIN <= hi <= _VLAN_MAX):
            raise StructListError("{0} must use VLAN IDs between {1} and {2}".format(where, _VLAN_MIN, _VLAN_MAX))
        if part.count("-") and lo >= hi:
            raise StructListError("{0} has a range whose start is not below its end".format(where))
        span = set(range(lo, hi + 1))
        if ids & span:
            raise StructListError("{0} lists a VLAN more than once".format(where))
        ids |= span
    return value, ids, "," in value or "-" in value


def _items(field, value, keys):
    if not isinstance(value, list):
        raise StructListError("'{0}' must be a list".format(field))
    for index, item in enumerate(value):
        where = "'{0}' item {1}".format(field, index + 1)
        if not isinstance(item, dict):
            raise StructListError("{0} must be a mapping".format(where))
        unknown = sorted(str(k) for k in item if k not in keys)
        if unknown:
            raise StructListError("{0} has unsupported key(s) {1}".format(where, ", ".join(unknown)))
        yield where, item


# ------------------------------------------------------------------ VLAN mapping
# int_trunk_host, int_port_channel_trunk_host and int_vpc_trunk_host declare the same item:
#
#     integerRange customerVlan (1-4094)   boolean dot1qTunnel
#     integer customerInnerVlan (1-4094, IsShow dot1qTunnel != true)   integer providerVlan (1-4094)
#
# interface_utility.validateVlanMappingCmds and getVlanMappingCmds read every key of every item and
# compare its values as strings (dot1qTunnel == "true", customerInnerVlan == "", "-" in customerVlan),
# so each row carries all four keys as strings. The vPC per-peer child parses the same value with
# ast.literal_eval, which a JSON wrapper of strings also satisfies.
_VLAN_MAPPING_KEYS = ("customer_vlan", "provider_vlan", "dot1q_tunnel", "customer_inner_vlan")


def _vlan_mapping_rows(field, value):
    rows = []
    providers = set()
    customers = set()
    tunnel_mode = None
    for where, item in _items(field, value, _VLAN_MAPPING_KEYS):
        for key in ("customer_vlan", "provider_vlan"):
            if item.get(key) is None:
                raise StructListError("{0} requires '{1}'".format(where, key))
        tunnel = item.get("dot1q_tunnel", False)
        if not isinstance(tunnel, bool):
            raise StructListError("{0} 'dot1q_tunnel' must be a boolean".format(where))
        customer, ids, is_range = _vlan_range(item["customer_vlan"], where + " 'customer_vlan'")
        provider = _vlan_id(item["provider_vlan"], where + " 'provider_vlan'")
        inner = item.get("customer_inner_vlan")
        if inner is not None:
            if tunnel:
                raise StructListError("{0} cannot set 'customer_inner_vlan' with 'dot1q_tunnel' true".format(where))
            inner = _vlan_id(inner, where + " 'customer_inner_vlan'")
        if is_range and not tunnel:
            raise StructListError("{0} 'customer_vlan' can be a range only with 'dot1q_tunnel' true".format(where))
        if tunnel_mode is not None and tunnel != tunnel_mode:
            raise StructListError(
                "'{0}' cannot mix selective dot1q-tunnel items with VLAN translation items on one interface".format(field)
            )
        tunnel_mode = tunnel
        if provider in providers:
            raise StructListError("{0} maps to provider VLAN {1}, which an earlier item already uses".format(where, provider))
        if customers & ids:
            raise StructListError("{0} repeats a customer VLAN of an earlier item".format(where))
        providers.add(provider)
        customers |= ids
        rows.append({
            "customerVlan": customer,
            "dot1qTunnel": "true" if tunnel else "false",
            "customerInnerVlan": "" if inner is None else str(inner),
            "providerVlan": str(provider),
        })
    return rows


def _vlan_mapping_read(raw):
    """The parent templates read the value with json.loads and index the wrapper key."""
    data = json.loads(raw)
    return data["vlanMappingEntries"] if isinstance(data, dict) and set(data) == {"vlanMappingEntries"} else None


# ------------------------------------------------------------------ DHCP relay servers
# int_routed_host, int_l3_port_channel and int_subif declare the same item, at most 16 of them:
#
#     ipAddress srvrAddr (IPv4 or IPv6)   string srvrVrf (^[a-zA-Z0-9:_-]*$, 0-32; blank = the interface VRF)
#
# The parents parse the value with ast.literal_eval (parseDhcpServers), refuse more than 16 items or an empty
# address, and hand the value unchanged to the child policy interface_dhcp_relay_internal, which renders one
# `ip dhcp relay address` (or `ipv6 dhcp relay address`) line per item, with `use-vrf` when srvrVrf is set and
# differs, ignoring case, from the interface VRF. The parents create that child only while the list is not empty.
# Each body deletes the interface's child policies before it recreates them on a modify (int_l3_port_channel unless
# the hidden SKIP_DEL_ON_ADD is true; int_subif marks them deleted), so an empty list may remove the child and its
# lines, but no full clear has been measured. An explicit empty list over a stored one is refused
# (clear_allowed False).
_DHCP_SERVER_KEYS = ("srvr_ip", "srvr_vrf")
_DHCP_SERVERS_MAX = 16
_VRF_TEXT = re.compile(r"^[a-zA-Z0-9:_-]*$")


def _dhcp_server_rows(field, value):
    if isinstance(value, list) and len(value) > _DHCP_SERVERS_MAX:
        raise StructListError("'{0}' allows at most {1} servers".format(field, _DHCP_SERVERS_MAX))
    rows = []
    seen = set()
    for where, item in _items(field, value, _DHCP_SERVER_KEYS):
        address = item.get("srvr_ip")
        if not isinstance(address, str) or address == "":
            raise StructListError("{0} requires 'srvr_ip' as an IPv4 or IPv6 address string".format(where))
        try:
            parsed = ipaddress.ip_address(address)
        except ValueError:
            raise StructListError("{0} 'srvr_ip' is not an IPv4 or IPv6 address".format(where))
        if str(parsed) != address:
            raise StructListError(
                "{0} 'srvr_ip' is not in canonical form (dotted IPv4, or compressed lowercase IPv6)".format(where)
            )
        vrf = item.get("srvr_vrf", "")
        if vrf is None:
            vrf = ""
        if not isinstance(vrf, str) or not _VRF_TEXT.match(vrf) or len(vrf) > 32:
            raise StructListError(
                "{0} 'srvr_vrf' must be a VRF name of up to 32 letters, digits, ':', '_' or '-'".format(where)
            )
        if (address, vrf) in seen:
            raise StructListError("{0} repeats the server and VRF of an earlier item".format(where))
        seen.add((address, vrf))
        rows.append({"srvrAddr": address, "srvrVrf": vrf})
    return rows


def _dhcp_server_read(raw):
    """The parents read the value with ast.literal_eval. Only the wrapper is accepted here: the child policy receives
    the value unchanged, and how it iterates a bare list is not established."""
    data = ast.literal_eval(raw)
    return data["dhcpServers"] if isinstance(data, dict) and set(data) == {"dhcpServers"} else None


# ------------------------------------------------------------------ contract table
# rows:          (field, playbook list) -> list of wire rows; raises StructListError
# read:          wire text -> list of rows, None when it is not the template's form; may raise
# clear_allowed: an explicit empty list may replace a stored non-empty one
_CONTRACTS = {
    CONTRACT_VLAN_MAPPING: {"rows": _vlan_mapping_rows, "read": _vlan_mapping_read, "clear_allowed": True},
    CONTRACT_DHCP_SERVERS: {"rows": _dhcp_server_rows, "read": _dhcp_server_read, "clear_allowed": False},
}


def struct_contracts():
    """The names a registry row may declare as `struct_contract`."""
    return frozenset(_CONTRACTS)


def _contract(name):
    contract = _CONTRACTS.get(name)
    if contract is None:
        raise StructListError("unknown list contract {0!r}".format(name))
    return contract


def struct_validate_input(contract, field, value):
    """Validate a playbook list; return the wire rows. Raises StructListError."""
    return _contract(contract)["rows"](field, value)


def struct_to_wire(contract, field, nvpair, value):
    """The nvPair wire string for a validated playbook list: "" for an empty list."""
    rows = struct_validate_input(contract, field, value)
    if not rows:
        return ""
    return json.dumps({nvpair: rows}, separators=(",", ":"))


def struct_read(contract, raw):
    """Authoritative controller value -> list of rows, or None when the template could not read it.

    "" is the empty list. Anything else must be text in the template's own form; rows are returned as
    stored, with their value types, so a comparison sees what the template sees.
    """
    if raw == "":
        return []
    if not isinstance(raw, str):
        return None
    try:
        rows = _contract(contract)["read"](raw)
    except (ValueError, SyntaxError, TypeError, KeyError, MemoryError, RecursionError):
        return None
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        return None
    return rows


def struct_compare_form(contract, raw):
    """A value in comparable form: the sorted rows, each as canonical JSON with its value types kept.

    Item order carries no meaning for these lists (each item renders its own command line), so two
    values that hold the same rows in a different order are equal. Duplicated rows are kept, and a
    native value never equals its string spelling, because the template treats them differently. A
    value the template could not read compares equal to nothing.
    """
    rows = struct_read(contract, raw)
    if rows is None:
        return object()
    return tuple(sorted(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows))


def struct_is_empty(contract, raw):
    """True when the value is readable and holds no row."""
    return struct_read(contract, raw) == []


def struct_clear_allowed(contract):
    """False when an explicit empty list may not replace a stored one (see the contract's comment)."""
    return _contract(contract)["clear_allowed"]
